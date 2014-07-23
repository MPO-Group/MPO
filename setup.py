#!/usr/bin/env python
# need
# sudo apt-get install build-essential gcc python-dev python-pip ipython graphviz #ipython optional
# For postgres build:
# apt-get install libreadline-dev libz1-dev libxml2-dev libxslt1-dev sp xsltproc
#recommend building from source: http://www.postgresql.org/ftp/source/v9.3rc1
import os, subprocess, sys

if sys.platform == 'win32':
    bin = 'Scripts'
else:
    bin = 'bin'

pip="pip"
subprocess.call(['python', 'virtualenv.py', 'flask'])
subprocess.call([os.path.join('flask', bin, pip), 'install', 'setuptools<3.0'])
subprocess.call([os.path.join('flask', bin, pip), 'install', 'simplejson>2.2'])
subprocess.call([os.path.join('flask', bin, pip), 'install', 'flask>0.9'])
subprocess.call([os.path.join('flask', bin, pip), 'install', 'flask-login'])
subprocess.call([os.path.join('flask', bin, pip), 'install', 'flask-cors'])
subprocess.call([os.path.join('flask', bin, pip), 'install', 'psycopg2']) #requires postgres to be installed
subprocess.call([os.path.join('flask', bin, pip), 'install', 'requests'])
subprocess.call([os.path.join('flask', bin, pip), 'install', 'sqlalchemy==0.7.9'])
subprocess.call([os.path.join('flask', bin, pip), 'install', 'flask-sqlalchemy'])
subprocess.call([os.path.join('flask', bin, pip), 'install', 'https://pypi.python.org/packages/source/p/pyparsing/pyparsing-1.5.7.tar.gz'])
subprocess.call([os.path.join('flask', bin, pip), 'install', '-U', 'pydot', 'pyparsing==1.5.7'])
subprocess.call([os.path.join('flask', bin, pip), 'install', 'uwsgi>1.3'])

#needed by command line client and python class
#requests
