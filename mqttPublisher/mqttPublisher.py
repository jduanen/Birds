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

#### TODO make this a service -- activate venv first, always run
#### grep -oP '([A-Z][^\s]*)_\1' Nachtzuster/model/labels_*/* | cut -d ":" -f 2 | sort | uniq

import logging
import select
import time

import json
import paho.mqtt.client as mqtt
from parse import parse
from systemd import journal


LOG_LEVEL = "WARNING"

UID = 1000          # uid of 'jdn'
WAIT_MSEC = 15000   # currently: 15sec batches, six 3sec chunks, with .5sec overlap

MQTT_HOST = "gpuServer1.lan"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60


logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)
poller = select.poll()

def initJournalReader(uid=UID):
    j = journal.Reader()
    j.log_level(journal.LOG_INFO)
    j.add_match(_UID=str(uid))

    # start at the current end of the current journal file
    j.seek_tail()
    j.get_previous()

    poller.register(j, j.get_events())
    logger.debug("Initialized Journal reader")
    return j

def initMqttClient(host=MQTT_HOST, port=MQTT_PORT, keepalive=MQTT_KEEPALIVE):
    client = mqtt.Client()
    if client.connect(host, port, keepalive) != mqtt.MQTT_ERR_SUCCESS:
        logger.error("Failed to connect to %s on port %d", host, port)
        raise Exception
    return client

def publishDetection(client, topic, msg):
    jsonPayload = json.dumps(msg)
    logging.debug("On topic %s, Publish %s", topic, jsonPayload)
    client.publish(topic, jsonPayload)

def processJournalEntry(entry):
    if 'MESSAGE' not in entry:
        logger.debug("No MESSAGE field in the journal entry")
        return None
    msgTime = entry['__REALTIME_TIMESTAMP']
    message = entry['MESSAGE']
    logger.debug("%s - message: %s", msgTime, message)
    res = parse("[server][INFO] {};{}-({}, {})", message)
    if not res:
        logger.debug("Unable to parse message, discarding entry")
        return None
    parts = list(res)
    logger.debug("parts: %s", parts)
    if len(parts) != 4:
        logger.debug("Bad parse of message, discarding entry")
        return None
#### TODO check for special cases and generate different messages -- e.g., Engine_Engine
    names = parts[2].split("_")
    if len(names) != 2:
        logger.error("Bad names: %s, discarding entry", parts[2])
        return None
#### TODO define a minimum confidence level, below which the message is discarded -- e.g., 0.5
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
    return msgBody

def main():
    journalReader = initJournalReader()
    mqttClient = initMqttClient()
    topic = "birdpi/detections"

    logger.info("Following INFO logs for user %s starting from most recent logged event", UID)
    while True:
        events = poller.poll(WAIT_MSEC)
        if events:
            state = journalReader.process()
            if state == journal.APPEND:
                # new entries added, so read them
                while True:
                    entry = journalReader.get_next()
                    if not entry:
                        break
                    msg = processJournalEntry(entry)
                    if msg:
                        publishDetection(mqttClient, topic, msg)
            elif state == journal.INVALIDATE:
                logger.debug("journal files changed, so reopen and seek to start of new file")
                journalReader.seek_head()
            elif state == journal.NOP:
                pass
        else:
            logger.debug("Timed out waiting on journal event, continuing...")
            time.sleep(0.1)
    logger.debug("Exiting")

if __name__ == "__main__":
    main()
