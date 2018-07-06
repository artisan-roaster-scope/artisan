#!/bin/sh

set -ex
#brew upgrade python # this installs now Python3.7 which breaks libs
# following https://stackoverflow.com/questions/51125013/how-can-i-install-a-previous-version-of-python-3-in-macos-using-homebrew/51125014#51125014
# to install Python 3.6.5
brew remove python
brew install https://raw.githubusercontent.com/Homebrew/homebrew-core/f2a764ef944b1080be64bd88dca9a1d80130c558/Formula/python.rb
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
