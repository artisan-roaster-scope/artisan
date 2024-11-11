#
# ABOUT
# WebSocket support for Artisan

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
# Marko Luther, 2024

import sys
import random
import json
import logging
import asyncio
import websockets
import contextlib
import socket

from contextlib import suppress
from threading import Thread
from typing import Final, Optional, Union, Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    from websockets.asyncio.client import ClientConnection # pylint: disable=unused-import

try:
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib import __version__

_log: Final[logging.Logger] = logging.getLogger(__name__)

class wsport:

    __slots__ = [ 'aw', '_loop', '_thread', '_write_queue', 'default_host', 'host', 'port', 'path', 'machineID', 'lastReadResult', 'channels', 'readings', 'tx',
                    'channel_requests', 'channel_nodes', 'channel_modes', 'connect_timeout', 'request_timeout', 'compression',
                    'reconnect_interval', 'ping_interval', 'ping_timeout', 'id_node', 'machine_node',
                    'command_node', 'data_node', 'pushMessage_node', 'request_data_command', 'charge_message', 'drop_message', 'addEvent_message', 'event_node',
                    'DRY_node', 'FCs_node', 'FCe_node', 'SCs_node', 'SCe_node', 'STARTonCHARGE', 'OFFonDROP', 'open_event', 'pending_events',
                    'ws', 'wst' ]

    def __init__(self, aw:'ApplicationWindow') -> None:
        self.aw = aw

        # internals
        self._loop:        Optional[asyncio.AbstractEventLoop] = None # the asyncio loop
        self._thread:      Optional[Thread]                    = None # the thread running the asyncio loop
        self._write_queue: Optional[asyncio.Queue[str]]    = None # the write queue

        # connects to "ws://<host>:<port>/<path>"
        self.default_host:Final[str] = '127.0.0.1'
        self.host:str = self.default_host # the TCP host
        self.port:int = 80          # the TCP port
        self.path:str = 'WebSocket' # the ws path
        self.machineID:int = 0
        self.compression:bool = True # activatesd/deactivates 'deflate' compression

        self.lastReadResult:Optional[Dict[str,Any]] = None # this is set by eventaction following some custom button/slider Modbus actions with "read" command

        self.channels:Final[int] = 10 # maximal number of WebSocket channels

        # WebSocket data
        self.tx:float = 0 # timestamp as epoch of last read
        self.readings:List[float] = [-1]*self.channels

        self.channel_requests:List[str] = ['']*self.channels
        self.channel_nodes:List[str] = ['']*self.channels
        self.channel_modes:List[int] = [0]*self.channels # temp mode is an int here, 0:__,1:C,2:F

        # configurable via the UI:
        self.connect_timeout:float = 4    # in seconds
        self.request_timeout:float = 0.5  # in seconds
        self.reconnect_interval:float = 2 # in seconds # not used for now
        # not configurable via the UI:
        self.ping_interval:float = 0      # in seconds; if 0 pings are not send automatically
        self.ping_timeout:Optional[float] = None    # in seconds

        # JSON nodes
        self.id_node:str = 'id'
        self.machine_node:str = 'roasterID'
        self.command_node:str = 'command'
        self.data_node:str = 'data'
        self.pushMessage_node:str = 'pushMessage'

        # commands
        self.request_data_command:str = 'getData'

        # push messages
        self.charge_message:str = 'startRoasting'
        self.drop_message:str = 'endRoasting'
        self.addEvent_message:str = 'addEvent'

        self.event_node:str = 'event'
        self.DRY_node:str = 'colorChangeEvent'
        self.FCs_node:str = 'firstCrackBeginningEvent'
        self.FCe_node:str = 'firstCrackEndEvent'
        self.SCs_node:str = 'secondCrackBeginningEvent'
        self.SCe_node:str = 'secondCrackEndEvent'

        # flags
        self.STARTonCHARGE:bool = False
        self.OFFonDROP:bool = False

        self.open_event:Optional[asyncio.Event] = None # an event set on connecting
        self.pending_events:Dict[int, Union[asyncio.Event, Dict[str,Any]]] = {} # message ids associated with pending asyncio.Event object or result


    # request event handling

    async def registerRequest(self, message_id:int) -> asyncio.Event:
        e = asyncio.Event()
        self.pending_events[message_id] = e
        return e

    def removeRequestResponse(self, message_id:int) -> None:
        del self.pending_events[message_id]

    # replace the request event by its result
    async def setRequestResponse(self, message_id:int, v:Dict[str, Any]) -> None:
        if message_id in self.pending_events:
            pe = self.pending_events[message_id]
            if isinstance(pe, asyncio.Event):
                pe.set() # unblock
                self.removeRequestResponse(message_id)
                self.pending_events[message_id] = v

    # returns the response received for request with id or None
    def getRequestResponse(self, message_id:int) -> Optional[Dict[str,Any]]:
        if message_id in self.pending_events:
            v = self.pending_events[message_id]
            del self.pending_events[message_id]
            if not isinstance(v, asyncio.Event):
                return v
        return None


    async def producer(self) -> Optional[str]:
        if self._write_queue is None:
            return None
        return await self._write_queue.get()

    async def consumer(self, message:str) -> None:
        j = json.loads(message)
        if self.aw.seriallogflag:
            self.aw.addserial(f'wsport onMessage(): {j}')
        if self.id_node in j:
            await self.setRequestResponse(j[self.id_node],j)
        elif self.pushMessage_node != ''  and self.pushMessage_node in j:
            pushMessage = j[self.pushMessage_node]
            if self.aw.seriallogflag:
                self.aw.addserial(f'wsport pushMessage {pushMessage} received')
            if self.charge_message != '' and pushMessage == self.charge_message:
                if self.aw.seriallogflag:
                    self.aw.addserial('wsport CHARGE message received')
                delay = 0 # in ms
                if self.STARTonCHARGE and not self.aw.qmc.flagstart:
                    # turn recording on
                    self.aw.qmc.toggleRecorderSignal.emit()
                    if self.aw.seriallogflag:
                        self.aw.addserial('wsport toggleRecorder signal sent')
                if self.aw.qmc.timeindex[0] == -1:
                    if self.aw.qmc.flagstart:
                        # markCHARGE without delay
                        delay = 1
                    else:
                        # markCharge with a delay waiting for the recorder to be started up
                        delay = self.aw.qmc.delay * 2 # we delay the markCharge action by 2 sampling periods
                    self.aw.qmc.markChargeDelaySignal.emit(delay)
                    if self.aw.seriallogflag:
                        self.aw.addserial(f'wsport markCHARGE() with delay={delay} signal sent')
            elif self.drop_message != '' and pushMessage == self.drop_message:
                if self.aw.seriallogflag:
                    self.aw.addserial('wsport message: DROP')
                if self.aw.qmc.flagstart and self.aw.qmc.timeindex[6] == 0:
                    # markDROP
                    self.aw.qmc.markDropSignal.emit(False)
                    if self.aw.seriallogflag:
                        self.aw.addserial('wsport markDROP signal sent')
                if self.OFFonDROP and self.aw.qmc.flagstart:
                    # turn Recorder off after two sampling periods
                    delay = self.aw.qmc.delay * 2 # we delay the turning OFF action by 2 sampling periods
                    await asyncio.sleep(delay)
                    self.aw.qmc.toggleMonitorSignal.emit()
                    if self.aw.seriallogflag:
                        self.aw.addserial('wsport toggleMonitor signal sent')
            elif self.addEvent_message != '' and pushMessage == self.addEvent_message:
                if self.aw.qmc.flagstart and self.data_node in j:
                    data = j[self.data_node]
                    if self.event_node in data:
                        if self.aw.seriallogflag:
                            self.aw.addserial(f'wsport message: addEvent({data[self.event_node]}) received')
                        if self.aw.qmc.timeindex[1] == 0 and data[self.event_node] == self.DRY_node:
                            # addEvent(DRY) received
                            if self.aw.seriallogflag:
                                self.aw.addserial('wsport message: addEvent(DRY) processed')
                            self.aw.qmc.markDRYSignal.emit(False)
                        elif self.aw.qmc.timeindex[2] == 0 and data[self.event_node] == self.FCs_node:
                            # addEvent(FCs) received
                            if self.aw.seriallogflag:
                                self.aw.addserial('wsport message: addEvent(FCs) processed')
                            self.aw.qmc.markFCsSignal.emit(False)
                        elif self.aw.qmc.timeindex[3] == 0 and data[self.event_node] == self.FCe_node:
                            # addEvent(FCe) received
                            if self.aw.seriallogflag:
                                self.aw.addserial('wsport message: addEvent(FCe) processed')
                            self.aw.qmc.markFCeSignal.emit(False)
                        elif self.aw.qmc.timeindex[4] == 0 and data[self.event_node] == self.SCs_node:
                            # addEvent(SCs) received
                            if self.aw.seriallogflag:
                                self.aw.addserial('wsport message: addEvent(SCs) processed')
                            self.aw.qmc.markSCsSignal.emit(False)
                        elif self.aw.qmc.timeindex[5] == 0 and data[self.event_node] == self.SCe_node:
                            # addEvent(SCe) received
                            if self.aw.seriallogflag:
                                self.aw.addserial('wsport message: addEvent(SCe) processed')
                            self.aw.qmc.markSCeSignal.emit(False)
                    elif self.aw.seriallogflag:
                        self.aw.addserial(f'wsport message: addEvent({data})')
                elif self.aw.seriallogflag:
                    self.aw.addserial('wsport message: addEvent() received and ignored. Not recording.')

            # set burner: { "pushMessage": "setBurnerCapacity", "data": { "burnercapacity": 51 } }
            # name of current roast set: {"pushMessage": "setRoastingProcessName", "data": { "name": "Test roast 123" }}
            # note of current roast set: {"pushMessage": "setRoastingProcessNote", "data": { "note": "A test comment" }}
            # fill weight of current roast set: {"pushMessage": "setRoastingProcessFillWeight", "data": { "fillWeight": 12 }}


    async def split_and_consume_message(self, message:str) -> None:
        # a message may contain several lines of JSON data separated by \n, like in "{'a':1}\n{'b':2}\n"
        for m in message.strip().split('\n'):
            single_message = m.strip()
            if single_message != '':
                await self.consumer(single_message)

    async def consumer_handler(self, websocket:'ClientConnection') -> None:
        async for message in websocket:
            if isinstance(message, str):
                await self.split_and_consume_message(message)
            elif isinstance(message, bytes):
                await self.split_and_consume_message(message.decode('utf-8'))


    async def producer_handler(self, websocket:'ClientConnection') -> None:
        while True:
            message = await self.producer()
            if message is not None:
                await websocket.send(message)


    # if serial settings are given, host/port are ignore and communication is handled by the given serial port
    async def connect(self) -> None:
        if self.aw.qmc.device_logging:
            logging.getLogger('websockets').setLevel(logging.DEBUG)
        else:
            logging.getLogger('websockets').setLevel(logging.ERROR)

        while True:
            try:
                if self.port == 80:
                    hostport = self.host
                else:
                    hostport = f'{self.host}:{self.port}'
                async with websockets.connect(
                        f'ws://{hostport}/{self.path}',
                        compression=('deflate' if self.compression else None),
                        origin=websockets.Origin(f'http://{socket.gethostname()}'),
                        user_agent_header = f'Artisan/{__version__} websockets') as websocket:
                    self.aw.sendmessageSignal.emit(QApplication.translate('Message', '{} connected').format('WebSocket'),True,None)
                    if self._write_queue is None:
                        self._write_queue = asyncio.Queue()
                    consumer_task = asyncio.create_task(self.consumer_handler(websocket))
                    producer_task = asyncio.create_task(self.producer_handler(websocket))
                    done, pending = await asyncio.wait(
                        [consumer_task, producer_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    for task in pending:
                        task.cancel()
                    for task in done:
                        exception = task.exception()
                        if isinstance(exception, Exception):
                            raise exception

            except asyncio.TimeoutError:
                _log.info('connection timeout')
            except Exception as e: # pylint: disable=broad-except
                _log.error(e)

            self.aw.sendmessageSignal.emit(QApplication.translate('Message', '{} disconnected').format('WebSocket'),True,None)
            await asyncio.sleep(0.5)


    def start_background_loop(self, loop: asyncio.AbstractEventLoop) -> None:
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
            self.aw.sendmessageSignal.emit(QApplication.translate('Message', '{} disconnected').format('WebSocket'),True,None)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            loop.close()

    # start/stop sample thread

    def start(self) -> None:
        try:
            self._loop = asyncio.new_event_loop()
            self._thread = Thread(target=self.start_background_loop, args=(self._loop,), daemon=True)
            self._thread.start()
            # run sample task in async loop
            asyncio.run_coroutine_threadsafe(self.connect(), self._loop)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

    def stop(self) -> None:
        # self._loop.stop() needs to be called as follows as the event loop class is not thread safe
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop = None
        # wait for the thread to finish
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        self._write_queue = None

#    # takes a request as dict to be send as JSON
#    # and returns a dict generated from the JSON response
#    # or None on exception or if block=False
    def send(self, request:Dict[str,Any], block:bool = True) -> Optional[Dict[str,Any]]:
        try:
            if self._loop is None:
                self.start()
            if self._loop is not None:
                message_id = random.randint(1,99999)
                request[self.id_node] = message_id
                if self.machine_node:
                    request[self.machine_node] = self.machineID
                json_req = json.dumps(request, indent=None, separators=(',', ':'), ensure_ascii=True) # we conservatively use escaping for accent characters here despite the utf-8 encoding as some clients might not be able to process non-ascii data
                if self._write_queue is not None:
                    if block:
                        future = asyncio.run_coroutine_threadsafe(self.registerRequest(message_id), self._loop)
                        e = future.result()
                        asyncio.run_coroutine_threadsafe(self._write_queue.put(json_req), self._loop)
                        if self.aw.seriallogflag:
                            self.aw.addserial(f'wsport send() blocking: {json_req}')
                        with contextlib.suppress(asyncio.TimeoutError):
                            asyncio.run_coroutine_threadsafe(asyncio.wait_for(e.wait(), self.request_timeout), self._loop).result()
                        if e.is_set():
                            if self.aw.seriallogflag:
                                self.aw.addserial(f'wsport send() received: {message_id}')
                            return self.getRequestResponse(message_id)
                        if self.aw.seriallogflag:
                            self.aw.addserial(f'wsport send() timeout: {message_id}')
                        self.removeRequestResponse(message_id)
                        return None # timeout
                    asyncio.run_coroutine_threadsafe(self._write_queue.put(json_req), self._loop)
                    if self.aw.seriallogflag:
                        self.aw.addserial(f'wsport send() non-blocking: {json_req}')
                return None
            return None
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            lineno = 0
            if exc_tb is not None:
                lineno = exc_tb.tb_lineno
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' wsport:send() {0}').format(str(e)),lineno)
            return None

    def disconnect(self) -> None:
        self.stop()
