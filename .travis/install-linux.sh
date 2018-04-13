#!/bin/sh

set -ex
sudo apt-get update
sudo apt-get install ruby-dev build-essential p7zip-full rpm gdb libudev-dev qt5-default
gem install fpm
pip3 install -r src/requirements.txt
pip3 install -r src/requirements-${TRAVIS_OS_NAME}.txt

.travis/install-libusb.sh
.travis/install-phidgets.sh
.travis/install-snap7.sh
.travis/install-pymodbus.sh
