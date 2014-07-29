#! /usr/bin/env bash 
# protocol: This script creates a test database, populates it with existing test scripts
#           Then dumps data with commandline API
#           User should separately test the UI in the web browser
#This script should be run by a postgres priveledged user

#set api and web ports
if [ $# == 0 ]; then
    api_port=8443
    web_port=9443
fi
if [ $# == 1 ]; then
    api_port=$1
    web_port=9443
fi
if [ $# == 2 ]; then
    api_port=$1
    web_port=$2
fi

export MPO_HOST=https://localhost:$api_port

#test that postgres is running and test for needed environmental variables
#pg_ctl should be in path, eg /usr/lib/postgresql/9.1/bin/pg_ctl
#This creates problems on systems with postgres user
#st=`pg_ctl status -D $PGDATA`
#if [[ "$st" != *PID* ]]
#then
#   echo ERROR: postgres not running or pg_ctl not in path or PGDATA not correctly set, exiting.
#   exit
#fi

if ! [ -n "${MPO_HOME:+x}" ]
then
  echo WARNING: MPO_HOME not defined, using defaults.
  export MPO_HOME=$(dirname $0)/../
  echo Home is $MPO_HOME
fi

if ! [ -n "${PGDATA:+x}" ]
then
  echo WARNING: PGDATA not defined, using defaults.
  export PGDATA=$MPO_HOME/db/data
fi

if ! [ -n "${MPO_VERSION:+x}" ]
then
  export MPO_VERSION=v0
fi

if ! [ -n "${MPO:+x}" ]
then
  export MPO=$MPO_HOME/client/python/mpo_testing.py
fi

export MPO_AUTH=$MPO_HOME/'MPO Demo User.pem'
echo env is
env

#start our own database
test_db=mpo_test
dropdb $test_db
createdb $test_db
psql -d $test_db -a -f $MPO_HOME/db/create_tables.sql

#start up api and web servers
echo Starting up uwsgi servers
$MPO_HOME/api_server.sh $api_port "host=localhost dbname=$test_db user='mpoadmin' password='mpo2013' " &> api_out.txt &
$MPO_HOME/web_server.sh $web_port https://localhost:$api_port &> web_out.txt &

echo %TESTING first create the ontology terms %%%%%%%%%%%%
$MPO_HOME/client/python/tests/ontology_terms_gyro.load
$MPO_HOME/client/python/tests/ontology_terms_swim.load
$MPO_HOME/client/python/tests/ontology_terms_efit.load

echo %TESTING postings with commandline api %%%%%%%%%%%%%%
$MPO_HOME/client/python/tests/josh.test
$MPO_HOME/client/python/tests/api_test.sh
$MPO_HOME/client/python/tests/gyro_out_parse.sh $MPO_HOME/client/python/tests/run1 'Testing api scripts'


echo %TESTING retrievals %%%%%%%%%%%%%%
for route in workflow comment activity metadata dataobject
do
  echo %---------------route $route------------------------
  $MPO --format=pretty -v get --route=$route
done



echo Commandline tests done. launch a browser at https://localhost:$web_port to check the web browser client
echo When done, run kill your servers. Inspect api.out.txt and web_out.txt for errors.
ps waux |grep uwsgi|grep $USER
