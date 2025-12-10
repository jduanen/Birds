#!/bin/bash
#
# Script to get the latest files for birdpi mqttd

USER="jdn"
SOURCE_MACHINE="gpuServer1.lan"
SOURCE_PATH="/home/jdn/Code/Birds/mqtt/"
TARGET_PATH="/home/jdn/Code/mqtt/"

rsync -avz ${USER}@${SOURCE_MACHINE}:${SOURCE_PATH} ${TARGET_PATH}
