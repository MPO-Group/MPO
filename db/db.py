# file : db.py

import psycopg2
import psycopg2.extras
import sys
import simplejson as json #plays nice with named tuples
import uuid
import datetime
import os
import textwrap

dbdebug=True
try:
	conn_string = os.environ['MPO_DB_CONNECTION']
except Exception, e:
	print('MPO_DB_CONNECTION not found: %s' % e)
	conn_string = "host='localhost' dbname='mpoDB' user='mpoadmin' password='mpo2013'"

#list of valid query fields and their mapped name in the table,
#  Use of a dictionary permits different fields in the query than are in the database tables
#  query_map is a dictionary of dictionaries indexed by the table name.
#  The first field is the query string and the second is the table column name. Technically, this
#  can support aliases by providing a second index that maps to the same column name.
# If it is not is this dictionary, it is ignored. This provides some protection from SQL injection

query_map = {'workflow':{'name':'name', 'description':'description', 'uid':'w_guid',
			 'composite_seq':'comp_seq', 'time':'creation_time::text' },
	     'comment' : {'content':'content', 'uid':'cm_guid', 'time':'creation_time::text','type':'comment_type',
			  'parent_uid':'parent_GUID','ptype':'parent_type','user':'u_guid'},
	     'mpousers' : {'username':'username', 'uid':'uuid', 'firstname': 'firstname',
		       'lastname':'lastname','email':'email','organization':'organization',
		       'phone':'phone','dn':'dn'},
	     'activity' : {'name':'name', 'description':'description', 'uid':'a_guid',
			   'work_uid':'w_guid', 'description':'description',
			   'time':'creation_time','u_guid':'u_guid','start':'start_time::text','end':'end_time::text',
			   'status':'completion_status'},
	     'activity_short' : {'w':'w_guid'},
	     'dataobject' : {'name':'name', 'description':'description', 'uid':'do_guid', 
			      'time':'creation_time', 'u_guid':'u_guid','work_uid':'w_guid', 'uri':'uri'},
	     'dataobject_short': {'w':'w_guid'},
	     'metadata' : {'key':'name', 'uid':'md_guid', 'value':'value', 'key_uid':'type', 
			   'time':'creation_time::text', 'parent_uid':'parent_guid', 'parent_type':'parent_type'},
	     'metadata_short' : {'n':'name', 'v':'value', 't':'type', 'c':'creation_time::text' }
	     }

def getRecord(table,queryargs=None, dn=None):
	'''
	Generic record retrieval. Handles GET requests for all tables.
	Use as a template for route specific behavior.
	
	Retrieve a record based on join of restrictions in query arguments.
        To get a specific record, call with {'uid':id}.
	id overrides any query arguments since it specifies an exact record. You can get an empty
	replay with conflicting restrictions in queryargs. This function should be called with either
	id or queryarg arguments.
	'''

	qm=query_map[table]
	# get a connection, if a connect cannot be made an exception will be raised here
	conn = psycopg2.connect(conn_string)
	# conn.cursor will return a cursor object, you can use this cursor to perform queries
	cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)

	q = 'SELECT'
	qm = query_map[table]
	for key in qm:
                if qm[key]=='creation_time':
                        qm[key]+='::text'
		q+=' a.'+qm[key]+' AS '+key+','
	q=q[:-1]+', b.username FROM '+table+' a, mpousers b ' #remove trailing comma

	if dbdebug:
		print('get query for route '+table+': '+q)

        s="where a.u_guid=b.uuid"
	for key in query_map[table]:
		if queryargs.has_key(key):
                        s+=" and "+ "%s='%s'" % (qm[key],queryargs[key])
        
        if (s): q+=s
        print q
	# execute our Query
	cursor.execute(q)
	# retrieve the records from the database
	records = cursor.fetchall()
	# Close communication with the database
	cursor.close()
	conn.close()

        return json.dumps(records)



def getUser(queryargs=None,dn=None):
	# get a connection, if a connect cannot be made an exception will be raised here
	conn = psycopg2.connect(conn_string)

	# conn.cursor will return a cursor object, you can use this cursor to perform queries
	cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)

	#        q = "select username,uuid,firstname,lastname,email,organization,phone,dn from mpousers"
	q = "select * from mpousers"

        s=""
	for key in query_map['mpousers']:
		if queryargs.has_key(key):
                        if (s):
                                s+=" and "+ "%s='%s'" % (query_map['mpousers'][key],queryargs[key])
                        else:
                                s+=" where "+ "%s='%s'" % (query_map['mpousers'][key],queryargs[key])
        
        if (s): q+=s
	# execute our Query
	cursor.execute(q)
	# retrieve the records from the database
	records = cursor.fetchall()
	# Close communication with the database
	cursor.close()
	conn.close()

        return json.dumps(records)

def addUser(json_request,dn):
	objs = json.loads(json_request)
	objs['uid']=str(uuid.uuid4())
	objs['dn']=dn
	
	#Check for valid keys against query map, we require all fields for user creation
	reqkeys=sorted([x.lower() for x in  query_map['mpousers'].keys() ] )
	objkeys= sorted([x.lower() for x in  objs.keys() ] )
	if reqkeys != objkeys:
		return '{"status":"error","error_mesg":"invalid or missing fields"}'
		
	if dbdebug:
		print('adding user:',dn)

	# get a connection, if a connect cannot be made an exception will be raised here
	conn = psycopg2.connect(conn_string)
	cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)

        # if the dn is already in the db we shouldn't even be here. make sure the username doesn't exist already
        cursor.execute("select username from mpousers where username=%s",(objs['username'],))
        username = cursor.fetchone()
        if (username):
		msg ={"status":"error","error_mesg":"username already exists", "username":username}
		print(msg)
                return json.dumps(msg)

	q = "insert into mpousers (" + ",".join([query_map['mpousers'][x] for x in reqkeys]) + ") values ("+",".join(["%s" for x in reqkeys])+")"
	v= tuple([objs[x] for x in reqkeys])
	cursor.execute(q,v)
	#JCW Example of returning created record. By calling get getUser() method we also get translation to api labels.
	#	cursor.execute('select * from mpousers where uuid=%s ',(objs['uid'],) )
	#records = cursor.fetchone()
	conn.commit()
	cursor.close()
	conn.close()

        #Retrieve the just created record to return it.
	#must close cursor BEFORE invoking another db method.
	records = getUser( {'uid':unicode(objs['uid'])} ) #JCW for some strange reason, this only works with a unicode string
        #get methods always return a list, but we 'know' this should be one item
	records = json.loads(records)
	if isinstance(records,list):
		if len(records)==1:
			records = records[0]
		else:
			print('DB ERROR: in addUser, record retrieval failed')
			msg ={"status":"error","error_mesg":"record retrieval failed", "username":username,"uid":objs['uid']}
			print(msg)
			return json.dumps(msg)

	if dbdebug:
		print('query is ',q,str(v))
		print('uid is ', objs['uid'])
		print('adduser records',records)

	return json.dumps(records)
	#	return json.dumps(objs)

def validUser(dn):
        #make sure the user exists in the db. return true/false
	conn = psycopg2.connect(conn_string)

	# conn.cursor will return a cursor object, you can use this cursor to perform queries
	cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)

        cursor.execute("select username from mpousers where dn=%s",(dn,))
        records = cursor.fetchone()

        if (records):
                return True
        else:
                return False

def getWorkflow(queryargs=None,dn=None):
	"""
	Processes the /workflow route. Handles get query arguments.
	"""
	# 'user' requires a join with USER table

	# get a connection, if a connect cannot be made an exception will be raised here
	conn = psycopg2.connect(conn_string)

	# conn.cursor will return a cursor object, you can use this cursor to perform queries
	cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)

	#build our Query, base query is a join between the workflow and user tables to get the username
	q = textwrap.dedent("""\
                            SELECT w_guid as uid, a.name, a.description, a.creation_time::text as time, 
                            a.comp_seq, b.firstname, b.lastname, b.username, b.uuid as userid 
                            FROM workflow a, mpousers b WHERE a.u_guid=b.uuid
			    """)

	#logic here to convert queryargs to additional WHERE constraints
	#query is built up from getargs keys that are found in query_map
	#JCW SEP 2013, would be preferable to group queryargs in separate value tuple
	#to protect from sql injection
	for key in query_map['workflow']:
		if dbdebug:
			print ('key',key,queryargs.has_key(key),queryargs.keys())
		if queryargs.has_key(key):
			q+=" and a.%s='%s'" % (query_map['workflow'][key],queryargs[key])

	if queryargs.has_key('alias'):  #handle composite id queries
	#logic here to extract composite_seq,user, and workflow name from composite ID
	#	q+=" and a.composite_seq='%s'"
		compid =  queryargs['alias']
		if dbdebug:
			print('compid: username/workflow_name/seq:',compid,compid.split('/'))
		compid = compid.split('/')
		q+=" and b.username     ='%s'" % compid[0]
		q+=" and a.name         ='%s'" % compid[1]
		q+=" and a.comp_seq='%s'" % compid[2]
		
	if queryargs.has_key('username'): #handle username queries
		q+=" and b.username='%s'" % queryargs['username']

	# execute our Query
        if dbdebug:
		print('workflows q',q)
	cursor.execute(q)

	# retrieve the records from the database and rearrange
	records = cursor.fetchall()
	#regroup user fields, first convert records from namedtuple to dict
        jr=json.loads(json.dumps(records))
	for r in jr:
		r['user']={'firstname':r['firstname'], 'lastname':r['lastname'],
			   'userid':r['userid'],'username':r['username']}
		r.pop('firstname')
		r.pop('lastname')
		r.pop('userid')
	# Close communication with the database
	cursor.close()
	conn.close()
	
        return json.dumps(jr)


def getWorkflowCompositeID(id):
	"Returns composite id of the form user/workflow_name/composite_seq"
	wf=json.loads(getWorkflow({'uid':id}))[0]
	compid = {'alias':wf['user']['username']+'/'+wf['name']+'/'+str(wf['comp_seq']),'uid':id}
	print('compid',wf,compid)
	return json.dumps(compid)


def getWorkflowElements(id):
	# get a connection, if a connect cannot be made an exception will be raised here
	conn = psycopg2.connect(conn_string)
	# conn.cursor will return a cursor object, you can use this cursor to perform queries
	cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)

	records = {}
	# fetch the nodes from the database
	cursor.execute("select w_guid as uid, name, 'workflow' as type from workflow where w_guid=%s union select do_guid as uid, name, 'dataobject' as type from dataobject where w_guid=%s union select a_guid as uid, name, 'activity' as type from activity where w_guid=%s",(id,id,id))
	r = cursor.fetchall()
	nodes={}
	for n in r:
		nodes[n.uid]={'type':n.type,'name':n.name}
	records['nodes']=nodes
	# fetch connectors from the database
	cursor.execute("select parent_guid as parent_uid, parent_type, child_guid as child_uid, child_type from workflow_connectivity where w_guid=%s",(id,))
	records['connectivity']=cursor.fetchall()
	# Close communication with the database
	cursor.close()
	conn.close()
	return json.dumps(records)

def addRecord(table,request,dn):
        objs = json.loads(request)
        objs['uid']=str(uuid.uuid4())
        objs['time']=datetime.datetime.now()
	# get a connection, if a connect cannot be made an exception will be raised here
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
        #get the user id
        cursor.execute("select uuid from mpousers where dn=%s", (dn,))
        user_id = cursor.fetchone()
        objs['u_guid'] = user_id.uuid
        objkeys= [x.lower() for x in query_map[table] if x in objs.keys() ]

        q = "insert into "+table+" (" + ",".join([query_map[table][x] for x in objkeys]) + ") values ("+",".join(["%s" for x in objkeys])+")"
        v = tuple(objs[x] for x in objkeys)
        cursor.execute(q,v)
        #connectivity table
	wc_guid = str(uuid.uuid4())
	for parent in objs['parent_uid']:
                if objs['parent_uid'] == objs['work_uid']:
                        parent_type = 'workflow'
                else:
                        cursor.execute("select w_guid as uid, 'workflow' as type from workflow where w_guid=%s union select a_guid as uid, 'activity' as type from activity where a_guid=%s union select do_guid as uid, 'dataobject' as type from dataobject where do_guid=%s",(parent,parent,parent))
                        records = cursor.fetchone()
                        parent_type = records.type
                cursor.execute("insert into workflow_connectivity (wc_guid, w_guid, parent_guid, parent_type, child_guid, child_type, creation_time) values (%s,%s,%s,%s,%s,%s,%s)", (wc_guid, objs['work_uid'], parent, parent_type , objs['uid'], 'dataobject',datetime.datetime.now()))
	# Make the changes to the database persistent
	conn.commit()

	records = {}
	records['uid'] = objs['uid']
	# Close communication with the database
	cursor.close()
	conn.close()
	return json.dumps(records)

def addWorkflow(json_request,dn):
	objs = json.loads(json_request)

	# get a connection, if a connect cannot be made an exception will be raised here
	conn = psycopg2.connect(conn_string)
	cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	w_guid = str(uuid.uuid4())

        #get the user id

        cursor.execute("select uuid from mpousers where dn=%s", (dn,))
        user_id = cursor.fetchone()

	#determine max composite sequence for incrementing.
	cursor.execute("select MAX(comp_seq) from workflow where name=%s and U_GUID=%s",
		       (objs['name'], user_id ) )
	count=cursor.fetchone()
	
	print ("#############count is",str(count),str(count.max))
	if count.max:
		seq_no=count.max+1
	else:
		seq_no=1

	q="insert into workflow (w_guid, name, description, u_guid, creation_time, comp_seq) values (%s,%s,%s,%s,%s,%s)"
	v= (w_guid, objs['name'], objs['description'], user_id, datetime.datetime.now(),seq_no)
	cursor.execute(q,v)
	# Make the changes to the database persistent
	conn.commit()
	records = {} #JCW we are not returning the full record here.
	records['uid'] = w_guid

	# Close communication with the database
	cursor.close()
	conn.close()
	return json.dumps(records)

def addComment(json_request,dn):
	objs = json.loads(json_request)
	# get a connection, if a connect cannot be made an exception will be raised here
	conn = psycopg2.connect(conn_string)
	cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
        #get the user id
        cursor.execute("select uuid from mpousers where dn=%s", (dn,))
        user_id = cursor.fetchone()

	#get parent object type
	q=textwrap.dedent("""\
	                 SELECT w_guid  AS uid, 'workflow'   AS type FROM workflow   WHERE w_guid=%s UNION
			 SELECT a_guid  AS uid, 'activity'   AS type FROM activity   WHERE a_guid=%s UNION
			 SELECT cm_guid AS uid, 'comment'    AS type FROM comment    WHERE cm_guid=%s UNION
			 SELECT do_guid AS uid, 'dataobject' AS type FROM dataobject WHERE do_guid=%s  
	                  """)
	pid=objs['parent_uid']
	v=(pid,pid,pid,pid)
	cursor.execute(q,v)
	records = cursor.fetchone()

	q="insert into comment (cm_guid,content,parent_guid,parent_type,u_guid,creation_time) values (%s,%s,%s,%s,%s,%s)"
	cm_guid = str(uuid.uuid4())
	v= (cm_guid, objs['content'], records.uid, records.type,user_id, datetime.datetime.now())
	cursor.execute(q,v)
	# Make the changes to the database persistent
	conn.commit()

	records = {}
	records['uid'] = cm_guid
	# Close communication with the database
	cursor.close()
	conn.close()
	return json.dumps(records)


def addMetadata(json_request,dn):
	objs = json.loads(json_request)
	# get a connection, if a connect cannot be made an exception will be raised here
	conn = psycopg2.connect(conn_string)
	cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
        #get the user id
        cursor.execute("select uuid from mpousers where dn=%s", (dn,))
        user_id = cursor.fetchone()

	#get parent object type
	q=textwrap.dedent("""\
	                 SELECT w_guid  AS uid, 'workflow'   AS type FROM workflow   WHERE w_guid=%s UNION
			 SELECT a_guid  AS uid, 'activity'   AS type FROM activity   WHERE a_guid=%s UNION
			 SELECT do_guid AS uid, 'dataobject' AS type FROM dataobject WHERE do_guid=%s  
	                  """)
	pid=objs['parent_uid']
	v=(pid,pid,pid)
	cursor.execute(q,v)
	records = cursor.fetchone()

	#insert record
	md_guid = str(uuid.uuid4())
	q="insert into metadata (md_guid,name,value,type,parent_guid,parent_type,creation_time,u_guid) values (%s,%s,%s,%s,%s,%s,%s,%s)"
	v= (md_guid, objs['key'], objs['value'], 'text', records.uid, records.type, datetime.datetime.now(),user_id)
	cursor.execute(q,v)
	# Make the changes to the database persistent
	conn.commit()

	records = {}
	records['uid'] = md_guid
	# Close communication with the database
	cursor.close()
	conn.close()
	return json.dumps(records)
