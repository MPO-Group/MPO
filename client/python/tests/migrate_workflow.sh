#!/bin/sh
#specify MPO server address. The API will read this value.
#defaults are used if environment is not set
if ! [ -n "${MPO_HOST:+x}" ]
then
  export MPO_HOST=https://localhost:8443
fi


if ! [ -n "${MPO_VERSION:+x}" ]
then
  export MPO_VERSION=v0
fi


if ! [ -n "${MPO_HOME:+x}" ]
then
  echo MPO_HOME not defined, exitting
  exit
fi

if ! [ -n "${MPO:+x}" ]
then
  export MPO="$MPO_HOME/client/python/mpo_testing.py --user=$USER"
fi

for name in 'EFIT' 'SWIM' 'Gyro'
do
  wids=(`$MPO get -r workflow -p name=$name`)
  for wid in ${wids[*]}
    do
      w=`echo $wid | sed -e 's/\[//' | sed 's/,//' | sed 's/\]//' | sed "s/'//g"`
      echo $w
      r=`$MPO ontology_instance $w '/Workflow/Type' $name`
      echo $r
  done
done
