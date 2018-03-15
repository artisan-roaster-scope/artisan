#!/bin/sh

QT=/usr/local/Qt-5.4.2/

#export LD_LIBRARY_PATH=/usr/local/lib/python2.7/site-packages/matplotlib/.libs:$LD_LIBRARY_PATH

# translations
# PyQt5
pylupdate5 artisan.pro
# PyQt4
#pylupdate4 artisan.pro

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
cp artisan-aset.xml dist
cp artisan-wg.xml dist
cp includes/Humor-Sans.ttf dist
cp /usr/local/lib/python2.7/site-packages/yoctopuce/cdll/* dist
cp includes/alarmclock.eot dist
cp includes/alarmclock.svg dist
cp includes/alarmclock.ttf dist
cp includes/alarmclock.woff dist
cp includes/artisan.tpl dist
cp includes/bigtext.js dist
cp includes/sorttable.js dist
cp includes/report-template.htm dist
cp includes/roast-template.htm dist
cp includes/ranking-template.htm dist
cp includes/jquery-1.11.1.min.js dist
cp -R icons dist
cp -R Wheels dist
cp README.txt dist
cp ../LICENSE dist/LICENSE.txt
mkdir dist/Resources
mkdir dist/Resources/qt_plugins
mkdir dist/Resources/qt_plugins/imageformats
mkdir dist/Resources/qt_plugins/iconengines
mkdir dist/Resources/qt_plugins/platforms
mkdir dist/Resources/qt_plugins/platformthemes
cp $QT/plugins/imageformats/libqsvg.so dist/Resources/qt_plugins/imageformats
patchelf --set-rpath '${ORIGIN}/../../..:${ORIGIN}/../../../../lib' dist/Resources/qt_plugins/imageformats/libqsvg.so
cp $QT/plugins/imageformats/libqgif.so dist/Resources/qt_plugins/imageformats
patchelf --set-rpath '${ORIGIN}/../../..:${ORIGIN}/../../../../lib' dist/Resources/qt_plugins/imageformats/libqgif.so
#cp $QT/plugins/imageformats/libqjpeg.so dist/Resources/qt_plugins/imageformats
#patchelf --set-rpath '${ORIGIN}/../../..:${ORIGIN}/../../../../lib' dist/Resources/qt_plugins/imageformats/libqjpeg.so
#cp $QT/plugins/imageformats/libqtiff.so dist/Resources/qt_plugins/imageformats
#patchelf --set-rpath '${ORIGIN}/../../..:${ORIGIN}/../../../../lib' dist/Resources/qt_plugins/imageformats/libqtiff.so
cp $QT/plugins/iconengines/libqsvgicon.so dist/Resources/qt_plugins/iconengines
patchelf --set-rpath '${ORIGIN}/../../..:${ORIGIN}/../../../../lib' dist/Resources/qt_plugins/iconengines/libqsvgicon.so
cp $QT/plugins/platforms/libqxcb.so dist/Resources/qt_plugins/platforms
patchelf --set-rpath '${ORIGIN}/../../..:${ORIGIN}/../../../../lib' dist/Resources/qt_plugins/platforms/libqxcb.so
cp $QT/plugins/platformthemes/libqgtk2.so dist/Resources/qt_plugins/platformthemes
patchelf --set-rpath '${ORIGIN}/../../..:${ORIGIN}/../../../../lib' dist/Resources/qt_plugins/platformthemes/libqgtk2.so
cp qt.conf dist
mkdir dist/translations
cp translations/*.qm dist/translations
cp $QT/translations/qt_ar.qm dist/translations
cp $QT/translations/qt_de.qm dist/translations
cp $QT/translations/qt_es.qm dist/translations
cp $QT/translations/qt_fi.qm dist/translations
cp $QT/translations/qt_fr.qm dist/translations
cp $QT/translations/qt_he.qm dist/translations
cp $QT/translations/qt_hu.qm dist/translations
cp $QT/translations/qt_it.qm dist/translations
cp $QT/translations/qt_ja.qm dist/translations
cp $QT/translations/qt_ko.qm dist/translations
cp $QT/translations/qt_pl.qm dist/translations
cp $QT/translations/qt_pt.qm dist/translations
cp $QT/translations/qt_ru.qm dist/translations
cp $QT/translations/qt_sv.qm dist/translations
cp $QT/translations/qt_zh_CN.qm dist/translations
cp $QT/translations/qt_zh_TW.qm dist/translations
mkdir dist/Machines
find includes/Machines -name '.*.aset' -exec rm -r {} \;
cp -R includes/Machines/* dist/Machines
tar -cf dist-centos.tar dist