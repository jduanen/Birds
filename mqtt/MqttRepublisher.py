#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
#
# Script that listens on the raw bird detection topic and republishes the
#  non-bird messages on another topic
#
################################################################################

#### TODO add method(s) to allow run to be done in the background

from abc import ABC, abstractmethod
import json
import logging
import paho.mqtt.client as mqtt
import select


LOG_LEVEL = "WARNING"

DEF_MQTT_PORT = 1883
DEF_MQTT_KEEP_ALIVE = 60  # 60secs


logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


class MqttRepublisher(ABC):
    def __init__(self, subTopic, pubTopic, host, port=DEF_MQTT_PORT, keepAlive=DEF_MQTT_KEEP_ALIVE):
        self.subTopic = subTopic
        self.pubTopic = pubTopic
        self.host = host
        self.port = port
        self.keepAlive = keepAlive

        self.poller = select.poll()
        self.client = mqtt.Client()
        self.client.on_message = self.onMsg

        self.minConfidence = None
        self.connected = False

    def setMinConfidence(self, confidence):
        if confidence > 1.0:
            logger.warning("Confidence must be in the range [0.0-1.0]")
            self.minConfidence = 1.0
        elif confidence < 0:
            self.minConfidence = None
        else:
            self.minConfidence = confidence

    def getMinConfidence(self):
        return self.minConfidence

    def connect(self):
        if self.client.connect(self.host, self.port) != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Failed to connect to %s on port %d", self.host, self.port)
            return True
        if self.client.subscribe(self.subTopic)[0] != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Failed to subscribe to topic: %s", self.subTopic)
            return True
        self.connected = True
        return False

    def run(self):
        """ Only returns if disconnect() is called by a callback
        """
        if not self.connected:
            logger.error("Not connected")
            return True
        if self.client.loop_forever() != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Failed to loop forever")
            return True
        return False

    def disconnect(self):
        if not self.connected:
            logger.warning("Not connected, ignoring")
            return False
        if self.client.disconnect() != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Failed to disconnect")
            return True
        return False

    @abstractmethod
    def _processPayload(self, inPayload):
        """ This method must be overridden in subclasses
            Takes incoming message, and returns outgoing message (both as JSON)
        """

    def onMsg(self, client, userdata, msg):
        """ Callback when a message is received on the subscribed topic
        """
        try:
            inPayload = json.loads(msg.payload.decode('utf-8'))
            if not inPayload:
                logger.error("Failed to decode message payload as JSON")
                return

            outPayload = self._processPayload(inPayload)
            if outPayload:
                if self.client.publish(self.pubTopic, outPayload)[0] == mqtt.MQTT_ERR_SUCCESS:
#                r = self.client.publish(self.pubTopic, outPayload)
#                print(r)
#                if r == mqtt.MQTT_ERR_SUCCESS:
                    logger.info("Republished message: %s", outPayload)
                else:
                    logger.error("Failed to republish message: %s", outPayload)
            else:
                logger.debug("No message to republish for message: %s", inPayload)
        except Exception as e:
            print(f"Error processing message: {e}")
