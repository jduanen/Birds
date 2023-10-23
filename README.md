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

* BirdNet-Pi
  - ~/BirdNET-Pi/scripts/birdnet_recording.sh
    * fmpeg -hide_banner -loglevel info -nostdin -vn -thread_queue_size 512 -i rtsp://192.168.166.115:8554 -map 0:a:0 -t 15 -acodec pcm_s16le -ac 2 -ar 48000 file:/home/jdn/BirdSongs/StreamData/2023-10-19-birdnet-RTSP_1-11:24:37.wav
      - change acodec to pcm_s16be and ar to 16000
  - fmpeg -hide_banner -loglevel info -nostdin -vn -thread_queue_size 512 -i rtsp://192.168.166.115:8554 -map 0:a:0 -t 15 -acodec pcm_s16le -ac 2 -ar 48000 file:/home/jdn/BirdSongs/StreamData/2023-10-19-birdnet-RTSP_1-11:24:37.wav
  - ffmpeg -hide_banner -loglevel info -nostdin -vn -thread_queue_size 512 -i  rtsp://192.168.166.115:8554 -map 0:a:0 -t 15 -acodec pcm_s16le -ac 2 -ar 48000 file:/home/jdn/BirdSongs/StreamData/2023-10-14-birdnet-RTSP_1-15:57:13.wav
  - ffmpeg -nostdin -loglevel error -ac 1 -i rtsp://192.168.166.115:8554 -acodec libmp3lame -b:a 320k -ac 1 -content_type audio/mpeg -f mp3 icecast://source:birdnetpi@localhost:8000/stream -re
  - ?

* ESP32-S3 Sense A/V source device
  - Micro-RTSP-Audio Example
    * comes with AudioTestSource class that emits a loop of tone bursts
    * play with ffmpeg
      - ffplay -v debug rtsp://192.168.166.115:8554
    * N.B. doesn't work with vlc
    * modify example code
      - use wifi.h for credentials
      - use default port
    * Arduino
      - Ardunio2->File->Examples->Micro-RTSP-Audio->RTSPTestServer
      - Tools->Events Run on Core '0'
      - Tools->Arduino Runs on Core '0'
      - Tools->Core Debug Level 'Debug'
    * VSCode/PlatformIO
      - ? having trouble making this work ?
    * make different audio test sources
      - edit AudioTestSource.h
        * ?
      - select RTSP format
        * https://en.wikipedia.org/wiki/RTP_payload_formats
          - original code defaulted to 2 byte PCM info with 16000 samples per second on 1 channel
            * p_fmt = new RTSPFormatPCM();
        * RTSPFormat.h
          - PCMInfo() class defines: sample rate, channels, sample size
          - PCMFormatPCM() class can use defaults or provide pointer to PCMInfo object
  - ESP32 AV Source
    * made work with VSCode/PlatformIO
    * to enable logging (e.g., log_?(<str>))
      - add "Serial.setDebugOutput(true);" to setup()
      - add "-DCORE_DEBUG_LEVEL=ARDUHAL_LOG_LEVEL_DEBUG" to platformio.ini
    * add delay after Serial setup to catch initial output on startup
    * get this error message
      - begin(): This mode is not officially supported - audio quality might suffer.
      At the moment the only supported mode is I2S_PHILIPS_MODE
      - Modes:
        I2S_PHILIPS_MODE
        I2S_RIGHT_JUSTIFIED_MODE
        I2S_LEFT_JUSTIFIED_MODE
        PDM_MONO_MODE
    * from https://espressif-docs.readthedocs-hosted.com/projects/arduino-esp32/en/latest/api/i2s.html
      - Officially supported operation mode is only I2S_PHILIPS_MODE. Other modes are implemented, but we cannot guarantee flawless execution and behavior.
    * I2S buffer size:
      - 8-1024 samples, default 128
      - always assumes two channels (even when MONO)
    * I2S docs:
      - https://github.com/espressif/arduino-esp32/blob/master/docs/source/api/i2s.rst
      - https://wiki.seeedstudio.com/xiao_esp32s3_sense_mic/


* XIAO ESP32-S3 Sense Microphone
  - configuration
    * I2S.setAllPins(-1, 42, 41, -1, -1);
    * I2S.begin(PDM_MONO_MODE, 16000, 16);
  - Pulse Density Modulation
    * each sample is in int16_t data format
  - from: https://wiki.seeedstudio.com/xiao_esp32s3_sense_mic/
    * It should be noted that for the current ESP32-S3 chip, we can only use PDM_MONO_MODE and the sampling bit width can only be 16bit. only the sampling rate can be modified, but after testing, the sampling rate at 16kHz is relatively stable.

* Audio tools
  - audacity
    * good visualization and editing of audio streams
  - ffmpeg
  - ffplay
    * options
      -decoders: list decoders
      -acodec <codec>: audio codec, pcm_s16be, pcm_s16le, etc.
      -vn: no video
  - jaaa
  - jack
  - jnoisemeter
  - rec
  - sox
  - soxi
  - spek
  - ?

* Links
  - https://github.com/atomic14/esp32_wireless_microphone
  - https://github.com/ikostoski/esp32-i2s-slm
  - https://iotassistant.io/esp32/smart-door-bell-noise-meter-using-fft-esp32/
  - https://gist.github.com/krisnoble/6ffef6aa68c374b7f519bbe9593e0c4b
