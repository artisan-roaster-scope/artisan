#
# ABOUT
# Artisan Sampling Dialog

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

from artisanlib.dialogs import ArtisanDialog
from artisanlib.widgets import MyQDoubleSpinBox

try:
    from PyQt6.QtCore import Qt, pyqtSlot, QSettings # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QMessageBox, QApplication, QHBoxLayout, QVBoxLayout, QCheckBox, QGridLayout, # @UnusedImport @Reimport  @UnresolvedImport
                                 QDialogButtonBox, QLayout) # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import Qt, pyqtSlot, QSettings # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QMessageBox, QApplication, QHBoxLayout, QVBoxLayout, QCheckBox, QGridLayout, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
                                 QDialogButtonBox, QLayout) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

class SamplingDlg(ArtisanDialog):
    def __init__(self, parent, aw) -> None:
        super().__init__(parent, aw)
        self.setWindowTitle(QApplication.translate('Message','Sampling'))
        self.setModal(True)

        self.keepOnFlag = QCheckBox(QApplication.translate('Label','Keep ON'))
        self.keepOnFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.keepOnFlag.setChecked(bool(self.aw.qmc.flagKeepON))

        self.openCompletedFlag = QCheckBox(QApplication.translate('Label','Open Completed Roast in Viewer'))
        self.openCompletedFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.openCompletedFlag.setChecked(bool(self.aw.qmc.flagOpenCompleted))

        self.interval = MyQDoubleSpinBox()
        self.interval.setSingleStep(1)
        self.interval.setValue(self.aw.qmc.delay/1000.)
        self.interval.setRange(self.aw.qmc.min_delay/1000.,40.)
        self.interval.setDecimals(2)
        self.interval.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.interval.setSuffix('s')

        intervalLayout = QHBoxLayout()
        intervalLayout.addStretch()
        intervalLayout.addWidget(self.interval)
        intervalLayout.addStretch()

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.ok)
        self.dialogbuttons.rejected.connect(self.close)

        flagGrid = QGridLayout()
        flagGrid.addWidget(self.keepOnFlag,0,0)
        flagGrid.addWidget(self.openCompletedFlag,1,0)

        flagLayout = QHBoxLayout()
        flagLayout.addStretch()
        flagLayout.addLayout(flagGrid)
        flagLayout.addStretch()
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.dialogbuttons)

        #incorporate layouts
        layout = QVBoxLayout()
        layout.addLayout(intervalLayout)
        layout.addLayout(flagLayout)
        layout.addStretch()
        layout.addLayout(buttonsLayout)
        self.setLayout(layout)
        self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok).setFocus()

        settings = QSettings()
        if settings.contains('SamplingPosition'):
            self.move(settings.value('SamplingPosition'))

        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    #window close box
    def closeEvent(self,_):
        self.close()

    #cancel button
    @pyqtSlot()
    def close(self):
        self.storeSettings()
        self.reject()

    def storeSettings(self):
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue('SamplingPosition',self.frameGeometry().topLeft())

    #ok button
    @pyqtSlot()
    def ok(self):
        self.aw.qmc.flagKeepON = bool(self.keepOnFlag.isChecked())
        self.aw.qmc.flagOpenCompleted = bool(self.openCompletedFlag.isChecked())
        self.aw.setSamplingRate(int(self.interval.value()*1000.))
        if self.aw.qmc.delay < self.aw.qmc.default_delay:
            QMessageBox.warning(self.aw,
                QApplication.translate('Message', 'Warning', None),
                QApplication.translate('Message', 'A tight sampling interval might lead to instability on some machines. We suggest a minimum of 1s.'))
        self.storeSettings()
#        self.aw.closeEventSettings()
        self.accept()
