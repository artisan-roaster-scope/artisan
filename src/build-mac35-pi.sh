#!/bin/sh

set -ex

export MACOSX_DEPLOYMENT_TARGET=10.10

if [ ! -z $TRAVIS ]; then
    export PYTHON=/usr/local
    export PYTHONPATH=$PYTHON/lib/python3.6/site-packages
    export PYTHON_V=3.6
else
    export PYTHON=/Library/Frameworks/Python.framework/Versions/3.5
    export PYTHONPATH=$PYTHON/lib/python3.5/site-packages
    export PYTHON_V=3.5
fi

export QT_PATH=~/Qt5.9.3/5.9.3/clang_64

export PATH=$PYTHON/bin:$PYTHON/lib:$PATH
export PATH=$QT_PATH/bin:$QT_PATH/lib:$PATH
#export DYLD_FRAMEWORK_PATH=$QT_PATH/lib
export DYLD_LIBRARY_PATH=$PYTHON/lib/python$PYTHON_V/site-packages/PIL/.dylibs/:$DYLD_LIBRARY_PATH

# translations
$PYTHON/bin/pylupdate5 artisan.pro
$QT_PATH/bin/lrelease -verbose artisan.pro

# distribution
rm -rf build dist

pyinstaller --noconfirm \
    --clean \
    --osx-bundle-identifier=com.google.code.p.Artisan \
    --windowed \
    artisan.spec
#    --log-level=WARN \


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
cp includes/jquery-1.11.1.min.js dist/Artisan.app/Contents/Resources


cp README.txt dist
cp ../LICENSE dist/LICENSE.txt

# remove the executable 
rm dist/Artisan

if [ ! -z $TRAVIS ]; then
    python3 create_dmg.py
else
    $PYTHON/bin/python3.5 create_dmg.py
fi
