#!/bin/sh
export MACOSX_DEPLOYMENT_TARGET=10.10
export PYTHON=/Library/Frameworks/Python.framework/Versions/3.5

export PYTHONPATH=$PYTHON/lib/python3.5/site-packages

export PATH=$PYTHON/bin:$PYTHON:/lib:$PATH

export QT_PATH=~/Qt5.10.1/5.10.1/clang_64
export PATH=$QT_PATH/bin:$QT_PATH/lib:$PATH
export DYLD_FRAMEWORK_PATH=$QT_PATH/lib

# translations
$PYTHON/bin/pylupdate5 artisan.pro
$QT_PATH/bin/lrelease -verbose artisan.pro

# distribution
rm -rf build dist
$PYTHON/bin/python3.5 setup-mac35.py py2app
