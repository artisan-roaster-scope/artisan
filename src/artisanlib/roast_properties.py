#!/usr/bin/env python3

# ABOUT
# Artisan Roast Properties Dialog

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

import sys
import math
import platform
import prettytable

# import artisan.plus module
import plus.config  # @UnusedImport
import plus.util
import plus.stock

from artisanlib.suppress_errors import suppress_stdout_stderr
from artisanlib.util import deltaLabelUTF8,stringfromseconds,stringtoseconds, appFrozen
from artisanlib.dialogs import ArtisanDialog, ArtisanResizeablDialog
from artisanlib.widgets import MyQComboBox, ClickableQLabel, ClickableTextEdit

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QRegularExpression, QSettings, QTimer, QEvent
from PyQt5.QtGui import QColor, QIntValidator, QRegularExpressionValidator, QKeySequence, QPalette
from PyQt5.QtWidgets import (QApplication, QWidget, QCheckBox, QComboBox, QDialogButtonBox, QGridLayout,
                             QHBoxLayout, QVBoxLayout, QHeaderView, QLabel, QLineEdit, QTextEdit, QListView, 
                             QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QSizePolicy,
                             QGroupBox)
                             
if sys.platform.startswith("darwin"):
    import darkdetect # @UnresolvedImport


########################################################################################
#####################  Volume Calculator DLG  ##########################################
########################################################################################

class volumeCalculatorDlg(ArtisanDialog):
    def __init__(self, parent = None, aw = None, weightIn=None, weightOut=None,
            weightunit=0,volumeunit=0,
            inlineedit=None,outlineedit=None,tare=0): # weight in and out expected in g (int)
        
        self.parent_dialog = parent
        # weightunit 0:g, 1:Kg  volumeunit 0:ml, 1:l
        super(volumeCalculatorDlg,self).__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate("Form Caption","Volume Calculator",None))

        if self.aw.scale.device is not None and self.aw.scale.device != "" and self.aw.scale.device != "None":
            self.scale_connected = True
        else:
            self.scale_connected = False

        self.weightIn = weightIn
        self.weightOut = weightOut
        
        # the units
        self.weightunit = weightunit
        self.volumeunit = volumeunit
        
        # the results
        self.inVolume = None
        self.outVolume = None
        
        # the QLineedits of the RoastProperties dialog to be updated
        self.inlineedit = inlineedit
        self.outlineedit = outlineedit
        
        # the current active tare
        self.tare = tare
        
        # Scale Weight
        self.scale_weight = self.parent_dialog.scale_weight
        self.scaleWeight = QLabel() # displays the current reading - tare of the connected scale
        if self.parent_dialog.ble is not None:
            self.update_scale_weight()
            self.parent_dialog.ble.weightChanged.connect(self.ble_weight_changed)
            self.parent_dialog.ble.deviceDisconnected.connect(self.ble_scan_failed)
        
        # Unit Group
        unitvolumeLabel = QLabel("<b>" + QApplication.translate("Label","Unit", None) + "</b>")
        self.unitvolumeEdit = QLineEdit("%g" % self.aw.qmc.volumeCalcUnit)
#        self.unitvolumeEdit.setValidator(QIntValidator(0, 99999,self.unitvolumeEdit))
        self.unitvolumeEdit.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, self.unitvolumeEdit))
        self.unitvolumeEdit.setMinimumWidth(70)
        self.unitvolumeEdit.setMaximumWidth(70)
        self.unitvolumeEdit.setAlignment(Qt.AlignRight)
        unitvolumeUnit = QLabel(QApplication.translate("Label","ml", None))
        
        # unit button
        unitButton = QPushButton(QApplication.translate("Button", "unit",None))
        unitButton.clicked.connect(self.unitWeight)
        unitButton.setFocusPolicy(Qt.NoFocus)

        unitLayout = QHBoxLayout()
        if self.scale_connected:
            unitLayout.addStretch()
        unitLayout.addWidget(self.scaleWeight)
        unitLayout.addStretch()
        unitLayout.addWidget(unitvolumeLabel)
        unitLayout.addWidget(self.unitvolumeEdit)
        unitLayout.addWidget(unitvolumeUnit)
        unitLayout.addStretch()
        if self.scale_connected:
            unitLayout.addWidget(unitButton)
        
        # In Group
        coffeeinunitweightLabel = QLabel("<b>" + QApplication.translate("Label","Unit Weight", None) + "</b>")
        self.coffeeinweightEdit = QLineEdit(self.aw.qmc.volumeCalcWeightInStr)
        self.coffeeinweightEdit.setMinimumWidth(70)
        self.coffeeinweightEdit.setMaximumWidth(70)
        self.coffeeinweightEdit.setAlignment(Qt.AlignRight)
        coffeeinunitweightUnit = QLabel(QApplication.translate("Label","g", None))

        coffeeinweightLabel = QLabel("<b>" + QApplication.translate("Label","Weight", None) + "</b>")
        self.coffeeinweight = QLineEdit()
        if self.weightIn:
            self.coffeeinweight.setText("%g" % self.aw.float2floatWeightVolume(self.weightIn))
        self.coffeeinweight.setMinimumWidth(70)
        self.coffeeinweight.setMaximumWidth(70)
        self.coffeeinweight.setAlignment(Qt.AlignRight)
        self.coffeeinweight.setReadOnly(True)
        self.coffeeinweight.setFocusPolicy(Qt.NoFocus)
        if sys.platform.startswith("darwin"):
            self.coffeeinweight.setStyleSheet("border: 0.5px solid lightgrey; background-color:'lightgrey'")
        else:
            self.coffeeinweight.setStyleSheet("background-color:'lightgrey'")
        coffeeinweightUnit = QLabel(self.aw.qmc.weight_units[weightunit])
        
        coffeeinvolumeLabel = QLabel("<b>" + QApplication.translate("Label","Volume", None) + "</b>")
        self.coffeeinvolume = QLineEdit()
        self.coffeeinvolume.setMinimumWidth(70)
        self.coffeeinvolume.setMaximumWidth(70)
        
        palette = QPalette()
        palette.setColor(self.coffeeinvolume.foregroundRole(), QColor('red'))
        self.coffeeinvolume.setPalette(palette)
        
        self.coffeeinvolume.setAlignment(Qt.AlignRight)
        self.coffeeinvolume.setReadOnly(True)
        self.coffeeinvolume.setFocusPolicy(Qt.NoFocus)
        coffeeinvolumeUnit = QLabel(self.aw.qmc.volume_units[volumeunit])
            
        # in button
        inButton = QPushButton(QApplication.translate("Button", "in",None))
        inButton.clicked.connect(self.inWeight)
        inButton.setFocusPolicy(Qt.NoFocus)
        
        inGrid = QGridLayout()
        inGrid.addWidget(coffeeinweightLabel,0,0)
        inGrid.addWidget(self.coffeeinweight,0,1)
        inGrid.addWidget(coffeeinweightUnit,0,2)
        inGrid.addWidget(coffeeinvolumeLabel,1,0)
        inGrid.addWidget(self.coffeeinvolume,1,1)
        inGrid.addWidget(coffeeinvolumeUnit,1,2)
        
        volumeInLayout = QHBoxLayout()
        volumeInLayout.addWidget(coffeeinunitweightLabel)
        volumeInLayout.addWidget(self.coffeeinweightEdit)
        volumeInLayout.addWidget(coffeeinunitweightUnit)
        volumeInLayout.addSpacing(15)
        volumeInLayout.addLayout(inGrid)
        
        inButtonLayout = QHBoxLayout()
        inButtonLayout.addWidget(inButton)
        inButtonLayout.addStretch()
        
        volumeInVLayout = QVBoxLayout()
        volumeInVLayout.addLayout(volumeInLayout)
        if self.scale_connected:
            volumeInVLayout.addLayout(inButtonLayout)
        
        volumeInGroupLayout = QGroupBox(QApplication.translate("Label","Green", None))
        volumeInGroupLayout.setLayout(volumeInVLayout)
        if weightIn is None:
            volumeInGroupLayout.setDisabled(True)

        self.resetInVolume()

        # Out Group
        coffeeoutunitweightLabel = QLabel("<b>" + QApplication.translate("Label","Unit Weight", None) + "</b>")
        self.coffeeoutweightEdit = QLineEdit(self.aw.qmc.volumeCalcWeightOutStr)
        self.coffeeoutweightEdit.setMinimumWidth(60)
        self.coffeeoutweightEdit.setMaximumWidth(60)
        self.coffeeoutweightEdit.setAlignment(Qt.AlignRight)
        coffeeoutunitweightUnit = QLabel(QApplication.translate("Label","g", None))

        coffeeoutweightLabel = QLabel("<b>" + QApplication.translate("Label","Weight", None) + "</b>")
        self.coffeeoutweight = QLineEdit()
        if self.weightOut:
            self.coffeeoutweight.setText("%g" % self.aw.float2floatWeightVolume(self.weightOut))
        self.coffeeoutweight.setMinimumWidth(60)
        self.coffeeoutweight.setMaximumWidth(60)
        self.coffeeoutweight.setAlignment(Qt.AlignRight)
        self.coffeeoutweight.setReadOnly(True)
        if sys.platform.startswith("darwin"):
            self.coffeeoutweight.setStyleSheet("border: 0.5px solid lightgrey; background-color:'lightgrey'")
        else:
            self.coffeeoutweight.setStyleSheet("background-color:'lightgrey'")
        self.coffeeoutweight.setFocusPolicy(Qt.NoFocus)
        coffeeoutweightUnit = QLabel(self.aw.qmc.weight_units[weightunit])

        coffeeoutvolumeLabel = QLabel("<b>" + QApplication.translate("Label","Volume", None) + "</b>")
        self.coffeeoutvolume = QLineEdit()
        self.coffeeoutvolume.setMinimumWidth(60)
        self.coffeeoutvolume.setMaximumWidth(60)
        
        palette = QPalette()
        palette.setColor(self.coffeeoutvolume.foregroundRole(), QColor('red'))
        self.coffeeoutvolume.setPalette(palette)

        self.coffeeoutvolume.setAlignment(Qt.AlignRight)
        self.coffeeoutvolume.setReadOnly(True)
        self.coffeeoutvolume.setFocusPolicy(Qt.NoFocus)
        coffeeoutvolumeUnit = QLabel(self.aw.qmc.volume_units[volumeunit])

        # out button
        outButton = QPushButton(QApplication.translate("Button", "out",None))
        outButton.clicked.connect(self.outWeight)
        outButton.setFocusPolicy(Qt.NoFocus)
                
        outGrid = QGridLayout()
        outGrid.addWidget(coffeeoutweightLabel,0,0)
        outGrid.addWidget(self.coffeeoutweight,0,1)
        outGrid.addWidget(coffeeoutweightUnit,0,2)
        outGrid.addWidget(coffeeoutvolumeLabel,1,0)
        outGrid.addWidget(self.coffeeoutvolume,1,1)
        outGrid.addWidget(coffeeoutvolumeUnit,1,2)
        
        volumeOutLayout = QHBoxLayout()
        volumeOutLayout.addWidget(coffeeoutunitweightLabel)
        volumeOutLayout.addWidget(self.coffeeoutweightEdit)
        volumeOutLayout.addWidget(coffeeoutunitweightUnit)
        volumeOutLayout.addSpacing(15)
        volumeOutLayout.addLayout(outGrid)
        
        outButtonLayout = QHBoxLayout()
        outButtonLayout.addWidget(outButton)
        outButtonLayout.addStretch()
        
        volumeOutVLayout = QVBoxLayout()
        volumeOutVLayout.addLayout(volumeOutLayout)
        if self.scale_connected:
            volumeOutVLayout.addLayout(outButtonLayout)
        
        volumeOutGroupLayout = QGroupBox(QApplication.translate("Label","Roasted", None))
        volumeOutGroupLayout.setLayout(volumeOutVLayout)
        if weightOut is None:
            volumeOutGroupLayout.setDisabled(True)

        self.resetOutVolume()
        
        self.coffeeinweightEdit.editingFinished.connect(self.resetInVolume)
        self.coffeeoutweightEdit.editingFinished.connect(self.resetOutVolume)
        self.unitvolumeEdit.editingFinished.connect(self.resetVolume)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.updateVolumes)
        self.dialogbuttons.rejected.connect(self.close)
        
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)

        mainlayout = QVBoxLayout()
        mainlayout.addLayout(unitLayout)
        mainlayout.addWidget(volumeInGroupLayout)
        mainlayout.addWidget(volumeOutGroupLayout)
        mainlayout.addLayout(buttonLayout)
        self.setLayout(mainlayout)
        self.coffeeinweightEdit.setFocus()
        
        self.parent_dialog.scaleWeightUpdated.connect(self.update_scale_weight)
        

    pyqtSlot()
    def ble_scan_failed(self):
        self.scale_weight = None
        self.scale_battery = None
        self.scaleWeight.setText("")

    pyqtSlot(float)
    def ble_weight_changed(self,w):
        if w is not None:
            self.scale_weight = w
            self.update_scale_weight()

    @pyqtSlot(float)
    def update_scale_weight(self,weight=None):
        try:
            if weight is not None:
                self.scale_weight = weight
            if self.scale_weight is not None and self.tare is not None:
                self.scaleWeight.setText("{0:.1f}g".format(self.scale_weight - self.tare))
            else:
                self.scaleWeight.setText("")
        except: # the dialog might have been closed already and thus the qlabel might not exist anymore
            pass
        
    #keyboard presses. There must not be widgets (pushbuttons, comboboxes, etc) in focus in order to work 
    def keyPressEvent(self,event):
        key = int(event.key())
        if key == 16777220 and self.scale_connected: # ENTER key pressed
            v = self.retrieveWeight()
            if v and v != 0:
                if self.unitvolumeEdit.hasFocus():
                    self.unitvolumeEdit.setText("%g" % self.aw.float2float(v))
                elif self.coffeeinweightEdit.hasFocus():
                    self.coffeeinweightEdit.setText("%g" % self.aw.float2float(v))
                elif self.coffeeoutweightEdit.hasFocus():
                    self.coffeeoutweightEdit.setText("%g" % self.aw.float2float(v))
                    
    def widgetWeight(self,widget):
        w = self.retrieveWeight()
        if w is not None:
            v = self.aw.float2floatWeightVolume(w)
#            widget.setText("%g" % self.aw.float2float(v))
            # updating this widget in a separate thread seems to be important on OS X 10.14 to avoid delayed updates and widget redraw problesm
            QTimer.singleShot(2,lambda : widget.setText("%g" % self.aw.float2float(v)))
    
    pyqtSlot(bool)
    def unitWeight(self,_):
        self.widgetWeight(self.unitvolumeEdit)
        
    pyqtSlot(bool)
    def inWeight(self,_):
        QTimer.singleShot(1,lambda : self.widgetWeight(self.coffeeinweightEdit))
        QTimer.singleShot(10,lambda : self.resetInVolume())
        QApplication.processEvents()
        
    pyqtSlot(bool)
    def outWeight(self,_):
        QTimer.singleShot(1,lambda : self.widgetWeight(self.coffeeoutweightEdit))
        QTimer.singleShot(10,lambda : self.resetOutVolume())
        QApplication.processEvents()
        
    def retrieveWeight(self):
        v = self.scale_weight
        if v is not None: # value received
            # substruct tare
            return v - self.tare
        else:
            return None

    @pyqtSlot()
    def resetVolume(self):
        self.resetInVolume()
        self.resetOutVolume()

    @pyqtSlot()
    def resetInVolume(self):
        try:
            line = self.coffeeinweightEdit.text()
            if line is None or str(line).strip() == "":
                self.coffeeinvolume.setText("")
                self.inVolume = None
            else:
                self.inVolume = self.aw.convertVolume(self.aw.convertWeight(self.weightIn,self.weightunit,0) * float(self.aw.comma2dot(self.unitvolumeEdit.text())) / float(self.aw.comma2dot(self.coffeeinweightEdit.text())),5,self.volumeunit)
                self.coffeeinvolume.setText("%g" % self.aw.float2floatWeightVolume(self.inVolume))
        except Exception:
            self.inVolume = None
            self.coffeeinvolume.setText("")

    @pyqtSlot()
    def resetOutVolume(self):
        try:
            line = self.coffeeoutweightEdit.text()
            if line is None or str(line).strip() == "":
                self.coffeeoutvolume.setText("")
                self.outVolume = None
            else:
                self.outVolume = self.aw.convertVolume(self.aw.convertWeight(self.weightOut,self.weightunit,0) * float(self.aw.comma2dot(str(self.unitvolumeEdit.text()))) / float(self.aw.comma2dot(str(self.coffeeoutweightEdit.text()))),5,self.volumeunit)
                self.coffeeoutvolume.setText("%g" % self.aw.float2floatWeightVolume(self.outVolume))
        except Exception:
            self.outVolume = None
            self.coffeeoutvolume.setText("")

    @pyqtSlot()
    def updateVolumes(self):
        if self.inVolume and self.inVolume != "":
            if self.volumeunit == 0:
                self.inlineedit.setText("%g" % self.aw.float2floatWeightVolume(self.inVolume))
            else:
                self.inlineedit.setText("%g" % self.aw.float2floatWeightVolume(self.inVolume))
        if self.outVolume and self.outVolume != "":
            if self.volumeunit == 0:
                self.outlineedit.setText("%g" % self.aw.float2floatWeightVolume(self.outVolume))
            else:
                self.outlineedit.setText("%g" % self.aw.float2floatWeightVolume(self.outVolume))
        self.parent_dialog.volume_percent()
        self.closeEvent(None)
        
    def closeEvent(self,_):
        try:
            self.parent_dialog.volumedialog = None
        except:
            pass
        if self.unitvolumeEdit.text() and self.unitvolumeEdit.text() != "":
            self.aw.qmc.volumeCalcUnit = float(self.aw.comma2dot(self.unitvolumeEdit.text()))
            self.aw.qmc.volumeCalcWeightInStr = self.aw.comma2dot(self.coffeeinweightEdit.text())
            self.aw.qmc.volumeCalcWeightOutStr = self.aw.comma2dot(self.coffeeoutweightEdit.text())
            self.parent_dialog.calculated_density()
        self.accept()

    @pyqtSlot()
    def close(self):
        self.closeEvent(None)


##########################################################################
#####################  VIEW Tare  ########################################
##########################################################################


class tareDlg(ArtisanDialog):
    def __init__(self, parent = None, aw = None, tarePopup = None):
        super(tareDlg,self).__init__(parent, aw)
        self.parent = parent
        self.tarePopup = tarePopup
        self.setModal(True)
        self.setWindowTitle(QApplication.translate("Form Caption","Tare Setup", None))

        self.taretable = QTableWidget()
        self.taretable.setTabKeyNavigation(True)
        self.createTareTable()
        
        self.taretable.itemSelectionChanged.connect(self.selectionChanged)
        
        addButton = QPushButton(QApplication.translate("Button","Add", None))
        addButton.setFocusPolicy(Qt.NoFocus)
        self.delButton = QPushButton(QApplication.translate("Button","Delete", None))
        self.delButton.setDisabled(True)
        self.delButton.setFocusPolicy(Qt.NoFocus)
        
        addButton.clicked.connect(self.addTare)
        self.delButton.clicked.connect(self.delTare)
        
        okButton = QPushButton(QApplication.translate("Button","OK", None))
        cancelButton = QPushButton(QApplication.translate("Button","Cancel",None))
        cancelButton.setFocusPolicy(Qt.NoFocus)
        okButton.clicked.connect(self.close)
        cancelButton.clicked.connect(self.reject)
        contentbuttonLayout = QHBoxLayout()
        contentbuttonLayout.addStretch()
        contentbuttonLayout.addWidget(addButton)
        contentbuttonLayout.addWidget(self.delButton)
        contentbuttonLayout.addStretch()

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(okButton)
        layout = QVBoxLayout()
        layout.addWidget(self.taretable)
        layout.addLayout(contentbuttonLayout)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)
    
    @pyqtSlot()
    def selectionChanged(self):
        if len(self.taretable.selectedRanges()) > 0:
            self.delButton.setDisabled(False)
        else:
            self.delButton.setDisabled(False)
        
    def closeEvent(self,_):
        self.saveTareTable()
        # update popup
        self.tarePopup.tarePopupEnabled = False
        self.tarePopup.tareComboBox.clear()
        self.tarePopup.tareComboBox.addItem("<edit> TARE")
        self.tarePopup.tareComboBox.insertSeparator(2)
        self.tarePopup.tareComboBox.addItem("")
        self.tarePopup.tareComboBox.addItems(self.aw.qmc.container_names)
        self.tarePopup.tareComboBox.setCurrentIndex(2) # reset to the empty entry
        self.aw.qmc.container_idx = -1
        self.tarePopup.tarePopupEnabled = True
        self.accept()

    @pyqtSlot(bool)
    def addTare(self,_):
        rows = self.taretable.rowCount()
        self.taretable.setRowCount(rows + 1)
        #add widgets to the table
        name = QLineEdit()
        name.setAlignment(Qt.AlignRight)
        name.setText("name")
        w,_,_ = self.aw.scale.readWeight(self.parent.scale_weight) # read value from scale in 'g'
        weight = QLineEdit()
        weight.setAlignment(Qt.AlignRight)
        if w > -1:
            weight.setText(str(w))
        else:
            weight.setText(str(0))
        weight.setValidator(QIntValidator(0,999,weight))
        self.taretable.setCellWidget(rows,0,name)
        self.taretable.setCellWidget(rows,1,weight)
        
    @pyqtSlot(bool)
    def delTare(self,_):
        selected = self.taretable.selectedRanges()
        if len(selected) > 0:
            bindex = selected[0].topRow()
            if bindex >= 0:
                self.taretable.removeRow(bindex)

    def saveTareTable(self):
        tars = self.taretable.rowCount() 
        names = []
        weights = []
        for i in range(tars):
            name = self.taretable.cellWidget(i,0).text()
            weight = int(round(float(self.aw.comma2dot(self.taretable.cellWidget(i,1).text()))))
            names.append(name)
            weights.append(weight)
        self.aw.qmc.container_names = names
        self.aw.qmc.container_weights = weights
        
    def createTareTable(self):
        self.taretable.clear()
        self.taretable.setRowCount(len(self.aw.qmc.container_names))
        self.taretable.setColumnCount(2)
        self.taretable.setHorizontalHeaderLabels([QApplication.translate("Table","Name",None),
                                                         QApplication.translate("Table","Weight",None)])
        self.taretable.setAlternatingRowColors(True)
        self.taretable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.taretable.setSelectionBehavior(QTableWidget.SelectRows)
        self.taretable.setSelectionMode(QTableWidget.SingleSelection)
        self.taretable.setShowGrid(True)
        self.taretable.verticalHeader().setSectionResizeMode(2)
        for i in range(len(self.aw.qmc.container_names)):
            #add widgets to the table
            name = QLineEdit()
            name.setAlignment(Qt.AlignRight)
            name.setText(self.aw.qmc.container_names[i])
            weight = QLineEdit()
            weight.setAlignment(Qt.AlignRight)
            weight.setText(str(self.aw.qmc.container_weights[i]))
            weight.setValidator(QIntValidator(0,999,weight))
            
            self.taretable.setCellWidget(i,0,name)
            self.taretable.setCellWidget(i,1,weight)
        header = self.taretable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.taretable.setColumnWidth(1,65)
        
########################################################################################
#####################  RECENT ROAST POPUP  #############################################

class RoastsComboBox(QComboBox):
    def __init__(self, parent = None, aw = None, selection = None):
        super(RoastsComboBox, self).__init__(parent)
        self.aw = aw
        self.installEventFilter(self)
        self.selection = selection # just the roast title
        self.edited = selection
        self.updateMenu()
        self.editTextChanged.connect(self.textEdited)
        self.setEditable(True)
#        self.setMouseTracking(False)

    @pyqtSlot("QString")
    def textEdited(self,txt):
        cleaned = ' '.join(txt.split())
        self.edited = cleaned

    def getSelection(self):
        return self.edited or self.selection

    def setSelection(self,i):
        if i >= 0:
            try:
                self.edited = None # reset the user text editing
            except Exception:
                pass

    def eventFilter(self, obj, event):
# the next prevents correct setSelection on Windows
#        if event.type() == QEvent.FocusIn:
#            self.setSelection(self.currentIndex())
        if event.type() == QEvent.MouseButtonPress:
            self.updateMenu()
#            return True # stops processing # popup not drawn if this line is added
#        return super(RoastsComboBox, self).eventFilter(obj, event) # this seems to slow down things on Windows and not necessary anyhow
        return False # cont processing

    # the first entry is always just the current text edit line
    def updateMenu(self):
        self.blockSignals(True)
        try:
            roasts = self.aw.recentRoastsMenuList()
            self.clear()
            self.addItems([self.edited] + roasts)
        except:
            pass
        self.blockSignals(False)

########################################################################################
#####################  Roast Properties Dialog  ########################################

class editGraphDlg(ArtisanResizeablDialog):
    scaleWeightUpdated = pyqtSignal(float)
    connectScaleSignal = pyqtSignal()
    readScaleSignal = pyqtSignal()

    def __init__(self, parent = None, aw = None, activeTab = 0):
        super(editGraphDlg,self).__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate("Form Caption","Roast Properties",None))
        
        # we remember user modifications to revert to them on deselecting a plus element
        self.modified_beans = self.aw.qmc.beans
        self.modified_density_in_text = str(self.aw.float2float(self.aw.qmc.density[0]))
        self.modified_volume_in_text = str(self.aw.float2float(self.aw.qmc.volume[0]))
        self.modified_beansize_min_text = str(self.aw.qmc.beansize_min)
        self.modified_beansize_max_text = str(self.aw.qmc.beansize_max)
        self.modified_moisture_greens_text = str(self.aw.qmc.moisture_greens)
        
        # remember parameters set by plus_coffee/plus_blend on entering the dialog to enable a Cancel action
        self.org_beans = self.aw.qmc.beans
        self.org_density = self.aw.qmc.density
        self.org_density_roasted = self.aw.qmc.density_roasted
        self.org_beansize_min = self.aw.qmc.beansize_min
        self.org_beansize_max = self.aw.qmc.beansize_max
        self.org_moisture_greens = self.aw.qmc.moisture_greens
        
        self.org_title = self.aw.qmc.title
        self.org_title_show_always = self.aw.qmc.title_show_always
        
        self.org_weight = self.aw.qmc.weight[:]
        self.org_volume = self.aw.qmc.volume[:]
        
        self.batcheditmode = False # a click to the batch label enables the batcheditmode
        
        self.ble = None # the BLE interface
        self.scale_weight = None # weight received from a connected scale
        self.scale_battery = None # battery level of the connected scale in %
        self.scale_set = None # set weight for accumulation in g
        
        self.disconnecting = False # this is set to True to terminate the scale connection
        self.volumedialog = None # link forward to the the Volume Calculator
        
        # other parameters remembered for Cancel operation
        self.org_specialevents = self.aw.qmc.specialevents[:]
        self.org_specialeventstype = self.aw.qmc.specialeventstype[:]
        self.org_specialeventsStrings = self.aw.qmc.specialeventsStrings[:]
        self.org_specialeventsvalue = self.aw.qmc.specialeventsvalue[:]
        self.org_timeindex = self.aw.qmc.timeindex[:]
        
        self.org_ambientTemp = self.aw.qmc.ambientTemp
        self.org_ambient_humidity = self.aw.qmc.ambient_humidity
        self.org_ambient_pressure = self.aw.qmc.ambient_pressure
        
        self.org_roastpropertiesAutoOpenFlag = self.aw.qmc.roastpropertiesAutoOpenFlag
        self.org_roastpropertiesAutoOpenDropFlag = self.aw.qmc.roastpropertiesAutoOpenDropFlag
        
        # propulated by selecting a recent roast from the popup via recentRoastActivated()
        self.template_file = None
        self.template_name = None
        self.template_uuid = None
        self.template_batchnr = None
        self.template_batchprefix = None
        
        regextime = QRegularExpression(r"^-?[0-9]?[0-9]?[0-9]:[0-5][0-9]$")
        #MARKERS
        chargelabel = QLabel("<b>" + QApplication.translate("Label", "CHARGE",None) + "</b>")
        chargelabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        chargelabel.setStyleSheet("background-color:'#f07800';")
        self.chargeedit = QLineEdit(stringfromseconds(0))
#        self.chargeedit.setFocusPolicy(Qt.NoFocus)
        self.chargeedit.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.chargeeditcopy = stringfromseconds(0)
        self.chargeedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.chargeedit.setMaximumWidth(50)
        self.chargeedit.setMinimumWidth(50)
        chargelabel.setBuddy(self.chargeedit)
        self.charge_idx = 0
        self.drop_idx = 0
        #charge_str = ""
        drop_str = ""
        if len(self.aw.qmc.timex):
            TP_index = self.aw.findTP()
            if self.aw.qmc.timeindex[1]:
                #manual dryend available
                dryEndIndex = self.aw.qmc.timeindex[1]
            else:
                #find when dry phase ends 
                dryEndIndex = self.aw.findDryEnd(TP_index)
            self.charge_idx = self.aw.findBTbreak(0,dryEndIndex,offset=0.5)
            self.drop_idx = self.aw.findBTbreak(dryEndIndex,offset=0.2)
            if self.drop_idx != 0 and self.drop_idx != self.aw.qmc.timeindex[6]:
                drop_str = stringfromseconds(self.aw.qmc.timex[self.drop_idx]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]])
        drylabel = QLabel("<b>" + QApplication.translate("Label", "DRY END",None) + "</b>")
        drylabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        drylabel.setStyleSheet("background-color:'orange';")
        if self.aw.qmc.timeindex[1] and self.aw.qmc.timeindex[1] < len(self.aw.qmc.timex):
            t2 = self.aw.qmc.timex[self.aw.qmc.timeindex[1]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            t2 = 0
        self.dryedit = QLineEdit(stringfromseconds(t2))
        self.dryedit.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.dryeditcopy = stringfromseconds(t2)
        self.dryedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.dryedit.setMaximumWidth(50)
        self.dryedit.setMinimumWidth(50)
        drylabel.setBuddy(self.dryedit)
        Cstartlabel = QLabel("<b>" + QApplication.translate("Label","FC START",None) + "</b>")
        Cstartlabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        Cstartlabel.setStyleSheet("background-color:'orange';")
        if self.aw.qmc.timeindex[2] and self.aw.qmc.timeindex[2] < len(self.aw.qmc.timex):
            t3 = self.aw.qmc.timex[self.aw.qmc.timeindex[2]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            t3 = 0
        self.Cstartedit = QLineEdit(stringfromseconds(t3))
#        self.Cstartedit.setFocusPolicy(Qt.NoFocus)
        self.Cstartedit.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.Cstarteditcopy = stringfromseconds(t3)
        self.Cstartedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.Cstartedit.setMaximumWidth(50)
        self.Cstartedit.setMinimumWidth(50)
        Cstartlabel.setBuddy(self.Cstartedit)
        
        Cendlabel = QLabel("<b>" + QApplication.translate("Label","FC END",None) + "</b>")
        Cendlabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        Cendlabel.setStyleSheet("background-color:'orange';")
        if self.aw.qmc.timeindex[3] and self.aw.qmc.timeindex[3] < len(self.aw.qmc.timex):
            t4 = self.aw.qmc.timex[self.aw.qmc.timeindex[3]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            t4 = 0
        self.Cendedit = QLineEdit(stringfromseconds(t4))
#        self.Cendedit.setFocusPolicy(Qt.NoFocus)
        self.Cendedit.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.Cendeditcopy = stringfromseconds(t4)
        self.Cendedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.Cendedit.setMaximumWidth(50)
        self.Cendedit.setMinimumWidth(50)
        Cendlabel.setBuddy(self.Cendedit)
        CCstartlabel = QLabel("<b>" + QApplication.translate("Label","SC START",None) + "</b>")
        CCstartlabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        CCstartlabel.setStyleSheet("background-color:'orange';")
        if self.aw.qmc.timeindex[4] and self.aw.qmc.timeindex[4] < len(self.aw.qmc.timex):
            t5 = self.aw.qmc.timex[self.aw.qmc.timeindex[4]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            t5 = 0
        self.CCstartedit = QLineEdit(stringfromseconds(t5))
#        self.CCstartedit.setFocusPolicy(Qt.NoFocus)
        self.CCstartedit.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.CCstarteditcopy = stringfromseconds(t5)
        self.CCstartedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.CCstartedit.setMaximumWidth(50)
        self.CCstartedit.setMinimumWidth(50)
        CCstartlabel.setBuddy(self.CCstartedit)
        CCendlabel = QLabel("<b>" + QApplication.translate("Label","SC END",None) + "</b>")
        CCendlabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        CCendlabel.setStyleSheet("background-color:'orange';")
        if self.aw.qmc.timeindex[5] and self.aw.qmc.timeindex[5] < len(self.aw.qmc.timex):
            t6 = self.aw.qmc.timex[self.aw.qmc.timeindex[5]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            t6 = 0
        self.CCendedit = QLineEdit(stringfromseconds(t6))
#        self.CCendedit.setFocusPolicy(Qt.NoFocus)
        self.CCendedit.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.CCendeditcopy = stringfromseconds(t6)
        self.CCendedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.CCendedit.setMaximumWidth(50)
        self.CCendedit.setMinimumWidth(50)
        CCendlabel.setBuddy(self.CCendedit)
        droplabel = QLabel("<b>" + QApplication.translate("Label", "DROP",None) + "</b>")
        droplabel.setStyleSheet("background-color:'#f07800';")
        droplabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        if self.aw.qmc.timeindex[6] and self.aw.qmc.timeindex[6] < len(self.aw.qmc.timex):
            t7 = self.aw.qmc.timex[self.aw.qmc.timeindex[6]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            t7 = 0
        self.dropedit = QLineEdit(stringfromseconds(t7))
#        self.dropedit.setFocusPolicy(Qt.NoFocus)
        self.dropedit.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.dropeditcopy = stringfromseconds(t7)
        self.dropedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.dropedit.setMaximumWidth(50)
        self.dropedit.setMinimumWidth(50)
        droplabel.setBuddy(self.dropedit)
        self.dropestimate = QLabel(drop_str)
        coollabel = QLabel("<b>" + QApplication.translate("Label", "COOL",None) + "</b>")
        coollabel.setStyleSheet("background-color:'#6666ff';")
        coollabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        if self.aw.qmc.timeindex[7] and self.aw.qmc.timeindex[7] < len(self.aw.qmc.timex):
            t8 = self.aw.qmc.timex[self.aw.qmc.timeindex[7]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            t8 = 0
        self.cooledit = QLineEdit(stringfromseconds(t8))
#        self.cooledit.setFocusPolicy(Qt.NoFocus)
        self.cooledit.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.cooleditcopy = stringfromseconds(t8)
        self.cooledit.setValidator(QRegularExpressionValidator(regextime,self))
        self.cooledit.setMaximumWidth(50)
        self.cooledit.setMinimumWidth(50)
        coollabel.setBuddy(self.cooledit)
        self.roastproperties = QCheckBox(QApplication.translate("CheckBox","Delete roast properties on RESET", None))
        self.roastproperties.setChecked(bool(self.aw.qmc.roastpropertiesflag))
        self.roastproperties.stateChanged.connect(self.roastpropertiesChanged)
        self.roastpropertiesAutoOpen = QCheckBox(QApplication.translate("CheckBox","Open on CHARGE", None))
        self.roastpropertiesAutoOpen.setChecked(bool(self.aw.qmc.roastpropertiesAutoOpenFlag))
        self.roastpropertiesAutoOpen.stateChanged.connect(self.roastpropertiesAutoOpenChanged)
        self.roastpropertiesAutoOpenDROP = QCheckBox(QApplication.translate("CheckBox","Open on DROP", None))
        self.roastpropertiesAutoOpenDROP.setChecked(bool(self.aw.qmc.roastpropertiesAutoOpenDropFlag))
        self.roastpropertiesAutoOpenDROP.stateChanged.connect(self.roastpropertiesAutoOpenDROPChanged)
        # EVENTS
        #table for showing events
        self.eventtable = QTableWidget()
        self.eventtable.setTabKeyNavigation(True)
        self.clusterEventsButton = QPushButton(QApplication.translate("Button", "Cluster",None))
        self.clusterEventsButton.setFocusPolicy(Qt.NoFocus)
        self.clusterEventsButton.setMaximumSize(self.clusterEventsButton.sizeHint())
        self.clusterEventsButton.setMinimumSize(self.clusterEventsButton.minimumSizeHint())
        self.clusterEventsButton.clicked.connect(self.clusterEvents)
        self.clearEventsButton = QPushButton(QApplication.translate("Button", "Clear",None))
        self.clearEventsButton.setFocusPolicy(Qt.NoFocus)
        self.clearEventsButton.setMaximumSize(self.clearEventsButton.sizeHint())
        self.clearEventsButton.setMinimumSize(self.clearEventsButton.minimumSizeHint())
        self.clearEventsButton.clicked.connect(self.clearEvents) 
        self.createalarmTableButton = QPushButton(QApplication.translate("Button", "Create Alarms",None))
        self.createalarmTableButton.setFocusPolicy(Qt.NoFocus)
        self.createalarmTableButton.setMaximumSize(self.createalarmTableButton.sizeHint())
        self.createalarmTableButton.setMinimumSize(self.createalarmTableButton.minimumSizeHint())
        self.createalarmTableButton.clicked.connect(self.createAlarmEventTable)
        self.ordereventTableButton = QPushButton(QApplication.translate("Button", "Order",None))
        self.ordereventTableButton.setFocusPolicy(Qt.NoFocus)
        self.ordereventTableButton.setMaximumSize(self.ordereventTableButton.sizeHint())
        self.ordereventTableButton.setMinimumSize(self.ordereventTableButton.minimumSizeHint())
        self.ordereventTableButton.clicked.connect(self.orderEventTable)
        self.neweventTableButton = QPushButton(QApplication.translate("Button", "Add",None))
        self.neweventTableButton.setFocusPolicy(Qt.NoFocus)
        self.neweventTableButton.setMaximumSize(self.neweventTableButton.sizeHint())
        self.neweventTableButton.setMinimumSize(self.neweventTableButton.minimumSizeHint())
        self.neweventTableButton.clicked.connect(self.addEventTable)
        self.deleventTableButton = QPushButton(QApplication.translate("Button", "Delete",None))
        self.deleventTableButton.setFocusPolicy(Qt.NoFocus)
        self.deleventTableButton.setMaximumSize(self.deleventTableButton.sizeHint())
        self.deleventTableButton.setMinimumSize(self.deleventTableButton.minimumSizeHint())
        self.deleventTableButton.clicked.connect(self.deleteEventTable)
        self.copyeventTableButton = QPushButton(QApplication.translate("Button", "Copy Table",None))
        self.copyeventTableButton.setToolTip(QApplication.translate("Tooltip","Copy table to clipboard, OPTION or ALT click for tabular text",None))
        self.copyeventTableButton.setFocusPolicy(Qt.NoFocus)
        self.copyeventTableButton.setMaximumSize(self.copyeventTableButton.sizeHint())
        self.copyeventTableButton.setMinimumSize(self.copyeventTableButton.minimumSizeHint())
        self.copyeventTableButton.clicked.connect(self.copyEventTabletoClipboard)
        
        #DATA Table
        self.datatable = QTableWidget()
        self.datatable.setTabKeyNavigation(True)
        self.copydataTableButton = QPushButton(QApplication.translate("Button", "Copy Table",None))
        self.copydataTableButton.setToolTip(QApplication.translate("Tooltip","Copy table to clipboard, OPTION or ALT click for tabular text",None))
        self.copydataTableButton.setFocusPolicy(Qt.NoFocus)
        self.copydataTableButton.setMaximumSize(self.copydataTableButton.sizeHint())
        self.copydataTableButton.setMinimumSize(self.copydataTableButton.minimumSizeHint())
        self.copydataTableButton.clicked.connect(self.copyDataTabletoClipboard)
        #TITLE
        titlelabel = QLabel("<b>" + QApplication.translate("Label", "Title",None) + "</b>")
        self.titleedit = RoastsComboBox(self,self.aw,selection = self.aw.qmc.title)
        self.titleedit.setMinimumWidth(100)
        self.titleedit.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Fixed)
        self.titleedit.activated.connect(self.recentRoastActivated)
        self.titleedit.editTextChanged.connect(self.recentRoastEnabled)
        if sys.platform.startswith("darwin") and darkdetect.isDark() and appFrozen():
            if self.aw.qmc.palette["canvas"] is None or self.aw.qmc.palette["canvas"] == "None":
                canvas_color = "white"
            else:
                canvas_color = self.aw.qmc.palette["canvas"]
            brightness_title = self.aw.QColorBrightness(QColor(self.aw.qmc.palette["title"]))
            brightness_canvas = self.aw.QColorBrightness(QColor(canvas_color))
            # in dark mode we choose the darker color as background
            if brightness_title > brightness_canvas:
                backgroundcolor = QColor(canvas_color).name()
                color = QColor(self.aw.qmc.palette["title"]).name()
            else:
                backgroundcolor = QColor(self.aw.qmc.palette["title"]).name()
                color = QColor(canvas_color).name()
            self.titleedit.setStyleSheet(
                "QComboBox {font-weight: bold; background-color: " + backgroundcolor + "; color: " + color + ";} QComboBox QAbstractItemView {font-weight: normal;}")
        else:
            color = ""
            if self.aw.qmc.palette["title"] != None and self.aw.qmc.palette["title"] != "None":
                color = " color: " + QColor(self.aw.qmc.palette["title"]).name() + ";"
            backgroundcolor = ""
            if self.aw.qmc.palette["canvas"] != None and self.aw.qmc.palette["canvas"] != "None":
                backgroundcolor = " background-color: " + QColor(self.aw.qmc.palette["canvas"]).name() + ";"
            self.titleedit.setStyleSheet(
                "QComboBox {font-weight: bold;" + color + backgroundcolor + "} QComboBox QAbstractItemView {font-weight: normal;}")
        self.titleedit.setView(QListView())
        self.titleShowAlwaysFlag = QCheckBox(QApplication.translate("CheckBox","Show Always", None))
        self.titleShowAlwaysFlag.setChecked(self.aw.qmc.title_show_always)
        
        #Date
        datelabel1 = QLabel("<b>" + QApplication.translate("Label", "Date",None) + "</b>")
        date = self.aw.qmc.roastdate.date().toString()
        date += ", " + self.aw.qmc.roastdate.time().toString()[:-3]
        dateedit = QLineEdit(date)
        dateedit.setFocusPolicy(Qt.NoFocus)
        dateedit.setReadOnly(True)
        if sys.platform.startswith("darwin") and darkdetect.isDark() and appFrozen():
            dateedit.setStyleSheet("background-color: #757575; color : white;")
        else:
            dateedit.setStyleSheet("background-color: #eeeeee;")
        #Batch
        batchlabel = ClickableQLabel("<b>" + QApplication.translate("Label", "Batch",None) + "</b>")
        batchlabel.right_clicked.connect(self.enableBatchEdit)
        self.batchLayout = QHBoxLayout()
        if self.aw.superusermode: # and self.aw.qmc.batchcounter > -1:
            self.defineBatchEditor()
        else:
            batch = ""
            if self.aw.qmc.roastbatchnr != 0:
                roastpos = " (" + str(self.aw.qmc.roastbatchpos) + ")"
            else:
                roastpos = ""
            if self.aw.qmc.roastbatchnr == 0:
                batch = ""
            else:
                batch = self.aw.qmc.roastbatchprefix + str(self.aw.qmc.roastbatchnr) + roastpos
            self.batchedit = QLineEdit(batch)
            self.batchedit.setReadOnly(True)
            if sys.platform.startswith("darwin") and darkdetect.isDark() and appFrozen():
                self.batchedit.setStyleSheet("background-color: #757575; color : white;")
            else:
                self.batchedit.setStyleSheet("background-color: #eeeeee;")
            self.batchedit.setFocusPolicy(Qt.NoFocus)
            
        #Beans
        beanslabel = QLabel("<b>" + QApplication.translate("Label", "Beans",None) + "</b>")
        self.beansedit = ClickableTextEdit()
        self.beansedit.editingFinished.connect(self.beansEdited)
        
#        self.beansedit.setMaximumHeight(60)
        if self.aw.qmc.beans is not None:
            self.beansedit.setNewPlainText(self.aw.qmc.beans)
                    
        #roaster
        self.roaster = QLineEdit(self.aw.qmc.roastertype)
        self.roaster.setCursorPosition(0)
        #operator
        self.operator = QLineEdit(self.aw.qmc.operator)
        self.operator.setCursorPosition(0)
        #organization
        self.organization = QLineEdit(self.aw.qmc.organization)
        self.organization.setCursorPosition(0)
        #drum speed
        self.drumspeed = QLineEdit(self.aw.qmc.drumspeed)
        self.drumspeed.setAlignment(Qt.AlignCenter)
        self.drumspeed.setCursorPosition(0)
        #weight
        weightlabel = QLabel("<b>" + QApplication.translate("Label", "Weight",None) + "</b>")
        green_label = QLabel("<b>" + QApplication.translate("Label", "Green",None) + "</b>")
        roasted_label = QLabel("<b>" + QApplication.translate("Label", "Roasted",None) + "</b>")
        inw = "%g" % self.aw.float2floatWeightVolume(self.aw.qmc.weight[0])
        outw = "%g" % self.aw.float2floatWeightVolume(self.aw.qmc.weight[1])
        self.weightinedit = QLineEdit(inw)
        self.weightinedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, self.weightinedit))  # the max limit has to be high enough otherwise the connected signals are not send!
        self.weightinedit.setMinimumWidth(70)
        self.weightinedit.setMaximumWidth(70)
        self.weightinedit.setAlignment(Qt.AlignRight)
        self.weightoutedit = QLineEdit(outw)
        self.weightoutedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, self.weightoutedit))  # the max limit has to be high enough otherwise the connected signals are not send!
        self.weightoutedit.setMinimumWidth(70)
        self.weightoutedit.setMaximumWidth(70)
        self.weightoutedit.setAlignment(Qt.AlignRight)
        self.weightpercentlabel = QLabel(QApplication.translate("Label", "",None))
        self.weightpercentlabel.setMinimumWidth(55)
        self.weightpercentlabel.setMaximumWidth(55)
        self.weightpercentlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.roastdegreelabel = QLabel("")
        self.roastdegreelabel.setMinimumWidth(80)
        self.roastdegreelabel.setMaximumWidth(80)
        self.percent()
        self.weightinedit.editingFinished.connect(self.weightineditChanged)
        self.weightoutedit.editingFinished.connect(self.weightouteditChanged)
        self.unitsComboBox = QComboBox()
        self.unitsComboBox.setMaximumWidth(60)
        self.unitsComboBox.setMinimumWidth(60)
        self.unitsComboBox.addItems(self.aw.qmc.weight_units)
        self.unitsComboBox.setCurrentIndex(self.aw.qmc.weight_units.index(self.aw.qmc.weight[2]))
        self.unitsComboBox.currentIndexChanged.connect(self.changeWeightUnit)
        #volume
        volumelabel = QLabel("<b>" + QApplication.translate("Label", "Volume",None) + "</b>")
        inv = "%g" %  self.aw.float2floatWeightVolume(self.aw.qmc.volume[0])
        outv = "%g" % self.aw.float2floatWeightVolume(self.aw.qmc.volume[1])
        self.volumeinedit = QLineEdit(inv)
        self.volumeinedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999999., 4, self.volumeinedit)) # the max limit has to be high enough otherwise the connected signals are not send!
        self.volumeinedit.setMinimumWidth(70)
        self.volumeinedit.setMaximumWidth(70)
        self.volumeinedit.setAlignment(Qt.AlignRight)
        self.volumeoutedit = QLineEdit(outv)
        self.volumeoutedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999999., 4, self.volumeoutedit)) # the max limit has to be high enough otherwise the connected signals are not send!
        self.volumeoutedit.setMinimumWidth(70)
        self.volumeoutedit.setMaximumWidth(70)
        self.volumeoutedit.setAlignment(Qt.AlignRight)
        self.volumepercentlabel = QLabel(QApplication.translate("Label", " %",None))
        self.volumepercentlabel.setMinimumWidth(55)
        self.volumepercentlabel.setMaximumWidth(55)
        self.volumepercentlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.volumeoutedit.editingFinished.connect(self.volume_percent)
        self.volumeinedit.editingFinished.connect(self.volume_percent)
        self.volumeUnitsComboBox = QComboBox()
        self.volumeUnitsComboBox.setMaximumWidth(60)
        self.volumeUnitsComboBox.setMinimumWidth(60)
        self.volumeUnitsComboBox.addItems(self.aw.qmc.volume_units)
        self.volumeUnitsComboBox.setCurrentIndex(self.aw.qmc.volume_units.index(self.aw.qmc.volume[2]))
        self.volumeUnitsComboBox.currentIndexChanged.connect(self.changeVolumeUnit)
        self.unitsComboBox.currentIndexChanged.connect(self.calculated_density)
        #density
        bean_density_label = QLabel("<b>" + QApplication.translate("Label", "Density",None) + "</b>")
        density_unit_label = QLabel("g/l")
        self.bean_density_in_edit = QLineEdit("%g" % self.aw.float2float(self.aw.qmc.density[0]))
        self.bean_density_in_edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999999., 1,self.bean_density_in_edit))
        self.bean_density_in_edit.setMinimumWidth(70)
        self.bean_density_in_edit.setMaximumWidth(70)
        self.bean_density_in_edit.setAlignment(Qt.AlignRight)
        self.bean_density_out_edit = QLineEdit("%g" % self.aw.float2float(self.aw.qmc.density_roasted[0]))
        self.bean_density_out_edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999999., 1,self.bean_density_out_edit))
        self.bean_density_out_edit.setMinimumWidth(70)
        self.bean_density_out_edit.setMaximumWidth(70)
        self.bean_density_out_edit.setAlignment(Qt.AlignRight)
        self.bean_density_in_edit.editingFinished.connect(self.density_in_editing_finished)
        self.bean_density_out_edit.editingFinished.connect(self.density_out_editing_finished)
        self.densitypercentlabel = QLabel(QApplication.translate("Label", "",None))
        self.densitypercentlabel.setMinimumWidth(55)
        self.densitypercentlabel.setMaximumWidth(55)
        self.densitypercentlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.organicpercentlabel = QLabel(QApplication.translate("Label", "",None))
        self.organicpercentlabel.setMinimumWidth(55)
        self.organicpercentlabel.setMaximumWidth(55)
        self.organicpercentlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # volume calc button
        volumeCalcButton = QPushButton(QApplication.translate("Button", "calc",None))
        volumeCalcButton.clicked.connect(self.volumeCalculatorTimer)
        #the size of Buttons on the Mac is too small with 70,30 and ok with sizeHint/minimumSizeHint
        volumeCalcButton.setFocusPolicy(Qt.NoFocus)
        
        # add to recent
        self.addRecentButton = QPushButton("+")
        self.addRecentButton.clicked.connect(self.addRecentRoast)
        self.addRecentButton.setFocusPolicy(Qt.NoFocus)
        
        # delete from recent
        self.delRecentButton = QPushButton("-")
        self.delRecentButton.clicked.connect(self.delRecentRoast)
        self.delRecentButton.setFocusPolicy(Qt.NoFocus)

        self.recentRoastEnabled()
        
        #bean size
        bean_size_label = QLabel("<b>" + QApplication.translate("Label", "Screen",None) + "</b>")
        self.bean_size_min_edit = QLineEdit(str(int(round(self.aw.qmc.beansize_min))))
        self.bean_size_min_edit.editingFinished.connect(self.beanSizeMinEdited)
        self.bean_size_min_edit.setValidator(QIntValidator(0,50,self.bean_size_min_edit))
        self.bean_size_min_edit.setMinimumWidth(25)
        self.bean_size_min_edit.setMaximumWidth(25)
        self.bean_size_min_edit.setAlignment(Qt.AlignRight)
        bean_size_sep_label = QLabel("/")
        self.bean_size_max_edit = QLineEdit(str(int(round(self.aw.qmc.beansize_max))))
        self.bean_size_max_edit.editingFinished.connect(self.beanSizeMaxEdited)
        self.bean_size_max_edit.setValidator(QIntValidator(0,50,self.bean_size_max_edit))
        self.bean_size_max_edit.setMinimumWidth(25)
        self.bean_size_max_edit.setMaximumWidth(25)
        self.bean_size_max_edit.setAlignment(Qt.AlignRight)
        bean_size_unit_label = QLabel(QApplication.translate("Label", "18/64\u2033",None))
        #bean color
        color_label = QLabel("<b>" + QApplication.translate("Label", "Color",None) + "</b>")
        whole_color_label = QLabel("<b>" + QApplication.translate("Label", "Whole",None) + "</b>")
        self.whole_color_edit = QLineEdit(str(self.aw.qmc.whole_color))
        self.whole_color_edit.setValidator(QIntValidator(0, 1000, self.whole_color_edit))
        self.whole_color_edit.setMinimumWidth(70)
        self.whole_color_edit.setMaximumWidth(70)
        self.whole_color_edit.setAlignment(Qt.AlignRight)
        ground_color_label = QLabel("<b>" + QApplication.translate("Label", "Ground",None) + "</b>")
        self.ground_color_edit = QLineEdit(str(self.aw.qmc.ground_color))
        self.ground_color_edit.setValidator(QIntValidator(0, 1000, self.ground_color_edit))
        self.ground_color_edit.setMinimumWidth(70)
        self.ground_color_edit.setMaximumWidth(70)
        self.ground_color_edit.setAlignment(Qt.AlignRight)
        self.bean_size_min_edit.setAlignment(Qt.AlignRight)
        self.bean_size_max_edit.setAlignment(Qt.AlignRight)
        self.colorSystemComboBox = QComboBox()
        self.colorSystemComboBox.addItems(self.aw.qmc.color_systems)
        self.colorSystemComboBox.setCurrentIndex(self.aw.qmc.color_system_idx)
        #Greens Temp
        greens_temp_label = QLabel("<b>" + QApplication.translate("Label", "Beans",None) + "</b>")
        greens_temp_unit_label = QLabel(self.aw.qmc.mode)
        self.greens_temp_edit = QLineEdit()
        self.greens_temp_edit.setText("%g" % self.aw.float2float(self.aw.qmc.greens_temp))
        self.greens_temp_edit.setMaximumWidth(60)
        self.greens_temp_edit.setValidator(self.aw.createCLocaleDoubleValidator(-9999., 999999., 1, self.greens_temp_edit)) # range to 1000 needed to trigger editing_finished on input "12,2"
        self.greens_temp_edit.setAlignment(Qt.AlignRight)
        self.greens_temp_edit.editingFinished.connect(self.greens_temp_editing_finished)
        greens_temp = QHBoxLayout()
        greens_temp.addStretch()
        #Moisture Greens
        moisture_label = QLabel("<b>" + QApplication.translate("Label", "Moisture",None) + "</b>")
        moisture_greens_unit_label = QLabel(QApplication.translate("Label", "%",None))
        self.moisture_greens_edit = QLineEdit()
        self.moisture_greens_edit.setText("%g" % self.aw.float2float(self.aw.qmc.moisture_greens))
        self.moisture_greens_edit.setMaximumWidth(70)
        self.moisture_greens_edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 100., 1, self.moisture_greens_edit))
        self.moisture_greens_edit.setAlignment(Qt.AlignRight)
        #Moisture Roasted
        #bag humidity
        moisture_roasted_label = QLabel("<b>" + QApplication.translate("Label", "Roasted",None) + "</b>")
        moisture_roasted_unit_label = QLabel(QApplication.translate("Label", "%",None))
        self.moisture_roasted_edit = QLineEdit()
        self.moisture_roasted_edit.setText("%g" % self.aw.float2float(self.aw.qmc.moisture_roasted))
        self.moisture_roasted_edit.setMaximumWidth(70)
        self.moisture_roasted_edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 100., 1, self.moisture_roasted_edit))
        self.moisture_roasted_edit.setAlignment(Qt.AlignRight)
        self.moisturepercentlabel = QLabel(QApplication.translate("Label", "",None))
        self.moisturepercentlabel.setMinimumWidth(55)
        self.moisturepercentlabel.setMaximumWidth(55)
        self.moisturepercentlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.moisture_greens_edit.editingFinished.connect(self.moistureEdited)
        self.moisture_roasted_edit.editingFinished.connect(self.moistureEdited)

        moisture_roasted = QHBoxLayout()
        moisture_roasted.addWidget(moisture_roasted_label)
        moisture_roasted.addWidget(moisture_roasted_unit_label)
        moisture_roasted.addStretch()
        #Ambient temperature (uses display mode as unit (F or C)
        ambientlabel = QLabel("<b>" + QApplication.translate("Label", "Ambient Conditions",None) + "</b>")
        ambientunitslabel = QLabel(self.aw.qmc.mode)
        ambient_humidity_unit_label = QLabel(QApplication.translate("Label", "%",None))
        self.ambient_humidity_edit = QLineEdit()
        self.ambient_humidity_edit.setText("%g" % self.aw.float2float(self.aw.qmc.ambient_humidity))
        self.ambient_humidity_edit.setMinimumWidth(50)
        self.ambient_humidity_edit.setMaximumWidth(50)
        self.ambient_humidity_edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 1, self.ambient_humidity_edit))
        self.ambient_humidity_edit.setAlignment(Qt.AlignRight)
        self.ambient_humidity_edit.editingFinished.connect(self.ambient_humidity_editing_finished)
        self.ambientedit = QLineEdit()
        self.ambientedit.setText("%g" % self.aw.float2float(self.aw.qmc.ambientTemp))
        self.ambientedit.setMinimumWidth(50)
        self.ambientedit.setMaximumWidth(50)
        self.ambientedit.setValidator(self.aw.createCLocaleDoubleValidator(-9999., 9999999., 1, self.ambientedit))  # larger range needed to triger editing_finished
        self.ambientedit.setAlignment(Qt.AlignRight)
        self.ambientedit.editingFinished.connect(self.ambientedit_editing_finished)
        pressureunitslabel = QLabel("hPa")
        self.pressureedit = QLineEdit()
        self.pressureedit.setText("%g" % self.aw.float2float(self.aw.qmc.ambient_pressure))
        self.pressureedit.setMinimumWidth(55)
        self.pressureedit.setMaximumWidth(55)
        self.pressureedit.setValidator(self.aw.createCLocaleDoubleValidator(0, 9999999., 1, self.pressureedit))
        self.pressureedit.setAlignment(Qt.AlignRight)
        self.pressureedit.editingFinished.connect(self.pressureedit_editing_finished)
        ambient = QHBoxLayout()
        ambient.addWidget(self.ambient_humidity_edit)
        ambient.addSpacing(1)
        ambient.addWidget(ambient_humidity_unit_label)
        ambient.addSpacing(7)
        ambient.addWidget(self.ambientedit)
        ambient.addSpacing(1)
        ambient.addWidget(ambientunitslabel)
        ambient.addSpacing(7)
        ambient.addWidget(self.pressureedit)
        ambient.addSpacing(1)
        ambient.addWidget(pressureunitslabel)
        ambient.addStretch()
        self.organiclosslabel = QLabel()
        self.scaleWeight = QLabel()
        self.scaleWeightAccumulated = ClickableQLabel("")
        self.scaleWeightAccumulated.clicked.connect(self.resetScaleSet)
        # NOTES
        roastertypelabel = QLabel()
        roastertypelabel.setText("<b>" + QApplication.translate("Label", "Machine",None) + "</b>")
        operatorlabel = QLabel()
        operatorlabel.setText("<b> " + QApplication.translate("Label", "Operator",None) + "</b>")
        organizationlabel = QLabel()
        organizationlabel.setText("<b> " + QApplication.translate("Label", "Organization",None) + "</b>")
        drumspeedlabel = QLabel()
        drumspeedlabel.setText("<b> " + QApplication.translate("Label", "Drum Speed",None) + "</b>")
        roastinglabel = QLabel("<b>" + QApplication.translate("Label", "Roasting Notes",None) + "</b>")
        self.roastingeditor = QTextEdit()
#        self.roastingeditor.setMaximumHeight(125)
        if self.aw.qmc.roastingnotes is not None:
            self.roastingeditor.setPlainText(self.aw.qmc.roastingnotes)
        cuppinglabel = QLabel("<b>" + QApplication.translate("Label", "Cupping Notes",None) + "</b>")
        self.cuppingeditor =  QTextEdit()
#        self.cuppingeditor.setMaximumHeight(125)
        if self.aw.qmc.cuppingnotes is not None:
            self.cuppingeditor.setPlainText(self.aw.qmc.cuppingnotes)
        # Flags
        self.heavyFC = QCheckBox(QApplication.translate("CheckBox","Heavy FC", None))
        self.heavyFC.setChecked(self.aw.qmc.heavyFC_flag)
        self.heavyFC.stateChanged.connect(self.roastflagHeavyFCChanged)
        self.lowFC = QCheckBox(QApplication.translate("CheckBox","Low FC", None))
        self.lowFC.setChecked(self.aw.qmc.lowFC_flag)
        self.lowFC.stateChanged.connect(self.roastflagLowFCChanged)
        self.lightCut = QCheckBox(QApplication.translate("CheckBox","Light Cut", None))
        self.lightCut.setChecked(self.aw.qmc.lightCut_flag)
        self.lightCut.stateChanged.connect(self.roastflagLightCutChanged)
        self.darkCut = QCheckBox(QApplication.translate("CheckBox","Dark Cut", None))
        self.darkCut.setChecked(self.aw.qmc.darkCut_flag)
        self.darkCut.stateChanged.connect(self.roastflagDarkCutChanged)        
        self.drops = QCheckBox(QApplication.translate("CheckBox","Drops", None))
        self.drops.setChecked(self.aw.qmc.drops_flag)
        self.drops.stateChanged.connect(self.roastflagDropsChanged)
        self.oily = QCheckBox(QApplication.translate("CheckBox","Oily", None))
        self.oily.setChecked(self.aw.qmc.oily_flag)
        self.oily.stateChanged.connect(self.roastflagOilyChanged)
        self.uneven = QCheckBox(QApplication.translate("CheckBox","Uneven", None))
        self.uneven.setChecked(self.aw.qmc.uneven_flag)
        self.tipping = QCheckBox(QApplication.translate("CheckBox","Tipping", None))
        self.tipping.setChecked(self.aw.qmc.tipping_flag)
        self.scorching = QCheckBox(QApplication.translate("CheckBox","Scorching", None))
        self.scorching.setChecked(self.aw.qmc.scorching_flag)
        self.divots = QCheckBox(QApplication.translate("CheckBox","Divots", None))
        self.divots.setChecked(self.aw.qmc.divots_flag)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.accept)
        self.dialogbuttons.rejected.connect(self.cancel_dialog)
        
        # container tare
        self.tareComboBox = QComboBox()
        self.tareComboBox.addItem("<edit> TARE")
        self.tareComboBox.addItem("")
        self.tareComboBox.insertSeparator(1)
        self.tareComboBox.addItems(self.aw.qmc.container_names)
        self.tareComboBox.setMaximumWidth(80)
        self.tareComboBox.setMinimumWidth(80)
        self.tareComboBox.setCurrentIndex(self.aw.qmc.container_idx + 3)
        self.tareComboBox.currentIndexChanged.connect(self.tareChanged)
        self.tarePopupEnabled = True # controls if the popup will process tareChange events
        
        # in button
        inButton = QPushButton(QApplication.translate("Button", "in",None))
        inButton.clicked.connect(self.inWeight)
        #the size of Buttons on the Mac is too small with 70,30 and ok with sizeHint/minimumSizeHint
        inButton.setFocusPolicy(Qt.NoFocus)
        inButton.setMinimumWidth(70)
        inButtonLayout = QHBoxLayout()
        inButtonLayout.addStretch()
        inButtonLayout.addWidget(inButton)
        inButtonLayout.addStretch()
        # out button
        outButton = QPushButton(QApplication.translate("Button", "out",None))
        outButton.clicked.connect(self.outWeight)
        #the size of Buttons on the Mac is too small with 70,30 and ok with sizeHint/minimumSizeHint
        outButton.setFocusPolicy(Qt.NoFocus)
        outButton.setMinimumWidth(70)
        outButtonLayout = QHBoxLayout()
        outButtonLayout.addStretch()
        outButtonLayout.addWidget(outButton)
        outButtonLayout.addStretch()
        # scan whole button
        scanWholeButton = QPushButton(QApplication.translate("Button", "scan",None))
        scanWholeButton.clicked.connect(self.scanWholeColor)
        scanWholeButton.setMinimumWidth(80)
        #the size of Buttons on the Mac is too small with 70,30 and ok with sizeHint/minimumSizeHint
        scanWholeButton.setFocusPolicy(Qt.NoFocus)
        # scan ground button
        scanGroundButton = QPushButton(QApplication.translate("Button", "scan",None))
        scanGroundButton.setMinimumWidth(80)
        scanGroundButton.clicked.connect(self.scanGroundColor)
        #the size of Buttons on the Mac is too small with 70,30 and ok with sizeHint/minimumSizeHint
        scanGroundButton.setFocusPolicy(Qt.NoFocus)
        # Ambient Temperature Source Selector
        self.ambientComboBox = QComboBox()
        self.ambientComboBox.addItems(self.buildAmbientTemperatureSourceList())
        self.ambientComboBox.setCurrentIndex(self.aw.qmc.ambientTempSource)
        self.ambientComboBox.currentIndexChanged.connect(self.ambientComboBoxIndexChanged)
        ambientSourceLabel = QLabel(QApplication.translate("Label", "Ambient Source",None))
        updateAmbientTemp = QPushButton(QApplication.translate("Button", "update",None))
        updateAmbientTemp.setFocusPolicy(Qt.NoFocus)
        updateAmbientTemp.clicked.connect(self.updateAmbientTemp)
        ##### LAYOUTS
        timeLayout = QGridLayout()
        timeLayout.setVerticalSpacing(3)
        timeLayout.setHorizontalSpacing(3)
        timeLayout.addWidget(chargelabel,0,0)
        timeLayout.addWidget(drylabel,0,1)
        timeLayout.addWidget(Cstartlabel,0,2)
        timeLayout.addWidget(Cendlabel,0,3)
        timeLayout.addWidget(CCstartlabel,0,4)
        timeLayout.addWidget(CCendlabel,0,5)
        timeLayout.addWidget(droplabel,0,6)
        timeLayout.addWidget(coollabel,0,7)
        timeLayout.addWidget(self.chargeedit,1,0,Qt.AlignHCenter)
        timeLayout.addWidget(self.dryedit,1,1,Qt.AlignHCenter)
        timeLayout.addWidget(self.Cstartedit,1,2,Qt.AlignHCenter)
        timeLayout.addWidget(self.Cendedit,1,3,Qt.AlignHCenter)
        timeLayout.addWidget(self.CCstartedit,1,4,Qt.AlignHCenter)
        timeLayout.addWidget(self.CCendedit,1,5,Qt.AlignHCenter)
        timeLayout.addWidget(self.dropedit,1,6,Qt.AlignHCenter)
        timeLayout.addWidget(self.cooledit,1,7,Qt.AlignHCenter)
        textLayout = QGridLayout()
        textLayout.setHorizontalSpacing(3)
        textLayout.setVerticalSpacing(2)
        textLayout.setContentsMargins(0,0,0,0)
        textLayout.addWidget(datelabel1,0,0)
        datebatch = QHBoxLayout()
        datebatch.addWidget(dateedit)
        datebatch.addSpacing(15)
        datebatch.addWidget(batchlabel)
        datebatch.addSpacing(7)
        datebatch.addLayout(self.batchLayout)
        if not self.aw.superusermode: # and self.aw.qmc.batchcounter > -1:
            self.batchLayout.addWidget(self.batchedit)
        textLayout.addLayout(datebatch,0,1)
        
        titleLine = QHBoxLayout()
        titleLine.addWidget(self.titleedit)
        titleLine.addWidget(self.addRecentButton)
        titleLine.addWidget(self.delRecentButton)
        titleLine.addSpacing(2)
        titleLine.addWidget(self.titleShowAlwaysFlag) 
        
        self.template_line = QLabel("P249 Guatemala")
        template_font = self.template_line.font()
        template_font.setPointSize(template_font.pointSize() -1)
        self.template_line.setFont(template_font)
        
#PLUS
        self.plus_store_selected = None # holds the hr_id of the store of the selected coffee or blend
        self.plus_store_selected_label = None # the label of the selected store
        self.plus_coffee_selected = None # holds the hr_id of the selected coffee
        self.plus_coffee_selected_label = None # the label of the selected coffee
        self.plus_blend_selected_label = None # the name of the selected blend
        self.plus_blend_selected_spec = None # holds the blend dict specification of the selected blend
        self.plus_blend_selected_spec_labels = None # the list of coffee labels of the selected blend specification
        if self.aw.plus_account is not None:
            # variables populated by stock data as rendered in the corresponding popups
            self.plus_stores = None
            self.plus_coffees = None
            self.plus_blends = None
            self.plus_default_store = self.aw.qmc.plus_default_store
            # current selected stock/coffee/blend _id
            if self.aw.qmc.plus_store is not None:
                self.plus_store_selected = self.aw.qmc.plus_store # holds the store corresponding to the plus_coffee_selected/plus_blend_selected
                self.plus_store_selected_label = self.aw.qmc.plus_store_label
            if self.aw.qmc.plus_coffee is not None:
                self.plus_coffee_selected = self.aw.qmc.plus_coffee
                self.plus_coffee_selected_label = self.aw.qmc.plus_coffee_label
            else:
                if self.aw.qmc.plus_blend_spec is not None:
                    self.plus_blend_selected_label = self.aw.qmc.plus_blend_label
                    self.plus_blend_selected_spec = self.aw.qmc.plus_blend_spec
                    self.plus_blend_selected_spec_labels = self.aw.qmc.plus_blend_spec_labels
            self.plus_amount_selected = None # holds the max amount of the selected coffee/blend if known
            self.plus_amount_replace_selected = None # holds the max amount of the selected coffee/blend incl. replacements if known
            plusCoffeeslabel = QLabel("<b>" + QApplication.translate("Label", "Stock",None) + "</b>")
            self.plusStoreslabel = QLabel("<b>" + QApplication.translate("Label", "Store",None) + "</b>")
            self.plusBlendslabel = QLabel("<b>" + QApplication.translate("Label", "Blend",None) + "</b>")
            self.plus_stores_combo = MyQComboBox() 
            self.plus_coffees_combo = MyQComboBox()
            self.plus_blends_combo = MyQComboBox()
            self.plus_stores_combo.currentIndexChanged.connect(self.storeSelectionChanged)
            self.plus_coffees_combo.currentIndexChanged.connect(self.coffeeSelectionChanged)
            self.plus_blends_combo.currentIndexChanged.connect(self.blendSelectionChanged)
            self.plus_selected_line = QLabel()
            self.plus_selected_line.setOpenExternalLinks(True)
            label_font = self.plus_selected_line.font()
            label_font.setPointSize(label_font.pointSize() -2)
            self.plus_selected_line.setFont(label_font)
            self.populatePlusCoffeeBlendCombos()
            # layouting
            self.plus_coffees_combo.setMinimumContentsLength(15)
            self.plus_blends_combo.setMinimumContentsLength(10)
            self.plus_stores_combo.setMinimumContentsLength(10)
            self.plus_stores_combo.setMaximumWidth(120)            
            self.plus_coffees_combo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
            self.plus_coffees_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
            self.plus_blends_combo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
            self.plus_blends_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
            self.plus_stores_combo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
            self.plus_stores_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
            # plus widget row
            plusLine = QHBoxLayout()
            plusLine.addWidget(self.plus_coffees_combo)
            plusLine.addSpacing(15)
            plusLine.addWidget(self.plusBlendslabel)
            plusLine.addSpacing(5)
            plusLine.addWidget(self.plus_blends_combo)
            plusLine.addSpacing(15)
            plusLine.addWidget(self.plusStoreslabel)
            plusLine.addSpacing(5)
            plusLine.addWidget(self.plus_stores_combo)
            textLayout.addWidget(self.plus_selected_line,4,1)
            textLayout.addWidget(plusCoffeeslabel,5,0)
            textLayout.addLayout(plusLine,5,1)
            textLayoutPlusOffset = 2 # to insert the plus widget row, we move the remaining ones one step lower
        else:
            textLayoutPlusOffset = 0
        textLayout.addWidget(self.template_line,2,1)
        textLayout.addWidget(titlelabel,3,0)
        textLayout.addLayout(titleLine,3,1)
        textLayout.addWidget(beanslabel,4+textLayoutPlusOffset,0)
        textLayout.addWidget(self.beansedit,4+textLayoutPlusOffset,1)
        textLayout.addWidget(operatorlabel,5+textLayoutPlusOffset,0)
            
        roasteroperator = QHBoxLayout()
        roasteroperator.addWidget(self.operator, stretch=3)
        roasteroperator.addSpacing(8)
        roasteroperator.addWidget(organizationlabel)
        roasteroperator.addSpacing(2)
        roasteroperator.addWidget(self.organization, stretch=3)
        roasteroperator.addSpacing(8)
        roasteroperator.addWidget(roastertypelabel)
        roasteroperator.addSpacing(2)
        roasteroperator.addWidget(self.roaster,stretch=3)
        roasteroperator.addSpacing(8)
        roasteroperator.addWidget(drumspeedlabel)
        roasteroperator.addSpacing(2)
        roasteroperator.addWidget(self.drumspeed,stretch=1)
        textLayout.addLayout(roasteroperator,5+textLayoutPlusOffset,1)
        
        beanSizeLayout = QHBoxLayout()
        beanSizeLayout.setSpacing(2)
        beanSizeLayout.addStretch()
        beanSizeLayout.addWidget(self.bean_size_min_edit)
        beanSizeLayout.addWidget(bean_size_sep_label)
        beanSizeLayout.addWidget(self.bean_size_max_edit)
        beanSizeLayout.addStretch()
        
        propGrid = QGridLayout()
        propGrid.setContentsMargins(0,0,0,0)
        propGrid.setHorizontalSpacing(3)
        propGrid.setVerticalSpacing(0)
        propGrid.addWidget(green_label,0,1,Qt.AlignCenter | Qt.AlignBottom)
        propGrid.addWidget(roasted_label,0,2,Qt.AlignCenter | Qt.AlignBottom)
        propGrid.addWidget(self.organicpercentlabel,0,4,Qt.AlignRight)
        propGrid.addWidget(self.organiclosslabel,0,5,1,3,Qt.AlignLeft)
        propGrid.addWidget(self.scaleWeight,0,8,1,2,Qt.AlignCenter)
        
        propGrid.addWidget(weightlabel,1,0)
        propGrid.addWidget(self.weightinedit,1,1,Qt.AlignRight)
        propGrid.addWidget(self.weightoutedit,1,2,Qt.AlignRight)
        propGrid.addWidget(self.unitsComboBox,1,3)
        propGrid.addWidget(self.weightpercentlabel,1,4,Qt.AlignRight)
        
        propGrid.setColumnStretch(5,10)
        
        if self.aw.scale.device is not None and self.aw.scale.device != "" and self.aw.scale.device != "None":
            propGrid.addWidget(self.tareComboBox,1,7)
            propGrid.addLayout(inButtonLayout,1,8)
            propGrid.addLayout(outButtonLayout,1,9)
            
            if self.aw.scale.device == "acaia":
                try:
                    with suppress_stdout_stderr():
                        # if selected scale is the Acaia, start the BLE interface
                        from artisanlib.ble import BleInterface
                        from artisanlib.acaia import AcaiaBLE
                        acaia = AcaiaBLE()
                        self.ble = BleInterface(
                            acaia.SERVICE_UUID,
                            acaia.CHAR_UUID,
                            acaia.processData,
                            acaia.sendHeartbeat,
                            acaia.sendStop,
                            acaia.reset)
                            
                    # start BLE loop
                    self.ble.deviceDisconnected.connect(self.ble_scan_failed)
                    self.ble.weightChanged.connect(self.ble_weight_changed)
                    self.ble.batteryChanged.connect(self.ble_battery_changed)
                    self.ble.scanDevices()
                except:
                    pass
            elif self.aw.scale.device in ["KERN NDE","Shore 930"]:
                self.connectScaleSignal.connect(self.connectScaleLoop)
                QTimer.singleShot(2,lambda : self.connectScaleSignal.emit())
        
        propGrid.addWidget(volumelabel,2,0)
        propGrid.addWidget(self.volumeinedit,2,1,Qt.AlignRight)
        propGrid.addWidget(self.volumeoutedit,2,2,Qt.AlignRight)
        propGrid.addWidget(self.volumeUnitsComboBox,2,3)
        propGrid.addWidget(self.volumepercentlabel,2,4,Qt.AlignRight)
        propGrid.addWidget(self.scaleWeightAccumulated,2,7,1,2,Qt.AlignCenter)
        propGrid.addWidget(volumeCalcButton,2,9)
        
        propGrid.setRowMinimumHeight(3,self.volumeUnitsComboBox.minimumSizeHint().height())
        propGrid.addWidget(bean_density_label,3,0)
        propGrid.addWidget(self.bean_density_in_edit,3,1,Qt.AlignRight)
        propGrid.addWidget(self.bean_density_out_edit,3,2,Qt.AlignRight)
        propGrid.addWidget(density_unit_label,3,3,Qt.AlignCenter)
        propGrid.addWidget(self.densitypercentlabel,3,4,Qt.AlignRight)
        
        propGrid.addWidget(bean_size_label,3,7)
        propGrid.addLayout(beanSizeLayout,3,8,Qt.AlignRight)
        propGrid.addWidget(bean_size_unit_label,3,9,Qt.AlignCenter)
        
        propGrid.addWidget(moisture_label,4,0)
        propGrid.addWidget(self.moisture_greens_edit,4,1,Qt.AlignRight)
        propGrid.addWidget(self.moisture_roasted_edit,4,2,Qt.AlignRight)
        propGrid.addWidget(moisture_greens_unit_label,4,3,Qt.AlignCenter)
        propGrid.addWidget(self.moisturepercentlabel,4,4,Qt.AlignRight)
        propGrid.addWidget(greens_temp_label,4,7)
        propGrid.addWidget(self.greens_temp_edit,4,8,Qt.AlignRight)
        propGrid.addWidget(greens_temp_unit_label,4,9,Qt.AlignCenter)
        
        propGrid.setRowMinimumHeight(7,30)
        propGrid.addWidget(whole_color_label,7,1,Qt.AlignCenter | Qt.AlignBottom)
        propGrid.addWidget(ground_color_label,7,2,Qt.AlignCenter | Qt.AlignBottom)
        
        propGrid.addWidget(color_label,8,0)
        propGrid.addWidget(self.whole_color_edit,8,1,Qt.AlignRight)
        propGrid.addWidget(self.ground_color_edit,8,2,Qt.AlignRight)
        propGrid.addWidget(self.colorSystemComboBox,8,3,1, 2)
                
        if self.aw.color.device is not None and self.aw.color.device != "" and self.aw.color.device not in ["None","Tiny Tonino", "Classic Tonino"]:
            propGrid.addWidget(scanWholeButton,8,6)
        if self.aw.color.device is not None and self.aw.color.device != "" and self.aw.color.device != "None":
            propGrid.addWidget(scanGroundButton,8,7)
            
        propGrid.addWidget(ambientSourceLabel,8,8,1,2,Qt.AlignRight | Qt.AlignBottom)
        
        ambientGrid = QGridLayout()
        ambientGrid.setContentsMargins(0,0,0,0)
        ambientGrid.setHorizontalSpacing(3)
        ambientGrid.setVerticalSpacing(0)
        ambientGrid.addWidget(ambientlabel,2,0)
        ambientGrid.addLayout(ambient,2,2,1,5)
        ambientGrid.addWidget(updateAmbientTemp,2,10)
        ambientGrid.addWidget(self.ambientComboBox,2,11,Qt.AlignRight)
        ambientGrid.setColumnMinimumWidth(3, 11)
        ambientGrid.setColumnMinimumWidth(5, 11)
        ambientGrid.setColumnMinimumWidth(8, 11)
        roastFlagsLayout = QHBoxLayout()
        roastFlagsGrid = QGridLayout()
        roastFlagsGrid.addWidget(self.lowFC,0,0)
        roastFlagsGrid.addWidget(self.heavyFC,1,0)
        roastFlagsGrid.addWidget(self.lightCut,0,1)
        roastFlagsGrid.addWidget(self.darkCut,1,1)
        roastFlagsGrid.addWidget(self.drops,0,2)
        roastFlagsGrid.addWidget(self.oily,1,2)
        roastFlagsGrid.addWidget(self.uneven,0,3)
        roastFlagsGrid.addWidget(self.tipping,1,3)
        roastFlagsGrid.addWidget(self.scorching,0,4)
        roastFlagsGrid.addWidget(self.divots,1,4)
        roastFlagsLayout.addLayout(roastFlagsGrid)
        roastFlagsLayout.addStretch()
        anotationLayout = QVBoxLayout()
        anotationLayout.addWidget(roastinglabel)
        anotationLayout.addWidget(self.roastingeditor)
        anotationLayout.addLayout(roastFlagsLayout)
        anotationLayout.addWidget(cuppinglabel)
        anotationLayout.addWidget(self.cuppingeditor)
        okLayout = QHBoxLayout()
        okLayout.addWidget(self.roastproperties)
        okLayout.addStretch()
        okLayout.addSpacing(3)
        okLayout.addWidget(self.roastpropertiesAutoOpen)
        okLayout.addStretch()
        okLayout.addSpacing(3)
        okLayout.addWidget(self.roastpropertiesAutoOpenDROP)
        okLayout.addStretch()
        okLayout.addWidget(self.dialogbuttons)
        okLayout.setSpacing(10)
        okLayout.setContentsMargins(5, 15, 5, 15) # left, top, right, bottom
        timeLayoutBox = QHBoxLayout()
        timeLayoutBox.addStretch()
        timeLayoutBox.addLayout(timeLayout)
        timeLayoutBox.addStretch()
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(3, 3, 3, 3)
        eventbuttonLayout = QHBoxLayout()
        eventbuttonLayout.addWidget(self.copyeventTableButton)
        eventbuttonLayout.addWidget(self.createalarmTableButton)
        eventbuttonLayout.addStretch()
        eventbuttonLayout.addWidget(self.clusterEventsButton)
        eventbuttonLayout.addWidget(self.ordereventTableButton)
        eventbuttonLayout.addStretch()
        eventbuttonLayout.addWidget(self.clearEventsButton)
        eventbuttonLayout.addStretch()
        eventbuttonLayout.addWidget(self.deleventTableButton)
        eventbuttonLayout.addWidget(self.neweventTableButton)
        databuttonLayout = QHBoxLayout()
        databuttonLayout.addWidget(self.copydataTableButton)
        databuttonLayout.addStretch()
        #tab 1
        self.tab1aLayout = QVBoxLayout()
        self.tab1aLayout.setContentsMargins(0,0,0,0)
        self.tab1aLayout.setSpacing(0)
#        self.tab1aLayout.addLayout(mainLayout)
#        self.tab1aLayout.addStretch()
        self.tab1aLayout.addLayout(textLayout)
#        self.tab1aLayout.addStretch()
        self.tab1aLayout.setSpacing(8)
        self.tab1aLayout.addLayout(propGrid)
        self.tab1aLayout.addLayout(ambientGrid)
        tab1Layout = QVBoxLayout()
#        tab1Layout.addStretch()
        tab1Layout.setContentsMargins(5, 5, 5, 5) # left, top, right, bottom
        tab1Layout.addLayout(self.tab1aLayout)
        tab1Layout.setSpacing(0)
#        tab1Layout.addStretch()
        # set volume from density if given
        self.density_in_editing_finished()
        self.density_out_editing_finished()
        # set density from volume if given
        #tab 2
        tab2Layout = QVBoxLayout()
        tab2Layout.addLayout(anotationLayout)
        tab2Layout.setContentsMargins(5, 5, 5, 5) # left, top, right, bottom
        #tab3 events
        tab3Layout = QVBoxLayout()
        tab3Layout.addLayout(timeLayoutBox)
        tab3Layout.addWidget(self.eventtable)
        tab3Layout.addLayout(eventbuttonLayout)
        tab3Layout.setContentsMargins(5, 5, 5, 5) # left, top, right, bottom
        #tab 4 data
        tab4Layout = QVBoxLayout()
        tab4Layout.addWidget(self.datatable) 
        tab4Layout.addLayout(databuttonLayout)
        tab4Layout.setContentsMargins(5, 5, 5, 5) # left, top, right, bottom 
        #tabwidget
        self.TabWidget = QTabWidget()
        self.TabWidget.setContentsMargins(0,0,0,0)
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        self.TabWidget.addTab(C1Widget,QApplication.translate("Tab", "General",None))
        C2Widget = QWidget()
        C2Widget.setLayout(tab2Layout)
        self.TabWidget.addTab(C2Widget,QApplication.translate("Tab", "Notes",None))
        C3Widget = QWidget()
        C3Widget.setLayout(tab3Layout)
        self.TabWidget.addTab(C3Widget,QApplication.translate("Tab", "Events",None))
        C4Widget = QWidget()
        C4Widget.setLayout(tab4Layout)
        self.TabWidget.addTab(C4Widget,QApplication.translate("Tab", "Data",None)) 
        self.TabWidget.currentChanged.connect(self.tabSwitched)
        #incorporate layouts
        totallayout = QVBoxLayout()
        totallayout.addWidget(self.TabWidget)
        totallayout.addLayout(okLayout)
        totallayout.setContentsMargins(10,10,10,0)
        totallayout.setSpacing(0)
        self.volume_percent()
        self.setLayout(totallayout)
        
        self.TabWidget.setCurrentIndex(activeTab)

        self.titleedit.setFocus()

        self.updateTemplateLine()
        
        settings = QSettings()
        if settings.contains("RoastGeometry"):
            self.restoreGeometry(settings.value("RoastGeometry"))
        else:
            self.resize(self.minimumSizeHint())

#PLUS
        try:
            if self.aw.plus_account is not None:
                plus.stock.update()
                QTimer.singleShot(1500,lambda : self.populatePlusCoffeeBlendCombos())
        except:
            pass
        if platform.system() == 'Windows':
            self.dialogbuttons.button(QDialogButtonBox.Ok)
        else:
            self.dialogbuttons.button(QDialogButtonBox.Ok).setFocus()
    
    def enableBatchEdit(self):
        if not self.aw.superusermode and not self.batcheditmode:
            self.batcheditmode = True
            self.batchLayout.removeWidget(self.batchedit)
            self.defineBatchEditor()
    
    def defineBatchEditor(self):
        self.batchprefixedit = QLineEdit(self.aw.qmc.roastbatchprefix)
        self.batchcounterSpinBox = QSpinBox()
        self.batchcounterSpinBox.setRange(0,999999)
        self.batchcounterSpinBox.setSingleStep(1)
        self.batchcounterSpinBox.setValue(self.aw.qmc.roastbatchnr)
        self.batchcounterSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter) 
        self.batchposSpinBox = QSpinBox()
        self.batchposSpinBox.setRange(1,99)
        self.batchposSpinBox.setSingleStep(1)
        self.batchposSpinBox.setValue(self.aw.qmc.roastbatchpos)
        self.batchposSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.batchLayout.addWidget(self.batchprefixedit)
        self.batchLayout.addWidget(self.batchcounterSpinBox)
        self.batchLayout.addWidget(self.batchposSpinBox)
        
    def readScale(self):
        if self.disconnecting:
            self.aw.scale.closeport()
            self.scale_weight = None
            self.scale_battery = None
        else:
            if self.aw.scale.SP is None or not self.aw.scale.SP.isOpen():
                self.connectScaleSignal.emit()
            else:
                w,_,_ = self.aw.scale.readWeight()
                if w != -1:
                    self.scale_weight = w
                else:
                    self.scale_weight = None
                self.update_scale_weight()
                if self.volumedialog is not None:
                    self.scaleWeightUpdated.emit(w)
                self.readScaleSignal.emit()
    
    @pyqtSlot()
    def readScaleLoop(self):
        QTimer.singleShot(1000,lambda : self.readScale())
    
    @pyqtSlot()
    def connectScaleLoop(self):
        QTimer.singleShot(2000,lambda : self.connectScale())
        
    def connectScale(self):
        if self.disconnecting:
            self.aw.scale.closeport()
        else:
            res = self.aw.scale.connect(error=False)
            if res:
                self.readScaleSignal.connect(self.readScaleLoop)
                QTimer.singleShot(2,lambda : self.readScaleSignal.emit())
            else:
                self.connectScaleSignal.emit()

    @pyqtSlot()
    def resetScaleSet(self):
        self.scale_set = None
        self.updateScaleWeightAccumulated()
    
    def updateScaleWeightAccumulated(self,weight=None):
        if self.scale_set is None or weight is None:
            self.scaleWeightAccumulated.setText("")
        else:
            v = weight + self.scale_set
            if self.aw.qmc.weight_units.index(self.aw.qmc.weight[2]) in [0,1]:
                if v > 1000:
                    v_formatted = "{0:.2f}kg".format(v/1000)
                else:
                    v_formatted = "{0:.1f}g".format(v)
            # non-metric
            else:
                v = self.aw.convertWeight(v,0,self.aw.qmc.weight_units.index(self.aw.qmc.weight[2]))
                v_formatted = "{0:.2f}{1}".format(v,self.aw.qmc.weight[2])
            self.scaleWeightAccumulated.setText(v_formatted)

    def ble_scan_failed(self):
#        import datetime
#        ts = libtime.time()
#        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
#        print(st,"ble_scan_failed")
        self.scale_weight = None
        self.scale_battery = None
        self.scaleWeight.setText("")
        if self.ble is not None:
            QTimer.singleShot(200,lambda : self.ble.scanDevices())

    def ble_weight_changed(self,w):
        if w is not None:
            self.scale_weight = w
            self.update_scale_weight()
    
    def ble_battery_changed(self,b):
        if b is not None:
            self.scale_battery = b
            self.update_scale_weight()
            
    def update_scale_weight(self):
        tare = 0
        try:
            tare_idx = self.tareComboBox.currentIndex() - 3
            if tare_idx > -1:
                tare = self.aw.qmc.container_weights[tare_idx]
        except Exception:
            pass
        if self.scale_weight is not None and tare is not None:
            v = self.scale_weight - tare # weight in g
            unit = self.aw.qmc.weight_units.index(self.aw.qmc.weight[2])
            if unit == 0: # g selected
                # metric
                if v > 1000:
                    v_formatted = "{0:.0f}g".format(v)
                else:
                    v_formatted = "{0:.1f}g".format(v)
            elif unit == 1: # kg selected
                # metric (always keep the accuracy to the g
                v_formatted = "{0:.3f}kg".format(v/1000)
            # non-metric
            else:
                v = self.aw.convertWeight(v,0,self.aw.qmc.weight_units.index(self.aw.qmc.weight[2]))
                v_formatted = "{0:.2f}{1}".format(v,self.aw.qmc.weight[2])
            self.scaleWeight.setText(v_formatted)
            self.updateScaleWeightAccumulated(self.scale_weight - tare)
        else:
            self.scaleWeight.setText("")
            self.updateScaleWeightAccumulated()
            
    def updateTemplateLine(self):
        line = ""
        if self.template_file:
            if self.template_batchprefix:
                line = self.template_batchprefix
            if self.template_batchnr:
                line = line + str(self.template_batchnr)
            if self.template_name:
                if len(line) != 0:
                    line = line + " "
                line = line + self.template_name
        if len(line) > 0:
            line = QApplication.translate("Label", "Template",None) + ": " + line
        self.template_line.setText(line)
            
    def updatePlusSelectedLine(self):
        try:
            if sys.platform.startswith("darwin") and darkdetect.isDark() and appFrozen():
                dark_mode_link_color = " style=\"color: #e5e9ec;\""
            else:
                dark_mode_link_color = ""
            line = ""
            if self.plus_coffee_selected is not None and self.plus_coffee_selected_label:
                line = '<a href="{0}"{2}>{1}</a>'.format(plus.util.coffeeLink(self.plus_coffee_selected),self.plus_coffee_selected_label,dark_mode_link_color)
            elif self.plus_blend_selected_spec and self.plus_blend_selected_spec_labels:
                # limit to max 4 component links
                for i,l in sorted(zip(self.plus_blend_selected_spec["ingredients"],self.plus_blend_selected_spec_labels), key=lambda tup:tup[0]["ratio"],reverse = True)[:4]:
                    if line:
                        line = line + ", "
                    c = '<a href="{0}"{2}>{1}</a>'.format(plus.util.coffeeLink(i["coffee"]),self.aw.qmc.abbrevString(l,18),dark_mode_link_color)
                    line = line + str(int(round(i["ratio"]*100))) + "% " + c
            if line and len(line)>0 and self.plus_store_selected is not None and self.plus_store_selected_label is not None:
                line = line + '  (<a href="{0}"{2}>{1}</a>)'.format(plus.util.storeLink(self.plus_store_selected),self.plus_store_selected_label,dark_mode_link_color)
            self.plus_selected_line.setText(line)
        except Exception:
            pass
    
    @pyqtSlot()
    def beansEdited(self):
        self.modified_beans = self.beansedit.toPlainText()
    
    @pyqtSlot()
    def beanSizeMinEdited(self):
        self.modified_beansize_min_text = self.bean_size_min_edit.text()
    
    @pyqtSlot()
    def beanSizeMaxEdited(self):
        self.modified_beansize_max_text = self.bean_size_max_edit.text()

    @pyqtSlot()
    def moistureEdited(self):
        self.moisture_greens_edit.setText(self.aw.comma2dot(str(self.moisture_greens_edit.text())))
        self.moisture_roasted_edit.setText(self.aw.comma2dot(str(self.moisture_roasted_edit.text())))
        self.modified_moisture_greens_text = self.moisture_greens_edit.text()
        self.calculated_organic_loss()
        
    def plus_popups_set_enabled(self,b):
        try:
            self.plus_stores_combo.setEnabled(b)
            self.plus_coffees_combo.setEnabled(b)
            self.plus_blends_combo.setEnabled(b)
        except:
            pass

    # storeIndex is the index of the selected entry in the popup
    def populatePlusCoffeeBlendCombos(self,storeIndex=None):
        try: # this can crash if dialog got closed while this is processed in a different thread!
            self.plus_popups_set_enabled(False)
            
            #---- Stores
            
            if storeIndex is None or storeIndex == -1:
                self.plus_stores = plus.stock.getStores()
                try:
                    if len(self.plus_stores) == 1:
                        self.plus_default_store = plus.stock.getStoreId(self.plus_stores[0])
                    if len(self.plus_stores) < 2:
                        self.plusStoreslabel.setVisible(False)
                        self.plus_stores_combo.setVisible(False)
                    else:
                        self.plusStoreslabel.setVisible(True)
                        self.plus_stores_combo.setVisible(True)
                except:
                    pass
                self.plus_stores_combo.blockSignals(True)       
                self.plus_stores_combo.clear()
                store_items = plus.stock.getStoreLabels(self.plus_stores)
                # HACK to prevent those cutted menu items on macOS and Qt 5.15.1:
                if sys.platform.startswith("darwin"):
                    store_items = [l + "  " for l in store_items]
                self.plus_stores_combo.addItems([""] + store_items)
                p = plus.stock.getStorePosition(self.plus_default_store,self.plus_stores)
                if p is None:
                    self.plus_stores_combo.setCurrentIndex(0)
                else:
                    # we set to the default_store if available
                    self.plus_stores_combo.setCurrentIndex(p+1)
                self.plus_stores_combo.blockSignals(False)
            
            storeIdx = self.plus_stores_combo.currentIndex()
            
            # we reset the store if a coffee or blend is selected and the selected store is not equal to the default store
            # we clean the coffee/blend selection as it does not fit
            if storeIdx > 0 and (self.plus_coffee_selected or self.plus_blend_selected_spec) and self.plus_store_selected != plus.stock.getStoreId(self.plus_stores[storeIdx-1]):
                self.defaultCoffeeData()
                self.plus_amount_selected = None
                self.plus_store_selected_label = None
                if self.plus_coffee_selected:
                    self.plus_coffee_selected = None
                    self.plus_coffee_selected_label = None
                if self.plus_blend_selected_spec:
                    self.plus_blend_selected_label = None
                    self.plus_blend_selected_spec = None
                    self.plus_blend_selected_spec_labels = None
            
            if storeIdx:
                self.plus_default_store = plus.stock.getStoreId(self.plus_stores[storeIdx-1])
            else:
                self.plus_default_store = None
            
            mark_coffee_fields = False
            
            #---- Coffees
            
            self.plus_coffees = plus.stock.getCoffees(self.unitsComboBox.currentIndex(),self.plus_default_store)
            self.plus_coffees_combo.blockSignals(True)  
            self.plus_coffees_combo.clear()
            coffee_items = plus.stock.getCoffeesLabels(self.plus_coffees)
            # HACK to prevent those cutted menu items on macOS and Qt 5.15.1:
            if sys.platform.startswith("darwin"):
                coffee_items = [l + "  " for l in coffee_items]
            self.plus_coffees_combo.addItems([""] + coffee_items)
            
            p = None
            if self.plus_coffee_selected:
                p = plus.stock.getCoffeeStockPosition(self.plus_coffee_selected,self.plus_store_selected,self.plus_coffees)
            if p is None:
                # not in the current stock
                self.plus_coffees_combo.setCurrentIndex(0)
                #self.plus_coffee_selected = None # we don't "deselect" a coffee just because it is not in the popup!
                self.plus_coffees_combo.blockSignals(False)
            else:
                # if roast is complete (charge and drop are set) 
                if self.aw.qmc.timeindex[0] > -1 and self.aw.qmc.timeindex[6] > 0:
                    # we first change the index and then unblock signals to avoid properties being overwritten from the selected coffee
                    self.plus_coffees_combo.setCurrentIndex(p+1)
                    self.plus_coffees_combo.blockSignals(False)
                else:
                    # if roast is not yet complete we unblock the signals before changing the index to get the coffee data be filled in
                    self.plus_coffees_combo.blockSignals(False)
                    self.plus_coffees_combo.setCurrentIndex(p+1)
                mark_coffee_fields = True
            
            
            #---- Blends  
    
            self.plus_blends = plus.stock.getBlends(self.unitsComboBox.currentIndex(),self.plus_default_store)
            self.plus_blends_combo.blockSignals(True)  
            self.plus_blends_combo.clear()
            blend_items = plus.stock.getBlendLabels(self.plus_blends)
            # HACK to prevent those cutted menu items on macOS and Qt 5.15.1:
            if sys.platform.startswith("darwin"):
                blend_items = [l + "  " for l in blend_items]
            self.plus_blends_combo.addItems([""] + blend_items) 
            
            if len(self.plus_blends) == 0:
                self.plusBlendslabel.setVisible(False)
                self.plus_blends_combo.setVisible(False)
            else:
                self.plusBlendslabel.setVisible(True)
                self.plus_blends_combo.setVisible(True)
            
            p = None
            if self.plus_blend_selected_spec:
                p = plus.stock.getBlendSpecStockPosition(self.plus_blend_selected_spec,self.plus_store_selected,self.plus_blends)
            if p is None:
                self.plus_blends_combo.setCurrentIndex(0)
                #self.plus_blend_selected_spec = None # we don't deselect a blend just because it is not in the popup
                self.plus_blends_combo.blockSignals(False)
            else:
                # if roast is complete (charge and drop are set) 
                if self.aw.qmc.timeindex[0] > -1 and self.aw.qmc.timeindex[6] > 0:
                    # we first change the index and then unblock signals to avoid properties being overwritten from the selected blend
                    self.plus_blends_combo.setCurrentIndex(p+1)
                    self.plus_blends_combo.blockSignals(False)
                else:
                    # if roast is not yet complete we unblock the signals before changing the index to get the blend data be filled in
                    self.plus_blends_combo.blockSignals(False)
                    self.plus_blends_combo.setCurrentIndex(p+1)
                mark_coffee_fields = True

            self.markPlusCoffeeFields(mark_coffee_fields)
            self.updatePlusSelectedLine() 
        except:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            pass     
        finally:
            self.plus_popups_set_enabled(True)

    def markPlusCoffeeFields(self,b):
        # for QTextEdit
        if b:
            if sys.platform.startswith("darwin") and darkdetect.isDark() and appFrozen():
                self.beansedit.setStyleSheet("QTextEdit { background-color: #0D658F; selection-background-color: darkgray; }")
            else:
                self.beansedit.setStyleSheet("QTextEdit { background-color: #e4f3f8; selection-background-color: darkgray;  }")
        else:
            self.beansedit.setStyleSheet("")
        # for QLineEdit
        if b:
            if sys.platform.startswith("darwin") and darkdetect.isDark() and appFrozen():
                qlineedit_marked_style = "QLineEdit { background-color: #0D658F; selection-background-color: darkgray; }"
            else:
                qlineedit_marked_style = "QLineEdit { background-color: #e4f3f8; selection-background-color: #424242; }"
            self.bean_density_in_edit.setStyleSheet(qlineedit_marked_style)
            self.bean_size_min_edit.setStyleSheet(qlineedit_marked_style)
            self.bean_size_max_edit.setStyleSheet(qlineedit_marked_style)
            self.moisture_greens_edit.setStyleSheet(qlineedit_marked_style)
        else:
            background_white_style = "" 
            self.bean_density_in_edit.setStyleSheet(background_white_style)
            self.bean_size_min_edit.setStyleSheet(background_white_style)
            self.bean_size_max_edit.setStyleSheet(background_white_style)
            self.moisture_greens_edit.setStyleSheet(background_white_style)
        
    def updateTitle(self,prev_coffee_label,prev_blend_label):
        titles_to_be_overwritten = [ "", QApplication.translate("Scope Title", "Roaster Scope",None) ]
        if prev_coffee_label is not None:
            titles_to_be_overwritten.append(prev_coffee_label)
        if prev_blend_label is not None:
            titles_to_be_overwritten.append(prev_blend_label)
        if self.titleedit.currentText() in titles_to_be_overwritten:
            if self.plus_blend_selected_label is not None:
                self.titleedit.textEdited(self.plus_blend_selected_label)
                self.titleedit.setEditText(self.plus_blend_selected_label)
            elif self.plus_coffee_selected_label is not None:
                self.titleedit.textEdited(self.plus_coffee_selected_label)
                self.titleedit.setEditText(self.plus_coffee_selected_label)
            else:
                default_title = QApplication.translate("Scope Title", "Roaster Scope",None) 
                self.titleedit.textEdited(default_title)
                self.titleedit.setEditText(default_title)
    
    def updateBlendLines(self,blend):
        if self.weightinedit.text() != "":
            weightIn = float(self.aw.comma2dot(self.weightinedit.text()))
        else:
            weightIn = 0.0
        weight_unit_idx = self.unitsComboBox.currentIndex()
        blend_lines = plus.stock.blend2beans(blend,weight_unit_idx,weightIn)
        self.beansedit.clear()
        for l in blend_lines:
            self.beansedit.append(l)
    
    def fillBlendData(self,blend,prev_coffee_label,prev_blend_label):
        try:
            self.updateBlendLines(blend)
            keep_modified_moisture = self.modified_moisture_greens_text
            keep_modified_density = self.modified_density_in_text
            
            blend_dict = self.getBlendDictCurrentWeight(blend)
            
            moisture_txt = "0"
            try:
                if "moisture" in blend_dict and blend_dict["moisture"] is not None:
                    moisture_txt = "%g" % blend_dict["moisture"]
            except:
                pass
            self.moisture_greens_edit.setText(moisture_txt)
            density_txt = "0"
            try:
                if "density" in blend_dict and blend_dict["density"] is not None:
                    density_txt = "%g" % self.aw.float2float(blend_dict["density"])
            except:
                pass
            self.bean_density_in_edit.setText(density_txt)
            screen_size_min = "0"
            screen_size_max = "0"
            try:
                if "screen_min" in blend_dict and blend_dict["screen_min"] is not None:
                    screen_size_min = str(int(blend_dict["screen_min"]))
                if "screen_max" in blend_dict and blend_dict["screen_max"] is not None:
                    screen_size_max = str(int(blend_dict["screen_max"]))
            except:
                pass
            self.bean_size_min_edit.setText(screen_size_min)
            self.bean_size_max_edit.setText(screen_size_max)
            # check if title should be changed (if still default, or equal to the previous selection:
            self.updateTitle(prev_coffee_label,prev_blend_label)
            self.markPlusCoffeeFields(True)
            self.density_in_editing_finished()
            self.moistureEdited()
            self.modified_density_in_text = keep_modified_density
            self.modified_moisture_greens_text = keep_modified_moisture
        except:
            pass
        
    # if current title is equal to default title or prev_coffee/blend_label, we set title from selected label
    def fillCoffeeData(self,coffee,prev_coffee_label,prev_blend_label):
        try:
            cd = plus.stock.getCoffeeCoffeeDict(coffee)
            self.beansedit.setPlainText(plus.stock.coffee2beans(coffee))
            keep_modified_moisture = self.modified_moisture_greens_text
            keep_modified_density = self.modified_density_in_text
            moisture_txt = "0"
            try:
                if "moisture" in cd and cd["moisture"] is not None:
                    moisture_txt = "%g" % cd["moisture"]
            except:
                pass
            self.moisture_greens_edit.setText(moisture_txt)
            density_txt = "0"
            try:
                if "density" in cd and cd["density"] is not None:
                    density_txt = "%g" % self.aw.float2float(cd["density"])
            except:
                pass
            self.bean_density_in_edit.setText(density_txt)
            screen_size_min = "0"
            screen_size_max = "0"
            try:
                if "screen_size" in cd and cd["screen_size"] is not None:
                    screen = cd["screen_size"]
                    if "min" in screen and screen["min"] is not None:
                        screen_size_min = str(int(screen["min"]))
                    if "max" in screen and screen["max"] is not None:
                        screen_size_max = str(int(screen["max"]))
            except:
                pass
            self.bean_size_min_edit.setText(screen_size_min)
            self.bean_size_max_edit.setText(screen_size_max)
            self.updateTitle(prev_coffee_label,prev_blend_label)
            self.markPlusCoffeeFields(True)
            self.density_in_editing_finished()
            self.moistureEdited()
            self.modified_density_in_text = keep_modified_density
            self.modified_moisture_greens_text = keep_modified_moisture
        except:
            pass
        
    def defaultCoffeeData(self):
        if self.modified_beans is None:
            self.beansedit.clear()
        else:
            self.beansedit.setPlainText(self.modified_beans)
        self.bean_density_in_edit.setText(self.modified_density_in_text)
        self.volumeinedit.setText(self.modified_volume_in_text)
        self.bean_size_min_edit.setText(self.modified_beansize_min_text)
        self.bean_size_max_edit.setText(self.modified_beansize_max_text)
        self.moisture_greens_edit.setText(self.modified_moisture_greens_text)
        self.markPlusCoffeeFields(False)
        self.density_in_editing_finished()
        self.moistureEdited()
    
    @pyqtSlot(int)
    def storeSelectionChanged(self,n):
        if n != -1:
            prev_coffee_label = self.plus_coffee_selected_label
            prev_blend_label = self.plus_blend_selected_label
            self.populatePlusCoffeeBlendCombos(n)
            self.updateTitle(prev_coffee_label,prev_blend_label)
 
    @pyqtSlot(int)
    def coffeeSelectionChanged(self,n):
        # check for previously selected blend label
        prev_coffee_label = self.plus_coffee_selected_label
        prev_blend_label = self.plus_blend_selected_label
        if n < 1:
            self.defaultCoffeeData()
            self.plus_store_selected = None
            self.plus_store_selected_label = None
            self.plus_coffee_selected = None
            self.plus_coffee_selected_label = None
            self.plus_amount_selected = None
            self.plus_amount_replace_selected = None
            self.updateTitle(prev_coffee_label,prev_blend_label)
        else:
            # reset blend and set new coffee            
            self.plus_blends_combo.setCurrentIndex(0)
            selected_coffee = self.plus_coffees[n-1]
            sd = plus.stock.getCoffeeStockDict(selected_coffee)
            self.plus_store_selected = sd["location_hr_id"]
            self.plus_store_selected_label = sd["location_label"]
            cd = plus.stock.getCoffeeCoffeeDict(selected_coffee)
            self.plus_coffee_selected = cd["hr_id"]
            origin = ""
            if "origin" in cd:
                origin = cd["origin"] + " "
            picked = ""
            if "crop_date" in cd and "picked" in cd["crop_date"] and len(cd["crop_date"]["picked"]) > 0:
                picked = "{}, ".format(cd["crop_date"]["picked"][0])
            self.plus_coffee_selected_label = "{}{}{}".format(origin,picked,cd["label"])
            self.plus_blend_selected_label = None
            self.plus_blend_selected_spec = None
            self.plus_blend_selected_spec_labels = None
            if "amount" in plus.stock.getCoffeeStockDict(selected_coffee):
                self.plus_amount_selected = plus.stock.getCoffeeStockDict(selected_coffee)["amount"]
            else:
                self.pus_amount_selected = None
            self.plus_amount_replace_selected = None
            self.fillCoffeeData(selected_coffee,prev_coffee_label,prev_blend_label)
        self.checkWeightIn()
        self.updatePlusSelectedLine()
    
    def getBlendDictCurrentWeight(self,blend):
        if self.weightinedit.text() != "":
            weightIn = float(self.aw.comma2dot(self.weightinedit.text()))
        else:
            weightIn = 0.0
        weight_unit_idx = self.unitsComboBox.currentIndex()
        v = self.aw.convertWeight(weightIn,weight_unit_idx,self.aw.qmc.weight_units.index("Kg")) # v is weightIn converted to kg
        res = plus.stock.getBlendBlendDict(blend,v)
        return res
    
    @pyqtSlot(int)
    def blendSelectionChanged(self,n):
        # check for previously selected blend label
        prev_coffee_label = self.plus_coffee_selected_label
        prev_blend_label = self.plus_blend_selected_label
        if n < 1:
            self.defaultCoffeeData()
            self.plus_store_selected = None
            self.plus_store_selected_label = None
            self.plus_blend_selected_label = None
            self.plus_blend_selected_spec = None
            self.plus_blend_selected_spec_labels = None
            self.pus_amount_selected = None
            self.updateTitle(prev_coffee_label,prev_blend_label)
        else:
            # reset coffee and set new blend
            self.plus_coffees_combo.setCurrentIndex(0)
            selected_blend = self.plus_blends[n-1]
            bsd = plus.stock.getBlendStockDict(selected_blend)
            self.plus_store_selected = bsd["location_hr_id"]    
            self.plus_store_selected_label = bsd["location_label"]
            
            bd = self.getBlendDictCurrentWeight(selected_blend)
            self.plus_coffee_selected = None
            self.plus_blend_selected_label = bd["label"]
            self.plus_blend_selected_spec = dict(bd) # make a copy of the blend dict
# UPDATE: we keep the hr_id in to be able to adjust the blend with its replacements if needed
#            # we trim the blend_spec to the external from
#            self.plus_blend_selected_spec.pop("hr_id", None) # remove the hr_id
            
            self.plus_blend_selected_spec_labels = [i["label"] for i in self.plus_blend_selected_spec["ingredients"]]
            # remove labels from ingredients
            ingredients = []
            for i in self.plus_blend_selected_spec["ingredients"]:
                entry = {}
                entry["ratio"] = i["ratio"]
                entry["coffee"] = i["coffee"]
                if "ratio_num" in i and i["ratio_num"] is not None:
                    entry["ratio_num"] = i["ratio_num"]
                if "ratio_denom" in i and i["ratio_denom"] is not None:
                    entry["ratio_denom"] = i["ratio_denom"]
                ingredients.append(entry)
            self.plus_blend_selected_spec["ingredients"] = ingredients
            if "amount" in bsd:
                self.plus_amount_selected = plus.stock.getBlendMaxAmount(selected_blend)
                self.plus_amount_replace_selected = plus.stock.getBlendReplaceMaxAmount(selected_blend)
            else:
                self.plus_amount_selected = None
                self.plus_amount_replace_selected = None
            self.fillBlendData(selected_blend,prev_coffee_label,prev_blend_label)
            
        self.checkWeightIn()
        self.updatePlusSelectedLine()

    # recentRoast activated from within RoastProperties dialog
    def recentRoastActivated(self,n):
        # note, the first item is the edited text!
        if n > 0 and n <= len(self.aw.recentRoasts):
            rr = self.aw.recentRoasts[n-1]
            if "title" in rr and rr["title"] is not None:
                self.titleedit.textEdited(rr["title"])
                self.titleedit.setEditText(rr["title"])
            if "weightUnit" in rr and rr["weightUnit"] is not None:
                self.unitsComboBox.setCurrentIndex(self.aw.qmc.weight_units.index(rr["weightUnit"]))
            if "weightIn" in rr and rr["weightIn"] is not None:
                self.weightinedit.setText("%g" % rr["weightIn"])
            # all of the following items might not be in the dict
            if "beans" in rr and rr["beans"] is not None:
                self.beansedit.setPlainText(rr["beans"])
            if "weightOut" in rr and rr["weightOut"] is not None:
                self.weightoutedit.setText("%g" % rr["weightOut"])
            else:
                self.weightoutedit.setText("%g" % 0)
            if "volumeIn" in rr and rr["volumeIn"] is not None:
                self.volumeinedit.setText("%g" % rr["volumeIn"])
            if "volumeOut" in rr and rr["volumeOut"] is not None:
                self.volumeoutedit.setText("%g" % rr["volumeOut"])
            else:
                self.volumeoutedit.setText("%g" % 0)
            if "volumeUnit" in rr and rr["volumeUnit"] is not None:
                self.volumeUnitsComboBox.setCurrentIndex(self.aw.qmc.volume_units.index(rr["volumeUnit"]))
            if "densityWeight" in rr and rr["densityWeight"] is not None:
                self.bean_density_in_edit.setText("%g" % self.aw.float2float(rr["densityWeight"]))
            if "densityRoasted" in rr and rr["densityRoasted"] is not None:
                self.bean_density_out_edit.setText("%g" % self.aw.float2float(rr["densityRoasted"]))
            else:
                self.bean_density_out_edit.setText("%g" % 0)
            if "moistureGreen" in rr and rr["moistureGreen"] is not None:
                self.moisture_greens_edit.setText("%g" % self.aw.float2float(rr["moistureGreen"]))
            if "moistureRoasted" in rr and rr["moistureRoasted"] is not None:
                self.moisture_roasted_edit.setText("%g" % self.aw.float2float(rr["moistureRoasted"]))
            else:
                self.moisture_roasted_edit.setText("%g" % 0)
            if "wholeColor" in rr and rr["wholeColor"] is not None:
                self.whole_color_edit.setText(str(rr["wholeColor"]))
            else:
                self.whole_color_edit.setText(str(0))
            if "groundColor" in rr and rr["groundColor"] is not None:
                self.ground_color_edit.setText(str(rr["groundColor"]))
            else:
                self.ground_color_edit.setText(str(0))
            if "colorSystem" in rr and rr["colorSystem"] is not None:
                self.colorSystemComboBox.setCurrentIndex(rr["colorSystem"])
            # items added in v1.4 might not be in the data set of previous stored recent roasts
            if "beanSize_min" in rr and rr["beanSize_min"] is not None:
                self.bean_size_min_edit.setText(str(int(rr["beanSize_min"])))
            if "beanSize_max" in rr and rr["beanSize_max"] is not None:
                self.bean_size_max_edit.setText(str(int(rr["beanSize_max"])))
            # Note: the background profile will not be changed if recent roast is activated from Roast Properties
            if "background" in rr and rr["background"] is not None:
                self.template_file = rr["background"]
                if "title" in rr and rr["title"] is not None:
                    self.template_name = rr["title"]
                if "roastUUID" in rr and rr["roastUUID"] is not None:
                    self.template_uuid = rr["roastUUID"]
                if "batchnr" in rr and rr["batchnr"] is not None:
                    self.template_batchnr = rr["batchnr"]
                if "batchprefix" in rr and rr["batchprefix"] is not None:
                    self.template_batchprefix = rr["batchprefix"]
            else:
                self.template_file = None
                self.template_name = None
                self.template_uuid = None
                self.template_batchnr = None
                self.template_batchprefix = None
            self.updateTemplateLine()
            self.percent()

#PLUS
            if self.aw.plus_account is not None and "plus_account" in rr and self.aw.plus_account == rr["plus_account"]:
                if "plus_store" in rr:
                    self.plus_store_selected = rr["plus_store"]
                if "plus_store_label" in rr:
                    self.plus_store_selected_label = rr["plus_store_label"]
                if "plus_coffee" in rr:
                    self.plus_coffee_selected = rr["plus_coffee"]
                else:
                    self.plus_coffee_selected = None
                if "plus_coffee_label" in rr:
                    self.plus_coffee_selected_label = rr["plus_coffee_label"]
                else:
                    self.plus_coffee_selected_label = None
                if "plus_blend_spec" in rr:
                    self.plus_blend_selected_label = rr["plus_blend_label"]
                    self.plus_blend_selected_spec = rr["plus_blend_spec"]
                    if "plus_blend_spec_labels":
                        self.plus_blend_selected_spec_labels = rr["plus_blend_spec_labels"]
                else:
                    self.plus_blend_selected_label = None
                    self.plus_blend_selected_spec = None
                    self.plus_blend_selected_spec_labels = None
                if self.plus_store_selected is not None and self.plus_default_store is not None and self.plus_default_store != self.plus_store_selected:
                    self.plus_default_store = None # we reset the defaultstore
                # we now set the actual values from the stock
                self.populatePlusCoffeeBlendCombos()
                if False: #self.plus_blend_selected_spec is not None and "hr_id" in self.plus_blend_selected_spec:
                    # try to apply blend replacement
                    # search for the position of blend/location hr_id combo in self.plus_blends and call blendSelectionChanged with pos+1
                    try:
                        pos_in_blends = next(i for i, b in enumerate(self.plus_blends) if \
                            plus.stock.getBlendId(b) == self.plus_blend_selected_spec["hr_id"] and
                            plus.stock.getBlendStockDict(b)["location_hr_id"] == self.plus_store_selected)
                        self.blendSelectionChanged(pos_in_blends+1)
                    except:
                        self.updatePlusSelectedLine()
                else:
                    # blend replacements not applied
                    self.updatePlusSelectedLine()
            
            self.aw.sendmessage(QApplication.translate("Message","Recent roast properties '{0}' set".format(self.aw.recentRoastLabel(rr))))
        self.recentRoastEnabled()
    
    @pyqtSlot("QString")
    def recentRoastEnabled(self,_=""):
        try:
            title = self.titleedit.currentText()
            weightIn = float(self.aw.comma2dot(self.weightinedit.text()))
            # add new recent roast entry only if title is not default, beans is not empty and weight-in is not 0
            if title != QApplication.translate("Scope Title", "Roaster Scope",None) and weightIn != 0:
                # enable "+" addRecentRoast button
                self.addRecentButton.setEnabled(True)
                self.delRecentButton.setEnabled(True)
            else:
                self.addRecentButton.setEnabled(False)
                self.delRecentButton.setEnabled(False)
        except:
            self.addRecentButton.setEnabled(False)
            self.delRecentButton.setEnabled(False)
        
    @pyqtSlot(bool)
    def delRecentRoast(self,_):
        try:
            title = ' '.join(self.titleedit.currentText().split())
            weightIn = float(self.aw.comma2dot(self.weightinedit.text()))
            weightUnit = self.unitsComboBox.currentText()
            self.aw.recentRoasts = self.aw.delRecentRoast(title,weightIn,weightUnit)
        except:
            pass
    
    @pyqtSlot(bool)
    def addRecentRoast(self,_):
        try:
            title = ' '.join(self.titleedit.currentText().split())
            weightIn = float(self.aw.comma2dot(str(self.weightinedit.text())))
            # add new recent roast entry only if title is not default, beans is not empty and weight-in is not 0
            if title != QApplication.translate("Scope Title", "Roaster Scope",None) and weightIn != 0:
                beans = self.beansedit.toPlainText()
                weightUnit = self.unitsComboBox.currentText()
                if self.volumeinedit.text() != "":
                    volumeIn = float(self.aw.comma2dot(str(self.volumeinedit.text())))
                else:
                    volumeIn = 0
                volumeUnit = self.volumeUnitsComboBox.currentText()
                if self.bean_density_in_edit.text() != "":
                    densityWeight = float(self.aw.comma2dot(str(self.bean_density_in_edit.text())))
                else:
                    densityWeight = 0
                if self.bean_size_min_edit.text() != "":
                    beanSize_min = int(round(float(self.aw.comma2dot(self.bean_size_min_edit.text()))))
                else:
                    beanSize_min = 0
                if self.bean_size_max_edit.text() != "":
                    beanSize_max = int(round(float(self.aw.comma2dot(self.bean_size_max_edit.text()))))
                else:
                    beanSize_max = 0  
                if self.moisture_greens_edit.text() != "":
                    moistureGreen = float(self.aw.comma2dot(self.moisture_greens_edit.text()))
                else:
                    moistureGreen = 0.0
                colorSystem = self.colorSystemComboBox.currentIndex()
                
                modifiers = QApplication.keyboardModifiers()
                weightOut = volumeOut = densityRoasted = moistureRoasted = wholeColor = groundColor = None
                if modifiers == Qt.AltModifier:  #alt click
                    # we add weightOut, volumeOut, moistureRoasted, wholeColor, groundColor
                    weightOut = float(self.aw.comma2dot(str(self.weightoutedit.text())))
                    volumeOut = float(self.aw.comma2dot(str(self.volumeoutedit.text())))
                    densityRoasted = float(self.aw.comma2dot(str(self.bean_density_out_edit.text())))
                    moistureRoasted = float(self.aw.comma2dot(self.moisture_roasted_edit.text()))
                    wholeColor = int(self.whole_color_edit.text())
                    groundColor = int(self.ground_color_edit.text())
                                 
                rr = self.aw.createRecentRoast(
                    title,
                    beans,
                    weightIn,
                    weightUnit,
                    volumeIn,
                    volumeUnit,
                    densityWeight,
                    beanSize_min,
                    beanSize_max,
                    moistureGreen,
                    colorSystem,
                    self.aw.curFile, # could be empty
                    self.aw.qmc.roastUUID, # could be empty
                    self.aw.qmc.roastbatchnr, #self.batchcounterSpinBox # self.aw.superusermode and self.aw.qmc.batchcounter > -1
                    self.aw.qmc.roastbatchprefix,  #self.batchprefixedit
                    self.aw.plus_account,
                    self.plus_store_selected,
                    self.plus_store_selected_label,
                    self.plus_coffee_selected, 
                    self.plus_coffee_selected_label,
                    self.plus_blend_selected_label,
                    self.plus_blend_selected_spec,
                    self.plus_blend_selected_spec_labels,
                    weightOut,
                    volumeOut,
                    densityRoasted,
                    moistureRoasted, 
                    wholeColor, 
                    groundColor
                    )
                self.aw.addRecentRoast(rr)
        except Exception as e:
            #import traceback
            #traceback.print_exc(file=sys.stdout)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:",None) + " addRecentRoast(): {0}").format(str(e)),exc_tb.tb_lineno)

    # triggered if dialog is closed via its windows close box
    # and called from accept if dialog is closed via OK
    def closeEvent(self, _):
        self.disconnecting = True
        if self.ble is not None:
            try:
                self.ble.batteryChanged.disconnect()
                self.ble.weightChanged.disconnect()
                self.ble.deviceDisconnected.disconnect()
            except:
                pass
            try:
                self.ble.disconnectDevice()
            except:
                pass
        settings = QSettings()
        #save window geometry
        settings.setValue("RoastGeometry",self.saveGeometry())
        self.aw.editGraphDlg_activeTab = self.TabWidget.currentIndex()

    # triggered via the cancel button
    @pyqtSlot()
    def cancel_dialog(self):
        self.disconnecting = True
        if self.ble is not None:
            try:
                self.ble.batteryChanged.disconnect()
                self.ble.weightChanged.disconnect()
                self.ble.deviceDisconnected.disconnect()
            except:
                pass
            try:
                self.ble.disconnectDevice()
            except:
                pass
        settings = QSettings()
        #save window geometry
        settings.setValue("RoastGeometry",self.saveGeometry())
        self.aw.editGraphDlg_activeTab = self.TabWidget.currentIndex()
        
        self.aw.qmc.beans = self.org_beans
        self.aw.qmc.density = self.org_density
        self.aw.qmc.density_roasted = self.org_density_roasted
        self.aw.qmc.beansize_min = self.org_beansize_min
        self.aw.qmc.beansize_max = self.org_beansize_max
        self.aw.qmc.moisture_greens = self.org_moisture_greens
        
        self.aw.qmc.weight = self.org_weight
        self.aw.qmc.volume = self.org_volume
        
        self.aw.qmc.specialevents = self.org_specialevents
        self.aw.qmc.specialeventstype = self.org_specialeventstype
        self.aw.qmc.specialeventsStrings = self.org_specialeventsStrings
        self.aw.qmc.specialeventsvalue = self.org_specialeventsvalue
        self.aw.qmc.timeindex = self.org_timeindex
        
        self.aw.qmc.ambientTemp = self.org_ambientTemp
        self.aw.qmc.ambient_humidity = self.org_ambient_humidity
        self.aw.qmc.ambient_pressure = self.org_ambient_pressure
        
        self.aw.qmc.roastpropertiesAutoOpenFlag = self.org_roastpropertiesAutoOpenFlag
        self.aw.qmc.roastpropertiesAutoOpenDropFlag = self.org_roastpropertiesAutoOpenDropFlag
        
        self.reject()

    # calcs volume (in ml) from density (in g/l) and weight (in g)
    def calc_volume(self,density,weight):
        return (1./density) * weight * 1000

    #keyboard presses. There must not be widgets (pushbuttons, comboboxes, etc) in focus in order to work 
    def keyPressEvent(self,event):
        key = int(event.key())
        if event.matches(QKeySequence.Copy):
            if self.TabWidget.currentIndex() == 3: # datatable
                self.aw.copy_cells_to_clipboard(self.datatable,adjustment=1)
                self.aw.sendmessage(QApplication.translate("Message","Data table copied to clipboard",None))
        if key == 16777220 and self.aw.scale.device is not None and self.aw.scale.device != "" and self.aw.scale.device != "None": # ENTER key pressed and scale connected
            if self.weightinedit.hasFocus():
                self.inWeight(True,overwrite=True) # we don't add to current reading but overwrite
            elif self.weightoutedit.hasFocus():
                self.outWeight(True,overwrite=True) # we don't add to current reading but overwrite
    
    @pyqtSlot(int)
    def tareChanged(self,i):
        if i == 0 and self.tarePopupEnabled:
            tareDLG = tareDlg(self,self.aw,tarePopup=self)
            tareDLG.show()
            # reset index and popup
            self.tareComboBox.setCurrentIndex(self.aw.qmc.container_idx + 3)
        # update displayed scale weight
        self.update_scale_weight()
    
    @pyqtSlot(int)
    def changeWeightUnit(self,i):
        o = self.aw.qmc.weight_units.index(self.aw.qmc.weight[2]) # previous unit index
        self.aw.qmc.weight[2] = self.unitsComboBox.currentText()
        for le in [self.weightinedit,self.weightoutedit]:
            if le.text() and le.text() != "":
                wi = float(self.aw.comma2dot(le.text()))
                if wi != 0.0:
                    converted = self.aw.convertWeight(wi,o,i)
                    le.setText("%g" % self.aw.float2floatWeightVolume(converted))
        self.calculated_density()
#PLUS
        try:
            # weight unit changed, we update the selected blend in plus mode
            if self.plus_blends_combo.currentIndex() > 0:
                self.blendSelectionChanged(self.plus_blends_combo.currentIndex())
        except:
            pass

    @pyqtSlot(int)
    def changeVolumeUnit(self,i):
        o = self.aw.qmc.volume_units.index(self.aw.qmc.volume[2]) # previous unit index
        self.aw.qmc.volume[2] = self.volumeUnitsComboBox.currentText()
        for le in [self.volumeinedit,self.volumeoutedit]:
            if le.text() and le.text() != "":
                wi = float(self.aw.comma2dot(le.text()))
                if wi != 0.0:
                    converted = self.aw.convertVolume(wi,o,i)
                    le.setText("%g" % self.aw.float2floatWeightVolume(converted))
#        self.calculated_density() # if just the unit changes, the density will not change as it is fixed now

    @pyqtSlot(int)
    def tabSwitched(self,i):
        if i == 0:
            self.saveEventTable()
        elif i == 1:
            self.saveEventTable()
        elif i == 2:
            self.createEventTable()
        elif i == 3:
            self.saveEventTable()
            self.createDataTable()

    @pyqtSlot(int)
    def roastflagHeavyFCChanged(self,i):
        if i:
            self.lowFC.setChecked(False)
    @pyqtSlot(int)
    def roastflagLowFCChanged(self,i):
        if i:
            self.heavyFC.setChecked(False)
    @pyqtSlot(int)
    def roastflagLightCutChanged(self,i):
        if i:
            self.darkCut.setChecked(False)
    @pyqtSlot(int)
    def roastflagDarkCutChanged(self,i):
        if i:
            self.lightCut.setChecked(False)
    @pyqtSlot(int)
    def roastflagDropsChanged(self,i):
        if i:
            self.oily.setChecked(False)
    @pyqtSlot(int)
    def roastflagOilyChanged(self,i):
        if i:
            self.drops.setChecked(False)

    @pyqtSlot(int)
    def ambientComboBoxIndexChanged(self,i):
        self.aw.qmc.ambientTempSource = i

    def buildAmbientTemperatureSourceList(self):
        extra_names = []
        for i in range(len(self.aw.qmc.extradevices)):
            extra_names.append(str(i) + "xT1: " + self.aw.qmc.extraname1[i])
            extra_names.append(str(i) + "xT2: " + self.aw.qmc.extraname2[i])
        return ["",
                QApplication.translate("ComboBox","ET",None),
                QApplication.translate("ComboBox","BT",None)] + extra_names

    @pyqtSlot(bool)
    def updateAmbientTemp(self,_):
        self.aw.qmc.updateAmbientTemp()
        self.ambientedit.setText("%g" % self.aw.float2float(self.aw.qmc.ambientTemp))
        self.ambientedit.repaint() # seems to be necessary in some PyQt versions!?
        self.ambient_humidity_edit.setText("%g" % self.aw.float2float(self.aw.qmc.ambient_humidity))
        self.ambient_humidity_edit.repaint() # seems to be necessary in some PyQt versions!?
        self.pressureedit.setText("%g" % self.aw.float2float(self.aw.qmc.ambient_pressure))
        self.pressureedit.repaint() # seems to be necessary in some PyQt versions!?

    @pyqtSlot(bool)
    def scanWholeColor(self,_):
        v = self.aw.color.readColor()
        if v is not None and v > -1:
            if v >= 0 and v <= 250:
                self.aw.qmc.whole_color = v
                self.whole_color_edit.setText(str(v))

    @pyqtSlot(bool)
    def scanGroundColor(self,_):
        v = self.aw.color.readColor()
        if v is not None and v > -1:
            v = max(0,min(250,v))
            self.aw.qmc.ground_color = v
            self.ground_color_edit.setText(str(v))

    @pyqtSlot(bool)
    def volumeCalculatorTimer(self,_):
        QTimer.singleShot(1,lambda : self.volumeCalculator())

    def volumeCalculator(self):
        weightin = None
        weightout = None
        try:
            weightin = float(self.aw.comma2dot(self.weightinedit.text()))
        except Exception:
            pass
        try:
            weightout = float(self.aw.comma2dot(self.weightoutedit.text()))
        except Exception:
            pass
        k = 1.
        if weightin is not None:
            weightin = weightin * k
        else:
            weightin = None
        if weightout is not None:
            weightout = weightout * k
        else:
            weightout = None
        tare = 0
        try:
            tare_idx = self.tareComboBox.currentIndex() - 3
            if tare_idx > -1:
                tare = self.aw.qmc.container_weights[tare_idx]
        except Exception:
            pass
        self.volumedialog = volumeCalculatorDlg(self,self.aw,
            weightIn=weightin,
            weightOut=weightout,
            weightunit=self.unitsComboBox.currentIndex(),
            volumeunit=self.volumeUnitsComboBox.currentIndex(),
            inlineedit=self.volumeinedit,
            outlineedit=self.volumeoutedit,
            tare=tare)
        self.volumedialog.show()
        self.volumedialog.setFixedSize(self.volumedialog.size())

    @pyqtSlot(bool)
    def inWeight(self,_,overwrite=False):
        QTimer.singleShot(1,lambda : self.setWeight(self.weightinedit,self.bean_density_in_edit,self.moisture_greens_edit,overwrite))
    
    @pyqtSlot(bool)
    def outWeight(self,_=False,overwrite=False):
        QTimer.singleShot(1,lambda : self.setWeight(self.weightoutedit,self.bean_density_out_edit,self.moisture_roasted_edit,overwrite))

    def setWeight(self,weight_edit,density_edit,moisture_edit,overwrite=False):
        tare = 0
        try:
            tare_idx = self.tareComboBox.currentIndex() - 3
            if tare_idx > -1:
                tare = self.aw.qmc.container_weights[tare_idx]
        except Exception:
            pass
        #w,d,m = self.aw.scale.readWeight(self.scale_weight) # read value from scale in 'g'
        w,d,m = self.scale_weight,-1,-1
        if w is not None and w > -1:
            w = w - tare
            w = self.aw.convertWeight(w,0,self.aw.qmc.weight_units.index(self.aw.qmc.weight[2])) # convert to weight units
            current_w = 0
            try:
                current_w = float(self.aw.comma2dot(weight_edit.text()))
            except:
                pass
            if overwrite:
                new_w = w
            else:
                new_w = current_w + w # we add the new weight to the already existing one!
                self.scale_set = self.aw.convertWeight(new_w,self.aw.qmc.weight_units.index(self.aw.qmc.weight[2]),0) # convert to weight units
#            weight_edit.setText("%g" % self.aw.float2float(new_w))
            # updating this widget in a separate thread seems to be important on OS X 10.14 to avoid delayed updates and widget redraw problems
            # a QApplication.processEvents() or an weight_edit.update() seems not to help
            # no issue on OS X 10.13
            QTimer.singleShot(2,lambda : self.updateWeightEdits(weight_edit,new_w))
        if d is not None and d > -1:
            density_edit.setText("%g" % self.aw.float2float(d))
        if m is not None and m > -1:
            moisture_edit.setText("%g" % self.aw.float2float(m))
    
    def updateWeightEdits(self,weight_edit,w):
        unit = self.aw.qmc.weight_units.index(self.aw.qmc.weight[2])
        if unit == 0: # g selected
            decimals = 1
        elif unit == 1: # kg selected
            decimals = 3
        else:
            decimals = 2
        weight_edit.setText("%g" % self.aw.float2float(w,decimals))
        self.updateScaleWeightAccumulated(w)
        self.weightouteditChanged()
    
    @pyqtSlot(int)
    def roastpropertiesChanged(self,_=0):
        if self.roastproperties.isChecked():
            self.aw.qmc.roastpropertiesflag = 1
        else:
            self.aw.qmc.roastpropertiesflag = 0
            
    @pyqtSlot(int)
    def roastpropertiesAutoOpenChanged(self,_=0):
        if self.roastpropertiesAutoOpen.isChecked():
            self.aw.qmc.roastpropertiesAutoOpenFlag = 1
        else:
            self.aw.qmc.roastpropertiesAutoOpenFlag = 0
            
    @pyqtSlot(int)
    def roastpropertiesAutoOpenDROPChanged(self,_=0):
        if self.roastpropertiesAutoOpenDROP.isChecked():
            self.aw.qmc.roastpropertiesAutoOpenDropFlag = 1
        else:
            self.aw.qmc.roastpropertiesAutoOpenDropFlag = 0

    def createDataTable(self):
        self.datatable.clear()
        ndata = len(self.aw.qmc.timex)
        self.datatable.setRowCount(ndata)
        columns = [QApplication.translate("Table", "Time",None),
                                                  QApplication.translate("Table", "ET",None),
                                                  QApplication.translate("Table", "BT",None),
                                                  deltaLabelUTF8 + QApplication.translate("Label", "ET",None),
                                                  deltaLabelUTF8 + QApplication.translate("Label", "BT",None)]
        for i in range(len(self.aw.qmc.extratimex)):
            en1 = self.aw.qmc.extraname1[i]
            en2 = self.aw.qmc.extraname2[i]
            try:
                en1 = en1.format(self.aw.qmc.etypes[0],self.aw.qmc.etypes[1],self.aw.qmc.etypes[2],self.aw.qmc.etypes[3])
                en2 = en2.format(self.aw.qmc.etypes[0],self.aw.qmc.etypes[1],self.aw.qmc.etypes[2],self.aw.qmc.etypes[3])
            except:
                pass
            columns.append(en1)
            columns.append(en2)
#        columns.append("") # add a last dummy table that extends
        self.datatable.setColumnCount(len(columns))
        self.datatable.setHorizontalHeaderLabels(columns)
        self.datatable.setAlternatingRowColors(True)
        self.datatable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.datatable.setSelectionBehavior(QTableWidget.SelectRows)
        self.datatable.setSelectionMode(QTableWidget.ExtendedSelection) # QTableWidget.SingleSelection, ContiguousSelection, MultiSelection
        self.datatable.setShowGrid(True)
        self.datatable.verticalHeader().setSectionResizeMode(2)
        offset = 0
        if self.aw.qmc.timeindex[0] > -1:
            offset = self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        
        for i in range(ndata):
            Rtime = QTableWidgetItem(stringfromseconds(self.aw.qmc.timex[i]-offset))
            Rtime.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
            if self.aw.qmc.LCDdecimalplaces:
                fmtstr = "%.1f"
            else:
                fmtstr = "%.0f"
            ET = QTableWidgetItem(fmtstr%self.aw.qmc.temp1[i])
            BT = QTableWidgetItem(fmtstr%self.aw.qmc.temp2[i])
            ET.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
            BT.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)            
            deltaET_str = "--"
            try:
                if i > 0 and (self.aw.qmc.timex[i]-self.aw.qmc.timex[i-1]) and self.aw.qmc.temp1[i] != -1 and self.aw.qmc.temp1[i-1] != -1:
                    rateofchange1 = 60*(self.aw.qmc.temp1[i]-self.aw.qmc.temp1[i-1])/(self.aw.qmc.timex[i]-self.aw.qmc.timex[i-1])
                    if self.aw.qmc.DeltaETfunction is not None and len(self.aw.qmc.DeltaETfunction):
                        try:
                            rateofchange1 = self.aw.qmc.eval_math_expression(self.aw.qmc.DeltaETfunction,self.aw.qmc.timex[i],RTsname="R1",RTsval=rateofchange1)
                        except:
                            pass
                    deltaET_str = "%.1f"%(rateofchange1)
            except:
                pass
            deltaET = QTableWidgetItem(deltaET_str)
            deltaBT_str = "--"
            try:
                if i > 0 and (self.aw.qmc.timex[i]-self.aw.qmc.timex[i-1]) and self.aw.qmc.temp2[i] != -1 and self.aw.qmc.temp2[i-1] != -1:
                    rateofchange2 = 60*(self.aw.qmc.temp2[i]-self.aw.qmc.temp2[i-1])/(self.aw.qmc.timex[i]-self.aw.qmc.timex[i-1])
                    if self.aw.qmc.DeltaBTfunction is not None and len(self.aw.qmc.DeltaBTfunction):
                        try:
                            rateofchange2 = self.aw.qmc.eval_math_expression(self.aw.qmc.DeltaBTfunction,self.aw.qmc.timex[i],RTsname="R2",RTsval=rateofchange2)
                        except:
                            pass
                    deltaBT_str = "%.1f"%(rateofchange2)
            except:
                pass
            deltaBT = QTableWidgetItem(deltaBT_str)
            
            deltaET.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
            deltaBT.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
            if i in self.aw.qmc.specialevents:
                index = self.aw.qmc.specialevents.index(i)
                text = QApplication.translate("Table", "#{0} {1}{2}",None).format(str(index+1),self.aw.qmc.etypesf(self.aw.qmc.specialeventstype[index])[0],self.aw.qmc.eventsvalues(self.aw.qmc.specialeventsvalue[index]))
                Rtime.setText(text + " " + Rtime.text())
            self.datatable.setItem(i,0,Rtime)
            if i in self.aw.qmc.specialevents:
                self.datatable.item(i,0).setBackground(QColor('yellow'))
            
            if i:
                    #identify by color and add notation
                if i == self.aw.qmc.timeindex[0]:
                    self.datatable.item(i,0).setBackground(QColor('#f07800'))
                    text = QApplication.translate("Table", "CHARGE",None)
                elif i == self.aw.qmc.timeindex[1]:
                    self.datatable.item(i,0).setBackground(QColor('orange'))
                    text = QApplication.translate("Table", "DRY END",None)
                elif i == self.aw.qmc.timeindex[2]:
                    self.datatable.item(i,0).setBackground(QColor('orange'))
                    text = QApplication.translate("Table", "FC START",None)
                elif i == self.aw.qmc.timeindex[3]:
                    self.datatable.item(i,0).setBackground(QColor('orange'))
                    text = QApplication.translate("Table", "FC END",None)
                elif i == self.aw.qmc.timeindex[4]:
                    self.datatable.item(i,0).setBackground(QColor('orange'))
                    text = QApplication.translate("Table", "SC START",None)
                elif i == self.aw.qmc.timeindex[5]:
                    self.datatable.item(i,0).setBackground(QColor('orange'))
                    text = QApplication.translate("Table", "SC END",None)
                elif i == self.aw.qmc.timeindex[6]:
                    self.datatable.item(i,0).setBackground(QColor('#f07800'))
                    text = QApplication.translate("Table", "DROP",None)
                elif i == self.aw.qmc.timeindex[7]:
                    self.datatable.item(i,0).setBackground(QColor('orange'))
                    text = QApplication.translate("Table", "COOL",None)
                else:
                    text = ""
                Rtime.setText(text + " " + Rtime.text())
            else:
                Rtime.setText(" " + Rtime.text())
                            
            self.datatable.setItem(i,1,ET)
            self.datatable.setItem(i,2,BT)
            self.datatable.setItem(i,3,deltaET)
            self.datatable.setItem(i,4,deltaBT)
            j = 5
            for k in range(len(self.aw.qmc.extratimex)):
                if len(self.aw.qmc.extratemp1) > k:
                    value = -1
                    if len(self.aw.qmc.extratemp1[k]) > i:
                        value = self.aw.qmc.extratemp1[k][i]
                    extra_qtw1 = QTableWidgetItem(fmtstr%value)
                    extra_qtw1.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
                    self.datatable.setItem(i,j,extra_qtw1)
                    j = j + 1
                if len(self.aw.qmc.extratemp2) > k:
                    value = -1
                    if len(self.aw.qmc.extratemp2[k]) > i:
                        value = self.aw.qmc.extratemp2[k][i]
                    extra_qtw2 = QTableWidgetItem(fmtstr%value)
                    extra_qtw2.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
                    self.datatable.setItem(i,j,extra_qtw2)
                    j = j + 1

    def createEventTable(self):
        try:
            #### lock shared resources #####
            self.aw.qmc.samplingsemaphore.acquire(1)
            
            nevents = len(self.aw.qmc.specialevents)
            
            #self.eventtable.clear() # this crashes Ubuntu 16.04
    #        if nevents != 0:
    #            self.eventtable.clearContents() # this crashes Ubuntu 16.04 if device table is empty and also sometimes else
            self.eventtable.clearSelection() # this seems to work also for Ubuntu 16.04
            
            self.eventtable.setRowCount(nevents)
            self.eventtable.setColumnCount(6)
            self.eventtable.setHorizontalHeaderLabels([QApplication.translate("Table", "Time", None),
                                                       QApplication.translate("Table", "ET", None),
                                                       QApplication.translate("Table", "BT", None),
                                                       QApplication.translate("Table", "Description", None),
                                                       QApplication.translate("Table", "Type", None),
                                                       QApplication.translate("Table", "Value", None)])
            self.eventtable.setAlternatingRowColors(True)
            self.eventtable.setEditTriggers(QTableWidget.NoEditTriggers)
            self.eventtable.setSelectionBehavior(QTableWidget.SelectRows)
            self.eventtable.setSelectionMode(QTableWidget.ExtendedSelection)

            self.eventtable.setShowGrid(True)
            
            self.eventtable.verticalHeader().setSectionResizeMode(2)
            regextime = QRegularExpression(r"^-?[0-9]?[0-9]?[0-9]:[0-5][0-9]$")
            etypes = self.aw.qmc.getetypes()
            #populate table
            for i in range(nevents):
                #create widgets
                typeComboBox = MyQComboBox()
                typeComboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)
                typeComboBox.addItems(etypes)
                typeComboBox.setCurrentIndex(self.aw.qmc.specialeventstype[i])
    
                if self.aw.qmc.LCDdecimalplaces:
                    fmtstr = "%.1f"
                else:
                    fmtstr = "%.0f"
    
                etline = QLineEdit()
                etline.setReadOnly(True)
                etline.setAlignment(Qt.AlignRight)
                try:
                    ettemp = fmtstr%(self.aw.qmc.temp1[self.aw.qmc.specialevents[i]]) + self.aw.qmc.mode
                except:
                    pass
                etline.setText(ettemp)
                    
                btline = QLineEdit()
                btline.setReadOnly(True)
                btline.setAlignment(Qt.AlignRight)
                bttemp = fmtstr%(self.aw.qmc.temp2[self.aw.qmc.specialevents[i]]) + self.aw.qmc.mode
                btline.setText(bttemp)
                
                valueEdit = QLineEdit()
                valueEdit.setAlignment(Qt.AlignRight)
                valueEdit.setText(self.aw.qmc.eventsvalues(self.aw.qmc.specialeventsvalue[i]))
                
                timeline = QLineEdit()
                timeline.setAlignment(Qt.AlignRight)
                if self.aw.qmc.timeindex[0] > -1 and len(self.aw.qmc.timex) > self.aw.qmc.timeindex[0]:
                    timez = stringfromseconds(self.aw.qmc.timex[self.aw.qmc.specialevents[i]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]])
                else:
                    timez = stringfromseconds(self.aw.qmc.timex[self.aw.qmc.specialevents[i]])
                timeline.setText(timez)
                timeline.setValidator(QRegularExpressionValidator(regextime,self))
                
                try:
                    stringline = QLineEdit(self.aw.qmc.specialeventsStrings[i])
                except:
                    stringline = QLineEdit("")
                #add widgets to the table
                self.eventtable.setCellWidget(i,0,timeline)
                self.eventtable.setCellWidget(i,1,etline)
                self.eventtable.setCellWidget(i,2,btline)
                self.eventtable.setCellWidget(i,3,stringline)
                self.eventtable.setCellWidget(i,4,typeComboBox)
                self.eventtable.setCellWidget(i,5,valueEdit)
                valueEdit.setValidator(QIntValidator(0,self.aw.eventsMaxValue,self.eventtable.cellWidget(i,5)))
            header = self.eventtable.horizontalHeader()
            #header.setStretchLastSection(True)
            header.setSectionResizeMode(0, QHeaderView.Fixed)
            header.setSectionResizeMode(1, QHeaderView.Fixed)
            header.setSectionResizeMode(2, QHeaderView.Fixed)
            header.setSectionResizeMode(3, QHeaderView.Stretch)
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.Fixed)
            # improve width of Time column
            self.eventtable.setColumnWidth(0,60)
            self.eventtable.setColumnWidth(1,65)
            self.eventtable.setColumnWidth(2,65)
            self.eventtable.setColumnWidth(5,55)
            # header.setSectionResizeMode(QHeaderView.Stretch)
        finally:
            if self.aw.qmc.samplingsemaphore.available() < 1:
                self.aw.qmc.samplingsemaphore.release(1)


    def saveEventTable(self):
        try:
            #### lock shared resources #####
            self.aw.qmc.samplingsemaphore.acquire(1)
            nevents = self.eventtable.rowCount()
            for i in range(nevents):
                try:
                    timez = self.eventtable.cellWidget(i,0)
                    if self.aw.qmc.timeindex[0] > -1:
                        self.aw.qmc.specialevents[i] = self.aw.qmc.time2index(self.aw.qmc.timex[self.aw.qmc.timeindex[0]]+ stringtoseconds(str(timez.text())))
                    else:
                        self.aw.qmc.specialevents[i] = self.aw.qmc.time2index(stringtoseconds(str(timez.text())))
                    description = self.eventtable.cellWidget(i,3)
                    self.aw.qmc.specialeventsStrings[i] = description.text()
                    etype = self.eventtable.cellWidget(i,4)
                    self.aw.qmc.specialeventstype[i] = etype.currentIndex()
                    evalue = self.eventtable.cellWidget(i,5).text()
                    self.aw.qmc.specialeventsvalue[i] = self.aw.qmc.str2eventsvalue(str(evalue))
                except:
                    pass
        finally:
            if self.aw.qmc.samplingsemaphore.available() < 1:
                self.aw.qmc.samplingsemaphore.release(1)

    @pyqtSlot(bool)
    def copyDataTabletoClipboard(self,_=False):
        self.aw.copy_cells_to_clipboard(self.datatable,adjustment=5)
        self.aw.sendmessage(QApplication.translate("Message","Data table copied to clipboard",None))

    @pyqtSlot(bool)
    def copyEventTabletoClipboard(self,_=False):
        nrows = self.eventtable.rowCount() 
        ncols = self.eventtable.columnCount()
        clipboard = ""
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.AltModifier:  #alt click
            tbl = prettytable.PrettyTable()
            fields = []
            for c in range(ncols):
                fields.append(self.eventtable.horizontalHeaderItem(c).text())
            tbl.field_names = fields
            for i in range(nrows):
                rows = []
                rows.append(self.eventtable.cellWidget(i,0).text())
                rows.append(self.eventtable.cellWidget(i,1).text())
                rows.append(self.eventtable.cellWidget(i,2).text())
                rows.append(self.eventtable.cellWidget(i,3).text())
                rows.append(self.eventtable.cellWidget(i,4).currentText())
                rows.append(self.eventtable.cellWidget(i,5).text())
                tbl.add_row(rows)
            clipboard = tbl.get_string()
        else:
            for c in range(ncols):
                clipboard += self.eventtable.horizontalHeaderItem(c).text()
                if c != (ncols-1):
                    clipboard += '\t'
            clipboard += '\n'
            for r in range(nrows):
                clipboard += self.eventtable.cellWidget(r,0).text() + "\t"
                clipboard += self.eventtable.cellWidget(r,1).text() + "\t"
                clipboard += self.eventtable.cellWidget(r,2).text() + "\t"
                clipboard += self.eventtable.cellWidget(r,3).text() + "\t"
                clipboard += self.eventtable.cellWidget(r,4).currentText() + "\t"
                clipboard += self.eventtable.cellWidget(r,5).text() + "\n"
        # copy to the system clipboard
        sys_clip = QApplication.clipboard()
        sys_clip.setText(clipboard)
        self.aw.sendmessage(QApplication.translate("Message","Event table copied to clipboard",None))

    def createAlarmEventRows(self,rows):
        for r in rows:
            TP = self.aw.findTP()
            if TP:
                self.aw.qmc.alarmflag.append(1)
                self.aw.qmc.alarmguard.append(-1)
                self.aw.qmc.alarmnegguard.append(-1)
                tx = self.aw.qmc.timex[self.aw.qmc.specialevents[r]] - self.aw.qmc.timex[TP]
                ev = 8 # TP
                if tx < 0: # events before TP are moved to CHARGE
                    tx = 1 # set to one second after
                    ev = 0 # CHARGE
                self.aw.qmc.alarmoffset.append(tx) # seconds after TP
                self.aw.qmc.alarmtime.append(ev)
                self.aw.qmc.alarmcond.append(1) # rises above (we assume that BT always rises after TP)
                self.aw.qmc.alarmstate.append(-1) # not yet triggered
                self.aw.qmc.alarmsource.append(1) # 1=BT
                self.aw.qmc.alarmtemperature.append(float(round(self.aw.qmc.temp2[self.aw.qmc.specialevents[r]]))) # the BT trigger temperature
                self.aw.qmc.alarmaction.append(self.aw.qmc.specialeventstype[r] + 3) # 3,4,5,6 for slider 0-3
                self.aw.qmc.alarmbeep.append(0)
                self.aw.qmc.alarmstrings.append(str(int(self.aw.qmc.specialeventsvalue[r]*10 - 10)))
        
    @pyqtSlot(bool)
    def clusterEvents(self,_=False):
        nevents = len(self.aw.qmc.specialevents)
        if nevents:
            self.aw.clusterEvents()
            self.createEventTable()
            self.aw.qmc.redraw(recomputeAllDeltas=False)
            self.aw.qmc.fileDirty()
            
    @pyqtSlot(bool)
    def clearEvents(self,_=False):
        try:
            #### lock shared resources #####
            self.aw.qmc.samplingsemaphore.acquire(1)
            nevents = len(self.aw.qmc.specialevents)
            if nevents:
                self.aw.qmc.specialevents = []
                self.aw.qmc.specialeventstype = []
                self.aw.qmc.specialeventsStrings = []
                self.aw.qmc.specialeventsvalue = []
        finally:
            if self.aw.qmc.samplingsemaphore.available() < 1:
                self.aw.qmc.samplingsemaphore.release(1)
        self.createEventTable()
        self.aw.qmc.redraw(recomputeAllDeltas=False)
        self.aw.qmc.fileDirty()
    
    @pyqtSlot(bool)
    def createAlarmEventTable(self,_=False):
        if len(self.aw.qmc.specialevents):
            # check for selection
            selected = self.eventtable.selectedRanges()
            if selected and len(selected) > 0:
                rows = []
                for s in selected:
                    top = s.topRow()
                    for x in range(s.rowCount()):
                        rows.append(top + x)
                #rows = [s.topRow() for s in selected]
                self.createAlarmEventRows(rows)
                message = QApplication.translate("Message","Alarms from events #{0} created", None).format(str([r+1 for r in rows]))
            else:
                rows = range(self.eventtable.rowCount())
                self.createAlarmEventRows(rows)
                message = QApplication.translate("Message","Alarms from events #{0} created", None).format(str([r+1 for r in rows]))
            self.aw.sendmessage(message)
        else:
            message = QApplication.translate("Message","No events found", None)
            self.aw.sendmessage(message)
    
    @pyqtSlot(bool)
    def orderEventTable(self,_=False):
        self.saveEventTable()
        self.orderEventTableLoop()
        self.aw.qmc.fileDirty()
        
    def orderEventTableLoop(self):
        nevents = len(self.aw.qmc.specialevents)
        if nevents:
            self.aw.orderEvents()
            self.createEventTable()
            self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(bool)
    def addEventTable(self,_=False):
        if len(self.aw.qmc.timex):
            self.saveEventTable()
            self.aw.qmc.specialevents.append(len(self.aw.qmc.timex)-1)   #qmc.specialevents holds indexes in qmx.timex. Initialize event index
            self.aw.qmc.specialeventstype.append(0)
            self.aw.qmc.specialeventsStrings.append(str(len(self.aw.qmc.specialevents)))
            self.aw.qmc.specialeventsvalue.append(0)
            self.createEventTable()
            self.aw.qmc.redraw(recomputeAllDeltas=False)
            message = QApplication.translate("Message","Event #{0} added", None).format(str(len(self.aw.qmc.specialevents))) 
            self.aw.sendmessage(message)
        else:
            message = QApplication.translate("Message","No profile found", None)
            self.aw.sendmessage(message)
            
    def deleteEventRows(self,rows):
        specialevents = []
        specialeventstype = []
        specialeventsStrings = []
        specialeventsvalue = []
        for r in range(len(self.aw.qmc.specialevents)):
            if not (r in rows):
                specialevents.append(self.aw.qmc.specialevents[r])
                specialeventstype.append(self.aw.qmc.specialeventstype[r])
                specialeventsStrings.append(self.aw.qmc.specialeventsStrings[r])
                specialeventsvalue.append(self.aw.qmc.specialeventsvalue[r])
        self.aw.qmc.specialevents = specialevents
        self.aw.qmc.specialeventstype = specialeventstype
        self.aw.qmc.specialeventsStrings = specialeventsStrings
        self.aw.qmc.specialeventsvalue = specialeventsvalue
    
    @pyqtSlot(bool)
    def deleteEventTable(self,_=False):
        if len(self.aw.qmc.specialevents):
            self.saveEventTable()
            # check for selection
            selected = self.eventtable.selectedRanges()
            if selected and len(selected) > 0:
                rows = []
                for s in selected:
                    top = s.topRow()
                    for x in range(s.rowCount()):
                        rows.append(top + x)
                self.deleteEventRows(rows)
                message = QApplication.translate("Message"," Events #{0} deleted", None).format(str([r+1 for r in rows]))
            else:
                self.aw.qmc.specialevents.pop()
                self.aw.qmc.specialeventstype.pop()
                self.aw.qmc.specialeventsStrings.pop()
                self.aw.qmc.specialeventsvalue.pop()
                message = QApplication.translate("Message"," Event #{0} deleted", None).format(str(len(self.aw.qmc.specialevents)+1))
            self.aw.qmc.fileDirty()
            self.createEventTable()
            self.aw.qmc.redraw(recomputeAllDeltas=False)
            self.aw.sendmessage(message)
        else:
            message = QApplication.translate("Message","No events found", None)
            self.aw.sendmessage(message)
    
    @pyqtSlot()
    def weightouteditChanged(self):
        self.weightoutedit.setText(self.aw.comma2dot(self.weightoutedit.text()))
        self.percent()
        self.calculated_density()
        self.density_out_editing_finished() # recalc volume_out

    def checkWeightIn(self):
        enough = True
        enough_replacement = False
        weightIn = 0.0
        try:
            weightIn = float(self.aw.comma2dot(self.weightinedit.text()))
        except:
            pass
        if self.plus_amount_selected is not None:
            try:
                # convert weight to kg
                wc = self.aw.convertWeight(weightIn,self.aw.qmc.weight_units.index(self.unitsComboBox.currentText()),self.aw.qmc.weight_units.index("Kg"))
                if wc > self.plus_amount_selected:
                    enough = False
            except:
                pass
        if self.plus_amount_replace_selected is not None:
            try:
                # convert weight to kg
                wc = self.aw.convertWeight(weightIn,self.aw.qmc.weight_units.index(self.unitsComboBox.currentText()),self.aw.qmc.weight_units.index("Kg"))
                if wc <= self.plus_amount_replace_selected:
                    enough_replacement = True
            except:
                pass
        if enough:
            self.weightinedit.setStyleSheet("")
        else:
            if sys.platform.startswith("darwin") and darkdetect.isDark() and appFrozen():
                self.weightinedit.setStyleSheet("""QLineEdit { background-color: #ad0427;  }""")
            else:
                if enough_replacement:
                    self.weightinedit.setStyleSheet("""QLineEdit { color: #0A5C90; }""")
                else:
                    self.weightinedit.setStyleSheet("""QLineEdit { color: #CC0F50; }""")

    @pyqtSlot()
    def weightineditChanged(self):
        self.weightinedit.setText(self.aw.comma2dot(str(self.weightinedit.text())))
        self.weightinedit.repaint()
        self.percent()
        self.calculated_density()
        keep_modified_density = self.modified_density_in_text
        self.density_in_editing_finished() # recalc volume_in
        self.modified_density_in_text = keep_modified_density
        self.recentRoastEnabled()
        if self.aw.plus_account is not None:
            blend_idx = self.plus_blends_combo.currentIndex()
            if blend_idx > 0:
                self.blendSelectionChanged(blend_idx)
            coffee_idx = self.plus_coffees_combo.currentIndex()
            if coffee_idx > 0:
                self.coffeeSelectionChanged(coffee_idx)
        
    def density_percent(self):
        percent = 0.
        try:
            if self.bean_density_out_edit.text() != "" and float(self.aw.comma2dot(self.bean_density_out_edit.text())) != 0.0:
                percent = self.aw.weight_loss(float(self.aw.comma2dot(str(self.bean_density_in_edit.text()))),float(self.aw.comma2dot(str(self.bean_density_out_edit.text()))))
        except Exception:
            pass
        if percent <= 0:
            self.densitypercentlabel.setText("")
        else:
            percentstring =  "-%.1f%%" % percent
            self.densitypercentlabel.setText(percentstring)    #density percent loss
        
    def moisture_percent(self):
        percent = 0.
        try:
            m_roasted = float(self.aw.comma2dot(str(self.moisture_roasted_edit.text())))
            if m_roasted != 0.0:
                percent = float(self.aw.comma2dot(str(self.moisture_greens_edit.text()))) - m_roasted
        except Exception:
            pass
        if percent <= 0:
            self.moisturepercentlabel.setText("")
        else:
            percentstring =  "-%.1f" %(percent) + "%"
            self.moisturepercentlabel.setText(percentstring)    #density percent loss
                
    def percent(self):
        percent = 0.
        try:
            if self.weightoutedit.text() != "" and float(self.aw.comma2dot(self.weightoutedit.text())) != 0.0:
                percent = self.aw.weight_loss(float(self.aw.comma2dot(self.weightinedit.text())),float(self.aw.comma2dot(self.weightoutedit.text())))
        except Exception:
            pass
        if percent > 0:
            percentstring =  "-%.1f" %(percent) + "%"
            self.weightpercentlabel.setText(percentstring)    #weight percent loss
        else:
            self.weightpercentlabel.setText("")

    @pyqtSlot()
    def volume_percent(self):
        self.volumeinedit.setText(self.aw.comma2dot(self.volumeinedit.text()))
        self.volumeoutedit.setText(self.aw.comma2dot(self.volumeoutedit.text()))
        self.modified_volume_in_text = str(self.volumeinedit.text())
        percent = 0.
        try:
            if self.volumeoutedit.text() != "" and float(self.aw.comma2dot(self.volumeoutedit.text())) != 0.0:
                percent = self.aw.volume_increase(float(self.aw.comma2dot(self.volumeinedit.text())),float(self.aw.comma2dot(self.volumeoutedit.text())))
        except Exception:
            pass
        if percent == 0:
            self.volumepercentlabel.setText("")
        else:
            percentstring =  "%.1f" %(percent) + "%"
            self.volumepercentlabel.setText(percentstring)    #volume percent gain
        self.calculated_density()
        
    # calculates density in g/l from weightin/weightout and volumein/volumeout
    def calc_density(self):
        din = dout = 0.0
        try:
            if self.volumeinedit.text() != "" and self.weightinedit.text() != "":
                volumein = float(self.aw.comma2dot(self.volumeinedit.text()))
                weightin = float(self.aw.comma2dot(self.weightinedit.text()))
                if volumein != 0.0 and weightin != 0.0:
                    vol_idx = self.aw.qmc.volume_units.index(self.volumeUnitsComboBox.currentText())
                    volumein = self.aw.convertVolume(volumein,vol_idx,0)
                    weight_idx = self.aw.qmc.weight_units.index(self.unitsComboBox.currentText())
                    weightin = self.aw.convertWeight(weightin,weight_idx,0)
                    din = (weightin / volumein) 
            if self.volumeoutedit.text() != ""  and self.weightoutedit.text() != "":
                volumeout = float(self.aw.comma2dot(self.volumeoutedit.text()))
                weightout = float(self.aw.comma2dot(self.weightoutedit.text()))
                if volumeout != 0.0 and weightout != 0.0:
                    vol_idx = self.aw.qmc.volume_units.index(self.volumeUnitsComboBox.currentText())
                    volumeout = self.aw.convertVolume(volumeout,vol_idx,0)
                    weight_idx = self.aw.qmc.weight_units.index(self.unitsComboBox.currentText())
                    weightout = self.aw.convertWeight(weightout,weight_idx,0)
                    dout = (weightout / volumeout)
        except:
            pass
        return din,dout

    @pyqtSlot(int)
    def calculated_density(self,_=0):
        din, dout = self.calc_density()
        if din > 0.:
            # set also the green density if not yet set
            self.bean_density_in_edit.setText("%g" % self.aw.float2float(din))
        if  dout > 0.:
            # set also the roasted density if not yet set
            self.bean_density_out_edit.setText("%g" % self.aw.float2float(dout))
        self.density_percent()
        self.calculated_organic_loss()
            
    def calc_organic_loss(self):
        wloss = 0. # weight (moisture + organic)
        mloss = 0. # moisture
        try:
            if self.weightpercentlabel.text() and self.weightpercentlabel.text() != "":
                wloss = abs(float(self.aw.comma2dot(self.weightpercentlabel.text()).split("%")[0]))
        except Exception:
            pass
        try:
            if self.moisturepercentlabel.text() and self.moisturepercentlabel.text() != "":
                mloss = abs(float(self.aw.comma2dot(self.moisturepercentlabel.text()).split("%")[0]))
        except Exception:
            pass
        if mloss != 0. and wloss != 0.:
            return mloss, self.aw.float2float(max(min(wloss - mloss,100),0))
        else:
            return 0., 0.

    def calculated_organic_loss(self):
        self.moisture_percent()
        mloss, oloss = self.calc_organic_loss()
        if oloss > 0. and mloss > 0.:
            self.organiclosslabel.setText(QApplication.translate("Label", "organic material",None))
            self.organicpercentlabel.setText("-{}%".format(oloss))
        else:
            self.organiclosslabel.setText("")
            self.organicpercentlabel.setText("")

    @pyqtSlot()
    def greens_temp_editing_finished(self):
        self.greens_temp_edit.setText(self.aw.comma2dot(str(self.greens_temp_edit.text())))
        
    @pyqtSlot()
    def ambientedit_editing_finished(self):
        self.ambientedit.setText(self.aw.comma2dot(str(self.ambientedit.text())))
    
    @pyqtSlot()
    def ambient_humidity_editing_finished(self):
        self.ambient_humidity_edit.setText(self.aw.comma2dot(str(self.ambient_humidity_edit.text())))
        
    @pyqtSlot()
    def pressureedit_editing_finished(self):
        self.pressureedit.setText(self.aw.comma2dot(str(self.pressureedit.text())))
    
    @pyqtSlot()
    def density_in_editing_finished(self):
        self.bean_density_in_edit.setText(self.aw.comma2dot(str(self.bean_density_in_edit.text())))
        self.modified_density_in_text = str(self.bean_density_in_edit.text())
        # if density-in and weight-in is given, we re-calc volume-in:
        if self.bean_density_in_edit.text() != "" and self.weightinedit.text() != "":
            density_in = float(self.aw.comma2dot(self.bean_density_in_edit.text()))
            weight_in = float(self.aw.comma2dot(self.weightinedit.text()))
            if density_in != 0 and weight_in != 0:
                weight_in = self.aw.convertWeight(weight_in,self.unitsComboBox.currentIndex(),self.aw.qmc.weight_units.index("g"))
                volume_in = weight_in / density_in # in g/l
                # convert to selected volume unit
                volume_in = self.aw.convertVolume(volume_in,self.aw.qmc.volume_units.index("l"),self.volumeUnitsComboBox.currentIndex())
            else:
                volume_in = 0
            self.volumeinedit.setText("%g" % self.aw.float2floatWeightVolume(volume_in))
            self.volume_percent()
    
    @pyqtSlot()
    def density_out_editing_finished(self):
        self.bean_density_out_edit.setText(self.aw.comma2dot(str(self.bean_density_out_edit.text())))
        # if density-out and weight-out is given, we re-calc volume-out:
        if self.bean_density_out_edit.text() != "" and self.weightoutedit.text() != "":
            density_out = float(self.bean_density_out_edit.text())
            weight_out = float(self.aw.comma2dot(self.weightoutedit.text()))
            if density_out != 0 and weight_out != 0:
                weight_out = self.aw.convertWeight(weight_out,self.unitsComboBox.currentIndex(),self.aw.qmc.weight_units.index("g"))
                volume_out = weight_out / density_out # in g/l
                # convert to selected volume unit
                volume_out = self.aw.convertVolume(volume_out,self.aw.qmc.volume_units.index("l"),self.volumeUnitsComboBox.currentIndex())
            else:
                volume_out = 0
            self.volumeoutedit.setText("%g" % self.aw.float2floatWeightVolume(volume_out))
            self.volume_percent()
    
    @pyqtSlot()
    def accept(self):
        #check for graph
        if len(self.aw.qmc.timex):
            #prevents accidentally deleting a modified profile.
            self.aw.qmc.fileDirty()
            if self.chargeedit.text() == "":
                self.aw.qmc.timeindex[0] = -1
                self.aw.qmc.xaxistosm(redraw=False)
            elif self.chargeeditcopy != str(self.chargeedit.text()):
                #if there is a CHARGE recorded and the time entered is positive. Use relative time
                if stringtoseconds(str(self.chargeedit.text())) > 0 and self.aw.qmc.timeindex[0] != -1:
                    startindex = self.aw.qmc.time2index(self.aw.qmc.timex[self.aw.qmc.timeindex[0]] + stringtoseconds(str(self.chargeedit.text())))
                    self.aw.qmc.timeindex[0] = max(-1,startindex)
                    self.aw.qmc.xaxistosm(redraw=False)
                #if there is a CHARGE recorded and the time entered is negative. Use relative time
                elif stringtoseconds(str(self.chargeedit.text())) < 0 and self.aw.qmc.timeindex[0] != -1:
                    relativetime = self.aw.qmc.timex[self.aw.qmc.timeindex[0]]-abs(stringtoseconds(str(self.chargeedit.text())))
                    startindex = self.aw.qmc.time2index(relativetime)
                    self.aw.qmc.timeindex[0] = max(-1,startindex)
                    self.aw.qmc.xaxistosm(redraw=False)
                #if there is _no_ CHARGE recorded and the time entered is positive. Use absolute time 
                elif stringtoseconds(str(self.chargeedit.text())) > 0 and self.aw.qmc.timeindex[0] == -1:
                    startindex = self.aw.qmc.time2index(stringtoseconds(str(self.chargeedit.text())))
                    self.aw.qmc.timeindex[0] = max(-1,startindex)
                    self.aw.qmc.xaxistosm(redraw=False)
                #if there is _no_ CHARGE recorded and the time entered is negative. ERROR
                elif stringtoseconds(str(self.chargeedit.text())) < 0 and self.aw.qmc.timeindex[0] == -1:
                    self.aw.qmc.adderror(QApplication.translate("Error Message", "Unable to move CHARGE to a value that does not exist",None))
                    return
            # check CHARGE (with index self.aw.qmc.timeindex[0])
            if self.aw.qmc.timeindex[0] == -1:
                start = 0                   #relative start time
            else:
                start = self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
            if self.dryeditcopy != str(self.dryedit.text()):
                s = stringtoseconds(str(self.dryedit.text()))
                if s <= 0:
                    self.aw.qmc.timeindex[1] = 0
                else:
                    dryindex = self.aw.qmc.time2index(start + s)
                    self.aw.qmc.timeindex[1] = max(0,dryindex)
            if self.Cstarteditcopy != str(self.Cstartedit.text()):
                s = stringtoseconds(str(self.Cstartedit.text()))
                if s <= 0:
                    self.aw.qmc.timeindex[2] = 0
                else:
                    fcsindex = self.aw.qmc.time2index(start + s)
                    self.aw.qmc.timeindex[2] = max(0,fcsindex)
            if self.Cendeditcopy != str(self.Cendedit.text()):
                s = stringtoseconds(str(self.Cendedit.text()))
                if s <= 0:
                    self.aw.qmc.timeindex[3] = 0
                else:
                    fceindex = self.aw.qmc.time2index(start + s)
                    self.aw.qmc.timeindex[3] = max(0,fceindex)
            if self.CCstarteditcopy != str(self.CCstartedit.text()):
                s = stringtoseconds(str(self.CCstartedit.text()))
                if s <= 0:
                    self.aw.qmc.timeindex[4] = 0
                else:
                    scsindex = self.aw.qmc.time2index(start + s)
                    self.aw.qmc.timeindex[4] = max(0,scsindex)
            if self.CCendeditcopy != str(self.CCendedit.text()):
                s = stringtoseconds(str(self.CCendedit.text()))
                if s <= 0:
                    self.aw.qmc.timeindex[5] = 0
                elif stringtoseconds(str(self.CCendedit.text())) > 0:
                    sceindex = self.aw.qmc.time2index(start + s)
                    self.aw.qmc.timeindex[5] = max(0,sceindex)
            if self.dropeditcopy != str(self.dropedit.text()):
                s = stringtoseconds(str(self.dropedit.text()))
                if s <= 0:
                    self.aw.qmc.timeindex[6] = 0
                else:
                    dropindex = self.aw.qmc.time2index(start + s)
                    self.aw.qmc.timeindex[6] = max(0,dropindex)
            if self.cooleditcopy != str(self.cooledit.text()):
                s = stringtoseconds(str(self.cooledit.text()))
                if s <= 0:
                    self.aw.qmc.timeindex[7] = 0
                else:
                    coolindex = self.aw.qmc.time2index(start + s)
                    self.aw.qmc.timeindex[7] = max(0,coolindex)
            if self.aw.qmc.phasesbuttonflag:   
                # adjust phases by DryEnd and FCs events
                if self.aw.qmc.timeindex[1]:
                    self.aw.qmc.phases[1] = max(0,int(round(self.aw.qmc.temp2[self.aw.qmc.timeindex[1]])))
                if self.aw.qmc.timeindex[2]:
                    self.aw.qmc.phases[2] = max(0,int(round(self.aw.qmc.temp2[self.aw.qmc.timeindex[2]])))
            
            self.saveEventTable()
        # Update Title
        self.aw.qmc.title = ' '.join(self.titleedit.currentText().split())
        self.aw.qmc.title_show_always = self.titleShowAlwaysFlag.isChecked()
        self.aw.qmc.container_idx = self.tareComboBox.currentIndex() - 3

#PLUS        
        # Update Plus
        if self.aw.plus_account is not None:
            self.aw.qmc.plus_default_store = self.plus_default_store
            self.aw.qmc.plus_store = self.plus_store_selected
            self.aw.qmc.plus_store_label = self.plus_store_selected_label
            self.aw.qmc.plus_coffee = self.plus_coffee_selected
            self.aw.qmc.plus_coffee_label = self.plus_coffee_selected_label
            self.aw.qmc.plus_blend_label = self.plus_blend_selected_label
            self.aw.qmc.plus_blend_spec = self.plus_blend_selected_spec
            self.aw.qmc.plus_blend_spec_labels = self.plus_blend_selected_spec_labels
        
        # Update beans
        self.aw.qmc.beans = self.beansedit.toPlainText()
        #update ambient temperature source
        self.aw.qmc.ambientTempSource = self.ambientComboBox.currentIndex()
        #update weight
        try:
            self.aw.qmc.weight[0] = float(self.aw.comma2dot(str(self.weightinedit.text())))
        except Exception:
            self.aw.qmc.weight[0] = 0
        try:
            self.aw.qmc.weight[1] = float(self.aw.comma2dot(str(self.weightoutedit.text())))
        except Exception:
            self.aw.qmc.weight[1] = 0
        self.aw.qmc.weight[2] = self.unitsComboBox.currentText()
        #update volume
        try:
            self.aw.qmc.volume[0] = float(self.aw.comma2dot(str(self.volumeinedit.text())))
        except Exception:
            self.aw.qmc.volume[0] = 0
        try:
            self.aw.qmc.volume[1] = float(self.aw.comma2dot(str(self.volumeoutedit.text())))
        except Exception:
            self.aw.qmc.volume[1] = 0
        self.aw.qmc.volume[2] = self.volumeUnitsComboBox.currentText()
        #update density
        try:
            self.aw.qmc.density[0] = float(self.aw.comma2dot(str(self.bean_density_in_edit.text())))
        except Exception:
            self.aw.qmc.density[0] = 0
        self.aw.qmc.density[1] = "g"
        self.aw.qmc.density[2] = 1
        self.aw.qmc.density[3] = "l"
        try:
            self.aw.qmc.density_roasted[0] = float(self.aw.comma2dot(str(self.bean_density_out_edit.text())))
        except Exception:
            self.aw.qmc.density_roasted[0] = 0
        self.aw.qmc.density_roasted[1] = "g"
        self.aw.qmc.density_roasted[2] = 1
        self.aw.qmc.density_roasted[3] = "l"
        #update bean size
        try:
            self.aw.qmc.beansize_min = int(str(self.bean_size_min_edit.text()))
        except Exception:
            self.aw.qmc.beansize_min = 0
        try:
            self.aw.qmc.beansize_max = int(str(self.bean_size_max_edit.text()))
        except Exception:
            self.aw.qmc.beansize_max = 0
        #update roastflags
        self.aw.qmc.heavyFC_flag = self.heavyFC.isChecked()
        self.aw.qmc.lowFC_flag = self.lowFC.isChecked()
        self.aw.qmc.lightCut_flag = self.lightCut.isChecked()
        self.aw.qmc.darkCut_flag = self.darkCut.isChecked()
        self.aw.qmc.drops_flag = self.drops.isChecked()
        self.aw.qmc.oily_flag = self.oily.isChecked()
        self.aw.qmc.uneven_flag = self.uneven.isChecked()
        self.aw.qmc.tipping_flag = self.tipping.isChecked()
        self.aw.qmc.scorching_flag = self.scorching.isChecked()
        self.aw.qmc.divots_flag = self.divots.isChecked()
        #update color
        try:
            self.aw.qmc.whole_color = int(str(self.whole_color_edit.text()))
        except:
            self.aw.qmc.whole_color = 0
        try:
            self.aw.qmc.ground_color = int(str(self.ground_color_edit.text()))
        except:
            self.aw.qmc.ground_color = 0
        self.aw.qmc.color_system_idx = self.colorSystemComboBox.currentIndex()
        #update beans temperature
        try:
            self.aw.qmc.greens_temp = float(self.aw.comma2dot(str(self.greens_temp_edit.text())))
        except:
            self.aw.qmc.greens_temp = 0.
        #update greens moisture
        try:
            self.aw.qmc.moisture_greens = float(self.aw.comma2dot(str(self.moisture_greens_edit.text())))
        except Exception:
            self.aw.qmc.moisture_greens = 0.
        #update roasted moisture
        try:
            self.aw.qmc.moisture_roasted = float(self.aw.comma2dot(str(self.moisture_roasted_edit.text())))
        except Exception:
            self.aw.qmc.moisture_roasted = 0.
        #update ambient temperature
        try:
            self.aw.qmc.ambientTemp = float(self.aw.comma2dot(self.ambientedit.text()))
            if math.isnan(self.aw.qmc.ambientTemp):
                self.aw.qmc.ambientTemp = 0.0
        except Exception:
            self.aw.qmc.ambientTemp = 0.0
        #update ambient humidity
        try:
            self.aw.qmc.ambient_humidity = float(self.aw.comma2dot(str(self.ambient_humidity_edit.text())))
        except Exception:
            self.aw.qmc.ambient_humidity = 0
        #update ambient pressure
        try:
            self.aw.qmc.ambient_pressure = float(self.aw.comma2dot(str(self.pressureedit.text())))
        except Exception:
            self.aw.qmc.ambient_pressure = 0
        #update notes
        self.aw.qmc.roastertype = self.roaster.text()
        self.aw.qmc.operator = self.operator.text()
        self.aw.qmc.organization = self.organization.text()
        self.aw.qmc.drumspeed = self.drumspeed.text()
        self.aw.qmc.roastingnotes = self.roastingeditor.toPlainText()
        self.aw.qmc.cuppingnotes = self.cuppingeditor.toPlainText()
        if self.aw.superusermode or self.batcheditmode:
            self.aw.qmc.roastbatchprefix = self.batchprefixedit.text()
            self.aw.qmc.roastbatchnr = self.batchcounterSpinBox.value()
            self.aw.qmc.roastbatchpos = self.batchposSpinBox.value()
            
        # if custom events were changed we clear the event flag position cache 
        if self.aw.qmc.specialevents != self.org_specialevents:
            self.aw.qmc.l_event_flags_dict = {}
        # if events were changed we clear the event flag position cache 
        if self.aw.qmc.timeindex != self.org_timeindex:
            self.aw.qmc.l_annotations_dict = {}
        
        # load selected recent roast template in the background
        if self.aw.loadbackgroundUUID(self.template_file,self.template_uuid):
            try:
                self.aw.qmc.background = True
                self.aw.qmc.timealign(redraw=False)
                self.aw.qmc.redraw()
            except:
                pass
        elif ((not self.aw.qmc.flagon) or
            (self.aw.qmc.specialevents != self.org_specialevents) or
            (self.aw.qmc.specialeventstype != self.org_specialeventstype) or
            (self.aw.qmc.specialeventsStrings != self.org_specialeventsStrings) or
            (self.aw.qmc.specialeventsvalue != self.org_specialeventsvalue) or
            (self.aw.qmc.timeindex != self.org_timeindex)):
            # we do a general redraw only if not sampling
            self.aw.qmc.redraw(recomputeAllDeltas=False)
        elif (self.org_title != self.aw.qmc.title) or self.org_title_show_always != self.aw.qmc.title_show_always:
            # if title changed we at least update that one
            if self.aw.qmc.flagstart and not self.aw.qmc.title_show_always:
                self.aw.qmc.setProfileTitle("")
                self.aw.qmc.setProfileBackgroundTitle("")
                self.aw.qmc.fig.canvas.draw()
            else:
                self.aw.qmc.setProfileTitle(self.aw.qmc.title)
                titleB = ""
                if self.aw.qmc.background and not (self.aw.qmc.title is None or self.aw.qmc.title == ""):
                    if self.aw.qmc.roastbatchnrB == 0:
                        titleB = self.aw.qmc.titleB
                    else:
                        titleB = self.aw.qmc.roastbatchprefixB + str(self.aw.qmc.roastbatchnrB) + " " + self.aw.qmc.titleB
                    self.aw.qmc.setProfileBackgroundTitle(titleB)
#                self.aw.qmc.updateBackground()
                self.aw.qmc.fig.canvas.draw()
        
        if not self.aw.qmc.flagon:
            self.aw.sendmessage(QApplication.translate("Message","Roast properties updated but profile not saved to disk", None))
        self.close()