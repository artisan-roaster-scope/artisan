#
# ABOUT
# Hottop 2k+ support for Artisan

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
# Marko Luther, 2023

import multiprocessing as mp
from multiprocessing.sharedctypes import Value
from ctypes import c_bool, c_double
import serial
import time
import logging
from typing import Optional, Any
from typing_extensions import Final  # Python <=3.7

_log: Final[logging.Logger] = logging.getLogger(__name__)

process = None
control = False # Hottop under control?

# serial port configurations
SP = None

# safety cut-off BT temperature
BTcutoff = 220 # 220C = 428F (was 212C/413F before)
BTleaveControl = 180 # 180C = 350F; the BT below which the control can be released; above the control cannot be released to avoid sudden stop at high temperatures

xCONTROL:Optional[Any] = None # False: just logging; True: logging+control
xBT:Optional[Any] = None
xET:Optional[Any] = None
xHEATER:Optional[Any] = None
xFAN:Optional[Any] = None
xMAIN_FAN:Optional[Any] = None
xSOLENOID:Optional[Any] = None # False: closed; True: open
xDRUM_MOTOR:Optional[Any] = None
xCOOLING_MOTOR:Optional[Any] = None
xCHAFF_TRAY:Optional[Any] = None
# set values
xSET_HEATER:Optional[Any] = None
xSET_FAN:Optional[Any] = None
xSET_MAIN_FAN:Optional[Any] = None
xSET_SOLENOID:Optional[Any] = None # False: closed; True: open
xSET_DRUM_MOTOR:Optional[Any] = None
xSET_COOLING_MOTOR:Optional[Any] = None

def hex2int(h1,h2=None):
    if h2:
        return int(h1*256 + h2)
    return int(h1)

def openport(p):
    try:
        if p is not None and not p.isOpen():
            p.open()
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)

def closeport(p):
    try:
        if p is not None and p.isOpen():
            p.close()
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)

def gettemperatures(p,retry=True):
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
        openport(p)
        if p.isOpen():
            #p.flushInput() # deprecated in v3
            p.reset_input_buffer()
            #p.flushOutput() # deprecated in v3
            p.reset_output_buffer()
            r = p.read(36)
#            print(len(r),"".join("\\x%02x" % ord(i) for i in r))
            if len(r) != 36:
                closeport(p)
                if retry: # we retry once
                    return gettemperatures(p,retry=False)
            else:
                P0 = hex2int(r[0])
                P1 = hex2int(r[1])
                chksum = sum(hex2int(c) for c in r[:35]) & 0xFF
                P35 = hex2int(r[35])
                if P0 != 165 or P1 != 150 or chksum != P35:
                    closeport(p)
                    if retry: # we retry once
                        return gettemperatures(p,retry=False)
                else:
                    #VERSION = hex2int(r[4]) # => 1 (first released version)
                    HEATER = hex2int(r[10]) # 0-100
                    FAN = hex2int(r[11])
                    MAIN_FAN = hex2int(r[12]) # 0-10
                    ET = hex2int(r[23],r[24]) # in C
                    BT = hex2int(r[25],r[26]) # in C
                    SOLENOID = hex2int(r[16]) # 0: closed, 1: open
                    DRUM_MOTOR = hex2int(r[17])
                    COOLING_MOTOR = hex2int(r[18])
                    CHAFF_TRAY = hex2int(r[19])
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)
    return BT, ET, HEATER, FAN, MAIN_FAN, SOLENOID, DRUM_MOTOR, COOLING_MOTOR, CHAFF_TRAY

def doWork(interval:float, comport, baudrate, bytesize, parity, stopbits, timeout,
        aBT, aET, aHEATER, aFAN, aMAIN_FAN, aSOLENOID, aDRUM_MOTOR, aCOOLING_MOTOR, aCHAFF_TRAY,
        aSET_HEATER, aSET_FAN, aSET_MAIN_FAN, aSET_SOLENOID, aSET_DRUM_MOTOR, aSET_COOLING_MOTOR, aCONTROL):
    global SP # pylint: disable=global-statement
    SP = serial.Serial()
    # configure serial port
    SP.port = comport
    SP.baudrate = baudrate
    SP.bytesize = bytesize
    SP.parity = parity
    SP.stopbits = stopbits
    SP.timeout = timeout
    while True:
        # logging part
        BT, ET, HEATER, FAN, MAIN_FAN, SOLENOID, DRUM_MOTOR, COOLING_MOTOR, CHAFF_TRAY = gettemperatures(SP)
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
            # safety cut at BT=220C/428F (was 212C/413F before)
            if BTcutoff <= BT:
                # set main fan to maximum (set to 10), turn off heater (set to 0), open solenoid for eject, turn on drum and stirrer (all set to 1)
                aSET_HEATER.value = 0
                #aSET_FAN.value = 10
                aSET_MAIN_FAN.value = 10
                aSET_SOLENOID.value = 1
                aSET_DRUM_MOTOR.value = 1
                aSET_COOLING_MOTOR.value = 1
            sendControl(SP,aHEATER, aFAN, aMAIN_FAN, aSOLENOID, aDRUM_MOTOR, aCOOLING_MOTOR,
                        aSET_HEATER, aSET_FAN, aSET_MAIN_FAN, aSET_SOLENOID, aSET_DRUM_MOTOR, aSET_COOLING_MOTOR)

        time.sleep(interval)


# Control processing

def sendControl(p,aHEATER, aFAN, aMAIN_FAN, aSOLENOID, aDRUM_MOTOR, aCOOLING_MOTOR,
        aSET_HEATER, aSET_FAN, aSET_MAIN_FAN, aSET_SOLENOID, aSET_DRUM_MOTOR, aSET_COOLING_MOTOR):
    try:
        openport(SP)
        if p.isOpen():
            cmd = HOTTOPcontrol(aHEATER, aFAN, aMAIN_FAN, aSOLENOID, aDRUM_MOTOR, aCOOLING_MOTOR,
                    aSET_HEATER, aSET_FAN, aSET_MAIN_FAN, aSET_SOLENOID, aSET_DRUM_MOTOR, aSET_COOLING_MOTOR)
#            print("".join("\\x%02x" % ord(i) for i in cmd))
            #p.flushInput() # deprecated in v3
            p.reset_input_buffer()
            #p.flushOutput() # deprecated in v3
            p.reset_output_buffer()
            p.write(cmd)
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)

# prefers set_value, and returns get_value if set_value is -1. If both are -1, returns 0
def newValue(set_value,get_value):
    if set_value != -1:
        return set_value
    if get_value != -1:
        return get_value
    return 0

def HOTTOPcontrol(aHEATER, aFAN, aMAIN_FAN, aSOLENOID, aDRUM_MOTOR, aCOOLING_MOTOR,
        aSET_HEATER, aSET_FAN, aSET_MAIN_FAN, aSET_SOLENOID, aSET_DRUM_MOTOR, aSET_COOLING_MOTOR):
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
    cmd[35] = sum(list(cmd[:35])) & 0xFF # checksum
    return bytes(cmd)




# External Interface

def takeHottopControl():
    if xCONTROL is not None:
        xCONTROL.value = True
        return True
    return False

def releaseHottopControl():
    if xCONTROL is not None and xBT is not None and xBT.value < BTleaveControl:
        xCONTROL.value = False
        return True
    return False

# BT/ET : double
# heater : int(0-100)
# main_fan : 0-100 (will be converted from the internal int(0-10))
# solenoid : bool
def getHottop():
    if xBT is not None and xET is not None and xHEATER is not None and xMAIN_FAN is not None:
        return xBT.value, xET.value, xHEATER.value, xMAIN_FAN.value * 10
    return -1, -1, 0, 0


# heater : int(0-100)
# fan, main_fan : int(0-100) (will be converted to the internal int(0-10))
# solenoid, drum_motor, cooling_motor : bool (will be converted to the internal 0 or 1)
# all parameters are optional and default to None (meanging: don't change value)
def setHottop(heater:Optional[int]=None,fan:Optional[int]=None,main_fan:Optional[int]=None,solenoid:Optional[int]=None,drum_motor:Optional[int]=None,cooling_motor:Optional[int]=None):
    if xCONTROL and xCONTROL.value:
        if heater is not None and xSET_HEATER is not None:
            xSET_HEATER.value = int(heater)
        if fan is not None and xSET_FAN is not None:
            xSET_FAN.value = int(round(fan / 10.))
        if main_fan is not None and xSET_MAIN_FAN is not None:
            xSET_MAIN_FAN.value = int(round(main_fan / 10.))
        if solenoid is not None and xSET_SOLENOID is not None:
            xSET_SOLENOID.value = int(solenoid)
        if drum_motor is not None and xSET_DRUM_MOTOR is not None:
            xSET_DRUM_MOTOR.value = int(drum_motor)
        if cooling_motor is not None and xSET_COOLING_MOTOR is not None:
            xSET_COOLING_MOTOR.value = int(cooling_motor)


# interval has to be smaller than 1 (= 1sec)
def startHottop(interval:float=1.0,comport='COM4',baudrate=115200,bytesize=8,parity='N',stopbits=1,timeout=0.5):
    global process, xCONTROL, xBT, xET, xHEATER, xFAN, xMAIN_FAN, xSOLENOID, xDRUM_MOTOR, xCOOLING_MOTOR, xCHAFF_TRAY, \
        xSET_HEATER, xSET_FAN, xSET_MAIN_FAN, xSET_SOLENOID, xSET_DRUM_MOTOR, xSET_COOLING_MOTOR # pylint: disable=global-statement
    try:
        if process:
            return False
        stopHottop() # we stop an already running process to ensure that only one is running
        lock = mp.Lock()
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
        # variables to write to the Hottop

        process = mp.Process(target=doWork, args=(interval,comport,baudrate,bytesize,parity,stopbits,timeout,
            xBT, xET, xHEATER, xFAN, xMAIN_FAN, xSOLENOID, xDRUM_MOTOR, xCOOLING_MOTOR, xCHAFF_TRAY, \
            xSET_HEATER, xSET_FAN, xSET_MAIN_FAN, xSET_SOLENOID, xSET_DRUM_MOTOR, xSET_COOLING_MOTOR, xCONTROL))
        process.start()
        return True
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)
        return False

def stopHottop():
    global process # pylint: disable=global-statement
    if process:
        process.terminate()
        process.join()
        process = None

def isHottopLoopRunning():
    return bool(process)
