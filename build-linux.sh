#!/bin/sh


# build CentOS .rpm

rm -rf debian/usr/share/artisan
tar -xf dist-centos.tar -C debian/usr/share
mv debian/usr/share/dist debian/usr/share/artisan
find debian -name .svn -exec rm -rf {} \; | /dev/null
dpkg --build debian artisan-0.6.0_i386.deb
alien -r artisan-0.6.0_i386.deb

# build Ubuntu .deb

rm -rf debian/usr/share/artisan
tar -xf dist-ubuntu.tar -C debian/usr/share
mv debian/usr/share/dist debian/usr/share/artisan
find debian -name .svn -exec rm -rf {} \; | /dev/null
dpkg --build debian artisan-0.6.0_i386.deb
