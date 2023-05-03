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
from websockets.exceptions import ConnectionClosed, ConnectionClosedError
import websockets.client
from contextlib import suppress
from threading import Thread
from pymodbus.client.serial_asyncio import open_serial_connection # patched pyserial-asyncio

import logging
from typing import Optional, Union, Callable, Dict, Tuple  #for Python >= 3.9: can remove 'List' since type hints can now use the generic 'list'
from typing_extensions import Final, TypedDict  # Python <=3.7

from artisanlib.types import SerialSettings

_log: Final[logging.Logger] = logging.getLogger(__name__)

class State(TypedDict, total=False):
    sid:int    # device status
    TU:str     # temperature unit
    BT:float   # bean temperature
    ET:float   # environmental temperature
    MT:float   # drum temperature
    TS:float   # target temperature set
    HP:int     # heating power
    FC:int     # fan speed
    RC:int     # drum speed
    AH:int     # auto heating mode (0: off, 1: on)

class KaleidoPort():

    __slots__ = [ '_loop', '_thread', '_write_queue', '_RDreceived', '_default_data_stream', '_ping_timeout', '_open_timeout',
            '_send_timeout', '_read_timeout', '_ping_retry_delay', '_reconnect_delay', '_state', '_pending_requests', '_logging' ]

    def __init__(self) -> None:
        # internals
        self._loop:        Optional[asyncio.AbstractEventLoop] = None # the asyncio loop
        self._thread:      Optional[Thread]                    = None # the thread running the asyncio loop
        self._write_queue: Optional['asyncio.Queue[str]']      = None # the write queue

        self._RDreceived = asyncio.Event() # async state indicating that new data was received

        self._default_data_stream:Final[str] = 'A0'
        self._open_timeout:Final[float] = 5
        self._ping_timeout:Final[float] = 0.7
        self._send_timeout:Final[float] = 0.3
        self._read_timeout:Final[float] = 4
        self._ping_retry_delay:Final[float] = 1
        self._reconnect_delay:Final[float] = 0.5

        # _state holds the last received data of the corresponding for known all tags
        # if data for tag was not received yet, there its entry is still missing
        self._state:State = {}

        # associates var names to pending request asyncio.Event locks
        self._pending_requests: Dict[str, asyncio.Event] = {}

        # configuration
        self._logging = False # if True device communication is logged

    def setLogging(self, b:bool) -> None:
        self._logging = b

    # getETBT triggers a 'Read Device Data' request to the machine also fetching data other than BT/ET
    def getBTET(self) -> Tuple[float,float]:
        if self.get_state('sid') is not None and self.get_state('TU') is not None:
            # only if initalization is complete (sid and TU received) we request data
            self.send_request('RD', self._default_data_stream, 'BT')
        bt = self.get_state('BT')
        et = self.get_state('ET')
        assert isinstance(bt, float)
        assert isinstance(et, float)
        return bt, et

    def getSVDT(self) -> Tuple[float,float]:
        ts = self.get_state('TS')
        mt = self.get_state('MT')
        assert isinstance(ts, float)
        assert isinstance(mt, float)
        return ts, mt

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
    def intVar(var):
        return var in ('sid', 'HP', 'FC', 'RC', 'AH', 'EV', 'CS')

    @staticmethod
    def floatVar(var):
        return not KaleidoPort.intVar(var) and not KaleidoPort.strVar(var)

    @staticmethod
    def strVar(var):
        return var in ['TU', 'SC', 'CL']

# -- Kaleido PID control

    def pidON(self) -> None:
#        _log.debug('Kaleido PID ON')
#        self.send_msg('AH', '1') # AH message is send via an ON IO Command action
        pass

    def pidOFF(self) -> None:
#        _log.debug('Kaleido PID OFF')
#        self.send_msg('AH', '0') # AH message is send via an ON IO Command action
        pass

    def setSV(self, sv:float) -> None:
        _log.debug('setSV(%s)',sv)
        self.send_msg('TS', f'{sv:0.1f}'.rstrip('0').rstrip('.'))

# -- state management


    # sync version of the corresponding get_state_async variant below
    # returns the current state of the given var or None (for sid/TU/SC/CL) and -1 (otherwise) if the state is unknown
    def get_state(self, var:str) -> Optional[Union[str,int,float]]:
        if var in self._state:
            return self._state[var] # type: ignore # TypedDict key must be a string literal
        if var in ['sid', 'TU', 'SC', 'CL']:
            return None
        if self.intVar(var):
            return -1
        return -1.

    # asyncio

    # returns the current state of the given var or None (for sid/TU) and -1 (otherwise) if the state is unknown
    async def get_state_async(self, var:str) -> Optional[Union[str,int,float]]:
        return self.get_state(var)

    async def set_state(self, var:str, value:str) -> None:
        if self.intVar(var):
            self._state[var] = int(round(float(value))) # type: ignore # TypedDict key must be a string literal
        elif self.strVar(var):
            self._state[var] = value # type: ignore # TypedDict key must be a string literal
        else:
            self._state[var] = float(value) # type: ignore # TypedDict key must be a string literal
        await self.clear_request(var)

    async def process_message(self, message:str) -> None:
        # message format '{<sid>[,<var>:<value>]*}'
        # <sid>: 0-10 (device status)
        # <var>: variable
        # <value>: new value of <var>
        if len(message)>2 and message.startswith('{') and message.endswith('}'):
            elems = message[1:-1].split(',')
            try:
                await self.set_state('sid',str(int(round(float(elems[0])))))
                for el in elems[1:]:
                    comp = el.split(':')
                    if len(comp) > 1:
                        await self.set_state(comp[0], comp[1])
            except Exception as e:  # pylint: disable=broad-except
                _log.error(e)

    async def add_request(self, var) -> asyncio.Event:
        if var in self._pending_requests:
            return self._pending_requests[var]
        self._pending_requests[var] = asyncio.Event()
        return self._pending_requests[var]

    async def clear_request(self, var) -> Optional[Union[str,int,float]]:
        if var in self._pending_requests:
            # clear and remove lock
            self._pending_requests.pop(var).set()
        # return current value
        return self.get_state(var)

#---- WebSocket transport

    async def ws_handle_reads(self, websocket:websockets.client.WebSocketClientProtocol) -> None:
        while True:
            res:Union[str,bytes] = await asyncio.wait_for(websocket.recv(), timeout=self._read_timeout)
            message:str = (str(res, 'utf-8') if isinstance(res, bytes) else res)
            if self._logging:
                _log.info('received: %s',message.strip())
            await self.process_message(message)

    async def ws_write(self, websocket: websockets.client.WebSocketClientProtocol, message: str) -> None:
        if self._logging:
            _log.info('write: %s',message)
        await websocket.send(message)

    async def ws_handle_writes(self, websocket: websockets.client.WebSocketClientProtocol, queue: 'asyncio.Queue[str]') -> None:
#        with suppress(asyncio.CancelledError):

        message = await queue.get()
        while message != '':
            await self.ws_write(websocket, message)
            message = await queue.get()

    # to initialize the connection we first successfully ping and then set the temperature mode
    async def ws_initialize(self, websocket: websockets.client.WebSocketClientProtocol, mode:str) -> None:
        message:str
        while True:
            try:
                # send PING
                await asyncio.wait_for(self.ws_write(websocket, self.create_msg('PI')), self._send_timeout)
                res:Union[str,bytes] = await asyncio.wait_for(websocket.recv(), self._ping_timeout)
                message = (str(res, 'utf-8') if isinstance(res, bytes) else res)
                # register response
                await self.process_message(message.strip())
            except asyncio.TimeoutError:
                _log.debug('ping response timeout')
            # check if response is ok
            if self.get_state('sid') is not None:
                break
            # otherwise repeat in one second
            await asyncio.sleep(self._ping_retry_delay)
        try:
            # ping was successfull, now we send the temperature mode via the queue
            await asyncio.wait_for(self.ws_write(websocket, self.create_msg('TU', mode)), self._send_timeout)
            # await response
            res = await asyncio.wait_for(websocket.recv(), self._ping_timeout) # with timeout
            message = (str(res, 'utf-8') if isinstance(res, bytes) else res)
            # register response
            await self.process_message(message.strip())
        except asyncio.TimeoutError:
            _log.debug('TU response timeout')

    async def ws_connect(self, mode:str, host:str, port:int, path:str,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None) -> None:

        _log.debug('connecting to %s:%s/%s ...',host,port,path)
        async for websocket in websockets.client.connect(f'ws://{host}:{port}/{path}', open_timeout=self._open_timeout):
            try:
                if connected_handler is not None:
                    try:
                        connected_handler()
                    except Exception as e: # pylint: disable=broad-except
                        _log.error(e)

                self._write_queue = asyncio.Queue()

                await self.ws_initialize(websocket, mode)

                read_handler = asyncio.create_task(self.ws_handle_reads(websocket))
                write_handler = asyncio.create_task(self.ws_handle_writes(websocket, self._write_queue))
                done, pending = await asyncio.wait([read_handler, write_handler], return_when=asyncio.FIRST_COMPLETED)

                for task in pending:
                    task.cancel()
                for task in done:
                    exception = task.exception()
                    if isinstance(exception, Exception):
                        raise exception

            except (ConnectionClosed, ConnectionClosedError):
                _log.debug('disconnected')
                self.resetReadings()
                if disconnected_handler is not None:
                    try:
                        disconnected_handler()
                    except Exception as e: # pylint: disable=broad-except
                        _log.error(e)
                continue

            except asyncio.TimeoutError:
                _log.debug('connection timeout')
            except Exception as e: # pylint: disable=broad-except
                _log.error(e)
            await asyncio.sleep(self._reconnect_delay)


#---- Serial transport

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

    # to initialize the connection we first successfully ping and then set the temperature mode
    async def serial_initialize(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, mode:str) -> None:
        while True:
            try:
                # send PING
                await asyncio.wait_for(self.serial_write(writer, self.create_msg('PI')), self._send_timeout)
                res = await asyncio.wait_for(reader.readline(), self._ping_timeout)
                # register response
                await self.process_message(str(res, 'utf-8').strip())
            except asyncio.TimeoutError:
                _log.debug('ping response timeout')
            # check if response is ok
            if self.get_state('sid') is not None:
                break
            # otherwise repeat in one second
            await asyncio.sleep(self._ping_retry_delay)
        try:
            # ping was successfull, now we send the temperature mode via the queue
            await asyncio.wait_for(self.serial_write(writer, self.create_msg('TU', mode)), self._send_timeout)
            # await response
            res = await asyncio.wait_for(reader.readline(), self._ping_timeout) # with timeout
            # register response
            await self.process_message(str(res, 'utf-8').strip())
        except asyncio.TimeoutError:
            _log.debug('TU response timeout')

    async def serial_connect(self, mode:str, serial:SerialSettings,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None) -> None:

        while True:
            try:
                _log.debug('connecting to %s@%s ...',serial['port'],serial['baudrate'])

                connect = open_serial_connection(
                        url=serial['port'],
                        baudrate=serial['baudrate'],
                        bytesize=serial['bytesize'],
                        stopbits=serial['stopbits'],
                        parity=serial['parity'],
                        timeout=serial['timeout'])
                # Wait for 2 seconds, then raise TimeoutError
                reader, writer = await asyncio.wait_for(connect, timeout=self._open_timeout)

                self._write_queue = asyncio.Queue()
                await self.serial_initialize(reader, writer, mode)

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
                writer.close()
                self.resetReadings()
                if disconnected_handler is not None:
                    try:
                        disconnected_handler()
                    except Exception as e: # pylint: disable=broad-except
                        _log.exception(e)

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
            await asyncio.sleep(self._reconnect_delay)

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
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        finally:
            loop.close()


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
        if self._loop is not None:
            msg = self.create_msg(target, value)
            if self._write_queue is not None:
                future = asyncio.run_coroutine_threadsafe(self._write_queue.put(msg), self._loop)
                try:
                    future.result(send_timeout)
                except TimeoutError:
                    # the coroutine took too long, cancelling the task...
                    future.cancel()
                except Exception as ex: # pylint: disable=broad-except
                    _log.error(ex)

    # adds message to write queue and awaits new data for var
    async def write_await(self, message:str, var:str) -> Optional[str]:
        if self._write_queue is None:
            return None
        task = await self.add_request(var)
        await self._write_queue.put(message)
        await task.wait()
        res = await self.get_state_async(var)
        return str(res)

    # <target> is the tag indicating the receiver of the <value>
    # will await new data assigned to given <var>, if <var> is not given <var> is set to <target>
    def send_request(self, target:str, value:Optional[str] = None, var:Optional[str] = None, timeout:Optional[float] = None) -> Optional[str]:
        send_timeout:float = self._send_timeout
        await_var:str
        if timeout is not None:
            send_timeout = timeout
        await_var = (target if var is None else var)
        if self._loop is not None:
            msg = self.create_msg(target, value)
            if self._write_queue is not None:
                task = self.write_await(msg, await_var)
                if task is None:
                    return None
                future = asyncio.run_coroutine_threadsafe(task, self._loop)
                try:
                    res = future.result(send_timeout)
                    return res
                except TimeoutError:
                    # the coroutine took too long, cancelling the task...
                    future.cancel()
                except Exception as ex: # pylint: disable=broad-except
                    _log.error(ex)
        return None

    # start/stop sample thread

    # mode: temperature mode; either C or F
    # if serial settings are given, host/port are ignore and communication handled by the given serial port
    def start(self, mode:str, host:str = '10.10.100.254', port:int = 20001, path:str = '',
                serial:Optional[SerialSettings] = None,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None) -> None:
        try:
            _log.debug('start sampling')
            self._loop = asyncio.new_event_loop()
            self._thread = Thread(target=self.start_background_loop, args=(self._loop,), daemon=True)
            self._thread.start()
            # run sample task in async loop
            if serial is None:
                # WebSocket communication
                coro = self.ws_connect(mode, host, port, path,
                    connected_handler, disconnected_handler)
            else:
                coro = self.serial_connect(mode, serial,
                    connected_handler, disconnected_handler)
            asyncio.run_coroutine_threadsafe(coro, self._loop)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

    def stop(self) -> None:
        _log.debug('stop sampling')
        # self._loop.stop() needs to be called as follows as the event loop class is not thread safe
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
        # wait for the thread to finish
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        self._write_queue = None
        self._loop = None
        self.resetReadings()
