# file : db.py

import psycopg2 as psycopg
import psycopg2.extras as psyext
import sqlalchemy.pool as pool
import sys
import simplejson as json #plays nice with named tuples from psycopg2
import uuid
import datetime
import os
import textwrap

dbdebug=True


#  list of valid query fields and their mapped name in the table, Use
#  of a dictionary permits different fields in the query than are in
#  the database tables query_map is a dictionary of dictionaries
#  indexed by the table name. The first field is the query string and
#  the second is the table column name. Technically, this can support
#  aliases by providing a second index that maps to the same column
#  name. If it is not is this dictionary, it is ignored. This provides
#  some protection from SQL injection

query_map = {'workflow':{'name':'name', 'description':'description', 'uid':'w_guid',
                         'composite_seq':'comp_seq', 'time':'creation_time',
                         },
             'collection':{'name':'name', 'description':'description', 'uid':'c_guid',
                           'user_uid':'u_guid', 'time':'creation_time'},
             'collection_elements':{'parent_uid':'c_guid','uid':'e_guid',
                                    'user_uid':'u_guid', 'time':'creation_time'},
             'comment' : {'content':'content', 'uid':'cm_guid', 'time':'creation_time',
                          'type':'comment_type', 'parent_uid':'parent_GUID',
                          'ptype':'parent_type','user_uid':'u_guid'},
             'mpousers' : {'username':'username', 'uid':'uuid', 'firstname': 'firstname',
                           'lastname':'lastname','email':'email','organization':'organization',
                           'phone':'phone','dn':'dn'},
             'activity' : {'name':'name', 'description':'description', 'uid':'a_guid',
                           'work_uid':'w_guid', 'time':'creation_time','user_uid':'u_guid',
                           'start':'start_time','end':'end_time',
                           'status':'completion_status'},
             'activity_short' : {'w':'w_guid'},
             'dataobject' : {'name':'name', 'description':'description','uri':'uri','uid':'do_guid',
                             'source_uid':'source_guid','time':'creation_time', 'user_uid':'u_guid'},
             'dataobject_instance' : {'do_uid':'do_guid', 'uid':'doi_guid',
                                      'time':'creation_time', 'user_uid':'u_guid','work_uid':'w_guid'},
             'dataobject_instance_short': {'w':'w_guid'},
             'metadata' : {'key':'name', 'uid':'md_guid', 'value':'value', 'key_uid':'type',
                           'user_uid':'u_guid', 'time':'creation_time',
                           'parent_uid':'parent_guid', 'parent_type':'parent_type'},
             'metadata_short' : {'n':'name', 'v':'value', 't':'type', 'c':'creation_time' },
             'ontology_terms' : {'uid':'ot_guid','name':'name', 'description':'description',
                                 'parent_uid':'parent_guid', 'type':'value_type',
                                 'units':'units','specified':'specified',
                                 'user_uid':'added_by','date_added':'date_added'},
             'ontology_instances' : {'uid':'oi_guid','parent_uid':'target_guid','value':'value',
                                     'term_uid':'term_guid','time':'creation_time','user_uid':'u_guid'}
         }


conn_string=""
mypool=None

def init(conn_str):
    global conn_string,mypool
    conn_string=conn_str
    print('DB in init connection made: ',conn_string)
    mypool  = pool.QueuePool(get_conn, max_overflow=10, pool_size=25)#,echo='debug')



def get_conn():
    c = psycopg.connect(conn_string)
    return c


def processArgument(a):
    """
    Handle arguments in GET queries. If in double quotes, strip quotes and pass as literal search.
    Otherwise interpret possible wildcards. Spaces between words are treated as wildcards.
    """
    #protect against empty input
    if not a: return a

    if a[0]=='"' and a[-1]=='"':
        qa=a[1:-1]
    else:
        qa=a.replace(' ','%')
        qa=a.replace('&','\&')
        qa=a.replace('\\','\\\\')

    return qa


def echo(table,queryargs={}, dn=None):
    """
    Dummy function to test route and api method construction
    """
    queryargs['table']=table
    return json.dumps(queryargs,cls=MPOSetEncoder)

def getRecordTable(id, dn=None):
    '''
    Given a record id return the table that record is in.
    '''
    if not id: return None
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = mypool.connect()
    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)

    q=''
    v=()
    for k,l in query_map.iteritems():
        if l.has_key('uid') and k!='collection_elements':
            q+="select distinct %s as table from "+k+" where "+l['uid']+"=%s"
            v+=k,id
            q+=' union '

    q=q[:-7]
    # execute our Query
    cursor.execute(q,v)
    # retrieve the records from the database
    table = cursor.fetchone()['table']
    # Close communication with the database
    cursor.close()
    conn.close()

    return table


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
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)

    q = 'SELECT'
    qm = query_map[table]
    for key in qm:
        q+=' a.'+qm[key]+' AS '+key+','

    # do we want this line now? username is not in the API interface
    # except for mpousers this line adds a username field to each
    # record returned in addition to the user_uid currently, this is
    # not defined in the API
    q=q[:-1]+', b.username' #remove trailing comma

    ##COMMENT and METADATA special handling
    if (table == 'comment' or table == 'metadata') and queryargs.has_key('uid') and type(queryargs['uid']) == 'uuid':
        q+=', work_uid'

    q+=' FROM '+table+' a, mpousers b '
    if (table == 'comment' or table == 'metadata') and queryargs.has_key('uid')  and type(queryargs['uid']) == 'uuid':
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

    ##ONTOLOGY/TERMS handling
    ontology_terms = []
    if table == 'ontology_terms' and queryargs.has_key('path'):
        s+= " and ot_guid=getTermUidByPath('"+processArgument(queryargs['path'])+"')"
    if (s): q+=s

    if dbdebug:
        print('get query for route '+table+': '+q)

    # execute our Query
    cursor.execute(q)
    # retrieve the records from the database
    if queryargs.has_key('uri'):
        records = [x for x in cursor.fetchall() if x.get('uri') == queryargs.get('uri')]
    else:
        records = cursor.fetchall()
    # Close communication with the database
    cursor.close()
    conn.close()

    if table == 'ontology_terms' and len(ontology_terms):
        terms=[x for x in records if not x.parent_uid]
        #terms = []  #JCW the following returns a [None] list. harmless but should be fixed.
        #[terms.append(x) for x in records if not x.parent_uid]
        if len(terms) != 1:
            return None

        parent = terms[0]

        for i,o in list(enumerate(ontology_terms[1:])):
            terms=[x for x in records if x.name == o and x.parent_uid == parent.uid]
            #terms = []
            #[terms.append(x) for x in records if x.name == o and x.parent_uid == parent.uid]
            if len(terms) != 1:
                return None
            parent = terms[0]

        records = parent

    return records

def getWorkflowType(id,queryargs={},dn=None):
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = mypool.connect()
    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)

    cursor.execute("select value from ontology_instances where target_guid=%s and term_guid=getTermUidByPath('/Workflow/Type')",(id,))
    records = cursor.fetchone()
    # Close communication with the database
    cursor.close()
    conn.close()

    return records['value']

def getOntologyTermTree(id='0',dn=None):
    """
    Constructs a tree from the ontology terms and returns
    structure suitable for parsing into graph or menu.
    Return is as a python dictionary (not JSON).
    """
    try:
        import treelib as t
    except Exception as e:
        print('Tree generation requires treelib.py')
        return {'status':'Not supported','error_message':str(e)}

    import types #for patching method

    #method patch dictionary method in treelib for this object only to provide data info as well
    def to_dict(self, nid=None, key=None, reverse=False):
        """transform self into a dict"""

        nid = self.root if (nid is None) else nid
        #print('adding',nid,self[nid].data)
        tree_dict = {self[nid].tag: { "children":[] , "data":self[nid].data } }

        if self[nid].expanded:
            queue = [self[i] for i in self[nid].fpointer]
            key = (lambda x: x) if (key is None) else key
            queue.sort(key=key, reverse=reverse)

            for elem in queue:
                tree_dict[self[nid].tag]["children"].append(
                    self.to_dict(elem.identifier))

            if tree_dict[self[nid].tag]["children"] == []:
                tree_dict = {self[nid].tag: { "data":self[nid].data } }

            return tree_dict


    ###Unfortunately, it is necessary to retrieve the entire ontology table
    ###to construct even partial trees because the order is unknown
    ###perhaps some research on tree representations in SQL would help

    #Construct query for database
    q = 'SELECT name as name, ot_guid as uid, parent_guid as parent_uid from ontology_terms'

    # get a connection, if a connect cannot be made an exception will be raised here
    conn = mypool.connect()
    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)
    # execute our Query
    cursor.execute(q)
    # retrieve the records from the database
    records = cursor.fetchall()
    # Close communication with the database
    cursor.close()
    conn.close()

    #cursor.fetchall always returns a list
    if isinstance(records,list):
        if len(records)==0: #throw error
            print('query error in Getontologytermtree, no records returned')
            r={"status"    : "error",
               "error_mesg": "query error in Getontologytermtree, no records returned"}
            return r

    ###Create tree structure for each head of the ontology
    #may be multiple trees, they have parent as None
    #we will place them under 'root' node if the whole tree is requested
    ot_tree=t.Tree()
    ot_tree.create_node('root','0')

    #make sure parents always occur before children
    #try to insert, if parent is not in tree, skip
    #repeat until all records are inserted
    while len(records)>0:
        for o in records:
            pid=o['parent_uid']
            if pid==None:
                pid='0'
            try:
                ot_tree.create_node(o['name'],o['uid'],parent=pid,data=o)
                records.remove(o)
            except t.tree.NodeIDAbsentError, e:
                pass #should test for NodeIDAbsentError

    ot_subtree=ot_tree.subtree(id) #get partial tree specified by uid
    #patch the method now for this instance only
    ot_subtree.to_dict=types.MethodType(to_dict, ot_subtree)

    return ot_subtree.to_dict() #json.dumps(ot_subtree.to_dict(),cls=MPOSetEncoder)


def getUser(queryargs={},dn=None):
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = mypool.connect()

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)

    #    q = "select username,uuid,firstname,lastname,email,organization,phone,dn from mpousers"
    #    q = "select * from mpousers"
    # translate field names
    q = "select "
    qm = query_map['mpousers']
    for key in qm:
        q += ' aa.'+qm[key]+' AS '+key+','
    q =  q[:-1] + ' from mpousers as aa '

    #translate query fields
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

    return records


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
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)

    # if the dn is already in the db we shouldn't even be here. make sure the
    #  username doesn't exist already
    cursor.execute("select username from mpousers where username=%s",(objs['username'],))
    username = cursor.fetchone()
    if (username):
        msg ={"status":"error","error_mesg":"username already exists", "username":username}

        if dbdebug:
            print(msg)
        return json.dumps(msg,cls=MPOSetEncoder)

    q = ("insert into mpousers (" + ",".join([query_map['mpousers'][x] for x in reqkeys]) +
         ") values ("+",".join(["%s" for x in reqkeys])+")")
    v= tuple([objs[x] for x in reqkeys])
    cursor.execute(q,v)
    #JCW Example of returning created record. By calling get getUser()
    #method we also get translation to api labels.
    #       cursor.execute('select * from mpousers where uuid=%s ',(objs['uid'],) )
    #records = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

    #Retrieve the just created record to return it.
    #must close cursor BEFORE invoking another db method.
    #JCW for some strange reason, this only works with a unicode string
    records = getUser( {'uid':unicode(objs['uid'])} )
    #get methods always return a list, but we 'know' this should be one item
    if isinstance(records,list):
        if len(records)==1:
            records = records[0]
        else:
            print('DB ERROR: in addUser, record retrieval failed')
            msg ={"status":"error","error_mesg":"record retrieval failed",
                  "username":username,"uid":objs['uid']}
            print(msg)
            return None

    if dbdebug:
        print('query is ',q,str(v))
        print('uid is ', objs['uid'])
        print('adduser records',records)

    return records


def validUser(dn):
    #make sure the user exists in the db. return true/false
    conn = mypool.connect()

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)

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
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)

    #build our Query, base query is a join between the workflow and user tables to get the username
    q = textwrap.dedent("""\
                SELECT a.w_guid as uid, a.name, a.description, a.creation_time as time,
                a.comp_seq as composite_seq, b.firstname, b.lastname, b.username, b.uuid as userid,
                c.value as w_type FROM workflow a, mpousers b, ontology_instances c """)

    #join with ontology_instance table to get workflow type
    q += " WHERE a.u_guid=b.uuid and a.w_guid=c.target_guid and c.term_guid=getTermUidByPath('/Workflow/Type')"
    # add extra query filter on workflow type (which is stored in a separate table)
    if queryargs.has_key('type'):
        #q+= " and a.w_guid=c.target_guid and c.value='"+processArgument(queryargs['type'])+"'"
        q+= " and c.value='"+processArgument(queryargs['type'])+"'"


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
    #       q+=" and a.composite_seq='%s'"
        compid =  queryargs['alias']
        if dbdebug:
            print('compid: username/workflow_type/seq:',compid,compid.split('/'))
        compid = compid.split('/')
        q+=" and b.username     ='%s'" % compid[0]
        q+=" and c.value     ='%s'" % compid[1]
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
    if dbdebug:
        print('get workflow records',records)
    for r in records:
        r['user']={'firstname':r['firstname'], 'lastname':r['lastname'],
               'userid':r['userid'],'username':r['username']}
        r.pop('firstname')
        r.pop('lastname')
        r.pop('userid')
        #JCW 9 SEP 2014, also add workflow type

        r['type'] = r['w_type']
        r.pop('w_type')

    # Close communication with the database
    cursor.close()
    conn.close()

    return records


def getWorkflowCompositeID(id, dn=None):
    "Returns composite id of the form user/workflow_name/composite_seq"
    wf=getWorkflow({'uid':id})
    compid=''
    #catch exception here if thrown by getWorkflow?
    if len(wf) == 1: #record found
        wf=wf[0] #getWorkflow always returns a list
        compid = {'alias':wf['user']['username']+'/'+wf['type']+'/'+str(wf['composite_seq']),'uid':id}
    if dbdebug:
        print('DBDEBUG: compid ',wf,compid)
    return compid


def getWorkflowElements(id,queryargs={},dn=None):
    """
    Returns datastructure {connectivity: [{parent_uid:, parent_type:, child_uid:, child_type:}... ],
    nodes: [{type:, name:, time:}... ] }
    That describes the workflow as a complete DAG.
    """
    from dateutil import parser

    # get a connection, if a connect cannot be made an exception will be raised here
    conn = mypool.connect()
    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)

    if dbdebug:
        print('DDBEBUG workflowelements query ',queryargs)
        if queryargs.has_key('after'):
            after=queryargs['after']
            print('DDEBUG after value is', after,str(after))
            print('DDEBUG timestamp for after is',parser.parse(after))

    records = {}
    # fetch the nodes from the database
    cursor.execute("select w_guid as uid, name, 'workflow' as type, creation_time from workflow a "+
                   "where w_guid=%s union select doi_guid as uid, b2.name as name, 'dataobject_instance' as type, b1.creation_time "+
                   "from dataobject_instance b1, dataobject b2 where w_guid=%s and b1.do_guid = b2.do_guid union select "+
                   "a_guid as uid, name, 'activity' as type, creation_time from activity c "+
                   "where w_guid=%s order by creation_time desc",(id,id,id))
    r = cursor.fetchall()
    nodes={}
    for n in r:
        nodes[n['uid']]={'type':n['type'],'name':n['name'],'time':n['creation_time']}
    records['nodes']=nodes
    # fetch connectors from the database
    cursor.execute("select parent_guid as parent_uid, parent_type, child_guid as child_uid, "+
                   "creation_time as time, child_type from workflow_connectivity "+
                   "where w_guid=%s order by creation_time", (id,) )
    records['connectivity']=cursor.fetchall()
    # Close communication with the database
    cursor.close()
    conn.close()

    return records


def getWorkflowComments(id,queryargs={},dn=None):
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = mypool.connect()
    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)
    q = "select "
    qm = query_map['comment']
    for key in qm:
        q += ' a.'+qm[key]+' AS '+key+','
    q = q[:-1] + (" from comment as a where a.parent_guid in "+
                  "(select w_guid as uid from workflow where w_guid=%s "+
                  "union "+
                  "select doi_guid as uid from dataobject_instance where w_guid=%s "+
                  "union " +
                  "select a_guid as uid from activity where w_guid=%s)" )
    cursor.execute(q,(id,id,id))
    records = cursor.fetchall()
    # get all the comments recursively
    parents = []
    for x in records:
        parents.append(x['uid'])
    #recursively get comments on comments
    while len(parents):
        q = "select "
        for key in qm:
            q+=' a.'+qm[key]+' AS '+key+','
        q=q[:-1]+" from comment as a where a.parent_guid in ( "
        for i in parents:
            q+="%s,"

        q=q[:-1]+")"
        v = tuple(x for x in parents)
        cursor.execute(q,v)
        children = cursor.fetchall()
        parents = []
        for x in children:
            records.append(x)
            parents.append(x['uid'])

    cursor.close()
    conn.close()

    return records


def addRecord(table,request,dn):
    objs = json.loads(request)
    if not objs.has_key('uid'): objs['uid']=str(uuid.uuid4())
    objs['time']=datetime.datetime.now()

    # get a connection, if a connect cannot be made an exception will be raised here
    conn = mypool.connect()
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)
    #get the user id
    cursor.execute("select uuid from mpousers where dn=%s", (dn,))

    objs['user_uid'] = cursor.fetchone()['uuid']
    objkeys= [x.lower() for x in query_map[table] if x in objs.keys() ]
    print('addrecord', objs,objkeys)

    q = ( "insert into "+table+" (" + ",".join([query_map[table][x] for x in objkeys]) +
          ") values ("+",".join(["%s" for x in objkeys])+")" )

    v = tuple(objs[x] for x in objkeys)
    if dbdebug:
        print('DDBEBUG addRecord to ',table)
        print(q,v)

    cursor.execute(q,v)
    #it turns out every object has a parent_uid. i know my fault.
    #if objs.has_key('parent_uid') and objs.has_key('work_uid'):
    if table == 'workflow' or table=='dataobject_instance' or table=='activity':
    #connectivity table
        for parent in objs['parent_uid']:
            wc_guid = str(uuid.uuid4())
            cursor.execute("insert into workflow_connectivity "+
                           "(wc_guid, w_guid, parent_guid, parent_type, child_guid, child_type, creation_time) "+
                           "values (%s,%s,%s,%s,%s,%s,%s)",
                           (wc_guid, objs['work_uid'], parent, getRecordTable(parent), objs['uid'],
                            table, datetime.datetime.now()))
    # Make the changes to the database persistent
    conn.commit()

    records = {}
    records['uid'] = objs['uid']
    # Close communication with the database
    cursor.close()
    conn.close()

    return records


def addCollection(request,dn):
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = mypool.connect()
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)
    c_guid = str(uuid.uuid4())

    #get the user id

    cursor.execute("select uuid from mpousers where dn=%s", (dn,))
    user_id = cursor.fetchone()['uuid']

    p = json.loads(request)
    q = ("insert into collection (c_guid, name, description, u_guid, creation_time) " +
         "values (%s,%s,%s,%s,%s)")
    v= (c_guid, p['name'], p['description'], user_id, datetime.datetime.now())
    if dbdebug:
        print ('DBDEBUG:: addcollection: ',q, v)
    cursor.execute(q,v)

    for e in p['elements']:
        q = ("insert into collection_elements (c_guid, e_guid, u_guid, creation_time) " +
             "values (%s,%s,%s,%s)")
        v= (c_guid, e, user_id, datetime.datetime.now())
        cursor.execute(q,v)

    # Make the changes to the database persistent
    conn.commit()
    records = {} #JCW we are not returning the full record here.
    records['uid'] = c_guid

    return records


def addWorkflow(request,dn):
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = mypool.connect()
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)
    w_guid = str(uuid.uuid4())

    #get the user id
    cursor.execute("select uuid from mpousers where dn=%s", (dn,))
    user_id = cursor.fetchone()['uuid']

    #determine max composite sequence for incrementing.
    #  find all workflows of this type that the users already has and increament the largest composite seq number
    cursor.execute("select MAX(comp_seq) from workflow a, ontology_instances c WHERE c.value=%s and a.U_GUID=%s and c.target_guid=a.w_guid",
               (request['value'], user_id ) )
    count=cursor.fetchone()

    if dbdebug:
        print ("#############count is",str(count),str(count['max']))

    if count['max']:
        seq_no=count['max']+1
    else:
        seq_no=1

    q = ("insert into workflow (w_guid, name, description, u_guid, creation_time, comp_seq) " +
         "values (%s,%s,%s,%s,%s,%s)")
    v= (w_guid, request['name'], request['description'], user_id, datetime.datetime.now(),seq_no)
    cursor.execute(q,v)

    # add the workflow type to the ontology_instance table
    q = ("insert into ontology_instances (oi_guid,target_guid,term_guid,value,creation_time,u_guid) "+
         "values (%s,%s,%s,%s,%s,%s)")
    v=(str(uuid.uuid4()),w_guid,request['type_uid'],request['value'],datetime.datetime.now(),user_id)
    cursor.execute(q,v)

    # Make the changes to the database persistent
    conn.commit()
    records = {} #JCW we are not returning the full record here.
    records['uid'] = w_guid

    # Close communication with the database
    cursor.close()
    conn.close()

    return records


def addMetadata(json_request,dn):
    objs = json.loads(json_request)
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = mypool.connect()
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)
    #get the user id
    cursor.execute("select uuid from mpousers where dn=%s", (dn,))
    user_id = cursor.fetchone()['uuid']

    #get parent object type
    q=textwrap.dedent("""\
             SELECT w_guid  AS uid, 'workflow'   AS type FROM workflow   WHERE w_guid=%s UNION
             SELECT a_guid  AS uid, 'activity'   AS type FROM activity   WHERE a_guid=%s UNION
             SELECT doi_guid AS uid, 'dataobject_instance' AS type FROM dataobject_instance WHERE doi_guid=%s
              """)
    pid=objs['parent_uid']
    v=(pid,pid,pid)
    cursor.execute(q,v)
    records = cursor.fetchone()

    #insert record
    md_guid = str(uuid.uuid4())
    q = ("insert into metadata (md_guid,name,value,type,parent_guid,parent_type,creation_time,u_guid) "+
         "values (%s,%s,%s,%s,%s,%s,%s,%s)")
    v= (md_guid, objs['key'], objs['value'], 'text', records['uid'], records['type'],
        datetime.datetime.now(), user_id)
    cursor.execute(q,v)
    # Make the changes to the database persistent
    conn.commit()

    records = {}
    records['uid'] = md_guid
    # Close communication with the database
    cursor.close()
    conn.close()
    return records


def addOntologyClass(json_request,dn):
    objs = json.loads(json_request)
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = mypool.connect()
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)
    #get the user id
    cursor.execute("select uuid from mpousers where dn=%s", (dn,))
    user_id = cursor.fetchone()['uuid']

    oc_uid = str(uuid.uuid4())
    q = ("insert into ontology_classes (oc_uid, name, description, parent_guid, added_by, date_added) "+
         "values (%s,%s,%s,%s,%s,%s,%s)")
    v=(oc_uid,objs['name'],objs['description'],objs['parent_uid'],user_id,datetime.datetime.now())
    cursor.execute(q,v)
    # Make the changes to the database persistent
    conn.commit()

    records = {}
    records['uid'] = oc_guid
    # Close communication with the database
    cursor.close()
    conn.close()
    return records


def addOntologyInstance(json_request,dn):
    objs = json.loads(json_request)
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = mypool.connect()
    cursor = conn.cursor(cursor_factory=psyext.RealDictCursor)
    #get the user id
    cursor.execute("select uuid from mpousers where dn=%s", (dn,))
    user_id = cursor.fetchone()['uuid']

    oi_guid = str(uuid.uuid4())
    # get the ontology term
    term = getRecord('ontology_terms', {'path':processArgument(objs['path'])}, dn )[0]
    if term['specified']:
        vocab = getRecord('ontology_terms', {'parent_uid':term['uid']}, dn )
        #added term has to exist in the controlled vocabulary.
        valid= tuple(x['name'] for x in vocab)
        if objs['value'] not in valid:
            return None

    # make sure the instance doesn't already exist.
    cursor.execute("select oi_guid from ontology_instances where term_guid=%s and "+
                   "target_guid=%s",(term['uid'],objs['parent_uid']))
    if cursor.fetchone():
        return None

    q=("insert into ontology_instances (oi_guid,target_guid,term_guid,value,creation_time,u_guid) "+
       "values(%s,%s,%s,%s,%s,%s)")
    v=(oi_guid,objs['parent_uid'],term['uid'],objs['value'],datetime.datetime.now(),user_id)
    cursor.execute(q,v)
    # Make the changes to the database persistent
    conn.commit()
    records = {}
    records['uid'] = oi_guid
    # Close communication with the database
    cursor.close()
    conn.close()

    return records
