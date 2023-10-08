:: ABOUT
:: Windows batch file to generate translation, ui and help files derived
:: on sources in the Artisan repository.
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

:: on entry to this script the current path must be the src folder
::
:: script commandline option LEGACY used to flag a legacy build
::

@echo off
:: test for existence of required environment variables
setlocal enabledelayedexpansion
if not defined QT_PATH (
    echo QT_PATH not set, be sure Qt 6.x is installed.
    echo Set QT_PATH appropriately, something like C:\Qt\6.4\msvc2019_64.  Exiting...
    exit /b 1
)
if not defined PYTHON_PATH (
    if defined PYTHONPATH (
        set PYTHON_PATH=%PYTHONPATH%
        echo PYTHON_PATH not set, defaulting to %PYTHONPATH%
    ) else (
        echo PYTHON_PATH not set, set it manually.  Exiting...
        exit /b 1
    )
)
if not defined ARTISAN_LEGACY (
    echo ARTISAN_LEGACY not set, defaulting to False
    set ARTISAN_LEGACY=False
    set ARTISAN_SPEC=win
)
if not defined ARTISAN_SPEC (
    echo ARTISAN_SPEC not set.
    echo Set it manually to win or win-legacy.  Exiting...
    exit /b 1
)
if not defined PYUIC (
    echo PYUIC not set, defaulting to pyuic6.exe
    set PYUIC=pyuic6.exe
)

::
:: Generate translation, ui, and help files derived from repository sources
::

:: convert help files from .xlsx to .py
echo ************* help files **************
python ..\doc\help_dialogs\Script\xlsx_to_artisan_help.py all
if ERRORLEVEL 1 (echo ** Failed in xlsx_to_artisan_help.py & exit /b 1) else (echo ** Success)

:: convert .ui files to .py files
echo ************* ui/uic **************
for /r %%a IN (ui\*.ui) DO (
    echo %%~na
    %PYUIC% -o uic\%%~na.py ui\%%~na.ui
    if ERRORLEVEL 1 (echo ** Failed in pyuic & exit /b 1)
)
echo ** Success

:: Process translation files
echo ************* pylupdate **************
if /i "%ARTISAN_LEGACY%" == "True" (
    echo *** Processing translation files defined in artisan.pro with pylupdate5.py
    %PYTHON_PATH%\Scripts\pylupdate5.exe artisan.pro
    if ERRORLEVEL 1 (echo ** Failed in pylupdate5.py & exit /b 1) else (echo ** Success)
) else (
    echo *** Processing translation files with pylupdate6pro.py
    python pylupdate6pro.py
    if ERRORLEVEL 1 (echo ** Failed in pylupdate6pro.py & exit /b 1) else (echo ** Success)
)
echo ************* lrelease **************
cd translations
for /r %%a IN (*.ts) DO (
    qt%PYQT%-tools lrelease %%~a
    if ERRORLEVEL 1 (echo ** Failed in qt%PYQT%-tools lrelease step 2 & exit /b 1)
)
echo ** Success
cd ..

:: Zip the generated files
7z a ..\generated-%ARTISAN_SPEC%.zip ..\doc\help_dialogs\Output_html\ help\ translations\ uic\
if ERRORLEVEL 1 (echo ** Failed in 7z & exit /b 1) else (echo ** Success)
::
::  End of generating derived files
::
