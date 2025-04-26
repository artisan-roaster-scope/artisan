#!/bin/bash

set -e  # lỗi lệnh nào dừng ngay
set -x  # in các lệnh ra màn hình (debug dễ)

echo "[RPI ARM64] Installing dependencies..."

# Update repo
sudo apt update

# Fix trusted.gpg warnings nếu cần (chưa làm trong bản này, tập trung cài build trước)

# Cài các gói cơ bản
sudo apt install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-venv \
    git \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb-xinerama0

# Cài PyQt6 qua pip (vì apt không có pyqt6-dev-tools)
pip install --upgrade pip
pip install pyqt6 pyqt6-tools

# In version cho chắc chắn
python3 --version
pip show pyqt6
pip show pyqt6-tools

echo "[RPI ARM64] Dependencies installed successfully!"
