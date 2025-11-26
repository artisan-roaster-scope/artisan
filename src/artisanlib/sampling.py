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

from typing import override, TYPE_CHECKING
from babel.units import get_unit_name

from artisanlib.dialogs import ArtisanDialog
from artisanlib.widgets import MyQDoubleSpinBox

from PyQt6.QtCore import Qt, pyqtSlot, QSettings
from PyQt6.QtWidgets import (QMessageBox, QApplication, QHBoxLayout, QVBoxLayout, QCheckBox, QGridLayout,
                             QDialogButtonBox, QLayout)

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget, QPushButton # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent # pylint: disable=unused-import

class SamplingDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.aw = aw
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
        self.interval.setRange(self.aw.qmc.min_delay/1000.,999.99)
        interval = self.aw.qmc.delay/1000.
        if self.aw.qmc.xgrid < 3600:
            unit_name = get_unit_name('duration-second', length='short', locale=self.aw.locale_str)
            self.interval.setSuffix(f" {unit_name if unit_name is not None else 'sec'}")
        else:
            unit_name = get_unit_name('duration-minute', length='short', locale=self.aw.locale_str)
            self.interval.setSuffix(f" {unit_name if unit_name is not None else 'min'}")
            interval = interval / 60
        self.interval.setValue(interval)
        self.interval.setDecimals(2)
        self.interval.setAlignment(Qt.AlignmentFlag.AlignRight)

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
        ok_button: QPushButton|None = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setFocus()

        settings = QSettings()
        if settings.contains('SamplingPosition'):
            self.move(settings.value('SamplingPosition'))

        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    #window close box
    @pyqtSlot('QCloseEvent')
    @override
    def closeEvent(self, a0:'QCloseEvent|None' = None) -> None:
        del a0
        self.close()

    #cancel button
    @pyqtSlot()
    @override
    def close(self) -> bool:
        self.storeSettings()
        self.reject()
        return True

    def storeSettings(self) -> None:
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue('SamplingPosition',self.frameGeometry().topLeft())

    #ok button
    @pyqtSlot()
    def ok(self) -> None:
        self.aw.qmc.flagKeepON = bool(self.keepOnFlag.isChecked())
        self.aw.qmc.flagOpenCompleted = bool(self.openCompletedFlag.isChecked())
        interval = self.interval.value()*1000.
        if self.aw.qmc.xgrid >= 3600:
            interval = interval * 60
        self.aw.setSamplingRate(int(interval))
        if self.aw.qmc.delay < self.aw.qmc.default_delay:
            QMessageBox.warning(None, #self.aw, # only without super this one shows the native dialog on macOS under Qt 6.6.2 and later
                QApplication.translate('Message', 'Warning', None),
                QApplication.translate('Message', 'A tight sampling interval might lead to instability on some machines. We suggest a minimum of 1s.'))
        self.storeSettings()
        self.accept()
