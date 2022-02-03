# -*- coding: utf-8 -*-
#
# ABOUT
# Artisan Phases Dialog

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

from artisanlib.dialogs import ArtisanDialog

try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtCore import Qt, pyqtSlot, QSettings # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QLabel, QDialogButtonBox, QGridLayout, # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QLayout, QSpinBox) # @UnusedImport @Reimport  @UnresolvedImport
except Exception:
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import Qt, pyqtSlot, QSettings # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QLabel, QDialogButtonBox, QGridLayout, # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QLayout, QSpinBox) # @UnusedImport @Reimport  @UnresolvedImport

class phasesGraphDlg(ArtisanDialog):
    def __init__(self, parent = None, aw = None):
        super().__init__(parent, aw)
        self.setWindowTitle(QApplication.translate("Form Caption","Roast Phases"))
        self.setModal(True)
        # remember initial values for Cancel action
        self.phases = list(self.aw.qmc.phases)
        self.org_phasesbuttonflag = bool(self.aw.qmc.phasesbuttonflag)
        self.org_fromBackgroundflag = bool(self.aw.qmc.phasesfromBackgroundflag)
        self.org_watermarksflag = bool(self.aw.qmc.watermarksflag)
        self.org_phasesLCDflag = bool(self.aw.qmc.phasesLCDflag)
        self.org_autoDRYflag = bool(self.aw.qmc.autoDRYflag)
        self.org_autoFCsFlag = bool(self.aw.qmc.autoFCsFlag)
        self.org_phasesLCDmode_l = list(self.aw.qmc.phasesLCDmode_l)
        self.org_phasesLCDmode_all = list(self.aw.qmc.phasesLCDmode_all)
        #
        dryLabel = QLabel(QApplication.translate("Label", "Drying"))
        midLabel = QLabel(QApplication.translate("Label", "Maillard"))
        finishLabel = QLabel(QApplication.translate("Label", "Finishing"))
        minf = QLabel(QApplication.translate("Label", "min","abbrev of minimum"))
        maxf = QLabel(QApplication.translate("Label", "max"))
        self.startdry = QSpinBox()
        self.startdry.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.startdry.setMinimumWidth(80)
        self.enddry = QSpinBox()
        self.enddry.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.enddry.setMinimumWidth(80)
        self.startmid = QSpinBox()
        self.startmid.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.startmid.setMinimumWidth(80)
        self.endmid = QSpinBox()
        self.endmid.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.endmid.setMinimumWidth(80)
        self.startfinish = QSpinBox()
        self.startfinish.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.startfinish.setMinimumWidth(80)
        self.endfinish = QSpinBox()
        self.endfinish.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.endfinish.setMinimumWidth(80) 
        if self.aw.qmc.mode == "F":
            self.startdry.setSuffix(" F")
            self.enddry.setSuffix(" F")
            self.startmid.setSuffix(" F")
            self.endmid.setSuffix(" F")
            self.startfinish.setSuffix(" F")
            self.endfinish.setSuffix(" F")
        elif self.aw.qmc.mode == "C":
            self.startdry.setSuffix(" C")
            self.enddry.setSuffix(" C")
            self.startmid.setSuffix(" C")
            self.endmid.setSuffix(" C")
            self.startfinish.setSuffix(" C")
            self.endfinish.setSuffix(" C")
        self.startdry.setRange(0,1000)    #(min,max)
        self.enddry.setRange(0,1000)
        self.startmid.setRange(0,1000)
        self.endmid.setRange(0,1000)
        self.startfinish.setRange(0,1000)
        self.endfinish.setRange(0,1000)
        self.enddry.valueChanged.connect(self.startmid.setValue)
        self.startmid.valueChanged.connect(self.enddry.setValue)
        self.endmid.valueChanged.connect(self.startfinish.setValue)
        self.startfinish.valueChanged.connect(self.endmid.setValue)
        self.pushbuttonflag = QCheckBox(QApplication.translate("CheckBox","Auto Adjusted"))
        self.pushbuttonflag.setChecked(bool(self.aw.qmc.phasesbuttonflag))
        self.pushbuttonflag.stateChanged.connect(self.pushbuttonflagChanged)
        self.fromBackgroundflag = QCheckBox(QApplication.translate("CheckBox","From Background"))
        self.fromBackgroundflag.setChecked(bool(self.aw.qmc.phasesfromBackgroundflag))
        self.fromBackgroundflag.stateChanged.connect(self.fromBackgroundflagChanged)
        self.watermarksflag = QCheckBox(QApplication.translate("CheckBox","Watermarks"))
        self.watermarksflag.setChecked(bool(self.aw.qmc.watermarksflag))
        self.phasesLCDflag = QCheckBox(QApplication.translate("CheckBox","Phases LCDs"))
        self.phasesLCDflag.setChecked(bool(self.aw.qmc.phasesLCDflag))
        self.autoDRYflag = QCheckBox(QApplication.translate("CheckBox","Auto DRY"))
        self.autoDRYflag.setChecked(bool(self.aw.qmc.autoDRYflag))
        self.autoFCsFlag = QCheckBox(QApplication.translate("CheckBox","Auto FCs"))
        self.autoFCsFlag.setChecked(bool(self.aw.qmc.autoFCsFlag))
        self.watermarksflag.stateChanged.connect(self.watermarksflagChanged)
        self.phasesLCDflag.stateChanged.connect(self.phasesLCDsflagChanged)
        self.autoDRYflag.stateChanged.connect(self.autoDRYflagChanged)
        self.autoFCsFlag.stateChanged.connect(self.autoFCsFlagChanged)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.updatephases)
        self.dialogbuttons.rejected.connect(self.cancel)
        setDefaultButton = self.dialogbuttons.addButton(QDialogButtonBox.StandardButton.RestoreDefaults)
        setDefaultButton.clicked.connect(self.setdefault)
        self.setButtonTranslations(setDefaultButton,"Restore Defaults",QApplication.translate("Button","Restore Defaults"))
        
        phaseLayout = QGridLayout()
        phaseLayout.addWidget(minf,0,1,Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignBottom)
        phaseLayout.addWidget(maxf,0,2,Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignBottom)
        phaseLayout.addWidget(dryLabel,1,0,Qt.AlignmentFlag.AlignRight)
        phaseLayout.addWidget(self.startdry,1,1)
        phaseLayout.addWidget(self.enddry,1,2)
        phaseLayout.addWidget(midLabel,2,0,Qt.AlignmentFlag.AlignRight)
        phaseLayout.addWidget(self.startmid,2,1)
        phaseLayout.addWidget(self.endmid,2,2)
        phaseLayout.addWidget(finishLabel,3,0,Qt.AlignmentFlag.AlignRight)
        phaseLayout.addWidget(self.startfinish,3,1)
        phaseLayout.addWidget(self.endfinish,3,2)

        lcdmodes = [QApplication.translate("ComboBox","Time"),
                    QApplication.translate("ComboBox","Percentage"),
                    QApplication.translate("ComboBox","Temp")]

        lcdmode = QLabel(QApplication.translate("Label", "Phases\nLCDs Mode"))
        phaseLayout.addWidget(lcdmode,0,3,Qt.AlignmentFlag.AlignCenter)
        lcdmode = QLabel(QApplication.translate("Label", "Phases\nLCDs All"))
        phaseLayout.addWidget(lcdmode,0,4,Qt.AlignmentFlag.AlignCenter)

        self.lcdmodeComboBox_dry = QComboBox()
        self.lcdmodeComboBox_dry.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lcdmodeComboBox_dry.addItems(lcdmodes)
        self.lcdmodeComboBox_dry.currentIndexChanged.connect(self.lcdmodeComboBox_dryChanged)
        self.lcdmodeComboBox_mid = QComboBox()
        self.lcdmodeComboBox_mid.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lcdmodeComboBox_mid.addItems(lcdmodes)
        self.lcdmodeComboBox_mid.currentIndexChanged.connect(self.lcdmodeComboBox_midChanged)
        self.lcdmodeComboBox_fin = QComboBox()
        self.lcdmodeComboBox_fin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lcdmodeComboBox_fin.addItems(lcdmodes)
        self.lcdmodeComboBox_fin.currentIndexChanged.connect(self.lcdmodeComboBox_finChanged)
        phaseLayout.addWidget(self.lcdmodeComboBox_dry,1,3)
        phaseLayout.addWidget(self.lcdmodeComboBox_mid,2,3)
        phaseLayout.addWidget(self.lcdmodeComboBox_fin,3,3)

        self.lcdmodeComboBox_dry.setCurrentIndex(self.aw.qmc.phasesLCDmode_l[0])
        self.lcdmodeComboBox_dry.setEnabled(not bool(self.aw.qmc.phasesLCDmode_all[0]))
        self.lcdmodeComboBox_mid.setCurrentIndex(self.aw.qmc.phasesLCDmode_l[1])
        self.lcdmodeComboBox_mid.setEnabled(not bool(self.aw.qmc.phasesLCDmode_all[1]))
        self.lcdmodeComboBox_fin.setCurrentIndex(self.aw.qmc.phasesLCDmode_l[2])
        self.lcdmodeComboBox_fin.setEnabled(not bool(self.aw.qmc.phasesLCDmode_all[2]))
        
        self.lcdmodeFlag_all_fin = QCheckBox()
        self.lcdmodeFlag_all_fin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lcdmodeFlag_all_fin.setChecked(self.aw.qmc.phasesLCDmode_all[2])
        self.lcdmodeFlag_all_fin.stateChanged.connect(self.lcdmodeFlagFinChanged)
        phaseLayout.addWidget(self.lcdmodeFlag_all_fin,3,4,Qt.AlignmentFlag.AlignCenter)
               
        self.events2phases()
        
        boxedPhaseLayout = QHBoxLayout()
        boxedPhaseLayout.addStretch()
        boxedPhaseLayout.addLayout(phaseLayout)
        boxedPhaseLayout.addStretch()
        boxedPhaseFlagGrid = QGridLayout()
        boxedPhaseFlagGrid.addWidget(self.pushbuttonflag,0,0)
        boxedPhaseFlagGrid.addWidget(self.fromBackgroundflag,0,1)
        boxedPhaseFlagGrid.addWidget(self.autoDRYflag,1,0)
        boxedPhaseFlagGrid.addWidget(self.autoFCsFlag,1,1)
        boxedPhaseFlagGrid.addWidget(self.watermarksflag,2,0)
        boxedPhaseFlagGrid.addWidget(self.phasesLCDflag,2,1)
        boxedPhaseFlagLayout = QHBoxLayout()
        boxedPhaseFlagLayout.addStretch()
        boxedPhaseFlagLayout.addLayout(boxedPhaseFlagGrid)
        boxedPhaseFlagLayout.addStretch()
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.dialogbuttons)
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(boxedPhaseLayout)
        mainLayout.addLayout(boxedPhaseFlagLayout)
        mainLayout.addStretch()
        mainLayout.addSpacing(10)
        mainLayout.addLayout(buttonsLayout)
        self.setLayout(mainLayout)
        self.getphases()
        self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok).setFocus()
        
        settings = QSettings()
        if settings.contains("PhasesPosition"):
            self.move(settings.value("PhasesPosition"))
        
        mainLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        
    @pyqtSlot(int)
    def lcdmodeFlagFinChanged(self,value):
        self.aw.qmc.phasesLCDmode_all[2] = bool(value)
        self.lcdmodeComboBox_fin.setEnabled(not bool(self.aw.qmc.phasesLCDmode_all[2]))
    
    @pyqtSlot(int)
    def lcdmodeComboBox_dryChanged(self,_):
        self.aw.qmc.phasesLCDmode_l[0] = self.lcdmodeComboBox_dry.currentIndex()
        self.aw.qmc.phasesLCD = self.aw.qmc.phasesLCDmode_l[0]

    @pyqtSlot(int)
    def lcdmodeComboBox_midChanged(self,_):
        self.aw.qmc.phasesLCDmode_l[1] = self.lcdmodeComboBox_mid.currentIndex()

    @pyqtSlot(int)
    def lcdmodeComboBox_finChanged(self,_):
        self.aw.qmc.phasesLCDmode_l[2] = self.lcdmodeComboBox_fin.currentIndex()

    def savePhasesSettings(self):
        if not self.aw.qmc.phasesbuttonflag:
            settings = QSettings()
            #save phases
            settings.setValue("Phases",self.aw.qmc.phases)

    def bevents2phases(self):
        if self.aw.qmc.phasesfromBackgroundflag and self.aw.qmc.backgroundprofile is not None:
            # adjust phases by DryEnd and FCs events from background profile
            if self.aw.qmc.timeindexB[1]:
                self.aw.qmc.phases[1] = int(round(self.aw.qmc.temp2B[self.aw.qmc.timeindexB[1]]))
            if self.aw.qmc.timeindexB[2]:
                self.aw.qmc.phases[2] = int(round(self.aw.qmc.temp2B[self.aw.qmc.timeindexB[2]]))
            
    def events2phases(self):
        if self.aw.qmc.phasesbuttonflag:
            # adjust phases by DryEnd and FCs events
            if self.aw.qmc.timeindex[1]:
                self.aw.qmc.phases[1] = int(round(self.aw.qmc.temp2[self.aw.qmc.timeindex[1]]))
            self.enddry.setDisabled(True)
            self.startmid.setDisabled(True)
            if self.aw.qmc.timeindex[2]:
                self.aw.qmc.phases[2] = int(round(self.aw.qmc.temp2[self.aw.qmc.timeindex[2]]))
            self.endmid.setDisabled(True)
            self.startfinish.setDisabled(True)

    @pyqtSlot(int)
    def watermarksflagChanged(self,_):
        self.aw.qmc.watermarksflag = not self.aw.qmc.watermarksflag
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def phasesLCDsflagChanged(self,_):
        self.aw.qmc.phasesLCDflag = not self.aw.qmc.phasesLCDflag
        if self.aw.qmc.flagstart:
            if self.aw.qmc.phasesLCDflag:
                self.aw.phasesLCDs.show()
            else:
                self.aw.phasesLCDs.hide()

    @pyqtSlot(int)
    def autoDRYflagChanged(self,_):
        self.aw.qmc.autoDRYflag = not self.aw.qmc.autoDRYflag
        if self.aw.qmc.autoDRYflag:
            self.pushbuttonflag.setChecked(False)
        
    @pyqtSlot(int)
    def autoFCsFlagChanged(self,_):
        self.aw.qmc.autoFCsFlag = not self.aw.qmc.autoFCsFlag
        if self.aw.qmc.autoFCsFlag:
            self.pushbuttonflag.setChecked(False)

    @pyqtSlot(int)
    def fromBackgroundflagChanged(self,i):
        if i:
            self.aw.qmc.phasesfromBackgroundflag = True
            self.bevents2phases()
            self.getphases()
            self.aw.qmc.redraw(recomputeAllDeltas=False)
        else:
            self.aw.qmc.phasesfromBackgroundflag = False
    
    @pyqtSlot(int)
    def pushbuttonflagChanged(self,i):
        if i:
            self.aw.qmc.phasesbuttonflag = True
            self.events2phases()
            self.getphases()
            self.aw.qmc.redraw(recomputeAllDeltas=False)
        else:
            self.aw.qmc.phasesbuttonflag = False
            self.enddry.setEnabled(True)
            self.startmid.setEnabled(True)
            self.endmid.setEnabled(True)
            self.startfinish.setEnabled(True)
        if self.aw.qmc.phasesbuttonflag:
            self.autoDRYflag.setChecked(False)
            self.autoFCsFlag.setChecked(False)

    @pyqtSlot()
    def updatephases(self):
        self.aw.qmc.phases[0] = self.startdry.value()
        self.aw.qmc.phases[1] = self.enddry.value()
        self.aw.qmc.phases[2] = self.endmid.value()
        self.aw.qmc.phases[3] = self.endfinish.value()

        if self.pushbuttonflag.isChecked():
            self.aw.qmc.phasesbuttonflag = True
        else:
            self.aw.qmc.phasesbuttonflag = False
        self.aw.qmc.redraw(recomputeAllDeltas=False)
        self.savePhasesSettings()
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue("PhasesPosition",self.frameGeometry().topLeft())
#        self.aw.closeEventSettings()
        self.accept()

    @pyqtSlot()
    def cancel(self):
        self.aw.qmc.phases = list(self.phases)
        self.aw.qmc.phasesbuttonflag = bool(self.org_phasesbuttonflag)
        self.aw.qmc.phasesfromBackgroundflag = bool(self.org_fromBackgroundflag)
        self.aw.qmc.watermarksflag = bool(self.org_watermarksflag)
        self.aw.qmc.phasesLCDflag = bool(self.org_phasesLCDflag)
        self.aw.qmc.autoDRYflag = bool(self.org_autoDRYflag)
        self.aw.qmc.autoFCsFlag = bool(self.org_autoFCsFlag)
        self.aw.qmc.phasesLCDmode_l = list(self.org_phasesLCDmode_l)
        self.aw.qmc.phasesLCDmode_all = list(self.org_phasesLCDmode_all)
        self.aw.qmc.redraw(recomputeAllDeltas=False)
        self.savePhasesSettings()
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue("PhasesPosition",self.frameGeometry().topLeft())
        self.reject()

    def getphases(self):
        self.startdry.setValue(self.aw.qmc.phases[0])
        self.startdry.repaint()
        self.enddry.setValue(self.aw.qmc.phases[1])
        self.enddry.repaint()
        self.endmid.setValue(self.aw.qmc.phases[2])
        self.endmid.repaint()
        self.endfinish.setValue(self.aw.qmc.phases[3])
        self.endfinish.repaint()
        
    @pyqtSlot(bool)
    def setdefault(self,_):
        if self.aw.qmc.mode == "F":
            self.aw.qmc.phases = list(self.aw.qmc.phases_fahrenheit_defaults)
        elif self.aw.qmc.mode == "C":
            self.aw.qmc.phases = list(self.aw.qmc.phases_celsius_defaults)
        self.events2phases()
        self.getphases()
        self.aw.sendmessage(QApplication.translate("Message","Phases changed to {0} default: {1}").format(self.aw.qmc.mode,str(self.aw.qmc.phases)))
        self.aw.qmc.redraw(recomputeAllDeltas=False)


