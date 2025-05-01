#
# ABOUT
# MODBUS support for Artisan

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
import asyncio
import logging

import pymodbus
from pymodbus.pdu import ExceptionResponse
from pymodbus.client import AsyncModbusSerialClient, AsyncModbusUdpClient, AsyncModbusTcpClient
from pymodbus.client.mixin import ModbusClientMixin
try:
    from pymodbus.framer import FramerType # type:ignore[attr-defined,unused-ignore]
except Exception: # pylint: disable=broad-except
    # FramerType named Framer in pymodbus < 3.7
    from pymodbus.framer import Framer as FramerType # type:ignore[attr-defined, no-redef, unused-ignore]

from packaging.version import Version
from typing import Final, Optional, List, Dict, Tuple, Union, Literal, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    from pymodbus.client import ModbusBaseClient # pylint: disable=unused-import
    from pymodbus.pdu.pdu import ModbusPDU # pylint: disable=unused-import

try:
    from PyQt6.QtCore import QSemaphore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QSemaphore # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.util import debugLogLevelActive
from artisanlib.async_comm import AsyncLoopThread


_log: Final[logging.Logger] = logging.getLogger(__name__)


def convert_to_bcd(value:int) -> int:
    """Converts a decimal value to a bcd value

    Args:
        value: the decimal value to to pack into bcd

    Returns:
        The number in bcd form
    """
    place, bcd = 0, 0
    while value > 0:
        nibble = value % 10
        bcd += nibble << place
        value = value // 10
        place += 4
    return bcd


def convert_from_bcd(value: int) -> int:
    """Converts a bcd value to a decimal value

    Args:
        value: the value to unpack from bcd

    Returns:
        The number in decimal form
    """
    place, decimal = 1, 0
    while value > 0:
        nibble = value & 0xf
        decimal += nibble * place
        value >>= 4
        place *= 10
    return decimal



###########################################################################################
##################### MODBUS PORT #########################################################
###########################################################################################


class modbusport:
    """ this class handles the communications with all the modbus devices"""

    __slots__ = [ 'aw', 'legacy_pymodbus', 'modbus_serial_read_delay', 'modbus_serial_connect_delay', 'modbus_serial_write_delay', 'maxCount', 'readRetries', 'default_comport', 'comport', 'baudrate', 'bytesize', 'parity', 'stopbits',
        'timeout', 'IP_timeout', 'IP_retries', 'serial_readRetries', 'PID_slave_ID', 'PID_SV_register', 'PID_p_register', 'PID_i_register', 'PID_d_register', 'PID_ON_action', 'PID_OFF_action',
        'channels', 'inputSlaves', 'inputRegisters', 'inputFloats', 'inputBCDs', 'inputFloatsAsInt', 'inputBCDsAsInt', 'inputSigned', 'inputCodes', 'inputDivs',
        'inputModes', 'optimizer', 'fetch_max_blocks', 'fail_on_cache_miss', 'disconnect_on_error', 'acceptable_errors', 'activeRegisters',
        'readingsCache', 'SVmultiplier', 'PIDmultiplier', 'SVwriteLong', 'SVwriteFloat',
        'wordorderLittle', '_asyncLoopThread', '_client', 'COMsemaphore', 'default_host', 'host', 'port', 'type', 'lastReadResult', 'commError' ]

    def __init__(self, aw:'ApplicationWindow') -> None:
        self.aw = aw

        self.legacy_pymodbus:bool = False
        if Version(pymodbus.__version__) < Version('3.8.2'):
            # pymodbus before 3.8.2 did not had the option to specify the word order in datatype conversions
            self.legacy_pymodbus = True

        self.modbus_serial_read_delay       :Final[float] = 0.035 # in seconds
        self.modbus_serial_write_delay      :Final[float] = 0.080 # in seconds
        self.modbus_serial_connect_delay    :float = 0.5          # in seconds (user configurable delay after serial connect; important for Arduino based slaves that reboot on connect)

        self.maxCount:Final[int] = 125 # the maximum number of registers that can be fetched in one request according to the MODBUS spec
        self.readRetries:int = 0  # retries
        #default initial settings. They are changed by settingsload() at initiation of program according to the device chosen
        self.default_comport:Final[str] = 'COM5'      #NOTE: this string should not be translated.
        self.comport:str = self.default_comport       #NOTE: this string should not be translated.
        self.baudrate:int = 115200
        self.bytesize:int = 8
        self.parity:str = 'N' # Literal['O','E','N']
        self.stopbits:int = 1
        self.timeout:float = 0.4 # serial MODBUS timeout
        self.serial_readRetries:int = 1 # user configurable, defaults to 0
        self.IP_timeout:float = 0.2 # UDP/TCP MODBUS timeout in seconds
        self.IP_retries:int = 1 # UDP/TCP MODBUS retries (max 3)
        self.PID_slave_ID:int = 0
        self.PID_SV_register:int = 0
        self.PID_p_register:int = 0
        self.PID_i_register:int = 0
        self.PID_d_register:int = 0
        self.PID_ON_action:str = ''
        self.PID_OFF_action:str = ''

        self.channels:Final[int] = 10
        self.inputSlaves:List[int] = [0]*self.channels
        self.inputRegisters:List[int] = [0]*self.channels
        # decoding (default: 16bit uInt)
        self.inputFloats:List[bool] = [False]*self.channels       # 32bit Floats
        self.inputBCDs:List[bool] = [False]*self.channels         # 32bit uInt BCD decoded
        self.inputFloatsAsInt:List[bool] = [False]*self.channels  # 32bit uInt/sInt
        self.inputBCDsAsInt:List[bool] = [False]*self.channels    # 16bit uInt/sInt
        self.inputSigned:List[bool] = [False]*self.channels       # if True, decode Integers as signed otherwise as unsigned
        #
        self.inputCodes:List[int] = [3]*self.channels
        self.inputDivs:List[int] = [0]*self.channels # 0: none, 1: 1/10, 2:1/100 # :List[Literal[0,1,2]]
        self.inputModes:List[str] = ['C']*self.channels

        self.optimizer:bool = True # if set, values of consecutive register addresses are requested in single requests
        # MODBUS functions associated to dicts associating MODBUS slave ids to registers in use
        # for optimized read of full register segments with single requests
        # this dict is re-computed on each connect() by a call to updateActiveRegisters()
        # NOTE: for registers of type float and BCD (32bit = 2x16bit) also the succeeding registers are registered
        self.fetch_max_blocks:bool = False # if set, the optimizer fetches only one sequence per area from the minimum to the maximum of "optimized" registers ignoring gaps (note that function 1 and 2 registers are not counting as they are never optimized)
        self.fail_on_cache_miss:bool = True # if False and request cannot be resolved from optimizer cache while optimizer is active,
            # send individual reading request; if set to True, never send individual data requests while optimizer is on
            # NOTE: if TRUE read requests with force=False (default) will fail
        self.disconnect_on_error:bool = True # if True we explicitly disconnect the MODBUS connection on IO errors (was: if on MODBUS serial and restart it on next request)
        self.acceptable_errors = 3 # the number of errors that are acceptable without a disconnect/reconnect. If set to 0 every error triggers a reconnect if disconnect_on_error is True

        self.activeRegisters:Dict[int, Dict[int, List[int]]] = {}
        # the readings cache that is filled by requesting sequences of values of activeRegisters in blocks
        self.readingsCache:Dict[int, Dict[int, Dict[int, int]]] = {}

        self.SVmultiplier:int = 0  # 0:no, 1:10x, 2:100x # Literal[0,1,2]
        self.SVwriteLong:bool = False # if True (and SVwriteFloat is False)  use self.writeLong() to update the SV, otherwise self.writeRegister() or self.writeWord()
        self.SVwriteFloat:bool = False # if True use self.writeWord() to update the SV, otherwise self.writeRegister() or self.writeLong()
        self.PIDmultiplier:int = 0  # 0:no, 1:10x, 2:100x # :Literal[0,1,2]
        self.wordorderLittle:bool = True

        self._asyncLoopThread: Optional[AsyncLoopThread]     = None # the asyncio AsyncLoopThread object
        self._client: Optional[ModbusBaseClient] = None


        self.COMsemaphore:QSemaphore = QSemaphore(1)
        self.default_host:Final[str] = '127.0.0.1'
        self.host:str = self.default_host # the TCP/UDP host
        self.port:int = 502 # the TCP/UDP port
        self.type:int = 0 # :Literal[0,1,2,3,4]
        # type =
        #    0: Serial RTU
        #    1: Serial ASCII
        #    2: Serial Binary
        #    3: TCP
        #    4: UDP
        self.lastReadResult:Optional[int] = None # this is set by eventaction following some custom button/slider Modbus actions with "read" command

        self.commError:int = 0 # number of errors that occurred after the last connect; cleared by receiving proper data



    # data conversions

    def word_order(self) -> Literal['big', 'little']:
        return 'little' if self.wordorderLittle else 'big'

#

    def convert_16bit_uint_to_registers(self, value:int) -> List [int]:
        return ModbusClientMixin.convert_to_registers(value, ModbusClientMixin.DATATYPE.UINT16, word_order=self.word_order()) # type:ignore[call-arg, unused-ignore]

    #- unused:

#    def convert_16bit_int_to_registers(self, value:int) -> List [int]:
#        return ModbusClientMixin.convert_to_registers(value, ModbusClientMixin.DATATYPE.INT16, word_order=self.word_order()) # type:ignore[call-arg, unused-ignore]
#
#    def convert_32bit_uint_to_registers(self, value:int) -> List [int]:
#        return ModbusClientMixin.convert_to_registers(value, ModbusClientMixin.DATATYPE.UINT32, word_order=self.word_order()) # type:ignore[call-arg, unused-ignore]

    #-

    def convert_32bit_int_to_registers(self, value:int) -> List [int]:
        if self.legacy_pymodbus:
            return ModbusClientMixin.convert_to_registers(value, ModbusClientMixin.DATATYPE.INT32)[::-1]
        return ModbusClientMixin.convert_to_registers(value, ModbusClientMixin.DATATYPE.INT32, word_order=self.word_order()) # type:ignore[call-arg, unused-ignore]

    def convert_float_to_registers(self, value:float) -> List[int]:
        if self.legacy_pymodbus:
            return ModbusClientMixin.convert_to_registers(value, ModbusClientMixin.DATATYPE.FLOAT32)[::-1]
        return ModbusClientMixin.convert_to_registers(value, ModbusClientMixin.DATATYPE.FLOAT32, word_order=self.word_order()) # type:ignore[call-arg, unused-ignore]


##############################


    def convert_16bit_uint_from_registers(self, registers:List[int]) -> int:
        res = ModbusClientMixin.convert_from_registers(registers, ModbusClientMixin.DATATYPE.UINT16, word_order=self.word_order()) # type:ignore[call-arg, unused-ignore]
        if isinstance(res, int):
            return res
        return -1


    def convert_16bit_int_from_registers(self, registers:List[int]) -> int:
        res = ModbusClientMixin.convert_from_registers(registers, ModbusClientMixin.DATATYPE.INT16, word_order=self.word_order()) # type:ignore[call-arg, unused-ignore]
        if isinstance(res, int):
            return res
        return -1


    def convert_32bit_uint_from_registers(self, registers:List[int]) -> int:
        res = ModbusClientMixin.convert_from_registers(registers, ModbusClientMixin.DATATYPE.UINT32, word_order=self.word_order()) # type:ignore[call-arg, unused-ignore]
        if isinstance(res, int):
            return res
        return -1


    def convert_32bit_int_from_registers(self, registers:List[int]) -> int:
        if self.legacy_pymodbus:
            res = ModbusClientMixin.convert_from_registers(registers[::-1], ModbusClientMixin.DATATYPE.INT32)
        else:
            res = ModbusClientMixin.convert_from_registers(registers, ModbusClientMixin.DATATYPE.INT32, word_order=self.word_order()) # type:ignore[call-arg, unused-ignore]
        if isinstance(res, int):
            return res
        return -1


    def convert_float_from_registers(self, registers:List[int]) -> float:
        if self.legacy_pymodbus:
            res = ModbusClientMixin.convert_from_registers(registers[::-1], ModbusClientMixin.DATATYPE.FLOAT32)
        else:
            res = ModbusClientMixin.convert_from_registers(registers, ModbusClientMixin.DATATYPE.FLOAT32, word_order=self.word_order()) # type:ignore[call-arg, unused-ignore]
        if isinstance(res, float):
            return res
        return -1


    # this guarantees a minimum of 30 milliseconds between readings and 80ms between writes (according to the Modbus spec) on serial connections
    # this sleep delays between requests seems to be beneficial on slow RTU serial connections like those of the FZ-94
    def sleepBetween(self, write:bool = False) -> None:
        pass
#        if write:
#            pass # handled in MODBUS lib
##            if self.type in {3,4}: # TCP or UDP
##                pass
##            else:
##                time.sleep(self.modbus_serial_write_delay)
#        elif self.type in {3, 4}: # delay between reads only on serial connections
#            pass
#        else:
#            time.sleep(self.modbus_serial_read_delay)

    @staticmethod
    def address2register(addr:Union[float, int], code:int = 3) -> int:
        if code in {3, 6}:
            return int(addr) - 40001
        return int(addr) - 30001

    def isConnected(self) -> bool:
        return self._client is not None and self._client.connected

    def disconnect(self) -> None:
        try:
            if self._client is not None:
                _log.debug('disconnect()')
                self._client.close()
                self.clearReadingsCache()
                self.aw.sendmessage(QApplication.translate('Message', 'MODBUS disconnected'))
                del self._client
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        self._client = None
        self._asyncLoopThread = None

    def clearCommError(self) -> None:
        if self.commError>0:
            self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Resumed'))
        self.commError = 0

    def disconnectOnError(self) -> None:
        # we only disconnect on error if mechanism is active, we are no longer connected or there is a IO commError, [ and we are on serial MODBUS (IP MODBUS reconnects automatically) NOTE: this seems to succeed in any case!?]
        if self.disconnect_on_error and (self.commError>self.acceptable_errors or not self.isConnected()): # and self.type < 3:
            _log.info('MODBUS disconnectOnError: %s', self.commError)
            self.disconnect()

    # t a duration between start and end time in seconds to be formatted in a string as ms
    @staticmethod
    def formatMS(start:float, end:float) -> str:
        return f'{(end-start)*1000:.1f}'


    def connect(self) -> None:
        if self._asyncLoopThread is None:
            self._asyncLoopThread = AsyncLoopThread()
        asyncio.run_coroutine_threadsafe(self.connect_async(), self._asyncLoopThread.loop).result()


    async def connect_async(self) -> None:
        if not self.isConnected():
            self.commError = 0
            try:
                # as in the following the port is None, no port is opened on creation of the (py)serial object
                if self.type == 1: # Serial ASCII
                    self._client = AsyncModbusSerialClient(
                        framer=FramerType.ASCII, # type:ignore[unused-ignore]
                        port=self.comport,
                        baudrate=self.baudrate,
                        bytesize=self.bytesize,
                        parity=self.parity,
                        stopbits=self.stopbits,
                        retries=self.serial_readRetries,   # number of send retries
                        reconnect_delay=0, # avoid automatic reconnection
                        # timeout is in seconds and defaults to 3
                        timeout=min((self.aw.qmc.delay/2000), self.timeout)) # the timeout should not be larger than half of the sampling interval
#                    self.readRetries = self.serial_readRetries # retire Artisan-level retries
                elif self.type == 2: # Serial Binary
                    pass # serial binary is no longer supported by pymodbus 3.7
                elif self.type == 3: # TCP
                    self._client = AsyncModbusTcpClient(
                            host=self.host,
                            port=self.port,
                            retries=self.IP_retries,                # number of send retries
#                            reconnect_delay=0.1,
#                            reconnect_delay_max=300,
                            # timeout is in seconds (int) and defaults to 3
                            timeout=min((self.aw.qmc.delay/2000), self.IP_timeout) # the timeout should not be larger than half of the sampling interval
#                            on_connect_callback # : Callable[[bool], None] | None = None
                            )
#                    self.readRetries = self.IP_retries # retire Artisan-level retries
                elif self.type == 4: # UDP
                    self._client = AsyncModbusUdpClient(
                        host=self.host,
                        port=self.port,
                        retries=0,                # number of send retries (if set to n>0 each requests is sent n-types on MODBUS UDP!)
#                        reconnect_delay=0.1,
#                        reconnect_delay_max=300,
                        # timeout is in seconds (int) and defaults to 3
                        timeout=min((self.aw.qmc.delay/2000), self.IP_timeout) # the timeout should not be larger than half of the sampling interval
#                        on_connect_callback # : Callable[[bool], None] | None = None
                        )
#                    self.readRetries = self.IP_retries # retire Artisan-level retries
                else: # Serial RTU
                    self._client = AsyncModbusSerialClient(
                        framer=FramerType.RTU, # type:ignore[unused-ignore]
                        port=self.comport,
                        baudrate=self.baudrate,
                        bytesize=self.bytesize,
                        parity=self.parity,
                        stopbits=self.stopbits,
                        retries=self.serial_readRetries,              # number of send retries (ignored on sync client pymodbus 3.6.9, but not on 3.7.2)
                        #  NOTE: pymodbus sync client disconnects between retries, therefore we set this to 0; for the async client one might go with 1
                        timeout=min((self.aw.qmc.delay/2000), self.timeout)) # the timeout should not be larger than half of the sampling interval
#                    self.readRetries = self.serial_readRetries # retire Artisan-level retries
                _log.debug('connect(): connecting')
                if self._client is not None:
                    await self._client.connect()
                if self.isConnected():
                    self.updateActiveRegisters()
                    self.clearReadingsCache()
                    if self.type in {0,1}: # RTU/ASCII
                        # respect the user defined connect delay on serial connections
                        await asyncio.sleep(self.modbus_serial_connect_delay)
                    else: # all others
                        await asyncio.sleep(.3) # avoid possible hickups on startup
                    self.aw.sendmessage(QApplication.translate('Message', 'Connected via MODBUS'))
                else:
                    self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Error: failed to connect'))
            except Exception as ex: # pylint: disable=broad-except
                _log.exception(ex)
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror((QApplication.translate('Error Message','Modbus Error:') + ' connect() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

########## MODBUS optimizer for fetching register data in batches

    # MODBUS code => slave => [registers]
    def updateActiveRegisters(self) -> None:
        _log.debug('updateActiveRegisters()')
        self.activeRegisters = {}
        for c in range(self.channels):
            slave = self.inputSlaves[c]
            if slave != 0:
                register = self.inputRegisters[c]
                code = self.inputCodes[c]
                if code not in {1,2}: # MODBUS functions 1 and 2 are not optimized
                    registers = [register]
                    if self.inputFloats[c] or self.inputBCDs[c] or self.inputFloatsAsInt[c]:
                        registers.append(register+1)
                    if code not in self.activeRegisters:
                        self.activeRegisters[code] = {}
                    if slave in self.activeRegisters[code]:
                        self.activeRegisters[code][slave].extend(registers)
                    else:
                        self.activeRegisters[code][slave] = registers
        _log.debug('active registers: %s',self.activeRegisters)

    def clearReadingsCache(self) -> None:
        _log.debug('clearReadingsCache()')
        self.readingsCache = {}

    def cacheReadings(self, code:int, slave:int, register:int, results:List[int]) -> None:
        if code not in self.readingsCache:
            self.readingsCache[code] = {}
        if slave not in self.readingsCache[code]:
            self.readingsCache[code][slave] = {}
        for i,v in enumerate(results):
            self.readingsCache[code][slave][register+i] = v
            if self.aw.seriallogflag:
                ser_str = f'cache reading : Slave = {slave} || Register = {register+i} || Rx = {v}'
                self.aw.addserial(ser_str)

    # first result signals an error
    # second result signals a server error which requires a disconnect/reconnect
    @staticmethod
    def invalidResult(res:Any, count:int) -> Tuple[bool, bool]:
        if res is None:
            _log.info('invalidResult(%d) => None', count)
            return True, False
        if isinstance(res, ExceptionResponse):
            _log.info('invalidResult(%d) => received exception from device', count)
            return True, False
        if res.isError():
            _log.info('invalidResult(%d) => pymodbus error: %s', count, res)
            return True, True
        if res.registers is None:
            _log.info('invalidResult(%d) => res.registers is None', count)
            return True,False
        # if count==0 no res.registers is expected as for MODBUS function 1 and 2
        if count>0 and len(res.registers) != count:
            _log.info('invalidResult(%d) => len(res.registers)=%d', count, len(res.registers))
            return True, False
        return False, False

    def readActiveRegisters(self) -> None:
        if not self.optimizer:
            return
        try:
            _log.debug('readActiveRegisters()')
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self._asyncLoopThread is not None and self.isConnected():
                asyncio.run_coroutine_threadsafe(self.read_active_registers_async(), self._asyncLoopThread.loop).result()
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    async def read_active_registers_async(self) -> None:
        error_disconnect = False # set to True if a serious error requiring a disconnect was detected
        try:
            assert self._client is not None
            self.clearReadingsCache()
            for code, slaves in self.activeRegisters.items():
                for slave, registers in slaves.items():
                    registers_sorted = sorted(registers)
                    sequences:List[Tuple[int,int]]
                    if self.fetch_max_blocks:
                        sequences = [(registers_sorted[0],registers_sorted[-1])]
                    else:
                        # split in successive sequences
                        gaps = [[s, er] for s, er in zip(registers_sorted, registers_sorted[1:]) if s+1 < er]
                        edges = iter(registers_sorted[:1] + sum(gaps, []) + registers_sorted[-1:])
                        sequences = list(zip(edges, edges)) # list of pairs of the form (start-register,end-register)
#                    just_send:bool = False
                    for seq in sequences:
                        retry:int = self.readRetries
                        register:int = seq[0]
                        count:int = seq[1]-seq[0] + 1
                        if 0 < count <= self.maxCount:
                            res:Optional[ModbusPDU] = None
                            tx:float = time.time()
                            while True:
                                _log.debug('readActive(%d,%d,%d,%d)', slave, code, register, count)
                                try:
                                    # we cache only MODBUS function 3 and 4 (not 1 and 2!)
                                    if code == 3:
                                        res = await self._client.read_holding_registers(address=register,count=count,slave=slave)
                                    elif code == 4:
                                        res = await self._client.read_input_registers(address=register,count=count,slave=slave)
                                except Exception as e: # pylint: disable=broad-except
                                    _log.info('readActive(%d,%d,%d,%d)', slave, code, register, count)
                                    _log.debug(e)
                                    res = None
                                error, disconnect = self.invalidResult(res,count)
                                if error:
                                    error_disconnect = error_disconnect or disconnect
                                    if retry > 0:
                                        retry = retry - 1
                                        await asyncio.sleep(0.020)
                                        _log.debug('retry')
                                    else:
                                        res = None
                                        raise Exception('Exception response') # pylint: disable=broad-exception-raised
                                else:
                                    break

                            #note: logged chars should be unicode not binary
                            if self.aw.seriallogflag and res is not None and hasattr(res, 'registers'):
                                if self.type < 3: # serial MODBUS
                                    ser_str = f'MODBUS readActiveregisters : {self.formatMS(tx,time.time())}ms => {self.comport},{self.baudrate},{self.bytesize},{self.parity},{self.stopbits},{self.timeout} || Slave = {slave} || Register = {register} || Code = {code} || Rx# = {len(res.registers)}'
                                else: # IP MODBUS
                                    ser_str = f'MODBUS readActiveregisters : {self.formatMS(tx,time.time())}ms => {self.host}:{self.port} || Slave = {slave} || Register = {register} || Code = {code} || Rx# = {len(res.registers)}'
                                _log.debug(ser_str)
                                self.aw.addserial(ser_str)

                            if res is not None and hasattr(res, 'registers'):
                                self.clearCommError()
                                self.cacheReadings(code,slave,register,res.registers)

        except Exception as ex: # pylint: disable=broad-except
            _log.debug(ex)
            self.disconnectOnError()
#            _, _, exc_tb = sys.exc_info()
#            self.aw.qmc.adderror((QApplication.translate("Error Message","Modbus Error:") + " readSingleRegister() {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
            self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Error'))
            if error_disconnect:
                self.commError = self.commError + 1

##########


    # function 15 (Write Multiple Coils)
    def writeCoils(self, slave:int, register:int, values:List[bool]) -> None:
        _log.debug('writeCoils(%d,%d,%s)', slave, register, values)
        if slave == 0:
            return
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self._asyncLoopThread is not None and self.isConnected():
                # wrap an Awaitable into a Coroutine
                async def write_coils_wrapper(client:'ModbusBaseClient', register:int, values:List[bool], slave:int) -> 'ModbusPDU':
                    return await client.write_coils(register, values, slave=slave)
                assert self._client is not None
                asyncio.run_coroutine_threadsafe(write_coils_wrapper(self._client, int(register), list(values), int(slave)), self._asyncLoopThread.loop).result()
#                time.sleep(.3) # avoid possible hickups on startup
        except Exception as ex: # pylint: disable=broad-except
            _log.info('writeCoils(%d,%d,%s)', slave, register, values)
            _log.debug(ex)
            self.disconnectOnError()
            _, _, exc_tb = sys.exc_info()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror((QApplication.translate('Error Message','Modbus Error:') + ' writeCoils() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    # function 5 (Write Single Coil)
    def writeCoil(self, slave:int ,register:int ,value:bool) -> None:
        _log.debug('writeCoil(%d,%d,%s)', slave, register, value)
        if slave == 0:
            return
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self._asyncLoopThread is not None and self.isConnected():
                # wrap an Awaitable into a Coroutine
                async def write_coil_wrapper(client:'ModbusBaseClient', register:int, value:bool, slave:int) -> 'ModbusPDU':
                    return await client.write_coil(register, value, slave=slave)
                assert self._client is not None
                asyncio.run_coroutine_threadsafe(write_coil_wrapper(self._client, int(register),value,int(slave)), self._asyncLoopThread.loop).result()
#                time.sleep(.3) # avoid possible hickups on startup
        except Exception as ex: # pylint: disable=broad-except
            _log.info('writeCoil(%d,%d,%s) failed', slave, register, value)
            _log.debug(ex)
            self.disconnectOnError()
            _, _, exc_tb = sys.exc_info()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror((QApplication.translate('Error Message','Modbus Error:') + ' writeCoil() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    # DEPRECATED: use writeSingle or writeWord (this one now just calls writeSingle with the value rounded to an integer)
    # write value to register on slave (function 6 for int or function 16 for float)
    # value can be one of string (containing an int or float), an int or a float
    def writeRegister(self, slave:int, register:int, value: Union[int, float, str]) -> None:
        _log.debug('writeRegister(%d,%d,%s)', slave, register, value)
        if slave == 0:
            return
        if isinstance(value, str):
            if '.' in value:
#                self.writeWord(slave, register, float(value))
                self.writeSingleRegister(slave, register, int(round(float(value))))
            else:
                self.writeSingleRegister(slave, register, int(value))
        elif isinstance(value, int):
            self.writeSingleRegister(slave,register,value)
        elif isinstance(value, float):
#            self.writeWord(slave,register,value)
            self.writeSingleRegister(slave,register,int(round(value)))

    # function 6 (Write Single Holding Register)
    def writeSingleRegister(self, slave:int, register:int, value:float) -> None:
        _log.debug('writeSingleRegister(%d,%d,%s)', slave, register, value)
        if slave == 0:
            return
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self._asyncLoopThread is not None and self.isConnected():
                assert self._client is not None
                # wrap an Awaitable into a Coroutine
                async def write_register_wrapper(client:'ModbusBaseClient', register:int, value:int, slave:int) -> 'ModbusPDU':
                    return await client.write_register(register, value, slave=slave)
                asyncio.run_coroutine_threadsafe(write_register_wrapper(self._client, int(register),int(round(value)),int(slave)), self._asyncLoopThread.loop).result()
#                time.sleep(.03) # avoid possible hickups on startup
        except Exception as ex: # pylint: disable=broad-except
            _log.info('writeSingleRegister(%d,%d,%s) failed', slave, register, int(round(value)))
            _log.debug(ex)
            self.disconnectOnError()
            _, _, exc_tb = sys.exc_info()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror((QApplication.translate('Error Message','Modbus Error:') + ' writeSingleRegister() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    # function 22 (Mask Write Register)
    # bits to be modified are "masked" with a 0 in the and_mask (not and_mask)
    # new bit values to be written are taken from the or_mask
    def maskWriteRegister(self, slave:int, register:int, and_mask:int, or_mask:int) -> None:
        _log.debug('maskWriteRegister(%d,%d,%s,%s)', slave, register, and_mask, or_mask)
        if slave == 0:
            return
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self._asyncLoopThread is not None and self.isConnected():
                # wrap an Awaitable into a Coroutine
                async def mask_write_register_wrapper(client:'ModbusBaseClient', register:int, and_mask:int, or_mask:int, slave:int) -> 'ModbusPDU':
                    return await client.mask_write_register(address=register, and_mask=and_mask, or_mask=or_mask, slave=slave)
                assert self._client is not None
                asyncio.run_coroutine_threadsafe(mask_write_register_wrapper(
                    self._client,
                    int(register),
                    int(and_mask),
                    int(or_mask),
                    int(slave)), self._asyncLoopThread.loop).result()

#                time.sleep(.03)
        except Exception as ex: # pylint: disable=broad-except
            _log.info('maskWriteRegister(%d,%d,%s,%s) failed', slave, register, and_mask, or_mask)
            if debugLogLevelActive():
                _log.debug(ex)
            self.disconnectOnError()
            _, _, exc_tb = sys.exc_info()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror((QApplication.translate('Error Message','Modbus Error:') + ' writeMask() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    # a local variant of function 22 (Mask Write Register)
    # the masks are evaluated locally on the given integer value and the result is send via
    # using function 6
    def localMaskWriteRegister(self, slave:int, register:int, and_mask:int, or_mask:int, value:int) -> None:
        _log.debug('localMaskWriteRegister(%d,%d,%s,%s,%s)', slave, register, and_mask, or_mask, value)
        if slave == 0:
            return
        new_val = (int(round(value)) & and_mask) | (or_mask & (and_mask ^ 0xFFFF))
        self.writeSingleRegister(slave,register,int(new_val))

    # function 16 (Write Multiple Holding Registers)
    # values is a list of integers or one integer (given floats are rounded to integers
    def writeRegisters(self, slave:int, register:int, values:Union[List[float], float]) -> None:
        _log.debug('writeRegisters(%d,%d,%s)', slave, register, values)
        if slave == 0:
            return
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self._asyncLoopThread is not None and self.isConnected():
                assert self._client is not None
                float_values:List[float] = (values if isinstance(values, list) else [float(values)])
                int_values:List[int] = [int(round(v)) for v in float_values]
                # wrap an Awaitable into a Coroutine
                async def write_registers_wrapper(client:'ModbusBaseClient', register:int, int_values:List[int], slave:int) -> 'ModbusPDU':
                    return await client.write_registers(register, int_values, slave=slave)
                asyncio.run_coroutine_threadsafe(write_registers_wrapper(self._client, int(register), int_values, int(slave)), self._asyncLoopThread.loop).result()
        except Exception as ex: # pylint: disable=broad-except
            _log.info('writeRegisters(%d,%d,%s) failed', slave, register, values)
            _log.debug(ex)
            self.disconnectOnError()
            _, _, exc_tb = sys.exc_info()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror((QApplication.translate('Error Message','Modbus Error:') + ' writeRegisters() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    # function 16 (Write Multiple Holding Registers)
    # value=int or float
    # writes a single precision 32bit float (2-registers)
    def writeWord(self, slave:int, register:int, value:float) -> None:
        _log.debug('writeWord(%d,%d,%s)', slave, register, value)
        if slave == 0:
            return
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self._asyncLoopThread is not None and self.isConnected():
                assert self._client is not None
                payload:List[int] = self.convert_float_to_registers(value)
                # wrap an Awaitable into a Coroutine
                async def write_registers_wrapper(client:'ModbusBaseClient', register:int, payload:List[int], slave:int) -> 'ModbusPDU':
                    return await client.write_registers(register, payload, slave=slave)
                asyncio.run_coroutine_threadsafe(write_registers_wrapper(self._client, int(register), payload, int(slave)), self._asyncLoopThread.loop).result()
#                time.sleep(.03)
        except Exception as ex: # pylint: disable=broad-except
            _log.info('writeWord(%d,%d,%s) failed', slave, register, value)
            _log.exception(ex)
            _log.debug(ex)
            self.disconnectOnError()
            _, _, exc_tb = sys.exc_info()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror((QApplication.translate('Error Message','Modbus Error:') + ' writeWord() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    # translates given int value (given floats are rounded to int) into a 16bit BCD and writes it into one register
    def writeBCD(self, slave:int, register:int, value:float) -> None:
        _log.debug('writeBCD(%d,%d,%s)', slave, register, value)
        if slave == 0:
            return
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if self._asyncLoopThread is not None and self.isConnected():
                assert self._client is not None
                self.connect()
                r = convert_to_bcd(int(round(value)))
                payload: List[int] = self.convert_16bit_uint_to_registers(r)
                asyncio.run_coroutine_threadsafe(self._client.write_registers(int(register),payload,slave=int(slave)), self._asyncLoopThread.loop).result() # type: ignore [reportGeneralTypeIssues, arg-type, unused-ignore] # Argument of type "list[bytes]" cannot be assigned to parameter "values" of type "List[int] | int" in function "write_registers"; in pymodbus 3.7.4 the error is now "List[bytes]"; expected "List[Union[bytes, int]
#                time.sleep(.03)
        except Exception as ex: # pylint: disable=broad-except
            _log.info('writeBCD(%d,%d,%s) failed', slave, register, int(round(value)))
            _log.debug(ex)
            self.disconnectOnError()
            _, _, exc_tb = sys.exc_info()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror((QApplication.translate('Error Message','Modbus Error:') + ' writeWord() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    # function 16 (Write Multiple Holding Registers)
    # value=int or float
    # writes a 32bit integer (2-registers)
    def writeLong(self, slave:int, register:int, value:float) -> None:
        _log.debug('writeLong(%d,%d,%s)', slave, register, value)
        if slave == 0:
            return
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self._asyncLoopThread is not None and self.isConnected():
                assert self._client is not None
                payload:List[int] = self.convert_32bit_int_to_registers(int(round(value)))
                asyncio.run_coroutine_threadsafe(self._client.write_registers(int(register),payload,slave=int(slave)), self._asyncLoopThread.loop).result() # type: ignore [reportGeneralTypeIssues, arg-type, unused-ignore] # Argument of type "list[bytes]" cannot be assigned to parameter "values" of type "List[int] | int" in function "write_registers"; in pymodbus 3.7.4 the error is now "List[bytes]"; expected "List[Union[bytes, int]
#                await asyncio.sleep(.03)
        except Exception as ex: # pylint: disable=broad-except
            _log.info('writeLong(%d,%d,%s) failed', slave, register, int(round(value)))
            _log.debug(ex)
            self.disconnectOnError()
            _, _, exc_tb = sys.exc_info()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror((QApplication.translate('Error Message','Modbus Error:') + ' writeLong() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

#####


    async def read_async(self, slave:int, register:int, count:int, code:int) -> 'Tuple[Optional[ModbusPDU], bool]':
        retry:int = self.readRetries
        error_disconnect:bool = False # set to True if a serious error requiring a disconnect was detected
        res: Optional[ModbusPDU] = None
        assert self._client is not None
        while True:
            try:
                if code==1:
                    res = await self._client.read_coils(address=int(register),count=count,slave=int(slave))
                elif code==2:
                    res = await self._client.read_discrete_inputs(address=int(register),count=count,slave=int(slave))
                elif code==4:
                    res = await self._client.read_input_registers(address=int(register),count=count,slave=int(slave))
                else: # code==3
                    res = await self._client.read_holding_registers(address=int(register),count=count,slave=int(slave))
            except Exception as ex: # pylint: disable=broad-except
                _log.debug(ex)
                res = None
            error, disconnect = self.invalidResult(res, (0 if code in {1, 2} else count)) # don't check for res.registers if function code is 1 or 2
            if error:
                error_disconnect = error_disconnect or disconnect
                if retry > 0:
                    retry = retry - 1
                    _log.debug('retry')
                else:
                    raise Exception(f'read_single_registers_async({slave},{register},{code}) failed')  # pylint: disable=broad-exception-raised
            else:
                break
        return res, error_disconnect

    # returns register data from optimizer cache or from slave
    def read_registers(self, slave:int, register:int, count:int, code:int, force:bool=False) -> Tuple[Optional[List[int]],Optional[List[bool]],bool]:
        res_registers:Optional[List[int]] = None
        res_bits:Optional[List[bool]] = None
        error_disconnect:bool = False
        if count>0:
            if self.optimizer and not force and code not in {1,2}: # MODBUS function 1 and 2 are never optimized
                if code in self.readingsCache and slave in self.readingsCache[code] and \
                        all(r in self.readingsCache[code][slave] for r in range(register,register+count)):
                    # cache hit
                    res_registers = [self.readingsCache[code][slave][r] for r in range(register,register+count)]
                    _log.debug('return cached registers => %.3f', res_registers)
                elif self.fail_on_cache_miss:
                    _log.debug('optimizer cache miss')
                    return None, None, error_disconnect
            try:
                if res_registers is None:
                    #### lock shared resources #####
                    self.COMsemaphore.acquire(1)
                    self.connect()
                    if self._asyncLoopThread is not None and self.isConnected():
                        res_response, res_error_disconnect = asyncio.run_coroutine_threadsafe(self.read_async(slave, register, count, code), self._asyncLoopThread.loop).result()
                        error_disconnect = res_error_disconnect
                        if res_response is not None:
                            if res_response is not None and hasattr(res_response, 'registers'):
                                res_registers = res_response.registers
                            if code in {1, 2} and hasattr(res_response, 'bits'):
                                res_bits = res_response.bits
            finally:
                if self.COMsemaphore.available() < 1:
                    self.COMsemaphore.release(1)
        return res_registers, res_bits, error_disconnect


#####


    # function 3 (Read Multiple Holding Registers) and 4 (Read Input Registers)
    # if force the readings cache is ignored and fresh readings are requested
    def readFloat(self, slave:int, register:int, code:int=3, force:bool=False) -> Optional[float]:
        _log.debug('readFloat(%d,%d,%d,%s)', slave, register, code, force)
        if slave == 0:
            return None
        tx:float = 0.
        if self.aw.seriallogflag:
            tx = time.time()
        error_disconnect:bool = False # set to True if a serious error requiring a disconnect was detected
        res:Optional[float] = None
        try:
            res_registers:Optional[List[int]]
            res_error_disconnect:bool
            res_registers, _, res_error_disconnect = self.read_registers(slave, register, 2, code, force)
            error_disconnect = res_error_disconnect
            if res_registers is not None:
                res = self.convert_float_from_registers(res_registers)
                # we clear the previous error and send a message
                self.clearCommError()
#             await asyncio.sleep(0.020) # we add a small sleep between requests to help out the slow Loring electronic
            return res
        except Exception as ex: # pylint: disable=broad-except
            _log.info('readFloat(%d,%d,%d,%s) failed', slave, register, code, force)
            _log.debug(ex)
            self.disconnectOnError()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Error'))
            if error_disconnect:
                self.commError = self.commError + 1
            return None
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                if self.type < 3: # serial MODBUS
                    ser_str = f'MODBUS readFloat : {self.formatMS(tx,time.time())}ms => {self.comport},{self.baudrate},{self.bytesize},{self.parity},{self.stopbits},{self.timeout} || Slave = {slave} || Register = {register} || Code = {code} || Rx = {res} || retries = {self.readRetries}'
                else: # IP MODBUS
                    ser_str = f'MODBUS readFloat : {self.formatMS(tx,time.time())}ms => {self.host}:{self.port} || Slave = {slave} || Register = {register} || Code = {code} || Rx = {res} || retries = {self.readRetries}'
                self.aw.addserial(ser_str)


    # function 3 (Read Multiple Holding Registers) and 4 (Read Input Registers)
    # if force the readings cache is ignored and fresh readings are requested
    def readBCD(self, slave:int, register:int, code:int=3, force:bool=False) -> Optional[int]:
        _log.debug('readBCD(%d,%d,%d,%s)', slave, register, code, force)
        if slave == 0:
            return None
        tx:float = 0.
        if self.aw.seriallogflag:
            tx = time.time()
        error_disconnect:bool = False # set to True if a serious error requiring a disconnect was detected
        res:Optional[int] = None
        try:
            res_registers:Optional[List[int]]
            res_error_disconnect:bool
            res_registers, _, res_error_disconnect = self.read_registers(slave, register, 2, code, force)
            error_disconnect = res_error_disconnect
            if res_registers is not None:
                res = convert_from_bcd(self.convert_32bit_uint_from_registers(res_registers))
                # we clear the previous error and send a message
                self.clearCommError()
#             await asyncio.sleep(0.020) # we add a small sleep between requests to help out the slow Loring electronic
            return res
        except Exception as ex: # pylint: disable=broad-except
            _log.info('readBCD(%d,%d,%d,%s) failed', slave, register, code, force)
            _log.debug(ex)
            self.disconnectOnError()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Error'))
            if error_disconnect:
                self.commError = self.commError + 1
            return None
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                if self.type < 3: # serial MODBUS
                    ser_str = f'MODBUS readBCD : {self.formatMS(tx,time.time())}ms => {self.comport},{self.baudrate},{self.bytesize},{self.parity},{self.stopbits},{self.timeout} || Slave = {slave} || Register = {register} || Code = {code} || Rx = {res} || retries = {self.readRetries}'
                else: # IP MODBUS
                    ser_str = f'MODBUS readBCD : {self.formatMS(tx,time.time())}ms => {self.host}:{self.port} || Slave = {slave} || Register = {register} || Code = {code} || Rx = {res} || retries = {self.readRetries}'
                self.aw.addserial(ser_str)


    # as readSingleRegister, but does not retry nor raise and error and returns a None instead
    # also does not reserve the port via a semaphore! This has to be done by the caller!
    def peekSingleRegister(self, slave:int, register:int, code:int = 3) -> Optional[int]:
        _log.debug('peekSingleRegister(%d,%d,%d)', slave, register, code)
        if slave == 0:
            return None
        res:Optional[ModbusPDU] = None
        try:
            self.connect()
            if self._asyncLoopThread is not None and self.isConnected():
                assert self._client is not None
                res, _ = asyncio.run_coroutine_threadsafe(self.read_async(int(slave), int(register), 1, code), self._asyncLoopThread.loop).result()
        except Exception as ex: # pylint: disable=broad-except
            _log.info('peekSingleRegister(%d,%d,%d) failed', slave, register, code)
            _log.debug(ex)
        error, _ = self.invalidResult(res,1)
        if res is not None and not error:
            if code in {1, 2}:
                if hasattr(res, 'bits') and len(res.bits)>0 and res.bits[0]:
                    return 1
                return 0
            if hasattr(res, 'registers'):
                r = self.convert_16bit_uint_from_registers(res.registers)
#                _log.debug('  res.registers => %s', res.registers)
                _log.debug('  convert_16bit_uint_from_registers() => %s', r)
                return r
        return None


    # function 1 (Read Coil)
    # function 2 (Read Discrete Input)
    # function 3 (Read Multiple Holding Registers) and
    # function 4 (Read Input Registers)
    # if force the readings cache is ignored and fresh readings are requested
    # if signed is True, the received data is interpreted as signed integer, otherwise as unsigned

    # function 3 (Read Multiple Holding Registers) and 4 (Read Input Registers)
    # if force the readings cache is ignored and fresh readings are requested
    def readSingleRegister(self, slave:int, register:int, code:int = 3, force:bool = False, signed:bool = False) -> Optional[int]:
        _log.debug('readSingleRegister(%d,%d,%d,%s,%s)', slave, register, code, force,signed)
        if slave == 0:
            return None
        tx:float = 0.
        if self.aw.seriallogflag:
            tx = time.time()
        error_disconnect:bool = False # set to True if a serious error requiring a disconnect was detected
        res:Optional[int] = None
        try:
            res_bits:Optional[List[bool]]
            res_registers:Optional[List[int]]
            res_error_disconnect:bool
            res_registers, res_bits, res_error_disconnect = self.read_registers(slave, register, 1, code, force)
            error_disconnect = res_error_disconnect
            if code in {1, 2} and res_bits is not None:
                res = sum(x[1] << x[0] for x in enumerate(res_bits)) if len(res_bits)>0 else 0
                # we clear the previous error and send a message
                self.clearCommError()
#             await asyncio.sleep(0.020) # we add a small sleep between requests to help out the slow Loring electronic
            elif res_registers is not None:
                if signed:
                    res = self.convert_16bit_int_from_registers(res_registers)
                else:
                    res = self.convert_16bit_uint_from_registers(res_registers)
                # we clear the previous error and send a message
                self.clearCommError()
#             await asyncio.sleep(0.020) # we add a small sleep between requests to help out the slow Loring electronic
            return res
        except Exception as ex: # pylint: disable=broad-except
            _log.info('readSingleRegister(%d,%d,%d,%s) failed', slave, register, code, force)
            _log.debug(ex)
            self.disconnectOnError()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Error'))
            if error_disconnect:
                self.commError = self.commError + 1
            return None
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                if self.type < 3: # serial MODBUS
                    ser_str = f'MODBUS readSingleRegister : {self.formatMS(tx,time.time())}ms => {self.comport},{self.baudrate},{self.bytesize},{self.parity},{self.stopbits},{self.timeout} || Slave = {slave} || Register = {register} || Code = {code} || Rx = {res} || retries = {self.readRetries}'
                else: # IP MODBUS
                    ser_str = f'MODBUS readSingleRegister : {self.formatMS(tx,time.time())}ms => {self.host}:{self.port} || Slave = {slave} || Register = {register} || Code = {code} || Rx = {res} || retries = {self.readRetries}'
                self.aw.addserial(ser_str)


    # function 3 (Read Multiple Holding Registers) and 4 (Read Input Registers)
    # if force the readings cache is ignored and fresh readings are requested
    def readInt32(self, slave:int, register:int, code:int = 3,force:bool = False, signed:bool = False) -> Optional[int]:
        _log.debug('readBCD(%d,%d,%d,%s)', slave, register, code, force)
        if slave == 0:
            return None
        tx:float = 0.
        if self.aw.seriallogflag:
            tx = time.time()
        error_disconnect:bool = False # set to True if a serious error requiring a disconnect was detected
        res:Optional[int] = None

        try:
            res_registers:Optional[List[int]]
            res_error_disconnect:bool
            res_registers, _, res_error_disconnect = self.read_registers(slave, register, 2, code, force)
            error_disconnect = res_error_disconnect
            if res_registers is not None:
                if signed:
                    res = self.convert_32bit_int_from_registers(res_registers)
                else:
                    res = self.convert_32bit_uint_from_registers(res_registers)

                # we clear the previous error and send a message
                self.clearCommError()
#             await asyncio.sleep(0.020) # we add a small sleep between requests to help out the slow Loring electronic
            return res
        except Exception as ex: # pylint: disable=broad-except
            _log.info('readInt32(%d,%d,%d,%s) failed', slave, register, code, force)
            _log.debug(ex)
            self.disconnectOnError()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Error'))
            if error_disconnect:
                self.commError = self.commError + 1
            return None
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                if self.type < 3: # serial MODBUS
                    ser_str = f'MODBUS readInt32 : {self.formatMS(tx,time.time())}ms => {self.comport},{self.baudrate},{self.bytesize},{self.parity},{self.stopbits},{self.timeout} || Slave = {slave} || Register = {register} || Code = {code} || Rx = {res} || retries = {self.readRetries}'
                else: # IP MODBUS
                    ser_str = f'MODBUS readInt32 : {self.formatMS(tx,time.time())}ms => {self.host}:{self.port} || Slave = {slave} || Register = {register} || Code = {code} || Rx = {res} || retries = {self.readRetries}'
                self.aw.addserial(ser_str)




    # function 3 (Read Multiple Holding Registers) and
    # function 4 (Read Input Registers)
    # if force the readings cache is ignored and fresh readings are requested
    def readBCDint(self, slave:int, register:int, code:int = 3, force:bool = False) -> Optional[int]:
        _log.debug('readBCD(%d,%d,%d,%s)', slave, register, code, force)
        if slave == 0:
            return None
        tx:float = 0.
        if self.aw.seriallogflag:
            tx = time.time()
        error_disconnect:bool = False # set to True if a serious error requiring a disconnect was detected
        res:Optional[int] = None
        try:
            res_registers:Optional[List[int]]
            res_error_disconnect:bool
            res_registers, _, res_error_disconnect = self.read_registers(slave, register, 1, code, force)
            error_disconnect = res_error_disconnect
            if res_registers is not None:
                res = convert_from_bcd(self.convert_16bit_uint_from_registers(res_registers))
                # we clear the previous error and send a message
                self.clearCommError()
#             await asyncio.sleep(0.020) # we add a small sleep between requests to help out the slow Loring electronic
            return res
        except Exception as ex: # pylint: disable=broad-except
            _log.info('readBCDint(%d,%d,%d,%s) failed', slave, register, code, force)
            _log.debug(ex)
            self.disconnectOnError()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Error'))
            if error_disconnect:
                self.commError = self.commError + 1
            return None
        finally:
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                if self.type < 3: # serial MODBUS
                    ser_str = f'MODBUS readBCDint : {self.formatMS(tx,time.time())}ms => {self.comport},{self.baudrate},{self.bytesize},{self.parity},{self.stopbits},{self.timeout} || Slave = {slave} || Register = {register} || Code = {code} || Rx = {res} || retries = {self.readRetries}'
                else: # IP MODBUS
                    ser_str = f'MODBUS readBCDint : {self.formatMS(tx,time.time())}ms => {self.host}:{self.port} || Slave = {slave} || Register = {register} || Code = {code} || Rx = {res} || retries = {self.readRetries}'
                self.aw.addserial(ser_str)




###


    def setTarget(self, sv:float) -> None:
        _log.debug('setTarget(%s)', sv)
        if self.PID_slave_ID:
            multiplier = 1.
            if self.SVmultiplier == 1:
                multiplier = 10.
            elif self.SVmultiplier == 2:
                multiplier = 100.
            if self.SVwriteFloat:
                self.writeWord(self.PID_slave_ID,self.PID_SV_register,float(sv*multiplier))
            elif self.SVwriteLong:
                self.writeLong(self.PID_slave_ID,self.PID_SV_register,int(round(sv*multiplier)))
            else:
                self.writeSingleRegister(self.PID_slave_ID,self.PID_SV_register,int(round(sv*multiplier)))

    def setPID(self, p:float, i:float, d:float) -> None:
        _log.debug('setPID(%s,%s,%s)', p, i, d)
        if self.PID_slave_ID and not self.PID_p_register == self.PID_i_register == self.PID_d_register == 0:
            multiplier = 1.
            if self.PIDmultiplier == 1:
                multiplier = 10.
            elif self.PIDmultiplier == 2:
                multiplier = 100.
            self.writeSingleRegister(self.PID_slave_ID,self.PID_p_register,p*multiplier)
            self.writeSingleRegister(self.PID_slave_ID,self.PID_i_register,i*multiplier)
            self.writeSingleRegister(self.PID_slave_ID,self.PID_d_register,d*multiplier)
