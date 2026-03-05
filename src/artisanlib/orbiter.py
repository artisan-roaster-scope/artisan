#
# ABOUT
# Oribter support for Artisan

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
# Marko Luther, 2026


import asyncio
import logging


from collections.abc import Callable
from typing import override, Final, TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.atypes import SerialSettings # pylint: disable=unused-import

from artisanlib.async_comm import AsyncComm, IteratorReader

_log: Final[logging.Logger] = logging.getLogger(__name__)




class State(TypedDict, total=False):
    Connected:int  # connection status (0:disconnected, 1:connected)
    BT:float   # bean temperature
    ET:float   # environmental temperature
    IT:float   # inlet temperature
    DT:float   # drum temperature
    Air:float  # air pressure
    Drum:int   # drum speed (50-90 RPM)
    Damper:int # air damper setting (0-15)
    Heater:int # heater power (0-10; 0-3200W)
    Sound:int  #
    RoR:float  # rate-of-rise




class Orbiter(AsyncComm):

    HEADER:Final[bytes] = b'\xFF\xFF'
    EVENT:Final[bytes] = b'\x00'
    CMD_INIT:Final[bytes] = b'\x01'
    CMD_SYNC:Final[bytes] = b'\x00'

    __slots__ = [ 'send_timeout', '_connected', '_new_readings_available', '_BT', '_ET', '_IT', '_DT', '_air', '_drum', '_damper',
            '_heater', '_sound', '_RoR', '_master_control', '_SERIAL',  '_FW_VERSION', '_PCB_VERSION', '_DASHBOARD_STATUS', '_MODEL', '_MODEL_NUM',
            'isRoaster_Roasting' ]

    def __init__(self, serial:'SerialSettings',
                connected_handler:Callable[[], None]|None = None,
                disconnected_handler:Callable[[], None]|None = None) -> None:

        super().__init__(serial=serial, connected_handler=connected_handler, disconnected_handler=disconnected_handler)

        # configuration
        self.send_timeout:Final[float] = 0.6    # in seconds
        self._logging = False # if True device communication is logged

        # current readings
        self._connected:int = 0  # connection status (0:disconnected, 1:connected)
        self._new_readings_available:asyncio.Event = asyncio.Event()
        #-
        self._BT:float = -1      # bean temperature
        self._ET:float = -1      # environmental temperature
        self._IT:float = -1      # interlayer temperature
        self._DT:float = -1      # drum temperature
        self._air:float = -1     # air pressure
        self._drum:int = -1      # drum speed (50-90 RPM)
        self._damper:int = -1    # air damper setting (0-15)
        self._heater:int = -1    # heater power (0-10; 0-3200W)
        self._sound:int = -1     # sound recognition
        self._RoR:float = -1     # rate-of-rise
        self._master_control:int = 0 # master control

        # machine spec
        self._SERIAL:str = ''                      # 7 bytes
        self._FW_VERSION:str = ''                  # 7 bytes
        self._PCB_VERSION:int = 0                  # 1 byte
        self._DASHBOARD_STATUS:bytes = b'\x00\x00' # 2 bytes
        self._MODEL:str = ''                       # 2 bytes
        self._MODEL_NUM:int = 0                    # 1 byte
        # machine status
        self.isRoaster_Roasting:bool = False

    @override
    def setLogging(self, b:bool) -> None:
        self._logging = b
        super().setLogging(b)

    # external API to access machine state

    # getBT triggers fetching a complete set of new readings
    # time is the preheat/roasting/cooling time in seconds send along the sync command to the machine
    def getBT(self, time:int = 0) -> float:
        if not self._new_readings_available.is_set():
            self.send_sync_await(time)
        self._new_readings_available.clear()
        return self._BT
    def getET(self) -> float:
        return self._ET
    def getIT(self) -> float:
        return self._IT
    def getDT(self) -> float:
        return self._DT
    def getAir(self) -> float:
        return self._air
    def getDrum(self) -> int:
        return self._drum
    def getDamper(self) -> int:
        return self._damper
    def getHeater(self) -> int:
        return self._heater
    def getSound(self) -> int:
        return self._sound
    def getRoR(self) -> float:
        return self._RoR
    def getMasterControl(self) -> float:
        return self._master_control

    def resetReadings(self) -> None:
        self._connected = 0
        self._BT = -1
        self._ET = -1
        self._IT = -1
        self._DT = -1
        self._air = -1
        self._drum = -1
        self._damper = -1
        self._heater = -1
        self._sound = -1
        self._RoR = -1


    # message decoder

    def register_reading(self, target:bytes, data:bytes) -> None:
        pass

    # decoding utils

    # returns True if bit at offset is 1 else False
    @staticmethod
    def test_bit(b:int, offset:int) -> bool:
        mask = 1 << offset
        return (b & mask) != 0

    # asyncio read implementation

    # https://www.oreilly.com/library/view/using-asyncio-in/9781492075325/ch04.html
    @override
    async def read_msg(self, stream: asyncio.StreamReader|IteratorReader) -> None:
        # await first header byte
        await stream.readuntil(self.HEADER[0:1])
        # check for the second header byte
        if await stream.readexactly(1) == self.HEADER[1:2]:
            cmd = await stream.readexactly(1)
            if cmd[0] == 0: # sync data (total 28 bytes)
                if self._logging:
                    _log.debug('Orbiter CMD sync data')
                data = await stream.readexactly(25)
                if self._logging:
                    _log.debug('Orbiter data: %s', data)
                # check CRC
                try:
                    if self.crc(cmd[0:1] + data[:24]) == data[24]:
                        dashboard_state = data[3:5]
                        dashboard_state_low = dashboard_state[0]
#                        dashboard_state_high = dashboard_state[1]
                        #
                        self.isRoaster_Roasting = self.test_bit(dashboard_state_low, 2)
#                        if self.isRoaster_Roasting:
#                            _log.debug("isRoaster_Roasting")
#                        else:
#                            _log.debug("NOT isRoaster_Roasting")
                        #
                        self._BT = int.from_bytes(data[7:9], 'little', signed=True)
                        self._DT = int.from_bytes(data[9:11], 'little', signed=True)
                        self._IT = int.from_bytes(data[11:13], 'little', signed=True)
                        self._ET = int.from_bytes(data[13:15], 'little', signed=True)
                        self._RoR = int.from_bytes(data[15:17], 'little', signed=True) / 4.
                        self._air = int.from_bytes(data[17:19], 'little', signed=True)
                        self._heater = data[19]
                        self._drum = data[20]
                        self._damper = data[21]
                        self._sound = data[22]
                        self._master_control = data[23]
                        self._new_readings_available.set()
                    else:
                        _log.debug('Orbiter CRC failed: %s != %s', self.crc(cmd[0:1] + data[:24]), data[24])
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            elif cmd[0] == 1: # init ack (total 28 bytes)
                if self._logging:
                    _log.debug('Orbiter CMD init ack')
                data = await stream.readexactly(25)
                if self._logging:
                    _log.debug('Orbiter ack init data: %s', data)
                # check CRC
                try:
                    if self.crc(cmd[0:1] + data[:24]) == data[24]:
                        self._SERIAL = data[1:8].decode('ascii')
                        self._FW_VERSION = data[8:15].decode('ascii')
                        self._PCB_VERSION = data[15]
                        self._DASHBOARD_STATUS = data[17:19]
                        self._MODEL = data[19:21].decode('ascii')
                        self._MODEL_NUM = data[21]
                        self._sound = data[22]
                        self._master_control = data[23]
                        _log.debug("Orbiter SERIAL: '%s'", self._SERIAL)
                        _log.debug("Orbiter FW_VERSION: '%s'", self._FW_VERSION)
                        _log.debug('Orbiter PCB_VERSION: %s', self._PCB_VERSION)
                        _log.debug('Orbiter DASHBOARD_STATUS: %s', self._DASHBOARD_STATUS)
                        _log.debug('Orbiter MODEL: %s', self._MODEL)
                        _log.debug('Orbiter MODEL_NUM: %s', self._MODEL_NUM)
                        _log.debug('Orbiter _sound: %s', self._sound)
                        _log.debug('Orbiter _master_control: %s', self._master_control)
                    else:
                        _log.debug('Orbiter CRC failed: %s != %s', self.crc(cmd[0:1] + data[:24]), data[24])
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)


    # send message interface

    @staticmethod
    def crc(data:bytes) -> int:
        crc = 0
        for b in data:
            crc = crc ^ b
        return crc

    # message encoder (HEADER-CMD-PARA-DATA-TIME-EVENT-CRC)
    def create_msg(self, cmd:bytes, data:bytes, param:bytes, time:int) -> bytes:
        if len(data) == 0:
            data = b'\x00\x00'
        if len(data) == 1:
            data = b'\x00' + data
        data = data[:2] # data is exactly 2 bytes
        payload = cmd[:1] + param + data + min(max(0,time),65535).to_bytes(2, 'little') + self.EVENT
        crc:int = self.crc(payload)
        return self.HEADER + payload + crc.to_bytes(1, 'little')

    # data byte order: LSB last (little-endian); eg. data=b'\x07\x00' equals 7
    def send_msg(self, cmd:bytes, data:bytes = b'\x00\x00', param:bytes = b'\x00', time:int = 0) -> None:
        # send via socket
        self.send(self.create_msg(cmd, data, param, time))

    def send_msg_await(self, event:asyncio.Event, timeout:float, cmd:bytes, data:bytes = b'\x00\x00', param:bytes = b'\x00', time:int = 0) -> None:
        # send via socket
        self.send_await(self.create_msg(cmd, data, param, time), event, timeout)

    #

    def send_init(self) -> None:
        self.send_msg(self.CMD_INIT)

    def send_sync(self) -> None:
        self.send_msg(self.CMD_SYNC)

    def send_sync_await(self, time:int) -> None:
        self.send_msg_await(self._new_readings_available, self.send_timeout, self.CMD_SYNC, time=time)

    #

    @override
    def start(self, connect_timeout:float=5) -> None:
        super().start(connect_timeout)

#    @override
#    def stop(self) -> None:
#        super().stop()


def main() -> None:
    import time
    from artisanlib.atypes import SerialSettings
    serial = SerialSettings(
        port = '/dev/slave',
        baudrate = 115200,
        bytesize = 8,
        stopbits = 1,
        parity = 'N',
        timeout = 0.5)
    orbiter = Orbiter(serial)
    orbiter.start()
    for _ in range(4):
        print('>>> hallo')
        val:int = 7
        orbiter.send_msg(b'\x0D', val.to_bytes(2, 'little')) # set power to 7
        time.sleep(1)
        print('BT', orbiter.getBT())
        time.sleep(1)
    orbiter.stop()
    time.sleep(1)
    #print('thread alive?',orbiter._thread.is_alive())

if __name__ == '__main__':
    main()
