#!/usr/bin/env python
import time as stime
print('WEBSERVER: timestamp start',stime.time() )
from flask import Flask, render_template, request, jsonify
from flask import redirect, url_for, make_response
from flask.ext.cors import cross_origin
import json
import requests
import datetime
from pprint import pprint
import pydot
import re,os
import math
from authentication import get_user_dn
import urllib
from collections import OrderedDict
try:
    memcache_loaded=True
    import memcache
except ImportError:
    print("MPO Web server error, could not import memcache, page loads may be slower.")
    memcache_loaded=False
from requests_futures.sessions import FuturesSession

app = Flask(__name__)

if memcache_loaded:
    mc = memcache.Client(['127.0.0.1:11211'], debug=0)
else:
    mc = False

MPO_API_SERVER=os.environ['MPO_API_SERVER']
MPO_WEB_CLIENT_CERT=os.environ['MPO_WEB_CLIENT_CERT']
MPO_WEB_CLIENT_KEY=os.environ['MPO_WEB_CLIENT_KEY']
if os.environ.has_key('MPO_EVENT_SERVER'):
    MPO_EVENT_SERVER=os.environ['MPO_EVENT_SERVER']
else:
    print("""
    WARNING: MPO_EVENT_SERVER not set, using localhost\n
    Webclients outside of localhost will not see events.
    """)
    MPO_EVENT_SERVER='localhost' #note this will not work for remote
    #access to webpages

MPO_API_VERSION = 'v0'
API_PREFIX=MPO_API_SERVER+"/"+MPO_API_VERSION
webdebug = True
app.debug = True
print('WEBSERVER: timestamp app started',stime.time() )

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/home')
def index():
    #use asynchronous requests now
    #use grouped requests:
    groupedrequests=False
    print('WEBSERVER: timestamp start index',stime.time() )
    #Need to get the latest information from MPO database here
    #and pass it to index.html template
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    if webdebug:
        print('WEBDEBUG: certargs',certargs)

    ##timing begin
    time_begin = stime.time()

    results=False
    if True:
#        s = requests.session()
        #Establish API session
        s = FuturesSession(max_workers=45) #can use Pooling as well
        a = requests.adapters.HTTPAdapter(max_retries=4)
        s.mount('https://', a)
        s.cert=(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY)
        s.verify=False
        s.headers={'Real-User-DN':dn}

        #send out some requests for preload
        #get quality ontology term uid
        quality_req=s.get("%s/ontology/term?path=/Generic/Status/quality"%(API_PREFIX,), 
                           headers={'Real-User-DN':dn})

        #get UID of Workflow types in ontology
        wf_type_req=s.get("%s/ontology/term?path=/Workflow/Type"%(API_PREFIX,), 
                           headers={'Real-User-DN':dn})

        #get full ontology
        ont_tree_req=s.get("%s/ontology/term/tree"%(API_PREFIX,), 
                           headers={'Real-User-DN':dn})

        #worktreeroot_req=s.get("%s/ontology/term"%(API_PREFIX),params={'path':'Workflow/Type'},
        #                   headers={'Real-User-DN':dn})
        #define call back for fetching ontology tree
        #def ont_tree_cb(sess, resp):


       #get URL variables for this page
        wid=request.args.get('wid')

        #pagination control variables
        wf_range=request.args.get('range')
        wf_page=request.args.get('p')
        wf_rpp=request.args.get('r')
        wf_type=request.args.get('wf_type')

        wf_name=request.args.get('wf_name')
        wf_desc=request.args.get('wf_desc')
        wf_lname=request.args.get('wf_lname')
        wf_fname=request.args.get('wf_fname')
        wf_username=request.args.get('wf_username')

        if wf_page:
            current_page=int(wf_page)
        else:
            current_page=1

        #records per page, 15 is default
        if wf_rpp:
            rpp=int(wf_rpp)
        else:
            rpp=15

        #get total # of workflows
        r=s.get("%s/workflow"%API_PREFIX,  headers={'Real-User-DN':dn}).result()
        #JCW may want to provide resource for this when transfer becomes large
        #().result() needed by FuturesSession to block for async response

        # need to check the status code
        if r.status_code == 401:
            return redirect(url_for('landing', dest_url=request.path))

        rjson = r.json()

        num_wf=len(rjson) # number of workflows returned from api call

        ### get start & end of range of workflows
        if wf_range:
            rlist=wf_range.split(',')
            rmin=int(rlist[0])
            #rmax=int(rlist[1])
            rmax=rmin+rpp-1
        else:
            #default range
            rmin=1
            rmax=rpp

        if wf_type:
            if wf_type != "all":
                #get workflows by specified type, JCW: can just filter initial query
                #CAUTION, may want to actually make this query if we choose not to get all workflows the first time
                #r=s.get("%s/workflow?type=%s"%(API_PREFIX,wf_type,), headers={'Real-User-DN':dn})
                #rjson = r.json()
                rjson = [item for item in rjson if item['type'] == wf_type]
                num_wf=len(rjson) # number of workflows of specified type
                #get range of workflows of specified type
                #r=s.get("%s/workflow?type=%s&range=(%s,%s)"%(API_PREFIX,wf_type,rmin,rmax), headers={'Real-User-DN':dn})
        #else:
            #wf_type=""
            #r=s.get("%s/workflow?range=(%s,%s)"%(API_PREFIX,rmin,rmax), headers={'Real-User-DN':dn})

        rjson=rjson[rmin-1:rmax]
        #calculate number of pages
        num_pages=int(math.ceil(float(num_wf)/float(rpp)))

        results = rjson #r.json()

        ### ontology tree
        #req=requests.get("%s/ontology/term/vocabulary"%(API_PREFIX), **certargs)
        #JCW optimize, ask for just workflow types leaf in ontology tree
        #that's all we are using here
        #its best really to use two queries here.
        #Actually, ont_result is used in index.html to display the whole ontology tree, so this should
        #really be right in index.html: req=requests.get("%s/ontology/term/tree"%(API_PREFIX), **certargs)
        #get workflow types
        #maybe this if we change nodes to be generic worknames=[item['node']['data']['name'] for item in worktree ]
        #JCW JAN 2015, ont request moved to delayed request below
#        worktreeroot=requests.get("%s/ontology/term"%(API_PREFIX),params={'path':'Workflow/Type'}, **certargs).json()
#        wf_ont_tree=requests.get("%s/ontology/term/%s/tree"%(API_PREFIX,worktreeroot[0]['uid']), **certargs).json()


        #Callbacks for use in following loop
        future_list=[]

        def qual_cb(sess, resp, index):
            #verify response and grab value
            qual_data = resp.json()
            if qual_data:
                if qual_data[0]['value']:
                    results[index]['quality']=qual_data[0]['value']
            else:
                results[index]['quality']=''

            if resp.status_code != 200:
                print("Error in index.html in retrieving quality for %s %s"%(qterm_uid,pid))
                results[index]['quality']=''


        def alias_cb(sess, resp, index):
            #verify response and grab value
            cid = resp.json()
            if cid:
                results[index]['alias']=cid['alias']

            if resp.status_code != 200:
                print("Error in index.html in retrieving alias for %s."%(str(results[index])) )
                results[index]['alias']='alias/not/found'


        def comment_cb(sess, resp, index):
            comments = resp.json()
            for temp in comments: #get number of comments, truncate time string
                if temp['time']:
                    thetime=temp['time'][:19]
                    temp['time']=thetime

            results[index]['num_comments']=len(comments)
            results[index]['comments']=comments


        #get needed info from prior requests before going through workflows
        #quality uid
        quality_info=quality_req.result().json()
        if len(quality_info)==1: 
            qterm_uid=quality_info[0]['uid']
        else:
            qterm_uid='0'
            print("Error in webserver, /ontology/term?path=/Generic/Status/quality not found")

        #retrieve workflow type UID from prior request
        worktreeroot = wf_type_req.result().json()
        #issue new request for workflow type data
        wf_ont_tree = s.get("%s/ontology/term/%s/tree"%(API_PREFIX,worktreeroot[0]['uid']),
                           headers={'Real-User-DN':dn})

        #list of workids for grouped requests
        if groupedrequests:
            wids = ','.join([i['uid'] for i in results])
            acm =s.get("%s/workflow/%s/comments"%(API_PREFIX,wids),  headers={'Real-User-DN':dn})
            aal =s.get("%s/workflow/%s/alias"%(API_PREFIX,wids),  headers={'Real-User-DN':dn})
            aqual=s.get("%s/ontology/instance?term_uid=%s&parent_uid=%s"%(API_PREFIX,qterm_uid,wids), 
                        headers={'Real-User-DN':dn})


        #get comments and quality factors for workflows
        for index,i in enumerate(results):        #i is dict, loop through list of workflows
            #if ?wid=<wid> used, show comments for only that workflow
            if wid:
                if wid == i['uid']:
                    results[index]['show_comments'] = 'in' #in is the name of the css class to collapse accordion body
            else:
                results[index]['show_comments'] = ''

            #filter milliseconds out (note, could be more robustly done with datetime functions)
            thetime=results[index]['time'][:19]
            results[index]['time']=thetime

            if not groupedrequests:
                pid=i['uid']
            #get comments for a workflow
                c=s.get("%s/workflow/%s/comments"%(API_PREFIX,pid),  headers={'Real-User-DN':dn},
                    background_callback=lambda sess,resp,index=index: comment_cb(sess,resp,index) )
                future_list.append(c)

            #get alias' for workflow display
                cid=s.get("%s/workflow/%s/alias"%(API_PREFIX,pid),  headers={'Real-User-DN':dn},
                      background_callback=lambda sess,resp,index=index: alias_cb(sess,resp,index) )
                future_list.append(cid)

            #get workflow ontology terms: quality values
                qual_req=s.get("%s/ontology/instance?term_uid=%s&parent_uid=%s"%(API_PREFIX,qterm_uid,pid), 
                           headers={'Real-User-DN':dn}, 
                           background_callback=lambda sess,resp,index=index: qual_cb(sess,resp,index) )
                future_list.append(qual_req)

    #process comments, alias'

    #JCW unroll callbacks here
    for future in future_list:
        future.result()

    if groupedrequests:
        allcomments=acm.result().json() #error checking
        allalias=aal.result().json()
        allqual=aqual.result().json()

        for index,i in enumerate(results):        #i is dict, loop through list of workflows
            comments=allcomments[i['uid']]
            for temp in comments: #get number of comments, truncate time string
                if temp['time']:
                    thetime=temp['time'][:19]
                    temp['time']=thetime

            #comments=allcomments[results[index]['uid']]
            i['num_comments']=len(comments)
            i['comments']=comments
            i['alias']=allalias[i['uid']]['alias']

            if allqual[i['uid']]:
                i['quality']=allqual[i['uid']][0].get('value')
            else:
                i['quality']=''




    ont_result=ont_tree_req.result().json().get('root').get('children')
    wf_type_list = [str(item.keys()[0]) for item in wf_ont_tree.result().json()['Type']['children']]

    #calculate page_created time for display
    time_end = stime.time()
    begin_to_end = time_end - time_begin
    page_created = "%s" %((str(begin_to_end))[:6])

    everything={"page_created":page_created, "results":results, "ont_result":ont_result,
                "rpp":rpp, "current_page":current_page, "wf_type_list":wf_type_list,
                "num_pages":num_pages, "num_wf":num_wf}
    return render_template('index.html', **everything)



#get children of specified uid (object)
@app.route('/ontology/children', methods=['GET'])
@app.route('/ontology/children/<uid>', methods=['GET'])
def ont_children(uid=""):
    #Need to get the latest information from MPO database here
    #and pass it to index.html template
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    s = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=10)
    s.mount('https://', a)
    s.cert=(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY)
    s.verify=False
    s.headers={'Real-User-DN':dn}

    result=""
    if uid:
        req=requests.get("%s/ontology/term/%s/tree"%(API_PREFIX,uid), **certargs)
        ont_tree=req.json()
        children={}
        for key,value in ont_tree.iteritems():
            for n in value:
                if n=="children":
                    for x in value[n]:
                        for k,v in x.iteritems():
                            children[k]=v["data"]
        result = jsonify(children)
    return result

@app.route('/graph', methods=['GET'])
@app.route('/graph/<wid>', methods=['GET'])
@app.route('/graph/<wid>/<format>', methods=['GET'])
def graph(wid="", format="svg"):
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    r=requests.get("%s/workflow/%s/graph"%(API_PREFIX,wid,), **certargs)
    r = r.json()
    nodeshape={'activity':'rectangle','dataobject':'ellipse','workflow':'diamond'}
    graph=pydot.Dot(graph_type='digraph')
    nodes = r['nodes']
    #add workflow node explicitly since in is not a child
    graph.add_node( pydot.Node(wid,label=nodes[wid]['name'],shape=
                               nodeshape[nodes[wid]['type']]))
    for item in r['connectivity']:
        pid=item['parent_uid']
        cid=item['child_uid']
        name=nodes[cid]['name']
        theshape=nodeshape[nodes[cid]['type']]
#        graph.add_node( pydot.Node(cid, label=name, shape=theshape, URL='javascript:postcomment("\N")') )
        graph.add_node( pydot.Node(cid, id=cid, label=name, shape=theshape) )
        if item['child_type']!='workflow':
            graph.add_edge( pydot.Edge(pid, cid) )
    if format == 'svg' :
        svgxml = graph.create_svg()
        ans = svgxml[245:] #removes the svg doctype header so only: <svg>...</svg>
    elif format == 'png' :
        ans = graph.create_png()
    elif format == 'gif' :
        ans = graph.create_gif()
    elif format == 'jpg' :
        ans = graph.create_jpg()
    elif format == 'dot' :
        ans = graph.create_dot()
    else:
        return "unsupported graph format", 404
    ans = ans[:-7] + ans[-7:]
    response = make_response(ans)

    if format == 'svg' :
        response.headers['Content-Type'] = 'text/plain'
        #response.headers['Content-Type'] = 'image/svg+xml'
    elif format == 'png' :
        response.headers['Content-Type'] = 'image/png'
    elif format == 'gif' :
        response.headers['Content-Type'] = 'image/gif'
    elif format == 'jpg' :
        response.headers['Content-Type'] = 'image/jpg'
    elif format == 'dot' :
        response.headers['Content-Type'] = 'text/plain'
    return response


def getsvgxml(wid):
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    r=requests.get("%s/workflow/%s/graph"%(API_PREFIX,wid,), **certargs)
    r = r.json()
    nodeshape={'activity':'rectangle','dataobject':'ellipse','workflow':'diamond'}
    graph=pydot.Dot(graph_type='digraph')
    nodes = r['nodes']
    #add workflow node explicitly since in is not a child
    graph.add_node( pydot.Node(wid,label=nodes[wid]['name'],
                               shape=nodeshape[nodes[wid]['type']]))

    object_order={} #stores numerical order of workflow objects.  used
#for object list display order on workflow detail page
    object_order[0]={ 'uid':wid, 'name':nodes[wid]['name'], 'type':nodes[wid]['type'], 'time':nodes[wid]['time'] }
    count=1
    prev_name=""
    for item in r['connectivity']:
        pid=item['parent_uid']
        cid=item['child_uid']
        name=nodes[cid]['name']
        if prev_name != name:
            #print(str(count) + " " + name)
            object_order[count]={ 'uid':cid, 'name':name, 'type':nodes[cid]['type'], 'time':nodes[cid]['time'] }
            prev_name=name
            count+=1

        theshape=nodeshape[nodes[cid]['type']]
#        graph.add_node( pydot.Node(cid, label=name, shape=theshape, URL='javascript:postcomment("\N")') )
        graph.add_node( pydot.Node(cid, id=cid, label=name, shape=theshape) )
        if item['child_type']!='workflow':
                graph.add_edge( pydot.Edge(pid, cid) )

    ans ={}
    ans[0] = graph.create_svg()
    ans[1] = OrderedDict(sorted(object_order.items(), 
                                key=lambda t: datetime.datetime.strptime(t[1]['time'], 
                                                                         '%Y-%m-%d %H:%M:%S.%f')))
    return ans


@app.route('/connections', methods=['GET'])
@app.route('/connections/<wid>', methods=['GET'])
def connections(wid=""):
  dn = get_user_dn(request)
  certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
  
  begin_to_end = 0;
  cache_id = "connections_%s" %(str(wid))

  ##timing begin
  time_begin = stime.time()
  ##timing end
  if memcache_loaded:
    everything = mc.get(cache_id)
  else:
    everything=False

  if everything:
    #cache hit 
    ##timing begin
    time_end = stime.time()
    begin_to_end = time_end - time_begin
    ##timing end
    everything["page_created"] = "%s" %((str(begin_to_end))[:6])
    return render_template('conn.html', **everything)
  else:
    #cache missed or memcache not loaded
    getsvg=getsvgxml(wid)
    svgdoc=getsvg[0]
    wf_objects=getsvg[1] #dict of workflow elements: name & type
    #JCW Item 2. TODO This list is augmented with additional data below
    #JCW cont. Modify method to add that data on server side when type is svg
    #JCW cont. by embedding data in svg data header <defs/>
    svg=svgdoc[154:] #removes the svg doctype header so only: <svg>...</svg>
    svg=svgdoc[245:] #removes the svg doctype header so only: <svg>...</svg>

    #get workflow info/alias
    wid_req=requests.get("%s/workflow/%s"%(API_PREFIX,wid,), **certargs)
    wid_info=wid_req.json() #JCW Item 1

    #get all data of each activity and dataobject of workflow <wid>

    wf_uid_compid = {}   #for linked workflow compIDs
    num_comment=0
    for key,value in wf_objects.iteritems():
        if value['type'] == "activity":
            req=requests.get("%s/activity/%s"%(API_PREFIX,value['uid'],), **certargs)
            data=req.json()
            if data[0]['time']:
                obj_time=data[0]['time']
                data[0]['time']=obj_time[:19]
            wf_objects[key]['data']=data
        elif value['type'] == "dataobject":
            #get data on each workflow element
            req=requests.get("%s/dataobject?uid=%s"%(API_PREFIX,value['uid'],), **certargs)
            data=req.json()
            if data[0]['time']:
                obj_time=data[0]['time']
                data[0]['time']=obj_time[:19]

            #get linked workflows using uri
            if data[0]['uri'] and len(data[0]['uri']) > 1:
                wf_links_req=requests.get("%s/dataobject?uri=%s"%(API_PREFIX,urllib.quote((data[0]['uri'])),), **certargs)
                if wf_links_req.text != "[]":
                    wf_links=wf_links_req.json()
                    data[0]['wf_link']=wf_links
            wf_objects[key]['data']=data

        meta_req=requests.get("%s/metadata?parent_uid=%s"%
                              (API_PREFIX,value['uid'],), **certargs)
        if meta_req.text != "[]":
            wf_objects[key]['metadata']=meta_req.json()

        comment=requests.get("%s/comment?parent_uid=%s"%(API_PREFIX,value['uid'],), **certargs)

        if comment.text != "[]":
            cm=comment.json()
            k=0
            for i in cm:
                if i['user_uid']:
                    user_req=requests.get("%s/user?uid=%s"%(API_PREFIX,i['user_uid'],), **certargs)
                    user_info=user_req.json()
                    username=user_info[0]['username']
                    cm[k]['user']=username
                if i['time']:
                    cm_time=i['time']
                    cm[k]['time']=cm_time[:19]
                k+=1

            num_comment+=k
            wf_objects[key]['comment']=cm

    if webdebug:
        print("WEBDEBUG: workflow objects")
        pprint(wf_objects)

    nodes=wf_objects
    evserver=MPO_EVENT_SERVER
    everything = {"wid_info":wid_info, "nodes": nodes, "wid": wid, "svg": svg, "num_comment": num_comment, "evserver": evserver }

    if memcache_loaded:
        mc.set(cache_id, everything, time=600)

    ##timing begin
    time_end = stime.time()
    begin_to_end = time_end - time_begin
    ##timing end
  
    everything["page_created"] = "%s" %((str(begin_to_end))[:6]) 
    return render_template('conn.html', **everything)


#created because of cross site scripting issue on ajax calls in development. same as api workflow/<wid> route
@app.route('/workflow', methods=['GET'])
@app.route('/workflow/<wid>', methods=['GET'])
def workflow(wid=""):
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    s = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=10)
    s.mount('https://', a)
    s.cert=(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY)
    s.verify=False
    s.headers={'Real-User-DN':dn}

    req=requests.get("%s/workflow/%s"%(API_PREFIX,wid,), **certargs)
    wf=req.json()
    result=json.dumps(wf)
    return result

#returns json string of nodes w/ their info
@app.route('/nodes', methods=['GET'])
@app.route('/nodes/<wid>', methods=['GET'])
def nodes(wid=""):
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    #get workflow svg xml and object order
    getsvg=getsvgxml(wid)
    wf_objects=getsvg[1] #dict of workflow elements: name & type

    #get workflow info/alias
    wid_req=requests.get("%s/workflow/%s"%(API_PREFIX,wid,), **certargs)
    wid_info=wid_req.json()

    #get all data of each activity and dataobject of workflow <wid>
    num_comment=0
    for key,value in wf_objects.iteritems():
        if value['type'] == "activity":
            req=requests.get("%s/activity/%s"%(API_PREFIX,value['uid'],), **certargs)
            data=req.json()
            if data[0]['time']:
                obj_time=data[0]['time']
                data[0]['time']=obj_time[:19]
            wf_objects[key]['data']=data
        elif value['type'] == "dataobject":
            req=requests.get("%s/dataobject?uid=%s"%(API_PREFIX,value['uid'],), **certargs) #get data on each workflow element
            data=req.json()
            if data[0]['time']:
                obj_time=data[0]['time']
                data[0]['time']=obj_time[:19]
                wf_objects[key]['data']=data

        meta_req=requests.get("%s/metadata?parent_uid=%s"%(API_PREFIX,value['uid'],), **certargs)
        if meta_req.text != "[]":
            wf_objects[key]['metadata']=meta_req.json()

        comment=requests.get("%s/comment?parent_uid=%s"%(API_PREFIX,value['uid'],), **certargs)
        if comment.text != "[]":
            cm=comment.json()
            k=0
            for i in cm:
                if i['user_uid']:
                    user_req=requests.get("%s/user?uid=%s"%(API_PREFIX,i['user_uid'],), **certargs)
                    user_info=user_req.json()
                    username=user_info[0]['username']
                    cm[k]['user']=username
                if i['time']:
                    cm_time=i['time']
                    cm[k]['time']=cm_time[:19]
                k+=1

            num_comment+=k
            wf_objects[key]['comment']=cm

    nodes=json.dumps(wf_objects)
    response = make_response(nodes)
    response.headers['Content-Type'] = 'text/plain'
    return response

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    if request.method == 'POST':
        try:
            form = request.form.to_dict() #gets POSTed form fields as dict
            #r = json.dumps(form)
            search_str=form['query'].strip()

            query_map = {'workflow':{'name':'name', 'description':'description', 'uid':'w_guid',
                                     'composite_seq':'comp_seq', 'time':'creation_time' },
                         'comment' : {'content':'content', 'uid':'cm_guid', 'time':'creation_time',
                                      'type':'comment_type', 'parent_uid':'parent_GUID',
                                      'ptype':'parent_type','user_uid':'u_guid'},
                         'mpousers' : {'username':'username', 'uid':'uuid', 'firstname': 'firstname',
                                       'lastname':'lastname','email':'email','organization':'organization',
                                       'phone':'phone','dn':'dn'},
                         'activity' : {'name':'name', 'description':'description', 'uid':'a_guid',
                                       'work_uid':'w_guid', 'time':'creation_time',
                                       'user_uid':'u_guid','start':'start_time',
                                       'end':'end_time', 'status':'completion_status'},
                         'activity_short' : {'w':'w_guid'},
                         'dataobject' : {'name':'name', 'description':'description', 'uid':'do_guid',
                                         'time':'creation_time', 'user_uid':'u_guid',
                                         'work_uid':'w_guid', 'uri':'uri'},
                         'dataobject_short': {'w':'w_guid'},
                         'metadata' : {'key':'name', 'uid':'md_guid', 'value':'value', 'key_uid':'type',
                                       'user_uid':'u_guid', 'time':'creation_time',
                                       'parent_uid':'parent_guid',
                                       'parent_type':'parent_type'},
                         'metadata_short' : {'n':'name', 'v':'value', 't':'type', 'c':'creation_time' }
                    }

            #wf=requests.get("%s/workflow?uid=%s"%(API_PREFIX,search_str,), **certargs)
            results={}
            if search_str !='':
                for pkey,pvalue in query_map.iteritems():
                    obj_result=[]
                    found=False
                    i=0
                    for ckey in pvalue:
                        if(pkey != "metadata_short" and pkey != "dataobject_short" and pkey != "activity_short"): #these get requests do not work and break the loop
                            if(pkey=="mpousers"): #api route is /user and not /mpousers
                                pkey="user"
                            req=requests.get("%s/%s?%s=%s"%(API_PREFIX,pkey,ckey,search_str,), **certargs)
                            if req.text != "[]":
                                obj_result.extend(req.json())
                                found=True
                                if webdebug:
                                    print('searching route:')
                                    print('%s/%s?%s=%s'%(API_PREFIX,pkey,ckey,search_str))
                    if found:
                        results[pkey]=obj_result

                if webdebug:
                    print('WEBDEBUG: user query')
                    pprint(form)
                    #print('WEBDEBUG: search results')
                    #pprint(results)

        except:
            pass

        return render_template('search.html', query=form, results=results)

    if request.method == 'GET':
        return render_template('search.html')


@app.route('/ontology')
@app.route('/ontology/<uid>', methods=['GET'])
def ontology(uid=False):
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
#    if request.method == 'GET':
#   if uid:
#       req=requests.get("%s/ontology/term/%s"%(API_PREFIX,uid,), **certargs)
#       if req.text != "[]":
#       result=req.text
#       else:
#       result=""
#       response = make_response(result)
#       response.headers['Content-Type'] = 'text/plain'
#       return response
#   else:
#       req=requests.get("%s/ontology/term"%(API_PREFIX), **certargs)
#       result=req.json()
#       pprint(result)
#       return render_template('ontology.html', result=result)
    if request.method == 'GET':
        if uid:
            req=requests.get("%s/ontology/term/%s/vocabulary"%(API_PREFIX,uid,), **certargs)
            if req.text != "[]":
                result=req.text
            else:
                result=""
            response = make_response(result)
            response.headers['Content-Type'] = 'text/plain'
            return response
        else:
            req=requests.get("%s/ontology/term/vocabulary"%(API_PREFIX), **certargs)
            result=req.json()
            ## need to revisit and create a recursive function to get all child levels of ontology terms
            n=0
            for i in result:
                if i['uid']:
                    result[n]['child']=get_child_terms(i['uid'])
                    #tmp_o=result[n]['child']
                    x=0
                    for y in result[n]['child']:
                        if y['uid']:
                            result[n]['child'][x]['child']=get_child_terms(y['uid'])
                        x+=1
                n+=1

            if webdebug:
                pprint(result)
            return render_template('ontology.html', result=result)

    return render_template('ontology.html')

@app.route('/submit_comment', methods=['POST'])
def submit_comment():
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    newc=''
    try:
        form = request.form.to_dict() #gets POSTed form fields as dict; fields: 'parent_uid','comment'
        form['dn'] = dn
        r = json.dumps(form) #convert to json
        if webdebug:
            print('WEBDEBUG: submit comment')
            pprint(r)

        #wid=form['wf_id']

        submit = requests.post("%s/comment"%API_PREFIX, r, **certargs)
        cid = submit.json()
        result = requests.get("%s/comment/%s"%(API_PREFIX,cid['uid']), **certargs)
        newc = result.text
        if webdebug:
            pprint(newc)

    except:
        pass

    return newc
    #return redirect(url_for('index', wid=form['parent_uid'])) # redirects to a refreshed homepage
    #                                                              # after comment submission,
    #                                                              # passes workflow ID so that the
    #                                                              # comments will show for that workflow
    #return redirect(url_for('connections', wid=wid))

@app.route('/ontology_instance', methods=['POST'])
def ontology_instance():
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    data=request.get_json() #dict
    data['dn']=dn
    r = json.dumps(data) #convert to json
    pprint(r)
    submit = requests.post("%s/ontology/instance"%API_PREFIX, r, **certargs)
    pprint(submit)
    results = submit.text
    print(results)

    response = make_response(results)
    response.headers['Content-Type'] = 'text/plain'
    return response


@app.route('/collections')
@app.route('/collections/<uid>', methods=['GET'])
def collections(uid=False):
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    results=False
    if True:
#        s = requests.Session()
        s = FuturesSession(max_workers=45) #can use Pooling as well
        a = requests.adapters.HTTPAdapter(max_retries=10)
        s.mount('https://', a)
        s.cert=(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY)
        s.verify=False
        s.headers={'Real-User-DN':dn}
        rpp=15


        #send out some requests for preload
        #get quality ontology term uid
        quality_req=s.get("%s/ontology/term?path=/Generic/Status/quality"%(API_PREFIX,), 
                           headers={'Real-User-DN':dn})

        #get UID of Workflow types in ontology
        wf_type_req=s.get("%s/ontology/term?path=/Workflow/Type"%(API_PREFIX,), 
                           headers={'Real-User-DN':dn})

        #get full ontology
        ont_tree_req=s.get("%s/ontology/term/tree"%(API_PREFIX,), 
                           headers={'Real-User-DN':dn})


        #get collections now
        rc=s.get("%s/collection"%(API_PREFIX), headers={'Real-User-DN':dn}).result()
        coll_list=rc.json()

        if uid:
            #get members of this collection
            r_coll=s.get("%s/collection/%s/element"%(API_PREFIX,uid), headers={'Real-User-DN':dn})
            results=r_coll.result().json()
            #get name and desc of this specific collection
            this_coll = [ c for c in coll_list if c['uid']==uid ]
            coll_name=this_coll[0]['name']
            coll_desc=this_coll[0]['description']
        else: #get members of first collection
            r_coll=s.get("%s/collection/%s/element"%(API_PREFIX,coll_list[0]['uid']), 
                         headers={'Real-User-DN':dn}).result()
            results=r_coll.json()
            coll_name=coll_list[0]['name']
            coll_desc=coll_list[0]['description']


        #Callbacks for use in following loop
        future_list=[]

        def qual_cb(sess, resp, index):
            #verify response and grab value
            qual_data = resp.json()
            if qual_data:
                if qual_data[0]['value']:
                    results[index]['quality']=qual_data[0]['value']

            if resp.status_code != 200:
                print("Error in index.html in retrieving quality for %s %s"%(qterm_uid,pid))
                results[index]['quality']='0'


        def alias_cb(sess, resp, index):
            #verify response and grab value
            cid = resp.json()
            if cid:
                print('alias_cb',str(cid))
                results[index]['alias']=cid['alias']

            if resp.status_code != 200:
                print("Error in index.html in retrieving alias for %s."%(str(results[index])) )
                results[index]['alias']='alias/not/found'


        def comment_cb(sess, resp, index):
            comments = resp.json()
            for temp in comments: #get number of comments, truncate time string
                if temp['time']:
                    thetime=temp['time'][:19]
                    temp['time']=thetime

            results[index]['num_comments']=len(comments)
            results[index]['comments']=comments


        def workflow_cb(sess, resp, index):
            wf_info=resp.json()
            if len(wf_info)!=0:
                thetime=wf_info[0]['time'][:19]
                wf_info[0]['time']=thetime
            else:
                wf_info={}
            results[index]['workflow']=wf_info


        #get needed info from prior requests before going through workflows
        #quality uid
        quality_info=quality_req.result().json()
        if len(quality_info)==1: 
            qterm_uid=quality_info[0]['uid']
        else:
            qterm_uid='0'
            print("Error in webserver, /ontology/term?path=/Generic/Status/quality not found")

        print("WEBDEBUG: collection results sent to index")
        pprint(results)

        for index,i in enumerate(results):        #i is dict, loop through list of collection elements
            pid=i['uid']
            thetime=results[index]['time'][:19]
            results[index]['time']=thetime

            #get workflow info
            wf_req=s.get("%s/workflow/%s"%(API_PREFIX,pid),  headers={'Real-User-DN':dn},
                    background_callback=lambda sess,resp,index=index: workflow_cb(sess,resp,index) )
            future_list.append(wf_req)

            #get comments for each workflow in a collection
            c=s.get("%s/workflow/%s/comments"%(API_PREFIX,pid),  headers={'Real-User-DN':dn},
                    background_callback=lambda sess,resp,index=index: comment_cb(sess,resp,index) )
            future_list.append(c)

            #get workflow alias #JCW this needs to be extended to object names for general collections
            cid=s.get("%s/workflow/%s/alias"%(API_PREFIX,pid),  headers={'Real-User-DN':dn},
                      background_callback=lambda sess,resp,index=index: alias_cb(sess,resp,index) )
            future_list.append(cid)


            #get workflow ontology terms: quality values
            qual_req=s.get("%s/ontology/instance?term_uid=%s&parent_uid=%s"%(API_PREFIX,qterm_uid,pid), 
                           headers={'Real-User-DN':dn}, 
                           background_callback=lambda sess,resp,index=index: qual_cb(sess,resp,index) )
            future_list.append(qual_req)


        if webdebug:
            print("WEBDEBUG: results sent to index")
            pprint(results)
            #print("WEBDEBUG: ontology_results sent to index")
            #pprint(ont_result)

    #JCW unroll callbacks here
    for future in future_list:
        future.result()

    #retrieve workflow type UID from prior request
    worktreeroot = wf_type_req.result().json()
    #issue new request for workflow type data
    wf_ont_tree = s.get("%s/ontology/term/%s/tree"%(API_PREFIX,worktreeroot[0]['uid']),
                        headers={'Real-User-DN':dn})

    ont_result=ont_tree_req.result().json().get('root').get('children')
    wf_type_list = [str(item.keys()[0]) for item in wf_ont_tree.result().json()['Type']['children']]

    everything={"results":results, "ont_result":ont_result,
                "rpp":rpp, "wf_type_list":wf_type_list,
                "coll_name":coll_name, "coll_desc":coll_desc, "coll_list":coll_list }

    return render_template('collections.html',  **everything)


@app.route('/register', methods=['GET', 'POST'])
def register():
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    if request.method == 'POST':
        try:
            form = request.form.to_dict() #gets POSTed form fields as dict
            form['dn'] = dn

            #validate input
            check="<strong>Missing required fields: </strong>"
            n=0
            for k,v in form.iteritems():
                tmp=v.strip()
                if not tmp:
                    if n>0:
                        check+=', '
                        if k=='firstname':
                            check+="first name"
                        elif k=='lastname':
                            check+="last name"
                        else:
                            check+=k
                        n+=1

            r = json.dumps(form) #convert to json
            result_post = requests.post("%s/user"%API_PREFIX, r, **certargs)
            result=result_post.json() #Convert body Response to json datastructure

            if webdebug:
                print("WEBDEBUG: get form")
                print(form)
                print('WEB DEBUG: result of register request')
                pprint(result)
                print(str(type(result)),len(result))

            if n==0:
                if result.has_key('status'): #JCW for now, check this. But we should have some sort of completion status on all route responses
                    if result['status']=="error":
                        msg = result['error_mesg']
                        if webdebug:
                            print("WEBDEBUG error")
                            pprint(msg)
                        return render_template('register.html', msg=msg, form=form)
                    else:
                        msg="Thank you for registering."
                        if webdebug:
                            print (msg)
                        return render_template('profile.html', msg=msg, result=result)
                else:
                    if webdebug:
                        print('WEBDEBUG: WARNING: in /register no status field in reply')

                    #JCW Should just fail at this point, but for now act as if successful
                    msg="Thank you for registering."
                    if webdebug:
                        print (msg)
                        return render_template('profile.html', msg=msg, result=result)
            else:
                return render_template('register.html', msg=check, form=form)


        except Exception, err:
            print('/register exception', Exception, err) #JCW should redirect to an error handling template here
            pass

    if request.method == 'GET':
        return render_template('register.html', form="_")

@app.route('/profile')
def profile():
    #retrieve user info and display
    return render_template('profile.html')


def is_email(email):
    pattern = '[\.\w]{1,}[@]\w+[.]\w+'
    if re.match(pattern, email):
        return True
    else:
        return False


@app.route("/testfeed")
def testfeed():
    debug_template = """
     <html>
       <head>
       </head>
       <body>
         <h1>Server sent events</h1>
         <div id="event"></div>
         <script type="text/javascript">

         host = "%s/subscribe";

         var eventOutputContainer = document.getElementById("event");
         var evtSrc = new EventSource(host);

         evtSrc.onmessage = function(ev) {
             console.log(ev.data);
             eventOutputContainer.innerHTML += ev.data + '<br>';
         };

         </script>
       </body>
     </html>
    """%MPO_API_SERVER
    return(debug_template)

@app.route('/docs')
def docs():
    return app.send_static_file('docs.html')


def get_child_terms(uid):
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    req=requests.get("%s/ontology/term/%s/vocabulary"%(API_PREFIX,uid), **certargs)

    #if req.text != "[]":
    return req.json()


#add serving host to template args
#listens and publishes all mpo events
@app.route("/testevent")
@cross_origin()
def testevent():
    return render_template('event_server_eg.html',evserver=MPO_EVENT_SERVER)

if __name__ == "__main__":
    #adding debug option here, so we can see what is going on.
    app.debug = True
    #app.run()
    #app.run(host='0.0.0.0', port=8080) #api server
    #app.run(host='0.0.0.0', port=8889) #web server
