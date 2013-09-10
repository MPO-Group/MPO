#!/usr/bin/env python

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
#from flask.ext.pymongo import PyMongo
import requests
import time
import datetime
#import pymongo
import db as rdb
from pprint import pprint
import pydot
import re,os

MPO_VERSION = 'v0'

#mpo=pymongo.Connection().mpo

app = Flask(__name__)
#mongo = PyMongo(app)

routes={"workflow":"workflow", "dataobject":"dataobject", "activity": "activity", "comment":"comment", "metadata":"metadata", "ontology":"ontology", "user":"user", 'guid':'guid'}

#here we create application routes for a specified MPO_VERSION
if MPO_VERSION:
	for k,v in routes.iteritems():
		routes[k] = "/" + MPO_VERSION + "/" + routes[k]
else:
	for k,v in routes.iteritems():
		routes[k] = "/" + routes[k]

def get_user_dn(request):
        import getpass
        try:
                ans =  request.environ['SSL_CLIENT_S_DN']
        except:
                ans = ''
        if len(ans) == 0:
                ans = getpass.getuser() 
	return ans

@app.route("/")
def index():
    #Need to get the latest information from MPO database here
    #and pass it to index.html template 
    results = False
    try:
	wid=request.args.get('wID', '')
	r=workflow()
	results = json.loads(r) #results is json object
	index=0
	for i in results:	#i is dict
		if wid:
			if wid == i['uid']:
				results[index]['show_comments'] = 'in' #in is the name of the css class to collapse accordion body
		else:
			results[index]['show_comments'] = ''
		#c = rdb.getCommentsByParent(i['uid'])
		c = comment(i['uid'])
		comments = json.loads(c)
		num_comments=0
		for temp in comments: #get number of comments
			num_comments+=1
		results[index]['num_comments']=num_comments
		results[index]['comments']=comments
		time=results[index]['start_time'][:16]
		results[index]['start_time']=time
		index+=1
    except:
        pass

    return render_template('index.html', results = results, root_uri = request.url_root)
    #return render_template('index.html')

@app.route('/connections/<wid>', methods=['GET', 'POST'])
def connections(wid):
	try:
		meta = []
		#wid = request.args.get('wid', '')
		gen_workgraph(wid,'')
		r = rdb.getWorkflowElements(wid) #json string
		results = json.loads(r)
		m =  rdb.getMetadataByParent(wid)		
		meta = json.loads(m)
        except:
                pass
	return render_template('conn.html', root_uri = request.url_root, **locals())

@app.route('/about')
def about():
    return render_template('about.html', root_uri = request.url_root) 

@app.route('/search')
def search():
    return render_template('search.html', root_uri = request.url_root) 

@app.route('/submit_comment', methods=['POST'])
def submit_comment():
	try:
		form = request.form.to_dict() #gets POSTed form fields as dict; fields: 'parent_uid','text'
		form['user_dn'] = get_user_dn(request)
		print form
		r = json.dumps(form) #convert to json
		submit = rdb.addComment(r)
        except:
                pass
	
	#return index()
	return redirect(url_for('index', wid=form['parent_uid'])) #redirects to a refreshed homepage after comment submission, passes workflow ID so that the comments will show for that workflow

#@app.route('/details')
#def details():
#	try:
#
#        except:
#                pass
#
#	return render_template('details.html')

#@app.route(routes['workflow'],  methods=['GET', 'POST'])
@app.route('/workflow',  methods=['GET', 'POST'])
def workflow():
	#username = request.args.get('username')
	if request.method == 'POST':
                r = rdb.initWorkflow(request.data)
 	else:
		r = rdb.getWorkflows()
	return r

#@app.route(routes['workflow']+'/<id>', methods=['GET', 'POST'])
@app.route('/workflow/<id>', methods=['GET', 'POST'])
def wid(id):
	if request.method == 'POST':
		pass
	else:
		r = rdb.getWorkflow(id)
	return r
	

#@app.route(routes['workflow']+'/<id>/graph', methods=['GET', 'POST'])
@app.route('/workflow/<id>/graph', methods=['GET', 'POST'])
def widGraph(id):
	if request.method == 'POST':
		pass
	else:
		r = rdb.getWorkflowElements(id)
	return r

#@app.route(routes["dataobject"], methods=['GET', 'POST'])
@app.route('/dataobject', methods=['GET', 'POST'])
def dataobject():
	if request.method == 'POST':
		#Here we process the data and save it into database
		#
		#
		r = rdb.addDataObject(request.data)
 	else:
		r = rdb.getAllDataObjects()
	return r

#@app.route(routes["dataobject"]+'/<id>', methods=['GET', 'POST'])
@app.route('/dataobject/<id>', methods=['GET', 'POST'])
def doID(id):
	if request.method == 'POST':
		pass
 	else:
		r = rdb.getDataObjectByID(id)
	return r


#@app.route(routes["activity"], methods=['GET', 'POST'])
@app.route('/activity', methods=['GET', 'POST'])
def activity():
	result = jsonify(json.loads(request.data),user_dn=get_user_dn(request))
#	print "ACTIVITY"
#	print result
	if request.method == 'POST':
		#Here we process the data and save it into database
		#
		#
		r = rdb.addActivity(request.data)
 	else:
		#Here we parse the request and read data from database.
		#
		#
		pass
	return r

#@app.route(routes["comment"], methods=['GET', 'POST'])
@app.route('/comment/<pid>', methods=['GET', 'POST'])
def comment(pid):
	if request.method == 'POST':
		r = rdb.addComment(request.data)
 	else:
#		r = jsonify([],user_dn=get_user_dn(request))
#		print "COMMENT"
#		print r
#		if request.args.has_key('parent_id'):
#			r = rdb.getCommentsByParent(request.args.get('parent_id'))
		r = rdb.getCommentsByParent(pid)
	return r

#@app.route(routes["comment"]+"/<id>", methods=['GET', 'POST'])
#@app.route('/comment/<id>', methods=['GET', 'POST'])
#def cid(id):
#	if request.method == 'POST':
#		pass
# 	else:
#		r = rdb.getCommentById(id)
#	return r

#@app.route(routes["metadata"], methods=['GET', 'POST'])
@app.route('/metadata', methods=['GET', 'POST'])
def metadata():
	if request.method == 'POST':
		#Here we process the data and save it into database
		#
		#
		r = rdb.addMetadata(request.data)
 	else:
		#Here we parse the request and read data from database.
		#
		#
		r = jsonify([],user_dn=get_user_dn(request))
#		print "METADATA"
#		print r
		if request.args.has_key('parent_id'):
			r = rdb.getMetadataByParent(request.args.get('parent_id'))
	return r

#@app.route(routes["metadata"]+"/<id>", methods=['GET', 'POST'])
@app.route('/metadata/<id>', methods=['GET', 'POST'])
def mid(id):
	if request.method == 'POST':
		pass
 	else:
		r = rdb.getMetadataById(id)
	return r

@app.route(routes["ontology"], methods=['GET', 'POST'])
def ontology():
	result = jsonify(json.loads(request.data),user_dn=get_user_dn(request))
#	print "ONTOLOGY"
#	print result
	if request.method == 'POST':
		#Here we process the data and save it into database
		#
		#
		pass
 	else:
		#Here we parse the request and read data from database.
		#
		#
		pass
	return result

@app.route(routes["user"], methods=['GET', 'POST'])
def user():
	result = jsonify(json.loads(request.data),user_dn=get_user_dn(request))
#	print "USER"
#	print result
	if request.method == 'POST':
		#Here we process the data and save it into database
		#
		#
		pass
 	else:
		#Here we parse the request and read data from database.
		#
		#
		pass
	return result


@app.route('/web_workflow', methods=['GET', 'POST'])
def web_workflow():
	try:
		if request.args.has_key('user'):
			user = request.args.get('user', '')
			r = mpo.workflow.find({'user':user})
		elif request.args.has_key('id'):
			id = request.args.get('id', '')
			r = mpo.workflow.find({'id':str(id)})	
		elif request.args.has_key('name'):
			name = request.args.get('name', '')
			r = mpo.workflow.find({'name':name})
		results={}
		results2=[]
                for i in range(r.count()):
                        results[i]=r[i]
                for i in results:
                        results[i]['time']=unix_time_conv(results[i]['time'])
                        results2.append(results[i])
        except:
                pass

        return render_template('details.html', results=results2, root_uri = request.url_root)		

#@app.route(routes['guid'])
@app.route('/guid')
def guid():
	"""
	Generates unique workflow GUID for each request. 
	"""
	try:
		import pickle	
		pkl_file = open('guid/guid.pkl', 'r')
		guid = pickle.load(pkl_file)
		pkl_file.close()

		guid = guid + 1
		pkl_file = open('guid/guid.pkl', 'w')
		pickle.dump(guid, pkl_file)
		pkl_file.close()
		return str(guid)

	except:
		return (500)

#convert unix timestamp to readable datetime; parameter is timestamp in millisecond precision
def unix_time_conv( timestamp ):
	return datetime.datetime.fromtimestamp(int(timestamp)*.001).strftime('%Y-%m-%d %H:%M:%S') 

#get current datetime unix timestamp
def now_utimestamp():
	current=datetime.datetime.now()
	return time.mktime(current.timetuple())*1e3 + current.microsecond/1e3 #convert to unix timestamp millisecond precision

#create workflow png file
def gen_workgraph(wid,prefix,fileformat="png"):
    save_to='static/img/workflows/'
    r = rdb.getWorkflowElements(wid)
    #    r=requests.get('{host}/{version}/workflow/{wid}/graph'.format(host=app.host,version=MPO_VERSION,wid=wid))
    #gf=r.json()
    gf=json.loads(r)
    #pprint(gf)
    
    nodeshape={'activity':'rectangle','dataobject':'ellipse','workflow':'diamond'}

    graph=pydot.Dot(graph_type='digraph')
    nodes = gf['nodes']

    #add workflow node explicitly since in is not a child
    graph.add_node( pydot.Node(wid,label=nodes[wid]['name'],shape=nodeshape[nodes[wid]['type']]))
    for item in gf['connectivity']:
        pid=item['parent_uid']
        cid=item['child_uid']
        name=nodes[cid]['name']
	theshape=nodeshape[nodes[cid]['type']]
        graph.add_node( pydot.Node(cid, label=name, shape=theshape) )
        if item['child_type']!='workflow':
		graph.add_edge( pydot.Edge(pid, cid) )

    graph.write(save_to+prefix+wid+'.gv')
    if fileformat=="jpg":
        graph.write_png(save_to+prefix+wid+"." + fileformat)
    else:
	graph.write_png(save_to+prefix+wid+".png")
    return

if __name__ == "__main__":
    #adding debug option here, so we can see what is going on.	
    app.debug = True
    #app.run()
    #app.run(host='0.0.0.0', port=8080) #production
    app.run(host='0.0.0.0', port=8889) #test
