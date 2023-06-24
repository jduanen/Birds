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
