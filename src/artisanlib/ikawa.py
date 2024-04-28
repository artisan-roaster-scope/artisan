#
# ABOUT
# IKAWA CSV Roast Profile importer for Artisan

from pathlib import Path
import time as libtime
import os
import base64
import csv
import re
import logging
from typing import Final, Optional, List, Dict, Tuple, Callable, ClassVar, Any, Generator, TYPE_CHECKING


if TYPE_CHECKING:
    from artisanlib.types import ProfileData # pylint: disable=unused-import
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import

try:
    from PyQt6.QtCore import QDateTime, Qt, QTimer, QMutex, QWaitCondition, QUrl # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QDateTime, Qt, QTimer, QMutex, QWaitCondition, QUrl  # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.util import encodeLocal
try:
    from artisanlib.ble import BleInterface, BLE_CHAR_TYPE # noqa: F811
except ImportError:
    # BLE not available on older Windows/PyQt5 platforms
    pass
from proto import IkawaCmd_pb2 # type:ignore[unused-ignore]


_log: Final[logging.Logger] = logging.getLogger(__name__)


def url_to_profile(url:str, log_data:bool = False) -> IkawaCmd_pb2.RoastProfile: # pylint: disable=no-member
    url += '=='
    base64_bytes = url.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    if log_data:
        _log.info('ikawa profile: %s',message_bytes)
    return IkawaCmd_pb2.RoastProfile().FromString(message_bytes) # pylint: disable=no-member

def extractProfileIkawaURL(url:QUrl, aw:'ApplicationWindow') -> 'ProfileData':
    ikawa_profile = url_to_profile(url.query(), log_data=aw.qmc.device_logging)
    res:ProfileData = {} # the interpreted data set
    res['samplinginterval'] = 1.0

    specialevents:List[int] = []
    specialeventstype:List[int] = []
    specialeventsvalue:List[float] = []
    specialeventsStrings:List[str] = []

    timex:List[float] = []
    temp1:List[float] = []
    temp2:List[float] = []
    extra1:List[float] = []
    extra2:List[float] = []
    extra3:List[float] = []
    extra4:List[float] = []
    extra5:List[float] = []
    extra6:List[float] = []
    timeindex:List[int] = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actual index used

    fan_points:List[Any] = list(ikawa_profile.fan_points)
    for idx, p in enumerate(ikawa_profile.temp_points):
        if idx != 0:
            # add additional fan_point before this temp point
            for fp in fan_points:
                if fp.time < p.time:
                    timex.append(fp.time/10+30)
                    temp1.append(-1.0)
                    temp2.append(-1.0)
                    extra1.append(-1)
                    extra2.append(-1.0)
                    extra3.append(-1.0)
                    fan = round(fp.power / 2.55)
                    extra4.append(fan)
                    extra5.append(-1.0)
                    extra6.append(-1.0)
                    v = fan/10. + 1
                    specialeventsvalue.append(v)
                    specialevents.append(idx)
                    specialeventstype.append(0)
                    specialeventsStrings.append(f'{int(fan)}' + '%')
                    fan_points = fan_points[1:]
                else:
                    break

        timex.append(p.time / 10 if idx == 0 else p.time / 10 + 30)
        temp1.append(-1.0)
        temp2.append(-1.0)
        extra1.append(p.temp/10)
        extra2.append(-1.0)
        extra3.append(-1.0)
        if fan_points and fan_points[0].time == p.time:
            # we add the fan information
            fan = round(fan_points[0].power / 2.55)
            extra4.append(fan)
            v = fan/10. + 1
            specialeventsvalue.append(v)
            specialevents.append(idx)
            specialeventstype.append(0)
            specialeventsStrings.append(f'{int(fan)}' + '%')
            # and remove the fan point from the list of fan points to be processed
            fan_points = fan_points[1:]
        else:
            extra4.append(-1.0)
        extra5.append(-1.0)
        extra6.append(-1.0)

    cooldown_fan = round(ikawa_profile.cooldown_fan.power / 2.55)
    v = cooldown_fan/10. + 1
    specialeventsvalue.append(v)
    specialevents.append(len(timex)-1)
    specialeventstype.append(0)
    specialeventsStrings.append(f'{int(cooldown_fan)}' + '%')


    res['title'] = ikawa_profile.name
    res['beans'] = ikawa_profile.coffee_name
    res['mode'] = 'C'

    timeindex = [0,0,0,0,0,0,len(timex)-1,0]
    res['timex'] = timex
    res['temp1'] = temp1
    res['temp2'] = temp2
    res['timeindex'] = timeindex

    res['extradevices'] = [143, 144, 145]
    res['extratimex'] = [timex[:],timex[:],timex[:]]

    res['extraname1'] = ['SET', '{3}', 'State']
    res['extratemp1'] = [extra1, extra3, extra5]
    res['extramathexpression1'] = ['', '', '']

    res['extraname2'] = ['RPM', '{0}', 'Extra 2']
    res['extratemp2'] = [extra2, extra4, extra6]
    res['extramathexpression2'] = ['x/100', '', '']

    if len(specialevents) > 0:
        res['specialevents'] = specialevents
        res['specialeventstype'] = specialeventstype
        res['specialeventsvalue'] = specialeventsvalue
        res['specialeventsStrings'] = specialeventsStrings

    res['etypes'] = aw.qmc.etypesdefault

    return res


# returns a dict containing all profile information contained in the given IKAWA CSV file
def extractProfileIkawaCSV(file:str, aw:'ApplicationWindow') -> 'ProfileData':
    res:ProfileData = {} # the interpreted data set

    res['samplinginterval'] = 1.0

    # set profile date from the file name if it has the format "IKAWA yyyy-mm-dd hhmmss.csv"
    try:
        filename = os.path.basename(file)
        p = re.compile(r'IKAWA \d{4,4}-\d{2,2}-\d{2,2} \d{6,6}.csv')
        if p.match(filename):
            s = filename[6:-4] # the extracted date time string
            date = QDateTime.fromString(s,'yyyy-MM-dd HHmmss')
            roastdate:Optional[str] = encodeLocal(date.date().toString())
            if roastdate is not None:
                res['roastdate'] = roastdate
            roastisodate:Optional[str] = encodeLocal(date.date().toString(Qt.DateFormat.ISODate))
            if roastisodate is not None:
                res['roastisodate'] = roastisodate
            roasttime:Optional[str] = encodeLocal(date.time().toString())
            if roasttime is not None:
                res['roasttime'] = roasttime
            res['roastepoch'] = int(date.toSecsSinceEpoch())
            res['roasttzoffset'] = libtime.timezone
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)

    with open(file, newline='',encoding='utf-8') as csvFile:
        data = csv.reader(csvFile,delimiter=',')
        #read file header
        header = [h.strip() for h in next(data)]

        fan:Optional[float] = None # holds last processed fan event value
        fan_last:Optional[float] = None # holds the fan event value before the last one
        heater:Optional[float] = None # holds last processed heater event value
        heater_last:Optional[float] = None # holds the heater event value before the last one
#        fan_event:bool = False # set to True if a fan event exists
#        heater_event:bool = False # set to True if a heater event exists
        specialevents:List[int] = []
        specialeventstype:List[int] = []
        specialeventsvalue:List[float] = []
        specialeventsStrings:List[str] = []
        timex:List[float] = []
        temp1:List[float] = []
        temp2:List[float] = []
        extra1:List[float] = []
        extra2:List[float] = []
        extra3:List[float] = []
        extra4:List[float] = []
        extra5:List[float] = []
        extra6:List[float] = []
        timeindex:List[int] = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actual index used
        i:int = 0
        v:Optional[float]
        last_item:Optional[Dict[str,str]] = None
        for row in data:
            i = i + 1
            items = list(zip(header, row))
            item:Dict[str,str] = {}
            for (name, value) in items:
                item[name] = value.strip()
            last_item = item
            # take i as time in seconds
            timex.append(i)
            if 'inlet temp' in item:
                temp1.append(float(item['inlet temp']))
            elif 'temp below' in item:
                temp1.append(float(item['temp below']))
            else:
                temp1.append(-1)
            # we map IKAWA Exhaust to BT as main events like CHARGE and DROP are marked on BT in Artisan
            if 'exaust temp' in item:
                temp2.append(float(item['exaust temp']))
            elif 'temp above' in item:
                temp2.append(float(item['temp above']))
            else:
                temp2.append(-1)
            # mark CHARGE
            if timeindex[0] <= -1 and 'state' in item and item['state'] == 'doser open':
                timeindex[0] = max(0,i)
            # mark DROP
            if timeindex[6] == 0 and 'state' in item and item['state'] == 'cooling':
                timeindex[6] = max(0,i)
            # add SET and RPM
            if 'temp set' in item:
                extra1.append(float(item['temp set']))
            elif 'setpoint' in item:
                extra1.append(float(item['setpoint']))
            else:
                extra1.append(-1)
            if 'fan speed (RPM)' in item:
                rpm = float(item['fan speed (RPM)'])
                extra2.append(rpm/100)
            elif 'fan speed' in item:
                rpm = float(item['fan speed'])
                extra2.append(rpm/100)
            else:
                extra2.append(-1)
            extra3.append(-1)
            extra4.append(-1)
            extra5.append(-1)
            if 'abs_humidity' in item:
                humidity = float(item['abs_humidity'])
                extra6.append(humidity)
            else:
                extra6.append(-1)

            if 'fan set (%)' in item or 'fan set' in item:
                try:
                    v = fan
                    if 'fan set (%)' in item:
                        v = float(item['fan set (%)'])
                    elif 'fan set' in item:
                        v = float(item['fan set'])
                    if v is not None and v != fan:
                        # fan value changed
                        if v == fan_last:
                            # just a fluctuation, we remove the last added fan value again
                            fan_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 0)
                            del specialeventsvalue[fan_last_idx]
                            del specialevents[fan_last_idx]
                            del specialeventstype[fan_last_idx]
                            del specialeventsStrings[fan_last_idx]
                            fan = fan_last
                            fan_last = None
                        else:
                            fan_last = fan
                            fan = v
#                            fan_event = True
                            v = v/10. + 1
                            specialeventsvalue.append(v)
                            specialevents.append(i-1)
                            specialeventstype.append(0)
                            specialeventsStrings.append(f'{fan}' + '%')
                    else:
                        fan_last = None
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            if 'heater power (%)' in item or 'heater' in item:
                try:
                    v = heater
                    if 'heater power (%)' in item:
                        v = float(item['heater power (%)'])
                    elif 'heater' in item:
                        v = float(item['heater'])
                    if v is not None and v != heater:
                        # heater value changed
                        if v == heater_last:
                            # just a fluctuation, we remove the last added heater value again
                            heater_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 3)
                            del specialeventsvalue[heater_last_idx]
                            del specialevents[heater_last_idx]
                            del specialeventstype[heater_last_idx]
                            del specialeventsStrings[heater_last_idx]
                            heater = heater_last
                            heater_last = None
                        else:
                            heater_last = heater
                            heater = v
#                            heater_event = True
                            v = v/10. + 1
                            specialeventsvalue.append(v)
                            specialevents.append(i-1)
                            specialeventstype.append(3)
                            specialeventsStrings.append(f'{heater}' + '%')
                    else:
                        heater_last = None
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
        if last_item is not None and timeindex[0]>-1 and 'adfc_timestamp' in last_item:
            # if there is data at all, CHARGE is set and adfc_timestamp is given
            # fcs_time is the time of FCs in seconds after CHARGE
            fcs_time = float(last_item['adfc_timestamp'])
            if fcs_time > 0:
                # if fcs_time is given
                FCs_idx = int(round(fcs_time + timeindex[0]))
                if 0 < FCs_idx < len(timex):
                    timeindex[2] = FCs_idx

    res['mode'] = 'C'

    res['timex'] = timex
    res['temp1'] = temp1
    res['temp2'] = temp2
    res['timeindex'] = timeindex

    res['extradevices'] = [143, 144, 145]
    res['extratimex'] = [timex[:],timex[:],timex[:]]

    res['extraname1'] = ['SET', '{3}', 'State']
    res['extratemp1'] = [extra1, extra3, extra5]
    res['extramathexpression1'] = ['', '', '']

    res['extraname2'] = ['RPM', '{0}', 'Humidity']
    res['extratemp2'] = [extra2, extra4, extra6]
    res['extramathexpression2'] = ['x/100', '', '']

    if len(specialevents) > 0:
        res['specialevents'] = specialevents
        res['specialeventstype'] = specialeventstype
        res['specialeventsvalue'] = specialeventsvalue
        res['specialeventsStrings'] = specialeventsStrings

    res['etypes'] = aw.qmc.etypesdefault
    res['title'] = Path(file).stem
    return res


try: # BLE not available on some platforms
    class IKAWA_BLE:

        ###CmdType
        BOOTLOADER_GET_VERSION:      ClassVar[int] = 0
        MACH_PROP_GET_TYPE:          ClassVar[int] = 2
        MACH_PROP_GET_ID:            ClassVar[int] = 3
        MACH_STATUS_GET_ERROR_VALUE: ClassVar[int] = 10
        MACH_STATUS_GET_ALL_VALUE:   ClassVar[int] = 11
        HIST_GET_TOTAL_ROAST_COUNT:  ClassVar[int] = 13
        PROFILE_GET:                 ClassVar[int] = 15
        PROFILE_SET:                 ClassVar[int] = 16
        SETTING_GET:                 ClassVar[int] = 17
        MACH_PROP_GET_SUPPORT_INFO:  ClassVar[int] = 23


        DEVICE_NAME_IKAWA:   ClassVar[str] = 'IKAWA'
        IKAWA_SERVICE_UUID:  ClassVar[str] = 'C92A6046-6C8D-4116-9D1D-D20A8F6A245F'
        IKAWA_SEND_CHAR_UUID: ClassVar[Tuple[str,BLE_CHAR_TYPE]] = ('851A4582-19C1-4E6C-AB37-E7A03766BA16', BLE_CHAR_TYPE.BLE_CHAR_WRITE) # type:ignore[reportPossibleUnboundVariable,unused-ignore]
        IKAWA_RECEIVE_CHAR_UUID: ClassVar[Tuple[str,BLE_CHAR_TYPE]] = ('948C5059-7F00-46D9-AC55-BF090AE066E3', BLE_CHAR_TYPE.BLE_CHAR_NOTIFY) # type:ignore[reportPossibleUnboundVariable,unused-ignore]


        def __init__(self,
                    connected_handler:Optional[Callable[[], None]] = None,
                    disconnected_handler:Optional[Callable[[], None]] = None) -> None:

            self.connected_handler:Optional[Callable[[], None]] = connected_handler
            self.disconnected_handler:Optional[Callable[[], None]] = disconnected_handler

            self.receiveMutex:QMutex = QMutex()
            self.dataReceived:QWaitCondition = QWaitCondition()
            self.receiveTimeout:int = 400

            self.log_data = False

            self.connected_state:bool = False

            self.TX:float = 0
            self.ET:float = -1
            self.BT:float = -1
            self.SP:float = -1
            self.RPM:float = -1 # fan speed in RPM
            self.heater:int = -1
            self.fan:int = -1
            self.state:int = -1
            self.absolute_humidity:float = -1
            self.humidity_roc:float = -1
            self.humidity_roc_dir:int = -1
            self.ambient_pressure:float = -1
            self.board_temp:float = -1
            # state is one of
            #  0: on-roaster (IDLE)
            #  1: pre-heating (START)
            #  2: ready-to-roast
            #  3: roasting
            #  4: roaster-is-busy (BUSY)
            #  5: cooling (DROP)
            #  6: doser-open (CHARGE)
            #  7: unexpected-problem (ERROR)
            #  8: ready-to-blow
            #  9: test-mode
            # 10: detecting
            # 11: development

            self.seq:Generator[int, None, None] = self.seqNum() # message sequence number generator

            self.ble:BleInterface = BleInterface(  # type:ignore[unused-ignore]
                [(IKAWA_BLE.IKAWA_SERVICE_UUID, [IKAWA_BLE.IKAWA_SEND_CHAR_UUID, IKAWA_BLE.IKAWA_RECEIVE_CHAR_UUID])],
                self.processData,
                sendStop = self.sendStop,
                connected = self.connected,
                #device_names = [ IKAWA_BLE.DEVICE_NAME_IKAWA ]
                )

            self.frame_char:Final[int]          = 126 # b'\x7e'
            self.escape_char:Final[int]         = 125 # b'\x7d'
            self.escape_offset:Final[int]       = 32
            self.frame_char_escaped:Final[int]  = self.frame_char - self.escape_offset # 94 = b'\x5e'
            self.escape_char_escaped:Final[int] = self.escape_char - self.escape_offset # 93 = b'\x5d'

            # either empty, or contains a partial payload incl. the beginning frame_char or contains the full payload incl. the beginning and ending frame_char
            self.rcv_buffer:Optional[bytes] = None

        @staticmethod
        def seqNum() -> Generator[int, None, None]:
            num = 1
            while True:
                yield num
                num = (num + 1) % 32767

        @staticmethod
        def crc16(bArr:bytes, i:int) -> bytes:
            for i2 in bArr:
                i3 = (i2 & 255) ^ (i & 255)
                i4 = i3 ^ ((i3 << 4) & 255)
                i = ((((i >> 8) & 255) | ((i4 << 8) & 65535)) ^ (i4 >> 4)) ^ ((i4 << 3) & 65535)
            return int(i & 65535).to_bytes(2, byteorder='big')

        def escape(self, msg:bytes) -> bytes:
            message:bytes = b''
            for i,_ in enumerate(msg):
                if msg[i] == self.escape_char:
                    message += self.escape_char.to_bytes(length=1, byteorder='big')
                    message += self.escape_char_escaped.to_bytes(length=1, byteorder='big')
                elif msg[i] == self.frame_char:
                    message += self.escape_char.to_bytes(length=1, byteorder='big')
                    message += self.frame_char_escaped.to_bytes(length=1, byteorder='big')
                else:
                    message += msg[i:i+1]
            return message

        def unescape(self, msg:bytes) -> bytes:
            unescaped_message = bytearray()
            i = 0
            while i < len(msg):
                if msg[i] == self.escape_char and len(msg)>i+1:
                    unescaped_message.append(msg[i + 1] + self.escape_offset)
                    i += 1 # skip one
                else:
                    unescaped_message.append(msg[i])
                i += 1
            return bytes(unescaped_message)

    #-----
        def clearData(self) -> None:
            self.ET = -1
            self.BT = -1
            self.SP = -1
            self.RPM = -1
            self.heater = -1
            self.fan = -1
            self.state = -1
            self.absolute_humidity = -1
            self.humidity_roc = -1
            self.humidity_roc_dir = -1
            self.ambient_pressure = -1
            self.board_temp = -1

        def reset(self) -> None:
            self.rcv_buffer = None

        def start(self, log_data:bool = False) -> None:
            self.log_data = log_data
            self.reset()
            # start BLE loop
            self.ble.deviceDisconnected.connect(self.ble_scan_failed)
            self.ble.scanDevices()

        def stop(self) -> None:
            # disconnect signals
            self.ble.deviceDisconnected.disconnect()
            self.ble.disconnectDevice()

        def ble_scan_failed(self) -> None:
            if self.ble is not None:
                QTimer.singleShot(200, self.ble.scanDevices)

        def processData(self, _write:Callable[[Optional[bytes]],None], data:bytes) -> Tuple[Optional[float], Optional[int]]:
            if len(data) > 0:
                try:
                    if self.rcv_buffer is None and data[0] == self.frame_char:
                        # we received the frame start
                        self.rcv_buffer = b''
                    if self.rcv_buffer is not None:
                        # add new data
                        self.rcv_buffer += data
                        if len(self.rcv_buffer)>3 and self.rcv_buffer[0] == self.frame_char and self.rcv_buffer[-1] == self.frame_char:
                            # we received a full frame
                            message = self.unescape(self.rcv_buffer[1:-1])
                            crc = message[-2:]
                            payload = message[:-2]
                            # clear the buffer
                            self.rcv_buffer = None
                            # log payload
                            if self.log_data:
                                _log.info('ikawa payload: %s',payload)
                            # verify CRC
                            if crc == self.crc16(payload, 65535):
                                try:
                                    decoded_message = IkawaCmd_pb2.IkawaResponse().FromString(payload) # pylint: disable=no-member
                                    if decoded_message.HasField('resp_mach_status_get_all'):
                                        _log.debug('IKAWA response.resp: %s (%s)', decoded_message.resp, decoded_message.MACH_STATUS_GET_ALL)
                                        status_get_all = decoded_message.resp_mach_status_get_all
                                        # temp below is Inlet Temperature on PRO machines and Exaust Temperature on HOME machines
                                        if status_get_all.HasField('temp_below'):
                                            self.ET = status_get_all.temp_below / 10
                                        elif status_get_all.HasField('temp_below_filtered'):
                                            self.ET = status_get_all.temp_below_filtered / 10
                                        else:
                                            self.ET = -1
                                        if status_get_all.HasField('temp_above'):
                                            self.BT = status_get_all.temp_above / 10
                                        elif status_get_all.HasField('temp_above_filtered'):
                                            self.BT = status_get_all.temp_above_filtered / 10
                                        else:
                                            self.BT = -1
                                        if status_get_all.HasField('setpoint'):
                                            self.SP = status_get_all.setpoint / 10
                                        else:
                                            self.SP = -1
                                        if status_get_all.HasField('fan_measured'):
                                            self.RPM = (status_get_all.fan_measured / 12)*60 # RPM
                                        else:
                                            self.RPM = -1
                                        self.heater = status_get_all.heater * 2
                                        self.fan = int(round(status_get_all.fan / 2.55))
                                        self.state = status_get_all.state
                                        # compute the average of all received ambient pressure readings (in mbar)
                                        if status_get_all.HasField('pressure_amb'):
                                            self.ambient_pressure = (status_get_all.pressure_amb if self.ambient_pressure == -1 else (self.ambient_pressure + status_get_all.pressure_amb)/2)
                                        # add absolute humidity in g/m^3
                                        if status_get_all.HasField('humidity_abs'):
                                            self.absolute_humidity = status_get_all.humidity_abs / 100
                                        else:
                                            self.absolute_humidity = -1
                                        # add humidity RoC in (g/m^3)/min
                                        if status_get_all.HasField('humidity_roc'):
                                            self.humidity_roc = status_get_all.humidity_roc / 10
                                        else:
                                            self.humidity_roc = -1
                                        # add humidity RoC direction (1: down, 2: up)
                                        if status_get_all.HasField('humidity_roc_direction'):
                                            self.humidity_roc_dir = int(status_get_all.humidity_roc_direction)
                                        else:
                                            self.humidity_roc_dir = -1
                                        # add board temperature in C
                                        if status_get_all.HasField('board_temp'):
                                            self.board_temp = status_get_all.board_temp / 10
                                        else:
                                            self.board_temp = -1
                                        # add data received and registered, enable delivery
                                        self.dataReceived.wakeAll()
                                except Exception as e: # pylint: disable=broad-except
                                    _log.error(e)
                            else:
                                _log.debug('processData() CRC check failed')
                except Exception as e:  # pylint: disable=broad-except
                    _log.error(e)
            return None, None

        def connected(self) -> None:
            self.connected_state = True
            if self.connected_handler is not None:
                self.connected_handler()

        def sendStop(self, _write:Callable[[Optional[bytes]],None]) -> None:
            self.connected_state = False
            if self.disconnected_handler is not None:
                self.disconnected_handler()

    #-----

        def requestDataMessage(self) -> bytes:
            message = IkawaCmd_pb2.Message() # pylint: disable=no-member
            message.cmd_type = IKAWA_BLE.MACH_STATUS_GET_ALL_VALUE
            message.seq = next(self.seq)
            msg = message.SerializeToString()
            crc = self.crc16(msg, 65535)
            return self.frame_char.to_bytes(length=1, byteorder='big') + self.escape(msg + crc) + self.frame_char.to_bytes(length=1, byteorder='big')

        def getData(self) -> None:
            if self.connected_state:
                request_data = self.requestDataMessage()
                self.ble.write(request_data)
                # wait for data to be delivered
                self.receiveMutex.lock()
                res = self.dataReceived.wait(self.receiveMutex, self.receiveTimeout)
                if not res:
                    # timeout, no data received
                    self.clearData()
                self.receiveMutex.unlock()
except Exception:  # pylint: disable=broad-except
    pass
