#include <WiFi.h>
#include <HTTPClient.h>
#include "wifi.h"


#define PAYLOAD_BUFFER_LEN    512


const char* ssid = WLAN_SSID;
const char* password = WLAN_PASS;

const char *host = "worldclockapi.com";
const int port = 80;
const char *uri = "/api/json/utc/now";
char payloadBuffer[PAYLOAD_BUFFER_LEN];


int httpGet(const char *host, int port, const char *uri, char *bufPtr, int bufLen);


void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  };
  delay(1000);
  Serial.println("BEGIN");

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  };
  Serial.println("WiFi connected");
}

void loop() {
  int payloadLen = httpGet(host, port, uri, payloadBuffer, PAYLOAD_BUFFER_LEN);
  Serial.println(payloadLen);
  if (payloadLen >= PAYLOAD_BUFFER_LEN) {
    Serial.print("ERROR: buffer overflow (");
    Serial.print(payloadLen); Serial.print(" >= "); Serial.print(PAYLOAD_BUFFER_LEN);
    Serial.println(")");
  }
  Serial.println(payloadBuffer);
  delay(1000);
}

int httpGet(const char *host, int port, const char *uri, char *bufPtr, int bufLen) {
  int payloadLen = 0;
  String payload;
  HTTPClient http;

  http.begin(host, port);
  http.setURL(uri);
  Serial.print("URI: "); Serial.println(uri);

  int httpCode = http.GET();
  switch (httpCode) {
  case 200:
    payload = http.getString();
    payload.toCharArray(bufPtr, bufLen);
    payloadLen = payload.length();
    break;
  default:
    Serial.println("WARNING: Unhandled HTTP response code" + String(httpCode));
  };
  http.end();
  return (payloadLen);
}
