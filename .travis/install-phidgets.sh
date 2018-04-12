#!/bin/sh

set -ex

version=22
if [ "$ARTISAN_OS" = "linux" ]; then
    curl -L -O https://www.phidgets.com/downloads/phidget22/libraries/linux/libphidget${version}.tar.gz
    tar -xzf libphidget${version}.tar.gz
    (cd libphidget${version}-* && ./configure --prefix=/usr && make && sudo make install && cp plat/linux/udev/* ../src/debian/etc/udev/rules.d)
elif [ "$ARTISAN_OS" = "osx" ]; then
    curl -L -O https://www.phidgets.com/downloads/phidget22/libraries/macos/Phidget${version}.dmg
    hdiutil attach Phidget${version}.dmg
    sudo installer -pkg /Volumes/Phidgets${version}/Phidgets.pkg -target /
fi
curl -L -O https://www.phidgets.com/downloads/phidget${version}/libraries/any/Phidget${version}Python.zip
unzip -q Phidget${version}Python.zip
(cd Phidget${version}Python && python3 setup.py install)
