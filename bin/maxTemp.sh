#!/bin/bash

hiTemp=0

echo "Monitoring temperature. Type Ctrl+C to stop."
while true; do
  curTempStr=$(vcgencmd measure_temp)
  curTemp=$(echo "$curTempStr" | sed "s/temp=\(.*\)'C/\1/")
  if (( $(echo "$curTemp > $hiTemp" | bc -l) )); then
    hiTemp=$curTemp
    echo ${hiTemp}C - $(date)
  fi
  sleep 10
done
