#!/bin/sh

set -ex

VERSION=$(python -c 'import artisanlib; print(artisanlib.__version__)')
NAME=artisan-linux-${VERSION}

# fix debian/DEBIAN/control _VERSION_
sed -i "s/_VERSION_/${VERSION}/g" debian/DEBIAN/control


# prepare debian directory

gzip -9 debian/usr/share/man/man1/artisan.1
gzip -9 debian/usr/share/doc/artisan/changelog


# build CentOS x86_64 .rpm

rm -rf debian/usr/share/artisan
tar -xf dist-centos64.tar -C debian/usr/share
mv debian/usr/share/dist debian/usr/share/artisan
find debian -name .svn -exec rm -rf {} \; > /dev/null 2>&1
sudo chown -R root:root debian
sudo chmod -R go-w debian
sudo chmod 0644 debian/usr/share/artisan/*.so*
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

fpm --debug --verbose -s dir -t rpm -n artisan --license GPL3 -m "Marko Luther <marko.luther@gmx.net>"  -p .. \
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
sudo chmod o+w .
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
ls -lh *.deb *.rpm
