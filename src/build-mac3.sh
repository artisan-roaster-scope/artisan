#!/bin/sh

set -ex


if [ ! -z $TRAVIS ]; then
    export PYTHON=/usr/local
    export PYTHONPATH=$PYTHON/lib/python3.6
    export PYTHON_V=3.6
    export QT_PATH=`echo /usr/local/Cellar/qt/*`
    export MACOSX_DEPLOYMENT_TARGET=10.13
else
    export PYTHON=/Library/Frameworks/Python.framework/Versions/3.6
    export PYTHONPATH=$PYTHON/lib/python3.6
    export PYTHON_V=3.6
    export QT_PATH=~/Qt5.10.0/5.10.0/clang_64
    export MACOSX_DEPLOYMENT_TARGET=10.13
fi

export PATH=$PYTHON/bin:$PYTHON:/lib:$PATH
export PATH=$QT_PATH/bin:$QT_PATH/lib:$PATH
export DYLD_FRAMEWORK_PATH=$QT_PATH/lib

# translations
$PYTHON/bin/pylupdate5 artisan.pro
$QT_PATH/bin/lrelease -verbose artisan.pro

# distribution
rm -rf build dist
sleep .3 # sometimes it takes a little for dist to get really empty
$PYTHON/bin/python$PYTHON_V setup-mac3.py py2app
