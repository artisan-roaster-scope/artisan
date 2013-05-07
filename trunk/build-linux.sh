#!/bin/sh


# build CentOS .rpm

rm -rf debian/usr/share/artisan
tar -xf dist-centos.tar -C debian/usr/share
mv debian/usr/share/dist debian/usr/share/artisan
find debian -name .svn -exec rm -rf {} \; > /dev/null 2>&1
dpkg --build debian artisan-0.6.0_i386.deb
alien -r artisan-0.6.0_i386.deb
mv artisan-0.6.0-1.i386.rpm artisan-0.6.0_i386.rpm

# build Ubuntu .deb

rm -rf debian/usr/share/artisan
tar -xf dist-ubuntu.tar -C debian/usr/share
mv debian/usr/share/dist debian/usr/share/artisan
find debian -name .svn -exec rm -rf {} \; > /dev/null 2>&1
rm debian artisan-0.6.0_i386.deb
dpkg --build debian artisan-0.6.0_i386.deb
