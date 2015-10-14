#!/bin/bash

# This script takes the large logo, and shrinks it so the max width is $MAX_WIDTH

MAX_WIDTH=400

for IMG in `ls SRC*.png`
do
    SMALL=`echo $IMG  |sed 's/^SRC-//'`
    /usr/bin/convert -thumbnail "${MAX_WIDTH}x${MAX_WIDTH}>" $IMG $SMALL
done
