#
# ABOUT
# Aillio support for Artisan

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
# Rui Paulo, 2023

import time
import random
from struct import unpack
from multiprocessing import Pipe
import threading
from platform import system
import usb.core # type: ignore[import-untyped]
import usb.util # type: ignore[import-untyped]

import array

if system().startswith('Windows'):
    import libusb_package # pyright:ignore[reportMissingImports] # pylint: disable=import-error

#import requests
#from requests_file import FileAdapter # type: ignore # @UnresolvedImport
#import json
#from lxml import html # unused

import logging
from typing import Final, Optional, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    try:
        from multiprocessing.connection import PipeConnection as Connection # type: ignore[unused-ignore,attr-defined,assignment] # pylint: disable=unused-import
    except ImportError:
        from multiprocessing.connection import Connection # type: ignore[unused-ignore,attr-defined,assignment] # pylint: disable=unused-import
#    from artisanlib.types import ProfileData # pylint: disable=unused-import
#    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import

#try:
#    from PyQt6.QtCore import QDateTime, Qt # @UnusedImport @Reimport  @UnresolvedImport
#except ImportError:
#    from PyQt5.QtCore import QDateTime, Qt # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

#from artisanlib.util import weight_units


_log: Final[logging.Logger] = logging.getLogger(__name__)


def _load_library(find_library:Any = None) -> Any:
    import usb.libloader # type: ignore[import-untyped, unused-ignore] # pylint: disable=redefined-outer-name
    return usb.libloader.load_locate_library(
                ('usb-1.0', 'libusb-1.0', 'usb'),
                'cygusb-1.0.dll', 'Libusb 1',
                find_library=find_library, check_symbols=('libusb_init',))

class AillioR1:
    AILLIO_VID = 0x0483
    AILLIO_PID = 0x5741
    AILLIO_PID_REV3 = 0xa27e
    AILLIO_ENDPOINT_WR = 0x3
    AILLIO_ENDPOINT_RD = 0x81
    AILLIO_INTERFACE = 0x1
    AILLIO_CONFIGURATION = 0x1
    AILLIO_DEBUG = 1
    AILLIO_CMD_INFO1 = [0x30, 0x02]
    AILLIO_CMD_INFO2 = [0x89, 0x01]
    AILLIO_CMD_STATUS1 = [0x30, 0x01]
    AILLIO_CMD_STATUS2 = [0x30, 0x03]
    AILLIO_CMD_PRS = [0x30, 0x01, 0x00, 0x00]
    AILLIO_CMD_HEATER_INCR = [0x34, 0x01, 0xaa, 0xaa]
    AILLIO_CMD_HEATER_DECR = [0x34, 0x02, 0xaa, 0xaa]
    AILLIO_CMD_FAN_INCR = [0x31, 0x01, 0xaa, 0xaa]
    AILLIO_CMD_FAN_DECR = [0x31, 0x02, 0xaa, 0xaa]
    AILLIO_STATE_OFF = 0x00
    AILLIO_STATE_PH = 0x02
    AILLIO_STATE_CHARGE = 0x04
    AILLIO_STATE_ROASTING = 0x06
    AILLIO_STATE_COOLING = 0x08
    AILLIO_STATE_SHUTDOWN = 0x09

    def __init__(self, debug:bool = False) -> None:
        self.simulated = False
        self.AILLIO_DEBUG = debug
        self.__dbg('init')
        self.usbhandle:Optional[usb.core.Device] = None # type:ignore[no-any-unimported,unused-ignore]
        self.bt:float = 0
        self.dt:float = 0
        self.heater:float = 0
        self.fan:float = 0
        self.bt_ror:float = 0
        self.drum:float = 0
        self.voltage:float = 0
        self.exitt:float = 0
        self.state_str:str = ''
        self.r1state:int = 0
        self.worker_thread:Optional[threading.Thread] = None
        self.worker_thread_run = True
        self.roast_number:int = -1
        self.fan_rpm:float = 0

        self.parent_pipe:Optional[Connection] = None # type:ignore[no-any-unimported,unused-ignore]
        self.child_pipe:Optional[Connection] = None # type:ignore[no-any-unimported,unused-ignore]
        self.irt:float = 0
        self.pcbt:float = 0
        self.coil_fan:int = 0
        self.coil_fan2:int = 0
        self.pht:int = 0
        self.minutes = 0
        self.seconds = 0

    def __del__(self) -> None:
        if not self.simulated:
            self.__close()

    def __dbg(self, msg:str) -> None:
        if self.AILLIO_DEBUG and not self.simulated:
            try:
                print('AillioR1: ' + msg)
            except OSError:
                pass

    def __open(self) -> None:
        if self.simulated:
            return
        if self.usbhandle is not None:
            return
        if not system().startswith('Windows'):
            backend = None

            if system().startswith('Linux'):
                # we prefer a system installed libusb-1.0 shared lib if available on Linux (incl. RPi),
                # especially since libusb-1.0.so is from removed from the AppImage installer
                # if we could not find one, backend remains None and pyusb is searching for a backend
                # within the app bundle
                # on macOS libusb is never pre-installed thus we always take the bundled one
                import os
                for shared_libusb_path in [
                        '/usr/lib/x86_64-linux-gnu/libusb-1.0.so',
                        '/usr/lib/x86_64-linux-gnu/libusb-1.0.so.0',
                        '/usr/lib/aarch64-linux-gnu/libusb-1.0.so'
                        '/usr/lib/aarch64-linux-gnu/libusb-1.0.so.0']:
                    if os.path.isfile(shared_libusb_path):
                        import usb.backend.libusb1 as libusb10 # type: ignore[import-untyped, unused-ignore]
                        libusb10._load_library = _load_library # pylint: disable=protected-access # overwrite the overwrite of the pyinstaller runtime hook pyi_rth_usb.py
                        from usb.backend.libusb1 import get_backend  # type: ignore[import-untyped, unused-ignore]
                        backend = get_backend(find_library=lambda _,shared_libusb_path=shared_libusb_path: shared_libusb_path)
                        break
            self.usbhandle = usb.core.find(idVendor=self.AILLIO_VID,
                                           idProduct=self.AILLIO_PID, backend=backend)
            if self.usbhandle is None:
                self.usbhandle = usb.core.find(idVendor=self.AILLIO_VID,
                                               idProduct=self.AILLIO_PID_REV3, backend=backend)
        else:
            self.usbhandle = libusb_package.find(idVendor=self.AILLIO_VID, # pyright:ignore[reportPossiblyUnboundVariable] # pylint: disable=possibly-used-before-assignment
                                                 idProduct=self.AILLIO_PID)
            if self.usbhandle is None:
                self.usbhandle = libusb_package.find(idVendor=self.AILLIO_VID, # pyright:ignore[reportPossiblyUnboundVariable] # pylint: disable=possibly-used-before-assignment
                                                     idProduct=self.AILLIO_PID_REV3)
        if self.usbhandle is None:
            raise OSError('not found or no permission')
        self.__dbg('device found!')
        if not system().startswith('Windows') and self.usbhandle.is_kernel_driver_active(self.AILLIO_INTERFACE):
            try:
                self.usbhandle.detach_kernel_driver(self.AILLIO_INTERFACE)
            except Exception: # pylint: disable=broad-except
                pass
                # detach fails on libusb 1.0.26 and newer on macOS >v12 if not running under sudo and seems not to be needed on those configurations
#                self.usbhandle = None
#                raise OSError('unable to detach kernel driver') from e
        try:
            config = self.usbhandle.get_active_configuration()
            if config.bConfigurationValue != self.AILLIO_CONFIGURATION:
                self.usbhandle.set_configuration(configuration=self.AILLIO_CONFIGURATION)
        except Exception as e:  # pylint: disable=broad-except
            self.usbhandle = None
            raise OSError('unable to configure') from e

        try:
            usb.util.claim_interface(self.usbhandle, self.AILLIO_INTERFACE)
        except Exception as e:  # pylint: disable=broad-except
            self.usbhandle = None
            raise OSError('unable to claim interface') from e
        self.__sendcmd(self.AILLIO_CMD_INFO1)
        reply = self.__readreply(32)
        sn = unpack('h', reply[0:2])[0]
        firmware = unpack('h', reply[24:26])[0]
        self.__dbg('serial number: ' + str(sn))
        self.__dbg('firmware version: ' + str(firmware))
        self.__sendcmd(self.AILLIO_CMD_INFO2)
        reply = self.__readreply(36)
        self.roast_number = unpack('>I', reply[27:31])[0]
        self.__dbg('number of roasts: ' + str(self.roast_number))
        self.parent_pipe, self.child_pipe = Pipe()
        self.worker_thread = threading.Thread(target=self.__updatestate,
                                              args=(self.child_pipe,))
        if self.worker_thread is not None:
            self.worker_thread.start()

    def __close(self) -> None:
        if self.simulated:
            return
        if self.usbhandle is not None:
            try:
                usb.util.release_interface(self.usbhandle,
                                           self.AILLIO_INTERFACE)
                usb.util.dispose_resources(self.usbhandle)
            except Exception: # pylint: disable=broad-except
                pass
            self.usbhandle = None

        if self.worker_thread:
            self.worker_thread_run = False
            self.worker_thread.join()
            if self.parent_pipe is not None:
                self.parent_pipe.close()
            if self.child_pipe is not None:
                self.child_pipe.close()
            self.worker_thread = None

    def get_roast_number(self) -> int:
        self.__getstate()
        return self.roast_number

    def get_bt(self) -> float:
        self.__getstate()
        return self.bt

    def get_dt(self) -> float:
        self.__getstate()
        return self.dt

    def get_heater(self) -> float:
        self.__dbg('get_heater')
        self.__getstate()
        return self.heater

    def get_fan(self) -> float:
        self.__dbg('get_fan')
        self.__getstate()
        return self.fan

    def get_fan_rpm(self) -> float:
        self.__dbg('get_fan_rpm')
        self.__getstate()
        return self.fan_rpm

    def get_drum(self) -> float:
        self.__getstate()
        return self.drum

    def get_voltage(self) -> float:
        self.__getstate()
        return self.voltage

    def get_bt_ror(self) -> float:
        self.__getstate()
        return self.bt_ror

    def get_exit_temperature(self) -> float:
        self.__getstate()
        return self.exitt

    def get_state_string(self) -> str:
        self.__getstate()
        return self.state_str

    def get_state(self) -> int:
        self.__getstate()
        return self.r1state

    def set_heater(self, value:float) -> None:
        self.__dbg('set_heater ' + str(value))
        value = int(value)
        if value < 0:
            value = 0
        elif value > 9:
            value = 9
        h = self.get_heater()
        d = abs(h - value)
        if d <= 0:
            return
        d = int(float(min(d,9)))
        if h > value:
            if self.parent_pipe is not None:
                for _ in range(d):
                    self.parent_pipe.send(self.AILLIO_CMD_HEATER_DECR)
        elif self.parent_pipe is not None:
            for _ in range(d):
                self.parent_pipe.send(self.AILLIO_CMD_HEATER_INCR)
        self.heater = value

    def set_fan(self, value:float) -> None:
        self.__dbg('set_fan ' + str(value))
        value = int(value)
        if value < 1:
            value = 1
        elif value > 12:
            value = 12
        f = self.get_fan()
        d = abs(f - value)
        if d <= 0:
            return
        d = int(round(min(d,11)))
        if f > value:
            if self.parent_pipe is not None:
                for _ in range(d):
                    self.parent_pipe.send(self.AILLIO_CMD_FAN_DECR)
        elif self.parent_pipe is not None:
            for _ in range(d):
                self.parent_pipe.send(self.AILLIO_CMD_FAN_INCR)
        self.fan = value

    def set_drum(self, value:float) -> None:
        self.__dbg('set_drum ' + str(value))
        value = int(value)
        if value < 1:
            value = 1
        elif value > 9:
            value = 9
        if self.parent_pipe is not None:
            self.parent_pipe.send([0x32, 0x01, value, 0x00])
        self.drum = value

    def prs(self) -> None:
        self.__dbg('PRS')
        if self.parent_pipe is not None:
            self.parent_pipe.send(self.AILLIO_CMD_PRS)

    def __updatestate(self, p:'Connection') -> None: # type:ignore[no-any-unimported,unused-ignore]
        while self.worker_thread_run:
            state1:array.array[int] = array.array('B', bytes(0)) # pylint: disable=unsubscriptable-object
            state2:array.array[int] = array.array('B', bytes(0)) # pylint: disable=unsubscriptable-object
            try:
                self.__dbg('updatestate')
                self.__sendcmd(self.AILLIO_CMD_STATUS1)
                state1 = self.__readreply(64)
                self.__sendcmd(self.AILLIO_CMD_STATUS2)
                state2 = self.__readreply(64)
            except Exception: # pylint: disable=broad-except
                pass
            if p.poll():
                cmd = p.recv()
                self.__sendcmd(cmd)
            if len(state1) + len(state2) == 128:
                p.send(state1 + state2)
            time.sleep(0.1)

    def __getstate(self) -> None:
        self.__dbg('getstate')
        if self.simulated:
            if random.random() > 0.05:
                return
            self.bt += random.random()
            self.bt_ror += random.random()
            self.dt += random.random()
            self.exitt += random.random()
            self.fan = random.random() * 10
            self.heater = random.random() * 8
            self.drum = random.random() * 8
            self.irt = random.random()
            self.pcbt = random.random()
            self.fan_rpm += random.random()
            self.voltage = 240
            self.coil_fan = 0
            self.coil_fan2 = 0
            self.pht = 0
            self.r1state = self.AILLIO_STATE_ROASTING
            self.state_str = 'roasting'
            return
        self.__open()
        if self.parent_pipe is None or not self.parent_pipe.poll():
            return
        state = self.parent_pipe.recv()
        valid = state[41]
        # Heuristic to find out if the data is valid
        # It looks like we get a different message every 15 seconds
        # when we're not roasting.  Ignore this message for now.
        if valid == 10:
            self.bt = round(unpack('f', state[0:4])[0], 1)
            self.bt_ror = round(unpack('f', state[4:8])[0], 1)
            self.dt = round(unpack('f', state[8:12])[0], 1)
            self.exitt = round(unpack('f', state[16:20])[0], 1)
            self.minutes = state[24]
            self.seconds = state[25]
            self.fan = state[26]
            self.heater = state[27]
            self.drum = state[28]
            self.r1state = state[29]
            self.irt = round(unpack('f', state[32:36])[0], 1)
            self.pcbt = round(unpack('f', state[36:40])[0], 1)
            self.fan_rpm = unpack('h', state[44:46])[0]
            self.voltage = unpack('h', state[48:50])[0]
            self.coil_fan = round(unpack('i', state[52:56])[0], 1)
            self.__dbg('BT: ' + str(self.bt))
            self.__dbg('BT RoR: ' + str(self.bt_ror))
            self.__dbg('DT: ' + str(self.dt))
            self.__dbg('exit temperature ' + str(self.exitt))
            self.__dbg('PCB temperature: ' + str(self.irt))
            self.__dbg('IR temperature: ' + str(self.pcbt))
            self.__dbg('voltage: ' + str(self.voltage))
            self.__dbg('coil fan: ' + str(self.coil_fan))
            self.__dbg('fan: ' + str(self.fan))
            self.__dbg('heater: ' + str(self.heater))
            self.__dbg('drum speed: ' + str(self.drum))
            self.__dbg('time: ' + str(self.minutes) + ':' + str(self.seconds))

        state = state[64:]
        self.coil_fan2 = round(unpack('i', state[32:36])[0], 1)
        self.pht = unpack('H', state[40:42])[0]
        self.__dbg('pre-heat temperature: ' + str(self.pht))
        if self.r1state == self.AILLIO_STATE_OFF:
            self.state_str = 'off'
        elif self.r1state == self.AILLIO_STATE_PH:
            self.state_str = 'pre-heating to ' + str(self.pht) + 'C'
        elif self.r1state == self.AILLIO_STATE_CHARGE:
            self.state_str = 'charge'
        elif self.r1state == self.AILLIO_STATE_ROASTING:
            self.state_str = 'roasting'
        elif self.r1state == self.AILLIO_STATE_COOLING:
            self.state_str = 'cooling'
        elif self.r1state == self.AILLIO_STATE_SHUTDOWN:
            self.state_str = 'shutdown'
        self.__dbg('state: ' + self.state_str)
        self.__dbg('second coil fan: ' + str(self.coil_fan2))

    def __sendcmd(self, cmd:List[int]) -> None:
        self.__dbg('sending command: ' + str(cmd))
        if self.usbhandle is not None:
            self.usbhandle.write(self.AILLIO_ENDPOINT_WR, cmd)

    def __readreply(self, length:int) -> Any:
        if self.usbhandle is not None:
            return self.usbhandle.read(self.AILLIO_ENDPOINT_RD, length)
        raise OSError('not found or no permission')

#def extractProfileBulletDict(data:Dict, aw:'ApplicationWindow') -> 'ProfileData':
#    try:
#        res:'ProfileData' = {} # the interpreted data set
#
#        if 'celsius' in data and not data['celsius']:
#            res['mode'] = 'F'
#        else:
#            res['mode'] = 'C'
#        if 'comments' in data:
#            res['roastingnotes'] = data['comments']
#        try:
#            if 'dateTime' in data:
#                try:
#                    dateQt = QDateTime.fromString(data['dateTime'],Qt.DateFormat.ISODate) # RFC 3339 date time
#                except Exception: # pylint: disable=broad-except
#                    dateQt = QDateTime.fromMSecsSinceEpoch (data['dateTime'])
#                if dateQt.isValid():
#                    roastdate:Optional[str] = encodeLocal(dateQt.date().toString())
#                    if roastdate is not None:
#                        res['roastdate'] = roastdate
#                    roastisodate:Optional[str] = encodeLocal(dateQt.date().toString(Qt.DateFormat.ISODate))
#                    if roastisodate is not None:
#                        res['roastisodate'] = roastisodate
#                    roasttime:Optional[str] = encodeLocal(dateQt.time().toString())
#                    if roasttime is not None:
#                        res['roasttime'] = roasttime
#                    res['roastepoch'] = int(dateQt.toSecsSinceEpoch())
#                    res['roasttzoffset'] = time.timezone
#        except Exception as e: # pylint: disable=broad-except
#            _log.exception(e)
#        try:
#            res['title'] = data['beanName']
#        except Exception: # pylint: disable=broad-except
#            pass
#        if 'roastName' in data:
#            res['title'] = data['roastName']
#        try:
#            if 'roastNumber' in data:
#                res['roastbatchnr'] = int(data['roastNumber'])
#        except Exception: # pylint: disable=broad-except
#            pass
#        if 'beanName' in data:
#            res['beans'] = data['beanName']
#        elif 'bean' in data and 'beanName' in data['bean']:
#            res['beans'] = data['bean']['beanName']
#        try:
#            if 'weightGreen' in data or 'weightRoasted' in data:
#                wunit = weight_units.index(aw.qmc.weight[2])
#                if wunit in {1,3}: # turn Kg into g, and lb into oz
#                    wunit = wunit -1
#                wgreen:float = 0
#                if 'weightGreen' in data:
#                    wgreen = float(data['weightGreen'])
#                wroasted:float = 0
#                if 'weightRoasted' in data:
#                    wroasted = float(data['weightRoasted'])
#                res['weight'] = [wgreen,wroasted,weight_units[wunit]]
#        except Exception: # pylint: disable=broad-except
#            pass
#        try:
#            if 'agtron' in data:
#                res['ground_color'] = int(round(data['agtron']))
#                if 'Agtron' in aw.qmc.color_systems:
#                    res['color_system'] = 'Agtron'
#        except Exception: # pylint: disable=broad-except
#            pass
#        try:
#            if 'roastMasterName' in data:
#                res['operator'] = data['roastMasterName']
#        except Exception: # pylint: disable=broad-except
#            pass
#        res['roastertype'] = 'Aillio Bullet R1'
#
#        if 'ambient' in data:
#            res['ambientTemp'] = data['ambient']
#        if 'humidity' in data:
#            res['ambient_humidity'] = data['humidity']
#
#        bt = data.get('beanTemperature', [])
#        dt = data.get('drumTemperature', [])
#        # make dt the same length as bt
#        dt = dt[:len(bt)]
#        dt.extend(-1 for _ in range(len(bt) - len(dt)))
#
#        et = data.get('exitTemperature', None)
#        if et is not None:
#            # make et the same length as bt
#            et = et[:len(bt)]
#            et.extend(-1 for _ in range(len(bt) - len(et)))
#
#        ror = data.get('beanDerivative', None)
#        if ror is not None:
#            # make et the same length as bt
#            ror = ror[:len(bt)]
#            ror.extend(-1 for _ in range(len(bt) - len(ror)))
#
#        sr = data.get('sampleRate', 2.)
#        res['samplinginterval'] = 1.0/sr
#        tx = [x/sr for x in range(len(bt))]
#        res['timex'] = tx
#        res['temp1'] = dt
#        res['temp2'] = bt
#
#        timeindex = [-1,0,0,0,0,0,0,0]
#        if 'roastStartIndex' in data:
#            timeindex[0] = min(max(data['roastStartIndex'],0),len(tx)-1)
#        else:
#            timeindex[0] = 0
#
#        labels = ['indexYellowingStart','indexFirstCrackStart','indexFirstCrackEnd','indexSecondCrackStart','indexSecondCrackEnd']
#        for i in range(1,6):
#            try:
#                idx = data[labels[i-1]]
#                # RoastTime seems to interpret all index values 1 based, while Artisan takes the 0 based approach. We substruct 1
#                if idx > 1:
#                    timeindex[i] = max(min(idx - 1,len(tx)-1),0)
#            except Exception: # pylint: disable=broad-except
#                pass
#
#        if 'roastEndIndex' in data:
#            timeindex[6] = max(0,min(data['roastEndIndex'],len(tx)-1))
#        else:
#            timeindex[6] = max(0,len(tx)-1)
#        res['timeindex'] = timeindex
#
#        # extract events from newer JSON format
#        specialevents = []
#        specialeventstype = []
#        specialeventsvalue = []
#        specialeventsStrings = []
#
#        # extract events from older JSON format
#        try:
#            eventtypes = ['blowerSetting','drumSpeedSetting','--','inductionPowerSetting']
#            for j, eventname in enumerate(eventtypes):
#                if eventname != '--' and eventname in data:
#                    last:Optional[float] = None
#                    ip = data[eventname]
#                    for i, _ in enumerate(ip):
#                        v = ip[i]+1
#                        if last is None or last != v:
#                            specialevents.append(i)
#                            specialeventstype.append(j)
#                            specialeventsvalue.append(v)
#                            specialeventsStrings.append('')
#                            last = v
#        except Exception as e: # pylint: disable=broad-except
#            _log.exception(e)
#
#        # extract events from newer JSON format
#        try:
#            for action in data['actions']['actionTimeList']:
#                time_idx = action['index'] - 1
#                value = action['value'] + 1
#                event_type = None
#                if action['ctrlType'] == 0:
#                    event_type = 3
#                elif action['ctrlType'] == 1:
#                    event_type = 0
#                elif action['ctrlType'] == 2:
#                    event_type = 1
#                if event_type is not None:
#                    specialevents.append(time_idx)
#                    specialeventstype.append(event_type)
#                    specialeventsvalue.append(value)
#                    specialeventsStrings.append(str(value))
#        except Exception as e: # pylint: disable=broad-except
#            _log.exception(e)
#        if len(specialevents) > 0:
#            res['specialevents'] = specialevents
#            res['specialeventstype'] = specialeventstype
#            res['specialeventsvalue'] = specialeventsvalue
#            res['specialeventsStrings'] = specialeventsStrings
#
#        if (ror is not None and len(ror) == len(tx)) or (et is not None and len(et) == len(tx)):
#            # add one (virtual) extra device
#            res['extradevices'] = [25]
#            res['extratimex'] = [tx]
#
#            temp3_visibility = True
#            temp4_visibility = False
#            if et is not None and len(et) == len(tx):
#                res['extratemp1'] = [et]
#            else:
#                res['extratemp1'] = [[-1]*len(tx)]
#                temp3_visibility = False
#            if ror is not None and len(ror) == len(tx):
#                res['extratemp2'] = [ror]
#            else:
#                res['extratemp2'] = [[-1]*len(tx)]
#                temp4_visibility = False
#            res['extraname1'] = ['Exhaust']
#            res['extraname2'] = ['RoR']
#            res['extramathexpression1'] = ['']
#            res['extramathexpression2'] = ['']
#            res['extraLCDvisibility1'] = [temp3_visibility]
#            res['extraLCDvisibility2'] = [temp4_visibility]
#            res['extraCurveVisibility1'] = [temp3_visibility]
#            res['extraCurveVisibility2'] = [temp4_visibility]
#            res['extraDelta1'] = [False]
#            res['extraDelta2'] = [True]
#            res['extraFill1'] = [False]
#            res['extraFill2'] = [False]
#            res['extradevicecolor1'] = ['black']
#            res['extradevicecolor2'] = ['black']
#            res['extramarkersizes1'] = [6.0]
#            res['extramarkersizes2'] = [6.0]
#            res['extramarkers1'] = ['None']
#            res['extramarkers2'] = ['None']
#            res['extralinewidths1'] = [aw.qmc.extra_linewidth_default]
#            res['extralinewidths2'] = [aw.qmc.extra_linewidth_default]
#            res['extralinestyles1'] = [aw.qmc.linestyle_default]
#            res['extralinestyles2'] = [aw.qmc.linestyle_default]
#            res['extradrawstyles1'] = [aw.qmc.drawstyle_default]
#            res['extradrawstyles2'] = [aw.qmc.drawstyle_default]
#
#        return res
#    except Exception as e: # pylint: disable=broad-except
#        _log.exception(e)
#        return {}

#def extractProfileRoastWorld(url:'QUrl', aw:'ApplicationWindow') -> Optional['ProfileData']:
#    s = requests.Session()
#    s.mount('file://', FileAdapter())
#    page = s.get(url.toString(), timeout=(4, 15), headers={'Accept-Encoding' : 'gzip'})
#    tree = html.fromstring(page.content)_
#    data = tree.xpath('//body/script[1]/text()')
#    data = data[0].split('gon.profile=')
#    data = data[1].split(';')
#    res = extractProfileBulletDict(json.loads(data[0]),aw)
#    if 'beans' not in res:
#        try:
#            b = tree.xpath("//div[*='Bean']/*/a/text()")
#            if b:
#                res['beans'] = b[0]
#        except Exception: # pylint: disable=broad-except
#            pass
#    return res

#def extractProfileRoasTime(file, aw:'ApplicationWindow') -> 'ProfileData':
#    with open(file, encoding='utf-8') as infile:
#        data = json.load(infile)
#    return extractProfileBulletDict(data, aw)

if __name__ == '__main__':
    R1 = AillioR1(debug=True)
    while True:
        R1.get_heater()
        time.sleep(0.1)
