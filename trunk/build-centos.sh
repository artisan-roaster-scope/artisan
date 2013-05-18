#!/bin/sh

# translations
pylupdate4 artisan.pro
lrelease -verbose artisan.pro

# distribution
rm -rf dist
bbfreeze artisan.py
cp -L /usr/lib/libz.so dist
cp -L /usr/lib/libxml2.so dist
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
mkdir dist/Resources
mkdir dist/Resources/qt_plugins
mkdir dist/Resources/qt_plugins/imageformats
mkdir dist/Resources/qt_plugins/iconengines
cp /usr/local/Trolltech/Qt-4.8.4/plugins/imageformats/libqsvg.so dist/Resources/qt_plugins/imageformats
cp /usr/local/Trolltech/Qt-4.8.4/plugins/imageformats/libqgif.so dist/Resources/qt_plugins/imageformats
cp /usr/local/Trolltech/Qt-4.8.4/plugins/imageformats/libqjpeg.so dist/Resources/qt_plugins/imageformats
cp /usr/local/Trolltech/Qt-4.8.4/plugins/imageformats/libqtiff.so dist/Resources/qt_plugins/imageformats
cp /usr/local/Trolltech/Qt-4.8.4/plugins/iconengines/libqsvgicon.so dist/Resources/qt_plugins/iconengines
cp qt.conf dist
mkdir dist/translations
cp translations/*.qm dist/translations
cp /usr/local/Trolltech/Qt-4.8.4/translations/qt_de.qm dist/translations
cp /usr/local/Trolltech/Qt-4.8.4/translations/qt_es.qm dist/translations
cp /usr/local/Trolltech/Qt-4.8.4/translations/qt_fr.qm dist/translations
cp /usr/local/Trolltech/Qt-4.8.4/translations/qt_sv.qm dist/translations
cp /usr/local/Trolltech/Qt-4.8.4/translations/qt_zh_CN.qm dist/translations
cp /usr/local/Trolltech/Qt-4.8.4/translations/qt_zh_TW.qm dist/translations
cp /usr/local/Trolltech/Qt-4.8.4/translations/qt_ko.qm dist/translations
cp /usr/local/Trolltech/Qt-4.8.4/translations/qt_pt.qm dist/translations
cp /usr/local/Trolltech/Qt-4.8.4/translations/qt_ru.qm dist/translations
cp /usr/local/Trolltech/Qt-4.8.4/translations/qt_ar.qm dist/translations
cp /usr/local/Trolltech/Qt-4.8.4/translations/qt_ja.qm dist/translations
tar -cf dist-centos.tar dist