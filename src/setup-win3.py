"""
This is a set up script for py2exe

USAGE: python setup-win py2exe

"""

from distutils.core import setup
import matplotlib as mpl
import py2exe

import os

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
            'c:\\Python34\\Lib\\site-packages\\PyQt5\\plugins\\imageformats\\qsvg.dll',
            'c:\\Python34\\Lib\\site-packages\\PyQt5\\plugins\\imageformats\\qgif.dll',
            'c:\\Python34\\Lib\\site-packages\\PyQt5\\plugins\\imageformats\\qtiff.dll',
            'c:\\Python34\\Lib\\site-packages\\PyQt5\\plugins\\imageformats\\qjpeg.dll',
            ]),
      ('plugins\\iconengines', [
            'c:\\Python34\\Lib\\site-packages\\PyQt5\\plugins\\iconengines\\qsvgicon.dll',
            ]),
      ('plugins\\platforms', [
            'c:\\Python34\\Lib\\site-packages\\PyQt5\\plugins\\platforms\\qwindows.dll',
            ]),
      ('plugins\\printsupport', [
            'c:\\Python34\\Lib\\site-packages\\PyQt5\\plugins\\printsupport\\windowsprintersupport.dll',
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
#                        'optimize':  2, # breaks py2exe on py3
#                        "bundle_files": 2, # default bundle_files: 3 breaks WebLCDs on Windows
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

os.system('mkdir dist')
os.system('mkdir build')
os.system('copy README.txt dist')
os.system('copy ..\\LICENSE dist\\LICENSE.txt')
os.system('copy qt-win.conf dist\\qt.conf')
os.system('mkdir dist\\Wheels')
os.system('mkdir dist\\Wheels\\Cupping')
os.system('mkdir dist\\Wheels\\Other')
os.system('mkdir dist\\Wheels\\Roasting')
os.system('copy Wheels\\Cupping\\* dist\\Wheels\\Cupping')
os.system('copy Wheels\\Other\\* dist\\Wheels\\Other')
os.system('copy Wheels\\Roasting\\* dist\\Wheels\\Roasting')
os.system('mkdir dist\\translations')
os.system('copy translations\\*.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_ar.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_de.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_es.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_fi.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_fr.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_he.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_hu.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_it.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_ja.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_ko.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_pt.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_pl.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_ru.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_ru.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_sv.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_zh_CN.qm dist\\translations')
os.system('copy c:\\Python34\\Lib\\site-packages\\PyQt5\\translations\\qt_zh_TW.qm dist\\translations')
os.system('rmdir /q /s dist\\mpl-data\\sample_data')
# YOCTO HACK BEGIN: manually copy over the dlls
os.system('mkdir dist\\lib')
os.system('copy c:\\Python34\\Lib\\site-packages\\yoctopuce\\cdll\\yapi.dll dist\\lib')
os.system('copy c:\\Python34\\Lib\\site-packages\\yoctopuce\\cdll\\yapi64.dll dist\\lib')
# YOCTO HACK END
os.system('copy artisan.png dist')
os.system('copy artisanAlarms.ico dist')
os.system('copy artisanProfile.ico dist')
os.system('copy artisanPalettes.ico dist')
os.system('copy artisanSettings.ico dist')
os.system('copy artisanTheme.ico dist')
os.system('copy artisanWheel.ico dist')
os.system('copy includes\\Humor-Sans.ttf dist')
os.system('copy includes\\alarmclock.eot dist')
os.system('copy includes\\alarmclock.svg dist')
os.system('copy includes\\alarmclock.ttf dist')
os.system('copy includes\\alarmclock.woff dist')
os.system('copy includes\\artisan.tpl dist')
os.system('copy includes\\bigtext.js dist')
os.system('copy includes\\sorttable.js dist')
os.system('copy includes\\report-template.htm dist')
os.system('copy includes\\roast-template.htm dist')
os.system('copy includes\\ranking-template.htm dist')
os.system('copy includes\\jquery-1.11.1.min.js dist')
os.system(r'mkdir dist\\Machines')
os.system(r'xcopy includes\\Machines dist\\Machines /y /S')
os.system(r'mkdir dist\\Themes')
os.system(r'xcopy includes\\Themes dist\\Themes /y /S')
os.system('copy ..\\Redistribution2010\\vcredist_x86.exe dist')



