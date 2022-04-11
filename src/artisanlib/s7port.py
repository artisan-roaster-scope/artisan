#
# ABOUT
# S7 support for Artisan

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
# Marko Luther, 2018

import time
import platform
import os
import sys
import struct
import logging
try:
    from typing import Final
except ImportError:
    # for Python 3.7:
    from typing_extensions import Final

# imports avoided to speed up startup for non-S7 users
#from snap7.types import Areas
#from snap7.util import get_bool, set_bool, get_int, set_int, get_real, set_real

import artisanlib.util

try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtCore import QSemaphore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except Exception:
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import QSemaphore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport


_log: Final = logging.getLogger(__name__)


################
# conversion methods copied from s7:util.py to avoid the import for non S7 users

def get_bool(bytearray_: bytearray, byte_index: int, bool_index: int) -> bool:
    """Get the boolean value from location in bytearray

    Args:
        bytearray_: buffer data.
        byte_index: byte index to read from.
        bool_index: bit index to read from.

    Returns:
        True if the bit is 1, else 0.

    Examples:
        >>> buffer = bytearray([0b00000001])  # Only one byte length
        >>> get_bool(buffer, 0, 0)  # The bit 0 starts at the right.
            True
    """
    index_value = 1 << bool_index
    byte_value = bytearray_[byte_index]
    current_value = byte_value & index_value
    return current_value == index_value


def set_bool(bytearray_: bytearray, byte_index: int, bool_index: int, value: bool):
    """Set boolean value on location in bytearray.

    Args:
        bytearray_: buffer to write to.
        byte_index: byte index to write to.
        bool_index: bit index to write to.
        value: value to write.

    Examples:
        >>> buffer = bytearray([0b00000000])
        >>> set_bool(buffer, 0, 0, True)
        >>> buffer
            bytearray(b"\\x01")
    """
    if value not in {0, 1, True, False}:
        raise TypeError(f'Value value:{value} is not a boolean expression.')

    current_value = get_bool(bytearray_, byte_index, bool_index)
    index_value = 1 << bool_index

    # check if bool already has correct value
    if current_value == value:
        return

    if value:
        # make sure index_v is IN current byte
        bytearray_[byte_index] += index_value
    else:
        # make sure index_v is NOT in current byte
        bytearray_[byte_index] -= index_value

def set_int(bytearray_: bytearray, byte_index: int, _int: int):
    """Set value in bytearray to int

    Notes:
        An datatype `int` in the PLC consists of two `bytes`.

    Args:
        bytearray_: buffer to write on.
        byte_index: byte index to start writing from.
        _int: int value to write.

    Returns:
        Buffer with the written value.

    Examples:
        >>> data = bytearray(2)
        >>> snap7.util.set_int(data, 0, 255)
            bytearray(b'\\x00\\xff')
    """
    # make sure were dealing with an int
    _int = int(_int)
    _bytes = struct.unpack('2B', struct.pack('>h', _int))
    bytearray_[byte_index:byte_index + 2] = _bytes
    return bytearray_

def get_int(bytearray_: bytearray, byte_index: int) -> int:
    """Get int value from bytearray.

    Notes:
        Datatype `int` in the PLC is represented in two bytes

    Args:
        bytearray_: buffer to read from.
        byte_index: byte index to start reading from.

    Returns:
        Value read.

    Examples:
        >>> data = bytearray([0, 255])
        >>> snap7.util.get_int(data, 0)
            255
    """
    data = bytearray_[byte_index:byte_index + 2]
    data[1] = data[1] & 0xff
    data[0] = data[0] & 0xff
    packed = struct.pack('2B', *data)
    value = struct.unpack('>h', packed)[0]
    return value

def get_real(bytearray_: bytearray, byte_index: int) -> float:
    """Get real value.

    Notes:
        Datatype `real` is represented in 4 bytes in the PLC.
        The packed representation uses the `IEEE 754 binary32`.

    Args:
        bytearray_: buffer to read from.
        byte_index: byte index to reading from.

    Returns:
        Real value.

    Examples:
        >>> data = bytearray(b'B\\xf6\\xa4Z')
        >>> snap7.util.get_real(data, 0)
            123.32099914550781
    """
    x = bytearray_[byte_index:byte_index + 4]
    real = struct.unpack('>f', struct.pack('4B', *x))[0]
    return real

def set_real(bytearray_: bytearray, byte_index: int, real) -> bytearray:
    """Set Real value

    Notes:
        Datatype `real` is represented in 4 bytes in the PLC.
        The packed representation uses the `IEEE 754 binary32`.

    Args:
        bytearray_: buffer to write to.
        byte_index: byte index to start writing from.
        real: value to be written.

    Returns:
        Buffer with the value written.

    Examples:
        >>> data = bytearray(4)
        >>> snap7.util.set_real(data, 0, 123.321)
            bytearray(b'B\\xf6\\xa4Z')
    """
    real = float(real)
    real = struct.pack('>f', real)
    _bytes = struct.unpack('4B', real)
    for i, b in enumerate(_bytes):
        bytearray_[byte_index + i] = b
    return bytearray_


class s7port():

    __slots__ = [ 'aw', 'readRetries', 'channels', 'host', 'port', 'rack', 'slot', 'lastReadResult', 'area', 'db_nr', 'start', 'type', 'mode',
        'div', 'optimizer', 'fetch_max_blocks', 'activeRegisters', 'readingsCache', 'PID_area', 'PID_db_nr', 'PID_SV_register', 'PID_p_register',
        'PID_i_register', 'PID_d_register', 'PID_ON_action', 'PID_OFF_action', 'PIDmultiplier', 'SVtype', 'SVmultiplier', 'COMsemaphore',
        'areas', 'last_request_timestamp', 'min_time_between_requests', 'is_connected', 'plc', 'commError', 'libLoaded' ]

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
        self.PID_ON_action = ''
        self.PID_OFF_action = ''
        self.PIDmultiplier = 0
        self.SVtype = 0
        self.SVmultiplier = 0

        self.COMsemaphore = QSemaphore(1)

        # we do not use the snap7 enums here to avoid the import for non S7 users
        self.areas = None # lazy initialized in initArray() on connect
        self.last_request_timestamp = time.time()
        self.min_time_between_requests = 0.04

        self.is_connected = False # local cache of the connection state

        self.plc = None
        self.commError = False # True after a communication error was detected and not yet cleared by receiving proper data
        self.libLoaded = False

################

    def initArrays(self):
        if self.areas is None:
            from snap7.types import Areas
            self.areas = [
                Areas.PE, # 129, 0x81
                Areas.PA, # 130, 0x82
                Areas.MK, # 131, 0x83
                Areas.CT, #  28, 0x1C
                Areas.TM, #  29, 0x1D
                Areas.DB  # 132, 0x84
            ]

    # waits if need to ensure a minimal time delta between network requests which are scheduled directly after this functions evaluation and set the new timestamp
    def waitToEnsureMinTimeBetweenRequests(self):
        elapsed = time.time() - self.last_request_timestamp
        if elapsed < self.min_time_between_requests:
            time.sleep(self.min_time_between_requests - elapsed)
        self.last_request_timestamp = time.time()

################


    def setPID(self,p,i,d,PIDmultiplier):
        _log.debug('setPID(%s,%s,%s,%s)',p,i,d,PIDmultiplier)
        if self.PID_area and not (self.PID_p_register == self.PID_i_register == self.PID_d_register == 0):
            multiplier = 1.
            if PIDmultiplier == 1:
                PIDmultiplier = 10.
            elif PIDmultiplier == 2:
                multiplier = 100.
            self.writeInt(self.PID_area-1,self.PID_db_nr,self.PID_p_register,p*multiplier)
            self.writeInt(self.PID_area-1,self.PID_db_nr,self.PID_i_register,i*multiplier)
            self.writeInt(self.PID_area-1,self.PID_db_nr,self.PID_d_register,d*multiplier)

    def setTarget(self,sv,SVmultiplier):
        _log.debug('setTarget(%s,%s)',sv,SVmultiplier)
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
        if self.plc is not None and ((self.is_connected and not self.commError) or (self.plc.get_connected() and str(self.plc.get_cpu_state()) == 'S7CpuStatusRun')):
            return True
#            if str(self.plc.get_cpu_state()) == "S7CpuStatusRun":
#                return True
#            else:
#                self.disconnect()
#                return False
        _log.debug('isConnected() => False')
        return False

    def disconnect(self):
        _log.debug('disconnect()')
# don't stop the PLC as we want to keep it running beyond the Artisan disconnect!!
#        try:
#            self.plc.plc_stop()
#        except:
#            pass
        try:
            if self.plc is not None:
                self.plc.disconnect()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        try:
            if self.plc is not None:
                self.plc.destroy()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        self.plc = None
        self.is_connected = False

    def connect(self):
        if not self.libLoaded:
            _log.debug('connect() load lib')
            from snap7.common import load_library as load_snap7_library
            # first load shared lib if needed
            platf = str(platform.system())
            if platf in ['Windows','Linux'] and artisanlib.util.appFrozen():
                libpath = os.path.dirname(sys.executable)
                if platf == 'Linux':
                    snap7dll = os.path.join(libpath,'libsnap7.so')
                else: # Windows:
                    snap7dll = os.path.join(libpath,'snap7.dll')
                load_snap7_library(snap7dll) # will ensure to load it only once
            elif platf in ['Darwin'] and artisanlib.util.appFrozen():
                libpath = os.path.dirname(sys.executable)
                snap7dll = os.path.abspath(os.path.join(libpath,'../Frameworks/libsnap7.dylib'))
                load_snap7_library(snap7dll) # will ensure to load it only once
            self.libLoaded = True

        if self.libLoaded and self.plc is None:
            _log.debug('connect() create S7Client')
            # create a client instance
            from artisanlib.s7client import S7Client
            self.plc = S7Client()
            self.initArrays() # initialize S7 arrays

        # next reset client instance if not yet connected to ensure a fresh start
        if not self.isConnected():
            _log.debug('connect(): connecting')
            try:
                if self.plc is None:
                    from artisanlib.s7client import S7Client # pylint: disable=reimported
                    self.plc = S7Client()
                    self.initArrays() # initialize S7 arrays
                else:
                    self.plc.disconnect()
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
            time.sleep(0.2)
            try:
                self.plc.connect(self.host,self.rack,self.slot,self.port)
                time.sleep(0.2)
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)

            if self.isConnected():
                _log.debug('connect(): connected')
                self.is_connected = True
                self.aw.sendmessage(QApplication.translate('Message','S7 connected'))
                self.clearReadingsCache()
                time.sleep(0.1)
            else:
                _log.debug('connect(): connecting failed')
                self.disconnect()
                time.sleep(0.3)
                from artisanlib.s7client import S7Client # pylint: disable=reimported
                self.plc = S7Client()
                self.initArrays() # initialize S7 arrays
                # we try a second time
                _log.debug('connect(): connecting (2nd attempt)')
                time.sleep(0.3)
                self.plc.connect(self.host,self.rack,self.slot,self.port)
                time.sleep(0.3)

                if self.isConnected():
                    _log.debug('connect(): connected')
                    self.is_connected = True
                    self.clearReadingsCache()
                    self.aw.sendmessage(QApplication.translate('Message','S7 Connected') + ' (2)')
                    time.sleep(0.1)
                else:
                    _log.debug('connect(): connecting failed')
            self.updateActiveRegisters()


########## S7 optimizer for fetching register data in batches

    # S7 area => db_nr => [start registers]
    def updateActiveRegisters(self):
        _log.debug('updateActiveRegisters()')
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
        _log.debug('clearReadingsCache()')
        self.readingsCache = {}

    def cacheReadings(self,area,db_nr,register,results):
        if not (area in self.readingsCache):
            self.readingsCache[area] = {}
        if not db_nr in self.readingsCache[area]:
            self.readingsCache[area][db_nr] = {}
        try:
            for i,v in enumerate(results):
                self.readingsCache[area][db_nr][register+i] = v
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    def readActiveRegisters(self):
        if not self.optimizer:
            return
        try:
            _log.debug('readActiveRegisters()')
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
                            gaps = [[s, e] for s, e in zip(registers, registers[1:]) if s+1 < e] # pylint: disable=used-before-assignment
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
                                except Exception as e: # pylint: disable=broad-except
                                    _log.exception(e)
                                    res = None
                                if res is None:
                                    if retry > 0:
                                        retry = retry - 1
                                    else:
                                        raise Exception(f'read_area({area},{db_nr},{register},{count})')
                                else:
                                    break
                            if res is not None:
                                if self.commError: # we clear the previous error and send a message
                                    self.commError = False
                                    self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Resumed'))
                                self.cacheReadings(area,db_nr,register,res)

                            #note: logged chars should be unicode not binary
                            if self.aw.seriallogflag:
                                self.aw.addserial(f'S7 read_area({area},{db_nr},{register},{count})')
        except Exception as e: # pylint: disable=broad-except
#            self.disconnect()
#            import traceback
#            traceback.print_exc(file=sys.stdout)
#            _, _, exc_tb = sys.exc_info()
#            self.aw.qmc.adderror((QApplication.translate("Error Message","S7 Error:") + " readSingleRegister() {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror(QApplication.translate('Error Message','readActiveRegisters() S7 Communication Error') + ': ' + str(e),getattr(exc_tb, 'tb_lineno', '?'))
            if self.aw.seriallogflag:
                self.aw.addserial(f'S7 readActiveRegisters() => S7 Communication Error: {str(e)}')
            self.commError = True
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

##########


    def writeFloat(self,area,dbnumber,start,value):
        _log.debug('writeFloat(%d,%d,%d,%.3f)',area,dbnumber,start,value)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                self.waitToEnsureMinTimeBetweenRequests()
                ba = self.plc.read_area(self.areas[area],dbnumber,start,4)
                set_real(ba, 0, float(value))
                self.waitToEnsureMinTimeBetweenRequests()
                self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.commError = True
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Error: connecting to PLC failed'))
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Error') + ' writeFloat: ' + str(e),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.aw.addserial(f'S7 writeFloat({area},{dbnumber},{start},{value})')

    def writeInt(self,area,dbnumber,start,value):
        _log.debug('writeInt(%d,%d,%d,%d)',area,dbnumber,start,value)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                self.waitToEnsureMinTimeBetweenRequests()
                ba = self.plc.read_area(self.areas[area],dbnumber,start,2)
                set_int(ba, 0, int(round(value)))
                self.waitToEnsureMinTimeBetweenRequests()
                self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.commError = True
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Error: connecting to PLC failed'))
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Error') + ' writeInt: ' + str(e),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.aw.addserial(f'S7 writeInt({area},{dbnumber},{start},{value})')

    def maskWriteInt(self,area,dbnumber,start,and_mask,or_mask,value):
        _log.debug('maskWriteInt(%d,%d,%d,%s,%s,%d)',area,dbnumber,start,and_mask,or_mask,value)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                self.waitToEnsureMinTimeBetweenRequests()
                ba = self.plc.read_area(self.areas[area],dbnumber,start,2)
                new_val = (int(round(value)) & and_mask) | (or_mask & (and_mask ^ 0xFFFF))
                set_int(ba, 0, int(new_val))
                self.waitToEnsureMinTimeBetweenRequests()
                self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.commError = True
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Error: connecting to PLC failed'))
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Error') + ' maskWriteInt: ' + str(e),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.aw.addserial(f'S7 writeInt({area},{dbnumber},{start},{value})')

    def writeBool(self,area,dbnumber,start,index,value):
        _log.debug('writeInt(%d,%d,%d,%d,%s)',area,dbnumber,start,index,value)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                self.waitToEnsureMinTimeBetweenRequests()
                ba = self.plc.read_area(self.areas[area],dbnumber,start,1)
                set_bool(ba, 0, int(index), bool(value))
                self.waitToEnsureMinTimeBetweenRequests()
                self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.commError = True
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Error: connecting to PLC failed'))
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Error') + ' writeBool: ' + str(e),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.aw.addserial(f'S7 writeBool({area},{dbnumber},{start},{index},{value})')

    # if force the readings cache is ignored and fresh readings are requested
    def readFloat(self,area,dbnumber,start,force=False):
        _log.debug('readFloat(%d,%d,%d,%s)',area,dbnumber,start,force)
        if area == 0:
            return None
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
                r = get_real(res,0)
                if self.aw.seriallogflag and not self.commError:
                    self.aw.addserial(f'S7 readFloat_cached({area},{dbnumber},{start},{force}) => {r}')
                _log.debug('return cached value => %.3f', r)
                return r
            self.connect()
            if self.isConnected():
                retry = self.readRetries
                res = None
                while True:
                    self.waitToEnsureMinTimeBetweenRequests()
                    try:
                        res = self.plc.read_area(self.areas[area],dbnumber,start,4)
                    except Exception as e: # pylint: disable=broad-except
                        _log.exception(e)
                        res = None
                    if res is None:
                        if retry > 0:
                            retry = retry - 1
                        else:
                            raise Exception('result None')
                    else:
                        break
                if res is None:
                    return None
                if self.commError: # we clear the previous error and send a message
                    self.commError = False
                    self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Resumed'))
                r = get_real(res,0)
                if self.aw.seriallogflag:
                    self.aw.addserial(f'S7 readFloat({area},{dbnumber},{start},{force}) => {r}')
                return r
            self.commError = True
            self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Error: connecting to PLC failed'))
            return None
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Error') + f' readFloat({area},{dbnumber},{start},{force}): {str(e)}',getattr(exc_tb, 'tb_lineno', '?'))
                if self.aw.seriallogflag:
                    self.aw.addserial(f'S7 readFloat({area},{dbnumber},{start},{force}) => S7 Communication Error: {str(e)}')
            self.commError = True
            return None
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    # as readFloat, but does not retry nor raise and error and returns a None instead
    # also does not reserve the port via a semaphore nor uses the cache!
    def peakFloat(self,area,dbnumber,start):
        _log.debug('peakFloat(%d,%d,%d)',area,dbnumber,start)
        if area == 0:
            return None
        try:
            self.connect()
            if self.isConnected():
                self.waitToEnsureMinTimeBetweenRequests()
                res = self.plc.read_area(self.areas[area],dbnumber,start,4)
                return get_real(res,0)
            return None
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            return None

    # if force the readings cache is ignored and fresh readings are requested
    def readInt(self,area,dbnumber,start,force=False):
        _log.debug('readInt(%d,%d,%d,%s)',area,dbnumber,start,force)
        if area == 0:
            return None
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if not force and area in self.readingsCache and dbnumber in self.readingsCache[area] and start in self.readingsCache[area][dbnumber] \
                and start+1 in self.readingsCache[area][dbnumber]:
                # cache hit
                res = bytearray([
                    self.readingsCache[area][dbnumber][start],
                    self.readingsCache[area][dbnumber][start+1]])
                r = get_int(res,0)
                if self.aw.seriallogflag:
                    self.aw.addserial(f'S7 readInt_cached({area},{dbnumber},{start},{force}) => {r}')
                _log.debug('return cached value => %d', r)
                return r
            self.connect()
            if self.isConnected():
                retry = self.readRetries
                res = None
                while True:
                    self.waitToEnsureMinTimeBetweenRequests()
                    try:
                        res = self.plc.read_area(self.areas[area],dbnumber,start,2)
                    except Exception as e: # pylint: disable=broad-except
                        _log.exception(e)
                        res = None
                    if res is None:
                        if retry > 0:
                            retry = retry - 1
                        else:
                            raise Exception('result None')
                    else:
                        break
                if res is None:
                    return None
                if self.commError: # we clear the previous error and send a message
                    self.commError = False
                    self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Resumed'))
                r = get_int(res,0)
                if self.aw.seriallogflag:
                    self.aw.addserial(f'S7 readInt({area},{dbnumber},{start},{force}) => {r}')
                return r
            self.commError = True
            self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Error: connecting to PLC failed'))
            return None
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
#            import traceback
#            traceback.print_exc(file=sys.stdout)
#            _, _, exc_tb = sys.exc_info()
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Error') + f' readInt({area},{dbnumber},{start},{force}): {str(e)}',getattr(exc_tb, 'tb_lineno', '?'))
                if self.aw.seriallogflag:
                    self.aw.addserial(f'S7 readInt({area},{dbnumber},{start},{force}) => S7 Communication Error: {str(e)}')
            self.commError = True
            return None
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)


    # as readInt, but does not retry nor raise and error and returns a None instead
    # also does not reserve the port via a semaphore nor uses the cache!
    def peekInt(self,area,dbnumber,start):
        _log.debug('peakInt(%d,%d,%d)',area,dbnumber,start)
        if area == 0:
            return None
        try:
            self.connect()
            if self.isConnected():
                self.waitToEnsureMinTimeBetweenRequests()
                res = self.plc.read_area(self.areas[area],dbnumber,start,2)
                return get_int(res,0)
            return None
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            return None

    # if force the readings cache is ignored and fresh readings are requested
    def readBool(self,area,dbnumber,start,index,force=False):
        _log.debug('readBool(%d,%d,%d,%s)',area,dbnumber,start,force)
        if area == 0:
            return None
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if not force and area in self.readingsCache and dbnumber in self.readingsCache[area] and start in self.readingsCache[area][dbnumber]:
                # cache hit
                res = bytearray([
                    self.readingsCache[area][dbnumber][start]])
                r = get_bool(res,0,index)
                if self.aw.seriallogflag:
                    self.aw.addserial(f'S7 readBool_cached({area},{dbnumber},{start},{index},{force}) => {r}')
                _log.debug('return cached value => %s', r)
                return r
            self.connect()
            if self.isConnected():
                retry = self.readRetries
                res = None
                while True:
                    self.waitToEnsureMinTimeBetweenRequests()
                    try:
                        res = self.plc.read_area(self.areas[area],dbnumber,start,1)
                    except Exception as e: # pylint: disable=broad-except
                        _log.exception(e)
                        res = None
                    if res is None:
                        if retry > 0:
                            retry = retry - 1
                        else:
                            raise Exception('result None')
                    else:
                        break
                if res is None:
                    return None
                if self.commError: # we clear the previous error and send a message
                    self.commError = False
                    self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Resumed'))
                r = get_bool(res,0,index)
                if self.aw.seriallogflag:
                    self.aw.addserial(f'S7 readBool({area},{dbnumber},{start},{index},{force}) => {r}')
                return r
            self.commError = True
            self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Error: connecting to PLC failed'))
            return None
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Error') + f' readBool({area},{dbnumber},{start},{index},{force}): {str(e)}',getattr(exc_tb, 'tb_lineno', '?'))
                if self.aw.seriallogflag:
                    self.aw.addserial(f'S7 readBool({area},{dbnumber},{start},{index},{force}) => S7 Communication Error: {str(e)}')
            self.commError = True
            return None
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
