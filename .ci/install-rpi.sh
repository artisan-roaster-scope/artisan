#!/bin/sh

set -ex
sudo apt-get update -y -q
sudo apt-get install -y -q p7zip-full libglib2.0-dev zlib1g-dev qemu
