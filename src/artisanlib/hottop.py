#
# ABOUT
# Hottop 2k+ support for Artisan

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

import time
import logging
import asyncio
from contextlib import suppress
from threading import Thread
from pymodbus.transport.transport_serial import create_serial_connection # patched pyserial-asyncio


from typing import Optional, Tuple, Callable, TYPE_CHECKING
from typing import Final  # Python <=3.7

if TYPE_CHECKING:
    from artisanlib.types import SerialSettings # pylint: disable=unused-import



_log: Final[logging.Logger] = logging.getLogger(__name__)


class Hottop:
    HEADER:Final[bytes] = b'\xa5\x96' # 165, 150

    SEND_INTERVAL:Final[float] = 0.5 # in seconds (should be larger than >100ms and <1s; if machine does not receive anything within 1s it ejects the beans)

    # safety cut-off BT temperature
    BTcutoff:Final[int] = 220        # 220C = 428F (was 212C/413F before)
    BTleaveControl:Final[int] = 180  # 180C = 350F; the BT below which the control can be released; above the control cannot be released to avoid sudden stop at high temperatures

    __slots__ = [ '_loop', '_thread', '_write_queue', '_bt', '_et', '_heater', '_main_fan', '_fan', '_solenoid', '_drum_motor', '_cooling_motor',
                     '_control_active', '_set_heater', '_set_fan', '_set_main_fan', '_set_solenoid', '_set_drum_motor', '_set_cooling_motor',
                     '_last_write', '_verify_crc', '_logging' ]


    def __init__(self) -> None:

        # internals
        self._loop:        Optional[asyncio.AbstractEventLoop] = None # the asyncio loop
        self._thread:      Optional[Thread]                    = None # the thread running the asyncio loop
        self._write_queue: Optional['asyncio.Queue[bytes]']    = None # the write queue

        # current readings
        self._bt:float = -1         # bean temperature in °C
        self._et:float = -1         # environmental temperature in °C
        self._heater:int = 0        # heater power in % [0-100]
        self._main_fan:int = 0      # fan speed in % [0-100]   # Hottop allows only values from 0-10!
        self._fan:int = 0           # cooling fan in % [0-100] # Hottop allows only values from 0-10!
        self._solenoid:int = 0      # 0: closed, 1: open
        self._drum_motor:int = 0    # 0: closed, 1: open
        self._cooling_motor:int = 0 # 0: closed, 1: open (stirrer)

        # control
        self._control_active = False # True while Artisan is controlling the Hottop
        # if a set value is -1 the corresponding process value is send
        self._set_heater:int = -1
        self._set_fan:int = -1
        self._set_main_fan:int = -1
        self._set_solenoid:int = -1
        self._set_drum_motor:int = -1
        self._set_cooling_motor:int = -1
        self._last_write = time.time()

        # configuration
        self._verify_crc:bool = True
        self._logging = False # if True device communication is logged


    # external configuration API
    def setVerifyCRC(self, b:bool) -> None:
        self._verify_crc = b
    def setLogging(self, b:bool) -> None:
        self._logging = b


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


    # message decoder

    def valid_message(self, message:bytearray) -> bool:
        return (len(message) == 36 and
            self.HEADER[0:2] == message[0:2] and
            (not self._verify_crc or int(message[35]) == sum(int(c) for c in message[:35]) & 0xFF))

    # https://www.oreilly.com/library/view/using-asyncio-in/9781492075325/ch04.html
    async def read_msg(self, stream: asyncio.StreamReader) -> None:
        # look for the first header byte
        message = bytearray()
        await stream.readuntil(self.HEADER[0:1])
        # check for the second header byte
        if await stream.readexactly(1) != self.HEADER[1:2]:
            return
        message.extend(self.HEADER)
        # read the remainder of the message
        message_body = await stream.readexactly(34)
        message.extend(message_body)
        if self.valid_message(message):
            if self._logging:
                _log.info('valid message received: %s', message)
            #VERSION = int(message[4])               # => 1 (first released version)
            self._heater = int(message[10])
            self._fan = int(message[11])
            self._main_fan = int(message[12]) * 10   # machine returns 0-10
            self._et = int(message[23]) * 256 + int(message[24])
            self._bt = int(message[25]) * 256 + int(message[26])
            self._solenoid = int(message[16])
            self._drum_motor = int(message[17])
            self._cooling_motor = int(message[18])
            #CHAFF_TRAY = int(message[19])
            if self._control_active:
                # safety cut
                if self.BTcutoff <= self._bt:
                    self._set_heater = 0
                    #self._set_fan = 10
                    self._set_main_fan = 10
                    self._set_solenoid = 1
                    self._set_drum_motor = 1
                    self._set_cooling_motor = 1
                if time.time() > self._last_write + self.SEND_INTERVAL:
                    self.send_control()
        elif self._logging:
            _log.info('invalid message received: %s', message)


    async def handle_reads(self, reader: asyncio.StreamReader) -> None:
        try:
            with suppress(asyncio.CancelledError):
                while not reader.at_eof():
                    await self.read_msg(reader)
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)

    async def write(self, writer: asyncio.StreamWriter, message: bytes) -> None:
        try:
            if self._logging:
                _log.info('write(%s)',message)
            writer.write(message)
            await writer.drain()
            self._last_write = time.time()
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
    async def connect(self, serial:'SerialSettings',
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None) -> None:
        writer = None
        while True:
            try:
                _log.debug('connecting to serial port: %s ...',serial['port'])
                connect = self.open_serial_connection(
                    url=serial['port'],
                    baudrate=serial['baudrate'],
                    bytesize=serial['bytesize'],
                    stopbits=serial['stopbits'],
                    parity=serial['parity'],
                    timeout=serial['timeout'])
                # Wait for 2 seconds, then raise TimeoutError
                reader, writer = await asyncio.wait_for(connect, timeout=2)
                _log.debug('connected')
                if connected_handler is not None:
                    try:
                        connected_handler()
                    except Exception as e: # pylint: disable=broad-except
                        _log.exception(e)
                self._write_queue = asyncio.Queue()
                read_handler = asyncio.create_task(self.handle_reads(reader))
                write_handler = asyncio.create_task(self.handle_writes(writer, self._write_queue))
                done, pending = await asyncio.wait([read_handler, write_handler], return_when=asyncio.FIRST_COMPLETED)

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
    def start_background_loop(loop: asyncio.AbstractEventLoop, disconnected_handler:Optional[Callable[[], None]] = None) -> None:
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
            if disconnected_handler is not None:
                try:
                    disconnected_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            loop.close()


    # send message interface

    # prefers set_value, and returns get_value if set_value is -1. If both are -1, returns 0
    @staticmethod
    def newValue(set_value:int, get_value:int) -> int:
        if set_value != -1:
            return set_value
        if get_value != -1:
            return get_value
        return 0

    # message encoder
    def create_msg(self) -> bytes:
        cmd = bytearray([0x00]*36)
        cmd[0] = 0xA5
        cmd[1] = 0x96
        cmd[2] = 0xB0
        cmd[3] = 0xA0
        cmd[4] = 0x01
        cmd[5] = 0x01
        cmd[6] = 0x24
        cmd[10] = self.newValue(self._set_heater, self._heater)
        cmd[11] = int(round(self.newValue(self._set_fan, self._fan) / 10.))
        cmd[12] = int(round(self.newValue(self._set_main_fan, self._main_fan) / 10.))
        cmd[16] = self.newValue(self._set_solenoid, self._solenoid)
        cmd[17] = self.newValue(self._set_drum_motor, self._drum_motor)
        cmd[18] = self.newValue(self._set_cooling_motor, self._cooling_motor)
        cmd[35] = sum(list(cmd[:35])) & 0xFF # checksum
        return bytes(cmd)

    def send_control(self) -> None:
        if self._loop is not None:
            msg = self.create_msg()
            if self._write_queue is not None:
                asyncio.run_coroutine_threadsafe(self._write_queue.put(msg), self._loop)

    # start/stop sample thread

    def start(self, serial:'SerialSettings',
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None) -> None:
        try:
            _log.debug('start sampling')
            self._loop = asyncio.new_event_loop()
            self._thread = Thread(target=self.start_background_loop, args=(self._loop,disconnected_handler), daemon=True)
            self._thread.start()
            # run sample task in async loop
            asyncio.run_coroutine_threadsafe(self.connect(serial,
                connected_handler, disconnected_handler), self._loop)
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


    # External Interface

    def takeHottopControl(self) -> bool:
        if self._bt <= self.BTcutoff:
            self._control_active = True
            return True
        return False

    def releaseHottopControl(self) -> bool:
        if self._bt < self.BTleaveControl:
            self._control_active = False
            return True
        return False

    def getState(self) -> Tuple[float, float, int, int]:
        return self._bt, self._et, self._heater, self._main_fan

    def resetReadings(self) -> None:
        self._bt = -1
        self._et = -1
        self._heater = 0
        self._main_fan = 0
        self._fan = 0
        self._solenoid = 0
        self._drum_motor = 0
        self._cooling_motor = 0

    # heater : int(0-100)
    # fan, main_fan : int(0-100) (will be converted to the internal int(0-10))
    # solenoid, drum_motor, cooling_motor : bool (will be converted to the internal 0 or 1)
    # all parameters are optional and default to None (meanging: don't change value)
    def setHottop(self, heater:Optional[int]=None, fan:Optional[int]=None, main_fan:Optional[int]=None,
            solenoid:Optional[bool]=None, drum_motor:Optional[bool]=None, cooling_motor:Optional[bool]=None) -> None:
        _log.debug('setHottop(heater: %s, fan: %s, main_fan: %s, solenoid: %s, drum_motor: %s, cooling_motor: %s)', heater, fan, main_fan, solenoid, drum_motor, cooling_motor)
        if self._control_active:
            if heater is not None:
                self._set_heater = max(0,min(heater,100))
            if fan is not None:
                self._set_fan = max(0,min(fan,100))
            if main_fan is not None:
                self._set_main_fan = max(0,min(main_fan,100))
            if solenoid is not None:
                self._set_solenoid = (1 if solenoid else 0)
            if drum_motor is not None:
                self._set_drum_motor = (1 if drum_motor else 0)
            if cooling_motor is not None:
                self._set_cooling_motor = (1 if cooling_motor else 0)

def main():
    hottop = Hottop()
    hottop_serial:'SerialSettings' = {
        'port': '/dev/slave',
        'baudrate': 9600, # 115200
        'bytesize': 8,
        'stopbits': 1,
        'parity': 'N',
        'timeout': 0.3}
    hottop.start(hottop_serial)
    for _ in range(4):
        hottop.setHottop(heater=35) # set power to 35%
        time.sleep(1)
        print('state',hottop.getState())
        time.sleep(1)
    hottop.stop()
    time.sleep(1)
    #print('thread alive?',hottop._thread.is_alive())

if __name__ == '__main__':
    main()
