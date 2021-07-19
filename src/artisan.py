#!/usr/bin/env python
"""
Start the application.
"""

import warnings
warnings.simplefilter("ignore", DeprecationWarning)

import sys
import os
from platform import system

#try:
#    from PyQt6.QtCore import QLibraryInfo  # @UnusedImport @UnresolvedImport
#    pyqtversion = 6
#except Exception as e:
#    pyqtversion = 5
pyqtversion = 5 # until MPL and all build tools fully support PyQt6 we run on PyQt5

# highDPI support must be set before creating the Application instance
try:
    if system() == 'Darwin':
        os.environ["QT_MAC_WANTS_LAYER"] = "1" # some widgets under PyQt 5.15.1 on macOS seem not to update properly without this (see the discussion on the pyqt mailing list from 15.6.2020 "Widgets are not updated - is this a bug?")
    if pyqtversion < 6:
        from PyQt5.QtWidgets import QApplication  # @UnusedImport
        from PyQt5.QtCore import Qt  # @UnusedImport
    else:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
#    os.environ["QT_SCALE_FACTOR"] = "1"
except:
    pass

try:
    # PyQt new exit scheme (default from 5.14 on)
    if pyqtversion < 6:
        from PyQt5.QtCore import pyqt5_enable_new_onexit_scheme  # @UnresolvedImport @UnusedImport
    else:
        from PyQt6.QtCore import pyqt5_enable_new_onexit_scheme  # @UnresolvedImport
    pyqt5_enable_new_onexit_scheme(True)
except:
    pass
        
# on Qt5, the platform plugin cocoa/windows is not found in the plugin directory (dispite the qt.conf file) if we do not
# extend the libraryPath accordingly
if system() == 'Darwin':
    try:
        if str(sys.frozen) == "macosx_app":
            if pyqtversion < 6:
                from PyQt5.QtWidgets import QApplication # @Reimport  @UnusedImport
            else:
                from PyQt6.QtWidgets import QApplication # @Reimport
            #QApplication.addLibraryPath(os.path.dirname(os.path.abspath(__file__)) + "/qt_plugins/")

            libpath = os.path.dirname(sys.executable) # Contents/MacOS
            plugins_path = os.path.abspath(os.path.join(libpath,"../PlugIns/"))
            QApplication.addLibraryPath(plugins_path)
    except Exception:
        pass
elif system().startswith("Windows"):
    try:
        ib = (hasattr(sys, "frozen") or # new py2exe
            hasattr(sys, "importers") # old py2exe
#            or imp.is_frozen("__main__")) # tools/freeze
             or getattr(sys, 'frozen', False)) # tools/freeze
        if pyqtversion < 6:
            from PyQt5.QtWidgets import QApplication # @Reimport   @UnusedImport
        else:
            from PyQt6.QtWidgets import QApplication # @Reimport 
        if ib:
            QApplication.addLibraryPath(os.path.join(os.path.dirname(os.path.realpath(sys.executable)), "plugins"))            
        else:
            import site # @Reimport @UnusedImport
            #gives error in python 3.4: could not find or load the Qt platform plugin "windows"
            QApplication.addLibraryPath(site.getsitepackages()[1] + "\\PyQt5\\plugins")

    except Exception:
        pass
else: # Linux
    try:
        ib = getattr(sys, 'frozen', False)
        if pyqtversion < 6:
            from PyQt5.QtWidgets import QApplication # @Reimport @UnusedImport
        else:
            from PyQt6.QtWidgets import QApplication # @Reimport
        if ib:
            QApplication.addLibraryPath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Resources/qt_plugins"))            
        else:
            import site # @Reimport
            QApplication.addLibraryPath(os.path.dirname(site.getsitepackages()[0]) + "/PyQt5/qt_plugins")
    except Exception:
        pass

from artisanlib import main, command_utility
#import numpy # @UnusedImport # what this for!?
from multiprocessing import freeze_support

if system() == "Windows" and (hasattr(sys, "frozen") # new py2exe
                            or hasattr(sys, "importers") # old py2exe
#                            or imp.is_frozen("__main__")): # tools/freeze
                            or getattr(sys, 'frozen', False)): # tools/freeze
    from multiprocessing import set_executable
    executable = os.path.join(os.path.dirname(sys.executable), 'artisan.exe')
    set_executable(executable)    
    del executable

if __name__ == '__main__':

    # Manange Commands that does not need to start the whole Application
    if command_utility.handleCommands() == True:
        freeze_support()
        if os.environ.get('TRAVIS'):
            # Hack to exit inside Travis CI
            # Ideally we would use pytest-qt.
            import threading
            t = threading.Timer(30, lambda: os._exit(0))
            t.start()
        main.main()


# EOF
