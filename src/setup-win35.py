"""
This is a set up script for py2exe

USAGE: python setup-win py2exe

"""

from distutils.core import setup
import matplotlib as mpl
import py2exe

# Before adding these imports Artisan could not read PyQt5.QtCore.pyd'
import sip
import PyQt5
# Importing numpy makes for a smaller Artisan.exe and I had thought it was necessary to run on the new Dell.
# However, after straightening out the mkl_ dlls it does not appear to be required.  For now I'm leaving
# it in to keep the exe smaller.
import numpy

import os


ARTISAN_SRC = r'C:\Users\luther\Desktop\src'
PYTHON35 = r'C:\Program Files\Python35'
NAME = 'artisan'

##
PYTHON_PACKAGES = PYTHON35 + r'\Lib\site-packages'
PYQT_QT = PYTHON_PACKAGES + r'\PyQt5\Qt'
PYQT_QT_TRANSLATIONS = PYQT_QT + '\\translations\\'
YOCTO_BIN = PYTHON_PACKAGES + r'\yoctopuce\cdll'
NUMPY_BIN = PYTHON_PACKAGES + '\\numpy\\core\\'
SNAP7_BIN = r'C:\Windows'


# Remove the build folder, a bit slower but ensures that build contains the latest
import shutil
shutil.rmtree("build", ignore_errors=True)
shutil.rmtree("dist", ignore_errors=True)


INCLUDES = [
            "sip",
            "serial",
            "scipy.special._ufuncs_cxx",
            "scipy.sparse.csgraph._validation",
            "scipy.integrate",
            "scipy.interpolate",
#            "urlparse",
            ]

EXCLUDES = ['six.moves.urllib.parse',
            '_tkagg',
            '_ps',
            '_fltkagg',
            'Tkinter',
            'Tkconstants',
            '_cairo',
            '_gtk',
            'gtkcairo',
            'pydoc',
            'doctest',
            'pdb',
            'pyreadline',
            'optparse',
            'sqlite3',
            'bsddb',
            'curses',
            'tcl',
            '_wxagg',
            '_gtagg',
            '_cocoaagg',
            '_wx',
            # the following two lines avoid a infinite loop in py2exe 0.9.2.2
            'six.moves',
            'six.moves.urllib',
            ]

# current version of Artisan

import artisanlib

VERSION = artisanlib.__version__
LICENSE = 'GNU General Public License (GPL)'

cwd = os.getcwd()

DATAFILES = mpl.get_py2exe_datafiles()
DATAFILES = DATAFILES + \
    [('plugins\\imageformats', [
            PYQT_QT + r'\plugins\imageformats\qsvg.dll',
            PYQT_QT + r'\plugins\imageformats\qgif.dll',
            PYQT_QT + r'\plugins\imageformats\qtiff.dll',
            PYQT_QT + r'\plugins\imageformats\qjpeg.dll',
            ]),
      ('plugins\\iconengines', [
            PYQT_QT + r'\plugins\iconengines\qsvgicon.dll',
            ]),
      ('plugins\\platforms', [
            PYQT_QT + r'\plugins\platforms\qwindows.dll',
            ]),
      ('plugins\\printsupport', [
            PYQT_QT + r'\plugins\printsupport\windowsprintersupport.dll',
            ]),
    ]


setup(
    name ="Artisan",
    version=VERSION,
    author='YOUcouldbeTOO',
    author_email='zaub.ERASE.org@yahoo.com',
    license=LICENSE,
    windows=[{"script" : cwd + "\\artisan.py",
            "icon_resources": [(0, cwd + "\\artisan.ico")]
            }],
    data_files = DATAFILES,
    zipfile = "lib\library.zip",
    options={"py2exe" :{
                       "packages": ['matplotlib','pytz'],
                       "compressed": False, # faster
                       "unbuffered": True, 
#                       'optimize':  2, # breaks py2exe on py3
#                       "bundle_files": 2, # default bundle_files: 3 breaks WebLCDs on Windows
      # bundle_files 1 or 2 breaks py2exe on py3 in gevent._semahores
                        "dll_excludes":[
                            'MSVCP90.dll','tcl84.dll','tk84.dll','libgdk-win32-2.0-0.dll',
                            'libgdk_pixbuf-2.0-0.dll','libgobject-2.0-0.dll',
                            'MSVCR90.dll','MSVCN90.dll','mwsock.dll','powrprof.dll'],
                        "includes" : INCLUDES,
                        "excludes" : EXCLUDES
                        }
            }
    )

os.system('copy README.txt dist')
os.system('copy LICENSE.txt dist')
#Appears to be not needed, not used: os.system('copy qt-win.conf dist\\qt.conf')
os.system(r'mkdir dist\Wheels')
os.system(r'mkdir dist\Wheels\Cupping')
os.system(r'mkdir dist\Wheels\Other')
os.system(r'mkdir dist\Wheels\Roasting')
os.system(r'copy Wheels\Cupping\* dist\Wheels\\Cupping')
os.system(r'copy Wheels\Other\* dist\Wheels\Other')
os.system(r'copy Wheels\Roasting\* dist\Wheels\Roasting')
os.system(r'mkdir dist\translations')
os.system(r'copy translations\*.qm dist\translations')
for e in [
    'qt_ar.qm',
    'qt_de.qm',
    'qt_es.qm',
    'qt_fi.qm',
    'qt_fr.qm',
    'qt_he.qm',
    'qt_hu.qm',
    'qt_it.qm',
    'qt_ja.qm',
    'qt_ko.qm',
    'qt_pt.qm',
    'qt_pl.qm',
    'qt_ru.qm',
    'qt_ru.qm',
    'qt_sv.qm',
    'qt_zh_CN.qm',
    'qt_zh_TW.qm',
    ]:
  os.system('copy "' + PYQT_QT_TRANSLATIONS + e + r'" dist\\translations') 

os.system('rmdir /q /s dist\\mpl-data\\sample_data')
# YOCTO HACK BEGIN: manually copy over the dlls
#Appears to be not needed, already created: os.system('mkdir dist\\lib')
os.system('copy "' + YOCTO_BIN + r'\yapi.dll" dist\lib')
os.system('copy "' + YOCTO_BIN + r'\yapi64.dll" dist\lib')
# YOCTO HACK END

# copy Snap7 lib
os.system('copy "' + SNAP7_BIN + r'\snap7.dll" dist\lib')


for e in [
    'artisan.png',
    'artisanAlarms.ico',
    'artisanProfile.ico',
    'artisanPalettes.ico',
    'artisanSettings.ico',
    'artisanWheel.ico',
    'artisanTheme.ico',
    ]:
  os.system('copy ' + e + ' dist')

for e in [
    'Humor-Sans.ttf',
    'alarmclock.eot',
    'alarmclock.svg',
    'alarmclock.ttf',
    'alarmclock.woff',
    'artisan.tpl',
    'bigtext.js',
    'sorttable.js',
    'report-template.htm',
    'roast-template.htm',
    'ranking-template.htm',
    'jquery-1.11.1.min.js',
    ]:
  os.system('copy includes\\' + e + ' dist')

os.system(r'mkdir dist\Machines')
os.system(r'xcopy includes\Machines dist\Machines /y /S')
os.system(r'mkdir dist\Themes')
os.system(r'xcopy includes\Themes dist\Themes /y /S')
# assumes the Microsoft Visual C++ 2015 Redistributable Package (x64), vc_redist.x64.exe, is located above the source directory
os.system(r'copy ..\vc_redist.x64.exe ' + 'dist\\')

# mkl hack for py3.4 and py3.5 because numpy and scipy grabbed from http://www.lfd.uci.edu/~gohlke/pythonlibs/ were built with mkl 
#  there are lots of mkl_ dlls that get installed in dist\lib that appear to be uneeded, and some of them need
#  to be in dist.  So we just delete them all and copy back just the ones needed to the required folders.
os.system('del dist\\lib\\mkl_*.dll')
for e in [
    'libimalloc.dll',
    'libiomp5md.dll',
    'mkl_avx.dll',
    'mkl_avx2.dll',
    'mkl_core.dll',
    'mkl_intel_thread.dll',
#    'mkl_msg.dll', # maybe not needed??   it is not in numpy.core
#    'mkl_p4.dll', # not part of current numpy anymore
    'mkl_rt.dll',
    ]:
  os.system('copy "' + NUMPY_BIN + e + '" dist/lib')
#mkl hack end 
