#
# ABOUT
# artisan scope sampling dialog
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

from babel.units import get_unit_name
from typing import override, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget, QPushButton # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent # pylint: disable=unused-import

from PyQt6.QtCore import Qt, pyqtSlot, QSettings
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QVBoxLayout, QCheckBox, QGridLayout,
                             QDialogButtonBox, QLayout)

from artisanlib.dialogs import ArtisanDialog, artisan_warning
from artisanlib.widgets import MyQDoubleSpinBox
from artisanlib.styles import spin_box_style


class SamplingDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.aw = aw
        self.setWindowTitle(QApplication.translate('Message','Sampling'))
        self.setModal(True)

        self.keepOnFlag = QCheckBox(QApplication.translate('Label','Keep ON'))
        self.keepOnFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.keepOnFlag.setChecked(self.aw.qmc.flagKeepON)
        self.keepOnFlag.stateChanged.connect(self.keepOn_flag_changed)
        self.keepOnFlag.setToolTip(QApplication.translate('Tooltip', 'Automatically trigger ON after ending a recording'))

        self.openCompletedFlag = QCheckBox(QApplication.translate('Label','Open completed roasts in viewer'))
        self.openCompletedFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.openCompletedFlag.setChecked(self.aw.qmc.flagOpenCompleted)
        self.openCompletedFlag.setEnabled(self.aw.qmc.flagKeepON)
        self.openCompletedFlag.setToolTip(QApplication.translate('Tooltip', 'Open roasts in ArtisanViewer upon completion'))

        self.automatiUploadFlag = QCheckBox(QApplication.translate('Label','Upload completed roasts'))
        self.automatiUploadFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.automatiUploadFlag.setChecked(self.aw.plus_automatic_profile_upload)
        self.automatiUploadFlag.setEnabled(self.aw.plus_account is not None and self.aw.plus_subscription == 'MAX')
        self.automatiUploadFlag.setToolTip(QApplication.translate('Tooltip', 'Upload completed roast profiles to the artisan platform'))

        self.interval = MyQDoubleSpinBox()
        self.interval.setStyleSheet(spin_box_style(self.aw.app.darkmode))
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
        flagGrid.addWidget(self.automatiUploadFlag,2,0)
        flagGrid.setVerticalSpacing(15)

        flagLayout = QHBoxLayout()
        flagLayout.addStretch()
        flagLayout.addLayout(flagGrid)
        flagLayout.addStretch()
        flagLayout.setContentsMargins(10,0,10,0)
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.dialogbuttons)
        buttonsLayout.addStretch()

        #incorporate layouts
        layout = QVBoxLayout()
        layout.addLayout(intervalLayout)
        layout.addSpacing(5)
        layout.addLayout(flagLayout)
        layout.addSpacing(8)
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

    @pyqtSlot(int)
    def keepOn_flag_changed(self, _:int = 0) -> None:
        self.openCompletedFlag.setEnabled(self.keepOnFlag.isChecked())

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
        self.aw.plus_automatic_profile_upload = bool(self.automatiUploadFlag.isChecked())
        interval = self.interval.value()*1000.
        if self.aw.qmc.xgrid >= 3600:
            interval = interval * 60
        self.aw.setSamplingRate(int(interval))
        if self.aw.qmc.delay < self.aw.qmc.default_delay:
#            QMessageBox.warning(None, #self.aw, # only without super this one shows the native dialog on macOS under Qt 6.6.2 and later
#                QApplication.translate('Message', 'Warning'),
#                QApplication.translate('Message', 'A tight sampling interval might lead to instability on some machines. We suggest a minimum of 1s.'))
            artisan_warning(self, self.aw,
                QApplication.translate('Message', 'A tight sampling interval might lead to instability on some machines. We suggest a minimum of 1s.'))
        self.storeSettings()
        self.accept()
