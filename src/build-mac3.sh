#!/bin/sh

#set -ex
set -e  # reduced logging

# add argument "legacy" to make a build that supports older OS X systems using an outdated Qt

if [ ! -z $APPVEYOR ]; then
    # Appveyor CI builds
    echo "NOTICE: Appveyor build"
    export PYTHON=/Users/appveyor/venv3.9.1
    export PYTHONBIN=$PYTHON/bin
    export PYTHONPATH=$PYTHON/lib/python3.9
    export PYTHON_V=3.9
    
    export QT_PATH=${PYTHONPATH}/site-packages/PyQt5/Qt5 # from PyQt v5.15.4 this dir changed form PyQt5/Qt to PyQt5/Qt5
    export QT_SRC_PATH=${QT_PATH}
    export MACOSX_DEPLOYMENT_TARGET=10.15
    export ARTISAN_LEGACY_BUILD=false
else
    # standard local builds
    echo "NOTICE: Standard build"
    export PYTHON_V=3.9	
    export PYTHON=/Library/Frameworks/Python.framework/Versions/${PYTHON_V}
    export PYTHONBIN=$PYTHON/bin
    export PYTHONPATH=$PYTHON/lib/python${PYTHON_V}

    export QT_PATH=${PYTHONPATH}/site-packages/PyQt5/Qt5 # from PyQt v5.15.4 this dir changed form PyQt5/Qt to PyQt5/Qt5
    export QT_SRC_PATH=~/Qt5.15.2/5.15.2/clang_64
    export MACOSX_DEPLOYMENT_TARGET=10.15
    export DYLD_LIBRARY_PATH=$PYTHON/lib:$DYLD_LIBRARY_PATH
    export ARTISAN_LEGACY_BUILD=false
fi

export PATH=$PYTHON/bin:$PYTHON/lib:$PATH
export PATH=$QT_PATH/bin:$QT_PATH/lib:$PATH
export DYLD_FRAMEWORK_PATH=$QT_PATH/lib


# ui / qrc
if [ -z $APPVEYOR ]; then
    echo "************* 0 **************"
    # ui
    find ui -iname "*.ui" | while read f
    do
        fullfilename=$(basename $f)
        fn=${fullfilename%.*}
        pyuic5 -o uic/${fn}.py --from-imports ui/${fn}.ui
    done
    
#    # qrc
#    find qrc -iname "*.qrc" | while read f
#    do
#        fullfilename=$(basename $f)
#        fn=${fullfilename%.*}
#        pyrcc5 -o uic/${fn}_rc.py qrc/${fn}.qrc
#    done
fi

# translations
echo "************* 1 **************"
$PYTHONBIN/pylupdate5 artisan.pro
#/Users/appveyor/venv3.8.6/bin/pylupdate5 artisan.pro

# there is no full Qt installation on Travis, thus don't run  lrelease
if [ -z $APPVEYOR ]; then
    echo "************* 2 **************"
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
echo "************* 3 **************"
$PYTHON/bin/python$PYTHON_V setup-mac3.py py2app | egrep -v '^(creating|copying file|byte-compiling|locate)'
#/Users/appveyor/venv3.8.6/bin/python$PYTHON_V setup-mac3.py py2app | egrep -v '^(creating|copying file|byte-compiling|locate)'
