!define py2exeOutputDir 'dist'
!define exe             'artisan.exe'
!define icon            'artisan.ico'
!define compressor      'zlib'  ;one of 'zlib', 'bzip2', 'lzma'
!define onlyOneInstance
!include FileFunc.nsh
!insertmacro GetParameters

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