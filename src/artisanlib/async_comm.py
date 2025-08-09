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
# Marko Luther, 2023

import time
import logging
import asyncio

from contextlib import suppress
from threading import Thread
from pymodbus.transport.serialtransport import create_serial_connection # patched pyserial-asyncio
from typing import Final, Optional, Union, Tuple, Callable, AsyncIterator, TYPE_CHECKING


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
            self.__loop.call_soon_threadsafe(self.__loop.stop) # pyrefly: ignore[bad-argument-type] # __loop.stop() might raise exception if __loop is closed
#        self.__thread.join()
# WARNING: we don't join and expect the clients running on this thread to stop them
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
                content += await self._chunks.__anext__()
            except StopAsyncIteration:
                break

        return content

    async def _read_chunk(self, size: int) -> bytes:

        content = self._backlog
        bytes_read = len(self._backlog)

        while bytes_read < size:

            try:
                chunk = await self._chunks.__anext__()
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

    async def readuntil(self, separator:bytes = b'\n') -> bytes:
        if len(separator) != 0:
            while True:
                next_char = await self.readexactly(len(separator))
                if next_char == separator:
                    break
        return separator


class AsyncComm:

    __slots__ = [ '_asyncLoopThread', '_write_queue', '_running', '_host', '_port', '_serial', '_connected_handler', '_disconnected_handler',
                    '_verify_crc', '_logging' ]

    def __init__(self, host:str = '127.0.0.1', port:int = 8080, serial:Optional['SerialSettings'] = None,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None) -> None:
        # internals
        self._asyncLoopThread: Optional[AsyncLoopThread]       = None # the asyncio AsyncLoopThread object
        self._write_queue:  Optional[asyncio.Queue[bytes]]     = None # noqa: UP037 # quotes for Python3.8 # the write_queue
        self._running:bool                                     = False              # while true we keep running the thread

        # connection
        self._host:str = host
        self._port:int = port
        self._serial:Optional[SerialSettings] = serial

        # handlers
        self._connected_handler:Optional[Callable[[], None]] = connected_handler
        self._disconnected_handler:Optional[Callable[[], None]] = disconnected_handler

        # configuration
        self._verify_crc:bool = True  # if True the CRC of incoming messages is verified
        self._logging = False         # if True device communication is logged


    # external API

    def setVerifyCRC(self, b:bool) -> None:
        self._verify_crc = b

    def setLogging(self, b:bool) -> None:
        self._logging = b

    @property
    def async_loop_thread(self) -> Optional[AsyncLoopThread]:
        return self._asyncLoopThread


    # asyncio loop

    @staticmethod
    async def open_serial_connection(url:str, *, loop:Optional[asyncio.AbstractEventLoop] = None,
            limit:Optional[int] = None, **kwargs:Union[int,float,str]) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
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
            loop, lambda: protocol, url, **kwargs
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
#                while (message := await queue.get()) != b'':
#                    await self.write(writer, message)
                message = await queue.get()
                while message != b'':
                    await self.write(writer, message)
                    message = await queue.get()
                # on empty messages we close the connection
                writer.close()
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)
        finally:
            with suppress(asyncio.CancelledError, ConnectionResetError):
                await writer.drain()

    # if serial settings are given, the host/port settings are ignored and communication is handled by the given serial port
    async def connect(self, connect_timeout:float=5) -> None:
        writer:Optional[asyncio.StreamWriter] = None
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
                        timeout = self._serial['timeout'])
                else:
                    _log.debug('connecting to %s:%s ...', self._host, self._port)
                    connect = asyncio.open_connection(self._host, self._port)
                # Wait for 2 seconds, then raise TimeoutError
                reader, writer = await asyncio.wait_for(connect, timeout=connect_timeout)
                if reader is not None and writer is not None:
                    _log.debug('connected')
                    if self._connected_handler is not None:
                        try:
                            self._connected_handler()
                        except Exception as e: # pylint: disable=broad-except
                            _log.exception(e)
                    self._write_queue = asyncio.Queue()
                    read_handler = asyncio.create_task(self.handle_reads(reader))
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
