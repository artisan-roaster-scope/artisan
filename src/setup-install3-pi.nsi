; ABOUT
; NSIS script file for Artisan Windows installer.
;
; LICENSE
; This program or module is free software: you can redistribute it and/or
; modify it under the terms of the GNU General Public License as published
; by the Free Software Foundation, either version 2 of the License, or
; version 3 of the License, or (at your option) any later versison. It is
; provided for educational purposes and is distributed in the hope that
; it will be useful, but WITHOUT ANY WARRANTY; without even the implied
; warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
; the GNU General Public License for more details.
;
; AUTHOR
; Dave Baxter, Marko Luther 2023
;
; .nsi command line options:
;    /DPRODUCT_VERSION=ww.xx.yy     -explicitly set the product version, default is 0.0.0
;    /DPRODUCT_BUILD=zz             -explicityl set the product build, default is 0
;    /DLEGACY=True|False            -True is a build for legacy Windows, default is False
;    /DSIGN=True|False              -True if the build is part of the process to sign files, default is False
;                                    Note: SignArtisan is not a part of the ci process
;
; installer command line options
;    /S                             -silent operation

RequestExecutionLevel admin

!macro APP_ASSOCIATE_URL FILECLASS DESCRIPTION COMMANDTEXT COMMAND
  WriteRegStr HKCR "${FILECLASS}" "" `${DESCRIPTION}`
  WriteRegStr HKCR "${FILECLASS}" "URL Protocol" ""
  WriteRegStr HKCR "${FILECLASS}\shell" "" "open"
  WriteRegStr HKCR "${FILECLASS}\shell\open" "" `${COMMANDTEXT}`
  WriteRegStr HKCR "${FILECLASS}\shell\open\command" "" `${COMMAND}`
!macroend

!macro APP_ASSOCIATE EXT FILECLASS DESCRIPTION ICON COMMANDTEXT COMMAND
  ; Backup the previously associated file class
  ReadRegStr $R0 HKCR ".${EXT}" ""
  WriteRegStr HKCR ".${EXT}" "${FILECLASS}_backup" "$R0"
  WriteRegStr HKCR ".${EXT}" "" "${FILECLASS}"
  WriteRegStr HKCR "${FILECLASS}" "" `${DESCRIPTION}`
  WriteRegStr HKCR "${FILECLASS}\DefaultIcon" "" `${ICON}`
  WriteRegStr HKCR "${FILECLASS}\shell" "" "open"
  WriteRegStr HKCR "${FILECLASS}\shell\open" "" `${COMMANDTEXT}`
  WriteRegStr HKCR "${FILECLASS}\shell\open\command" "" `${COMMAND}`
!macroend

!macro APP_UNASSOCIATE EXT FILECLASS
  ; Backup the previously associated file class
  ReadRegStr $R0 HKCR ".${EXT}" `${FILECLASS}_backup`
  WriteRegStr HKCR ".${EXT}" "" "$R0"
  DeleteRegKey HKCR `${FILECLASS}`
!macroend

!macro Rmdir_Wildcard dir uid
  ; RMDIR with wildcard, dir in the form $INSTDIR\dir_with_wildcard, uid should be ${__LINE__}
  FindFirst $0 $1 ${dir}
  loop_${uid}:
    StrCmp $1 "" endloop_${uid}
    RMDIR /r "$INSTDIR\$1"
    FindNext $0 $1
    Goto loop_${uid}
  endloop_${uid}:
  FindClose $0
!macroend

!macro IsRunning
  Delete "$TEMP\25b241e1.tmp"
  nsExec::Exec "cmd /c for /f $\"tokens=1,2$\" %i in ('tasklist') do (if /i %i EQU artisan.exe fsutil file createnew $TEMP\25b241e1.tmp 0)"
  IfFileExists $TEMP\25b241e1.tmp 0 notRunning
    ;we have at least one main window active
    MessageBox MB_OK|MB_ICONEXCLAMATION "Artisan was found to be running. Please close all instances then try the installer again." /SD IDOK
    Delete "$TEMP\25b241e1.tmp"
    Quit
  notRunning:
!macroEnd


;Unused macros ------
!macro APP_ASSOCIATE_EX EXT FILECLASS DESCRIPTION ICON VERB DEFAULTVERB SHELLNEW COMMANDTEXT COMMAND
  ; Backup the previously associated file class
  ReadRegStr $R0 HKCR ".${EXT}" ""
  WriteRegStr HKCR ".${EXT}" "${FILECLASS}_backup" "$R0"
  WriteRegStr HKCR ".${EXT}" "" "${FILECLASS}"
  StrCmp "${SHELLNEW}" "0" +2
  WriteRegStr HKCR ".${EXT}\ShellNew" "NullFile" ""
  WriteRegStr HKCR "${FILECLASS}" "" `${DESCRIPTION}`
  WriteRegStr HKCR "${FILECLASS}\DefaultIcon" "" `${ICON}`
  WriteRegStr HKCR "${FILECLASS}\shell" "" `${DEFAULTVERB}`
  WriteRegStr HKCR "${FILECLASS}\shell\${VERB}" "" `${COMMANDTEXT}`
  WriteRegStr HKCR "${FILECLASS}\shell\${VERB}\command" "" `${COMMAND}`
!macroend

!macro APP_ASSOCIATE_ADDVERB FILECLASS VERB COMMANDTEXT COMMAND
  WriteRegStr HKCR "${FILECLASS}\shell\${VERB}" "" `${COMMANDTEXT}`
  WriteRegStr HKCR "${FILECLASS}\shell\${VERB}\command" "" `${COMMAND}`
!macroend

!macro APP_ASSOCIATE_REMOVEVERB FILECLASS VERB
  DeleteRegKey HKCR `${FILECLASS}\shell\${VERB}`
!macroend

!macro APP_ASSOCIATE_GETFILECLASS OUTPUT EXT
  ReadRegStr ${OUTPUT} HKCR ".${EXT}" ""
!macroend

; !defines for use with SHChangeNotify
!ifdef SHCNE_ASSOCCHANGED
  !undef SHCNE_ASSOCCHANGED
!endif
!define SHCNE_ASSOCCHANGED 0x08000000
!ifdef SHCNF_FLUSH
  !undef SHCNF_FLUSH
!endif
!define SHCNF_FLUSH        0x1000

!macro UPDATEFILEASSOC
; Using the system.dll plugin to call the SHChangeNotify Win32 API function so we
; can update the shell.
  System::Call "shell32::SHChangeNotify(i,i,i,i) (${SHCNE_ASSOCCHANGED}, ${SHCNF_FLUSH}, 0, 0)"
!macroend
;End Unused macros ------


; HM NIS Edit Wizard helper defines
!define pyinstallerOutputDir 'dist/artisan'
!define PRODUCT_NAME "Artisan"
!define PRODUCT_PUBLISHER "The Artisan Team"
!define PRODUCT_WEB_SITE "https://github.com/artisan-roaster-scope/artisan/blob/master/README.md"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\artisan.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; Special commandline options
; Product version and build can be defined on the command line '/DPRODUCT_VERSION=ww.xx.yy'
;   and '/DPRODUCT_VERSION=zz' These will override the default version an build explicitly set below.
!define /ifndef PRODUCT_VERSION "0.0.0"
!define /ifndef PRODUCT_BUILD "0"
!define /ifndef SIGN "False"
!define /ifndef LEGACY "False"
!if ${LEGACY} == "True"
  !define LEGACY_STR "-legacy"
!else
  !define LEGACY_STR ""
!endif

!define /date CUR_YEAR "%Y"
Caption "${PRODUCT_NAME} Installer"

VIProductVersion "${PRODUCT_VERSION}.${PRODUCT_BUILD}"
VIAddVersionKey ProductName "${PRODUCT_NAME}"
VIAddVersionKey Comments "Installer for Artisan"
VIAddVersionKey CompanyName ""
VIAddVersionKey LegalCopyright "Copyright 2010-${CUR_YEAR}, Artisan developers. GNU General Public License"
VIAddVersionKey FileVersion "${PRODUCT_VERSION}.${PRODUCT_BUILD}"
VIAddVersionKey FileDescription "${PRODUCT_NAME} Installer"
VIAddVersionKey ProductVersion "${PRODUCT_VERSION}.${PRODUCT_BUILD}"

SetCompressor lzma

!include x64.nsh

; MUI 1.67 compatible ------
!include "MUI.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "artisan.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Welcome page
!insertmacro MUI_PAGE_WELCOME
; Directory page
!insertmacro MUI_PAGE_DIRECTORY
; Instfiles page
!insertmacro MUI_PAGE_INSTFILES
; Finish page
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

; Reserve files
!insertmacro MUI_RESERVEFILE_INSTALLOPTIONS

; MUI end ------

Name "${PRODUCT_NAME}"
OutFile "artisan-win-x64${LEGACY_STR}-${PRODUCT_VERSION}-setup.exe"
InstallDir "C:\Program Files\Artisan"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

!include WinVer.nsh

Function .onInit
  ${If} ${LEGACY} == "False"
  ${AndIfNot} ${AtLeastWin10}
    MessageBox mb_iconStop "Artisan requires Windows 10 or later to install and run."
    Abort
  ${EndIf}

  ${If} ${LEGACY} == "True"
  ${AndIf} ${AtLeastWin10}
    MessageBox mb_iconStop "Artisan Legacy builds require 64 bit Windows 7 or Windows 8 to install and run."
    Abort
  ${EndIf}

  ${If} ${LEGACY} == "True"
  ${AndIfNot} ${AtLeastWin7}
    MessageBox mb_iconStop "Artisan Legacy builds require 64 bit Windows 7 or Windows 8 to install and run."
    Abort
  ${EndIf}
  !insertmacro IsRunning

  ${If} ${RunningX64}
    ReadRegStr $R0 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" \
    "UninstallString"
    StrCmp $R0 "" done

    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
    "${PRODUCT_NAME} is already installed. $\n$\nClick `OK` to remove the \
    previous version or `Cancel` to cancel this upgrade." /SD IDOK \
    IDOK uninst
    Abort
  ${Else}
    MessageBox MB_OK "You are not using a 64bit system.\nSorry, we can not install Artisan on your system."
    Abort
  ${EndIf}

  ;Run the uninstaller
  uninst:
    ClearErrors
    IfSilent mysilent nosilent

  mysilent:
    ExecWait '$R0 /S _?=$INSTDIR' ;Do not copy the uninstaller to a temp file
    IfErrors no_remove_uninstaller done

  nosilent:
    ExecWait '$R0 _?=$INSTDIR' ;Do not copy the uninstaller to a temp file
    IfErrors no_remove_uninstaller done

  no_remove_uninstaller:
      ;You can either use Delete /REBOOTOK in the uninstaller or add some code
      ;here to remove the uninstaller. Use a registry key to check
      ;whether the user has chosen to uninstall. If you are using an uninstaller
      ;components page, make sure all sections are uninstalled.

  done:
FunctionEnd



Section "MainSection" SEC01
  SetShellVarContext all
  SetOutPath "$INSTDIR"
  SetOverwrite on
  File /r '${pyinstallerOutputDir}\*.*'
  CreateDirectory "$SMPROGRAMS\Artisan"
  CreateShortCut "$SMPROGRAMS\Artisan\Artisan.lnk" "$INSTDIR\artisan.exe"
  CreateShortCut "$DESKTOP\Artisan.lnk" "$INSTDIR\artisan.exe"
SectionEnd

Section "Microsoft Visual C++ Redistributable Package (x64)" SEC02
  ExecWait '$INSTDIR\vc_redist.x64.exe /install /passive /norestart'
  Delete '$INSTDIR\vc_redist.x64.exe'
SectionEnd

Section -AdditionalIcons
  SetShellVarContext all
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\Artisan\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\Artisan\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  ;The generated uninst.exe file needs to be redirected when signing so the signed uninstaller is packed. Include '/DSign="True"' on the command line.
  !if ${Sign} S== "True"
    WriteUninstaller "$%TEMP%\uninst.exe"
  !else
    WriteUninstaller "$INSTDIR\uninst.exe"
  !endif

  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\artisan.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "Path" "$INSTDIR"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\artisan.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}.${PRODUCT_BUILD}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"

  ; file associations
  !insertmacro APP_ASSOCIATE "alog" "Artisan.Profile" "Artisan Roast Profile" \
     "$INSTDIR\artisanProfile.ico" "Open with Artisan" "$INSTDIR\artisan.exe $\"%1$\""

  !insertmacro APP_ASSOCIATE "alrm" "Artisan.Alarms" "Artisan Alarms" \
     "$INSTDIR\artisanAlarms.ico" "Open with Artisan" "$INSTDIR\artisan.exe $\"%1$\""

  !insertmacro APP_ASSOCIATE "apal" "Artisan.Palettes" "Artisan Palettes" \
     "$INSTDIR\artisanPalettes.ico" "Open with Artisan" "$INSTDIR\artisan.exe $\"%1$\""

  !insertmacro APP_ASSOCIATE "athm" "Artisan.Theme" "Artisan Theme" \
     "$INSTDIR\artisanTheme.ico" "Open with Artisan" "$INSTDIR\artisan.exe $\"%1$\""

  !insertmacro APP_ASSOCIATE "aset" "Artisan.Settings" "Artisan Settings" \
     "$INSTDIR\artisanSettings.ico" "Open with Artisan" "$INSTDIR\artisan.exe $\"%1$\""

  !insertmacro APP_ASSOCIATE "wg" "Artisan.Wheel" "Artisan Wheel" \
     "$INSTDIR\artisanWheel.ico" "Open with Artisan" "$INSTDIR\artisan.exe $\"%1$\""

  !insertmacro APP_ASSOCIATE_URL "artisan" "URL:artisan Protocol" \
     "Open with URL" "$INSTDIR\artisan.exe $\"%1$\""

SectionEnd


Function un.onUninstSuccess
  HideWindow
  IfSilent +2 0
    MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer." /SD IDOK
FunctionEnd

Function un.onInit
    !insertmacro IsRunning

    IfSilent +3
        MessageBox MB_ICONQUESTION|MB_YESNO|MB_TOPMOST "Are you sure you want to remove $(^Name)?" IDYES +2
        Abort
    HideWindow

FunctionEnd

Section Uninstall
  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\artisan.exe"
  Delete "$INSTDIR\artisan.exe.manifest"
  Delete "$INSTDIR\*.pyd"
  Delete "$INSTDIR\*.dll"
  Delete "$INSTDIR\base_library.zip"

  RMDir /r "$INSTDIR\certifi"
  RMDir /r "$INSTDIR\charset_normalizer"
  RMDir /r "$INSTDIR\contourpy"
  RMDir /r "$INSTDIR\fontTools"
  RMDir /r "$INSTDIR\gevent"
  RMDir /r "$INSTDIR\google"
  RMDir /r "$INSTDIR\greenlet"
  RMDir /r "$INSTDIR\Icons"
  RMDir /r "$INSTDIR\Include"
  RMDir /r "$INSTDIR\kiwisolver"
  RMDir /r "$INSTDIR\lib"
  RMDir /r "$INSTDIR\lib2to3"
  RMDir /r "$INSTDIR\lxml"
  RMDir /r "$INSTDIR\Machines"
  RMDir /r "$INSTDIR\markupsafe"
  RMDir /r "$INSTDIR\matplotlib"
  RMDir /r "$INSTDIR\matplotlib.libs"
  RMDir /r "$INSTDIR\mpl-data"
  RMDir /r "$INSTDIR\numpy"
  RMDir /r "$INSTDIR\openpyxl"
  RMDir /r "$INSTDIR\PIL"
  RMDir /r "$INSTDIR\psutil"
  RMDir /r "$INSTDIR\pyinstaller"
  RMDir /r "$INSTDIR\pytz"
  RMDir /r "$INSTDIR\pywin32_system32"
  RMDir /r "$INSTDIR\scipy"
  RMDir /r "$INSTDIR\scipy.libs"
  RMDir /r "$INSTDIR\tcl"
  RMDir /r "$INSTDIR\tcl8"
  RMDir /r "$INSTDIR\Themes"
  RMDir /r "$INSTDIR\tk"
  RMDir /r "$INSTDIR\tornado"
  RMDir /r "$INSTDIR\translations"
  RMDir /r "$INSTDIR\wcwidth"
  RMDir /r "$INSTDIR\websockets"
  RMDir /r "$INSTDIR\Wheels"
  RMDir /r "$INSTDIR\win32com"
  RMDir /r "$INSTDIR\win32"
  RMDir /r "$INSTDIR\wx"
  RMDir /r "$INSTDIR\yaml"
  RMDir /r "$INSTDIR\yoctopuce"
  RMDir /r "$INSTDIR\zope"

  RMDir /r "$INSTDIR\_internal"

  !insertmacro Rmdir_Wildcard "$INSTDIR\PyQt*" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\qt*_plugins" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\altgraph*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\cffi*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\gevent*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\gevent*.egg-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\greenlet*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\importlib_metadata*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\importlib_metadata*.egg-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\keyring*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\keyring*.egg-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\prettytable*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\prettytable*.egg-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\pycparser*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\pyinstaller*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\python_snap7*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\setuptools*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\websockets*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\wheel*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\zope.event*.dist-info" ${__LINE__}
  !insertmacro Rmdir_Wildcard "$INSTDIR\zope.interface*.dist-info" ${__LINE__}

  Delete "$INSTDIR\artisan.png"
  Delete "$INSTDIR\LICENSE.txt"
  Delete "$INSTDIR\README.txt"
  Delete "$INSTDIR\artisanAlarms.ico"
  Delete "$INSTDIR\artisanProfile.ico"
  Delete "$INSTDIR\artisanPalettes.ico"
  Delete "$INSTDIR\artisanTheme.ico"
  Delete "$INSTDIR\artisanWheel.ico"
  Delete "$INSTDIR\artisanSettings.ico"
  Delete "$INSTDIR\Humor-Sans.ttf"
  Delete "$INSTDIR\dijkstra.ttf"
  Delete "$INSTDIR\xkcd-script.ttf"
  Delete "$INSTDIR\ComicNeue-Regular.ttf"
  Delete "$INSTDIR\WenQuanYiZenHei-01.ttf"
  Delete "$INSTDIR\WenQuanYiZenHeiMonoMedium.ttf"
  Delete "$INSTDIR\SourceHanSansCN-Regular.otf"
  Delete "$INSTDIR\SourceHanSansHK-Regular.otf"
  Delete "$INSTDIR\SourceHanSansJP-Regular.otf"
  Delete "$INSTDIR\SourceHanSansKR-Regular.otf"
  Delete "$INSTDIR\SourceHanSansTW-Regular.otf"
  Delete "$INSTDIR\alarmclock.eot"
  Delete "$INSTDIR\alarmclock.svg"
  Delete "$INSTDIR\alarmclock.ttf"
  Delete "$INSTDIR\alarmclock.woff"
  Delete "$INSTDIR\android-chrome-192x192.png"
  Delete "$INSTDIR\android-chrome-512x512.png"
  Delete "$INSTDIR\apple-touch-icon.png"
  Delete "$INSTDIR\browserconfig.xml"
  Delete "$INSTDIR\favicon-16x16.png"
  Delete "$INSTDIR\favicon-32x32.png"
  Delete "$INSTDIR\favicon.ico"
  Delete "$INSTDIR\mstile-150x150.png"
  Delete "$INSTDIR\safari-pinned-tab.svg"
  Delete "$INSTDIR\site.webmanifest"
  Delete "$INSTDIR\artisan.tpl"
  Delete "$INSTDIR\bigtext.js"
  Delete "$INSTDIR\sorttable.js"
  Delete "$INSTDIR\report-template.htm"
  Delete "$INSTDIR\roast-template.htm"
  Delete "$INSTDIR\ranking-template.htm"
  Delete "$INSTDIR\jquery-1.11.1.min.js"
  Delete "$INSTDIR\qt.conf"
  Delete "$INSTDIR\vc_redist.x64.exe"
  Delete "$INSTDIR\logging.yaml"

  SetShellVarContext all
  Delete "$SMPROGRAMS\Artisan\Uninstall.lnk"
  Delete "$SMPROGRAMS\Artisan\Website.lnk"
  Delete "$DESKTOP\Artisan.lnk"
  Delete "$SMPROGRAMS\Artisan\Artisan.lnk"

  RMDir "$SMPROGRAMS\Artisan"
  RMDir "$INSTDIR"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  DeleteRegKey HKCR ".alog"
  DeleteRegKey HKCR "Artisan.Profile\DefaultIcon"
  DeleteRegKey HKCR "Artisan.Profile\shell"
  DeleteRegKey HKCR "Artisan.Profile\shell\open\command"
  DeleteRegKey HKCR "Artisan.Profile"

  !insertmacro APP_UNASSOCIATE "alog" "Artisan.Profile"
  !insertmacro APP_UNASSOCIATE "alrm" "Artisan.Alarms"
  !insertmacro APP_UNASSOCIATE "apal" "Artisan.Palettes"
  !insertmacro APP_UNASSOCIATE "athm" "Artisan.Theme"
  !insertmacro APP_UNASSOCIATE "aset" "Artisan.Settings"
  !insertmacro APP_UNASSOCIATE "wg" "Artisan.Wheel"

  DeleteRegKey HKCR "artisan\shell"
  DeleteRegKey HKCR "artisan\shell\open\command"
  DeleteRegKey HKCR "artisan"

  SetAutoClose true
SectionEnd
