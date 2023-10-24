#!/bin/sh
# ABOUT
# Build shell script for Artisan Linux builds
#
# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# AUTHOR
# Dave Baxter, Marko Luther 2023

#set -ex
set -e  # reduced logging


export LD_LIBRARY_PATH=$LD_LIBTRARY_PATH:/usr/local/lib
export PATH=$PATH:$HOME/.local/bin

if [ ! -z $APPVEYOR ]; then
    # Appveyor environment
    echo "NOTICE: Appveyor build"
elif [ -d /usr/lib/python3/dist-packages/PyQt6 ]; then
    # ARM RPi bookworm builds (assumes requirements.txt installed in a user local venv
    export PYTHON_PATH=`python3 -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])'`
    export PYTHONSITEPKGS=`python3 -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])'`
    export QT_PATH=/usr/share/qt6
    export QT_SRC_PATH=/usr/lib/qt6
#    export PYUIC=`python3 -m PyQt6.uic.pyuic`
    export PYLUPDATE=./pylupdate6pro.py
#    export PYLUPDATE=/usr/bin/pylupdate6
else
    # Other builds
    export PYTHON_PATH=`python3 -m site --user-site`
    export QT_PATH=$PYTHON_PATH/PyQt5/Qt
fi

echo "************* build derived files **************"
./build-derived.sh linux  #generate the derived files
if [ $? -ne 0 ]; then echo "Failed in build-derived.sh"; exit $?; else (echo "** Finished build-derived.sh"); fi

rm -rf build
rm -rf dist

rm -f libusb-1.0.so.0
if [ -f /lib/x86_64-linux-gnu/libusb-1.0.so.0 ]; then
    ln -s /lib/x86_64-linux-gnu/libusb-1.0.so.0
elif [ -f /lib/arm-linux-gnueabihf/libusb-1.0.so.0 ]; then
    ln -s /lib/arm-linux-gnueabihf/libusb-1.0.so.0
else
    ln -s /usr/lib/libusb-1.0.so.0
fi

pyinstaller -y --log-level=INFO artisan-linux.spec

mv dist/artisan dist/artisan.d
mv dist/artisan.d/* dist
rm -rf dist/artisan.d

# copy translations
mkdir dist/translations


for lan in ar, da, de, en, el, es, fa, fi, fr, gd, he, hu, id, it, ja, ko, lv, nl, no, pl, pt_BR, pt, sk, sv, th, tr, uk, vi, zh_CN, zh_TW; do
     QTBASE_FILE=$QT_PATH/translations/qtbase_${lan}.qm
     QT_FILE=$QT_PATH/translations/qt_${lan}.qm
#     QTCONNECTIVITY_FILE=$QT_PATH/translations/qtconnectivity_${lan}.qm
     if [ -e ${QTBASE_FILE} ]
          then cp ${QTBASE_FILE} dist/translations
     fi
     if [ -e ${QT_FILE} ]
          then cp ${QT_FILE} dist/translations
     fi
#     if [ -e ${QTCONNECTIVITY_FILE} ]
#          then cp ${QTCONNECTIVITY_FILE} dist/translations
#     fi
done

cp translations/*.qm dist/translations

# copy data (mpl-data is now copied to matplotlib/mpl-data by pyinstaller)
#cp -R $PYTHON_PATH/matplotlib/mpl-data dist
rm -rf dist/_internal/matplotlib/sample_data

# copy file icon and other includes
cp artisan-alog.xml dist
cp artisan-alrm.xml dist
cp artisan-apal.xml dist
cp artisan-athm.xml dist
cp artisan-aset.xml dist
cp artisan-wg.xml dist
cp includes/Humor-Sans.ttf dist
cp includes/WenQuanYiZenHei-01.ttf dist
cp includes/WenQuanYiZenHeiMonoMedium.ttf dist
cp includes/SourceHanSansCN-Regular.otf dist
cp includes/SourceHanSansHK-Regular.otf dist
cp includes/SourceHanSansJP-Regular.otf dist
cp includes/SourceHanSansKR-Regular.otf dist
cp includes/SourceHanSansTW-Regular.otf dist
cp includes/dijkstra.ttf dist
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
cp includes/android-chrome-192x192.png dist
cp includes/android-chrome-512x512.png dist
cp includes/apple-touch-icon.png dist
cp includes/browserconfig.xml dist
cp includes/favicon-16x16.png dist
cp includes/favicon-32x32.png dist
cp includes/favicon.ico dist
cp includes/mstile-150x150.png dist
cp includes/safari-pinned-tab.svg dist
cp includes/site.webmanifest dist
cp includes/logging.yaml dist
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

# remove automatically collected PyQt6 libs that are not used to save space
# with pyinstaller 6.0 it seems not to needed any longer to remove unused Qt libs:
#keep_qt_modules="libQt6Core libQt6Gui libQt6Widgets libQt6Svg libQt6PrintSupport
# libQt6Network libQt6DBus libQt6Bluetooth libQt6Concurrent libQt6WebEngineWidgets
# libQt6WebEngineCore libQt6WebEngine libQt6Quick libQt6QuickWidgets libQt6Qml
# libQt6QmlModels libQt6WebChannel libQt6Positioning libQt6OpenGL libQt6WaylandClient"
#
#for qtlib in dist/_internal/libQt6*.so.*; do
#    match=0
#    for item in ${keep_qt_modules}; do
#        if [ ${qtlib} = dist/_internal/${item}.so.* ]; then
#            match=1
#            break
#        fi
#    done
#    if [ $match = 0 ]; then
##        rm -f ${qtlib}
#        echo ${qtlib}
#    fi
#done

# remove Qt5 libs
rm -rf dist/_internal/libQt5*
rm -rf dist/_internal/PyQt5

rm -rf dist/_internal/PyQt6/Qt6/translations
rm -rf dist/_internal/PyQt6/Qt6/qml/QtQuick3D

# remove automatically collected libs that might break things on some installations (eg. Ubuntu 16.04)
# so it is better to rely on the system installed once
# see https://github.com/gridsync/gridsync/issues/47 and https://github.com/gridsync/gridsync/issues/43
#   and https://askubuntu.com/questions/575505/glibcxx-3-4-20-not-found-how-to-fix-this-error
rm -f dist/_internal/libdrm.so.2 # https://github.com/gridsync/gridsync/issues/47
rm -f dist/_internal/libX11.so.6 # https://github.com/gridsync/gridsync/issues/43
rm -f dist/_internal/libstdc++.so.6 # https://github.com/gridsync/gridsync/issues/189
# the following libs might not need to be removed
rm -f dist/_internal/libgio-2.0.so.0
rm -f dist/_internal/libz.so.1 # removing this lib seems to break the build on some RPi Buster version
rm -f dist/_internal/libglib-2.0.so.0 # removed for v1.6 and later

rm -f libusb-1.0.so.0
