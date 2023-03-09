#!/usr/bin/env python3
"""
Start the application.
"""

import warnings
warnings.simplefilter('ignore', DeprecationWarning)

import sys
import os
from platform import system

# highDPI support must be set before creating the Application instance
try:
    if system() == 'Darwin':
        os.environ['QT_MAC_WANTS_LAYER'] = '1' # some widgets under PyQt  on macOS seem not to update properly without this (see the discussion on the pyqt mailing list from 15.6.2020 "Widgets are not updated - is this a bug?")
    try:
        #pylint: disable = E, W, R, C
        from PyQt6.QtWidgets import QApplication  # @UnusedImport @Reimport  @UnresolvedImport
        from PyQt6.QtCore import Qt     # @Reimport # @UnusedImport @Reimport  @UnresolvedImport
    except Exception: # pylint: disable=broad-except
        #pylint: disable = E, W, R, C
        from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        from PyQt5.QtCore import Qt # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
#    os.environ["QT_SCALE_FACTOR"] = "1"
except Exception: # pylint: disable=broad-except
    pass

# on Qt5, the platform plugin cocoa/windows is not found in the plugin directory (dispite the qt.conf file) if we do not
# extend the libraryPath accordingly
if system().startswith('Windows'):
    try:
        ib = (
            hasattr(sys, 'frozen') or # new py2exe
            hasattr(sys, 'importers') # old py2exe
        )
        try:
            from PyQt6.QtWidgets import QApplication  # @UnresolvedImport @Reimport @UnusedImport pylint: disable=import-error
            if ib:
                QApplication.addLibraryPath(os.path.join(os.path.dirname(os.path.realpath(sys.executable)), 'plugins'))
            else:
                import site # @Reimport @UnusedImport
                QApplication.addLibraryPath(site.getsitepackages()[1] + '\\PyQt6\\plugins')
        except Exception:  # pylint: disable=broad-except
            from PyQt5.QtWidgets import QApplication  # @UnresolvedImport @Reimport @UnusedImport pylint: disable=import-error
            if ib:
                QApplication.addLibraryPath(os.path.join(os.path.dirname(os.path.realpath(sys.executable)), 'plugins'))
            else:
                import site # @Reimport @UnusedImport
                QApplication.addLibraryPath(site.getsitepackages()[1] + '\\PyQt5\\plugins')

    except Exception: # pylint: disable=broad-except
        pass
else: # Linux
    try:
        ib = getattr(sys, 'frozen', False)
        try:
            from PyQt6.QtWidgets import QApplication  # @UnresolvedImport @Reimport @UnusedImport pylint: disable=import-error
            if ib:
                QApplication.addLibraryPath(os.path.join(os.path.dirname(__file__), 'Resources/qt_plugins'))
            else:
                import site # @Reimport
                QApplication.addLibraryPath(os.path.dirname(site.getsitepackages()[0]) + '/PyQt6/qt_plugins')
        except Exception:  # pylint: disable=broad-except
            from PyQt5.QtWidgets import QApplication  # @UnresolvedImport @Reimport @UnusedImport pylint: disable=import-error
            if ib:
                QApplication.addLibraryPath(os.path.join(os.path.dirname(__file__), 'Resources/qt_plugins'))
            else:
                import site # @Reimport
                QApplication.addLibraryPath(os.path.dirname(site.getsitepackages()[0]) + '/PyQt5/qt_plugins')
    except Exception: # pylint: disable=broad-except
        pass

from artisanlib import main, command_utility
from multiprocessing import freeze_support

if system() == 'Windows' and hasattr(sys, 'frozen'): # tools/freeze
    from multiprocessing import set_executable
    executable = os.path.join(os.path.dirname(sys.executable), 'artisan.exe')
    set_executable(executable)
    del executable

if __name__ == '__main__':

    # Manage commands that does not need to start the whole application
    if command_utility.handleCommands():
        freeze_support()
        main.main()


# EOF
