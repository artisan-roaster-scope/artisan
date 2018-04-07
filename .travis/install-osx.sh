#!/bin/sh

set -ex
brew upgrade python
brew install p7zip qt
pip3 install -r src/requirements.txt
pip3 install -r src/requirements-${TRAVIS_OS_NAME}.txt
curl -L -O https://www.phidgets.com/downloads/phidget22/libraries/any/Phidget22Python.zip
unzip -q Phidget22Python.zip
(cd Phidget22Python && python3 setup.py install)
curl -L -O https://kent.dl.sourceforge.net/project/snap7/1.4.2/snap7-full-1.4.2.7z
7z x -bd snap7-full-1.4.2.7z
(cd snap7-full-1.4.2/build/osx && make -f x86_64_osx.mk all && sudo make -f x86_64_osx.mk LibInstall=/usr/local/lib install)
curl -L -O https://www.phidgets.com/downloads/phidget22/libraries/macos/Phidget22.dmg
hdiutil attach Phidget22.dmg
sudo installer -pkg /Volumes/Phidgets22/Phidgets.pkg -target /
sudo rm -rf /usr/local/lib/python3.6/site-packages/matplotlib/mpl-data/sample_data
