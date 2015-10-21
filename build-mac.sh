#!/bin/sh
export MACOSX_DEPLOYMENT_TARGET=10.7
export PYTHONPATH="/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages"

# for PyQt4 running on Qt5
export ORGPATH=$PATH
export PATH=/Users/luther/Qt5.4.2/5.4/clang_64/bin:$PATH

export DYLD_FRAMEWORK_PATH=/Users/luther//Qt5.4.2/5.4/clang_64/lib/

# translations
#pylupdate5 artisan.pro # we need to use pylupdate4 for Qt4 and pylupdate5 for Qt5
pylupdate4 artisan.pro
lrelease -verbose artisan.pro

# distribution
rm -rf build dist
python setup-mac.py py2app


# recreate the translations with PyQt4/Qt4 for the Windows releases that are behind


export PATH=$ORGPATH
lrelease -verbose artisan.pro
