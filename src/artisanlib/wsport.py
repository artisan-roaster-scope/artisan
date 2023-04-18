#
# ABOUT
# WebSocket support for Artisan

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

import sys
import time
import threading

import json
import random

from typing import List, Dict, Optional, Any, TYPE_CHECKING
from typing_extensions import Final  # Python <=3.7

if TYPE_CHECKING:
    import websocket # type: ignore # pylint: disable=unused-import

try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #pylint: disable = E, W, R, C
    from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

class wsport():
    def __init__(self,aw) -> None:
        self.aw = aw

        # connects to "ws://<host>:<port>/<path>"
        self.host:str = '127.0.0.1' # the TCP host
        self.port:int = 80          # the TCP port
        self.path:str = 'WebSocket' # the ws path
        self.machineID:int = 0

        self.lastReadResult:Optional[Dict] = {} # this is set by eventaction following some custom button/slider Modbus actions with "read" command

        self.channels:Final[int] = 10 # maximal number of WebSocket channels

        # WebSocket data
        self.readings:List[float] = [-1]*self.channels

        self.channel_requests:List[str] = ['']*self.channels
        self.channel_nodes:List[str] = ['']*self.channels
        self.channel_modes:List[int] = [0]*self.channels # temp mode is an int here, 0:__,1:C,2:F

        # configurable via the UI:
        self.connect_timeout:float = 4    # in seconds
        self.request_timeout:float = 0.5  # in seconds
        self.reconnect_interval:float = 2 # in seconds
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

        self.open_event:Optional[threading.Event] = None # an event set on connecting
        self.pending_events:Dict[int, Any] = {} # message ids associated with pending threading.Event object or result

        self.active:bool = False
        self.ws:Optional['websocket.WebSocketApp'] = None  # the WebService client object
        self.wst:Optional[threading.Thread] = None # the WebService thread

    def onMessage(self, _, message):
        if message is not None:
            j = json.loads(message)
            if self.aw.seriallogflag:
                self.aw.addserial(f'wsport onMessage(): {j}')
            if self.id_node in j:
                self.setRequestResponse(j[self.id_node],j)
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
                        self.aw.qmc.markChargeSignal.emit(delay)
                        if self.aw.seriallogflag:
                            self.aw.addserial(f'wsport markCHARGE() with delay={delay} signal sent')
                elif self.drop_message != '' and pushMessage == self.drop_message:
                    if self.aw.seriallogflag:
                        self.aw.addserial('wsport message: DROP')
                    if self.aw.qmc.flagstart and self.aw.qmc.timeindex[6] == 0:
                        # markDROP
                        self.aw.qmc.markDropSignal.emit()
                        if self.aw.seriallogflag:
                            self.aw.addserial('wsport markDROP signal sent')
                    if self.OFFonDROP and self.aw.qmc.flagstart:
                        # turn Recorder off after two sampling periods
                        delay = self.aw.qmc.delay * 2 # we delay the turning OFF action by 2 sampling periods
                        time.sleep(delay)
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
                                self.aw.qmc.markDRYSignal.emit()
                            elif self.aw.qmc.timeindex[2] == 0 and data[self.event_node] == self.FCs_node:
                                # addEvent(FCs) received
                                if self.aw.seriallogflag:
                                    self.aw.addserial('wsport message: addEvent(FCs) processed')
                                self.aw.qmc.markFCsSignal.emit()
                            elif self.aw.qmc.timeindex[3] == 0 and data[self.event_node] == self.FCe_node:
                                # addEvent(FCe) received
                                if self.aw.seriallogflag:
                                    self.aw.addserial('wsport message: addEvent(FCe) processed')
                                self.aw.qmc.markFCeSignal.emit()
                            elif self.aw.qmc.timeindex[4] == 0 and data[self.event_node] == self.SCs_node:
                                # addEvent(SCs) received
                                if self.aw.seriallogflag:
                                    self.aw.addserial('wsport message: addEvent(SCs) processed')
                                self.aw.qmc.markSCsSignal.emit()
                            elif self.aw.qmc.timeindex[5] == 0 and data[self.event_node] == self.SCe_node:
                                # addEvent(SCe) received
                                if self.aw.seriallogflag:
                                    self.aw.addserial('wsport message: addEvent(SCe) processed')
                                self.aw.qmc.markSCeSignal.emit()
                        elif self.aw.seriallogflag:
                            self.aw.addserial(f'wsport message: addEvent({data})')
                    elif self.aw.seriallogflag:
                        self.aw.addserial('wsport message: addEvent() received and ignored. Not recording.')

                # set burner: { "pushMessage": "setBurnerCapacity", "data": { "burnercapacity": 51 } }
                # name of current roast set: {"pushMessage": "setRoastingProcessName", "data": { "name": "Test roast 123" }}
                # note of current roast set: {"pushMessage": "setRoastingProcessNote", "data": { "note": "A test comment" }}
                # fill weight of current roast set: {"pushMessage": "setRoastingProcessFillWeight", "data": { "fillWeight": 12 }}

    def onError(self, _, err):
        self.aw.qmc.adderror(QApplication.translate('Error Message','WebSocket connection failed: {}').format(err))
        if self.aw.seriallogflag:
            self.aw.addserial(f'wsport onError(): {err}')

    def onClose(self, *_):
        self.aw.sendmessage(QApplication.translate('Message','WebSocket disconnected'))
        if self.aw.seriallogflag:
            self.aw.addserial('wsport onClose()')

    def onOpen(self, *_):
        if self.open_event is not None:
            self.open_event.set() # unblock the connect action
        self.aw.sendmessage(QApplication.translate('Message','WebSocket connected'))
        if self.aw.seriallogflag:
            self.aw.addserial('wsport onOpen()')

    def onPing(self, *_):
        if self.aw.seriallogflag:
            self.aw.addserial('wsport onPing()')

    def onPong(self, *_):
        if self.aw.seriallogflag:
            self.aw.addserial('wsport onPong()')

    def create(self):
        import websocket # type: ignore
        # initialize readings
        self.readings = [-1]*self.channels
        while self.active:
            try:
                if self.aw.seriallogflag:
                    self.aw.addserial('wsport create()')
                websocket.setdefaulttimeout(self.connect_timeout)
                #websocket.enableTrace(True)
                self.ws = websocket.WebSocketApp(f'ws://{self.host}:{self.port}/{self.path}',
                                on_message=self.onMessage,
                                on_error=self.onError,
                                on_ping=self.onPing,
                                on_pong=self.onPong,
                                on_close=self.onClose,
                                on_open=self.onOpen
                                )
                if self.ws is not None:
                    self.ws.run_forever(
                        skip_utf8_validation=True,
                        ping_interval=self.ping_interval,
                        ping_timeout=self.ping_timeout)
            except Exception as e: # pylint: disable=broad-except
                self.aw.qmc.adderror(QApplication.translate('Error Message','WebSocket connection failed: {}').format(e))
                if self.aw.seriallogflag:
                    self.aw.addserial(f'wsport create() error: {e}')
            time.sleep(self.reconnect_interval)
            if self.active:
                self.aw.sendmessage(QApplication.translate('Error Message','Reconnecting WebSocket'))
        self.ws = None

    def connect(self) -> bool:
        if not self.is_connected():
            if self.aw.seriallogflag:
                self.aw.addserial('wsport connect()')
            self.active = True
            self.wst = threading.Thread(target=self.create)
#            if self.wst is not None:
            self.open_event = threading.Event()
            if self.open_event is not None:
                self.wst.start()
                success = self.open_event.wait(timeout=self.connect_timeout + 0.3)
                self.open_event = None
                return success
#            return False
        return True

    def is_connected(self):
        return self.ws is not None and self.ws.sock

    def disconnect(self):
        if self.is_connected():
            if self.aw.seriallogflag:
                self.aw.addserial('wsport disconnect()')
            self.active = False
            if self.ws is not None:
                self.ws.close()
                self.ws = None
            if self.wst is not None:
                self.wst.join()
                self.wst = None


    # request event handling

    def registerRequest(self,message_id):
        e = threading.Event()
        self.pending_events[message_id] = e
        return e

    def removeRequestResponse(self,message_id):
        del self.pending_events[message_id]

    # replace the request event by its result
    def setRequestResponse(self,message_id,v):
        if message_id in self.pending_events:
            pe = self.pending_events[message_id]
            if isinstance(pe,threading.Event):
                pe.set() # unblock
                self.removeRequestResponse(message_id)
                self.pending_events[message_id] = v

    # returns the response received for request with id or None
    def getRequestResponse(self, message_id):
        if message_id in self.pending_events:
            v = self.pending_events[message_id]
            del self.pending_events[message_id]
            if not isinstance(v, threading.Event):
                return v
        return None

    # takes a request as dict to be send as JSON
    # and returns a dict generated from the JSON response
    # or None on exception or if block=False
    def send(self, request:Dict, block=True) -> Optional[Dict]:
        try:
            connected = self.connect()
            if connected and self.ws is not None:
                message_id = random.randint(1,99999)
                request[self.id_node] = message_id
                if self.machine_node:
                    request[self.machine_node] = self.machineID
                json_req = json.dumps(request)
                if block:
                    e = self.registerRequest(message_id)
                    self.ws.send(json_req)
                    if self.aw.seriallogflag:
                        self.aw.addserial(f'wsport send() blocking: {json_req}')
                    success = e.wait(timeout=self.request_timeout)
                    if success:
                        if self.aw.seriallogflag:
                            self.aw.addserial(f'wsport send() received: {message_id}')
                        return self.getRequestResponse(message_id)
                    if self.aw.seriallogflag:
                        self.aw.addserial(f'wsport send() timeout: {message_id}')
                    self.removeRequestResponse(message_id)
                    return None # timeout
                self.ws.send(json_req)
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
