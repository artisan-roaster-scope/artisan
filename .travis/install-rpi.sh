#!/bin/sh

set -ex
sudo apt-get update
sudo apt-get install p7zip-full libglib2.0-dev zlib1g-dev
sudo apt-get install qemu-system-arm

#curl -L -O https://download.qemu.org/qemu-4.0.0.tar.xz
#tar xJf qemu-4.0.0.tar.xz
#cd qemu-4.0.0
#./configure --target-list=arm-softmmu
#make -j4
#sudo make install
#cd ..

# Use updated sfdisk
curl -L -O https://dl.bintray.com/artisan/artisan-cache/sfdisk.tar.gz
tar xvf sfdisk.tar.gz
sudo mv sfdisk /sbin
#curl -L -O https://mirrors.edge.kernel.org/pub/linux/utils/util-linux/v2.32/util-linux-2.32.tar.gz
#tar xzf util-linux-2.32.tar.gz
#cd util-linux-2.32
#./configure --disable-plymouth_support --disable-libmount --without-python
#make -j4 sfdisk

