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
# Marko Luther, 2023

import time
import sys
import logging
from typing import Final, List, Dict, Tuple, Optional, Iterator, TYPE_CHECKING, no_type_check

if TYPE_CHECKING:
    from snap7.client import Client as S7Client
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import

try:
    # >= v2.0
    from snap7.type import Area # type:ignore[import-not-found, unused-ignore]
except Exception: # pylint: disable=broad-except
    # < v2.0
    from snap7.types import Areas # type:ignore[import-not-found, unused-ignore] # noqa: F401 # pylint: disable=unused-import
from snap7.util.getters import get_bool, get_int, get_real
from snap7.util.setters import set_bool, set_int, set_real

import artisanlib.util

try:
    from PyQt6.QtCore import QSemaphore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QSemaphore # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


_log: Final[logging.Logger] = logging.getLogger(__name__)


class s7port:

    __slots__ = [ 'aw', 'readRetries', 'channels', 'default_host', 'host', 'port', 'rack', 'slot', 'lastReadResult', 'area', 'db_nr', 'start', 'type', 'mode',
        'div', 'optimizer', 'fetch_max_blocks', 'fail_on_cache_miss', 'activeRegisters', 'readingsCache', 'PID_area', 'PID_db_nr', 'PID_SV_register', 'PID_p_register',
        'PID_i_register', 'PID_d_register', 'PID_ON_action', 'PID_OFF_action', 'PIDmultiplier', 'SVtype', 'SVmultiplier', 'COMsemaphore',
        'areas', 'last_request_timestamp', 'min_time_between_requests', 'is_connected', 'plc', 'commError' ]

    def __init__(self, aw:'ApplicationWindow') -> None:
        self.aw = aw

        self.readRetries:int = 1
        self.channels:int = 12 # maximal number of S7 channels
        self.default_host:Final[str] = '127.0.0.1'
        self.host:str = self.default_host # the TCP host
        self.port:int = 102 # the TCP port
        self.rack:int = 0 # 0,..,7
        self.slot:int = 0 # 0,..,31

        self.lastReadResult:float = 0. # this is set by eventaction following some custom button/slider S/ actions with "read" command

        self.area:List[int] = [0]*self.channels
        self.db_nr:List[int] = [1]*self.channels
        self.start:List[int] = [0]*self.channels
        self.type:List[int] = [0]*self.channels # type 0 => int, type 1 => float, type 2 => intFloat
        #  type 3 => Bool(0), type 4 => Bool(1), type 5 => Bool(2), type 6 => Bool(3), type 7 => Bool(4), type 8 => Bool(5), type 9 => Bool(6), type 10 => Bool(7)
        self.mode:List[int] = [0]*self.channels # temp mode is an int here, 0:__,1:C,2:F (this is different than other places)
        self.div:List[int] = [0]*self.channels

        self.optimizer:bool = True # if set, values of consecutive register addresses are requested in single requests
        self.fetch_max_blocks:bool = False # if set, the optimizer fetches only one sequence per area from the minimum to the maximum register ignoring gaps
        self.fail_on_cache_miss:bool = True # if False and request cannot be resolved from optimizer cache while optimizer is active,
            # send individual reading request; if set to True, never send individual data requests while optimizer is on
            # NOTE: if TRUE read requests with force=False (default) will fail

        # S7 areas associated to dicts associating S7 DB numbers to registers in use
        # for optimized read of full register segments with single requests
        # this dict is re-computed on each connect() by a call to updateActiveRegisters()
        # NOTE: for registers of type float (32bit = 2x16bit) also the succeeding register is registered here
        # S7 area => db_nr => [registers]
        self.activeRegisters:Dict[int, Dict[int, List[int]]] = {}

        # the readings cache that is filled by requesting sequences of values in blocks
        # readingsCache is a dict associating area to dicts associating db numbers to dicts associating registers to readings
        # S7 area => db_nr => register => value
        self.readingsCache:Dict[int, Dict[int, Dict[int, int]]] = {}

        self.PID_area:int = 0
        self.PID_db_nr:int = 0
        self.PID_SV_register:int = 0
        self.PID_p_register:int = 0
        self.PID_i_register:int = 0
        self.PID_d_register:int = 0
        self.PID_ON_action:str = ''
        self.PID_OFF_action:str = ''
        self.PIDmultiplier:int = 0
        self.SVtype:int = 0
        self.SVmultiplier:int = 0

        self.COMsemaphore:QSemaphore = QSemaphore(1)

        # we do not use the snap7 enums here to avoid the import for non S7 users
        self.areas:Optional[List[Area]] = None # type:ignore[reportPossiblyUnboundVariable, unused-ignore, no-any-unimported] # lazy initialized in initArray() on connect
        self.last_request_timestamp:float = time.time()
        self.min_time_between_requests:float = 0.04

        self.is_connected:bool = False # local cache of the connection state

        self.plc:Optional[S7Client] = None
        self.commError:bool = False # True after a communication error was detected and not yet cleared by receiving proper data

################

    @no_type_check # as types changed between vs 1.x and 2.x
    def initArrays(self) -> None:
        if self.areas is None:
            try:
                # >= v2.0
                self.areas = [
                    Area.PE, # 129, 0x81
                    Area.PA, # 130, 0x82
                    Area.MK, # 131, 0x83
                    Area.CT, #  28, 0x1C
                    Area.TM, #  29, 0x1D
                    Area.DB  # 132, 0x84
                ]
            except Exception: # pylint: disable=broad-except
                # < v2.0
                self.areas = [
                    Areas.PE, # 129, 0x81 # pylint: disable=used-before-assignment
                    Areas.PA, # 130, 0x82
                    Areas.MK, # 131, 0x83
                    Areas.CT, #  28, 0x1C
                    Areas.TM, #  29, 0x1D
                    Areas.DB  # 132, 0x84
                ]

    # waits if need to ensure a minimal time delta between network requests which are scheduled directly after this functions evaluation and set the new timestamp
    def waitToEnsureMinTimeBetweenRequests(self) -> None:
        elapsed = time.time() - self.last_request_timestamp
        if elapsed < self.min_time_between_requests:
            time.sleep(self.min_time_between_requests - elapsed)
        self.last_request_timestamp = time.time()

################


    def setPID(self, p:float, i:float, d:float, PIDmultiplier:int) -> None:
        _log.debug('setPID(%s,%s,%s,%s)',p,i,d,PIDmultiplier)
        if self.PID_area and not self.PID_p_register == self.PID_i_register == self.PID_d_register == 0:
            multiplier = 1.
            if PIDmultiplier == 1:
                multiplier = 10.
            elif PIDmultiplier == 2:
                multiplier = 100.
            self.writeInt(self.PID_area-1,self.PID_db_nr,self.PID_p_register,p*multiplier)
            self.writeInt(self.PID_area-1,self.PID_db_nr,self.PID_i_register,i*multiplier)
            self.writeInt(self.PID_area-1,self.PID_db_nr,self.PID_d_register,d*multiplier)

    def setTarget(self,sv:float, SVmultiplier:int) -> None:
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

    def isConnected(self) -> bool:
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

    def disconnect(self) -> None:
# don't stop the PLC as we want to keep it running beyond the Artisan disconnect!!
#        try:
#            self.plc.plc_stop()
#        except:
#            pass
        try:
            if self.plc is not None:
                _log.debug('disconnect()')
                self.plc.disconnect()
                self.clearReadingsCache()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        try:
            if self.plc is not None:
                self.plc.destroy()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        self.plc = None
        self.is_connected = False


    def connect(self) -> None:
        if self.plc is None:
            _log.debug('connect() create S7Client')
            # create a client instance
            from artisanlib.s7client import S7Client
            self.plc = S7Client()
            self.initArrays() # initialize S7 arrays

        # next reset client instance if not yet connected to ensure a fresh start
        if not self.isConnected():
            _log.debug('connect(): connecting')
            try:
#                if self.plc is None:
#                    from artisanlib.s7client import S7Client # pylint: disable=reimported
#                    self.plc = S7Client()
#                    self.initArrays() # initialize S7 arrays
#                else:
#                    self.plc.disconnect()
                self.plc.disconnect()
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
            time.sleep(0.2)
            if artisanlib.util.isOpen(self.host,self.port):
                try:
                    assert self.plc is not None
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
                    from artisanlib.s7client import S7Client # ylint: disable=reimported
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
            else:
                self.aw.sendmessage(QApplication.translate('Message','S7 connection failed'))



########## S7 optimizer for fetching register data in batches

    # S7 area => db_nr => [registers]
    def updateActiveRegisters(self) -> None:
        _log.debug('updateActiveRegisters()')
        self.activeRegisters = {}
        for c in range(self.channels):
            area = self.area[c]-1
            if area != -1:
                db_nr = self.db_nr[c]
                register = self.start[c]
                registers = [register] # BOOL
                if self.type[c] in {1,2}: # FLOAT (or FLOAT2INT)
                    registers.append(register+1)
                    registers.append(register+2)
                    registers.append(register+3)
                elif self.type[c] == 0: # INT
                    registers.append(register+1)
                if area not in self.activeRegisters:
                    self.activeRegisters[area] = {}
                if db_nr in self.activeRegisters[area]:
                    self.activeRegisters[area][db_nr].extend(registers)
                else:
                    self.activeRegisters[area][db_nr] = registers

    def clearReadingsCache(self) -> None:
        _log.debug('clearReadingsCache()')
        self.readingsCache = {}

    def cacheReadings(self,area:int, db_nr:int, register:int, results:bytearray) -> None:
        if area not in self.readingsCache:
            self.readingsCache[area] = {}
        if db_nr not in self.readingsCache[area]:
            self.readingsCache[area][db_nr] = {}
        try:
            for i,v in enumerate(results):
                self.readingsCache[area][db_nr][register+i] = v
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    def readActiveRegisters(self) -> None:
        if not self.optimizer:
            return
        try:
            _log.debug('readActiveRegisters()')
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.clearReadingsCache()
            self.connect()
            if self.isConnected():
                for area, db_numbers in self.activeRegisters.items():
                    for db_nr, registers in db_numbers.items():
                        sorted_registers:List[int] = sorted(registers)
                        sequences:List[Tuple[int, int]]
                        if self.fetch_max_blocks:
                            sequences = [(sorted_registers[0],sorted_registers[-1])]
                        else:
                            # split in successive sequences
                            gaps:List[List[int]] = [[s, e] for s, e in zip(sorted_registers, sorted_registers[1:]) if s+1 < e] # ylint: disable=used-before-assignment
                            edges:Iterator[int] = iter(sorted_registers[:1] + sum(gaps, []) + sorted_registers[-1:])
                            sequences = list(zip(edges, edges)) # list of pairs of the form (start-register,end-register)
                        for seq in sequences:
                            retry = self.readRetries
                            register = seq[0]
                            count = seq[1]-seq[0] + 1
                            res = None
                            while True:
                                self.waitToEnsureMinTimeBetweenRequests()
                                _log.debug('readActive(%d,%d,%d,%d)', area, db_nr, register, count)
                                try:
                                    assert self.plc is not None
                                    assert self.areas is not None
                                    res = self.plc.read_area(self.areas[area],db_nr,register,count)
                                except Exception as e: # pylint: disable=broad-except
                                    _log.info('readActive(%d,%d,%d,%d) failed', area, db_nr, register, count)
                                    _log.exception(e)
                                    res = None
                                if res is None or len(res) != count:
                                    if retry > 0:
                                        retry = retry - 1
                                    else:
                                        raise Exception(f'read_area({area},{db_nr},{register},{count})') # pylint: disable=broad-exception-raised
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


    def writeFloat(self, area:int, dbnumber:int, start:int, value:float) -> None:
        _log.debug('writeFloat(%d,%d,%d,%.3f)',area,dbnumber,start,value)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                self.waitToEnsureMinTimeBetweenRequests()
                assert self.plc is not None
                assert self.areas is not None
                ba = self.plc.read_area(self.areas[area],dbnumber,start,4)
                if len(ba) != 4:
                    raise Exception(f'read_area({area},{dbnumber},{start},4) returned result of length {len(ba)}') # pylint: disable=broad-exception-raised
                set_real(ba, 0, float(value))
                self.waitToEnsureMinTimeBetweenRequests()
                self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.commError = True
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Error: connecting to PLC failed'))
        except Exception as e: # pylint: disable=broad-except
            _log.info('writeFloat(%d,%d,%d,%.3f) failed',area,dbnumber,start,value)
            _log.debug(e)
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Error') + ' writeFloat: ' + str(e),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.aw.addserial(f'S7 writeFloat({area},{dbnumber},{start},{value})')

    def writeInt(self, area:int, dbnumber:int, start:int, value:float) -> None:
        _log.debug('writeInt(%d,%d,%d,%d)',area,dbnumber,start,value)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                self.waitToEnsureMinTimeBetweenRequests()
                assert self.plc is not None
                assert self.areas is not None
                ba = self.plc.read_area(self.areas[area],dbnumber,start,2)
                if len(ba) != 2:
                    raise Exception(f'read_area({area},{dbnumber},{start},2) returned result of length {len(ba)}') # pylint: disable=broad-exception-raised
                set_int(ba, 0, int(round(value)))
                self.waitToEnsureMinTimeBetweenRequests()
                self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.commError = True
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Error: connecting to PLC failed'))
        except Exception as e: # pylint: disable=broad-except
            _log.info('writeInt(%d,%d,%d,%d) failed',area,dbnumber,start,value)
            _log.debug(e)
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Error') + ' writeInt: ' + str(e),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.aw.addserial(f'S7 writeInt({area},{dbnumber},{start},{value})')

    def maskWriteInt(self, area:int, dbnumber:int, start:int, and_mask:int, or_mask:int, value:int) -> None:
        _log.debug('maskWriteInt(%d,%d,%d,%s,%s,%d)',area,dbnumber,start,and_mask,or_mask,value)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                self.waitToEnsureMinTimeBetweenRequests()
                assert self.plc is not None
                assert self.areas is not None
                ba = self.plc.read_area(self.areas[area],dbnumber,start,2)
                if len(ba) != 2:
                    raise Exception(f'read_area({area},{dbnumber},{start},2) returned result of length {len(ba)}') # pylint: disable=broad-exception-raised
                new_val = (int(round(value)) & and_mask) | (or_mask & (and_mask ^ 0xFFFF))
                set_int(ba, 0, int(new_val))
                self.waitToEnsureMinTimeBetweenRequests()
                self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.commError = True
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Error: connecting to PLC failed'))
        except Exception as e: # pylint: disable=broad-except
            _log.info('maskWriteInt(%d,%d,%d,%s,%s,%d) failed',area,dbnumber,start,and_mask,or_mask,value)
            _log.debug(e)
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Error') + ' maskWriteInt: ' + str(e),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.aw.addserial(f'S7 writeInt({area},{dbnumber},{start},{value})')

    def writeBool(self, area:int, dbnumber:int, start:int, index:int, value:bool) -> None:
        _log.debug('writeBool(%d,%d,%d,%d,%s)',area,dbnumber,start,index,value)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                self.waitToEnsureMinTimeBetweenRequests()
                assert self.plc is not None
                assert self.areas is not None
                ba = self.plc.read_area(self.areas[area],dbnumber,start,1)
                if len(ba) != 1:
                    raise Exception(f'read_area({area},{dbnumber},{start},1) returned result of length {len(ba)}') # pylint: disable=broad-exception-raised
                set_bool(ba, 0, int(index), bool(value))
                self.waitToEnsureMinTimeBetweenRequests()
                self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.commError = True
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Error: connecting to PLC failed'))
        except Exception as e: # pylint: disable=broad-except
            _log.info('writeBool(%d,%d,%d,%d,%s) failed',area,dbnumber,start,index,value)
            _log.debug(e)
            if self.aw.qmc.flagon:
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror(QApplication.translate('Error Message','S7 Communication Error') + ' writeBool: ' + str(e),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.aw.addserial(f'S7 writeBool({area},{dbnumber},{start},{index},{value})')

    # if force the readings cache is ignored and fresh readings are requested
    def readFloat(self, area:int, dbnumber:int, start:int,force:bool=False) -> Optional[float]:
        _log.debug('readFloat(%d,%d,%d,%s)',area,dbnumber,start,force)
        if area == 0:
            return None
        res: Optional[bytearray]
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if self.optimizer and not force:
                if area in self.readingsCache and dbnumber in self.readingsCache[area] and start in self.readingsCache[area][dbnumber] \
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
                if self.fail_on_cache_miss:
                    _log.debug('optimizer cache miss')
                    return None
            self.connect()
            if self.isConnected():
                retry = self.readRetries
                res = None
                while True:
                    self.waitToEnsureMinTimeBetweenRequests()
                    try:
                        assert self.plc is not None
                        assert self.areas is not None
                        res = self.plc.read_area(self.areas[area],dbnumber,start,4)
                    except Exception as e: # pylint: disable=broad-except
                        _log.info('readFloat(%d,%d,%d,%s) failed',area,dbnumber,start,force)
                        _log.exception(e)
                        res = None
                    if res is None or len(res) != 4:
                        if retry > 0:
                            retry = retry - 1
                        else:
                            raise Exception('result None') # pylint: disable=broad-exception-raised
                    else:
                        break
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
            _log.info('readFloat(%d,%d,%d,%s) failed',area,dbnumber,start,force)
            _log.debug(e)
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
    def peekFloat(self, area:int, dbnumber:int, start:int) -> Optional[float]:
        _log.debug('peekFloat(%d,%d,%d)',area,dbnumber,start)
        if area == 0:
            return None
        try:
            self.connect()
            if self.isConnected():
                self.waitToEnsureMinTimeBetweenRequests()
                assert self.plc is not None
                assert self.areas is not None
                res = self.plc.read_area(self.areas[area],dbnumber,start,4)
                if len(res) != 4:
                    raise Exception(f'read_area({area},{dbnumber},{start},4) returned result of length {len(res)}') # pylint: disable=broad-exception-raised
                return get_real(res,0)
            return None
        except Exception as e: # pylint: disable=broad-except
            _log.info('peekFloat(%d,%d,%d) failed',area,dbnumber,start)
            _log.debug(e)
            return None

    # if force the readings cache is ignored and fresh readings are requested
    def readInt(self, area:int, dbnumber:int, start:int, force:bool=False) -> Optional[int]:
        _log.debug('readInt(%d,%d,%d,%s)',area,dbnumber,start,force)
        if area == 0:
            return None
        res: Optional[bytearray]
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if self.optimizer and not force:
                if area in self.readingsCache and dbnumber in self.readingsCache[area] and start in self.readingsCache[area][dbnumber] \
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
                if self.fail_on_cache_miss:
                    _log.debug('optimizer cache miss')
                    return None
            self.connect()
            if self.isConnected():
                retry = self.readRetries
                res = None
                while True:
                    self.waitToEnsureMinTimeBetweenRequests()
                    try:
                        assert self.plc is not None
                        assert self.areas is not None
                        res = self.plc.read_area(self.areas[area],dbnumber,start,2)
                    except Exception as e: # pylint: disable=broad-except
                        _log.info('readInt(%d,%d,%d,%s) failed',area,dbnumber,start,force)
                        _log.exception(e)
                        res = None
                    if res is None or len(res) != 2:
                        if retry > 0:
                            retry = retry - 1
                        else:
                            raise Exception('result None') # pylint: disable=broad-exception-raised
                    else:
                        break
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
            _log.info('readInt(%d,%d,%d,%s) failed',area,dbnumber,start,force)
            _log.debug(e)
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
    def peekInt(self, area:int, dbnumber:int, start:int) -> Optional[int]:
        _log.debug('peakInt(%d,%d,%d)',area,dbnumber,start)
        if area == 0:
            return None
        try:
            self.connect()
            if self.isConnected():
                self.waitToEnsureMinTimeBetweenRequests()
                assert self.plc is not None
                assert self.areas is not None
                res = self.plc.read_area(self.areas[area],dbnumber,start,2)
                if len(res) != 2:
                    raise Exception(f'read_area({area},{dbnumber},{start},2) returned result of length {len(res)}') # pylint: disable=broad-exception-raised
                return get_int(res,0)
            return None
        except Exception as e: # pylint: disable=broad-except
            _log.info('peakInt(%d,%d,%d) failed',area,dbnumber,start)
            _log.debug(e)
            return None

    # if force the readings cache is ignored and fresh readings are requested
    def readBool(self, area:int, dbnumber:int, start:int, index:int, force:bool = False) -> Optional[bool]:
        _log.debug('readBool(%d,%d,%d,%s)',area,dbnumber,start,force)
        if area == 0:
            return None
        res: Optional[bytearray]
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if self.optimizer and not force:
                if area in self.readingsCache and dbnumber in self.readingsCache[area] and start in self.readingsCache[area][dbnumber]:
                    # cache hit
                    res = bytearray([
                        self.readingsCache[area][dbnumber][start]])
                    r = get_bool(res,0,index)
                    if self.aw.seriallogflag:
                        self.aw.addserial(f'S7 readBool_cached({area},{dbnumber},{start},{index},{force}) => {r}')
                    _log.debug('return cached value => %s', r)
                    return r
                if self.fail_on_cache_miss:
                    _log.debug('optimizer cache miss')
                    return None
            self.connect()
            if self.isConnected():
                retry = self.readRetries
                res = None
                while True:
                    self.waitToEnsureMinTimeBetweenRequests()
                    try:
                        assert self.plc is not None
                        assert self.areas is not None
                        res = self.plc.read_area(self.areas[area],dbnumber,start,1)
                    except Exception as e: # pylint: disable=broad-except
                        _log.info('readBool(%d,%d,%d,%s) failed',area,dbnumber,start,force)
                        _log.exception(e)
                        res = None
                    if res is None or len(res) != 1:
                        if retry > 0:
                            retry = retry - 1
                        else:
                            raise Exception('result None') # pylint: disable=broad-exception-raised
                    else:
                        break
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
            _log.info('readBool(%d,%d,%d,%s) failed',area,dbnumber,start,force)
            _log.debug(e)
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
