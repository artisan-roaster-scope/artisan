@echo off
:: the current directory on entry to this script must be the folder above src
::
:: script comandline option LEGACY used to flag a legacy build
::

:: ----------------------------------------------------------------------
:: normally these paths are set in appveyor.yml
:: when running locally these paths must be set here 
:: CAUTION: the paths in this section are not gurantted to be to date!! 
:: ----------------------------------------------------------------------
setlocal enabledelayedexpansion
if /i "%APPVEYOR%" NEQ "True" (
    if /i "%~1" == "LEGACY" (
        set ARTISAN_SPEC=win-legacy
        set PYTHON_PATH=c:\Python38-64
        set QT_PATH=c:\qt\5.15\msvc2019_64
        set PYINSTALLER_VER=5.5
        set LIBUSB_VER=1.2.6.0
        set BUILD_PYINSTALLER=False
        set VC_REDIST=https://aka.ms/vs/16/release/vc_redist.x64.exe
    ) else (
        set ARTISAN_SPEC=win
        set PYTHON_PATH=c:\Python310-64
        set QT_PATH=c:\qt\6.2\msvc2019_64
        set PYINSTALLER_VER=5.5
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

echo Python Version
%PYTHON_PATH%\python -V

::
:: get pip up to date
::
%PYTHON_PATH%\python.exe -m pip install --upgrade pip
%PYTHON_PATH%\python.exe -m pip install wheel

::
:: install Artisan required libraries from pip
::
%PYTHON_PATH%\python.exe -m pip install -r src\requirements.txt
%PYTHON_PATH%\python.exe -m pip install -r src\requirements-%ARTISAN_SPEC%.txt

::
:: custom build the pyinstaller bootloader or install a prebuilt
::
if /i "%BUILD_PYINSTALLER%"=="True" (
    echo ***** Start build pyinstaller v%PYINSTALLER_VER%
    ::
    :: download pyinstaller source
    echo ***** curl pyinstaller v%PYINSTALLER_VER%
    curl -L -O https://github.com/pyinstaller/pyinstaller/archive/refs/tags/v%PYINSTALLER_VER%.zip
    if not exist v%PYINSTALLER_VER%.zip (exit /b 100)
    7z x v%PYINSTALLER_VER%.zip
    del v%PYINSTALLER_VER%.zip
    if not exist pyinstaller-%PYINSTALLER_VER%\bootloader\ (exit /b 101)
    cd pyinstaller-%PYINSTALLER_VER%\bootloader
    ::
    :: build the bootlaoder and wheel
    echo ***** Running WAF
    %PYTHON_PATH%\python.exe ./waf all --target-arch=64bit
    cd ..
    ::setup install is deprecated
    ::%PYTHON_PATH%\python.exe setup.py -q install
    echo ***** Building Wheel
    %PYTHON_PATH%\python.exe setup.py -q bdist_wheel
    if not exist dist\\pyinstaller-%PYINSTALLER_VER%-py3-none-any.whl (exit /b 102)
    echo ***** Finished build pyinstaller v%PYINSTALLER_VER%
    ::
    :: install pyinstaller
    echo ***** Start install pyinstaller v%PYINSTALLER_VER%
    %PYTHON_PATH%\python.exe -m pip install -q dist\\pyinstaller-%PYINSTALLER_VER%-py3-none-any.whl
    cd ..
) else (
    if not exist .ci\\pyinstaller-%PYINSTALLER_VER%-py3-none-any.whl (exit /b 103)
    echo ***** Start install pyinstaller v%PYINSTALLER_VER%
    %PYTHON_PATH%\\python.exe -m pip install -q .ci\\pyinstaller-%PYINSTALLER_VER%-py3-none-any.whl
)
echo ***** Finished installing pyinstaller v%PYINSTALLER_VER%

::
:: download and install required libraries not available on pip
::
echo curl vc_redist.x64.exe
curl -L -O %VC_REDIST%
if not exist vc_redist.x64.exe (exit /b 104)

:: snap7 binaries are now included in the pip install thus no longer downloaded
::echo curl snap7
::curl -k -L -O https://netcologne.dl.sourceforge.net/project/snap7/1.4.2/snap7-full-1.4.2.7z
::7z x snap7-full-1.4.2.7z
::copy snap7-full-1.4.2\build\bin\win64\snap7.dll c:\windows

::
:: copy the snap7 binary
::
copy %PYTHON_PATH%\Lib\site-packages\snap7\lib\snap7.dll C:\Windows

::
:: download and copy the libusb-win32 dll. NOTE-the version number for appveypr builds is set in the requirements-win*.txt file.
::
echo curl libusb-win32
curl -k -L -O https://netcologne.dl.sourceforge.net/project/libusb-win32/libusb-win32-releases/%LIBUSB_VER%/libusb-win32-bin-%LIBUSB_VER%.zip
if not exist libusb-win32-bin-%LIBUSB_VER%.zip (exit /b 105)
7z x libusb-win32-bin-%LIBUSB_VER%.zip
copy libusb-win32-bin-%LIBUSB_VER%\bin\amd64\libusb0.dll C:\Windows\SysWOW64
