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

import argparse

#Developers note: 
#all print statements except those in mpo_cli.storeresult should go to sys.stderr
#Non-standard dependencies: requests.py
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
    ID='uid'
    MPO_PORT='8080' #not used yet            
    WORKID_QRY='workid' #query argument for connection table

    MPO_VERSION='v0'
    WORKFLOW_RT = 'workflow'
    COMMENT_RT  = 'comment'
    METADATA_RT = 'metadata'
    CONNECTION_RT='connection'
    DATAOBJECT_RT='dataobject'
    ACTIVITY_RT=  'activity'


    def __init__(self, host='https://localhost', version='v0', debug=True, auth_cert=''):
        "Initialize mpo methods class"
        #private class variables
        self.__user="george"
        self.__pass="jungle"
        self.__server=host
        self.debug=debug
        self.MPO_VERSION=version
        self.MPO_HOST=host

        if self.debug:
            print('#MPO user',self.get_user())
            print('#MPO server',self.get_server())

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

    def set_pass(self,passwd):
        self.__pass=passwd

    def get_pass(self):
        return self.__pass


# define api methods here. All methods must be declared as method(**kwargs).
    def init(self,route='default',*a,**kw):
        print('init:',a,kw)
        print('with route', route)
        return


class mpo_cli(object):
    """
    mpo command line interface to restful primitives.
    """

#import foreign classes for methods here

    def __init__(self,api_url='https://localhost:8080',version='v0',
                 user='noone',password='pass',mpo_cert='cert', 
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
        self.mpo=mpo_methods(api_url,version,debug=True)
        
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
        get_parser.add_argument('route',action='store',help='Route of resource to query')
           #add keyword argument passed to func as 'params'
        get_parser.add_argument('--params',action='store',help='Query arguments as {key:value,key2:value2}')
        get_parser.set_defaults(func=self.mpo.init)
        
        #post
        post_parser=subparsers.add_parser('post',help='POST to a route')
        post_parser.add_argument('route',action='store',help='Route of resource to query')
        post_parser.add_argument('--params',action='store',help='Payload arguments as {key:value,key2:value2}')
        post_parser.set_defaults(func=self.mpo.init)

        #init
        init_parser=subparsers.add_parser('init',help='Start a new workflow')
        init_parser.add_argument('name',action='store',help='''Name to assign the workflow\n.
        Label used on workflow graphs.''')
        init_parser.add_argument('description',action='store',help='Describe the workflow')
        init_parser.set_defaults(func=self.mpo.init)

        #add
        add_parser=subparsers.add_parser('add',help='Add a data object to a workflow.')
        addio = add_parser.add_mutually_exclusive_group()
        addio.add_argument('--parent', action='store',dest='parent')
        addio.add_argument('--child', action='store',dest='child')
        add_parser.set_defaults(func=self.mpo.init)

        #step
        step_parser=subparsers.add_parser('step',help='Add an action to a workflow.')
        step_parser.set_defaults(func=self.mpo.init)

        #comment
        comment_parser=subparsers.add_parser('comment',help='Attach a comment an object.')
        comment_parser.add_argument('comment',action='store',help='Text of comment')
        comment_parser.add_argument('--object',action='store',help='UUID of object to comment on',
                                    type=self.type_uuid)
        comment_parser.set_defaults(func=self.mpo.init)

        #meta
        meta_parser=subparsers.add_parser('meta',help='Add an action to a workflow.')
        meta_parser.set_defaults(func=self.mpo.init)

        #archive
        archive_parser=subparsers.add_parser('archive',help='Archive a file or directory')
        archive_parser.add_argument('source',action='append', nargs='+', 
                                    help='File or directory to archive')        
        group = archive_parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--workflow_id','--wid', '-w', nargs=1,
                           help='Workflow ID of the workflow this data is part of')
        group.add_argument('--composite_id','--cid', '-c',
                           help='Composite ID of the workflow this data is part of')
        archive_parser.add_argument('--prefix','--pre', '-p', required=False, 
                                    action='store',
                                    help='Optional string to prefix archived files with')
        archive_parser.set_defaults(func=self.mpo.init)

        #restore
        restore_parser=subparsers.add_parser('restore',help='Restore a file or directory')
        group = restore_parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--workflow_id','--wid', '-w', 
                           help='Workflow ID of the workflow this data is part of')
        group.add_argument('--composite_id','--cid', '-c',
                           help='Composite ID of the workflow this data is part of')
        restore_parser.add_argument('files',action='append', nargs='*',
                                    help='Optional name of file or directory to restore')
        restore_parser.set_defaults(func=self.mpo.init)

        #ls
        ls_parser=subparsers.add_parser('ls',help='list file(s) or directories')
        group = ls_parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--workflow_id','--wid', '-w', 
                           help='Workflow ID of the workflow this data is part of')
        group.add_argument('--composite_id','--cid', '-c',
                           help='Composite ID of the workflow this data is part of')
        ls_parser.add_argument('files',action='append', nargs='*',
                                    help='Optional name of file(s) or directories to list')
        ls_parser.set_defaults(func=self.mpo.init)

        #print parser.parse_args(['-a', '-bval', '-c', '3'])
        # here we handle global arguments
        # now execute method
        args=parser.parse_args()
    #    r=args.func(args._get_args(),args._get_kwargs())
        r=args.func(**args.__dict__)


####main block
if __name__ == '__main__':
    import os
#    from mpo_arg import mpo_cli

    mpo_version=os.getenv('MPO_VERSION','v0')
    mpo_api_url=os.getenv('MPO_API_URL', 'https://localhost:8080/')
    mpo_cert=os.getenv('MPO_CERT', '~/.mpo/mpo_cert')
    archive_host =  os.getenv('MPO_ARCHIVE_HOST', 'psfcstor1.psfc.mit.edu')
    archive_user =  os.getenv('MPO_ARCHIVE_USER', 'psfcmpo')
    archive_key = os.getenv('MPO_ARCHIVE_KEY', '~/.mporsync/id_rsa')
    archive_prefix =  os.getenv('MPO_ARCHIVE_PREFIX', 'mpo-persistent-store/')

    cli_app=mpo_cli(version=mpo_version, api_url=mpo_api_url, 
                    archive_host=archive_host, archive_user=archive_user, 
                    archive_key=archive_key, archive_prefix=archive_prefix, 
                    mpo_cert=mpo_cert)    
    cli_app.cli()
