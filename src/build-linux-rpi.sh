#!/bin/bash
set -e

echo "[RPI ARM64] Starting build process..."

cd src

# Compile or prepare the application for ARM64
python3 build-linux.py

# Create .deb package
./build-linux-pkg.sh

echo "[RPI ARM64] Build finished successfully."
