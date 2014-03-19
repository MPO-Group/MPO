#!/usr/bin/env python

from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
from flask.ext.cors import cross_origin
import json
import requests
import time
import datetime
from pprint import pprint
import pydot
import re,os
import math
from authentication import get_user_dn

app = Flask(__name__)

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
    MPO_EVENT_SERVER='localhost' #note this will not work for remote access to webpages

MPO_API_VERSION = 'v0'
API_PREFIX=MPO_API_SERVER+"/"+MPO_API_VERSION
webdebug=True
app.debug = False

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/home')
def index():
    #Need to get the latest information from MPO database here
    #and pass it to index.html template 
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    if webdebug:
	print('WEBDEBUG: certargs',certargs)

    results=False
    try:
	s = requests.Session()
        s.cert=(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY)
	s.verify=False
	s.headers={'Real-User-DN':dn}
	wid=request.args.get('wid')
	wf_name=request.args.get('wf_name')
	
	#pagination control variables
	wf_range=request.args.get('range')
	wf_page=request.args.get('p')
	wf_rpp=request.args.get('r')

        if webdebug:
	    print('WEBDEBUG: requests in index route',API_PREFIX,wf_name)
	#req=request.args.to_dict()

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
	r=s.get("%s/workflow"%API_PREFIX,  headers={'Real-User-DN':dn}) 

        # need to check the status code
        if r.status_code == 401:
            return redirect(url_for('landing', dest_url=request.path))

	rjson = r.json()
	num_wf=len(rjson) # number of workflows returned from api call

	#get start & end of range
	if wf_range:
	    rlist=wf_range.split(',')
	    rmin=int(rlist[0])
	    #rmax=int(rlist[1])
	    rmax=rmin+rpp-1
	else:
	    #default range
	    rmin=1
	    rmax=rmin+rpp-1

	if wf_name:
	    #get workflows by specified name
	    r=s.get("%s/workflow?name=%s"%(API_PREFIX,wf_name,),  headers={'Real-User-DN':dn})
	    rjson = r.json()
	    num_wf=len(rjson) # number of workflows of specified name
	    #get range of workflows of specified name
	    r=s.get("%s/workflow?name=%s&range=(%s,%s)"%(API_PREFIX,wf_name,rmin,rmax),  headers={'Real-User-DN':dn})
	else:
	    r=s.get("%s/workflow?range=(%s,%s)"%(API_PREFIX,rmin,rmax),  headers={'Real-User-DN':dn})
	
	#calculate number of pages
	num_pages=int(math.ceil(float(num_wf)/float(rpp)))

        if webdebug:
	    print('WEBDEBUG: after requests in index route',API_PREFIX,wf_name)
	    
	results = r.json()

	#get comments
	index=0
	for i in results:	#i is dict
		if wid:
			if wid == i['uid']:
				results[index]['show_comments'] = 'in' #in is the name of the css class to collapse accordion body
		else:
			results[index]['show_comments'] = ''
                pid=i['uid']
                c=s.get("%s/comment?parent_uid=%s"%(API_PREFIX,pid),  headers={'Real-User-DN':dn})
		comments = c.json()

		num_comments=0
                if comments == None: #replace null reply in requests body with empty list so below logic still works
                    comments=[]
                for temp in comments: #get number of comments, truncate time string
                    num_comments+=1
                    if temp['time']:
                        time=temp['time'][:16]
                        temp['time']=time

		results[index]['num_comments']=num_comments
		results[index]['comments']=comments
#JCW 19 JUL 2013. Change 'start_time' to 'creation_time'. 'start_time' is not at presently set or returned by db
# need to clarify two different times. index.html does request 'start_time'
# this was throwing an exception because 'start_time' field wasn't found and breaking adding commments or displaying them
#JCW 9 SEP 2013 API exposure of 'creation_time' is 'time' for comments.
		time=results[index]['time'][:16]
		results[index]['time']=time
                cid=s.get("%s/workflow/%s/alias"%(API_PREFIX,pid),  headers={'Real-User-DN':dn})
                cid=cid.json()
#                if webdebug:
#                    print ('webdebug ',cid,cid)
                cid=cid['alias']
                results[index]['alias']=cid		
		index+=1

#        if webdebug:
#            print("WEBDEBUG: results sent to index")
#            pprint(results)
		
    except Exception, err:
	print "web_server.index()- there was an exception"
	print err
#        pass

    #return render_template('index.html', results = results, num_wf = num_wf, wf_name = wf_name)
    return render_template('index.html', **locals())

@app.route('/graph/<wid>', methods=['GET'])
@app.route('/graph/<wid>/<format>', methods=['GET'])
def graph(wid, format="svg"):
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    r=requests.get("%s/workflow/%s/graph"%(API_PREFIX,wid,), **certargs)
    r = r.json()
    nodeshape={'activity':'rectangle','dataobject':'ellipse','workflow':'diamond'}
    graph=pydot.Dot(graph_type='digraph')
    nodes = r['nodes']
    #add workflow node explicitly since in is not a child
    graph.add_node( pydot.Node(wid,label=nodes[wid]['name'],shape=nodeshape[nodes[wid]['type']]))
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
        ans = graph.create_svg()
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
        response.headers['Content-Type'] = 'image/svg+xml'
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
    graph.add_node( pydot.Node(wid,label=nodes[wid]['name'],shape=nodeshape[nodes[wid]['type']]))
    
    object_order={} #stores numerical order of workflow objects.  used for object list display order on workflow detail page
    object_order[0]={ 'uid':wid, 'name':nodes[wid]['name'], 'type':nodes[wid]['type'] }
    count=1
    prev_name=""
    for item in r['connectivity']:
        pid=item['parent_uid']
        cid=item['child_uid']
        name=nodes[cid]['name']
	if prev_name != name:
	    #print(str(count) + " " + name)
	    object_order[count]={ 'uid':cid, 'name':name, 'type':nodes[cid]['type'] }
	    prev_name=name
	    count+=1
	
        theshape=nodeshape[nodes[cid]['type']]
#        graph.add_node( pydot.Node(cid, label=name, shape=theshape, URL='javascript:postcomment("\N")') )
        graph.add_node( pydot.Node(cid, id=cid, label=name, shape=theshape) )
        if item['child_type']!='workflow':
                graph.add_edge( pydot.Edge(pid, cid) )
	
    ans ={}
    ans[0] = graph.create_svg()
    ans[1] = object_order
    return ans

# adds the raw svg xml to the html template <svg></svg>
@app.route('/connections/<wid>', methods=['GET'])
def connections(wid):
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    
    #get workflow svg xml and object order
    getsvg=getsvgxml(wid)
    svgdoc=getsvg[0]
    wf_objects=getsvg[1] #dict of workflow elements: name & type
    svg=svgdoc[154:] #removes the svg doctype header so only: <svg>...</svg>
    
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
		data[0]['time']=obj_time[:16]	    
	    wf_objects[key]['data']=data
	elif value['type'] == "dataobject":
	    req=requests.get("%s/dataobject?uid=%s"%(API_PREFIX,value['uid'],), **certargs) #get data on each workflow element
	    data=req.json()
	    if data[0]['time']:
		obj_time=data[0]['time']
		data[0]['time']=obj_time[:16]	    
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
		    user_info=user_req.json();
		    username=user_info[0]['username']
		    cm[k]['user']=username
		if i['time']:
		    cm_time=i['time']
		    cm[k]['time']=cm_time[:16]
		k+=1

	    num_comment+=k
	    wf_objects[key]['comment']=cm
	
#   if webdebug:
#        print("WEBDEBUG: workflow objects")
#        pprint(wf_objects)
    
    nodes=wf_objects
    return render_template('conn.html', **locals())

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
			 'comment' : {'content':'content', 'uid':'cm_guid', 'time':'creation_time','type':'comment_type',
				      'parent_uid':'parent_GUID','ptype':'parent_type','user_uid':'u_guid'},
			 'mpousers' : {'username':'username', 'uid':'uuid', 'firstname': 'firstname',
				   'lastname':'lastname','email':'email','organization':'organization',
				   'phone':'phone','dn':'dn'},
			 'activity' : {'name':'name', 'description':'description', 'uid':'a_guid',
				       'work_uid':'w_guid', 'description':'description',
				       'time':'creation_time','user_uid':'u_guid','start':'start_time','end':'end_time',
				       'status':'completion_status'},
			 'activity_short' : {'w':'w_guid'},
			 'dataobject' : {'name':'name', 'description':'description', 'uid':'do_guid', 
					  'time':'creation_time', 'user_uid':'u_guid','work_uid':'w_guid', 'uri':'uri'},
			 'dataobject_short': {'w':'w_guid'},
			 'metadata' : {'key':'name', 'uid':'md_guid', 'value':'value', 'key_uid':'type', 'user_uid':'u_guid',
				       'time':'creation_time', 'parent_uid':'parent_guid', 'parent_type':'parent_type'},
			 'metadata_short' : {'n':'name', 'v':'value', 't':'type', 'c':'creation_time' }
			 }
	    
	    #wf=requests.get("%s/workflow?uid=%s"%(API_PREFIX,search_str,), **certargs)
	    results={}
	    if search_str !='':	    
		for pkey,pvalue in query_map.iteritems():
		    obj_result=[]
		    found=False
		    for ckey in pvalue:
			if(pkey != "metadata_short" and pkey != "dataobject_short" and pkey != "activity_short"): #these get requests do not work and break the loop			
			    if(pkey=="mpousers"): #api route is /user and not /mpousers
				pkey="user"
			    
			    req=requests.get("%s/%s?%s=%s"%(API_PREFIX,pkey,ckey,search_str,), **certargs)
			    if req.text != "[]":
				obj_result.extend(req.json())
				found=True
				
				if webdebug:
				    print('%s/%s?%s=%s'%(API_PREFIX,pkey,ckey,search_str))
		    
		    if found:
			results[pkey]=obj_result
		    
		if webdebug:
		    print('WEBDEBUG: user query')
		    pprint(form)
		    print('WEBDEBUG: search results')
		    pprint(results)		
	    
	except:
	    pass
	
	return render_template('search.html', query=form, results=results)
    
    if request.method == 'GET': 
	return render_template('search.html')
    
@app.route('/submit_comment', methods=['POST'])
def submit_comment():
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}
    try:
        form = request.form.to_dict() #gets POSTed form fields as dict; fields: 'parent_uid','comment'
        form['dn'] = dn
        r = json.dumps(form) #convert to json
        if webdebug:
            print('WEBDEBUG: submit comment', r)

        submit = requests.post("%s/comment"%API_PREFIX, r, **certargs)
    except:
        pass
	
    return redirect(url_for('index', wid=form['parent_uid'])) # redirects to a refreshed homepage
                                                                  # after comment submission,
                                                                  # passes workflow ID so that the
                                                                  # comments will show for that workflow

#@app.route('/login')
#def login():
#    return render_template('login.html')

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
		tmp=v.strip();
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
