#!/bin/sh

set -ex
sudo apt-get update
sudo apt-get install ruby-dev build-essential p7zip-full rpm gdb libudev-dev qt5-default
sudo apt-get remove libusb-1.0-0
curl -L -O https://kent.dl.sourceforge.net/project/libusb/libusb-1.0/libusb-1.0.21/libusb-1.0.21.tar.bz2
tar xjf libusb-1.0.21.tar.bz2
(cd libusb-1.0.21 && ./configure --prefix=/usr && make && sudo make install)
curl -L -O https://www.phidgets.com/downloads/phidget22/libraries/linux/libphidget22.tar.gz
tar -xzf libphidget22.tar.gz
(cd libphidget22-* && ./configure --prefix=/usr && make && sudo make install && cp plat/linux/udev/* ../src/debian/etc/udev/rules.d)
gem install fpm
pip3 install -r src/requirements.txt
pip3 install -r src/requirements-${TRAVIS_OS_NAME}.txt
curl -L -O https://www.phidgets.com/downloads/phidget22/libraries/any/Phidget22Python.zip
unzip -q Phidget22Python.zip
(cd Phidget22Python && python3 setup.py install)
curl -L -O https://kent.dl.sourceforge.net/project/snap7/1.4.2/snap7-full-1.4.2.7z
7z x -bd snap7-full-1.4.2.7z
(cd snap7-full-1.4.2/build/unix && make -f x86_64_linux.mk all && sudo make -f x86_64_linux.mk install)

