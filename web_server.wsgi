import sys, os, socket

here = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(here,'db'))
sys.path.insert(0, os.path.join(here,'server'))
os.environ['MPO_WEB_CLIENT_CERT']=os.path.join(here,'MPO-UI-SERVER.crt')
os.environ['MPO_WEB_CLIENT_KEY']=os.path.join(here,'MPO-UI-SERVER.key')
os.environ['MPO_API_SERVER']='https://'+socket.getfqdn()+'/api'

from web_server import app as application
