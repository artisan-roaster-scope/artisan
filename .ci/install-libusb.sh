#!/bin/sh

set -ex

# For now, this only applies to Linux
if [ "$ARTISAN_OS" != "linux" ]; then
   exit 0
fi

sudo apt-get remove -y libusb-1.0-0
# we use the -k option in the following as the SSL certificate on sourceforge does not validate

##curl -k -L -O https://kent.dl.sourceforge.net/project/libusb/libusb-1.0/libusb-1.0.21/libusb-1.0.21.tar.bz2
##tar xjf libusb-1.0.21.tar.bz2
##(cd libusb-1.0.21 && ./configure --prefix=/usr && make -j4 && sudo make install)

##curl -k -L -O https://github.com/libusb/libusb/releases/download/v1.0.23/libusb-1.0.23.tar.bz2
##tar xjf libusb-1.0.23.tar.bz2
##(cd libusb-1.0.23 && ./configure --prefix=/usr && make -j4 && sudo make install)

##curl -k -L -O https://github.com/libusb/libusb/releases/download/v1.0.24/libusb-1.0.24.tar.bz2
##tar xjf libusb-1.0.24.tar.bz2
##(cd libusb-1.0.24 && ./configure --prefix=/usr && make -j4 && sudo make install)

#curl -k -L -O https://github.com/libusb/libusb/releases/download/v1.0.25/libusb-1.0.25.tar.bz2
curl -k -L -O https://github.com/libusb/libusb/releases/download/v${LIBUSB_VER}/libusb-${LIBUSB_VER}.tar.bz2
tar xjf libusb-${LIBUSB_VER}.tar.bz2
(cd libusb-${LIBUSB_VER} && ./configure --prefix=/usr && make -j4 && sudo make install)
