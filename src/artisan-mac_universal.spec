### -*- mode: python ; coding: utf-8 -*-
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
# Dave Baxter, Marko Luther 2025
"""

Usage:
    pyinstaller artisan-mac.spec
"""

import os
import pathlib
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
    PYTHON_V = os.environ["PYTHON_V"]
except Exception:
    PYTHON_V = '3.14'
python_version = f'python{PYTHON_V}'

try:
    QTDIR = os.environ['QT_PATH'] + r'/'
except Exception:
    from os.path import expanduser
    HOME = expanduser('~')
    QTDIR = HOME + r'/Qt/6.5.3/macos/'

SUPPORTED_LANGUAGES = ['ar', 'cs', 'da', 'de','el','en','es','fa','fi','fr','gd', 'he','hu','id','it','ja','ko','lv', 'nl','no','pl','pt_BR','pt','sk', 'sv','th','tr','uk','vi','zh_CN','zh_TW']

DATA_FILES = [
        (r'Assets.car', '.'),
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
        (r'includes/roboto-300.woff2', '.'),
        (r'includes/roboto-600.woff2', '.'),
        (r'includes/roboto-regular.woff2', '.'),
        (r'includes/artisan.tpl', '.'),
        (r'includes/scale_widget.tpl', '.'),
        (r'includes/fitty_patched.js', '.'),
        (r'includes/bigtext.js', '.'),
        (r'includes/fitty_patched.js', '.'),
        (r'includes/jquery-1.11.1.min.js', '.'),
        (r'includes/android-chrome-192x192.png', '.'),
        (r'includes/android-chrome-512x512.png', '.'),
        (r'includes/apple-touch-icon.png', '.'),
        (r'includes/browserconfig.xml', '.'),
        (r'includes/favicon-16x16.png', '.'),
        (r'includes/favicon-32x32.png', '.'),
        (r'includes/favicon-96x96.png', '.'),
        (r'includes/favicon.ico', '.'),
        (r'includes/favicon.svg', '.'),
        (r'includes/mstile-70x70.png', '.'),
        (r'includes/mstile-144x144.png', '.'),
        (r'includes/mstile-150x150.png', '.'),
        (r'includes/mstile-310x310.png', '.'),
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
# add phidgets libs
BINARIES.extend([(os.path.join(get_package_paths('Phidget22')[1], '.libs/libphidget22.dylib'), 'Phidget22/.libs' )])

# brew installed libusb is added automatically by pyinstaller

a = Analysis(['artisan.py'],
             binaries=BINARIES,
             datas=DATA_FILES,
             hiddenimports=['babel.numbers'], # should not be needed as it got fixed in pyinstaller 6.11
             hooksconfig={
                'matplotlib': {
                'backends': ['QtAgg', 'svg', 'pdf'] # 'auto',  # auto-detect; the default behavior (QtAgg
                },
             },
             hookspath=[],
             runtime_hooks=['./pyinstaller_hooks/rthooks/pyi_rth_mplconfig.py'], # overwrites default MPL runtime hook which keeps loading font cache from (new) temp directory
             additional_hooks_dir=[],
             excludes= ['tkinter', 'mypy'],
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
            options=[], # runtime python options
            exclude_binaries=not onefile,
            name='Artisan',
            debug=False,
            bootloader_ignore_signals=False,
            strip=True, # not recommended for Windows
            upx=False,  # binary compressor: https://github.com/upx/upx # brew install upx # UPX is currently used only on Windows
            upx_exclude=[],
            runtime_tmpdir=None,
            console=False,
            disable_windowed_traceback=False,
            argv_emulation=False, # False for GUI apps
            target_arch='universal2', # 'arm64', 'x86_64', 'universal2'
            codesign_identity='6M3Z6W45L4', #None,
            entitlements_file='Artisan.entitlements', #None
            )

try:
    minimumSystemVersion = os.environ['MACOSX_DEPLOYMENT_TARGET']
except Exception: # pylint: disable=broad-except
    minimumSystemVersion = '13.0' # needs the old-style numpy/scipy libs!! Qt 6.10 requires >= 13.0

plist = {}
with open('Info.plist', 'rb') as infile:
    plist = plistlib.load(infile)
    plist.update({ 'CFBundleDisplayName': 'Artisan',
                    'CFBundleGetInfoString': 'Artisan, Roast Logger',
                    'CFBundleIdentifier': 'org.artisan-scope.artisan',
                    'CFBundleShortVersionString': VERSION,
                    'CFBundleVersion': 'Artisan ' + VERSION,
                    'LSMinimumSystemVersion': minimumSystemVersion,
                    'LSMultipleInstancesProhibited': False,
                    'LSArchitecturePriority': ['arm64'],
                    'NSHumanReadableCopyright': LICENSE,
                    'NSHighResolutionCapable': True,
#                    'UIDesignRequiresCompatibility': True, # run in compatibility mode, keeping the existing look and metrics of pre v26 macOS releases
                    'CFBundleIconName': 'artisan-liquid-glass'
                })

bundle_obj = exe

if not onefile:
    coll = COLLECT(
            exe,
            a.binaries,
            a.zipfiles,
            a.datas,
            strip=True, # not recommended for Windows
            upx=False,  # brew install upx # UPX is currently used only on Windows
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

subprocess.check_call(r'mv dist/Artisan.app/Contents/Resources/translations dist/Artisan.app/Contents/',shell = True)
subprocess.check_call(r'rm -rf dist/Test/_internal/babel/*',shell = True) # unclear: without this line, the next fails
subprocess.check_call(r'rm -rf dist/Test',shell = True)
subprocess.check_call(r'cp README.txt dist',shell = True)
subprocess.check_call(r'cp ../LICENSE dist/LICENSE.txt',shell = True)
subprocess.check_call(r'mkdir -p dist/Wheels',shell = True)
subprocess.check_call(r'mkdir -p dist/Wheels/Cupping',shell = True)
subprocess.check_call(r'mkdir -p dist/Wheels/Other',shell = True)
subprocess.check_call(r'mkdir -p dist/Wheels/Roasting',shell = True)
subprocess.check_call(r'cp Wheels/Cupping/* dist/Wheels/Cupping',shell = True)
subprocess.check_call(r'cp Wheels/Other/* dist/Wheels/Other',shell = True)
subprocess.check_call(r'cp Wheels/Roasting/* dist/Wheels/Roasting',shell = True)
try:
    subprocess.check_call('rm -rf dist/Artisan.app/Contents/Resources/matplotlib/mpl-data/sample_data',shell = True)
except Exception: # pylint: disable=broad-except
    pass

os.chdir('./dist')

# add localization stubs to make macOS translate the systems menu item and native dialogs
for lang in SUPPORTED_LANGUAGES:
    loc_dir = r'Artisan.app/Contents/Resources/' + lang + r'.lproj'
    subprocess.check_call(r'mkdir ' + loc_dir,shell = True)
    subprocess.check_call(r'touch ' + loc_dir + r'/Localizable.string',shell = True)



#######
## remove unused and duplicate parts of packages

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
#    'QtBluetooth', # replaced by bleak
#    'QtConcurrent', # not on PyQt6.2, but PyQt6.4 and PyQt5.x
# needed for QtWebEngine HTML2PDF export:
    'QtWebEngineCore',
#    'QtWebEngine', # only on PyQt5, does not exists for PyQt6
    'QtWebEngineWidgets', # required by QtWebEngineCore
# the following are required by QtWebEngineWidgets and thus by QtWebEngine for the HTML2PDF export
    'QtQuick',
    'QtQuickWidgets',
    'QtQml',
    'QtQmlModels',
    'QtQmlMeta',
    'QtQmlWorkerScript',
    'QtWebChannel',
    'QtPositioning',
    'QtOpenGL'
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
    'libqsvgicon.dylib', # needed to render MPL toolbar as SVG icons (fallback is PNG; built-in support)
#    'libqgif.dylib',
#    'libqicns.dylib',
#    'libqico.dylib',
    'libqjpeg.dylib',
#    'libqmacjp2.dylib',
#    'libqpdf.dylib',
	'libqsvg.dylib',
#    'libqtga.dylib',
#   'libqtiff.dylib',
#    'libqwbmp.dylib',
#    'libqwebp.dylib',
    'libqcocoa.dylib',
    'libcocoaprintersupport.dylib',
    'libqmacstyle.dylib'
]


## remove unused Qt frameworks libs (not in Qt_modules_frameworks)
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



rootdir = f'./Artisan.app/Contents/Resources'

# remove Qt artefacts
for qt_dir in [
        'PyQt6/Qt',
        'PyQt6/bindings',
        'PyQt6/lupdate',
        'PyQt6/uic',
#        'PyQt6/Qt6/translations', # qt translations are kept and loaded from their standard dir
        'PyQt6/Qt6/qml',
        'PyQt6/Qt6/qsci',
#        'PyQt6/Qt6/lib', # comment for the non-Framework variant
    ]:
    try:
        subprocess.check_call(f'rm -rf {rootdir}/{qt_dir}',shell = True)
    except Exception: # pylint: disable=broad-except
        pass

qt_trans_prefix_keep = {
    'qtbase',
    'qt'
}
qt_trans_prefix_delete = {
    'qt_help'
}

# remove unused translations of unused Qt modules
for qt_dir in ['PyQt6/Qt6/translations']:
    qt = f'{rootdir}/{qt_dir}'
    for root, _, files in os.walk(qt):
        for file in files:
            if (any(file.startswith(f'{x}_') for x in qt_trans_prefix_delete) or
                    not (any(file.startswith(f'{x}_') for x in qt_trans_prefix_keep) and any(file.endswith(f'_{x}.qm') for x in SUPPORTED_LANGUAGES))):
                file_path = os.path.join(root, file)
                subprocess.check_call(f'rm -rf {file_path}',shell = True)


print('*** Removing QtWebEngine translations ***')

for qtwebengine_dir in ['PyQt6/Qt6/lib/QtWebEngineCore.framework/Versions/A/Resources/qtwebengine_locales/']:
    qtwebengine = f'{rootdir}/{qtwebengine_dir}'
    for root, _, files in os.walk(qtwebengine):
        for file in files:
            if not file == 'en-US.pak':
                file_path = os.path.join(root, file)
                print(f'rm -rf {file_path}')
                subprocess.check_call(f'rm {file_path}',shell = True)

print('*** Removing QtWebEngine remote debug lib ***')

try:
    subprocess.check_call(f'rm -rf {rootdir}/PyQt6/Qt6/lib/QtWebEngineCore.framework/Versions/A/Resources/qtwebengine_devtools_resources.pak',shell = True)
except Exception: # pylint: disable=broad-except
    pass


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
                    print('Deleting', os.path.join(r,fl))
                    if not fl.endswith(('.py', '.pyc')):
                        os.remove(os.path.join(r,fl))


# remove unused language support from babel

print('*** Removing unused language support from babel ***')

for root, _, files in os.walk(f'./Artisan.app/Contents/Resources/babel/locale-data'):
    for file in files:
        if (file.endswith('.dat') and
            file != 'root.dat' and not (file.startswith('zh') and file.endswith('.dat')) and
            (('_' not in file and file.split('.')[0] not in SUPPORTED_LANGUAGES) or
                ('_' in file and file.split('.')[0] not in SUPPORTED_LANGUAGES))):
#            print('Deleting', file)
            os.remove(os.path.join(root,file))


print('*** Removing Phidget driver libs not for this platforms ***')
try:
    subprocess.check_call(f'rm -f ./Artisan.app/Contents/Frameworks/phidget22.dll',shell = True)
except Exception: # pylint: disable=broad-except
    pass


print('*** Removing mypy completely ***')
try:
    subprocess.check_call(f'rm -rf ./Artisan.app/Contents/Frameworks/mypy',shell = True)
except Exception: # pylint: disable=broad-except
    pass


print('*** Removing broken symbolic links ***')
for subdir, _dirs, files in os.walk('.', followlinks=False):
    for file in files:
        file_path = pathlib.Path(os.path.join(subdir, file))
        if file_path.is_symlink() and not file_path.exists():
            print(f"unlink dangling symlink at {file_path}")
            subprocess.check_call(f'unlink {file_path}',shell = True)


####


dist_name = r'artisan-mac-' + VERSION + r'.dmg'
os.chdir('..')
os.system(r'rm ' + dist_name)
os.system(r'hdiutil create ' + dist_name + r' -volname "Artisan" -fs HFS+ -srcfolder "dist"')
