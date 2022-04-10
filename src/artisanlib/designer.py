#
# ABOUT
# Artisan Designer Dialogs

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

from artisanlib.util import stringfromseconds, stringtoseconds
from artisanlib.dialogs import ArtisanDialog

try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtCore import Qt, pyqtSlot, QRegularExpression, QSettings # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QIntValidator, QRegularExpressionValidator # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QLabel, # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QDialogButtonBox, QGridLayout, # @UnusedImport @Reimport  @UnresolvedImport
        QGroupBox, QLineEdit, QMessageBox, QLayout) # @UnusedImport @Reimport  @UnresolvedImport
except Exception:
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import Qt, pyqtSlot, QRegularExpression, QSettings # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QIntValidator, QRegularExpressionValidator # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QLabel, # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QDialogButtonBox, QGridLayout, # @UnusedImport @Reimport  @UnresolvedImport
        QGroupBox, QLineEdit, QMessageBox, QLayout) # @UnusedImport @Reimport  @UnresolvedImport


#########################################################################
#############  DESIGNER CONFIG DIALOG ###################################
#########################################################################

class designerconfigDlg(ArtisanDialog):
    def __init__(self, parent = None, aw = None):
        super().__init__(parent, aw)
        self.setWindowTitle(QApplication.translate('Form Caption','Designer Config'))
        self.setModal(True)
        #landmarks
        charge = QLabel(QApplication.translate('Label', 'CHARGE'))
        charge.setAlignment(Qt.AlignmentFlag.AlignRight)
        charge.setStyleSheet('background-color: #f07800')
        self.dryend = QCheckBox(QApplication.translate('CheckBox','DRY END'))
        self.dryend.setStyleSheet('background-color: orange')
        self.fcs = QCheckBox(QApplication.translate('CheckBox','FC START'))
        self.fcs.setStyleSheet('background-color: orange')
        self.fce = QCheckBox(QApplication.translate('CheckBox','FC END'))
        self.fce.setStyleSheet('background-color: orange')
        self.scs = QCheckBox(QApplication.translate('CheckBox','SC START'))
        self.scs.setStyleSheet('background-color: orange')
        self.sce = QCheckBox(QApplication.translate('CheckBox','SC END'))
        self.sce.setStyleSheet('background-color: orange')
        drop = QLabel(QApplication.translate('Label', 'DROP'))
        drop.setAlignment(Qt.AlignmentFlag.AlignRight)
        drop.setStyleSheet('background-color: #f07800')
        self.loadconfigflags()
        self.dryend.clicked.connect(self.changeflags)
        self.fcs.clicked.connect(self.changeflags)
        self.fce.clicked.connect(self.changeflags)
        self.scs.clicked.connect(self.changeflags)
        self.sce.clicked.connect(self.changeflags)
        if self.aw.qmc.timeindex[0] != -1:
            start = self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            start = 0
        markersettinglabel = QLabel(QApplication.translate('Label', 'Marker'))
        markersettinglabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timesettinglabel = QLabel(QApplication.translate('Label', 'Time'))
        timesettinglabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btsettinglabel = QLabel(QApplication.translate('Label', 'BT'))
        btsettinglabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        etsettinglabel = QLabel(QApplication.translate('Label', 'ET'))
        etsettinglabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.Edit0 = QLineEdit(stringfromseconds(0))
        self.Edit0.setEnabled(False)
        self.Edit0bt = QLineEdit('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[0]])
        self.Edit0et = QLineEdit('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[0]])
        self.Edit0.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit0bt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit0et.setAlignment(Qt.AlignmentFlag.AlignRight)
        if self.aw.qmc.timeindex[1]:
            self.Edit1 = QLineEdit(stringfromseconds(self.aw.qmc.timex[self.aw.qmc.timeindex[1]] - start))
            self.Edit1bt = QLineEdit('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[1]])
            self.Edit1et = QLineEdit('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[1]])
        else:
            self.Edit1 = QLineEdit(stringfromseconds(0))
            self.Edit1bt = QLineEdit('0.0')
            self.Edit1et = QLineEdit('0.0')
        self.Edit1.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit1bt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit1et.setAlignment(Qt.AlignmentFlag.AlignRight)
        if self.aw.qmc.timeindex[2]:
            self.Edit2 = QLineEdit(stringfromseconds(self.aw.qmc.timex[self.aw.qmc.timeindex[2]] - start))
            self.Edit2bt = QLineEdit('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[2]])
            self.Edit2et = QLineEdit('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[2]])
        else:
            self.Edit2 = QLineEdit(stringfromseconds(0))
            self.Edit2bt = QLineEdit('0.0')
            self.Edit2et = QLineEdit('0.0')
        self.Edit2.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit2bt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit2et.setAlignment(Qt.AlignmentFlag.AlignRight)
        if self.aw.qmc.timeindex[3]:
            self.Edit3 = QLineEdit(stringfromseconds(self.aw.qmc.timex[self.aw.qmc.timeindex[3]] - start))
            self.Edit3bt = QLineEdit('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[3]])
            self.Edit3et = QLineEdit('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[3]])
        else:
            self.Edit3 = QLineEdit(stringfromseconds(0))
            self.Edit3bt = QLineEdit('0.0')
            self.Edit3et = QLineEdit('0.0')
        self.Edit3.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit3bt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit3et.setAlignment(Qt.AlignmentFlag.AlignRight)
        if self.aw.qmc.timeindex[4]:
            self.Edit4 = QLineEdit(stringfromseconds(self.aw.qmc.timex[self.aw.qmc.timeindex[4]] - start))
            self.Edit4bt = QLineEdit('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[4]])
            self.Edit4et = QLineEdit('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[4]])
        else:
            self.Edit4 = QLineEdit(stringfromseconds(0))
            self.Edit4bt = QLineEdit('0.0')
            self.Edit4et = QLineEdit('0.0')
        self.Edit4.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit4bt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit4et.setAlignment(Qt.AlignmentFlag.AlignRight)
        if self.aw.qmc.timeindex[5]:
            self.Edit5 = QLineEdit(stringfromseconds(self.aw.qmc.timex[self.aw.qmc.timeindex[5]] - start))
            self.Edit5bt = QLineEdit('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[5]])
            self.Edit5et = QLineEdit('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[5]])
        else:
            self.Edit5 = QLineEdit(stringfromseconds(0))
            self.Edit5bt = QLineEdit('0.0')
            self.Edit5et = QLineEdit('0.0')
        self.Edit5.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit5bt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit5et.setAlignment(Qt.AlignmentFlag.AlignRight)
        if self.aw.qmc.timeindex[6]:
            self.Edit6 = QLineEdit(stringfromseconds(self.aw.qmc.timex[self.aw.qmc.timeindex[6]] - start))
            self.Edit6bt = QLineEdit('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[6]])
            self.Edit6et = QLineEdit('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[6]])
        else:
            self.Edit6 = QLineEdit(stringfromseconds(0))
            self.Edit6bt = QLineEdit('0.0')
            self.Edit6et = QLineEdit('0.0')
        self.Edit6.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit6bt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.Edit6et.setAlignment(Qt.AlignmentFlag.AlignRight)
        maxwidth = 70
        self.Edit0.setMaximumWidth(maxwidth)
        self.Edit1.setMaximumWidth(maxwidth)
        self.Edit2.setMaximumWidth(maxwidth)
        self.Edit3.setMaximumWidth(maxwidth)
        self.Edit4.setMaximumWidth(maxwidth)
        self.Edit5.setMaximumWidth(maxwidth)
        self.Edit6.setMaximumWidth(maxwidth)
        self.Edit0bt.setMaximumWidth(maxwidth)
        self.Edit1bt.setMaximumWidth(maxwidth)
        self.Edit2bt.setMaximumWidth(maxwidth)
        self.Edit3bt.setMaximumWidth(maxwidth)
        self.Edit4bt.setMaximumWidth(maxwidth)
        self.Edit5bt.setMaximumWidth(maxwidth)
        self.Edit6bt.setMaximumWidth(maxwidth)
        self.Edit0et.setMaximumWidth(maxwidth)
        self.Edit1et.setMaximumWidth(maxwidth)
        self.Edit2et.setMaximumWidth(maxwidth)
        self.Edit3et.setMaximumWidth(maxwidth)
        self.Edit4et.setMaximumWidth(maxwidth)
        self.Edit5et.setMaximumWidth(maxwidth)
        self.Edit6et.setMaximumWidth(maxwidth)
        self.Edit1copy = self.Edit1.text()
        self.Edit2copy = self.Edit2.text()
        self.Edit3copy = self.Edit3.text()
        self.Edit4copy = self.Edit4.text()
        self.Edit5copy = self.Edit5.text()
        self.Edit6copy = self.Edit6.text()
        self.Edit0btcopy = self.Edit0bt.text()
        self.Edit1btcopy = self.Edit1bt.text()
        self.Edit2btcopy = self.Edit2bt.text()
        self.Edit3btcopy = self.Edit3bt.text()
        self.Edit4btcopy = self.Edit4bt.text()
        self.Edit5btcopy = self.Edit5bt.text()
        self.Edit6btcopy = self.Edit6bt.text()
        self.Edit0etcopy = self.Edit0et.text()
        self.Edit1etcopy = self.Edit1et.text()
        self.Edit2etcopy = self.Edit2et.text()
        self.Edit3etcopy = self.Edit3et.text()
        self.Edit4etcopy = self.Edit4et.text()
        self.Edit5etcopy = self.Edit5et.text()
        self.Edit6etcopy = self.Edit6et.text()
        regextime = QRegularExpression(r'^-?[0-9]?[0-9]?[0-9]:[0-5][0-9]$')
        self.Edit0.setValidator(QRegularExpressionValidator(regextime,self))
        self.Edit1.setValidator(QRegularExpressionValidator(regextime,self))
        self.Edit2.setValidator(QRegularExpressionValidator(regextime,self))
        self.Edit3.setValidator(QRegularExpressionValidator(regextime,self))
        self.Edit4.setValidator(QRegularExpressionValidator(regextime,self))
        self.Edit5.setValidator(QRegularExpressionValidator(regextime,self))
        self.Edit6.setValidator(QRegularExpressionValidator(regextime,self))
        regextemp = QRegularExpression(r'^-?[0-9]?[0-9]?[0-9]?\.?[0-9]?$')
        self.Edit0bt.setValidator(QRegularExpressionValidator(regextemp,self))
        self.Edit1bt.setValidator(QRegularExpressionValidator(regextemp,self))
        self.Edit2bt.setValidator(QRegularExpressionValidator(regextemp,self))
        self.Edit3bt.setValidator(QRegularExpressionValidator(regextemp,self))
        self.Edit4bt.setValidator(QRegularExpressionValidator(regextemp,self))
        self.Edit5bt.setValidator(QRegularExpressionValidator(regextemp,self))
        self.Edit6bt.setValidator(QRegularExpressionValidator(regextemp,self))
        self.Edit0et.setValidator(QRegularExpressionValidator(regextemp,self))
        self.Edit1et.setValidator(QRegularExpressionValidator(regextemp,self))
        self.Edit2et.setValidator(QRegularExpressionValidator(regextemp,self))
        self.Edit3et.setValidator(QRegularExpressionValidator(regextemp,self))
        self.Edit4et.setValidator(QRegularExpressionValidator(regextemp,self))
        self.Edit5et.setValidator(QRegularExpressionValidator(regextemp,self))
        self.Edit6et.setValidator(QRegularExpressionValidator(regextemp,self))
        curvinesslabel = QLabel(QApplication.translate('Label', 'Curviness'))
        etcurviness = QLabel(QApplication.translate('Label', 'ET'))
        btcurviness = QLabel(QApplication.translate('Label', 'BT'))
        etcurviness.setAlignment(Qt.AlignmentFlag.AlignRight)
        btcurviness.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.ETsplineComboBox = QComboBox()
        self.ETsplineComboBox.addItems(['1','2','3','4','5'])
        self.ETsplineComboBox.setCurrentIndex(self.aw.qmc.ETsplinedegree - 1)
        self.ETsplineComboBox.currentIndexChanged.connect(self.redrawcurviness)
        self.BTsplineComboBox = QComboBox()
        self.BTsplineComboBox.addItems(['1','2','3','4','5'])
        self.BTsplineComboBox.setCurrentIndex(self.aw.qmc.BTsplinedegree - 1)
        self.BTsplineComboBox.currentIndexChanged.connect(self.redrawcurviness)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.removeButton(self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok))
        self.dialogbuttons.removeButton(self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel))

        self.dialogbuttons.addButton(QDialogButtonBox.StandardButton.Close)
        self.dialogbuttons.addButton(QDialogButtonBox.StandardButton.Apply)
        self.dialogbuttons.addButton(QDialogButtonBox.StandardButton.RestoreDefaults)
        self.setButtonTranslations(self.dialogbuttons.button(QDialogButtonBox.StandardButton.Close),'Close',QApplication.translate('Button','Close'))
        self.setButtonTranslations(self.dialogbuttons.button(QDialogButtonBox.StandardButton.Apply),'Apply',QApplication.translate('Button','Apply'))
        self.setButtonTranslations(self.dialogbuttons.button(QDialogButtonBox.StandardButton.RestoreDefaults),'Restore Defaults',QApplication.translate('Button','Restore Defaults'))

        self.dialogbuttons.rejected.connect(self.accept)
        self.dialogbuttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.reset)
        self.dialogbuttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.settimes)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)
        marksLayout = QGridLayout()
        marksLayout.addWidget(markersettinglabel,0,0)
        marksLayout.addWidget(timesettinglabel,0,1)
        marksLayout.addWidget(btsettinglabel,0,2)
        marksLayout.addWidget(etsettinglabel,0,3)
        marksLayout.addWidget(charge,1,0)
        marksLayout.addWidget(self.Edit0,1,1)
        marksLayout.addWidget(self.Edit0bt,1,2)
        marksLayout.addWidget(self.Edit0et,1,3)
        marksLayout.addWidget(self.dryend,2,0)
        marksLayout.addWidget(self.Edit1,2,1)
        marksLayout.addWidget(self.Edit1bt,2,2)
        marksLayout.addWidget(self.Edit1et,2,3)
        marksLayout.addWidget(self.fcs,3,0)
        marksLayout.addWidget(self.Edit2,3,1)
        marksLayout.addWidget(self.Edit2bt,3,2)
        marksLayout.addWidget(self.Edit2et,3,3)
        marksLayout.addWidget(self.fce,4,0)
        marksLayout.addWidget(self.Edit3,4,1)
        marksLayout.addWidget(self.Edit3bt,4,2)
        marksLayout.addWidget(self.Edit3et,4,3)
        marksLayout.addWidget(self.scs,5,0)
        marksLayout.addWidget(self.Edit4,5,1)
        marksLayout.addWidget(self.Edit4bt,5,2)
        marksLayout.addWidget(self.Edit4et,5,3)
        marksLayout.addWidget(self.sce,6,0)
        marksLayout.addWidget(self.Edit5,6,1)
        marksLayout.addWidget(self.Edit5bt,6,2)
        marksLayout.addWidget(self.Edit5et,6,3)
        marksLayout.addWidget(drop,7,0)
        marksLayout.addWidget(self.Edit6,7,1)
        marksLayout.addWidget(self.Edit6bt,7,2)
        marksLayout.addWidget(self.Edit6et,7,3)
        settingsLayout = QVBoxLayout()
        settingsLayout.addLayout(marksLayout)
        curvinessLayout = QHBoxLayout()
        curvinessLayout.addWidget(curvinesslabel)
        curvinessLayout.addWidget(etcurviness)
        curvinessLayout.addWidget(self.ETsplineComboBox)
        curvinessLayout.addWidget(btcurviness)
        curvinessLayout.addWidget(self.BTsplineComboBox)
        modLayout = QVBoxLayout()
        modLayout.addLayout(curvinessLayout)
        marksGroupLayout = QGroupBox(QApplication.translate('GroupBox','Initial Settings'))
        marksGroupLayout.setLayout(settingsLayout)
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(marksGroupLayout)
        mainLayout.addLayout(modLayout)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
        self.dialogbuttons.button(QDialogButtonBox.StandardButton.Close).setFocus()

        settings = QSettings()
        if settings.contains('DesignerPosition'):
            self.move(settings.value('DesignerPosition'))

        mainLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    @pyqtSlot(int)
    def redrawcurviness(self,_):
        ETcurviness = int(str(self.ETsplineComboBox.currentText()))
        BTcurviness = int(str(self.BTsplineComboBox.currentText()))
        timepoints = len(self.aw.qmc.timex)
        if (timepoints - ETcurviness) >= 1:
            self.aw.qmc.ETsplinedegree = ETcurviness
        else:
            self.aw.qmc.ETsplinedegree = len(self.aw.qmc.timex)-1
            self.ETsplineComboBox.setCurrentIndex(self.aw.qmc.ETsplinedegree-1)
            ms = QApplication.translate('Message','Not enough time points for an ET curviness of {0}. Set curviness to {1}').format(ETcurviness,self.aw.qmc.ETsplinedegree)
            QMessageBox.information(self,QApplication.translate('Message','Designer Config'),ms)
        if (timepoints - BTcurviness) >= 1:
            self.aw.qmc.BTsplinedegree = BTcurviness
        else:
            self.aw.qmc.BTsplinedegree = len(self.aw.qmc.timex)-1
            self.BTsplineComboBox.setCurrentIndex(self.aw.qmc.BTsplinedegree-1)
            ms = QApplication.translate('Message','Not enough time points for an BT curviness of {0}. Set curviness to {1}').format(BTcurviness,self.aw.qmc.BTsplinedegree)
            QMessageBox.information(self,QApplication.translate('Message','Designer Config'),ms)
        self.aw.qmc.redrawdesigner()

    @pyqtSlot(bool)
    def settimes(self,_):
        #check input
        strings = [QApplication.translate('Message','CHARGE'),
                   QApplication.translate('Message','DRY END'),
                   QApplication.translate('Message','FC START'),
                   QApplication.translate('Message','FC END'),
                   QApplication.translate('Message','SC START'),
                   QApplication.translate('Message','SC END'),
                   QApplication.translate('Message','DROP')]
        timecheck = self.validatetime()
        if timecheck != 1000:
            st = QApplication.translate('Message','Incorrect time format. Please recheck {0} time').format(strings[timecheck])
            QMessageBox.information(self,QApplication.translate('Message','Designer Config'),st)
            return 1
        checkvalue = self.validatetimeorder()
        if checkvalue != 1000:
            st = QApplication.translate('Message','Times need to be in ascending order. Please recheck {0} time').format(strings[checkvalue+1])
            QMessageBox.information(self,QApplication.translate('Message','Designer Config'),st)
            return 1
        if self.Edit0bt.text() != self.Edit0btcopy:
            self.aw.qmc.temp2[self.aw.qmc.timeindex[0]] = float(str(self.Edit0bt.text()))
            self.Edit0btcopy = self.Edit0bt.text()
        if self.Edit0et.text() != self.Edit0etcopy:
            self.aw.qmc.temp1[self.aw.qmc.timeindex[0]] = float(str(self.Edit0et.text()))
            self.Edit0etcopy = self.Edit0et.text()
        if self.dryend.isChecked():
            if self.Edit1.text() != self.Edit1copy:
                if stringtoseconds(str(self.Edit1.text())):
                    timez = stringtoseconds(str(self.Edit1.text()))+ self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
                    self.aw.qmc.timex[self.aw.qmc.timeindex[1]] = timez
                    self.Edit1copy = self.Edit1.text()
            if self.Edit1bt.text() != self.Edit1btcopy:
                self.aw.qmc.temp2[self.aw.qmc.timeindex[1]] = float(str(self.Edit1bt.text()))
                self.Edit1btcopy = self.Edit1bt.text()
            if self.Edit1et.text() != self.Edit1etcopy:
                self.aw.qmc.temp1[self.aw.qmc.timeindex[1]] = float(str(self.Edit1et.text()))
                self.Edit1etcopy = self.Edit1et.text()
        if self.fcs.isChecked():
            if self.Edit2.text() != self.Edit2copy:
                if stringtoseconds(str(self.Edit2.text())):
                    timez = stringtoseconds(str(self.Edit2.text()))+ self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
                    self.aw.qmc.timex[self.aw.qmc.timeindex[2]] = timez
                    self.Edit2copy = self.Edit2.text()
            if self.Edit2bt.text() != self.Edit2btcopy:
                self.aw.qmc.temp2[self.aw.qmc.timeindex[2]] = float(str(self.Edit2bt.text()))
                self.Edit2btcopy = self.Edit2bt.text()
            if self.Edit2et.text() != self.Edit2etcopy:
                self.aw.qmc.temp1[self.aw.qmc.timeindex[2]] = float(str(self.Edit2et.text()))
                self.Edit2etcopy = self.Edit2et.text()
        if self.fce.isChecked():
            if self.Edit3.text() != self.Edit3copy:
                if stringtoseconds(str(self.Edit3.text())):
                    timez = stringtoseconds(str(self.Edit3.text()))+ self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
                    self.aw.qmc.timex[self.aw.qmc.timeindex[3]] = timez
                    self.Edit3copy = self.Edit3.text()
            if self.Edit3bt.text() != self.Edit3btcopy:
                self.aw.qmc.temp2[self.aw.qmc.timeindex[3]] = float(str(self.Edit3bt.text()))
                self.Edit3btcopy = self.Edit3bt.text()
            if self.Edit3et.text() != self.Edit3etcopy:
                self.aw.qmc.temp1[self.aw.qmc.timeindex[3]] = float(str(self.Edit3et.text()))
                self.Edit3etcopy = self.Edit3et.text()
        if self.scs.isChecked():
            if self.Edit4.text() != self.Edit4copy:
                if stringtoseconds(str(self.Edit4.text())):
                    timez = stringtoseconds(str(self.Edit4.text()))+ self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
                    self.aw.qmc.timex[self.aw.qmc.timeindex[4]] = timez
                    self.Edit4copy = self.Edit4.text()
            if self.Edit4bt.text() != self.Edit4btcopy:
                self.aw.qmc.temp2[self.aw.qmc.timeindex[4]] = float(str(self.Edit4bt.text()))
                self.Edit4btcopy = self.Edit4bt.text()
            if self.Edit4et.text() != self.Edit4etcopy:
                self.aw.qmc.temp1[self.aw.qmc.timeindex[4]] = float(str(self.Edit4et.text()))
                self.Edit4etcopy = self.Edit4et.text()
        if self.sce.isChecked():
            if self.Edit5.text() != self.Edit5copy:
                if stringtoseconds(str(self.Edit5.text())):
                    timez = stringtoseconds(str(self.Edit5.text()))+ self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
                    self.aw.qmc.timex[self.aw.qmc.timeindex[5]] = timez
                    self.Edit5copy = self.Edit5.text()
            if self.Edit5bt.text() != self.Edit5btcopy:
                self.aw.qmc.temp2[self.aw.qmc.timeindex[5]] = float(str(self.Edit5bt.text()))
                self.Edit5btcopy = self.Edit5bt.text()
            if self.Edit5et.text() != self.Edit5etcopy:
                self.aw.qmc.temp1[self.aw.qmc.timeindex[5]] = float(str(self.Edit5et.text()))
                self.Edit5etcopy = self.Edit5et.text()
        if self.Edit6.text() != self.Edit6copy:
            if stringtoseconds(str(self.Edit6.text())):
                timez = stringtoseconds(str(self.Edit6.text()))+ self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
                self.aw.qmc.timex[self.aw.qmc.timeindex[6]] = timez
                self.Edit6copy = self.Edit6.text()
        if self.Edit6bt.text() != self.Edit6btcopy:
            self.aw.qmc.temp2[self.aw.qmc.timeindex[6]] = float(str(self.Edit6bt.text()))
            self.Edit6btcopy = self.Edit6bt.text()
        if self.Edit6et.text() != self.Edit6etcopy:
            self.aw.qmc.temp1[self.aw.qmc.timeindex[6]] = float(str(self.Edit6et.text()))
            self.Edit6etcopy = self.Edit6et.text()
        for i in range(1,6): #1-5
            self.aw.qmc.designertimeinit[i] = self.aw.qmc.timex[self.aw.qmc.timeindex[i]]
        self.aw.qmc.xaxistosm(redraw=False)
        self.aw.qmc.redrawdesigner()
        return 0

    #supporting function for settimes()
    def validatetimeorder(self):
        time = []
        checks = self.readchecks()
        time.append(stringtoseconds(str(self.Edit0.text())) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]])
        time.append(stringtoseconds(str(self.Edit1.text())) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]])
        time.append(stringtoseconds(str(self.Edit2.text())) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]])
        time.append(stringtoseconds(str(self.Edit3.text())) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]])
        time.append(stringtoseconds(str(self.Edit4.text())) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]])
        time.append(stringtoseconds(str(self.Edit5.text())) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]])
        time.append(stringtoseconds(str(self.Edit6.text())) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]])
        for i in range(len(time)-1):
            if time[i+1] <= time[i] and checks[i+1] != 0:
                return i
        return 1000

    def validatetime(self):
        strings = []
        strings.append(self.Edit0.text())
        strings.append(self.Edit1.text())
        strings.append(self.Edit2.text())
        strings.append(self.Edit3.text())
        strings.append(self.Edit4.text())
        strings.append(self.Edit5.text())
        strings.append(self.Edit6.text())
        for i in range(len(strings)):
            if len(str(strings[i])) < 5:
                return i
            return 1000

    #supporting function for settimes()
    @pyqtSlot(bool)
    def readchecks(self,_=False):
        checks = [0,0,0,0,0,0,0]
        if self.dryend.isChecked():
            checks[1] = 1
        if self.fcs.isChecked():
            checks[2] = 1
        if self.fce.isChecked():
            checks[3] = 1
        if self.scs.isChecked():
            checks[4] = 1
        if self.sce.isChecked():
            checks[5] = 1
        return checks

    def create(self):
        self.close()
        self.aw.qmc.convert_designer()

    @pyqtSlot()
    def accept(self):
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue('DesignerPosition',self.frameGeometry().topLeft())
        super().accept()

    #reset
    @pyqtSlot(bool)
    def reset(self,_):
        self.dryend.setChecked(True)
        self.fcs.setChecked(True)
        self.fce.setChecked(True)
        self.scs.setChecked(True)
        self.sce.setChecked(True)
        #reset designer
        self.aw.qmc.reset_designer()
        #update editboxes
        self.Edit0.setText(stringfromseconds(0))
        self.Edit1.setText(stringfromseconds(self.aw.qmc.designertimeinit[1]))
        self.Edit2.setText(stringfromseconds(self.aw.qmc.designertimeinit[2]))
        self.Edit3.setText(stringfromseconds(self.aw.qmc.designertimeinit[3]))
        self.Edit4.setText(stringfromseconds(self.aw.qmc.designertimeinit[4]))
        self.Edit5.setText(stringfromseconds(self.aw.qmc.designertimeinit[5]))
        self.Edit6.setText(stringfromseconds(self.aw.qmc.designertimeinit[6]))
        self.Edit0bt.setText('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[0]])
        self.Edit1bt.setText('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[1]])
        self.Edit2bt.setText('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[2]])
        self.Edit3bt.setText('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[3]])
        self.Edit4bt.setText('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[4]])
        self.Edit5bt.setText('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[5]])
        self.Edit6bt.setText('%.1f'%self.aw.qmc.temp2[self.aw.qmc.timeindex[6]])
        self.Edit0et.setText('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[0]])
        self.Edit1et.setText('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[1]])
        self.Edit2et.setText('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[2]])
        self.Edit3et.setText('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[3]])
        self.Edit4et.setText('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[4]])
        self.Edit5et.setText('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[5]])
        self.Edit6et.setText('%.1f'%self.aw.qmc.temp1[self.aw.qmc.timeindex[6]])
        self.aw.sendmessage(QApplication.translate('Message','Designer has been reset'))

    def loadconfigflags(self):
        self.dryend.setChecked(self.aw.qmc.timeindex[1])
        self.fcs.setChecked(self.aw.qmc.timeindex[2])
        self.fce.setChecked(self.aw.qmc.timeindex[3])
        self.scs.setChecked(self.aw.qmc.timeindex[4])
        self.sce.setChecked(self.aw.qmc.timeindex[5])

    #adds deletes landmarks
    @pyqtSlot(bool)
    def changeflags(self,_):
        sender = self.sender()
        if sender == self.dryend:
            idi = 1
        elif sender == self.fcs:
            idi = 2
        elif sender == self.fce:
            idi = 3
        elif sender == self.scs:
            idi = 4
        elif sender == self.sce:
            idi = 5
        else:
            return
        if self.validatetimeorder() != 1000:
            if idi == 1:
                if self.dryend.isChecked():
                    self.dryend.setChecked(False)
            elif idi == 2:
                if self.fcs.isChecked():
                    self.fcs.setChecked(False)
            elif idi == 3:
                if self.fce.isChecked():
                    self.fce.setChecked(False)
            elif idi == 4:
                if self.scs.isChecked():
                    self.scs.setChecked(False)
            elif idi == 5:
                if self.sce.isChecked():
                    self.sce.setChecked(False)
            #ERROR time from edit boxes is not in ascending order
            strings = [QApplication.translate('Message','CHARGE'),
                       QApplication.translate('Message','DRY END'),
                       QApplication.translate('Message','FC START'),
                       QApplication.translate('Message','FC END'),
                       QApplication.translate('Message','SC START'),
                       QApplication.translate('Message','SC END'),
                       QApplication.translate('Message','DROP')]
            st = QApplication.translate('Message','Times need to be in ascending order. Please recheck {0} time').format(strings[idi])
            QMessageBox.information(self,QApplication.translate('Message','Designer Config'),st)
            return
        #idi = id index
        if self.aw.qmc.timeindex[idi]:
            #ERASE mark point
            self.aw.qmc.currentx = self.aw.qmc.timex[self.aw.qmc.timeindex[idi]]
            self.aw.qmc.currenty = self.aw.qmc.temp2[self.aw.qmc.timeindex[idi]]
            self.aw.qmc.removepoint()
        else:
            #ADD mark point
            if idi == 1:
                timez = stringtoseconds(str(self.Edit1.text())) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
                bt = float(str(self.Edit1bt.text()))
                et = float(str(self.Edit1et.text()))
            if idi == 2:
                timez = stringtoseconds(str(self.Edit2.text())) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
                bt = float(str(self.Edit2bt.text()))
                et = float(str(self.Edit2et.text()))
            if idi == 3:
                timez = stringtoseconds(str(self.Edit3.text())) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
                bt = float(str(self.Edit3bt.text()))
                et = float(str(self.Edit3et.text()))
            if idi == 4:
                timez = stringtoseconds(str(self.Edit4.text())) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
                bt = float(str(self.Edit4bt.text()))
                et = float(str(self.Edit4et.text()))
            if idi == 5:
                timez = stringtoseconds(str(self.Edit5.text())) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
                bt = float(str(self.Edit5bt.text()))
                et = float(str(self.Edit5et.text()))
            self.aw.qmc.currentx = timez
            self.aw.qmc.currenty = bt
            newindex = self.aw.qmc.addpoint(manual=False)
            self.aw.qmc.timeindex[idi] = newindex
            self.aw.qmc.temp2[self.aw.qmc.timeindex[idi]] = bt
            self.aw.qmc.temp1[self.aw.qmc.timeindex[idi]] = et
            self.aw.qmc.xaxistosm(redraw=False)
            self.aw.qmc.redrawdesigner()

class pointDlg(ArtisanDialog):
    def __init__(self,parent = None, aw = None, values = None):
        super().__init__(parent, aw)
        if values is None:
            values = [0,0]
        else:
            self.values = values
        self.setWindowTitle(QApplication.translate('Form Caption','Add Point'))
        self.tempEdit = QLineEdit(str(int(round(self.values[1]))))
        self.tempEdit.setValidator(QIntValidator(0, 999, self.tempEdit))
        self.tempEdit.setFocus()
        self.tempEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        templabel = QLabel(QApplication.translate('Label', 'temp'))
        regextime = QRegularExpression(r'^-?[0-9]?[0-9]?[0-9]:[0-5][0-9]$')
        self.timeEdit = QLineEdit(stringfromseconds(self.values[0],leadingzero=False))
        self.timeEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.timeEdit.setValidator(QRegularExpressionValidator(regextime,self))
        timelabel = QLabel(QApplication.translate('Label', 'time'))

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.return_values)
        self.dialogbuttons.rejected.connect(self.reject)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)
        grid = QGridLayout()
        grid.addWidget(timelabel,0,0)
        grid.addWidget(self.timeEdit,0,1)
        grid.addWidget(templabel,1,0)
        grid.addWidget(self.tempEdit,1,1)
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(grid)
        mainLayout.addStretch()
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
        self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok).setFocus()

    @pyqtSlot()
    def return_values(self):
        self.values[0] = stringtoseconds(str(self.timeEdit.text()))
        self.values[1] = float(self.tempEdit.text())
        self.accept()
