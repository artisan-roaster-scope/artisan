#!/bin/sh

#set -ex
set -e # reduced logging

cd src
./build-mac3.sh
# the following test results in
# in Unable to revert mtime: /Library/Fonts
#python3 artisan.py
cd ..
