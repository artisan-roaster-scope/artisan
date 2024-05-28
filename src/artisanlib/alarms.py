#
# ABOUT
# Artisan Alarms Dialog

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

import os
import sys
import platform
import logging
from typing import Final, Dict, Union, List, Optional, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from artisanlib.types import ProfileData, AlarmSet # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent # pylint: disable=unused-import
    from PyQt6.QtWidgets import QStyleOptionViewItem  # pylint: disable=unused-import
    from PyQt6.QtCore import QModelIndex # pylint: disable=unused-import

from artisanlib.util import deltaLabelUTF8, comma2dot, float2float
from artisanlib.dialogs import ArtisanResizeablDialog
from artisanlib.widgets import (MyQComboBox, MyTableWidgetItemNumber, MyTableWidgetItemQCheckBox,
                                MyTableWidgetItemQComboBox, MyTableWidgetItemQLineEdit, MyTableWidgetItemQTime)


try:
    from PyQt6.QtCore import (Qt, pyqtSlot, QSettings, QTimer) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QColor, QIntValidator # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QComboBox, QDialogButtonBox, # @UnusedImport @Reimport  @UnresolvedImport
                QTableWidget, QHBoxLayout, QVBoxLayout, QCheckBox, QPushButton, QSizePolicy, QSpinBox, # @UnusedImport @Reimport  @UnresolvedImport
                QTableWidgetSelectionRange, QTimeEdit, QTabWidget, QGridLayout, QGroupBox, QHeaderView, QStyledItemDelegate, QAbstractSpinBox) # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import (Qt, pyqtSlot, QSettings, QTimer) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QColor, QIntValidator # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QComboBox, QDialogButtonBox, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
                QTableWidget, QHBoxLayout, QVBoxLayout, QCheckBox, QPushButton, QSizePolicy, QSpinBox, # # @UnusedImport @Reimport  @UnresolvedImport
                QTableWidgetSelectionRange, QTimeEdit, QTabWidget, QGridLayout, QGroupBox, QHeaderView, QStyledItemDelegate, QAbstractSpinBox) # @UnusedImport @Reimport  @UnresolvedImport



_log: Final[logging.Logger] = logging.getLogger(__name__)


class AlignDelegate(QStyledItemDelegate): # pyright:ignore[reportGeneralTypeIssues]
    def initStyleOption(self, option:Optional['QStyleOptionViewItem'], index:'QModelIndex') -> None:
        super().initStyleOption(option, index)
        if option is not None:
            option.displayAlignment = Qt.AlignmentFlag.AlignCenter

class AlarmDlg(ArtisanResizeablDialog):
    def __init__(self, parent:QWidget, aw:'ApplicationWindow', activeTab:int = 0) -> None:
        super().__init__(parent, aw)
        self.activeTab = activeTab
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Alarms'))
        self.helpdialog = None

        # restore window position
        settings = QSettings()
        if settings.contains('AlarmsGeometry'):
            self.restoreGeometry(settings.value('AlarmsGeometry'))

        #table for alarms
        self.alarmtable = QTableWidget()
        self.alarmtable.itemSelectionChanged.connect(self.selectionChanged)
        allonButton = QPushButton(QApplication.translate('Button','All On'))
        allonButton.clicked.connect(self.alarmsAllOn)
        allonButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        alloffButton = QPushButton(QApplication.translate('Button','All Off'))
        alloffButton.clicked.connect(self.alarmsAllOff)
        alloffButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        addButton = QPushButton(QApplication.translate('Button','Add'))
        addButton.clicked.connect(self.addalarm)
        addButton.setMinimumWidth(80)
        addButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.insertButton = QPushButton(QApplication.translate('Button','Insert'))
        self.insertButton.clicked.connect(self.insertalarm)
        self.insertButton.setMinimumWidth(80)
        self.insertButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.insertButton.setEnabled(False)

        deleteButton = QPushButton(QApplication.translate('Button','Delete'))
        deleteButton.clicked.connect(self.deletealarm)
        deleteButton.setMinimumWidth(80)
        deleteButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.copyalarmTableButton = QPushButton(QApplication.translate('Button', 'Copy Table'))
        self.copyalarmTableButton.setToolTip(QApplication.translate('Tooltip','Copy table to clipboard, OPTION or ALT click for tabular text'))
        self.copyalarmTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.copyalarmTableButton.clicked.connect(self.copyAlarmTabletoClipboard)

        importButton = QPushButton(QApplication.translate('Button','Load'))
        importButton.clicked.connect(self.importalarms)
        importButton.setMinimumWidth(80)
        importButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        exportButton = QPushButton(QApplication.translate('Button','Save'))
        exportButton.clicked.connect(self.exportalarms)
        exportButton.setMinimumWidth(80)
        exportButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.closealarms)
        self.dialogbuttons.removeButton(self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel))

        helpDialogButton = QDialogButtonBox()
        helpButton = helpDialogButton.addButton(QDialogButtonBox.StandardButton.Help)
        if helpButton is not None:
            self.setButtonTranslations(helpButton,'Help',QApplication.translate('Button','Help'))
            helpButton.setToolTip(QApplication.translate('Tooltip','Show help'))
            helpButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            helpButton.setMinimumWidth(80)
            helpButton.clicked.connect(self.showAlarmbuttonhelp)
        clearButton = QPushButton(QApplication.translate('Button','Clear'))
        clearButton.setToolTip(QApplication.translate('Tooltip','Clear alarms table'))
        clearButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        clearButton.setMinimumWidth(80)
        clearButton.clicked.connect(self.clearalarms)
        self.loadAlarmsFromProfile = QCheckBox(QApplication.translate('CheckBox', 'Load from profile'))
        self.loadAlarmsFromProfile.setChecked(self.aw.qmc.loadalarmsfromprofile)
        self.loadAlarmsFromBackground = QCheckBox(QApplication.translate('CheckBox', 'Load from background'))
        self.loadAlarmsFromBackground.setChecked(self.aw.qmc.loadalarmsfrombackground)

        self.popupTimoutSpinBox = QSpinBox()
        self.popupTimoutSpinBox.setSuffix('s')
        self.popupTimoutSpinBox.setSingleStep(1)
        self.popupTimoutSpinBox.setRange(0,120)
        self.popupTimoutSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.popupTimoutSpinBox.setValue(int(self.aw.qmc.alarm_popup_timout))
        popupTimeoutLabel = QLabel(QApplication.translate('Label', 'Pop Up Timeout'))

        alarmLabelLabel = QLabel(QApplication.translate('Label', 'Label'))
        self.alarmLabelEdit = QLineEdit(self.aw.qmc.alarmsetlabel)

        self.alarmsfile = QLabel(self.aw.qmc.alarmsfile)
        self.alarmsfile.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.alarmsfile.setMinimumWidth(300)
        self.alarmsfile.setSizePolicy(QSizePolicy.Policy.MinimumExpanding,QSizePolicy.Policy.Preferred)
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
        alarmSetListLabel = QLabel(QApplication.translate('Label','Alarm Sets'))
        transferalarmsetbutton = QPushButton(QApplication.translate('Button','<< Store Alarm Set'))
        transferalarmsetbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        setalarmsetbutton = QPushButton(QApplication.translate('Button','Activate Alarm Set >>'))
        setalarmsetbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        transferalarmesetcurrentLabel = QLabel(QApplication.translate('Label','Current Alarm Set'))
        self.transferalarmesetcurrentset = QLineEdit(self.aw.qmc.alarmsetlabel)
        self.transferalarmsetcombobox = QComboBox()
        self.transferalarmsetcombobox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # next line needed to avoid truncation of entries on Mac OS X under Qt 5.12.1-5.12.3
        # https://bugreports.qt.io/browse/QTBUG-73653
        self.transferalarmsetcombobox.setMinimumWidth(120)

        self.setAlarmSetLabels()

        transferalarmsetbutton.clicked.connect(self.setAlarmSet)
        setalarmsetbutton.clicked.connect(self.setAlarmTable)

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
        alarmsetGroupLayout = QGroupBox(QApplication.translate('GroupBox','Management'))
        alarmsetGroupLayout.setLayout(alarmsetManagementBox)
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
        self.TabWidget.addTab(C1Widget,QApplication.translate('Tab','Alarm Table'))
        C1Widget.setContentsMargins(5, 0, 5, 0)

        tab2layout = QVBoxLayout()
        tab2layout.addWidget(alarmsetGroupLayout)

        C2Widget = QWidget()
        C2Widget.setLayout(tab2layout)
        self.TabWidget.addTab(C2Widget,QApplication.translate('Tab','Alarm Sets'))
        C2Widget.setContentsMargins(5, 0, 5, 0)

        self.TabWidget.currentChanged.connect(self.tabSwitched)

        mainlayout = QVBoxLayout()
        mainlayout.setSpacing(5)
        mainlayout.setContentsMargins(5, 15, 5, 5)
        mainlayout.addWidget(self.TabWidget)
        mainlayout.addLayout(okbuttonlayout)
        self.setLayout(mainlayout)
        if platform.system() != 'Windows':
            ok_button: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button is not None:
                ok_button.setFocus()
        else:
            self.TabWidget.setFocus()

        # we set the active tab with a QTimer after the tabbar has been rendered once, as otherwise
        # some tabs are not rendered at all on Windows using Qt v6.5.1 (https://bugreports.qt.io/projects/QTBUG/issues/QTBUG-114204?filter=allissues)
        QTimer.singleShot(50, self.setActiveTab)

    @pyqtSlot()
    def setActiveTab(self) -> None:
        if self.activeTab == 0:
            self.createalarmtable()
        self.TabWidget.setCurrentIndex(self.activeTab)

    def setAlarmSetLabels(self) -> None:
        alarmset_labels = []
        for i in range(self.aw.qmc.ALARMSET_COUNT):
            alarmset:Optional[AlarmSet] = self.aw.qmc.getAlarmSet(i)
            if alarmset is not None:
                alarmset_labels.append(f"{str(i)} {alarmset['label']}")
        self.transferalarmsetcombobox.clear()
        self.transferalarmsetcombobox.addItems(alarmset_labels)
        self.transferalarmsetcombobox.setCurrentIndex(-1)


    # transfers the alarm table to the selected alarm set
    @pyqtSlot(bool)
    def setAlarmSet(self, _:bool = False) -> None:
        i = self.transferalarmsetcombobox.currentIndex()
        if 0 <= i < len(self.aw.qmc.alarmsets):
            self.aw.qmc.alarmsetlabel = self.transferalarmesetcurrentset.text()
            self.transferalarmesetcurrentset.setText(self.aw.qmc.alarmsetlabel)
            # we clear the alarmsfile as we overwrite here from an alarmset
            self.aw.qmc.alarmsfile = ''
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
    def setAlarmTable(self, _:bool = False) -> None:
        i = self.transferalarmsetcombobox.currentIndex()
        if 0 <= i < len(self.aw.qmc.alarmsets):
            self.aw.qmc.selectAlarmSet(i)
            self.transferalarmesetcurrentset.setText(self.aw.qmc.alarmsetlabel)
            self.transferalarmsetcombobox.setCurrentIndex(-1)

    @pyqtSlot(int)
    def tabSwitched(self, i:int) -> None:
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
    def selectionChanged(self) -> None:
        selected = self.alarmtable.selectedRanges()
        if selected and len(selected) > 0:
            self.insertButton.setEnabled(True)
        else:
            self.insertButton.setEnabled(False)

    def deselectAll(self) -> None:
        selected = self.alarmtable.selectedRanges()
        if selected and len(selected) > 0:
            self.alarmtable.setRangeSelected(selected[0],False)

    @pyqtSlot(bool)
    def clearalarms(self, _:bool = False) -> None:
        self.aw.qmc.alarmtablecolumnwidths = [self.alarmtable.columnWidth(c) for c in range(self.alarmtable.columnCount())]
        self.aw.qmc.alarmsfile = ''
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
        self.aw.qmc.alarmsetlabel = ''
        self.alarmLabelEdit.setText('')

    @pyqtSlot(bool)
    def alarmsAllOn(self, _:bool = False) -> None:
        self.alarmson(1)

    @pyqtSlot(bool)
    def alarmsAllOff(self, _:bool = False) -> None:
        self.alarmson(0)

    def alarmson(self, flag:int) -> None:
        for i, _ in enumerate(self.aw.qmc.alarmflag):
            if flag == 1:
                self.aw.qmc.alarmflag[i] = 1
            else:
                self.aw.qmc.alarmflag[i] = 0
        self.createalarmtable()

    @pyqtSlot(bool)
    def addalarm(self, _:bool = False) -> None:
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
        alarm_string = ''
        selected = self.alarmtable.selectedRanges()
        if len(selected) > 0:
            self.savealarms() # we first "save" the alarmtable to be able to pick up the values of the selected row
            selected_idx = selected[0].topRow()
            item = self.alarmtable.item(selected_idx,0)
            if item is not None:
                selected_idx = int(item.text()) -1 # we deref the rows number that might be different per sorting order
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
                except Exception: # pylint: disable=broad-except
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
        if header is not None:
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
            for i, __ in enumerate(self.aw.qmc.alarmtablecolumnwidths):
                try:
                    self.alarmtable.setColumnWidth(i,self.aw.qmc.alarmtablecolumnwidths[i])
                except Exception: # pylint: disable=broad-except
                    pass
            self.alarmtable.setSortingEnabled(True)
        else:
            self.deselectAll()
            # select newly added row i.e. the last one
            self.alarmtable.setRangeSelected(QTableWidgetSelectionRange(nalarms,0,nalarms,self.alarmtable.columnCount()-1),True)
            if header is not None:
                header.setStretchLastSection(True)
            self.markNotEnabledAlarmRows()
            self.alarmtable.setSortingEnabled(True)

    @pyqtSlot(bool)
    def insertalarm(self, _:bool = False) -> None:
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
            alarm_string = QApplication.translate('Label','Enter description')
            # check for selection
            selected = self.alarmtable.selectedRanges()
            if selected and len(selected) > 0:
                self.savealarms() # we first "save" the alarmtable to be able to pick up the values of the selected row
                selected_row = selected[0].topRow()
                item = self.alarmtable.item(selected_row,0)
                if item is not None:
                    selected_row = int(item.text()) -1 # we derref the rows number that might be different per sorting order
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
                    except Exception: # pylint: disable=broad-except
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
                    if header is not None:
                        header.setStretchLastSection(False)
                        self.deselectAll()
                        # select newly inserted item
                        self.alarmtable.setRangeSelected(QTableWidgetSelectionRange(selected_row,0,selected_row,self.alarmtable.columnCount()-1),True)
                        header.setStretchLastSection(True)
                    self.markNotEnabledAlarmRows()
                    self.alarmtable.sortItems(0, Qt.SortOrder.AscendingOrder) # we first have to sort the table according to the row numbers
                    # we no re-number rows
                    self.renumberRows()
                    # we correct the IfAlarm and ButNot references to items after the inserted one
                    for i in range(self.alarmtable.rowCount()):
                        guard = cast(QLineEdit, self.alarmtable.cellWidget(i,2))
                        try:
                            guard_value = int(str(guard.text())) - 1
                        except Exception: # pylint: disable=broad-except
                            guard_value = -1
                        if guard_value >= selected_row:
                            guard.setText(str(guard_value+2))
                        nguard = cast(QLineEdit, self.alarmtable.cellWidget(i,3))
                        try:
                            nguard_value = int(str(nguard.text())) - 1
                        except Exception: # pylint: disable=broad-except
                            nguard_value = -1
                        if nguard_value >= selected_row:
                            nguard.setText(str(nguard_value+2))
        self.alarmtable.setSortingEnabled(True)

    def renumberRows(self) -> None:
        for i in range(self.alarmtable.rowCount()):
            self.alarmtable.setItem(i, 0, MyTableWidgetItemNumber(str(i+1),i))

    @pyqtSlot(bool)
    def deletealarm(self, _:bool = False) -> None:
        self.aw.qmc.alarmtablecolumnwidths = [self.alarmtable.columnWidth(c) for c in range(self.alarmtable.columnCount())]
        self.alarmtable.setSortingEnabled(False)
        nalarms = self.alarmtable.rowCount()
        if nalarms:
            # check for selection
            selected = self.alarmtable.selectedRanges()
            if selected and len(selected) > 0:
                selected_row = selected[0].topRow()
                item = self.alarmtable.item(selected_row,0)
                if item is not None:
                    selected_row = int(item.text()) -1 # we derref the rows number that might be different per sorting order
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
                    self.alarmtable.sortItems(0, Qt.SortOrder.AscendingOrder) # we first have to sort the table according to the row numbers
                    # renumber elements
                    self.renumberRows()
                    # we correct the IfAlarm and ButNot references to items after the deleted one
                    for i in range(self.alarmtable.rowCount()):
                        guard = cast(QLineEdit, self.alarmtable.cellWidget(i,2))
                        try:
                            guard_value = int(str(guard.text())) - 1
                        except Exception: # pylint: disable=broad-except
                            guard_value = -1
                        if guard_value >= selected_row:
                            guard.setText(str(guard_value))
                        nguard = cast(QLineEdit, self.alarmtable.cellWidget(i,3))
                        try:
                            nguard_value = int(str(nguard.text())) - 1
                        except Exception: # pylint: disable=broad-except
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
    def importalarms(self, _:bool = False) -> None:
        self.aw.fileImport(QApplication.translate('Message', 'Load Alarms'),self.importalarmsJSON,ext='*.alrm *.alog')

    def importalarmsJSON(self, filename:str) -> None:
        try:
            _,ext = os.path.splitext(filename)
            if ext == '.alrm':
                from json import load as json_load
                with open(filename, encoding='utf-8') as infile:
                    alarms = json_load(infile)
                self.aw.qmc.alarmsfile = filename
                self.alarmsfile.setText(self.aw.qmc.alarmsfile)
                self.aw.qmc.alarmflag = alarms['alarmflags']
                self.aw.qmc.alarmguard = alarms['alarmguards']
                if 'alarmnegguards' in alarms:
                    self.aw.qmc.alarmnegguard = alarms['alarmnegguards']
                else:
                    self.aw.qmc.alarmnegguard = [0]*len(self.aw.qmc.alarmflag)
                self.aw.qmc.alarmtime = alarms['alarmtimes']
                self.aw.qmc.alarmoffset = alarms['alarmoffsets']
                self.aw.qmc.alarmcond = alarms['alarmconds']
                self.aw.qmc.alarmsource = alarms['alarmsources']
                self.aw.qmc.alarmtemperature = alarms['alarmtemperatures']
                self.aw.qmc.alarmaction = alarms['alarmactions']
                if 'alarmbeep' in alarms:
                    self.aw.qmc.alarmbeep = alarms['alarmbeep']
                else:
                    self.aw.qmc.alarmbeep = [0]*len(self.aw.qmc.alarmflag)
                self.aw.qmc.alarmstrings = alarms['alarmstrings']
            elif ext == '.alog':
                obj = cast('ProfileData', self.aw.deserialize(filename))
                self.aw.loadAlarmsFromProfile(filename, obj)
                self.alarmsfile.setText(self.aw.qmc.alarmsfile)
            self.aw.qmc.alarmstate = [-1]*len(self.aw.qmc.alarmflag)
            aitems = self.buildAlarmSourceList()
            for i, _ in enumerate(self.aw.qmc.alarmsource):
                if self.aw.qmc.alarmsource[i] + 3 >= len(aitems):
                    self.aw.qmc.alarmsource[i] = 1 # BT
            self.createalarmtable()
        except Exception as ex: # pylint: disable=broad-except
            _log.exception(ex)
            _, _, exc_tb = sys.exc_info()
            self.aw.sendmessage(QApplication.translate('Message','Error loading alarm file'))
            self.aw.qmc.adderror((QApplication.translate('Error Message','Exception:') + ' importalarmsJSON() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def exportalarms(self, _:bool = False) -> None:
        self.aw.fileExport(QApplication.translate('Message', 'Save Alarms'), '*.alrm', self.exportalarmsJSON)

    def exportalarmsJSON(self, filename:str) -> bool:
        try:
            self.savealarms()
            alarms:Dict[str,Union[List[int],List[float],List[str]]] = {}
            alarms['alarmflags'] = self.aw.qmc.alarmflag
            alarms['alarmguards'] = self.aw.qmc.alarmguard
            alarms['alarmnegguards'] = self.aw.qmc.alarmnegguard
            alarms['alarmtimes'] = self.aw.qmc.alarmtime
            alarms['alarmoffsets'] = self.aw.qmc.alarmoffset
            alarms['alarmconds'] = self.aw.qmc.alarmcond
            alarms['alarmsources'] = self.aw.qmc.alarmsource
            alarms['alarmtemperatures'] = self.aw.qmc.alarmtemperature
            alarms['alarmactions'] = self.aw.qmc.alarmaction
            alarms['alarmbeep'] = self.aw.qmc.alarmbeep
            alarms['alarmstrings'] = list(self.aw.qmc.alarmstrings)
            from json import dump as json_dump
            with open(filename, 'w', encoding='utf-8') as outfile:
                json_dump(alarms, outfile, ensure_ascii=True)
                outfile.write('\n')
            return True
        except Exception as ex: # pylint: disable=broad-except
            _log.exception(ex)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' exportalarmsJSON(): {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
            return False

    @pyqtSlot()
    def closealarms(self) -> None:
        self.savealarms()
        # save column widths
        self.aw.qmc.alarmtablecolumnwidths = [self.alarmtable.columnWidth(c) for c in range(self.alarmtable.columnCount())]

        self.aw.qmc.alarm_popup_timout = int(self.popupTimoutSpinBox.value())
        self.aw.qmc.alarmsetlabel = self.alarmLabelEdit.text()
        self.closeHelp()
        settings = QSettings()
        #save window geometry
        settings.setValue('AlarmsGeometry',self.saveGeometry())
#        self.aw.closeEventSettings()

        self.aw.AlarmDlg_activeTab = self.TabWidget.currentIndex()
        self.accept()

    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        self.closealarms()

    def savealarms(self) -> None:
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
            self.aw.qmc.alarmstrings = ['']*nalarms
            for i in range(nalarms):
                flag = cast(QCheckBox, self.alarmtable.cellWidget(i,1))
                self.aw.qmc.alarmflag[i] = int(flag.isChecked())
                guard = cast(QLineEdit, self.alarmtable.cellWidget(i,2))
                try:
                    guard_value = int(str(guard.text())) - 1
                except Exception: # pylint: disable=broad-except
                    guard_value = -1
                if -1 < guard_value < nalarms:
                    self.aw.qmc.alarmguard[i] = guard_value
                else:
                    self.aw.qmc.alarmguard[i] = -1
                negguard = cast(QLineEdit, self.alarmtable.cellWidget(i,3))
                try:
                    negguard_value = int(str(negguard.text())) - 1
                except Exception: # pylint: disable=broad-except
                    negguard_value = -1
                if -1 < negguard_value < nalarms:
                    self.aw.qmc.alarmnegguard[i] = negguard_value
                else:
                    self.aw.qmc.alarmnegguard[i] = -1
                timez = cast(MyQComboBox, self.alarmtable.cellWidget(i,4))
                self.aw.qmc.alarmtime[i] = self.aw.qmc.menuidx2alarmtime[timez.currentIndex()]
                offset = cast(QTimeEdit, self.alarmtable.cellWidget(i,5))
                tx = self.aw.QTime2time(offset.time())
                self.aw.qmc.alarmoffset[i] = max(0,int(round(tx)))
                atype = cast(MyQComboBox, self.alarmtable.cellWidget(i,6))
                self.aw.qmc.alarmsource[i] = int(str(atype.currentIndex())) - 3
                cond = cast(MyQComboBox, self.alarmtable.cellWidget(i,7))
                self.aw.qmc.alarmcond[i] = int(str(cond.currentIndex()))
                temp = cast(QLineEdit, self.alarmtable.cellWidget(i,8))
                try:
                    self.aw.qmc.alarmtemperature[i] = float(comma2dot(str(temp.text())))
                except Exception: # pylint: disable=broad-except
                    self.aw.qmc.alarmtemperature[i] = 0.0
                action = cast(MyQComboBox, self.alarmtable.cellWidget(i,9))
                self.aw.qmc.alarmaction[i] = int(str(action.currentIndex() - 1))
                beepWidget = cast(QWidget, self.alarmtable.cellWidget(i,10))
                beepLayout = beepWidget.layout()
                if beepLayout is not None:
                    item0 = beepLayout.itemAt(0)
                    if item0 is not None:
                        beep = cast(QCheckBox, item0.widget())
                        if beep and beep is not None:
                            self.aw.qmc.alarmbeep[i] = int(beep.isChecked())
                description = cast(QLineEdit, self.alarmtable.cellWidget(i,11))
                self.aw.qmc.alarmstrings[i] = description.text()
        except Exception as ex: # pylint: disable=broad-except
            _log.exception(ex)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' savealarms(): {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

    def buildAlarmSourceList(self) -> List[str]:
        extra_names = []
        for i in range(len(self.aw.qmc.extradevices)):
            extra_names.append(str(i) + 'xT1: ' + self.aw.qmc.extraname1[i])
            extra_names.append(str(i) + 'xT2: ' + self.aw.qmc.extraname2[i])
        return ['',
             deltaLabelUTF8 + QApplication.translate('Label','ET'),
             deltaLabelUTF8 + QApplication.translate('Label','BT'),
             QApplication.translate('ComboBox','ET'),
             QApplication.translate('ComboBox','BT')] + extra_names

    # creates Widget in row i of self.alarmtable and sets them to values from local dialog variables at position i
    def setalarmtablerow(self, i:int) -> None:
        #1: flag
        flagComboBox = QCheckBox()
        flagComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        flagComboBox.setText(QApplication.translate('ComboBox','ON'))
        if self.aw.qmc.alarmflag[i]:
            flagComboBox.setCheckState(Qt.CheckState.Checked)
        else:
            flagComboBox.setCheckState(Qt.CheckState.Unchecked)
        #2: guarded by alarm
        if self.aw.qmc.alarmguard[i] > -1:
            guardstr = str(self.aw.qmc.alarmguard[i] + 1)
        else:
            guardstr = '0'
        guardedit = QLineEdit(guardstr)
        guardedit.setValidator(QIntValidator(0, 999,guardedit))
        guardedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        #3: neg guarded by alarm
        if self.aw.qmc.alarmnegguard[i] > -1:
            negguardstr = str(self.aw.qmc.alarmnegguard[i] + 1)
        else:
            negguardstr = '0'
        negguardedit = QLineEdit(negguardstr)
        negguardedit.setValidator(QIntValidator(0, 999,negguardedit))
        negguardedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        #4: Effective time from
        timeComboBox = MyQComboBox()
        timeComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        timeComboBox.addItems([QApplication.translate('ComboBox','ON'), # qmc.alarmtime 9
                               QApplication.translate('ComboBox','START'), # qmc.alarmtime -1
                               QApplication.translate('ComboBox','CHARGE'), # qmc.alarmtime 0
                               QApplication.translate('ComboBox','TP'), # qmc.alarmtime 8
                               QApplication.translate('ComboBox','DRY END'), # qmc.alarmtime 1
                               QApplication.translate('ComboBox','FC START'), # qmc.alarmtime 2
                               QApplication.translate('ComboBox','FC END'), # qmc.alarmtime 3
                               QApplication.translate('ComboBox','SC START'), # qmc.alarmtime 4
                               QApplication.translate('ComboBox','SC END'), # qmc.alarmtime 5
                               QApplication.translate('ComboBox','DROP'), # qmc.alarmtime 6
                               QApplication.translate('ComboBox','COOL'), # qmc.alarmtime 7
                               QApplication.translate('ComboBox','If Alarm')]) # qmc.alarmtime 10
        timeComboBox.setCurrentIndex(self.aw.qmc.alarmtime2menuidx[self.aw.qmc.alarmtime[i]])
        #5: time after selected event
        timeoffsetedit = QTimeEdit()
        timeoffsetedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        timeoffsetedit.setDisplayFormat('mm:ss')
        timeoffsetedit.setTime(self.aw.time2QTime(max(0,self.aw.qmc.alarmoffset[i])))
        timeoffsetedit.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        #6: type/source
        typeComboBox = MyQComboBox()
        typeComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        aitems = self.buildAlarmSourceList()
        typeComboBox.addItems(aitems)
        if self.aw.qmc.alarmsource[i] + 3 < len(aitems):
            typeComboBox.setCurrentIndex(self.aw.qmc.alarmsource[i] + 3)
        else:
            typeComboBox.setCurrentIndex(3)
        #7: condition
        condComboBox = MyQComboBox()
        delegate = AlignDelegate(condComboBox)
        condComboBox.setItemDelegate(delegate)
        condComboBox.setEditable(True)
        condComboBoxLineEdit = condComboBox.lineEdit()
        if condComboBoxLineEdit is not None:
            condComboBoxLineEdit.setReadOnly(True)
            condComboBoxLineEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        condComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
#        condComboBox.addItems([QApplication.translate('ComboBox','below'),
#                               QApplication.translate('ComboBox','above')])
        condComboBox.addItems(['<','>','=', '\u2260'])
        condComboBox.setCurrentIndex(self.aw.qmc.alarmcond[i])
        #8: temperature
        tempedit = QLineEdit(str(float2float(self.aw.qmc.alarmtemperature[i])))
        tempedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        tempedit.setMaximumWidth(130)
#        tempedit.setValidator(QIntValidator(0, 999,tempedit))
        tempedit.setValidator(self.aw.createCLocaleDoubleValidator(-999.9, 999.9,1,tempedit))
        #9: action
        actionComboBox = MyQComboBox()
        actionComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        actionComboBox.addItems(['',
                                 QApplication.translate('ComboBox','Pop Up'),
                                 QApplication.translate('ComboBox','Call Program'),
                                 QApplication.translate('ComboBox','Event Button'),
                                 QApplication.translate('ComboBox','Slider') + ' ' + self.aw.qmc.etypesf(0),
                                 QApplication.translate('ComboBox','Slider') + ' ' + self.aw.qmc.etypesf(1),
                                 QApplication.translate('ComboBox','Slider') + ' ' + self.aw.qmc.etypesf(2),
                                 QApplication.translate('ComboBox','Slider') + ' ' + self.aw.qmc.etypesf(3),
                                 QApplication.translate('ComboBox','START'),
                                 QApplication.translate('ComboBox','DRY'),
                                 QApplication.translate('ComboBox','FCs'),
                                 QApplication.translate('ComboBox','FCe'),
                                 QApplication.translate('ComboBox','SCs'),
                                 QApplication.translate('ComboBox','SCe'),
                                 QApplication.translate('ComboBox','DROP'),
                                 QApplication.translate('ComboBox','COOL END'),
                                 QApplication.translate('ComboBox','OFF'),
                                 QApplication.translate('ComboBox','CHARGE'),
                                 QApplication.translate('ComboBox','RampSoak ON'),
                                 QApplication.translate('ComboBox','RampSoak OFF'),
                                 QApplication.translate('ComboBox','PID ON'),
                                 QApplication.translate('ComboBox','PID OFF'),
                                 QApplication.translate('ComboBox','SV'),
                                 QApplication.translate('ComboBox','Playback ON'),
                                 QApplication.translate('ComboBox','Playback OFF'),
                                 QApplication.translate('ComboBox','Set Canvas Color'),
                                 QApplication.translate('ComboBox','Reset Canvas Color')])
        actionComboBox.setCurrentIndex(self.aw.qmc.alarmaction[i] + 1)
        #10: beep
        beepWidget = QWidget()
        beepCheckBox = QCheckBox()
        beepCheckBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        beepLayout = QHBoxLayout(beepWidget)
        beepLayout.addWidget(beepCheckBox)
        beepLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        beepLayout.setContentsMargins(0,0,0,0)
        if len(self.aw.qmc.alarmbeep) > i and self.aw.qmc.alarmbeep[i]:
            beepCheckBox.setCheckState(Qt.CheckState.Checked)
        else:
            beepCheckBox.setCheckState(Qt.CheckState.Unchecked)
        #11: text description
        descriptionedit = QLineEdit(self.aw.qmc.alarmstrings[i])
        descriptionedit.setCursorPosition(0)
        descriptionedit.setPlaceholderText(QApplication.translate('Label','Enter description'))
        #
        numberWidget = MyTableWidgetItemNumber(str(i+1),i)
        numberWidget.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        self.alarmtable.setItem(i, 0, numberWidget)
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
        # ensure proper sorting
        beepL = beepWidget.layout()
        if beepL is not None:
            item0 = beepL.itemAt(0)
            if item0 is not None:
                item0widget = cast(QCheckBox, item0.widget())
#                if isinstance(item0widget,QCheckBox):
                self.alarmtable.setItem(i, 10, MyTableWidgetItemQCheckBox(item0widget))
        self.alarmtable.setCellWidget(i,11,descriptionedit)
        self.alarmtable.setItem(i, 11, MyTableWidgetItemQLineEdit(descriptionedit))


    # puts a gray background on alarm rows that have already been fired
    def markNotEnabledAlarmRows(self) -> None:
        for i in range(self.alarmtable.rowCount()):
            for j in range(11):
                try:
                    if self.aw.qmc.alarmstate[i] != -1:
                        item = self.alarmtable.item(i,j)
                        if item is not None:
                            item.setBackground(QColor(191, 191, 191))
                except Exception: # pylint: disable=broad-except
                    pass

    def createalarmtable(self) -> None:
        try:
            self.alarmtable.clear()
            self.alarmtable.setTabKeyNavigation(True)
            self.alarmtable.setColumnCount(12)
            self.alarmtable.setHorizontalHeaderLabels([QApplication.translate('Table','Nr'),
                                                           QApplication.translate('Table','Status'),
                                                           QApplication.translate('Table','If Alarm'),
                                                           QApplication.translate('Table','But Not'),
                                                           QApplication.translate('Table','From'),
                                                           QApplication.translate('Table','Time'),
                                                           QApplication.translate('Table','Source'),
                                                           QApplication.translate('Table','Condition'),
                                                           QApplication.translate('Table','Value'),
                                                           QApplication.translate('Table','Action'),
                                                           QApplication.translate('Table','Beep'),
                                                           QApplication.translate('Table','Description')])
            self.alarmtable.setAlternatingRowColors(True)
            self.alarmtable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.alarmtable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.alarmtable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.alarmtable.setShowGrid(True)
            nalarms = len(self.aw.qmc.alarmtemperature)
            vheader = self.alarmtable.verticalHeader()
            if vheader is not None:
                vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
                vheader.setVisible(False)
            self.alarmtable.setSortingEnabled(False)
            self.alarmtable.setRowCount(nalarms)
            #populate table
            for i in range(nalarms):
                self.setalarmtablerow(i)
            fixed_columns:Final[List[int]] = [0,1,5,7,10]
            header = self.alarmtable.horizontalHeader()
            if header is not None:
                header.setStretchLastSection(True)
                self.alarmtable.resizeColumnsToContents()
                for i in fixed_columns:
                    header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                    header.resizeSection(i, header.sectionSize(i) + (10 if i in {0,5} else 5))
            if not self.aw.qmc.alarmtablecolumnwidths:
                self.alarmtable.setColumnWidth(2, 50)
                self.alarmtable.setColumnWidth(3, 50)
                self.alarmtable.setColumnWidth(4, 95)
                self.alarmtable.setColumnWidth(5, 65)
                self.alarmtable.setColumnWidth(6, 100)
                self.alarmtable.setColumnWidth(8, 51)
                self.alarmtable.setColumnWidth(9, 103)
            else:
                # remember the columnwidth
                for i, _ in enumerate(self.aw.qmc.alarmtablecolumnwidths):
                    if i not in fixed_columns:
                        try:
                            w = self.aw.qmc.alarmtablecolumnwidths[i]
                            if i == 6:
                                w = max(100,w)
                            self.alarmtable.setColumnWidth(i,w)
                        except Exception: # pylint: disable=broad-except
                            pass
            self.markNotEnabledAlarmRows()
            self.alarmtable.setSortingEnabled(True)
            self.alarmtable.sortItems(0)

        except Exception as ex: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message','Exception:') + ' createalarmtable() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def copyAlarmTabletoClipboard(self, _:bool=False) -> None:
        import prettytable
        nrows = self.alarmtable.rowCount()
        ncols = self.alarmtable.columnCount()
        clipboard = ''
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.AltModifier:  #alt click
            tbl = prettytable.PrettyTable()
            fields = []
            for c in range(ncols):
                item = self.alarmtable.horizontalHeaderItem(c)
                if item is not None:
                    fields.append(item.text())
            tbl.field_names = fields
            for r in range(nrows):
                rows = []
                item0 = self.alarmtable.item(r,0)
                if item0 is not None:
                    rows.append(item0.text())
                flagComboBox = cast(QCheckBox, self.alarmtable.cellWidget(r,1))
                rows.append(str(flagComboBox.isChecked()))
                guardedit = cast(QLineEdit, self.alarmtable.cellWidget(r,2))
                rows.append(guardedit.text())
                negguardedit = cast(QLineEdit, self.alarmtable.cellWidget(r,3))
                rows.append(negguardedit.text())
                timeComboBox = cast(MyQComboBox, self.alarmtable.cellWidget(r,4))
                rows.append(timeComboBox.currentText())
                timeoffsetedit = cast(QTimeEdit, self.alarmtable.cellWidget(r,5))
                rows.append(timeoffsetedit.time().toString('mm:ss'))
                typeComboBox = cast(MyQComboBox, self.alarmtable.cellWidget(r,6))
                rows.append(typeComboBox.currentText())
                condComboBox = cast(MyQComboBox, self.alarmtable.cellWidget(r,7))
                rows.append(condComboBox.currentText())
                tempedit= cast(QLineEdit, self.alarmtable.cellWidget(r,8))
                rows.append(tempedit.text())
                actionComboBox = cast(MyQComboBox, self.alarmtable.cellWidget(r,9))
                rows.append(actionComboBox.currentText())
                beepWidget = cast(QWidget, self.alarmtable.cellWidget(r,10))
                beepLayout = beepWidget.layout()
                if beepLayout is not None:
                    item1 = beepLayout.itemAt(0)
                    if item1 is not None:
                        beepCheckBox = cast(QCheckBox, item1.widget())
                        if beepCheckBox and beepCheckBox is not None:
                            rows.append(str(beepCheckBox.isChecked()))
                descriptionedit = cast(QLineEdit, self.alarmtable.cellWidget(r,11))
                rows.append(descriptionedit.text())
                tbl.add_row(rows)
            clipboard = tbl.get_string()
        else:
            for c in range(ncols):
                item = self.alarmtable.horizontalHeaderItem(c)
                if item is not None:
                    clipboard += item.text()
                    if c != (ncols-1):
                        clipboard += '\t'
            clipboard += '\n'
            for r in range(nrows):
                item0 = self.alarmtable.item(r,0)
                if item0 is not None:
                    clipboard += item0.text() + '\t'
                flagComboBox = cast(QCheckBox, self.alarmtable.cellWidget(r,1))
                clipboard += str(flagComboBox.isChecked()) + '\t'
                guardedit = cast(QLineEdit, self.alarmtable.cellWidget(r,2))
                clipboard += guardedit.text() + '\t'
                negguardedit = cast(QLineEdit, self.alarmtable.cellWidget(r,3))
                clipboard += negguardedit.text() + '\t'
                timeComboBox = cast(MyQComboBox, self.alarmtable.cellWidget(r,4))
                clipboard += timeComboBox.currentText() + '\t'
                timeoffsetedit = cast(QTimeEdit, self.alarmtable.cellWidget(r,5))
                clipboard += timeoffsetedit.time().toString('mm:ss') + '\t'
                typeComboBox = cast(MyQComboBox, self.alarmtable.cellWidget(r,6))
                clipboard += typeComboBox.currentText() + '\t'
                condComboBox = cast(MyQComboBox, self.alarmtable.cellWidget(r,7))
                clipboard += condComboBox.currentText() + '\t'
                tempedit = cast(QLineEdit, self.alarmtable.cellWidget(r,8))
                clipboard += tempedit.text() + '\t'
                actionComboBox = cast(MyQComboBox, self.alarmtable.cellWidget(r,9))
                clipboard += actionComboBox.currentText() + '\t'
                beepWidget = cast(QWidget, self.alarmtable.cellWidget(r,10))
                beepLayout = beepWidget.layout()
                if beepLayout is not None:
                    item1 = beepLayout.itemAt(0)
                    if item1 is not None:
                        beepCheckBox = cast(QCheckBox, item1.widget())
                        if beepCheckBox and beepCheckBox is not None:
                            clipboard += str(beepCheckBox.isChecked()) + '\t'
                        else:
                            clipboard += ' ' + '\t'
                descriptionedit = cast(QLineEdit, self.alarmtable.cellWidget(r,11))
                clipboard += descriptionedit.text() + '\n'
        # copy to the system clipboard
        sys_clip = QApplication.clipboard()
        if sys_clip is not None:
            sys_clip.setText(clipboard)
        self.aw.sendmessage(QApplication.translate('Message','Alarm table copied to clipboard'))

    @pyqtSlot(bool)
    def showAlarmbuttonhelp(self, _:bool=False) -> None:
        from help import alarms_help # pyright: ignore [attr-defined] # pylint: disable=no-name-in-module
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate('Form Caption','Alarms Help'),
                alarms_help.content())

    def closeHelp(self) -> None:
        self.aw.closeHelpDialog(self.helpdialog)
