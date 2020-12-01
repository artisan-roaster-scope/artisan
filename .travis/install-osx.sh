#!/bin/sh

set -ex # reduced logging
#set -e # increased logging

.travis/slience.sh brew update # this seems to help to work around some homebrew issues; and fails on others


# Python 3.7.5 is installed by default on image xcode10.1
# to update use either:
#brew upgrade python
# or, to avoid issues with brew auto updates by deactivating them,
#HOMEBREW_NO_AUTO_UPDATE=1 brew install python

brew uninstall numpy gdal postgis
brew unlink python@2
##brew upgrade python

# a (slow) way to upgrade to Python 3.8
#brew unlink python
#brew install python@3.8
#brew link --force --overwrite python@3.8

hash -r
which python3
python3 --version

# following https://stackoverflow.com/questions/51125013/how-can-i-install-a-previous-version-of-python-3-in-macos-using-homebrew/51125014#51125014
# to install Python 3.6.5
#brew remove --ignore-dependencies python 1>/dev/null 2>&1
#brew install https://raw.githubusercontent.com/Homebrew/homebrew-core/f2a764ef944b1080be64bd88dca9a1d80130c558/Formula/python.rb 1>/dev/null 2>&1

# to work around a wget open ssl issue: dyld: Library not loaded: /usr/local/opt/openssl/lib/libssl.1.0.0.dylib
# however for now we settled to use curl instead to download the upload script
#brew uninstall wget
#brew install wget


brew install p7zip

python3 -m pip install --upgrade pip
# to allow the installation of numpy >v1.15.4, avoiding the Permission denied: '/usr/local/bin/f2py' error, we run the following pip3 installs under sudo:
# (an alternative could be to use pip install --user ..)
# the lxml binaries are compiled with an SDK older than the 10.9 SDK which breaks the notarization
# thus we force the compilation from source
sudo -H python3 -m pip install --no-binary lxml lxml==4.5.1
sudo -H python3 -m pip install -r src/requirements.txt
# use a custom py2app v0.21 (Python3.8) with apptemplate main-x86_64 build for 
# target 10.13 using MacOSX10.15.sdk build on macOS 10.15 to add dark-mode support to builds
#sudo -H python3 -m pip install .travis/py2app-0.21-py38-none-any.whl
sudo -H python3 -m pip install .travis/py2app-0.22-py2.py3-none-any.whl
sudo -H python3 -m pip install -r src/requirements-${TRAVIS_OS_NAME}.txt
#sudo rm -rf /usr/local/lib/python3.7/site-packages/matplotlib/mpl-data/sample_data
sudo rm -rf /usr/local/opt/python@3.8/lib/python3.8/site-packages/matplotlib/mpl-data/sample_data
sudo rm -rf /usr/local/opt/python@3.8/Frameworks/Python.framework/Versions/3.8/lib/python3.8/site-packages/matplotlib/mpl-data/sample_data

#.travis/install-phidgets.sh # now installed via pip
.travis/install-snap7.sh
