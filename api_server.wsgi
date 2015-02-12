import mod_wsgi
import sys
import os

process_group = mod_wsgi.process_group
print('api_server.wsgi running under process group: ',process_group,str(dir(mod_wsgi)))

if process_group=='test-mpoapi':
   os.environ['MPO_DB_CONNECTION'] = "host='localhost' dbname='mpo_test' user='mpoadmin' password='mpo2013'"
   if not '/var/www/test-mposvn/db' in sys.path:
      sys.path.insert(0, '/var/www/test-mposvn/db') #change this to change which source copy modules are loaded
      sys.path.insert(0, '/var/www/test-mposvn/server')
elif process_group=='demo-mpoapi':
   os.environ['MPO_DB_CONNECTION'] = "host='localhost' dbname='mpo_demo' user='mpoadmin' password='mpo2013'"
   if not '/var/www/mposvn/db' in sys.path:
      sys.path.insert(0, '/var/www/mposvn/db')
      sys.path.insert(0, '/var/www/mposvn/server')
else:
   os.environ['MPO_DB_CONNECTION'] = "host='localhost' dbname='mpoDB' user='mpoadmin' password='mpo2013'"
   if not '/var/www/mposvn/db' in sys.path:
      sys.path.insert(0, '/var/www/mposvn/db')
      sys.path.insert(0, '/var/www/mposvn/server')

os.environ['UDP_EVENTS']='yes'
print('wsgi path ',str(sys.path))
from api_server import app as application
import api_server
print os.path.abspath(api_server.__file__) 
