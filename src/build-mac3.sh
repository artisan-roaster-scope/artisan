#!/bin/sh

set -ex


if [ ! -z $TRAVIS ]; then
    export PYTHON=/usr/local
    export PYTHONPATH=$PYTHON/lib/python3.6
    export PYTHON_V=3.6
    export QT_PATH=${PYTHONPATH}/site-packages/PyQt5/Qt
    export QT_SRC_PATH=${QT_PATH}
    export MACOSX_DEPLOYMENT_TARGET=10.13
else
    export PYTHON=/Library/Frameworks/Python.framework/Versions/3.6
    export PYTHONPATH=$PYTHON/lib/python3.6
    export PYTHON_V=3.6
    export QT_PATH=${PYTHONPATH}/site-packages/PyQt5/Qt
    export QT_SRC_PATH=~/Qt5.11.1/5.11.1/clang_64
    export MACOSX_DEPLOYMENT_TARGET=10.13
    export DYLD_LIBRARY_PATH=$PYTHON/lib:$DYLD_LIBRARY_PATH
fi

export PATH=$PYTHON/bin:$PYTHON/lib:$PATH
export PATH=$QT_PATH/bin:$QT_PATH/lib:$PATH
export DYLD_FRAMEWORK_PATH=$QT_PATH/lib

# translations
$PYTHON/bin/pylupdate5 artisan.pro
$QT_SRC_PATH/bin/lrelease -verbose artisan.pro || true

# distribution
rm -rf build dist
sleep .3 # sometimes it takes a little for dist to get really empty
$PYTHON/bin/python$PYTHON_V setup-mac3.py py2app
