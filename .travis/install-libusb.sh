#!/bin/sh

set -ex

# For now, this only applies to Linux
if [ "$ARTISAN_OS" != "linux" ]; then
   exit 0
fi

sudo apt-get remove libusb-1.0-0
curl -L -O https://kent.dl.sourceforge.net/project/libusb/libusb-1.0/libusb-1.0.21/libusb-1.0.21.tar.bz2
tar xjf libusb-1.0.21.tar.bz2
(cd libusb-1.0.21 && ./configure --prefix=/usr && make && sudo make install)
