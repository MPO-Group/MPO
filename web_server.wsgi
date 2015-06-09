import mod_wsgi
import sys, os, socket

here = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(here,'server'))
os.environ['MPO_WEB_CLIENT_CERT']=os.path.join(here,'MPO-UI-SERVER.crt')
os.environ['MPO_WEB_CLIENT_KEY']=os.path.join(here,'MPO-UI-SERVER.key')
os.environ['MPO_EVENT_SERVER']='https://'+socket.getfqdn()+'/mdsplusEvents'

process_group = mod_wsgi.process_group
print('in web_server.wsgi, running under process group: ',process_group)
#Can configure different API servers for different UI servers if desired.

if process_group=='mpowww': #standard server
   os.environ['MPO_EDITION'] = "PRODUCTION"
   os.environ['MPO_API_SERVER']='https://'+socket.getfqdn()+''
elif process_group=='demo-mpowww': #demo server
   os.environ['MPO_EDITION'] = "DEMO"
   os.environ['DEMO_AUTH'] = "/C=US/ST=Massachusetts/L=Cambridge/O=MIT/O=c21f969b5f03d33d43e04f8f136e7682/OU=PSFC/CN=MPO Demo User/emailAddress=jas@psfc.mit.edu"
   os.environ['MPO_API_SERVER']='https://'+socket.getfqdn()+''

#otherwise, let existing environment stand, eg if using local uWSGI server
print('in web_server.wsgi, environment is: ',os.environ)
from web_server import app as application

