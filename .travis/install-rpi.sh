#!/bin/sh

set -ex
sudo apt-get update
sudo apt-get install p7zip-full libglib2.0-dev zlib1g-dev

# Use updated qemu
curl -L -O https://download.qemu.org/qemu-2.11.1.tar.xz
tar xJf qemu-2.11.1.tar.xz
cd qemu-2.11.1
./configure --target-list=arm-softmmu
make
sudo make install
cd ..

# Use updated sfdisk
curl -L -O https://mirrors.edge.kernel.org/pub/linux/utils/util-linux/v2.32/util-linux-2.32.tar.gz
tar xzf util-linux-2.32.tar.gz
cd util-linux-2.32
./configure --disable-plymouth_support 
make
sudo make install
