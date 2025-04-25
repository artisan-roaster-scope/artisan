#!/bin/bash
set -e

echo "[RPI ARM64] Installing dependencies..."

# Update and install necessary packages
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-dev libffi-dev                         libusb-1.0-0-dev libjpeg-dev libqt6core6 libqt6gui6                         libqt6widgets6 pyqt6-dev-tools qt6-base-dev                         build-essential git curl

# Upgrade pip and install Python dependencies
python3 -m pip install --upgrade pip
pip3 install -r src/requirements.txt

echo "[RPI ARM64] Install complete."
