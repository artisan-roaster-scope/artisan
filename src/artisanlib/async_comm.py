#
# ABOUT
# Generic asyncio communication for Artisan

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
# Marko Luther, 2026

import os
import sys
import time
import logging
import serial as pyserial
import asyncio
import platform

from contextlib import suppress
from threading import Thread
from pymodbus.transport.serialtransport import SerialTransport # patched pyserial-asyncio
from collections.abc import Callable, AsyncIterator
from typing import Final, Any, TYPE_CHECKING


if TYPE_CHECKING:
    from artisanlib.atypes import SerialSettings # pylint: disable=unused-import

_log: Final[logging.Logger] = logging.getLogger(__name__)


# An AsyncLoopThread instance holds a thread and an asyncio loop running in that thread.
# On object deletion the loop is terminated and the thread is ended.
class AsyncLoopThread:

    __slots__ = [ '__loop', '__thread' ]

    def __init__(self) -> None:

        def start_background_loop(loop:asyncio.AbstractEventLoop) -> None:
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
            except Exception:  # pylint: disable=broad-except
                pass
            finally:
                loop.close()

        self.__loop:asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.__thread:Thread = Thread(target=start_background_loop, args=(self.__loop,), daemon=True)
        self.__thread.start()

    def __del__(self) -> None:
        if not self.__loop.is_closed():
            self.__loop.call_soon_threadsafe(self.__loop.stop)
#        self.__thread.join()
# WARNING: we don't join and expect the clients running on this thread to stop themself
# (using self._running) to finally get rid of this thread to prevent hangs

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self.__loop


class AsyncIterable:

    _queue: 'asyncio.Queue[bytes]' # type Queue is not subscriptable in Python <3.9 thus it is quoted

    def __init__(self, queue:'asyncio.Queue[bytes]') -> None:
        self._queue = queue

    def __aiter__(self) -> 'AsyncIterable':
        return self

    async def __anext__(self) -> bytes:
        return await self._queue.get()


class IteratorReader:

    _chunks: AsyncIterator[bytes]
    _backlog: bytes

    def __init__(self, chunks: AsyncIterator[bytes]):
        self._chunks = chunks
        self._backlog = b''

    async def _read_until_end(self) -> bytes:

        content = self._backlog
        self._backlog = b''

        while True:
            try:
                content += await anext(self._chunks)
            except StopAsyncIteration:
                break

        return content

    async def _read_chunk(self, size: int) -> bytes:

        content = self._backlog
        bytes_read = len(self._backlog)

        while bytes_read < size:

            try:
                chunk = await anext(self._chunks)
            except StopAsyncIteration:
                break

            content += chunk
            bytes_read += len(chunk)

        self._backlog = content[size:]
        return content[:size]

    async def readexactly(self, size: int = -1) -> bytes:
        if size > 0:
            return await self._read_chunk(size)
        if size == -1:
            return await self._read_until_end()
        return b''

    # returns only the data incl. the final separator
    async def readuntil(self, separator:bytes = b'\n') -> bytes:
        res = b''
        if len(separator) != 0:
            while True:
                next_char = await self.readexactly(len(separator))
                res += next_char
                if next_char == separator:
                    break
        return res


# clone from pymodbus/serialtransport.py extended by parameter 'do_not_open' (default False) which prevents opening the created serial port if set to True
class ArtisanSerialTransport(SerialTransport):
    """An asyncio serial transport."""

    force_poll: bool = os.name == 'nt'
    # async_loop: asyncio.AbstractEventLoop

    def __init__(self, # pylint: disable=super-init-not-called
            loop:asyncio.AbstractEventLoop,
            protocol:asyncio.Protocol,
            url:str,
            baudrate:int,
            bytesize:int,
            parity:str,
            stopbits:float,
            timeout:float,
            do_not_open:bool = False) -> None:
        """Initialize."""
        # we call __init__ of async.Transport, but NOT that of pymodbus SerialTransport which would open the port
        asyncio.Transport.__init__(self) # pylint: disable=non-parent-init-called
        if 'serial' not in sys.modules:
            raise RuntimeError(
                'Serial client requires pyserial '
                'Please install with "pip install pyserial" and try again.'
            )
        self.async_loop = loop
        self.intern_protocol: asyncio.BaseProtocol = protocol
        self.sync_serial = pyserial.serial_for_url(url, exclusive=True,
            baudrate=baudrate, bytesize=bytesize, parity=parity, stopbits=stopbits, timeout=timeout,
            do_not_open=do_not_open)
        self.intern_write_buffer: list[bytes] = []
        self.poll_task: asyncio.Task[Any] | None = None
        self._poll_wait_time = 0.0005
        self.sync_serial.timeout = 0
        self.sync_serial.write_timeout = 0


async def create_serial_connection(
    loop:asyncio.AbstractEventLoop,
    protocol_factory:Callable[[], asyncio.Protocol],
    url:str,
    baudrate:int,
    bytesize:int,
    parity:str,
    stopbits:float,
    timeout:float,
    clear_HUPCL:bool = False # if True, try to prevent toggling the RTS/DTR lines on opening the port to prevent to trigger a reboot on the connected device (ESP32/Orbiter)
) -> tuple[asyncio.Transport, asyncio.BaseProtocol]:
    """Create a connection to a new serial port instance."""
    protocol = protocol_factory()
    transport = ArtisanSerialTransport(loop, protocol, url,
                    baudrate,
                    bytesize,
                    parity,
                    stopbits,
                    timeout,
                    clear_HUPCL) # prevent opening the serial port on creation if clear_HUPCL is set
    ####

    # first we need to clear HUPCL, Hang Up on Close, (UNIX) or clear RTS/DTR (Windows) so the device will not reboot based on RTS and/or DTR
    # stty -F /dev/ttyACM0 -hupcl to clear the HUPCL (Hang Up on Close) flag, preventing the reset when the port closes or reopens.
    # see https://github.com/pyserial/pyserial/issues/124
    # and https://github.com/npat-efault/picocom/blob/master/lowerrts.md
    if clear_HUPCL:
        # the transport serial port is not open yet in this case
        try:
            if platform.system() == 'Linux': # seems not to resolve the issue on macOS
                import termios # pylint: disable=C0415,E0401
                # the following might hang on macOS for non-callup devices
                #url = url.replace('/dev/tty.','/dev/cu.')
                with open(url, encoding='utf8') as f:
                    attrs = termios.tcgetattr(f)
                    attrs[2] = attrs[2] & ~termios.HUPCL
                    termios.tcsetattr(f, termios.TCSAFLUSH, attrs)
                    f.close()
                time.sleep(0.1)
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)
        try:
            # for Windows the following should be enough (and for the other platforms it should not harm)
            transport.sync_serial.dtr = False
            transport.sync_serial.rts = False
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)

    # in any case we open the serial port
    if not transport.sync_serial.is_open:
        transport.sync_serial.open()

    # and if clear_HUPCL, we immediately set the dtr/rts again
    if clear_HUPCL:
        try:
            transport.sync_serial.dtr = False
            transport.sync_serial.rts = False
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)

    loop.call_soon(transport.setup)
    return transport, protocol

class AsyncComm:

    __slots__ = [ '_asyncLoopThread', '_write_queue', '_running', '_serialize_write_lock', '_host', '_port', '_serial', '_connected_handler', '_disconnected_handler',
                    '_verify_crc', '_logging', '_send_timeout' ]

    def __init__(self, host:str = '127.0.0.1', port:int = 8080, serial:'SerialSettings|None' = None,
                connected_handler:Callable[[], None]|None = None,
                disconnected_handler:Callable[[], None]|None = None) -> None:
        # internals
        self._asyncLoopThread: AsyncLoopThread|None       = None # the asyncio AsyncLoopThread object
        self._write_queue:  asyncio.Queue[bytes]|None     = None # noqa: UP037 # quotes for Python3.8 # the write_queue
        self._running:bool                                = False              # while true we keep running the thread

        # lock to serialize write_await calls to realize request/response patterns
        self._serialize_write_lock:asyncio.Lock = asyncio.Lock()

        # connection
        self._host:str = host
        self._port:int = port
        self._serial:SerialSettings|None = serial

        # handlers
        self._connected_handler:Callable[[], None]|None = connected_handler
        self._disconnected_handler:Callable[[], None]|None = disconnected_handler

        # configuration
        self._verify_crc:bool = True  # if True the CRC of incoming messages is verified
        self._logging = False         # if True device communication is logged
        self._send_timeout:Final[float] = 0.6    # in seconds


    # external API

    def setVerifyCRC(self, b:bool) -> None:
        self._verify_crc = b

    def setLogging(self, b:bool) -> None:
        self._logging = b

    @property
    def async_loop_thread(self) -> AsyncLoopThread|None:
        return self._asyncLoopThread


    # asyncio loop

    @staticmethod
    async def open_serial_connection(url:str, *, loop:asyncio.AbstractEventLoop|None = None,
            limit:int|None = None, **kwargs:int|float|str) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
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
            loop, lambda: protocol, url, **kwargs # type: ignore[arg-type]
        )
        writer = asyncio.StreamWriter(transport, protocol, reader, loop)
        return reader, writer


    # to be overwritten by the subclass

    def reset_readings(self) -> None:
        pass

    async def read_msg(self, stream: asyncio.StreamReader) -> None:
        pass


    # reads

    async def handle_reads(self, reader: asyncio.StreamReader) -> None:
        try:
            with suppress(asyncio.CancelledError):
                while not reader.at_eof():
                    await self.read_msg(reader)
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)

    # writes

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
                while (message := await queue.get()) != b'':
                    await self.write(writer, message)
#                message = await queue.get()
#                while message != b'':
#                    await self.write(writer, message)
#                    message = await queue.get()
                # on empty messages we close the connection
                writer.close()
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)
        finally:
            with suppress(asyncio.CancelledError, ConnectionResetError):
                await writer.drain()

    # if serial settings are given, the host/port settings are ignored and communication is handled by the given serial port
    async def connect(self, connect_timeout:float=5) -> None:
        writer:asyncio.StreamWriter|None = None
        while self._running:
            try:
                if self._serial is not None:
                    _log.debug('connecting to serial port: %s ...', self._serial['port'])
                    connect = self.open_serial_connection(
                        url = self._serial['port'],
                        baudrate = self._serial['baudrate'],
                        bytesize = self._serial['bytesize'],
                        stopbits = self._serial['stopbits'],
                        parity = self._serial['parity'],
                        timeout = self._serial['timeout'],
                        clear_HUPCL = self._serial['clear_HUPCL'])
                else:
                    _log.debug('connecting to %s:%s ...', self._host, self._port)
                    connect = asyncio.open_connection(self._host, self._port)
                # Wait for 2 seconds, then raise TimeoutError
                reader, writer = await asyncio.wait_for(connect, timeout=connect_timeout)
                if writer is not None: # pyright:ignore[reportUnnecessaryComparison] # reader is of type asyncio.streams.StreamReader and thus never None
                    self._write_queue = asyncio.Queue()
                    read_handler = asyncio.create_task(self.handle_reads(reader))
                    write_handler = asyncio.create_task(self.handle_writes(writer, self._write_queue))
                    _log.debug('connected')
                    if self._connected_handler is not None:
                        try:
                            self._connected_handler()
                        except Exception as e: # pylint: disable=broad-except
                            _log.exception(e)
                    done, pending = await asyncio.wait([read_handler, write_handler], return_when=asyncio.FIRST_COMPLETED)
                    _log.debug('disconnected')

                    for task in pending:
                        task.cancel()
                    for task in done:
                        exception = task.exception()
                        if isinstance(exception, Exception):
                            raise exception

            except TimeoutError:
                _log.debug('connection timeout')
            except Exception as e: # pylint: disable=broad-except
                _log.error(e)
            finally:
                if writer is not None:
                    try:
                        writer.close()
                        await asyncio.wait_for(writer.wait_closed(), timeout=0.3)
                    except Exception as e: # pylint: disable=broad-except
                        _log.error(e)

            self.reset_readings()
            if self._disconnected_handler is not None:
                try:
                    self._disconnected_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)

            await asyncio.sleep(0.5)

    def send(self, message:bytes) -> None:
        if self.async_loop_thread is not None and self._write_queue is not None:
            asyncio.run_coroutine_threadsafe(self._write_queue.put(message), self.async_loop_thread.loop)

    # adds message to write queue and awaits new data which is assumed to event.set() in read_msg() once received
    # if serialize is set, writes are serialized such that at any moment only one response is awaited using the given event
    # ensuring minimum delay of 'delay' between writes (in seconds)
    # returns True on success and False on timeout
    # on return the event is always cleared
    async def write_await(self, message:bytes, event:asyncio.Event, send_timeout:float, serialize:bool, delay:float) -> bool:
        if self._write_queue is None:
            return False
        try:
            if serialize:
                was_writing = self._serialize_write_lock.locked() # remember if writing was in progress
                try:
                    await asyncio.wait_for(self._serialize_write_lock.acquire(), send_timeout)
                except TimeoutError:
                    pass
                if was_writing and delay > 0: # only if writing was in progress we add a delay before writing
                    await asyncio.sleep(delay)
            # write out the message
            await self._write_queue.put(message)
            # await a response with timeout indicated by the event being set
            try:
                await asyncio.wait_for(event.wait(), send_timeout)
                return True
            except TimeoutError:
                if self._logging:
                    _log.info('write_await (msg=%s, send_timeout:%s)', message.strip(), send_timeout)
            return False
        finally:
            # in any case, clear the event belonging to this message
            event.clear()
            if serialize:
                # release the serializing write lock
                self._serialize_write_lock.release()


    # returns True if message was sent successfully
    def send_await(self, message:bytes, event:asyncio.Event, timeout:float|None = None, serialize:bool = False, delay:float = 0) -> bool:
        if self.async_loop_thread is not None and self._write_queue is not None:
            send_timeout:float = self._send_timeout
            if timeout is not None:
                send_timeout = timeout
            task = self.write_await(message, event, send_timeout, serialize, delay)
            if self._asyncLoopThread is not None:
                future = asyncio.run_coroutine_threadsafe(task, self._asyncLoopThread.loop)
                try:
                    return future.result()
                except TimeoutError:
                    # the coroutine took too long, cancelling the task...
                    if self._logging:
                        _log.info('send_request timeout (msg=%s, timeout:%s, send_timeout:%s)',message,timeout,send_timeout)
                    future.cancel()
                except Exception as ex: # pylint: disable=broad-except
                    _log.error(ex)
        return False



    # start/stop sample thread

    def start(self, connect_timeout:float=5) -> None:
        try:
            _log.debug('start sampling')
            if self._asyncLoopThread is None:
                self._running = True
                self._asyncLoopThread = AsyncLoopThread()
                # run sample task in async loop
                asyncio.run_coroutine_threadsafe(self.connect(connect_timeout), self._asyncLoopThread.loop)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

    def stop(self) -> None:
        _log.debug('stop sampling')
        self._running = False
        self.send(b'') # we write an empty byte to stop the writer and disconnect
        time.sleep(0.3) # wait a moment to allow the loop to disconnect
        self._asyncLoopThread = None
        self._write_queue = None
        self.reset_readings()
