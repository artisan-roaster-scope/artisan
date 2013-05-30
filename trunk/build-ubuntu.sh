#!/bin/sh

# translations
pylupdate4 artisan.pro
lrelease -verbose artisan.pro

# distribution
rm -rf dist
bbfreeze artisan.py
#cp -L /usr/lib/i386-linux-gnu/libz.so dist
#cp -L /usr/lib/i386-linux-gnu/libxml2.so.2 dist
#cp -L /usr/lib/libicudata.so.48 dist
#cp -L /usr/lib/libicuuc.so.48 dist
#cp -L /usr/lib/libicui18n.so.48 dist
#cp -L /usr/lib/i386-linux-gnu/pkcs11/gnome-keyring-pkcs11.so dist
cp -R /usr/local/lib/python2.7/dist-packages/matplotlib/mpl-data/ dist
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
patchelf --set-rpath '${ORIGIN}:${ORIGIN}/../lib' dist/Resources/qt_plugins/imageformats/libqsvg.so
cp /usr/local/Trolltech/Qt-4.8.4/plugins/imageformats/libqgif.so dist/Resources/qt_plugins/imageformats
patchelf --set-rpath '${ORIGIN}:${ORIGIN}/../lib' dist/Resources/qt_plugins/imageformats/libqgif.so
#cp /usr/local/Trolltech/Qt-4.8.4/plugins/imageformats/libqjpeg.so dist/Resources/qt_plugins/imageformats
#patchelf --set-rpath '${ORIGIN}:${ORIGIN}/../lib' dist/Resources/qt_plugins/imageformats/libqjpeg.so
#cp /usr/local/Trolltech/Qt-4.8.4/plugins/imageformats/libqtiff.so dist/Resources/qt_plugins/imageformats
#patchelf --set-rpath '${ORIGIN}:${ORIGIN}/../lib' dist/Resources/qt_plugins/imageformats/libqtiff.so
cp /usr/local/Trolltech/Qt-4.8.4/plugins/iconengines/libqsvgicon.so dist/Resources/qt_plugins/iconengines
patchelf --set-rpath '${ORIGIN}:${ORIGIN}/../lib' dist/Resources/qt_plugins/iconengines/libqsvgicon.so
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
tar -cf dist-ubuntu.tar dist