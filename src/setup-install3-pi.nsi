; ABOUT
; NSIS script file for artisan Windows installer.
;
; COPYRIGHT (C) 2010-2026 The artisan team represented by
; Marko Luther <marko.luther@gmx.net> (maintainer) and all contributors
;
; LICENSE
; This program or module is free software: you can redistribute it and/or modify
; it under the terms of the GNU Affero General Public License as
; published by the Free Software Foundation, either version 3 of the
; License, or (at your option) any later version.
;
; This program is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
; GNU Affero General Public License for more details.
;
; You should have received a copy of the GNU Affero General Public License
; along with this program.  If not, see <https://www.gnu.org/licenses/>.
; the GNU General Public License for more details.
;
; AUTHOR
; Dave Baxter, Marko Luther 2023-2026
;

; All command line options are intended for internal use only.
;    .nsi command line options, overrides any default defines:
;        /DPRODUCT_VERSION=ww.xx.yy  -explicitly set the product version, default is 0.0.0
;        /DPRODUCT_BUILD=zz          -explicityl set the product build, default is 0
;        /DSIGN                      -Used by SignArtisan to prevent generating uninstall.exe
;        /DSkel                      -builds a skeleton installer for local testing, not supported from repository
;
;    installer/uninstaller command line options:
;        /S                          -silent operation
;        /L=nnnn                     -force language at runtime, nnnn is language id, used for Skeling
;        /SHOWPROGRESS               -uninstaller only, used with upgrade flow, shows progress only, skips other pages


; -----------------------------------------------------------------------------
; INCLUDES
; -----------------------------------------------------------------------------
!include "x64.nsh"
!include "WinVer.nsh"
!include "FileFunc.nsh"
!include "MUI2.nsh"
; Note - the following are included by reference in MUI2
;   !include WinMessages.nsh
;   !include LogicLib.nsh
;   !include nsDialogs.nsh
;   !include LangFile.nsh

; =============================================================================
; COMPILER FLAGS
; =============================================================================
RequestExecutionLevel admin
SetCompressor lzma
ManifestDPIAware true


; =============================================================================
; MACROS
; =============================================================================
; ---------------------------------------------------------------------------
; Macros for making and removing associations, ref:https://nsis.sourceforge.io/FileAssoc
; ---------------------------------------------------------------------------
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

!macro UPDATEFILEASSOC
    ; Use the system call to update the shell associations
     System::Call "shell32::SHChangeNotify(i,i,i,i) (${SHCNE_ASSOCCHANGED}, ${SHCNF_FLUSH}, 0, 0)"
!macroend

; ---------------------------------------------------------------------------
; Macro to simulate the missing !Info
; ---------------------------------------------------------------------------
!macro info msg
    !verbose push
    !verbose 4
    !echo "INFO: ${msg}"
    !verbose pop
!macroend

; ---------------------------------------------------------------------------
; Macro to remove directory with wildcards
; ---------------------------------------------------------------------------
!macro Rmdir_Wildcard dir uid
    ; dir: in the quoted form "$INSTDIR\dir_with_wildcard", uid: must be ${__LINE__} not quoted
    FindFirst $0 $1 ${dir}
    loop_${uid}:
        StrCmp $1 "" endloop_${uid}
        RMDIR /r "$INSTDIR\$1"
        FindNext $0 $1
        Goto loop_${uid}
    endloop_${uid}:
    FindClose $0
!macroend

; ---------------------------------------------------------------------------
; Macro to identify when an artisan instance is running
; ---------------------------------------------------------------------------
!macro AppIsRunning caller
    Delete "$TEMP\25b241e1.tmp"
    nsExec::Exec "cmd /c for /f $\"tokens=1,2$\" %i in ('tasklist') do (if /i %i EQU ${PRODUCT_NAME}.exe fsutil file createnew $TEMP\25b241e1.tmp 0)"
    IfFileExists $TEMP\25b241e1.tmp 0 notRunning
        ;we have at least one main window active
        !if "${caller}" == "install"
            System::Call 'user32::MessageBox(i $HWNDPARENT, t "$(Alert_AppIsRunning)", t "$(Caption_Setup)", i 0x30) i.r0'
        !else
            System::Call 'user32::MessageBox(i $HWNDPARENT, t "$(Alert_AppIsRunning_Uninstall)", t "$(Caption_Uninstall)", i 0x30) i.r0'
        !endif
        Delete "$TEMP\25b241e1.tmp"
        Quit
    notRunning:
!macroend

; ---------------------------------------------------------------------------
; Macro to prevent multiple install/uninstall instances
; ---------------------------------------------------------------------------
!macro CheckForRunningInstances caller
    System::Call 'KERNEL32::CreateMutex(i 0, i 0, t "${INSTALLMUTEX}") i .r1 ?e'
    Pop $0
    IntCmpU $0 183 anotherRunning noneRunning  ; ERROR_ALREADY_EXISTS = 183
    anotherRunning:
        !if "${caller}" == "install"
            System::Call 'user32::MessageBox(i $HWNDPARENT, t "$(Another_Instance)", t "$(Caption_Setup)", i 0x30) i.r0'
        !else
            System::Call 'user32::MessageBox(i $HWNDPARENT, t "$(Another_Instance)", t "$(Caption_Uninstall)", i 0x30) i.r0'
        !endif
        Abort
    noneRunning:
!macroend

; ---------------------------------------------------------------------------
; Macro to set ProgressBar color
; ---------------------------------------------------------------------------
!macro SetProgressBarColor FgColor BgColor  ;FgColor is BBGGRR
    ; Find the inner dialog of the current page
    FindWindow $0 "#32770" "" $HWNDPARENT

    ; Get the progress bar handle by Class Name
    FindWindow $1 "msctls_progress32" "" $0

    ; Set the colors
    ${If} $1 <> 0
        ; Disable visual styles so PBM_SETBARCOLOR/PBM_SETBKCOLOR will take effect
        System::Call 'UxTheme::SetWindowTheme(i $1, w "", w "")'
        ; Set the colors
        SendMessage $1 ${PBM_SETBARCOLOR} 0 "0x${FgColor}"
        SendMessage $1 ${PBM_SETBKCOLOR} 0 "0x${BgColor}"
    ${EndIf}
!macroend


; =============================================================================
; CHECK NSIS MINIMUM VERSION AT COMPILE TIME (DURING CI)
; =============================================================================
; 0x + Major(2 digits) + Minor(3 digits) + Revision(2 digits) + Build(1 digit)
!if ${NSIS_PACKEDVERSION} < 0x03011000
    !error "NSIS 3.11 or higher is required to build this installer"
!else
    !insertmacro info "NSIS running version ${NSIS_VERSION}"
!endif


; =============================================================================
; USER VARIABLES
; =============================================================================
; Global variables
Var PathToUninstaller
Var Dialog
Var CheckboxState
Var CheckboxRunApp
Var CheckboxOpenDocs
Var CheckboxOpenDonate
Var UseInstallPath
Var UpgradeFlow
Var NoConfirmCancel
Var IsProgressMode      ; 1 = /SHOWPROGRESS mode
Var IsSilentMode        ; 1 = /S mode

; Source locations
!define pyinstallerOutputDir "dist/artisan"
!define nsisLocalIncludesDir "nsis_includes"

; Product definitions
!define PRODUCT_NAME "artisan"
!define PRODUCT_NAME_CAP "Artisan"
!define PRODUCT_PUBLISHER "The Artisan Team"
!define PRODUCT_WEB_SITE "https://github.com/artisan-roaster-scope/artisan/blob/master/README.md"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\${PRODUCT_NAME}.exe"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"
; The following gets transposed to "SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define Finish_Documentation_URL "https://artisan-scope.org/docs/"
!define Finish_Donate_URL "https://artisan-scope.org/donate/"

; Set with command line options
!define /ifndef PRODUCT_VERSION "0.0.0"
!define /ifndef PRODUCT_BUILD "0"

; Used by SHChangeNotify (UPDATEFILEASSOC)
!ifdef SHCNE_ASSOCCHANGED
    !undef SHCNE_ASSOCCHANGED
!endif
!define SHCNE_ASSOCCHANGED 0x08000000
!ifdef SHCNF_FLUSH
    !undef SHCNF_FLUSH
!endif
!define SHCNF_FLUSH 0x1000

; Font values
!define Font_Name "Segoe UI"
!define Font_Size_Title "13"
!define Font_Size_Body "10"
!define Font_Size_Option "9.5"
!define Font_Weight "600" ; Range from 400:Normal to 700:Bold
!define Font_Weight_Option "400"

; Other
!define /date CUR_YEAR "%Y"
!define INSTALLMUTEX "{c2a7be4e-da57-44b9-b2cf-5b1f80c6b429}"

;---------
!ifdef Skel
    !include artisan-skeleton.nsh  #for local testing, not supported from repository
    !insertmacro identify
    !insertmacro skel01
!endif
;---------


; =============================================================================
; MUI CONFIGURATION
; =============================================================================
; General
!define MUI_CUSTOMFUNCTION_ABORT onUserAbort
!define MUI_BGCOLOR "2899c7"
!define MUI_TEXTCOLOR "FFFFFF"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_INSTFILESPAGE_PROGRESSBAR "colored"

; INSTALL
!define MUI_ICON "${PRODUCT_NAME}.ico"
!define MUI_HEADERIMAGE_BITMAP "${nsisLocalIncludesDir}\header-install.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "${nsisLocalIncludesDir}\sidebar-install.bmp"

; UNINSTALL
!define MUI_UNICON "${nsisLocalIncludesDir}\uninstall.ico"
!define MUI_HEADERIMAGE_UNBITMAP "${nsisLocalIncludesDir}\header-uninstall.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "${nsisLocalIncludesDir}\sidebar-uninstall.bmp"
!define MUI_FINISHPAGE_TITLE "$(UnFinish_Title)"  ;used only for uninstall
!define MUI_FINISHPAGE_TEXT "$(UnFinish_Text)"    ;used only for uninstall


; ============================================================================
; INSTALLER PAGES
; ============================================================================
; Welcome page, only one will be shown
Page custom CustomWelcomeUpgradeCreator CustomWelcomeUpgradeLeave
Page custom CustomWelcomeFreshCreator CustomWelcomeFreshLeave

; Directory page
!define MUI_DIRECTORYPAGE_VARIABLE $UseInstallPath
!define MUI_PAGE_CUSTOMFUNCTION_PRE DirectoryPre
!define MUI_PAGE_CUSTOMFUNCTION_SHOW DirectoryShow
!insertmacro MUI_PAGE_DIRECTORY

; Instfiles page
!define MUI_PAGE_CUSTOMFUNCTION_PRE InstFilesPre
!define MUI_PAGE_CUSTOMFUNCTION_SHOW InstFilesShow
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE InstFilesLeave
!insertmacro MUI_PAGE_INSTFILES

; Finish page
Page custom CustomFinishPageCreate CustomFinishPageLeave


; ============================================================================
; UNINSTALLER PAGES
; ============================================================================
; Un_Welcome page
UninstPage custom un.WelcomeShow un.WelcomeLeave

; Un_Instfiles page
!define MUI_PAGE_CUSTOMFUNCTION_SHOW un.InstFilesShow
!insertmacro MUI_UNPAGE_INSTFILES

; Un_Finish page
!define MUI_PAGE_CUSTOMFUNCTION_PRE un.PreFinish
!define MUI_PAGE_CUSTOMFUNCTION_SHOW un.FinishShow
!insertmacro MUI_UNPAGE_FINISH


; ============================================================================
; LANGUAGE  (must come after MUI configuration))
; ============================================================================
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "German"
!insertmacro MUI_LANGUAGE "Italian"
!insertmacro MUI_LANGUAGE "Spanish"
!insertmacro MUI_LANGUAGE "PortugueseBR"
!insertmacro MUI_LANGUAGE "SimpChinese"
!include "${nsisLocalIncludesDir}\install_translations.nsh"


; ============================================================================
; ATTRIBUTES
; ============================================================================
Name "${PRODUCT_NAME}"
OutFile "${PRODUCT_NAME}-win-x64-${PRODUCT_VERSION}-setup.exe"
InstallDir "C:\Program Files\${PRODUCT_NAME}"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUninstDetails show
UninstallCaption "$(Caption_Uninstall)"
BrandingText "$(Tag_Line)"

; Displayed by file properties, not language translated
VIProductVersion "${PRODUCT_VERSION}.${PRODUCT_BUILD}"
VIAddVersionKey ProductName "${PRODUCT_NAME}"
VIAddVersionKey Comments "Installer for ${PRODUCT_NAME}"
VIAddVersionKey CompanyName ""
VIAddVersionKey LegalCopyright "Copyright 2010-${CUR_YEAR}, Artisan developers. GNU Affero General Public License"
VIAddVersionKey FileVersion "${PRODUCT_VERSION}.${PRODUCT_BUILD}"
VIAddVersionKey FileDescription "${PRODUCT_NAME} Installer"
VIAddVersionKey ProductVersion "${PRODUCT_VERSION}.${PRODUCT_BUILD}"


; =============================================================================
; FUNCTIONS
; =============================================================================
; ----------------------------------------------------------------------------
; Cancel and Esc handler
; ----------------------------------------------------------------------------
Function onUserAbort
    ${If} $NoConfirmCancel != "1"
        MessageBox MB_YESNO|MB_ICONEXCLAMATION "$(Alert_AbortConfirm)" IDYES abort_cancel
        Abort          ;"No" Abort aborts the exit and stays on the page (crazy nsis logic)
        abort_cancel:  ;"Yes", no Abort call so the user abort proceeds to exit
    ${EndIf}
FunctionEnd

; ----------------------------------------------------------------------------
; INSTALL on.Init
; ----------------------------------------------------------------------------
Function .onInit
    ; Prevent multiple instances of install / uninstall
    !insertmacro CheckForRunningInstances "install"

    ; Check for x64 Windows platform
    ${IfNot} ${RunningX64}
        MessageBox MB_OK "$(Alert_Windows_Arch)"
        Abort
    ${EndIf}

    ; Check the Windows version is appropriate
    ${IfNot} ${AtLeastWin10}
        MessageBox MB_ICONSTOP "$(Alert_Windows_Version)"
        Abort
    ${EndIf}

    ; Stop if there is a running instance of the app
    !insertmacro AppIsRunning "install"

    ; Extract image
    InitPluginsDir
    File /oname=$PLUGINSDIR\sidebar.bmp "${MUI_WELCOMEFINISHPAGE_BITMAP}"

    ; Check for existing installation
    ReadRegStr $PathToUninstaller ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString"
    StrCmp $PathToUninstaller "" notInstalled isInstalled

    notInstalled:
        StrCpy $UpgradeFlow 0
        StrCpy $UseInstallPath "$INSTDIR"
        goto done

    isInstalled:
        ; Get the existing install folder
        ReadRegStr $UseInstallPath HKLM "${PRODUCT_DIR_REGKEY}" "Path"
        ; Fallback if registry key is empty
        StrCmp $UseInstallPath "" 0 +2
        StrCpy $UseInstallPath "$INSTDIR"
        StrCpy $UpgradeFlow 1
        goto done

    done:

    ; Language forced from the command line, used for testing only
    ${GetOptions} $CMDLINE "/L=" $LANGUAGE
FunctionEnd

; --------------------------------------------
; CUSTOM WELCOME PAGE - FRESH INSTALL
; --------------------------------------------
Function CustomWelcomeFreshCreator
    ; Skip this page if this is an Upgrade install
    ${If} $UpgradeFlow == 1
        Abort
    ${EndIf}

    ; Set the caption
    SendMessage $HWNDPARENT ${WM_SETTEXT} 0 "STR:$(Caption_Install)"

    ; Remove the back button
    GetDlgItem $0 $HWNDPARENT 3
    ShowWindow $0 ${SW_HIDE}

    ; Hide branding text (ID 1028) and line (ID 1045)
    GetDlgItem $0 $HWNDPARENT 1028
    ShowWindow $0 ${SW_HIDE}
    GetDlgItem $0 $HWNDPARENT 1045
    ShowWindow $0 ${SW_HIDE}

    ; Create dialog
    nsDialogs::Create 1044
    Pop $Dialog
    nsDialogs::SetRTL $(^RTL)
    SetCtlColors $Dialog "" "2899C7"  ; blue background

    ; Image control (left sidebar bitmap)
    ${NSD_CreateBitmap} 0u 0u 109u 193u ""
    Pop $0
    ${NSD_SetStretchedImage} $0 "$PLUGINSDIR\sidebar.bmp" $1

    ; Title
    ${NSD_CreateLabel} 120u 10u 195u 38u "$(Welcome_Install_Title)"
    Pop $0
    SetCtlColors $0 "FFFFFF" "2899C7"  ; white text, blue background
    CreateFont $1 "${Font_Name}" "${Font_Size_Title}" "${Font_Weight}"
    SendMessage $0 ${WM_SETFONT} $1 0

    ; Body text
    ${NSD_CreateLabel} 120u 45u 195u 130u "$(Welcome_Install_Text)"
    Pop $0
    SetCtlColors $0 "FFFFFF" "2899C7"  ; white text, blue background
    CreateFont $1 "${Font_Name}" "${Font_Size_Body}" "${Font_Weight}"
    SendMessage $0 ${WM_SETFONT} $1 0

    nsDialogs::Show
FunctionEnd

Function CustomWelcomeFreshLeave
FunctionEnd

; --------------------------------------------
; CUSTOM WELCOME PAGE - UPGRADE
; --------------------------------------------
Function CustomWelcomeUpgradeCreator
    ; Skip this page if this is note an Upgrade install
    ${If} $UpgradeFlow == 0
        Abort
    ${EndIf}

    ; Set the caption
    SendMessage $HWNDPARENT ${WM_SETTEXT} 0 "STR:$(Caption_Upgrade)"

    ; Remove the back button
    GetDlgItem $0 $HWNDPARENT 3
    ShowWindow $0 ${SW_HIDE}

    ; Change Next button to Upgrade
    GetDlgItem $0 $HWNDPARENT 1
    SendMessage $0 ${WM_SETTEXT} 0 "STR:$(Button_Upgrade)"

    ; Hide branding text (ID 1028) and line (ID 1045)
    GetDlgItem $0 $HWNDPARENT 1028
    ShowWindow $0 ${SW_HIDE}
    GetDlgItem $0 $HWNDPARENT 1045
    ShowWindow $0 ${SW_HIDE}

    ; Create dialog
    nsDialogs::Create 1044
    Pop $Dialog
    nsDialogs::SetRTL $(^RTL)
    SetCtlColors $Dialog "" "2899C7"  ; blue background

    ; Image control (left sidebar bitmap)
    ${NSD_CreateBitmap} 0u 0u 109u 193u ""
    Pop $0
    ${NSD_SetStretchedImage} $0 "$PLUGINSDIR\sidebar.bmp" $1

    ; Title
    ${NSD_CreateLabel} 120u 10u 195u 38u "$(Welcome_Upgrade_Title)"
    Pop $0
    SetCtlColors $0 "FFFFFF" "2899C7"  ; white text, blue background
    CreateFont $1 "${Font_Name}" "${Font_Size_Title}" "${Font_Weight}"
    SendMessage $0 ${WM_SETFONT} $1 0

    ; Body text
    ${NSD_CreateLabel} 120u 55u 195u 130u "$(Welcome_Upgrade_Text)"
    Pop $0
    SetCtlColors $0 "FFFFFF" "2899C7"  ; white text, blue background
    CreateFont $1 "${Font_Name}" "${Font_Size_Body}" "${Font_Weight}"
    SendMessage $0 ${WM_SETFONT} $1 0

    nsDialogs::Show
FunctionEnd

Function CustomWelcomeUpgradeLeave
    ; Set the flag to show the progress
    StrCpy $IsProgressMode 1

    ; Language forced from the command line, used for testing only
    ; pass it to the uninstaller
    StrCpy $0 ""
    ${GetOptions} $CMDLINE "/L=" $0
    StrCmp $0 "" +3 0
        ExecWait '$PathToUninstaller /SHOWPROGRESS /L=$LANGUAGE _?=$INSTDIR'
        Goto +2

    ; Start the uninstall as part of the upgrade process
    ExecWait '$PathToUninstaller /SHOWPROGRESS _?=$INSTDIR'
FunctionEnd

; --------------------------------------------
; CUSTOM DIRECTORY PAGE
; --------------------------------------------
Function DirectoryPre
    ; Skip this page if $UpgradeFlow is 1
    StrCmp $UpgradeFlow "1" 0 +2
    Abort
FunctionEnd

Function DirectoryShow
    ; Set the caption
    SendMessage $HWNDPARENT ${WM_SETTEXT} 0 "STR:$(Caption_Install)"

    ; Show branding text (ID 1028) and line (ID 1045)
    GetDlgItem $0 $HWNDPARENT 1028
    ShowWindow $0 ${SW_SHOW}
    GetDlgItem $0 $HWNDPARENT 1045
    ShowWindow $0 ${SW_SHOW}
FunctionEnd

; --------------------------------------------
; CUSTOM INSTFILES PAGE
; --------------------------------------------
Function InstFilesPre
    ; Set the appropriate caption
    ${If} $UpgradeFlow == 1
        SendMessage $HWNDPARENT ${WM_SETTEXT} 0 "STR:$(Caption_Upgrade)"
    ${Else}
        SendMessage $HWNDPARENT ${WM_SETTEXT} 0 "STR:$(Caption_Install)"
    ${EndIf}
FunctionEnd

Function InstFilesShow
    ; Change progress bar color
    !insertmacro SetProgressBarColor "C79928" "FFFFFF"

    ; Remove the Back, Next and Cancel buttons
    GetDlgItem $0 $HWNDPARENT 3
    ShowWindow $0 ${SW_HIDE}
    GetDlgItem $0 $HWNDPARENT 1
    ShowWindow $0 ${SW_HIDE}
    GetDlgItem $0 $HWNDPARENT 2
    ShowWindow $0 ${SW_HIDE}

    ; Show branding text (ID 1028) and line (ID 1045)
    GetDlgItem $0 $HWNDPARENT 1028
    ShowWindow $0 ${SW_SHOW}
    GetDlgItem $0 $HWNDPARENT 1045
    ShowWindow $0 ${SW_SHOW}

    ; Unconditional close on Complete
    SetAutoClose true
FunctionEnd

Function InstFilesLeave
FunctionEnd

; --------------------------------------------
; CUSTOM FINISH PAGE
; --------------------------------------------
Function CustomFinishPageCreate
    ; Set appropriate Caption
    ${If} $UpgradeFlow == 1
        SendMessage $HWNDPARENT ${WM_SETTEXT} 0 "STR:$(Caption_Upgrade)"
    ${Else}
        SendMessage $HWNDPARENT ${WM_SETTEXT} 0 "STR:$(Caption_Install)"
    ${EndIf}

    ; Remove the back button
    GetDlgItem $0 $HWNDPARENT 3
    ShowWindow $0 ${SW_HIDE}

    ; Show the cancel button, set NoConfirmCancel for onFinishAbort
    GetDlgItem $0 $HWNDPARENT 2
    ShowWindow $0 ${SW_SHOW}
    EnableWindow $0 1
    StrCpy $NoConfirmCancel 1

    ; Show the Close button
    GetDlgItem $0 $HWNDPARENT 1
    ShowWindow $0 ${SW_SHOW}

    ; Change Close button label to Upgrade
    GetDlgItem $0 $HWNDPARENT 1
    SendMessage $0 ${WM_SETTEXT} 0 "STR:$(Button_Finish)"

    ; Hide branding text (ID 1028) and line (ID 1045)
    GetDlgItem $0 $HWNDPARENT 1028
    ShowWindow $0 ${SW_HIDE}
    GetDlgItem $0 $HWNDPARENT 1045
    ShowWindow $0 ${SW_HIDE}

    ; Create dialog
    nsDialogs::Create 1044
    Pop $Dialog
    nsDialogs::SetRTL $(^RTL)
    SetCtlColors $Dialog "" "2899C7"  ; blue background

    ; Image control (left sidebar bitmap)
    ${NSD_CreateBitmap} 0u 0u 109u 193u ""
    Pop $0
    ${NSD_SetStretchedImage} $0 "$PLUGINSDIR\sidebar.bmp" $1

    ; Title
    ${NSD_CreateLabel} 120u 10u 195u 38u "$(Finish_Title)"
    Pop $0
    SetCtlColors $0 "FFFFFF" "2899C7"  ; white text, blue background
    CreateFont $1 "${Font_Name}" "${Font_Size_Title}" "${Font_Weight}"
    SendMessage $0 ${WM_SETFONT} $1 0

    ; Body text
    ${If} $UpgradeFlow == 1
        ${NSD_CreateLabel} 120u 45u 195u 58u "$(Finish_Text_Upgrade)$\n$\n$(Finish_Instructions)"
    ${Else}
        ${NSD_CreateLabel} 120u 45u 195u 58u "$(Finish_Text_Install)$\n$\n$(Finish_Instructions)"
    ${EndIf}
    Pop $0
    SetCtlColors $0 "FFFFFF" "2899C7"  ; white text, blue background
    CreateFont $1 "${Font_Name}" "${Font_Size_Body}" "${Font_Weight}"
    SendMessage $0 ${WM_SETFONT} $1 0

    ; Checkbox 1: Open the app (default checked)
    ${NSD_CreateCheckbox} 120u 120u 12u 12u ""
    Pop $CheckboxRunApp
    SetCtlColors $CheckboxRunApp "FFFFFF" "2899C7"
    ${NSD_SetState} $CheckboxRunApp ${BST_CHECKED}
    ${NSD_CreateLabel} 135u 120u 195u 12u "$(Finish_RunApp)"
    Pop $0
    SetCtlColors $0 "FFFFFF" "2899C7"
    CreateFont $1 "${Font_Name}" "${Font_Size_Option}" "${Font_Weight_Option}"
    SendMessage $0 ${WM_SETFONT} $1 0

    ; Checkbox 2: Open Documentation page
    ${NSD_CreateCheckbox} 120u 135u 12u 12u ""
    Pop $CheckboxOpenDocs
    SetCtlColors $CheckboxOpenDocs "FFFFFF" "2899C7"
    ${NSD_SetState} $CheckboxOpenDocs ${BST_UNCHECKED}
    ${NSD_CreateLabel} 135u 135u 195u 12u "$(Finish_OpenDocumentation)"
    Pop $0
    SetCtlColors $0 "FFFFFF" "2899C7"
    CreateFont $1 "${Font_Name}" "${Font_Size_Option}" "${Font_Weight_Option}"
    SendMessage $0 ${WM_SETFONT} $1 0

    ; Checkbox 3: Open Donate page
    ${NSD_CreateCheckbox} 120u 150u 12u 12u ""
    Pop $CheckboxOpenDonate
    SetCtlColors $CheckboxOpenDonate "FFFFFF" "2899C7"
    ${NSD_SetState} $CheckboxOpenDonate ${BST_UNCHECKED}
    ${NSD_CreateLabel} 135u 150u 195u 12u "$(Finish_OpenDonate)"
    Pop $0
    SetCtlColors $0 "FFFFFF" "2899C7"
    CreateFont $1 "${Font_Name}" "${Font_Size_Option}" "${Font_Weight_Option}"
    SendMessage $0 ${WM_SETFONT} $1 0

    nsDialogs::Show
FunctionEnd

Function CustomFinishPageLeave
    ; Check the state of each checkbox and execute actions
    ${NSD_GetState} $CheckboxRunApp $CheckboxState
    ${If} $CheckboxState == ${BST_CHECKED}
        ; Run the application
        ExecShell "open" "$INSTDIR\${PRODUCT_NAME}.exe"
    ${EndIf}

    ${NSD_GetState} $CheckboxOpenDocs $CheckboxState
    ${If} $CheckboxState == ${BST_CHECKED}
        ; Open Documentation URL
        ExecShell "open" "${Finish_Documentation_URL}"
    ${EndIf}

    ${NSD_GetState} $CheckboxOpenDonate $CheckboxState
    ${If} $CheckboxState == ${BST_CHECKED}
        ; Open Donate URL
        ExecShell "open" "${Finish_Donate_URL}"
    ${EndIf}
FunctionEnd


; ----------------------------------------------------------------------------
; UNINSTALL un.onInit
; ----------------------------------------------------------------------------
Function un.onInit
    ; Set the flag variables
    StrCpy $IsProgressMode 0
    StrCpy $IsSilentMode 0

    ; Get command line options
    ${GetParameters} $R0
    ClearErrors
    ; Test if this is an Upgrade uninstall
    ${GetOptions} $R0 "/SHOWPROGRESS" $R1
    ${IfNot} ${Errors}
        ; started from the installer
        StrCpy $IsProgressMode 1
        SetAutoClose true
    ${Else}
        ; Check for other instances only when uninstall is started by the user
        ; Stop if there is a running instance of install/uninstall
        !insertmacro CheckForRunningInstances "uninstall"
        ; Stop if there is a running instance of the app
        !insertmacro AppIsRunning "uninstall"
    ${EndIf}

    ; Test for the /S option
    ${If} ${Silent}
        StrCpy $IsSilentMode 1
        SetAutoClose true
        Return
    ${EndIf}

    ; Extract the bitmap to the plugins directory with a fixed name
    InitPluginsDir
    File /oname=$PLUGINSDIR\unsidebar.bmp "${MUI_UNWELCOMEFINISHPAGE_BITMAP}"

    ; Language forced from the command line, used for testing only
    ${GetOptions} $CMDLINE "/L=" $LANGUAGE
FunctionEnd

; --------------------------------------------
; CUSTOM UNINSTALL WELCOME PAGE
; --------------------------------------------
Function un.WelcomeShow
    ; Skip the page for /SHOWPROGRESS and /S
    ${If} $IsProgressMode == 1
        Abort
    ${EndIf}
    ${If} $IsSilentMode == 1
        Abort
    ${EndIf}

    ; Set the Caption
    SendMessage $HWNDPARENT ${WM_SETTEXT} 0 "STR:$(Caption_Uninstall)"

    ; Remove the back button
    GetDlgItem $0 $HWNDPARENT 3
    ShowWindow $0 ${SW_HIDE}

    ; Hide branding text (ID 1028) and line (ID 1045)
    GetDlgItem $0 $HWNDPARENT 1028
    ShowWindow $0 ${SW_HIDE}
    GetDlgItem $0 $HWNDPARENT 1045
    ShowWindow $0 ${SW_HIDE}

    ; Create Dialog (Use 1018 for client area)
    nsDialogs::Create 1044
    Pop $Dialog
    nsDialogs::SetRTL $(^RTL)
    SetCtlColors $Dialog "" "2899C7"

    ; Create Bitmap Control (Size: 109x193)
    ${NSD_CreateBitmap} 0u 0u 109u 193u ""
    Pop $0
    ${NSD_SetStretchedImage} $0 "$PLUGINSDIR\unsidebar.bmp" $1

    ; Title
    ${NSD_CreateLabel} 120u 10u 195u 38u "$(Welcome_Uninstall_Title)"
    Pop $0
    SetCtlColors $0 "FFFFFF" "2899C7"
    CreateFont $1 "${Font_Name}" "${Font_Size_Title}" "${Font_Weight}"
    SendMessage $0 ${WM_SETFONT} $1 0

    ; Body text
    ${NSD_CreateLabel} 120u 45u 195u 130u "$(Welcome_Uninstall_Text)"
    Pop $0
    SetCtlColors $0 "FFFFFF" "2899C7"
    CreateFont $1 "${Font_Name}" "${Font_Size_Body}" "${Font_Weight}"
    SendMessage $0 ${WM_SETFONT} $1 0

    nsDialogs::Show
FunctionEnd

Function un.WelcomeLeave
FunctionEnd

; --------------------------------------------
; CUSTOM UNINSTALL INSTFILES PAGE
; --------------------------------------------
Function un.InstFilesShow
    ; Change progress bar color
    !insertmacro SetProgressBarColor "C79928" "FFFFFF"

    ; Change Caption when upgrading
    ${If} $IsProgressMode == 1
        SendMessage $HWNDPARENT ${WM_SETTEXT} 0 "STR:$(Caption_Upgrade)"
    ${EndIf}

    ; Remove the Back, Next and Cancel buttons
    GetDlgItem $0 $HWNDPARENT 3
    ShowWindow $0 ${SW_HIDE}
    GetDlgItem $0 $HWNDPARENT 1
    ShowWindow $0 ${SW_HIDE}
    GetDlgItem $0 $HWNDPARENT 2
    ShowWindow $0 ${SW_HIDE}

    ; Show branding text (ID 1028) and line (ID 1045)
    GetDlgItem $0 $HWNDPARENT 1028
    ShowWindow $0 ${SW_SHOW}
    GetDlgItem $0 $HWNDPARENT 1045
    ShowWindow $0 ${SW_SHOW}

    SetAutoClose true
FunctionEnd

; --------------------------------------------
; CUSTOM UNINSTALL FINISH PAGE
; --------------------------------------------
Function un.PreFinish
    ; Skip the page for /SHOWPROGRESS and /S
    ${If} $IsProgressMode == 1
        SetAutoClose true
        Abort
    ${EndIf}
    ${If} $IsSilentMode == 1
        SetAutoClose true
        Abort
    ${EndIf}
FunctionEnd

Function un.FinishShow
    ; Remove the back button and Cancel button
    GetDlgItem $0 $HWNDPARENT 3
    ShowWindow $0 ${SW_HIDE}
    GetDlgItem $0 $HWNDPARENT 2
    ShowWindow $0 ${SW_HIDE}

    ; Show the Close button
    GetDlgItem $0 $HWNDPARENT 1
    ShowWindow $0 ${SW_SHOW}

    ; Hide branding text (ID 1028) and line (ID 1045)
    GetDlgItem $0 $HWNDPARENT 1028
    ShowWindow $0 ${SW_HIDE}
    GetDlgItem $0 $HWNDPARENT 1045
    ShowWindow $0 ${SW_HIDE}

    ; Title Label
    CreateFont $0 "${Font_Name}" "${Font_Size_Title}" "${Font_Weight}"
    SendMessage $mui.FinishPage.Title ${WM_SETFONT} $0 1

    ; Text Label
    CreateFont $0 "${Font_Name}" "${Font_Size_Body}" "${Font_Weight}"
    SendMessage $mui.FinishPage.Text ${WM_SETFONT} $0 1
FunctionEnd


; ============================================================================
; INSTALL SECTIONS
; ============================================================================
Section "Install"
    SetShellVarContext all
    SetOutPath "$INSTDIR"
    SetOverwrite on
    File /r '${pyinstallerOutputDir}\*.*'

;---------
    !ifdef Skel
        !insertmacro skel02
    !endif
;---------

    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
    CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_NAME}.exe"
    CreateShortcut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_NAME}.exe"
    !insertmacro UPDATEFILEASSOC

    ; Install Microsoft Visual C++ Redistributable Package (x64)
    ExecWait '$INSTDIR\vc_redist.x64.exe /install /passive /norestart'
    Delete '$INSTDIR\vc_redist.x64.exe'
SectionEnd

Section "-Install Hidden"
;--------
    !ifdef Skel
        !insertmacro skel03
    !endif
;--------

    SetShellVarContext all
    WriteINIStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
    CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
    CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"

    ; When called from SignArtisan, copy the signed uninstall.exe otherwise generate the uninstaller
    !ifndef SIGN
        WriteUninstaller "$INSTDIR\uninstall.exe"
    !else
        File "dist\artisan\uninstall.exe"
    !endif

    WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\${PRODUCT_NAME}.exe"
    WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "Path" "$INSTDIR"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\${PRODUCT_NAME}.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}.${PRODUCT_BUILD}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"

    ; file associations
    !insertmacro APP_ASSOCIATE "alog" "${PRODUCT_NAME}.Profile" "${PRODUCT_NAME} Roast Profile" \
       "$INSTDIR\${PRODUCT_NAME}Profile.ico" "Open with ${PRODUCT_NAME}" "$INSTDIR\${PRODUCT_NAME}.exe $\"%1$\""

    !insertmacro APP_ASSOCIATE "alrm" "${PRODUCT_NAME}.Alarms" "${PRODUCT_NAME} Alarms" \
       "$INSTDIR\${PRODUCT_NAME}Alarms.ico" "Open with ${PRODUCT_NAME}" "$INSTDIR\${PRODUCT_NAME}.exe $\"%1$\""

    !insertmacro APP_ASSOCIATE "apal" "${PRODUCT_NAME}.Palettes" "${PRODUCT_NAME} Palettes" \
       "$INSTDIR\${PRODUCT_NAME}Palettes.ico" "Open with ${PRODUCT_NAME}" "$INSTDIR\${PRODUCT_NAME}.exe $\"%1$\""

    !insertmacro APP_ASSOCIATE "athm" "${PRODUCT_NAME}.Theme" "${PRODUCT_NAME} Theme" \
       "$INSTDIR\${PRODUCT_NAME}Theme.ico" "Open with ${PRODUCT_NAME}" "$INSTDIR\${PRODUCT_NAME}.exe $\"%1$\""

    !insertmacro APP_ASSOCIATE "aset" "${PRODUCT_NAME}.Settings" "${PRODUCT_NAME} Settings" \
       "$INSTDIR\${PRODUCT_NAME}Settings.ico" "Open with ${PRODUCT_NAME}" "$INSTDIR\${PRODUCT_NAME}.exe $\"%1$\""

    !insertmacro APP_ASSOCIATE "wg" "${PRODUCT_NAME}.Wheel" "${PRODUCT_NAME} Wheel" \
       "$INSTDIR\${PRODUCT_NAME}Wheel.ico" "Open with ${PRODUCT_NAME}" "$INSTDIR\${PRODUCT_NAME}.exe $\"%1$\""

    !insertmacro APP_ASSOCIATE_URL "${PRODUCT_NAME}" "URL:${PRODUCT_NAME} Protocol" \
       "Open with URL" "$INSTDIR\${PRODUCT_NAME}.exe $\"%1$\""
;--------
    !ifdef Skel
        !insertmacro skel04
    !endif
;--------

SectionEnd


; ============================================================================
; UNINSTALL SECTIONS
; ============================================================================
!ifndef SIGN  ;skip this section when called from SignArtisan
Section Uninstall
;---------
    !ifdef Skel
        !insertmacro skel05
    !endif
;---------
    Delete "$INSTDIR\${PRODUCT_NAME}.url"
    Delete "$INSTDIR\uninstall.exe"
    Delete "$INSTDIR\${PRODUCT_NAME}.exe"
    Delete "$INSTDIR\${PRODUCT_NAME}.exe.manifest"
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
    Delete "$INSTDIR\Nunito-Regular.ttf"
    Delete "$INSTDIR\Nunito-SemiBold.ttf"
    Delete "$INSTDIR\Nunito-ExtraBold.ttf"
    Delete "$INSTDIR\NotoSansMono-Regular.ttf"
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
    Delete "$INSTDIR\roboto-300.woff2"
    Delete "$INSTDIR\roboto-600.woff2"
    Delete "$INSTDIR\roboto-regular.woff2"
    Delete "$INSTDIR\android-chrome-192x192.png"
    Delete "$INSTDIR\android-chrome-512x512.png"
    Delete "$INSTDIR\apple-touch-icon.png"
    Delete "$INSTDIR\browserconfig.xml"
    Delete "$INSTDIR\favicon-16x16.png"
    Delete "$INSTDIR\favicon-32x32.png"
    Delete "$INSTDIR\favicon-48x48.png"
    Delete "$INSTDIR\favicon.ico"
    Delete "$INSTDIR\mstile-150x150.png"
    Delete "$INSTDIR\safari-pinned-tab.svg"
    Delete "$INSTDIR\site.webmanifest"
    Delete "$INSTDIR\artisan.tpl"
    Delete "$INSTDIR\green_scale_widget.tpl"
    Delete "$INSTDIR\green-android-chrome-192x192.png"
    Delete "$INSTDIR\green-android-chrome-512x512.png"
    Delete "$INSTDIR\green-apple-touch-icon.png"
    Delete "$INSTDIR\green-favicon-16x16.png"
    Delete "$INSTDIR\green-favicon-32x32.png"
    Delete "$INSTDIR\green-favicon-48x48.png"
    Delete "$INSTDIR\green-favicon.ico"
    Delete "$INSTDIR\green-site.webmanifest"
    Delete "$INSTDIR\roasted_scale_widget.tpl"
    Delete "$INSTDIR\roasted-android-chrome-192x192.png"
    Delete "$INSTDIR\roasted-android-chrome-512x512.png"
    Delete "$INSTDIR\roasted-apple-touch-icon.png"
    Delete "$INSTDIR\roasted-favicon-16x16.png"
    Delete "$INSTDIR\roasted-favicon-32x32.png"
    Delete "$INSTDIR\roasted-favicon-48x48.png"
    Delete "$INSTDIR\roasted-favicon.ico"
    Delete "$INSTDIR\roasted-site.webmanifest"
    Delete "$INSTDIR\artisan-combo-mark-white.svg"
    Delete "$INSTDIR\fitty_patched.js"
    Delete "$INSTDIR\bigtext.js"
    Delete "$INSTDIR\sorttable.js"
    Delete "$INSTDIR\report-template.htm"
    Delete "$INSTDIR\report-template-pdf.htm"
    Delete "$INSTDIR\roast-template.htm"
    Delete "$INSTDIR\roast-template-pdf.htm"
    Delete "$INSTDIR\ranking-template.htm"
    Delete "$INSTDIR\ranking-template-pdf.htm"
    Delete "$INSTDIR\jquery-1.11.1.min.js"
    Delete "$INSTDIR\qt.conf"
    Delete "$INSTDIR\vc_redist.x64.exe"
    Delete "$INSTDIR\logging.json"
    Delete "$INSTDIR\artisan_public_key.pem"
    Delete "$INSTDIR\uninst.exe"  ;if left around after upgrading an older version

    SetShellVarContext all

    Delete "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\Website.lnk"
    Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"

    RMDir "$SMPROGRAMS\${PRODUCT_NAME}"
    RMDir "$INSTDIR"

    DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
    DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
    DeleteRegKey HKCR ".alog"
    DeleteRegKey HKCR "${PRODUCT_NAME}.Profile\DefaultIcon"
    DeleteRegKey HKCR "${PRODUCT_NAME}.Profile\shell"
    DeleteRegKey HKCR "${PRODUCT_NAME}.Profile\shell\open\command"
    DeleteRegKey HKCR "${PRODUCT_NAME}.Profile"

    !insertmacro APP_UNASSOCIATE "alog" "${PRODUCT_NAME}.Profile"
    !insertmacro APP_UNASSOCIATE "alrm" "${PRODUCT_NAME}.Alarms"
    !insertmacro APP_UNASSOCIATE "apal" "${PRODUCT_NAME}.Palettes"
    !insertmacro APP_UNASSOCIATE "athm" "${PRODUCT_NAME}.Theme"
    !insertmacro APP_UNASSOCIATE "aset" "${PRODUCT_NAME}.Settings"
    !insertmacro APP_UNASSOCIATE "wg" "${PRODUCT_NAME}.Wheel"

    DeleteRegKey HKCR "${PRODUCT_NAME}\shell"
    DeleteRegKey HKCR "${PRODUCT_NAME}\shell\open\command"
    DeleteRegKey HKCR "${PRODUCT_NAME}"

;--------
    !ifdef Skel
        !insertmacro skel05
    !endif
;--------

SectionEnd
!endif
