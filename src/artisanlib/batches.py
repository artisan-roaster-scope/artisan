#!/usr/bin/env python3

# ABOUT
# Artisan Batches Dialog

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

from artisanlib.dialogs import ArtisanDialog

from PyQt5.QtCore import Qt, pyqtSlot, QSettings
from PyQt5.QtWidgets import (QApplication, QLabel, QHBoxLayout, QVBoxLayout, QCheckBox,
                             QDialogButtonBox, QGridLayout, QLineEdit, QSpinBox, QLayout)

class batchDlg(ArtisanDialog):
    def __init__(self, parent = None, aw = None):
        super(batchDlg,self).__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate("Form Caption","Batch", None))
        self.prefixEdit = QLineEdit(self.aw.qmc.batchprefix)
        self.prefixEdit.setToolTip(QApplication.translate("Tooltip", "Batch prefix",None))
        self.counterSpinBox = QSpinBox()
        self.counterSpinBox.setRange(0,999999)
        self.counterSpinBox.setSingleStep(1)
        self.counterSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        batchchecklabel = QLabel(QApplication.translate("CheckBox","Batch Counter", None))
        self.batchcheckbox = QCheckBox()
        self.batchcheckbox.setToolTip(QApplication.translate("Tooltip", "ON/OFF batch counter",None))
        if self.aw.qmc.batchcounter > -1:
            self.batchcheckbox.setChecked(True)
        else:
            self.batchcheckbox.setChecked(False)
        prefixlabel = QLabel()
        prefixlabel.setAlignment(Qt.Alignment(Qt.AlignVCenter | Qt.AlignRight))
        prefixlabel.setText(QApplication.translate("Label", "Prefix",None))
        counterlabel = QLabel()
        counterlabel.setAlignment(Qt.Alignment(Qt.AlignVCenter | Qt.AlignRight))
        counterlabel.setText(QApplication.translate("Label", "Counter",None))
        descrLabel = QLabel("<i>" + QApplication.translate("Message", "Next batch: counter+1",None) + "</i>")
        
        neverOverwriteCounterlabel = QLabel(QApplication.translate("CheckBox","Never overwrite counter", None))
        self.neverOverwriteCheckbox = QCheckBox()
        self.neverOverwriteCheckbox.setToolTip(QApplication.translate("Tooltip", "If ticked, the batch counter is never modified by loading a settings file",None))
        if self.aw.qmc.neverUpdateBatchCounter:
            self.neverOverwriteCheckbox.setChecked(True)
        else:
            self.neverOverwriteCheckbox.setChecked(False)
        
        if self.aw.qmc.batchcounter > -1:
            self.counterSpinBox.setValue(self.aw.qmc.batchcounter)
            self.counterSpinBox.setEnabled(True)
            self.prefixEdit.setEnabled(True)
            self.neverOverwriteCheckbox.setEnabled(True)
        else:
            self.counterSpinBox.setValue(0)
            self.counterSpinBox.setEnabled(False)
            self.prefixEdit.setEnabled(False)
            self.neverOverwriteCheckbox.setEnabled(False)
        
        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.batchChanged)
        self.dialogbuttons.rejected.connect(self.close)
        
        self.batchcheckbox.stateChanged.connect(self.toggleCounterFlag)
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)
        batchlayout = QGridLayout()
        batchlayout.addWidget(self.batchcheckbox,0,0,Qt.AlignRight)
        batchlayout.addWidget(batchchecklabel,0,1)
        batchlayout.addWidget(prefixlabel,1,0)
        batchlayout.addWidget(self.prefixEdit,1,1)
        batchlayout.addWidget(counterlabel,2,0)
        batchlayout.addWidget(self.counterSpinBox,2,1)
        batchlayout.addWidget(descrLabel,3,0,1,3)
        batchlayout.addWidget(self.neverOverwriteCheckbox,4,0,Qt.AlignRight)
        batchlayout.addWidget(neverOverwriteCounterlabel,4,1)
        
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(batchlayout)
        mainLayout.addStretch()
        mainLayout.addSpacing(10)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
        self.dialogbuttons.button(QDialogButtonBox.Ok).setFocus()

        settings = QSettings()
        if settings.contains("BatchPosition"):
            self.move(settings.value("BatchPosition"))
        
        mainLayout.setSizeConstraint(QLayout.SetFixedSize)

    @pyqtSlot(int)
    def toggleCounterFlag(self,_):
        if self.batchcheckbox.isChecked():
            self.prefixEdit.setEnabled(True)
            self.counterSpinBox.setEnabled(True)
            self.neverOverwriteCheckbox.setEnabled(True)
        else:
            self.prefixEdit.setEnabled(False)
            self.counterSpinBox.setEnabled(False)
            self.neverOverwriteCheckbox.setEnabled(False)

    @pyqtSlot()
    def batchChanged(self):
        self.aw.qmc.batchprefix = self.prefixEdit.text()
        if self.batchcheckbox.isChecked():
            self.aw.qmc.batchcounter = self.counterSpinBox.value()
        else:
            self.aw.qmc.batchcounter = -1
            self.aw.qmc.batchsequence = 1
        self.aw.qmc.neverUpdateBatchCounter = self.neverOverwriteCheckbox.isChecked()
        self.aw.closeEventSettings()
        self.close()
    
    @pyqtSlot()
    def close(self):
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue("BatchPosition",self.frameGeometry().topLeft())
        super(batchDlg,self).close()