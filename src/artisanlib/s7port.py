#!/usr/bin/env python3

# ABOUT
# S7 support for Artisan

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
# Marko Luther, 2018

import time
import platform
import struct
import os
import sys

from snap7.types import Areas

import artisanlib.util
from artisanlib.suppress_errors import suppress_stdout_stderr

from PyQt5.QtCore import QSemaphore
from PyQt5.QtWidgets import QApplication


class s7port(object):
    def __init__(self,aw):
        self.aw = aw
        
        self.readRetries = 1
        self.channels = 10 # maximal number of S7 channels
        self.host = '127.0.0.1' # the TCP host
        self.port = 102 # the TCP port
        self.rack = 0 # 0,..,7
        self.slot = 0 # 0,..,31
                
        self.lastReadResult = 0 # this is set by eventaction following some custom button/slider S/ actions with "read" command
        
        self.area = [0]*self.channels
        self.db_nr = [1]*self.channels
        self.start = [0]*self.channels
        self.type = [0]*self.channels # type 0 => int, type 1 => float, type 2 => intFloat
        #  type 3 => Bool(0), type 4 => Bool(1), type 5 => Bool(2), type 6 => Bool(3), type 7 => Bool(4), type 8 => Bool(5), type 9 => Bool(6), type 10 => Bool(7)
        self.mode = [0]*self.channels # temp mode is an int here, 0:__,1:C,2:F (this is different than other places)
        self.div = [0]*self.channels
        
        self.optimizer = True # if set, values of consecutive register addresses are requested in single requests
        self.fetch_max_blocks = False # if set, the optimizer fetches only one sequence per area from the minimum to the maximum register ignoring gaps
        # S7 areas associated to dicts associating S7 DB numbers to start registers in use 
        # for optimized read of full register segments with single requests
        # this dict is re-computed on each connect() by a call to updateActiveRegisters()
        # NOTE: for registers of type float (32bit = 2x16bit) also the succeeding register is registered here
        self.activeRegisters = {}        
        # the readings cache that is filled by requesting sequences of values in blocks
        self.readingsCache = {}
        
        self.PID_area = 0
        self.PID_db_nr = 0
        self.PID_SV_register = 0
        self.PID_p_register = 0
        self.PID_i_register = 0
        self.PID_d_register = 0
        self.PID_ON_action = ""
        self.PID_OFF_action = ""
        self.PIDmultiplier = 0
        self.SVtype = 0
        self.SVmultiplier = 0
        
        self.COMsemaphore = QSemaphore(1)
        
#        self.areas = [
#            0x81, # PE, 129
#            0x82, # PA, 130
#            0x83, # MK, 131
#            0x1C, # CT, 28
#            0x1D, # TM, 29
#            0x84, # DB, 132
#        ]
        self.areas = [
            Areas.PE,
            Areas.PA,
            Areas.MK,
            Areas.CT,
            Areas.TM,
            Areas.DB
        ]
        
        self.last_request_timestamp = time.time()
        self.min_time_between_requests = 0.03
        
        self.is_connected = False # local cache of the connection state
        
        self.plc = None
        self.commError = False # True after a communication error was detected and not yet cleared by receiving proper data
        self.libLoaded = False
    
################
    
    # waits if need to ensure a minimal time delta between network requests which are scheduled directly after this functions evaluation and set the new timestamp
    def waitToEnsureMinTimeBetweenRequests(self):
        elapsed = time.time() - self.last_request_timestamp
        if elapsed < self.min_time_between_requests:
            time.sleep(self.min_time_between_requests - elapsed)
        self.last_request_timestamp = time.time()
    

################
# conversion methods copied from s7:util.py

    def get_bool(self, _bytearray, byte_index, bool_index):
        """
        Get the boolean value from location in bytearray
        """
        index_value = 1 << bool_index
        byte_value = _bytearray[byte_index]
        current_value = byte_value & index_value
        return current_value == index_value
    
    
    def set_bool(self, _bytearray, byte_index, bool_index, value):
        """
        Set boolean value on location in bytearray
        """
        assert value in [0, 1, True, False]
        current_value = self.get_bool(_bytearray, byte_index, bool_index)
        index_value = 1 << bool_index
    
        # check if bool already has correct value
        if current_value == value:
            return
    
        if value:
            # make sure index_v is IN current byte
            _bytearray[byte_index] += index_value
        else:
            # make sure index_v is NOT in current byte
            _bytearray[byte_index] -= index_value

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
            if self.SVtype == 1:
                self.writeFloat(self.PID_area-1,self.PID_db_nr,self.PID_SV_register,sv*multiplier)
            else:
                self.writeInt(self.PID_area-1,self.PID_db_nr,self.PID_SV_register,int(round(sv*multiplier)))
                    
    def isConnected(self):
        # the check on the CPU state is needed as get_connected() still returns True if the connect got terminated from the peer due to a bug in snap7
        # disconnects and clears the S7 plc objects if get_connected() but not str(self.plc.get_cpu_state()) == "S7CpuStatusRun" to force a clear restart
#        return self.plc is not None and self.plc.get_connected() and str(self.plc.get_cpu_state()) == "S7CpuStatusRun"
        if self.plc is not None and ((self.is_connected and not self.commError) or self.plc.get_connected()):
            return True
#            if str(self.plc.get_cpu_state()) == "S7CpuStatusRun":
#                return True
#            else:
#                self.disconnect()
#                return False
        else:
            return False
        
    def disconnect(self):
# don't stop the PLC as we want to keep it running beyond the Artisan disconnect!!
#        try:
#            self.plc.plc_stop()
#        except:
#            pass
        try:
            self.plc.disconnect()
        except:
            pass
        try:
            self.plc.destroy()
        except:
            pass
        self.plc = None
        self.is_connected = False

    def connect(self):
        if not self.libLoaded:
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
            elif platf in ['Darwin'] and artisanlib.util.appFrozen():
                libpath = os.path.dirname(sys.executable)
                snap7dll = os.path.abspath(os.path.join(libpath,"../Frameworks/libsnap7.dylib"))
                load_snap7_library(snap7dll) # will ensure to load it only once
            self.libLoaded = True
        
        if self.libLoaded and self.plc is None:
            # create a client instance
            from artisanlib.s7client import S7Client
            self.plc = S7Client()
            
        # next reset client instance if not yet connected to ensure a fresh start
        if not self.isConnected():
            try:
                if self.plc is None:
                    from artisanlib.s7client import S7Client
                    self.plc = S7Client()
                else:
                    self.plc.disconnect()
            except:
                pass
            with suppress_stdout_stderr():
                time.sleep(0.2)
                try:
                    self.plc.connect(self.host,self.rack,self.slot,self.port)
                    time.sleep(0.2)
                except Exception:
                    pass
            
            if self.isConnected():
                self.is_connected = True
                self.aw.sendmessage(QApplication.translate("Message","S7 connected", None))
                self.clearReadingsCache()
                time.sleep(0.1)
            else:
                self.disconnect()
                time.sleep(0.3)
                from artisanlib.s7client import S7Client
                self.plc = S7Client()
                # we try a second time
                with suppress_stdout_stderr():
                    time.sleep(0.3)
                    self.plc.connect(self.host,self.rack,self.slot,self.port)
                    time.sleep(0.3)
                    
                    if self.isConnected():
                        self.is_connected = True
                        self.clearReadingsCache()
                        self.aw.sendmessage(QApplication.translate("Message","S7 Connected", None) + " (2)")
                        time.sleep(0.1)
            self.updateActiveRegisters()


########## S7 optimizer for fetching register data in batches

    # S7 area => db_nr => [start registers]
    def updateActiveRegisters(self):
        self.activeRegisters = {}
        for c in range(self.channels):
            area = self.area[c]-1
            if area != -1:
                db_nr = self.db_nr[c]
                register = self.start[c]
                registers = [register] # BOOL
                if self.type[c] in [1,2]: # FLOAT (or FLOAT2INT)
                    registers.append(register+1)
                    registers.append(register+2)
                    registers.append(register+3)
                elif self.type[c] == 0: # INT
                    registers.append(register+1)
                if not (area in self.activeRegisters):
                    self.activeRegisters[area] = {}
                if db_nr in self.activeRegisters[area]:
                    self.activeRegisters[area][db_nr].extend(registers)
                else:
                    self.activeRegisters[area][db_nr] = registers
    
    def clearReadingsCache(self):
        self.readingsCache = {}

    def cacheReadings(self,area,db_nr,register,results):
        if not (area in self.readingsCache):
            self.readingsCache[area] = {}
        if not db_nr in self.readingsCache[area]:
            self.readingsCache[area][db_nr] = {}
        try:
            for i,v in enumerate(results):
                self.readingsCache[area][db_nr][register+i] = v
        except:
            pass

    def readActiveRegisters(self):
        if not self.optimizer:
            return
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.clearReadingsCache()
            self.connect()
            if self.isConnected():
                for area in self.activeRegisters:
                    for db_nr in self.activeRegisters[area]:
                        registers = sorted(self.activeRegisters[area][db_nr])
                        if self.fetch_max_blocks:
                            sequences = [[registers[0],registers[-1]]]
                        else:
                            # split in successive sequences
                            gaps = [[s, e] for s, e in zip(registers, registers[1:]) if s+1 < e]
                            edges = iter(registers[:1] + sum(gaps, []) + registers[-1:])
                            sequences = list(zip(edges, edges)) # list of pairs of the form (start-register,end-register)
                        for seq in sequences:
                            retry = self.readRetries
                            register = seq[0]
                            count = seq[1]-seq[0] + 1
                            res = None
                            while True:
                                self.waitToEnsureMinTimeBetweenRequests()
                                try:
                                    res = self.plc.read_area(self.areas[area],db_nr,register,count)
                                except:
                                    res = None
                                if res is None:
                                    if retry > 0:
                                        retry = retry - 1
                                    else:
                                        raise Exception("read_area({},{},{},{})".format(area,db_nr,register,count))
                                else:
                                    break
                            if res is not None:
                                if self.commError: # we clear the previous error and send a message
                                    self.commError = False
                                    self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Communication Resumed",None))
                                self.cacheReadings(area,db_nr,register,res)
    
                            #note: logged chars should be unicode not binary
                            if self.aw.seriallogflag:
                                self.aw.addserial("S7 read_area({},{},{},{})".format(area,db_nr,register,count))
        except Exception as e: # as ex:
#            self.disconnect()
#            import traceback
#            traceback.print_exc(file=sys.stdout)
#            _, _, exc_tb = sys.exc_info()
#            self.aw.qmc.adderror((QApplication.translate("Error Message","S7 Error:",None) + " readSingleRegister() {0}").format(str(ex)),exc_tb.tb_lineno)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror(QApplication.translate("Error Message","readActiveRegisters() S7 Communication Error",None) + ": " + str(e),exc_tb.tb_lineno)
            if self.aw.seriallogflag:
                self.aw.addserial("S7 readActiveRegisters() => S7 Communication Error: {}".format(str(e)))
            self.commError = True
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
                
##########


    def writeFloat(self,area,dbnumber,start,value):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                with suppress_stdout_stderr():
                    ba = self.plc.read_area(self.areas[area],dbnumber,start,4)
                    self.set_real(ba, 0, float(value))
                    self.waitToEnsureMinTimeBetweenRequests()
                    self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.commError = True
                self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Error: connecting to PLC failed",None))
        except Exception as e:
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " writeFloat: " + str(e),exc_tb.tb_lineno)
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.aw.addserial("S7 writeFloat({},{},{},{})".format(area,dbnumber,start,value))

    def writeInt(self,area,dbnumber,start,value):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                with suppress_stdout_stderr():
                    ba = self.plc.read_area(self.areas[area],dbnumber,start,2)
                    self.set_int(ba, 0, int(round(value)))
                    self.waitToEnsureMinTimeBetweenRequests()
                    self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.commError = True
                self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Error: connecting to PLC failed",None))
        except Exception as e:
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " writeInt: " + str(e),exc_tb.tb_lineno)
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.aw.addserial("S7 writeInt({},{},{},{})".format(area,dbnumber,start,value))

    def maskWriteInt(self,area,dbnumber,start,and_mask,or_mask,value):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                with suppress_stdout_stderr():
                    ba = self.plc.read_area(self.areas[area],dbnumber,start,2)
                    new_val = (int(round(value)) & and_mask) | (or_mask & (and_mask ^ 0xFFFF))
                    self.set_int(ba, 0, int(new_val))
                    self.waitToEnsureMinTimeBetweenRequests()
                    self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.commError = True
                self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Error: connecting to PLC failed",None))
        except Exception as e:
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " maskWriteInt: " + str(e),exc_tb.tb_lineno)
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.aw.addserial("S7 writeInt({},{},{},{})".format(area,dbnumber,start,value))

    def writeBool(self,area,dbnumber,start,index,value): 
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                with suppress_stdout_stderr():
                    ba = self.plc.read_area(self.areas[area],dbnumber,start,1)
                    self.set_bool(ba, 0, int(index), bool(value))
                    self.waitToEnsureMinTimeBetweenRequests()
                    self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.commError = True
                self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Error: connecting to PLC failed",None))
        except Exception as e:
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " writeBool: " + str(e),exc_tb.tb_lineno)
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.aw.addserial("S7 writeBool({},{},{},{},{})".format(area,dbnumber,start,index,value))

    # if force the readings cache is ignored and fresh readings are requested
    def readFloat(self,area,dbnumber,start,force=False):
        if area == 0:
            return
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if not force and area in self.readingsCache and dbnumber in self.readingsCache[area] and start in self.readingsCache[area][dbnumber] \
                and start+1 in self.readingsCache[area][dbnumber] and start+2 in self.readingsCache[area][dbnumber] \
                and start+3 in self.readingsCache[area][dbnumber]:
                # cache hit
                res = bytearray([
                    self.readingsCache[area][dbnumber][start],
                    self.readingsCache[area][dbnumber][start+1],
                    self.readingsCache[area][dbnumber][start+2],
                    self.readingsCache[area][dbnumber][start+3]])
                r = self.get_real(res,0)
                if self.aw.seriallogflag and not self.commError:
                    self.aw.addserial("S7 readFloat_cached({},{},{},{}) => {}".format(area,dbnumber,start,force,r))
                return r
            else:
                self.connect()
                if self.isConnected():
                    retry = self.readRetries
                    res = None
                    while True:
                        self.waitToEnsureMinTimeBetweenRequests()
                        try:
                            with suppress_stdout_stderr():
                                res = self.plc.read_area(self.areas[area],dbnumber,start,4)
                        except:
                            res = None
                        if res is None:
                            if retry > 0:
                                retry = retry - 1
                            else:
                                raise Exception("result None")
                        else:
                            break
                    if res is None:
                        return
                    else:
                        if self.commError: # we clear the previous error and send a message
                            self.commError = False
                            self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Communication Resumed",None))
                        r = self.get_real(res,0)
                        if self.aw.seriallogflag:
                            self.aw.addserial("S7 readFloat({},{},{},{}) => {}".format(area,dbnumber,start,force,r))
                        return r
                else:
                    self.commError = True  
                    self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Error: connecting to PLC failed",None))
        except Exception as e:
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " readFloat({},{},{},{}): {}".format(area,dbnumber,start,force,str(e)),exc_tb.tb_lineno)
                if self.aw.seriallogflag:
                    self.aw.addserial("S7 readFloat({},{},{},{}) => S7 Communication Error: {}".format(area,dbnumber,start,force,str(e)))
            self.commError = True
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
        
    # as readFloat, but does not retry nor raise and error and returns a None instead
    # also does not reserve the port via a semaphore nor uses the cache!
    def peakFloat(self,area,dbnumber,start):
        if area == 0:
            return  
        try:
            self.connect()
            if self.isConnected():
                self.waitToEnsureMinTimeBetweenRequests()
                with suppress_stdout_stderr():
                    res = self.plc.read_area(self.areas[area],dbnumber,start,4)
                return self.get_real(res,0)
            else:
                return
        except:
            return
                
    # if force the readings cache is ignored and fresh readings are requested
    def readInt(self,area,dbnumber,start,force=False):
        if area == 0:
            return     
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if not force and area in self.readingsCache and dbnumber in self.readingsCache[area] and start in self.readingsCache[area][dbnumber] \
                and start+1 in self.readingsCache[area][dbnumber]:
                # cache hit
                res = bytearray([
                    self.readingsCache[area][dbnumber][start],
                    self.readingsCache[area][dbnumber][start+1]])
                r = self.get_int(res,0)
                if self.aw.seriallogflag:
                    self.aw.addserial("S7 readInt_cached({},{},{},{}) => {}".format(area,dbnumber,start,force,r))
                return r
            else:
                self.connect()
                if self.isConnected():
                    retry = self.readRetries
                    res = None
                    while True:
                        self.waitToEnsureMinTimeBetweenRequests()
                        try:
                            with suppress_stdout_stderr():
                                res = self.plc.read_area(self.areas[area],dbnumber,start,2)
                        except Exception:
                            res = None
                        if res is None:
                            if retry > 0:
                                retry = retry - 1
                            else:
                                raise Exception("result None")
                        else:
                            break
                    if res is None:
                        return
                    else:
                        if self.commError: # we clear the previous error and send a message
                            self.commError = False
                            self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Communication Resumed",None))
                        r = self.get_int(res,0)
                        if self.aw.seriallogflag:
                            self.aw.addserial("S7 readInt({},{},{},{}) => {}".format(area,dbnumber,start,force,r))
                        return r
                else:
                    self.commError = True  
                    self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Error: connecting to PLC failed",None))
        except Exception as e:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
#            _, _, exc_tb = sys.exc_info()        
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " readInt({},{},{},{}): {}".format(area,dbnumber,start,force,str(e)),exc_tb.tb_lineno)
                if self.aw.seriallogflag:
                    self.aw.addserial("S7 readInt({},{},{},{}) => S7 Communication Error: {}".format(area,dbnumber,start,force,str(e)))
            self.commError = True
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    
    # as readInt, but does not retry nor raise and error and returns a None instead
    # also does not reserve the port via a semaphore nor uses the cache!
    def peekInt(self,area,dbnumber,start):
        if area == 0:
            return    
        try:
            self.connect()
            if self.isConnected(): 
                with suppress_stdout_stderr():
                    self.waitToEnsureMinTimeBetweenRequests()
                    res = self.plc.read_area(self.areas[area],dbnumber,start,2)
                return self.get_int(res,0)
            else:
                return
        except:
            return

    # if force the readings cache is ignored and fresh readings are requested
    def readBool(self,area,dbnumber,start,index,force=False):
        if area == 0:
            return
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if not force and area in self.readingsCache and dbnumber in self.readingsCache[area] and start in self.readingsCache[area][dbnumber]:
                # cache hit
                res = bytearray([
                    self.readingsCache[area][dbnumber][start]])
                r = self.get_bool(res,0,index)
                if self.aw.seriallogflag:
                    self.aw.addserial("S7 readBool_cached({},{},{},{},{}) => {}".format(area,dbnumber,start,index,force,r))
                return r
            else:
                self.connect()
                if self.isConnected():
                    retry = self.readRetries
                    res = None
                    while True:
                        self.waitToEnsureMinTimeBetweenRequests()
                        try:
                            with suppress_stdout_stderr():
                                res = self.plc.read_area(self.areas[area],dbnumber,start,1)                            
                        except Exception:
                            res = None
                        if res is None:
                            if retry > 0:
                                retry = retry - 1
                            else:
                                raise Exception("result None")
                        else:
                            break
                    if res is None:
                        return
                    else:
                        if self.commError: # we clear the previous error and send a message
                            self.commError = False
                            self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Communication Resumed",None))
                        r = self.get_bool(res,0,index)
                        if self.aw.seriallogflag:
                            self.aw.addserial("S7 readBool({},{},{},{},{}) => {}".format(area,dbnumber,start,index,force,r))
                        return r
                else:
                    self.commError = True
                    self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Error: connecting to PLC failed",None))
        except Exception as e:
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " readBool({},{},{},{},{}): {}".format(area,dbnumber,start,index,force,str(e)),exc_tb.tb_lineno)
                if self.aw.seriallogflag:
                    self.aw.addserial("S7 readBool({},{},{},{},{}) => S7 Communication Error: {}".format(area,dbnumber,start,index,force,str(e)))
            self.commError = True
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
