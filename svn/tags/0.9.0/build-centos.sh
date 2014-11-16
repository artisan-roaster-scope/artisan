#!/bin/sh

QT=/usr/local/Trolltech/Qt-4.8.6/

# translations
pylupdate4 artisan.pro
lrelease -verbose artisan.pro

# distribution
rm -rf dist
bbfreeze artisan.py
cp -L /usr/lib/libxml2.so.2 dist
patchelf --set-rpath '${ORIGIN}:${ORIGIN}/../lib' dist/libxml2.so.2
cp -L /usr/lib/libicudata.so.42 dist
patchelf --set-rpath '${ORIGIN}:${ORIGIN}/../lib' dist/libicudata.so.42
cp -L /usr/lib/libicuuc.so.42 dist
patchelf --set-rpath '${ORIGIN}:${ORIGIN}/../lib' dist/libicuuc.so.42
cp -L /usr/lib/libicui18n.so.42 dist
patchelf --set-rpath '${ORIGIN}:${ORIGIN}/../lib' dist/libicui18n.so.42
cp -L /usr/lib/gnome-keyring/gnome-keyring-pkcs11.so dist
patchelf --set-rpath '${ORIGIN}:${ORIGIN}/../lib' dist/gnome-keyring-pkcs11.so
cp -R /usr/local/lib/python2.7/site-packages/matplotlib/mpl-data/ dist
cp artisan-alog.xml dist
cp artisan-alrm.xml dist
cp artisan-apal.xml dist
cp artisan-wg.xml dist
cp includes/Humor-Sans.ttf dist
cp /usr/local/lib/python2.7/site-packages/yoctopuce/cdll/* dist
cp includes/alarmclock.eot dist
cp includes/alarmclock.svg dist
cp includes/alarmclock.ttf dist
cp includes/alarmclock.woff dist
cp includes/artisan.tpl dist
cp includes/bigtext.js dist
cp includes/jquery-1.11.1.min.js dist
cp -R icons dist
cp -R Wheels dist
cp README.txt dist
cp LICENSE.txt dist
mkdir dist/Resources
mkdir dist/Resources/qt_plugins
mkdir dist/Resources/qt_plugins/imageformats
mkdir dist/Resources/qt_plugins/iconengines
cp $QT/plugins/imageformats/libqsvg.so dist/Resources/qt_plugins/imageformats
patchelf --set-rpath '${ORIGIN}/../../..:${ORIGIN}/../../../../lib' dist/Resources/qt_plugins/imageformats/libqsvg.so
cp $QT/plugins/imageformats/libqgif.so dist/Resources/qt_plugins/imageformats
patchelf --set-rpath '${ORIGIN}/../../..:${ORIGIN}/../../../../lib' dist/Resources/qt_plugins/imageformats/libqgif.so
#cp $QT/plugins/imageformats/libqjpeg.so dist/Resources/qt_plugins/imageformats
#patchelf --set-rpath '/../../..${ORIGIN}:${ORIGIN}/../../../../lib' dist/Resources/qt_plugins/imageformats/libqjpeg.so
#cp $QT/plugins/imageformats/libqtiff.so dist/Resources/qt_plugins/imageformats
#patchelf --set-rpath '/../../..${ORIGIN}:${ORIGIN}/../../../../lib' dist/Resources/qt_plugins/imageformats/libqtiff.so
cp $QT/plugins/iconengines/libqsvgicon.so dist/Resources/qt_plugins/iconengines
patchelf --set-rpath '/../../..${ORIGIN}:${ORIGIN}/../../../../lib' dist/Resources/qt_plugins/iconengines/libqsvgicon.so
cp qt.conf dist
mkdir dist/translations
cp translations/*.qm dist/translations
cp $QT/translations/qt_de.qm dist/translations
cp $QT/translations/qt_es.qm dist/translations
cp $QT/translations/qt_fr.qm dist/translations
cp $QT/translations/qt_sv.qm dist/translations
cp $QT/translations/qt_zh_CN.qm dist/translations
cp $QT/translations/qt_zh_TW.qm dist/translations
cp $QT/translations/qt_ko.qm dist/translations
cp $QT/translations/qt_pt.qm dist/translations
cp $QT/translations/qt_ru.qm dist/translations
cp $QT/translations/qt_ar.qm dist/translations
cp $QT/translations/qt_ja.qm dist/translations
cp $QT/translations/qt_hu.qm dist/translations
cp $QT/translations/qt_pl.qm dist/translations
tar -cf dist-centos.tar dist