#
# ABOUT
# Artisan Device Configuration Dialog

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

import sys
import time as libtime
import re
import platform
import logging
from PIL import ImageColor
from typing import Final, Optional, List, Tuple, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QAbstractItemView # pylint: disable=unused-import

from artisanlib.util import (deltaLabelUTF8, setDeviceDebugLogLevel, argb_colorname2rgba_colorname, rgba_colorname2argb_colorname,
    toInt, weight_units, convertWeight, render_weight)
from artisanlib.dialogs import ArtisanResizeablDialog, tareDlg

from artisanlib.widgets import MyContentLimitedQComboBox, MyQComboBox, MyQDoubleSpinBox, wait_cursor
from artisanlib.scale import SUPPORTED_SCALES, ScaleSpecs


_log: Final[logging.Logger] = logging.getLogger(__name__)

try:
    from PyQt6.QtCore import (Qt, pyqtSlot, QSettings, QTimer, QRegularExpression, QSignalBlocker) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import (QStandardItemModel, QStandardItem, QColor, QIntValidator, QRegularExpressionValidator, QPixmap) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QWidget, QCheckBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,  # @UnusedImport @Reimport  @UnresolvedImport
                                 QPushButton, QSpinBox, QTabWidget, QComboBox, QDialogButtonBox, QGridLayout, # @UnusedImport @Reimport  @UnresolvedImport
                                 QGroupBox, QRadioButton, QButtonGroup, # @UnusedImport @Reimport  @UnresolvedImport
                                 QTableWidget, QMessageBox, QHeaderView, QTableWidgetItem, QSizePolicy) # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import (Qt, pyqtSlot, QSettings, QTimer, QRegularExpression, QSignalBlocker) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import (QStandardItemModel, QStandardItem, QColor, QIntValidator, QRegularExpressionValidator, QPixmap) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QWidget, QCheckBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
                                 QPushButton, QSpinBox, QTabWidget, QComboBox, QDialogButtonBox, QGridLayout, # @UnusedImport @Reimport  @UnresolvedImport
                                 QGroupBox, QRadioButton, QButtonGroup, # @UnusedImport @Reimport  @UnresolvedImport
                                 QTableWidget, QMessageBox, QHeaderView, QTableWidgetItem, QSizePolicy) # @UnusedImport @Reimport  @UnresolvedImport


class DeviceAssignmentDlg(ArtisanResizeablDialog):
    def __init__(self, parent:QWidget, aw:'ApplicationWindow', activeTab:int = 0) -> None:
        super().__init__(parent,aw)
        self.activeTab = activeTab
        self.setWindowTitle(QApplication.translate('Form Caption','Device Assignment'))
        self.setModal(True)

        self.helpdialog = None

        self.org_phidgetRemoteFlag = self.aw.qmc.phidgetRemoteFlag
        self.org_yoctoRemoteFlag = self.aw.qmc.yoctoRemoteFlag
        self.org_santokerSerial = self.aw.santokerSerial
        self.org_santokerBLE = self.aw.santokerBLE
        self.org_kaleidoSerial = self.aw.kaleidoSerial

        self.org_scale1_model = self.aw.scale1_model
        self.org_scale1_name = self.aw.scale1_name
        self.org_scale1_id = self.aw.scale1_id
        self.org_container1_idx = self.aw.container1_idx
        self.org_scale2_model = self.aw.scale2_model
        self.org_scale2_name = self.aw.scale2_name
        self.org_scale2_id = self.aw.scale2_id
        self.org_container2_idx = self.aw.container2_idx

        ################ TAB 1   WIDGETS
        #ETcurve
        self.ETcurve = QCheckBox(QApplication.translate('CheckBox', 'ET'))
        self.ETcurve.setChecked(self.aw.qmc.ETcurve)
        #BTcurve
        self.BTcurve = QCheckBox(QApplication.translate('CheckBox', 'BT'))
        self.BTcurve.setChecked(self.aw.qmc.BTcurve)
        #ETlcd
        self.ETlcd = QCheckBox(QApplication.translate('CheckBox', 'ET'))
        self.ETlcd.setChecked(self.aw.qmc.ETlcd)
        #BTlcd
        self.BTlcd = QCheckBox(QApplication.translate('CheckBox', 'BT'))
        self.BTlcd.setChecked(self.aw.qmc.BTlcd)
        #swaplcd
        self.swaplcds = QCheckBox(QApplication.translate('CheckBox', 'Swap'))
        self.swaplcds.setChecked(self.aw.qmc.swaplcds)
        self.curveHBox = QHBoxLayout()
        self.curveHBox.setContentsMargins(10,5,10,5)
        self.curveHBox.setSpacing(5)
        self.curveHBox.addWidget(self.ETcurve)
        self.curveHBox.addSpacing(10)
        self.curveHBox.addWidget(self.BTcurve)
        self.curveHBox.addStretch()
        self.curves = QGroupBox(QApplication.translate('GroupBox','Curves'))
        self.curves.setLayout(self.curveHBox)
        self.lcdHBox = QHBoxLayout()
        self.lcdHBox.setContentsMargins(0,5,0,5)
        self.lcdHBox.setSpacing(5)
        self.lcdHBox.addWidget(self.ETlcd)
        self.lcdHBox.addSpacing(10)
        self.lcdHBox.addWidget(self.BTlcd)
        self.lcdHBox.addSpacing(15)
        self.lcdHBox.addWidget(self.swaplcds)
        self.lcds = QGroupBox(QApplication.translate('GroupBox','LCDs'))
        self.lcds.setLayout(self.lcdHBox)

        self.deviceLoggingFlag = QCheckBox(QApplication.translate('Label', 'Logging'))
        self.deviceLoggingFlag.setChecked(self.aw.qmc.device_logging)

        self.controlButtonFlag = QCheckBox(QApplication.translate('Label', 'Control'))
        self.controlButtonFlag.setChecked(self.aw.qmc.Controlbuttonflag)
        self.controlButtonFlag.stateChanged.connect(self.showControlbuttonToggle)

        self.nonpidButton = QRadioButton(QApplication.translate('Radio Button','Meter'))
        self.pidButton = QRadioButton(QApplication.translate('Radio Button','PID'))
        self.arduinoButton = QRadioButton(QApplication.translate('Radio Button','TC4'))
        self.programButton = QRadioButton(QApplication.translate('Radio Button','Prog'))
        #As a main device, don't show the devices that start with a "+"
        # devices with a first letter "+" are extra devices an depend on another device
        # each device provides 2 curves
        #don't show devices with a "-". Devices with a - at front are either a pid, arduino, or an external program
        dev = self.aw.qmc.devices[:]             #deep copy
        limit = len(dev)
        for _ in range(limit):
            for i, _ in enumerate(dev):
                if dev[i][0] in {'+', '-'}:
                    dev.pop(i)              #note: pop() makes the list smaller that's why there are 2 FOR statements
                    break
        self.sorted_devices = sorted(dev)
        self.devicetypeComboBox = MyContentLimitedQComboBox()

##        self.devicetypeComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
##        self.devicetypeComboBox.view().setTextElideMode(Qt.TextElideMode.ElideNone)
#        # HACK: only needed for the macintosh UI on Qt 5.12 onwords; without long items get cut in the popup
#        #  note the -7 as the width of the popup is too large if given the correct maximum characters
##        self.devicetypeComboBox.setMinimumContentsLength(max(22,len(max(dev, key=len)) - 7)) # expects # characters, but is to wide
# the following "hack" helped on PyQt5, but seems not to be needed on PyQt6 any longer
#        self.devicetypeComboBox.setSizePolicy(QSizePolicy.Policy.Expanding,self.devicetypeComboBox.sizePolicy().verticalPolicy())

        self.devicetypeComboBox.addItems(self.sorted_devices)
        self.programedit = QLineEdit(self.aw.ser.externalprogram)
        self.outprogramedit = QLineEdit(self.aw.ser.externaloutprogram)
        self.outprogramFlag = QCheckBox(QApplication.translate('CheckBox', 'Output'))
        self.outprogramFlag.setChecked(self.aw.ser.externaloutprogramFlag)
        self.outprogramFlag.stateChanged.connect(self.changeOutprogramFlag)         #toggle
        selectprogrambutton =  QPushButton(QApplication.translate('Button','Select'))
        selectprogrambutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        selectprogrambutton.clicked.connect(self.loadprogramname)

        # hack to access the Qt automatic translation of the RestoreDefaults button
        db_help = QDialogButtonBox(QDialogButtonBox.StandardButton.Help)
        help_button = db_help.button(QDialogButtonBox.StandardButton.Help)
        if help_button is not None:
            help_text_translated = help_button.text()
        else:
            help_text_translated = QApplication.translate('Button','Help')
        helpprogrambutton =  QPushButton(help_text_translated)
        self.setButtonTranslations(helpprogrambutton,'Help',QApplication.translate('Button','Help'))
        helpprogrambutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        helpprogrambutton.clicked.connect(self.showhelpprogram)
        selectoutprogrambutton =  QPushButton(QApplication.translate('Button','Select'))
        selectoutprogrambutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        selectoutprogrambutton.clicked.connect(self.loadoutprogramname)
        ###################################################
        # PID
        controllabel =QLabel(QApplication.translate('Label', 'Control ET'))
        # 0 = FujiPXG, 1 = FujiPXR3, 2 = DTA, 3 = not used, 4 = PXF
        supported_ET_pids = [('Fuji PXF', 4), ('Fuji PXG', 0), ('Fuji PXR', 1), ('Delta DTA', 2)]
        self.controlpidtypeComboBox = QComboBox()
        self.controlpidtypeComboBox.addItems([item[0] for item in supported_ET_pids])
        cp = self.aw.ser.controlETpid[0]
        self.controlpidtypeComboBox.setCurrentIndex([y[1] for y in supported_ET_pids].index(cp))
        btlabel =QLabel(QApplication.translate('Label', 'Read BT'))
        supported_BT_pids = [('', 2), ('Fuji PXF', 4), ('Fuji PXG', 0), ('Fuji PXR', 1), ('Delta DTA', 3)]
        self.btpidtypeComboBox = QComboBox()
        self.btpidtypeComboBox.addItems([item[0] for item in supported_BT_pids])
        self.btpidtypeComboBox.setCurrentIndex([y[1] for y in supported_BT_pids].index(self.aw.ser.readBTpid[0])) #pid type is index 0
        label1 = QLabel(QApplication.translate('Label', 'Type'))
        label2 = QLabel(QApplication.translate('Label', 'RS485 Unit ID'))
        #rs485 possible unit IDs (1-32); unit 0 is client (computer)
        unitids = list(map(str,list(range(1,33))))
        self.controlpidunitidComboBox = QComboBox()
        self.controlpidunitidComboBox.addItems(unitids)
        self.btpidunitidComboBox = QComboBox()
        self.btpidunitidComboBox.addItems(unitids)
        # index 1 = unitID of the rs485 network
        self.controlpidunitidComboBox.setCurrentIndex(unitids.index(str(self.aw.ser.controlETpid[1])))
        self.btpidunitidComboBox.setCurrentIndex(unitids.index(str(self.aw.ser.readBTpid[1])))
        #Show Fuji PID SV/% LCDs
        self.showFujiLCDs = QCheckBox(QApplication.translate('CheckBox', 'PID Duty/Power LCDs'))
        self.showFujiLCDs.setChecked(self.aw.ser.showFujiLCDs)
        #Reuse Modbus port
        self.useModbusPort = QCheckBox(QApplication.translate('CheckBox', 'Modbus Port'))
        self.useModbusPort.setChecked(self.aw.ser.useModbusPort)
        ####################################################
        #Arduino TC4 channel config
        arduinoChannels = ['None','1','2','3','4']
        arduinoETLabel =QLabel(QApplication.translate('Label', 'ET Channel'))
        self.arduinoETComboBox = QComboBox()
        self.arduinoETComboBox.addItems(arduinoChannels)
        arduinoBTLabel =QLabel(QApplication.translate('Label', 'BT Channel'))
        self.arduinoBTComboBox = QComboBox()
        self.arduinoBTComboBox.addItems(arduinoChannels)
        #check previous settings for radio button
        if self.aw.qmc.device in {0, 26}:   #if Fuji pid or Delta DTA pid
            self.pidButton.setChecked(True)
        elif self.aw.qmc.device == 19:                       #if arduino
            self.arduinoButton.setChecked(True)
        elif self.aw.qmc.device == 27:                       #if program
            self.programButton.setChecked(True)
        else:
            self.nonpidButton.setChecked(True)          #else
            selected_device_index = 0
            try:
                selected_device_index = self.sorted_devices.index(self.aw.qmc.devices[self.aw.qmc.device - 1])
            except Exception: # pylint: disable=broad-except
                pass
            self.devicetypeComboBox.setCurrentIndex(selected_device_index)
        try:
            self.arduinoETComboBox.setCurrentIndex(arduinoChannels.index(self.aw.ser.arduinoETChannel))
        except Exception: # pylint: disable=broad-except
            pass
        try:
            self.arduinoBTComboBox.setCurrentIndex(arduinoChannels.index(self.aw.ser.arduinoBTChannel))
        except Exception: # pylint: disable=broad-except
            pass
        arduinoATLabel =QLabel(QApplication.translate('Label', 'AT Channel'))

        arduinoTemperatures = ['None','T1','T2','T3','T4','T5','T6']
        self.arduinoATComboBox = QComboBox()
        self.arduinoATComboBox.addItems(arduinoTemperatures)
        self.arduinoATComboBox.setCurrentIndex(arduinoTemperatures.index(self.aw.ser.arduinoATChannel))
        self.showControlButton = QCheckBox(QApplication.translate('CheckBox', 'PID Firmware'))
        self.showControlButton.setChecked(self.aw.qmc.PIDbuttonflag)
        self.showControlButton.stateChanged.connect(self.PIDfirmwareToggle)
        FILTLabel =QLabel(QApplication.translate('Label', 'Filter'))
        self.FILTspinBoxes = []
        for i in range(4):
            spinBox = QSpinBox()
            spinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
            spinBox.setRange(0,99)
            spinBox.setSingleStep(5)
            spinBox.setSuffix(' %')
            spinBox.setValue(int(self.aw.ser.ArduinoFILT[i]))
            self.FILTspinBoxes.append(spinBox)
        ####################################################

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.okEvent)
        self.dialogbuttons.rejected.connect(self.cancelEvent)

        labelETadvanced = QLabel(QApplication.translate('Label', 'ET Y(x)'))
        labelBTadvanced = QLabel(QApplication.translate('Label', 'BT Y(x)'))
        self.ETfunctionedit = QLineEdit(str(self.aw.qmc.ETfunction))
        self.BTfunctionedit = QLineEdit(str(self.aw.qmc.BTfunction))
        symbolicHelpButton = QPushButton(help_text_translated)
        self.setButtonTranslations(symbolicHelpButton,'Help',QApplication.translate('Button','Help'))
        symbolicHelpButton.setMaximumSize(symbolicHelpButton.sizeHint())
        symbolicHelpButton.setMinimumSize(symbolicHelpButton.minimumSizeHint())
        symbolicHelpButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        symbolicHelpButton.clicked.connect(self.showSymbolicHelp)
        ##########################    TAB 2  WIDGETS   "EXTRA DEVICES"
        #table for showing data
        self.devicetable = QTableWidget()
        self.devicetable.setTabKeyNavigation(True)
        self.copydeviceTableButton = QPushButton(QApplication.translate('Button', 'Copy Table'))
        self.copydeviceTableButton.setToolTip(QApplication.translate('Tooltip','Copy table to clipboard, OPTION or ALT click for tabular text'))
        self.copydeviceTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.copydeviceTableButton.clicked.connect(self.copyDeviceTabletoClipboard)
        self.addButton = QPushButton(QApplication.translate('Button','Add'))
        self.addButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.addButton.setMinimumWidth(100)
        #self.addButton.setMaximumWidth(100)
        self.addButton.clicked.connect(self.adddevice)
        # hack to access the Qt automatic translation of the RestoreDefaults button
        db_reset = QDialogButtonBox(QDialogButtonBox.StandardButton.Reset)
        db_reset_button = db_reset.button(QDialogButtonBox.StandardButton.Reset)
        if db_reset_button is not None:
            reset_text_translated = db_reset_button.text()
        else:
            reset_text_translated = QApplication.translate('Button','Reset')
        resetButton = QPushButton(reset_text_translated)
        self.setButtonTranslations(resetButton,'Reset',QApplication.translate('Button','Reset'))
        resetButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        resetButton.setMinimumWidth(100)
        resetButton.clicked.connect(self.resetextradevices)
        extradevHelpButton = QPushButton(help_text_translated)
        self.setButtonTranslations(extradevHelpButton,'Help',QApplication.translate('Button','Help'))
        extradevHelpButton.setMinimumWidth(100)
        extradevHelpButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        extradevHelpButton.clicked.connect(self.showExtradevHelp)
        self.delButton = QPushButton(QApplication.translate('Button','Delete'))
        self.delButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.delButton.setMinimumWidth(100)
        #self.delButton.setMaximumWidth(100)
        self.delButton.clicked.connect(self.deldevice)
        self.recalcButton = QPushButton(QApplication.translate('Button','Update Profile'))
        self.recalcButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.recalcButton.setMinimumWidth(100)
        self.recalcButton.setToolTip(QApplication.translate('Tooltip','Recaclulates all Virtual Devices and updates their values in the profile'))
        self.recalcButton.clicked.connect(self.updateVirtualdevicesinprofile_clicked)
        self.enableDisableAddDeleteButtons()
        ##########     LAYOUTS
        # create Phidget box
        phidgetProbeTypeItems = ['K', 'J', 'E', 'T']
        phidgetBox1048 = QGridLayout()
        self.asyncCheckBoxes1048 = []
        self.changeTriggerCombos1048 = []
        self.probeTypeCombos = []
        for i in range(1,5):
            changeTriggersCombo = QComboBox()
            changeTriggersCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            model = cast(QStandardItemModel, changeTriggersCombo.model())
            changeTriggerItems = self.createItems(self.aw.qmc.phidget1048_changeTriggersStrings)
            for item in changeTriggerItems:
                model.appendRow(item)
            try:
                changeTriggersCombo.setCurrentIndex(self.aw.qmc.phidget1048_changeTriggersValues.index(self.aw.qmc.phidget1048_changeTriggers[i-1]))
            except Exception: # pylint: disable=broad-except
                pass

            changeTriggersCombo.setMinimumContentsLength(1)
            changeTriggersCombo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents) # AdjustToMinimumContentsLengthWithIcon
            changeTriggersCombo.setEnabled(bool(self.aw.qmc.phidget1048_async[i-1]))
            width = changeTriggersCombo.minimumSizeHint().width()
            changeTriggersCombo.setMinimumWidth(width)
            if platform.system() == 'Darwin':
                changeTriggersCombo.setMaximumWidth(width)

            self.changeTriggerCombos1048.append(changeTriggersCombo)
            phidgetBox1048.addWidget(changeTriggersCombo,3,i)
            asyncFlag = QCheckBox()
            self.asyncCheckBoxes1048.append(asyncFlag)
            asyncFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            asyncFlag.setChecked(True)
            phidgetBox1048.addWidget(asyncFlag,2,i)
            asyncFlag.stateChanged.connect(self.asyncFlagStateChanged1048)
            asyncFlag.setChecked(self.aw.qmc.phidget1048_async[i-1])
            probeTypeCombo = QComboBox()
            probeTypeCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            model = cast(QStandardItemModel, probeTypeCombo.model())
            probeTypeItems = self.createItems(phidgetProbeTypeItems)
            for item in probeTypeItems:
                model.appendRow(item)
            try:
                probeTypeCombo.setCurrentIndex(self.aw.qmc.phidget1048_types[i-1]-1)
            except Exception: # pylint: disable=broad-except
                pass

            probeTypeCombo.setMinimumContentsLength(1)
            probeTypeCombo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents) # AdjustToMinimumContentsLengthWithIcon
            width = probeTypeCombo.minimumSizeHint().width()
            probeTypeCombo.setMinimumWidth(width)
            if platform.system() == 'Darwin':
                probeTypeCombo.setMaximumWidth(width)

            self.probeTypeCombos.append(probeTypeCombo)
            phidgetBox1048.addWidget(probeTypeCombo,1,i)
            rowLabel = QLabel(str(i-1))
            phidgetBox1048.addWidget(rowLabel,0,i)

        self.dataRateCombo1048 = QComboBox()
        self.dataRateCombo1048.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = cast(QStandardItemModel, self.dataRateCombo1048.model())
        dataRateItems = self.createItems(self.aw.qmc.phidget_dataRatesStrings)
        for item in dataRateItems:
            model.appendRow(item)
        try:
            self.dataRateCombo1048.setCurrentIndex(self.aw.qmc.phidget_dataRatesValues.index(self.aw.qmc.phidget1048_dataRate))
        except Exception: # pylint: disable=broad-except
            pass
        self.dataRateCombo1048.setMinimumContentsLength(5)
        self.dataRateCombo1048.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents) # AdjustToContents
        width = self.dataRateCombo1048.minimumSizeHint().width()
        self.dataRateCombo1048.setMinimumWidth(width)
        if platform.system() == 'Darwin':
            self.dataRateCombo1048.setMaximumWidth(width)

        phidgetBox1048.addWidget(self.dataRateCombo1048,4,1,1,2)
        phidgetBox1048.setSpacing(2)

        typeLabel = QLabel(QApplication.translate('Label','Type'))
        asyncLabel = QLabel(QApplication.translate('Label','Async'))
        changeTriggerLabel = QLabel(QApplication.translate('Label','Change'))
        rateLabel = QLabel(QApplication.translate('Label','Rate'))
        phidgetBox1048.addWidget(typeLabel,1,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1048.addWidget(asyncLabel,2,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1048.addWidget(changeTriggerLabel,3,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1048.addWidget(rateLabel,4,0,Qt.AlignmentFlag.AlignRight)
        phidget1048HBox = QHBoxLayout()
        phidget1048HBox.addStretch()
        phidget1048HBox.addLayout(phidgetBox1048)
        phidget1048HBox.addStretch()
        phidget1048VBox = QVBoxLayout()
        phidget1048VBox.addLayout(phidget1048HBox)
        phidget1048VBox.addStretch()
        phidget1048GroupBox = QGroupBox('1048/1051/TMP1100/TMP1101 TC')
        phidget1048GroupBox.setLayout(phidget1048VBox)
        phidget1048GroupBox.setContentsMargins(0,0,0,0)
        phidget1048HBox.setContentsMargins(0,0,0,0)
        phidget1048VBox.setContentsMargins(0,0,0,0)

        # Phidget IR
        phidgetBox1045 = QGridLayout()
        phidgetBox1045.setSpacing(2)
        self.changeTriggerCombos1045 = QComboBox()
        self.changeTriggerCombos1045.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = cast(QStandardItemModel, self.changeTriggerCombos1045.model())
        changeTriggerItems = self.createItems(self.aw.qmc.phidget1045_changeTriggersStrings)
        for item in changeTriggerItems:
            model.appendRow(item)
        try:
            self.changeTriggerCombos1045.setCurrentIndex(self.aw.qmc.phidget1045_changeTriggersValues.index(self.aw.qmc.phidget1045_changeTrigger))
        except Exception: # pylint: disable=broad-except
            pass

        self.changeTriggerCombos1045.setMinimumContentsLength(3)
        self.changeTriggerCombos1045.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents) # AdjustToMinimumContentsLengthWithIcon
        width = self.changeTriggerCombos1045.minimumSizeHint().width()
        self.changeTriggerCombos1045.setMinimumWidth(width)
        if platform.system() == 'Darwin':
            self.changeTriggerCombos1045.setMaximumWidth(width)

        phidgetBox1045.addWidget(self.changeTriggerCombos1045,3,1)
        self.asyncCheckBoxe1045 = QCheckBox()
        phidgetBox1045.addWidget(self.asyncCheckBoxe1045,2,1)
        self.asyncCheckBoxe1045.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.asyncCheckBoxe1045.setChecked(True)
        self.asyncCheckBoxe1045.stateChanged.connect(self.asyncFlagStateChanged1045)
        self.asyncCheckBoxe1045.setChecked(self.aw.qmc.phidget1045_async)
        asyncLabel = QLabel(QApplication.translate('Label','Async'))
        changeTriggerLabel = QLabel(QApplication.translate('Label','Change'))
        rateLabel = QLabel(QApplication.translate('Label','Rate'))

        self.dataRateCombo1045 = QComboBox()
        self.dataRateCombo1045.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = cast(QStandardItemModel, self.dataRateCombo1045.model())
        dataRateItems = self.createItems(self.aw.qmc.phidget_dataRatesStrings)
        for item in dataRateItems:
            model.appendRow(item)
        try:
            self.dataRateCombo1045.setCurrentIndex(self.aw.qmc.phidget_dataRatesValues.index(self.aw.qmc.phidget1045_dataRate))
        except Exception: # pylint: disable=broad-except
            pass
        self.dataRateCombo1045.setMinimumContentsLength(3)
        self.dataRateCombo1045.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents) # AdjustToMinimumContentsLengthWithIcon
        width = self.dataRateCombo1045.minimumSizeHint().width()
        self.dataRateCombo1045.setMinimumWidth(width)
        if platform.system() == 'Darwin':
            self.dataRateCombo1045.setMaximumWidth(width)

        EmissivityLabel = QLabel(QApplication.translate('Label','Emissivity'))
        self.emissivitySpinBox = MyQDoubleSpinBox()
        self.emissivitySpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.emissivitySpinBox.setRange(0.,1.)
        self.emissivitySpinBox.setSingleStep(.1)
        self.emissivitySpinBox.setValue(self.aw.qmc.phidget1045_emissivity)

        phidgetBox1045.addWidget(asyncLabel,2,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1045.addWidget(changeTriggerLabel,3,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1045.addWidget(rateLabel,4,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1045.addWidget(EmissivityLabel,5,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1045.addWidget(self.dataRateCombo1045,4,1)
        phidgetBox1045.addWidget(self.emissivitySpinBox,5,1)
        phidget1045VBox = QVBoxLayout()
        phidget1045VBox.addStretch()
        phidget1045VBox.addLayout(phidgetBox1045)
        phidget1045VBox.addStretch()
        phidget1045VBox.addStretch()
        phidget1045GroupBox = QGroupBox('1045 IR')
        phidget1045GroupBox.setLayout(phidget1045VBox)
        phidget1045VBox.setContentsMargins(0,0,0,0)


        # 1046 RTD
        phidgetBox1046 = QGridLayout()
        phidgetBox1046.setSpacing(2)
        phidgetBox1046.setContentsMargins(0,0,0,0)
        self.gainCombos1046 = []
        self.formulaCombos1046 = []
        self.asyncCheckBoxes1046 = []
        for i in range(1,5):
            gainCombo = QComboBox()
            gainCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)

            model = cast(QStandardItemModel, gainCombo.model())
            gainItems = self.createItems(self.aw.qmc.phidget1046_gainValues)
            for item in gainItems:
                model.appendRow(item)
            try:
                gainCombo.setCurrentIndex(self.aw.qmc.phidget1046_gain[i-1] - 1)
            except Exception: # pylint: disable=broad-except
                pass

            gainCombo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents) # AdjustToMinimumContentsLengthWithIcon
            gainCombo.setMinimumContentsLength(1)
            width = gainCombo.minimumSizeHint().width()
            gainCombo.setMinimumWidth(width)
            if platform.system() == 'Darwin':
                gainCombo.setMaximumWidth(width)

            self.gainCombos1046.append(gainCombo)
            phidgetBox1046.addWidget(gainCombo,1,i)

            formulaCombo = QComboBox()
            formulaCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            model = cast(QStandardItemModel, formulaCombo.model())
            formulaItems = self.createItems(self.aw.qmc.phidget1046_formulaValues)
            for item in formulaItems:
                model.appendRow(item)
            try:
                formulaCombo.setCurrentIndex(self.aw.qmc.phidget1046_formula[i-1])
            except Exception: # pylint: disable=broad-except
                pass

            formulaCombo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents) # AdjustToMinimumContentsLengthWithIcon
            formulaCombo.setMinimumContentsLength(1)
            width = formulaCombo.minimumSizeHint().width()
            formulaCombo.setMinimumWidth(width)
            if platform.system() == 'Darwin':
                formulaCombo.setMaximumWidth(width)

            self.formulaCombos1046.append(formulaCombo)
            phidgetBox1046.addWidget(formulaCombo,2,i)

            asyncFlag = QCheckBox()
            asyncFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            asyncFlag.setChecked(True)
            asyncFlag.setChecked(self.aw.qmc.phidget1046_async[i-1])
            self.asyncCheckBoxes1046.append(asyncFlag)
            phidgetBox1046.addWidget(asyncFlag,3,i)
            rowLabel = QLabel(str(i-1))
            phidgetBox1046.addWidget(rowLabel,0,i)

        self.dataRateCombo1046 = QComboBox()
        self.dataRateCombo1046.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = cast(QStandardItemModel, self.dataRateCombo1046.model())
        dataRateItems = self.createItems(self.aw.qmc.phidget_dataRatesStrings)
        for item in dataRateItems:
            model.appendRow(item)
        try:
            self.dataRateCombo1046.setCurrentIndex(self.aw.qmc.phidget_dataRatesValues.index(self.aw.qmc.phidget1046_dataRate))
        except Exception: # pylint: disable=broad-except
            pass
        self.dataRateCombo1046.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents) # AdjustToMinimumContentsLengthWithIcon
        self.dataRateCombo1046.setMinimumContentsLength(5)
        width = self.dataRateCombo1046.minimumSizeHint().width()
        self.dataRateCombo1046.setMinimumWidth(width)
        if platform.system() == 'Darwin':
            self.dataRateCombo1046.setMaximumWidth(width)

        phidgetBox1046.addWidget(self.dataRateCombo1046,4,1,1,2)


        gainLabel = QLabel(QApplication.translate('Label','Gain'))
        formulaLabel = QLabel(QApplication.translate('Label','Wiring'))
        asyncLabel = QLabel(QApplication.translate('Label','Async'))
        rateLabel = QLabel(QApplication.translate('Label','Rate'))
        phidgetBox1046.addWidget(gainLabel,1,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1046.addWidget(formulaLabel,2,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1046.addWidget(asyncLabel,3,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1046.addWidget(rateLabel,4,0,Qt.AlignmentFlag.AlignRight)
        phidget1046HBox = QHBoxLayout()
        phidget1046HBox.addStretch()
        phidget1046HBox.addLayout(phidgetBox1046)
#        phidget1046HBox.addStretch()
        phidget1046VBox = QVBoxLayout()
        phidget1046VBox.addLayout(phidget1046HBox)
        phidget1046VBox.addStretch()
        phidget1046GroupBox = QGroupBox('1046 RTD / DAQ1500')
        phidget1046GroupBox.setLayout(phidget1046VBox)
        phidget1046GroupBox.setContentsMargins(0,10,0,0)
        phidget1046HBox.setContentsMargins(0,0,0,0)
        phidget1046VBox.setContentsMargins(0,0,0,0)

        # TMP1200 RTD
        phidgetBox1200 = QGridLayout()
        phidgetBox1200.setSpacing(2)
        phidgetBox1200_2 = QGridLayout()
        phidgetBox1200_2.setSpacing(2)

        self.formulaCombo1200 = QComboBox()
        self.formulaCombo1200.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = cast(QStandardItemModel, self.formulaCombo1200.model())
        wireItems = self.createItems(self.aw.qmc.phidget1200_formulaValues)
        for item in wireItems:
            model.appendRow(item)
        try:
            self.formulaCombo1200.setCurrentIndex(self.aw.qmc.phidget1200_formula)
        except Exception: # pylint: disable=broad-except
            pass
        self.formulaCombo1200.setMinimumContentsLength(5)
        width = self.formulaCombo1200.minimumSizeHint().width()
        self.formulaCombo1200.setMinimumWidth(width)
#        self.formulaCombo1200.setMaximumWidth(width)

        self.wireCombo1200 = QComboBox()
        self.wireCombo1200.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = cast(QStandardItemModel, self.wireCombo1200.model())
        wireItems = self.createItems(self.aw.qmc.phidget1200_wireValues)
        for item in wireItems:
            model.appendRow(item)
        try:
            self.wireCombo1200.setCurrentIndex(self.aw.qmc.phidget1200_wire)
        except Exception: # pylint: disable=broad-except
            pass
        self.wireCombo1200.setMinimumContentsLength(5)
        width = self.wireCombo1200.minimumSizeHint().width()
        self.wireCombo1200.setMinimumWidth(width)
#        self.wireCombo1200.setMaximumWidth(width)

        self.asyncCheckBoxe1200 = QCheckBox()
        self.asyncCheckBoxe1200.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.asyncCheckBoxe1200.setChecked(self.aw.qmc.phidget1200_async)
        self.asyncCheckBoxe1200.stateChanged.connect(self.asyncFlagStateChanged1200)

        self.changeTriggerCombo1200 = QComboBox()
        self.changeTriggerCombo1200.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = cast(QStandardItemModel, self.changeTriggerCombo1200.model())
        changeTriggerItems = self.createItems(self.aw.qmc.phidget1200_changeTriggersStrings)
        for item in changeTriggerItems:
            model.appendRow(item)
        try:
            self.changeTriggerCombo1200.setCurrentIndex(self.aw.qmc.phidget1200_changeTriggersValues.index(self.aw.qmc.phidget1200_changeTrigger))
        except Exception: # pylint: disable=broad-except
            pass
        self.changeTriggerCombo1200.setMinimumContentsLength(4)
        width = self.changeTriggerCombo1200.minimumSizeHint().width()
        self.changeTriggerCombo1200.setMinimumWidth(width)
#        self.changeTriggerCombo1200.setMaximumWidth(width)
        self.changeTriggerCombo1200.setEnabled(self.aw.qmc.phidget1200_async)

        self.rateCombo1200 = QComboBox()
        self.rateCombo1200.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = cast(QStandardItemModel, self.rateCombo1200.model())
        dataRateItems = self.createItems(self.aw.qmc.phidget1200_dataRatesStrings)
        for item in dataRateItems:
            model.appendRow(item)
        try:
            self.rateCombo1200.setCurrentIndex(self.aw.qmc.phidget1200_dataRatesValues.index(self.aw.qmc.phidget1200_dataRate))
        except Exception: # pylint: disable=broad-except
            pass
        self.rateCombo1200.setMinimumContentsLength(3)
        width = self.rateCombo1200.minimumSizeHint().width()
        self.rateCombo1200.setMinimumWidth(width)
#        self.rateCombo1200.setMaximumWidth(width)

#---
        self.formulaCombo1200_2 = QComboBox()
        self.formulaCombo1200_2.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = cast(QStandardItemModel, self.formulaCombo1200_2.model())
        wireItems = self.createItems(self.aw.qmc.phidget1200_formulaValues)
        for item in wireItems:
            model.appendRow(item)
        try:
            self.formulaCombo1200_2.setCurrentIndex(self.aw.qmc.phidget1200_2_formula)
        except Exception: # pylint: disable=broad-except
            pass
        self.formulaCombo1200_2.setMinimumContentsLength(4)
        width = self.formulaCombo1200_2.minimumSizeHint().width()
        self.formulaCombo1200_2.setMinimumWidth(width)

        self.wireCombo1200_2 = QComboBox()
        self.wireCombo1200_2.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = cast(QStandardItemModel, self.wireCombo1200_2.model())
        wireItems = self.createItems(self.aw.qmc.phidget1200_wireValues)
        for item in wireItems:
            model.appendRow(item)
        try:
            self.wireCombo1200_2.setCurrentIndex(self.aw.qmc.phidget1200_2_wire)
        except Exception: # pylint: disable=broad-except
            pass
        self.wireCombo1200_2.setMinimumContentsLength(4)
        width = self.wireCombo1200_2.minimumSizeHint().width()
        self.wireCombo1200_2.setMinimumWidth(width)
#        self.wireCombo1200_2.setMaximumWidth(width)

        self.asyncCheckBoxe1200_2 = QCheckBox()
        self.asyncCheckBoxe1200_2.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.asyncCheckBoxe1200_2.setChecked(self.aw.qmc.phidget1200_2_async)
        self.asyncCheckBoxe1200_2.stateChanged.connect(self.asyncFlagStateChanged1200_2)

        self.changeTriggerCombo1200_2 = QComboBox()
        self.changeTriggerCombo1200_2.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = cast(QStandardItemModel, self.changeTriggerCombo1200_2.model())
        changeTriggerItems = self.createItems(self.aw.qmc.phidget1200_changeTriggersStrings)
        for item in changeTriggerItems:
            model.appendRow(item)
        try:
            self.changeTriggerCombo1200_2.setCurrentIndex(self.aw.qmc.phidget1200_changeTriggersValues.index(self.aw.qmc.phidget1200_2_changeTrigger))
        except Exception: # pylint: disable=broad-except
            pass
        self.changeTriggerCombo1200_2.setMinimumContentsLength(4)
        width = self.changeTriggerCombo1200_2.minimumSizeHint().width()
        self.changeTriggerCombo1200_2.setMinimumWidth(width)
#        self.changeTriggerCombo1200_2.setMaximumWidth(width)
        self.changeTriggerCombo1200_2.setEnabled(self.aw.qmc.phidget1200_async)

        self.rateCombo1200_2 = QComboBox()
        self.rateCombo1200_2.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = cast(QStandardItemModel, self.rateCombo1200_2.model())
        dataRateItems = self.createItems(self.aw.qmc.phidget1200_dataRatesStrings)
        for item in dataRateItems:
            model.appendRow(item)
        try:
            self.rateCombo1200_2.setCurrentIndex(self.aw.qmc.phidget1200_dataRatesValues.index(self.aw.qmc.phidget1200_2_dataRate))
        except Exception: # pylint: disable=broad-except
            pass
        self.rateCombo1200_2.setMinimumContentsLength(3)
        width = self.rateCombo1200_2.minimumSizeHint().width()
        self.rateCombo1200_2.setMinimumWidth(width)
#        self.rateCombo1200_2.setMaximumWidth(width)
#---

        typeLabel = QLabel(QApplication.translate('Label','Type'))
        wireLabel = QLabel(QApplication.translate('Label','Wiring'))
        asyncLabel = QLabel(QApplication.translate('Label','Async'))
        changeLabel = QLabel(QApplication.translate('Label','Change'))
        rateLabel = QLabel(QApplication.translate('Label','Rate'))

        typeLabel2 = QLabel(QApplication.translate('Label','Type'))
        wireLabel2 = QLabel(QApplication.translate('Label','Wiring'))
        asyncLabel2 = QLabel(QApplication.translate('Label','Async'))
        changeLabel2 = QLabel(QApplication.translate('Label','Change'))
        rateLabel2 = QLabel(QApplication.translate('Label','Rate'))

        phidgetBox1200.addWidget(typeLabel,1,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1200.addWidget(self.formulaCombo1200,1,1)
        phidgetBox1200.addWidget(wireLabel,2,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1200.addWidget(self.wireCombo1200,2,1)
        phidgetBox1200.addWidget(asyncLabel,3,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1200.addWidget(self.asyncCheckBoxe1200,3,1)
        phidgetBox1200.addWidget(changeLabel,4,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1200.addWidget(self.changeTriggerCombo1200,4,1)
        phidgetBox1200.addWidget(rateLabel,5,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1200.addWidget(self.rateCombo1200,5,1)

        phidgetBox1200_2.addWidget(typeLabel2,1,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1200_2.addWidget(self.formulaCombo1200_2,1,1)
        phidgetBox1200_2.addWidget(wireLabel2,2,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1200_2.addWidget(self.wireCombo1200_2,2,1)
        phidgetBox1200_2.addWidget(asyncLabel2,3,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1200_2.addWidget(self.asyncCheckBoxe1200_2,3,1)
        phidgetBox1200_2.addWidget(changeLabel2,4,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1200_2.addWidget(self.changeTriggerCombo1200_2,4,1)
        phidgetBox1200_2.addWidget(rateLabel2,5,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1200_2.addWidget(self.rateCombo1200_2,5,1)

        phidget1200HBox = QHBoxLayout()
        phidget1200HBox.addStretch()
        phidget1200HBox.addLayout(phidgetBox1200)
        phidget1200HBox.addStretch()
        phidget1200VBox = QVBoxLayout()
        phidget1200VBox.addLayout(phidget1200HBox)
        phidget1200VBox.addStretch()
        phidget1200VBox.setContentsMargins(0,0,0,0)
        phidget1200HBox.setContentsMargins(0,0,0,0)

        phidget1200HBox_2 = QHBoxLayout()
        phidget1200HBox_2.addStretch()
        phidget1200HBox_2.addLayout(phidgetBox1200_2)
        phidget1200HBox_2.addStretch()
        phidget1200VBox_2 = QVBoxLayout()
        phidget1200VBox_2.addLayout(phidget1200HBox_2)
        phidget1200VBox_2.addStretch()
        phidget1200VBox_2.setContentsMargins(0,0,0,0)
        phidget1200HBox_2.setContentsMargins(0,0,0,0)

        phidget1200_tabs = QTabWidget()
        phidget1200_tab1_widget = QWidget()
        phidget1200_tab1_widget.setLayout(phidget1200VBox)
        phidget1200_tabs.addTab(phidget1200_tab1_widget,'A')

        phidget1200_tab2_widget = QWidget()
        phidget1200_tab2_widget.setLayout(phidget1200VBox_2)
        phidget1200_tabs.addTab(phidget1200_tab2_widget,'B')

        phidgetGroupBoxLayout = QVBoxLayout()
        phidgetGroupBoxLayout.addWidget(phidget1200_tabs)

        phidgetGroupBoxLayout.setContentsMargins(0,0,0,0) # left, top, right, bottom

        phidget1200GroupBox = QGroupBox('TMP1200/1202 RTD')
        phidget1200GroupBox.setLayout(phidgetGroupBoxLayout)
        phidget1200GroupBox.setContentsMargins(0,2,0,0) # left, top, right, bottom


        # DAQ1400 VI
        powerLabel = QLabel(QApplication.translate('Label','Power'))
        modeLabel = QLabel(QApplication.translate('Label','Mode'))

        self.powerCombo1400 = QComboBox()
        self.powerCombo1400.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.powerCombo1400.addItems(self.aw.qmc.phidgetDAQ1400_powerSupplyStrings)
        self.powerCombo1400.setCurrentIndex(self.aw.qmc.phidgetDAQ1400_powerSupply)
        self.powerCombo1400.setMinimumContentsLength(3)
        width = self.powerCombo1400.minimumSizeHint().width()
        self.powerCombo1400.setMinimumWidth(width)

        self.modeCombo1400 = QComboBox()
        self.modeCombo1400.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.modeCombo1400.addItems(self.aw.qmc.phidgetDAQ1400_inputModeStrings)
        self.modeCombo1400.setCurrentIndex(self.aw.qmc.phidgetDAQ1400_inputMode)
        self.modeCombo1400.setMinimumContentsLength(3)
        width = self.modeCombo1400.minimumSizeHint().width()
        self.modeCombo1400.setMinimumWidth(width)

        phidgetBox1400 = QGridLayout()
        phidgetBox1400.setSpacing(2)
        phidgetBox1400.setContentsMargins(0,0,0,0)
        phidgetBox1400.addWidget(powerLabel,0,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1400.addWidget(self.powerCombo1400,0,1)
        phidgetBox1400.addWidget(modeLabel,1,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1400.addWidget(self.modeCombo1400,1,1)

        phidget1400HBox = QHBoxLayout()
        phidget1400HBox.addLayout(phidgetBox1400)
        phidget1400VBox = QVBoxLayout()
        phidget1400VBox.addLayout(phidget1400HBox)
        phidget1400VBox.addStretch()

        phidget1400GroupBox = QGroupBox('DAQ1400 VI')
        phidget1400GroupBox.setLayout(phidget1400VBox)
        phidget1400GroupBox.setContentsMargins(0,0,0,0)
        phidget1400VBox.setContentsMargins(0,0,0,0)
        phidget1400HBox.setContentsMargins(0,0,0,0)

        phdget10481045GroupBoxHBox = QHBoxLayout()
        phdget10481045GroupBoxHBox.addWidget(phidget1048GroupBox)
        phdget10481045GroupBoxHBox.addStretch()
        phdget10481045GroupBoxHBox.addWidget(phidget1200GroupBox)
        phdget10481045GroupBoxHBox.addStretch()
        phdget10481045GroupBoxHBox.addWidget(phidget1400GroupBox)
        phdget10481045GroupBoxHBox.addStretch()
        phdget10481045GroupBoxHBox.addWidget(phidget1046GroupBox)
        phdget10481045GroupBoxHBox.setContentsMargins(2,0,0,0) # left, top, right, bottom
        phdget10481045GroupBoxHBox.setSpacing(2)


        # Phidget IO 1018
        # per each of the 8-channels: raw flag / data rate popup / change trigger popup
        phidgetBox1018 = QGridLayout()
        phidgetBox1018.setSpacing(2)
        self.asyncCheckBoxes = []
        self.ratioCheckBoxes = []
        self.dataRateCombos = []
        self.changeTriggerCombos = []
        self.voltageRangeCombos = []
        for i in range(1,9):
            dataRatesCombo = QComboBox()
            dataRatesCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            model = cast(QStandardItemModel, dataRatesCombo.model())
            dataRateItems = self.createItems(self.aw.qmc.phidget_dataRatesStrings)
            for item in dataRateItems:
                model.appendRow(item)
            try:
                dataRatesCombo.setCurrentIndex(self.aw.qmc.phidget_dataRatesValues.index(self.aw.qmc.phidget1018_dataRates[i-1]))
            except Exception: # pylint: disable=broad-except
                pass
            dataRatesCombo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents) # AdjustToMinimumContentsLengthWithIcon
            dataRatesCombo.setMinimumContentsLength(4)
            width = dataRatesCombo.minimumSizeHint().width()
            dataRatesCombo.setMinimumWidth(width)
            if platform.system() == 'Darwin':
                dataRatesCombo.setMaximumWidth(width)
            self.dataRateCombos.append(dataRatesCombo)
            phidgetBox1018.addWidget(dataRatesCombo,4,i)

            changeTriggersCombo = QComboBox()
            changeTriggersCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            changeTriggersCombo.setEnabled(bool(self.aw.qmc.phidget1018_async[i-1]))
            model = cast(QStandardItemModel, changeTriggersCombo.model())
            changeTriggerItems = self.createItems(self.aw.qmc.phidget1018_changeTriggersStrings)
            for item in changeTriggerItems:
                model.appendRow(item)
            try:
                changeTriggersCombo.setCurrentIndex(self.aw.qmc.phidget1018_changeTriggersValues.index(self.aw.qmc.phidget1018_changeTriggers[i-1]))
            except Exception: # pylint: disable=broad-except
                pass
            changeTriggersCombo.setMinimumContentsLength(4)
            changeTriggersCombo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents) # AdjustToMinimumContentsLengthWithIcon
            width = changeTriggersCombo.minimumSizeHint().width()
            changeTriggersCombo.setMinimumWidth(width)
            if platform.system() == 'Darwin':
                changeTriggersCombo.setMaximumWidth(width)
            self.changeTriggerCombos.append(changeTriggersCombo)
            phidgetBox1018.addWidget(changeTriggersCombo,3,i)

            voltageRangeCombo = QComboBox()
            voltageRangeCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            model = cast(QStandardItemModel, voltageRangeCombo.model())
            voltageRangeItems = self.createItems(self.aw.qmc.phidgetVCP100x_voltageRangeStrings)
            for item in voltageRangeItems:
                model.appendRow(item)
            try:
                voltageRangeCombo.setCurrentIndex(self.aw.qmc.phidgetVCP100x_voltageRangeValues.index(self.aw.qmc.phidgetVCP100x_voltageRanges[i-1]))
            except Exception: # pylint: disable=broad-except
                pass
            voltageRangeCombo.setMinimumContentsLength(4)
            voltageRangeCombo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents) # AdjustToMinimumContentsLengthWithIcon
            width = voltageRangeCombo.minimumSizeHint().width()
            voltageRangeCombo.setMinimumWidth(width)
            if platform.system() == 'Darwin':
                voltageRangeCombo.setMaximumWidth(width)
            self.voltageRangeCombos.append(voltageRangeCombo)
            phidgetBox1018.addWidget(voltageRangeCombo,5,i)


            asyncFlag = QCheckBox()
            self.asyncCheckBoxes.append(asyncFlag)
            asyncFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            asyncFlag.setChecked(True)
            asyncFlag.stateChanged.connect(self.asyncFlagStateChanged)
            asyncFlag.setChecked(self.aw.qmc.phidget1018_async[i-1])
            phidgetBox1018.addWidget(asyncFlag,2,i)

            ratioFlag = QCheckBox()
            ratioFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            ratioFlag.setChecked(False)
            ratioFlag.setChecked(self.aw.qmc.phidget1018_ratio[i-1])
            self.ratioCheckBoxes.append(ratioFlag)
            phidgetBox1018.addWidget(ratioFlag,6,i)

            rowLabel = QLabel(str(i-1))
            phidgetBox1018.addWidget(rowLabel,0,i)

        asyncLabel = QLabel(QApplication.translate('Label','Async'))
        dataRateLabel = QLabel(QApplication.translate('Label','Rate'))
        changeTriggerLabel = QLabel(QApplication.translate('Label','Change'))
        ratioLabel = QLabel(QApplication.translate('Label','Ratio'))
        rangeLabel = QLabel(QApplication.translate('Label','Range'))
        phidgetBox1018.addWidget(asyncLabel,2,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1018.addWidget(changeTriggerLabel,3,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1018.addWidget(dataRateLabel,4,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1018.addWidget(rangeLabel,5,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1018.addWidget(ratioLabel,6,0,Qt.AlignmentFlag.AlignRight)
        phidget1018HBox = QVBoxLayout()
        phidget1018HBox.addLayout(phidgetBox1018)
        phidget1018GroupBox = QGroupBox('1010/1011/1013/1018/1019/HUB0000/SBC/DAQxxxx/VCP100x IO')
        phidget1018GroupBox.setLayout(phidget1018HBox)
        phidget1018HBox.setContentsMargins(0,0,0,0)
        self.phidgetBoxRemoteFlag = QCheckBox()
        self.phidgetBoxRemoteFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.phidgetBoxRemoteFlag.setChecked(self.aw.qmc.phidgetRemoteFlag)
        self.phidgetBoxRemoteFlag.stateChanged.connect(self.phidgetRemoteStateChanged)
        phidgetServerIdLabel = QLabel(QApplication.translate('Label','Host'))
        self.phidgetServerId = QLineEdit(self.aw.qmc.phidgetServerID)
        self.phidgetServerId.textChanged.connect(self.phidgetHostChanged)
        self.phidgetServerId.setMinimumWidth(200)
        self.phidgetServerId.setEnabled(self.aw.qmc.phidgetRemoteFlag)
        phidgetPasswordLabel = QLabel(QApplication.translate('Label','Password'))
        self.phidgetPassword = QLineEdit(self.aw.qmc.phidgetPassword)
        self.phidgetPassword.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        self.phidgetPassword.setEnabled(self.aw.qmc.phidgetServerID != '')
        self.phidgetPassword.setMinimumWidth(100)
        self.phidgetPassword.setEnabled(self.aw.qmc.phidgetRemoteFlag)
        self.phidgetPassword.setToolTip(QApplication.translate('Tooltip','Phidget server password'))
        phidgetPortLabel = QLabel(QApplication.translate('Label','Port'))
        self.phidgetPort = QLineEdit(str(self.aw.qmc.phidgetPort))
        self.phidgetPort.setMaximumWidth(70)
        self.phidgetPort.setEnabled(self.aw.qmc.phidgetRemoteFlag)
        self.phidgetBoxRemoteOnlyFlag = QCheckBox(QApplication.translate('Label','Remote Only'))
        self.phidgetBoxRemoteOnlyFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.phidgetBoxRemoteOnlyFlag.setChecked(self.aw.qmc.phidgetRemoteOnlyFlag)
        self.phidgetBoxRemoteOnlyFlag.setEnabled(self.aw.qmc.phidgetRemoteFlag)
        phidgetServerBox = QHBoxLayout()
        phidgetServerBox.addWidget(phidgetServerIdLabel)
        phidgetServerBox.addWidget(self.phidgetServerId)
        phidgetServerBox.setContentsMargins(0,0,0,0)
        phidgetServerBox.setSpacing(3)
        phidgetPasswordBox = QHBoxLayout()
        phidgetPasswordBox.addWidget(phidgetPasswordLabel)
        phidgetPasswordBox.addWidget(self.phidgetPassword)
        phidgetPasswordBox.setContentsMargins(0,0,0,0)
        phidgetPasswordBox.setSpacing(3)
        phidgetPortBox = QHBoxLayout()
        phidgetPortBox.addWidget(phidgetPortLabel)
        phidgetPortBox.addWidget(self.phidgetPort)
        phidgetPortBox.setContentsMargins(0,0,0,0)
        phidgetPortBox.setSpacing(3)
        phidgetNetworkGrid = QHBoxLayout()
        phidgetNetworkGrid.addWidget(self.phidgetBoxRemoteFlag)
        phidgetNetworkGrid.addStretch()
        phidgetNetworkGrid.addLayout(phidgetServerBox)
        phidgetNetworkGrid.addLayout(phidgetPortBox)
        phidgetNetworkGrid.addStretch()
        phidgetNetworkGrid.addLayout(phidgetPasswordBox)
        phidgetNetworkGrid.addStretch()
        phidgetNetworkGrid.addWidget(self.phidgetBoxRemoteOnlyFlag)
        phidgetNetworkGrid.setContentsMargins(0,0,0,0)
        phidgetNetworkGrid.setSpacing(20)
        phidgetNetworkGroupBox = QGroupBox(QApplication.translate('GroupBox','Network'))
        phidgetNetworkGroupBox.setLayout(phidgetNetworkGrid)
        phidget10451018HBox = QHBoxLayout()
        phidget10451018HBox.addWidget(phidget1045GroupBox)
        phidget10451018HBox.addStretch()
        phidget10451018HBox.addWidget(phidget1018GroupBox)
        phidget10451018HBox.setSpacing(2)
        phidgetVBox = QVBoxLayout()
        phidgetVBox.addLayout(phdget10481045GroupBoxHBox)
        phidgetVBox.addLayout(phidget10451018HBox)
        phidgetVBox.addWidget(phidgetNetworkGroupBox)
        phidgetVBox.addStretch()
        phidgetVBox.setSpacing(5)
        phidgetVBox.setContentsMargins(0,0,0,0)
        # yoctopuce widgets
        self.yoctoBoxRemoteFlag = QCheckBox()
        self.yoctoBoxRemoteFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.yoctoBoxRemoteFlag.setChecked(self.aw.qmc.yoctoRemoteFlag)
        self.yoctoBoxRemoteFlag.stateChanged.connect(self.yoctoBoxRemoteFlagStateChanged)
        yoctoServerIdLabel = QLabel(QApplication.translate('Label','VirtualHub'))
        self.yoctoServerId = QLineEdit(self.aw.qmc.yoctoServerID)
        self.yoctoServerId.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.yoctoServerId.setMinimumWidth(100)
        self.yoctoServerId.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.yoctoServerId.setEnabled(self.aw.qmc.yoctoRemoteFlag)
        YoctoEmissivityLabel = QLabel(QApplication.translate('Label','Emissivity'))
        self.yoctoEmissivitySpinBox = MyQDoubleSpinBox()
        self.yoctoEmissivitySpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.yoctoEmissivitySpinBox.setRange(0.,1.)
        self.yoctoEmissivitySpinBox.setSingleStep(.1)
        self.yoctoEmissivitySpinBox.setValue(self.aw.qmc.YOCTO_emissivity)
        yoctoServerBox = QHBoxLayout()
        yoctoServerBox.addWidget(yoctoServerIdLabel)
        yoctoServerBox.addSpacing(10)
        yoctoServerBox.addWidget(self.yoctoServerId)
        yoctoServerBox.addStretch()
        yoctoServerBox.setContentsMargins(0,0,0,0)
        yoctoServerBox.setSpacing(10)
        yoctoNetworkGrid = QGridLayout()
        yoctoNetworkGrid.addWidget(self.yoctoBoxRemoteFlag,0,0)
        yoctoNetworkGrid.addLayout(yoctoServerBox,0,1)
#        yoctoNetworkGrid.setContentsMargins(10,10,10,10)
        yoctoNetworkGrid.setSpacing(20)
        yoctoNetworkGroupBox = QGroupBox(QApplication.translate('GroupBox','Network'))
        yoctoNetworkGroupBox.setLayout(yoctoNetworkGrid)
        yoctoIRGrid = QGridLayout()
        yoctoIRGrid.addWidget(YoctoEmissivityLabel,0,0)
        yoctoIRGrid.addWidget(self.yoctoEmissivitySpinBox,0,1)
        yoctoIRHorizontalLayout = QHBoxLayout()
        yoctoIRHorizontalLayout.addLayout(yoctoIRGrid)
        yoctoIRHorizontalLayout.addStretch()
        self.yoctoDataRateCombo = QComboBox()
        self.yoctoDataRateCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = cast(QStandardItemModel, self.yoctoDataRateCombo.model())
        dataRateItems = self.createItems(self.aw.qmc.YOCTO_dataRatesStrings)
        for item in dataRateItems:
            model.appendRow(item)
        try:
            self.yoctoDataRateCombo.setCurrentIndex(self.aw.qmc.YOCTO_dataRatesValues.index(self.aw.qmc.YOCTO_dataRate))
        except Exception: # pylint: disable=broad-except
            pass
        self.yoctoDataRateCombo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents) # AdjustToMinimumContentsLengthWithIcon
        self.yoctoDataRateCombo.setMinimumContentsLength(5)
        width = self.yoctoDataRateCombo.minimumSizeHint().width()
        self.yoctoDataRateCombo.setMinimumWidth(width)
        self.yoctoAyncChanFlag = QCheckBox()
        self.yoctoAyncChanFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.yoctoAyncChanFlag.setChecked(self.aw.qmc.YOCTO_async[0]) # only one flag for both channels, as running on async and the other sync will disturbe the readings
        yoctoAsyncGrid = QGridLayout()
        yoctoAsyncGrid.addWidget(self.yoctoAyncChanFlag,0,0)
        yoctoAsyncGrid.addWidget(self.yoctoDataRateCombo,0,1)
        yoctoAsyncHorizontalLayout = QHBoxLayout()
        yoctoAsyncHorizontalLayout.addLayout(yoctoAsyncGrid)
        yoctoAsyncHorizontalLayout.addStretch()
        yoctoAsyncGroupBox = QGroupBox(QApplication.translate('GroupBox','Async'))
        yoctoAsyncGroupBox.setLayout(yoctoAsyncHorizontalLayout)
        yoctoIRGroupBox = QGroupBox(QApplication.translate('GroupBox','IR'))
        yoctoIRGroupBox.setLayout(yoctoIRHorizontalLayout)
        yoctoVBox = QVBoxLayout()
        yoctoVBox.addWidget(yoctoNetworkGroupBox)
        yoctoVBox.addWidget(yoctoIRGroupBox)
        yoctoVBox.addWidget(yoctoAsyncGroupBox)
        yoctoVBox.addStretch()
        yoctoVBox.setSpacing(5)
        yoctoVBox.setContentsMargins(0,0,0,0)
        # Ambient Widgets and Layouts
        self.temperatureDeviceCombo = QComboBox()
        self.temperatureDeviceCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.temperatureDeviceCombo.addItems(self.aw.qmc.temperaturedevicefunctionlist)

        # HACK: only needed for the macOS UI on Qt 5.12 onwords; without long items get cut in the popup
        #  note the -7 as the width of the popup is too large if given the correct maximum characters
#        self.temperatureDeviceCombo.setMinimumContentsLength(max(22,len(max(self.aw.qmc.temperaturedevicefunctionlist, key=len)) - 7)) # expects # characters, but is to wide

        try:
            self.temperatureDeviceCombo.setCurrentIndex(self.aw.qmc.ambient_temperature_device)
        except Exception: # pylint: disable=broad-except
            pass
        self.humidityDeviceCombo = QComboBox()
        self.humidityDeviceCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.humidityDeviceCombo.addItems(self.aw.qmc.humiditydevicefunctionlist)
        try:
            self.humidityDeviceCombo.setCurrentIndex(self.aw.qmc.ambient_humidity_device)
        except Exception: # pylint: disable=broad-except
            pass
        self.pressureDeviceCombo = QComboBox()
        self.pressureDeviceCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pressureDeviceCombo.addItems(self.aw.qmc.pressuredevicefunctionlist)
        try:
            self.pressureDeviceCombo.setCurrentIndex(self.aw.qmc.ambient_pressure_device)
        except Exception: # pylint: disable=broad-except
            pass
        self.elevationSpinBox = QSpinBox()
        self.elevationSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.elevationSpinBox.setRange(0,3000)
        self.elevationSpinBox.setSingleStep(1)
        self.elevationSpinBox.setValue(int(self.aw.qmc.elevation))
        self.elevationSpinBox.setSuffix(' ' + QApplication.translate('Label','MASL'))
        temperatureDeviceLabel = QLabel(QApplication.translate('Label','Temperature'))
        humidityDeviceLabel = QLabel(QApplication.translate('Label','Humidity'))
        pressureDeviceLabel = QLabel(QApplication.translate('Label','Pressure'))
        elevationLabel = QLabel(QApplication.translate('Label','Elevation'))
        ambientGrid = QGridLayout()
        ambientGrid.addWidget(temperatureDeviceLabel,0,0)
        ambientGrid.addWidget(self.temperatureDeviceCombo,0,1)
        ambientGrid.addWidget(humidityDeviceLabel,1,0)
        ambientGrid.addWidget(self.humidityDeviceCombo,1,1)
        ambientGrid.addWidget(pressureDeviceLabel,2,0)
        ambientGrid.addWidget(self.pressureDeviceCombo,2,1)
        ambientGrid.addWidget(elevationLabel,3,0)
        ambientGrid.addWidget(self.elevationSpinBox,3,1)
        ambientHBox = QHBoxLayout()
        ambientHBox.addStretch()
        ambientHBox.addLayout(ambientGrid)
        ambientHBox.addStretch()
        ambientVBox = QVBoxLayout()
        ambientVBox.addStretch()
        ambientVBox.addLayout(ambientHBox)
        ambientVBox.addStretch()
        ambientVBox.setContentsMargins(0,0,0,0)

        #https://stackoverflow.com/questions/106179/regular-expression-to-match-dns-hostname-or-ip-address
        #ValidIpAddressRegex = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$";
        #ValidHostnameRegex = "^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$";
        regexhost = QRegularExpression(r'(^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$)|(^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$)')

        santokerHostLabel = QLabel(QApplication.translate('Label','Host'))
        self.santokerHost = QLineEdit(self.aw.santokerHost)
        self.santokerHost.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.santokerHost.setFixedWidth(150)
        self.santokerHost.setValidator(QRegularExpressionValidator(regexhost,self.santokerHost))
        self.santokerHost.setEnabled(not self.aw.santokerSerial)
        santokerPortLabel = QLabel(QApplication.translate('Label','Port'))
        self.santokerPort = QLineEdit(str(self.aw.santokerPort))
        self.santokerPort.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.santokerPort.setFixedWidth(150)
        self.santokerPort.setValidator(QIntValidator(1, 65535,self.santokerPort))
        self.santokerPort.setEnabled(not self.aw.santokerSerial)

        self.santokerSerialFlag = QCheckBox(QApplication.translate('Label','Serial'))
        self.santokerSerialFlag.setChecked(self.aw.santokerSerial and not self.aw.santokerBLE)
        self.santokerSerialFlag.stateChanged.connect(self.santokerSerialStateChanged)

        self.santokerNetworkFlag = QCheckBox(QApplication.translate('Label','WiFi'))
        self.santokerNetworkFlag.setChecked(not self.aw.santokerSerial and not self.aw.santokerBLE)
        self.santokerNetworkFlag.stateChanged.connect(self.santokerNetworkStateChanged)

        self.santokerBLEFlag = QCheckBox(QApplication.translate('Label','Bluetooth'))
        self.santokerBLEFlag.setChecked(self.aw.santokerBLE and not self.aw.santokerSerial)
        self.santokerBLEFlag.stateChanged.connect(self.santokerBLEStateChanged)

        # make those flags exclusive
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.santokerSerialFlag)
        self.button_group.addButton(self.santokerNetworkFlag)
        self.button_group.addButton(self.santokerBLEFlag)

        kaleidoHostLabel = QLabel(QApplication.translate('Label','Host'))
        self.kaleidoHost = QLineEdit(self.aw.kaleidoHost)
        self.kaleidoHost.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.kaleidoHost.setFixedWidth(150)
        self.kaleidoHost.setValidator(QRegularExpressionValidator(regexhost,self.kaleidoHost))
        self.kaleidoHost.setEnabled(not self.aw.kaleidoSerial)
        kaleidoPortLabel = QLabel(QApplication.translate('Label','Port'))
        self.kaleidoPort = QLineEdit(str(self.aw.kaleidoPort))
        self.kaleidoPort.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.kaleidoPort.setFixedWidth(150)
        self.kaleidoPort.setValidator(QIntValidator(1, 65535,self.kaleidoPort))
        self.kaleidoPort.setEnabled(not self.aw.kaleidoSerial)
        self.kaleidoSerialFlag = QCheckBox(QApplication.translate('Label','WiFi'))
        self.kaleidoSerialFlag.setChecked(not self.aw.kaleidoSerial)
        self.kaleidoSerialFlag.stateChanged.connect(self.kaleidoSerialStateChanged)
#        kaleidoPIDLabel = QLabel('PID')
#        self.kaleidoPIDFlag = QCheckBox()
#        self.kaleidoPIDFlag.setChecked(self.aw.kaleidoPID)

        mugmaHostLabel = QLabel(QApplication.translate('Label','Host'))
        self.mugmaHost = QLineEdit(self.aw.mugmaHost)
        self.mugmaHost.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.mugmaHost.setFixedWidth(150)
        self.mugmaHost.setValidator(QRegularExpressionValidator(regexhost,self.mugmaHost))
        mugmaPortLabel = QLabel(QApplication.translate('Label','Port'))
        self.mugmaPort = QLineEdit(str(self.aw.mugmaPort))
        self.mugmaPort.setValidator(QIntValidator(1, 65535,self.mugmaPort))
        self.mugmaPort.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.mugmaPort.setFixedWidth(150)

        colorTrackMeanLabel = QLabel(QApplication.translate('Label','Mean Filter'))
        self.colorTrackMeanSpinBox = QSpinBox()
        self.colorTrackMeanSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.colorTrackMeanSpinBox.setRange(10,200)
        self.colorTrackMeanSpinBox.setValue(int(self.aw.colorTrack_mean_window_size))
        colorTrackMedianLabel = QLabel(QApplication.translate('Label','Median Filter'))
        self.colorTrackMedianSpinBox = QSpinBox()
        self.colorTrackMedianSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.colorTrackMedianSpinBox.setRange(10,200)
        self.colorTrackMedianSpinBox.setValue(int(self.aw.colorTrack_median_window_size))

        santokerNetworkGrid = QGridLayout()
        santokerNetworkGrid.addWidget(self.santokerNetworkFlag,0,0)
        santokerNetworkGrid.addWidget(santokerHostLabel,0,1)
        santokerNetworkGrid.addWidget(self.santokerHost,0,2)
        santokerNetworkGrid.addWidget(santokerPortLabel,1,1)
        santokerNetworkGrid.addWidget(self.santokerPort,1,2)
        santokerNetworkGrid.setSpacing(20)
        santokerSerialHBox = QHBoxLayout()
        santokerSerialHBox.addSpacing(20)
        santokerSerialHBox.addWidget(self.santokerBLEFlag)
        santokerSerialHBox.addSpacing(20)
        santokerSerialHBox.addWidget(self.santokerSerialFlag)
        santokerSerialHBox.addStretch()
        santokerHBox = QHBoxLayout()
        santokerHBox.addStretch()
        santokerHBox.addLayout(santokerNetworkGrid)
        santokerHBox.addStretch()
        santokerVBox = QVBoxLayout()
        santokerVBox.addLayout(santokerSerialHBox)
        santokerVBox.addLayout(santokerHBox)
        santokerVBox.addStretch()
        santokerVBox.setSpacing(5)
        santokerVBox.setContentsMargins(0,0,0,0)

        santokerNetworkGroupBox = QGroupBox('Santoker')
        santokerNetworkGroupBox.setLayout(santokerVBox)

        kaleidoNetworkGrid = QGridLayout()
        kaleidoNetworkGrid.addWidget(self.kaleidoSerialFlag,0,0)
        kaleidoNetworkGrid.addWidget(kaleidoHostLabel,0,1)
        kaleidoNetworkGrid.addWidget(self.kaleidoHost,0,2)
        kaleidoNetworkGrid.addWidget(kaleidoPortLabel,1,1)
        kaleidoNetworkGrid.addWidget(self.kaleidoPort,1,2)
#        kaleidoNetworkGrid.addWidget(self.kaleidoPIDFlag,2,0)
#        kaleidoNetworkGrid.addWidget(kaleidoPIDLabel,2,1)
        kaleidoNetworkGrid.setSpacing(20)
        kaleidoNetworkGroupBox = QGroupBox('Kaleido')
        kaleidoNetworkGroupBox.setLayout(kaleidoNetworkGrid)
        kaleidoHBox = QHBoxLayout()
        kaleidoHBox.addWidget(kaleidoNetworkGroupBox)
        kaleidoHBox.addStretch()
        kaleidoVBox = QVBoxLayout()
        kaleidoVBox.addLayout(kaleidoHBox)
        kaleidoVBox.addStretch()
        kaleidoVBox.setSpacing(5)
        kaleidoVBox.setContentsMargins(0,0,0,0)

        mugmaNetworkGrid = QGridLayout()
        mugmaNetworkGrid.addWidget(mugmaHostLabel,0,1)
        mugmaNetworkGrid.addWidget(self.mugmaHost,0,2)
        mugmaNetworkGrid.addWidget(mugmaPortLabel,1,1)
        mugmaNetworkGrid.addWidget(self.mugmaPort,1,2)
        mugmaNetworkGrid.setSpacing(20)
        mugmaNetworkGroupBox = QGroupBox('Mugma')
        mugmaNetworkGroupBox.setLayout(mugmaNetworkGrid)
        mugmaHBox = QHBoxLayout()
        mugmaHBox.addWidget(mugmaNetworkGroupBox)
        mugmaHBox.addStretch()
        mugmaVBox = QVBoxLayout()
        mugmaVBox.addLayout(mugmaHBox)
        mugmaVBox.setContentsMargins(0,0,0,0)

        colorTrackNetworkGrid = QGridLayout()
        colorTrackNetworkGrid.addWidget(colorTrackMeanLabel,0,1)
        colorTrackNetworkGrid.addWidget(self.colorTrackMeanSpinBox,0,2)
        colorTrackNetworkGrid.addWidget(colorTrackMedianLabel,1,1)
        colorTrackNetworkGrid.addWidget(self.colorTrackMedianSpinBox,1,2)
        colorTrackNetworkGrid.setSpacing(20)
        colorTrackNetworkGroupBox = QGroupBox('ColorTrack')
        colorTrackNetworkGroupBox.setLayout(colorTrackNetworkGrid)
        colorTrackHBox = QHBoxLayout()
        colorTrackHBox.addWidget(colorTrackNetworkGroupBox)
        colorTrackHBox.addStretch()
        colorTrackVBox = QVBoxLayout()
        colorTrackVBox.addLayout(colorTrackHBox)
        colorTrackVBox.addStretch()
        colorTrackVBox.setSpacing(5)
        colorTrackVBox.setContentsMargins(0,0,0,0)

        # create pid box
        PIDgrid = QGridLayout()
        PIDgrid.addWidget(label1,0,1)
        PIDgrid.addWidget(label2,0,2)
        PIDgrid.addWidget(controllabel,1,0)
        PIDgrid.addWidget(self.controlpidtypeComboBox,1,1)
        PIDgrid.addWidget(self.controlpidunitidComboBox,1,2)
        PIDgrid.addWidget(self.showFujiLCDs,1,3)
        PIDgrid.addWidget(btlabel,2,0,Qt.AlignmentFlag.AlignRight)
        PIDgrid.addWidget(self.btpidtypeComboBox,2,1)
        PIDgrid.addWidget(self.btpidunitidComboBox,2,2)
        PIDgrid.addWidget(self.useModbusPort,2,3)
        PIDBox = QHBoxLayout()
        PIDBox.addLayout(PIDgrid)
        PIDBox.addStretch()
        PIDBox.setContentsMargins(5,0,5,5)
        PIDGroupBox = QGroupBox(QApplication.translate('GroupBox','PID'))
        PIDGroupBox.setLayout(PIDBox)
        # create arduino box
        filtgrid = QGridLayout()
        for i in range(4):
            filtgrid.addWidget(self.FILTspinBoxes[i],1,i+2)
        filtgridBox = QHBoxLayout()
        filtgridBox.addLayout(filtgrid)
        filtgridBox.addStretch()
        filtgridBox.setContentsMargins(5,5,5,5)
        arduinogrid = QGridLayout()
        arduinogrid.addWidget(arduinoETLabel,1,0,Qt.AlignmentFlag.AlignRight)
        arduinogrid.addWidget(self.arduinoETComboBox,1,1)
        arduinogrid.addWidget(arduinoBTLabel,2,0,Qt.AlignmentFlag.AlignRight)
        arduinogrid.addWidget(self.arduinoBTComboBox,2,1)
        arduinogrid.addWidget(self.arduinoATComboBox,2,3)
        arduinogrid.addWidget(arduinoATLabel,2,4)
        arduinogrid.addWidget(self.showControlButton,2,5)
        arduinogrid.addWidget(FILTLabel,1,3,Qt.AlignmentFlag.AlignRight)
        arduinogrid.addLayout(filtgridBox,1,4,1,2)
        arduinogridBox = QHBoxLayout()
        arduinogridBox.addLayout(arduinogrid)
        arduinogridBox.addStretch()
        arduinogridBox.setContentsMargins(5,5,5,5)
        arduinoBox = QVBoxLayout()
        arduinoBox.addLayout(arduinogridBox)
        arduinoBox.setContentsMargins(5,5,5,5)
        arduinoGroupBox = QGroupBox(QApplication.translate('GroupBox','Arduino TC4'))
        arduinoGroupBox.setLayout(arduinoBox)
        arduinoBox.setContentsMargins(0,0,0,0)
        arduinoGroupBox.setContentsMargins(0,12,0,0)
        #create program Box
        programlayout = QGridLayout()
        programlayout.addWidget(helpprogrambutton,0,0)
        programlayout.addWidget(selectprogrambutton,0,1)
        programlayout.addWidget(self.programedit,0,2)
        programlayout.addWidget(self.outprogramFlag,1,0)
        programlayout.addWidget(selectoutprogrambutton,1,1)
        programlayout.addWidget(self.outprogramedit,1,2)
        programGroupBox = QGroupBox(QApplication.translate('GroupBox','External Program'))
        programGroupBox.setLayout(programlayout)
        programlayout.setContentsMargins(5,10,5,5)
        programGroupBox.setContentsMargins(0,12,0,0)
        #ET BT symbolic adjustments/assignments Box
        self.updateETBTButton = QPushButton(QApplication.translate('Button','Update Profile'))
        self.updateETBTButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.updateETBTButton.setToolTip(QApplication.translate('Tooltip','Recaclulates ET and BT and updates their values in the profile'))
        self.updateETBTButton.clicked.connect(self.updateETBTinprofile)

        adjustmentHelp = QHBoxLayout()
        adjustmentHelp.addWidget(self.updateETBTButton)
        adjustmentHelp.addStretch()
        adjustmentHelp.addWidget(symbolicHelpButton)
        adjustmentGroupBox = QGroupBox(QApplication.translate('GroupBox','Symbolic Assignments'))
        adjustmentsLayout = QVBoxLayout()
        adjustmentsLayout.addWidget(labelETadvanced)
        adjustmentsLayout.addWidget(self.ETfunctionedit)
        adjustmentsLayout.addWidget(labelBTadvanced)
        adjustmentsLayout.addWidget(self.BTfunctionedit)
        adjustmentsLayout.addStretch()

        adjustmentsLayout.addLayout(adjustmentHelp)
        adjustmentGroupBox.setLayout(adjustmentsLayout)
        #LAYOUT TAB 1
        deviceSubSelector = QHBoxLayout()
        deviceSubSelector.addWidget(self.controlButtonFlag)
        deviceSubSelector.addSpacing(35)
        deviceSubSelector.addWidget(self.curves)
        deviceSubSelector.addSpacing(15)
        deviceSubSelector.addWidget(self.lcds)

        deviceSelector = QHBoxLayout()
        deviceSelector.addWidget(self.devicetypeComboBox)
        deviceSelector.addStretch()
        deviceSelector.addLayout(deviceSubSelector)

        grid = QGridLayout()
        grid.addWidget(self.nonpidButton,2,0)
        grid.addLayout(deviceSelector,2,1)
        grid.addWidget(self.pidButton,3,0)
        grid.addWidget(PIDGroupBox,3,1)
        grid.addWidget(self.arduinoButton,4,0)
        grid.addWidget(arduinoGroupBox,4,1)
        grid.addWidget(self.programButton,5,0)
        grid.addWidget(programGroupBox,5,1)
        grid.setSpacing(3)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.deviceLoggingFlag)
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)
        buttonLayout.setSpacing(10)
        tab1Layout = QVBoxLayout()
        tab1Layout.addLayout(grid)
        tab1Layout.setContentsMargins(5,5,5,5)
        tab1Layout.addStretch()
        bLayout = QHBoxLayout()
        bLayout.addWidget(self.addButton)
        bLayout.addWidget(self.delButton)
        bLayout.addWidget(self.copydeviceTableButton)
        bLayout.addStretch()
        bLayout.addSpacing(10)
        bLayout.addWidget(self.recalcButton)
        bLayout.addStretch()
        bLayout.addSpacing(10)
        bLayout.addWidget(resetButton)
        bLayout.addSpacing(10)
        bLayout.addWidget(extradevHelpButton)
        #LAYOUT TAB 2 (Extra Devices)
        tab2Layout = QVBoxLayout()
        tab2Layout.addWidget(self.devicetable)
        tab2Layout.setSpacing(5)
        tab2Layout.setContentsMargins(0,10,0,5)
        tab2Layout.addLayout(bLayout)
        #LAYOUT TAB 3 (Symb ET/BT)
        tab3Layout = QVBoxLayout()
        tab3Layout.addWidget(adjustmentGroupBox)
        tab3Layout.setContentsMargins(2,10,2,5)
        #LAYOUT TAB 4 (Phidgets)
        tab4Layout = QVBoxLayout()
        tab4Layout.addLayout(phidgetVBox)
        tab4Layout.setContentsMargins(2,10,2,5)
        tab4Layout.setSpacing(3)
        #LAYOUT TAB 5 (Yoctopuce)
        tab5Layout = QVBoxLayout()
        tab5Layout.addLayout(yoctoVBox)
        tab5Layout.setContentsMargins(2,10,2,5)
        #LAYOUT TAB 6 (Ambient)
        tab6Layout = QVBoxLayout()
        tab6Layout.addLayout(ambientVBox)
        tab6Layout.setContentsMargins(2,10,2,5)
        #LAYOUT TAB 7 (Santoker)
        tab7VLayout = QVBoxLayout()
        tab7VLayout.addWidget(santokerNetworkGroupBox)
        tab7VLayout.addLayout(kaleidoVBox)
        tab7VLayout.addStretch()
        tab7V2Layout = QVBoxLayout()
        tab7V2Layout.addLayout(mugmaVBox)
        tab7V2Layout.addLayout(colorTrackVBox)
        tab7V2Layout.addStretch()
        tab7Layout = QHBoxLayout()
        tab7Layout.addLayout(tab7VLayout)
        tab7Layout.addLayout(tab7V2Layout)
        tab7Layout.addStretch()
        tab7Layout.setContentsMargins(2,10,2,5)


        # scale tab
        tab8Layout = QGridLayout()
        tab8LayoutOFF = QVBoxLayout()
        if not self.aw.app.artisanviewerMode:
            self.scale1_devices:ScaleSpecs = [] # discovered scale1 devices
            self.scale2_devices:ScaleSpecs = [] # discovered scale2 devices
            self.scale1_weight:Optional[float] = None # weight of scale 1 in g
            self.scale2_weight:Optional[float] = None # weight of scale 2 in g

            scale1ModelLabel = QLabel(QApplication.translate('Label','Model'))
            self.scale1ModelComboBox = QComboBox()
            self.scale1ModelComboBox.setToolTip(QApplication.translate('Tooltip','Choose the model of your scale'))
            self.scale1ModelComboBox.setMinimumWidth(150)
            self.scale1ModelComboBox.addItems([''] + [m for (m,_) in SUPPORTED_SCALES])
            self.scale1NameLabel = QLabel(QApplication.translate('Label','Name'))
            self.scale1NameComboBox = QComboBox()
            self.scale1NameComboBox.setToolTip(QApplication.translate('Tooltip','Choose your scale'))
            self.scale1NameComboBox.setMinimumWidth(150)
            self.scale1ScanButton = QPushButton(QApplication.translate('Button', 'Scan'))
            self.scale1ScanButton.setToolTip(QApplication.translate('Tooltip','Start scanning to discover your scale'))
            self.scale1ScanButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.scale1Weight = QLabel() # displays the current reading
            self.scale1Weight.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.scale1Weight.setMinimumWidth(60)
            self.scale1Weight.setEnabled(False)
            self.scale1TareButton = QPushButton(QApplication.translate('Button', 'Tare'))
            self.scale1TareButton.setToolTip(QApplication.translate('Tooltip','Tare your scale'))
            self.scale1TareButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.scale1TareButton.setEnabled(False)
            if self.aw.scale1_model is None:
                self.scale1NameComboBox.setEnabled(False)
                self.scale1ScanButton.setEnabled(False)
            elif self.aw.scale1_model < len(SUPPORTED_SCALES):
                self.scale1ModelComboBox.setCurrentIndex(self.aw.scale1_model + 1)
                if self.aw.scale1_name is None:
                    self.scale1NameComboBox.setEnabled(False)
                else:
                    self.scale1NameComboBox.setEnabled(True)
            self.scale1ModelComboBox.currentIndexChanged.connect(self.scale1ModelChanged)
            self.scale1NameComboBox.currentIndexChanged.connect(self.scale1NameChanged)
            self.scale1ScanButton.clicked.connect(self.scanScale1)
            self.scale1TareButton.clicked.connect(self.tareScale1)
            self.update_scale1_weight(None)

            if self.aw.scale1_name and self.aw.scale1_id:
                self.updateScale1devices([(self.aw.scale1_name, self.aw.scale1_id)])

            scale1Grid = QGridLayout()
            scale1Grid.addWidget(scale1ModelLabel,0,0)
            scale1Grid.addWidget(self.scale1ModelComboBox,0,1)
            scale1Grid.addWidget(self.scale1NameLabel,1,0)
            scale1Grid.addWidget(self.scale1NameComboBox,1,1)
            scale1Grid.addWidget(self.scale1ScanButton,1,2)
            scale1Grid.addWidget(self.scale1Weight,1,3,Qt.AlignmentFlag.AlignCenter)
            scale1Grid.addWidget(self.scale1TareButton,1,4,Qt.AlignmentFlag.AlignRight)
            scale1Grid.setHorizontalSpacing(10)
            scale1Grid.setVerticalSpacing(10)
            scale1Grid.setContentsMargins(10,10,10,10)
            scale1HLayout = QHBoxLayout()
            scale1HLayout.addLayout(scale1Grid)
            scale1HLayout.addStretch()
            scale1HLayout.setContentsMargins(0,0,0,0)
            scale1Layout = QVBoxLayout()
            scale1Layout.addLayout(scale1HLayout)
            scale1Layout.setContentsMargins(0,0,0,0)

            scale2ModelLabel = QLabel(QApplication.translate('Label','Model'))
            self.scale2ModelComboBox = QComboBox()
            self.scale2ModelComboBox.setToolTip(QApplication.translate('Tooltip','Choose the model of your scale'))
            self.scale2ModelComboBox.setMinimumWidth(150)
            self.scale2ModelComboBox.addItems([''] + [m for (m,_) in SUPPORTED_SCALES])
            self.scale2NameLabel = QLabel(QApplication.translate('Label','Name'))
            self.scale2NameComboBox = QComboBox()
            self.scale2NameComboBox.setToolTip(QApplication.translate('Tooltip','Choose your scale'))
            self.scale2NameComboBox.setMinimumWidth(150)
            self.scale2ScanButton = QPushButton(QApplication.translate('Button', 'Scan'))
            self.scale2ScanButton.setToolTip(QApplication.translate('Tooltip','Start scanning to discover your scale'))
            self.scale2ScanButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.scale2Weight = QLabel() # displays the current reading
            self.scale2Weight.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.scale2Weight.setMinimumWidth(60)
            self.scale2Weight.setEnabled(False)
            self.scale2TareButton = QPushButton(QApplication.translate('Button', 'Tare'))
            self.scale2TareButton.setToolTip(QApplication.translate('Tooltip','Tare your scale'))
            self.scale2TareButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.scale2TareButton.setEnabled(False)
            if self.aw.scale2_model is None:
                self.scale2NameComboBox.setEnabled(False)
                self.scale2ScanButton.setEnabled(False)
            elif self.aw.scale2_model < len(SUPPORTED_SCALES):
                self.scale2ModelComboBox.setCurrentIndex(self.aw.scale2_model + 1)
                if self.aw.scale2_name is None:
                    self.scale2NameComboBox.setEnabled(False)
                else:
                    self.scale2NameComboBox.setEnabled(True)
            self.scale2ModelComboBox.currentIndexChanged.connect(self.scale2ModelChanged)
            self.scale2NameComboBox.currentIndexChanged.connect(self.scale2NameChanged)
            self.scale2ScanButton.clicked.connect(self.scanScale2)
            self.scale2TareButton.clicked.connect(self.tareScale2)
            self.update_scale2_weight(None)

            if self.aw.scale2_name and self.aw.scale2_id:
                self.updateScale2devices([(self.aw.scale2_name, self.aw.scale2_id)])

            scale2Grid = QGridLayout()
            scale2Grid.addWidget(scale2ModelLabel,0,0)
            scale2Grid.addWidget(self.scale2ModelComboBox,0,1)
            scale2Grid.addWidget(self.scale2NameLabel,1,0)
            scale2Grid.addWidget(self.scale2NameComboBox,1,1)
            scale2Grid.addWidget(self.scale2ScanButton,1,2)
            scale2Grid.addWidget(self.scale2Weight,1,3,Qt.AlignmentFlag.AlignCenter)
            scale2Grid.addWidget(self.scale2TareButton,1,4,Qt.AlignmentFlag.AlignRight)
            scale2Grid.setHorizontalSpacing(10)
            scale2Grid.setVerticalSpacing(10)
            scale2Grid.setContentsMargins(10,10,10,10)
            scale2HLayout = QHBoxLayout()
            scale2HLayout.setContentsMargins(0,0,0,0)
            scale2HLayout.addLayout(scale2Grid)
            scale2HLayout.addStretch()
            scale2Layout = QVBoxLayout()
            scale2Layout.addLayout(scale2HLayout)
            scale2Layout.setContentsMargins(0,0,0,0)

            self.taskWebDisplayGreenURL = QLabel()
            self.taskWebDisplayGreenURL.setOpenExternalLinks(True)
            self.taskWebDisplayGreenFlag = QCheckBox()
            self.taskWebDisplayGreenFlag.setToolTip(QApplication.translate('Tooltip','Start/stop the green coffee weighting task web display'))
            self.taskWebDisplayGreenFlag.setChecked(self.aw.taskWebDisplayGreenActive)
            self.taskWebDisplayGreenFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.taskWebDisplayGreenFlag.clicked.connect(self.taskWebDisplayGreen)
            self.taskWebDisplayGreenPortLabel = QLabel(QApplication.translate('Label', 'Port'))
            self.taskWebDisplayGreenPort = QLineEdit(str(self.aw.taskWebDisplayGreenPort))
            self.taskWebDisplayGreenPort.setToolTip(QApplication.translate('Tooltip','IP port of the green coffee weighting task web display'))
            self.taskWebDisplayGreenPort.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.taskWebDisplayGreenPort.setValidator(QRegularExpressionValidator(QRegularExpression(r'^[0-9]{1,4}$'),self))
            self.taskWebDisplayGreenPort.setMaximumWidth(45)
            self.taskWebDisplayGreenPort.editingFinished.connect(self.changeTaskWebDisplayGreenPort)
            self.taskWebDisplayGreenPort.setDisabled(self.aw.taskWebDisplayGreenActive)
            self.taskWebDisplayGreenQRpic = QLabel() # the QLabel holding the QR code image
            if self.aw.taskWebDisplayGreenActive and self.aw.taskWebDisplayGreen_server is not None:
                try:
                    self.setTaskGreenURL(self.getTaskURL(self.aw.taskWebDisplayGreenPort, self.aw.taskWebDisplayGreen_server.indexPath()))
                except Exception: # pylint: disable=broad-except
                    self.taskWebDisplayGreenURL.setText('')
                    self.taskWebDisplayGreenQRpic.setPixmap(QPixmap())
                    self.aw.taskWebDisplayGreenActive = False
            else:
                self.taskWebDisplayGreenURL.setText('')
                self.taskWebDisplayGreenQRpic.setPixmap(QPixmap())
            taskWebDisplayGreenVLayout = QVBoxLayout()
            taskWebDisplayGreenLayout = QHBoxLayout()
            taskWebDisplayGreenLayout.addWidget(self.taskWebDisplayGreenFlag)
            taskWebDisplayGreenLayout.addWidget(self.taskWebDisplayGreenPortLabel)
            taskWebDisplayGreenLayout.addWidget(self.taskWebDisplayGreenPort)
            taskWebDisplayGreenLayout.addWidget(self.taskWebDisplayGreenURL)
            taskWebDisplayGreenLayout.addStretch()
            taskWebDisplayGreenVLayout.addLayout(taskWebDisplayGreenLayout)
            taskWebDisplayGreenHLayout = QHBoxLayout()
            taskWebDisplayGreenHLayout.addStretch()
            taskWebDisplayGreenHLayout.addWidget(self.taskWebDisplayGreenQRpic)
            taskWebDisplayGreenHLayout.addStretch()
            taskWebDisplayGreenVLayout.addLayout(taskWebDisplayGreenHLayout)
            taskWebDisplayGreenVLayout.addStretch()

            self.taskWebDisplayRoastedURL = QLabel()
            self.taskWebDisplayRoastedURL.setOpenExternalLinks(True)
            self.taskWebDisplayRoastedFlag = QCheckBox()
            self.taskWebDisplayRoastedFlag.setToolTip(QApplication.translate('Tooltip','Start/stop the roasted coffee weighting task web display'))
            self.taskWebDisplayRoastedFlag.setChecked(self.aw.taskWebDisplayRoastedActive)
            self.taskWebDisplayRoastedFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.taskWebDisplayRoastedFlag.clicked.connect(self.taskWebDisplayRoasted)
            self.taskWebDisplayRoastedPortLabel = QLabel(QApplication.translate('Label', 'Port'))
            self.taskWebDisplayRoastedPort = QLineEdit(str(self.aw.taskWebDisplayRoastedPort))
            self.taskWebDisplayRoastedPort.setToolTip(QApplication.translate('Tooltip','IP port of the roasted coffee weighting task web display'))
            self.taskWebDisplayRoastedPort.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.taskWebDisplayRoastedPort.setValidator(QRegularExpressionValidator(QRegularExpression(r'^[0-9]{1,4}$'),self))
            self.taskWebDisplayRoastedPort.setMaximumWidth(45)
            self.taskWebDisplayRoastedPort.editingFinished.connect(self.changeTaskWebDisplayRoastedPort)
            self.taskWebDisplayRoastedPort.setDisabled(self.aw.taskWebDisplayRoastedActive)
            self.taskWebDisplayRoastedQRpic = QLabel() # the QLabel holding the QR code image
            if self.aw.taskWebDisplayRoastedActive:
                try:
                    self.setTaskRoastedURL(self.getTaskURL(self.aw.taskWebDisplayRoastedPort, self.aw.taskWebDisplayRoastedIndexPath))
                except Exception: # pylint: disable=broad-except
                    self.taskWebDisplayRoastedURL.setText('')
                    self.taskWebDisplayRoastedQRpic.setPixmap(QPixmap())
                    self.aw.taskWebDisplayRoastedActive = False
            else:
                self.taskWebDisplayRoastedURL.setText('')
                self.taskWebDisplayRoastedQRpic.setPixmap(QPixmap())
            taskWebDisplayRoastedVLayout = QVBoxLayout()
            taskWebDisplayRoastedLayout = QHBoxLayout()
            taskWebDisplayRoastedLayout.addWidget(self.taskWebDisplayRoastedFlag)
            taskWebDisplayRoastedLayout.addWidget(self.taskWebDisplayRoastedPortLabel)
            taskWebDisplayRoastedLayout.addWidget(self.taskWebDisplayRoastedPort)
            taskWebDisplayRoastedLayout.addWidget(self.taskWebDisplayRoastedURL)
            taskWebDisplayRoastedLayout.addStretch()
            taskWebDisplayRoastedVLayout.addLayout(taskWebDisplayRoastedLayout)
            taskWebDisplayRoastedHLayout = QHBoxLayout()
            taskWebDisplayRoastedHLayout.addStretch()
            taskWebDisplayRoastedHLayout.addWidget(self.taskWebDisplayRoastedQRpic)
            taskWebDisplayRoastedHLayout.addStretch()
            taskWebDisplayRoastedVLayout.addLayout(taskWebDisplayRoastedHLayout)
            taskWebDisplayRoastedVLayout.addStretch()

            scale1 = QGroupBox(QApplication.translate('GroupBox', 'Scale {0}').format(1))
            scale1.setLayout(scale1Layout)
            scale2 = QGroupBox(QApplication.translate('GroupBox', 'Scale {0}').format(2))
            scale2.setLayout(scale2Layout)


            # container green
            self.containerGreenTareWeight = QLabel('')
            self.containerGreenTareWeight.setToolTip(QApplication.translate('Tooltip','Weight of your green coffee container'))
            self.containerGreenComboBox = QComboBox()
            self.containerGreenComboBox.setToolTip(QApplication.translate('Tooltip','Identify your green coffee container and its weight'))
            self.containerGreenComboBox.setMaximumWidth(120)
            self.containerGreenComboBox.setMinimumWidth(120)
            self.updateGreenContainerPopup()
            self.containerGreenComboBox.currentIndexChanged.connect(self.greenContainerChanged)
            self.containerGreenComboBox.setCurrentIndex(self.container_menu_idx(self.aw.container1_idx))
            self.updateGreenContainerWeight()

            containerGreenGridLayout = QGridLayout()
            containerGreenGridLayout.addWidget(self.containerGreenComboBox,0,0)
            containerGreenGridLayout.addWidget(self.containerGreenTareWeight,0,1)

            containerGreenHLayout = QHBoxLayout()
            containerGreenHLayout.addLayout(containerGreenGridLayout)
            containerGreenHLayout.addStretch()

            # container roasted
            self.containerRoastedTareWeight = QLabel('')
            self.containerRoastedTareWeight.setToolTip(QApplication.translate('Tooltip','Weight of your roasted coffee container'))
            self.containerRoastedComboBox = QComboBox()
            self.containerRoastedComboBox.setToolTip(QApplication.translate('Tooltip','Identify your roasted coffee container and its weight'))
            self.containerRoastedComboBox.setMaximumWidth(120)
            self.containerRoastedComboBox.setMinimumWidth(120)
            self.updateRoastedContainerPopup()
            self.containerRoastedComboBox.currentIndexChanged.connect(self.roastedContainerChanged)
            self.containerRoastedComboBox.setCurrentIndex(self.container_menu_idx(self.aw.container2_idx))
            self.updateRoastedContainerWeight()

            containerRoastedGridLayout = QGridLayout()
            containerRoastedGridLayout.addWidget(self.containerRoastedComboBox,0,0)
            containerRoastedGridLayout.addWidget(self.containerRoastedTareWeight,0,1)

            containerRoastedHLayout = QHBoxLayout()
            containerRoastedHLayout.addLayout(containerRoastedGridLayout)
            containerRoastedHLayout.addStretch()

            # Bucket Hobbock, Container, Bin
            containerGreen = QGroupBox(QApplication.translate('GroupBox','Container Green'))
            containerGreen.setLayout(containerGreenHLayout)
            containerRoasted = QGroupBox(QApplication.translate('GroupBox','Container Roasted'))
            containerRoasted.setLayout(containerRoastedHLayout)

            taskGreen = QGroupBox(QApplication.translate('GroupBox', 'Task Green'))
            taskGreen.setLayout(taskWebDisplayGreenVLayout)
            taskRoasted = QGroupBox(QApplication.translate('GroupBox', 'Task Roasted'))
            taskRoasted.setLayout(taskWebDisplayRoastedVLayout)

            tab8Layout.addWidget(scale1,0,0)
            tab8Layout.addWidget(scale2,0,1)
            tab8Layout.addWidget(containerGreen,1,0)
            tab8Layout.addWidget(containerRoasted,1,1)
            tab8Layout.addWidget(taskGreen,2,0)
            tab8Layout.addWidget(taskRoasted,2,1)
        else:
            naLayout = QHBoxLayout()
            notavailLable = QLabel(QApplication.translate('Label', 'Not available in ArtisanViewer'))
            naLayout.addStretch()
            naLayout.addWidget(notavailLable)
            naLayout.addStretch()
            tab8LayoutOFF.addStretch()
            tab8LayoutOFF.addLayout(naLayout)
            tab8LayoutOFF.addStretch()

        #main tab widget
        self.TabWidget = QTabWidget()
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        self.TabWidget.addTab(C1Widget,QApplication.translate('Tab','ET/BT'))
        C2Widget = QWidget()
        C2Widget.setLayout(tab2Layout)
        self.TabWidget.addTab(C2Widget,QApplication.translate('Tab','Extra Devices'))
        C3Widget = QWidget()
        C3Widget.setLayout(tab3Layout)
        self.TabWidget.addTab(C3Widget,QApplication.translate('Tab','Symb ET/BT'))
        C4Widget = QWidget()
        C4Widget.setLayout(tab4Layout)
        self.TabWidget.addTab(C4Widget,'Phidgets')
        C5Widget = QWidget()
        C5Widget.setLayout(tab5Layout)
        self.TabWidget.addTab(C5Widget,'Yoctopuce')
        C6Widget = QWidget()
        C6Widget.setLayout(tab6Layout)
        self.TabWidget.addTab(C6Widget,QApplication.translate('Tab','Ambient'))
        C7Widget = QWidget()
        C7Widget.setLayout(tab7Layout)
        self.TabWidget.addTab(C7Widget,QApplication.translate('Tab','Networks'))
        self.TabWidget.currentChanged.connect(self.tabSwitched)
        C8Widget = QWidget()
        if not self.aw.app.artisanviewerMode:
            C8Widget.setLayout(tab8Layout)
        else:
            C8Widget.setLayout(tab8LayoutOFF)
        self.TabWidget.addTab(C8Widget,QApplication.translate('Tab','Scales'))
        self.TabWidget.currentChanged.connect(self.tabSwitched)
        #incorporate layouts
        Mlayout = QVBoxLayout()
        Mlayout.addWidget(self.TabWidget)
        Mlayout.addLayout(buttonLayout)
        Mlayout.setSpacing(0)
        Mlayout.setContentsMargins(5,10,5,5)
        self.setLayout(Mlayout)
        if platform.system() != 'Windows':
            ok_button: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button is not None:
                ok_button.setFocus()
        else:
            self.TabWidget.setFocus()
        settings = QSettings()
        if settings.contains('DeviceAssignmentGeometry'):
            self.restoreGeometry(settings.value('DeviceAssignmentGeometry'))

        # we set the active tab with a QTimer after the tabbar has been rendered once, as otherwise
        # some tabs are not rendered at all on Windows using Qt v6.5.1 (https://bugreports.qt.io/projects/QTBUG/issues/QTBUG-114204?filter=allissues)
        QTimer.singleShot(50, self.setActiveTab)


    @pyqtSlot()
    def changeTaskWebDisplayGreenPort(self) -> None:
        try:
            self.aw.taskWebDisplayGreenPort = int(str(self.taskWebDisplayGreenPort.text()))
        except Exception: # pylint: disable=broad-except
            pass

    @pyqtSlot(int)
    def scale1ModelChanged(self, i:int) -> None:
        if i > 0 and len(SUPPORTED_SCALES) > i-1 and len(SUPPORTED_SCALES[i-1]) > 0:
            self.aw.scale1_model = i-1
            self.scale1NameComboBox.setEnabled(False)
            self.scale1ScanButton.setEnabled(True)
        else:
            self.aw.scale1_name = None
            self.aw.scale1_model = None
            self.scale1NameComboBox.clear()
            self.scale1NameComboBox.setEnabled(False)
            self.scale1ScanButton.setEnabled(False)
            self.update_scale1_weight(None)

    @pyqtSlot(int)
    def scale1NameChanged(self, i:int) -> None:
        if 0 <= i < len(self.scale1_devices) and self.aw.scale1_model is not None:
            self.aw.scale1_name = self.scale1_devices[i][0]
            self.aw.scale1_id = self.scale1_devices[i][1]
            scale = self.aw.scale_manager.get_scale(self.aw.scale1_model, self.aw.scale1_id, self.aw.scale1_name)
            self.aw.scale_manager.set_scale1(scale)
            if scale is not None:
                scale.set_connected_handler(self.scale1connected)
                scale.set_disconnected_handler(self.scale1disconnected)
                scale.weight_changed_signal.connect(self.scale1_weight_changed) # type:ignore[call-overload]
                scale.connect_scale()
        # i == -1 if self.scale1NameComboBox is empty!
        else:
            scale1 = self.aw.scale_manager.get_scale1()
            if scale1 is not None:
                scale1.weight_changed_signal.disconnect() # type:ignore[call-overload]
                scale1.disconnect_scale()

    def scale1connected(self) -> None:
        self.aw.sendmessageSignal.emit(QApplication.translate('Message', '{} connected').format(self.aw.scale1_name),True,None)
        self.scale1Weight.setEnabled(True)
        self.scale1TareButton.setEnabled(True)

    def scale1disconnected(self) -> None:
        self.aw.sendmessageSignal.emit(QApplication.translate('Message', '{} disconnected').format(self.aw.scale1_name),True,None)
        self.scale1Weight.setEnabled(False)
        self.scale1TareButton.setEnabled(False)
        self.update_scale1_weight(None)

    @pyqtSlot(int)
    def scale1_weight_changed(self, w:int) -> None:
        self.update_scale1_weight(w)

    # returns formatted weight converted to current weight unit
    def format_scale_weight(self, w:Optional[float]) -> str:
        if w is None:
            return '----'
        unit = weight_units.index(self.aw.qmc.weight[2])
        if unit == 0: # g selected
            # metric
            return f'{w:.0f}g' # never show decimals for g
        if unit == 1: # kg selected
            # metric (always keep the accuracy to the g
            return f'{w/1000:.3f}kg'
        # non-metric
        v = convertWeight(w,0,weight_units.index(self.aw.qmc.weight[2]))
        return f'{v:.2f}{self.aw.qmc.weight[2].lower()}'

    def update_scale1_weight(self, weight:Optional[float]) -> None:
        self.scale1_weight = weight
        if self.aw.scale1_name is not None and self.aw.scale1_id is not None:
            self.scale1Weight.setText(self.format_scale_weight(self.scale1_weight))
        else:
            self.scale1Weight.setText('')

    def updateScale1devices(self, devices:ScaleSpecs) -> None:
        self.scale1_devices = devices
        self.scale1NameComboBox.clear()
        if self.scale1_devices:
            self.scale1NameComboBox.addItems([d[0] for d in self.scale1_devices])
            self.scale1NameComboBox.setEnabled(True)

    @pyqtSlot(bool)
    def scanScale1(self, _:bool = False) -> None:
        if self.aw.scale1_model is not None:
            with wait_cursor():
                devices:ScaleSpecs = self.aw.scale_manager.scan_for_scales(self.aw.scale1_model)
                self.updateScale1devices(devices)
                if devices:
                    self.scale1NameComboBox.setEnabled(True)
                else:
                    self.scale1NameComboBox.setEnabled(False)

    @pyqtSlot(bool)
    def tareScale1(self, _:bool = False) -> None:
        scale = self.aw.scale_manager.get_scale1()
        if scale is not None:
            scale.tare_scale()

    @pyqtSlot(int)
    def scale2ModelChanged(self, i:int) -> None:
        if i > 0 and len(SUPPORTED_SCALES) > i-1 and len(SUPPORTED_SCALES[i-1]) > 0:
            self.aw.scale2_model = i-1
            self.scale2NameComboBox.setEnabled(False)
            self.scale2ScanButton.setEnabled(True)
        else:
            self.aw.scale2_name = None
            self.aw.scale2_model = None
            self.scale2NameComboBox.clear()
            self.scale2NameComboBox.setEnabled(False)
            self.scale2ScanButton.setEnabled(False)
            self.update_scale2_weight(None)

    @pyqtSlot(int)
    def scale2NameChanged(self, i:int) -> None:
        if 0 <= i < len(self.scale2_devices) and self.aw.scale2_model is not None:
            self.aw.scale2_name = self.scale2_devices[i][0]
            self.aw.scale2_id = self.scale2_devices[i][1]
            scale = self.aw.scale_manager.get_scale(self.aw.scale2_model, self.aw.scale2_id, self.aw.scale2_name)
            self.aw.scale_manager.set_scale2(scale)
            if scale is not None:
                scale.set_connected_handler(self.scale2connected)
                scale.set_disconnected_handler(self.scale2disconnected)
                scale.weight_changed_signal.connect(self.scale2_weight_changed) # type:ignore[call-overload]
                scale.connect_scale()
        # i == -1 if self.scale2NameComboBox is empty!
        else:
            scale2 = self.aw.scale_manager.get_scale2()
            if scale2 is not None:
                scale2.weight_changed_signal.disconnect() # type:ignore[call-overload]
                scale2.disconnect_scale()

    @pyqtSlot(int)
    def scale2_weight_changed(self, w:int) -> None:
        self.update_scale2_weight(w)

    def update_scale2_weight(self, weight:Optional[float]) -> None:
        self.scale2_weight = weight
        if self.aw.scale2_name is not None and self.aw.scale2_id is not None:
            self.scale2Weight.setText(self.format_scale_weight(self.scale2_weight))
        else:
            self.scale2Weight.setText('')

    def scale2connected(self) -> None:
        self.aw.sendmessageSignal.emit(QApplication.translate('Message', '{} connected').format(self.aw.scale2_name),True,None)
        self.scale2Weight.setEnabled(True)
        self.scale2TareButton.setEnabled(True)

    def scale2disconnected(self) -> None:
        self.aw.sendmessageSignal.emit(QApplication.translate('Message', '{} disconnected').format(self.aw.scale2_name),True,None)
        self.scale2Weight.setEnabled(False)
        self.scale2TareButton.setEnabled(False)
        self.update_scale2_weight(None)

    def updateScale2devices(self, devices:ScaleSpecs) -> None:
        self.scale2_devices = devices
        self.scale2NameComboBox.clear()
        if self.scale2_devices:
            self.scale2NameComboBox.addItems([d[0] for d in self.scale2_devices])
            self.scale2NameComboBox.setEnabled(True)

    @pyqtSlot(bool)
    def scanScale2(self, _:bool = False) -> None:
        if self.aw.scale2_model is not None:
            with wait_cursor():
                devices:ScaleSpecs = self.aw.scale_manager.scan_for_scales(self.aw.scale2_model)
                self.updateScale2devices(devices)
                if devices:
                    self.scale2NameComboBox.setEnabled(True)
                else:
                    self.scale2NameComboBox.setEnabled(False)

    @pyqtSlot(bool)
    def tareScale2(self, _:bool = False) -> None:
        scale = self.aw.scale_manager.get_scale2()
        if scale is not None:
            scale.tare_scale()

    @staticmethod
    def container_menu_idx(i:int) -> int: # takes a container idx and returns the index of the corresponding menu item
        return i + 3 # skip <edit>, separator and empty index

    @pyqtSlot()
    def updateGreenContainerPopup(self) -> None:
        prev_item_count = self.containerGreenComboBox.count()
        with QSignalBlocker(self.containerGreenComboBox): # blocking all signals, especially its currentIndexChanged connected to tareChanged which would lead to cycles
            self.containerGreenComboBox.clear()
            self.containerGreenComboBox.addItem(f"<{QApplication.translate('Label','edit')}>")
            self.containerGreenComboBox.insertSeparator(2)
            self.containerGreenComboBox.addItem('')
            self.containerGreenComboBox.addItems(self.aw.qmc.container_names)
            width = self.containerGreenComboBox.minimumSizeHint().width()
            view: Optional[QAbstractItemView] = self.containerGreenComboBox.view()
            if view is not None:
                view.setMinimumWidth(width)
        if self.containerGreenComboBox.count() > prev_item_count:
            # if item list is longer (new items added), we select the last item
            self.aw.container1_idx = self.containerGreenComboBox.count() - 4
        if len(self.aw.qmc.container_weights) > self.aw.container1_idx:
            self.containerGreenComboBox.setCurrentIndex(self.container_menu_idx(self.aw.container1_idx))
        else:
            self.containerGreenComboBox.setCurrentIndex(2) # reset to the empty entry
            self.aw.container1_idx = -1

    @pyqtSlot(int)
    def greenContainerChanged(self, i:int) -> None:
        if i == 0:
            self.containerGreenComboBox.setCurrentIndex(self.container_menu_idx(self.aw.container1_idx))
            tareDLG = tareDlg(self,self.aw, self.get_scale1_weight)
            tareDLG.tare_updated_signal.connect(self.updateGreenContainerPopup)
            tareDLG.show()
        else:
            self.aw.container1_idx = i - 3
            # update displayed scale weight
            self.updateGreenContainerWeight()

    def updateGreenContainerWeight(self) -> None:
        weight = self.aw.qmc.get_container_weight(self.aw.container1_idx)
        if weight is None:
            self.containerGreenTareWeight.setText('')
        else:
            self.containerGreenTareWeight.setText(render_weight(weight, 0,  weight_units.index(self.aw.qmc.weight[2])))

    def get_scale1_weight(self) -> Optional[float]:
        return self.scale1_weight


    @pyqtSlot()
    def updateRoastedContainerPopup(self) -> None:
        prev_item_count = self.containerRoastedComboBox.count()
        with QSignalBlocker(self.containerRoastedComboBox): # blocking all signals, especially its currentIndexChanged connected to tareChanged which would lead to cycles
            self.containerRoastedComboBox.clear()
            self.containerRoastedComboBox.addItem(f"<{QApplication.translate('Label','edit')}>")
            self.containerRoastedComboBox.insertSeparator(2)
            self.containerRoastedComboBox.addItem('')
            self.containerRoastedComboBox.addItems(self.aw.qmc.container_names)
            width = self.containerRoastedComboBox.minimumSizeHint().width()
            view: Optional[QAbstractItemView] = self.containerGreenComboBox.view()
            if view is not None:
                view.setMinimumWidth(width)
        if self.containerRoastedComboBox.count() > prev_item_count:
            # if item list is longer (new items added), we select the last item
            self.aw.container2_idx = self.containerRoastedComboBox.count() - 4
        if len(self.aw.qmc.container_weights) > self.aw.container2_idx:
            self.containerRoastedComboBox.setCurrentIndex(self.container_menu_idx(self.aw.container2_idx))
        else:
            self.containerRoastedComboBox.setCurrentIndex(2) # reset to the empty entry
            self.aw.container2_idx = -1

    @pyqtSlot(int)
    def roastedContainerChanged(self, i:int) -> None:
        if i == 0:
            self.containerRoastedComboBox.setCurrentIndex(self.container_menu_idx(self.aw.container2_idx))
            tareDLG = tareDlg(self,self.aw, self.get_scale2_weight)
            tareDLG.tare_updated_signal.connect(self.updateRoastedContainerPopup)
            tareDLG.show()
        else:
            self.aw.container2_idx = i - 3
            # update displayed scale weight
            self.updateRoastedContainerWeight()

    def updateRoastedContainerWeight(self) -> None:
        weight = self.aw.qmc.get_container_weight(self.aw.container2_idx)
        if weight is None:
            self.containerRoastedTareWeight.setText('')
        else:
            self.containerRoastedTareWeight.setText(render_weight(weight, 0,  weight_units.index(self.aw.qmc.weight[2])))

    def get_scale2_weight(self) -> Optional[float]:
        return self.scale2_weight


    @pyqtSlot(bool)
    def taskWebDisplayGreen(self, b:bool = False) -> None:
        res = False
        if b:
            try:
                self.changeTaskWebDisplayGreenPort()
                res = self.aw.startWebGreen()
                if res and self.aw.taskWebDisplayGreen_server is not None:
                    self.setTaskGreenURL(self.getTaskURL(self.aw.taskWebDisplayGreenPort, self.aw.taskWebDisplayGreen_server.indexPath())) # this might fail if socket cannot be established
                    self.taskWebDisplayGreenFlag.setChecked(True)
                    self.taskWebDisplayGreenPort.setDisabled(True)
            except Exception as e: # pylint: disable=broad-except
                self.aw.sendmessage(str(e))
                res = False
                self.aw.taskWebDisplayGreenActive = False
        else:
            self.aw.stopWebGreen()
        if not res:
            self.taskWebDisplayGreenFlag.setChecked(False)
            self.taskWebDisplayGreenPort.setDisabled(False)
            self.taskWebDisplayGreenURL.setText('')
            self.taskWebDisplayGreenQRpic.setPixmap(QPixmap())

    def setTaskGreenURL(self, url:str) -> None:
        # set URL label
        self.taskWebDisplayGreenURL.setText(f'<a href="{url}">{url}</a>')
        # set QR label
        try:
            from artisanlib.qrcode import QRlabel
            qr = QRlabel(url)
            self.taskWebDisplayGreenQRpic.setPixmap(qr.make_image().pixmap())
        except Exception: # pylint: disable=broad-except
            pass

    @pyqtSlot()
    def changeTaskWebDisplayRoastedPort(self) -> None:
        try:
            self.aw.taskWebDisplayRoastedPort = int(str(self.taskWebDisplayRoastedPort.text()))
        except Exception: # pylint: disable=broad-except
            pass

    @pyqtSlot(bool)
    def taskWebDisplayRoasted(self, b:bool = False) -> None:
        res = False
        if b:
            try:
                self.changeTaskWebDisplayRoastedPort()
                res = self.aw.startWebRoasted()
                if res:
                    self.setTaskRoastedURL(self.getTaskURL(self.aw.taskWebDisplayRoastedPort, self.aw.taskWebDisplayRoastedIndexPath)) # this might fail if socket cannot be established
                    self.taskWebDisplayRoastedFlag.setChecked(True)
                    self.taskWebDisplayRoastedPort.setDisabled(True)
            except Exception as e: # pylint: disable=broad-except
                self.aw.sendmessage(str(e))
                res = False
                self.aw.taskWebDisplayRoastedActive = False
        else:
            self.aw.stopWebRoasted()
        if not res:
            self.taskWebDisplayRoastedFlag.setChecked(False)
            self.taskWebDisplayRoastedPort.setDisabled(False)
            self.taskWebDisplayRoastedURL.setText('')
            self.taskWebDisplayRoastedQRpic.setPixmap(QPixmap())

    def setTaskRoastedURL(self, url:str) -> None:
        # set URL label
        self.taskWebDisplayRoastedURL.setText(f'<a href="{url}">{url}</a>')
        # set QR label
        try:
            from artisanlib.qrcode import QRlabel
            qr = QRlabel(url)
            self.taskWebDisplayRoastedQRpic.setPixmap(qr.make_image().pixmap())
        except Exception: # pylint: disable=broad-except
            pass

    @staticmethod
    def getTaskURL(port:int, index_path:str) -> str:
        import socket
#        # use Artisan's host IP address
#        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#        s.connect(('8.8.8.8', 80))
#        localIP = s.getsockname()[0]
#        s.close()
#        return f'http://{str(localIP)}:{str(port)}/{index_path}'
        # use Artisan's host name (more stable over DHCP/zeroconf updates), but cannot be accessed on Windows from iPhone
        if sys.platform.startswith('darwin'):
            import subprocess
            host = subprocess.check_output(['scutil', '--get', 'LocalHostName']).decode('utf-8')
        else:
            # on Linux/Windows the mdns name is created by appending ".local" to the hostname
            host = socket.gethostname()
        return f"http://{host.strip().replace(' ', '_').casefold()}.local:{str(port)}/{index_path}"




    @pyqtSlot()
    def setActiveTab(self) -> None:
        self.TabWidget.setCurrentIndex(self.activeTab)
        # we create the device table here instead of __init__ as otherwise setting the columnWidth to the saved defaults has no effect using Qt 6.2.2
        self.createDeviceTable()

    @pyqtSlot(int)
    def yoctoBoxRemoteFlagStateChanged(self, _:int) -> None:
        self.aw.qmc.yoctoRemoteFlag = not self.aw.qmc.yoctoRemoteFlag
        self.yoctoServerId.setEnabled(self.aw.qmc.yoctoRemoteFlag)

    @pyqtSlot(int)
    def phidgetRemoteStateChanged(self, _:int) -> None:
        self.aw.qmc.phidgetRemoteFlag = not self.aw.qmc.phidgetRemoteFlag
        self.phidgetServerId.setEnabled(self.aw.qmc.phidgetRemoteFlag)
        self.phidgetPassword.setEnabled(self.aw.qmc.phidgetRemoteFlag)
        self.phidgetPort.setEnabled(self.aw.qmc.phidgetRemoteFlag)
        self.phidgetBoxRemoteOnlyFlag.setEnabled(self.aw.qmc.phidgetRemoteFlag)

    @pyqtSlot(int)
    def santokerSerialStateChanged(self, i:int) -> None:
        self.aw.santokerSerial = bool(i)
        if self.aw.santokerSerial:
            self.aw.santokerBLE = False

    @pyqtSlot(int)
    def santokerNetworkStateChanged(self, i:int) -> None:
        self.aw.santokerSerial = not bool(i)
        if not self.aw.santokerSerial:
            self.aw.santokerBLE = False
        self.santokerHost.setEnabled(not self.aw.santokerSerial)
        self.santokerPort.setEnabled(not self.aw.santokerSerial)

    @pyqtSlot(int)
    def santokerBLEStateChanged(self, i:int) -> None:
        self.aw.santokerBLE = bool(i)
        if self.aw.santokerBLE:
            self.aw.santokerSerial = False

    @pyqtSlot(int)
    def kaleidoSerialStateChanged(self, _:int) -> None:
        self.aw.kaleidoSerial = not self.aw.kaleidoSerial
        self.kaleidoHost.setEnabled(not self.aw.kaleidoSerial)
        self.kaleidoPort.setEnabled(not self.aw.kaleidoSerial)

    @pyqtSlot(str)
    def phidgetHostChanged(self, s:str) -> None:
        self.phidgetPassword.setEnabled(s != '')

    @pyqtSlot(int)
    def changeOutprogramFlag(self,_:int) -> None:
        self.aw.ser.externaloutprogramFlag = not self.aw.ser.externaloutprogramFlag

    @pyqtSlot(int)
    def asyncFlagStateChanged1048(self, x:int) -> None:
        try:
            sender = cast(QCheckBox, self.sender())
            i = self.asyncCheckBoxes1048.index(sender)
            if x == 0:
                # disable ChangeTrigger selection
                self.changeTriggerCombos1048[i].setEnabled(False)
            else:
                # enable ChangeTrigger selection
                self.changeTriggerCombos1048[i].setEnabled(True)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    @pyqtSlot(int)
    def asyncFlagStateChanged1045(self, x:int) -> None:
        if x == 0:
            # disable ChangeTrigger selection
            self.changeTriggerCombos1045.setEnabled(False)
        else:
            # enable ChangeTrigger selection
            self.changeTriggerCombos1045.setEnabled(True)

    @pyqtSlot(int)
    def asyncFlagStateChanged1200(self, x:int) -> None:
        if x == 0:
            # disable ChangeTrigger selection
            self.changeTriggerCombo1200.setEnabled(False)
        else:
            # enable ChangeTrigger selection
            self.changeTriggerCombo1200.setEnabled(True)

    @pyqtSlot(int)
    def asyncFlagStateChanged1200_2(self, x:int) -> None:
        if x == 0:
            # disable ChangeTrigger selection
            self.changeTriggerCombo1200_2.setEnabled(False)
        else:
            # enable ChangeTrigger selection
            self.changeTriggerCombo1200_2.setEnabled(True)

    @pyqtSlot(int)
    def asyncFlagStateChanged(self, x:int) -> None:
        try:
            sender = cast(QCheckBox, self.sender())
            i = self.asyncCheckBoxes.index(sender)
            if x == 0:
                # disable DataRate selection
                self.changeTriggerCombos[i].setEnabled(False)
            else:
                # enable ChangeTrigger and if that is 0 also DataRate selection
                self.changeTriggerCombos[i].setEnabled(True)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    @staticmethod
    def createItems(strs:List[str]) -> List[QStandardItem]:
        items:List[QStandardItem] = []
        for st in strs:
            item = QStandardItem(st)
            items.append(item)
        return items

    @pyqtSlot(int)
    def PIDfirmwareToggle(self, i:int) -> None:
        if i:
            self.aw.qmc.PIDbuttonflag = True
        else:
            self.aw.qmc.PIDbuttonflag = False
        self.aw.showControlButton()

    @pyqtSlot(int)
    def showControlbuttonToggle(self, i:int) -> None:
        if i:
            self.aw.qmc.Controlbuttonflag = True
        else:
            self.aw.qmc.Controlbuttonflag = False
        self.aw.showControlButton()

    @staticmethod
    def centeredCheckBox() -> Tuple[QWidget, QCheckBox]:
        widget = QWidget()
        checkBox = QCheckBox()
        checkBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QHBoxLayout(widget)
        layout.addWidget(checkBox)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0,0,0,0)
        return widget, checkBox

    @staticmethod
    def centeredCheckBox_isChecked(widget:Optional[QWidget]) -> bool:
        if widget is not None:
            layout = widget.layout()
            if layout is not None:
                item0 = layout.itemAt(0)
                if item0 is not None:
                    checkBox = item0.widget()
                    if checkBox is not None and isinstance(checkBox, QCheckBox):
                        return checkBox.isChecked() # type:ignore[reportAttributeAccessIssue, unused-ignore] # pyright reports isChecked not known for QWidget
        return False

    def createDeviceTable(self) -> None:
        try:
            columns = 15
            if self.devicetable is not None and self.devicetable.columnCount() == columns:
                # rows have been already established
                # save the current columnWidth to reset them after table creation
                self.aw.qmc.devicetablecolumnwidths = [self.devicetable.columnWidth(c) for c in range(self.devicetable.columnCount())]

            nddevices = len(self.aw.qmc.extradevices)
            #self.devicetable.clear() # this crashes Ubuntu 16.04
#            if nddevices != 0:
#                self.devicetable.clearContents() # this crashes Ubuntu 16.04 if device table is empty
#            self.devicetable.clearSelection()

            self.devicetable.setRowCount(nddevices)
            self.devicetable.setColumnCount(columns)
            self.devicetable.setHorizontalHeaderLabels([QApplication.translate('Table', 'Device'),
                                                        QApplication.translate('Table', 'Color 1'),
                                                        QApplication.translate('Table', 'Color 2'),
                                                        QApplication.translate('Table', 'Label 1'),
                                                        QApplication.translate('Table', 'Label 2'),
                                                        QApplication.translate('Table', 'y1(x)'),
                                                        QApplication.translate('Table', 'y2(x)'),
                                                        QApplication.translate('Table', 'LCD 1'),
                                                        QApplication.translate('Table', 'LCD 2'),
                                                        QApplication.translate('Table', 'Curve 1'),
                                                        QApplication.translate('Table', 'Curve 2'),
                                                        deltaLabelUTF8 + ' ' + QApplication.translate('GroupBox','Axis') + ' 1',
                                                        deltaLabelUTF8 + ' ' + QApplication.translate('GroupBox','Axis') + ' 2',
                                                        QApplication.translate('Table', 'Fill 1'),
                                                        QApplication.translate('Table', 'Fill 2')])
            self.devicetable.setAlternatingRowColors(True)
            self.devicetable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.devicetable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.devicetable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

#            self.devicetable.setStyleSheet("selection-background-color: transparent;") # avoid the selection color to shine through transparent device color items

            self.devicetable.setShowGrid(True)
            vheader = self.devicetable.verticalHeader()
            if vheader is not None:
                vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

            fixed_size_sections = [7,8,9,10,11,12,13,14]
            if nddevices:
                dev = self.aw.qmc.devices[:]             #deep copy
                limit = len(dev)
                for _ in range(limit):
                    for i, _ in enumerate(dev):
                        if dev[i][0] == '-' or dev[i] == 'NONE': # non manual device or deactivated device in extra device list
                            dev.pop(i)              #note: pop() makes the list smaller
                            break
                devices = sorted(((x[1:] if x.startswith('+') else x) for x in dev), key=lambda x: (x[1:] if x.startswith('+') else x))
                for i in range(nddevices):
                    try:
                        # 0: device type
                        typeComboBox =  MyContentLimitedQComboBox()
#                        typeComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow) # default
                        typeComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
#                        typeComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
                        typeComboBox.addItems(devices[:])
                        try:
                            dev_name = self.aw.qmc.devices[max(0,self.aw.qmc.extradevices[i]-1)]
                            if dev_name[0] == '+':
                                dev_name = dev_name[1:]
                            typeComboBox.setCurrentIndex(devices.index(dev_name))
                        except Exception: # pylint: disable=broad-except
                            pass
                        # 1: color 1
                        color1Button = QPushButton(self.aw.qmc.extradevicecolor1[i])
                        color1Button.clicked.connect(self.setextracolor1)
                        textcolor = self.aw.labelBorW(self.aw.qmc.extradevicecolor1[i])
                        color1Button.setStyleSheet(f"selection-background-color: transparent; border: none; outline: none; background-color: rgba{ImageColor.getcolor(self.aw.qmc.extradevicecolor1[i], 'RGBA')}; color: {textcolor}")
                        color1Button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                        # 2: color 2
                        color2Button = QPushButton(self.aw.qmc.extradevicecolor2[i])
                        color2Button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                        color2Button.clicked.connect(self.setextracolor2)
                        textcolor = self.aw.labelBorW(self.aw.qmc.extradevicecolor2[i])
                        color2Button.setStyleSheet(f"selection-background-color: transparent; border: none; outline: none; background-color: rgba{ImageColor.getcolor(self.aw.qmc.extradevicecolor2[i], 'RGBA')}; color: {textcolor}")
                        # 3+4: name 1 + 2
                        name1edit = QLineEdit(self.aw.qmc.extraname1[i])
                        name2edit = QLineEdit(self.aw.qmc.extraname2[i])
                        # 5+6: math 1 + 2
                        mexpr1edit = QLineEdit(self.aw.qmc.extramathexpression1[i])
                        mexpr2edit = QLineEdit(self.aw.qmc.extramathexpression2[i])
                        mexpr1edit.setToolTip(QApplication.translate('Tooltip','Example: 100 + 2*x'))
                        mexpr2edit.setToolTip(QApplication.translate('Tooltip','Example: 100 + x'))
                        # 7: lcd 1
                        LCD1widget, LCD1visibilityQCheckBox = self.centeredCheckBox()
                        if self.aw.extraLCDvisibility1[i]:
                            LCD1visibilityQCheckBox.setCheckState(Qt.CheckState.Checked)
                        else:
                            LCD1visibilityQCheckBox.setCheckState(Qt.CheckState.Unchecked)
                        LCD1visibilityQCheckBox.stateChanged.connect(self.updateLCDvisibility1)
                        # 8: lcd 2
                        LCD2widget, LCD2visibilityQCheckBox = self.centeredCheckBox()
                        if self.aw.extraLCDvisibility2[i]:
                            LCD2visibilityQCheckBox.setCheckState(Qt.CheckState.Checked)
                        else:
                            LCD2visibilityQCheckBox.setCheckState(Qt.CheckState.Unchecked)
                        LCD2visibilityQCheckBox.stateChanged.connect(self.updateLCDvisibility2)
                        # 9: curve 1
                        Curve1widget, Curve1visibilityQCheckBox = self.centeredCheckBox()
                        if self.aw.extraCurveVisibility1[i]:
                            Curve1visibilityQCheckBox.setCheckState(Qt.CheckState.Checked)
                        else:
                            Curve1visibilityQCheckBox.setCheckState(Qt.CheckState.Unchecked)
                        Curve1visibilityQCheckBox.stateChanged.connect(self.updateCurveVisibility1)
                        # 10: curve 2
                        Curve2widget, Curve2visibilityQCheckBox = self.centeredCheckBox()
                        if self.aw.extraCurveVisibility2[i]:
                            Curve2visibilityQCheckBox.setCheckState(Qt.CheckState.Checked)
                        else:
                            Curve2visibilityQCheckBox.setCheckState(Qt.CheckState.Unchecked)
                        Curve2visibilityQCheckBox.stateChanged.connect(self.updateCurveVisibility2)
                        # 11: delta 1
                        Delta1widget, Delta1QCheckBox = self.centeredCheckBox()
                        if self.aw.extraDelta1[i]:
                            Delta1QCheckBox.setCheckState(Qt.CheckState.Checked)
                        else:
                            Delta1QCheckBox.setCheckState(Qt.CheckState.Unchecked)
                        Delta1QCheckBox.stateChanged.connect(self.updateDelta1)
                        # 12: delta 2
                        Delta2widget, Delta2QCheckBox = self.centeredCheckBox()
                        if self.aw.extraDelta2[i]:
                            Delta2QCheckBox.setCheckState(Qt.CheckState.Checked)
                        else:
                            Delta2QCheckBox.setCheckState(Qt.CheckState.Unchecked)
                        Delta2QCheckBox.stateChanged.connect(self.updateDelta2)
                        # 13: fill 1
                        Fill1SpinBox = QSpinBox()
                        Fill1SpinBox.setSingleStep(1)
                        Fill1SpinBox.setRange(0,100)
                        Fill1SpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
                        Fill1SpinBox.setValue(int(self.aw.extraFill1[i]))
                        Fill1SpinBox.editingFinished.connect(self.updateFill1)
                        # 14: fill 2
                        Fill2SpinBox = QSpinBox()
                        Fill2SpinBox.setSingleStep(1)
                        Fill2SpinBox.setRange(0,100)
                        Fill2SpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
                        Fill2SpinBox.setValue(int(self.aw.extraFill2[i]))
                        Fill2SpinBox.editingFinished.connect(self.updateFill2)
                        #add widgets to the table
                        self.devicetable.setCellWidget(i,0,typeComboBox)
                        self.devicetable.setCellWidget(i,1,color1Button)
                        self.devicetable.setCellWidget(i,2,color2Button)
                        self.devicetable.setCellWidget(i,3,name1edit)
                        self.devicetable.setCellWidget(i,4,name2edit)
                        self.devicetable.setCellWidget(i,5,mexpr1edit)
                        self.devicetable.setCellWidget(i,6,mexpr2edit)
                        self.devicetable.setCellWidget(i,7,LCD1widget)
                        self.devicetable.setCellWidget(i,8,LCD2widget)
                        self.devicetable.setCellWidget(i,9,Curve1widget)
                        self.devicetable.setCellWidget(i,10,Curve2widget)
                        self.devicetable.setCellWidget(i,11,Delta1widget)
                        self.devicetable.setCellWidget(i,12,Delta2widget)
                        self.devicetable.setCellWidget(i,13,Fill1SpinBox)
                        self.devicetable.setCellWidget(i,14,Fill2SpinBox)

                        # we add QTableWidgetItems disable selection of cells and to have tab focus to jump over those cells
                        color1item = QTableWidgetItem()
                        color1item.setFlags(Qt.ItemFlag.NoItemFlags)
                        self.devicetable.setItem(i,1,color1item)
                        color2item = QTableWidgetItem()
                        color2item.setFlags(Qt.ItemFlag.NoItemFlags)
                        self.devicetable.setItem(i,2,color2item)
                        for j in range(7, 13):
                            item = QTableWidgetItem()
                            item.setFlags(Qt.ItemFlag.NoItemFlags)
                            self.devicetable.setItem(i,j,item)

                    except Exception as e: # pylint: disable=broad-except
                        _log.exception(e)
                header = self.devicetable.horizontalHeader()
                if header is not None:
                    header.setStretchLastSection(False)
                    self.devicetable.resizeColumnsToContents()
                    for i in fixed_size_sections:
                        header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                        header.resizeSection(i, header.sectionSize(i) + 5)
            if not self.aw.qmc.devicetablecolumnwidths:
                self.devicetable.setColumnWidth(0, 230)
                self.devicetable.setColumnWidth(1, 80)
                self.devicetable.setColumnWidth(2, 80)
                self.devicetable.setColumnWidth(3, 80)
                self.devicetable.setColumnWidth(4, 80)
                self.devicetable.setColumnWidth(5, 40)
                self.devicetable.setColumnWidth(6, 40)
            else:
                # remember the columnwidth
                for i, _ in enumerate(self.aw.qmc.devicetablecolumnwidths):
                    if i not in fixed_size_sections:
                        try:
                            self.devicetable.setColumnWidth(i, self.aw.qmc.devicetablecolumnwidths[i])
                        except Exception: # pylint: disable=broad-except
                            pass
        except Exception as e: # pylint: disable=broad-except
            _t, _e, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' createDeviceTable(): {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def copyDeviceTabletoClipboard(self, _:bool = False) -> None:
        import prettytable
        nrows = self.devicetable.rowCount()
        ncols = self.devicetable.columnCount()
        clipboard = ''
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.AltModifier:  #alt click
            tbl = prettytable.PrettyTable()
            fields = []
            re_strip = re.compile('[\u2009]')  #thin space is not read properly by prettytable
            for c in range(ncols):
                item = self.devicetable.horizontalHeaderItem(c)
                if item is not None:
                    fields.append(re_strip.sub('',item.text()))
            tbl.field_names = fields
            for r in range(nrows):
                rows = []
                # device type
                typeComboBox = cast(MyQComboBox, self.devicetable.cellWidget(r,0))
                rows.append(typeComboBox.currentText())
                # color 1
                color1Button = cast(QPushButton, self.devicetable.cellWidget(r,1))
                rows.append(color1Button.palette().button().color().name())
                # color 2
                color2Button = cast(QPushButton, self.devicetable.cellWidget(r,2))
                rows.append(color2Button.palette().button().color().name())
                # name 1
                name1edit = cast(QLineEdit, self.devicetable.cellWidget(r,3))
                rows.append(name1edit.text())
                # name 2
                name2edit = cast(QLineEdit, self.devicetable.cellWidget(r,4))
                rows.append(name2edit.text())
                # math 1
                mexpr1edit = cast(QLineEdit, self.devicetable.cellWidget(r,5))
                rows.append(mexpr1edit.text())
                # math 2
                mexpr2edit = cast(QLineEdit, self.devicetable.cellWidget(r,6))
                rows.append(mexpr2edit.text())
                # lcd 1
                rows.append(str(self.centeredCheckBox_isChecked(self.devicetable.cellWidget(r,7))))
                # lcd 2
                rows.append(str(self.centeredCheckBox_isChecked(self.devicetable.cellWidget(r,8))))
                # curve 1
                rows.append(str(self.centeredCheckBox_isChecked(self.devicetable.cellWidget(r,9))))
                # curve 2
                rows.append(str(self.centeredCheckBox_isChecked(self.devicetable.cellWidget(r,10))))
                # delta 1
                rows.append(str(self.centeredCheckBox_isChecked(self.devicetable.cellWidget(r,11))))
                # delta 2
                rows.append(str(self.centeredCheckBox_isChecked(self.devicetable.cellWidget(r,12))))
                # fill 1
                Fill1SpinBox = cast(QSpinBox, self.devicetable.cellWidget(r,13))
                rows.append(str(Fill1SpinBox.value()))
            # fill 2
                Fill2SpinBox = cast(QSpinBox, self.devicetable.cellWidget(r,14))
                rows.append(str(Fill2SpinBox.value()))
                tbl.add_row(rows)
            clipboard = tbl.get_string()
        else:
            for c in range(ncols):
                item = self.devicetable.horizontalHeaderItem(c)
                if item is not None:
                    clipboard += item.text()
                    if c != (ncols-1):
                        clipboard += '\t'
            clipboard += '\n'
            for r in range(nrows):
                # device type
                typeComboBox = cast(MyQComboBox, self.devicetable.cellWidget(r,0))
                clipboard += typeComboBox.currentText() + '\t'
                # color 1
                color1Button = cast(QPushButton, self.devicetable.cellWidget(r,1))
                clipboard += color1Button.palette().button().color().name() + '\t'
                # color 2
                color2Button = cast(QPushButton, self.devicetable.cellWidget(r,2))
                clipboard += color2Button.palette().button().color().name() + '\t'
                # name 1
                name1edit = cast(QLineEdit, self.devicetable.cellWidget(r,3))
                clipboard += name1edit.text() + '\t'
                # name 2
                name2edit = cast(QLineEdit, self.devicetable.cellWidget(r,4))
                clipboard += name2edit.text() + '\t'
                # math 1
                mexpr1edit = cast(QLineEdit, self.devicetable.cellWidget(r,5))
                clipboard += mexpr1edit.text() + '\t'
                # math 2
                mexpr2edit = cast(QLineEdit, self.devicetable.cellWidget(r,6))
                clipboard += mexpr2edit.text() + '\t'
                # lcd 1
                LCD1visibilityWidget = cast(QWidget, self.devicetable.cellWidget(r,7))
                LCD1visibilityLayout = LCD1visibilityWidget.layout()
                if LCD1visibilityLayout is not None:
                    item0 = LCD1visibilityLayout.itemAt(0)
                    if item0 is not None:
                        LCD1visibilityCheckBox = cast(QCheckBox, item0.widget())
                        clipboard += str(LCD1visibilityCheckBox.isChecked()) + '\t'
                # lcde 2
                LCD2visibilityWidget = cast(QWidget, self.devicetable.cellWidget(r,8))
                LCD2visibilityLayout = LCD2visibilityWidget.layout()
                if LCD2visibilityLayout is not None:
                    item0 = LCD2visibilityLayout.itemAt(0)
                    if item0 is not None:
                        LCD2visibilityCheckBox = cast(QCheckBox, item0.widget())
                        clipboard += str(LCD2visibilityCheckBox.isChecked()) + '\t'
                # curve 1
                Curve1visibilityWidget = cast(QWidget, self.devicetable.cellWidget(r,9))
                Curve1visibilityLayout = Curve1visibilityWidget.layout()
                if Curve1visibilityLayout is not None:
                    item0 = Curve1visibilityLayout.itemAt(0)
                    if item0 is not None:
                        Curve1visibilityCheckBox = cast(QCheckBox, item0.widget())
                        clipboard += str(Curve1visibilityCheckBox.isChecked()) + '\t'
                # curve 2
                Curve2visibilityWidget = cast(QWidget, self.devicetable.cellWidget(r,10))
                Curve2visibilityLayout = Curve2visibilityWidget.layout()
                if Curve2visibilityLayout is not None:
                    item0 = Curve2visibilityLayout.itemAt(0)
                    if item0 is not None:
                        Curve2visibilityCheckBox = cast(QCheckBox, item0.widget())
                        clipboard += str(Curve2visibilityCheckBox.isChecked()) + '\t'
                # delta 1
                Delta1Widget = cast(QWidget, self.devicetable.cellWidget(r,11))
                Delta1Layout = Delta1Widget.layout()
                if Delta1Layout is not None:
                    item0 = Delta1Layout.itemAt(0)
                    if item0 is not None:
                        Delta1CheckBox = cast(QCheckBox, item0.widget())
                        clipboard += str(Delta1CheckBox.isChecked()) + '\t'
                # delta 2
                Delta2Widget = cast(QWidget, self.devicetable.cellWidget(r,12))
                Delta2Layout = Delta2Widget.layout()
                if Delta2Layout is not None:
                    item0 = Delta2Layout.itemAt(0)
                    if item0 is not None:
                        Delta2CheckBox = cast(QCheckBox, item0.widget())
                        clipboard += str(Delta2CheckBox.isChecked()) + '\t'
                # fill 1
                Fill1SpinBox = cast(QSpinBox, self.devicetable.cellWidget(r,13))
                clipboard += str(Fill1SpinBox.value()) + '\t'
                # fill 2
                Fill2SpinBox = cast(QSpinBox, self.devicetable.cellWidget(r,14))
                clipboard += str(Fill2SpinBox.value()) + '\n'
        # copy to the system clipboard
        sys_clip = QApplication.clipboard()
        if sys_clip is not None:
            sys_clip.setText(clipboard)
        self.aw.sendmessage(QApplication.translate('Message','Device table copied to clipboard'))

    @pyqtSlot(bool)
    def loadprogramname(self, _:bool) -> None:
        fileName = self.aw.ArtisanOpenFileDialog()
        if fileName:
            if ' ' in fileName:
                self.programedit.setText('"' + fileName + '"')
            else:
                self.programedit.setText(fileName)

    @pyqtSlot(bool)
    def loadoutprogramname(self, _:bool) -> None:
        fileName = self.aw.ArtisanOpenFileDialog()
        if fileName:
            self.outprogramedit.setText(fileName)
            self.aw.ser.externaloutprogram = self.outprogramedit.text()

    def enableDisableAddDeleteButtons(self) -> None:
        if len(self.aw.qmc.extradevices) >= self.aw.nLCDS:
            self.addButton.setEnabled(False)
        else:
            self.addButton.setEnabled(True)
        if len(self.aw.qmc.extradevices) > 0:
            self.delButton.setEnabled(True)
        else:
            self.delButton.setEnabled(False)
        if len(self.aw.qmc.timex) > 0:
            self.recalcButton.setEnabled(True)
        else:
            self.recalcButton.setEnabled(False)

    #adds extra device
    @pyqtSlot(bool)
    def adddevice(self, _:bool) -> None:
        try:
            self.savedevicetable()
            #addDevice() is located in aw so that the same function can be used in init after dynamically loading settings
            self.aw.addDevice()
            self.createDeviceTable()
            self.enableDisableAddDeleteButtons()
            self.aw.qmc.resetlinecountcaches()
            self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception as e: # pylint: disable=broad-except
            _t, _e, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' adddevice(): {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def deldevice(self, _:bool) -> None:
        try:
            self.savedevicetable()
            bindex = len(self.aw.qmc.extradevices)-1
            selected = self.devicetable.selectedRanges()
            if len(selected) > 0:
                bindex = selected[0].topRow()
            if 0 <= bindex < len(self.aw.qmc.extradevices):
                self.delextradevice(bindex)
                self.enableDisableAddDeleteButtons()
        except Exception as e: # pylint: disable=broad-except
            _t, _e, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' deldevice(): {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def resetextradevices(self, _:bool) -> None:
        try:
            self.aw.resetExtraDevices()
            #update table
            self.createDeviceTable()
            #enable/disable buttons
            self.enableDisableAddDeleteButtons()
            #redraw
            self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception as e: # pylint: disable=broad-except
            _t, _e, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' resetextradevices(): {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    def delextradevice(self, x:int) -> None:
        try:
            self.aw.qmc.extradevices.pop(x)
            self.aw.qmc.extradevicecolor1.pop(x)
            self.aw.qmc.extradevicecolor2.pop(x)
            self.aw.qmc.extratimex.pop(x)
            self.aw.qmc.extratemp1.pop(x)
            self.aw.qmc.extratemp2.pop(x)
            self.aw.qmc.extrastemp1.pop(x)
            self.aw.qmc.extrastemp2.pop(x)
            self.aw.qmc.extractimex1.pop(x)
            self.aw.qmc.extractimex2.pop(x)
            self.aw.qmc.extractemp1.pop(x)
            self.aw.qmc.extractemp2.pop(x)
            self.aw.qmc.extralinestyles1.pop(x)
            self.aw.qmc.extralinestyles2.pop(x)
            self.aw.qmc.extradrawstyles1.pop(x)
            self.aw.qmc.extradrawstyles2.pop(x)
            self.aw.qmc.extralinewidths1.pop(x)
            self.aw.qmc.extralinewidths2.pop(x)
            self.aw.qmc.extramarkers1.pop(x)
            self.aw.qmc.extramarkers2.pop(x)
            self.aw.qmc.extramarkersizes1.pop(x)
            self.aw.qmc.extramarkersizes2.pop(x)

            # visible curves before this one
            before1 = before2 = 0
            for j in range(x):
                if self.aw.extraCurveVisibility1[j]:
                    before1 = before1 + 1
                if self.aw.extraCurveVisibility2[j]:
                    before2 = before2 + 1
            if self.aw.extraCurveVisibility1[x]:
                self.aw.qmc.extratemp1lines.pop(before1)
            if self.aw.extraCurveVisibility2[x]:
                self.aw.qmc.extratemp2lines.pop(before2)

            self.aw.extraLCDvisibility1.pop(x)
            self.aw.extraLCDvisibility1.append(True) # keep length constant (self.aw.nLCDS)
            self.aw.extraLCDvisibility2.pop(x)
            self.aw.extraLCDvisibility2.append(True) # keep length constant (self.aw.nLCDS)
            self.aw.extraCurveVisibility1.pop(x)
            self.aw.extraCurveVisibility1.append(True) # keep length constant (self.aw.nLCDS)
            self.aw.extraCurveVisibility2.pop(x)
            self.aw.extraCurveVisibility2.append(True) # keep length constant (self.aw.nLCDS)
            self.aw.extraDelta1.pop(x)
            self.aw.extraDelta1.append(False) # keep length constant (self.aw.nLCDS)
            self.aw.extraDelta2.pop(x)
            self.aw.extraDelta2.append(False) # keep length constant (self.aw.nLCDS)
            self.aw.extraFill1.pop(x)
            self.aw.extraFill1.append(0) # keep length constant (self.aw.nLCDS)
            self.aw.extraFill2.pop(x)
            self.aw.extraFill2.append(0) # keep length constant (self.aw.nLCDS)

            self.aw.qmc.extraname1.pop(x)
            self.aw.qmc.extraname2.pop(x)
            self.aw.qmc.extramathexpression1.pop(x)
            self.aw.qmc.extramathexpression2.pop(x)
            self.aw.updateLCDproperties()
            #pop serial port settings
            if len(self.aw.extracomport) > x:
                self.aw.extracomport.pop(x)
            if len(self.aw.extrabaudrate) > x:
                self.aw.extrabaudrate.pop(x)
            if len(self.aw.extrabytesize) > x:
                self.aw.extrabytesize.pop(x)
            if len(self.aw.extraparity) > x:
                self.aw.extraparity.pop(x)
            if len(self.aw.extrastopbits) > x:
                self.aw.extrastopbits.pop(x)
            if len(self.aw.extratimeout) > x:
                self.aw.extratimeout.pop(x)
            if len(self.aw.extraser) > x:
                if self.aw.extraser[x].SP.is_open:
                    self.aw.extraser[x].SP.close()
                    libtime.sleep(0.7) # on OS X opening a serial port too fast after closing the port gets disabled
                self.aw.extraser.pop(x)
            self.createDeviceTable()
            self.aw.qmc.resetlinecountcaches()
            self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception as ex: # pylint: disable=broad-except
            _t, _e, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + 'delextradevice(): {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

    def savedevicetable(self, redraw:bool = True) -> None:
        try:
            for i, _ in enumerate(self.aw.qmc.extradevices):
                typecombobox = cast(MyQComboBox, self.devicetable.cellWidget(i,0))
                #cellWidget(i,1) and cellWidget(i,2) are saved automatically when there is a change. No need to save here.
                name1edit = cast(QLineEdit, self.devicetable.cellWidget(i,3))
                name2edit = cast(QLineEdit, self.devicetable.cellWidget(i,4))
                mexpr1edit = cast(QLineEdit, self.devicetable.cellWidget(i,5))
                mexpr2edit = cast(QLineEdit, self.devicetable.cellWidget(i,6))
                try:
                    self.aw.qmc.extradevices[i] = self.aw.qmc.devices.index(str(typecombobox.currentText())) + 1
                except Exception: # pylint: disable=broad-except
                    try: # might be a +device
                        self.aw.qmc.extradevices[i] = self.aw.qmc.devices.index('+' + str(typecombobox.currentText())) + 1
                    except Exception: # pylint: disable=broad-except
                        self.aw.qmc.extradevices[i] = 0
                if name1edit:
                    self.aw.qmc.extraname1[i] = name1edit.text()
                else:
                    self.aw.qmc.extraname1[i] = ''
                if name2edit:
                    self.aw.qmc.extraname2[i] = name2edit.text()
                else:
                    self.aw.qmc.extraname2[i] = ''

                self.aw.extraLCDlabel1[i].setText('<b>' + self.aw.qmc.device_name_subst(self.aw.qmc.extraname1[i]) + '</b>')
                self.aw.extraLCDlabel2[i].setText('<b>' + self.aw.qmc.device_name_subst(self.aw.qmc.extraname2[i]) + '</b>')
                if mexpr2edit:
                    self.aw.qmc.extramathexpression1[i] = mexpr1edit.text()
                else:
                    self.aw.qmc.extramathexpression1[i] = ''
                if mexpr2edit:
                    self.aw.qmc.extramathexpression2[i] = mexpr2edit.text()
                else:
                    self.aw.qmc.extramathexpression2[i] = ''
            #update legend with new curves
            if redraw:
                self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception as ex: # pylint: disable=broad-except
            _t, _e, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + 'savedevicetable(): {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))


    @pyqtSlot(bool)
    def updateVirtualdevicesinprofile_clicked(self, _:bool) -> None:
        self.updateVirtualdevicesinprofile(redraw=True)

    def updateVirtualdevicesinprofile(self, redraw:bool = True) -> None:
        try:
            self.savedevicetable(redraw=False)
            if self.aw.calcVirtualdevices(update=True) and redraw:
                self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception as ex: # pylint: disable=broad-except
            _t, _e, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + 'updateVirtualdevicesinprofile(): {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def updateETBTinprofile(self, _:bool) -> None:
        try:
            # be sure there is an equation to process
            nonempty_ETfunction = bool(self.ETfunctionedit.text() is not None and len(self.ETfunctionedit.text().strip()))
            nonempty_BTfunction = bool(self.BTfunctionedit.text() is not None and len(self.BTfunctionedit.text().strip()))
            if (nonempty_ETfunction or nonempty_BTfunction):

                # confirm the action
                string = QApplication.translate('Message', 'Overwrite existing ET and BT values?')
                reply = QMessageBox.warning(None, #self.aw, # only without super this one shows the native dialog on macOS under Qt 6.6.2 and later
                            QApplication.translate('Message', 'Caution - About to overwrite profile data'),string,
                            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel)
                if reply == QMessageBox.StandardButton.Cancel:
                    return

                # confirm updating the dependent Virtual Extra Devices?
                updatevirtualextradevices = False
                etorbt = re.compile('Y1|Y2|T1|T2|R1|R2')
                for j in range(len(self.aw.qmc.extradevices)):
                    if (re.search(etorbt,self.aw.qmc.extramathexpression1[j]) or re.search(etorbt,self.aw.qmc.extramathexpression2[j])):
                        string = QApplication.translate('Message', 'At least one Virtual Extra Device depends on ET or BT.  Do you want to update all the Virtual Extra Devices after ET and BT are updated?')
                        reply = QMessageBox.warning(None, #self.aw, # only without super this one shows the native dialog on macOS under Qt 6.6.2 and later
                                    QApplication.translate('Message', 'Caution - About to overwrite profile data'),string,
                                    QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
                        if reply == QMessageBox.StandardButton.Yes:
                            updatevirtualextradevices = True
                        break

                # grab the latest symbolic equations as they may have changed without being saved by an OK
                self.aw.qmc.ETfunction = str(self.ETfunctionedit.text())
                self.aw.qmc.BTfunction = str(self.BTfunctionedit.text())

                # make the updates to ET.BT and Virtual Extra Devices if needed
                if self.aw.updateSymbolicETBT():
                    if updatevirtualextradevices:
                        self.updateVirtualdevicesinprofile(redraw=False)
                    self.aw.qmc.redraw(recomputeAllDeltas=True)
                    self.aw.sendmessage(QApplication.translate('Message', 'Symbolic values updated.'))
                else:
                    self.aw.sendmessage(QApplication.translate('Message', 'Symbolic values were not updated.'))
            else:
                self.aw.sendmessage(QApplication.translate('Message', 'Nothing here to process.'))
        except Exception as ex: # pylint: disable=broad-except
            _t, _e, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + 'updateETBTinprofile(): {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(int)
    def updateLCDvisibility1(self, x:int) -> None:
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),7)
        if r is not None:
            self.aw.extraLCDvisibility1[r] = bool(x)
            self.aw.extraLCDframe1[r].setVisible(bool(x))

    @pyqtSlot(int)
    def updateLCDvisibility2(self, x:int) -> None:
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),8)
        if r is not None:
            self.aw.extraLCDvisibility2[r] = bool(x)
            self.aw.extraLCDframe2[r].setVisible(bool(x))

    @pyqtSlot(int)
    def updateCurveVisibility1(self, x:int) -> None:
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),9)
        if r is not None:
            self.aw.extraCurveVisibility1[r] = bool(x)
            self.aw.qmc.resetlinecountcaches()

    @pyqtSlot(int)
    def updateCurveVisibility2(self, x:int) -> None:
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),10)
        if r is not None:
            self.aw.extraCurveVisibility2[r] = bool(x)
            self.aw.qmc.resetlinecountcaches()

    @pyqtSlot(int)
    def updateDelta1(self, x:int) -> None:
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),11)
        if r is not None:
            self.aw.extraDelta1[r] = bool(x)

    @pyqtSlot(int)
    def updateDelta2(self, x:int) -> None:
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),12)
        if r is not None:
            self.aw.extraDelta2[r] = bool(x)

    @pyqtSlot()
    def updateFill1(self) -> None:
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),13)
        if r is not None:
            sender = cast(QSpinBox, self.sender())
            self.aw.extraFill1[r] = sender.value()

    @pyqtSlot()
    def updateFill2(self) -> None:
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),14)
        if r is not None:
            sender = cast(QSpinBox, self.sender())
            self.aw.extraFill2[r] = sender.value()

    @pyqtSlot(bool)
    def setextracolor1(self, _:bool) -> None:
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(), 1)
        if r is not None:
            self.setextracolor(1, r)

    @pyqtSlot(bool)
    def setextracolor2(self, _:bool) -> None:
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(), 2)
        if r is not None:
            self.setextracolor(2, r)

    def setextracolor(self, ll:int, i:int) -> None:
        try:
            #line 1
            if ll == 1:
                # use native no buttons dialog on Mac OS X, blocks otherwise
                colorf = self.aw.colordialog(QColor(rgba_colorname2argb_colorname(self.aw.qmc.extradevicecolor1[i])),True,self, alphasupport=True)
                if colorf.isValid():
                    colorname = argb_colorname2rgba_colorname(colorf.name(QColor.NameFormat.HexArgb))
                    self.aw.qmc.extradevicecolor1[i] = colorname
                    # set LCD label color
                    self.aw.setLabelColor(self.aw.extraLCDlabel1[i],colorname)
                    color1Button = cast(QPushButton, self.devicetable.cellWidget(i,1))
                    color1Button.setStyleSheet(f"border: none; outline: none; background-color: rgba{ImageColor.getcolor(self.aw.qmc.extradevicecolor1[i], 'RGBA')}; color: { self.aw.labelBorW(self.aw.qmc.extradevicecolor1[i])}")
                    color1Button.setText(colorname)
                    self.aw.checkColors([(self.aw.qmc.extraname1[i], self.aw.qmc.extradevicecolor1[i], QApplication.translate('Label','Background'), self.aw.qmc.palette['background'])])
                    self.aw.checkColors([(self.aw.qmc.extraname1[i], self.aw.qmc.extradevicecolor1[i], QApplication.translate('Label','Legend bkgnd'), self.aw.qmc.palette['background'])])
            #line 2
            elif ll == 2:
                # use native no buttons dialog on Mac OS X, blocks otherwise
                colorf = self.aw.colordialog(QColor(rgba_colorname2argb_colorname(self.aw.qmc.extradevicecolor2[i])),True,self, alphasupport=True)
                if colorf.isValid():
                    colorname = argb_colorname2rgba_colorname(colorf.name(QColor.NameFormat.HexArgb))
                    self.aw.qmc.extradevicecolor2[i] = colorname
                    # set LCD label color
                    self.aw.setLabelColor(self.aw.extraLCDlabel2[i],colorname)
                    color2Button = cast(QPushButton, self.devicetable.cellWidget(i,2))
                    color2Button.setStyleSheet(f"border: none; outline: none; background-color: rgba{ImageColor.getcolor(self.aw.qmc.extradevicecolor2[i], 'RGBA')}; color: {self.aw.labelBorW(self.aw.qmc.extradevicecolor2[i])}")
                    color2Button.setText(colorname)
                    self.aw.checkColors([(self.aw.qmc.extraname2[i], self.aw.qmc.extradevicecolor2[i], QApplication.translate('Label','Background'), self.aw.qmc.palette['background'])])
                    self.aw.checkColors([(self.aw.qmc.extraname2[i], self.aw.qmc.extradevicecolor2[i], QApplication.translate('Label','Legend bkgnd'),self.aw.qmc.palette['background'])])
        except Exception as e: # pylint: disable=broad-except
            _t, _e, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' setextracolor(): {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    # close is called from OK and CANCEL
    def close(self) -> bool:
        self.closeHelp()
        settings = QSettings()
        #save window geometry
        settings.setValue('DeviceAssignmentGeometry',self.saveGeometry())
        self.aw.DeviceAssignmentDlg_activeTab = self.TabWidget.currentIndex()
#        self.aw.closeEventSettings() # save all app settings

        if not self.aw.schedule_window:
            # we disconnect all scales again if scheduler is not active
            self.aw.scale_manager.disconnect_all()

        return True

    @pyqtSlot()
    def cancelEvent(self) -> None:
        self.aw.DeviceAssignmentDlg_activeTab = self.TabWidget.currentIndex()
        self.close()
        self.aw.qmc.phidgetRemoteFlag = self.org_phidgetRemoteFlag
        self.aw.qmc.yoctoRemoteFlag = self.org_yoctoRemoteFlag
        self.aw.santokerSerial = self.org_santokerSerial
        self.aw.santokerBLE = self.org_santokerBLE
        self.aw.kaleidoSerial = self.org_kaleidoSerial

        self.aw.scale1_model = self.org_scale1_model
        self.aw.scale1_name = self.org_scale1_name
        self.aw.scale1_id = self.org_scale1_id
        self.aw.container1_idx = self.org_container1_idx
        self.aw.scale2_model = self.org_scale2_model
        self.aw.scale2_name = self.org_scale2_name
        self.aw.scale2_id = self.org_scale2_id
        self.aw.container2_idx = self.org_container2_idx

        self.reject()

    @pyqtSlot()
    def okEvent(self) -> None: # pyright: ignore [reportGeneralTypeIssues] # Code is too complex to analyze; reduce complexity by refactoring into subroutines or reducing conditional code paths

        try:
            self.aw.qmc.device_logging = self.deviceLoggingFlag.isChecked()
            try:
                setDeviceDebugLogLevel(self.aw.qmc.device_logging)
            except Exception: # pylint: disable=broad-except
                pass

            #save any extra devices here
            self.savedevicetable(redraw=False)
            self.aw.qmc.devicetablecolumnwidths = [self.devicetable.columnWidth(c) for c in range(self.devicetable.columnCount())]

            message = QApplication.translate('Message','Device not set')
            # by default switch PID buttons/LCDs off
            self.aw.buttonCONTROL.setVisible(False)
            self.aw.LCD6frame.setVisible(False)
            self.aw.LCD7frame.setVisible(False)
            self.aw.qmc.resetlinecountcaches()
            self.aw.ser.arduinoETChannel = str(self.arduinoETComboBox.currentText())
            self.aw.ser.arduinoBTChannel = str(self.arduinoBTComboBox.currentText())
            self.aw.ser.arduinoATChannel = str(self.arduinoATComboBox.currentText())
            self.aw.ser.ArduinoFILT = [sb.value() for sb in self.FILTspinBoxes]

            self.aw.ser.externalprogram = self.programedit.text()
            self.aw.ser.externaloutprogram = self.outprogramedit.text()

            if self.pidButton.isChecked():
                #type index[0]: 0 = PXG, 1 = PXR, 2 = DTA
                #if str(self.controlpidtypeComboBox.currentText()) == 'Fuji PXG':
                self.aw.ser.controlETpid[0] = 0
                str1 = 'Fuji PXG'
                if str(self.controlpidtypeComboBox.currentText()) == 'Fuji PXR':
                    self.aw.ser.controlETpid[0] = 1
                    str1 = 'Fuji PXR'
                elif str(self.controlpidtypeComboBox.currentText()) == 'Delta DTA':
                    self.aw.ser.controlETpid[0] = 2
                    str1 = 'Delta DTA'
                elif str(self.controlpidtypeComboBox.currentText()) == 'Fuji PXF':
                    self.aw.ser.controlETpid[0] = 4
                    str1 = 'Fuji PXF'
                self.aw.ser.controlETpid[1] =  toInt(str(self.controlpidunitidComboBox.currentText()))
                #if str(self.btpidtypeComboBox.currentText()) == 'Fuji PXG':
                self.aw.ser.readBTpid[0] = 0
                str2 = 'Fuji PXG'
                if str(self.btpidtypeComboBox.currentText()) == 'Fuji PXR':
                    self.aw.ser.readBTpid[0] = 1
                    str2 = 'Fuji PXR'
                elif str(self.btpidtypeComboBox.currentText()) == '':
                    self.aw.ser.readBTpid[0] = 2
                    str2 = 'None'
                elif str(self.btpidtypeComboBox.currentText()) == 'Delta DTA':
                    self.aw.ser.readBTpid[0] = 3
                    str2 = 'Delta DTA'
                elif str(self.btpidtypeComboBox.currentText()) == 'Fuji PXF':
                    self.aw.ser.readBTpid[0] = 4
                    str2 = 'Fuji PXF'
                self.aw.ser.readBTpid[1] =  toInt(str(self.btpidunitidComboBox.currentText()))
                if self.showFujiLCDs.isChecked():
                    self.aw.ser.showFujiLCDs = True
                else:
                    self.aw.ser.showFujiLCDs = False
                if self.useModbusPort.isChecked():
                    self.aw.ser.useModbusPort = True
                else:
                    self.aw.ser.useModbusPort = False
                #If fuji pid
                if str1 != 'Delta DTA':
                    if self.aw.qmc.device != 0:
                        self.aw.qmc.device = 0
                        #self.aw.ser.comport = "COM4"
                        self.aw.ser.baudrate = 9600
                        self.aw.ser.bytesize = 8
                        self.aw.ser.parity= 'O'
                        self.aw.ser.stopbits = 1
                        self.aw.ser.timeout = 1.0
                #else if DTA pid
                elif self.aw.qmc.device != 26:
                    self.aw.qmc.device = 26
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 2400
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 1.0
                message = QApplication.translate('Message','PID to control ET set to {0} {1}' + \
                                                 ' ; PID to read BT set to {2} {3}').format(str1,str(self.aw.ser.controlETpid[1]),str2,str(self.aw.ser.readBTpid[1]))
            elif self.arduinoButton.isChecked():
                meter = 'Arduino (TC4)'
                if self.aw.qmc.device != 19:
                    self.aw.qmc.device = 19
                    self.aw.ser.baudrate = 115200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.8
                    self.aw.ser.ArduinoIsInitialized = 0 # ensure the Arduino gets reinitalized if settings changed
                    message = QApplication.translate('Message','Device set to {0}. Now, check Serial Port settings').format(meter)
            elif self.programButton.isChecked():
                meter = self.programedit.text()
                self.aw.ser.externalprogram = meter
                self.aw.qmc.device = 27
                message = QApplication.translate('Message','Device set to {0}. Now, check Serial Port settings').format(meter)
            elif self.nonpidButton.isChecked():
                meter = str(self.devicetypeComboBox.currentText())
                if meter == 'Omega HH806AU' and self.aw.qmc.device != 1:
                    self.aw.qmc.device = 1
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 19200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'E'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                elif meter == 'Omega HH506RA' and self.aw.qmc.device != 2:
                    self.aw.qmc.device = 2
                    #self.aw.ser.comport = "/dev/tty.usbserial-A2001Epn"
                    self.aw.ser.baudrate = 2400
                    self.aw.ser.bytesize = 7
                    self.aw.ser.parity= 'E'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    self.aw.ser.HH506RAid = 'X' # ensure the HH506RA gets reinitalized if settings changed
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                elif meter == 'CENTER 309' and self.aw.qmc.device != 3:
                    self.aw.qmc.device = 3
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                elif meter == 'CENTER 306' and self.aw.qmc.device != 4:
                    self.aw.qmc.device = 4
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                elif meter == 'CENTER 305' and self.aw.qmc.device != 5:
                    self.aw.qmc.device = 5
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to CENTER 305, which is equivalent to CENTER 306. Now, choose serial port').format(meter)
                elif meter == 'CENTER 304' and self.aw.qmc.device != 6:
                    self.aw.qmc.device = 6
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}, which is equivalent to CENTER 309. Now, choose serial port').format(meter)
                elif meter == 'CENTER 303' and self.aw.qmc.device != 7:
                    self.aw.qmc.device = 7
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                elif meter == 'CENTER 302' and self.aw.qmc.device != 8:
                    self.aw.qmc.device = 8
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}, which is equivalent to CENTER 303. Now, choose serial port').format(meter)
                elif meter == 'CENTER 301' and self.aw.qmc.device != 9:
                    self.aw.qmc.device = 9
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}, which is equivalent to CENTER 303. Now, choose serial port').format(meter)
                elif meter == 'CENTER 300' and self.aw.qmc.device != 10:
                    self.aw.qmc.device = 10
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}, which is equivalent to CENTER 303. Now, choose serial port').format(meter)
                elif meter == 'VOLTCRAFT K204' and self.aw.qmc.device != 11:
                    self.aw.qmc.device = 11
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}, which is equivalent to CENTER 309. Now, choose serial port').format(meter)
                elif meter == 'VOLTCRAFT K202' and self.aw.qmc.device != 12:
                    self.aw.qmc.device = 12
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}, which is equivalent to CENTER 306. Now, choose serial port').format(meter)
                elif meter == 'VOLTCRAFT 300K' and self.aw.qmc.device != 13:
                    self.aw.qmc.device = 13
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.5
                    message = QApplication.translate('Message','Device set to {0}, which is equivalent to CENTER 303. Now, choose serial port').format(meter)
                elif meter == 'VOLTCRAFT 302KJ' and self.aw.qmc.device != 14:
                    self.aw.qmc.device = 14
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}, which is equivalent to CENTER 303. Now, choose serial port').format(meter)
                elif meter == 'EXTECH 421509' and self.aw.qmc.device != 15:
                    self.aw.qmc.device = 15
                    #self.aw.ser.comport = "/dev/tty.usbserial-A2001Epn"
                    self.aw.ser.baudrate = 2400
                    self.aw.ser.bytesize = 7
                    self.aw.ser.parity= 'E'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}, which is equivalent to Omega HH506RA. Now, choose serial port').format(meter)
                elif meter == 'Omega HH802U' and self.aw.qmc.device != 16:
                    self.aw.qmc.device = 16
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 19200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'E'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}, which is equivalent to Omega HH806AU. Now, choose serial port').format(meter)
                elif meter == 'Omega HH309' and self.aw.qmc.device != 17:
                    self.aw.qmc.device = 17
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                #special device manual mode. No serial settings.
                elif meter == 'NONE':
                    self.aw.qmc.device = 18
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                    st = ''
                    # ensure that events button is shown
                    self.aw.eventsbuttonflag = 1
                    self.aw.buttonEVENT.setVisible(True)
                    message = QApplication.translate('Message','Device set to {0}{1}').format(meter,st)
                ##########################
                ####  DEVICE 19 is the Arduino/TC4
                ##########################
                elif meter == 'TE VA18B' and self.aw.qmc.device != 20:
                    self.aw.qmc.device = 20
                    #self.aw.ser.comport = "COM7"
                    self.aw.ser.baudrate = 2400
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 1.0
                    message = QApplication.translate('Message','Device set to {0}. Now, check Serial Port settings').format(meter)
                ##########################
                ####  DEVICE 21 is +309_34 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 22 is +PID DUTY% but +DEVICE cannot be set as main device
                ##########################
                elif meter == 'Omega HHM28[6]' and self.aw.qmc.device != 23:
                    self.aw.qmc.device = 23
                    #self.aw.ser.comport = "COM1"
                    self.aw.ser.baudrate = 2400
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 1.0
                    message = QApplication.translate('Message','Device set to {0}. Now, check Serial Port settings').format(meter)
# +DEVICEs cannot be set as main device
                ##########################
                ####  DEVICE 24 is +VOLTCRAFT 204_34 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 25 is +Virtual but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 26 is DTA pid
                ##########################
                ##########################
                ####  DEVICE 27 is an external program
                ##########################
                ##########################
                ####  DEVICE 28 is +ArduinoTC4 34 but +DEVICE cannot be set as main device
                ##########################
                elif meter == 'MODBUS' and self.aw.qmc.device != 29:
                    self.aw.qmc.device = 29
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 115200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.6
                    message = QApplication.translate('Message','Device set to {0}. Now, choose Modbus serial port or IP address').format(meter)
                elif meter == 'VOLTCRAFT K201' and self.aw.qmc.device != 30:
                    self.aw.qmc.device = 30
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}, which is equivalent to CENTER 302. Now, choose serial port').format(meter)
                elif meter == 'Amprobe TMD-56' and self.aw.qmc.device != 31:
                    self.aw.qmc.device = 31
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 19200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'E'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}, which is equivalent to Omega HH806AU. Now, choose serial port').format(meter)
                ##########################
                ####  DEVICE 32 is +ArduinoTC4 56 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 33 is +MODBUS 34 but +DEVICE cannot be set as main device
                ##########################
                elif meter == 'Phidget 1048 4xTC 01':
                    self.aw.qmc.device = 34
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 35 is +Phidget 1048 4xTC 23 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 36 is +Phidget 1048 4xTC AT but +DEVICE cannot be set as main device
                ##########################
                elif meter == 'Phidget 1046 4xRTD 01':
                    self.aw.qmc.device = 37
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 38 is +Phidget 1046 4xRTD 23 but +DEVICE cannot be set as main device
                ##########################
                elif meter == 'Mastech MS6514' and self.aw.qmc.device != 39:
                    self.aw.qmc.device = 39
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                ##########################
                elif meter == 'Phidget IO 01':
                    self.aw.qmc.device = 40
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 41 is +Phidget IO 23 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 42 is +Phidget IO 45 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 43 is +Phidget IO 67 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 44 is +ARDUINOTC4_78 but +DEVICE cannot be set as main device
                ##########################
                elif meter == 'Yocto Thermocouple':
                    self.aw.qmc.device = 45
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                elif meter == 'Yocto PT100':
                    self.aw.qmc.device = 46
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                elif meter == 'Phidget 1045 IR':
                    self.aw.qmc.device = 47
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 48 is an external program 34
                ##########################
                ##########################
                ####  DEVICE 49 is an external program 56
                ##########################
                elif meter == 'DUMMY' and self.aw.qmc.device != 50: # including a dummy serial device (can be used for serial commands)
                    self.aw.qmc.device = 50
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.5
                ##########################
                ####  DEVICE 51 is +304_34 but +DEVICE cannot be set as main device
                ##########################
                elif meter == 'Phidget 1051 1xTC 01':
                    self.aw.qmc.device = 52
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                elif meter == 'Hottop BT/ET' and self.aw.qmc.device != 53:
                    self.aw.qmc.device = 53
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 115200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                ##########################
                ####  DEVICE 54 is +Hottop HF but +DEVICE cannot be set as main device
                ##########################
                elif meter == 'Omega HH806W' and self.aw.qmc.device != 55:
                    self.aw.qmc.device = 55
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 38400
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'E'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                ##########################
                ####  DEVICE 55 is +MODBUS_56 but +DEVICE cannot be set as main device
                ##########################
                elif meter == 'Apollo DT301' and self.aw.qmc.device != 56:
                    self.aw.qmc.device = 56
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                ##########################
                elif meter == 'EXTECH 755' and self.aw.qmc.device != 57:
                    self.aw.qmc.device = 57
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                ##########################
                elif meter == 'Phidget TMP1101 4xTC 01':
                    self.aw.qmc.device = 58
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 59 is +Phidget TMP1101 4xTC 23 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 60 is +Phidget TMP1101 4xTC AT but +DEVICE cannot be set as main device
                ##########################
                ##########################
                elif meter == 'Phidget TMP1100 1xTC':
                    self.aw.qmc.device = 61
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                elif meter == 'Phidget 1011 IO 01':
                    self.aw.qmc.device = 62
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                elif meter == 'Phidget HUB IO 01':
                    self.aw.qmc.device = 63
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 64 is +Phidget HUB IO 23 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 65 is +Phidget HUB IO 45 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 66 is -HH806W but -DEVICE cannot be set as main device
                ##########################
                ##########################
                elif meter == 'VOLTCRAFT PL-125-T2' and self.aw.qmc.device != 67:
                    self.aw.qmc.device = 67
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                ##########################
                ##########################
                elif meter == 'Phidget TMP1200 1xRTD A':
                    self.aw.qmc.device = 68
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                elif meter == 'Phidget IO Digital 01':
                    self.aw.qmc.device = 69
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 70 is +Phidget IO Digital 23 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 71 is +Phidget IO Digital 45 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 72 is +Phidget IO Digital 67 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                elif meter == 'Phidget 1011 IO Digital 01':
                    self.aw.qmc.device = 73
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                elif meter == 'Phidget HUB IO Digital 01':
                    self.aw.qmc.device = 74
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 75 is +Phidget HUB IO Digital 23 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 76 is +Phidget HUB IO Digital 45 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                elif meter == 'VOLTCRAFT PL-125-T4' and self.aw.qmc.device != 77:
                    self.aw.qmc.device = 77
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                ##########################
                ##########################
                ####  DEVICE 78 is +VOLTCRAFT PL-125-T4 34 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                elif meter == 'S7':
                    self.aw.qmc.device = 79
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 80 is +S7 34 but no serial setup
                ##########################
                ##########################
                ####  DEVICE 81 is +S7 56 but no serial setup
                ##########################
                ##########################
                ####  DEVICE 82 is +S7 78 but no serial setup
                ##########################
                ##########################
                ####  DEVICE 83-87 are Aillio R1 and have no serial setup
                ##########################
                elif meter == 'Aillio Bullet R1 BT/DT':
                    self.aw.qmc.device = 83
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 88 and 89 are an external program 78 and 910
                ##########################
                ##########################
                ####  DEVICE 90 and 91 are an slider 01 and slider 23
                ##########################
                ##########################
                ####  DEVICE 92-94 are an Probat Middleware and have no serial setup
                ##########################
                elif meter == 'Probat Middleware':
                    self.aw.qmc.device = 92
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 95 is Phidget DAQ1400 Current
                ##########################
                elif meter == 'Phidget DAQ1400 Current':
                    self.aw.qmc.device = 95
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 96 is Phidget DAQ1400 Frequency
                ##########################
                elif meter == 'Phidget DAQ1400 Frequency':
                    self.aw.qmc.device = 96
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 97 is Phidget DAQ1400 Digital
                ##########################
                elif meter == 'Phidget DAQ1400 Digital':
                    self.aw.qmc.device = 97
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 98 is Phidget DAQ1400 Voltage
                ##########################
                elif meter == 'Phidget DAQ1400 Voltage':
                    self.aw.qmc.device = 98
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 99 is Aillio Bullet R1 IBTS/DT
                ##########################
                elif meter == 'Aillio Bullet R1 IBTS/DT':
                    self.aw.qmc.device = 99
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 100 are Yocto IR
                ##########################
                elif meter == 'Yocto IR':
                    self.aw.qmc.device = 100
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                elif meter == 'Behmor BT/CT' and self.aw.qmc.device != 101:
                    self.aw.qmc.device = 101
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 57600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                ##########################
                ####  DEVICE 102 Behmor 34 channel 3 and 4
                ##########################
                elif meter == 'VICTOR 86B' and self.aw.qmc.device != 103:
                    self.aw.qmc.device = 103
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 2400
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                ##########################
                ####  DEVICE 104 Behmor 56 channel 5 and 6
                ##########################
                ##########################
                ####  DEVICE 105 Behmor 78 channel 7 and 8
                ##########################
                ##########################
                elif meter == 'Phidget HUB IO 0':
                    self.aw.qmc.device = 106
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                elif meter == 'Phidget HUB IO Digital 0':
                    self.aw.qmc.device = 107
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                elif meter == 'Yocto 4-20mA Rx':
                    self.aw.qmc.device = 108
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 109 is +MODBUS_78 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 110 is +S7_010 but +DEVICE cannot be set as main device
                ##########################
                elif meter == 'WebSocket':
                    self.aw.qmc.device = 111
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 112 is +WebSocket 34 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 113 is +WebSocket 56 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 114 is +TMP1200_2 (a second TMP1200 configuration)
                ##########################
                elif meter == 'HB BT/ET' and self.aw.qmc.device != 115:
                    self.aw.qmc.device = 115
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.8
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                ##########################
                ####  DEVICE 116 is +HB DT/IT
                ##########################
                ##########################
                ####  DEVICE 117 is +HB AT
                ##########################
                ##########################
                ####  DEVICE 118 is +WebSocket 78 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 119 is +WebSocket 910 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 120 is Yocto 0-10V Rx
                elif meter == 'Yocto 0-10V Rx':
                    self.aw.qmc.device = 120
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 121 is Yocto milliVolt Rx
                elif meter == 'Yocto milliVolt Rx':
                    self.aw.qmc.device = 121
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 122 is Yocto Serial
                elif meter == 'Yocto Serial':
                    self.aw.qmc.device = 122
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 123 is Phidget VCP1000
                elif meter == 'Phidget VCP1000':
                    self.aw.qmc.device = 123
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 124 is Phidget VCP1001
                elif meter == 'Phidget VCP1001':
                    self.aw.qmc.device = 124
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 125 is Phidget VCP1002
                elif meter == 'Phidget VCP1002':
                    self.aw.qmc.device = 125
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                elif meter == 'ARC BT/ET' and self.aw.qmc.device != 126:
                    self.aw.qmc.device = 126
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 115200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.4
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                ##########################
                ####  DEVICE 127 is +ARC MET/IT
                ##########################
                ##########################
                ####  DEVICE 128 is +ARC AT (points to "+HB AT")
                ##########################
                ##########################
                ####  DEVICE 129 is Yocto Power
                elif meter == 'Yocto Power':
                    self.aw.qmc.device = 129
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 130 is Yocto Energy
                elif meter == 'Yocto Energy':
                    self.aw.qmc.device = 130
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 131 is Yocto Voltage
                elif meter == 'Yocto Voltage':
                    self.aw.qmc.device = 131
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 132 is Yocto Current
                elif meter == 'Yocto Current':
                    self.aw.qmc.device = 132
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 133 is Yocto Sensor
                elif meter == 'Yocto Sensor':
                    self.aw.qmc.device = 133
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 134 is Santoker BT/ET
                elif meter == 'Santoker BT/ET':
                    self.aw.qmc.device = 134
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 135 is +Santoker Power/Fan but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 136 is +Santoker Drum  but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 137 is Phidget DAQ1500
                elif meter == 'Phidget DAQ1500':
                    self.aw.qmc.device = 137
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 138 is Kaleido BT/ET
                elif meter == 'Kaleido BT/ET':
                    self.aw.qmc.device = 138
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 139 is +Kaleido ST/AT but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 140 is +Kaleido Drum/AH but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 141 is +Kaleido Heater/Fan but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 142 is IKAWA
                elif meter == 'IKAWA':
                    self.aw.qmc.device = 142
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                    permission_status:Optional[bool] = self.aw.app.getBluetoothPermission(request=True)
                    if permission_status is False:
                        msg:str = QApplication.translate('Message','Bluetootooth access denied')
                        QMessageBox.warning(None, #self, # only without super this one shows the native dialog on macOS under Qt 6.6.2 and later
                            msg, msg)
                ##########################
                ####  DEVICE 143 is +IKAWA SET/RPM but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 144 is +IKAWA Heater/Fan but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 145 is +IKAWA State/Humidity but +DEVICE cannot be set as main device
                ##########################
                ##########################
                elif meter == 'Phidget DAQ1000 01':
                    self.aw.qmc.device = 146
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ####  DEVICE 147 is +Phidget DAQ1000 23 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 148 is +Phidget DAQ1000 45 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 149 is +Phidget DAQ1000 67 but +DEVICE cannot be set as main device
                ##########################
                ####  DEVICE 150 is +MODBUS_910 but +DEVICE cannot be set as main device
                ##########################
                ####  DEVICE 151 is +S7_1112 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                elif meter == 'Phidget DAQ1200 01':
                    self.aw.qmc.device = 152
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 153 is +Phidget DAQ1200 23 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                elif meter == 'Phidget DAQ1300 01':
                    self.aw.qmc.device = 154
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 155 is +Phidget DAQ1300 23 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                elif meter == 'Phidget DAQ1301 01':
                    self.aw.qmc.device = 156
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 157 is +Phidget DAQ1301 23 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 158 is +Phidget DAQ1301 45 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 159 is +Phidget DAQ1301 67 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 160 is +IKAWA \Delta Humidity / Humidity direction but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 161 is +Omega HH309 34 but +DEVICE cannot be set as main device
                ##########################
                elif meter == 'Digi-Sense 20250-07' and self.aw.qmc.device != 161: # noqa: SIM114
                    self.aw.qmc.device = 17
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                elif meter == 'Extech 42570' and self.aw.qmc.device != 162:
                    self.aw.qmc.device = 17
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate('Message','Device set to {0}. Now, choose serial port').format(meter)
                ##########################
                ####  DEVICE 164 is Mugma BT/ET
                elif meter == 'Mugma BT/ET':
                    self.aw.qmc.device = 164
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 165 is +Mugma Heater/Fan but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 166 is +Mugma Heater/Catalyzer but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 167 is +Mugma SV but +DEVICE cannot be set as main device
                ##########################
                ##########################
                elif meter == 'Phidget TMP1202 1xRTD A':
                    self.aw.qmc.device = 168
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 169 is +TMP1202_2 (a second TMP1202 configuration)
                ##########################
                ##########################
                ####  DEVICE 170 is ColorTrack Serial
                elif meter == 'ColorTrack Serial':
                    self.aw.qmc.device = 170
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 171 is Santoker BT/ET
                elif meter == 'Santoker R BT/ET':
                    self.aw.qmc.device = 171
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 172 is +Santoker IR/Board  but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 173 is +Santoker DelatBT/DeltaET  but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 174 is ColorTrack BT
                elif meter == 'ColorTrack BT':
                    self.aw.qmc.device = 174
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################
                ##########################
                ####  DEVICE 171 is Thermoworks BlueDOT BT
                elif meter == 'Thermoworks BlueDOT':
                    self.aw.qmc.device = 175
                    message = QApplication.translate('Message','Device set to {0}').format(meter)
                ##########################


                # ADD DEVICE:

                # ensure that by selecting a real device, the initial sampling rate is set to 3s
                if meter != 'NONE':
                    self.aw.qmc.delay = max(self.aw.qmc.delay,self.aw.qmc.min_delay)
            # update Control button visibility
            self.aw.showControlButton()

    # ADD DEVICE: to add a device you have to modify several places. Search for the tag "ADD DEVICE:"in the code
    # - add an elif entry above to specify the default serial settings
            #extra devices serial config
            #set of different serial settings modes options
            ssettings: Final[List[Tuple[int,int,str,int,float]]] = [(9600,8,'O',1,0.5),(19200,8,'E',1,0.5),(2400,7,'E',1,1),(9600,8,'N',1,0.5),
                         (19200,8,'N',1,0.5),(2400,8,'N',1,1),(9600,8,'E',1,0.5),(38400,8,'E',1,0.5),(115200,8,'N',1,0.4),(57600,8,'N',1,0.4)]
            #map device index to a setting mode (choose the one that matches the device)
    # ADD DEVICE: to add a device you have to modify several places. Search for the tag "ADD DEVICE:"in the code
    # - add an entry to devsettings below (and potentially to ssettings above)
            devssettings: Final[List[int]] = [
                0, # 0
                1, # 1
                2, # 2
                3, # 3
                3, # 4
                3, # 5
                3, # 6
                3, # 7
                3, # 8
                3, # 9
                3, # 10
                3, # 11
                3, # 12
                3, # 13
                3, # 14
                2, # 15
                1, # 16
                3, # 17
                0, # 18
                4, # 19
                5, # 20
                3, # 21
                6, # 22
                5, # 23
                3, # 24
                3, # 25
                6, # 26
                3, # 27
                4, # 28
                8, # 29
                3, # 30
                1, # 31
                4, # 32
                7, # 33
                1, # 34
                1, # 35
                1, # 36
                1, # 37
                1, # 38
                3, # 39
                1, # 40
                1, # 41
                1, # 42
                1, # 43
                4, # 44
                1, # 45
                1, # 46
                1, # 47
                3, # 48
                3, # 49
                3, # 50
                3, # 51
                1, # 52
                8, # 53
                8, # 54
                7, # 55
                3, # 56
                3, # 57
                1, # 58
                1, # 59
                1, # 60
                1, # 61
                1, # 62
                1, # 63
                1, # 64
                1, # 65
                8, # 66
                3, # 67
                1, # 68
                1, # 69
                1, # 70
                1, # 71
                1, # 72
                1, # 73
                1, # 74
                1, # 75
                1, # 76
                3, # 77
                3, # 78
                1, # 79
                1, # 80
                1, # 81
                1, # 82
                1, # 83
                1, # 84
                1, # 85
                1, # 86
                1, # 87
                1, # 88
                1, # 89
                1, # 90
                1, # 91
                1, # 92
                1, # 93
                1, # 94
                1, # 95
                1, # 96
                1, # 97
                1, # 98
                1, # 99
                1, # 100
                9, # 101
                9, # 102
                5, # 103
                9, # 104
                9, # 105
                1, # 106
                1, # 107
                1, # 108
                7, # 109
                1, # 110
                1, # 111
                1, # 112
                1, # 113
                1, # 114
                3, # 115
                3, # 116
                3, # 117
                1, # 118
                1, # 119
                1, # 120
                1, # 121
                1, # 122
                1, # 123
                1, # 124
                1, # 125
                8, # 126
                8, # 127
                8, # 128
                1, # 129
                1, # 130
                1, # 131
                1, # 132
                1, # 133
                1, # 134
                1, # 135
                1, # 136
                1, # 137
                9, # 138
                9, # 139
                9, # 140
                9, # 141
                9, # 142
                9, # 143
                9, # 144
                9, # 145
                1, # 146
                1, # 147
                1, # 148
                1, # 149
                7, # 150
                1, # 151
                1, # 152
                1, # 153
                1, # 154
                1, # 155
                1, # 156
                1, # 157
                1, # 158
                1, # 159
                9, # 160
                3, # 161
                3, # 162
                3, # 163
                1, # 164
                1, # 165
                1, # 166
                1, # 167
                1, # 168
                1, # 169
                3, # 170
                1, # 171
                1, # 172
                1, # 173
                1, # 174
                1  # 175
                ]
            #init serial settings of extra devices
            for i, _ in enumerate(self.aw.qmc.extradevices):
                if self.aw.qmc.extradevices[i] < len(devssettings) and devssettings[self.aw.qmc.extradevices[i]] < len(ssettings):
                    dsettings: Tuple[int,int,str,int,float] = ssettings[devssettings[self.aw.qmc.extradevices[i]]]
                    if i < len(self.aw.extrabaudrate):
                        self.aw.extrabaudrate[i] = dsettings[0]
                    else:
                        self.aw.extrabaudrate.append(dsettings[0])
                    if i < len(self.aw.extrabytesize):
                        self.aw.extrabytesize[i] = dsettings[1]
                    else:
                        self.aw.extrabytesize.append(dsettings[1])
                    if i < len(self.aw.extraparity):
                        self.aw.extraparity[i] = dsettings[2]
                    else:
                        self.aw.extraparity.append(dsettings[2])
                    if i < len(self.aw.extrastopbits):
                        self.aw.extrastopbits[i] = dsettings[3]
                    else:
                        self.aw.extrastopbits.append(dsettings[3])
                    if i < len(self.aw.extratimeout):
                        self.aw.extratimeout[i] = dsettings[4]
                    else:
                        self.aw.extratimeout.append(dsettings[4])
            if self.nonpidButton.isChecked():
                self.aw.buttonSVp5.setVisible(False)
                self.aw.buttonSVp10.setVisible(False)
                self.aw.buttonSVp20.setVisible(False)
                self.aw.buttonSVm20.setVisible(False)
                self.aw.buttonSVm10.setVisible(False)
                self.aw.buttonSVm5.setVisible(False)
                self.aw.LCD6frame.setVisible(False)
                self.aw.LCD7frame.setVisible(False)
            self.aw.qmc.ETfunction = str(self.ETfunctionedit.text())
            self.aw.qmc.BTfunction = str(self.BTfunctionedit.text())
            if self.aw.qmc.BTcurve != self.BTcurve.isChecked() or self.aw.qmc.ETcurve != self.ETcurve.isChecked():
                # we reset the cached main event annotation positions as those annotations are now rendered on the other curve
                self.aw.qmc.l_annotations_dict = {}
                self.aw.qmc.l_event_flags_dict = {}
            self.aw.qmc.ETcurve = self.ETcurve.isChecked()
            self.aw.qmc.BTcurve = self.BTcurve.isChecked()
            self.aw.qmc.ETlcd = self.ETlcd.isChecked()
            self.aw.qmc.BTlcd = self.BTlcd.isChecked()

            swap = self.swaplcds.isChecked()
            # swap BT/ET lcds on leaving the dialog
            if self.aw.qmc.swaplcds != swap:
                tmp = QWidget()
                tmp.setLayout(self.aw.LCD2frame.layout())
                self.aw.LCD2frame.setLayout(self.aw.LCD3frame.layout())
                self.aw.LCD3frame.setLayout(tmp.layout())
                if self.aw.largeLCDs_dialog is not None:
                    self.aw.qmc.swaplcds = swap
                    self.aw.largeLCDs_dialog.reLayout()
            self.aw.qmc.swaplcds = swap

            # close all ports to force a reopen
            self.aw.qmc.disconnectProbes()

            # Yotopuce configurations
            self.aw.qmc.yoctoRemoteFlag = self.yoctoBoxRemoteFlag.isChecked()
            self.aw.qmc.yoctoServerID = self.yoctoServerId.text()
            self.aw.qmc.YOCTO_emissivity = self.yoctoEmissivitySpinBox.value()
            self.aw.qmc.YOCTO_async[0] = self.yoctoAyncChanFlag.isChecked()
            self.aw.qmc.YOCTO_async[1] = self.yoctoAyncChanFlag.isChecked() # flag for channel 1 is ignored and only that of channel 0 is respected for both channels
            self.aw.qmc.YOCTO_dataRate = self.aw.qmc.YOCTO_dataRatesValues[self.yoctoDataRateCombo.currentIndex()]

            # Ambient confifgurations
            self.aw.qmc.ambient_temperature_device = self.temperatureDeviceCombo.currentIndex()
            self.aw.qmc.ambient_humidity_device = self.humidityDeviceCombo.currentIndex()
            self.aw.qmc.ambient_pressure_device = self.pressureDeviceCombo.currentIndex()
            try:
                self.aw.qmc.elevation = int(self.elevationSpinBox.value())
            except Exception: # pylint: disable=broad-except
                pass

            # Phidget configurations
            for i in range(4):
                self.aw.qmc.phidget1048_types[i] = self.probeTypeCombos[i].currentIndex()+1
                self.aw.qmc.phidget1048_async[i] = self.asyncCheckBoxes1048[i].isChecked()
                self.aw.qmc.phidget1048_changeTriggers[i] = self.aw.qmc.phidget1048_changeTriggersValues[self.changeTriggerCombos1048[i].currentIndex()]
                self.aw.qmc.phidget1046_gain[i] = self.gainCombos1046[i].currentIndex()+1
                self.aw.qmc.phidget1046_formula[i] = self.formulaCombos1046[i].currentIndex()
                self.aw.qmc.phidget1046_async[i] = self.asyncCheckBoxes1046[i].isChecked()
            self.aw.qmc.phidget1048_dataRate = self.aw.qmc.phidget_dataRatesValues[self.dataRateCombo1048.currentIndex()]
            self.aw.qmc.phidget1046_dataRate = self.aw.qmc.phidget_dataRatesValues[self.dataRateCombo1046.currentIndex()]
            self.aw.qmc.phidget1045_async = self.asyncCheckBoxe1045.isChecked()
            self.aw.qmc.phidget1045_changeTrigger = self.aw.qmc.phidget1045_changeTriggersValues[self.changeTriggerCombos1045.currentIndex()]
            self.aw.qmc.phidget1045_emissivity = self.emissivitySpinBox.value()
            self.aw.qmc.phidget1045_dataRate = self.aw.qmc.phidget_dataRatesValues[self.dataRateCombo1045.currentIndex()]

            self.aw.qmc.phidget1200_formula = self.formulaCombo1200.currentIndex()
            self.aw.qmc.phidget1200_wire = self.wireCombo1200.currentIndex()
            self.aw.qmc.phidget1200_async = self.asyncCheckBoxe1200.isChecked()
            self.aw.qmc.phidget1200_changeTrigger = self.aw.qmc.phidget1200_changeTriggersValues[self.changeTriggerCombo1200.currentIndex()]
            self.aw.qmc.phidget1200_dataRate = self.aw.qmc.phidget1200_dataRatesValues[self.rateCombo1200.currentIndex()]

            self.aw.qmc.phidget1200_2_formula = self.formulaCombo1200_2.currentIndex()
            self.aw.qmc.phidget1200_2_wire = self.wireCombo1200_2.currentIndex()
            self.aw.qmc.phidget1200_2_async = self.asyncCheckBoxe1200_2.isChecked()
            self.aw.qmc.phidget1200_2_changeTrigger = self.aw.qmc.phidget1200_changeTriggersValues[self.changeTriggerCombo1200_2.currentIndex()]
            self.aw.qmc.phidget1200_2_dataRate = self.aw.qmc.phidget1200_dataRatesValues[self.rateCombo1200_2.currentIndex()]

            self.aw.qmc.phidgetDAQ1400_powerSupply = self.powerCombo1400.currentIndex()
            self.aw.qmc.phidgetDAQ1400_inputMode = self.modeCombo1400.currentIndex()

            self.aw.qmc.phidgetRemoteFlag = self.phidgetBoxRemoteFlag.isChecked()
            self.aw.qmc.phidgetServerID = self.phidgetServerId.text()
            self.aw.qmc.phidgetPassword = self.phidgetPassword.text()
            self.aw.qmc.phidgetRemoteOnlyFlag = self.phidgetBoxRemoteOnlyFlag.isChecked()
            try:
                self.aw.qmc.phidgetPort = int(self.phidgetPort.text())
            except Exception: # pylint: disable=broad-except
                pass
            self.aw.santokerHost = self.santokerHost.text().strip()
            try:
                self.aw.santokerPort = int(self.santokerPort.text())
            except Exception: # pylint: disable=broad-except
                pass
            self.aw.kaleidoHost = self.kaleidoHost.text().strip()
            try:
                self.aw.kaleidoPort = int(self.kaleidoPort.text())
            except Exception: # pylint: disable=broad-except
                pass
#            self.aw.kaleidoPID = self.kaleidoPIDFlag.isChecked()
            self.aw.mugmaHost = self.mugmaHost.text().strip()
            try:
                self.aw.mugmaPort = int(self.mugmaPort.text())
            except Exception: # pylint: disable=broad-except
                pass
            self.aw.colorTrack_mean_window_size = self.colorTrackMeanSpinBox.value()
            self.aw.colorTrack_median_window_size = self.colorTrackMedianSpinBox.value()
            for i in range(8):
                self.aw.qmc.phidget1018_async[i] = self.asyncCheckBoxes[i].isChecked()
                self.aw.qmc.phidget1018_ratio[i] = self.ratioCheckBoxes[i].isChecked()
                self.aw.qmc.phidget1018_dataRates[i] = self.aw.qmc.phidget_dataRatesValues[self.dataRateCombos[i].currentIndex()]
                self.aw.qmc.phidget1018_changeTriggers[i] = self.aw.qmc.phidget1018_changeTriggersValues[self.changeTriggerCombos[i].currentIndex()]
                self.aw.qmc.phidgetVCP100x_voltageRanges[i] = self.aw.qmc.phidgetVCP100x_voltageRangeValues[self.voltageRangeCombos[i].currentIndex()]

            # LCD visibility
            self.aw.LCD2frame.setVisible(self.aw.qmc.BTlcd if self.aw.qmc.swaplcds else self.aw.qmc.ETlcd)
            self.aw.LCD3frame.setVisible(self.aw.qmc.ETlcd if self.aw.qmc.swaplcds else self.aw.qmc.BTlcd)
            if self.aw.largeLCDs_dialog:
                self.aw.largeLCDs_dialog.updateVisiblitiesETBT()
            if self.aw.largePIDLCDs_dialog:
                self.aw.largePIDLCDs_dialog.updateVisiblitiesPID()
            if self.aw.largeExtraLCDs_dialog:
                self.aw.largeExtraLCDs_dialog.reLayout() # names, styles and visibilties might have changed

            # restart PhidgetManager
            try:
                self.aw.qmc.restartPhidgetManager()
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)

            self.aw.qmc.intChannel.cache_clear() # device type and thus int channels might have been changed
            self.aw.qmc.clearLCDs()
            self.aw.qmc.redraw(recomputeAllDeltas=False)
            self.aw.sendmessage(message)
            #open serial conf Dialog
            #if device is not None or not external-program (don't need serial settings config)
            if (self.aw.qmc.device not in self.aw.qmc.nonSerialDevices or (self.aw.qmc.device == 134 and self.aw.santokerSerial) or
                (self.aw.qmc.device == 138 and self.aw.kaleidoSerial)) and self.TabWidget.currentIndex() in {0,1,6}:
                QTimer.singleShot(700, self.aw.setcommport)
            self.close()
            self.accept()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            _t, _e, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' device accept(): {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def showExtradevHelp(self, _checked:bool = False) -> None:
        from help import symbolic_help # type: ignore [attr-defined,unused-ignore] # pylint: disable=no-name-in-module
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate('Form Caption','Symbolic Formulas Help'),
                symbolic_help.content())

    @pyqtSlot(bool)
    def showSymbolicHelp(self, _checked:bool = False) -> None:
        from help import symbolic_help # type: ignore [attr-defined,unused-ignore] # pylint: disable=no-name-in-module
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate('Form Caption','Symbolic Formulas Help'),
                symbolic_help.content())

    @pyqtSlot(bool)
    def showhelpprogram(self, _checked:bool = False) -> None:
        from help import programs_help # type: ignore [attr-defined,unused-ignore] # pylint: disable=no-name-in-module
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate('Form Caption','External Programs Help'),
                programs_help.content())

    def closeHelp(self) -> None:
        self.aw.closeHelpDialog(self.helpdialog)

    @pyqtSlot(int)
    def tabSwitched(self, _:int) -> None:
        self.closeHelp()
