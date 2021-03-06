#!/usr/bin/env python
import time as stime
print('WEBSERVER: timestamp start',stime.time() )
from flask import Flask, render_template, request, jsonify
from flask import redirect, url_for, make_response
from flask.ext.cors import cross_origin
import json
import requests
from requests_futures.sessions import FuturesSession #asynch support for performance
import threading
import datetime
from pprint import pprint
import pydot
import re,os
import math
from authentication import get_user_dn, parse_dn
import urllib
from collections import OrderedDict
import ast
import MySQLdb


try:
    import memcache   #for efficient viewing of pages a second time
    memcache_loaded=True
except ImportError:
    print("MPO Web server error, could not import memcache, page loads may be slower.")
    memcache_loaded=False

if memcache_loaded:
    mc = memcache.Client(['127.0.0.1:11211'], debug=0)
else:
    mc = False

#debug logging
webdebug = False  #our inline print statements
if webdebug:
    httploglevel=1
else:
    httploglevel=0

import logging #python module for handling of log messages and levels

    # These two lines enable debugging at httplib level (requests->urllib3->http.client)
    # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # The only thing missing will be the response.body which is not logged.
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client

http_client.HTTPConnection.debuglevel = httploglevel

    # You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.WARN)  #logging.DEBUG , logging.WARN, logging.FATAL
requests_log.propagate = True


#Setup from process environment
MPO_API_SERVER=os.environ.get('MPO_API_SERVER')
if not MPO_API_SERVER:
    print("""
    WARNING: MPO_API_SERVER not set, using localhost:8443\n
    """)
    MPO_API_SERVER='https://localhost:8443'

MPO_WEB_CLIENT_CERT=os.environ.get('MPO_WEB_CLIENT_CERT')
MPO_WEB_CLIENT_KEY=os.environ.get('MPO_WEB_CLIENT_KEY')
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
API_PREFIX = ''
DB_SERVER = ''
CONN_TYPE = ''
USERNAME = ''

USING_UWSGI = os.environ.get('UWSGI_ORIGINAL_PROC_NAME')

#SWIM connection informationa
SWIM_DB_HOST = os.environ.get('SWIM_DB_HOST')
SWIM_DB_NAME = os.environ.get('SWIM_DB_NAME')
SWIM_DB_USER = os.environ.get('SWIM_DB_USER')
SWIM_DB_PW = os.environ.get('SWIM_DB_PASSWORD')


#Establish some asychronous request workers
s = FuturesSession(max_workers=10) #we only want to call this once to avoid cleaning up workers socket connections
a = requests.adapters.HTTPAdapter(max_retries=10,pool_connections=100, pool_maxsize=100, pool_block=True) #defaults are 0,10,10,False
s.mount('https://', a)
s.cert=(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY)
s.verify=False


#Begin the application
app = Flask(__name__)
app.debug = True
print('WEBSERVER: timestamp app started',stime.time() )

@app.before_request
def before_request():
    global DB_SERVER
    global API_PREFIX
    global CONN_TYP
    global USERNAME

    if USING_UWSGI:
        CONN_TYPE='' #no sub-path for uwsgi test server
    else:
        if os.environ['MPO_EDITION'] == "PRODUCTION":
            DB_SERVER=request.cookies.get('db_server')
            if webdebug:
                print ("WEBSERVER: db selected ", DB_SERVER)
                print ("WEBSERVER: COOKIES: ",request.cookies)

            if DB_SERVER=='prod':
                CONN_TYPE='api'
            elif DB_SERVER=='test':
               CONN_TYPE='test-api'  #remove 'test-api' to use with uwsgi api server
            else:
               CONN_TYPE='test-api' #default to allow initial connection, but
           #cookie should be set.
        else:
            CONN_TYPE='demo-api'
            DB_SERVER='demo'
    API_PREFIX=MPO_API_SERVER+"/"+CONN_TYPE+"/"+MPO_API_VERSION
    if webdebug: print("WEBSERVER: prefix",MPO_API_SERVER,API_PREFIX)
    print("WEBSERVER: prefix",MPO_API_SERVER,API_PREFIX)

    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    if webdebug:
        print ('USERNAME: ', USERNAME)
        print ("WEBSERVER: db set to ",DB_SERVER)
        print ('WEBSERVER: api_prefix',API_PREFIX)
        print ('WEBSERVER: certargs',certargs)
        print ('WEBSERVER:  request.environ', request.environ)


    if(request.endpoint != 'register'):
        #Check and redirect to /register if not registered
        is_mpo_user=requests.get("%s/user?dn=%s"%(API_PREFIX,dn), **certargs).json()
        print ('WEBDEBUG, is user:',request.endpoint,dn,str(is_mpo_user) )
        if(len(is_mpo_user)==0):
            parsed_dn=parse_dn(dn)
            print("BEFORE: dn = %s"%dn)
            pprint(parsed_dn)
            dn_email=parsed_dn['emailAddress']
            dn_ou=parsed_dn['O']
            dn_name=parsed_dn['CN']
            t=parsed_dn['CN'].find(' ')
            dn_fname=dn_name[0:t]
            dn_lname=dn_name[t+1:len(dn_name)]
            everything={'firstname': dn_fname, 'lastname': dn_lname, 'email': dn_email, 'organization': dn_ou, 'username': dn_email}
        #if is_mpo_user.status_code == 401:
            return render_template('register.html', **everything)
        USERNAME=is_mpo_user[0]['username']

TEST_API_PREFIX=MPO_API_SERVER+"/"+"test-api"+"/"+MPO_API_VERSION
DEMO_API_PREFIX=MPO_API_SERVER+"/"+"demo-api"+"/"+MPO_API_VERSION
PRODUCTION_API_PREFIX=MPO_API_SERVER+"/"
if not USING_UWSGI:
    PRODUCTION_API_PREFIX+="api"
PRODUCTION_API_PREFIX+="/"+MPO_API_VERSION


def swimdata_connect():
    if SWIM_DB_HOST<>"" and SWIM_DB_USER<>"" and SWIM_DB_PW<>"" and SWIM_DB_NAME:
        conn = MySQLdb.connect(host=SWIM_DB_HOST,
                               user=SWIM_DB_USER,
                               passwd=SWIM_DB_PW,
                               db=SWIM_DB_NAME)
        c = conn.cursor()
        return c, conn

def swimdata_close(conn):
    conn.close()


@app.route('/')
def index():
    everything={"username":USERNAME,"db_server":DB_SERVER}
    return render_template('index.html', **everything)


@app.route('/cart')
def cart():

    #using asynchronous requests now
    global s
    #optionally use grouped requests:
    groupedrequests=False

    print('WEBSERVER: workflows timestamp start index',stime.time() )
    if webdebug: print('WEBSERVER: workflows thread count START : ', threading.active_count() )
    #Need to get the latest information from MPO database here
    #and pass it to index.html template
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    #Set dn for API session
    s.headers={'Real-User-DN':dn, 'Connection':'close' }

    #Get all collections
    collection_list=(s.get("%s/collection"%(API_PREFIX))).result().json()
   # collection_list=(s.get("%s/collection"%(API_PREFIX))).result()

    everything={"username":USERNAME,"db_server":DB_SERVER,"collection_list":collection_list}
    return render_template('cart.html', **everything)


@app.route('/workflows')
def workflows():
    #using asynchronous requests now
    global s
    #optionally use grouped requests:
    groupedrequests=False

    print('WEBSERVER: workflows timestamp start index',stime.time() )
    if webdebug: print('WEBSERVER: workflows thread count START : ', threading.active_count() )
    #Need to get the latest information from MPO database here
    #and pass it to index.html template
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    if webdebug:
        print('WEBDEBUG: workflows certargs',certargs)

    #Set dn for API session
    s.headers={'Real-User-DN':dn, 'Connection':'close' }

    #send out some requests for preload
    #get quality ontology term uid
    quality_req=s.get("%s/ontology/term?path=/Generic/Status/quality"%(API_PREFIX,))

    #get UID of Workflow types in ontology
    wf_type_req=s.get("%s/ontology/term?path=/Workflow/Type"%(API_PREFIX,))

    #get full ontology
    ont_tree_req=s.get("%s/ontology/term/tree"%(API_PREFIX,))

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

    #retrieve workflow type UID from prior request
    worktreeroot = wf_type_req.result().json()
    #issue new request for workflow type data
    if(worktreeroot):
        wf_ont_tree = s.get("%s/ontology/term/%s/tree"%(API_PREFIX,worktreeroot[0]['uid']))

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

    wf_type_list=""
    if(worktreeroot):
        wf_type_list = [str(item.keys()[0]) for item in wf_ont_tree.result().json()['Type']['children']]

    everything={"username":USERNAME,"db_server":DB_SERVER,"wf_type_list":wf_type_list}

    return render_template('workflows_index.html', **everything)

@app.route('/get_ontology_count')
def get_ontology_count():

    #using asynchronous requests now
    global s
    #optionally use grouped requests:
    groupedrequests=False

    print('WEBSERVER: workflows timestamp start index',stime.time() )
    if webdebug: print('WEBSERVER: workflows thread count START : ', threading.active_count() )
    #Need to get the latest information from MPO database here
    #and pass it to index.html template
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    #Set dn for API session
    s.headers={'Real-User-DN':dn, 'Connection':'close' }
    
    #General wf filter user input
    wf_date_val1=request.args.get('wf_date1')
    wf_date_val2=request.args.get('wf_date2')
    wf_name=request.args.get('wf_name')
    wf_desc=request.args.get('wf_description')
    wf_username=request.args.get('wf_username')
    wf_lname=request.args.get('wf_lname')
    wf_fname=request.args.get('wf_fname')

    #Ont filter selection list
    wf_ont_id=request.args.get('wf_ont_id')
    
    #Process wf filter value, store pairs into list to produce the query str
    wf_query_list=[]
    if wf_date_val1 or wf_date_val2:
        if wf_date_val1 is None:
            wf_date_val1=""
        if wf_date_val2 is None:
            wf_date_val2=""
        wf_query_list.append("time="+wf_date_val1+","+wf_date_val2)
    if wf_name:
        wf_query_list.append("name="+wf_name)
    if wf_desc:
        wf_query_list.append("description="+wf_desc)
    if wf_username:
        wf_query_list.append("username="+wf_username)
    if wf_lname:
        wf_query_list.append("lastname="+wf_lname)
    if wf_fname:
        wf_query_list.append("firstname="+wf_fname)
    wf_query='&'.join(wf_query_list) 
    
    #Process ont filter selection input, store pairs into list and create query str
    ont_query=[] 
    if wf_ont_id:
        wf_ont_id_list=json.loads(wf_ont_id)
        for ont in wf_ont_id_list:
            ont=ont.encode('UTF8')
            ont=ast.literal_eval(ont)
            wf_ont_value=ont['value']
            wf_ont_pid=ont['uid']
            ont_query.append({"uid":wf_ont_pid,"value":wf_ont_value})
    ont_params=json.dumps(ont_query) 

    if ont_query:
        ont_list=s.get("%s/ontology/term/count/workflow?term=%s&%s"%(API_PREFIX,ont_params,wf_query))
    else:
        ont_list=s.get("%s/ontology/term/count/workflow?%s"%(API_PREFIX,wf_query))

    return jsonify(ont_list = ont_list.result().json())


@app.route('/get_collections')
def get_collections():

    #using asynchronous requests now
    global s
    #optionally use grouped requests:
    groupedrequests=False

    print('WEBSERVER: workflows timestamp start index',stime.time() )
    if webdebug: print('WEBSERVER: workflows thread count START : ', threading.active_count() )
    #Need to get the latest information from MPO database here
    #and pass it to index.html template
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    #Set dn for API session
    s.headers={'Real-User-DN':dn, 'Connection':'close' }
    
    #Get all collections
    collection_list=s.get("%s/collection"%(API_PREFIX,wf_query))

    return jsonify(collection_list = collection_list.result().json())
    

@app.route('/get_workflows', methods=['POST'])
def get_workflows():
    #using asynchronous requests now
    global s
    #optionally use grouped requests:
    groupedrequests=False

    print('WEBSERVER: workflows timestamp start index',stime.time() )
    if webdebug: print('WEBSERVER: workflows thread count START : ', threading.active_count() )
    #Need to get the latest information from MPO database here
    #and pass it to index.html template
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    if webdebug:
        print('WEBDEBUG: workflows certargs',certargs)

    ##timing begin
    time_begin = stime.time()

    results=False

    #Set dn for API session
    s.headers={'Real-User-DN':dn, 'Connection':'close' }

    #get quality ontology term uid
    quality_req=s.get("%s/ontology/term?path=/Generic/Status/quality"%(API_PREFIX,))

    #pagination control variables
    wf_range=request.args.get('range')
    wf_page=request.args.get('p')
    wf_rpp=request.args.get('r')
    wf_type=request.args.get('wf_type')

    wf_name=request.args.get('wf_name')
    wf_desc=request.args.get('wf_description')
    wf_lname=request.args.get('wf_lname')
    wf_fname=request.args.get('wf_fname')
    wf_username=request.args.get('wf_username')
    wf_date_val1=request.args.get('wf_date1')
    wf_date_val2=request.args.get('wf_date2')
    wf_ont_id=request.args.get('wf_ont_id')
    ont_id=request.args.get('ont_id')
    display=request.args.get('display')

    if wf_page:
        current_page=int(wf_page)
    else:
        current_page=1

    #records per page, 15 is default
    if wf_rpp:
        rpp=int(wf_rpp)
    else:
        rpp=15

    #Process wf filter value, store pairs into list to produce the query str
    wf_query_list=[]
    if wf_date_val1 or wf_date_val2:
        if wf_date_val1 is None:
            wf_date_val1=""
        if wf_date_val2 is None:
            wf_date_val2=""
        wf_query_list.append("time="+wf_date_val1+","+wf_date_val2)
    if wf_name:
        wf_query_list.append("name="+wf_name)
    if wf_desc:
        wf_query_list.append("description="+wf_desc)
    if wf_username:
        wf_query_list.append("username="+wf_username)
    if wf_lname:
        wf_query_list.append("lastname="+wf_lname)
    if wf_fname:
        wf_query_list.append("firstname="+wf_fname)
    wf_query='&'.join(wf_query_list)

    #Process ont filter selection input, store pairs into list and create query str
    ont_query=[]
    if wf_ont_id:
        wf_ont_id_list=json.loads(wf_ont_id)
        for ont in wf_ont_id_list:
            ont=ont.encode('UTF8')
            ont=ast.literal_eval(ont)
            wf_ont_value=ont['value']
            wf_ont_pid=ont['uid']
            ont_query.append({"uid":wf_ont_pid,"value":wf_ont_value})

    ont_params=json.dumps(ont_query)

    #grab wf data
    if ont_query:
        ont_list=s.get("%s/workflow?term=%s&%s"%(API_PREFIX,ont_params,wf_query))
    else:
        ont_list=s.get("%s/workflow?%s"%(API_PREFIX,wf_query))
    r=ont_list.result()

    #JCW may want to provide resource for this when transfer becomes large
    #().result() needed by FuturesSession to block for async response

    # need to check the status code
    if r.status_code == 401:
        return redirect(url_for('index', dest_url=request.path))

    rjson = r.json()

    ### get start & end of range of workflows
    if wf_range:
        rlist=wf_range.split(',')
        rmin=int(rlist[0])
        rmax=rmin+rpp-1
    else:
        #default range
        rmin=1
        rmax=rpp

    if webdebug: print('web debug rjson',rjson, rmin, rmax)
    num_wf=len(rjson)
    rjson=rjson[rmin-1:rmax]
    #calculate number of pages
    num_pages=int(math.ceil(float(num_wf)/float(rpp)))

    results = rjson #r.json()

    if display=="id":
        id_result = [item['uid'] for item in results]
        return jsonify(results = id_result)

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

            if temp['user_uid']:
                user_req=requests.get("%s/user?uid=%s"%(API_PREFIX,temp['user_uid'],), **certargs)
                user_info=user_req.json()
                username=user_info[0]['username']
                temp['username']=username

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

    #list of workids for grouped requests
    if groupedrequests:
        wids = ','.join([i['uid'] for i in results])
        acm =s.get("%s/workflow/%s/comments"%(API_PREFIX,wids))
        aal =s.get("%s/workflow/%s/alias"%(API_PREFIX,wids))
        aqual=s.get("%s/ontology/instance?term_uid=%s&parent_uid=%s"%(API_PREFIX,qterm_uid,wids))

    #get comments and quality factors for workflows
    for index,i in enumerate(results):        #i is dict, loop through list of workflows
        #if ?wid=<wid> used, show comments for only that workflow
        #if wid:
        #    if wid == i['uid']:
        #        results[index]['show_comments'] = 'in' #in is the name of the css class to collapse accordion body
        #else:
        results[index]['show_comments'] = ''
        this_state=getwfstate(i['uid'])
        results[index]['state']=this_state

        #filter milliseconds out (note, could be more robustly done with datetime functions)
        thetime=results[index]['time'][:19]
        results[index]['time']=thetime

        if not groupedrequests:
            pid=i['uid']
            #get comments for a workflow
            c=s.get("%s/workflow/%s/comments"%(API_PREFIX,pid),
                    background_callback=lambda sess,resp,index=index: comment_cb(sess,resp,index) )
            future_list.append(c)

            #get alias' for workflow display
            cid=s.get("%s/workflow/%s/alias"%(API_PREFIX,pid),
                      background_callback=lambda sess,resp,index=index: alias_cb(sess,resp,index) )
            future_list.append(cid)

            #get workflow ontology terms: quality values
            qual_req=s.get("%s/ontology/instance?term_uid=%s&parent_uid=%s"%(API_PREFIX,qterm_uid,pid),
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

    #calculate page_created time for display
    time_end = stime.time()
    begin_to_end = time_end - time_begin
    page_created = "%s" %((str(begin_to_end))[:6])
    
    if display=="table":
        print ""
        print ""
        print ""
        print "NUM WF is ",num_wf
        everything={"username":USERNAME,"db_server":DB_SERVER,"results":results,"page_created":page_created,
                    "rpp":rpp,"current_page":current_page,"num_pages":num_pages, "num_wf":num_wf}
        return render_template('get_workflows.html', **everything)
    elif display=="count":
        return jsonify(num_wf=num_wf)


#get children of specified uid (object)
@app.route('/ontology/children', methods=['GET'])
@app.route('/ontology/children/<uid>', methods=['GET'])
def ont_children(uid=""):
    #Need to get the latest information from MPO database here
    #and pass it to index.html template
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

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
    time_begin = stime.time()

    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    r=requests.get("%s/workflow/%s/graph"%(API_PREFIX,wid,), **certargs)
    r = r.json()
    nodeshape={'activity':'rectangle','dataobject_instance':'ellipse','workflow':'diamond'}
    graph=pydot.Dot(graph_type='digraph')
    nodes = r['nodes']
    #add workflow node explicitly since in is not a child
    graph.add_node( pydot.Node(wid,label=str(nodes[wid].get('name')),shape=
                               nodeshape[nodes[wid]['type']]))

    for item in r['connectivity']:
        pid=item['parent_uid']
        cid=item['child_uid']
        name=str(nodes[cid].get('name'))
        theshape=nodeshape[nodes[cid]['type']]
        graph.add_node( pydot.Node(cid, id=cid, label=name, shape=theshape) )
        if item['child_type']!='workflow':
            graph.add_edge( pydot.Edge(pid, cid) )

    if format == 'svg' :
        svgxml = graph.create_svg()
        ans = svgxml#[245:] #removes the svg doctype header so only: <svg>...</svg>
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
    elif format == 'png' :
        response.headers['Content-Type'] = 'image/png'
    elif format == 'gif' :
        response.headers['Content-Type'] = 'image/gif'
    elif format == 'jpg' :
        response.headers['Content-Type'] = 'image/jpg'
    elif format == 'dot' :
        response.headers['Content-Type'] = 'text/plain'

    time_end = stime.time()
    if webdebug:
        print('WEB_SERVER:: graph time',str(time_end-time_begin) )
    return response


def getsvgxml(wid):
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    r=requests.get("%s/workflow/%s/graph"%(API_PREFIX,wid,), **certargs)
    r = r.json()
    nodeshape={'activity':'rectangle','dataobject_instance':'ellipse','workflow':'diamond'}
    graph=pydot.Dot(graph_type='digraph')
    nodes = r['nodes']
    #add workflow node explicitly since in is not a child
    graph.add_node( pydot.Node(wid,label=str(nodes[wid].get('name')),
                               shape=nodeshape[nodes[wid]['type']]))

    object_order={} #stores numerical order of workflow objects.  used
    #for object list display order on workflow detail page
    object_order[0]={ 'uid':wid, 'name':str(nodes[wid].get('name')), 'type':nodes[wid]['type'], 'time':nodes[wid]['time'] }
    count=1
    prev_name=""
    prev_cid=""
    for item in r['connectivity']:
        pid=item['parent_uid']
        cid=item['child_uid']
        name=str(nodes[cid].get('name'))
        if prev_cid != cid:
            object_order[count]={ 'uid':cid, 'name':name, 'type':nodes[cid]['type'], 'time':nodes[cid]['time'] }
            prev_name=name
            prev_cid=cid
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

def getwfstate(wid):
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    #get term_uid for State
    r=requests.get("%s/ontology/term?path=/Workflow/Status/State"%(API_PREFIX,), **certargs)
    r=r.json()
    if r:
        state_uid = r[0]['uid']
        #get all instances with assigned state value
        r=requests.get("%s/ontology/instance?term_uid=%s"%(API_PREFIX,state_uid,), **certargs)
        result = r.json()
        for item in result:
            #matches workflow id
            if item['parent_uid'] == wid:
                return item['value']



@app.route('/connections', methods=['GET'])
@app.route('/connections/<wid>', methods=['GET'])
def connections(wid=""):
  import lxml.etree as et

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
    wfstate=getwfstate(wid)

    svgdoc=getsvg[0]

    wf_objects=getsvg[1] #dict of workflow elements: name & type
    #JCW Item 2. TODO This list is augmented with additional data below
    #JCW cont. Modify method to add that data on server side when type is svg
    #JCW cont. by embedding data in svg data header <defs/>

    #parse to get just the root element, assumed to be <svg>
    #svg=svgdoc[154:] #removes the svg doctype header so only: <svg>...</svg>
    #svg=svgdoc[245:] #removes the svg doctype header so only: <svg>...</svg>
    #this parsing could be moved into getsvgxml function too.
    svgxml=et.fromstring(svgdoc) #get root document, drops DOCTYPE and leading comments
    ns,tag=svgxml.tag[1:].split('}')
    if not tag=='svg':
        print ('WEBDEBUG: connection error, svg tag not found')
        #render error template or set svg to error svg
        svg = """
        <svg height="300" width="340">
          <text x="80" y="150" fill="red">Error in graph rendering!</text>
        </svg>
        """
        graphname='text'
    else:
        graphname =  svgxml.getchildren()[0].attrib['id']
        svg = et.tostring(svgxml)

    #get workflow info/alias
    wid_req=requests.get("%s/workflow/%s"%(API_PREFIX,wid,), **certargs)
    wid_info=wid_req.json() #JCW Item 1
    wid_type=wid_info[0]['type']

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
        elif value['type'] == "dataobject_instance":
            #get data on each workflow element
            req=requests.get("%s/dataobject/%s"%(API_PREFIX,value['uid'],), **certargs)
            data=req.json()

            if data[0]['time']:
                obj_time=data[0]['time']
                data[0]['time']=obj_time[:19]

            #get linked workflows using uri
            if data[0]['do_info']['uri'] and len(data[0]['do_info']['uri']) > 1:
                wf_links_req=requests.get("%s/workflow?do_uri=%s"%(API_PREFIX,urllib.quote((data[0]['do_info']['uri'])),), **certargs)
                if (wf_links_req):
                    wf_links=wf_links_req.json()
                    data[0]['wf_link']=wf_links

            wf_objects[key]['data']=data

        meta_req=requests.get("%s/metadata?parent_uid=%s"%
                              (API_PREFIX,value['uid'],), **certargs)
        if meta_req.text != "[]":
            wf_objects[key]['metadata']=meta_req.json()

        comment=requests.get("%s/comment?parent_uid=%s"%(API_PREFIX,value['uid'],), **certargs)

        if comment.text != "[]":
            if webdebug:
                print("WEBDEBUG comment: ",str(comment.content))
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

    #Grab a list of collections - first, get parent id
    r=requests.get("%s/collection?element_uid=%s"%(API_PREFIX,wid), **certargs)
    if(r):
      # grab all collections for now
      collections=r.json()
      rc=requests.get("%s/collection"%(API_PREFIX), **certargs)
      if(rc):
         coll_list=rc.json()
      # loop through parents
      for item in collections:
         coll_uid=item['parent_uid']
         for citem in coll_list:
            if(citem['uid']==coll_uid):
               item['name']=citem['name']
               item['description']=citem['description']
               item['collection_uid']=citem['uid']
               break

    nodes=wf_objects
    evserver=MPO_EVENT_SERVER
    swimdata=""
    runId=""
    if wid_type=="SWIM":
       #grab SWIM runid 
       r=requests.get("%s/metadata"%(API_PREFIX), **certargs)
       if(r):
          meta_list=r.json()
          for mitem in meta_list:
             if wid==mitem['parent_uid'] and "RunID" in mitem['key']:
                runId=mitem['value']
 
       if runId!="":
          try:
              c, conn = swimdata_connect()
              if c and conn:
                  c.execute("SELECT date, seqnum, eventtype, code, state, walltime, phystimestamp, comment FROM monitor_simulation where portal_runid='"+runId+"' order by seqnum desc")
                  swimdata=c.fetchall()
                  swimdata_close(conn)
          except Exception as e:
              pass

    everything = {"username":USERNAME, "db_server":DB_SERVER, "wid_info":wid_info, "wf_state":wfstate, "swimdata": swimdata,
                  "nodes": nodes, "wid": wid, "svg": svg,  "evserver": evserver, "graphname":graphname, "coll_list":collections}
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
                         'dataobject' : {'name':'name', 'description':'description','uri':'uri','uid':'do_guid',
                                         'source_uid':'source_guid','time':'creation_time', 'user_uid':'u_guid'},
                         #'dataobject_instance' : {'do_uid':'do_guid', 'uid':'doi_guid',
                         #                         'time':'creation_time', 'user_uid':'u_guid','work_uid':'w_guid'},
                         #'dataobject_instance_short': {'w':'w_guid'},
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
                    i=0
                    found=False
                    for ckey in pvalue:
                        if(pkey != "metadata_short" and pkey != "dataobject_short" and pkey != "activity_short"): #these get requests do not work and break the loop
                            if(pkey=="mpousers"): #api route is /user and not /mpousers
                                pkey="user"
                            req=requests.get("%s/%s?%s=%s"%(API_PREFIX,pkey,ckey,search_str,), **certargs)
                            if req.status_code == 500:
                                if webdebug:
                                   print "Error in webserver, 500 from search api route: %s/%s?%s=%s"%(API_PREFIX,pkey,ckey,search_str,)
                            else:
                                if req.text != "[]":
                                   obj_result.extend(req.json())
                                   found=True
                                   if webdebug:
                                        print('Searching route - data returned:')
                                        print('%s/%s?%s=%s'%(API_PREFIX,pkey,ckey,search_str))
                    if found:
                        results[pkey]=obj_result

        except:
            pass


        if webdebug:
            print('WEBDEBUG: user query')
            pprint(form)
            print('WEBDEBUG: result')
            print results

        return render_template('search.html', query=form, results=results, db_server=DB_SERVER, username=USERNAME)

    if request.method == 'GET':
        return render_template('search.html', db_server=DB_SERVER, username=USERNAME)


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

@app.route('/submit_db', methods=['POST'])
def submit_db():
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    newc=''
    redirect_to_index = redirect(url_for('workflows'))
    response = app.make_response(redirect_to_index )

    try:
        form = request.form.to_dict() #gets POSTed form fields as dict; fields: 'parent_uid','comment'
        form['dn'] = dn
        r = json.dumps(form) #convert to json
        if webdebug:
            print('WEBDEBUG: submit db')
            pprint(r)
            print(form['db'])
        response.set_cookie('db_server',value=form['db'])
        return redirect_to_index

    except:
        pass

    return redirect_to_index
    #return redirect(url_for('index', wid=form['parent_uid'])) # redirects to a refreshed homepage
    #                                                              # after comment submission,
    #                                                              # passes workflow ID so that the
    #                                                              # comments will show for that workflow
    #return redirect(url_for('connections', wid=wid))



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
        if submit.status_code == 401:
            return "401"

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

@app.route('/create_collection', methods=['POST'])
def create_collection():
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    try:
        data = request.form.to_dict()
        data['elements']=request.form.getlist('elements[]')
        submit = requests.post("%s/collection"%API_PREFIX, json.dumps(data), **certargs)
    
        if submit.status_code == 401:
            return "401"
        return "200"
    except:
        pass
    return ''


@app.route('/add_to_collection', methods=['GET','POST'])
def add_to_collection():
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    try:
        data = request.form.to_dict()
        data['dn']=dn
        data['elements']=data['oid']
        r=json.dumps(data)
        cid=data['cid']
        response=requests.post("%s/collection/%s/element"%(API_PREFIX,cid), r, **certargs)
        if response.status_code == 401:
            return "401"
        return "200"

    except:
        pass

@app.route('/delete_from_collection', methods=['GET','POST'])
def delete_from_collection():
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    try:
        data = request.form.to_dict()
        data['dn']=dn
        data['elements']=data['oid']
        r=json.dumps(data)
        cid=data['cid'].strip()
        oid=data['oid'].strip()
        response=requests.delete("%s/collection/%s/element/%s"%(API_PREFIX,cid,oid), **certargs)
        if response.status_code == 401:
            return "401"
        return "200"

    except:
        pass


@app.route('/collections')
@app.route('/collections/<uid>', methods=['GET'])
def collections(uid=False):
    global s
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    results=[]
    if True:
        s.headers={'Real-User-DN':dn}
        rpp=15


        #send out some requests for preload
        #get quality ontology term uid
        quality_req=s.get("%s/ontology/term?path=/Generic/Status/quality"%(API_PREFIX,))

        #get UID of Workflow types in ontology
        wf_type_req=s.get("%s/ontology/term?path=/Workflow/Type"%(API_PREFIX,))

        #get full ontology
        ont_tree_req=s.get("%s/ontology/term/tree"%(API_PREFIX,))

        #get collections now
        rc=s.get("%s/collection"%(API_PREFIX,)).result()
        coll_list=rc.json()

        coll_name="None"
        coll_desc="No collections found"

        ont_result=[]
        wf_type_list=[]
        coll_username=""
        coll_time=""

        if uid:
            #get members of this collection
            r_coll=s.get("%s/collection/%s/element"%(API_PREFIX,uid))
            results=r_coll.result().json()
            #get name and desc of this specific collection
            this_coll = [ c for c in coll_list if c['uid']==uid ]
            if len(this_coll)>0:
                coll_name=this_coll[0]['name']
                coll_desc=this_coll[0]['description']
                coll_username=this_coll[0]['username']
                coll_time=this_coll[0]['time'][:19]
        else: #get members of first collection
            if len(coll_list)>0:
                coll_name=coll_list[0]['name']
                coll_desc=coll_list[0]['description']

            everything={
                "username":USERNAME,"db_server":DB_SERVER, "rpp":rpp,
                "coll_name":coll_name, "coll_desc":coll_desc, "coll_list":coll_list}
            return render_template('collections_index.html',  **everything)

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

        def collection_item_cb(sess, resp, index):
            info=resp.json()

            if((len(info))>1):
                info[0]=info
                r=s.get("%s/metadata?parent_uid=%s"%(API_PREFIX,info[0]['uid']))
                info[0]['metadata']=r.result().json()
            if len(info)!=0:
                thetime=info[0]['time'][:19]
                info[0]['time']=thetime
                r=s.get("%s/metadata?parent_uid=%s"%(API_PREFIX,info[0]['uid']))
                info[0]['metadata']=r.result().json()
            else:
                info={}
            results[index]['citem']=info


        #get needed info from prior requests before going through workflows
        #quality uid
        quality_info=quality_req.result().json()
        if len(quality_info)==1:
            qterm_uid=quality_info[0]['uid']
        else:
            qterm_uid='0'
            print("Error in webserver, /ontology/term?path=/Generic/Status/quality not found")
        if webdebug:
                print("WEBDEBUG: collection results sent to index")
                pprint(results)

        for index,i in enumerate(results):        #i is dict, loop through list of collection elements
            print('web server collections',i)
            pid=i['uid']
            thetime=results[index]['time'][:19]
            results[index]['time']=thetime

            #Process workflow items
            if results[index]['type']=="workflow":
                #get workflow info
                wf_req=s.get("%s/workflow/%s"%(API_PREFIX,pid),
                             background_callback=lambda sess,resp,index=index: collection_item_cb(sess,resp,index) )
                future_list.append(wf_req)
                #get comments for each workflow in a collection
                c=s.get("%s/workflow/%s/comments"%(API_PREFIX,pid),
                        background_callback=lambda sess,resp,index=index: comment_cb(sess,resp,index) )
                future_list.append(c)
                #get workflow alias #JCW this needs to be extended to object names for general collections
                cid=s.get("%s/workflow/%s/alias"%(API_PREFIX,pid),
                          background_callback=lambda sess,resp,index=index: alias_cb(sess,resp,index) )
                future_list.append(cid)

            #Process dataobject
            elif results[index]['type']=="dataobject":
                #get node info
                wf_req=s.get("%s/dataobject/%s"%(API_PREFIX,pid),
                             background_callback=lambda sess,resp,index=index: collection_item_cb(sess,resp,index) )
                future_list.append(wf_req)
                #get comments for each workflow in a collection
                c=s.get("%s/comment?parent_uid=%s"%(API_PREFIX,pid),
                        background_callback=lambda sess,resp,index=index: comment_cb(sess,resp,index) )
                future_list.append(c)

            #Process dataobject
            elif results[index]['type']=="dataobject_instance":
               #get node info
                wf_req=s.get("%s/dataobject/%s"%(API_PREFIX,pid),
                             background_callback=lambda sess,resp,index=index: collection_item_cb(sess,resp,index) )
                future_list.append(wf_req)
                #get comments for each workflow in a collection
                c=s.get("%s/comment?parent_uid=%s"%(API_PREFIX,pid),
                        background_callback=lambda sess,resp,index=index: comment_cb(sess,resp,index) )
                future_list.append(c)
                wf_id=wf_req.result().json()[0]['work_uid']
                doi_wf=s.get("%s/workflow/%s"%(API_PREFIX,wf_id)).result()
                doi_wf_cid=str(doi_wf.json()[0]['username'])+" / "+str(doi_wf.json()[0]['name'])+" / "+str(doi_wf.json()[0]['composite_seq'])
                results[index]['wf_cid']=doi_wf_cid

            elif results[index]['type']=="collection":
                #get node info
                wf_req=s.get("%s/collection/%s"%(API_PREFIX,pid),
                             background_callback=lambda sess,resp,index=index: collection_item_cb(sess,resp,index) )
                future_list.append(wf_req)
                #get comments for each workflow in a collection
                c=s.get("%s/comment?parent_uid=%s"%(API_PREFIX,pid),
                        background_callback=lambda sess,resp,index=index: comment_cb(sess,resp,index) )
                future_list.append(c)

            #get workflow ontology terms: quality values
            qual_req=s.get("%s/ontology/instance?term_uid=%s&parent_uid=%s"%(API_PREFIX,qterm_uid,pid),
                           background_callback=lambda sess,resp,index=index: qual_cb(sess,resp,index) )
            future_list.append(qual_req)


        if webdebug:
            print("WEBDEBUG: results sent to index")
            pprint(results)

    #JCW unroll callbacks here
    for future in future_list:
        future.result()

    #retrieve workflow type UID from prior request
    worktreeroot = wf_type_req.result().json()
    #issue new request for workflow type data
    if(worktreeroot):
        wf_ont_tree = s.get("%s/ontology/term/%s/tree"%(API_PREFIX,worktreeroot[0]['uid']))


    ont_result_json=ont_tree_req.result().json()
    if(ont_result_json):
        ont_result=ont_result_json.get('root').get('children')
    if(worktreeroot):
        wf_type_list = [str(item.keys()[0]) for item in wf_ont_tree.result().json()['Type']['children']]

    #close the requests connection
    s.close()

    if webdebug:
        print("WEBDEBUG: collection results sent to index")
        pprint(results)

    everything={"username":USERNAME,"db_server":DB_SERVER, "results":results, "ont_result":ont_result,
                "rpp":rpp, "wf_type_list":wf_type_list,
                "coll_name":coll_name, "coll_desc":coll_desc,
                "coll_username":coll_username, "coll_time":coll_time, "uid":uid  }

    return render_template('collections.html',  **everything)


@app.route('/dataobjects')
@app.route('/dataobjects/<uid>', methods=['GET'])
def dataobject(uid=False):
    global s
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    results=False
    if True:
        s.headers={'Real-User-DN':dn}
        rpp=15

        #send out some requests for preload
        #get quality ontology term uid
        quality_req=s.get("%s/ontology/term?path=/Generic/Status/quality"%(API_PREFIX,))

        #get UID of Workflow types in ontology
        wf_type_req=s.get("%s/ontology/term?path=/Workflow/Type"%(API_PREFIX,))

        #get full ontology
        ont_tree_req=s.get("%s/ontology/term/tree"%(API_PREFIX,))

        quality_info=quality_req.result().json()
        if len(quality_info)==1:
            qterm_uid=quality_info[0]['uid']
        else:
            qterm_uid='0'
            print("Error in webserver, /ontology/term?path=/Generic/Status/quality not found")

        if uid:
            #Grab specified dataobject
            r=s.get("%s/dataobject/%s"%(API_PREFIX,uid))
            if(r):
               results=r.result().json()
               if "do_info" in results[0]:
                   username=results[0]['username']
                   uri=results[0]['do_info']['uri']
                   name=results[0]['do_info']['name']
                   time=results[0]['do_info']['time'][:19]
                   desc=results[0]['do_info']['description']
               else:
                   username=results[0]['username']
                   uri=results[0]['uri']
                   name=results[0]['name']
                   time=results[0]['time'][:19]
                   desc=results[0]['description']

               wf_links_req=requests.get("%s/workflow?do_uri=%s"%(API_PREFIX,urllib.quote(uri)), **certargs)
               if (wf_links_req):
                   wf_links=wf_links_req.json()
                   workflows=wf_links
                   for item in workflows['result']:
                      #filter milliseconds out (note, could be more robustly done with datetime functions)
                      thetime=item['time'][:19]
                      item['time']=thetime
                      pid=item['uid']
                      #get comments for a workflow
                      comment=s.get("%s/workflow/%s/comments"%(API_PREFIX,pid)).result().json()
                      item['comments']=comment
                      item['num_comments']=len(comment)

                      #get quality info for a workflow
                      qual_req=s.get("%s/ontology/instance?term_uid=%s&parent_uid=%s"%(API_PREFIX,qterm_uid,pid))

                      qual_data = qual_req.result().json()
                      if qual_data:
                         if qual_data[0]['value']:
                             item['quality']=qual_data[0]['value']
                      else:
                         item['quality']=''

            #Grab a list of collections - first, get parent id
            r=s.get("%s/collection?element_uid=%s"%(API_PREFIX,uid))
            if(r):
              # grab all collections for now
              rc=s.get("%s/collection"%(API_PREFIX) )
              if(rc):
                  coll_list=rc.result().json()
              # loop through parents
              collections=r.result().json()
              for item in collections:
                 coll_uid=item['parent_uid']
                 for citem in coll_list:
                    if(citem['uid']==coll_uid):
                       item['name']=citem['name']
                       item['description']=citem['description']
                       item['collection_uid']=citem['uid']
                       break
        else:
            #Grab a list of all dataobjects
            dataobj_list=""
            rc=s.get("%s/dataobject"%(API_PREFIX)).result()
            if(rc):
                dataobj_list=rc.json()
                for temp in dataobj_list:
                    if temp['time']:
                        thetime=temp['time'][:19]
                        temp['time']=thetime

            #close the connection
            s.close()
            everything={"username":USERNAME,"db_server":DB_SERVER,"rpp":rpp, "coll_list":dataobj_list }

            return render_template('dataobject_index.html',  **everything)

    if webdebug:
        print("WEBDEBUG: results sent to index")
        pprint(results)

    worktreeroot = wf_type_req.result().json()


    r=s.get("%s/metadata?parent_uid=%s"%(API_PREFIX,uid))
    if(r):
        metadata=r.result().json()

    #close the connection
    s.close()

    everything={"username":USERNAME,"db_server":DB_SERVER, "workflows":workflows,
                "rpp":rpp, "coll_list":collections,
                "name":name, "desc":desc, "metadata": metadata,
                "username":username, "time":time, "uri":uri, "uid":uid  }

    return render_template('dataobject.html',  **everything)



@app.route('/get_server_data', methods=['POST'])
def get_server_data(uid=False):
    global s
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    s.headers={'Real-User-DN':dn}

    #Get request values - this should match up with the order of columns in HTML
    columns=["uid", "name", "description", "uri", "source_uid", "username", "time"]

    form = request.form.to_dict() #gets POSTed form fields as dict
    start=int(form['start'])
    length=int(form['length'])
    end=start+length
    draw=int(form['draw'])
    order_by=int(form['order[0][column]'])
    order_dir=(form['order[0][dir]'])
    #overall serach value
    search_str=(form['search[value]'])
    i=0;

    #search per column - columnsx4][search][value]
#    for c in columns:
#       col_searchable=str(request.args.get("columns[%s][searchable]"%(i,)))
#       col_search_str=str(request.args.get("columns[%s][search][value]"%(i,)))
#       i=i+1

#       print ("COL: ",c," searchable: ",col_searchable, " AND VALUE: ", col_search_str)

#       if(col_search_str<>"None"):
#          rc=s.get("%s/dataobject?%s=%s"%(API_PREFIX,c,col_search_str,), headers={'Real-User-DN':dn}).result()
#          if(rc):
#               data_list=rc.json();

    #Grab a list of all dataobjects
    data_list=[]
    if(search_str):
        for c in columns:
            this_list=[]
#            rc=s.get("%s/dataobject?uri=%s"%(API_PREFIX,search_str,), headers={'Real-User-DN':dn}).result()
            rc=s.get("%s/dataobject?%s=%s"%(API_PREFIX,c,search_str,)).result()

            if(rc):
               this_list=rc.json()
               if("message" in this_list):
                   this_list=[]
               else:
                   data_list+=this_list
#                   in_data_list=set(data_list)
#                   in_this_list=set(this_list)
#                   new_to_add=in_this_list-in_data_list
#                   data_list=data_list+list(new_to_add)
            #   data_list=rc.json()
    else:
        #rc=s.get("%s/dataobject?instance=False"%(API_PREFIX), headers={'Real-User-DN':dn}).result()
        rc=s.get("%s/dataobject"%(API_PREFIX)).result()
        if(rc):
            data_list=rc.json()
            #for i in range(len(data_list)):
            #   data_list[i]['name']=data_list[i]['name']
            #   data_list[i]['uri']=data_list[i]['uri']
            #   data_list[i]['description']=data_list[i]['description']
            #   date_list[i]['source_uid']=data_list[i]['source_uid']

    if(data_list):
        total=len(data_list)
#        keylist = data_list.keys()

        if("message" in data_list):
            data_list=[]
        if(data_list):
            #order list
            if(order_dir=="desc"):
                data_list.sort(key=lambda e: e[columns[order_by]], reverse=True)
            else:
                data_list.sort(key=lambda e: e[columns[order_by]])
            data_list=data_list[start:end]
            for temp in data_list:
               if temp['time']:
                   thetime=temp['time'][:19]
                   temp['time']=thetime

    return jsonify(draw=draw, recordsTotal=total, recordsFiltered=total, data=data_list)

@app.route('/register', methods=['GET', 'POST'])
def register():
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    if webdebug: print('register dn',dn, certargs)
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

            # check if users already in db, add new users only
            in_prod=requests.get("%s/user?dn=%s"%(PRODUCTION_API_PREFIX,dn), **certargs).json()
            if(len(in_prod)==0):
                print "ADDING TO PROD"
                result_post = requests.post("%s/user"%PRODUCTION_API_PREFIX, r, **certargs)
            # if using uwsgi there is only the production db
            if not USING_UWSGI:
                in_test=requests.get("%s/user?dn=%s"%(TEST_API_PREFIX,dn), **certargs).json()
                if(len(in_test)==0):
                    print "ADDING TO TEMP"
                    result_post = requests.post("%s/user"%TEST_API_PREFIX, r, **certargs)
                in_demo=requests.get("%s/user?dn=%s"%(DEMO_API_PREFIX,dn), **certargs).json()
                if(len(in_demo)==0):
                    print"ADDING TO DEMO"
                    result_post = requests.post("%s/user"%DEMO_API_PREFIX, r, **certargs)
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
                        return render_template('index.html', msg=msg, result=result)
                else:
                    if webdebug:
                        print('WEBDEBUG: WARNING: in /register no status field in reply')

                    #JCW Should just fail at this point, but for now act as if successful
                    msg="Thank you for registering."
                    if webdebug:
                        print (msg)
                    return render_template('index.html', msg=msg, result=result)
            else:
                return render_template('register.html', msg=check, form=form)


        except Exception, err:
            print('/register exception', Exception, err) #JCW should redirect to an error handling template here
            pass

    if request.method == 'GET':
        #Check and redirect to /register if not registered
        is_mpo_user=requests.get("%s/user?dn=%s"%(API_PREFIX,dn), **certargs)
        if(is_mpo_user):
            is_mpo_user=is_mpo_user.json()
            if(len(is_mpo_user)==0): #Not registered, display form
                dn = get_user_dn(request)
                parsed_dn=parse_dn(dn)
                dn_email=parsed_dn['emailAddress']
                dn_ou=parsed_dn['OU']
                dn_name=parsed_dn['CN']
                t=parsed_dn['CN'].find(' ')
                dn_fname=dn_name[0:t]
                dn_lname=dn_name[t+1:len(dn_name)]
                everything={'firstname': dn_fname, 'lastname': dn_lname, 'email': dn_email, 'organization': dn_ou, 'username': dn_email}
                return render_template('register.html', **everything)
            else:  #Already registered, disable form from template
                return render_template('register.html', registered=1)

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
