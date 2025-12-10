#!/bin/bash
#
# Script to setup birdpi for mqttd


sudo groupadd mqtt
sudo adduser --system --no-create-home --group mqtt

sudo mkdir /var/log/mqtt
sudo chown mqtt:mqtt /var/log/mqtt
sudo chmod 750 /var/log/mqtt
