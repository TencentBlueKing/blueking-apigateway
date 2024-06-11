#!/bin/bash

# create data file
if [ ! -f data_1K.dat ]
then
    dd if=/dev/zero of=data_1K.dat  bs=1024  count=1
fi

if [ ! -f data_41M.dat ]
then
    dd if=/dev/zero of=data_41M.dat  bs=42991616  count=1
fi

# run cases
bru run . -r --env local
if [ $? -ne 0 ]
then
    echo "run cases fail, please check"
    exit 1
else
    echo "run cases success"
    exit 0
fi
