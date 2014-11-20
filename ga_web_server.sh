#!/bin/bash
#
# web_server.sh - script to run the MPO WEB GUI server.
#
# This script uses uwsgi to to run a local copy of the MPO WEB GUI server. 
# This server listens on the specified port (default 9443) for https 
# connections.  Clients are verified using X.509 certificates.
#
# Exports:
# MPO_API_SERVER    - the url of the API server
# MPO_WEB_CLIENT_CERT - the filespec of this server's public key
# MPO_WEB_CLIENT_KEY  - the filespec of this server's private key
#
# Uses five ssl PEM files which are in this same directory:
#   The first two for the certificate that identifes this server for https
#     MPO_WEB_SERVER_CERT - mpo.psfc.mit.edu.crt
#        - public certificate for the WEB server
#     MPO_WEB_SERVER_KEY - mpo.psfc.mit.edu.key
#        - private key for WEB server (must be owned by you and 600)
#   The second two for the certificate that this server uses to identify itself
#   to the API server.
#     MPO_WEB_CLIENT_CERT - MPO-UI-SERVER.crt
#        - public certificate for the WEB server to identify itself to the API server
#     MPO_WEB_CLIENT_KEY - MPO-UI-SERVER.key
#        - private key for the WEB server to idenfify itself to the API server
#          (must be owned by you and 600)
#   MPO_CA_CERT - mpo.psfc.mit.edu-ca.crt
#        - public keys for the acceptable certificate authorities
# 

function usage {
  echo "Usage: $0 -h | [port [api_url ]]
  -h                   - print this message
  port                 - network port to listen on [9443]
  api_url              - https url for the api server [https://localhost:8443]

  for example:
    ./web_server.sh  9443 https://localhost:8443
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
export PYTHONPATH
MPO_API_SERVER=${2:-https://localhost:8443}
MPO_API_VERSION=v0
export MPO_API_SERVER MPO_API_VERSION
MPO_WEB_SERVER_PORT=${1:-9443}
MPO_WEB_CLIENT_CERT=$mydir/MPO-UI-SERVER.crt
MPO_WEB_CLIENT_KEY=$mydir/MPO-UI-SERVER.key
#MPO_WEB_SERVER_CERT=$mydir/mpo.gat.com.crt
#MPO_WEB_SERVER_KEY=$mydir/mpo.gat.com.key
MPO_WEB_SERVER_CERT=$mydir/host_certificate.H4022.mpo.gat.com.pem
MPO_WEB_SERVER_KEY=$mydir/private_key.pem
MPO_CA_CERT=\!$mydir/mpo.psfc.mit.edu-ca.crt
#consistent with event_server.sh for uwsgi
#MPO_EVENT_SERVER="http://localhost:9444/mdsplusEvents"
#use this,otherwise uwsgi redirect needed which has not been done
MPO_EVENT_SERVER="http://localhost:9444/mdsplusWsgi/event"
key_check $MPO_WEB_CLIENT_KEY
key_check $MPO_WEB_SERVER_KEY

export MPO_API_SERVER
export MPO_EVENT_SERVER
export MPO_WEB_CLIENT_CERT
export MPO_WEB_CLIENT_KEY

#uncomment this opt (or set in launching env) to test gevent framework
#export GEVENT_OPT="--gevent 100 --master --pidfile /tmp/web_master.pid"
export THREAD_OPT=--enable-threads
uwsgi $GEVENT_OPT $THREAD_OPT --https  "0.0.0.0:$MPO_WEB_SERVER_PORT,$MPO_WEB_SERVER_CERT,$MPO_WEB_SERVER_KEY,HIGH,$MPO_CA_CERT" --wsgi-file $mydir/server/web_server.py  --callable app

#with --master option, can restart after changes to server with
# uwsgi --reload /tmp/web-master.pid
