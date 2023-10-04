#!/bin/bash

SCRIPT=scripts/run_topzoo.sh
NAME=$1
PROPS=$2
CONCAT=$3
DIR=$4

#FILES=./topologies/topzoo/*.gml
CONCAT=5

GML_NAME=""

n=0
while (($n<3))
do
    for PROP in $PROPS
    do
        for file in "$DIR"/*
        do
            GML_NAME=$(basename $file)
	    echo "$GML_NAME"
            # Reduce
            #mkdir -p $NAME/$PROP/reduce/BDD-$n
            #./$SCRIPT BDD $NAME/$PROP/reduce/BDD-$n $PROP "$file" $CONCAT --reduce &> $NAME/$PROP/reduce/BDD-$n\/$CONCAT$GML_NAME.log

            # NS
            #mkdir -p $NAME/$PROP/NS/NS-$n
            #./$SCRIPT NS $NAME/$PROP/NS/NS-$n $PROP "$file" $CONCAT &> $NAME/$PROP/NS/NS-$n\/$CONCAT$GML_NAME.log

            # FLIP
            #if [[ $PROP != "SC" ]]
            #then
            #    mkdir -p $NAME/$PROP/FLIP/FLIP-$n
            #    ./$SCRIPT FLIP $NAME/$PROP/FLIP/FLIP-$n $PROP "$file" $CONCAT &> $NAME/$PROP/FLIP/FLIP-$n\/$CONCAT$GML_NAME.log
            #fi

            # Persimmon
            mkdir -p $NAME/$PROP/PERS/PERS-$n
            ./$SCRIPT PERS $NAME/$PROP/PERS/PERS-$n $PROP "$file" $CONCAT &> $NAME/$PROP/PERS/PERS-$n\/$CONCAT$GML_NAME.log

	    # kaki
	    #mkdir -p $NAME/$PROP/kaki/kaki-$n
	    #./$SCRIPT kaki $NAME/$PROP/kaki/kaki-$n $PROP "$file" $CONCAT &> $NAME/$PROP/kaki/kaki-$n\/$CONCAT$GML_NAME.log

        done | tqdm --total $(ls -l "$DIR" | wc -l)
    done
	n=$(( n + 1))
done

wait
