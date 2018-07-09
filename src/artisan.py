#!/usr/bin/env python
"""
Start the application.
"""
import sys
#import imp # deprecated favour of importlib
import os
from platform import system

# needs to be done before any other PyQt import
import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

        
# on Qt5, the platform plugin cocoa/windows is not found in the plugin directory (dispite the qt.conf file) if we do not
# extend the libraryPath accordingly
if system() == 'Darwin':
    try:
        if str(sys.frozen) == "macosx_app":
            from PyQt5.QtWidgets import QApplication
            QApplication.addLibraryPath(os.path.dirname(os.path.abspath(__file__)) + "/qt_plugins/")
    except Exception:
        try:
            if str(sys.frozen) == "macosx_app":
                from PyQt4.QtGui import QApplication
                QApplication.addLibraryPath(os.path.dirname(os.path.abspath(__file__)) + "/qt_plugins/")
        except Exception:
            pass
elif system().startswith("Windows"):
    try:
        ib = (hasattr(sys, "frozen") or # new py2exe
            hasattr(sys, "importers") # old py2exe
#            or imp.is_frozen("__main__")) # tools/freeze
             or getattr(sys, 'frozen', False)) # tools/freeze           
        from PyQt5.QtWidgets import QApplication
        if ib:
            QApplication.addLibraryPath(os.path.join(os.path.dirname(os.path.realpath(sys.executable)), "plugins"))            
        else:
            import site
            #gives error in python 3.4: could not find or load the Qt platform plugin "windows"
            QApplication.addLibraryPath(site.getsitepackages()[1] + "\\PyQt5\\plugins")

    except Exception:
        try:
            from PyQt4.QtGui import QApplication
            if ib:
                QApplication.addLibraryPath(os.path.join(os.path.dirname(os.path.realpath(sys.executable)), "plugins"))
            else:
                import site
                QApplication.addLibraryPath(os.path.dirname(site.getsitepackages()[0]) + "\\PyQt4\\plugins")
        except:
            pass
else: # Linux
    try:
        ib = getattr(sys, 'frozen', False)
        from PyQt5.QtWidgets import QApplication
        if ib:
            QApplication.addLibraryPath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Resources/qt_plugins"))            
        else:
            import site
            QApplication.addLibraryPath(os.path.dirname(site.getsitepackages()[0]) + "/PyQt5/qt_plugins")
    except Exception:
        try:
            from PyQt4.QtGui import QApplication
            if ib:
                QApplication.addLibraryPath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Resources/qt_plugins"))
            else:
                import site
                QApplication.addLibraryPath(os.path.dirname(site.getsitepackages()[0]) + "/PyQt4/qt_plugins")
        except:
            pass
        
from artisanlib import main
import numpy
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
    freeze_support()
    if os.environ.get('TRAVIS'):
        # Hack to exit inside Travis CI
        # Ideally we would use pytest-qt.
        import threading
        t = threading.Timer(30, lambda: os._exit(0))
        t.start()
    main.main()


# EOF
