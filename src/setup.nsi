!define py2exeOutputDir 'dist'
!define exe             'Artisan.exe'
!define icon            'artisan.ico'
!define compressor      'zlib'  ;one of 'zlib', 'bzip2', 'lzma'
!define onlyOneInstance
!include FileFunc.nsh
!insertmacro GetParameters

; HM NIS Edit Wizard helper defines
!define PRODUCT_NAME "Artisan"
!define PRODUCT_VERSION "0.9.9.0"
!define PRODUCT_PUBLISHER "The Artisan Team"
!define PRODUCT_WEB_SITE "http://code.google.com/p/artisan/"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\artisan.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

Caption "${PRODUCT_NAME}"
VIProductVersion ${PRODUCT_VERSION}
VIAddVersionKey ProductName "${PRODUCT_NAME}"
VIAddVersionKey Comments "Artisan App"
VIAddVersionKey CompanyName ""
VIAddVersionKey LegalCopyright Artisan.org
VIAddVersionKey FileVersion "${PRODUCT_VERSION}"
VIAddVersionKey FileDescription "${PRODUCT_NAME} ${PRODUCT_VERSION} Installer"
VIAddVersionKey ProductVersion "${PRODUCT_VERSION}"

; - - - - do not edit below this line, normaly - - - -
!ifdef compressor
    SetCompressor ${compressor}
!else
    SetCompress Off
!endif
Name ${exe}
OutFile ${exe}
SilentInstall silent
!ifdef icon
    Icon ${icon}
!endif

; - - - - Allow only one installer instance - - - - 
!ifdef onlyOneInstance
Function .onInit
 System::Call "kernel32::CreateMutexA(i 0, i 0, t '$(^Name)') i .r0 ?e"
 Pop $0
 StrCmp $0 0 launch
  Abort
 launch:
FunctionEnd
!endif
; - - - - Allow only one installer instance - - - - 

Section
    
    ; Get directory from which the exe was called
    System::Call "kernel32::GetCurrentDirectory(i ${NSIS_MAX_STRLEN}, t .r0)"
    
    ; Unzip into pluginsdir
    InitPluginsDir
    SetOutPath '$PLUGINSDIR'
    File /r '${py2exeOutputDir}\*.*'
    
    ; Set working dir and execute, passing through commandline params
    SetOutPath '$0'
    ${GetParameters} $R0
    ExecWait '"$PLUGINSDIR\${exe}" $R0' $R2
    SetErrorLevel $R2
 
SectionEnd