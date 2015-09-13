@echo off

rem # set PY2EXE_VERBOSE=1

C:\Python34\python setup-win3.py py2exe
rem # C:\Python34\python -m py2exe.build_exe artisan.py

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
%NSIS_EXE% setup-install3.nsi


rem #
rem # Backup - use the one found in the path
rem #
set NSIS_EXE
if %ERRORLEVEL% NEQ 0 set NSIS_EXE="makensis.exe"