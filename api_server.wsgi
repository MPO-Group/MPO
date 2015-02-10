import mod_wsgi
import sys
import os
sys.path.insert(0, '/var/www/mposvn/db')
sys.path.insert(0, '/var/www/mposvn/server')

process_group = mod_wsgi.process_group
print('api_server.wsgi running under process group: ',process_group)

if process_group=='test-api':
   os.environ['MPO_DB_CONNECTION'] = "host='localhost' dbname='mpo_test' user='mpoadmin' password='mpo2013'"
elif process_group=='demo-api':
   os.environ['MPO_DB_CONNECTION'] = "host='localhost' dbname='mpo_demo' user='mpoadmin' password='mpo2013'"
else:
   os.environ['MPO_DB_CONNECTION'] = "host='localhost' dbname='mpoDB' user='mpoadmin' password='mpo2013'"

os.environ['UDP_EVENTS']='yes'

from api_server import app as application
