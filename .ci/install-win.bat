@echo off
:: ABOUT
:: CI install script for Artisan Windows builds
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
::
:: script comandline option LEGACY used to flag a legacy build
::

:: ----------------------------------------------------------------------
:: normally these paths are set in appveyor.yml
:: when running locally these paths must be set here 
:: CAUTION: the paths in this section are not gurantted to be up to date!! 
:: ----------------------------------------------------------------------
setlocal enabledelayedexpansion
if /i "%APPVEYOR%" NEQ "True" (
    if /i "%~1" == "LEGACY" (
        set ARTISAN_SPEC=win-legacy
        set PYTHON_PATH=c:\Python38-64
        set QT_PATH=c:\qt\5.15\msvc2019_64
        set PYINSTALLER_VER=5.7
        set LIBUSB_VER=1.2.6.0
        set BUILD_PYINSTALLER=False
        set VC_REDIST=https://aka.ms/vs/16/release/vc_redist.x64.exe
    ) else (
        set ARTISAN_SPEC=win
        set PYTHON_PATH=c:\Python311-64
        set QT_PATH=c:\qt\6.4\msvc2022_64
        set PYINSTALLER_VER=5.7
        set LIBUSB_VER=1.2.6.0
        set BUILD_PYINSTALLER=True
        set VC_REDIST=https://aka.ms/vs/17/release/vc_redist.x64.exe
    )
    set PATH=!PYTHON_PATH!;!PYTHON_PATH!\Scripts;!PATH!
) else (
    if /i "%ARTISAN_LEGACY%" NEQ "True" (
        set ARTISAN_SPEC=win
    ) else (
        set ARTISAN_SPEC=win-legacy
    )
)
:: ----------------------------------------------------------------------

ver
echo Python Version
python -V

::
:: get pip up to date
::
python -m pip install --upgrade pip
python -m pip install wheel

::
:: install Artisan required libraries from pip
::
python -m pip install -r src\requirements.txt
python -m pip install -r src\requirements-%ARTISAN_SPEC%.txt

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
    if not exist pyinstaller-%PYINSTALLER_VER%/bootloader/ (exit /b 101)
    cd pyinstaller-%PYINSTALLER_VER%/bootloader
    rem
    rem build the bootloader and wheel
    echo ***** Running WAF
    python ./waf all --msvc_targets=x64
    cd ..
    echo ***** Start build pyinstaller v%PYINSTALLER_VER% wheel
    rem redirect standard output to lower the noise in the logs
    python -m build --wheel > NUL
    if not exist dist/pyinstaller-%PYINSTALLER_VER%-py3-none-any.whl (exit /b 102)
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
if not exist vc_redist.x64.exe (exit /b 104)

::
:: copy the snap7 binary
::
copy "%PYTHON_PATH%\Lib\site-packages\snap7\lib\snap7.dll" "C:\Windows"
if not exist "C:\Windows\snap7.dll" (exit /b 105)

::
:: download and copy the libusb-win32 dll. NOTE-the version number for libusb is set in the requirements-win*.txt file.
::
echo curl libusb-win32
curl -k -L -O https://netcologne.dl.sourceforge.net/project/libusb-win32/libusb-win32-releases/%LIBUSB_VER%/libusb-win32-bin-%LIBUSB_VER%.zip
if not exist libusb-win32-bin-%LIBUSB_VER%.zip (exit /b 106)
7z x libusb-win32-bin-%LIBUSB_VER%.zip
copy "libusb-win32-bin-%LIBUSB_VER%\bin\amd64\libusb0.dll" "C:\Windows\SysWOW64"
if not exist "C:\Windows\SysWOW64\libusb0.dll" (exit /b 107)
