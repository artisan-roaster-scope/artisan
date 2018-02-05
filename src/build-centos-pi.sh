#!/bin/sh

export LD_LIBRARY_PATH=$LD_LIBTRARY_PATH:/usr/local/lib

export PYTHON_PATH=/usr/local/lib/python3.5
export QT_PATH=/usr/local/lib/python3.5/site-packages/PyQt5/Qt

rm -rf build
rm -rf dist

# pyinstaller -D -n artisan -y -c --hidden-import scipy._lib.messagestream --log-level=WARN "artisan.py"

pyinstaller -D -n artisan -y -c --hidden-import scipy._lib.messagestream --log-level=WARN artisan-linux.spec

mv dist/artisan dist/artisan.d
mv dist/artisan.d/* dist
rm -rf dist/artisan.d

# copy translations
mkdir dist/translations
cp $QT_PATH/translations/qt_ar.qm dist/translations
cp $QT_PATH/translations/qt_de.qm dist/translations
cp $QT_PATH/translations/qt_es.qm dist/translations
cp $QT_PATH/translations/qt_fi.qm dist/translations
cp $QT_PATH/translations/qt_fr.qm dist/translations
cp $QT_PATH/translations/qt_he.qm dist/translations
cp $QT_PATH/translations/qt_hu.qm dist/translations
cp $QT_PATH/translations/qt_it.qm dist/translations
cp $QT_PATH/translations/qt_ja.qm dist/translations
cp $QT_PATH/translations/qt_ko.qm dist/translations
cp $QT_PATH/translations/qt_pl.qm dist/translations
cp $QT_PATH/translations/qt_pt.qm dist/translations
cp $QT_PATH/translations/qt_ru.qm dist/translations
cp $QT_PATH/translations/qt_sv.qm dist/translations
cp $QT_PATH/translations/qt_zh_CN.qm dist/translations
cp $QT_PATH/translations/qt_zh_TW.qm dist/translations
cp translations/*.qm dist/translations

# copy data
cp -R $PYTHON_PATH/site-packages/matplotlib/mpl-data/ dist
rm -rf dist/mpl-data/sample_data

# copy file icon and other includes
cp artisan-alog.xml dist
cp artisan-alrm.xml dist
cp artisan-apal.xml dist
cp artisan-athm.xml dist
cp artisan-aset.xml dist
cp artisan-wg.xml dist
cp includes/Humor-Sans.ttf dist
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
cp LICENSE.txt dist

mkdir dist/Machines
find includes/Machines -name '.*.aset' -exec rm -r {} \;
cp -R includes/Machines/* dist/Machines

mkdir dist/Themes
find includes/Themes -name '.*.athm' -exec rm -r {} \;
cp -R includes/Themes/* dist/Themes

cp $PYTHON_PATH/site-packages/yoctopuce/cdll/* dist


cp README.txt dist
cp LICENSE.txt dist


tar -cf dist-centos64.tar dist

