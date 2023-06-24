# Birds
ML-based bird detection and classification tools and devices

**WIP**

## Notes
* Audio-based bird detector
  - listen for bird sounds
  - classify bird sounds with ML model (e.g., BirdNET)
  - when given birds are detected (with a given confidence level)
    * take a picture
    * send a notification
    * log time/date
  - development process
    * start running ML model and audio capture on desktop
    * run ML model server and logic on desktop
      - capture and stream audio from ESP32-S3 Sense device
    * run ML model and logic on ESP device, send notifications, log on server (or local file system on SD card)

* Links
  - https://github.com/atomic14/esp32_wireless_microphone
  - https://github.com/ikostoski/esp32-i2s-slm
  - https://iotassistant.io/esp32/smart-door-bell-noise-meter-using-fft-esp32/
  - https://gist.github.com/krisnoble/6ffef6aa68c374b7f519bbe9593e0c4b
