#!/bin/sh

#set -ex # increased logging
set -e # reduced logging

#.ci/silence.sh brew update # this seems to help to work around some homebrew issues; and fails on others

## upgrade Python from 3.11.0 to 3.11.3
# first deactivate current venv
source $VIRTUAL_ENV/bin/activate
deactivate
# brew update Python
brew update && brew upgrade python
# relink Python
brew unlink python@3.11 && brew link --force python@3.11
# add path
export PATH="$(brew --prefix)/Cellar/python@3.11/3.11.3/bin:$PATH"
# create new venv
python3 -m venv /Users/appveyor/venv3.11.3
source /Users/appveyor/venv3.11.3/bin/activate
# update symbolic link venv3.11 to point to our new venv3.11.3
ln -vfns /Users/appveyor/venv3.11.3 /Users/appveyor/venv3.11

# to work around a wget open ssl issue: dyld: Library not loaded: /usr/local/opt/openssl/lib/libssl.1.0.0.dylib
# however for now we settled to use curl instead to download the upload script
#brew uninstall wget
#brew install wget


#brew install p7zip

python -m pip install --upgrade pip
sudo -H python -m pip install --root-user-action=ignore -r src/requirements.txt
sudo -H python -m pip install --root-user-action=ignore -r src/requirements-${ARTISAN_OS}.txt

# copy the snap7 binary installed by pip
cp -f ${PYTHONSITEPKGS}/snap7/lib/libsnap7.dylib /usr/local/lib
