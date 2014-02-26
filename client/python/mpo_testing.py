#!/usr/bin/env python
"""
.mpo_response = has last response to request

echo $thing | mpo put
OR
mpo -a $mpo_response put <thing>
"""
from __future__ import print_function
import requests
import ast, textwrap
import unittest
import sys,os,datetime,getopt
import json
from urlparse import urlparse

#Developers note: 
#all print statements except those in mpo_cli.storeresult should go to sys.stderr
#Non-standard dependencies: requests.py

# TODO
# * Error handling on request replies, define standard replies. Server should always return 
#    an object (JSON or XML)
# * santize urls, for example url/workflow and url//workflow should both work

class mpo_methods(object):
    """
    Class of RESTful primitives. I/O is through stdin/stdout.
    Implementation of MPO client side API as described at 
    http://www.psfc.mit.edu/mpo/

    Commandline invocation:
    mpo <mpo flags> method <url> <method flags> <payload>
    Functional invocation:
    import mpo.mpo_methods as m
    m.flags=values #set some defaults, eg m.server=$MPO_HOST
    m.mpo_method(url=url,payload=payload,arg1=arg1,arg2=arg2)
    """
    #Need error handling
    #By giving each method **kwargs in its definition, they will accepts
    #arbitrary sets of keywords arguments that they may or may not act upon.
    #kwargs in body will only contain keyword pars that were not matched in the 
    #function call
    POSTheaders = {'content-type': 'application/json'}
    GETheaders= {'ACCEPT': 'application/json'}
    ID='uid'  #change to '_id' for mongo
    WORKID='work_uid'
    PARENTID='parent_uid' #field for object id to which comments and metadata are attached

    mpo_settings={}
    MPO_VERSION='v0'
    MPO_AUTH=''
    WORKFLOW_RT = 'workflow'
    COMMENT_RT  = 'comment'
    METADATA_RT = 'metadata'
    DATAOBJECT_RT='dataobject'
    ACTIVITY_RT=  'activity'
    ONTOLOGY_TERM_RT = 'ontology/term'
    debug=1

    def __init__(self):
        "Initialize mpo methods class"
        #private class variables
        self.__user=""
        self.__server=""
        if os.environ.has_key('MPO_VERSION'):
            self.MPO_VERSION=os.environ['MPO_VERSION']

        if os.environ.has_key('MPO_AUTH'):
            self.MPO_AUTH=os.environ['MPO_AUTH']
        return

    def set_server(self,host):
        #Error checking. Valid host string.
        self.__server=host
        return

    def get_server(self):
        return self.__server

    def set_user(self,user):
        #Error checking, look up user to see if they exist. return record
        self.__user=user
        return

    def get_user(self):
        return self.__user


    def mpo_post(self,url,workflowID=None,objID=None,data=None,**kwargs):
        """
        workflow is the workflow being added to
        url is the target being posted to
        obj is the object we are making a connection from
        data is the object being posted

        """
        #need flexible number of args so you can just post to a url.

        # Need to validate body? No, servers job.
        # We might want to use different headers?
        # handling binary data, or data in a file?
        # requests.post is happy to take those in the data argument but server has to handle it.
        # mongo returns {time:,_id:} by default
        # could parse data so see if starts with file:


        if isinstance(data,str):
            datadict=ast.literal_eval(data)
        else:
            datadict=data

        if kwargs.has_key('user'):
            if self.get_user()!="":
                datadict['user']=self.get_user()
                #kwargs overrides
            if kwargs['user']!=None: 
                datadict['user']=kwargs['user']
            del kwargs['user'] #dont pass it along to requests

        if self.debug>0:
            print('mpo_POST',url,json.dumps(datadict),file=sys.stderr)

        if workflowID==None and objID==None and data==None:
            r = requests.post(url, headers=self.POSTheaders,**kwargs)
            if r.status_code!=200:
                return r.status_code
            else:
                return r

        if workflowID==None and data!=None: #eg init
# commented out because top of ontology hierarchy is null (at least for now)
#            if objID!=None:  #comments and metadata
            datadict[self.PARENTID]=objID

            try:
                r = requests.post(url, json.dumps(datadict), headers=self.POSTheaders,**kwargs)
            except requests.exceptions.ConnectionError,err:
                print("ERROR: Could not connect to server, "+url,file=sys.stderr)
                print("ERROR: payload was: "+json.dumps(datadict),file=sys.stderr)
                sys.stderr.write('MPO ERROR: %s\n' % str(err))
                print(" ",file=sys.stderr)
                return 1

            if r.status_code!=200:
                return r.status_code,r.text
            else:
                return r

        #If we reach here, workflowID, objID, and data arguments are present.

        # note we convert python dict to json format and tell the server and requests.py in the header it is JSON
        # requests will actually send the dict directly if headers doesn't declare body type

        datadict[self.WORKID]=workflowID
        datadict[self.PARENTID]=objID
        try:
            r = requests.post(url, json.dumps(datadict), headers=self.POSTheaders,**kwargs)
        except requests.exceptions.ConnectionError,err:
            print("ERROR: Could not connect to server, "+url,file=sys.stderr)
            sys.stderr.write('MPO ERROR: %s\n' % str(err))
            print(" ",file=sys.stderr)
            return 1

        if r.status_code!=200:
            return r.status_code, r.text

        return r


    def mpo_get(self,url,*args,**kwargs):
        """arguments: url, <params>
           params is a python key:value dictionary
        """

        if kwargs.has_key('user'):
            #add to params or header?
            del kwargs['user'] #dont pass it along to requests

        flags="r:p:"
        longflags=["route=","params="]

        try:
            opts, cmdargs = getopt.getopt(map(str,list(args)), flags, longflags)

        except getopt.GetoptError:
            print("Test Accepted flags are:\n"+str(flags)+"\n"+str(longflags),file=sys.stderr)
            sys.exit(2)

        params=None
        for opt, arg in opts:
            if opt in ("-r","--route"):
                route=arg
                o=urlparse(url)
                url=o.scheme+"://"+o.netloc+o.path+'/'+self.MPO_VERSION+'/'+route
            elif opt in ("-p","--params"):
                params=arg

        if self.debug>0:
            print('mpo_GET',url,params,kwargs,file=sys.stderr)
        try:
            r = requests.get(url,headers=self.GETheaders,params=params,**kwargs)
        except requests.exceptions.ConnectionError,err:
            print("ERROR: Could not connect to server, "+url,file=sys.stderr)
            sys.stderr.write('MPO ERROR: %s\n' % str(err))
            print(" ",file=sys.stderr)
            return 1
        
        #if parameters are present, this is a search
        #requests.py reconstructs the url with the parameters appended 
        #in the "?param=val" http syntax

        return r


    # Begin higher order methods
    def mpo_init(self,url,*args,**kwargs):
        """
        The INIT method starts a workflow.
        It returns the server response for a new workflow.
        URL should be the host root.
        Syntactic sugar, alias for post
        args are <url>,--name,--description

        """

        flags="n:d:"
        longflags=["name=","desc="]

        try:
            opts, cmdargs = getopt.getopt(map(str,list(args)), flags, longflags)

        except getopt.GetoptError:
            print("Test Accepted flags are:\n"+str(flags)+"\n"+str(longflags),file=sys.stderr)
            sys.exit(2)

        for opt, arg in opts:
            if opt in ("-n","--name"):
                name=arg
            elif opt in ("-d","--desc"):
                desc=arg

        o=urlparse(url)
        urlcon=o.scheme+"://"+o.netloc+o.path+'/'+self.MPO_VERSION+'/'+self.WORKFLOW_RT

        payload={"name":name,"description":desc}

        r=self.mpo_post(urlcon,None,None,payload,**kwargs)
        return r


    def mpo_add(self,url,workflow_ID,parentobj_ID,*args,**kwargs):
        """Syntactic sugar, alias for post
        args are <url>,workflow_id,parentobj_id ,--name,--description,--uri
        """

        flags="n:d:u:"
        longflags=["name=","desc=","uri="]

        try:
            opts, cmdargs = getopt.getopt(map(str,list(args)), flags, longflags)

        except getopt.GetoptError:
            print("Test Accepted flags are:\n"+str(flags)+"\n"+str(longflags),file=sys.stderr)
            sys.exit(2)

        name=''
        desc=''
        uri=''
        for opt, arg in opts:
            if opt in ("-n","--name"):
                name=arg
            elif opt in ("-d","--desc"):
                desc=arg
            elif opt in ("-u","--uri"):
                uri=arg
        
        o=urlparse(url)
        urlcon=o.scheme+"://"+o.netloc+o.path+'/'+self.MPO_VERSION+'/'+self.DATAOBJECT_RT
        payload={"name":name,"description":desc,"uri":uri}

        return self.mpo_post(urlcon,workflow_ID,[parentobj_ID],payload,**kwargs)


    def mpo_step(self,url,workflow_ID,parentobj_ID,*args,**kwargs):
        """Syntactic sugar, wrapper for post
           For adding actions
           args are <url>,workflow_id,parentobj_id ,--input,--name,--desc,--uri
        """

        flags="n:d:u:i:"
        longflags=["name=","desc=","uri=","input="]

        try:
            opts, cmdargs = getopt.getopt(map(str,list(args)), flags, longflags)

        except getopt.GetoptError:
            print("Test Accepted flags are:\n"+str(flags)+"\n"+str(longflags),file=sys.stderr)
            sys.exit(2)

        name=""
        desc=""
        uri=""
        inp=[parentobj_ID]

        for opt, arg in opts:
            if opt in ("-n","--name"):
                name=arg
            elif opt in ("-d","--desc"):
                desc=arg
            elif opt in ("-u","--uri"):
                uri=arg
            elif opt in ("-i","--input"):
                inp.append(arg)
        
        o=urlparse(url)
        urlcon=o.scheme+"://"+o.netloc+o.path+'/'+self.MPO_VERSION+'/'+self.ACTIVITY_RT
        payload={"name":name,"description":desc,"uri":uri}

        r=self.mpo_post(urlcon,workflow_ID,inp,payload,**kwargs)
        return r

    def mpo_ontology_term(self,url,term,*args,**kwargs):
        """Add terms to the ontology
           args are term,--parent,--desc,--vtype,--specified,--units
        """

        flags="p:d:t:s:u"
        longflags=["parent=","desc=","vtype=","specified=","units="]

        try:
            opts, cmdargs = getopt.getopt(map(str,list(args)), flags, longflags)

        except getopt.GetoptError:
            print("Test Accepted flags are:\n"+str(flags)+"\n"+str(longflags),file=sys.stderr)
            sys.exit(2)

        desc=None
        vtype=None
        specified=None
        units=None
        pid = None

        for opt, arg in opts:
            if opt in ("-d","--desc"):
                desc = arg
            elif opt in ("-t","--vtype"):
                vtype = arg
            elif opt in ("-u","--units"):
                units = arg
            elif opt in ("-p","--parent"):
                pid = arg
            elif opt in ("-s","--specified"):
                if (arg=='y'):
                    specified=True
                else:
                    specified=False

        o=urlparse(url)
        urlcon=o.scheme+"://"+o.netloc+o.path+'/'+self.MPO_VERSION+'/'+self.ONTOLOGY_TERM_RT
        payload={"term":term,"description":desc,"value_type":vtype,"specified":specified,"units":units}
        r=self.mpo_post(urlcon,None,pid,payload,**kwargs)
        return r

    def mpo_comment(self,url,obj_ID,data,**kwargs):
        """Takes a returned record and adds a comment to it.
        In this case, data should be a plain string.
        """
        if not (isinstance(data,str) or isinstance(data,unicode)):
            print('Error in mpo_commment, should be a plain string')
            return -1
            
        o=urlparse(url)
        urlcon=o.scheme+"://"+o.netloc+o.path+'/'+self.MPO_VERSION+'/'+self.COMMENT_RT
        
        r=self.mpo_post(urlcon,None,obj_ID,{'content':str(data)},**kwargs)

        return r


    def mpo_meta(self,url,obj_ID,key,value,**kwargs):
        """Takes a returned record and adds a metadata to it.
        In this case, data should be a plain string.
        """
        if not (isinstance(key,str) or isinstance(key,unicode)):
            print('Error in mpo_meta, should be a plain string')
            return -1
            
        o=urlparse(url)
        urlcon=o.scheme+"://"+o.netloc+o.path+'/'+self.MPO_VERSION+'/'+self.METADATA_RT
        
        r=self.mpo_post(urlcon,None,obj_ID,{'value':str(value),'key':key}, **kwargs)

        return r


    def mpo_search(self,url,route,params,**kwargs):
        "Find objects by query"
        o=urlparse(url)
        urlcon=o.scheme+"://"+o.netloc+o.path+'/'+self.MPO_VERSION+'/'+route
        return self.mpo_get(urlcon,**kwargs) # ,params=ast.literal_eval(params))


    def mpo_help(self,*args,**kwargs):
        """
        You are on your own!

        """
        print(self.__doc__)
        print('methods:')
        for method in dir(self):
            if method[:4]=='mpo_':
                print(method[4:]+":")
                mdoc='self.'+method+'.__doc__'
                exec('print(eval(mdoc))')
                print()
                print('------------------------------------------------------------------------')
        return 0


class mpo_cli(mpo_methods):
    """
    Implementation of MPO client side API as described at 
    http://www.psfc.mit.edu/mpo/
    High level command line interface to API.
    """

    def __init__(self):
        mpo_methods.__init__(self)

        self.debug=0
        self.ifile='./.mpo_result'
        self.istate='echo' #default. Values are ['echo','env','dotfile']
        self.comment=None
        self.response_format='ID'
        self.set_server(self.getmpohost())
        return


    def meta( self, method_name,url, *args,**kwargs ):
        """
           First argument is the method name. It maps to 'mpo_x' defined 
           in the mpo_methods class.
           Second argument is optionally the url of the mpo host. Otherwise, 
           defaults to other resource specifications.
        """

        try :
            method = getattr(self, 'mpo_'+str(method_name))
        except AttributeError :
            print('method %s not found' %method_name,file=sys.stderr) #send this to stderr
            sys.exit(2)

        if self.MPO_AUTH!='':
            kwargs['cert']=self.MPO_AUTH
            kwargs['verify']=False

        if self.debug>0:
            print("#META command:",method_name,url,args,self.get_user(),kwargs,file=sys.stderr)


        result=method(url,*args,user=self.get_user(),**kwargs)

        #insert comment handling here
        if self.comment!=None:
            if self.debug>0:
                print("Adding a comment "+url+self.comment,file=sys.stderr)
            #body=json comment
            result_comment=self.mpo_comment(url,str(result.content),self.comment)
            self.comment=None

        return result

    def getargs(self):
        """Returns tuple: method,uri,args,kwargs
           If second argument does not start with 'scheme:' where scheme can be http or
           some other protocol, then we check for /etc/mporc, ~/.mporc, $MPO_HOST for a host.

           Expects the form:
           mpo <mpo flags> method_name <url> <method flags>
        """

        flags="vhs:p:f:c:l:r:"
        longflags=["verbose","help","state=","parameters=","file=",
                   "comment=","user=","format="]

        helpstring= textwrap.dedent("""\
                Command line API for the MPO
                ----------------------------
                Arguments are
                {f}
                {lf}
                """.format(f=str(flags),lf=str(longflags)))
        kwargs={}
    #Process commandline
    
        try:
            opts, args = getopt.getopt(sys.argv[1:], flags, longflags)

        except getopt.GetoptError:
            print("Accepted flags are:\n"+str(flags)+"\n"+str(longflags),file=sys.stderr)
            sys.exit(2)
        
        for opt, arg in opts:
            if opt in ("-v","--verbose"):
                self.debug=1
            elif opt in ("-p","--parameters"):
                if self.debug==1:
                    print( 'parameters: ',arg,type(arg),file=sys.stderr)
                #should be a dictionary expression
                kwargs['params']=ast.literal_eval(arg)
            elif opt in ("-h","--help"):
                print(helpstring,file=sys.stderr)
                sys.exit()
            elif opt in ("-s","--state"):
                self.istate=arg
            elif opt in ("-f","--file"):
                self.ifile=arg
            elif opt in ("-c","--comment"):
                self.comment=arg
            elif opt in ("-l","--user"):
                self.set_user(arg)
            elif opt in ("-r","--format"): #pretty, [id], json, xml
                self.response_format=arg

        url=None
        if len(args)==0:
            print("A command must be given",file=sys.stderr)
            sys.exit(1)
        elif len(args)==1: #only method given
            args.append(None)
            args.append(None)
        elif len(args)==2: #method and url or payload
            args.append(None)
        if (self.debug>0):
            print("#CLI opts "+str(opts),file=sys.stderr)
            print("#CLI args "+str(args),file=sys.stderr)
            print("#CLI Added kwargs "+str(kwargs),file=sys.stderr)
            print("#CLI self.istate "+str(self.istate),file=sys.stderr)
            print("#CLI server",str(self.get_server()),url,file=sys.stderr)

        #see if a URL host was given, otherwise grab host from class.
        #JCW Work in progress
        method=args[0]
        rargs=[]

        if len(args)>1:  #Check for url specification
            scheme=urlparse(args[1]).scheme
            if scheme=='http' or scheme=='https':
                url=args[1]
                rargs=args[min(2,len(args)):]
            else:
                url=self.get_server()
                rargs=args[1:]
                
        if self.debug>0:
            print('#CLI: URL constructed ',url,file=sys.stderr)
            
        #args[2:] is helpful or not? Could just use only kwargs
#        return args[0],args[1],args[2:],kwargs #method,uri,args,kwargs
        return method,url,rargs,kwargs

    def getmpohost(self):
        mpohost=None
#	print(os.environ,file=sys.stderr)
        if os.environ.has_key('MPO_HOST'):
            mpohost=os.environ['MPO_HOST']
        return mpohost

    def storeresult(self,result):
        if self.response_format=='ID': #this does not handle lists
            output=[]
            if isinstance(result.json(),list):
                print("Caution, response format of 'id' used when result is a list.",file=sys.stderr)
                print("Returning list of ID's",file=sys.stderr)
                for r in result.json():
                    output.append(str(r[self.ID]))
            else:
                if result.json().has_key(self.ID):
                    output=result.json()[self.ID]
        elif self.response_format=='JSON':
            output=result.json()
        elif self.response_format=='pretty':
            output=json.dumps(result.json(),separators=(',', ':'),indent=4)
        elif self.response_format=='raw':
            output=result.text
        else:
            output=result.json()

        if self.istate=='echo':
            print ("Response URI is "+result.url,file=sys.stderr)
            print (output)
        elif self.istate=='env': #actually, this will not work because we are in a subprocess
            os.environ['MPO_RESULT']=output
        elif self.istate=='file':
            ff=open(self.ifile,'w')
            ff.write(output)
            ff.close()


class mpo_unittest(unittest.TestCase):
    """
    Function to test the mpo interface.
    """
    tests=[
        "http://localhost:3000/wines/"
        ]

    results=[
        '{}'
        ]

####main block
if __name__ == '__main__':
    import mpo_testing

    debug=0
    cli=mpo_testing.mpo_cli()
    if os.environ.has_key('USER'):
        cli.set_user(os.environ['USER'])

    method,hosturl,args,kwargs=cli.getargs()

    if debug>0:
        print("main:", method,hosturl,args,kwargs,file=sys.stderr)

    result=cli.meta(method,hosturl,*args,**kwargs)
    if isinstance(result,requests.models.Response):
        cli.storeresult(result)
    elif result==0 or result==None:
        exit
    elif isinstance(result,dict):
        print("INFO: Python dict data structure returned. Not an http response.",file=sys.stderr)
        print(result)
    else:
        print("mpo request failed, result of method is not a valid response:",file=sys.stderr)
        print("     "+str(type(result)),result,file=sys.stderr)
	print(result)

