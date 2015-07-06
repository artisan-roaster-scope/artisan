#!/bin/sh
export MACOSX_DEPLOYMENT_TARGET=10.6
export PYTHONPATH="/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages"

export PATH=/Library/Frameworks/Python.framework/Versions/3.4/bin/:$PATH

# for PyQt4 running on Qt5
export ORGPATH=$PATH
export PATH=/Users/luther/Qt5.4.2/5.4/clang_64/bin:$PATH

# translations
pylupdate5 artisan.pro
lrelease -verbose artisan.pro

# distribution
rm -rf build dist
python3.4 setup-mac3.py py2app


# recreate the translations with PyQt4/Qt4 for the Windows releases that are behind

$PATH = ORGPATH
lrelease -verbose artisan.pro