#
# ABOUT
# Oribter support for Artisan

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
# Marko Luther, 2026

import io
import os
import asyncio
import logging
import time as libtime

from pathlib import Path
from collections.abc import Callable
from PyQt6.QtCore import Qt, QDateTime, QDate, QTime
from PyQt6.QtWidgets import QApplication
from typing import override, Final, TypedDict, IO, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.atypes import SerialSettings # pylint: disable=unused-import

from artisanlib.async_comm import AsyncComm, IteratorReader
from artisanlib.atypes import ProfileData
from artisanlib.util import (replace_duplicates, encodeLocalStrict, encodeLocal, decodeLocalStrict, weight_units,
    convertWeight, fromFtoCstrict, events_internal_to_external_value, to_ascii)

_log: Final[logging.Logger] = logging.getLogger(__name__)



def compute_crc(data:bytes) -> int:
    crc = 0
    for b in data:
        crc = crc ^ b
    return crc


class State(TypedDict, total=False):
    Connected:int  # connection status (0:disconnected, 1:connected)
    BT:float   # bean temperature
    ET:float   # environmental temperature (damper temperature)
    IT:float   # inlet temperature (furnace temperature)
    DT:float   # drum temperature (interlayer temperature; reserved)
    Air:float  # air pressure
    Drum:int   # drum speed (50-90 RPM)
    Damper:int # air damper setting (0-15)
    Heater:int # heater power (0-10; 0-3200W)
    Sound:int  #
    RoR:float  # rate-of-rise


class Orbiter(AsyncComm):

    HEADER:Final[bytes] = b'\xFF\xFF'
    EVENT:Final[bytes] = b'\x00'
    CMD_SYNC:Final[bytes] = b'\x00'

    __slots__ = [ 'send_timeout', 'connected', 'outer_connected_handler', 'outer_disconnected_handler', '_ACK_received', '_BT', '_ET', '_IT', '_DT', '_air', '_drum', '_damper',
            '_heater', '_sound', '_RoR', '_master_control', '_SERIAL',  '_FW_VERSION', '_PCB_VERSION', '_DASHBOARD_STATUS', '_MODEL', '_MODEL_NUM',
            'isRoaster_Roasting' ]

    def __init__(self, serial:'SerialSettings',
                connected_handler:Callable[[], None]|None = None,
                disconnected_handler:Callable[[], None]|None = None) -> None:

        self.outer_connected_handler:Callable[[], None]|None = connected_handler
        self.outer_disconnected_handler:Callable[[], None]|None = disconnected_handler

        super().__init__(serial=serial, connected_handler=self.connected_handler, disconnected_handler=self.disconnected_handler)

        # configuration
        self.send_timeout:Final[float] = 0.5    # in seconds (note that this period spans the full request/response pair)
        self._logging = False # if True device communication is logged

        #
        self._ACK_received:asyncio.Event = asyncio.Event() # not threadsafe! Only to be used in the async thread
        self.connected:bool = False

        # current readings
        self._BT:float = -1      # bean temperature
        self._ET:float = -1      # environmental temperature
        self._IT:float = -1      # interlayer temperature
        self._DT:float = -1      # drum temperature
        self._air:float = -1     # air pressure
        self._drum:int = -1      # drum speed (50-90 RPM)
        self._damper:int = -1    # air damper setting (0-15)
        self._heater:int = -1    # heater power (0-10; 0-3200W)
        self._sound:int = -1     # sound recognition
        self._RoR:float = -1     # rate-of-rise
        self._master_control:int = 0 # master control

        # machine spec
        self._SERIAL:str = ''                      # 7 bytes
        self._FW_VERSION:str = ''                  # 7 bytes
        self._PCB_VERSION:int = 0                  # 1 byte
        self._DASHBOARD_STATUS:bytes = b'\x00\x00' # 2 bytes
        self._MODEL:str = ''                       # 2 bytes
        self._MODEL_NUM:int = 0                    # 1 byte
        # machine status
        self.isRoaster_Roasting:bool = False

    def connected_handler(self) -> None:
        self.connected = True
        if self.outer_connected_handler is not None:
            self.outer_connected_handler()

    def disconnected_handler(self) -> None:
        self.connected = False
        self.resetReadings()
        if self.outer_disconnected_handler is not None:
            self.outer_disconnected_handler()


    @override
    def setLogging(self, b:bool) -> None:
        self._logging = b
        super().setLogging(b)

    # external API to access machine state

    # getBT triggers fetching a complete set of new readings
    # time is the preheat/roasting/cooling time in seconds send along the sync command to the machine
    def getBT(self, time:int = 0) -> float:
        self.send_sync_await(time)
        return self._BT
    def getET(self) -> float:
        return self._ET
    def getIT(self) -> float:
        return self._IT
    def getDT(self) -> float:
        return self._DT
    def getAir(self) -> float:
        return self._air
    def getDrum(self) -> int:
        return self._drum
    def getDamper(self) -> int:
        return self._damper
    def getHeater(self) -> int:
        return self._heater
    def getSound(self) -> int:
        return self._sound
    def getRoR(self) -> float:
        return self._RoR
    def getMasterControl(self) -> float:
        return self._master_control

    def resetReadings(self) -> None:
        self._BT = -1
        self._ET = -1
        self._IT = -1
        self._DT = -1
        self._air = -1
        self._drum = -1
        self._damper = -1
        self._heater = -1
        self._sound = -1
        self._RoR = -1


    # message decoder

    def register_reading(self, target:bytes, data:bytes) -> None:
        pass

    # decoding utils

    # returns True if bit at offset is 1 else False
    @staticmethod
    def test_bit(b:int, offset:int) -> bool:
        mask = 1 << offset
        return (b & mask) != 0

    # asyncio read implementation

    # https://www.oreilly.com/library/view/using-asyncio-in/9781492075325/ch04.html
    @override
    async def read_msg(self, stream: asyncio.StreamReader|IteratorReader) -> None:
        # await first header byte
        await stream.readuntil(self.HEADER[0:1])
        # check for the second header byte
        if await stream.readexactly(1) == self.HEADER[1:2]:
            cmd = await stream.readexactly(1)
            if cmd[0] == 0: # sync data ACK (total 28 bytes)
                if self._logging:
                    _log.debug('Orbiter CMD sync data')
                data = await stream.readexactly(25)
                if self._logging:
                    _log.debug('Orbiter data: %s', data)
                # check CRC
                try:
                    if compute_crc(cmd[0:1] + data[:24]) == data[24]:
                        dashboard_state = data[3:5]
                        dashboard_state_low = dashboard_state[0]
                        #
                        self.isRoaster_Roasting = self.test_bit(dashboard_state_low, 2)
#                        if self.isRoaster_Roasting:
#                            _log.debug("isRoaster_Roasting")
#                        else:
#                            _log.debug("NOT isRoaster_Roasting")
                        #
                        self._BT = int.from_bytes(data[7:9], 'little', signed=True)
                        self._DT = int.from_bytes(data[9:11], 'little', signed=True)
                        self._IT = int.from_bytes(data[11:13], 'little', signed=True)
                        self._ET = int.from_bytes(data[13:15], 'little', signed=True)
                        self._RoR = int.from_bytes(data[15:17], 'little', signed=True) / 4.
                        self._air = int.from_bytes(data[17:19], 'little', signed=True)
                        self._heater = data[19]
                        self._drum = data[20]
                        self._damper = data[21]
                        self._sound = data[22]
                        self._master_control = data[23]
                    else:
                        _log.debug('Orbiter CRC failed: %s != %s', compute_crc(cmd[0:1] + data[:24]), data[24])
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
                self._ACK_received.set()
            elif cmd[0] == 1: # init ack (total 28 bytes)
                if self._logging:
                    _log.debug('Orbiter CMD init ack')
                data = await stream.readexactly(25)
                if self._logging:
                    _log.debug('Orbiter ack init data: %s', data)
                # check CRC
                try:
                    if compute_crc(cmd[0:1] + data[:24]) == data[24]:
                        self._SERIAL = data[1:8].decode('ascii')
                        self._FW_VERSION = data[8:15].decode('ascii')
                        self._PCB_VERSION = data[15]
                        self._DASHBOARD_STATUS = data[17:19]
                        self._MODEL = data[19:21].decode('ascii')
                        self._MODEL_NUM = data[21]
                        self._sound = data[22]
                        self._master_control = data[23]
                        _log.debug("Orbiter SERIAL: '%s'", self._SERIAL)
                        _log.debug("Orbiter FW_VERSION: '%s'", self._FW_VERSION)
                        _log.debug('Orbiter PCB_VERSION: %s', self._PCB_VERSION)
                        _log.debug('Orbiter DASHBOARD_STATUS: %s', self._DASHBOARD_STATUS)
                        _log.debug('Orbiter MODEL: %s', self._MODEL)
                        _log.debug('Orbiter MODEL_NUM: %s', self._MODEL_NUM)
                        _log.debug('Orbiter _sound: %s', self._sound)
                        _log.debug('Orbiter _master_control: %s', self._master_control)
                    else:
                        _log.debug('Orbiter CRC failed: %s != %s', compute_crc(cmd[0:1] + data[:24]), data[24])
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
                self._ACK_received.set()


    # send message interface

    # message encoder (HEADER-CMD-PARA-DATA-TIME-EVENT-CRC)
    def create_msg(self, cmd:bytes, data:bytes, param:bytes, time:int) -> bytes:
        if len(data) == 0:
            data = b'\x00\x00'
        if len(data) == 1:
            data = b'\x00' + data
        data = data[:2] # data is exactly 2 bytes
        payload = cmd[:1] + param + data + min(max(0,time),65535).to_bytes(2, 'little') + self.EVENT
        crc:int = compute_crc(payload)
        return self.HEADER + payload + crc.to_bytes(1, 'little')

    # data byte order: LSB last (little-endian); eg. data=b'\x07\x00' equals 7
    # returns True if response was received in time, otherwise False
    def send_msg_await(self, cmd:bytes, data:bytes = b'\x00\x00', param:bytes = b'\x00', time:int = 0) -> bool:
        # send via socket using a request/response pattern (serialize=True) awaiting a response that sets the _ACK_received event
        # ensuring a 100ms delay between those request/response pairs
        return self.send_await(self.create_msg(cmd, data, param, time), self._ACK_received, self.send_timeout, serialize=True, delay=0.1)

    #

    def send_sync_await(self, time:int) -> bool:
        return self.send_msg_await(self.CMD_SYNC, time=time)

    #

    @override
    def start(self, connect_timeout:float=5) -> None:
        super().start(connect_timeout)


#    @override
#    def stop(self) -> None:
#        super().stop()


#######


# FILE IMPORTER


def extractProfileOrbiterROP(file:str,
        etypesdefault:list[str],
        alt_etypesdefault:list[str],
        artisanflavordefaultlabels:list[str],
        eventsExternal2InternalValue:Callable[[int],float]) -> ProfileData:
    if file.endswith('.zip'):
        from zipfile import ZipFile
        with ZipFile(file) as zf:
            for rfile in zf.namelist():
                if not rfile.endswith('.rop'):
                    continue
                with zf.open(rfile, 'r') as f:
                    return extractProfileOrbiter(f, etypesdefault, alt_etypesdefault, artisanflavordefaultlabels, eventsExternal2InternalValue)
    elif file.endswith('.rop'):
        with open(file, 'rb') as f:
            return extractProfileOrbiter(f, etypesdefault, alt_etypesdefault, artisanflavordefaultlabels, eventsExternal2InternalValue)
    return ProfileData()


# returns a dict containing all profile information contained in the given Orbiter ROP file
def extractProfileOrbiter(f:IO[bytes],
        etypesdefault:list[str],
        alt_etypesdefault:list[str],
        _artisanflavordefaultlabels:list[str],
        eventsExternal2InternalValue:Callable[[int],float]) -> ProfileData:
    res:ProfileData = ProfileData() # the interpreted data set
    i = 0
    total_packets:int = 0
    footer:bool = False
    title_raw:bytes = b''
    #
    last_drum:int|None = None
    last_damper:int|None = None
    last_heater:int|None = None
    #
    specialevents:list[int] = []
    specialeventstype:list[int] = []
    specialeventsvalue:list[float] = []
    specialeventsStrings:list[str] = []
    #
    timeindex:list[int] = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actual index used
    timex:list[float] = []
    temp1:list[float] = [] # ET (damper temperature)
    temp2:list[float] = [] # BT (bean temperature)
    extra1:list[float] = [] # IT (interlayer temperature)
    extra2:list[float] = [] # DT (furnace temperature; reserved)
    extra3:list[float] = [] # sound
    extra4:list[float] = [] # drum
    extra5:list[float] = [] # damper
    extra6:list[float] = [] # heater
    extra7:list[float] = [] # air pessure
    extra8:list[float] = [] # RoR

    #
    while (packet := f.read(26)):
        if len(packet) == 26:
            header = packet[0:2]
            data = packet[2:25]
            data_crc = packet[25]
            computed_crc = compute_crc(data)
            if header == b'\xff\xff' and int(data_crc) == computed_crc:
                count = packet[2:4]
                time = packet[4:6]
                if total_packets == 0 and count == b'\x00\x00':
                    # header; first data packet
                    total_packets = int.from_bytes(time, 'little', signed = False)
                    batchsize = int.from_bytes(packet[6:8], 'little', signed = False)
                    roasted = int.from_bytes(packet[8:10], 'little', signed = False)
                    #total_time = int.from_bytes(packet[12:14], 'little', signed = False)
                    res['weight'] = [batchsize,roasted,'g']
                elif int.from_bytes(count, 'little', signed = False) == total_packets - 2 and time == b'\xff\xff':
                    # footer 1 (profile name)
                    title_raw = data[4:-1]
                    footer = True
                elif int.from_bytes(count, 'little', signed = False) == total_packets - 1 and time == b'\xfe\xff':
                    # footer 2 (date)
                    year = int.from_bytes(data[4:6], 'little', signed = False)
                    month = int.from_bytes(data[6:8], 'little', signed = False)
                    day = int.from_bytes(data[8:10], 'little', signed = False)
                    date = QDateTime(QDate(year, month, day), QTime(0, 0))
                    roastdate:str|None = encodeLocal(date.date().toString())
                    if roastdate is not None:
                        res['roastdate'] = roastdate
                    roastisodate:str|None = encodeLocal(date.date().toString(Qt.DateFormat.ISODate))
                    if roastisodate is not None:
                        res['roastisodate'] = roastisodate
                    roasttime:str|None = encodeLocal(date.time().toString())
                    if roasttime is not None:
                        res['roasttime'] = roasttime
                    res['roastepoch'] = int(date.toSecsSinceEpoch())
                    res['roasttzoffset'] = libtime.timezone
                    title = (title_raw + data[10:-1]).rstrip(b'\x00').decode('utf-8')
                    res['title'] = encodeLocalStrict(title)
                elif not footer and i < total_packets - 2: # ignore data beyond total_packets and only process data between header and the two footers
                    # regular data
                    BT = int.from_bytes(packet[6:8], 'little', signed = False)
                    DT = int.from_bytes(packet[8:10], 'little', signed = False)
                    IT = int.from_bytes(packet[10:12], 'little', signed = False)
                    ET = int.from_bytes(packet[12:14], 'little', signed = False)
#                    BT_target = int.from_bytes(packet[14:16], 'little', signed = False)

                    air = int.from_bytes(packet[16:18], 'little', signed = False)
                    heater = packet[20] * 10
                    drum = packet[21]
                    damper = packet[22] * 10
                    event = packet[23]

                    if timeindex[0] == -1: # and event == 0: # the first reading is marked CHARGE
                        timeindex[0] = len(timex)
                    elif event == 3 and timeindex[1] == 0:
                        timeindex[1] = len(timex)
                    elif event == 5 and timeindex[2] == 0:
                        timeindex[2] = len(timex)
                    elif event == 6 and timeindex[4] == 0:
                        timeindex[4] = len(timex)
                    elif event == 7 and timeindex[6] == 0:
                        timeindex[6] = len(timex)

                    if damper != last_damper:
                        last_damper = damper
                        specialeventsvalue.append(eventsExternal2InternalValue(damper))
                        specialevents.append(len(timex))
                        specialeventstype.append(0)
                        specialeventsStrings.append(f'{damper}')

                    if drum != last_drum:
                        last_drum = drum
                        specialeventsvalue.append(eventsExternal2InternalValue(drum))
                        specialevents.append(len(timex))
                        specialeventstype.append(1)
                        specialeventsStrings.append(f'{drum}' + 'RPM')

                    if heater != last_heater:
                        last_heater = heater
                        specialeventsvalue.append(eventsExternal2InternalValue(heater))
                        specialevents.append(len(timex))
                        specialeventstype.append(3)
                        specialeventsStrings.append(f'{heater*10}' + '%')

                    timex.append(int.from_bytes(time, 'little', signed = False))
                    temp1.append(ET)
                    temp2.append(BT)
                    extra1.append(IT)
                    extra2.append(DT)
                    extra3.append(-1)
                    extra4.append(drum)
                    extra5.append(damper)
                    extra6.append(heater)
                    extra7.append(air)
                    extra8.append(-1)
            i += 1

        res['mode'] = 'C'
        res['timex'] = timex
        res['temp1'] = replace_duplicates(temp1)
        res['temp2'] = replace_duplicates(temp2)
        res['timeindex'] = timeindex

        res['extradevices'] = [197, 198, 199, 200]
        res['extratimex'] = [timex[:],timex[:],timex[:],timex[:]]

        res['extraname1'] = ['IT', 'Sound', '{2}', '{0}']
        res['extratemp1'] = [extra1, extra3, extra5, extra7]
        res['extramathexpression1'] = ['', '', '', '']

        res['extraname2'] = ['DT', '{1}', '{3}', 'RoR']
        res['extratemp2'] = [extra2, extra4, extra6, extra8]
        res['extramathexpression2'] = ['', '', '', '']

        res['extraLCDvisibility1'] = [True, False, False, True, True, True, True, True, True, True]
        res['extraLCDvisibility2'] = [False, False, False, True, True, True, True, True, True, True]
        res['extraCurveVisibility1'] = [True, False, False, False, True, True, True, True, True, True]
        res['extraCurveVisibility2'] = [False, False, False, True, True, True, True, True, True, True]

        if len(specialevents) > 0:
            res['specialevents'] = specialevents
            res['specialeventstype'] = specialeventstype
            res['specialeventsvalue'] = specialeventsvalue
            res['specialeventsStrings'] = specialeventsStrings

        etypes = etypesdefault
        etypes[3] = alt_etypesdefault[3]
        res['etypes'] = [encodeLocalStrict(etype) for etype in etypes]

    return res


# FILE EXPORTER


def saveOrbiterROP(filename:str, profile:ProfileData) -> bool:
    res:bool = False
    from zipfile import ZipFile
    if not filename.endswith('.rop.zip'):
        root, ext = os.path.splitext(filename)
        if ext in {'.rop', '.zip'}:
            filename = root + '.rop.zip'
        else:
            filename += '.rop.zip'
    with ZipFile(filename, 'w') as zip_file:
        buffer = io.BytesIO()
        with buffer as file:
            res = saveOrbiter(Path(filename).name.rstrip('.zip').rstrip('.rop'), file, profile)
            filename = os.path.basename(filename)
            root, ext = os.path.splitext(filename)
            if ext != '.zip':
                root = filename
            if not root.endswith('.rop'):
                root += '.rop'
            zip_file.writestr(root, buffer.getvalue())
    return res

# store given profile in Orbiter format to outfile
def saveOrbiter(filename:str, outfile:IO[bytes], profile:ProfileData) -> bool:
    readings:list[bytes] = []
    try:
        default_title:str = QApplication.translate('Scope Title', 'Roaster Scope')
        title:str = decodeLocalStrict(profile.get('title', default_title), default_title)
        if title == default_title:
            title = filename
        date:QDate = (QDate.fromString(decodeLocalStrict(profile['roastisodate']),Qt.DateFormat.ISODate) if 'roastisodate' in profile else QDate())
        mode:str = profile.get('mode', 'C')
        weight:list[float|str] = [0,0,'g']
        if 'weight' in profile:
            weight = profile['weight']
        unit:str = decodeLocalStrict(weight[2], 'g')
        try:
            weight_unit_idx = weight_units.index(unit)
        except ValueError:
            weight_unit_idx = 0
        batchsize:int = int(round(convertWeight(float(weight[0]), weight_unit_idx, 0))) # in g
        roasted_weight = int(round(convertWeight(float(weight[1]), weight_unit_idx, 0))) # in g
        #
        timeindex:list[int] = profile.get('timeindex', [-1,0,0,0,0,0,0,0])
        timex:list[float] = profile.get('timex', [])
        temp1:list[float] = profile.get('temp1', [])
        temp2:list[float] = profile.get('temp2', [])
        extratimex = profile.get('extratimex', [])
        extratemp1 = profile.get('extratemp1', [])
        extratemp2 = profile.get('extratemp2', [])
        if mode == 'F':
            # we convert the temperature data to C
            temp1 = [fromFtoCstrict(temp) for temp in temp1]
            temp2 = [fromFtoCstrict(temp) for temp in temp2]
            for i,_ in enumerate(extratimex):
                extratemp1[i] = [fromFtoCstrict(temp) for temp in extratemp1[i]]
                extratemp2[i] = [fromFtoCstrict(temp) for temp in extratemp2[i]]
        #
        # we assume that the specialevents are order
        specialevents = profile.get('specialevents', [])
        specialeventstype = profile.get('specialeventstype', [])
        specialeventsvalue = profile.get('specialeventsvalue', [])
        #
        #
        time:int = -1
        time_offset:float = 0
        heater:int = 0
        drum:int = 0
        damper:int = 0
        event:int = 255 # main event
        CHARGE:bool = False
        DRY:bool = False
        FCs:bool = False
        SCs:bool = False
        DROP:bool = False
        CHARGE_idx = (timeindex[0] if timeindex[0]>=0 else 0)
        for idx,tx in enumerate(timex):
            if not (DROP or (timeindex[0] > -1 and tx < timex[timeindex[0]])): # ignore all readings before CHARGE and after DROP
                if len(specialevents)>0 and idx >= specialevents[0]:
                    # we passed the next special event
                    if specialeventstype[0] == 0:
                        damper = int(round(events_internal_to_external_value(specialeventsvalue[0])/10))
                    elif specialeventstype[0] == 1:
                        drum = events_internal_to_external_value(specialeventsvalue[0])
                    elif specialeventstype[0] == 3:
                        heater = int(round(events_internal_to_external_value(specialeventsvalue[0])/10))
                    # we consume the event
                    specialevents = specialevents[1:]
                    specialeventstype = specialeventstype[1:]
                    specialeventsvalue = specialeventsvalue[1:]

                if not CHARGE: # mark the first reading as CHARGE
                    event = 0
                    CHARGE = True
                    time_offset = (timex[CHARGE_idx] if len(timex)>CHARGE_idx else 0)
                elif not DRY and timeindex[1] > 0 and tx >= timex[timeindex[1]]:
                    event = 3
                    DRY = True
                elif not FCs and timeindex[2] > 0 and tx >= timex[timeindex[2]]:
                    event = 5
                    FCs = True
                elif not SCs and timeindex[4] > 0 and tx >= timex[timeindex[4]]:
                    event = 6
                    SCs = True
                elif timeindex[6] > 0 and tx >= timex[timeindex[6]]: # and not DROP
                    event = 7
                    DROP = True

                tx_new = int(round(tx - time_offset))

                if tx_new != time:
                    # ignore readings with timestamps already used to prevent the introduction of duplicates
                    time = tx_new

                    values:bytes = time.to_bytes(2, 'little') + \
                        int(float(temp2[idx])).to_bytes(2, 'little') + \
                        (int(float(extratemp2[0][idx])).to_bytes(2, 'little') if len(extratemp2)>0 else b'\x00\x00') + \
                        (int(float(extratemp1[0][idx])).to_bytes(2, 'little') if len(extratemp1)>0 else b'\x00\x00') + \
                        int(float(temp1[idx])).to_bytes(2, 'little') + \
                        b'\x00\x00' + \
                        (int(float(extratemp1[3][idx])).to_bytes(2, 'little') if len(extratemp1)>3 else b'\x00\x00') + \
                        b'\x00\x00' + \
                        heater.to_bytes(1, 'little') + \
                        drum.to_bytes(1, 'little') + \
                        damper.to_bytes(1, 'little') + \
                        event.to_bytes(1, 'little') + \
                        b'\x00' # reserve
                    event = 255
                    readings.append(values)

        title_length:int = 30
        title_bytes = to_ascii(title).encode('utf-8')[:title_length].ljust(title_length, b'\00')
        preheat_temperature = int(round(temp2[CHARGE_idx] if len(temp2)>CHARGE_idx else 0))
        drop_time_seconds:int = (int(round(timex[-1])) if len(timex)>0 else 0)
        header = b'\xff\xff'
        # header
        header_data = b'\x00\x00' + \
            (len(readings) + 3).to_bytes(2, 'little') + \
            batchsize.to_bytes(2, 'little') + \
            roasted_weight.to_bytes(2, 'little') + \
            preheat_temperature.to_bytes(2, 'little') + \
            drop_time_seconds.to_bytes(2, 'little') + \
            b'\x00\x00' + b'\x00\x00' + b'\x00\x00' + \
            b'\x00\x00\x00\x00\x00'
        header_data_crc = compute_crc(header_data)
        header_bytes = header + header_data + header_data_crc.to_bytes(1,byteorder='little',signed = False)
        outfile.write(header_bytes)
        # readings
        for count, values in enumerate(readings):
            data = count.to_bytes(2, 'little') + values
            crc = compute_crc(data)
            packet = header + data + crc.to_bytes(1,byteorder='little',signed = False)
            outfile.write(packet)
        # footer 1
        footer1_count = len(readings) + 1
        footer1_values = title_bytes[:18] + b'\x00'
        footer1_data = footer1_count.to_bytes(2, 'little') + b'\xFF\xFF' + footer1_values
        footer1_crc = compute_crc(footer1_data)
        footer1 = header + footer1_data + footer1_crc.to_bytes(1,byteorder='little',signed = False)
        outfile.write(footer1)
        # footer 2
        footer2_count = len(readings) + 2
        year = date.year().to_bytes(2,byteorder='little',signed = False)
        month = date.month().to_bytes(2,byteorder='little',signed = False)
        day = date.day().to_bytes(2,byteorder='little',signed = False)
        footer2_values = year + month + day + title_bytes[18:title_length] + b'\x00'
        footer2_data = footer2_count.to_bytes(2, 'little') + b'\xFE\xFF' + footer2_values
        footer2_crc = compute_crc(footer2_data)
        footer2 = header + footer2_data + footer2_crc.to_bytes(1,byteorder='little',signed = False)
        outfile.write(footer2)

        return True
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)
    return False


#######

def main() -> None:
    import time # pylint:disable=reimported
    from artisanlib.atypes import SerialSettings
    serial = SerialSettings(
        port = '/dev/slave',
        baudrate = 115200,
        bytesize = 8,
        stopbits = 1,
        parity = 'N',
        timeout = 0.5,
        clear_HUPCL = True)
    orbiter = Orbiter(serial)
    orbiter.start()
    for _ in range(4):
        print('>>> hallo')
        val:int = 7
        orbiter.send_msg_await(b'\x0D', val.to_bytes(2, 'little')) # set power to 7
        time.sleep(1)
        print('BT', orbiter.getBT())
        time.sleep(1)
    orbiter.stop()
    time.sleep(1)
    #print('thread alive?',orbiter._thread.is_alive())

if __name__ == '__main__':
    main()
