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
MQTTD_CONF_PATH="${MQTTD_PATH}/etc/systemd"
if [ -e "${MQTTD_CONF_PATH}/mqttd.conf" ]; then
    sudo rm /etc/systemd/mqttd.conf
fi
sudo ln -s ${MQTTD_CONF_PATH}/mqttd.conf /etc/systemd/
if [ ! -e "${MQTTD_CONF_PATH}/mqttd.conf" ]; then
    echo "ERROR: Failed to make link to mqttd conf file"
    exit 1
fi

MQTTD_SERVICE_PATH="${MQTTD_PATH}/etc/systemd/system"
if [ -e "${MQTTD_SERVICE_PATH}/mqttd.conf" ]; then
    sudo rm /etc/systemd/system/mqttd.service
fi
sudo ln -s ${MQTTD_SERVICE_PATH}/mqttd.service /etc/systemd/system/
if [ ! -e "${MQTTD_SERVICE_PATH}/mqttd.conf" ]; then
    echo "ERROR: Failed to make link to mqttd service file"
    exit 1
fi

sudo systemctl stop mqttd.service
sudo systemctl daemon-reload

sudo systemctl enable mqttd.service
sudo systemctl start mqttd.service

sudo systemctl status mqttd.service
