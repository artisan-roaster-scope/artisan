#!/bin/sh
export MACOSX_DEPLOYMENT_TARGET=10.11
export PYTHON=/Library/Frameworks/Python.framework/Versions/2.7
export PYTHONPATH=$PYTHON/lib/python2.7/site-packages

export PATH=$PYTHON/bin:$PYTHON:/lib:$PATH

export QT_PATH=~/Qt5.10.0/5.10.0/clang_64
export PATH=$QT_PATH/bin:$QT_PATH/lib:$PATH
export DYLD_FRAMEWORK_PATH=$QT_PATH/lib

# translations
$PYTHON/bin/pylupdate5 artisan.pro # we need to use pylupdate4 for Qt4 and pylupdate5 for Qt5
#$PYTHON/bin/pylupdate4 artisan.pro
$QT_PATH/bin/lrelease -verbose artisan.pro

# distribution
rm -rf build dist
$PYTHON/bin/python setup-mac.py py2app
