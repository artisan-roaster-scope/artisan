#!/bin/sh

set -ex

export LD_LIBRARY_PATH=$LD_LIBTRARY_PATH:/usr/local/lib
export PATH=$PATH:$HOME/.local/bin

if [ ! -z $TRAVIS ]; then
    export PYTHON_PATH=/home/travis/virtualenv/python3.5/lib/python3.5/site-packages
else
    export PYTHON_PATH=`python -m site --user-site`
fi
export QT_PATH=$PYTHON_PATH/PyQt5/Qt

rm -rf build
rm -rf dist

rm -f libusb-1.0.so.0
if [ -f /lib/x86_64-linux-gnu/libusb-1.0.so.0 ]; then
    ln -s /lib/x86_64-linux-gnu/libusb-1.0.so.0
else
    ln -s /usr/lib/libusb-1.0.so.0
fi

# pyinstaller -D -n artisan -y -c --hidden-import scipy._lib.messagestream --log-level=WARN "artisan.py"

pyinstaller -D -n artisan -y -c --hidden-import scipy._lib.messagestream --log-level=INFO artisan-linux.spec

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
cp -R $PYTHON_PATH/matplotlib/mpl-data dist
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
cp ../LICENSE dist/LICENSE.txt

mkdir dist/Machines
find includes/Machines -name '.*.aset' -exec rm -r {} \;
cp -R includes/Machines/* dist/Machines

mkdir dist/Themes
find includes/Themes -name '.*.athm' -exec rm -r {} \;
cp -R includes/Themes/* dist/Themes

mkdir dist/Icons
find includes/Icons -name '.*.aset' -exec rm -r {} \;
cp -R includes/Icons/* dist/Icons

cp $PYTHON_PATH/yoctopuce/cdll/* dist

cp /usr/lib/libsnap7.so dist


cp README.txt dist
cp ../LICENSE dist/LICENSE.txt

rm -f libusb-1.0.so.0

tar -cf dist-centos64.tar dist

