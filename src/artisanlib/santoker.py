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

import asyncio
import logging

try:
    from pymodbus.framer.rtu import FramerRTU  # type:ignore[attr-defined,unused-ignore]
except Exception: # pylint: disable=broad-except
    # pymodbus <3.7
    from pymodbus.message.rtu import MessageRTU as FramerRTU # type:ignore[import-not-found, no-redef, unused-ignore]
from typing import Final, Optional, Union, Callable, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.atypes import SerialSettings # pylint: disable=unused-import
    from bleak.backends.characteristic import BleakGATTCharacteristic  # pylint: disable=unused-import

from artisanlib.async_comm import AsyncComm, AsyncIterable, IteratorReader
from artisanlib.ble_port import ClientBLE

_log: Final[logging.Logger] = logging.getLogger(__name__)

class SantokerCube_BLE(ClientBLE):

    # Santoker Cube (RFstar) service and characteristics UUIDs
    SANTOKER_CUBE_NAME:Final[str] = 'SANTOKER'
    SANTOKER_CUBE_SERVICE_UUID:Final[str] = '6e400001-b5a3-f393-e0a9-e50e24dcca9e' # Nordic UART Service # advertised service UUID
    SANTOKER_CUBE_NOTIFY_UUID:Final[str] = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'
    SANTOKER_CUBE_WRTIE_UUID:Final[str] = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'

    def __init__(self,
                    read_msg:Callable[[Union[asyncio.StreamReader, IteratorReader]], Awaitable[None]],
                    connected_handler:Optional[Callable[[], None]] = None,
                    disconnected_handler:Optional[Callable[[], None]] = None):
        super().__init__()

        # Protocol parser variables
        self._read_queue : asyncio.Queue[bytes] = asyncio.Queue(maxsize=200)
        self._input_stream = IteratorReader(AsyncIterable(self._read_queue))
        self._read_msg:Callable[[Union[asyncio.StreamReader, IteratorReader]], Awaitable[None]] = read_msg

        # handlers
        self._connected_handler = connected_handler
        self._disconnected_handler = disconnected_handler

        self.add_device_description(self.SANTOKER_CUBE_SERVICE_UUID, self.SANTOKER_CUBE_NAME)
        self.add_notify(self.SANTOKER_CUBE_NOTIFY_UUID, self.notify_callback)
        self.add_write(self.SANTOKER_CUBE_SERVICE_UUID, self.SANTOKER_CUBE_WRTIE_UUID)

    def notify_callback(self, _sender:'BleakGATTCharacteristic', data:bytearray) -> None:
        if self._logging:
            _log.debug('notify: %s => %s', self._read_queue.qsize(), data)
        if hasattr(self, '_async_loop_thread') and self._async_loop_thread is not None:
            asyncio.run_coroutine_threadsafe(
                    self._read_queue.put(bytes(data)),
                    self._async_loop_thread.loop)

    def on_connect(self) -> None: # pylint: disable=no-self-use
        if self._connected_handler is not None:
            self._connected_handler()

    def on_disconnect(self) -> None: # pylint: disable=no-self-use
        if self._disconnected_handler is not None:
            self._disconnected_handler()

    async def reader(self, stream:IteratorReader) -> None:
        while True:
            await self._read_msg(stream)

    def on_start(self) -> None:
        if hasattr(self, '_async_loop_thread') and self._async_loop_thread is not None:
            # start the reader
            asyncio.run_coroutine_threadsafe(
                    self.reader(self._input_stream),
                    self._async_loop_thread.loop)



class Santoker(AsyncComm):

    HEADER_WIFI:Final[bytes] = b'\xEE\xA5'
    HEADER_BT:Final[bytes] = b'\xEE\xB5'
    CODE_HEADER:Final[bytes] = b'\x02\x04'
    TAIL:Final[bytes] = b'\xff\xfc\xff\xff'

    # data targets
    BOARD:Final[bytes] = b'\xF0'
    BT:Final[bytes] = b'\xF1'
    ET:Final[bytes] = b'\xF2'
    OLD_BT:Final[bytes] = b'\xF3'
    OLD_ET:Final[bytes] = b'\xF4'
    BT_ROR:Final[bytes] = b'\xF5'
    ET_ROR:Final[bytes] = b'\xF6'
    IR:Final[bytes] = b'\xF8'
    POWER:Final[bytes] = b'\xFA'
    AIR:Final[bytes] = b'\xCA'
    DRUM:Final[bytes] = b'\xC0'
    #
    CHARGE:Final = b'\x80'
    DRY:Final = b'\x81'
    FCs:Final = b'\x82'
    SCs:Final = b'\x83'
    DROP:Final = b'\x84'
    #
    # unsupported commands:
    MIN_POWER = b'\x85'
    MAX_POWER = b'\x86'
    BT_CALIB = b'\x87'
    ET_CALIB = b'\x88'

    __slots__ = [ 'HEADER', '_charge_handler', '_dry_handler', '_fcs_handler', '_scs_handler', '_drop_handler', '_board', '_bt', '_et',
                    '_bt_ror', '_et_ror', '_ir',
                    '_power', '_air', '_drum', '_CHARGE', '_DRY', '_FCs', '_SCs', '_DROP', '_connect_using_ble', '_ble_client' ]

    def __init__(self, host:str = '127.0.0.1', port:int = 8080, serial:Optional['SerialSettings'] = None,
                connect_using_ble:bool = False,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None,
                charge_handler:Optional[Callable[[], None]] = None,
                dry_handler:Optional[Callable[[], None]] = None,
                fcs_handler:Optional[Callable[[], None]] = None,
                scs_handler:Optional[Callable[[], None]] = None,
                drop_handler:Optional[Callable[[], None]] = None) -> None:

        super().__init__(host, port, serial, connected_handler, disconnected_handler)

        self.HEADER:bytes = (self.HEADER_BT if connect_using_ble else self.HEADER_WIFI)

        self._connect_using_ble:bool = connect_using_ble

        # handlers
        self._charge_handler:Optional[Callable[[], None]] = charge_handler
        self._dry_handler:Optional[Callable[[], None]] = dry_handler
        self._fcs_handler:Optional[Callable[[], None]] = fcs_handler
        self._scs_handler:Optional[Callable[[], None]] = scs_handler
        self._drop_handler:Optional[Callable[[], None]] = drop_handler

        # current readings
        self._board:float = -1  # board temperature in °C
        self._bt:float = -1     # bean temperature in °C
        self._et:float = -1     # environmental temperature in °C
        self._bt_ror:float = -1 # bean temperature rate-of-rise in C°/min
        self._et_ror:float = -1 # environmental temperature rate-of-rise in C°/min
        self._ir:float = -1     # IR temperature in °C
        self._power:int = -1    # heater power in % [0-100]
        self._air:int = -1      # fan speed in % [0-100]
        self._drum:int = -1     # drum speed in % [0-100]

        # current roast state
        self._CHARGE:bool = False
        self._DRY:bool = False
        self._FCs:bool = False
        self._SCs:bool = False
        self._DROP:bool = False

        self._ble_client:Optional[SantokerCube_BLE] = \
                (SantokerCube_BLE(self.read_msg, connected_handler, disconnected_handler) if self._connect_using_ble else None)


    # external API to access machine state

    def getBoard(self) -> float:
        return self._board
    def getBT(self) -> float:
        return self._bt
    def getET(self) -> float:
        return self._et
    def getBT_RoR(self) -> float:
        return self._bt_ror
    def getET_RoR(self) -> float:
        return self._et_ror
    def getIR(self) -> float:
        return self._ir
    def getPower(self) -> int:
        return self._power
    def getAir(self) -> int:
        return self._air
    def getDrum(self) -> int:
        return self._drum

    def resetReadings(self) -> None:
        self._board = -1
        self._bt = -1
        self._et = -1
        self._bt_ror = -1
        self._et_ror = -1
        self._ir = -1
        self._power = -1
        self._air = -1
        self._drum = -1

    # message decoder

    def register_reading(self, target:bytes, data:bytes) -> None:
        #if self._logging:
        value:int
        # convert data into the integer data
        if target in {self.BT_ROR, self.ET_ROR}:
            # first for bits of the RoR data contain the sign of the value
            if len(data) != 2:
                return
            unsigned_data = bytearray(data)
            unsigned_data[0] = data[0] & 15 # clear first 4 bits
            value = int.from_bytes(bytes(unsigned_data), 'big')
            if data[0] & 240 != 176: # first 4 bits not a positive sign (b1011)
                value = - value
        else:
            value = int.from_bytes(data, 'big')
#        if self._logging:
#            _log.debug('register_reading(%s,%s)',target,value)
        if target == self.BOARD:
            self._board = value / 10.0
        elif target in {self.BT, self.OLD_BT}:
            BT = value / 10.0
            self._bt = (BT if self._bt == -1 else (2*BT + self._bt)/3)
            if self._logging:
                _log.debug('BT: %s',self._bt)
        elif target in {self.ET, self.OLD_ET}:
            ET = value / 10.0
            self._et = (ET if self._et == -1 else (2*ET + self._et)/3)
            if self._logging:
                _log.debug('ET: %s',self._et)
        elif target == self.BT_ROR:
            self._bt_ror = value / 10.0
        elif target == self.ET_ROR:
            self._et_ror = value / 10.0
        elif target == self.IR:
            self._ir = value / 10.0
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
#        elif self._logging and target in {self.MIN_POWER, self.MAX_POWER, self.BT_CALIB, self.ET_CALIB}:
#            _log.debug('unsupported data target %s', target)
#        elif self._logging:
#            _log.debug('unknown data target %s', target)


    # asyncio read implementation

    # https://www.oreilly.com/library/view/using-asyncio-in/9781492075325/ch04.html
    async def read_msg(self, stream: Union[asyncio.StreamReader, IteratorReader]) -> None:
        # look for the first header byte
        await stream.readuntil(self.HEADER[0:1])
        # check for the second header byte
#        if await stream.readexactly(1) != self.HEADER[1:2]:
#            return
#        if await stream.readexactly(1) not in {self.HEADER_BT[1:2], self.HEADER_WIFI[1:2]}: # we always accept both headers, the one for WiFi and the one for BT
#            return
        # we accept both headers, BT and WiFi and adjust the self.HEADER to be used on sending messages accordingly
        # as it seems that some machines connected via bluetooth still send data using the WiFi header and expect that header also on read
        # so we adjust to the header we receive and use that on sending our messages as well
        snd_header_byte = await stream.readexactly(1)
        if snd_header_byte == self.HEADER_BT[1:2]:
            self.HEADER = self.HEADER_BT
        elif snd_header_byte == self.HEADER_WIFI[1:2]:
            self.HEADER = self.HEADER_WIFI
        else:
            return
        # read the data target (BT, ET,..)
        target = await stream.readexactly(1)
        # read code header
        code2 = await stream.readexactly(2)
        if code2 != self.CODE_HEADER:
            if self._logging:
                _log.debug('unexpected CODE_HEADER: %s', code2)
            return
        # read the data length
        data_len = await stream.readexactly(1)
        data = await stream.readexactly(int.from_bytes(data_len, 'big'))
        # compute and check the CRC over the code header, length and data
        crc = await stream.readexactly(2)
        calculated_crc = FramerRTU.compute_CRC(self.CODE_HEADER + data_len + data).to_bytes(2, 'big')
#        if self._verify_crc and crc != calculated_crc: # for whatever reason, the first byte of the received CRC is often wrongly just \x00
#        if self._verify_crc and crc != calculated_crc and crc[0] != 0: # we accept a 0 as first CRC bit always!
        if self._verify_crc and crc[1] != calculated_crc[1]: # we only check the second CRC bit!
            if self._logging:
                _log.debug('CRC error')
            return
        # check tail
        tail = await stream.readexactly(4)
        if tail != self.TAIL:
            return
        # full message decoded
        self.register_reading(target, data)

    # send message interface

    # message encoder for values as unsigned integers
    def create_msg(self, target:bytes, value: int) -> bytes:
        data_len = 3 #(value.bit_length() + 7) // 8
        data = self.CODE_HEADER + data_len.to_bytes(1, 'big') + value.to_bytes(data_len, 'big')
        crc: bytes = FramerRTU.compute_CRC(data).to_bytes(2, 'big')
        return self.HEADER + target + data + crc + self.TAIL

    def send_msg(self, target:bytes, value: int) -> None:
        if self._connect_using_ble and hasattr(self, '_ble_client') and self._ble_client is not None:
            # send via BLE
            if self._logging:
                _log.debug('send_msg(%s,%s): %s',target,value,self.create_msg(target, value))
            self._ble_client.send(self.create_msg(target, value))
        else:
            # send via socket
            self.send(self.create_msg(target, value))


    def start(self, connect_timeout:float=5) -> None:
        if self._connect_using_ble and hasattr(self, '_ble_client') and self._ble_client is not None:
            self._ble_client.setLogging(self._logging)
            self._ble_client.start(case_sensitive=False, scan_timeout=5, connect_timeout=3)
        else:
            super().start(connect_timeout)

    def stop(self) -> None:
        if self._connect_using_ble and hasattr(self, '_ble_client') and self._ble_client is not None:
            self._ble_client.stop()
            #del self._ble_client # on this level the released object should be automatically collected by the GC
            self._ble_client = None
        else:
            super().stop()


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
