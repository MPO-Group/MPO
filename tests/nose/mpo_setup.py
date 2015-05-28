#!/usr/bin/env python

### Set up environment
from __future__ import print_function
import os, sys, inspect

# Use this if you want to include modules from a subfolder or relative path.
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(
    inspect.getfile( inspect.currentframe() ))[0],"../../client/python")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)


def setup():
    #default preferences. overridden by environment
    mpo_version    = os.getenv('MPO_VERSION','v0')
    mpo_api_url    = os.getenv('MPO_HOST', 'https://localhost:8443') #API_URL
    mpo_cert       = os.getenv('MPO_AUTH', '../../MPO Demo User.pem')
    archive_host   = os.getenv('MPO_ARCHIVE_HOST', 'psfcstor1.psfc.mit.edu')
    archive_user   = os.getenv('MPO_ARCHIVE_USER', 'psfcmpo')
    archive_key    = os.getenv('MPO_ARCHIVE_KEY', '~/.mpo/rsync_id_rsa')
    archive_prefix = os.getenv('MPO_ARCHIVE_PREFIX', 'mpo-persistent-store/')

    # Load user prefs here, these override any environmental settings or the above defaults.
    userconfdir = os.getenv('HOME')+'/.mpo/'
    userconf = userconfdir+'mpo.conf'
    if os.path.isfile(userconf):
        from ConfigParser import SafeConfigParser
        parser = SafeConfigParser()
        parser.read(userconfdir+'/mpo.conf')
        mpo_api_url = parser.get('api','MPO_HOST')
        mpo_cert = userconfdir+parser.get('api','MPO_AUTH')

    ### Establish a session to mpo
    print('mpo_setup env',mpo_cert,mpo_api_url)
    from mpo_arg import mpo_methods as mpo
    m=mpo(api_url=mpo_api_url,cert=mpo_cert,debug=True,filter='json')
    return m

def teardown(m):
    pass
