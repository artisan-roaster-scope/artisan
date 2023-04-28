#
# ABOUT
# Artisan Wheels Dialog

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

from artisanlib.dialogs import ArtisanDialog

from matplotlib import rcParams

try:
    from PyQt6.QtCore import Qt, pyqtSlot # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QColor # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QLabel, QTableWidget, QPushButton, # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QTableWidgetItem, QDialogButtonBox, # @UnusedImport @Reimport  @UnresolvedImport
        QDoubleSpinBox, QGroupBox, QLineEdit, QSpinBox, QHeaderView) # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import Qt, pyqtSlot # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QColor # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QLabel, QTableWidget, QPushButton, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QTableWidgetItem, QDialogButtonBox, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QDoubleSpinBox, QGroupBox, QLineEdit, QSpinBox, QHeaderView) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


class WheelDlg(ArtisanDialog):
    def __init__(self, parent, aw) -> None:
        super().__init__(parent, aw)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False) # overwrite the ArtisanDialog class default here!!

        rcParams['path.effects'] = []

        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Wheel Graph Editor'))
        #table
        self.datatable = QTableWidget()
        self.createdatatable()
        #table for labels
        self.labeltable = QTableWidget()

        self.subdialogbuttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close | QDialogButtonBox.StandardButton.RestoreDefaults, Qt.Orientation.Horizontal)
        self.setButtonTranslations(self.subdialogbuttons.button(QDialogButtonBox.StandardButton.RestoreDefaults),'Restore Defaults',QApplication.translate('Button','Restore Defaults'))
        self.setButtonTranslations(self.subdialogbuttons.button(QDialogButtonBox.StandardButton.Close),'Close',QApplication.translate('Button','Close'))

        self.subdialogbuttons.rejected.connect(self.closelabels)
        self.subdialogbuttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.resetlabelparents)

        self.labelwheelx = 0   #index of wheel being edited on labeltable
#        self.hierarchyButton = QPushButton(QApplication.translate("Button","Reverse Hierarchy"))
#        self.hierarchyButton.setToolTip(QApplication.translate("Tooltip","Sets graph hierarchy child->parent instead of parent->child"))
#        self.hierarchyButton.clicked.connect(self.aw.qmc.setWheelHierarchy)
        self.labeltable.setVisible(False)
        self.subdialogbuttons.setVisible(False)
        aspectlabel = QLabel(QApplication.translate('Label','Ratio'))
        self.aspectSpinBox = QDoubleSpinBox()
        self.aspectSpinBox.setToolTip(QApplication.translate('Tooltip','Aspect Ratio'))
        self.aspectSpinBox.setRange(0.,2.)
        self.aspectSpinBox.setSingleStep(.1)
        self.aspectSpinBox.setValue(self.aw.qmc.wheelaspect)
        self.aspectSpinBox.valueChanged.connect(self.setaspect)
        txtlabel = QLabel(QApplication.translate('Label','Text'))
        txtButtonplus = QPushButton('+')
        txtButtonplus.setToolTip(QApplication.translate('Tooltip','Increase size of text in all the graph'))
        txtButtonplus.clicked.connect(self.changetext1)
        txtButtonminus = QPushButton('-')
        txtButtonminus.setToolTip(QApplication.translate('Tooltip','Decrease size of text in all the graph'))
        txtButtonminus.clicked.connect(self.changetext0)
        edgelabel = QLabel(QApplication.translate('Label','Edge'))
        self.edgeSpinBox = QSpinBox()
        self.edgeSpinBox.setToolTip(QApplication.translate('Tooltip','Decorative edge between wheels'))
        self.edgeSpinBox.setRange(0,5)
        self.edgeSpinBox.setValue(int(round(self.aw.qmc.wheeledge*100)))
        self.edgeSpinBox.valueChanged.connect(self.setedge)
        linewidthlabel = QLabel(QApplication.translate('Label','Line'))
        self.linewidthSpinBox = QSpinBox()
        self.linewidthSpinBox.setToolTip(QApplication.translate('Tooltip','Line thickness'))
        self.linewidthSpinBox.setRange(0,20)
        self.linewidthSpinBox.setValue(int(round(self.aw.qmc.wheellinewidth)))
        self.linewidthSpinBox.valueChanged.connect(self.setlinewidth)
        linecolor = QPushButton(QApplication.translate('Button','Line Color'))
        linecolor.setToolTip(QApplication.translate('Tooltip','Line color'))
        linecolor.clicked.connect(self.setlinecolor)
        textcolor = QPushButton(QApplication.translate('Button','Text Color'))
        textcolor.setToolTip(QApplication.translate('Tooltip','Text color'))
        textcolor.clicked.connect(self.settextcolor)
        colorlabel = QLabel(QApplication.translate('Label','Color pattern'))
        self.colorSpinBox = QSpinBox()
        self.colorSpinBox.setToolTip(QApplication.translate('Tooltip','Apply color pattern to whole graph'))
        self.colorSpinBox.setRange(0,255)
        self.colorSpinBox.setValue(int(round(self.aw.qmc.wheelcolorpattern)))
        self.colorSpinBox.setWrapping(True)
        self.colorSpinBox.valueChanged.connect(self.setcolorpattern)
        addButton = QPushButton(QApplication.translate('Button','Add'))
        addButton.setToolTip(QApplication.translate('Tooltip','Add new wheel'))
        addButton.clicked.connect(self.insertwheel)
        rotateLeftButton = QPushButton('<')
        rotateLeftButton.setToolTip(QApplication.translate('Tooltip','Rotate graph 1 degree counter clockwise'))
        rotateLeftButton.clicked.connect(self.rotatewheels1)
        rotateRightButton = QPushButton('>')
        rotateRightButton.setToolTip(QApplication.translate('Tooltip','Rotate graph 1 degree clockwise'))
        rotateRightButton.clicked.connect(self.rotatewheels0)

        self.main_buttons = QDialogButtonBox()

        saveButton = QPushButton(QApplication.translate('Button','Save File'))
        saveButton.clicked.connect(self.fileSave)
        saveButton.setToolTip(QApplication.translate('Tooltip','Save graph to a text file.wg'))
        self.main_buttons.addButton(saveButton,QDialogButtonBox.ButtonRole.ActionRole)

        saveImgButton = QPushButton(QApplication.translate('Button','Save Img'))
        saveImgButton.setToolTip(QApplication.translate('Tooltip','Save image using current graph size to a png format'))
        #saveImgButton.clicked.connect(self.aw.resizeImg_0_1) # save as PNG (raster)
        saveImgButton.clicked.connect(self.aw.saveVectorGraph_PDF) # save as PDF (vector)
        self.main_buttons.addButton(saveImgButton,QDialogButtonBox.ButtonRole.ActionRole)

        openButton = self.main_buttons.addButton(QDialogButtonBox.StandardButton.Open)
        openButton.setToolTip(QApplication.translate('Tooltip','open wheel graph file'))
        openButton.clicked.connect(self.loadWheel)

        viewModeButton = self.main_buttons.addButton(QDialogButtonBox.StandardButton.Close)
        viewModeButton.setToolTip(QApplication.translate('Tooltip','Sets Wheel graph to view mode'))
        viewModeButton.clicked.connect(self.viewmode)

        if self.aw.locale_str not in self.aw.qtbase_locales:
            self.main_buttons.button(QDialogButtonBox.StandardButton.Close).setText(QApplication.translate('Button','Close'))
            self.main_buttons.button(QDialogButtonBox.StandardButton.Open).setText(QApplication.translate('Button','Open'))

        self.aw.qmc.drawWheel()
        label1layout = QVBoxLayout()
        label2layout = QHBoxLayout()
        label1layout.addWidget(self.labeltable)
        label2layout.addWidget(self.subdialogbuttons)
        label1layout.addLayout(label2layout)
        self.labelGroupLayout = QGroupBox(QApplication.translate('GroupBox','Label Properties'))
        self.labelGroupLayout.setLayout(label1layout)
        self.labelGroupLayout.setVisible(False)
        buttonlayout = QHBoxLayout()
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
        configlayout.addWidget(txtlabel)
        configlayout.addWidget(txtButtonplus)
        configlayout.addWidget(txtButtonminus)
        controlLayout = QHBoxLayout()
        controlLayout.addWidget(addButton)
        controlLayout.addWidget(rotateLeftButton)
        controlLayout.addWidget(rotateRightButton)
#        controlLayout.addWidget(self.hierarchyButton)
        mainlayout = QVBoxLayout()
        mainlayout.addWidget(self.datatable)
        mainlayout.addWidget(self.labelGroupLayout)
        mainlayout.addLayout(controlLayout)
        mainlayout.addLayout(configlayout)
        mainlayout.addLayout(buttonlayout)
        self.setLayout(mainlayout)

    def close(self):
        self.accept()

    #creates config table for wheel with index x
    @pyqtSlot(bool)
    def createlabeltable(self,_):
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),3)
        if x is not None:
            self.createlabeltablex(x)

    def createlabeltablex(self,x):
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
            self.labeltable.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
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
                labelwidthSpinBox.setRange(1.,100.)
                labelwidthSpinBox.setValue(self.aw.qmc.segmentlengths[x][i])
                labelwidthSpinBox.setSuffix('%')
                labelwidthSpinBox.valueChanged.connect(self.setlabelwidth)
                colorButton = QPushButton('Set Color')
                colorButton.clicked.connect(self.setsegmentcolor)
                alphaSpinBox = QSpinBox()
                alphaSpinBox.setRange(0,10)
                alphaSpinBox.setValue(int(round(self.aw.qmc.segmentsalpha[x][i]*10)))
                alphaSpinBox.valueChanged.connect(self.setsegmentalpha)
                #add widgets to the table
                self.labeltable.setItem(i,0,label)
                self.labeltable.setCellWidget(i,1,parentComboBox)
                self.labeltable.setCellWidget(i,2,labelwidthSpinBox)
                self.labeltable.setCellWidget(i,3,colorButton)
                self.labeltable.setCellWidget(i,4,alphaSpinBox)

    @pyqtSlot(bool)
    def setsegmentcolor(self,_):
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
    def setwheelcolor(self,_):
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),8)
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
    def setwheelcolorpattern(self,_):
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),9)
        if x is not None:
            wsb =  self.datatable.cellWidget(x,9)
            assert isinstance(wsb, QSpinBox)
            wpattern = wsb.value()
            wlen = len(self.aw.qmc.wheelcolor[x])
            for i in range(wlen):
                color = QColor()
                color.setHsv(int(round((360/wlen)*i*wpattern)),255,255,255)
                self.aw.qmc.wheelcolor[x][i] = str(color.name())
            self.aw.qmc.drawWheel()

    #sets color pattern (many colors) for whole graph
    @pyqtSlot(int)
    def setcolorpattern(self,_):
        self.aw.qmc.wheelcolorpattern = self.colorSpinBox.value()
        if self.aw.qmc.wheelcolorpattern:
            for x, _ in enumerate(self.aw.qmc.wheelcolor):
                wlen = len(self.aw.qmc.wheelcolor[x])
                for i in range(wlen):
                    color = QColor()
                    color.setHsv(int(round((360/wlen)*i*self.aw.qmc.wheelcolorpattern)),255,255,255)
                    self.aw.qmc.wheelcolor[x][i] = str(color.name())
            self.aw.qmc.drawWheel()

    @pyqtSlot(int)
    def setsegmentalpha(self,z):
        u = self.aw.findWidgetsRow(self.labeltable,self.sender(),4)
        if u is not None:
            x = self.labelwheelx
            self.aw.qmc.segmentsalpha[x][u] = float(z/10.)
            self.aw.qmc.drawWheel()

    #rotate whole graph
    @pyqtSlot(bool)
    def rotatewheels1(self,_):
        for i, _ in enumerate(self.aw.qmc.startangle):
            self.aw.qmc.startangle[i] += 1
        self.aw.qmc.drawWheel()

    @pyqtSlot(bool)
    def rotatewheels0(self,_):
        for i, _ in enumerate(self.aw.qmc.startangle):
            self.aw.qmc.startangle[i] -= 1
        self.aw.qmc.drawWheel()

    #z= new width%, x= wheel number index, u = index of segment in the wheel
    @pyqtSlot(float)
    def setlabelwidth(self,z):
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
    def setwheelchild(self,z):
        i = self.aw.findWidgetsRow(self.labeltable,self.sender(),1)
        if i is not None:
            self.aw.qmc.setwheelchild(z,self.labelwheelx,i)
            self.aw.qmc.drawWheel()
            self.createdatatable() #update data table

    #deletes parent-child relation in a wheel. It obtains the wheel index by self.labelwheelx
    @pyqtSlot(bool)
    def resetlabelparents(self,_):
        x = self.labelwheelx
        nsegments = len(self.aw.qmc.wheellabelparent[x])
        for i in range(nsegments):
            self.aw.qmc.wheellabelparent[x][i] = 0
            self.aw.qmc.segmentlengths[x][i] = 100./nsegments
        self.aw.qmc.drawWheel()
        self.createlabeltablex(x)

    @pyqtSlot(float)
    def setaspect(self,_):
        self.aw.qmc.wheelaspect = self.aspectSpinBox.value()
        self.aw.qmc.drawWheel()

    #adjust decorative edge between wheels
    @pyqtSlot(int)
    def setedge(self):
        self.aw.qmc.wheeledge = float(self.edgeSpinBox.value())/100.
        self.aw.qmc.drawWheel()

    #adjusts line thickness
    @pyqtSlot(int)
    def setlinewidth(self,_):
        self.aw.qmc.wheellinewidth = self.linewidthSpinBox.value()
        self.aw.qmc.drawWheel()

    #sets line color
    @pyqtSlot(bool)
    def setlinecolor(self,_):
        colorf = self.aw.colordialog(QColor(self.aw.qmc.wheellinecolor))
        if colorf.isValid():
            colorname = str(colorf.name())
            #self.aw.qmc.wheellinealpha = colorf.alphaF()
            self.aw.qmc.wheellinecolor = colorname      #add new color to label
            self.aw.qmc.drawWheel()

    #sets text color
    @pyqtSlot(bool)
    def settextcolor(self,_):
        colorf = self.aw.colordialog(QColor(self.aw.qmc.wheeltextcolor))
        if colorf.isValid():
            colorname = str(colorf.name())
            #self.aw.qmc.wheeltextalpha = colorf.alphaF()
            self.aw.qmc.wheeltextcolor = colorname      #add new color to label
            self.aw.qmc.drawWheel()

    #makes not visible the wheel config table
    @pyqtSlot()
    def closelabels(self):
        self.labelGroupLayout.setVisible(False)
        self.labeltable.setVisible(False)
#        self.labelCloseButton.setVisible(False)
#        self.labelResetButton.setVisible(False)
        self.subdialogbuttons.setVisible(False)

    #creates graph table
    def createdatatable(self):
        ndata = len(self.aw.qmc.wheelnames)

        # self.datatable.clear() # this crashes Ubuntu 16.04
#        if ndata != 0:
#            self.datatable.clearContents() # this crashes Ubuntu 16.04 if device table is empty and also sometimes else
        self.datatable.clearSelection() # this seems to work also for Ubuntu 16.04

        self.datatable.setRowCount(ndata)
        self.datatable.setColumnCount(10)
        self.datatable.setHorizontalHeaderLabels([QApplication.translate('Table','Delete Wheel'),
                                                  QApplication.translate('Table','Edit Labels'),
                                                  QApplication.translate('Table','Update Labels'),
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
        self.datatable.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        #populate table
        for i in range(ndata):
            delButton = QPushButton(QApplication.translate('Button','Delete'))
            delButton.clicked.connect(self.popwheel)
            labelsedit = QLineEdit(str(','.join(self.aw.qmc.wheelnames[i])))
            updateButton = QPushButton(QApplication.translate('Button','Update'))
            updateButton.clicked.connect(self.updatelabels)
            setButton = QPushButton(QApplication.translate('Button','Select'))
            setButton.clicked.connect(self.createlabeltable)
            widthSpinBox = QDoubleSpinBox()
            widthSpinBox.setRange(1.,100.)
            widthSpinBox.setValue(self.aw.qmc.wradii[i])
            widthSpinBox.setSuffix('%')
            widthSpinBox.valueChanged.connect(self.setwidth)
            angleSpinBox = QSpinBox()
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
            txtSpinBox = QSpinBox()
            txtSpinBox.setRange(1,30)
            txtSpinBox.setValue(int(round(self.aw.qmc.wheeltextsize[i])))
            txtSpinBox.valueChanged.connect(self.setTextsizeX)
            colorButton = QPushButton(QApplication.translate('Button','Set Color'))
            colorButton.clicked.connect(self.setwheelcolor)
            colorSpinBox = QSpinBox()
            colorSpinBox.setRange(0,255)
            colorSpinBox.setWrapping(True)
            colorSpinBox.valueChanged.connect(self.setwheelcolorpattern)
            #add widgets to the table
            self.datatable.setCellWidget(i,0,delButton)
            self.datatable.setCellWidget(i,1,labelsedit)
            self.datatable.setCellWidget(i,2,updateButton)
            self.datatable.setCellWidget(i,3,setButton)
            self.datatable.setCellWidget(i,4,widthSpinBox)
            self.datatable.setCellWidget(i,5,angleSpinBox)
            self.datatable.setCellWidget(i,6,projectionComboBox)
            self.datatable.setCellWidget(i,7,txtSpinBox)
            self.datatable.setCellWidget(i,8,colorButton)
            self.datatable.setCellWidget(i,9,colorSpinBox)

    #reads label edit box for wheel with index x, and updates labels
    @pyqtSlot(bool)
    def updatelabels(self,_):
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),2)
        if x is not None:
            labelsedit =  self.datatable.cellWidget(x,1)
            assert isinstance(labelsedit,QLineEdit)
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
    def setwidth(self,_):
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),4)
        if x is not None:
            widthSpinBox = self.datatable.cellWidget(x,4)
            assert isinstance(widthSpinBox, QDoubleSpinBox)
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
            for i, _ in enumerate(self.aw.qmc.wradii):
                count +=  self.aw.qmc.wradii[i]
            diff = 100. - count
            if diff  != 0.:
                if diff > 0.000:  #if count smaller
                    self.aw.qmc.wradii[x] += abs(diff)
                else:
                    self.aw.qmc.wradii[x] -= abs(diff)
            self.aw.qmc.drawWheel()

    #sets starting angle (rotation) for a wheel with index x
    @pyqtSlot(int)
    def setangle(self,_):
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),5)
        if x is not None:
            angleSpinBox = self.datatable.cellWidget(x,5)
            assert isinstance(angleSpinBox, QSpinBox)
            self.aw.qmc.startangle[x] = angleSpinBox.value()
            self.aw.qmc.drawWheel()

    #sets text projection style for a wheel with index x
    @pyqtSlot(int)
    def setprojection(self,_):
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),6)
        if x is not None:
            projectionComboBox = self.datatable.cellWidget(x,6)
            assert isinstance(projectionComboBox, QComboBox)
            self.aw.qmc.projection[x] = projectionComboBox.currentIndex()
            self.aw.qmc.drawWheel()

    #changes text size in wheel with index x
    @pyqtSlot(int)
    def setTextsizeX(self,_):
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),7)
        if x is not None:
            txtSpinBox = self.datatable.cellWidget(x,7)
            assert isinstance(txtSpinBox, QSpinBox)
            self.aw.qmc.wheeltextsize[x] = txtSpinBox.value()
            self.aw.qmc.drawWheel()

    #changes size of text in whole graph
    @pyqtSlot(bool)
    def changetext1(self,_):
        for i, _ in enumerate(self.aw.qmc.wheeltextsize):
            self.aw.qmc.wheeltextsize[i] += 1
        self.aw.qmc.drawWheel()

    @pyqtSlot(bool)
    def changetext0(self,_):
        for i, _ in enumerate(self.aw.qmc.wheeltextsize):
            self.aw.qmc.wheeltextsize[i] -= 1
        self.aw.qmc.drawWheel()

    #adds new top wheel
    @pyqtSlot(bool)
    def insertwheel(self,_):
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
        wn,sl,sa,wlp,co = [],[],[],[],[]
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

    #deletes wheel with index x
    @pyqtSlot(bool)
    def popwheel(self,_):
        x = self.aw.findWidgetsRow(self.datatable,self.sender(),0)
        if x is not None:
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

    @pyqtSlot(bool)
    def fileSave(self,_):
        try:
            filename = self.aw.ArtisanSaveFileDialog(msg=QApplication.translate('Message','Save Wheel graph'),ext='*.wg')
            if filename:
                #write
                self.aw.serialize(filename,self.aw.getWheelGraph())
                self.aw.sendmessage(QApplication.translate('Message','Wheel Graph saved'))
        except OSError as e:
            self.aw.qmc.adderror((QApplication.translate('Error Message','IO Error:') + ' Wheel graph filesave(): {0}').format(str(e)))
            return

    @pyqtSlot(bool)
    def loadWheel(self,_):
        filename = self.aw.ArtisanOpenFileDialog(msg=QApplication.translate('Message','Open Wheel Graph'),path = self.aw.getDefaultPath(),ext='*.wg')
        if filename:
            self.aw.loadWheel(filename)
            self.aw.wheelpath = filename
            self.createdatatable()
            self.aw.qmc.drawWheel()

    def closeEvent(self, _):
        self.viewmode(False)

    @pyqtSlot(bool)
    def viewmode(self,_):
        self.close()
        self.aw.qmc.connectWheel()
        self.aw.qmc.drawWheel()
