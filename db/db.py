# file : db.py

import psycopg2 as psycopg
import psycopg2.extras as psyext
import sqlalchemy.pool as pool
import sys
import simplejson as json #plays nice with named tuples
import uuid
import datetime
import os
import textwrap

dbdebug=False
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
	     'metadata_short' : {'n':'name', 'v':'value', 't':'type', 'c':'creation_time' },
             'ontology_terms' : {'uid':'ot_guid','name':'name', 'description':'description','parent_uid':'parent_guid','type':'value_type','units':'units','specified':'specified','user_uid':'added_by','date_added':'date_added'},
             'ontology_instances' : {'uid':'oi_guid','parent_uid':'target_guid','value':'value','time':'creation_time','user_uid':'u_guid'}
	     }


def getconn():
	c = psycopg.connect(conn_string)
	return c

mypool  = pool.QueuePool(getconn, max_overflow=10, pool_size=25)#,echo='debug')
#mypool  = pool.NullPool(getconn)

class MPOSetEncoder(json.JSONEncoder):
	"""
	This class autoconverts datetime.datetime class types returned from postgres.
	Add any new types not handled by json.dumps() by default.
	"""
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return str(obj)
		return json.JSONEncoder.default(self, obj)

def processArgument(a):
	"""
	Handle arguments in GET queries. If in double quotes, strip quotes and pass as literal search.
	Otherwise interpret possible wildcards. Spaces between words are treated as wildcards.
	"""
	if a[0]=='"' and a[-1]=='"':
		qa=a[1:-1]
	else:
		qa=a.replace(' ','%')

	return qa

def getRecord(table,queryargs={}, dn=None):
	'''
	Generic record retrieval. Handles GET requests for all tables.
	Use as a template for route specific behavior.

	Retrieve a record based on join of restrictions in query arguments.
        To get a specific record, call with {'uid':id}.
	id overrides any query arguments since it specifies an exact record. You can get an empty
	replay with conflicting restrictions in queryargs. This function should be called with either
	id or queryarg arguments.
	'''

	# get a connection, if a connect cannot be made an exception will be raised here
	conn = mypool.connect()
	# conn.cursor will return a cursor object, you can use this cursor to perform queries
	cursor = conn.cursor(cursor_factory=psyext.NamedTupleCursor)

	q = 'SELECT'
	qm = query_map[table]
	for key in qm:
		q+=' a.'+qm[key]+' AS '+key+','

	#do we want this line now? username is not in the API interface except for mpousers
	#this line adds a username field to each record returned in addition to the user_uid
	#currently, this is not defined in the API
	q=q[:-1]+', b.username' #remove trailing comma
        if (table == 'comment' or table == 'metadata') and queryargs.has_key('uid'):
                q+=', work_uid'
        q+=' FROM '+table+' a, mpousers b '
        if (table == 'comment' or table == 'metadata') and queryargs.has_key('uid'):
                q+=", getWID('"+processArgument(queryargs['uid'])+"') as work_uid "
        #map user and filter by query
        s="where a."+qm['user_uid']+"=b.uuid"
	for key in query_map[table]:
		if queryargs.has_key(key):
			qa=processArgument(queryargs[key])
                        if qa == 'None':
                                s+=" and "+ "CAST(%s as text) is Null" % (qm[key],)
                        else:
                                s+=" and "+ "CAST(%s as text) ILIKE '%%%s%%'" % (qm[key],qa)
        ontology_terms = []
        if table == 'ontology_terms' and queryargs.has_key('path'):
                ontology_terms=processArgument(queryargs['path']).split("/")
                if '' in ontology_terms: ontology_terms.remove('')
                s+=" and ("
                for i in ontology_terms:
                        s+=" name = '%s' or" % (i,)
                #remove the last or
                s=s[:-3]
                s+=")"
        if (s): q+=s

	if dbdebug:
		print('get query for route '+table+': '+q)

	# execute our Query
	cursor.execute(q)
	# retrieve the records from the database
	records = cursor.fetchall()
	# Close communication with the database
	cursor.close()
	conn.close()

        if table == 'ontology_terms' and len(ontology_terms):
                terms = []
                [terms.append(x) for x in records if not x.parent_uid]
                if len(terms) != 1:
                        return json.dumps({},cls=MPOSetEncoder)
                parent = terms[0]
                for i,o in list(enumerate(ontology_terms[1:])):
                        terms = []
                        [terms.append(x) for x in records if x.name == o and x.parent_uid == parent.uid]
                        if len(terms) != 1:
                                return json.dumps({},cls=MPOSetEncoder)
                        parent = terms[0]
                records = parent

        return json.dumps(records,cls=MPOSetEncoder)



def getUser(queryargs={},dn=None):
	# get a connection, if a connect cannot be made an exception will be raised here
	conn = mypool.connect()

	# conn.cursor will return a cursor object, you can use this cursor to perform queries
	cursor = conn.cursor(cursor_factory=psyext.NamedTupleCursor)

	#        q = "select username,uuid,firstname,lastname,email,organization,phone,dn from mpousers"
	q = "select * from mpousers"

        s=""
	for key in query_map['mpousers']:
		if queryargs.has_key(key):
			qa=processArgument(queryargs[key])
                        if (s):
                                s+=" and "+ "CAST(%s as text) iLIKE '%%%s%%'" % (query_map['mpousers'][key],qa)
                        else:
                                s+=" where "+ "CAST(%s as text) iLIKE '%%%s%%'" % (query_map['mpousers'][key],qa)

        if (s): q+=s
	# execute our Query
	if dbdebug:
		print('get query for route '+'user'+': '+q)

	cursor.execute(q)
	# retrieve the records from the database
	records = cursor.fetchall()
	# Close communication with the database
	cursor.close()
	conn.close()

        return json.dumps(records,cls=MPOSetEncoder)

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
	conn = mypool.connect()
	cursor = conn.cursor(cursor_factory=psyext.NamedTupleCursor)

        # if the dn is already in the db we shouldn't even be here. make sure the username doesn't exist already
        cursor.execute("select username from mpousers where username=%s",(objs['username'],))
        username = cursor.fetchone()
        if (username):
		msg ={"status":"error","error_mesg":"username already exists", "username":username}

		if dbdebug:
			print(msg)
                return json.dumps(msg,cls=MPOSetEncoder)

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
			return json.dumps(msg,cls=MPOSetEncoder)

	if dbdebug:
		print('query is ',q,str(v))
		print('uid is ', objs['uid'])
		print('adduser records',records)

	return json.dumps(records,cls=MPOSetEncoder)
	#	return json.dumps(objs)

def validUser(dn):
        #make sure the user exists in the db. return true/false
	conn = mypool.connect()

	# conn.cursor will return a cursor object, you can use this cursor to perform queries
	cursor = conn.cursor(cursor_factory=psyext.NamedTupleCursor)

        cursor.execute("select username from mpousers where dn=%s",(dn,))
        records = cursor.fetchone()

        if (records):
                return True
        else:
                return False

def getWorkflow(queryargs={},dn=None):
	"""
	Processes the /workflow route. Handles get query arguments.
	"""
	# 'user' requires a join with USER table

	if dbdebug:
		print('DDEBUG getworkflow query ',queryargs)
		if queryargs.has_key('range'):
			therange=queryargs['range']
			print('DDEBUG range is', therange,str(therange))
			qa= tuple(map(int, therange[1:-1].split(',')))
			print('DDEBUG tuple range is',qa)

	# get a connection, if a connect cannot be made an exception will be raised here
	conn = mypool.connect()

	# conn.cursor will return a cursor object, you can use this cursor to perform queries
	cursor = conn.cursor(cursor_factory=psyext.NamedTupleCursor)

	#build our Query, base query is a join between the workflow and user tables to get the username
	q = textwrap.dedent("""\
                            SELECT w_guid as uid, a.name, a.description, a.creation_time as time,
                            a.comp_seq, b.firstname, b.lastname, b.username, b.uuid as userid
                            FROM workflow a, mpousers b""")
        if queryargs.has_key('type'):
                q+= ", ontology_instances c"
        q+=" WHERE a.u_guid=b.uuid"

        if queryargs.has_key('type'):
                q+= " and a.w_guid=c.target_guid and c.value='"+processArgument(queryargs['type'])+"'"

	#logic here to convert queryargs to additional WHERE constraints
	#query is built up from getargs keys that are found in query_map
	#JCW SEP 2013, would be preferable to group queryargs in separate value tuple
	#to protect from sql injection
	for key in query_map['workflow']:
		if dbdebug:
			print ('DBDEBUG workflow key',key,queryargs.has_key(key),queryargs.keys())
		if queryargs.has_key(key):
			qa=processArgument(queryargs[key])
			q+=" and CAST(a.%s as text) iLIKE '%%%s%%'" % (query_map['workflow'][key],qa)

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

        # order by date
        q+=" order by time desc"

        if queryargs.has_key('range'): # return a range
                therange=queryargs['range']
                qa= tuple(map(int, therange[1:-1].split(',')))
                q+=" limit %s" % (qa[1]-qa[0]+1)
                q+=" offset %s" % (qa[0]-1)

	# execute our Query
        if dbdebug:
		print('workflows q',q)
	cursor.execute(q)

	# retrieve the records from the database and rearrange
	records = cursor.fetchall()
	#regroup user fields, first convert records from namedtuple to dict
        jr=json.loads(json.dumps(records,cls=MPOSetEncoder))
	for r in jr:
		r['user']={'firstname':r['firstname'], 'lastname':r['lastname'],
			   'userid':r['userid'],'username':r['username']}
		r.pop('firstname')
		r.pop('lastname')
		r.pop('userid')

	#add total records count
	#cursor.execute('select count ('+q+'))
	#	records = cursor.fetchone()
	#       r['total_count'] = records
	count=cursor.rowcount
	# Close communication with the database
	cursor.close()
	conn.close()

        return json.dumps(jr,cls=MPOSetEncoder)


def getWorkflowCompositeID(id):
	"Returns composite id of the form user/workflow_name/composite_seq"
	wf=json.loads(getWorkflow({'uid':id}))[0]
	compid = {'alias':wf['user']['username']+'/'+wf['name']+'/'+str(wf['comp_seq']),'uid':id}
	if dbdebug:
		print('DBDEBUG: compid ',wf,compid)
	return json.dumps(compid,cls=MPOSetEncoder)


def getWorkflowElements(id,queryargs={},dn=None):
	from dateutil import parser

	# get a connection, if a connect cannot be made an exception will be raised here
	conn = mypool.connect()
	# conn.cursor will return a cursor object, you can use this cursor to perform queries
	cursor = conn.cursor(cursor_factory=psyext.NamedTupleCursor)

	if dbdebug:
		print('DDBEBUG workflowelements query ',queryargs)
		if queryargs.has_key('after'):
			after=queryargs['after']
			print('DDEBUG after value is', after,str(after))
			print('DDEBUG timestamp for after is',parser.parse(after))

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
	return json.dumps(records,cls=MPOSetEncoder)

def addRecord(table,request,dn):
        objs = json.loads(request)
        objs['uid']=str(uuid.uuid4())
        objs['time']=datetime.datetime.now()
	# get a connection, if a connect cannot be made an exception will be raised here
        conn = mypool.connect()
        cursor = conn.cursor(cursor_factory=psyext.NamedTupleCursor)
        #get the user id
        cursor.execute("select uuid from mpousers where dn=%s", (dn,))
        user_id = cursor.fetchone()

        objs['user_uid'] = user_id.uuid
        objkeys= [x.lower() for x in query_map[table] if x in objs.keys() ]

        q = "insert into "+table+" (" + ",".join([query_map[table][x] for x in objkeys]) + ") values ("+",".join(["%s" for x in objkeys])+")"
        v = tuple(objs[x] for x in objkeys)
	if dbdebug:
		print('DDBEBUG addRecord to ',table)
                print(q,v)

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
	return json.dumps(records,cls=MPOSetEncoder)

def addWorkflow(json_request,dn):
	objs = json.loads(json_request)

	# get a connection, if a connect cannot be made an exception will be raised here
	conn = mypool.connect()
	cursor = conn.cursor(cursor_factory=psyext.NamedTupleCursor)
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
        # add the workflow type to the ontology_instance table
        q="insert into ontology_instances (oi_guid,target_guid,term_guid,value,creation_time,u_guid) values (%s,%s,%s,%s,%s,%s)"
        v=(str(uuid.uuid4()),w_guid,objs['id'],objs['value'],datetime.datetime.now(),user_id)
        cursor.execute(q,v)
	# Make the changes to the database persistent
	conn.commit()
	records = {} #JCW we are not returning the full record here.
	records['uid'] = w_guid

	# Close communication with the database
	cursor.close()
	conn.close()
	return json.dumps(records,cls=MPOSetEncoder)

def addComment(json_request,dn):
	objs = json.loads(json_request)
	# get a connection, if a connect cannot be made an exception will be raised here
	conn = mypool.connect()
	cursor = conn.cursor(cursor_factory=psyext.NamedTupleCursor)
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
	return json.dumps(records,cls=MPOSetEncoder)


def addMetadata(json_request,dn):
	objs = json.loads(json_request)
	# get a connection, if a connect cannot be made an exception will be raised here
	conn = mypool.connect()
	cursor = conn.cursor(cursor_factory=psyext.NamedTupleCursor)
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
	return json.dumps(records,cls=MPOSetEncoder)

def addOntologyClass(json_request,dn):
	objs = json.loads(json_request)
	# get a connection, if a connect cannot be made an exception will be raised here
	conn = mypool.connect()
	cursor = conn.cursor(cursor_factory=psyext.NamedTupleCursor)
        #get the user id
        cursor.execute("select uuid from mpousers where dn=%s", (dn,))
        user_id = cursor.fetchone()

        oc_uid = str(uuid.uuid4())
        q="insert into ontology_classes (oc_uid, name, description, parent_guid, added_by, date_added) values (%s,%s,%s,%s,%s,%s,%s)"
        v=(oc_uid,objs['name'],objs['description'],objs['parent_uid'],user_id,datetime.datetime.now())
        cursor.execute(q,v)
	# Make the changes to the database persistent
	conn.commit()

	records = {}
	records['uid'] = oc_guid
	# Close communication with the database
	cursor.close()
	conn.close()
	return json.dumps(records,cls=MPOSetEncoder)

def addOntologyTerm(json_request,dn):
	objs = json.loads(json_request)
	# get a connection, if a connect cannot be made an exception will be raised here
	conn = mypool.connect()
	cursor = conn.cursor(cursor_factory=psyext.NamedTupleCursor)
        #get the user id
        cursor.execute("select uuid from mpousers where dn=%s", (dn,))
        user_id = cursor.fetchone()

        ot_guid = str(uuid.uuid4())
        q="insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,specified,added_by,date_added) values(%s,%s,%s,%s,%s,%s,%s,%s)"
        v=(ot_guid,objs['term'],objs['description'],objs['parent_uid'],objs['value_type'],objs['specified'],user_id,datetime.datetime.now())
        cursor.execute(q,v)
	# Make the changes to the database persistent
	conn.commit()

	records = {}
	records['uid'] = ot_guid
	# Close communication with the database
	cursor.close()
	conn.close()
	return json.dumps(records,cls=MPOSetEncoder)

def addOntologyInstance(json_request,dn):
	objs = json.loads(json_request)
	# get a connection, if a connect cannot be made an exception will be raised here
	conn = mypool.connect()
	cursor = conn.cursor(cursor_factory=psyext.NamedTupleCursor)
        #get the user id
        cursor.execute("select uuid from mpousers where dn=%s", (dn,))
        user_id = cursor.fetchone().uuid

        oi_guid = str(uuid.uuid4())

        terms=objs['path'].split("/")
        terms.remove('')
        # get the ontology term uid
        cursor.execute("select ot_guid,parent_guid from ontology_terms where name=%s",(terms[0],))
        parent=[]
        parent.insert(0,cursor.fetchall())
        if len(parent[0]) != 1 and parent[0][0].parent_guid != None:
                return json.dumps({},cls=MPOSetEncoder)
        for i,o in list(enumerate(terms[1:])):
                cursor.execute("select ot_guid,parent_guid,specified from ontology_terms where name=%s",(o,))
                parent.insert(i+1,cursor.fetchall())
                for l in parent[i+1]:
                        if l.parent_guid != parent[i][0].ot_guid:
                                parent[i+1].remove(l)
                if len(parent[i+1]) != 1:
                        return json.dumps({},cls=MPOSetEncoder)
        if parent[-1][0].specified:
                vocab = json.loads(getRecord('ontology_terms', {'parent_uid':parent[-1][0].ot_guid}, dn ))
                #added term has to exist in the controlled vocabulary.
                valid= tuple(x['name'] for x in vocab)
                if objs['value'] not in valid:
                        return json.dumps({},cls=MPOSetEncoder)
        # make sure the target corresponds to the path
        # parent[1][0].ot_guid is the term uid, terms[2] is the type.
        # allow for the migration of workflows os do this only if Type exists
        # i.e. len(terms)>2
        print len(terms)
        if len(terms) > 2:
                cursor.execute("select oi_guid from ontology_instances where target_guid=%s and term_guid=%s and value=%s",(objs['parent_uid'],parent[1][0].ot_guid,terms[2]))
                if cursor.fetchone() == None:
                        return json.dumps({},cls=MPOSetEncoder)
        # and finally make sure the instance doesn't already exist.
        cursor.execute("select oi_guid from ontology_instances where term_guid=%s and target_guid=%s",(parent[-1][0].ot_guid,objs['parent_uid']))
        if cursor.fetchone():
             return json.dumps({},cls=MPOSetEncoder)
        q="insert into ontology_instances (oi_guid,target_guid,term_guid,value,creation_time,u_guid) values(%s,%s,%s,%s,%s,%s)"
        v=(oi_guid,objs['parent_uid'],parent[-1][0].ot_guid,objs['value'],datetime.datetime.now(),user_id)
        cursor.execute(q,v)
	# Make the changes to the database persistent
	conn.commit()

	records = {}
	records['uid'] = oi_guid
	# Close communication with the database
	cursor.close()
	conn.close()
	return json.dumps(records,cls=MPOSetEncoder)
