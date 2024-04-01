#
# ABOUT
# Artisan Large LCDs

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

import logging
from artisanlib.dialogs import ArtisanDialog
from artisanlib.widgets import MyQLabel, MyQLCDNumber, ClickableLCDFrame

try:
    from PyQt6.QtCore import (Qt, QSettings, pyqtSlot, QPoint) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QFrame, QWidget, QLCDNumber, QHBoxLayout, QVBoxLayout) # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import (Qt, QSettings, pyqtSlot, QPoint) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QFrame, QWidget, QLCDNumber, QHBoxLayout, QVBoxLayout) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from typing import Final, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QLayout # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent, QResizeEvent # pylint: disable=unused-import


_log: Final[logging.Logger] = logging.getLogger(__name__)

class LargeLCDs(ArtisanDialog):

    __slots__ = ['lcds1', 'lcds2', 'lcds1styles', 'lcds2styles', 'lcds1labelsUpper', 'lcds2labelsUpper', 'lcds1labelsLower', 'lcds2labelsLower',
        'lcds1frames', 'lcds2frames', 'visibleFrames', 'tight', 'layoutNr', 'swaplcds']

    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        if aw.get_os()[0] == 'RPi':
            super().__init__(None, aw) # set the parent to None to make LargeLCD windows on RPi Bookworm non-modal (not blocking the main window)
        else:
            super().__init__(parent, aw) # if parent is set to None, largeLCD panels hide behind the main window in full screen mode on Windows!
        # it is assumed that both lists of lcds (lcd1 & lcd2) have the same length
        # the same is assumed for the other lists below:
        self.lcds1:List[QLCDNumber] = []
        self.lcds2:List[QLCDNumber] = []
        self.lcds1styles:List[str] = []
        self.lcds2styles:List[str] = []
        self.lcds1labelsUpper:List[MyQLabel] = []
        self.lcds1labelsLower:List[MyQLabel] = []
        self.lcds2labelsUpper:List[MyQLabel] = []
        self.lcds2labelsLower:List[MyQLabel] = []
        self.lcds1frames:List[ClickableLCDFrame] = []
        self.lcds2frames:List[ClickableLCDFrame] = []
        self.visibleFrames:List[ClickableLCDFrame] = [] # visibility flags in display order for all lcd frames
        self.tight:bool = False
        self.layoutNr:int = -1 # -1: unknown, 0: landscape, 1: portrait
        self.swaplcds:bool = False
#        self.setWindowModality(Qt.WindowModality.NonModal) # this seems not to be effective on RPi bookworm thus we set the parent to None
        windowFlags = self.windowFlags()
        windowFlags |= Qt.WindowType.Tool
        self.setWindowFlags(windowFlags)

    def resizeEvent(self, event:Optional['QResizeEvent']) -> None:
        super().resizeEvent(event)
        if event is not None:
            w = event.size().width()
            h = event.size().height()
            self.chooseLayout(w,h)

    def landscapeLayout(self) -> 'QLayout':
        self.tight = False
        self.makeLCDs()
        landscapelayout = QHBoxLayout()
        for i in range(min(len(self.lcds1frames),len(self.lcds2frames))):
            if self.swaplcds:
                landscapelayout.addWidget(self.lcds2frames[i])
                landscapelayout.addWidget(self.lcds1frames[i])
            else:
                landscapelayout.addWidget(self.lcds1frames[i])
                landscapelayout.addWidget(self.lcds2frames[i])
        landscapelayout.setSpacing(0)
        landscapelayout.setContentsMargins(0, 0, 0, 0)
        return landscapelayout

    def portraitLayout(self) -> 'QLayout':
        self.tight = True
        self.makeLCDs()
        portraitlayout = QVBoxLayout()
        for i in range(min(len(self.lcds1frames),len(self.lcds2frames))):
            if self.swaplcds:
                portraitlayout.addWidget(self.lcds2frames[i],1)
                portraitlayout.addWidget(self.lcds1frames[i],1)
            else:
                portraitlayout.addWidget(self.lcds1frames[i],1)
                portraitlayout.addWidget(self.lcds2frames[i],1)
        portraitlayout.setSpacing(0)
        portraitlayout.setContentsMargins(0, 0, 0, 0)
        return portraitlayout

    def hideAllEmptyLabels(self) -> None:
        if all(ll is not None and ll.text().strip() == '' for ll in (self.lcds1labelsLower + self.lcds2labelsLower)):
            # all lower labels empty, hide them to gain space
            self.lowerLabelssvisibility(False)
        else:
            self.lowerLabelssvisibility(True)
        if all(ll is not None and ll.text().strip() == '' for ll in (self.lcds1labelsUpper + self.lcds2labelsUpper)):
            # all lower labels empty, hide them to gain space
            self.upperLabelssvisibility(False)
        else:
            self.upperLabelssvisibility(True)

    def hideOuterEmptyLabels(self) -> None:
        all_frames = [val for pair in zip(self.lcds1frames, self.lcds2frames) for val in pair]
        visible_frames = []
        for i, _ in enumerate(all_frames):
            if len(self.visibleFrames) > i and self.visibleFrames[i]:
                visible_frames.append(all_frames[i])

        if visible_frames:
            all_upper_labels = [val for pair in zip(self.lcds1labelsUpper, self.lcds2labelsUpper) for val in pair]
            for i, ll in enumerate(all_upper_labels):
                if (all_frames[i] == visible_frames[0] and ll.text().strip() == ''):
                    # hide first visible upper label if empty
                    if not ll.isHidden():
                        ll.setVisible(False)
                elif len(self.visibleFrames) > i and self.visibleFrames[i] and ll.isHidden():
                    ll.setVisible(True)
            all_lower_labels = [val for pair in zip(self.lcds1labelsLower, self.lcds2labelsLower) for val in pair]
            for i, ll in enumerate(all_lower_labels):
                if (all_frames[i] == visible_frames[-1] and ll.text().strip() == ''):
                    # hide last visible label if empty
                    if not ll.isHidden():
                        ll.setVisible(False)
                elif len(self.visibleFrames) > i and self.visibleFrames[i] and ll.isHidden():
                    ll.setVisible(True)

    def lowerLabelssvisibility(self, b:bool) -> None:
        lower_labels = [val for pair in zip(self.lcds1labelsLower, self.lcds2labelsLower) for val in pair]
        for i, ll in enumerate(lower_labels):
            if len(self.visibleFrames) > i and self.visibleFrames[i] and ll.isHidden() == b:
                ll.setVisible(b)

    def upperLabelssvisibility(self, b:bool) -> None:
        upper_labels = [val for pair in zip(self.lcds1labelsUpper, self.lcds2labelsUpper) for val in pair]
        for i, ll in enumerate(upper_labels):
            if len(self.visibleFrames) > i and self.visibleFrames[i] and ll.isHidden() == b:
                ll.setVisible(b)

    # n the number of layout to be set (0: landscape, 1: portrait)
    # calling reLayout() without arg will force a relayout using the current layout
    def reLayout(self, n:Optional[int] = None) -> None:
        if self.layoutNr != n:
            newLayoutNr = self.layoutNr if n is None else n
            newLayoutNr = max(newLayoutNr, 0)
            # release old layout
            if self.layout():
                QWidget().setLayout(self.layout())
            # install the new layout
            if newLayoutNr == 0:
                self.setLayout(self.landscapeLayout())
                # in horizontal mode we hide rows of empty labels to save space
                self.hideAllEmptyLabels()
            elif newLayoutNr == 1:
                self.setLayout(self.portraitLayout())
                # in vertical mode we hide the top and bottom labels if empty
                self.hideOuterEmptyLabels()
            self.raise_()
            self.activateWindow()
            self.layoutNr = newLayoutNr

    def chooseLayout(self, w:int, h:int) -> None:
        if w > h:
            self.reLayout(0)
        else:
            self.reLayout(1)

    def makeLCD(self, s:str) -> MyQLCDNumber:
        lcd = MyQLCDNumber()
        lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        lcd.setFrameStyle(QFrame.Shadow.Plain)
        lcd.setSmallDecimalPoint(False)
        lcd.setStyleSheet(f'QLCDNumber {{ color: {self.aw.lcdpaletteF[s]}; background-color: {self.aw.lcdpaletteB[s]};}}')
        return lcd

    @staticmethod
    def makeLabel(name:str) -> MyQLabel:
        label = MyQLabel(name)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        return label

    @staticmethod
    def makeLCDframe(lcdUpper:QWidget, lcd:QWidget, lcdLower:QWidget) -> ClickableLCDFrame:
        lcdlayout = QVBoxLayout()
        lcdlayout.addWidget(lcdUpper,1)
        lcdlayout.addWidget(lcd,5)
        lcdlayout.addWidget(lcdLower,1)
        lcdlayout.setSpacing(0)
        lcdlayout.setContentsMargins(0, 0, 0, 0)
        frame = ClickableLCDFrame()
        frame.setContentsMargins(0, 0, 0, 0)
        frame.setLayout(lcdlayout)
        return frame

    # to be implemented in subclasses
    def makeLCDs(self) -> None: # pylint: disable=no-self-use
        return None

    def updateVisibilities(self, l1:List[bool], l2:List[bool]) -> None:
        self.visibleFrames = [val for pair in zip(l1,l2) for val in pair] # type: ignore # pyright: error: "object*" is not iterable
        for i, lc in enumerate(l1):
            try:
                self.lcds1frames[i].setVisible(lc)
            except Exception: # pylint: disable=broad-except
                pass
        for i, lc in enumerate(l2):
            try:
                self.lcds2frames[i].setVisible(lc)
            except Exception: # pylint: disable=broad-except
                pass

    def updateStyles(self) -> None:
        for i,s in enumerate(self.lcds1styles):
            try:
                self.lcds1labelsUpper[i].setStyleSheet(f'QLabel {{ color: {self.aw.lcdpaletteF[s]}; background-color: {self.aw.lcdpaletteB[s]};}}')
            except Exception: # pylint: disable=broad-except
                pass
            try:
                self.lcds1[i].setStyleSheet(f'QLCDNumber {{ color: {self.aw.lcdpaletteF[s]}; background-color: {self.aw.lcdpaletteB[s]};}}')
            except Exception: # pylint: disable=broad-except
                pass
            try:
                self.lcds1labelsLower[i].setStyleSheet(f'QLabel {{ color: {self.aw.lcdpaletteF[s]}; background-color: {self.aw.lcdpaletteB[s]};}}')
            except Exception: # pylint: disable=broad-except
                pass
        for i,s in enumerate(self.lcds2styles):
            try:
                self.lcds2labelsUpper[i].setStyleSheet(f'QLabel {{ color: {self.aw.lcdpaletteF[s]}; background-color: {self.aw.lcdpaletteB[s]};}}')
            except Exception: # pylint: disable=broad-except
                pass
            try:
                self.lcds2[i].setStyleSheet(f'QLCDNumber {{ color: {self.aw.lcdpaletteF[s]}; background-color: {self.aw.lcdpaletteB[s]};}}')
            except Exception: # pylint: disable=broad-except
                pass
            try:
                self.lcds2labelsLower[i].setStyleSheet(f'QLabel {{ color: {self.aw.lcdpaletteF[s]}; background-color: {self.aw.lcdpaletteB[s]};}}')
            except Exception: # pylint: disable=broad-except
                pass

    # in horizontal layouts we add one more digit per LCD than needed as spacer for separation
    # in vertical layouts we add only the exact number of digits that are needed to fully display the number to save space (tight mode)
    def updateDecimals(self) -> None:
        for i,(lcd1,lcd2) in enumerate(zip(self.lcds1,self.lcds2)):
            for j,lcd in enumerate([lcd1,lcd2]):
                if self.aw.qmc.LCDdecimalplaces and not self.aw.qmc.intChannel(i,j):
                    if self.tight:
                        lcd.setDigitCount(5)
                        if not self.aw.qmc.flagon:
                            lcd.display('  -.-')
                    else:
                        lcd.setDigitCount(6)
                        if not self.aw.qmc.flagon:
                            lcd.display('   -.-')
                elif self.tight:
                    lcd.setDigitCount(5)
                    if not self.aw.qmc.flagon:
                        lcd.display('   --')
                else:
                    lcd.setDigitCount(6)
                    if not self.aw.qmc.flagon:
                        lcd.display('   --')

    # note that values1 and values2 can contain None values indicating that those lcds are not updated in this round
    def updateValues(self, values1:List[Optional[str]], values2:List[Optional[str]], **kwargs:Optional[str]) -> None:
        del kwargs
        for i,v1 in enumerate(values1):
            try:
                if v1 is not None:
                    self.lcds1[i].display(v1)
            except Exception: # pylint: disable=broad-except
                pass
        for i,v2 in enumerate(values2):
            try:
                if v2 is not None:
                    self.lcds2[i].display(v2)
            except Exception: # pylint: disable=broad-except
                pass

    # note that all given values can contain None indicating that those labels are not updated in this round
    def updateLabels(self, lowerlabels1:List[Optional[str]],
            lowerlabels2:List[Optional[str]],
            upperlabels1:List[Optional[str]],
            upperlabels2:List[Optional[str]],
            **kwargs:str) -> None:
        del kwargs
        if lowerlabels1 is not None:
            for i,v1 in enumerate(lowerlabels1):
                try:
                    if v1 is not None:
                        self.lcds1labelsLower[i].setText(v1)
                        self.lcds1labelsLower[i].repaint()
                except Exception: # pylint: disable=broad-except
                    pass
        if lowerlabels2 is not None:
            for i,v2 in enumerate(lowerlabels2):
                try:
                    if v2 is not None:
                        self.lcds2labelsLower[i].setText(v2)
                        self.lcds2labelsLower[i].repaint()
                except Exception: # pylint: disable=broad-except
                    pass
        if upperlabels1 is not None:
            for i,v1 in enumerate(upperlabels1):
                try:
                    if v1 is not None:
                        self.lcds1labelsUpper[i].setText(v1)
                        self.lcds1labelsUpper[i].repaint()
                except Exception: # pylint: disable=broad-except
                    pass
        if upperlabels2 is not None:
            for i,v2 in enumerate(upperlabels2):
                try:
                    if v2 is not None:
                        self.lcds2labelsUpper[i].setText(v2)
                        self.lcds2labelsUpper[i].repaint()
                except Exception: # pylint: disable=broad-except
                    pass
        if self.layoutNr == 1:
            # show all labels in portrait mode
            self.hideOuterEmptyLabels()
        elif self.layoutNr == 0:
            # hide all empty upperlabels in landscape mode
            self.hideAllEmptyLabels()


class LargeMainLCDs(LargeLCDs):

    __slots__ = ['lcd0']

    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        self.lcd0:Optional[QLCDNumber] = None # Timer
        # we add the ET lcd to the lcd1 list and the BT lcds to the lcd2 list (same for styles, labels and frames
        super().__init__(parent, aw)
        settings = QSettings()
        if settings.contains('LCDGeometry'):
            self.restoreGeometry(settings.value('LCDGeometry'))
        else:
            self.resize(200,100)
        self.chooseLayout(self.width(),self.height())
        self.setWindowTitle(QApplication.translate('Menu', 'Main LCDs'))

    def updateVisiblitiesETBT(self) -> None:
        self.updateVisibilities([self.aw.qmc.ETlcd],[self.aw.qmc.BTlcd])

    def setTimerLCDcolor(self, fc:str, bc:str) -> None:
        if self.lcd0 is not None:
            self.lcd0.setStyleSheet(f'QLCDNumber {{ color: {fc}; background-color: {bc};}}')

    def updateStyles(self) -> None:
        self.setTimerLCDcolor(self.aw.lcdpaletteF['timer'],self.aw.lcdpaletteB['timer'])
        super().updateStyles()

    def updateValues(self, values1:List[Optional[str]], values2:List[Optional[str]],
            **kwargs:Optional[str]) -> None:
        super().updateValues(values1,values2,**kwargs)
        if self.lcd0 is not None and 'time' in kwargs and kwargs['time'] is not None:
            self.lcd0.display(kwargs['time'])

    # create LCDs, LCD labels and LCD frames
    def makeLCDs(self) -> None:
        # time LCD
        self.lcd0 = self.makeLCD('timer') # time
        self.lcd0.setDigitCount(5)
        self.lcd0.display('00:00')
        self.lcd0.clicked.connect(self.aw.superusermodeLeftClicked)
        # ET
        ETlcd = self.makeLCD('et') # Environmental Temperature ET
        ETlabelUpper = self.makeLabel(f'<b>{self.aw.ETname.format(self.aw.qmc.etypes[0],self.aw.qmc.etypes[1],self.aw.qmc.etypes[2],self.aw.qmc.etypes[3])}</b> ')
        ETlabelLower = self.makeLabel(' ')
        #
        self.lcds1 = [ETlcd]
        self.lcds1styles = ['et']
        self.lcds1labelsUpper = [ETlabelUpper]
        self.lcds1labelsLower = [ETlabelLower]
        self.lcds1frames = [self.makeLCDframe(ETlabelUpper,ETlcd,ETlabelLower)]
        self.lcds1frames[0].left_clicked.connect(self.aw.toggleETCurve)
        self.lcds1frames[0].setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lcds1frames[0].customContextMenuRequested.connect(self.aw.setTareET)
        # BT
        BTlcd = self.makeLCD('bt') # Bean Temperature BT
        BTlabelUpper = self.makeLabel(f'<b>{self.aw.BTname.format(self.aw.qmc.etypes[0],self.aw.qmc.etypes[1],self.aw.qmc.etypes[2],self.aw.qmc.etypes[3])}</b> ')
        BTlabelLower = self.makeLabel(' ')
        #
        self.lcds2 = [BTlcd]
        self.lcds2styles = ['bt']
        self.lcds2labelsUpper = [BTlabelUpper]
        self.lcds2labelsLower = [BTlabelLower]
        self.lcds2frames = [self.makeLCDframe(BTlabelUpper,BTlcd,BTlabelLower)]
        self.lcds2frames[0].left_clicked.connect(self.aw.toggleBTCurve)
        self.lcds2frames[0].setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lcds2frames[0].customContextMenuRequested.connect(self.aw.setTareBT)
        ##
        self.updateVisiblitiesETBT()
        self.updateStyles()
        self.updateDecimals()

    def landscapeLayout(self) -> 'QLayout':
        self.tight = False
        self.makeLCDs()
        templayout = QHBoxLayout()
        if self.aw.qmc.swaplcds:
            templayout.addWidget(self.lcds2frames[0])
            templayout.addWidget(self.lcds1frames[0])
        else:
            templayout.addWidget(self.lcds1frames[0])
            templayout.addWidget(self.lcds2frames[0])
        landscapelayout = QVBoxLayout()
        if self.lcd0 is not None:
            landscapelayout.addWidget(self.lcd0, 1)
        landscapelayout.addLayout(templayout, 1)
        landscapelayout.setSpacing(0)
        landscapelayout.setContentsMargins(0, 0, 0, 0)
        return landscapelayout

    def landscapeTightLayout(self) -> 'QLayout':
        self.tight = False
        self.makeLCDs()
        landscapetightlayout = QHBoxLayout()
        if self.lcd0 is not None:
            landscapetightlayout.addWidget(self.lcd0, 1)
        if self.aw.qmc.swaplcds:
            landscapetightlayout.addWidget(self.lcds2frames[0],1)
            landscapetightlayout.addWidget(self.lcds1frames[0],1)
        else:
            landscapetightlayout.addWidget(self.lcds1frames[0],1)
            landscapetightlayout.addWidget(self.lcds2frames[0],1)
        landscapetightlayout.setSpacing(0)
        landscapetightlayout.setContentsMargins(0, 0, 0, 0)
        return landscapetightlayout

    def portraitLayout(self) -> 'QLayout':
        self.tight = True
        self.makeLCDs()
        portraitlayout = QVBoxLayout()
        if self.lcd0 is not None:
            portraitlayout.addWidget(self.lcd0,1)
        if self.aw.qmc.swaplcds:
            portraitlayout.addWidget(self.lcds2frames[0],1)
            portraitlayout.addWidget(self.lcds1frames[0],1)
        else:
            portraitlayout.addWidget(self.lcds1frames[0],1)
            portraitlayout.addWidget(self.lcds2frames[0],1)
        portraitlayout.setSpacing(0)
        portraitlayout.setContentsMargins(0, 0, 0, 0)
        return portraitlayout

    # n the number of layout to be set (0: landscape, 1: landscape tight, 2: portrait)
    # calling reLayout() without arg will force a relayout using the current layout
    def reLayout(self, n:Optional[int] = None) -> None:
        if self.layoutNr != n:
            newLayoutNr = self.layoutNr if n is None else n
            newLayoutNr = max(newLayoutNr,0)
            # release old layout
            if self.layout():
                QWidget().setLayout(self.layout())
            # install the new layout
            if newLayoutNr == 0:
                self.setLayout(self.landscapeLayout())
                self.hideAllEmptyLabels()
            elif newLayoutNr == 1:
                self.setLayout(self.landscapeTightLayout())
                self.hideAllEmptyLabels()
            elif newLayoutNr == 2:
                self.setLayout(self.portraitLayout())
                self.hideOuterEmptyLabels()
            self.raise_()
            self.activateWindow()
            self.layoutNr = newLayoutNr

    def chooseLayout(self, w:int, h:int) -> None:
        if w > h:
            if w > 3*h:
                self.reLayout(1)
            else:
                self.reLayout(0)
        else:
            self.reLayout(2)

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        settings = QSettings()
        #save window geometry
        settings.setValue('LCDGeometry', self.saveGeometry())
        #free resources
        self.aw.largeLCDs_dialog = None
        self.aw.LargeLCDsFlag = False
        self.aw.lcdsAction.setChecked(False)

class LargeDeltaLCDs(LargeLCDs):

    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        settings = QSettings()
        if settings.contains('DeltaLCDGeometry'):
            self.restoreGeometry(settings.value('DeltaLCDGeometry'))
        else:
            self.resize(100,200)
        self.setWindowTitle(QApplication.translate('Menu', 'Delta LCDs'))
        self.chooseLayout(self.width(),self.height())

    def makeLCDs(self) -> None:
        self.lcds1styles = ['deltaet']
        self.lcds1 = [self.makeLCD(self.lcds1styles[0])] # DeltaET
        label1Upper = self.makeLabel(f'<b>&Delta;{self.aw.ETname.format(self.aw.qmc.etypes[0],self.aw.qmc.etypes[1],self.aw.qmc.etypes[2],self.aw.qmc.etypes[3])}</b> ')
        label1Lower = self.makeLabel(' ')
        self.lcds1labelsUpper = [label1Upper]
        self.lcds1labelsLower = [label1Lower]
        self.lcds1frames = [self.makeLCDframe(label1Upper,self.lcds1[0],label1Lower)]
        self.lcds1frames[0].left_clicked.connect(self.aw.toggleDeltaETCurve)
        #
        self.lcds2styles = ['deltabt']
        self.lcds2 = [self.makeLCD(self.lcds2styles[0])] # DeltaBT
        label2Upper = self.makeLabel(f'<b>&Delta;{self.aw.BTname.format(self.aw.qmc.etypes[0],self.aw.qmc.etypes[1],self.aw.qmc.etypes[2],self.aw.qmc.etypes[3])}</b> ')
        label2Lower = self.makeLabel(' ')
        self.lcds2labelsUpper = [label2Upper]
        self.lcds2labelsLower = [label2Lower]
        self.lcds2frames = [self.makeLCDframe(label2Upper,self.lcds2[0],label2Lower)]
        self.lcds2frames[0].left_clicked.connect(self.aw.toggleDeltaBTCurve)
        ##
        self.updateVisiblitiesDeltaETBT()
        self.updateStyles()
        self.updateDecimals()

    def updateVisiblitiesDeltaETBT(self) -> None:
        self.updateVisibilities([self.aw.qmc.DeltaETlcdflag],[self.aw.qmc.DeltaBTlcdflag])

    def reLayout(self, n:Optional[int] = None) -> None:
        self.swaplcds = self.aw.qmc.swapdeltalcds
        super().reLayout(n)

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        settings = QSettings()
        #save window geometry
        settings.setValue('DeltaLCDGeometry',self.saveGeometry())
        self.aw.largeDeltaLCDs_dialog = None
        self.aw.LargeDeltaLCDsFlag = False
        self.aw.deltalcdsAction.setChecked(False)

class LargePIDLCDs(LargeLCDs):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        settings = QSettings()
        if settings.contains('PIDLCDGeometry'):
            self.restoreGeometry(settings.value('PIDLCDGeometry'))
        else:
            self.resize(100,200)
        self.setWindowTitle(QApplication.translate('Menu', 'PID LCDs'))
        self.chooseLayout(self.width(),self.height())

    def makeLCDs(self) -> None:
        self.lcds1styles = ['sv']
        self.lcds1 = [self.makeLCD(self.lcds1styles[0])] # PID SV
        label1Upper = self.makeLabel('<b>' + QApplication.translate('Label', 'PID SV') + '</b> ')
        label1Lower = self.makeLabel(' ')
        self.lcds1labelsUpper = [label1Upper]
        self.lcds1labelsLower = [label1Lower]
        self.lcds1frames = [self.makeLCDframe(label1Upper,self.lcds1[0],label1Lower)]
        #
        self.lcds2styles = ['sv']
        self.lcds2 = [self.makeLCD(self.lcds2styles[0])] # PID %
        label2Upper = self.makeLabel('<b>' + QApplication.translate('Label', 'PID %') + '</b> ')
        label2Lower = self.makeLabel(' ')
        self.lcds2labelsUpper = [label2Upper]
        self.lcds2labelsLower = [label2Lower]
        self.lcds2frames = [self.makeLCDframe(label2Upper,self.lcds2[0],label2Lower)]
        ##
        self.updateVisiblitiesPID()
        self.updateStyles()
        self.updateDecimals()

    def updateVisiblitiesPID(self) -> None:
        if self.aw.ser.showFujiLCDs and self.aw.qmc.device == 0 or self.aw.qmc.device == 26:
            self.updateVisibilities([True],[True])
        else:
            self.updateVisibilities([False],[False])

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        settings = QSettings()
        #save window geometry
        settings.setValue('PIDLCDGeometry',self.saveGeometry())
        self.aw.largePIDLCDs_dialog = None
        self.aw.LargePIDLCDsFlag = False
        self.aw.pidlcdsAction.setChecked(False)

class LargeExtraLCDs(LargeLCDs):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        settings = QSettings()
        if settings.contains('ExtraLCDGeometry'):
            self.restoreGeometry(settings.value('ExtraLCDGeometry'))
        else:
            self.resize(100,200)
        self.chooseLayout(self.width(),self.height())
        self.setWindowTitle(QApplication.translate('Menu', 'Extra LCDs'))

    @pyqtSlot(QPoint)
    def setTare_slot(self,_:QPoint) -> None:
        sender = self.sender()
        try:
            assert isinstance(sender, ClickableLCDFrame)
            idx = self.lcds1frames.index(sender)
            self.aw.setTare(2+idx*2)
        except Exception: # pylint: disable=broad-except
            pass
        try:
            assert isinstance(sender, ClickableLCDFrame)
            idx = self.lcds2frames.index(sender)
            self.aw.setTare(2+idx*2 + 1)
        except Exception: # pylint: disable=broad-except
            pass

    @pyqtSlot()
    def toggleExtraCurve1(self) -> None:
        try:
            sender = self.sender()
            assert isinstance(sender, ClickableLCDFrame)
            i = self.lcds1frames.index(sender)
            self.aw.extraCurveVisibility1[i] = not self.aw.extraCurveVisibility1[i]
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        self.aw.qmc.redraw_keep_view(recomputeAllDeltas=False)

    @pyqtSlot()
    def toggleExtraCurve2(self) -> None:
        try:
            sender = self.sender()
            assert isinstance(sender, ClickableLCDFrame)
            i = self.lcds2frames.index(sender)
            self.aw.extraCurveVisibility2[i] = not self.aw.extraCurveVisibility2[i]
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        self.aw.qmc.redraw_keep_view(recomputeAllDeltas=False)

    def makeLCDs(self) -> None:
        self.lcds1 = []
        self.lcds2 = []
        self.lcds1styles = []
        self.lcds2styles = []
        self.lcds1labelsUpper = []
        self.lcds2labelsUpper = []
        self.lcds1labelsLower = []
        self.lcds2labelsLower = []
        self.lcds1frames = []
        self.lcds2frames = []
        for i in range(len(self.aw.qmc.extradevices)): #(self.aw.nLCDS):
            lcdstyle = 'sv'
            #
            lcd1 = self.makeLCD(lcdstyle)
            self.lcds1.append(lcd1)
            self.lcds1styles.append(lcdstyle)
            l1 = '<b>' + self.aw.qmc.extraname1[i] + '</b>'
            try:
                l1 = l1.format(self.aw.qmc.etypes[0],self.aw.qmc.etypes[1],self.aw.qmc.etypes[2],self.aw.qmc.etypes[3])
            except Exception: # pylint: disable=broad-except
                pass
            label1Upper = self.makeLabel(l1)
            self.lcds1labelsUpper.append(label1Upper)
            label1Lower = self.makeLabel(' ')
            self.lcds1labelsLower.append(label1Lower)
            self.lcds1frames.append(self.makeLCDframe(label1Upper,lcd1,label1Lower))
            self.lcds1frames[-1].left_clicked.connect(self.toggleExtraCurve1)
            self.lcds1frames[-1].setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.lcds1frames[-1].customContextMenuRequested.connect(self.setTare_slot)
            #
            lcd2 = self.makeLCD(lcdstyle)
            self.lcds2.append(lcd2)
            self.lcds2styles.append(lcdstyle)
            l2 = '<b>' + self.aw.qmc.extraname2[i] + '</b>'
            try:
                l2 = l2.format(self.aw.qmc.etypes[0],self.aw.qmc.etypes[1],self.aw.qmc.etypes[2],self.aw.qmc.etypes[3])
            except Exception: # pylint: disable=broad-except
                pass
            label2Upper = self.makeLabel(l2)
            self.lcds2labelsUpper.append(label2Upper)
            label2Lower = self.makeLabel(' ')
            self.lcds2labelsLower.append(label2Lower)
            self.lcds2frames.append(self.makeLCDframe(label2Upper,lcd2,label2Lower))
            self.lcds2frames[-1].left_clicked.connect(self.toggleExtraCurve2)
            self.lcds2frames[-1].setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.lcds2frames[-1].customContextMenuRequested.connect(self.setTare_slot)
        ##
        self.updateVisiblitiesExtra()
        self.updateStyles()
        self.updateDecimals()

    def updateVisiblitiesExtra(self) -> None:
        self.updateVisibilities(self.aw.extraLCDvisibility1,self.aw.extraLCDvisibility2)

    def updateStyles(self) -> None:
        super().updateStyles()
        for i,s in enumerate(self.lcds1styles):
            try:
                self.lcds1labelsUpper[i].setStyleSheet(f'QLabel {{ color: {self.aw.qmc.extradevicecolor1[i]}; background-color: {self.aw.lcdpaletteB[s]};}}')
            except Exception: # pylint: disable=broad-except
                pass
        for i,s in enumerate(self.lcds2styles):
            try:
                self.lcds2labelsUpper[i].setStyleSheet(f'QLabel {{ color: {self.aw.qmc.extradevicecolor2[i]}; background-color: {self.aw.lcdpaletteB[s]};}}')
            except Exception: # pylint: disable=broad-except
                pass

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        settings = QSettings()
        #save window geometry
        settings.setValue('ExtraLCDGeometry',self.saveGeometry())
        self.aw.largeExtraLCDs_dialog = None
        self.aw.LargeExtraLCDsFlag = False
        self.aw.extralcdsAction.setChecked(False)

class LargePhasesLCDs(LargeLCDs):

    __slots__ = ['labels', 'values1', 'values2']

    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        self.labels:List[str] = [' ', ' ', ' ', str(self.formatLabel('AUC'))] # formatted labels
        self.values1:List[str] = [' ']*2
        self.values2:List[str] = [' ']*2
        super().__init__(parent, aw)
        settings = QSettings()
        if settings.contains('PhasesLCDGeometry'):
            self.restoreGeometry(settings.value('PhasesLCDGeometry'))
        else:
            self.resize(100,200)
        self.chooseLayout(self.width(),self.height())
        self.setWindowTitle(QApplication.translate('Menu', 'Phases LCDs'))

    @staticmethod
    def formatLabel(ll:Optional[str]) -> Optional[str]:
        if ll is None:
            return None
        return f'<b>{ll}</b>'

    def makeLCDs(self) -> None:
        self.lcds1styles = ['sv','sv']
        self.lcds1 = [
            self.makeLCD(self.lcds1styles[0]), # Phase 1
            self.makeLCD(self.lcds1styles[1])  # Phase 3
            ]
        label1Upper = self.makeLabel(self.labels[0])
        label1Lower = self.makeLabel(' ')
        label3Upper = self.makeLabel(self.labels[2])
        label3Lower = self.makeLabel(' ')
        self.lcds1labelsUpper = [label1Upper,label3Upper]
        self.lcds1labelsLower = [label1Lower,label3Lower]
        self.lcds1frames = [self.makeLCDframe(label1Upper,self.lcds1[0],label1Lower),self.makeLCDframe(label3Upper,self.lcds1[1],label3Lower)]
        for f in self.lcds1frames:
            f.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            f.customContextMenuRequested.connect(self.aw.PhaseslcdClicked)
        #
        self.lcds2styles = ['sv','sv']
        self.lcds2 = [
            self.makeLCD(self.lcds2styles[0]), # Phase 2
            self.makeLCD(self.lcds2styles[1])  # AUC
            ]
        label2Upper = self.makeLabel(self.labels[1])
        label2Lower = self.makeLabel(' ')
        label4Upper = self.makeLabel(self.labels[3])
        label4Lower = self.makeLabel(' ')
        self.lcds2labelsUpper = [label2Upper,label4Upper]
        self.lcds2labelsLower = [label2Lower,label4Lower]
        self.lcds2frames = [self.makeLCDframe(label2Upper,self.lcds2[0],label2Lower),self.makeLCDframe(label4Upper,self.lcds2[1],label4Lower)]
        self.lcds2frames[0].setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lcds2frames[0].customContextMenuRequested.connect(self.aw.PhaseslcdClicked)
        self.lcds2frames[1].setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lcds2frames[1].customContextMenuRequested.connect(self.aw.AUClcdClicked)
        ##
        for i, _ in enumerate(self.values1):
            self.lcds1[i].display(self.values1[i])
        for i, _ in enumerate(self.values2):
            self.lcds2[i].display(self.values2[i])
        ##
        self.updateVisiblitiesPhases()
        self.updateStyles()
        self.updateDecimals()

    def updateValues(self, values1:List[Optional[str]], values2:List[Optional[str]],
            **kwargs:Optional[str]) -> None:
        del kwargs
        # don't update None values
        for i,v in enumerate(values1):
            if v is not None:
                self.values1[i] = v
        for i,v in enumerate(values2):
            if v is not None:
                self.values2[i] = v
        super().updateValues(values1,values2)

    def updateVisiblitiesPhases(self) -> None:
        self.updateVisibilities([True,True],[True,self.aw.qmc.AUClcdFlag])

    def updateDecimals(self) -> None:
        for lcd in self.lcds1 + self.lcds2:
            lcd.setDigitCount(6)

    def updatePhasesLabels(self, labels:List[Optional[str]]) -> None:
        # don't update None values
        for i, ll in enumerate(map(self.formatLabel,labels)):
            if ll is not None:
                self.labels[i] = ll
        super().updateLabels([' ']*2,[' ']*2,[self.labels[0],self.labels[2]],[self.labels[1],self.labels[3]])

    def updateAUCstyle(self, style:str) -> None:
        self.lcds2[1].setStyleSheet(style)

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        settings = QSettings()
        #save window geometry
        settings.setValue('PhasesLCDGeometry',self.saveGeometry())
        self.aw.largePhasesLCDs_dialog = None
        self.aw.LargePhasesLCDsFlag = False
        self.aw.phaseslcdsAction.setChecked(False)

class LargeScaleLCDs(LargeLCDs):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        settings = QSettings()
        if settings.contains('ScaleLCDGeometry'):
            self.restoreGeometry(settings.value('ScaleLCDGeometry'))
        else:
            self.resize(100,200)
        self.setWindowTitle(QApplication.translate('Menu', 'Scale LCDs'))
        self.chooseLayout(self.width(),self.height())
        self.updateValues([''],[''])

    def weightLabel(self, unit:Optional[str] = None) -> str:
        if unit is None:
            unit = self.aw.qmc.weight[2]
        return f"<b>{QApplication.translate('Label', 'Weight')} ({unit})</b> "

    def totalLabel(self, unit:Optional[str] = None) -> str:
        if unit is None:
            unit = self.aw.qmc.weight[2]
        return f"<b>{QApplication.translate('Label', 'Total')} ({unit})</b> "

    def updateWeightUnitWeight(self, unit:Optional[str] = None) -> None:
        if len(self.lcds1labelsUpper)>0:
            self.lcds1labelsUpper[0].setText(self.weightLabel(unit))

    def updateWeightUnitTotal(self, unit:Optional[str] = None) -> None:
        if len(self.lcds2labelsUpper)>0:
            self.lcds2labelsUpper[0].setText(self.totalLabel(unit))

    def updateWeightUnit(self, unit:Optional[str] = None) -> None:
        self.updateWeightUnitWeight(unit)
        self.updateWeightUnitTotal(unit)

    def makeLCDs(self) -> None:
        self.lcds1styles = ['slowcoolingtimer']
        self.lcds1 = [self.makeLCD(self.lcds1styles[0])] # Weight
        label1Upper = self.makeLabel(self.weightLabel())
        label1Lower = self.makeLabel(' ')
        self.lcds1labelsUpper = [label1Upper]
        self.lcds1labelsLower = [label1Lower]
        self.lcds1frames = [self.makeLCDframe(label1Upper,self.lcds1[0],label1Lower)]
        #
        self.lcds2styles = ['sv']
        self.lcds2 = [self.makeLCD(self.lcds2styles[0])] # Total
        label2Upper = self.makeLabel(self.totalLabel())
        label2Lower = self.makeLabel(' ')
        self.lcds2labelsUpper = [label2Upper]
        self.lcds2labelsLower = [label2Lower]
        self.lcds2frames = [self.makeLCDframe(label2Upper,self.lcds2[0],label2Lower)]
        ##
        self.updateVisiblitiesScale()
        self.updateStyles()
        self.updateDecimals()

    def updateVisiblitiesScale(self) -> None:
        self.updateVisibilities([True],[True])

    def updateDecimals(self) -> None:
        for (lcd1,lcd2) in zip(self.lcds1,self.lcds2):
            for lcd in [lcd1,lcd2]:
                if self.tight:
                    lcd.setDigitCount(6)
                else:
                    lcd.setDigitCount(7)
                if lcd.value() == 0:
                    lcd.display('')

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        settings = QSettings()
        #save window geometry
        settings.setValue('ScaleLCDGeometry',self.saveGeometry())
        self.aw.largeScaleLCDs_dialog = None
        self.aw.LargeScaleLCDsFlag = False
        self.aw.scalelcdsAction.setChecked(False)
