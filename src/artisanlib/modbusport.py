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
# Marko Luther, 2019

import sys
import time
import logging
try:
    from typing import Final
except ImportError:
    # for Python 3.7:
    from typing_extensions import Final

try:
    #ylint: disable = E, W, R, C
    from PyQt6.QtCore import QSemaphore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #ylint: disable = E, W, R, C
    from PyQt5.QtCore import QSemaphore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.util import stringp, debugLogLevelActive


_log: Final = logging.getLogger(__name__)


def convert_to_bcd(decimal):
    ''' Converts a decimal value to a bcd value

    :param value: The decimal value to to pack into bcd
    :returns: The number in bcd form
    '''
    place, bcd = 0, 0
    while decimal > 0:
        nibble = decimal % 10
        bcd += nibble << place
        decimal = decimal // 10
        place += 4
    return bcd


def convert_from_bcd(bcd):
    ''' Converts a bcd value to a decimal value

    :param value: The value to unpack from bcd
    :returns: The number in decimal form
    '''
    place, decimal = 1, 0
    while bcd > 0:
        nibble = bcd & 0xf
        decimal += nibble * place
        bcd >>= 4
        place *= 10
    return decimal

def getBinaryPayloadBuilder(byteorderLittle=True,wordorderLittle=False):
    from pymodbus.constants import Endian
    from pymodbus.payload import BinaryPayloadBuilder
    if byteorderLittle:
        byteorder = Endian.Little
    else:
        byteorder = Endian.Big
    if wordorderLittle:
        wordorder = Endian.Little
    else:
        wordorder = Endian.Big
    return BinaryPayloadBuilder(byteorder=byteorder, wordorder=wordorder)

def getBinaryPayloadDecoderFromRegisters(registers,byteorderLittle=True,wordorderLittle=False):
    from pymodbus.constants import Endian
    from pymodbus.payload import BinaryPayloadDecoder
    if byteorderLittle:
        byteorder = Endian.Little
    else:
        byteorder = Endian.Big
    if wordorderLittle:
        wordorder = Endian.Little
    else:
        wordorder = Endian.Big
    return BinaryPayloadDecoder.fromRegisters(registers, byteorder=byteorder, wordorder=wordorder)


###########################################################################################
##################### MODBUS PORT #########################################################
###########################################################################################


# pymodbus version
class modbusport():
    """ this class handles the communications with all the modbus devices"""

    __slots__ = [ 'aw', 'modbus_serial_read_delay', 'modbus_serial_extra_read_delay', 'modbus_serial_write_delay', 'maxCount', 'readRetries', 'comport', 'baudrate', 'bytesize', 'parity', 'stopbits',
        'timeout', 'IP_timeout', 'IP_retries', 'serial_readRetries', 'PID_slave_ID', 'PID_SV_register', 'PID_p_register', 'PID_i_register', 'PID_d_register', 'PID_ON_action', 'PID_OFF_action',
        'channels', 'inputSlaves', 'inputRegisters', 'inputFloats', 'inputBCDs', 'inputFloatsAsInt', 'inputBCDsAsInt', 'inputSigned', 'inputCodes', 'inputDivs',
        'inputModes', 'optimizer', 'fetch_max_blocks', 'fail_on_cache_miss', 'disconnect_on_error', 'reset_socket', 'activeRegisters', 'readingsCache', 'SVmultiplier', 'PIDmultiplier',
        'byteorderLittle', 'wordorderLittle', 'master', 'COMsemaphore', 'host', 'port', 'type', 'lastReadResult', 'commError' ]

    def __init__(self,aw):
        self.aw = aw

        self.modbus_serial_read_delay = 0.035 # in seconds
        self.modbus_serial_extra_read_delay = 0.0 # in seconds (user configurable)
        self.modbus_serial_write_delay = 0.080 # in seconds

        self.maxCount = 125 # the maximum number of registers that can be fetched in one request according to the MODBUS spec
        self.readRetries = 0  # retries
        #default initial settings. They are changed by settingsload() at initiation of program according to the device chosen
        self.comport = 'COM5'      #NOTE: this string should not be translated.
        self.baudrate = 115200
        self.bytesize = 8
        self.parity= 'N'
        self.stopbits = 1
        self.timeout = 0.3 # serial MODBUS timeout
        self.serial_readRetries = 0 # user configurable, defaults to 0
        self.IP_timeout = 0.2 # UDP/TCP MODBUS timeout in seconds
        self.IP_retries = 1 # UDP/TCP MODBUS retries (max 2)
        self.PID_slave_ID = 0
        self.PID_SV_register = 0
        self.PID_p_register = 0
        self.PID_i_register = 0
        self.PID_d_register = 0
        self.PID_ON_action = ''
        self.PID_OFF_action = ''

        self.channels = 8
        self.inputSlaves = [0]*self.channels
        self.inputRegisters = [0]*self.channels
        # decoding (default: 16bit uInt)
        self.inputFloats = [False]*self.channels       # 32bit Floats
        self.inputBCDs = [False]*self.channels         # 32bit uInt BCD decoded
        self.inputFloatsAsInt = [False]*self.channels  # 32bit uInt/sInt
        self.inputBCDsAsInt = [False]*self.channels    # 16bit uInt/sInt
        self.inputSigned = [False]*self.channels       # if True, decode Integers as signed otherwise as unsigned
        #
        self.inputCodes = [3]*self.channels
        self.inputDivs = [0]*self.channels # 0: none, 1: 1/10, 2:1/100
        self.inputModes = ['C']*self.channels

        self.optimizer = True # if set, values of consecutive register addresses are requested in single requests
        # MODBUS functions associated to dicts associating MODBUS slave ids to registers in use
        # for optimized read of full register segments with single requests
        # this dict is re-computed on each connect() by a call to updateActiveRegisters()
        # NOTE: for registers of type float and BCD (32bit = 2x16bit) also the succeeding registers are registered
        self.fetch_max_blocks = False # if set, the optimizer fetches only one sequence per area from the minimum to the maximum register ignoring gaps
        self.fail_on_cache_miss = True # if False and request cannot be resolved from optimizer cache while optimizer is active,
            # send individual reading request; if set to True, never send individual data requests while optimizer is on
            # NOTE: if TRUE read requests with force=False (default) will fail
        self.disconnect_on_error = True # if True we explicitly disconnect the MODBUS connection on errors and restart it on next request

        self.reset_socket = False # reset socket connection on error (True by default in pymodbus>v2.5.2, False by default in pymodbus v2.3)

        self.activeRegisters = {}
        # the readings cache that is filled by requesting sequences of values in blocks
        self.readingsCache = {}

        self.SVmultiplier = 0
        self.PIDmultiplier = 0
        self.byteorderLittle = False
        self.wordorderLittle = True
        self.master = None
        self.COMsemaphore = QSemaphore(1)
        self.host = '127.0.0.1' # the TCP/UDP host
        self.port = 502 # the TCP/UDP port
        self.type = 0
        # type =
        #    0: Serial RTU
        #    1: Serial ASCII
        #    2: Serial Binary
        #    3: TCP
        #    4: UDP
        self.lastReadResult = 0 # this is set by eventaction following some custom button/slider Modbus actions with "read" command

        self.commError = False # True after a communication error was detected and not yet cleared by receiving proper data

    # this guarantees a minimum of 30 milliseconds between readings and 80ms between writes (according to the Modbus spec) on serial connections
    # this sleep delays between requests seems to be beneficial on slow RTU serial connections like those of the FZ-94
    def sleepBetween(self,write=False):
        if write:
            pass # handled in MODBUS lib
#            if self.type in [3,4]: # TCP or UDP
#                pass
#            else:
#                time.sleep(self.modbus_serial_write_delay)
        else:
            if self.type in [3,4]: # delay between writes only on serial connections
                pass
            else:
                time.sleep(self.modbus_serial_read_delay + self.modbus_serial_extra_read_delay)

    @staticmethod
    def address2register(addr, code=3):
        if code in [3, 6]:
            return addr - 40001
        return addr - 30001

    def isConnected(self):
        return not (self.master is None) and self.master.socket

    def disconnect(self):
        _log.debug('disconnect()')
        try:
            if self.master is not None:
                self.master.close()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        self.master = None
        self.clearReadingsCache()

    def disconnectOnError(self):
        if self.disconnect_on_error and (self.commError or not self.isConnected()):
            self.disconnect()

    # t a duration between start and end time in seconds to be formatted in a string as ms
    @staticmethod
    def formatMS(start, end):
        return f'{(end-start)*1000:.1f}'

    def connect(self):
#        if self.master and not self.master.socket:
#            self.master = None
        if self.master is None or not self.master.socket:
            self.commError = False
            try:
                # as in the following the port is None, no port is opened on creation of the (py)serial object
                if self.type == 1: # Serial ASCII
                    from pymodbus.client import ModbusSerialClient
                    self.master = ModbusSerialClient(
                        method='ascii',
                        port=self.comport,
                        baudrate=self.baudrate,
                        bytesize=self.bytesize,
                        parity=self.parity,
                        stopbits=self.stopbits,
                        retry_on_empty=False,
                        retry_on_invalid=False,
                        reset_socket=self.reset_socket,
                        # timeout is in seconds and defaults to 3
                        timeout=min((self.aw.qmc.delay/2000), self.timeout)) # the timeout should not be larger than half of the sampling interval
                    self.readRetries = self.serial_readRetries
                elif self.type == 2: # Serial Binary
                    from pymodbus.client import ModbusSerialClient # @Reimport
                    self.master = ModbusSerialClient(
                        method='binary',
                        port=self.comport,
                        baudrate=self.baudrate,
                        bytesize=self.bytesize,
                        parity=self.parity,
                        stopbits=self.stopbits,
                        retry_on_empty=False,
                        retry_on_invalid=False,
                        reset_socket=self.reset_socket,
                        # timeout is in seconds and defaults to 3
                        timeout=min((self.aw.qmc.delay/2000), self.timeout)) # the timeout should not be larger than half of the sampling interval
                    self.readRetries = self.serial_readRetries
                elif self.type == 3: # TCP
                    from pymodbus.client import ModbusTcpClient
                    try:
                        self.master = ModbusTcpClient(
                                host=self.host,
                                port=self.port,
                                retry_on_empty=False,   # only supported for serial clients in v2.5.2
                                retry_on_invalid=False, # only supported for serial clients in v2.5.2
                                reset_socket=self.reset_socket,
                                retries=self.IP_retries,
                                # timeout is in seconds (int) and defaults to 3
                                timeout=min((self.aw.qmc.delay/2000), self.IP_timeout) # the timeout should not be larger than half of the sampling interval
                                )
                        self.readRetries = 1
                    except Exception: # pylint: disable=broad-except
                        self.master = ModbusTcpClient(
                                host=self.host,
                                port=self.port,
                                )
                elif self.type == 4: # UDP
                    from pymodbus.client import ModbusUdpClient
                    try:
                        self.master = ModbusUdpClient(
                            host=self.host,
                            port=self.port,
                            retry_on_empty=False,   # only supported for serial clients in v2.5.2
                            retry_on_invalid=False, # only supported for serial clients in v2.5.2
                            reset_socket=self.reset_socket,
                            retries=self.IP_retries,
                            # timeout is in seconds (int) and defaults to 3
                            timeout=min((self.aw.qmc.delay/2000), self.IP_timeout) # the timeout should not be larger than half of the sampling interval
                            )
                        self.readRetries = 1
                    except Exception: # pylint: disable=broad-except # older versions of pymodbus don't support the retries, timeout nor the retry_on_empty arguments
                        self.master = ModbusUdpClient(
                            host=self.host,
                            port=self.port,
                            )
                else: # Serial RTU
                    from pymodbus.client import ModbusSerialClient # @Reimport
                    self.master = ModbusSerialClient(
                        method='rtu',
                        port=self.comport,
                        baudrate=self.baudrate,
                        bytesize=self.bytesize,
                        parity=self.parity,
                        stopbits=self.stopbits,
                        retry_on_empty=False,  # by default False for faster speed
                        retry_on_invalid=False, # by default False
                        reset_socket=self.reset_socket,
                        strict=False, # settings this to False disables the inter char timeout restriction
                        timeout=min((self.aw.qmc.delay/2000), self.timeout)) # the timeout should not be larger than half of the sampling interval
#                    self.master.inter_char_timeout = 0.05
                    self.readRetries = self.serial_readRetries
                _log.debug('connect(): connecting')
                self.master.connect()
                if self.isConnected():
                    self.updateActiveRegisters()
                    self.clearReadingsCache()
                    time.sleep(.5) # avoid possible hickups on startup
                    self.aw.sendmessage(QApplication.translate('Message', 'Connected via MODBUS'))
                else:
                    self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Error: failed to connect'))
            except Exception as ex: # pylint: disable=broad-except
                _log.exception(ex)
                _, _, exc_tb = sys.exc_info()
                self.aw.qmc.adderror((QApplication.translate('Error Message','Modbus Error:') + ' connect() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

########## MODBUS optimizer for fetching register data in batches

    # MODBUS code => slave => [registers]
    def updateActiveRegisters(self):
        _log.debug('updateActiveRegisters()')
        self.activeRegisters = {}
        for c in range(self.channels):
            slave = self.inputSlaves[c]
            if slave != 0:
                register = self.inputRegisters[c]
                code = self.inputCodes[c]
                registers = [register]
                if self.inputFloats[c] or self.inputBCDs[c] or self.inputFloatsAsInt[c]:
                    registers.append(register+1)
                if not (code in self.activeRegisters):
                    self.activeRegisters[code] = {}
                if slave in self.activeRegisters[code]:
                    self.activeRegisters[code][slave].extend(registers)
                else:
                    self.activeRegisters[code][slave] = registers
        _log.debug('active registers: %s',self.activeRegisters)

    def clearReadingsCache(self):
        _log.debug('clearReadingsCache()')
        self.readingsCache = {}

    def cacheReadings(self,code,slave,register,results):
        if not (code in self.readingsCache):
            self.readingsCache[code] = {}
        if not slave in self.readingsCache[code]:
            self.readingsCache[code][slave] = {}
        for i,v in enumerate(results):
            self.readingsCache[code][slave][register+i] = v
            if self.aw.seriallogflag:
                ser_str = 'cache reading : Slave = {} || Register = {} || Rx = {}'.format(
                    slave,
                    register+i,
                    v)
                self.aw.addserial(ser_str)

    @staticmethod
    def invalidResult(res,count):
        from pymodbus.pdu import ExceptionResponse
        if res is None:
            _log.info('invalidResult(%d) => None', count)
            return True
        elif isinstance(res, ExceptionResponse):
            _log.info('invalidResult(%d) => received exception from device', count)
            return True
        elif res.isError():
            _log.info('invalidResult(%d) => pymodbus error: %s', count, res)
            return True
        elif res.registers is None:
            _log.info('invalidResult(%d) => res.registers is None', count)
            return True
        elif len(res.registers) != count:
            _log.info('invalidResult(%d) => len(res.registers)=%d', count, len(res.registers))
            return True
        return False

    def readActiveRegisters(self):
        if not self.optimizer:
            return
        try:
            _log.debug('readActiveRegisters()')
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                self.clearReadingsCache()
                for code in self.activeRegisters:
                    for slave in self.activeRegisters[code]:
                        registers = sorted(self.activeRegisters[code][slave])
                        if self.fetch_max_blocks:
                            sequences = [[registers[0],registers[-1]]]
                        else:
                            # split in successive sequences
                            gaps = [[s, er] for s, er in zip(registers, registers[1:]) if s+1 < er]
                            edges = iter(registers[:1] + sum(gaps, []) + registers[-1:])
                            sequences = list(zip(edges, edges)) # list of pairs of the form (start-register,end-register)
                        just_send = False
                        for seq in sequences:
                            retry = self.readRetries
                            register = seq[0]
                            count = seq[1]-seq[0] + 1
                            if 0 < count <= self.maxCount:
                                res = None
                                if just_send:
                                    self.sleepBetween() # we start with a sleep, as it could be that just a send command happened before the semaphore was caught
                                just_send = True
                                tx = time.time()
                                while True:
                                    _log.debug('readActive(%d,%d,%d,%d)', slave, code, register, count)
                                    try:
                                        # we cache only MODBUS function 3 and 4 (not 1 and 2!)
                                        if code == 3:
                                            res = self.master.read_holding_registers(register,count,slave=slave)
                                        elif code == 4:
                                            res = self.master.read_input_registers(register,count,slave=slave)
                                    except Exception as e: # pylint: disable=broad-except
                                        _log.info('readActive(%d,%d,%d,%d)', slave, code, register, count)
                                        _log.debug(e)
                                        res = None
                                    if self.invalidResult(res,count):
                                        if retry > 0:
                                            retry = retry - 1
                                            time.sleep(0.020)
                                            _log.debug('retry')
                                        else:
                                            res = None
                                            raise Exception('Exception response')
                                    else:
                                        break

                                #note: logged chars should be unicode not binary
                                if self.aw.seriallogflag:
                                    if self.type < 3: # serial MODBUS
                                        ser_str = 'MODBUS readActiveRegisters : {}ms => {},{},{},{},{},{} || Slave = {} || Register = {} || Code = {} || Rx# = {}'.format(
                                            self.formatMS(tx,time.time()),
                                            self.comport,
                                            self.baudrate,
                                            self.bytesize,
                                            self.parity,
                                            self.stopbits,
                                            self.timeout,
                                            slave,
                                            register,
                                            code,
                                            len(res.registers))
                                    else: # IP MODBUS
                                        ser_str = 'MODBUS readActiveRegisters : {}ms => {}:{} || Slave = {} || Register = {} || Code = {} || Rx# = {}'.format(
                                            self.formatMS(tx,time.time()),
                                            self.host,
                                            self.port,
                                            slave,
                                            register,
                                            code,
                                            len(res.registers))
                                    _log.debug(ser_str)
                                    self.aw.addserial(ser_str)

                                if res is not None:
                                    if self.commError: # we clear the previous error and send a message
                                        self.commError = False
                                        self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Resumed'))
                                    self.cacheReadings(code,slave,register,res.registers)

        except Exception as ex: # pylint: disable=broad-except
            _log.debug(ex)
            self.disconnectOnError()
#            import traceback
#            traceback.print_exc(file=sys.stdout)
#            _, _, exc_tb = sys.exc_info()
#            self.aw.qmc.adderror((QApplication.translate("Error Message","Modbus Error:") + " readSingleRegister() {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
            self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Error'))
            self.commError = True
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

##########

    # function 15 (Write Multiple Coils)
    def writeCoils(self,slave,register,values):
        _log.debug('writeCoils(%d,%d,%s)', slave, register, values)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            self.master.write_coils(int(register),list(values),slave=int(slave))
            time.sleep(.3) # avoid possible hickups on startup
        except Exception as ex: # pylint: disable=broad-except
            _log.info('writeCoils(%d,%d,%s)', slave, register, values)
            _log.debug(ex)
            self.disconnectOnError()
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            _, _, exc_tb = sys.exc_info()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror((QApplication.translate('Error Message','Modbus Error:') + ' writeCoils() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    # function 5 (Write Single Coil)
    def writeCoil(self,slave,register,value):
        _log.debug('writeCoil(%d,%d,%s)', slave, register, value)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            self.master.write_coil(int(register),value,slave=int(slave))
            time.sleep(.3) # avoid possible hickups on startup
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

    # write value to register on slave (function 6 for int or function 16 for float)
    # value can be one of string (containing an int or float), an int or a float
    def writeRegister(self,slave,register,value):
        _log.debug('writeRegister(%d,%d,%s)', slave, register, value)
        if stringp(value):
            if '.' in value:
                self.writeWord(slave,register,value)
            else:
                self.writeSingleRegister(slave,register,value)
        elif isinstance(value, int):
            self.writeSingleRegister(slave,register,value)
        elif isinstance(value, float):
            self.writeWord(slave,register,value)

    # function 6 (Write Single Holding Register)
    def writeSingleRegister(self,slave,register,value):
        _log.debug('writeSingleRegister(%d,%d,%s)', slave, register, value)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            self.master.write_register(int(register),int(round(value)),slave=int(slave))
            time.sleep(.03) # avoid possible hickups on startup
        except Exception as ex: # pylint: disable=broad-except
            _log.info('writeSingleRegister(%d,%d,%s) failed', slave, register, value)
            _log.debug(ex)
#            _logger.debug("writeSingleRegister exception: %s" % str(ex))
#            import traceback
#            traceback.print_exc(file=sys.stdout)
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
    def maskWriteRegister(self,slave,register,and_mask,or_mask):
        _log.debug('maskWriteRegister(%d,%d,%s,%s)', slave, register, and_mask, or_mask)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            self.master.mask_write_register(int(register),int(and_mask),int(or_mask),slave=int(slave))
            time.sleep(.03)
        except Exception as ex: # pylint: disable=broad-except
            _log.info('maskWriteRegister(%d,%d,%s,%s) failed', slave, register, and_mask, or_mask)
            if debugLogLevelActive():
                _log.debug(ex)
#            import traceback
#            traceback.print_exc(file=sys.stdout)
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
    def localMaskWriteRegister(self,slave,register,and_mask,or_mask,value):
        new_val = (int(round(value)) & and_mask) | (or_mask & (and_mask ^ 0xFFFF))
        self.writeSingleRegister(slave,register,int(new_val))

    # function 16 (Write Multiple Holding Registers)
    # values is a list of integers or one integer
    def writeRegisters(self,slave,register,values):
        _log.debug('writeRegisters(%d,%d,%s)', slave, register, values)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            self.master.write_registers(int(register),values,slave=int(slave))
            time.sleep(.03)
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
    def writeWord(self,slave,register,value):
        _log.debug('writeWord(%d,%d,%s)', slave, register, value)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            builder = getBinaryPayloadBuilder(self.byteorderLittle,self.wordorderLittle)
            builder.add_32bit_float(float(value))
            payload = builder.build()
            self.master.write_registers(int(register),payload,slave=int(slave),skip_encode=True)
            time.sleep(.03)
        except Exception as ex: # pylint: disable=broad-except
            _log.info('writeWord(%d,%d,%s) failed', slave, register, value)
            _log.debug(ex)
            self.disconnectOnError()
            _, _, exc_tb = sys.exc_info()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror((QApplication.translate('Error Message','Modbus Error:') + ' writeWord() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    # translates given int value int a 16bit BCD and writes it into one register
    def writeBCD(self,slave,register,value):
        _log.debug('writeBCD(%d,%d,%s)', slave, register, value)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            builder = getBinaryPayloadBuilder(self.byteorderLittle,self.wordorderLittle)
            r = convert_to_bcd(int(value))
            builder.add_16bit_uint(r)
            payload = builder.build() # .tolist()
            self.master.write_registers(int(register),payload,slave=int(slave),skip_encode=True)
            time.sleep(.03)
        except Exception as ex: # pylint: disable=broad-except
            _log.info('writeBCD(%d,%d,%s) failed', slave, register, value)
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
    def writeLong(self,slave,register,value):
        _log.debug('writeLong(%d,%d,%s)', slave, register, value)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            builder = getBinaryPayloadBuilder(self.byteorderLittle,self.wordorderLittle)
            builder.add_32bit_int(int(value))
            payload = builder.build()
            self.master.write_registers(int(register),payload,slave=int(slave),skip_encode=True)
            time.sleep(.03)
        except Exception as ex: # pylint: disable=broad-except
            _log.info('writeLong(%d,%d,%s) failed', slave, register, value)
            _log.debug(ex)
            self.disconnectOnError()
            _, _, exc_tb = sys.exc_info()
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror((QApplication.translate('Error Message','Modbus Error:') + ' writeLong() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    # function 3 (Read Multiple Holding Registers) and 4 (Read Input Registers)
    # if force the readings cache is ignored and fresh readings are requested
    def readFloat(self,slave,register,code=3,force=False):
        _log.debug('readFloat(%d,%d,%d,%s)', slave, register, code, force)
        if slave == 0:
            return None
        r = None
        retry = self.readRetries
        if self.aw.seriallogflag:
            tx = time.time()
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if self.optimizer and not force:
                if code in self.readingsCache and slave in self.readingsCache[code] and register in self.readingsCache[code][slave] \
                    and register+1 in self.readingsCache[code][slave]:
                    # cache hit
                    res = [self.readingsCache[code][slave][register],self.readingsCache[code][slave][register+1]]
                    decoder = getBinaryPayloadDecoderFromRegisters(res, self.byteorderLittle, self.wordorderLittle)
                    r = decoder.decode_32bit_float()
                    _log.debug('return cached value => %.3f', r)
                    return r
                if self.fail_on_cache_miss:
                    _log.debug('optimizer cache miss')
                    return None
            self.connect()
            if self.isConnected():
                while True:
                    if code==3:
                        res = self.master.read_holding_registers(int(register),2,slave=int(slave))
                    else:
                        res = self.master.read_input_registers(int(register),2,slave=int(slave))
                    if self.invalidResult(res,2):
                        if retry > 0:
                            retry = retry - 1
                            #time.sleep(0.020)  # no retry delay as timeout time should already be large enough
                            _log.debug('retry')
                        else:
                            raise Exception('Exception response')
                    else:
                        break
                decoder = getBinaryPayloadDecoderFromRegisters(res.registers, self.byteorderLittle, self.wordorderLittle)
                r = decoder.decode_32bit_float()
                if self.commError: # we clear the previous error and send a message
                    self.commError = False
                    self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Resumed'))
                return r
            else:
                return None
        except Exception as ex: # pylint: disable=broad-except
            _log.info('readFloat(%d,%d,%d,%s) failed', slave, register, code, force)
            _log.debug(ex)
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            self.disconnectOnError()
#            _, _, exc_tb = sys.exc_info()
#            self.aw.qmc.adderror((QApplication.translate("Error Message","Modbus Error:") + " readFloat() {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Error'))
            self.commError = True
            return None
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                if self.type < 3: # serial MODBUS
                    ser_str = 'MODBUS readFloat : {}ms => {},{},{},{},{},{} || Slave = {} || Register = {} || Code = {} || Rx = {} || retries = {}'.format(
                        self.formatMS(tx,time.time()),
                        self.comport,
                        self.baudrate,
                        self.bytesize,
                        self.parity,
                        self.stopbits,
                        self.timeout,
                        slave,
                        register,
                        code,
                        r,
                        self.readRetries-retry)
                else: # IP MODBUS
                    ser_str = 'MODBUS readFloat : {}ms => {}:{} || Slave = {} || Register = {} || Code = {} || Rx = {} || retries = {}'.format(
                        self.formatMS(tx,time.time()),
                        self.host,
                        self.port,
                        slave,
                        register,
                        code,
                        r,
                        self.readRetries-retry)
                self.aw.addserial(ser_str)


    # function 3 (Read Multiple Holding Registers) and 4 (Read Input Registers)
    # if force the readings cache is ignored and fresh readings are requested
    def readBCD(self,slave,register,code=3,force=False):
        _log.debug('readBCD(%d,%d,%d,%s)', slave, register, code, force)
        if slave == 0:
            return None
        r = None
        retry = self.readRetries
        if self.aw.seriallogflag:
            tx = time.time()
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if self.optimizer and not force:
                if code in self.readingsCache and slave in self.readingsCache[code] and register in self.readingsCache[code][slave] \
                    and register+1 in self.readingsCache[code][slave]:
                    # cache hit
                    res = [self.readingsCache[code][slave][register],self.readingsCache[code][slave][register+1]]
                    decoder = getBinaryPayloadDecoderFromRegisters(res, self.byteorderLittle, self.wordorderLittle)
                    r = convert_from_bcd(decoder.decode_32bit_uint())
                    _log.debug('return cached value => %.3f', r)
                    return r
                if self.fail_on_cache_miss:
                    _log.debug('optimizer cache miss')
                    return None
            self.connect()
            if self.isConnected():
                while True:
                    if code==3:
                        res = self.master.read_holding_registers(int(register),2,slave=int(slave))
                    else:
                        res = self.master.read_input_registers(int(register),2,slave=int(slave))
                    if self.invalidResult(res,2):
                        if retry > 0:
                            retry = retry - 1
                            #time.sleep(0.020)  # no retry delay as timeout time should already be larger enough
                            _log.debug('retry')
                        else:
                            raise Exception('Exception response')
                    else:
                        break
                decoder = getBinaryPayloadDecoderFromRegisters(res.registers, self.byteorderLittle, self.wordorderLittle)
                r = decoder.decode_32bit_uint()
                if self.commError: # we clear the previous error and send a message
                    self.commError = False
                    self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Resumed'))
                time.sleep(0.020) # we add a small sleep between requests to help out the slow Loring electronic
                return convert_from_bcd(r)
            else:
                return None
        except Exception as ex: # pylint: disable=broad-except
            _log.info('readBCD(%d,%d,%d,%s) failed', slave, register, code, force)
            _log.debug(ex)
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            self.disconnectOnError()
#            _, _, exc_tb = sys.exc_info()
#            self.aw.qmc.adderror((QApplication.translate("Error Message","Modbus Error:") + " readBCD() {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Error'))
            self.commError = True
            return None
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                if self.type < 3: # serial MODBUS
                    ser_str = 'MODBUS readBCD : {}ms => {},{},{},{},{},{} || Slave = {} || Register = {} || Code = {} || Rx = {} || retries = {}'.format(
                        self.formatMS(tx,time.time()),
                        self.comport,
                        self.baudrate,
                        self.bytesize,
                        self.parity,
                        self.stopbits,
                        self.timeout,
                        slave,
                        register,
                        code,
                        r,
                        self.readRetries-retry)
                else: # IP MODBUS
                    ser_str = 'MODBUS readBCD : {}ms => {}:{} || Slave = {} || Register = {} || Code = {} || Rx = {} || retries = {}'.format(
                        self.formatMS(tx,time.time()),
                        self.host,
                        self.port,
                        slave,
                        register,
                        code,
                        r,
                        self.readRetries-retry)
                self.aw.addserial(ser_str)

    # as readSingleRegister, but does not retry nor raise and error and returns a None instead
    # also does not reserve the port via a semaphore!
    def peekSingleRegister(self,slave,register,code=3):
        _log.debug('peekSingleRegister(%d,%d,%d)', slave, register, code)
        if slave == 0:
            return None
        try:
            if code==1:
                res = self.master.read_coils(int(register),1,slave=int(slave))
            elif code==2:
                res = self.master.read_discrete_inputs(int(register),1,slave=int(slave))
            elif code==4:
                res = self.master.read_input_registers(int(register),1,slave=int(slave))
            else: # code==3
                res = self.master.read_holding_registers(int(register),1,slave=int(slave))
        except Exception as ex: # pylint: disable=broad-except
            _log.info('peekSingleRegister(%d,%d,%d) failed', slave, register, code)
            _log.debug(ex)
            res = None
        if not self.invalidResult(res,1):
            if code in [1,2]:
                if res is not None and res.bits[0]:
                    return 1
                return 0
            _log.info('RES %s',res)
            decoder = getBinaryPayloadDecoderFromRegisters(res.registers, self.byteorderLittle, self.wordorderLittle)
            r = decoder.decode_16bit_uint()
            _log.debug('  res.registers => %s', res.registers)
            _log.debug('  decoder.decode_16bit_uint() => %s', r)
            return r
        return None

    # function 1 (Read Coil)
    # function 2 (Read Discrete Input)
    # function 3 (Read Multiple Holding Registers) and
    # function 4 (Read Input Registers)
    # if force the readings cache is ignored and fresh readings are requested
    # if signed is True, the received data is interpreted as signed integer, otherwise as unsigned
    def readSingleRegister(self,slave,register,code=3,force=False,signed=False):
        _log.debug('readSingleRegister(%d,%d,%d,%s)', slave, register, code, force)
        if slave == 0:
            return None
        r = None
        retry = self.readRetries
        if self.aw.seriallogflag:
            tx = time.time()
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if self.optimizer and not force:
                if code in self.readingsCache and slave in self.readingsCache[code] and register in self.readingsCache[code][slave]:
                    # cache hit
                    res = self.readingsCache[code][slave][register]
                    decoder = getBinaryPayloadDecoderFromRegisters([res], self.byteorderLittle, self.wordorderLittle)
                    if signed:
                        r = decoder.decode_16bit_int()
                    else:
                        r = decoder.decode_16bit_uint()
                    _log.debug('return cached value => %d', r)
                    return r
                if self.fail_on_cache_miss:
                    _log.debug('optimizer cache miss')
                    return None
            self.connect()
            if self.isConnected():
                while True:
                    try:
                        if code==1:
                            res = self.master.read_coils(int(register),1,slave=int(slave))
                        elif code==2:
                            res = self.master.read_discrete_inputs(int(register),1,slave=int(slave))
                        elif code==4:
                            res = self.master.read_input_registers(int(register),1,slave=int(slave))
                        else: # code==3
                            res = self.master.read_holding_registers(int(register),1,slave=int(slave))
                    except Exception as ex: # pylint: disable=broad-except
                        _log.debug(ex)
                        res = None
                    if self.invalidResult(res,1):
                        if retry > 0:
                            retry = retry - 1
                            #time.sleep(0.020)  # no retry delay as timeout time should already be larger enough
                            _log.debug('retry')
                        else:
                            raise Exception(f'readSingleRegister({slave},{register},{code},{force},{signed}) failed')
                    else:
                        break
                if code in [1,2]:
                    if res is not None and res.bits[0]:
                        r = 1
                    else:
                        r = 0
                    if self.commError: # we clear the previous error and send a message
                        self.commError = False
                        self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Resumed'))
                    return r
                decoder = getBinaryPayloadDecoderFromRegisters(res.registers, self.byteorderLittle, self.wordorderLittle)
                if signed:
                    r = decoder.decode_16bit_int()
                else:
                    r = decoder.decode_16bit_uint()
                if self.commError: # we clear the previous error and send a message
                    self.commError = False
                    self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Resumed'))
                return r
            else:
                return None
        except Exception as ex: # pylint: disable=broad-except
            _log.info('readSingleRegister(%d,%d,%d,%s) failed', slave, register, code, force)
            _log.debug(ex)
            self.disconnectOnError()
#            import traceback
#            traceback.print_exc(file=sys.stdout)
#            _, _, exc_tb = sys.exc_info()
#            self.aw.qmc.adderror((QApplication.translate("Error Message","Modbus Error:") + " readSingleRegister() {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Error'))
            self.commError = True
            return None
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                if self.type < 3: # serial MODBUS
                    ser_str = 'MODBUS readSingleRegister : {}ms => {},{},{},{},{},{} || Slave = {} || Register = {} || Code = {} || Rx = {} || retries = {}'.format(
                        self.formatMS(tx,time.time()),
                        self.comport,
                        self.baudrate,
                        self.bytesize,
                        self.parity,
                        self.stopbits,
                        self.timeout,
                        slave,
                        register,
                        code,
                        r,
                        self.readRetries-retry)
                else: # IP MODBUS
                    ser_str = 'MODBUS readSingleRegister : {}ms => {}:{} || Slave = {} || Register = {} || Code = {} || Rx = {} || retries = {}'.format(
                        self.formatMS(tx,time.time()),
                        self.host,
                        self.port,
                        slave,
                        register,
                        code,
                        r,
                        self.readRetries-retry)
                self.aw.addserial(ser_str)

    # function 3 (Read Multiple Holding Registers) and 4 (Read Input Registers)
    # if force the readings cache is ignored and fresh readings are requested
    def readInt32(self,slave,register,code=3,force=False,signed=False):
        _log.debug('readInt32(%d,%d,%d,%s)', slave, register, code, force)
        if slave == 0:
            return None
        r = None
        retry = self.readRetries
        if self.aw.seriallogflag:
            tx = time.time()
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if self.optimizer and not force:
                if code in self.readingsCache and slave in self.readingsCache[code] and register in self.readingsCache[code][slave] \
                    and register+1 in self.readingsCache[code][slave]:
                    # cache hit
                    res = [self.readingsCache[code][slave][register],self.readingsCache[code][slave][register+1]]
                    decoder = getBinaryPayloadDecoderFromRegisters(res, self.byteorderLittle, self.wordorderLittle)
                    if signed:
                        r = decoder.decode_32bit_int()
                    else:
                        r = decoder.decode_32bit_uint()
                    _log.debug('return cached value => %d', r)
                    return r
                if self.fail_on_cache_miss:
                    _log.debug('optimizer cache miss')
                    return None
            self.connect()
            if self.isConnected():
                while True:
                    if code==3:
                        res = self.master.read_holding_registers(int(register),2,slave=int(slave))
                    else:
                        res = self.master.read_input_registers(int(register),2,slave=int(slave))
                    if self.invalidResult(res,2):
                        if retry > 0:
                            retry = retry - 1
                            #time.sleep(0.020)  # no retry delay as timeout time should already be larger enough
                            _log.debug('retry')
                        else:
                            raise Exception('Exception response')
                    else:
                        break
                decoder = getBinaryPayloadDecoderFromRegisters(res.registers, self.byteorderLittle, self.wordorderLittle)
                if signed:
                    r = decoder.decode_32bit_int()
                else:
                    r = decoder.decode_32bit_uint()
                if self.commError: # we clear the previous error and send a message
                    self.commError = False
                    self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Resumed'))
                return r
            else:
                return None
        except Exception as ex: # pylint: disable=broad-except
            _log.info('readInt32(%d,%d,%d,%s) failed', slave, register, code, force)
            _log.debug(ex)
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            self.disconnectOnError()
#            _, _, exc_tb = sys.exc_info()
#            self.aw.qmc.adderror((QApplication.translate("Error Message","Modbus Error:") + " readFloat() {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Error'))
            self.commError = True
            return None
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                if self.type < 3: # serial MODBUS
                    ser_str = 'MODBUS readInt32 : {}ms => {},{},{},{},{},{} || Slave = {} || Register = {} || Code = {} || Rx = {} || retries = {}'.format(
                        self.formatMS(tx,time.time()),
                        self.comport,
                        self.baudrate,
                        self.bytesize,
                        self.parity,
                        self.stopbits,
                        self.timeout,
                        slave,
                        register,
                        code,
                        r,
                        self.readRetries-retry)
                else: # IP MODBUS
                    ser_str = 'MODBUS readInt32 : {}ms => {}:{} || Slave = {} || Register = {} || Code = {} || Rx = {} || retries = {}'.format(
                        self.formatMS(tx,time.time()),
                        self.host,
                        self.port,
                        slave,
                        register,
                        code,
                        r,
                        self.readRetries-retry)
                self.aw.addserial(ser_str)


    # function 3 (Read Multiple Holding Registers) and
    # function 4 (Read Input Registers)
    # if force the readings cache is ignored and fresh readings are requested
    def readBCDint(self,slave,register,code=3,force=False):
        _log.debug('readBCDint(%d,%d,%d,%s)', slave, register, code, force)
#        import logging
#        logging.basicConfig()
#        log = logging.getLogger()
#        log.setLevel(logging.DEBUG)
        if slave == 0:
            return None
        r = None
        retry = self.readRetries
        if self.aw.seriallogflag:
            tx = time.time()
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            if self.optimizer and not force:
                if code in self.readingsCache and slave in self.readingsCache[code] and register in self.readingsCache[code][slave]:
                    # cache hit
                    res = self.readingsCache[code][slave][register]
                    decoder = getBinaryPayloadDecoderFromRegisters([res], self.byteorderLittle, self.wordorderLittle)
                    r = convert_from_bcd(decoder.decode_16bit_uint())
                    _log.debug('return cached value => %d', r)
                    return r
                if self.fail_on_cache_miss:
                    _log.debug('optimizer cache miss')
                    return None
            self.connect()
            if self.isConnected():
                while True:
                    try:
                        if code==3:
                            res = self.master.read_holding_registers(int(register),1,slave=int(slave))
                        else:
                            res = self.master.read_input_registers(int(register),1,slave=int(slave))
                    except Exception: # pylint: disable=broad-except
                        res = None
                    if self.invalidResult(res,1):
                        if retry > 0:
                            retry = retry - 1
                            # time.sleep(0.020)  # no retry delay as timeout time should already be larger enough
                            _log.debug('retry')
                        else:
                            raise Exception('Exception response')
                    else:
                        break
                decoder = getBinaryPayloadDecoderFromRegisters(res.registers, self.byteorderLittle, self.wordorderLittle)
                r = decoder.decode_16bit_uint()
                if self.commError: # we clear the previous error and send a message
                    self.commError = False
                    self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Resumed'))
                time.sleep(0.020) # we add a small sleep between requests to help out the slow Loring electronic
                return convert_from_bcd(r)
            else:
                return None
        except Exception as ex: # pylint: disable=broad-except
            _log.info('readBCDint(%d,%d,%d,%s) failed', slave, register, code, force)
            _log.debug(ex)
            self.disconnectOnError()
#            import traceback
#            traceback.print_exc(file=sys.stdout)
#            _, _, exc_tb = sys.exc_info()
#            self.aw.qmc.adderror((QApplication.translate("Error Message","Modbus Error:") + " readBCDint() {0}").format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
            if self.aw.qmc.flagon:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Modbus Communication Error'))
            self.commError = True
            return None
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            #note: logged chars should be unicode not binary
            if self.aw.seriallogflag:
                if self.type < 3: # serial MODBUS
                    ser_str = 'MODBUS readBCDint : {}ms => {},{},{},{},{},{} || Slave = {} || Register = {} || Code = {} || Rx = {} || retries = {}'.format(
                        self.formatMS(tx,time.time()),
                        self.comport,
                        self.baudrate,
                        self.bytesize,
                        self.parity,
                        self.stopbits,
                        self.timeout,
                        slave,
                        register,
                        code,
                        r,
                        self.readRetries-retry)
                else: # IP MODBUS
                    ser_str = 'MODBUS readBCDint : {}ms => {}:{} || Slave = {} || Register = {} || Code = {} || Rx = {} || retries = {}'.format(
                        self.formatMS(tx,time.time()),
                        self.host,
                        self.port,
                        slave,
                        register,
                        code,
                        r,
                        self.readRetries-retry)
                self.aw.addserial(ser_str)

    def setTarget(self,sv):
        _log.debug('setTarget(%s)', sv)
        if self.PID_slave_ID:
            multiplier = 1.
            if self.SVmultiplier == 1:
                multiplier = 10.
            elif self.SVmultiplier == 2:
                multiplier = 100.
            self.writeSingleRegister(self.PID_slave_ID,self.PID_SV_register,int(round(sv*multiplier)))

    def setPID(self,p,i,d):
        _log.debug('setPID(%s,%s,%s)', p, i, d)
        if self.PID_slave_ID and not (self.PID_p_register == self.PID_i_register == self.PID_d_register == 0):
            multiplier = 1.
            if self.PIDmultiplier == 1:
                multiplier = 10.
            elif self.PIDmultiplier == 2:
                multiplier = 100.
            self.writeSingleRegister(self.PID_slave_ID,self.PID_p_register,p*multiplier)
            self.writeSingleRegister(self.PID_slave_ID,self.PID_i_register,i*multiplier)
            self.writeSingleRegister(self.PID_slave_ID,self.PID_d_register,d*multiplier)
