# -*- coding: utf-8 -*-
#
# ABOUT
# Artisan Fuji PID Dialog

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

from artisanlib.util import stringfromseconds, stringtoseconds
from artisanlib.dialogs import ArtisanDialog
from artisanlib.widgets import MyQComboBox

try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtCore import Qt, pyqtSlot, QRegularExpression, QSettings # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QIntValidator, QRegularExpressionValidator # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QTableWidget, QPushButton, # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QGridLayout, QGroupBox, QLineEdit, # @UnusedImport @Reimport  @UnresolvedImport
        QMessageBox, QRadioButton, QSpinBox, QStatusBar, QTabWidget, QButtonGroup, QDoubleSpinBox, # @UnusedImport @Reimport  @UnresolvedImport
        QTimeEdit, QLayout, QSizePolicy, QHeaderView) # @UnusedImport @Reimport  @UnresolvedImport
except Exception:
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import Qt, pyqtSlot, QRegularExpression, QSettings # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QIntValidator, QRegularExpressionValidator # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QTableWidget, QPushButton, # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QGridLayout, QGroupBox, QLineEdit, # @UnusedImport @Reimport  @UnresolvedImport
        QMessageBox, QRadioButton, QSpinBox, QStatusBar, QTabWidget, QButtonGroup, QDoubleSpinBox, # @UnusedImport @Reimport  @UnresolvedImport
        QTimeEdit, QLayout, QSizePolicy, QHeaderView) # @UnusedImport @Reimport  @UnresolvedImport


############################################################################
######################## Artisan PID CONTROL DIALOG ########################
############################################################################

class PID_DlgControl(ArtisanDialog):
    def __init__(self, parent = None, aw = None, activeTab = 0):
        super().__init__(parent, aw)
        self.setModal(True)
        #self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose) # default is True and this is set by default in ArtisanDialog!
        self.setWindowTitle(QApplication.translate("Form Caption","PID Control"))
        
        # PID tab
        tab1Layout = QVBoxLayout()
        pidGrp = QGroupBox(QApplication.translate("GroupBox","p-i-d"))
        self.pidKp = QDoubleSpinBox()
        self.pidKp.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pidKp.setRange(.0,9999.)
        self.pidKp.setSingleStep(.1)
        self.pidKp.setDecimals(3)
        self.pidKp.setValue(self.aw.pidcontrol.pidKp)
        pidKpLabel = QLabel("kp")
        self.pidKi = QDoubleSpinBox()
        self.pidKi.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pidKi.setRange(.0,9999.)
        self.pidKi.setSingleStep(.1)
        self.pidKi.setDecimals(3)
        self.pidKi.setValue(self.aw.pidcontrol.pidKi)
        pidKiLabel = QLabel("ki")
        self.pidKd = QDoubleSpinBox()
        self.pidKd.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pidKd.setRange(.0,9999.)
        self.pidKd.setSingleStep(.1)
        self.pidKd.setDecimals(3)
        self.pidKd.setValue(self.aw.pidcontrol.pidKd)
        pidKdLabel = QLabel("kd")
        pidSetPID = QPushButton(QApplication.translate("Button","Set"))
        pidSetPID.clicked.connect(self.pidConf)
        pidSetPID.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.pidSource = QComboBox()
        if self.aw.qmc.device == 19 and self.aw.qmc.PIDbuttonflag:
            # Arduino/TC4
            pidSourceItems = ["1","2","3","4"]
            self.pidSource.addItems(pidSourceItems)
            self.pidSource.setCurrentIndex(self.aw.pidcontrol.pidSource - 1)
        else:
            # Hottop or MODBUS or others (self.qmc.device in [53,29])
            pidSourceItems = ["BT","ET"]
            self.pidSource.addItems(pidSourceItems)
            if self.aw.pidcontrol.pidSource == 1:
                self.pidSource.setCurrentIndex(0)
            else:
                self.pidSource.setCurrentIndex(1)
        
        pidSourceLabel = QLabel(QApplication.translate("Label","Source"))

        pidGrid = QGridLayout()
        pidGrid.addWidget(pidKpLabel,0,0)
        pidGrid.addWidget(self.pidKp,0,1)
        pidGrid.addWidget(pidKiLabel,1,0)
        pidGrid.addWidget(self.pidKi,1,1)
        pidGrid.addWidget(pidKdLabel,2,0)
        pidGrid.addWidget(self.pidKd,2,1)


        pidSourceBox = QHBoxLayout()
        pidSourceBox.addStretch()
        pidSourceBox.addWidget(pidSourceLabel)
        pidSourceBox.addWidget(self.pidSource)
        #pidSourceBox.addSpacing(80)
        pidSourceBox.addStretch()
        
        self.pidCycle = QSpinBox()
        self.pidCycle.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pidCycle.setRange(0,99999)
        self.pidCycle.setSingleStep(100)
        self.pidCycle.setValue(self.aw.pidcontrol.pidCycle)
        self.pidCycle.setSuffix(" ms")
        pidCycleLabel = QLabel(QApplication.translate("Label","Cycle"))
        
        pidCycleBox = QHBoxLayout()
        pidCycleBox.addStretch()  
        pidCycleBox.addWidget(pidCycleLabel)
        pidCycleBox.addWidget(self.pidCycle)
        pidCycleBox.addStretch()  
        
        pidSetBox = QHBoxLayout()
        pidSetBox.addStretch()
        pidSetBox.addWidget(pidSetPID)
        
        self.pOnGroup = QButtonGroup()
        self.pOnGroup.setExclusive(True)
        self.pOnE = QRadioButton("P on Error")
        self.pOnGroup.addButton(self.pOnE)
        self.pOnM = QRadioButton("P on Input")
        self.pOnGroup.addButton(self.pOnM)
        self.pOnE.setChecked(self.aw.pidcontrol.pOnE)
        self.pOnM.setChecked(not self.aw.pidcontrol.pOnE)
        if self.aw.pidcontrol.externalPIDControl() in [1,2]:
            self.pOnE.setEnabled(False)
            self.pOnM.setEnabled(False)
        
        pOnLayout = QVBoxLayout() 
        pOnLayout.addWidget(self.pOnE)
        pOnLayout.addWidget(self.pOnM)
        
        pidVBox = QVBoxLayout()
        pidVBox.addLayout(pidSourceBox)
        if self.aw.qmc.device == 19 and self.aw.qmc.PIDbuttonflag: # ArduinoTC4
            pidVBox.addLayout(pidCycleBox)
        pidVBox.addLayout(pOnLayout)
        pidVBox.setAlignment(pOnLayout,Qt.AlignmentFlag.AlignRight)
        pidVBox.addLayout(pidSetBox)
        pidVBox.setAlignment(pidSetBox,Qt.AlignmentFlag.AlignRight)
        
        #PID target (only shown if interal PID for hottop/modbus/TC4 is active
        controlItems = ["None",self.aw.qmc.etypesf(0),self.aw.qmc.etypesf(1),self.aw.qmc.etypesf(2),self.aw.qmc.etypesf(3)]
        #positiveControl
        positiveControlLabel = QLabel(QApplication.translate("Label","Positive"))
        self.positiveControlCombo = QComboBox()
        self.positiveControlCombo.addItems(controlItems)
        self.positiveControlCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.positiveControlCombo.setCurrentIndex(self.aw.pidcontrol.pidPositiveTarget)
        #negativeControl
        negativeControlLabel = QLabel(QApplication.translate("Label","Negative"))
        self.negativeControlCombo = QComboBox()
        self.negativeControlCombo.addItems(controlItems)
        self.negativeControlCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.negativeControlCombo.setCurrentIndex(self.aw.pidcontrol.pidNegativeTarget)
        
        controlSelectorLayout = QGridLayout()
        controlSelectorLayout.addWidget(positiveControlLabel,0,0)
        controlSelectorLayout.addWidget(self.positiveControlCombo,0,1)
        controlSelectorLayout.addWidget(negativeControlLabel,1,0)
        controlSelectorLayout.addWidget(self.negativeControlCombo,1,1)
                
        self.invertControlFlag = QCheckBox(QApplication.translate("Label", "Invert Control"))
        self.invertControlFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.invertControlFlag.setChecked(self.aw.pidcontrol.invertControl)

        controlVBox = QVBoxLayout()
        controlVBox.addLayout(controlSelectorLayout)
        controlVBox.addWidget(self.invertControlFlag)
        
        controlHBox = QHBoxLayout()
        controlHBox.addStretch()
        controlHBox.addLayout(controlVBox)
        controlHBox.addStretch()
        
        pidTargetGrp = QGroupBox(QApplication.translate("GroupBox","Target"))
        pidTargetGrp.setLayout(controlHBox)
        pidTargetGrp.setContentsMargins(0,10,0,0)
        
        pidGridBox = QHBoxLayout()
        pidGridBox.addLayout(pidGrid)
        pidGridBox.addStretch()
        pidGridBox.addLayout(pidVBox)
        if not (self.aw.qmc.device == 19 and self.aw.qmc.PIDbuttonflag): # don't show Targets if TC4 firmware PID is in use
            pidGridBox.addWidget(pidTargetGrp)
        
        pidGridVBox = QVBoxLayout()
        pidGridVBox.addLayout(pidGridBox)
        pidGrp.setLayout(pidGridVBox)
        pidGrp.setContentsMargins(0,10,0,0)
        
        self.pidSV = QSpinBox()
        self.pidSV.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pidSV.setRange(0,999)
        self.pidSV.setSingleStep(10)
        self.pidSV.setValue(self.aw.pidcontrol.svValue)
        pidSVLabel = QLabel(QApplication.translate("Label","SV"))
        
        self.pidSVLookahead = QSpinBox()
        self.pidSVLookahead.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pidSVLookahead.setRange(0,999)
        self.pidSVLookahead.setSingleStep(1)
        self.pidSVLookahead.setValue(self.aw.pidcontrol.svLookahead)
        self.pidSVLookahead.setSuffix(" s")
        pidSVLookaheadLabel = QLabel(QApplication.translate("Label","Lookahead"))
        
        self.pidDutySteps = QSpinBox()
        self.pidDutySteps.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pidDutySteps.setRange(1,10)
        self.pidDutySteps.setSingleStep(1)
        self.pidDutySteps.setValue(self.aw.pidcontrol.dutySteps)  
        self.pidDutySteps.setSuffix(" %")
        pidDutyStepsLabel = QLabel(QApplication.translate("Label","Steps"))
        
        pidSetSV = QPushButton(QApplication.translate("Button","Set"))
        pidSetSV.clicked.connect(self.setSV)
        pidSetSV.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        pidSVModeLabel = QLabel(QApplication.translate("Label","Mode"))
        pidModeItems = [
            QApplication.translate("Label", "Manual"),
            QApplication.translate("Label", "Ramp/Soak"),
            QApplication.translate("Label", "Background")]
        self.pidMode = QComboBox()
        self.pidMode.addItems(pidModeItems)
        self.pidMode.setCurrentIndex(self.aw.pidcontrol.svMode)
        self.pidMode.currentIndexChanged.connect(self.updatePidMode)
        
        self.pidSVbuttonsFlag = QCheckBox(QApplication.translate("Label","Buttons"))
        self.pidSVbuttonsFlag.setChecked(self.aw.pidcontrol.svButtons)
        self.pidSVbuttonsFlag.stateChanged.connect(self.activateONOFFeasySVslot)
        self.pidSVsliderFlag = QCheckBox(QApplication.translate("Label","Slider"))
        self.pidSVsliderFlag.setChecked(self.aw.pidcontrol.svSlider)
        self.pidSVsliderFlag.stateChanged.connect(self.activateSVSlider)
        
        self.pidSVSliderMin = QSpinBox()
        self.pidSVSliderMin.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pidSVSliderMin.setRange(0,999)
        self.pidSVSliderMin.setSingleStep(10)
        self.pidSVSliderMin.setValue(self.aw.pidcontrol.svSliderMin)
        pidSVSliderMinLabel = QLabel(QApplication.translate("Label","Min"))
        self.pidSVSliderMin.valueChanged.connect(self.sliderMinValueChangedSlot)
        
        self.pidSVSliderMax = QSpinBox()
        self.pidSVSliderMax.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pidSVSliderMax.setRange(0,999)
        self.pidSVSliderMax.setSingleStep(10)
        self.pidSVSliderMax.setValue(self.aw.pidcontrol.svSliderMax)
        pidSVSliderMaxLabel = QLabel(QApplication.translate("Label","Max"))
        self.pidSVSliderMax.valueChanged.connect(self.sliderMaxValueChangedSlot)
        
        if self.aw.qmc.mode == "F":
            self.pidSVSliderMin.setSuffix(" F")
            self.pidSVSliderMax.setSuffix(" F")
            self.pidSV.setSuffix(" F")
        elif self.aw.qmc.mode == "C":
            self.pidSVSliderMin.setSuffix(" C")
            self.pidSVSliderMax.setSuffix(" C")
            self.pidSV.setSuffix(" C")
        
        modeBox = QHBoxLayout()
        modeBox.addWidget(pidSVModeLabel)
        modeBox.addWidget(self.pidMode)
        modeBox.addStretch()
        modeBox.addWidget(pidSVLookaheadLabel)
        modeBox.addWidget(self.pidSVLookahead)
        
        sliderBox = QHBoxLayout()
        sliderBox.addWidget(self.pidSVsliderFlag)
        sliderBox.addStretch()
        sliderBox.addWidget(pidSVSliderMinLabel)
        sliderBox.addWidget(self.pidSVSliderMin)
        sliderBox.addSpacing(10)
        sliderBox.addWidget(pidSVSliderMaxLabel)
        sliderBox.addWidget(self.pidSVSliderMax)
        
        svInputBox = QHBoxLayout()
        svInputBox.addWidget(self.pidSVbuttonsFlag)
        svInputBox.addStretch()
        svInputBox.addWidget(pidSVLabel)
        svInputBox.addWidget(self.pidSV)
        svInputBox.addWidget(pidSetSV)
        
        self.dutyMin = QSpinBox()
        self.dutyMin.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.dutyMin.setRange(-100,100)
        self.dutyMin.setSingleStep(10)
        self.dutyMin.setValue(self.aw.pidcontrol.dutyMin)
        self.dutyMin.setSuffix(" %")
        dutyMinLabel = QLabel(QApplication.translate("Label","Min"))
        
        self.dutyMax = QSpinBox()
        self.dutyMax.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.dutyMax.setRange(-100,100)
        self.dutyMax.setSingleStep(10)
        self.dutyMax.setValue(self.aw.pidcontrol.dutyMax) 
        self.dutyMax.setSuffix(" %")
        dutyMaxLabel = QLabel(QApplication.translate("Label","Max"))
        
        svGrpBox = QVBoxLayout()
        svGrpBox.addStretch()
        svGrpBox.addLayout(modeBox)
        svGrpBox.addLayout(sliderBox)
        svGrpBox.addLayout(svInputBox)
        svGrpBox.addStretch()
        svGrp = QGroupBox(QApplication.translate("GroupBox","Set Value"))
        svGrp.setLayout(svGrpBox)
        svGrp.setContentsMargins(0,10,0,0)
        
        dutyGrid = QGridLayout()
        dutyGrid.addWidget(pidDutyStepsLabel,0,0)
        dutyGrid.addWidget(self.pidDutySteps,0,1)
        dutyGrid.addWidget(dutyMaxLabel,1,0)
        dutyGrid.addWidget(self.dutyMax,1,1)
        dutyGrid.addWidget(dutyMinLabel,2,0)
        dutyGrid.addWidget(self.dutyMin,2,1)
        
        
        dutyGrpBox = QVBoxLayout()
        dutyGrpBox.addStretch()
        dutyGrpBox.addLayout(dutyGrid)
        dutyGrpBox.addStretch()
        dutyGrp = QGroupBox(QApplication.translate("GroupBox","Duty"))
        dutyGrp.setLayout(dutyGrpBox)
        dutyGrp.setContentsMargins(0,15,0,0)
        
        pidBox = QHBoxLayout()
        pidBox.addWidget(pidGrp)
        
        svBox = QHBoxLayout()
        svBox.addWidget(svGrp)
        svBox.addWidget(dutyGrp)
                
        self.startPIDonCHARGE = QCheckBox(QApplication.translate("CheckBox", "Start PID on CHARGE"))
        self.startPIDonCHARGE.setChecked(self.aw.pidcontrol.pidOnCHARGE)

        tab1Layout.addLayout(pidBox)
        tab1Layout.addLayout(svBox)
        tab1Layout.addStretch()
        tab1Layout.addWidget(self.startPIDonCHARGE)

        labelLabel = QLabel(QApplication.translate("Label", "Label"))
        self.labelEdit = QLineEdit() 

        labelRow = QHBoxLayout()
        labelRow.addStretch()
        labelRow.addWidget(labelLabel)
        labelRow.addWidget(self.labelEdit)
        labelRow.addStretch()
        
        # Ramp/Soak tab
        tab2InnerLayout = QHBoxLayout()
        tab2Layout = QVBoxLayout()
        tab2Layout.addSpacing(10)
        tab2Layout.addLayout(labelRow)
        tab2Layout.addSpacing(15)
        tab2Layout.addLayout(tab2InnerLayout)
        rsGrid = QGridLayout()
        self.SVWidgets = []
        self.RampWidgets = []
        self.SoakWidgets = []
        self.ActionWidgets = []
        self.BeepWidgets = []
        self.DescriptionWidgets = []
        rsGrid.addWidget(QLabel(QApplication.translate("Table","SV")),0,1)
        rsGrid.addWidget(QLabel(QApplication.translate("Table","Ramp")),0,2)
        rsGrid.addWidget(QLabel(QApplication.translate("Table","Soak")),0,3)
        rsGrid.addWidget(QLabel(QApplication.translate("Table","Action")),0,4)
        rsGrid.addWidget(QLabel(QApplication.translate("Table","Beep")),0,5)
        rsGrid.addWidget(QLabel(QApplication.translate("Table","Description")),0,6)
        actions = ["",
            QApplication.translate("ComboBox","Pop Up"),
            QApplication.translate("ComboBox","Call Program"),
            QApplication.translate("ComboBox","Event Button"),
            QApplication.translate("ComboBox","Slider") + " " + self.aw.qmc.etypesf(0),
            QApplication.translate("ComboBox","Slider") + " " + self.aw.qmc.etypesf(1),
            QApplication.translate("ComboBox","Slider") + " " + self.aw.qmc.etypesf(2),
            QApplication.translate("ComboBox","Slider") + " " + self.aw.qmc.etypesf(3),
            QApplication.translate("ComboBox","START"),
            QApplication.translate("ComboBox","DRY"),
            QApplication.translate("ComboBox","FCs"),
            QApplication.translate("ComboBox","FCe"),
            QApplication.translate("ComboBox","SCs"),
            QApplication.translate("ComboBox","SCe"),
            QApplication.translate("ComboBox","DROP"),
            QApplication.translate("ComboBox","COOL END"),
            QApplication.translate("ComboBox","OFF"),
            QApplication.translate("ComboBox","CHARGE"),
            QApplication.translate("ComboBox","RampSoak ON"),
            QApplication.translate("ComboBox","RampSoak OFF"),
            QApplication.translate("ComboBox","PID ON"),
            QApplication.translate("ComboBox","PID OFF"),
            QApplication.translate("ComboBox","SV"),
            QApplication.translate("ComboBox","Playback ON"),
            QApplication.translate("ComboBox","Playback OFF"),
            QApplication.translate("ComboBox","Set Canvas Color"),
            QApplication.translate("ComboBox","Reset Canvas Color")]
        for i in range(self.aw.pidcontrol.svLen):
            n = i+1
            svwidget = QSpinBox()
            svwidget.setAlignment(Qt.AlignmentFlag.AlignRight)
            svwidget.setRange(0,999)
            svwidget.setSingleStep(10)
            if self.aw.qmc.mode == "F":
                svwidget.setSuffix(" F")
            elif self.aw.qmc.mode == "C":
                svwidget.setSuffix(" C")
            self.SVWidgets.append(svwidget)
            rampwidget = QTimeEdit()
            rampwidget.setDisplayFormat("mm:ss")
            rampwidget.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.RampWidgets.append(rampwidget)
            soakwidget = QTimeEdit()
            soakwidget.setDisplayFormat("mm:ss")
            soakwidget.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.SoakWidgets.append(soakwidget)
            actionwidget = MyQComboBox()
            actionwidget.addItems(actions)  
            self.ActionWidgets.append(actionwidget)         
            #beep
            beepwidget = QWidget()
            beepCheckBox = QCheckBox()
            beepCheckBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            beepLayout = QHBoxLayout()
            beepLayout.addStretch()
            beepLayout.addWidget(beepCheckBox)
            beepLayout.addSpacing(6)
            beepLayout.addStretch()
            beepLayout.setContentsMargins(0,0,0,0)
            beepLayout.setSpacing(0)
            beepwidget.setLayout(beepLayout) 
            self.BeepWidgets.append(beepwidget) 
            # description
            descriptionwidget = QLineEdit()
            descriptionwidget.setCursorPosition(0) 
            self.DescriptionWidgets.append(descriptionwidget)
            rsGrid.addWidget(QLabel(str(n)),n,0)
            rsGrid.addWidget(svwidget,n,1)
            rsGrid.addWidget(self.RampWidgets[i],n,2)
            rsGrid.addWidget(self.SoakWidgets[i],n,3)
            rsGrid.addWidget(self.ActionWidgets[i],n,4)
            rsGrid.addWidget(self.BeepWidgets[i],n,5)
            rsGrid.addWidget(self.DescriptionWidgets[i],n,6)
        
        ############################
        importButton = QPushButton(QApplication.translate("Button","Load"))
        importButton.setMinimumWidth(80)
        importButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        importButton.clicked.connect(self.importrampsoaks)
        exportButton = QPushButton(QApplication.translate("Button","Save"))
        exportButton.setMinimumWidth(80)
        exportButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        exportButton.clicked.connect(self.exportrampsoaks)
        self.loadRampSoakFromProfile = QCheckBox(QApplication.translate("CheckBox", "Load from profile"))
        self.loadRampSoakFromProfile.setChecked(self.aw.pidcontrol.loadRampSoakFromProfile)
        self.loadRampSoakFromProfile.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.loadRampSoakFromBackground = QCheckBox(QApplication.translate("CheckBox", "Load from background"))
        self.loadRampSoakFromBackground.setChecked(self.aw.pidcontrol.loadRampSoakFromBackground)
        self.loadRampSoakFromBackground.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.rsfile = QLabel(self.aw.qmc.rsfile)
        self.rsfile.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.rsfile.setMinimumWidth(300)
        self.rsfile.setSizePolicy(QSizePolicy.Policy.MinimumExpanding,QSizePolicy.Policy.Preferred)
        
        tab2InnerLayout.addStretch()
        tab2InnerLayout.addLayout(rsGrid)
        tab2InnerLayout.addStretch()

        okButton = QPushButton(QApplication.translate("Button","OK"))
        okButton.clicked.connect(self.okAction)
        onButton = QPushButton(QApplication.translate("Button","On"))
        onButton.clicked.connect(self.pidONAction)
        onButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        offButton = QPushButton(QApplication.translate("Button","Off"))
        offButton.clicked.connect(self.pidOFFAction)
        offButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        okButtonLayout = QHBoxLayout()
        okButtonLayout.addWidget(onButton)
        okButtonLayout.addWidget(offButton)
        okButtonLayout.addStretch()
        okButtonLayout.addWidget(self.rsfile)
        okButtonLayout.addStretch()
        okButtonLayout.addWidget(okButton)        
        okButtonLayout.setContentsMargins(0,0,0,0)
        tab1Layout.setContentsMargins(0,0,0,0) # left, top, right, bottom
        tab1Layout.setSpacing(5)
        tab2Layout.setContentsMargins(10,10,10,10)
        tab2Layout.setSpacing(5)
        self.tabWidget = QTabWidget()
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        self.tabWidget.addTab(C1Widget,QApplication.translate("Tab","PID"))
        C2Widget = QWidget()
        C2Widget.setLayout(tab2Layout)
        self.tabWidget.addTab(C2Widget,QApplication.translate("Tab","Ramp/Soak"))
        self.tabWidget.setContentsMargins(0,0,0,0)
        ############################
        
        # RSn tabs
        self.RSnTab_LabelWidgets = []
        self.RSnTab_SVWidgets = []
        self.RSnTab_RampWidgets = []
        self.RSnTab_SoakWidgets = []
        self.RSnTab_ActionWidgets = []
        self.RSnTab_BeepWidgets = []
        self.RSnTab_DescriptionWidgets = []
        
        self.RSnButtons = []
        
        RSbuttonLayout = QHBoxLayout()
        RSbuttonLayout.addStretch()
        
        for j in range(self.aw.pidcontrol.RSLen):
            # create tab per RSn set
            RSnGrid = QGridLayout()
            RSnGrid.addWidget(QLabel(QApplication.translate("Table","SV")),0,1)
            RSnGrid.addWidget(QLabel(QApplication.translate("Table","Ramp")),0,2)
            RSnGrid.addWidget(QLabel(QApplication.translate("Table","Soak")),0,3)
            RSnGrid.addWidget(QLabel(QApplication.translate("Table","Action")),0,4)
            RSnGrid.addWidget(QLabel(QApplication.translate("Table","Beep")),0,5)
            RSnGrid.addWidget(QLabel(QApplication.translate("Table","Description")),0,6)
            SVWidgets = []
            RampWidgets = []
            SoakWidgets = []
            ActionWidgets = []
            BeepWidgets = []
            DescriptionWidgets = []
            labelLabel = QLabel(QApplication.translate("Label", "Label"))
            labelEdit = QLineEdit() 
            for i in range(self.aw.pidcontrol.svLen):
                n = i+1              
                svwidget = QSpinBox()
                svwidget.setAlignment(Qt.AlignmentFlag.AlignRight)
                svwidget.setRange(0,999)
                svwidget.setSingleStep(10)
                if self.aw.qmc.mode == "F":
                    svwidget.setSuffix(" F")
                elif self.aw.qmc.mode == "C":
                    svwidget.setSuffix(" C")
                SVWidgets.append(svwidget)
                rampwidget = QTimeEdit()
                rampwidget.setDisplayFormat("mm:ss")
                rampwidget.setAlignment(Qt.AlignmentFlag.AlignRight)
                RampWidgets.append(rampwidget)
                soakwidget = QTimeEdit()
                soakwidget.setDisplayFormat("mm:ss")
                soakwidget.setAlignment(Qt.AlignmentFlag.AlignRight)
                SoakWidgets.append(soakwidget)
                actionwidget = MyQComboBox()
                actionwidget.addItems(actions)  
                ActionWidgets.append(actionwidget)         
                #beep
                beepwidget = QWidget()
                beepCheckBox = QCheckBox()
                beepCheckBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                beepLayout = QHBoxLayout()
                beepLayout.addStretch()
                beepLayout.addWidget(beepCheckBox)
                beepLayout.addSpacing(6)
                beepLayout.addStretch()
                beepLayout.setContentsMargins(0,0,0,0)
                beepLayout.setSpacing(0)
                beepwidget.setLayout(beepLayout) 
                BeepWidgets.append(beepwidget) 
                # description
                descwidget = QLineEdit()
                descwidget.setCursorPosition(0) 
                DescriptionWidgets.append(descwidget)
                #
                RSnGrid.addWidget(QLabel(str(n)),n,0)
                RSnGrid.addWidget(svwidget,n,1)
                RSnGrid.addWidget(RampWidgets[i],n,2)
                RSnGrid.addWidget(SoakWidgets[i],n,3)
                RSnGrid.addWidget(ActionWidgets[i],n,4)
                RSnGrid.addWidget(BeepWidgets[i],n,5)
                RSnGrid.addWidget(DescriptionWidgets[i],n,6)
            self.RSnTab_LabelWidgets.append(labelEdit)
            self.RSnTab_SVWidgets.append(SVWidgets)
            self.RSnTab_RampWidgets.append(RampWidgets)
            self.RSnTab_SoakWidgets.append(SoakWidgets)
            self.RSnTab_ActionWidgets.append(ActionWidgets)
            self.RSnTab_BeepWidgets.append(BeepWidgets)
            self.RSnTab_DescriptionWidgets.append(DescriptionWidgets)
            # create tab
            RSnTabLayout = QVBoxLayout()
            RSnLabelLayout = QHBoxLayout()
            RSnLabelLayout.addStretch()
            RSnLabelLayout.addWidget(labelLabel)
            RSnLabelLayout.addWidget(labelEdit)
            RSnLabelLayout.addStretch()
            RSnTabInnerLayout = QHBoxLayout()
            RSnTabInnerLayout.addStretch()
            RSnTabInnerLayout.addLayout(RSnGrid)
            RSnTabInnerLayout.addStretch()
            RSnTabLayout.addSpacing(10)
            RSnTabLayout.addLayout(RSnLabelLayout)
            RSnTabLayout.addSpacing(15)
            RSnTabLayout.addLayout(RSnTabInnerLayout)
            RSnTabLayout.addStretch()
            RSnTabLayout.setContentsMargins(10,10,10,10)
            RSnTabLayout.setSpacing(5)
        
            RSnTabWidget = QWidget()
            RSnTabWidget.setLayout(RSnTabLayout)
            self.tabWidget.addTab(RSnTabWidget,QApplication.translate("Tab","RS")+str(j+1))
            
            setRSnButton = QPushButton(QApplication.translate("Button","RS")+str(j+1))
            setRSnButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            setRSnButton.clicked.connect(self.setRS)
            self.RSnButtons.append(setRSnButton)
            RSbuttonLayout.addWidget(setRSnButton)
        RSbuttonLayout.addStretch()
        
        flagsLayout = QHBoxLayout()
        flagsLayout.addStretch()
        flagsLayout.addWidget(self.loadRampSoakFromProfile)
        flagsLayout.addSpacing(15)
        flagsLayout.addWidget(self.loadRampSoakFromBackground)
        flagsLayout.addStretch()
        
            
            
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(importButton)
        buttonLayout.addWidget(exportButton)
        if self.aw.pidcontrol.RSLen > 0:
            buttonLayout.addSpacing(25)
            buttonLayout.addLayout(RSbuttonLayout)
        buttonLayout.addStretch()
        
        tab2Layout.addLayout(buttonLayout)
        tab2Layout.addStretch()
        tab2Layout.addLayout(flagsLayout)
        
        
        self.tabWidget.setCurrentIndex(activeTab)
        ############################
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addLayout(okButtonLayout)
        mainLayout.setContentsMargins(2,10,2,2)
        self.setLayout(mainLayout)
        okButton.setFocus()
        
        self.setrampsoaks()
        self.setRSs()

        settings = QSettings()
        if settings.contains("PIDPosition"):
            self.move(settings.value("PIDPosition"))
        
        mainLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
    
    @pyqtSlot(int)
    def updatePidMode(self,i):
        self.aw.pidcontrol.svMode = i
        if self.aw.pidcontrol.pidActive and i == 1:
            self.aw.pidcontrol.pidModeInit()
        else:
            self.aw.lcd1.setStyleSheet("QLCDNumber { border-radius: 4; color: %s; background-color: %s;}"%(self.aw.lcdpaletteF["timer"],self.aw.lcdpaletteB["timer"]))
            self.aw.qmc.setTimerLargeLCDcolorSignal.emit(self.aw.lcdpaletteF["timer"],self.aw.lcdpaletteB["timer"])
            if self.aw.qmc.flagon and not self.aw.qmc.flagstart:
                self.aw.qmc.setLCDtime(0)
    
    @pyqtSlot(int)
    def activateSVSlider(self,i):
        self.aw.pidcontrol.activateSVSlider(i)
        
    @pyqtSlot(bool)
    def pidONAction(self,_):
        self.aw.pidcontrol.pidOn()
    
    @pyqtSlot(bool)
    def pidOFFAction(self,_):
        self.aw.pidcontrol.pidOff()
    
    @pyqtSlot(bool)
    def okAction(self,_):
        self.close()
    
    @pyqtSlot(int)
    def activateONOFFeasySVslot(self,i):
        self.aw.pidcontrol.activateONOFFeasySV(bool(i))

    @pyqtSlot(int)
    def sliderMinValueChangedSlot(self,i):
        self.aw.pidcontrol.sliderMinValueChanged(i)
    
    @pyqtSlot(int)
    def sliderMaxValueChangedSlot(self,i):
        self.aw.pidcontrol.sliderMaxValueChanged(i)
    
    @pyqtSlot(bool)
    def importrampsoaks(self,_):
        self.aw.fileImport(QApplication.translate("Message", "Load Ramp/Soak Table"),self.importrampsoaksJSON)
    
    @pyqtSlot(bool)
    def setRS(self,_):
        try:
            n = self.RSnButtons.index(self.sender())
            self.aw.pidcontrol.svLabel = self.getRSnSVLabel(n)
            self.aw.pidcontrol.svValues = self.getRSnSVvalues(n)
            self.aw.pidcontrol.svRamps = self.getRSnSVramps(n)
            self.aw.pidcontrol.svSoaks = self.getRSnSVsoaks(n)
            self.aw.pidcontrol.svActions = self.getRSnSVactions(n)
            self.aw.pidcontrol.svBeeps = self.getRSnSVbeeps(n)
            self.aw.pidcontrol.svDescriptions = self.getRSnSVdescriptions(n)
            self.setrampsoaks()
            self.aw.pidcontrol.rsfile = ""
            self.rsfile.setText(self.aw.pidcontrol.rsfile)
        except Exception: # pylint: disable=broad-except
            pass

    def getRSnSVLabel(self,n):
        return self.RSnTab_LabelWidgets[n].text()
    def getRSnSVvalues(self,n):
        return [w.value() for w in self.RSnTab_SVWidgets[n]]
    def getRSnSVramps(self,n):
        return [self.aw.QTime2time(w.time()) for w in self.RSnTab_RampWidgets[n]]
    def getRSnSVsoaks(self,n):
        return [self.aw.QTime2time(w.time()) for w in self.RSnTab_SoakWidgets[n]]
    def getRSnSVactions(self,n):
        return [int(w.currentIndex()) - 1 for w in self.RSnTab_ActionWidgets[n]]
    def getRSnSVbeeps(self,n):
        return [bool(w.layout().itemAt(1).widget().isChecked()) for w in self.RSnTab_BeepWidgets[n]]
    def getRSnSVdescriptions(self,n):
        return [w.text() for w in self.RSnTab_DescriptionWidgets[n]]

    def setRSnSVLabel(self,n):
        self.RSnTab_LabelWidgets[n].setText(self.aw.pidcontrol.RS_svLabels[n])
    def setRSnSVvalues(self,n):
        for i in range(self.aw.pidcontrol.svLen):
            self.RSnTab_SVWidgets[n][i].setValue(self.aw.pidcontrol.RS_svValues[n][i])
    def setRSnSVramps(self,n):
        for i in range(self.aw.pidcontrol.svLen):
            self.RSnTab_RampWidgets[n][i].setTime(self.aw.time2QTime(self.aw.pidcontrol.RS_svRamps[n][i]))
    def setRSnSVsoaks(self,n):
        for i in range(self.aw.pidcontrol.svLen):
            self.RSnTab_SoakWidgets[n][i].setTime(self.aw.time2QTime(self.aw.pidcontrol.RS_svSoaks[n][i]))
    def setRSnSVactions(self,n):
        for i in range(self.aw.pidcontrol.svLen):
            self.RSnTab_ActionWidgets[n][i].setCurrentIndex(self.aw.pidcontrol.RS_svActions[n][i] + 1)
    def setRSnSVbeeps(self,n):
        for i in range(self.aw.pidcontrol.svLen):
            beep = self.RSnTab_BeepWidgets[n][i].layout().itemAt(1).widget()
            if self.aw.pidcontrol.RS_svBeeps[n][i]:
                beep.setCheckState(Qt.CheckState.Checked)
            else:
                beep.setCheckState(Qt.CheckState.Unchecked)
    def setRSnSVdescriptions(self,n):
        for i in range(self.aw.pidcontrol.svLen):
            self.RSnTab_DescriptionWidgets[n][i].setText(self.aw.pidcontrol.RS_svDescriptions[n][i])
                
    def importrampsoaksJSON(self,filename):
        try:
            self.aw.qmc.rampSoakSemaphore.acquire(1)
            import io
            from json import load as json_load
            with io.open(filename, 'r', encoding='utf-8') as infile:
                rampsoaks = json_load(infile)
            if "svLabel" in rampsoaks:
                self.aw.pidcontrol.svLabel = rampsoaks["svLabel"]
            else:
                self.aw.pidcontrol.svLabel = ""
            self.aw.pidcontrol.svValues = rampsoaks["svValues"]
            self.aw.pidcontrol.svRamps = rampsoaks["svRamps"]
            self.aw.pidcontrol.svSoaks = rampsoaks["svSoaks"]
            self.aw.pidcontrol.svActions = rampsoaks["svActions"]
            self.aw.pidcontrol.svBeeps = rampsoaks["svBeeps"]
            self.aw.pidcontrol.svDescriptions = rampsoaks["svDescriptions"]
            self.setrampsoaks()
            self.aw.qmc.rsfile = filename
            self.rsfile.setText(self.aw.qmc.rsfile)            
        except Exception as ex: # pylint: disable=broad-except
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:") + " importrampsoaksJSON() {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.aw.qmc.rampSoakSemaphore.available() < 1:
                self.aw.qmc.rampSoakSemaphore.release(1)
    
    @pyqtSlot(bool)
    def exportrampsoaks(self,_):
        self.aw.fileExport(QApplication.translate("Message", "Save Ramp/Soak Table"),"*.aprs",self.exportrampsoaksJSON)
        
    def exportrampsoaksJSON(self,filename):
        try:
            self.aw.qmc.rampSoakSemaphore.acquire(1)
            self.saverampsoaks()
            rampsoaks = {}
            rampsoaks["svLabel"] = self.aw.pidcontrol.svLabel
            rampsoaks["svValues"] = self.aw.pidcontrol.svValues
            rampsoaks["svRamps"] = self.aw.pidcontrol.svRamps
            rampsoaks["svSoaks"] = self.aw.pidcontrol.svSoaks
            rampsoaks["svActions"] = self.aw.pidcontrol.svActions
            rampsoaks["svBeeps"] = self.aw.pidcontrol.svBeeps
            rampsoaks["svDescriptions"] = self.aw.pidcontrol.svDescriptions
            rampsoaks["mode"] = self.aw.qmc.mode
            from json import dump as json_dump
            with open(filename, 'w', encoding='utf-8') as outfile:
                json_dump(rampsoaks, outfile, ensure_ascii=True)
                outfile.write('\n')
            self.aw.qmc.rsfile = filename
            self.rsfile.setText(self.aw.qmc.rsfile) 
            return True
        except Exception as ex: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + " exportrampsoaksJSON(): {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
            return False
        finally:
            if self.aw.qmc.rampSoakSemaphore.available() < 1:
                self.aw.qmc.rampSoakSemaphore.release(1)
            
    def saverampsoaks(self):
        try:
            self.aw.qmc.rampSoakSemaphore.acquire(1)
            self.aw.pidcontrol.svLabel = self.labelEdit.text()
            for i in range(self.aw.pidcontrol.svLen):
                self.aw.pidcontrol.svValues[i] = self.SVWidgets[i].value()
                self.aw.pidcontrol.svRamps[i] = self.aw.QTime2time(self.RampWidgets[i].time())
                self.aw.pidcontrol.svSoaks[i] = self.aw.QTime2time(self.SoakWidgets[i].time())            
                self.aw.pidcontrol.svActions[i] = int(self.ActionWidgets[i].currentIndex()) - 1 
                beep = self.BeepWidgets[i].layout().itemAt(1).widget()           
                self.aw.pidcontrol.svBeeps[i] = bool(beep.isChecked())
                self.aw.pidcontrol.svDescriptions[i] = self.DescriptionWidgets[i].text()
        finally:
            if self.aw.qmc.rampSoakSemaphore.available() < 1:
                self.aw.qmc.rampSoakSemaphore.release(1)
            
    def setrampsoaks(self):
        try:
            self.aw.qmc.rampSoakSemaphore.acquire(1)
            self.labelEdit.setText(self.aw.pidcontrol.svLabel)
            for i in range(self.aw.pidcontrol.svLen):
                self.SVWidgets[i].setValue(self.aw.pidcontrol.svValues[i])
                self.RampWidgets[i].setTime(self.aw.time2QTime(self.aw.pidcontrol.svRamps[i]))
                self.SoakWidgets[i].setTime(self.aw.time2QTime(self.aw.pidcontrol.svSoaks[i]))
                self.ActionWidgets[i].setCurrentIndex(self.aw.pidcontrol.svActions[i] + 1)
                beep = self.BeepWidgets[i].layout().itemAt(1).widget() 
                if self.aw.pidcontrol.svBeeps[i]:
                    beep.setCheckState(Qt.CheckState.Checked)
                else:
                    beep.setCheckState(Qt.CheckState.Unchecked)
                self.DescriptionWidgets[i].setText(self.aw.pidcontrol.svDescriptions[i])
        finally:
            if self.aw.qmc.rampSoakSemaphore.available() < 1:
                self.aw.qmc.rampSoakSemaphore.release(1)

    def saveRSs(self):
        try:
            self.aw.qmc.rampSoakSemaphore.acquire(1)
            self.aw.pidcontrol.RS_svLabels = []
            self.aw.pidcontrol.RS_svValues = []
            self.aw.pidcontrol.RS_svRamps = []
            self.aw.pidcontrol.RS_svSoaks = []
            self.aw.pidcontrol.RS_svActions = []
            self.aw.pidcontrol.RS_svBeeps = []
            self.aw.pidcontrol.RS_svDescriptions = []
            for n in range(self.aw.pidcontrol.RSLen):
                self.aw.pidcontrol.RS_svLabels.append(self.getRSnSVLabel(n))
                self.aw.pidcontrol.RS_svValues.append(self.getRSnSVvalues(n))
                self.aw.pidcontrol.RS_svRamps.append(self.getRSnSVramps(n))
                self.aw.pidcontrol.RS_svSoaks.append(self.getRSnSVsoaks(n))
                self.aw.pidcontrol.RS_svActions.append(self.getRSnSVactions(n))
                self.aw.pidcontrol.RS_svBeeps.append(self.getRSnSVbeeps(n))
                self.aw.pidcontrol.RS_svDescriptions.append(self.getRSnSVdescriptions(n))
        finally:
            if self.aw.qmc.rampSoakSemaphore.available() < 1:
                self.aw.qmc.rampSoakSemaphore.release(1)

    def setRSs(self):
        for n in range(self.aw.pidcontrol.RSLen):
            self.setRSnSVLabel(n)
            self.setRSnSVvalues(n)
            self.setRSnSVramps(n)
            self.setRSnSVsoaks(n)
            self.setRSnSVactions(n)
            self.setRSnSVbeeps(n)
            self.setRSnSVdescriptions(n)

    @pyqtSlot(bool)
    def pidConf(self,_):
        kp = self.pidKp.value() # 5.00
        ki = self.pidKi.value() # 0.15
        kd = self.pidKd.value() # 0.00
        source = self.pidSource.currentIndex() + 1 # 1-4, def 1
        cycle = self.pidCycle.value() # def 1000 in ms
        pOnE = bool(self.pOnE.isChecked())
        self.aw.pidcontrol.confPID(kp,ki,kd,source,cycle,pOnE)
        if not (self.aw.qmc.device == 19 and self.aw.qmc.PIDbuttonflag): # don't show Targets if TC4 firmware PID is in use
            self.aw.pidcontrol.pidPositiveTarget = self.positiveControlCombo.currentIndex()
            self.aw.pidcontrol.pidNegativeTarget = self.negativeControlCombo.currentIndex()
            self.aw.pidcontrol.invertControl = self.invertControlFlag.isChecked()
    
    @pyqtSlot(bool)
    def setSV(self,_): # and DutySteps
        self.aw.pidcontrol.setSV(self.pidSV.value())
        self.aw.pidcontrol.setDutySteps(self.pidDutySteps.value())
        
    def close(self):
        kp = self.pidKp.value() # 5.00
        ki = self.pidKi.value() # 0.15
        kd = self.pidKd.value() # 0.00
        
        source = self.pidSource.currentIndex() + 1 # 1-4, def 1
        if not (self.aw.qmc.device == 19 and self.aw.qmc.PIDbuttonflag): # don't show Targets if TC4 firmware PID is in use
            self.aw.pidcontrol.pidPositiveTarget = self.positiveControlCombo.currentIndex()
            self.aw.pidcontrol.pidNegativeTarget = self.negativeControlCombo.currentIndex()
            self.aw.pidcontrol.invertControl = self.invertControlFlag.isChecked()
        cycle = self.pidCycle.value() # def 1000 in ms
        pOnE = bool(self.pOnE.isChecked())
        self.aw.pidcontrol.setPID(kp,ki,kd,source,cycle,pOnE)
        #
        self.aw.pidcontrol.pidOnCHARGE = self.startPIDonCHARGE.isChecked()
        self.aw.pidcontrol.loadRampSoakFromProfile = self.loadRampSoakFromProfile.isChecked()
        self.aw.pidcontrol.loadRampSoakFromBackground = self.loadRampSoakFromBackground.isChecked()
        self.aw.pidcontrol.svSliderMin = min(self.pidSVSliderMin.value(),self.pidSVSliderMax.value())
        self.aw.pidcontrol.svSliderMax = max(self.pidSVSliderMin.value(),self.pidSVSliderMax.value())
        self.aw.pidcontrol.svValue = self.pidSV.value()
        self.aw.pidcontrol.svSlider = self.pidSVsliderFlag.isChecked()
        self.aw.pidcontrol.activateSVSlider(self.aw.pidcontrol.svSlider)
        self.aw.pidcontrol.svButtons = self.pidSVbuttonsFlag.isChecked()
        self.aw.pidcontrol.activateONOFFeasySV(self.aw.pidcontrol.svButtons)
        self.aw.pidcontrol.svMode = self.pidMode.currentIndex()
        self.aw.pidcontrol.dutyMin = min(self.dutyMin.value(),self.dutyMax.value())
        self.aw.pidcontrol.dutyMax = max(self.dutyMin.value(),self.dutyMax.value())
        self.aw.pidcontrol.svLookahead = self.pidSVLookahead.value()
        self.aw.pidcontrol.dutySteps = self.pidDutySteps.value()
        #
        self.aw.PID_DlgControl_activeTab = self.tabWidget.currentIndex()
        #
        self.saverampsoaks()
        self.saveRSs()
        #
        self.closeEvent(None)

    def closeEvent(self,_):
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue("PIDPosition",self.frameGeometry().topLeft())
        self.accept()

############################################################################
######################## FUJI PX PID CONTROL DIALOG ########################
############################################################################

# common code for all Fuji PXxx subclasses
class PXpidDlgControl(ArtisanDialog):

    @pyqtSlot(bool)
    def setpointET(self,_):
        self.setpoint("ET")
    
    @pyqtSlot(bool)
    def setpointBT(self,_):
        self.setpoint("BT")
    
    def setpoint(self,PID):
        if PID == "ET":
            slaveID = self.aw.ser.controlETpid[1]
            if self.aw.ser.controlETpid[0] == 0:
                reg_dict = self.aw.fujipid.PXG4
            elif self.aw.ser.controlETpid[0] == 1:
                reg_dict = self.aw.fujipid.PXR
            else:
                reg_dict = self.aw.fujipid.PXF
        else: # "BT"
            slaveID = self.aw.ser.readBTpid[1]
            if self.aw.ser.readBTpid[0] == 0:
                reg_dict = self.aw.fujipid.PXG4
            elif self.aw.ser.readBTpid[0] == 1:
                reg_dict = self.aw.fujipid.PXR
            else:
                reg_dict = self.aw.fujipid.PXF
        command = ""
        reg = None
        try:
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(reg_dict["decimalposition"][1],6)
                if reg:
                    self.aw.modbus.writeSingleRegister(slaveID,reg,1)
                r = command
            else:
                command = self.aw.fujipid.message2send(slaveID,6,reg_dict["decimalposition"][1],1)
                r = self.aw.ser.sendFUJIcommand(command,8)
            #check response from pid and update message on main window
            if r == command:
                message = QApplication.translate("StatusBar","Decimal position successfully set to 1")
                self.status.showMessage(message, 5000)
            else:
                self.status.showMessage(QApplication.translate("StatusBar","Problem setting decimal position"),5000)
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + " setpoint(): {0}").format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def setthermocoupletypeET(self,_):
        self.setthermocoupletype("ET")

    @pyqtSlot(bool)
    def setthermocoupletypeBT(self,_):
        self.setthermocoupletype("BT")

    def setthermocoupletype(self,PID):
        if PID == "ET":
            slaveID = self.aw.ser.controlETpid[1]
            index = self.ETthermocombobox.currentIndex()
            if self.aw.ser.controlETpid[0] == 0:
                reg_dict = self.aw.fujipid.PXG4
                conversiontoindex = self.aw.fujipid.PXGconversiontoindex
            elif self.aw.ser.controlETpid[0] == 1:
                reg_dict = self.aw.fujipid.PXR
                conversiontoindex = self.aw.fujipid.PXRconversiontoindex
            else:
                reg_dict = self.aw.fujipid.PXF
                conversiontoindex = self.aw.fujipid.PXFconversiontoindex
        else: # "BT"
            slaveID = self.aw.ser.readBTpid[1]
            index = self.BTthermocombobox.currentIndex()
            if self.aw.ser.readBTpid[0] == 0:
                reg_dict = self.aw.fujipid.PXG4
                conversiontoindex = self.aw.fujipid.PXGconversiontoindex
            elif self.aw.ser.readBTpid[0] == 1:
                reg_dict = self.aw.fujipid.PXR
                conversiontoindex = self.aw.fujipid.PXRconversiontoindex
            else:
                reg_dict = self.aw.fujipid.PXF
                conversiontoindex = self.aw.fujipid.PXFconversiontoindex
        command = ""
        reg = None
        try:
            if self.aw.ser.useModbusPort:
                value = conversiontoindex[index]
                reg = self.aw.modbus.address2register(reg_dict["pvinputtype"][1],6)
                if reg:
                    self.aw.modbus.writeSingleRegister(slaveID,reg,value)
                r = command
            else:
                value = conversiontoindex[index]
                command = self.aw.fujipid.message2send(slaveID,6,reg_dict["pvinputtype"][1],value)
                r = self.aw.ser.sendFUJIcommand(command,8)
            #check response from pid and update message on main window
            if r == command:
                reg_dict["pvinputtype"][0] = conversiontoindex[index]
                message = QApplication.translate("StatusBar","Thermocouple type successfully set")
                self.status.showMessage(message, 5000)
            else:
                self.status.showMessage(QApplication.translate("StatusBar","Problem setting thermocouple type"),5000)
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + " setthermocoupletype(): {0}").format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def readthermocoupletypeET(self,_):
        self.readthermocoupletype("ET")

    @pyqtSlot(bool)
    def readthermocoupletypeBT(self,_):
        self.readthermocoupletype("BT")
    
    def readthermocoupletype(self,PID):
        if PID == "ET":
            unitID = self.aw.ser.controlETpid[1]
            if self.aw.ser.controlETpid[0] == 0:
                reg_dict = self.aw.fujipid.PXG4
                conversiontoindex = self.aw.fujipid.PXGconversiontoindex
                thermotypes = self.aw.fujipid.PXGthermotypes
            elif self.aw.ser.controlETpid[0] == 1:
                reg_dict = self.aw.fujipid.PXR
                conversiontoindex = self.aw.fujipid.PXRconversiontoindex
                thermotypes = self.aw.fujipid.PXRthermotypes
            else:
                reg_dict = self.aw.fujipid.PXF
                conversiontoindex = self.aw.fujipid.PXFconversiontoindex
                thermotypes = self.aw.fujipid.PXFthermotypes
        else: # "BT"
            unitID = self.aw.ser.readBTpid[1]
            if self.aw.ser.readBTpid[0] == 0:
                reg_dict = self.aw.fujipid.PXG4
                conversiontoindex = self.aw.fujipid.PXGconversiontoindex
                thermotypes = self.aw.fujipid.PXGthermotypes
            elif self.aw.ser.readBTpid[0] == 1:
                reg_dict = self.aw.fujipid.PXR
                conversiontoindex = self.aw.fujipid.PXRconversiontoindex
                thermotypes = self.aw.fujipid.PXRthermotypes
            else:
                reg_dict = self.aw.fujipid.PXF
                conversiontoindex = self.aw.fujipid.PXFconversiontoindex
                thermotypes = self.aw.fujipid.PXFthermotypes
        command = ""
        message = "empty"
        reg = None
        Thtype = None
        try:
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(reg_dict["pvinputtype"][1],3)
                if reg:
                    Thtype = self.aw.modbus.readSingleRegister(unitID,reg,3)
            else:
                command = self.aw.fujipid.message2send(unitID,3,reg_dict["pvinputtype"][1],1)
                if command:
                    Thtype = self.aw.fujipid.readoneword(command)
            if Thtype is not None:
                if PID == "ET":
                    if Thtype in conversiontoindex:
                        reg_dict["pvinputtype"][0] = Thtype
                        self.ETthermocombobox.setCurrentIndex(conversiontoindex.index(Thtype))
                        message = "ET type %i: %s"%(Thtype,thermotypes[conversiontoindex.index(Thtype)])
                    else:
                        message = "ERR"
                elif PID == "BT":
                    if Thtype in conversiontoindex:
                        reg_dict["pvinputtype"][0] = Thtype
                        message = "BT type %i: %s"%(Thtype,thermotypes[conversiontoindex.index(Thtype)])
                        self.BTthermocombobox.setCurrentIndex(conversiontoindex.index(Thtype))
                self.status.showMessage(message,5000)
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:") + " readthermocoupletype(): {0}").format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))



#########################################################################
######################## FUJI PXR CONTROL DIALOG  #######################
#########################################################################

class PXRpidDlgControl(PXpidDlgControl):
    def __init__(self, parent = None, aw = None):
        super().__init__(parent,aw)
        self.setModal(True)
        #self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose) # default is True and this is set already in ArtisanDialog by default
        self.setWindowTitle(QApplication.translate("Form Caption","Fuji PXR PID Control"))
        #create Ramp Soak control button colums
        self.labelrs1 = QLabel()
        self.labelrs1.setContentsMargins(5,5,5,5)
        self.labelrs1.setStyleSheet("background-color:'#CCCCCC';")
        self.labelrs1.setText("<font color='white'><b>" + QApplication.translate("Label", "Ramp Soak HH:MM<BR>(1-4)") + "</b></font>")
        self.labelrs2 = QLabel()
        self.labelrs2.setContentsMargins(5,5,5,5)
        self.labelrs2.setStyleSheet("background-color:'#CCCCCC';")
        self.labelrs2.setText("<font color='white'><b>" + QApplication.translate("Label", "Ramp Soak HH:MM<BR>(5-8)") + "</b></font>")
        labelpattern = QLabel(QApplication.translate("Label", "Ramp/Soak Pattern"))
        self.patternComboBox =  QComboBox()
        self.patternComboBox.addItems(["1-4","5-8","1-8"])
        self.patternComboBox.setCurrentIndex(self.aw.fujipid.PXR["rampsoakpattern"][0])
        self.status = QStatusBar()
        self.status.setSizeGripEnabled(False)
        self.status.showMessage(QApplication.translate("StatusBar","Ready"),5000)
        self.label_rs1 =  QLabel()
        self.label_rs2 =  QLabel()
        self.label_rs3 =  QLabel()
        self.label_rs4 =  QLabel()
        self.label_rs5 =  QLabel()
        self.label_rs6 =  QLabel()
        self.label_rs7 =  QLabel()
        self.label_rs8 =  QLabel()
        self.paintlabels()
        #update button and exit button
        button_getall = QPushButton(QApplication.translate("Button","Read Ra/So values"))
        button_getall.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_rson =  QPushButton(QApplication.translate("Button","RampSoak ON"))
        button_rson.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_rsoff =  QPushButton(QApplication.translate("Button","RampSoak OFF"))
        button_rsoff.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_standbyON = QPushButton(QApplication.translate("Button","PID OFF"))
        button_standbyON.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_standbyOFF = QPushButton(QApplication.translate("Button","PID ON"))
        button_standbyOFF.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        button_exit = QPushButton(QApplication.translate("Button","OK"))
        button_exit.setFocus()

        self.patternComboBox.currentIndexChanged.connect(self.paintlabels)
        button_getall.clicked.connect(self.getallsegments)
        button_rson.clicked.connect(self.setONrampsoak)
        button_rsoff.clicked.connect(self.setOFFrampsoak)
        button_standbyON.clicked.connect(self.setONstandby)
        button_standbyOFF.clicked.connect(self.setOFFstandby)
        button_exit.clicked.connect(self.reject)
        #TAB 2
        tab2svbutton = QPushButton(QApplication.translate("Button","Write SV"))
        tab2svbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.tab2easySVbuttonsFlag = QCheckBox(QApplication.translate("Label","SV Buttons"))
        self.tab2easySVbuttonsFlag.setChecked(self.aw.pidcontrol.svButtons)
        self.tab2easySVbuttonsFlag.stateChanged.connect(self.setSVbuttons)
        self.tab2easySVsliderFlag = QCheckBox(QApplication.translate("Label","SV Slider"))
        self.tab2easySVsliderFlag.setChecked(self.aw.pidcontrol.svSlider)
        self.tab2easySVsliderFlag.stateChanged.connect(self.setSVsliderSlot)
        
        
        tab2getsvbutton = QPushButton(QApplication.translate("Button","Read SV"))
        tab2getsvbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.readsvedit = QLineEdit()
        tab2svbutton.clicked.connect(self.setsv)
        tab2getsvbutton.clicked.connect(self.getsv)
        svwarning1 = QLabel("<CENTER><b>" + QApplication.translate("Label", "WARNING") + "</b><br>"
                            + QApplication.translate("Label", "Writing eeprom memory") + "<br>"
                            + QApplication.translate("Label", "<u>Max life</u> 10,000 writes") + "<br>"
                            + QApplication.translate("Label", "Infinite read life.") + "</CENTER>")
        svwarning2 = QLabel("<CENTER><b>" + QApplication.translate("Label", "WARNING") + "</b><br>"
                            + QApplication.translate("Label", "After <u>writing</u> an adjustment,<br>never power down the pid<br>for the next 5 seconds <br>or the pid may never recover.") + "<br>"
                            + QApplication.translate("Label", "Read operations manual") + "</CENTER>")
        self.svedit = QLineEdit()
        self.svedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.svedit))
        #TAB 3
        button_p = QPushButton(QApplication.translate("Button","Set p"))
        button_p.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_i = QPushButton(QApplication.translate("Button","Set i"))
        button_i.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_d = QPushButton(QApplication.translate("Button","Set d"))
        button_d.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        plabel =  QLabel("p")
        ilabel =  QLabel("i")
        dlabel =  QLabel("d")
        self.pedit = QLineEdit(str(self.aw.fujipid.PXR["p"][0]))
        self.iedit = QLineEdit(str(self.aw.fujipid.PXR["i"][0]))
        self.dedit = QLineEdit(str(self.aw.fujipid.PXR["d"][0]))
        self.pedit.setMaximumWidth(60)
        self.iedit.setMaximumWidth(60)
        self.dedit.setMaximumWidth(60)
        self.pedit.setValidator(QIntValidator(0., 999, self.pedit))
        self.iedit.setValidator(QIntValidator(0, 3200, self.iedit))
        self.dedit.setValidator(QIntValidator(0., 999, self.dedit))
        button_autotuneON = QPushButton(QApplication.translate("Button","Autotune ON"))
        button_autotuneON.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_autotuneOFF = QPushButton(QApplication.translate("Button","Autotune OFF"))
        button_autotuneOFF.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_readpid = QPushButton(QApplication.translate("Button","Read PID Values"))
        button_readpid.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_autotuneON.clicked.connect(self.setONautotune)
        button_autotuneOFF.clicked.connect(self.setOFFautotune)
        button_p.clicked.connect(self.setpid_p)
        button_i.clicked.connect(self.setpid_i)
        button_d.clicked.connect(self.setpid_d)
        button_readpid.clicked.connect(self.getpid)
        #TAB4
        #table for setting segments
        self.segmenttable = QTableWidget()
        self.createsegmenttable()
        #****************************   TAB5 WIDGETS
        BTthermolabelnote = QLabel(QApplication.translate("Label","NOTE: BT Thermocouple type is not stored in the Artisan settings"))
        self.ETthermocombobox = QComboBox()
        self.BTthermocombobox = QComboBox()
        #self.BTthermocombobox.setStyleSheet("background-color:'lightgrey';")
        self.ETthermocombobox.addItems(self.aw.fujipid.PXRthermotypes)
        if self.aw.ser.readBTpid[0] == 0:        #fuji PXG
            self.BTthermocombobox.addItems(self.aw.fujipid.PXGthermotypes)
        elif self.aw.ser.readBTpid[0] == 1:      #fuji PXR
            self.BTthermocombobox.addItems(self.aw.fujipid.PXRthermotypes)
        else: # fuji PXF
            self.BTthermocombobox.addItems(self.aw.fujipid.PXFthermotypes)
        if self.aw.fujipid.PXR["pvinputtype"][0] in self.aw.fujipid.PXRconversiontoindex:
            self.ETthermocombobox.setCurrentIndex(self.aw.fujipid.PXRconversiontoindex.index(self.aw.fujipid.PXR["pvinputtype"][0]))
        setETthermocouplebutton = QPushButton(QApplication.translate("Button","Set"))
        setETthermocouplebutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        setBTthermocouplebutton = QPushButton(QApplication.translate("Button","Set"))
        setBTthermocouplebutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        getETthermocouplebutton = QPushButton(QApplication.translate("Button","Read"))
        getETthermocouplebutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        getBTthermocouplebutton = QPushButton(QApplication.translate("Button","Read"))
        getBTthermocouplebutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        setETthermocouplebutton.setMaximumWidth(80)
        getETthermocouplebutton.setMaximumWidth(80)
        setBTthermocouplebutton.setMaximumWidth(80)
        getBTthermocouplebutton.setMaximumWidth(80)
        setETthermocouplebutton.clicked.connect(self.setthermocoupletypeET)
        setBTthermocouplebutton.clicked.connect(self.setthermocoupletypeBT)
        getETthermocouplebutton.clicked.connect(self.readthermocoupletypeET)
        getBTthermocouplebutton.clicked.connect(self.readthermocoupletypeBT)
        PointButtonET = QPushButton(QApplication.translate("Button","Set ET PID to 1 decimal point"))
        PointButtonET.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        PointButtonBT = QPushButton(QApplication.translate("Button","Set BT PID to 1 decimal point"))
        PointButtonBT.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        PointButtonET.setMaximumWidth(250)
        PointButtonBT.setMaximumWidth(250)
        pointlabel = QLabel(QApplication.translate("Label","Artisan uses 1 decimal point"))
        PointButtonET.clicked.connect(self.setpointET)
        PointButtonBT.clicked.connect(self.setpointBT)
        
                
        # Follow Background 
        self.followBackground = QCheckBox(QApplication.translate("CheckBox", "Follow Background"))
        self.followBackground.setChecked(self.aw.fujipid.followBackground)
        self.followBackground.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.followBackground.stateChanged.connect(self.changeFollowBackground)         #toggle
        # Follow Background Lookahead
        self.pidSVLookahead = QSpinBox()
        self.pidSVLookahead.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pidSVLookahead.setRange(0,999)
        self.pidSVLookahead.setSingleStep(1)
        self.pidSVLookahead.setValue(self.aw.fujipid.lookahead)  
        self.pidSVLookahead.setSuffix(" s")
        self.pidSVLookahead.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pidSVLookahead.valueChanged.connect(self.changeLookAhead)
        pidSVLookaheadLabel = QLabel(QApplication.translate("Label","Lookahead"))
        followLayout = QHBoxLayout()
        followLayout.addStretch()
        followLayout.addWidget(pidSVLookaheadLabel)
        followLayout.addWidget(self.pidSVLookahead)
        followLayout.addStretch() 
        
        
        #create layouts
        buttonMasterLayout = QGridLayout()
        buttonRampSoakLayout1 = QVBoxLayout()
        buttonRampSoakLayout2 = QVBoxLayout()
        tab3layout = QGridLayout()
        svlayout = QGridLayout()
        #place rs buttoms in RampSoakLayout1
        buttonRampSoakLayout1.addWidget(self.labelrs1,0)
        buttonRampSoakLayout1.addWidget(self.label_rs1,1)
        buttonRampSoakLayout1.addWidget(self.label_rs2,2)
        buttonRampSoakLayout1.addWidget(self.label_rs3,3)
        buttonRampSoakLayout1.addWidget(self.label_rs4,4)
        buttonRampSoakLayout2.addWidget(self.labelrs2,0)
        buttonRampSoakLayout2.addWidget(self.label_rs5,1)
        buttonRampSoakLayout2.addWidget(self.label_rs6,2)
        buttonRampSoakLayout2.addWidget(self.label_rs7,3)
        buttonRampSoakLayout2.addWidget(self.label_rs8,4)
        buttonMasterLayout.addLayout(buttonRampSoakLayout1,0,0)
        buttonMasterLayout.addLayout(buttonRampSoakLayout2,0,1)
        buttonMasterLayout.addWidget(labelpattern,1,0)
        buttonMasterLayout.addWidget(self.patternComboBox,1,1)
        buttonMasterLayout.addWidget(button_rson,2,0)
        buttonMasterLayout.addWidget(button_rsoff,2,1)
        buttonMasterLayout.addWidget(button_autotuneOFF,3,1)
        buttonMasterLayout.addWidget(button_autotuneON,3,0)
        buttonMasterLayout.addWidget(button_standbyOFF,4,0)
        buttonMasterLayout.addWidget(button_standbyON,4,1)
        buttonMasterLayout.addWidget(self.followBackground,5,0)
        buttonMasterLayout.addLayout(followLayout,5,1)
        buttonMasterLayout.addWidget(button_getall,6,0)

        ############################
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addStretch()
        buttonLayout.addWidget(button_exit)
        
                
        #tab 2
        svlayout.addWidget(svwarning2,0,0)
        svlayout.addWidget(svwarning1,0,1)
        svlayout.addWidget(self.readsvedit,1,0)
        svlayout.addWidget(tab2getsvbutton,1,1)
        svlayout.addWidget(self.svedit,2,0)
        svlayout.addWidget(tab2svbutton,2,1)
        svlayout.addWidget(self.tab2easySVbuttonsFlag,3,0)
        svlayout.addWidget(self.tab2easySVsliderFlag,3,1)
        #tab 3
        tab3layout.addWidget(plabel,0,0)
        tab3layout.addWidget(self.pedit,0,1)
        tab3layout.addWidget(button_p,0,2)
        tab3layout.addWidget(ilabel,1,0)
        tab3layout.addWidget(self.iedit,1,1)
        tab3layout.addWidget(button_i,1,2)
        tab3layout.addWidget(dlabel,2,0)
        tab3layout.addWidget(self.dedit,2,1)
        tab3layout.addWidget(button_d,2,2)
        tab3layout.addWidget(button_autotuneON,3,1)
        tab3layout.addWidget(button_autotuneOFF,3,2)
        tab3layout.addWidget(button_readpid,4,1)
        #tab4
        tab4layout = QVBoxLayout()
        tab4layout.addWidget(self.segmenttable)
        
        #tab5
        thermolayoutET = QHBoxLayout()
        thermolayoutET.addWidget(self.ETthermocombobox)
        thermolayoutET.addStretch()
        thermolayoutET.addWidget(getETthermocouplebutton)
        thermolayoutET.addWidget(setETthermocouplebutton)
        ETGroupBox = QGroupBox(QApplication.translate("Label","ET Thermocouple type"))
        ETGroupBox.setLayout(thermolayoutET)
        thermolayoutBT = QHBoxLayout()
        thermolayoutBT.addWidget(self.BTthermocombobox)
        thermolayoutBT.addStretch()
        thermolayoutBT.addWidget(getBTthermocouplebutton)
        thermolayoutBT.addWidget(setBTthermocouplebutton)
        BTGroupBox = QGroupBox(QApplication.translate("Label","BT Thermocouple type"))
        BTGroupBox.setLayout(thermolayoutBT)
        tab5Layout = QVBoxLayout()
        tab5Layout.addWidget(ETGroupBox)
        tab5Layout.addWidget(BTGroupBox)
        tab5Layout.addWidget(BTthermolabelnote)
        tab5Layout.addStretch()
        tab5Layout.addWidget(pointlabel)
        tab5Layout.addWidget(PointButtonET)
        tab5Layout.addWidget(PointButtonBT)
        tab5Layout.addStretch()
        ###################################
        TabWidget = QTabWidget()
        C1Widget = QWidget()
        C1Widget.setLayout(buttonMasterLayout)
        TabWidget.addTab(C1Widget,QApplication.translate("Tab","RS"))
        C2Widget = QWidget()
        C2Widget.setLayout(svlayout)
        TabWidget.addTab(C2Widget,QApplication.translate("Tab","SV"))
        tab3Hlayout = QHBoxLayout()
        tab3Hlayout.addStretch()
        tab3Hlayout.addLayout(tab3layout)
        tab3Hlayout.addStretch()
        tab3Vlayout = QVBoxLayout()
        tab3Vlayout.addStretch()
        tab3Vlayout.addLayout(tab3Hlayout)
        tab3Vlayout.addStretch()
        C3Widget = QWidget()        
        C3Widget.setLayout(tab3Vlayout)
        TabWidget.addTab(C3Widget,QApplication.translate("Tab","PID"))
        C4Widget = QWidget()
        C4Widget.setLayout(tab4layout)
        TabWidget.addTab(C4Widget,QApplication.translate("Tab","Set RS"))
        C5Widget = QWidget()
        C5Widget.setLayout(tab5Layout)
        TabWidget.addTab(C5Widget,QApplication.translate("Tab","Extra"))
        #incorporate layouts
        Mlayout = QVBoxLayout()
        Mlayout.addWidget(self.status,0)
        Mlayout.addWidget(TabWidget,1)
        Mlayout.addLayout(buttonLayout,2)
        self.setLayout(Mlayout)
    
    @pyqtSlot(int)
    def setSVbuttons(self,flag):
        self.aw.pidcontrol.svButtons = bool(flag)
    
    @pyqtSlot(int)
    def setSVsliderSlot(self,flag):
        self.setSVslider(flag)
        self.aw.pidcontrol.activateSVSlider(flag)

    def setSVslider(self,flag):
        self.aw.pidcontrol.svSlider = bool(flag)

    @pyqtSlot(int)
    def changeLookAhead(self,_):
        self.aw.fujipid.lookahead = int(self.pidSVLookahead.value())
    
    @pyqtSlot(int)
    def changeFollowBackground(self,_):
        self.aw.fujipid.followBackground = not self.aw.fujipid.followBackground

    @pyqtSlot(int)
    def paintlabels(self,_=0):
        str1 = "T = " + str(self.aw.fujipid.PXR["segment1sv"][0]) + ", Ramp = " + stringfromseconds(self.aw.fujipid.PXR["segment1ramp"][0]) + ", Soak = " + stringfromseconds(self.aw.fujipid.PXR["segment1soak"][0])
        str2 = "T = " + str(self.aw.fujipid.PXR["segment2sv"][0]) + ", Ramp = " + stringfromseconds(self.aw.fujipid.PXR["segment2ramp"][0]) + ", Soak = " + stringfromseconds(self.aw.fujipid.PXR["segment2soak"][0])
        str3 = "T = " + str(self.aw.fujipid.PXR["segment3sv"][0]) + ", Ramp = " + stringfromseconds(self.aw.fujipid.PXR["segment3ramp"][0]) + ", Soak = " + stringfromseconds(self.aw.fujipid.PXR["segment3soak"][0])
        str4 = "T = " + str(self.aw.fujipid.PXR["segment4sv"][0]) + ", Ramp = " + stringfromseconds(self.aw.fujipid.PXR["segment4ramp"][0]) + ", Soak = " + stringfromseconds(self.aw.fujipid.PXR["segment4soak"][0])
        str5 = "T = " + str(self.aw.fujipid.PXR["segment5sv"][0]) + ", Ramp = " + stringfromseconds(self.aw.fujipid.PXR["segment5ramp"][0]) + ", Soak = " + stringfromseconds(self.aw.fujipid.PXR["segment5soak"][0])
        str6 = "T = " + str(self.aw.fujipid.PXR["segment6sv"][0]) + ", Ramp = " + stringfromseconds(self.aw.fujipid.PXR["segment6ramp"][0]) + ", Soak = " + stringfromseconds(self.aw.fujipid.PXR["segment6soak"][0])
        str7 = "T = " + str(self.aw.fujipid.PXR["segment7sv"][0]) + ", Ramp = " + stringfromseconds(self.aw.fujipid.PXR["segment7ramp"][0]) + ", Soak = " + stringfromseconds(self.aw.fujipid.PXR["segment7soak"][0])
        str8 = "T = " + str(self.aw.fujipid.PXR["segment8sv"][0]) + ", Ramp = " + stringfromseconds(self.aw.fujipid.PXR["segment8ramp"][0]) + ", Soak = " + stringfromseconds(self.aw.fujipid.PXR["segment8soak"][0])
        self.label_rs1.setText(str1)
        self.label_rs2.setText(str2)
        self.label_rs3.setText(str3)
        self.label_rs4.setText(str4)
        self.label_rs5.setText(str5)
        self.label_rs6.setText(str6)
        self.label_rs7.setText(str7)
        self.label_rs8.setText(str8)
        pattern = [[1,1,1,1,0,0,0,0],
                  [0,0,0,0,1,1,1,1],
                  [1,1,1,1,1,1,1,1]]
        self.aw.fujipid.PXR["rampsoakpattern"][0] = self.patternComboBox.currentIndex()
        if pattern[self.aw.fujipid.PXR["rampsoakpattern"][0]][0]:   
            self.label_rs1.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs1.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXR["rampsoakpattern"][0]][1]:
            self.label_rs2.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs2.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXR["rampsoakpattern"][0]][2]:   
            self.label_rs3.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs3.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXR["rampsoakpattern"][0]][3]:   
            self.label_rs4.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs4.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXR["rampsoakpattern"][0]][4]:   
            self.label_rs5.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs5.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXR["rampsoakpattern"][0]][5]:   
            self.label_rs6.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs6.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXR["rampsoakpattern"][0]][6]:   
            self.label_rs7.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs7.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXR["rampsoakpattern"][0]][7]:   
            self.label_rs8.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs8.setStyleSheet("background-color:white;")

    @pyqtSlot(bool)
    def setONautotune(self,_):
        self.setONOFFautotune(1)
    
    @pyqtSlot(bool)
    def setOFFautotune(self,_):
        self.setONOFFautotune(0)
    
    def setONOFFautotune(self,flag):
        self.status.showMessage(QApplication.translate("StatusBar","setting autotune..."),500)
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(self.aw.fujipid.PXR["autotuning"][1],6)
            self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,flag)
            r = "00000000"
        else:
            command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXR["autotuning"][1],flag)
            #TX and RX
            r = self.aw.ser.sendFUJIcommand(command,8)
        if len(r) == 8:
            if flag == 0:
                self.aw.fujipid.PXR["autotuning"][0] = 0
                self.status.showMessage(QApplication.translate("StatusBar","Autotune successfully turned OFF"),5000)
            if flag == 1:
                self.aw.fujipid.PXR["autotuning"][0] = 1
                self.status.showMessage(QApplication.translate("StatusBar","Autotune successfully turned ON"),5000)
        else:
            mssg = QApplication.translate("Error Message","Exception:") + " setONOFFautotune()"
            self.status.showMessage(mssg,5000)
            self.aw.qmc.adderror(QApplication.translate("Error Message","Exception:") + " setONOFFautotune()")

    @pyqtSlot(bool)
    def setONstandby(self,_):
        self.setONOFFstandby(1)
    
    @pyqtSlot(bool)
    def setOFFstandby(self,_):
        self.setONOFFstandby(0)

    def setONOFFstandby(self,flag):
        try:
            #standby ON (pid off) will reset: rampsoak modes/autotuning/self tuning
            #flag = 0 standby OFF, flag = 1 standby ON (pid off)
            self.status.showMessage(QApplication.translate("StatusBar","wait..."),500)
            res = self.aw.fujipid.setONOFFstandby(flag)
            if res:
                if flag == 1:
                    message = QApplication.translate("StatusBar","PID OFF")     #put pid in standby 1 (pid off)
                else:
                    message = QApplication.translate("StatusBar","PID ON")      #put pid in standby 0 (pid on)
                self.status.showMessage(message,5000)
            else:
                mssg = QApplication.translate("Error Message","Exception:") + " setONOFFstandby()"
                self.status.showMessage(mssg,5000)
                self.aw.qmc.adderror(mssg)
        except Exception as e: # pylint: disable=broad-except
            #import traceback
            #traceback.print_exc(file=sys.stdout)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:") + " setONOFFstandby() {0}").format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def setsv(self,_):
        self.svedit.setText(self.aw.comma2dot(str(self.svedit.text())))
        if self.svedit.text() != "":
            newSVvalue = int(float(self.svedit.text())*10) #multiply by 10 because of decimal point
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXR["sv0"][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,newSVvalue)
                message = QApplication.translate("StatusBar","SV successfully set to {0}").format(self.svedit.text())
                self.aw.fujipid.PXR["sv0"][0] = float(str(self.svedit.text()))
                self.status.showMessage(message,5000)
                #record command as an Event 
                strcommand = "SETSV::"+ str("%.1f"%(newSVvalue/10.))
                self.aw.qmc.DeviceEventRecord(strcommand)
            else:          
                command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXR["sv0"][1],newSVvalue)
                r = self.aw.ser.sendFUJIcommand(command,8)
                if r == command:
                    message = QApplication.translate("StatusBar","SV successfully set to {0}").format(self.svedit.text())
                    self.aw.fujipid.PXR["sv0"][0] = float(str(self.svedit.text()))
                    self.status.showMessage(message,5000)
                    #record command as an Event 
                    strcommand = "SETSV::"+ str("%.1f"%(newSVvalue/10.))
                    self.aw.qmc.DeviceEventRecord(strcommand)
                else:
                    mssg = QApplication.translate("Error Message","Exception:") + " setsv()"
                    self.status.showMessage(mssg,5000)
                    self.aw.qmc.adderror(mssg)
        else:
            self.status.showMessage(QApplication.translate("StatusBar","Empty SV box"),5000)
            
    @pyqtSlot(bool)
    def getsv(self,_):
        temp = self.aw.fujipid.readcurrentsv()
        if temp != -1:
            self.aw.fujipid.PXR["sv0"][0] =  temp
            self.aw.lcd6.display(self.aw.fujipid.PXR["sv0"][0])
            self.readsvedit.setText(str(self.aw.fujipid.PXR["sv0"][0]))
        else:
            self.status.showMessage(QApplication.translate("StatusBar","Unable to read SV"),5000)

    def checkrampsoakmode(self):
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(self.aw.fujipid.PXR["rampsoakmode"][1],3)
            currentmode = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
        else:
            msg = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,self.aw.fujipid.PXR["rampsoakmode"][1],1)
            currentmode = self.aw.fujipid.readoneword(msg)
        self.aw.fujipid.PXR["rampsoakmode"][0] = currentmode
        if currentmode == 0:
            mode = ["0",
                    QApplication.translate("Message","OFF"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","OFF")]
        elif currentmode == 1:
            mode = ["1",
                    QApplication.translate("Message","OFF"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","ON")]
        elif currentmode == 2:
            mode = ["2",
                    QApplication.translate("Message","OFF"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","OFF")]
        elif currentmode == 3:
            mode = ["3",
                    QApplication.translate("Message","OFF"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","ON")]
        elif currentmode == 4:
            mode = ["4",
                    QApplication.translate("Message","OFF"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","OFF")]
        elif currentmode == 5:
            mode = ["5",
                    QApplication.translate("Message","OFF"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","ON")]
        elif currentmode == 6:
            mode = ["6",
                    QApplication.translate("Message","OFF"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","OFF")]
        elif currentmode == 7:
            mode = ["7",
                    QApplication.translate("Message","OFF"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","ON")]
        elif currentmode == 8:
            mode = ["8",
                    QApplication.translate("Message","ON"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","OFF")]
        elif currentmode == 9:
            mode = ["9",
                    QApplication.translate("Message","ON"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","ON")]
        elif currentmode == 10:
            mode = ["10",
                    QApplication.translate("Message","ON"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","OFF")]
        elif currentmode == 11:
            mode = ["11",
                    QApplication.translate("Message","ON"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","ON")]
        elif currentmode == 12:
            mode = ["12",
                    QApplication.translate("Message","ON"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","OFF")]
        elif currentmode == 13:
            mode = ["13",
                    QApplication.translate("Message","ON"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","CONTINUOUS CONTROL"),
                    QApplication.translate("Message","ON")]
        elif currentmode == 14:
            mode = ["14",
                    QApplication.translate("Message","ON"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","OFF")]
        elif currentmode == 15:
            mode = ["15",
                    QApplication.translate("Message","ON"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","STANDBY MODE"),
                    QApplication.translate("Message","ON")]
        else:
            return -1
        string =  QApplication.translate("Message","The rampsoak-mode tells how to start and end the ramp/soak") + "\n\n"
        string += QApplication.translate("Message","Your rampsoak mode in this pid is:") + "\n\n"
        string += QApplication.translate("Message","Mode = {0}").format(mode[0]) + "\n"
        string += "-----------------------------------------------------------------------\n"
        string += QApplication.translate("Message","Start to run from PV value: {0}").format(mode[1]) + "\n"
        string += QApplication.translate("Message","End output status at the end of ramp/soak: {0}").format(mode[2]) + "\n"
        string += QApplication.translate("Message","Output status while ramp/soak operation set to OFF: {0}").format(mode[3]) + "\n"
        string += QApplication.translate("Message","\nRepeat Operation at the end: {0}").format(mode[4]) + "\n"
        string += "-----------------------------------------------------------------------\n"
        string += QApplication.translate("Message","Recomended Mode = 0") + "\n\n"
        string += QApplication.translate("Message","If you need to change it, change it now and come back later") + "\n"
        string += QApplication.translate("Message","Use the Parameter Loader Software by Fuji if you need to\n\n") + "\n\n\n"
        string += QApplication.translate("Message","Continue?")
        reply = QMessageBox.question(self.aw,QApplication.translate("Message","Ramp Soak start-end mode"),string,
                            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Yes:
            return 1
        return 0

    @pyqtSlot(bool)
    def setONrampsoak(self,_):
        self.setONOFFrampsoak(1)
    
    @pyqtSlot(bool)
    def setOFFrampsoak(self,_):
        self.setONOFFrampsoak(0)
    
    def setONOFFrampsoak(self,flag):
        #flag =0 OFF, flag = 1 ON, flag = 2 hold
        #set rampsoak pattern ON
        if flag == 1:
            check = self.checkrampsoakmode()
            if check == 0:
                self.status.showMessage(QApplication.translate("StatusBar","Ramp/Soak operation cancelled"), 5000)
                return
            if check == -1:
                self.status.showMessage(QApplication.translate("StatusBar","No RX data"), 5000)
            self.status.showMessage(QApplication.translate("StatusBar","RS ON"),500)
            #0 = 1-4
            #1 = 5-8
            #2 = 1-8
            selectedmode = self.patternComboBox.currentIndex()
            currentmode = self.aw.fujipid.getrampsoakmode()
            if currentmode != -1:
                self.aw.fujipid.PXR["rampsoakpattern"][0] = currentmode
                if currentmode != selectedmode:
                    #set mode in pid to match the mode selected in the combobox
                    self.status.showMessage(QApplication.translate("StatusBar","Need to change pattern mode..."),1000)
                    res = self.aw.fujipid.setrampsoakmode(selectedmode)
                    if res:
                        self.status.showMessage(QApplication.translate("StatusBar","Pattern has been changed. Wait 5 secs."), 500)
                    else:
                        self.status.showMessage(QApplication.translate("StatusBar","Pattern could not be changed"), 5000)
                        return
                #combobox mode matches pid mode
                #set ramp soak mode ON/OFF
                res = self.aw.fujipid.setrampsoak(flag)
                if res:
                    #record command as an Event if flag = 1
                    self.status.showMessage(QApplication.translate("StatusBar","RS ON"), 5000)
                    #ramp soak pattern. 0=executes 1 to 4; 1=executes 5 to 8; 2=executes 1 to 8
                    pattern =[[1,4],[5,8],[1,8]]
                    start = pattern[self.aw.fujipid.PXR["rampsoakpattern"][0]][0]
                    end = pattern[self.aw.fujipid.PXR["rampsoakpattern"][0]][1]+1
                    strcommand = "SETRS"
                    result = ""
                    for i in range(start,end):
                        svkey = "segment"+str(i)+"sv"
                        rampkey = "segment"+str(i)+"ramp"
                        soakkey = "segment"+str(i)+"soak"
                        strcommand += "::" + str(self.aw.fujipid.PXR[svkey][0]) + "::" + str(self.aw.fujipid.PXR[rampkey][0]) + "::" + str(self.aw.fujipid.PXR[soakkey][0])+"::"
                        result += strcommand
                        strcommand = "SETRS"
                    result = result.strip(":")
                    self.aw.qmc.DeviceEventRecord(result)
                else:
                    self.status.showMessage(QApplication.translate("StatusBar","RampSoak could not be changed"), 5000)
            else:
                mssg = QApplication.translate("Error Message","Exception:") + " setONOFFrampsoak()"
                self.status.showMessage(mssg,5000)
                self.aw.qmc.adderror(mssg)
        #set ramp soak OFF
        elif flag == 0:
            self.status.showMessage(QApplication.translate("StatusBar","RS OFF"),500)
            self.aw.fujipid.setrampsoak(flag)

    #get all Ramp Soak values for all 8 segments
    @pyqtSlot(bool)
    def getallsegments(self,_):
        for i in range(8):
            msg = QApplication.translate("StatusBar","Reading Ramp/Soak {0} ...").format(str(i+1))
            self.status.showMessage(msg,500)
            k = self.aw.fujipid.getsegment(i+1)
            libtime.sleep(0.03)
            if k == -1:
                self.status.showMessage(QApplication.translate("StatusBar","problem reading Ramp/Soak"),5000)
                return
            self.paintlabels()
        self.status.showMessage(QApplication.translate("StatusBar","Finished reading Ramp/Soak val."),5000)
        self.createsegmenttable()

    @pyqtSlot(bool)
    def getpid(self,_):
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(self.aw.fujipid.PXR["p"][1],3)
            p = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)/10.
        else:    
            pcommand= self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,self.aw.fujipid.PXR["p"][1],1)
            p = self.aw.fujipid.readoneword(pcommand)/10.
        if p == -1 :
            return
        self.pedit.setText(str(int(p)))
        self.aw.fujipid.PXR["p"][0] = p
        #i is int range 0-3200
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(self.aw.fujipid.PXR["i"][1],3)
            i = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)/10.
        else:
            icommand = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,self.aw.fujipid.PXR["i"][1],1)
            i = self.aw.fujipid.readoneword(icommand)/10.
        if i == -1:
            return
        self.iedit.setText(str(int(i)))
        self.aw.fujipid.PXR["i"][0] = i
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(self.aw.fujipid.PXR["d"][1],3)
            d = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)/10.
        else:
            dcommand = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,self.aw.fujipid.PXR["d"][1],1)
            d = self.aw.fujipid.readoneword(dcommand)/10.
        if d == -1:
            return
        self.dedit.setText(str(int(d)))
        self.aw.fujipid.PXR["d"][0] = d
            
        self.status.showMessage(QApplication.translate("StatusBar","Finished reading pid values"),5000)

    @pyqtSlot(bool)
    def setpid_p(self,_):
        if str(self.pedit.text()).isdigit():
            p = int(str(self.pedit.text()))
            self.aw.fujipid.setpidPXR("p",p)
    
    @pyqtSlot(bool)
    def setpid_i(self,_):
        if str(self.iedit.text()).isdigit():
            i = int(str(self.iedit.text()))
            self.aw.fujipid.setpidPXR("i",i)
    
    @pyqtSlot(bool)
    def setpid_d(self,_):
        if str(self.dedit.text()).isdigit():
            d = int(str(self.dedit.text()))
            self.aw.fujipid.setpidPXR("d",d)

    def createsegmenttable(self):
        self.segmenttable.setRowCount(8)
        self.segmenttable.setColumnCount(4)
        self.segmenttable.setHorizontalHeaderLabels([QApplication.translate("Table","SV"),
                                                     QApplication.translate("Table","Ramp HH:MM"),
                                                     QApplication.translate("Table","Soak HH:MM"),""])
        self.segmenttable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.segmenttable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.segmenttable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.segmenttable.setShowGrid(True)
        self.segmenttable.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        regextime = QRegularExpression(r"^-?[0-9]?[0-9]?[0-9]:[0-5][0-9]$")
        #populate table
        for i in range(8):
            #create widgets
            svkey = "segment" + str(i+1) + "sv"
            rampkey = "segment" + str(i+1) + "ramp"
            soakkey = "segment" + str(i+1) + "soak"
            
            svedit = QLineEdit(str(self.aw.fujipid.PXR[svkey][0]))
            svedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, svedit))
            rampedit = QLineEdit(stringfromseconds(self.aw.fujipid.PXR[rampkey][0]))
            rampedit.setValidator(QRegularExpressionValidator(regextime,self))
            soakedit  = QLineEdit(stringfromseconds(self.aw.fujipid.PXR[soakkey][0]))
            soakedit.setValidator(QRegularExpressionValidator(regextime,self))
            setButton = QPushButton(QApplication.translate("Button","Set"))
            setButton.clicked.connect(self.setsegment)
            setButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            #add widgets to the table
            self.segmenttable.setCellWidget(i,0,svedit)
            self.segmenttable.setCellWidget(i,1,rampedit)
            self.segmenttable.setCellWidget(i,2,soakedit)
            self.segmenttable.setCellWidget(i,3,setButton)

    #idn = id number, sv = float set value, ramp = ramp value, soak = soak value
    @pyqtSlot(bool)
    def setsegment(self,_):
        i = self.aw.findWidgetsRow(self.segmenttable,self.sender(),3)
        if i is not None:
            idn = i+1
            svedit =  self.segmenttable.cellWidget(i,0)
            rampedit = self.segmenttable.cellWidget(i,1)
            soakedit = self.segmenttable.cellWidget(i,2)
            sv = float(self.aw.comma2dot(str(svedit.text())))
            ramp = stringtoseconds(str(rampedit.text()))
            soak = stringtoseconds(str(soakedit.text()))
            svkey = "segment" + str(idn) + "sv"
            rampkey = "segment" + str(idn) + "ramp"
            soakkey = "segment" + str(idn) + "soak"
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXR[svkey][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,int(sv*10))
                libtime.sleep(0.1) #important time between writings
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXR[rampkey][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,ramp)
                libtime.sleep(0.1) #important time between writings
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXR[soakkey][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,soak)
                r1 = r2 = r3 = "        "
            else:
                svcommand = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXR[svkey][1],int(sv*10))
                r1 = self.aw.ser.sendFUJIcommand(svcommand,8)
                libtime.sleep(0.1) #important time between writings
                rampcommand = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXR[rampkey][1],ramp)
                r2 = self.aw.ser.sendFUJIcommand(rampcommand,8)
                libtime.sleep(0.1) #important time between writings
                soakcommand = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXR[soakkey][1],soak)
                r3 = self.aw.ser.sendFUJIcommand(soakcommand,8)
            #check if OK
            if len(r1) == 8 and len(r2) == 8 and len(r3) == 8:
                self.aw.fujipid.PXR[svkey][0] = sv
                self.aw.fujipid.PXR[rampkey][0] = ramp
                self.aw.fujipid.PXR[soakkey][0] = soak
                self.paintlabels()
                self.status.showMessage(QApplication.translate("StatusBar","Ramp/Soak successfully written"),5000) 
            else:
                self.aw.qmc.adderror(QApplication.translate("Error Message","Segment values could not be written into PID"))


############################################################################
######################## FUJI PXG4 PID CONTROL DIALOG ######################
############################################################################

class PXG4pidDlgControl(PXpidDlgControl):
    def __init__(self, parent = None, aw = None):
        super().__init__(parent, aw)
        self.setModal(True)
        #self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose) # default is True and this is set already in ArtisanDialog by default
        if self.aw.ser.controlETpid[0] == 0:
            self.setWindowTitle(QApplication.translate("Form Caption","Fuji PXG PID Control"))
        else:
            self.setWindowTitle(QApplication.translate("Form Caption","Fuji PXF PID Control"))
        self.status = QStatusBar()
        self.status.setSizeGripEnabled(False)
        self.status.showMessage(QApplication.translate("StatusBar","Ready"),5000)
        #*************    TAB 1 WIDGETS
        labelrs1 = QLabel()
        labelrs1.setContentsMargins(5,5,5,5)
        labelrs1.setStyleSheet("background-color:'#CCCCCC';")
        labelrs1.setText("<font color='white'><b>" + QApplication.translate("Label", "Ramp Soak (MM:SS)<br>(1-7)") + "</b></font>")
        #labelrs1.setMaximumSize(90, 42)
        #labelrs1.setMinimumHeight(50)
        labelrs2 = QLabel()
        labelrs2.setContentsMargins(5,5,5,5)
        labelrs2.setStyleSheet("background-color:'#CCCCCC';")
        labelrs2.setText("<font color='white'><b>" + QApplication.translate("Label", "Ramp Soak (MM:SS)<br>(8-16)") + "</b></font>")
        #labelrs2.setMaximumSize(90, 42)
        #labelrs2.setMinimumHeight(50)
        self.label_rs1 =  QLabel()
        self.label_rs2 =  QLabel()
        self.label_rs3 =  QLabel()
        self.label_rs4 =  QLabel()
        self.label_rs5 =  QLabel()
        self.label_rs6 =  QLabel()
        self.label_rs7 =  QLabel()
        self.label_rs8 =  QLabel()
        self.label_rs9 =  QLabel()
        self.label_rs10 =  QLabel()
        self.label_rs11 =  QLabel()
        self.label_rs12 =  QLabel()
        self.label_rs13 =  QLabel()
        self.label_rs14 =  QLabel()
        self.label_rs15 =  QLabel()
        self.label_rs16 =  QLabel()
        self.label_rs1.setMinimumWidth(170)
        self.label_rs2.setMinimumWidth(170)
        self.label_rs3.setMinimumWidth(170)
        self.label_rs4.setMinimumWidth(170)
        self.label_rs5.setMinimumWidth(170)
        self.label_rs6.setMinimumWidth(170)
        self.label_rs7.setMinimumWidth(170)
        self.label_rs8.setMinimumWidth(170)
        self.label_rs9.setMinimumWidth(170)
        self.label_rs10.setMinimumWidth(170)
        self.label_rs11.setMinimumWidth(170)
        self.label_rs12.setMinimumWidth(170)
        self.label_rs13.setMinimumWidth(170)
        self.label_rs14.setMinimumWidth(170)
        self.label_rs15.setMinimumWidth(170)
        self.label_rs16.setMinimumWidth(170)
        self.patternComboBox =  QComboBox()
        self.patternComboBox.addItems(["1-4","5-8","1-8","9-12","13-16","9-16","1-16"])
        if self.aw.ser.controlETpid[0] == 0:
            self.patternComboBox.setCurrentIndex(self.aw.fujipid.PXG4["rampsoakpattern"][0])
        else:
            self.patternComboBox.setCurrentIndex(self.aw.fujipid.PXF["rampsoakpattern"][0])
        self.patternComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.patternComboBox.currentIndexChanged.connect(self.paintlabels)
        self.paintlabels()
        button_load = QPushButton(QApplication.translate("Button","Load"))
        button_load.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_save = QPushButton(QApplication.translate("Button","Save"))
        button_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_writeall = QPushButton(QApplication.translate("Button","Write All"))
        button_writeall.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        patternlabel = QLabel(QApplication.translate("Label","Pattern"))
        patternlabel.setAlignment(Qt.AlignmentFlag.AlignRight)
        button_getall = QPushButton(QApplication.translate("Button","Read RS values"))
        button_getall.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_writeallrs = QPushButton(QApplication.translate("Button","Write RS values"))
        button_writeallrs.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_rson =  QPushButton(QApplication.translate("Button","RampSoak ON"))
        button_rson.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_rsoff =  QPushButton(QApplication.translate("Button","RampSoak OFF"))
        button_rsoff.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_exit = QPushButton(QApplication.translate("Button","OK"))
        button_standbyON = QPushButton(QApplication.translate("Button","PID OFF"))
        button_standbyON.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_standbyOFF = QPushButton(QApplication.translate("Button","PID ON"))
        button_standbyOFF.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_getall.clicked.connect(self.getallsegments)
        button_writeallrs.clicked.connect(self.writeRSValues)
        button_rson.clicked.connect(self.setONrampsoak)
        button_rsoff.clicked.connect(self.setOFFrampsoak)
        button_standbyON.clicked.connect(self.setONstandby)
        button_standbyOFF.clicked.connect(self.setOFFstandby)
        button_exit.clicked.connect(self.accept)
        button_load.clicked.connect(self.load)
        button_save.clicked.connect(self.save)
        button_writeall.clicked.connect(self.writeAll)

        #create layouts and place tab1 widgets inside 
        buttonRampSoakLayout1 = QVBoxLayout() #TAB1/COLUNM 1
        buttonRampSoakLayout1.setSpacing(10)
        buttonRampSoakLayout2 = QVBoxLayout() #TAB1/COLUMN 2
        buttonRampSoakLayout2.setSpacing(10)
        #place rs labels in RampSoakLayout1 #TAB1/COLUNM 1
        buttonRampSoakLayout1.addWidget(labelrs1)
        buttonRampSoakLayout1.addWidget(self.label_rs1)
        buttonRampSoakLayout1.addWidget(self.label_rs2)
        buttonRampSoakLayout1.addWidget(self.label_rs3)
        buttonRampSoakLayout1.addWidget(self.label_rs4)
        buttonRampSoakLayout1.addWidget(self.label_rs5)
        buttonRampSoakLayout1.addWidget(self.label_rs6)
        buttonRampSoakLayout1.addWidget(self.label_rs7)
        buttonRampSoakLayout1.addWidget(self.label_rs8)
        #place rs labels in RampSoakLayout2 #TAB1/COLUMN 2
        buttonRampSoakLayout2.addWidget(labelrs2)
        buttonRampSoakLayout2.addWidget(self.label_rs9)
        buttonRampSoakLayout2.addWidget(self.label_rs10)
        buttonRampSoakLayout2.addWidget(self.label_rs11)
        buttonRampSoakLayout2.addWidget(self.label_rs12)
        buttonRampSoakLayout2.addWidget(self.label_rs13)
        buttonRampSoakLayout2.addWidget(self.label_rs14)
        buttonRampSoakLayout2.addWidget(self.label_rs15)
        buttonRampSoakLayout2.addWidget(self.label_rs16)
        
        # Follow Background 
        self.followBackground = QCheckBox(QApplication.translate("CheckBox", "Follow Background"))
        self.followBackground.setChecked(self.aw.fujipid.followBackground)
        self.followBackground.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.followBackground.stateChanged.connect(self.changeFollowBackground)         #toggle
        # Follow Background Lookahead
        self.pidSVLookahead = QSpinBox()
        self.pidSVLookahead.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pidSVLookahead.setRange(0,999)
        self.pidSVLookahead.setSingleStep(1)
        self.pidSVLookahead.setValue(self.aw.fujipid.lookahead)
        self.pidSVLookahead.setSuffix(" s")
        self.pidSVLookahead.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pidSVLookahead.valueChanged.connect(self.changeLookAhead)
        pidSVLookaheadLabel = QLabel(QApplication.translate("Label","Lookahead"))
        
        # *************** TAB 2 WIDGETS
        labelsv = QLabel()
        labelsv.setContentsMargins(10,10,10,10)
        labelsv.setStyleSheet("background-color:'#CCCCCC';")
        labelsv.setText("<font color='white'><b>" + QApplication.translate("Label", "SV (7-0)") + "</b></font>")
        labelsv.setMaximumSize(100, 42)
        labelsv.setMinimumHeight(50)
        labelsvedit = QLabel()
        labelsvedit.setContentsMargins(10,10,10,10)
        labelsvedit.setStyleSheet("background-color:'#CCCCCC';")
        labelsvedit.setText("<font color='white'><b>" + QApplication.translate("Label", "Write") + "</b></font>")
        labelsvedit.setMaximumSize(100, 42)
        labelsvedit.setMinimumHeight(50)
        button_sv1 =QPushButton(QApplication.translate("Button","Write SV1"))
        button_sv1.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_sv2 =QPushButton(QApplication.translate("Button","Write SV2"))
        button_sv2.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_sv3 =QPushButton(QApplication.translate("Button","Write SV3"))
        button_sv3.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_sv4 =QPushButton(QApplication.translate("Button","Write SV4"))
        button_sv4.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_sv5 =QPushButton(QApplication.translate("Button","Write SV5"))
        button_sv5.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_sv6 =QPushButton(QApplication.translate("Button","Write SV6"))
        button_sv6.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_sv7 =QPushButton(QApplication.translate("Button","Write SV7"))
        button_sv7.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_sv1.clicked.connect(self.setsv1)
        button_sv2.clicked.connect(self.setsv2)
        button_sv3.clicked.connect(self.setsv3)
        button_sv4.clicked.connect(self.setsv4)
        button_sv5.clicked.connect(self.setsv5)
        button_sv6.clicked.connect(self.setsv6)
        button_sv7.clicked.connect(self.setsv7)
        self.sv1edit = QLineEdit(str(self.aw.fujipid.PXG4["sv1"][0]))
        self.sv2edit = QLineEdit(str(self.aw.fujipid.PXG4["sv2"][0]))
        self.sv3edit = QLineEdit(str(self.aw.fujipid.PXG4["sv3"][0]))
        self.sv4edit = QLineEdit(str(self.aw.fujipid.PXG4["sv4"][0]))
        self.sv5edit = QLineEdit(str(self.aw.fujipid.PXG4["sv5"][0]))
        self.sv6edit = QLineEdit(str(self.aw.fujipid.PXG4["sv6"][0]))
        self.sv7edit = QLineEdit(str(self.aw.fujipid.PXG4["sv7"][0]))
        self.sv1edit.setMaximumWidth(80)
        self.sv2edit.setMaximumWidth(80)
        self.sv3edit.setMaximumWidth(80)
        self.sv4edit.setMaximumWidth(80)
        self.sv5edit.setMaximumWidth(80)
        self.sv6edit.setMaximumWidth(80)
        self.sv7edit.setMaximumWidth(80)
        self.sv1edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.sv1edit))
        self.sv2edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.sv2edit))
        self.sv3edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.sv3edit))
        self.sv4edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.sv4edit))
        self.sv5edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.sv5edit))
        self.sv6edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.sv6edit))
        self.sv7edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.sv7edit))
        self.radiosv1 = QRadioButton()
        self.radiosv2 = QRadioButton()
        self.radiosv3 = QRadioButton()
        self.radiosv4 = QRadioButton()
        self.radiosv5 = QRadioButton()
        self.radiosv6 = QRadioButton()
        self.radiosv7 = QRadioButton()
        N = self.aw.fujipid.PXG4["selectsv"][0]
        if N == 1:
            self.radiosv1.setChecked(True)
        elif N == 2:
            self.radiosv2.setChecked(True)
        elif N == 3:
            self.radiosv3.setChecked(True)
        elif N == 4:
            self.radiosv4.setChecked(True)
        elif N == 5:
            self.radiosv5.setChecked(True)
        elif N == 6:
            self.radiosv6.setChecked(True)
        elif N == 7:
            self.radiosv7.setChecked(True)
        self.tab2easySVbuttonsFlag = QCheckBox(QApplication.translate("Label","SV Buttons"))
        self.tab2easySVbuttonsFlag.setChecked(self.aw.pidcontrol.svButtons)
        self.tab2easySVbuttonsFlag.stateChanged.connect(self.setSVbuttons)
        self.tab2easySVsliderFlag = QCheckBox(QApplication.translate("Label","SV Slider"))
        self.tab2easySVsliderFlag.setChecked(self.aw.pidcontrol.svSlider)
        self.tab2easySVsliderFlag.stateChanged.connect(self.setSVsliderSlot)
        self.pidSVSliderMin = QSpinBox()
        self.pidSVSliderMin.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pidSVSliderMin.setRange(0,999)
        self.pidSVSliderMin.setSingleStep(10)
        self.pidSVSliderMin.setValue(self.aw.pidcontrol.svSliderMin)
        self.pidSVSliderMin.valueChanged.connect(self.sliderMinValueChangedSlot)
        pidSVSliderMinLabel = QLabel(QApplication.translate("Label","SV min"))
        self.pidSVSliderMax = QSpinBox()
        self.pidSVSliderMax.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pidSVSliderMax.setRange(0,999)
        self.pidSVSliderMax.setSingleStep(10)
        self.pidSVSliderMax.setValue(self.aw.pidcontrol.svSliderMax)
        self.pidSVSliderMax.valueChanged.connect(self.sliderMaxValueChangedSlot)
        pidSVSliderMaxLabel = QLabel(QApplication.translate("Label","SV max"))
        if self.aw.qmc.mode == "F":
            self.pidSVSliderMin.setSuffix(" F")
            self.pidSVSliderMax.setSuffix(" F")
        elif self.aw.qmc.mode == "C":
            self.pidSVSliderMin.setSuffix(" C")
            self.pidSVSliderMax.setSuffix(" C")

        tab2getsvbutton = QPushButton(QApplication.translate("Button","Read SV (7-0)"))
        tab2getsvbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tab2putsvbutton = QPushButton(QApplication.translate("Button","Write SV (7-0)"))
        tab2putsvbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tab2getsvbutton.clicked.connect(self.getallsv)
        tab2putsvbutton.clicked.connect(self.writeSetValues)
        self.radiosv1.clicked.connect(self.setNsvSlot)
        self.radiosv2.clicked.connect(self.setNsvSlot)
        self.radiosv3.clicked.connect(self.setNsvSlot)
        self.radiosv4.clicked.connect(self.setNsvSlot)
        self.radiosv5.clicked.connect(self.setNsvSlot)
        self.radiosv6.clicked.connect(self.setNsvSlot)
        self.radiosv7.clicked.connect(self.setNsvSlot)
        #****************   TAB 3 WIDGETS
        plabel = QLabel()
        plabel.setContentsMargins(10,10,10,10)
        plabel.setStyleSheet("background-color:'#CCCCCC';")
        plabel.setText("<font color='white'><b>" + QApplication.translate("Label", "P") + "</b></font>")
        plabel.setMaximumSize(50, 42)
        plabel.setMinimumHeight(50)
        ilabel = QLabel()
        ilabel.setContentsMargins(10,10,10,10)
        ilabel.setStyleSheet("background-color:'#CCCCCC';")
        ilabel.setText("<font color='white'><b>" + QApplication.translate("Label", "I") + "</b></font>")
        ilabel.setMaximumSize(50, 42)
        ilabel.setMinimumHeight(50)
        dlabel = QLabel()
        dlabel.setContentsMargins(10,10,10,10)
        dlabel.setStyleSheet("background-color:'#CCCCCC';")
        dlabel.setText("<font color='white'><b>" + QApplication.translate("Label", "D") + "</b></font>")
        dlabel.setMaximumSize(50, 42)
        dlabel.setMinimumHeight(50)
        wlabel = QLabel()
        wlabel.setContentsMargins(10,10,10,10)
        wlabel.setStyleSheet("background-color:'#CCCCCC';")
        wlabel.setText("<font color='white'><b>" + QApplication.translate("Label", "Write") + "</b></font>")
        wlabel.setMaximumSize(100, 42)
        wlabel.setMinimumHeight(50)
        self.p1edit =  QLineEdit(str(self.aw.fujipid.PXG4["p1"][0]))
        self.p2edit =  QLineEdit(str(self.aw.fujipid.PXG4["p2"][0]))
        self.p3edit =  QLineEdit(str(self.aw.fujipid.PXG4["p3"][0]))
        self.p4edit =  QLineEdit(str(self.aw.fujipid.PXG4["p4"][0]))
        self.p5edit =  QLineEdit(str(self.aw.fujipid.PXG4["p5"][0]))
        self.p6edit =  QLineEdit(str(self.aw.fujipid.PXG4["p6"][0]))
        self.p7edit =  QLineEdit(str(self.aw.fujipid.PXG4["p7"][0]))
        self.i1edit =  QLineEdit(str(self.aw.fujipid.PXG4["i1"][0]))
        self.i2edit =  QLineEdit(str(self.aw.fujipid.PXG4["i2"][0]))
        self.i3edit =  QLineEdit(str(self.aw.fujipid.PXG4["i3"][0]))
        self.i4edit =  QLineEdit(str(self.aw.fujipid.PXG4["i4"][0]))
        self.i5edit =  QLineEdit(str(self.aw.fujipid.PXG4["i5"][0]))
        self.i6edit =  QLineEdit(str(self.aw.fujipid.PXG4["i6"][0]))
        self.i7edit =  QLineEdit(str(self.aw.fujipid.PXG4["i7"][0]))
        self.d1edit =  QLineEdit(str(self.aw.fujipid.PXG4["d1"][0]))
        self.d2edit =  QLineEdit(str(self.aw.fujipid.PXG4["d2"][0]))
        self.d3edit =  QLineEdit(str(self.aw.fujipid.PXG4["d3"][0]))
        self.d4edit =  QLineEdit(str(self.aw.fujipid.PXG4["d4"][0]))
        self.d5edit =  QLineEdit(str(self.aw.fujipid.PXG4["d5"][0]))
        self.d6edit =  QLineEdit(str(self.aw.fujipid.PXG4["d6"][0]))
        self.d7edit =  QLineEdit(str(self.aw.fujipid.PXG4["d7"][0]))
        self.p1edit.setMaximumSize(50, 42)
        self.p2edit.setMaximumSize(50, 42)
        self.p3edit.setMaximumSize(50, 42)
        self.p4edit.setMaximumSize(50, 42)
        self.p5edit.setMaximumSize(50, 42)
        self.p6edit.setMaximumSize(50, 42)
        self.p7edit.setMaximumSize(50, 42)
        self.i1edit.setMaximumSize(50, 42)
        self.i2edit.setMaximumSize(50, 42)
        self.i3edit.setMaximumSize(50, 42)
        self.i4edit.setMaximumSize(50, 42)
        self.i5edit.setMaximumSize(50, 42)
        self.i6edit.setMaximumSize(50, 42)
        self.i7edit.setMaximumSize(50, 42)
        self.d1edit.setMaximumSize(50, 42)
        self.d2edit.setMaximumSize(50, 42)
        self.d3edit.setMaximumSize(50, 42)
        self.d4edit.setMaximumSize(50, 42)
        self.d5edit.setMaximumSize(50, 42)
        self.d6edit.setMaximumSize(50, 42)
        self.d7edit.setMaximumSize(50, 42)
        #p = 0-999.9
        self.p1edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.p1edit))
        self.p2edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.p2edit))
        self.p3edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.p3edit))
        self.p4edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.p4edit))
        self.p5edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.p5edit))
        self.p6edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.p6edit))
        self.p7edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.p7edit))
        #i are int 0-3200
        self.i1edit.setValidator(QIntValidator(0, 3200, self.i1edit))
        self.i2edit.setValidator(QIntValidator(0, 3200, self.i2edit))
        self.i3edit.setValidator(QIntValidator(0, 3200, self.i3edit))
        self.i4edit.setValidator(QIntValidator(0, 3200, self.i4edit))
        self.i5edit.setValidator(QIntValidator(0, 3200, self.i5edit))
        self.i6edit.setValidator(QIntValidator(0, 3200, self.i6edit))
        self.i7edit.setValidator(QIntValidator(0, 3200, self.i7edit))
        #d 0-999.9
        self.d1edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.d1edit))
        self.d2edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.d2edit))
        self.d3edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.d3edit))
        self.d4edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.d4edit))
        self.d5edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.d5edit))
        self.d6edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.d6edit))
        self.d7edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.d7edit))
        self.pid1button = QPushButton(QApplication.translate("Button","pid 1"))
        self.pid1button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pid2button = QPushButton(QApplication.translate("Button","pid 2"))
        self.pid2button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pid3button = QPushButton(QApplication.translate("Button","pid 3"))
        self.pid3button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pid4button = QPushButton(QApplication.translate("Button","pid 4"))
        self.pid4button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pid5button = QPushButton(QApplication.translate("Button","pid 5"))
        self.pid5button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pid6button = QPushButton(QApplication.translate("Button","pid 6"))
        self.pid6button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pid7button = QPushButton(QApplication.translate("Button","pid 7"))
        self.pid7button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        pidreadallbutton = QPushButton(QApplication.translate("Button","Read PIDs"))
        pidreadallbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        pidwriteallbutton = QPushButton(QApplication.translate("Button","Write PIDs"))
        pidwriteallbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        autotuneONbutton = QPushButton(QApplication.translate("Button","Autotune ON"))
        autotuneONbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        autotuneOFFbutton = QPushButton(QApplication.translate("Button","Autotune OFF"))
        autotuneOFFbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cancel3button = QPushButton(QApplication.translate("Button","Cancel"))
        cancel3button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.radiopid1 = QRadioButton()
        self.radiopid2 = QRadioButton()
        self.radiopid3 = QRadioButton()
        self.radiopid4 = QRadioButton()
        self.radiopid5 = QRadioButton()
        self.radiopid6 = QRadioButton()
        self.radiopid7 = QRadioButton()
        pidreadallbutton.clicked.connect(self.getallpid)
        pidwriteallbutton.clicked.connect(self.writePIDValues)
        self.radiopid1.clicked.connect(self.setNpidSlot)
        self.radiopid2.clicked.connect(self.setNpidSlot)
        self.radiopid3.clicked.connect(self.setNpidSlot)
        self.radiopid4.clicked.connect(self.setNpidSlot)
        self.radiopid5.clicked.connect(self.setNpidSlot)
        self.radiopid6.clicked.connect(self.setNpidSlot)
        self.radiopid7.clicked.connect(self.setNpidSlot)
        self.pid1button.clicked.connect(self.setpidSlot)
        self.pid2button.clicked.connect(self.setpidSlot)
        self.pid3button.clicked.connect(self.setpidSlot)
        self.pid4button.clicked.connect(self.setpidSlot)
        self.pid5button.clicked.connect(self.setpidSlot)
        self.pid6button.clicked.connect(self.setpidSlot)
        self.pid7button.clicked.connect(self.setpidSlot)
        cancel3button.clicked.connect(self.cancelAction)
        autotuneONbutton.clicked.connect(self.setONautotune)
        autotuneOFFbutton.clicked.connect(self.setOFFautotune)
        #****************************   TAB4 WIDGETS
        #table for setting segments
        self.segmenttable = QTableWidget()
        self.createsegmenttable()
        #****************************   TAB5 WIDGETS
        BTthermolabelnote = QLabel(QApplication.translate("Label","NOTE: BT Thermocouple type is not stored in the Artisan settings"))
        self.ETthermocombobox = QComboBox()
        self.ETthermocombobox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.BTthermocombobox = QComboBox()
        self.BTthermocombobox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if self.aw.ser.controlETpid[0] == 0: # PXG
            self.ETthermocombobox.addItems(self.aw.fujipid.PXGthermotypes)
            if self.aw.fujipid.PXG4["pvinputtype"][0] in self.aw.fujipid.PXGconversiontoindex:
                self.ETthermocombobox.setCurrentIndex(self.aw.fujipid.PXGconversiontoindex.index(self.aw.fujipid.PXG4["pvinputtype"][0]))
        else: # PXF
            self.ETthermocombobox.addItems(self.aw.fujipid.PXFthermotypes)
            if self.aw.fujipid.PXF["pvinputtype"][0] in self.aw.fujipid.PXFconversiontoindex:
                self.ETthermocombobox.setCurrentIndex(self.aw.fujipid.PXFconversiontoindex.index(self.aw.fujipid.PXF["pvinputtype"][0]))
        if self.aw.ser.readBTpid[0] == 0:        #fuji PXG
            self.BTthermocombobox.addItems(self.aw.fujipid.PXGthermotypes)
        elif self.aw.ser.readBTpid[0] == 1:      #fuji PXR
            self.BTthermocombobox.addItems(self.aw.fujipid.PXRthermotypes)
        else:      #fuji PXF
            self.BTthermocombobox.addItems(self.aw.fujipid.PXFthermotypes)
        setETthermocouplebutton = QPushButton(QApplication.translate("Button","Set"))
        setETthermocouplebutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        setBTthermocouplebutton = QPushButton(QApplication.translate("Button","Set"))
        setBTthermocouplebutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        getETthermocouplebutton = QPushButton(QApplication.translate("Button","Read"))
        getETthermocouplebutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        getBTthermocouplebutton = QPushButton(QApplication.translate("Button","Read"))
        getBTthermocouplebutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        setETthermocouplebutton.setMaximumWidth(80)
        getETthermocouplebutton.setMaximumWidth(80)
        setBTthermocouplebutton.setMaximumWidth(80)
        getBTthermocouplebutton.setMaximumWidth(80)
        setETthermocouplebutton.clicked.connect(self.setthermocoupletypeET)
        setBTthermocouplebutton.clicked.connect(self.setthermocoupletypeBT)
        getETthermocouplebutton.clicked.connect(self.readthermocoupletypeET)
        getBTthermocouplebutton.clicked.connect(self.readthermocoupletypeBT)
        PointButtonET = QPushButton(QApplication.translate("Button","Set ET PID to 1 decimal point"))
        PointButtonET.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        PointButtonBT = QPushButton(QApplication.translate("Button","Set BT PID to 1 decimal point"))
        PointButtonBT.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        timeunitsbutton = QPushButton(QApplication.translate("Button","Set ET PID to MM:SS time units"))
        timeunitsbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        pointlabel = QLabel(QApplication.translate("Label","Artisan uses 1 decimal point"))
        if self.aw.ser.controlETpid[0] == 0:
            timelabel = QLabel(QApplication.translate("Label","Artisan Fuji PXG uses MINUTES:SECONDS units in Ramp/Soaks"))
        else:
            timelabel = QLabel(QApplication.translate("Label","Artisan Fuji PXF uses MINUTES:SECONDS units in Ramp/Soaks"))
        PointButtonET.clicked.connect(self.setpointET)
        PointButtonBT.clicked.connect(self.setpointBT)
        timeunitsbutton.clicked.connect(self.settimeunits)
        # LAYOUTS
        tab1Layout = QGridLayout() #TAB1
        tab1Layout.setSpacing(10)
        tab1Layout.setSizeConstraint(2)
        tab1Layout.addLayout(buttonRampSoakLayout1,0,0)
        tab1Layout.addLayout(buttonRampSoakLayout2,0,1)
        tab1Layout.addWidget(button_rson,1,0)
        tab1Layout.addWidget(button_rsoff,1,1)
        tab1Layout.addWidget(button_standbyOFF,2,0)
        tab1Layout.addWidget(button_standbyON,2,1)
        tab1Layout.addWidget(patternlabel,3,0)
        tab1Layout.addWidget(self.patternComboBox,3,1)
        tab1Layout.addWidget(button_getall,4,0)
        tab1Layout.addWidget(button_writeallrs,4,1)
        tab2Layout = QGridLayout() #TAB2 
        tab2Layout.setSpacing(10)
        tab2Layout.setSizeConstraint(2)
        tab2Layout.addWidget(labelsv,0,0)
        tab2Layout.addWidget(labelsvedit,0,1)
        tab2Layout.addWidget(self.sv7edit,1,0)
        tab2Layout.addWidget(button_sv7,1,1)
        tab2Layout.addWidget(self.sv6edit,2,0)
        tab2Layout.addWidget(button_sv6,2,1)
        tab2Layout.addWidget(self.sv5edit,3,0)
        tab2Layout.addWidget(button_sv5,3,1)
        tab2Layout.addWidget(self.sv4edit,4,0)
        tab2Layout.addWidget(button_sv4,4,1)
        tab2Layout.addWidget(self.sv3edit,5,0)
        tab2Layout.addWidget(button_sv3,5,1)
        tab2Layout.addWidget(self.sv2edit,6,0)
        tab2Layout.addWidget(button_sv2,6,1)
        tab2Layout.addWidget(self.sv1edit,7,0)
        tab2Layout.addWidget(button_sv1,7,1)
        tab2Layout.addWidget(self.radiosv7,1,2)
        tab2Layout.addWidget(self.radiosv6,2,2)
        tab2Layout.addWidget(self.radiosv5,3,2)
        tab2Layout.addWidget(self.radiosv4,4,2)
        tab2Layout.addWidget(self.radiosv3,5,2)
        tab2Layout.addWidget(self.radiosv2,6,2)
        tab2Layout.addWidget(self.radiosv1,7,2)
        tab2Layout.addWidget(self.tab2easySVbuttonsFlag,8,0)
        tab2Layout.addWidget(self.tab2easySVsliderFlag,8,1)
        tab2Layout.addWidget(pidSVSliderMinLabel,8,3)
        tab2Layout.addWidget(self.pidSVSliderMin,8,4)
#        tab2Layout.addWidget(tab2easyOFFsvslider,9,0)
#        tab2Layout.addWidget(tab2easyONsvslider,9,1)
        tab2Layout.addWidget(pidSVSliderMaxLabel,9,3)
        tab2Layout.addWidget(self.pidSVSliderMax,9,4)
        tab2Layout.addWidget(tab2getsvbutton,9,0)
        tab2Layout.addWidget(tab2putsvbutton,9,1)
        tab3Layout = QGridLayout() #TAB3
        tab3Layout.setSpacing(10)
        tab3Layoutbutton = QGridLayout()
        tab3MasterLayout = QVBoxLayout()
        tab3MasterLayout.addLayout(tab3Layout,0)
        tab3MasterLayout.addLayout(tab3Layoutbutton,1)
        tab3Layout.addWidget(plabel,0,0)
        tab3Layout.addWidget(ilabel,0,1)
        tab3Layout.addWidget(dlabel,0,2)
        tab3Layout.addWidget(wlabel,0,3)
        tab3Layout.addWidget(self.p1edit,1,0)
        tab3Layout.addWidget(self.i1edit,1,1)
        tab3Layout.addWidget(self.d1edit,1,2)
        tab3Layout.addWidget(self.pid1button,1,3)
        tab3Layout.addWidget(self.p2edit,2,0)
        tab3Layout.addWidget(self.i2edit,2,1)
        tab3Layout.addWidget(self.d2edit,2,2)
        tab3Layout.addWidget(self.pid2button,2,3)
        tab3Layout.addWidget(self.p3edit,3,0)
        tab3Layout.addWidget(self.i3edit,3,1)
        tab3Layout.addWidget(self.d3edit,3,2)
        tab3Layout.addWidget(self.pid3button,3,3)
        tab3Layout.addWidget(self.p4edit,4,0)
        tab3Layout.addWidget(self.i4edit,4,1)
        tab3Layout.addWidget(self.d4edit,4,2)
        tab3Layout.addWidget(self.pid4button,4,3)
        tab3Layout.addWidget(self.p5edit,5,0)
        tab3Layout.addWidget(self.i5edit,5,1)
        tab3Layout.addWidget(self.d5edit,5,2)
        tab3Layout.addWidget(self.pid5button,5,3)
        tab3Layout.addWidget(self.p6edit,6,0)
        tab3Layout.addWidget(self.i6edit,6,1)
        tab3Layout.addWidget(self.d6edit,6,2)
        tab3Layout.addWidget(self.pid6button,6,3)
        tab3Layout.addWidget(self.p7edit,7,0)
        tab3Layout.addWidget(self.i7edit,7,1)
        tab3Layout.addWidget(self.d7edit,7,2)
        tab3Layout.addWidget(self.pid7button,7,3)
        tab3Layout.addWidget(self.radiopid1,1,4)
        tab3Layout.addWidget(self.radiopid2,2,4)
        tab3Layout.addWidget(self.radiopid3,3,4)
        tab3Layout.addWidget(self.radiopid4,4,4)
        tab3Layout.addWidget(self.radiopid5,5,4)
        tab3Layout.addWidget(self.radiopid6,6,4)
        tab3Layout.addWidget(self.radiopid7,7,4)
        tab3Layoutbutton.addWidget(autotuneONbutton,0,0)
        tab3Layoutbutton.addWidget(autotuneOFFbutton,0,1)
        tab3Layoutbutton.addWidget(pidreadallbutton,1,0)
        tab3Layoutbutton.addWidget(pidwriteallbutton,1,1)
        #tab 4
        tab4layout = QVBoxLayout()
        tab4layout.addWidget(self.segmenttable)
        #tab5
        thermolayoutET = QHBoxLayout()
        thermolayoutET.addWidget(self.ETthermocombobox)
        thermolayoutET.addStretch()
        thermolayoutET.addWidget(getETthermocouplebutton)
        thermolayoutET.addWidget(setETthermocouplebutton)
        ETGroupBox = QGroupBox(QApplication.translate("Label","ET Thermocouple type"))
        ETGroupBox.setLayout(thermolayoutET)
        thermolayoutBT = QHBoxLayout()
        thermolayoutBT.addWidget(self.BTthermocombobox)
        thermolayoutBT.addStretch()
        thermolayoutBT.addWidget(getBTthermocouplebutton)
        thermolayoutBT.addWidget(setBTthermocouplebutton)
        BTGroupBox = QGroupBox(QApplication.translate("Label","BT Thermocouple type"))
        BTGroupBox.setLayout(thermolayoutBT)
        tab5Layout = QVBoxLayout()
        tab5Layout.addStretch()
        tab5Layout.addWidget(ETGroupBox)
        tab5Layout.addWidget(BTGroupBox)
        tab5Layout.addWidget(BTthermolabelnote)
        tab5Layout.addStretch()
        tab5Layout.addWidget(pointlabel)
        tab5Layout.addWidget(PointButtonET)
        tab5Layout.addWidget(PointButtonBT)
        tab5Layout.addStretch()
        tab5Layout.addWidget(timelabel)
        tab5Layout.addWidget(timeunitsbutton)
        tab5Layout.addStretch()
        ############################
        followLayout = QHBoxLayout()
        followLayout.addStretch()
        followLayout.addWidget(self.followBackground)
        followLayout.addStretch()
        followLayout.addWidget(pidSVLookaheadLabel)
        followLayout.addWidget(self.pidSVLookahead)
        followLayout.addStretch()
        ############################
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(button_load)
        buttonLayout.addWidget(button_save)
        buttonLayout.addStretch()
        buttonLayout.addWidget(button_writeall)
        buttonLayout.addStretch()
        buttonLayout.addWidget(button_exit)
        ############################
        TabWidget = QTabWidget()
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        TabWidget.addTab(C1Widget,QApplication.translate("Tab","RS"))
        C2Widget = QWidget()
        C2Widget.setLayout(tab2Layout)
        TabWidget.addTab(C2Widget,QApplication.translate("Tab","SV"))
        C3Widget = QWidget()
        C3Widget.setLayout(tab3MasterLayout)
        TabWidget.addTab(C3Widget,QApplication.translate("Tab","PID"))
        C4Widget = QWidget()
        C4Widget.setLayout(tab4layout)
        TabWidget.addTab(C4Widget,QApplication.translate("Tab","Set RS"))
        C5Widget = QWidget()
        C5Widget.setLayout(tab5Layout)
        TabWidget.addTab(C5Widget,QApplication.translate("Tab","Extra"))
        #incorporate layouts
        layout = QVBoxLayout()
        layout.addWidget(self.status,0)
        layout.addWidget(TabWidget,1)
        layout.addLayout(followLayout,2)
        layout.addLayout(buttonLayout,3)
        self.setLayout(layout)
    
    @pyqtSlot(bool)
    def cancelAction(self,_):
        self.reject()
    
    @pyqtSlot(int)
    def sliderMinValueChangedSlot(self,i):
        self.aw.pidcontrol.sliderMinValueChanged(i)
    
    @pyqtSlot(int)
    def sliderMaxValueChangedSlot(self,i):
        self.aw.pidcontrol.sliderMaxValueChanged(i)
    
    @pyqtSlot(int)
    def setSVbuttons(self,flag):
        self.aw.pidcontrol.svButtons = bool(flag)
        
    @pyqtSlot(int)
    def setSVsliderSlot(self,i):
        self.setSVslider(i)
        self.aw.pidcontrol.activateSVSlider(i)

    def setSVslider(self,flag):
        self.aw.pidcontrol.svSlider = bool(flag)

    @pyqtSlot(int)
    def changeLookAhead(self,_):
        self.aw.fujipid.lookahead = int(self.pidSVLookahead.value())
    
    @pyqtSlot(int)
    def changeFollowBackground(self,_):
        self.aw.fujipid.followBackground = not self.aw.fujipid.followBackground
    
    @pyqtSlot(bool)
    def load(self,_):
        self.aw.fileImport(QApplication.translate("Message", "Load PID Settings",None),self.loadPIDJSON)

    def loadPIDJSON(self,filename):
        try:
            import io
            from json import load as json_load
            with io.open(filename, 'r', encoding='utf-8') as infile:
                pids = json_load(infile)
            # load set values
            setvalues = pids["setvalues"]
            for i in range(7):
                svkey = "sv" + str(i+1)
                self.aw.fujipid.PXG4[svkey][0] = setvalues[svkey]
            self.sv1edit.setText(str(self.aw.fujipid.PXG4["sv1"][0]))
            self.sv2edit.setText(str(self.aw.fujipid.PXG4["sv2"][0]))
            self.sv3edit.setText(str(self.aw.fujipid.PXG4["sv3"][0]))
            self.sv4edit.setText(str(self.aw.fujipid.PXG4["sv4"][0]))
            self.sv5edit.setText(str(self.aw.fujipid.PXG4["sv5"][0]))
            self.sv6edit.setText(str(self.aw.fujipid.PXG4["sv6"][0]))
            self.sv7edit.setText(str(self.aw.fujipid.PXG4["sv7"][0]))
            # load PID values
            pidvalues = pids["pidvalues"]
            for i in range(7):
                pkey = "p" + str(i+1)
                ikey = "i" + str(i+1)
                dkey = "d" + str(i+1)
                self.aw.fujipid.PXG4[pkey][0] = pidvalues[pkey]
                self.aw.fujipid.PXG4[ikey][0] = pidvalues[ikey]
                self.aw.fujipid.PXG4[dkey][0] = pidvalues[dkey]
            self.p1edit.setText(str(self.aw.fujipid.PXG4["p1"][0]))
            self.p2edit.setText(str(self.aw.fujipid.PXG4["p2"][0]))
            self.p3edit.setText(str(self.aw.fujipid.PXG4["p3"][0]))
            self.p4edit.setText(str(self.aw.fujipid.PXG4["p4"][0]))
            self.p5edit.setText(str(self.aw.fujipid.PXG4["p5"][0]))
            self.p6edit.setText(str(self.aw.fujipid.PXG4["p6"][0]))
            self.p7edit.setText(str(self.aw.fujipid.PXG4["p7"][0]))
            self.i1edit.setText(str(self.aw.fujipid.PXG4["i1"][0]))
            self.i2edit.setText(str(self.aw.fujipid.PXG4["i2"][0]))
            self.i3edit.setText(str(self.aw.fujipid.PXG4["i3"][0]))
            self.i4edit.setText(str(self.aw.fujipid.PXG4["i4"][0]))
            self.i5edit.setText(str(self.aw.fujipid.PXG4["i5"][0]))
            self.i6edit.setText(str(self.aw.fujipid.PXG4["i6"][0]))
            self.i7edit.setText(str(self.aw.fujipid.PXG4["i7"][0]))
            self.d1edit.setText(str(self.aw.fujipid.PXG4["d1"][0]))
            self.d2edit.setText(str(self.aw.fujipid.PXG4["d2"][0]))
            self.d3edit.setText(str(self.aw.fujipid.PXG4["d3"][0]))
            self.d4edit.setText(str(self.aw.fujipid.PXG4["d4"][0]))
            self.d5edit.setText(str(self.aw.fujipid.PXG4["d5"][0]))
            self.d6edit.setText(str(self.aw.fujipid.PXG4["d6"][0]))
            self.d7edit.setText(str(self.aw.fujipid.PXG4["d7"][0]))
            # load ramp-soak segments
            segments = pids["segments"]
            for i in range(16):
                svkey = "segment" + str(i+1) + "sv"
                rampkey = "segment" + str(i+1) + "ramp"
                soakkey = "segment" + str(i+1) + "soak"
                self.aw.fujipid.PXG4[svkey][0] = segments[svkey]
                self.aw.fujipid.PXG4[rampkey][0] = stringtoseconds(segments[rampkey])
                self.aw.fujipid.PXG4[soakkey][0] = stringtoseconds(segments[soakkey])
            self.createsegmenttable()
        except Exception as ex: # pylint: disable=broad-except
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " loadPIDJSON() {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def writeSetValues(self,_=False):
        for i in range(7):
            self.setsv(i+1)

    @pyqtSlot(bool)
    def writePIDValues(self,_=False):
        for i in range(7):
            self.setpid(i+1)

    @pyqtSlot(bool)
    def writeRSValues(self,_=False):
        for i in range(16):
            self.setsegment(i)

    @pyqtSlot(bool)
    def writeAll(self,_):
        self.writeSetValues()
        self.writePIDValues()
        self.writeRSValues()

    @pyqtSlot(bool)
    def save(self,_):
        self.aw.fileExport(QApplication.translate("Message", "Save PID Settings",None),"*.apid",self.savePIDJSON)

    def savePIDJSON(self,filename):
        try:
            pids = {}
            # store set values
            setvalues = {}
            for i in range(7):
                svkey = "sv" + str(i+1)
                setvalues[svkey] = self.aw.fujipid.PXG4[svkey][0]
            pids["setvalues"] = setvalues
            # store PID values
            pidvalues = {}
            for i in range(7):
                pkey = "p" + str(i+1)
                ikey = "i" + str(i+1)
                dkey = "d" + str(i+1)
                pidvalues[pkey] = self.aw.fujipid.PXG4[pkey][0]
                pidvalues[ikey] = self.aw.fujipid.PXG4[ikey][0]
                pidvalues[dkey] = self.aw.fujipid.PXG4[dkey][0]
            pids["pidvalues"] = pidvalues
            # store ramp-soak segments
            segments = {}
            for i in range(16):
                svkey = "segment" + str(i+1) + "sv"
                rampkey = "segment" + str(i+1) + "ramp"
                soakkey = "segment" + str(i+1) + "soak"
                segments[svkey] = self.aw.fujipid.PXG4[svkey][0]
                segments[rampkey] = stringfromseconds(self.aw.fujipid.PXG4[rampkey][0])
                segments[soakkey] = stringfromseconds(self.aw.fujipid.PXG4[soakkey][0])
            pids["segments"] = segments
            from json import dump as json_dump
            with open(filename, 'w', encoding='utf-8') as outfile:
                json_dump(pids, outfile, ensure_ascii=True)
                outfile.write('\n')
            return True
        except Exception as ex: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:",None) + " savePIDJSON(): {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
            return False

    @pyqtSlot(bool)
    def settimeunits(self,_):
        if self.aw.ser.controlETpid[0] == 0:
            reg_dict = self.aw.fujipid.PXG4
        else:
            reg_dict = self.aw.fujipid.PXF
        try:
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(reg_dict["timeunits"][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,1)
                r = command = ""
            else:
                command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,reg_dict["timeunits"][1],1)
                r = self.aw.ser.sendFUJIcommand(command,8)
            #check response from pid and update message on main window
            if r == command:
                message = QApplication.translate("StatusBar","Time Units successfully set to MM:SS",None)
                self.status.showMessage(message, 5000)
            else:
                self.status.showMessage(QApplication.translate("StatusBar","Problem setting time units",None),5000)
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:",None) + " settimeunits(): {0}").format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))
    
    @pyqtSlot(int)
    def paintlabels(self,_=0):
        #read values of computer variables (not the actual pid values) to place in buttons
        str1 = "1 [T " + str(self.aw.fujipid.PXG4["segment1sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment1ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment1soak"][0]) + "]"
        str2 = "2 [T " + str(self.aw.fujipid.PXG4["segment2sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment2ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment2soak"][0]) + "]"
        str3 = "3 [T " + str(self.aw.fujipid.PXG4["segment3sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment3ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment3soak"][0]) + "]"
        str4 = "4 [T " + str(self.aw.fujipid.PXG4["segment4sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment4ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment4soak"][0]) + "]"
        str5 = "5 [T " + str(self.aw.fujipid.PXG4["segment5sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment5ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment5soak"][0]) + "]"
        str6 = "6 [T " + str(self.aw.fujipid.PXG4["segment6sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment6ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment6soak"][0]) + "]"
        str7 = "7 [T " + str(self.aw.fujipid.PXG4["segment7sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment7ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment7soak"][0]) + "]"
        str8 = "8 [T " + str(self.aw.fujipid.PXG4["segment8sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment8ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment8soak"][0]) + "]"
        str9 = "9 [T " + str(self.aw.fujipid.PXG4["segment9sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment9ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment9soak"][0]) + "]"
        str10 = "10 [T " + str(self.aw.fujipid.PXG4["segment10sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment10ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment10soak"][0]) + "]"
        str11 = "11 [T " + str(self.aw.fujipid.PXG4["segment11sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment11ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment11soak"][0]) + "]"
        str12 = "12 [T " + str(self.aw.fujipid.PXG4["segment12sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment12ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment12soak"][0]) + "]"
        str13 = "13 [T " + str(self.aw.fujipid.PXG4["segment13sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment13ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment13soak"][0]) + "]"
        str14 = "14 [T " + str(self.aw.fujipid.PXG4["segment14sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment14ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment14soak"][0]) + "]"
        str15 = "15 [T " + str(self.aw.fujipid.PXG4["segment15sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment15ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment15soak"][0]) + "]"
        str16 = "16 [T " + str(self.aw.fujipid.PXG4["segment16sv"][0]) + "] [R " + stringfromseconds(self.aw.fujipid.PXG4["segment16ramp"][0]) + "] [S " + stringfromseconds(self.aw.fujipid.PXG4["segment16soak"][0]) + "]"
        self.label_rs1.setText(str1)
        self.label_rs2.setText(str2)
        self.label_rs3.setText(str3)
        self.label_rs4.setText(str4)
        self.label_rs5.setText(str5)
        self.label_rs6.setText(str6)
        self.label_rs7.setText(str7)
        self.label_rs8.setText(str8)
        self.label_rs9.setText(str9)
        self.label_rs10.setText(str10)
        self.label_rs11.setText(str11)
        self.label_rs12.setText(str12)
        self.label_rs13.setText(str13)
        self.label_rs14.setText(str14)
        self.label_rs15.setText(str15)
        self.label_rs16.setText(str16)
        pattern = [[1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],
                  [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0],
                  [1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0],
                  [0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0],
                  [0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1],
                  [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1],
                  [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]]
        self.aw.fujipid.PXG4["rampsoakpattern"][0] = self.patternComboBox.currentIndex()
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][0]:
            self.label_rs1.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs1.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][1]:
            self.label_rs2.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs2.setStyleSheet("background-color:white;")

        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][2]:
            self.label_rs3.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs3.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][3]:
            self.label_rs4.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs4.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][4]:
            self.label_rs5.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs5.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][5]:
            self.label_rs6.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs6.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][6]:
            self.label_rs7.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs7.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][7]:
            self.label_rs8.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs8.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][8]:
            self.label_rs9.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs9.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][9]:
            self.label_rs10.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs10.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][10]:
            self.label_rs11.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs11.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][11]:
            self.label_rs12.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs12.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][12]:
            self.label_rs13.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs13.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][13]:
            self.label_rs14.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs14.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][14]:
            self.label_rs15.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs15.setStyleSheet("background-color:white;")
        if pattern[self.aw.fujipid.PXG4["rampsoakpattern"][0]][15]:
            self.label_rs16.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs16.setStyleSheet("background-color:white;")

    @pyqtSlot(bool)
    def setNsvSlot(self,_):
        widget = self.sender()
        if widget == self.radiosv1:
            self.setNsv(1)
        elif widget == self.radiosv2:
            self.setNsv(2)
        elif widget == self.radiosv3:
            self.setNsv(3)
        elif widget == self.radiosv4:
            self.setNsv(4)
        elif widget == self.radiosv5:
            self.setNsv(5)
        elif widget == self.radiosv6:
            self.setNsv(6)
        elif widget == self.radiosv7:
            self.setNsv(7)

    #selects an sv
    def setNsv(self,svn):
        if self.aw.ser.controlETpid[0] == 0:
            reg_dict = self.aw.fujipid.PXG4
        else:
            reg_dict = self.aw.fujipid.PXF
        # read current sv N
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(reg_dict["selectsv"][1],3)
            N = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
        else:
            command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,reg_dict["selectsv"][1],1)
            N = self.aw.fujipid.readoneword(command)
        # if current svN is different than requested svN
        if N != -1:
            if N != svn:
                string = QApplication.translate("Message","Current sv = {0}. Change now to sv = {1}?",None).format(str(N),str(svn))
                reply = QMessageBox.question(self.aw,QApplication.translate("Message","Change svN",None),string,
                                    QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel)
                if reply == QMessageBox.StandardButton.Yes:
                    #change variable svN
                    if self.aw.ser.useModbusPort:
                        reg = self.aw.modbus.address2register(reg_dict["selectsv"][1],6)
                        self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,svn)
                        r = command = ""
                    else:
                        command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,reg_dict["selectsv"][1],svn)
                        r = self.aw.ser.sendFUJIcommand(command,8)
                    #check response from pid and update message on main window
                    if r == command:
                        if svn > 0:
                            reg_dict["selectsv"][0] = svn
                            key = "sv" + str(svn)
                            message = QApplication.translate("StatusBar","SV{0} set to {1}",None).format(str(svn),str(reg_dict[key][0]))
                            self.aw.lcd6.display(str(reg_dict[key][0]))
                            self.status.showMessage(message, 5000)
                    else:
                        self.status.showMessage(QApplication.translate("StatusBar","Problem setting SV",None),5000)
                elif reply == QMessageBox.StandardButton.Cancel:
                    self.status.showMessage(QApplication.translate("StatusBar","Cancelled svN change",None),5000)
                    #set radio button
                    if N == 1:
                        self.radiosv1.setChecked(True)
                    elif N == 2:
                        self.radiosv2.setChecked(True)
                    elif N == 3:
                        self.radiosv3.setChecked(True)
                    elif N == 4:
                        self.radiosv4.setChecked(True)
                    elif N == 5:
                        self.radiosv5.setChecked(True)
                    elif N == 6:
                        self.radiosv6.setChecked(True)
                    elif N == 7:
                        self.radiosv7.setChecked(True)
                    return 
            else:
                mssg = QApplication.translate("StatusBar","PID already using sv{0}",None).format(str(N))
                self.status.showMessage(mssg,1000)
        else:
            mssg = QApplication.translate("StatusBar","setNsv(): bad response",None)
            self.status.showMessage(mssg,1000)
            self.aw.qmc.adderror(mssg)

    def setNpidSlot(self,_):
        widget = self.sender()
        if widget == self.radiopid1:
            self.setNpid(1)
        elif widget == self.radiopid2:
            self.setNpid(2)
        elif widget == self.radiopid3:
            self.setNpid(3)
        elif widget == self.radiopid4:
            self.setNpid(4)
        elif widget == self.radiopid5:
            self.setNpid(5)
        elif widget == self.radiopid6:
            self.setNpid(6)
        elif widget == self.radiopid7:
            self.setNpid(7)
        
    #selects an sv
    def setNpid(self,pidn):
        if self.aw.ser.controlETpid[0] == 0:
            reg_dict = self.aw.fujipid.PXG4
        else:
            reg_dict = self.aw.fujipid.PXF
        # read current sv N
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(reg_dict["selectedpid"][1],3)
            N = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
        else:
            command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,reg_dict["selectedpid"][1],1)
            N = self.aw.fujipid.readoneword(command)
        if N is not None and N != -1:
            reg_dict["selectedpid"][0] = N
            # if current svN is different than requested svN
            if N != pidn:
                string = QApplication.translate("Message","Current pid = {0}. Change now to pid ={1}?",None).format(str(N),str(pidn))
                reply = QMessageBox.question(self.aw,QApplication.translate("Message","Change svN",None),string,
                                    QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel)
                if reply == QMessageBox.StandardButton.Yes:
                    #change variable svN
                    if self.aw.ser.useModbusPort:
                        reg = self.aw.modbus.address2register(reg_dict["selectedpid"][1],6)
                        self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,pidn)
                        r = command = ""
                    else:
                        command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,reg_dict["selectedpid"][1],pidn)
                        r = self.aw.ser.sendFUJIcommand(command,8)
                    #check response from pid and update message on main window
                    if r == command:
                        reg_dict["selectedpid"][0] = pidn
                        #key = "sv" + str(pidn)
                        message = QApplication.translate("StatusBar","pid changed to {0}",None).format(str(pidn))
                        self.status.showMessage(message, 5000)
                    else:
                        mssg = QApplication.translate("StatusBar","setNpid(): bad confirmation",None)
                        self.status.showMessage(mssg,1000)
                        self.aw.qmc.adderror(mssg)
                elif reply == QMessageBox.StandardButton.Cancel:
                    self.status.showMessage(QApplication.translate("StatusBar","Cancelled pid change",None),5000)
                    #put back radio button
                    if N == 1:
                        self.radiosv1.setChecked(True)
                        self.radiopid1.setChecked(True)
                    elif N == 2:
                        self.radiosv2.setChecked(True)
                        self.radiopid2.setChecked(True)
                    elif N == 3:
                        self.radiosv3.setChecked(True)
                        self.radiopid3.setChecked(True)
                    elif N == 4:
                        self.radiosv4.setChecked(True)
                        self.radiopid4.setChecked(True)
                    elif N == 5:
                        self.radiosv5.setChecked(True)
                        self.radiopid5.setChecked(True)
                    elif N == 6:
                        self.radiosv6.setChecked(True)
                        self.radiopid6.setChecked(True)
                    elif N == 7:
                        self.radiosv7.setChecked(True)
                        self.radiopid7.setChecked(True)
                    return
            else:
                mssg = QApplication.translate("StatusBar","PID was already using pid {0}",None).format(str(N))
                self.status.showMessage(mssg,1000)
        else:
            mssg = QApplication.translate("StatusBar","setNpid(): Unable to set pid {0} ",None).format(str(N))
            self.status.showMessage(mssg,1000)
            self.aw.qmc.adderror(mssg)

    @pyqtSlot(bool)
    def setsv1(self,_):
        self.setsv(1)
    @pyqtSlot(bool)
    def setsv2(self,_):
        self.setsv(2)
    @pyqtSlot(bool)
    def setsv3(self,_):
        self.setsv(3)
    @pyqtSlot(bool)
    def setsv4(self,_):
        self.setsv(4)
    @pyqtSlot(bool)
    def setsv5(self,_):
        self.setsv(5)
    @pyqtSlot(bool)
    def setsv6(self,_):
        self.setsv(6)
    @pyqtSlot(bool)
    def setsv7(self,_):
        self.setsv(7)

    #writes new value on sv(i)
    def setsv(self,i):
        if self.aw.ser.controlETpid[0] == 0:
            reg_dict = self.aw.fujipid.PXG4
        else:
            reg_dict = self.aw.fujipid.PXF
        #first get the new sv value from the correspondig edit line
        if i == 1:
            self.sv1edit.setText(self.aw.comma2dot(str(self.sv1edit.text())))
            if self.sv1edit.text() != "":
                newSVvalue = int(float(str(self.sv1edit.text()))*10.) #multiply by 10 because of decimal point. Then convert to int.
        elif i == 2:
            self.sv2edit.setText(self.aw.comma2dot(str(self.sv2edit.text())))
            if self.sv2edit.text() != "":
                newSVvalue = int(float(str(self.sv2edit.text()))*10.)
        elif i == 3:
            self.sv3edit.setText(self.aw.comma2dot(str(self.sv3edit.text())))
            if self.sv3edit.text() != "":
                newSVvalue = int(float(str(self.sv3edit.text()))*10.)
        elif i == 4:
            self.sv4edit.setText(self.aw.comma2dot(str(self.sv4edit.text())))
            if self.sv4edit.text() != "":
                newSVvalue = int(float(str(self.sv4edit.text()))*10.)
        elif i == 5:
            self.sv5edit.setText(self.aw.comma2dot(str(self.sv5edit.text())))
            if self.sv5edit.text() != "":
                newSVvalue = int(float(str(self.sv5edit.text()))*10.)
        elif i == 6:
            self.sv6edit.setText(self.aw.comma2dot(str(self.sv6edit.text())))
            if self.sv6edit.text() != "":
                newSVvalue = int(float(str(self.sv6edit.text()))*10.)
        elif i == 7:
            self.sv7edit.setText(self.aw.comma2dot(str(self.sv7edit.text())))
            if self.sv7edit.text() != "":
                newSVvalue = int(float(str(self.sv7edit.text()))*10.)
        #send command to the right sv
        svkey = "sv"+ str(i)
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(reg_dict[svkey][1],6)
            self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,newSVvalue)
            r = "00000000"
        else:
            command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,reg_dict[svkey][1],newSVvalue)
            r = self.aw.ser.sendFUJIcommand(command,8)
        #verify it went ok
        if len(r) == 8:
            if i == 1:
                self.sv1edit.setText(self.aw.comma2dot(str(self.sv1edit.text())))
                reg_dict[svkey][0] = float(str(self.sv1edit.text()))
                message = QApplication.translate("StatusBar","SV{0} successfully set to {1}",None).format(str(i),str(self.sv1edit.text()))
                self.status.showMessage(message,5000)
                self.setNsv(1)
                self.aw.lcd6.display(str(self.sv1edit.text()))
            elif i == 2:
                self.sv2edit.setText(self.aw.comma2dot(str(self.sv2edit.text())))
                reg_dict[svkey][0] = float(str(self.sv2edit.text()))
                message = QApplication.translate("StatusBar","SV{0} successfully set to {1}",None).format(str(i),str(self.sv2edit.text()))
                self.status.showMessage(message,5000)
                self.setNsv(2)
                self.aw.lcd6.display(str(self.sv2edit.text()))
            elif i == 3:
                self.sv3edit.setText(self.aw.comma2dot(str(self.sv3edit.text())))
                reg_dict[svkey][0] = float(str(self.sv3edit.text()))
                message = QApplication.translate("StatusBar","SV{0} successfully set to {1}",None).format(str(i),str(self.sv3edit.text()))
                self.status.showMessage(message,5000)
                self.setNsv(3)
                self.aw.lcd6.display(str(self.sv3edit.text()))
            elif i == 4:
                self.sv4edit.setText(self.aw.comma2dot(str(self.sv4edit.text())))
                reg_dict[svkey][0] = float(str(self.sv4edit.text()))
                message = QApplication.translate("StatusBar","SV{0} successfully set to {1}",None).format(str(i),str(self.sv4edit.text()))
                self.status.showMessage(message,5000)
                self.setNsv(4)
                self.aw.lcd6.display(str(self.sv4edit.text()))
            elif i == 5:
                self.sv5edit.setText(self.aw.comma2dot(str(self.sv5edit.text())))
                reg_dict[svkey][0] = float(str(self.sv5edit.text()))
                message = QApplication.translate("StatusBar","SV{0} successfully set to {1}",None).format(str(i),str(self.sv5edit.text()))
                self.status.showMessage(message,5000)
                self.setNsv(5)
                self.aw.lcd6.display(str(self.sv5edit.text()))
            elif i == 6:
                self.sv6edit.setText(self.aw.comma2dot(str(self.sv6edit.text())))
                reg_dict[svkey][0] = float(str(self.sv6edit.text()))
                message = QApplication.translate("StatusBar","SV{0} successfully set to {1}",None).format(str(i),str(self.sv6edit.text()))
                self.status.showMessage(message,5000)
                self.setNsv(6)
                self.aw.lcd6.display(str(self.sv6edit.text()))
            elif i == 7:
                self.sv7edit.setText(self.aw.comma2dot(str(self.sv7edit.text())))
                reg_dict[svkey][0] = float(str(self.sv7edit.text()))
                message = QApplication.translate("StatusBar","SV{0} successfully set to {1}",None).format(str(i),str(self.sv7edit.text()))
                self.status.showMessage(message,5000)
                self.setNsv(7)
                self.aw.lcd6.display(str(self.sv7edit.text()))
            #record command as an Event 
            strcommand = "SETSV::" + str("%.1f"%(newSVvalue/10.))
            self.aw.qmc.DeviceEventRecord(strcommand)
        else:
            mssg = QApplication.translate("StatusBar","setsv(): Unable to set SV",None)
            self.status.showMessage(mssg,5000)
            self.aw.qmc.adderror(mssg)

    @pyqtSlot(bool)
    def setpidSlot(self,_):
        widget = self.sender()
        if widget == self.pid1button:
            self.setpid(1)
        elif widget == self.pid2button:
            self.setpid(2)
        elif widget == self.pid3button:
            self.setpid(3)
        elif widget == self.pid4button:
            self.setpid(4)
        elif widget == self.pid5button:
            self.setpid(5)
        elif widget == self.pid6button:
            self.setpid(6)
        elif widget == self.pid7button:
            self.setpid(7)

    #writes new values for p - i - d
    def setpid(self,k):
        if self.aw.ser.controlETpid[0] == 0:
            reg_dict = self.aw.fujipid.PXG4
        else:
            reg_dict = self.aw.fujipid.PXF
        #first get the new sv value from the correspondig edit ine
        if k == 1:
            if self.p1edit.text() != "" and self.i1edit.text() != "" and self.d1edit.text() != "":
                newPvalue = int(float(str(self.p1edit.text().replace(',','.')))*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(str(self.i1edit.text().replace(',','.')))*10.)
                newDvalue = int(float(str(self.d1edit.text().replace(',','.')))*10.)
        elif k == 2:
            if self.p2edit.text() != "" and self.i2edit.text() != "" and self.d2edit.text() != "":
                newPvalue = int(float(str(self.p2edit.text().replace(',','.')))*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(str(self.i2edit.text().replace(',','.')))*10.)
                newDvalue = int(float(str(self.d2edit.text().replace(',','.')))*10.) 
        elif k == 3:
            if self.p3edit.text() != "" and self.i3edit.text() != "" and self.d3edit.text() != "":
                newPvalue = int(float(str(self.p3edit.text().replace(',','.')))*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(str(self.i3edit.text().replace(',','.')))*10.)
                newDvalue = int(float(str(self.d3edit.text().replace(',','.')))*10.)
        elif k == 4:
            if self.p4edit.text() != "" and self.i4edit.text() != "" and self.d4edit.text() != "":
                newPvalue = int(float(str(self.p4edit.text().replace(',','.')))*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(str(self.i4edit.text().replace(',','.')))*10.)
                newDvalue = int(float(str(self.d4edit.text().replace(',','.')))*10.) 
        elif k == 5:
            if self.p5edit.text() != "" and self.i5edit.text() != "" and self.d5edit.text() != "":
                newPvalue = int(float(str(self.p5edit.text().replace(',','.')))*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(str(self.i5edit.text().replace(',','.')))*10.)
                newDvalue = int(float(str(self.d5edit.text().replace(',','.')))*10.) 
        elif k == 6:
            if self.p6edit.text() != "" and self.i6edit.text() != "" and self.d6edit.text() != "":
                newPvalue = int(float(str(self.p6edit.text().replace(',','.')))*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(str(self.i6edit.text().replace(',','.')))*10.)
                newDvalue = int(float(str(self.d6edit.text().replace(',','.')))*10.) 
        elif k == 7:
            if self.p7edit.text() != "" and self.i7edit.text() != "" and self.d7edit.text() != "":
                newPvalue = int(float(str(self.p7edit.text().replace(',','.')))*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(str(self.i7edit.text().replace(',','.')))*10.)
                newDvalue = int(float(str(self.d7edit.text().replace(',','.')))*10.) 
        #send command to the right sv
        pkey = "p" + str(k)
        ikey = "i" + str(k)
        dkey = "d" + str(k)
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(reg_dict[pkey][1],6)
            self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,newPvalue)
            reg = self.aw.modbus.address2register(reg_dict[ikey][1],6)
            self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,newIvalue)
            reg = self.aw.modbus.address2register(reg_dict[dkey][1],6)
            self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,newDvalue)
            p = i = d = "        "
        else:
            commandp = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,reg_dict[pkey][1],newPvalue)
            commandi = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,reg_dict[ikey][1],newIvalue)
            commandd = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,reg_dict[dkey][1],newDvalue)
            p = self.aw.ser.sendFUJIcommand(commandp,8)
            libtime.sleep(0.035) 
            i = self.aw.ser.sendFUJIcommand(commandi,8)
            libtime.sleep(0.035) 
            d = self.aw.ser.sendFUJIcommand(commandd,8)
            libtime.sleep(0.035) 
        #verify it went ok
        if len(p) == 8 and len(i)==8 and len(d) == 8:
            if k == 1:               
                reg_dict[pkey][0] = float(str(self.p1edit.text().replace(',','.')))
                reg_dict[ikey][0] = float(str(self.i1edit.text().replace(',','.')))
                reg_dict[dkey][0] = float(str(self.d1edit.text().replace(',','.')))
                message = (QApplication.translate("StatusBar","pid #{0} successfully set to ({1},{2},{3})",None
                                                   )).format(str(k),str(self.p1edit.text()),str(self.i1edit.text()),str(self.d1edit.text()))
                self.status.showMessage(message,5000)
                self.setNpid(1)
            elif k == 2:
                reg_dict[pkey][0] = float(str(self.p2edit.text().replace(',','.')))
                reg_dict[ikey][0] = float(str(self.i2edit.text().replace(',','.')))
                reg_dict[dkey][0] = float(str(self.d2edit.text().replace(',','.')))
                message = (QApplication.translate("StatusBar","pid #{0} successfully set to ({1},{2},{3})",None
                                                   )).format(str(k),str(self.p2edit.text()),str(self.i2edit.text()),str(self.d2edit.text()))
                self.status.showMessage(message,5000)
                self.setNpid(2)
            elif k == 3:
                reg_dict[pkey][0] = float(str(self.p3edit.text().replace(',','.')))
                reg_dict[ikey][0] = float(str(self.i3edit.text().replace(',','.')))
                reg_dict[dkey][0] = float(str(self.d3edit.text().replace(',','.')))
                message = (QApplication.translate("StatusBar","pid #{0} successfully set to ({1},{2},{3})",None
                                                   )).format(str(k),str(self.p3edit.text()),str(self.i3edit.text()),str(self.d3edit.text()))
                self.status.showMessage(message,5000)
                self.setNpid(3)
            elif k == 4:
                reg_dict[pkey][0] = float(str(self.p4edit.text().replace(',','.')))
                reg_dict[ikey][0] = float(str(self.i4edit.text().replace(',','.')))
                reg_dict[dkey][0] = float(str(self.d4edit.text().replace(',','.')))
                message = (QApplication.translate("StatusBar","pid #{0} successfully set to ({1},{2},{3})",None
                                                   )).format(str(k),str(self.p4edit.text()),str(self.i4edit.text()),str(self.d4edit.text()))
                self.status.showMessage(message,5000)
                self.setNpid(4)
            elif k == 5:
                reg_dict[pkey][0] = float(str(self.p5edit.text().replace(',','.')))
                reg_dict[ikey][0] = float(str(self.i5edit.text().replace(',','.')))
                reg_dict[dkey][0] = float(str(self.d5edit.text().replace(',','.')))
                message = (QApplication.translate("StatusBar","pid #{0} successfully set to ({1},{2},{3})",None
                                                   )).format(str(k),str(self.p5edit.text()),str(self.i5edit.text()),str(self.d5edit.text()))
                self.status.showMessage(message,5000)
                self.setNpid(5)
            elif k == 6:
                reg_dict[pkey][0] = float(str(self.p6edit.text().replace(',','.')))
                reg_dict[ikey][0] = float(str(self.i6edit.text().replace(',','.')))
                reg_dict[dkey][0] = float(str(self.d6edit.text().replace(',','.')))
                message = (QApplication.translate("StatusBar","pid #{0} successfully set to ({1},{2},{3})",None
                                                   )).format(str(k),str(self.p6edit.text()),str(self.i6edit.text()),str(self.d6edit.text()))
                self.status.showMessage(message,5000)
                self.setNpid(6)
            elif k == 7:
                reg_dict[pkey][0] = float(str(self.p7edit.text().replace(',','.')))
                reg_dict[ikey][0] = float(str(self.i7edit.text().replace(',','.')))
                reg_dict[dkey][0] = float(str(self.d7edit.text().replace(',','.')))
                message = (QApplication.translate("StatusBar","pid #{0} successfully set to ({1},{2},{3})",None
                                                   )).format(str(k),str(self.p7edit.text()),str(self.i7edit.text()),str(self.d7edit.text()))
                self.status.showMessage(message,5000)
                self.setNpid(7) 
        else:
            lp = len(p)
            li = len(i)
            ld = len(d)
            mssg = QApplication.translate("StatusBar","pid command failed. Bad data at pid{0} (8,8,8): ({1},{2},{3}) ",None
                                                   ).format(str(k),str(lp),str(li),str(ld))
            self.status.showMessage(mssg,5000)
            self.aw.qmc.adderror(mssg)
    
    @pyqtSlot(bool)
    def getallpid(self,_):
        if self.aw.ser.controlETpid[0] == 0:
            reg_dict = self.aw.fujipid.PXG4
        else:
            reg_dict = self.aw.fujipid.PXF
        for k in range(1,8):
            pkey = "p" + str(k)
            ikey = "i" + str(k)
            dkey = "d" + str(k)
            msg = QApplication.translate("StatusBar","sending commands for p{0} i{1} d{2}",None).format(str(k),str(k),str(k))
            self.status.showMessage(msg,1000)
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(reg_dict[pkey][1],3)
                p = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)/10.
            else:
                commandp = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,reg_dict[pkey][1],1)
                p = self.aw.fujipid.readoneword(commandp)/10.
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(reg_dict[ikey][1],3)
                i = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)/10.
            else:
                commandi = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,reg_dict[ikey][1],1)
                i = self.aw.fujipid.readoneword(commandi)/10.
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(reg_dict[dkey][1],3)
                dd = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)/10.
            else:
                commandd = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,reg_dict[dkey][1],1)
                dd = self.aw.fujipid.readoneword(commandd)/10.
            p = float(p)
            i = float(i)
            dd = float(dd)
            if p != -1 and i != -1 and dd != -1:
                reg_dict[pkey][0] = p
                reg_dict[ikey][0] = i
                reg_dict[dkey][0] = dd
                if k == 1:
                    self.p1edit.setText(str(p))
                    self.i1edit.setText(str(i))
                    self.d1edit.setText(str(dd))
                    mssg = pkey + "=" + str(p) + " " + ikey + "=" + str(i) + " " + dkey + "=" + str(dd) # No translation needed here
                    self.status.showMessage(mssg,1000)
                if k == 2:
                    self.p2edit.setText(str(p))
                    self.i2edit.setText(str(i))
                    self.d2edit.setText(str(dd))
                    mssg = pkey + "=" + str(p) + " " + ikey + "=" + str(i) + " " + dkey + "=" + str(dd)
                    self.status.showMessage(mssg,1000)
                elif k == 3:
                    self.p3edit.setText(str(p))
                    self.i3edit.setText(str(i))
                    self.d3edit.setText(str(dd))
                    mssg = pkey + "=" + str(p) + " " + ikey + "=" + str(i) + " " + dkey + "=" + str(dd)
                    self.status.showMessage(mssg,1000)
                elif k == 4:
                    self.p4edit.setText(str(p))
                    self.i4edit.setText(str(i))
                    self.d4edit.setText(str(dd))
                    mssg = pkey + "=" + str(p) + " " + ikey + "=" + str(i) + " " + dkey + "=" + str(dd)
                    self.status.showMessage(mssg,1000)
                elif k == 5:
                    self.p5edit.setText(str(p))
                    self.i5edit.setText(str(i))
                    self.d5edit.setText(str(dd))
                    mssg = pkey + "=" + str(p) + " " + ikey + "=" + str(i) + " " + dkey + "=" + str(dd)
                    self.status.showMessage(mssg,1000)
                elif k == 6:
                    self.p6edit.setText(str(p))
                    self.i6edit.setText(str(i))
                    self.d6edit.setText(str(dd))
                    mssg = pkey + "=" + str(p) + " " + ikey + "=" + str(i) + " " + dkey + "=" + str(dd)
                    self.status.showMessage(mssg,1000)
                elif k == 7:
                    self.p7edit.setText(str(p))
                    self.i7edit.setText(str(i))
                    self.d7edit.setText(str(dd))
                    mssg = pkey + "=" + str(p) + " " + ikey + "=" + str(i) + " " + dkey + "=" + str(dd)
                    self.status.showMessage(mssg,1000)
            else:
                mssg = QApplication.translate("StatusBar","getallpid(): Unable to read pid values",None)
                self.status.showMessage(mssg,5000)
                self.aw.qmc.adderror(mssg)
                return
        #read current pidN
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(reg_dict["selectedpid"][1],3)
            N = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
        else:
            command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,reg_dict["selectedpid"][1],1)
            N = self.aw.fujipid.readoneword(command)
        libtime.sleep(0.035) 
        if N != -1:
            self.aw.fujipid.PXG4["selectedpid"][0] = N
            if N == 1:
                self.radiopid1.setChecked(True)
            elif N == 2:
                self.radiopid2.setChecked(True)
            elif N == 3:
                self.radiopid3.setChecked(True)
            elif N == 4:
                self.radiopid4.setChecked(True)
            elif N == 5:
                self.radiopid5.setChecked(True)
            elif N == 6:
                self.radiopid6.setChecked(True)
            elif N == 7:
                self.radiopid7.setChecked(True)
            mssg = QApplication.translate("StatusBar","PID is using pid = {0}",None).format(str(N))
            self.status.showMessage(mssg,5000)
        else:
            mssg = QApplication.translate("StatusBar","getallpid(): Unable to read current sv",None)
            self.status.showMessage(mssg,5000)
            self.aw.qmc.adderror(mssg)

    @pyqtSlot(bool)
    def getallsv(self,_):
        if self.aw.ser.controlETpid[0] == 0:
            reg_dict = self.aw.fujipid.PXG4
        else:
            reg_dict = self.aw.fujipid.PXF
        for i in reversed(list(range(1,8))):
            svkey = "sv" + str(i)
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(reg_dict[svkey][1],3)
                sv = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)/10.
            else:
                command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,reg_dict[svkey][1],1)
                sv = self.aw.fujipid.readoneword(command)/10.
            self.aw.fujipid.PXG4[svkey][0] = sv
            if i == 1:
                self.sv1edit.setText(str(sv))
                mssg = svkey + " = " + str(sv)
                self.status.showMessage(mssg,1000)
            elif i == 2:
                self.sv2edit.setText(str(sv))
                mssg = svkey + " = " + str(sv)
                self.status.showMessage(mssg,1000)
            elif i == 3:
                mssg = svkey + " = " + str(sv)
                self.status.showMessage(mssg,1000)
                self.sv3edit.setText(str(sv))
            elif i == 4:
                mssg = svkey + " = " + str(sv)
                self.status.showMessage(mssg,1000)
                self.sv4edit.setText(str(sv))
            elif i == 5:
                mssg = svkey + " = " + str(sv)
                self.status.showMessage(mssg,1000)
                self.sv5edit.setText(str(sv))
            elif i == 6:
                mssg = svkey + " = " + str(sv)
                self.status.showMessage(mssg,1000)
                self.sv6edit.setText(str(sv))
            elif i == 7:
                mssg = svkey + " = " + str(sv)
                self.status.showMessage(mssg,1000)
                self.sv7edit.setText(str(sv))
        #read current svN
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(reg_dict["selectsv"][1],3)
            N = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
        else:
            command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,reg_dict["selectsv"][1],1)
            N = self.aw.fujipid.readoneword(command)
        if N > 0:
            reg_dict["selectsv"][0] = N
        if N == 1:
            self.radiosv1.setChecked(True)
        elif N == 2:
            self.radiosv2.setChecked(True)
        elif N == 3:
            self.radiosv3.setChecked(True)
        elif N == 4:
            self.radiosv4.setChecked(True)
        elif N == 5:
            self.radiosv5.setChecked(True)
        elif N == 6:
            self.radiosv6.setChecked(True)
        elif N == 7:
            self.radiosv7.setChecked(True)
        mssg = QApplication.translate("StatusBar","PID is using SV = {0}",None).format(str(N))
        self.status.showMessage(mssg,5000)

    def checkrampsoakmode(self):
        currentmode = self.aw.fujipid.getCurrentRampSoakMode()
        if currentmode == 0:
            mode = ["0",
                    QApplication.translate("Message","OFF",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","OFF",None)]
        elif currentmode == 1:
            mode = ["1",
                    QApplication.translate("Message","OFF",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","ON",None)]
        elif currentmode == 2:
            mode = ["2",
                    QApplication.translate("Message","OFF",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","OFF",None)]
        elif currentmode == 3:
            mode = ["3",
                    QApplication.translate("Message","OFF",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","ON",None)]
        elif currentmode == 4:
            mode = ["4",
                    QApplication.translate("Message","OFF",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","OFF",None)]
        elif currentmode == 5:
            mode = ["5",
                    QApplication.translate("Message","OFF",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","ON",None)]
        elif currentmode == 6:
            mode = ["6",
                    QApplication.translate("Message","OFF",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","OFF",None)]
        elif currentmode == 7:
            mode = ["7",
                    QApplication.translate("Message","OFF",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","ON",None)]
        elif currentmode == 8:
            mode = ["8",
                    QApplication.translate("Message","ON",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","OFF",None)]
        elif currentmode == 9:
            mode = ["9",
                    QApplication.translate("Message","ON",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","ON",None)]
        elif currentmode == 10:
            mode = ["10",
                    QApplication.translate("Message","ON",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","OFF",None)]
        elif currentmode == 11:
            mode = ["11",
                    QApplication.translate("Message","ON",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","ON",None)]
        elif currentmode == 12:
            mode = ["12",
                    QApplication.translate("Message","ON",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","OFF",None)]
        elif currentmode == 13:
            mode = ["13",
                    QApplication.translate("Message","ON",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","CONTINUOUS CONTROL",None),
                    QApplication.translate("Message","ON",None)]
        elif currentmode == 14:
            mode = ["14",
                    QApplication.translate("Message","ON",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","OFF",None)]
        elif currentmode == 15:
            mode = ["15",
                    QApplication.translate("Message","ON",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","STANDBY MODE",None),
                    QApplication.translate("Message","ON",None)]
        else:
            return -1
        string = "The rampsoak-mode tells how to start and end the ramp/soak\n\n"
        string += "Your rampsoak mode in this pid is:\n"
        string += "\nMode = " + mode[0]
        string += "\n-----------------------------------------------------------------------"
        string += "\nStart to run from PV value: " + mode[1]
        string += "\nEnd output status at the end of ramp/soak: " + mode[2]
        string += "\nOutput status while ramp/soak opearion set to OFF: " + mode[3] 
        string += "\nRepeat Operation at the end: " + mode[4]
        string += "\n-----------------------------------------------------------------------"
        string += "\n\nRecomended Mode = 0\n"
        string += "\nIf you need to change it, change it now and come back later"
        string += "\nUse the Parameter Loader Software by Fuji if you need to\n\n"
        string += "\n\n\nContinue?" 
        reply = QMessageBox.question(self.aw,QApplication.translate("Message","Ramp Soak start-end mode",None),string,
                            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Yes:
            return 1
        return 0

    @pyqtSlot(bool)
    def setONrampsoak(self,_):
        self.setONOFFrampsoak(1)
    
    @pyqtSlot(bool)
    def setOFFrampsoak(self,_):
        self.setONOFFrampsoak(0)
    
    def setONOFFrampsoak(self,flag):
        #warning check how it ends at "rampsoakend":[0,41081] can let pid inop till value changed    UNFINISHED
        # you can come out of this mode by putting the pid in standby (pid off) 
        #flag =0 OFF, flag = 1 ON, flag = 2 hold        
        #set rampsoak pattern ON
        if flag == 1:
            check = self.checkrampsoakmode()
            if check == 0:
                self.status.showMessage(QApplication.translate("StatusBar","Ramp/Soak operation cancelled",None), 5000)
                return
            if check == -1:
                self.status.showMessage(QApplication.translate("StatusBar","No RX data",None), 5000)
            self.status.showMessage(QApplication.translate("StatusBar","RS ON",None),500)
            selectedmode = self.patternComboBox.currentIndex()
            currentmode = self.aw.fujipid.getrampsoakmode()
            if currentmode != selectedmode:
                #set mode in pid to match the mode selected in the combobox
                self.status.showMessage(QApplication.translate("StatusBar","Need to change pattern mode...",None),1000)
                res = self.aw.fujipid.setrampsoakmode(selectedmode)
                if res:
                    self.status.showMessage(QApplication.translate("StatusBar","Pattern has been changed. Wait 5 secs.",None), 500)
                else:
                    self.status.showMessage(QApplication.translate("StatusBar","Pattern could not be changed",None), 5000)
                    return
            #combobox mode matches pid mode
            #set ramp soak mode ON/OFF
            res = self.aw.fujipid.setrampsoak(flag)
            if res:
                #record command as an Event if flag = 1
                self.status.showMessage(QApplication.translate("StatusBar","RS ON",None), 5000)
                pattern =[[1,4],[5,8],[1,8],[9,12],[13,16],[9,16],[1,16]]
                if self.aw.ser.controlETpid[0] == 0: #Fuji PXG
                    reg_dict = self.aw.fujipid.PXG4
                elif self.aw.ser.controlETpid[0] == 4: #Fuji PXF
                    reg_dict = self.aw.fujipid.PXF
                start = pattern[reg_dict["rampsoakpattern"][0]][0]
                end = pattern[reg_dict["rampsoakpattern"][0]][1]+1
                strcommand = "SETRS"
                result = ""
                for i in range(start,end):
                    svkey = "segment"+str(i)+"sv"
                    rampkey = "segment"+str(i)+"ramp"
                    soakkey = "segment"+str(i)+"soak"
                    strcommand += "::" + str(reg_dict[svkey][0]) + "::" + str(reg_dict[rampkey][0]) + "::" + str(reg_dict[soakkey][0])+"::"
                    result += strcommand
                    strcommand = "SETRS"
                result = result.strip(":")
                self.aw.qmc.DeviceEventRecord(result)
            else:
                self.status.showMessage(QApplication.translate("StatusBar","RampSoak could not be changed",None), 5000)
        #set ramp soak OFF
        elif flag == 0:
            self.status.showMessage(QApplication.translate("StatusBar","RS OFF",None),500)
            self.aw.fujipid.setrampsoak(flag)

    def setpattern(self):
        #Need to make sure that RampSoak is not ON in order to change pattern:
        onoff = self.getONOFFrampsoak()
        if onoff == 0:
            self.aw.fujipid.PXG4["rampsoakpattern"][0] = self.patternComboBox.currentIndex()
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXG4["rampsoakpattern"][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,self.aw.fujipid.PXG4["rampsoakpattern"][0])
                r = command = ""
            else:
                command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXG4["rampsoakpattern"][1],self.aw.fujipid.PXG4["rampsoakpattern"][0])
                #TX and RX
                r = self.aw.ser.sendFUJIcommand(command,8)
            #check response from pid and update message on main window
            if r == command:
                patterns = ["1-4","5-8","1-8","9-12","13-16","9-16","1-16"]
                message = QApplication.translate("Message","Pattern changed to {0}", None).format(patterns[self.aw.fujipid.PXG4["rampsoakpattern"][0]])
            else:
                message = QApplication.translate("Message","Pattern did not changed",None)
            self.aw.sendmessage(message)
        elif onoff == 1:
            self.aw.sendmessage(QApplication.translate("Message","Ramp/Soak was found ON! Turn it off before changing the pattern", None))
        elif onoff == 2:
            self.aw.sendmessage(QApplication.translate("Message","Ramp/Soak was found in Hold! Turn it off before changing the pattern", None))

    @pyqtSlot(bool)
    def setONstandby(self,_):
        self.setONOFFstandby(1)
    
    @pyqtSlot(bool)
    def setOFFstandby(self,_):
        self.setONOFFstandby(0)
    
    def setONOFFstandby(self,flag):
        try:
            #standby ON (pid off) will reset: rampsoak modes/autotuning/self tuning
            #flag = 0 standby OFF, flag = 1 standby ON (pid off)
            self.status.showMessage(QApplication.translate("StatusBar","wait...",None),500)
            res = self.aw.fujipid.setONOFFstandby(flag)
            if res:
                if flag == 1:
                    message = QApplication.translate("StatusBar","PID set to OFF",None)     #put pid in standby 1 (pid on)
                else:
                    message = QApplication.translate("StatusBar","PID set to ON",None)      #put pid in standby 0 (pid off)
                self.status.showMessage(message,5000)
            else:
                message = QApplication.translate("StatusBar","Unable",None)
                self.status.showMessage(QApplication.translate("StatusBar","No data received",None),5000)
        except Exception as e: # pylint: disable=broad-except
            #import traceback
            #traceback.print_exc(file=sys.stdout)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " setONOFFstandby() {0}").format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    #get all Ramp Soak values for all 8 segments
    @pyqtSlot(bool)
    def getallsegments(self,_):
        for i in range(1,17):
            msg = QApplication.translate("StatusBar","Reading Ramp/Soak {0} ...",None).format(str(i))
            self.status.showMessage(msg,500)
            k = self.aw.fujipid.getsegment(i)
            libtime.sleep(0.035)
            if k == -1:
                self.status.showMessage(QApplication.translate("StatusBar","problem reading Ramp/Soak",None),5000)
                return
            self.paintlabels()
        self.status.showMessage(QApplication.translate("StatusBar","Finished reading Ramp/Soak val.",None),5000)
        self.createsegmenttable()

    @pyqtSlot(bool)
    def setONautotune(self,_):
        self.setONOFFautotune(1)
        
    @pyqtSlot(bool)
    def setOFFautotune(self,_):
        self.setONOFFautotune(0)

    def setONOFFautotune(self,flag):
        if self.aw.ser.controlETpid[0] == 0:
            reg_dict = self.aw.fujipid.PXG4
        else:
            reg_dict = self.aw.fujipid.PXF
        self.status.showMessage(QApplication.translate("StatusBar","setting autotune...",None),500)
        #read current pidN
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(reg_dict["selectedpid"][1],3)
            N = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
        else:
            command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,reg_dict["selectedpid"][1],1)
            N = self.aw.fujipid.readoneword(command)
        reg_dict["selectedpid"][0] = N
        string = QApplication.translate("StatusBar","Current pid = {0}. Proceed with autotune command?",None).format(str(N))
        reply = QMessageBox.question(self.aw,QApplication.translate("Message","Ramp Soak start-end mode",None),string,
                            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Cancel:
            self.status.showMessage(QApplication.translate("StatusBar","Autotune cancelled",None),5000)
            return
        if reply == QMessageBox.StandardButton.Yes:
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(reg_dict["autotuning"][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,flag)
                r = "00000000"
            else:
                command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,reg_dict["autotuning"][1],flag)
                #TX and RX
                r = self.aw.ser.sendFUJIcommand(command,8)
            if len(r) == 8:
                if flag == 0:
                    reg_dict["autotuning"][0] = 0
                    self.status.showMessage(QApplication.translate("StatusBar","Autotune successfully turned OFF",None),5000)
                if flag == 1:
                    reg_dict["autotuning"][0] = 1
                    self.status.showMessage(QApplication.translate("StatusBar","Autotune successfully turned ON",None),5000) 
            else:
                self.status.showMessage(QApplication.translate("StatusBar","UNABLE to set Autotune",None),5000) 
    
    @pyqtSlot(bool)
    def accept(self,_):
        # store set values
        self.aw.fujipid.PXG4["sv1"][0] = float(self.aw.comma2dot(self.sv1edit.text()))
        self.aw.fujipid.PXG4["sv2"][0] = float(self.aw.comma2dot(self.sv2edit.text()))
        self.aw.fujipid.PXG4["sv3"][0] = float(self.aw.comma2dot(self.sv3edit.text()))
        self.aw.fujipid.PXG4["sv4"][0] = float(self.aw.comma2dot(self.sv4edit.text()))
        self.aw.fujipid.PXG4["sv5"][0] = float(self.aw.comma2dot(self.sv5edit.text()))
        self.aw.fujipid.PXG4["sv6"][0] = float(self.aw.comma2dot(self.sv6edit.text()))
        self.aw.fujipid.PXG4["sv7"][0] = float(self.aw.comma2dot(self.sv7edit.text()))
        # store set values
        self.aw.fujipid.PXG4["p1"][0] = float(self.p1edit.text())
        self.aw.fujipid.PXG4["p2"][0] = float(self.p2edit.text())
        self.aw.fujipid.PXG4["p3"][0] = float(self.p3edit.text())
        self.aw.fujipid.PXG4["p4"][0] = float(self.p4edit.text())
        self.aw.fujipid.PXG4["p5"][0] = float(self.p5edit.text())
        self.aw.fujipid.PXG4["p6"][0] = float(self.p6edit.text())
        self.aw.fujipid.PXG4["p7"][0] = float(self.p7edit.text())
        self.aw.fujipid.PXG4["i1"][0] = float(self.i1edit.text())
        self.aw.fujipid.PXG4["i2"][0] = float(self.i2edit.text())
        self.aw.fujipid.PXG4["i3"][0] = float(self.i3edit.text())
        self.aw.fujipid.PXG4["i4"][0] = float(self.i4edit.text())
        self.aw.fujipid.PXG4["i5"][0] = float(self.i5edit.text())
        self.aw.fujipid.PXG4["i6"][0] = float(self.i6edit.text())
        self.aw.fujipid.PXG4["i7"][0] = float(self.i7edit.text())
        self.aw.fujipid.PXG4["d1"][0] = float(self.d1edit.text())
        self.aw.fujipid.PXG4["d2"][0] = float(self.d2edit.text())
        self.aw.fujipid.PXG4["d3"][0] = float(self.d3edit.text())
        self.aw.fujipid.PXG4["d4"][0] = float(self.d4edit.text())
        self.aw.fujipid.PXG4["d5"][0] = float(self.d5edit.text())
        self.aw.fujipid.PXG4["d6"][0] = float(self.d6edit.text())
        self.aw.fujipid.PXG4["d7"][0] = float(self.d7edit.text())
        # store segment table
        for i in range(16):
            svkey = "segment" + str(i+1) + "sv"
            rampkey = "segment" + str(i+1) + "ramp"
            soakkey = "segment" + str(i+1) + "soak"
            self.aw.fujipid.PXG4[svkey][0] = float(self.segmenttable.cellWidget(i,0).text())
            self.aw.fujipid.PXG4[rampkey][0] = stringtoseconds(self.segmenttable.cellWidget(i,1).text())
            self.aw.fujipid.PXG4[soakkey][0] = stringtoseconds(self.segmenttable.cellWidget(i,2).text())
        # SV slider
        self.aw.pidcontrol.svSliderMin = min(self.pidSVSliderMin.value(),self.pidSVSliderMax.value())
        self.aw.pidcontrol.svSliderMax = max(self.pidSVSliderMin.value(),self.pidSVSliderMax.value())
        self.close()

    def createsegmenttable(self):
        self.segmenttable.setRowCount(16)
        self.segmenttable.setColumnCount(4)
        self.segmenttable.setHorizontalHeaderLabels([QApplication.translate("StatusBar","SV",None),
                                                     QApplication.translate("StatusBar","Ramp (MM:SS)",None),
                                                     QApplication.translate("StatusBar","Soak (MM:SS)",None),""])
        self.segmenttable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.segmenttable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.segmenttable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.segmenttable.setShowGrid(True)
        self.segmenttable.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        regextime = QRegularExpression(r"^-?[0-9]?[0-9]?[0-9]:[0-5][0-9]$")
        #populate table
        for i in range(16):
            #create widgets
            svkey = "segment" + str(i+1) + "sv"
            rampkey = "segment" + str(i+1) + "ramp"
            soakkey = "segment" + str(i+1) + "soak"
            svedit = QLineEdit(str(self.aw.fujipid.PXG4[svkey][0]))
            svedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, svedit))
            rampedit = QLineEdit(stringfromseconds(self.aw.fujipid.PXG4[rampkey][0]))
            rampedit.setValidator(QRegularExpressionValidator(regextime,self))
            soakedit  = QLineEdit(stringfromseconds(self.aw.fujipid.PXG4[soakkey][0]))
            soakedit.setValidator(QRegularExpressionValidator(regextime,self))
            setButton = QPushButton(QApplication.translate("Button","Set",None))
            setButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            setButton.clicked.connect(self.setsegment)
            #add widgets to the table
            self.segmenttable.setCellWidget(i,0,svedit)
            self.segmenttable.setCellWidget(i,1,rampedit)
            self.segmenttable.setCellWidget(i,2,soakedit)
            self.segmenttable.setCellWidget(i,3,setButton)

    #idn = id number, sv = float set value, ramp = ramp value, soak = soak value
    @pyqtSlot(bool)
    def setsegment(self,_):
        i = self.aw.findWidgetsRow(self.segmenttable,self.sender(),3)
        idn = i+1
        svedit =  self.segmenttable.cellWidget(i,0)
        rampedit = self.segmenttable.cellWidget(i,1)
        soakedit = self.segmenttable.cellWidget(i,2)
        sv = float(self.aw.comma2dot(str(svedit.text())))
        ramp = stringtoseconds(str(rampedit.text()))
        soak = stringtoseconds(str(soakedit.text()))
        svkey = "segment" + str(idn) + "sv"
        rampkey = "segment" + str(idn) + "ramp"
        soakkey = "segment" + str(idn) + "soak"
        if self.aw.ser.controlETpid[0] == 0: # PXG
            reg_dict = self.aw.fujipid.PXG4
        else: # PXF
            reg_dict = self.aw.fujipid.PXF
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(reg_dict[svkey][1],6)
            self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,int(sv*10))
            libtime.sleep(0.1) #important time between writings
            reg = self.aw.modbus.address2register(reg_dict[rampkey][1],6)
            self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,ramp)
            libtime.sleep(0.1) #important time between writings
            reg = self.aw.modbus.address2register(reg_dict[soakkey][1],6)
            self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,soak)
            r1 = r2 = r3 = "        "
        else:
            svcommand = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,reg_dict[svkey][1],int(sv*10))
            r1 = self.aw.ser.sendFUJIcommand(svcommand,8)
            libtime.sleep(0.1) #important time between writings
            rampcommand = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,reg_dict[rampkey][1],ramp)
            r2 = self.aw.ser.sendFUJIcommand(rampcommand,8)
            libtime.sleep(0.1) #important time between writings
            soakcommand = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,reg_dict[soakkey][1],soak)
            r3 = self.aw.ser.sendFUJIcommand(soakcommand,8)
        #check if OK
        if len(r1) == 8 and len(r2) == 8 and len(r3) == 8:
            self.aw.fujipid.PXG4[svkey][0] = sv
            self.aw.fujipid.PXG4[rampkey][0] = ramp
            self.aw.fujipid.PXG4[soakkey][0] = soak
            self.paintlabels()
            self.status.showMessage(QApplication.translate("StatusBar","Ramp/Soak successfully written",None),5000) 
        else:
            self.aw.qmc.adderror(QApplication.translate("Error Message","Segment values could not be written into PID",None))
            

############################################################################
######################## DTA PID CONTROL DIALOG ############################
############################################################################

class DTApidDlgControl(ArtisanDialog):
    def __init__(self, parent = None, aw = None):
        super().__init__(parent, aw)
        self.setModal(True)
        #self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose) # default is to set to True, which is already set in ArtisanDialog
        self.setWindowTitle(QApplication.translate("Form Caption","Delta DTA PID Control",None))
        self.status = QStatusBar()
        self.status.setSizeGripEnabled(False)
        self.status.showMessage(QApplication.translate("StatusBar","Work in Progress",None),5000)
        svlabel = QLabel(QApplication.translate("Label", "SV", None))
        self.svedit = QLineEdit(str(self.aw.dtapid.dtamem["sv"][0]))
        self.svedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999.,1, self.svedit))
        readsvbutton = QPushButton(QApplication.translate("Button","Read", None))
        writesvbutton = QPushButton(QApplication.translate("Button","Write", None))
        readsvbutton.clicked.connect(self.readsv)
        writesvbutton.clicked.connect(self.writesv)
        tab1Layout = QGridLayout()
        tab1Layout.addWidget(svlabel,0,0)
        tab1Layout.addWidget(self.svedit,0,1)
        tab1Layout.addWidget(readsvbutton,0,2)
        tab1Layout.addWidget(writesvbutton,0,3)
        ############################
        TabWidget = QTabWidget()
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        TabWidget.addTab(C1Widget,QApplication.translate("Tab","General",None))
        mainlayout = QVBoxLayout()
        mainlayout.addWidget(self.status,0)
        mainlayout.addWidget(TabWidget,1)
        self.setLayout(mainlayout)

    @pyqtSlot(bool)
    def readsv(self,_):
        ### create command message2send(unitID,function,address,ndata)
        command = self.aw.dtapid.message2send(self.aw.ser.controlETpid[1],3,self.aw.dtapid.dtamem["sv"][1],1)
        #read sv
        sv = self.aw.ser.sendDTAcommand(command)
        #update SV value 
        self.aw.dtapid.dtamem["sv"][0] = sv
        #update svedit
        self.svedit.setText(str(sv)) 
        #update sv LCD
        self.aw.lcd6.display(sv)
        #update status
        message = QApplication.translate("StatusBar","SV = %s"%(str(sv)),None)
        self.status.showMessage(message,5000)

    #write uses function = 6
    @pyqtSlot(bool)
    def writesv(self,_):
        v = self.aw.comma2dot(self.svedit.text())
        if v:
            newsv = hex(int(abs(float(str(v)))*10.))[2:].upper()
            ### create command message2send(unitID,function,address,ndata)
            command = self.aw.dtapid.message2send(self.aw.ser.controlETpid[1],6,self.aw.dtapid.dtamem["sv"][1],newsv)
                #read sv
        self.aw.ser.sendDTAcommand(command)