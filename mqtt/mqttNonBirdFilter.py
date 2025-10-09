#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
#
# Script that listens on the raw bird detection topic and republishes the
#  non-bird messages on another topic
#
################################################################################

from MqttRepublisher import MqttRepublisher

MQTT_HOST = "gpuServer1.lan"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

MQTT_SUB_TOPIC = "birdpi/detections"
MQTT_PUB_TOPIC = "birdpi/nonbirds"


class NonBirdRepublisher(MqttRepublisher):
    def _processMsg(self, inMsg):
        #### FIXME implement this
        outMsg = inMsg
        return outMsg


def main():
    repub = NonBirdRepublisher(MQTT_SUB_TOPIC, MQTT_PUB_TOPIC, MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
    if repub.connect():
        exit(1)
    repub.run()

if __name__ == "__main__":
    main()
