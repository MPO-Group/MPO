#!/bin/bash
#
# api_server.sh - script to run the MPO API server.
#
# This script uses uwsgi to to run a local copy of the MPO API server. 
# This server listens on the specified port (default 8443) for https 
# connections.  Clients are verified using X.509 certificates.
#
# Exports the MPO_DB_CONNECTION string so that db.py will know where
# to connect to. 
#
# Uses three ssl PEM files which are in this same directory:
#   MPO_API_SERVER_CERT - mpo.psfc.mit.edu.crt
#        - public certificate for the API server
#   MPO_API_SERVER_KEY - mpo.psfc.mit.edu.key
#        - private key for API server (must be owned by you and 600)
#   MPO_CA_CERT - mpo.psfc.mit.edu-ca.crt
#        - public keys for the acceptable certificate authorities
# 
function usage {
  echo "Usage: $0 -h | [port [db_connection_string]]
  -h                   - print this message
  port                 - network port to listen on [9443]
  db_connection_string - string to connect to the database

  for example:
    ./api_server.sh 8443 'host=localhost dbname=mpoDB user=xxx password="yyy"' 
"
  exit 0
}

if [ $# -ge 1 ]
then
  if [ $1 = "-h" ]
  then
    usage
  fi
fi

myfp=`which $0`
mydir=`dirname $myfp`
. $mydir/functions.sh

PYTHONPATH=$mydir/db:$mydir/server
#this ignores any environmental variable, so you have to give it on the commandline
MPO_DB_CONNECTION=${2:-host=\'localhost\' dbname=\'mpoDB\' user=\'mpoadmin\' password=\'mpo2013\'}
MPO_API_SERVER_PORT=${1:-8443}
MPO_API_SERVER_CERT=$mydir/mpo.psfc.mit.edu.crt
MPO_API_SERVER_KEY=$mydir/mpo.psfc.mit.edu.key
MPO_CA_CERT=\!$mydir/mpo.psfc.mit.edu-ca.crt

key_check $MPO_API_SERVER_KEY

export MPO_DB_CONNECTION
export PYTHONPATH

uwsgi --https "0.0.0.0:$MPO_API_SERVER_PORT,$MPO_API_SERVER_CERT,$MPO_API_SERVER_KEY,HIGH,$MPO_CA_CERT" --wsgi-file $mydir/server/api_server.py  --callable app  

#add this above to redirect logging
#--logto /tmp/mylog.log
