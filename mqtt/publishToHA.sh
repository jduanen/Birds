#!/bin/bash
#
# Script to publish a discovery and a test message to HA

MQTT_HOST="homeassistant.local"
MQTT_TOPIC="birdpi/my_birds"

CMD_PREFIX="mosquitto_pub -h ${MQTT_HOST} -p 1883 -t ${MQTT_TOPIC} -u ${MQTT_USER} -P ${MQTT_PASSWD} -m "

# publish discovery message to HA
echo "TBD"

# publish test message to HA
TIME="2025-11-13T11:19:35.387502-08:00"
CHUNK_START=
CONFIDENCE=0.1
SCIENTIFIC_NAME="XXXXXX"
COMMON_NAME="YYYYYYY"
MQTT_MSG=$(printf '{"timestamp":"%s", "chunk":[0.0, 0.0], "confidence":%f, "scientific":"%s", "common":"%s"}' "${TIME}" "${CONFIDENCE}" "${SCIENTIFIC_NAME}" "${COMMON_NAME}")
${CMD_PREFIX} "${MQTT_MSG}"
