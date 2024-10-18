# ABOUT
# Artisan pyinstaller specification file

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, Dave Baxter 2023

# -*- mode: python -*-

import logging
import sys

from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_dynamic_libs

# Set up the logger
logging.basicConfig(level=logging.INFO)

# Function to perform file copy
def copy_file(source_file, destination_file, fatal=True):
    #logging.info("Copying %s",source_file)
    copy_command = f'copy "{source_file}" "{destination_file}"'
    exit_code = os.system(copy_command)
    if exit_code != 0:
        msg = f'Copy operation failed {source_file} {destination_file}'
        logging.error(msg)
        if fatal:
            sys.exit('Fatal Error')

# Function to perform xcopy
def xcopy_files(source_dir, destination_dir, fatal=True):
    #logging.info("Copying %s",source_file)
    xcopy_command = f'xcopy "{source_dir}" "{destination_dir}"  /y /S'
    exit_code = os.system(xcopy_command)
    if exit_code != 0:
        msg =f'Xcopy operation failed {source_dir} {destination_dir}'
        logging.error(msg)
        if fatal:
            sys.exit('Fatal Error')

# Function to make dir
def make_dir(source_dir, fatal=True):
    mkdir_command = f'mkdir "{source_dir}"'
    exit_code = os.system(mkdir_command)
    if exit_code != 0:
        msg =f'mkdir operation failed {source_dir}'
        logging.error(msg)
        if fatal:
            sys.exit('Fatal Error')

# Function to remove dir
def remove_dir(source_dir, fatal=True):
    rmdir_command = f'rmdir /q /s {source_dir}'
    exit_code = os.system(rmdir_command)
    if exit_code != 0:
        msg =f'rmdir operation failed {source_dir}'
        logging.error(msg)
        if fatal:
            sys.exit('Fatal Error')

# Function to check if a file exists
def check_file_exists(file_path, fatal=True):
    if not os.path.isfile(file_path):
        msg = f'File does not exist: {file_path} '
        logging.error(msg)
        if fatal:
            sys.exit('Fatal Error')

# Function to delete file
def del_file(file_path, fatal=True):
    del_command = f'del /q {file_path}'
    exit_code = os.system(del_command)
    if exit_code != 0:
        msg =f'del operation failed {file_path}'
        logging.error(msg)
        if fatal:
            sys.exit('Fatal Error')

block_cipher = None

import os
if os.environ.get('APPVEYOR'):
    ARTISAN_SRC = r'C:\projects\artisan\src'
    PYTHON = os.environ.get('PYTHON_PATH')
    PYQT = os.environ.get('PYQT')
    QT_TRANSL = os.environ.get('QT_TRANSL')
    ARTISAN_LEGACY = os.environ.get('ARTISAN_LEGACY')
else:
    msg =f'artisan-win.spec is intended only to run on Appveyor CI.'
    logging.error(msg)
    sys.exit('Fatal Error')

NAME = 'artisan'

logging.info("** ARTISAN_LEGACY: %s", ARTISAN_LEGACY)
logging.info("** QT_TRANSL: %s",QT_TRANSL)

##
TARGET = 'dist\\' + NAME + '\\'
PYTHON_PACKAGES = PYTHON + r'\Lib\site-packages'
PYQT_QT = PYTHON_PACKAGES + r'\PyQt' + PYQT + r'\Qt'
PYQT_QT_BIN = PYQT_QT + r'\bin'
PYQT_QT_TRANSLATIONS = QT_TRANSL
YOCTO_BIN = PYTHON_PACKAGES + r'\yoctopuce\cdll'
SNAP7_BIN = PYTHON_PACKAGES + r'\snap7\lib'

from PyInstaller.utils.hooks import is_module_satisfies
if is_module_satisfies('scipy >= 1.3.2'):
    SCIPY_BIN = PYTHON_PACKAGES + r'\scipy\.libs'
else:
    SCIPY_BIN = PYTHON_PACKAGES + r'\scipy\extra-dll'

#os.system(PYTHON + r'\Scripts\pylupdate5 artisan.pro')

hiddenimports_list=['charset_normalizer.md__mypyc', # part of requests 2.28.2 # see https://github.com/pyinstaller/pyinstaller-hooks-contrib/issues/534
                            'matplotlib.backends.backend_pdf',
                            'matplotlib.backends.backend_svg',
                            'scipy.spatial.transform._rotation_groups',
                            'scipy.special.cython_special',
                            'scipy._lib.messagestream',
                            'pywintypes',
                            'win32cred',
                            'win32timezone',
                            'babel.numbers'  # should not be needed as it got fixed in pyinstaller 6.11
                            ]
# Add the hidden imports not required by legacy Windows.
if not ARTISAN_LEGACY=='True':
    hiddenimports_list[len(hiddenimports_list):] = [
                            'importlib_resources',
                            'winrt.windows.foundation.collections'
                            ]

datas = collect_data_files('bleak', subdir=r'backends\winrt')
binaries = collect_dynamic_libs('bleak')
logging.info(">>>>> Appending hidden imports")

a = Analysis(['artisan.py'],
             pathex=[PYQT_QT_BIN, ARTISAN_SRC, SCIPY_BIN],
             binaries=binaries,
             datas=datas, # + copy_metadata('tzdata')
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             hiddenimports=hiddenimports_list,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name=NAME,
          debug=False,
          strip=False, # =True fails
          upx=True, # not installed
          icon='artisan.ico',
          version='version_info-win.txt',
          console=False) # was True

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False, # =True fails
               upx=True, # not installed
               name=NAME)


# assumes the Microsoft Visual C++ 2015 Redistributable Package (x64), vc_redist.x64.exe, is located above the source directory
copy_file(r'..\vc_redist.x64.exe', TARGET)

copy_file('README.txt',TARGET)
copy_file(r'..\LICENSE', TARGET + r'\LICENSE.txt')
#os.system('copy qt-win.conf ' + TARGET + 'qt.conf')
make_dir(TARGET + 'Wheels')
make_dir(TARGET + r'Wheels\Cupping')
make_dir(TARGET + r'Wheels\Other')
make_dir(TARGET + r'Wheels\Roasting')
copy_file(r'Wheels\Cupping\*', TARGET + r'Wheels\Cupping')
copy_file(r'Wheels\Other\*', TARGET + r'Wheels\Other')
copy_file(r'Wheels\Roasting\*', TARGET + r'Wheels\Roasting')

make_dir(TARGET + 'translations')
copy_file(r'translations\*.qm', TARGET + 'translations')
for tr in [
    'qtbase_ar.qm',
    'qtbase_de.qm',
    'qtbase_en.qm',
    'qtbase_es.qm',
    'qtbase_fi.qm',
    'qtbase_fr.qm',
    'qtbase_he.qm',
    'qtbase_hu.qm',
    'qtbase_it.qm',
    'qtbase_ja.qm',
    'qtbase_ko.qm',
    'qtbase_pl.qm',
    'qtbase_uk.qm',
    'qtbase_tr.qm',
    'qtbase_zh_TW.qm',
#    'qtconnectivity_de.qm',
#    'qtconnectivity_en.qm',
#    'qtconnectivity_es.qm',
#    'qtconnectivity_hu.qm',
#    'qtconnectivity_ko.qm',
#    'qtconnectivity_tr.qm',
    ]:
    copy_file(QT_TRANSL + '\\' + tr, TARGET + 'translations',False)
# Add the translations not available in PyQt5 for legacy Windows.
if not ARTISAN_LEGACY=='True':
    for tr in [
        'qtbase_da.qm',
        'qtbase_fa.qm',
        'qtbase_gd.qm',
        'qtbase_lv.qm',
        'qtbase_nl.qm',
        'qtbase_pt_BR.qm',
        'qtbase_zh_CN.qm',
#        'qtconnectivity_da.qm',
#        'qtconnectivity_ko.qm',
#        'qtconnectivity_nl.qm',
#        'qtconnectivity_pt_BR.qm',
#        'qtconnectivity_zh_CN.qm',
        ]:
        copy_file(QT_TRANSL + '\\' + tr, TARGET + 'translations',False)


# this directory no longer exists
#remove_dir(TARGET + 'mpl-data\sample_data',False)

# YOCTO HACK BEGIN: manually copy over the dlls
make_dir(TARGET + r'_internal\yoctopuce\cdll')
copy_file(YOCTO_BIN + r'\yapi64.dll', TARGET + r'_internal\yoctopuce\cdll')
# YOCTO HACK END

# copy Snap7 lib
copy_file(SNAP7_BIN + r'\snap7.dll', TARGET + r'_internal')

for fn in [
    'artisan.png',
    'artisanAlarms.ico',
    'artisanProfile.ico',
    'artisanPalettes.ico',
    'artisanTheme.ico',
    'artisanSettings.ico',
    'artisanWheel.ico',
    r'includes\Humor-Sans.ttf',
    r'includes\dijkstra.ttf',
    r'includes\ComicNeue-Regular.ttf',
    r'includes\xkcd-script.ttf',
    r'includes\WenQuanYiZenHei-01.ttf',
    r'includes\WenQuanYiZenHeiMonoMedium.ttf',
    r'includes\SourceHanSansCN-Regular.otf',
    r'includes\SourceHanSansHK-Regular.otf',
    r'includes\SourceHanSansJP-Regular.otf',
    r'includes\SourceHanSansKR-Regular.otf',
    r'includes\SourceHanSansTW-Regular.otf',
    r'includes\alarmclock.eot',
    r'includes\alarmclock.svg',
    r'includes\alarmclock.ttf',
    r'includes\alarmclock.woff',
    r'includes\artisan.tpl',
    r'includes\bigtext.js',
    r'includes\sorttable.js',
    r'includes\report-template.htm',
    r'includes\roast-template.htm',
    r'includes\ranking-template.htm',
    r'includes\jquery-1.11.1.min.js',
    r'includes\android-chrome-192x192.png',
    r'includes\android-chrome-512x512.png',
    r'includes\apple-touch-icon.png',
    r'includes\browserconfig.xml',
    r'includes\favicon-16x16.png',
    r'includes\favicon-32x32.png',
    r'includes\favicon.ico',
    r'includes\mstile-150x150.png',
    r'includes\safari-pinned-tab.svg',
    r'includes\site.webmanifest',
    r'includes\logging.yaml',
    ]:
    copy_file(fn, TARGET)

make_dir(TARGET + 'Machines')
xcopy_files(r'includes\Machines', TARGET + 'Machines')

make_dir(TARGET + 'Themes')
xcopy_files(r'includes\Themes', TARGET + 'Themes')

make_dir(TARGET + 'Icons')
xcopy_files(r'includes\Icons', TARGET + 'Icons')



if not ARTISAN_LEGACY=='True':
    logging.info(">>>>> Deleting unneeded files")
    for fn in [
        TARGET + r'\_internal\Artisan\_internal\api-ms-win-*',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Multimedia.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6MultimediaQuick.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6PdfQuick.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6PositioningQuick.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QmlWorkerScript.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Quick3D.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Quick3DAssetImport.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Quick3DAssetUtils.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Quick3DEffects.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Quick3DHelpers.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Quick3DHelpersImpl.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Quick3DParticles.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Quick3DPhysics.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Quick3DPhysicsHelpers.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Quick3DRuntimeRender.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Quick3DSpatialAudio.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Quick3DUtils.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickControls2.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickControls2Basic.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickControls2BasicStyleImpl.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickControls2Fusion.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickControls2FusionStyleImpl.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickControls2Imagine.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickControls2ImagineStyleImpl.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickControls2Impl.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickControls2Material.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickControls2MaterialStyleImpl.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickControls2Universal.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickControls2UniversalStyleImpl.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickDialogs2.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickDialogs2QuickImpl.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickDialogs2Utils.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickLayouts.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickParticles.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickShapes.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickTemplates2.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickTest.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickTimeline.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6QuickTimelineBlendTrees.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6RemoteObjects.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6RemoteObjectsQml.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Sensors.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6SensorsQuick.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6SerialPort.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6ShaderTools.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6SpatialAudio.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6Test.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6TextToSpeech.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6WebChannelQuick.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6WebEngineQuick.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6WebEngineQuickDelegatesQml.dll',
        TARGET + r'\_internal\PyQt6\Qt6\bin\Qt6WebSockets.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\generic\qtuiotouchplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\networkinformation\qnetworklistmanager.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\platforms\qminimal.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\platforms\qoffscreen.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\position\qtposition_nmea.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\position\qtposition_positionpoll.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\position\qtposition_winrt.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\tls\qcertonlybackend.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\tls\qopensslbackend.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\tls\qschannelbackend.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtMultimedia\quickmultimediaplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtPositioning\positioningquickplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQml\Base\qmlplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQml\Models\modelsplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQml\WorkerScript\workerscriptplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQml\qmlmetaplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick3D\AssetUtils\qtquick3dassetutilsplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick3D\Effects\qtquick3deffectplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick3D\Helpers\impl\qtquick3dhelpersimplplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick3D\Helpers\qtquick3dhelpersplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick3D\Particles3D\qtquick3dparticles3dplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick3D\Physics\Helpers\qtquick3dphysicshelpersplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick3D\Physics\qquick3dphysicsplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick3D\SpatialAudio\quick3dspatialaudioplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick3D\qquick3dplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Controls\Basic\impl\qtquickcontrols2basicstyleimplplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Controls\Basic\qtquickcontrols2basicstyleplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Controls\Fusion\impl\qtquickcontrols2fusionstyleimplplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Controls\Fusion\qtquickcontrols2fusionstyleplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Controls\Imagine\impl\qtquickcontrols2imaginestyleimplplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Controls\Imagine\qtquickcontrols2imaginestyleplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Controls\Material\impl\qtquickcontrols2materialstyleimplplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Controls\Material\qtquickcontrols2materialstyleplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Controls\Universal\impl\qtquickcontrols2universalstyleimplplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Controls\Universal\qtquickcontrols2universalstyleplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Controls\Windows\qtquickcontrols2windowsstyleplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Controls\impl\qtquickcontrols2implplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Controls\qtquickcontrols2plugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Dialogs\qtquickdialogsplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Dialogs\quickimpl\qtquickdialogs2quickimplplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Layouts\qquicklayoutsplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\NativeStyle\qtquickcontrols2nativestyleplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Particles\particlesplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Pdf\pdfquickplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Shapes\qmlshapesplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Templates\qtquicktemplates2plugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Timeline\BlendTrees\qtquicktimelineblendtreesplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Timeline\qtquicktimelineplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\Window\quickwindowplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\qtquick2plugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtQuick\tooling\quicktoolingplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtRemoteObjects\declarative_remoteobjectsplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtSensors\sensorsquickplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtTest\quicktestplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtTextToSpeech\texttospeechqmlplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtWebChannel\webchannelquickplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtWebEngine\ControlsDelegates\qtwebenginequickdelegatesplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtWebEngine\qtwebenginequickplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\qml\QtWebSockets\qmlwebsocketsplugin.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\imageformats\qicns.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\imageformats\qtga.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\imageformats\qtiff.dll',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\imageformats\qwebp.dll',
        TARGET + r'\_internal\yoctopuce\cdll\yapi.dll',      # could simply not copy this one above
        ]:
        del_file(fn, False)

    logging.info(">>>>> Removing unneeded folders")
    for dp in [
        TARGET + r'\_internal\PyQt6\Qt6\plugins\generic',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\networkinformation',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\position',
        TARGET + r'\_internal\PyQt6\Qt6\plugins\tls',
        TARGET + r'\_internal\PyQt6\Qt6\qml',
        TARGET + r'\_internal\matplotlib\mpl-data\sample_data',
        ]:
        remove_dir(dp,False)

