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
st=`pg_ctl status -D $PGDATA`
if [[ "$st" != *PID* ]]
then
   echo ERROR: postgres not running or pg_ctl not in path or PGDATA not correctly set, exiting.
   exit
fi

if ! [ -n "${MPO_HOME:+x}" ]
then
  echo ERROR: need to define MPO_HOME
  exit
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

#start our own database
test_db=mpo_test
createdb $test_db
psql -d $test_db -a -f $MPO_HOME/db/create_tables.sql

#start up api and web servers
$MPO_HOME/api_server.sh $api_port "host=localhost dbname=$test_db user='mpoadmin' password='mpo2013' " &> api_out.txt &
$MPO_HOME/web_server.sh $web_port https://localhost:$api_port &> web_out.txt &

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



echo Commandline tests done. lauch a browser at https://localhost:$api_port to check the web browser client
echo When done, run kill your servers. Inspect api.out.txt and web_out.txt for errors.
ps waux |grep uwsgi|grep $USER
