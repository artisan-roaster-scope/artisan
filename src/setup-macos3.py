# ABOUT
# setup.py script for Artisan macOS builds
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
"""This is a setup.py script

Usage:
    python3 setup-mac3.py py2app
"""

import os
import sys
import subprocess
from setuptools import setup

import plistlib

import artisanlib

from typing import List, Tuple


# current version of artisan
VERSION = artisanlib.__version__
LICENSE = 'GNU General Public License (GPL)'

QTDIR = os.environ['QT_PATH']

APP = ['artisan.py']

SUPPORTED_LANGUAGES = ['ar', 'da', 'de','el','en','es','fa','fi','fr','gd', 'he','hu','id','it','ja','ko','lv', 'nl','no','pl','pt_BR','pt','sk', 'sv','th','tr','uk','vi','zh_CN','zh_TW']


DATA_FILES:List[Tuple[str,List[str]]] = [
    ('../Resources', [
        r'artisanProfile.icns',
        r'artisanAlarms.icns',
        r'artisanPalettes.icns',
        r'artisanSettings.icns',
        r'artisanTheme.icns',
        r'artisanWheel.icns',
        r'includes/alarmclock.eot',
        r'includes/alarmclock.svg',
        r'includes/alarmclock.ttf',
        r'includes/alarmclock.woff',
        r'includes/artisan.tpl',
        r'includes/bigtext.js',
        r'includes/jquery-1.11.1.min.js',
        r'includes/android-chrome-192x192.png',
        r'includes/android-chrome-512x512.png',
        r'includes/apple-touch-icon.png',
        r'includes/browserconfig.xml',
        r'includes/favicon-16x16.png',
        r'includes/favicon-32x32.png',
        r'includes/favicon.ico',
        r'includes/mstile-150x150.png',
        r'includes/safari-pinned-tab.svg',
        r'includes/site.webmanifest',
        r'includes/sorttable.js',
        r'includes/report-template.htm',
        r'includes/roast-template.htm',
        r'includes/ranking-template.htm',
        r'includes/Humor-Sans.ttf',
        r'includes/WenQuanYiZenHei-01.ttf',
        r'includes/WenQuanYiZenHeiMonoMedium.ttf',
        r'includes/SourceHanSansCN-Regular.otf',
        r'includes/SourceHanSansHK-Regular.otf',
        r'includes/SourceHanSansJP-Regular.otf',
        r'includes/SourceHanSansKR-Regular.otf',
        r'includes/SourceHanSansTW-Regular.otf',
        r'includes/dijkstra.ttf',
        r'includes/ComicNeue-Regular.ttf',
        r'includes/xkcd-script.ttf',
        r'includes/Machines',
        r'includes/Themes',
        r'includes/Icons',
        r'includes/logging.yaml',
  ])]

# add Artisan translations to DATA_FILES
DATA_FILES.append(('../translations',
    [f'translations/{file}' for root,dirs,files in os.walk('translations') for file in files if (file.split('.')[1]) == 'qm']))

with open('Info.plist', 'r+b') as fp:
    plist = plistlib.load(fp)
    plist['CFBundleDisplayName'] = 'Artisan'
    plist['CFBundleGetInfoString'] = 'Artisan, Roast Logger'
    plist['CFBundleIdentifier'] = 'org.artisan-scope.artisan'
    plist['CFBundleShortVersionString'] = VERSION
    plist['CFBundleVersion'] = 'Artisan ' + VERSION
    try:
        plist['LSMinimumSystemVersion'] = os.environ['MACOSX_DEPLOYMENT_TARGET']
    except Exception: # pylint: disable=broad-except
        plist['LSMinimumSystemVersion'] = '12.0'
    plist['LSMultipleInstancesProhibited'] = 'false'
    plist['LSArchitecturePriority'] = ['arm64', 'x86_64']
    plist['NSHumanReadableCopyright'] = LICENSE
    plist['NSHighResolutionCapable'] = True
    fp.seek(0, os.SEEK_SET)
    fp.truncate()
    plistlib.dump(plist, fp)

OPTIONS = {
    'no_strip': True,
    'argv_emulation': False, # this would confuses GUI processing
    'semi_standalone': False,
    'site_packages': True,
    'packages': ['yoctopuce','openpyxl','numpy','scipy','certifi', 'kiwisolver', 'psutil',
        'matplotlib','PIL', 'lxml', 'snap7', 'google.protobuf', 'google._upb', 'keyring.backends'],
    'optimize':  2,
    'compressed': True,
    'iconfile': 'artisan.icns',
    'arch': 'x86_64', # 'universal2', 'x86_64',
    'matplotlib_backends': '-', # '-' for imported or explicit "Qt5Agg, PDF, PS, SVG"
    'includes': ['serial', 'charset_normalizer.md__mypyc'],
    'excludes' :  ['tkinter','curses',
                'test', # don't bundle the Python tests
                'pydoc_data', # python documentation tools
                'setuptools', # not needed
                'PyInstaller', # if pyinstaller is installed, whyever, py2app tries to include pyinstaller and fails on some missing pyside modules
                'PyQt5', # standard builds are now running on PyQt6. If PyQt5 is not excluded here it will be included in Resources/lib/python310.zip
                # 'sqlite3',
                ],
    'plist'    : plist}

# remove parts of the .dist_info content (removes 2MB of data)
#from py2app._pkg_meta import IGNORED_DISTINFO
#IGNORED_DISTINFO.add('METADATA')
##IGNORED_DISTINFO.add('LICENSE.txt')
##IGNORED_DISTINFO.add('LICENSE')
##IGNORED_DISTINFO.add('license_files')

setup(
    name='Artisan',
    version=VERSION,
    author='YOUcouldbeTOO',
    author_email='zaub.ERASE.org@yahoo.com',
    license=LICENSE,
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

subprocess.check_call(r'cp README.txt dist',shell = True)
subprocess.check_call(r'cp ../LICENSE dist/LICENSE.txt',shell = True)
subprocess.check_call(r'mkdir dist/Wheels',shell = True)
subprocess.check_call(r'mkdir dist/Wheels/Cupping',shell = True)
subprocess.check_call(r'mkdir dist/Wheels/Other',shell = True)
subprocess.check_call(r'mkdir dist/Wheels/Roasting',shell = True)
subprocess.check_call(r'cp Wheels/Cupping/* dist/Wheels/Cupping',shell = True)
subprocess.check_call(r'cp Wheels/Other/* dist/Wheels/Other',shell = True)
subprocess.check_call(r'cp Wheels/Roasting/* dist/Wheels/Roasting',shell = True)
os.chdir('./dist')

#try:
#    PYTHONPATH = os.environ['PYTHONPATH'] + r'/'
#except Exception: # pylint: disable=broad-except
#    PYTHONPATH = r'/Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/'
#

try:
    PYTHON_V = os.environ['PYTHON_V']
except Exception:
    PYTHON_V = '3.12'
python_version = f'python{PYTHON_V}'

# (independent) matplotlib (installed via pip) shared libs are not copied by py2app (both cp are needed!)
# UPDATE 9/2020: pip install of MPL v3.3.x does not come with a .dylibs directory any longer
#subprocess.check_call(r'mkdir Artisan.app/Contents/Resources/lib/python' + PYTHON_V + '/lib-dynload/matplotlib/.dylibs',shell = True)
#subprocess.check_call(r'cp -R ' + PYTHONPATH + r'site-packages/matplotlib/.dylibs/* Artisan.app/Contents/Resources/lib/python' + PYTHON_V + '/lib-dynload/#matplotlib/.dylibs',shell = True)
#subprocess.check_call(r'cp ' + PYTHONPATH + r'site-packages/matplotlib/.dylibs/* Artisan.app/Contents/Frameworks',shell = True)

# add localization stubs to make macOS translate the systems menu item and native dialogs
for lang in SUPPORTED_LANGUAGES:
    loc_dir = r'Artisan.app/Contents/Resources/' + lang + r'.lproj'
    subprocess.check_call(r'mkdir ' + loc_dir,shell = True)
    subprocess.check_call(r'touch ' + loc_dir + r'/Localizable.string',shell = True)



# copy brew installed libusb (note the slight name change of the dylib!)
    # cannot be run brew as root thus the following does not work
    # subprocess.check_call(r'cp $(brew list libusb | grep libusb-1.0.0.dylib) Artisan.app/Contents/Frameworks/libusb-1.0.dylib',shell = True)

# you need to do a
#
#  # brew install libusb
#
# to get libusb installed
#
# NOTE: brew does not install universal binaries. You need to fuse the libusb dynamic lib yourself from the Intel and arm brew binaries and
#  place it in the brew Cellar

brew_paths = ['/usr/local/Cellar', '/opt/homebrew/Cellar'] # path for Intel and arm brew installations
libusb_versions = ['1.0.27', '1.0.26' , '1.0.25']
success = False
for libusb_cand in [rf'{p}/libusb/{v}/lib/libusb-1.0.0.dylib' for v in libusb_versions for p in brew_paths]:
    print('libusb_cand',libusb_cand)
    try:
        subprocess.check_call(rf'cp {libusb_cand} Artisan.app/Contents/Frameworks/libusb-1.0.dylib',shell = True)
        success = True
        break
    except Exception: # pylint: disable=broad-except
        pass
if not success:
    print('ERROR: libusb not found')
    sys.exit(1)



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
    'QtWebEngine', # only on PyQt5, does not exists for PyQt6
    'QtWebEngineWidgets', # required by QtWebEngineCore
# the following are required by QtWebEngineWidgets and thus by QtWebEngine for the HTML2PDF export
    'QtQuick',
    'QtQuickWidgets',
    'QtQml',
    'QtQmlModels',
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


# remove unused Qt frameworks libs (not in Qt_modules_frameworks)
for subdir, dirs, _files in os.walk('./Artisan.app/Contents/Frameworks'):
    for di in dirs:
        if di.startswith('Qt') and di.endswith('.framework') and di not in Qt_frameworks:
            file_path = os.path.join(subdir, di)
            print(f'rm -rf {file_path}')
            subprocess.check_call(f'rm -rf {file_path}',shell = True)


# remove duplicate Qt plugins folder
# (py2app v0.26.1 copes non-relocated PlugIns to the toplevel)
try:
    subprocess.check_call('rm -rf ./Artisan.app/Contents/plugins',shell = True)
except Exception: # pylint: disable=broad-except
    pass


rootdir = f'./Artisan.app/Contents/Resources/lib/{python_version}'

if os.path.isdir(f'{rootdir}/PyQt6'):
    # if PyQt6 exists we remove PyQt5 completely
    try:
        subprocess.check_call(f'rm -rf {rootdir}/PyQt5',shell = True)
    except Exception: # pylint: disable=broad-except
        pass
# remove Qt artefacts
for qt_dir in [
        'PyQt5/Qt',
        'PyQt5/bindings',
        'PyQt5/uic',
#        'PyQt5/Qt5/translations', # qt translations are kept and loaded from their standard dir
        'PyQt5/Qt5/qml',
        'PyQt5/Qt5/qsci',
#        'PyQt5/Qt5/lib', # comment for the non-Framework variant
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
for pyqt_dir in ['PyQt5', 'PyQt6']:
    # remove unused PyQt libs (not in Qt_modules)
    for subdir, _dirs, files in os.walk(f'{rootdir}/{pyqt_dir}'):
        for file in files:
            if file.endswith('.pyi'):
                file_path = os.path.join(subdir, file)
                subprocess.check_call(f'rm -rf {file_path}',shell = True)
            if file.endswith(('.abi3.so','.pyi')) and file.split('.')[0] not in Qt_modules:
                file_path = os.path.join(subdir, file)
                subprocess.check_call(f'rm -rf {file_path}',shell = True)

# uncomment for non-Framework variant
# remove unused Qt frameworks libs (not in Qt_modules_frameworks)
for qt_dir in ['PyQt5/Qt5/lib', 'PyQt6/Qt6/lib']:
    qt = f'{rootdir}/{qt_dir}'
    for _root, dirs, _ in os.walk(qt):
        for di in dirs:
            if di.startswith('Qt') and di.endswith('.framework') and di not in Qt_frameworks:
                file_path = os.path.join(qt, di)
                subprocess.check_call(f'rm -rf {file_path}',shell = True)
    # remove all WebEngine locales, but keep en-US.pak
    file_path = os.path.join(qt, 'QtWebEngineCore.framework/Resources/qtwebengine_locales')
    try:
        subprocess.check_call(f"find {file_path} ! -name 'en-US.pak' -type f -exec rm -f {{}} + 2>/dev/null",shell = True)
    except Exception: # pylint: disable=broad-except
        pass


# we create an empty directory to get rid of the warning on creating PDF reports:
##WARNING: Path override failed for key base::DIR_APP_DICTIONARIES and path
##'..Artisan.app/Contents/MacOS/qtwebengine_dictionaries'
subprocess.check_call('mkdir ./Artisan.app/Contents/MacOS/qtwebengine_dictionaries', shell = True)


# remove unused plugins
for qt_dir in ['PyQt5/Qt5/plugins', 'PyQt6/Qt6/plugins']:
    for root, dirs, _ in os.walk(f'{rootdir}/{qt_dir}'):
        for d in dirs:
            if d not in qt_plugin_dirs:
                subprocess.check_call('rm -rf ' + os.path.join(root,d),shell = True)
            else:
                for subdir, _, files in os.walk(os.path.join(root,d)):
                    for file in files:
                        if file not in qt_plugin_files:
                            file_path = os.path.join(subdir, file)
                            subprocess.check_call(f'rm -rf {file_path}',shell = True)
# comment for non-Framework variant
#    # move plugins directory from Resources/lib/python3.x/PyQtX/QtX/plugins to the root of the app
#    try:
#        shutil.move(f"{rootdir}/{qt_dir}", "./Artisan.app/Contents/PlugIns")
#    except Exception: # pylint: disable=broad-except
#        pass

qt_trans_prefix_keep = {
    'qtbase',
    'qt'
}
qt_trans_prefix_delete = {
    'qt_help'
}

# remove unused translations of unused Qt modules
for qt_dir in ['PyQt5/Qt5/translations', 'PyQt6/Qt6/translations']:
    qt = f'{rootdir}/{qt_dir}'
    for root, _, files in os.walk(qt):
        for file in files:
            if (any(file.startswith(f'{x}_') for x in qt_trans_prefix_delete) or
                    not (any(file.startswith(f'{x}_') for x in qt_trans_prefix_keep) and any(file.endswith(f'_{x}.qm') for x in SUPPORTED_LANGUAGES))):
                file_path = os.path.join(root, file)
                subprocess.check_call(f'rm -rf {file_path}',shell = True)

print('*** Removing duplicate mpl_data folder and mpl_data/sample_data subfolder ***')

# remove duplicate mpl_data folder
try:
    subprocess.check_call('rm -rf ./Artisan.app/Contents/Resources/mpl-data',shell = True)
except Exception: # pylint: disable=broad-except
    pass
try:
    subprocess.check_call(f'rm -rf ./Artisan.app/Contents/Resources/lib/{python_version}/matplotlib/mpl-data/sample_data',shell = True)
except Exception: # pylint: disable=broad-except
    pass

print('*** Removing debug and test files and folders  ***')

for root, dirs, files in os.walk('.'):
    for file in files:
        # ruff: noqa: SIM114
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
        elif file.endswith('.c'):
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

print('*** Removing parts of scipy ***')

# remove unused parts of scipy
for sdir in [
        'scipy/io',
        'scipy/misc',
        'scipy/cluster',
        'scipy/odr',
    ]:
    try:
        subprocess.check_call(f'rm -rf ./Artisan.app/Contents/Resources/lib/{python_version}/{sdir}',shell = True)
    except Exception: # pylint: disable=broad-except
        pass

# remove unused language support from babel

print('*** Removing unused language support from babel ***')

for root, _, files in os.walk(f'./Artisan.app/Contents/Resources/lib/{python_version}/babel/locale-data'):
    for file in files:
        if file.endswith('.dat') and (('_' not in file and file.split('.')[0] not in SUPPORTED_LANGUAGES) or
                ('_' in file and file.split('.')[0] not in SUPPORTED_LANGUAGES)):
#            print('Deleting', file)
            os.remove(os.path.join(root,file))


print('*** Removing yoctopuce driver libs not for this platforms ***')
try:
    subprocess.check_call(f'rm -f ./Artisan.app/Contents/Resources/lib/{python_version}/yoctopuce/cdll/*.so',shell = True)
    subprocess.check_call(f'rm -f ./Artisan.app/Contents/Resources/lib/{python_version}/yoctopuce/cdll/*.dll',shell = True)
except Exception: # pylint: disable=broad-except
    pass

####

os.chdir('..')
subprocess.check_call(r'rm -f artisan-mac-' + VERSION + r'.dmg',shell = True)
subprocess.check_call(r'hdiutil create artisan-mac-' + VERSION + r'.dmg -volname "artisan" -fs HFS+ -srcfolder "dist"',shell = True)
# otool -L dist/Artisan.app/Contents/MacOS/Artisan

# brew install create-dmg
#subprocess.check_call(r'create-dmg \
#  --volname "Artisan" \
#  --volicon "Hello World.icns" \
#  --window-pos 200 120 \
#  --window-size 600 300 \
#  --icon-size 100 \
#  --icon "Hello World.app" 175 120 \
#  --hide-extension "Hello World.app" \
#  --app-drop-link 425 120 \
#  "dist/Hello World.dmg" \
#  "dist/dmg/"
