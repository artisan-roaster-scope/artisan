#
# ABOUT
# Artisan serial, error and message logs

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2023

from artisanlib import __version__

from artisanlib.dialogs import ArtisanDialog

try:
    from PyQt6.QtCore import pyqtSlot # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QLabel, QCheckBox, QTextEdit, QVBoxLayout) # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import pyqtSlot # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QLabel, QCheckBox, QTextEdit, QVBoxLayout) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


##########################################################################
#####################  VIEW SERIAL LOG DLG  ##############################
##########################################################################

class serialLogDlg(ArtisanDialog):
    def __init__(self, parent, aw) -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Serial Log'))
        self.serialcheckbox = QCheckBox(QApplication.translate('CheckBox','Serial Log ON/OFF'))
        self.serialcheckbox.setToolTip(QApplication.translate('Tooltip', 'ON/OFF logs serial communication'))
        self.serialcheckbox.setChecked(self.aw.seriallogflag)
        self.serialcheckbox.stateChanged.connect(self.serialcheckboxChanged)
        self.serialEdit = QTextEdit()
        self.serialEdit.setReadOnly(True)
        self.serialEdit.setHtml(self.getstring())
        layout = QVBoxLayout()
        layout.addWidget(self.serialcheckbox,0)
        layout.addWidget(self.serialEdit,1)
        self.setLayout(layout)

    def getstring(self):
        #convert list of serial comm an html string
        htmlserial = 'version = ' +__version__ +'<br><br>'
        lenl = len(self.aw.seriallog)
        for i in range(len(self.aw.seriallog)):
            htmlserial += '<b>' + str(lenl-i) + '</b> ' + self.aw.seriallog[-i-1] + '<br><br>'
        return htmlserial

    def update(self):
        if self.aw.seriallogflag:
            self.serialEdit.setText(self.getstring())

    @pyqtSlot(int)
    def serialcheckboxChanged(self,_):
        if self.serialcheckbox.isChecked():
            self.aw.seriallogflag = True
        else:
            self.aw.seriallogflag = False

    def closeEvent(self,_):
        self.close()
        self.aw.serial_dlg = None

##########################################################################
#####################  VIEW ERROR LOG DLG  ###############################
##########################################################################

class errorDlg(ArtisanDialog):
    def __init__(self, parent, aw) -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Error Log'))
        self.elabel = QLabel()
        self. errorEdit = QTextEdit()
        self.errorEdit.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addWidget(self.elabel,0)
        layout.addWidget(self.errorEdit,1)
        self.setLayout(layout)
        self.update()

    def update(self):
        #convert list of errors to an html string
        lenl = len(self.aw.qmc.errorlog)
        htmlerr = ''.join([f'<b>{lenl-i}</b> {m}<br><br>' for i,m in enumerate(reversed(self.aw.qmc.errorlog))])

        enumber = len(self.aw.qmc.errorlog)
        labelstr =  '<b>'+ QApplication.translate('Label','Number of errors found {0}').format(str(enumber)) + '</b>'
        self.elabel.setText(labelstr)
        self.errorEdit.setHtml('version = ' +__version__ +'<br><br>' + htmlerr)

    def closeEvent(self,_):
        self.close()
        self.aw.error_dlg = None


##########################################################################
#####################  MESSAGE HISTORY DLG  ##############################
##########################################################################

class messageDlg(ArtisanDialog):
    def __init__(self, parent, aw) -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Message History'))
        self.messageEdit = QTextEdit()
        self.messageEdit.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addWidget(self.messageEdit,0)
        self.setLayout(layout)
        self.update()

    def update(self):
        #convert list of messages to an html string
        lenl = len(self.aw.messagehist)
        htmlmessage = ''.join([f'<b>{lenl-i}</b> {m}<br><br>' for i,m in enumerate(reversed(self.aw.messagehist))])
        self.messageEdit.setHtml(htmlmessage)

    def closeEvent(self,_):
        self.close()
        self.aw.message_dlg = None
