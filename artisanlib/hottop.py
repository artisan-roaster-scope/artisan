#!/usr/bin/env python
from multiprocessing import Process, Lock
from multiprocessing.sharedctypes import Value
from ctypes import c_bool, c_double
import serial

import time
import sys
import binascii

process = None
control = False # Hottop under control?

# serial port configurations
SP = None

xCONTROL = None # False: just logging; True: logging+control
xBT = None
xET = None
xHEATER = None
xFAN = None
xMAIN_FAN = None
xSOLENOID = None # False: closed; True: open
xDRUM_MOTOR = None
xCOOLING_MOTOR = None
xCHAFF_TRAY = None
# set values
xSET_HEATER = None
xSET_FAN = None
xSET_MAIN_FAN = None
xSET_SOLENOID = None # False: closed; True: open
xSET_DRUM_MOTOR = None
xSET_COOLING_MOTOR = None
xSET_CHAFF_TRAY = None

if sys.version < '3':
    def hex2int(h1,h2=""):
        return int(binascii.hexlify(h1+h2),16)
else:
    def hex2int(h1,h2=None):
        if h2:
            return int(h1*256 + h2)
        else:
            return int(h1)
        
def openport():
    try:
        if not SP.isOpen():
            SP.open()
    except Exception:
        pass
        
def closeport():
    try:
        if SP == None and SP.isOpen():
            SP.close()
    except Exception:
        pass
        
def gettemperatures(retry=True):
    BT = -1
    ET = -1
    HEATER = -1
    FAN = -1
    MAIN_FAN = -1
    SOLENOID = -1
    DRUM_MOTOR = -1
    COOLING_MOTOR = -1
    CHAFF_TRAY = -1
    try:
        openport()
        if SP.isOpen():
            SP.flushInput()
            SP.flushOutput()
            r = SP.read(36)
#            print(len(r),"".join("\\x%02x" % ord(i) for i in r))
            if len(r) != 36:
                closeport()
                if retry: # we retry once
                    return gettemperatures(retry=False)
            else:
                P0 = hex2int(r[0])
                P1 = hex2int(r[1])
                chksum = sum([hex2int(c) for c in r[:35]]) & 0xFF 
                P35 = hex2int(r[35])
                if P0 != 165 or P1 != 150 or P35 != chksum:
                    closeport()
                    if retry: # we retry once
                        return gettemperatures(retry=False)
                else:
                    #VERSION = hex2int(r[4])
                    HEATER = hex2int(r[10]) # 0-100
                    FAN = hex2int(r[11])
                    MAIN_FAN = hex2int(r[12]) # 0-10
                    ET = hex2int(r[23],r[24]) # in C
                    BT = hex2int(r[25],r[26]) # in C
                    SOLENOID = hex2int(r[16]) # 0: closed, 1: open
                    DRUM_MOTOR = hex2int(r[17])
                    COOLING_MOTOR = hex2int(r[18])
                    CHAFF_TRAY = hex2int(r[19])
    except Exception:
        pass
    return BT, ET, HEATER, FAN, MAIN_FAN, SOLENOID, DRUM_MOTOR, COOLING_MOTOR, CHAFF_TRAY

def doWork(interval, aBT, aET, aHEATER, aFAN, aMAIN_FAN, aSOLENOID, aDRUM_MOTOR, aCOOLING_MOTOR, aCHAFF_TRAY,
        aSET_HEATER, aSET_FAN, aSET_MAIN_FAN, aSET_SOLENOID, aSET_DRUM_MOTOR, aSET_COOLING_MOTOR, aSET_CHAFF_TRAY, aCONTROL):
    while True:
        # logging part
        BT, ET, HEATER, FAN, MAIN_FAN, SOLENOID, DRUM_MOTOR, COOLING_MOTOR, CHAFF_TRAY = gettemperatures()
        if BT != -1:
            if aBT.value == -1:
                aBT.value = float(BT)
            else:
                # we compute a running average to compensate for the low precisions
                aBT.value = (aBT.value + float(BT)) / 2.0
        if ET != -1:
            if aET.value == -1:
                aET.value = ET
            else:
                # we compute a running average to compensate for the low precisions
                aET.value = (aET.value + float(ET)) / 2.0
        if HEATER != -1:
            aHEATER.value = HEATER
        if FAN != -1:
            aFAN.value = FAN
        if MAIN_FAN != -1:
            aMAIN_FAN.value = MAIN_FAN
        if SOLENOID != -1:
            aSOLENOID.value = SOLENOID
        if DRUM_MOTOR != -1:
            aDRUM_MOTOR.value = DRUM_MOTOR
        if COOLING_MOTOR != -1:
            aCOOLING_MOTOR.value = COOLING_MOTOR
        if CHAFF_TRAY != -1:
            aCHAFF_TRAY.value = xCHAFF_TRAY

        # control part
        if aCONTROL.value:
            sendControl(aHEATER, aFAN, aMAIN_FAN, aSOLENOID, aDRUM_MOTOR, aCOOLING_MOTOR, aCHAFF_TRAY,
                    aSET_HEATER, aSET_FAN, aSET_MAIN_FAN, aSET_SOLENOID, aSET_DRUM_MOTOR, aSET_COOLING_MOTOR, aSET_CHAFF_TRAY)            
            
        time.sleep(interval)
        # needs a flag to know if control commands should be send
        # needs a different sleep in control mode
        # how often to "read" data? At the same speed as the "send" commands? This is a lot!
      

# Control processing 

def sendControl(aHEATER, aFAN, aMAIN_FAN, aSOLENOID, aDRUM_MOTOR, aCOOLING_MOTOR, aCHAFF_TRAY,
        aSET_HEATER, aSET_FAN, aSET_MAIN_FAN, aSET_SOLENOID, aSET_DRUM_MOTOR, aSET_COOLING_MOTOR, aSET_CHAFF_TRAY):
    try:
        openport()
        if SP.isOpen():
            cmd = HOTTOPcontrol(aHEATER, aFAN, aMAIN_FAN, aSOLENOID, aDRUM_MOTOR, aCOOLING_MOTOR, aCHAFF_TRAY,
                    aSET_HEATER, aSET_FAN, aSET_MAIN_FAN, aSET_SOLENOID, aSET_DRUM_MOTOR, aSET_COOLING_MOTOR, aSET_CHAFF_TRAY)
#            print("".join("\\x%02x" % ord(i) for i in cmd))
            SP.flushInput()
            SP.flushOutput()
            SP.write(cmd) 
    except Exception:
#        import traceback
#        import sys
#        traceback.print_exc(file=sys.stdout)
        pass
            
# prefers set_value, and returns get_value if set_value is -1. If both are -1, returns 0
def newValue(set_value,get_value):
    if set_value != -1:
        return set_value
    elif get_value != -1:
        return get_value
    else:
        return 0

def HOTTOPcontrol(aHEATER, aFAN, aMAIN_FAN, aSOLENOID, aDRUM_MOTOR, aCOOLING_MOTOR, aCHAFF_TRAY,
        aSET_HEATER, aSET_FAN, aSET_MAIN_FAN, aSET_SOLENOID, aSET_DRUM_MOTOR, aSET_COOLING_MOTOR, aSET_CHAFF_TRAY):
    cmd = bytearray([0x00]*36)
    cmd[0] = 0xA5
    cmd[1] = 0x96
    cmd[2] = 0xB0
    cmd[3] = 0xA0
    cmd[4] = 0x01
    cmd[5] = 0x01
    cmd[6] = 0x24
    cmd[10] = newValue(aSET_HEATER.value,aHEATER.value)
    cmd[11] = newValue(aSET_FAN.value,aFAN.value)
    cmd[12] = newValue(aSET_MAIN_FAN.value,aMAIN_FAN.value)
    cmd[16] = newValue(aSET_SOLENOID.value,aSOLENOID.value)
    cmd[17] = newValue(aSET_DRUM_MOTOR.value,aDRUM_MOTOR.value)
    cmd[18] = newValue(aSET_COOLING_MOTOR.value,aCOOLING_MOTOR.value)
    cmd[35] = sum([b for b in cmd[:35]]) & 0xFF # checksum
    return bytes(cmd)




# External Interface
        
def takeHottopControl():
    if xCONTROL:
        xCONTROL.value = True
        return True
    else:
        return False
    
def releaseHottopControl():
    if xCONTROL:
        xCONTROL.value = False
        return True
    else:
        return False

# BT/ET : double
# heater : int(0-100)
# main_fan : 0-100 (will be converted from the internal int(0-10))
# solenoid : bool
def getHottop():
    if xBT != None and xET != None and xHEATER != None and xMAIN_FAN != None and xSOLENOID != None:
        return xBT.value, xET.value, xHEATER.value, xMAIN_FAN.value * 10, bool(xSOLENOID.value)
    else:
        return -1, -1, 0, 0, False


# heater : int(0-100)
# fan, main_fan : int(0-100) (will be converted to the internal int(0-10))
# solenoid, drum_motor, cooling_motor, chaff_tray : bool (will be converted to the internal 0 or 1)
# all parameters are optional and default to None (meanging: don't change value)
def setHottop(heater=None,fan=None,main_fan=None,solenoid=None,drum_motor=None,cooling_motor=None,chaff_tray=None):
    if heater != None:
        xSET_HEATER.value = int(heater)
    if fan != None:
        xSET_FAN.value = int(round(fan / 10.))
    if main_fan != None:
        xSET_MAIN_FAN.value = int(round(main_fan / 10.))
    if solenoid != None:
        xSET_SOLENOID.value = int(solenoid)
    if drum_motor != None:
        xSET_DRUM_MOTOR.value = int(drum_motor)
    if cooling_motor != None:
        xSET_COOLING_MOTOR.value = int(cooling_motor)
    if chaff_tray != None:
        xSET_CHAFF_TRAY.value = int(chaff_tray)


# interval has to be smaller than 1 (= 1sec)
def startHottop(interval=1,comport="COM4",baudrate=115200,bytesize=8,parity='N',stopbits=1,timeout=1):
    global process, SP, xCONTROL, xBT, xET, xHEATER, xFAN, xMAIN_FAN, xSOLENOID, xDRUM_MOTOR, xCOOLING_MOTOR, xCHAFF_TRAY, \
        xSET_HEATER, xSET_FAN, xSET_MAIN_FAN, xSET_SOLENOID, xSET_DRUM_MOTOR, xSET_COOLING_MOTOR, xSET_CHAFF_TRAY
    try:
        SP = serial.Serial()
        # configure serial port
        SP.setPort(comport)
        SP.setBaudrate(baudrate)
        SP.setByteSize(bytesize)
        SP.setParity(parity)
        SP.setStopbits(stopbits)
        SP.setTimeout(timeout)
        lock = Lock()
        xCONTROL = Value(c_bool, False, lock=lock)
        # variables to read from the Hottop
        xBT = Value(c_double, -1.0, lock=lock)
        xET = Value(c_double, -1.0, lock=lock)
        xHEATER = Value('i', -1, lock=lock)
        xFAN = Value('i', -1, lock=lock)
        xMAIN_FAN = Value('i', -1, lock=lock)
        xSOLENOID = Value(c_bool, False, lock=lock)
        xDRUM_MOTOR = Value(c_bool, False, lock=lock)
        xCOOLING_MOTOR = Value(c_bool, False, lock=lock)
        xCHAFF_TRAY = Value(c_bool, False, lock=lock)
        # set variables to write to the Hottop
        xSET_HEATER = Value('i', -1, lock=lock)
        xSET_FAN = Value('i', -1, lock=lock)
        xSET_MAIN_FAN = Value('i', -1, lock=lock)
        xSET_SOLENOID = Value('i', -1, lock=lock)
        xSET_DRUM_MOTOR = Value('i', -1, lock=lock)
        xSET_COOLING_MOTOR = Value('i', -1, lock=lock)
        xSET_CHAFF_TRAY = Value('i', -1, lock=lock)
        # variables to write to the Hottop
        
        process = Process(target=doWork, args=(interval, xBT, xET, xHEATER, xFAN, xMAIN_FAN, xSOLENOID, xDRUM_MOTOR, xCOOLING_MOTOR, xCHAFF_TRAY, \
            xSET_HEATER, xSET_FAN, xSET_MAIN_FAN, xSET_SOLENOID, xSET_DRUM_MOTOR, xSET_COOLING_MOTOR, xSET_CHAFF_TRAY, xCONTROL))
        process.start()
        return True
    except Exception:
        return False

def stopHottop():
    global process
    if process:
        process.terminate()
        process.join()
        process = None
