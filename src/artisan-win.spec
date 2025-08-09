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
import subprocess
import os

from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_dynamic_libs

# Set up the logger
logging.basicConfig(level=logging.INFO)

# Function to perform file copy
def copy_file(source_file, destination_file, fatal=True):
    #logging.info("Copying %s",source_file)
    copy_command = f'copy "{source_file}" "{destination_file}"'
    exit_code = subprocess.call(copy_command, stdout=subprocess.DEVNULL, shell=True)
    if exit_code != 0:
        msg = f'Copy operation failed {source_file} {destination_file}'
        logging.error(msg)
        if fatal:
            sys.exit('Fatal Error')

# Function to perform xcopy
def xcopy_files(source_dir, destination_dir, fatal=True):
    #logging.info("Copying %s",source_file)
    xcopy_command = f'xcopy "{source_dir}" "{destination_dir}"  /y /S'
    exit_code = subprocess.call(xcopy_command, stdout=subprocess.DEVNULL, shell=True)
    if exit_code != 0:
        msg =f'Xcopy operation failed {source_dir} {destination_dir}'
        logging.error(msg)
        if fatal:
            sys.exit('Fatal Error')

# Function to make dir
def make_dir(source_dir, fatal=True):
    mkdir_command = f'mkdir "{source_dir}"'
    exit_code = subprocess.call(mkdir_command, shell=True)
    if exit_code != 0:
        msg =f'mkdir operation failed {source_dir}'
        logging.error(msg)
        if fatal:
            sys.exit('Fatal Error')

# Function to remove dir
def remove_dir(source_dir, fatal=True):
    rmdir_command = f'rmdir /q /s {source_dir}'
    exit_code = subprocess.call(rmdir_command, shell=True)
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
    exit_code = subprocess.call(del_command, shell=True)
    if exit_code != 0:
        msg =f'del operation failed {file_path}'
        logging.error(msg)
        if fatal:
            sys.exit('Fatal Error')


###################################
# Setup the environment
###################################
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
TARGET = 'dist\\' + NAME + '\\'
PYTHON_PACKAGES = PYTHON + r'\Lib\site-packages'
PYQT_QT = PYTHON_PACKAGES + r'\PyQt' + PYQT + r'\Qt'
PYQT_QT_BIN = PYQT_QT + r'\bin'
PYQT_QT_TRANSLATIONS = QT_TRANSL
YOCTO_BIN = PYTHON_PACKAGES + r'\yoctopuce\cdll'
SNAP7_BIN = PYTHON_PACKAGES + r'\snap7\lib'
PHIDGET22_BIN = PYTHON_PACKAGES + r'\Phidget22\.libs'

from PyInstaller.utils.hooks import is_module_satisfies
if is_module_satisfies('scipy >= 1.3.2'):
    SCIPY_BIN = PYTHON_PACKAGES + r'\scipy\.libs'
else:
    SCIPY_BIN = PYTHON_PACKAGES + r'\scipy\extra-dll'

logging.info("** ARTISAN_LEGACY: %s", ARTISAN_LEGACY)
logging.info("** QT_TRANSL: %s",QT_TRANSL)

###################################
# Pyinstaller core
###################################
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
                            'PyQt6.QtWebChannel',
                            'PyQt6.QtWebEngineCore',
                            'importlib_resources',
                            'winrt.windows.foundation.collections'
                            ]

datas = collect_data_files('bleak', subdir=r'backends\winrt')

binaries = collect_dynamic_libs('bleak')
block_cipher = None

a = Analysis(['artisan.py'],
             pathex=[PYQT_QT_BIN, ARTISAN_SRC, SCIPY_BIN, PHIDGET22_BIN],
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


###################################
# copy additional needed files
###################################
logging.info(">>>>> Copying additional needed files")

# requires the Microsoft Visual C++ 2015 Redistributable Package (x64), vc_redist.x64.exe, to be located above the source directory
copy_file(r'..\vc_redist.x64.exe', TARGET)

copy_file('README.txt',TARGET)
copy_file(r'..\LICENSE', TARGET + r'\LICENSE.txt')
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
        'qtbase_cs.qm',
        'qtbase_da.qm',
        'qtbase_fa.qm',
        'qtbase_gd.qm',
        'qtbase_lv.qm',
        'qtbase_nl.qm',
        'qtbase_pt_BR.qm',
        'qtbase_ru.qm',
        'qtbase_sk.qm',
        'qtbase_zh_CN.qm',
#        'qtconnectivity_da.qm',
#        'qtconnectivity_ko.qm',
#        'qtconnectivity_nl.qm',
#        'qtconnectivity_pt_BR.qm',
#        'qtconnectivity_zh_CN.qm',
        ]:
        copy_file(QT_TRANSL + '\\' + tr, TARGET + 'translations',False)


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
    r'includes\roboto-300.woff2',
    r'includes\roboto-600.woff2',
    r'includes\roboto-regular.woff2',
    r'includes\artisan.tpl',
    r'includes\scale_widget.tpl',
    r'includes\fitty_patched.js',
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


###################################
# Remove unneeded files and folders
###################################
# remove unused translations of unused Qt modules
rootdir = f'{TARGET}_internal'
SUPPORTED_LANGUAGES = ['ar', 'cs', 'da', 'de','el','en','es','fa','fi','fr','gd', 'he','hu','id','it','ja','ko','lv', 'nl','no','pl','pt_BR','pt','sk', 'sv','th','tr','uk','vi','zh_CN','zh_TW']

qt_trans_prefix_keep = {
    'qtbase',
    'qt'
}
qt_trans_file_keep = {
    'en-US.pak'
}
qt_trans_prefix_delete = {
    'qt_help'
}

logging.info(">>>>> Removing unneeded Qt translation files")
for qt_dir in [r'PyQt5\Qt5\translations', r'PyQt6\Qt6\translations']:
    qt = rootdir + '\\' + qt_dir
    for root, _, files in os.walk(qt):
        for file in files:
            if (any(file.startswith(f'{x}_') for x in qt_trans_prefix_delete) or
                    not ( (any(file.startswith(f'{x}_') for x in qt_trans_prefix_keep) and any(file.endswith(f'_{x}.qm') for x in SUPPORTED_LANGUAGES)) or
                         any(file == f'{x}' for x in qt_trans_file_keep))):
                file_path = os.path.join(root, file)
                del_file(file_path, True)
                #logging.info(file_path)

logging.info(">>>>> Removing unneeded language support from babel")
for root, _, files in os.walk(rootdir + r'\babel\locale-data'):
    for file in files:
        if file.endswith('.dat') and file != 'root.dat' and (('_' not in file and file.split('.')[0] not in SUPPORTED_LANGUAGES) or
                ('_' in file and file.split('.')[0] not in SUPPORTED_LANGUAGES)):
            file_path = os.path.join(root, file)
            del_file(file_path, True)
            #logging.info(file_path)

# remove unneeded files and folders from Windows (not implemented for legacy)
if not ARTISAN_LEGACY=='True':
    logging.info(">>>>> Removing unneeded files")
    for fn in [
        r'_internal\PyQt6\Qt6\bin\Qt6Multimedia.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6MultimediaQuick.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6PdfQuick.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6PositioningQuick.dll',
#        r'_internal\PyQt6\Qt6\bin\Qt6QmlWorkerScript.dll',  # required for pyqt6 v6.8
        r'_internal\PyQt6\Qt6\bin\Qt6Quick3D.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6Quick3DAssetImport.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6Quick3DAssetUtils.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6Quick3DEffects.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6Quick3DHelpers.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6Quick3DHelpersImpl.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6Quick3DParticles.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6Quick3DPhysics.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6Quick3DPhysicsHelpers.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6Quick3DRuntimeRender.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6Quick3DSpatialAudio.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6Quick3DUtils.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickControls2.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickControls2Basic.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickControls2BasicStyleImpl.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickControls2Fusion.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickControls2FusionStyleImpl.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickControls2Imagine.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickControls2ImagineStyleImpl.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickControls2Impl.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickControls2Material.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickControls2MaterialStyleImpl.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickControls2Universal.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickControls2UniversalStyleImpl.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickDialogs2.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickDialogs2QuickImpl.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickDialogs2Utils.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickLayouts.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickParticles.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickShapes.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickTemplates2.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickTest.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickTimeline.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6QuickTimelineBlendTrees.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6RemoteObjects.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6RemoteObjectsQml.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6Sensors.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6SensorsQuick.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6SerialPort.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6ShaderTools.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6SpatialAudio.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6Test.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6TextToSpeech.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6WebChannelQuick.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6WebEngineQuick.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6WebEngineQuickDelegatesQml.dll',
        r'_internal\PyQt6\Qt6\bin\Qt6WebSockets.dll',
        r'_internal\PyQt6\Qt6\plugins\platforms\qminimal.dll',
        r'_internal\PyQt6\Qt6\plugins\platforms\qoffscreen.dll',
        r'_internal\PyQt6\Qt6\plugins\imageformats\qicns.dll',
        r'_internal\PyQt6\Qt6\plugins\imageformats\qtga.dll',
        r'_internal\PyQt6\Qt6\plugins\imageformats\qtiff.dll',
        r'_internal\PyQt6\Qt6\plugins\imageformats\qwebp.dll',
        ]:
        del_file(f'{TARGET}{fn}', True)

    # The api-ms-win*.dll files are generated on Appveyer CI and are not required
    for root, _, files in os.walk(TARGET):
        for file in files:
            if (file.startswith('api-ms-win')):
                file_path = os.path.join(root, file)
                del_file(file_path, True)

    logging.info(">>>>> Removing unneeded folders")
    for dp in [
        r'_internal\PyQt6\Qt6\plugins\generic',
        r'_internal\PyQt6\Qt6\plugins\networkinformation',
        r'_internal\PyQt6\Qt6\plugins\position',
        r'_internal\PyQt6\Qt6\plugins\tls',
        r'_internal\PyQt6\Qt6\qml',
        r'_internal\matplotlib\mpl-data\sample_data',
        ]:
        remove_dir(f'{TARGET}{dp}', True)



###################################
# log the size of install folder
###################################
def get_size(path):
    size = 0
    # If the path is a file, get its size directly
    if os.path.isfile(path):
        size += os.path.getsize(path)
    # If the path is a directory, walk through all files and sum their sizes
    elif os.path.isdir(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                size += os.path.getsize(file_path)
    return size

def readable_bytes(size_in_bytes):
    # Converts bytes to readable format
    for unit in ['Bytes', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0

# Get total size in bytes minus the vc_redist.x64.exe file
size_bytes = get_size(TARGET) - get_size(TARGET + 'vc_redist.x64.exe')
logging.info(f'>>>>> Net size of install folder: {readable_bytes(size_bytes)}')

###################################
