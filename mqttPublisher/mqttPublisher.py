#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
#
# Script that loops forever reading the journal log, and publishes all of the
#  logged detection events -- i.e., the highest confidence detection in each
#  (potentially overlapping) time chunk within each recording interval.
#
# The format of the birdpi logs is as follows:
#  [server][INFO] <startOffset>;<endOffset>-('<scientificName>_<commonName>', <confidence>)
#
################################################################################

import logging
import time

import json
import paho.mqtt.client as mqtt
from parse import parse
from systemd import journal


LOG_LEVEL = "DEBUG"  ##"WARNING"

UID = 1000          # uid of 'jdn'
WAIT_MSEC = 15000   # currently: 15sec batches, six 3sec chunks, with .5sec overlap

MQTT_HOST = "gpuServer1.lan"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60


logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


def initJournalReader(uid=UID):
    j = journal.Reader()
    j.log_level(journal.LOG_INFO)
    j.add_match(_UID=str(uid))
    j.seek_tail()
    j.get_previous()
    logger.debug("Initialized Journal reader")
    return j

def initMqttClient(host=MQTT_HOST, port=MQTT_PORT, keepalive=MQTT_KEEPALIVE):
    client = mqtt.Client()
    if client.connect(host, port, keepalive) != mqtt.MQTTErrorCode.MQTT_ERR_SUCCESS:
        logger.error("Failed to connect to %s on port %d", host, port)
        raise Exception
    return client

def publishDetection(client, topic, msg):
    jsonPayload = json.dumps(msg)
    logging.debug("On topic %s, Publish %s", topic, jsonPayload)
    client.publish(topic, jsonPayload)

def getDetectionMsg(journalReader):
    msgBody = None
    while not msgBody:
        if not journalReader.wait(WAIT_MSEC):
            logger.debug("Timed out waiting on journal entry, continuing...")
            time.sleep(0.1)
            continue
        entry = journalReader.get_next()
        if not entry or 'MESSAGE' not in entry:
            logger.debug("No journal entry or no MESSAGE in the entry, trying again")
            continue
        msgTime = entry['__REALTIME_TIMESTAMP']
        message = entry['MESSAGE']
        logger.debug("%s: <<<%s>>>", msgTime, message)
        res = parse("[server][INFO] {};{}-({}, {})", message)
        if not res:
            logger.debug("Unable to parse message, discarding entry")
            continue
        parts = list(res)
        logger.debug("parts: %s", parts)
        if len(parts) != 4:
            logger.debug("Bad parse of message, discarding entry")
            continue
        names = parts[2].split("_")
        if len(names) != 2:
            logger.error("Bad names: %s, discarding entry", parts[2])
            continue
        intervalStart = float(parts[0])
        intervalEnd = float(parts[1])
        confidence = float(parts[3])
        scientificName = names[0].lstrip('\'"')
        commonName = names[1].rstrip('\'"')
        msgBody = {
            'timestamp': msgTime.isoformat(),
            'chunk': (intervalStart, intervalEnd),
            'confidence': confidence,
            'scientific': scientificName,
            'common': commonName
        }
        break
    return msgBody

def main():
    journalReader = initJournalReader()
    mqttClient = initMqttClient()
    topic = "birdpi/detections"

    logger.info("Following INFO logs for user %s starting from most recent logged event", UID)
    while True:
        detectionMsg = getDetectionMsg(journalReader)
        if not detectionMsg:
            break
        publishDetection(mqttClient, topic, detectionMsg)
    logger.debug("Exiting")

if __name__ == "__main__":
    main()
