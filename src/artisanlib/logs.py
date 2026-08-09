#
# ABOUT
# artisan scope serial, error and message logs
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


from typing import override, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent # pylint: disable=unused-import

from artisanlib import __version__

from artisanlib.dialogs import ArtisanDialog
from artisanlib.widgets import ArtisanPlainTextEdit

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (QApplication, QLabel, QCheckBox, QVBoxLayout)


##########################################################################
#####################  VIEW SERIAL LOG DLG  ##############################
##########################################################################

class serialLogDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Serial Log'))
        self.serialcheckbox = QCheckBox(QApplication.translate('CheckBox','Serial Log ON/OFF'))
        self.serialcheckbox.setToolTip(QApplication.translate('Tooltip', 'ON/OFF logs serial communication'))
        self.serialcheckbox.setChecked(self.aw.seriallogflag)
        self.serialcheckbox.stateChanged.connect(self.serialcheckboxChanged)
        self.serialEdit = ArtisanPlainTextEdit()
        self.serialEdit.setReadOnly(True)
        self.serialEdit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.serialEdit.setPlainText(self.getstring())
        layout = QVBoxLayout()
        layout.addWidget(self.serialcheckbox,0)
        layout.addWidget(self.serialEdit,1)
        self.setLayout(layout)

    def getstring(self) -> str:
        #convert list of serial comm an html string
        htmlserial = f'version = {__version__}\n\n'
        lenl = len(self.aw.seriallog)
        for i in range(len(self.aw.seriallog)):
            htmlserial += f'{lenl-i}: {self.aw.seriallog[-i-1]}\n\n'
        return htmlserial

    def update_log(self) -> None:
        if self.aw.seriallogflag:
            self.serialEdit.setPlainText(self.getstring())

    @pyqtSlot(int)
    def serialcheckboxChanged(self, _:int) -> None:
        if self.serialcheckbox.isChecked():
            self.aw.seriallogflag = True
        else:
            self.aw.seriallogflag = False

    @pyqtSlot('QCloseEvent')
    @override
    def closeEvent(self, a0:'QCloseEvent|None' = None) -> None:
        del a0
        self.close()
        self.aw.serial_dlg = None

##########################################################################
#####################  VIEW ERROR LOG DLG  ###############################
##########################################################################

class errorDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Error Log'))
        self.elabel = QLabel()
        self. errorEdit = ArtisanPlainTextEdit()
        self.errorEdit.setReadOnly(True)
        self.errorEdit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QVBoxLayout()
        layout.addWidget(self.elabel,0)
        layout.addWidget(self.errorEdit,1)
        self.setLayout(layout)
        self.update_log()

    def update_log(self) -> None:
        #convert list of errors to an html string
        lenl = len(self.aw.qmc.errorlog)
        htmlerr = ''.join([f'<b>{lenl-i}</b> {m}<br><br>' for i,m in enumerate(reversed(self.aw.qmc.errorlog))])

        enumber = len(self.aw.qmc.errorlog)
        labelstr =  f'{QApplication.translate('Label','Number of errors found {0}').format(str(enumber))}\n'
        self.elabel.setText(labelstr)
        self.errorEdit.setPlainText(f'version = {__version__}\n\n' + htmlerr)

    @pyqtSlot('QCloseEvent')
    @override
    def closeEvent(self, a0:'QCloseEvent|None' = None) -> None:
        del a0
        self.close()
        self.aw.error_dlg = None


##########################################################################
#####################  MESSAGE HISTORY DLG  ##############################
##########################################################################

class messageDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Message History'))
        self.messageEdit = ArtisanPlainTextEdit()
        self.messageEdit.setReadOnly(True)
        self.messageEdit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QVBoxLayout()
        layout.addWidget(self.messageEdit,0)
        self.setLayout(layout)
        self.update_log()

    def update_log(self) -> None:
        #convert list of messages to an html string
        lenl = len(self.aw.messagehist)
        htmlmessage = ''.join([f'<b>{lenl-i}</b> {m}<br><br>' for i,m in enumerate(reversed(self.aw.messagehist))])
        self.messageEdit.clear()
        self.messageEdit.appendHtml(htmlmessage)

    @pyqtSlot('QCloseEvent')
    @override
    def closeEvent(self, a0:'QCloseEvent|None' = None) -> None:
        del a0
        self.close()
        self.aw.message_dlg = None
