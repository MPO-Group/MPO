#!/usr/bin/env python
"""
Test commandline parsing
Will permit all parsing to be moved to the meta command where it belongs.
Then methods can stay put functional invocation.
argument layout for mpo:
post
get
not implemented: delete
not implemented: put
add
step
init
comment
record/meta
help

"""
from __future__ import print_function
import requests
import ast, textwrap
import unittest
import sys,os,datetime
import json
from urlparse import urlparse
import copy
import argparse

class shell_exception(Exception):
    def __init__(self, status, *args, **kwargs):
        self.return_status=status
        Exception.__init__(self, *args, **kwargs)

#Developers note:
#all print statements except those in mpo_cli.storeresult should go to sys.stderr
#Non-standard dependencies: requests.py
class mpo_methods(object):
    """
    Class of RESTful primitives. I/O is through stdin/stdout.
    Implementation of MPO client side API as described at
    http://www.psfc.mit.edu/mpo/

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
    ID='uid'
    WORKID='work_uid'
    PARENTID='parent_uid' #field for object id to which comments and metadata are attached
    MPO_PORT='8080' #not used yet
    WORKID_QRY='workid' #query argument for connection table

    MPO_VERSION='v0'
    WORKFLOW_RT = 'workflow'
    COMMENT_RT  = 'comment'
    METADATA_RT = 'metadata'
    CONNECTION_RT='connection'
    DATAOBJECT_RT='dataobject'
    ACTIVITY_RT=  'activity'


    def __init__(self,api_url='https://localhost:8080',version='v0',
                 user='noone',password='pass',cert='cert',
                 archive_host='psfcstor1.psfc.mit.edu',
                 archive_user='psfcmpo', archive_key=None,
                 archive_prefix=None, debug=False,filter=False):

        self.debug=debug
        self.filter=filter
        self.user=user
        self.password=password
        self.version=version
        self.cert=cert
        self.archive_host=archive_host
        self.archive_user=archive_user
        self.archive_key=archive_key
        self.archive_prefix=archive_prefix
        o=urlparse(api_url)
         #makes a clean url ending in trailing slash
        self.api_url=o.scheme+"://"+o.netloc+o.path+'/'+self.version+'/'
        self.requestargs={'cert':self.cert,'verify':False}

        if self.debug:
#            print('#MPO user',self.get_user())
#            print('#MPO server',self.get_server())
            pass
        return


# define api methods here. All methods must be declared as method(**kwargs).
    def test(self,route='default',*a,**kw):
        print('init:',a,kw)
        print('with route', route)
        return


    def format(self,result,filter='id'):
        """
        Routine to handle reformatting of responses from submethods. It is aware of the
        internal format returned.
        """

        #check that result is a request object.
        # if isinstance(result,requests.models.Response):

        if filter=='id':
            output=[]
            if isinstance(result.json(),list):
                print("Caution, response format of 'id' used when result is a list.",file=sys.stderr)
                print("Returning list of ID's",file=sys.stderr)
                for r in result.json():
                    output.append(str(r[self.ID]))
            else:
                if result.json().has_key(self.ID):
                    output=result.json()[self.ID]
        elif filter=='json':
            output=result.json()
        elif filter=='pretty':
            output=json.dumps(result.json(),separators=(',', ':'),indent=4)
        elif filter=='raw':
            output=result
        elif filter=='text':
            output=result.text
        else:
            output=result.json()

        return output

    def get(self,route="",params={},verbose=False,**kwargs):
        import re
        """GET a resource from the MPO API server.

        Keyword arguments:
        params -- python dictionary or a list of tuples
        route -- API route for resource
        """
        #if parameters are present, this is a search
        #requests.py reconstructs the url with the parameters appended
        #in the "?param=val" http syntax
        #JCW check on the params syntax for requests
        #check for dict and str instances, requests expects a dict


        url=self.api_url+route
        if self.debug or verbose:
            print('mpo_GET',url,params,kwargs,file=sys.stderr)


        if isinstance(params,str): #string repr of a dict
            datadict=ast.literal_eval(params)
        elif isinstance(params,dict):
            datadict=params
        elif isinstance(params,list): #list of key=value strings
            datadict=dict(re.findall(r'(\S+)=(".*?"|\S+)', ' '.join(params) ))
        else:
            #throw error
            datadict={}


        r = requests.get(url,params=datadict,
                             headers=self.GETheaders,**self.requestargs)
        r.raise_for_status()
        if self.debug or verbose:
            print('mpo_GET response',r.url,r.status_code,file=sys.stderr)

        if self.filter:
            r=self.format(r,self.filter)

        return r


    def post(self,route="",workflowID=None,objID=None,data=None,**kwargs):
        """POST a messsage to an MPO route.
        Used by all methods that create objects in an MPO workflow.

        Keyword arguments:
        workflowID -- the workflow being added to
        objID -- the object we are making a connection from
        data -- the object being posted
        """
        #need flexible number of args so you can just post to a url.

        # Need to validate body? No, servers job.
        # We might want to use different headers?
        # handling binary data, or data in a file?
        # requests.post is happy to take those in the data argument but server has to handle it.
        # mongo returns {time:,_id:} by default
        # could parse data so see if starts with file:

        if route=="":
            #throw error
            return

        if isinstance(data,str):
            datadict=ast.literal_eval(data)
        elif isinstance(data,dict):
            datadict=data
        else:
            #throw error
            pass

        url=self.api_url+route

        if self.debug>0:
            print('MPO.POST',url,json.dumps(datadict),file=sys.stderr)

        if objID:
            datadict[self.PARENTID]=objID

        if workflowID:
            datadict[self.WORKID]=workflowID

        # note we convert python dict to json format and tell the server and requests.py
        #    in the header it is JSON
        # requests will actually send the dict directly if headers doesn't declare body type
        try:
            r = requests.post(url, json.dumps(datadict),
                              headers=self.POSTheaders, **self.requestargs)
        except requests.exceptions.ConnectionError,err:
            print("ERROR: Could not connect to server, "+url,file=sys.stderr)
            sys.stderr.write('MPO ERROR: %s\n' % str(err))
            print(" ",file=sys.stderr)
            return 1

        if r.status_code!=200:
            return r.status_code, r.text
        else:
            if self.filter:
                r=self.format(r,self.filter)
            return r

    def comment(self,object,comment,**kwargs):
        """Takes a returned record and adds a comment to it.
        In this case, data should be a plain string.
        """
        if not (isinstance(comment,str) or isinstance(comment,unicode)):
            print('Error in mpo_commment, should be a plain string')
            return -1

        r=self.post(self.COMMENT_RT,objID=object,data={'content':str(comment)})
        return r

    def get_wid(self, cid):
        self.filter='id'
        res = self.get("%s?alias=%s"%(self.WORKFLOW_RT, cid[0]))
        return res[0]

    def get_cid(self, wid):
        self.filter='json'
        res = self.get("%s/%s/alias"%(self.WORKFLOW_RT, wid[0],))
        ans = res[u'alias']

        if self.debug>0:
            print("get_cid returning %s"%ans,file=sys.stderr)
        return ans


    def search(self,route,params,**kwargs):
        """Find objects by query. An supermethod of GET.
        Presently, identical to 'get' but can be generalized.

        Keyword arguments:
        params -- python dictionary
        route -- API route for resource
        """
        #Presently, route is specified but search syntax should be developed.
        #eventually, some specialized target route for searching would be used.

        r=self.get(route,params) # ,params=ast.literal_eval(params))
        return r

    def shell(self,cmd):
        import subprocess
        import sys
        retcode = subprocess.call(cmd,shell=True)
        if retcode != 0:
            raise shell_exception(retcode, "Error Executing command %s - returned %d"%(cmd,retcode,))

    def archive_file(self, cid, prefix, name):
        import os
        if self.debug:
            print("archive_file", cid, prefix, name, file=sys.stderr)
        destspec=None
        if name:
            if os.path.isfile(name):
                if os.access(name, os.R_OK):
                    destspec=name
            elif os.path.isdir(name):
                if os.access(name, os.R_OK):
                    if os.access(name, os.X_OK):
                        destspec=name
        if not destspec:
            raise Exception("Source not specified or not readable - can not archive")
        ans=""
        if self.archive_prefix:
            ans = "%s/"%(self.archive_prefix,)
        if prefix:
            ans = "%s/%s/"%(ans, prefix,)
        ans = "%s%s"%(ans,cid,)
        cmd=" ssh  -i %s %s@%s mkdir -p %s"%(self.archive_key,self.archive_user,self.archive_host,ans,)
        self.shell(cmd)
        destspec="%s/%s"%(ans,destspec,)
        cmd="rsync -av -e \"ssh -i %s\" %s %s@%s:%s"%(self.archive_key,
                                                      name,
                                                      self.archive_user,
                                                      self.archive_host,
                                                      destspec,)
        if self.debug:
            print("archive_file about to '%s'"%(cmd,), file=sys.stderr)
        self.shell(cmd)
        ans = "rsync://%s/%s"%(self.archive_host,destspec)
        return ans

    def archive(self, prefix=None, workflow_id=None, composite_id=None, source=None, *arg,  **kw):
        if self.debug:
            print('archive', workflow_id, composite_id, source, file=sys.stderr)
        if composite_id != None :
            wid=self.get_wid(composite_id)
            cid=composite_id[0]
        elif workflow_id != None :
            cid = self.get_cid(workflow_id)
        else:
            raise Execption("one of workflow_id or composite_id must be specified")
        url = self.archive_file(cid, prefix, source[0])
        return url

    def ls_archive(self, cid, prefix, files):
        path = ""
        if self.archive_prefix:
            path=self.archive_prefix
        if prefix:
            path="%s%s" %(path, prefix)
        path="%s%s"%(path,cid,)
        paths = ""
        for f in files:
            paths+="%s/%s "%(path, f)
        cmd = "ssh -i %s %s@%s ls -Rl %s"%(self.archive_key,self.archive_user,self.archive_host, paths,)
        if self.debug:
            print ("about to execute ", cmd, file=sys.stderr)
        try:
            ans = self.shell(cmd)
        except shell_exception,e:
            ans=None
            if e.return_status !=2:
                raise
        return ans

    def ls(self, prefix=None, workflow_id=None, composite_id=None, files=None, *arg,  **kw):
        if self.debug:
            print('ls', workflow_id, composite_id, files, file=sys.stderr)
        if composite_id != None :
            wid=self.get_wid(composite_id)
            cid=composite_id[0]
        elif workflow_id != None :
            cid = self.get_cid(workflow_id)
        else:
            raise Execption("one of workflow_id or composite_id must be specified")

        answer = self.ls_archive(cid, prefix, files)
        return answer

    def restore_archive(self, cid, prefix, filename):
        path = ""
        if self.archive_prefix:
            path=self.archive_prefix
        if prefix:
            path="%s%s" %(path, prefix)
        path="%s%s/%s"%(path,cid,filename,)
        cmd = "rsync -av  -e \"ssh  -i %s\" %s@%s:%s ."%(self.archive_key, self.archive_user, self.archive_host, path,)
        if self.debug:
            print ("about to execute ", cmd, file=sys.stderr)

        ans = self.shell(cmd)
        return ans

    def restore(self, prefix=None, workflow_id=None, composite_id=None, filename=None, *arg,  **kw):
        if self.debug:
            print('restore', workflow_id, composite_id, filename, file=sys.stderr)
        if composite_id != None :
            wid=self.get_wid(composite_id)
            cid=composite_id[0]
        elif workflow_id != None :
            cid = self.get_cid(workflow_id)
        else:
            raise Execption("one of workflow_id or composite_id must be specified")

        answer = self.restore_archive(cid, prefix, filename[0])
        return answer


class mpo_cli(object):
    """
    mpo command line interface to restful primitives.
    Commandline invocation:
    mpo <mpo flags> method <url> <method flags> <payload>
    """

#import foreign classes for methods here

    def __init__(self,api_url='https://localhost:8080',version='v0',
                 user='noone',password='pass',mpo_cert='',
                 archive_host='psfcstor1.psfc.mit.edu',
                 archive_user='psfcmpo', archive_key=None,
                 archive_prefix=None):

        self.debug=False
        self.api_url=api_url
        self.user=user
        self.password=password
        self.version = version
        self.cert=mpo_cert
        self.archive_host=archive_host
        self.archive_user=archive_user
        self.archive_key=archive_key
        self.archive_prefix=archive_prefix

        #initialize foreign methods here
        self.mpo=mpo_methods(api_url,version,debug=self.debug,cert=mpo_cert,archive_key=archive_key)

    def type_uuid(self,uuid):
        if not isinstance(uuid,str):
            msg = "%r is not a valid uuid" % uuid
            raise argparse.ArgumentTypeError(msg)
        return uuid


    def cli(self):

        parser = argparse.ArgumentParser(description='MPO Command line API',
                                         epilog="""Metadata Provenance Ontology project""")

    #note that arguments will be available in functions as arg.var

        #global mpo options
        parser.add_argument('--user','-u',action='store',help='''Specify user.''',default=self.user)
        parser.add_argument('--pass','-p',action='store',help='''Specify password.''',
                            default=self.password)
        parser.add_argument('--format','-f',action='store',help='Set the format of the response.',
                            choices=['id','raw','text','json','pretty'], default='id') #case insensitive?
        parser.add_argument('--verbose','-v',action='store_true',help='Turn on debugging info',
                            default=False)

        #method options
        subparsers = parser.add_subparsers(help='commands')

        #get
        get_parser=subparsers.add_parser('get',help='GET from a route')
           #add positional argument which will be passed to func 'route' in 'Namespace' named tuple
        get_parser.add_argument('-r','--route',action='store',help='Route of resource to query')
           #add keyword argument passed to func as 'params'
        get_parser.add_argument('-p','--params',action='store',nargs='*',
                                help='Query arguments as {key:value,key2:value2}')
        get_parser.set_defaults(func=self.mpo.get)

        #post
        post_parser=subparsers.add_parser('post',help='POST to a route')
        post_parser.add_argument('route',action='store',help='Route of resource to query')
        post_parser.add_argument('--params',action='store',help='Payload arguments as {key:value,key2:value2}')
        post_parser.set_defaults(func=self.mpo.post)

        #init
        init_parser=subparsers.add_parser('init',help='Start a new workflow')
        init_parser.add_argument('name',action='store',help='''Name to assign the workflow\n.
        Label used on workflow graphs.''')
        init_parser.add_argument('description',action='store',help='Describe the workflow')
        init_parser.set_defaults(func=self.mpo.test)

        #add
        add_parser=subparsers.add_parser('add',help='Add a data object to a workflow.')
        addio = add_parser.add_mutually_exclusive_group()
        addio.add_argument('--parent', action='store',dest='parent')
        addio.add_argument('--child', action='store',dest='child')
        add_parser.set_defaults(func=self.mpo.test)

        #step
        step_parser=subparsers.add_parser('step',help='Add an action to a workflow.')
        step_parser.set_defaults(func=self.mpo.test)

        #comment
        comment_parser=subparsers.add_parser('comment',help='Attach a comment an object.')
        comment_parser.add_argument('object',action='store',
                                    help='UUID of object to comment on',
                                    type=self.type_uuid)
        comment_parser.add_argument('comment',action='store',help='Text of comment')
        comment_parser.set_defaults(func=self.mpo.comment)

        #meta
        meta_parser=subparsers.add_parser('meta',help='Add an action to a workflow.')
        meta_parser.set_defaults(func=self.mpo.test)


        #search
        search_parser=subparsers.add_parser('search',help='SEARCH the MPO store')
           #add positional argument which will be passed to func 'route' in 'Namespace' named tuple
        search_parser.add_argument('-r','--route',action='store',help='Route of resource to query')
           #add keyword argument passed to func as 'params'
        search_parser.add_argument('-p','--params',action='store',help='Query arguments as {key:value,key2:value2}')
        search_parser.set_defaults(func=self.mpo.search)

        #archive
        archive_parser=subparsers.add_parser('archive',help='Archive a file or directory')
        archive_parser.add_argument('source', nargs=1,
                                    help='File or directory to archive')
        group = archive_parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--workflow_id','--wid', '-w', nargs=1, action='store',
                           help='Workflow ID of the workflow this data is part of')
        group.add_argument('--composite_id','--cid', '-c',nargs=1, action='store',
                           help='Composite ID of the workflow this data is part of')
        archive_parser.add_argument('--prefix','--pre', '-p', required=False,
                                    action='store',
                                    help='Optional string to prefix archived files with')
        archive_parser.set_defaults(func=self.mpo.archive)

        #restore
        restore_parser=subparsers.add_parser('restore',help='Restore a file or directory')
        group = restore_parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--workflow_id','--wid', '-w', nargs=1, action='store',
                           help='Workflow ID of the workflow this data is part of')
        group.add_argument('--composite_id','--cid', '-c', nargs=1, action='store',
                           help='Composite ID of the workflow this data is part of')
        restore_parser.add_argument('filename', nargs=1,
                                    help='Optional name of file or directory to restore')
        restore_parser.set_defaults(func=self.mpo.restore)

        #ls
        ls_parser=subparsers.add_parser('ls',help='list file(s) or directories')
        group = ls_parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--workflow_id','--wid', '-w', nargs=1, action='store',
                           help='Workflow ID of the workflow this data is part of')
        group.add_argument('--composite_id','--cid', '-c', nargs=1, action='store',
                           help='Composite ID of the workflow this data is part of')
        ls_parser.add_argument('files', nargs='*',
                                    help='Optional name of file(s) or directories to list')
        ls_parser.set_defaults(func=self.mpo.ls)

        #print parser.parse_args(['-a', '-bval', '-c', '3'])
        # here we handle global arguments
        # now execute method
        args=parser.parse_args()
        kwargs=copy.deepcopy(args.__dict__)
        # strip out 'func' method
        del(kwargs['func'])
        if self.debug:
            print('args',str(args.__dict__))

        try:
            r=args.func(**kwargs)
        except Exception,e:
            print("error executing command\n%s"%e, file=sys.stderr)
            return 0
        if kwargs.has_key('format'):
            r=self.mpo.format(r,filter=kwargs['format'])
        return r

####main routine
if __name__ == '__main__':
    import os

    mpo_version    = os.getenv('MPO_VERSION','v0')
    mpo_api_url    = os.getenv('MPO_HOST', 'https://localhost:8080/') #API_URL
    mpo_cert       = os.getenv('MPO_AUTH', '~/.mpo/mpo_cert.pem')
    archive_host   = os.getenv('MPO_ARCHIVE_HOST', 'psfcstor1.psfc.mit.edu')
    archive_user   = os.getenv('MPO_ARCHIVE_USER', 'psfcmpo')
    archive_key    = os.getenv('MPO_ARCHIVE_KEY', '~/.mporsync/id_rsa')
    archive_prefix = os.getenv('MPO_ARCHIVE_PREFIX', 'mpo-persistent-store/')

    cli_app=mpo_cli(version=mpo_version, api_url=mpo_api_url,
                    archive_host=archive_host, archive_user=archive_user,
                    archive_key=archive_key, archive_prefix=archive_prefix,
                    mpo_cert=mpo_cert)
    result=cli_app.cli()
#    print(json.dumps(result.json(),separators=(',', ':'),indent=4))
    print(result)
