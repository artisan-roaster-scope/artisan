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
from typing import Optional, Callable
from typing import Final  # Python <=3.7

import asyncio
from contextlib import suppress
from threading import Thread

from pymodbus.utilities import computeCRC
#from pymodbus.client.serial_asyncio import open_serial_connection # patched pyserial-asyncio
from pymodbus.transport.transport_serial import create_serial_connection # patched pyserial-asyncio

from artisanlib.types import SerialSettings

_log: Final[logging.Logger] = logging.getLogger(__name__)

class SantokerNetwork:

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

    __slots__ = [ '_loop', '_thread', '_write_queue', '_bt', '_et', '_power', '_air', '_drum',
        '_CHARGE', '_DRY', '_FCs', '_SCs', '_DROP', '_verify_crc', '_logging' ]

    def __init__(self) -> None:
        # internals
        self._loop:        Optional[asyncio.AbstractEventLoop] = None # the asyncio loop
        self._thread:      Optional[Thread]                    = None # the thread running the asyncio loop
        self._write_queue: Optional['asyncio.Queue[bytes]']    = None # the write queue

        # current readings
        self._bt:float = -1   # bean temperature in °C
        self._et:float = -1   # environmental temperature in °C
        self._power:int = -1  # heater power in % [0-100]
        self._air:int = -1    # fan speed in % [0-100]
        self._drum:int = -1   # drum speed in % [0-100]

        # current roast state (not used yet!)
        self._CHARGE:bool = False
        self._DRY:bool = False
        self._FCs:bool = False
        self._SCs:bool = False
        self._DROP:bool = False

        # configuration
        self._verify_crc:bool = True
        self._logging = False # if True device communication is logged

    # external configuration API
    def setVerifyCRC(self, b:bool) -> None:
        self._verify_crc = b
    def setLogging(self, b:bool) -> None:
        self._logging = b

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

    def register_reading(self, target:bytes, value:int,
                charge_handler:Optional[Callable[[], None]] = None,
                dry_handler:Optional[Callable[[], None]] = None,
                fcs_handler:Optional[Callable[[], None]] = None,
                scs_handler:Optional[Callable[[], None]] = None,
                drop_handler:Optional[Callable[[], None]] = None) -> None:
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
            if b and b != self._CHARGE and charge_handler is not None:
                try:
                    charge_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            self._CHARGE = b
        elif target == self.DRY:
            b = bool(value)
            if b and b != self._DRY and dry_handler is not None:
                try:
                    dry_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            self._DRY = b
        elif target == self.FCs:
            b = bool(value)
            if b and b != self._FCs and fcs_handler is not None:
                try:
                    fcs_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            self._FCs = b
        elif target == self.SCs:
            b = bool(value)
            if b and b != self._SCs and scs_handler is not None:
                try:
                    scs_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            self._SCs = b
        elif target == self.DROP:
            b = bool(value)
            if b and b != self._DROP and drop_handler is not None:
                try:
                    drop_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            self._DROP = b
        else:
            _log.debug('unknown data target %s', target)


    # asyncio loop

    @staticmethod
    async def open_serial_connection(*, loop=None, limit=None, **kwargs):
        """A wrapper for create_serial_connection() returning a (reader,
        writer) pair.

        The reader returned is a StreamReader instance; the writer is a
        StreamWriter instance.

        The arguments are all the usual arguments to Serial(). Additional
        optional keyword arguments are loop (to set the event loop instance
        to use) and limit (to set the buffer limit passed to the
        StreamReader.

        This function is a coroutine.
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        if limit is None:
            limit = 2 ** 16  # 64 KiB
        reader = asyncio.StreamReader(limit=limit, loop=loop)
        protocol = asyncio.StreamReaderProtocol(reader, loop=loop)
        transport, _ = await create_serial_connection(
            loop=loop, protocol_factory=lambda: protocol, **kwargs
        )
        writer = asyncio.StreamWriter(transport, protocol, reader, loop)
        return reader, writer

    # https://www.oreilly.com/library/view/using-asyncio-in/9781492075325/ch04.html
    async def read_msg(self, stream: asyncio.StreamReader,
                charge_handler:Optional[Callable[[], None]] = None,
                dry_handler:Optional[Callable[[], None]] = None,
                fcs_handler:Optional[Callable[[], None]] = None,
                scs_handler:Optional[Callable[[], None]] = None,
                drop_handler:Optional[Callable[[], None]] = None) -> None:
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
        if self._verify_crc and int.from_bytes(crc, 'big') != computeCRC(self.CODE_HEADER + data_len + data):
            _log.debug('CRC error')
            return
        # check tail
        tail = await stream.readexactly(4)
        if tail != self.TAIL:
            _log.debug('unexpected TAIL: %s', tail)
            return
        # full message decoded
        self.register_reading(target, value, charge_handler, dry_handler,
                        fcs_handler, scs_handler, drop_handler)

    async def handle_reads(self, reader: asyncio.StreamReader,
                charge_handler:Optional[Callable[[], None]] = None,
                dry_handler:Optional[Callable[[], None]] = None,
                fcs_handler:Optional[Callable[[], None]] = None,
                scs_handler:Optional[Callable[[], None]] = None,
                drop_handler:Optional[Callable[[], None]] = None) -> None:
        try:
            with suppress(asyncio.CancelledError):
                while not reader.at_eof():
                    await self.read_msg(reader, charge_handler, dry_handler,
                                fcs_handler, scs_handler, drop_handler)
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)

    async def write(self, writer: asyncio.StreamWriter, message: bytes) -> None:
        try:
            if self._logging:
                _log.info('write(%s)',message)
            writer.write(message)
            await writer.drain()
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)

    async def handle_writes(self, writer: asyncio.StreamWriter, queue: 'asyncio.Queue[bytes]') -> None:
        try:
            with suppress(asyncio.CancelledError):
# assignments in while are only only available from Python 3.8
#                while (message := await queue.get()) != b'':
#                    await self.write(writer, message)
                message = await queue.get()
                while message != b'':
                    await self.write(writer, message)
                    message = await queue.get()
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)
        finally:
            with suppress(asyncio.CancelledError, ConnectionResetError):
                await writer.drain()

    # if serial settings are given, host/port are ignore and communication handled by the given serial port
    async def connect(self, host:str, port:int, serial:Optional[SerialSettings] = None,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None,
                charge_handler:Optional[Callable[[], None]] = None,
                dry_handler:Optional[Callable[[], None]] = None,
                fcs_handler:Optional[Callable[[], None]] = None,
                scs_handler:Optional[Callable[[], None]] = None,
                drop_handler:Optional[Callable[[], None]] = None) -> None:
        writer = None
        while True:
            try:
                if serial is not None:
                    _log.debug('connecting to serial port: %s ...',serial['port'])
                    connect = self.open_serial_connection(
                        url=serial['port'],
                        baudrate=serial['baudrate'],
                        bytesize=serial['bytesize'],
                        stopbits=serial['stopbits'],
                        parity=serial['parity'],
                        timeout=serial['timeout'])
                else:
                    _log.debug('connecting to %s:%s ...',host,port)
                    connect = asyncio.open_connection(host, port)
                # Wait for 2 seconds, then raise TimeoutError
                reader, writer = await asyncio.wait_for(connect, timeout=2)
                _log.debug('connected')
                if connected_handler is not None:
                    try:
                        connected_handler()
                    except Exception as e: # pylint: disable=broad-except
                        _log.exception(e)
                self._write_queue = asyncio.Queue()
                read_handler = asyncio.create_task(self.handle_reads(reader, charge_handler,
                                    dry_handler, fcs_handler, scs_handler, drop_handler))
                write_handler = asyncio.create_task(self.handle_writes(writer, self._write_queue))
                done, pending = await asyncio.wait([read_handler, write_handler], return_when=asyncio.FIRST_COMPLETED)
                _log.debug('disconnected')

                for task in pending:
                    task.cancel()
                for task in done:
                    exception = task.exception()
                    if isinstance(exception, Exception):
                        raise exception

            except asyncio.TimeoutError:
                _log.debug('connection timeout')
            except Exception as e: # pylint: disable=broad-except
                _log.error(e)
            finally:
                if writer is not None:
                    try:
                        writer.close()
                    except Exception as e: # pylint: disable=broad-except
                        _log.error(e)

            self.resetReadings()
            if disconnected_handler is not None:
                try:
                    disconnected_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)

            await asyncio.sleep(1)

    @staticmethod
    def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        try:
            # run_forever() returns after calling loop.stop()
            loop.run_forever()
            # clean up tasks
            for task in asyncio.all_tasks(loop):
                task.cancel()
            for t in [t for t in asyncio.all_tasks(loop) if not (t.done() or t.cancelled())]:
                with suppress(asyncio.CancelledError):
                    loop.run_until_complete(t)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            loop.close()


    # send message interface

    # message encoder
    def create_msg(self, target:bytes, value: int) -> bytes:
        data_len = 3
        data = self.CODE_HEADER + data_len.to_bytes(1, 'big') + value.to_bytes(data_len, 'big')
        crc: bytes = computeCRC(data).to_bytes(2, 'big')
        return self.HEADER + target + data + crc + self.TAIL

    def send_msg(self, target:bytes, value: int) -> None:
        if self._loop is not None:
            msg = self.create_msg(target, value)
            if self._write_queue is not None:
                asyncio.run_coroutine_threadsafe(self._write_queue.put(msg), self._loop)


    # start/stop sample thread

    def start(self, host:str = '10.10.100.254', port:int = 20001,
                serial:Optional[SerialSettings] = None,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None,
                charge_handler:Optional[Callable[[], None]] = None,
                dry_handler:Optional[Callable[[], None]] = None,
                fcs_handler:Optional[Callable[[], None]] = None,
                scs_handler:Optional[Callable[[], None]] = None,
                drop_handler:Optional[Callable[[], None]] = None) -> None:
        try:
            _log.debug('start sampling')
            self._loop = asyncio.new_event_loop()
            self._thread = Thread(target=self.start_background_loop, args=(self._loop,), daemon=True)
            self._thread.start()
            # run sample task in async loop
            asyncio.run_coroutine_threadsafe(self.connect(host, port, serial,
                connected_handler, disconnected_handler,
                charge_handler, dry_handler, fcs_handler, scs_handler, drop_handler), self._loop)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

    def stop(self) -> None:
        _log.debug('stop sampling')
        # self._loop.stop() needs to be called as follows as the event loop class is not thread safe
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop = None
        # wait for the thread to finish
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        self._write_queue = None
        self.resetReadings()


def main():
    import time
    santoker = SantokerNetwork()
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
