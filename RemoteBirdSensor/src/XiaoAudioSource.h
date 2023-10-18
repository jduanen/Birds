#pragma once

#include <stdint.h>
#include <SPI.h>
#include <I2S.h>

#include "IAudioSource.h"

class XiaoAudioSource : public IAudioSource {

 public:
  XiaoAudioSource() {};

  //// FIXME make this take args and select different audio formats
  bool init() {
    log_i("INIT: PDM_MONO_MODE");
    I2S.setAllPins(_sclkPin, _fsPin, _sdataPin, _outSdPin, _inSdPin);
//    I2S.setAllPins(-1, 42, 41, -1, -1);
//    if (!I2S.begin(PDM_MONO_MODE, 16000, 16)) {
//    if (!I2S.begin(I2S_PHILIPS_MODE, sampleRate, sampleSize)) {
    if (!I2S.begin(PDM_MONO_MODE, _sampleRate, _sampleSize)) {
      Serial.println("Failed to initialize I2S!");
      return true;
    }
    return false;
  }

  int readBytes(void* dest, int maxBytes) override {
    int16_t* destSamples = (int16_t*)dest;
    for (int i = 0; i < maxBytes/2; i++) {
      destSamples[i] = (0xFFFF & _indx++);
    }
    return maxBytes;
  }

  void start() { log_i("start"); }
  void stop() { log_i("stop"); }

 private:
  int _indx = 0;
  static const int _sclkPin = -1;
  static const int _fsPin = 42;
  static const int _sdataPin = 41;
  static const int _outSdPin = -1;
  static const int _inSdPin = -1;
  static const int _sampleRate = 16000;
  static const int _sampleSize = 16;
};
