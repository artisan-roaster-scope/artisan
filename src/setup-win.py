"""
This is a set up script for py2exe

USAGE: python setup-win py2exe

"""

from distutils.core import setup
import matplotlib as mpl
import py2exe

import numpy
import os
import sys

# add any numpy directory containing a dll file to sys.path
def numpy_dll_paths_fix():
    paths = set()
    np_path = numpy.__path__[0]
    for dirpath, _, filenames in os.walk(np_path):
        for item in filenames:
            if item.endswith('.dll'):
                paths.add(dirpath)
    if paths:
        sys.path.append(*list(paths))

numpy_dll_paths_fix()


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
            ]

EXCLUDES = ['gevent._socket3',
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
            '_wx']


# current version of Artisan

import artisanlib

VERSION = artisanlib.__version__
LICENSE = 'GNU General Public License (GPL)'

cwd = os.getcwd()

DATAFILES = mpl.get_py2exe_datafiles()
DATAFILES = DATAFILES + \
    [('plugins\imageformats', [
            'c:\Python27\Lib\site-packages\PyQt4\plugins\imageformats\qsvg4.dll',
            'c:\Python27\Lib\site-packages\PyQt4\plugins\imageformats\qgif4.dll',
            'c:\Python27\Lib\site-packages\PyQt4\plugins\imageformats\qtiff4.dll',
            'c:\Python27\Lib\site-packages\PyQt4\plugins\imageformats\qjpeg4.dll',
            ]),
      ('plugins\iconengines', [
            'c:\Python27\Lib\site-packages\PyQt4\plugins\iconengines\qsvgicon4.dll',
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
                        'optimize':  2,
                        "bundle_files": 2, # default bundle_files: 3 breaks WebLCDs on Windows
                        "dll_excludes":[
                            'MSVCP90.dll','tcl84.dll','tk84.dll','libgdk-win32-2.0-0.dll',
                            'libgdk_pixbuf-2.0-0.dll','libgobject-2.0-0.dll',
                            'MSVCR90.dll','MSVCN90.dll','mwsock.dll','powrprof.dll'],
                        "includes" : INCLUDES,
                        "excludes" : EXCLUDES}
            }
    )

os.system(r'copy README.txt dist')
os.system(r'copy LICENSE.txt dist')
os.system(r'copy qt-win.conf dist\\qt.conf')
os.system(r'mkdir dist\\Wheels')
os.system(r'mkdir dist\\Wheels\\Cupping')
os.system(r'mkdir dist\\Wheels\\Other')
os.system(r'mkdir dist\\Wheels\\Roasting')
os.system(r'copy Wheels\\Cupping\\* dist\\Wheels\\Cupping')
os.system(r'copy Wheels\\Other\\* dist\\Wheels\\Other')
os.system(r'copy Wheels\\Roasting\\* dist\\Wheels\\Roasting')
os.system(r'mkdir dist\\translations')
os.system(r'copy translations\\*.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_ar.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_de.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_es.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_fr.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_he.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_hu.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_ja.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_ko.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_ru.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_pl.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_pt.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_ru.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_sv.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_zh_CN.qm dist\\translations')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\PyQt4\\translations\\qt_zh_TW.qm dist\\translations')
os.system(r'rmdir /q /s dist\\mpl-data\\sample_data')
# YOCTO HACK BEGIN: manually copy over the dlls
os.system(r'mkdir dist\\lib')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\yoctopuce\\cdll\\yapi.dll dist\\lib')
os.system(r'copy c:\\Python27\\Lib\\site-packages\\yoctopuce\\cdll\\yapi64.dll dist\\lib')
# YOCTO HACK END
os.system(r'copy artisan.png dist')
os.system(r'copy artisanAlarms.ico dist')
os.system(r'copy artisanProfile.ico dist')
os.system(r'copy artisanPalettes.ico dist')
os.system(r'copy artisanSettings.ico dist')
os.system(r'copy artisanTheme.ico dist')
os.system(r'copy artisanWheel.ico dist')
os.system(r'copy includes\\Humor-Sans.ttf dist')
os.system(r'copy includes\\alarmclock.eot dist')
os.system(r'copy includes\\alarmclock.svg dist')
os.system(r'copy includes\\alarmclock.ttf dist')
os.system(r'copy includes\\alarmclock.woff dist')
os.system(r'copy includes\\artisan.tpl dist')
os.system(r'copy includes\\bigtext.js dist')
os.system(r'copy includes\\sorttable.js dist')
os.system(r'copy includes\\report-template.htm dist')
os.system(r'copy includes\\roast-template.htm dist')
os.system(r'copy includes\\ranking-template.htm dist')
os.system(r'copy includes\\jquery-1.11.1.min.js dist')
os.system(r'mkdir dist\\Machines')
os.system(r'xcopy includes\\Machines dist\\Machines /y /S')
os.system(r'mkdir dist\\Themes')
os.system(r'xcopy includes\\Themes dist\\Themes /y /S')
os.system(r'copy ..\\vcredist_x86.exe dist')
