#include <Arduino.h>

#include "RTSPServer.h"
#include "AudioStreamer.h"

#include "AudioTestSource.h"

#include "wifi.h"

const char *ssid = WLAN_SSID;
const char *password = WLAN_PASS;

int port = 554;
AudioTestSource testSource = AudioTestSource();
AudioStreamer streamer = AudioStreamer(&testSource);
RTSPServer rtsp(&streamer); // , port);

void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }
  Serial.println("BEGIN");

  rtsp.begin(ssid, password);
  Serial.println(WiFi.localIP());
  Serial.println("START");
}

void loop()
{
  delay(1000);
}
