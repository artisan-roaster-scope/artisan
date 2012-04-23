#!/bin/sh
export MACOSX_DEPLOYMENT_TARGET=10.6
export PYTHONPATH="/Library/Frameworks/Python.framework/Versions/3.2/lib/python3.2/site-packages"

# translations
pylupdate4 artisan.pro
lrelease -verbose artisan.pro

# distribution
rm -rf build dist
python3.2 setup-mac3.py py2app
