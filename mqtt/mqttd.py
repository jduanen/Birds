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
#import tempfile
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

logger = None
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
        logger.info("Bad parse of message, discarding entry")
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
        logging.basicConfig(level=DEF_LOG_LEVEL)
        logger = logging.getLogger(__name__)
        logger.error("Failed to read config file at: %s", CONF_FILE_PATH)
        sys.exit(1)
    minC = float(config['MQTT']['MinConfidence'])
    if minC < 0 or minC > 1.0:
        logger.error("Invalid MinConfidence value: %f (must be in [0.0,1.0])", minC)
        sys.exit(1)
    conf = {
        'LogLevel': getattr(logging, config['MQTT'].get('LogLevel', fallback=DEF_LOG_LEVEL)),
        'Uid': config['MQTT'].getint('Uid', fallback=DEF_UID),
        'WaitMsec': config['MQTT'].getint('WaitMsec', fallback=DEF_WAIT_MSEC),
        'MqttHost': config['MQTT'].get('MqttHost', fallback=DEF_MQTT_HOST),
        'MqttPort': config['MQTT'].getint('MqttPort', fallback=DEF_MQTT_PORT),
        'MqttKeepalive': config['MQTT'].getint('MqttKeepalive', fallback=DEF_MQTT_KEEPALIVE),
        'DisableRawDetections': config['MQTT'].getboolean('DisableRawDetections', fallback=False),
        'DisableConfidentDetections': config['MQTT'].getboolean('DisableConfidentDetections', fallback=False),
        'DisableMyBirds': config['MQTT'].getboolean('DisableMyBirds', fallback=False),
        'DisableNonBirds': config['MQTT'].getboolean('DisableNonBirds', fallback=False),
        'MinConfidence': config['MQTT'].getfloat('MinConfidence', fallback=DEF_CONFIDENCE),
    }
    conf['BirdsOfInterest'] = config['MQTT'].get('BirdsOfInterest', fallback=[])
    if conf['BirdsOfInterest']:
        conf['BirdsOfInterest'] = [item.strip() for item in conf['BirdsOfInterest'].split(',')]
    conf['BirdsOfNoInterest'] = config['MQTT'].get('BirdsOfNoInterest', fallback=[])
    if conf['BirdsOfNoInterest']:
        conf['BirdsOfNoInterest'] = [item.strip() for item in conf['BirdsOfNoInterest'].split(',')]
    if set(conf['BirdsOfInterest']) & set(conf['BirdsOfNoInterest']):
        logging.basicConfig(level=conf['LogLevel'])
        logger = logging.getLogger(__name__)
        logger.error("Cannot have a name that is both of interest and of no interest")
        sys.exit(1)
    return conf

def main():
    global poller, logger

    conf = getConfig()
#    with tempfile.NamedTemporaryFile(prefix="tmpMqtt_", suffix="*.txt", delete=False) as f:
#        json.dump(conf, sys.stderr, indent=4, sort_keys=False)
    logging.basicConfig(level=conf['LogLevel'])
    logger = logging.getLogger(__name__)
    poller = select.poll()
    journalReader = initJournalReader(conf['Uid'])
    mqttClient = initMqttClient(conf['MqttHost'], conf['MqttPort'], conf['MqttKeepalive'])

    logger.info("Following user '%s' INFO logs starting from the last event",
                conf['Uid'])
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
                        if msg['common'] in conf['BirdsOfNoInterest']:
                            # skip detections of no interest
                            logger.warning("Detected name '%s' not of interest", msg['common']) ####FIXME
                            continue
                        if not conf['DisableRawDetections']:
                            # all detections, not of no interest, with no other filtering
                            topic = "birdpi/raw_detections"
                            publishDetection(mqttClient, topic, msg)
                        if (not conf['DisableConfidentDetections'] and 
                            (msg['confidence'] >= conf['MinConfidence'])):
                            # all detections not of no interest and of sufficient confidence level
                            topic = "birdpi/confident_detections"
                            publishDetection(mqttClient, topic, msg)
                        if (not conf['DisableMyBirds'] and
                            (msg['confidence'] >= conf['MinConfidence']) and
                            (msg['common'] in conf['BirdsOfInterest'])):
                            # detections of interest, not of no interest, and of sufficient confidence level
                            topic = "birdpi/my_birds"
                            publishDetection(mqttClient, topic, msg)
                        if (not conf['DisableNonBirds'] and
                            (msg['common'] in NON_BIRD_COMMON_NAMES)):
                            # detections not of no interest that are not bird sounds
                            topic = "birdpi/non_birds"
                            publishDetection(mqttClient, topic, msg)
            elif state == journal.INVALIDATE:
                logger.info("journal files changed, so reopen and seek to start of new file")
                journalReader.seek_head()
            elif state == journal.NOP:
                pass
        else:
            logger.info("Timed out waiting on journal event, continuing...")
            time.sleep(0.1)
    logger.info("Exiting")

if __name__ == "__main__":
    main()
