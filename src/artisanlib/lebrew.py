#
# ABOUT
# # Lebrew Roast See NEXT BLE support for Artisan

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
# Marko Luther, 2025

import re
import asyncio
import logging
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

    SEPARATOR:Final[bytes] = b'\x00'

    __slots__ = [ '_ble_client', '_ble_client_started', '_payload_pattern', '_agtron', '_crack', '_RoR', '_FoR', '_distance', '_time', '_yellow', '_logging' ]

    def __init__(self,
                    connected_handler:Callable[[], None]|None = None,
                    disconnected_handler:Callable[[], None]|None = None) -> None:

        self._ble_client:Lebrew_RoastSeeNEXT_BLE|None = \
                Lebrew_RoastSeeNEXT_BLE(self.read_msg, connected_handler, disconnected_handler)
        self._ble_client_started:bool = False
        self._payload_pattern:re.Pattern[str] = re.compile(r'[^0-9,.]')

        # current readings
        self._agtron:float = -1  # Color in Agtron
        self._crack:float = -1
        self._RoR:float = -1
        self._FoR:float = -1
        self._distance:float = -1
        self._time:float = -1
        self._yellow:float = 0

        # configuration
        self._logging = False         # if True device communication is logged

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

    def register_reading(self, data:bytes) -> None:
        if self._logging:
            _log.debug('register_reading(%s)',data)
        try:
            values = tuple(float(v) for v in self._payload_pattern.sub('', data.decode('utf-8')).split(','))
            if len(values) == 7:
                self._agtron, self._crack, self._RoR, self._FoR, self._distance, self._time, self._yellow = values
        except UnicodeDecodeError:
            pass

    # asyncio read implementation

    # https://www.oreilly.com/library/view/using-asyncio-in/9781492075325/ch04.html
    async def read_msg(self, stream: asyncio.StreamReader|IteratorReader) -> None:
        data = await stream.readuntil(self.SEPARATOR)
        # register readings
        self.register_reading(data[:-len(self.SEPARATOR)]) # self.SEPARATOR is included in readuntil result and need to be removed

    def start(self, connect_timeout:float=3) -> None:
        if self._ble_client is not None and not self._ble_client_started:
            self._ble_client_started = True
            self._ble_client.setLogging(self._logging)
            self._ble_client.start(case_sensitive=False, scan_timeout=5, connect_timeout=connect_timeout)

    def stop(self) -> None:
        if self._ble_client is not None:
            self._ble_client.stop()
        self._ble_client = None
        self._ble_client_started = False
