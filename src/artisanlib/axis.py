#
# ABOUT
# Artisan Axis Dialog

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

import platform
from typing import Optional, TYPE_CHECKING


from artisanlib.util import deltaLabelUTF8, stringfromseconds, stringtoseconds
from artisanlib.dialogs import ArtisanDialog

try:
    from PyQt6.QtCore import Qt, pyqtSlot, QRegularExpression, QSettings # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QIntValidator, QRegularExpressionValidator # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QLabel, QDialogButtonBox, QFrame, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QGridLayout, QGroupBox, QLineEdit, QLayout, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QSpinBox) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import Qt, pyqtSlot, QRegularExpression, QSettings # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QIntValidator, QRegularExpressionValidator # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QLabel, QDialogButtonBox, QFrame, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QGridLayout, QGroupBox, QLineEdit, QLayout, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QSpinBox) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    from PyQt6.QtWidgets import QPushButton, QWidget # pylint: disable=unused-import

class WindowsDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)

        # remember previous original settings

        self.time_grid_org = self.aw.qmc.time_grid
        self.temp_grid_org = self.aw.qmc.temp_grid
        self.gridlinestyle_org = self.aw.qmc.gridlinestyle
        self.gridthickness_org = self.aw.qmc.gridthickness
        self.gridalpha_org = self.aw.qmc.gridalpha
        self.step100temp_org = self.aw.qmc.step100temp
        self.xgrid_org = self.aw.qmc.xgrid
        self.ygrid_org = self.aw.qmc.ygrid
        self.grid_org = self.aw.qmc.zgrid
        self.zlimit_org = self.aw.qmc.zlimit
        self.zlimit_min_org = self.aw.qmc.zlimit_min
        self.legendloc_org = self.aw.qmc.legendloc
        self.resetmaxtime_org = self.aw.qmc.resetmaxtime
        self.chargemintime_org = self.aw.qmc.chargemintime
        self.fixmaxtime_org = self.aw.qmc.fixmaxtime
        self.locktimex_org = self.aw.qmc.locktimex
        self.autotimex_org = self.aw.qmc.autotimex
        self.autotimexMode_org = self.aw.qmc.autotimexMode
        self.autodeltaxET_org = self.aw.qmc.autodeltaxET
        self.autodeltaxBT_org = self.aw.qmc.autodeltaxBT
        self.loadaxisfromprofile_org = self.aw.qmc.loadaxisfromprofile
        self.startofx_org = self.aw.qmc.startofx
        self.endofx_org = self.aw.qmc.endofx
        self.locktimex_start = self.aw.qmc.locktimex_start
        self.locktimex_end_org = self.aw.qmc.locktimex_end
        self.ylimit_org = self.aw.qmc.ylimit
        self.ylimit_min_org = self.aw.qmc.ylimit_min

        self.setWindowTitle(QApplication.translate('Form Caption','Axes'))
        self.setModal(True)
        xlimitLabel = QLabel(QApplication.translate('Label', 'Max'))
        xlimitLabel_min = QLabel(QApplication.translate('Label', 'Min'))
        ylimitLabel = QLabel(QApplication.translate('Label', 'Max'))
        ylimitLabel_min = QLabel(QApplication.translate('Label', 'Min'))
        zlimitLabel = QLabel(QApplication.translate('Label', 'Max'))
        zlimitLabel_min = QLabel(QApplication.translate('Label', 'Min'))
        step100Label = QLabel(QApplication.translate('Label', '100% Event Step'))
        self.step100Edit = QLineEdit()
        self.step100Edit.setMaximumWidth(55)
        self.step100Edit.setValidator(QIntValidator(int(self.aw.qmc.ylimit_min_max), 999999, self.step100Edit))
        self.step100Edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.step100Edit.setToolTip(QApplication.translate('Tooltip', '100% event values in step mode are aligned with the given y-axis value or the lowest phases limit if left empty'))
        self.step100Edit.editingFinished.connect(self.step100Changed)
        self.xlimitEdit = QLineEdit()
        self.xlimitEdit.setMaximumWidth(50)
        self.xlimitEdit.setMinimumWidth(50)
        self.xlimitEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.xlimitEdit_min = QLineEdit()
        self.xlimitEdit_min.setMaximumWidth(55)
        self.xlimitEdit_min.setMinimumWidth(55)
        self.xlimitEdit_min.setAlignment(Qt.AlignmentFlag.AlignRight)
        regextime = QRegularExpression(r'^-?[0-9]?[0-9]?[0-9]:[0-5][0-9]$')
        self.xlimitEdit.setValidator(QRegularExpressionValidator(regextime,self))
        self.xlimitEdit_min.setValidator(QRegularExpressionValidator(regextime,self))
        self.ylimitEdit = QLineEdit()
        self.ylimitEdit.setMaximumWidth(60)
        self.ylimitEdit_min = QLineEdit()
        self.ylimitEdit_min.setMaximumWidth(60)
        self.ylimitEdit.setValidator(QIntValidator(int(self.aw.qmc.ylimit_min_max), int(self.aw.qmc.ylimit_max), self.ylimitEdit))
        self.ylimitEdit_min.setValidator(QIntValidator(int(self.aw.qmc.ylimit_min_max), int(self.aw.qmc.ylimit_max), self.ylimitEdit_min))
        self.ylimitEdit.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.ylimitEdit_min.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.zlimitEdit = QLineEdit()
        self.zlimitEdit.setMaximumWidth(60)
        self.zlimitEdit_min = QLineEdit()
        self.zlimitEdit_min.setMaximumWidth(60)
        self.zlimitEdit.setValidator(QIntValidator(int(self.aw.qmc.zlimit_min_max), int(self.aw.qmc.zlimit_max), self.zlimitEdit))
        self.zlimitEdit_min.setValidator(QIntValidator(int(self.aw.qmc.zlimit_min_max), int(self.aw.qmc.zlimit_max), self.zlimitEdit_min))
        self.zlimitEdit.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.zlimitEdit_min.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.xlimitEdit.setText(stringfromseconds(self.aw.qmc.endofx))

        self.xlimitEdit.editingFinished.connect(self.xlimitChanged)
        if self.aw.qmc.timeindex[0] != -1:
            self.xlimitEdit_min.setText(stringfromseconds(self.aw.qmc.startofx - self.aw.qmc.timex[self.aw.qmc.timeindex[0]]))
        else:
            self.xlimitEdit_min.setText(stringfromseconds(self.aw.qmc.startofx))
        self.xlimitEdit_min.editingFinished.connect(self.xlimitMinChanged)
        self.ylimitEdit.setText(str(self.aw.qmc.ylimit))
        self.ylimitEdit.editingFinished.connect(self.ylimitChanged)
        self.ylimitEdit_min.setText(str(self.aw.qmc.ylimit_min))
        self.ylimitEdit_min.editingFinished.connect(self.ylimitChanged)
        if self.aw.qmc.step100temp is not None:
            self.step100Edit.setText(str(self.aw.qmc.step100temp))
        else:
            self.step100Edit.setText('')
        self.zlimitEdit.setText(str(self.aw.qmc.zlimit))
        self.zlimitEdit.editingFinished.connect(self.zlimitChanged)
        self.zlimitEdit_min.setText(str(self.aw.qmc.zlimit_min))
        self.zlimitEdit_min.editingFinished.connect(self.zlimitMinChanged)
        self.legendComboBox = QComboBox()
        self.legendComboBox.setMaximumWidth(160)
        legendlocs = ['',#QApplication.translate("ComboBox", "none"),
                      QApplication.translate('ComboBox', 'upper right'),
                      QApplication.translate('ComboBox', 'upper left'),
                      QApplication.translate('ComboBox', 'lower left'),
                      QApplication.translate('ComboBox', 'lower right'),
                      QApplication.translate('ComboBox', 'right'),
                      QApplication.translate('ComboBox', 'center left'),
                      QApplication.translate('ComboBox', 'center right'),
                      QApplication.translate('ComboBox', 'lower center'),
                      QApplication.translate('ComboBox', 'upper center'),
                      QApplication.translate('ComboBox', 'center')]
        self.legendComboBox.addItems(legendlocs)
        self.legendComboBox.setCurrentIndex(self.aw.qmc.legendloc)
        self.legendComboBox.currentIndexChanged.connect(self.changelegendloc)
        resettimelabel = QLabel(QApplication.translate('Label', 'Max'))
        self.resetEdit = QLineEdit()
        self.resetEdit.setMaximumWidth(50)
        self.resetEdit.setMinimumWidth(50)
        self.resetEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        regextime = QRegularExpression(r'^-?[0-9]?[0-9]?[0-9]:[0-5][0-9]$')
        self.resetEdit.setValidator(QRegularExpressionValidator(regextime,self))
        self.resetEdit.setText(stringfromseconds(self.aw.qmc.resetmaxtime))
        self.resetEdit.setToolTip(QApplication.translate('Tooltip', 'Time axis max on start of a recording'))
        # CHARGE min
        chargeminlabel = QLabel(QApplication.translate('Label', 'RECORD') + '   ' + QApplication.translate('Label', 'Min'))
        self.chargeminEdit = QLineEdit()
        self.chargeminEdit.setMaximumWidth(50)
        self.chargeminEdit.setMinimumWidth(50)
        self.chargeminEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.chargeminEdit.setValidator(QRegularExpressionValidator(regextime,self))
        self.chargeminEdit.setText(stringfromseconds(self.aw.qmc.chargemintime))
        self.chargeminEdit.setToolTip(QApplication.translate('Tooltip', 'Time axis min on start of a recording'))

        # fixmaxtime flag
        self.fixmaxtimeFlag = QCheckBox(QApplication.translate('CheckBox', 'Expand'))
        self.fixmaxtimeFlag.setChecked(not self.aw.qmc.fixmaxtime)
        self.fixmaxtimeFlag.setToolTip(QApplication.translate('Tooltip', 'Automatically extend the time axis by 3min on need'))
        # locktimex flag
        self.locktimexFlag = QCheckBox(QApplication.translate('CheckBox', 'Lock'))
        self.locktimexFlag.setChecked(self.aw.qmc.locktimex)
        self.locktimexFlag.stateChanged.connect(self.lockTimexFlagChanged)
        self.locktimexFlag.setToolTip(QApplication.translate('Tooltip', 'Do not set time axis min and max from profile on load'))
        # autotimex flag
        self.autotimexFlag = QCheckBox(QApplication.translate('CheckBox', 'Auto'))
        self.autotimexFlag.setChecked(self.aw.qmc.autotimex)
        self.autotimexFlag.stateChanged.connect(self.autoTimexFlagChanged)
        self.autotimexFlag.setToolTip(QApplication.translate('Tooltip', 'Automatically set time axis min and max from profile CHARGE/DROP events'))
#        self.autoButton = QPushButton(QApplication.translate('Button','Calc'))
#        self.autoButton.setToolTip(QApplication.translate('Tooltip', 'Calc time axis using current auto time axis settings'))
#        self.autoButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
#        self.autoButton.clicked.connect(self.autoAxis)
        # autotimexMode
        self.autotimexModeCombobox = QComboBox()
        if not self.autotimexFlag.isChecked():
            self.autotimexModeCombobox.setEnabled(False)
#            self.autoButton.setEnabled(False)
#        if self.aw.qmc.flagon:
#            self.autoButton.setEnabled(False)
        self.autotimexModeCombobox.setToolTip(QApplication.translate('Tooltip', 'Coverage of auto time axis mode'))
        autotimeModes =   [
                      QApplication.translate('ComboBox', 'Roast'),
                      QApplication.translate('ComboBox', 'BBP+Roast'),
                      QApplication.translate('ComboBox', 'BBP')]
        self.autotimexModeCombobox.addItems(autotimeModes)
        try:
            self.autotimexModeCombobox.setCurrentIndex(self.aw.qmc.autotimexMode)
        except Exception: # pylint: disable=broad-except
            self.autotimexModeCombobox.setCurrentIndex(0)
        self.autotimexModeCombobox.currentIndexChanged.connect(self.changeAutoTimexMode)

        # time axis steps
        timegridlabel = QLabel(QApplication.translate('Label', 'Step'))
        timegridlabel.setToolTip(QApplication.translate('Tooltip', 'Distance of major tick labels'))
        self.xaxislencombobox = QComboBox()
        self.xaxislencombobox.setToolTip(QApplication.translate('Tooltip', 'Distance of major tick labels'))
        timelocs =   [
                      '',
                      QApplication.translate('ComboBox', '1 minute'),
                      QApplication.translate('ComboBox', '2 minutes'),
                      QApplication.translate('ComboBox', '3 minutes'),
                      QApplication.translate('ComboBox', '4 minutes'),
                      QApplication.translate('ComboBox', '5 minutes'),
                      QApplication.translate('ComboBox', '10 minutes'),
                      QApplication.translate('ComboBox', '30 minutes'),
                      QApplication.translate('ComboBox', '1 hour')]
        self.xaxislencombobox.addItems(timelocs)

        self.xaxislencombobox.setMinimumContentsLength(6)
        width = self.xaxislencombobox.minimumSizeHint().width()
        self.xaxislencombobox.setMinimumWidth(width)
        if platform.system() == 'Darwin':
            self.xaxislencombobox.setMaximumWidth(width)
#        self.xaxislencombobox.setMaximumWidth(120)

        self.timeconversion = [0,60,120,180,240,300,600,1800,3600]
        try:
            self.xaxislencombobox.setCurrentIndex(self.timeconversion.index(self.aw.qmc.xgrid))
        except Exception: # pylint: disable=broad-except
            self.xaxislencombobox.setCurrentIndex(0)
        self.xaxislencombobox.currentIndexChanged.connect(self.xaxislenloc)
        self.timeGridCheckBox = QCheckBox(QApplication.translate('CheckBox','Time'))
        self.timeGridCheckBox.setChecked(self.aw.qmc.time_grid)
        self.timeGridCheckBox.setToolTip(QApplication.translate('Tooltip', 'Show time grid'))
        self.timeGridCheckBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.timeGridCheckBox.stateChanged.connect(self.changetimeGridCheckBox)
        self.tempGridCheckBox = QCheckBox(QApplication.translate('CheckBox','Temp'))
        self.tempGridCheckBox.setToolTip(QApplication.translate('Tooltip', 'Show temperature grid'))
        self.tempGridCheckBox.setChecked(self.aw.qmc.temp_grid)
        self.tempGridCheckBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tempGridCheckBox.stateChanged.connect(self.changetempGridCheckBox)
        ygridlabel = QLabel(QApplication.translate('Label', 'Step'))
        ygridlabel.setToolTip(QApplication.translate('Tooltip', 'Distance of major tick labels'))
        self.ygridSpinBox = QSpinBox()
        self.ygridSpinBox.setToolTip(QApplication.translate('Tooltip', 'Distance of major tick labels'))
        self.ygridSpinBox.setRange(0,500)
        self.ygridSpinBox.setSingleStep(5)
        self.ygridSpinBox.setValue(int(self.aw.qmc.ygrid))
        self.ygridSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.ygridSpinBox.editingFinished.connect(self.changeygrid)
        self.ygridSpinBox.setMaximumWidth(60)
        zgridlabel = QLabel(QApplication.translate('Label', 'Step'))
        zgridlabel.setToolTip(QApplication.translate('Tooltip', 'Distance of major tick labels'))
        self.zgridSpinBox = QSpinBox()
        self.zgridSpinBox.setToolTip(QApplication.translate('Tooltip', 'Distance of major tick labels'))
        self.zgridSpinBox.setRange(0,100)
        self.zgridSpinBox.setSingleStep(1)
        self.zgridSpinBox.setValue(int(self.aw.qmc.zgrid))
        self.zgridSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.zgridSpinBox.editingFinished.connect(self.changezgrid)
        self.zgridSpinBox.setMaximumWidth(60)

        self.autodeltaxLabel = QLabel(QApplication.translate('CheckBox', 'Auto'))
        self.autodeltaxETFlag = QCheckBox(deltaLabelUTF8 + QApplication.translate('CheckBox', 'ET'))
        self.autodeltaxETFlag.setChecked(self.aw.qmc.autodeltaxET)
        self.autodeltaxBTFlag = QCheckBox(deltaLabelUTF8 + QApplication.translate('CheckBox', 'BT'))
        self.autodeltaxBTFlag.setChecked(self.aw.qmc.autodeltaxBT)
        self.autodeltaxETFlag.setToolTip(QApplication.translate('Tooltip', 'Automatically set delta axis max from DeltaET'))
        self.autodeltaxBTFlag.setToolTip(QApplication.translate('Tooltip', 'Automatically set delta axis max from DeltaBT'))

        self.autodeltaxETFlag.stateChanged.connect(self.autoDeltaxFlagChanged)
        self.autodeltaxBTFlag.stateChanged.connect(self.autoDeltaxFlagChanged)

#        autoDeltaButton = QPushButton(QApplication.translate('Button','Calc'))
#        autoDeltaButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
#        autoDeltaButton.clicked.connect(self.autoDeltaAxis)

        linestylegridlabel = QLabel(QApplication.translate('Label', 'Style'))
        self.gridstylecombobox = QComboBox()
        gridstyles = [QApplication.translate('ComboBox', 'solid'),
                      QApplication.translate('ComboBox', 'dashed'),
                      QApplication.translate('ComboBox', 'dashed-dot'),
                      QApplication.translate('ComboBox', 'dotted'),
                      #QApplication.translate('ComboBox', 'None') # not needed any longer as the grids can be individually deactivated
                      ]
        self.gridstylecombobox.addItems(gridstyles)
        if self.aw.qmc.gridlinestyle > 3:
            self.aw.qmc.gridlinestyle = 0 # style 'None' is gone
        self.gridstylecombobox.setCurrentIndex(self.aw.qmc.gridlinestyle)
        self.gridstylecombobox.currentIndexChanged.connect(self.changegridstyle)
        gridthicknesslabel = QLabel(QApplication.translate('Label', 'Width'))
        self.gridwidthSpinBox = QSpinBox()
        self.gridwidthSpinBox.setRange(1,5)
        self.gridwidthSpinBox.setValue(int(self.aw.qmc.gridthickness))
        self.gridwidthSpinBox.valueChanged.connect(self.changegridwidth)
        self.gridwidthSpinBox.setMaximumWidth(40)
        self.gridwidthSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        gridalphalabel = QLabel(QApplication.translate('Label', 'Opaqueness'))
        self.gridalphaSpinBox = QSpinBox()
        self.gridalphaSpinBox.setRange(1,10)
        self.gridalphaSpinBox.setValue(int(self.aw.qmc.gridalpha*10))
        self.gridalphaSpinBox.valueChanged.connect(self.changegridalpha)
        self.gridalphaSpinBox.setMaximumWidth(40)
        self.gridalphaSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.updatewindow)
        self.dialogbuttons.rejected.connect(self.restoreState)

        resetButton: Optional['QPushButton'] = self.dialogbuttons.addButton(QDialogButtonBox.StandardButton.RestoreDefaults)
        if resetButton is not None:
            resetButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            resetButton.clicked.connect(self.reset)
            self.setButtonTranslations(resetButton,'Restore Defaults',QApplication.translate('Button','Restore Defaults'))
            resetButton.setToolTip(QApplication.translate('Tooltip', 'Reset axis settings to their defaults'))

        self.loadAxisFromProfile = QCheckBox(QApplication.translate('CheckBox', 'Load from profile'))
        self.loadAxisFromProfile.setChecked(self.aw.qmc.loadaxisfromprofile)
        self.loadAxisFromProfile.setToolTip(QApplication.translate('Tooltip', 'Take axis settings from profile on load'))

        hline = QFrame()
        hline.setFrameShape(QFrame.Shape.HLine)
        hline.setFrameShadow(QFrame.Shadow.Sunken)

        hline2 = QFrame()
        hline2.setFrameShape(QFrame.Shape.HLine)
        hline2.setFrameShadow(QFrame.Shadow.Sunken)

        xlayout1 = QHBoxLayout()
        xlayout1.addWidget(self.autotimexFlag)
        xlayout1.addWidget(self.autotimexModeCombobox)
#        xlayout1.addWidget(self.autoButton)
        xlayout1.addStretch()
        xlayout1.addWidget(self.locktimexFlag)
        xlayout2 = QHBoxLayout()
        xlayout2.addWidget(xlimitLabel_min)
        xlayout2.addWidget(self.xlimitEdit_min)
        xlayout2.addSpacing(10)
        xlayout2.addWidget(xlimitLabel)
        xlayout2.addWidget(self.xlimitEdit)
        xlayout2.addStretch()
        xlayout2.addSpacing(10)
        xlayout2.addWidget(timegridlabel)
        xlayout2.addWidget(self.xaxislencombobox)
        xlayout3 = QHBoxLayout()
        xlayout3.addWidget(chargeminlabel)
        xlayout3.addWidget(self.chargeminEdit)
        xlayout3.addSpacing(7)
        xlayout3.addWidget(resettimelabel)
        xlayout3.addWidget(self.resetEdit)
        xlayout3.addSpacing(7)
        xlayout3.addStretch()
        xlayout3.addWidget(self.fixmaxtimeFlag)
        xlayout = QVBoxLayout()
        xlayout.addLayout(xlayout1)
        xlayout.addLayout(xlayout2)
        xlayout.addWidget(hline)
        xlayout.addLayout(xlayout3)
        ylayout = QGridLayout()
        ylayout.addWidget(ylimitLabel_min,0,0,Qt.AlignmentFlag.AlignRight)
        ylayout.addWidget(self.ylimitEdit_min,0,1)
        ylayout.addWidget(ylimitLabel,0,3,Qt.AlignmentFlag.AlignRight)
        ylayout.addWidget(self.ylimitEdit,0,4)
        ylayout.addWidget(ygridlabel,0,6,Qt.AlignmentFlag.AlignRight)
        ylayout.addWidget(self.ygridSpinBox,0,7)
        ylayout.setColumnMinimumWidth(2,10)
        ylayout.setColumnMinimumWidth(5,10)
        ylayoutHbox = QHBoxLayout()
        ylayoutHbox.addStretch()
        ylayoutHbox.addLayout(ylayout)
        ylayoutHbox.addStretch()
        steplayoutHbox = QHBoxLayout()
        steplayoutHbox.addWidget(step100Label)
        steplayoutHbox.addWidget(self.step100Edit)
        steplayoutHbox.addStretch()
        ylayoutVbox = QVBoxLayout()
        ylayoutVbox.addLayout(ylayoutHbox)
        ylayoutVbox.addWidget(hline)
        ylayoutVbox.addLayout(steplayoutHbox)
        ylayoutVbox.addStretch()
        zlayout1 = QHBoxLayout()
        zlayout1.addWidget(self.autodeltaxLabel)
        zlayout1.addSpacing(5)
        zlayout1.addWidget(self.autodeltaxETFlag)
        zlayout1.addSpacing(5)
        zlayout1.addWidget(self.autodeltaxBTFlag)
        zlayout1.addSpacing(5)
#        zlayout1.addWidget(autoDeltaButton)
        zlayout1.addStretch()
        zlayout = QGridLayout()
        zlayout.addWidget(zlimitLabel_min,0,0,Qt.AlignmentFlag.AlignRight)
        zlayout.addWidget(self.zlimitEdit_min,0,1)
        zlayout.addWidget(zlimitLabel,0,3,Qt.AlignmentFlag.AlignRight)
        zlayout.addWidget(self.zlimitEdit,0,4)
        zlayout.addWidget(zgridlabel,0,6,Qt.AlignmentFlag.AlignRight)
        zlayout.addWidget(self.zgridSpinBox,0,7)
        zlayout.setColumnMinimumWidth(2,10)
        zlayout.setColumnMinimumWidth(5,10)
        zlayoutHbox = QHBoxLayout()
        zlayoutHbox.addStretch()
        zlayoutHbox.addLayout(zlayout)
        zlayoutHbox.addStretch()
        zlayoutVbox = QVBoxLayout()
        zlayoutVbox.addLayout(zlayout1)
        zlayoutVbox.addLayout(zlayoutHbox)
        zlayoutVbox.addStretch()

        legentlayout = QHBoxLayout()
        legentlayout.addStretch()
        legentlayout.addWidget(self.legendComboBox,0,Qt.AlignmentFlag.AlignLeft)
        legentlayout.addStretch()
        graphgridlayout = QGridLayout()
        graphgridlayout.addWidget(linestylegridlabel,1,0,Qt.AlignmentFlag.AlignRight)
        graphgridlayout.addWidget(self.gridstylecombobox,1,1,Qt.AlignmentFlag.AlignLeft)
        graphgridlayout.addWidget(gridthicknesslabel,1,2,Qt.AlignmentFlag.AlignRight)
        graphgridlayout.addWidget(self.gridwidthSpinBox,1,3,Qt.AlignmentFlag.AlignLeft)
        graphgridlayout.addWidget(self.timeGridCheckBox,2,0,Qt.AlignmentFlag.AlignLeft)
        graphgridlayout.addWidget(self.tempGridCheckBox,2,1,Qt.AlignmentFlag.AlignLeft)
        graphgridlayout.addWidget(gridalphalabel,2,2,Qt.AlignmentFlag.AlignRight)
        graphgridlayout.addWidget(self.gridalphaSpinBox,2,3,Qt.AlignmentFlag.AlignLeft)
        xGroupLayout = QGroupBox(QApplication.translate('GroupBox','Time Axis'))
        xGroupLayout.setLayout(xlayout)
        yGroupLayout = QGroupBox(QApplication.translate('GroupBox','Temperature Axis'))
        yGroupLayout.setLayout(ylayoutVbox)
        zGroupLayout = QGroupBox(deltaLabelUTF8 + ' ' + QApplication.translate('GroupBox','Axis'))
        zGroupLayout.setLayout(zlayoutVbox)
        legendLayout = QGroupBox(QApplication.translate('GroupBox','Legend Location'))
        legendLayout.setLayout(legentlayout)
        GridGroupLayout = QGroupBox(QApplication.translate('GroupBox','Grid'))
        GridGroupLayout.setLayout(graphgridlayout)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.loadAxisFromProfile)
        buttonLayout.addSpacing(10)
        buttonLayout.addWidget(self.dialogbuttons)
        mainLayout1 = QVBoxLayout()
        mainLayout1.addWidget(xGroupLayout)
        mainLayout1.addWidget(yGroupLayout)
        mainLayout1.addStretch()
        mainLayout2 = QVBoxLayout()
        mainLayout2.addWidget(legendLayout)
        mainLayout2.addWidget(GridGroupLayout)
        mainLayout2.addWidget(zGroupLayout)
        mainLayout2.addStretch()
        mainHLayout = QHBoxLayout()
        mainHLayout.addLayout(mainLayout1)
        mainHLayout.addLayout(mainLayout2)
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(mainHLayout)
        mainLayout.addStretch()
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
        if platform.system() != 'Windows':
            ok_button: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button is not None:
                ok_button.setFocus()

        if self.aw.qmc.locktimex:
            self.disableXAxisControls()
        else:
            self.enableXAxisControls()

        settings = QSettings()
        if settings.contains('AxisPosition'):
            self.move(settings.value('AxisPosition'))

        mainLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)


    def enableXAxisControls(self):
        self.xlimitEdit.setEnabled(True)
        self.xlimitEdit_min.setEnabled(True)
        self.chargeminEdit.setEnabled(True)
        self.resetEdit.setEnabled(True)
        self.fixmaxtimeFlag.setEnabled(True)

    def disableXAxisControls(self):
        self.xlimitEdit.setEnabled(False)
        self.xlimitEdit_min.setEnabled(False)
        self.chargeminEdit.setEnabled(False)
        self.resetEdit.setEnabled(False)
        self.fixmaxtimeFlag.setEnabled(False)

    def enableAutoControls(self):
        self.autotimexModeCombobox.setEnabled(True)
#        if not self.aw.qmc.flagon:
#            self.autoButton.setEnabled(True)

    def disableAutoControls(self):
        self.autotimexModeCombobox.setEnabled(False)
#        self.autoButton.setEnabled(False)


    @pyqtSlot()
    def step100Changed(self):
        try:
            step100 = self.step100Edit.text().strip()
            if step100 == '':
                self.aw.qmc.step100temp = None
            else:
                self.aw.qmc.step100temp = int(step100)
            self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception: # pylint: disable=broad-except
            pass

    @pyqtSlot()
    def xlimitChanged(self):
        try:
            endedittime_str = str(self.xlimitEdit.text())
            if endedittime_str is not None and endedittime_str != '':
                endeditime = stringtoseconds(endedittime_str)
                if self.aw.qmc.endofx != endeditime:
                    self.autotimexFlag.setChecked(False)
                    self.aw.qmc.autotimex = False
                    self.aw.qmc.endofx = endeditime
                    self.aw.qmc.locktimex_end = endeditime
                    self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception: # pylint: disable=broad-except
            pass

    @pyqtSlot()
    def xlimitMinChanged(self):
        try:
            startedittime_str = str(self.xlimitEdit_min.text())
            if startedittime_str is not None and startedittime_str != '':
                starteditime = stringtoseconds(startedittime_str)
                if starteditime >= 0 and self.aw.qmc.timeindex[0] != -1:
                    self.aw.qmc.startofx = self.aw.qmc.timex[self.aw.qmc.timeindex[0]] + starteditime
                elif starteditime >= 0 and self.aw.qmc.timeindex[0] == -1:
                    self.aw.qmc.startofx = starteditime
                elif starteditime < 0 and self.aw.qmc.timeindex[0] != -1:
                    self.aw.qmc.startofx = self.aw.qmc.timex[self.aw.qmc.timeindex[0]]-abs(starteditime)
                else:
                    self.aw.qmc.startofx = starteditime
                self.aw.qmc.locktimex_start = starteditime
                self.autotimexFlag.setChecked(False)
                self.aw.qmc.autotimex = False
                self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception: # pylint: disable=broad-except
            pass

    @pyqtSlot()
    def ylimitChanged(self):
        try:
            yl = int(str(self.ylimitEdit.text()))
            yl_min = int(str(self.ylimitEdit_min.text()))
            if yl > yl_min:
                if (self.aw.qmc.ylimit != yl) or (self.aw.qmc.ylimit_min != yl_min):
                    self.aw.qmc.ylimit = yl
                    self.aw.qmc.ylimit_min = yl_min
                    self.aw.qmc.redraw(recomputeAllDeltas=False)
            else:
                self.ylimitEdit.setText(str(self.aw.qmc.ylimit))
                self.ylimitEdit_min.setText(str(self.aw.qmc.ylimit_min))
        except Exception: # pylint: disable=broad-except
            self.ylimitEdit.setText(str(self.aw.qmc.ylimit))
            self.ylimitEdit_min.setText(str(self.aw.qmc.ylimit_min))

    @pyqtSlot()
    def zlimitChanged(self):
        try:
            new_value = int(self.zlimitEdit.text().strip())
            if self.aw.qmc.zlimit != new_value:
                self.aw.qmc.autodeltaxET = False
                self.aw.qmc.autodeltaxBT = False
                self.autodeltaxETFlag.blockSignals(True)
                self.autodeltaxBTFlag.blockSignals(True)
                self.autodeltaxETFlag.setChecked(self.aw.qmc.autodeltaxET)
                self.autodeltaxBTFlag.setChecked(self.aw.qmc.autodeltaxBT)
                self.autodeltaxETFlag.blockSignals(False)
                self.autodeltaxBTFlag.blockSignals(False)
                self.aw.qmc.zlimit = new_value
                if self.aw.comparator is not None:
                    self.aw.comparator.redraw()
                else:
                    self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception: # pylint: disable=broad-except
            self.zlimitEdit.setText(str(self.aw.qmc.zlimit))

    @pyqtSlot()
    def zlimitMinChanged(self):
        try:
            self.aw.qmc.zlimit_min = int(self.zlimitEdit_min.text().strip())
            self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception: # pylint: disable=broad-except
            self.zlimitEdit_min.setText(str(self.aw.qmc.zlimit_min))

    @pyqtSlot(int)
    def lockTimexFlagChanged(self,n):
        if n:
            self.autotimexFlag.setChecked(False)
            self.disableXAxisControls()
        else:
            self.enableXAxisControls()

    @pyqtSlot(int)
    def autoDeltaxFlagChanged(self,_):
        self.aw.qmc.autodeltaxET = self.autodeltaxETFlag.isChecked()
        self.aw.qmc.autodeltaxBT = self.autodeltaxBTFlag.isChecked()
        if not self.aw.qmc.flagon and (self.autodeltaxETFlag or self.autodeltaxBTFlag):
            if self.aw.comparator is not None:
                self.aw.comparator.redraw()
                self.zlimitEdit.setText(str(self.aw.qmc.zlimit))
            else:
                self.autoDeltaAxis()

    @pyqtSlot(int)
    def autoTimexFlagChanged(self,n):
        if n:
            self.aw.qmc.autotimex = True
            self.locktimexFlag.setChecked(False)
            self.enableAutoControls()
            self.enableXAxisControls()
            if self.aw.comparator is not None:
                self.aw.comparator.redraw()
            elif not self.aw.qmc.flagon:
                self.autoAxis()
        else:
            self.disableAutoControls()

    @pyqtSlot(bool)
    def autoAxis(self,_=False):
        changed = False
        if self.aw.qmc.backgroundpath and (self.aw.qmc.flagon or len(self.aw.qmc.timex)<2):
            # no foreground profile
            t_min,t_max = self.aw.calcAutoAxisBackground()
            t_min = min(-30,t_min)
        else:
            t_min,t_max = self.aw.calcAutoAxisForeground()
        if self.aw.qmc.timeindex[0] != -1:
            self.xlimitEdit_min.setText(stringfromseconds(t_min - self.aw.qmc.timex[self.aw.qmc.timeindex[0]]))
            self.xlimitEdit.setText(stringfromseconds(t_max - self.aw.qmc.timex[self.aw.qmc.timeindex[0]]))
        else:
            self.xlimitEdit_min.setText(stringfromseconds(t_min))
            self.xlimitEdit.setText(stringfromseconds(t_max))
        self.xlimitEdit_min.repaint()
        self.xlimitEdit.repaint()

        endedittime_str = str(self.xlimitEdit.text())
        if endedittime_str is not None and endedittime_str != '':
            endeditime = stringtoseconds(endedittime_str)
            if self.aw.qmc.endofx != endeditime:
                self.aw.qmc.endofx = endeditime
                self.aw.qmc.locktimex_end = endeditime
                changed = True
        startedittime_str = str(self.xlimitEdit_min.text())
        if startedittime_str is not None and startedittime_str != '':
            starteditime = stringtoseconds(startedittime_str)
            if starteditime >= 0 and self.aw.qmc.timeindex[0] != -1:
                self.aw.qmc.startofx = self.aw.qmc.timex[self.aw.qmc.timeindex[0]] + starteditime
            elif starteditime >= 0 and self.aw.qmc.timeindex[0] == -1:
                self.aw.qmc.startofx = starteditime
            elif starteditime < 0 and self.aw.qmc.timeindex[0] != -1:
                self.aw.qmc.startofx = self.aw.qmc.timex[self.aw.qmc.timeindex[0]]-abs(starteditime)
            else:
                self.aw.qmc.startofx = starteditime
            self.aw.qmc.locktimex_start = starteditime
            changed = True
        if changed:
            self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(bool)
    def autoDeltaAxis(self,_=False):
        changed = False
        autodeltaxET_org = self.aw.qmc.autodeltaxET
        autodeltaxBT_org = self.aw.qmc.autodeltaxBT
        self.aw.qmc.autodeltaxET = self.autodeltaxETFlag.isChecked()
        self.aw.qmc.autodeltaxBT = self.autodeltaxBTFlag.isChecked()
        if self.aw.qmc.backgroundpath and not self.aw.curFile:
            dmax = self.aw.calcAutoDeltaAxisBackground()
        else:
            dmax = self.aw.calcAutoDeltaAxis()
            if self.aw.qmc.backgroundpath:
                dmax_b = self.aw.calcAutoDeltaAxisBackground()
                dmax = max(dmax,dmax_b)
        zlimit_min = int(str(self.zlimitEdit_min.text()))
        if dmax > zlimit_min and dmax+1 != self.aw.qmc.zlimit:
            self.zlimitEdit.setText(str(int(dmax) + 1))
            self.zlimitEdit.repaint()
            changed = True
        self.aw.qmc.autodeltaxET = autodeltaxET_org
        self.aw.qmc.autodeltaxBT = autodeltaxBT_org
        # adjust zgrid
        if self.zgridSpinBox.value() != 0 and (self.autodeltaxETFlag.isChecked() or self.autodeltaxBTFlag.isChecked()):
            zlimit_max = int(str(self.zlimitEdit.text()))
            d = zlimit_max - zlimit_min
            steps = int(round(d/5))
            if steps > 50:
                steps = int(round(steps/10))*10
            elif steps > 10:
                steps = int(round(steps/5))*5
            elif steps > 5:
                steps = 5
            else:
                steps = int(round(steps/2))*2
            auto_grid = max(2,steps)
            self.zgridSpinBox.setValue(int(auto_grid))
            if auto_grid != self.aw.qmc.zgrid:
                self.aw.qmc.zgrid = auto_grid
                changed = True
        self.aw.qmc.zlimit_min = int(self.zlimitEdit_min.text().strip())
        self.aw.qmc.zlimit = int(self.zlimitEdit.text().strip())
        if changed:
            self.aw.qmc.redraw(recomputeAllDeltas=False)

#    def changexrotation(self):
#        self.aw.qmc.xrotation = self.xrotationSpinBox.value()
#        self.xrotationSpinBox.setDisabled(True)
#        self.aw.qmc.xaxistosm(redraw=False)
#        self.aw.qmc.redraw(recomputeAllDeltas=False)
#        self.xrotationSpinBox.setDisabled(False)
#        self.xrotationSpinBox.setFocus()

    @pyqtSlot(int)
    def changegridalpha(self,_):
        self.aw.qmc.gridalpha = self.gridalphaSpinBox.value()/10.
        self.gridalphaSpinBox.setDisabled(True)
        self.aw.qmc.redraw(recomputeAllDeltas=False)
        self.gridalphaSpinBox.setDisabled(False)
        self.gridalphaSpinBox.setFocus()

    @pyqtSlot(int)
    def changegridwidth(self,_):
        self.aw.qmc.gridthickness = self.gridwidthSpinBox.value()
        self.gridwidthSpinBox.setDisabled(True)
        self.aw.qmc.redraw(recomputeAllDeltas=False)
        self.gridwidthSpinBox.setDisabled(False)
        self.gridwidthSpinBox.setFocus()

    @pyqtSlot(int)
    def changetimeGridCheckBox(self,_):
        self.aw.qmc.time_grid = not self.aw.qmc.time_grid
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def changetempGridCheckBox(self,_):
        self.aw.qmc.temp_grid = not self.aw.qmc.temp_grid
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def changegridstyle(self,_):
        self.aw.qmc.gridlinestyle = self.gridstylecombobox.currentIndex()
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def changelegendloc(self,_):
        self.aw.qmc.legendloc = self.legendComboBox.currentIndex()
        if self.aw.comparator is not None:
            self.aw.comparator.legend = None
            self.aw.comparator.redraw()
        else:
            self.aw.qmc.legend = None
            self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def changeAutoTimexMode(self,_):
        self.aw.qmc.autotimexMode = self.autotimexModeCombobox.currentIndex()
        if self.aw.comparator is not None:
            self.aw.comparator.modeComboBox.setCurrentIndex(self.aw.qmc.autotimexMode)
        elif not self.aw.qmc.flagon:
            self.autoAxis()

    @pyqtSlot(int)
    def xaxislenloc(self,_):
        self.aw.qmc.xgrid = self.timeconversion[self.xaxislencombobox.currentIndex()]
        self.aw.qmc.xaxistosm(redraw=False)
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot()
    def changeygrid(self):
        self.aw.qmc.ygrid = self.ygridSpinBox.value()
#        self.ygridSpinBox.setDisabled(True)
        self.aw.qmc.redraw(recomputeAllDeltas=False)
#        self.ygridSpinBox.setDisabled(False)
#        self.ygridSpinBox.setFocus()

    @pyqtSlot()
    def changezgrid(self):
        self.aw.qmc.zgrid = self.zgridSpinBox.value()
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    # exit dialog with OK
    @pyqtSlot()
    def updatewindow(self):
        limits_changed = False
        # trigger auto limits on leaving the dialog if active
        if not self.aw.qmc.flagon and self.autotimexFlag.isChecked():
            self.autoAxis()
        if not self.aw.qmc.flagon and (self.autodeltaxETFlag.isChecked() or self.autodeltaxBTFlag.isChecked()):
            self.autoDeltaAxis()
        #
        self.aw.qmc.loadaxisfromprofile = self.loadAxisFromProfile.isChecked()
        try:
            yl = int(str(self.ylimitEdit.text()))
            yl_min = int(str(self.ylimitEdit_min.text()))
            if yl > yl_min:
                if (self.aw.qmc.ylimit != yl) or (self.aw.qmc.ylimit_min != yl_min):
                    limits_changed = True
                self.aw.qmc.ylimit = yl
                self.aw.qmc.ylimit_min = yl_min
        except Exception: # pylint: disable=broad-except
            pass
        try:
            zl = int(str(self.zlimitEdit.text()))
            zl_min = int(str(self.zlimitEdit_min.text()))
            if (self.aw.qmc.zlimit != zl) or (self.aw.qmc.zlimit_min != zl_min):
                limits_changed = True
            if zl > zl_min:
                self.aw.qmc.zlimit = zl
                self.aw.qmc.zlimit_min = zl_min
        except Exception: # pylint: disable=broad-except
            pass

        if limits_changed and self.aw.qmc.crossmarker:
            # switch crosslines off and on again to adjust for changed axis limits
            self.aw.qmc.togglecrosslines()
            self.aw.qmc.togglecrosslines()


        endedittime_str = str(self.xlimitEdit.text())
        if endedittime_str is not None and endedittime_str != '':
            endeditime = stringtoseconds(endedittime_str)
            self.aw.qmc.endofx = endeditime
            self.aw.qmc.locktimex_end = endeditime
        else:
            self.aw.qmc.endofx = self.aw.qmc.endofx_default
            self.aw.qmc.locktimex_end = self.aw.qmc.endofx_default

        startedittime_str = str(self.xlimitEdit_min.text())
        if startedittime_str is not None and startedittime_str != '':
            starteditime = stringtoseconds(startedittime_str)
            if starteditime >= 0 and self.aw.qmc.timeindex[0] != -1:
                self.aw.qmc.startofx = self.aw.qmc.timex[self.aw.qmc.timeindex[0]] + starteditime
            elif starteditime >= 0 and self.aw.qmc.timeindex[0] == -1:
                self.aw.qmc.startofx = starteditime
            elif starteditime < 0 and self.aw.qmc.timeindex[0] != -1:
                self.aw.qmc.startofx = self.aw.qmc.timex[self.aw.qmc.timeindex[0]]-abs(starteditime)
            else:
                self.aw.qmc.startofx = starteditime
            self.aw.qmc.locktimex_start = starteditime
        else:
            self.aw.qmc.startofx = self.aw.qmc.startofx_default
            self.aw.qmc.locktimex_start = self.aw.qmc.startofx_default

        try:
            step100 = self.step100Edit.text().strip()
            if step100 == '':
                self.aw.qmc.step100temp = None
            else:
                self.aw.qmc.step100temp = int(step100)
        except Exception: # pylint: disable=broad-except
            pass

        resettime = stringtoseconds(str(self.resetEdit.text()))
        if resettime > 0:
            self.aw.qmc.resetmaxtime = resettime

        chargetime = stringtoseconds(str(self.chargeminEdit.text()))
        if chargetime <= 0:
            self.aw.qmc.chargemintime = chargetime

        self.aw.qmc.fixmaxtime = not self.fixmaxtimeFlag.isChecked()
        self.aw.qmc.locktimex = self.locktimexFlag.isChecked()
        self.aw.qmc.autotimex = self.autotimexFlag.isChecked()
        self.aw.qmc.autodeltaxET = self.autodeltaxETFlag.isChecked()
        self.aw.qmc.autodeltaxBT = self.autodeltaxBTFlag.isChecked()
        if not self.aw.qmc.flagon:
            self.aw.autoAdjustAxis(background=(bool(self.aw.qmc.backgroundpath) and not len(self.aw.qmc.timex) > 3)) # align background if no foreground
        self.aw.qmc.redraw(recomputeAllDeltas=False)
        try:
            self.aw.ntb.update() # reset the MPL navigation history
        except Exception: # pylint: disable=broad-except
            pass
        string = QApplication.translate('Message','xlimit = ({2},{3}) ylimit = ({0},{1}) zlimit = ({4},{5})').format(str(self.ylimitEdit_min.text()),str(self.ylimitEdit.text()),str(self.xlimitEdit_min.text()),str(self.xlimitEdit.text()),str(self.zlimitEdit_min.text()),str(self.zlimitEdit.text()))
        self.aw.sendmessage(string)
        self.close()

    # on Cancel
    def restoreState(self):
        self.aw.qmc.time_grid = self.time_grid_org
        self.aw.qmc.temp_grid = self.temp_grid_org
        self.aw.qmc.gridlinestyle = self.gridlinestyle_org
        self.aw.qmc.gridthickness = self.gridthickness_org
        self.aw.qmc.gridalpha = self.gridalpha_org
        self.aw.qmc.step100temp = self.step100temp_org
        self.aw.qmc.xgrid = self.xgrid_org
        self.aw.qmc.ygrid = self.ygrid_org
        self.aw.qmc.zgrid = self.grid_org
        self.aw.qmc.zlimit = self.zlimit_org
        self.aw.qmc.zlimit_min = self.zlimit_min_org
        self.aw.qmc.legendloc = self.legendloc_org
        self.aw.qmc.resetmaxtime = self.resetmaxtime_org
        self.aw.qmc.chargemintime = self.chargemintime_org
        self.aw.qmc.fixmaxtime = self.fixmaxtime_org
        self.aw.qmc.locktimex = self.locktimex_org
        self.aw.qmc.autotimex = self.autotimex_org
        self.aw.qmc.autotimexMode = self.autotimexMode_org
        self.aw.qmc.autodeltaxET = self.autodeltaxET_org
        self.aw.qmc.autodeltaxBT = self.autodeltaxBT_org
        self.aw.qmc.loadaxisfromprofile = self.loadaxisfromprofile_org
        self.aw.qmc.startofx = self.startofx_org
        self.aw.qmc.endofx = self.endofx_org
        self.aw.qmc.locktimex_start = self.locktimex_start
        self.aw.qmc.locktimex_end = self.locktimex_end_org
        self.aw.qmc.ylimit = self.ylimit_org
        self.aw.qmc.ylimit_min = self.ylimit_min_org
        # redraw and close dialog
        self.aw.qmc.redraw(recomputeAllDeltas=False)
        self.close()

    @pyqtSlot('QCloseEvent')
    def closeEvent(self,_):
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue('AxisPosition',self.frameGeometry().topLeft())

    @pyqtSlot(bool)
    def reset(self,_):
        self.locktimexFlag.setChecked(False)
        self.autotimexFlag.setChecked(True)
        self.autotimexModeCombobox.setCurrentIndex(0)
        self.chargeminEdit.setText('-00:30')
        self.resetEdit.setText('10:00')
        self.fixmaxtimeFlag.setChecked(True)
        self.autodeltaxETFlag.setChecked(False)
        self.autodeltaxBTFlag.setChecked(False)
        self.step100Edit.setText('')
        self.loadAxisFromProfile.setChecked(False)
        self.gridstylecombobox.setCurrentIndex(0)
        self.gridwidthSpinBox.setValue(1)
        self.gridalphaSpinBox.setValue(2)
        self.timeGridCheckBox.setChecked(False)
        self.tempGridCheckBox.setChecked(False)
        if len(self.aw.qmc.timex) > 1:
            self.xlimitEdit.setText(stringfromseconds(self.aw.qmc.timex[-1]))
        else:
            self.xlimitEdit.setText(stringfromseconds(self.aw.qmc.endofx_default))
        self.xlimitEdit_min.setText(stringfromseconds(self.aw.qmc.startofx_default))

        try:
            self.xaxislencombobox.setCurrentIndex(self.timeconversion.index(self.aw.qmc.xgrid_default))
        except Exception: # pylint: disable=broad-except
            self.xaxislencombobox.setCurrentIndex(2)
        if self.aw.qmc.mode == 'F':
            self.ygridSpinBox.setValue(int(self.aw.qmc.ygrid_F_default))
            self.aw.qmc.ygrid = self.aw.qmc.ygrid_F_default
            self.ylimitEdit.setText(str(self.aw.qmc.ylimit_F_default))
            self.ylimitEdit_min.setText(str(self.aw.qmc.ylimit_min_F_default))
            self.zlimitEdit.setText(str(self.aw.qmc.zlimit_F_default))
            self.zlimitEdit_min.setText(str(self.aw.qmc.zlimit_min_F_default))
            self.zgridSpinBox.setValue(int(self.aw.qmc.zgrid_F_default))
        else:
            self.ygridSpinBox.setValue(int(self.aw.qmc.ygrid_C_default))
            self.aw.qmc.ygrid = self.aw.qmc.ygrid_C_default
            self.ylimitEdit.setText(str(self.aw.qmc.ylimit_C_default))
            self.ylimitEdit_min.setText(str(self.aw.qmc.ylimit_min_C_default))
            self.zlimitEdit.setText(str(self.aw.qmc.zlimit_C_default))
            self.zlimitEdit_min.setText(str(self.aw.qmc.zlimit_min_C_default))
            self.zgridSpinBox.setValue(int(self.aw.qmc.zgrid_C_default))
        if self.aw.comparator is not None:
            self.aw.comparator.redraw()
        else:
            self.aw.qmc.redraw(recomputeAllDeltas=False)
