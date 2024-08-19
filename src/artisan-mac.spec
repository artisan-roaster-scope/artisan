# -*- mode: python ; coding: utf-8 -*-
# ABOUT
# artisan-mac.spec script for Artisan macOS builds using pyinstaller
#
# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# AUTHOR
# Dave Baxter, Marko Luther 2023
"""

Usage:
    pyinstaller artisan-mac.spec
"""

import os
import subprocess
import plistlib
from PyInstaller.utils.hooks import get_package_paths

import sys
sys.path.insert(1, SPECPATH)
import artisanlib  # previous line needed to successfully load local module lib

onefile = False
block_cipher = None

# current version
VERSION = artisanlib.__version__
LICENSE = 'GNU General Public License (GPL)'

try:
    QTDIR = os.environ['QT_PATH'] + r'/'
except Exception:
    from os.path import expanduser
    HOME = expanduser('~')
    QTDIR = HOME + r'/Qt5.14.2/5.14.2/clang_64/'

DATA_FILES = [
        (r'artisanProfile.icns', '.'),
        (r'artisanAlarms.icns', '.'),
        (r'artisanPalettes.icns', '.'),
        (r'artisanSettings.icns', '.'),
        (r'artisanTheme.icns', '.'),
        (r'artisanWheel.icns', '.'),
        (r'includes/alarmclock.eot', '.'),
        (r'includes/alarmclock.svg', '.'),
        (r'includes/alarmclock.ttf', '.'),
        (r'includes/alarmclock.woff', '.'),
        (r'includes/artisan.tpl', '.'),
        (r'includes/bigtext.js', '.'),
        (r'includes/jquery-1.11.1.min.js', '.'),
        (r'includes/android-chrome-192x192.png', '.'),
        (r'includes/android-chrome-512x512.png', '.'),
        (r'includes/apple-touch-icon.png', '.'),
        (r'includes/browserconfig.xml', '.'),
        (r'includes/favicon-16x16.png', '.'),
        (r'includes/favicon-32x32.png', '.'),
        (r'includes/favicon.ico', '.'),
        (r'includes/mstile-150x150.png', '.'),
        (r'includes/safari-pinned-tab.svg', '.'),
        (r'includes/site.webmanifest', '.'),
        (r'includes/sorttable.js', '.'),
        (r'includes/report-template.htm', '.'),
        (r'includes/roast-template.htm', '.'),
        (r'includes/ranking-template.htm', '.'),
        (r'includes/Humor-Sans.ttf', '.'),
        (r'includes/WenQuanYiZenHei-01.ttf', '.'),
        (r'includes/WenQuanYiZenHeiMonoMedium.ttf', '.'),
        (r'includes/SourceHanSansCN-Regular.otf', '.'),
        (r'includes/SourceHanSansHK-Regular.otf', '.'),
        (r'includes/SourceHanSansJP-Regular.otf', '.'),
        (r'includes/SourceHanSansKR-Regular.otf', '.'),
        (r'includes/SourceHanSansTW-Regular.otf', '.'),
        (r'includes/dijkstra.ttf', '.'),
        (r'includes/ComicNeue-Regular.ttf', '.'),
        (r'includes/xkcd-script.ttf', '.'),
        (r'includes/Machines', './Machines'),
        (r'includes/Themes', './Themes'),
        (r'includes/Icons', './Icons'),
        (r'includes/logging.yaml', '.')
]

# add Artisan translations to DATA_FILES
DATA_FILES.extend(
    [(f'translations/{file}', './translations') for root,dirs,files in os.walk('translations') for file in files if (file.split('.')[1]) == 'qm'])

# add snap7 libs
BINARIES = [(os.path.join(get_package_paths('snap7')[1], 'lib/libsnap7.dylib'), 'snap7/lib' )]
# add yocto libs
yocto_lib_path = os.path.join(get_package_paths('yoctopuce')[1], 'cdll')
BINARIES.extend([(os.path.join(yocto_lib_path, fn),'yoctopuce/cdll') for fn in os.listdir(yocto_lib_path) if fn.endswith('.dylib')])
# brew installed libusb is added automatically by pyinstaller

a = Analysis(['artisan.py'],
             binaries=BINARIES,
             datas=DATA_FILES,
             hiddenimports=['babel.numbers'],
             hookspath=[],
             runtime_hooks=[],
             excludes= [],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
            a.scripts,
            a.binaries if onefile else [],
            a.zipfiles if onefile else [],
            a.datas if onefile else [],
            exclude_binaries=not onefile,
            name='Artisan',
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=False,  # binary compressor: https://github.com/upx/upx
            upx_exclude=[],
            runtime_tmpdir=None,
            console=False,
            disable_windowed_traceback=False,
            argv_emulation=False, # False for GUI apps
            target_arch='universal2', #'x86_64', #'universal2',
            codesign_identity='6M3Z6W45L4', #None,
            entitlements_file='Artisan.entitlements' #None
            )

try:
    minimumSystemVersion = os.environ['MACOSX_DEPLOYMENT_TARGET']
except Exception: # pylint: disable=broad-except
    minimumSystemVersion = '12.0'

plist = {}
with open('Info.plist', 'rb') as infile:
    plist = plistlib.load(infile)
    plist.update({ 'CFBundleDisplayName': 'Artisan',
                    'CFBundleGetInfoString': 'Artisan, Roast Logger',
                    'CFBundleIdentifier': 'org.artisan-scope.artisan',
                    'CFBundleShortVersionString': VERSION,
                    'CFBundleVersion': 'Artisan ' + VERSION,
                    'LSMinimumSystemVersion': minimumSystemVersion,
                    'LSMultipleInstancesProhibited': 'false',
                    'LSArchitecturePriority': ['arm64', 'x86_64'],
                    'NSHumanReadableCopyright': LICENSE,
                    'NSHighResolutionCapable': True
                })

bundle_obj = exe

if not onefile:
    coll = COLLECT(
            exe,
            a.binaries,
            a.zipfiles,
            a.datas,
            strip=False,
            upx=False,
            upx_exclude=[],
            name='Test',
        )
    bundle_obj = coll

app = BUNDLE(bundle_obj,
          name='Artisan.app',
          icon='artisan.icns',
          bundle_identifier='org.artisan-scope.artisan',
          info_plist=plist)

#------

subprocess.check_call(r'rm -rf dist/Test',shell = True)
subprocess.check_call(r'cp README.txt dist',shell = True)
subprocess.check_call(r'cp ../LICENSE dist/LICENSE.txt',shell = True)
subprocess.check_call(r'mkdir dist/Wheels',shell = True)
subprocess.check_call(r'mkdir dist/Wheels/Cupping',shell = True)
subprocess.check_call(r'mkdir dist/Wheels/Other',shell = True)
subprocess.check_call(r'mkdir dist/Wheels/Roasting',shell = True)
subprocess.check_call(r'cp Wheels/Cupping/* dist/Wheels/Cupping',shell = True)
subprocess.check_call(r'cp Wheels/Other/* dist/Wheels/Other',shell = True)
subprocess.check_call(r'cp Wheels/Roasting/* dist/Wheels/Roasting',shell = True)
try:
    subprocess.check_call('rm -rf dist/Artisan.app/Contents/Resources/matplotlib/mpl-data/sample_data',shell = True)
except Exception: # pylint: disable=broad-except
    pass

os.chdir('./dist')

# add localization stubs to make macOS translate the systems menu item and native dialogs
for lang in ['ar', 'da', 'de','el','en','es','fa','fi','fr','gd', 'he','hu','id','it','ja','ko','lv', 'nl','no','pl','pt_BR','pt','sk', 'sv','th','tr','uk','vi','zh_CN','zh_TW']:
    loc_dir = r'Artisan.app/Contents/Resources/' + lang + r'.lproj'
    subprocess.check_call(r'mkdir ' + loc_dir,shell = True)
    subprocess.check_call(r'touch ' + loc_dir + r'/Localizable.string',shell = True)


# for Qt
print('*** Removing unused Qt frameworks ***')

# QT modules to keep frameworks:
Qt_modules = [
    'QtCore',
    'QtGui',
    'QtWidgets',
    'QtSvg',
    'QtPrintSupport',
    'QtNetwork',
    'QtDBus',
    'QtBluetooth',
    'QtConcurrent', # not on PyQt6.2, but PyQt6.4 and PyQt5.x
# needed for QtWebEngine HTML2PDF export:
    'QtWebEngineWidgets',
    'QtWebEngineCore',
    'QtWebEngine', # not on PyQt6
    'QtQuick',
    'QtQuickWidgets',
    'QtQml',
    'QtQmlModels',
    'QtWebChannel',
    'QtPositioning',
    'QtOpenGL' # required by QtWebEngineCore
]
Qt_frameworks = [module + '.framework' for module in Qt_modules]

qt_plugin_dirs = [
    'iconengines',
    'imageformats',
    'platforms',
    'printsupport',
    'styles'
]
qt_plugin_files = [
    'libqsvgicon.dylib',
    'libqgif.dylib',
    'libqicns.dylib',
    'libqico.dylib',
    'libqjpeg.dylib',
    'libqmacjp2.dylib',
	'libqsvg.dylib',
    'libqtga.dylib',
    'libqwbmp.dylib',
    'libqwebp.dylib',
    'libqcocoa.dylib',
    'libcocoaprintersupport.dylib',
    'libqmacstyle.dylib'
]

# remove unused Qt frameworks libs (not in Qt_modules_frameworks)
for subdir, dirs, _files in os.walk('./Artisan.app/Contents/Frameworks/PyQt6/Qt6/lib'):
    for di in dirs:
        if di.startswith('Qt') and di.endswith('.framework') and di not in Qt_frameworks:
            file_path = os.path.join(subdir, di)
            print(f'rm -rf {file_path}')
            subprocess.check_call(f'rm -rf {file_path}',shell = True)

## remove unused plugins
for root, dirs, _ in os.walk('./Artisan.app/Contents/Frameworks/PyQt6/Qt6/plugins'):
    for d in dirs:
        if d not in qt_plugin_dirs:
            print(f'rm -rf {os.path.join(root,d)}')
            subprocess.check_call('rm -rf ' + os.path.join(root,d),shell = True)
        else:
            for subdir, _, files in os.walk(os.path.join(root,d)):
                for file in files:
                    if file not in qt_plugin_files:
                        file_path = os.path.join(subdir, file)
                        print(f'rm -rf {file_path}')
                        subprocess.check_call(f'rm -rf {file_path}',shell = True)

subprocess.check_call(r'rm -rf ./Artisan.app/Contents/Frameworks/PyQt6/Qt6/qml',shell = True)

print('*** Removing unused files ***')
for root, dirs, files in os.walk('.'):
    for file in files:
        if 'debug' in file:
#            print('Deleting', file)
            os.remove(os.path.join(root,file))
        elif file.startswith('test_'):
#            print('Deleting', file)
            os.remove(os.path.join(root,file))
        elif file.endswith('.pyc') and file != 'site.pyc' and os.path.isfile(os.path.join(root,file[:-3] + 'pyo')):
#            print('Deleting', file)
            os.remove(os.path.join(root,file))
        # remove also all .h .in .cpp .cc .html files
        elif file.endswith('.h') and file != 'pyconfig.h':
#            print('Deleting', file)
            os.remove(os.path.join(root,file))
        elif file.endswith('.in'):
#            print('Deleting', file)
            os.remove(os.path.join(root,file))
        elif file.endswith('.cpp'):
#            print('Deleting', file)
            os.remove(os.path.join(root,file))
        elif file.endswith('.cc'):
#            print('Deleting', file)
            os.remove(os.path.join(root,file))
# .afm files should not be removed as without matplotlib will fail on startup
#        elif file.endswith('.afm'):
#            print('Deleting', file)
#            os.remove(os.path.join(root,file))
    # remove test files
    for di in dirs:
        if 'tests' in di:
            for r,_d,f in os.walk(os.path.join(root,di)):
                for fl in f:
#                    print('Deleting', os.path.join(r,fl))
                    os.remove(os.path.join(r,fl))




dist_name = r'artisan-mac-' + VERSION + r'.dmg'
os.chdir('..')
os.system(r'rm ' + dist_name)
os.system(r'hdiutil create ' + dist_name + r' -volname "Artisan" -fs HFS+ -srcfolder "dist"')
