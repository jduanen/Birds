#include <Arduino.h>
/*
#include <Audio.h>
#include <I2S.h>
#include <FS.h>
#include <SD.h>
#include <SPI.h>
#include <WiFi.h>
#include <WiFiMulti.h>
#include <HTTPClient.h>
*/

#include "wifi.h"


#define SERVER_NAME     "gpuServer1"
#define SERVER_PORT     8080

#define SCK_PIN         -1  // Clock
#define FS_PIN          42  // Frame Sync
#define SD_PIN          41  // Data
#define OUT_SD_PIN      -1  // Data Input
#define IN_SD_PIN       -1  // Data Output

#define I2S_SAMPLE_RATE 16000
#define BITS_PER_SAMPLE 16

#define MAX_SAMPLES     256  // FIXME
#define I2S_BUF_SIZE    MAX_SAMPLES
#define I2S_MODE        PDM_MONO_MODE  // Master Mode

/*
  String serverURL = "http://" + String(pPtr->serverName) + ":" + String(pPtr->serverPort);
  http.begin(serverURL.c_str());
*/

typedef struct {
  wifi_mode_t mode;
  char* ssid;
  char* password;
  IPAddress ipAddr;
  byte mac[6];
} WifiParms;

typedef struct {
  int8_t sClkPin;
  int8_t fsPin;
  int8_t dataPin;
  int8_t inDataPin;
  int8_t outDataPin;
  uint16_t mode;
  uint32_t sampleRate;
  uint8_t bitsPerSample;
  int16_t bufSize;
} MicParms;


bool setupWifi(WifiParms *pPtr);
bool setupMic(MicParms *pPtr);
void readMic(int *samples, int numSamples);


void errorHalt() {
  Serial.println("HALT"); //// FIXME
  while (false) { ; };
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {};
  delay(5000);
  Serial.println("READY");

  WifiParms wifiParms; // = {};
/*
    WIFI_STA,
    WIFI_PASS,
    WIFI_SSID,
    0
  };
  */
  if (setupWifi(&wifiParms)) {
    Serial.println("Initialized WiFi");
  } else {
    Serial.println("ERROR: Failed to init WiFi");
    errorHalt();
  }

  /*
  // start I2S at 16 kHz with 16-bits per sample
  I2S.setAllPins(-1, 42, 41, -1, -1);
  if (!I2S.begin(PDM_MONO_MODE, 16000, 16)) {
    Serial.println("Failed to initialize I2S!");
    while (1); // do nothing
  }
  */
  
  // start I2S at 16 kHz with 16-bits per sample
  MicParms micParms = {
    SCK_PIN,
    FS_PIN,
    SD_PIN,
    OUT_SD_PIN,
    IN_SD_PIN,
    I2S_MODE,
    I2S_SAMPLE_RATE,
    BITS_PER_SAMPLE,
    -1  // I2S_BUF_SIZE
  };
  if (setupMic(&micParms)) {
    Serial.println("Initialized I2S Microphone");
  } else {
    Serial.println("ERROR: Failed to init I2S Microphone");
    errorHalt();
  }

  Serial.println("BEGIN");
}

int minVal = 0xFFFFFFFF;
int maxVal = 0;

void loop() {
  // read a sample
  int sample = I2S.read();
//  Serial.println(String(sample, HEX));


  if (sample && sample != -1 && sample != 1) {
//    Serial.println(sample);

    if (sample < minVal) {
      minVal = sample;
      Serial.print("min="); Serial.println(sample);
    }
    if (sample > maxVal) {
      maxVal = sample;
      Serial.print("max="); Serial.println(sample);
    }
  }
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
  Serial.println("Connected to the WiFi network: " + macAddr + " @ " + pPtr->ipAddr.toString());
  Serial.println("RSSI = " + String(WiFi.RSSI()));
  return (true);
}

bool setupMic(MicParms *pPtr) {
  I2S.setAllPins(pPtr->sClkPin, pPtr->fsPin, pPtr->dataPin, pPtr->outDataPin, pPtr->inDataPin);
  if (!I2S.begin(pPtr->mode, pPtr->sampleRate, pPtr->bitsPerSample)) {
    Serial.println("ERROR: Failed to initialize I2S!");
    return (false);
  }

  if (pPtr->bufSize > 0) {
    if (!I2S.setBufferSize(pPtr->bufSize)) {
      //Serial.println("ERROR: Failed to set I2S buffer to " + String(I2S_BUF_SIZE) + " Bytes"); 
      Serial.print("ERROR: Failed to set I2S buffer to "); Serial.print(I2S_BUF_SIZE) + Serial.println(" Bytes");
      return (false);
    }
  }
  return (true);
}

/*
void readMic(int *samples, int numSamples) {
  int read;
  int available;
  int toRead = numSamples;

  while (toRead > 0) {
    available = I2S.available();
    read = (available >= toRead) ? toRead : available;
    toRead -= I2S.read(samples, read);
  }
}
*/

void readMic(byte *samples, int numSamples) {
  //// TODO do multiple byte reads when possible
  for (int i = 0; (i < numSamples); i++) {
    samples[i] = I2S.read();
//    Serial.print("S: "); Serial.println(samples[i]);
  }
}

#ifdef UNDEF
void setClock() {
  configTime(0, 0, "pool.ntp.org");

  Serial.print(F("Waiting for NTP time sync: "));
  time_t nowSecs = time(nullptr);
  while (nowSecs < 8 * 3600 * 2) {
    delay(500);
    Serial.print(F("."));
    yield();
    nowSecs = time(nullptr);
  }

  Serial.println();
  struct tm timeinfo;
  gmtime_r(&nowSecs, &timeinfo);
  Serial.print(F("Current time: "));
  Serial.print(asctime(&timeinfo));
}
#endif /* UNDEF */
