#
# ABOUT
# Artisan Cup Profile Dialog

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
from artisanlib.dialogs import ArtisanResizeablDialog
from artisanlib.widgets import MyQDoubleSpinBox

from typing import Optional, List, Any, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent # pylint: disable=unused-import

try:
    from PyQt6.QtCore import (Qt, pyqtSlot, QSettings) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QVBoxLayout, QLabel, # @UnusedImport @Reimport  @UnresolvedImport
                                 QLineEdit,QPushButton, QComboBox, QDialogButtonBox, QHeaderView, # @UnusedImport @Reimport  @UnresolvedImport
                                 QTableWidget, QDoubleSpinBox, QGroupBox) # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import (Qt, pyqtSlot, QSettings) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QVBoxLayout, QLabel, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
                                 QLineEdit,QPushButton, QComboBox, QDialogButtonBox, QHeaderView, # @UnusedImport @Reimport  @UnresolvedImport
                                 QTableWidget, QDoubleSpinBox, QGroupBox) # @UnusedImport @Reimport  @UnresolvedImport

class flavorDlg(ArtisanResizeablDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        #avoid question mark context help
        flags = self.windowFlags()
        helpFlag = Qt.WindowType.WindowContextHelpButtonHint
        flags = flags & (~helpFlag)
        if not platform.system().startswith('Windows'):
            flags |= Qt.WindowType.Tool
            flags |= Qt.WindowType.CustomizeWindowHint # needed to be able to customize the close/min/max controls (at least on macOS)
            flags |= Qt.WindowType.WindowMinimizeButtonHint
            flags |= Qt.WindowType.WindowCloseButtonHint # not needed on macOS, but maybe on Linux
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setWindowFlags(flags)
        self.setWindowTitle(QApplication.translate('Form Caption','Cup Profile'))

        self.aw.hideControls(False)
        self.aw.hideLCDs(False)
        self.aw.hideSliders(False)
        self.aw.hide_minieventline(False)
        self.aw.hideExtraButtons()

        settings = QSettings()
        if settings.contains('FlavorProperties'):
            self.restoreGeometry(settings.value('FlavorProperties'))

        defaultlabel = QLabel(QApplication.translate('Label','Default'))
        self.defaultcombobox = QComboBox()
        self.defaultcombobox.addItems(['','Artisan','SCA','SCAA','CQI','SweetMarias','C','E','CoffeeGeek','Intelligentsia','IIAC','WCRC','*CUSTOM*'])
        self.defaultcombobox.setCurrentIndex(0)
        self.lastcomboboxIndex = 0
        self.defaultcombobox.currentIndexChanged.connect(self.setdefault)
        self.flavortable = QTableWidget()
        self.flavortable.setTabKeyNavigation(True)

        vheader = self.flavortable.verticalHeader()
        if vheader is not None:
            vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            vheader.setSectionsMovable(True)
            vheader.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
            vheader.setAutoScroll(False)
            vheader.sectionMoved.connect(self.sectionMoved)

        self.createFlavorTable()

        correctionLabel = QLabel(QApplication.translate('Label','Correction'))
        self.correctionSpinBox = MyQDoubleSpinBox()
        self.correctionSpinBox.setRange(-10.,10.)
        self.correctionSpinBox.setSingleStep(.25)
        self.correctionSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.correctionSpinBox.setValue(self.aw.qmc.flavors_total_correction)
        self.correctionSpinBox.valueChanged.connect(self.setcorrection)

        leftButton = QPushButton('<')
        leftButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        leftButton.clicked.connect(self.moveLeft)
        rightButton = QPushButton('>')
        rightButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        rightButton.clicked.connect(self.moveRight)
        addButton = QPushButton(QApplication.translate('Button','Add'))
        addButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        addButton.clicked.connect(self.addlabel)
        delButton = QPushButton(QApplication.translate('Button','Del'))
        delButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        delButton.clicked.connect(self.poplabel)
        saveImgButton = QPushButton(QApplication.translate('Button','Save Image'))
        saveImgButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        saveImgButton.clicked.connect(self.aw.saveVectorGraph_PDF) # save as PDF (vector)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.close)
        self.dialogbuttons.removeButton(self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel))

        self.backgroundCheck = QCheckBox(QApplication.translate('CheckBox','Background'))
        if self.aw.qmc.flavorbackgroundflag:
            self.backgroundCheck.setChecked(True)
        self.backgroundCheck.clicked.connect(self.showbackground)
        aspectlabel = QLabel(QApplication.translate('Label','Aspect Ratio'))
        self.aspectSpinBox = QDoubleSpinBox()
        self.aspectSpinBox.setToolTip(QApplication.translate('Tooltip','Aspect Ratio'))
        self.aspectSpinBox.setRange(0.5,2.)
        self.aspectSpinBox.setSingleStep(.1)
        self.aspectSpinBox.setValue(self.aw.qmc.flavoraspect)
        self.aspectSpinBox.valueChanged.connect(self.setaspect)
        flavorLayout = QHBoxLayout()
        flavorLayout.addWidget(self.flavortable)
        comboLayout = QHBoxLayout()
        comboLayout.addWidget(defaultlabel)
        comboLayout.addWidget(self.defaultcombobox)
        comboLayout.addStretch()
        aspectLayout = QHBoxLayout()
        aspectLayout.addWidget(self.backgroundCheck)
        aspectLayout.addStretch()
        aspectLayout.addWidget(aspectlabel)
        aspectLayout.addWidget(self.aspectSpinBox)
        blayout1 = QHBoxLayout()
        blayout1.addWidget(addButton)
        blayout1.addSpacing(5)
        blayout1.addWidget(delButton)
        blayout1.addStretch()
        blayout1.addSpacing(10)
        blayout1.addWidget(correctionLabel)
        blayout1.addWidget(self.correctionSpinBox)
        extralayout = QVBoxLayout()
        extralayout.addLayout(comboLayout)
        extralayout.addLayout(aspectLayout)
        extralayout.setSpacing(1)
        extraGroupLayout = QGroupBox()
        extraGroupLayout.setLayout(extralayout)
        extralayout.setContentsMargins(5,0,5,0) # left, top, right, bottom
        blayout = QHBoxLayout()
        blayout.addStretch()
        blayout.addWidget(leftButton)
        blayout.addSpacing(5)
        blayout.addWidget(rightButton)
        blayout.addStretch()
        mainButtonsLayout = QHBoxLayout()
        mainButtonsLayout.addWidget(saveImgButton)
        mainButtonsLayout.addStretch()
        mainButtonsLayout.addSpacing(7)
        mainButtonsLayout.addLayout(blayout)
        mainButtonsLayout.addStretch()
        mainButtonsLayout.addSpacing(7)
        mainButtonsLayout.addWidget(self.dialogbuttons)
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(flavorLayout)
        mainLayout.addLayout(blayout1)
        mainLayout.addWidget(extraGroupLayout)
#        mainLayout.addLayout(blayout)
        mainLayout.addLayout(mainButtonsLayout)
        mainLayout.setContentsMargins(7,5,7,5) # left, top, right, bottom
        mainLayout.setSpacing(3)
        self.setLayout(mainLayout)
        self.aw.qmc.updateFlavorchartValues() # fast incremental redraw
        self.aw.qmc.flavorchart()
        ok_button = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setFocus()

    @pyqtSlot(int,int,int)
    def sectionMoved(self, logicalIndex:int, _oldVisualIndex:int, newVisualIndex:int) -> None:
        # adjust datamodel
        swap:bool = False # default action is to move item to new position
        if QApplication.queryKeyboardModifiers() == Qt.KeyboardModifier.AltModifier:
            # if ALT/OPTION key is hold, the items are swap
            swap = True
        l:List[Any]
        for l in (self.aw.qmc.flavors, self.aw.qmc.flavorlabels):
            if swap:
                self.swapItems(l, logicalIndex, newVisualIndex)
            else:
                self.moveItem(l, logicalIndex, newVisualIndex)

        self.flavortable.clearContents() # resets the view
        self.flavortable.setRowCount(0)  # resets the data model
        self.createFlavorTable()
        self.aw.qmc.flavorchart()

    @staticmethod
    def swapItems(l:List[Any], source:int, target:int) -> None:
        l[target],l[source] = l[source],l[target]

    @staticmethod
    def moveItem(l:List[Any], source:int, target:int) -> None:
        l.insert(target, l.pop(source))

    @pyqtSlot(float)
    def setaspect(self, _:float) -> None:
        self.aw.qmc.flavoraspect = self.aspectSpinBox.value()
        self.aw.qmc.flavorchart()

    def createFlavorTable(self) -> None:
        nflavors = len(self.aw.qmc.flavorlabels)

        # self.flavortable.clear() # this crashes Ubuntu 16.04
#        if ndata != 0:
#            self.flavortable.clearContents() # this crashes Ubuntu 16.04 if device table is empty and also sometimes else
        self.flavortable.clearSelection() # this seems to work also for Ubuntu 16.04

        if nflavors:
            self.flavortable.setRowCount(nflavors)
            self.flavortable.setColumnCount(2)
            self.flavortable.setHorizontalHeaderLabels([QApplication.translate('Table', 'Label'),
                                                        QApplication.translate('Table', 'Value'),
                                                        ''])
            self.flavortable.setAlternatingRowColors(True)
            self.flavortable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.flavortable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.flavortable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.flavortable.setShowGrid(True)
            #self.flavortable.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            #populate table
            for i in range(nflavors):
                labeledit = QLineEdit(self.aw.qmc.flavorlabels[i])
                labeledit.textChanged.connect(self.setlabel)
                valueSpinBox = MyQDoubleSpinBox()
                valueSpinBox.setRange(0.,10.)
                valueSpinBox.setSingleStep(.25)
                valueSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
                val = self.aw.qmc.flavors[i]
                if self.aw.qmc.flavors[0] < 1. and self.aw.qmc.flavors[-1] < 1.: # < 0.5.0 version style compatibility
                    val *= 10.
                valueSpinBox.setValue(val)
                valueSpinBox.valueChanged.connect(self.setvalue)
                #add widgets to the table
                self.flavortable.setCellWidget(i,0,labeledit)
                self.flavortable.setCellWidget(i,1,valueSpinBox)
            self.flavortable.resizeColumnsToContents()
            header = self.flavortable.horizontalHeader()
            if header is not None:
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    @pyqtSlot(bool)
    def showbackground(self, _:bool) -> None:
        if self.backgroundCheck.isChecked():
            if not self.aw.qmc.background:
                message = QApplication.translate('Message','Background profile not found')
                self.aw.sendmessage(message)
                self.backgroundCheck.setChecked(False)
            elif len(self.aw.qmc.backgroundFlavors) != len(self.aw.qmc.flavors):
                message = QApplication.translate('Message','Background does not match number of labels')
                self.aw.sendmessage(message)
                self.aw.qmc.flavorbackgroundflag = False
                self.backgroundCheck.setChecked(False)
            else:
                self.aw.qmc.flavorbackgroundflag = True
                self.aw.qmc.flavorchart()
        else:
            self.aw.qmc.flavorbackgroundflag = False
            self.aw.qmc.flavorchart()

    @pyqtSlot(bool)
    def moveLeft(self, _:bool) -> None:
        self.aw.qmc.flavorstartangle += 5
        self.aw.qmc.flavorchart()

    @pyqtSlot(bool)
    def moveRight(self, _:bool) -> None:
        self.aw.qmc.flavorstartangle -= 5
        self.aw.qmc.flavorchart()

    def savetable(self) -> None:
        for i, _ in enumerate(self.aw.qmc.flavorlabels):
            labeledit = cast(QLineEdit, self.flavortable.cellWidget(i,0))
            valueSpinBox = cast(MyQDoubleSpinBox, self.flavortable.cellWidget(i,1))
            label = labeledit.text()
            if '\\n' in label:              #make multiple line text if "\n" found in label string
                parts = label.split('\\n')
                label = chr(10).join(parts)
            self.aw.qmc.flavorlabels[i] = label
            self.aw.qmc.flavors[i] = valueSpinBox.value()
        if self.lastcomboboxIndex == self.defaultcombobox.count()-1:
            # store the current labels as *CUSTOM*
            self.aw.qmc.customflavorlabels = self.aw.qmc.flavorlabels

    @pyqtSlot(str)
    def setlabel(self,_:str) -> None:
        x = self.aw.findWidgetsRow(self.flavortable,self.sender(),0)
        if x is not None:
            labeledit = cast(QLineEdit, self.flavortable.cellWidget(x,0))
            self.aw.qmc.flavorlabels[x] = labeledit.text()
            self.aw.qmc.updateFlavorchartLabel(x) # fast incremental redraw

    @pyqtSlot(float)
    def setvalue(self,_:float) -> None:
        x = self.aw.findWidgetsRow(self.flavortable,self.sender(),1)
        if x is not None:
            valueSpinBox = cast(MyQDoubleSpinBox, self.flavortable.cellWidget(x,1))
            self.aw.qmc.flavors[x] = valueSpinBox.value()
            self.aw.qmc.updateFlavorchartValues() # fast incremental redraw
            self.aw.qmc.updateFlavorchartLabel(x) # fast incremental redraw

    @pyqtSlot(float)
    def setcorrection(self,_:float) -> None:
        self.aw.qmc.flavors_total_correction = self.correctionSpinBox.value()
        self.aw.qmc.updateFlavorchartValues() # fast incremental redraw

    @pyqtSlot(int)
    def setdefault(self,_:int) -> None:
        if self.lastcomboboxIndex == self.defaultcombobox.count()-1:
            # store the current labels as *CUSTOM*
            self.aw.qmc.customflavorlabels = self.aw.qmc.flavorlabels
        dindex =  self.defaultcombobox.currentIndex()
        #["","Artisan","SCAA","CQI","SweetMarias","C","E","coffeegeek","Intelligentsia","WCRC"]
        if dindex > 0 or dindex < self.defaultcombobox.count()-1:
            self.aw.qmc.flavorstartangle = 90
        if dindex == 1:
            self.aw.qmc.flavorlabels = list(self.aw.qmc.artisanflavordefaultlabels)
        elif dindex == 2:
            self.aw.qmc.flavorlabels = list(self.aw.qmc.SCAflavordefaultlabels)
        elif dindex == 3:
            self.aw.qmc.flavorlabels = list(self.aw.qmc.SCAAflavordefaultlabels)
        elif dindex == 4:
            self.aw.qmc.flavorlabels = list(self.aw.qmc.CQIflavordefaultlabels)
        elif dindex == 5:
            self.aw.qmc.flavorlabels = list(self.aw.qmc.SweetMariasflavordefaultlabels)
        elif dindex == 6:
            self.aw.qmc.flavorlabels = list(self.aw.qmc.Cflavordefaultlabels)
        elif dindex == 7:
            self.aw.qmc.flavorlabels = list(self.aw.qmc.Eflavordefaultlabels)
        elif dindex == 8:
            self.aw.qmc.flavorlabels = list(self.aw.qmc.coffeegeekflavordefaultlabels)
        elif dindex == 9:
            self.aw.qmc.flavorlabels = list(self.aw.qmc.Intelligentsiaflavordefaultlabels)
        elif dindex == 10:
            self.aw.qmc.flavorlabels = list(self.aw.qmc.IstitutoInternazionaleAssaggiatoriCaffe)
        elif dindex == 11:
            self.aw.qmc.flavorlabels = list(self.aw.qmc.WorldCoffeeRoastingChampionship)
        elif dindex == 12:
            self.aw.qmc.flavorlabels = list(self.aw.qmc.customflavorlabels)
        else:
            return
        self.aw.qmc.flavors = [5.]*len(self.aw.qmc.flavorlabels)
        self.createFlavorTable()
        self.aw.qmc.flavorchart()
        self.lastcomboboxIndex = dindex

    @pyqtSlot()
    @pyqtSlot(bool)
    def addlabel(self,_:bool = False) -> None:
        self.aw.qmc.flavorlabels.append('???')
        self.aw.qmc.flavors.append(5.)
        self.createFlavorTable()
        self.aw.qmc.flavorchart()

    @pyqtSlot()
    @pyqtSlot(bool)
    def poplabel(self,_:bool = False) -> None:
        fn = len(self.aw.qmc.flavors)
        if fn>1:
            self.aw.qmc.flavors = self.aw.qmc.flavors[:(fn-1)]
            self.aw.qmc.flavorlabels = self.aw.qmc.flavorlabels[:(fn -1)]
            self.createFlavorTable()
            self.aw.qmc.flavorchart()

    @pyqtSlot('QCloseEvent')
    def closeEvent(self,_:Optional['QCloseEvent'] = None) -> None:
        self.close()

    def close(self) -> bool:
        settings = QSettings()
        #save window geometry
        settings.setValue('FlavorProperties',self.saveGeometry())
        self.savetable()
        self.aw.qmc.fileDirty()
        if self.aw.qmc.ax1 is not None:
            try:
                self.aw.qmc.fig.delaxes(self.aw.qmc.ax1)
            except Exception: # pylint: disable=broad-except
                pass
        self.aw.qmc.fig.clf()
        self.aw.qmc.clearFlavorChart()
        self.aw.redrawOnResize = True
        self.aw.qmc.redraw(recomputeAllDeltas=False)

        self.aw.updateControlsVisibility()
        self.aw.updateReadingsLCDsVisibility()
        self.aw.updateSlidersVisibility()
        self.aw.update_minieventline_visibility()
        self.aw.updateExtraButtonsVisibility()

        self.accept()
        return True
