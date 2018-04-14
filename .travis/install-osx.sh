#!/bin/sh

set -ex
brew upgrade python
brew install p7zip
#curl -L -O https://download.qt.io/archive/qt/5.10/5.10.0/single/qt-everywhere-src-5.10.0.tar.xz
#tar xzf qt-everywhere-src-5.10.0.tar.xz
#cd qt-everywhere-src-5.10.0
#./configure -opensource -confirm-license 
#make -j4
#make install
#cd ..

pip3 install -r src/requirements.txt
pip3 install -r src/requirements-${TRAVIS_OS_NAME}.txt
sudo rm -rf /usr/local/lib/python3.6/site-packages/matplotlib/mpl-data/sample_data

.travis/install-phidgets.sh
.travis/install-snap7.sh
.travis/install-pymodbus.sh
