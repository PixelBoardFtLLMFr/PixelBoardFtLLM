#!/bin/sh

count=0
printf "\r%d requests sent" $count

while true
do
    curl --silent --insecure --output /dev/null "https://localhost:5555/" --data '{"input":"dance","key":""}'
    count=$(($count+1))
    printf "\r%d requests sent" $count
done
echo
