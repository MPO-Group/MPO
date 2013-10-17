#!/usr/bin/env python

from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
import json
import requests
import time
import datetime
from pprint import pprint
import pydot
import re,os
from authentication import get_user_dn

app = Flask(__name__)

MPO_API_SERVER=os.environ['MPO_API_SERVER']
MPO_WEB_CLIENT_CERT=os.environ['MPO_WEB_CLIENT_CERT']
MPO_WEB_CLIENT_KEY=os.environ['MPO_WEB_CLIENT_KEY']
MPO_API_VERSION = 'v0'
API_PREFIX=MPO_API_SERVER+"/"+MPO_API_VERSION
webdebug=True
app.debug = True

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
    num_wf=0
    wf_name=False
    try:
	wid=request.args.get('wid')
	wf_name=request.args.get('wf_name')


        if webdebug:
	    print('WEBDEBUG: requests in index route',API_PREFIX,wf_name)
	#req=request.args.to_dict()
	
	if wf_name:
	    #get workflows by specified name
	    r=requests.get("%s/workflow?name=%s"%(API_PREFIX,wf_name,), **certargs)
	else:
	    #get all workflows
	    r=requests.get("%s/workflow"%API_PREFIX, **certargs)

	
        if webdebug:
	    print('WEBDEBUG: after requests in index route',API_PREFIX,wf_name)
	    
        # need to check the status code
        if r.status_code == 401:
            return redirect(url_for('landing', dest_url=request.path))
        else:
	#results = json.loads(r) #results is json object
            results = r.json()
        
	#if webdebug:
        #    print("WEBDEBUG: results in index")
        #    pprint(results)

	#pagination control
	num_wf=len(results) # number of workflows returned from api call
	
	index=0
	for i in results:	#i is dict
		if wid:
			if wid == i['uid']:
				results[index]['show_comments'] = 'in' #in is the name of the css class to collapse accordion body
		else:
			results[index]['show_comments'] = ''
                pid=i['uid']
                c=requests.get("%s/comment?parent_uid=%s"%(API_PREFIX,pid), **certargs)
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
                cid=requests.get("%s/workflow/%s/alias"%(API_PREFIX,pid), **certargs)
                cid=cid.json()
                if webdebug:
                    print ('webdebug ',cid,cid)
                cid=cid['alias']
                results[index]['alias']=cid		
		index+=1

        if webdebug:
            print("WEBDEBUG: results sent to index")
            pprint(results)
		
    except Exception, err:
	print "web_server.index()- there was an exception"
	print err
#        pass

    return render_template('index.html', results = results, num_wf = num_wf, wf_name = wf_name)


@app.route('/graph/<wid>', methods=['GET'])
@app.route('/graph/<wid>/<format>', methods=['GET'])
def graph(wid, format="svg"):
    dn = get_user_dn(request)
    certargs={'cert':(MPO_WEB_CLIENT_CERT, MPO_WEB_CLIENT_KEY),
              'verify':False, 'headers':{'Real-User-DN':dn}}

    jsfun = """
        <script>
 //               document.getElementById("graph1").addEventListener("click", sendClickToParentDocument, false);
//                document.getElementById("graph1").addEventListener("onmouseover", sendMouseOverToParent, false);
//                document.getElementById("graph1").addEventListener("onmouseout", sendMouseoutToParent, false);
                function sendClickToParentDocument(evt)
                {
                        // SVGElementInstance objects aren't normal DOM nodes, so fetch the corresponding 'use' element instead
                        var target = evt.target;
      
			// call a method in the parent document if it exists
			if (window.parent.svgElementClicked)
				window.parent.svgElementClicked(target);
			else
				alert("You clicked '" + target.id + "' which is a " + target.textContent + " element");
		}

		//get list of nodes for svg xml tag "g" w/ class "node"
		var nodelist = document.querySelectorAll("g.node");
		
		//parse nodelist object and add click event function to each node (w/ respective data)
		for (var key in nodelist) {
		  if (nodelist.hasOwnProperty(key)) {
		    var node=nodelist[key];
		    node.addEventListener(
			"click",
			(function(node) {
				return function(event) {
					alert(node.childNodes[4].textContent + " (" + node.childNodes[0].textContent + ")" + " node clicked.");
				}
			})(node),
			false
		    );
		  }
		}

		//alert(document.getElementsByTagName("title")[1].textContent);
		//alert(nodelist[0].childNodes[0])
		//alert(nodelist[0].childNodes[0].textContent)

        </script>
    """

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
    else: 
	return "unsupported graph format", 404
    ans = ans[:-7] + jsfun + ans[-7:]
    response = make_response(ans)

    if format == 'svg' :
        response.headers['Content-Type'] = 'image/svg+xml'
    elif format == 'png' :
        response.headers['Content-Type'] = 'image/png'
    elif format == 'gif' :
        response.headers['Content-Type'] = 'image/gif'
    elif format == 'jpg' :
        response.headers['Content-Type'] = 'image/jpg'
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
	    pprint(cm)
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
	
    if webdebug:
        print("WEBDEBUG: workflow objects")
        pprint(wf_objects)
    
    nodes=wf_objects
    return render_template('conn.html', **locals())

@app.route('/about')
def about():
    return render_template('about.html') 

@app.route('/search')
def search():
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

@app.route('/login')
def login():
    return render_template('login.html')

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

#@app.route('/profile')
#def profile():
#    #retrieve user info and display
#    return render_template('profile.html')

def is_email(email):
    pattern = '[\.\w]{1,}[@]\w+[.]\w+'
    if re.match(pattern, email):
        return True
    else:
        return False


if __name__ == "__main__":
    #adding debug option here, so we can see what is going on.	
    app.debug = True
    #app.run()
    #app.run(host='0.0.0.0', port=8080) #api server
    #app.run(host='0.0.0.0', port=8889) #web server
