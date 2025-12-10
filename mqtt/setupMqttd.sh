#!/bin/bash
#
# Script to setup birdpi for mqttd
# 

LOG_PATH="/var/log/mqtt"

if [ ! -d "$LOG_PATH" ]; then
    sudo mkdir -p "$LOG_PATH"
    sudo chown jdn:jdn "$LOG_PATH"
    sudo chmod 750 "$LOG_PATH"
fi
