#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
#
# Script that loops forever reading the journal log, and publishes the requested
#  birdpi detection events -- i.e., the highest confidence detection in each
#  (potentially overlapping) time chunk within each recording interval.
#
# The format of the birdpi logs is as follows:
#  [server][INFO] <startOffset>;<endOffset>-('<scientificName>_<commonName>', <confidence>)
#
################################################################################

#### TODO get labels whose scientific and common names are the same
####      grep -oP '([A-Z][^\s]*)_\1' Nachtzuster/model/labels_*/* | cut -d ":" -f 2 | sort | uniq

import configparser
import logging
import select
import sys
import time

import json
import paho.mqtt.client as mqtt
from parse import parse
from systemd import journal


DEF_LOG_LEVEL = "WARNING"
CONF_FILE_PATH = "etc/systemd/mqttd.conf"   #### FIXME add leading '/'

DEF_CONFIDENCE = 0.8

DEF_UID = 1000          # uid of 'jdn'
DEF_WAIT_MSEC = 15000   # currently: 15sec batches, six 3sec chunks, with .5sec overlap

DEF_MQTT_HOST = "gpuServer1.lan"
DEF_MQTT_PORT = 1883
DEF_MQTT_KEEPALIVE = 60


LOG_LEVEL = DEF_LOG_LEVEL  #### TMP TMP TMP
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)
poller = None


def initJournalReader(uid):
    j = journal.Reader()
    j.log_level(journal.LOG_INFO)
    j.add_match(_UID=str(uid))

    # start at the current end of the current journal file
    j.seek_tail()
    j.get_previous()

    poller.register(j, j.get_events())
    logger.debug("Initialized Journal reader")
    return j

def initMqttClient(host, port, keepalive):
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
    names = parts[2].split("_")
    if len(names) != 2:
        logger.error("Bad names: %s, discarding entry", parts[2])
        return None
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

def getConfig():
    config = configparser.ConfigParser()
    if not config.read(CONF_FILE_PATH):
        logger.error("Failed to read config file at: %s", CONF_FILE_PATH)
        sys.exit(1)
    conf = {
        'LogLevel': getattr(logging, config['MQTT'].get('LogLevel', fallback=DEF_LOG_LEVEL)),
        'Uid': config['MQTT'].getint('Uid', fallback=DEF_UID),
        'WaitMsec': config['MQTT'].getint('WaitMsec', fallback=DEF_WAIT_MSEC),
        'MqttHost': config['MQTT'].get('MqttHost', fallback=DEF_MQTT_HOST),
        'MqttPort': config['MQTT'].getint('MqttPort', fallback=DEF_MQTT_PORT),
        'MqttKeepalive': config['MQTT'].getint('MqttKeepalive', fallback=DEF_MQTT_KEEPALIVE),
        'DisableRawDetections': config['MQTT'].getboolean('DisableRawDetections', fallback=True),
        'DisableConfidentDetections': config['MQTT'].getboolean('DisableConfidentDetections', fallback=False),
        'DisableMyBirds': config['MQTT'].getboolean('DisableMyBirds', fallback=False),
        'DisableNonBirds': config['MQTT'].getboolean('DisableNonBirds', fallback=False),
        'MinConfidence': config['MQTT'].getint('MinConfidence', fallback=DEF_CONFIDENCE),
    }
    conf['BirdsOfInterest'] = config['MQTT'].get('BirdsOfInterest', fallback=[])
    if conf['BirdsOfInterest']:
        conf['BirdsOfInterest'] = [item.strip() for item in conf['BirdsOfInterest'].split(',')]
    conf['BirdsOfNoInterest'] = config['MQTT'].get('BirdsOfNoInterest', fallback=[])
    if conf['BirdsOfNoInterest']:
        conf['BirdsOfNoInterest'] = [item.strip() for item in conf['BirdsOfNoInterest'].split(',')]
    return conf

def main():
    global poller

    conf = getConfig()
    if False:
        json.dump(conf, sys.stdout, indent=4, sort_keys=False)
    poller = select.poll()
    journalReader = initJournalReader(conf['Uid'])
    mqttClient = initMqttClient(conf['MqttHost'], conf['MqttPort'], conf['MqttKeepalive'])
    topic = "birdpi/detections"
    print(f"BirdPi MQTT Publishing on topic: {topic}")

    logger.info("Following INFO logs for user %s starting from most recent logged event", conf['Uid'])
    while True:
        events = poller.poll(conf['WaitMsec'])
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
