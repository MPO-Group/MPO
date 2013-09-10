#!/usr/bin/env python

from flask import Flask, render_template, request, jsonify, redirect, Response
import json
import db as rdb
from authentication import get_user_dn

MPO_API_VERSION = 'v0'

app = Flask(__name__)
app.debug=True
debug=False

routes={'workflow':'workflow', 'dataobject':'dataobject', 'activity': 'activity',
	'comment':'comment', 'metadata':'metadata', 'ontology':'ontology', 'user':'user',
	'guid':'guid'}

#here we create application routes for a specified MPO_VERSION
if MPO_API_VERSION:
	for k,v in routes.iteritems():
		routes[k] = '/' + MPO_API_VERSION + '/' + routes[k]
else:
	for k,v in routes.iteritems():
		routes[k] = '/' + routes[k]

@app.route(routes['workflow']+'/<id>', methods=['GET'])
@app.route(routes['workflow'],  methods=['GET', 'POST'])
def workflow(id=None):
	dn=get_user_dn(request)
	if debug:
		print ('You are: %s'% dn )
		print ('workflow url request is',request.url)
		print('app in workflow',app.SERVER_NAME,request.url_root)
        if not rdb.validUser(dn):
                return Response(None, status=401)

	if request.method == 'POST':
                r = rdb.addWorkflow(request.data,dn)
 	elif request.method == 'GET':
		if id:
			r = rdb.getWorkflow({'uid':id})
		else:
			r = rdb.getWorkflow(request.args)
	return r


@app.route(routes['workflow']+'/<id>/graph', methods=['GET'])
def getWorkflowGraph(id):
	if request.method == 'GET':
		r = rdb.getWorkflowElements(id)
	return r


@app.route(routes['workflow']+'/<id>/alias', methods=['GET'])
def getWorkflowCompositeID(id):
	if request.method == 'GET':
		r = rdb.getWorkflowCompositeID(id)
	return r


@app.route(routes['dataobject']+'/<id>', methods=['GET'])
@app.route(routes['dataobject'], methods=['GET', 'POST'])
def dataobject(id=None):
	dn=get_user_dn(request)
	if request.method == 'POST':
		r = rdb.addDataObject(request.data)
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
		r = rdb.addActivity(request.data)
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
		r = rdb.addMetadata( request.data, dn )
 	elif request.method == 'GET':
		if id:
			r = rdb.getRecord('metadata', {'uid':id}, dn )
		else:
			r = rdb.getRecord('metadata', request.args, dn )
	return r


@app.route(routes['ontology']+'/<id>', methods=['GET'])
@app.route(routes['ontology'], methods=['GET', 'POST'])
def ontology(id=None):
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
    app.debug = True
    #app.run()
    #app.run(host='0.0.0.0', port=8080) #api server
    #app.run(host='0.0.0.0', port=8889) #web ui server
