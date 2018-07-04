#!/bin/sh

set -ex
#ML: brew upgrade python installs now python3.7 which fails in numpy/scipy => commented
#brew upgrade python
#ML: force the installation of Python 3.5.6 instead
brew update
brew upgrade pyenv
pyenv install 3.6.5
pyenv local 3.6.5
export PATH="/shims:$PATH"
eval "$(pyenv init -)"
#
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
