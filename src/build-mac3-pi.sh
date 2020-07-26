#!/bin/sh

#set -ex
set -e

# add argument "legacy" to make a build that supports older OS X systems using an outdated Qt

if [ ! -z $TRAVIS ]; then
    # Travis CI builds
    export PYTHON=/usr/local
    export PYTHONPATH=$PYTHON/lib/python3.7
    export PYTHON_V=3.7
    export QT_PATH=${PYTHONPATH}/site-packages/PyQt5/Qt
    export QT_SRC_PATH=${QT_PATH}
    export MACOSX_DEPLOYMENT_TARGET=10.13
    export ARTISAN_LEGACY_BUILD=false
elif [[ "$1" = "legacy" ]]; then
    # local legacy build featuring an outdated Qt to minimize the DEPLOYMENT_TARGET supporting older system
    export PYTHON=/Library/Frameworks/Python.framework/Versions/3.6
    export PYTHONPATH=$PYTHON/lib/python3.6
    export PYTHON_V=3.6
    export QT_PATH=${PYTHONPATH}/site-packages/PyQt5/Qt
#    export QT_SRC_PATH=~/Qt5.9.3/5.9.3/clang_64
    export QT_SRC_PATH=${QT_PATH}
    export MACOSX_DEPLOYMENT_TARGET=10.10
    export DYLD_LIBRARY_PATH=$PYTHON/lib:$DYLD_LIBRARY_PATH
    export ARTISAN_LEGACY_BUILD=true
else
    # standard local builds
    export PYTHON=/Library/Frameworks/Python.framework/Versions/3.7
    export PYTHONPATH=$PYTHON/lib/python3.7
    export PYTHON_V=3.7
    export QT_PATH=${PYTHONPATH}/site-packages/PyQt5/Qt
    export QT_SRC_PATH=~/Qt5.13.2/5.13.2/clang_64
    export MACOSX_DEPLOYMENT_TARGET=10.13
    export DYLD_LIBRARY_PATH=$PYTHON/lib:$DYLD_LIBRARY_PATH
    export ARTISAN_LEGACY_BUILD=false
fi

export PATH=$PYTHON/bin:$PYTHON/lib:$PATH
export PATH=$QT_PATH/bin:$QT_PATH/lib:$PATH
export DYLD_FRAMEWORK_PATH=$QT_PATH/lib
#export DYLD_LIBRARY_PATH=$PYTHON/lib/python$PYTHON_V/site-packages/PIL/.dylibs/:$DYLD_LIBRARY_PATH

# translations
$PYTHON/bin/pylupdate5 artisan.pro
# there is no full Qt installation on Travis, thus don't run  lrelease
if [ -z $TRAVIS ]; then
    $QT_SRC_PATH/bin/lrelease -verbose artisan.pro || true
    for f in translations/qtbase_*.ts
    do
        echo "Processing $f file..."
        $QT_SRC_PATH/bin/lrelease -verbose $f || true
    done
fi

# distribution
rm -rf build dist
sleep .3 # sometimes it takes a little for dist to get really empty

pyinstaller --noconfirm \
    --clean \
    --osx-bundle-identifier=org.artisan-scope.artisan \
    --windowed \
    --log-level=WARN \
    artisan-mac.spec

# copy qt_plugins to Resources/qt_plugins/
# copy qt.conf => Resources/

# copy translations
mkdir dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_ar.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_de.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_es.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_fi.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_fr.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_he.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_hu.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_it.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_ja.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_ko.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_pl.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_pt.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_ru.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_sv.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_zh_CN.qm dist/Artisan.app/Contents/Resources/translations
cp $QT_PATH/translations/qt_zh_TW.qm dist/Artisan.app/Contents/Resources/translations
cp translations/*.qm dist/Artisan.app/Contents/Resources/translations

# copy file icons and others
cp artisanProfile.icns dist/Artisan.app/Contents/Resources
cp artisanAlarms.icns dist/Artisan.app/Contents/Resources
cp artisanPalettes.icns dist/Artisan.app/Contents/Resources
cp artisanSettings.icns dist/Artisan.app/Contents/Resources
cp includes/alarmclock.eot dist/Artisan.app/Contents/Resources
cp includes/alarmclock.svg dist/Artisan.app/Contents/Resources
cp includes/alarmclock.ttf dist/Artisan.app/Contents/Resources
cp includes/alarmclock.woff dist/Artisan.app/Contents/Resources
cp includes/artisan.tpl dist/Artisan.app/Contents/Resources
cp includes/bigtext.js dist/Artisan.app/Contents/Resources
cp includes/sorttable.js dist/Artisan.app/Contents/Resources
cp includes/report-template.htm dist/Artisan.app/Contents/Resources
cp includes/roast-template.htm dist/Artisan.app/Contents/Resources
cp includes/ranking-template.htm dist/Artisan.app/Contents/Resources
cp includes/Humor-Sans.ttf dist/Artisan.app/Contents/Resources
cp includes/WenQuanYiZenHei-01.ttf dist/Artisan.app/Contents/Resources
cp includes/SourceHanSansCN-Regular.otf dist/Artisan.app/Contents/Resources
cp includes/SourceHanSansHK-Regular.otf dist/Artisan.app/Contents/Resources
cp includes/SourceHanSansJP-Regular.otf dist/Artisan.app/Contents/Resources
cp includes/SourceHanSansKR-Regular.otf dist/Artisan.app/Contents/Resources
cp includes/SourceHanSansTW-Regular.otf dist/Artisan.app/Contents/Resources
cp includes/jquery-1.11.1.min.js dist/Artisan.app/Contents/Resources


mkdir dist/Artisan.app/Contents/Resources/Machines
find includes/Machines -name '.*.aset' -exec rm -r {} \;
cp -R includes/Machines/* dist/Artisan.app/Contents/Resources/Machines

mkdir dist/Artisan.app/Contents/Resources/Themes
find includes/Themes -name '.*.athm' -exec rm -r {} \;
cp -R includes/Themes/* dist/Artisan.app/Contents/Resources/Themes

mkdir dist/Artisan.app/Contents/Resources/Icons
find includes/Icons -name '.*.aset' -exec rm -r {} \;
cp -R includes/Icons/* dist/Artisan.app/Contents/Resources/Icons

#cp $PYTHON_PATH/yoctopuce/cdll/* dist

cp README.txt dist
cp ../LICENSE dist/LICENSE.txt

# remove the executable 
rm dist/Artisan

$PYTHON/bin/python$PYTHON_V  create_dmg.py
