@echo off
:: ABOUT
:: Script to upgrade Python for Artisan Windows CI builds
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
:: Dave Baxter 2025
::
:: Upgrade the Python version to PYUPGRADE_WIN_VER whenever the environment variable exists
::   and the upgrade version is greater than current Python version. 
::
:: Requires environment variables set in .appveyor.yml: 
::      PYUPGRADE_WIN_VER set to the full version number for target upgrade, or blank, or non-existent.
::      PREV_PYTHON_PATH set to the python.exe path corresponding to the original environment: PYTHON_V variable.
:: Creates local scope environment variables: PREV_PYTHON_VER, INSTALLED_PYTHON_VER not available outside this script.

setlocal enabledelayedexpansion

:: If there is no upgrade version then simply return
if "%PYUPGRADE_WIN_VER%"=="" (
    goto End
)

:: Get the default Python version
if exist "%PREV_PYTHON_PATH%\python.exe" (
    for /f "tokens=2 delims= " %%a in ('%PREV_PYTHON_PATH%\python.exe -V 2^>^&1') do set "PREV_PYTHON_VER=%%a"
    ) else (
    echo **** ERROR: %PREV_PYTHON_PATH%\python.exe does not exist in the build environment
    exit /b 91
)

:: Log an informational message
echo *** Current Python Version: !PREV_PYTHON_VER!  Upgrade to: !PYUPGRADE_WIN_VER! requested

:: Check if both current and upgrade full versions match 
if "!PREV_PYTHON_VER!"=="!PYUPGRADE_WIN_VER!" (
    echo *** Versions are the same.  No need to upgrade.
    goto End
)

:: Split the version strings into components - major.minor.patch
for /f "tokens=1,2,3 delims=." %%a in ("!PREV_PYTHON_VER!") do (
    set "major_py=%%a"
    set "minor_py=%%b"
    set "patch_py=%%c"
)
for /f "tokens=1,2,3 delims=." %%a in ("!PYUPGRADE_WIN_VER!") do (
    set "major_up=%%a"
    set "minor_up=%%b"
    set "patch_up=%%c"
)

:: Compare version numbers at each level
if !major_py! lss !major_up! (
    echo **** WARNING A major release upgrade was requested.  This has never been tried before!
    goto Upgrade
) else if !major_py! gtr !major_up! (
    goto NoUpgrade
)
if !minor_py! lss !minor_up! (
    echo PYTHON_PATH !PYTHON_PATH! 
    if exist "!PYTHON_PATH!\python.exe" (
        echo !PYTHON_PATH!\python.exe EXISTS
        for /f "tokens=2 delims= " %%a in ('!PYTHON_PATH!\python -V 2^>^&1') do (
            set "INSTALLED_PYTHON_VER=%%a"
        )
        if "!INSTALLED_PYTHON_VER!"=="!PYUPGRADE_WIN_VER!" (
            echo **** WARNING Python !INSTALLED_PYTHON_VER! is already installed.  Upgrade installation is skipped.
            goto End
        )
    ) else (
        goto Upgrade
    )
) else if !minor_py! gtr !minor_up! (
    goto NoUpgrade
)
if !patch_py! lss !patch_up! (
    goto Upgrade
)
goto NoUpgrade

:Upgrade
:: Before upgrading, check whether the requested version is already
echo ***** Upgrading Python from !PREV_PYTHON_VER! to !PYUPGRADE_WIN_VER!
rem echo *** Downloading Python install exe
rem curl -L -O https://www.python.org/ftp/python/!PYUPGRADE_WIN_VER!/python-!PYUPGRADE_WIN_VER!-amd64.exe
rem if not exist python-!PYUPGRADE_WIN_VER!-amd64.exe (exit /b 80)
rem echo *** Installing Python !PYUPGRADE_WIN_VER!
rem python-!PYUPGRADE_WIN_VER!-amd64.exe /quiet PrependPath=1
rem if not exist !PYTHON_PATH!\python.exe (exit /b 90)
rem echo ***** Upgrade Complete
rem echo Python Version Now:
rem !PYTHON_PATH!\python -V
goto End

:NoUpgrade
echo **** ERROR: Python upgrade is not happening from !PREV_PYTHON_VER! to !PYUPGRADE_WIN_VER!
exit /b 92

:End
endlocal
