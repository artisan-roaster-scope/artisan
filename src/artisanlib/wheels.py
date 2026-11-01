#
# ABOUT
# Wheels dialog
#
# COPYRIGHT (C) 2010-2026 The artisan team represented by
#   Marko Luther <marko.luther@gmx.net> (maintainer) and all contributors
#
# LICENSE
# This program or module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# MAINTAINER
# Marko Luther, 2026
#
# AUTHOR
# Marko Luther, 2023

import platform
from typing import override, cast, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent # pylint: disable=unused-import

from PyQt6.QtCore import Qt, pyqtSlot, QSize
from PyQt6.QtGui import QColor, QIcon, QPalette
from PyQt6.QtWidgets import (QApplication, QLabel, QTableWidget, QPushButton,
    QComboBox, QHBoxLayout, QVBoxLayout, QTableWidgetItem, QDialogButtonBox,
    QDoubleSpinBox, QGroupBox, QLineEdit, QSpinBox, QHeaderView, QToolButton, QWidget)

from artisanlib.util import serialize, getStyleIconPath
from artisanlib.dialogs import ArtisanDialog
from artisanlib.widgets import ArtisanMinorPushButton, MyQSpinBox
from artisanlib.styles import (horizontal_header_style, vertical_header_style, line_edit_style, spin_box_style,
    table_style, artisan_minor_push_button_style, tool_button_icon_style, artisan_dialog_button_style)


class WheelDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False) # overwrite the ArtisanDialog class default here!!
        self.dashboard_was_active_on_open = self.aw.dashboard.dashboard_active()

        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Wheel Graph Editor'))
        #table
        self.datatable = QTableWidget()
        self.createdatatable()
        self.datatable.itemSelectionChanged.connect(self.selectionChanged)
        #table for labels
        self.labeltable = QTableWidget()

        for table in [self.datatable, self.labeltable]:
            table.setStyleSheet(table_style(self.aw.app.darkmode))
            table.setShowGrid(False)

        self.subdialogbuttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close | QDialogButtonBox.StandardButton.RestoreDefaults, Qt.Orientation.Horizontal)

        restoreButton = self.subdialogbuttons.button(QDialogButtonBox.StandardButton.RestoreDefaults)
        if restoreButton is not None:
            self.subdialogbuttons.removeButton(restoreButton)
            restoreButton.clicked.connect(self.resetlabelparents)
            restoreButton.setStyleSheet(artisan_minor_push_button_style(self.aw.app.darkmode))
            self.setButtonTranslations(restoreButton,'Restore Defaults',QApplication.translate('Button','Restore Defaults'))
            restoreButton.setIconSize(QSize(14,14))
            restoreButton.setIcon(QIcon(getStyleIconPath(
                'undo-03-stroke-rounded-dark.svg' if self.aw.app.darkmode else 'undo-03-stroke-rounded-white.svg')))
        closeButton = self.subdialogbuttons.button(QDialogButtonBox.StandardButton.Close)
        if closeButton is not None:
            self.subdialogbuttons.removeButton(closeButton)
            closeButton.clicked.connect(self.closelabels)
            closeButton.setStyleSheet(artisan_minor_push_button_style(self.aw.app.darkmode))
            self.setButtonTranslations(closeButton,'Close',QApplication.translate('Button','Close'))
            closeButton.setIconSize(QSize(14,14))
            closeButton.setIcon(QIcon(getStyleIconPath(
                'cancel-square-stroke-rounded-dark.svg' if self.aw.app.darkmode else 'cancel-square-stroke-rounded-white.svg')))

        subdialogbuttonsHBox = QHBoxLayout()
        subdialogbuttonsHBox.addWidget(restoreButton)
        subdialogbuttonsHBox.addStretch()
        subdialogbuttonsHBox.addWidget(closeButton)

        self.labelwheelx = 0   #index of wheel being edited on labeltable
#        self.hierarchyButton = QPushButton(QApplication.translate("Button","Reverse Hierarchy"))
#        self.hierarchyButton.setToolTip(QApplication.translate("Tooltip","Sets graph hierarchy child->parent instead of parent->child"))
#        self.hierarchyButton.clicked.connect(self.aw.qmc.setWheelHierarchy)
        self.labeltable.setVisible(False)
        self.subdialogbuttons.setVisible(False)
        aspectlabel = QLabel(QApplication.translate('Label','Ratio'))
        self.aspectSpinBox = QDoubleSpinBox()
        self.aspectSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.aspectSpinBox.setStyleSheet(spin_box_style(self.aw.app.darkmode))
        self.aspectSpinBox.setToolTip(QApplication.translate('Tooltip','Aspect Ratio'))
        self.aspectSpinBox.setRange(0.,2.)
        self.aspectSpinBox.setSingleStep(.1)
        self.aspectSpinBox.setValue(self.aw.qmc.wheelaspect)
        self.aspectSpinBox.valueChanged.connect(self.setaspect)
        txtButtonplus = QToolButton()
        txtButtonplus.setText('')
        txtButtonplus.setStyleSheet(tool_button_icon_style(self.aw.app.darkmode, 'a-arrow-up-stroke-rounded-light.svg', 'a-arrow-up-stroke-rounded-dark.svg'))
        txtButtonplus.setMinimumWidth(28)
        txtButtonplus.setMinimumHeight(28)
        txtButtonplus.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        txtButtonplus.setToolTip(QApplication.translate('Tooltip','Increase size of text in all the graph'))
        txtButtonplus.clicked.connect(self.changetext1)
        txtButtonminus = QToolButton()
        txtButtonminus.setText('')
        txtButtonminus.setStyleSheet(tool_button_icon_style(self.aw.app.darkmode, 'a-arrow-down-stroke-rounded-light.svg', 'a-arrow-down-stroke-rounded-dark.svg'))
        txtButtonminus.setMinimumWidth(28)
        txtButtonminus.setMinimumHeight(28)
        txtButtonminus.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        txtButtonminus.setToolTip(QApplication.translate('Tooltip','Decrease size of text in all the graph'))
        txtButtonminus.clicked.connect(self.changetext0)
        edgelabel = QLabel(QApplication.translate('Label','Edge'))
        self.edgeSpinBox = MyQSpinBox()
        self.edgeSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.edgeSpinBox.setStyleSheet(spin_box_style(self.aw.app.darkmode))
        self.edgeSpinBox.setToolTip(QApplication.translate('Tooltip','Decorative edge between wheels'))
        self.edgeSpinBox.setRange(0,5)
        self.edgeSpinBox.setValue(int(round(self.aw.qmc.wheeledge*100)))
        self.edgeSpinBox.valueChanged.connect(self.setedge)
        linewidthlabel = QLabel(QApplication.translate('Label','Line'))
        self.linewidthSpinBox = MyQSpinBox()
        self.linewidthSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.linewidthSpinBox.setStyleSheet(spin_box_style(self.aw.app.darkmode))
        self.linewidthSpinBox.setToolTip(QApplication.translate('Tooltip','Line thickness'))
        self.linewidthSpinBox.setRange(0,20)
        self.linewidthSpinBox.setValue(int(round(self.aw.qmc.wheellinewidth)))
        self.linewidthSpinBox.valueChanged.connect(self.setlinewidth)
        linecolor = ArtisanMinorPushButton(QApplication.translate('Button','Line Color'),
                'palette-stroke-rounded-white.svg',
                'palette-stroke-rounded-dark.svg',
                self.aw.app.darkmode)
        linecolor.setToolTip(QApplication.translate('Tooltip','Line color'))
        linecolor.clicked.connect(self.setlinecolor)
        textcolor = ArtisanMinorPushButton(QApplication.translate('Button','Text Color'),
                'palette-stroke-rounded-white.svg',
                'palette-stroke-rounded-dark.svg',
                self.aw.app.darkmode)
        textcolor.setToolTip(QApplication.translate('Tooltip','Text color'))
        textcolor.clicked.connect(self.settextcolor)
        colorlabel = QLabel(QApplication.translate('Label','Color pattern'))
        self.colorSpinBox = MyQSpinBox()
        self.colorSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.colorSpinBox.setStyleSheet(spin_box_style(self.aw.app.darkmode))
        self.colorSpinBox.setToolTip(QApplication.translate('Tooltip','Apply color pattern to whole graph'))
        self.colorSpinBox.setRange(0,255)
        self.colorSpinBox.setValue(int(round(self.aw.qmc.wheelcolorpattern)))
        self.colorSpinBox.setWrapping(True)
        self.colorSpinBox.valueChanged.connect(self.setcolorpattern)
        addButton = ArtisanMinorPushButton(QApplication.translate('Button','Add'),
            'add-01-stroke-rounded-white.svg',
            'add-01-stroke-rounded-dark.svg',
            self.aw.app.darkmode)
        addButton.setToolTip(QApplication.translate('Tooltip','Add new wheel'))
        addButton.clicked.connect(self.insertwheel)
        addButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.delButton = ArtisanMinorPushButton(QApplication.translate('Button','Delete'),
            'delete-02-stroke-rounded-light.svg',
            'delete-02-stroke-rounded-dark.svg',
            self.aw.app.darkmode)
        self.delButton.setToolTip(QApplication.translate('Tooltip','Add new wheel'))
        self.delButton.clicked.connect(self.delWheel)
        self.delButton.setEnabled(False)
        self.delButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        rotateLeftButton = QToolButton()
        rotateLeftButton.setText('')
        rotateLeftButton.setToolTip(QApplication.translate('Tooltip','Rotate graph 1 degree counter clockwise'))
        rotateLeftButton.setStyleSheet(tool_button_icon_style(self.aw.app.darkmode, 'rotate-left-02-stroke-rounded-light.svg', 'rotate-left-02-stroke-rounded-dark.svg'))
        rotateLeftButton.setMinimumWidth(28)
        rotateLeftButton.setMinimumHeight(28)
        rotateLeftButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        rotateLeftButton.clicked.connect(self.rotatewheels1)

        rotateRightButton = QToolButton()
        rotateRightButton.setText('')
        rotateRightButton.setToolTip(QApplication.translate('Tooltip','Rotate graph 1 degree clockwise'))
        rotateRightButton.setStyleSheet(tool_button_icon_style(self.aw.app.darkmode, 'rotate-right-02-stroke-rounded-light.svg', 'rotate-right-02-stroke-rounded-dark.svg'))
        rotateRightButton.setMinimumWidth(28)
        rotateRightButton.setMinimumHeight(28)
        rotateRightButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        rotateRightButton.clicked.connect(self.rotatewheels0)

        self.main_buttons = QDialogButtonBox()

        saveButton = ArtisanMinorPushButton(QApplication.translate('Button','Save File'),
                'save-stroke-rounded-white.svg',
                'save-stroke-rounded-dark.svg',
                self.aw.app.darkmode)
        saveButton.clicked.connect(self.fileSave)
        saveButton.setToolTip(QApplication.translate('Tooltip','Save graph to a text file.wg'))
#        self.main_buttons.addButton(saveButton,QDialogButtonBox.ButtonRole.ActionRole)

        saveImgButton: QPushButton = ArtisanMinorPushButton(QApplication.translate('Button','Save Image'),
                'save-stroke-rounded-white.svg',
                'save-stroke-rounded-dark.svg',
                self.aw.app.darkmode)
        saveImgButton.setToolTip(QApplication.translate('Tooltip','Save image using current graph size to a png format'))
        #saveImgButton.clicked.connect(self.aw.resizeImg_0_1) # save as PNG (raster)
        saveImgButton.clicked.connect(self.aw.saveVectorGraph_PDF) # save as PDF (vector)
#        self.main_buttons.addButton(saveImgButton,QDialogButtonBox.ButtonRole.ActionRole)

        openButton: QPushButton|None = self.main_buttons.addButton(QDialogButtonBox.StandardButton.Open)
        if openButton is not None:
            self.main_buttons.removeButton(openButton)
            openButton.setToolTip(QApplication.translate('Tooltip','Open wheel graph file'))
            openButton.clicked.connect(self.loadWheel)
            self.setButtonTranslations(openButton,'Open',QApplication.translate('Button','Open'))
            openButton.setIconSize(QSize(14,14))
            openButton.setStyleSheet(artisan_minor_push_button_style(self.aw.app.darkmode))
            openButton.setIcon(QIcon(getStyleIconPath('file-02-stroke-rounded-dark.svg' if self.aw.app.darkmode else 'file-02-stroke-rounded-white.svg')))

        closeButton_main: QPushButton|None = self.main_buttons.addButton(QDialogButtonBox.StandardButton.Close)
        if closeButton_main is not None:
            closeButton_main.setToolTip(QApplication.translate('Tooltip','Sets Wheel graph to view mode'))
            closeButton_main.clicked.connect(self.viewmode)
            self.setButtonTranslations(closeButton_main,'Close',QApplication.translate('Button','Close'))
            # style
            palette = self.palette()
            accent_color = palette.color(QPalette.ColorRole.Accent)
            if not accent_color.isValid() or platform.system() != 'darwin':
                accent_color = QColor('#3979ae')  # Fallback artisan button blue if OS provides none (and on Windows/Linux)
            # Generate math-driven lighting variants for the accent button
            accent_name = accent_color.name()
            accent_hover = accent_color.lighter(115).name() if self.aw.app.darkmode else accent_color.darker(115).name()
            accent_pressed = accent_color.darker(110).name() if self.aw.app.darkmode else accent_color.darker(125).name()
            closeButton_main.setStyleSheet(artisan_dialog_button_style(
                self.aw.app.darkmode,
                accent_name,
                accent_hover,
                accent_pressed))
            closeButton_main.setIcon(QIcon())
            closeButton_main.setFocus()

        self.aw.qmc.drawWheel()
        label2layout = QHBoxLayout()
#        label2layout.addWidget(self.subdialogbuttons)
        label2layout.addLayout(subdialogbuttonsHBox)
        label1layout = QVBoxLayout()
        label1layout.addWidget(self.labeltable)
        label1layout.addLayout(label2layout)
        self.labelGroupLayout = QGroupBox(QApplication.translate('GroupBox','Label Properties'))
        self.labelGroupLayout.setLayout(label1layout)
        self.labelGroupLayout.setVisible(False)
        buttonlayout = QHBoxLayout()
        buttonlayout.addWidget(saveButton)
        buttonlayout.addWidget(saveImgButton)
        buttonlayout.addStretch()
        buttonlayout.addWidget(openButton)
        buttonlayout.addStretch()
        buttonlayout.addWidget(self.main_buttons)
        configlayout =  QHBoxLayout()
        configlayout.addWidget(colorlabel)
        configlayout.addWidget(self.colorSpinBox)
        configlayout.addWidget(aspectlabel)
        configlayout.addWidget(self.aspectSpinBox)
        configlayout.addWidget(edgelabel)
        configlayout.addWidget(self.edgeSpinBox)
        configlayout.addWidget(linewidthlabel)
        configlayout.addWidget(self.linewidthSpinBox)
        configlayout.addWidget(linecolor)
        configlayout.addWidget(textcolor)
        controlLayout = QHBoxLayout()
        controlLayout.addStretch()
        controlLayout.addWidget(rotateLeftButton)
        controlLayout.addWidget(rotateRightButton)
        controlLayout.addSpacing(10)
        controlLayout.addStretch()
        controlLayout.addWidget(addButton)
        controlLayout.addWidget(self.delButton)
        controlLayout.addSpacing(10)
        controlLayout.addStretch()
        controlLayout.addWidget(txtButtonplus)
        controlLayout.addWidget(txtButtonminus)
#        controlLayout.addWidget(self.hierarchyButton)
        controlLayout.addStretch()
        mainlayout = QVBoxLayout()
        mainlayout.addWidget(self.datatable)
        mainlayout.addWidget(self.labelGroupLayout)
        mainlayout.addLayout(controlLayout)
        mainlayout.addLayout(configlayout)
        mainlayout.addLayout(buttonlayout)
        self.setLayout(mainlayout)

    def updateDelButtonState(self) -> None:
        if len(self.datatable.selectedRanges()) > 0:
            self.delButton.setEnabled(True)
            self.delButton.setIcon(QIcon(getStyleIconPath('delete-02-stroke-rounded-white.svg')))
        else:
            self.delButton.setEnabled(False)
            self.delButton.setIcon(QIcon(getStyleIconPath('delete-02-stroke-rounded-dark.svg' if self.aw.app.darkmode else 'delete-02-stroke-rounded.svg')))

    @pyqtSlot()
    def selectionChanged(self) -> None:
        self.updateDelButtonState()

    @override
    def close(self) -> bool:
        self.aw.qmc.connectWheel()
        self.aw.qmc.drawWheel()
        self.accept()
        return True

    #creates config table for wheel with index x
    @pyqtSlot(bool)
    def createlabeltable(self, _:bool = False) -> None:
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),1)
        if x is not None:
            self.createlabeltablex(x)

    def createlabeltablex(self, x:int) -> None:
        self.labelwheelx = x                    #wheel being edited
        self.labelGroupLayout.setVisible(True)
        self.labeltable.setVisible(True)
        self.subdialogbuttons.setVisible(True)

        nlabels = len(self.aw.qmc.wheelnames[x])
        # self.labeltable.clear() # this crashes Ubuntu 16.04
        self.labeltable.clearSelection() # this seems to work also for Ubuntu 16.04

        if nlabels:
            self.labeltable.setRowCount(nlabels)
            self.labeltable.setColumnCount(5)
            self.labeltable.setHorizontalHeaderLabels([QApplication.translate('Table','Label'),
                                                       QApplication.translate('Table','Parent'),
                                                       QApplication.translate('Table','Width'),
                                                       QApplication.translate('Table','Color'),
                                                       QApplication.translate('Table','Opaqueness')])
            self.labeltable.setAlternatingRowColors(True)
            self.labeltable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.labeltable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.labeltable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.labeltable.setShowGrid(True)
            vheader: QHeaderView|None = self.labeltable.verticalHeader()
            if vheader is not None:
                vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
                vheader.setStyleSheet(vertical_header_style(self.aw.app.darkmode))
                vheader.setDefaultAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            horizontal_header: QHeaderView|None = self.labeltable.horizontalHeader()
            if horizontal_header is not None:
                horizontal_header.setStyleSheet(horizontal_header_style(self.aw.app.darkmode))
                horizontal_header.setSectionsClickable(False)
                horizontal_header.setHighlightSections(False)
                horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

            #populate table
            for i in range(nlabels):
                label = QTableWidgetItem(self.aw.qmc.wheelnames[x][i])
                parentComboBox =  QComboBox()
                if x > 0:
                    items = self.aw.qmc.wheelnames[x-1][:]
                    items.insert(0,'')
                    parentComboBox.addItems(items)
                    if self.aw.qmc.wheellabelparent[x][i]:
                        parentComboBox.setCurrentIndex(self.aw.qmc.wheellabelparent[x][i])
                else:
                    parentComboBox.addItems([])
                parentComboBox.currentIndexChanged.connect(self.setwheelchild)
                labelwidthSpinBox = QDoubleSpinBox()
                labelwidthSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
                labelwidthSpinBox.setStyleSheet(spin_box_style(self.aw.app.darkmode))
                labelwidthSpinBox.setRange(1.,100.)
                labelwidthSpinBox.setValue(self.aw.qmc.segmentlengths[x][i])
                labelwidthSpinBox.setSuffix('%')
                labelwidthSpinBox.valueChanged.connect(self.setlabelwidth)
                colorButton = ArtisanMinorPushButton('Set Color',
                    'palette-stroke-rounded-white.svg',
                    'palette-stroke-rounded-dark.svg',
                    self.aw.app.darkmode)
                colorButton.clicked.connect(self.setsegmentcolor)
                colorContainer = QWidget()
                colorLayout = QHBoxLayout(colorContainer)
                colorLayout.setContentsMargins(0, 0, 0, 0)
                colorLayout.addWidget(colorButton, alignment=Qt.AlignmentFlag.AlignCenter)
                alphaSpinBox = MyQSpinBox()
                alphaSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
                alphaSpinBox.setStyleSheet(spin_box_style(self.aw.app.darkmode))
                alphaSpinBox.setRange(0,10)
                alphaSpinBox.setValue(int(round(self.aw.qmc.segmentsalpha[x][i]*10)))
                alphaSpinBox.valueChanged.connect(self.setsegmentalpha)
                #add widgets to the table
                self.labeltable.setItem(i,0,label)
                self.labeltable.setCellWidget(i,1,parentComboBox)
                self.labeltable.setCellWidget(i,2,labelwidthSpinBox)
                self.labeltable.setCellWidget(i,3,colorContainer)
                self.labeltable.setCellWidget(i,4,alphaSpinBox)

    @pyqtSlot(bool)
    def setsegmentcolor(self, _:bool = False) -> None:
        i = self.aw.findWidgetsRow(self.labeltable,self.sender(),3)
        if i is not None:
            x = self.labelwheelx
            colorf = self.aw.colordialog(QColor(self.aw.qmc.wheelcolor[x][i]))
            if colorf.isValid():
                colorname = str(colorf.name())
                self.aw.qmc.wheelcolor[x][i] = colorname      #add new color to label
                self.createdatatable()                           #update main table with label names (label::color)
                self.aw.qmc.drawWheel()

    #sets a uniform color in wheel
    @pyqtSlot(bool)
    def setwheelcolor(self, _:bool = False) -> None:
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),6)
        if x is not None:
            colorf = self.aw.colordialog(QColor(self.aw.qmc.wheelcolor[x][0]))
            if colorf.isValid():
                colorname = str(colorf.name())
                for i in range(len(self.aw.qmc.wheelcolor[x])):
                    self.aw.qmc.wheelcolor[x][i] =  colorname
            self.createdatatable()
            self.aw.qmc.drawWheel()

    #sets color pattern (many colors) in wheel
    @pyqtSlot(int)
    def setwheelcolorpattern(self, _:int) -> None:
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),7)
        if x is not None:
            wsb = cast(QSpinBox, self.datatable.cellWidget(x,7))
            wpattern = wsb.value()
            wlen = len(self.aw.qmc.wheelcolor[x])
            for i in range(wlen):
                color = QColor()
                color.setHsv(int(round((360/wlen)*i*wpattern)),255,255,255)
                self.aw.qmc.wheelcolor[x][i] = str(color.name())
            self.aw.qmc.drawWheel()

    #sets color pattern (many colors) for whole graph
    @pyqtSlot(int)
    def setcolorpattern(self, _:int) -> None:
        self.aw.qmc.wheelcolorpattern = self.colorSpinBox.value()
        if self.aw.qmc.wheelcolorpattern:
            for x, __ in enumerate(self.aw.qmc.wheelcolor):
                wlen = len(self.aw.qmc.wheelcolor[x])
                for i in range(wlen):
                    color = QColor()
                    color.setHsv(int(round((360/wlen)*i*self.aw.qmc.wheelcolorpattern)),255,255,255)
                    self.aw.qmc.wheelcolor[x][i] = str(color.name())
            self.aw.qmc.drawWheel()

    @pyqtSlot(int)
    def setsegmentalpha(self, z:int) -> None:
        u = self.aw.findWidgetsRow(self.labeltable,self.sender(),4)
        if u is not None:
            x = self.labelwheelx
            self.aw.qmc.segmentsalpha[x][u] = float(z/10.)
            self.aw.qmc.drawWheel()

    #rotate whole graph
    @pyqtSlot(bool)
    def rotatewheels1(self, _:bool = False) -> None:
        for i, __ in enumerate(self.aw.qmc.startangle):
            self.aw.qmc.startangle[i] += 1
        self.aw.qmc.drawWheel()

    @pyqtSlot(bool)
    def rotatewheels0(self, _:bool = False) -> None:
        for i, __ in enumerate(self.aw.qmc.startangle):
            self.aw.qmc.startangle[i] -= 1
        self.aw.qmc.drawWheel()

    #z= new width%, x= wheel number index, u = index of segment in the wheel
    @pyqtSlot(float)
    def setlabelwidth(self, z:float) -> None:
        u = self.aw.findWidgetsRow(self.labeltable,self.sender(),2)
        if u is not None:
            x = self.labelwheelx
            newwidth = z
            oldwidth = self.aw.qmc.segmentlengths[x][u]
            diff = newwidth - oldwidth
            ll = len(self.aw.qmc.segmentlengths[x])
            for i in range(ll):
                if i != u:
                    if diff > 0:
                        self.aw.qmc.segmentlengths[x][i] -= abs(float(diff))/(ll-1)
                    else:
                        self.aw.qmc.segmentlengths[x][i] += abs(float(diff))/(ll-1)
            self.aw.qmc.segmentlengths[x][u] = newwidth
            self.aw.qmc.drawWheel()

    #input: z = index of parent in previous wheel; x = wheel number; i = index of element in wheel
    @pyqtSlot(int)
    def setwheelchild(self, z:int) -> None:
        i = self.aw.findWidgetsRow(self.labeltable,self.sender(),1)
        if i is not None:
            self.aw.qmc.setwheelchild(z,self.labelwheelx,i)
            self.aw.qmc.drawWheel()
            self.createdatatable() #update data table

    #deletes parent-child relation in a wheel. It obtains the wheel index by self.labelwheelx
    @pyqtSlot(bool)
    def resetlabelparents(self, _:bool = False) -> None:
        x = self.labelwheelx
        nsegments = len(self.aw.qmc.wheellabelparent[x])
        for i in range(nsegments):
            self.aw.qmc.wheellabelparent[x][i] = 0
            self.aw.qmc.segmentlengths[x][i] = 100./nsegments
        self.aw.qmc.drawWheel()
        self.createlabeltablex(x)

    @pyqtSlot(float)
    def setaspect(self, _:float) -> None:
        self.aw.qmc.wheelaspect = self.aspectSpinBox.value()
        self.aw.qmc.drawWheel()

    #adjust decorative edge between wheels
    @pyqtSlot(int)
    def setedge(self, _:int) -> None:
        self.aw.qmc.wheeledge = float(self.edgeSpinBox.value())/100.
        self.aw.qmc.drawWheel()

    #adjusts line thickness
    @pyqtSlot(int)
    def setlinewidth(self, _:int) -> None:
        self.aw.qmc.wheellinewidth = self.linewidthSpinBox.value()
        self.aw.qmc.drawWheel()

    #sets line color
    @pyqtSlot(bool)
    def setlinecolor(self, _:bool = False) -> None:
        colorf = self.aw.colordialog(QColor(self.aw.qmc.wheellinecolor))
        if colorf.isValid():
            colorname = str(colorf.name())
            #self.aw.qmc.wheellinealpha = colorf.alphaF()
            self.aw.qmc.wheellinecolor = colorname      #add new color to label
            self.aw.qmc.drawWheel()

    #sets text color
    @pyqtSlot(bool)
    def settextcolor(self, _:bool = False) -> None:
        colorf = self.aw.colordialog(QColor(self.aw.qmc.wheeltextcolor))
        if colorf.isValid():
            colorname = str(colorf.name())
            #self.aw.qmc.wheeltextalpha = colorf.alphaF()
            self.aw.qmc.wheeltextcolor = colorname      #add new color to label
            self.aw.qmc.drawWheel()

    #makes not visible the wheel config table
    @pyqtSlot()
    def closelabels(self) -> None:
        self.labelGroupLayout.setVisible(False)
        self.labeltable.setVisible(False)
#        self.labelCloseButton.setVisible(False)
#        self.labelResetButton.setVisible(False)
        self.subdialogbuttons.setVisible(False)

    #creates graph table
    def createdatatable(self) -> None:
        ndata = len(self.aw.qmc.wheelnames)

        # self.datatable.clear() # this crashes Ubuntu 16.04
#        if ndata != 0:
#            self.datatable.clearContents() # this crashes Ubuntu 16.04 if device table is empty and also sometimes else
        self.datatable.clearSelection() # this seems to work also for Ubuntu 16.04

        self.datatable.setRowCount(ndata)
        self.datatable.setColumnCount(8)
        self.datatable.setHorizontalHeaderLabels([QApplication.translate('Table','Edit Labels'),
                                                  QApplication.translate('Table','Properties'),
                                                  QApplication.translate('Table','Radius'),
                                                  QApplication.translate('Table','Starting angle'),
                                                  QApplication.translate('Table','Projection'),
                                                  QApplication.translate('Table','Text Size'),
                                                  QApplication.translate('Table','Color'),
                                                  QApplication.translate('Table','Color Pattern')])
        self.datatable.setAlternatingRowColors(True)
        self.datatable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.datatable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.datatable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.datatable.setShowGrid(True)
        vheader: QHeaderView|None = self.datatable.verticalHeader()
        if vheader is not None:
            vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            vheader.setStyleSheet(vertical_header_style(self.aw.app.darkmode))
            vheader.setDefaultAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        horizontal_header: QHeaderView|None = self.datatable.horizontalHeader()
        if horizontal_header is not None:
            horizontal_header.setStyleSheet(horizontal_header_style(self.aw.app.darkmode))
            horizontal_header.setSectionsClickable(False)
            horizontal_header.setHighlightSections(False)
            horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        #populate table
        for i in range(ndata):
            labelsedit = QLineEdit(str(','.join(self.aw.qmc.wheelnames[i])))
            labelsedit.setStyleSheet(line_edit_style(self.aw.app.darkmode))
            labelsedit.editingFinished.connect(self.updatelabels)
            setButton = ArtisanMinorPushButton(QApplication.translate('Button','Properties'),
                'setting-07-stroke-rounded-white.svg',
                'setting-07-stroke-rounded-dark.svg',
                self.aw.app.darkmode)
            setButton.clicked.connect(self.createlabeltable)
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.addWidget(setButton, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            widthSpinBox = QDoubleSpinBox()
            widthSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
            widthSpinBox.setStyleSheet(spin_box_style(self.aw.app.darkmode))
            widthSpinBox.setRange(1.,100.)
            widthSpinBox.setValue(self.aw.qmc.wradii[i])
            widthSpinBox.setSuffix('%')
            widthSpinBox.valueChanged.connect(self.setwidth)
            angleSpinBox = MyQSpinBox()
            angleSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
            angleSpinBox.setStyleSheet(spin_box_style(self.aw.app.darkmode))
            angleSpinBox.setSuffix(QApplication.translate('Label',' dg'))
            angleSpinBox.setRange(0,359)
            angleSpinBox.setWrapping(True)
            angleSpinBox.setValue(int(round(self.aw.qmc.startangle[i])))
            angleSpinBox.valueChanged.connect(self.setangle)
            projectionComboBox =  QComboBox()
            projectionComboBox.addItems([QApplication.translate('ComboBox','Flat'),
                                         QApplication.translate('ComboBox','Perpendicular'),
                                         QApplication.translate('ComboBox','Radial')])
            projectionComboBox.setCurrentIndex(self.aw.qmc.projection[i])
            projectionComboBox.currentIndexChanged.connect(self.setprojection)
            txtSpinBox = MyQSpinBox()
            txtSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
            txtSpinBox.setStyleSheet(spin_box_style(self.aw.app.darkmode))
            txtSpinBox.setRange(1,30)
            txtSpinBox.setValue(int(round(self.aw.qmc.wheeltextsize[i])))
            txtSpinBox.valueChanged.connect(self.setTextsizeX)
            colorButton = ArtisanMinorPushButton(QApplication.translate('Button','Set Color'),
                    'palette-stroke-rounded-white.svg',
                    'palette-stroke-rounded-dark.svg',
                    self.aw.app.darkmode)
            colorButton.clicked.connect(self.setwheelcolor)
            colorContainer = QWidget()
            colorLayout = QHBoxLayout(colorContainer)
            colorLayout.setContentsMargins(0, 0, 0, 0)
            colorLayout.addWidget(colorButton, alignment=Qt.AlignmentFlag.AlignCenter)
            colorSpinBox = MyQSpinBox()
            colorSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
            colorSpinBox.setStyleSheet(spin_box_style(self.aw.app.darkmode))
            colorSpinBox.setRange(0,255)
            colorSpinBox.setWrapping(True)
            colorSpinBox.valueChanged.connect(self.setwheelcolorpattern)
            #add widgets to the table
            self.datatable.setCellWidget(i,0,labelsedit)
            self.datatable.setCellWidget(i,1,container)
            self.datatable.setCellWidget(i,2,widthSpinBox)
            self.datatable.setCellWidget(i,3,angleSpinBox)
            self.datatable.setCellWidget(i,4,projectionComboBox)
            self.datatable.setCellWidget(i,5,txtSpinBox)
            self.datatable.setCellWidget(i,6,colorContainer)
            self.datatable.setCellWidget(i,7,colorSpinBox)


    #reads label edit box for wheel with index x, and updates labels
    @pyqtSlot()
    def updatelabels(self) -> None:
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),0)
        if x is not None:
            labelsedit = cast(QLineEdit, self.datatable.cellWidget(x,0))
            text  = str(labelsedit.text())
            if '\\n' in text:              #make multiple line text if "\n" found in label string
                parts = text.split('\\n')
                text = chr(10).join(parts)
            newwheellabels = text.strip().split(',')
            newnlabels = len(newwheellabels)
            oldnlabels = len(self.aw.qmc.wheelnames[x])
            #adjust segments len and alpha for each wheel if number of labels changed
            if oldnlabels != newnlabels:
                self.aw.qmc.segmentlengths[x] = [100./newnlabels]*newnlabels
                self.aw.qmc.segmentsalpha[x] = [.3]*newnlabels
                self.aw.qmc.wheellabelparent[x] = [0]*newnlabels
                self.aw.qmc.wheelcolor[x] = [self.aw.qmc.wheelcolor[x][0]]*newnlabels
            self.aw.qmc.wheelnames[x] = newwheellabels[:]
            self.aw.qmc.drawWheel()

    #sets radii for a wheel
    @pyqtSlot(float)
    def setwidth(self, _:float) -> None:
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),2)
        if x is not None:
            widthSpinBox = cast(QDoubleSpinBox, self.datatable.cellWidget(x,2))
            newwidth = widthSpinBox.value()
            oldwidth = self.aw.qmc.wradii[x]
            diff = newwidth - oldwidth
            ll = len(self.aw.qmc.wradii)
            for i in range(ll):
                if i != x:
                    if diff > 0:
                        self.aw.qmc.wradii[i] -= abs(float(diff))/(ll-1)
                    else:
                        self.aw.qmc.wradii[i] += abs(float(diff))/(ll-1)
            self.aw.qmc.wradii[x] = newwidth
            #Need 100.0% coverage. Correct for numerical floating point rounding errors:
            count = 0.
            for wrad in self.aw.qmc.wradii:
                count += wrad
            diff = 100. - count
            if diff  != 0.:
                if diff > 0.000:  #if count smaller
                    self.aw.qmc.wradii[x] += abs(diff)
                else:
                    self.aw.qmc.wradii[x] -= abs(diff)
            self.aw.qmc.drawWheel()

    #sets starting angle (rotation) for a wheel with index x
    @pyqtSlot(int)
    def setangle(self, _:int) -> None:
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),3)
        if x is not None:
            angleSpinBox = cast(QSpinBox, self.datatable.cellWidget(x,3))
            self.aw.qmc.startangle[x] = angleSpinBox.value()
            self.aw.qmc.drawWheel()

    #sets text projection style for a wheel with index x
    @pyqtSlot(int)
    def setprojection(self, _:int) -> None:
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),4)
        if x is not None:
            projectionComboBox = cast(QComboBox, self.datatable.cellWidget(x,4))
            self.aw.qmc.projection[x] = projectionComboBox.currentIndex()
            self.aw.qmc.drawWheel()

    #changes text size in wheel with index x
    @pyqtSlot(int)
    def setTextsizeX(self, _:int) -> None:
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),5)
        if x is not None:
            txtSpinBox = cast(QSpinBox, self.datatable.cellWidget(x,5))
            self.aw.qmc.wheeltextsize[x] = txtSpinBox.value()
            self.aw.qmc.drawWheel()

    #changes size of text in whole graph
    @pyqtSlot(bool)
    def changetext1(self, _:bool = False) -> None:
        for i, __ in enumerate(self.aw.qmc.wheeltextsize):
            self.aw.qmc.wheeltextsize[i] += 1
        self.aw.qmc.drawWheel()

    @pyqtSlot(bool)
    def changetext0(self, _:bool = False) -> None:
        for i, __ in enumerate(self.aw.qmc.wheeltextsize):
            self.aw.qmc.wheeltextsize[i] -= 1
        self.aw.qmc.drawWheel()

    @pyqtSlot(bool)
    def delWheel(self, _:bool = False) -> None:
        selected = self.datatable.selectedRanges()
        if len(selected) > 0:
            x = selected[0].topRow()
            if x >= 0:
                #correct raius of other wheels (to use 100% coverage)
                width = self.aw.qmc.wradii[x]
                ll = len(self.aw.qmc.wradii)
                for i in range(ll):
                    if i != x:
                        self.aw.qmc.wradii[i] += float(width)/(ll-1)
                self.aw.qmc.wheelnames.pop(x)
                self.aw.qmc.wradii.pop(x)
                self.aw.qmc.startangle.pop(x)
                self.aw.qmc.projection.pop(x)
                self.aw.qmc.wheeltextsize.pop(x)
                self.aw.qmc.segmentlengths.pop(x)
                self.aw.qmc.segmentsalpha.pop(x)
                self.aw.qmc.wheellabelparent.pop(x)
                self.aw.qmc.wheelcolor.pop(x)
                self.createdatatable()
                self.aw.qmc.drawWheel()
                self.updateDelButtonState()

    #adds new top wheel
    @pyqtSlot(bool)
    def insertwheel(self, _:bool = False) -> None:
        ndata = len(self.aw.qmc.wradii)
        if ndata:
            count = 0.
            for i in range(ndata):
                self.aw.qmc.wradii[i] = 100./(ndata+1)
                count += self.aw.qmc.wradii[i]
            self.aw.qmc.wradii.append(100.-count)
        else:
            self.aw.qmc.wradii.append(100.)
        #find number of labels of most outer wheel (last)
        if len(self.aw.qmc.wheelnames):
            nwheels = len(self.aw.qmc.wheelnames[-1])
        else:                                       #if no wheels
            nwheels = 3
        wn:list[str] = []
        sl:list[float] = []
        sa:list[float] = []
        wlp:list[int] = []
        co:list[str] = []
        for i in range(nwheels+1):
            wn.append(f'W{len(self.aw.qmc.wheelnames)+1} {i+1}')
            sl.append(100./(nwheels+1))
            sa.append(.3)
            wlp.append(0)
            color = QColor()
            color.setHsv(int(round((360/(nwheels+1))*i)),255,255,255)
            co.append(str(color.name()))
        self.aw.qmc.wheelnames.append(wn)
        self.aw.qmc.segmentlengths.append(sl)
        self.aw.qmc.segmentsalpha.append(sa)
        self.aw.qmc.wheellabelparent.append(wlp)
        self.aw.qmc.startangle.append(0)
        self.aw.qmc.projection.append(2)
        self.aw.qmc.wheeltextsize.append(10)
        self.aw.qmc.wheelcolor.append(co)
        self.createdatatable()
        self.aw.qmc.drawWheel()

    @pyqtSlot(bool)
    def fileSave(self, _:bool = False) -> None:
        try:
            filename = self.aw.ArtisanSaveFileDialog(msg=QApplication.translate('Message','Save Wheel graph'),ext='*.wg')
            if filename:
                #write
                serialize(filename, cast(dict[str, Any], self.aw.getWheelGraph()))
                self.aw.sendmessage(QApplication.translate('Message','Wheel Graph saved'))
        except OSError as e:
            self.aw.qmc.adderror((QApplication.translate('Error Message','IO Error:') + ' Wheel graph filesave(): {0}').format(str(e)))

    @pyqtSlot(bool)
    def loadWheel(self, _:bool = False) -> None:
        filename = self.aw.ArtisanOpenFileDialog(msg=QApplication.translate('Message','Open Wheel Graph'),path = self.aw.getDefaultPath(),ext='*.wg')
        if filename:
            self.aw.loadWheel(filename)
            self.aw.wheelpath = filename
            self.createdatatable()
            self.aw.qmc.drawWheel()

    @pyqtSlot('QCloseEvent')
    @override
    def closeEvent(self, a0:'QCloseEvent|None' = None) -> None:
        del a0
        self.viewmode(False)

    @pyqtSlot(bool)
    def viewmode(self, _:bool = False) -> None:
        self.close()
