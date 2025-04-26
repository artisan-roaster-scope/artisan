#!/bin/bash

set -e
set -x

echo "[CROSS-BUILD] Start Raspberry Pi cross build inside Docker..."

# Ensure docker is installed
sudo apt update
sudo apt install -y docker.io qemu-user-static

# Enable ARM emulation
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Pull ARM64 Ubuntu image
docker pull arm64v8/ubuntu:22.04

# Build inside the ARM64 container
docker run --rm -t \
    --platform linux/arm64 \
    -v $(pwd):/workdir \
    -w /workdir \
    arm64v8/ubuntu:22.04 \
    bash -c "
        apt update &&
        apt install -y python3 python3-pip python3-venv git build-essential libffi-dev libssl-dev libjpeg-dev zlib1g-dev libopenjp2-7-dev libtiff5-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev libharfbuzz-dev libfribidi-dev libxcb-xinerama0 &&
        pip3 install --upgrade pip &&
        pip3 install pyqt6 pyqt6-tools &&
        chmod +x .ci/*.sh src/*.sh &&
        .ci/install-rpi.sh &&
        cd src &&
        ./build-rpi-deb.sh
    "

echo "[CROSS-BUILD] Finished building for Raspberry Pi!"
