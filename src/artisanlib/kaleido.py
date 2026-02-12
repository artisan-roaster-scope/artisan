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
from collections.abc import Callable
from functools import partial
from typing import Final,  TypedDict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from websockets.asyncio.client import ClientConnection # pylint: disable=unused-import

from artisanlib.util import encodeLocalStrict
from artisanlib.atypes import SerialSettings, ProfileData
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

    __slots__ = [ '_asyncLoopThread', '_write_queue', '_running', '_default_data_stream', '_ping_timeout', '_open_timeout', '_init_timeout',
            '_send_timeout', '_read_timeout', '_ping_retry_delay', '_reconnect_delay', 'send_button_timeout', '_single_await_var_prefix',
            '_state', '_pending_requests', '_logging' ]

    def __init__(self) -> None:
        # internals
        self._asyncLoopThread: AsyncLoopThread|None     = None  # the asyncio AsyncLoopThread object
        self._write_queue: asyncio.Queue[str]|None      = None  # the write queue
        self._running:bool                              = False # while True we keep running the thread

        self._default_data_stream:Final[str] = 'A0'
        self._open_timeout:Final[float] = 6      # in seconds
        self._init_timeout:Final[float] = 6      # in seconds
        self._ping_timeout:Final[float] = 0.8    # in seconds
        self._send_timeout:Final[float] = 0.4    # in seconds
        self._read_timeout:Final[float] = 4      # in seconds
        self._ping_retry_delay:Final[float] = 1  # in seconds
        self._reconnect_delay:Final[float] = 0.2 # in seconds

        self.send_button_timeout:Final[float] = 1.2  # in seconds

        # _state holds the last received data of the corresponding var for known all tags
        # if data for tag was not received yet, its entry is still missing
        self._state:State = {}

        # requests send via send_request with var=None use target as await_var prefixed with this string
        # such requests are awating responses with a single var/value pair (but for sid) by using those prefixed vars
        # to block request/reply processing via asyncio.Event locks until a corresponding response is received (with timeout)
        self._single_await_var_prefix = '!'

        # associates var names to pending request asyncio.Event locks
        self._pending_requests: dict[str, asyncio.Event] = {}

        # configuration
        self._logging = False # if True device communication is logged

    def setLogging(self, b:bool) -> None:
        self._logging = b

    # getETBT triggers a 'Read Device Data' request to the machine also fetching data other than BT/ET
    def getBTET(self) -> tuple[float,float, int]:
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

    def getSVAT(self) -> tuple[float,float]:
        ts = self.get_state('TS')
        at = self.get_state('AT')
        assert isinstance(ts, float)
        assert isinstance(at, float)
        return ts, at

    def getDrumAH(self) -> tuple[float,float]:
        rc = self.get_state('RC')
        ah = self.get_state('AH')
        assert isinstance(rc, int)
        assert isinstance(ah, int)
        return float(rc), float(ah)

    def getHeaterFan(self) -> tuple[float,float]:
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
    def get_state(self, var:str) -> str|int|float|None:
        if var in self._state:
            return self._state[var] # type: ignore[literal-required, no-any-return, misc, unused-ignore] # TypedDict key must be a string literal
        if var in {'sid', 'TU', 'SC', 'CL', 'SN'}:
            return None
        if self.intVar(var):
            return -1
        return -1.

    # asyncio

    # returns the current state of the given var or None (for sid/TU/SC/CL/SN) and -1 (otherwise) if the state is unknown
    async def get_state_async(self, var:str) -> str|int|float|None:
        return self.get_state(var)

    # if single_res is True we assume the state is set from a single var/value pair response and thus we clear the var prefixed by _single_await_var_prefix
    async def set_state(self, var:str, value:str, single_res:bool) -> None:
        if self.intVar(var):
            self._state[var] = int(round(float(value))) # type: ignore[literal-required, misc, unused-ignore] # TypedDict key must be a string literal
        elif self.strVar(var):
            self._state[var] = value # type: ignore[literal-required, misc, unused-ignore] # TypedDict key must be a string literal
        else:
            try:
                self._state[var] = float(value) # type: ignore[literal-required, misc, unused-ignore] # TypedDict key must be a string literal
            except Exception: # pylint: disable=broad-except
                # if conversion to a float failed (maybe an unknown tag), we still keep the reading as original string
                self._state[var] = value # type: ignore[literal-required, misc, unused-ignore] # TypedDict key must be a string literal
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
        while self._running:
            res:str|bytes = await asyncio.wait_for(websocket.recv(), timeout=self._read_timeout)
            message:str = (str(res, 'utf-8') if isinstance(res, bytes) else res) # pyright: ignore[reportAssignmentType]
            if self._logging:
                _log.info('received: %s',message.strip())
            await self.process_message(message)

    async def ws_write(self, websocket: 'ClientConnection', message: str) -> None:
        if self._logging:
            _log.info('write: %s',message)
        await websocket.send(message)
        await asyncio.sleep(0.1)  # yield control to the event loop

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
        res:str|bytes = await asyncio.wait_for(websocket.recv(), self._ping_timeout)
        response:str = (str(res, 'utf-8') if isinstance(res, bytes) else res) # pyright: ignore[reportAssignmentType]
        # register response
        await self.process_message(response.strip())

    # to initialize the connection we first successfully ping and then set the temperature mode
    # during initialization we are not yet using the async write queue and the read handler
    async def ws_initialize(self, websocket: 'ClientConnection', mode:str) -> None:
        # ping first
        while self._running:
            try:
                # send PING
                await self.ws_write_process(websocket, self.create_msg('PI'))
            except TimeoutError:
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
        except TimeoutError:
            _log.debug('TU response timeout')
        # send SC (start guard)
        try:
            # ping was successful, now we send the start guard via the queue
            await self.ws_write_process(websocket, self.create_msg('SC', 'AR'))
        except TimeoutError:
            _log.debug('SC AR timeout')

    async def ws_connect(self, mode:str, host:str, port:int, path:str,
                connected_handler:Callable[[], None]|None = None,
                disconnected_handler:Callable[[], None]|None = None) -> None:
        while self._running:
            try:
                _log.debug('connecting to ws://%s:%s/%s ...',host, port, path)

                async for websocket in websockets.connect(f'ws://{host}:{port}/{path}', open_timeout=self._open_timeout):
                    done: set[asyncio.Task[Any]] = set()
                    pending: set[asyncio.Task[Any]] = set()
                    try:
                        self._write_queue = asyncio.Queue()
                        await asyncio.wait_for(self.ws_initialize(websocket, mode), timeout=self._init_timeout)
                        SN:str|int|float|None = await self.get_state_async('SN')
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
                    except websockets.ConnectionClosed:
                        _log.debug('reconnecting')
                        continue
                    finally:
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

            self.resetReadings()

            if disconnected_handler is not None:
                try:
                    disconnected_handler()
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)

            await asyncio.sleep(self._reconnect_delay)


#---- Serial transport

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
            loop, lambda: protocol, url, **kwargs
        )
        writer = asyncio.StreamWriter(transport, protocol, reader, loop)
        return reader, writer


    async def serial_handle_reads(self, reader: asyncio.StreamReader) -> None:
        while self._running:
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
        while self._running:
            try:
                # send PING
                await self.serial_write_process(reader, writer, self.create_msg('PI'))
            except TimeoutError:
                _log.debug('ping response timeout')
            # check if response is ok
            if self.get_state('sid') is not None:
                break
            # otherwise repeat in one second
            await asyncio.sleep(self._ping_retry_delay)
        try:
            # ping was successful, now we send the temperature mode
            await self.serial_write_process(reader, writer, self.create_msg('TU', mode))
        except TimeoutError:
            _log.debug('TU response timeout')
        # send SC (start guard)
        try:
            # ping was successful, now we send the safe guard
            await self.serial_write_process(reader, writer, self.create_msg('SC', 'AR'))
        except TimeoutError:
            _log.debug('SC AR timeout')

    async def serial_connect(self, mode:str, serial:SerialSettings,
                connected_handler:Callable[[], None]|None = None,
                disconnected_handler:Callable[[], None]|None = None) -> None:

        writer:asyncio.StreamWriter|None = None
        while self._running:
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

                if writer is not None: # pyright:ignore[reportUnnecessaryComparison] # reader is never None!
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
            except TimeoutError:
                _log.debug('connection timeout')
            except Exception as e: # pylint: disable=broad-except
                _log.error(e)
            finally:
                if self._write_queue is not None:
                    try:
                        while not self._write_queue.empty():
                            self._write_queue.get_nowait()
                            self._write_queue.task_done()
                    except Exception as e: # pylint: disable=broad-except
                        _log.error(e)
                if writer is not None:
                    try:
                        writer.transport.close()
                    except Exception as e: # pylint: disable=broad-except
                        _log.error(e)
                if writer is not None:
                    try:
                        writer.close()
                        await asyncio.wait_for(writer.wait_closed(), timeout=0.3) # this seems to always timeout!?
                    except Exception: # pylint: disable=broad-except
                        #_log.error("exception in writer close")
                        pass

            # the following is not reached on stop()
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
    def create_msg(self, tag:str, value:str|None = None) -> str:
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

    def send_msg(self, target:str, value:str|None = None, timeout:float|None = None) -> None:
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
    async def write_await(self, message:str, var:str, await_var:str, timeout:float|None = None) -> str|None:
        send_timeout:float = self._send_timeout
        if timeout is not None:
            send_timeout = timeout
        if self._write_queue is None:
            return None
        task = await self.add_request(await_var)
        await self._write_queue.put(message)
        # await a response containing a new value for var with timeout
        try:
            await asyncio.wait_for(task.wait(), send_timeout)
            return str(await self.get_state_async(var))
        except TimeoutError:
            if self._logging:
                _log.info('write_await timeout (msg=%s, timeout:%s, send_timeout:%s)',message.strip(),timeout,send_timeout)
        return None


    # <target> is the tag indicating the receiver of the <value>
    # will await new data assigned to given <var>, if <var> is not given, a response with a single <target>/value pair is awaited
    # using the target prefixed by _single_await_var_prefix as async.Event lock variable
    def send_request(self, target:str, value:str|None = None, var:str|None = None,
                timeout:float|None = None, single_request:bool = False) -> str|None:
        send_timeout:float = self._send_timeout
        if timeout is not None:
            send_timeout = timeout
        # await_var is prefixed by _single_await_var_prefix to ensure that a response with a single <target>/value pair is awaited
        variable:str = (target if var is None else var)
        await_var:str = (self._single_await_var_prefix + variable if var is None or single_request else var)
        if self._asyncLoopThread is not None:
            msg = self.create_msg(target, value)
            if self._write_queue is not None:
                task = self.write_await(msg, variable, await_var, send_timeout)
                future = asyncio.run_coroutine_threadsafe(task, self._asyncLoopThread.loop)
                try:
                    return future.result()
                except TimeoutError:
                    # the coroutine took too long, cancelling the task...
                    if self._logging:
                        _log.info('send_request timeout (msg=%s, timeout:%s, send_timeout:%s)',msg.strip(),timeout,send_timeout)
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
                serial:SerialSettings|None = None,
                connected_handler:Callable[[], None]|None = None,
                disconnected_handler:Callable[[], None]|None = None) -> None:
        try:
            # initialize data structures
            self._state = {}
            self._pending_requests = {}

            _log.debug('start sampling')
            if self._asyncLoopThread is None:
                self._asyncLoopThread = AsyncLoopThread()
            # run sample task in async loop
            self._running = True
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
        # send "end safety guard"
        self.send_request('CL','AR','SN', 2*self._send_timeout, True)
        self._running = False
        self._asyncLoopThread = None
        self._write_queue = None
        self.resetReadings()



######

# returns a dict containing all profile information contained in the given Kaleido CSV file
def extractProfileKaleidoCSV(file:str,
        etypesdefault:list[str],
        alt_etypesdefault:list[str],
        _artisanflavordefaultlabels:list[str],
        eventsExternal2InternalValue:Callable[[int],float]) -> ProfileData:
    res:ProfileData = ProfileData() # the interpreted data set

    # Initialize data list
    timex:list[float] = []  # Timeline
    temp1:list[float] = []  # ET
    temp2:list[float] = []  # BT
    BT_ror:list[float] = []  # BT RoR

    specialevents:list[int] = []        # Special event time points
    specialeventstype:list[int] = []    # Event Type (0=Fan, 1=Drum, 2=Damper, 3=Burner)
    specialeventsvalue:list[float] = []   # Event value
    specialeventsStrings:list[str] = [] # Event Description

    timeindex:list[int] = [-1, 0, 0, 0, 0, 0, 0, 0]  # Time Index: [CHARGE, DRY END, FC START, FC END, SC START, SC END, DROP, COOL]
                                            # CHARGE index init set to -1 as 0 could be an actual index used

    # Analysis Kaleido CSV File（Kaleido The file is in text format and contains multiple sections.）
    # Try multiple encodings to handle files with different character sets, especially Chinese characters
    content:str = ''
    encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    for encoding in encodings_to_try:
        try:
            with open(file, encoding=encoding) as f:
                content = f.read()
            break  # If successful, exit the loop
        except UnicodeDecodeError:
            continue
    else:
        # If all encodings fail, try with utf-8 and ignore errors
        with open(file, encoding='utf-8', errors='ignore') as f:
            content = f.read()

    # Split file content into different sections
    sections:dict[str,list[str]] = {}
    current_section:str|None = None
    lines:list[str] = content.split('\n')

    i:int = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check if it is a section tag, such as [{DATA}], [{EVENT}], [{CookDate}] ...
        if line.startswith('[{') and line.endswith('}]'):
            current_section = line[2:-2]  # Remove [{ and }]
            sections[current_section] = []
            i += 1
            continue

        # If currently in a certain section Inside, collecting content
        if current_section and line:
            sections[current_section].append(line)

        i += 1

    # Analyze basic information
    # Analyzing the baking date and time
    if 'CookDate' in sections and sections['CookDate']:
        cook_date = sections['CookDate'][0].strip() if sections['CookDate'] else ''
        if cook_date:
            # Format: 25-05-18 19:32:48
            try:
                date_part, time_part = cook_date.split(' ')
                year = f"20{date_part[:2]}"
                month = date_part[3:5]
                day = date_part[6:8]
                res['roastdate'] = f"{year}-{month}-{day}"
                res['roastisodate'] = f"{year}-{month}-{day}"
                res['roasttime'] = time_part
            except Exception: # pylint: disable=broad-except
                _log.warning('Could not parse CookDate: %s', cook_date)

    # Analyze comments/titles
    if 'Comment' in sections and sections['Comment']:
        comment_raw = sections['Comment'][0].strip() if sections['Comment'] else ''
        if comment_raw:
            # Handle encoding conversion for potential Chinese characters
            try:
                # Use encodeLocalStrict to properly handle different encodings
                res['title'] = encodeLocalStrict(comment_raw)
            except Exception: # pylint: disable=broad-except
                # Fallback to raw comment if encoding fails
                res['title'] = comment_raw

    # Parse DATA section
    if 'DATA' in sections:
        data_lines = sections['DATA']

        # First line is header
        if data_lines:
            #headers = [h.strip() for h in data_lines[0].split(',')]

            # Store previous parameter values to detect changes
            last_fan:float|None = None      # Corresponds to SM (Fan/Air) -> Fan (index 0)
            last_drum:float|None = None     # Corresponds to RL (Rotation) -> Drum (index 1)
            last_burner:float|None = None   # Corresponds to HP (Heat Power) -> Burner (index 3)

            # Prepare lists for extra device data
            sm_list:list[float] = []  # SM (Fan/Air) -> Fan %
            rl_list:list[float] = []  # RL (Rotation) -> Drum %
            hp_list:list[float] = []  # HP (Heat Power) -> Burner %
            sv_list:list[float] = []  # SV (Set Value) -> Set Value
            hpm_list:list[float] = [] # HPM (Manual/Auto mode) -> Mode (not displayed in Roast Properties Data)
            # ps_list:list[float] = []  # PS (Status) -> Status (not displayed in Roast Properties Data)

            for idx, line_raw in enumerate(data_lines[1:]):  # Skip the header row
                line = line_raw.strip()
                if line:
                    parts = line.split(',')
                    if len(parts) >= 11:  # Ensure there are enough columns
                        try:
                            # 解析数据列: Index,Time,BT,ET,RoR,SV,HPM,HP,SM,RL,PS
                            # Index = parts[0] (跳过)
                            time_ms = int(parts[1])      # Time (milliseconds)
                            bt = float(parts[2])         # BT
                            et = float(parts[3])         # ET
                            ror = float(parts[4])        # RoR
                            sv = float(parts[5])         # Set value

                            hpm_str = parts[6].strip()   # HPM (Manual/Auto Mode - M=Manual Heating, A=PID Heating Control based on SV value)
                            hp_str = parts[7].strip()    # HP (Burner)
                            sm_str = parts[8].strip()    # SM (Air damper setting)
                            rl_str = parts[9].strip()    # RL (RPM)
#                            ps_str = parts[10].strip()   # PS (Burner Status - O OR C)

                            # Conversion time (milliseconds to seconds)
                            time_sec = time_ms / 1000.0

                            # Convert each parameter value
                            hpm = hpm_str if hpm_str else 'M'  # Default to manual mode
                            hp = float(hp_str) if hp_str and hp_str not in ['0', ''] else 0.0
                            sm = float(sm_str) if sm_str and sm_str not in ['0', ''] else 0.0
                            rl = float(rl_str) if rl_str and rl_str not in ['0', ''] else 0.0
#                            ps = ps_str if ps_str else 'O'  # Default to firepower on.

                            # Add to the data list
                            timex.append(time_sec)
                            temp1.append(et)
                            temp2.append(bt)
                            # Convert ROR from C/30s to C/60s for Artisan compatibility
                            BT_ror.append(ror * 2) # Kaleido ROR is in C/30s, Artisan expects C/60s

                            # Add to extra device data lists
                            sm_list.append(sm)
                            rl_list.append(rl)
                            hp_list.append(hp)
                            sv_list.append(sv)
                            # HPM: M=Manual Heat (1), A=PID Heat Control based on SV value (0) - Kaleido machine mode, not displayed in Roast Properties Data
                            hpm_numeric = 1 if hpm == 'M' else 0
                            hpm_list.append(hpm_numeric) # HPM data not added to extra device list
                            # PS: O=Heat On (1), C=Heat Off (0) - Kaleido machine specific, not displayed in Roast Properties Data
                            # ps_numeric = 1 if ps == 'O' else 0
                            # ps_list.append(ps_numeric) - PS data not added to extra device list

                            # Detect Fan (SM - Fan/Air) changes - Map to Artisan Fan (index 0)
                            if sm != last_fan:
                                last_fan = sm
                                specialeventsvalue.append(eventsExternal2InternalValue(int(sm)))
                                specialevents.append(idx)
                                specialeventstype.append(0)  # Fan
                                specialeventsStrings.append(f'SM={int(sm)}%')

                            # Detect Drum (RL - Rotation) changes - Map to Artisan Drum (index 1)
                            if rl != last_drum:
                                last_drum = rl
                                specialeventsvalue.append(eventsExternal2InternalValue(int(rl)))
                                specialevents.append(idx)
                                specialeventstype.append(1)  # Drum
                                specialeventsStrings.append(f'RL={int(rl)}%')

                            # Detect Burner (HP - Heat Power) changes - Map to Artisan Burner (index 3)
                            if hp != last_burner:
                                last_burner = hp
                                specialeventsvalue.append(eventsExternal2InternalValue(int(hp)))
                                specialevents.append(idx)
                                specialeventstype.append(3)  # Burner
                                specialeventsStrings.append(f'HP={int(hp)}%')

                        except (ValueError, IndexError) as e:
                            # Skip unparsable lines
                            _log.warning('Could not parse data line: %s, error: %s', line, str(e))
                            continue

            # Add extra device data - Include all Kaleido parameters except HPM and PS
            if timex:  # Ensure there is data
                res['extradevices'] = [141, 139, 140, 25]  # Device IDs
                res['extraname1'] = ['{3}', 'SV', '{1}', 'RoR']
                res['extraname2'] = ['{0}', 'AT', 'AH', '']
                res['extratimex'] = [timex[:], timex[:], timex[:], timex[:]]
                res['extratemp1'] = [hp_list, sv_list, rl_list, BT_ror] # Convert ROR values to C/60s
                res['extratemp2'] = [sm_list, [0]*len(timex), hpm_list, [0]*len(timex)]
                # NOTE: assuming aw.nLCDs = 10 here:
                res['extraDelta1'] = [False, False, False, True, False, False, False, False, False, False]
                res['extraDelta2'] = [False, False, False, False, False, False, False, False, False, False]

    # Parse event timestamps and map to Artisan timeindex
    # Mapping relationship:
    # StartBeansIn -> CHARGE (timeindex[0])
    # TurntoYellow -> DRY END (timeindex[1])
    # 1stBoomStart -> FC START (timeindex[2])
    # 1stBoomEnd -> FC END (timeindex[3])
    # 2ndBoomStart -> SC START (timeindex[4])
    # 2ndBoomEnd -> SC END (timeindex[5])
    # BeansColdDown -> DROP (timeindex[6])

    event2timeindex = {
        'StartBeansIn': 0,  # CHARGE
        'TurntoYellow': 1,  # DRY END
        '1stBoomStart': 2,  # FC START
        '1stBoomEnd': 3,    # FC END
        '2ndBoomStart': 4,  # SC START
        '2ndBoomEnd': 5,    # SC END
        'BeansColdDown': 6  # DROP
    }

    def timex_diff(time:int, i:int) -> float:
        return abs(timex[i] - time)

    # Process events
    for event_name, time_idx in event2timeindex.items():
        if event_name in sections:
            event_data = sections[event_name][0] if sections[event_name] else ''
            if event_data and '@' in event_data:
                # Parse format like "170@00:00" -> temperature@time
                try:
                    time_str = event_data.split('@')[1]
                    time_parts = time_str.split(':')
                    if len(time_parts) == 2:
                        minutes = int(time_parts[0])
                        seconds = int(time_parts[1])
                        time_seconds = minutes * 60 + seconds
                        # Find closest time index
                        if timex:  # Ensure timex is not empty
                            closest_idx = min(range(len(timex)), key=partial(timex_diff, time_seconds))
                            timeindex[time_idx] = closest_idx
                except (ValueError, IndexError) as e:
                    _log.warning('Could not parse event time for %s: %s, error: %s', event_name, event_data, str(e))

    # Set basic roast information
    res['samplinginterval'] = 1.5  # Kaleido CSV sampling interval is 1.5 seconds
    res['mode'] = 'C'  # Default Celsius

    # Set roast data
    res['timex'] = timex
    res['temp1'] = temp1
    res['temp2'] = temp2

    res['timeindex'] = timeindex

    # Set special events (if exist)
    if len(specialevents) > 0:
        res['specialevents'] = specialevents
        res['specialeventstype'] = specialeventstype
        res['specialeventsvalue'] = specialeventsvalue
        res['specialeventsStrings'] = specialeventsStrings

    # Kaleido has only 3 control events, using 3 from Artisan:
    # SM (Fan/Air) -> Fan (0)
    # RL (Rotation) -> Drum (1)
    # HP (Heat Power) -> Burner (3)
    # HPM (M=Manual Heat, A=PID Heat Control based on SV value) - Kaleido machine mode, not used as Artisan control event
    # PS (Status) - Kaleido machine specific, not mapped to Artisan control event
    res['etypes'] = [encodeLocalStrict(etype) for etype in alt_etypesdefault]
    res['etypes'][2] = encodeLocalStrict(etypesdefault[2])

    # Set roaster information
    res['roastertype'] = 'Kaleido Legacy'
    res['roastersize'] = 0.1  # Default roaster size


    return res
