#
# ABOUT
# Kaleido support for Artisan

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
import websockets
from pymodbus.transport.serialtransport import create_serial_connection # patched pyserial-asyncio

import logging
from typing import Final, Optional, TypedDict, Union, Callable, Dict, Tuple, TYPE_CHECKING  #for Python >= 3.9: can remove 'List' since type hints can now use the generic 'list'

if TYPE_CHECKING:
    from websockets.asyncio.client import ClientConnection # pylint: disable=unused-import

from artisanlib.atypes import SerialSettings
from artisanlib.async_comm import AsyncLoopThread

_log: Final[logging.Logger] = logging.getLogger(__name__)

class State(TypedDict, total=False):
    sid:int    # device status
    TU:str     # temperature unit
    BT:float   # bean temperature
    ET:float   # environmental temperature
    AT:float   # ambient temperature
    TS:float   # target temperature set
    HP:int     # heating power
    FC:int     # fan speed
    RC:int     # drum speed
    AH:int     # auto heating mode (0: off, 1: on)
    HS:int     # heating (0: off, 1: on)

class KaleidoPort:

    __slots__ = [ '_asyncLoopThread', '_write_queue', '_default_data_stream', '_ping_timeout', '_open_timeout', '_init_timeout',
            '_send_timeout', '_read_timeout', '_ping_retry_delay', '_reconnect_delay', 'send_button_timeout', '_single_await_var_prefix',
            '_state', '_pending_requests', '_logging' ]

    def __init__(self) -> None:
        # internals
        self._asyncLoopThread: Optional[AsyncLoopThread]     = None # the asyncio AsyncLoopThread object
        self._write_queue: Optional[asyncio.Queue[str]]      = None # the write queue

        self._default_data_stream:Final[str] = 'A0'
        self._open_timeout:Final[float] = 6      # in seconds
        self._init_timeout:Final[float] = 6      # in seconds
        self._ping_timeout:Final[float] = 0.8    # in seconds
        self._send_timeout:Final[float] = 0.4    # in seconds
        self._read_timeout:Final[float] = 4      # in seconds
        self._ping_retry_delay:Final[float] = 1  # in seconds
        self._reconnect_delay:Final[float] = 1   # in seconds

        self.send_button_timeout:Final[float] = 1.2  # in seconds

        # _state holds the last received data of the corresponding var for known all tags
        # if data for tag was not received yet, its entry is still missing
        self._state:State = {}

        # requests send via send_request with var=None use target as await_var prefixed with this string
        # such requests are awating responses with a single var/value pair (but for sid) by using those prefixed vars
        # to block request/reply processing via asyncio.Event locks until a corresponding response is received (with timeout)
        self._single_await_var_prefix = '!'

        # associates var names to pending request asyncio.Event locks
        self._pending_requests: Dict[str, asyncio.Event] = {}

        # configuration
        self._logging = False # if True device communication is logged

    def setLogging(self, b:bool) -> None:
        self._logging = b

    # getETBT triggers a 'Read Device Data' request to the machine also fetching data other than BT/ET
    def getBTET(self) -> Tuple[float,float, int]:
        if self.get_state('sid') is not None and self.get_state('TU') is not None:
            # only if initialization is complete (sid and TU received) we request data
            self.send_request('RD', self._default_data_stream, 'BT')
        bt = self.get_state('BT')
        et = self.get_state('ET')
        sid = self.get_state('sid')
        if sid is not None:
            assert isinstance(bt, float)
            assert isinstance(et, float)
            assert isinstance(sid, int)
            return bt, et, sid
        return -1, -1, 0

    def getSVAT(self) -> Tuple[float,float]:
        ts = self.get_state('TS')
        at = self.get_state('AT')
        assert isinstance(ts, float)
        assert isinstance(at, float)
        return ts, at

    def getDrumAH(self) -> Tuple[float,float]:
        rc = self.get_state('RC')
        ah = self.get_state('AH')
        assert isinstance(rc, int)
        assert isinstance(ah, int)
        return float(rc), float(ah)

    def getHeaterFan(self) -> Tuple[float,float]:
        hp = self.get_state('HP')
        fc = self.get_state('FC')
        assert isinstance(hp, int)
        assert isinstance(fc, int)
        return float(hp), float(fc)

    def resetReadings(self) -> None:
        self._state = {}

    @staticmethod
    def intVar(var:str) -> bool:
        return var in {'sid', 'HP', 'FC', 'RC', 'AH', 'HS', 'EV', 'CS'}

    @staticmethod
    def floatVar(var:str) -> bool:
        return not KaleidoPort.intVar(var) and not KaleidoPort.strVar(var)

    @staticmethod
    def strVar(var:str) -> bool:
        return var in {'TU', 'SC', 'CL', 'SN'}

# -- Kaleido PID control

    def pidON(self) -> None:
        _log.debug('Kaleido PID ON')
        if not self.get_state('AH'):
            # only if the state changed we issue the command
            self.send_msg('AH', '1') # AH message can also be send via an ON IO Command action

    def pidOFF(self) -> None:
        _log.debug('Kaleido PID OFF')
        if self.get_state('AH'):
            self.send_msg('AH', '0') # AH message can also be send via an ON IO Command action

    def setSV(self, sv:float) -> None:
        _log.debug('setSV(%s)',sv)
        if self.get_state('TS') != sv:
            self.send_msg('TS', f'{sv:0.1f}'.rstrip('0').rstrip('.'))

# -- state management


    # sync version of the corresponding get_state_async variant below
    # returns the current state of the given var or None (for sid/TU/SC/CL) and -1 (otherwise) if the state is unknown
    def get_state(self, var:str) -> Optional[Union[str,int,float]]:
        if var in self._state:
            return self._state[var] # type: ignore # TypedDict key must be a string literal
        if var in {'sid', 'TU', 'SC', 'CL', 'SN'}:
            return None
        if self.intVar(var):
            return -1
        return -1.

    # asyncio

    # returns the current state of the given var or None (for sid/TU) and -1 (otherwise) if the state is unknown
    async def get_state_async(self, var:str) -> Optional[Union[str,int,float]]:
        return self.get_state(var)

    # if single_res is True we assume the state is set from a single var/value pair response and thus we clear the var prefixed by _single_await_var_prefix
    async def set_state(self, var:str, value:str, single_res:bool) -> None:
        if self.intVar(var):
            self._state[var] = int(round(float(value))) # type: ignore # TypedDict key must be a string literal
        elif self.strVar(var):
            self._state[var] = value # type: ignore # TypedDict key must be a string literal
        else:
            try:
                self._state[var] = float(value) # type: ignore # TypedDict key must be a string literal
            except Exception: # pylint: disable=broad-except
                # if conversion to a float failed (maybe an unknown tag), we still keep the reading as original string
                self._state[var] = value # type: ignore # TypedDict key must be a string literal
        clear_var = var
        if single_res:
            # value received by a response with a single var/value pair thus we clear the prefixed variable
            clear_var = self._single_await_var_prefix + var
        await self.clear_request(clear_var)

    async def process_message(self, message:str) -> None:
        # message format '{<sid>[,<var>:<value>]*}'
        # <sid>: 0-10 (device status)
        # <var>: variable
        # <value>: new value of <var>
        if len(message)>2 and message.startswith('{') and message.endswith('}'):
            elems = message[1:-1].split(',')
            try:
                sid:int = int(round(float(elems[0])))
                await self.set_state('sid',str(sid),False)
                single_res:bool = len(elems[1:]) == 1 # true if the response contains only one var/value pair
                for el in elems[1:]:
                    comp = el.split(':')
                    if len(comp) > 1:
                        await self.set_state(comp[0], comp[1], single_res)
            except Exception as e:  # pylint: disable=broad-except
                _log.exception(e)

    async def add_request(self, var:str) -> asyncio.Event:
        if var in self._pending_requests:
            return self._pending_requests[var]
        self._pending_requests[var] = asyncio.Event()
        return self._pending_requests[var]

    async def clear_request(self, var:str) -> None:
        if var in self._pending_requests:
            # clear and remove lock
            self._pending_requests.pop(var).set()

#---- WebSocket transport

    async def ws_handle_reads(self, websocket:'ClientConnection') -> None:
        while True:
            res:Union[str,bytes] = await asyncio.wait_for(websocket.recv(), timeout=self._read_timeout)
            message:str = (str(res, 'utf-8') if isinstance(res, bytes) else res) # pyright: ignore[reportAssignmentType]
            if self._logging:
                _log.info('received: %s',message.strip())
            await self.process_message(message)

    async def ws_write(self, websocket: 'ClientConnection', message: str) -> None:
        if self._logging:
            _log.info('write: %s',message)
        await websocket.send(message)

    async def ws_handle_writes(self, websocket: 'ClientConnection', queue: 'asyncio.Queue[str]') -> None:
        message = await queue.get()
        while message != '':
            await self.ws_write(websocket, message)
            message = await queue.get()

    # write aside of the write queue and directly await response
    async def ws_write_process(self, websocket: 'ClientConnection', message: str) -> None:
        if self._logging:
            _log.info('ws_write_process(%s)',message)
        await asyncio.wait_for(self.ws_write(websocket, message), self._send_timeout)
        res:Union[str,bytes] = await asyncio.wait_for(websocket.recv(), self._ping_timeout)
        response:str = (str(res, 'utf-8') if isinstance(res, bytes) else res) # pyright: ignore[reportAssignmentType]
        # register response
        await self.process_message(response.strip())

    # to initialize the connection we first successfully ping and then set the temperature mode
    # during initialization we are not yet using the async write queue and the read handler
    async def ws_initialize(self, websocket: 'ClientConnection', mode:str) -> None:
        # ping first
        while True:
            try:
                # send PING
                await self.ws_write_process(websocket, self.create_msg('PI'))
            except asyncio.TimeoutError:
                _log.debug('ping response timeout')
            # check if response is ok
            if self.get_state('sid') is not None:
                break
            # otherwise repeat in one second
            await asyncio.sleep(self._ping_retry_delay)
        # send TU (temperature unit)
        try:
            # ping was successful, now we send the temperature mode via the queue
            await self.ws_write_process(websocket, self.create_msg('TU', mode))
        except asyncio.TimeoutError:
            _log.debug('TU response timeout')
        # send SC (start guard)
        try:
            # ping was successful, now we send the start guard via the queue
            await self.ws_write_process(websocket, self.create_msg('SC', 'AR'))
        except asyncio.TimeoutError:
            _log.debug('SC AR timeout')

    async def ws_connect(self, mode:str, host:str, port:int, path:str,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None) -> None:
        websocket = None
        while True:
            try:
                _log.debug('connecting to ws://%s:%s/%s ...',host, port, path)

                websocket = await asyncio.wait_for(websockets.connect(f'ws://{host}:{port}/{path}'), timeout=self._open_timeout)

                self._write_queue = asyncio.Queue()

                await asyncio.wait_for(self.ws_initialize(websocket, mode), timeout=self._init_timeout)

                SN:Optional[Union[str,int,float]] = await self.get_state_async('SN')
                _log.debug('connected (%s)', SN)
                if connected_handler is not None:
                    try:
                        connected_handler()
                    except Exception as e: # pylint: disable=broad-except
                        _log.error(e)

                read_handler = asyncio.create_task(self.ws_handle_reads(websocket))
                write_handler = asyncio.create_task(self.ws_handle_writes(websocket, self._write_queue))
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
                if websocket is not None:
                    try:
                        await websocket.close()
                    except Exception as e: # pylint: disable=broad-except
                        _log.error(e)

            self.resetReadings()

            if disconnected_handler is not None:
                try:
                    disconnected_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)

            await asyncio.sleep(self._reconnect_delay)


#---- Serial transport

    @staticmethod
    async def open_serial_connection(*, loop:Optional[asyncio.AbstractEventLoop] = None,
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
            loop=loop, protocol_factory=lambda: protocol, **kwargs
        )
        writer = asyncio.StreamWriter(transport, protocol, reader, loop)
        return reader, writer


    async def serial_handle_reads(self, reader: asyncio.StreamReader) -> None:
        while True:
            res = await asyncio.wait_for(reader.readline(), timeout=self._read_timeout)
            message:str = str(res, 'utf-8').strip()
            if self._logging:
                _log.info('received: %s',message)
            await self.process_message(message.strip())

    async def serial_write(self, writer: asyncio.StreamWriter, message: str) -> None:
        if self._logging:
            _log.info('write: %s',message)
        writer.write(str.encode(message))
        await asyncio.wait_for(writer.drain(), timeout=self._send_timeout)

    async def serial_handle_writes(self, writer: asyncio.StreamWriter, queue: 'asyncio.Queue[str]') -> None:
        message = await queue.get()
        while message != '':
            await self.serial_write(writer, message)
            message = await queue.get()

    # write aside of the write queue and directly await response
    async def serial_write_process(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, message: str) -> None:
        if self._logging:
            _log.info('serial_write_process(%s)',message)
        await asyncio.wait_for(self.serial_write(writer, message), self._send_timeout)
        res:bytes = await asyncio.wait_for(reader.readline(), self._ping_timeout)
        response:str = str(res, 'utf-8')
        # register response
        await self.process_message(response.strip())

    # to initialize the connection we first successfully ping and then set the temperature mode
    # during initialization we are not yet using the async write queue and the read handler
    async def serial_initialize(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, mode:str) -> None:
        while True:
            try:
                # send PING
                await self.serial_write_process(reader, writer, self.create_msg('PI'))
            except asyncio.TimeoutError:
                _log.debug('ping response timeout')
            # check if response is ok
            if self.get_state('sid') is not None:
                break
            # otherwise repeat in one second
            await asyncio.sleep(self._ping_retry_delay)
        try:
            # ping was successful, now we send the temperature mode via the queue
            await self.serial_write_process(reader, writer, self.create_msg('TU', mode))
        except asyncio.TimeoutError:
            _log.debug('TU response timeout')
        # send SC (start guard)
        try:
            # ping was successful, now we send the temperature mode via the queue
            await self.serial_write_process(reader, writer, self.create_msg('SC', 'AR'))
        except asyncio.TimeoutError:
            _log.debug('SC AR timeout')

    async def serial_connect(self, mode:str, serial:SerialSettings,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None) -> None:

        writer = None
        while True:
            try:
                _log.debug('connecting to %s@%s ...',serial['port'],serial['baudrate'])

                connect = self.open_serial_connection(
                        url=serial['port'],
                        baudrate=serial['baudrate'],
                        bytesize=serial['bytesize'],
                        stopbits=serial['stopbits'],
                        parity=serial['parity'],
                        timeout=serial['timeout'])
                # Wait for 2 seconds, then raise TimeoutError
                reader, writer = await asyncio.wait_for(connect, timeout=self._open_timeout)

                self._write_queue = asyncio.Queue()
                await asyncio.wait_for(self.serial_initialize(reader, writer, mode), timeout=self._init_timeout)

                _log.debug('connected')
                if connected_handler is not None:
                    try:
                        connected_handler()
                    except Exception as e: # pylint: disable=broad-except
                        _log.error(e)

                read_handler = asyncio.create_task(self.serial_handle_reads(reader))
                write_handler = asyncio.create_task(self.serial_handle_writes(writer, self._write_queue))
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

            await asyncio.sleep(self._reconnect_delay)


    # send message interface

    # message encoder
    # encodes given tag and value in a message respecting the expected type of the value per tag
    def create_msg(self, tag:str, value:Optional[str] = None) -> str:
        if value is None:
            return f'{{[{tag}]}}\n'
        value_encoded:str
        value_encoded = value
        if not self.strVar(tag):
            try:
                # we try to convert to integer or float with one decimal packaged within a string if possible
                # (we default to float)
                if self.floatVar(tag):
                    # integers expected, we remove decimals
                    value_encoded = f'{float(value):.0f}'
                else:
                    # floats expected, we reduce to one decimal
                    value_encoded = f'{float(value):.1f}'.rstrip('0').rstrip('.')
            except Exception:  # pylint: disable=broad-except
                # fails if value is a string like "UP" or "DW"
                pass
        return f'{{[{tag} {value_encoded}]}}\n'

    def send_msg(self, target:str, value:Optional[str] = None, timeout:Optional[float] = None) -> None:
        send_timeout = self._send_timeout
        if timeout is not None:
            send_timeout = timeout
        if self._asyncLoopThread is not None:
            msg = self.create_msg(target, value)
            if self._write_queue is not None:
                future = asyncio.run_coroutine_threadsafe(self._write_queue.put(msg), self._asyncLoopThread.loop)
                try:
                    future.result(send_timeout)
                except TimeoutError:
                    # the coroutine took too long, cancelling the task...
                    future.cancel()
                except Exception as ex: # pylint: disable=broad-except
                    _log.error(ex)

    # adds message to write queue and awaits new data for var
    async def write_await(self, message:str, var:str, await_var:str) -> Optional[str]:
        if self._write_queue is None:
            return None
        task = await self.add_request(await_var)
        await self._write_queue.put(message)
        await task.wait() # await a response containing a new value for var
        res = await self.get_state_async(var)
        return str(res)

    # <target> is the tag indicating the receiver of the <value>
    # will await new data assigned to given <var>, if <var> is not given, a response with a single <target>/value pair is awaited
    # using the target prefixed by _single_await_var_prefix as async.Event lock variable
    def send_request(self, target:str, value:Optional[str] = None, var:Optional[str] = None, timeout:Optional[float] = None) -> Optional[str]:
        send_timeout:float = self._send_timeout
        if timeout is not None:
            send_timeout = timeout
        # await_var is prefixed by _single_await_var_prefix to ensure that a response with a single <target>/value pair is awaited
        variable:str = (target if var is None else var)
        await_var:str = (self._single_await_var_prefix + target if var is None else var)
        if self._asyncLoopThread is not None:
            msg = self.create_msg(target, value)
            if self._write_queue is not None:
                task = self.write_await(msg, variable, await_var)
                future = asyncio.run_coroutine_threadsafe(task, self._asyncLoopThread.loop)
                try:
                    return future.result(send_timeout)
                except TimeoutError:
                    # the coroutine took too long, cancelling the task...
                    if self._logging:
                        _log.info('send_request timeout (msg=%s, timeout:%s)',msg.strip(),timeout)
                    future.cancel()
                except Exception as ex: # pylint: disable=broad-except
                    _log.error(ex)
        return None

    def markTP(self) -> None:
        self.send_msg('EV', '2')

    # start/stop sample thread

    # mode: temperature mode; either C or F
    # if serial settings are given, host/port are ignore and communication handled by the given serial port
    def start(self, mode:str, host:str = '127.0.0.1', port:int = 80, path:str = 'ws',
                serial:Optional[SerialSettings] = None,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None) -> None:
        try:
            _log.debug('start sampling')
            if self._asyncLoopThread is None:
                self._asyncLoopThread = AsyncLoopThread()
            # run sample task in async loop
            if serial is None:
                # WebSocket communication
                coro = self.ws_connect(mode, host, port, path,
                    connected_handler, disconnected_handler)
            else:
                coro = self.serial_connect(mode, serial,
                    connected_handler, disconnected_handler)
            asyncio.run_coroutine_threadsafe(coro, self._asyncLoopThread.loop)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

    def stop(self) -> None:
        _log.debug('stop sampling')
        # send end guard
        self.send_request('CL','AR','SN')
        del self._asyncLoopThread
        self._asyncLoopThread = None
        self._write_queue = None
        self.resetReadings()
