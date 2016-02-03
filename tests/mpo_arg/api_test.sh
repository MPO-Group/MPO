#!/bin/sh

#specify MPO server address. The API will read this value.
#defaults are used if environment is not set
if ! [ -n "${MPO_HOST:+x}" ]
then
  export MPO_HOST=https://localhost
fi


if ! [ -n "${MPO_VERSION:+x}" ]
then
  export MPO_VERSION=v0
fi

if ! [ -n "${MPO:+x}" ]
then
  export MPO="$MPO_HOME/client/python/mpo_arg.py"
fi

#use API methods to create a workflow
wid=`$MPO init --name=EFIT --desc=test --type=EFIT`
oid=`$MPO add  $wid $wid --name=shot --desc="Plasma shot number" --uri=150335`
oid2=`$MPO add  $wid $wid --name="Snap file" --desc="EFIT input file" --uri="\\efit01:namelist"`
aid=`$MPO step $wid $oid --input=$oid2 --name="EFIT exec" --desc="Fit equilibrium and compute plasma parameters" `
cid=`$MPO comment $aid "This program is the only one in this workflow"`

#useful?:
#$MPO end $wid -c "I'm done with this workflow"
