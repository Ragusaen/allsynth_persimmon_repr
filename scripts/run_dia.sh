#!/bin/bash

let "m=1024*1024*14"
ulimit -v $m

let "t=3600*2"
TIMEOUT=$t

TOOL=$1
RESPATH=$2
PROP=$3
INDEX=$4
COLLAPSE=$5
OPT=$6
DUMP=$7

timeout $t /usr/bin/time -v python3.8 allsynth/run.py -t $TOOL -e diamond --dir $RESPATH --index $INDEX --e-prop $PROP --repeat 1 $COLLAPSE $OPT $DUMP