#
# ABOUT
# Lebrew Roast See NEXT BLE support for artisan scope
#
# COPYRIGHT (C) 2010-2026 The artisan team represented by
#   Marko Luther <marko.luther@gmx.net> (maintainer) and all contributors
#
# LICENSE
# This program or module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# MAINTAINER
# Marko Luther, 2026
#
# AUTHOR
# Marko Luther, 2025

import re
import time
import asyncio
import logging
import struct
from pymodbus.framer.rtu import FramerRTU
from collections.abc import Callable, Awaitable
from typing import override, Final, TYPE_CHECKING

if TYPE_CHECKING:
    from bleak.backends.characteristic import BleakGATTCharacteristic  # pylint: disable=unused-import

from artisanlib.async_comm import AsyncIterable, IteratorReader
from artisanlib.ble_port import ClientBLE

_log: Final[logging.Logger] = logging.getLogger(__name__)

class Lebrew_RoastSeeNEXT_BLE(ClientBLE):
    # Lebrew RoastSee NEXT service and characteristics UUIDs
    LEBREW_RoastSeeNEXT_Name:Final[str] = 'RoastSeeNEXT'
    LEBREW_RoastSeeNEXT_UUID:Final[str] = '000000bb-0000-1000-8000-00805f9b34fb' # '00bb'
    LEBREW_RoastSeeNEXT_NOTIFY_UUID:Final[str] = '0000bb01-0000-1000-8000-00805f9b34fb' # 'bb01'
    LEBREW_RoastSeeNEXT_WRITE_UUID:Final[str] = '0000bb01-0000-1000-8000-00805f9b34fb' # 'bb01'

    def __init__(self,
                    read_msg:Callable[[asyncio.StreamReader|IteratorReader], Awaitable[None]],
                    connected_handler:Callable[[], None]|None = None,
                    disconnected_handler:Callable[[], None]|None = None):
        super().__init__()

        # Protocol parser variables
        self._read_queue : asyncio.Queue[bytes]|None = None
        self._read_msg:Callable[[asyncio.StreamReader|IteratorReader], Awaitable[None]] = read_msg

        # handlers
        self._connected_handler = connected_handler
        self._disconnected_handler = disconnected_handler

        self.add_device_description(self.LEBREW_RoastSeeNEXT_UUID, self.LEBREW_RoastSeeNEXT_Name)
        self.add_notify(self.LEBREW_RoastSeeNEXT_NOTIFY_UUID, self.notify_callback)
        self.add_write(self.LEBREW_RoastSeeNEXT_UUID, self.LEBREW_RoastSeeNEXT_WRITE_UUID)

    def notify_callback(self, _sender:'BleakGATTCharacteristic', data:bytearray) -> None:
        if hasattr(self, '_async_loop_thread') and self._async_loop_thread is not None and self._read_queue is not None:
            if self._logging:
                _log.debug('notify: %s => %s', self._read_queue.qsize(), data)
            asyncio.run_coroutine_threadsafe(
                    self._read_queue.put(bytes(data)),
                    self._async_loop_thread.loop)

    @override
    def on_connect(self) -> None: # pylint: disable=no-self-use
        if self._connected_handler is not None:
            self._connected_handler()

    @override
    def on_disconnect(self) -> None: # pylint: disable=no-self-use
        if self._disconnected_handler is not None:
            self._disconnected_handler()

    async def reader(self) -> None:
        self._read_queue = asyncio.Queue(maxsize=200) # queue needs to be started in the current async event loop!
        stream = IteratorReader(AsyncIterable(self._read_queue))
        while True:
            await self._read_msg(stream)

    @override
    def on_start(self) -> None:
        if hasattr(self, '_async_loop_thread') and self._async_loop_thread is not None:
            # start the reader
            asyncio.run_coroutine_threadsafe(
                    self.reader(),
                    self._async_loop_thread.loop)



class Lebrew_RoastSeeNEXT:

#    SEPARATOR:Final[bytes] = b'\x00'
    HEADER:Final[bytes] = b'\xAA\x55'
    TAIL:Final[bytes] = b'\x53\x42'

    __slots__ = [ '_connected_handler', '_disconnected_handler', '_ble_client', '_ble_client_started',
        '_payload_pattern', '_agtron', '_crack', '_RoR', '_FoR', '_distance', '_time', '_yellow', '_logging',
        '_verify_crc' ]

    def __init__(self,
                    connected_handler:Callable[[], None]|None = None,
                    disconnected_handler:Callable[[], None]|None = None) -> None:

        self._connected_handler = connected_handler
        self._disconnected_handler = disconnected_handler
        self._ble_client:Lebrew_RoastSeeNEXT_BLE|None = \
                Lebrew_RoastSeeNEXT_BLE(self.read_msg, self.connected_handler, self.disconnected_handler)
        self._ble_client_started:bool = False
        self._payload_pattern:re.Pattern[str] = re.compile(r'[^0-9,.]')

        # current readings
        self._agtron:float = -1  # Color in Agtron
        self._crack:float = -1
        self._RoR:float = -1
        self._FoR:float = -1 # weighted_median_mean_agtron (mean or median!?)
        self._distance:float = -1
        self._time:float = -1
        self._yellow:float = 0

        # configuration
        self._logging = False         # if True device communication is logged
        self._verify_crc:bool = True  # if True the CRC of incoming messages is verified

    # handlers

    def connected_handler(self) -> None:
        self.start_measuring()
        if self._connected_handler is not None:
            self._connected_handler()

    def disconnected_handler(self) -> None:
        if self._disconnected_handler is not None:
            self._disconnected_handler()


    # external API to access sensor state

    def getAgtron(self) -> float:
        return self._agtron
    def getCrack(self) -> float:
        return self._crack
    def getRoR(self) -> float:
        return self._RoR
    def getFoR(self) -> float:
        return self._FoR
    def getDistance(self) -> float:
        return self._distance
    def getTime(self) -> float:
        return self._time
    def getYellow(self) -> float:
        return self._yellow

    def resetReadings(self) -> None:
        self._agtron = -1
        self._crack = -1
        self._RoR = -1
        self._FoR = -1
        self._distance = -1
        self._time = -1
        self._yellow = 0


    # config

    def setLogging(self, b:bool) -> None:
        self._logging = b

    def client_started(self) -> bool:
        return self._ble_client_started


    # message decoder

#    def register_reading(self, data:bytes) -> None:
#        if self._logging:
#            _log.debug('register_reading(%s)',data)
#        try:
#            values = tuple(float(v) for v in self._payload_pattern.sub('', data.decode('utf-8')).split(','))
#            if len(values) == 7:
#                self._agtron, self._crack, self._RoR, self._FoR, self._distance, self._time, self._yellow = values
#        except UnicodeDecodeError:
#            pass

    def register_reading(self, data:bytes) -> None:
        if self._logging:
            _log.debug('register_reading(%s)',data)
        try:
            if len(data)>3:
                self._agtron = struct.unpack('<f', data[:4])[0] # little endian interpretation of 4 bytes as float
            if len(data)>4:
                self._crack = data[4]
            if len(data)>8:
                self._RoR = struct.unpack('<f', data[5:9])[0]
            if len(data)>12:
                self._FoR = struct.unpack('<f', data[9:13])[0]
            if len(data)>14:
                self._distance = int.from_bytes(data[13:15], 'little')
            if len(data)>16:
                self._time = int.from_bytes(data[15:17], 'little')
            if len(data)>17:
                self._yellow = data[17]
#            if len(data)>19L
#                roast_nr = int.from_bytes(data[18:20], "little") # nr of roast
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    # asyncio read implementation

#    # https://www.oreilly.com/library/view/using-asyncio-in/9781492075325/ch04.html
#    async def read_msg(self, stream: asyncio.StreamReader|IteratorReader) -> None:
#        data = await stream.readuntil(self.SEPARATOR)
#        # register readings
#        self.register_reading(data[:-len(self.SEPARATOR)]) # self.SEPARATOR is included in readuntil result and need to be removed

    async def read_msg(self, stream: asyncio.StreamReader|IteratorReader) -> None:
        try:
            await stream.readuntil(self.HEADER[0:1])
            # check for the second header byte
            snd_byte = await stream.readexactly(1)
            if snd_byte != self.HEADER[1:2]:
                return
            data_len = await stream.readexactly(1)
            data = await stream.readexactly(data_len[0])

            # CRC calculated over data
            calculated_crc = FramerRTU.compute_CRC(data_len + data).to_bytes(2, 'big')
            crc = await stream.readexactly(2)
            if self._verify_crc and crc != calculated_crc:
                if self._logging:
                    _log.debug('CRC error')
                return
            tail = await stream.readexactly(2)
            if tail != self.TAIL:
                return

            self.register_reading(data)

        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)


    def send_msg(self, message:bytes) -> None:
        if hasattr(self, '_ble_client') and self._ble_client is not None:
            # send via BLE
            if self._logging:
                _log.debug('send_msg(%s)',message)
            self._ble_client.send(message, response=True)

    def start(self, connect_timeout:float=3) -> None:
        if self._ble_client is not None and not self._ble_client_started:
            self._ble_client_started = True
            self._ble_client.setLogging(self._logging)
            self._ble_client.start(case_sensitive=False, scan_timeout=5, connect_timeout=connect_timeout)

    def stop(self) -> None:
        if self._ble_client is not None:
            self.stop_measuring()
            self._ble_client.stop()
        self._ble_client = None
        self._ble_client_started = False

    # adds \r\n to make sure commands are processed
    def send_message(self, msg:str) -> None:
        self.send_msg(f'{msg}\r\n'.encode(encoding='ascii', errors='ignore'))

    def start_measuring(self) -> None:
        self.send_message('roasting')
        time.sleep(0.3)
        self.send_message('start')

    def stop_measuring(self) -> None:
        self.send_message('stop')

# further commands
#  back
#  agtron
#  zeroing
#  history
#  readlog
#  yellow
#
# and the following (which have to given in quotes in an Artisan Command):
#  NEXT:PAGE.ROASTING_LIVE
#  NEXT:PAGE.AGTRON_LIVE
#  NEXT:PAGE.ZEROING_CONFIRM
#  NEXT:PAGE.HISTORY
#  NEXT:PAGE.BACK
#  NEXT:ROASTING.START
#  NEXT:ROASTING.STOP
#  NEXT:AGTRON.START
#  NEXT:AGTRON.STOP
#  NEXT:HISTORY.READ
#  NEXT:SETTING.YELLOW <1-50>
