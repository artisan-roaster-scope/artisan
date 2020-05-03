#!/usr/bin/env python3

# ABOUT
# Artisan Sampling Dialog

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

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QVBoxLayout, QCheckBox,
                             QDialogButtonBox, QDoubleSpinBox, QLayout, QMessageBox)

class SamplingDlg(ArtisanDialog):
    def __init__(self, parent = None, aw = None):
        super(SamplingDlg,self).__init__(parent, aw)
        self.setWindowTitle(QApplication.translate("Message","Sampling Interval", None))
        self.setModal(True)
        
        self.keepOnFlag = QCheckBox(QApplication.translate("Label","Keep ON", None))
        self.keepOnFlag.setFocusPolicy(Qt.NoFocus)
        self.keepOnFlag.setChecked(bool(self.aw.qmc.flagKeepON))
        
        self.interval = QDoubleSpinBox()
        self.interval.setSingleStep(1)
        self.interval.setValue(self.aw.qmc.delay/1000.)
        self.interval.setRange(self.aw.qmc.min_delay/1000.,40.)
        self.interval.setDecimals(1)
        self.interval.setAlignment(Qt.AlignRight)
        self.interval.setSuffix("s")
        
        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.ok)
        self.dialogbuttons.rejected.connect(self.close)
        
        flagLayout = QHBoxLayout()
        flagLayout.addStretch()
        flagLayout.addWidget(self.keepOnFlag)
        flagLayout.addStretch()
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.dialogbuttons)
        
        #incorporate layouts
        layout = QVBoxLayout()
        layout.addWidget(self.interval)
        layout.addLayout(flagLayout)
        layout.addStretch()
        layout.addLayout(buttonsLayout)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(layout) 
        self.dialogbuttons.button(QDialogButtonBox.Ok).setFocus()
        
    def closeEvent(self,_):
        self.close()
        
    #cancel button
    @pyqtSlot()
    def close(self):
        self.reject()
    
    #ok button
    @pyqtSlot()
    def ok(self):
        if self.keepOnFlag.isChecked():
            self.aw.qmc.flagKeepON = True
        else:
            self.aw.qmc.flagKeepON = False
        self.aw.qmc.delay = int(self.interval.value()*1000.)
        if self.aw.qmc.delay < self.aw.qmc.default_delay:
            QMessageBox.warning(self.aw,QApplication.translate("Message", "Warning",None),QApplication.translate("Message", "A tight sampling interval might lead to instability on some machines. We suggest a minimum of 3s.",None))        
        self.accept()

