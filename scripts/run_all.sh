#!/bin/bash

SCRIPT=$1
NAME=$2
START=$3
STOP=$4
STEP=$5
PROPS=$6

n=0
while (($n<3))
do
    for PROP in $PROPS
    do
        for ((i=START;i<=STOP;i=i+STEP));
        do
            # Reduce
            mkdir -p $NAME/$PROP/reduce/BDD-$n
            ./$SCRIPT BDD $NAME/$PROP/reduce/BDD-$n $PROP $i --reduce &> $NAME/$PROP/reduce/BDD-$n\/$i.log 

            # NS
            mkdir -p $NAME/$PROP/NS/NS-$n
            ./$SCRIPT NS $NAME/$PROP/NS/NS-$n $PROP $i &> $NAME/$PROP/NS/NS-$n\/$i.log 

            # FLIP
            if [[ $PROP != "SC" ]]
            then
                mkdir -p $NAME/$PROP/FLIP/FLIP-$n
                ./$SCRIPT FLIP $NAME/$PROP/FLIP/FLIP-$n $PROP $i &> $NAME/$PROP/FLIP/FLIP-$n\/$i.log 
            fi
        done
    done
	n=$(( n + 1))
done