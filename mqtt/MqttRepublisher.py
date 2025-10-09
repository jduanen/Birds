#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
#
# Script that listens on the raw bird detection topic and republishes the
#  non-bird messages on another topic
#
################################################################################

import json
import logging
import paho.mqtt.client as mqtt
import select


LOG_LEVEL = "DEBUG"  ## "WARNING"

DEF_MQTT_PORT = 1883
DEF_MQTT_KEEP_ALIVE = 60  # 60secs


logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


class MqttRepublisher:
    def __init__(self, subTopic, pubTopic, host, port=DEF_MQTT_PORT, keepAlive=DEF_MQTT_KEEP_ALIVE):
        self.subTopic = subTopic
        self.pubTopic = pubTopic
        self.host = host
        self.port = port
        self.keepAlive = keepAlive

        self.poller = select.poll()
        self.client = mqtt.Client()
        self.client.on_message = self.onMsg

        self.connected = False

    def connect(self):
        if self.client.connect(self.host, self.port) != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Failed to connect to %s on port %d", self.host, self.port)
            return True
        if self.client.subscribe(self.subTopic) != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Failed to subscribe to topic: %s", self.subTopic)
            return True
        if self.client.loop_forever() != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Failed to loop forever")
            return True
        self.connected = True
        return False

    def disconnect(self):
        if not self.connected:
            logger.warning("Not connected, ignoring")
            return False
        if self.client.disconnect() != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Failed to disconnect")
            return True
        return False

    def onMsg(self, client, userdata, msg):
        """ Callback when a message is received on the subscribed topic
        """
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            if not payload:
                logger.error("Failed to decode message payload as JSON")
                return

            #### TODO call message processing method here

            if self.client.publish(self.pubTopic, msg.payload) == mqtt.MQTT_ERR_SUCCESS:
                logger.debug("Republished message: %s", payload)
            else:
                logger.error("Failed to republish message: %s", payload)
        except Exception as e:
            print(f"Error processing message: {e}")
