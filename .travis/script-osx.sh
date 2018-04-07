#!/bin/sh

set -ex
cd src
./build-mac35.sh
python3 artisan.py
cd ..
