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
# Marko Luther, Dave Baxter 2023, 2024

import sys
import platform
from typing import Optional, List, Any, cast, TYPE_CHECKING, Final
from artisanlib.dialogs import ArtisanResizeablDialog
from artisanlib.util import deltaLabelUTF8
from artisanlib.widgets import MyContentLimitedQComboBox, MyQTableWidget
import logging

try:
    from PyQt6.QtCore import Qt, pyqtSlot, QSettings, QTimer # @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QLabel, QDialogButtonBox, QGridLayout, # @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QGroupBox, # @Reimport  @UnresolvedImport
        QSpinBox, QWidget, QTabWidget, QTableWidget, QPushButton, QHeaderView, QLineEdit) # @XUnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import Qt, pyqtSlot, QSettings, QTimer # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QLabel, QDialogButtonBox, QGridLayout, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QGroupBox, # @UnusedImport @Reimport  @UnresolvedImport
        QSpinBox, QWidget, QTabWidget, QTableWidget, QPushButton, QHeaderView, QLineEdit) # @UnusedImport @Reimport  @UnresolvedImport

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QPushButton, QWidget # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent # pylint: disable=unused-import

_log: Final[logging.Logger] = logging.getLogger(__name__)

class StatisticsDlg(ArtisanResizeablDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow', activeTab:int = 0) -> None:
        super().__init__(parent, aw)

        self.activeTab = activeTab
        self.setWindowTitle(QApplication.translate('Form Caption','Statistics'))
        self.setModal(True)
#        self.helpdialog = None

        # restore window position
        settings = QSettings()
        if settings.contains('StatisticsGeometry'):
            self.restoreGeometry(settings.value('StatisticsGeometry'))

        ### Tab 1 - Statistics
        #Display
        self.timez = QCheckBox(QApplication.translate('CheckBox','Time'))
        self.timez.setToolTip(QApplication.translate('Tooltip','Show phase times and percent'))
        if self.aw.qmc.statisticsflags[0]:
            self.timez.setChecked(True)
        self.timez.stateChanged.connect(self.changeStatisticsflag)

        self.barb = QCheckBox(QApplication.translate('CheckBox','Bar'))
        self.barb.setToolTip(QApplication.translate('Tooltip','Show the Phases Bar'))
        if self.aw.qmc.statisticsflags[1]:
            self.barb.setChecked(True)
        self.barb.stateChanged.connect(self.changeStatisticsflag)

        # flag 2 not used anymore

        self.area = QCheckBox(QApplication.translate('CheckBox','Characteristics'))
        self.area.setToolTip(QApplication.translate('Tooltip','Show metrics below graph, right click on metrics to toggle'))
        if self.aw.qmc.statisticsflags[3]:
            self.area.setChecked(True)
        self.area.stateChanged.connect(self.changeStatisticsflag)

        self.ror = QCheckBox(self.aw.qmc.mode + QApplication.translate('CheckBox','/min'))
        self.ror.setToolTip(QApplication.translate('Tooltip','Show RoR from begin to end of phase'))
        if self.aw.qmc.statisticsflags[4]:
            self.ror.setChecked(True)
        self.ror.stateChanged.connect(self.changeStatisticsflag)

        # flag 5 not used anymore

        self.dt = QCheckBox(deltaLabelUTF8 + self.aw.qmc.mode)
        self.dt.setToolTip(QApplication.translate('Tooltip','Show delta temp from begin to end of phase'))
        if self.aw.qmc.statisticsflags[6]:
            self.dt.setChecked(True)
        self.dt.stateChanged.connect(self.changeStatisticsflag)

        flagsLayout = QGridLayout()
        flagsLayout.addWidget(self.timez,0,0)
        flagsLayout.addWidget(self.barb,0,1)
        flagsLayout.addWidget(self.dt,0,2)
        flagsLayout.addWidget(self.ror,0,3)
        flagsLayout.addWidget(self.area,0,4)

        #AUC
        beginlabel =QLabel(QApplication.translate('Label', 'From'))
        beginitems = [
                    QApplication.translate('Label','CHARGE'),
                    QApplication.translate('Label','TP'),
                    QApplication.translate('Label','DRY END'),
                    QApplication.translate('Label','FC START')]
        self.beginComboBox = QComboBox()
        self.beginComboBox.setToolTip(QApplication.translate('Tooltip','Set start of AUC, must tick "From Event"'))
        self.beginComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.beginComboBox.setMaximumWidth(120)
        self.beginComboBox.addItems(beginitems)
        self.beginComboBox.setCurrentIndex(self.aw.qmc.AUCbegin)
        self.beginComboBox.setEnabled(self.aw.qmc.AUCbaseFlag)
        self.beginComboBox.currentIndexChanged.connect(self.AUCBeginChanged)
        baseeditlabel = QLabel(QApplication.translate('Label', 'Base'))
        self.baseedit = QSpinBox()
        self.baseedit.setToolTip(QApplication.translate('Tooltip','Set start temp of AUC, must un-tick "From Event"'))
        self.baseedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.baseedit.setRange(0,999)
        self.baseedit.setValue(int(round(self.aw.qmc.AUCbase)))
        if self.aw.qmc.mode == 'F':
            self.baseedit.setSuffix(' F')
        else:
            self.baseedit.setSuffix(' C')
        self.baseedit.valueChanged.connect(self.AUCbaseChanged)
        self.baseFlag = QCheckBox(QApplication.translate('CheckBox','From Event'))
        self.baseFlag.setToolTip(QApplication.translate('Tooltip','When selected use From event to start AUC else use Base Temp'))
        self.baseedit.setEnabled(not self.aw.qmc.AUCbaseFlag)
        self.baseFlag.setChecked(self.aw.qmc.AUCbaseFlag)
        self.baseFlag.stateChanged.connect(self.switchAUCbase)
        targetlabel =QLabel(QApplication.translate('Label', 'Target'))
        self.targetedit = QSpinBox()
        self.targetedit.setToolTip(QApplication.translate('Tooltip','Set a target total AUC to display during roast'))
        self.targetedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.targetedit.setRange(0,9999)
        self.targetedit.setValue(int(round(self.aw.qmc.AUCtarget)))
        self.targetFlag = QCheckBox(QApplication.translate('CheckBox','Background'))
        self.targetFlag.setToolTip(QApplication.translate('Tooltip','Use background profile for AUC target'))
        self.targetedit.setEnabled(not self.aw.qmc.AUCtargetFlag)
        self.targetFlag.setChecked(self.aw.qmc.AUCtargetFlag)
        self.targetFlag.stateChanged.connect(self.switchAUCtarget)
        self.guideFlag = QCheckBox(QApplication.translate('CheckBox','Guide'))
        self.guideFlag.setToolTip(QApplication.translate('Tooltip','Show AUC Target guideline during roast'))
        self.guideFlag.setChecked(self.aw.qmc.AUCguideFlag)
        self.AUClcdFlag = QCheckBox(QApplication.translate('CheckBox','LCD'))
        self.AUClcdFlag.setToolTip(QApplication.translate('Tooltip','Show AUC LCD during roast'))
        self.AUClcdFlag.setChecked(self.aw.qmc.AUClcdFlag)
        self.AUClcdFlag.stateChanged.connect(self.AUCLCDflagChanged)
        self.AUCshowFlag = QCheckBox(QApplication.translate('CheckBox','Show Area'))
        self.AUCshowFlag.setToolTip(QApplication.translate('Tooltip','Show AUC area on graph'))
        self.AUCshowFlag.setChecked(self.aw.qmc.AUCshowFlag)
        self.AUCshowFlag.stateChanged.connect(self.changeAUCshowFlag)

        AUCgrid = QGridLayout()
        AUCgrid.addWidget(beginlabel,0,0,Qt.AlignmentFlag.AlignRight)
        AUCgrid.addWidget(self.beginComboBox,0,1,1,2)
        AUCgrid.addWidget(baseeditlabel,1,0,Qt.AlignmentFlag.AlignRight)
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
        AUCgroupLayout = QGroupBox(QApplication.translate('GroupBox','AUC'))
        AUCgroupLayout.setLayout(AUCvertical)
        displayGroupLayout = QGroupBox(QApplication.translate('GroupBox','Display'))
        displayGroupLayout.setLayout(flagsLayout)
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.dialogbuttons)
        buttonsLayout.setContentsMargins(15, 15, 15, 15)  # left, top, right, bottom
        vgroupLayout = QVBoxLayout()
        vgroupLayout.addWidget(AUCgroupLayout)

        ### TAB 2 - Config Summary Stats
        self.summarystatstypes:List[int] = []
        self.buttonlistmaxlen:int = self.aw.buttonlistmaxlen
        # Statistic entries are made here and in buildStat() in canvas.py
        self.summarystats_types:List[str] = [
                # Presentation of these stats is done with corresponding entries in canvas:statsSummary():buildStat()
                # Add new stats at the end of the list.
                # The string used to identify a statistic may be changed without causing compatibility issues
                # To remove a stat:
                #   Do not delete it, change its entry to 'Unused' and do not translate it.
                #   The handler in canvas:statsSummary():buildStat() for the stattype must remain, it should be changed to "stattype_str = f'{newline}'".
                #       This is to maintain compatibility with previous settings.
                #   Once the createSummarystatsTable is opened the change(s) to 'Blank Line' will be updated in settings.
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('ComboBox','Blank Line')),                      # 0
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('Label','Title')),                              # 1
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('ComboBox','Roast Date, Time')),                # 2
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('AddlInfo','Roast of the Day')),                # 3
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('ComboBox','Ambient Conditions')),              # 4
                self.aw.qmc.dijkstra_to_ascii(f"{QApplication.translate('Label','Roaster')}, "                       # 5
                                              f"{QApplication.translate('Label','Drum Speed')}"),
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('Label','Beans')),                              # 6
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('AddlInfo','Screen Size')),                     # 7
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('AddlInfo','Density Green')),                   # 8
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('AddlInfo','Moisture Green')),                  # 9
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('AddlInfo','Batch Size')),                      # 10
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('AddlInfo','Density Roasted')),                 # 11
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('AddlInfo','Moisture Roasted')),                # 12
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('AddlInfo','Ground Color')),                    # 13
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('AddlInfo','Energy')),                          # 14
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('AddlInfo','CO2')),                             # 15
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('GroupBox','AUC')),                             # 16
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('Label','Roasting Notes')),                     # 17
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('Label','Cupping Score')),                      # 18
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('Label','Cupping Notes')),                      # 19
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('ComboBox','Weight Green')),                    # 20
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('AddlInfo','Weight Roasted')),                  # 21
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('AddlInfo','Weight Loss')),                     # 22
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('HTML Report Template','BBP Total Time')),      # 23
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('HTML Report Template','BBP Bottom Temp')),     # 24
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('HTML Report Template','BBP Summary')),         # 25
                'Unused',                                                                                            # 26
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('HTML Report Template','BBP Summary compact')), # 27
                self.aw.qmc.dijkstra_to_ascii(f"{QApplication.translate('Table','Phases')} - {QApplication.translate('Label','Finishing')}"), # 28
                self.aw.qmc.dijkstra_to_ascii(f"{QApplication.translate('Table','Phases')} - {QApplication.translate('Label','Maillard')}"),  # 29
                self.aw.qmc.dijkstra_to_ascii(f"{QApplication.translate('Table','Phases')} - {QApplication.translate('Label','Drying')}"),    # 30
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('HTML Report Template','Whole Color')),         # 31
                self.aw.qmc.dijkstra_to_ascii(QApplication.translate('Label','Cupping Correction')),                 # 32
                ]

        # function to remove from a list any elements matching string_to_remove
        def remove_matching_strings(input_list:List[str], string_to_remove:str) -> List[str]:
            return [s for s in input_list if string_to_remove not in s ]

        # remove entries designated as 'Unused' from the sorted list of statistic types
        self.summarystats_types_sorted:List[str] = sorted(remove_matching_strings(self.summarystats_types,'Unused'))

#        helpDialogButton = QDialogButtonBox()

        self.storeState()

        # show statistics summary
        self.ShowStatsSummary = QCheckBox(QApplication.translate('CheckBox', 'Show summary'))
        self.ShowStatsSummary.setToolTip(QApplication.translate('Tooltip','Show Summary Statistics'))
        self.ShowStatsSummary.setChecked(self.aw.qmc.statssummary)
        self.ShowStatsSummary.stateChanged.connect(self.changeStatsSummary)         #toggle
        self.ShowStatsSummary.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # max chars per line
        self.statsmaxchrperlinelabel = QLabel(QApplication.translate('Label', 'Max characters per line'))
        self.statsmaxchrperlineSpinBox = QSpinBox()
        self.statsmaxchrperlineSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.statsmaxchrperlineSpinBox.setToolTip(QApplication.translate('Tooltip','Determines the width of the display box'))
        self.statsmaxchrperlineSpinBox.setRange(1,120)
        self.statsmaxchrperlineSpinBox.setValue(int(round(self.aw.qmc.statsmaxchrperline)))
        self.statsmaxchrperlineSpinBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.statsmaxchrperlineSpinBox.valueChanged.connect(self.setstatsmaxchrperline)
        self.statsmaxchrperlineSpinBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # Font size
        self.fontsizeLabel = QLabel(QApplication.translate('Table', 'Text Size'))
        self.fontsizeSpinBox = QSpinBox()
        self.fontsizeSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.fontsizeSpinBox.setToolTip(QApplication.translate('Tooltip','Choose the font size\nFont type is set in Config>> Curves>> UI tab'))
        self.fontsizeSpinBox.setRange(1,4)
        self.fontsizeSpinBox.setValue(int(round(self.aw.summarystatsfontsize)))
        self.fontsizeSpinBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.fontsizeSpinBox.setPrefix('  ')
        self.fontsizeSpinBox.valueChanged.connect(self.setstatsfontsize)
        self.fontsizeSpinBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        #table for showing events
        self.summarystatstable = MyQTableWidget() #QTableWidget()
        self.summarystatstable.setTabKeyNavigation(True)
        self.summarystatstable.itemSelectionChanged.connect(self.selectionChanged)
        vheader: Optional[QHeaderView] = self.summarystatstable.verticalHeader()
        if vheader is not None:
            vheader.sectionMoved.connect(self.sectionMoved)
        self.copysummarystatsTableButton = QPushButton(QApplication.translate('Button', 'Copy Table'))
        self.copysummarystatsTableButton.setToolTip(QApplication.translate('Tooltip','Copy table to clipboard, OPTION or ALT click for tabular text'))
        self.copysummarystatsTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.copysummarystatsTableButton.clicked.connect(self.copyEventButtonTabletoClipboard)
        addButton: Optional[QPushButton] = QPushButton(QApplication.translate('Button','Add'))
        if addButton is not None:
            addButton.setToolTip(QApplication.translate('Tooltip','Add new Statistic'))
            #addButton.setMaximumWidth(100)
            addButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            addButton.clicked.connect(self.addsummarystatSlot)
        delButton: Optional[QPushButton] = QPushButton(QApplication.translate('Button','Delete'))
        if delButton is not None:
            delButton.setToolTip(QApplication.translate('Tooltip','Delete the selected Statistic'))
            #delButton.setMaximumWidth(100)
            delButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            delButton.clicked.connect(self.deletesummarystat)
        self.insertButton: Optional[QPushButton] = QPushButton(QApplication.translate('Button','Insert'))
        if self.insertButton is not None:
            self.insertButton.setToolTip(QApplication.translate('Tooltip','Insert below the selected Statistic'))
            self.insertButton.clicked.connect(self.insertsummarystatSlot)
            self.insertButton.setMinimumWidth(80)
            self.insertButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.insertButton.setEnabled(False)
        self.copyTableButton = QPushButton(QApplication.translate('Button', 'Copy Table'))
        if self.copyTableButton is not None:
            self.copyTableButton.setToolTip(QApplication.translate('Tooltip','Copy table to clipboard, OPTION or ALT click for tabular text'))
            self.copyTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.copyTableButton.clicked.connect(self.copyEventButtonTabletoClipboard)
        self.defaultButton = QPushButton(QApplication.translate('Button', 'Defaults'))
        if self.defaultButton is not None:
            self.defaultButton.setToolTip(QApplication.translate('Tooltip','Set Statistics Summary to default settings'))
            self.defaultButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.defaultButton.clicked.connect(self.restoreDefaults)
#        helpDialogButton = QDialogButtonBox()
#        helpButtonD: Optional[QPushButton] = helpDialogButton.addButton(QDialogButtonBox.StandardButton.Help)
#        if helpButtonD is not None:
#            helpButtonD.setFocusPolicy(Qt.FocusPolicy.NoFocus)
#            helpButtonD.setToolTip(QApplication.translate('Tooltip','Show help'))
#            self.setButtonTranslations(helpButtonD,'Help',QApplication.translate('Button','Help'))
#            helpButtonD.clicked.connect(self.showSummarystatshelp)

        statstablebuttonslayout = QHBoxLayout()
        statstablebuttonslayout.addWidget(self.ShowStatsSummary)
        statstablebuttonslayout.addSpacing(10)
        statstablebuttonslayout.addStretch()
        statstablebuttonslayout.addWidget(self.statsmaxchrperlinelabel)
        statstablebuttonslayout.addWidget(self.statsmaxchrperlineSpinBox)
        statstablebuttonslayout.addSpacing(5)
        statstablebuttonslayout.addStretch()
        statstablebuttonslayout.addWidget(self.fontsizeLabel)
        statstablebuttonslayout.addWidget(self.fontsizeSpinBox)
        statstablebuttonslayout.addStretch()
        tab2buttonlayout = QHBoxLayout()
        tab2buttonlayout.addWidget(addButton)
        tab2buttonlayout.addWidget(self.insertButton)
        tab2buttonlayout.addWidget(delButton)
        tab2buttonlayout.addWidget(self.copyTableButton)
        tab2buttonlayout.addStretch()
        tab2buttonlayout.addWidget(self.defaultButton)
#        tab2buttonlayout.addWidget(helpDialogButton)
        tab2buttonlayout.setContentsMargins(10, 0, 0, 0)  # left, top, right, bottom

        self.dialogbuttons.accepted.connect(self.accept)
        self.dialogbuttons.removeButton(self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel))

        ### tab1 layout
        self.TabWidget = QTabWidget()
        self.TabWidget.setContentsMargins(0, 0, 0, 0)  # left, top, right, bottom
        tab1layout = QVBoxLayout()
        tab1layout.addWidget(displayGroupLayout)
        tab1layout.addLayout(vgroupLayout)
        C1Widget = QWidget()
        C1Widget.setLayout(tab1layout)
        self.TabWidget.addTab(C1Widget,QApplication.translate('Form Caption','Statistics'))
        C1Widget.setContentsMargins(5, 0, 5, 0)

        ### tab2 layout
        tab2layout = QVBoxLayout()
        tab2layout.addWidget(self.summarystatstable)
        tab2layout.addLayout(statstablebuttonslayout)
        tab2layout.addLayout(tab2buttonlayout)
        tab2layout.setSpacing(5)
        tab2layout.setContentsMargins(0,10,0,5)  # left, top, right, bottom

        C2Widget = QWidget()
        C2Widget.setLayout(tab2layout)
        self.TabWidget.addTab(C2Widget,QApplication.translate('GroupBox','Stats Summary'))
        C2Widget.setContentsMargins(0, 0, 0, 0)  # left, top, right, bottom

        self.TabWidget.currentChanged.connect(self.tabSwitched)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.TabWidget)
        mainLayout.addLayout(buttonsLayout)
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(5, 10, 5, 0)  # left, top, right, bottom
        self.setLayout(mainLayout)

        if platform.system() != 'Windows':
            ok_button: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button is not None:
                ok_button.setFocus()
        else:
            self.TabWidget.setFocus()

        self.TabWidget.currentChanged.connect(self.tabSwitched)

        # we set the active tab with a QTimer after the tabbar has been rendered once, as otherwise
        # some tabs are not rendered at all on Windows using Qt v6.5.1 (https://bugreports.qt.io/projects/QTBUG/issues/QTBUG-114204?filter=allissues)
        QTimer.singleShot(50, self.setActiveTab)

# removed when making the dialog resizeable
#        settings = QSettings()
#        if settings.contains('StatisticsPosition'):
#            self.move(settings.value('StatisticsPosition'))

#        mainLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    @pyqtSlot(int)
    def AUCLCDflagChanged(self, _:int) -> None:
        self.aw.qmc.AUClcdFlag = not self.aw.qmc.AUClcdFlag
        if self.aw.qmc.flagstart:
            if self.aw.qmc.AUClcdFlag:
                self.aw.AUCLCD.show()
            else:
                self.aw.AUCLCD.hide()
        if self.aw.largePhasesLCDs_dialog is not None:
            self.aw.largePhasesLCDs_dialog.updateVisiblitiesPhases()

    @pyqtSlot(int)
    def AUCBeginChanged(self, _:int) -> None:
        self.aw.qmc.AUCbegin = self.beginComboBox.currentIndex()
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def AUCbaseChanged(self, _:int) -> None:
        self.aw.qmc.AUCbase = self.baseedit.value()
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def changeAUCshowFlag(self, _:int) -> None:
        self.aw.qmc.AUCshowFlag = not self.aw.qmc.AUCshowFlag
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def switchAUCbase(self, i:int) -> None:
        if i:
            self.baseedit.setEnabled(False)
            self.beginComboBox.setEnabled(True)
        else:
            self.baseedit.setEnabled(True)
            self.beginComboBox.setEnabled(False)
        self.aw.qmc.AUCbaseFlag = self.baseFlag.isChecked()
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def switchAUCtarget(self, i:int) -> None:
        if i:
            self.targetedit.setEnabled(False)
        else:
            self.targetedit.setEnabled(True)

    @pyqtSlot(int)
    def changeStatsSummary(self, _:int) -> None:
        self.aw.qmc.statssummary = not self.aw.qmc.statssummary
        # If Auto is set for the axis then recompute it
        if self.aw.qmc.autotimex and not self.aw.qmc.statssummary:
            self.aw.autoAdjustAxis()
        self.aw.qmc.redraw(recomputeAllDeltas=False)
        if self.aw.qmc.statssummary and not self.aw.qmc.flagon and self.aw.saveStatisticsMenu is not None:
            self.aw.saveStatisticsMenu.setEnabled(True)
        elif self.aw.saveStatisticsMenu is not None:
            self.aw.saveStatisticsMenu.setEnabled(False)

    @pyqtSlot(int)
    def changeStatisticsflag(self, value:int) -> None:
        sender = self.sender()
        if sender == self.timez:
            i = 0
        elif sender == self.barb:
            i = 1
        # flag 2 not used anymore
        elif sender == self.area:
            i = 3
        elif sender == self.ror:
            i = 4
        # flag 5 not used anymore
        elif sender == self.dt:
            i = 6
        else:
            return
        self.aw.qmc.statisticsflags[i] = value
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot()
    def accept(self) -> None:
        self.aw.qmc.AUCtarget = self.targetedit.value()
        self.aw.qmc.AUCtargetFlag = self.targetFlag.isChecked()
        self.aw.qmc.AUCguideFlag = self.guideFlag.isChecked()
        self.aw.qmc.AUClcdFlag = self.AUClcdFlag.isChecked()

        try:
            self.aw.qmc.AUCbackground = self.aw.compute_auc_background()
        except Exception: # pylint: disable=broad-except
            self.aw.qmc.AUCbackground = -1

        self.aw.qmc.redraw(recomputeAllDeltas=False)
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue('StatisticsPosition',self.frameGeometry().topLeft())
        self.aw.StatisticsDlg_activeTab = self.TabWidget.currentIndex()

        self.updatetypes()
        self.close()

    @pyqtSlot()
    def setActiveTab(self) -> None:
        self.TabWidget.setCurrentIndex(self.activeTab)

    @staticmethod
    def swapItems(l:List[Any], source:int, target:int) -> None:
        l[target],l[source] = l[source],l[target]

    @staticmethod
    def moveItem(l:List[Any], source:int, target:int) -> None:
        l.insert(target, l.pop(source))

    @pyqtSlot(int,int,int)
    def sectionMoved(self, logicalIndex:int, _oldVisualIndex:int, newVisualIndex:int) -> None:
        max_rows:int = len(self.summarystatstypes)

        # adjust vertical headers # seems not to be required with the clearContent/setRowCount(0) below
        self.summarystatstable.setVerticalHeaderLabels([str(1 + self.summarystatstable.visualRow(i)) for i in range(max_rows)])

        # adjust datamodel
        swap:bool = False # default action is to move item to new position
        if QApplication.queryKeyboardModifiers() == Qt.KeyboardModifier.AltModifier:
            # if ALT/OPTION key is hold, the items are swap
            swap = True
        l:List[Any]
        event_data:List[List[Any]] = [self.summarystatstypes]
        for l in event_data:
            if swap:
                self.swapItems(l, logicalIndex, newVisualIndex)
            else:
                self.moveItem(l, logicalIndex, newVisualIndex)

        self.summarystatstable.clearContents() # resets the view
        self.summarystatstable.setRowCount(0)  # resets the data model
        self.createSummarystatsTable()

    @pyqtSlot()
    def selectionChanged(self) -> None:
        selected = self.summarystatstable.selectedRanges()
        if self.insertButton is not None:
            if selected and len(selected) > 0:
                self.insertButton.setEnabled(True)
            else:
                self.insertButton.setEnabled(False)
        vheader = self.summarystatstable.verticalHeader()
        if self.summarystatstable.cursor_navigation and vheader is not None:
            QTimer.singleShot(0, vheader.setFocus)

    @pyqtSlot(int)
    def tabSwitched(self, i:int) -> None:
        if i == 0:
            pass
        elif i == 1: # switched to Config Summary tab
            self.createSummarystatsTable()

    @pyqtSlot(int)
    def setstatsmaxchrperline(self, _:int) -> None:
        self.aw.qmc.statsmaxchrperline = self.statsmaxchrperlineSpinBox.value()
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def setstatsfontsize(self, _:int) -> None:
        self.aw.summarystatsfontsize = self.fontsizeSpinBox.value()
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    def createSummarystatsTable(self) -> None:
        # Column zero with the row numbers is added, and the row header disabled to improve keyboard navigation.  With only
        # one column that is a ComboBox, the row selector also selects the ComboBox and the down arrow opens the combo.  No
        # solution was found, tus this alternate implementaition.

        columns = 1  # With one column we don't need lists, but the plumbing is here if more columns are needed in the future

#        if self.summarystatstable is not None and self.summarystatstable.columnCount() == columns:
#            # rows have been already established
#            # save the current columnWidth to reset them after table creation
#            self.aw.summarystatstablecolumnwidths = [self.summarystatstable.columnWidth(self.summarystatstable.width())]

        # deleting all rows is not allowed, create a first row if that happens
        if len(self.summarystatstypes) < 1:
            self.summarystatstypes.append(1)        #Title

        nstats = len(self.summarystatstypes)

        # self.summarystatstable.clear() # this crashes Ubuntu 16.04
#        if ndata != 0:
#            self.summarystatstable.clearContents() # this crashes Ubuntu 16.04 if device table is empty and also sometimes else
#        self.summarystatstable.clearSelection() # this seems to work also for Ubuntu 16.04

        self.summarystatstable.setRowCount(nstats)
        self.summarystatstable.setColumnCount(columns)
        self.summarystatstable.setHorizontalHeaderLabels([
                                                         '',
                                                         QApplication.translate('Tab','Statistics'),
                                                         ])
        self.summarystatstable.setEditTriggers(QTableWidget.EditTrigger.SelectedClicked)
        self.summarystatstable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.summarystatstable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.summarystatstable.setShowGrid(True)


        vheader = self.summarystatstable.verticalHeader()
        if vheader is not None:
            # Turn off row header
#            vheader.setVisible(False)
            vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        #Enable Drag Sorting
        self.summarystatstable.setDragEnabled(False) # content not draggable, only vertical header!
        self.summarystatstable.setAutoScroll(True)
        vheader = self.summarystatstable.verticalHeader()
        if vheader is not None:
            vheader.setSectionsMovable(True)
            vheader.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
            vheader.setAutoScroll(False)

        for i in range(nstats):
            #0 Type
            typeComboBox = MyContentLimitedQComboBox()
            # set the combox width to the full width of the table
            typeComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            typeComboBox.setToolTip(QApplication.translate('Tooltip','Choose a statistic to display'))
            typeComboBox.addItems(self.summarystats_types_sorted)
            # change table entries that point to a statistic type that is 'Unused' or to a statistic added in a later release
            # to point to 'Blank Line' instead
            if self.summarystatstypes[i] >= len(self.summarystats_types) or self.summarystats_types[self.summarystatstypes[i]] == 'Unused':
                typeComboBox.setCurrentIndex(self.summarystats_types_sorted.index(self.summarystats_types[0]))
                self.summarystatstypes[i] = 0  # updates to settings on
            else:
                typeComboBox.setCurrentIndex(self.summarystats_types_sorted.index(self.summarystats_types[self.summarystatstypes[i]]))
            typeComboBox.currentIndexChanged.connect(self.setitemsummarystat)
#            QWidget.setTabOrder(typeComboBox, vheader)
            #add widgets to the table
#            rowlabel = QTableWidgetItem(str(i+1))
#            rowlabel.setFlags(rowlabel.flags() ^ Qt.ItemFlag.ItemIsEditable) # disallow editing of row labels
#            rowlabel.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
#            self.summarystatstable.setItem(i,0,rowlabel)
#            self.summarystatstable.setCellWidget(i,1,typeComboBox)
            self.summarystatstable.setCellWidget(i,0,typeComboBox)


        hheader = self.summarystatstable.horizontalHeader()
        if hheader is not None:
            hheader.setStretchLastSection(False)
            self.summarystatstable.resizeColumnsToContents()
            hheader.setStretchLastSection(True)

#        # remember the columnwidth
#        for i, _ in enumerate(self.aw.summarystatstablecolumnwidths):
#            try:
#                self.summarystatstable.setColumnWidth(i,self.aw.summarystatstablecolumnwidths[i])
#            except Exception: # pylint: disable=broad-except
#                pass

        self.savetablesummarystats()

    @pyqtSlot(bool)
    def copyEventButtonTabletoClipboard(self, _:bool=False) -> None:
        import prettytable
        nrows = self.summarystatstable.rowCount()
        ncols = self.summarystatstable.columnCount()
        clipboard = ''
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.AltModifier:  #alt click
            tbl = prettytable.PrettyTable()
            fields = []
            #fields.append(' ')  # this column shows the row number
            for c in range(ncols):
                item = self.summarystatstable.horizontalHeaderItem(c)
                if item is not None:
                    fields.append(item.text())
            tbl.field_names = fields
            for r in range(nrows):
                rows = []
                rows.append(str(r+1))
                # type
                typeComboBox = cast(MyContentLimitedQComboBox, self.summarystatstable.cellWidget(r,1))
                rows.append(typeComboBox.currentText())
                tbl.add_row(rows)
            clipboard = tbl.get_string()
        else:
            clipboard += ' ' + '\t'  # this column shows the row number
            for c in range(ncols):
                item = self.summarystatstable.horizontalHeaderItem(c)
                if item is not None:
                    clipboard += item.text()
                    if c != (ncols):
                        clipboard += '\t'
            clipboard += '\n'
            for r in range(nrows):
                clipboard += str(r+1) + '\t'
                typeComboBox = cast(MyContentLimitedQComboBox, self.summarystatstable.cellWidget(r,1))
                clipboard += typeComboBox.currentText() + '\t'
        # copy to the system clipboard
        sys_clip = QApplication.clipboard()
        if sys_clip is not None:
            sys_clip.setText(clipboard)
        self.aw.sendmessage(QApplication.translate('Message','Event Button table copied to clipboard'))


    def savetablesummarystats(self, forceRedraw:bool = False) -> None:
        maxStat = len(self.summarystatstypes)
        prev_summarystatstypes = self.aw.summarystatstypes.copy()

        #Clean Lists:
        #Types
        self.aw.summarystatstypes        = [0] * maxStat

        #Sorting buttons based on the visualRow
        for i in range(maxStat):
            visualIndex = i #self.summarystatstable.visualRow(i)

            #Types
            self.aw.summarystatstypes[visualIndex]        = self.summarystatstypes[i]

        # Conserve redraws
        if prev_summarystatstypes != self.summarystatstypes or forceRedraw:
            self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def setitemsummarystat(self, _:int) -> None:
        i = self.aw.findWidgetsRow(self.summarystatstable,self.sender(),1)
        if i is not None:
            typecombobox = cast(MyContentLimitedQComboBox, self.summarystatstable.cellWidget(i,1))
            if i < len(self.summarystatstypes):
                self.summarystatstypes[i] = self.summarystats_types.index(self.summarystats_types_sorted[typecombobox.currentIndex()])
                self.savetablesummarystats()

    def disconnectTableItemActions(self) -> None:
        for x in range(self.summarystatstable.rowCount()):
            try:
                typeComboBox = cast(MyContentLimitedQComboBox, self.summarystatstable.cellWidget(x,1))
                typeComboBox.currentIndexChanged.disconnect() # type combo
            except Exception: # pylint: disable=broad-except
                pass

    @pyqtSlot(bool)
    def deletesummarystat(self, _:bool = False) -> None:
        bindex = len(self.summarystatstypes)-1
        selected = self.summarystatstable.selectedRanges()

        if len(selected) > 0:
            bindex = selected[0].topRow()

        if bindex >= 0:
            self.disconnectTableItemActions() # we ensure that signals from to be deleted items are not fired anymore
            self.summarystatstypes.pop(bindex)

            self.createSummarystatsTable()
            # workaround a table redrawbug in PyQt 5.14.2 on macOS
            if len(self.summarystatstypes) > 1:
                self.repaint()

    @pyqtSlot(bool)
    def addsummarystatSlot(self, _:bool = False) -> None:
        self.insertsummarystat(insert=False)

    @pyqtSlot(bool)
    def insertsummarystatSlot(self, _:bool = False) -> None:
        self.insertsummarystat(insert=True)

    def insertsummarystat(self, insert:bool = False) -> None:
        try:
            focusWidget = QApplication.focusWidget()
            if focusWidget is not None and isinstance(focusWidget, QLineEdit):
                fw:QLineEdit = focusWidget
                fw.editingFinished.emit()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

        bindex = len(self.summarystatstypes)
        selected = self.summarystatstable.selectedRanges()

        # defaults for new entries
        stat_type:int = 0
#        stat_visibility:int = 1

        if len(selected) > 0:
            selected_idx = selected[0].topRow()
            if insert:
                bindex = selected_idx

        if bindex >= 0:
            self.summarystatstypes.insert(bindex,stat_type)

            self.createSummarystatsTable()
            # workaround a table redrawbug in PyQt 5.14.2 on macOS
            if len(self.summarystatstypes) > 1:
                self.repaint()
            if not insert:
                self.summarystatstable.selectRow(self.summarystatstable.rowCount()-1)

    def storeState(self) -> None:
        self.summarystatstypes = self.aw.summarystatstypes[:]
        self.buttonlistmaxlen = self.aw.buttonlistmaxlen

    #called from OK button
    @pyqtSlot()
    def updatetypes(self) -> None:
        try:
#            self.closeHelp()
#            # save column widths
#            self.aw.summarystatstablecolumnwidths = [self.summarystatstable.columnWidth(c) for c in range(self.summarystatstable.columnCount())]
            self.savetablesummarystats()
            self.aw.sendmessage(QApplication.translate('Message','Statistics configuration saved'))
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' updatetypes(): {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def restoreDefaults(self, _:bool = False) -> None:
        self.summarystatstypes = self.aw.summarystatstypes_default.copy()
        self.createSummarystatsTable()
        #self.savetablesummarystats(True)
        self.summarystatstable.cursor_navigation = True
        vheader = self.summarystatstable.verticalHeader()
        if vheader is not None:
            vheader.setFocus()


    @pyqtSlot('QCloseEvent')
    def closeEvent(self,_:Optional['QCloseEvent'] = None) -> None:
#        self.closeHelp()
        settings = QSettings()
        #save window geometry
        settings.setValue('StatisticsGeometry',self.saveGeometry())
        self.aw.StatisticsDlg_activeTab = self.TabWidget.currentIndex()

#    @pyqtSlot(bool)
#    def showSummarystatshelp(self, _:bool = False) -> None:
#        from help import eventbuttons_help # pyright: ignore [attr-defined] # pylint: disable=no-name-in-module
#        self.helpdialog = self.aw.showHelpDialog(
#                self,            # this dialog as parent
#                self.helpdialog, # the existing help dialog
#                QApplication.translate('Form Caption','Summary Stats Config Help'),
#                eventbuttons_help.content())
#
#    def closeHelp(self) -> None:
#        self.aw.closeHelpDialog(self.helpdialog)
