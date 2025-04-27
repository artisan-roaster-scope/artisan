@echo off
:: ABOUT
:: Install script for Artisan Windows CI builds
::
:: LICENSE
:: This program or module is free software: you can redistribute it and/or
:: modify it under the terms of the GNU General Public License as published
:: by the Free Software Foundation, either version 2 of the License, or
:: version 3 of the License, or (at your option) any later versison. It is
:: provided for educational purposes and is distributed in the hope that
:: it will be useful, but WITHOUT ANY WARRANTY; without even the implied
:: warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
:: the GNU General Public License for more details.
::
:: AUTHOR
:: Dave Baxter, Marko Luther 2023


:: the current directory on entry to this script must be the folder above src

setlocal enabledelayedexpansion
if /i "%APPVEYOR%" NEQ "True" (
    echo This file is for use on Appveyor CI only.
    exit /b 1
)
if /i "%ARTISAN_LEGACY%" NEQ "True" (
    set ARTISAN_SPEC=win
) else (
    set ARTISAN_SPEC=win-legacy
)
:: ----------------------------------------------------------------------

ver
echo Python Version:
python -V

::
:: Upgrade the Python version to PYUPGRADE_WIN_V whenever the environment variable exists.
::
if NOT "%PYUPGRADE_WIN_V%" == "" (
    echo ***** Upgrading to %PYUPGRADE_WIN_V%
    echo *** Downloading Python install exe
    curl -L -O https://www.python.org/ftp/python/%PYUPGRADE_WIN_V%/python-%PYUPGRADE_WIN_V%-amd64.exe
    if not exist python-%PYUPGRADE_WIN_V%-amd64.exe (exit /b 80)
    echo *** Installing Python %PYUPGRADE_WIN_V%
    python-%PYUPGRADE_WIN_V%-amd64.exe /quiet PrependPath=1
    if not exist %PYTHON_PATH%\python.exe (exit /b 90)
    echo ***** Upgrade Complete
    echo Python Version Now:
    python -V
)

::
:: get pip up to date
::
:: pip update to 24.1 breaks CI
::python -m pip install --upgrade pip
python -m pip install pip==24.0

:: install wheel
python -m pip install wheel

::
:: install Artisan required libraries from pip
::
python -m pip install -r src\requirements.txt | findstr /v /b "Ignoring"

:: Check that libusb-1.0.dll was installed.  Was missing once on CI with Win11.
if not exist %PYTHON_PATH%\Lib\site-packages\libusb_package\libusb-1.0.dll (
    echo *** ERROR - libusb-1.0.dll is missing from the libusb-package installation
    exit /b 95
)
::
:: custom build the pyinstaller bootloader or install a prebuilt
::
if /i "%BUILD_PYINSTALLER%"=="True" (
    echo ***** Start build pyinstaller v%PYINSTALLER_VER%
    rem
    rem download pyinstaller source
    echo ***** curl pyinstaller v%PYINSTALLER_VER%
    curl -L -O https://github.com/pyinstaller/pyinstaller/archive/refs/tags/v%PYINSTALLER_VER%.zip
    if not exist v%PYINSTALLER_VER%.zip (exit /b 100)
    7z x v%PYINSTALLER_VER%.zip
    del v%PYINSTALLER_VER%.zip
    if ERRORLEVEL 1 (exit /b 110)
    if not exist pyinstaller-%PYINSTALLER_VER%/bootloader/ (exit /b 120)
    cd pyinstaller-%PYINSTALLER_VER%/bootloader
    rem
    rem build the bootloader and wheel
    echo ***** Running WAF
    python ./waf all --msvc_targets=x64
    cd ..
    echo ***** Start build pyinstaller v%PYINSTALLER_VER% wheel
    rem redirect standard output to lower the noise in the logs
    python -m build --wheel > NUL
    if not exist dist/pyinstaller-%PYINSTALLER_VER%-py3-none-any.whl (exit /b 130)
    echo ***** Finished build pyinstaller v%PYINSTALLER_VER% wheel
    rem
    rem install pyinstaller
    echo ***** Start install pyinstaller v%PYINSTALLER_VER%
    python -m pip install -q dist/pyinstaller-%PYINSTALLER_VER%-py3-none-any.whl
    cd ..
) else (
     python -m pip install -q pyinstaller==%PYINSTALLER_VER%
)
echo ***** Finished install pyinstaller v%PYINSTALLER_VER%

::
:: download and install required libraries not available on pip
::
echo curl vc_redist.x64.exe
curl -L -O %VC_REDIST%
if not exist vc_redist.x64.exe (exit /b 140)


::
:: show set of libraries are installed
::
echo **** pip freeze ****
python -m pip freeze
