# -*- coding: utf-8 -*-
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
# Marko Luther, 2020

import sys
import time as libtime
import re
import platform
import logging
try:
    from typing import Final
except ImportError:
    # for Python 3.7:
    from typing_extensions import Final

from artisanlib.util import deltaLabelUTF8
from artisanlib.dialogs import ArtisanResizeablDialog
from artisanlib.widgets import MyQComboBox, MyQDoubleSpinBox


_log: Final = logging.getLogger(__name__)

try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtCore import (Qt, pyqtSlot, QSettings) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import (QStandardItem, QColor) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QWidget, QCheckBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,  # @UnusedImport @Reimport  @UnresolvedImport
                                 QPushButton, QSpinBox, QTabWidget, QComboBox, QDialogButtonBox, QGridLayout, # @UnusedImport @Reimport  @UnresolvedImport
                                 QGroupBox, QRadioButton, QSizePolicy, # @UnusedImport @Reimport  @UnresolvedImport
                                 QTableWidget, QMessageBox, QHeaderView) # @UnusedImport @Reimport  @UnresolvedImport
except Exception:
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import (Qt, pyqtSlot, QSettings) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import (QStandardItem, QColor) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QWidget, QCheckBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, # @UnusedImport @Reimport  @UnresolvedImport
                                 QPushButton, QSpinBox, QTabWidget, QComboBox, QDialogButtonBox, QGridLayout, # @UnusedImport @Reimport  @UnresolvedImport
                                 QGroupBox, QRadioButton, QSizePolicy, # @UnusedImport @Reimport  @UnresolvedImport
                                 QTableWidget, QMessageBox, QHeaderView) # @UnusedImport @Reimport  @UnresolvedImport


class DeviceAssignmentDlg(ArtisanResizeablDialog):
    def __init__(self, parent = None, aw = None, activeTab = 0):
        super().__init__(parent,aw)
        self.setWindowTitle(QApplication.translate("Form Caption","Device Assignment"))
        self.setModal(True)

        self.helpdialog = None
                    
        ################ TAB 1   WIDGETS
        #ETcurve
        self.ETcurve = QCheckBox(QApplication.translate("CheckBox", "ET"))
        self.ETcurve.setChecked(self.aw.qmc.ETcurve)
        #BTcurve
        self.BTcurve = QCheckBox(QApplication.translate("CheckBox", "BT"))
        self.BTcurve.setChecked(self.aw.qmc.BTcurve)
        #ETlcd
        self.ETlcd = QCheckBox(QApplication.translate("CheckBox", "ET"))
        self.ETlcd.setChecked(self.aw.qmc.ETlcd)
        #BTlcd
        self.BTlcd = QCheckBox(QApplication.translate("CheckBox", "BT"))
        self.BTlcd.setChecked(self.aw.qmc.BTlcd)
        #swaplcd
        self.swaplcds = QCheckBox(QApplication.translate("CheckBox", "Swap"))
        self.swaplcds.setChecked(self.aw.qmc.swaplcds)
        self.curveHBox = QHBoxLayout()
        self.curveHBox.setContentsMargins(10,5,10,5)
        self.curveHBox.setSpacing(5)
        self.curveHBox.addWidget(self.ETcurve)
        self.curveHBox.addSpacing(10)
        self.curveHBox.addWidget(self.BTcurve)
        self.curveHBox.addStretch()
        self.curves = QGroupBox(QApplication.translate("GroupBox","Curves"))
        self.curves.setLayout(self.curveHBox)
        self.lcdHBox = QHBoxLayout()
        self.lcdHBox.setContentsMargins(0,5,0,5)
        self.lcdHBox.setSpacing(5)
        self.lcdHBox.addWidget(self.ETlcd)
        self.lcdHBox.addSpacing(10)
        self.lcdHBox.addWidget(self.BTlcd)
        self.lcdHBox.addSpacing(15)
        self.lcdHBox.addWidget(self.swaplcds)
        self.lcds = QGroupBox(QApplication.translate("GroupBox","LCDs"))
        self.lcds.setLayout(self.lcdHBox)
        
        self.deviceLoggingFlag = QCheckBox(QApplication.translate("Label", "Logging"))
        self.deviceLoggingFlag.setChecked(self.aw.qmc.device_logging)
        
        self.controlButtonFlag = QCheckBox(QApplication.translate("Label", "Control"))
        self.controlButtonFlag.setChecked(self.aw.qmc.Controlbuttonflag)
        self.controlButtonFlag.stateChanged.connect(self.showControlbuttonToggle)
        
        self.nonpidButton = QRadioButton(QApplication.translate("Radio Button","Meter"))
        self.pidButton = QRadioButton(QApplication.translate("Radio Button","PID"))
        self.arduinoButton = QRadioButton(QApplication.translate("Radio Button","TC4"))
        self.programButton = QRadioButton(QApplication.translate("Radio Button","Prog"))
        #As a main device, don't show the devices that start with a "+"
        # devices with a first letter "+" are extra devices an depend on another device
        # each device provides 2 curves
        #don't show devices with a "-". Devices with a - at front are either a pid, arduino, or an external program
        dev = self.aw.qmc.devices[:]             #deep copy
        limit = len(dev)
        for _ in range(limit):
            for i in range(len(dev)):
                if dev[i][0] == "+" or dev[i][0] == "-":
                    dev.pop(i)              #note: pop() makes the list smaller that's why there are 2 FOR statements
                    break 
        self.sorted_devices = sorted(dev)
        self.devicetypeComboBox = MyQComboBox()
        
##        self.devicetypeComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
##        self.devicetypeComboBox.view().setTextElideMode(Qt.TextElideMode.ElideNone)
#        # HACK: only needed for the macintosh UI on Qt 5.12 onwords; without long items get cutted in the popup
#        #  note the -7 as the width of the popup is too large if given the correct maximum characters
##        self.devicetypeComboBox.setMinimumContentsLength(max(22,len(max(dev, key=len)) - 7)) # expects # characters, but is to wide
# the following "hack" helped on PyQt5, but seems not to be needed on PyQt6 any longer
#        self.devicetypeComboBox.setSizePolicy(QSizePolicy.Policy.Expanding,self.devicetypeComboBox.sizePolicy().verticalPolicy())

        self.devicetypeComboBox.addItems(self.sorted_devices)
        self.programedit = QLineEdit(self.aw.ser.externalprogram)
        self.outprogramedit = QLineEdit(self.aw.ser.externaloutprogram)
        self.outprogramFlag = QCheckBox(QApplication.translate("CheckBox", "Output"))
        self.outprogramFlag.setChecked(self.aw.ser.externaloutprogramFlag)
        self.outprogramFlag.stateChanged.connect(self.changeOutprogramFlag)         #toggle
        selectprogrambutton =  QPushButton(QApplication.translate("Button","Select"))
        selectprogrambutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        selectprogrambutton.clicked.connect(self.loadprogramname)
        
        # hack to access the Qt automatic translation of the RestoreDefaults button
        db_help = QDialogButtonBox(QDialogButtonBox.StandardButton.Help)
        help_text_translated = db_help.button(QDialogButtonBox.StandardButton.Help).text()
        helpprogrambutton =  QPushButton(help_text_translated)
        self.setButtonTranslations(helpprogrambutton,"Help",QApplication.translate("Button","Help"))
        helpprogrambutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        helpprogrambutton.clicked.connect(self.showhelpprogram)
        selectoutprogrambutton =  QPushButton(QApplication.translate("Button","Select"))
        selectoutprogrambutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        selectoutprogrambutton.clicked.connect(self.loadoutprogramname)
        ###################################################
        # PID
        controllabel =QLabel(QApplication.translate("Label", "Control ET"))
        # 0 = FujiPXG, 1 = FujiPXR3, 2 = DTA, 3 = not used, 4 = PXF
        supported_ET_pids = [("Fuji PXF", 4), ("Fuji PXG", 0), ("Fuji PXR", 1), ("Delta DTA", 2)]
        self.controlpidtypeComboBox = QComboBox()
        self.controlpidtypeComboBox.addItems([item[0] for item in supported_ET_pids])
        cp = self.aw.ser.controlETpid[0]
        self.controlpidtypeComboBox.setCurrentIndex([y[1] for y in supported_ET_pids].index(cp))
        btlabel =QLabel(QApplication.translate("Label", "Read BT"))
        supported_BT_pids = [("", 2), ("Fuji PXF", 4), ("Fuji PXG", 0), ("Fuji PXR", 1), ("Delta DTA", 3)]
        self.btpidtypeComboBox = QComboBox()
        self.btpidtypeComboBox.addItems([item[0] for item in supported_BT_pids])
        self.btpidtypeComboBox.setCurrentIndex([y[1] for y in supported_BT_pids].index(self.aw.ser.readBTpid[0])) #pid type is index 0
        label1 = QLabel(QApplication.translate("Label", "Type"))
        label2 = QLabel(QApplication.translate("Label", "RS485 Unit ID"))
        #rs485 possible unit IDs (1-32); unit 0 is master (computer)
        unitids = list(map(str,list(range(1,33))))
        self.controlpidunitidComboBox = QComboBox()
        self.controlpidunitidComboBox.addItems(unitids)
        self.btpidunitidComboBox = QComboBox()
        self.btpidunitidComboBox.addItems(unitids)
        # index 1 = unitID of the rs485 network
        self.controlpidunitidComboBox.setCurrentIndex(unitids.index(str(self.aw.ser.controlETpid[1])))
        self.btpidunitidComboBox.setCurrentIndex(unitids.index(str(self.aw.ser.readBTpid[1])))
        #Show Fuji PID SV/% LCDs
        self.showFujiLCDs = QCheckBox(QApplication.translate("CheckBox", "PID Duty/Power LCDs"))
        self.showFujiLCDs.setChecked(self.aw.ser.showFujiLCDs)
        #Reuse Modbus port
        self.useModbusPort = QCheckBox(QApplication.translate("CheckBox", "Modbus Port"))
        self.useModbusPort.setChecked(self.aw.ser.useModbusPort)
        ####################################################
        #Arduino TC4 channel config
        arduinoChannels = ["None","1","2","3","4"]
        arduinoETLabel =QLabel(QApplication.translate("Label", "ET Channel"))
        self.arduinoETComboBox = QComboBox()
        self.arduinoETComboBox.addItems(arduinoChannels)
        arduinoBTLabel =QLabel(QApplication.translate("Label", "BT Channel"))
        self.arduinoBTComboBox = QComboBox()
        self.arduinoBTComboBox.addItems(arduinoChannels)
        #check previous settings for radio button
        if self.aw.qmc.device in (0, 26):   #if Fuji pid or Delta DTA pid
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
        arduinoATLabel =QLabel(QApplication.translate("Label", "AT Channel"))
        
        arduinoTemperatures = ["None","T1","T2","T3","T4","T5","T6"]
        self.arduinoATComboBox = QComboBox()
        self.arduinoATComboBox.addItems(arduinoTemperatures)
        self.arduinoATComboBox.setCurrentIndex(arduinoTemperatures.index(self.aw.ser.arduinoATChannel))
        self.showControlButton = QCheckBox(QApplication.translate("CheckBox", "PID Firmware"))
        self.showControlButton.setChecked(self.aw.qmc.PIDbuttonflag)
        self.showControlButton.stateChanged.connect(self.PIDfirmwareToggle)
        FILTLabel =QLabel(QApplication.translate("Label", "Filter"))
        self.FILTspinBoxes = []
        for i in range(4):
            spinBox = QSpinBox()
            spinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
            spinBox.setRange(0,99)
            spinBox.setSingleStep(5)
            spinBox.setSuffix(" %")
            spinBox.setValue(self.aw.ser.ArduinoFILT[i])
            self.FILTspinBoxes.append(spinBox)
        ####################################################
        
        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.okEvent)
        self.dialogbuttons.rejected.connect(self.cancelEvent)
        
        labelETadvanced = QLabel(QApplication.translate("Label", "ET Y(x)"))
        labelBTadvanced = QLabel(QApplication.translate("Label", "BT Y(x)"))
        self.ETfunctionedit = QLineEdit(str(self.aw.qmc.ETfunction))
        self.BTfunctionedit = QLineEdit(str(self.aw.qmc.BTfunction))
        symbolicHelpButton = QPushButton(help_text_translated)
        self.setButtonTranslations(symbolicHelpButton,"Help",QApplication.translate("Button","Help"))
        symbolicHelpButton.setMaximumSize(symbolicHelpButton.sizeHint())
        symbolicHelpButton.setMinimumSize(symbolicHelpButton.minimumSizeHint())
        symbolicHelpButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        symbolicHelpButton.clicked.connect(self.showSymbolicHelp)
        ##########################    TAB 2  WIDGETS   "EXTRA DEVICES"
        #table for showing data
        self.devicetable = QTableWidget()
        self.devicetable.setTabKeyNavigation(True)
        self.createDeviceTable()
        self.copydeviceTableButton = QPushButton(QApplication.translate("Button", "Copy Table"))
        self.copydeviceTableButton.setToolTip(QApplication.translate("Tooltip","Copy table to clipboard, OPTION or ALT click for tabular text"))
        self.copydeviceTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.copydeviceTableButton.clicked.connect(self.copyDeviceTabletoClipboard)
        self.addButton = QPushButton(QApplication.translate("Button","Add"))
        self.addButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.addButton.setMinimumWidth(100)
        #self.addButton.setMaximumWidth(100)
        self.addButton.clicked.connect(self.adddevice)
        # hack to access the Qt automatic translation of the RestoreDefaults button
        db_reset = QDialogButtonBox(QDialogButtonBox.StandardButton.Reset)
        reset_text_translated = db_reset.button(QDialogButtonBox.StandardButton.Reset).text()
        resetButton =  QPushButton(reset_text_translated)
        self.setButtonTranslations(resetButton,"Reset",QApplication.translate("Button","Reset"))
        resetButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        resetButton.setMinimumWidth(100)
        resetButton.clicked.connect(self.resetextradevices)
        extradevHelpButton = QPushButton(help_text_translated)
        self.setButtonTranslations(extradevHelpButton,"Help",QApplication.translate("Button","Help"))
        extradevHelpButton.setMinimumWidth(100)
        extradevHelpButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        extradevHelpButton.clicked.connect(self.showExtradevHelp)
        self.delButton = QPushButton(QApplication.translate("Button","Delete"))
        self.delButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.delButton.setMinimumWidth(100)
        #self.delButton.setMaximumWidth(100)
        self.delButton.clicked.connect(self.deldevice)
        self.recalcButton = QPushButton(QApplication.translate("Button","Update Profile"))
        self.recalcButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.recalcButton.setMinimumWidth(100)
        self.recalcButton.setToolTip(QApplication.translate("Tooltip","Recaclulates all Virtual Devices and updates their values in the profile"))
        self.recalcButton.clicked.connect(self.updateVirtualdevicesinprofile_clicked)
        self.enableDisableAddDeleteButtons()
        ##########     LAYOUTS
        # create Phidget box
        phidgetProbeTypeItems = ["K", "J", "E", "T"]
        phidgetBox1048 = QGridLayout()
        self.asyncCheckBoxes1048 = []
        self.ratioCheckBoxes1048 = []
        self.changeTriggerCombos1048 = []
        self.probeTypeCombos = []
        for i in range(1,5):
            changeTriggersCombo = QComboBox()
            changeTriggersCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            model = changeTriggersCombo.model()
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
            model = probeTypeCombo.model()
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
        model = self.dataRateCombo1048.model()
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
        phidgetBox1048.setSpacing(1)
            
        typeLabel = QLabel(QApplication.translate("Label","Type"))
        asyncLabel = QLabel(QApplication.translate("Label","Async"))
        changeTriggerLabel = QLabel(QApplication.translate("Label","Change"))
        rateLabel = QLabel(QApplication.translate("Label","Rate"))
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
        phidget1048GroupBox = QGroupBox("1048/1051/TMP1100/TMP1101 TC")
        phidget1048GroupBox.setLayout(phidget1048VBox)
        phidget1048GroupBox.setContentsMargins(0,0,0,0)
        phidget1048HBox.setContentsMargins(0,0,0,0)
        phidget1048VBox.setContentsMargins(0,0,0,0)
        
        # Phidget IR
        phidgetBox1045 = QGridLayout()
        phidgetBox1045.setSpacing(1)
        self.changeTriggerCombos1045 = QComboBox()
        self.changeTriggerCombos1045.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = self.changeTriggerCombos1045.model()
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
        asyncLabel = QLabel(QApplication.translate("Label","Async"))
        changeTriggerLabel = QLabel(QApplication.translate("Label","Change"))
        rateLabel = QLabel(QApplication.translate("Label","Rate")) 
                
        self.dataRateCombo1045 = QComboBox()
        self.dataRateCombo1045.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = self.dataRateCombo1045.model()
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
        
        EmissivityLabel = QLabel(QApplication.translate("Label","Emissivity"))
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
        phidget1045GroupBox = QGroupBox("1045 IR")
        phidget1045GroupBox.setLayout(phidget1045VBox)
        phidget1045VBox.setContentsMargins(0,0,0,0) 


        # 1046 RTD
        phidgetBox1046 = QGridLayout()
        phidgetBox1046.setSpacing(1)
        self.gainCombos1046 = []
        self.formulaCombos1046 = []
        self.asyncCheckBoxes1046 = []
        for i in range(1,5):
            gainCombo = QComboBox()
            gainCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            
            model = gainCombo.model()
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
            model = formulaCombo.model()
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
        model = self.dataRateCombo1046.model()
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
        phidgetBox1046.setSpacing(5)
     
        gainLabel = QLabel(QApplication.translate("Label","Gain"))
        formulaLabel = QLabel(QApplication.translate("Label","Wiring"))
        asyncLabel = QLabel(QApplication.translate("Label","Async"))
        rateLabel = QLabel(QApplication.translate("Label","Rate"))
        phidgetBox1046.addWidget(gainLabel,1,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1046.addWidget(formulaLabel,2,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1046.addWidget(asyncLabel,3,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1046.addWidget(rateLabel,4,0,Qt.AlignmentFlag.AlignRight)
        phidget1046HBox = QHBoxLayout()
        phidget1046HBox.addStretch()
        phidget1046HBox.addLayout(phidgetBox1046)
        phidget1046HBox.addStretch()
        phidget1046VBox = QVBoxLayout()
        phidget1046VBox.addLayout(phidget1046HBox)
        phidget1046VBox.addStretch()
        phidget1046GroupBox = QGroupBox("1046 RTD")
        phidget1046GroupBox.setLayout(phidget1046VBox)
        phidget1046GroupBox.setContentsMargins(0,10,0,0)
        phidget1046HBox.setContentsMargins(0,0,0,0)
        phidget1046VBox.setContentsMargins(0,0,0,0)
        
        # TMP1200 RTD
        phidgetBox1200 = QGridLayout()
        phidgetBox1200.setSpacing(1)
        phidgetBox1200_2 = QGridLayout()
        phidgetBox1200_2.setSpacing(1)

        self.formulaCombo1200 = QComboBox()
        self.formulaCombo1200.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = self.formulaCombo1200.model()
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
        model = self.wireCombo1200.model()
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
        model = self.changeTriggerCombo1200.model()
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
        model = self.rateCombo1200.model()
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
        model = self.formulaCombo1200_2.model()
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
        model = self.wireCombo1200_2.model()
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
        model = self.changeTriggerCombo1200_2.model()
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
        model = self.rateCombo1200_2.model()
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
        
        typeLabel = QLabel(QApplication.translate("Label","Type"))
        wireLabel = QLabel(QApplication.translate("Label","Wiring"))
        asyncLabel = QLabel(QApplication.translate("Label","Async"))
        changeLabel = QLabel(QApplication.translate("Label","Change"))
        rateLabel = QLabel(QApplication.translate("Label","Rate"))
        
        typeLabel2 = QLabel(QApplication.translate("Label","Type"))
        wireLabel2 = QLabel(QApplication.translate("Label","Wiring"))
        asyncLabel2 = QLabel(QApplication.translate("Label","Async"))
        changeLabel2 = QLabel(QApplication.translate("Label","Change"))
        rateLabel2 = QLabel(QApplication.translate("Label","Rate"))
        
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
        phidget1200_tabs.addTab(phidget1200_tab1_widget,"A")
        
        phidget1200_tab2_widget = QWidget()
        phidget1200_tab2_widget.setLayout(phidget1200VBox_2)
        phidget1200_tabs.addTab(phidget1200_tab2_widget,"B")
        
        phidgetGroupBoxLayout = QVBoxLayout()
        phidgetGroupBoxLayout.addWidget(phidget1200_tabs)
           
#        phidgetBox1200_2.setSpacing(1)
        phidgetGroupBoxLayout.setContentsMargins(0,0,0,0) # left, top, right, bottom
        
        phidget1200GroupBox = QGroupBox("TMP1200 RTD")
        phidget1200GroupBox.setLayout(phidgetGroupBoxLayout)
        phidget1200GroupBox.setContentsMargins(0,2,0,0) # left, top, right, bottom
        
        
        # DAQ1400 VI
        powerLabel = QLabel(QApplication.translate("Label","Power"))
        modeLabel = QLabel(QApplication.translate("Label","Mode"))

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
        phidgetBox1400.setSpacing(1)
        phidgetBox1400.addWidget(powerLabel,0,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1400.addWidget(self.powerCombo1400,0,1)
        phidgetBox1400.addWidget(modeLabel,1,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1400.addWidget(self.modeCombo1400,1,1)

        phidget1400HBox = QHBoxLayout()
        phidget1400HBox.addLayout(phidgetBox1400)
        phidget1400VBox = QVBoxLayout()
        phidget1400VBox.addLayout(phidget1400HBox)
        phidget1400VBox.addStretch()
        
        phidget1400GroupBox = QGroupBox("DAQ1400 VI")
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
        phdget10481045GroupBoxHBox.setContentsMargins(2,0,2,0)
        phdget10481045GroupBoxHBox.setSpacing(1)


        # Phidget IO 1018
        # per each of the 8-channels: raw flag / data rate popup / change trigger popup
        phidgetBox1018 = QGridLayout()
        phidgetBox1018.setSpacing(1)
        self.asyncCheckBoxes = []
        self.ratioCheckBoxes = []
        self.dataRateCombos = []
        self.changeTriggerCombos = []
        self.voltageRangeCombos = []
        for i in range(1,9):
            dataRatesCombo = QComboBox()
            dataRatesCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            model = dataRatesCombo.model()
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
            model = changeTriggersCombo.model()
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
            model = voltageRangeCombo.model()
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

        asyncLabel = QLabel(QApplication.translate("Label","Async"))
        dataRateLabel = QLabel(QApplication.translate("Label","Rate"))
        changeTriggerLabel = QLabel(QApplication.translate("Label","Change"))
        ratioLabel = QLabel(QApplication.translate("Label","Ratio"))
        rangeLabel = QLabel(QApplication.translate("Label","Range"))
        phidgetBox1018.addWidget(asyncLabel,2,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1018.addWidget(changeTriggerLabel,3,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1018.addWidget(dataRateLabel,4,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1018.addWidget(rangeLabel,5,0,Qt.AlignmentFlag.AlignRight)
        phidgetBox1018.addWidget(ratioLabel,6,0,Qt.AlignmentFlag.AlignRight)
        phidget1018HBox = QVBoxLayout()
        phidget1018HBox.addLayout(phidgetBox1018)
        phidget1018GroupBox = QGroupBox("1010/1011/1013/1018/1019/HUB0000/SBC/DAQ1400/VCP100x IO")
        phidget1018GroupBox.setLayout(phidget1018HBox)
        phidget1018HBox.setContentsMargins(0,0,0,0)
        self.phidgetBoxRemoteFlag = QCheckBox()
        self.phidgetBoxRemoteFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.phidgetBoxRemoteFlag.setChecked(self.aw.qmc.phidgetRemoteFlag)
        phidgetServerIdLabel = QLabel(QApplication.translate("Label","Host"))
        self.phidgetServerId = QLineEdit(self.aw.qmc.phidgetServerID)
        self.phidgetServerId.setMinimumWidth(200)
        phidgetPasswordLabel = QLabel(QApplication.translate("Label","Password"))
        self.phidgetPassword = QLineEdit(self.aw.qmc.phidgetPassword)
        self.phidgetPassword.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        self.phidgetPassword.setMinimumWidth(100)
        phidgetPortLabel = QLabel(QApplication.translate("Label","Port"))
        self.phidgetPort = QLineEdit(str(self.aw.qmc.phidgetPort))
        self.phidgetPort.setMaximumWidth(70)
        self.phidgetBoxRemoteOnlyFlag = QCheckBox(QApplication.translate("Label","Remote Only"))
        self.phidgetBoxRemoteOnlyFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.phidgetBoxRemoteOnlyFlag.setChecked(self.aw.qmc.phidgetRemoteOnlyFlag)
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
        phidgetNetworkGroupBox = QGroupBox(QApplication.translate("GroupBox","Network"))
        phidgetNetworkGroupBox.setLayout(phidgetNetworkGrid)
        phidget10451018HBox = QHBoxLayout()
        phidget10451018HBox.addWidget(phidget1045GroupBox)
        phidget10451018HBox.addStretch()
        phidget10451018HBox.addWidget(phidget1018GroupBox)
        phidget10451018HBox.setSpacing(1)
        phidgetVBox = QVBoxLayout()
        phidgetVBox.addLayout(phdget10481045GroupBoxHBox)
        phidgetVBox.addLayout(phidget10451018HBox)
        phidgetVBox.addWidget(phidgetNetworkGroupBox)
        phidgetVBox.addStretch()
        phidgetVBox.setSpacing(5)
        # yoctopuce widgets
        self.yoctoBoxRemoteFlag = QCheckBox()
        self.yoctoBoxRemoteFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.yoctoBoxRemoteFlag.setChecked(self.aw.qmc.yoctoRemoteFlag)
        yoctoServerIdLabel = QLabel(QApplication.translate("Label","VirtualHub"))
        self.yoctoServerId = QLineEdit(self.aw.qmc.yoctoServerID)
        YoctoEmissivityLabel = QLabel(QApplication.translate("Label","Emissivity"))
        self.yoctoEmissivitySpinBox = MyQDoubleSpinBox()
        self.yoctoEmissivitySpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.yoctoEmissivitySpinBox.setRange(0.,1.)
        self.yoctoEmissivitySpinBox.setSingleStep(.1) 
        self.yoctoEmissivitySpinBox.setValue(self.aw.qmc.YOCTO_emissivity) 
        yoctoServerBox = QHBoxLayout()
        yoctoServerBox.addWidget(yoctoServerIdLabel)
        yoctoServerBox.addSpacing(10)
        yoctoServerBox.addWidget(self.yoctoServerId)
        yoctoServerBox.setContentsMargins(0,0,0,0)
        yoctoServerBox.setSpacing(10)
        yoctoNetworkGrid = QGridLayout()
        yoctoNetworkGrid.addWidget(self.yoctoBoxRemoteFlag,0,0)
        yoctoNetworkGrid.addLayout(yoctoServerBox,0,1)
#        yoctoNetworkGrid.setContentsMargins(10,10,10,10)
        yoctoNetworkGrid.setSpacing(20)
        yoctoNetworkGroupBox = QGroupBox(QApplication.translate("GroupBox","Network"))
        yoctoNetworkGroupBox.setLayout(yoctoNetworkGrid)
        yoctoIRGrid = QGridLayout()
        yoctoIRGrid.addWidget(YoctoEmissivityLabel,0,0)
        yoctoIRGrid.addWidget(self.yoctoEmissivitySpinBox,0,1)
        yoctoIRHorizontalLayout = QHBoxLayout()
        yoctoIRHorizontalLayout.addLayout(yoctoIRGrid)
        yoctoIRHorizontalLayout.addStretch()
        self.yoctoDataRateCombo = QComboBox()
        self.yoctoDataRateCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        model = self.yoctoDataRateCombo.model()
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
        yoctoAsyncGroupBox = QGroupBox(QApplication.translate("GroupBox","Async"))
        yoctoAsyncGroupBox.setLayout(yoctoAsyncHorizontalLayout)
        yoctoIRGroupBox = QGroupBox(QApplication.translate("GroupBox","IR"))
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

        # HACK: only needed for the macintosh UI on Qt 5.12 onwords; withou long items get cutted in the popup
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
        self.elevationSpinBox.setValue(self.aw.qmc.elevation)
        self.elevationSpinBox.setSuffix(" " + QApplication.translate("Label","MASL"))
        temperatureDeviceLabel = QLabel(QApplication.translate("Label","Temperature"))
        humidityDeviceLabel = QLabel(QApplication.translate("Label","Humidity"))
        pressureDeviceLabel = QLabel(QApplication.translate("Label","Pressure"))
        elevationLabel = QLabel(QApplication.translate("Label","Elevation"))
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
        PIDGroupBox = QGroupBox(QApplication.translate("GroupBox","PID"))
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
        arduinoGroupBox = QGroupBox(QApplication.translate("GroupBox","Arduino TC4"))
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
        programGroupBox = QGroupBox(QApplication.translate("GroupBox","External Program"))
        programGroupBox.setLayout(programlayout)
        programlayout.setContentsMargins(5,10,5,5)
        programGroupBox.setContentsMargins(0,12,0,0)
        #ET BT symbolic adjustments/assignments Box
        self.updateETBTButton = QPushButton(QApplication.translate("Button","Update Profile"))
        self.updateETBTButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.updateETBTButton.setToolTip(QApplication.translate("Tooltip","Recaclulates ET and BT and updates their values in the profile"))
        self.updateETBTButton.clicked.connect(self.updateETBTinprofile)

        adjustmentHelp = QHBoxLayout()
        adjustmentHelp.addWidget(self.updateETBTButton)
        adjustmentHelp.addStretch()
        adjustmentHelp.addWidget(symbolicHelpButton)
        adjustmentGroupBox = QGroupBox(QApplication.translate("GroupBox","Symbolic Assignments"))
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
        #main tab widget
        self.TabWidget = QTabWidget()
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        self.TabWidget.addTab(C1Widget,QApplication.translate("Tab","ET/BT"))
        C2Widget = QWidget()
        C2Widget.setLayout(tab2Layout)
        self.TabWidget.addTab(C2Widget,QApplication.translate("Tab","Extra Devices"))
        C3Widget = QWidget()
        C3Widget.setLayout(tab3Layout)
        self.TabWidget.addTab(C3Widget,QApplication.translate("Tab","Symb ET/BT"))
        C4Widget = QWidget()
        C4Widget.setLayout(tab4Layout)
        self.TabWidget.addTab(C4Widget,QApplication.translate("Tab","Phidgets"))
        C5Widget = QWidget()
        C5Widget.setLayout(tab5Layout)
        self.TabWidget.addTab(C5Widget,QApplication.translate("Tab","Yoctopuce"))
        C6Widget = QWidget()
        C6Widget.setLayout(tab6Layout)
        self.TabWidget.addTab(C6Widget,QApplication.translate("Tab","Ambient"))
        self.TabWidget.currentChanged.connect(self.tabSwitched)
        #incorporate layouts
        Mlayout = QVBoxLayout()
        Mlayout.addWidget(self.TabWidget)
        Mlayout.addLayout(buttonLayout)
        Mlayout.setSpacing(0)
        Mlayout.setContentsMargins(5,10,5,5)
        self.setLayout(Mlayout)
        if platform.system() == 'Windows':
            self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        else:
            self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok).setFocus()
        settings = QSettings()
        if settings.contains("DeviceAssignmentGeometry"):
            self.restoreGeometry(settings.value("DeviceAssignmentGeometry"))
        self.TabWidget.setCurrentIndex(activeTab)

    @pyqtSlot(int)
    def changeOutprogramFlag(self,_):
        self.aw.ser.externaloutprogramFlag = not self.aw.ser.externaloutprogramFlag

    @pyqtSlot(int)
    def asyncFlagStateChanged1048(self,x):
        try:
            i = self.asyncCheckBoxes1048.index(self.sender())
            if x == 0:
                # disable ChangeTrigger selection
                self.changeTriggerCombos1048[i].setEnabled(False)
            else:
                # enable ChangeTrigger selection
                self.changeTriggerCombos1048[i].setEnabled(True)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    @pyqtSlot(int)
    def asyncFlagStateChanged1045(self,x):
        if x == 0:
            # disable ChangeTrigger selection
            self.changeTriggerCombos1045.setEnabled(False)
        else:
            # enable ChangeTrigger selection
            self.changeTriggerCombos1045.setEnabled(True)
            
    @pyqtSlot(int)
    def asyncFlagStateChanged1200(self,x):
        if x == 0:
            # disable ChangeTrigger selection
            self.changeTriggerCombo1200.setEnabled(False)
        else:
            # enable ChangeTrigger selection
            self.changeTriggerCombo1200.setEnabled(True)

    @pyqtSlot(int)
    def asyncFlagStateChanged1200_2(self,x):
        if x == 0:
            # disable ChangeTrigger selection
            self.changeTriggerCombo1200_2.setEnabled(False)
        else:
            # enable ChangeTrigger selection
            self.changeTriggerCombo1200_2.setEnabled(True)

    @pyqtSlot(int)
    def asyncFlagStateChanged(self,x):
        try:
            i = self.asyncCheckBoxes.index(self.sender())
            if x == 0:
                # disable DataRate selection
                self.changeTriggerCombos[i].setEnabled(False)
            else:
                # enable ChangeTrigger and if that is 0 also DataRate selection
                self.changeTriggerCombos[i].setEnabled(True)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    @staticmethod
    def createItems(strs):
        items = []
        for i in range(len(strs)):
            item = QStandardItem(strs[i])
            items.append(item)
        return items

    @pyqtSlot(int)
    def PIDfirmwareToggle(self,i):
        if i:
            self.aw.qmc.PIDbuttonflag = True
        else:
            self.aw.qmc.PIDbuttonflag = False
        self.aw.showControlButton()

    @pyqtSlot(int)
    def showControlbuttonToggle(self,i):
        if i:
            self.aw.qmc.Controlbuttonflag = True
        else:
            self.aw.qmc.Controlbuttonflag = False
        self.aw.showControlButton()

    def createDeviceTable(self):
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
            self.devicetable.clearSelection()
            self.devicetable.setRowCount(nddevices)
            self.devicetable.setColumnCount(columns)
            self.devicetable.setHorizontalHeaderLabels([QApplication.translate("Table", "Device"),
                                                        QApplication.translate("Table", "Color 1"),
                                                        QApplication.translate("Table", "Color 2"),
                                                        QApplication.translate("Table", "Label 1"),
                                                        QApplication.translate("Table", "Label 2"),
                                                        QApplication.translate("Table", "y1(x)"),
                                                        QApplication.translate("Table", "y2(x)"),
                                                        QApplication.translate("Table", "LCD 1"),
                                                        QApplication.translate("Table", "LCD 2"),
                                                        QApplication.translate("Table", "Curve 1"),
                                                        QApplication.translate("Table", "Curve 2"),
                                                        deltaLabelUTF8 + " " + QApplication.translate("GroupBox","Axis") + " 1",
                                                        deltaLabelUTF8 + " " + QApplication.translate("GroupBox","Axis") + " 2",
                                                        QApplication.translate("Table", "Fill 1"),
                                                        QApplication.translate("Table", "Fill 2")])
            self.devicetable.setAlternatingRowColors(True)
            self.devicetable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.devicetable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.devicetable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.devicetable.setShowGrid(True)
            self.devicetable.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            if nddevices:
                dev = self.aw.qmc.devices[:]             #deep copy
                limit = len(dev)
                for _ in range(limit):
                    for i in range(len(dev)):
                        if dev[i][0] == "-" or dev[i] == "NONE": # non manual device or deactivated device in extra device list
                            dev.pop(i)              #note: pop() makes the list smaller 
                            break 
                devices = sorted(map(lambda x:(x[1:] if x.startswith("+") else x),dev), key=lambda x: (x[1:] if x.startswith("+") else x))
                for i in range(nddevices):
                    try:
                        typeComboBox =  MyQComboBox()
#                        typeComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
#                        typeComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
                        typeComboBox.addItems(devices[:])
                        try:
                            dev_name = self.aw.qmc.devices[max(0,self.aw.qmc.extradevices[i]-1)]
                            if dev_name[0] == "+":
                                dev_name = dev_name[1:]
                            typeComboBox.setCurrentIndex(devices.index(dev_name))
                        except Exception: # pylint: disable=broad-except
                            pass
                        color1Button = QPushButton(self.aw.qmc.extradevicecolor1[i])
                        color1Button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                        color1Button.clicked.connect(self.setextracolor1)
                        textcolor = self.aw.labelBorW(self.aw.qmc.extradevicecolor1[i])
                        color1Button.setStyleSheet("background-color: %s; color: %s"%(self.aw.qmc.extradevicecolor1[i], textcolor))
                        color2Button = QPushButton(self.aw.qmc.extradevicecolor2[i])
                        color2Button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                        color2Button.clicked.connect(self.setextracolor2)
                        textcolor = self.aw.labelBorW(self.aw.qmc.extradevicecolor2[i])
                        color2Button.setStyleSheet("background-color: %s; color: %s"%(self.aw.qmc.extradevicecolor2[i], textcolor))
                        name1edit = QLineEdit(self.aw.qmc.extraname1[i])
                        name2edit = QLineEdit(self.aw.qmc.extraname2[i])
                        mexpr1edit = QLineEdit(self.aw.qmc.extramathexpression1[i])
                        mexpr2edit = QLineEdit(self.aw.qmc.extramathexpression2[i])
                        mexpr1edit.setToolTip(QApplication.translate("Tooltip","Example: 100 + 2*x"))
                        mexpr2edit.setToolTip(QApplication.translate("Tooltip","Example: 100 + x"))
                        LCD1visibilityComboBox =  QCheckBox()
                        if self.aw.extraLCDvisibility1[i]:
                            LCD1visibilityComboBox.setCheckState(Qt.CheckState.Checked)
                        else:
                            LCD1visibilityComboBox.setCheckState(Qt.CheckState.Unchecked)
                        LCD1visibilityComboBox.stateChanged.connect(self.updateLCDvisibility1)
                        LCD2visibilityComboBox =  QCheckBox()
                        if self.aw.extraLCDvisibility2[i]:
                            LCD2visibilityComboBox.setCheckState(Qt.CheckState.Checked)
                        else:
                            LCD2visibilityComboBox.setCheckState(Qt.CheckState.Unchecked)
                        LCD2visibilityComboBox.stateChanged.connect(self.updateLCDvisibility2)
                        Curve1visibilityComboBox =  QCheckBox()
                        if self.aw.extraCurveVisibility1[i]:
                            Curve1visibilityComboBox.setCheckState(Qt.CheckState.Checked)
                        else:
                            Curve1visibilityComboBox.setCheckState(Qt.CheckState.Unchecked)
                        Curve1visibilityComboBox.stateChanged.connect(self.updateCurveVisibility1)
                        Curve2visibilityComboBox =  QCheckBox()
                        if self.aw.extraCurveVisibility2[i]:
                            Curve2visibilityComboBox.setCheckState(Qt.CheckState.Checked)
                        else:
                            Curve2visibilityComboBox.setCheckState(Qt.CheckState.Unchecked)
                        Curve2visibilityComboBox.stateChanged.connect(self.updateCurveVisibility2)
                        Delta1ComboBox =  QCheckBox()
                        if self.aw.extraDelta1[i]:
                            Delta1ComboBox.setCheckState(Qt.CheckState.Checked)
                        else:
                            Delta1ComboBox.setCheckState(Qt.CheckState.Unchecked)
                        Delta1ComboBox.stateChanged.connect(self.updateDelta1)
                        Delta2ComboBox =  QCheckBox()
                        if self.aw.extraDelta2[i]:
                            Delta2ComboBox.setCheckState(Qt.CheckState.Checked)
                        else:
                            Delta2ComboBox.setCheckState(Qt.CheckState.Unchecked)
                        Delta2ComboBox.stateChanged.connect(self.updateDelta2)
                        Fill1SpinBox =  QSpinBox()
                        Fill1SpinBox.setSingleStep(1)
                        Fill1SpinBox.setRange(0,100)
                        Fill1SpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
                        Fill1SpinBox.setValue(self.aw.extraFill1[i])
                        Fill1SpinBox.editingFinished.connect(self.updateFill1)
                        Fill2SpinBox =  QSpinBox()
                        Fill2SpinBox.setSingleStep(1)
                        Fill2SpinBox.setRange(0,100)
                        Fill2SpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
                        Fill2SpinBox.setValue(self.aw.extraFill2[i])
                        Fill2SpinBox.editingFinished.connect(self.updateFill2)
                        #add widgets to the table
                        self.devicetable.setCellWidget(i,0,typeComboBox)
                        self.devicetable.setCellWidget(i,1,color1Button)
                        self.devicetable.setCellWidget(i,2,color2Button)
                        self.devicetable.setCellWidget(i,3,name1edit)
                        self.devicetable.setCellWidget(i,4,name2edit)
                        self.devicetable.setCellWidget(i,5,mexpr1edit)
                        self.devicetable.setCellWidget(i,6,mexpr2edit)
                        self.devicetable.setCellWidget(i,7,LCD1visibilityComboBox)
                        self.devicetable.setCellWidget(i,8,LCD2visibilityComboBox)
                        self.devicetable.setCellWidget(i,9,Curve1visibilityComboBox)
                        self.devicetable.setCellWidget(i,10,Curve2visibilityComboBox)
                        self.devicetable.setCellWidget(i,11,Delta1ComboBox)
                        self.devicetable.setCellWidget(i,12,Delta2ComboBox)
                        self.devicetable.setCellWidget(i,13,Fill1SpinBox)
                        self.devicetable.setCellWidget(i,14,Fill2SpinBox)
                    except Exception as e: # pylint: disable=broad-except
                        _log.exception(e)
                header = self.devicetable.horizontalHeader()
                header.setStretchLastSection(True)
                self.devicetable.resizeColumnsToContents()
                # remember the columnwidth
                for i in range(len(self.aw.qmc.devicetablecolumnwidths)):
                    try:
                        self.devicetable.setColumnWidth(i, self.aw.qmc.devicetablecolumnwidths[i])
                    except Exception: # pylint: disable=broad-except
                        pass
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + " createDeviceTable(): {0}").format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def copyDeviceTabletoClipboard(self,_=False):
        import prettytable
        nrows = self.devicetable.rowCount() 
        ncols = self.devicetable.columnCount()
        clipboard = ""
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.AltModifier:  #alt click
            tbl = prettytable.PrettyTable()
            fields = []
            re_strip = re.compile('[\u2009]')  #thin space is not read properly by prettytable
            for c in range(ncols):
                fields.append(re_strip.sub('',self.devicetable.horizontalHeaderItem(c).text()))
            tbl.field_names = fields
            for r in range(nrows):
                rows = []
                rows.append(self.devicetable.cellWidget(r,0).currentText())
                rows.append(self.devicetable.cellWidget(r,1).palette().button().color().name())
                rows.append(self.devicetable.cellWidget(r,2).palette().button().color().name())
                rows.append(self.devicetable.cellWidget(r,3).text())
                rows.append(self.devicetable.cellWidget(r,4).text())
                rows.append(self.devicetable.cellWidget(r,5).text())
                rows.append(self.devicetable.cellWidget(r,6).text())
                rows.append(str(self.devicetable.cellWidget(r,7).isChecked()))
                rows.append(str(self.devicetable.cellWidget(r,8).isChecked()))
                rows.append(str(self.devicetable.cellWidget(r,9).isChecked()))
                rows.append(str(self.devicetable.cellWidget(r,10).isChecked()))
                rows.append(str(self.devicetable.cellWidget(r,11).isChecked()))
                rows.append(str(self.devicetable.cellWidget(r,12).isChecked()))
                rows.append(str(self.devicetable.cellWidget(r,13).value()))
                rows.append(str(self.devicetable.cellWidget(r,14).value()))
                tbl.add_row(rows)
            clipboard = tbl.get_string()
        else:
            for c in range(ncols):
                clipboard += self.devicetable.horizontalHeaderItem(c).text()
                if c != (ncols-1):
                    clipboard += '\t'
            clipboard += '\n'
            for r in range(nrows):
                clipboard += self.devicetable.cellWidget(r,0).currentText() + '\t'
                clipboard += self.devicetable.cellWidget(r,1).palette().button().color().name() + '\t'
                clipboard += self.devicetable.cellWidget(r,2).palette().button().color().name() + '\t'
                clipboard += self.devicetable.cellWidget(r,3).text() + '\t'
                clipboard += self.devicetable.cellWidget(r,4).text() + '\t'
                clipboard += self.devicetable.cellWidget(r,5).text() + '\t'
                clipboard += self.devicetable.cellWidget(r,6).text() + '\t'
                clipboard += str(self.devicetable.cellWidget(r,7).isChecked()) + '\t'
                clipboard += str(self.devicetable.cellWidget(r,8).isChecked()) + '\t'
                clipboard += str(self.devicetable.cellWidget(r,9).isChecked()) + '\t'
                clipboard += str(self.devicetable.cellWidget(r,10).isChecked()) + '\t'
                clipboard += str(self.devicetable.cellWidget(r,11).isChecked()) + '\t'
                clipboard += str(self.devicetable.cellWidget(r,12).isChecked()) + '\t'
                clipboard += str(self.devicetable.cellWidget(r,13).value()) + '\t'
                clipboard += str(self.devicetable.cellWidget(r,14).value()) + '\n'
        # copy to the system clipboard
        sys_clip = QApplication.clipboard()
        sys_clip.setText(clipboard)
        self.aw.sendmessage(QApplication.translate("Message","Device table copied to clipboard"))

    @pyqtSlot(bool)
    def loadprogramname(self,_):
        fileName = self.aw.ArtisanOpenFileDialog()
        if fileName:
            if ' ' in fileName:
                self.programedit.setText('"' + fileName + '"')
            else:
                self.programedit.setText(fileName)

    @pyqtSlot(bool)
    def loadoutprogramname(self,_):
        fileName = self.aw.ArtisanOpenFileDialog()
        if fileName:
            self.outprogramedit.setText(fileName)
            self.aw.ser.externaloutprogram = self.outprogramedit.text()

    def enableDisableAddDeleteButtons(self):
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
    def adddevice(self,_):
        try:
            self.savedevicetable()
            #addDevice() is located in aw so that the same function can be used in init after dynamically loading settings
            self.aw.addDevice()
            self.createDeviceTable()
            # workaround a table redrawbug in PyQt 5.14.2 on macOS
            if len(self.aw.qmc.extradevices)>1:
                self.repaint()
            self.enableDisableAddDeleteButtons()
            self.aw.qmc.resetlinecountcaches()
            self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + " adddevice(): {0}").format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def deldevice(self,_):
        try:
            self.savedevicetable()
            bindex = len(self.aw.qmc.extradevices)-1
            selected = self.devicetable.selectedRanges()
            if len(selected) > 0:
                bindex = selected[0].topRow()
            if 0 <= bindex < len(self.aw.qmc.extradevices):
                self.delextradevice(bindex)
            self.aw.updateExtraLCDvisibility()
            self.aw.qmc.resetlinecountcaches()
            self.enableDisableAddDeleteButtons()
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + " deldevice(): {0}").format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def resetextradevices(self,_):
        try:
            self.aw.resetExtraDevices()
            #update table
            self.createDeviceTable()
            #enable/disable buttons
            self.enableDisableAddDeleteButtons()
            #redraw
            self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + " resetextradevices(): {0}").format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    def delextradevice(self,x):
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
            self.aw.updateExtraLCDvisibility()
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
                if self.aw.extraser[x].SP.isOpen():
                    self.aw.extraser[x].SP.close()
                    libtime.sleep(0.7) # on OS X opening a serial port too fast after closing the port get's disabled
                self.aw.extraser.pop(x)
            self.createDeviceTable()
            self.aw.qmc.resetlinecountcaches()
            self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception as ex: # pylint: disable=broad-except
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + "delextradevice(): {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

    def savedevicetable(self,redraw=True):
        try:
            for i in range(len(self.aw.qmc.extradevices)):
                typecombobox = self.devicetable.cellWidget(i,0)
                #cellWidget(i,1) and cellWidget(i,2) are saved automatically when there is a change. No need to save here.
                name1edit = self.devicetable.cellWidget(i,3)
                name2edit = self.devicetable.cellWidget(i,4)
                mexpr1edit = self.devicetable.cellWidget(i,5)
                mexpr2edit = self.devicetable.cellWidget(i,6)
                try:
                    self.aw.qmc.extradevices[i] = self.aw.qmc.devices.index(str(typecombobox.currentText())) + 1
                except Exception: # pylint: disable=broad-except
                    try: # might be a +device
                        self.aw.qmc.extradevices[i] = self.aw.qmc.devices.index("+" + str(typecombobox.currentText())) + 1
                    except Exception: # pylint: disable=broad-except
                        self.aw.qmc.extradevices[i] = 0
                if name1edit:
                    self.aw.qmc.extraname1[i] = name1edit.text()
                else:
                    self.aw.qmc.extraname1[i] = ""
                if name2edit:
                    self.aw.qmc.extraname2[i] = name2edit.text()
                else:
                    self.aw.qmc.extraname2[i] = ""
                    
                l1 = "<b>" + self.aw.qmc.extraname1[i] + "</b>"
                try:
                    self.aw.extraLCDlabel1[i].setText(l1.format(self.aw.qmc.etypes[0],self.aw.qmc.etypes[1],self.aw.qmc.etypes[2],self.aw.qmc.etypes[3]))
                except Exception: # pylint: disable=broad-except
                    self.aw.extraLCDlabel1[i].setText(l1)
                l2 = "<b>" + self.aw.qmc.extraname2[i] + "</b>"
                try:
                    self.aw.extraLCDlabel2[i].setText(l2.format(self.aw.qmc.etypes[0],self.aw.qmc.etypes[1],self.aw.qmc.etypes[2],self.aw.qmc.etypes[3]))
                except Exception: # pylint: disable=broad-except
                    self.aw.extraLCDlabel2[i].setText(l2)
                if mexpr2edit:
                    self.aw.qmc.extramathexpression1[i] = mexpr1edit.text()
                else:
                    self.aw.qmc.extramathexpression1[i] = ""
                if mexpr2edit:
                    self.aw.qmc.extramathexpression2[i] = mexpr2edit.text()
                else:
                    self.aw.qmc.extramathexpression2[i] = ""
            #update legend with new curves
            if redraw:
                self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception as ex: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + "savedevicetable(): {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def updateVirtualdevicesinprofile_clicked(self,_):
        self.updateVirtualdevicesinprofile(redraw=True)

    def updateVirtualdevicesinprofile(self,redraw=True):
        try:
            self.savedevicetable(redraw=False)
            if self.aw.calcVirtualdevices(update=True):
                if redraw:
                    self.aw.qmc.redraw(recomputeAllDeltas=False)
        except Exception as ex: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + "updateVirtualdevicesinprofile(): {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def updateETBTinprofile(self,_):
        try:
            # be sure there is an equation to process
            nonempty_ETfunction = bool(self.ETfunctionedit.text() is not None and len(self.ETfunctionedit.text().strip()))
            nonempty_BTfunction = bool(self.BTfunctionedit.text() is not None and len(self.BTfunctionedit.text().strip()))
            if (nonempty_ETfunction or nonempty_BTfunction):

                # confirm the action
                string = QApplication.translate("Message", "Clicking YES will overwrite the existing ET and BT values in this profile with the symbolic values defined here.  Click CANCEL to abort.")
                reply = QMessageBox.warning(self.aw,QApplication.translate("Message", "Caution - About to overwrite profile data"),string,
                            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel)
                if reply == QMessageBox.StandardButton.Cancel:
                    return

                # confirm updating the dependent Virtual Extra Devices?
                updatevirtualextradevices = False
                etorbt = re.compile('Y1|Y2|T1|T2|R1|R2')
                for j in range(len(self.aw.qmc.extradevices)):
                    if (re.search(etorbt,self.aw.qmc.extramathexpression1[j]) or re.search(etorbt,self.aw.qmc.extramathexpression2[j])):
                        string = QApplication.translate("Message", "At least one Virtual Extra Device depends on ET or BT.  Do you want to update all the Virtual Extra Devices after ET and BT are updated?")
                        reply = QMessageBox.warning(self.aw,QApplication.translate("Message", "Caution - About to overwrite profile data"),string,
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
                    self.aw.sendmessage(QApplication.translate("Message", "Symbolic values updated."))
                else:
                    self.aw.sendmessage(QApplication.translate("Message", "Symbolic values were not updated."))
            else:
                self.aw.sendmessage(QApplication.translate("Message", "Nothing here to process."))
        except Exception as ex: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + "updateETBTinprofile(): {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(int)
    def updateLCDvisibility1(self,x):
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),7)
        if r is not None:
            self.aw.extraLCDvisibility1[r] = bool(x)
            self.aw.extraLCDframe1[r].setVisible(bool(x))

    @pyqtSlot(int)
    def updateLCDvisibility2(self,x):
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),8)
        if r is not None:
            self.aw.extraLCDvisibility2[r] = bool(x)
            self.aw.extraLCDframe2[r].setVisible(bool(x))

    @pyqtSlot(int)
    def updateCurveVisibility1(self,x):
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),9)
        if r is not None:
            self.aw.extraCurveVisibility1[r] = bool(x)
            self.aw.qmc.resetlinecountcaches()

    @pyqtSlot(int)
    def updateCurveVisibility2(self,x):
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),10)
        if r is not None:
            self.aw.extraCurveVisibility2[r] = bool(x)
            self.aw.qmc.resetlinecountcaches()

    @pyqtSlot(int)
    def updateDelta1(self,x):
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),11)
        if r is not None:
            self.aw.extraDelta1[r] = bool(x)

    @pyqtSlot(int)
    def updateDelta2(self,x):
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),12)
        if r is not None:
            self.aw.extraDelta2[r] = bool(x)
    
    @pyqtSlot()
    def updateFill1(self):
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),13)
        if r is not None:
            self.aw.extraFill1[r] = self.sender().value()
    
    @pyqtSlot()
    def updateFill2(self):
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),14)
        if r is not None:
            self.aw.extraFill2[r] = self.sender().value()

    @pyqtSlot(bool)
    def setextracolor1(self,_):
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),1)
        if r is not None:
            self.setextracolor(1,r)

    @pyqtSlot(bool)
    def setextracolor2(self,_):
        r = self.aw.findWidgetsRow(self.devicetable,self.sender(),2)
        if r is not None:
            self.setextracolor(2,r)

    def setextracolor(self,l,i):
        try:
            #line 1
            if l == 1:
                # use native no buttons dialog on Mac OS X, blocks otherwise
                colorf = self.aw.colordialog(QColor(self.aw.qmc.extradevicecolor1[i]),True,self)
                if colorf.isValid():
                    colorname = str(colorf.name())
                    self.aw.qmc.extradevicecolor1[i] = colorname
                    # set LCD label color
                    self.aw.setLabelColor(self.aw.extraLCDlabel1[i],QColor(colorname))
                    self.devicetable.cellWidget(i,1).setStyleSheet("background-color: %s; color: %s"%(self.aw.qmc.extradevicecolor1[i], self.aw.labelBorW(self.aw.qmc.extradevicecolor1[i])))
                    self.devicetable.cellWidget(i,1).setText(colorname)
                    self.aw.checkColors([(self.aw.qmc.extraname1[i], self.aw.qmc.extradevicecolor1[i], QApplication.translate("Label","Background"), self.aw.qmc.palette['background'])])
                    self.aw.checkColors([(self.aw.qmc.extraname1[i], self.aw.qmc.extradevicecolor1[i], QApplication.translate("Label","Legend bkgnd"), self.aw.qmc.palette['background'])])
            #line 2
            elif l == 2:
                # use native no buttons dialog on Mac OS X, blocks otherwise
                colorf = self.aw.colordialog(QColor(self.aw.qmc.extradevicecolor2[i]),True,self)
                if colorf.isValid():
                    colorname = str(colorf.name())
                    self.aw.qmc.extradevicecolor2[i] = colorname
                    # set LCD label color
                    self.aw.setLabelColor(self.aw.extraLCDlabel2[i],QColor(colorname))
                    self.devicetable.cellWidget(i,2).setStyleSheet("background-color: %s; color: %s"%(self.aw.qmc.extradevicecolor2[i], self.aw.labelBorW(self.aw.qmc.extradevicecolor2[i])))
                    self.devicetable.cellWidget(i,2).setText(colorname)
                    self.aw.checkColors([(self.aw.qmc.extraname2[i], self.aw.qmc.extradevicecolor2[i], QApplication.translate("Label","Background"), self.aw.qmc.palette['background'])])
                    self.aw.checkColors([(self.aw.qmc.extraname2[i], self.aw.qmc.extradevicecolor2[i], QApplication.translate("Label","Legend bkgnd"),self.aw.qmc.palette['background'])])
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + " setextracolor(): {0}").format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    def close(self):
        self.closeHelp()
        settings = QSettings()
        #save window geometry
        settings.setValue("DeviceAssignmentGeometry",self.saveGeometry()) 
        self.aw.DeviceAssignmentDlg_activeTab = self.TabWidget.currentIndex()
#        self.aw.closeEventSettings() # save all app settings
    
    @pyqtSlot()
    def cancelEvent(self):
        self.aw.DeviceAssignmentDlg_activeTab = self.TabWidget.currentIndex()
        self.close()
        self.reject()

    @pyqtSlot()
    def okEvent(self):
        try:
            self.aw.qmc.device_logging = self.deviceLoggingFlag.isChecked()
            
            #save any extra devices here
            self.savedevicetable(redraw=False)
            self.aw.qmc.devicetablecolumnwidths = [self.devicetable.columnWidth(c) for c in range(self.devicetable.columnCount())]
            
            message = QApplication.translate("Message","Device not set")
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
                if str(self.controlpidtypeComboBox.currentText()) == "Fuji PXG":
                    self.aw.ser.controlETpid[0] = 0
                    str1 = "Fuji PXG"
                elif str(self.controlpidtypeComboBox.currentText()) == "Fuji PXR":
                    self.aw.ser.controlETpid[0] = 1
                    str1 = "Fuji PXR"
                elif str(self.controlpidtypeComboBox.currentText()) == "Delta DTA":
                    self.aw.ser.controlETpid[0] = 2
                    str1 = "Delta DTA"
                elif str(self.controlpidtypeComboBox.currentText()) == "Fuji PXF":
                    self.aw.ser.controlETpid[0] = 4
                    str1 = "Fuji PXF"
                self.aw.ser.controlETpid[1] =  int(str(self.controlpidunitidComboBox.currentText()))
                if str(self.btpidtypeComboBox.currentText()) == "Fuji PXG":
                    self.aw.ser.readBTpid[0] = 0
                    str2 = "Fuji PXG"
                elif str(self.btpidtypeComboBox.currentText()) == "Fuji PXR":
                    self.aw.ser.readBTpid[0] = 1
                    str2 = "Fuji PXR"
                elif str(self.btpidtypeComboBox.currentText()) == "":
                    self.aw.ser.readBTpid[0] = 2
                    str2 = "None"
                elif str(self.btpidtypeComboBox.currentText()) == "Delta DTA":
                    self.aw.ser.readBTpid[0] = 3
                    str2 = "Delta DTA"
                elif str(self.btpidtypeComboBox.currentText()) == "Fuji PXF":
                    self.aw.ser.readBTpid[0] = 4
                    str2 = "Fuji PXF"
                self.aw.ser.readBTpid[1] =  int(str(self.btpidunitidComboBox.currentText()))
                if self.showFujiLCDs.isChecked():
                    self.aw.ser.showFujiLCDs = True
                else:
                    self.aw.ser.showFujiLCDs = False
                if self.useModbusPort.isChecked():
                    self.aw.ser.useModbusPort = True
                else:
                    self.aw.ser.useModbusPort = False
                #If fuji pid
                if str1 != "Delta DTA":
                    if self.aw.qmc.device != 0:
                        self.aw.qmc.device = 0
                        #self.aw.ser.comport = "COM4"
                        self.aw.ser.baudrate = 9600
                        self.aw.ser.bytesize = 8
                        self.aw.ser.parity= 'O'
                        self.aw.ser.stopbits = 1
                        self.aw.ser.timeout = 1.0
                #else if DTA pid
                else:
                    if self.aw.qmc.device != 26:
                        self.aw.qmc.device = 26
                        #self.aw.ser.comport = "COM4"
                        self.aw.ser.baudrate = 2400
                        self.aw.ser.bytesize = 8
                        self.aw.ser.parity= 'N'
                        self.aw.ser.stopbits = 1
                        self.aw.ser.timeout = 1.0
                message = QApplication.translate("Message","PID to control ET set to {0} {1}" + \
                                                 " ; PID to read BT set to {2} {3}").format(str1,str(self.aw.ser.controlETpid[1]),str2,str(self.aw.ser.readBTpid[1]))
            elif self.arduinoButton.isChecked():
                meter = "Arduino (TC4)"
                if self.aw.qmc.device != 19:
                    self.aw.qmc.device = 19
                    self.aw.ser.baudrate = 115200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.8
                    self.aw.ser.ArduinoIsInitialized = 0 # ensure the Arduino gets reinitalized if settings changed
                    message = QApplication.translate("Message","Device set to {0}. Now, check Serial Port settings").format(meter)
            elif self.programButton.isChecked():
                meter = self.programedit.text()
                self.aw.ser.externalprogram = meter
                self.aw.qmc.device = 27
                message = QApplication.translate("Message","Device set to {0}. Now, check Serial Port settings").format(meter)
            elif self.nonpidButton.isChecked():
                meter = str(self.devicetypeComboBox.currentText())
                if meter == "Omega HH806AU" and self.aw.qmc.device != 1:
                    self.aw.qmc.device = 1
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 19200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'E'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                elif meter == "Omega HH506RA" and self.aw.qmc.device != 2:
                    self.aw.qmc.device = 2
                    #self.aw.ser.comport = "/dev/tty.usbserial-A2001Epn"
                    self.aw.ser.baudrate = 2400
                    self.aw.ser.bytesize = 7
                    self.aw.ser.parity= 'E'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    self.aw.ser.HH506RAid = "X" # ensure the HH506RA gets reinitalized if settings changed
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                elif meter == "CENTER 309" and self.aw.qmc.device != 3:
                    self.aw.qmc.device = 3
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                elif meter == "CENTER 306" and self.aw.qmc.device != 4:
                    self.aw.qmc.device = 4
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                elif meter == "CENTER 305" and self.aw.qmc.device != 5:
                    self.aw.qmc.device = 5
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to CENTER 305, which is equivalent to CENTER 306. Now, choose serial port").format(meter)
                elif meter == "CENTER 304" and self.aw.qmc.device != 6:
                    self.aw.qmc.device = 6
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}, which is equivalent to CENTER 309. Now, choose serial port").format(meter)
                elif meter == "CENTER 303" and self.aw.qmc.device != 7:
                    self.aw.qmc.device = 7
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                elif meter == "CENTER 302" and self.aw.qmc.device != 8:
                    self.aw.qmc.device = 8
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}, which is equivalent to CENTER 303. Now, choose serial port").format(meter)
                elif meter == "CENTER 301" and self.aw.qmc.device != 9:
                    self.aw.qmc.device = 9
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}, which is equivalent to CENTER 303. Now, choose serial port").format(meter)
                elif meter == "CENTER 300" and self.aw.qmc.device != 10:
                    self.aw.qmc.device = 10
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}, which is equivalent to CENTER 303. Now, choose serial port").format(meter)
                elif meter == "VOLTCRAFT K204" and self.aw.qmc.device != 11:
                    self.aw.qmc.device = 11
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}, which is equivalent to CENTER 309. Now, choose serial port").format(meter)
                elif meter == "VOLTCRAFT K202" and self.aw.qmc.device != 12:
                    self.aw.qmc.device = 12
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}, which is equivalent to CENTER 306. Now, choose serial port").format(meter)
                elif meter == "VOLTCRAFT 300K" and self.aw.qmc.device != 13:
                    self.aw.qmc.device = 13
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.5
                    message = QApplication.translate("Message","Device set to {0}, which is equivalent to CENTER 303. Now, choose serial port").format(meter)
                elif meter == "VOLTCRAFT 302KJ" and self.aw.qmc.device != 14:
                    self.aw.qmc.device = 14
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}, which is equivalent to CENTER 303. Now, choose serial port").format(meter)
                elif meter == "EXTECH 421509" and self.aw.qmc.device != 15:
                    self.aw.qmc.device = 15
                    #self.aw.ser.comport = "/dev/tty.usbserial-A2001Epn"
                    self.aw.ser.baudrate = 2400
                    self.aw.ser.bytesize = 7
                    self.aw.ser.parity= 'E'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}, which is equivalent to Omega HH506RA. Now, choose serial port").format(meter)
                elif meter == "Omega HH802U" and self.aw.qmc.device != 16:
                    self.aw.qmc.device = 16
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 19200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'E'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}, which is equivalent to Omega HH806AU. Now, choose serial port").format(meter)
                elif meter == "Omega HH309" and self.aw.qmc.device != 17:
                    self.aw.qmc.device = 17
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                #special device manual mode. No serial settings.
                elif meter == "NONE":
                    self.aw.qmc.device = 18
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                    st = ""
                    # ensure that events button is shown
                    self.aw.eventsbuttonflag = 1
                    self.aw.buttonEVENT.setVisible(True)
                    message = QApplication.translate("Message","Device set to {0}{1}").format(meter,st)
                ##########################
                ####  DEVICE 19 is the Arduino/TC4
                ##########################
                elif meter == "TE VA18B" and self.aw.qmc.device != 20:
                    self.aw.qmc.device = 20
                    #self.aw.ser.comport = "COM7"
                    self.aw.ser.baudrate = 2400
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 1.0
                    message = QApplication.translate("Message","Device set to {0}. Now, check Serial Port settings").format(meter)
                ##########################
                ####  DEVICE 21 is +309_34 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 22 is +PID DUTY% but +DEVICE cannot be set as main device
                ##########################
                elif meter == "Omega HHM28[6]" and self.aw.qmc.device != 23:
                    self.aw.qmc.device = 23
                    #self.aw.ser.comport = "COM1"
                    self.aw.ser.baudrate = 2400
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 1.0
                    message = QApplication.translate("Message","Device set to {0}. Now, check Serial Port settings").format(meter)
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
                elif meter == "MODBUS" and self.aw.qmc.device != 29:
                    self.aw.qmc.device = 29
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 115200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.6
                    message = QApplication.translate("Message","Device set to {0}. Now, choose Modbus serial port or IP address").format(meter)
                elif meter == "VOLTCRAFT K201" and self.aw.qmc.device != 30:
                    self.aw.qmc.device = 30
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}, which is equivalent to CENTER 302. Now, choose serial port").format(meter)
                elif meter == "Amprobe TMD-56" and self.aw.qmc.device != 31:
                    self.aw.qmc.device = 31
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 19200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'E'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}, which is equivalent to Omega HH806AU. Now, choose serial port").format(meter)
                ##########################
                ####  DEVICE 32 is +ArduinoTC4 56 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 33 is +MODBUS 34 but +DEVICE cannot be set as main device
                ##########################
                elif meter == "Phidget 1048 4xTC 01":
                    self.aw.qmc.device = 34
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ####  DEVICE 35 is +Phidget 1048 4xTC 23 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 36 is +Phidget 1048 4xTC AT but +DEVICE cannot be set as main device
                ##########################
                elif meter == "Phidget 1046 4xRTD 01":
                    self.aw.qmc.device = 37
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ####  DEVICE 38 is +Phidget 1046 4xRTD 23 but +DEVICE cannot be set as main device
                ##########################
                elif meter == "Mastech MS6514" and self.aw.qmc.device != 39:
                    self.aw.qmc.device = 39
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                ##########################
                elif meter == "Phidget IO 01":
                    self.aw.qmc.device = 40
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
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
                elif meter == "Yocto Thermocouple":
                    self.aw.qmc.device = 45
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                elif meter == "Yocto PT100":
                    self.aw.qmc.device = 46
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                elif meter == "Phidget 1045 IR":
                    self.aw.qmc.device = 47
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ####  DEVICE 48 is an external program 34
                ##########################
                ##########################
                ####  DEVICE 49 is an external program 56
                ##########################
                elif meter == "DUMMY" and self.aw.qmc.device != 50: # including a dummy serial device (can be used for serial commands)
                    self.aw.qmc.device = 50
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.5
                ##########################
                ####  DEVICE 51 is +304_34 but +DEVICE cannot be set as main device
                ##########################
                elif meter == "Phidget 1051 1xTC 01":
                    self.aw.qmc.device = 52
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                elif meter == "Hottop BT/ET" and self.aw.qmc.device != 53:
                    self.aw.qmc.device = 53
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 115200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                ##########################
                ####  DEVICE 54 is +Hottop HF but +DEVICE cannot be set as main device
                ##########################
                elif meter == "Omega HH806W" and self.aw.qmc.device != 55:
                    self.aw.qmc.device = 55
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 38400
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'E'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                ##########################
                ####  DEVICE 55 is +MODBUS_56 but +DEVICE cannot be set as main device
                ##########################
                elif meter == "Apollo DT301" and self.aw.qmc.device != 56:
                    self.aw.qmc.device = 56
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                ##########################
                elif meter == "EXTECH 755" and self.aw.qmc.device != 57:
                    self.aw.qmc.device = 57
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                ##########################
                elif meter == "Phidget TMP1101 4xTC 01":
                    self.aw.qmc.device = 58
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ####  DEVICE 59 is +Phidget TMP1101 4xTC 23 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 60 is +Phidget TMP1101 4xTC AT but +DEVICE cannot be set as main device
                ##########################
                ##########################
                elif meter == "Phidget TMP1100 1xTC":
                    self.aw.qmc.device = 61
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                elif meter == "Phidget 1011 IO 01":
                    self.aw.qmc.device = 62
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                elif meter == "Phidget HUB IO 01":
                    self.aw.qmc.device = 63
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
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
                elif meter == "VOLTCRAFT PL-125-T2" and self.aw.qmc.device != 67:
                    self.aw.qmc.device = 67
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                ##########################
                ##########################
                elif meter == "Phidget TMP1200 1xRTD A":
                    self.aw.qmc.device = 68
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                elif meter == "Phidget IO Digital 01":
                    self.aw.qmc.device = 69
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
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
                elif meter == "Phidget 1011 IO Digital 01":
                    self.aw.qmc.device = 73
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                elif meter == "Phidget HUB IO Digital 01":
                    self.aw.qmc.device = 74
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ##########################
                ####  DEVICE 75 is +Phidget HUB IO Digital 23 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 76 is +Phidget HUB IO Digital 45 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                elif meter == "VOLTCRAFT PL-125-T4" and self.aw.qmc.device != 77:
                    self.aw.qmc.device = 77
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                ##########################
                ##########################
                ####  DEVICE 78 is +VOLTCRAFT PL-125-T4 34 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                elif meter == "S7":
                    self.aw.qmc.device = 79
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
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
                elif meter == "Aillio Bullet R1 BT/DT":
                    self.aw.qmc.device = 83
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ####  DEVICE 88 and 89 are an external program 78 and 910
                ##########################
                ##########################
                ####  DEVICE 90 and 91 are an slider 01 and slider 23
                ##########################
                ##########################
                ####  DEVICE 92-94 are an Probat Middleware and have no serial setup
                ##########################
                elif meter == "Probat Middleware":
                    self.aw.qmc.device = 92
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ####  DEVICE 95 is Phidget DAQ1400 Current
                ##########################
                elif meter == "Phidget DAQ1400 Current":
                    self.aw.qmc.device = 95
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ####  DEVICE 96 is Phidget DAQ1400 Frequency
                ##########################
                elif meter == "Phidget DAQ1400 Frequency":
                    self.aw.qmc.device = 96
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ####  DEVICE 97 is Phidget DAQ1400 Digital
                ##########################
                elif meter == "Phidget DAQ1400 Digital":
                    self.aw.qmc.device = 97
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ####  DEVICE 98 is Phidget DAQ1400 Voltage
                ##########################
                elif meter == "Phidget DAQ1400 Voltage":
                    self.aw.qmc.device = 98
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ####  DEVICE 99 is Aillio Bullet R1 IBTS/DT
                ##########################
                elif meter == "Aillio Bullet R1 IBTS/DT":
                    self.aw.qmc.device = 99
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ####  DEVICE 100 are Yocto IR
                ##########################
                elif meter == "Yocto IR":
                    self.aw.qmc.device = 100
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                elif meter == "Behmor BT/CT" and self.aw.qmc.device != 101:
                    self.aw.qmc.device = 101
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 57600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                ##########################
                ####  DEVICE 102 Behmor 34 channel 3 and 4
                ##########################
                elif meter == "VICTOR 86B" and self.aw.qmc.device != 103:
                    self.aw.qmc.device = 103
                    #self.aw.ser.comport = "COM4"
                    self.aw.ser.baudrate = 2400
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.7
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                ##########################
                ####  DEVICE 104 Behmor 56 channel 5 and 6
                ##########################
                ##########################
                ####  DEVICE 105 Behmor 78 channel 7 and 8
                ##########################
                ##########################
                elif meter == "Phidget HUB IO 0":
                    self.aw.qmc.device = 106
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                elif meter == "Phidget HUB IO Digital 0":
                    self.aw.qmc.device = 107
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                elif meter == "Yocto 4-20ma Rx":
                    self.aw.qmc.device = 108
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ####  DEVICE 109 is +MODBUS_78 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 110 is +S7_010 but +DEVICE cannot be set as main device
                ##########################
                elif meter == "WebSocket":
                    self.aw.qmc.device = 111
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ####  DEVICE 112 is +WebSocket 34 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 113 is +WebSocket 56 but +DEVICE cannot be set as main device
                ##########################
                ##########################
                ####  DEVICE 114 is +TMP1200_2 (a second TMP1200 configuration)
                ##########################
                elif meter == "HB BT/ET" and self.aw.qmc.device != 115:
                    self.aw.qmc.device = 115
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 9600
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.8
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
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
                elif meter == "Yocto 0-10V Rx":
                    self.aw.qmc.device = 120
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ##########################
                ####  DEVICE 121 is Yocto milliVolt Rx
                elif meter == "Yocto milliVolt Rx":
                    self.aw.qmc.device = 121
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ##########################
                ####  DEVICE 122 is Yocto Serial
                elif meter == "Yocto Serial":
                    self.aw.qmc.device = 122
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ##########################
                ####  DEVICE 123 is Phidget VCP1000
                elif meter == "Phidget VCP1000":
                    self.aw.qmc.device = 123
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ##########################
                ####  DEVICE 124 is Phidget VCP1001
                elif meter == "Phidget VCP1001":
                    self.aw.qmc.device = 124
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ##########################
                ####  DEVICE 125 is Phidget VCP1002
                elif meter == "Phidget VCP1002":
                    self.aw.qmc.device = 125
                    message = QApplication.translate("Message","Device set to {0}").format(meter)
                ##########################
                ##########################
                elif meter == "ARC BT/ET" and self.aw.qmc.device != 126:
                    self.aw.qmc.device = 126
                    #self.aw.ser.comport = "COM11"
                    self.aw.ser.baudrate = 115200
                    self.aw.ser.bytesize = 8
                    self.aw.ser.parity= 'N'
                    self.aw.ser.stopbits = 1
                    self.aw.ser.timeout = 0.4
                    message = QApplication.translate("Message","Device set to {0}. Now, choose serial port").format(meter)
                ##########################
                ####  DEVICE 127 is +ARC MET/IT
                ##########################
                ##########################
                ####  DEVICE 128 is +ARC AT (points to "+HB AT")


                # ADD DEVICE:

                # ensure that by selecting a real device, the initial sampling rate is set to 3s
                if meter != "NONE":
                    self.aw.qmc.delay = max(self.aw.qmc.delay,self.aw.qmc.min_delay)
            # update Control button visibility
            self.aw.showControlButton()
            
    # ADD DEVICE: to add a device you have to modify several places. Search for the tag "ADD DEVICE:"in the code
    # - add an elif entry above to specify the default serial settings
            #extra devices serial config
            #set of different serial settings modes options
            ssettings: Final = [[9600,8,'O',1,0.5],[19200,8,'E',1,0.5],[2400,7,'E',1,1],[9600,8,'N',1,0.5],
                         [19200,8,'N',1,0.5],[2400,8,'N',1,1],[9600,8,'E',1,0.5],[38400,8,'E',1,0.5],[115200,8,'N',1,0.4],[57600,8,'N',1,0.5]]
            #map device index to a setting mode (choose the one that matches the device)
    # ADD DEVICE: to add a device you have to modify several places. Search for the tag "ADD DEVICE:"in the code
    # - add an entry to devsettings below (and potentially to ssettings above)
            devssettings: Final = [
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
                8  # 128
                ] 
            #init serial settings of extra devices
            for i in range(len(self.aw.qmc.extradevices)):
                if self.aw.qmc.extradevices[i] < len(devssettings) and devssettings[self.aw.qmc.extradevices[i]] < len(ssettings):
                    dsettings = ssettings[devssettings[self.aw.qmc.extradevices[i]]]
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
            for i in range(8):
                self.aw.qmc.phidget1018_async[i] = self.asyncCheckBoxes[i].isChecked()
                self.aw.qmc.phidget1018_ratio[i] = self.ratioCheckBoxes[i].isChecked()
                self.aw.qmc.phidget1018_dataRates[i] = self.aw.qmc.phidget_dataRatesValues[self.dataRateCombos[i].currentIndex()]
                self.aw.qmc.phidget1018_changeTriggers[i] = self.aw.qmc.phidget1018_changeTriggersValues[self.changeTriggerCombos[i].currentIndex()]
                self.aw.qmc.phidgetVCP100x_voltageRanges[i] = self.aw.qmc.phidgetVCP100x_voltageRangeValues[self.voltageRangeCombos[i].currentIndex()]

            # LCD visibility
            self.aw.LCD2frame.setVisible((self.aw.qmc.BTlcd if self.aw.qmc.swaplcds else self.aw.qmc.ETlcd))
            self.aw.LCD3frame.setVisible((self.aw.qmc.ETlcd if self.aw.qmc.swaplcds else self.aw.qmc.BTlcd))
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

            self.aw.qmc.redraw(recomputeAllDeltas=False)
            self.aw.sendmessage(message)
            #open serial conf Dialog
            self.accept()
            #if device is not None or not external-program (don't need serial settings config)
            if not(self.aw.qmc.device in self.aw.qmc.nonSerialDevices):
                self.aw.setcommport()
            self.close()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + " device accept(): {0}").format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def showExtradevHelp(self):
        from help import symbolic_help
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate("Form Caption","Symbolic Formulas Help"),
                symbolic_help.content())

    @pyqtSlot(bool)
    def showSymbolicHelp(self):
        from help import symbolic_help
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate("Form Caption","Symbolic Formulas Help"),
                symbolic_help.content())

    @pyqtSlot(bool)
    def showhelpprogram(self,_=False):
        from help import programs_help
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate("Form Caption","External Programs Help"),
                programs_help.content())

    def closeHelp(self):
        self.aw.closeHelpDialog(self.helpdialog)

    @pyqtSlot(int)
    def tabSwitched(self,_):
        self.closeHelp()
