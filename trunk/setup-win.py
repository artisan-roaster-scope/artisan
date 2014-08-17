"""
This is a set up script for py2exe

USAGE: python setup-win py2exe

"""

from distutils.core import setup
import matplotlib as mpl
import py2exe

import os



INCLUDES = [
            "sip",
            "serial",
            "scipy.special._ufuncs_cxx",
            ]

EXCLUDES = ['_tkagg',
            '_ps',
            '_fltkagg',
            'Tkinter',
            'Tkconstants',
            '_cairo',
            '_gtk',
            'gtkcairo',
            'pydoc',
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
                        "dll_excludes":[
                            'MSVCP90.dll','tcl84.dll','tk84.dll','libgdk-win32-2.0-0.dll',
                            'libgdk_pixbuf-2.0-0.dll','libgobject-2.0-0.dll'],
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
os.system(r'copy c:\\Qt\\4.8.5\\translations\\qt_de.qm dist\\translations')
os.system(r'copy c:\\Qt\\4.8.5\\translations\\qt_es.qm dist\\translations')
os.system(r'copy c:\\Qt\\4.8.5\\translations\\qt_fr.qm dist\\translations')
os.system(r'copy c:\\Qt\\4.8.5\\translations\\qt_sv.qm dist\\translations')
os.system(r'copy c:\\Qt\\4.8.5\\translations\\qt_zh_CN.qm dist\\translations')
os.system(r'copy c:\\Qt\\4.8.5\\translations\\qt_zh_TW.qm dist\\translations')
os.system(r'copy c:\\Qt\\4.8.5\\translations\\qt_ko.qm dist\\translations')
os.system(r'copy c:\\Qt\\4.8.5\\translations\\qt_pt.qm dist\\translations')
os.system(r'copy c:\\Qt\\4.8.5\\translations\\qt_ru.qm dist\\translations')
os.system(r'copy c:\\Qt\\4.8.5\\translations\\qt_ar.qm dist\\translations')
os.system(r'copy c:\\Qt\\4.8.5\\translations\\qt_ja.qm dist\\translations')
os.system(r'copy c:\\Qt\\4.8.5\\translations\\qt_hu.qm dist\\translations')
os.system(r'copy artisan.png dist')
os.system(r'copy artisanAlarms.ico dist')
os.system(r'copy artisanProfile.ico dist')
os.system(r'copy artisanPalettes.ico dist')
os.system(r'copy artisanWheel.ico dist')
os.system(r'copy includes\\Humor-Sans.ttf dist')
os.system(r'copy ..\\vcredist_x86.exe dist')
