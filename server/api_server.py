#!/usr/bin/env python

from flask import Flask, render_template, request, jsonify, redirect, Response
import json
import db as rdb
from authentication import get_user_dn
import time
from flask.ext.cors import cross_origin

#Only needed for event prototype
import gevent
from gevent.queue import Queue

#MDSplus Events support
def publishEvent(eventname, eventbody=None):
    """
    eventbody should be text presently as we do not implement
    deserialization of arbitrary types.
    """
    try:
        from MDSplus import Event
        from numpy import uint8
        Event.seteventRaw(eventname,uint8(bytearray(eventbody)))
    except:
        print("ERROR, events not supported. Tried to "+
              "send event %s, with message %s.")%(eventname,eventbody)


MPO_API_VERSION = 'v0'

app = Flask(__name__)
app.debug=False
apidebug=False

routes={'collection':'collection','workflow':'workflow',
        'activity': 'activity', 'dataobject':'dataobject',
	'comment':'comment', 'metadata':'metadata', 
        'ontology_class':'ontology/class', 
        'ontology_term':'ontology/term',
        'ontology_instance':'ontology/instance',
        'user':'user',
	'guid':'guid'}

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
	     if apidebug:#subscription gets removed if we navigate away from the page
		 print("in gen(): removing subscription")
	     subscriptions.remove(q)
    # This invokes gen() which returns an iterator that is returned by /subscribe in a Response()
    # Response() is a WSGI application. Response will send the next message in the iterator/generator 
    # for each http request
    return Response(gen(), mimetype="text/event-stream",headers={'cache-control': 'no-cache',
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
	dn=get_user_dn(request)
	result = jsonify(json.loads(request.data),user_dn=dn)
	if request.method == 'POST':
            pass
 	elif request.method == 'GET':
            pass
        return result

@app.route(routes['workflow']+'/<id>', methods=['GET'])
@app.route(routes['workflow'],  methods=['GET', 'POST'])
def workflow(id=None):
	dn=get_user_dn(request)
	if apidebug:
		print ('APIDEBUG: You are: %s'% dn )
		print ('APIDEBUG: workflow url request is',request.url)
        if not rdb.validUser(dn):
                return Response(None, status=401)

	if request.method == 'POST':
                r = rdb.addWorkflow(request.data,dn)
 	elif request.method == 'GET':
		if id:
			darg=dict(request.args.items(multi=True)+[('uid',id)])
			print('darg',darg)
			r = rdb.getWorkflow({'uid':id},dn)
		else:
			r = rdb.getWorkflow(request.args,dn)
	return r


@app.route(routes['workflow']+'/<id>/graph', methods=['GET'])
def getWorkflowGraph(id):
	dn=get_user_dn(request)
	if request.method == 'GET':
		r = rdb.getWorkflowElements(id,request.args,dn)
	return r


@app.route(routes['workflow']+'/<id>/alias', methods=['GET'])
def getWorkflowCompositeID(id):
	dn=get_user_dn(request)
	if request.method == 'GET':
		r = rdb.getWorkflowCompositeID(id)
	return r


@app.route(routes['dataobject']+'/<id>', methods=['GET'])
@app.route(routes['dataobject'], methods=['GET', 'POST'])
def dataobject(id=None):
	dn=get_user_dn(request)
	if request.method == 'POST':
                r = rdb.addRecord('dataobject',request.data,dn)
                publishEvent('mpo_object',r)
 	elif request.method == 'GET':
		if id:
			r = rdb.getRecord('dataobject',{'uid':id})
		else:
			r = rdb.getRecord('dataobject',request.args)
	return r
        

@app.route(routes['activity']+'/<id>', methods=['GET'])
@app.route(routes['activity'], methods=['GET', 'POST'])
def activity(id=None):
	dn=get_user_dn(request)
	if request.method == 'POST':
		r = rdb.addRecord('activity',request.data,dn)
                publishEvent('mpo_activity',r)
 	elif request.method == 'GET':
		if id:
			r = rdb.getRecord('activity', {'uid':id})
		else:
			r = rdb.getRecord('activity',request.args)
	return r


@app.route(routes['comment']+'/<id>', methods=['GET'])
@app.route(routes['comment'], methods=['GET', 'POST'])
def comment(id=None):
	dn=get_user_dn(request)
	if request.method == 'POST':
		r = rdb.addComment(request.data,dn)
                publishEvent('mpo_comment',r)
	elif request.method == 'GET':
		if id:
			r = rdb.getRecord('comment',{'uid':id},dn)
		else:
			r = rdb.getRecord('comment',request.args,dn)

	return r


@app.route(routes['metadata']+'/<id>', methods=['GET'])
@app.route(routes['metadata'], methods=['GET', 'POST'])
def metadata(id=None):
	dn=get_user_dn(request)
	if request.method == 'POST':
		r = rdb.addMetadata( request.data, dn)
                publishEvent('mpo_metadata',r)
 	elif request.method == 'GET':
		if id:
			r = rdb.getRecord('metadata', {'uid':id}, dn )
		else:
			r = rdb.getRecord('metadata', request.args, dn )
	return r


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

@app.route(routes['ontology_term']+'/<id>', methods=['GET'])
@app.route(routes['ontology_term'], methods=['GET', 'POST'])
def ontologyTerm(id=None):
	dn=get_user_dn(request)
        print request.data
	if request.method == 'POST':
		r = rdb.addOntologyTerm(request.data,dn)
 	else:
		pass
	return r

@app.route(routes['ontology_instance']+'/<id>', methods=['GET'])
@app.route(routes['ontology_instance'], methods=['GET', 'POST'])
def ontologyInstance(id=None):
	dn=get_user_dn(request)
	result = jsonify(json.loads(request.data),user_dn=dn)
	if request.method == 'POST':
		pass
 	else:
		pass
	return result

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
        
if __name__ == '__main__':
    #adding debug option here, so we can see what is going on.	
    app.debug = False
    #app.run()
    #app.run(host='0.0.0.0', port=8080) #api server
    #app.run(host='0.0.0.0', port=8889) #web ui server
