#!/bin/sh

VERSION=$(python -c 'import artisanlib; print(artisanlib.__version__)')
NAME=artisan-${VERSION}

# fix debian/DEBIAN/control _VERSION_
sed -e "s/_VERSION_/${VERSION}/g" debian/DEBIAN/control

# build CentOS .rpm

rm -rf debian/usr/share/artisan
tar -xf dist-centos.tar -C debian/usr/share
mv debian/usr/share/dist debian/usr/share/artisan
find debian -name .svn -exec rm -rf {} \; > /dev/null 2>&1
rm ${NAME}_i386.deb
dpkg --build debian ${NAME}_i386.deb
alien -r ${NAME}_i386.deb
mv ${NAME}-1.i386.rpm ${NAME}_i386-glibc2.3.rpm
mv ${NAME}_i386.deb ${NAME}_i386-glibc2.3.deb

# build Ubuntu .deb

rm -rf debian/usr/share/artisan
tar -xf dist-ubuntu.tar -C debian/usr/share
mv debian/usr/share/dist debian/usr/share/artisan
find debian -name .svn -exec rm -rf {} \; > /dev/null 2>&1
rm ${NAME}_i386.deb
dpkg --build debian ${NAME}_i386-glibc2.4.deb
