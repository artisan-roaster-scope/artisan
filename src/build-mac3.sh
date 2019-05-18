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
    export QT_SRC_PATH=~/Qt5.12.3/5.12.3/clang_64
    export MACOSX_DEPLOYMENT_TARGET=10.13
    export DYLD_LIBRARY_PATH=$PYTHON/lib:$DYLD_LIBRARY_PATH
    export ARTISAN_LEGACY_BUILD=false
fi

export PATH=$PYTHON/bin:$PYTHON/lib:$PATH
export PATH=$QT_PATH/bin:$QT_PATH/lib:$PATH
export DYLD_FRAMEWORK_PATH=$QT_PATH/lib

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
$PYTHON/bin/python$PYTHON_V setup-mac3.py py2app | egrep -v '^(creating|copying file|byte-compiling|locate)'
