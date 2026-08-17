#
# ABOUT
# artisan scope platform dialog
#
# COPYRIGHT (C) 2010-2026 The artisan team represented by
#   Marko Luther <marko.luther@gmx.net> (maintainer) and all contributors
#
# LICENSE
# This program or module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# MAINTAINER
# Marko Luther, 2026
#
# AUTHOR
# Marko Luther, 2023

import platform

from typing import TYPE_CHECKING

from artisanlib import __version__
from artisanlib import __revision__

from artisanlib.dialogs import ArtisanDialog
from artisanlib.widgets import ArtisanPlainTextEdit
from artisanlib.util import appFrozen, application_name, application_viewer_name


import matplotlib as mpl
import numpy

from PyQt6.QtCore import Qt, PYQT_VERSION_STR
from PyQt6.QtWidgets import QApplication, QVBoxLayout


if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget # pylint: disable=unused-import

class platformDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)

        from scipy import __version__ as SCIPY_VERSION_STR
        from pymodbus import __version__ as PYMODBUS_VERSION_STR

        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Artisan Platform'))

        platformdic:dict[str,str] = {}

        system = str(platform.system())
        if system == 'Windows':
            platformdic['Win32'] = str(platform.win32_ver())
        elif system == 'Darwin':
            platformdic['Mac'] = str(platform.mac_ver())
        elif system == 'Linux':
            try:
                import distro # type: ignore[import-not-found,unused-ignore] # @UnresolvedImport # pylint: disable=import-error
                platformdic['Linux'] = str(distro.linux_distribution()) # pyright:ignore[reportUnknownArgumentType]
                platformdic['Libc'] = str(platform.libc_ver())
            except Exception: # pylint: disable=broad-except
                pass
        platformdic['Architecture'] = str(platform.architecture())
        platformdic['Machine'] = str(platform.machine())
        platformdic['Platform name'] =  str(platform.platform())
        platformdic['Processor'] = str(platform.processor())
        platformdic['==========='] = ''
        platformdic['Python Build'] = str(platform.python_build())
        platformdic['Python Compiler'] = str(platform.python_compiler())
        platformdic['Python Branch'] = str(platform.python_branch())
        platformdic['Python Implementation'] = str(platform.python_implementation())
        platformdic['Python Revision'] = str(platform.python_revision())
        platformdic['Release'] = str(platform.release())
        platformdic['System'] = str(platform.system())
        platformdic['Version'] = str(platform.version())
        platformdic['Python version'] = str(platform.python_version())
        platformdic['============'] = ''
        from PyQt6.QtCore import qVersion
        platformdic['Qt'] = qVersion()
        platformdic['PyQt'] = PYQT_VERSION_STR
        platformdic['numpy'] = numpy.__version__
        platformdic['scipy'] = SCIPY_VERSION_STR
        platformdic['matplotlib'] = mpl.__version__
        platformdic['pymodbus'] = PYMODBUS_VERSION_STR
        try:
            from Phidget22.Phidget import Phidget as PhidgetDriver # type: ignore[import-untyped]
            platformdic['Phidget driver'] = PhidgetDriver.getLibraryVersion()
        except Exception: # pylint: disable=broad-except
            pass
        try:
            from Phidget22 import __version__ as phidget_lib_version # type: ignore[import-untyped] # @UnresolvedImport
            platformdic['Phidget lib'] = phidget_lib_version
        except Exception: # pylint: disable=broad-except
            pass
        try:
            from yoctopuce.yocto_api import YAPI # type: ignore[import-untyped]
            yocto_version = YAPI.GetAPIVersion() # type:ignore[reportPossibleUnboundVariable,unused-ignore]
            platformdic['Yoctopuce'] = yocto_version
        except Exception: # pylint: disable=broad-except
            pass

        unofficial = ('' if not appFrozen() or self.aw.official_build else QApplication.translate('Message', 'unoffical build')) # fork, mod

        htmlplatform:str = f'<b>{(application_viewer_name if self.aw.app.artisanviewerMode else application_name)} version =</b> {__version__} ({__revision__}) {unofficial}<br>---------<br>'
        for key,value in platformdic.items():
            htmlplatform += '<b>' + key + ' = </b> <i>' + value + '</i><br>'
        platformEdit = ArtisanPlainTextEdit()
        platformEdit.appendHtml(htmlplatform)
        platformEdit.setReadOnly(True)
        platformEdit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QVBoxLayout()
        layout.addWidget(platformEdit)
        self.setLayout(layout)
