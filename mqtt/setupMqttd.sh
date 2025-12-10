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

MQTTD_PATH="${HOME}/Code/Birds/mqtt"
sudo ln -s ${MQTTD_PATH}/etc/systemd/mqttd.conf /etc/systemd/
sudo ln -s ${MQTTD_PATH}/etc/systemd/system/mqttd.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable mqttd.service
sudo systemctl start mqttd.service
sudo systemctl status mqttd.service