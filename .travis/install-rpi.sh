#!/bin/sh

set -ex
sudo apt-get install p7zip-full libglib2.0-dev zlib1g-dev

# Use updated qemu
curl -L -O http://ftp.us.debian.org/debian/pool/main/q/qemu/qemu-system-arm_2.11+dfsg-1_amd64.deb
curl -L -O http://ftp.us.debian.org/debian/pool/main/q/qemu/qemu-system-common_2.11+dfsg-1_amd64.deb
dpkg -i qemu*
#curl -L -O https://download.qemu.org/qemu-2.11.1.tar.xz
#tar xJf qemu-2.11.1.tar.xz
#cd qemu-2.11.1
#./configure --target-list=arm-softmmu
#make -j4
#sudo make install
#cd ..

# Use updated sfdisk
curl -L -O https://mirrors.edge.kernel.org/pub/linux/utils/util-linux/v2.32/util-linux-2.32.tar.gz
tar xzf util-linux-2.32.tar.gz
cd util-linux-2.32
./configure --disable-plymouth_support --disable-libmount --without-python
make -j4 sfdisk
./sfdisk || true

