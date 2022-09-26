#!/bin/sh

#set -ex # increased logging
set -e # reduced logging

#.ci/slience.sh brew update # this seems to help to work around some homebrew issues; and fails on others

#------------
# Python 3.7.5 is installed by default
# to update use either:
#brew upgrade python
# or, to avoid issues with brew auto updates by deactivating them,
#HOMEBREW_NO_AUTO_UPDATE=1 brew install python

#brew uninstall numpy gdal postgis
#brew unlink python@2
#brew unlink python
#brew upgrade python

#brew install python@3.8
#brew link --force --overwrite python@3.8


# following https://stackoverflow.com/questions/51125013/how-can-i-install-a-previous-version-of-python-3-in-macos-using-homebrew/51125014#51125014
# to install Python 3.6.5
#brew remove --ignore-dependencies python 1>/dev/null 2>&1
#brew install https://raw.githubusercontent.com/Homebrew/homebrew-core/f2a764ef944b1080be64bd88dca9a1d80130c558/Formula/python.rb 1>/dev/null 2>&1
#------------

## upgrade python from 3.9 to 3.10
# 3.10.2 now already installed on AppVeyor
#brew install python@3.10
#brew unlink python@3.9
#brew link --force python@3.10
export PATH="/usr/local/opt/python@${PYTHON_V}/bin:$PATH"

hash -r
which python3
python3 --version


# to work around a wget open ssl issue: dyld: Library not loaded: /usr/local/opt/openssl/lib/libssl.1.0.0.dylib
# however for now we settled to use curl instead to download the upload script
#brew uninstall wget
#brew install wget


#brew install p7zip

python3 -m pip install --upgrade pip
# to allow the installation of numpy >v1.15.4, avoiding the Permission denied: '/usr/local/bin/f2py' error, we run the following pip3 installs under sudo:
# (an alternative could be to use pip install --user ..)
# the lxml binaries are compiled with an SDK older than the 10.9 SDK which breaks the notarization
# thus we force the compilation from source
sudo -H python3 -m pip install --no-binary lxml lxml==4.9.1 #4.7.1
sudo -H python3 -m pip install -r src/requirements.txt
sudo -H python3 -m pip install -r src/requirements-${ARTISAN_OS}.txt

# copy the snap7 binary installed by pip
cp -f ${PYTHONPATH}/site-packages/snap7/lib/libsnap7.dylib /usr/local/lib

# use a custom py2app v0.23 with apptemplate main-x86_64 build for
# target 10.13 using MacOSX10.15.sdk build on macOS 10.15 to add dark-mode support to builds
#sudo -H python3 -m pip install .ci/py2app-0.23-py2.py3-none-any.whl
# with PyQt6 we need to use 0.26.1 which duplicates the Qt installation hopefully resolved in the next version

# not needed any longer with py2app 0.28.2:
#sudo -H python3 -m pip install .ci/py2app-0.27-py2.py3-none-any.whl


sudo rm -rf /usr/local/opt/python@3.9/lib/python3.9/site-packages/matplotlib/mpl-data/sample_data
sudo rm -rf /usr/local/opt/python@3.9/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/matplotlib/mpl-data/sample_data

sudo rm -rf /usr/local/opt/python@3.10/lib/python3.9/site-packages/matplotlib/mpl-data/sample_data
sudo rm -rf /usr/local/opt/python@3.10/Frameworks/Python.framework/Versions/3.10/lib/python3.9/site-packages/matplotlib/mpl-data/sample_data

#.ci/install-phidgets.sh # now installed via pip
#.ci/install-snap7.sh
