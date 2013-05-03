#!/bin/sh

# translations
pylupdate4 artisan.pro
lrelease -verbose artisan.pro

# distribution
rm -rf dist
bbfreeze artisan.py
cp -R /usr/local/lib/python2.7/dist-packages/matplotlib/mpl-data/ dist
cp -R Wheels dist
cp README.txt dist
cp LICENSE.txt dist
mkdir dist/translations
cp translations/*.qm dist/translations
tar -cf dist-ubuntu.tar dist