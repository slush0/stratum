#!/bin/bash
CURDIR=$(pwd)

cd $CURDIR/protob

for i in stratum ; do
    protoc --python_out=../stratum/ -I/usr/include -I. $i.proto
done
