#!/usr/bin/env python2.7
from __future__ import print_function
if __name__ == '__main__':
    import os, sys, inspect
    from ConfigParser import SafeConfigParser

    DEFAULT_API_SERVER = 'https://mpo.psfc.mit.edu/test-api'
    DEFAULT_API_VERSION = 'v0'
    DEFAULT_API_AUTH = '/etc/MPO Demo User.pem'

    #install path to mpo_arg
    cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(
                    inspect.getfile( inspect.currentframe() ))[0],"./client/python")))
    if cmd_subfolder not in sys.path:
        sys.path.insert(0, cmd_subfolder)
   
    #path of this command
    cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(
                    inspect.getfile( inspect.currentframe() ))[0],"./")))
    if cmd_subfolder not in sys.path:
        sys.path.insert(0, cmd_subfolder)

    from mpo_arg import mpo_cli

#load user prefs here, these override any environmental settings or the above defaults

#first load any global configuration
    globalconf = '/etc/mporc'
    if os.path.isfile(globalconf):
        sparser = SafeConfigParser()
        sparser.read(globalconf)
        mpo_api_url = sparser.get('api','MPO_HOST')
        mpo_version = sparser.get('api','MPO_VERSION')
        mpo_cert = sparser.get('api','MPO_AUTH')
    else: #defaults if no global settings
        mpo_api_url = DEFAULT_API_SERVER
        mpo_version = DEFAULT_API_VERSION
        mpo_cert    = DEFAULT_API_AUTH

#user overrides, either in .mpo directory or .mporc file
    userconfdir = os.getenv('HOME')+'/.mpo/'
    userconf = userconfdir+'mpo.conf'
    uconf = False
    if os.path.isfile(userconf):
        uconf=userconf
    elif os.path.isfile(os.getenv('HOME')+'/.mporc'):
        uconf=os.getenv('HOME')+'/.mporc'

    if uconf:
        parser = SafeConfigParser()
        parser.read(uconf)
        if parser.has_option('api','MPO_HOST'):
            mpo_api_url = parser.get('api','MPO_HOST')
        if parser.has_option('api','MPO_AUTH'):
            mpo_cert = parser.get('api','MPO_AUTH')

#environmental overrides last
    if os.environ.has_key('MPO_VERSION'):
        mpo_version    = os.getenv('MPO_VERSION')
    if os.environ.has_key('MPO_HOST'):
        mpo_api_url    = os.getenv('MPO_HOST')
    if os.environ.has_key('MPO_AUTH'):
        mpo_cert       = os.getenv('MPO_AUTH')

#    archive_host   = os.getenv('MPO_ARCHIVE_HOST', 'psfcstor1.psfc.mit.edu')
#    archive_user   = os.getenv('MPO_ARCHIVE_USER', 'psfcmpo')
#    archive_key    = os.getenv('MPO_ARCHIVE_KEY', '~/.mpo/id_rsa')
#    archive_prefix = os.getenv('MPO_ARCHIVE_PREFIX', 'mpo-persistent-store/')
   
    cli_app=mpo_cli(version=mpo_version, api_url=mpo_api_url, 
                    mpo_cert=mpo_cert)    
    result=cli_app.cli()

   
    print(result,file=sys.stdout)
    

