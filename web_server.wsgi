import mod_wsgi
import sys, os, socket

here = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(here,'server'))
os.environ['MPO_WEB_CLIENT_CERT']=os.path.join(here,'MPO-UI-SERVER.crt')
os.environ['MPO_WEB_CLIENT_KEY']=os.path.join(here,'MPO-UI-SERVER.key')
os.environ['MPO_EVENT_SERVER']='https://'+socket.getfqdn()+'/mdsplusEvents'

process_group = mod_wsgi.process_group
print('api_server.wsgi running under process group: ',process_group)
if process_group=='test-api':
   os.environ['MPO_API_SERVER']='https://'+socket.getfqdn()+''
elif process_group=='demo-mpoapi':
   os.environ['DEMO_AUTH'] = "/C=US/ST=Massachusetts/L=Cambridge/O=MIT/O=c21f969b5f03d33d43e04f8f136e7682/OU=PSFC/CN=MPO Demo User/emailAddress=jas@psfc.mit.edu"
else:
   os.environ['MPO_API_SERVER']='https://'+socket.getfqdn()+''

from web_server import app as application

