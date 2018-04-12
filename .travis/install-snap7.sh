#!/bin/sh

set -ex

version=1.4.2

if [ "$ARTISAN_OS" = "linux" ]; then
    libinstall=/usr/lib
    mkfile=x86_64_linux
elif [ "$ARTISAN_OS" = "osx" ]; then
    libinstall=/usr/local/lib
    mkfile=x86_64_osx
fi

curl -L -O https://kent.dl.sourceforge.net/project/snap7/${version}/snap7-full-${version}.7z
7z x -bd snap7-full-${version}.7z
(cd snap7-full-${version}/build/${ARTISAN_OS} && make -f ${mkfile}.mk all && sudo make -f ${mkfile}.mk LibInstall=${libinstall} install)
