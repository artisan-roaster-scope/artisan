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
#import time as libtime
from enum import IntEnum, unique
from typing import Optional, Union, List, Tuple, Final, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from bleak.backends.characteristic import BleakGATTCharacteristic  # pylint: disable=unused-import

try:
    from PyQt6.QtCore import pyqtSignal, pyqtSlot # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import pyqtSignal, pyqtSlot # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.ble_port import ClientBLE
from artisanlib.async_comm import AsyncIterable, IteratorReader
from artisanlib.scale import Scale, ScaleSpecs, STATE_ACTION
from artisanlib.util import float2float


_log: Final[logging.Logger] = logging.getLogger(__name__)


####

Color = Tuple[int, int, int] # RGB color with valid values from 0-255

@unique
class SCALE_CLASS(IntEnum):
    LEGACY = 1 # eg. Pearl Legacy, Lunar Legacy
        # split messages between several (mostly 2) payloads
    MODERN = 2 # eg. Lunar 2021, Pearl, Pearl 2021, Pearl S, Cinco, Pyxis
        # report weight in unit indicated by byte 2 of STATUS_A message
    RELAY = 3  # relaying scales without display eg. Umbra, ..

@unique
class UNIT(IntEnum):
    KG = 1
    G = 2
    OZ = 5

@unique
class AUTO_OFF_TIMER(IntEnum):
    AUTO_SLEEP_OFF = 1
    AUTO_SLEEP_1MIN = 2
    AUTO_SLEEP_5MIN = 3
    AUTO_SLEEP_15MIN = 4
    AUTO_SLEEP_30MIN = 5
    AUTO_OFF_5MIN = 6
    AUTO_OFF_10MIN = 7
    AUTO_OFF_30MIN = 8

@unique
class KEY_INFO(IntEnum):
    TARE = 0
    START = 8
    RESET = 9
    STOP = 10
    DOUBLE = 15

@unique
class KEY_ADDITIONAL_INFO(IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    WEIGHT = 5
    SIX = 6
    WEIGHT_TIME = 7
    BATTERY = 8
    NINE = 9
    TEN = 10
    ELEVEN = 11
    TWELVE = 12
    THIRTEEN = 13

@unique
class FACTOR(IntEnum):
    TEN = 1
    HUNDRED = 2
    THOUSAND = 3
    TENTHOUSAND = 4

# Data to Scale
@unique
class MSG(IntEnum):
    SYSTEM = 0
    TARE = 4
    SETTINGS = 6
    INFO = 7
    STATUS = 8
    IDENTIFY = 11
    EVENT = 12
    TIMER = 13
    LED = 53

# Command IDs
@unique
class CMD(IntEnum):
    SYSTEM_SA = 0
    INFO_A = 7
    STATUS_A = 8
    EVENT_SA = 12

@unique
class LED_CMD(IntEnum):
    OFF = 0
    EFFECT = 1
    ON = 2
    TOGGLE_DEFAULT_EFFECT = 3 # turn on/off default stable weight effect

@unique
class LED_EFFECT(IntEnum):
    HALO = 1
    WIPE_OFF = 2
    BREATHE = 3

# Event types
@unique
class EVENT(IntEnum):
    SYSTEM = 0
    WEIGHT = 5
    BATTERY = 6
    TIMER = 7
    KEY = 8
    SETTING = 9
    ACK = 11

class EVENT_LEN(IntEnum):
    WEIGHT = 6
    BATTERY = 1
    TIMER = 3
    KEY = 1
    ACK = 2 # specifies minimum len (ACK payloads have len 2 or 9)

@unique
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


# Acaia Relay service and characteristics UUIDs
ACAIA_RELAY_SERVICE_UUID:Final[str] = '0000fe40-cc7a-482a-984a-7f2ed5b3e58f'
ACAIA_RELAY_NOTIFY_UUID:Final[str] = '0000fe42-8e22-4541-9d4c-21edae82ed19'
ACAIA_RELAY_WRITE_UUID:Final[str] = '0000fe41-8e22-4541-9d4c-21edae82ed19' # write without response

# Acaia Relay name prefixes
ACAIA_UMBRA_NAME:Final[str] = 'UMBRA'    # Acaia Umbra
ACAIA_COSMO_NAME:Final[str] = 'COSMO'    # Acaia Cosmo


# Acaia scale device name prefixes and product names
ACAIA_SCALE_NAMES = [
    (ACAIA_LEGACY_LUNAR_NAME, 'Lunar'), # original Lunar
    (ACAIA_LUNAR_NAME, 'Lunar'), # Lunar 2021 and later
    (ACAIA_LEGACY_PEARL_NAME, 'Pearl'), # original Pearl
    (ACAIA_PEARLS_NAME, 'Pearl S'),
    (ACAIA_PEARL_NAME, 'Pearl'), # Pearl 2021
    (ACAIA_CINCO_NAME, 'Cinco'),
    (ACAIA_PYXIS_NAME, 'Pyxis'),
    (ACAIA_UMBRA_NAME, 'Umbra'),
    (ACAIA_COSMO_NAME, 'Cosmo')]



class AcaiaBLE(ClientBLE): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class

    weight_changed_signal = pyqtSignal(float, bool) # delivers new weight in g with decimals for accurate conversion, and flag indicaating stable readings
    battery_changed_signal = pyqtSignal(int)  # delivers new batter level in %
    connected_signal = pyqtSignal()     # issued on connect
    disconnected_signal = pyqtSignal()  # issued on disconnect

    # Acaia message constants
    HEADER1:Final[bytes]      = b'\xef'
    HEADER2:Final[bytes]      = b'\xdd'

    # Colors
    BLACK:Final[Color] = (0,0,0)
    WHITE:Final[Color] = (255,255,255)
    RED:Final[Color] = (255,0,0)
    GREEN:Final[Color] = (0,255,0)
    BLUE:Final[Color] = (0,0,255)
    LIGHT_BLUE:Final[Color] = (0,128,255)
    MAGENTA:Final[Color] = (255,0,255)
    CYAN:Final[Color] = (0,255,255) # not used
    ORANGE:Final[Color] = (255,128,0) # not used
    BROWN:Final[Color] = (255,60,0)


    HEARTBEAT_FREQUENCY = 5 # send the heartbeat every 5 sec


# NOTE: __slots__ are incompatible with multiple inheritance mixings in subclasses (as done below in class Acaia with QObject)
#    __slots__ = [ '_read_queue', '_input_stream',
#            'id_sent', 'fast_notifications_sent', 'slow_notifications_sent', 'weight', 'battery', 'firmware', 'unit', 'max_weight'
#            '_connected_handler', '_disconnected_handler' ]

    def __init__(self, connected_handler:Optional[Callable[[], None]] = None,
                       disconnected_handler:Optional[Callable[[], None]] = None,
                       stable_only:bool=True, # if True only stable weight readings are reported by weight_changed_signal
                       decimals:int=1): # number of significant decimals (0, 1, ..) of the weight signal
        super().__init__()

        # handlers
        self._connected_handler = connected_handler
        self._disconnected_handler = disconnected_handler

        # configuration
        self.stable_only:bool = stable_only
        self.decimals:int = decimals

        # scale class
        self.scale_class:SCALE_CLASS = SCALE_CLASS.MODERN

        # Protocol parser variables
        self._read_queue : Optional[asyncio.Queue[bytes]] = None

        self.id_sent:bool = False # ID is sent once after first data is received from scale
        self.fast_notifications_sent:bool = False # after connect we switch fast notification on to receive first reading fast
        self.slow_notifications_sent:bool = False # after first reading is received we step down to slow readings again

        # readings
        self.weight:Optional[float] = None
        self.stable_weight:Optional[float] = None
        self.battery:Optional[int] = None
        self.firmware:Optional[Tuple[int,int,int]] = None # on connect this is set to a triple of integers, (major, minor, patch)-version
        self.unit:int = UNIT.G
        self.max_weight:int = 0 # always in g
        self.readability:float = 0 # scale accuracy; minimal weight steps
        self.auto_off_timer:AUTO_OFF_TIMER = AUTO_OFF_TIMER.AUTO_SLEEP_OFF
        self.has_leds:bool = False # scale supports LED commands

        ###

        # configure heartbeat
        self.set_heartbeat(self.HEARTBEAT_FREQUENCY) # send keep-alive heartbeat all 5sec; only for LEGACY scales

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

        # register Acaia Relay UUIDs
        for acaia_name in (ACAIA_UMBRA_NAME, ACAIA_COSMO_NAME):
            self.add_device_description(ACAIA_RELAY_SERVICE_UUID, acaia_name)
        self.add_notify(ACAIA_RELAY_NOTIFY_UUID, self.notify_callback)
        self.add_write(ACAIA_RELAY_SERVICE_UUID, ACAIA_RELAY_WRITE_UUID)

    # protocol parser


    def reset_readings(self) -> None:
        self.weight = None
        self.stable_weight = None
        self.battery = None
        self.firmware = None
        self.unit = UNIT.G
        self.max_weight = 0
        self.readability = 0


    def on_connect(self) -> None:
        self.reset_readings()
        self.id_sent = False
        self.fast_notifications_sent = False
        self.slow_notifications_sent = False
        connected_service_UUID, connected_device_name = self.connected()
        self.has_leds = False
        if connected_service_UUID == ACAIA_LEGACY_SERVICE_UUID:
            _log.debug('connected to Acaia Legacy Scale (%s)', connected_device_name)
            self.scale_class = SCALE_CLASS.LEGACY
            self.set_heartbeat(self.HEARTBEAT_FREQUENCY) # enable heartbeat

            if connected_device_name is not None:
                # Acaia Pearl/Lunar (Legacy)
                self.max_weight = 2000
                self.readability = 0.1

        elif connected_service_UUID == ACAIA_RELAY_SERVICE_UUID:
            _log.debug('connected to Acaia Relay Scale (%s)', connected_device_name)
            self.scale_class = SCALE_CLASS.RELAY
            self.set_heartbeat(0) # disable heartbeat

            if connected_device_name is not None:
                if connected_device_name.startswith('UMBRA'):
                    # Acaia Umbra
                    self.max_weight = 1000
                    self.readability = 0.1
                elif connected_device_name.startswith('COSMO-100'):
                    # Acaia Cosmo 100kg
                    self.max_weight = 100*1000
                    self.readability = 10
                    self.has_leds = True
                elif connected_device_name.startswith('COSMO-10'):
                    self.max_weight = 10*1000
                    self.readability = 0.1
                    self.has_leds = True
                else:
                    self.max_weight = 1000
                    self.readability = 0.1
                self.fast_notifications()
                self.fast_notifications_sent = False

        else: #connected_service_UUID == ACAIA_SERVICE_UUID:
            _log.debug('connected to Acaia Scale (%s)', connected_device_name)
            self.scale_class = SCALE_CLASS.MODERN
            # in principle the heartbeat on those newer scales with newer firmwares is not needed
            # but it seems to be needed at least on Pearl 2021 as in some cases (1 of 5) the scale stops sending ID events on connect
            # and thus never gets configured (slow/fast notifications) and thus sends weight messages
            # to be on the safe side we keep sending the heartbeat for those scales
            self.set_heartbeat(self.HEARTBEAT_FREQUENCY)

            if connected_device_name is not None:
                if connected_device_name.startswith(('PYXIS', 'CINCO')):
                    # Acaia Pearl (2021)
                    self.max_weight = 500
                    self.readability = 0.01
                elif connected_device_name.startswith(('PEARL-', 'LUNAR-')):
                    # Acaia Pearl (2021)
                    self.max_weight = 2000
                    self.readability = 0.1
                else:
                    # Acaia Lunar (PEARLS)
                    self.max_weight = 3000
                    self.readability = 0.1

        if self._connected_handler is not None:
            self._connected_handler()
        self.connected_signal.emit()

    def on_disconnect(self) -> None:
        _log.debug('disconnected')
        if self._disconnected_handler is not None:
            self._disconnected_handler()
        self.disconnected_signal.emit()


    ##


    def parse_info(self, data:bytes) -> None:
        _log.debug('INFO MSG')

        if len(data)>5:
            self.firmware = (data[3],data[4],data[5])
            _log.debug('firmware: %s.%s.%s', self.firmware[0], self.firmware[1], f'{self.firmware[2]:>03}')

    def decode_weight(self, payload:bytes) -> Tuple[Optional[float], bool]:
        try:
            #big_endian = (payload[5] & 0x08) == 0x08 # bit 3 of byte 5 is set if weight is in big endian
            big_endian = False # self.scale_class == SCALE_CLASS.RELAY

            value:float = 0
            if big_endian:
                # first 4 bytes encode the weight as unsigned long (big endian)
                value = ((payload[0] & 0xff) << 24) | \
                        ((payload[1] & 0xff) << 16) | \
                        ((payload[2] & 0xff) << 8) | \
                        (payload[3] & 0xff)
            else:
                # first 4 bytes encode the weight as unsigned long (little endian)
                value = ((payload[3] & 0xff) << 24) + \
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
            if self.scale_class != SCALE_CLASS.RELAY:
                # the relay scales report weight always in g
                if self.unit == UNIT.KG:
                    value = value * 1000
                elif self.unit == UNIT.OZ:
                    value = value * 28.3495 # scale set to oz displays 4 decimals

#            if big_endian:
#                stable = (payload[5] & 0x01) == 0x01
#            else:
            stable = (payload[5] & 0x01) != 0x01

            # if 2nd bit of payload[5] is set, the reading is negative
            if (payload[5] & 0x02) == 0x02:
                value *= -1
            return value, stable
        except Exception:  # pylint: disable=broad-except
            return None, False

    def update_weight(self, value:Optional[float], stable:Optional[bool] = False) -> None:
#        _log.debug('PRINT update_weight(%s,%s)', value, stable)
        if value is not None and (not self.stable_only or stable):
            # convert the weight in g delivered with one decimal to an int
            value_rounded:float = float2float(value, self.decimals)
            if stable and value_rounded != self.stable_weight:
                # if value is fresh and reading is stable (if self.stable_only is set)
                self.stable_weight = value_rounded
                self.weight = self.weight # we also update the last weight value to prevent it to be send again
#                _log.debug('PRINT new stable weight: %s', self.stable_weight)
                self.weight_changed_signal.emit(self.stable_weight, stable)
            elif not stable and value_rounded != self.weight:
                self.stable_weight = None # non-stable weights invalidate the last stable weight to ensure a sequence of equal stable weights is reported if interleaved with non-stable weights
                self.weight = value_rounded
#                _log.debug('PRINT new weight: %s', self.weight)
                self.weight_changed_signal.emit(self.weight, stable)

    # returns length of consumed data or -1 on error
    def parse_weight_event(self, payload:bytes) -> int:
        if len(payload) < EVENT_LEN.WEIGHT:
            return -1
        weight, stable = self.decode_weight(payload)
        self.update_weight(weight, stable)
        return EVENT_LEN.WEIGHT

    def parse_battery_event(self, payload:bytes) -> int:
        if len(payload) < EVENT_LEN.BATTERY:
            return -1
        b = payload[0]
        if 0 <= b <= 100:
            self.battery = int(payload[0])
            self.battery_changed_signal.emit(self.battery)
            _log.debug('battery: %s', self.battery)
        return EVENT_LEN.BATTERY

    @staticmethod
    def decode_time(payload:bytes) -> float:
        return ((payload[0] & 0xff) * 60) + payload[1] + payload[2] / 10.

    @staticmethod
    def parse_timer_event(payload:bytes) -> int:
        if len(payload) < EVENT_LEN.TIMER:
            return -1
        value = AcaiaBLE.decode_time(payload)
        _log.debug('time: %sm%s%sms, %s',payload[0],payload[1],payload[2], value)
        return EVENT_LEN.TIMER

    def parse_ack_event(self, payload:bytes) -> int:
        if len(payload) < EVENT_LEN.ACK:
            return -1
#        _log.debug('ACK EVENT')
        consumed_extra = self.parse_extra_weight_time_data(payload[1:])
        return EVENT_LEN.ACK + consumed_extra

    def parse_extra_weight_time_data(self, payload:bytes) -> int:
        if len(payload) > EVENT_LEN.KEY:
            weight:Optional[float] = None
            time:Optional[float] = None
            if payload[0] == KEY_ADDITIONAL_INFO.ZERO:
                _log.debug('aditional key info 0: %s', payload[1:])
            elif payload[0] == KEY_ADDITIONAL_INFO.ONE:
                _log.debug('aditional key info 1: %s', payload[1:])
            elif payload[0] == KEY_ADDITIONAL_INFO.TWO:
                _log.debug('aditional key info 2: %s', payload[1:])
            elif payload[0] == KEY_ADDITIONAL_INFO.THREE:
                _log.debug('aditional key info 3: %s', payload[1:])
            elif payload[0] == KEY_ADDITIONAL_INFO.FOUR:
                _log.debug('aditional key info 4: %s', payload[1:])
            elif payload[0] == KEY_ADDITIONAL_INFO.WEIGHT:
                data_payload = payload[1:]
                if len(data_payload) >= EVENT_LEN.WEIGHT:
                    weight, stable = self.decode_weight(data_payload)
                    _log.debug('key event weight: %s (stable: %s)', weight, stable)
                else:
                    weight = 0
            elif payload[0] == KEY_ADDITIONAL_INFO.SIX:
                _log.debug('aditional key info 6: %s', payload[1:])
            elif payload[0] == KEY_ADDITIONAL_INFO.WEIGHT_TIME:
                time_payload = payload[1:]
                time = (self.decode_time(time_payload) if len(time_payload) >= EVENT_LEN.TIMER else 0)
                weight_payload = payload[5:]
                if len(weight_payload) >= EVENT_LEN.WEIGHT:
                    weight, stable = self.decode_weight(weight_payload)
                    _log.debug('key event time: %s, weight: %s (stable: %s)',time,weight,stable)
                else:
                    weight = 0
            elif payload[0] == KEY_ADDITIONAL_INFO.BATTERY:
                data_payload = payload[1:]
                if len(data_payload) > EVENT_LEN.BATTERY:
                    _log.debug('key event battery: %s', int(data_payload[0]))
            elif payload[0] == KEY_ADDITIONAL_INFO.NINE:
                _log.debug('aditional key info 9: %s', payload[1:])
            elif payload[0] == KEY_ADDITIONAL_INFO.TEN:
                _log.debug('aditional key info 10: %s', payload[1:])
            elif payload[0] == KEY_ADDITIONAL_INFO.ELEVEN:
                _log.debug('aditional key info 11: %s', payload[1:])
            elif payload[0] == KEY_ADDITIONAL_INFO.TWELVE:
                _log.debug('aditional key info 12: %s', payload[1:])
            elif payload[0] == KEY_ADDITIONAL_INFO.THIRTEEN:
                _log.debug('aditional key info 13: %s', payload[1:])
            return 1
        return 0

    def parse_key_event(self, payload:bytes) -> int:
        if len(payload) < EVENT_LEN.KEY:
            return -1
        _log.debug('KEY EVENT')

        if payload[0] == KEY_INFO.TARE:
            _log.debug('tare key')
        elif payload[0] == KEY_INFO.START:
            _log.debug('start timer key')
        elif payload[0] == KEY_INFO.STOP:
            _log.debug('stop timer key')
        elif payload[0] == KEY_INFO.RESET:
            _log.debug('reset timer key')
        elif payload[0] == KEY_INFO.DOUBLE:
            _log.debug('double key event')
        else:
            _log.debug('unknown key event: %s', payload)
        consumed_extra = self.parse_extra_weight_time_data(payload[1:])
        return EVENT_LEN.KEY + consumed_extra

    def parse_scale_event(self, payload:bytes) -> int:
        if payload and len(payload) > 1:
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
            elif event == EVENT.SETTING:
                pass
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
#        _log.debug('STATUS')

        # byte 0: message len

        # byte 1: battery level (7 bits of second byte) + TIMER_START (1bit)
        if payload and len(payload) > 1:
            self.battery = int(payload[1] & ~(1 << 7))
            self.battery_changed_signal.emit(self.battery)
#            _log.debug('battery: %s%%', self.battery)

        # byte 2:
        if payload and len(payload) > 2:
            if self.scale_class == SCALE_CLASS.RELAY:
                # relay scales: auto off setting for
                auto_off = int(payload[2] & 0xFF)
                if auto_off == 0:
                    self.auto_off_timer = AUTO_OFF_TIMER.AUTO_SLEEP_OFF
#                    _log.debug('AUTO OFF TIMER: Auto Sleep Off')
                elif auto_off == 1:
                    self.auto_off_timer = AUTO_OFF_TIMER.AUTO_SLEEP_5MIN
#                    _log.debug('AUTO OFF TIMER: AutoSleep 5 min')
                elif auto_off == 2:
                    self.auto_off_timer = AUTO_OFF_TIMER.AUTO_SLEEP_15MIN
#                    _log.debug('AUTO OFF TIMER: AutoSleep 15 min')
                elif auto_off == 3:
                    self.auto_off_timer = AUTO_OFF_TIMER.AUTO_SLEEP_30MIN
#                    _log.debug('AUTO OFF TIMER: AutoSleep 30 min')
                elif auto_off == 4:
                    self.auto_off_timer = AUTO_OFF_TIMER.AUTO_OFF_5MIN
#                    _log.debug('AUTO OFF TIMER: Auto Off 5 min')
                elif auto_off == 5:
                    self.auto_off_timer = AUTO_OFF_TIMER.AUTO_OFF_10MIN
#                    _log.debug('AUTO OFF TIMER: Auto Off 10 min')
                elif auto_off == 6:
                    self.auto_off_timer = AUTO_OFF_TIMER.AUTO_OFF_30MIN
#                    _log.debug('AUTO OFF TIMER: Auto Off 30 min')
                elif auto_off == 7:
                    self.auto_off_timer = AUTO_OFF_TIMER.AUTO_SLEEP_1MIN
#                    _log.debug('AUTO OFF TIMER: AutoSleep 1 min')
            else:
                # display scales: weight unit (7 bits of third byte) + CD_START (1bit)
                self.unit = int(payload[2] & 0x7F)
#                _log.debug('unit: %s (%s)', self.unit, ('g' if self.unit == UNIT.G else 'oz'))

#        # byte 3:
#        if payload and len(payload) > 3:
#            if self.scale_class == SCALE_CLASS.RELAY:
#                # relay scales: beep setting (0:off, 1:on)
#                # display scales: beep setting (0:off, 1:on)
#                _log.debug('sound: %s', ('on' if payload[6] else 'off'))
#            else:
#                # display scales: mode (7 bits of third byte) + tare (1bit)
#                mode = int(payload[3] & 0x7F)
#                _log.debug('mode: %s', mode)
#                _log.debug('tare: %s', (payload[3] & 0x80) == 0x80)
#                # Lunar
#                # 2: NodE_1 Weighing Mode
#                # 4: NodE_2 Dual Display Mode
#                # 3: NodE_3 Timer Starts with Flow Mode (drop)
#                # 15: NodE_4 Auto-Tare Timer Starts with Flow Mode (drop/square)
#                # 16: NodE_5 Auto-Tare Auto-Start Timer Mode (triangle/square)
#                # 17: NodE_6 Auto-Tare Mode (square)

#        # byte 4:
#        if payload and len(payload) > 4:
#            if self.scale_class == SCALE_CLASS.RELAY:
#                # relay scales: weight unit setting (0:g, 1:oz)
#                self.unit = (UNIT.OZ if payload[4] == 1 else UNIT.G)
#                _log.debug('unit: %s (%s)', self.unit, ('g' if self.unit == UNIT.G else 'oz'))
#            else:
#                sleep_modes = {0:'off', 1:'5sec', 2:'10sec', 3:'20sec', 4:'30sec', 5:'60sec'}
#                _log.debug('sleep: %s%s', payload[4], (f' ({sleep_modes[payload[4]]})' if (payload[4] in sleep_modes) else ''))

#        # byte 5:
#        if payload and len(payload) > 5:
#            if self.scale_class == SCALE_CLASS.RELAY:
#                # relay scales: resolution setting
#                _log.debug('resolution: %s', ('0.01g' if payload[5] else '0.1g')) # resolution/readability: 0.1g / 0.01g
#            else:
#                # display scales: key disabled (0: off , 1: on)
#                _log.debug('keys disabled: %s', ('on' if payload[5] else 'off'))

#        # byte 6:
#        if payload and len(payload) > 6:
#            if self.scale_class == SCALE_CLASS.RELAY:
#                # relay scales: magic relay sensing (low/normal/high)
#                _log.debug('magic relay sensing: %s', payload[6])
#                # 0: low, 1: normal, 2: high
#            else:
#                # display scales: beep setting (0:off, 1:on)
#                _log.debug('sound: %s', ('on' if payload[6] else 'off'))

        # byte 7:
#        if payload and len(payload) > 7:
#            if self.scale_class == SCALE_CLASS.RELAY:
#                # relay scales: magic relay beep
#                _log.debug('magic relay beep: %s', ('on' if payload[7] else 'off'))
#            else:
#                # display scales: resolution (0:default, 1:high)
#                _log.debug('resolution: %s', ('high' if payload[7] else 'default'))

#        # byte 8/8/10:
#        if payload and len(payload) > 10 and self.scale_class == SCALE_CLASS.RELAY:
#            # firmware version
#            firmware = (payload[8],payload[9],payload[10])
#            _log.debug('firmware: %s.%s.%s', firmware[0], firmware[1], firmware[2])

        # bytes 11 & 12 reserved


    def parse_data(self, msg_type:int, data:bytes) -> None:
        try:
            if msg_type == CMD.INFO_A:
                self.parse_info(data)
                self.send_ID() # send after very INFO_A as handshake confirmation
            elif msg_type == CMD.STATUS_A:
                self.parse_status(data)
            elif msg_type == CMD.EVENT_SA:
                self.parse_scale_events(data)
            #
            if self.id_sent and (not self.fast_notifications_sent or not self.slow_notifications_sent):
                # NOTE: in some cases previously send fast_notifications are ignore so we have to repeat sending them until we received some initial weight data
                #   (until self.slow_notifications_sent is set)
                # we configure the scale to receive the initial
                # weight notification as fast as possible
                # Note: this event is needed to have the connected scale start to send weight messages even on relay scales which ignore the settings
                self.fast_notifications()

            if not self.id_sent:
                # send ID only once per connect to initiate the handshake
                self.send_ID()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            _log.debug('data: %s',data)

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
            _log.debug('send: %s',payload)

    def send_event(self, payload:bytes) -> None:
        self.send_message(MSG.EVENT, bytes([len(payload)+1]) + payload)

    def send_timer_command(self, cmd:bytes) -> None:
        self.send_message(MSG.TIMER, b'\x00' + cmd)


    ###

    # keep alive should be send every 3-5sec
    def heartbeat(self) -> None:
#        _log.debug('send heartbeat')
        self.send_message(MSG.SYSTEM, b'\x02\x00')

    def send_stop(self) -> None: # stop what?
        _log.debug('send stop')
        self.send_message(MSG.SYSTEM,b'\x00\x00')

    def send_tare(self) -> None:
        _log.debug('send tare')
        self.send_message(MSG.TARE,b'\x00')

    def send_get_settings(self) -> None:
        _log.debug('send get settings')
        self.send_message(MSG.SETTINGS, b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

    def send_start_timer(self) -> None:
        _log.debug('send start time')
        self.send_message(MSG.TIMER,b'\x00\x00')

    def send_stop_timer(self) -> None:
        _log.debug('send stop time')
        self.send_message(MSG.TIMER,b'\x00\x02')

    def send_reset_timer(self) -> None:
        _log.debug('send reset time')
        self.send_message(MSG.TIMER,b'\x00\x01')

    def send_led_cmd(self, payload:bytes) -> None:
        if self.has_leds:
            if self._logging:
                _log.debug('send led command: %s', payload)
            self.send_message(MSG.LED, payload)

    @staticmethod
    def led_color_payload(cmd:LED_CMD, color:Color, value:int=0) -> bytes:
        return bytes([
            cmd,
            value,
            max(0,min(255,color[0])),
            max(0,min(255,color[1])),
            max(0,min(255,color[2])),
            0])

    def send_default_effects_on(self) -> None:
        self.send_led_cmd(self.led_color_payload(LED_CMD.TOGGLE_DEFAULT_EFFECT, self.BLACK, 1))

    def send_default_effects_off(self) -> None:
        self.send_led_cmd(self.led_color_payload(LED_CMD.TOGGLE_DEFAULT_EFFECT, self.BLACK, 0))

    def send_leds_on(self, color:Color) -> None:
        self.send_led_cmd(self.led_color_payload(LED_CMD.ON, color))

    def send_leds_off(self) -> None:
        self.send_led_cmd(self.led_color_payload(LED_CMD.OFF, self.BLACK))

    def send_leds_halo(self, color:Color) -> None:
        self.send_led_cmd(self.led_color_payload(LED_CMD.EFFECT, color, LED_EFFECT.HALO))

    def send_leds_wipe_off(self, color:Color) -> None:
        self.send_led_cmd(self.led_color_payload(LED_CMD.EFFECT, color, LED_EFFECT.WIPE_OFF))

    def send_leds_breathe(self, color:Color) -> None:
        self.send_led_cmd(self.led_color_payload(LED_CMD.EFFECT, color, LED_EFFECT.BREATHE))

    ###

    # handshaking
    def send_ID(self) -> None:
        _log.debug('send ID')
        self.send_message(MSG.IDENTIFY,b'\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d')
        # Old-style id message (for scales with just one characteristic for both, notify and write (e.g. Pyxis)
        # self.send_message(MSG.IDENTIFY,b'\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x31\x32\x33\x34')
        self.id_sent = True

    # NOTE: notifications configuration not supported by Umbra and newer scales!

    def streaming_notifications(self) -> None:
        _log.debug('streaming_notifications')
        self.send_event(
            bytes([ # pairs of key/setting
                    0,  # weight id
                    1])) # only SCALE_CLASS.RELAY # 0: only weight changes are reported; 1: streaming weight changes at 1/10

    def changes_notifications(self) -> None:
        _log.debug('changes_notifications')
        self.send_event(
            bytes([ # pairs of key/setting
                    0,  # weight id
                    0])) # only SCALE_CLASS.RELAY # 0: only weight changes are reported; 1: streaming weight changes at 1/10

    def slow_notifications(self) -> None:
        _log.debug('slow notifications')
        self.send_event(
            bytes([ # pairs of key/setting
                    0,  # weight id
                    (0 if self.scale_class == SCALE_CLASS.RELAY # 0: only weight changes are reported; 1: streaming weight changes at 1/10
                     else 3), # 0, 1, 3, 5, 7, 15, 31, 63, 127  # weight argument (speed of notifications in 1/10 sec; 0:  report changes in weight every 1/10)
                        # 5 or 7 seems to be good values for this app in Artisan
#                    1,   # battery id
#                    255, #2,  # battery argument (if 0 : fast, 1 : slow)
#                    2,  # timer id
#                    255, #5,  # timer argument (number of heartbeats between timer messages)
#                    3,  # key id
#                    255, #4   # request to receive key events
                ])
                )
        self.slow_notifications_sent = True

    def fast_notifications(self) -> None:
        _log.debug('fast notifications')
        self.send_event(
            bytes([ # pairs of key/setting
                    0,  # weight id
                    (1 if self.scale_class == SCALE_CLASS.RELAY # 0: only weight changes are reported; 1: streaming weight changes at 1/10
                     else 1),  # 0, 1, 3, 5, 7, 15, 31, 63, 127  # weight argument (speed of notifications in 1/10 sec) # larger values => slower updates
                        # 5 or 7 seems to be good values for this app in Artisan
#                    1,   # battery id
#                    255, #2,  # battery argument (if 0 : fast, 1 : slow, 2: very slow; not set only once?)
#                    2,  # timer id
#                    255, #5,  # timer argument (number of heartbeats between timer messages; 0: many timer events)
#                    3,  # key id
#                    255, #4   # 0: fast, 1: normal
                ])
                )
        self.fast_notifications_sent = True


    ###

    def notify_callback(self, _sender:'BleakGATTCharacteristic', data:bytearray) -> None:
        if hasattr(self, '_async_loop_thread') and self._async_loop_thread is not None and self._read_queue is not None:
            asyncio.run_coroutine_threadsafe(
                    self._read_queue.put(bytes(data)),
                    self._async_loop_thread.loop)
            if self._logging:
                _log.debug('received: %s',data)


    # EX: d = b'\xef\xdd\x07\x07\x02\x14\x02<\x14\x00W\x18\xef\xdd\x07' (len: 12)
    # 2 header:     d[0:2]   = b'\xef\xdd'
    # 1 cmd:        d[2]     = b'\x07'  => INFO
    # 1 data_len:   d[3]     = b'\x07'  => 7
    # 6 data:       d[4:10]  = b'\x02\x14\x02<\x14\x00'
    # 2 crc:        d[10:12] = b'\x00W\x18'  # calculated over "data_len+data"

    async def reader(self) -> None:
        self._read_queue = asyncio.Queue(maxsize=200) # queue needs to be started in the current async event loop!
        stream = IteratorReader(AsyncIterable(self._read_queue))
        while True:
            try:
                await stream.readuntil(self.HEADER1)
                if await stream.readexactly(1) == self.HEADER2:
                    cmd = int.from_bytes(await stream.readexactly(1), 'big')
                    if cmd in {CMD.SYSTEM_SA, CMD.INFO_A, CMD.STATUS_A, CMD.EVENT_SA}:
                        dl = await stream.readexactly(1)
                        data_len:int = int.from_bytes(dl, 'big')
                        data = await stream.readexactly(data_len - 1)
                        crc = await stream.readexactly(2)
                        data = dl+data
                        if crc == self.crc(data):
                            self.parse_data(cmd, data)
                        else:
                            _log.debug('CRC error: %s <- %s',self.crc(data),data)
            except Exception as e:  # pylint: disable=broad-except
                _log.error(e)


    def on_start(self) -> None:
        if hasattr(self, '_async_loop_thread') and self._async_loop_thread is not None:
            # start the reader
            asyncio.run_coroutine_threadsafe(
                    self.reader(),
                    self._async_loop_thread.loop)


class Acaia(Scale): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class

    def __init__(self, model:int, ident:Optional[str], name:Optional[str], connected_handler:Optional[Callable[[], None]] = None,
                       disconnected_handler:Optional[Callable[[], None]] = None,
                       stable_only:bool=False,
                       decimals:int=1):
        super().__init__(model, ident, name)
        self.acaia = AcaiaBLE(connected_handler = connected_handler, disconnected_handler=disconnected_handler, stable_only=stable_only, decimals=decimals)
        self.acaia.weight_changed_signal.connect(self.weight_changed)
        self.acaia.connected_signal.connect(self.on_connect)
        self.acaia.disconnected_signal.connect(self.on_disconnect)
        self.stable_only = stable_only

        self.scale_connected = False


    def scan(self) -> None:
        devices = self.acaia.scan()
        acaia_devices:ScaleSpecs = []
        # for Acaia scales we filter by name
        for d, a in devices:
            name = (a.local_name or d.name)
            if name:
                match = next((f'{product_name} ({name})' for (name_prefix, product_name) in ACAIA_SCALE_NAMES
                            if name and name.startswith(name_prefix)), None)
                if match is not None:
                    acaia_devices.append((match, d.address))
        self.scanned_signal.emit(acaia_devices)

    def is_connected(self) -> bool:
        return self.scale_connected

    def connect_scale(self, device_logging:bool) -> None:
        self.acaia.setLogging(device_logging)
        self.acaia.start(address=self.ident)

    def disconnect_scale(self) -> None:
        self.acaia.stop()

    @pyqtSlot(float, bool)
    def weight_changed(self, new_value:float, stable:bool) -> None:
        self.weight_changed_signal.emit(new_value, stable)

    def battery_changed(self, new_value:int) -> None:
        self.battery_changed_signal.emit(new_value)

    @pyqtSlot()
    def on_connect(self) -> None:
        self.scale_connected = True
        self.connected_signal.emit()

    @pyqtSlot()
    def on_disconnect(self) -> None:
        self.scale_connected = False
        self.disconnected_signal.emit()

    def tare_scale(self) -> None:
        self.acaia.send_tare()

    def max_weight(self) -> float:
        return self.acaia.max_weight

    def readability(self) -> float:
        return self.acaia.readability

    # signal state actions to the user
    def signal_user(self, action:STATE_ACTION) -> None:
        if action == STATE_ACTION.DISCONNECTED:
            self.acaia.send_leds_wipe_off(self.acaia.MAGENTA)
        elif action == STATE_ACTION.CONNECTED:
            self.acaia.send_leds_halo(self.acaia.CYAN)
        elif action == STATE_ACTION.RELEASED:
            self.acaia.send_leds_breathe(self.acaia.MAGENTA)
            self.acaia.send_default_effects_on()
        elif action == STATE_ACTION.ASSIGNED_GREEN:
            self.acaia.send_default_effects_off()
            self.acaia.send_leds_breathe(self.acaia.WHITE)
        elif action == STATE_ACTION.ASSIGNED_ROASTED:
            self.acaia.send_default_effects_off()
            self.acaia.send_leds_breathe(self.acaia.BROWN)
        elif action == STATE_ACTION.ZONE_ENTER:
            self.acaia.send_leds_on(self.acaia.LIGHT_BLUE)
        elif action == STATE_ACTION.ZONE_EXIT:
            self.acaia.send_leds_off()
        elif action == STATE_ACTION.SWAP_ENTER:
            self.acaia.send_leds_on(self.acaia.ORANGE)
        elif action == STATE_ACTION.SWAP_EXIT:
            self.acaia.send_leds_off()
        elif action == STATE_ACTION.TARGET_ENTER:
#            self.acaia.send_leds_halo(self.acaia.BLUE)
#            libtime.sleep(0.6)
            self.acaia.send_leds_on(self.acaia.BLUE)
        elif action == STATE_ACTION.TARGET_EXIT:
            self.acaia.send_leds_off()
        elif action == STATE_ACTION.OK_ENTER:
            self.acaia.send_leds_on(self.acaia.GREEN)
        elif action == STATE_ACTION.OK_EXIT:
            self.acaia.send_leds_wipe_off(self.acaia.GREEN)
        elif action == STATE_ACTION.CANCEL_ENTER:
            self.acaia.send_leds_on(self.acaia.RED)
        elif action in {STATE_ACTION.CANCEL_EXIT, STATE_ACTION.INTERRUPTED}:
            self.acaia.send_leds_wipe_off(self.acaia.RED)
        elif action in {STATE_ACTION.COMPONENT_CHANGED, STATE_ACTION.TARE}:
            self.acaia.send_leds_breathe(self.acaia.ORANGE)
