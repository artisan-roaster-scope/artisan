import time
import platform
import struct
import os

import artisanlib.util
from artisanlib.suppress_errors import suppress_stdout_stderr

from PyQt5.QtCore import QSemaphore
from PyQt5.QtWidgets import QApplication


class s7port(object):
    def __init__(self,sendmessage,adderror,addserial):
        self.sendmessage = sendmessage # function to create an Artisan message to the user in the message line
        self.adderror = adderror # signal an error to the user
        self.addserial = addserial # add to serial log
        
        self.readRetries = 1
        self.channels = 8 # maximal number of S7 channels
        self.host = '127.0.0.1' # the TCP host
        self.port = 102 # the TCP port
        self.rack = 0 # 0,..,7
        self.slot = 0 # 0,..,31
                
        self.lastReadResult = 0 # this is set by eventaction following some custom button/slider S/ actions with "read" command
        
        self.area = [0]*self.channels
        self.db_nr = [1]*self.channels
        self.start = [0]*self.channels
        self.type = [0]*self.channels
        self.mode = [0]*self.channels # temp mode is an int here, 0:__,1:C,2:F (this is different than other places)
        self.div = [0]*self.channels
        
        self.PID_area = 0
        self.PID_db_nr = 0
        self.PID_SV_register = 0
        self.PID_p_register = 0
        self.PID_i_register = 0
        self.PID_d_register = 0
        self.PID_ON_action = ""
        self.PID_OFF_action = ""
        self.SVmultiplier = 0
        self.PIDmultiplier = 0
        
        self.COMsemaphore = QSemaphore(1)
        
        self.areas = [
            0x81, # PE
            0x82, # PA
            0x83, # MK
            0x1C, # CT
            0x1D, # TM
            0x84, # DB
        ]
        
        self.plc = None
        self.commError = False # True after a communication error was detected and not yet cleared by receiving proper data

################
# conversion methods copied from s7:util.py

    def set_int(self,_bytearray, byte_index, _int):
        """
        Set value in bytearray to int
        """
        # make sure were dealing with an int
        _int = int(_int)
        _bytes = struct.unpack('2B', struct.pack('>h', _int))
        _bytearray[byte_index:byte_index + 2] = _bytes
        
    def get_int(self,_bytearray, byte_index):
        """
        Get int value from bytearray.
    
        int are represented in two bytes
        """
        data = _bytearray[byte_index:byte_index + 2]
        data[1] = data[1] & 0xFF # added to fix a conversion problem: see https://github.com/gijzelaerr/python-snap7/issues/101
        value = struct.unpack('>h', struct.pack('2B', *data))[0]
        return value
        
    def set_real(self,_bytearray, byte_index, real):
        """
        Set Real value
    
        make 4 byte data from real
    
        """
        real = float(real)
        real = struct.pack('>f', real)
        _bytes = struct.unpack('4B', real)
        for i, b in enumerate(_bytes):
            _bytearray[byte_index + i] = b
        
    def get_real(self,_bytearray, byte_index):
        """
        Get real value. create float from 4 bytes
        """
        x = _bytearray[byte_index:byte_index + 4]
        real = struct.unpack('>f', struct.pack('4B', *x))[0]
        return real
        
################

        
    def setPID(self,p,i,d,PIDmultiplier):
        if self.PID_area and not (self.PID_p_register == self.PID_i_register == self.PID_d_register == 0):
            multiplier = 1.
            if PIDmultiplier == 1:
                PIDmultiplier = 10.
            elif PIDmultiplier == 2:
                multiplier = 100.
            self.writeInt(self.PID_area-1,self.PID_db_nr,self.PID_p_register,p*multiplier)
            self.writeInt(self.PID_area-1,self.PID_area,self.PID_db_nr,self.PID_i_register,i*multiplier)
            self.writeInt(self.PID_area-1,self.PID_area,self.PID_db_nr,self.PID_d_register,d*multiplier)
        
    def setTarget(self,sv,SVmultiplier):
        if self.PID_area:
            multiplier = 1.
            if SVmultiplier == 1:
                multiplier = 10.
            elif SVmultiplier == 2:
                multiplier = 100.
            self.writeInt(self.PID_area-1,self.PID_db_nr,self.PID_SV_register,int(round(sv*multiplier)))
                    
    def isConnected(self):
        return not (self.plc is None) and self.plc.get_connected()
        
    def disconnect(self):
        if self.isConnected():
            try:
                self.plc.disconnect()
                self.plc.destroy()
                self.plc = None
            except Exception:
                pass
        
    def connect(self):
        from artisanlib.s7client import S7Client
        from snap7.common import load_library as load_snap7_library
        # first load shared lib if needed
        platf = str(platform.system())
        if platf in ['Windows','Linux'] and artisanlib.util.appFrozen():
            libpath = os.path.dirname(sys.executable)
            if platf == 'Linux':
                snap7dll = os.path.join(libpath,"libsnap7.so")
            else: # Windows:
                snap7dll = os.path.join(libpath,"snap7.dll")                
            load_snap7_library(snap7dll) # will ensure to load it only once
        # next reset client instance if not yet connected to ensure a fresh start
        if self.plc and not self.plc.get_connected():
            self.plc = None
        # connect if not yet connected
        if self.plc is None:
            self.plc = S7Client()
            with suppress_stdout_stderr():
                time.sleep(0.4)
                self.plc.connect(self.host,self.rack,self.slot,self.port)
                time.sleep(0.4)
            if self.plc.get_connected():
                self.sendmessage(QApplication.translate("Message","S7 Connected", None))
                time.sleep(0.7)
            else:
                time.sleep(0.6)
                self.plc = S7Client()
                # we try a second time
                with suppress_stdout_stderr():
                    time.sleep(0.4)
                    self.plc.connect(self.host,self.rack,self.slot,self.port)
                    time.sleep(0.4)
                if self.plc.get_connected():
                    self.sendmessage(QApplication.translate("Message","S7 Connected", None) + " (2)")
                    time.sleep(0.7)

    def writeFloat(self,area,dbnumber,start,value):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.plc is not None and self.plc.get_connected():
                with suppress_stdout_stderr():
                    ba = self.plc.read_area(self.areas[area],dbnumber,start,4)
                    self.set_real(ba, 0, float(value))
                    self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.adderror((QApplication.translate("Error Message","S7 Error:",None) + " connecting to PLC failed"))               
        except Exception as e:
            self.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " writeFloat: " + str(e))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            self.addserial("S7 writeFloat(" + str(area) + "," + str(dbnumber) + "," + str(start) + "," + str(value) + ")")

    def writeInt(self,area,dbnumber,start,value): 
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.plc is not None and self.plc.get_connected():
                with suppress_stdout_stderr():
                    ba = self.plc.read_area(self.areas[area],dbnumber,start,2)
                    self.set_int(ba, 0, int(value))
                    self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.adderror((QApplication.translate("Error Message","S7 Error:",None) + " connecting to PLC failed"))               
        except Exception as e:
            self.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " writeInt: " + str(e))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            self.addserial("S7 writeInt(" + str(area) + "," + str(dbnumber) + "," + str(start) + "," + str(value) + ")")
                    
    def readFloat(self,area,dbnumber,start):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.plc is not None and self.plc.get_connected():
                retry = self.readRetries   
                res = None             
                while True:
                    try:
                        with suppress_stdout_stderr():
                            res = self.plc.read_area(self.areas[area],dbnumber,start,4)
                    except:
                        res = None
                    if res is None:
                        if retry > 0:
                            retry = retry - 1
                        else:
                            raise Exception("Communication error")
                    else:
                        break
                if res is None:
                    return -1
                else:
                    if self.commError: # we clear the previous error and send a message
                        self.commError = False
                        self.adderror(QApplication.translate("Error Message","S7 Communication Resumed",None))
                    return self.get_real(res,0)
            else:
                self.commError = True  
                self.adderror((QApplication.translate("Error Message","S7 Error:",None) + " connecting to PLC failed"))                                 
                return -1
        except Exception as e:
            self.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " readFloat: " + str(e))
            self.commError = True
            return -1
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            self.addserial("S7 readFloat(" + str(area) + "," + str(dbnumber) + "," + str(start) + ")")
                
    def readInt(self,area,dbnumber,start):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.plc is not None and self.plc.get_connected():
                retry = self.readRetries   
                res = None             
                while True:
                    try:
                        with suppress_stdout_stderr():
                            res = self.plc.read_area(self.areas[area],dbnumber,start,2)
                    except Exception:
                        res = None
                    if res is None:
                        if retry > 0:
                            retry = retry - 1
                        else:
                            raise Exception("Communication error")
                    else:
                        break
                if res is None:
                    return -1
                else:
                    if self.commError: # we clear the previous error and send a message
                        self.commError = False
                        self.adderror(QApplication.translate("Error Message","S7 Communication Resumed",None))
                    return self.get_int(res,0)
            else:
                self.commError = True  
                self.adderror((QApplication.translate("Error Message","S7 Error:",None) + " connecting to PLC failed"))
                return -1
        except Exception as e:
            self.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " readInt: " + str(e))
            self.commError = True
            return -1
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            self.addserial("S7 readInt(" + str(area) + "," + str(dbnumber) + "," + str(start) + ")")  
