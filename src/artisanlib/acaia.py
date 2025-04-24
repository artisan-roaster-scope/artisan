#
# ABOUT
# Acaia scale support for Artisan

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
# Marko Luther, 2024

import asyncio
import logging
from enum import IntEnum, unique
from typing import Optional, Union, List, Tuple, Final, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from bleak.backends.characteristic import BleakGATTCharacteristic  # pylint: disable=unused-import

try:
    from PyQt6.QtCore import QObject # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QObject # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.ble_port import ClientBLE
from artisanlib.async_comm import AsyncIterable, IteratorReader
from artisanlib.scale import Scale


_log: Final[logging.Logger] = logging.getLogger(__name__)


####

@unique
class UNIT(IntEnum):
    KG = 1
    G = 2
    OZ = 5

class FACTOR(IntEnum):
    TEN = 1
    HUNDRED = 2
    THOUSAND = 3
    TENTHOUSAND = 4

class MSG(IntEnum):
    SYSTEM = 0
    TARE = 4
    INFO = 7
    STATUS = 8
    IDENTIFY = 11
    EVENT = 12
    TIMER = 13

class PRS(IntEnum):
    CHECKHEADER1 = 0
    CHECKHEADER2 = 1
    CMDID = 2
    CMDDATA = 3
    CHECKSUM1 = 4
    CHECKSUM2 = 5

class CMD(IntEnum):
    SYSTEM_SA = 0
    INFO_A = 7
    STATUS_A = 8
    EVENT_SA = 12

class EVENT(IntEnum):
    WEIGHT = 5
    BATTERY = 6
    TIMER = 7
    KEY = 8
    ACK = 11

class EVENT_LEN(IntEnum):
    WEIGHT = 6
    BATTERY = 1
    TIMER = 3
    KEY = 1
    ACK = 2

class ACAIA_TIMER(IntEnum):
    TIMER_STATE_STOPPED = 0
    TIMER_STATE_STARTED = 1
    TIMER_STATE_PAUSED = 2

# Acaia legacy service and characteristics UUIDs
ACAIA_LEGACY_SERVICE_UUID:Final[str] = '00001820-0000-1000-8000-00805f9b34fb' # Internet Protocol Support Service # adverstised service UUID
ACAIA_LEGACY_NOTIFY_UUID:Final[str] = '00002a80-0000-1000-8000-00805f9b34fb'
ACAIA_LEGACY_WRITE_UUID:Final[str] = '00002a80-0000-1000-8000-00805f9b34fb' # same as notify!

# Acaia legacy name prefixes
ACAIA_LEGACY_PEARL_NAME:Final[str] = 'PROCHBT' # Acaia Pearl
ACAIA_LEGACY_LUNAR_NAME:Final[str] = 'ACAIA'   # Acaia Lunar Legacy

# Acaia service and characteristics UUIDs
ACAIA_SERVICE_UUID:Final[str] = '49535343-FE7D-4AE5-8FA9-9FAFD205E455'
ACAIA_NOTIFY_UUID:Final[str] = '49535343-1E4D-4BD9-BA61-23C647249616'
ACAIA_WRITE_UUID:Final[str] = '49535343-8841-43F4-A8D4-ECBE34729BB3'

# Acaia name prefixes
ACAIA_PEARL_NAME:Final[str] = 'PEARL-'   # Acaia Pearl (2021)
ACAIA_PEARLS_NAME:Final[str] = 'PEARLS'  # Acaia Pearl S
ACAIA_LUNAR_NAME:Final[str] = 'LUNAR-'   # Acaia Lunar (2021)
ACAIA_CINCO_NAME:Final[str] = 'CINCO'    # Acaia Cinco
ACAIA_PYXIS_NAME:Final[str] = 'PYXIS'    # Acaia Pyxis


# Acaia scale device name prefixes and product names
ACAIA_SCALE_NAMES = [
    (ACAIA_LEGACY_LUNAR_NAME, 'Lunar'), # original Lunar
    (ACAIA_LUNAR_NAME, 'Lunar'), # Lunar 2021 and later
    (ACAIA_LEGACY_PEARL_NAME, 'Pearl'), # original Pearl
    (ACAIA_PEARLS_NAME, 'Pearl S'),
    (ACAIA_PEARL_NAME, 'Pearl'), # Pearl 2021
    (ACAIA_CINCO_NAME, 'Cinco'),
    (ACAIA_PYXIS_NAME, 'Pyxis')]



class AcaiaBLE(QObject, ClientBLE): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class


    # Acaia message constants
    HEADER1:Final[bytes]      = b'\xef'
    HEADER2:Final[bytes]      = b'\xdd'

    HEARTBEAT_FREQUENCY = 3 # every 3 sec send the heartbeat


# NOTE: __slots__ are incompatible with multiple inheritance mixings in subclasses (as done below in class Acaia with QObject)
#    __slots__ = [ '_read_queue', '_input_stream',
#            'id_sent', 'fast_notifications_sent', 'slow_notifications_sent', 'weight', 'battery', 'firmware', 'unit', 'max_weight'
#            '_connected_handler', '_disconnected_handler' ]

    def __init__(self, connected_handler:Optional[Callable[[], None]] = None,
                       disconnected_handler:Optional[Callable[[], None]] = None):
        super().__init__()

        # handlers
        self._connected_handler = connected_handler
        self._disconnected_handler = disconnected_handler

        # Protocol parser variables
        self._read_queue : asyncio.Queue[bytes] = asyncio.Queue(maxsize=200)
        self._input_stream = IteratorReader(AsyncIterable(self._read_queue))

        self.id_sent:bool = False # ID is sent once after first data is received from scale
        self.fast_notifications_sent:bool = False # after connect we switch fast notification on to receive first reading fast
        self.slow_notifications_sent:bool = False # after first reading is received we step down to slow readings again

        # readings
        self.weight:Optional[int] = None
        self.battery:Optional[int] = None
        self.firmware:Optional[Tuple[int,int,int]] = None # on connect this is set to a triple of integers, (major, minor, patch)-version
        self.unit:int = UNIT.G
        self.max_weight:int = 0 # always in g

        ###

        # configure heartbeat
        self.set_heartbeat(self.HEARTBEAT_FREQUENCY) # send keep-alive heartbeat all 3-5sec; seems not to be needed any longer after sending ID on newer firmware versions!?

        # register Acaia Legacy UUIDs
        for legacy_name in (ACAIA_LEGACY_LUNAR_NAME, ACAIA_LEGACY_PEARL_NAME):
            self.add_device_description(ACAIA_LEGACY_SERVICE_UUID, legacy_name)
        self.add_notify(ACAIA_LEGACY_NOTIFY_UUID, self.notify_callback)
        self.add_write(ACAIA_LEGACY_SERVICE_UUID, ACAIA_LEGACY_WRITE_UUID)

        # register Acaia Current UUIDs
        for acaia_name in (ACAIA_PEARL_NAME, ACAIA_PEARLS_NAME, ACAIA_LUNAR_NAME, ACAIA_PYXIS_NAME, ACAIA_CINCO_NAME):
            self.add_device_description(ACAIA_SERVICE_UUID, acaia_name)
        self.add_notify(ACAIA_NOTIFY_UUID, self.notify_callback)
        self.add_write(ACAIA_SERVICE_UUID, ACAIA_WRITE_UUID)

    def set_connected_handler(self, connected_handler:Optional[Callable[[], None]]) -> None:
        self._connected_handler = connected_handler

    def set_disconnected_handler(self, disconnected_handler:Optional[Callable[[], None]]) -> None:
        self._disconnected_handler = disconnected_handler


    # protocol parser


    def reset_readings(self) -> None:
        self.weight = None
        self.battery = None
        self.firmware = None
        self.unit = UNIT.G
        self.max_weight = 0


    def on_connect(self) -> None:
        self.reset_readings()
        self.id_sent = False
        self.fast_notifications_sent = False
        self.slow_notifications_sent = False
        connected_service_UUID = self.connected()
        if connected_service_UUID == ACAIA_LEGACY_SERVICE_UUID:
            _log.debug('connected to Acaia Legacy Scale')
        elif connected_service_UUID == ACAIA_SERVICE_UUID:
            _log.debug('connected to Acaia Scale')
        if self._connected_handler is not None:
            self._connected_handler()

    def on_disconnect(self) -> None:
        _log.debug('disconnected')
        if self._disconnected_handler is not None:
            self._disconnected_handler()


    ##


    def parse_info(self, data:bytes) -> None:
        _log.debug('INFO MSG')
#        if len(data)>1:
#            print(data[1])
        if len(data)>4:
            self.firmware = (data[2],data[3],data[4])
            _log.debug('%s.%s.%s', self.firmware[1], self.firmware[2], self.firmware[0])
        # passwd_set
#        if len(data)>5:
#            print(data[5])
#        if len(data)>6:
#            print(data[6])

    # returns length of consumed data or -1 on error
    def parse_weight_event(self, payload:bytes) -> int:
        if len(payload) < EVENT_LEN.WEIGHT:
            return -1
        # first 4 bytes encode the weight as unsigned long
        value:float = ((payload[3] & 0xff) << 24) + \
            ((payload[2] & 0xff) << 16) + ((payload[1] & 0xff) << 8) + (payload[0] & 0xff)

        factor = payload[4]

        if factor == FACTOR.TEN:
            value /= 10
        elif factor == FACTOR.HUNDRED:
            value /= 100
        elif factor == FACTOR.THOUSAND:
            value /= 1000
        elif factor == FACTOR.TENTHOUSAND:
            value /= 10000

        # convert received weight data to g
        if self.unit == UNIT.KG:
            value = value * 1000
        elif self.unit == UNIT.OZ:
            value = value * 28.3495

        #stable = (payload[5] & 0x01) != 0x01

        # if 2nd bit of payload[5] is set, the reading is negative
        if (payload[5] & 0x02) == 0x02:
            value *= -1

        # convert the weight in g delivered with two decimals to an int
        value_int = int(round(value))
        # if value is fresh and reading is stable
        if value_int != self.weight: # and stable:
            self.weight = value_int
            self.weight_changed(self.weight)
            _log.debug('new weight: %s', self.weight)

        return EVENT_LEN.WEIGHT

    def parse_battery_event(self, payload:bytes) -> int:
        if len(payload) < EVENT_LEN.BATTERY:
            return -1
        b = payload[0]
        if 0 <= b <= 100:
            self.battery = int(payload[0])
            self.battery_changed(self.battery)
            _log.debug('battery: %s', self.battery)
        return EVENT_LEN.BATTERY

    @staticmethod
    def parse_timer_event(payload:bytes) -> int:
        if len(payload) < EVENT_LEN.TIMER:
            return -1
        value = ((payload[0] & 0xff) * 60) + payload[1] + payload[2] / 10.
        _log.debug('time: %sm%s%sms, %s',payload[0],payload[1],payload[2], value)
        return EVENT_LEN.TIMER

    @staticmethod
    def parse_ack_event(payload:bytes) -> int:
        if len(payload) < EVENT_LEN.ACK:
            return -1
        _log.debug('ACK EVENT')
        return EVENT_LEN.ACK

    @staticmethod
    def parse_key_event(payload:bytes) -> int:
        if len(payload) < EVENT_LEN.KEY:
            return -1
        _log.debug('KEY EVENT')
        return EVENT_LEN.KEY

    def parse_scale_event(self, payload:bytes) -> int:
        if payload and len(payload) > 0:
            event = payload[1]
            payload = payload[2:]
            val = -1
            if event == EVENT.WEIGHT:
                val = self.parse_weight_event(payload)
                if self.fast_notifications_sent and not self.slow_notifications_sent:
                    # after receiving the first weight quick,
                    # we slow down the weight notificatinos
                    self.slow_notifications()
            elif event == EVENT.BATTERY:
                val = self.parse_battery_event(payload)
            elif event == EVENT.TIMER:
                val = self.parse_timer_event(payload)
            elif event == EVENT.ACK:
                val = self.parse_ack_event(payload)
            elif event == EVENT.KEY:
                val = self.parse_key_event(payload)
            else:
                return -1
            if val < 0:
                return -1
            return val + 1
        return -1

    def parse_scale_events(self, payload:bytes) -> None:
        if payload and len(payload) > 0:
            pos = self.parse_scale_event(payload)
            if pos > -1:
                self.parse_scale_events(payload[pos+1:])

    ##

    def parse_status(self, payload:bytes) -> None:
        _log.debug('STATUS')

        # battery level (7 bits of first byte) + TIMER_START (1bit)
        if payload and len(payload) > 0:
            self.battery = int(payload[1] & ~(1 << 7))
            self.battery_changed(self.battery)
            _log.debug('battery: %s%%', self.battery)
        # unit (7 bits of second byte) + CD_START (1bit)
        if payload and len(payload) > 1:
            self.unit = int(payload[2] & 0x7F)
            _log.debug('unit: %s', self.unit)

        # mode (7 bits of third byte) + tare (1bit)
        # sleep (4th byte), 0:off, 1:5sec, 2:10sec, 3:20sec, 4:30sec, 5:60sec
        # key disabled (5th byte), touch key setting 0: off , 1:On
        # sound (6th byte), beep setting 0 : off 1: on
        # resolution (7th byte), 0 : default, 1 : high
        # max weight (8th byte)
        if payload and len(payload) > 7:
            self.max_weight = (payload[7] + 1) * 1000
            _log.debug('max_weight: %s', self.max_weight)



    def parse_data(self, msg_type:int, data:bytes) -> None:
        if msg_type == MSG.INFO:
            self.parse_info(data)
        elif msg_type == MSG.STATUS:
            self.parse_status(data)
        elif msg_type == MSG.EVENT:
            self.parse_scale_events(data)
        #
        if self.id_sent and not self.fast_notifications_sent:
            # we configure the scale to receive the initial
            # weight notification as fast as possible
            self.fast_notifications()
        if not self.id_sent:
            # send ID only once per connect
            self.send_ID()

    ##


    # return a bytearray of len 2 containing the even and odd CRCs over the given payload
    @staticmethod
    def crc(payload:Union[bytes,List[int]]) -> bytes:
        cksum1 = 0
        cksum2 = 0
        for i, _ in enumerate(payload):
            if (i % 2) == 0:
                cksum1 = (cksum1 + payload[i]) & 0xFF
            else:
                cksum2 = (cksum2 + payload[i]) & 0xFF
        return bytes([cksum1,cksum2])

    # constructs message bytearray of the given type (int) and payload (bytearray) by adding headers and CRCs
    def message(self, tp:int, payload:bytes) -> bytes:
        return self.HEADER1 + self.HEADER2 + tp.to_bytes(1, 'big') + payload + self.crc(payload)

    def send_message(self, tp:int, payload:bytes) -> None:
        self.send(self.message(tp, payload))
        if self._logging:
            _log.info('send: %s',payload)

    def send_event(self, payload:bytes) -> None:
        self.send_message(MSG.EVENT, bytes([len(payload)+1]) + payload)

    def send_timer_command(self, cmd:bytes) -> None:
        self.send_message(MSG.TIMER, b'\x00' + cmd)


    ###

    # keep alive should be send every 3-5sec
    def heartbeat(self) -> None:
        _log.debug('send heartbeat')
        self.send_message(MSG.SYSTEM, b'\x02\x00')

    def send_stop(self) -> None:
        _log.debug('send stop')
        self.send_message(MSG.SYSTEM,b'\x00\x00')

    def send_tare(self) -> None:
        _log.debug('send tare')
        self.send_message(MSG.TARE,b'\x00')

    ###

    def send_ID(self) -> None:
        _log.debug('send ID')
        self.send_message(MSG.IDENTIFY,b'\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d')
        # non-legacy id message
        # self.send_message(MSG.IDENTIFY,b'\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x31\x32\x33\x34')
        self.id_sent = True

    # configure notifications

    def slow_notifications(self) -> None:
        _log.debug('slow notifications')
        self.send_event(
            bytes([ # pairs of key/setting
                    0,  # weight id
                    7,  # 0, 1, 3, 5, 7, 15, 31, 63, 127  # weight argument (speed of notifications in 1/10 sec)
                        # 5 or 7 seems to be good values for this app in Artisan
#                    1,   # battery id
#                    255, #2,  # battery argument (if 0 : fast, 1 : slow)
#                    2,  # timer id
#                    255, #5,  # timer argument
#                    3,  # key id (not used)
#                    255, #4   # setting (not used)
                ])
                )
        self.slow_notifications_sent = True

    def fast_notifications(self) -> None:
        _log.debug('fast notifications')
        self.send_event(
            bytes([ # pairs of key/setting
                    0,  # weight id
                    1,  # 0, 1, 3, 5, 7, 15, 31, 63, 127  # weight argument (speed of notifications in 1/10 sec)
                        # 5 or 7 seems to be good values for this app in Artisan
#                    1,   # battery id
#                    255, #2,  # battery argument (if 0 : fast, 1 : slow)
#                    2,  # timer id
#                    255, #5,  # timer argument
#                    3,  # key id (not used)
#                    255, #4   # setting (not used)
                ])
                )
        self.fast_notifications_sent = True


    ###


    def notify_callback(self, _sender:'BleakGATTCharacteristic', data:bytearray) -> None:
        if hasattr(self, '_async_loop_thread') and self._async_loop_thread is not None:
            asyncio.run_coroutine_threadsafe(
                    self._read_queue.put(bytes(data)),
                    self._async_loop_thread.loop)
            if self._logging:
                _log.info('received: %s',data)


    # EX: d = b'\xef\xdd\x07\x07\x02\x14\x02<\x14\x00W\x18\xef\xdd\x07' (len: 12)
    # 2 header:     d[0:2]   = b'\xef\xdd'
    # 1 cmd:        d[2]     = b'\x07'  => INFO
    # 1 data_len:   d[3]     = b'\x07'
    # 6 data:       d[4:10]  = b'\x02\x14\x02<\x14\x00'
    # 2 crc:        d[10:12] = b'\x00W\x18'  # calculated over "data_len+data"

    async def reader(self, stream:IteratorReader) -> None:
        while True:
            await stream.readuntil(self.HEADER1)
            if await stream.readexactly(1) == self.HEADER2:
                cmd = int.from_bytes(await stream.readexactly(1), 'big')
                if cmd in {CMD.SYSTEM_SA, CMD.INFO_A, CMD.STATUS_A, CMD.EVENT_SA}:
                    dl = await stream.readexactly(1)
                    data_len:int = min(20, int.from_bytes(dl, 'big'))
                    data = await stream.readexactly(data_len - 1)
                    crc = await stream.readexactly(2)
                    data = dl+data
                    if crc == self.crc(data):
                        self.parse_data(cmd, data)
                    else:
                        _log.debug('CRC error')


    def on_start(self) -> None:
        if hasattr(self, '_async_loop_thread') and self._async_loop_thread is not None:
            # start the reader
            asyncio.run_coroutine_threadsafe(
                    self.reader(self._input_stream),
                    self._async_loop_thread.loop)


    def weight_changed(self, new_value:int) -> None:  # pylint: disable=no-self-use
        del new_value


    def battery_changed(self, new_value:int) -> None: # pylint: disable=no-self-use
        del new_value



# AcaiaBLE and its super class are not allowed to hold __slots__
class Acaia(AcaiaBLE, Scale): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class

    def __init__(self, model:int, ident:Optional[str], name:Optional[str], connected_handler:Optional[Callable[[], None]] = None,
                       disconnected_handler:Optional[Callable[[], None]] = None):
        Scale.__init__(self, model, ident, name)
        AcaiaBLE.__init__(self, connected_handler = connected_handler, disconnected_handler=disconnected_handler)

    def connect_scale(self) -> None:
        self.start(address=self.ident)

    def disconnect_scale(self) -> None:
        self.stop()

    def weight_changed(self, new_value:int) -> None:
        self.weight_changed_signal.emit(new_value)

    def battery_changed(self, new_value:int) -> None:
        self.battery_changed_signal.emit(new_value)

    def on_disconnect(self) -> None:
        self.disconnected_signal.emit()
        AcaiaBLE.on_disconnect(self)

    def tare_scale(self) -> None:
        self.send_tare()
