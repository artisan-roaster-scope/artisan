#!/usr/bin/env python3

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
# mikefsq, r2 update 2025

import time
import random
from struct import unpack
from multiprocessing import Pipe
import threading
from platform import system
import usb.core # type: ignore[import-untyped]
import usb.util # type: ignore[import-untyped]
import json

if system().startswith('Windows'):
    import libusb_package # pyright:ignore[reportMissingImports] # pylint: disable=import-error

#import requests
#from requests_file import FileAdapter # type: ignore # @UnresolvedImport
#import json
#from lxml import html # unused

import logging
from typing import Final, Optional, List, Union, TypedDict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    try:
        from multiprocessing.connection import PipeConnection as Connection # type: ignore[unused-ignore,attr-defined,assignment] # pylint: disable=unused-import
    except ImportError:
        from multiprocessing.connection import Connection # type: ignore[unused-ignore,attr-defined,assignment] # pylint: disable=unused-import
#    from artisanlib.atypes import ProfileData # pylint: disable=unused-import
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

class DEVICE_VARIANT(TypedDict):
    vid: int
    pid: int
    protocol: int
    model: str

class AillioR1:
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
    AILLIO_CMD_DRUM_INCR = [0x32, 0x01, 0xaa, 0xaa]
    AILLIO_CMD_DRUM_DECR = [0x32, 0x02, 0xaa, 0xaa]
    AILLIO_CMD_FAN_INCR = [0x31, 0x01, 0xaa, 0xaa]
    AILLIO_CMD_FAN_DECR = [0x31, 0x02, 0xaa, 0xaa]

    AILLIO_STATE_OFF = 0x00
    AILLIO_STATE_PH = 0x02
    AILLIO_STATE_STABILIZING = 0x03
    AILLIO_STATE_READY_TO_ROAST = 0x04
    AILLIO_STATE_CHARGE = 0x04
    AILLIO_STATE_ROASTING = 0x06
    AILLIO_STATE_COOLDOWN = 0x07
    AILLIO_STATE_COOLING = 0x08
    AILLIO_STATE_SHUTDOWN = 0x09
    AILLIO_STATE_BACK_TO_BACK = 0x08
    AILLIO_STATE_POWER_ON_RESET = 0x0B

	# sequence of valid states in PRS Button sequence
    VALID_STATES = [
            AILLIO_STATE_OFF,
            AILLIO_STATE_PH,
            AILLIO_STATE_CHARGE,
            AILLIO_STATE_ROASTING,
            AILLIO_STATE_COOLDOWN
    ]

    FRAME_TYPES = {
        0xA0: 'Temperature Frame',
        0xA1: 'Fan Control Frame',
        0xA2: 'Power Frame',
        0xA3: 'A3 Frame',
        0xA4: 'A4 Frame',
    }

    FRAME_SIZE = 64

    def __init__(self, debug:bool = False) -> None:
        self.simulated:bool = False
        self.AILLIO_DEBUG = debug
        self.__dbg('init')
        self.usbhandle:Optional[usb.core.Device] = None # type:ignore[no-any-unimported,unused-ignore]
        self.protocol:int = 1
        self.model:str = 'Unknown'
        self.ep_in = None
        self.ep_out = None
        self.TIMEOUT:int = 1000  # USB timeout in milliseconds
        self.MAX_PACKET_SIZE:int = 64  # Standard USB packet size

        # Device variants
        self.DEVICE_VARIANTS:List[DEVICE_VARIANT] = [
            {'vid': 0x0483, 'pid': 0x5741, 'protocol': 1, 'model': 'Aillio Bullet R1'},
            {'vid': 0x0483, 'pid': 0xa27e, 'protocol': 1, 'model': 'Aillio Bullet R1 IrBts'},
            {'vid': 0x0483, 'pid': 0xa4cd, 'protocol': 2, 'model': 'Aillio Bullet R2'},
        ]

        # Common fields
        self.bt:float = 0
        self.dt:float = 0
        self.heater:float = 0
        self.fan:float = 0
        self.bt_ror:float = 0
        self.dt_ror:float = 0
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

        # R2 specific fields
        self.ibts_bean_temp:float = 0
        self.ibts_bean_temp_rate:float = 0
        self.ibts_ambient_temp:float = 0
        self.bean_probe_temp:float = 0
        self.bean_probe_temp_rate:float = 0
        self.energy_used_this_roast:float = 0
        self.differential_air_pressure:float = 0
        self.inlet_air_temp:float = 0
        self.hot_air_temp:float = 0
        self.absolute_atmospheric_pressure:float = 0
        self.humidity_roaster:float = 0
        self.humidity_temp:float = 0
        self.button_crack_mark:int = 0
        self.roasting_method:int = 0
        self.fc_sample_index:int = 0
        self.fc_number_cracks:int = 0
        self.samples_in_fifo:int = 0
        self.sample_number:int = 0
        self.error_counts:int = 0
        self.active_power:float = 0
        self.reactive_power:float = 0
        self.apparent_power:float = 0
        self.current_rms:float = 0

    def __del__(self) -> None:
        if not self.simulated:
            self._close_port()

    def __dbg(self, msg:str) -> None:
        if self.AILLIO_DEBUG and not self.simulated:
            try:
                print(f'AillioR1: {msg}')
            except OSError:
                pass

    def _open_port(self) -> None:
        if self.simulated:
            return
        if self.usbhandle is not None:
            return

        if not system().startswith('Windows'):
            backend = None

            if system().startswith('Linux'):
                import os
                for shared_libusb_path in [
                        '/usr/lib/x86_64-linux-gnu/libusb-1.0.so',
                        '/usr/lib/x86_64-linux-gnu/libusb-1.0.so.0',
                        '/usr/lib/aarch64-linux-gnu/libusb-1.0.so'
                        '/usr/lib/aarch64-linux-gnu/libusb-1.0.so.0']:
                    if os.path.isfile(shared_libusb_path):
                        import usb.backend.libusb1 as libusb10  # type: ignore[import-untyped, unused-ignore]
                        libusb10._load_library = _load_library  # pylint: disable=protected-access # overwrite the overwrite of the pyinstaller runtime hook pyi_rth_usb.py
                        from usb.backend.libusb1 import get_backend  # type: ignore[import-untyped, unused-ignore]
                        backend = get_backend(find_library=lambda _,shared_libusb_path=shared_libusb_path: shared_libusb_path)
                        break

            # Try each known device variant
            for variant in self.DEVICE_VARIANTS:
                self.usbhandle = usb.core.find(idVendor=variant['vid'],
                                            idProduct=variant['pid'],
                                            backend=backend)
                if self.usbhandle is not None:
                    self.protocol = variant['protocol']
                    self.model = variant['model']
                    break
        else:
            # Windows handling
            for variant in self.DEVICE_VARIANTS:
                self.usbhandle = libusb_package.find(idVendor=variant['vid'], # pyright:ignore[reportPossiblyUnboundVariable] # pylint: disable=possibly-used-before-assignment
                                                idProduct=variant['pid'])
                if self.usbhandle is not None:
                    self.protocol = variant['protocol']
                    self.model = variant['model']
                    break

        if self.usbhandle is None:
            raise OSError('not found or no permission')

        self.__dbg(f'device found! {self.model} using protocol V{self.protocol}')

        try:
            try:
                self.usbhandle.reset()
            except Exception as e: # pylint: disable=broad-except
                self.__dbg(f'Warning: Could not reset device: {str(e)}')

            if not system().startswith('Windows') and self.usbhandle.is_kernel_driver_active(self.AILLIO_INTERFACE):
                try:
                    self.usbhandle.detach_kernel_driver(self.AILLIO_INTERFACE)
                except Exception as e: # pylint: disable=broad-except
                    self.__dbg(f'Warning: Failed to detach kernel driver: {str(e)}')

            try:
                self.usbhandle.set_configuration(self.AILLIO_CONFIGURATION)
            except Exception as e: # pylint: disable=broad-except
                self.__dbg(f'Warning: Could not set configuration: {str(e)}')

            cfg = self.usbhandle.get_active_configuration()
            intf = cfg[(self.AILLIO_INTERFACE,0)]

            try:
                usb.util.claim_interface(self.usbhandle, self.AILLIO_INTERFACE)
            except Exception as e: # pylint: disable=broad-except
                self.__dbg(f'Warning: Could not claim interface: {str(e)}')

            self.ep_out = None
            self.ep_in = None

            for ep in intf:
                self.__dbg(f'Found endpoint: {ep.bEndpointAddress:#x}')
                if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                    self.ep_out = ep
                elif usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
                    self.ep_in = ep

            if self.ep_out is None:
                raise OSError('Output endpoint not found')
            if self.ep_in is None: # type:ignore[unreachable] # mypy bug?
                raise OSError('Input endpoint not found')

            self.__dbg('Endpoints configured successfully')
            self.__dbg(f'Output endpoint: {self.ep_out.bEndpointAddress:#x}')
            self.__dbg(f'Input endpoint: {self.ep_in.bEndpointAddress:#x}')

            # Initialize communication with larger timeout for first commands
            initial_timeout = self.TIMEOUT * 2

            # INFO1 Command
            try:
                cmd = bytes(self.AILLIO_CMD_INFO1) + b'\x00' * (self.MAX_PACKET_SIZE - len(self.AILLIO_CMD_INFO1))
                self.ep_out.write(cmd, timeout=initial_timeout)
                reply = self.ep_in.read(self.MAX_PACKET_SIZE, timeout=initial_timeout)

                if len(reply) >= 26:  # Ensure we have enough data
                    sn = unpack('h', reply[0:2])[0]
                    firmware = unpack('h', reply[24:26])[0]
                    self.__dbg('serial number: ' + str(sn))
                    self.__dbg('firmware version: ' + str(firmware))
                else:
                    self.__dbg(f'Warning: Incomplete INFO1 response, length: {len(reply)}')
            except Exception as e: # pylint: disable=broad-except
                self.__dbg(f'Warning: INFO1 command failed: {str(e)}')

            # INFO2 Command
            try:
                cmd = bytes(self.AILLIO_CMD_INFO2) + b'\x00' * (self.MAX_PACKET_SIZE - len(self.AILLIO_CMD_INFO2))
                self.ep_out.write(cmd, timeout=initial_timeout)
                reply = self.ep_in.read(self.MAX_PACKET_SIZE, timeout=initial_timeout)

                if len(reply) >= 31:  # Ensure we have enough data
                    self.roast_number = unpack('>I', reply[27:31])[0]
                    self.__dbg('number of roasts: ' + str(self.roast_number))
                else:
                    self.__dbg(f'Warning: Incomplete INFO2 response, length: {len(reply)}')
                    self.roast_number = 0
            except Exception as e: # pylint: disable=broad-except
                self.__dbg(f'Warning: INFO2 command failed: {str(e)}')
                self.roast_number = 0

            self.parent_pipe, self.child_pipe = Pipe()
            self.worker_thread = threading.Thread(target=self.__updatestate,
                                            args=(self.child_pipe,))
            if self.worker_thread is not None:
                self.worker_thread.start()

        except Exception as e: # pylint: disable=broad-except
            self.usbhandle = None
            self.ep_out = None
            self.ep_in = None
            raise OSError(f'Failed to configure device: {str(e)}') from e

    def _close_port(self) -> None:
        if self.simulated:
            return

        self.worker_thread_run = False

        if self.parent_pipe is not None:
            try:
                self.parent_pipe.close()
            except Exception: # pylint: disable=broad-except
                pass
            self.parent_pipe = None

        if self.child_pipe is not None:
            try:
                self.child_pipe.close()
            except Exception: # pylint: disable=broad-except
                pass
            self.child_pipe = None

        if self.worker_thread is not None:
            try:
                self.worker_thread.join(timeout=1.0)
            except Exception: # pylint: disable=broad-except
                pass
            self.worker_thread = None

        if self.usbhandle is not None:
            try:
                usb.util.release_interface(self.usbhandle, self.AILLIO_INTERFACE)
                usb.util.dispose_resources(self.usbhandle)
            except Exception: # pylint: disable=broad-except
                pass
            self.usbhandle = None

    def __sendcmd(self, cmd:Union[List[int],bytes]) -> None:
        self.__dbg('sending command: ' + str(cmd))
        if self.usbhandle is None or self.ep_out is None:
            raise OSError('Device not properly initialized')

        try: # type:ignore[unreachable] # mypy bug?
            if isinstance(cmd, list):
                cmd = bytes(cmd)

            if self.protocol == 2:
                # For R2, ensure command is properly formatted with CRC
                if len(cmd) == 4:  # Basic command without CRC
                    cmd_with_crc = self.prepare_command(cmd)
                    self.ep_out.write(cmd_with_crc, timeout=self.TIMEOUT)
                else:  # Command already has CRC
                    self.ep_out.write(cmd, timeout=self.TIMEOUT)
            else:
                # R1 commands are sent as-is
                if len(cmd) < self.MAX_PACKET_SIZE:
                    cmd = cmd + b'\x00' * (self.MAX_PACKET_SIZE - len(cmd))
                self.ep_out.write(cmd, timeout=self.TIMEOUT)
        except Exception as e: # pylint: disable=broad-except
            raise OSError(f'Failed to send command: {str(e)}') from e

    def __readreply(self, length:int) -> Any:
        if self.usbhandle is None or self.ep_in is None:
            raise OSError('Device not properly initialized')
        try: # type:ignore[unreachable] # mypy bug?
            packets_needed = (length + self.MAX_PACKET_SIZE - 1) // self.MAX_PACKET_SIZE
            total_length = packets_needed * self.MAX_PACKET_SIZE

            data = self.ep_in.read(total_length, timeout=self.TIMEOUT)
            return data[:length]
        except Exception as e: # pylint: disable=broad-except
            raise OSError(f'Failed to read reply: {str(e)}') from e

    def __updatestate(self, p:'Connection') -> None:
        while self.worker_thread_run:
            try:
                # Check connection periodically
                if self.usbhandle is None:
                    self._open_port()

                if self.protocol == 1:
                    # V1 protocol - read two 64 byte frames
                    self.__dbg('Requesting V1 status frames')
                    self.__sendcmd(self.AILLIO_CMD_STATUS1)
                    state1 = self.__readreply(64)
                    self.__sendcmd(self.AILLIO_CMD_STATUS2)
                    state2 = self.__readreply(64)
                    data = state1 + state2

                    if len(data) == 128:
                        valid = data[41]
                        if valid == 10:
                            self.bt = round(unpack('f', data[0:4])[0], 1)
                            self.bt_ror = round(unpack('f', data[4:8])[0], 1)
                            self.dt = round(unpack('f', data[8:12])[0], 1)
                            self.exitt = round(unpack('f', data[16:20])[0], 1)
                            self.minutes = data[24]
                            self.seconds = data[25]
                            self.fan = data[26]
                            self.heater = data[27]
                            self.drum = data[28]
                            self.r1state = data[29]
                            self.irt = round(unpack('f', data[32:36])[0], 1)
                            self.pcbt = round(unpack('f', data[36:40])[0], 1)
                            self.fan_rpm = unpack('h', data[44:46])[0]
                            self.voltage = unpack('h', data[48:50])[0]
                            self.coil_fan = round(unpack('i', data[52:56])[0], 1)

                else:
                    data = self.__readreply(64)
                    if len(data) == 64:
                        frame_type = data[0]

                        if frame_type == 0xA0:
                            self.ibts_bean_temp = round(unpack('f', data[4:8])[0], 1)
                            self.ibts_bean_temp_rate = round(unpack('f', data[8:12])[0], 1)
                            self.ibts_ambient_temp = unpack('f', data[12:16])[0]
                            self.bean_probe_temp = round(unpack('f', data[16:20])[0], 1)
                            self.bean_probe_temp_rate = unpack('f', data[20:24])[0]
                            self.irt = round(float(unpack('<H', data[34:36])[0]) / 10.0, 1)
                            self.exitt = round(float(unpack('<H', data[38:40])[0]) / 10.0, 1)
                            self.heater = data[50]
                            self.fan = data[51]
                            self.drum = data[53]
                            self.r1state = data[59]

                        elif frame_type == 0xA1:
                            self.fan_rpm = unpack('h', data[48:50])[0]
                            self.coil_fan = unpack('h', data[34:36])[0]
                            self.coil_fan2 = unpack('h', data[36:38])[0]

                # Update state string
                if self.r1state == self.AILLIO_STATE_OFF:
                    self.state_str = 'off'
                elif self.r1state == self.AILLIO_STATE_PH:
                    self.state_str = 'pre-heating'
                elif self.r1state == self.AILLIO_STATE_CHARGE:
                    self.state_str = 'charge'
                elif self.r1state == self.AILLIO_STATE_ROASTING:
                    self.state_str = 'roasting'
                elif self.r1state == self.AILLIO_STATE_COOLING:
                    self.state_str = 'cooling'
                elif self.r1state == self.AILLIO_STATE_COOLDOWN:
                    self.state_str = 'cooldown'
                elif self.r1state == self.AILLIO_STATE_SHUTDOWN:
                    self.state_str = 'shutdown'
                else:
                    self.state_str = f'unknown-{self.r1state:02x}'

                if p.poll():
                    cmd = p.recv()
                    self.__dbg(f'Received command request: {cmd}')
                    if self.protocol == 2:
                        cmd = self.prepare_command(cmd)
                    self.__sendcmd(cmd)

            except Exception as e: # pylint: disable=broad-except
                self.__dbg(f'Error in updatestate: {str(e)}')
                continue

            if self.protocol == 1:
                time.sleep(0.1)

    @staticmethod
    def calculate_crc32(data:bytes) -> int:
        SHORT_LOOKUP_TABLE = [
            0x00000000, 0x04c11db7, 0x09823b6e, 0x0d4326d9,
            0x130476dc, 0x17c56b6b, 0x1a864db2, 0x1e475005,
            0x2608edb8, 0x22c9f00f, 0x2f8ad6d6, 0x2b4bcb61,
            0x350c9b64, 0x31cd86d3, 0x3c8ea00a, 0x384fbdbd,
        ]

        def crc32_fast(arg1:int, arg2:int) -> int:
            rax = (arg1 ^ arg2) & 0xffffffff
            idx = (rax >> 0x1c) & 0xf
            rcx_2 = ((rax << 4) & 0xffffffff) ^ SHORT_LOOKUP_TABLE[idx]

            idx = (rcx_2 >> 0x1c) & 0xf
            rax_4 = ((rcx_2 << 4) & 0xffffffff) ^ SHORT_LOOKUP_TABLE[idx]

            idx = (rax_4 >> 0x1c) & 0xf
            rcx_6 = ((rax_4 << 4) & 0xffffffff) ^ SHORT_LOOKUP_TABLE[idx]

            idx = (rcx_6 >> 0x1c) & 0xf
            return ((rcx_6 << 4) & 0xffffffff) ^ SHORT_LOOKUP_TABLE[idx]

        data_copy = bytearray(data)
        data_copy[-4:] = [0, 0, 0, 0]

        ints = []
        for i in range(0, len(data_copy), 4):
            val = int.from_bytes(data_copy[i:i+4], 'big')
            ints.append(val)

        result = 0xffffffff
        for val in ints:
            result = crc32_fast(result, val) & 0xffffffff

        return result & 0xffffffff

# unused:
#    def verify_crc(self, data:bytes) -> bool:
#        expected_crc = int.from_bytes(data[-4:], 'little')
#        return expected_crc == self.calculate_crc32(data)

    # prepare command (assuming self.protocol == 2)
    def prepare_command(self, cmd:Union[List[int],bytes]) -> bytes:
        if isinstance(cmd, list):
            cmd = bytes(cmd)
        cmd_with_crc = bytearray(cmd)
        while len(cmd_with_crc) < 60:
            cmd_with_crc.extend([0])
        cmd_with_crc.extend([0, 0, 0, 0])
        crc = self.calculate_crc32(bytes(cmd_with_crc))
        cmd_with_crc[-4:] = crc.to_bytes(4, 'little')
        return bytes(cmd_with_crc)


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
        # Check connection periodically
        if self.usbhandle is None:
            self._open_port()


    def get_roast_number(self) -> int:
        #self.__getstate()
        return self.roast_number

    def get_bt(self) -> float:
        self.__getstate()
        if self.protocol == 2:
            # For R2, use IBTS bean temp rate
            return self.ibts_bean_temp
        # For R1, return the stored bt_ror value
        return self.bt

    def get_dt(self) -> float:
        self.__getstate()
        if self.protocol == 2:
            # For R2, use IBTS bean temp rate
            return self.bean_probe_temp
        # For R1, return the stored bt_ror value
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
        """Get bean temperature rate of rise in °C/min"""
        self.__getstate()
        if self.protocol == 2:
            # For R2, use IBTS bean temp rate
            return self.ibts_bean_temp_rate
        # For R1, return the stored bt_ror value
        return self.bt_ror

    def get_dt_ror(self) -> float:
        """Get drum temperature rate of rise in °C/min"""
        self.__getstate()
        if self.protocol == 2:
            # For R2, use bean probe temp rate since it's closer to drum temp
            return self.bean_probe_temp_rate
        # For R1, calculate RoR from current and previous readings
        # Note: This is a basic implementation - you might want to add
        # more sophisticated RoR calculation with averaging
        try:
            return self.dt_ror
        except AttributeError:
            return 0.0

    def get_exit_temperature(self) -> float:
        self.__getstate()
        return self.exitt

    def get_state_string(self) -> str:
        self.__getstate()
        return self.state_str

    def get_state(self) -> int:
        self.__getstate()
        return self.r1state

    # R2 specific
    def get_humidity(self) -> float:
        self.__getstate()
        return self.humidity_roaster

    def get_atmospheric_pressure(self) -> float:
        self.__getstate()
        return self.absolute_atmospheric_pressure

    def get_energy_used(self) -> float:
        self.__getstate()
        return self.energy_used_this_roast

    def get_crack_count(self) -> int:
        self.__getstate()
        return self.fc_number_cracks

    def get_ibts_ambient_temp(self) -> float:
        self.__getstate()
        return self.ibts_ambient_temp

    def set_heater(self, value:float) -> None:
        self.__dbg('set_heater ' + str(value))
        value = int(value)
        if value < 0:
            value = 0
        elif value > 14:
            value = 14

        h = self.get_heater()
        d = abs(h - value)
        if d <= 0:
            return
        d = int(float(min(d,9)))
        if h > value:
            cmd = self.AILLIO_CMD_HEATER_DECR
            if self.parent_pipe is not None:
                for _ in range(d):
                    self.parent_pipe.send(bytes(cmd))
        else:
            cmd = self.AILLIO_CMD_HEATER_INCR
            if self.parent_pipe is not None:
                for _ in range(d):
                    self.parent_pipe.send(bytes(cmd))
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
            cmd = self.AILLIO_CMD_FAN_DECR
            if self.parent_pipe is not None:
                for _ in range(d):
                    self.parent_pipe.send(cmd)
        elif self.parent_pipe is not None:
            cmd = self.AILLIO_CMD_FAN_INCR
            for _ in range(d):
                self.parent_pipe.send(cmd)
        self.fan = value

    def set_drum(self, value:float) -> None:
        self.__dbg('set_drum ' + str(value))
        value = int(value)
        if value < 1:
            value = 1
        elif value > 9:
            value = 9

        d = self.get_drum()
        delta = abs(d - value)
        if delta <= 0:
            return
        delta = int(float(min(delta,9)))

        if d > value:
            cmd = self.AILLIO_CMD_DRUM_DECR
            if self.parent_pipe is not None:
                for _ in range(delta):
                    self.parent_pipe.send(bytes(cmd))
        else:
            cmd = self.AILLIO_CMD_DRUM_INCR
            if self.parent_pipe is not None:
                for _ in range(delta):
                    self.parent_pipe.send(bytes(cmd))
        self.drum = value

    def set_state(self, target_state: int) -> None:
        self.__dbg(f'set_state {target_state}')
        current_state = self.get_state()
        if current_state == target_state:
            return

        try:
            current_pos = self.VALID_STATES.index(current_state)
            target_pos = self.VALID_STATES.index(target_state)
        except ValueError:
            return

        if target_pos > current_pos:
            presses = target_pos - current_pos
        else:
            presses = len(self.VALID_STATES) - current_pos + target_pos

        for _ in range(presses):
            self.prs()
            time.sleep(0.5)

    def prs(self) -> None:
        """Press PRS button"""
        self.__dbg('PRS')

        if self.parent_pipe is not None:
            self.parent_pipe.send(self.AILLIO_CMD_PRS)

    def r2_cmd(self, str_in:str) -> None:
        if str_in.startswith('send(') and str_in.endswith(')'):
            str_in = str_in[len('send('):-1]
        json_data = json.loads(str_in)
        command = json_data.get('command', '').lower()

        if command == 'prs':
            self.prs()

        elif command == 'reset':
            pass

        elif command == 'start':
            current_state = self.get_state()
            if current_state in [self.AILLIO_STATE_PH, self.AILLIO_STATE_READY_TO_ROAST]:
                self.set_drum(5)
                self.set_fan(2)
                self.set_heater(2)
                self.set_state(self.AILLIO_STATE_ROASTING)
                time.sleep(0.25)
                self.set_drum(5)
                self.set_fan(2)
                self.set_heater(2)

            else:
                self.__dbg('Machine must be in PH or Ready state to start preheat')

        elif command == 'dopreheat':
            if self.get_state() == self.AILLIO_STATE_OFF:
                self.set_state(self.AILLIO_STATE_PH)
            else:
                self.__dbg('Machine must be in OFF state to start preheat')

        elif command in {'on', 'off', 'sync', 'charge', 'dryend', 'fcstart', 'fcend', 'scstart', 'scend'}:
            pass #usb not connected reliably at this point

        elif command == 'drop':
            current_state = self.get_state()
            if current_state == self.AILLIO_STATE_ROASTING:
                self.__dbg('Starting cooling cycle...')
                self.set_state(self.AILLIO_STATE_COOLDOWN)
                self.__dbg(f"New state: {self.get_state_string()}")
            else:
                self.__dbg(f"Cannot start cooling from {self.get_state_string()} state")
                self.__dbg('Machine must be in ROASTING state')

        elif command == 'coolend':
            current_state = self.get_state()
            self.__dbg(f"Current state: {self.get_state_string()} (0x{current_state:02x})")
            if current_state in [self.AILLIO_STATE_COOLING, self.AILLIO_STATE_COOLDOWN]:
                self.__dbg('Stopping roast...')
                self.set_state(self.AILLIO_STATE_OFF)
                time.sleep(0.5)
                self.__dbg(f"New state: {self.get_state_string()} (0x{self.get_state():02x})")
            else:
                self.__dbg(f"Cannot stop from {self.get_state_string()} state")
                self.__dbg('Machine must be in COOLING or transitional state')

        elif command == 'preheat':
            temp = int(json_data.get('value', 0))
            if 20 <= temp <= 350:
                self.__dbg(f"Setting preheat temperature to {temp}°C")
                if self.protocol == 2:
                    self.set_preheat(temp)
                else:
                    self.__dbg('Preheat setting only available on R2')
            else:
                self.__dbg('Preheat temperature must be between 20°C and 350°C')

        elif command == 'fan':
            value = int(json_data.get('value', 0))
            if 1 <= value <= 12:
                self.__dbg(f"Setting fan to {value}")
                self.set_fan(value)
            else:
                self.__dbg('Fan value must be between 1 and 12')

        elif command == 'heater':
            value = int(json_data.get('value', 0))
            if 0 <= value <= 14:
                self.__dbg(f"Setting heater to {value}")
                self.set_heater(value)
            else:
                self.__dbg('Heater value must be between 0 and 14')

        elif command == 'drum':
            value = int(json_data.get('value', 0))
            if 1 <= value <= 9:
                self.__dbg(f"Setting drum to {value}")
                self.set_drum(value)
            else:
                self.__dbg('Drum value must be between 1 and 9')

        else:
            self.__dbg(f"Unknown command: {command}")

    def set_preheat(self, temp: int) -> None:
        """Set preheat temperature (R2 only)"""
        if self.protocol != 2:
            self.__dbg('Preheat setting only available on R2')
            return

        cmd = [0x35, 0x00, 0x00, 0x00]
        cmd[3] = temp & 0xFF
        cmd[2] = (temp >> 8) & 0xFF

        if self.parent_pipe is not None:
            self.parent_pipe.send(bytes(cmd))
            self.__dbg(f"Sent preheat command: temp={temp}°C")

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
    R1 = AillioR1(debug=False)
    try:
        R1._open_port()
        print(f"Connected to {R1.model} using protocol V{R1.protocol}")

        # Example reading loop
        while True:
            if R1.protocol == 1:
                print(f"BT: {R1.get_bt():.1f}°C, DT: {R1.get_dt():.1f}°C, State: {R1.get_state_string()}")
            else:  # protocol 2
                print(f"IBTS: {R1.get_bt():.1f}°C (RoR: {R1.get_bt_ror():.1f}°C/min), "
                    f"Probe: {R1.get_dt():.1f}°C (RoR: {R1.get_dt_ror():.1f}°C/min), "
                    f"Power: {R1.get_heater()}, Fan: {R1.get_fan()}, "
                    f"State: {R1.get_state_string()}, "
                    f"Hot Air: {R1.exitt:.1f}°C, "
                    f"Inlet: {R1.irt:.1f}°C")
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nExiting...')
    except OSError as e:
        print(f"Error: {e}")
    finally:
        R1._close_port()
