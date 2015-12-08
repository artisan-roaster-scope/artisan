#!/bin/sh
export MACOSX_DEPLOYMENT_TARGET=10.7
export PYTHON="/Library/Frameworks/Python.framework/Versions/2.7"
export PYTHONPATH=$PYTHON/"/lib/python2.7/site-packages"

# for PyQt4 running on Qt5
export ORGPATH=$PATH

# add the following two lines to your ~/.bash_profile (without the commenting)
#  QT_PATH="/Users/<shortname>/Qt5.4.2/5.4/clang_64"
#  export QT_PATH
export PATH=$QT_PATH/bin:$PATH

export DYLD_FRAMEWORK_PATH=$QT_PATH/lib

# translations
$PYTHON/bin/pylupdate5 artisan.pro # we need to use pylupdate4 for Qt4 and pylupdate5 for Qt5
#$PYTHON/bin/pylupdate4 artisan.pro
$QT_PATH/bin/lrelease -verbose artisan.pro

# distribution
rm -rf build dist
$PYTHON/bin/python setup-mac.py py2app


# recreate the translations with PyQt4/Qt4 for the Windows releases that are behind


export PATH=$ORGPATH
$QT_PATH/bin/lrelease -verbose artisan.pro
