#include <Arduino.h>

#include "RTSPServer.h"
#include "AudioStreamer.h"
#include "AudioTestSource.h"

#include "wifi.h"

const char* ssid = WLAN_SSID;
const char* password = WLAN_PASS;


int port = 554;
AudioTestSource testSource = AudioTestSource();
AudioStreamer streamer = AudioStreamer(&testSource);
RTSPServer rtsp(&streamer); // , port);

void setup() {
    Serial.begin(114200);

    rtsp.begin(ssid, password);    
}

void loop() {
    delay(1000);
}