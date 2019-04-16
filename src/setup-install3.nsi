
RequestExecutionLevel admin

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

!macro APP_UNASSOCIATE EXT FILECLASS
  ; Backup the previously associated file class
  ReadRegStr $R0 HKCR ".${EXT}" `${FILECLASS}_backup`
  WriteRegStr HKCR ".${EXT}" "" "$R0"
 
  DeleteRegKey HKCR `${FILECLASS}`
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


; HM NIS Edit Wizard helper defines
!define py2exeOutputDir 'dist'
!define PRODUCT_NAME "Artisan"
!define PRODUCT_VERSION "1.6.99.0"
!define PRODUCT_PUBLISHER "The Artisan Team"
!define PRODUCT_WEB_SITE "https://github.com/artisan-roaster-scope/artisan/blob/master/README.md"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\artisan.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

;!define MSVC2008 "http://download.microsoft.com/download/1/1/1/1116b75a-9ec3-481a-a3c8-1777b5381140/vcredist_x86.exe"

Caption "${PRODUCT_NAME} Installer"
VIProductVersion ${PRODUCT_VERSION}
VIAddVersionKey ProductName "${PRODUCT_NAME}"
VIAddVersionKey Comments "Installer for Artisan"
VIAddVersionKey CompanyName ""
VIAddVersionKey LegalCopyright Artisan.org
VIAddVersionKey FileVersion "${PRODUCT_VERSION}"
VIAddVersionKey FileDescription "${PRODUCT_NAME} ${PRODUCT_VERSION} Installer"
VIAddVersionKey ProductVersion "${PRODUCT_VERSION}"

SetCompressor lzma

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
OutFile "Setup-${PRODUCT_NAME}-${PRODUCT_VERSION}.exe"
InstallDir "C:\Program Files\Artisan"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Function .onInit
 
  ReadRegStr $R0 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" \
  "UninstallString"
  StrCmp $R0 "" done  
 
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
  "${PRODUCT_NAME} is already installed. $\n$\nClick `OK` to remove the \
  previous version or `Cancel` to cancel this upgrade." /SD IDOK \
  IDOK uninst
  Abort
 
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


Function CheckRedistributableInstalled

  ;{F0C3E5D1-1ADE-321E-8167-68EF0DE699A5} - msvs2010 sp1
  
  Push $R0
  ClearErrors
   
  ;try to read Version subkey to R0
  ReadRegDword $R0 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{F0C3E5D1-1ADE-321E-8167-68EF0DE699A5}" "Version"

  ;was there error or not?
  IfErrors 0 NoErrors
   
  ;error occured, copy "Error" to R0
  StrCpy $R0 "Error"

  NoErrors:
  
    Exch $R0 
FunctionEnd


Section "MainSection" SEC01
  SetShellVarContext all
  SetOutPath "$INSTDIR"
  SetOverwrite on
  File /r '${py2exeOutputDir}\*.*'
  CreateDirectory "$SMPROGRAMS\Artisan"
  CreateShortCut "$SMPROGRAMS\Artisan\Artisan.lnk" "$INSTDIR\artisan.exe"
  CreateShortCut "$DESKTOP\Artisan.lnk" "$INSTDIR\artisan.exe"
SectionEnd

; -----------------------------------------------------------------------
; MSVC Redistributable - required if the user does not already have it
; Note: if your NSIS generates an error here it means you need to download the latest
; visual studio redist package from microsoft.  Any redist 2008/SP1 or newer will do.
;
; IMPORTANT: Online references for how to detect the presence of the VS2008 redists LIE.
; None of the methods are reliable, because the registry keys placed by the MSI installer
; vary depending on operating system *and* MSI installer version (youch).
;
;Section -VC++2008Runtime SEC02
;  SetOutPath $INSTDIR
;  ; Check if VC++ 2008 runtimes are already installed:
;;  ReadRegStr $0 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{FF66E9F6-83E7-3A3E-AF14-8DE9A809A6A4}" "DisplayName"
;  ; If VC++ 2008 runtimes are not installed execute in Quiet mode
;;  StrCmp $0 "Microsoft Visual C++ 2008 Redistributable - x86 9.0.21022" done
;  ClearErrors
;  ReadRegDword $R0 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{FF66E9F6-83E7-3A3E-AF14-8DE9A809A6A4}" "Version"
;  ; if VS 2005+ redist SP1 not installed, install it
;  IfErrors 0 done  
;  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "You don't have the 'Microsoft Visual C++ 2008 Redistributable' library installed and it is necessary to run this program.$\n$\nDo you want to download it now?" IDNO end
;  DetailPrint "Downloading Visual C++ 2008 Redistributable Setup..."
;  NSISdl::download /TIMEOUT=15000 "${MSVC2008}" "vcredist_x86.exe"
;  Pop $R0 ;Get the return value
;  StrCmp $R0 "success" install
;  MessageBox MB_OK "Could not download Visual Studio 2008 Redist; none of the mirrors appear to be functional."
;  Goto end
;  install:
;    DetailPrint "Running Visual C++ 2008 Redistributable Setup..."
;    ExecWait '"$INSTDIR\vcredist_x86.exe /qb'
;    DetailPrint "Finished Visual C++ 2008 Redistributable Setup"
;    Delete "$INSTDIR\vcredist_x86.exe"
;  done:
;    DetailPrint "Runtime MSVC++ 2008 OK."
;  end:
;SectionEnd

Section "Microsoft Visual C++ 2010 Redistributable Package (x86)" SEC02

Call  CheckRedistributableInstalled
Pop $R0

${If} $R0 == "Error"
  ExecWait '$INSTDIR\vcredist_x86.exe /q:a /c:"VCREDI~3.EXE /q:a /c:""msiexec /i vcredist.msi /qn"" "'	
${EndIf}

SectionEnd

Section -AdditionalIcons
  SetShellVarContext all
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\Artisan\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\Artisan\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\artisan.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "Path" "$INSTDIR"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\artisan.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"

  ; file associations
  !insertmacro APP_ASSOCIATE "alog" "Artisan.Profile" "Artisan Roast Profile" \
     "$INSTDIR\artisanProfile.ico" "Open with Artisan" "$INSTDIR\artisan.exe $\"%1$\""
     
  !insertmacro APP_ASSOCIATE "alrm" "Artisan.Alarms" "Artisan Alarms" \
     "$INSTDIR\artisanAlarms.ico" "Open with Artisan" "$INSTDIR\artisan.exe $\"%1$\""
     
  !insertmacro APP_ASSOCIATE "apal" "Artisan.Palettes" "Artisan Palettes" \
     "$INSTDIR\artisanPalettes.ico" "Open with Artisan" "$INSTDIR\artisan.exe $\"%1$\""
     
  !insertmacro APP_ASSOCIATE "aset" "Artisan.Theme" "Artisan Theme" \
     "$INSTDIR\artisanTheme.ico" "Open with Artisan" "$INSTDIR\artisan.exe $\"%1$\""
     
  !insertmacro APP_ASSOCIATE "aset" "Artisan.Settings" "Artisan Settings" \
     "$INSTDIR\artisanSettings.ico" "Open with Artisan" "$INSTDIR\artisan.exe $\"%1$\""
     
  !insertmacro APP_ASSOCIATE "wg" "Artisan.Wheel" "Artisan Wheel" \
     "$INSTDIR\artisanWheel.ico" "Open with Artisan" "$INSTDIR\artisan.exe $\"%1$\""
     
SectionEnd


Function un.onUninstSuccess
  HideWindow
  IfSilent +2 0
    MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer." /SD IDOK
FunctionEnd

Function un.onInit

    IfSilent +3 
        MessageBox MB_ICONQUESTION|MB_YESNO|MB_TOPMOST "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2 
        Abort 
    HideWindow   

FunctionEnd

Section Uninstall
  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\artisan.exe"
  Delete "$INSTDIR\artisan.png"
  Delete "$INSTDIR\LICENSE.txt"
  Delete "$INSTDIR\python34.dll"
  Delete "$INSTDIR\README.txt"
  Delete "$INSTDIR\w9xpopen.exe"
  Delete "$INSTDIR\artisanAlarms.ico"
  Delete "$INSTDIR\artisanProfile.ico"
  Delete "$INSTDIR\artisanPalettes.ico"
  Delete "$INSTDIR\artisanTheme.ico"
  Delete "$INSTDIR\artisanWheel.ico"
  Delete "$INSTDIR\artisanSettings.ico"
  Delete "$INSTDIR\Humor-Sans.ttf"
  Delete "$INSTDIR\alarmclock.eot"
  Delete "$INSTDIR\alarmclock.svg"
  Delete "$INSTDIR\alarmclock.ttf"
  Delete "$INSTDIR\alarmclock.woff"
  Delete "$INSTDIR\artisan.tpl"
  Delete "$INSTDIR\bigtext.js"
  Delete "$INSTDIR\sorttable.js"
  Delete "$INSTDIR\report-template.htm"
  Delete "$INSTDIR\roast-template.htm"
  Delete "$INSTDIR\ranking-template.htm"
  Delete "$INSTDIR\jquery-1.11.1.min.js"
  Delete "$INSTDIR\qt.conf"
  Delete "$INSTDIR\vcredist_x86.exe"

  SetShellVarContext all
  Delete "$SMPROGRAMS\Artisan\Uninstall.lnk"
  Delete "$SMPROGRAMS\Artisan\Website.lnk"
  Delete "$DESKTOP\Artisan.lnk"
  Delete "$SMPROGRAMS\Artisan\Artisan.lnk"
  
  RMDir /r "$INSTDIR\plugins"
  RMDir /r "$INSTDIR\lib"
  RMDir /r "$INSTDIR\mpl-data"
  RMDir /r "$INSTDIR\translations"
  RMDir /r "$INSTDIR\Wheels"

  RMDir /r "$INSTDIR\gevent-1.4.0-py3.6.egg-info"

  RMDir /r "$INSTDIR\gevent"
  RMDir /r "$INSTDIR\matplotlib"
  RMDir /r "$INSTDIR\numpy"
  RMDir /r "$INSTDIR\scipy"
  RMDir /r "$INSTDIR\win32com"
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
  !insertmacro APP_UNASSOCIATE "aset" "Artisan.Settings"
  !insertmacro APP_UNASSOCIATE "aset" "Artisan.Theme"
  !insertmacro APP_UNASSOCIATE "wg" "Artisan.Wheel"
  
  SetAutoClose true
SectionEnd
