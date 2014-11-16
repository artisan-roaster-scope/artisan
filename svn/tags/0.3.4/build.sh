#!/bin/sh
export MACOSX_DEPLOYMENT_TARGET=10.5
export PYTHONPATH="/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/site-packages"
rm -rf build dist
python setup-mac.py py2app
