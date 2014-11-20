#!/usr/bin/env bash 

#GYRO setup
#function to retrieve gyro metadata
#arg is dir path /exports/data1/gyro/test_dirs/87513_.7_5

if [ $# == 0 ]; then
    echo Usage: $0 directory_to_archive comment
    exit
fi
rundir=$1


###Set the output file to parse and the variables desired.
#This script expects variables in the output file of the format
# .variable : value
#on each line
outfile=out.gyro.run
vars=(RADIUS DLNTDR DLNNDR_ELECTRON DLNTDR_ELECTRON) #list of gyro variable to record

gyrofile=$rundir/$outfile
#bash function to parse $vars from $outfile into JSON or plain value
function gyro_kv_json {
    sed -n "s/^[ ]\+\.\($2\)[ ]\+:[ ]\+\([0-9\.]*\)/\{\"name\":\"\1\",\"value\":\2}/p" $1
}

function gyro_kv_bash {
    sed -n "s/^[\ ]\.$2[\ ]*:[\ ]*\([0-9\.]*\)/\1/p" $1
}

#    sed -n "s/^[ ]\+\.\($2\)[ ]\+:[ ]\+\([0-9\.]*\)/\2/p" $1

#populate array $metav with key value pairs for $vars list
declare -A metav
for name in "${vars[@]}"; do metav[$name]=`gyro_kv_bash $gyrofile $name`; done


###MPO setup
#specify MPO server address. The API will read this value.
#defaults are used if environment is not set
if ! [ -n "${MPO_HOST:+x}" ]
then
  export MPO_HOST=http://localhost:3001
fi


if ! [ -n "${MPO_VERSION:+x}" ]
then
  export MPO_VERSION=v0
fi

if ! [ -n "${MPO:+x}" ]
then
  export MPO="$MPO_HOME/client/python/mpo_testing.py"
fi

swift_root=http://localhost:8080/v1/AUTH_0d63fa5f677f4042b7c359598c2e25bb
SWIFT=/usr/bin/swift
mpo_user=nthoward
run_comment=$(cat <<- EOF #describe the run here
Imported run.
EOF
);
if [ $# == 2 ]; then
  run_comment="$2"
fi

#############Record GYRO storage workflow###################

#Initialize workflow
wid=`$MPO --user=$mpo_user init --name=Archive-GYRO --desc="Import of gyro simulation results from $rundir" --type=Gyro`
echo Workflow ID is $wid.

#Comment on the workflow
$MPO --user=$mpo_user comment    $wid "$run_comment"

#Get alias for the workflow
compid=`$MPO  get workflow/$wid/alias`

#Add an action to the workflow
aid=`$MPO --user=$mpo_user step       $wid $wid --name="Archive" --desc="Store run and extract meta data."`

#Add an output of this action to the workflow
#uri points to resource location, in this case the swift object store
#created
oid=`$MPO --user=$mpo_user add        $wid $aid --name="Archive Store" --desc="Location of archived files." --uri=swift:$swift_root/$mpo_user/$rundir`

#Store files in archive
#comp_id alias is prepended to upload path for uniqueness
##$SWIFT --os-auth-url http://localhost:5000/v2.0 -U mpo:$mpo_user -K try-mpo-swift  upload -c mpo/$compid/ $rundir

#Record location in metadata of the archive object
$MPO --user=$mpo_user meta $oid archive swift:$swift_root/$mpo_user/$oid/$rundir

#attach key/value pairs to the workflow as searchable metadata
for i in "${!metav[@]}"
do
  echo "storing key  : $i" ",  value: ${metav[$i]}"
  $MPO --user=$mpo_user meta $wid $i ${metav[$i]}
done

#Store the directory and machine that was archived 
$MPO --user=$mpo_user meta $wid 'sourcedir' "`hostname -f` : $rundir"

#finalize the workflow (currently a nop)
#$MPO --user=$mpo_user stop $wid

#grab timestamp - not in unique location
#move command?
#record move command
#end workflow (no command or convention for this yet)
#search batch.out for runtime, host
