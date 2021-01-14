#!/bin/sh

set -ex

if [ "$ARTISAN_OS" = "rpi" ]; then
    SUDO="sudo"
else
    SUDO=""
fi

git clone -b python3 https://github.com/riptideio/pymodbus.git
(cd pymodbus && patch -p0 < ../src/patches/pymodbus.patch && $SUDO python3 setup.py install)
