#!/usr/bin/env python

from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
import json
from flask.ext.pymongo import PyMongo
import requests

MPO_VERSION = 'v0'

app = Flask(__name__)
mongo = PyMongo(app)

routes={"workflow":"workflow", "connection":"connection","dataobject":"dataobject", "activity": "activity", "comment":"comment", "ontology":"ontology", "user":"user", "about":"about", 'guid':'guid'}

#here we create application routes for a specified MPO_VERSION
if MPO_VERSION:
	for k,v in routes.iteritems():
		routes[k] = "/" + MPO_VERSION + "/" + routes[k]
else:
	for k,v in routes.iteritems():
		routes[k] = "/" + routes[k]


@app.route("/")
def index():
    #Need to get the latest information from MPO database here
    #and pass it to index.html template 
    return render_template('index.html')

@app.route(routes['workflow'], methods=['GET', 'POST'])
def workflow():
	print 'here'
	if request.method == 'POST':
		#result = jsonify(json.loads(request.data))
		#Here we process the data and save it into database
		#
		#

		#mongo.db.workflow.insert(json.loads(request.data))
                r = requests.post("http://localhost/mpo/putData.php", {'json_input':request.data})
 	else:
		#Here we parse the request and read data from database.
		#
		#
		#result = mongo.db.workflow.find()
                r = requests.post("http://localhost/mpo/getData.php","query=select w_guid, a.name from workflow a, users b where a.u_guid=b.uuid  and b.name='romosan'")
	return r.text
@app.route(routes["connection"], methods=['GET', 'POST'])
def connection():
	result = jsonify(json.loads(request.data))
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

@app.route(routes["dataobject"], methods=['GET', 'POST'])
def dataobject():
	result = jsonify(json.loads(request.data))
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

@app.route(routes["activity"], methods=['GET', 'POST'])
def activity():
	result = jsonify(json.loads(request.data))
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

@app.route(routes["comment"], methods=['GET', 'POST'])
def activity():
	result = jsonify(json.loads(request.data))
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

@app.route(routes["ontology"], methods=['GET', 'POST'])
def ontology():
	result = jsonify(json.loads(request.data))
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
	result = jsonify(json.loads(request.data))
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

@app.route(routes['about'])
def about():
    return render_template('about.html') 


@app.route(routes['guid'])
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

if __name__ == "__main__":
    #adding debug option here, so we can see what is going on.	
    app.debug = True
    #app.run()
    app.run(host='0.0.0.0', port=8080)

