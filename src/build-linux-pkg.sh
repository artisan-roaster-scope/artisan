#!/bin/sh

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
fakeroot chmod 0644 debian/usr/share/artisan/*.so*
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

fpm -s dir -t rpm -n artisan --license GPL3 -m "Marko Luther <marko.luther@gmx.net>"  -p .. \
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
fpm --deb-no-default-config-files -s dir -t deb -n artisan --license GPL3 -m "Marko Luther <marko.luther@gmx.net>" -p .. \
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

export ARCH=x86_64
# Create AppImage by using the pkg2appimage tool
wget -c https://github.com/$(wget -q https://github.com/AppImage/pkg2appimage/releases -O - | grep "pkg2appimage-.*-x86_64.AppImage" | head -n 1 | cut -d '"' -f 2)
chmod +x ./pkg2appimage-*.AppImage
ARCH=x86_64 ./pkg2appimage-*.AppImage artisan-AppImage.yml

mv ./out/*.AppImage ${NAME}.AppImage

ls -lh *.deb *.rpm
