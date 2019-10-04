#!/bin/sh

set -ex

version=22
if [ "$ARTISAN_OS" = "rpi" ]; then
    SUDO="sudo"
else
    SUDO=""
fi
if [ "$ARTISAN_OS" = "linux" ] || [ "$ARTISAN_OS" = "rpi" ]; then
    curl -L -O https://www.phidgets.com/downloads/phidget22/libraries/linux/libphidget${version}.tar.gz
    tar -xzf libphidget${version}.tar.gz
    (cd libphidget${version}-* && ./configure --prefix=/usr && make -j4 && sudo make install && cp plat/linux/udev/* ../src/debian/etc/udev/rules.d)
elif [ "$ARTISAN_OS" = "osx" ]; then
    curl -L -O https://www.phidgets.com/downloads/phidget${version}/libraries/macos/Phidget${version}.dmg
    hdiutil attach Phidget${version}.dmg
    sudo installer -pkg /Volumes/Phidget${version}/Phidgets.pkg -target /
fi

# Phidget Python module now installed via pip
# curl -L -O https://www.phidgets.com/downloads/phidget${version}/libraries/any/Phidget${version}Python.zip
# unzip -q Phidget${version}Python.zip
# (cd Phidget${version}Python && $SUDO python3 setup.py install)
