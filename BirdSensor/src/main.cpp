//#include <WiFi.h>
#include <HTTPClient.h>
#include "wifi.h"

#include <WiFiUtilities.h>


#define PAYLOAD_BUFFER_LEN    512


const char* ssid = WLAN_SSID;
const char* password = WLAN_PASS;

const char *host = "worldclockapi.com";
const int port = 80;
const char *uri = "/api/json/utc/now";
char payloadBuffer[PAYLOAD_BUFFER_LEN];


typedef struct {
  wifi_mode_t mode;
  const char *ssid;
  const char *password;
  IPAddress ipAddr;
  byte mac[6];
} WifiParms;

bool setupWifi(WifiParms *pPtr);
int httpGet(const char *host, int port, const char *uri, char *bufPtr, int bufLen);


void errorHalt() {
  Serial.println("HALT"); //// FIXME
  while (false) { ; };
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  };
  delay(1000);
  Serial.println("READY"); //// TMP TMP TMP

  WifiParms wifiParms = {
    WIFI_STA,
    ssid,
    password,
    IPAddress(),
    {0, 0, 0, 0, 0, 0}
  };
  if (setupWifi(&wifiParms)) {
    Serial.println("Initialized WiFi");
  } else {
    Serial.println("ERROR: Failed to init WiFi");
    errorHalt();
  }

  Serial.println("BEGIN"); //// TMP TMP TMP
}

void loop() {
  int payloadLen = httpGet(host, port, uri, payloadBuffer, PAYLOAD_BUFFER_LEN);
  Serial.println(payloadLen);
  Serial.println(payloadBuffer);
  delay(1000);
}

bool setupWifi(WifiParms *pPtr) {
  int n = 0;

  WiFi.mode(pPtr->mode);
  WiFi.begin(pPtr->ssid, pPtr->password);
  Serial.print("Starting WIFI...");
  delay(500);

  while (WiFi.status() != WL_CONNECTED) {
    delay(200);
    Serial.println("Connecting to WiFi.." + String(WiFi.status()));
    if (n++ > 16) {
      Serial.println("ERROR: failed to setup WiFi");
      return (false);
    }
  }

  pPtr->ipAddr = WiFi.localIP();
  WiFi.macAddress(pPtr->mac);
  String macAddr = String(pPtr->mac[0], HEX) + ":" +
    String(pPtr->mac[1], HEX) + ":" +
    String(pPtr->mac[2], HEX) + ":" +
    String(pPtr->mac[3], HEX) + ":" +
    String(pPtr->mac[4], HEX) + ":" +
    String(pPtr->mac[5], HEX);
  Serial.println("Connected to the WiFi network: MAC = ");
  Serial.print(macAddr);
  Serial.print(", ipAddr = ");
  Serial.print(pPtr->ipAddr.toString());
  Serial.print(", RSSI = ");
  Serial.println(WiFi.RSSI());

  return (true);
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
    if (payloadLen >= bufLen) {
      Serial.print("ERROR: buffer overflow (");
      Serial.print(payloadLen); Serial.print(" >= "); Serial.print(bufLen);
      Serial.println(")");
    }
    break;
  default:
    Serial.println("WARNING: Unhandled HTTP response code" + String(httpCode));
  };
  http.end();
  return (payloadLen);
}
