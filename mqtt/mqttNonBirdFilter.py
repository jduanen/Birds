#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
#
# Script that listens on the raw bird detection topic and republishes the
#  non-bird messages on another topic
#
################################################################################

import json
import sys

from MqttRepublisher import MqttRepublisher


MQTT_HOST = "gpuServer1.lan"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 15000

MQTT_SUB_TOPIC = "birdpi/detections"
MQTT_PUB_TOPIC = "birdpi/nonbirds"

NON_BIRD_LABELS = [
    "Dog_Dog",
    "Engine_Engine",
    "Environmental_Environmental",
    "Fireworks_Fireworks",
    "Gun_Gun",
    "Human_Human",
    "Noise_Noise",
    "Siren_Siren"
]

NON_BIRD_NAMES = [names.split('_') for names in NON_BIRD_LABELS]
NON_BIRD_SCIENTIFIC_NAMES, NON_BIRD_COMMON_NAMES = zip(*NON_BIRD_NAMES)


class NonBirdRepublisher(MqttRepublisher):
    def _processPayload(self, inPayload):
        """ Return the message payload to be republished if its names are in
             the lists of non-bird names.
            Return None if no message is to be published in response to the
             received message.
        """
        outPayload = None
        if (inPayload['scientific'] in NON_BIRD_SCIENTIFIC_NAMES and
            inPayload['common'] in NON_BIRD_COMMON_NAMES):
            if (not self.minConfidence or
                (self.minConfidence <= inPayload['confidence'])):
                outPayload = json.dumps(inPayload)
        return outPayload


def main():
    repub = NonBirdRepublisher(MQTT_SUB_TOPIC, MQTT_PUB_TOPIC, MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
    repub.setMinConfidence(0.0)
    print(f"Min Confidence: {repub.getMinConfidence()}")
    if repub.connect():
        sys.exit(1)
    repub.run()
    repub.disconnect()

if __name__ == "__main__":
    main()
