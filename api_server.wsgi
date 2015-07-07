import mod_wsgi
import sys
import os

process_group = mod_wsgi.process_group
print('api_server.wsgi in test-api running under process group: ',process_group,str(dir(mod_wsgi)))
print('api_server.wsgi INFO: Make sure to add each source directory to the Directory directive in apache config.')

if process_group=='test-api': #uses test database
   os.environ['MPO_DB_CONNECTION'] = "host='localhost' dbname='mpo_test' user='mpoadmin' password='mpo2013'"
   os.environ['MPO_EDITION'] = "TEST"
   if not '/var/www/test-mposvn/db' in sys.path:
      sys.path.insert(0, '/var/www/prod-mposvn/db') #change this to change which source copy modules are loaded
      sys.path.insert(0, '/var/www/prod-mposvn/server')
elif process_group=='demo-api':
   os.environ['MPO_DB_CONNECTION'] = "host='localhost' dbname='mpo_demo' user='mpoadmin' password='mpo2013'"
   os.environ['MPO_EDITION'] = "DEMO"
   os.environ['DEMO_AUTH'] = "/C=US/ST=Massachusetts/L=Cambridge/O=MIT/O=c21f969b5f03d33d43e04f8f136e7682/OU=PSFC/CN=MPO Demo User/emailAddress=jas@psfc.mit.edu"
   if not '/var/www/demo-mposvn/db' in sys.path:
      sys.path.insert(0, '/var/www/demo-mposvn/db')
      sys.path.insert(0, '/var/www/demo-mposvn/server')
else:
   os.environ['MPO_DB_CONNECTION'] = "host='localhost' dbname='mpoDB' user='mpoadmin' password='mpo2013'"
   os.environ['MPO_EDITION'] = "PRODUCTION"
   if not '/var/www/prod-mposvn/db' in sys.path:
      sys.path.insert(0, '/var/www/prod-mposvn/db')
      sys.path.insert(0, '/var/www/prod-mposvn/server')

os.environ['UDP_EVENTS']='yes'
print('wsgi path ',str(sys.path))

#make sure load path is right
import api_server
print ("wsgi os path: ", os.path.abspath(api_server.__file__) )


from api_server import app as application


