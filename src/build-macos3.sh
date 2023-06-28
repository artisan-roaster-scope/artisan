#!/bin/sh
# ABOUT
# Build shell script for Artisan macOS builds
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

echo $PATH

#set -ex
set -e  # reduced logging
python3 -V

if [ ! -z $APPVEYOR ]; then
    # Appveyor CI builds
    echo "NOTICE: Appveyor build"

else
    # standard local builds
    echo "NOTICE: Standard build"
    export PYTHON_V=3.11
    export PYTHON=/Library/Frameworks/Python.framework/Versions/${PYTHON_V}
    export PYTHONBIN=$PYTHON/bin
    export PYTHONPATH=$PYTHON/lib/python${PYTHON_V}

# for PyQt6:
    export QT_PATH=${PYTHONPATH}/site-packages/PyQt6/Qt6
    export QT_SRC_PATH=~/Qt/6.5.1/macos
    export PYUIC=pyuic6
    #remove export PYRCC=pyrcc6
    export PYLUPDATE=./pylupdate6pro

    export MACOSX_DEPLOYMENT_TARGET=11.0
    export DYLD_LIBRARY_PATH=$PYTHON/lib:$DYLD_LIBRARY_PATH
    export PATH=$PYTHON/bin:$PYTHON/lib:$PATH
    export PATH=$QT_PATH/bin:$QT_PATH/lib:$PATH

    #export DYLD_FRAMEWORK_PATH=$QT_PATH/lib # with this line all Qt libs are copied into Contents/Frameworks. Why?

fi

echo "************* build derived files **************"
./build-derived.sh macos  #generate the derived files
if [ $? -ne 0 ]; then echo "Failed in build-derived.sh"; exit $?; else (echo "** Finished build-derived.sh"); fi


# distribution
rm -rf build dist
sleep .3 # sometimes it takes a little for dist to get really empty
echo "************* p2app **************"
python3 setup-macos3.py py2app | egrep -v '^(creating|copying file|byte-compiling|locate)'

# Check that the packaged files are above an expected size
version=$(python3 -c "import artisanlib; print(artisanlib.__version__)")
basename="artisan-mac-$version"
echo "basename: $basename"
suffixes=".dmg" # array of suffixes to check
min_size=260000000
for suffix in $suffixes; do
    filename="$basename$suffix"
    size=$(($(du -k "$filename" | cut -f1) * 1024)) # returns kB so multiply by 1024 (du works on macOS)
    echo "$filename size: $size bytes"
    if [ "$size" -lt "$min_size" ]; then
        echo "$filename is smaller than minimum $min_size bytes"
        exit 1
    else
        echo "**** Success: $filename is larger than minimum $min_size bytes"
    fi
done
