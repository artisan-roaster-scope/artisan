#!/bin/sh

set -ex
sudo apt-get update
sudo apt-get install ruby-dev build-essential p7zip-full rpm gdb libudev-dev qt5-default

# add libs not installed by default on Qt5.15 any longer
sudo apt-get install -y libdbus-1-3 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0

gem install fpm
pip3 install --upgrade pip
pip3 install -r src/requirements.txt
pip3 install -r src/requirements-${TRAVIS_OS_NAME}.txt

.travis/install-libusb.sh
.travis/install-phidgets.sh
.travis/install-snap7.sh
