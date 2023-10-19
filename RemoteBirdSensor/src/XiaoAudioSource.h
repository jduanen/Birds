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
    log_i("Initialized I2S microphone: PDM_MONO_MODE");
    I2S.setAllPins(_sclkPin, _fsPin, _sdataPin, _outSdPin, _inSdPin);
//    I2S.setAllPins(-1, 42, 41, -1, -1);
//    if (!I2S.begin(PDM_MONO_MODE, 16000, 16)) {
//    if (!I2S.begin(I2S_PHILIPS_MODE, sampleRate, sampleSize)) {
    if (!I2S.setBufferSize(_bufSize)) {
      log_e("Failed to set buffer size to: %d", _bufSize);
      return true;
    }
    return false;
  };

  void start() {
    if (!I2S.begin(PDM_MONO_MODE, _sampleRate, _sampleSize)) {
      log_e("Failed to initialize I2S microphone");
      //// FIXME throw an exception here
    }
    I2S.read();  // ????
    log_i("Started I2S microphone");
  };

  void stop() {
    I2S.end();
    log_i("Stopped I2S microphone");
  };

  int readBytes(void* dest, int maxBytes) override {
    int numRead = I2S.read(dest, min(I2S.available(), maxBytes));
    if (numRead == false) {
      log_e("Microphone read failed");
      return 0;
    }
    return numRead;
  }

 private:
  int _indx = 0;
  static const int _sclkPin = -1;
  static const int _fsPin = 42;
  static const int _sdataPin = 41;
  static const int _outSdPin = -1;
  static const int _inSdPin = -1;
  static const int _sampleRate = 16000;
  static const int _sampleSize = 16;
  static const int _bufSize = 256;  // default is 128 samples

  int16_t _buffer[_bufSize];
};
