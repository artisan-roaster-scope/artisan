"""
This is a set up script for py2exe

USAGE: python setup-win py2exe

"""

from distutils.core import setup
import matplotlib as mpl
import py2exe

INCLUDES = [
            "sip",
            "serial",
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

setup(
    name ="Artisan",
    author = "YOU",
    windows=[{"script" : "C:\\SVN\\trunk\\artisan\\artisan.py"}],
    data_files = mpl.get_py2exe_datafiles(),
    zipfile = "lib\library.zip",
    options={"py2exe" :{
                        "packages": ['matplotlib','pytz',],
                        "compressed": True,
                        "unbuffered": True,
                        "dll_excludes":[
                            'tcl84.dll','tk84.dll','libgdk-win32-2.0-0.dll',
                            'libgdk_pixbuf-2.0-0.dll','libgobject-2.0-0.dll'],
                        "includes" : INCLUDES,
                        "excludes" : EXCLUDES}
             }
    )

