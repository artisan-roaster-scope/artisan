#!/bin/sh
# ABOUT
# CI install shell script for Artisan Linux builds
#
# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# AUTHOR
# Dave Baxter, Marko Luther 2023

set -ex
hash -r
uname -srv
which python3
python3 --version
sudo apt-get update -y -q --allow-releaseinfo-change
sudo apt-get install -y -q ruby-dev build-essential p7zip-full rpm gdb libudev-dev libfuse2
sudo apt-get install -y -q fakeroot

# add libs not installed by default on Qt5.15/Qt6 any longer
sudo apt-get install -y -q libdbus-1-3 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0 libxcb-cursor0

gem install dotenv -v ${DOTENV_VER}
gem install fpm # Linux build fails using 1.13.0
pip install --upgrade pip
pip install -r src/requirements.txt | sed '/^Ignoring/d'

.ci/install-libusb.sh

# show set of libraries are installed
echo "**** pip freeze ****"
pip freeze
