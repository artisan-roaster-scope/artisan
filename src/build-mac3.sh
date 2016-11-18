#!/bin/sh
export MACOSX_DEPLOYMENT_TARGET=10.7
export PYTHON=/Library/Frameworks/Python.framework/Versions/3.4
export PYTHONPATH="/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages"

export PATH=$PYTHON/bin:$PYTHON:/lib:$PATH

export QT_PATH=~/Qt5.6.2/5.6/clang_64
export PATH=$QT_PATH/bin:$QT_PATH/lib:$PATH
export DYLD_FRAMEWORK_PATH=$QT_PATH/lib

# translations
$PYTHON/bin/pylupdate5 artisan.pro
$QT_PATH/bin/lrelease -verbose artisan.pro

# distribution
rm -rf build dist
$PYTHON/bin/python3.4 setup-mac3.py py2app

