#!/bin/sh

#set -ex
set -e

cd src
./build-mac3.sh
python3 artisan.py
cd ..
