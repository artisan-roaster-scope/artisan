#!/bin/sh
export MACOSX_DEPLOYMENT_TARGET=10.5
export PYTHONPATH="/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages"

# translations
pylupdate4 artisan.pro
lrelease -verbose artisan.pro

# distribution
rm -rf build dist
python setup-mac.py py2app
