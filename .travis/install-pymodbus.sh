#!/bin/sh

set -ex

git clone -b python3 https://github.com/riptideio/pymodbus.git
(cd pymodbus && patch -p0 < ../src/patches/pymodbus.patch && python3 setup.py install)
