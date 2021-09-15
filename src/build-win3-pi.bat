@echo off

rem comandline potion LEGACY used to flag a legacy build in NSIS
if "%~1" == "LEGACY"  (set ARTISAN_LEGACY="True") else (set ARTISAN_LEGACY="False")


pyinstaller --noconfirm artisan-win.spec

rem #
rem # Don't make assumptions as to where the 'makensis.exe' is - look in the obvious places
rem #
if exist "C:\Program Files (x86)\NSIS\makensis.exe" set NSIS_EXE="C:\Program Files (x86)\NSIS\makensis.exe"
if exist "C:\Program Files\NSIS\makensis.exe"       set NSIS_EXE="C:\Program Files\NSIS\makensis.exe"
if exist "%ProgramFiles%\NSIS\makensis.exe"         set NSIS_EXE="%ProgramFiles%\NSIS\makensis.exe"
if exist "%ProgramFiles(x86)%\NSIS\makensis.exe"    set NSIS_EXE="%ProgramFiles(x86)%\NSIS\makensis.exe"

rem #
rem #
rem #
FOR /F "usebackq delims==" %%a IN (`python -c "import artisanlib; print(artisanlib.__version__)"`) DO (set ARTISAN_VERSION=%%~a)
rem FOR /F "usebackq delims==" %%a IN (`python -c "import artisanlib; print(artisanlib.__revision__)"`) DO (set ARTISAN_REVISION=%%~a)
FOR /F "usebackq delims==" %%a IN (`python -c "import artisanlib; print(artisanlib.__build__)"`) DO (set ARTISAN_BUILD=%%~a)
%NSIS_EXE% /DPRODUCT_VERSION=%ARTISAN_VERSION%.%ARTISAN_BUILD% /DLEGACY=%ARTISAN_LEGACY% setup-install3-pi.nsi