#!/bin/sh
export MACOSX_DEPLOYMENT_TARGET=10.7
export PYTHONPATH="/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages"

export PATH=/Library/Frameworks/Python.framework/Versions/3.4/bin/:$PATH

# for PyQt4 running on Qt5
export ORGPATH=$PATH

# add the following two lines to your ~/.bash_profile (without the commenting)
#  QT_PATH="/Users/<shortname>/Qt5.4.2/5.4/clang_64"
#  export QT_PATH
export PATH=$QT_PATH/bin:$QT_PATH/lib:$PATH

export DYLD_FRAMEWORK_PATH=$QT_PATH/lib

# translations
$PYTHON/bin/pylupdate5 artisan.pro
$QT_PATH/bin/lrelease -verbose artisan.pro

# distribution
rm -rf build dist
python3.4 setup-mac3.py py2app


# recreate the translations with PyQt4/Qt4 for the Windows releases that are behind

export PATH=$ORGPATH
$QT_PATH/bin/lrelease -verbose artisan.pro