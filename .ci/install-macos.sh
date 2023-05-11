#!/bin/sh

#set -ex # increased logging
set -e # reduced logging

#.ci/silence.sh brew update # this seems to help to work around some homebrew issues; and fails on others

# upgrade Python version when PYUPGRADE_V exists and has a value
if [ -n "${PYUPGRADE_V:-}" ]; then
    # first deactivate current venv
    source ${VIRTUAL_ENV}/bin/activate
    deactivate
    # brew update Python
    brew update && brew upgrade python
    # relink Python
    brew unlink python@${PYTHON_V} && brew link --force python@${PYTHON_V}
    # add path
    export PATH="$(brew --prefix)/Cellar/python@${PYTHON_V}/${PYUPGRADE_V}/bin:${PATH}"
    # create new venv
    python3 -m venv /Users/appveyor/venv${PYUPGRADE_V}
    source /Users/appveyor/venv${PYUPGRADE_V}/bin/activate
    # update symbolic link to point to our new venv
    ln -vfns /Users/appveyor/venv${PYUPGRADE_V} /Users/appveyor/venv${PYTHON_V}
    export PATH=/Users/appveyor/venv${PYUPGRADE_V}/bin:${PATH} # not exported?
fi 

hash -r
which python3
python3 --version

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
