#!/bin/sh

set -ex # reduced logging
#set -e

cd src
./build-mac3.sh
# the following test results in
# in Unable to revert mtime: /Library/Fonts
python3 artisan.py
cd ..
