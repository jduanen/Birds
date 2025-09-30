# Birds
ML-based bird detection and classification tools and devices

I looked at several BirdNET-Pi repos on git hub, and settled on the one from ppdpauw (git@github.com:pddpauw/BirdPi.git).  <add reasons why, and what I had to do here>

I tried a variety of different approaches to get high-quality audio input, including:
  - creating a remote microphone (and camera) unit that streams RTSP audio (and video) to an instance of BirdNET-Pi <put in results here>
  - tried a large variety of different microphones and ADCs connected directly to the Raspi running BirdNET-Pi. <put in results here>
  - tried a number of different outdoor WebCams as RTSP sources <put results here>


![BirdPi Sensor](BirdPiSensor.png)


## My implementations of BirdPi
  - several different repos exist, using Nachtzuster
    * lineage: kahst -> mcquirepr89 -> pddpauw/BirdPi-\
                                    \-------------------> Nachtzuster
  - currently running: https://github.com/pddpauw/BirdPi.git 
    * No longer supported, refers to this repository: https://github.com/Nachtzuster/BirdNET-Pi
  - switching to Nachtzuster and adding Headless RasPi support

### Install and Configure BirdNET-Pi and HeadlessRasPi

* clean install of Bookworm-Lite with rpi-imager

* update the system
  - `sudo apt update`
  - `sudo apt upgrade`

* install Nachtzuster
  - `curl -s https://raw.githubusercontent.com/Nachtzuster/BirdNET-Pi/main/newinstaller.sh | bash`
    * creates a log in '$HOME/installation-$(date "+%F").txt'

* configure BirdNet
  - if there's a backup, use the old config file
    * on *birdpi.lan*:
      - `cp birdnet.conf birdnet.conf.orig`
      - `chmod 664 birdnet.conf`
    * on *host*:
      - `scp birdnet.conf ${USER}@birdpi.lan:BirdNET-Pi/birdnet.conf.old`
      - `scp apprise.txt ${USER}@birdpi.lan:BirdNET-Pi/`
  - on the web page: http://birdpi.lan --> Tools->Settings->Basic Settings
    * Location->Latitude/Longitude
    * Notifications [Optional]
      - keep 'hassio:*' line and remove 'mqtt:*' line
      - Tools->Settings->Advanced Settings
        * BirdNET-Lite Settings
          - Minimum Confidence: 0.85
    * Bird Photo Source->Image Provider: Wikipedia
  - manually update applications
    * scripts/update_birdnet.sh
  - update model to v2
    * curl -s https://raw.githubusercontent.com/pddpauw/BirdPi/main/install_model_V2_4V2.sh| bash

* set limits on journal logs
  - edit /etc/systemd/journald.conf
    * 'SystemMaxUse=500M'
    * alternatively: 'MaxFileSec=7day'

* copy my tools
  - on *birdpi.lan*: `mkdir ~/bin/`
  - on *host*:
    * `cd ~/Code/Birds/Backups/${USER}/BirdNET-Pi/`
    * `scp rssi.sh maxTemp.sh ${USER}@birdpi.lan:bin/`

* copy backed up database from earlier version
==> this doesn't work, figure out how to fix it
  - on *birdpi.lan*:
    * `cp BirdDB.txt BirdDB.txt.orig`
    * `cp scripts/birds.db scripts/birds.db.orig`
  - on *host*:
    * `scp BirdDB.txt ${USER}@birdpi.lan:BirdNET-Pi/`
    * `scp scripts/birds.db ${USER}@birdpi.lan:BirdNET-Pi/scripts/`

* install HeadlessRasPi package
  - install and configure Mini Information Display
    * enable I2C on *birdpi.lan*
      - `sudo raspi-config`
        * Interface Options -> I2C: `enable`
      - reboot the device
    * install i2c tools
      - `sudo apt-get install i2c-tools`
    * clone my HeadlessRasPi repo from github
      - `mkdir ~/Code`
      - `cd ~/Code/`
      - `git clone https://github.com/jduanen/HeadlessRasPi.git`
    * install Python libraries in a venv on *birdpi.lan*
      - `sudo apt install virtualenvwrapper python3-virtualenvwrapper`
      - `echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bashrc`
      - `echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python" >> ~/.bashrc`
      - `echo "source /usr/share/virtualenvwrapper/virtualenvwrapper.sh" >> ~/.bashrc`
      - `mkvirtualenv --python=`which python3` --prompt=wifi WIFI`
        * if first time, run `bash` to execute new .bashrc commands
        * if already loaded the new bashrc, just run `workon WIFI`
    * install python packages with pip
      - on *birdpi.lan*
        * `cd ~/Code/HeadlessRasPi`
        * `pip3 install -r requirements.txt`
    * configure system to activate information display when the WiFi subsystem's state changes
      - on *birdpi.lan*
        * `cd ~/Code/HeadlessRasPi`
        * `sudo cp ./etc/NetworkManager/dispatcher.d/90wifi-state-change.sh /etc/NetworkManager/dispatcher.d/`
  - enable Information Display Trigger Switch
    * install service description
      - `cd ${HOME}/Code/HeadlessRasPi`
      - `sudo ln -s ${HOME}/Code/HeadlessRasPi/etc/systemd/system/infoDisplay.service /etc/systemd/system/`
    * reload systemd
      - `sudo systemctl daemon-reload`
    * start the service
      - `sudo systemctl start infoDisplay`
    * make sure it works
      - `sudo systemctl status infoDisplay`
    * enable start of service on boot
      - `sudo systemctl enable infoDisplay`
    * Connections:
      - `GND`: pin 39 (bottom row, farthest from the edge)
      - `GPIO20`: pin 38 (next to the bottom row, closest to the edge)

* install Comitup
  - fix bookworm WiFi bug
    * `cd ~/Code/HeadlessRasPi`
    * `sudo mv ./conf/brcmfmac.conf /etc/modprobe.d/brcmfmac.conf`
  - get the latest build
    * get link to latest release at: 'https://davesteele.github.io/comitup/latest/comitup_latest.html'
      - use this instead of the path below if it's different
  - install the latest build
    * `cd ~/Code`
    * `wget https://davesteele.github.io/comitup/deb/comitup_1.43-1_all.deb`
    * `sudo dpkg -i --force-all comitup_1.43-1_all.deb`
  - check that it's been properly installed
    * `apt list | egrep comitup`  # comitup/now 1.43-1 all [installed,local]
  - fix bug: NM is out of sync with it's python bindings
    * "It seems rather fragile manually ensuring that the network manager bindings and its python bindings are in sync."
    *  patch NetworkManager.py
      - add NM_DEVICE_TYPE_LOOPBACK (32) to NetworkManager.py
      - it's a deprecated package, so I cloned the repo and added the necessary lines
      - `sudo cp /usr/lib/python3/dist-packages/NetworkManager.py /usr/lib/python3/dist-packages/NetworkManager.py.orig`
      - `cd ~/Code/HeadlessRasPi`
      - `sudo patch /usr/lib/python3/dist-packages/NetworkManager.py NetworkManager.patch`

* configure Comitup
  - edit config file to enable flushing of WiFi credentials
    * `sudo cp /etc/comitup.conf /etc/comitup.conf.orig`
    * `sudo ex /etc/comitup.conf`
      - enable flushing the WiFi credentials with `enable_nuke: 1`
      - can also set `verbose: <n>` if you want logs in `/var/log/comitup.log` and `/var/log/comitup-web.log`
* finish install of Comitup and test it
  - remove the file that rpi-imager sets up to preconfigure the WiFi
    * `sudo rm /etc/NetworkManager/system-connections/preconfigured.nmconnection`
  - move the web server to a different port (80 and 8080 are taken by birdpi)
    * `sudo cp /usr/share/comitup/web/comitupweb.py /usr/share/comitup/web/comitupweb.py.orig`
    * `sudo ex /usr/share/comitup/web/comitupweb.py`
      - change port '80' to '9090' on line 179
  - remove it and reboot
  - test nuke feature by shorting GPIO pins 39 and 40 for three seconds or more
    * look for green LED to flash three times
  - notes
    * the comitup utility writes connection files to /etc/NetworkManager/system-connections/
      - `comitup-<num>-<num'>.nmconnection`: the 10.41.0.1 config address
        * [connection]->autoconnect flag set to `false`
        * [ipv4]->method = `manual`
      - `<SSID>.nmconnection`: the connection that was provisioned via the web interface
        * this should be `chmod 600`
        * this does not have the [connection]->autoconnect flag set to `true`
          - it doesn't exist at all in this file
        * [ipv4]->method = `auto`
* test Comitup
  - short pins 39 and 40 to flush the current configuration
    * watch for green LED to flash three times indicating done
  - connect to "comitup-<num>" AP
  - open 'http://10.0.41.1:9090'
    * enter in wifi credentials
* after all is stable, stop or disable Comitup (to save resources)
  - `sudo systemd stop/disable comitup.service`
  - can restart again if changing networks

### Using MEMS Microphone

* INMP441 I2S mic
  - Connect to 40pin header
    * VDD: 17 (3V3)
    * GND: 14 (GND)
    * SCK: 12 (BCM18) [I2S BCLK]
    * WS: 35 (BCM19) [I2S LRCL]
    * SD: 38 (BCM20) [I2S Data In]
    * L/R: left=GND, right=3V3 [Channel Select]
  - enable I2S interface
    * `sudo ex /boot/firmware/config.txt`
      - dtparam=i2s=on
      - dtoverlay=googlevoicehat-soundcard
    * **see if this can be done with `raspi-config`**
    * reboot
  - install packages
    * `sudo apt-get update`
    * `sudo apt-get install python3-pip`
    * `sudo apt install python3-pyaudio`
  - enable mic in ALSA
    * `wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/i2smic.py`
    * set up venv as root and enable I2S mic then exit root
      - `sudo -s`
      - `python3 -m venv ~/myenv`
      - `source ~/myenv/bin/activate`
      - `python3 -m pip install adafruit-python-shell`
    * `python3 i2smic.py`
    * `reboot`
  - test with ALSA
    * `arecord -L`
    * `arecord -D plughw:1 -c2 -r 48000 -f S32_LE -t wav test.wav`
  - test with sox
    * `sudo apt install sox`
    * `sox test.wav test_norm.wav --norm=0`

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
  - https://wiki.seeedstudio.com/xiao_esp32s3_sense_mic/
  - https://github.com/rzeldent/esp32cam-rtsp/issues/86
  - https://github.com/rzeldent/esp32cam-rtsp
  - https://github.com/spawn451/ESP32-CAM_Audio
  - https://github.com/AlexxIT/go2rtc#cameras-experience
  - https://github.com/pschatzmann?tab=repositories
  - https://pschatzmann.github.io/Micro-RTSP-Audio/docs/html/class_audio_streamer.html

* Birdpi
  - https://github.com/pddpauw/BirdPi/tree/main
    * fork that is maintained (unlike mcquirepr89)
  - uses caddy (instead of nginx)
  - need to change php version in /etc/caddy/Caddyfile to match system (or install new version)
  - update applications
    * scripts/update_birdnet.sh
  - update model to v2
    * curl -s https://raw.githubusercontent.com/pddpauw/BirdPi/main/install_model_V2_4V2.sh| bash
  - tools: birdnet/''
  - passwd hash: $2a$14$QIyBqJ07wDpdyvhVB9d8FuW.ogUJAp31AsmDbBOsUV5AzdD/B5Jte
  - see ~/Notes/Audio.txt

* BirdNet-Pi [DEPRECATED]
  - command lines
    * ~/BirdNET-Pi/scripts/birdnet_recording.sh
      - fmpeg -hide_banner -loglevel info -nostdin -vn -thread_queue_size 512 -i rtsp://192.168.166.115:8554 -map 0:a:0 -t 15 -acodec pcm_s16le -ac 2 -ar 48000 file:/home/jdn/BirdSongs/StreamData/2023-10-19-birdnet-RTSP_1-11:24:37.wav
      - change acodec to pcm_s16be and ar to 16000
    * ?
      - fmpeg -hide_banner -loglevel info -nostdin -vn -thread_queue_size 512 -i rtsp://192.168.166.115:8554 -map 0:a:0 -t 15 -acodec pcm_s16le -ac 2 -ar 48000 file:/home/jdn/BirdSongs/StreamData/2023-10-19-birdnet-RTSP_1-11:24:37.wav
    * ?
      - ffmpeg -hide_banner -loglevel info -nostdin -vn -thread_queue_size 512 -i  rtsp://192.168.166.115:8554 -map 0:a:0 -t 15 -acodec pcm_s16le -ac 2 -ar 48000 file:/home/jdn/BirdSongs/StreamData/2023-10-14-birdnet-RTSP_1-15:57:13.wav
    * ?
      - ffmpeg -nostdin -loglevel error -ac 1 -i rtsp://192.168.166.115:8554 -acodec libmp3lame -b:a 320k -ac 1 -content_type audio/mpeg -f mp3 icecast://source:birdnetpi@localhost:8000/stream -re
  * ?
    - arecord -f S16_LE -c1 -r48000 -t wav --max-file-time 15 -D dsnoop:CARD=Device,DEV=0 --use-strftime /home/jdn/BirdSongs/%B-%Y/%d-%A/%F-birdnet-%H:%M:%S.wav
  * ?
    - sox -V1 /home/jdn/BirdSongs/October-2023/26-Thursday/2023-10-26-birdnet-16:11:06.wav -n remix 1 rate 24k spectrogram -c BirdSongs/October-2023/26-Thursday/2023-10-26-birdnet-16:11:06.wav -o /home/jdn/BirdSongs/Extracted/spectrogram.png
  * ?
    - ffmpeg -nostdin -loglevel error -ac 1 -f alsa -i dsnoop:CARD=Device,DEV=0 -acodec libmp3lame -b:a 320k -ac 1 -content_type audio/mpeg -f mp3 icecast://source:birdnetpi@localhost:8000/stream -re
  - Settings
    * use the GLOBAL_6K_V2.4_Model_FP16 model
    * enter lat/lon
    * setup Apprise Notifications
      - select notification mechanism
        * Google Chat: ?
        * Home Assistant: ?
        * IFTTT: ?
        * MQTT: ?
        * Telegram: ?
        * Twitter: ?
        * WhatsApp: ?
        * SMS
          - Twilio: ?
          - Vonage: ?
        * Desktop: ?
        * Email: ?
      - set white-/black-list birds
      - select min time between notifications of same species
  - Advanced Settings:
    * purge old files when disk full (or keep)
    * Audio Settings
      - Audio Card:
        * 'default': use PulseAudio (always recommended)
        * else: use ALSA sound card device from "arecord -L" list
          - USB mic: "dsnoop:CARD=Device,DEV=0"
          - ?
      - Audio Channels: 1 [1-2]
      - Recording Length: 15 seconds [6-60] (multiples of 3 recommended)
      - Extraction Length:  [min=3, max=Recording Length]
      - Extractions Audio Format: s16
      - RSTP Stream: (multiple streams are allowed)
    * Password
    * Custom URL
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
  - ffplay: media player using ffmpeg libraries
    * options
      -decoders: list decoders
      -acodec <codec>: audio codec, pcm_s16be, pcm_s16le, etc.
      -vn: no video
  - jaaa: JACK and ALSA audio analyzer
    * 
  - jackd: JACK audio connection kit sound server
    * jackd1 and jackd2 exist
  - jnoisemeter: measure audio test signals
    * depends on Jack
    * can measure S/N ratio of sound card
  - rec
    * record from default device to WAV file
      - rec --channels 1 -b 24 ./<file>.wav
  - sox
    * print information about file
      - sox -i ./<file>.wav
    * print statistics on audio in file
      - sox ./<file>.wav -n stat
    * print stats for all wav files in a dir
      - for f in *.wav; do echo "----"; echo $f; sox $f -n stat; sox $f -n stats; done
  - soxi: get information about audio file
    * equivalent to sox --i
  - spek: audio spectrum analyzer
    * give it an audio file and it displays spectrogram and info on the file
    * 
  - ?

* USB ADCs
  - Brand: USB type, bias voltage, linux dev
  - UGREEN: Type A, 0V, n/a
    ==> USB device not recognized
    * ?
  - UGREEN: Type C, 0V, n/a
    ==> USB device not recognized
    * ?
  - JSAUX: Type A, 0V, n/a
    ==> USB device not recognized
    * ?
  - JSAUX i/o: Type A, 2.7V, ?
    * Audio Card: "snoop:CARD=AUDIO,DEV=0"
    * dmesg
      - ?
    * arecord -t wav -c 1 -r 48000 -f S16_LE -D dsnoop:CARD=AUDIO,DEV=0 /tmp/foo.wav
      - low volume
  - CULILUX: Type C, 0V, Generic USB-C Audio Adapter
    * Audio Card: "snoop:CARD=Adapter,DEV=0"
    * dmesg
      - New USB device found, idVendor=0bda, idProduct=4926, bcdDevice= 0.05
        Product: USB-C Audio Adapter
        input: Generic USB-C Audio Adapter as /devices/platform/scb/fd500000.pcie/pci0000:00/0000:00:00.0/0000:01:00.0/usb1/1-1/1-1.1/1-1.1:1.3/0003:0BDA:4926.0003/input/input4
        hid-generic 0003:0BDA:4926.0003: input,hidraw0: USB HID v1.11 Device [Generic USB-C Audio Adapter] on usb-0000:01:00.0-1.1/input3
    * ?
  - SABRENT: Type A, 2.7V, USB Audio Device
    * input and output capable, different connectors
      - use the pink connector
    * Audio Card: "snoop:CARD=Device,DEV=0"
    * dmesg
      - New USB device found, idVendor=0d8c, idProduct=0014, bcdDevice= 1.00
        Product: USB Audio Device
        Manufacturer: C-Media Electronics Inc.
        input: C-Media Electronics Inc. USB Audio Device as /devices/platform/scb/fd500000.pcie/pci0000:00/0000:00:00.0/0000:01:00.0/usb1/1-1/1-1.1/1-1.1:1.3/0003:0D8C:0014.0004/input/input5
        hid-generic 0003:0D8C:0014.0004: input,hidraw0: USB HID v1.00 Device [C-Media Electronics Inc. USB Audio Device] on usb-0000:01:00.0-1.1/input3
    * arecord -t wav -c 1 -r 48000 -f S16_LE -D dsnoop:CARD=Device,DEV=0 /tmp/foo.wav
      - low volume
  - MCSPER: Type A, 0V, ?
    * input and output capable, same connector
    * high-speed USB capable?
    * Audio Card: "snoop:CARD=Audio,DEV=0"
    * dmesg
      - New USB device found, idVendor=001f, idProduct=0b21, bcdDevice= 1.00
        Product: TX USB Audio
        Manufacturer: TX Co.,Ltd
        Warning! Unlikely big volume range (=11520), cval->res is probably wrong.
        [2] FU [PCM Playback Volume] ch = 1, val = -11520/0/1
        Warning! Unlikely big volume range (=8191), cval->res is probably wrong.
        [5] FU [Mic Capture Volume] ch = 1, val = 0/8191/1
        input: TX Co.,Ltd TX USB Audio as /devices/platform/scb/fd500000.pcie/pci0000:00/0000:00:00.0/0000:01:00.0/usb1/1-1/1-1.1/1-1.1:1.3/0003:001F:0B21.0005/input/input6
        hid-generic 0003:001F:0B21.0005: input,hidraw0: USB HID v2.01 Device [TX Co.,Ltd TX USB Audio] on usb-0000:01:00.0-1.1/input3
  - GeneralPlus, Type A, 2.44V, USB Audio Device
    * white dongle, with input and output
    * Audio Card: "snoop:CARD=Device,DEV=0"
    * dmesg
      - USB HID v2.01 Device [GeneralPlus USB Audio Device]

* Microphones
  - USB Mic
    * PNP Sound Device
    * Audio Card: "snoop:CARD=Device,DEV=0"
    * dmesg:
      - New USB device found, idVendor=08bb, idProduct=2902, bcdDevice= 1.00
        Product: USB PnP Sound Device
        Manufacturer: C-Media Electronics Inc. 
        input: C-Media Electronics Inc.       USB PnP Sound Device as /devices/platform/scb/fd500000.pcie/pci0000:00/0000:00:00.0/0000:01:00.0/usb1/1-1/1-1.1/1-1.1:1.2/0003:08BB:2902.0002/input/input3
        hid-generic 0003:08BB:2902.0002: input,hidraw0: USB HID v1.00 Device [C-Media Electronics Inc.       USB PnP Sound Device] on usb-0000:01:00.0-1.1/input2
    * arecord -t wav -c 1 -r 48000 -f S16_LE -D dsnoop:CARD=Device,DEV=0 /tmp/foo.wav
      - low volume?
  - MCm-1
    * SABRENT
      - low volume
    * MCSPER
      - nothing
    * CULILUX
      - nothing
    * JSAUX i/o
      - low volume
  - Sun Mic
    * SABRENT
      - very low volume
  - Sun Lozenge Mic
    * SABRENT
      - without battery: nothing
      - with battery: low volume
  - Yamaha Mic
    * SABRENT
      - very low volume
  - Moded Sun Mic
    * SABRENT
      - noise
  - Mic MAX4466
    * ?
  - Mic Amp - MAX4466
    * http://adafru.it/1063
  - Electret Mic Amp - MAX9814
    * http://adafru.it/1713

* I2S Microphone on Raspi
  - I2S Microphones
    * Adafruit PDM MEMS Microphone
      - links
        * https://www.adafruit.com/product/3492
        * https://learn.adafruit.com/adafruit-pdm-microphone-breakout/
      - Pulse Density Modulation (PDM)
        * similar to 1bit PWM
        * 1-3MHz clock rate
        * data line is square wave that syncs from clock
        * square wave density is averaged to get analog value
      - many uctlrs have PDM interfaces
      - need SW to filter (either in HW or SW)
      - pins: 3V3, GND, SEL, CLK, DAT
      - needs PDM interface on Raspi
    * Adafruit MEMS Microphone SPW2430
      - links
        * https://www.adafruit.com/product/2716
        * 100-10KHz
        * Vin: 3.3-5VDC, on-board 3V voltage regulator
        * has series 10uF cap on output
        * connect DC pin directly to uctrl
    * Adafruit I2S Microphone
      - links
        * https://www.adafruit.com/product/3421
        * https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/arduino-wiring-and-test
        * https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/raspberry-pi-wiring-test
      - SPH0645LM4H
        * 1.6-3.6V input (not 5V tolerant)
      - 50-15KHz
      - connect to uctrl I2S
      - pins: Clock, Data, Left-Right (Word Select) Clock)
        * SEL: Low=left channel, High=right channel, default low/left
        * LRCL: aka WS, high=right channel Tx, low=left channel Tx
        * DOUT: data output
        * BCLK: bit clock, 2-4MHz
        * GND: ground
        * 3V: 3V3
      - can select either Left or Right channel by grounding Select pin
        * other channel opposite Select and shared Clock, WS, and Data
      - Raspi mono mic
        * install
          - "sudo apt-get -y install git raspberrypi-kernel-headers"
          - "sudo git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git"
          - "sudo cd Raspberry-Pi-Installer-Scripts/i2s_mic_module"
          - "sudo make clean"
          - "sudo make"
          - "sudo make install"
          - "sudo echo 'snd-i2smic-rpi' > /etc/modules-load.d/snd-i2smic-rpi.conf"
          - "sudo echo 'options snd-i2smic-rpi rpi_platform_generation=2' > /etc/modprobe.d/snd-i2smic-rpi.conf"
          - "sudo sed -i -e 's/#dtparam=i2s/dtparam=i2s/g' /boot/config.txt"
        * manual load drivers
          - sudo modprobe snd-i2smic-rpi rpi_platform_generation=PI_SEL
            * PI_SEL: 0=Pi0, 1=Pi2_3, 2=Pi4
        * load drivers on startup
          - cd ~
          - sudo pip3 install --upgrade adafruit-python-shell
          - wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/i2smic.py
          - sudo python3 i2smic.py
        * connections
          - SEL: ground
          - BCLK: pin 12 (BCM 18)
          - DOUT: pin 20 (BCM 38)
          - LRCL: pin 35 (BCM 19)
        * test audio input
          - "arecord -l"
          - "arecord -D plughw:0 -c1 -r 48000 -f S32_LE -t wav -V mono -v file.wav"
        * add volume control
          - ~/.asoundrc
pcm.dmic_hw {
  type hw
  card sndrpii2scard
  channels 2
  format S32_LE
}
pcm.dmic_sv {
  type softvol
  slave.pcm dmic_hw
  control {
    name "Boost Capture Volume"
    card sndrpii2scard
  }
  min_dB -3.0
  max_dB 30.0
}
--------
pcm.device{
  type hw
  card sndrpii2scard
  format S32_LE
  rate 48000
}
pcm.mic_control {
  type  softvol
  slave.pcm device
  control {
    name "Boost Capture Volume"
    card sndrpii2scard
  }
  min_dB -3.0
  max_dB 30.0
}
pcm.mic_sv {
  type plug
  slave.pcm mic_control
}
pcm.!default{
  type plug
  slave.pcm mic_sv
}
        * volume control GUI
          - "alsamixer"
            * select I2S mic: "F6"
            * set recording volume: "F4" and arrow up/down
        * volume control
          - "arecord -D dmic_sv -c1 -r 48000 -f S32_LE -t wav -V mono -v <filename>.wav"
    * PUI Audio I2S Microphones
      - DMM-4026-B-I2S-EB-R
        * MEMS MIC EVAL BD -26DB 1.8VDC
        * Sensitivity: -26db
        * Freq Range: 20-20KHz
        * Vcc: 1.8-3.6V
        * Icc: 1mA
      - DMM-4026-B-I2S-R
        * MICROPHONE -26DB 1.8VDC
        * Sensitivity: -26db
        * Freq Range: 20-20KHz
        * Vcc: 1.5-3.6V
        * Icc: 0.82mA
  * I2S Microphones
    - Fermion
      * MEMS, 3.3V, I2S, SPL: 140dB, SNR: 59dB
    - MakerPortal
      ==> obsolete, out of production
      * INMP441
      * MEMS
      * Sensitivity: -26dB
      * Freq Range: 60-15KHz
      * Noise Floor: -87dB
      * Sample Rate: 44.1-48KHz
    - SPH0645LM4H
      * MEMS
      * Sensitivity: -26dB
      * Freq Range: 20-10KHz
      * SNR: 65dB
      * 1.62-3.6V @ 600uA
    - ICS-43434 TDK InvenSense
      * MEMS
      * Sensitivity: -26dB
      * Freq Range: 60-20KHz
      * SNR: 64dB
      * Noise Floor: -87dB
      * Vcc: 1.65-3.63V @ 550uA
    - ICS-43432 TDK InvenSense
      * same as ICS-43434 but lower power and smaller package
  - measurements
    * https://forum.edgeimpulse.com/t/different-sound-qualities-when-sampling-with-different-frequencies-and-microphones/6614
    * INMP441: very quiet and noisy
    * ICS-43434: better, but still distorted
    * ICS-43432: even better, but still noisy
    * PUI-DMM-4026-B: didn't work

## BirdPi Repos

* BirdPi
  - git@github.com:pddpauw/BirdPi.git
  - last updated four months ago
  - copy of  https://github.com/mcguirepr89/BirdNET-Pi/
  - works with Rpi5
  - improvements
    * disable Apache
    * enable Caddy as systemd service
    * updated requirement.txt file to tflite_runtime-2.14.0-cp311...
    * disable terminal (reenable in $HOME/views.php after install - line 264/265
  - use V2.4 model v2
    *  https://github.com/mcguirepr89/BirdNET-Pi/
  - RPi Bookworm
    * network managed by nmcli
    * examine state: 'nmcli con show'
    * hardcode network
      - sudo nmcli con mod "Wired connection 1" ipv4.method manual ipv4.addr 192.168.15.56/24
      - sudo nmcli con mod "Wired connection 1" ipv4.gateway 192.168.15.1
      - sudo nmcli con mod "Wired connection 1" ipv4.dns "8.8.8.8"
      - sudo nmcli con up "Wired connection 1"
  - installation
    * start with Bookworm 64b LITE
    * curl -s https://raw.githubusercontent.com/pddpauw/BirdPi/main/newinstaller.sh | bash
    * set model to V2.4 in web browser
    * use V2.4 Model V2
      - curl -s https://raw.githubusercontent.com/pddpauw/BirdPi/main/install_model_V2_4V2.sh | bash

* mcquirepr89
  - https://github.com/mcguirepr89/BirdNET-Pi.git
  - last updated a year ago
  - fork of kahst/BirdNET-Lite (Deprecated)
  - https://github.com/mcguirepr89/BirdNET-Pi
  - https://github.com/mcguirepr89/BirdNET-Pi/wiki

* Nachtzuster
  - git@github.com:Nachtzuster/BirdNET-Pi.git
  - last updated last month
  - forked from mcquirepr89
  - run 64b RaspiOS (Bookworm)
    * Lite is recommended, but works on Full as well

* notes
  - lineage: kahst -> mcquirepr89 -> {Nachtzuster | pddpauw/BirdPi}


