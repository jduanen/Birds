/***************************************************************************
 *
 * Example of WiFi Utilities
 *
 ***************************************************************************/

#include <Arduino.h>
#include <WiFiUtilities.h>
#include "wifi.h"


const char *ssid = WLAN_SSID;
const char *password = WLAN_PASS;

#define VERBOSE 1
#define APP_NAME "WiFiExample"
#define APP_VERSION "1.0.0"

WiFiUtilities *wifi;

//// TODO make test cases for: working/not working STA/AP connections, timed, immediate (caller handled)

void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  };
  delay(1000);
  Serial.println(String(APP_NAME) + ": BEGIN");
  wifi = new WiFiUtilities(WIFI_STA, ssid, password, -1);
  Serial.println(String(APP_NAME) + ": READY");
}

void loop()
{
  delay(10000);
};
