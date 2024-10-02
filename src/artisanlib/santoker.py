#
# ABOUT
# Santoker Network support for Artisan

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
# Marko Luther, 2023

import logging
try:
    from pymodbus.framer.rtu import FramerRTU  # type:ignore[attr-defined,unused-ignore]
except Exception: # pylint: disable=broad-except
    # pymodbus <3.7
    from pymodbus.message.rtu import MessageRTU as FramerRTU # type:ignore[import-not-found, no-redef, unused-ignore]
from typing import Final, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.types import SerialSettings # pylint: disable=unused-import
import asyncio

from artisanlib.async_comm import AsyncComm

_log: Final[logging.Logger] = logging.getLogger(__name__)

class Santoker(AsyncComm):

    HEADER:Final[bytes] = b'\xEE\xA5'
    CODE_HEADER:Final[bytes] = b'\x02\x04'
    TAIL:Final[bytes] = b'\xff\xfc\xff\xff'

    # data targets
    BT:Final[bytes] = b'\xF3'
    ET:Final[bytes] = b'\xF4'
    POWER:Final[bytes] = b'\xFA'
    AIR:Final[bytes] = b'\xCA'
    DRUM:Final[bytes] = b'\xC0'
    #
    CHARGE:Final = b'\x80'
    DRY:Final = b'\x81'
    FCs:Final = b'\x82'
    SCs:Final = b'\x83'
    DROP:Final = b'\x84'

    __slots__ = [ '_charge_handler', '_dry_handler', '_fcs_handler', '_scs_handler', '_drop_handler', '_bt', '_et', '_power',
                    '_air', '_drum', '_CHARGE', '_DRY', '_FCs', '_SCs', '_DROP' ]

    def __init__(self, host:str = '127.0.0.1', port:int = 8080, serial:Optional['SerialSettings'] = None,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None,
                charge_handler:Optional[Callable[[], None]] = None,
                dry_handler:Optional[Callable[[], None]] = None,
                fcs_handler:Optional[Callable[[], None]] = None,
                scs_handler:Optional[Callable[[], None]] = None,
                drop_handler:Optional[Callable[[], None]] = None) -> None:

        super().__init__(host, port, serial, connected_handler, disconnected_handler)

        # handlers
        self._charge_handler:Optional[Callable[[], None]] = charge_handler
        self._dry_handler:Optional[Callable[[], None]] = dry_handler
        self._fcs_handler:Optional[Callable[[], None]] = fcs_handler
        self._scs_handler:Optional[Callable[[], None]] = scs_handler
        self._drop_handler:Optional[Callable[[], None]] = drop_handler

        # current readings
        self._bt:float = -1   # bean temperature in °C
        self._et:float = -1   # environmental temperature in °C
        self._power:int = -1  # heater power in % [0-100]
        self._air:int = -1    # fan speed in % [0-100]
        self._drum:int = -1   # drum speed in % [0-100]

        # current roast state
        self._CHARGE:bool = False
        self._DRY:bool = False
        self._FCs:bool = False
        self._SCs:bool = False
        self._DROP:bool = False

    # external API to access machine state

    def getBT(self) -> float:
        return self._bt
    def getET(self) -> float:
        return self._et
    def getPower(self) -> int:
        return self._power
    def getAir(self) -> int:
        return self._air
    def getDrum(self) -> int:
        return self._drum

    def resetReadings(self) -> None:
        self._bt = -1
        self._et = -1
        self._power = -1
        self._air = -1
        self._drum = -1

    # message decoder

    def register_reading(self, target:bytes, value:int) -> None:
        if self._logging:
            _log.info('register_reading(%s,%s)',target,value)
        if target == self.BT:
            self._bt = value / 10.0
        elif target == self.ET:
            self._et = value / 10.0
        elif target == self.POWER:
            self._power = value
        elif target == self.AIR:
            self._air = value
        elif target == self.DRUM:
            self._drum = value
        #
        elif target == self.CHARGE:
            b = bool(value)
            if b and b != self._CHARGE and self._charge_handler is not None:
                try:
                    self._charge_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            self._CHARGE = b
        elif target == self.DRY:
            b = bool(value)
            if b and b != self._DRY and self._dry_handler is not None:
                try:
                    self._dry_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            self._DRY = b
        elif target == self.FCs:
            b = bool(value)
            if b and b != self._FCs and self._fcs_handler is not None:
                try:
                    self._fcs_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            self._FCs = b
        elif target == self.SCs:
            b = bool(value)
            if b and b != self._SCs and self._scs_handler is not None:
                try:
                    self._scs_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            self._SCs = b
        elif target == self.DROP:
            b = bool(value)
            if b and b != self._DROP and self._drop_handler is not None:
                try:
                    self._drop_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            self._DROP = b
        else:
            _log.debug('unknown data target %s', target)


    # asyncio read implementation

    # https://www.oreilly.com/library/view/using-asyncio-in/9781492075325/ch04.html
    async def read_msg(self, stream: asyncio.StreamReader) -> None:
        # look for the first header byte
        await stream.readuntil(self.HEADER[0:1])
        # check for the second header byte (wifi)
        if await stream.readexactly(1) != self.HEADER[1:2]:
            return
        # read the data target (BT, ET,..)
        target = await stream.readexactly(1)
        # read code header
        code2 = await stream.readexactly(2)
        if code2 != self.CODE_HEADER:
            _log.debug('unexpected CODE_HEADER: %s', code2)
            return
        # read the data length
        data_len = await stream.readexactly(1)
        data = await stream.readexactly(int.from_bytes(data_len, 'big'))
        # convert data into the integer data
        value = int.from_bytes(data, 'big')
        # compute and check the CRC over the code header, length and data
        crc = await stream.readexactly(2)
        if self._verify_crc and int.from_bytes(crc, 'big') != FramerRTU.compute_CRC(self.CODE_HEADER + data_len + data):
            _log.debug('CRC error')
            return
        # check tail
        tail = await stream.readexactly(4)
        if tail != self.TAIL:
            _log.debug('unexpected TAIL: %s', tail)
            return
        # full message decoded
        self.register_reading(target, value)


    # send message interface

    # message encoder
    def create_msg(self, target:bytes, value: int) -> bytes:
        data_len = 3
        data = self.CODE_HEADER + data_len.to_bytes(1, 'big') + value.to_bytes(data_len, 'big')
        crc: bytes = FramerRTU.compute_CRC(data).to_bytes(2, 'big')
        return self.HEADER + target + data + crc + self.TAIL

    def send_msg(self, target:bytes, value: int) -> None:
        self.send(self.create_msg(target, value))


def main() -> None:
    import time
    santoker = Santoker(host = '10.10.100.254', port = 20001)
    santoker.start()
    for _ in range(4):
        print('>>> hallo')
        santoker.send_msg(santoker.POWER,1000) # set power to 1000Hz
        time.sleep(1)
        print('BT',santoker.getBT())
        time.sleep(1)
    santoker.stop()
    time.sleep(1)
    #print('thread alive?',santoker._thread.is_alive())

if __name__ == '__main__':
    main()
