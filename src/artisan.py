#!/usr/bin/env python3
"""Start the application.
"""

import warnings
warnings.simplefilter('ignore', DeprecationWarning)

import sys
import os
from platform import system
from typing import Any

# limit the number of numpy threads to 1 to limit the total number of threads taking into account a potential performance reduction on array operations using blas,
# which should not be significant
os.environ['OMP_NUM_THREADS'] = '1'

# highDPI support must be set before creating the Application instance
try:
# the following two lines seem not to be needed any longer with Qt6.1
#    if system() == 'Darwin':
#        os.environ['QT_MAC_WANTS_LAYER'] = '1' # some widgets under PyQt  on macOS seem not to update properly without this (see the discussion on the pyqt mailing list from 15.6.2020 "Widgets are not updated - is this a bug?")
    try:
        #pylint: disable = E, W, R, C
        from PyQt6.QtWidgets import QApplication  # @UnusedImport @Reimport  @UnresolvedImport
        from PyQt6.QtCore import Qt     # @Reimport # @UnusedImport @Reimport  @UnresolvedImport
    except Exception: # pylint: disable=broad-except
        #pylint: disable = E, W, R, C
        from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        from PyQt5.QtCore import Qt # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling) # type: ignore
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps) # type: ignore
#    os.environ["QT_SCALE_FACTOR"] = "1"
except Exception: # pylint: disable=broad-except
    pass

# on Qt5, the platform plugin cocoa/windows is not found in the plugin directory (despite the qt.conf file) if we do not
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
            from PyQt5.QtWidgets import QApplication # type: ignore # @UnresolvedImport @Reimport @UnusedImport pylint: disable=import-error
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
            from PyQt5.QtWidgets import QApplication # type: ignore # @UnresolvedImport @Reimport @UnusedImport pylint: disable=import-error
            if ib:
                QApplication.addLibraryPath(os.path.join(os.path.dirname(__file__), 'Resources/qt_plugins'))
            else:
                import site # @Reimport
                QApplication.addLibraryPath(os.path.dirname(site.getsitepackages()[0]) + '/PyQt5/qt_plugins')
    except Exception: # pylint: disable=broad-except
        pass

from artisanlib import main, command_utility
#from multiprocessing import freeze_support

# from pyinstaller 5.8:
class NullWriter:
    softspace = 0
    encoding:str = 'UTF-8'

    @staticmethod
    def write(*args:Any) -> None:
        pass

    @staticmethod
    def flush(*args:Any) -> None:
        pass

    # Some packages are checking if stdout/stderr is available (e.g., youtube-dl). For details, see #1883.
    @staticmethod
    def isatty() -> bool:
        return False

if system() == 'Windows' and hasattr(sys, 'frozen'): # tools/freeze
    # to (re-)set sys.stdout/sys.stderr on Windows builds under PyInstaller >= 5.8.0 (set to None under --noconsole using pythonw)
    # which is assumed by bottle.py (used by WebLCDs) to exists (Issue #1229)
    # see also
    #   https://github.com/bottlepy/bottle/issues/1104#issuecomment-1195740112
    #   https://github.com/bottlepy/bottle/issues/1401#issuecomment-1284450625
    #   https://github.com/r0x0r/pywebview/pull/1048/files
    #   https://stackoverflow.com/questions/19425736/how-to-redirect-stdout-and-stderr-to-logger-in-python
    try:
        if sys.stdout is None:
            sys.stdout = NullWriter() # type: ignore[unreachable, unused-ignore]
        if sys.stderr is None:
            sys.stderr = NullWriter() # type: ignore[unreachable, unused-ignore]
    except Exception: # pylint: disable=broad-except
        pass

# no longer needed as multiprocessing is not used by Hottop/WebLCDs any longer
#    from multiprocessing import set_executable
#    executable = os.path.join(os.path.dirname(sys.executable), 'artisan.exe')
#    set_executable(executable)
#    del executable

if __name__ == '__main__':

    # Manage commands that does not need to start the whole application
    if command_utility.handleCommands():
#        freeze_support() # needed for multiprocessing; was used by Hottop/WebLCDs module, as well as for py-cpuinfo!
        main.main()


# EOF
