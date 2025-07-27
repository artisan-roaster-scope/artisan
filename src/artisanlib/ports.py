#
# ABOUT
# Artisan Communication Ports Dialog

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

import sys
import time
import platform
import logging
from typing import Final, List, Optional, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from artisanlib.dialogs import HelpDlg # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent, QKeyEvent # pylint: disable=unused-import

from artisanlib.util import toFloat, uchr, comma2dot, float2float, toInt
from artisanlib.dialogs import ArtisanDialog, ArtisanResizeablDialog, PortComboBox
from artisanlib.comm import serialport


try:
    from PyQt6.QtCore import (Qt, pyqtSlot, QSettings) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QIntValidator, QStandardItemModel # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QWidget, QCheckBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, # @UnusedImport @Reimport  @UnresolvedImport
                                 QPushButton, QTabWidget, QComboBox, QDialogButtonBox, QGridLayout,QSizePolicy, # @UnusedImport @Reimport  @UnresolvedImport
                                 QGroupBox, QTableWidget, QTableWidgetItem, QDialog, QTextEdit, QDoubleSpinBox, # @UnusedImport @Reimport  @UnresolvedImport
                                 QHeaderView, QMessageBox, QScrollArea, QFrame)  # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import (Qt, pyqtSlot, QSettings) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QIntValidator, QStandardItemModel # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QWidget, QCheckBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
                                 QPushButton, QTabWidget, QComboBox, QDialogButtonBox, QGridLayout,QSizePolicy, # @UnusedImport @Reimport  @UnresolvedImport
                                 QGroupBox, QTableWidget, QTableWidgetItem, QDialog, QTextEdit, QDoubleSpinBox, # @UnusedImport @Reimport  @UnresolvedImport
                                 QHeaderView, QMessageBox, QScrollArea, QFrame) # @UnusedImport @Reimport  @UnresolvedImport


_log: Final[logging.Logger] = logging.getLogger(__name__)

class scanModbusDlg(ArtisanDialog):
    def __init__(self, parent:QWidget, aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        # current setup selected in the MODBUS tab
        self.port:str = ''
        self.baudrate:int = 19200
        self.bytesize:int = 8
        self.stopbits:int = 1
        self.parity:str = 'N'
        self.timeout:float = 0.5
        self.mtype:int = 1
        self.mhost:str = '127.0.0.1'
        self.mport:int = 502
        # save current MODBUS serial, type, host, port settings
        self.port_aw:str = self.aw.modbus.comport
        self.baudrate_aw:int = self.aw.modbus.baudrate
        self.bytesize_aw:int = self.aw.modbus.bytesize
        self.parity_aw:str = self.aw.modbus.parity
        self.stopbits_aw:int = self.aw.modbus.stopbits
        self.timeout_aw:float = self.aw.modbus.timeout
        self.mtype_aw:int = self.aw.modbus.type
        self.mhost_aw:str = self.aw.modbus.host
        self.mport_aw:int = self.aw.modbus.port
        self.stop:bool = False # if True stop the processing
        self.setWindowTitle(QApplication.translate('Form Caption','Scan Modbus'))
        self.slave:int = 1
        self.slaveLabel:QLabel = QLabel(QApplication.translate('Label', 'Slave'))
        self.slaveEdit:QLineEdit = QLineEdit(str(self.slave))
        self.slaveEdit.setValidator(QIntValidator(1,247,self.slaveEdit))
        self.slaveEdit.setFixedWidth(65)
        self.slaveEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.min_register:int = 0
        self.registerLabel:QLabel = QLabel(QApplication.translate('Label', 'Register'))
        self.toLabel:QLabel = QLabel(uchr(8212))
        self.minRegisterEdit:QLineEdit = QLineEdit(str(self.min_register))
        self.minRegisterEdit.setValidator(QIntValidator(0,65536,self.minRegisterEdit))
        self.minRegisterEdit.setFixedWidth(65)
        self.minRegisterEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.max_register:int = 65536
        self.maxRegisterEdit:QLineEdit = QLineEdit(str(self.max_register))
        self.maxRegisterEdit.setValidator(QIntValidator(0,65536,self.maxRegisterEdit))
        self.maxRegisterEdit.setFixedWidth(65)
        self.maxRegisterEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.code3:bool = True
        self.code4:bool = False
        self.checkbox3:QCheckBox = QCheckBox(QApplication.translate('CheckBox','Fct. 3'))
        self.checkbox3.setChecked(self.code3)
        self.checkbox3.stateChanged.connect(self.checkbox3Changed)
        self.checkbox4:QCheckBox = QCheckBox(QApplication.translate('CheckBox','Fct. 4'))
        self.checkbox4.setChecked(self.code4)
        self.checkbox4.stateChanged.connect(self.checkbox4Changed)
        self.modbusEdit:QTextEdit = QTextEdit()
        self.modbusEdit.setReadOnly(True)
        startButton:QPushButton = QPushButton(QApplication.translate('Button','Start'))
        startButton.setMaximumWidth(150)
        startButton.clicked.connect(self.start_pressed)
        labellayout:QHBoxLayout = QHBoxLayout()
        labellayout.addWidget(self.slaveLabel)
        labellayout.addStretch()
        labellayout.addWidget(self.registerLabel)
        labellayout.addStretch()
        srlayout:QHBoxLayout = QHBoxLayout()
        srlayout.addWidget(self.slaveEdit)
        srlayout.addStretch()
        srlayout.addWidget(self.minRegisterEdit)
        srlayout.addWidget(self.toLabel)
        srlayout.addWidget(self.maxRegisterEdit)
        cblayout:QHBoxLayout = QHBoxLayout()
        cblayout.addStretch()
        cblayout.addWidget(self.checkbox3)
        cblayout.addStretch()
        cblayout.addWidget(self.checkbox4)
        cblayout.addStretch()
        hlayout:QHBoxLayout = QHBoxLayout()
        hlayout.addStretch()
        hlayout.addWidget(startButton)
        hlayout.addStretch()
        layout:QVBoxLayout = QVBoxLayout()
        layout.addLayout(labellayout)
        layout.addLayout(srlayout)
        layout.addLayout(cblayout)
        layout.addWidget(self.modbusEdit)
        layout.addLayout(hlayout)
        self.setLayout(layout)

    def keyPressEvent(self, event: Optional['QKeyEvent']) -> None:
        if event is not None:
            key = int(event.key())
            if key != 0:
                self.stop = True

    @pyqtSlot(bool)
    def start_pressed(self, _:bool = False) -> None:
        try:
            # set MODBUS serial, type, host, port settings from dialog
            self.aw.modbus.comport = self.port
            self.aw.modbus.baudrate = self.baudrate
            self.aw.modbus.bytesize = self.bytesize
            self.aw.modbus.stopbits = self.stopbits
            self.aw.modbus.parity = self.parity
            self.aw.modbus.timeout = self.timeout
            self.aw.modbus.type = self.mtype
            self.aw.modbus.host = self.mhost
            self.aw.modbus.port = self.mport
            self.stop = False

            # update slave and register limits
            self.slave = int(self.slaveEdit.text())
            self.min_register = int(self.minRegisterEdit.text())
            self.max_register = int(self.maxRegisterEdit.text())

            # scan and report
            result = 'Register,Value<br>'
            result += '--------------<br>'
            #### lock shared resources #####
            self.aw.modbus.COMsemaphore.acquire(1)
            for register in range(min(self.min_register,self.max_register),max(self.min_register,self.max_register)+1):
                QApplication.processEvents()
                if self.stop:
                    result += '<br>stopped<br>'
                    self.modbusEdit.setHtml(result)
                    break
                if self.code4:
                    for __ in range(10):
                        self.aw.modbus.sleepBetween()
                    res = self.aw.modbus.peekSingleRegister(self.slave,int(register),code=4)
                    if res is not None:
                        result += str(register) + '(4),' + str(res) + '<br>'
                        self.modbusEdit.setHtml(result)
                if self.code3:
                    for __ in range(10):
                        self.aw.modbus.sleepBetween()
                    res = self.aw.modbus.peekSingleRegister(self.slave,int(register),code=3)
                    if res is not None:
                        result += str(register) + '(3),' + str(res) + '<br>'
                        self.modbusEdit.setHtml(result) # pyrefly: ignore[bad-assignment]
            self.aw.modbus.disconnect()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if self.aw.modbus.COMsemaphore.available() < 1:
                self.aw.modbus.COMsemaphore.release(1)
        # reconstruct MODBUS setup
        self.aw.modbus.comport = self.port_aw
        self.aw.modbus.baudrate = self.baudrate_aw
        self.aw.modbus.bytesize = self.bytesize_aw
        self.aw.modbus.stopbits = self.stopbits_aw
        self.aw.modbus.parity = self.parity_aw
        self.aw.modbus.timeout = self.timeout_aw
        self.aw.modbus.type = self.mtype_aw
        self.aw.modbus.host = self.mhost_aw
        self.aw.modbus.port = self.mport_aw

    @pyqtSlot(int)
    def checkbox3Changed(self, _:int) -> None:
        if self.checkbox3.isChecked():
            self.code3 = True
        else:
            self.code3 = False

    @pyqtSlot(int)
    def checkbox4Changed(self, _:int) -> None:
        if self.checkbox4.isChecked():
            self.code4 = True
        else:
            self.code4 = False

    @pyqtSlot('QCloseEvent')
    def closeEvent(self,_:Optional['QCloseEvent'] = None) -> None:
        self.stop = True
        self.accept()


class scanS7Dlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        # current setup selected in the S7 tab
        self.shost = '127.0.0.1'
        self.sport = 502
        self.srack = 0
        self.sslot = 0
        self.shost_aw = self.aw.s7.host
        self.sport_aw = self.aw.s7.port
        self.srack_aw = self.aw.s7.rack
        self.sslot_aw = self.aw.s7.slot
        self.stop = False # if True stop the processing
        self.setWindowTitle(QApplication.translate('Form Caption','Scan S7'))

        s7_areas = ['PE','PA','MK','CT','TM','DB']
        self.area = 5
        self.areaLabel = QLabel(QApplication.translate('Label', 'Area'))
        self.areaCombo = QComboBox()
        self.areaCombo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.areaCombo.addItems(s7_areas)
        self.areaCombo.setCurrentIndex(self.area)

        self.DBnr = 1
        self.DBnrLabel = QLabel(QApplication.translate('Label', 'DB#'))
        self.DBnrEdit = QLineEdit(str(self.DBnr))
        self.DBnrEdit.setValidator(QIntValidator(1,99999,self.DBnrEdit))
        self.DBnrEdit.setFixedWidth(65)
        self.DBnrEdit.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.min_register = 0
        self.registerLabel = QLabel(QApplication.translate('Label', 'Start'))
        self.toLabel = QLabel(uchr(8212))
        self.minRegisterEdit = QLineEdit(str(self.min_register))
        self.minRegisterEdit.setValidator(QIntValidator(0,65536,self.minRegisterEdit))
        self.minRegisterEdit.setFixedWidth(65)
        self.minRegisterEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.max_register = 65536
        self.maxRegisterEdit = QLineEdit(str(self.max_register))
        self.maxRegisterEdit.setValidator(QIntValidator(0,65536,self.maxRegisterEdit))
        self.maxRegisterEdit.setFixedWidth(65)
        self.maxRegisterEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.typeInt = True
        self.typeFloat = False
        self.checkbox3 = QCheckBox(QApplication.translate('CheckBox','Int'))
        self.checkbox3.setChecked(self.typeInt)
        self.checkbox3.stateChanged.connect(self.checkbox3Changed)
        self.checkbox4 = QCheckBox(QApplication.translate('CheckBox','Float'))
        self.checkbox4.setChecked(self.typeFloat)
        self.checkbox4.stateChanged.connect(self.checkbox4Changed)
        self.S7Edit = QTextEdit()
        self.S7Edit.setReadOnly(True)
        startButton = QPushButton(QApplication.translate('Button','Start'))
        startButton.setMaximumWidth(150)
        startButton.clicked.connect(self.start_pressed)
        gridlayout = QGridLayout()
        gridlayout.addWidget(self.areaLabel,0,0)
        gridlayout.addWidget(self.DBnrLabel,0,1)
        gridlayout.addWidget(self.registerLabel,0,2)
        gridlayout.addWidget(self.areaCombo,1,0)
        gridlayout.addWidget(self.DBnrEdit,1,1)
        gridlayout.addWidget(self.minRegisterEdit,1,2)
        gridlayout.addWidget(self.toLabel,1,3,Qt.AlignmentFlag.AlignHCenter)
        gridlayout.addWidget(self.maxRegisterEdit,1,4)
        cblayout= QHBoxLayout()
        cblayout.addStretch()
        cblayout.addWidget(self.checkbox3)
        cblayout.addStretch()
        cblayout.addWidget(self.checkbox4)
        cblayout.addStretch()
        hlayout = QHBoxLayout()
        hlayout.addStretch()
        hlayout.addWidget(startButton)
        hlayout.addStretch()
        layout = QVBoxLayout()
        layout.addLayout(gridlayout)
        layout.addLayout(cblayout)
        layout.addWidget(self.S7Edit)
        layout.addLayout(hlayout)
        self.setLayout(layout)

    def keyPressEvent(self, event: Optional['QKeyEvent']) -> None:
        if event is not None:
            key = int(event.key())
            if key != 0:
                self.stop = True

    @pyqtSlot(bool)
    def start_pressed(self, _:bool = False) -> None:
        try:
            # set S7 host, port and other settings from dialog

            self.aw.s7.host = self.shost
            self.aw.s7.port = self.sport
            self.aw.s7.rack = self.srack
            self.aw.s7.slot = self.sslot

            self.stop = False

            # update slave and register limits
            self.area = int(self.areaCombo.currentIndex())
            self.DBnr = int(self.DBnrEdit.text())
            self.min_register = int(self.minRegisterEdit.text())
            self.max_register = int(self.maxRegisterEdit.text())

            # scan and report
            result = 'Start,Value<br>'
            result += '--------------<br>'
            #### lock shared resources #####
            self.aw.s7.COMsemaphore.acquire(1)
            for register in range(min(self.min_register,self.max_register),max(self.min_register,self.max_register)+1,(4 if self.typeFloat else 2)):
                QApplication.processEvents()
                if self.stop:
                    result += '<br>stopped<br>'
                    self.S7Edit.setHtml(result)
                    break
                if self.typeFloat:
                    res = self.aw.s7.peekFloat(self.area,self.DBnr,register)
                else:
                    res = self.aw.s7.peekInt(self.area,self.DBnr,register)
                if res is not None:
                    result += f'{str(register)}: {str(res)}<br>'
                    self.S7Edit.setHtml(result) # pyrefly: ignore[bad-assignment]
                time.sleep(0.4)
            self.aw.s7.disconnect()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if self.aw.s7.COMsemaphore.available() < 1:
                self.aw.s7.COMsemaphore.release(1)
        # reconstruct S7 setup
        self.aw.s7.host = self.shost_aw
        self.aw.s7.port = self.sport_aw
        self.aw.s7.rack = self.srack_aw
        self.aw.s7.slot = self.sslot_aw

    @pyqtSlot(int)
    def checkbox3Changed(self, _:int) -> None:
        if self.checkbox3.isChecked():
            self.typeInt = True
            self.checkbox4.setChecked(not self.typeInt)
        else:
            self.typeInt = False
            self.checkbox4.setChecked(not self.typeInt)

    @pyqtSlot(int)
    def checkbox4Changed(self, _:int) -> None:
        if self.checkbox4.isChecked():
            self.typeFloat = True
            self.checkbox3.setChecked(not self.typeFloat)
        else:
            self.typeFloat = False
            self.checkbox3.setChecked(not self.typeFloat)

    @pyqtSlot('QCloseEvent')
    def closeEvent(self,_:Optional['QCloseEvent'] = None) -> None:
        self.stop = True
        self.accept()


class comportDlg(ArtisanResizeablDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False) # overwrite the ArtisanDialog class default here!!
        self.setWindowTitle(QApplication.translate('Form Caption','Ports Configuration'))
        self.setModal(True)
        self.helpdialog:Optional[HelpDlg] = None
        ##########################    TAB 1 WIDGETS
        comportlabel =QLabel(QApplication.translate('Label', 'Comm Port'))
        self.comportEdit = PortComboBox(selection = self.aw.ser.comport)
        self.comportEdit.activated.connect(self.portComboBoxIndexChanged)
#        comportlabel.setBuddy(self.comportEdit)
        baudratelabel = QLabel(QApplication.translate('Label', 'Baud Rate'))
        self.baudrateComboBox = QComboBox()
#        baudratelabel.setBuddy(self.baudrateComboBox)
        self.bauds = ['1200', '2400','4800','9600','19200','38400','57600','57800','115200']
        self.baudrateComboBox.addItems(self.bauds)
        self.baudrateComboBox.setCurrentIndex(self.bauds.index(str(self.aw.ser.baudrate)))
        bytesizelabel = QLabel(QApplication.translate('Label', 'Byte Size'))
        self.bytesizeComboBox = QComboBox()
#        bytesizelabel.setBuddy(self.bytesizeComboBox)
        self.bytesizes = ['7','8']
        self.bytesizeComboBox.addItems(self.bytesizes)
        self.bytesizeComboBox.setCurrentIndex(self.bytesizes.index(str(self.aw.ser.bytesize)))
        paritylabel = QLabel(QApplication.translate('Label', 'Parity'))
        self.parityComboBox = QComboBox()
#        paritylabel.setBuddy(self.parityComboBox)
        #0 = Odd, E = Even, N = None. NOTE: These strings cannot be translated as they are arguments to the lib pyserial.
        self.parity = ['O','E','N']
        self.parityComboBox.addItems(self.parity)
        self.parityComboBox.setCurrentIndex(self.parity.index(self.aw.ser.parity))
        stopbitslabel = QLabel(QApplication.translate('Label', 'Stopbits'))
        self.stopbitsComboBox = QComboBox()
#        stopbitslabel.setBuddy(self.stopbitsComboBox)
        self.stopbits = ['1','2']
        self.stopbitsComboBox.addItems(self.stopbits)
        self.stopbitsComboBox.setCurrentIndex(self.aw.ser.stopbits-1)
        timeoutlabel = QLabel(QApplication.translate('Label', 'Timeout'))
        self.timeoutEdit:QLineEdit = QLineEdit(str(self.aw.ser.timeout))
        self.timeoutEdit.setValidator(self.aw.createCLocaleDoubleValidator(0,5,1,self.timeoutEdit))
        etbt_help_label = QLabel(QApplication.translate('Label', 'Settings for non-Modbus devices') + '<br>')
        ##########################    TAB 2  WIDGETS   EXTRA DEVICES
        self.serialtable = QTableWidget()
        self.serialtable.setTabKeyNavigation(True)
        self.serialtable.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        hheader: Optional[QHeaderView] = self.serialtable.horizontalHeader()
        if hheader is not None:
            hheader.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            hheader.setStretchLastSection(True)
        self.createserialTable()
        ##########################    TAB 3 WIDGETS   MODBUS
        modbus_comportlabel = QLabel(QApplication.translate('Label', 'Comm Port'))
        self.modbus_comportEdit = PortComboBox(self, selection = self.aw.modbus.comport)

#        self.modbus_comportEdit.setFixedWidth(120)
        self.modbus_comportEdit.activated.connect(self.portComboBoxIndexChanged)
#        modbus_comportlabel.setBuddy(self.modbus_comportEdit)
        modbus_baudratelabel = QLabel(QApplication.translate('Label', 'Baud Rate'))
        self.modbus_baudrateComboBox = QComboBox()
#        modbus_baudratelabel.setBuddy(self.modbus_baudrateComboBox)
        self.modbus_bauds = ['1200','2400','4800','9600','19200','38400','57600','57800','115200']
        self.modbus_baudrateComboBox.addItems(self.modbus_bauds)
        try:
            self.modbus_baudrateComboBox.setCurrentIndex(self.modbus_bauds.index(str(self.aw.modbus.baudrate)))
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        modbus_bytesizelabel = QLabel(QApplication.translate('Label', 'Byte Size'))
        self.modbus_bytesizeComboBox = QComboBox()
#        modbus_bytesizelabel.setBuddy(self.modbus_bytesizeComboBox)
        self.modbus_bytesizes = ['7','8']
        self.modbus_bytesizeComboBox.addItems(self.modbus_bytesizes)
        self.modbus_bytesizeComboBox.setCurrentIndex(self.modbus_bytesizes.index(str(self.aw.modbus.bytesize)))
        modbus_paritylabel = QLabel(QApplication.translate('Label', 'Parity'))
        self.modbus_parityComboBox = QComboBox()
#        modbus_paritylabel.setBuddy(self.modbus_parityComboBox)
        #0 = Odd, E = Even, N = None. NOTE: These strings cannot be translated as they are arguments to the lib pyserial.
        self.modbus_parity = ['O','E','N']
        self.modbus_parityComboBox.addItems(self.modbus_parity)
        self.modbus_parityComboBox.setCurrentIndex(self.modbus_parity.index(self.aw.modbus.parity))
        modbus_stopbitslabel = QLabel(QApplication.translate('Label', 'Stopbits'))
        self.modbus_stopbitsComboBox = QComboBox()
#        modbus_stopbitslabel.setBuddy(self.modbus_stopbitsComboBox)
        self.modbus_stopbits = ['1','2']
        self.modbus_stopbitsComboBox.addItems(self.stopbits)
        self.modbus_stopbitsComboBox.setCurrentIndex(self.aw.modbus.stopbits - 1)
        modbus_timeoutlabel = QLabel(QApplication.translate('Label', 'Timeout'))
        self.modbus_timeoutEdit = QLineEdit(str(self.aw.modbus.timeout))
        self.modbus_timeoutEdit.setValidator(self.aw.createCLocaleDoubleValidator(0,5,1,self.modbus_timeoutEdit))

        modbus_function_codes = ['1','2','3','4']
        modbus_modes = ['', 'C','F']
        modbus_divs = ['', '1/10','1/100']
        modbus_decode = ['uInt16', 'uInt32', 'sInt16', 'sInt32', 'BCD16', 'BCD32', 'Float32']

        modbus_input1slavelabel = QLabel(QApplication.translate('Label', 'Slave'))
        modbus_input1registerlabel = QLabel(QApplication.translate('Label', 'Register'))
        modbus_input1floatlabel = QLabel(QApplication.translate('Label', 'Decode'))
        modbus_input1codelabel = QLabel(QApplication.translate('Label', 'Function'))
        modbus_input1divlabel = QLabel(QApplication.translate('Label', 'Divider'))
        modbus_input1modelabel = QLabel(QApplication.translate('Label', 'Mode'))

        self.modbus_inputSlaveEdits:List[Optional[QLineEdit]] = [None]*self.aw.modbus.channels # pyrefly: ignore[bad-assignment]
        self.modbus_inputRegisterEdits:List[Optional[QLineEdit]] = [None]*self.aw.modbus.channels # pyrefly: ignore[bad-assignment]
        self.modbus_inputCodes:List[Optional[QComboBox]] = [None]*self.aw.modbus.channels # pyrefly: ignore[bad-assignment]
        self.modbus_inputDivs:List[Optional[QComboBox]] = [None]*self.aw.modbus.channels # pyrefly: ignore[bad-assignment]
        self.modbus_inputModes:List[Optional[QComboBox]] = [None]*self.aw.modbus.channels # pyrefly: ignore[bad-assignment]
        self.modbus_inputDecodes:List[Optional[QComboBox]] = [None]*self.aw.modbus.channels # pyrefly: ignore[bad-assignment]

        for i in range(self.aw.modbus.channels):
            modbus_inputSlaveEdit:QLineEdit = QLineEdit(str(self.aw.modbus.inputSlaves[i]))
            modbus_inputSlaveEdit.setValidator(QIntValidator(0,247,self.modbus_inputSlaveEdits[i]))
            modbus_inputSlaveEdit.setFixedWidth(75)
            modbus_inputSlaveEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.modbus_inputSlaveEdits[i] = modbus_inputSlaveEdit
            #
            modbus_inputRegisterEdit:QLineEdit = QLineEdit(str(self.aw.modbus.inputRegisters[i]))
            modbus_inputRegisterEdit.setValidator(QIntValidator(0,65536,self.modbus_inputRegisterEdits[i]))
            modbus_inputRegisterEdit.setFixedWidth(75)
            modbus_inputRegisterEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.modbus_inputRegisterEdits[i] = modbus_inputRegisterEdit
            #
            modbus_inputCode:QComboBox = QComboBox()
            modbus_inputCode.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            modbus_inputCode.addItems(modbus_function_codes)
            modbus_inputCode.setCurrentIndex(modbus_function_codes.index(str(self.aw.modbus.inputCodes[i])))
            modbus_inputCode.setFixedWidth(85)
            self.modbus_inputCodes[i] = modbus_inputCode
            #
            modbus_inputDiv:QComboBox = QComboBox()
            modbus_inputDiv.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            modbus_inputDiv.addItems(modbus_divs)
            modbus_inputDiv.setCurrentIndex(self.aw.modbus.inputDivs[i])
            modbus_inputDiv.setFixedWidth(85)
            self.modbus_inputDivs[i] = modbus_inputDiv
            #
            modbus_inputMode:QComboBox = QComboBox()
            modbus_inputMode.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            modbus_inputMode.addItems(modbus_modes)
            modbus_inputMode.setCurrentIndex(modbus_modes.index(str(self.aw.modbus.inputModes[i])))
            modbus_inputMode.setFixedWidth(85)
            self.modbus_inputModes[i] = modbus_inputMode
            #
            modbus_inputDecode:QComboBox = QComboBox()
            modbus_inputDecode.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            modbus_inputDecode.addItems(modbus_decode)
            if (self.aw.modbus.inputBCDsAsInt[i] and not self.aw.modbus.inputFloatsAsInt[i] and not self.aw.modbus.inputFloats[i] and
                    not self.aw.modbus.inputBCDs[i]):
                modbus_inputDecode.setCurrentIndex(4)
            elif self.aw.modbus.inputFloatsAsInt[i]:
                if self.aw.modbus.inputSigned[i]:
                    modbus_inputDecode.setCurrentIndex(3)
                else:
                    modbus_inputDecode.setCurrentIndex(1)
            elif self.aw.modbus.inputFloats[i]:
                modbus_inputDecode.setCurrentIndex(6)
            elif self.aw.modbus.inputBCDs[i]:
                modbus_inputDecode.setCurrentIndex(5)
            elif self.aw.modbus.inputSigned[i]:
                modbus_inputDecode.setCurrentIndex(2)
            else:
                modbus_inputDecode.setCurrentIndex(0)
            modbus_inputDecode.setFixedWidth(85)
            self.modbus_inputDecodes[i] = modbus_inputDecode

        modbus_endianlabel = QLabel(QApplication.translate('Label', 'little-endian'))

        self.modbus_littleEndianWords = QCheckBox(QApplication.translate('ComboBox','words'))
        self.modbus_littleEndianWords.setChecked(self.aw.modbus.wordorderLittle)
        self.modbus_littleEndianWords.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # type
        self.modbus_type = QComboBox()
        modbus_typelabel = QLabel(QApplication.translate('Label', 'Type'))
#        modbus_typelabel.setBuddy(self.modbus_type)
        self.modbus_type.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.modbus_type.addItems(['Serial RTU', 'Serial ASCII', 'Serial Binary', 'TCP', 'UDP'])
        modbus_type_model:Optional[QStandardItemModel] = cast(Optional[QStandardItemModel], self.modbus_type.model())
        if modbus_type_model is not None:
            serial_binary_item = modbus_type_model.item(2)
            if serial_binary_item is not None:
                serial_binary_item.setEnabled(False)
        self.modbus_type.setCurrentIndex(self.aw.modbus.type)

        # host (IP or hostname)
        modbus_hostlabel = QLabel(QApplication.translate('Label', 'Host'))
        self.modbus_hostEdit = QLineEdit(str(self.aw.modbus.host))
        self.modbus_hostEdit.setFixedWidth(110)
        self.modbus_hostEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # port (default 502)
        modbus_portlabel = QLabel(QApplication.translate('Label', 'Port'))
        self.modbus_portEdit = QLineEdit(str(self.aw.modbus.port))
        self.modbus_portEdit.setValidator(QIntValidator(1,65535,self.modbus_portEdit))
        self.modbus_portEdit.setFixedWidth(50)
        self.modbus_portEdit.setAlignment(Qt.AlignmentFlag.AlignRight)

        # modbus external PID conf
        modbus_PIDslave_label = QLabel(QApplication.translate('Label', 'Slave'))
        self.modbus_PIDslave_Edit = QLineEdit(str(self.aw.modbus.PID_slave_ID))
        self.modbus_PIDslave_Edit.setValidator(QIntValidator(0,65536,self.modbus_PIDslave_Edit))
        self.modbus_PIDslave_Edit.setFixedWidth(50)
        self.modbus_PIDslave_Edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        modbus_SVregister_label = QLabel(QApplication.translate('Label', 'SV'))
        self.modbus_SVregister_Edit = QLineEdit(str(self.aw.modbus.PID_SV_register))
        self.modbus_SVregister_Edit.setValidator(QIntValidator(0,65536,self.modbus_SVregister_Edit))
        self.modbus_SVregister_Edit.setFixedWidth(50)
        self.modbus_SVregister_Edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        modbus_multis = ['', '10','100']

        self.SVComboBox = QComboBox()
        svVariants = [
            'Int16',
            'Int32',
            'Float32',
            ]
        self.SVComboBox.addItems(svVariants)
        self.SVComboBox.setCurrentIndex(2 if self.aw.modbus.SVwriteFloat else (1 if self.aw.modbus.SVwriteLong else 0))

        modbus_SVmultiplier_label = QLabel(QApplication.translate('Label', 'SV Factor'))
        self.modbus_SVmultiplier = QComboBox()
        self.modbus_SVmultiplier.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.modbus_SVmultiplier.addItems(modbus_multis)
        self.modbus_SVmultiplier.setCurrentIndex(self.aw.modbus.SVmultiplier)
        self.modbus_SVmultiplier.setFixedWidth(70)

        modbus_PIDmultiplier_label = QLabel(QApplication.translate('Label', 'pid Factor'))
        self.modbus_PIDmultiplier = QComboBox()
        self.modbus_PIDmultiplier.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.modbus_PIDmultiplier.addItems(modbus_multis)
        self.modbus_PIDmultiplier.setCurrentIndex(self.aw.modbus.PIDmultiplier)
        self.modbus_PIDmultiplier.setFixedWidth(70)

        modbus_Pregister_label = QLabel(QApplication.translate('Label', 'P'))
        self.modbus_Pregister_Edit = QLineEdit(str(self.aw.modbus.PID_p_register))
        self.modbus_Pregister_Edit.setValidator(QIntValidator(0,65536,self.modbus_Pregister_Edit))
        self.modbus_Pregister_Edit.setFixedWidth(50)
        self.modbus_Pregister_Edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        modbus_Iregister_label = QLabel(QApplication.translate('Label', 'I'))
        self.modbus_Iregister_Edit = QLineEdit(str(self.aw.modbus.PID_i_register))
        self.modbus_Iregister_Edit.setValidator(QIntValidator(0,65536,self.modbus_Iregister_Edit))
        self.modbus_Iregister_Edit.setFixedWidth(50)
        self.modbus_Iregister_Edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        modbus_Dregister_label = QLabel(QApplication.translate('Label', 'D'))
        self.modbus_Dregister_Edit = QLineEdit(str(self.aw.modbus.PID_d_register))
        self.modbus_Dregister_Edit.setValidator(QIntValidator(0,65536,self.modbus_Dregister_Edit))
        self.modbus_Dregister_Edit.setFixedWidth(50)
        self.modbus_Dregister_Edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        modbus_pid_registers = QHBoxLayout()
        modbus_pid_registers.addWidget(modbus_SVregister_label)
        modbus_pid_registers.addWidget(self.modbus_SVregister_Edit)
        modbus_pid_registers.addSpacing(35)
        modbus_pid_registers.addStretch()
        modbus_pid_registers.addWidget(modbus_Pregister_label)
        modbus_pid_registers.addWidget(self.modbus_Pregister_Edit)
        modbus_pid_registers.addSpacing(15)
        modbus_pid_registers.addStretch()
        modbus_pid_registers.addWidget(modbus_Iregister_label)
        modbus_pid_registers.addWidget(self.modbus_Iregister_Edit)
        modbus_pid_registers.addSpacing(15)
        modbus_pid_registers.addStretch()
        modbus_pid_registers.addWidget(modbus_Dregister_label)
        modbus_pid_registers.addWidget(self.modbus_Dregister_Edit)

        modbus_pid_multipliers = QHBoxLayout()
        modbus_pid_multipliers.addWidget(self.SVComboBox)
        modbus_pid_multipliers.addStretch()
        modbus_pid_multipliers.addWidget(modbus_SVmultiplier_label)
        modbus_pid_multipliers.addWidget(self.modbus_SVmultiplier)
        modbus_pid_multipliers.addStretch()
        modbus_pid_multipliers.addWidget(modbus_PIDmultiplier_label)
        modbus_pid_multipliers.addWidget(self.modbus_PIDmultiplier)

        modbus_pid_regmulti = QVBoxLayout()
        modbus_pid_regmulti.addLayout(modbus_pid_registers)
        modbus_pid_regmulti.addLayout(modbus_pid_multipliers)

        modbus_pid_registers_box = QGroupBox(QApplication.translate('GroupBox','Registers'))
        modbus_pid_registers_box.setLayout(modbus_pid_regmulti)
        modbus_pid_regmulti.setContentsMargins(2,2,20,2)

        modbus_pid_off_label = QLabel(QApplication.translate('Label', 'OFF'))
        self.modbus_pid_off = QLineEdit(self.aw.modbus.PID_OFF_action)
        self.modbus_pid_off.setToolTip(QApplication.translate('Tooltip', 'OFF Action String'))
        modbus_pid_on_label = QLabel(QApplication.translate('Label', 'ON'))
        self.modbus_pid_on = QLineEdit(self.aw.modbus.PID_ON_action)
        self.modbus_pid_on.setToolTip(QApplication.translate('Tooltip', 'ON Action String'))

        modbus_pid_commands = QGridLayout()
        modbus_pid_commands.addWidget(modbus_pid_on_label,0,0)
        modbus_pid_commands.addWidget(self.modbus_pid_on,0,1)
        modbus_pid_commands.addWidget(modbus_pid_off_label,1,0)
        modbus_pid_commands.addWidget(self.modbus_pid_off,1,1)

        modbus_pid_commands_box = QGroupBox(QApplication.translate('GroupBox','Commands'))
        modbus_pid_commands_box.setLayout(modbus_pid_commands)
        modbus_pid_commands.setContentsMargins(2,2,20,2)

        modbus_pid = QHBoxLayout()
        modbus_pid.addStretch()
        modbus_pid.addWidget(modbus_PIDslave_label)
        modbus_pid.addWidget(self.modbus_PIDslave_Edit)
        modbus_pid.addWidget(modbus_pid_registers_box)
        modbus_pid.addWidget(modbus_pid_commands_box)
        modbus_pid.addStretch()

        modbus_pidgroup = QGroupBox(QApplication.translate('GroupBox', 'PID'))
        modbus_pidgroup.setLayout(modbus_pid)
        modbus_pid.setContentsMargins(0,10,0,0)
        modbus_pidgroup.setContentsMargins(0,20,0,3)


        modbus_Serial_delaylabel = QLabel(QApplication.translate('Label', 'Delay'))
        modbus_Serial_delaylabel.setToolTip(QApplication.translate('Tooltip', 'Extra delay after connect in seconds before sending requests (needed by Arduino devices restarting on connect)'))
        self.modbus_Serial_delayEdit = QLineEdit(str(self.aw.modbus.modbus_serial_connect_delay))
        self.modbus_Serial_delayEdit.setValidator(self.aw.createCLocaleDoubleValidator(0,3,1,self.modbus_Serial_delayEdit))
        self.modbus_Serial_delayEdit.setFixedWidth(50)
        self.modbus_Serial_delayEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.modbus_Serial_delayEdit.setToolTip(QApplication.translate('Tooltip', 'Extra delay after connect in seconds before sending requests (needed by Arduino devices restarting on connect)'))
        modbus_Serial_retries = QLabel(QApplication.translate('Label', 'Retries'))
        self.modbus_Serial_retriesComboBox = QComboBox()
#        modbus_Serial_retries.setBuddy(self.modbus_Serial_retriesComboBox)
        self.modbus_Serial_retriesComboBox.addItems([str(n) for n in range(4)])
        self.modbus_Serial_retriesComboBox.setCurrentIndex(self.aw.modbus.serial_readRetries)

        modbus_Serial_grid = QGridLayout()
        modbus_Serial_grid.addWidget(modbus_Serial_delaylabel,0,0,Qt.AlignmentFlag.AlignRight)
        modbus_Serial_grid.addWidget(self.modbus_Serial_delayEdit,0,1,Qt.AlignmentFlag.AlignRight)
        modbus_Serial_grid.addWidget(modbus_Serial_retries,1,0,Qt.AlignmentFlag.AlignRight)
        modbus_Serial_grid.addWidget(self.modbus_Serial_retriesComboBox,1,1,Qt.AlignmentFlag.AlignRight)

        modbus_Serial_layout = QVBoxLayout()
        modbus_Serial_layout.addLayout(modbus_Serial_grid)
        modbus_Serial_layout.addStretch()

        modbus_Serialgroup = QGroupBox(QApplication.translate('GroupBox', 'Serial'))
        modbus_Serialgroup.setLayout(modbus_Serial_layout)


        modbus_IP_timeoutlabel = QLabel(QApplication.translate('Label', 'Timeout'))
        modbus_IP_timeoutlabel.setToolTip(QApplication.translate('Tooltip', 'IP timeout in seconds, not larger than half of the sampling interval'))
        self.modbus_IP_timeoutEdit = QLineEdit(str(self.aw.modbus.IP_timeout))
        self.modbus_IP_timeoutEdit.setValidator(self.aw.createCLocaleDoubleValidator(0,5,1,self.modbus_IP_timeoutEdit))
        self.modbus_IP_timeoutEdit.setFixedWidth(50)
        self.modbus_IP_timeoutEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.modbus_IP_timeoutEdit.setToolTip(QApplication.translate('Tooltip', 'IP timeout in seconds, not larger than half of the sampling interval'))
        modbus_IP_retries = QLabel(QApplication.translate('Label', 'Retries'))
        self.modbus_IP_retriesComboBox = QComboBox()
#        modbus_IP_retries.setBuddy(self.modbus_IP_retriesComboBox)
        self.modbus_IP_retriesComboBox.addItems([str(n) for n in range(4)])
        self.modbus_IP_retriesComboBox.setCurrentIndex(self.aw.modbus.IP_retries)

        modbus_IP_grid = QGridLayout()
        modbus_IP_grid.addWidget(modbus_IP_timeoutlabel,0,0,Qt.AlignmentFlag.AlignRight)
        modbus_IP_grid.addWidget(self.modbus_IP_timeoutEdit,0,1,Qt.AlignmentFlag.AlignRight)
        modbus_IP_grid.addWidget(modbus_IP_retries,1,0,Qt.AlignmentFlag.AlignRight)
        modbus_IP_grid.addWidget(self.modbus_IP_retriesComboBox,1,1,Qt.AlignmentFlag.AlignRight)

        modbus_IP_layout = QVBoxLayout()
        modbus_IP_layout.addLayout(modbus_IP_grid)
        modbus_IP_layout.addStretch()

        modbus_IPgroup = QGroupBox(QApplication.translate('GroupBox', 'UDP/TCP'))
        modbus_IPgroup.setLayout(modbus_IP_layout)

        modbus_PID_IP = QHBoxLayout()
        modbus_PID_IP.addWidget(modbus_pidgroup)
        modbus_PID_IP.addWidget(modbus_Serialgroup)
        modbus_PID_IP.addWidget(modbus_IPgroup)

        scanButton = QPushButton(QApplication.translate('Button','Scan'))
        scanButton.setToolTip(QApplication.translate('Tooltip','Scan MODBUS'))
        scanButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        scanButton.clicked.connect(self.scanModbus)

        self.modbus_optimize = QCheckBox(QApplication.translate('ComboBox','optimize'))
        self.modbus_optimize.setChecked(self.aw.modbus.optimizer)
        self.modbus_optimize.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.modbus_optimize.stateChanged.connect(self.modbus_optimize_toggle)

        self.modbus_full_block = QCheckBox(QApplication.translate('ComboBox','fetch full blocks'))
        self.modbus_full_block.setChecked(self.aw.modbus.fetch_max_blocks)
        self.modbus_full_block.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.modbus_full_block.setEnabled(bool(self.aw.modbus.optimizer))

        ##########################    TAB 4 WIDGETS   SCALE
        scale_devicelabel = QLabel(QApplication.translate('Label', 'Device'))
        self.scale_deviceEdit = QComboBox()
        self.supported_scales = list(self.aw.scale.devicefunctionlist.keys())
        self.scale_deviceEdit.addItems(self.supported_scales)
        try:
            if self.aw.scale.device is not None:
                self.scale_deviceEdit.setCurrentIndex(self.supported_scales.index(self.aw.scale.device))
        except Exception: # pylint: disable=broad-except
            self.scale_deviceEdit.setCurrentIndex(0)
        self.scale_deviceEdit.setEditable(False)
        self.scale_deviceEdit.activated.connect(self.scaleDeviceIndexChanged)
#        scale_devicelabel.setBuddy(self.scale_deviceEdit)
        scale_comportlabel = QLabel(QApplication.translate('Label', 'Comm Port'))
        self.scale_comportEdit = PortComboBox(selection = self.aw.scale.comport)
        self.scale_comportEdit.activated.connect(self.portComboBoxIndexChanged)
#        scale_comportlabel.setBuddy(self.scale_comportEdit)
        scale_baudratelabel = QLabel(QApplication.translate('Label', 'Baud Rate'))
        self.scale_baudrateComboBox = QComboBox()
#        scale_baudratelabel.setBuddy(self.scale_baudrateComboBox)
        self.scale_bauds = ['1200','2400','4800','9600','19200','38400','57600','115200']
        self.scale_baudrateComboBox.addItems(self.scale_bauds)
        try:
            self.scale_baudrateComboBox.setCurrentIndex(self.scale_bauds.index(str(self.aw.scale.baudrate)))
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        scale_bytesizelabel = QLabel(QApplication.translate('Label', 'Byte Size'))
        self.scale_bytesizeComboBox = QComboBox()
#        scale_bytesizelabel.setBuddy(self.scale_bytesizeComboBox)
        self.scale_bytesizes = ['7','8']
        self.scale_bytesizeComboBox.addItems(self.scale_bytesizes)
        self.scale_bytesizeComboBox.setCurrentIndex(self.scale_bytesizes.index(str(self.aw.scale.bytesize)))
        scale_paritylabel = QLabel(QApplication.translate('Label', 'Parity'))
        self.scale_parityComboBox = QComboBox()
#        scale_paritylabel.setBuddy(self.scale_parityComboBox)
        #0 = Odd, E = Even, N = None. NOTE: These strings cannot be translated as they are arguments to the lib pyserial.
        self.scale_parity = ['O','E','N']
        self.scale_parityComboBox.addItems(self.scale_parity)
        self.scale_parityComboBox.setCurrentIndex(self.scale_parity.index(self.aw.scale.parity))
        scale_stopbitslabel = QLabel(QApplication.translate('Label', 'Stopbits'))
        self.scale_stopbitsComboBox = QComboBox()
#        scale_stopbitslabel.setBuddy(self.scale_stopbitsComboBox)
        self.scale_stopbits = ['1','2']
        self.scale_stopbitsComboBox.addItems(self.stopbits)
        self.scale_stopbitsComboBox.setCurrentIndex(self.aw.scale.stopbits - 1)
        scale_timeoutlabel = QLabel(QApplication.translate('Label', 'Timeout'))
        self.scale_timeoutEdit = QLineEdit(str(float2float(self.aw.scale.timeout)))
        self.scale_timeoutEdit.setValidator(self.aw.createCLocaleDoubleValidator(0,5,1,self.scale_timeoutEdit))
        ##########################    TAB 5 WIDGETS   COLOR
        color_devicelabel = QLabel(QApplication.translate('Label', 'Device'))
        self.color_deviceEdit = QComboBox()
        supported_color_meters = list(self.aw.color.devicefunctionlist.keys())
        self.color_deviceEdit.addItems(supported_color_meters)
        try:
            if self.aw.color.device is not None:
                self.color_deviceEdit.setCurrentIndex(supported_color_meters.index(self.aw.color.device))
        except Exception: # pylint: disable=broad-except
            self.color_deviceEdit.setCurrentIndex(0)
        self.color_deviceEdit.setEditable(False)
        self.color_deviceEdit.activated.connect(self.colorDeviceIndexChanged)
#        color_devicelabel.setBuddy(self.color_deviceEdit)
        color_comportlabel = QLabel(QApplication.translate('Label', 'Comm Port'))
        self.color_comportEdit = PortComboBox(selection = self.aw.color.comport)
        self.color_comportEdit.activated.connect(self.portComboBoxIndexChanged)
#        color_comportlabel.setBuddy(self.color_comportEdit)
        color_baudratelabel = QLabel(QApplication.translate('Label', 'Baud Rate'))
        self.color_baudrateComboBox = QComboBox()
#        color_baudratelabel.setBuddy(self.color_baudrateComboBox)
        self.color_bauds = ['1200','2400','4800','9600','19200','38400','57600','115200']
        self.color_baudrateComboBox.addItems(self.color_bauds)
        self.color_baudrateComboBox.setCurrentIndex(self.color_bauds.index(str(self.aw.color.baudrate)))
        color_bytesizelabel = QLabel(QApplication.translate('Label', 'Byte Size'))
        self.color_bytesizeComboBox = QComboBox()
#        color_bytesizelabel.setBuddy(self.color_bytesizeComboBox)
        self.color_bytesizes = ['7','8']
        self.color_bytesizeComboBox.addItems(self.color_bytesizes)
        self.color_bytesizeComboBox.setCurrentIndex(self.color_bytesizes.index(str(self.aw.color.bytesize)))
        color_paritylabel = QLabel(QApplication.translate('Label', 'Parity'))
        self.color_parityComboBox = QComboBox()
#        color_paritylabel.setBuddy(self.color_parityComboBox)
        #0 = Odd, E = Even, N = None. NOTE: These strings cannot be translated as they are arguments to the lib pyserial.
        self.color_parity = ['O','E','N']
        self.color_parityComboBox.addItems(self.color_parity)
        self.color_parityComboBox.setCurrentIndex(self.color_parity.index(self.aw.color.parity))
        color_stopbitslabel = QLabel(QApplication.translate('Label', 'Stopbits'))
        self.color_stopbitsComboBox = QComboBox()
#        color_stopbitslabel.setBuddy(self.color_stopbitsComboBox)
        self.color_stopbits = ['1','2']
        self.color_stopbitsComboBox.addItems(self.stopbits)
        self.color_stopbitsComboBox.setCurrentIndex(self.aw.color.stopbits - 1)
        color_timeoutlabel = QLabel(QApplication.translate('Label', 'Timeout'))
        self.color_timeoutEdit = QLineEdit(str(self.aw.color.timeout))
        self.color_timeoutEdit.setValidator(self.aw.createCLocaleDoubleValidator(0,5,1,self.color_timeoutEdit))
        #### dialog buttons
        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.accept)
        self.dialogbuttons.rejected.connect(self.reject)

        helpButton: Optional[QPushButton] = self.dialogbuttons.addButton(QDialogButtonBox.StandardButton.Help)
        if helpButton is not None:
            helpButton.setToolTip(QApplication.translate('Tooltip','Show help'))
            self.setButtonTranslations(helpButton,'Help',QApplication.translate('Button','Help'))
            helpButton.clicked.connect(self.showModbusbuttonhelp)
            helpButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        #button layout
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.dialogbuttons)
        #LAYOUT TAB 1
        tab1Layout = QVBoxLayout()
        tab1Layout.addWidget(etbt_help_label)
        devid = self.aw.qmc.device
        if (((devid not in self.aw.qmc.nonSerialDevices) or (devid == 134 and self.aw.santokerSerial) or (devid == 138 and self.aw.kaleidoSerial)) and
                not(devid == 0 and self.aw.ser.useModbusPort)): # hide serial confs for MODBUS, Phidget and Yocto devices (but enable for Santoker/Serial)
            grid = QGridLayout()
            grid.addWidget(comportlabel,0,0,Qt.AlignmentFlag.AlignRight)
            grid.addWidget(self.comportEdit,0,1)
            grid.addWidget(baudratelabel,1,0,Qt.AlignmentFlag.AlignRight)
            grid.addWidget(self.baudrateComboBox,1,1)
            grid.addWidget(bytesizelabel,2,0,Qt.AlignmentFlag.AlignRight)
            grid.addWidget(self.bytesizeComboBox,2,1)
            grid.addWidget(paritylabel,3,0,Qt.AlignmentFlag.AlignRight)
            grid.addWidget(self.parityComboBox,3,1)
            grid.addWidget(stopbitslabel,4,0,Qt.AlignmentFlag.AlignRight)
            grid.addWidget(self.stopbitsComboBox,4,1)
            grid.addWidget(timeoutlabel,5,0,Qt.AlignmentFlag.AlignRight)
            grid.addWidget(self.timeoutEdit,5,1)
            gridBoxLayout = QHBoxLayout()
            gridBoxLayout.addLayout(grid)
            gridBoxLayout.addStretch()
            tab1Layout.addLayout(gridBoxLayout)
        tab1Layout.addStretch()
        #LAYOUT TAB 2
        tab2Layout = QVBoxLayout()
        tab2Layout.addWidget(self.serialtable)
        #LAYOUT TAB 3
        modbus_grid = QGridLayout()
        modbus_grid.addWidget(modbus_comportlabel,0,0,Qt.AlignmentFlag.AlignRight)
        modbus_grid.addWidget(self.modbus_comportEdit,0,1)
        modbus_grid.addWidget(modbus_baudratelabel,1,0,Qt.AlignmentFlag.AlignRight)
        modbus_grid.addWidget(self.modbus_baudrateComboBox,1,1)
        modbus_grid.addWidget(modbus_bytesizelabel,2,0,Qt.AlignmentFlag.AlignRight)
        modbus_grid.addWidget(self.modbus_bytesizeComboBox,2,1)
        modbus_grid.addWidget(modbus_paritylabel,3,0,Qt.AlignmentFlag.AlignRight)
        modbus_grid.addWidget(self.modbus_parityComboBox,3,1)
        modbus_grid.addWidget(modbus_stopbitslabel,4,0,Qt.AlignmentFlag.AlignRight)
        modbus_grid.addWidget(self.modbus_stopbitsComboBox,4,1)
        modbus_grid.addWidget(modbus_timeoutlabel,5,0,Qt.AlignmentFlag.AlignRight)
        modbus_grid.addWidget(self.modbus_timeoutEdit,5,1)
        modbus_grid.setContentsMargins(3,3,3,3)
        modbus_grid.setSpacing(5)
        modbus_gridV = QVBoxLayout()
        modbus_gridV.addStretch()
        modbus_gridV.addLayout(modbus_grid)
        modbus_gridV.addStretch()

        modbus_serial_group = QGroupBox(QApplication.translate('GroupBox','Serial'))
        modbus_serial_group.setLayout(modbus_gridV)
        modbus_serial_group.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Preferred)

        modbus_input_grid = QGridLayout()

        modbus_input_grid.addWidget(modbus_input1slavelabel,1,0,Qt.AlignmentFlag.AlignRight)
        modbus_input_grid.addWidget(modbus_input1registerlabel,2,0,Qt.AlignmentFlag.AlignRight)
        modbus_input_grid.addWidget(modbus_input1codelabel,3,0,Qt.AlignmentFlag.AlignRight)
        modbus_input_grid.addWidget(modbus_input1divlabel,4,0,Qt.AlignmentFlag.AlignRight)
        modbus_input_grid.addWidget(modbus_input1modelabel,5,0,Qt.AlignmentFlag.AlignRight)
        modbus_input_grid.addWidget(modbus_input1floatlabel,6,0,Qt.AlignmentFlag.AlignRight)

        for i in range(self.aw.modbus.channels):
            if (len(self.modbus_inputSlaveEdits)>i and
                    len(self.modbus_inputRegisterEdits)>i and
                    len(self.modbus_inputCodes)>i and
                    len(self.modbus_inputDivs)>i and
                    len(self.modbus_inputModes)>i and
                    len(self.modbus_inputDecodes)>i):
                modbus_input_grid.addWidget(QLabel(QApplication.translate('GroupBox', 'Input') + ' ' + str(i+1)),0,i+1,Qt.AlignmentFlag.AlignCenter)
                inputSlaveEdit:Optional[QLineEdit] = self.modbus_inputSlaveEdits[i]
                inputRegisterEdit:Optional[QLineEdit] = self.modbus_inputRegisterEdits[i]
                inputCode:Optional[QComboBox] = self.modbus_inputCodes[i]
                inputDiv:Optional[QComboBox] = self.modbus_inputDivs[i]
                inputMode:Optional[QComboBox] = self.modbus_inputModes[i]
                inputDecode:Optional[QComboBox] = self.modbus_inputDecodes[i]
                if (inputSlaveEdit is not None and
                        inputRegisterEdit is not None and
                        inputCode is not None and
                        inputDiv is not None and
                        inputMode is not None and
                        inputDecode is not None):
                    modbus_input_grid.addWidget(inputSlaveEdit,1,i+1)
                    modbus_input_grid.addWidget(inputRegisterEdit,2,i+1)
                    modbus_input_grid.addWidget(inputCode,3,i+1)
                    modbus_input_grid.addWidget(inputDiv,4,i+1)
                    modbus_input_grid.addWidget(inputMode,5,i+1)
                    modbus_input_grid.addWidget(inputDecode,6,i+1,Qt.AlignmentFlag.AlignCenter)

        modbus_input_grid.setContentsMargins(0,0,0,0)
        modbus_input_grid.setSpacing(5)

        modbus_input_scroll = QScrollArea()
        modbus_input_scroll.setWidgetResizable(False)
        modbus_input_scroll_content = QFrame()
        modbus_input_scroll_content.setSizePolicy(QSizePolicy.Policy.MinimumExpanding,QSizePolicy.Policy.Ignored)
        modbus_input_scroll_content.setLayout(modbus_input_grid)
        modbus_input_scroll.setWidget(modbus_input_scroll_content)


        modbus_gridVLayout = QHBoxLayout()
        modbus_gridVLayout.addWidget(modbus_serial_group)
        modbus_gridVLayout.addWidget(modbus_input_scroll)
        modbus_setup = QHBoxLayout()
        modbus_setup.addWidget(scanButton)
        modbus_setup.addStretch()
        modbus_setup.addSpacing(7)
        modbus_setup.addWidget(modbus_endianlabel)
        modbus_setup.addSpacing(5)
        modbus_setup.addWidget(self.modbus_littleEndianWords)
        modbus_setup.addStretch()
        modbus_setup.addSpacing(15)
        modbus_setup.addWidget(self.modbus_optimize)
        modbus_setup.addSpacing(5)
        modbus_setup.addWidget(self.modbus_full_block)
        modbus_setup.addSpacing(7)
        modbus_setup.addStretch()
        modbus_setup.addWidget(modbus_typelabel)
        modbus_setup.addWidget(self.modbus_type)
        modbus_setup.addStretch()
        modbus_setup.addWidget(modbus_hostlabel)
        modbus_setup.addWidget(self.modbus_hostEdit)
        modbus_setup.addSpacing(7)
        modbus_setup.addWidget(modbus_portlabel)
        modbus_setup.addWidget(self.modbus_portEdit)
        tab3Layout = QVBoxLayout()
        tab3Layout.addLayout(modbus_gridVLayout)
        tab3Layout.addLayout(modbus_PID_IP)
        tab3Layout.addStretch()
        tab3Layout.addLayout(modbus_setup)
        tab3Layout.addStretch()
        tab3Layout.setContentsMargins(0,0,0,0)
        tab3Layout.setSpacing(5)

        #LAYOUT TAB 4
        # host (IP or hostname)
        s7_hostlabel = QLabel(QApplication.translate('Label', 'Host'))
        self.s7_hostEdit = QLineEdit(str(self.aw.s7.host))
        self.s7_hostEdit.setFixedWidth(120)
        self.s7_hostEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # port (default 102)
        s7_portlabel = QLabel(QApplication.translate('Label', 'Port'))
        self.s7_portEdit = QLineEdit(str(self.aw.s7.port))
        self.s7_portEdit.setValidator(QIntValidator(1,65535,self.s7_portEdit))
        self.s7_portEdit.setFixedWidth(60)
        self.s7_portEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # rack (default 0)
        s7_racklabel = QLabel(QApplication.translate('Label', 'Rack'))
        self.s7_rackEdit = QLineEdit(str(self.aw.s7.rack))
        self.s7_rackEdit.setValidator(QIntValidator(0,7,self.s7_rackEdit))
        self.s7_rackEdit.setFixedWidth(60)
        self.s7_rackEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # slot (default 0)
        s7_slotlabel = QLabel(QApplication.translate('Label', 'Slot'))
        self.s7_slotEdit = QLineEdit(str(self.aw.s7.slot))
        self.s7_slotEdit.setValidator(QIntValidator(0,31,self.s7_slotEdit))
        self.s7_slotEdit.setFixedWidth(60)
        self.s7_slotEdit.setAlignment(Qt.AlignmentFlag.AlignRight)

        scanButtonS7 = QPushButton(QApplication.translate('Button','Scan'))
        scanButtonS7.setToolTip(QApplication.translate('Tooltip','Scan S7'))
        scanButtonS7.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        scanButtonS7.clicked.connect(self.scanS7)

        self.s7_optimize = QCheckBox(QApplication.translate('ComboBox','optimize'))
        self.s7_optimize.setChecked(self.aw.s7.optimizer)
        self.s7_optimize.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.s7_optimize.stateChanged.connect(self.s7_optimize_toggle)

        self.s7_full_block = QCheckBox(QApplication.translate('ComboBox','fetch full blocks'))
        self.s7_full_block.setChecked(self.aw.s7.fetch_max_blocks)
        self.s7_full_block.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.s7_full_block.setEnabled(bool(self.aw.s7.optimizer))

        s7_areaLabel = QLabel(QApplication.translate('Label', 'Area'))
        s7_dbLabel = QLabel(QApplication.translate('Label', 'DB#'))
        s7_startLabel = QLabel(QApplication.translate('Label', 'Start'))
        s7_typeLabel = QLabel(QApplication.translate('Label', 'Type'))
        s7_modeLabel = QLabel(QApplication.translate('Label', 'Mode'))
        s7_divLabel = QLabel(QApplication.translate('Label', 'Factor'))

        self.s7_areaCombos = []
        self.s7_dbEdits = []
        self.s7_startEdits = []
        self.s7_typeCombos = []
        self.s7_modeCombos = []
        self.s7_divCombos = []

        s7_areas = [' ','PE','PA','MK','CT','TM','DB']
        s7_types = ['Int', 'Float', 'IntFloat','Bool(0)', 'Bool(1)', 'Bool(2)', 'Bool(3)', 'Bool(4)', 'Bool(5)', 'Bool(6)', 'Bool(7)']

        s7_grid = QGridLayout()

        s7_grid.addWidget(s7_areaLabel,1,0,Qt.AlignmentFlag.AlignRight)
        s7_grid.addWidget(s7_dbLabel,2,0,Qt.AlignmentFlag.AlignRight)
        s7_grid.addWidget(s7_startLabel,3,0,Qt.AlignmentFlag.AlignRight)
        s7_grid.addWidget(s7_typeLabel,4,0,Qt.AlignmentFlag.AlignRight)
        s7_grid.addWidget(s7_divLabel,5,0,Qt.AlignmentFlag.AlignRight)
        s7_grid.addWidget(s7_modeLabel,6,0,Qt.AlignmentFlag.AlignRight)

        for i in range(self.aw.s7.channels):
            # channel label
            label = QLabel(QApplication.translate('Label', 'Input') + ' ' + str(i+1))
            s7_grid.addWidget(label,0,i+1,Qt.AlignmentFlag.AlignRight)
            # area combo
            area = QComboBox()
            area.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            area.addItems(s7_areas)
            area.setCurrentIndex(self.aw.s7.area[i])
            area.setFixedWidth(70)
            self.s7_areaCombos.append(area)
            s7_grid.addWidget(area,1,i+1,Qt.AlignmentFlag.AlignRight)
            # db edit: 1-16000
            dbEdit = QLineEdit(str(self.aw.s7.db_nr[i]))
            dbEdit.setFixedWidth(65)
            dbEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.s7_dbEdits.append(dbEdit)
            dbEdit.setValidator(QIntValidator(1,16000,self.s7_dbEdits[i]))
            s7_grid.addWidget(dbEdit,2,i+1,Qt.AlignmentFlag.AlignRight)
            # start edit:
            startEdit = QLineEdit(str(self.aw.s7.start[i]))
            startEdit.setFixedWidth(65)
            startEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.s7_startEdits.append(startEdit)
            startEdit.setValidator(QIntValidator(0,65536,self.s7_startEdits[i]))
            s7_grid.addWidget(startEdit,3,i+1,Qt.AlignmentFlag.AlignRight)
            # type combo: Int, Float
            tp = QComboBox()
            tp.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            tp.addItems(s7_types)
            tp.setCurrentIndex(self.aw.s7.type[i])
            tp.setFixedWidth(70)
            self.s7_typeCombos.append(tp)
            s7_grid.addWidget(tp,4,i+1,Qt.AlignmentFlag.AlignRight)
            # div combo: -,1/10,1/100
            div = QComboBox()
            div.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            div.addItems(modbus_divs)
            div.setCurrentIndex(self.aw.s7.div[i])
            div.setFixedWidth(70)
            self.s7_divCombos.append(div)
            s7_grid.addWidget(div,5,i+1,Qt.AlignmentFlag.AlignRight)
            # mode combo: -,C,F
            mode = QComboBox()
            mode.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            mode.addItems(modbus_modes)
            mode.setCurrentIndex(self.aw.s7.mode[i])
            mode.setFixedWidth(70)
            self.s7_modeCombos.append(mode)
            s7_grid.addWidget(mode,6,i+1,Qt.AlignmentFlag.AlignRight)

        # s7 external PID conf

        s7_PIDareaLabel = QLabel(QApplication.translate('Label', 'Area'))
        self.s7_PIDarea = QComboBox()
        self.s7_PIDarea.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.s7_PIDarea.addItems(s7_areas)
        self.s7_PIDarea.setCurrentIndex(self.aw.s7.PID_area)
        self.s7_PIDarea.setFixedWidth(70)
        s7_PIDdb_nr_label = QLabel(QApplication.translate('Label', 'DB#'))
        self.s7_PIDdb_nr_Edit = QLineEdit(str(self.aw.s7.PID_db_nr))
        self.s7_PIDdb_nr_Edit.setValidator(QIntValidator(0,65536,self.s7_PIDdb_nr_Edit))
        self.s7_PIDdb_nr_Edit.setFixedWidth(50)
        self.s7_PIDdb_nr_Edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        s7_SVregister_label = QLabel(QApplication.translate('Label', 'SV'))
        self.s7_SVregister_Edit = QLineEdit(str(self.aw.s7.PID_SV_register))
        self.s7_SVregister_Edit.setValidator(QIntValidator(0,65536,self.s7_SVregister_Edit))
        self.s7_SVregister_Edit.setFixedWidth(50)
        self.s7_SVregister_Edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        s7_SVtypes = ['Int', 'Float']

        s7_SVtype_label = QLabel(QApplication.translate('Label', 'Type'))
        self.s7_SVtype = QComboBox()
        self.s7_SVtype.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.s7_SVtype.addItems(s7_SVtypes)
        self.s7_SVtype.setCurrentIndex(self.aw.s7.SVtype)
        self.s7_SVtype.setFixedWidth(70)

        s7_multis = ['', '10','100']

        s7_SVmultiplier_label = QLabel(QApplication.translate('Label', 'SV Factor'))
        self.s7_SVmultiplier = QComboBox()
        self.s7_SVmultiplier.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.s7_SVmultiplier.addItems(s7_multis)
        self.s7_SVmultiplier.setCurrentIndex(self.aw.s7.SVmultiplier)
        self.s7_SVmultiplier.setFixedWidth(70)

        s7_PIDmultiplier_label = QLabel(QApplication.translate('Label', 'pid Factor'))
        self.s7_PIDmultiplier = QComboBox()
        self.s7_PIDmultiplier.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.s7_PIDmultiplier.addItems(s7_multis)
        self.s7_PIDmultiplier.setCurrentIndex(self.aw.s7.PIDmultiplier)
        self.s7_PIDmultiplier.setFixedWidth(70)

        s7_Pregister_label = QLabel(QApplication.translate('Label', 'P'))
        self.s7_Pregister_Edit = QLineEdit(str(self.aw.s7.PID_p_register))
        self.s7_Pregister_Edit.setValidator(QIntValidator(0,65536,self.s7_Pregister_Edit))
        self.s7_Pregister_Edit.setFixedWidth(50)
        self.s7_Pregister_Edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        s7_Iregister_label = QLabel(QApplication.translate('Label', 'I'))
        self.s7_Iregister_Edit = QLineEdit(str(self.aw.s7.PID_i_register))
        self.s7_Iregister_Edit.setValidator(QIntValidator(0,65536,self.s7_Iregister_Edit))
        self.s7_Iregister_Edit.setFixedWidth(50)
        self.s7_Iregister_Edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        s7_Dregister_label = QLabel(QApplication.translate('Label', 'D'))
        self.s7_Dregister_Edit = QLineEdit(str(self.aw.s7.PID_d_register))
        self.s7_Dregister_Edit.setValidator(QIntValidator(0,65536,self.s7_Dregister_Edit))
        self.s7_Dregister_Edit.setFixedWidth(50)
        self.s7_Dregister_Edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        s7_pid_registers = QHBoxLayout()
        s7_pid_registers.addWidget(s7_SVregister_label)
        s7_pid_registers.addWidget(self.s7_SVregister_Edit)
        s7_pid_registers.addSpacing(30)
        s7_pid_registers.addStretch()
        s7_pid_registers.addWidget(s7_Pregister_label)
        s7_pid_registers.addWidget(self.s7_Pregister_Edit)
        s7_pid_registers.addSpacing(10)
        s7_pid_registers.addStretch()
        s7_pid_registers.addWidget(s7_Iregister_label)
        s7_pid_registers.addWidget(self.s7_Iregister_Edit)
        s7_pid_registers.addSpacing(10)
        s7_pid_registers.addStretch()
        s7_pid_registers.addWidget(s7_Dregister_label)
        s7_pid_registers.addWidget(self.s7_Dregister_Edit)

        s7_pid_multipliers = QHBoxLayout()
        s7_pid_multipliers.addWidget(s7_SVtype_label)
        s7_pid_multipliers.addWidget(self.s7_SVtype)
        s7_pid_multipliers.addSpacing(10)
        s7_pid_multipliers.addWidget(s7_SVmultiplier_label)
        s7_pid_multipliers.addWidget(self.s7_SVmultiplier)
        s7_pid_multipliers.addStretch()
        s7_pid_multipliers.addWidget(s7_PIDmultiplier_label)
        s7_pid_multipliers.addWidget(self.s7_PIDmultiplier)

        s7_pid_regmulti = QVBoxLayout()
        s7_pid_regmulti.addLayout(s7_pid_registers)
        s7_pid_regmulti.addLayout(s7_pid_multipliers)

        s7_pid_registers_box = QGroupBox(QApplication.translate('GroupBox','Registers'))
        s7_pid_registers_box.setLayout(s7_pid_regmulti)
        s7_pid_regmulti.setContentsMargins(2,2,20,2)

        s7_pid_off_label = QLabel(QApplication.translate('Label', 'OFF'))
        self.s7_pid_off = QLineEdit(self.aw.s7.PID_OFF_action)
        self.s7_pid_off.setToolTip(QApplication.translate('Tooltip', 'OFF Action String'))
        s7_pid_on_label = QLabel(QApplication.translate('Label', 'ON'))
        self.s7_pid_on = QLineEdit(self.aw.s7.PID_ON_action)
        self.s7_pid_on.setToolTip(QApplication.translate('Tooltip', 'ON Action String'))

        s7_pid_commands = QGridLayout()
        s7_pid_commands.addWidget(s7_pid_on_label,0,0)
        s7_pid_commands.addWidget(self.s7_pid_on,0,1)
        s7_pid_commands.addWidget(s7_pid_off_label,1,0)
        s7_pid_commands.addWidget(self.s7_pid_off,1,1)

        s7_pid_commands_box = QGroupBox(QApplication.translate('GroupBox','Commands'))
        s7_pid_commands_box.setLayout(s7_pid_commands)
        s7_pid_commands.setContentsMargins(2,2,20,2)

        s7_pid_area = QHBoxLayout()
        s7_pid_area.addWidget(s7_PIDareaLabel)
        s7_pid_area.addWidget(self.s7_PIDarea)

        s7_pid_dbnr = QHBoxLayout()
        s7_pid_dbnr.addWidget(s7_PIDdb_nr_label)
        s7_pid_dbnr.addWidget(self.s7_PIDdb_nr_Edit)

        s7_pid_base = QVBoxLayout()
        s7_pid_base.addLayout(s7_pid_area)
        s7_pid_base.addLayout(s7_pid_dbnr)

        s7_pid = QHBoxLayout()
        s7_pid.addStretch()
        s7_pid.addLayout(s7_pid_base)
        s7_pid.addWidget(s7_pid_registers_box)
        s7_pid.addWidget(s7_pid_commands_box)
        s7_pid.addStretch()

        s7_pidgroup = QGroupBox(QApplication.translate('GroupBox', 'PID'))
        s7_pidgroup.setLayout(s7_pid)
        s7_pid.setContentsMargins(0,10,0,0)
        s7_pidgroup.setContentsMargins(0,20,0,3)

        s7_gridHLayout = QHBoxLayout()
        s7_gridHLayout.addStretch()
        s7_gridHLayout.addLayout(s7_grid)
        s7_gridHLayout.addStretch()

        s7_setup = QHBoxLayout()
        s7_setup.addWidget(scanButtonS7)
        s7_setup.addStretch()
        s7_setup.addSpacing(7)
        s7_setup.addWidget(self.s7_optimize)
        s7_setup.addSpacing(5)
        s7_setup.addWidget(self.s7_full_block)
        s7_setup.addSpacing(7)
        s7_setup.addStretch()
        s7_setup.addWidget(s7_hostlabel)
        s7_setup.addWidget(self.s7_hostEdit)
        s7_setup.addSpacing(7)
        s7_setup.addWidget(s7_portlabel)
        s7_setup.addWidget(self.s7_portEdit)
        s7_setup.addStretch()
        s7_setup.addWidget(s7_racklabel)
        s7_setup.addWidget(self.s7_rackEdit)
        s7_setup.addSpacing(7)
        s7_setup.addWidget(s7_slotlabel)
        s7_setup.addWidget(self.s7_slotEdit)
        s7_setup.addStretch()

        tab4Layout = QVBoxLayout()
        tab4Layout.addStretch()
        tab4Layout.addLayout(s7_gridHLayout)
        tab4Layout.addWidget(s7_pidgroup)
        tab4Layout.addStretch()
        tab4Layout.addLayout(s7_setup)
        tab4Layout.addStretch()
        tab4Layout.setContentsMargins(0,0,0,0)
        tab4Layout.setSpacing(5)

        #LAYOUT TAB 5
        scale_grid = QGridLayout()
        scale_grid.addWidget(scale_devicelabel,0,0,Qt.AlignmentFlag.AlignRight)
        scale_grid.addWidget(self.scale_deviceEdit,0,1)
        scale_grid.addWidget(scale_comportlabel,1,0,Qt.AlignmentFlag.AlignRight)
        scale_grid.addWidget(self.scale_comportEdit,1,1)
        scale_grid.addWidget(scale_baudratelabel,2,0,Qt.AlignmentFlag.AlignRight)
        scale_grid.addWidget(self.scale_baudrateComboBox,2,1)
        scale_grid.addWidget(scale_bytesizelabel,3,0,Qt.AlignmentFlag.AlignRight)
        scale_grid.addWidget(self.scale_bytesizeComboBox,3,1)
        scale_grid.addWidget(scale_paritylabel,4,0,Qt.AlignmentFlag.AlignRight)
        scale_grid.addWidget(self.scale_parityComboBox,4,1)
        scale_grid.addWidget(scale_stopbitslabel,5,0,Qt.AlignmentFlag.AlignRight)
        scale_grid.addWidget(self.scale_stopbitsComboBox,5,1)
        scale_grid.addWidget(scale_timeoutlabel,6,0,Qt.AlignmentFlag.AlignRight)
        scale_grid.addWidget(self.scale_timeoutEdit,6,1)
        scaleH = QHBoxLayout()
        scaleH.addLayout(scale_grid)
        scaleH.addStretch()
        tab5Layout = QVBoxLayout()
        tab5Layout.addLayout(scaleH)
        tab5Layout.addStretch()

        #LAYOUT TAB 6
        color_grid = QGridLayout()
        color_grid.addWidget(color_devicelabel,0,0,Qt.AlignmentFlag.AlignRight)
        color_grid.addWidget(self.color_deviceEdit,0,1)
        color_grid.addWidget(color_comportlabel,1,0,Qt.AlignmentFlag.AlignRight)
        color_grid.addWidget(self.color_comportEdit,1,1)
        color_grid.addWidget(color_baudratelabel,2,0,Qt.AlignmentFlag.AlignRight)
        color_grid.addWidget(self.color_baudrateComboBox,2,1)
        color_grid.addWidget(color_bytesizelabel,3,0,Qt.AlignmentFlag.AlignRight)
        color_grid.addWidget(self.color_bytesizeComboBox,3,1)
        color_grid.addWidget(color_paritylabel,4,0,Qt.AlignmentFlag.AlignRight)
        color_grid.addWidget(self.color_parityComboBox,4,1)
        color_grid.addWidget(color_stopbitslabel,5,0,Qt.AlignmentFlag.AlignRight)
        color_grid.addWidget(self.color_stopbitsComboBox,5,1)
        color_grid.addWidget(color_timeoutlabel,6,0,Qt.AlignmentFlag.AlignRight)
        color_grid.addWidget(self.color_timeoutEdit,6,1)
        colorH = QHBoxLayout()
        colorH.addLayout(color_grid)
        colorH.addStretch()
        tab6Layout = QVBoxLayout()
        tab6Layout.addLayout(colorH)
        tab6Layout.addStretch()
        #
        # host (IP or hostname)
        ws_hostlabel = QLabel(QApplication.translate('Label', 'Host'))
        self.ws_hostEdit = QLineEdit(str(self.aw.ws.host))
        self.ws_hostEdit.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_hostEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # port (default 102)
        ws_portlabel = QLabel(QApplication.translate('Label', 'Port'))
        self.ws_portEdit = QLineEdit(str(self.aw.ws.port))
        self.ws_portEdit.setValidator(QIntValidator(1,65535,self.ws_portEdit))
        self.ws_portEdit.setFixedWidth(40)
        self.ws_portEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # rack (default 0)
        ws_pathlabel = QLabel(QApplication.translate('Label', 'Path'))
        self.ws_pathEdit = QLineEdit(str(self.aw.ws.path))
        self.ws_pathEdit.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_pathEdit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.ws_pathEdit.setCursorPosition(0)
        # slot (default 0)
        ws_machineIDlabel = QLabel(QApplication.translate('Label', 'ID'))
        self.ws_machineIDEdit = QLineEdit(str(self.aw.ws.machineID))
        self.ws_machineIDEdit.setValidator(QIntValidator(0,99999,self.ws_machineIDEdit))
        self.ws_machineIDEdit.setFixedWidth(25)
        self.ws_machineIDEdit.setAlignment(Qt.AlignmentFlag.AlignRight)

        ws_setup = QHBoxLayout()
        ws_setup.addWidget(ws_hostlabel)
        ws_setup.addWidget(self.ws_hostEdit)
        ws_setup.addSpacing(7)
        ws_setup.addWidget(ws_portlabel)
        ws_setup.addWidget(self.ws_portEdit)
        ws_setup.addSpacing(7)
        ws_setup.addWidget(ws_pathlabel)
        ws_setup.addWidget(self.ws_pathEdit)
        ws_setup.addSpacing(7)
        ws_setup.addWidget(ws_machineIDlabel)
        ws_setup.addWidget(self.ws_machineIDEdit)
        ws_setup.setSpacing(5)
        ws_setup.setContentsMargins(5,5,5,5)

        ws_setup_box = QGroupBox(QApplication.translate('GroupBox','Machine'))
        ws_setup_box.setLayout(ws_setup)

        self.ws_connect_timeout = QDoubleSpinBox()
        self.ws_connect_timeout.setSingleStep(1)
        self.ws_connect_timeout.setValue(self.aw.ws.connect_timeout)
        self.ws_connect_timeout.setRange(0,5)
        self.ws_connect_timeout.setDecimals(1)
        self.ws_connect_timeout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.ws_connect_timeout.setSuffix('s')

        self.ws_reconnect_timeout = QDoubleSpinBox()
        self.ws_reconnect_timeout.setSingleStep(1)
        self.ws_reconnect_timeout.setValue(self.aw.ws.reconnect_interval)
        self.ws_reconnect_timeout.setRange(0,5)
        self.ws_reconnect_timeout.setDecimals(1)
        self.ws_reconnect_timeout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.ws_reconnect_timeout.setSuffix('s')

        self.ws_request_timeout = QDoubleSpinBox()
        self.ws_request_timeout.setSingleStep(1)
        self.ws_request_timeout.setValue(self.aw.ws.request_timeout)
        self.ws_request_timeout.setRange(0,5)
        self.ws_request_timeout.setDecimals(1)
        self.ws_request_timeout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.ws_request_timeout.setSuffix('s')

        ws_timeouts = QHBoxLayout()
        ws_timeouts.addWidget(QLabel(QApplication.translate('Label','Connect')))
        ws_timeouts.addWidget(self.ws_connect_timeout)
        ws_timeouts.addSpacing(7)
        ws_timeouts.addWidget(QLabel(QApplication.translate('Label','Reconnect')))
        ws_timeouts.addWidget(self.ws_reconnect_timeout)
        ws_timeouts.addSpacing(7)
        ws_timeouts.addWidget(QLabel(QApplication.translate('Label','Request')))
        ws_timeouts.addWidget(self.ws_request_timeout)
        ws_timeouts.setSpacing(5)
        ws_timeouts.setContentsMargins(5,5,5,5)

        ws_timeouts_box = QGroupBox(QApplication.translate('GroupBox','Timeout'))
        ws_timeouts_box.setLayout(ws_timeouts)

        ws_line1 = QHBoxLayout()
        ws_line1.addWidget(ws_setup_box)
        ws_line1.addWidget(ws_timeouts_box)

        self.ws_messageID = QLineEdit(str(self.aw.ws.id_node))
        self.ws_messageID.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_messageID.setCursorPosition(0)
        self.ws_machineID = QLineEdit(str(self.aw.ws.machine_node))
        self.ws_machineID.setMinimumWidth(70)
        self.ws_messageID.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_machineID.setCursorPosition(0)
        self.ws_message = QLineEdit(str(self.aw.ws.pushMessage_node))
        self.ws_message.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_message.setCursorPosition(0)
        self.ws_command = QLineEdit(str(self.aw.ws.command_node))
        self.ws_command.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_command.setCursorPosition(0)
        self.ws_data = QLineEdit(str(self.aw.ws.data_node))
        self.ws_data.setCursorPosition(0)

        ws_nodes = QGridLayout()
        ws_nodes.addWidget(QLabel(QApplication.translate('Label','Message ID')),0,0)
        ws_nodes.addWidget(self.ws_messageID,1,0)
        ws_nodes.addWidget(QLabel(QApplication.translate('Label','Machine ID')),0,1)
        ws_nodes.addWidget(self.ws_machineID,1,1)
        ws_nodes.addWidget(QLabel(QApplication.translate('Label','Command')),0,2)
        ws_nodes.addWidget(self.ws_command,1,2)
        ws_nodes.addWidget(QLabel(QApplication.translate('Label','Data')),0,3)
        ws_nodes.addWidget(self.ws_data,1,3)
        ws_nodes.addWidget(QLabel(QApplication.translate('Label','Message')),0,4)
        ws_nodes.addWidget(self.ws_message,1,4)
        ws_nodes.setSpacing(5)
        ws_nodes.setContentsMargins(5,5,5,5)

        ws_nodes_box = QGroupBox(QApplication.translate('GroupBox','Nodes'))
        ws_nodes_box.setLayout(ws_nodes)

        self.ws_data_request = QLineEdit(str(self.aw.ws.request_data_command))
        self.ws_data_request.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_data_request.setCursorPosition(0)
        ws_commands = QGridLayout()
        ws_commands.addWidget(QLabel(QApplication.translate('Label','Data Request')),0,0)
        ws_commands.addWidget(self.ws_data_request,1,0)
        ws_commands.setSpacing(5)
        ws_commands.setContentsMargins(5,5,5,5)

        ws_commands_box = QGroupBox(QApplication.translate('GroupBox','Commands'))
        ws_commands_box.setLayout(ws_commands)


        self.ws_charge = QLineEdit(str(self.aw.ws.charge_message))
        self.ws_charge.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_charge.setCursorPosition(0)
        self.ws_drop = QLineEdit(str(self.aw.ws.drop_message))
        self.ws_drop.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_drop.setCursorPosition(0)
        ws_messages = QGridLayout()
        ws_messages.addWidget(QLabel(QApplication.translate('Label','CHARGE')),0,0)
        ws_messages.addWidget(self.ws_charge,1,0)
        ws_messages.addWidget(QLabel(QApplication.translate('Label','DROP')),0,1)
        ws_messages.addWidget(self.ws_drop,1,1)
        ws_messages.setSpacing(5)
        ws_messages.setContentsMargins(5,5,5,5)

        ws_messages_box = QGroupBox(QApplication.translate('GroupBox','Messages'))
        ws_messages_box.setLayout(ws_messages)

        self.ws_STARTonCHARGE = QCheckBox(QApplication.translate('CheckBox','START on CHARGE'))
        self.ws_STARTonCHARGE.setChecked(self.aw.ws.STARTonCHARGE)
        self.ws_OFFonDROP = QCheckBox(QApplication.translate('CheckBox','OFF on DROP'))
        self.ws_OFFonDROP.setChecked(self.aw.ws.OFFonDROP)
        ws_flags = QGridLayout()
        ws_flags.addWidget(self.ws_STARTonCHARGE,0,0)
        ws_flags.addWidget(self.ws_OFFonDROP,1,0)
        ws_flags.setSpacing(5)
        ws_flags.setContentsMargins(5,5,5,5)

        ws_flags_box = QGroupBox(QApplication.translate('GroupBox','Flags'))
        ws_flags_box.setLayout(ws_flags)

        ws_line2 = QHBoxLayout()
        ws_line2.addWidget(ws_nodes_box,35)
        ws_line2.addWidget(ws_commands_box,20)
        ws_line2.addWidget(ws_messages_box,30)
        ws_line2.addWidget(ws_flags_box,15)

        #

        self.ws_event_message = QLineEdit(str(self.aw.ws.addEvent_message))
        self.ws_event_message.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_event_message.setCursorPosition(0)

        self.ws_event = QLineEdit(str(self.aw.ws.event_node))
        self.ws_event.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_event.setCursorPosition(0)

        self.ws_DRY = QLineEdit(str(self.aw.ws.DRY_node))
        self.ws_DRY.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_DRY.setCursorPosition(0)

        self.ws_FCs = QLineEdit(str(self.aw.ws.FCs_node))
        self.ws_FCs.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_FCs.setCursorPosition(0)

        self.ws_FCe = QLineEdit(str(self.aw.ws.FCe_node))
        self.ws_FCe.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_FCe.setCursorPosition(0)

        self.ws_SCs = QLineEdit(str(self.aw.ws.SCs_node))
        self.ws_SCs.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_SCs.setCursorPosition(0)

        self.ws_SCe = QLineEdit(str(self.aw.ws.SCe_node))
        self.ws_SCe.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.ws_SCe.setCursorPosition(0)

        ws_events = QGridLayout()
        ws_events.addWidget(QLabel(QApplication.translate('Label','Event')),0,0)
        ws_events.addWidget(self.ws_event_message,1,0)
        ws_events.addWidget(QLabel(QApplication.translate('Label','Node')),0,1)
        ws_events.addWidget(self.ws_event,1,1)

        ws_events.addWidget(QLabel(QApplication.translate('Label','DRY')),0,3)
        ws_events.addWidget(self.ws_DRY,1,3)
        ws_events.addWidget(QLabel(QApplication.translate('Label','FCs')),0,4)
        ws_events.addWidget(self.ws_FCs,1,4)
        ws_events.addWidget(QLabel(QApplication.translate('Label','FCe')),0,5)
        ws_events.addWidget(self.ws_FCe,1,5)
        ws_events.addWidget(QLabel(QApplication.translate('Label','SCs')),0,6)
        ws_events.addWidget(self.ws_SCs,1,6)
        ws_events.addWidget(QLabel(QApplication.translate('Label','SCe')),0,7)
        ws_events.addWidget(self.ws_SCe,1,7)
        ws_events.setContentsMargins(5,5,5,5)
        ws_events.setSpacing(5)
        ws_events.setColumnMinimumWidth(2,20)

        ws_events_box = QGroupBox(QApplication.translate('GroupBox','Events'))
        ws_events_box.setLayout(ws_events)

        ws_line3 = QHBoxLayout()
        ws_line3.addWidget(ws_events_box)


        self.ws_requestEdits = []
        self.ws_nodeEdits = []
        self.ws_modeCombos = []

        ws_grid = QGridLayout()

        ws_requestLabel = QLabel(QApplication.translate('Label', 'Request'))
        ws_nodeLabel = QLabel(QApplication.translate('Label', 'Node'))
        ws_modeLabel = QLabel(QApplication.translate('Label', 'Mode'))

        ws_grid.addWidget(ws_requestLabel,1,0,Qt.AlignmentFlag.AlignRight)
        ws_grid.addWidget(ws_nodeLabel,2,0,Qt.AlignmentFlag.AlignRight)
        ws_grid.addWidget(ws_modeLabel,3,0,Qt.AlignmentFlag.AlignRight)


        for i in range(self.aw.ws.channels):
            # channel label
            label = QLabel(QApplication.translate('Label', 'Input') + ' ' + str(i+1))
            ws_grid.addWidget(label,0,i+1,Qt.AlignmentFlag.AlignRight)

            # request edit
            request_edit = QLineEdit(str(self.aw.ws.channel_requests[i]))
            request_edit.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
            request_edit.setCursorPosition(0)
            self.ws_requestEdits.append(request_edit)
            ws_grid.addWidget(request_edit,1,i+1,Qt.AlignmentFlag.AlignRight)

            # node edit
            node_edit = QLineEdit(str(self.aw.ws.channel_nodes[i]))
            node_edit.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
            node_edit.setCursorPosition(0)
            self.ws_nodeEdits.append(node_edit)
            ws_grid.addWidget(node_edit,2,i+1,Qt.AlignmentFlag.AlignRight)

            # mode combo: -,C,F
            mode = QComboBox()
            mode.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            mode.addItems(modbus_modes)
            mode.setCurrentIndex(self.aw.ws.channel_modes[i])
            self.ws_modeCombos.append(mode)
            ws_grid.addWidget(mode,3,i+1,1,1) #Qt.AlignmentFlag.AlignRight)

        self.ws_compression = QCheckBox(QApplication.translate('ComboBox','compression'))
        self.ws_compression.setChecked(self.aw.ws.compression)

        ws_line4 = QHBoxLayout()
        ws_line4.addStretch()
        ws_line4.addLayout(ws_grid)
        ws_line4.addStretch()

        ws_line5 = QHBoxLayout()
        ws_line5.addWidget(self.ws_compression)
        ws_line5.addStretch()


        tab7Layout = QVBoxLayout()
        tab7Layout.addLayout(ws_line1)
        tab7Layout.addLayout(ws_line2)
        tab7Layout.addLayout(ws_line3)
        tab7Layout.addLayout(ws_line4)
        tab7Layout.addLayout(ws_line5)
        tab7Layout.addStretch()
        tab7Layout.setSpacing(8)
        tab7Layout.setContentsMargins(5,5,5,5)
        #tab widget
        self.TabWidget = QTabWidget()
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        self.TabWidget.addTab(C1Widget,QApplication.translate('Tab','ET/BT'))
        C2Widget = QWidget()
        C2Widget.setLayout(tab2Layout)
        self.TabWidget.addTab(C2Widget,QApplication.translate('Tab','Extra'))
        C3Widget = QWidget()
        C3Widget.setLayout(tab3Layout)
        self.TabWidget.addTab(C3Widget,QApplication.translate('Tab','Modbus'))
        C4Widget = QWidget()
        C4Widget.setLayout(tab4Layout)
        self.TabWidget.addTab(C4Widget,QApplication.translate('Tab','S7'))
        C5Widget = QWidget()
        C5Widget.setLayout(tab5Layout)
        self.TabWidget.addTab(C5Widget,QApplication.translate('Tab','Scale'))
        C6Widget = QWidget()
        C6Widget.setLayout(tab6Layout)
        self.TabWidget.addTab(C6Widget,QApplication.translate('Tab','Color'))
        C7Widget = QWidget()
        C7Widget.setLayout(tab7Layout)
        self.TabWidget.addTab(C7Widget,QApplication.translate('Tab','WebSocket'))
        self.TabWidget.currentChanged.connect(self.tabSwitched)

        if devid == 29 or (devid == 0 and self.aw.ser.useModbusPort) : # switch to MODBUS tab if MODBUS device was selected as main device
            # or if PID and "Use ModbusPort" was selected
            self.TabWidget.setCurrentIndex(2)
        elif devid == 79: # switch to S7 tab if S7 device was selected as main device
            self.TabWidget.setCurrentIndex(3)
        elif devid == 111:  # switch to WebSocket tab if WebSocket device was selected as main device
            self.TabWidget.setCurrentIndex(6)
        #incorporate layouts
        Mlayout = QVBoxLayout()
        Mlayout.addWidget(self.TabWidget)
        Mlayout.addLayout(buttonLayout)
        Mlayout.setContentsMargins(5,15,5,5)
        Mlayout.setSpacing(5)
        self.setLayout(Mlayout)
        if platform.system() != 'Windows':
            ok_button: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button is not None:
                ok_button.setFocus()
        else:
            self.TabWidget.setFocus()
        settings = QSettings()
        if settings.contains('PortsGeometry'):
            self.restoreGeometry(settings.value('PortsGeometry'))

    @pyqtSlot(int)
    def scaleDeviceIndexChanged(self, i:int) -> None:
        if self.supported_scales[i] in self.aw.scale.bluetooth_devices:
            permission_status:Optional[bool] = self.aw.app.getBluetoothPermission(request=True)
            if permission_status is False:
                message:str = QApplication.translate('Message','Bluetootooth access denied')
                QMessageBox.warning(None, #self, # only without super this one shows the native dialog on macOS under Qt 6.6.2 and later
                    message, message)


    @pyqtSlot(int)
    def s7_optimize_toggle(self, i:int) -> None:
        if i:
            self.s7_full_block.setEnabled(True)
        else:
            self.s7_full_block.setEnabled(False)

    @pyqtSlot(int)
    def modbus_optimize_toggle(self, i:int) -> None:
        if i:
            self.modbus_full_block.setEnabled(True)
        else:
            self.modbus_full_block.setEnabled(False)

    @pyqtSlot(int)
    def colorDeviceIndexChanged(self, i:int) -> None:
        try:
            if i==2: # Classic Tonino
                self.aw.color.baudrate = 115200
            elif i==1: # Tiny Tonino
                self.aw.color.baudrate = 57600
            self.color_baudrateComboBox.setCurrentIndex(self.color_bauds.index(str(self.aw.color.baudrate)))
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    @pyqtSlot(bool)
    def scanS7(self, _:bool = False) -> None:
        scan_S7_dlg = scanS7Dlg(self,self.aw)
        scan_S7_dlg.shost = str(self.s7_hostEdit.text())
        scan_S7_dlg.sport = toInt(str(self.s7_portEdit.text()))
        scan_S7_dlg.srack = toInt(str(self.s7_rackEdit.text()))
        scan_S7_dlg.sslot = toInt(str(self.s7_slotEdit.text()))
        scan_S7_dlg.show()

    @pyqtSlot(bool)
    def scanModbus(self, _:bool = False) -> None:
        scan_modbuds_dlg = scanModbusDlg(self,self.aw)
        scan_modbuds_dlg.port = str(self.modbus_comportEdit.getSelection())
        scan_modbuds_dlg.baudrate = toInt(str(self.modbus_baudrateComboBox.currentText()))
        scan_modbuds_dlg.bytesize = toInt(str(self.modbus_bytesizeComboBox.currentText()))
        scan_modbuds_dlg.stopbits = toInt(str(self.modbus_stopbitsComboBox.currentText()))
        scan_modbuds_dlg.parity = str(self.modbus_parityComboBox.currentText())
        scan_modbuds_dlg.timeout = float2float(toFloat(comma2dot(str(self.modbus_timeoutEdit.text()))))
        scan_modbuds_dlg.mtype = int(self.modbus_type.currentIndex())
        scan_modbuds_dlg.mhost = str(self.modbus_hostEdit.text())
        scan_modbuds_dlg.mport = toInt(str(self.modbus_portEdit.text()))
        scan_modbuds_dlg.show()

    @pyqtSlot(int)
    def portComboBoxIndexChanged(self, i:int) -> None:
        sender = cast(PortComboBox, self.sender())
        sender.setSelection(i)

    def createserialTable(self) -> None:
        try:
            self.serialtable.clear()
            nssdevices = min(len(self.aw.extracomport),len(self.aw.qmc.extradevices))
            if nssdevices:
                self.serialtable.setRowCount(nssdevices)
                self.serialtable.setColumnCount(7)
                self.serialtable.setHorizontalHeaderLabels([QApplication.translate('Table','Device'),
                                                            QApplication.translate('Table','Comm Port'),
                                                            QApplication.translate('Table','Baud Rate'),
                                                            QApplication.translate('Table','Byte Size'),
                                                            QApplication.translate('Table','Parity'),
                                                            QApplication.translate('Table','Stopbits'),
                                                            QApplication.translate('Table','Timeout')])
                self.serialtable.setAlternatingRowColors(True)
                self.serialtable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                self.serialtable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                self.serialtable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
                self.serialtable.setShowGrid(True)
                vheader: Optional[QHeaderView] = self.serialtable.verticalHeader()
                if vheader is not None:
                    vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
                for i in range(nssdevices):
                    if len(self.aw.qmc.extradevices) > i:
                        devid = self.aw.qmc.extradevices[i]
                        devicename = self.aw.qmc.devices[max(0,devid-1)]
                        if devicename[0] == '+':
                            devname = devicename[1:]
                        else:
                            devname = devicename
                        device = QTableWidgetItem(devname)    #type identification of the device. Non editable
                        self.serialtable.setItem(i,0,device)
                        if (devid not in self.aw.qmc.nonSerialDevices) and devid != 29 and devicename[0] != '+': # hide serial confs for MODBUS, Phidgets and "+X" extra devices
                            comportComboBox = PortComboBox(selection = self.aw.extracomport[i])
                            comportComboBox.activated.connect(self.portComboBoxIndexChanged)
                            comportComboBox.setMinimumContentsLength(15)
                            baudComboBox =  QComboBox()
                            baudComboBox.addItems(self.bauds)
                            if str(self.aw.extrabaudrate[i]) in self.bauds:
                                baudComboBox.setCurrentIndex(self.bauds.index(str(self.aw.extrabaudrate[i])))
                            byteComboBox =  QComboBox()
                            byteComboBox.addItems(self.bytesizes)
                            if str(self.aw.extrabytesize[i]) in self.bytesizes:
                                byteComboBox.setCurrentIndex(self.bytesizes.index(str(self.aw.extrabytesize[i])))
                            parityComboBox =  QComboBox()
                            parityComboBox.addItems(self.parity)
                            if self.aw.extraparity[i] in self.parity:
                                parityComboBox.setCurrentIndex(self.parity.index(self.aw.extraparity[i]))
                            stopbitsComboBox = QComboBox()
                            stopbitsComboBox.addItems(self.stopbits)
                            if str(self.aw.extrastopbits[i]) in self.stopbits:
                                stopbitsComboBox.setCurrentIndex(self.stopbits.index(str(self.aw.extrastopbits[i])))
                            timeoutEdit = QLineEdit(str(self.aw.extratimeout[i]))
                            timeoutEdit.setValidator(self.aw.createCLocaleDoubleValidator(0,5,1,timeoutEdit))
#                            timeoutEdit.setFixedWidth(65)
                            timeoutEdit.setMinimumWidth(65)
                            timeoutEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
                            #add widgets to the table
                            self.serialtable.setCellWidget(i,1,comportComboBox)
                            self.serialtable.setCellWidget(i,2,baudComboBox)
                            self.serialtable.setCellWidget(i,3,byteComboBox)
                            self.serialtable.setCellWidget(i,4,parityComboBox)
                            self.serialtable.setCellWidget(i,5,stopbitsComboBox)
                            self.serialtable.setCellWidget(i,6,timeoutEdit)
                self.serialtable.resizeColumnsToContents()
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' createserialTable(): {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    def saveserialtable(self) -> None:
        try:
            ser_ports = min(len(self.aw.extracomport),len(self.aw.qmc.extradevices))
            self.closeserialports()
            for i in range(ser_ports):
                if len(self.aw.qmc.extradevices) > i:
                    devid = self.aw.qmc.extradevices[i]
                    devicename = self.aw.qmc.devices[devid-1]    #type identification of the device. Non editable
                    if (devid not in self.aw.qmc.nonSerialDevices) and devid != 29 and devicename[0] != '+': # hide serial confs for MODBUS and "+XX" extra devices
                        comportComboBox = cast(PortComboBox, self.serialtable.cellWidget(i,1))
                        self.aw.extracomport[i] = str(comportComboBox.getSelection())
                        baudComboBox = cast(QComboBox, self.serialtable.cellWidget(i,2))
                        self.aw.extrabaudrate[i] = toInt(str(baudComboBox.currentText()))
                        byteComboBox = cast(QComboBox, self.serialtable.cellWidget(i,3))
                        self.aw.extrabytesize[i] = toInt(str(byteComboBox.currentText()))
                        parityComboBox = cast(QComboBox, self.serialtable.cellWidget(i,4))
                        self.aw.extraparity[i] = str(parityComboBox.currentText())
                        stopbitsComboBox = cast(QComboBox, self.serialtable.cellWidget(i,5))
                        self.aw.extrastopbits[i] = toInt(str(stopbitsComboBox.currentText()))
                        timeoutEdit = cast(QLineEdit, self.serialtable.cellWidget(i,6))
                        self.aw.extratimeout[i] = float(str(timeoutEdit.text()))
            #create serial ports for each extra device
            self.aw.extraser = []
            #load the settings for the extra serial ports found
            for i in range(ser_ports):
                xser = serialport(self.aw)
                if len(self.aw.extracomport)>i:
                    xser.comport = str(self.aw.extracomport[i])
                if len(self.aw.extrabaudrate)>i:
                    xser.baudrate = self.aw.extrabaudrate[i]
                if len(self.aw.extrabytesize)>i:
                    xser.bytesize = self.aw.extrabytesize[i]
                if len(self.aw.extraparity)>i:
                    xser.parity = str(self.aw.extraparity[i])
                if len(self.aw.extrastopbits)>i:
                    xser.stopbits = self.aw.extrastopbits[i]
                if len(self.aw.extratimeout)>i:
                    xser.timeout = self.aw.extratimeout[i]
                self.aw.extraser.append(xser)
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' saveserialtable(): {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot(bool)
    def showModbusbuttonhelp(self, _:bool = False) -> None:
        if self.TabWidget.currentIndex() == 2:
            from help import modbus_help # pyright: ignore [attr-defined] # pylint: disable=no-name-in-module
            self.helpdialog = self.aw.showHelpDialog(
                    self,            # this dialog as parent
                    self.helpdialog, # the existing help dialog
                    QApplication.translate('Form Caption','MODBUS Help'),
                    modbus_help.content())
        elif self.TabWidget.currentIndex() == 3:
            from help import s7_help # pyright: ignore [attr-defined] # pylint: disable=no-name-in-module
            self.helpdialog = self.aw.showHelpDialog(
                    self,            # this dialog as parent
                    self.helpdialog, # the existing help dialog
                    QApplication.translate('Form Caption','S7 Help'),
                    s7_help.content())

    def closeHelp(self) -> None:
        self.aw.closeHelpDialog(self.helpdialog)

    @pyqtSlot(int)
    def tabSwitched(self, _:int) -> None:
        self.closeHelp()

    @pyqtSlot('QCloseEvent')
    def closeEvent(self,_:Optional['QCloseEvent'] = None) -> None:
        self.closeHelp()
        settings = QSettings()
        #save window geometry
        settings.setValue('PortsGeometry',self.saveGeometry())

    @pyqtSlot()
    def accept(self) -> None:
        #validate serial parameter against input errors
        class comportError(Exception):
            pass
        class timeoutError(Exception):
            pass
        comport = str(self.comportEdit.getSelection())
        baudrate = str(self.baudrateComboBox.currentText())
        bytesize = str(self.bytesizeComboBox.currentText())
        parity = str(self.parityComboBox.currentText())
        stopbits = str(self.stopbitsComboBox.currentText())
        timeout = comma2dot(str(self.timeoutEdit.text()))
        #save extra serial ports by reading the serial extra table
        self.saveserialtable()
        if (self.aw.qmc.device not in self.aw.qmc.nonSerialDevices) and not(self.aw.qmc.device == 0 and self.aw.ser.useModbusPort): # only if serial conf is not hidden
            try:
                #check here comport errors
                if not comport:
                    raise comportError
                if not timeout:
                    raise timeoutError
                #add more checks here
                self.aw.sendmessage(QApplication.translate('Message','Serial Port Settings: {0}, {1}, {2}, {3}, {4}, {5}').format(comport,baudrate,bytesize,parity,stopbits,timeout))
            except comportError:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Serial Exception: invalid comm port'))
                self.comportEdit.setFocus()
                return
            except timeoutError:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Serial Exception: timeout'))
                self.timeoutEdit.selectAll()
                self.timeoutEdit.setFocus()
                return
        self.closeEvent(None)
        QDialog.accept(self)

    def closeserialports(self) -> None:
        self.aw.closeserialports()
