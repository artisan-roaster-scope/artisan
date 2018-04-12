#!/bin/sh

set -ex
cd src
./build-mac3.sh
python3 artisan.py
cd ..
