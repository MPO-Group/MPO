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
                 archive_prefix=None, debug=True):
    
        self.debug=debug
        self.user=user
        self.password=password
        self.version = version
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


    def get(self,params={},route="",**kwargs):
        """GET a resource from the MPO API server.

        Keyword arguments:
        params -- python dictionary
        route -- API route for resource
        """
        #if parameters are present, this is a search
        #requests.py reconstructs the url with the parameters appended 
        #in the "?param=val" http syntax
        #JCW check on the params syntax for requests

        url=self.api_url+route
        if self.debug:
            print('mpo_GET',url,params,kwargs,file=sys.stderr)

        try:
            r = requests.get(url,params=params,
                             headers=self.GETheaders,**self.requestargs)
        except requests.exceptions.ConnectionError,err:
            #something standard here to be nice to calling routine
            print("ERROR: Could not connect to server, "+url,file=sys.stderr)
            sys.stderr.write('MPO ERROR: %s\n' % str(err))
            print(" ",file=sys.stderr)
            return 1

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


    def archive(self, wid=None, cid=None, prefix=None, *files, **kw):
        """
       if cid != None :
            try:
                wid=self.get_wid(cid)
            except:
                # deal with error workflow not found
                pass
        elif wid != None :
            try:
                cid = self.get_cid(wid)
            except:
                # deal with error workflow not found
                pass
        else:
            # deal with error must specify 1 of them
            pass

        for f in files:

            self.archive_file(cid, f)
        """
        pass



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
    
        self.debug=True
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
        self.mpo=mpo_methods(api_url,version,debug=True,cert=mpo_cert)
        
    def type_uuid(self,uuid):
        if not isinstance(uuid,str):
            msg = "%r is not a valid uuid" % uuid
            raise argparse.ArgumentTypeError(msg)
        return uuid
    
    def cli(self):

        parser = argparse.ArgumentParser(description='MPO Command line API')

	#note that arguments will be available in functions as arg.var

        #global mpo options
        parser.add_argument('--user','-u',action='store',help='''Specify user.''',default=self.user)
        parser.add_argument('--pass','-p',action='store',help='''Specify password.''',default=self.password)

        #method options
        subparsers = parser.add_subparsers(help='commands')

        #get
        get_parser=subparsers.add_parser('get',help='GET from a route')
           #add positional argument which will be passed to func 'route' in 'Namespace' named tuple
        get_parser.add_argument('-r','--route',action='store',help='Route of resource to query')
           #add keyword argument passed to func as 'params'
        get_parser.add_argument('-p','--params',action='store',help='Query arguments as {key:value,key2:value2}')
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
        archive_parser.set_defaults(func=self.mpo.test)

        #restore
        restore_parser=subparsers.add_parser('restore',help='Restore a file or directory')
        group = restore_parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--workflow_id','--wid', '-w', nargs=1, action='store', 
                           help='Workflow ID of the workflow this data is part of')
        group.add_argument('--composite_id','--cid', '-c', nargs=1, action='store',
                           help='Composite ID of the workflow this data is part of')
        restore_parser.add_argument('files', nargs='*',
                                    help='Optional name of file or directory to restore')
        restore_parser.set_defaults(func=self.mpo.test)

        #ls
        ls_parser=subparsers.add_parser('ls',help='list file(s) or directories')
        group = ls_parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--workflow_id','--wid', '-w', nargs=1, action='store',
                           help='Workflow ID of the workflow this data is part of')
        group.add_argument('--composite_id','--cid', '-c', nargs=1, action='store',
                           help='Composite ID of the workflow this data is part of')
        ls_parser.add_argument('files', nargs='*',
                                    help='Optional name of file(s) or directories to list')
        ls_parser.set_defaults(func=self.mpo.test)

        #print parser.parse_args(['-a', '-bval', '-c', '3'])
        # here we handle global arguments
        # now execute method
        args=parser.parse_args()
        kwargs=copy.deepcopy(args.__dict__)
        # strip out 'func' method
        del(kwargs['func'])
        r=args.func(**kwargs)
        return r

####main routine
if __name__ == '__main__':
    import os

    mpo_version    = os.getenv('MPO_VERSION','v0')
    mpo_api_url    = os.getenv('MPO_HOST', 'https://localhost:8080/') #API_URL
    mpo_cert       = os.getenv('MPO_AUTH', '~/.mpo/mpo_cert')
    archive_host   = os.getenv('MPO_ARCHIVE_HOST', 'psfcstor1.psfc.mit.edu')
    archive_user   = os.getenv('MPO_ARCHIVE_USER', 'psfcmpo')
    archive_key    = os.getenv('MPO_ARCHIVE_KEY', '~/.mporsync/id_rsa')
    archive_prefix = os.getenv('MPO_ARCHIVE_PREFIX', 'mpo-persistent-store/')

    cli_app=mpo_cli(version=mpo_version, api_url=mpo_api_url, 
                    archive_host=archive_host, archive_user=archive_user, 
                    archive_key=archive_key, archive_prefix=archive_prefix, 
                    mpo_cert=mpo_cert)    
    result=cli_app.cli()
    print(json.dumps(result.json(),separators=(',', ':'),indent=4))
