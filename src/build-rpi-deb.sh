#!/bin/sh

set -ex

## generate the .deb package

VERSION=$(python3 -c 'import artisanlib; print(artisanlib.__version__)')
NAME=artisan-linux-${VERSION}

# fix debian/DEBIAN/control _VERSION_ and arch
sed -i'' -e "s/_VERSION_/${VERSION}/g" debian/DEBIAN/control
sed -i'' -e "s/x86_64/armhf/g" debian/DEBIAN/control


# prepare debian directory

gzip -9 debian/usr/share/man/man1/artisan.1
chmod +r debian/usr/share/man/man1/artisan.1.gz
gzip -9 debian/usr/share/doc/artisan/changelog
chmod +r debian/usr/share/doc/artisan/changelog.gz

chmod +r debian/usr/share/applications/artisan.desktop
chmod -x debian/usr/share/applications/artisan.desktop
chmod +rx debian/usr/bin/artisan
chmod -R +r dist
chmod +x dist/icons

# build .deb package (into /usr/share)

tar -cf dist-rpi.tar dist
rm -rf dist
rm -rf debian/usr/share/artisan
tar -xf dist-rpi.tar -C debian/usr/share
rm dist-rpi.tar
mv debian/usr/share/dist debian/usr/share/artisan
find debian -name .svn -exec rm -rf {} \; > /dev/null 2>&1
sudo chown -R root:root debian
sudo chmod -R go-w debian
rm -f ${NAME}_raspbian-stretch.deb
sudo chmod 755 debian/DEBIAN
sudo chmod 755 debian/DEBIAN/postinst
sudo chmod 755 debian/DEBIAN/prerm
(while :; do ps ax | grep dpkg; sleep 300;done)&
dpkg-deb --build debian ${NAME}_raspbian-bookworm.deb
