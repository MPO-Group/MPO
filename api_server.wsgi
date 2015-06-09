import mod_wsgi
import sys
import os

process_group = mod_wsgi.process_group
print('api_server.wsgi in test-api running under process group: ',process_group,str(dir(mod_wsgi)))
print('api_server.wsgi INFO: Make sure to add each source directory to the Directory directive in apache config.')

if process_group=='test-api':
   os.environ['MPO_DB_CONNECTION'] = "host='localhost' dbname='mpo_test' user='mpoadmin' password='mpo2013'"
   os.environ['MPO_EDITION'] = "TEST"
   if not '/var/www/test-mposvn/db' in sys.path:
      sys.path.insert(0, '/var/www/test-mposvn/db') #change this to change which source copy modules are loaded
      sys.path.insert(0, '/var/www/test-mposvn/server')
elif process_group=='demo-api':
   os.environ['MPO_DB_CONNECTION'] = "host='localhost' dbname='mpo_demo' user='mpoadmin' password='mpo2013'"
   os.environ['MPO_EDITION'] = "DEMO"
   if not '/var/www/mposvn/db' in sys.path:
      sys.path.insert(0, '/var/www/mposvn/db')
      sys.path.insert(0, '/var/www/mposvn/server')
else:
   os.environ['MPO_DB_CONNECTION'] = "host='localhost' dbname='mpoDB' user='mpoadmin' password='mpo2013'"
   os.environ['MPO_EDITION'] = "PRODUCTION"
   if not '/var/www/mposvn/db' in sys.path:
      sys.path.insert(0, '/var/www/mposvn/db')
      sys.path.insert(0, '/var/www/mposvn/server')

os.environ['UDP_EVENTS']='yes'
print('wsgi path ',str(sys.path))

#make sure load path is right
import api_server
print ("wsgi os path: ", os.path.abspath(api_server.__file__) )


from api_server import app as application


