#!/bin/sh
export MACOSX_DEPLOYMENT_TARGET=10.6
export PYTHONPATH="/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages"

export PATH=/Library/Frameworks/Python.framework/Versions/3.4/bin/:$PATH

# translations
pylupdate4 artisan.pro
lrelease -verbose artisan.pro

# distribution
rm -rf build dist
python3.4 setup-mac3.py py2app
