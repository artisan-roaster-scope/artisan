import time

from PyQt5.QtCore import QSemaphore
from PyQt5.QtWidgets import QApplication

def getBinaryPayloadBuilder(byteorderLittle=True,wordorderLittle=False):
    import pymodbus.version as pymodbus_version
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
    if pymodbus_version.version.major > 1 or (pymodbus_version.version.major == 1 and pymodbus_version.version.minor > 3):
        # pymodbus v1.4 and newer
        return BinaryPayloadBuilder(byteorder=byteorder, wordorder=wordorder)
    else:
        # pymodbus v1.3 and older
        return BinaryPayloadBuilder(endian=byteorder)

def getBinaryPayloadDecoderFromRegisters(registers,byteorderLittle=True,wordorderLittle=False):
    import pymodbus.version as pymodbus_version
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
    if pymodbus_version.version.major > 1 or (pymodbus_version.version.major == 1 and pymodbus_version.version.minor > 3):
        # pymodbus v1.4 and newer
        return BinaryPayloadDecoder.fromRegisters(registers, byteorder=byteorder, wordorder=wordorder) 
    else:
        # pymodbus v1.3 and older
        return BinaryPayloadDecoder.fromRegisters(registers, endian=byteorder)

#import pymodbus.version as pymodbus_version
#from pymodbus.constants import Endian
#from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
#
#if pymodbus_version.version.major > 1 or (pymodbus_version.version.major == 1 and pymodbus_version.version.minor > 3):
#    # pymodbus v1.4 and newer
#    def getBinaryPayloadBuilder(byteorderLittle=True,wordorderLittle=False):
#        if byteorderLittle: 
#            byteorder = Endian.Little
#        else:
#            byteorder = Endian.Big
#        if wordorderLittle:
#            wordorder = Endian.Little
#        else:
#            wordorder = Endian.Big
#        return BinaryPayloadBuilder(byteorder=byteorder, wordorder=wordorder)
#    def getBinaryPayloadDecoderFromRegisters(registers,byteorderLittle=True,wordorderLittle=False):
#        if byteorderLittle:
#            byteorder = Endian.Little
#        else:
#            byteorder = Endian.Big
#        if wordorderLittle:
#            wordorder = Endian.Little
#        else:
#            wordorder = Endian.Big
#        return BinaryPayloadDecoder.fromRegisters(registers, byteorder=byteorder, wordorder=wordorder)
#else:
#    # pymodbus v1.3 and older
#    def getBinaryPayloadBuilder(byteorderLittle=True,_=False):
#        if byteorderLittle:
#            return BinaryPayloadBuilder(endian=Endian.Little)
#        else:
#            return BinaryPayloadBuilder(endian=Endian.Big)
#    def getBinaryPayloadDecoderFromRegisters(registers,byteorderLittle=True,_=False):
#        if byteorderLittle:
#            return BinaryPayloadDecoder.fromRegisters(registers, endian=Endian.Little)
#        else:
#            return BinaryPayloadDecoder.fromRegisters(registers, endian=Endian.Big)


###########################################################################################
##################### MODBUS PORT #########################################################
###########################################################################################


# pymodbus version
class modbusport(object):
    """ this class handles the communications with all the modbus devices"""
    def __init__(self,sendmessage,adderror,addserial):
        self.sendmessage = sendmessage # function to create an Artisan message to the user in the message line
        self.adderror = adderror # signal an error to the user
        self.addserial = addserial # add to serial log
        
        # retries
        self.readRetries = 1
        #default initial settings. They are changed by settingsload() at initiation of program acording to the device chosen
        self.comport = "COM5"      #NOTE: this string should not be translated.
        self.baudrate = 115200
        self.bytesize = 8
        self.parity= 'N'
        self.stopbits = 1
        self.timeout = 1.0
        self.PID_slave_ID = 0
        self.PID_SV_register = 0
        self.PID_p_register = 0
        self.PID_i_register = 0
        self.PID_d_register = 0
        self.PID_ON_action = ""
        self.PID_OFF_action = ""
        self.input1slave = 0
        self.input1register = 0
        self.input1float = False
        self.input1bcd = False
        self.input1code = 3
        self.input1div = 0 # 0: none, 1: 1/10, 2:1/100
        self.input1mode = "C"
        self.input2slave = 0
        self.input2register = 0
        self.input2float = False
        self.input2bcd = False
        self.input2code = 3
        self.input2div = 0
        self.input2mode = "C"
        self.input3slave = 0
        self.input3register = 0
        self.input3float = False
        self.input3bcd = False
        self.input3code = 3
        self.input3div = 0
        self.input3mode = "C"
        self.input4slave = 0
        self.input4register = 0
        self.input4float = False
        self.input4bcd = False
        self.input4code = 3
        self.input4div = 0
        self.input4mode = "C"
        self.input5slave = 0
        self.input5register = 0
        self.input5float = False
        self.input5bcd = False
        self.input5code = 3
        self.input5div = 0
        self.input5mode = "C"
        self.input6slave = 0
        self.input6register = 0
        self.input6float = False
        self.input6bcd = False
        self.input6code = 3
        self.input6div = 0
        self.input6mode = "C"
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
        
    # this garantees a minimum of 30 miliseconds between readings and 80ms between writes (according to the Modbus spec) on serial connections
    # this sleep delays between requests seems to be beneficial on slow RTU serial connections like those of the FZ-94
    def sleepBetween(self,write=False):
        if write:
#            if self.type in [3,4]: # TCP or UDP
#                time.sleep(0.040)
                pass # handled in MODBUS lib
#            else:
                time.sleep(0.035)
        else:
            if self.type in [3,4]: # delay between writes only on serial connections
                pass
            else:
                time.sleep(0.035)

    def address2register(self,addr,code=3):
        if code == 3 or code == 6:
            return addr - 40001
        else:
            return addr - 30001      

    def isConnected(self):
        return not (self.master is None) and self.master.socket
        
    def disconnect(self):
        try:
            self.master.close()
        except Exception:
            pass
        self.master = None

    def connect(self):
#        if self.master and not self.master.socket:
#            self.master = None
        if self.master is None:
            self.commError = False
            try:
                # as in the following the port is None, no port is opened on creation of the (py)serial object
                if self.type == 1: # Serial ASCII
                    from pymodbus.client.sync import ModbusSerialClient
                    self.master = ModbusSerialClient(
                        method='ascii',
                        port=self.comport,
                        baudrate=self.baudrate,
                        bytesize=self.bytesize,
                        parity=self.parity,
                        stopbits=self.stopbits,
                        retry_on_empty=True,
                        timeout=self.timeout)
                elif self.type == 2: # Serial Binary
                    from pymodbus.client.sync import ModbusSerialClient
                    self.master = ModbusSerialClient(
                        method='binary',
                        port=self.comport,
                        baudrate=self.baudrate,
                        bytesize=self.bytesize,
                        parity=self.parity,
                        stopbits=self.stopbits,
                        retry_on_empty=True,
                        timeout=self.timeout)  
                elif self.type == 3: # TCP
                    from pymodbus.client.sync import ModbusTcpClient
                    try:
                        self.master = ModbusTcpClient(
                                host=self.host, 
                                port=self.port,
                                retry_on_empty=True,
                                retries=1,
                                timeout=0.9, #self.timeout
                                )
                        self.readRetries = 0
                    except:
                        self.master = ModbusTcpClient(
                                host=self.host, 
                                port=self.port,
                                )
                elif self.type == 4: # UDP
                    from pymodbus.client.sync import ModbusUdpClient
                    try:
                        self.master = ModbusUdpClient(
                            host=self.host, 
                            port=self.port,
                            retry_on_empty=True,
                            retries=3,
                            timeout=0.7, #self.timeout
                            )
                    except: # older versions of pymodbus don't support the retries, timeout nor the retry_on_empty arguments
                        self.master = ModbusUdpClient(
                            host=self.host, 
                            port=self.port,
                            )
                else: # Serial RTU
                    from pymodbus.client.sync import ModbusSerialClient
                    self.master = ModbusSerialClient(
                        method='rtu',
                        port=self.comport,
                        baudrate=self.baudrate,
                        bytesize=self.bytesize,
                        parity=self.parity,
                        stopbits=self.stopbits,
                        retry_on_empty=False,
                        timeout=self.timeout)   
                    self.readRetries = 1
                self.master.connect()
                self.adderror(QApplication.translate("Error Message","Connected via MODBUS",None))
                time.sleep(.5) # avoid possible hickups on startup
            except Exception as ex:
                _, _, exc_tb = sys.exc_info()
                self.adderror((QApplication.translate("Error Message","Modbus Error:",None) + " connect() {0}").format(str(ex)),exc_tb.tb_lineno)

    # function 15 (Write Multiple Coils)
    def writeCoils(self,slave,register,values):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            self.master.write_coils(int(register),list(values),unit=int(slave))
            time.sleep(.3) # avoid possible hickups on startup
        except Exception as ex:
#            self.disconnect()
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            _, _, exc_tb = sys.exc_info()
            self.adderror((QApplication.translate("Error Message","Modbus Error:",None) + " writeCoils() {0}").format(str(ex)),exc_tb.tb_lineno)
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)    
                
    # function 5 (Write Single Coil)
    def writeCoil(self,slave,register,value):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            self.master.write_coil(int(register),value,unit=int(slave))
            time.sleep(.3) # avoid possible hickups on startup
        except Exception as ex:
#            self.disconnect()
            _, _, exc_tb = sys.exc_info()
            self.adderror((QApplication.translate("Error Message","Modbus Error:",None) + " writeCoil() {0}").format(str(ex)),exc_tb.tb_lineno)
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
        
    # write value to register on slave (function 6 for int or function 16 for float)
    # value can be one of string (containing an int or float), an int or a float
    def writeRegister(self,slave,register,value):
        if stringp(value):
            if "." in value:
                self.writeWord(slave,register,value)
            else:
                self.writeSingleRegister(slave,register,value)
        elif isinstance(value, int):
            self.writeSingleRegister(slave,register,value)
        elif isinstance(value, float):
            self.writeWord(slave,register,value)

    # function 6 (Write Single Holding Register)
    def writeSingleRegister(self,slave,register,value):
#        _logger.debug("writeSingleRegister(%d,%d,%d)" % (slave,register,value))
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            self.master.write_register(int(register),int(value),unit=int(slave))
            time.sleep(.03) # avoid possible hickups on startup
        except Exception as ex:
#            _logger.debug("writeSingleRegister exception: %s" % str(ex))
#            import traceback
#            traceback.print_exc(file=sys.stdout)
#            self.disconnect()
            _, _, exc_tb = sys.exc_info()
            self.adderror((QApplication.translate("Error Message","Modbus Error:",None) + " writeSingleRegister() {0}").format(str(ex)),exc_tb.tb_lineno)
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    # function 22 (Mask Write Register)
    def maskWriteRegister(self,slave,register,and_mask,or_mask):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            self.master.mask_write_register(int(register),int(and_mask),int(or_mask),unit=int(slave))
            time.sleep(.03)
        except Exception as ex:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
#            self.disconnect()
            _, _, exc_tb = sys.exc_info()
            self.adderror((QApplication.translate("Error Message","Modbus Error:",None) + " writeMask() {0}").format(str(ex)),exc_tb.tb_lineno)
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
                
    # function 16 (Write Multiple Holding Registers)
    # values is a list of integers or one integer
    def writeRegisters(self,slave,register,values):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            self.master.write_registers(int(register),values,unit=int(slave))
            time.sleep(.03)
        except Exception as ex:
#            self.disconnect()
            _, _, exc_tb = sys.exc_info()
            self.adderror((QApplication.translate("Error Message","Modbus Error:",None) + " writeRegisters() {0}").format(str(ex)),exc_tb.tb_lineno)
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)


    # function 16 (Write Multiple Holding Registers)
    # value=int or float
    # writes a single precision 32bit float (2-registers)
    def writeWord(self,slave,register,value):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            builder = getBinaryPayloadBuilder(self.byteorderLittle,self.wordorderLittle)
            builder.add_32bit_float(float(value))
            payload = builder.build() # .tolist()
            self.master.write_registers(int(register),payload,unit=int(slave),skip_encode=True)
            time.sleep(.03)
        except Exception as ex:
#            self.disconnect()
            _, _, exc_tb = sys.exc_info()
            self.adderror((QApplication.translate("Error Message","Modbus Error:",None) + " writeWord() {0}").format(str(ex)),exc_tb.tb_lineno)
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)

    # translates given int value int a 16bit BCD and writes it into one register
    def writeBCD(self,slave,register,value):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            builder = getBinaryPayloadBuilder(self.byteorderLittle,self.wordorderLittle)
            r = convert_to_bcd(int(value))
            builder.add_16bit_uint(r)
            payload = builder.build() # .tolist()
            self.master.write_registers(int(register),payload,unit=int(slave),skip_encode=True)
            time.sleep(.03)
        except Exception as ex:
#            self.disconnect()
            _, _, exc_tb = sys.exc_info()
            self.adderror((QApplication.translate("Error Message","Modbus Error:",None) + " writeWord() {0}").format(str(ex)),exc_tb.tb_lineno)
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
                
    # function 3 (Read Multiple Holding Registers) and 4 (Read Input Registers)
    def readFloat(self,slave,register,code=3):
        from pymodbus.pdu import ExceptionResponse
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            retry = self.readRetries                
            while True:
                if code==3:
                    res = self.master.read_holding_registers(int(register),2,unit=int(slave))
                else:
                    res = self.master.read_input_registers(int(register),2,unit=int(slave))
                if res is None or isinstance(res,ExceptionResponse) or isinstance(res,Exception):
                    if retry > 0:
                        retry = retry - 1
                        #time.sleep(0.020)
                    else:
                        raise Exception("Exception response")
                else:
                    break
            decoder = getBinaryPayloadDecoderFromRegisters(res.registers, self.byteorderLittle, self.wordorderLittle)
            r = decoder.decode_32bit_float()
            if self.commError: # we clear the previous error and send a message
                self.commError = False
                self.adderror(QApplication.translate("Error Message","Modbus Communication Resumed",None))
            return r
        except Exception: # as ex:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
#            self.disconnect()
#            _, _, exc_tb = sys.exc_info()
#            self.adderror((QApplication.translate("Error Message","Modbus Error:",None) + " readFloat() {0}").format(str(ex)),exc_tb.tb_lineno)
            self.adderror(QApplication.translate("Error Message","Modbus Communication Error",None))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            #note: logged chars should be unicode not binary
            settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
            self.addserial("MODBUS readFloat :" + settings + " || Slave = " + str(slave) + " || Register = " + str(register) + " || Code = " + str(code) + " || Rx = " + str(r))

    # function 3 (Read Multiple Holding Registers) and 4 (Read Input Registers)
    def readBCD(self,slave,register,code=3):
        from pymodbus.pdu import ExceptionResponse
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            retry = self.readRetries                
            while True:
                if code==3:
                    res = self.master.read_holding_registers(int(register),1,unit=int(slave))
                else:
                    res = self.master.read_input_registers(int(register),1,unit=int(slave))
                if res is None or isinstance(res,ExceptionResponse) or isinstance(res,Exception):
                    if retry > 0:
                        retry = retry - 1
                        #time.sleep(0.020)
                    else:
                        raise Exception("Exception response")
                else:
                    break
            decoder = getBinaryPayloadDecoderFromRegisters(res.registers, self.byteorderLittle, self.wordorderLittle)            
            r = decoder.decode_16bit_uint()
            if self.commError: # we clear the previous error and send a message
                self.commError = False
                self.adderror(QApplication.translate("Error Message","Modbus Communication Resumed",None))
            time.sleep(0.020) # we add a small sleep between requests to help out the slow Loring electronic
            return convert_from_bcd(r)
        except Exception: # as ex:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
#            self.disconnect()
#            _, _, exc_tb = sys.exc_info()
#            self.adderror((QApplication.translate("Error Message","Modbus Error:",None) + " readBCD() {0}").format(str(ex)),exc_tb.tb_lineno)
            self.adderror(QApplication.translate("Error Message","Modbus Communication Error",None))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            #note: logged chars should be unicode not binary
            settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
            self.addserial("MODBUS readBCD :" + settings + " || Slave = " + str(slave) + " || Register = " + str(register) + " || Code = " + str(code) + " || Rx = " + str(r))


    # function 1 (Read Coil)
    # function 2 (Read Discrete Input)
    # function 3 (Read Multiple Holding Registers) and 
    # function 4 (Read Input Registers)
    def readSingleRegister(self,slave,register,code=3):
        from pymodbus.pdu import ExceptionResponse
#        import logging
#        logging.basicConfig()
#        log = logging.getLogger()
#        log.setLevel(logging.DEBUG)
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            retry = self.readRetries
            while True:
                try:
                    if code==1:
                        res = self.master.read_coils(int(register),1,unit=int(slave))
                    elif code==2:
                        res = self.master.read_discrete_inputs(int(register),1,unit=int(slave))                    
                    elif code==4:
                        res = self.master.read_input_registers(int(register),1,unit=int(slave))
                    else: # code==3
                        res = self.master.read_holding_registers(int(register),1,unit=int(slave))
                except Exception:
                    res = None
                if res is None or isinstance(res,ExceptionResponse) or isinstance(res,Exception):
                    if retry > 0:
                        retry = retry - 1
                        time.sleep(0.020)
                    else:
                        raise Exception("Exception response")
                else:
                    break
            if code in [1,2]:
                if res is not None and res.bits[0]:
                    return 1
                else:
                    return 0                
            else:
                decoder = getBinaryPayloadDecoderFromRegisters(res.registers, self.byteorderLittle, self.wordorderLittle)
                r = decoder.decode_16bit_uint()
                if self.commError: # we clear the previous error and send a message
                    self.commError = False
                    self.adderror(QApplication.translate("Error Message","Modbus Communication Resumed",None))
                return r
        except Exception: # as ex:
#            self.disconnect()
#            import traceback
#            traceback.print_exc(file=sys.stdout)
#            _, _, exc_tb = sys.exc_info()
#            self.adderror((QApplication.translate("Error Message","Modbus Error:",None) + " readSingleRegister() {0}").format(str(ex)),exc_tb.tb_lineno)
            self.adderror(QApplication.translate("Error Message","Modbus Communication Error",None))
            self.commError = True
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            #note: logged chars should be unicode not binary
            settings = str(self.comport) + "," + str(self.baudrate) + "," + str(self.bytesize)+ "," + str(self.parity) + "," + str(self.stopbits) + "," + str(self.timeout)
            self.addserial("MODBUS readSingleRegister :" + settings + " || Slave = " + str(slave) + " || Register = " + str(register) + " || Code = " + str(code) + " || Rx = " + str(r))


    def setTarget(self,sv):
        if self.PID_slave_ID:
            multiplier = 1.
            if self.SVmultiplier == 1:
                multiplier = 10.
            elif self.SVmultiplier == 2:
                multiplier = 100.
            self.writeSingleRegister(self.PID_slave_ID,self.PID_SV_register,int(round(sv*multiplier)))
        
    def setPID(self,p,i,d):
        if self.PID_slave_ID and not (self.PID_p_register == self.PID_i_register == self.PID_d_register == 0):
            multiplier = 1.
            if self.PIDmultiplier == 1:
                multiplier = 10.
            elif self.PIDmultiplier == 2:
                multiplier = 100.
            self.writeSingleRegister(self.PID_slave_ID,self.PID_p_register,p*multiplier)
            self.writeSingleRegister(self.PID_slave_ID,self.PID_i_register,i*multiplier)
            self.writeSingleRegister(self.PID_slave_ID,self.PID_d_register,d*multiplier)
        
