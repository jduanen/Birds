#include <Arduino.h>

#include "RTSPServer.h"
#include "AudioStreamer.h"

#include "XiaoAudioSource.h"

#include "wifi.h"


const char *ssid = WLAN_SSID;
const char *password = WLAN_PASS;

int port = 554;
XiaoAudioSource audioSource = XiaoAudioSource();
AudioStreamer streamer = AudioStreamer(&audioSource);
//RTSPServer rtsp(&streamer, port);
RTSPServer rtsp(&streamer);


void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }
  Serial.setDebugOutput(true);
  delay(2000);
  Serial.println("BEGIN");

  rtsp.begin(ssid, password);
  Serial.println(WiFi.localIP());

  if (audioSource.init()) {
    Serial.println("ERROR: unable to init audio source");
    //// FIXME
    while (true) {;};
  }
  Serial.println("START");
}

void loop() {
  delay(1000);
  //// TODO check if client disconnected and reset things
}
