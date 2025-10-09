#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
#
# Script that listens on the raw bird detection topic and republishes the
#  messages that match given names on another topic
#
################################################################################

import json
import sys

from MqttRepublisher import MqttRepublisher


MQTT_HOST = "gpuServer1.lan"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 15000

MQTT_SUB_TOPIC = "birdpi/detections"
MQTT_PUB_TOPIC = "birdpi/mybirds"

MY_NAME_PARTS = [
    "Owl",
    "Hawk",
    "Eagle",
    "Pheasant",
    "Quail",
    "Oriole",
    "Rufous Hummingbird",
    "Costa's Hummingbird",
    "Allen's Hummingbird",
    "Tanager"
]


class myBirdsRepublisher(MqttRepublisher):
    def _processPayload(self, inPayload):
        """ Return the message payload to be republished if its common name
             (partially) matches any in the list of desired bird list.
            Return None if no message is to be published in response to the
             received message.
        """
        outPayload = None
        if any(namePart in inPayload['common'] for namePart in MY_NAME_PARTS):
            if (not self.minConfidence or
                (self.minConfidence <= inPayload['confidence'])):
                outPayload = json.dumps(inPayload)
        return outPayload


def main():
    print(f"My Birds: {MY_NAME_PARTS}")
    repub = myBirdsRepublisher(MQTT_SUB_TOPIC, MQTT_PUB_TOPIC, MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
    repub.setMinConfidence(0.0)
    print(f"Min Confidence: {repub.getMinConfidence()}")
    if repub.connect():
        sys.exit(1)
    repub.run()
    repub.disconnect()

if __name__ == "__main__":
    main()
