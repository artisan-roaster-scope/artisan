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
            "serial"
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

cwd = os.getcwd()

setup(
    name ="Artisan",
    author = "YOU",
    windows=[{"script" : cwd + "\\artisan.py",
            "icon_resources": [(0, cwd + "\\artisan.ico")]
            }],
    data_files = mpl.get_py2exe_datafiles(),
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
os.system(r'mkdir dist\\Wheels')
os.system(r'mkdir dist\\Wheels\\Cupping')
os.system(r'mkdir dist\\Wheels\\Other')
os.system(r'mkdir dist\\Wheels\\Roasting')
os.system(r'copy Wheels\\Cupping\\* dist\\Wheels\\Cupping')
os.system(r'copy Wheels\\Other\\* dist\\Wheels\\Other')
os.system(r'copy Wheels\\Roasting\\* dist\\Wheels\\Roasting')
os.system(r'mkdir dist\\translations')
os.system(r'copy translations\\*.qm dist\\translations')
#os.system(r'copy artisan.png dist')
