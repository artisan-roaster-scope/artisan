"""
This is a set up script for py2exe

USAGE: python setup-win py2exe

"""

from distutils.core import setup
import matplotlib
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
            '_agg',
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
    author = "YOUcouldbeTOO",
    author_email="zaub.ERASE.org@yahoo.com",
    windows=[{"script" : "E:\\Artisan\\artisan\\trunk\\artisan.pyw"}],
    data_files = matplotlib.get_py2exe_datafiles(),
    # using zipfile to reduce number of files in \dist output
    zipfile = r'lib\library.zip',
    options={"py2exe" :{
                        "packages": ['matplotlib','pytz'],
                        "compressed":False,
                        "unbuffered": True,
                        "optimize":0,
                        "dll_excludes":[
                            'tcl84.dll','tk84.dll','libgdk-win32-2.0-0.dll',
                            'libgdk_pixbuf-2.0-0.dll','libgobject-2.0-0.dll'],
                        "includes" : INCLUDES,
                        "excludes" : EXCLUDES}
             }
    )

