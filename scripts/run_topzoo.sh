#!/bin/bash

let "m=1024*1024*14"
ulimit -v $m

let "t=60"
TIMEOUT=$t
TOOL=$1
RESPATH=$2
PROP=$3
FILE=$4
CONCAT=$5
COLLAPSE=$6
OPT=$7
DUMP=$8

timeout $t /usr/bin/time -v python3 allsynth/run.py -t $TOOL --GML $FILE $CONCAT --dir $RESPATH --e-prop $PROP --repeat 1 $COLLAPSE $OPT $DUMP
