#!/bin/bash
function key_check {
  key=$1
  if [ ! -O  $key ]
  then
    echo "you must be the owner of $key"
    exit 1
  fi
  keystat=`stat -c %a $key`  #older stat doesn't work on osx

  if [ ${keystat:-600} -ne 600 ]
  then
    echo "The file permissions on $key must be 600"
    exit 1
  fi
}
