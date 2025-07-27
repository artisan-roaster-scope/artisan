#
# ABOUT
# Artisan Roast Calculator

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

from typing import Optional, TYPE_CHECKING

from artisanlib.util import fromCtoF, fromFtoC, stringfromseconds, stringtoseconds, comma2dot, weight_units, convertWeight, convertVolume
from artisanlib.dialogs import ArtisanDialog

try:
    from PyQt6.QtCore import pyqtSlot, QSettings, QRegularExpression # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QRegularExpressionValidator # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QLabel, QGridLayout, QGroupBox, QLineEdit, # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout) # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import pyqtSlot, QSettings, QRegularExpression # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QRegularExpressionValidator # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QLabel, QGridLayout, QGroupBox, QLineEdit, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout) # @UnusedImport @Reimport  @UnresolvedImport


if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent # pylint: disable=unused-import

class calculatorDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Roast Calculator'))

        settings = QSettings()
        if settings.contains('CalculatorGeometry'):
            self.restoreGeometry(settings.value('CalculatorGeometry'))

        #RATE OF CHANGE
        self.result1 = QLabel(QApplication.translate('Label', 'Enter two times along profile'))
        self.result2 = QLabel()
        self.result2.setStyleSheet("background-color:'lightgrey';")
        startlabel = QLabel(QApplication.translate('Label', 'Start (00:00)'))
        endlabel = QLabel(QApplication.translate('Label', 'End (00:00)'))
        self.startEdit = QLineEdit()
        self.endEdit = QLineEdit()
        regextime = QRegularExpression(r'^[0-5][0-9]:[0-5][0-9]$')
        self.startEdit.setValidator(QRegularExpressionValidator(regextime,self))
        self.endEdit.setValidator(QRegularExpressionValidator(regextime,self))
        self.startEdit.editingFinished.connect(self.calculateRC)
        self.endEdit.editingFinished.connect(self.calculateRC)
        nevents = len(self.aw.qmc.specialevents)
        events_found = [f"{QApplication.translate('Form Caption', 'Event')} #0"]
        for i in range(nevents):
            events_found.append(f"{QApplication.translate('Form Caption', 'Event')} #{str(i+1)}")
        self.eventAComboBox = QComboBox()
        self.eventAComboBox.addItems(events_found)
        self.eventAComboBox.currentIndexChanged.connect(self.calcEventRC)
        self.eventBComboBox = QComboBox()
        self.eventBComboBox.addItems(events_found)
        self.eventBComboBox.currentIndexChanged.connect(self.calcEventRC)
        #TEMPERATURE CONVERSION
        flabel = QLabel(QApplication.translate('Label', 'Fahrenheit'))
        clabel = QLabel(QApplication.translate('Label', 'Celsius'))
        self.faEdit = QLineEdit()
        self.ceEdit = QLineEdit()
        self.faEdit.setValidator(self.aw.createCLocaleDoubleValidator(-999999., 9999999., 2, self.faEdit))
        self.ceEdit.setValidator(self.aw.createCLocaleDoubleValidator(-999999., 9999999., 2, self.ceEdit))
        self.faEdit.editingFinished.connect(self.convertTempFtoC)
        self.ceEdit.editingFinished.connect(self.convertTempCtoF)
        #WEIGHT CONVERSION
        self.WinComboBox = QComboBox()
        self.WinComboBox.addItems(weight_units)
        self.WinComboBox.setMaximumWidth(80)
        self.WinComboBox.setMinimumWidth(80)
        self.WoutComboBox = QComboBox()
        self.WoutComboBox.setMaximumWidth(80)
        self.WoutComboBox.setMinimumWidth(80)
        self.WoutComboBox.addItems(weight_units)
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
        volumeunits = [QApplication.translate('ComboBox','liter'),
                       QApplication.translate('ComboBox','gallon'),
                       QApplication.translate('ComboBox','quart'),
                       QApplication.translate('ComboBox','pint'),
                       QApplication.translate('ComboBox','cup'),
                       QApplication.translate('ComboBox','cm^3')]
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
        yieldlabel = QLabel(QApplication.translate('Label', 'Yield (%)'))
        groundslabel = QLabel(QApplication.translate('Label', 'Grounds (g)'))
        tdslabel = QLabel(QApplication.translate('Label', 'TDS (%)'))
        coffeelabel = QLabel(QApplication.translate('Label', 'Coffee (g)'))
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
        #Rate of change
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

        RoCGroup = QGroupBox(QApplication.translate('GroupBox','Rate of Change'))
        RoCGroup.setLayout(rclayout)
        tempConvGroup = QGroupBox(QApplication.translate('GroupBox','Temperature Conversion'))
        tempConvGroup.setLayout(tempLayout)
        weightConvGroup = QGroupBox(QApplication.translate('GroupBox','Weight Conversion'))
        weightConvGroup.setLayout(weightLayout)
        volumeConvGroup = QGroupBox(QApplication.translate('GroupBox','Volume Conversion'))
        volumeConvGroup.setLayout(volumeLayout)
        extractionYieldGroup = QGroupBox(QApplication.translate('GroupBox','Extraction Yield'))
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
    def calcEventRC(self, _:int) -> None:
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
    def calculateRC(self) -> None:
        if len(self.aw.qmc.timex)>2:
            if not self.startEdit.text() or not self.endEdit.text():
                #empty field
                return
            try:
                starttime = stringtoseconds(str(self.startEdit.text()))
                endtime = stringtoseconds(str(self.endEdit.text()))
                if  endtime > self.aw.qmc.timex[-1] or endtime < starttime:
                    self.aw.sendmessage(QApplication.translate('Label', 'Error: End time smaller than Start time'))
                    self.result1.setText('')
                    self.result2.setText('')
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
                deltaseconds = 0 if deltatime == 0 else deltatemperature / deltatime
                deltaminutes = deltaseconds*60.
                string1 = QApplication.translate('Label', 'Best approximation was made from {0} to {1}').format(stringfromseconds(self.aw.qmc.timex[startindex]- start),stringfromseconds(self.aw.qmc.timex[endindex]- start))
                string2 = QApplication.translate('Label', '<b>{0}</b> {1}/sec, <b>{2}</b> {3}/min').format(f'{deltaseconds:.2f}',self.aw.qmc.mode,f'{deltaminutes:.2f}',self.aw.qmc.mode)
                self.result1.setText(string1)
                self.result2.setText(string2)
            except Exception: # pylint: disable=broad-except
                self.aw.sendmessage(QApplication.translate('Label', 'Time syntax error. Time not valid'))
                self.result1.setText('')
                self.result2.setText('')
                return
        else:
            self.result1.setText(QApplication.translate('Label', 'No profile found'))
            self.result2.setText('')

    @pyqtSlot()
    def convertTempFtoC(self) -> None:
        self.convertTempLocal('FtoC')

    @pyqtSlot()
    def convertTempCtoF(self) -> None:
        self.convertTempLocal('CtoF')

    def convertTempLocal(self, x:str) -> None:
        self.faEdit.setText(comma2dot(str(self.faEdit.text())))
        self.ceEdit.setText(comma2dot(str(self.ceEdit.text())))
        if x == 'FtoC':
            newC = fromFtoC(float(str(self.faEdit.text())))
            result = f'{newC:.2f}'
            self.ceEdit.setText(result)
        elif x == 'CtoF':
            newF = fromCtoF(float(str(self.ceEdit.text())))
            result = f'{newF:.2f}'
            self.faEdit.setText(result)

    @pyqtSlot()
    def convertWeightItoO(self) -> None:
        self.WinEdit.setText(comma2dot(str(self.WinEdit.text())))
        inx = float(str(self.WinEdit.text()))
        outx = convertWeight(inx,self.WinComboBox.currentIndex(),self.WoutComboBox.currentIndex())
        self.WoutEdit.setText(f'{outx:.2f}')

    @pyqtSlot()
    def convertWeightOtoI(self) -> None:
        self.WoutEdit.setText(comma2dot(str(self.WoutEdit.text())))
        outx = float(str(self.WoutEdit.text()))
        inx = convertWeight(outx,self.WoutComboBox.currentIndex(),self.WinComboBox.currentIndex())
        self.WinEdit.setText(f'{inx:.2f}')

    @pyqtSlot()
    def convertVolumeItoO(self) -> None:
        self.VinEdit.setText(comma2dot(str(self.VinEdit.text())))
        inx = float(str(self.VinEdit.text()))
        outx = convertVolume(inx,self.VinComboBox.currentIndex(),self.VoutComboBox.currentIndex())
        self.VoutEdit.setText(f'{outx:.3f}')

    @pyqtSlot()
    def convertVolumeOtoI(self) -> None:
        self.VoutEdit.setText(comma2dot(str(self.VoutEdit.text())))
        outx = float(str(self.VoutEdit.text()))
        inx = convertVolume(outx,self.VoutComboBox.currentIndex(),self.VinComboBox.currentIndex())
        self.VinEdit.setText(f'{inx:.3f}')

    @pyqtSlot()
    def calculateYield(self) -> None:
        self.groundsEdit.setText(comma2dot(str(self.groundsEdit.text())))
        self.tdsEdit.setText(comma2dot(str(self.tdsEdit.text())))
        self.coffeeEdit.setText(comma2dot(str(self.coffeeEdit.text())))
        # Extraction yield % = Brewed Coffee[g] x TDS[%] / Coffee Grounds[g]
        if self.groundsEdit.text() == '' or self.tdsEdit.text() == '' or self.coffeeEdit.text() == '':
            return
        grounds = float(str(self.groundsEdit.text()))
        tds = float(str(self.tdsEdit.text()))
        coffee = float(str(self.coffeeEdit.text()))
        if grounds == 0:
            return
        cyield = coffee * tds / grounds
        self.yieldEdit.setText(f'{cyield:.1f}')

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        settings = QSettings()
        #save window geometry
        settings.setValue('CalculatorGeometry',self.saveGeometry())
