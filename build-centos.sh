#!/bin/sh

# translations
pylupdate4 artisan.pro
lrelease -verbose artisan.pro

# distribution
rm -rf dist
bbfreeze artisan.py
cp -L /usr/lib/libicudata.so.42 dist
cp -L /usr/lib/libicuuc.so.42 dist
cp -L /usr/lib/libicui18n.so.42 dist
cp -L /usr/lib/gnome-keyring/gnome-keyring-pkcs11.so dist
cp -R /usr/local/lib/python2.7/site-packages/matplotlib/mpl-data/ dist
cp artisan-alog.xml dist
cp artisan-alrm.xml dist
cp artisan-apal.xml dist
cp -R icons dist
cp -R Wheels dist
cp README.txt dist
cp LICENSE.txt dist
mkdir dist/translations
cp translations/*.qm dist/translations
tar -cf dist-centos.tar dist