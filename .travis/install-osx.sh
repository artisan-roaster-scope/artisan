#!/bin/sh

set -ex # reduced logging
#set -e

# avoid issues with brew auto updates
HOMEBREW_NO_AUTO_UPDATE=1

#brew update # this seems to help to work around some homebrew issues; and fails on others

# for Python 3.7:
brew upgrade python

# following https://stackoverflow.com/questions/51125013/how-can-i-install-a-previous-version-of-python-3-in-macos-using-homebrew/51125014#51125014
# to install Python 3.6.5
#brew remove --ignore-dependencies python 1>/dev/null 2>&1
#brew install https://raw.githubusercontent.com/Homebrew/homebrew-core/f2a764ef944b1080be64bd88dca9a1d80130c558/Formula/python.rb 1>/dev/null 2>&1



brew install p7zip

pip3 install --upgrade pip
# to allow the installation of numpy >v1.15.4, avoiding the Permission denied: '/usr/local/bin/f2py' error, we run the following pip3 installs under sudo:
# (an alternative could be to use pip install --user ..)
sudo pip3 install -r src/requirements.txt
sudo pip3 install -r src/requirements-${TRAVIS_OS_NAME}.txt
sudo rm -rf /usr/local/lib/python3.6/site-packages/matplotlib/mpl-data/sample_data

.travis/install-phidgets.sh
.travis/install-snap7.sh
