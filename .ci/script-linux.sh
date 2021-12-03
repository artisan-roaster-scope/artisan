#!/bin/sh

#set -ex
set -e # reduced logging

cd src
./build-linux.sh && ./build-linux-pkg.sh
#xvfb-run --server-args="-screen 0 1024x768x24" python artisan.py
cd ..
