#include <Arduino.h>
#include <HTTPClient.h>

#include <WiFiUtilities.h>
#include "wifi.h"


#define PAYLOAD_BUFFER_LEN    512

const char* ssid = WLAN_SSID;
const char* password = WLAN_PASS;

const char *host = "gpuServer1"; // "worldclockapi.com";
const int port = 8000;
char payloadBuffer[PAYLOAD_BUFFER_LEN];

IPAddress ipAddr;
byte mac[6];
WiFiUtilities *wifi;


int httpPost(const char *host, int port, const char *uri, char *bufPtr, int bufLen);
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
    wifi = new WiFiUtilities(WIFI_STA, ssid, password, -1);
    Serial.println("BEGIN"); //// TMP TMP TMP
}

void loop() {
    /*
    // GET json file
    Serial.print("GET: http://" + String(host));
    if (port > 0) {
        Serial.print(":"); Serial.print(port);
    }
    const char *uri = "/now.json"; // "/api/json/utc/now";
    Serial.println(uri);
    int payloadLen = httpGet(host, port, uri, payloadBuffer, PAYLOAD_BUFFER_LEN);
    Serial.println(payloadLen);
    Serial.println(payloadBuffer);
    */

    // send a POST request
    char *buf = "{\"$id\":\"1\",\"currentDateTime\":\"2023-06-26T21:34Z\",\"utcOffset\":\"00:00:00\",\"isDayLightSavingsTime\":false,\"dayOfTheWeek\":\"Monday\",\"timeZoneName\":\"UTC\",\"currentFileTime\":133322888567487654,\"ordinalDate\":\"2023-177\",\"serviceResponse\":null}";
    int resp = httpPost("gpuServer1", 8000, "/analyze", buf, strlen(buf));

    delay(10000);
}

int httpPost(const char *host, int port, const char *uri, char *bufPtr, int bufLen) {
    int payloadLen = 0;
    HTTPClient http;

    if (port > 0) {
        http.begin(host, port);
    } else {
        http.begin(host);
    }
    http.setURL(uri);
    Serial.print("URI: "); Serial.println(uri);

    wl_status_t wifiStatus = wifi->getWiFiStatus();
    if (wifiStatus != WL_CONNECTED) {
        Serial.println("WARNING: WiFi not connected - " + String(wifiStatus));
        payloadLen = -1;
    } else {
        http.addHeader("Content-Type", "application/json"); //"multipart/form-data");
        int httpCode = http.POST((uint8_t *)bufPtr, bufLen);
        Serial.println(httpCode);
        if (httpCode > 0) {
            switch (httpCode) {
            case 200:
                Serial.println("Successful POST");
                break;
            default:
                Serial.println("WARNING: Unhandled HTTP response code - " + String(httpCode));
                payloadLen = -1;
                break;
            }
        } else {
            Serial.println("ERROR: HTTP GET response error code received - " + String(httpCode));
        }
    }
    http.end();
    return (payloadLen);
}

int httpGet(const char *host, int port, const char *uri, char *bufPtr, int bufLen) {
    int payloadLen = 0;
    String payload;
    HTTPClient http;

    if (port > 0) {
        http.begin(host, port);
    } else {
        http.begin(host);
    }
    http.setURL(uri);
    Serial.print("URI: "); Serial.println(uri);

    wl_status_t wifiStatus = wifi->getWiFiStatus();
    if (wifiStatus != WL_CONNECTED) {
        Serial.println("WARNING: WiFi not connected - " + String(wifiStatus));
        payloadLen = -1;
    } else {
        int httpCode = http.GET();
        if (httpCode > 0) {
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
                Serial.println("WARNING: Unhandled HTTP response code - " + String(httpCode));
                payloadLen = -1;
                break;
            }
        } else {
            Serial.println("ERROR: HTTP GET response error code received - " + String(httpCode));
        }
    }
    http.end();
    return (payloadLen);
};
