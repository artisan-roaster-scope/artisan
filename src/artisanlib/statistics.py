# -*- coding: utf-8 -*-
#
# ABOUT
# Artisan Statistics Dialog

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
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QGroupBox, QLayout, # @UnusedImport @Reimport  @UnresolvedImport
        QSpinBox) # @UnusedImport @Reimport  @UnresolvedImport
except Exception:
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import Qt, pyqtSlot, QSettings # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QLabel, QDialogButtonBox, QGridLayout, # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QGroupBox, QLayout, # @UnusedImport @Reimport  @UnresolvedImport
        QSpinBox) # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.util import deltaLabelUTF8

class StatisticsDlg(ArtisanDialog):
    def __init__(self, parent = None, aw = None):
        super().__init__(parent, aw)
        self.setWindowTitle(QApplication.translate("Form Caption","Statistics"))
        self.setModal(True)
        self.timez = QCheckBox(QApplication.translate("CheckBox","Time"))
        self.bar = QCheckBox(QApplication.translate("CheckBox","Bar"))
        self.dt = QCheckBox(deltaLabelUTF8 + self.aw.qmc.mode)
        self.ror = QCheckBox(self.aw.qmc.mode + QApplication.translate("CheckBox","/min"))
        self.area = QCheckBox(QApplication.translate("CheckBox","Characteristics"))
        self.ShowStatsSummary = QCheckBox(QApplication.translate("CheckBox", "Summary"))
        self.ShowStatsSummary.setChecked(self.aw.qmc.statssummary)
        self.ShowStatsSummary.stateChanged.connect(self.changeStatsSummary)         #toggle
        #temp fix for possible bug self.aw.qmc.statisticsflags=[] > empty list out of range
        if self.aw.qmc.statisticsflags:
            if self.aw.qmc.statisticsflags[0]:
                self.timez.setChecked(True)
            if self.aw.qmc.statisticsflags[1]:
                self.bar.setChecked(True)
            if self.aw.qmc.statisticsflags[3]:
                self.area.setChecked(True)
            if self.aw.qmc.statisticsflags[4]:
                self.ror.setChecked(True)
            if self.aw.qmc.statisticsflags[6]:
                self.dt.setChecked(True)
        else:
            self.aw.qmc.statisticsflags = [1,1,0,1,1,0,1]
            self.timez.setChecked(True)
            self.bar.setChecked(True)
            self.area.setChecked(True)
            self.ror.setChecked(True)
            self.dt.setChecked(False)
        self.timez.stateChanged.connect(self.changeStatisticsflag)
        self.bar.stateChanged.connect(self.changeStatisticsflag)
        # flag 2 not used anymore
        self.area.stateChanged.connect(self.changeStatisticsflag)
        self.ror.stateChanged.connect(self.changeStatisticsflag)
        # flag 5 not used anymore
        self.dt.stateChanged.connect(self.changeStatisticsflag)
        
        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.accept)
        self.dialogbuttons.removeButton(self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel))
        flagsLayout = QGridLayout()
        flagsLayout.addWidget(self.timez,0,0)
        flagsLayout.addWidget(self.bar,0,1)
        flagsLayout.addWidget(self.dt,0,2)
        flagsLayout.addWidget(self.ror,0,3)
        flagsLayout.addWidget(self.area,0,4)
        flagsLayout.addWidget(self.ShowStatsSummary,0,5)
        
        beginlabel =QLabel(QApplication.translate("Label", "From"))
        beginitems = [
                    QApplication.translate("Label","CHARGE"),
                    QApplication.translate("Label","TP"),
                    QApplication.translate("Label","DRY END"),
                    QApplication.translate("Label","FC START")]
        self.beginComboBox = QComboBox()
        self.beginComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.beginComboBox.setMaximumWidth(120)
        self.beginComboBox.addItems(beginitems)
        self.beginComboBox.setCurrentIndex(self.aw.qmc.AUCbegin)
        baselabel =QLabel(QApplication.translate("Label", "Base"))
        self.baseedit = QSpinBox()
        self.baseedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.baseedit.setRange(0,999)
        self.baseedit.setValue(self.aw.qmc.AUCbase)
        if self.aw.qmc.mode == "F":
            self.baseedit.setSuffix(" F")
        else:
            self.baseedit.setSuffix(" C")
        self.baseFlag = QCheckBox(QApplication.translate("CheckBox","From Event"))
        self.baseedit.setEnabled(not self.aw.qmc.AUCbaseFlag)
        self.baseFlag.setChecked(self.aw.qmc.AUCbaseFlag)
        self.baseFlag.stateChanged.connect(self.switchAUCbase)
        targetlabel =QLabel(QApplication.translate("Label", "Target"))
        self.targetedit = QSpinBox()
        self.targetedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.targetedit.setRange(0,9999)
        self.targetedit.setValue(self.aw.qmc.AUCtarget)
        self.targetFlag = QCheckBox(QApplication.translate("CheckBox","Background"))
        self.targetedit.setEnabled(not self.aw.qmc.AUCtargetFlag)
        self.targetFlag.setChecked(self.aw.qmc.AUCtargetFlag)
        self.targetFlag.stateChanged.connect(self.switchAUCtarget)
        self.guideFlag = QCheckBox(QApplication.translate("CheckBox","Guide"))
        self.guideFlag.setChecked(self.aw.qmc.AUCguideFlag)
        self.AUClcdFlag = QCheckBox(QApplication.translate("CheckBox","LCD"))
        self.AUClcdFlag.setChecked(self.aw.qmc.AUClcdFlag)
        self.AUClcdFlag.stateChanged.connect(self.AUCLCFflagChanged)
        self.AUCshowFlag = QCheckBox(QApplication.translate("CheckBox","Show Area"))
        self.AUCshowFlag.setChecked(self.aw.qmc.AUCshowFlag)
        self.AUCshowFlag.stateChanged.connect(self.changeAUCshowFlag)

        statsmaxchrperlinelabel =QLabel(QApplication.translate("Label", "Max characters per line"))
        self.statsmaxchrperlineedit = QSpinBox()
        self.statsmaxchrperlineedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.statsmaxchrperlineedit.setRange(1,120)
        self.statsmaxchrperlineedit.setValue(self.aw.qmc.statsmaxchrperline)
        self.statsmaxchrperlineedit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        statsmaxchrperlineHorizontal = QHBoxLayout()
        statsmaxchrperlineHorizontal.addWidget(statsmaxchrperlinelabel)
        statsmaxchrperlineHorizontal.addWidget(self.statsmaxchrperlineedit)
        statsmaxchrperlineHorizontal.addStretch()
        statsmaxchrperlineGroupLayout = QGroupBox(QApplication.translate("GroupBox","Stats Summary"))
        statsmaxchrperlineGroupLayout.setLayout(statsmaxchrperlineHorizontal)

        AUCgrid = QGridLayout()
        AUCgrid.addWidget(beginlabel,0,0,Qt.AlignmentFlag.AlignRight)
        AUCgrid.addWidget(self.beginComboBox,0,1,1,2)
        AUCgrid.addWidget(baselabel,1,0,Qt.AlignmentFlag.AlignRight)
        AUCgrid.addWidget(self.baseedit,1,1)
        AUCgrid.addWidget(self.baseFlag,1,2)
        AUCgrid.addWidget(targetlabel,2,0,Qt.AlignmentFlag.AlignRight)
        AUCgrid.addWidget(self.targetedit,2,1)
        AUCgrid.addWidget(self.targetFlag,2,2)
        AUCgrid.setRowMinimumHeight(3, 20)
        
        aucFlagsLayout = QHBoxLayout()
        aucFlagsLayout.addStretch()
        aucFlagsLayout.addWidget(self.AUClcdFlag)
        aucFlagsLayout.addSpacing(10)
        aucFlagsLayout.addWidget(self.guideFlag)
        aucFlagsLayout.addSpacing(10)
        aucFlagsLayout.addWidget(self.AUCshowFlag)
        aucFlagsLayout.addStretch()
        
        AUCvertical = QVBoxLayout()
        AUCvertical.addLayout(AUCgrid)
        AUCvertical.addLayout(aucFlagsLayout)
        AUCvertical.addStretch()
        AUCgroupLayout = QGroupBox(QApplication.translate("GroupBox","AUC"))
        AUCgroupLayout.setLayout(AUCvertical)
        displayGroupLayout = QGroupBox(QApplication.translate("GroupBox","Display"))
        displayGroupLayout.setLayout(flagsLayout)
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.dialogbuttons)
        vgroupLayout = QVBoxLayout()
        vgroupLayout.addWidget(AUCgroupLayout)
        vgroupLayout.addWidget(statsmaxchrperlineGroupLayout)
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(displayGroupLayout)
        mainLayout.addLayout(vgroupLayout)
        mainLayout.addStretch()
        mainLayout.addLayout(buttonsLayout)
        mainLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.setLayout(mainLayout)
        self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok).setFocus()
        
        settings = QSettings()
        if settings.contains("StatisticsPosition"):
            self.move(settings.value("StatisticsPosition"))
        
        mainLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def AUCLCFflagChanged(self,_):
        self.aw.qmc.AUClcdFlag = not self.aw.qmc.AUClcdFlag
        if self.aw.qmc.flagstart:
            if self.aw.qmc.AUClcdFlag:
                self.aw.AUCLCD.show()
            else:
                self.aw.AUCLCD.hide()
        if self.aw.largePhasesLCDs_dialog is not None:
            self.aw.largePhasesLCDs_dialog.updateVisiblitiesPhases()

    @pyqtSlot(int)
    def changeAUCshowFlag(self,_):
        self.aw.qmc.AUCshowFlag = not self.aw.qmc.AUCshowFlag
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def switchAUCbase(self,i):
        if i:
            self.baseedit.setEnabled(False)
        else:
            self.baseedit.setEnabled(True)
            
    @pyqtSlot(int)
    def switchAUCtarget(self,i):
        if i:
            self.targetedit.setEnabled(False)
        else:
            self.targetedit.setEnabled(True)

    @pyqtSlot(int)
    def changeStatsSummary(self,_):
        self.aw.qmc.statssummary = not self.aw.qmc.statssummary
        # IF Auto is set for the axis the recompute it
        if self.aw.qmc.autotimex and not self.aw.qmc.statssummary:
            self.aw.autoAdjustAxis()
        self.aw.qmc.redraw(recomputeAllDeltas=False)
        if self.aw.qmc.statssummary and not self.aw.qmc.flagon:
            self.aw.savestatisticsAction.setEnabled(True)
        else:
            self.aw.savestatisticsAction.setEnabled(False)
    
    @pyqtSlot(int)
    def changeStatisticsflag(self,value):
        sender = self.sender()
        if sender == self.timez:
            i = 0
        elif sender == self.bar:
            i = 1
        elif sender == self.area:
            i = 3
        elif sender == self.ror:
            i = 4
        elif sender == self.dt:
            i = 6
        else:
            return
        self.aw.qmc.statisticsflags[i] = value
        self.aw.qmc.redraw(recomputeAllDeltas=False)
        
    @pyqtSlot()
    def accept(self):
        self.aw.qmc.statsmaxchrperline = self.statsmaxchrperlineedit.value()
        self.aw.qmc.AUCbegin = self.beginComboBox.currentIndex()
        self.aw.qmc.AUCbase = self.baseedit.value()
        self.aw.qmc.AUCbaseFlag = self.baseFlag.isChecked()
        self.aw.qmc.AUCtarget = self.targetedit.value()
        self.aw.qmc.AUCtargetFlag = self.targetFlag.isChecked()
        self.aw.qmc.AUCguideFlag = self.guideFlag.isChecked()
        self.aw.qmc.AUClcdFlag = self.AUClcdFlag.isChecked()
        try:
            if self.aw.qmc.TP_time_B:
                _,_,auc,_ = self.aw.ts(tp=self.aw.qmc.backgroundtime2index(self.aw.qmc.TP_time_B),background=True)
            else:
                _,_,auc,_ = self.aw.ts(tp=0,background=True)
            self.aw.qmc.AUCbackground = auc
        except Exception: # pylint: disable=broad-except
            pass
        if self.timez.isChecked(): 
            self.aw.qmc.statisticsflags[0] = 1
        else:
            self.aw.qmc.statisticsflags[0] = 0
            
        if self.bar.isChecked(): 
            self.aw.qmc.statisticsflags[1] = 1
        else:
            self.aw.qmc.statisticsflags[1] = 0
            
        if self.area.isChecked(): 
            self.aw.qmc.statisticsflags[3] = 1
        else:
            self.aw.qmc.statisticsflags[3] = 0
            
        if self.ror.isChecked(): 
            self.aw.qmc.statisticsflags[4] = 1
        else:
            self.aw.qmc.statisticsflags[4] = 0
            
        if self.dt.isChecked(): 
            self.aw.qmc.statisticsflags[6] = 1
        else:
            self.aw.qmc.statisticsflags[6] = 0

        self.aw.qmc.redraw(recomputeAllDeltas=False)
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue("StatisticsPosition",self.frameGeometry().topLeft())
#        self.aw.closeEventSettings()
        self.close()