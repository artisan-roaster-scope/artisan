#!/usr/bin/env python3

# ABOUT
# Aillio R2 support for Artisan

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
# mikefsq, r2 2025

import time
from struct import unpack
from multiprocessing import Pipe
import threading
from platform import system
import usb.core # type: ignore[import-untyped]
import usb.util # type: ignore[import-untyped]
import json

if system().startswith('Windows'):
    import libusb_package # pyright:ignore[reportMissingImports] # pylint: disable=import-error


import logging
from typing import Final, Optional, List, Union, Any, TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    try:
        from multiprocessing.connection import PipeConnection as Connection # type: ignore[unused-ignore,attr-defined,assignment] # pylint: disable=unused-import
    except ImportError:
        from multiprocessing.connection import Connection # type: ignore[unused-ignore,attr-defined,assignment] # pylint: disable=unused-import
    from usb.core import Configuration, Interface, Endpoint

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

class AillioR2:
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
        # Thread safety and cleanup controls
        self._cleanup_lock = threading.Lock()
        self._is_cleanup_done:bool = False
        self.worker_thread_run:bool = True

        # Communication pipes
        self.parent_pipe: Optional[Connection] = None
        self.child_pipe: Optional[Connection] = None
        self.worker_thread: Optional[threading.Thread] = None

        # Basic configuration
        self.simulated:bool = False
        self.AILLIO_DEBUG = debug
        self.__dbg('init')

        # USB handling
        self.usbhandle:Optional[usb.core.Device] = None # type:ignore[no-any-unimported,unused-ignore]
        self.protocol:int = 2
        self.model:str = 'Unknown'
        self.ep_in:Optional[Endpoint] = None
        self.ep_out:Optional[Endpoint] = None
        self.TIMEOUT = 1000  # USB timeout in milliseconds
        self.FRAME_SIZE = 64  # Standard USB packet size

        # Device variants
        self.DEVICE_VARIANTS:List[DEVICE_VARIANT] = [
            {'vid': 0x0483, 'pid': 0xa4cd, 'protocol': 2, 'model': 'Aillio Bullet R2'},
        ]

        # Fields from R1 for compatibility
        self.bt:float = 0
        self.dt:float = 0
#        self.heater:float = 0
#        self.fan:float = 0
        self.bt_ror:float = 0
        self.dt_ror:float = 0
#        self.drum:float = 0
        self.voltage:float = 0
#        self.exitt:float = 0
#        self.state_str:str = ''
#        self.r1state:int = 0
        self.roast_number:int = -1
        self.fan_rpm:float = 0
        self.irt:float = 0
        self.pcbt:float = 0
#        self.coil_fan:int = 0
#        self.coil_fan2:int = 0
        self.pht:int = 0
#        self.minutes = 0
#        self.seconds = 0

        # A0 Frame - Basic Temperature Data
        self.ibts_bean_temp: float = 0.0
        self.ibts_bean_temp_rate: float = 0.0
        self.ibts_ambient_temp: float = 0.0
        self.bean_probe_temp: float = 0.0
        self.bean_probe_temp_rate: float = 0.0
        self.energy_used_this_roast: float = 0.0
        self.differential_air_pressure: float = 0.0
        self.exhaust_fan_rpm: int = 0
        self.inlet_air_temp: float = 0.0
        self.hot_air_temp: float = 0.0
        self.exitt: float = 0.0  # ExhaustAirTemp
        self.absolute_atmospheric_pressure: float = 0.0
        self.humidity_roaster: float = 0.0
        self.humidity_temp: float = 0.0
        self.minutes: int = 0
        self.button_crack_mark: int = 0
        self.seconds: int = 0
        self.heater: int = 0    # PSet
        self.fan: int = 0       # FSet
        self.ha_set: int = 0    # HASet
        self.drum: int = 0      # DSet
        self.r_count: int = 0
        self.fc_sample_index: int = 0
        self.fc_number_cracks: int = 0
        self.roasting_method: int = 0  # Manual or Recipe
        self.status: int = 0
        self.r1state: int = 0   # StateMachine

        # A1 Frame - Fan Control and Error Data
        self.error_counts: int = 0
        self.extra_u8_1: int = 0
        self.extra_u8_2: int = 0
        self.extra_u8_3: int = 0
        self.error_category1: int = 0
        self.error_type1: int = 0
        self.error_info1: int = 0
        self.error_value1: int = 0
        self.error_category2: int = 0
        self.error_type2: int = 0
        self.error_info2: int = 0
        self.error_value2: int = 0
        self.coil_fan1_duty: int = 0
        self.coil_fan2_duty: int = 0
        self.induction_fan1_duty: int = 0
        self.induction_fan2_duty: int = 0
        self.induction_blower_duty: int = 0
        self.icf1_fan_duty: int = 0
        self.exhaust_blower_duty: int = 0
        self.vibrator_motor_duty: int = 0
        self.reserved_u16_1: int = 0
        self.coil_fan: int = 0  # CoilFan1Rpm
        self.coil_fan2: int = 0  # CoilFan2Rpm
        self.induction_fan1_rpm: int = 0
        self.induction_fan2_rpm: int = 0
        self.induction_blower_rpm: int = 0
        self.icf1_fan_rpm: int = 0
        self.ibts_fan_rpm: int = 0
        self.roast_drum_rpm: int = 0
        self.reserved_u16_3: int = 0
        self.control_board_critical: int = 0
        self.buttons: int = 0

        # A2 Frame - Power Data
        self.power_setpoint_watt: int = 0
        self.line_frequency_hz: float = 0.0
        self.igbt_frequency_hz: int = 0
        self.igbt_error: int = 0
        self.igbt_temp1: float = 0.0
        self.igbt_temp2: float = 0.0
        self.state_runtime: int = 0
        self.status_register: int = 0
        self.status_error: int = 0
        self.voltage_rms: float = 0.0
        self.current_rms: float = 0.0
        self.active_power: float = 0.0
        self.reactive_power: float = 0.0
        self.apparent_power: float = 0.0
        self.accumulator_energy: int = 0
        self.extra_u16_1: int = 0
        self.extra_u16_2: int = 0
        self.extra_u16_3: int = 0
        self.extra_u16_4: int = 0
        self.extra_u8_5: int = 0
        self.extra_u8_6: int = 0
        self.extra_u32_7: int = 0
        self.extra_f32_8: float = 0.0
        self.extra_f32_9: float = 0.0
        self.extra_f32_10: float = 0.0

        # Other fields
        self.state_str: str = ''

        # Initialize USB connection and start worker thread
        self._open_port()

    def __del__(self) -> None:
        if not self.simulated:
            self._close_port()

    def __dbg(self, msg:str) -> None:
        _log.debug('Aillio: %s', msg)
        if self.AILLIO_DEBUG and not self.simulated:
            try:
                print('AillioR2: ' + msg)
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
                self.usbhandle = libusb_package.find(idVendor=variant['vid'],  # pyright:ignore[reportPossiblyUnboundVariable] # pylint: disable=possibly-used-before-assignment
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

            cfg:Configuration = self.usbhandle.get_active_configuration()
            intf:Interface = cfg[(self.AILLIO_INTERFACE,0)]

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
            if self.ep_in is None:
                raise OSError('Input endpoint not found')

            self.__dbg('Endpoints configured successfully')
            self.__dbg(f'Output endpoint: {self.ep_out.bEndpointAddress:#x}')
            self.__dbg(f'Input endpoint: {self.ep_in.bEndpointAddress:#x}')

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
        """Clean shutdown of USB and worker thread"""
        with self._cleanup_lock:
            if self._is_cleanup_done:
                return
            self._is_cleanup_done = True

            # Signal thread to stop
            self.worker_thread_run = False  # Use boolean instead of Event.clear()

            # Close pipes
            if hasattr(self, 'parent_pipe') and self.parent_pipe is not None:
                try:
                    self.parent_pipe.close()
                except Exception: # pylint: disable=broad-except
                    pass
                self.parent_pipe = None

            if hasattr(self, 'child_pipe') and self.child_pipe is not None:
                try:
                    self.child_pipe.close()
                except Exception: # pylint: disable=broad-except
                    pass
                self.child_pipe = None

            # Wait for thread to finish
            if hasattr(self, 'worker_thread') and self.worker_thread is not None:
                try:
                    self.worker_thread.join(self.TIMEOUT)
                except Exception: # pylint: disable=broad-except
                    pass
                self.worker_thread = None

            # Release USB resources last
            if hasattr(self, 'usbhandle') and self.usbhandle is not None:
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

        try:
            if isinstance(cmd, list):
                cmd = bytes(cmd)

            self.ep_out.write(cmd, timeout=self.TIMEOUT)

        except Exception as e: # pylint: disable=broad-except
            raise OSError(f'Failed to send command: {str(e)}') from e

    def __readreply(self, length:int) -> Any:
        if self.usbhandle is None or self.ep_in is None:
            raise OSError('Device not properly initialized')
        try:
            packets_needed = (length + self.FRAME_SIZE - 1) // self.FRAME_SIZE
            total_length = packets_needed * self.FRAME_SIZE

            data = self.ep_in.read(total_length, timeout=self.TIMEOUT)
            return data[:length]
        except Exception as e: # pylint: disable=broad-except
            raise OSError(f'Failed to read reply: {str(e)}') from e

    @staticmethod
    def __debug_frame(data: bytes) -> None:
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_values = ' '.join(f'{b:02x}' for b in chunk)
            ascii_values = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            print(f"{i:04x}: {hex_values:<48} {ascii_values}")


    def __updatestate(self, p:'Connection') -> None:
        """Worker thread main loop for updating roaster state data"""
        while self.worker_thread_run:
            try:
                # Check connection periodically
                if self.usbhandle is None:
                    time.sleep(0.5)  # Don't spin if disconnected
                    continue

                # Read frame from USB
                frame_type = 0xff
                data = self.__readreply(self.FRAME_SIZE)
                if len(data) == self.FRAME_SIZE:
                    frame_type = data[0]

                    # serial debug output
                    if self.AILLIO_DEBUG:
                        print()
                        self.__debug_frame(data)

                    # Temperature frame
                    if frame_type == 0xA0:
                        # Use little-endian struct unpacking
                        self.ibts_bean_temp = round(unpack('<f', data[4:8])[0], 1)
                        self.ibts_bean_temp_rate = round(unpack('<f', data[8:12])[0], 1)
                        self.ibts_ambient_temp = unpack('<f', data[12:16])[0]
                        self.bean_probe_temp = round(unpack('<f', data[16:20])[0], 1)
                        self.bean_probe_temp_rate = unpack('<f', data[20:24])[0]
                        self.energy_used_this_roast = unpack('<f', data[24:28])[0]
                        self.differential_air_pressure = unpack('<f', data[28:32])[0]
                        self.exhaust_fan_rpm = unpack('<H', data[32:34])[0]
                        self.inlet_air_temp = float(unpack('<H', data[34:36])[0]) / 10.0
                        self.hot_air_temp = float(unpack('<H', data[36:38])[0]) / 10.0
                        self.exitt = float(unpack('<H', data[38:40])[0]) / 10.0  # ExhaustAirTemp
                        self.absolute_atmospheric_pressure = float(unpack('<H', data[40:42])[0]) / 10.0
                        self.humidity_roaster = float(unpack('<H', data[42:44])[0]) / 10.0
                        self.humidity_temp = float(unpack('<H', data[44:46])[0]) / 10.0
                        self.minutes = data[46]  # ClockM
                        self.button_crack_mark = data[47]
                        self.seconds = data[48]  # ClockS
                        self.heater = data[50]   # PSet
                        self.fan = data[51]      # FSet
                        self.ha_set = data[52]   # HASet
                        self.drum = data[53]     # DSet
                        self.r_count = data[54]
                        self.fc_sample_index = data[55]
                        self.fc_number_cracks = data[56]
                        self.roasting_method = data[57]  # Manual or Recipe
                        self.status = data[58]
                        self.r1state = data[59]  # StateMachine
                        #
                        self.irt = self.inlet_air_temp #mapping to R1
                        self.fan_rpm = self.exhaust_fan_rpm #mapping to R1

                        # Update state string based on r1state
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

                        # Debug output
                        if self.AILLIO_DEBUG:
                            print(f"[0x{frame_type:02x}] IBTS: {self.ibts_bean_temp:.1f}°C (RoR: {self.ibts_bean_temp_rate:.1f}°C/min), "
                            f"Probe: {self.bean_probe_temp:.1f}°C (RoR: {self.bean_probe_temp_rate:.1f}°C/min), "
                            f"Power: {self.heater}, Fan: {self.fan}, Drum: {self.drum}, "
                            f"Status: {self.status}, r1state: {self.r1state} ")

                    # Fan frame
                    elif frame_type == 0xA1:
                        self.error_counts = data[4]
                        self.extra_u8_1 = data[5]
                        self.extra_u8_2 = data[6]
                        self.extra_u8_3 = data[7]
                        self.error_category1 = data[8]
                        self.error_type1 = data[9]
                        self.error_info1 = data[10]
                        self.error_value1 = data[11]
                        self.error_category2 = data[12]
                        self.error_type2 = data[13]
                        self.error_info2 = data[14]
                        self.error_value2 = data[15]
                        self.coil_fan1_duty = unpack('<H', data[16:18])[0]
                        self.coil_fan2_duty = unpack('<H', data[18:20])[0]
                        self.induction_fan1_duty = unpack('<H', data[20:22])[0]
                        self.induction_fan2_duty = unpack('<H', data[22:24])[0]
                        self.induction_blower_duty = unpack('<H', data[24:26])[0]
                        self.icf1_fan_duty = unpack('<H', data[26:28])[0]
                        self.exhaust_blower_duty = unpack('<H', data[28:30])[0]
                        self.vibrator_motor_duty = unpack('<H', data[30:32])[0]
                        self.reserved_u16_1 = unpack('<H', data[32:34])[0]
                        self.coil_fan = unpack('<H', data[34:36])[0]  # CoilFan1Rpm
                        self.coil_fan2 = unpack('<H', data[36:38])[0]  # CoilFan2Rpm
                        self.induction_fan1_rpm = unpack('<H', data[38:40])[0]
                        self.induction_fan2_rpm = unpack('<H', data[40:42])[0]
                        self.induction_blower_rpm = unpack('<H', data[42:44])[0]
                        self.icf1_fan_rpm = unpack('<H', data[44:46])[0]
                        self.ibts_fan_rpm = unpack('<H', data[46:48])[0]
                        self.roast_drum_rpm = unpack('<H', data[48:50])[0]
                        self.reserved_u16_3 = unpack('<H', data[50:52])[0]
                        self.control_board_critical = unpack('<H', data[52:54])[0]
                        self.buttons = unpack('<H', data[58:60])[0]

                        # Debug output
                        if self.AILLIO_DEBUG:
                            print(f"[0x{frame_type:02x}] coil_fan1_duty: {self.coil_fan1_duty}, coil_fan2_duty: {self.coil_fan2_duty}, "
                            f"induction_fan1_rpm: {self.induction_fan1_rpm:.1f}, induction_fan2_rpm: {self.induction_fan2_rpm:.1f}, "
                            f"induction_blower_rpm: {self.induction_blower_rpm}, icf1_fan_rpm: {self.icf1_fan_rpm}, ibts_fan_rpm: {self.ibts_fan_rpm}, "
                            f"roast_drum_rpm: {self.roast_drum_rpm}, buttons: {self.buttons} ")

                    elif frame_type == 0xA2:
                        self.power_setpoint_watt = unpack('<H', data[4:6])[0]
                        self.line_frequency_hz = float(unpack('<H', data[6:8])[0]) / 100.0
                        self.igbt_frequency_hz = unpack('<H', data[8:10])[0]
                        self.igbt_error = unpack('<H', data[10:12])[0]
                        self.igbt_temp1 = float(unpack('<H', data[12:14])[0]) / 10.0
                        self.igbt_temp2 = float(unpack('<H', data[14:16])[0]) / 10.0
                        self.state_runtime = unpack('<H', data[16:18])[0]
                        self.status_register = unpack('<H', data[18:20])[0]
                        self.status_error = unpack('<H', data[20:22])[0]
                        self.active_power = float(unpack('<H', data[22:24])[0]) / 10.0
                        self.reactive_power = float(unpack('<H', data[24:26])[0]) / 10.0
                        self.apparent_power = float(unpack('<H', data[26:28])[0]) / 10.0
                        self.voltage_rms = float(unpack('<H', data[28:30])[0]) / 10.0
                        self.current_rms = float(unpack('<H', data[30:32])[0]) / 1000.0
                        self.accumulator_energy = unpack('<H', data[32:34])[0]
                        self.extra_u16_1 = unpack('<H', data[34:36])[0]
                        self.extra_u16_2 = unpack('<H', data[36:38])[0]
                        self.extra_u16_3 = unpack('<H', data[38:40])[0]
                        self.extra_u16_4 = unpack('<H', data[40:42])[0]
                        self.extra_u8_5 = data[42]
                        self.extra_u8_6 = data[43]
                        self.extra_u32_7 = unpack('<I', data[44:48])[0]
                        self.extra_f32_8 = unpack('<f', data[48:52])[0]
                        self.extra_f32_9 = unpack('<f', data[52:56])[0]
                        self.extra_f32_10 = unpack('<f', data[56:60])[0]

                        # Debug output
                        if self.AILLIO_DEBUG:
                            print(f"[0x{frame_type:02x}] power_setpoint_watt: {self.power_setpoint_watt}, line_frequency_hz: {self.line_frequency_hz:0.1f}Hz, "
                            f"igbt_frequency_hz: {self.igbt_frequency_hz}Hz, igbt_temp1 {self.igbt_temp1:.1f}°C, igbt_temp2 {self.igbt_temp2:.1f}°C, "
                            f"active_power: {self.active_power:.1f}, reactive_power: {self.reactive_power:.1f}, apparent_power: {self.apparent_power:.1f}, "
                            f"voltage_rms: {self.voltage_rms:.1f}V, current_rms: {self.current_rms:.1f}A ")

                    else:
                        pass #unparsed

                # Check for and handle commands from the pipe
                try:
                    if p.poll():  # Check if there are commands waiting
                        cmd = p.recv()
                        if isinstance(cmd, bytes):
                            self.__dbg(f'Sending command: {[hex(b) for b in cmd]}')
                            try:
                                self.__sendcmd(cmd)
                                time.sleep(0.1) # large slider changes need this
                            except Exception as e: # pylint: disable=broad-except
                                self.__dbg(f'Error sending command: {str(e)}')
                except Exception as e: # pylint: disable=broad-except
                    self.__dbg(f'Pipe error: {str(e)}')

            except Exception as e: # pylint: disable=broad-except
                self.__dbg(f'Error in updatestate: {str(e)}')
                time.sleep(0.5)  # Longer delay on error

        self.__dbg('Update thread exiting')


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
#    def verify_crc(self, data):
#        expected_crc = int.from_bytes(data[-4:], 'little')
#        return expected_crc == self.calculate_crc32(data)

    def prepare_command(self, cmd:Union[List[int],bytes]) -> bytes:
        if isinstance(cmd, list):
            cmd = bytes(cmd)
        cmd_with_crc = bytearray(cmd)
        cmd_with_crc.extend([0, 0, 0, 0])
        crc = self.calculate_crc32(bytes(cmd_with_crc))
        cmd_with_crc[-4:] = crc.to_bytes(4, 'little')
        return bytes(cmd_with_crc)

    def get_roast_number(self) -> int:
        return self.roast_number

    def get_bt(self) -> float:
        """Get ibts temperature in °C"""
        return self.ibts_bean_temp

    def get_dt(self) -> float:
        """Get bean probe temperature in °C"""
        return self.bean_probe_temp

    def get_heater(self) -> float:
        self.__dbg('get_heater')
        return self.heater

    def get_fan(self) -> float:
        self.__dbg('get_fan')
        return self.fan

    def get_fan_rpm(self) -> float:
        self.__dbg('get_fan_rpm')
        return self.fan_rpm

    def get_drum(self) -> float:
        return self.drum

    def get_voltage(self) -> float:
        return self.voltage_rms

    def get_bt_ror(self) -> float:
        """Get ibts temperature rate of rise in °C/min"""
        return self.ibts_bean_temp_rate

    def get_dt_ror(self) -> float:
        """Get bean probe temperature rate of rise in °C/min"""
        return self.bean_probe_temp_rate

    def get_exit_temperature(self) -> float:
        return self.exitt

    def get_state_string(self) -> str:
        return self.state_str

    def get_state(self) -> int:
        return self.r1state

    # R2 specific
    def get_humidity(self) -> float:
        return self.humidity_roaster

    def get_atmospheric_pressure(self) -> float:
        return self.absolute_atmospheric_pressure

    def get_energy_used(self) -> float:
        return self.energy_used_this_roast

    def get_crack_count(self) -> int:
        return self.fc_number_cracks

    def get_ibts_ambient_temp(self) -> float:
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
            cmd = self.prepare_command(self.AILLIO_CMD_HEATER_DECR)
            if self.parent_pipe is not None:
                for _ in range(d):
                    self.parent_pipe.send(cmd)
        else:
            cmd = self.prepare_command(self.AILLIO_CMD_HEATER_INCR)
            if self.parent_pipe is not None:
                for _ in range(d):
                    self.parent_pipe.send(cmd)
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
            cmd = self.prepare_command(self.AILLIO_CMD_FAN_DECR)
            if self.parent_pipe is not None:
                for _ in range(d):
                    self.parent_pipe.send(cmd)
        else:
            cmd = self.prepare_command(self.AILLIO_CMD_FAN_INCR)
            if self.parent_pipe is not None:
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
            cmd = self.prepare_command(self.AILLIO_CMD_DRUM_DECR)
            if self.parent_pipe is not None:
                for _ in range(delta):
                    self.parent_pipe.send(cmd)
        else:
            cmd = self.prepare_command(self.AILLIO_CMD_DRUM_INCR)
            if self.parent_pipe is not None:
                for _ in range(delta):
                    self.parent_pipe.send(cmd)
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
            cmd = self.prepare_command(self.AILLIO_CMD_PRS)
            self.parent_pipe.send(cmd)

    def send_command(self, str_in:str) -> None:
        if str_in.startswith('send(') and str_in.endswith(')'):
            str_in = str_in[len('send('):-1]
        json_data = json.loads(str_in)
        command = json_data.get('command', '').strip().lower()

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
                print('Machine must be in PH or Ready state to start preheat')

        elif command == 'dopreheat':
            if self.get_state() == self.AILLIO_STATE_OFF:
                self.set_state(self.AILLIO_STATE_PH)
            else:
                print('Machine must be in OFF state to start preheat')

        elif command in {'on', 'off', 'sync', 'charge', 'dryend', 'fcstart', 'fcend', 'scstart', 'scend'}:
            pass #usb not connected reliably at this point

        elif command == 'drop':
            current_state = self.get_state()
            if current_state == self.AILLIO_STATE_ROASTING:
                print('Starting cooling cycle...')
                self.set_state(self.AILLIO_STATE_COOLDOWN)
                print(f"New state: {self.get_state_string()}")
            else:
                print(f"Cannot start cooling from {self.get_state_string()} state")
                print('Machine must be in ROASTING state')

        elif command == 'coolend':
            current_state = self.get_state()
            print(f"Current state: {self.get_state_string()} (0x{current_state:02x})")
            if current_state in [self.AILLIO_STATE_COOLING, self.AILLIO_STATE_COOLDOWN]:
                print('Stopping roast...')
                self.set_state(self.AILLIO_STATE_OFF)
                time.sleep(0.5)
                print(f"New state: {self.get_state_string()} (0x{self.get_state():02x})")
            else:
                print(f"Cannot stop from {self.get_state_string()} state")
                print('Machine must be in COOLING or transitional state')

        elif command == 'preheat':
            temp = int(json_data.get('value', 0))
            if 20 <= temp <= 350:
                print(f"Setting preheat temperature to {temp}°C")
                self.set_preheat(temp)
            else:
                print('Preheat temperature must be between 20°C and 350°C')

        elif command == 'fan':
            value = int(json_data.get('value', 0))
            if 1 <= value <= 12:
                print(f"Setting fan to {value}")
                self.set_fan(value)
            else:
                print('Fan value must be between 1 and 12')

        elif command == 'heater':
            value = int(json_data.get('value', 0))
            if 0 <= value <= 14:
                print(f"Setting heater to {value}")
                self.set_heater(value)
            else:
                print('Heater value must be between 0 and 14')

        elif command == 'drum':
            value = int(json_data.get('value', 0))
            if 1 <= value <= 9:
                print(f"Setting drum to {value}")
                self.set_drum(value)
            else:
                print('Drum value must be between 1 and 9')

        else:
            print(f"Unknown command: {command}")

    def set_preheat(self, temp: int) -> None:
        """Set preheat temperature (R2 only)"""
        self.__dbg('aillio_rs:set_preheat()')

        cmd = [0x35, 0x00, 0x00, 0x00]
        cmd[3] = temp & 0xFF
        cmd[2] = (temp >> 8) & 0xFF
        cmdOut = self.prepare_command(cmd)
        if self.parent_pipe is not None:
            self.parent_pipe.send(bytes(cmdOut))
            print(f"Sent preheat command: temp={temp}°C")

if __name__ == '__main__':
    R2 = AillioR2(debug=True)
    try:
        R2._open_port() # pylint: disable=protected-access
        print(f"Connected to {R2.model} using protocol V{R2.protocol}")

        # Example reading loop
        while True:
            # print(f"IBTS: {R2.get_bt():.1f}°C (RoR: {R2.get_bt_ror():.1f}°C/min), "
            #     f"Probe: {R2.get_dt():.1f}°C (RoR: {R2.get_dt_ror():.1f}°C/min), "
            #     f"Power: {R2.get_heater()}, Fan: {R2.get_fan()}, "
            #     f"State: {R2.get_state_string()}, "
            #     f"Hot Air: {R2.exitt:.1f}°C, "
            #     f"Inlet: {R2.irt:.1f}°C")
            time.sleep(10)
    except KeyboardInterrupt:
        print('\nExiting...')
    except OSError as e:
        print(f"Error: {e}")
    finally:
        R2._close_port() # pylint: disable=protected-access
