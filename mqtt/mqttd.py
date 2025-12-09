#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
#
# Script that loops forever reading the journal log, and publishes the requested
#  birdpi detection events -- i.e., the highest confidence detection in each
#  (potentially overlapping) time chunk within each recording interval.
#
# The format of the birdpi logs is as follows:
#  [utils.analysis][INFO] <startOffset>;<endOffset>-('<scientificName>_<commonName>', <confidence>)
#
################################################################################

#### TODO get labels whose scientific and common names are the same
####      grep -oP '([A-Z][^\s]*)_\1' Nachtzuster/model/labels_*/* | cut -d ":" -f 2 | sort | uniq

import configparser
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import select
import sys
import time

import json
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
from parse import parse
from systemd import journal
import threading


ENABLE_DEBUGGING = False

DEF_LOG_LEVEL = "WARN"
CONF_FILE_PATH = "/etc/systemd/mqttd.conf"

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

LOG_FILE = "/var/log/mqttd.log"

CPU_TEMP_INTERVAL = 15 * 60.0  # log every 15mins

lastCpuTempTime = 0.0

logger = None


def initJournalReader(uid):
    j = journal.Reader()
    j.log_level(journal.LOG_INFO)
    j.add_match(_UID=str(uid))

    # start at the current end of the current journal file
    j.seek_tail()
    j.get_previous()

    logger.debug("Initialized Journal reader")
    return j

def publishHaDiscovery(client):
    topic = "homeassistant/sensor/birdpi_cpu/config"
    msg = {
        "name": "BirdPi CPU Temperature",
        "state_topic": "birdpi/cpu_temperature",
        "unit_of_measurement": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "unique_id": "birdpi_cpu_temperature",
        "value_template": "{{ value_json.temperature}}",
        "device": {
            "identifiers": ["birdpi"],
            "name": "BirdPi CPU Temperature",
            "manufacturer": "Custom",
            "model": "BirdPi"
        }
    }
    publishJson(client, topic, msg)
    print(f"DISCOVERY: topic: {topic}, msg: {msg}")

def onConnect(client, userdata, flags, rc, properties=None):
    if rc != 0:
        logger.error("Connection failed with result code: %d", rc)
        return True
    logger.info("Connected to MQTT broker successfully")
    # 100ms delay for connection to settle and then publish discovery message(s)
    threading.Timer(0.1, publishHaDiscovery(client))
    return False

def initMqttClient(host, port, keepalive, username=None, password=None):
    client = mqtt.Client(client_id="birdPiClient", callback_api_version=CallbackAPIVersion.VERSION2)
    if username and password:
        client.username_pw_set(username, password)
    client.on_connect = onConnect
    if client.connect(host, port, keepalive) != mqtt.MQTT_ERR_SUCCESS:
        logger.error("Failed to connect to %s on port %d", host, port)
        return None
    if client.loop_start() != mqtt.MQTT_ERR_SUCCESS:
        logger.error("Failed to start the polling loop")
        return None
    logger.debug("MQTT Client Initialized")
    return client

def publishJson(client, topic, msg):
    jsonPayload = json.dumps(msg)
    logging.debug("On topic %s, Publish %s", topic, jsonPayload)
    result = client.publish(topic, jsonPayload)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        logger.info("Message sent to topic: %s", topic)
    else:
        logger.warning("Failed to send message to topic: %s; error code: %d", topic, result.rc)

def processJournalEntry(entry):
    if 'MESSAGE' not in entry:
        logger.debug("No MESSAGE field in the journal entry")
        return None
    msgTime = entry['__REALTIME_TIMESTAMP']
    message = entry['MESSAGE']
    logger.debug("%s - message: %s", msgTime, message)
    res = parse("[utils.analysis][INFO] {};{}-({}, {})", message)
    if not res:
        logger.debug("Unable to parse message, discarding entry")
        return None
    parts = list(res)
    logger.debug("parts: %s", parts)
    if len(parts) != 4:
        logger.info("Bad parse of message, discarding entry")
        return None
    names = parts[2].split("_")
    if len(names) != 2 and len(names) != 4:
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
    consoleLogger = logging.getLogger(__name__)
    consoleLogger.setLevel(logging.WARNING)

    config = configparser.ConfigParser()
    if not config.read(CONF_FILE_PATH):
        consoleLogger.error("Failed to read config file at: %s", CONF_FILE_PATH)
        sys.exit(1)
    minC = float(config['MQTT']['MinConfidence'])
    if minC < 0 or minC > 1.0:
        consoleLogger.error("Invalid MinConfidence value: %f (must be in [0.0,1.0])", minC)
        sys.exit(1)
    conf = {
        'LogLevel': getattr(logging, config['MQTT'].get('LogLevel', fallback=DEF_LOG_LEVEL)),
        'Uid': config['MQTT'].getint('Uid', fallback=DEF_UID),
        'WaitMsec': config['MQTT'].getint('WaitMsec', fallback=DEF_WAIT_MSEC),
        'MqttHost': config['MQTT'].get('MqttHost', fallback=DEF_MQTT_HOST),
        'MqttPort': config['MQTT'].getint('MqttPort', fallback=DEF_MQTT_PORT),
        'MqttKeepalive': config['MQTT'].getint('MqttKeepalive', fallback=DEF_MQTT_KEEPALIVE),
        'MqttUsername': config['MQTT'].get('MqttUsername', fallback=None),
        'MqttPasswd': config['MQTT'].get('MqttPasswd', fallback=None),
        'DisableRawDetections': config['MQTT'].getboolean('DisableRawDetections', fallback=False),
        'DisableConfidentDetections': config['MQTT'].getboolean('DisableConfidentDetections', fallback=False),
        'DisableMyBirds': config['MQTT'].getboolean('DisableMyBirds', fallback=False),
        'DisableNonBirds': config['MQTT'].getboolean('DisableNonBirds', fallback=False),
        'MinConfidence': config['MQTT'].getfloat('MinConfidence', fallback=DEF_CONFIDENCE),
        'CpuTemperature': config['MQTT'].getboolean('CpuTemperature', fallback=False),
    }

    conf['BirdsOfInterest'] = config['MQTT'].get('BirdsOfInterest', fallback=[])
    if conf['BirdsOfInterest']:
        conf['BirdsOfInterest'] = [item.strip() for item in conf['BirdsOfInterest'].split(',')]
    conf['BirdsOfNoInterest'] = config['MQTT'].get('BirdsOfNoInterest', fallback=[])
    if conf['BirdsOfNoInterest']:
        conf['BirdsOfNoInterest'] = [item.strip() for item in conf['BirdsOfNoInterest'].split(',')]
    if set(conf['BirdsOfInterest']) & set(conf['BirdsOfNoInterest']):
        consoleLogger.error("Cannot have a name that is both of interest and of no interest")
        sys.exit(1)
    return conf

def main():
    global logger, lastCpuTempTime

    conf = getConfig()

    rootLogger = logging.getLogger(__file__)
    rootLogger.setLevel(logging.WARNING)
    logger = logging.getLogger(f"{__file__}.{__name__}")
    logger.setLevel(conf['LogLevel'])
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    if ENABLE_DEBUGGING:
        handler = logging.StreamHandler()  # logging to console for debugging
    else:
        handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=2)  # logging to file
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False  # prevent root interference

    journalReader = initJournalReader(conf['Uid'])
    poller = select.poll()
    poller.register(journalReader, journalReader.get_events())
    mqttClient = initMqttClient(conf['MqttHost'], conf['MqttPort'],
                                conf['MqttKeepalive'], conf['MqttUsername'],
                                conf['MqttPasswd'])
    if not mqttClient:
        sys.exit(1)

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
                            logger.info("Detected name '%s' not of interest", msg['common'])
                            continue
                        if not conf['DisableRawDetections']:
                            # all detections, not of no interest, with no other filtering
                            topic = "birdpi/raw_detections"
                            publishJson(mqttClient, topic, msg)
                        if (not conf['DisableConfidentDetections'] and
                            (msg['confidence'] >= conf['MinConfidence'])):
                            # all detections not of no interest and of sufficient confidence level
                            topic = "birdpi/confident_detections"
                            publishJson(mqttClient, topic, msg)
                        if (not conf['DisableMyBirds'] and
                            (msg['confidence'] >= conf['MinConfidence']) and
                            (msg['common'] in conf['BirdsOfInterest'])):
                            # detections of interest, not of no interest, and of sufficient confidence level
                            topic = "birdpi/my_birds"
                            publishJson(mqttClient, topic, msg)
                        if (not conf['DisableNonBirds'] and
                            (msg['common'] in NON_BIRD_COMMON_NAMES)):
                            # detections not of no interest that are not bird sounds
                            topic = "birdpi/non_birds"
                            publishJson(mqttClient, topic, msg)
            elif state == journal.INVALIDATE:
                logger.info("journal file changed, so close it and open the new file")
                journalReader.close()
                journalReader = initJournalReader(conf['Uid'])
                poller = select.poll()
                poller.register(journalReader, journalReader.get_events())
            elif state == journal.NOP:
                pass
        else:
            logger.info("Timed out waiting on journal event, continuing...")
            time.sleep(0.1)
        if conf['CpuTemperature']:
            now = time.time()
            if now - lastCpuTempTime >= CPU_TEMP_INTERVAL:
                try:
                    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                        temp = int(f.read().strip()) / 1000.0
                    msg = {
                        'timestamp': datetime.fromtimestamp(now).isoformat(),
                        'temperature': temp
                    }
                    topic = "birdpi/cpu_temperature"
                    publishJson(mqttClient, topic, msg)
                    print(f"STATE: topic: {topic}, msg: {msg}")
                    lastCpuTempTime = now
                except FileNotFoundError:
                    logger.info("Failed to read CPU temperature")
    logger.info("Exiting")

if __name__ == "__main__":
    main()
