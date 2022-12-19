@echo off
:: on entry to this script the current path must be the src folder
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
        set ARTISAN_LEGACY=True
        set PYUIC=pyuic5.exe
        set QT_PATH=c:\qt\5.15\msvc2019_64
    ) else (
        set ARTISAN_SPEC=win
        set PYTHON_PATH=c:\Python311-64
        set ARTISAN_LEGACY=False
        set PYUIC=pyuic6.exe
        set QT_PATH=c:\qt\6.4\msvc2022_64
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

::
:: convert .ui files to .py files
::
for /r %%a IN (ui\*.ui) DO (
    echo %%~na
    rem %PYUIC% -o uic\%%~na.py --from-imports ui\%%~na.ui
    %PYUIC% -o uic\%%~na.py ui\%%~na.ui
)

::
:: convert help files from .xlsx to .py
::
%PYTHON_PATH%\python.exe ..\doc\help_dialogs\Script\xlsx_to_artisan_help.py all

::
:: Process translation files
::
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsall.bat" x86_amd64
echo Processing translation files defined in artisan.pro
%QT_PATH%\bin\lrelease -verbose artisan.pro
echo Processing translation qtbase_*.ts files
for /r %%a IN (translations\qtbase_*.ts) DO (
    %QT_PATH%\bin\lrelease -verbose %%~a
)

::
:: run pyinstaller and NSIS to gnerate the install .exe
::
:: set environment variables for version and build
for /f "usebackq delims==" %%a IN (`python -c "import artisanlib; print(artisanlib.__version__)"`) DO (set ARTISAN_VERSION=%%~a)
for /f "usebackq delims==" %%a IN (`python -c "import artisanlib; print(artisanlib.__build__)"`) DO (set ARTISAN_BUILD=%%~a)
::
:: create a version file for pyinstaller
create-version-file version-metadata.yml --outfile version_info-win.txt --version %ARTISAN_VERSION%.%ARTISAN_BUILD%
::
:: run pyinstaller
pyinstaller --noconfirm artisan-%ARTISAN_SPEC%.spec
::
:: Don't make assumptions as to where the 'makensis.exe' is - look in the obvious places
if exist "C:\Program Files (x86)\NSIS\makensis.exe" set NSIS_EXE="C:\Program Files (x86)\NSIS\makensis.exe"
if exist "C:\Program Files\NSIS\makensis.exe"       set NSIS_EXE="C:\Program Files\NSIS\makensis.exe"
if exist "%ProgramFiles%\NSIS\makensis.exe"         set NSIS_EXE="%ProgramFiles%\NSIS\makensis.exe"
if exist "%ProgramFiles(x86)%\NSIS\makensis.exe"    set NSIS_EXE="%ProgramFiles(x86)%\NSIS\makensis.exe"
::
:: echo the file date since makensis does not have a version command
for %%x in (%NSIS_EXE%) do set NSIS_DATE=%%~tx
echo NSIS makensis.exe file date %NSIS_DATE%
::
:: run NSIS to build the install .exe file
%NSIS_EXE% /DPRODUCT_VERSION=%ARTISAN_VERSION%.%ARTISAN_BUILD% /DLEGACY=%ARTISAN_LEGACY% setup-install3-pi.nsi
if ERRORLEVEL 1 (exit /b 1)

::
:: package the zip file
::
if /i "%APPVEYOR%" == "True" (
    copy ..\LICENSE LICENSE.txt
    7z a artisan-%ARTISAN_SPEC%-%ARTISAN_VERSION%.zip Setup*.exe LICENSE.txt README.txt
)

::
:: check the approximate size of the zip file  
::
set file=artisan-%ARTISAN_SPEC%-%ARTISAN_VERSION%.zip
set expectedbytesize=170000000
for %%A in (%file%) do set size=%%~zA
if %size% LSS %expectedbytesize% (
    echo ***Zip file is smaller than expected
    exit /b 1
)
