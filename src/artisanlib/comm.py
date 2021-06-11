#!/usr/bin/env python3

# ABOUT
# Artisan Device Communication

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

import os
import sys
import math
import re
import binascii
import time as libtime
import numpy
import shlex
import subprocess
import threading
import platform
import wquantiles

from artisanlib.util import cmd2str, RoRfromCtoF, appFrozen, fromCtoF, fromFtoC, hex2int, str2cmd, toFloat

from PyQt5.QtCore import Qt, QDateTime, QSemaphore, pyqtSlot
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (QApplication, QCheckBox, QDialog, QGridLayout, QHBoxLayout, QVBoxLayout,
                             QLabel, QLineEdit,QPushButton)
try: # hidden import to allow pyinstaller build on OS X to include the PyQt5.x private sip module
    from PyQt5 import sip # @UnusedImport
except:
    pass

from Phidget22.DeviceID import DeviceID
from Phidget22.Devices.TemperatureSensor import TemperatureSensor as PhidgetTemperatureSensor
from Phidget22.Devices.HumiditySensor import HumiditySensor as PhidgetHumiditySensor
from Phidget22.Devices.PressureSensor import PressureSensor as PhidgetPressureSensor
from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput  # @UnusedWildImport
from Phidget22.Devices.VoltageInput import VoltageInput # @UnusedWildImport
from Phidget22.Devices.DigitalInput import DigitalInput # @UnusedWildImport
from Phidget22.Devices.DigitalOutput import DigitalOutput # @UnusedWildImport 
from Phidget22.Devices.VoltageOutput import VoltageOutput, VoltageOutputRange # @UnusedWildImport
from Phidget22.Devices.RCServo import RCServo # @UnusedWildImport
from Phidget22.Devices.CurrentInput import CurrentInput # @UnusedWildImport
from Phidget22.Devices.FrequencyCounter import FrequencyCounter # @UnusedWildImport
from Phidget22.Devices.DCMotor import DCMotor # @UnusedWildImport

from yoctopuce.yocto_api import YAPI, YRefParam

# maps Artisan thermocouple types (order as listed in the menu; see phidget1048_types) to Phidget thermocouple types
# 1 => k-type (default)
# 2 => j-type
# 3 => e-type
# 4 => t-type
def PHIDGET_THERMOCOUPLE_TYPE(tp):
    from Phidget22.ThermocoupleType import ThermocoupleType
    if tp == 2:
        return ThermocoupleType.THERMOCOUPLE_TYPE_J
    elif tp == 3:
        return ThermocoupleType.THERMOCOUPLE_TYPE_E
    elif tp == 4:
        return ThermocoupleType.THERMOCOUPLE_TYPE_T
    else:
        return ThermocoupleType.THERMOCOUPLE_TYPE_K

# maps Artisan RTD wire setups (order as listed in the menu; see phidget1200_wireValues) to Phdiget wire setups
# 0 => 2-wire (default)
# 2 => 3-wire
# 3 => 4-wire
def PHIDGET_RTD_WIRE(tp):
    from Phidget22.RTDWireSetup import RTDWireSetup
    if tp == 1:
        return RTDWireSetup.RTD_WIRE_SETUP_3WIRE
    elif tp == 2:
        return RTDWireSetup.RTD_WIRE_SETUP_4WIRE
    else:
        return RTDWireSetup.RTD_WIRE_SETUP_2WIRE
     
# maps Artisan RTD types (order as listed in the menu; see phidget1200_formulaValues) to Phdiget RTD types
# 0 => PT100 3850 (default)
# 2 => PT100 3920
# 3 => PT1000 3850
# 4 => PT1000 3920        
def PHIDGET_RTD_TYPE(tp):
    from Phidget22.RTDType import RTDType
    if tp == 1:
        return RTDType.RTD_TYPE_PT100_3920
    elif tp == 2:
        return RTDType.RTD_TYPE_PT1000_3850
    elif tp == 3:
        return RTDType.RTD_TYPE_PT1000_3920
    else:
        return RTDType.RTD_TYPE_PT100_3850
    
# maps Artisan gain values (see phidget1046_gainValues) to Phidgets gain values
# defaults to no gain (BRIDGE_GAIN_1)
# not supported:
#   2x Amplification => BRIDGE_GAIN_2
#   4x Amplification => BRIDGE_GAIN_4
def PHIDGET_GAIN_VALUE(gv):
    from Phidget22.BridgeGain import BridgeGain as BG  # @UnusedImport
    if gv == 2:
        return BG.BRIDGE_GAIN_8 # 8x Amplification
    elif gv == 3:    
        return BG.BRIDGE_GAIN_16 # 16x Amplification
    elif gv == 4:    
        return BG.BRIDGE_GAIN_32 # 32x Amplification
    elif gv == 5:
        return BG.BRIDGE_GAIN_64 # 64x Amplification
    elif gv == 6:    
        return BG.BRIDGE_GAIN_128 # 128x Amplification
    else:
        return BG.BRIDGE_GAIN_1 # no gain

class YoctoThread(threading.Thread):
    def __init__(self):
        self._stopevent = threading.Event()
        threading.Thread.__init__(self)
    
    def run(self):
        errmsg = YRefParam()
        while not self._stopevent.isSet():
            YAPI.UpdateDeviceList(errmsg)  # traps plug/unplug events
            YAPI.Sleep(500, errmsg)  # traps others events

    def join(self, timeout=None):
        self._stopevent.set()
        threading.Thread.join(self, timeout)

#########################################################################
#############  NONE DEVICE DIALOG #######################################
#########################################################################

#inputs temperature
class nonedevDlg(QDialog):
    __slots__ = ['etEdit','btEdit','ETbox','okButton','cancelButton'] # save some memory by using slots
    def __init__(self, parent = None, aw = None):
        super(nonedevDlg,self).__init__(parent)
        self.aw = aw
        
        self.setWindowTitle(QApplication.translate("Form Caption","Manual Temperature Logger",None))
        if len(self.aw.qmc.timex):
            if self.aw.qmc.manuallogETflag:
                etval = str(int(aw.qmc.temp1[-1]))
            else:
                etval = "0"
            btval = str(int(aw.qmc.temp2[-1])) 
        else:
            etval = "0"
            btval = "0"
        self.etEdit = QLineEdit(etval)
        btlabel = QLabel(QApplication.translate("Label", "BT",None))
        self.btEdit = QLineEdit(btval)
        self.etEdit.setValidator(QIntValidator(0, 1000, self.etEdit))
        self.btEdit.setValidator(QIntValidator(0, 1000, self.btEdit))
        self.btEdit.setFocus()
        self.ETbox = QCheckBox(QApplication.translate("CheckBox","ET",None))
        if self.aw.qmc.manuallogETflag == True:
            self.ETbox.setChecked(True)
        else:
            self.ETbox.setChecked(False)
            self.etEdit.setVisible(False)
        self.ETbox.stateChanged.connect(self.changemanuallogETflag)
        self.okButton = QPushButton(QApplication.translate("Button","OK",None))
        self.cancelButton = QPushButton(QApplication.translate("Button","Cancel",None))
        self.cancelButton.setFocusPolicy(Qt.NoFocus)
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addWidget(self.okButton)
        grid = QGridLayout()
        grid.addWidget(self.ETbox,0,0)
        grid.addWidget(self.etEdit,0,1)
        grid.addWidget(btlabel,1,0)
        grid.addWidget(self.btEdit,1,1)
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(grid)
        mainLayout.addStretch()  
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)

    @pyqtSlot(int)
    def changemanuallogETflag(self,_):
        if self.ETbox.isChecked():
            self.aw.qmc.manuallogETflag = 1
            self.etEdit.setVisible(True)
            self.etEdit.setFocus()
        else:
            self.aw.qmc.manuallogETflag = 0
            self.etEdit.setVisible(False)
            self.btEdit.setFocus()


###########################################################################################
##################### SERIAL PORT #########################################################
###########################################################################################

class serialport(object):
    """ this class handles the communications with all the devices"""

    __slots__ = ['aw', 'platf', 'comport','baudrate','bytesize','parity','stopbits','timeout','SP','COMsemaphore','commavailable',\
        'PhidgetTemperatureSensor','Phidget1048values','Phidget1048lastvalues','Phidget1048semaphores',\
        'PhidgetIRSensor','PhidgetIRSensorIC','Phidget1045values','Phidget1045lastvalue','Phidget1045tempIRavg',\
        'Phidget1045semaphore','PhidgetBridgeSensor','Phidget1046values','Phidget1046lastvalues','Phidget1046semaphores',\
        'PhidgetIO','PhidgetIOvalues','PhidgetIOlastvalues','PhidgetIOsemaphores','PhidgetDigitalOut',\
        'PhidgetDigitalOutLastPWM','PhidgetDigitalOutLastToggle','PhidgetDigitalOutHub','PhidgetDigitalOutLastPWMhub',\
        'PhidgetDigitalOutLastToggleHub','PhidgetAnalogOut','PhidgetDCMotor','PhidgetRCServo','PhidgetBinaryOut',\
        'YOCTOlibImported','YOCTOsensor','YOCTOchan1','YOCTOchan2','YOCTOtempIRavg','YOCTOvalues','YOCTOlastvalues','YOCTOsemaphores',\
        'YOCTOthread','YOCTOvoltageOutputs','YOCTOcurrentOutputs','YOCTOrelays','YOCTOservos','YOCTOpwmOutputs','HH506RAid','MS6514PrevTemp1','MS6514PrevTemp2','DT301PrevTemp','EXTECH755PrevTemp',\
        'controlETpid','readBTpid','useModbusPort','showFujiLCDs','arduinoETChannel','arduinoBTChannel','arduinoATChannel',\
        'ArduinoIsInitialized','ArduinoFILT','HH806Winitflag','R1','devicefunctionlist','externalprogram',\
        'externaloutprogram','externaloutprogramFlag']

    def __init__(self, aw = None):
    
        self.aw = aw
        
        self.platf = platform.system()
        
        #default initial settings. They are changed by settingsload() at initiation of program acording to the device chosen
        self.comport = "COM4"      #NOTE: this string should not be translated. It is an argument for lib Pyserial
        self.baudrate = 9600
        self.bytesize = 8
        self.parity= 'O'
        self.stopbits = 1
        self.timeout=0.4
        #serial port for ET/BT
        import serial  # @UnusedImport
        self.SP = serial.Serial()
        #used only in devices that also control the roaster like PIDs or arduino (possible to recieve asynchrous comands from GUI commands and thread sample()). 
        self.COMsemaphore = QSemaphore(1) 
        #list of comm ports available after Scan
        self.commavailable = []
        ##### SPECIAL METER FLAGS ########
        #stores the Phidget 1048 TemperatureSensor object (None if not initialized)
        self.PhidgetTemperatureSensor = None # either None or a list containing one PhidgetTemperatureSensor() object per channel
        self.Phidget1048values = [[],[],[],[]] # the values for each of the 4 channels gathered by registered change triggers in the last period
        self.Phidget1048lastvalues = [-1]*4 # the last async values returned
        self.Phidget1048semaphores = [QSemaphore(1),QSemaphore(1),QSemaphore(1),QSemaphore(1)] # semaphores protecting the access to self.Phidget1048values per channel
        # list of (serial,port) tuples filled on attaching the corresponding main device and consumed on attaching the other channel pairs
        #stores the Phidget 1045 TemperatureSensor object (None if not initialized)
        self.PhidgetIRSensor = None
        self.PhidgetIRSensorIC = None
        self.Phidget1045values = [] # async values of the one channel
        self.Phidget1045lastvalue = -1
        self.Phidget1045tempIRavg = None
        self.Phidget1045semaphore = QSemaphore(1) # semaphore protecting the access to self.Phidget1045values per channel
        #stores the Phidget BridgeSensor object (None if not initialized)
        self.PhidgetBridgeSensor = None
        self.Phidget1046values = [[],[],[],[]] # the values for each of the 4 channels gathered by registered change triggers in the last period
        self.Phidget1046lastvalues = [-1]*4 # the last async values returned
        self.Phidget1046semaphores = [QSemaphore(1),QSemaphore(1),QSemaphore(1),QSemaphore(1)] # semaphores protecting the access to self.Phidget1046values per channel
        #stores the Phidget IO object (None if not initialized)
        self.PhidgetIO = None
        self.PhidgetIOvalues = [[],[],[],[],[],[],[],[]] # the values gathered by registered change triggers
        self.PhidgetIOlastvalues = [-1]*8 # the values gathered by registered change triggers
        self.PhidgetIOsemaphores = [QSemaphore(1),QSemaphore(1),QSemaphore(1),QSemaphore(1)] # semaphores protecting the access to self.Phidget1048values per channel
        #stores the Phidget Digital Output PMW objects (None if not initialized)
        self.PhidgetDigitalOut = {} # a dict associating out serials with lists of channels
        self.PhidgetDigitalOutLastPWM = {} # a dict assocating out serials with the list of last PWMs per channel
        self.PhidgetDigitalOutLastToggle = {} # a dict associating out serials with the list of last toggles per channel; if not None, channel was last toggled OFF and the value indicates that lastPWM on switching OFF
        self.PhidgetDigitalOutHub = {} # a dict associating hub serials with lists of channels
        self.PhidgetDigitalOutLastPWMhub = {} # a dict assocating hub serials with the list of last PWMs per port of the hub
        self.PhidgetDigitalOutLastToggleHub = {} # a dict associating hub serials with the list of last toggles per port of the hub; if not None, channel was last toggled OFF and the value indicates that lastPWM on switching OFF
        #store the Phidget Analog Output objects
        self.PhidgetAnalogOut = {} # a dict associating serials with lists of channels
        #store the servo objects
        self.PhidgetRCServo = {} # a dict associating serials with lists of channels
        #store the Phidget IO Binary Output objects
        self.PhidgetBinaryOut = {} # a dict associating binary out serials with lists of channels
        #store the Phidget DCMotor objects
        self.PhidgetDCMotor = {} # a dict associating serials with lists of channels
        #Yoctopuce channels
        self.YOCTOlibImported = False # ensure that the YOCTOlib is only imported once
        self.YOCTOsensor = None
        self.YOCTOchan1 = None
        self.YOCTOchan2 = None
        self.YOCTOtempIRavg = None # averages IR module temperature channel to eliminate noise

        self.YOCTOvalues = [[],[]] # the values for each of the 2 channels gathered by registered change triggers in the last period
        self.YOCTOlastvalues = [-1]*2 # the last async values returned
        self.YOCTOsemaphores = [QSemaphore(1),QSemaphore(1)] # semaphores protecting the access to YOCTO per channel
        self.YOCTOthread = None
        
        self.YOCTOvoltageOutputs = []
        self.YOCTOcurrentOutputs = []
        self.YOCTOrelays = []
        self.YOCTOservos = []
        self.YOCTOpwmOutputs = []

        #stores the _id of the meter HH506RA as a string
        self.HH506RAid = "X"
        #MS6514 variables
        self.MS6514PrevTemp1 = -1
        self.MS6514PrevTemp2 = -1
        #DT301 variable
        self.DT301PrevTemp = -1
        #EXPTECH755 variable
        self.EXTECH755PrevTemp = -1
        #select PID type that controls the roaster.
        # Reads/Controls ET
        self.controlETpid = [0,1]        # index0: type of pid: 0 = FujiPXG, 1 = FujiPXR3, 2 = DTA, 3 = not used, 4 = PXF
#                                        # index1: RS485 unitID: Can be changed in device menu.
        # Reads BT
        self.readBTpid = [1,2]           # index 0: type: FujiPXG, 1 = FujiPXR3, 2 = None, 3 = DTA, 4 = PXF
#                                        # index 1: RS485 unitID. Can be changed in device menu. 
        # Reuse Modbus-meter port
        self.useModbusPort = False
        self.showFujiLCDs = True
        #Initialization for ARDUINO and TC4 meter
        self.arduinoETChannel = "1"
        self.arduinoBTChannel = "2"
        self.arduinoATChannel = "None" # the channel the Ambient Temperature of the Arduino TC4 is reported as (this value will overwrite the corresponding real channel)
        self.ArduinoIsInitialized = 0
        self.ArduinoFILT = [70,70,70,70] # Arduino Filter settings per channel in %
        self.HH806Winitflag = 0
        self.R1 = None
        #list of functions calls to read temperature for devices.
        # device 0 (with index 0 bellow) is Fuji Pid
        # device 1 (with index 1 bellow) is Omega HH806
        # device 2 (with index 2 bellow) is omega HH506
        # etc
        # ADD DEVICE: to add a device you have to modify several places. Search for the tag "ADD DEVICE:"in the code
        # - add to self.devicefunctionlist
        self.devicefunctionlist = [self.fujitemperature,    #0
                                   self.HH806AU,            #1
                                   self.HH506RA,            #2
                                   self.CENTER309,          #3
                                   self.CENTER306,          #4
                                   self.CENTER305,          #5
                                   self.CENTER304,          #6
                                   self.CENTER303,          #7
                                   self.CENTER302,          #8
                                   self.CENTER301,          #9
                                   self.CENTER300,          #10
                                   self.VOLTCRAFTK204,      #11
                                   self.VOLTCRAFTK202,      #12
                                   self.VOLTCRAFT300K,      #13
                                   self.VOLTCRAFT302KJ,     #14
                                   self.EXTECH421509,       #15
                                   self.HH802U,             #16
                                   self.HH309,              #17
                                   self.NONE,               #18
                                   self.ARDUINOTC4,         #19
                                   self.TEVA18B,            #20
                                   self.CENTER309_34,       #21
                                   self.piddutycycle,       #22
                                   self.HHM28,              #23
                                   self.K204_34,            #24
                                   self.virtual,            #25
                                   self.DTAtemperature,     #26
                                   self.callprogram,        #27
                                   self.ARDUINOTC4_34,      #28
                                   self.MODBUS,             #29
                                   self.VOLTCRAFTK201,      #30
                                   self.AmprobeTMD56,       #31
                                   self.ARDUINOTC4_56,      #32
                                   self.MODBUS_34,          #33
                                   self.PHIDGET1048,        #34
                                   self.PHIDGET1048_34,     #35
                                   self.PHIDGET1048_AT,     #36
                                   self.PHIDGET1046,        #37
                                   self.PHIDGET1046_34,     #38
                                   self.MastechMS6514,      #39
                                   self.PHIDGET1018,        #40
                                   self.PHIDGET1018_34,     #41
                                   self.PHIDGET1018_56,     #42
                                   self.PHIDGET1018_78,     #43
                                   self.ARDUINOTC4_78,      #44
                                   self.YOCTO_thermo,       #45
                                   self.YOCTO_pt100,        #46
                                   self.PHIDGET1045,        #47
                                   self.callprogram_34,     #48
                                   self.callprogram_56,     #49
                                   self.DUMMY,              #50
                                   self.CENTER304_34,       #51
                                   self.PHIDGET1051,        #52
                                   self.HOTTOP_BTET,        #53
                                   self.HOTTOP_HF,          #54
                                   self.MODBUS_56,          #55
                                   self.DT301,              #56
                                   self.EXTECH755,          #57
                                   self.PHIDGET_TMP1101,    #58
                                   self.PHIDGET_TMP1101_34, #59
                                   self.PHIDGET_TMP1101_AT, #60
                                   self.PHIDGET_TMP1100,    #61
                                   self.PHIDGET1011,        #62
                                   self.PHIDGET_HUB0000,    #63
                                   self.PHIDGET_HUB0000_34, #64
                                   self.PHIDGET_HUB0000_56, #65
                                   self.HH806W,             #66
                                   self.VOLTCRAFTPL125T2,   #67
                                   self.PHIDGET_TMP1200,    #68
                                   self.PHIDGET1018_D,        #69
                                   self.PHIDGET1018_D_34,     #70
                                   self.PHIDGET1018_D_56,     #71
                                   self.PHIDGET1018_D_78,     #72
                                   self.PHIDGET1011_D,        #73
                                   self.PHIDGET_HUB0000_D,    #74
                                   self.PHIDGET_HUB0000_D_34, #75
                                   self.PHIDGET_HUB0000_D_56, #76
                                   self.VOLTCRAFTPL125T4,     #77
                                   self.VOLTCRAFTPL125T4_34,  #78
                                   self.S7,                   #79
                                   self.S7_34,                #80
                                   self.S7_56,                #81
                                   self.S7_78,                #82
                                   self.R1_DTBT,              #83
                                   self.R1_HF,                #84
                                   self.R1_DRUM_BTROR,        #85
                                   self.R1_EXIT_TEMP_VOLT,    #86
                                   self.R1_RPM_STATE,         #87
                                   self.callprogram_78,       #88
                                   self.callprogram_910,      #89
                                   self.slider_01,            #90
                                   self.slider_23,            #91
                                   self.probat_middleware,    #92
                                   self.probat_middleware_burner_drum,  #93
                                   self.probat_middleware_fan_pressure, #94
                                   self.PHIDGET_DAQ1400_CURRENT,   #95
                                   self.PHIDGET_DAQ1400_FREQUENCY, #96 
                                   self.PHIDGET_DAQ1400_DIGITAL,   #97 
                                   self.PHIDGET_DAQ1400_VOLTAGE,   #98
                                   self.R1_BTIBTS,            # 99
                                   self.YOCTO_IR,             #100
                                   self.BEHMOR_BTET,          #101
                                   self.BEHMOR_34,            #102
                                   self.VICTOR86B,            #103
                                   self.BEHMOR_56,            #104
                                   self.BEHMOR_78,            #105
                                   self.PHIDGET_HUB0000_0,    #106
                                   self.PHIDGET_HUB0000_D_0,  #107
                                   self.YOCTO_generic,        #108 # Yocto-4-20mA-Rx
                                   self.MODBUS_78,            #109
                                   self.S7_910,               #110
                                   self.WS,     # self.probat_sample,        #111
                                   self.WS_34,  # self.probat_sample_heater_air,    #112
                                   self.WS_56,  # self.probat_sample_drum_pressure, #113
                                   self.PHIDGET_TMP1200_2,    #114
                                   self.HB_BTET,              #115
                                   self.HB_DTIT,              #116
                                   self.HB_AT,                #117
                                   self.WS_78,  # self.probat_sample_inlet_ambient, # 118
                                   self.WS_910,  # self.probat_sample_cooling # 119
                                   self.YOCTO_generic,        #120 # Yocto-0-10V-Rx
                                   self.YOCTO_generic,        #120 # Yocto-milliVolt-Rx
                                   self.YOCTO_generic        #120 # Yocto-Serial
                                   ]
        #string with the name of the program for device #27
        self.externalprogram = "test.py"
        self.externaloutprogram = "out.py" # this program is called with arguments <ET>,<BT>,<ETB>,<BTB> values on each sampling
        self.externaloutprogramFlag = False # if true the externaloutprogram will be called on each sample()

#####################  FUNCTIONS  ############################
    ######### functions used by Fuji PIDs
    def sendFUJIcommand(self,binstring,nbytes):
        try:
            ###  lock resources ##
            self.COMsemaphore.acquire(1)
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                self.SP.write(binstring)
                r = self.SP.read(nbytes)
                #serTX.close()
                libtime.sleep(0.035)                     #this garantees a minimum of 35 miliseconds between readings (for all Fujis)
                lenstring = len(r)
                if lenstring:
                    # CHECK FOR RECEIVED ERROR CODES
                    if r[1] == 128:
                        if r[2] == 1:
                            errorcode = QApplication.translate("Error Message","F80h Error",None) + " 1: A nonexistent function code was specified. Please check the function code."
                            errorcode += (QApplication.translate("Error Message","Exception:",None) + " SendFUJIcommand() 1: Illegal Function in unit {0}").format(ord(binstring[0]))
                            self.aw.qmc.adderror(errorcode)
                        if r[2] == 2:
                            errorcode = QApplication.translate("Error Message","F80h Error",None) + " 2: Faulty address for coil or resistor: The specified relative address for the coil number or resistor\n number cannot be used by the specified function code."
                            errorcode += (QApplication.translate("Error Message","Exception:",None) + " SendFUJIcommand() 2 Illegal Address for unit {0}").format(ord(binstring[0]))
                            self.aw.qmc.adderror(errorcode)
                        if r[2] == 3:
                            errorcode = QApplication.translate("Error Message","F80h Error",None) + " 3: Faulty coil or resistor number: The specified number is too large and specifies a range that does not contain\n coil numbers or resistor numbers."
                            errorcode += (QApplication.translate("Error Message","Exception:",None) + " SendFUJIcommand() 3 Illegal Data Value for unit {0}").format(ord(binstring[0]))
                            self.aw.qmc.adderror(errorcode)
                    else:
                        #Check crc16
                        crcRx =  hex2int(r[-1],r[-2])
                        crcCal1 = self.aw.fujipid.fujiCrc16(r[:-2])
                        if crcCal1 == crcRx:
                            return r           #OK. Return r after it has been checked for errors
                        else:
                            self.aw.qmc.adderror(QApplication.translate("Error Message","CRC16 data corruption ERROR. TX does not match RX. Check wiring",None))
                            return "0"
                else:
                    self.aw.qmc.adderror(QApplication.translate("Error Message","No RX data received",None))
                    return "0"
            else:
                return "0"
        except Exception:
            timez = str(QDateTime.currentDateTime().toString("hh:mm:ss.zzz"))    #zzz = miliseconds
            error = QApplication.translate("Error Message","Serial Exception:",None) + " ser.sendFUJIcommand()"
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror(timez + " " + error,exc_tb.tb_lineno)
            return "0"
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)                
                self.aw.addserial("Fuji: " + settings + " || Tx = " + cmd2str(binascii.hexlify(binstring)) + " || Rx = " + cmd2str(binascii.hexlify(r)))

    #finds time, ET and BT when using Fuji PID. Updates sv (set value) LCD. Finds power duty cycle
    def fujitemperature(self):
        #update ET SV LCD 6
        self.aw.qmc.currentpidsv = self.aw.fujipid.readcurrentsv()
        #get time of temperature reading in seconds from start; .elapsed() returns miliseconds
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        # get the temperature for ET. self.aw.fujipid.gettemperature(unitID)
        t1 = self.aw.fujipid.gettemperature(self.controlETpid[0],self.controlETpid[1])/10.  #Need to divide by 10 because using 1 decimal point in Fuji (ie. received 843 = 84.3)
        #if Fuji for BT is not None (0= PXG, 1 = PXR, 2 = None 3 = DTA)
        if self.readBTpid[0] < 2 or self.readBTpid[0] == 4:                    
            t2 = self.aw.fujipid.gettemperature(self.readBTpid[0],self.readBTpid[1])/10.
        elif self.readBTpid[0] == 3:
            ### arguments to create command to READ TEMPERATURE
            unitID = self.readBTpid[1]
            function = 3
            address = self.aw.dtapid.dtamem["pv"][1]  #index 1; ascii string
            ndata = 1
            ### create command
            command = self.aw.dtapid.message2send(unitID,function,address,ndata)
            t2 = self.sendDTAcommand(command)
        else:
            t2 = -1
        #get current duty cycle and update LCD 7
        try:
            dc = self.aw.fujipid.readdutycycle()
            if dc != -1: # on wrong reading we just keep the previous one
                self.aw.qmc.dutycycle = max(0,min(100,dc))
            self.aw.qmc.dutycycleTX = self.aw.qmc.timeclock.elapsed()/1000.
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","",None) + " fujitemperature() {0}").format(str(ex)),exc_tb.tb_lineno)
        return tx,t1,t2

    #especial function that collects extra duty cycle % and SV
    def piddutycycle(self):
        if self.aw.qmc.device == 0: # FUJI
            #return saved readings from device 0
            return self.aw.qmc.dutycycleTX, self.aw.qmc.dutycycle, self.aw.qmc.currentpidsv
        elif not self.aw.pidcontrol.pidActive:
            return self.aw.qmc.timeclock.elapsed()/1000.,-1,-1
        elif (self.aw.qmc.device == 19 and not self.aw.pidcontrol.externalPIDControl()) or \
                (self.aw.qmc.device == 53) or \
                (self.aw.qmc.device == 29 and not self.aw.pidcontrol.externalPIDControl()):
                # TC4, HOTTOP or MODBUS with Artisan Software PID
            return self.aw.qmc.timeclock.elapsed()/1000., min(100,max(-100,self.aw.qmc.pid.getDuty())), self.aw.qmc.pid.target
        else:
            if self.aw.pidcontrol.sv is not None:
                sv = self.aw.pidcontrol.sv
            else:
                sv = -1
            if self.aw.qmc.device == 29: # external MODBUS PID
                duty = -1
            else:
                duty = min(100,max(-100,self.aw.qmc.pid.getDuty()))
            return self.aw.qmc.timeclock.elapsed()/1000.,duty,sv
            

    def DTAtemperature(self):
        ###########################################################
        ### create command
        command = self.aw.dtapid.message2send(self.controlETpid[1],3,self.aw.dtapid.dtamem["sv"][1],1)
        #read sv
        self.aw.qmc.currentpidsv = self.sendDTAcommand(command)
        #update SV value 
        self.aw.dtapid.dtamem["sv"][0] = self.aw.qmc.currentpidsv    #index 0
        #sv LCD is updated in qmc.updadegraphics()
        #give some time to rest
        libtime.sleep(.1)
        ##############################################################
        ### create command
        command = self.aw.dtapid.message2send(self.controlETpid[1],3,self.aw.dtapid.dtamem["pv"][1],1)
        #read
        t1 = self.sendDTAcommand(command)
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        #if Fuji for BT is not None (0= PXG, 1 = PXR, 2 = None 3 = DTA)
        if self.readBTpid[0] < 2:                    
            t2 = self.aw.fujipid.gettemperature(self.readBTpid[0],self.readBTpid[1])/10.
        elif self.readBTpid[0] == 3:
            ### create command
            command = self.aw.dtapid.message2send(self.readBTpid[1],3,self.aw.dtapid.dtamem["pv"][1],1)
            t2 = self.sendDTAcommand(command)
        else:
            t2 = self.aw.qmc.currentpidsv  #return 
        ################################################################
        if t1 is None:
            t1 = -1
        if t2 is None:
            t2 = -1
        return tx,t1,t2

    def sendDTAcommand(self,command):
        try:
            ###  lock resources ##
            self.COMsemaphore.acquire(1)
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                nrxbytes = 15
                #clear
                self.SP.reset_input_buffer()
                self.SP.reset_input_buffer()
                #SEND (tx)
                self.SP.write(str2cmd(command))
                #READ n bytes(rx)
                r = self.SP.read(nrxbytes).decode('utf-8')
##                command = ":010347000001B4"
##                r =       ":01030401900067"
                if len(r) == nrxbytes:
                    #READ and WRITE commands are different
                    #READ command
                    if command[4] == "3":
                        #CRCreceived = int(r[13:15],16)  #bytes 14&15
                        #CRCcalculated = self.aw.dtapid.DTACalcChecksum(r[1:11]) #bytes 1-10
                        #if CRCreceived == CRCcalculated:
                        t1 = float(int(r[7:11], 16))*0.1    #convert ascii string from bytes 8-11 (4 bytes) to a float
                        return t1
##                        else:
##                            self.aw.qmc.adderror(QApplication.translate("Error Message","DTAtemperature(): Data corruption. Check wiring",None))            
##                            if len(self.aw.qmc.timex) > 2:
##                                return self.aw.qmc.temp1[-1]
##                            else:
##                                return 0.
                    #WRITE COMMAND. Under Test
##                    if command[4] == "4":
##                        #received  data is equal to sent command
##                        if r == command:
##                            self.aw.sendmessage("Write operation OK")
##                            return 1
##                        else:
##                            self.aw.sendmessage("Write operation BAD")
##                            return 0
                else:
                    nbytes = len(r)
                    self.aw.qmc.adderror(QApplication.translate("Error Message","DTAcommand(): {0} bytes received but 15 needed",None).format(nbytes))
                    if len(self.aw.qmc.timex) > 2:
                        return self.aw.qmc.temp1[-1]
                    else:
                        return -1.
        except Exception:
            error = QApplication.translate("Error Message","Serial Exception:",None) + " ser.sendDTAcommand()"
            timez = str(QDateTime.currentDateTime().toString("hh:mm:ss.zzz"))    #zzz = miliseconds
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror(timez + " " + error,exc_tb.tb_lineno)
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("Delta DTA: " + settings + " || Tx = " + cmd2str(command) + " || Rx = " + str(r))



    def callprogram(self):
        try:
#            output = os.popen(self.aw.ser.externalprogram,"r").readline()
            # we try to set the users standard environment, replacing the one pointing to the restrictive python build in Artisan
            my_env = self.aw.calc_env()
        
            # hide the console window on Windows 
            startupinfo = None  
            if self.platf == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            if self.platf == 'Windows':
                cmd_str = os.path.expanduser(self.aw.ser.externalprogram)
                p = subprocess.Popen(cmd_str,env=my_env,stdout=subprocess.PIPE,startupinfo=startupinfo,shell=True)
            else:
                p = subprocess.Popen([os.path.expanduser(c) for c in shlex.split(self.aw.ser.externalprogram)],env=my_env,stdout=subprocess.PIPE,startupinfo=startupinfo)
            output = p.communicate()[0].decode('UTF-8')
            
            tx = self.aw.qmc.timeclock.elapsed()/1000.
            if "," in output:
                parts = output.split(",")
                if len(parts) > 2:
                    self.aw.qmc.program_t3 = float(parts[2].strip())
                    if len(parts) > 3:
                        self.aw.qmc.program_t4 = float(parts[3].strip())
                        if len(parts) > 4:
                            self.aw.qmc.program_t5 = float(parts[4].strip())
                            if len(parts) > 5:
                                self.aw.qmc.program_t6 = float(parts[5].strip())
                                if len(parts) > 6:
                                    self.aw.qmc.program_t7 = float(parts[6].strip())
                                    if len(parts) > 7:
                                        self.aw.qmc.program_t8 = float(parts[7].strip())
                                        if len(parts) > 8:
                                            self.aw.qmc.program_t9 = float(parts[8].strip())
                                            if len(parts) > 9:
                                                self.aw.qmc.program_t10 = float(parts[9].strip())
                return tx,float(parts[0].strip()),float(parts[1].strip())
            else:
                return tx,0.,float(output)
        except Exception as e:
            tx = self.aw.qmc.timeclock.elapsed()/1000.
            _, _, exc_tb = sys.exc_info() 
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:",None) + " callprogram(): {0} ").format(str(e)),exc_tb.tb_lineno)
            self.aw.qmc.adderror((QApplication.translate("Error Message", "callprogram() received:",None) + " {0} ").format(str(output)),exc_tb.tb_lineno)
            return tx,0.,0.
            
    def callprogram_34(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t1 = self.aw.qmc.program_t3
        t2 = self.aw.qmc.program_t4
        return tx,t2,t1

    def callprogram_56(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t1 = self.aw.qmc.program_t5
        t2 = self.aw.qmc.program_t6
        return tx,t2,t1

    def callprogram_78(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t1 = self.aw.qmc.program_t7
        t2 = self.aw.qmc.program_t8
        return tx,t2,t1

    def callprogram_910(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t1 = self.aw.qmc.program_t9
        t2 = self.aw.qmc.program_t10
        return tx,t2,t1

    def slider_01(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t1 = self.aw.slider1.value()
        t2 = self.aw.slider2.value()
        return tx,t2,t1

    def slider_23(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t1 = self.aw.slider3.value()
        t2 = self.aw.slider4.value()
        return tx,t2,t1

    def virtual(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        return tx,1.,1.

    def HH506RA(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.HH506RAtemperature()
        return tx,t2,t1

    def HH806AU(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.HH806AUtemperature()
        return tx,t2,t1

    def AmprobeTMD56(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.HH806AUtemperature()
        return tx,t2,t1 

    def MastechMS6514(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.MS6514temperature()
        return tx,t2,t1 

    def DT301(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.DT301temperature()
        return tx,t2,t1 

    def HH806W(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.HH806Wtemperature()
        return tx,t2,t1
    
    def DUMMY(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        return tx,0,0
        
    def PHIDGET1045(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t,a = self.PHIDGET1045temperature(DeviceID.PHIDID_1045)
        return tx,a,t

    def PHIDGET1048(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.PHIDGET1048temperature(DeviceID.PHIDID_1048,0)
        return tx,t1,t2 # time, ET (chan2), BT (chan1)

    def PHIDGET1048_34(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.PHIDGET1048temperature(DeviceID.PHIDID_1048,1)
        return tx,t1,t2

    def PHIDGET1048_AT(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.PHIDGET1048temperature(DeviceID.PHIDID_1048,2)
        return tx,t1,t2

    def PHIDGET1046(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.PHIDGET1046temperature(0)
        return tx,t1,t2

    def PHIDGET1046_34(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.PHIDGET1046temperature(1)
        return tx,t1,t2
        
    def PHIDGET1051(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t,a = self.PHIDGET1045temperature(DeviceID.PHIDID_1051)
        return tx,a,t
        
    def PHIDGET1011(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_1011,0,"voltage")
        return tx,v1,v2
                
    def PHIDGET1018(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_1010_1013_1018_1019,0,"voltage")
        return tx,v1,v2

    def PHIDGET1018_34(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_1010_1013_1018_1019,1,"voltage")
        return tx,v1,v2

    def PHIDGET1018_56(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_1010_1013_1018_1019,2,"voltage")
        return tx,v1,v2

    def PHIDGET1018_78(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_1010_1013_1018_1019,3,"voltage")
        return tx,v1,v2
        
    def PHIDGET1011_D(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_1011,0,"digital")
        return tx,v1,v2
        
    def PHIDGET1018_D(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_1010_1013_1018_1019,0,"digital")
        return tx,v1,v2

    def PHIDGET1018_D_34(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_1010_1013_1018_1019,1,"digital")
        return tx,v1,v2

    def PHIDGET1018_D_56(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_1010_1013_1018_1019,2,"digital")
        return tx,v1,v2

    def PHIDGET1018_D_78(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_1010_1013_1018_1019,3,"digital")
        return tx,v1,v2
        
    def PHIDGET_HUB0000_D(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_HUB0000,0,"digital")
        return tx,v1,v2

    def PHIDGET_HUB0000_D_34(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_HUB0000,1,"digital")
        return tx,v1,v2

    def PHIDGET_HUB0000_D_56(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_HUB0000,2,"digital")
        return tx,v1,v2   
        
    def PHIDGET_HUB0000_D_0(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_HUB0000,0,API="digital",retry=False,single=True)
        return tx,v1,v2     

    def PHIDGET_TMP1101(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.PHIDGET1048temperature(DeviceID.PHIDID_TMP1101,0)
        return tx,t1,t2 # time, ET (chan2), BT (chan1)
        
    def PHIDGET_TMP1101_34(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.PHIDGET1048temperature(DeviceID.PHIDID_TMP1101,1)
        return tx,t1,t2
            
    def PHIDGET_TMP1101_AT(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.PHIDGET1048temperature(DeviceID.PHIDID_TMP1101,2)
        return tx,t1,t2

    def PHIDGET_TMP1100(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t,a = self.PHIDGET1045temperature(DeviceID.PHIDID_TMP1100)
        return tx,a,t

    def PHIDGET_TMP1200(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t,a = self.PHIDGET1045temperature(DeviceID.PHIDID_TMP1200)
        return tx,a,t

    def PHIDGET_TMP1200_2(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t,a = self.PHIDGET1045temperature(DeviceID.PHIDID_TMP1200,alternative_conf=True)
        return tx,a,t
        
    def PHIDGET_HUB0000(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1  = self.PHIDGET1018values(DeviceID.PHIDID_HUB0000,0,"voltage")
        return tx,v1,v2

    def PHIDGET_HUB0000_34(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_HUB0000,1,"voltage")
        return tx,v1,v2

    def PHIDGET_HUB0000_56(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_HUB0000,2,"voltage")
        return tx,v1,v2
        
    def PHIDGET_HUB0000_0(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1  = self.PHIDGET1018values(DeviceID.PHIDID_HUB0000,0,API="voltage",retry=False,single=True)
        return tx,v1,v2

    def PHIDGET_DAQ1400_CURRENT(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_DAQ1400,0,"current")
        return tx,v1,v2

    def PHIDGET_DAQ1400_FREQUENCY(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_DAQ1400,0,"frequency")
        return tx,v1,v2

    def PHIDGET_DAQ1400_DIGITAL(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_DAQ1400,0,"digital")
        return tx,v1,v2

    def PHIDGET_DAQ1400_VOLTAGE(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.PHIDGET1018values(DeviceID.PHIDID_DAQ1400,0,"voltage")
        return tx,v1,v2

    def HOTTOP_BTET(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.HOTTOPtemperatures()
        self.aw.qmc.hottop_TX = tx
        return tx,t1,t2 # time, ET (chan2), BT (chan1)
        
    def HOTTOP_HF(self):
        return self.aw.qmc.hottop_TX,self.aw.qmc.hottop_MAIN_FAN,self.aw.qmc.hottop_HEATER # time, Fan (chan2), Heater (chan1)
        
    def BEHMOR_BTET(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.BEHMORtemperatures(8,9)
        return tx,t1,t2 # time, ET (chan2), BT (chan1)
    
    def BEHMOR_34(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.BEHMORtemperatures(10,11)
        return tx,t1,t2 # time, chan2, chan1

    def BEHMOR_56(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.BEHMORtemperatures(1,2)
        return tx,t1,t2 # time, chan2, chan1

    def BEHMOR_78(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.BEHMORtemperatures(3,4)
        return tx,t1,t2 # time, chan2, chan1
    
    def VICTOR86B(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t,_= self.HHM28multimeter()  #NOTE: val and symbols are type strings
        if "L" in t:  #L = Out of Range
            return tx, -1, -1
        else:
            return tx,-1,float(t)

    # if force the optimizer is deactivated to ensure fetching fresh readings
    def S7(self,force=False):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.S7read(0,force)
        return tx,t2,t1
    
    def S7_34(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.S7read(1)
        return tx,t2,t1
        
    def S7_56(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.S7read(2)
        return tx,t2,t1

    def S7_78(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.S7read(3)
        return tx,t2,t1

    def S7_910(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.S7read(4)
        return tx,t2,t1

    def R1_DTBT(self):
        if self.R1 is None:
            from artisanlib.aillio import AillioR1
            self.R1 = AillioR1()
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        try:
            if self.aw.qmc.batchcounter != -1:
                self.aw.qmc.batchcounter = self.R1.get_roast_number()
            self.aw.qmc.R1_BT = self.R1.get_bt()
            self.aw.qmc.R1_DT = self.R1.get_dt()
            self.aw.qmc.R1_DRUM = self.R1.get_drum() * 10
            self.aw.qmc.R1_VOLTAGE = self.R1.get_voltage()
            self.aw.qmc.R1_HEATER = self.R1.get_heater() * 10
            self.aw.qmc.R1_FAN = self.R1.get_fan() * 10
            self.aw.qmc.R1_BT_ROR = self.R1.get_bt_ror()
            self.aw.qmc.R1_EXIT_TEMP = self.R1.get_exit_temperature()
            self.aw.qmc.R1_STATE = self.R1.get_state()
            self.aw.qmc.R1_FAN_RPM = self.R1.get_fan_rpm()
            self.aw.qmc.R1_TX = tx
            newstate = self.R1.get_state_string()
            if newstate != self.aw.qmc.R1_STATE_STR:
                self.aw.qmc.R1_STATE_STR = newstate
                self.aw.sendmessage(QApplication.translate("Message", "R1 state: " + newstate, None))
            if self.aw.qmc.mode == "F":
                self.aw.qmc.R1_DT = fromCtoF(self.aw.qmc.R1_DT)
                self.aw.qmc.R1_BT = fromCtoF(self.aw.qmc.R1_BT)
                self.aw.qmc.R1_EXIT_TEMP = fromCtoF(self.aw.qmc.R1_EXIT_TEMP)
                self.aw.qmc.R1_BT_ROR = RoRfromCtoF(self.aw.qmc.R1_BT_ROR)
        except Exception as exception:
            error = QApplication.translate("Error Message", "Aillio R1: " + str(exception), None)
            self.aw.qmc.adderror(error)
        return tx, self.aw.qmc.R1_DT, self.aw.qmc.R1_BT

    def R1_BTIBTS(self):
        self.R1_DTBT()
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        # DT is being used as IBTS.
        return tx, self.aw.qmc.R1_BT, self.aw.qmc.R1_DT

    def R1_DRUM_BTROR(self):
        tx = self.aw.qmc.R1_TX
        return tx, self.aw.qmc.R1_DRUM, self.aw.qmc.R1_BT_ROR

    def R1_HF(self):
        tx = self.aw.qmc.R1_TX
        return tx, self.aw.qmc.R1_FAN, self.aw.qmc.R1_HEATER

    def R1_EXIT_TEMP_VOLT(self):
        tx = self.aw.qmc.R1_TX
        return tx, self.aw.qmc.R1_EXIT_TEMP, self.aw.qmc.R1_VOLTAGE

    def R1_RPM_STATE(self):
        tx = self.aw.qmc.R1_TX
        return tx, self.aw.qmc.R1_FAN_RPM, self.aw.qmc.R1_STATE
    
    # if force the optimizer is deactivated to ensure fetching fresh readings
    def MODBUS(self,force=False):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.MODBUSread(force)
        return tx,t2,t1

    def MODBUS_34(self):
        return self.aw.qmc.extraMODBUStx,self.aw.qmc.extraMODBUStemps[3],self.aw.qmc.extraMODBUStemps[2]
        
    def MODBUS_56(self):
        return self.aw.qmc.extraMODBUStx,self.aw.qmc.extraMODBUStemps[5],self.aw.qmc.extraMODBUStemps[4]
        
    def MODBUS_78(self):
        return self.aw.qmc.extraMODBUStx,self.aw.qmc.extraMODBUStemps[7],self.aw.qmc.extraMODBUStemps[6]

    def HH802U(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.HH806AUtemperature()
        return tx,t2,t1

    def HH309(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER309temperature()
        return tx,t2,t1

    def CENTER309(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER309temperature()
        return tx,t2,t1

    #special function that collects extra T3 and T4 from center 309 while keeping compatibility
    def CENTER309_34(self):
        #return saved readings collected at self.CENTER309temperature()
        return self.aw.qmc.extra309TX,self.aw.qmc.extra309T4,self.aw.qmc.extra309T3

    #special function that collects extra T3 and T4 from center 304 while keeping compatibility
    def CENTER304_34(self):
        return self.CENTER309_34()

    def CENTER306(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER306temperature()
        return tx,t2,t1

    def CENTER305(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER306temperature()
        return tx,t2,t1

    def CENTER304(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER309temperature()
        return tx,t2,t1

    def CENTER303(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER303temperature()
        return tx,t2,t1

    def CENTER302(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER302temperature()
        return tx,t2,t1

    def CENTER301(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER303temperature()
        return tx,t2,t1

    def CENTER300(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER302temperature()
        return tx,t2,t1

    def VOLTCRAFTK204(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER309temperature()
        return tx,t2,t1

    #especial function that collects extra T3 and T4 from Vol K204 while keeping compatibility
    def K204_34(self):
        #return saved readings collected at self.CENTER309temperature()
        return self.aw.qmc.extra309TX,self.aw.qmc.extra309T4,self.aw.qmc.extra309T3

    def VOLTCRAFTK201(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER302temperature()
        return tx,t2,t1

    def VOLTCRAFTK202(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER306temperature()
        return tx,t2,t1

    def VOLTCRAFT300K(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER302temperature()
        return tx,t2,t1

    def VOLTCRAFT302KJ(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.CENTER303temperature()
        return tx,t2,t1

    def VOLTCRAFTPL125T2(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.VOLTCRAFTPL125T2temperature()
        return tx,t2,t1

    def VOLTCRAFTPL125T4(self):
        t2,t1 = self.VOLTCRAFTPL125T4temperature()
        return self.aw.qmc.extraPL125T4TX,t2,t1

    #especial function that collects extra T3 and T4 from Vol PL125-T4 while keeping compatibility
    def VOLTCRAFTPL125T4_34(self):
        #return saved readings collected at self.VOLTCRAFTPL125T4temperature()
        return self.aw.qmc.extraPL125T4TX,self.aw.qmc.extraPL125T4T4,self.aw.qmc.extraPL125T4T3

    def EXTECH421509(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.HH506RAtemperature()
        return tx,t2,t1

    def NONE(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.NONEtmp()
        return tx,t2,t1

    def ARDUINOTC4(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.ARDUINOTC4temperature()
        return tx,t2,t1

    def ARDUINOTC4_34(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t1 = self.aw.qmc.extraArduinoT1
        t2 = self.aw.qmc.extraArduinoT2
        return tx,t2,t1

    def ARDUINOTC4_56(self): # heater / fan DUTY %
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t1 = self.aw.qmc.extraArduinoT3
        t2 = self.aw.qmc.extraArduinoT4
        return tx,t2,t1

    def ARDUINOTC4_78(self): # PID SV / internal temp
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t1 = self.aw.qmc.extraArduinoT5
        t2 = self.aw.qmc.extraArduinoT6
        return tx,t2,t1
    
    def HB_BTET(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.ARDUINOTC4temperature("1300")
        return tx,t2,t1
    
    def HB_DTIT(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        self.SP = self.aw.ser.SP # we link to the serial port object of the main device
        t2,t1 = self.ARDUINOTC4temperature("2400")
        return tx,t2,t1

    def HB_AT(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t = self.aw.qmc.extraArduinoT6
        return tx,t,t

    def probat_middleware(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t1 = -1
        t2 = -1
        self.aw.qmc.ProbatMiddleware_pressure = -1
        self.aw.qmc.ProbatMiddleware_burner = -1
        self.aw.qmc.ProbatMiddleware_drum = -1
        self.aw.qmc.ProbatMiddleware_fan = -1
        if self.aw.qmc.probatManager is None:
            from artisanlib.probat import ProbatMiddleware
            self.aw.qmc.probatManager = ProbatMiddleware()
        if self.aw.qmc.probatManager is not None:
            connected = self.aw.qmc.probatManager.isConnected()
            if not connected:
                connected = self.aw.qmc.probatManager.connect()
                if connected:
                    name = self.aw.qmc.probatManager.getRoasterName()
                    if name is None:
                        name = ""
                    self.aw.sendmessage(QApplication.translate("Message","Probat Middleware roaster {} connected".format(name),None))
            if connected:
                url = self.aw.qmc.probatManager.getRoasterURL()
                if url is not None:
                    try:
                        data = self.aw.qmc.probatManager.getJSON(url)
                        roastData = data["roastingProcess"]
                        if "productTemperature" in roastData:
                            t1 = roastData["productTemperature"]
                        if "exhaustTemperature" in roastData:
                            t2 = roastData["exhaustTemperature"]
                        if "underPressure" in roastData:
                            self.aw.qmc.ProbatMiddleware_pressure = roastData["underPressure"]
                        if "burnerCapacity" in roastData:
                            self.aw.qmc.ProbatMiddleware_burner = roastData["burnerCapacity"]
                        if "drumSpeed" in roastData:
                            self.aw.qmc.ProbatMiddleware_drum = roastData["drumSpeed"]
                        if "exhaustFanSpeed" in roastData:
                            self.aw.qmc.ProbatMiddleware_fan = roastData["exhaustFanSpeed"]
                    except:
                        self.aw.qmc.probatManager.disconnect()
                        self.aw.sendmessage(QApplication.translate("Message","Probat Middleware disconnected",None))
        return tx,t2,t1

    def probat_middleware_burner_drum(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t1 = self.aw.qmc.ProbatMiddleware_burner
        t2 = self.aw.qmc.ProbatMiddleware_drum
        return tx,t2,t1

    def probat_middleware_fan_pressure(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t1 = self.aw.qmc.ProbatMiddleware_fan
        t2 = self.aw.qmc.ProbatMiddleware_pressure
        return tx,t2,t1
    
    def WSextractData(self,channel,data):
        if self.aw.ws.channel_nodes[channel] != "" and self.aw.ws.channel_nodes[channel] in data:
            # channel active and data availabel
            res = data[self.aw.ws.channel_nodes[channel]]
            # convert temperature scale
            m = self.aw.ws.channel_modes[channel]
            if m == 1 and self.aw.qmc.mode == "F":
                res = fromCtoF(res)
            elif m == 2 and self.aw.qmc.mode == "C":
                res = fromFtoC(res) 
            return res
        else:
            return -1
        
    #returns v1,v2 from a connected WebService device
    # mode=0 to read ch1+2
    # mode=1 to read ch3+4
    # mode=2 to read ch5+6
    # mode=3 to read ch7+8
    # mode=4 to read ch9+10
    def WSread(self,mode):
        # update data
        if mode == 0 and self.aw.ws.request_data_command != "":
            # if device is the main WebSocket device and the request data command is set we request a full set of data using the request data command
            try:
                res = self.aw.ws.send({self.aw.ws.command_node: self.aw.ws.request_data_command})
                if res is not None and self.aw.ws.data_node in res:
                    data = res[self.aw.ws.data_node]
                    for c in range(self.aw.ws.channels):
                        self.aw.ws.readings[c] = self.WSextractData(c,data)
                    
            except:
                self.aw.ws.readings = [-1]*self.aw.ws.channels 
        else:
            for i in [0,1]:
                c = mode*2+i
                if self.aw.ws.channel_requests[c] != "":
                    self.aw.ws.readings[c] = -1
                    try:
                        res = self.aw.ws.send({self.aw.ws.command_node: self.aw.ws.channel_requests[c]})
                        if res is not None and self.aw.ws.data_node in res:
                            data = res[self.aw.ws.data_node]
                            self.aw.ws.readings[c] = self.WSextractData(c,data)
                        else:
                            self.aw.ws.readings[c] = -1
                    except:
                        pass
        
        # return requested data            
        return self.aw.ws.readings[mode*2+1],self.aw.ws.readings[mode*2]
    
    def WS(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.WSread(0)
        return tx,t2,t1
    
    def WS_34(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.WSread(1)
        return tx,t2,t1
        
    def WS_56(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.WSread(2)
        return tx,t2,t1

    def WS_78(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.WSread(3)
        return tx,t2,t1

    def WS_910(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.WSread(4)
        return tx,t2,t1
    
    def YOCTO_thermo(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.YOCTOtemperatures(0)
        return tx,v1,v2
        
    def YOCTO_generic(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.YOCTOtemperatures(4)
        return tx,v1,v2

    def YOCTO_pt100(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.YOCTOtemperatures(1)
        return tx,v1,v2

    def YOCTO_IR(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        v2,v1 = self.YOCTOtemperatures(2)
        return tx,v2,v1

    def TEVA18B(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.TEVA18Btemperature()
        return tx,t2,t1
        
    def EXTECH755(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        t2,t1 = self.EXTECH755pressure()
        return tx,t2,t1

    # EXTECH755 Device
    # returns t1,t2 from EXTECH 755. By Bailey Glen
    def EXTECH755pressure(self, retry=2):
        try:
            r = ''
            if not self.SP.isOpen():
            
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                self.SP.write(b'\x56\xaa\x01')
                r = self.SP.read(10)
                if len(r) == 10:
                    ##Single  line to return pressure twice. obviously only need to do this once.
                    # Takes the last 5 of the 10 byte signal, which is ascii for a float
                    try:
                        self.EXTECH755PrevTemp = float(r[5:])
                        return self.EXTECH755PrevTemp, self.EXTECH755PrevTemp
                    except:
                        if retry:
                            return self.EXTECH755pressure(retry=retry - 1)
                        else:
                            nbytes = len(r)
                            self.aw.qmc.adderror(QApplication.translate("Error Message",
                                                               "Extech755pressure(): conversion error, {0} bytes received",
                                                               None).format(nbytes))
                            if self.EXTECH755PrevTemp != -1:
                                s = self.EXTECH755PrevTemp
                                self.EXTECH755PrevTemp = -1
                                return s,s
                            else:
                                return -1,-1                       
                else:
                    if retry:
                        return self.EXTECH755pressure(retry=retry - 1)
                    else:
                        nbytes = len(r)
                        self.aw.qmc.adderror(QApplication.translate("Error Message",
                                                               "Extech755pressure(): {0} bytes received but 10 needed",
                                                               None).format(nbytes))
                        if self.EXTECH755PrevTemp != -1:
                            s = self.EXTECH755PrevTemp
                            self.EXTECH755PrevTemp = -1
                            return s,s
                        else:
                            return -1,-1
            else:
                return -1, -1
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:",
                                                    None) + " ser.EXTECH755pressure() {0}").format(str(ex)),
                            exc_tb.tb_lineno)
            self.closeport()
            return -1, -1
        finally:
            # note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize) + "," + str(
                    self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial(
                    "EXTECH755: " + settings + " || Tx = " + cmd2str(binascii.hexlify(b'\x56\xaa\x01')) + " || Rx = " + cmd2str(
                        binascii.hexlify(r[5:])))        

    #multimeter
    def HHM28(self):
        tx = self.aw.qmc.timeclock.elapsed()/1000.
        val,symbols= self.HHM28multimeter()  #NOTE: val and symbols are type strings
        #temporary fix to display the output
        self.aw.sendmessage(val + symbols)
        if "L" in val:  #L = Out of Range
            return tx, 0., 0.
##        else:
##            #read quantifier symbols
##            if "n" in symbols:
##                val /= 1000000000.
##            elif "u" in symbols:
##                val /= 1000000.
##            elif "m" in symbols:
##                val /= 1000.
##            elif "k" in symbols:
##                val *= 1000.
##            elif "M" in symbols:
##                val *= 1000000.
            ### not finished
        else:
            return tx, 0., float(val)   #send a 0. as second reading because the meter only returns one reading

    # connects to a Yocto Meteo, returns current humidity value
    def YoctoMeteoHUM(self):
        try:
            self.YOCTOimportLIB() # first import the lib
            from yoctopuce.yocto_humidity import YHumidity
            HUMsensor = YHumidity.FirstHumidity()
            if HUMsensor is not None and HUMsensor.isOnline():
                return HUMsensor.get_currentValue()
            else:
                return None
        except:
            return None
            
    # connects to a Yocto Meteo, returns current temperature value
    def YoctoMeteoTEMP(self):
        try:
            self.YOCTOimportLIB() # first via import the lib
            from yoctopuce.yocto_temperature import YTemperature
            METEOsensor = self.getNextYOCTOsensorOfType(3,[],YTemperature.FirstTemperature())
            if METEOsensor is not None and METEOsensor.isOnline():
                serial = METEOsensor.get_module().get_serialNumber()
                tempCh = YTemperature.FindTemperature(serial + '.temperature')
                if tempCh.isOnline():
                    return tempCh.get_currentValue()
                else:
                    return None
            else:
                return None
        except:
            return None
            
    # connects to a Yocto Meteo, returns current pressure value
    def YoctoMeteoPRESS(self):
        try:
            self.YOCTOimportLIB() # first via import the lib
            from yoctopuce.yocto_pressure import YPressure
            PRESSsensor = YPressure.FirstPressure()
            if PRESSsensor is not None and PRESSsensor.isOnline():
                return PRESSsensor.get_currentValue()
            else:
                return None
        except:
            return None

    # connects to a Phidgets HUM1000, returns current temperature value and disconnects
    def PhidgetHUM1000temperature(self):
        try:
            # Temperature
            tempSensor = PhidgetTemperatureSensor()
            ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetTemperatureSensor',DeviceID.PHIDID_HUM1000,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
            if ser is None:
                ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetTemperatureSensor',DeviceID.PHIDID_HUM1001,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
            if ser:
                tempSensor.setDeviceSerialNumber(ser)
                tempSensor.setHubPort(port)   #explicitly set the port to where the HUM is attached
                if self.aw.qmc.phidgetRemoteFlag:
                    self.addPhidgetServer() 
                if self.aw.qmc.phidgetRemoteFlag and self.aw.qmc.phidgetRemoteOnlyFlag:
                    tempSensor.setIsRemote(True)
                    tempSensor.setIsLocal(False)
                tempSensor.openWaitForAttachment(1500)
                if tempSensor.getAttached():
                    libtime.sleep(0.3)
                    res = tempSensor.getTemperature()
                    tempSensor.close()
                    return res
                else:
                    return None
            else:
                return None
        except Exception:
            return None

    # connects to a Phidgets TMP1000, returns current temperature value and disconnects
    def PhidgetTMP1000temperature(self):
        try:
            # Temperature
            tempSensor = PhidgetTemperatureSensor()
            ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetTemperatureSensor',DeviceID.PHIDID_TMP1000,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
            if ser:
                tempSensor.setDeviceSerialNumber(ser)
                tempSensor.setHubPort(port)   #explicitly set the port to where the HUM is attached
                if self.aw.qmc.phidgetRemoteFlag:
                    self.addPhidgetServer() 
                if self.aw.qmc.phidgetRemoteFlag and self.aw.qmc.phidgetRemoteOnlyFlag:
                    tempSensor.setIsRemote(True)
                    tempSensor.setIsLocal(False)
                tempSensor.openWaitForAttachment(1500)
                if tempSensor.getAttached():
                    libtime.sleep(0.3)
                    res = tempSensor.getTemperature()
                    tempSensor.close()
                    return res
                else:
                    return None
            else:
                return None
        except Exception:
            return None
            
    # connects to a Phidgets HUM1000, returns current humidity value and disconnects
    def PhidgetHUM1000humidity(self):
        try:
            # Humidity
            humSensor = PhidgetHumiditySensor()
            ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetHumiditySensor',DeviceID.PHIDID_HUM1000,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
            if ser is None:
                ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetHumiditySensor',DeviceID.PHIDID_HUM1001,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
            if ser:
                humSensor.setDeviceSerialNumber(ser)
                humSensor.setHubPort(port)   #explicitly set the port to where the HUM is attached
                if self.aw.qmc.phidgetRemoteFlag:
                    self.addPhidgetServer() 
                if self.aw.qmc.phidgetRemoteFlag and self.aw.qmc.phidgetRemoteOnlyFlag:
                    humSensor.setIsRemote(True)
                    humSensor.setIsLocal(False)
                humSensor.openWaitForAttachment(1500)
                if humSensor.getAttached():
                    libtime.sleep(0.3)
                    res = humSensor.getHumidity()
                    humSensor.close()
                    return res
                else:
                    return None
            else:
                return None
        except Exception:
            return None

    # connects to a Phidgets PRE1000, returns current pressure value and disconnects
    def PhidgetPRE1000pressure(self):
        try:
            pressSensor = PhidgetPressureSensor()
            ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetPressureSensor',DeviceID.PHIDID_PRE1000,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
            if ser:
                pressSensor.setDeviceSerialNumber(ser)
                pressSensor.setHubPort(port)   #explicitly set the port to where the PRE is attached  
                if self.aw.qmc.phidgetRemoteFlag:
                    self.addPhidgetServer() 
                if self.aw.qmc.phidgetRemoteFlag and self.aw.qmc.phidgetRemoteOnlyFlag:
                    pressSensor.setIsRemote(True)
                    pressSensor.setIsLocal(False)
                pressSensor.openWaitForAttachment(1500)
                if pressSensor.getAttached():
                    libtime.sleep(0.3)
                    res = pressSensor.getPressure()
                    pressSensor.close()
                    return res
                else:
                    return None
            else:
                return None
        except Exception:
            return None

############################################################################
    def openport(self):
        try:
            self.confport()
            self.ArduinoIsInitialized = 0  # Assume the Arduino has to be reinitialized
            #open port
            if not self.SP.isOpen():
                self.SP.open()
                if self.aw.seriallogflag:
                    settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                    self.aw.addserial("serial port openend: " + settings) 
                libtime.sleep(.2) # avoid possible hickups on startup
        except Exception:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            self.SP.close()
            libtime.sleep(0.7) # on OS X opening a serial port too fast after closing the port get's disabled
            error = QApplication.translate("Error Message","Serial Exception:",None) + QApplication.translate("Error Message","Unable to open serial port",None)
            self.aw.qmc.adderror(error)

    #loads configuration to ports
    def confport(self):
        self.SP.port = self.comport
        self.SP.baudrate = self.baudrate
        self.SP.bytesize = self.bytesize
        self.SP.parity = self.parity
        self.SP.stopbits = self.stopbits
        self.SP.timeout = self.timeout

    def closeport(self):
        try:
            if self.SP and self.SP.isOpen():
                self.SP.close()
                libtime.sleep(0.1) # on OS X opening a serial port too fast after closing the port get's disabled
        except Exception:
            pass

    def closeEvent(self,_):
        try:
            self.closeport() 
        except Exception:
            pass

    def binary(self, n, digits=8):
        return "{0:0>{1}}".format(bin(n)[2:], digits)

    #similar to Omega HH806
    def MS6514temperature(self, retry=2):
        try:
#            command = str2cmd("#0A0000NA2\r\n")  #"#0A0101NA4\r\n"
            r = ""
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_input_buffer()
#                self.SP.reset_output_buffer()
#                self.SP.write(command)
                r = self.SP.read(18)
                index = -1
                if(len(r) == 18 and r[0] == 101 and r[1] == 20):  # 101="\x65"  20="\x14"
                    index = 0
                else:
                    if(len(r) >= 9):
                        # find 0x65 0x14
                        for i in range(len(r)-1):
                            if(r[i] == 101 and r[i+1] == 20): # "\x65" and "\x14"
                                index = i
                                break
                
                    if index > 0:
                        r += self.SP.read(index)
                    else:
                        r += self.SP.read(18-1)     # maybe last character is 0x65. otherwise error.
                
                        if(len(r) >= 9):
                            # find 0x65 0x14
                            for i in range(len(r)-1):
                                if (r[i] == 101 and r[i+1] == 20):  # "\x65" and "\x14"
                                    index = i
                                    break
                
                if(index >= 0 and len(r) >= index+18):
                    if (r[index+16] == 13 and r[index+17] == 10):  # 13="\x0d" and  10="\x0a"
                        #convert to binary to hex string
                        # Display [5-6] [7-8]  [11]                                          [12]
                        #   T1     T1    T2    T1: OK(08), NC(40)                            T2: OK(08), NC(40)
                        #   T2     T2    T1    T2: OK(09), NC(41)                            T1: OK(08), NC(40)
                        #  T1-T2  T1-T2  T1    T1+T2: OK+(0A), OK-(8A), T1NC(42), T2NC(C2)   T1: OK(08), NC(40)
                        #  T1-T2  T1-T2  T2    T1-T2: OK+(0B), OK-(8B), T1NC(43), T2NC(C3)   T2: OK(08), NC(40)
                        s1 = hex2int(r[index+5],r[index+6])/10.
                        s2 = hex2int(r[index+7],r[index+8])/10.

                        # 64="\x40"  67="\x43" 194="\xC2" 195="\xC3"
                        if ((r[index+11] >= 64 and r[index+11] <= 67) or (r[index+11] >= 194 and r[index+11] <= 195)):
                            s1 = -1
                    
                        if(r[index+12] == 64): # 64="\x40"
                            s2 = -1

                        #return original T1 T2
                        if(r[index+11] == 9 or r[index+11] == 65): # 9="\x09" 65="\x41"
                            temp = s2
                            s2 = s1
                            s1 = temp
                        elif(r[index+11] == 10): # 10="\x0a"
                            temp = s2
                            s2 = s2-s1
                            s1 = temp
                        elif(r[index+11] == 138): # 138="\x8a"
                            temp = s2
                            s2 = s2+s1
                            s1 = temp
                        elif(r[index+11] == 66 or r[index+11] == 194):  # 66="\x42" and 194="\xc2"
                            s1 = s2
                            s2 = -1
                        elif(r[index+11] == 11): # 11="\x0b"
                            s1 += s2
                        elif(r[index+11] == 139): # 139="\x8b"
                            s1 = s2-s1

                        #we convert the strings to integers. Divide by 10.0 (decimal position)
                        self.MS6514PrevTemp1 = s1
                        self.MS6514PrevTemp2 = s2
                        return s1,s2
                
                if retry:
                    if retry < 2:
                        self.closeport()
                        libtime.sleep(.05)
                    a,b = self.MS6514temperature(retry=retry-1)
                    return a,b                    
                else:
                    # error but return previous temperature
                    if(self.MS6514PrevTemp1 != -1 or self.MS6514PrevTemp2 != -1):
                        s1 = self.MS6514PrevTemp1
                        s2 = self.MS6514PrevTemp2
                        self.MS6514PrevTemp1 = -1
                        self.MS6514PrevTemp2 = -1
                        return s1,s2
                        
                    # error
                    nbytes = len(r)
                    self.aw.qmc.adderror(QApplication.translate("Error Message","MS6514temperature(): {0} bytes received but 18 needed",None).format(nbytes))
                    return -1,-1                                    #return something out of scope to avoid function error (expects two values)
            else:
                return -1,-1
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " ser.MS6514temperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            self.closeport()
            return -1,-1
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("MS6514: " + settings + " || Rx = " + cmd2str(binascii.hexlify(r))) 


    def DT301temperature(self, retry=2):
        try:
            temp = 0
            command = b"\xEC\xD0\xF3"
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.write(command)
                libtime.sleep(0.01)  # this may not be necessary but works well
                r = self.SP.read(11)
                if len(r)==11:
                    data = bytearray(r)
                    if len(data)==11 and data[0] == 0xfc and data[1] == 0x13 and data[10] == 0xf3:
                        for i in range(2,6):
                            temp = (temp << 4) | (data[i] & 0xf)
                        self.DT301PrevTemp = temp/10.0,0
                        return self.DT301PrevTemp,-1
                if retry:
                    self.SP.reset_input_buffer()
                    self.SP.reset_output_buffer()
                    libtime.sleep(.05)
                    return self.DT301temperature(retry=retry-1)
                else:
                    self.closeport()
                    # error but return previous temperature
                    if self.DT301PrevTemp != -1:
                        s = self.DT301PrevTemp
                        self.DT301PrevTemp = -1
                        return s,0
                        
                    # error
                    nbytes = len(data)
                    self.aw.qmc.adderror(QApplication.translate("Error Message","DT301temperature(): {0} bytes received but 11 needed",None).format(nbytes))
                    return -1,-1                                    #return something out of scope to avoid function error (expects two values)
            else:
                return -1,-1
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " ser.DT301temperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            self.closeport()
            return -1,-1
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("DT301: " + settings + " || Rx = " + cmd2str(binascii.hexlify(data))) 

    # if serial input is not \0 terminated standard pyserial readline returns only after the timeout
    def readline_terminated(self,eol=b'\r'):
        leneol = len(eol)
        line = bytearray()
        while True:
            c = self.SP.read(1)
            if c:
                line += c
                if line[-leneol:] == eol:
                    break
            else:
                break
        return bytes(line)
    
    def BEHMORtemperatures(self,ch1,ch2):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            command = ""
            if not self.aw.ser.SP.isOpen():
                self.aw.ser.openport()
            temps = [-1,-1]
            if self.aw.ser.SP.isOpen():
                for i,c in [(0,ch1),(1,ch2)]:
                    try:
                        command = "gts," + str(c) + "\r\n"
                        self.aw.ser.SP.reset_input_buffer()
                        self.aw.ser.SP.reset_output_buffer()
                        self.aw.ser.SP.write(str2cmd(command))
                        res = self.aw.ser.readline_terminated(b'\r') # .decode('utf-8', 'ignore')
                        #res = self.aw.ser.SP.readline() # takes at least the timeout period as line is not \n terminated!
                        #res = self.aw.ser.SP.read_until('\r') # takes at least the timeout period!
                        t = float(res)
                        if self.aw.qmc.mode == "F":
                            t = fromCtoF(t)
                        temps[i] = t
                        if self.aw.seriallogflag:
                            settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                            self.aw.addserial("Behmor: " + settings + " || Tx = " + str(command) + " || Rx = " + str(res) + " || Ts= %.2f"%t)
                    except:
                        pass
            return temps[0],temps[1]
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:",None) + " ser.BEHMORtemperatures(): {0}").format(str(e)),exc_tb.tb_lineno)
            self.aw.ser.closeport()
            return -1.,-1.
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    
    def HOTTOPtemperatures(self):
        try:
            from artisanlib.hottop import getHottop
            BT, ET, heater, main_fan = getHottop()
            self.aw.qmc.hottop_HEATER = heater
            self.aw.qmc.hottop_MAIN_FAN = main_fan
            self.aw.qmc.hottop_ET = ET
            self.aw.qmc.hottop_BT = BT
            if self.aw.qmc.mode == "F":
                self.aw.qmc.hottop_ET = fromCtoF(self.aw.qmc.hottop_ET)
                self.aw.qmc.hottop_BT = fromCtoF(self.aw.qmc.hottop_BT)
            return self.aw.qmc.hottop_BT,self.aw.qmc.hottop_ET
        except Exception as ex:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " ser.HOTTOPtemperatures() {0}").format(str(ex)),exc_tb.tb_lineno)
            return -1,-1

    #t2 and t1 from Omega HH806, HH802 or Amprobe TMD56 meter 
    def HH806AUtemperature(self, retry=2):
        try:
            command = str2cmd("#0A0000NA2\r\n")
            r = ""
            if not self.SP.isOpen():
                self.openport()
                libtime.sleep(.05)
            if self.SP.isOpen():
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                self.SP.write(command)
                r = self.SP.read(16)
                if len(r) == 16 and hex2int(r[0])==62 and hex2int(r[1])==15:
                    #convert to binary to hex string
                    s1 = hex2int(r[5],r[6])/10.
                    s2 = hex2int(r[10],r[11])/10.
                    #we convert the strings to integers. Divide by 10.0 (decimal position)
                    return s1,s2
                else:
                    # first try to resync data (shift to right assuming some extra bytes were appended):
                    for i in range(4):
                        if len(r) > 12+i and hex2int(r[1+i])==62 and hex2int(r[2+i])==15:
                            s1 = hex2int(r[6+i],r[7+i])/10.
                            s2 = hex2int(r[11+i],r[12+i])/10.
                            return s1,s2
                    if retry:
                        if retry < 2:
                            self.closeport()
                            libtime.sleep(.05)
                        a,b = self.HH806AUtemperature(retry=retry-1)
                        return a,b
                    else:
                        nbytes = len(r)
                        self.aw.qmc.adderror(QApplication.translate("Error Message","HH806AUtemperature(): {0} bytes received",None).format(nbytes))
                        return -1,-1                                    #return something out of scope to avoid function error (expects two values)
            else:
                return -1,-1
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " ser.HH806AUtemperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            self.closeport()
            return -1,-1
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("H806: " + settings + " || Tx = " + cmd2str(binascii.hexlify(command)) + " || Rx = " + cmd2str(binascii.hexlify(r)))

    def HH806Winit(self):
        try:
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                self.SP.write(str2cmd("#0A0000RA6\r\n"))
                libtime.sleep(.3)
                self.SP.write(str2cmd("#0A0000RA6\r\n"))
                libtime.sleep(.3)
                self.SP.write(str2cmd("\x21\x05\x00\x58\x7E"))
                libtime.sleep(2.)
                self.HH806Winitflag = 1
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " ser.HH806Winit() {0}").format(str(ex)),exc_tb.tb_lineno)
            return -1,-1
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                command = "#0A0000RA6\r\n #0A0000RA6\r\n \x21\x05\x00\x58\x7E"
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("H806Winit: " + settings + " || Tx = " + command + " || Rx = ")

    #UNDER WORK 806 wireless meter
    def HH806Wtemperature(self):
        if self.HH806Winitflag == 0:
            self.HH806Winit()
            if self.HH806Winitflag == 0:
                self.aw.qmc.adderror(QApplication.translate("Error Message","HH806Wtemperature(): Unable to initiate device",None))
                return -1,-1
        try:
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                for _ in range(27):
                    rcode = self.SP.read(1)
                    #locate first byte
                    if rcode == "\x3d":
                        r = self.SP.read(25)
                        if len(r) == 25:
                            r1 = hex2int(r[11],r[12])/10.
                            r2 = hex2int(r[19],r[20])/10.
                            #GOOD
                            return r1,r2
                #BAD
                return -1.,-1.
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " ser.HH806Wtemperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            return -1,-1
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("H806Wtemperature: " + settings + " || Rx = " + binascii.hexlify(r))

    # input: value x; divider d; mode m
    # returns processed value
    def processChannelData(self,x,d,m):
        if x is None:
            res = -1
        else:            
            # apply divider
            if d==1: # apply divider
                res = x / 10.
            elif d==2: # apply divider
                res = x / 100.
            else:
                res = x
            # convert temperature scale
            if m == "C" and self.aw.qmc.mode == "F":
                res = fromCtoF(res)
            elif m == "F" and self.aw.qmc.mode == "C":
                res = fromFtoC(res)
        return res
        
    #returns v1,v2 from a connected S7 device
    # mode=0 to read ch1+2
    # mode=1 to read ch3+4
    # mode=2 to read ch5+6
    # mode=3 to read ch7+8
    # mode=4 to read ch9+10
    def S7read(self,mode,force=False):
        # fill the S7 optimizer (if active and not forced to fetch fresh data) with data for all read requests specified in the device S7 tab using block reads
        if not force and mode == 0:
            self.aw.s7.readActiveRegisters()
        res = []
        for i in range(mode*2,mode*2+2):
            if self.aw.s7.area[i]:
                if self.aw.s7.type[i] == 0:
                    v = self.aw.s7.readInt(self.aw.s7.area[i]-1,self.aw.s7.db_nr[i],self.aw.s7.start[i],force)
                elif self.aw.s7.type[i] in [1,2]: # Type FLOAT and FLOAT2INT are read as floats, FLOAT2INT is just displayed without decimals
                    v = self.aw.s7.readFloat(self.aw.s7.area[i]-1,self.aw.s7.db_nr[i],self.aw.s7.start[i],force)
                else:
                    if self.aw.s7.readBool(self.aw.s7.area[i]-1,self.aw.s7.db_nr[i],self.aw.s7.start[i],self.aw.s7.type[i]-3,force):
                        v = 1
                    else:
                        v = 0
                v = self.processChannelData(v,self.aw.s7.div[i],("C" if self.aw.s7.mode[i]==1 else ("F" if self.aw.s7.mode[i]==2 else "")))
                res.append(v)
            else:
                res.append(-1)
        return res[1], res[0]

    #returns v1,v2 from a connected MODBUS device
    # if force, do retrieve fresh readings and ignore the optimizers cached values
    def MODBUSread(self,force=False):
        # fill the MODBUS optimizer (if active and not an oversampling call) with data for all read requests specified in the device MODBUS tab using block reads
        if not force:
            self.aw.modbus.readActiveRegisters()
        
        res = [-1]*self.aw.modbus.channels
        
        for i in range(self.aw.modbus.channels):
            if self.aw.modbus.inputSlaves[i] and not force or i in [0,1]: # in force mode (second request in oversampling mode) read only first two channels (ET/BT)
                if not self.aw.modbus.optimizer:
                    self.aw.modbus.sleepBetween() # we start with a sleep, as it could be that just a send command happend before the semaphore was catched
                if self.aw.modbus.inputFloats[i]:
                    res[i] = self.aw.modbus.readFloat(self.aw.modbus.inputSlaves[i],self.aw.modbus.inputRegisters[i],self.aw.modbus.inputCodes[i],force)
                elif self.aw.modbus.inputFloatsAsInt[i]:
                    res[i] = self.aw.modbus.readInt32(self.aw.modbus.inputSlaves[i],self.aw.modbus.inputRegisters[i],self.aw.modbus.inputCodes[i],force)
                elif self.aw.modbus.inputBCDs[i]:
                    res[i] = self.aw.modbus.readBCD(self.aw.modbus.inputSlaves[i],self.aw.modbus.inputRegisters[i],self.aw.modbus.inputCodes[i],force)
                elif self.aw.modbus.inputBCDsAsInt[i]:
                    res[i] = self.aw.modbus.readBCDint(self.aw.modbus.inputSlaves[i],self.aw.modbus.inputRegisters[i],self.aw.modbus.inputCodes[i],force)
                else:
                    res[i] = self.aw.modbus.readSingleRegister(self.aw.modbus.inputSlaves[i],self.aw.modbus.inputRegisters[i],self.aw.modbus.inputCodes[i],force)
                res[i] = self.processChannelData(res[i],self.aw.modbus.inputDivs[i],self.aw.modbus.inputModes[i])
        
        self.aw.qmc.extraMODBUStemps = res[:]
        self.aw.qmc.extraMODBUStx = self.aw.qmc.timeclock.elapsed()/1000.
        return res[1], res[0]

    def NONEtmp(self):
        dialogx = nonedevDlg(self.aw, self.aw)
        
        # NOT CORRECT:
        ##from sys import getsizeof  # getsizesof not reporting the full size here!
        ##print(getsizeof(dialogx)) # 192bytes using slots; 152bytes without slots;
        
        # # sudo -H python3 -m pip install pympler 
        #from pympler import asizeof
        #print(asizeof.asizeof(dialogx)) # 2440 using slots; 2568 without using slots
        if dialogx.exec_():
            try:
                ET = (int(str(dialogx.etEdit.text())) * 10)/10.
            except Exception:
                ET = 0
            try:
                BT = (int(str(dialogx.btEdit.text())) * 10)/10.
            except Exception:
                BT = 0
            try:
                dialogx.okButton.disconnect()
                dialogx.cancelButton.disconnect()
                QApplication.processEvents() # we ensure events concerning this dialog are processed before deletion
                try: # sip not supported on older PyQt versions (RPi!)
                    sip.delete(dialogx)
                    #print(sip.isdeleted(dialogx))
                except:
                    pass
                del dialogx
            except:
                pass
            return ET, BT
        else:
            try:
                dialogx.okButton.disconnect()
                dialogx.cancelButton.disconnect()
                QApplication.processEvents() # we ensure events concerning this dialog are processed before deletion
                try: # sip not supported on older PyQt versions (RPi!)
                    sip.delete(dialogx)
                    #print(sip.isdeleted(dialogx))
                except:
                    pass
                del dialogx
            except:
                pass
            return -1, -1

    #reads once the id of the HH506RA meter and stores it in the serial variable self.HH506RAid.
    def HH506RAGetID(self):
        try:
            ID = ""
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                sync = None
                while sync != b"Err\r\n":
                    self.SP.write(b"\r\n")
                    sync = self.SP.read(5)
                    libtime.sleep(1)
                self.SP.write(b"%000R")
                self.SP.flush()
                libtime.sleep(.1)
                ID = self.SP.read(5)
                if len(ID) == 5:
                    self.HH506RAid = ID[0:3]               # Assign new id to self.HH506RAid
                else:
                    nbytes = len(ID)
                    self.aw.qmc.adderror(QApplication.translate("Error Message","HH506RAGetID: {0} bytes received but 5 needed",None).format(nbytes))
        except Exception as ex:
            self.closeport()
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " ser.HH506RAGetID() {0}").format(str(ex)),exc_tb.tb_lineno)
            return -1,-1
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("H506: " + settings + " || Rx = " + str(ID))

    #HH506RA Device
    #returns t1,t2 from Omega HH506 meter
    def HH506RAtemperature(self, retry=2):
        #if initial id "X" has not changed then get a new one;
        if self.HH506RAid == "X":
            self.HH506RAGetID()                       # obtain new id one time; self.HH506RAid should not be "X" any more
            if self.HH506RAid == "X":                 # if self.HH506RAGetID() went wrong and self.HH506RAid is still "X"
                self.aw.qmc.adderror(QApplication.translate("Error Message","HH506RAtemperature(): Unable to get id from HH506RA device ",None))
                return -1,-1
        try:
            command = b"#" + self.HH506RAid + b"N" # + "\r\n" this seems not to be needed
            r = ""
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                self.SP.write(command)
                self.SP.flush()
                libtime.sleep(.1)
                r = self.SP.read(14)
                if len(r) != 14:
                    # we did not receive all data yet, let's wait a little longer and try to fetch the missing part
                    libtime.sleep(0.05)
                    r = r + self.SP.read(14 - len(r))
                if len(r) == 14:
                    #we convert the hex strings to integers. Divide by 10.0 (decimal position)
                    r = r.replace(str2cmd(' '),str2cmd('0'))
                    return int(r[1:5],16)/10., int(r[7:11],16)/10.
                else:
                    if retry:
                        return self.HH506RAtemperature(retry=retry-1)
                    else:
                        nbytes = len(r)
                        self.aw.qmc.adderror(QApplication.translate("Error Message","HH506RAtemperature(): {0} bytes received but 14 needed",None).format(nbytes))               
                        return -1,-1
            else:
                return -1,-1
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " ser.HH506RAtemperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            self.closeport()
            return -1,-1
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("H506: " + settings + " || Tx = " + cmd2str(binascii.hexlify(command)) + " || Rx = " + cmd2str(binascii.hexlify(r)))

    def CENTER302temperature(self,retry=2):
        try:
            command = str2cmd("\x41")
            r = ""
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                self.SP.write(command)
                self.SP.flush()
                libtime.sleep(.1)
                r = self.SP.read(7)                                   #NOTE: different
                if len(r) != 7:
                    # we did not receive all data yet, let's wait a little longer and try to fetch the missing part
                    libtime.sleep(0.05)
                    r = r + self.SP.read(7 - len(r))                
                if len(r) == 7:
                    #DECIMAL POINT
                    #if bit 2 of byte 3 = 1 then T1 = ####      (don't divide by 10)
                    #if bit 2 of byte 3 = 0 then T1 = ###.#     ( / by 10)
                    #extract bit 2, and bit 5 of BYTE 3
                    b3bin = self.binary(r[2])              #bit"[7][6][5][4][3][2][1][0]"
                    bit2 = b3bin[5]
                    #extract T1
                    B34 = cmd2str(binascii.hexlify(r[3:5])) # select byte 3 and 4
                    if B34[0].isdigit():
                        T1 = float(B34)
                    else:
                        T1 = float(B34[1:])
                    #check decimal point
                    if bit2 == "0":
                        T1 /= 10.
                    return T1,0
                else:
                    if retry:
                        return self.CENTER302temperature(retry=retry-1)
                    else:
                        nbytes = len(r)
                        error = QApplication.translate("Error Message","CENTER302temperature(): {0} bytes received but 7 needed",None).format(nbytes)
                        timez = str(QDateTime.currentDateTime().toString("hh:mm:ss.zzz"))    #zzz = miliseconds
                        self.aw.qmc.adderror(timez + " " + error)
                        return -1,-1 
            else:
                return -1,-1 
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " CENTER302temperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            self.closeport()
            return -1,-1
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("CENTER302: " + settings + " || Tx = " + cmd2str(binascii.hexlify(command)) + " || Rx = " + cmd2str((binascii.hexlify(r))))

    def CENTER303temperature(self,retry=2):
        try:
            command = str2cmd("\x41")
            r = ""
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                self.SP.write(command)
                self.SP.flush()
                libtime.sleep(.1)
                r = self.SP.read(8) #NOTE: different to CENTER306
                if len(r) != 8:
                    # we did not receive all data yet, let's wait a little longer and try to fetch the missing part
                    libtime.sleep(0.05)
                    r = r + self.SP.read(8 - len(r))                
                if len(r) == 8:
                    #DECIMAL POINT
                    #if bit 2 of byte 3 = 1 then T1 = ####      (don't divide by 10)
                    #if bit 2 of byte 3 = 0 then T1 = ###.#     ( / by 10)
                    #if bit 5 of byte 3 = 1 then T2 = ####
                    #if bit 5 of byte 3 = 0 then T2 = ###.#
                    #extract bit 2, and bit 5 of BYTE 3
                    b3bin = self.binary(r[2])              #bit"[7][6][5][4][3][2][1][0]"
                    bit2 = b3bin[5]
                    bit5 = b3bin[2]
                    #extract T1
                    B34 = cmd2str(binascii.hexlify(r[3:5])) # select byte 3 and 4
                    if B34[0].isdigit():
                        T1 = float(B34)
                    else:
                        T1 = float(B34[1:])
                    #extract T2
                    B56 = cmd2str(binascii.hexlify(r[5:7])) # select byte 5 and 6; NOTE: different to CENTER303
                    if B56[0].isdigit():
                        T2 = float(B56)
                    else:
                        T2 = float(B56[1:])
                    #check decimal point
                    if bit2 == "0":
                        T1 /= 10.
                    if bit5 == "0":
                        T2 /= 10.
                    return T1,T2
                else:
                    if retry:
                        return self.CENTER303temperature(retry=retry-1)
                    else:
                        nbytes = len(r)
                        error = QApplication.translate("Error Message","CENTER303temperature(): {0} bytes received but 8 needed",None).format(nbytes)
                        timez = str(QDateTime.currentDateTime().toString("hh:mm:ss.zzz"))    #zzz = miliseconds
                        self.aw.qmc.adderror(timez + " " + error)
                        return -1,-1
            else:
                return -1,-1 
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " CENTER303temperature() {0}").format(str(ex)),exc_tb.tb_lineno)            
            self.closeport()
            return -1,-1
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("CENTER303: " + settings + " || Tx = " + cmd2str(binascii.hexlify(command)) + " || Rx = " + cmd2str((binascii.hexlify(r))))


    def VOLTCRAFTPL125T2temperature(self,retry=2):
        try:
            command = bytearray([244, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
            r = ""
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                self.SP.write(command)
                self.SP.flush()
                libtime.sleep(.1)
                r = self.SP.read(26)
                if len(r) != 26:
                    # we did not receive all data yet, let's wait a little longer and try to fetch the missing part
                    libtime.sleep(0.05)
                    r = r + self.SP.read(26 - len(r))                
                if len(r) == 26 and hex2int(r[0],r[1]) == 43605: # filter out bad/strange data
                    #extract T1
                    T1 = hex2int(r[19],r[18])/10. # select byte 19 and 18
                    #extract T2
                    T2 = hex2int(r[21],r[20])/10.# select byte 21 and 20 
                    return T1,T2
                else:
                    if retry:
                        libtime.sleep(.05)
                        return self.VOLTCRAFTPL125T2temperature(retry=retry-1)
                    else:
                        nbytes = len(r)
                        error = QApplication.translate("Error Message","VOLTCRAFTPL125T2temperature(): {0} bytes received but 26 needed",None).format(nbytes)
                        timez = str(QDateTime.currentDateTime().toString("hh:mm:ss.zzz"))    #zzz = miliseconds
                        _,_, exc_tb = sys.exc_info()
                        self.aw.qmc.adderror(timez + " " + error)
                        return -1,-1
            else:
                return -1,-1
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " VOLTCRAFTPL125T2temperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            self.closeport()
            return -1,-1
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("VOLTCRAFTPL125T2: " + settings + " || Tx = " + cmd2str(binascii.hexlify(command)) + " || Rx = " + cmd2str((binascii.hexlify(r))))

    def VOLTCRAFTPL125T4temperature(self,retry=2):
        try:
            command = bytearray([244, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
            r = ""
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                self.SP.write(command)
                self.SP.flush()
                libtime.sleep(.1)
                r = self.SP.read(26)
                if len(r) != 26:
                    # we did not receive all data yet, let's wait a little longer and try to fetch the missing part
                    libtime.sleep(0.05)
                    r = r + self.SP.read(26 - len(r))                
                if len(r) == 26 and hex2int(r[0],r[1]) == 43605: # filter out bad/strange data
                    self.aw.qmc.extraPL125T4TX = self.aw.qmc.timeclock.elapsed()/1000.
                    #extract T1
                    T1 = hex2int(r[23],r[22])/10.# select byte 23 and 22
                    #extract T2
                    T2 = hex2int(r[25],r[24])/10.# select byte 25 and 24
                    self.aw.qmc.extraPL125T4T4 = hex2int(r[21],r[20])/10.# select byte 21 and 20
                    self.aw.qmc.extraPL125T4T3 = hex2int(r[19],r[18])/10. # select byte 19 and 18
                    return T1,T2
                else:
                    if retry:
                        libtime.sleep(.05)
                        return self.VOLTCRAFTPL125T4temperature(retry=retry-1)
                    else:
                        nbytes = len(r)
                        error = QApplication.translate("Error Message","VOLTCRAFTPL125T4temperature(): {0} bytes received but 26 needed",None).format(nbytes)
                        timez = str(QDateTime.currentDateTime().toString("hh:mm:ss.zzz"))    #zzz = miliseconds
                        _,_, exc_tb = sys.exc_info()
                        self.aw.qmc.adderror(timez + " " + error)
                        return -1,-1
            else:
                return -1,-1
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " VOLTCRAFTPL125T4temperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            self.closeport()
            return -1,-1
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("VOLTCRAFTPL125T4: " + settings + " || Tx = " + cmd2str(binascii.hexlify(command)) + " || Rx = " + cmd2str((binascii.hexlify(r))))


    def CENTER306temperature(self,retry=2):
        try:
            command = str2cmd("\x41")
            r = ""
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                self.SP.write(command)
                self.SP.flush()
                libtime.sleep(.1)
                r = self.SP.read(10) #NOTE: different to CENTER303
                if len(r) != 10:
                    # we did not receive all data yet, let's wait a little longer and try to fetch the missing part
                    libtime.sleep(0.05)
                    r = r + self.SP.read(10 - len(r))                
                if len(r) == 10:
                    #DECIMAL POINT
                    #if bit 2 of byte 3 = 1 then T1 = ####      (don't divide by 10)
                    #if bit 2 of byte 3 = 0 then T1 = ###.#     ( / by 10)
                    #if bit 5 of byte 3 = 1 then T2 = ####
                    #if bit 5 of byte 3 = 0 then T2 = ###.#
                    #extract bit 2, and bit 5 of BYTE 3
                    b3bin = self.binary(r[2])          #bits string order "[7][6][5][4][3][2][1][0]"
                    bit2 = b3bin[5]
                    bit5 = b3bin[2]
                    #extract T1
                    B34 = cmd2str(binascii.hexlify(r[3:5])) # select byte 3 and 4
                    if B34[0].isdigit():
                        T1 = float(B34)
                    else:
                        T1 = float(B34[1:])
                    #extract T2
                    B78 = cmd2str(binascii.hexlify(r[7:9])) # select byte 7 and 9; NOTE: different to CENTER303
                    if B78[0].isdigit():
                        T2 = float(B78)
                    else:
                        T2 = float(B78[1:])
                    #check decimal point
                    if bit2 == "0":
                        T1 /= 10.
                    if bit5 == "0":
                        T2 /= 10.
                    return T1,T2
                else:
                    if retry:
                        return self.CENTER306temperature(retry=retry-1)
                    else:
                        nbytes = len(r)
                        error = QApplication.translate("Error Message","CENTER306temperature(): {0} bytes received but 10 needed",None).format(nbytes)
                        timez = str(QDateTime.currentDateTime().toString("hh:mm:ss.zzz"))    #zzz = miliseconds
                        _,_, exc_tb = sys.exc_info()
                        self.aw.qmc.adderror(timez + " " + error,exc_tb.tb_lineno)
                        return -1,-1
            else:
                return -1,-1
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " CENTER306temperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            self.closeport()
            return -1,-1
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("CENTER306: " + settings + " || Tx = " + cmd2str(binascii.hexlify(command)) + " || Rx = " + cmd2str((binascii.hexlify(r))))

    def CENTER309temperature(self, retry=1):
        ##    command = "\x4B" returns 4 bytes . Model number.
        ##    command = "\x48" simulates HOLD button
        ##    command = "\x4D" simulates MAX/MIN button
        ##    command = "\x4E" simulates EXIT MAX/MIN button
        ##    command = "\x52" simulates TIME button
        ##    command = "\x43" simulates C/F button
        ##    command = "\x55" dump all memmory
        ##    command = "\x50" Load recorded data
        ##    command = "\x41" returns 45 bytes (8x5 + 5 = 45) as follows:
        ##    
        ##    "\x02\x80\xUU\xUU\xUU\xUU\xUU\xAA"  \x80 means "Celsi" (if \x00 then "Faren") UUs unknown
        ##    "\xAA\xBB\xBB\xCC\xCC\xDD\xDD\x00"  Temprerature T1 = AAAA, T2=BBBB, T3= CCCC, T4 = DDDD
        ##    "\x00\x00\x00\x00\x00\x00\x00\x00"  unknown (possible data containers but found empty)
        ##    "\x00\x00\x00\x00\x00\x00\x00\x00"  unknown
        ##    "\x00\x00\x00\x00\x00\x00\x00\x00"  unknown
        ##    "\x00\x00\x00\x0E\x03"              The byte r[43] \x0E changes depending on what thermocouple(s) are connected.
        ##                                        If T1 thermocouple connected alone, then r[43]  = \x0E = 14
        ##                                        If T2 thermocouple connected alone, then r[43]  = \x0D = 13
        ##                                        If T1 + T2 thermocouples connected, then r[43]  = \x0C = 12
        ##                                        If T3 thermocouple connected alone, then r[43]  = \x0B = 11
        ##                                        If T4 thermocouple connected alone, then r[43]  = \x07 = 7
        ##                                        Note: Print r[43] if you want to find other connect-combinations
        ##                                        THIS ONLY WORKS WHEN TEMPERATURE < 200. If T >= 200 r[43] changes
        try:
            command = str2cmd("\x41")
            r = ""
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_output_buffer()
                self.SP.reset_input_buffer()
                self.SP.write(command)
                self.SP.flush()
                libtime.sleep(.1)
                r = self.SP.read(45)
                # the device needs 0.1 too answer a request for temperature data
                # and delivers a reading maximally every 0.4sec, however,
                # readings are internally updated within the instrument only at a rate of about every 3sec thus Artisan should not sample faster than every 3sec                
                if len(r) != 45:
                    # we did not receive all data yet, let's wait a little longer and try to fetch the missing part
                    libtime.sleep(0.05)
                    r = r + self.SP.read(45 - len(r))
                if len(r) == 45:
                    T1 = T2 = T3 = T3 = -1
                    try:
                        T1 = hex2int(r[7],r[8])/10.
                    except Exception:
                        pass
                    try:
                        T2 = hex2int(r[9],r[10])/10.
                    except Exception:
                        pass
                    try:
                        T3 = hex2int(r[11],r[12])/10.
                    except Exception:
                        pass
                    try:
                        T4 = hex2int(r[13],r[14])/10.
                    except Exception:
                        pass
                    #save these variables if using T3 and T4
                    self.aw.qmc.extra309T3 = T3
                    self.aw.qmc.extra309T4 = T4
                    self.aw.qmc.extra309TX = self.aw.qmc.timeclock.elapsed()/1000.
                    return T1,T2
                else:
                    if retry:
                        return self.CENTER309temperature(retry=retry-1)
                    else:
                        nbytes = len(r)
                        self.aw.qmc.adderror(QApplication.translate("Error Message","CENTER309temperature(): {0} bytes received but 45 needed",None).format(nbytes))            
                        return -1,-1 
            else:
                return -1,-1
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " CENTER309temperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            self.closeport()
            return -1,-1
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("CENTER309: " + settings + " || Tx = " + cmd2str(binascii.hexlify(command)) + " || Rx = " + cmd2str((binascii.hexlify(r))))

#---

    def addPhidgetServer(self):
        if not self.aw.qmc.phidgetServerAdded:
            from Phidget22.Net import Net as PhidgetNetwork
            PhidgetNetwork.addServer("PhidgetServer",self.aw.qmc.phidgetServerID,self.aw.qmc.phidgetPort,self.aw.qmc.phidgetPassword,0)
            self.aw.qmc.phidgetServerAdded = True

    def removePhidgetServer(self):
        if self.aw.qmc.phidgetServerAdded:
            from Phidget22.Net import Net as PhidgetNetwork
            PhidgetNetwork.removeServer("PhidgetServer")
            self.aw.qmc.phidgetServerAdded = False

#---

    def phidget1045TemperatureChanged(self,_,t):
        try:
            #### lock shared resources #####
            self.Phidget1045semaphore.acquire(1)
            self.Phidget1045values.append((t,libtime.time()))
        finally:
            if self.Phidget1045semaphore.available() < 1:
                self.Phidget1045semaphore.release(1)
          
    # applies given emissivity to the IR temperature value assuming the given ambient temperature
    def IRtemp(self,emissivity,temp,ambient):
        return (temp - ambient) * emissivity + ambient

    def configure1045(self):
        self.Phidget1045values = []
        self.Phidget1045lastvalue = -1
        self.Phidget1045tempIRavg = None
        if self.PhidgetIRSensor is not None:
            try:
                if self.aw.qmc.phidget1045_async:
                    self.PhidgetIRSensor.setTemperatureChangeTrigger(self.aw.qmc.phidget1045_changeTrigger)
                else:
                    self.PhidgetIRSensor.setTemperatureChangeTrigger(0)
            except:
                pass
            try:
                if self.aw.qmc.phidget1045_async:
                    self.PhidgetIRSensor.setOnTemperatureChangeHandler(self.phidget1045TemperatureChanged)
                else:
                    self.PhidgetIRSensor.setOnTemperatureChangeHandler(lambda *_:None)
            except:
                pass
            # set rate
            try:
                self.PhidgetIRSensor.setDataInterval(self.aw.qmc.phidget1045_dataRate)
            except Exception:
                pass
            
    def configureOneTC(self):
        self.Phidget1045values = []
        self.Phidget1045lastvalue = -1
        self.PhidgetIRSensor.setThermocoupleType(PHIDGET_THERMOCOUPLE_TYPE(self.aw.qmc.phidget1048_types[0]))
        if self.aw.qmc.phidget1048_async[0]:
            self.PhidgetIRSensor.setTemperatureChangeTrigger(self.aw.qmc.phidget1048_changeTriggers[0])
        else:
            self.PhidgetIRSensor.setTemperatureChangeTrigger(0)
        if self.aw.qmc.phidget1048_async[0]:
            self.PhidgetIRSensor.setOnTemperatureChangeHandler(self.phidget1045TemperatureChanged)
        else:
            self.PhidgetIRSensor.setOnTemperatureChangeHandler(lambda *_:None)
        # set rate
        try:
            self.PhidgetIRSensor.setDataInterval(self.aw.qmc.phidget1048_dataRate)
        except Exception:
            pass
            
    def configureOneRTD(self):
        self.Phidget1045values = []
        self.Phidget1045lastvalue = -1
        self.PhidgetIRSensor.setRTDType(PHIDGET_RTD_TYPE(self.aw.qmc.phidget1200_formula))
        self.PhidgetIRSensor.setRTDWireSetup(PHIDGET_RTD_WIRE(self.aw.qmc.phidget1200_wire))
        if self.aw.qmc.phidget1200_async:
            self.PhidgetIRSensor.setTemperatureChangeTrigger(self.aw.qmc.phidget1200_changeTrigger)
            self.PhidgetIRSensor.setOnTemperatureChangeHandler(self.phidget1045TemperatureChanged)
        else:
            self.PhidgetIRSensor.setTemperatureChangeTrigger(0)
            self.PhidgetIRSensor.setOnTemperatureChangeHandler(lambda *_:None)
        # set rate
        try:
            self.PhidgetIRSensor.setDataInterval(self.aw.qmc.phidget1200_dataRate)
        except Exception:
            pass
    
    def configureOneRTD_2(self):
        self.Phidget1045values = []
        self.Phidget1045lastvalue = -1
        self.PhidgetIRSensor.setRTDType(PHIDGET_RTD_TYPE(self.aw.qmc.phidget1200_2_formula))
        self.PhidgetIRSensor.setRTDWireSetup(PHIDGET_RTD_WIRE(self.aw.qmc.phidget1200_2_wire))
        if self.aw.qmc.phidget1200_async:
            self.PhidgetIRSensor.setTemperatureChangeTrigger(self.aw.qmc.phidget1200_2_changeTrigger)
            self.PhidgetIRSensor.setOnTemperatureChangeHandler(self.phidget1045TemperatureChanged)
        else:
            self.PhidgetIRSensor.setTemperatureChangeTrigger(0)
            self.PhidgetIRSensor.setOnTemperatureChangeHandler(lambda *_:None)
        # set rate
        try:
            self.PhidgetIRSensor.setDataInterval(self.aw.qmc.phidget1200_2_dataRate)
        except Exception:
            pass

    def phidget1045attached(self,serial,port,deviceType,alternative_conf=False):
        try:
            self.aw.qmc.phidgetManager.reserveSerialPort(serial,port,0,"PhidgetTemperatureSensor",deviceType,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
            if deviceType != DeviceID.PHIDID_TMP1200:
                self.aw.qmc.phidgetManager.reserveSerialPort(serial,port,1,"PhidgetTemperatureSensor",deviceType,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
            if deviceType == DeviceID.PHIDID_1045:
                self.configure1045()
                self.aw.sendmessage(QApplication.translate("Message","Phidget Temperature Sensor IR attached",None))
            elif deviceType == DeviceID.PHIDID_1051:
                self.configureOneTC()
                self.aw.sendmessage(QApplication.translate("Message","Phidget Temperature Sensor 1-input attached",None))
            elif deviceType == DeviceID.PHIDID_TMP1100:
                self.configureOneTC()
                self.aw.sendmessage(QApplication.translate("Message","Phidget Isolated Thermocouple 1-input attached",None))
            elif deviceType == DeviceID.PHIDID_TMP1200:
                if alternative_conf:
                    self.configureOneRTD_2()
                else:
                    self.configureOneRTD()
                self.aw.sendmessage(QApplication.translate("Message","Phidget VINT RTD 1-input attached",None))
        except:
            pass

    def phidget1045detached(self,serial,port,deviceType):
        try:
            self.aw.qmc.phidgetManager.releaseSerialPort(serial,port,0,"PhidgetTemperatureSensor",deviceType,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
            if deviceType != DeviceID.PHIDID_TMP1200:
                self.aw.qmc.phidgetManager.releaseSerialPort(serial,port,1,"PhidgetTemperatureSensor",deviceType,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
            if deviceType == DeviceID.PHIDID_1045:
                self.aw.sendmessage(QApplication.translate("Message","Phidget Temperature Sensor IR detached",None))
            elif deviceType == DeviceID.PHIDID_1051:
                self.aw.sendmessage(QApplication.translate("Message","Phidget Temperature Sensor 1-input detached",None))
            elif deviceType == DeviceID.PHIDID_TMP1100:
                self.aw.sendmessage(QApplication.translate("Message","Phidget Isolated Thermocouple 1-input detached",None))
            elif deviceType == DeviceID.PHIDID_TMP1200:
                self.aw.sendmessage(QApplication.translate("Message","Phidget VINT RTD 1-input detached",None))
        except:
            pass

    # this one is reused for the 1045 (IR), the 1051 (1xTC), TMP1100 (1xTC), and TMP1200 (1xRTD)
    # if alternative_conf is set, the second configuration for the TMP1200 module is used
    def PHIDGET1045temperature(self,deviceType=DeviceID.PHIDID_1045,retry=True,alternative_conf=False):
        try:
            if not self.PhidgetIRSensor and self.aw.qmc.phidgetManager is not None:
                ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetTemperatureSensor',deviceType,
                            remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                if ser:
                    self.PhidgetIRSensor = PhidgetTemperatureSensor()
                    if deviceType == DeviceID.PHIDID_TMP1200:
                        self.PhidgetIRSensorIC = None # the TMP1200 does not has an internal temperature sensor
                    else:
                        self.PhidgetIRSensorIC = PhidgetTemperatureSensor()
                    try:
                        self.PhidgetIRSensor.setOnAttachHandler(lambda _:self.phidget1045attached(ser,port,deviceType,alternative_conf))
                        self.PhidgetIRSensor.setOnDetachHandler(lambda _:self.phidget1045detached(ser,port,deviceType))
                        if self.aw.qmc.phidgetRemoteFlag:
                            self.addPhidgetServer()
                        if port is not None:
                            self.PhidgetIRSensor.setHubPort(port)
                            if deviceType != DeviceID.PHIDID_TMP1200:
                                self.PhidgetIRSensorIC.setHubPort(port)
                        self.PhidgetIRSensor.setDeviceSerialNumber(ser)
                        self.PhidgetIRSensor.setChannel(0) # attache to the IR channel
                        try:
                            if self.aw.qmc.phidgetRemoteFlag and self.aw.qmc.phidgetRemoteOnlyFlag:
                                self.PhidgetIRSensor.setIsRemote(True)
                                self.PhidgetIRSensor.setIsLocal(False)
                            self.PhidgetIRSensor.open() #.openWaitForAttachment(timeout) # wait attach for the TMP1200 takes about 1sec on USB
                        except:
                            pass
                        if deviceType != DeviceID.PHIDID_TMP1200:
                            self.PhidgetIRSensorIC.setDeviceSerialNumber(ser)
                            self.PhidgetIRSensorIC.setChannel(1) # attache to the IC channel
                            if self.aw.qmc.phidgetRemoteFlag and self.aw.qmc.phidgetRemoteOnlyFlag:
                                self.PhidgetIRSensorIC.setIsRemote(True)
                                self.PhidgetIRSensorIC.setIsLocal(False)
                            try:
                                self.PhidgetIRSensorIC.open() #.openWaitForAttachment(timeout)
                            except:
                                pass
                        # we need to give this device a bit time to attach, otherwise it will be considered for another Artisan channel of the same type
                        if self.aw.qmc.phidgetRemoteOnlyFlag:
                            libtime.sleep(.8)
                        else:
                            libtime.sleep(.5)
                    except Exception as ex:
                        _, _, exc_tb = sys.exc_info()
                        self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " PHIDGET1045temperature() {0}").format(str(ex)),exc_tb.tb_lineno)
                        try:
                            if self.PhidgetIRSensor and self.PhidgetIRSensor.getAttached():
                                self.PhidgetIRSensor.close()
                            if self.PhidgetIRSensorIC and self.PhidgetIRSensorIC.getAttached():
                                self.PhidgetIRSensorIC.close()
                        except Exception:
                            pass
                        self.PhidgetIRSensor = None
                        self.Phidget1045values = []
                        self.Phidget1045lastvalue = -1
                        self.PhidgetIRSensorIC = None
                        self.Phidget1045tempIRavg = None
            if self.PhidgetIRSensor and self.PhidgetIRSensor.getAttached():
                res = -1
                ambient = -1
                try:
                    if (deviceType == DeviceID.PHIDID_1045 and self.aw.qmc.phidget1045_async) or \
                        (deviceType in [DeviceID.PHIDID_1051,DeviceID.PHIDID_TMP1100] and self.aw.qmc.phidget1048_async[0]) or \
                        (deviceType == DeviceID.PHIDID_TMP1200 and ((alternative_conf and self.aw.qmc.phidget1200_2_async) or self.aw.qmc.phidget1200_async)):
                        async_res = None
                        try:
                            #### lock shared resources #####
                            self.Phidget1045semaphore.acquire(1)
                            now = libtime.time()
                            start_of_interval = now-self.aw.qmc.delay/1000
                            # 1. just consider async readings taken within the previous sampling interval
                            # and associate them with the (arrivial) time since the begin of that interval
                            valid_readings = [(r,t - start_of_interval) for (r,t) in self.Phidget1045values if t > start_of_interval]
                            if len(valid_readings) > 0:
                                # 2. calculate the value
                                # we take the median of all valid_readings weighted by the time of arrival, preferrring newer readings
                                readings = [r for (r,t) in valid_readings]
                                weights = [t for (r,t) in valid_readings]
                                async_res = wquantiles.median(numpy.array(readings),numpy.array(weights))
                                # 3. consume old readings
                                self.Phidget1045values = []
                        except:
                            self.Phidget1045values = []
                        finally:
                            if self.Phidget1045semaphore.available() < 1:
                                self.Phidget1045semaphore.release(1)
                        if async_res is None:
                            if self.Phidget1045lastvalue == -1: # there is no last value yet, we take a sync value
                                probe = self.PhidgetIRSensor.getTemperature()
                                self.Phidget1045lastvalue = self.PhidgetIRSensor.getTemperature()
                            else:
                                probe = self.Phidget1045lastvalue
                        else:
                            self.Phidget1045lastvalue = async_res
                            probe = async_res
                    else:
                        probe = self.PhidgetIRSensor.getTemperature()
                    if self.aw.qmc.mode == "F":
                        probe = fromCtoF(probe)
                    res = probe
                except Exception:
                    pass
                try:
                    if self.PhidgetIRSensorIC is not None and self.PhidgetIRSensorIC.getAttached():
                        ambient = self.PhidgetIRSensorIC.getTemperature()
                        # we heavily average this ambient temperature IC readings not to introduce additional noise via emissivity calc to the IR reading
                        if self.Phidget1045tempIRavg is None:
                            self.Phidget1045tempIRavg = ambient
                        else:
                            self.Phidget1045tempIRavg = (20*self.Phidget1045tempIRavg + ambient) / 21.0
                            ambient = self.Phidget1045tempIRavg
                        if self.aw.qmc.mode == "F":
                            ambient = fromCtoF(ambient)
                except Exception:
                    pass
                if deviceType == DeviceID.PHIDID_TMP1200:
                    ambient = res
                if ambient == -1:
                    return -1,-1
                else:
                    if deviceType == DeviceID.PHIDID_1045:
                        return self.IRtemp(self.aw.qmc.phidget1045_emissivity,res,ambient),ambient
                    else:
                        return res,ambient
            elif retry:
                libtime.sleep(0.1)
                return self.PHIDGET1045temperature(deviceType,retry=False,alternative_conf=alternative_conf)
            else:
                return -1,-1
        except Exception as ex:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            try:
                if self.PhidgetIRSensor and self.PhidgetIRSensor.getAttached():
                    self.PhidgetIRSensor.close()
                if self.PhidgetIRSensorIC and self.PhidgetIRSensorIC.getAttached():
                    self.PhidgetIRSensorIC.close()
            except Exception:
                pass
            self.PhidgetIRSensor = None
            self.Phidget1045values = []
            self.Phidget1045lastvalue = -1
            self.PhidgetIRSensorIC = None
            self.Phidget1045tempIRavg = None
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " PHIDGET1045temperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            return -1,-1

#----

    def phidget1048TemperatureChanged(self,t,channel):
        try:
            #### lock shared resources #####
            self.Phidget1048semaphores[channel].acquire(1)
            self.Phidget1048values[channel].append((t,libtime.time()))
        finally:
            if self.Phidget1048semaphores[channel].available() < 1:
                self.Phidget1048semaphores[channel].release(1)

    def phidget1048getSensorReading(self,channel,idx):
        if self.aw.qmc.phidget1048_async[channel]:
            res = None
            try:
                #### lock shared resources #####
                self.Phidget1048semaphores[channel].acquire(1)
                
                now = libtime.time()
                start_of_interval = now-self.aw.qmc.delay/1000
                # 1. just consider async readings taken within the previous sampling interval
                # and associate them with the (arrivial) time since the begin of that interval
                valid_readings = [(r,t - start_of_interval) for (r,t) in self.Phidget1048values[channel] if t > start_of_interval]
                if len(valid_readings) > 0:
                    # 2. calculate the value
                    # we take the median of all valid_readings weighted by the time of arrival, preferrring newer readings
                    readings = [r for (r,t) in valid_readings]
                    weights = [t for (r,t) in valid_readings]
                    res = wquantiles.median(numpy.array(readings),numpy.array(weights))
#                    res = numpy.median(numpy.array(readings))
                    # 3. consume old readings
                    self.Phidget1048values[channel] = []                
                
#                if len(self.Phidget1048values[channel]) > 0:
##                    res = numpy.average(self.Phidget1048values[channel])
#                    res = numpy.median(self.Phidget1048values[channel])
#                    
##                    data = self.Phidget1048values[channel]
##                    data_mean, data_std = numpy.mean(data), numpy.std(data)
##                    if data_std > 0:
##                        cut_off = data_std * 0.9
##                        lower, upper = data_mean - cut_off, data_mean + cut_off
##                        outliers_removed = [x for x in data if x > lower and x < upper]
##                        if len(outliers_removed) < 3:
##                            outliers_removed = data
##                    else:
##                        outliers_removed = data
##                    res = numpy.average(outliers_removed)
#
#                    self.Phidget1048values[channel] = self.Phidget1048values[channel][-round((self.aw.qmc.delay/self.aw.qmc.phidget1048_dataRate)):]
            except:
                self.Phidget1048values[channel] = []
            finally:
                if self.Phidget1048semaphores[channel].available() < 1:
                    self.Phidget1048semaphores[channel].release(1)
            if res is None:
                if self.Phidget1048lastvalues[channel] == -1: # there is no last value yet, we take a sync value
                    res = self.PhidgetTemperatureSensor[idx].getTemperature()
                    self.Phidget1048lastvalues[channel] = res
                    return res
                else:
                    return self.Phidget1048lastvalues[channel] # return the previous result
            else:
                self.Phidget1048lastvalues[channel] = res
                return res
        else:
            return self.PhidgetTemperatureSensor[idx].getTemperature()
    
    # each channel is configured separately
    def configure1048(self,idx):
        if self.PhidgetTemperatureSensor and len(self.PhidgetTemperatureSensor) > idx:
            # reset async values
            channel = self.PhidgetTemperatureSensor[idx].getChannel()
            if channel < 4: # the ambient temperature sensor does not need to be configured
                # set probe type
                self.PhidgetTemperatureSensor[idx].setThermocoupleType(PHIDGET_THERMOCOUPLE_TYPE(self.aw.qmc.phidget1048_types[channel]))
                # set rate
                try:
                    self.PhidgetTemperatureSensor[idx].setDataInterval(self.aw.qmc.phidget1048_dataRate)
                except Exception:
                    pass
                # set change trigger
                try:
                    if self.aw.qmc.phidget1048_async[channel]:
                        self.PhidgetTemperatureSensor[idx].setTemperatureChangeTrigger(self.aw.qmc.phidget1048_changeTriggers[channel])
                        self.PhidgetTemperatureSensor[idx].setOnTemperatureChangeHandler(lambda _,t: self.phidget1048TemperatureChanged(t,channel))
                    else:
                        self.PhidgetTemperatureSensor[idx].setTemperatureChangeTrigger(0)
                        self.PhidgetTemperatureSensor[idx].setOnTemperatureChangeHandler(lambda *_:None)
                except:
                    pass
                self.Phidget1048values[channel] = []
                self.Phidget1048lastvalues[channel] = -1

    def phidget1048attached(self,serial,port,deviceType,idx):
        try:
            self.configure1048(idx)
            if self.PhidgetTemperatureSensor is not None and len(self.PhidgetTemperatureSensor) > idx:
                channel = self.PhidgetTemperatureSensor[idx].getChannel()
                self.aw.qmc.phidgetManager.reserveSerialPort(serial,port,channel,"PhidgetTemperatureSensor",deviceType,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                if channel == 0:
                    self.aw.sendmessage(QApplication.translate("Message","Phidget Temperature Sensor 4-input attached",None))
        except:
            pass
        
    def phidget1048detached(self,serial,port,deviceType,idx):
        try:
            if self.PhidgetTemperatureSensor is not None and len(self.PhidgetTemperatureSensor) > idx:
                channel = self.PhidgetTemperatureSensor[idx].getChannel()
                self.aw.qmc.phidgetManager.releaseSerialPort(serial,port,channel,"PhidgetTemperatureSensor",deviceType,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                if channel == 0:
                    self.aw.sendmessage(QApplication.translate("Message","Phidget Temperature Sensor 4-input detached",None))
        except:
            pass

    # mode = 0 for probe 1 and 2; mode = 1 for probe 3 and 4; mode 2 for Ambient Temperature
    # works for the 4xTC USB_Phidget 1048 and the 4xTC VINT Phidget TMP1101
    def PHIDGET1048temperature(self,deviceType=DeviceID.PHIDID_1048,mode=0,retry=True):
        try:
            if not self.PhidgetTemperatureSensor and self.aw.qmc.phidgetManager is not None:
                ser = None
                port = None 
                if mode == 0:
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetTemperatureSensor',deviceType,0,
                        remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                # in all other cases, we check for existing serial/port pairs from attaching the main channels 1+2 of the device
                elif mode == 1: 
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetTemperatureSensor',deviceType,2,
                        remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                elif mode == 2:
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetTemperatureSensor',deviceType,4,
                        remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                if ser:
                    self.PhidgetTemperatureSensor = [PhidgetTemperatureSensor()]
                    if mode != 2:
                        self.PhidgetTemperatureSensor.append(PhidgetTemperatureSensor())
                    try:
                        self.PhidgetTemperatureSensor[0].setOnAttachHandler(lambda _:self.phidget1048attached(ser,port,deviceType,0))
                        self.PhidgetTemperatureSensor[0].setOnDetachHandler(lambda _:self.phidget1048detached(ser,port,deviceType,0))
                        if mode != 2:                            
                            self.PhidgetTemperatureSensor[1].setOnAttachHandler(lambda _:self.phidget1048attached(ser,port,deviceType,1))
                            self.PhidgetTemperatureSensor[1].setOnDetachHandler(lambda _:self.phidget1048detached(ser,port,deviceType,1))
                        if self.aw.qmc.phidgetRemoteFlag:
                            self.addPhidgetServer()
                        if port is not None:
                            self.PhidgetTemperatureSensor[0].setHubPort(port)
                            if mode != 2:
                                self.PhidgetTemperatureSensor[1].setHubPort(port)
                        self.PhidgetTemperatureSensor[0].setDeviceSerialNumber(ser)
                        self.PhidgetTemperatureSensor[0].setChannel(mode*2)
                        if self.aw.qmc.phidgetRemoteFlag and self.aw.qmc.phidgetRemoteOnlyFlag:
                            self.PhidgetTemperatureSensor[0].setIsRemote(True)
                            self.PhidgetTemperatureSensor[0].setIsLocal(False)
                        try:
                            self.PhidgetTemperatureSensor[0].open() #.openWaitForAttachment(timeout)
                        except:
                            pass
                        if mode != 2:
                            self.PhidgetTemperatureSensor[1].setDeviceSerialNumber(ser)
                            self.PhidgetTemperatureSensor[1].setChannel(mode*2 + 1)
                            if self.aw.qmc.phidgetRemoteFlag and self.aw.qmc.phidgetRemoteOnlyFlag:
                                self.PhidgetTemperatureSensor[1].setIsRemote(True)
                                self.PhidgetTemperatureSensor[1].setIsLocal(False)
                            try:
                                self.PhidgetTemperatureSensor[1].open() # .openWaitForAttachment(timeout)
                            except:
                                pass
                        # we need to give this device a bit time to attach, otherwise it will be considered for another Artisan channel of the same type
                        if self.aw.qmc.phidgetRemoteOnlyFlag:
                            libtime.sleep(.8)
                        else:
                            libtime.sleep(.5)
                    except Exception as ex:
                        #_, _, exc_tb = sys.exc_info()
                        #self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " PHIDGET1048temperature() {0}").format(str(ex)),exc_tb.tb_lineno)
                        try:
                            if self.PhidgetTemperatureSensor and self.PhidgetTemperatureSensor[0].getAttached():
                                self.PhidgetTemperatureSensor[0].close()
                            if mode != 2 and self.PhidgetTemperatureSensor and len(self.PhidgetTemperatureSensor)> 1 and self.PhidgetTemperatureSensor[1].getAttached():
                                self.PhidgetTemperatureSensor[1].close()
                        except Exception:
                            pass
                        self.Phidget1048values = [[],[],[],[]]
                        self.Phidget1048lastvalues = [-1]*4
                        self.PhidgetTemperatureSensor = None
            if self.PhidgetTemperatureSensor and ((mode == 2) or (len(self.PhidgetTemperatureSensor)>1 and self.PhidgetTemperatureSensor[0].getAttached() and self.PhidgetTemperatureSensor[1].getAttached())):
                # now just harvest both temps (or one in case type is 2)
                if mode in [0,1]:
                    probe1 = probe2 = -1
                    try:
                        probe1 = self.phidget1048getSensorReading(mode*2,0)
                        if self.aw.qmc.mode == "F":
                            probe1 = fromCtoF(probe1)
                    except Exception:
                        pass
                    try:
                        probe2 = self.phidget1048getSensorReading(mode*2 + 1,1)
                        if self.aw.qmc.mode == "F":
                            probe2 = fromCtoF(probe2)
                    except Exception:
                        pass
                    return probe1, probe2
                elif mode == 2:
                    try:
                        at = self.PhidgetTemperatureSensor[0].getTemperature()
                        if self.aw.qmc.mode == "F":
                            at = fromCtoF(at)
                        return at,-1
                    except Exception:
                        return -1,-1
                else:
                    return -1,-1
            elif retry:
                libtime.sleep(0.1)
                return self.PHIDGET1048temperature(deviceType,mode,False)
            else:
                return -1,-1
        except Exception as ex:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            try:
                if self.PhidgetTemperatureSensor and self.PhidgetTemperatureSensor[0].getAttached():
                    self.PhidgetTemperatureSensor[0].close()
                if mode != 2 and self.PhidgetTemperatureSensor and len(self.PhidgetTemperatureSensor)>1 and self.PhidgetTemperatureSensor[1].getAttached():
                    self.PhidgetTemperatureSensor[1].close()
            except Exception:
                pass
            self.Phidget1048values = [[],[],[],[]]
            self.Phidget1048lastvalues = [-1]*4
            self.PhidgetTemperatureSensor = None
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " PHIDGET1048temperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            return -1,-1

#--- code for the Phidgets 1046

    # takes a bridge value in mV/V and returns the resistance of the corresponding RTD, assuming the RTD is connected
    # via a Wheatstone Bridge build from 1K ohm resistors
    # http://en.wikipedia.org/wiki/Wheatstone_bridge
    # Note: the 1046 returns the bridge value in mV/V
    def R_RTD_WS(self,bv):
        return (1000 * (1000 - 2 * bv))/(1000 + 2 * bv)
    
    # takes a bridge value in mV/V and returns the resistance of the corresponding RTD, assuming the RTD is connected
    # via a Voltage Divider build from 1K ohm resistors
    # http://en.wikipedia.org/wiki/Voltage_divider
    # Note: the 1046 returns the bridge value in mV/V
    def R_RTD_DIV(self,bv):
        return (2000 * bv) / (1000 - bv)
        
    # this formula results from a direct mathematical linearization of the Callendar-Van Dusen equation
    # see Analog Devices Application Note AN-709 http://www.analog.com/static/imported-files/application_notes/AN709_0.pdf
    # Wikipedia http://en.wikipedia.org/wiki/Resistance_thermometer
    #  or http://www.abmh.de
    def rRTD2PT100temp(self,R_RTD):
        Z1 = -3.9083e-03
        Z2 = 1.76e-05
        Z3 = -2.31e-08
        Z4 = -1.155e-06
        try:
            return (Z1 + math.sqrt(abs(Z2 + (Z3 * R_RTD))))/Z4
        except Exception:
            return -1

    # convert the BridgeValue given by the PhidgetBridge to a temperature value assuming a PT100 probe
    # see http://www.phidgets.com/docs/3175_User_Guide
    # this one is a simpler and less accurate approximation as above that directly gives the temperature for a given bridge value in mV/V,
    # that works only for the Voltage Divider case
#    def bridgeValue2PT100(self,bv):
#        bvf = bv / (1000 - bv)
#        return 4750.3 * bvf * bvf + 4615.6 * bvf - 242.615

    def phidget1046TemperatureChanged(self,v,channel):
        try:
            #### lock shared resources #####
            self.Phidget1046semaphores[channel].acquire(1)
            temp = self.bridgeValue2Temperature(channel,v*1000) # Note in Phidgets API v22 this factor 1000 has to be added
            if self.aw.qmc.mode == "F" and self.aw.qmc.phidget1046_formula[channel] != 2:
                temp = fromCtoF(temp)
            self.Phidget1046values[channel].append((temp,libtime.time()))
        finally:
            if self.Phidget1046semaphores[channel].available() < 1:
                self.Phidget1046semaphores[channel].release(1)

    def bridgeValue2Temperature(self,i,bv):
        v = -1
        try:
            if self.aw.qmc.phidget1046_formula[i] == 0:
                v = self.rRTD2PT100temp(self.R_RTD_WS(abs(bv)))  # we add the abs() here to support inverted wirings
            elif self.aw.qmc.phidget1046_formula[i] == 1:
                v = self.rRTD2PT100temp(self.R_RTD_DIV(abs(bv)))  # we add the abs() here to support inverted wirings
            elif self.aw.qmc.phidget1046_formula[i] == 2:
                v = bv # no abs() for raw values
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:",None) + " bridgeValue2Temperature(): {0}").format(str(e)),exc_tb.tb_lineno)            
        return v

    def phidget1046getTemperature(self,i,idx):
        v = -1
        try:
            bv = self.PhidgetBridgeSensor[idx].getVoltageRatio() * 1000 # Note in Phidgets API v22 this factor 1000 has to be added
            
# test values for the bridge value to temperature conversion
#            bv = 51.77844 # about room temperature for Voltage Divider wiring
#            bv = 400.2949 # about room temperature for Wheatstone Bridge

            v = self.bridgeValue2Temperature(i,bv)
            if self.aw.qmc.mode == "F" and self.aw.qmc.phidget1046_formula[i] != 2:
                v = fromCtoF(v)
        except:
            v = -1
        return v
                        
    def phidget1046getSensorReading(self,channel,idx):
        if self.aw.qmc.phidget1046_async[channel]:
            res = None
            try:
                #### lock shared resources #####
                self.Phidget1046semaphores[channel].acquire(1)
                now = libtime.time()
                start_of_interval = now-self.aw.qmc.delay/1000
                # 1. just consider async readings taken within the previous sampling interval
                # and associate them with the (arrivial) time since the begin of that interval
                valid_readings = [(r,t - start_of_interval) for (r,t) in self.Phidget1046values[channel] if t > start_of_interval]
                if len(valid_readings) > 0:
                    # 2. calculate the value
                    # we take the median of all valid_readings weighted by the time of arrival, preferrring newer readings
                    readings = [r for (r,t) in valid_readings]
                    weights = [t for (r,t) in valid_readings]
                    res = wquantiles.median(numpy.array(readings),numpy.array(weights))
                    # 3. consume old readings
                    self.Phidget1046values[channel] = []
                                                
#                if len(self.Phidget1046values[channel]) > 0:
##                    res = numpy.average(self.Phidget1046values[channel])
#                    res = numpy.median(self.Phidget1046values[channel])
#                    self.Phidget1046values[channel] = self.Phidget1046values[channel][-round((self.aw.qmc.delay/self.aw.qmc.phidget1046_dataRate)):] 
            except:
                self.Phidget1046values[channel] = []
            finally:
                if self.Phidget1046semaphores[channel].available() < 1:
                    self.Phidget1046semaphores[channel].release(1)
            if res is None:
                if self.Phidget1046lastvalues[channel] == -1: # there is no last value yet, we take a sync value
                    res = self.phidget1046getTemperature(channel,idx)
                    self.Phidget1046lastvalues[channel] = res
                    return res
                else:
                    return self.Phidget1046lastvalues[channel]
            else:
                self.Phidget1046lastvalues[channel] = res
                return res
        else:
            return self.phidget1046getTemperature(channel,idx)

    def configure1046(self,idx):
        if self.PhidgetBridgeSensor and len(self.PhidgetBridgeSensor) > idx:
            channel = self.PhidgetBridgeSensor[idx].getChannel()
            if channel < 4:
                # set gain
                try:
                    self.PhidgetBridgeSensor[idx].setBridgeGain(PHIDGET_GAIN_VALUE(self.aw.qmc.phidget1046_gain[channel]))
                except Exception:
                    pass
                # set rate
                try:
                    self.PhidgetBridgeSensor[idx].setDataInterval(self.aw.qmc.phidget1046_dataRate)
                except Exception:
                    pass
                # set voltage ratio change trigger to 0 (fire every DataInterval)
                try:
                    self.PhidgetBridgeSensor[idx].setVoltageChangeTrigger(0)
                except Exception:
                    pass
                # enable channel
                try:
                    self.PhidgetBridgeSensor[idx].setBridgeEnabled(channel, True)
                except Exception:
                    pass
                if self.aw.qmc.phidget1046_async[channel]:
                    self.PhidgetBridgeSensor[idx].setOnVoltageRatioChangeHandler(lambda _,v:self.phidget1046TemperatureChanged(v,channel))
                else:
                    self.PhidgetBridgeSensor[idx].setOnVoltageRatioChangeHandler(lambda *_:None)
                # reset async value
                self.Phidget1046values[channel] = []
                self.Phidget1046lastvalues[channel] = -1

    def phidget1046attached(self,serial,port,deviceType,idx):
        try:
            self.configure1046(idx)
            if self.PhidgetBridgeSensor is not None:
                channel = self.PhidgetBridgeSensor[idx].getChannel()
                self.aw.qmc.phidgetManager.reserveSerialPort(serial,port,channel,"PhidgetVoltageRatioInput",deviceType,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                if channel == 0:
                    self.aw.sendmessage(QApplication.translate("Message","Phidget Bridge 4-input attached",None))
        except:
            pass
        
    def phidget1046detached(self,serial,port,deviceType,idx):
        try:
            if self.PhidgetBridgeSensor is not None:
                channel = self.PhidgetBridgeSensor[idx].getChannel()
                self.aw.qmc.phidgetManager.releaseSerialPort(serial,port,channel,"PhidgetVoltageRatioInput",deviceType,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                if channel == 0:
                    self.aw.sendmessage(QApplication.translate("Message","Phidget Bridge 4-input detached",None))
        except:
            pass

    # mode = 0 for probe 1 and 2; mode = 1 for probe 3 and 4
    def PHIDGET1046temperature(self,mode=0,retry=True):
        try:
            if not self.PhidgetBridgeSensor and self.aw.qmc.phidgetManager is not None:
                ser = None
                port = None 
                if mode == 0:
                    # we scan for available main device
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetVoltageRatioInput',DeviceID.PHIDID_1046,0,
                        remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                # in all other cases, we check for existing serial/port pairs from attaching the main channels 1+2 of the device
                elif mode == 1:
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetVoltageRatioInput',DeviceID.PHIDID_1046,2,
                        remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                if ser:
                    self.PhidgetBridgeSensor = [VoltageRatioInput(),VoltageRatioInput()]
                
                    try:
                        for i in [0,1]:
                            if self.aw.qmc.phidgetRemoteFlag:
                                self.addPhidgetServer()
                            if port is not None:
                                self.PhidgetBridgeSensor[i].setHubPort(port)
                            self.PhidgetBridgeSensor[i].setDeviceSerialNumber(ser)
                            self.PhidgetBridgeSensor[i].setChannel(mode*2+i)
                            if self.aw.qmc.phidgetRemoteFlag and self.aw.qmc.phidgetRemoteOnlyFlag:
                                self.PhidgetBridgeSensor[i].setIsRemote(True)
                                self.PhidgetBridgeSensor[i].setIsLocal(False)
                            self.PhidgetBridgeSensor[i].setOnAttachHandler(lambda _,x=i:self.phidget1046attached(ser,port,DeviceID.PHIDID_1046,x))
                            self.PhidgetBridgeSensor[i].setOnDetachHandler(lambda _,x=i:self.phidget1046detached(ser,port,DeviceID.PHIDID_1046,x))
                            libtime.sleep(.1)
                            try:
                                self.PhidgetBridgeSensor[i].open() #.openWaitForAttachment(timeout)
                            except:
                                pass
                        # we need to give this device a bit time to attach, otherwise it will be considered for another Artisan channel of the same type
                        if self.aw.qmc.phidgetRemoteOnlyFlag:
                            libtime.sleep(.8)
                        else:
                            libtime.sleep(.5)
                    except Exception as ex:
                        #_, _, exc_tb = sys.exc_info()
                        #self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " PHIDGET1046temperature() {0}").format(str(ex)),exc_tb.tb_lineno)
                        try:
                            if self.PhidgetBridgeSensor and self.PhidgetBridgeSensor[0].getAttached():
                                self.PhidgetBridgeSensor[0].close()
                            if self.PhidgetBridgeSensor and len(self.PhidgetBridgeSensor)>1 and self.PhidgetBridgeSensor[1].getAttached():
                                self.PhidgetBridgeSensor[1].close()
                        except Exception:
                            pass
                        self.Phidget1046values = [[],[],[],[]]
                        self.Phidget1046lastvalues = [-1]*4
                        self.PhidgetBridgeSensor = None
            if self.PhidgetBridgeSensor and len(self.PhidgetBridgeSensor) == 2 and self.PhidgetBridgeSensor[0].getAttached() and self.PhidgetBridgeSensor[1].getAttached():
                if mode in [0,1]:
                    probe1 = probe2 = -1
                    try:
                        probe1 = self.phidget1046getSensorReading(mode*2,0)
                    except Exception:
                        pass
                    try:
                        probe2 = self.phidget1046getSensorReading(mode*2+1,1)
                    except Exception:
                        pass
                    return probe1, probe2
                else:
                    return -1,-1
            elif retry:
                libtime.sleep(0.1)
                return self.PHIDGET1046temperature(mode,False)
            else:
                return -1,-1
        except Exception as ex:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            try:
                if self.PhidgetBridgeSensor and self.PhidgetBridgeSensor[0].getAttached():
                    self.PhidgetBridgeSensor[0].close()
                if self.PhidgetBridgeSensor and len(self.PhidgetBridgeSensor)>1 and self.PhidgetBridgeSensor[1].getAttached():
                    self.PhidgetBridgeSensor[1].close()
            except Exception:
                pass
            self.Phidget1046values = [[],[],[],[]]
            self.Phidget1046lastvalues = [-1]*4
            self.PhidgetBridgeSensor = None
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " PHIDGET1046temperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            return -1,-1

    # takes a string of the form "<serial>[:<hubport>]" or None and returns serial and hubport numbers
    def serialString2serialPort(self,serial):
        if serial is None:
            return None, None
        else:
            serial_split = serial.split(":")
            s = None
            p = None
            try:
                s = int(serial_split[0])
            except:
                pass
            try:
                p = int(serial_split[1])
            except:
                pass
            return s,p
            
    # takes serial and hubport as integers and returns the composed serial string
    def serialPort2serialString(self,serial,port):
        if serial is None and port is None:
            return None
        elif port is None:
            return str(serial)
        else:
            return str(serial) + ":" + str(port)
    
    def phidgetOUTattached(self,ch):
        self.aw.qmc.phidgetManager.reserveSerialPort(
            ch.getDeviceSerialNumber(), # serial
            ch.getHubPort(), # port
            ch.getChannel(), # channel
            ch.getChannelClassName(), # phidget_class_name
            ch.getDeviceID(), # device_id
            remote=self.aw.qmc.phidgetRemoteFlag,
            remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
    
    def phidgetOUTdetached(self,ch):
        self.aw.qmc.phidgetManager.releaseSerialPort(
            ch.getDeviceSerialNumber(), # serial
            ch.getHubPort(), # port
            ch.getChannel(), # channel
            ch.getChannelClassName(), # phidget_class_name
            ch.getDeviceID(), # device_id
            remote=self.aw.qmc.phidgetRemoteFlag,
            remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)

#--- Phidget IO Binay Output
#  only supporting (trying to attach in this order)
#      4 channel Phidget 1014, OUT1100, REL1000, REL1100, REL1101
#      8 channel Phidget 1017
#      8 channel Phidget 1010, 1013, 1018, 1019 modules
#  commands: set(n,0), set(n,1), toggle(n) with n channel number

    # serial: optional Phidget HUB serial number with optional port number as string of the form "<serial>[:<port>]"
    def phidgetBinaryOUTattach(self,channel,serial=None):
        if not serial in self.aw.ser.PhidgetBinaryOut:
            if self.aw.qmc.phidgetManager is None:
                self.aw.qmc.startPhidgetManager()
            if self.aw.qmc.phidgetManager is not None:
                ser = None
                s,p = self.serialString2serialPort(serial)
                for phidget_id in [DeviceID.PHIDID_1014,DeviceID.PHIDID_OUT1100,DeviceID.PHIDID_REL1000,DeviceID.PHIDID_REL1100]:
                    if ser is None:
                        ser,_ = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetDigitalOutput',phidget_id,channel,
                                remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                ports = 4
                if ser is None:
                    ser,_ = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetDigitalOutput',DeviceID.PHIDID_1017,
                                remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                    ports = 8
                # try to attach up to 8 IO channels of the first Phidget 1010, 1013, 1018, 1019 module
                if ser is None:
                    ser,_ = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetDigitalOutput',DeviceID.PHIDID_1010_1013_1018_1019,
                                remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                    ports = 8
                # try to attach up to 16 IO channels of the first Phidget REL1101 module
                if ser is None:
                    ser,_ = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetDigitalOutput',DeviceID.PHIDID_REL1100,
                                remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                    ports = 16
                if ser is not None:
                    self.aw.ser.PhidgetBinaryOut[serial] = []
                    for i in range(ports):
                        do = DigitalOutput()
                        do.setChannel(i)
                        do.setDeviceSerialNumber(ser)
                        if self.aw.qmc.phidgetRemoteFlag:
                            do.setIsRemote(True)
                            do.setIsLocal(False)
                        elif not self.aw.qmc.phidgetRemoteFlag:
                            do.setIsRemote(False)
                            do.setIsLocal(True)
                        self.aw.ser.PhidgetBinaryOut[serial].append(do)
                    if serial is None:
                        # we make this also accessible via its serial number
                        self.aw.ser.PhidgetBinaryOut[str(ser)] = self.aw.ser.PhidgetBinaryOut[None]
        try:
            ch = self.aw.ser.PhidgetBinaryOut[serial][channel]
            ch.setOnAttachHandler(self.phidgetOUTattached)
            ch.setOnDetachHandler(self.phidgetOUTdetached)
            if not ch.getAttached():
                if self.aw.qmc.phidgetRemoteFlag:
                    ch.openWaitForAttachment(3000)
                else:
                    ch.openWaitForAttachment(1000)
                if serial is None and ch.getAttached():
                    # we make this also accessible via its serial number + port
                    s = self.serialPort2serialString(ch.getDeviceSerialNumber(),ch.getHubPort()) # NOTE: ch.getHubPort() returns -1 if not yet attached
                    self.aw.ser.PhidgetBinaryOut[s] = self.aw.ser.PhidgetBinaryOut[None]
        except:
            pass

    def phidgetBinaryOUTpulse(self,channel,millis,serial=None):
        self.phidgetBinaryOUTset(channel,1,serial)
#        QTimer.singleShot(int(round(millis)),lambda : self.phidgetBinaryOUTset(channel,0))
        # QTimer (which does not work being called from a QThread) call replaced by the next 2 lines (event actions are now started in an extra thread)
        # the following solution has the drawback to block the eventaction thread
#        libtime.sleep(millis/1000.)
#        self.phidgetBinaryOUTset(channel,0)
        # so we use a QTimer.singleShot running in the main thread
        if serial is None:
            self.aw.singleShotPhidgetsPulseOFF.emit(channel,millis,"BinaryOUTset")
        else:
            self.aw.singleShotPhidgetsPulseOFFSerial.emit(channel,millis,"BinaryOUTset",serial)

    # value: True or False
    def phidgetBinaryOUTset(self,channel,value,serial=None):
        res = False
        self.phidgetBinaryOUTattach(channel,serial)
        if serial in self.aw.ser.PhidgetBinaryOut:
            # set state of the given channel
            out = self.aw.ser.PhidgetBinaryOut[serial]
            try:
                if len(out) > channel and out[channel] and out[channel].getAttached():
                    out[channel].setState(value)
                    res = True
            except:
                res = False
        return res

    # returns: True or False (default)
    def phidgetBinaryOUTget(self,channel,serial=None):
        self.phidgetBinaryOUTattach(channel,serial)
        res = False
        if serial in self.aw.ser.PhidgetBinaryOut:
            # get state of the given channel
            out = self.aw.ser.PhidgetBinaryOut[serial]
            try:
                if len(out) > channel and out[channel] and out[channel].getAttached():
                    res = out[channel].getState()
            except:
                pass
        return res
    
    def phidgetBinaryOUTtoggle(self,channel,serial=None):
        self.phidgetBinaryOUTset(channel,not self.phidgetBinaryOUTget(channel,serial),serial)
        
    def phidgetBinaryOUTclose(self):
        for o in self.aw.ser.PhidgetBinaryOut:
            out = self.aw.ser.PhidgetBinaryOut[o]
            if out is not None:
                for i in range(len(out)):
                    try:
                        if out[i].getAttached():
                            self.phidgetOUTdetached(out[i])
                        out[i].close()
                    except Exception:
                        pass
        self.aw.ser.PhidgetBinaryOut = {}
    
    
#--- Phidget Digital PWM Output
#  only supporting 
#           4 channel Phidget OUT1100, REL1100
#          16 channel Phidget REL1101
#  commands: out(n,v) and toggle(n) with n channel number and value v from [0-100]
#    toggle switches between last value != 0 and 0

    # serial: optional Phidget HUB serial number with optional port number as string of the form "<serial>[:<port>]"
    def phidgetOUTattach(self,channel,serial=None):
        if not serial in self.aw.ser.PhidgetDigitalOut:
            if self.aw.qmc.phidgetManager is None:
                self.aw.qmc.startPhidgetManager()
            if self.aw.qmc.phidgetManager is not None:
                # try to attach the 4 channels of the Phidget OUT1100 module
                ser = None
                s,p = self.serialString2serialPort(serial)
                port = None
                for phidget_id in [DeviceID.PHIDID_OUT1100,DeviceID.PHIDID_REL1100]:
                    if ser is None:
                        ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetDigitalOutput',phidget_id,channel,
                                remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                    else:
                        break
                ports = 4
                if ser is None:
                    ports = 16
                    for phidget_id in [DeviceID.PHIDID_REL1101]:
                        if ser is None:
                            ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetDigitalOutput',phidget_id,channel,
                                    remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                        else:
                            break
                if ser is not None:
                    self.aw.ser.PhidgetDigitalOut[serial] = []
                    self.aw.ser.PhidgetDigitalOutLastPWM[serial] = [0]*ports # 0-100
                    self.aw.ser.PhidgetDigitalOutLastToggle[serial] = [None]*ports
                    for i in range(ports):
                        do = DigitalOutput()
                        if port is not None:
                            do.setHubPort(port)
                        do.setChannel(i)
                        do.setDeviceSerialNumber(ser)
                        if self.aw.qmc.phidgetRemoteFlag and self.aw.qmc.phidgetRemoteOnlyFlag:
                            do.setIsRemote(True)
                            do.setIsLocal(False)
                        elif not self.aw.qmc.phidgetRemoteFlag:
                            do.setIsRemote(False)
                            do.setIsLocal(True)
                        self.aw.ser.PhidgetDigitalOut[serial].append(do)
                    if serial is None:
                        # we make this also accessible via its serial number
                        self.aw.ser.PhidgetDigitalOut[str(ser)] = self.aw.ser.PhidgetDigitalOut[None]
        try:
            ch = self.aw.ser.PhidgetDigitalOut[serial][channel]
            if not ch.getAttached():
                ch.setOnAttachHandler(self.phidgetOUTattached)
                ch.setOnDetachHandler(self.phidgetOUTdetached)
                if self.aw.qmc.phidgetRemoteFlag:
                    ch.openWaitForAttachment(3000)
                else:
                    ch.openWaitForAttachment(1200)
                if serial is None and ch.getAttached():
                    # we make this also accessible via its serial number + port
                    s = self.serialPort2serialString(ch.getDeviceSerialNumber(),ch.getHubPort())
                    self.aw.ser.PhidgetDigitalOut[s] = self.aw.ser.PhidgetDigitalOut[None]
        except:
            pass

    def phidgetOUTtogglePWM(self,channel,serial=None):
        self.phidgetOUTattach(channel,serial) # this is to ensure that the lastToggle/lastPWM structures are allocated
        if serial in self.aw.ser.PhidgetDigitalOut:
            lastPWM = self.aw.ser.PhidgetDigitalOutLastPWM[serial][channel]
            lastToggle = self.aw.ser.PhidgetDigitalOutLastToggle[serial][channel]
            if lastPWM == 0:
                # we switch on
                if lastToggle is None:
                    self.phidgetOUTsetPWM(channel,100,serial)
                else:
                    # we have a lastPWM from before toggling off
                    self.phidgetOUTsetPWM(channel,lastToggle,serial)
            else:
                # we switch off
                self.phidgetOUTsetPWM(channel,0,serial)
                self.aw.ser.PhidgetDigitalOutLastToggle[serial][channel] = lastPWM # remember lastPWM to be able to switch on again
                if serial is None:
                    # also establish for the entry with serial number
                    s = self.aw.ser.PhidgetDigitalOut[serial][channel].getDeviceSerialNumber()
                    ser = self.serialPort2serialString(s,self.aw.ser.PhidgetDigitalOut[serial][channel].getHubPort())
                    self.aw.ser.PhidgetDigitalOutLastToggle[ser][channel] = lastPWM # remember lastPWM to be able to switch on again
                    self.aw.ser.PhidgetDigitalOutLastToggle[str(s)][channel] = lastPWM # remember lastPWM to be able to switch on again
    
    def phidgetOUTpulsePWM(self,channel,millis,serial=None):
        self.phidgetOUTsetPWM(channel,100,serial)
#        QTimer.singleShot(int(round(millis)),lambda : self.phidgetOUTsetPWM(channel,0))
#        # QTimer (which does not work being called from a QThread) call replaced by the next 2 lines (event actions are now started in an extra thread)
        # the following solution has the drawback to block the eventaction thread
#        libtime.sleep(millis/1000.)
#        self.phidgetOUTsetPWM(channel,0)
        if serial is None:
            self.aw.singleShotPhidgetsPulseOFF.emit(channel,millis,"OUTsetPWM")
        else:
            self.aw.singleShotPhidgetsPulseOFFSerial.emit(channel,millis,"OUTsetPWM",serial)

    # value: 0-100
    def phidgetOUTsetPWM(self,channel,value,serial=None):
        self.phidgetOUTattach(channel,serial)
        if serial in self.aw.ser.PhidgetDigitalOut:
            out = self.aw.ser.PhidgetDigitalOut[serial]
            # set PWM of the given channel
            try:
                if len(out) > channel and out[channel].getAttached():
                    out[channel].setDutyCycle(value/100.)
                    self.aw.ser.PhidgetDigitalOutLastPWM[serial][channel] = value
                    self.aw.ser.PhidgetDigitalOutLastToggle[serial][channel] = None # clears the lastToggle value
                    if serial is None:
                        # also establish for the entry with serial number
                        s = out[channel].getDeviceSerialNumber()
                        sr = self.serialPort2serialString(s,out[channel].getHubPort())
                        self.aw.ser.PhidgetDigitalOutLastPWM[sr][channel] = value
                        self.aw.ser.PhidgetDigitalOutLastToggle[sr][channel] = None # clears the lastToggle value
                        self.aw.ser.PhidgetDigitalOutLastPWM[str(s)][channel] = value
                        self.aw.ser.PhidgetDigitalOutLastToggle[str(s)][channel] = None # clears the lastToggle value
            except Exception:
                pass

    # value: real
    def phidgetOUTsetPWMfrequency(self,channel,value,serial=None):
        self.phidgetOUTattach(channel,serial)
        if serial in self.aw.ser.PhidgetDigitalOut:
            out = self.aw.ser.PhidgetDigitalOut[serial]
            # set PWM frequency for all channels of the module
            try:
                v = max(100,min(20000,value))
                if len(out) > channel and out[channel].getAttached():
                    out[channel].setFrequency(v)
            except:
                pass

    def phidgetOUTclose(self):
        for m in self.aw.ser.PhidgetDigitalOut:
            out = self.aw.ser.PhidgetDigitalOut[m]
            if out is not None:
                for i in range(len(out)):
                    try:
                        if out[i].getAttached():
                            self.phidgetOUTdetached(out[i])
                        out[i].close()
                    except Exception:
                        pass
        self.aw.ser.PhidgetDigitalOut = {}
        self.aw.ser.PhidgetDigitalOutLastPWM = {}
        self.aw.ser.PhidgetDigitalOutLastToggle = {}


#--- Phidget Digital PWMhub Output
#  only supporting 6 channel Phidget HUB module

    # serial: optional Phidget HUB serial number with optional port number as string of the form "<serial>[:<port>]"
    def phidgetOUTattachHub(self,channel,serial=None):
        if not serial in self.aw.ser.PhidgetDigitalOutHub:
            if self.aw.qmc.phidgetManager is None:
                self.aw.qmc.startPhidgetManager()
            if self.aw.qmc.phidgetManager is not None:
                # try to attach the 6 channels of the Phidget HUB module
                s,p = self.serialString2serialPort(serial)
                ser,_ = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetDigitalOutput',DeviceID.PHIDID_DIGITALOUTPUT_PORT,channel,
                            remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                if ser is not None:
                    self.aw.ser.PhidgetDigitalOutHub[serial] = [DigitalOutput(),DigitalOutput(),DigitalOutput(),DigitalOutput(),DigitalOutput(),DigitalOutput()]
                    self.aw.ser.PhidgetDigitalOutLastPWMhub[serial] = [0]*6 # 0-100
                    self.aw.ser.PhidgetDigitalOutLastToggleHub[serial] = [None]*6
                    for i in range(6):
                        self.aw.ser.PhidgetDigitalOutHub[serial][i].setChannel(0)
                        self.aw.ser.PhidgetDigitalOutHub[serial][i].setHubPort(i)
                        self.aw.ser.PhidgetDigitalOutHub[serial][i].setDeviceSerialNumber(ser)
                        self.aw.ser.PhidgetDigitalOutHub[serial][i].setIsHubPortDevice(True)
                        if self.aw.qmc.phidgetRemoteFlag and self.aw.qmc.phidgetRemoteOnlyFlag:
                            self.aw.ser.PhidgetDigitalOutHub[serial][i].setIsRemote(True)
                            self.aw.ser.PhidgetDigitalOutHub[serial][i].setIsLocal(False)
                    if serial is None:
                        # we make this also accessible via its serial number
                        self.aw.ser.PhidgetDigitalOutHub[str(ser)] = self.aw.ser.PhidgetDigitalOutHub[None]
                        self.aw.ser.PhidgetDigitalOutLastPWMhub[str(ser)] = self.aw.ser.PhidgetDigitalOutLastPWMhub[None]
                        self.aw.ser.PhidgetDigitalOutLastToggleHub[str(ser)] = self.aw.ser.PhidgetDigitalOutLastToggleHub[None]
        try:
            ch = self.aw.ser.PhidgetDigitalOutHub[serial][channel]
            ch.setOnAttachHandler(self.phidgetOUTattached)
            ch.setOnDetachHandler(self.phidgetOUTdetached)
            if not ch.getAttached():
                if self.aw.qmc.phidgetRemoteFlag:
                    ch.openWaitForAttachment(3000)
                else:
                    ch.openWaitForAttachment(1000)
        except:
            pass
    
    def phidgetOUTtogglePWMhub(self,channel,serial=None):
        self.phidgetOUTattachHub(channel,serial) # this is to ensure that the lastToggle/lastPWM structures are allocated
        if serial in self.aw.ser.PhidgetDigitalOutHub:
            lastToggle = self.aw.ser.PhidgetDigitalOutLastToggleHub[serial][channel]
            lastPWM = self.aw.ser.PhidgetDigitalOutLastPWMhub[serial][channel]
            if lastPWM == 0:
                # we switch on
                if lastToggle is None:
                    self.phidgetOUTsetPWMhub(channel,100,serial)
                else:
                    # we have a lastPWM from before toggling off
                    self.phidgetOUTsetPWMhub(channel,lastToggle,serial)
            else:
                # we switch off
                self.phidgetOUTsetPWMhub(channel,0,serial)
                self.aw.ser.PhidgetDigitalOutLastToggleHub[serial][channel] = lastPWM # remember lastPWM to be able to switch on again
                if serial is None:
                    # also establish for the entry with serial number
                    ser = self.aw.ser.PhidgetDigitalOutHub[serial][channel].getDeviceSerialNumber()
                    self.aw.ser.PhidgetDigitalOutLastToggleHub[str(ser)][channel] = lastPWM # remember lastPWM to be able to switch on again
    

    def phidgetOUTpulsePWMhub(self,channel,millis,serial=None):
        self.phidgetOUTsetPWMhub(channel,100,serial)
#        QTimer.singleShot(int(round(millis)),lambda : self.phidgetOUTsetPWMhub(channel,0))
        # QTimer (which does not work being called from a QThread) call replaced by the next 2 lines (event actions are now started in an extra thread)
        # the following solution has the drawback to block the eventaction thread
#        libtime.sleep(millis/1000.)
#        self.phidgetOUTsetPWMhub(channel,0)
        if serial is None:
            self.aw.singleShotPhidgetsPulseOFF.emit(channel,millis,"OUTsetPWMhub")
        else:
            self.aw.singleShotPhidgetsPulseOFFSerial.emit(channel,millis,"OUTsetPWMhub",serial)
    
    # channel: 0-5
    # value: 0-100
    # serial: optional Phidget HUB serial number with optional port number as string of the form "<serial>[:<port>]"
    def phidgetOUTsetPWMhub(self,channel,value,serial=None):
        self.phidgetOUTattachHub(channel,serial)
        if serial in self.aw.ser.PhidgetDigitalOutHub:
            outHub = self.aw.ser.PhidgetDigitalOutHub[serial]
            # set PWM of the given channel
            try:
                if len(outHub) > channel and outHub[channel] and outHub[channel].getAttached():
                    outHub[channel].setDutyCycle(value/100.)
                    self.aw.ser.PhidgetDigitalOutLastPWMhub[serial][channel] = value
                    self.aw.ser.PhidgetDigitalOutLastToggleHub[serial][channel] = None # clears the lastToggle value
                    if serial is None:
                        # also establish for the entry with serial number
                        sr = outHub[channel].getDeviceSerialNumber()
                        self.aw.ser.PhidgetDigitalOutLastPWMhub[str(sr)][channel] = value
                        self.aw.ser.PhidgetDigitalOutLastToggleHub[str(sr)][channel] = None # clears the lastToggle value
            except:
                pass
    
    def phidgetOUTcloseHub(self):
        for h in self.aw.ser.PhidgetDigitalOutHub:
            outHub = self.aw.ser.PhidgetDigitalOutHub[h]
            if outHub is not None:
                for i in range(len(outHub)):
                    try:
                        if outHub[i].getAttached():
                            self.phidgetOUTdetached(outHub[i])
                        outHub[i].close()
                    except:
                        pass
        self.aw.ser.PhidgetDigitalOutHub = {}
        self.aw.ser.PhidgetDigitalOutLastPWMhub = {}
        self.aw.ser.PhidgetDigitalOutLastToggleHub = {}


#--- Phidget Analog Voltage Output
#  only supporting 
#     1 channel Phidget OUT1000, OUT1001 and OUT1002
#     4 channel USB Phidget 1002
#  commands:
#    out(n,v[,serial]) with n channel number and value v voltage in V as a float, and serial the optional serial/port number of the addressed module
#    range(n,r[,serial]) with n channel number and value r either 5 or 10 for voltage range 0-5V or -10 to 10V voltage range, and serial the optional serial/port number of the addressed module

    # serial: optional Phidget HUB serial number with optional port number as string of the form "<serial>[:<port>]"
    def phidgetVOUTattach(self,channel,serial):
        if not serial in self.aw.ser.PhidgetAnalogOut:
            if self.aw.qmc.phidgetManager is None:
                self.aw.qmc.startPhidgetManager()
            if self.aw.qmc.phidgetManager is not None:
                # try to attach the Phidget OUT100x module
                s,p = self.serialString2serialPort(serial)
                ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetVoltageOutput',DeviceID.PHIDID_OUT1000,
                            remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                ports = 1
                if ser is None:
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetVoltageOutput',DeviceID.PHIDID_OUT1001,
                                    remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                    ports = 1
                if ser is None:
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetVoltageOutput',DeviceID.PHIDID_OUT1002,
                                    remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                    ports = 1
                if ser is None:
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetVoltageOutput',DeviceID.PHIDID_1002,
                                    remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                    ports = 4
                if ser is not None:
                    self.aw.ser.PhidgetAnalogOut[serial] = []
                    for i in range(ports):
                        vo = VoltageOutput()
                        if port is not None:
                            vo.setHubPort(port)
                        vo.setDeviceSerialNumber(ser)
                        vo.setChannel(i)
                        if self.aw.qmc.phidgetRemoteOnlyFlag and self.aw.qmc.phidgetRemoteFlag:
                            vo.setIsRemote(True)
                            vo.setIsLocal(False)
                        elif not self.aw.qmc.phidgetRemoteFlag:
                            vo.setIsRemote(False)
                            vo.setIsLocal(True)
                        self.aw.ser.PhidgetAnalogOut[serial].append(vo)
                    if serial is None:
                        # we make this also accessible via its serial number
                        self.aw.ser.PhidgetAnalogOut[str(ser)] = self.aw.ser.PhidgetAnalogOut[None]
        try:
            ch = self.aw.ser.PhidgetAnalogOut[serial][channel]
            ch.setOnAttachHandler(self.phidgetOUTattached)
            ch.setOnDetachHandler(self.phidgetOUTdetached)
            if not ch.getAttached():
                if self.aw.qmc.phidgetRemoteFlag:
                    ch.openWaitForAttachment(3000)
                else:
                    ch.openWaitForAttachment(1200)
                if serial is None and ch.getAttached():
                    # we make this also accessible via its serial number + port
                    s = self.serialPort2serialString(ch.getDeviceSerialNumber(),ch.getHubPort())
                    self.aw.ser.PhidgetAnalogOut[s] = self.aw.ser.PhidgetAnalogOut[None]
        except:
            pass

    # value: float
    # returns True or False indicating set status
    def phidgetVOUTsetVOUT(self,channel,value,serial=None):
        res = False
        self.phidgetVOUTattach(channel,serial)
        if serial in self.aw.ser.PhidgetAnalogOut:
            out = self.aw.ser.PhidgetAnalogOut[serial]
            # set voltage output
            try:
                if len(out) > channel and out[channel].getAttached():
                    if value == 0:
                        out[channel].setVoltage(0)
                        out[channel].setEnabled(False)
                    else:
                        out[channel].setVoltage(value)
                        out[channel].setEnabled(True)
                    res = True
            except Exception:
                res = False
        return res
        
    # value: int (either 5 or 10)
    # returns True or False indicating set status
    def phidgetVOUTsetRange(self,channel,value,serial=None):
        res = False
        self.phidgetVOUTattach(channel,serial)
        if serial in self.aw.ser.PhidgetAnalogOut:
            out = self.aw.ser.PhidgetAnalogOut[serial]
            # set voltage output
            try:
                if len(out) > channel and out[channel].getAttached():
                    if value == 5:
                        out[channel].setVoltageOutputRange(VoltageOutputRange.VOLTAGE_OUTPUT_RANGE_5V)
                    else:
                        out[channel].setVoltageOutputRange(VoltageOutputRange.VOLTAGE_OUTPUT_RANGE_10V)
                    res = True
            except:
                res = False
        return res

    def phidgetVOUTclose(self):
        for c in self.aw.ser.PhidgetAnalogOut:
            out = self.aw.ser.PhidgetAnalogOut[c]
            for i in range(len(out)):
                try:
                    if out[i].getAttached():
                        out[i].setEnabled(False)
                        self.phidgetOUTdetached(out[i])
                    out[i].close()
                except Exception:
                    pass
        self.aw.ser.PhidgetAnalogOut = {}


#--- Phidget DCMotor
#  only supporting
#     1 channel VINT DCC1000 and DCC1002
#     2 channel VINT DCC1003
#  commands: 
#     accel(c,v[,sn]) with c channel number and v acceleration as a float, and sn serial the optional serial/port number of the addressed module
#     vel(c,v[,sn])   with c channel number and v target velocity as a float, and sn serial the optional serial/port number of the addressed module

    # serial: optional Phidget HUB serial number with optional port number as string of the form "<serial>[:<port>]"
    def phidgetDCMotorAttach(self,channel,serial):
        if not serial in self.aw.ser.PhidgetDCMotor:
            if self.aw.qmc.phidgetManager is None:
                self.aw.qmc.startPhidgetManager()
            if self.aw.qmc.phidgetManager is not None:
                # try to attach the DCMotor modules
                s,p = self.serialString2serialPort(serial)
                ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetDCMotor',DeviceID.PHIDID_DCC1000,
                            remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                ports = 1
                if ser is None:
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetDCMotor',DeviceID.PHIDID_DCC1002,
                                    remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                    ports = 1
                if ser is None:
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetDCMotor',DeviceID.PHIDID_DCC1003,
                                    remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                    ports = 2
                if ser is not None:
                    self.aw.ser.PhidgetDCMotor[serial] = []
                    for i in range(ports):
                        dcm = DCMotor()
                        if port is not None:
                            dcm.setHubPort(port)
                        dcm.setDeviceSerialNumber(ser)
                        dcm.setChannel(i)
                        if self.aw.qmc.phidgetRemoteOnlyFlag and self.aw.qmc.phidgetRemoteFlag:
                            dcm.setIsRemote(True)
                            dcm.setIsLocal(False)
                        elif not self.aw.qmc.phidgetRemoteFlag:
                            dcm.setIsRemote(False)
                            dcm.setIsLocal(True)
                        self.aw.ser.PhidgetDCMotor[serial].append(dcm)
                    if serial is None:
                        # we make this also accessible via its serial number
                        self.aw.ser.PhidgetDCMotor[str(ser)] = self.aw.ser.PhidgetDCMotor[None]
        try:
            ch = self.aw.ser.PhidgetDCMotor[serial][channel]
            ch.setOnAttachHandler(self.phidgetOUTattached)
            ch.setOnDetachHandler(self.phidgetOUTdetached)
            if not ch.getAttached():
                if self.aw.qmc.phidgetRemoteFlag:
                    ch.openWaitForAttachment(3000)
                else:
                    ch.openWaitForAttachment(1200)
                if serial is None and ch.getAttached():
                    # we make this also accessible via its serial number + port
                    s = self.serialPort2serialString(ch.getDeviceSerialNumber(),ch.getHubPort())
                    self.aw.ser.PhidgetDCMotor[s] = self.aw.ser.PhidgetDCMotor[None]
        except:
            pass

    # value: float
    def phidgetDCMotorSetAcceleration(self,channel,value,serial=None):
        self.phidgetDCMotorAttach(channel,serial)
        if serial in self.aw.ser.PhidgetDCMotor:
            dcm = self.aw.ser.PhidgetDCMotor[serial]
            # set velocity
            try:
                if len(dcm) > channel and dcm[channel].getAttached():
                    dcm[channel].setAcceleration(value)
            except Exception:
                pass

    # value: float
    def phidgetDCMotorSetVelocity(self,channel,value,serial=None):
        self.phidgetDCMotorAttach(channel,serial)
        if serial in self.aw.ser.PhidgetDCMotor:
            dcm = self.aw.ser.PhidgetDCMotor[serial]
            self.aw.sendmessage("dcm found")
            # set velocity
            try:
                if len(dcm) > channel and dcm[channel].getAttached():
                    dcm[channel].setTargetVelocity(value)
            except:
                pass
                
    # value: float
    def phidgetDCMotorSetCurrentLimit(self,channel,value,serial=None):
        self.phidgetDCMotorAttach(channel,serial)
        if serial in self.aw.ser.PhidgetDCMotor:
            dcm = self.aw.ser.PhidgetDCMotor[serial]
            # set current limit
            try:
                if len(dcm) > channel and dcm[channel].getAttached():
                    dcm[channel].setCurrentLimit(value)
            except Exception:
                pass
    
    def phidgetDCMotorClose(self):
        for c in self.aw.ser.PhidgetDCMotor:
            dcm = self.aw.ser.PhidgetDCMotor[c]
            for i in range(len(dcm)):
                try:
                    if dcm[i].getAttached():
                        self.phidgetOUTdetached(dcm[i])
                    dcm[i].close()
                except Exception:
                    pass
        self.aw.ser.PhidgetDCMotor = {}




#--- Yoctopuce Voltage Output
#  only supporting 
#     2 channel Yocto-0-10V-Tx
#  commands: vout(c,v[,sn]) with c the channel (1 or 2), v voltage in V as a float [0.0-10.0], and sn the modules serial number or its logical name

    # module_id is a string that is either None, a module serial number or a module logical name
    # it is assumed that the modules two channels do not have custom function names different from
    # voltageOutput1 and voltageOutput2
    def yoctoVOUTattach(self,c,module_id):
        # check if VoltageOutput object for channel c and module_id is already attached
        voltageOutputs = self.aw.ser.YOCTOvoltageOutputs
        m = next((x for x in voltageOutputs if 
                x.get_functionId() == "voltageOutput"+str(c) and 
                (module_id is None or module_id == x.get_serialNumber() or module_id == x.get_logicalName())),
                None)
        if m is not None:
            return m
        # the module/channel is not yet attached search for it
        self.YOCTOimportLIB() # first import the lib
        from yoctopuce.yocto_voltageoutput import YVoltageOutput
        if module_id is None:
            vout = YVoltageOutput.FirstVoltageOutput()
            if vout is None:
                return None
            m = vout.get_module()
            target = m.get_serialNumber()
        else:
            target = module_id
        YOCTOvoltageOutput = YVoltageOutput.FindVoltageOutput(target + '.voltageOutput' + str(c))
        if YOCTOvoltageOutput.isOnline():
            self.aw.ser.YOCTOvoltageOutputs.append(YOCTOvoltageOutput)
            return YOCTOvoltageOutput
        else:
            return None
    
    def yoctoVOUTsetVOUT(self,c,v,module_id=None):
        try:
            m = self.yoctoVOUTattach(c,module_id)
            if m is not None and m.isOnline():
                m.set_currentVoltage(v) # with v a voltage in V [0.0-10.0]
        except:
            pass
    
    def yoctoVOUTclose(self):
        self.aw.ser.YOCTOvoltageOutputs = []
        try:
            YAPI.FreeAPI() 
        except:
            pass


#--- Yoctopuce Current Output
#  only supporting 
#     1 channel Yocto-4-20mA-Tx
#  commands: cout(c[,sn]) with c current in mA as a float [3.0-21.0], and sn the modules serial number or its logical name

    # module_id is a string that is either None, a module serial number or a module logical name
    # it is assumed that the modules two channels do not have custom function names different from
    # voltageOutput1 and voltageOutput2
    def yoctoCOUTattach(self,module_id):
        # check if YOCTOcurrentOutput object for module_id is already attached
        currentOutputs = self.aw.ser.YOCTOcurrentOutputs
        m = next((x for x in currentOutputs if 
                x.get_functionId() == "currentLoopOutput" and 
                (module_id is None or module_id == x.get_serialNumber() or module_id == x.get_logicalName())),
                None)
        if m is not None:
            return m
        # the module/channel is not yet attached search for it
        self.YOCTOimportLIB() # first import the lib
        from yoctopuce.yocto_currentloopoutput import YCurrentLoopOutput
        if module_id is None:
            cout = YCurrentLoopOutput.FirstCurrentLoopOutput()
            if cout is None:
                return None
            m = cout.get_module()
            target = m.get_serialNumber()
        else:
            target = module_id
        YOCTOcurrentOutput = YCurrentLoopOutput.FindCurrentLoopOutput(target + '.currentLoopOutput')
        if YOCTOcurrentOutput.isOnline():
            self.aw.ser.YOCTOcurrentOutputs.append(YOCTOcurrentOutput)
            return YOCTOcurrentOutput
        else:
            return None

    def yoctoCOUTsetCOUT(self,c,module_id=None):
        try:
            m = self.yoctoCOUTattach(module_id)
            if m is not None and m.isOnline():
                m.set_current(c) # with c a current in mA [3.0-21.0]
        except:
            pass

    def yoctoCOUTclose(self):
        self.aw.ser.YOCTOcurrentOutputs = []
        try:
            YAPI.FreeAPI() 
        except:
            pass


#--- Yoctopuce PWM Output
#  only supporting 
#     2 channel Yocto-PWM-Tx
#  commands:
#     enabled(c,b[,sn])
#     freq(c,f[,sn])
#     duty(c,d[,sn])
#     move(c,d,t[,sn]) 
#    with 
#     c the channel (1 or 2)
#     b a bool given as 0, 1, False or True
#     f the frequency in Hz as an integer [0-1000000]
#     d the duty cycle in % as a float [0.0-100.0]
#     t the time as an integer in milliseconds
#     sn the modules serial number or its logical name

    # module_id is a string that is either None, a module serial number or a module logical name
    # it is assumed that the modules two channels do not have custom function names different from
    # pwmOutput1 and pwmOutput2
    def yoctoPWMattach(self,c,module_id):
        # check if YPwmOutput object for channel c and module_id is already attached
        pwmOutputs = self.aw.ser.YOCTOpwmOutputs
        m = next((x for x in pwmOutputs if 
                x.get_functionId() == "pwmOutput"+str(c) and 
                (module_id is None or module_id == x.get_serialNumber() or module_id == x.get_logicalName())),
                None)
        if m is not None:
            return m
        # the module/channel is not yet attached search for it
        self.YOCTOimportLIB() # first import the lib
        from yoctopuce.yocto_pwmoutput import YPwmOutput
        if module_id is None:
            vout = YPwmOutput.FirstPwmOutput()
            if vout is None:
                return None
            m = vout.get_module()
            target = m.get_serialNumber()
        else:
            target = module_id
        YOCTOpwmOutput = YPwmOutput.FindPwmOutput(target + '.pwmOutput' + str(c))
        if YOCTOpwmOutput.isOnline():
            self.aw.ser.YOCTOpwmOutputs.append(YOCTOpwmOutput)
            return YOCTOpwmOutput
        else:
            return None
    
    def yoctoPWMenabled(self,c,b,module_id=None):
        try:
            m = self.yoctoPWMattach(c,module_id)
            if m is not None and m.isOnline():
                from yoctopuce.yocto_pwmoutput import YPwmOutput
                if b:
                    m.set_enabled(YPwmOutput.ENABLED_TRUE)
                else:
                    m.set_enabled(YPwmOutput.ENABLED_FALSE)
        except:
            pass
    
    def yoctoPWMsetFrequency(self,c,f,module_id=None):
        try:
            m = self.yoctoPWMattach(c,module_id)
            if m is not None and m.isOnline():
                m.set_frequency(f) # with f the frequency in Hz as an integer [0-1000000]
        except:
            pass
    
    def yoctoPWMsetDuty(self,c,d,module_id=None):
        try:
            m = self.yoctoPWMattach(c,module_id)
            if m is not None and m.isOnline():
                m.set_dutyCycle(d) # d the duty cycle in % as a float [0.0-100.0]
        except:
            pass
    
    def yoctoPWMmove(self,c,d,t,module_id=None):
        try:
            m = self.yoctoPWMattach(c,module_id)
            if m is not None and m.isOnline():
                m.dutyCycleMove(d,t) # d the duty cycle in % as a float [0.0-100.0] and t the time as an integer in milliseconds
        except:
            pass
    
    def yoctoPWMclose(self):
        self.aw.ser.YOCTOpwmOutputs = []
        try:
            YAPI.FreeAPI() 
        except:
            pass


#--- Yoctopuce Relay Output
#  supporting
#     2 channel Yocto-Relay
#     1 channel Yocto-LatchedRelay
#     8 channel Yocto-MaxiCoupler-V2
#     1 channel Yocto-PowerRelay-V2
#     1 channel Yocto-PowerRelay-V3
#     5 channel Yocto-MaxiPowerRelay
#  commands: 
#      on(c[,sn])
#      off(c[,sn])
#      flip(c[,sn])
#      pulse(c,delay,duration[,sn])
#    with c the channel, delay and duration in milliseconds, sn the option module serial number or its logical name as string

    # module_id is a string that is either None, a module serial number or a module logical name
    # it is assumed that the modules two channels do not have custom function names different from
    # relay1, relay2,...
    def yoctoRELattach(self,c,module_id):
        # check if Relay object for channel c and module_id is already attached
        relays = self.aw.ser.YOCTOrelays
        m = next((x for x in relays if 
                x.get_functionId() == "relay"+str(c) and 
                (module_id is None or module_id == x.get_serialNumber() or module_id == x.get_logicalName())),
                None)
        if m is not None:
            return m
        # the module/channel is not yet attached search for it
        self.YOCTOimportLIB() # first import the lib
        from yoctopuce.yocto_relay import YRelay
        if module_id is None:
            rel = YRelay.FirstRelay()
            if rel is None:
                return None
            m = rel.get_module()
            target = m.get_serialNumber()
        else:
            target = module_id
        YOCTOrelay = YRelay.FindRelay(target + '.relay' + str(c))
        module = YOCTOrelay.get_module()
        module.isOnline()
        if YOCTOrelay.isOnline():
            self.aw.ser.YOCTOrelays.append(YOCTOrelay)
            return YOCTOrelay
        else:
            return None

    def yoctoRELon(self,c,module_id=None):
        try:
            m = self.yoctoRELattach(c,module_id)
            if m is not None and m.isOnline():
                from yoctopuce.yocto_relay import YRelay
                m.set_state(YRelay.STATE_B)
                #m.set_output(YRelay.OUTPUT_ON)
        except:
            pass
    
    def yoctoRELoff(self,c,module_id=None):
        try:
            m = self.yoctoRELattach(c,module_id)
            if m is not None and m.isOnline():
                from yoctopuce.yocto_relay import YRelay
                m.set_state(YRelay.STATE_A)
                #m.set_output(YRelay.OUTPUT_OFF)
        except:
            pass
    
    def yoctoRELflip(self,c,module_id=None):
        try:
            m = self.yoctoRELattach(c,module_id)
            if m is not None and m.isOnline():
                m.toggle()
        except:
            pass
    
    def yoctoRELpulse(self,c,delay,duration,module_id=None):
        try:
            m = self.yoctoRELattach(c,module_id)
            if m is not None and m.isOnline():
                m.delayedPulse(delay,duration)
        except:
            pass

    def yoctoRELclose(self):
        self.aw.ser.YOCTOrelays = []
        try:
            YAPI.FreeAPI() 
        except:
            pass


#--- Yoctopuce Servo Output
#  supporting
#     5 channel Yocto-Servo
#  commands: 
#      enabled(c,b[,sn])
#      move(c,p[,t][,sn])
#      neutral(c,n[,sn])
#      range(c,r[,sn])
#    with c the channel, delay and duration in milliseconds, sn the option module serial number or its logical name as string

    # module_id is a string that is either None, a module serial number or a module logical name
    # it is assumed that the modules two channels do not have custom function names different from
    # relay1, relay2,...
    def yoctoSERVOattach(self,c,module_id):
        # check if Servo object for channel c and module_id is already attached
        servos = self.aw.ser.YOCTOservos
        m = next((x for x in servos if 
                x.get_functionId() == "servo"+str(c) and 
                (module_id is None or module_id == x.get_serialNumber() or module_id == x.get_logicalName())),
                None)
        if m is not None:
            return m
        # the module/channel is not yet attached search for it
        self.YOCTOimportLIB() # first import the lib
        from yoctopuce.yocto_servo import YServo
        if module_id is None:
            srv = YServo.FirstServo()
            if srv is None:
                return None
            m = srv.get_module()
            target = m.get_serialNumber()
        else:
            target = module_id
        YOCTOservo = YServo.FindServo(target + '.servo' + str(c))
        module = YOCTOservo.get_module()
        module.isOnline()
        if YOCTOservo.isOnline():
            self.aw.ser.YOCTOservos.append(YOCTOservo)
            return YOCTOservo
        else:
            return None

    def yoctoSERVOenabled(self,c,b,module_id=None):
        try:
            m = self.yoctoSERVOattach(c,module_id)
            if m is not None and m.isOnline():
                m.enabled(b)
        except:
            pass

    def yoctoSERVOposition(self,c,p,module_id=None):
        try:
            m = self.yoctoSERVOattach(c,module_id)
            if m is not None and m.isOnline():
                m.set_position(p)
        except:
            pass

    def yoctoSERVOmove(self,c,p,t,module_id=None):
        try:
            m = self.yoctoSERVOattach(c,module_id)
            if m is not None and m.isOnline():
                m.move(p,t)
        except:
            pass

    def yoctoSERVOneutral(self,c,n,module_id=None):
        try:
            m = self.yoctoSERVOattach(c,module_id)
            if m is not None and m.isOnline():
                m.neutral(n)
        except:
            pass

    def yoctoSERVOrange(self,c,r,module_id=None):
        try:
            m = self.yoctoSERVOattach(c,module_id)
            if m is not None and m.isOnline():
                m.range(r)
        except:
            pass

    def yoctoSERVOclose(self):
        self.aw.ser.YOCTOservos = []
        try:
            YAPI.FreeAPI() 
        except:
            pass


#--- Phidget RC (only one supported for now)
#  supporting up to 16 channels like those of the RCC1000
#  commands: 
#     pulse(ch,min,max[,sn]) # sets min/max pulse width
#     pos(ch,min,max[,sn])   # sets min/max position
#     engaged(ch,state[,sn]) # engage channel
#     set(ch,pos[,sn])       # sets position
#     ramp(ch,b[,sn])        # activates or deactivates the speed ramping state
#     volt(ch,v[,sn])        # set the voltage to one of 5, 6 or 7.4 in Volt
#     accel(ch,accel[,sn])   # set the acceleration 
#     veloc(ch,v[,sn])       # set the velocity

    # serial: optional Phidget HUB serial number with optional port number as string of the form "<serial>[:<port>]"
    def phidgetRCattach(self,channel,serial=None):
        if not serial in self.aw.ser.PhidgetRCServo:
            if self.aw.qmc.phidgetManager is None:
                self.aw.qmc.startPhidgetManager()
            if self.aw.qmc.phidgetManager is not None:
                # try to attach an Phidget RCC1000 module
                s,p = self.serialString2serialPort(serial)
                ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetRCServo',DeviceID.PHIDID_RCC1000,
                            remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                ports = 16
                # try to attach an Phidget RC 1061 module
                if ser is None:
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetRCServo',DeviceID.PHIDID_1061,
                                    remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                    ports = 8
                # try to attach an Phidget RC 1066 module
                if ser is None:
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget('PhidgetRCServo',DeviceID.PHIDID_1066,
                                    remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag,serial=s,hubport=p)
                    ports = 1
                if ser is not None:
                    self.aw.ser.PhidgetRCServo[serial] = []
                    for i in range(ports):
                        rcservo = RCServo()
                        if port is not None:
                            rcservo.setHubPort(port)
                        rcservo.setDeviceSerialNumber(ser)
                        rcservo.setChannel(i)
                        if self.aw.qmc.phidgetRemoteOnlyFlag and self.aw.qmc.phidgetRemoteFlag:
                            rcservo.setIsRemote(True)
                            rcservo.setIsLocal(False)
                        self.aw.ser.PhidgetRCServo[serial].append(rcservo)
                    if serial is None:
                        # we make this also accessible via its serial number
                        self.aw.ser.PhidgetRCServo[str(ser)] = self.aw.ser.PhidgetRCServo[None]
        try:
            ch = self.aw.ser.PhidgetRCServo[serial][channel]
            ch.setOnAttachHandler(self.phidgetOUTattached)
            ch.setOnDetachHandler(self.phidgetOUTdetached)
            if not ch.getAttached():
                if self.aw.qmc.phidgetRemoteFlag:
                    ch.openWaitForAttachment(3000)
                else:
                    ch.openWaitForAttachment(1500)
                if serial is None and ch.getAttached():
                    # we make this also accessible via its serial number + port
                    s = self.serialPort2serialString(ch.getDeviceSerialNumber(),ch.getHubPort())
                    self.aw.ser.PhidgetRCServo[s] = self.aw.ser.PhidgetRCServo[None]
        except:
            pass

    # sets min/max pulse width
    def phidgetRCpulse(self,channel,min_pulse,max_pulse,serial=None):
        self.phidgetRCattach(channel,serial)
        if serial in self.aw.ser.PhidgetRCServo and len(self.aw.ser.PhidgetRCServo[serial])>channel:
            self.aw.ser.PhidgetRCServo[serial][channel].setMinPulseWidth(min_pulse)
            self.aw.ser.PhidgetRCServo[serial][channel].setMaxPulseWidth(max_pulse)

    # sets min/max position
    def phidgetRCpos(self,channel,min_pos,max_pos,serial=None):
        self.phidgetRCattach(channel,serial)
        if serial in self.aw.ser.PhidgetRCServo and len(self.aw.ser.PhidgetRCServo[serial])>channel:
            self.aw.ser.PhidgetRCServo[serial][channel].setMinPosition(min_pos)
            self.aw.ser.PhidgetRCServo[serial][channel].setMaxPosition(max_pos)

    # engage channel
    def phidgetRCengaged(self,channel,state,serial=None):
        self.phidgetRCattach(channel,serial)
        if serial in self.aw.ser.PhidgetRCServo and len(self.aw.ser.PhidgetRCServo[serial])>channel:
            self.aw.ser.PhidgetRCServo[serial][channel].setEngaged(state)

    # sets position
    def phidgetRCset(self,channel,position,serial=None):
        self.phidgetRCattach(channel,serial)
        if serial in self.aw.ser.PhidgetRCServo and len(self.aw.ser.PhidgetRCServo[serial])>channel:
            self.aw.ser.PhidgetRCServo[serial][channel].setTargetPosition(position)

    # set speed rampling state per channel
    def phidgetRCspeedRamping(self,channel,state,serial=None):
        self.phidgetRCattach(channel,serial)
        if serial in self.aw.ser.PhidgetRCServo and len(self.aw.ser.PhidgetRCServo[serial])>channel:
            self.aw.ser.PhidgetRCServo[serial][channel].setSpeedRampingState(state)

    # set voltage per channel
    def phidgetRCvoltage(self,channel,volt,serial=None):
        self.phidgetRCattach(channel,serial)
        if serial in self.aw.ser.PhidgetRCServo and len(self.aw.ser.PhidgetRCServo[serial])>channel:
            from Phidget22.RCServoVoltage import RCServoVoltage
            if volt>6:
                # set to 7.4V
                v = RCServoVoltage.RCSERVO_VOLTAGE_7_4V
            elif volt < 6:
                # set to 5V
                v = RCServoVoltage.RCSERVO_VOLTAGE_5V
            else:
                # set to 6V
                v = RCServoVoltage.RCSERVO_VOLTAGE_6V
            self.aw.ser.PhidgetRCServo[serial][channel].setVoltage(v)
            
    # sets acceleration
    def phidgetRCaccel(self,channel,accel,serial=None):
        self.phidgetRCattach(channel,serial)
        if serial in self.aw.ser.PhidgetRCServo and len(self.aw.ser.PhidgetRCServo[serial])>channel:
            self.aw.ser.PhidgetRCServo[serial][channel].setAcceleration(accel)
            
    # sets velocity
    def phidgetRCveloc(self,channel,veloc,serial=None):
        self.phidgetRCattach(channel,serial)
        if serial in self.aw.ser.PhidgetRCServo and len(self.aw.ser.PhidgetRCServo[serial])>channel:
            self.aw.ser.PhidgetRCServo[serial][channel].setVelocityLimit(veloc)

    def phidgetRCclose(self):
        for c in self.aw.ser.PhidgetRCServo:
            rc = self.aw.ser.PhidgetRCServo[c]
            for i in range(len(rc)):
                try:
                    if rc[i].getAttached():
                        rc[i].setEngaged(False)
                        self.phidgetOUTdetached(rc[i])
                    rc[i].close()
                except Exception:
                    pass
            self.aw.ser.PhidgetRCServo = {}
        
#---

    def phidget1018SensorChanged(self,v,channel,idx,API):
        if self.PhidgetIO and len(self.PhidgetIO) > idx:
            if API == "current" or (API == "voltage" and not self.aw.qmc.phidget1018_ratio[channel]):
                v = v * self.aw.qmc.phidget1018valueFactor
            try:
                #### lock shared resources #####
                self.PhidgetIOsemaphores[channel].acquire(1)
                self.PhidgetIOvalues[channel].append((v,libtime.time()))
            finally:
                if self.PhidgetIOsemaphores[channel].available() < 1:
                    self.PhidgetIOsemaphores[channel].release(1)

    def phidget1018getSensorReading(self,i,idx,deviceType,API="voltage"):
        if self.PhidgetIO and len(self.PhidgetIO) > idx: 
            if API != "digital" and self.aw.qmc.phidget1018_async[i]:
                res = None
                try:
                    #### lock shared resources #####
                    self.PhidgetIOsemaphores[i].acquire(1)
                    now = libtime.time()
                    start_of_interval = now-self.aw.qmc.delay/1000
                    # 1. just consider async readings taken within the previous sampling interval
                    # and associate them with the (arrivial) time since the begin of that interval
                    valid_readings = [(r,t - start_of_interval) for (r,t) in self.PhidgetIOvalues[i] if t > start_of_interval]
                    if len(valid_readings) > 0:
                        # 2. calculate the value
                        # we take the median of all valid_readings weighted by the time of arrival, preferrring newer readings
                        readings = [r for (r,t) in valid_readings]
                        weights = [t for (r,t) in valid_readings]
                        res = wquantiles.median(numpy.array(readings),numpy.array(weights))
                        # 3. consume old readings
                        self.PhidgetIOvalues[i] = []                    
#                    if len(self.PhidgetIOvalues[i]) > 0:
##                        res = numpy.average(self.PhidgetIOvalues[i])
#                        res = numpy.median(self.PhidgetIOvalues[i])
#                        self.PhidgetIOvalues[i] = self.PhidgetIOvalues[i][-round((self.aw.qmc.delay/self.aw.qmc.phidget1018_dataRates[i])):] 
                except Exception:
                    self.PhidgetIOvalues[i] = []
                finally:
                    if self.PhidgetIOsemaphores[i].available() < 1:
                        self.PhidgetIOsemaphores[i].release(1)
                if res is None:
                    if self.PhidgetIOlastvalues[i] == -1: # there is no last value yet, we take a sync value
                        if API == "current":
                            res = self.PhidgetIO[idx].getCurrent() * self.aw.qmc.phidget1018valueFactor
                        elif API == "frequency":
                            res = self.PhidgetIO[idx].getFrequency()
                        else:
                            if self.aw.qmc.phidget1018_ratio[i] and deviceType != DeviceID.PHIDID_DAQ1400:
                                res = self.PhidgetIO[idx].getVoltageRatio()
                            else:
                                res = self.PhidgetIO[idx].getVoltage() * self.aw.qmc.phidget1018valueFactor
                        self.PhidgetIOlastvalues[i] = res
                        return res
                    else:
                        return self.PhidgetIOlastvalues[i] # return the previous result
                else:
                    self.PhidgetIOlastvalues[i] = res
                    return res
            else:
                if API == "digital":
                    v = self.PhidgetIOvalues[i] = int(self.PhidgetIO[idx].getState())
                elif API == "current":
                    v = self.PhidgetIO[idx].getCurrent() * self.aw.qmc.phidget1018valueFactor
                elif API == "frequency":
                    v = self.PhidgetIO[idx].getFrequency()
                else:
                    if self.aw.qmc.phidget1018_ratio[i] and deviceType != DeviceID.PHIDID_DAQ1400:
                        v = self.PhidgetIO[idx].getVoltageRatio()
                    else:
                        v = self.PhidgetIO[idx].getVoltage() * self.aw.qmc.phidget1018valueFactor
                return v
        else:
            return -1

    def configure1018(self,deviceType,idx,API="voltage"):
        # set data rates of all active inputs to 4ms
        if self.PhidgetIO and len(self.PhidgetIO) > idx:
            # reset async values
            if deviceType in [DeviceID.PHIDID_HUB0000]:
                # on VINT HUBs we use the
                channel = self.PhidgetIO[idx].getHubPort()
            else:
                channel = self.PhidgetIO[idx].getChannel()
            # set rate
            try:
                self.PhidgetIO[idx].setDataInterval(self.aw.qmc.phidget1018_dataRates[channel])
            except Exception:
                pass
            # set the PowerSupply for the DAQ1400
            if deviceType == DeviceID.PHIDID_DAQ1400:
                try:
                    from Phidget22.PowerSupply import PowerSupply
                    power_idx = self.aw.qmc.phidgetDAQ1400_powerSupply
                    if power_idx == 0:
                        power = PowerSupply.POWER_SUPPLY_OFF
                    elif power_idx == 1:
                        power = PowerSupply.POWER_SUPPLY_12V
                    else: # power_idx == 2:
                        power = PowerSupply.POWER_SUPPLY_24V
                    self.PhidgetIO[idx].setPowerSupply(power)
                except:
                    pass
            if API == "voltage":
                if self.aw.qmc.phidget1018_async[channel]:
                    try:
                        if self.aw.qmc.phidget1018_ratio[channel] and deviceType != DeviceID.PHIDID_DAQ1400:
                            ct = max(min(float(self.aw.qmc.phidget1018_changeTriggers[channel]/100.0),self.PhidgetIO[idx].getMaxVoltageRatioChangeTrigger()),self.PhidgetIO[idx].getMinVoltageRatioChangeTrigger())
                            self.PhidgetIO[idx].setVoltageRatioChangeTrigger(ct)
                        else:
                            ct = max(min(float(self.aw.qmc.phidget1018_changeTriggers[channel]/100.0),self.PhidgetIO[idx].getMaxVoltageChangeTrigger()),self.PhidgetIO[idx].getMinVoltageChangeTrigger())
                            self.PhidgetIO[idx].setVoltageChangeTrigger(ct)
                    except:
                        pass
                    if self.aw.qmc.phidget1018_ratio[channel] and deviceType != DeviceID.PHIDID_DAQ1400:                    
                        self.PhidgetIO[idx].setOnVoltageRatioChangeHandler(lambda _,t: self.phidget1018SensorChanged(t,channel,idx,API))
                    else:
                        self.PhidgetIO[idx].setOnVoltageChangeHandler(lambda _,t: self.phidget1018SensorChanged(t,channel,idx,API))
                else:
                    if self.aw.qmc.phidget1018_ratio[channel] and deviceType != DeviceID.PHIDID_DAQ1400:
                        self.PhidgetIO[idx].setVoltageRatioChangeTrigger(0.0)
                    else:
                        self.PhidgetIO[idx].setVoltageChangeTrigger(0.0)
                    if self.aw.qmc.phidget1018_ratio[channel] and deviceType != DeviceID.PHIDID_DAQ1400:
                        self.PhidgetIO[idx].setOnVoltageRatioChangeHandler(lambda *_:None) 
                    else:
                        self.PhidgetIO[idx].setOnVoltageChangeHandler(lambda *_:None) 
            elif API == "current":
                if self.aw.qmc.phidget1018_async[channel]:
                    ct = max(min(float(self.aw.qmc.phidget1018_changeTriggers[channel]/100.0),self.PhidgetIO[idx].getMaxCurrentChangeTrigger()),self.PhidgetIO[idx].getMinCurrentChangeTrigger())
                    self.PhidgetIO[idx].setCurrentChangeTrigger(ct)
                    self.PhidgetIO[idx].setOnCurrentChangeHandler(lambda _,t: self.phidget1018SensorChanged(t,channel,idx,API))
                else:
                    self.PhidgetIO[idx].setCurrentChangeTrigger(0.0)
                    self.PhidgetIO[idx].setOnCurrentChangeHandler(lambda *_:None)
            elif API == "frequency":
                if deviceType == DeviceID.PHIDID_DAQ1400:
                    # set the InputMode for the DAQ1400
                    self.setDAQ1400inputMode(idx)
                if self.aw.qmc.phidget1018_async[channel]:
                    self.PhidgetIO[idx].setOnFrequencyChangeHandler(lambda _,t: self.phidget1018SensorChanged(t,channel,idx,API))
                else:
                    self.PhidgetIO[idx].setOnFrequencyChangeHandler(lambda *_:None)
            elif API == "digital":
                if deviceType == DeviceID.PHIDID_DAQ1400:
                    # set the InputMode for the DAQ1400
                    self.setDAQ1400inputMode(idx)
            self.PhidgetIOvalues[channel] = [[],[],[],[],[],[],[],[]]
            self.PhidgetIOlastvalues = [-1]*8

    def setDAQ1400inputMode(self,idx):
        try:
            from Phidget22.InputMode import InputMode
            mode_idx = self.aw.qmc.phidgetDAQ1400_inputMode
            if mode_idx == 0:
                mode = InputMode.INPUT_MODE_NPN
            elif mode_idx == 1:
                mode = InputMode.INPUT_MODE_PNP
            self.PhidgetIO[idx].setInputMode(mode)
        except:
            pass

    def phidget1018attached(self,serial,port,className,deviceType,idx,API="voltage"):
        try:
            self.configure1018(deviceType,idx,API)
            if self.PhidgetIO is not None:
                channel = self.PhidgetIO[idx].getChannel()
                self.aw.qmc.phidgetManager.reserveSerialPort(serial,port,channel,className,deviceType,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                if channel == 0:
                    if deviceType == DeviceID.PHIDID_1011:
                        self.aw.sendmessage(QApplication.translate("Message","Phidget IO 2/2/2 attached",None))
                    elif deviceType == DeviceID.PHIDID_HUB0000:
                        self.aw.sendmessage(QApplication.translate("Message","Phidget IO 6/6/6 attached",None))
                    elif deviceType == DeviceID.PHIDID_1010_1013_1018_1019:
                        self.aw.sendmessage(QApplication.translate("Message","Phidget IO 8/8/8 attached",None))
                    elif deviceType == DeviceID.PHIDID_DAQ1400:
                        self.aw.sendmessage(QApplication.translate("Message","Phidget DAQ1400 attached",None))
                    else:
                        self.aw.sendmessage(QApplication.translate("Message","Phidget IO attached",None))
        except:
            pass

    def phidget1018detached(self,serial,port,className,deviceType,idx):
        try:
            if self.PhidgetIO is not None:
                channel = self.PhidgetIO[idx].getChannel()
                self.aw.qmc.phidgetManager.releaseSerialPort(serial,port,channel,className,deviceType,remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                if channel == 0:
                    if deviceType == DeviceID.PHIDID_1011:
                        self.aw.sendmessage(QApplication.translate("Message","Phidget IO 2/2/2 detached",None))
                    elif deviceType == DeviceID.PHIDID_HUB0000:
                        self.aw.sendmessage(QApplication.translate("Message","Phidget IO 6/6/6 detached",None))
                    elif deviceType == DeviceID.PHIDID_1010_1013_1018_1019:
                        self.aw.sendmessage(QApplication.translate("Message","Phidget IO 8/8/8 detached",None))
                    elif deviceType == DeviceID.PHIDID_DAQ1400:
                        self.aw.sendmessage(QApplication.translate("Message","Phidget DAQ1400 detached",None))
                    else:
                        self.aw.sendmessage(QApplication.translate("Message","Phidget IO detached",None))
        except:
            pass

    # mode = 0 for probe 1 and 2; mode = 1 for probe 3 and 4; mode 2 for probe 5 and 6; mode 3 for probe 7 and 8
    # access of the VoltageInput, DigitalInput or VoltageRatioInput for the following IO Phidgets
    #  - Phidget IO 8/8/8 (1010,1013,1018,1019,SBC): DeviceID.PHIDID_1010_1013_1018_1019
    #  - Phidget IO 6/6/6 (HUB0000): DeviceID.PHIDID_HUB0000
    #  - Phidget IO 2/2/2 (1011): DeviceID.PHIDID_1011
    # the API parameter is one of "voltage", "digital", "current", "frequency"
    # if single is set, only the first channel of the two is allocated
    def PHIDGET1018values(self,deviceType=DeviceID.PHIDID_1010_1013_1018_1019,mode=0, API="voltage", retry=True, single=False):
        try:
            if self.PhidgetIO is None and self.aw.qmc.phidgetManager is not None:
                ser = None
                port = None 
                if API == "digital":
                    tp = "PhidgetDigitalInput"
                elif API == "current":
                    tp = "PhidgetCurrentInput"
                elif API == "frequency":
                    tp = "PhidgetFrequencyCounter"
                else:
                    if self.aw.qmc.phidget1018_ratio[mode*2] and deviceType != DeviceID.PHIDID_DAQ1400:
                        tp = "PhidgetVoltageRatioInput"
                    else:
                        tp = "PhidgetVoltageInput"
                if mode == 0:
                    # we scan for available main device
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget(tp,deviceType,0,
                        remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                elif mode == 1:
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget(tp,deviceType,2,
                        remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                elif mode == 2:
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget(tp,deviceType,4,
                        remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                elif mode == 3:
                    ser,port = self.aw.qmc.phidgetManager.getFirstMatchingPhidget(tp,deviceType,6,
                        remote=self.aw.qmc.phidgetRemoteFlag,remoteOnly=self.aw.qmc.phidgetRemoteOnlyFlag)
                if ser:
                    if API == "digital":
                        self.PhidgetIO = [DigitalInput(),DigitalInput()]
                    elif API == "current":
                        self.PhidgetIO = [CurrentInput(),CurrentInput()]
                    elif API == "frequency":
                        self.PhidgetIO = [FrequencyCounter(),FrequencyCounter()]
                    else: # voltage
                        if self.aw.qmc.phidget1018_ratio[mode*2] and deviceType != DeviceID.PHIDID_DAQ1400:
                            ch1 = VoltageRatioInput()
                        else:
                            ch1 = VoltageInput()
                        if self.aw.qmc.phidget1018_ratio[mode*2+1] and deviceType != DeviceID.PHIDID_DAQ1400:
                            ch2 = VoltageRatioInput()
                        else:
                            ch2 = VoltageInput()
                        self.PhidgetIO = [ch1,ch2]
                    try: 
                        self.PhidgetIO[0].setOnAttachHandler(lambda _:self.phidget1018attached(ser,port,tp,deviceType,0,API))
                        self.PhidgetIO[0].setOnDetachHandler(lambda _:self.phidget1018detached(ser,port,tp,deviceType,0))
                        if deviceType != DeviceID.PHIDID_DAQ1400 and not single:
                            self.PhidgetIO[1].setOnAttachHandler(lambda _:self.phidget1018attached(ser,port,tp,deviceType,1,API))
                            self.PhidgetIO[1].setOnDetachHandler(lambda _:self.phidget1018detached(ser,port,tp,deviceType,1))
                        if deviceType in [DeviceID.PHIDID_HUB0000]:
                            # we are looking to attach a HUB port
                            self.PhidgetIO[0].setIsHubPortDevice(1)
                            self.PhidgetIO[1].setIsHubPortDevice(1)
                            # on VINT HUB devices we have to set the port
                            self.PhidgetIO[0].setHubPort(mode*2)
                            self.PhidgetIO[1].setHubPort(mode*2+1)
                        else:
                            self.PhidgetIO[0].setChannel(mode*2)
                            self.PhidgetIO[1].setChannel(mode*2+1)
                            if port is not None:
                                self.PhidgetIO[0].setHubPort(port)
                                self.PhidgetIO[1].setHubPort(port)
                        if self.aw.qmc.phidgetRemoteFlag:
                            self.addPhidgetServer()
                        self.PhidgetIO[0].setDeviceSerialNumber(ser)
                        try:
                            self.PhidgetIO[0].open() #.openWaitForAttachment(timeout)
                        except:
                            pass
                        self.PhidgetIO[1].setDeviceSerialNumber(ser)
                        if deviceType != DeviceID.PHIDID_DAQ1400 and not single:
                            try:
                                self.PhidgetIO[1].open() #.openWaitForAttachment(timeout)
                            except:
                                pass
                        # we need to give this device a bit time to attach, otherwise it will be considered for another Artisan channel of the same type
                        if self.aw.qmc.phidgetRemoteOnlyFlag:
                            libtime.sleep(.8)
                        else:
                            libtime.sleep(.5)
                    except Exception as ex:
                        #_, _, exc_tb = sys.exc_info()
                        #self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " PHIDGET1018values() {0}").format(str(ex)),exc_tb.tb_lineno)
                        try:
                            if self.PhidgetIO and self.PhidgetIO[0].getAttached():
                                self.PhidgetIO[0].close()
                            if self.PhidgetIO and len(self.PhidgetIO)> 1 and self.PhidgetIO[1].getAttached():
                                self.PhidgetIO[1].close()
                        except Exception:
                            pass
                        self.PhidgetIO = None
                        self.PhidgetIOvalues = [[],[],[],[],[],[],[],[]]
                        self.PhidgetIOlastvalues = [-1]*8
            if deviceType == DeviceID.PHIDID_DAQ1400 and self.PhidgetIO is not None and self.PhidgetIO and self.PhidgetIO[0].getAttached():
                probe = -1
                try:
                    probe = self.phidget1018getSensorReading(0,0,deviceType,API)
                except:
                    pass
                return probe, -1
            elif deviceType != DeviceID.PHIDID_DAQ1400 and self.PhidgetIO is not None and self.PhidgetIO and len(self.PhidgetIO)>1 and self.PhidgetIO[0].getAttached() and (single or self.PhidgetIO[1].getAttached()):
                probe1 = probe2 = -1
                try:
                    probe1 = self.phidget1018getSensorReading(mode*2,0,deviceType,API)
                except:
                    pass
                if not single:
                    try:
                        probe2 = self.phidget1018getSensorReading(mode*2 + 1,1,deviceType,API)
                    except Exception:
                        pass
                return probe1, probe2
            elif retry:
                libtime.sleep(0.1)
                self.PHIDGET1018values(deviceType,mode,API,False)
            else:
                return -1,-1
        except Exception as ex:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            try:
                if self.PhidgetIO and self.PhidgetIO[0].getAttached():
                    self.PhidgetIO[0].close()
                if not single and self.PhidgetIO and len(self.PhidgetIO)> 1 and self.PhidgetIO[1].getAttached():
                    self.PhidgetIO[1].close()
            except Exception:
                pass
            self.PhidgetIO = None
            self.PhidgetIOlastvalues = [[],[],[],[],[],[],[],[]] 
            self.PhidgetIOlastvalues = [-1]*8
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " PHIDGET1018values() {0}").format(str(ex)),exc_tb.tb_lineno)
            return -1,-1

#---

    # given the YOCTOsensor, return the first of the given mode
    #   mode=0 => Yocto-Thermocouple
    #   mode=1 => Yocto-Pt100
    #   mode=2 => Yocto-IR
    #   mode=3 => Yocto-Meteo
    #   mode=4 => Yocto-4-20mA-Rx (works also for the Yocto-0-10V-Rx, the Yocto-milliVolt-Rx and the Yocto-Serial)
    # that is not in the list of already connected ones
    def getNextYOCTOsensorOfType(self,mode,connected_yoctos,YOCTOsensor):
        if mode == 4:
            from yoctopuce.yocto_genericsensor import YGenericSensor
        else:
            from yoctopuce.yocto_temperature import YTemperature
        if YOCTOsensor:
            productName = YOCTOsensor.get_module().get_productName()
            if not (YOCTOsensor.get_module().get_serialNumber() in connected_yoctos) and  \
                ((mode == 0 and productName == "Yocto-Thermocouple") or (mode == 1 and productName == "Yocto-PT100") or \
                 (mode == 2 and productName == "Yocto-Temperature-IR") or \
                 (mode == 3 and productName.startswith("Yocto-Meteo")) or \
                 (mode == 4 and productName.startswith("Yocto-4-20mA-Rx")) or \
                 (mode == 4 and productName.startswith("Yocto-0-10V-Rx")) or \
                 (mode == 4 and productName.startswith("Yocto-milliVolt-Rx")) or \
                 (mode == 4 and productName.startswith("Yocto-Serial"))):
                return YOCTOsensor
            else:
                if mode == 4:
                    return self.getNextYOCTOsensorOfType(mode,connected_yoctos,YGenericSensor.nextGenericSensor(YOCTOsensor))
                else:
                    return self.getNextYOCTOsensorOfType(mode,connected_yoctos,YTemperature.nextTemperature(YOCTOsensor))
        else:
            return None
            
    def YOCTOimportLIB(self):
        errmsg=YRefParam()
        if not self.YOCTOlibImported:
            # import Yoctopuce Python library (installed form PyPI)
            #self.aw.sendmessage(str(errmsg))
            YAPI.DisableExceptions
            ## WINDOWS/Linux DLL HACK BEGIN
            arch = platform.architecture()[0]
            machine = platform.machine()
            libpath = os.path.dirname(sys.executable)
            if self.platf == 'Windows' and appFrozen():
                if arch == '32bit':
                    YAPI._yApiCLibFile = libpath + "\\lib\\yapi.dll"
                else:
                    YAPI._yApiCLibFile = libpath + "\\lib\\yapi64.dll"
                YAPI._yApiCLibFileFallback = libpath + "\\lib\\yapi.dll"
            elif self.platf == "Linux" and appFrozen():
                if machine.find("arm") >= 0: # Raspberry
                    YAPI._yApiCLibFile = libpath + "/libyapi-armhf.so"
                    YAPI._yApiCLibFileFallback = libpath + "/libyapi-armel.so"
                elif machine.find("mips") >= 0:
                    YAPI._yApiCLibFile = libpath + "/libyapi-mips.so"
                    YAPI._yApiCLibFileFallback = ""
                elif machine == 'x86_32' or (machine[0] == 'i' and machine[-2:] == '86'):
                    YAPI._yApiCLibFile = libpath + "/libyapi-i386.so"
                    YAPI._yApiCLibFileFallback = libpath + "/libyapi-amd64.so"  # just in case
                elif machine == 'x86_64':
                    YAPI._yApiCLibFile = libpath + "/libyapi-amd64.so"
                    YAPI._yApiCLibFileFallback = libpath + "/libyapi-i386.so"  # just in case
            ## WINDOWS/Linux DLL HACK END
        try:
            if self.aw.qmc.yoctoRemoteFlag:
                YAPI.RegisterHub(self.aw.qmc.yoctoServerID,errmsg)
            else:
                YAPI.RegisterHub("usb", errmsg)
            self.YOCTOlibImported = True
        except Exception as e:
            self.aw.sendmessage(str(e))

    def yoctoTimedCallback(self,_, measure,channel):
        try:
            #### lock shared resources #####
            self.YOCTOsemaphores[channel].acquire(1)
            self.YOCTOvalues[channel].append((measure.get_averageValue(),libtime.time()))
        finally:
            if self.YOCTOsemaphores[channel].available() < 1:
                self.YOCTOsemaphores[channel].release(1)
    
    # mode = 0 for 2x thermocouple model; mode = 1 for 1x PT100 type probe; mode = 2 for IR sensor; mode = 4 for the Yocto-4-20mA-Rx
    #   (as well as the Yocto-0-10V-Rx, Yocto-milliVolt-Rx and Yocto-Serial)
    def YOCTOtemperatures(self,mode=0):
        try: 
            if not self.YOCTOsensor:
                self.YOCTOimportLIB()
                try:
                    if mode == 4:
                        from yoctopuce.yocto_genericsensor import YGenericSensor
                    else:
                        from yoctopuce.yocto_temperature import YTemperature
                    YAPI.DisableExceptions
                    # already connected YOCTOsensors?
                    if not self.aw.ser.YOCTOsensor:
                        connected_yoctos = []
                    else:
                        connected_yoctos = [self.aw.ser.YOCTOsensor.get_module().get_serialNumber()]
                    for s in self.aw.extraser:
                        if s.YOCTOsensor is not None:
                            connected_yoctos.append(s.YOCTOsensor.get_module().get_serialNumber())
                    
                    # search for the next one of the required type, but not yet connected
                    if mode == 4:
                        self.YOCTOsensor = self.getNextYOCTOsensorOfType(mode,connected_yoctos,YGenericSensor.FirstGenericSensor())
                    else:
                        self.YOCTOsensor = self.getNextYOCTOsensorOfType(mode,connected_yoctos,YTemperature.FirstTemperature())
                    
                    yocto_res = 0.0001 # while 0.001 seems to be the maximum accepted, but just returning mostly 2 decimals!?
                    if mode in [0,2] and self.YOCTOsensor is not None and self.YOCTOsensor.isOnline():
                        serial=self.YOCTOsensor.get_module().get_serialNumber()
                        self.YOCTOchan1 = YTemperature.FindTemperature(serial + '.temperature1')
                        self.YOCTOchan2 = YTemperature.FindTemperature(serial + '.temperature2')
                        if mode == 0:
                            self.aw.sendmessage(QApplication.translate("Message","Yocto Thermocouple attached",None))
                        elif mode == 2:
                            self.aw.sendmessage(QApplication.translate("Message","Yocto IR attached",None))
                        # increase the resolution
                        try:
                            self.YOCTOchan1.set_resolution(yocto_res)
                            self.YOCTOchan2.set_resolution(yocto_res)
                        except:
                            pass
                        # get units
                        try:
                            unit1 = self.YOCTOchan1.get_unit()
                            if unit1 is not None and len(unit1) > 0 and unit1[-1] != "C":
                                self.aw.qmc.YOCTOchan1Unit = "F"
                            else:
                                self.aw.qmc.YOCTOchan1Unit = "C"
                            unit2 = self.YOCTOchan2.get_unit()
                            if unit2 is not None and len(unit2) > 0 and unit2[-1] != "C":
                                self.aw.qmc.YOCTOchan2Unit = "F"
                            else:
                                self.aw.qmc.YOCTOchan2Unit = "C"
                        except:
                            pass
                        if self.aw.qmc.YOCTO_dataRate > 1000:
                            reportFrequency = "60/m" # in this mode the average of a measurements over the last second is returned
                        else:
                            reportFrequency = "{}/s".format(int(round(1000/self.aw.qmc.YOCTO_dataRate)))   # 30/s => 30ms
                            # if reportFrequency is set to "1/s", every second the last measurement sampled by the device is returned
                            # note that this is different from "60/m" which returns an average over many values

                        if self.aw.qmc.YOCTO_async[0]:
                            self.YOCTOchan1.set_reportFrequency(reportFrequency)
                            self.YOCTOchan1.registerTimedReportCallback(lambda fct,measure: self.yoctoTimedCallback(fct,measure,0))
                        else:
                            self.YOCTOchan1.registerTimedReportCallback(lambda *_:None)
                        if self.aw.qmc.YOCTO_async[0]: # flag for channel 1 is ignored and only that of channel 0 is respected for both channels
                            self.YOCTOchan2.set_reportFrequency(reportFrequency)
                            self.YOCTOchan2.registerTimedReportCallback(lambda fct,measure: self.yoctoTimedCallback(fct,measure,1))
                        else:
                            self.YOCTOchan2.registerTimedReportCallback(lambda *_:None)
                        if self.aw.qmc.YOCTO_async[0]:# or self.aw.qmc.YOCTO_async[1]: # flag for channel 1 is ignored and only that of channel 0 is respected for both channels
                            if self.YOCTOthread is None:
                                self.YOCTOthread = YoctoThread()
                            self.YOCTOthread.start()
                    elif mode == 1 and self.YOCTOsensor is not None and self.YOCTOsensor.isOnline():
                        self.aw.sendmessage(QApplication.translate("Message","Yocto PT100 attached",None))  
                        # increase the resolution
                        try:
                            self.YOCTOsensor.set_resolution(yocto_res)
                            self.YOCTOsensor.set_resolution(yocto_res)
                        except:
                            pass  
                        # get units
                        try:
                            unit = self.YOCTOchan.get_unit()
                            if unit is not None and len(unit) > 0 and unit[-1] != "C":
                                self.aw.qmc.YOCTOchanUnit = "F"
                            else:
                                self.aw.qmc.YOCTOchanUnit = "C"
                        except:
                            pass
                        if self.aw.qmc.YOCTO_async[0]:
                            if self.aw.qmc.YOCTO_dataRate > 1000:
                                reportFrequency = "60/m" # in this mode the average of a measurements over the last second is returned
                            else:
                                reportFrequency = "{}/s".format(int(round(1000/self.aw.qmc.YOCTO_dataRate)))   # 30/s => 30ms
                                # if reportFrequency is set to "1/s", every second the last measurement sampled by the device is returned
                                # note that this is different from "60/m" which returns an average over many values
                            self.YOCTOsensor.set_reportFrequency(reportFrequency)
                            self.YOCTOsensor.registerTimedReportCallback(lambda fct,measure: self.yoctoTimedCallback(fct,measure,0))
                            if self.YOCTOthread is None:
                                self.YOCTOthread = YoctoThread()
                            self.YOCTOthread.start()
                    elif mode == 4 and self.YOCTOsensor is not None and self.YOCTOsensor.isOnline():
                        serial=self.YOCTOsensor.get_module().get_serialNumber()
                        self.YOCTOchan1 = YGenericSensor.FindGenericSensor(serial + '.genericSensor1')
                        self.YOCTOchan2 = YGenericSensor.FindGenericSensor(serial + '.genericSensor2')
                        self.aw.sendmessage(QApplication.translate("Message","Yocto 4-20mA-Rx attached",None))
                except:
                    if self.YOCTOthread is not None:
                        self.YOCTOthread.join()
                        self.YOCTOthread = None
            probe1 = -1
            probe2 = -1
            if mode in [0,2]:
                try:
                    if self.aw.qmc.YOCTO_async[0]:
                        try:
                            #### lock shared resources #####
                            self.YOCTOsemaphores[0].acquire(1)
                            now = libtime.time()
                            start_of_interval = now-self.aw.qmc.delay/1000
                            # 1. just consider async readings taken within the previous sampling interval
                            # and associate them with the (arrivial) time since the begin of that interval
                            valid_readings = [(r,t - start_of_interval) for (r,t) in self.YOCTOvalues[0] if t > start_of_interval]
                            if len(valid_readings) > 0:
                                # 2. calculate the value
                                # we take the median of all valid_readings weighted by the time of arrival, preferrring newer readings
                                readings = [r for (r,t) in valid_readings]
                                weights = [t for (r,t) in valid_readings]
                                probe1 = wquantiles.median(numpy.array(readings),numpy.array(weights))
                                # 3. consume old readings
                                self.YOCTOvalues[0] = []
#                            if len(self.YOCTOvalues[0]) > 0:
##                                probe1 = numpy.average(self.YOCTOvalues[0])
#                                probe1 = numpy.median(self.YOCTOvalues[0])
#                                self.YOCTOvalues[0] = self.YOCTOvalues[0][-max(1,round((self.aw.qmc.delay/self.aw.qmc.YOCTO_dataRate))):]
                        except:
                            self.YOCTOvalues[0] = []
                        finally:
                            if self.YOCTOsemaphores[0].available() < 1:
                                self.YOCTOsemaphores[0].release(1)
                        if probe1 == -1:
                            probe1 = self.YOCTOlastvalues[0]
                        else:
                            self.YOCTOlastvalues[0] = probe1
                    if probe1 == -1 and self.YOCTOchan1 and self.YOCTOchan1.isOnline():
                        probe1 = self.YOCTOchan1.get_currentValue()
                    if probe1 != -1:
                        if mode == 2:
                            # we average this module temperature channel for the IR module to remove noise
                            if self.YOCTOtempIRavg is None:
                                self.YOCTOtempIRavg = probe1
                            else:
                                self.YOCTOtempIRavg = (20* self.YOCTOtempIRavg + probe1) / 21.0
                                probe1 = self.YOCTOtempIRavg
                        # convert temperature scale
                        if self.aw.qmc.YOCTOchan1Unit == "C" and self.aw.qmc.mode == "F":
                            probe1 = fromCtoF(probe1)
                        elif self.aw.qmc.YOCTOchan1Unit == "F" and self.aw.qmc.mode == "C":
                            probe1 = fromFtoC(probe1)
                except:
                    pass
                try:
                    if self.aw.qmc.YOCTO_async[0]: # flag for channel 1 is ignored and only that of channel 0 is respected for both channels
                        try:
                            #### lock shared resources #####
                            self.YOCTOsemaphores[1].acquire(1)
                            now = libtime.time()
                            start_of_interval = now-self.aw.qmc.delay/1000
                            # 1. just consider async readings taken within the previous sampling interval
                            # and associate them with the (arrivial) time since the begin of that interval
                            valid_readings = [(r,t - start_of_interval) for (r,t) in self.YOCTOvalues[1] if t > start_of_interval]
                            if len(valid_readings) > 0:
                                # 2. calculate the value
                                # we take the median of all valid_readings weighted by the time of arrival, preferrring newer readings
                                readings = [r for (r,t) in valid_readings]
                                weights = [t for (r,t) in valid_readings]
                                probe2 = wquantiles.median(numpy.array(readings),numpy.array(weights))
                                # 3. consume old readings
                                self.YOCTOvalues[1] = []
#                            if len(self.YOCTOvalues[1]) > 0:
##                                probe2 = numpy.average(self.YOCTOvalues[1])
#                                probe2 = numpy.median(self.YOCTOvalues[1])
#                                self.YOCTOvalues[1] = self.YOCTOvalues[1][-round((self.aw.qmc.delay/self.aw.qmc.YOCTO_dataRate)):]
                        except:
                            self.YOCTOvalues[1] = []
                        finally:
                            if self.YOCTOsemaphores[1].available() < 1:
                                self.YOCTOsemaphores[1].release(1)
                        if probe2 == -1:
                            probe2 = self.YOCTOlastvalues[1]
                        else:
                            self.YOCTOlastvalues[1] = probe2
                    if probe2 == -1 and self.YOCTOchan2 and self.YOCTOchan2.isOnline():
                        probe2 = self.YOCTOchan2.get_currentValue()
                    if probe2 != -1:
                        # convert temperature scale
                        if self.aw.qmc.YOCTOchan2Unit == "C" and self.aw.qmc.mode == "F":
                            probe2 = fromCtoF(probe2)
                        elif self.aw.qmc.YOCTOchan2Unit == "F" and self.aw.qmc.mode == "C":
                            probe2 = fromFtoC(probe2)
                except Exception:
                    pass
            elif mode == 1:
                try:
                    if self.aw.qmc.YOCTO_async[0]:
                        try:
                            #### lock shared resources #####
                            self.YOCTOsemaphores[0].acquire(1)
                            if len(self.YOCTOvalues[0]) > 0:
#                                probe1 = numpy.average(self.YOCTOvalues[0])
                                probe1 = numpy.median(self.YOCTOvalues[0])
                                self.YOCTOvalues[0] = self.YOCTOvalues[0][-round((self.aw.qmc.delay/self.aw.qmc.YOCTO_dataRate)):]
                        except:
                            self.YOCTOvalues[0] = []
                        finally:
                            if self.YOCTOsemaphores[0].available() < 1:
                                self.YOCTOsemaphores[0].release(1)
                        if probe1 == -1:
                            probe1 = self.YOCTOlastvalues[0]
                        else:
                            self.YOCTOlastvalues[0] = probe1
                    if probe1 == -1 and self.YOCTOsensor and self.YOCTOsensor.isOnline():
                        probe1 = self.YOCTOsensor.get_currentValue()
                    if probe1 != -1:
                        # convert temperature scale
                        if self.aw.qmc.YOCTOchanUnit == "C" and self.aw.qmc.mode == "F":
                            probe1 = fromCtoF(probe1)
                        elif self.aw.qmc.YOCTOchanUnit == "F" and self.aw.qmc.mode == "C":
                            probe1 = fromFtoC(probe1)
                except Exception:
                    pass
            elif mode == 4:
                try:
                    if self.YOCTOchan1 and self.YOCTOchan1.isOnline():
                        probe1 = self.YOCTOchan1.get_currentValue()
                except:
                    pass
                try:
                    if self.YOCTOchan2 and self.YOCTOchan2.isOnline():
                        probe2 = self.YOCTOchan2.get_currentValue()
                except:
                    pass
            # apply the emissivity to the IR value
            if mode == 2 and probe1 != -1 and probe2 != -1:
                probe2 = self.IRtemp(self.aw.qmc.YOCTO_emissivity,probe2,probe1)
            return probe1, probe2
        except Exception as ex:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            try:
                if self.YOCTOthread is not None:
                    self.YOCTOthread.join()
                    self.YOCTOthread = None
                self.YOCTOsensor = None
                self.YOCTOchan1 = None
                self.YOCTOchan2 = None
                self.YOCOTtempIRavg = None
                self.YOCTOvalues = [[],[]]
                self.YOCTOlastvalues = [-1]*2
                YAPI.FreeAPI()
            except Exception:
                pass
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " YOCTOtemperatures() {0}").format(str(ex)),exc_tb.tb_lineno)
            return -1,-1

    # if chan is given, it is expected to be a string <s> send along the "CHAN;<s>" command on each call 
    # (not sending the unit or filter commands afterwards) and overwriting the self.arduinoETChannel and self.arduinoBTChannel settings
    def ARDUINOTC4temperature(self,chan=None):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            command = ""
            res = ""
            result = ""
            t1,t2 = 0.,0.
            if not self.SP.isOpen():
                self.openport()
                #libtime.sleep(1)
                #Reinitialize Arduino in case communication was interupted
                self.ArduinoIsInitialized = 0
            if self.SP.isOpen():
                #INITIALIZE (ONLY ONCE)
                if not self.ArduinoIsInitialized or chan is not None:
                    self.SP.reset_input_buffer()
                    self.SP.reset_output_buffer()
                    #build initialization command
                    if chan is None:
                        et_channel = self.arduinoETChannel
                        if et_channel == "None":
                            et_channel = "0"
                        bt_channel = self.arduinoBTChannel
                        if bt_channel == "None":
                            bt_channel = "0"
                        #If extra device +ArduinoTC4_XX present. read all 4 Ts
                        if 28 in self.aw.qmc.extradevices: # +ArduinoTC4_34
                            vals = ["1","2","3","4"]
                            try:
                                if self.arduinoETChannel and self.arduinoETChannel != "None" and self.arduinoETChannel in vals:
                                    vals.pop(vals.index(self.arduinoETChannel))
                                if self.arduinoBTChannel and self.arduinoBTChannel != "None" and self.arduinoBTChannel in vals:
                                    vals.pop(vals.index(self.arduinoBTChannel))
                            except:
                                pass
                            command = "CHAN;" + et_channel + bt_channel + vals[0] + vals[1]
                        else:
                        #no extra device +ArduinoTC4_XX present. reads ambient T, ET, BT
                            command = "CHAN;" + et_channel + bt_channel + "00"
                    else:
                        command = "CHAN;{}".format(chan)
                    #libtime.sleep(0.3)
                    self.SP.write(str2cmd(command + "\n"))       #send command
                    self.SP.flush()
                    libtime.sleep(.1)
                    result = self.SP.readline().decode('utf-8')[:-2]  #read
                    if (not len(result) == 0 and not result.startswith("#")):
                        raise Exception(QApplication.translate("Error Message","Arduino could not set channels",None))
                    elif result.startswith("#") and chan is None:
                        #OK. NOW SET UNITS
                        self.SP.reset_input_buffer()
                        self.SP.reset_output_buffer()
                        command = "UNITS;" + self.aw.qmc.mode + "\n"   #Set units
                        self.SP.write(str2cmd(command))
                        self.SP.flush()
                        libtime.sleep(.1)
                        result = self.SP.readline().decode('utf-8')[:-2]
                        if (not len(result) == 0 and not result.startswith("#")):
                            raise Exception(QApplication.translate("Error Message","Arduino could not set temperature unit",None))
                        else:
                            #OK. NOW SET FILTER
                            self.SP.reset_input_buffer()
                            self.SP.reset_output_buffer()
                            filt =  ",".join(map(str,self.aw.ser.ArduinoFILT))
                            command = "FILT;" + filt + "\n"   #Set filters
                            self.SP.write(str2cmd(command))
                            result = self.SP.readline().decode('utf-8')[:-2]
                            if (not len(result) == 0 and not result.startswith("#")):
                                raise Exception(QApplication.translate("Error Message","Arduino could not set filters",None))
                            else:
                                ### EVERYTHING OK  ###
                                self.ArduinoIsInitialized = 1
                        self.aw.sendmessage(QApplication.translate("Message","TC4 initialized",None))
                #READ TEMPERATURE
                command = "READ\n"  #Read command.
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                self.SP.write(str2cmd(command))
                self.SP.flush()
                libtime.sleep(.1)
                rl = self.SP.readline().decode('utf-8', 'ignore')[:-2]
                res = rl.rsplit(',')
                #response: list ["t0","t1","t2"]  with t0 = internal temp; t1 = ET; t2 = BT on "CHAN;1200" 
                #response: list ["t0","t1","t2","t3","t4"]  with t0 = internal temp; t1 = ET; t2 = BT, t3 = chan3, t4 = chan4 on "CHAN;1234" if ArduinoTC4_34 is configured
                # after PID_ON: + [,"Heater", "Fan", "SV"]
                if self.arduinoETChannel == "None":
                    t1 = -1
                else:
                    try:
                        t1 = float(res[1])
                    except Exception:
                        t1 = -1
                if self.arduinoBTChannel == "None":
                    t2 = -1
                else:
                    try:
                        t2 = float(res[2])
                    except Exception:
                        t2 = -1
                #if extra device +ArduinoTC4_34
                if 28 in self.aw.qmc.extradevices and chan is None:
                    #set the other values to extra temp variables
                    try:
                        self.aw.qmc.extraArduinoT1 = float(res[3])
                        self.aw.qmc.extraArduinoT2 = float(res[4])
                    except Exception:
                        self.aw.qmc.extraArduinoT1 = 0
                        self.aw.qmc.extraArduinoT2 = 0
                    if 32 in self.aw.qmc.extradevices: # +ArduinoTC4_56
                        try:
                            self.aw.qmc.extraArduinoT3 = float(res[5])
                            self.aw.qmc.extraArduinoT4 = float(res[6])
                        except Exception:
                            self.aw.qmc.extraArduinoT3 = 0
                            self.aw.qmc.extraArduinoT4 = 0
                    if 44 in self.aw.qmc.extradevices: # +ArduinoTC4_78
                        # report SV as extraArduinoT5
                        try:
                            self.aw.qmc.extraArduinoT5 = float(res[7])
                        except Exception:
                            self.aw.qmc.extraArduinoT5 = 0
                        # report Ambient Temperature as extraArduinoT6
                        try:
                            self.aw.qmc.extraArduinoT6 = float(res[0])
                        except Exception:
                            self.aw.qmc.extraArduinoT6 = 0
                else:
                    self.aw.qmc.extraArduinoT1 = -1.
                    self.aw.qmc.extraArduinoT2 = -1.
                    if 32 in self.aw.qmc.extradevices: # +ArduinoTC4_56
                        try:
                            self.aw.qmc.extraArduinoT3 = float(res[3])
                            self.aw.qmc.extraArduinoT4 = float(res[4])
                        except Exception:
                            self.aw.qmc.extraArduinoT3 = 0
                            self.aw.qmc.extraArduinoT4 = 0
                    else:
                        self.aw.qmc.extraArduinoT3 = -1.
                        self.aw.qmc.extraArduinoT4 = -1.
                    if 44 in self.aw.qmc.extradevices or 117 in self.aw.qmc.extradevices: # +ArduinoTC4_78 or +HB AT
                        # report SV as extraArduinoT5
                        try:
                            self.aw.qmc.extraArduinoT5 = float(res[5])
                        except Exception:
                            self.aw.qmc.extraArduinoT5 = 0
                        # report Ambient Temperature as extraArduinoT6
                        try:
                            self.aw.qmc.extraArduinoT6 = float(res[0])
                        except Exception:
                            self.aw.qmc.extraArduinoT6 = 0
                # overwrite temps by AT internal Ambient Temperature
                if self.aw.ser.arduinoATChannel != "None":
                    if self.aw.ser.arduinoATChannel == "T1":
                        t1 = float(res[0])
                    elif self.aw.ser.arduinoATChannel == "T2":
                        t2 = float(res[0])
                    elif (28 in self.aw.qmc.extradevices or (32 in self.aw.qmc.extradevices and not 28 in self.aw.qmc.extradevices)) and self.aw.ser.arduinoATChannel == "T3":
                        self.aw.qmc.extraArduinoT1 = float(res[0])
                    elif (28 in self.aw.qmc.extradevices or (32 in self.aw.qmc.extradevices and not 28 in self.aw.qmc.extradevices)) and self.aw.ser.arduinoATChannel == "T4":
                        self.aw.qmc.extraArduinoT2 = float(res[0])
                    elif (28 in self.aw.qmc.extradevices and 32 in self.aw.qmc.extradevices) and self.aw.ser.arduinoATChannel == "T5":
                        self.aw.qmc.extraArduinoT3 = float(res[0])
                    elif (28 in self.aw.qmc.extradevices and 32 in self.aw.qmc.extradevices) and self.aw.ser.arduinoATChannel == "T6":
                        self.aw.qmc.extraArduinoT4 = float(res[0])
                if chan is not None and len(res) == 4 and res[3] == "F":
                    # data is given in F, we convert it back to C
                    t1 = fromFtoC(t1)
                    t2 = fromFtoC(t2)
                return t1, t2
        except Exception as e:
            # self.closeport() # closing the port on error is to serve as the Arduino needs time to restart and has to be reinitialized!
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message", "Exception:",None) + " ser.ARDUINOTC4temperature(): {0}").format(str(e)),exc_tb.tb_lineno)
            return -1.,-1.
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("ArduinoTC4: " + settings + " || Tx = " + str(command) + " || Rx = " + str(res) + "|| Ts= %.2f, %.2f, %.2f, %.2f, %.2f, %.2f"%(t1,t2,self.aw.qmc.extraArduinoT1,self.aw.qmc.extraArduinoT2,self.aw.qmc.extraArduinoT3,self.aw.qmc.extraArduinoT4))


    def TEVA18Bconvert(self, seg):
        if seg == 0x7D:
            return 0
        elif seg == 0x05:
            return 1
        elif seg == 0x5B:
            return 2
        elif seg == 0x1F:
            return 3
        elif seg == 0x27:
            return 4
        elif seg == 0x3E:
            return 5
        elif seg == 0x7E:
            return 6
        elif seg == 0x15:
            return 7
        elif seg == 0x7F:
            return 8
        elif seg == 0x3F:
            return 9
        else:
            return -1

    def TEVA18Btemperature(self):
        try:
            r = ""
            run = 1
            counter = 0
            while(run):
                
                #MaWa
                #really interesting:
                #need this sleep. without artisan hungs after 20 to 40 seconds.
                #seems like iam running the loop forever, forever .... with sleep it is ok
                #seen this sometimes in communication between threads in C or C++. --> volatile problem?
                if counter > 0:
                    libtime.sleep(0.7)
                counter = counter + 1
                if not self.SP.isOpen():
                    self.openport()    
                    libtime.sleep(1)
                if self.SP.isOpen():
                    self.SP.reset_input_buffer() # self.SP.flushInput() # deprecated in v3
                    r = self.SP.read(14)
                    if len(r) != 14:
                        continue
#                    s200 = binascii.hexlify(r[0])
                    s201 = binascii.hexlify(r[1])
                    s202 = binascii.hexlify(r[2])
                    s203 = binascii.hexlify(r[3])
                    s204 = binascii.hexlify(r[4])
                    s205 = binascii.hexlify(r[5])
                    s206 = binascii.hexlify(r[6])
                    s207 = binascii.hexlify(r[7])
                    s208 = binascii.hexlify(r[8])
    #                s209 = binascii.hexlify(r[9])
    #                s210 = binascii.hexlify(r[10])
    #                s211 = binascii.hexlify(r[11])
    #                s212 = binascii.hexlify(r[12])
                    s213 = binascii.hexlify(r[13])
#                   t200 = int(s200,16)
                    t201 = int(s201,16)
                    t202 = int(s202,16)
                    t203 = int(s203,16)
                    t204 = int(s204,16)
                    t205 = int(s205,16)
                    t206 = int(s206,16)
                    t207 = int(s207,16)
                    t208 = int(s208,16)
    #                t209 = int(s209,16)
    #                t210 = int(s210,16)
    #                t211 = int(s211,16)
    #                t212 = int(s212,16)
                    t213 = int(s213,16)
                    # is meter in temp mode?
                    # first check byte order
                    if(((t213 & 0xf0) >> 4) != 14):
                        #ERROR try again .....
                        continue
#                    elif(((t213 & 0x0f) & 0x02) != 2):
#                        #ERROR
#                        # device seems not to be in temp mode, break here
#                        raise ValueError
                    # convert
                    bNegative = 0
                    iDivisor = 0
                    # first lets check the byte order
                    # seg1 bytes
                    if (((t201 & 0xf0) >> 4) == 2) and (((t202 & 0xf0) >> 4) == 3):
                        seg1 = ((t201 & 0x0f) << 4) + (t202 & 0x0f)
                    else:
                        continue
                    # seg2 bytes
                    if (((t203 & 0xf0) >> 4) == 4) and (((t204 & 0xf0) >> 4) == 5):
                        seg2 = ((t203 & 0x0f) << 4) + (t204 & 0x0f)
                    else:
                        continue
                    # seg3 bytes
                    if (((t205 & 0xf0) >> 4) == 6) and (((t206 & 0xf0) >> 4) == 7):
                        seg3 = ((t205 & 0x0f) << 4) + (t206 & 0x0f)
                    else:
                        continue
                    # seg4 bytes
                    if (((t207 & 0xf0) >> 4) == 8) and (((t208 & 0xf0) >> 4) == 9):
                        seg4 = ((t207 & 0x0f) << 4) + (t208 & 0x0f)
                    else:
                        continue
                    # is negative?
                    if (seg1 & 0x80):
                        bNegative = 1
                        seg1 = seg1 & ~0x80
                    # check divisor
                    if (seg2 & 0x80):
                        iDivisor = 1000.
                        seg2 = seg2 & ~0x80
                    elif (seg3 & 0x80):
                        iDivisor = 100.
                        seg3 = seg3 & ~0x80
                    elif (seg4 & 0x80):
                        iDivisor = 10.
                        seg4 = seg4 & ~0x80
                    iValue = 0
                    fReturn = 0
                    i = self.TEVA18Bconvert(seg1)
                    if (i < 0):
                        # recv nonsense, try again
                        continue
                    iValue = i * 1000
                    i = self.TEVA18Bconvert(seg2)
                    if (i < 0):
                        # recv nonsense, try again
                        continue
                    iValue = iValue + (i * 100)
                    i = self.TEVA18Bconvert(seg3)
                    if (i < 0):
                        # recv nonsense, try again
                        continue
                    iValue = iValue + (i * 10)
                    i = self.TEVA18Bconvert(seg4)
                    if (i < 0):
                        # recv nonsense, try again
                        continue
                    iValue = iValue + i
                    # what about the divisor?
                    if (iDivisor > 0):
                        fReturn = iValue / iDivisor
                    # is value negative?
                    if (fReturn):
                        if (bNegative):
                            fReturn = fReturn * (-1)
                    #ok seems we got valid value
                    # break loop here
                    run = 0
            #Since the meter reads only one temperature, send 0 as ET and fReturn as BT
            if fReturn:
                return 0.,fReturn    #  **** RETURN T HERE  ******
            else:
                raise ValueError
        except ValueError:
            #self.closeport()
            error = QApplication.translate("Error Message","Value Error:",None) + " ser.TEVA18Btemperature()"
            timez = str(QDateTime.currentDateTime().toString("hh:mm:ss.zzz"))    #zzz = miliseconds
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror(timez + " " + error,exc_tb.tb_lineno)
            return -1,-1 
        except Exception as ex:
            #self.closeport()
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " ser.TEVA18Btemperature() {0}").format(str(ex)),exc_tb.tb_lineno)
            return -1,-1
        finally:
            #note: logged chars should not be binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("TEVA18B: " + settings + " || Tx = " + "No command" + " || Rx = " + cmd2str(binascii.hexlify(r)))

    def HHM28multimeter(self):
        # This meter sends a continuos frame byte by byte. It only transmits data. It does not receive commands.
        # A frame is composed of 14 ordered bytes. A byte is represented bellow enclosed in "XX"
        # FRAME  = ["1A","2B","3C","4D","5E","6F","7G","8H","9I","10J","11K","12L","13M","14N"]
        # The first 4 bits of each byte are dedicated to identify the byte in the frame by using a number.
        # The last 4 bits of each byte are dedicated to carry Data. Depending on the byte number, the meaning of data changes.
        # Bytes 2,3,4,5,6,7,8,9 carry data bits that represent actual segments of the four LCD numbers of the meter display.
        # Bytes 1,10,11,12,13 carry data bits that represent other symbols like F (for Farad), u (for micro), M (for Mega), etc, of the meter display
        try:
            r, r2 = "",""
            frame = ""
            if not self.SP.isOpen():
                self.openport()
            if self.SP.isOpen():
                self.SP.reset_input_buffer() # self.SP.flushInput() # deprecated in v3
                self.SP.reset_output_buffer() # self.SP.flushOutput() # deprecated in v3
            #keep reading till the first byte of next frame (till we read an actual 1 in 1A )
            for i in range(28):  #any number > 14 will be OK
                r = self.SP.read(1)
                if r:
                    fb = (r[0] & 0xf0) >> 4
                    if fb == 1:
                        r2 = self.SP.read(13)   #read the remaining 13 bytes to get 14 bytes
                        break
                else:
                    raise ValueError(str("No Data received"))
##                if (r[0] & 0xf0) >> 4 == 1:
##                    r2 = self.SP.read(13)   #read the remaining 13 bytes to get 14 bytes
##                    break
            frame = r + r2
            #check bytes
            for i in range(14):
                number = fb = (frame[i] & 0xf0) >> 4
                if number != i+1:
                    #find device index
                    raise ValueError(str("Data corruption"))
            if len(frame) == 14:
                #extract data from frame in to a list containing the hex string values of the data
                data = []
                for i in range(14):
                    data.append(hex((frame[i] & 0x0f))[2:])
                #The four LCD digits are BC + DE + FG + HI   
                digits = [data[1]+data[2],data[3]+data[4],data[5]+data[6],data[7]+data[8]]
                #find sign 
                sign = ""   # +
                if (int(digits[0],16) & 0x80) >> 7:
                    sign = "-"
                #find location of decimal point
                for i in range(4):
                    if (int(digits[i],16) & 0x80) >> 7:
                        dec = i
                        digits[i] = hex(int(digits[i],16) & 0x7f)[2:]  #remove decimal point
                        if len(digits[i]) < 2:
                            digits[i] = "0" + digits[i]
                #find value from table
                table = {"00":" ","68":"L","7d":"0","05":"1","5b":"2","1f":"3",
                         "27":"4","3e":"5","7e":"6","15":"7","7f":"8","3f":"9"} 
                val = ""
                #some erros found in values: "38","5d",0A,etc
                for i in range(4):
                    if digits[i] in table:
                        val += table[digits[i]]
                    else:
                        raise ValueError(str("Data corruption"))
                number = ".".join((val[:dec],val[dec:]))  #add the decimal point
                #find symbols
                tablesymbols = [
                                ["AC","","",""],    #["AC","","Auto","RS232"]
                                ["u","n","k","diode"],
                                ["m","%","M","Beep"],
                                ["F","Ohm","Relative","Hold"],
                                ["A","V","Hz","Low Batt"]
                                ]
                masks = [0x08,0x04,0x02,0x01]
                nbytes = [0,9,10,11,12]
                symbols = ""
                for p in range(5):
                    for i in range(4):
                        if (int(data[nbytes[p]],16) & masks[i]):
                            symbols += " " + tablesymbols[p][i]
                return (sign + number), symbols
            else:
                raise ValueError(str("Needed 14 bytes but only received %i"%(len(frame))))
        except ValueError:
            #self.closeport()
            error  = QApplication.translate("Error Message","Value Error:",None) + " ser.HHM28multimeter()"
            timez = str(QDateTime.currentDateTime().toString("hh:mm:ss.zzz"))    #zzz = miliseconds
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror(timez + " " + error,exc_tb.tb_lineno)
            #find device index
            if self.aw.qmc.device == 23:
                if len(self.aw.qmc.temp1):
                    return str(self.aw.qmc.temp1[-1]),str(self.aw.qmc.temp2[-1])
                else:
                    return "0","0"
            else:
                index = self.aw.qmc.extradevices.index(23)
                if len(self.aw.qmc.extratemp1[i]):
                    return str(self.aw.qmc.extratemp1[index][-1]),str(self.aw.qmc.temp2[index][-1])
                else:
                    return "0","0"
        except Exception as ex:
            #self.closeport()
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " ser.HHM28multimeter() {0}").format(str(ex)),exc_tb.tb_lineno)
            return "0"""
        finally:
            #note: logged chars should not be binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("HHM28multimeter: " + settings + " || Tx = " + "No command" + " || Rx = " + str(frame))

    #sends a command to the ET/BT device. (used by eventaction to send serial command to e.g. Arduino)
    def sendTXcommand(self,command):
        try:
            #### lock shared resources #####
            self.aw.qmc.samplingsemaphore.acquire(1)
            if not self.SP.isOpen():
                self.openport()
                libtime.sleep(1)
                #Reinitialize Arduino in case communication was interrupted
                if self.aw.qmc.device == 19:
                    self.ArduinoIsInitialized = 0
            if self.SP.isOpen():
                self.SP.reset_input_buffer() # self.SP.flushInput() # deprecated in v3
                self.SP.reset_output_buffer() # self.SP.flushOutput() # deprecated in v3
                if (self.aw.qmc.device == 19 and not command.endswith("\n")):
                    command += "\n"
                self.SP.write(str2cmd(command))
                #self.SP.flush()
        except Exception as ex:
            #self.closeport() # do not close the serial port as reopening might take too long
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " ser.sendTXcommand() {0}").format(str(ex)),exc_tb.tb_lineno)
        finally:
            if self.aw.qmc.samplingsemaphore.available() < 1:
                self.aw.qmc.samplingsemaphore.release(1)
            #note: logged chars should not be binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
                self.aw.addserial("Serial Command: " + settings + " || Tx = " + command + " || Rx = " + "No answer needed")
                


#########################################################################
#############  Extra Serial Ports #######################################
#########################################################################

class extraserialport(object):
    def __init__(self, aw):
        self.aw = aw
        
        #default initial settings. They are changed by settingsload() at initiation of program acording to the device chosen
        self.comport = "/dev/cu.usbserial-FTFKDA5O"      #NOTE: this string should not be translated.
        self.baudrate = 19200
        self.bytesize = 8
        self.parity= 'N'
        self.stopbits = 1
        self.timeout = 0.4
        self.devicefunctionlist = {}
        self.device = None
        self.SP = None

    def confport(self):
        self.SP.port = self.comport
        self.SP.baudrate = self.baudrate
        self.SP.bytesize = self.bytesize
        self.SP.parity = self.parity
        self.SP.stopbits = self.stopbits
        self.SP.timeout = self.timeout

    def openport(self):
        try:
            self.confport()
            #open port
            if not self.SP.isOpen():
                self.SP.open()
        except Exception:
            self.SP.close()
#            libtime.sleep(0.7) # on OS X opening a serial port too fast after closing the port get's disabled
            error = QApplication.translate("Error Message","Serial Exception:",None)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror(error + " Unable to open serial port",exc_tb.tb_lineno)

    def closeport(self):
        if self.SP is not None:
            self.SP.close()
            libtime.sleep(0.3) # on OS X opening a serial port too fast after closing the port get's disabled

    # this one is called from scale and color meter code
    def connect(self,error=True):
        if self.SP is None:
            try:
                import serial  # @UnusedImport
                self.SP = serial.Serial()
            except Exception as e:
                if error:
                    _, _, exc_tb = sys.exc_info()
                    self.aw.qmc.adderror((QApplication.translate("Error Message","Serial Exception:",None) + " connect() {0}").format(str(e)),exc_tb.tb_lineno)
        if self.SP is not None:
            try:
                self.openport()
                if self.SP.isOpen():
                    return True
                else:
                    return False
            except Exception as e:
                if error:
                    _, _, exc_tb = sys.exc_info()
                    self.aw.qmc.adderror((QApplication.translate("Error Message","Serial Exception:",None) + " connect() {0}").format(str(e)),exc_tb.tb_lineno)
                return False
        else:
            return False

class scaleport(extraserialport):
    """ this class handles the communications with the scale"""
    def __init__(self,aw):
        super(scaleport, self).__init__(aw)
        
        #default initial settings. They are changed by settingsload() at initiation of program acording to the device chosen
        self.comport = "/dev/cu.usbserial-FTFKDA5O"      #NOTE: this string should not be translated.
        self.baudrate = 19200
        self.bytesize = 8
        self.parity= 'N'
        self.stopbits = 1
        self.timeout = 0.2
        self.devicefunctionlist = {
            "None" : None,
            "KERN NDE" : self.readKERN_NDE,
            "acaia" : self.readAcaia,
            #"Shore 930" : self.readShore930,
        }

    def closeport(self):
        if self.device == "acaia":
            # disconnect from acaia scale
            try:
                if self.SP.isOpen():
                    self.SP.write(str2cmd('BTDS\r\n'))
            except Exception:
                pass
        super(scaleport, self).closeport()
        
    # returns one of weight (g), density (g/l), or moisture (%).  Others return -1.
    def readWeight(self,scale_weight=None):
        if scale_weight != None:
            return scale_weight,-1,-1
        else:
            if self.device is not None and self.device != "None" and self.device != "" and self.device != "acaia":
                wei,den,moi = self.devicefunctionlist[self.device]()
                if moi is not None and moi > -1:
                    return -1, -1, self.aw.float2float(moi)
                elif den is not None and den > -1:
                    return -1, self.aw.float2float(den), -1
                elif wei is not None and wei > -1:
                    return self.aw.float2float(wei), -1, -1
                else:
                    return -1,-1,-1
            else:
                return -1,-1,-1
            
    def readLine(self):
        return str(self.SP.readline().decode('ascii'))

    # replaced by BLE direct implementation
    def readAcaia(self):
        pass

    def readKERN_NDE(self):
        try:
            if not self.SP:
                self.connect()
            if self.SP:
                if not self.SP.isOpen():
                    self.openport()
                if self.SP.isOpen():
                    #self.SP.write(str2cmd('s')) # only stable
                    self.SP.write(str2cmd('w')) # any weight
                    v = self.SP.readline()
                    if len(v) == 0:
                        return -1,-1,-1
                    sa = v.decode('ascii').split('g')
                    if len(sa) == 2:
                        return int(sa[0].replace(" ", "")), -1, -1
                    else:
                        # some times the unit is just missing, we assume it is g
                        sa = v.decode('ascii').split('\r\n')
                        if len(sa) == 2:
                            return int(sa[0].replace(" ", "")),-1,-1
                        return -1, -1, -1
        except Exception:
            return -1, -1, -1

    def readShore930(self):
        try:
            if not self.SP:
                self.connect()
            if self.SP:
                if not self.SP.isOpen():
                    self.openport()
                if self.SP.isOpen():
                    line1 = self.SP.readline()
                    weight = re.search(r'Current Weight:',str(line1))
                    if weight:                    
                        w = re.findall(r'([0-9\.]+)',str(line1))
                        if len(w) == 1:
                            return toFloat(w[0]),-1,-1
                        else:
                            return -1,-1,-1

                    density = re.search(r'Test Weight',str(line1))
                    if density:
                        line2 = self.SP.readline()
                        d = re.findall(r'[0-9\.\-]+',str(line2))
                        if len(d) == 1:
                            den = toFloat(d[0]) *12.8718597   # convert from LBS/BU to g/
                            return -1,toFloat(den),-1
                        else:
                            return -1,-1,-1

                    moisture = re.search(r'Beans',str(line1))
                    if moisture:
                        line2 = self.SP.readline()
                        m = re.findall(r'[0-9\.\-]+',str(line2))
#                        line3 = self.SP.readline() # unused!
                        if len(m) == 1:
                            return -1,-1,toFloat(m[0])
                        else:
                            return -1,-1,-1

                    else:
                        return -1,-1,-1
        except Exception:
            return -1,-1,-1


class colorport(extraserialport):
    """ this class handles the communications with the color meter"""
    def __init__(self,aw):
        super(colorport, self).__init__(aw)
        
        #default initial settings. They are changed by settingsload() at initiation of program acording to the device chosen
        self.comport = "/dev/cu.usbserial-FTFKDA5O"      #NOTE: this string should not be translated.
        self.baudrate = 115200
        self.bytesize = 8
        self.parity= 'N'
        self.stopbits = 1
        self.timeout = 2
        self.devicefunctionlist = {
            "None" : None,
            "Tiny Tonino" : self.readTonino,
            "Classic Tonino" : self.readTonino
        }

    # returns color as int or -1 if something went wrong
    def readColor(self):
        if self.device is not None and self.device != "None" and self.device != "":
            return self.devicefunctionlist[self.device]()
        else:
            return -1

    def readline_terminated(self,eol=b'\r'):
        leneol = len(eol)
        line = bytearray()
        while True:
            c = self.SP.read(1)
            if c:
                line += c
                if line[-leneol:] == eol:
                    break
            else:
                break
        return bytes(line)

    def readTonino(self,retry=2):
        try:
            if not self.SP:
                self.connect()
                libtime.sleep(2)
                # put Tonino into PC mode on first connect
                self.SP.write(str2cmd('\nTONINO\n'))
                #self.SP.flush()
                self.readline_terminated(b'\n')
            if self.SP:
                if not self.SP.isOpen():
                    self.openport()
                if self.SP.isOpen():
                    self.SP.reset_input_buffer()
                    self.SP.reset_output_buffer()
                    self.SP.write(str2cmd('\nSCAN\n'))
                    #self.SP.flush()
                    v = self.readline_terminated(b'\n').decode('ascii')
                    if "SCAN" in v:
                        n = int(v.split(":")[1]) # response should have format "SCAN:128"
                        return n
                    elif retry > 0:
                        return self.readTonino(self,retry-1)
                    else:
                        return -1
        except Exception:
            return -1
