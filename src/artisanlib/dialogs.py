#!/usr/bin/env python3

# ABOUT
# Artisan Dialogs

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2020

import platform

from PyQt5.QtCore import (Qt, QSettings)
from PyQt5.QtWidgets import (QAction, QDialog, QMessageBox, QDialogButtonBox, QTextEdit, QHBoxLayout, QVBoxLayout)
from PyQt5.QtGui import QKeySequence

class ArtisanDialog(QDialog):
    def __init__(self, parent=None, aw = None):
        super(ArtisanDialog,self).__init__(parent)
        self.aw = aw # the Artisan application window
        
        # IMPORTANT NOTE: if dialog items have to be access after it has been closed, this Qt.WA_DeleteOnClose attribute 
        # has to be set to False explicitly in its initializer (like in comportDlg) to avoid the early GC and one might
        # want to use a dialog.deleteLater() call to explicitly have the dialog and its widgets GCe
        # or rather use sip.delete(dialog) if the GC via .deleteLater() is prevented by a link to a parent object (parent not None)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

#        if platf == 'Windows':
# setting those Windows flags could be the reason for some instabilities on Windows
#        #self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
#            windowFlags = self.windowFlags()
#        #windowFlags &= ~Qt.WindowContextHelpButtonHint # remove help button
#        #windowFlags &= ~Qt.WindowMaximizeButtonHint # remove maximise button
#        #windowFlags &= ~Qt.WindowMinMaxButtonsHint  # remove min/max combo
#        #windowFlags |= Qt.WindowMinimizeButtonHint  # Add minimize  button
#        windowFlags |= Qt.WindowSystemMenuHint  # Adds a window system menu, and possibly a close button
#            windowFlags |= Qt.WindowMinMaxButtonsHint  # add min/max combo
#            self.setWindowFlags(windowFlags)

        # configure standard dialog buttons
        self.dialogbuttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,Qt.Horizontal)
        self.dialogbuttons.button(QDialogButtonBox.Ok).setDefault(True)
        self.dialogbuttons.button(QDialogButtonBox.Ok).setAutoDefault(True)
        self.dialogbuttons.button(QDialogButtonBox.Cancel).setDefault(False)
        self.dialogbuttons.button(QDialogButtonBox.Cancel).setAutoDefault(False)
        self.dialogbuttons.button(QDialogButtonBox.Ok).setFocusPolicy(Qt.StrongFocus) # to add to tab focus switch
        if self.aw.locale not in self.aw.qtbase_locales:
            self.dialogbuttons.button(QDialogButtonBox.Ok).setText(QApplication.translate("Button","OK", None))
            self.dialogbuttons.button(QDialogButtonBox.Cancel).setText(QApplication.translate("Button","Cancel",None))
        # add additional CMD-. shortcut to close the dialog
        self.dialogbuttons.button(QDialogButtonBox.Cancel).setShortcut(QKeySequence("Ctrl+."))
        # add additional CMD-W shortcut to close this dialog (ESC on Mac OS X)
        cancelAction = QAction(self, triggered=lambda _:self.dialogbuttons.rejected.emit())
        try:
            cancelAction.setShortcut(QKeySequence.Cancel)
        except:
            pass
        self.dialogbuttons.button(QDialogButtonBox.Cancel).addActions([cancelAction])

    def closeEvent(self,_):
        self.dialogbuttons.rejected.emit()

    def keyPressEvent(self,event):
        key = int(event.key())
        #uncomment next line to find the integer value of a key
        #print(key)
        #modifiers = QApplication.keyboardModifiers()
        modifiers = event.modifiers()
        if key == 16777216 or (key == 87 and modifiers == Qt.ControlModifier): #ESCAPE or CMD-W
            self.close()

class ArtisanResizeablDialog(ArtisanDialog):
    def __init__(self, parent = None, aw = None):
        super(ArtisanResizeablDialog,self).__init__(parent, aw)
        if str(platform.system()) == 'Windows':
            windowFlags = self.windowFlags()
            windowFlags |= Qt.WindowMinMaxButtonsHint  # add min/max combo
            self.setWindowFlags(windowFlags)

class ArtisanMessageBox(QMessageBox):
    def __init__(self, parent = None, aw = None, title=None, text=None, timeout=0, modal=True):
        super(ArtisanMessageBox, self).__init__(parent, aw)
        self.setWindowTitle(title)
        self.setText(text)
        self.setModal(modal)
        self.setIcon(QMessageBox.Information)
        self.setStandardButtons(QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Ok)
        self.timeout = timeout # configured timeout, defaults to 0 (no timeout)
        self.currentTime = 0 # counts seconds after timer start
        
    def showEvent(self,_):
        self.currentTime = 0
        if (self.timeout and self.timeout != 0):
            self.startTimer(1000)
    
    def timerEvent(self,_):
        self.currentTime = self.currentTime + 1
        if (self.currentTime >= self.timeout):
            self.done(0)

class HelpDlg(ArtisanDialog):
    def __init__(self, parent = None, aw = None, title = "", content = ""):
        super(HelpDlg,self).__init__(parent, aw)
        self.setWindowTitle(title) 
        self.setModal(False)
        
        settings = QSettings()
        if settings.contains("HelpGeometry"):
            self.restoreGeometry(settings.value("HelpGeometry"))

        phelp = QTextEdit()
        phelp.setHtml(content)
        phelp.setReadOnly(True)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.removeButton(self.dialogbuttons.button(QDialogButtonBox.Cancel))
        self.dialogbuttons.accepted.connect(self.close)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)
        hLayout = QVBoxLayout()
        hLayout.addWidget(phelp)
        hLayout.addLayout(buttonLayout)
        self.setLayout(hLayout)
        self.dialogbuttons.button(QDialogButtonBox.Ok).setFocus()

    def closeEvent(self, _):
        settings = QSettings()
        #save window geometry
        settings.setValue("HelpGeometry",self.saveGeometry())
