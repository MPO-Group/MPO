import sys
import os
sys.path.insert(0, '/var/www/mposvn/db')
sys.path.insert(0, '/var/www/mposvn/server')
os.environ['UDP_EVENTS']='yes'
os.environ['MPO_DB_CONNECTION'] = "host='localhost' dbname='mpoDB' user='mpoadmin' password='mpo2013'"

from api_server import app as application
