#!/usr/bin/env python3

# ABOUT
# Artisan Alarms Dialog

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2020

import os
import sys
import prettytable

from artisanlib.util import deltaLabelUTF8#, stringfromseconds, stringtoseconds
from artisanlib.dialogs import ArtisanResizeablDialog
from artisanlib.widgets import (MyQComboBox, MyTableWidgetItemNumber, MyTableWidgetItemQCheckBox,
                                MyTableWidgetItemQComboBox, MyTableWidgetItemQLineEdit, MyTableWidgetItemQTime)

from help import alarms_help

from PyQt5.QtCore import (Qt, pyqtSlot, QSettings)#, QRegularExpression)
from PyQt5.QtGui import QColor, QIntValidator#, QRegularExpressionValidator
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QComboBox, QDialogButtonBox,
            QTableWidget, QHBoxLayout, QVBoxLayout, QCheckBox, QPushButton, QSizePolicy, QSpinBox,
            QTableWidgetSelectionRange, QTimeEdit, QTabWidget, QGridLayout, QGroupBox)

class AlarmDlg(ArtisanResizeablDialog):
    def __init__(self, parent = None, aw = None, activeTab = 0):
        super(AlarmDlg,self).__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate("Form Caption","Alarms",None))
        self.helpdialog = None

        # restore window position
        settings = QSettings()
        if settings.contains("AlarmsGeometry"):
            self.restoreGeometry(settings.value("AlarmsGeometry"))
        
        #table for alarms
        self.alarmtable = QTableWidget()
        self.createalarmtable()
        self.alarmtable.itemSelectionChanged.connect(self.selectionChanged)
        allonButton = QPushButton(QApplication.translate("Button","All On",None))
        allonButton.clicked.connect(self.alarmsAllOn)
        allonButton.setFocusPolicy(Qt.NoFocus)
        alloffButton = QPushButton(QApplication.translate("Button","All Off",None))
        alloffButton.clicked.connect(self.alarmsAllOff)
        alloffButton.setFocusPolicy(Qt.NoFocus)
        addButton = QPushButton(QApplication.translate("Button","Add",None))
        addButton.clicked.connect(self.addalarm)
        addButton.setMinimumWidth(80)
        addButton.setFocusPolicy(Qt.NoFocus)   
        
        self.insertButton = QPushButton(QApplication.translate("Button","Insert",None))
        self.insertButton.clicked.connect(self.insertalarm)
        self.insertButton.setMinimumWidth(80)
        self.insertButton.setFocusPolicy(Qt.NoFocus)
        self.insertButton.setEnabled(False)
                     
        deleteButton = QPushButton(QApplication.translate("Button","Delete",None))
        deleteButton.clicked.connect(self.deletealarm)
        deleteButton.setMinimumWidth(80)
        deleteButton.setFocusPolicy(Qt.NoFocus)

        self.copyalarmTableButton = QPushButton(QApplication.translate("Button", "Copy Table",None))
        self.copyalarmTableButton.setToolTip(QApplication.translate("Tooltip","Copy table to clipboard, OPTION or ALT click for tabular text",None))
        self.copyalarmTableButton.setFocusPolicy(Qt.NoFocus)
        self.copyalarmTableButton.clicked.connect(self.copyAlarmTabletoClipboard)

        importButton = QPushButton(QApplication.translate("Button","Load",None))
        importButton.clicked.connect(self.importalarms)
        importButton.setMinimumWidth(80)
        importButton.setFocusPolicy(Qt.NoFocus)
        exportButton = QPushButton(QApplication.translate("Button","Save",None))
        exportButton.clicked.connect(self.exportalarms)
        exportButton.setMinimumWidth(80)
        exportButton.setFocusPolicy(Qt.NoFocus)
        
        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.closealarms)
        self.dialogbuttons.removeButton(self.dialogbuttons.button(QDialogButtonBox.Cancel))
        
        helpDialogButton = QDialogButtonBox()
        helpButton = helpDialogButton.addButton(QDialogButtonBox.Help)
        self.setButtonTranslations(helpButton,"Help",QApplication.translate("Button","Help", None))
        helpButton.setToolTip(QApplication.translate("Tooltip","Show help",None))
        helpButton.setFocusPolicy(Qt.NoFocus)
        helpButton.setMinimumWidth(80)
        helpButton.clicked.connect(self.showAlarmbuttonhelp)
        clearButton = QPushButton(QApplication.translate("Button","Clear",None))
        clearButton.setToolTip(QApplication.translate("Tooltip","Clear alarms table",None))
        clearButton.setFocusPolicy(Qt.NoFocus)
        clearButton.setMinimumWidth(80)
        clearButton.clicked.connect(self.clearalarms)
        self.loadAlarmsFromProfile = QCheckBox(QApplication.translate("CheckBox", "Load from profile",None))
        self.loadAlarmsFromProfile.setChecked(self.aw.qmc.loadalarmsfromprofile)
        self.loadAlarmsFromBackground = QCheckBox(QApplication.translate("CheckBox", "Load from background",None))
        self.loadAlarmsFromBackground.setChecked(self.aw.qmc.loadalarmsfrombackground)
        
        self.popupTimoutSpinBox = QSpinBox()
        self.popupTimoutSpinBox.setSuffix("s")
        self.popupTimoutSpinBox.setSingleStep(1)
        self.popupTimoutSpinBox.setRange(0,120)
        self.popupTimoutSpinBox.setAlignment(Qt.AlignRight)
        self.popupTimoutSpinBox.setValue(self.aw.qmc.alarm_popup_timout)
        popupTimeoutLabel = QLabel(QApplication.translate("Label", "Pop Up Timeout",None))
        
        alarmLabelLabel = QLabel(QApplication.translate("Label", "Label",None))
        self.alarmLabelEdit = QLineEdit(self.aw.qmc.alarmsetlabel)
                
        self.alarmsfile = QLabel(self.aw.qmc.alarmsfile)
        self.alarmsfile.setAlignment(Qt.AlignLeft)
        self.alarmsfile.setMinimumWidth(300)
        self.alarmsfile.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Preferred)
        tablelayout = QVBoxLayout()
        buttonlayout = QHBoxLayout()
        okbuttonlayout = QHBoxLayout()
        tablelayout.addWidget(self.alarmtable)
        buttonlayout.addWidget(addButton)
        buttonlayout.addWidget(self.insertButton)
        buttonlayout.addWidget(deleteButton)
        buttonlayout.addWidget(self.copyalarmTableButton)
        buttonlayout.addStretch()
        buttonlayout.addSpacing(10)
        buttonlayout.addWidget(allonButton)
        buttonlayout.addWidget(alloffButton)
        buttonlayout.addStretch()
        buttonlayout.addSpacing(10)
        buttonlayout.addWidget(importButton)
        buttonlayout.addWidget(exportButton)
        buttonlayout.addStretch()
        buttonlayout.addSpacing(15)
        buttonlayout.addWidget(clearButton)
        buttonlayout.addStretch()
        buttonlayout.addSpacing(15)
        buttonlayout.addWidget(helpButton)
        confButtonLayout = QHBoxLayout()
        confButtonLayout.addWidget(self.loadAlarmsFromProfile)
        confButtonLayout.addSpacing(10)
        confButtonLayout.addWidget(self.loadAlarmsFromBackground)
        confButtonLayout.addSpacing(25)
        confButtonLayout.addWidget(popupTimeoutLabel)
        confButtonLayout.addWidget(self.popupTimoutSpinBox)
        confButtonLayout.addSpacing(25)
        confButtonLayout.addWidget(alarmLabelLabel)
        confButtonLayout.addWidget(self.alarmLabelEdit)
        
        okbuttonlayout.addSpacing(5)
        okbuttonlayout.addWidget(self.alarmsfile)
        okbuttonlayout.addWidget(self.dialogbuttons)
        
        ## alarm sets
        alarmSetListLabel = QLabel(QApplication.translate("Label","Alarm Sets", None))
        transferalarmsetbutton = QPushButton(QApplication.translate("Button","<< Store Alarm Set", None))
        transferalarmsetbutton.setFocusPolicy(Qt.NoFocus)
        setalarmsetbutton = QPushButton(QApplication.translate("Button","Activate Alarm Set >>", None))
        setalarmsetbutton.setFocusPolicy(Qt.NoFocus)
        transferalarmesetcurrentLabel = QLabel(QApplication.translate("Label","Current Alarm Set", None))
        self.transferalarmesetcurrentset = QLineEdit(self.aw.qmc.alarmsetlabel)
        self.transferalarmsetcombobox = QComboBox()
        self.transferalarmsetcombobox.setFocusPolicy(Qt.NoFocus)
        # next line needed to avoid truncation of entries on Mac OS X under Qt 5.12.1-5.12.3
        # https://bugreports.qt.io/browse/QTBUG-73653
        self.transferalarmsetcombobox.setMinimumWidth(120)
        
        self.setAlarmSetLabels()
        
        transferalarmsetbutton.clicked.connect(self.setAlarmSet)        
        setalarmsetbutton.clicked.connect(self.setAlarmTable)

#        backupbutton = QPushButton(QApplication.translate("Button","Save", None))
#        backupbutton.setFocusPolicy(Qt.NoFocus)
#        restorebutton = QPushButton(QApplication.translate("Button","Load", None))
#        restorebutton.setFocusPolicy(Qt.NoFocus)
#        backupbutton.setToolTip(QApplication.translate("Tooltip","Backup all alarm sets to a text file",None))
#        restorebutton.setToolTip(QApplication.translate("Tooltip","Restore all alarm sets from a text file",None))
#        backupbutton.setMaximumWidth(140)
#        restorebutton.setMaximumWidth(140)
#        
#        backupbutton.clicked.connect(self.backupalarmsets)
#        restorebutton.clicked.connect(self.restorealarmsets)
                    
        alarmsetGrid = QGridLayout()
        alarmsetGrid.addWidget(alarmSetListLabel,1,0)
        alarmsetGrid.addWidget(transferalarmsetbutton,0,2)
        alarmsetGrid.addWidget(self.transferalarmsetcombobox,1,1)
        alarmsetGrid.addWidget(transferalarmesetcurrentLabel,1,3)
        alarmsetGrid.addWidget(self.transferalarmesetcurrentset,1,4)
        alarmsetGrid.addWidget(setalarmsetbutton,2,2)
        alarmsetBox = QHBoxLayout()
        alarmsetBox.addSpacing(30)
        alarmsetBox.addLayout(alarmsetGrid)
        alarmsetBox.addStretch()
        alarmsetManagementBox = QVBoxLayout()
        alarmsetManagementBox.addLayout(alarmsetBox)
        alarmsetGroupLayout = QGroupBox(QApplication.translate("GroupBox","Management",None))
        alarmsetGroupLayout.setLayout(alarmsetManagementBox)
#        alarmsetButtons = QHBoxLayout()
#        alarmsetButtons.addStretch()
#        alarmsetButtons.addWidget(restorebutton)
#        alarmsetButtons.addWidget(backupbutton)

        #tab layout
        self.TabWidget = QTabWidget()

        tab1layout = QVBoxLayout()
        tab1layout.addLayout(tablelayout)
        tab1layout.addLayout(buttonlayout)
        tab1layout.addLayout(confButtonLayout)
        tab1layout.setSpacing(5)
        tab1layout.setContentsMargins(2, 10, 2, 2)

        C1Widget = QWidget()
        C1Widget.setLayout(tab1layout)
        self.TabWidget.addTab(C1Widget,QApplication.translate("Tab","Alarm Table",None))
        C1Widget.setContentsMargins(5, 0, 5, 0)
        
        tab2layout = QVBoxLayout()
        tab2layout.addWidget(alarmsetGroupLayout)
        
        C2Widget = QWidget()
        C2Widget.setLayout(tab2layout)
        self.TabWidget.addTab(C2Widget,QApplication.translate("Tab","Alarm Sets",None))
        C2Widget.setContentsMargins(5, 0, 5, 0)
        
        self.TabWidget.setCurrentIndex(activeTab)
        self.TabWidget.currentChanged.connect(self.tabSwitched)

        mainlayout = QVBoxLayout()
        mainlayout.setSpacing(5)
        mainlayout.setContentsMargins(5, 15, 5, 5)
        mainlayout.addWidget(self.TabWidget)
        mainlayout.addLayout(okbuttonlayout)
        self.setLayout(mainlayout)
        self.dialogbuttons.button(QDialogButtonBox.Ok).setFocus()

    def setAlarmSetLabels(self):
        alarmset_labels = []
        for i in range(self.aw.qmc.alarmsets_count):
            alarmset = self.aw.qmc.getAlarmSet(i)
            if alarmset is not None:
                alarmset_labels.append("{} {}".format(str(i),alarmset[0]))
        self.transferalarmsetcombobox.clear()
        self.transferalarmsetcombobox.addItems(alarmset_labels)
        self.transferalarmsetcombobox.setCurrentIndex(-1)


    # transfers the alarm table to the selected alarm set
    @pyqtSlot(bool)
    def setAlarmSet(self,_):
        i = self.transferalarmsetcombobox.currentIndex()
        if i >= 0 and i < len(self.aw.qmc.alarmsets):
            self.aw.qmc.alarmsetlabel = self.transferalarmesetcurrentset.text()
            self.transferalarmesetcurrentset.setText(self.aw.qmc.alarmsetlabel)
            # we clear the alarmsfile as we overwrite here from an alarmset
            self.aw.qmc.alarmsfile = ""
            self.alarmsfile.setText(self.aw.qmc.alarmsfile)
            self.aw.qmc.setAlarmSet(i,
                self.aw.qmc.makeAlarmSet(
                    self.aw.qmc.alarmsetlabel,
                    self.aw.qmc.alarmflag[:],
                    self.aw.qmc.alarmguard[:],
                    self.aw.qmc.alarmnegguard[:],
                    self.aw.qmc.alarmtime[:],
                    self.aw.qmc.alarmoffset[:],
                    self.aw.qmc.alarmsource[:],
                    self.aw.qmc.alarmcond[:],
                    self.aw.qmc.alarmtemperature[:],
                    self.aw.qmc.alarmaction[:],
                    self.aw.qmc.alarmbeep[:],
                    self.aw.qmc.alarmstrings[:]))
            self.setAlarmSetLabels()
    
    # transfers the selected alarm set to the alarm table
    @pyqtSlot(bool)
    def setAlarmTable(self,_):
        i = self.transferalarmsetcombobox.currentIndex()
        if i >= 0 and i < len(self.aw.qmc.alarmsets):
            self.aw.qmc.selectAlarmSet(i)
            self.transferalarmesetcurrentset.setText(self.aw.qmc.alarmsetlabel)
            self.transferalarmsetcombobox.setCurrentIndex(-1)
    
    @pyqtSlot(int)
    def tabSwitched(self,i):
        if i == 0:
            # Alarm Table
            self.aw.qmc.alarmsetlabel = self.transferalarmesetcurrentset.text()
            self.alarmLabelEdit.setText(self.aw.qmc.alarmsetlabel)
            self.createalarmtable()
        elif i == 1:
            # Alarm Sets
            # save column widths
            self.aw.qmc.alarmtablecolumnwidths = [self.alarmtable.columnWidth(c) for c in range(self.alarmtable.columnCount())]
            # establish alarm table
            self.savealarms()
            # we update the current alarmset label
            self.aw.qmc.alarmsetlabel = self.alarmLabelEdit.text()
            self.transferalarmesetcurrentset.setText(self.aw.qmc.alarmsetlabel)

    @pyqtSlot()
    def selectionChanged(self):
        selected = self.alarmtable.selectedRanges()
        if selected and len(selected) > 0:
            self.insertButton.setEnabled(True)	
        else:	
            self.insertButton.setEnabled(False)
            
    def deselectAll(self):
        selected = self.alarmtable.selectedRanges()
        if selected and len(selected) > 0:
            self.alarmtable.setRangeSelected(selected[0],False)

    @pyqtSlot(bool)
    def clearalarms(self):
        self.aw.qmc.alarmtablecolumnwidths = [self.alarmtable.columnWidth(c) for c in range(self.alarmtable.columnCount())]
        self.aw.qmc.alarmsfile = ""
        self.alarmsfile.setText(self.aw.qmc.alarmsfile)
        self.aw.qmc.alarmflag = []
        self.aw.qmc.alarmguard = []
        self.aw.qmc.alarmnegguard = []
        self.aw.qmc.alarmtime = []
        self.aw.qmc.alarmoffset = []
        self.aw.qmc.alarmcond = []
        self.aw.qmc.alarmstate = []
        self.aw.qmc.alarmsource = []
        self.aw.qmc.alarmtemperature = []
        self.aw.qmc.alarmaction = []
        self.aw.qmc.alarmbeep = []
        self.aw.qmc.alarmstrings = []
        self.alarmtable.setSortingEnabled(False)
        self.alarmtable.setRowCount(0)
        self.alarmtable.setSortingEnabled(True)
        self.aw.qmc.alarmsetlabel = ""
        self.alarmLabelEdit.setText("")

    @pyqtSlot(bool)
    def alarmsAllOn(self,_):
        self.alarmson(1)

    @pyqtSlot(bool)
    def alarmsAllOff(self,_):
        self.alarmson(0)
    
    def alarmson(self,flag):
        for i in range(len(self.aw.qmc.alarmflag)):
            if flag == 1:
                self.aw.qmc.alarmflag[i] = 1
            else:
                self.aw.qmc.alarmflag[i] = 0
        self.createalarmtable()

    @pyqtSlot(bool)
    def addalarm(self,_):
        alarm_flag = 1
        alarm_guard = -1
        alarm_negguard = -1
        alarm_time = -1
        alarm_offset = 0
        alarm_cond = 1
        alarm_state = -1
        alarm_source = 1
        alarm_temperature = 500.
        alarm_action = 0
        alarm_beep = 0
        alarm_string = QApplication.translate("Label","Enter description",None)
        selected = self.alarmtable.selectedRanges()
        if len(selected) > 0:
            self.savealarms() # we first "save" the alarmtable to be able to pick up the values of the selected row
            selected_idx = selected[0].topRow()
            selected_idx = int(self.alarmtable.item(selected_idx,0).text()) -1 # we derref the rows number that might be different per sorting order
            try:
                alarm_flag = self.aw.qmc.alarmflag[selected_idx]
                alarm_guard = self.aw.qmc.alarmguard[selected_idx]
                alarm_negguard = self.aw.qmc.alarmnegguard[selected_idx]
                alarm_time = self.aw.qmc.alarmtime[selected_idx]
                alarm_offset = self.aw.qmc.alarmoffset[selected_idx]
                alarm_cond = self.aw.qmc.alarmcond[selected_idx]
                alarm_state = self.aw.qmc.alarmstate[selected_idx]
                alarm_source = self.aw.qmc.alarmsource[selected_idx]
                alarm_temperature = self.aw.qmc.alarmtemperature[selected_idx]
                alarm_action = self.aw.qmc.alarmaction[selected_idx]
                alarm_beep = self.aw.qmc.alarmbeep[selected_idx]
                alarm_string= self.aw.qmc.alarmstrings[selected_idx]
            except:
                pass
        self.aw.qmc.alarmflag.append(alarm_flag)
        self.aw.qmc.alarmguard.append(alarm_guard)
        self.aw.qmc.alarmnegguard.append(alarm_negguard)
        self.aw.qmc.alarmtime.append(alarm_time)
        self.aw.qmc.alarmoffset.append(alarm_offset)
        self.aw.qmc.alarmcond.append(alarm_cond)
        self.aw.qmc.alarmstate.append(alarm_state)
        self.aw.qmc.alarmsource.append(alarm_source)
        self.aw.qmc.alarmtemperature.append(alarm_temperature)
        self.aw.qmc.alarmaction.append(alarm_action)
        self.aw.qmc.alarmbeep.append(alarm_beep)
        self.aw.qmc.alarmstrings.append(alarm_string)
        self.alarmtable.setSortingEnabled(False)
        nalarms = self.alarmtable.rowCount()
        self.alarmtable.setRowCount(nalarms + 1)
        self.setalarmtablerow(nalarms)
        
        header = self.alarmtable.horizontalHeader()
        header.setStretchLastSection(True)
        
        if len(self.aw.qmc.alarmflag) == 1: # only for the first entry we apply some default column width
            # improve width of Qlineedit columns
            self.alarmtable.resizeColumnsToContents()
            self.alarmtable.setColumnWidth(1,50)
            self.alarmtable.setColumnWidth(2,50)
            self.alarmtable.setColumnWidth(3,50)
            self.alarmtable.setColumnWidth(4,90)
            self.alarmtable.setColumnWidth(5,50)
            self.alarmtable.setColumnWidth(6,70)
            self.alarmtable.setColumnWidth(7,90)
            self.alarmtable.setColumnWidth(8,50)
            self.alarmtable.setColumnWidth(9,90)
            # remember the columnwidth
            for i in range(len(self.aw.qmc.alarmtablecolumnwidths)):
                try:
                    self.alarmtable.setColumnWidth(i,self.aw.qmc.alarmtablecolumnwidths[i])
                except:
                    pass
            self.alarmtable.setSortingEnabled(True)
        else:
            self.deselectAll()
            # select newly added row i.e. the last one
            self.alarmtable.setRangeSelected(QTableWidgetSelectionRange(nalarms,0,nalarms,self.alarmtable.columnCount()-1),True)
            header.setStretchLastSection(True)
            self.markNotEnabledAlarmRows()
            self.alarmtable.setSortingEnabled(True)
#        self.alarmtable.viewport().update()
#        self.alarmtable.update()
#        self.repaint()

    @pyqtSlot(bool)
    def insertalarm(self,_):
        self.alarmtable.setSortingEnabled(False)
        nalarms = self.alarmtable.rowCount()
        if nalarms:
            alarm_flag = 1
            alarm_guard = -1
            alarm_negguard = -1
            alarm_time = -1
            alarm_offset = 0
            alarm_cond = 1
            alarm_state = 0
            alarm_source = 1
            alarm_temperature = 500.
            alarm_action = 0
            alarm_beep = 0
            alarm_string = QApplication.translate("Label","Enter description",None)
            # check for selection
            selected = self.alarmtable.selectedRanges()
            if selected and len(selected) > 0:
                self.savealarms() # we first "save" the alarmtable to be able to pick up the values of the selected row
                selected_row = selected[0].topRow()
                selected_row = int(self.alarmtable.item(selected_row,0).text()) -1 # we derref the rows number that might be different per sorting order
                try:
                    alarm_flag = self.aw.qmc.alarmflag[selected_row]
                    alarm_guard = self.aw.qmc.alarmguard[selected_row]
                    alarm_negguard = self.aw.qmc.alarmnegguard[selected_row]
                    alarm_time = self.aw.qmc.alarmtime[selected_row]
                    alarm_offset = self.aw.qmc.alarmoffset[selected_row]
                    alarm_cond = self.aw.qmc.alarmcond[selected_row]
                    alarm_state = self.aw.qmc.alarmstate[selected_row]
                    alarm_source = self.aw.qmc.alarmsource[selected_row]
                    alarm_temperature = self.aw.qmc.alarmtemperature[selected_row]
                    alarm_action = self.aw.qmc.alarmaction[selected_row]
                    alarm_beep = self.aw.qmc.alarmbeep[selected_row]
                    alarm_string= self.aw.qmc.alarmstrings[selected_row]
                except:
                    pass  
                self.aw.qmc.alarmflag.insert(selected_row,alarm_flag)
                self.aw.qmc.alarmguard.insert(selected_row,alarm_guard)
                self.aw.qmc.alarmnegguard.insert(selected_row,alarm_negguard)
                self.aw.qmc.alarmtime.insert(selected_row,alarm_time)
                self.aw.qmc.alarmoffset.insert(selected_row,alarm_offset)
                self.aw.qmc.alarmcond.insert(selected_row,alarm_cond)
                self.aw.qmc.alarmstate.insert(selected_row,alarm_state)
                self.aw.qmc.alarmsource.insert(selected_row,alarm_source)
                self.aw.qmc.alarmtemperature.insert(selected_row,alarm_temperature)
                self.aw.qmc.alarmaction.insert(selected_row,alarm_action)
                self.aw.qmc.alarmbeep.insert(selected_row,alarm_beep)
                self.aw.qmc.alarmstrings.insert(selected_row,alarm_string)
                self.alarmtable.insertRow(selected_row)
                self.setalarmtablerow(selected_row)
#                self.alarmtable.resizeColumnsToContents()
#                #  improve width of Qlineedit columns
#                self.alarmtable.setColumnWidth(2,50)
#                self.alarmtable.setColumnWidth(3,50)
#                self.alarmtable.setColumnWidth(5,50)
#                self.alarmtable.setColumnWidth(6,80)
#                self.alarmtable.setColumnWidth(8,40)
                header = self.alarmtable.horizontalHeader()
                header.setStretchLastSection(False)
                self.deselectAll()
                # select newly inserted item
                self.alarmtable.setRangeSelected(QTableWidgetSelectionRange(selected_row,0,selected_row,self.alarmtable.columnCount()-1),True)
                header.setStretchLastSection(True)
                self.markNotEnabledAlarmRows()
                self.alarmtable.sortItems(0, Qt.AscendingOrder) # we first have to sort the table according to the row numbers
                # we no re-number rows
                self.renumberRows()
                # we correct the IfAlarm and ButNot references to items after the inserted one
                for i in range(self.alarmtable.rowCount()):
                    guard = self.alarmtable.cellWidget(i,2)
                    try:
                        guard_value = int(str(guard.text())) - 1
                    except Exception:
                        guard_value = -1
                    if guard_value >= selected_row:
                        guard.setText(str(guard_value+2))
                    nguard = self.alarmtable.cellWidget(i,3)
                    try:
                        nguard_value = int(str(nguard.text())) - 1
                    except Exception:
                        nguard_value = -1
                    if nguard_value >= selected_row:
                        nguard.setText(str(nguard_value+2))
        self.alarmtable.setSortingEnabled(True)
        
    def renumberRows(self):
        for i in range(self.alarmtable.rowCount()):
            self.alarmtable.setItem(i, 0, MyTableWidgetItemNumber(str(i+1),i))

    @pyqtSlot(bool)
    def deletealarm(self,_):
        self.aw.qmc.alarmtablecolumnwidths = [self.alarmtable.columnWidth(c) for c in range(self.alarmtable.columnCount())]
        self.alarmtable.setSortingEnabled(False)
        nalarms = self.alarmtable.rowCount()
        if nalarms:
            # check for selection
            selected = self.alarmtable.selectedRanges()
            if selected and len(selected) > 0:
                selected_row = selected[0].topRow()
                selected_row = int(self.alarmtable.item(selected_row,0).text()) -1 # we derref the rows number that might be different per sorting order
                self.alarmtable.removeRow(selected_row)
                self.aw.qmc.alarmflag = self.aw.qmc.alarmflag[0:selected_row] + self.aw.qmc.alarmflag[selected_row + 1:]
                self.aw.qmc.alarmguard = self.aw.qmc.alarmguard[0:selected_row] + self.aw.qmc.alarmguard[selected_row + 1:]
                self.aw.qmc.alarmnegguard = self.aw.qmc.alarmnegguard[0:selected_row] + self.aw.qmc.alarmnegguard[selected_row + 1:]
                self.aw.qmc.alarmtime = self.aw.qmc.alarmtime[0:selected_row] + self.aw.qmc.alarmtime[selected_row + 1:]
                self.aw.qmc.alarmoffset = self.aw.qmc.alarmoffset[0:selected_row] + self.aw.qmc.alarmoffset[selected_row + 1:]
                self.aw.qmc.alarmcond = self.aw.qmc.alarmcond[0:selected_row] + self.aw.qmc.alarmcond[selected_row + 1:]
                self.aw.qmc.alarmstate = self.aw.qmc.alarmstate[0:selected_row] + self.aw.qmc.alarmstate[selected_row + 1:]
                self.aw.qmc.alarmsource = self.aw.qmc.alarmsource[0:selected_row] + self.aw.qmc.alarmsource[selected_row + 1:]
                self.aw.qmc.alarmtemperature = self.aw.qmc.alarmtemperature[0:selected_row] + self.aw.qmc.alarmtemperature[selected_row + 1:]
                self.aw.qmc.alarmaction = self.aw.qmc.alarmaction[0:selected_row] + self.aw.qmc.alarmaction[selected_row + 1:]
                self.aw.qmc.alarmbeep = self.aw.qmc.alarmbeep[0:selected_row] + self.aw.qmc.alarmbeep[selected_row + 1:]
                self.aw.qmc.alarmstrings = self.aw.qmc.alarmstrings[0:selected_row] + self.aw.qmc.alarmstrings[selected_row + 1:]
                self.alarmtable.setRowCount(nalarms - 1)
                self.deselectAll()
                # select row number that was just deleted
                self.alarmtable.setRangeSelected(QTableWidgetSelectionRange(selected_row,0,selected_row,self.alarmtable.columnCount()-1),True)
                self.alarmtable.sortItems(0)
                self.alarmtable.sortItems(0, Qt.AscendingOrder) # we first have to sort the table according to the row numbers
                # renumber elements
                self.renumberRows()
                # we correct the IfAlarm and ButNot references to items after the deleted one
                for i in range(self.alarmtable.rowCount()):
                    guard = self.alarmtable.cellWidget(i,2)
                    try:
                        guard_value = int(str(guard.text())) - 1
                    except Exception:
                        guard_value = -1
                    if guard_value >= selected_row:
                        guard.setText(str(guard_value))
                    nguard = self.alarmtable.cellWidget(i,3)
                    try:
                        nguard_value = int(str(nguard.text())) - 1
                    except Exception:
                        nguard_value = -1
                    if nguard_value >= selected_row:
                        nguard.setText(str(nguard_value))
            else:
                self.alarmtable.removeRow(self.alarmtable.rowCount() - 1)
                # nothing selected, we pop the last element
                self.aw.qmc.alarmflag.pop()
                self.aw.qmc.alarmguard.pop()
                self.aw.qmc.alarmnegguard.pop()
                self.aw.qmc.alarmtime.pop()
                self.aw.qmc.alarmoffset.pop()
                self.aw.qmc.alarmcond.pop()
                self.aw.qmc.alarmstate.pop()
                self.aw.qmc.alarmsource.pop()
                self.aw.qmc.alarmtemperature.pop()
                self.aw.qmc.alarmaction.pop()
                self.aw.qmc.alarmbeep.pop()
                self.aw.qmc.alarmstrings.pop()
                self.alarmtable.setRowCount(nalarms - 1)
                self.deselectAll()
                self.alarmtable.sortItems(0)
            self.markNotEnabledAlarmRows()
        self.alarmtable.setSortingEnabled(True)

    @pyqtSlot(bool)
    def importalarms(self,_):
        self.aw.fileImport(QApplication.translate("Message", "Load Alarms",None),self.importalarmsJSON,ext="*.alrm *.alog")

    def importalarmsJSON(self,filename):
        try:
            _,ext = os.path.splitext(filename)
            if ext == ".alrm":
                import io
                infile = io.open(filename, 'r', encoding='utf-8')
                from json import load as json_load
                alarms = json_load(infile)
                infile.close()
                self.aw.qmc.alarmsfile = filename
                self.alarmsfile.setText(self.aw.qmc.alarmsfile)
                self.aw.qmc.alarmflag = alarms["alarmflags"]
                self.aw.qmc.alarmguard = alarms["alarmguards"]
                if "alarmnegguards" in alarms:
                    self.aw.qmc.alarmnegguard = alarms["alarmnegguards"]
                else:
                    self.aw.qmc.alarmnegguard = [0]*len(self.aw.qmc.alarmflag)
                self.aw.qmc.alarmtime = alarms["alarmtimes"]
                self.aw.qmc.alarmoffset = alarms["alarmoffsets"]
                self.aw.qmc.alarmcond = alarms["alarmconds"]
                self.aw.qmc.alarmsource = alarms["alarmsources"]
                self.aw.qmc.alarmtemperature = alarms["alarmtemperatures"]
                self.aw.qmc.alarmaction = alarms["alarmactions"]
                if "alarmbeep" in alarms:
                    self.aw.qmc.alarmbeep = alarms["alarmbeep"]
                else:
                    self.aw.qmc.alarmbeep = [0]*len(self.aw.qmc.alarmflag)
                self.aw.qmc.alarmstrings = alarms["alarmstrings"]
            elif ext == ".alog":
                obj = self.aw.deserialize(filename)
                self.aw.loadAlarmsFromProfile(filename,obj)
                self.alarmsfile.setText(self.aw.qmc.alarmsfile) 
            self.aw.qmc.alarmstate = [-1]*len(self.aw.qmc.alarmflag) 
            aitems = self.buildAlarmSourceList()
            for i in range(len(self.aw.qmc.alarmsource)):
                if self.aw.qmc.alarmsource[i] + 3 >= len(aitems):
                    self.aw.qmc.alarmsource[i] = 1 # BT
            self.createalarmtable()
        except Exception as ex:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            _, _, exc_tb = sys.exc_info()
            self.aw.sendmessage(QApplication.translate("Message","Error loading alarm file", None))
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " importalarmsJSON() {0}").format(str(ex)),exc_tb.tb_lineno)

    @pyqtSlot(bool)
    def exportalarms(self,_):
        self.aw.fileExport(QApplication.translate("Message", "Save Alarms",None),"*.alrm",self.exportalarmsJSON)

    def exportalarmsJSON(self,filename):
        try:
            self.savealarms()
            alarms = {}
            alarms["alarmflags"] = self.aw.qmc.alarmflag
            alarms["alarmguards"] = self.aw.qmc.alarmguard
            alarms["alarmnegguards"] = self.aw.qmc.alarmnegguard
            alarms["alarmtimes"] = self.aw.qmc.alarmtime
            alarms["alarmoffsets"] = self.aw.qmc.alarmoffset
            alarms["alarmconds"] = self.aw.qmc.alarmcond
            alarms["alarmsources"] = self.aw.qmc.alarmsource
            alarms["alarmtemperatures"] = self.aw.qmc.alarmtemperature
            alarms["alarmactions"] = self.aw.qmc.alarmaction
            alarms["alarmbeep"] = self.aw.qmc.alarmbeep
            alarms["alarmstrings"] = list(self.aw.qmc.alarmstrings)
            outfile = open(filename, 'w')
            from json import dump as json_dump
            json_dump(alarms, outfile, ensure_ascii=True)
            outfile.write('\n')
            outfile.close()
            return True
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:",None) + " exportalarmsJSON(): {0}").format(str(ex)),exc_tb.tb_lineno)
            return False

    @pyqtSlot()
    def closealarms(self):
        self.savealarms()
        # save column widths
        self.aw.qmc.alarmtablecolumnwidths = [self.alarmtable.columnWidth(c) for c in range(self.alarmtable.columnCount())]
        
        self.aw.qmc.alarm_popup_timout = int(self.popupTimoutSpinBox.value())
        self.aw.qmc.alarmsetlabel = self.alarmLabelEdit.text()
        self.closeHelp()
        settings = QSettings()
        #save window geometry
        settings.setValue("AlarmsGeometry",self.saveGeometry())
        self.aw.closeEventSettings()
        
        self.aw.AlarmDlg_activeTab = self.TabWidget.currentIndex()
        self.accept()
    
    def closeEvent(self, _):
        self.closealarms()

    @pyqtSlot(bool)
    def restorealarmsets(self,_):
        self.aw.restorealarmsets()
        self.setAlarmSetLabels()
    
    @pyqtSlot(bool)
    def backupalarmsets(self,_):
        self.aw.backupalarmsets()
    
    def savealarms(self):
        try:
            self.alarmtable.sortItems(0)
            nalarms = self.alarmtable.rowCount()
            self.aw.qmc.loadalarmsfromprofile = self.loadAlarmsFromProfile.isChecked()
            self.aw.qmc.loadalarmsfrombackground = self.loadAlarmsFromBackground.isChecked()
            self.aw.qmc.alarmflag = [1]*nalarms
            self.aw.qmc.alarmguard = [-1]*nalarms
            self.aw.qmc.alarmnegguard = [-1]*nalarms
            self.aw.qmc.alarmtime = [-1]*nalarms
            self.aw.qmc.alarmoffset = [0]*nalarms
            self.aw.qmc.alarmcond = [1]*nalarms
            self.aw.qmc.alarmsource = [1]*nalarms
            self.aw.qmc.alarmtemperature = [500.]*nalarms
            self.aw.qmc.alarmaction = [0]*nalarms
            self.aw.qmc.alarmbeep = [0]*nalarms
            self.aw.qmc.alarmstrings = [""]*nalarms
            for i in range(nalarms):
                flag = self.alarmtable.cellWidget(i,1)
                self.aw.qmc.alarmflag[i] = int(flag.isChecked())
                guard = self.alarmtable.cellWidget(i,2)
                try:
                    guard_value = int(str(guard.text())) - 1
                except Exception:
                    guard_value = -1
                if guard_value > -1 and guard_value < nalarms:
                    self.aw.qmc.alarmguard[i] = guard_value
                else:
                    self.aw.qmc.alarmguard[i] = -1
                negguard = self.alarmtable.cellWidget(i,3)
                try:
                    negguard_value = int(str(negguard.text())) - 1
                except Exception:
                    negguard_value = -1
                if negguard_value > -1 and negguard_value < nalarms:
                    self.aw.qmc.alarmnegguard[i] = negguard_value
                else:
                    self.aw.qmc.alarmnegguard[i] = -1
                timez =  self.alarmtable.cellWidget(i,4)
                self.aw.qmc.alarmtime[i] = self.aw.qmc.menuidx2alarmtime[timez.currentIndex()]
                offset =  self.alarmtable.cellWidget(i,5)
                if offset and offset != "":
#                    self.aw.qmc.alarmoffset[i] = max(0,stringtoseconds(str(offset.text())))
                    tx = self.aw.QTime2time(offset.time())
                    self.aw.qmc.alarmoffset[i] = max(0,tx)
                atype = self.alarmtable.cellWidget(i,6)
                self.aw.qmc.alarmsource[i] = int(str(atype.currentIndex())) - 3
                cond = self.alarmtable.cellWidget(i,7)
                self.aw.qmc.alarmcond[i] = int(str(cond.currentIndex())) 
                temp = self.alarmtable.cellWidget(i,8)
                try:
                    self.aw.qmc.alarmtemperature[i] = float(self.aw.comma2dot(str(temp.text())))
                except Exception:
                    self.aw.qmc.alarmtemperature[i] = 0.0
                action = self.alarmtable.cellWidget(i,9)
                self.aw.qmc.alarmaction[i] = int(str(action.currentIndex() - 1))
                beepWidget = self.alarmtable.cellWidget(i,10)
                beep = beepWidget.layout().itemAt(1).widget()
                if beep and beep is not None:
                    self.aw.qmc.alarmbeep[i] = int(beep.isChecked())
                description = self.alarmtable.cellWidget(i,11)
                self.aw.qmc.alarmstrings[i] = description.text()
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:",None) + " savealarms(): {0}").format(str(ex)),exc_tb.tb_lineno)
            
    def buildAlarmSourceList(self):
        extra_names = []
        for i in range(len(self.aw.qmc.extradevices)):
            extra_names.append(str(i) + "xT1: " + self.aw.qmc.extraname1[i])
            extra_names.append(str(i) + "xT2: " + self.aw.qmc.extraname2[i])
        return ["",
             deltaLabelUTF8 + QApplication.translate("Label","ET",None),
             deltaLabelUTF8 + QApplication.translate("Label","BT",None),
             QApplication.translate("ComboBox","ET",None),
             QApplication.translate("ComboBox","BT",None)] + extra_names

    # creates Widget in row i of self.alarmtable and sets them to values from local dialog variables at position i
    def setalarmtablerow(self,i):
        #flag
        flagComboBox = QCheckBox()
        flagComboBox.setFocusPolicy(Qt.NoFocus)
        flagComboBox.setText(QApplication.translate("ComboBox","ON",None))
        if self.aw.qmc.alarmflag[i]:
            flagComboBox.setCheckState(Qt.Checked)
        else:
            flagComboBox.setCheckState(Qt.Unchecked)
        #guarded by alarm
        if self.aw.qmc.alarmguard[i] > -1:
            guardstr = str(self.aw.qmc.alarmguard[i] + 1)
        else:
            guardstr = "0"
        guardedit = QLineEdit(guardstr)
        guardedit.setValidator(QIntValidator(0, 999,guardedit))
        guardedit.setAlignment(Qt.AlignRight)
        #neg guarded by alarm
        if self.aw.qmc.alarmnegguard[i] > -1:
            negguardstr = str(self.aw.qmc.alarmnegguard[i] + 1)
        else:
            negguardstr = "0"
        negguardedit = QLineEdit(negguardstr)
        negguardedit.setValidator(QIntValidator(0, 999,negguardedit))
        negguardedit.setAlignment(Qt.AlignRight)
        #Effective time from
        timeComboBox = MyQComboBox()
        timeComboBox.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        timeComboBox.addItems([QApplication.translate("ComboBox","ON",None), # qmc.alarmtime 9
                               QApplication.translate("ComboBox","START",None), # qmc.alarmtime -1
                               QApplication.translate("ComboBox","CHARGE",None), # qmc.alarmtime 0
                               QApplication.translate("ComboBox","TP",None), # qmc.alarmtime 8
                               QApplication.translate("ComboBox","DRY END",None), # qmc.alarmtime 1
                               QApplication.translate("ComboBox","FC START",None), # qmc.alarmtime 2
                               QApplication.translate("ComboBox","FC END",None), # qmc.alarmtime 3
                               QApplication.translate("ComboBox","SC START",None), # qmc.alarmtime 4
                               QApplication.translate("ComboBox","SC END",None), # qmc.alarmtime 5
                               QApplication.translate("ComboBox","DROP",None), # qmc.alarmtime 6
                               QApplication.translate("ComboBox","COOL",None), # qmc.alarmtime 7
                               QApplication.translate("ComboBox","If Alarm",None)]) # qmc.alarmtime 10
        timeComboBox.setCurrentIndex(self.aw.qmc.alarmtime2menuidx[self.aw.qmc.alarmtime[i]])
        #time after selected event
#        timeoffsetedit = QLineEdit(stringfromseconds(max(0,self.aw.qmc.alarmoffset[i])))
#        timeoffsetedit.setAlignment(Qt.AlignRight)
#        regextime = QRegularExpression(r"^[0-5][0-9]:[0-5][0-9]$")
#        timeoffsetedit.setValidator(QRegularExpressionValidator(regextime,self))
        timeoffsetedit = QTimeEdit()
        timeoffsetedit.setAlignment(Qt.AlignRight)
        timeoffsetedit.setDisplayFormat("mm:ss")
        timeoffsetedit.setTime(self.aw.time2QTime(max(0,self.aw.qmc.alarmoffset[i])))
        #type/source
        typeComboBox = MyQComboBox()
        typeComboBox.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        aitems = self.buildAlarmSourceList()
        typeComboBox.addItems(aitems)
        if self.aw.qmc.alarmsource[i] + 3 < len(aitems):
            typeComboBox.setCurrentIndex(self.aw.qmc.alarmsource[i] + 3)
        else:
            typeComboBox.setCurrentIndex(3)
        #condition
        condComboBox = MyQComboBox()
        condComboBox.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        condComboBox.addItems([QApplication.translate("ComboBox","below",None),
                               QApplication.translate("ComboBox","above",None)])
        condComboBox.setCurrentIndex(self.aw.qmc.alarmcond[i])
        #temperature
        tempedit = QLineEdit(str(self.aw.float2float(self.aw.qmc.alarmtemperature[i])))
        tempedit.setAlignment(Qt.AlignRight)
        tempedit.setMaximumWidth(130)
#        tempedit.setValidator(QIntValidator(0, 999,tempedit))
        tempedit.setValidator(self.aw.createCLocaleDoubleValidator(-999.9, 999.9,1,tempedit))
        #action
        actionComboBox = MyQComboBox()
        actionComboBox.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        actionComboBox.addItems(["",
                                 QApplication.translate("ComboBox","Pop Up",None),
                                 QApplication.translate("ComboBox","Call Program",None),
                                 QApplication.translate("ComboBox","Event Button",None),
                                 QApplication.translate("ComboBox","Slider",None) + " " + self.aw.qmc.etypesf(0),
                                 QApplication.translate("ComboBox","Slider",None) + " " + self.aw.qmc.etypesf(1),
                                 QApplication.translate("ComboBox","Slider",None) + " " + self.aw.qmc.etypesf(2),
                                 QApplication.translate("ComboBox","Slider",None) + " " + self.aw.qmc.etypesf(3),
                                 QApplication.translate("ComboBox","START",None),
                                 QApplication.translate("ComboBox","DRY",None),
                                 QApplication.translate("ComboBox","FCs",None),
                                 QApplication.translate("ComboBox","FCe",None),
                                 QApplication.translate("ComboBox","SCs",None),
                                 QApplication.translate("ComboBox","SCe",None),
                                 QApplication.translate("ComboBox","DROP",None),
                                 QApplication.translate("ComboBox","COOL END",None),
                                 QApplication.translate("ComboBox","OFF",None),
                                 QApplication.translate("ComboBox","CHARGE",None),
                                 QApplication.translate("ComboBox","RampSoak ON",None),
                                 QApplication.translate("ComboBox","RampSoak OFF",None),
                                 QApplication.translate("ComboBox","PID ON",None),
                                 QApplication.translate("ComboBox","PID OFF",None),
                                 QApplication.translate("ComboBox","SV",None),
                                 QApplication.translate("ComboBox","Playback ON",None),
                                 QApplication.translate("ComboBox","Playback OFF",None),
                                 QApplication.translate("ComboBox","Set Canvas Color",None),
                                 QApplication.translate("ComboBox","Reset Canvas Color",None)])
        actionComboBox.setCurrentIndex(self.aw.qmc.alarmaction[i] + 1)
        #beep
        beepWidget = QWidget()
        beepComboBox = QCheckBox()
        beepComboBox.setFocusPolicy(Qt.NoFocus)
        beepLayout = QHBoxLayout()
        beepLayout.addStretch()
        beepLayout.addWidget(beepComboBox)
        beepLayout.addSpacing(6);        
        beepLayout.addStretch()
        beepLayout.setContentsMargins(0,0,0,0)
        beepLayout.setSpacing(0)
        beepWidget.setLayout(beepLayout)
        if len(self.aw.qmc.alarmbeep) > i and self.aw.qmc.alarmbeep[i]:
            beepComboBox.setCheckState(Qt.Checked)
        else:
            beepComboBox.setCheckState(Qt.Unchecked)
        #text description
        descriptionedit = QLineEdit(self.aw.qmc.alarmstrings[i])
        descriptionedit.setCursorPosition(0)
        self.alarmtable.setItem(i, 0, MyTableWidgetItemNumber(str(i+1),i))
        self.alarmtable.setCellWidget(i,1,flagComboBox)
        self.alarmtable.setItem(i, 1, MyTableWidgetItemQCheckBox(flagComboBox))
        self.alarmtable.setCellWidget(i,2,guardedit)
        self.alarmtable.setItem(i, 2, MyTableWidgetItemQLineEdit(guardedit))
        self.alarmtable.setCellWidget(i,3,negguardedit)
        self.alarmtable.setItem(i, 3, MyTableWidgetItemQLineEdit(negguardedit))
        self.alarmtable.setCellWidget(i,4,timeComboBox)
        self.alarmtable.setItem(i, 4, MyTableWidgetItemQComboBox(timeComboBox))
        self.alarmtable.setCellWidget(i,5,timeoffsetedit)
#        self.alarmtable.setItem(i, 5, MyTableWidgetItemQLineEdit(timeoffsetedit))
        self.alarmtable.setItem(i, 5, MyTableWidgetItemQTime(timeoffsetedit))
        self.alarmtable.setCellWidget(i,6,typeComboBox)
        self.alarmtable.setItem(i, 6, MyTableWidgetItemQComboBox(typeComboBox))
        self.alarmtable.setCellWidget(i,7,condComboBox)
        self.alarmtable.setItem(i, 7, MyTableWidgetItemQComboBox(condComboBox))
        self.alarmtable.setCellWidget(i,8,tempedit)
        self.alarmtable.setItem(i, 8, MyTableWidgetItemQLineEdit(tempedit))
        self.alarmtable.setCellWidget(i,9,actionComboBox)
        self.alarmtable.setItem(i, 9, MyTableWidgetItemQComboBox(actionComboBox))
        self.alarmtable.setCellWidget(i,10,beepWidget)
        self.alarmtable.setItem(i, 10, MyTableWidgetItemQCheckBox(beepWidget.layout().itemAt(1).widget()))
        self.alarmtable.setCellWidget(i,11,descriptionedit)
        self.alarmtable.setItem(i, 11, MyTableWidgetItemQLineEdit(descriptionedit))
        

    # puts a gray background on alarm rows that have already been fired
    def markNotEnabledAlarmRows(self):
        for i in range(self.alarmtable.rowCount()):
            for j in range(11):
                try:
                    if self.aw.qmc.alarmstate[i] != -1:
                        #self.alarmtable.setItem(i,j,QTableWidgetItem())
                        self.alarmtable.item(i,j).setBackground(QColor(191, 191, 191))
                except:
                    pass

    def createalarmtable(self):
        try:
            self.alarmtable.clear()
            self.alarmtable.setTabKeyNavigation(True)
            self.alarmtable.setColumnCount(12)
            self.alarmtable.setHorizontalHeaderLabels([QApplication.translate("Table","Nr",None),
                                                           QApplication.translate("Table","Status",None),
                                                           QApplication.translate("Table","If Alarm",None),
                                                           QApplication.translate("Table","But Not",None),
                                                           QApplication.translate("Table","From",None),
                                                           QApplication.translate("Table","Time",None),
                                                           QApplication.translate("Table","Source",None),
                                                           QApplication.translate("Table","Condition",None),
                                                           QApplication.translate("Table","Value",None),
                                                           QApplication.translate("Table","Action",None),
                                                           QApplication.translate("Table","Beep",None),
                                                           QApplication.translate("Table","Description",None)])
            self.alarmtable.setAlternatingRowColors(True)
            self.alarmtable.setEditTriggers(QTableWidget.NoEditTriggers)
            self.alarmtable.setSelectionBehavior(QTableWidget.SelectRows)
            self.alarmtable.setSelectionMode(QTableWidget.SingleSelection)
            self.alarmtable.setShowGrid(True)
            nalarms = len(self.aw.qmc.alarmtemperature)
            self.alarmtable.verticalHeader().setSectionResizeMode(2)
            self.alarmtable.verticalHeader().setVisible(False)
            self.alarmtable.setSortingEnabled(False)
            self.alarmtable.setRowCount(nalarms)
            #populate table
            for i in range(nalarms):
                self.setalarmtablerow(i)
            header = self.alarmtable.horizontalHeader()
            header.setStretchLastSection(True)
            self.alarmtable.resizeColumnsToContents()
            # remember the columnwidth
            for i in range(len(self.aw.qmc.alarmtablecolumnwidths)):
                try:
                    w = self.aw.qmc.alarmtablecolumnwidths[i]
                    if i == 6:
                        w = max(80,w)
                    self.alarmtable.setColumnWidth(i,w)
                except:
                    pass
            self.markNotEnabledAlarmRows()
            self.alarmtable.setSortingEnabled(True)
            self.alarmtable.sortItems(0)
            
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " createalarmtable() {0}").format(str(ex)),exc_tb.tb_lineno)

    @pyqtSlot(bool)
    def copyAlarmTabletoClipboard(self,_=False):
        nrows = self.alarmtable.rowCount() 
        ncols = self.alarmtable.columnCount()
        clipboard = ""
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.AltModifier:  #alt click
            tbl = prettytable.PrettyTable()
            fields = []
            for c in range(ncols):
                fields.append(self.alarmtable.horizontalHeaderItem(c).text())
            tbl.field_names = fields
            for r in range(nrows):
                rows = []
                rows.append(self.alarmtable.item(r,0).text())
                rows.append(str(self.alarmtable.cellWidget(r,1).isChecked()))
                rows.append(self.alarmtable.cellWidget(r,2).text())
                rows.append(self.alarmtable.cellWidget(r,3).text())
                rows.append(self.alarmtable.cellWidget(r,4).currentText())
#                rows.append(self.alarmtable.cellWidget(r,5).text())
                rows.append(self.alarmtable.cellWidget(r,5).time().toString("mm:ss"))
                rows.append(self.alarmtable.cellWidget(r,6).currentText())
                rows.append(self.alarmtable.cellWidget(r,7).currentText())
                rows.append(self.alarmtable.cellWidget(r,8).text())
                rows.append(self.alarmtable.cellWidget(r,9).currentText())
                rows.append(str(self.alarmtable.cellWidget(r,10).layout().itemAt(1).widget().isChecked()))
                rows.append(self.alarmtable.cellWidget(r,11).text())
                tbl.add_row(rows)
            clipboard = tbl.get_string()
        else:
            for c in range(ncols):
                clipboard += self.alarmtable.horizontalHeaderItem(c).text()
                if c != (ncols-1):
                    clipboard += '\t'
            clipboard += '\n'
            for r in range(nrows):
                clipboard += self.alarmtable.item(r,0).text() + '\t'
                clipboard += str(self.alarmtable.cellWidget(r,1).isChecked()) + '\t'
                clipboard += self.alarmtable.cellWidget(r,2).text() + '\t'
                clipboard += self.alarmtable.cellWidget(r,3).text() + '\t'
                clipboard += self.alarmtable.cellWidget(r,4).currentText() + '\t'
#                clipboard += self.alarmtable.cellWidget(r,5).text() + '\t'
                clipboard += self.alarmtable.cellWidget(r,5).time().toString("mm:ss") + '\t'
                clipboard += self.alarmtable.cellWidget(r,6).currentText() + '\t'
                clipboard += self.alarmtable.cellWidget(r,7).currentText() + '\t'
                clipboard += self.alarmtable.cellWidget(r,8).text() + '\t'
                clipboard += self.alarmtable.cellWidget(r,9).currentText() + '\t'
                clipboard += str(self.alarmtable.cellWidget(r,10).layout().itemAt(1).widget().isChecked()) + '\t'
                clipboard += self.alarmtable.cellWidget(r,11).text() + '\n'
        # copy to the system clipboard
        sys_clip = QApplication.clipboard()
        sys_clip.setText(clipboard)
        self.aw.sendmessage(QApplication.translate("Message","Alarm table copied to clipboard",None))

    @pyqtSlot(bool)
    def showAlarmbuttonhelp(self,_=False):
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate("Form Caption","Alarms Help",None),
                alarms_help.content())

    def closeHelp(self):
        self.aw.closeHelpDialog(self.helpdialog)