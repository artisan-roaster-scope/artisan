#!/usr/bin/env python3

# ABOUT
# Artisan Roast Calculator

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

from artisanlib.util import fromCtoF, fromFtoC, stringfromseconds, stringtoseconds
from artisanlib.dialogs import ArtisanDialog

from PyQt5.QtCore import pyqtSlot, QSettings, QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import (QApplication, QLabel, QGridLayout, QGroupBox, QLineEdit,
    QComboBox, QHBoxLayout, QVBoxLayout)

class calculatorDlg(ArtisanDialog):
    def __init__(self, parent = None, aw = None):
        super(calculatorDlg,self).__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate("Form Caption","Roast Calculator",None))
        
        settings = QSettings()
        if settings.contains("CalculatorGeometry"):
            self.restoreGeometry(settings.value("CalculatorGeometry"))
            
        #RATE OF CHANGE
        self.result1 = QLabel(QApplication.translate("Label", "Enter two times along profile",None))
        self.result2 = QLabel()
        self.result2.setStyleSheet("background-color:'lightgrey';")
        startlabel = QLabel(QApplication.translate("Label", "Start (00:00)",None))
        endlabel = QLabel(QApplication.translate("Label", "End (00:00)",None))
        self.startEdit = QLineEdit()
        self.endEdit = QLineEdit()
        regextime = QRegularExpression(r"^[0-5][0-9]:[0-5][0-9]$")
        self.startEdit.setValidator(QRegularExpressionValidator(regextime,self))
        self.endEdit.setValidator(QRegularExpressionValidator(regextime,self))
        self.startEdit.editingFinished.connect(self.calculateRC)
        self.endEdit.editingFinished.connect(self.calculateRC)
        nevents = len(self.aw.qmc.specialevents)
        events_found = [QApplication.translate("ComboBox","Event #0",None)]
        for i in range(nevents):
            events_found.append(QApplication.translate("ComboBox","Event #{0}",None).format(str(i+1)))
        self.eventAComboBox = QComboBox()
        self.eventAComboBox.addItems(events_found)
        self.eventAComboBox.currentIndexChanged.connect(self.calcEventRC)
        self.eventBComboBox = QComboBox()
        self.eventBComboBox.addItems(events_found)
        self.eventBComboBox.currentIndexChanged.connect(self.calcEventRC)
        #TEMPERATURE CONVERSION
        flabel = QLabel(QApplication.translate("Label", "Fahrenheit",None))
        clabel = QLabel(QApplication.translate("Label", "Celsius",None))
        self.faEdit = QLineEdit()
        self.ceEdit = QLineEdit()
        self.faEdit.setValidator(self.aw.createCLocaleDoubleValidator(-999999., 9999999., 2, self.faEdit))
        self.ceEdit.setValidator(self.aw.createCLocaleDoubleValidator(-999999., 9999999., 2, self.ceEdit))
        self.faEdit.editingFinished.connect(self.convertTempFtoC)
        self.ceEdit.editingFinished.connect(self.convertTempCtoF)
        #WEIGHT CONVERSION
        self.WinComboBox = QComboBox()
        self.WinComboBox.addItems(self.aw.qmc.weight_units)
        self.WinComboBox.setMaximumWidth(80)
        self.WinComboBox.setMinimumWidth(80)
        self.WoutComboBox = QComboBox()
        self.WoutComboBox.setMaximumWidth(80)
        self.WoutComboBox.setMinimumWidth(80)
        self.WoutComboBox.addItems(self.aw.qmc.weight_units)
        self.WoutComboBox.setCurrentIndex(2)
        self.WinEdit = QLineEdit()
        self.WoutEdit = QLineEdit()
        self.WinEdit.setMaximumWidth(70)
        self.WoutEdit.setMaximumWidth(70)
        #self.WinEdit.setMinimumWidth(60)
        #self.WoutEdit.setMinimumWidth(60)
        self.WinEdit.setValidator(self.aw.createCLocaleDoubleValidator(0., 99999., 4, self.WinEdit))
        self.WoutEdit.setValidator(self.aw.createCLocaleDoubleValidator(0., 99999., 4, self.WoutEdit))
        self.WinEdit.editingFinished.connect(self.convertWeightItoO)
        self.WoutEdit.editingFinished.connect(self.convertWeightOtoI)
        #VOLUME CONVERSION
        self.VinComboBox = QComboBox()
        volumeunits = [QApplication.translate("ComboBox","liter",None),
                       QApplication.translate("ComboBox","gallon",None),
                       QApplication.translate("ComboBox","quart",None),
                       QApplication.translate("ComboBox","pint",None),
                       QApplication.translate("ComboBox","cup",None),
                       QApplication.translate("ComboBox","cm^3",None)]
        self.VinComboBox.addItems(volumeunits)
        self.VinComboBox.setMaximumWidth(80)
        self.VinComboBox.setMinimumWidth(80)
        self.VoutComboBox = QComboBox()
        self.VoutComboBox.setMaximumWidth(80)
        self.VoutComboBox.setMinimumWidth(80)
        self.VoutComboBox.addItems(volumeunits)
        self.VoutComboBox.setCurrentIndex(4)
        self.VinEdit = QLineEdit()
        self.VoutEdit = QLineEdit()
        self.VinEdit.setMaximumWidth(70)
        self.VoutEdit.setMaximumWidth(70)
        #self.VinEdit.setMinimumWidth(60)
        #self.VoutEdit.setMinimumWidth(60)
        self.VinEdit.setValidator(self.aw.createCLocaleDoubleValidator(0., 99999., 4, self.VinEdit))
        self.VoutEdit.setValidator(self.aw.createCLocaleDoubleValidator(0., 99999., 4, self.VoutEdit))
        self.VinEdit.editingFinished.connect(self.convertVolumeItoO)
        self.VoutEdit.editingFinished.connect(self.convertVolumeOtoI)
        #EXTRACTION YIELD
        yieldlabel = QLabel(QApplication.translate("Label", "Yield (%)",None))
        groundslabel = QLabel(QApplication.translate("Label", "Grounds (g)",None))
        tdslabel = QLabel(QApplication.translate("Label", "TDS (%)",None))
        coffeelabel = QLabel(QApplication.translate("Label", "Coffee (g)",None))
        self.groundsEdit = QLineEdit()
        self.coffeeEdit = QLineEdit()
        self.tdsEdit = QLineEdit()
        self.yieldEdit = QLineEdit()
        self.yieldEdit.setReadOnly(True)
        self.groundsEdit.setValidator(self.aw.createCLocaleDoubleValidator(1., 999999., 2, self.groundsEdit))
        self.coffeeEdit.setValidator(self.aw.createCLocaleDoubleValidator(1., 999999., 2, self.coffeeEdit))
        self.tdsEdit.setValidator(self.aw.createCLocaleDoubleValidator(0., 100., 2, self.tdsEdit))
        for e in [self.groundsEdit, self.coffeeEdit, self.tdsEdit]:
            e.editingFinished.connect(self.calculateYield)
        #LAYOUTS
        #Rate of chage
        calrcLayout = QGridLayout()
        calrcLayout.addWidget(startlabel,0,0)
        calrcLayout.addWidget(endlabel,0,1)
        calrcLayout.addWidget(self.startEdit,1,0)
        calrcLayout.addWidget(self.endEdit,1,1)
        calrcLayout.addWidget(self.eventAComboBox ,2,0)
        calrcLayout.addWidget(self.eventBComboBox ,2,1)
        rclayout = QVBoxLayout()
        rclayout.addWidget(self.result1,0)
        rclayout.addWidget(self.result2,1)
        rclayout.addLayout(calrcLayout,2)
        #temperature conversion
        tempLayout = QGridLayout()
        tempLayout.addWidget(flabel,0,0)
        tempLayout.addWidget(clabel,0,1)
        tempLayout.addWidget(self.faEdit,1,0)
        tempLayout.addWidget(self.ceEdit,1,1)
        #weight conversions
        weightLayout = QHBoxLayout()
        weightLayout.addWidget(self.WinComboBox)
        weightLayout.addWidget(self.WinEdit)
        weightLayout.addWidget(self.WoutEdit)
        weightLayout.addWidget(self.WoutComboBox)
        #volume conversions
        volumeLayout = QHBoxLayout()
        volumeLayout.addWidget(self.VinComboBox)
        volumeLayout.addWidget(self.VinEdit)
        volumeLayout.addWidget(self.VoutEdit)
        volumeLayout.addWidget(self.VoutComboBox)
        #extraction yield
        extractionLayout = QGridLayout()
        extractionLayout.addWidget(groundslabel,0,0)
        extractionLayout.addWidget(self.groundsEdit,1,0)
        extractionLayout.addWidget(coffeelabel,0,1)
        extractionLayout.addWidget(self.coffeeEdit,1,1)
        extractionLayout.addWidget(tdslabel,0,2)
        extractionLayout.addWidget(self.tdsEdit,1,2)
        extractionLayout.addWidget(yieldlabel,0,3)
        extractionLayout.addWidget(self.yieldEdit,1,3)
        
        RoCGroup = QGroupBox(QApplication.translate("GroupBox","Rate of Change",None))
        RoCGroup.setLayout(rclayout)
        tempConvGroup = QGroupBox(QApplication.translate("GroupBox","Temperature Conversion",None))
        tempConvGroup.setLayout(tempLayout)
        weightConvGroup = QGroupBox(QApplication.translate("GroupBox","Weight Conversion",None))
        weightConvGroup.setLayout(weightLayout)
        volumeConvGroup = QGroupBox(QApplication.translate("GroupBox","Volume Conversion",None))
        volumeConvGroup.setLayout(volumeLayout)
        extractionYieldGroup = QGroupBox(QApplication.translate("GroupBox","Extraction Yield",None))
        extractionYieldGroup.setLayout(extractionLayout)
        #left side
        leftSide = QVBoxLayout()
        leftSide.addWidget(RoCGroup)
        #right side
        rightSide = QVBoxLayout()
        rightSide.addWidget(tempConvGroup)
        rightSide.addWidget(extractionYieldGroup)
        #rightSide.addStretch()
        topLayout = QHBoxLayout()
        topLayout.addLayout(leftSide)
        topLayout.addLayout(rightSide)
        botLayout = QHBoxLayout()
        botLayout.addWidget(weightConvGroup)
        botLayout.addWidget(volumeConvGroup)
        #main
        mainlayout = QVBoxLayout()
        mainlayout.addLayout(topLayout)
        mainlayout.addLayout(botLayout)
        self.setLayout(mainlayout)
        self.setFixedHeight(self.sizeHint().height())

    @pyqtSlot(int)
    def calcEventRC(self,_):
        nevents = len(self.aw.qmc.specialevents)
        Aevent = int(self.eventAComboBox.currentIndex())
        Bevent = int(self.eventBComboBox.currentIndex())
        if Aevent <= nevents and Bevent <= nevents and Aevent and Bevent:
            if self.aw.qmc.timeindex[0] != -1:
                start = self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
            else:
                start = 0
            self.startEdit.setText(stringfromseconds(self.aw.qmc.timex[self.aw.qmc.specialevents[Aevent-1]] - start))
            self.endEdit.setText(stringfromseconds(self.aw.qmc.timex[self.aw.qmc.specialevents[Bevent-1]] - start))
            self.calculateRC()

    #calculate rate of change
    @pyqtSlot()
    def calculateRC(self):
        if len(self.aw.qmc.timex)>2:
            if not len(self.startEdit.text()) or not len(self.endEdit.text()):
                #empty field
                return
            starttime = stringtoseconds(str(self.startEdit.text()))
            endtime = stringtoseconds(str(self.endEdit.text()))
            if starttime == -1 or endtime == -1:
                self.result1.setText(QApplication.translate("Label", "Time syntax error. Time not valid",None))
                self.result2.setText("")
                return
            if  endtime > self.aw.qmc.timex[-1] or endtime < starttime:
                self.result1.setText(QApplication.translate("Label", "Error: End time smaller than Start time",None))
                self.result2.setText("")
                return
            if self.aw.qmc.timeindex[0] != -1:
                start = self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
            else:
                start = 0
            startindex = self.aw.qmc.time2index(starttime + start)
            endindex = self.aw.qmc.time2index(endtime + start)
            #delta
            deltatime = self.aw.qmc.timex[endindex] -  self.aw.qmc.timex[startindex]
            deltatemperature = self.aw.qmc.temp2[endindex] - self.aw.qmc.temp2[startindex]
            if deltatime == 0:
                deltaseconds = 0
            else:
                deltaseconds = deltatemperature/deltatime
            deltaminutes = deltaseconds*60.
            string1 = QApplication.translate("Label", "Best approximation was made from {0} to {1}",None).format(stringfromseconds(self.aw.qmc.timex[startindex]- start),stringfromseconds(self.aw.qmc.timex[endindex]- start))
            string2 = QApplication.translate("Label", "<b>{0}</b> {1}/sec, <b>{2}</b> {3}/min",None).format("%.2f"%(deltaseconds),self.aw.qmc.mode,"%.2f"%(deltaminutes),self.aw.qmc.mode)
            self.result1.setText(string1)
            self.result2.setText(string2)
        else:
            self.result1.setText(QApplication.translate("Label", "No profile found",None))
            self.result2.setText("")

    @pyqtSlot()
    def convertTempFtoC(self):
        self.convertTempLocal("FtoC")
    
    @pyqtSlot()
    def convertTempCtoF(self):
        self.convertTempLocal("CtoF")
    
    def convertTempLocal(self,x):
        self.faEdit.setText(self.aw.comma2dot(str(self.faEdit.text())))
        self.ceEdit.setText(self.aw.comma2dot(str(self.ceEdit.text())))
        if x == "FtoC":
            newC = fromFtoC(float(str(self.faEdit.text())))
            result = "%.2f"%newC
            self.ceEdit.setText(result)
        elif x == "CtoF":
            newF = fromCtoF(float(str(self.ceEdit.text())))
            result = "%.2f"%newF
            self.faEdit.setText(result)

    @pyqtSlot()
    def convertWeightItoO(self):
        self.WinEdit.setText(self.aw.comma2dot(str(self.WinEdit.text())))
        inx = float(str(self.WinEdit.text()))
        outx = self.aw.convertWeight(inx,self.WinComboBox.currentIndex(),self.WoutComboBox.currentIndex())
        self.WoutEdit.setText("%.2f"%outx)

    @pyqtSlot()
    def convertWeightOtoI(self):
        self.WoutEdit.setText(self.aw.comma2dot(str(self.WoutEdit.text())))
        outx = float(str(self.WoutEdit.text()))
        inx = self.aw.convertWeight(outx,self.WoutComboBox.currentIndex(),self.WinComboBox.currentIndex())
        self.WinEdit.setText("%.2f"%inx)
        
    @pyqtSlot()
    def convertVolumeItoO(self):
        self.VinEdit.setText(self.aw.comma2dot(str(self.VinEdit.text())))
        inx = float(str(self.VinEdit.text()))
        outx = self.aw.convertVolume(inx,self.VinComboBox.currentIndex(),self.VoutComboBox.currentIndex())
        self.VoutEdit.setText("%.3f"%outx)
    
    @pyqtSlot()
    def convertVolumeOtoI(self):
        self.VoutEdit.setText(self.aw.comma2dot(str(self.VoutEdit.text())))
        outx = float(str(self.VoutEdit.text()))
        inx = self.aw.convertVolume(outx,self.VoutComboBox.currentIndex(),self.VinComboBox.currentIndex())
        self.VinEdit.setText("%.3f"%inx)

    @pyqtSlot()
    def calculateYield(self):
        self.groundsEdit.setText(self.aw.comma2dot(str(self.groundsEdit.text())))
        self.tdsEdit.setText(self.aw.comma2dot(str(self.tdsEdit.text())))
        self.coffeeEdit.setText(self.aw.comma2dot(str(self.coffeeEdit.text())))
        # Extraction yield % = Brewed Coffee[g] x TDS[%] / Coffee Grounds[g]
        if self.groundsEdit.text() == "" or self.tdsEdit.text() == "" or self.coffeeEdit.text == "":
            return
        grounds = float(str(self.groundsEdit.text()))
        tds = float(str(self.tdsEdit.text()))
        coffee = float(str(self.coffeeEdit.text()))
        if grounds == 0:
            return
        cyield = coffee * tds / grounds
        self.yieldEdit.setText("%.1f" % cyield)

    def closeEvent(self, _):
        settings = QSettings()
        #save window geometry
        settings.setValue("CalculatorGeometry",self.saveGeometry())