#!/bin/bash
#
# Script to get the latest files for birdpi mqttd from github


#wget -r -np -nH --cut-dirs=1 -l 5 https://raw.githubusercontent.com/jduanen/Birds/tree/main/mqtt/
#wget -r -np -nH --cut-dirs=3 \
#  -A '*.py,*.sh,*.conf,*.txt,*.md,*.service' \
#  -R 'index.html*,*.png,*.jpg,*.css,*.js' \
#  -l 5 \
#  https://github.com/jduanen/Birds/tree/main/mqtt/

## see available files
#curl -s https://api.github.com/repos/jduanen/Birds/contents/mqtt/ | jq '.[].name'


cd ${HOME}/Code
git clone --no-checkout --filter=blob:none --sparse https://github.com/jduanen/Birds.git

cd ./Code/Birds
git sparse-checkout set mqtt/
git checkout main
rm ./BirdPiSensor.png ./BirdSensor.code-workspace ./LICENSE 
