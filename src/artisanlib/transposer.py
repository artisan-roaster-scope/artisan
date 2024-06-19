#
# ABOUT
# Artisan Profile Transposer

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

import time as libtime
import warnings
import copy
import numpy
from typing import List, Tuple, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent # pylint: disable=unused-import
    import numpy.typing as npt  # pylint: disable=unused-import

from artisanlib.dialogs import ArtisanDialog
from artisanlib.util import stringfromseconds, stringtoseconds, float2float


try:
    from PyQt6.QtCore import Qt, pyqtSlot, QSettings, QRegularExpression, QDateTime # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QRegularExpressionValidator # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QHeaderView, QAbstractItemView, QWidget, QLabel, QLineEdit, QComboBox, QDialogButtonBox, # @UnusedImport @Reimport  @UnresolvedImport
                QTableWidget, QTableWidgetItem, QGroupBox, QLayout, QHBoxLayout, QVBoxLayout, QFrame) # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import Qt, pyqtSlot, QSettings, QRegularExpression, QDateTime # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QRegularExpressionValidator # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QHeaderView, QAbstractItemView, QWidget, QLabel, QLineEdit, QComboBox, QDialogButtonBox, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
                QTableWidget, QTableWidgetItem, QGroupBox, QLayout, QHBoxLayout, QVBoxLayout, QFrame) # @UnusedImport @Reimport  @UnresolvedImport


class MyQRegularExpressionValidator(QRegularExpressionValidator): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class
    # we fix partial time input like '12' => '12:00', '12:' => '12:00' and '12:0' => '12:00'

    @staticmethod
    def fixup(value:Optional[str]) -> str:
        if value is not None:
            if ':' not in value:
                return value + ':00'
            if value.endswith(':'):
                return value + '00'
            if len(value[value.index(':')+1:]) == 1:
                return value + '0'
            return value
        return ''

class profileTransformatorDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Profile Transposer'))

        self.helpdialog = None

        self.regexpercent = QRegularExpression(r'^$|[0-9]?[0-9]?(\.[0-9])?')
        self.regextime = QRegularExpression(r'^$|[0-9]?[0-9]:[0-5][0-9]')
        self.regextemp = QRegularExpression(r'^$|[0-9]?[0-9]?[0-9]?(\.[0-9])?')

        # original data
        self.org_transMappingMode = self.aw.qmc.transMappingMode
        self.org_timex = self.aw.qmc.timex[:]
        self.org_temp2 = self.aw.qmc.temp2[:]
        self.org_extratimex = copy.deepcopy(self.aw.qmc.extratimex)
        self.org_curFile = self.aw.curFile
        self.org_UUID = self.aw.qmc.roastUUID
        self.org_roastdate = self.aw.qmc.roastdate
        self.org_roastepoch = self.aw.qmc.roastepoch
        self.org_roasttzoffset = self.aw.qmc.roasttzoffset
        self.org_roastbatchnr = self.aw.qmc.roastbatchnr
        self.org_safesaveflag = self.aw.qmc.safesaveflag
        self.org_l_event_flags_dict = self.aw.qmc.l_event_flags_dict
        self.org_l_annotations_dict = self.aw.qmc.l_annotations_dict

        self.phasestable = QTableWidget()
        self.timetable = QTableWidget()
        self.temptable = QTableWidget()

        # time table widgets initialized by createTimeTable() to a list (target/result) with 4 widgets each
        #   DRY, FCs, SCs, DROP
        # if an event is not set in the profile, None is set instead of a widget
        #
        self.phases_target_widgets_time:Optional[List[Optional[QLineEdit]]] = None
        self.phases_target_widgets_percent:Optional[List[Optional[QLineEdit]]] = None
        self.phases_result_widgets:Optional[List[Optional[QTableWidgetItem]]] = None
        #
        self.time_target_widgets:Optional[List[Optional[QLineEdit]]] = None
        self.time_result_widgets:Optional[List[Optional[QTableWidgetItem]]] = None

        # profileTimes: list of DRY, FCs, SCs and DROP times in seconds if event is set, otherwise None
        self.profileTimes:List[Optional[float]] = self.getProfileTimes()
        # list of DRY, FCs, SCs, and DROP target times in seconds as specified by the user, or None if not set
        self.targetTimes:List[Optional[float]] = self.getTargetTimes()

        # temp table widgets initialized by createTempTable() to a list (target/result) with 5 widgets each
        #   CHARGE, DRY, FCs, SCs, DROP
        # if an event is not set in the profile, None is set instead of a widget
        self.temp_target_widgets:Optional[List[Optional[QLineEdit]]] = None
        self.temp_result_widgets:Optional[List[Optional[QTableWidgetItem]]] = None

        # list of CHARGE, DRY, FCs, SCs and DROP BT temperatures
        self.profileTemps = self.getProfileTemps()
        # list of DRY, FCs, SCs, and DROP target temperatures as specified by the user, or None if not set
        self.targetTemps = self.getTargetTemps()

        self.createPhasesTable()
        self.createTimeTable()
        self.createTempTable()

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.applyTransformations)
        self.dialogbuttons.rejected.connect(self.restoreState)
        self.applyButton = self.dialogbuttons.addButton(QDialogButtonBox.StandardButton.Apply)
        self.resetButton = self.dialogbuttons.addButton(QDialogButtonBox.StandardButton.Reset)
        self.helpButton = self.dialogbuttons.addButton(QDialogButtonBox.StandardButton.Help)
        if self.applyButton is not None:
            self.applyButton.clicked.connect(self.apply)
            self.setButtonTranslations(self.applyButton,'Apply',QApplication.translate('Button','Apply'))
        if self.resetButton is not None:
            self.resetButton.clicked.connect(self.restore)
            self.setButtonTranslations(self.resetButton,'Reset',QApplication.translate('Button','Reset'))
        if self.helpButton is not None:
            self.helpButton.clicked.connect(self.openHelp)
            self.setButtonTranslations(self.helpButton,'Help',QApplication.translate('Button','Help'))

        #buttons
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.dialogbuttons)

        mappingLabel = QLabel(QApplication.translate('Label','Mapping'))
        self.mappingModeComboBox = QComboBox()
        self.mappingModeComboBox.addItems([QApplication.translate('ComboBox','discrete'),
                                              QApplication.translate('ComboBox','linear'),
                                              QApplication.translate('ComboBox','quadratic')])
        self.mappingModeComboBox.setCurrentIndex(self.aw.qmc.transMappingMode)
        self.mappingModeComboBox.currentIndexChanged.connect(self.changeMappingMode)

        self.temp_formula:QLabel = QLabel()
        self.temp_formula.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        settingsHLayout = QHBoxLayout()
        settingsHLayout.addStretch()
        settingsHLayout.addWidget(mappingLabel)
        settingsHLayout.addWidget(self.mappingModeComboBox)
        settingsHLayout.addStretch()

        phasesHLayout = QHBoxLayout()
        phasesHLayout.addStretch()
        phasesHLayout.addWidget(self.phasestable)
        phasesHLayout.addStretch()
        phasesLayout = QVBoxLayout()
        phasesLayout.addLayout(phasesHLayout)

        timeHLayout = QHBoxLayout()
        timeHLayout.addStretch()
        timeHLayout.addWidget(self.timetable)
        timeHLayout.addStretch()
        timeLayout = QVBoxLayout()
        timeLayout.addLayout(timeHLayout)
        timeLayout.addStretch()

        tempHLayout = QHBoxLayout()
        tempHLayout.addWidget(self.temptable)
        tempHLayout.addStretch()
        formulaHLayout = QHBoxLayout()
        formulaHLayout.addStretch()
        formulaHLayout.addWidget(self.temp_formula)
        formulaHLayout.addStretch()
        tempLayout = QVBoxLayout()
        tempLayout.addLayout(tempHLayout)
        tempLayout.addLayout(formulaHLayout)
        tempLayout.addStretch()

        phasesGroupLayout = QGroupBox(QApplication.translate('Table','Phases'))
        phasesGroupLayout.setLayout(phasesLayout)
        timeGroupLayout = QGroupBox(QApplication.translate('Table','Time'))
        timeGroupLayout.setLayout(timeLayout)
        tempGroupLayout = QGroupBox(QApplication.translate('Table','BT'))
        tempGroupLayout.setLayout(tempLayout)

        #main
        mainlayout = QVBoxLayout()
        mainlayout.addLayout(settingsHLayout)
        mainlayout.addWidget(phasesGroupLayout)
        mainlayout.addWidget(timeGroupLayout)
        mainlayout.addWidget(tempGroupLayout)
        mainlayout.addStretch()
        mainlayout.addLayout(buttonsLayout)

        self.setLayout(mainlayout)
        ok_button = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setFocus()

        settings = QSettings()
        if settings.contains('TransformatorPosition'):
            self.move(settings.value('TransformatorPosition'))

        mainlayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)


    # utility functions

    def forgroundOffset(self) -> float:
        if self.aw.qmc.timeindex[0] == -1:
            return 0
        return self.org_timex[self.aw.qmc.timeindex[0]]

    def backgroundOffset(self) -> float:
        if self.aw.qmc.timeindexB[0] != -1 and len(self.aw.qmc.timeB) > self.aw.qmc.timeindexB[0]:
            return self.aw.qmc.timeB[self.aw.qmc.timeindexB[0]]
        return 0

    def clearPhasesTargetTimes(self) -> None:
        if self.phases_target_widgets_time is not None and len(self.phases_target_widgets_time)>2:
            for i in range(3):
                phases_target_widgets_time = self.phases_target_widgets_time[i]
                if phases_target_widgets_time is not None:
                    phases_target_widgets_time.setText('')

    def clearPhasesTargetPercent(self) -> None:
        if self.phases_target_widgets_percent is not None and len(self.phases_target_widgets_percent)>2:
            for i in range(3):
                phases_target_widgets_percent = self.phases_target_widgets_percent[i]
                if phases_target_widgets_percent is not None:
                    phases_target_widgets_percent.setText('')

    def clearPhasesResults(self) -> None:
        if self.phases_result_widgets is not None and len(self.phases_result_widgets)>2:
            for i in range(3):
                phases_result_widgets = self.phases_result_widgets[i]
                if phases_result_widgets is not None:
                    phases_result_widgets.setText('')

    def clearTimeTargets(self) -> None:
        if self.time_target_widgets is not None and len(self.time_target_widgets)>3:
            for i in range(4):
                time_target_widgets = self.time_target_widgets[i]
                if time_target_widgets is not None:
                    time_target_widgets.setText('')

    def clearTimeResults(self) -> None:
        if self.time_result_widgets is not None and len(self.time_result_widgets)>3:
            for i in range(4):
                time_result_widgets = self.time_result_widgets[i]
                if time_result_widgets is not None:
                    time_result_widgets.setText('')

    def clearTempTargets(self) -> None:
        if self.temp_target_widgets is not None and len(self.temp_target_widgets)>4:
            for i in range(5):
                temp_target_widget:Optional[QLineEdit] = self.temp_target_widgets[i]
                if temp_target_widget is not None:
                    temp_target_widget.setText('')

    def clearTempResults(self) -> None:
        if self.temp_result_widgets is not None and len(self.temp_result_widgets)>4:
            for i in range(5):
                temp_result_widget:Optional[QTableWidgetItem] = self.temp_result_widgets[i]
                if temp_result_widget is not None:
                    temp_result_widget.setText('')
        self.temp_formula.setText('')
        self.temp_formula.repaint()

    # returns list of DRY, FCs, SCs and DROP profile times in seconds if event is set, otherwise None
    def getProfileTimes(self) -> List[Optional[float]]:
        offset = self.forgroundOffset()
        res:List[Optional[float]] = []
        for i in [1,2,4,6]:
            idx = self.aw.qmc.timeindex[i]
            if idx == 0 or len(self.aw.qmc.timex) < idx:
                res.append(None)
            else:
                res.append(self.aw.qmc.timex[idx] - offset)
        return res

    # returns list of CHARGE, DRY, FCs, SCs and DROP BT temperatures if event is set, otherwise None
    def getProfileTemps(self) -> List[Optional[float]]:
        res:List[Optional[float]] = []
        for i in [0,1,2,4,6]:
            idx = self.aw.qmc.timeindex[i]
            if (i == 0 and idx == -1) or (i != 0 and idx == 0) or len(self.aw.qmc.timex) < idx:
                res.append(None)
            elif len(self.aw.qmc.temp2) > idx:
                res.append(self.aw.qmc.temp2[idx])
            else:
                res.append(None)
        return res

    # returns list of DRYING, MAILARD, FINISHING target phases times in seconds as first result and phases percentages (float) as second result
    # if a phase is set not set None is returned instead of a value
    def getTargetPhases(self) -> Tuple[List[Optional[int]], List[Optional[float]]]:
        res_times:List[Optional[int]] = []
        res_phases:List[Optional[float]] = []
        if self.phases_target_widgets_time is not None:
            for w in self.phases_target_widgets_time:
                ri:Optional[int] = None
                if w is not None:
                    txt = w.text()
                    if txt is not None and txt != '':
                        ri = stringtoseconds(txt)
                res_times.append(ri)
        if self.phases_target_widgets_percent is not None:
            for w in self.phases_target_widgets_percent:
                rf:Optional[float] = None
                if w is not None:
                    txt = w.text()
                    if txt is not None and txt != '':
                        rf = float(txt)
                res_phases.append(rf)
        return res_times, res_phases

    # returns list of DRY, FCs, SCs and DROP target times in seconds if event is set, otherwise None
    def getTargetTimes(self) -> List[Optional[float]]:
        res:List[Optional[float]] = []
        if self.time_target_widgets is not None:
            for w in self.time_target_widgets:
                r = None
                if w is not None:
                    txt = w.text()
                    if txt is not None and txt != '':
                        r = stringtoseconds(txt)
                res.append(r)
        return res

    # returns list of CHARGE, DRY, FCs, SCs and DROP BT temperatures if event is set, otherwise None
    def getTargetTemps(self) -> List[Optional[float]]:
        res = []
        if self.temp_target_widgets is not None:
            for w in self.temp_target_widgets:
                r = None
                if w is not None:
                    txt = w.text()
                    if txt is not None and txt != '':
                        r = float(txt)
                res.append(r)
        return res


    # message slots

    @pyqtSlot(int)
    def changeMappingMode(self, i:int) -> None:
        self.aw.qmc.transMappingMode = i
        self.updateTimeResults()
        self.updateTempResults()

    @pyqtSlot(int)
    def phasesTableColumnHeaderClicked(self, i:int) -> None:
        if (self.phases_target_widgets_time is not None and
                self.phases_target_widgets_time[i] is not None and
                self.phases_target_widgets_percent is not None and
                self.phases_target_widgets_percent[i] is not None):
            # clear target value i
            phases_target_widgets_time_i = self.phases_target_widgets_time[i]
            phases_target_widgets_percent_i = self.phases_target_widgets_percent[i]
            if (phases_target_widgets_time_i is not None and phases_target_widgets_time_i.text() != '') or (phases_target_widgets_percent_i is not None and phases_target_widgets_percent_i.text() != ''):
                if phases_target_widgets_time_i is not None:
                    phases_target_widgets_time_i.setText('')
                if phases_target_widgets_percent_i is not None:
                    phases_target_widgets_percent_i.setText('')
            elif self.aw.qmc.backgroundprofile is not None and self.aw.qmc.timeindexB[1]>0 and self.aw.qmc.timeindexB[2]>0 and self.aw.qmc.timeindexB[6]>0 and \
                    self.aw.qmc.timeindex[1]>0 and self.aw.qmc.timeindex[2]>0 and self.aw.qmc.timeindex[6]>0:
                back_offset = self.backgroundOffset()
                back_dry = self.aw.qmc.timeB[self.aw.qmc.timeindexB[1]]
                back_fcs = self.aw.qmc.timeB[self.aw.qmc.timeindexB[2]]
                back_drop = self.aw.qmc.timeB[self.aw.qmc.timeindexB[6]]
                s:str = ''
                if i == 0:
                    # DRYING
                    s = stringfromseconds(back_dry - back_offset)
                elif i == 1:
                    # MAILARD
                    s = stringfromseconds(back_fcs - back_dry)
                elif i == 2:
                    s = stringfromseconds(back_drop - back_fcs)
                qline_edit = (self.phases_target_widgets_time[i] if len(self.phases_target_widgets_time)>i else None)
                if qline_edit is not None:
                    qline_edit.setText(s)
            self.updateTimeResults()

    @pyqtSlot(int)
    def phasesTableRowHeaderClicked(self, i:int) -> None:
        if i == 1: # row targets
            # clear all targets and results
            # clear all targets
            self.clearPhasesTargetTimes()
            self.clearPhasesTargetPercent()
            self.clearPhasesResults()

    @pyqtSlot(int)
    def timeTableColumnHeaderClicked(self, i:int) -> None:
        if self.time_target_widgets is not None and self.time_target_widgets[i] is not None:
            # clear target value i
            time_target_widgets_i = self.time_target_widgets[i]
            if time_target_widgets_i is not None:
                if time_target_widgets_i.text() != '':
                    time_target_widgets_i.setText('')
                    self.updateTimeResults()
                elif self.aw.qmc.backgroundprofile is not None:
                    timeidx = [1,2,4,6][i]
                    if self.aw.qmc.timeindex[timeidx] and self.aw.qmc.timeindexB[timeidx]:
                        s = stringfromseconds(self.aw.qmc.timeB[self.aw.qmc.timeindexB[timeidx]]-self.backgroundOffset(),False)
                        time_target_widgets_i.setText(s)
                        self.updateTimeResults()

    @pyqtSlot(int)
    def timeTableRowHeaderClicked(self, i:int) -> None:
        if i == 1: # row targets
            self.clearTimeTargets()
            self.clearTimeResults()

    @pyqtSlot(int)
    def tempTableColumnHeaderClicked(self, i:int) -> None:
        if self.temp_target_widgets is not None and self.temp_target_widgets[i] is not None:
            # clear target value i
            temp_target_widgets_i = self.temp_target_widgets[i]
            if temp_target_widgets_i is not None:
                if temp_target_widgets_i.text() != '':
                    temp_target_widgets_i.setText('')
                    self.updateTempResults()
                elif self.aw.qmc.backgroundprofile is not None:
                    timeidx = [0,1,2,4,6][i]
                    if self.aw.qmc.timeindexB[timeidx] > 0:
                        temp_target_widgets_i.setText(str(float2float(self.aw.qmc.temp2B[self.aw.qmc.timeindexB[timeidx]])))
                        self.updateTempResults()

    @pyqtSlot(int)
    def tempTableRowHeaderClicked(self, i:int) -> None:
        if i == 1: # row targets
            self.clearTempTargets()
            self.clearTempResults()

    @pyqtSlot()
    def updatePhasesWidget(self) -> None:
        self.clearTimeTargets()
        if self.phases_target_widgets_time is not None and self.phases_target_widgets_percent is not None:
            sender = self.sender()
            assert isinstance(sender, QLineEdit)
            # clear corresponding time target if percentage target is set, or the otherway around
            if sender.text() != '':
                try:
                    time_idx = self.phases_target_widgets_time.index(sender)
                    phases_target_widgets_percent = self.phases_target_widgets_percent[time_idx]
                    if phases_target_widgets_percent is not None:
                        phases_target_widgets_percent.setText('')
                except Exception: # pylint: disable=broad-except
                    pass
                try:
                    percent_idx = self.phases_target_widgets_percent.index(sender)
                    phases_target_widgets_time = self.phases_target_widgets_time[percent_idx]
                    if phases_target_widgets_time is not None:
                        phases_target_widgets_time.setText('')
                except Exception: # pylint: disable=broad-except
                    pass
            self.updateTimeResults()

    @pyqtSlot()
    def updateTimesWidget(self) -> None:
        self.clearPhasesTargetTimes()
        self.clearPhasesTargetPercent()
        self.updateTimeResults()

    # updates time and phases result widgets
    def updateTimeResults(self) -> None:
        self.targetTimes = self.getTargetTimes()
        time_targets_clear = all(v is None for v in self.targetTimes)
        target_times, target_phases = self.getTargetPhases()
        phases_targets_clear = all(v is None for v in target_times + target_phases)
        self.clearPhasesResults()
        self.clearTimeResults()
        if not (phases_targets_clear and time_targets_clear):
            # phases targets are set, first clear the time targets
            if not phases_targets_clear:
                self.targetTimes = self.getTargetPhasesTimes()
            else:
                self.targetTimes = self.getTargetTimes()
            # set new time results
            result_times = self.calcTimeResults()
            if self.time_result_widgets is not None:
                for i in range(4):
                    time_result_widget = self.time_result_widgets[i]
                    if time_result_widget is not None:
                        if result_times[i] is None:
                            s = ''
                        else:
                            s = stringfromseconds(result_times[i],leadingzero=False)
                        time_result_widget.setText(s)
            # set new phases results
            if self.phases_result_widgets is not None:
                result_times = self.calcTimeResults()
                if all(result_times[r] is not None for r in [0,1,3]):
                    # DRYING
                    drying_period = result_times[0]
                    drying_percentage = 100 * drying_period / result_times[3]
                    drying_str = \
                            f'{stringfromseconds(drying_period,leadingzero=False)}    {float2float(drying_percentage)}%'
                    phases_result_widgets = self.phases_result_widgets[0]
                    if phases_result_widgets is not None:
                        phases_result_widgets.setText(drying_str)
                    # MAILARD
                    mailard_period = result_times[1] - result_times[0]
                    mailard_percentage = 100 * mailard_period / result_times[3]
                    mailard_str = \
                            f'{stringfromseconds(mailard_period,leadingzero=False)}    {float2float(mailard_percentage)}%'
                    phases_result_widgets= self.phases_result_widgets[1]
                    if phases_result_widgets is not None:
                        phases_result_widgets.setText(mailard_str)
                    # FINISHING
                    finishing_period = result_times[3] - result_times[1]
                    finishing_percentage = 100 * finishing_period / result_times[3]
                    finishing_str = \
                            f'{stringfromseconds(finishing_period,leadingzero=False)}    {float2float(finishing_percentage)}%'
                    phases_result_widgets = self.phases_result_widgets[2]
                    if phases_result_widgets is not None:
                        phases_result_widgets.setText(finishing_str)
                else:
                    for w in self.phases_result_widgets:
                        if w is not None:
                            w.setText('')

    @pyqtSlot()
    def updateTempResults(self) -> None:
        self.targetTemps = self.getTargetTemps()
        if all(v is None for v in self.targetTemps):
            # clear all results if no targets are set
            self.clearTempResults()
        # set new results
        elif self.temp_result_widgets is not None and len(self.temp_result_widgets)>4:
            result_temps,fit = self.calcTempResults()
            for i in range(5):
                temp_result_widget:Optional[QTableWidgetItem] = self.temp_result_widgets[i]
                result_temp = result_temps[i]
                if temp_result_widget is not None and result_temp is not None:
                    temp_result_widget.setText(str(float2float(result_temp)) + self.aw.qmc.mode)
            s = ''
            if fit is not None:
                s = fit
            self.temp_formula.setText(s)
            self.temp_formula.repaint()

    #called from Apply button
    @pyqtSlot(bool)
    def apply(self,_:bool = False) -> None:
        applied_time = self.applyTimeTransformation()
        applied_temp = self.applyTempTransformation()
        if applied_time or applied_temp:
            self.aw.qmc.roastUUID = None
            self.aw.qmc.roastdate = QDateTime.currentDateTime()
            self.aw.qmc.roastepoch = self.aw.qmc.roastdate.toSecsSinceEpoch()
            self.aw.qmc.roasttzoffset = libtime.timezone
            self.aw.qmc.roastbatchnr = 0
            self.aw.setCurrentFile(None,addToRecent=False)
            self.aw.qmc.l_event_flags_dict = {}
            self.aw.qmc.l_annotations_dict = {}
            self.aw.qmc.fileDirty()
            self.aw.qmc.timealign()
            self.aw.autoAdjustAxis()
            self.aw.qmc.redraw()
        else:
            self.restore()

    #called from Restore button
    @pyqtSlot(bool)
    def restore(self, _:bool = False) -> None:
        self.aw.setCurrentFile(self.org_curFile,addToRecent=False)
        self.aw.qmc.roastUUID = self.org_UUID
        self.aw.qmc.roastdate = self.org_roastdate
        self.aw.qmc.roastepoch = self.org_roastepoch
        self.aw.qmc.roasttzoffset = self.org_roasttzoffset
        self.aw.qmc.roastbatchnr = self.org_roastbatchnr
        if self.org_safesaveflag:
            self.aw.qmc.fileDirty()
        else:
            self.aw.qmc.fileClean()
        self.aw.qmc.l_event_flags_dict = self.org_l_event_flags_dict
        self.aw.qmc.l_annotations_dict = self.org_l_annotations_dict
        self.aw.qmc.timex = self.org_timex[:]
        self.aw.qmc.extratimex = copy.deepcopy(self.org_extratimex)
        self.aw.qmc.temp2 = self.org_temp2[:]
        self.aw.autoAdjustAxis()
        self.aw.qmc.redraw()

    #called from OK button
    @pyqtSlot()
    def applyTransformations(self) -> None:
        self.apply()
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue('TransformatorPosition',self.frameGeometry().topLeft())
        self.accept()

    #called from Cancel button
    @pyqtSlot()
    def restoreState(self) -> None:
        self.restore()
        self.aw.qmc.transMappingMode = self.org_transMappingMode
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue('TransformatorPosition',self.geometry().topLeft())
        self.closeHelp()
        self.reject()

    @pyqtSlot(bool)
    def openHelp(self,_:bool = False) -> None:
        from help import transposer_help # pyright: ignore [attr-defined] # pylint: disable=no-name-in-module
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate('Form Caption','Profile Transposer Help'),
                transposer_help.content())

    def closeHelp(self) -> None:
        self.aw.closeHelpDialog(self.helpdialog)

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        self.restoreState()


    # Calculations

    # returns the list of results times in seconds
    def calcTimeResults(self) -> List[float]:
        res = []
        profileTime:Optional[float]
        if self.aw.qmc.transMappingMode == 0:
            # discrete mapping
            # adding CHARGE
            fits:List[Optional[npt.NDArray[numpy.float64]]] = self.calcDiscretefits([0] + self.profileTimes,[0] + self.targetTimes)
            if len(fits)>4 and len(self.profileTimes)>3:
                for i in range(4):
                    fit:Optional[npt.NDArray[numpy.float64]] = fits[i+1]
                    profileTime = self.profileTimes[i]
                    if fit is not None and profileTime is not None:
                        res.append(numpy.poly1d(fit)(profileTime))
                    else:
                        res.append(None)
        else:
            with warnings.catch_warnings():
                warnings.filterwarnings('error')
                try:
                    fit_fuc = self.calcTimePolyfit() # note that this fit is already applied to numpy.polyfit !!
                    for i in range(4):
                        profileTime = self.profileTimes[i]
                        if fit_fuc is not None and profileTime is not None:
                            res.append(fit_fuc(profileTime))
                        else:
                            res.append(None)
                except numpy.exceptions.RankWarning:
                    pass
                except Exception: # pylint: disable=broad-except
                    pass
        return res

    # returns the list of results temperatures and the polyfit or None as second result
    def calcTempResults(self) -> Tuple[List[Optional[float]], Optional[str]]:
        res:List[Optional[float]] = []
        fit:Optional[npt.NDArray[numpy.float64]] = None
        fit_str:Optional[str] = None
        profileTemp:Optional[float]
        if self.aw.qmc.transMappingMode == 0:
            # discrete mapping
            fits = self.calcDiscretefits(self.profileTemps,self.targetTemps)
            for i in range(5):
                fit = fits[i]
                profileTemp = self.profileTemps[i]
                if profileTemp is not None and fit is not None:
                    res.append(numpy.poly1d(fit)(profileTemp))
                else:
                    res.append(None)
            active_fits = list(filter(lambda x: x[1][1] is not None,zip(fits,zip(self.profileTemps,self.targetTemps))))
            if len(active_fits) > 0 and len(active_fits) < 3:
                fit_str = self.aw.fit2str(fits[0])
            else:
                formula = ''
                last_target:Optional[float] = None
                for f,tpl in reversed(active_fits[:-1]):
                    if last_target is None:
                        formula = self.aw.fit2str(f)
                    else:
                        formula = f'({self.aw.fit2str(f)} if x<{last_target} else {formula})'
                    last_target = tpl[1]
                fit_str = formula
        else:
            with warnings.catch_warnings():
                warnings.filterwarnings('error')
                try:
                    fit_func = self.calcTempPolyfit() # numpy.poly1d not yet applied to this fit
                    if fit_func is not None:
                        p = numpy.poly1d(fit_func)
                        for i in range(5):
                            profileTemp = self.profileTemps[i]
                            if profileTemp is not None:
                                res.append(p(profileTemp))
                            else:
                                res.append(None)
                        fit_str = self.aw.fit2str(fit_func)
                    else:
                        res = [None]*5
                except numpy.exceptions.RankWarning:
                    pass
                except Exception: # pylint: disable=broad-except
                    pass
        return res,fit_str

    # returns target times based on the phases target
    def getTargetPhasesTimes(self) -> List[Optional[float]]:
        # get the offset
        offset:float = self.forgroundOffset()
        # get profile phases events time
        dry:float = self.aw.qmc.timex[self.aw.qmc.timeindex[1]] - offset
        fcs:float = self.aw.qmc.timex[self.aw.qmc.timeindex[2]] - offset
        drop:float = self.aw.qmc.timex[self.aw.qmc.timeindex[6]] - offset
        # flags for targets set
        dry_set:bool = False
        drop_set:bool = False
        fcs_set:bool = False

        if self.phases_target_widgets_time is None or self.phases_target_widgets_percent is None:
            return []

        # first determine the target DROP time (relative to the profile drop) if any
        drop_phases_target_widget_time = self.phases_target_widgets_time[2]
        drop_phases_target_widget_percent = self.phases_target_widgets_percent[2]
        if drop_phases_target_widget_time is not None and drop_phases_target_widget_time.text() != '':
            drop = fcs + stringtoseconds(drop_phases_target_widget_time.text())
            drop_set = True
        elif drop_phases_target_widget_percent is not None and drop_phases_target_widget_percent.text() != '':
            drop = fcs + (float(drop_phases_target_widget_percent.text()) * drop / 100)
            drop_set = True

        # determine the target DRY time (relative to the target drop of above) if any
        dry_phases_target_widgets_time = self.phases_target_widgets_time[0]
        dry_phases_target_widgets_percent = self.phases_target_widgets_percent[0]
        if dry_phases_target_widgets_time is not None and dry_phases_target_widgets_time.text() != '':
            dry = stringtoseconds(dry_phases_target_widgets_time.text())
            dry_set = True
        elif dry_phases_target_widgets_percent is not None and dry_phases_target_widgets_percent.text() != '':
            dry = float(dry_phases_target_widgets_percent.text()) * drop / 100
            dry_set = True

        # determine the target FCs time (relative to the target drop of above) if any
        fcs_phases_target_widgets_time = self.phases_target_widgets_time[1]
        fcs_phases_target_widgets_percent = self.phases_target_widgets_percent[1]
        if fcs_phases_target_widgets_time is not None and fcs_phases_target_widgets_time.text() != '':
            fcs = dry + stringtoseconds(fcs_phases_target_widgets_time.text())
            fcs_set = True
        elif fcs_phases_target_widgets_percent is not None and fcs_phases_target_widgets_percent.text() != '':
            fcs = dry + (float(fcs_phases_target_widgets_percent.text()) * drop / 100)
            fcs_set = True

#        return [(dry if dry_set else None),(fcs if fcs_set else None), None, (drop if drop_set else None)]
        # set all unset target times to the profile times
        return [
            (dry if dry_set else (self.aw.qmc.timex[self.aw.qmc.timeindex[1]] - offset)),
            (fcs if fcs_set else (self.aw.qmc.timex[self.aw.qmc.timeindex[2]] - offset)),
            None,
            (drop if drop_set else (self.aw.qmc.timex[self.aw.qmc.timeindex[6]] - offset))]

    # calculates the linear (self.aw.qmc.transMappingMode = 1) or quadratic (self.aw.qmc.transMappingMode = 2) mapping
    # between the profileTimes and the targetTimes
    def calcTimePolyfit(self) -> Optional[Callable[[float], float]]:
        # initialized by CHARGE time 00:00
        xa:List[float] = [0]
        ya:List[float] = [0]
        for i in range(4):
            profileTime:Optional[float] = self.profileTimes[i]
            targetTime:Optional[float] = self.targetTimes[i]
            if profileTime is not None and targetTime is not None:
                xa.append(profileTime)
                ya.append(targetTime)
        deg = self.aw.qmc.transMappingMode
        if len(xa) > 1:
            try:
                deg = min(len(xa) - 1,deg)
                z = numpy.polyfit(xa, ya, deg)
                return numpy.poly1d(z)
            except Exception: # pylint: disable=broad-except
                return None
        else:
            return None

    # calculates the linear (self.aw.qmc.transMappingMode = 1) or quadratic (self.aw.qmc.transMappingMode = 2) mapping
    # between the profileTemps and the targetTemps
    def calcTempPolyfit(self) -> Optional['npt.NDArray[numpy.float64]']:
        xa:List[float] = []
        ya:List[float] = []
        for i in range(5):
            profileTemp:Optional[float] = self.profileTemps[i]
            targetTemp:Optional[float] = self.targetTemps[i]
            if profileTemp is not None and targetTemp is not None:
                xa.append(profileTemp)
                ya.append(targetTemp)
        deg = self.aw.qmc.transMappingMode
        if len(xa) > 0:
            try:
                deg = min(len(xa) - 1,deg)
                if deg == 0:
                    z = numpy.array([1, ya[0] - xa[0]])
                else:
                    z = numpy.polyfit(xa, ya, deg)
                return z
            except Exception: # pylint: disable=broad-except
                return None
        else:
            return None

    # returns a list of segment-wise fits between sources and targets
    # each fit is a numpy.array as returned by numpy.polyfit
    # a source element of None generates None as fit
    # a target element of None is skipped and previous and next segments are joined
    # the lists of sources and targets are expected to be of the same length
    # the length of the result list is the same as that of the sources and targets
    @staticmethod
    def calcDiscretefits(sources:List[Optional[float]], targets:List[Optional[float]]) -> List[Optional['npt.NDArray[numpy.float64]']]:
        if len(sources) != len(targets):
            return [None]*len(sources)
        fits:List[Optional[npt.NDArray[numpy.float64]]] = [None]*len(sources)
        last_fit:Optional[npt.NDArray[numpy.float64]] = None
        for i, _ in enumerate(sources):
            if sources[i] is not None:
                if targets[i] is None:
                    # we take the last fit
                    fits[i] = last_fit
                else:
                    next_idx = None # the index of the next non-empty source/target pair
                    for j in range(i+1,len(sources)):
                        if sources[j] is not None and targets[j] is not None:
                            next_idx = j
                            break
                    sources_i:Optional[float] = None
                    targets_i:Optional[float] = None
                    sources_i = sources[i]
                    targets_i = targets[i]
                    if next_idx is None:
                        if last_fit is not None:
                            fits[i] = last_fit # copy previous fit
                        elif sources_i is not None and targets_i is not None:
                            # set a simple offset only as there is no previous nor next fit
                            fits[i] = numpy.array([1,targets_i - sources_i])
                        else:
                            fits[i] = numpy.array([1,0])
                    else:
                        sources_next = sources[next_idx]
                        targets_next = targets[next_idx]
                        if sources_i is None or targets_i is None or sources_next is None or targets_next is None:
                            fits[i] = numpy.array([1,0])
                        else:
                            fits[i] = numpy.polyfit([sources_i, sources_next], [targets_i, targets_next] ,1)
                    # if this is the first fit, we copy it to all previous positions
                    if last_fit is None:
                        for k in range(i):
                            if sources[k] is not None:
                                fits[k] = fits[i]
                    # register this fit
                    last_fit = fits[i]
        return fits

    # fits of length 5
    def applyDiscreteTimeMapping(self, timex:List[float], fits:List[Optional['npt.NDArray[numpy.float64]']]) -> List[float]:
        offset = self.forgroundOffset()
        res_timex = []
        if offset == 0 or fits[0] is None:
            new_offset = 0
        else:
            new_offset = numpy.poly1d(fits[0])(offset)
        for i, _ in enumerate(timex):
            # first fit is to be applied for all readings before DRY
            j = 0
            if self.aw.qmc.timeindex[6] > 0 and i >= self.aw.qmc.timeindex[6]:
                # last fit counts after DROP
                j = 4
            elif self.aw.qmc.timeindex[4] > 0 and i >= self.aw.qmc.timeindex[4]:
                j = 3 # after SCs
            elif self.aw.qmc.timeindex[2] > 0 and i >= self.aw.qmc.timeindex[2]:
                j = 2 # after FCs
            elif self.aw.qmc.timeindex[1] > 0 and i >= self.aw.qmc.timeindex[1]:
                j = 1 # after DRY
            fitsj = fits[j]
            if fitsj is None:
                res_timex.append(timex[i] - offset + new_offset)
            else:
                fit = numpy.poly1d(fitsj) # fit to be applied
                res_timex.append(fit(timex[i] - offset)+new_offset)
        return res_timex

    # returns False if no transformation was applied
    def applyTimeTransformation(self) -> bool:
        # first update the targets
        self.targetTimes = self.getTargetTimes()
        if all(v is None for v in self.targetTimes):
            target_times, target_phases = self.getTargetPhases()
            if all(v is None for v in target_times + target_phases):
                self.aw.qmc.timex = self.org_timex[:]
                self.aw.qmc.extratimex = copy.deepcopy(self.org_extratimex)
                return False
            self.targetTimes = self.getTargetPhasesTimes()
        # calculate the offset of 00:00
        offset = self.forgroundOffset()
        # apply either the discrete or the polyfit mappings
        if self.aw.qmc.transMappingMode == 0:
            # discrete mapping
            base:List[Optional[float]] = [0]
            base.extend(self.targetTimes)
            fits = self.calcDiscretefits([0] + self.profileTimes, base)
            self.aw.qmc.timex = self.applyDiscreteTimeMapping(self.org_timex,fits)
            # apply to the extra timex
            self.aw.qmc.extratimex = []
            for timex in self.org_extratimex:
                try:
                    timex_trans = self.applyDiscreteTimeMapping(timex,fits)
                except Exception: # pylint: disable=broad-except
                    timex_trans = timex
                self.aw.qmc.extratimex.append(timex_trans)
        else:
            # polyfit mappings
            with warnings.catch_warnings():
                warnings.filterwarnings('error')
                try:
                    fit = self.calcTimePolyfit() # the fit returned here is already applied to numpy.poly1d
                    if fit is not None:
                        self.aw.qmc.timex = [fit(tx-offset) for tx in self.org_timex]
                        if len(self.aw.qmc.timex) > 0 and self.aw.qmc.timeindex[0] != -1:
                            foffset = self.aw.qmc.timex[0]
                            self.aw.qmc.timex = [tx+foffset for tx in self.aw.qmc.timex]
                        extratimex = []
                        for timex in self.org_extratimex:
                            offset = 0
                            if len(timex) > 0 and self.aw.qmc.timeindex[0] != -1:
                                offset = timex[self.aw.qmc.timeindex[0]]
                            new_timex = [fit(tx-offset) for tx in timex]
                            if len(new_timex) > 0 and self.aw.qmc.timeindex[0] != -1:
                                foffset = new_timex[0]
                                new_timex = [tx+foffset for tx in new_timex]
                            extratimex.append(new_timex)
                        self.aw.qmc.extratimex = extratimex
                except numpy.exceptions.RankWarning:
                    pass
        return True

    # returns False if no transformation was applied
    def applyTempTransformation(self) -> bool:
        # first update the targets
        self.targetTemps = self.getTargetTemps()
        if all(v is None for v in self.targetTemps):
            self.aw.qmc.temp2 = self.org_temp2[:]
            return False
        # apply either the discrete or the polyfit mappings
        if self.aw.qmc.transMappingMode == 0:
            # discrete mappings, length 5
            fits = self.calcDiscretefits(self.profileTemps,self.targetTemps)
            self.aw.qmc.temp2 = []
            for i, _ in enumerate(self.org_temp2):
                # first fit is to be applied for all readings before DRY
                j = 0
                if self.aw.qmc.timeindex[6] > 0 and i >= self.aw.qmc.timeindex[6]:
                    # last fit counts after DROP
                    j = 4
                elif self.aw.qmc.timeindex[4] > 0 and i >= self.aw.qmc.timeindex[4]:
                    j = 3 # after SCs
                elif self.aw.qmc.timeindex[2] > 0 and i >= self.aw.qmc.timeindex[2]:
                    j = 2 # after FCs
                elif self.aw.qmc.timeindex[1] > 0 and i >= self.aw.qmc.timeindex[1]:
                    j = 1 # after DRY

                tp = self.org_temp2[i]
                fitj = fits[j]
                if tp is None or tp == -1 or fitj is None:
                    self.aw.qmc.temp2.append(tp)
                else:
                    fit = numpy.poly1d(fitj) # fit to be applied
                    self.aw.qmc.temp2.append(fit(tp))
            return True
        # polyfit mappings
        with warnings.catch_warnings():
            warnings.filterwarnings('error')
            try:
                p = self.calcTempPolyfit()
                if p is not None:
                    fit = numpy.poly1d(p)
                    if fit is not None:
                        self.aw.qmc.temp2 = [(-1 if (temp is None) or (temp == -1) else fit(temp)) for temp in self.org_temp2]
            except numpy.exceptions.RankWarning:
                pass
        return True

    # tables

    def createPhasesTable(self) -> None:
        vheader = self.phasestable.verticalHeader()
        hheader = self.phasestable.horizontalHeader()

        self.phasestable.setRowCount(3)
        self.phasestable.setColumnCount(3)
        if hheader is not None:
            hheader.setStretchLastSection(False)
            hheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            hheader.setHighlightSections(False)
        if vheader is not None:
            vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        self.phasestable.setHorizontalHeaderLabels([QApplication.translate('Label','Drying'),
                                                         QApplication.translate('Label','Maillard'),
                                                         QApplication.translate('Label','Finishing')])
        self.phasestable.setVerticalHeaderLabels([QApplication.translate('Table','Profile'),
                                                         QApplication.translate('Table','Target'),
                                                         QApplication.translate('Table','Result')])
        self.phasestable.setShowGrid(True)
        self.phasestable.setAlternatingRowColors(True)
        self.phasestable.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.phasestable.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        if hheader is not None and vheader is not None:
            self.phasestable.setFixedSize(
                hheader.length() +
                    vheader.sizeHint().width(),
                vheader.length() +
                    hheader.height())
        self.phasestable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.phasestable.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.phasestable.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.phasestable.setAutoScroll(False)
        if vheader is not None:
            vheader.sectionClicked.connect(self.phasesTableRowHeaderClicked)
        if hheader is not None:
            hheader.sectionClicked.connect(self.phasesTableColumnHeaderClicked)

        self.phases_target_widgets_time = []
        self.phases_target_widgets_percent = []
        self.phases_result_widgets = []

        profilePhasesTimes:List[Optional[float]] = [None]*3 # DRYING, MAILARD, FINISHING
        profilePhasesPercentages:List[Optional[float]] = [None] * 3
        #
        # the phases transformation are only enabled if at least DRY, FCs and DROP events are set
        phases_enabled = self.aw.qmc.timeindex[1] and self.aw.qmc.timeindex[2] and self.aw.qmc.timeindex[6]
        #
        if phases_enabled:
            profilePhasesTimes[0] = self.profileTimes[0] # DRYING == DRY
            if self.profileTimes[0] is not None and self.profileTimes[1] is not None:
                profilePhasesTimes[1] = self.profileTimes[1] - self.profileTimes[0]
            if self.profileTimes[1] is not None and self.profileTimes[3] is not None:
                profilePhasesTimes[2] = self.profileTimes[3] - self.profileTimes[1]
            if self.profileTimes[3] is not None:
                profilePhasesPercentages = [(ppt/self.profileTimes[3])*100 for ppt in profilePhasesTimes if ppt is not None]

        for i in range(3):
            profilePhasesTime = profilePhasesTimes[i]
            profilePhasesPercentage = profilePhasesPercentages[i]
            if len(profilePhasesTimes) > i and profilePhasesTime is not None and profilePhasesPercentage is not None:
                profile_phases_time_str = \
                    f'{stringfromseconds(int(round(profilePhasesTime)),leadingzero=False)}    {float2float(profilePhasesPercentage)}%'
                profile_phases_widget = QTableWidgetItem(profile_phases_time_str)
                profile_phases_widget.setTextAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
                self.phasestable.setItem(0,i,profile_phases_widget)
                #
                target_widget_time = QLineEdit('')
                target_widget_time.setValidator(MyQRegularExpressionValidator(self.regextime))
                target_widget_time.setAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
                if phases_enabled:
                    target_widget_time.editingFinished.connect(self.updatePhasesWidget)
                else:
                    target_widget_time.setEnabled(False)
                target_widget_percent = QLineEdit('')
                target_widget_percent.setValidator(QRegularExpressionValidator(self.regexpercent))
                target_widget_percent.setAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
                if phases_enabled:
                    target_widget_percent.editingFinished.connect(self.updatePhasesWidget)
                else:
                    target_widget_percent.setEnabled(False)
                target_cell_widget = QWidget()
                target_cell_layout = QHBoxLayout(target_cell_widget)
                target_cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
                target_cell_layout.setContentsMargins(4,4,4,4)
                target_cell_layout.addWidget(target_widget_time)
                target_cell_layout.addWidget(target_widget_percent)
                target_cell_widget.setLayout(target_cell_layout)
                self.phasestable.setCellWidget(1,i,target_cell_widget)
                #
                result_widget = QTableWidgetItem('')
                result_widget.setTextAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
                self.phasestable.setItem(2,i,result_widget)
            else:
                target_widget_time = None
                target_widget_percent = None
                result_widget = None
            self.phases_target_widgets_time.append(target_widget_time)
            self.phases_target_widgets_percent.append(target_widget_percent)
            self.phases_result_widgets.append(result_widget)

    def createTimeTable(self) -> None:
        hheader = self.timetable.horizontalHeader()
        vheader = self.timetable.verticalHeader()
        self.timetable.clear()
        self.timetable.setRowCount(3)
        self.timetable.setColumnCount(4)
        if hheader is not None:
            hheader.setStretchLastSection(False)
            hheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            hheader.setHighlightSections(False)
        if vheader is not None:
            vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.timetable.setHorizontalHeaderLabels([QApplication.translate('Label','DRY END'),
                                                         QApplication.translate('Label','FC START'),
                                                         QApplication.translate('Label','SC START'),
                                                         QApplication.translate('Label','DROP')])
        self.timetable.setVerticalHeaderLabels([QApplication.translate('Table','Profile'),
                                                         QApplication.translate('Table','Target'),
                                                         QApplication.translate('Table','Result')])
        self.timetable.setShowGrid(True)
        self.timetable.setAlternatingRowColors(False)
        self.timetable.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.timetable.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.timetable.setFrameStyle(QFrame.Shape.NoFrame)
        if hheader is not None and vheader is not None:
            self.timetable.setFixedSize(
                hheader.length() +
                    vheader.sizeHint().width(),
                vheader.length() +
                    hheader.height())
        self.timetable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.timetable.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.timetable.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.timetable.setAutoScroll(False)
        if vheader is not None:
            vheader.sectionClicked.connect(self.timeTableRowHeaderClicked)
        if hheader is not None:
            hheader.sectionClicked.connect(self.timeTableColumnHeaderClicked)

        self.time_target_widgets = []
        self.time_result_widgets = []

        for i in range(4):
            profileTime = self.profileTimes[i]
            if len(self.profileTimes) > i and profileTime is not None:
                profile_time_str = stringfromseconds(int(round(profileTime)),leadingzero=False)
                profile_widget = QTableWidgetItem(profile_time_str)
                profile_widget.setTextAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
                self.timetable.setItem(0,i,profile_widget)
                #
                target_widget = QLineEdit('')
                target_widget.setValidator(MyQRegularExpressionValidator(self.regextime))
                target_widget.setAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
                target_widget.editingFinished.connect(self.updateTimesWidget)
                target_cell_widget = QWidget()
                target_cell_layout = QHBoxLayout(target_cell_widget)
                target_cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
                target_cell_layout.setContentsMargins(4,4,4,4)
                target_cell_layout.addWidget(target_widget)
                target_cell_widget.setLayout(target_cell_layout)
                self.timetable.setCellWidget(1,i,target_cell_widget)
                #
                result_widget = QTableWidgetItem('') #profile_time_str)
                result_widget.setTextAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
                self.timetable.setItem(2,i,result_widget)
            else:
                target_widget = None
                result_widget = None
            self.time_target_widgets.append(target_widget)
            self.time_result_widgets.append(result_widget)

    def createTempTable(self) -> None:
        vheader = self.temptable.verticalHeader()
        hheader = self.temptable.horizontalHeader()
        self.temptable.clear()
        self.temptable.setRowCount(3)
        self.temptable.setColumnCount(5)
        if hheader is not None:
            hheader.setStretchLastSection(False)
            hheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        if vheader is not None:
            vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.temptable.setHorizontalHeaderLabels([QApplication.translate('Label','CHARGE'),
                                                         QApplication.translate('Label','DRY END'),
                                                         QApplication.translate('Label','FC START'),
                                                         QApplication.translate('Label','SC START'),
                                                         QApplication.translate('Label','DROP')])
        self.temptable.setVerticalHeaderLabels([QApplication.translate('Table','Profile'),
                                                         QApplication.translate('Table','Target'),
                                                         QApplication.translate('Table','Result')])
        self.temptable.setShowGrid(True)
        self.temptable.setAlternatingRowColors(False)
        self.temptable.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.temptable.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        hheader = self.temptable.horizontalHeader()
        vheader = self.temptable.verticalHeader()
        if hheader is not None and vheader is not None:
            self.temptable.setFixedSize(
                hheader.length() +
                    vheader.sizeHint().width(),
                vheader.length() +
                    hheader.height())
        self.temptable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.temptable.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.temptable.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.temptable.setAutoScroll(False)
        if vheader is not None:
            vheader.sectionClicked.connect(self.tempTableRowHeaderClicked)
        if hheader is not None:
            hheader.sectionClicked.connect(self.tempTableColumnHeaderClicked)

        self.temp_target_widgets = []
        self.temp_result_widgets = []

        for i in range(5):
            profileTemp = self.profileTemps[i]
            if len(self.profileTemps) > i and profileTemp is not None:
                profile_temp_str = str(float2float(profileTemp)) + self.aw.qmc.mode
                profile_widget = QTableWidgetItem(profile_temp_str)
                profile_widget.setTextAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
                self.temptable.setItem(0,i,profile_widget)
                #
                target_widget = QLineEdit('')
                target_widget.setValidator(QRegularExpressionValidator(self.regextemp))
                target_widget.editingFinished.connect(self.updateTempResults)
                target_widget.setAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)

                target_cell_widget = QWidget()
                target_cell_layout = QHBoxLayout(target_cell_widget)
                target_cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
                target_cell_layout.setContentsMargins(4,4,4,4)
                target_cell_layout.addWidget(target_widget)
#                target_cell_layout.addWidget(QLabel(self.aw.qmc.mode))
                target_cell_widget.setLayout(target_cell_layout)
                self.temptable.setCellWidget(1,i,target_cell_widget)
                #
                result_widget = QTableWidgetItem('')
                result_widget.setTextAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
                self.temptable.setItem(2,i,result_widget)
            else:
                target_widget = None
                result_widget = None
            self.temp_target_widgets.append(target_widget)
            self.temp_result_widgets.append(result_widget)
