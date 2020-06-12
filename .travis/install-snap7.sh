#!/bin/sh

set -ex

version=1.4.2

if [ "$ARTISAN_OS" = "linux" ]; then
    libinstall=/usr/lib
    mkfile=x86_64_linux
    os="unix"
elif [ "$ARTISAN_OS" = "osx" ]; then
    libinstall=/usr/local/lib
    mkfile=x86_64_osx
    os="osx"
fi

# we use the -k option in the following as the SSL certificate on sourceforge does not validate
#curl -k -L -O https://kent.dl.sourceforge.net/project/snap7/${version}/snap7-full-${version}.7z
curl -k -L -O https://netcologne.dl.sourceforge.net/project/snap7/${version}/snap7-full-${version}.7z
7z x -bd snap7-full-${version}.7z
(cd snap7-full-${version}/build/${os} && make -f ${mkfile}.mk -j4 all && sudo make -f ${mkfile}.mk LibInstall=${libinstall} install)
