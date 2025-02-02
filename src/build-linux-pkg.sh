#!/bin/sh
# ABOUT
# build packaging shell script for Artisan Linux builds
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

VERSION=$(python -c 'import artisanlib; print(artisanlib.__version__)')
NAME=artisan-linux-${VERSION}

# fix debian/DEBIAN/control _VERSION_
sed -i "s/_VERSION_/${VERSION}/g" debian/DEBIAN/control


# prepare debian directory

gzip -9 debian/usr/share/man/man1/artisan.1
gzip -9 debian/usr/share/doc/artisan/changelog


# build CentOS x86_64 .rpm

tar -cf dist-centos64.tar dist
rm -rf dist
rm -rf debian/usr/share/artisan
tar -xf dist-centos64.tar -C debian/usr/share
rm dist-centos64.tar
mv debian/usr/share/dist debian/usr/share/artisan
find debian -name .svn -exec rm -rf {} \; > /dev/null 2>&1
fakeroot chown -R root:root debian
fakeroot chmod -R go-w debian
# Find and delete dangling symbolic links
find "debian/usr/share/artisan/_internal/" -type l -name "*.so*" ! -exec test -e {} \; -delete
fakeroot chmod 0644 debian/usr/share/artisan/_internal/*.so* || true
fakeroot chmod +x debian/usr/bin/artisan
rm -f ${NAME}*.rpm

cd debian

rm -rf usr/._bin
rm -rf usr/._share
rm -rf usr/bin/._*
rm -rf usr/share/._*
rm -rf usr/share/doc/._*
rm -rf usr/share/doc/artisan/._*
rm -rf usr/share/man/._*
rm -rf usr/share/man/man1/._*
rm -rf usr/share/pixmaps/._*
rm -rf usr/share/applications/._*

sudo fpm -s dir -t rpm -n artisan --license GPL3 -m "Marko Luther <marko.luther@gmx.net>"  -p .. \
--vendor "Artisan GitHub" \
--url "https://github.com/artisan-roaster-scope/artisan" \
--description "This program or software helps coffee roasters record, analyze, and control
roast profiles. With the help of a thermocouple data logger, or a
proportional–integral–derivative controller (PID controller), this software
offers roasting metrics to help make decisions that influence the final coffee
flavor." \
--after-install DEBIAN/postinst \
--before-remove DEBIAN/prerm \
-v ${VERSION} --prefix / usr etc

# Allow FPM to write some temporary files
fakeroot chmod o+w .
sudo fpm --deb-no-default-config-files -s dir -t deb -n artisan --license GPL3 -m "Marko Luther <marko.luther@gmx.net>" -p .. \
--vendor "Artisan GitHub" \
--no-auto-depends \
--url "https://github.com/artisan-roaster-scope/artisan" \
--description "This program or software helps coffee roasters record, analyze, and control
roast profiles. With the help of a thermocouple data logger, or a
proportional–integral–derivative controller (PID controller), this software
offers roasting metrics to help make decisions that influence the final coffee
flavor." \
--after-install DEBIAN/postinst \
--before-remove DEBIAN/prerm \
-v ${VERSION} --prefix / usr etc

cd ..
mv *.rpm ${NAME}.rpm
mv *.deb ${NAME}.deb

# imagemagick missing from pkg2appimage continuous as of bd9684f (27-Jan-25)
# reference https://github.com/AppImageCommunity/pkg2appimage/issues/445
# TODO - watch for this to be resolved
echo "*** Installing imagemagick"
sudo apt-get install -y imagemagick

export ARCH=x86_64
# Create AppImage by using the pkg2appimage tool
wget -c https://github.com/$(wget -q https://github.com/AppImage/pkg2appimage/releases/expanded_assets/continuous -O - | grep "pkg2appimage-.*-x86_64.AppImage" | head -n 1 | cut -d '"' -f 2)
chmod +x ./pkg2appimage-*.AppImage
ARCH=x86_64 ./pkg2appimage-*.AppImage artisan-AppImage.yml

mv ./out/*.AppImage ${NAME}.AppImage

ls -lh *.deb *.rpm

# Check that the packaged files are above an expected size
basename=${NAME}
suffixes=".deb .rpm .AppImage" # separate statements for suffixes to check
min_size=270000000
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
