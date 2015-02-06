#!/usr/bin/env python

from flask import Flask, render_template, request, jsonify
#from flask.ext.jsonpify import jsonify #uncomment to support JSONP CORS access
from flask import redirect, Response, make_response
import json
print('api importing db')
import db as rdb
print('api done importing db')
from authentication import get_user_dn
import os, time
from flask.ext.cors import cross_origin

#Only needed for event prototype
import gevent
from gevent.queue import Queue

#API version we are serving.
MPO_API_VERSION = 'v0'

#Set the database we are using
try:
    conn_string = os.environ['MPO_DB_CONNECTION']
except Exception, e:
    print('MPO_DB_CONNECTION not found: %s. Using default mpoDB at localhost.' % e)
    conn_string = "host='localhost' dbname='mpoDB' user='mpoadmin' password='mpo2013'"

print('db test-1', rdb.conn_string, str(rdb.mypool) )
rdb.init(conn_string)
print('db test-2', rdb.conn_string, str(rdb.mypool) )

app = Flask(__name__)
app.debug=True
apidebug=True

routes={'collection':'collection','workflow':'workflow',
        'activity': 'activity', 'dataobject':'dataobject',
        'dataobject_instance':'dataobject_instance',
        'comment':'comment', 'metadata':'metadata',
        'ontology_class':'ontology/class',
        'ontology_term':'ontology/term',
        'ontology_instance':'ontology/instance',
        'user':'user', 'item':'item',
        'guid':'uid'}


#MDSplus Events support
def publishEvent(eventname, eventbody=None):
    """
    eventname -- name convention for this event. Tag to listen for.

    eventbody -- should be text presently as we do not implement
    deserialization of arbitrary types.

    events are broadcast by Event over UDP
    """
    try:
        from MDSplus import Event
        from numpy import uint8
        if apidebug:
            print("APIDEBUG: publishEvent",eventname,eventbody)
            print("APIDEBUG: publishEvent",str(type(eventbody)))
        Event.seteventRaw(eventname,uint8(bytearray(eventbody)))
    except Exception as e:
        import sys,os
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("ERROR, events not supported. Tried to "+
              "send event %s, with message %s.")%(eventname,eventbody)
        print(exc_type, fname, exc_tb.tb_lineno)


# SSE "protocol" is described here: http://mzl.la/UPFyxY
class ServerSentEvent(object):

    def __init__(self, data):
        self.data = data
        self.event = None
        self.id = None
        self.desc_map = {
            self.data : "data",
            self.event : "event",
            self.id : "id"
        }


    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k)
                 for k, v in self.desc_map.iteritems() if k]

        return "%s\n\n" % "\n".join(lines)

subscriptions = []


def publishgevent(msg = str(time.time())):
    #this routine launches an asynchronous thread running notify().
    #Dummy data - pick up from request for real data

    #?logic here to choose with subs to send out?
    sendsubs=subscriptions #sendsubs will be subset of subscriptions later
    noticefound=False
    if len(sendsubs)>0:
        noticefound=True

    def notify():
        for sub in sendsubs[:]:
            sub.put(msg)

    if noticefound:
        gevent.spawn(notify)


def onlyone(recordstr): #error codes are made up for now
    if not isinstance(recordstr,str):
        s={"errorcode":1,"errormsg":"returned record is not a string"}
        s["record"]=str(recordstr)
        s["recordtype"]=str(type(recordstr))
        return json.dumps(s)
    else:
        j=json.loads(recordstr)
        if isinstance(j,list) and len(j)==1:  #strip off list
            return json.dumps(j[0])
        if isinstance(j,list) and len(j)>1:  #strip off list
            s=j[0]
            s["errorcode"]=3
            s["errormsg"]="returned record has more than one record"
            s["recordlen"]=len(j)
            return json.dumps(s)
        if isinstance(j,dict):  #strip off list
            s=j
            s["errorcode"]=0
            s["errormsg"]="warning, received json encoded dict and not a list of dict"
            return json.dumps(s)

        #default error
        s = {"errorcode":2,"errormsg":
               "returned record is not a valid type, must be a json string."}
        s["recordtype"]=str(type(recordstr))
        s["record"]=str(recordstr)
        return json.dumps(s)


###############ROUTE handling###############################
@app.errorhandler(404)
def not_found(error=None):
    message = {
            'status': 404,
            'message': 'Not Found: ' + request.url,
            'uid' : -9,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp


@app.errorhandler(400)
def syntax_error(error=None):
    message = {
            'status': 400,
            'message': 'Query error: ' + request.url,
            'request_body': request.data,
            'uid' : -1,
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@app.errorhandler(401)
def unathorized_error(error=None):
    message = {
            'status': 401,
            'message': 'Unauthorized error: ' + request.url,
            'request_body': request.data,
            'uid' : -1,
    }
    if apidebug:
        print('401 error',error)
    resp = jsonify(message)
    resp.status_code = 401

    return resp


class InvalidAPIUsage(Exception):
    status_code = 400

    def __init__(self, message="", status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidAPIUsage)
def handle_invalid_usage(error):
    resp = jsonify(error.to_dict())
    resp.status_code = error.status_code
    return resp



@app.route("/subscribe")
@cross_origin()
def subscribe(): #subscribe returns the gen() function. gen() returns an iterator
    print('subscribing')
    def gen():
        q = Queue()
        subscriptions.append(q)
        print('invoking gen')
        try:
            while True:
                result = q.get()
                print('invoking gen2')
                if apidebug:
                    print("SSE message: "+ str(result))
                ev = ServerSentEvent(str(result))
                yield ev.encode()
        except GeneratorExit: # Or maybe use flask signals
             if apidebug:#subscription gets removed if we navigate
                 #away from the page
                 print("in gen(): removing subscription")
             subscriptions.remove(q)
    # This invokes gen() which returns an iterator that is
    # returned by /subscribe in a Response()
    # Response() is a WSGI application. Response will send the next
    # message in the iterator/generator
    # for each http request
    return Response(gen(), mimetype="text/event-stream",
                    headers={'cache-control': 'no-cache',
                             'connection': 'keep-alive'})


@app.route("/nsub")
def debug():
    return "Currently %d subscriptions" % len(subscriptions)


#here we create application routes for a specified MPO_VERSION
if MPO_API_VERSION:
        for k,v in routes.iteritems():
                routes[k] = '/' + MPO_API_VERSION + '/' + routes[k]
else:
        for k,v in routes.iteritems():
                routes[k] = '/' + routes[k]



@app.route(routes['collection']+'/<id>', methods=['GET'])
@app.route(routes['collection'],  methods=['GET', 'POST'])
def collection(id=None):
    """
    Create and add to collections.
    Supported routes:
    /collection - GET a list of all (or filtered) collections
                - POST a new collection
    /collection/<id> - GET collection information, including list of member UUIDs

    /collection/<id>?detail=full[sparse] - GET collection information with full
               details [or default sparse as /collection/<id>]
    """
    dn=get_user_dn(request)
    if request.method == 'POST':
        r = rdb.addCollection(request.data,dn)
        morer = rdb.getRecord('collection',{'uid':json.loads(r)['uid']},dn)
        publishEvent('mpo_collection',onlyone(morer))
    elif request.method == 'GET':
        if id:
            r = rdb.getRecord('collection',{'uid':id})
        else:
            r = rdb.getRecord('collection',request.args)
    return r



@app.route(routes['collection']+'/<id>'+'/element', methods=['GET','POST'])
@app.route(routes['collection']+'/<id>'+'/element'+'/<oid>', methods=['GET'])
def collectionElement(id=None, oid=None):
    """
    /collection/<id>/element       - GET a list of objects in a collection
                                   - POST to add to the collection
    /collection/<id>/element/<oid> - GET details of a single object in a collection.
                                    Should resolve oid to full record from relevant table.
    """
    dn=get_user_dn(request)
    if request.method == 'POST':
        #make sure the element hasn't been added to the collection already
        payload = json.loads(request.data)
        elems = payload['elements']
        for e in elems[:]:
            r = rdb.getRecord('collection_elements',{'uid':e,'parent_uid':id})
            if json.loads(r)['uid']: elems.remove(e)
        payload['elements'] = elems
        r = rdb.addRecord('collection_elements',json.dumps(payload),dn)
        morer = rdb.getRecord('collection_elements',{'uid':json.loads(r)['uid']},dn)
        publishEvent('mpo_collection_elements',onlyone(morer))
    elif request.method == 'GET':
        if oid:
            r = rdb.getRecord('collection_elements',{'uid':oid})
        else:
            r = rdb.getRecord('collection_elements',{'parent_uid':id})

    # '[]'
    if len(r) == 2 : 
         r = make_response(r, 404)
         #resp=Response(r, mimetype='application/json')
    return r



@app.route(routes['workflow']+'/<id>', methods=['GET'])
@app.route(routes['workflow'],  methods=['GET', 'POST'])
def workflow(id=None):
    """
    Implementation of the /workflow route
    Enforces ontological constraints on workflows types retrieved from ontology_terms.
    """

    #Desperately need to add field error checking. Note, we have access to db.query_map
    dn=get_user_dn(request)
    if apidebug:
        print ('APIDEBUG: You are: %s'% str(dn) )
        print ('APIDEBUG: workflow url request is %s' %request.url)

    if not rdb.validUser(dn):
        if apidebug:
            print ('APIDEBUG: Not a valid user %s' % str(dn) )
        return Response(None, status=401)

    if request.method == 'POST':
        #check for valid workflow type
        wtype = json.loads(request.data).get('type')
        ont_entry = json.loads(rdb.getRecord('ontology_terms', {'path':'/Workflow/Type'}, dn ))[0]
        vocab=json.loads( rdb.getRecord('ontology_terms', {'parent_uid':ont_entry['uid']}, dn ) )
        valid= tuple(x['name'] for x in vocab)
        if (wtype in valid):
            ##Add logic to check for fields or exceptions from query
            type_uid = ont_entry.get('uid')
            p=json.loads(request.data)
            payload={"name":p['name'],"description":p['description'],"type_uid":type_uid,"value":wtype}
            r = rdb.addWorkflow(payload,dn)
            #should return ENTIRE record created. use rdb.getworkflow internally
        else:
            payload={"url":request.url, "body":request.data, "hint":valid, "uid":-1}
            raise InvalidAPIUsage(message='Invalid workflow type specified',status_code=400,
                                    payload=payload)

    elif request.method == 'GET':
        if id:
            darg=dict(request.args.items(multi=True)+[('uid',id)])
            if apidebug:
                print('APIDEBUG: darg is %s' %darg)
            r = rdb.getWorkflow({'uid':id},dn)
        else:
            r = rdb.getWorkflow(request.args,dn)
            #add workflow type here in return. Use complete path?

        if apidebug:
            print ('APIDEBUG: workflow returning "%s" len %d'% (r,len(r),))
        if len(r) == 2:
            r = make_response(r,404)

    if apidebug:
        print ('APIDEBUG: workflow %s'% (r,) )

    return r



@app.route(routes['workflow']+'/<id>/graph', methods=['GET'])
def getWorkflowGraph(id):
    dn=get_user_dn(request)
    if request.method == 'GET':
        r = rdb.getWorkflowElements(id,request.args,dn)
        return r



@app.route(routes['workflow']+'/<id>/comments', methods=['GET'])
def getWorkflowComments(id):
    dn=get_user_dn(request)

    ids=id.strip().split(',')
    r={} #[]
    for id in ids:
        rs = json.loads(rdb.getWorkflowComments(id,request.args,dn))
        if len(rs)!=0:        #append a dict query_id:result. strip off [].
            r[id]=rs
        else:
            rs=[]#{'uid':'0'} #not found
            r[id]=rs

    if len(r)==1:
        r=rs
    return Response(json.dumps(r), mimetype='application/json')


@app.route(routes['workflow']+'/<id>/type', methods=['GET'])
def getWorkflowType(id):
    dn=get_user_dn(request)
    r = rdb.getWorkflowType(id,request.args,dn)
    return r



@app.route(routes['workflow']+'/<id>/alias', methods=['GET'])
def getWorkflowCompositeID(id):
    """
    Method to retrieve a workflow composite id in the field 'alias'.
    """
    dn=get_user_dn(request)
    r={}
    if request.method == 'GET':
        #Add logic to parse id if comma separated
        if id:
            ids=id.strip().split(',')
            for id in ids:
                rs = json.loads(rdb.getWorkflowCompositeID(id,dn))
                if rs:
                    r[id]=rs
                else:
                    r[id]=[]#{'uid':'0','msg':'invalid response','len':len(rs),'resp':rs}

            if len(ids)==1: #return just single record if one uid
                r=rs

    return Response(json.dumps(r), mimetype='application/json')



@app.route(routes['dataobject']+'/<id>', methods=['GET'])
@app.route(routes['dataobject'], methods=['GET', 'POST'])
def dataobject(id=None):
    dn=get_user_dn(request)
    istatus=200
    if request.method == 'POST':
        r = rdb.addDataobject(request.data,dn)
        rr = json.loads(r)
        id = rr['uid']
        morer = rdb.getRecord('dataobject',{'uid':id},dn)
        publishEvent('mpo_dataobject',onlyone(morer))
    elif request.method == 'GET':
        if id:
            ids=id.strip().split(',')
            r={}
            for id in ids:
                rs = json.loads(rdb.getRecord('dataobject',{'uid':id},dn))
                if rs:
                    r[id]=rs
                else:
                    r[id]=[]#{'uid':'0','msg':'invalid response','len':len(rs),'resp':rs}

            if len(ids)==1: #return just single record if one uid
                r=rs
        else:
            r = json.loads(rdb.getRecord('dataobject',request.args,dn))
            if len(r) == 0 :
                istatus=404
                #r = make_response(json.dumps(r), 404)

    return Response(r, mimetype='application/json',status=istatus)



@app.route(routes['dataobject_instance']+'/<id>', methods=['GET'])
@app.route(routes['dataobject_instance'], methods=['GET', 'POST'])
def dataobject_instance(id=None):
    dn=get_user_dn(request)
    istatus=200
    if request.method == 'POST':
        r = rdb.addRecord('dataobject_instance',request.data,dn)
        rr = json.loads(r)
        id = rr['uid']
        morer = rdb.getRecord('dataobject_instance',{'uid':id},dn)
        publishEvent('mpo_dataobject_instance',onlyone(morer))
    elif request.method == 'GET':
        if id:
            ids=id.strip().split(',')
            r={}
            for id in ids:
                rs = json.loads(rdb.getRecord('dataobject_instance',{'uid':id},dn))
                if rs:
                    r[id]=rs
                else:
                    r[id]=[]#{'uid':'0','msg':'invalid response','len':len(rs),'resp':rs}

            if len(ids)==1: #return just single record if one uid
                r=rs
        else:
            r = json.loads(rdb.getRecord('dataobject_instance',request.args,dn))
            if len(r) == 0 :
                istatus=404
                #r = make_response(json.dumps(r), 404)

    return Response(r, mimetype='application/json',status=istatus)



@app.route(routes['activity']+'/<id>', methods=['GET'])
@app.route(routes['activity'], methods=['GET', 'POST'])
def activity(id=None):
    istatus=200
    dn=get_user_dn(request)
    if request.method == 'POST':
        r = rdb.addRecord('activity',request.data,dn)
        rr = json.loads(r)
        id = rr['uid']
        morer = rdb.getRecord('activity',{'uid':id},dn)
        publishEvent('mpo_activity',onlyone(morer))
    elif request.method == 'GET':
        if id:
            ids=id.strip().split(',')
            r={}
            for id in ids:
                rs = json.loads(rdb.getRecord('activity',{'uid':id},dn))
                if rs:
                    r[id]=rs
                else:
                    r[id]=[]#{'uid':'0','msg':'invalid response','len':len(rs),'resp':rs}

            if len(ids)==1: #return just single record if one uid
                r=rs

            r=json.dumps(r)
        else:
            r = rdb.getRecord('activity',request.args,dn)


    #if r='[]', later set metadata with number of records
    if len(r) == 2 :
        istatus=404

    return Response(r, mimetype='application/json',status=istatus)




@app.route(routes['comment']+'/<id>', methods=['GET'])
@app.route(routes['comment'], methods=['GET', 'POST'])
def comment(id=None):
    dn=get_user_dn(request)
    if request.method == 'POST':
        r = rdb.addComment(request.data,dn)
        rr = json.loads(r)
        id = rr['uid']
        try:  #JCW just being careful here on first implementation
            morer = rdb.getRecord('comment',{'uid':id},dn)
        except Exception as e:
            import sys,os
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('get comment',exc_type, fname, exc_tb.tb_lineno)

        publishEvent('mpo_comment',onlyone(morer))

    elif request.method == 'GET':
        #Add logic to parse id if comma separated
        if id:
            ids=id.strip().split(',')
            r={}
            for id in ids:
                rs = json.loads(rdb.getRecord('comment',{'uid':id},dn))
                if len(rs)==1:
                    r[id]=rs[0] #unpack single element list
                else:
                    r[id]=[]#{'uid':'0','msg':'invalid response','len':len(rs),'resp':rs}
            if len(ids)==1: #return just single record if one uid
                r=json.dumps(rs)
            else:
                r=json.dumps(r)
        else:
            r = rdb.getRecord('comment',request.args,dn)

    return Response(r, mimetype='application/json')



@app.route(routes['metadata']+'/<id>', methods=['GET'])
@app.route(routes['metadata'], methods=['GET', 'POST'])
def metadata(id=None):
    dn=get_user_dn(request)
    if request.method == 'POST':
        r = rdb.addMetadata( request.data, dn)
        rr = json.loads(r)
        id = rr['uid']
        morer = rdb.getRecord('metadata',{'uid':id},dn)
        publishEvent('mpo_metadata',onlyone(morer))
    elif request.method == 'GET':
        #Add logic to parse id if comma separated
        if id:
            ids=id.strip().split(',')
            r={}
            for id in ids:
                rs = json.loads(rdb.getRecord('metadata',{'uid':id},dn))
                if len(rs)==1:
                    r[id]=rs[0] #unpack single element list
                else:
                    r[id]=[]#{'uid':'0','msg':'invalid response','len':len(rs),'resp':rs}
            if len(ids)==1: #return just single record if one uid
                r=json.dumps(rs)
            else:
                r=json.dumps(r)
        else:
            r = rdb.getRecord('metadata',request.args,dn)

    return Response(r, mimetype='application/json')


@app.route(routes['ontology_class']+'/<id>', methods=['GET'])
@app.route(routes['ontology_class'], methods=['GET', 'POST'])
def ontologyClass(id=None):
    dn=get_user_dn(request)
    result = jsonify(json.loads(request.data),user_dn=dn)
    if request.method == 'POST':
        pass
    else:
        pass
    return result


@app.route(routes['ontology_term']+'/<id>/vocabulary', methods=['GET'])
@app.route(routes['ontology_term']+'/vocabulary', methods=['GET'])
def ontologyTermVocabulary(id=None):
    '''
    This function returns the vocabulary of an ontology term specified by its <id>=parent_id.
    Vocabulary is defined as the next set of terms below it in the
    ontology term tree.
    It is a convenience route equivalent to GET ontology_term?parent_uid=uid
    '''
    dn=get_user_dn(request)

    if not id:
        id='None'

    r = rdb.getRecord('ontology_terms', {'parent_uid':id}, dn )

    return r


@app.route(routes['ontology_term']+'/<id>/tree', methods=['GET'])
@app.route(routes['ontology_term']+'/tree', methods=['GET'])
@cross_origin()
def ontologyTermTree(id=None):
    '''
    This function returns the vocabulary of an ontology term specified by its <id>=parent_id.
    Vocabulary is defined as the next set of terms below it in the ontology term tree.
    '''
    dn=get_user_dn(request)

    if not id:
        id='0' #root parent_uid

    r = rdb.getOntologyTermTree(id, dn )

    return jsonify(**r)


@app.route(routes['ontology_term']+'/<id>', methods=['GET'])
@app.route(routes['ontology_term'], methods=['GET', 'POST'])
def ontologyTerm(id=None):
    '''
    Retrieves the record of an ontology term from its <id> or path.
    valid routes:
    ontology/term/<id>
    ontology/term?path=term/term2/termN
    '''
    dn=get_user_dn(request)
    if not rdb.validUser(dn):
        if apidebug:
            print ('APIDEBUG: Not a valid user'% dn)
        return Response(None, status=401)

    if request.method == 'POST':
        r = rdb.addOntologyTerm(request.data,dn)
                #r = rdb.addRecord('ontology_terms',request.data,dn)
    else:
        if id:
            r = rdb.getRecord('ontology_terms', {'uid':id}, dn )
        else:
            r = rdb.getRecord('ontology_terms', request.args, dn )
    return r


@app.route(routes['ontology_instance']+'/<id>', methods=['GET'])
@app.route(routes['ontology_instance'], methods=['GET', 'POST'])
def ontologyInstance(id=None):
    dn=get_user_dn(request)
    if request.method == 'POST':
        r = rdb.addOntologyInstance(request.data,dn)
    else:
        if id:
            r = rdb.getRecord('ontology_instances', {'uid':id}, dn )
        else:
            p_uids=request.args.get('parent_uid')
            if p_uids:
                p_uids=p_uids.strip().split(',')
                print('ont inst',p_uids,str(len(p_uids)))
                r={}
                rargs=request.args.to_dict() #multidict conversion to dict
                for pid in p_uids:
                    rargs['parent_uid']=pid
                    rs = json.loads(rdb.getRecord('ontology_instances', rargs, dn ))
                    print('ont inst',pid,str(rargs),str(type(rargs)))
                    r[pid]=rs #element list, can have multiple instances

                if len(p_uids)==1: #return just single record if one uid
                    r=rs
            else:
                r = json.loads(rdb.getRecord('ontology_instances', request.args, dn ))

    return Response(json.dumps(r), mimetype='application/json')



@app.route(routes['user']+'/<id>', methods=['GET'])
@app.route(routes['user'], methods=['GET', 'POST'])
def user(id=None):
    dn=get_user_dn(request)
    if request.method == 'POST':
        r = rdb.addUser( request.data, dn )
    elif request.method == 'GET':
        if id:
            r = rdb.getUser( {'uid':id}, dn )
        else:
            r = rdb.getUser( request.args, dn )

    return r


@app.route(routes['item']+'/<id>', methods=['GET'])
def item(id):
    dn=get_user_dn(request)
    if id:
        r = rdb.getRecordTable( id, dn )
    else:
        payload={"url":request.url, "body":request.data, "hint":"Must provide an UID", "uid":-1}
        raise InvalidAPIUsage(message='Unsupported route specified',status_code=400,
                              payload=payload)

    return Response(json.dumps(r), mimetype='application/json')
    

if __name__ == '__main__':
    #adding debug option here, so we can see what is going on.
    app.debug = False
    #    app.run()
    app.run(host='0.0.0.0', port=8080) #api server
    #app.run(host='0.0.0.0', port=8889) #web ui server
