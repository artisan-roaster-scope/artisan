#
# ABOUT
# Artisan Template Background Dialog

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
import logging

from artisanlib.util import deltaLabelUTF8, deltaLabelPrefix, stringfromseconds
from artisanlib.dialogs import ArtisanResizeablDialog
from artisanlib.widgets import (MyTableWidgetItemNumber)
from typing import Final, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent, QKeyEvent # pylint: disable=unused-import

try:
    from PyQt6.QtCore import (Qt, pyqtSlot, QSettings, QTimer) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QColor, QKeySequence # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QCheckBox, QGridLayout, QHBoxLayout, QVBoxLayout, # @UnusedImport @Reimport  @UnresolvedImport
                                 QLabel, QLineEdit,QPushButton, QComboBox, QDialogButtonBox, QHeaderView, # @UnusedImport @Reimport  @UnresolvedImport
                                 QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QWidget, QGroupBox) # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import (Qt, pyqtSlot, QSettings, QTimer) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QColor, QKeySequence # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QCheckBox, QGridLayout, QHBoxLayout, QVBoxLayout, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
                                 QLabel, QLineEdit,QPushButton, QComboBox, QDialogButtonBox, QHeaderView, # @UnusedImport @Reimport  @UnresolvedImport
                                 QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QWidget, QGroupBox) # @UnusedImport @Reimport  @UnresolvedImport



_log: Final[logging.Logger] = logging.getLogger(__name__)

class backgroundDlg(ArtisanResizeablDialog):
    def __init__(self, parent:QWidget, aw:'ApplicationWindow', activeTab:int = 0) -> None:
        super().__init__(parent, aw)
        self.activeTab = activeTab

        self.ETname = self.aw.qmc.device_name_subst(self.aw.ETname)
        self.BTname = self.aw.qmc.device_name_subst(self.aw.BTname)

        self.setWindowTitle(QApplication.translate('Form Caption','Profile Background'))
        self.setModal(True)

        settings = QSettings()
        if settings.contains('BackgroundGeometry'):
            self.restoreGeometry(settings.value('BackgroundGeometry'))

        #TAB 1
        self.pathedit = QLineEdit(self.aw.qmc.backgroundpath)
        self.pathedit.setStyleSheet("background-color:'lightgrey';")
        self.pathedit.setReadOnly(True)
        self.pathedit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.filename = ''
        self.backgroundCheck = QCheckBox(QApplication.translate('CheckBox','Show'))
        self.backgroundDetails = QCheckBox(QApplication.translate('CheckBox','Annotations'))
        self.backgroundeventsflag = QCheckBox(QApplication.translate('CheckBox','Events'))
        self.backgroundDeltaETflag = QCheckBox()
        backgroundDeltaETflagLabel = QLabel(deltaLabelPrefix + self.ETname)
        self.backgroundDeltaBTflag = QCheckBox()
        backgroundDeltaBTflagLabel = QLabel(deltaLabelPrefix + self.BTname)
        self.backgroundETflag = QCheckBox(self.ETname)
        self.backgroundBTflag = QCheckBox(self.BTname)
        self.backgroundFullflag = QCheckBox(QApplication.translate('CheckBox','Show Full'))
        self.keyboardControlflag = QCheckBox(QApplication.translate('CheckBox','Keyboard Control'))
        self.keyboardControlflag.setToolTip(QApplication.translate('Tooltip', 'Move the background profile using the cursor keys'))
        self.backgroundCheck.setChecked(self.aw.qmc.background)
        self.backgroundDetails.setChecked(self.aw.qmc.backgroundDetails)
        self.backgroundeventsflag.setChecked(self.aw.qmc.backgroundeventsflag)
        self.backgroundDeltaETflag.setChecked(self.aw.qmc.DeltaETBflag)
        self.backgroundDeltaBTflag.setChecked(self.aw.qmc.DeltaBTBflag)
        self.backgroundETflag.setChecked(self.aw.qmc.backgroundETcurve)
        self.backgroundBTflag.setChecked(self.aw.qmc.backgroundBTcurve)
        self.backgroundFullflag.setChecked(self.aw.qmc.backgroundShowFullflag)
        self.keyboardControlflag.setChecked(self.aw.qmc.backgroundKeyboardControlFlag)
        loadButton = QPushButton(QApplication.translate('Button','Load'))
        loadButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        delButton = QPushButton(QApplication.translate('Button','Delete'))
        delButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.accept)
        self.dialogbuttons.removeButton(self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel))

        alignButton = QPushButton(QApplication.translate('Button','Align'))
        alignButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.alignComboBox = QComboBox()
        self.aw.qmc.alignnames = [
            QApplication.translate('Label','CHARGE'),
            QApplication.translate('Label','DRY'),
            QApplication.translate('Label','FCs'),
            QApplication.translate('Label','FCe'),
            QApplication.translate('Label','SCs'),
            QApplication.translate('Label','SCe'),
            QApplication.translate('Label','DROP'),
            QApplication.translate('Label','ALL'),
            ]
        self.alignComboBox.addItems(self.aw.qmc.alignnames)
        self.alignComboBox.setCurrentIndex(self.aw.qmc.alignEvent)
        self.alignComboBox.currentIndexChanged.connect(self.changeAlignEventidx)
        loadButton.clicked.connect(self.load)
        alignButton.clicked.connect(self.timealign)

        self.speedSpinBox = QSpinBox()
        self.speedSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.speedSpinBox.setRange(1,90)
        self.speedSpinBox.setSingleStep(5)
        self.speedSpinBox.setValue(int(self.aw.qmc.backgroundmovespeed))

        curvenames = [''] # first entry is the empty one, no extra curve displayed
        for i in range(min(len(self.aw.qmc.extraname1B),len(self.aw.qmc.extraname2B),len(self.aw.qmc.extratimexB))):
            curvenames.append('B' + str(2*i+3) + ': ' + self.aw.qmc.extraname1B[i].format(
                self.aw.qmc.Betypesf(0),self.aw.qmc.Betypesf(1),self.aw.qmc.Betypesf(2),self.aw.qmc.Betypesf(3),self.aw.qmc.mode))
            curvenames.append('B' + str(2*i+4) + ': ' + self.aw.qmc.extraname2B[i].format(
                self.aw.qmc.Betypesf(0),self.aw.qmc.Betypesf(1),self.aw.qmc.Betypesf(2),self.aw.qmc.Betypesf(3),self.aw.qmc.mode))

        self.xtcurvelabel = QLabel(QApplication.translate('Label', 'Extra 1'))
        self.xtcurveComboBox = QComboBox()
        self.xtcurveComboBox.setToolTip(QApplication.translate('Tooltip','For loaded backgrounds with extra devices only'))
        self.xtcurveComboBox.setMinimumWidth(120)
        self.xtcurveComboBox.addItems(curvenames)
        if self.aw.qmc.xtcurveidx < len(curvenames):
            self.xtcurveComboBox.setCurrentIndex(self.aw.qmc.xtcurveidx)
        self.xtcurveComboBox.currentIndexChanged.connect(self.changeXTcurveidx)

        self.ytcurvelabel = QLabel(QApplication.translate('Label', 'Extra 2'))
        self.ytcurveComboBox = QComboBox()
        self.ytcurveComboBox.setToolTip(QApplication.translate('Tooltip','For loaded backgrounds with extra devices only'))
        self.ytcurveComboBox.setMinimumWidth(120)
        self.ytcurveComboBox.addItems(curvenames)
        if self.aw.qmc.ytcurveidx < len(curvenames):
            self.ytcurveComboBox.setCurrentIndex(self.aw.qmc.ytcurveidx)
        self.ytcurveComboBox.currentIndexChanged.connect(self.changeYTcurveidx)

        self.upButton = QPushButton(QApplication.translate('Button','Up'))
        self.upButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.downButton = QPushButton(QApplication.translate('Button','Down'))
        self.downButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.leftButton = QPushButton(QApplication.translate('Button','Left'))
        self.leftButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.rightButton = QPushButton(QApplication.translate('Button','Right'))
        self.rightButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundCheck.clicked.connect(self.readChecks)
        self.backgroundDetails.clicked.connect(self.readChecks)
        self.backgroundeventsflag.clicked.connect(self.readChecks)
        self.backgroundDeltaETflag.clicked.connect(self.readChecks)
        self.backgroundDeltaBTflag.clicked.connect(self.readChecks)
        self.backgroundETflag.clicked.connect(self.readChecks)
        self.backgroundBTflag.clicked.connect(self.readChecks)
        self.backgroundFullflag.clicked.connect(self.readChecks)
        delButton.clicked.connect(self.delete)
        self.upButton.clicked.connect(self.moveUp)
        self.downButton.clicked.connect(self.moveDown)
        self.leftButton.clicked.connect(self.moveLeft)
        self.rightButton.clicked.connect(self.moveRight)
        #TAB 2 EVENTS
        #table for showing events
        self.eventtable = QTableWidget()
        self.eventtable.setTabKeyNavigation(True)
        self.copyeventTableButton = QPushButton(QApplication.translate('Button', 'Copy Table'))
        self.copyeventTableButton.setToolTip(QApplication.translate('Tooltip','Copy table to clipboard, OPTION or ALT click for tabular text'))
        self.copyeventTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.copyeventTableButton.setMaximumSize(self.copyeventTableButton.sizeHint())
        self.copyeventTableButton.setMinimumSize(self.copyeventTableButton.minimumSizeHint())
        self.copyeventTableButton.clicked.connect(self.copyEventTabletoClipboard)
        #TAB 3 DATA
        #table for showing data
        self.datatable = QTableWidget()
        self.datatable.setTabKeyNavigation(True)
        self.copydataTableButton = QPushButton(QApplication.translate('Button', 'Copy Table'))
        self.copydataTableButton.setToolTip(QApplication.translate('Tooltip','Copy table to clipboard, OPTION or ALT click for tabular text'))
        self.copydataTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.copydataTableButton.setMaximumSize(self.copydataTableButton.sizeHint())
        self.copydataTableButton.setMinimumSize(self.copydataTableButton.minimumSizeHint())
        self.copydataTableButton.clicked.connect(self.copyDataTabletoClipboard)
        #TAB 4
        self.replayComboBox = QComboBox()
        replayVariants = [
            QApplication.translate('Label','by time'),
            QApplication.translate('Label','by BT').replace('BT', self.aw.BTname),
            QApplication.translate('Label','by ET').replace('ET', self.aw.ETname),
            QApplication.translate('Label','by time/BT').replace('BT', self.aw.BTname),
            QApplication.translate('Label','by time/ET').replace('ET', self.aw.ETname),
            ]
        self.replayComboBox.addItems(replayVariants)
        self.replayComboBox.setCurrentIndex(self.aw.qmc.replayType)
        self.replayComboBox.currentIndexChanged.connect(self.changeReplayTypeidx)
        self.replayComboBox.setEnabled(self.aw.qmc.backgroundPlaybackEvents)

        self.replayDropComboBox = QComboBox()
        replayDropVariants = [
            QApplication.translate('Label','by time'),
            QApplication.translate('Label','by BT').replace('BT', self.aw.BTname),
            QApplication.translate('Label','by ET').replace('ET', self.aw.ETname),
            ]
        self.replayDropComboBox.addItems(replayDropVariants)
        self.replayDropComboBox.setCurrentIndex(self.aw.qmc.replayDropType)
        self.replayDropComboBox.currentIndexChanged.connect(self.changeReplayDropTypeidx)
        self.replayDropComboBox.setEnabled(self.aw.qmc.backgroundPlaybackDROP)

        self.backgroundReproduce = QCheckBox(QApplication.translate('CheckBox','Playback Aid'))
        self.backgroundReproduce.setChecked(self.aw.qmc.backgroundReproduce)
        self.backgroundReproduce.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundReproduce.stateChanged.connect(self.setreproduce)
        self.backgroundReproduceBeep = QCheckBox(QApplication.translate('CheckBox','Beep'))
        self.backgroundReproduceBeep.setChecked(self.aw.qmc.backgroundReproduceBeep)
        self.backgroundReproduceBeep.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundReproduceBeep.setEnabled(self.aw.qmc.backgroundReproduce)
        self.backgroundReproduceBeep.stateChanged.connect(self.setreproduceBeep)
        self.backgroundPlaybackEvents = QCheckBox(QApplication.translate('CheckBox','Playback Events'))
        self.backgroundPlaybackEvents.setChecked(self.aw.qmc.backgroundPlaybackEvents)
        self.backgroundPlaybackEvents.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackEvents.stateChanged.connect(self.setplaybackevent)
        self.backgroundPlaybackEvents.setToolTip(QApplication.translate('Tooltip', 'Replays the selected backgrounds events by time, BT, or ET (before TP always by time at least until 2min into the roast)'))
        self.backgroundPlaybackDROP = QCheckBox(QApplication.translate('CheckBox','Playback DROP'))
        self.backgroundPlaybackDROP.setChecked(self.aw.qmc.backgroundPlaybackDROP)
        self.backgroundPlaybackDROP.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackDROP.stateChanged.connect(self.setplaybackdrop)
        self.backgroundPlaybackDROP.setToolTip(QApplication.translate('Tooltip', 'Replays the backgrounds DROP event by time, BT, or ET (but earlierst 4min into the roast)'))
        self.etimelabel =QLabel(QApplication.translate('Label', 'Text Warning'))
        self.etimelabel.setEnabled(self.aw.qmc.backgroundReproduce)
        self.etimeunit =QLabel(QApplication.translate('Label', 'sec'))
        self.etimeunit.setEnabled(self.aw.qmc.backgroundReproduce)
        self.etimeSpinBox = QSpinBox()
        self.etimeSpinBox.setRange(1,60)
        self.etimeSpinBox.setValue(int(self.aw.qmc.detectBackgroundEventTime))
        self.etimeSpinBox.valueChanged.connect(self.setreproduce)
        self.etimeSpinBox.setEnabled(self.aw.qmc.backgroundReproduce)
        self.clearBgbeforeprofileload = QCheckBox(QApplication.translate('CheckBox','Clear background before loading'))
        self.clearBgbeforeprofileload.setToolTip(QApplication.translate('Tooltip', 'Clear background before loading a profile'))
        self.clearBgbeforeprofileload.setChecked(self.aw.qmc.clearBgbeforeprofileload)
        self.clearBgbeforeprofileload.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.clearBgbeforeprofileload.stateChanged.connect(self.optclearbgbeforeprofileload)
        self.setBatchSizeFromBackground = QCheckBox(QApplication.translate('CheckBox','Set batch size'))
        self.setBatchSizeFromBackground.setToolTip(QApplication.translate('Tooltip', 'Set batch size from background profile on load'))
        self.setBatchSizeFromBackground.setChecked(self.aw.qmc.setBatchSizeFromBackground)
        self.setBatchSizeFromBackground.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setBatchSizeFromBackground.stateChanged.connect(self.optsetBatchSizeFromBackground)
        self.hideBgafterprofileload = QCheckBox(QApplication.translate('CheckBox','Always hide background on loading'))
        self.hideBgafterprofileload.setToolTip(QApplication.translate('Tooltip', 'Always hide background on loading a profile'))
        self.hideBgafterprofileload.setChecked(self.aw.qmc.hideBgafterprofileload)
        self.hideBgafterprofileload.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.hideBgafterprofileload.stateChanged.connect(self.opthideBgafterprofileload)

        #LAYOUT MANAGERS
        movelayout = QGridLayout()
        movelayout.addWidget(self.upButton,0,1)
        movelayout.addWidget(self.leftButton,1,0)
        movelayout.addWidget(self.speedSpinBox,1,1)
        movelayout.addWidget(self.rightButton,1,2)
        movelayout.addWidget(self.downButton,2,1)
        movelayout.setSpacing(15)
        checkslayout1 = QHBoxLayout()
        checkslayout1.addStretch()
        checkslayout1.addWidget(self.backgroundCheck)
        checkslayout1.addSpacing(5)
        checkslayout1.addWidget(self.backgroundDetails)
        checkslayout1.addSpacing(5)
        checkslayout1.addWidget(self.backgroundeventsflag)
        checkslayout1.addSpacing(5)
        checkslayout1.addWidget(self.backgroundETflag)
        checkslayout1.addSpacing(5)
        checkslayout1.addWidget(self.backgroundBTflag)
        checkslayout1.addSpacing(5)
        checkslayout1.addWidget(self.backgroundDeltaETflag)
        checkslayout1.addSpacing(3)
        checkslayout1.addWidget(backgroundDeltaETflagLabel)
        checkslayout1.addSpacing(5)
        checkslayout1.addWidget(self.backgroundDeltaBTflag)
        checkslayout1.addSpacing(3)
        checkslayout1.addWidget(backgroundDeltaBTflagLabel)
        checkslayout1.addSpacing(5)
        checkslayout1.addWidget(self.backgroundFullflag)
        checkslayout1.addStretch()
        layoutBoxedH = QHBoxLayout()
        layoutBoxedH.addStretch()
        layoutBoxedH.addStretch()
        layoutBoxedH.addLayout(movelayout)
        layoutBoxedH.addStretch()
        layoutBoxedH.addWidget(self.keyboardControlflag)
        layoutBoxed = QVBoxLayout()
        layoutBoxed.addStretch()
        layoutBoxed.addLayout(checkslayout1)
        layoutBoxed.addStretch()
        layoutBoxed.addLayout(layoutBoxedH)
        layoutBoxed.addStretch()
        alignButtonBoxed = QHBoxLayout()
        alignButtonBoxed.addWidget(self.xtcurvelabel)
        alignButtonBoxed.addWidget(self.xtcurveComboBox)
        alignButtonBoxed.addSpacing(10)
        alignButtonBoxed.addWidget(self.ytcurvelabel)
        alignButtonBoxed.addWidget(self.ytcurveComboBox)
        alignButtonBoxed.addStretch()
        alignButtonBoxed.addWidget(alignButton)
        alignButtonBoxed.addWidget(self.alignComboBox)

        self.backgroundPlaybackAid0 = QCheckBox(self.aw.qmc.etypesf(0))
        self.backgroundPlaybackAid0.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackAid0.setChecked(self.aw.qmc.specialeventplaybackaid[0])
        self.backgroundPlaybackAid0.stateChanged.connect(self.setplaybackaideventtypeenabled)
        self.backgroundPlaybackAid0.setEnabled(self.aw.qmc.backgroundReproduce)

        self.backgroundPlaybackAid1 = QCheckBox(self.aw.qmc.etypesf(1))
        self.backgroundPlaybackAid1.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackAid1.setChecked(self.aw.qmc.specialeventplaybackaid[1])
        self.backgroundPlaybackAid1.stateChanged.connect(self.setplaybackaideventtypeenabled)
        self.backgroundPlaybackAid1.setEnabled(self.aw.qmc.backgroundReproduce)

        self.backgroundPlaybackAid2 = QCheckBox(self.aw.qmc.etypesf(2))
        self.backgroundPlaybackAid2.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackAid2.setChecked(self.aw.qmc.specialeventplaybackaid[2])
        self.backgroundPlaybackAid2.stateChanged.connect(self.setplaybackaideventtypeenabled)
        self.backgroundPlaybackAid2.setEnabled(self.aw.qmc.backgroundReproduce)

        self.backgroundPlaybackAid3 = QCheckBox(self.aw.qmc.etypesf(3))
        self.backgroundPlaybackAid3.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackAid3.setChecked(self.aw.qmc.specialeventplaybackaid[3])
        self.backgroundPlaybackAid3.stateChanged.connect(self.setplaybackaideventtypeenabled)
        self.backgroundPlaybackAid3.setEnabled(self.aw.qmc.backgroundReproduce)

        tab4content1 = QHBoxLayout()
        tab4content1.addWidget(self.backgroundReproduce)
        tab4content1.addSpacing(10)
        tab4content1.addWidget(self.backgroundReproduceBeep)
        tab4content1.addSpacing(10)
        tab4content1.addWidget(self.etimelabel)
        tab4content1.addWidget(self.etimeSpinBox)
        tab4content1.addWidget(self.etimeunit)
        tab4content1.addSpacing(20)
        tab4content1.addStretch()
        tab4content1.addWidget(self.backgroundPlaybackAid0)
        tab4content1.addSpacing(10)
        tab4content1.addWidget(self.backgroundPlaybackAid1)
        tab4content1.addSpacing(10)
        tab4content1.addWidget(self.backgroundPlaybackAid2)
        tab4content1.addSpacing(10)
        tab4content1.addWidget(self.backgroundPlaybackAid3)

        self.backgroundPlaybackEvent0 = QCheckBox(self.aw.qmc.etypesf(0))
        self.backgroundPlaybackEvent0.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackEvent0.setChecked(self.aw.qmc.specialeventplayback[0])
        self.backgroundPlaybackEvent0.stateChanged.connect(self.setplaybackeventtypeenabled)
        self.backgroundPlaybackEvent0.setEnabled(self.aw.qmc.backgroundPlaybackEvents)

        self.backgroundPlaybackEvent1 = QCheckBox(self.aw.qmc.etypesf(1))
        self.backgroundPlaybackEvent1.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackEvent1.setChecked(self.aw.qmc.specialeventplayback[1])
        self.backgroundPlaybackEvent1.stateChanged.connect(self.setplaybackeventtypeenabled)
        self.backgroundPlaybackEvent1.setEnabled(self.aw.qmc.backgroundPlaybackEvents)

        self.backgroundPlaybackEvent2 = QCheckBox(self.aw.qmc.etypesf(2))
        self.backgroundPlaybackEvent2.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackEvent2.setChecked(self.aw.qmc.specialeventplayback[2])
        self.backgroundPlaybackEvent2.stateChanged.connect(self.setplaybackeventtypeenabled)
        self.backgroundPlaybackEvent2.setEnabled(self.aw.qmc.backgroundPlaybackEvents)

        self.backgroundPlaybackEvent3 = QCheckBox(self.aw.qmc.etypesf(3))
        self.backgroundPlaybackEvent3.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackEvent3.setChecked(self.aw.qmc.specialeventplayback[3])
        self.backgroundPlaybackEvent3.stateChanged.connect(self.setplaybackeventtypeenabled)
        self.backgroundPlaybackEvent3.setEnabled(self.aw.qmc.backgroundPlaybackEvents)

        tab4content2 = QHBoxLayout()
        tab4content2.addWidget(self.backgroundPlaybackEvents)
        tab4content2.addSpacing(10)
        tab4content2.addWidget(self.replayComboBox)
        tab4content2.addStretch()
        tab4content2.addSpacing(10)
        tab4content2.addWidget(self.backgroundPlaybackEvent0)
        tab4content2.addSpacing(10)
        tab4content2.addWidget(self.backgroundPlaybackEvent1)
        tab4content2.addSpacing(10)
        tab4content2.addWidget(self.backgroundPlaybackEvent2)
        tab4content2.addSpacing(10)
        tab4content2.addWidget(self.backgroundPlaybackEvent3)

        self.playbackRampLabel = QLabel(QApplication.translate('Label', 'Ramp'))

        self.backgroundPlaybackRampEvent0 = QCheckBox(self.aw.qmc.etypesf(0))
        self.backgroundPlaybackRampEvent0.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackRampEvent0.setChecked(self.aw.qmc.specialeventplaybackramp[0])
        self.backgroundPlaybackRampEvent0.stateChanged.connect(self.setplaybackeventrampenabled)
        self.backgroundPlaybackRampEvent0.setEnabled(self.aw.qmc.backgroundPlaybackEvents and self.aw.qmc.specialeventplayback[0])

        self.backgroundPlaybackRampEvent1 = QCheckBox(self.aw.qmc.etypesf(1))
        self.backgroundPlaybackRampEvent1.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackRampEvent1.setChecked(self.aw.qmc.specialeventplaybackramp[1])
        self.backgroundPlaybackRampEvent1.stateChanged.connect(self.setplaybackeventrampenabled)
        self.backgroundPlaybackRampEvent1.setEnabled(self.aw.qmc.backgroundPlaybackEvents and self.aw.qmc.specialeventplayback[1])

        self.backgroundPlaybackRampEvent2 = QCheckBox(self.aw.qmc.etypesf(2))
        self.backgroundPlaybackRampEvent2.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackRampEvent2.setChecked(self.aw.qmc.specialeventplaybackramp[2])
        self.backgroundPlaybackRampEvent2.stateChanged.connect(self.setplaybackeventrampenabled)
        self.backgroundPlaybackRampEvent2.setEnabled(self.aw.qmc.backgroundPlaybackEvents and self.aw.qmc.specialeventplayback[2])

        self.backgroundPlaybackRampEvent3 = QCheckBox(self.aw.qmc.etypesf(3))
        self.backgroundPlaybackRampEvent3.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundPlaybackRampEvent3.setChecked(self.aw.qmc.specialeventplaybackramp[3])
        self.backgroundPlaybackRampEvent3.stateChanged.connect(self.setplaybackeventrampenabled)
        self.backgroundPlaybackRampEvent3.setEnabled(self.aw.qmc.backgroundPlaybackEvents and self.aw.qmc.specialeventplayback[3])

        tab4content3 = QHBoxLayout()
        tab4content3.addStretch()
        tab4content3.addWidget(self.playbackRampLabel)
        tab4content3.addSpacing(10)
        tab4content3.addWidget(self.backgroundPlaybackRampEvent0)
        tab4content3.addSpacing(10)
        tab4content3.addWidget(self.backgroundPlaybackRampEvent1)
        tab4content3.addSpacing(10)
        tab4content3.addWidget(self.backgroundPlaybackRampEvent2)
        tab4content3.addSpacing(10)
        tab4content3.addWidget(self.backgroundPlaybackRampEvent3)

        tab4content4 = QHBoxLayout()
        tab4content4.addWidget(self.backgroundPlaybackDROP)
        tab4content4.addSpacing(10)
        tab4content4.addWidget(self.replayDropComboBox)
        tab4content4.addStretch()

        tab4content = QVBoxLayout()
        tab4content.addLayout(tab4content1)
        tab4content.addLayout(tab4content2)
        tab4content.addLayout(tab4content3)
        tab4content.addLayout(tab4content4)
        tab4content.setSpacing(5)
        tab4content.setContentsMargins(2, 5, 2, 5) # left, top, right, bottom

        playbackGroupLayout = QGroupBox(QApplication.translate('GroupBox','Playback'))
        playbackGroupLayout.setLayout(tab4content)

        optcontent = QHBoxLayout()
        optcontent.addWidget(self.clearBgbeforeprofileload)
        optcontent.addSpacing(5)
        optcontent.addStretch()
        optcontent.addWidget(self.setBatchSizeFromBackground)
        optcontent.addSpacing(5)
        optcontent.addStretch()
        optcontent.addWidget(self.hideBgafterprofileload)
        tab1layout = QVBoxLayout()
        tab1layout.addLayout(layoutBoxed)
#        tab1layout.addStretch()
        tab1layout.addLayout(alignButtonBoxed)
        tab1layout.addWidget(playbackGroupLayout)
        tab1layout.addLayout(optcontent)
        tab1layout.setContentsMargins(5, 0, 5, 0) # left, top, right, bottom
        tab1layout.setSpacing(5)
        eventbuttonLayout = QHBoxLayout()
        eventbuttonLayout.addWidget(self.copyeventTableButton)
        eventbuttonLayout.addStretch()
        tab2layout = QVBoxLayout()
        tab2layout.addWidget(self.eventtable)
        tab2layout.addLayout(eventbuttonLayout)
        tab2layout.setContentsMargins(5, 0, 5, 0) # left, top, right, bottom
        databuttonLayout = QHBoxLayout()
        databuttonLayout.addWidget(self.copydataTableButton)
        databuttonLayout.addStretch()
        tab3layout = QVBoxLayout()
        tab3layout.addWidget(self.datatable)
        tab3layout.addLayout(databuttonLayout)
        tab3layout.setContentsMargins(5, 0, 5, 0) # left, top, right, bottom
        #tab layout
        self.TabWidget = QTabWidget()
        C1Widget = QWidget()
        C1Widget.setLayout(tab1layout)
        self.TabWidget.addTab(C1Widget,QApplication.translate('Tab','Config'))
        C2Widget = QWidget()
        C2Widget.setLayout(tab2layout)
        self.TabWidget.addTab(C2Widget,QApplication.translate('Tab','Events'))
        C3Widget = QWidget()
        C3Widget.setLayout(tab3layout)
        self.TabWidget.addTab(C3Widget,QApplication.translate('Tab','Data'))
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(loadButton)
        buttonLayout.addWidget(delButton)
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.TabWidget)
        mainLayout.addWidget(self.pathedit)
        mainLayout.addLayout(buttonLayout)
        mainLayout.setContentsMargins(5, 10, 5, 5) # left, top, right, bottom
        mainLayout.setSpacing(5)
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

    @pyqtSlot(int)
    def tabSwitched(self, i:int) -> None:
        if i == 1:
            self.createEventTable()
        elif i == 2:
            self.createDataTable()

    @pyqtSlot()
    def setActiveTab(self) -> None:
        if self.activeTab == 1:
            self.createEventTable()
        elif self.activeTab == 2:
            self.createDataTable()
        self.TabWidget.setCurrentIndex(self.activeTab)

    @pyqtSlot(bool)
    def timealign(self, _:bool = False) -> None:
        self.aw.qmc.timealign()
        self.aw.autoAdjustAxis()

    #keyboard presses. There must not be widgets (pushbuttons, comboboxes, etc) in focus in order to work
    def keyPressEvent(self, event: Optional['QKeyEvent']) -> None:
        if event is not None and event.matches(QKeySequence.StandardKey.Copy):
            if self.TabWidget.currentIndex() == 2: # datatable
                self.aw.copy_cells_to_clipboard(self.datatable)
                self.aw.sendmessage(QApplication.translate('Message','Data table copied to clipboard'))
        else:
            super().keyPressEvent(event)

    @pyqtSlot()
    def accept(self) -> None:
        self.aw.qmc.backgroundmovespeed = self.speedSpinBox.value()
        self.aw.qmc.backgroundKeyboardControlFlag = bool(self.keyboardControlflag.isChecked())
        if self.aw.qmc.backgroundPlaybackEvents:
            # turn on again after background load to ignore already passed events
            self.aw.qmc.turn_playback_event_ON()
        self.close()

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        settings = QSettings()
        #save window geometry
        settings.setValue('BackgroundGeometry',self.saveGeometry())
        self.aw.backgroundDlg_activeTab = self.TabWidget.currentIndex()
#        self.aw.closeEventSettings() # save all app settings

#    def getColorIdx(self,c):
#        try:
#            return self.defaultcolorsmapped.index(c)
#        except Exception: # pylint: disable=broad-except
#            try:
#                return self.colors.index(c) + 5
#            except Exception:  # pylint: disable=broad-except
#                return 0

    @pyqtSlot(int)
    def setplaybackevent(self, _:int) -> None:
        s = None
        if self.backgroundPlaybackEvents.isChecked():
            self.aw.qmc.turn_playback_event_ON()
            msg = QApplication.translate('Message','Playback Events set ON')
        else:
            self.aw.qmc.turn_playback_event_OFF()
            msg = QApplication.translate('StatusBar','Playback Events set OFF')
            s = "background-color:'transparent';"
        self.aw.sendmessage(msg, style=s)
        self.aw.updatePlaybackIndicator()
        for widget in [
                self.replayComboBox,
                self.backgroundPlaybackEvent0,
                self.backgroundPlaybackEvent1,
                self.backgroundPlaybackEvent2,
                self.backgroundPlaybackEvent3,
                ]:
            widget.setEnabled(self.aw.qmc.backgroundPlaybackEvents)
        for i, widget in enumerate([
                self.backgroundPlaybackRampEvent0,
                self.backgroundPlaybackRampEvent1,
                self.backgroundPlaybackRampEvent2,
                self.backgroundPlaybackRampEvent3,
                ]):
            widget.setEnabled(self.aw.qmc.backgroundPlaybackEvents and self.aw.qmc.specialeventplayback[i])

    @pyqtSlot(int)
    def setplaybackaideventtypeenabled(self, _:int) -> None:
        for i, widget in enumerate([
                self.backgroundPlaybackAid0,
                self.backgroundPlaybackAid1,
                self.backgroundPlaybackAid2,
                self.backgroundPlaybackAid3]):
            self.aw.qmc.specialeventplaybackaid[i] = widget.isChecked()

    @pyqtSlot(int)
    def setplaybackeventtypeenabled(self, _:int) -> None:
        for i, widget in enumerate([
                self.backgroundPlaybackEvent0,
                self.backgroundPlaybackEvent1,
                self.backgroundPlaybackEvent2,
                self.backgroundPlaybackEvent3]):
            self.aw.qmc.specialeventplayback[i] = widget.isChecked()
        for i, widget in enumerate([
                self.backgroundPlaybackRampEvent0,
                self.backgroundPlaybackRampEvent1,
                self.backgroundPlaybackRampEvent2,
                self.backgroundPlaybackRampEvent3,
                ]):
            widget.setEnabled(self.aw.qmc.backgroundPlaybackEvents and self.aw.qmc.specialeventplayback[i])

    @pyqtSlot(int)
    def setplaybackeventrampenabled(self, _:int) -> None:
        for i, widget in enumerate([
                self.backgroundPlaybackRampEvent0,
                self.backgroundPlaybackRampEvent1,
                self.backgroundPlaybackRampEvent2,
                self.backgroundPlaybackRampEvent3]):
            self.aw.qmc.specialeventplaybackramp[i] = widget.isChecked()
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def setplaybackdrop(self, _:int) -> None:
        s = None
        if self.backgroundPlaybackDROP.isChecked():
            self.aw.qmc.backgroundPlaybackDROP = True
            msg = QApplication.translate('Message','Playback DROP set ON')
        else:
            self.aw.qmc.backgroundPlaybackDROP = False
            msg = QApplication.translate('StatusBar','Playback DROP set OFF')
            s = "background-color:'transparent';"
        self.replayDropComboBox.setEnabled(self.aw.qmc.backgroundPlaybackDROP)
        self.aw.sendmessage(msg, style=s)

    @pyqtSlot(int)
    def setreproduceBeep(self, _:int) -> None:
        if self.backgroundReproduceBeep.isChecked():
            self.aw.qmc.backgroundReproduceBeep = True
        else:
            self.aw.qmc.backgroundReproduceBeep = False

    @pyqtSlot(int)
    def setreproduce(self, _:int) -> None:
        self.aw.qmc.detectBackgroundEventTime = self.etimeSpinBox.value()
        s = None
        if self.backgroundReproduce.isChecked():
            self.aw.qmc.backgroundReproduce = True
            msg = QApplication.translate('Message','Playback Aid set ON at {0} secs').format(str(self.aw.qmc.detectBackgroundEventTime))
        else:
            self.aw.qmc.backgroundReproduce = False
            msg = QApplication.translate('StatusBar','Playback Aid set OFF')
            s = "background-color:'transparent';"
        self.aw.sendmessage(msg, style=s)
        for widget in [
                self.backgroundPlaybackAid0,
                self.backgroundPlaybackAid1,
                self.backgroundPlaybackAid2,
                self.backgroundPlaybackAid3,
#                self.backgroundPlaybackAid0Label,
#                self.backgroundPlaybackAid1Label,
#                self.backgroundPlaybackAid2Label,
#                self.backgroundPlaybackAid3Label
                ]:
            widget.setEnabled(self.aw.qmc.backgroundReproduce)
        self.backgroundReproduceBeep.setEnabled(self.aw.qmc.backgroundReproduce)
        self.etimeSpinBox.setEnabled(self.aw.qmc.backgroundReproduce)
        self.etimelabel.setEnabled(self.aw.qmc.backgroundReproduce)
        self.etimeunit.setEnabled(self.aw.qmc.backgroundReproduce)

    @pyqtSlot(int)
    def optsetBatchSizeFromBackground(self, _:int) -> None:
        if self.setBatchSizeFromBackground.isChecked():
            self.aw.qmc.setBatchSizeFromBackground = True
        else:
            self.aw.qmc.setBatchSizeFromBackground = False

    @pyqtSlot(int)
    def optclearbgbeforeprofileload(self, _:int) -> None:
        if self.clearBgbeforeprofileload.isChecked():
            self.aw.qmc.clearBgbeforeprofileload = True
        else:
            self.aw.qmc.clearBgbeforeprofileload = False

    @pyqtSlot(int)
    def opthideBgafterprofileload(self, _:int) -> None:
        if self.hideBgafterprofileload.isChecked():
            self.aw.qmc.hideBgafterprofileload = True
        else:
            self.aw.qmc.hideBgafterprofileload = False

#    def adjustcolor(self,curve):
#
#        curve = str(curve).lower()
#
#        etcolor = str(self.metcolorComboBox.currentText()).lower()
#        btcolor = str(self.btcolorComboBox.currentText()).lower()
#        deltabtcolor = str(self.deltabtcolorComboBox.currentText()).lower()
#        deltaetcolor = str(self.deltaetcolorComboBox.currentText()).lower()
#        xtcolor = str(self.xtcolorComboBox.currentText()).lower()
#
#        defaults =  ['et','bt','deltaet','deltabt']
#
#        if curve == 'et':
#            if etcolor in defaults:
#                self.aw.qmc.backgroundmetcolor = self.aw.qmc.palette[etcolor]
#            else:
#                self.aw.qmc.backgroundmetcolor = etcolor
#
#        elif curve == 'bt':
#            if btcolor in defaults:
#                self.aw.qmc.backgroundbtcolor = self.aw.qmc.palette[btcolor]
#            else:
#                self.aw.qmc.backgroundbtcolor = btcolor
#
#        elif curve == 'deltaet':
#            if deltaetcolor in defaults:
#                self.aw.qmc.backgrounddeltaetcolor = self.aw.qmc.palette[deltaetcolor]
#            else:
#                self.aw.qmc.backgrounddeltaetcolor = deltaetcolor
#
#        elif curve == 'deltabt':
#            if deltabtcolor in defaults:
#                self.aw.qmc.backgrounddeltabtcolor = self.aw.qmc.palette[deltabtcolor]
#            else:
#                self.aw.qmc.backgrounddeltabtcolor = deltabtcolor
#
#        elif curve == 'xt':
#            if xtcolor in defaults:
#                self.aw.qmc.backgroundxtcolor = self.aw.qmc.palette[xtcolor]
#            else:
#                self.aw.qmc.backgroundxtcolor = xtcolor
#
#        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(bool)
    def delete(self, _:bool = False) -> None:
        self.pathedit.setText('')
# we should not overwrite the users app settings here, right:
# but we have to deactivate the show flag
        self.backgroundCheck.setChecked(False)
        self.aw.qmc.background = False
        self.aw.qmc.backgroundprofile = None
        self.xtcurveComboBox.blockSignals(True)
        self.xtcurveComboBox.clear()
        self.aw.deleteBackground()
        self.aw.qmc.resetlinecountcaches()
        self.xtcurveComboBox.blockSignals(False)
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(bool)
    def moveUp(self, _:bool = False) -> None:
        self.upButton.setDisabled(True)
        self.move_background('up')
        self.upButton.setDisabled(False)
    @pyqtSlot(bool)
    def moveDown(self,_:bool = False) -> None:
        self.downButton.setDisabled(True)
        self.move_background('down')
        self.downButton.setDisabled(False)
    @pyqtSlot(bool)
    def moveLeft(self,_:bool = False) -> None:
        self.leftButton.setDisabled(True)
        self.move_background('left')
        self.leftButton.setDisabled(False)
    @pyqtSlot(bool)
    def moveRight(self,_:bool = False) -> None:
        self.rightButton.setDisabled(True)
        self.move_background('right')
        self.rightButton.setDisabled(False)

    def move_background(self, m:str) -> None:
        step = self.speedSpinBox.value()
        self.aw.qmc.movebackground(m, step)
        self.aw.qmc.redraw(recomputeAllDeltas=False, re_smooth_foreground=False,
            re_smooth_background=False)

    def readChecks(self) -> None:
        self.aw.qmc.background = bool(self.backgroundCheck.isChecked())
        self.aw.qmc.backgroundDetails = bool(self.backgroundDetails.isChecked())
        self.aw.qmc.backgroundeventsflag = bool(self.backgroundeventsflag.isChecked())
        self.aw.qmc.DeltaETBflag = bool(self.backgroundDeltaETflag.isChecked())
        self.aw.qmc.DeltaBTBflag = bool(self.backgroundDeltaBTflag.isChecked())
        self.aw.qmc.backgroundETcurve = bool(self.backgroundETflag.isChecked())
        self.aw.qmc.backgroundBTcurve = bool(self.backgroundBTflag.isChecked())
        self.aw.qmc.backgroundShowFullflag = bool(self.backgroundFullflag.isChecked())
        self.aw.qmc.l_annotations_dict = {}
        self.aw.qmc.redraw_keep_view(recomputeAllDeltas=True)

    @pyqtSlot(int)
    def changeAlignEventidx(self, i:int) -> None:
        self.aw.qmc.alignEvent = i

    @pyqtSlot(int)
    def changeReplayTypeidx(self, i:int) -> None:
        self.aw.qmc.replayType = i

    @pyqtSlot(int)
    def changeReplayDropTypeidx(self, i:int) -> None:
        self.aw.qmc.replayDropType = i

    @pyqtSlot(int)
    def changeXTcurveidx(self, i:int) -> None:
        self.aw.qmc.xtcurveidx = i
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def changeYTcurveidx(self, i:int) -> None:
        self.aw.qmc.ytcurveidx = i
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(bool)
    def load(self, _:bool = False) -> None:
        self.filename = self.aw.ArtisanOpenFileDialog(msg=QApplication.translate('Message','Load Background'),ext='*.alog')
        if len(self.filename) == 0:
            return
        self.aw.sendmessage(QApplication.translate('Message','Reading background profile...'))
        self.aw.qmc.resetlinecountcaches()
        self.aw.loadbackground(self.filename)

        # reset XT curve popup
        curvenames = [''] # first entry is the empty one (no extra curve displayed)
        for i in range(min(len(self.aw.qmc.extraname1B),len(self.aw.qmc.extraname2B),len(self.aw.qmc.extratimexB))):
            curvenames.append('B' + str(2*i+3) + ': ' + self.aw.qmc.extraname1B[i])
            curvenames.append('B' + str(2*i+4) + ': ' + self.aw.qmc.extraname2B[i])

        self.xtcurveComboBox.blockSignals(True)
        self.xtcurveComboBox.clear()
        self.xtcurveComboBox.addItems(curvenames)
        if self.aw.qmc.xtcurveidx < len(curvenames):
            self.xtcurveComboBox.setCurrentIndex(self.aw.qmc.xtcurveidx)
        self.xtcurveComboBox.blockSignals(False)

        self.ytcurveComboBox.blockSignals(True)
        self.ytcurveComboBox.clear()
        self.ytcurveComboBox.addItems(curvenames)
        if self.aw.qmc.ytcurveidx < len(curvenames):
            self.ytcurveComboBox.setCurrentIndex(self.aw.qmc.ytcurveidx)
        self.ytcurveComboBox.blockSignals(False)

        self.pathedit.setText(self.filename)
        self.backgroundCheck.setChecked(True)
        self.aw.qmc.timealign(redraw=False)
        self.readChecks()

    def createEventTable(self) -> None:
        ndata = len(self.aw.qmc.backgroundEvents)

        # self.eventtable.clear() # this crashes Ubuntu 16.04
#        if ndata != 0:
#            self.eventtable.clearContents() # this crashes Ubuntu 16.04 if device table is empty and also sometimes else
        self.eventtable.clearSelection() # this seems to work also for Ubuntu 16.04

        self.eventtable.setRowCount(ndata)
        self.eventtable.setColumnCount(6)
        self.eventtable.setHorizontalHeaderLabels([QApplication.translate('Table','Time'),
                                                   self.ETname,
                                                   self.BTname,
                                                   QApplication.translate('Table','Description'),
                                                   QApplication.translate('Table','Type'),
                                                   QApplication.translate('Table','Value')])
        self.eventtable.setAlternatingRowColors(True)
        self.eventtable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.eventtable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.eventtable.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.eventtable.setShowGrid(True)
        vheader: Optional[QHeaderView] = self.eventtable.verticalHeader()
        if vheader is not None:
            vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        if self.aw.qmc.timeindex[0] != -1:
            start = self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            start = 0
        self.eventtable.setSortingEnabled(False)
        for i in range(ndata):
            #timez = QTableWidgetItem(stringfromseconds(self.aw.qmc.timeB[self.aw.qmc.backgroundEvents[i]]-start))
            tx = self.aw.qmc.timeB[self.aw.qmc.backgroundEvents[i]]-start
            timez = MyTableWidgetItemNumber(stringfromseconds(tx),tx)
            timez.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            fmtstr = '%.1f' if self.aw.qmc.LCDdecimalplaces else '%.0f'

            #etline = QTableWidgetItem(fmtstr%(self.aw.qmc.temp1B[self.aw.qmc.backgroundEvents[i]]) + self.aw.qmc.mode)
            et = self.aw.qmc.temp1B[self.aw.qmc.backgroundEvents[i]]
            etline = MyTableWidgetItemNumber(fmtstr%(et) + self.aw.qmc.mode,et)
            etline.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            #btline = QTableWidgetItem(fmtstr%(self.aw.qmc.temp2B[self.aw.qmc.backgroundEvents[i]]) + self.aw.qmc.mode)
            bt = self.aw.qmc.temp2B[self.aw.qmc.backgroundEvents[i]]
            btline = MyTableWidgetItemNumber(fmtstr%(bt) + self.aw.qmc.mode,bt)
            btline.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            description = QTableWidgetItem(self.aw.qmc.backgroundEStrings[i])
            etype = QTableWidgetItem(self.aw.qmc.Betypesf(self.aw.qmc.backgroundEtypes[i]))

            #evalue = QTableWidgetItem(self.aw.qmc.eventsvalues(self.aw.qmc.backgroundEvalues[i]))
            v = self.aw.qmc.eventsInternal2ExternalValue(self.aw.qmc.backgroundEvalues[i])
            evalue = MyTableWidgetItemNumber(str(v),v)
            evalue.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            #add widgets to the table
            self.eventtable.setItem(i,0,timez)
            self.eventtable.setItem(i,1,etline)
            self.eventtable.setItem(i,2,btline)
            self.eventtable.setItem(i,3,description)
            self.eventtable.setItem(i,4,etype)
            self.eventtable.setItem(i,5,evalue)
        header: Optional[QHeaderView] = self.eventtable.horizontalHeader()
        if header is not None:
            #header.setStretchLastSection(True)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        # set width of temp / time columns
        self.eventtable.setColumnWidth(0,60)
        self.eventtable.setColumnWidth(1,65)
        self.eventtable.setColumnWidth(2,65)
        self.eventtable.setColumnWidth(5,55)
        # sorting
        self.eventtable.setSortingEnabled(True)
        self.eventtable.sortItems(0)


    def createDataTable(self) -> None:
        try:
            #### lock shared resources #####
            self.aw.qmc.profileDataSemaphore.acquire(1)

            ndata = min(len(self.aw.qmc.timeB), len(self.aw.qmc.temp1B), len(self.aw.qmc.temp2B))

            self.datatable.clear() # this crashes Ubuntu 16.04
    #        if ndata != 0:
    #            self.datatable.clearContents() # this crashes Ubuntu 16.04 if device table is empty and also sometimes else
            self.datatable.clearSelection() # this seems to work also for Ubuntu 16.04

            if self.aw.qmc.timeindexB[0] != -1 and len(self.aw.qmc.timeB) > self.aw.qmc.timeindexB[0]:
                start = self.aw.qmc.timeB[self.aw.qmc.timeindexB[0]]
            else:
                start = 0
            self.datatable.setRowCount(ndata)
            headers = [QApplication.translate('Table','Time'),
                                                      self.ETname,
                                                      self.BTname,
                                                      deltaLabelUTF8 + self.ETname,
                                                      deltaLabelUTF8 + self.BTname]
            xtcurve = False # no XT curve
            n3:int = 0
            n4:int = 0
            if self.aw.qmc.xtcurveidx > 0: # 3rd background curve set?
                idx3 = self.aw.qmc.xtcurveidx - 1
                n3 = idx3 // 2
                if len(self.aw.qmc.temp1BX) > n3 and len(self.aw.qmc.extratimexB) > n3:
                    xtcurve = True
                    if self.aw.qmc.xtcurveidx % 2:
                        headers.append(self.aw.qmc.device_name_subst(self.aw.qmc.extraname1B[n3]))
                    else:
                        headers.append(self.aw.qmc.device_name_subst(self.aw.qmc.extraname2B[n3]))

            ytcurve = False # no YT curve
            if self.aw.qmc.ytcurveidx > 0: # 4th background curve set?
                idx4 = self.aw.qmc.ytcurveidx - 1
                n4 = idx4 // 2
                if len(self.aw.qmc.temp1BX) > n4 and len(self.aw.qmc.extratimexB) > n4:
                    ytcurve = True
                    if self.aw.qmc.ytcurveidx % 2:
                        headers.append(self.aw.qmc.device_name_subst(self.aw.qmc.extraname1B[n4]))
                    else:
                        headers.append(self.aw.qmc.device_name_subst(self.aw.qmc.extraname2B[n4]))

            self.datatable.setColumnCount(len(headers))
            self.datatable.setHorizontalHeaderLabels(headers)
            self.datatable.setAlternatingRowColors(True)
            self.datatable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.datatable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.datatable.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection) # QTableWidget.SelectionMode.SingleSelection, ContiguousSelection, MultiSelection
            self.datatable.setShowGrid(True)
            vheader: Optional[QHeaderView] = self.datatable.verticalHeader()
            if vheader is not None:
                vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            for i in range(ndata):
                Rtime = QTableWidgetItem(stringfromseconds(self.aw.qmc.timeB[i]-start))
                Rtime.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                fmtstr = '%.1f' if self.aw.qmc.LCDdecimalplaces else '%.0f'
                ET = QTableWidgetItem(fmtstr%self.aw.qmc.temp1B[i])
                BT = QTableWidgetItem(fmtstr%self.aw.qmc.temp2B[i])
                ET.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                BT.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                if i:
                    d = self.aw.qmc.timeB[i] - self.aw.qmc.timeB[i-1]
                    if d == 0:
                        dET = 0.
                        dBT = 0.
                    else:
                        dET = 60*(self.aw.qmc.temp1B[i] - self.aw.qmc.temp1B[i-1])/d
                        dBT = 60*(self.aw.qmc.temp2B[i] - self.aw.qmc.temp2B[i-1])/d
                    deltaET = QTableWidgetItem(f'{dET:.1f}')
                    deltaBT = QTableWidgetItem(f'{dBT:.1f}')
                else:
                    deltaET = QTableWidgetItem('--')
                    deltaBT = QTableWidgetItem('--')
                deltaET.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                deltaBT.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                self.datatable.setItem(i,0,Rtime)

                if i:
                    #identify by color and add notation
                    item0: Optional[QTableWidgetItem] = self.datatable.item(i,0)
                    if item0 is not None:
                        if i == self.aw.qmc.timeindexB[0] != -1:
                            item0.setBackground(QColor('#f07800'))
                            text = QApplication.translate('Table', 'CHARGE')
                        elif i == self.aw.qmc.timeindexB[1]:
                            item0.setBackground(QColor('orange'))
                            text = QApplication.translate('Table', 'DRY END')
                        elif i == self.aw.qmc.timeindexB[2]:
                            item0.setBackground(QColor('orange'))
                            text = QApplication.translate('Table', 'FC START')
                        elif i == self.aw.qmc.timeindexB[3]:
                            item0.setBackground(QColor('orange'))
                            text = QApplication.translate('Table', 'FC END')
                        elif i == self.aw.qmc.timeindexB[4]:
                            item0.setBackground(QColor('orange'))
                            text = QApplication.translate('Table', 'SC START')
                        elif i == self.aw.qmc.timeindexB[5]:
                            item0.setBackground(QColor('orange'))
                            text = QApplication.translate('Table', 'SC END')
                        elif i == self.aw.qmc.timeindexB[6]:
                            item0.setBackground(QColor('#f07800'))
                            text = QApplication.translate('Table', 'DROP')
                        elif i == self.aw.qmc.timeindexB[7]:
                            item0.setBackground(QColor('orange'))
                            text = QApplication.translate('Table', 'COOL')
                        elif i in self.aw.qmc.backgroundEvents:
                            item0.setBackground(QColor('yellow'))
                            index = self.aw.qmc.backgroundEvents.index(i)
                            text = QApplication.translate('Table', '#{0} {1}{2}').format(str(index+1),
                                self.aw.qmc.etypeAbbrev(self.aw.qmc.Betypesf(self.aw.qmc.backgroundEtypes[index])),
                                self.aw.qmc.eventsvalues(self.aw.qmc.backgroundEvalues[index]))
                        else:
                            text = ''
                    else:
                        text = ''
                    Rtime.setText(text + ' ' + Rtime.text())
                self.datatable.setItem(i,1,ET)
                self.datatable.setItem(i,2,BT)
                self.datatable.setItem(i,3,deltaET)
                self.datatable.setItem(i,4,deltaBT)

                if xtcurve and n3 is not None and len(self.aw.qmc.temp1BX[n3]) > i: # an XT column is available, fill it with data
                    if self.aw.qmc.xtcurveidx % 2:
                        XT = QTableWidgetItem(f'{self.aw.qmc.temp1BX[n3][i]:.0f}')
                    else:
                        XT = QTableWidgetItem(f'{self.aw.qmc.temp2BX[n3][i]:.0f}')
                    XT.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                    self.datatable.setItem(i,5,XT)

                if ytcurve and n4 is not None and len(self.aw.qmc.temp1BX[n4]) > i: # an YT column is available, fill it with data
                    if self.aw.qmc.ytcurveidx % 2:
                        YT = QTableWidgetItem(f'{self.aw.qmc.temp1BX[n4][i]:.0f}')
                    else:
                        YT = QTableWidgetItem(f'{self.aw.qmc.temp2BX[n4][i]:.0f}')
                    YT.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                    if xtcurve:
                        self.datatable.setItem(i,6,YT)
                    else:
                        self.datatable.setItem(i,5,YT)

            header: Optional[QHeaderView] = self.datatable.horizontalHeader()
            if header is not None:
                self.datatable.resizeColumnsToContents()
                for i in range(1, len(headers)):
                    header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                    header.resizeSection(i, max(header.sectionSize(i) + 5, 65))

        finally:
            if self.aw.qmc.profileDataSemaphore.available() < 1:
                self.aw.qmc.profileDataSemaphore.release(1)

    @pyqtSlot(bool)
    def copyDataTabletoClipboard(self, _:bool = False) -> None:
        self.datatable.selectAll()
        self.aw.copy_cells_to_clipboard(self.datatable,adjustment=7)
        self.datatable.clearSelection()
        self.aw.sendmessage(QApplication.translate('Message','Data table copied to clipboard'))

    @pyqtSlot(bool)
    def copyEventTabletoClipboard(self, _:bool = False) -> None:
        self.aw.copy_cells_to_clipboard(self.eventtable,adjustment=0)
        self.aw.sendmessage(QApplication.translate('Message','Event table copied to clipboard'))
