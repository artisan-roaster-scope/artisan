#!/bin/sh

set -ex

export QT_SELECT="default"
export QTTOOLDIR="/usr/lib/arm-linux-gnueabihf/qt4/bin"
export QTLIBDIR="/usr/lib/arm-linux-gnueabihf"
export QT_PATH=/usr/share/qt4

export QT=/usr/lib/arm-linux-gnueabihf/qt4
export PATH=$PATH:`python3 -m site --user-base`/bin

# translations
pylupdate4 artisan.pro
lrelease -verbose artisan.pro

# distribution
rm -rf build dist

pyinstaller --runtime-hook rthook_pyqt4.py -D -n artisan -y -c --log-level=WARN "artisan.py"


mv dist/artisan dist/artisan.d
mv dist/artisan.d/* dist
rm -rf dist/artisan.d

# copy translations
mkdir dist/translations
cp $QT_PATH/translations/qt_ar.qm dist/translations
cp $QT_PATH/translations/qt_de.qm dist/translations
cp $QT_PATH/translations/qt_es.qm dist/translations
#cp $QT_PATH/translations/qt_fi.qm dist/translations
cp $QT_PATH/translations/qt_fr.qm dist/translations
cp $QT_PATH/translations/qt_he.qm dist/translations
cp $QT_PATH/translations/qt_hu.qm dist/translations
#cp $QT_PATH/translations/qt_it.qm dist/translations
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
cp -R /usr/local/lib/python2.7/dist-packages/matplotlib/mpl-data/ dist
rm -rf dist/mpl-data/sample_data

# copy file icon and other includes
cp artisan-alog.xml dist
cp artisan-alrm.xml dist
cp artisan-apal.xml dist
cp artisan-aset.xml dist
cp artisan-wg.xml dist
cp includes/Humor-Sans.ttf dist
cp includes/WenQuanYiZenHei-01.ttf dist
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
cp -R icons dist
cp -R Wheels dist
cp README.txt dist
cp ../LICENSE dist/LICENSE.txt

mkdir dist/Machines
find includes/Machines -name '.*.aset' -exec rm -r {} \;
cp -R includes/Machines/* dist/Machines

mkdir dist/Themes
find includes/Themes -name '.*.aset' -exec rm -r {} \;
cp -R includes/Themes/* dist/Themes

mkdir dist/Icons
find includes/Icons -name '.*.aset' -exec rm -r {} \;
cp -R includes/Icons/* dist/Icons

cp /usr/local/lib/python2.7/dist-packages/yoctopuce/cdll/* dist

cp /usr/lib/libsnap7.so dist



## generate the .deb package

cp raspbian/DEBIAN/control debian/DEBIAN/
VERSION=$(python -c 'import artisanlib; print(artisanlib.__version__)')
NAME=artisan-linux-${VERSION}

# fix debian/DEBIAN/control _VERSION_
sed -i "s/_VERSION_/${VERSION}/g" debian/DEBIAN/control


# prepare debian directory

gzip -9 debian/usr/share/man/man1/artisan.1
chmod +r debian/usr/share/man/man1/artisan.1.gz
gzip -9 debian/usr/share/doc/artisan/changelog
chmod +r debian/usr/share/doc/artisan/changelog.gz

chmod +r debian/usr/share/applications/artisan.desktop
chmod -x debian/usr/share/applications/artisan.desktop
chmod +rx debian/usr/bin/artisan
chmod -R +r dist
chmod +x dist/icons

# buid .deb package (into /usr/share)

tar -cf dist-rpi.tar dist
rm -rf debian/usr/share/artisan
tar -xf dist-rpi.tar -C debian/usr/share
mv debian/usr/share/dist debian/usr/share/artisan
find debian -name .svn -exec rm -rf {} \; > /dev/null 2>&1
chown -R root:root debian
chmod -R go-w debian
rm -f ${NAME}_raspbian-jessie.deb
chmod 755 debian/DEBIAN
chmod 755 debian/DEBIAN/postinst
chmod 755 debian/DEBIAN/prerm
dpkg-deb --build debian ${NAME}_raspbian-jessie-py2.deb
