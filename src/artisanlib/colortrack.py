#
# ABOUT
# ColorTrack support for Artisan

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

import asyncio
import logging
import numpy as np

from artisanlib.async_comm import AsyncComm
from artisanlib.ble_port import ClientBLE

try:
    from PyQt6.QtCore import QRegularExpression # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QRegularExpression # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from typing import Final, Optional, Callable, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtCore import QRegularExpressionMatch # pylint: disable=unused-import
    from artisanlib.types import SerialSettings # pylint: disable=unused-import
    import numpy.typing as npt # pylint: disable=unused-import
    from bleak.backends.characteristic import BleakGATTCharacteristic  # pylint: disable=unused-import

_log: Final[logging.Logger] = logging.getLogger(__name__)


class ColorTrack(AsyncComm):

    __slots__ = [ '_color_regex', '_weights', '_received_readings' ]

    def __init__(self, host:str = '127.0.0.1', port:int = 8080, serial:Optional['SerialSettings'] = None,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None) -> None:

        super().__init__(host, port, serial, connected_handler, disconnected_handler)

        self._color_regex: Final[QRegularExpression] = QRegularExpression(r'\d+\.\d+')

        # weights for averaging (length 5)
        self._weights:Final[npt.NDArray[np.float64]] = np.array([1,2,3,5,7])
        # received but not yet consumed readings
        self._received_readings:npt.NDArray[np.float64] = np.array([])

    # external API to access machine state

    def getColor(self) -> float:
        try:
            number_of_readings = len(self._received_readings)
            if number_of_readings == 1:
                return float(self._received_readings[0])
            if number_of_readings > 1:
                # consume and average the readings
                l = min(len(self._weights), number_of_readings)
                res:float = float(np.average(self._received_readings[-l:], weights=self._weights[-l:]))
                self._received_readings = np.array([])
                return res
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        return -1

    def register_reading(self, value:float) -> None:
        self._received_readings = np.append(self._received_readings, value)
        if self._logging:
            _log.info('register_reading: %s',value)


    # asyncio read implementation

    # https://www.oreilly.com/library/view/using-asyncio-in/9781492075325/ch04.html
    async def read_msg(self, stream: asyncio.StreamReader) -> None:
        line = await stream.readline()
        if self._logging:
            _log.debug('received: %s',line)
        match:QRegularExpressionMatch = self._color_regex.match(line.decode('ascii', errors='ignore'))
        if match.hasMatch() and match.hasCaptured(0):
            try:
                first_match:str = match.captured(0)
                value:float = float(first_match)
                self.register_reading(value)
            except Exception as e: # pylint: disable=broad-except
                _log.error(e)


class ColorTrackBLE(ClientBLE):

    # ColorTrack RT service and characteristics UUIDs
    COLORTRACK_NAME:Final[str] = 'ColorTrack'
    COLORTRACK_SERVICE_UUID:Final[str] = '713D0000-503E-4C75-BA94-3148F18D941E'
    COLORTRACK_READ_NOTIFY_LASER_UUID:Final[str] = '713D0002-503E-4C75-BA94-3148F18D9410'    # Laser Measurements
    COLORTRACK_TEMP_HUM_READ_NOTIFY_UUID:Final[str] = '713D0004-503E-4C75-BA94-3148F18D9410' # Temperature and Humidity

    # maps bytes received via BLE to color values [100-0]
    COLOR_MAP = [ 0,0,0.01,0.02,0.04,0.06,0.08,0.11,0.15,0.19,0.23,
            0.28,0.33,0.39,0.45,0.51,0.58,0.66,0.73,0.82,0.9,
            1.0,1.09,1.19,1.3,1.41,1.52,1.64,1.77,1.89,2.03,
            2.16,2.3,2.45,2.6,2.75,2.91,3.08,3.25,3.42,3.59,
            3.78,3.96,4.15,4.35,4.55,4.75,4.96,5.17,5.39,5.61,
            5.83,6.07,6.3,6.54,6.78,7.03,7.28,7.54,7.8,8.07,
            8.34,8.61,8.89,9.18,9.47,9.76,10.06,10.36,10.66,10.98,
            11.29,11.61,11.93,12.26,12.6,12.93,13.28,13.62,13.97,14.33,
            14.69,15.05,15.42,15.79,16.17,16.55,16.94,17.33,17.73,18.13,
            18.53,18.94,19.35,19.77,20.19,20.62,21.05,21.49,21.93,22.37,
            22.82,23.27,23.73,24.19,24.66,25.31,25.61,26.09,26.57,27.06,
            27.56,28.05,28.56,29.06,29.58,30.09,30.61,31.14,31.67,32.2,
            32.74,33.28,33.83,34.38,34.94,35.5,36.06,36.63,37.21,37.78,
            38.37,38.95,39.55,40.14,40.74,41.35,41.96,42.57,43.19,43.81,
            44.44,45.07,45.71,46.35,47,47.65,48.3,48.96,49.62,50.29,
            50.96,51.64,52.32,53.0,53.69,54.39,55.09,55.79,56.5,57.21,
            57.93,58.65,59.38,60.11,60.84,61.58,62.32,63.07,63.82,64.58,
            65.34,66.11,66.88,67.65,68.43,69.22,70,70.8,71.59,72.39,
            73.2,74.01,74.83,75.65,76.47,77.3,78.13,78.97,79.82,80.65,
            81.51,82.36,83.22,84.08,84.95,85.83,86.7,87.58,88.47,89.36,
            90.26,91.16,92.06,92.97,93.88,94.8,95.72,96.65,97.58,98.51,
            99.45,100 ]

    def __init__(self, connected_handler:Optional[Callable[[], None]] = None,
                    disconnected_handler:Optional[Callable[[], None]] = None):
        super().__init__()

        # handlers
        self._connected_handler = connected_handler
        self._disconnected_handler = disconnected_handler

        self.add_device_description(self.COLORTRACK_SERVICE_UUID, self.COLORTRACK_NAME)
        self.add_notify(self.COLORTRACK_READ_NOTIFY_LASER_UUID, self.notify_laser_callback)
        self.add_read(self.COLORTRACK_SERVICE_UUID, self.COLORTRACK_READ_NOTIFY_LASER_UUID)
        self.add_notify(self.COLORTRACK_TEMP_HUM_READ_NOTIFY_UUID, self.notify_temp_hum_callback)

        # weights for averaging (length 40) # ColorTrack sends about 65 laser readings per second
        self._weights:Final[npt.NDArray[np.float64]] = np.array(range(1, 40))
        # received but not yet consumed readings (mapped)
        self._received_readings:npt.NDArray[np.float64] = np.array([])
        self._received_raw_readings:npt.NDArray[np.float64] = np.array([])


    def map_reading(self, r:int) -> float:
        if 0 <= r < 213:
            return self.COLOR_MAP[r]
        return 0

    def register_reading(self, value:float) -> None:
        self._received_readings = np.append(self._received_readings, value)
        if self._logging:
            _log.info('register_reading: %s',value)

    def register_raw_reading(self, value:float) -> None:
        self._received_raw_readings = np.append(self._received_raw_readings, value)

    # second result is the raw average
    def getColor(self) -> Tuple[float, float]:
        read_res = self.read(self.COLORTRACK_READ_NOTIFY_LASER_UUID)
        _log.info('PRINT getLaser: %s',read_res)
        try:
            number_of_readings = len(self._received_readings)
            number_of_raw_readings = len(self._received_raw_readings)
            if number_of_readings == 1:
                return float(self._received_readings[0]), (float(self._received_raw_readings[0]) if number_of_raw_readings==1 else -1)
            if number_of_readings > 1:
                # consume and average the readings
                l = min(len(self._weights), number_of_readings)
                res:float = float(np.average(self._received_readings[-l:], weights=self._weights[-l:]))
                self._received_readings = np.array([])
                # raw
                l_raw = min(len(self._weights), number_of_raw_readings)
                res_raw:float = float(np.average(self._received_raw_readings[-l_raw:], weights=self._weights[-l_raw:]))
                self._received_raw_readings = np.array([])
                return res, res_raw
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        return -1, -1

    # every second reading is the sync character 36
    # returns readings as bytes extracted from the given payload. If the payload is not valid the result is empty.
    @staticmethod
    def validate_data(payload:bytearray) -> bytearray:
        if len(payload) % 2 == 0:
            payload_even = payload[::2]
            payload_odd = payload[1::2]
            if all(d == 36 for d in payload_even):
                return payload_odd
            if all(d == 36 for d in payload_odd):
                return payload_even
        return bytearray()

    def notify_laser_callback(self, _sender:'BleakGATTCharacteristic', payload:bytearray) -> None:
        for r in self.validate_data(payload):
            self.register_reading(self.map_reading(r))
            self.register_raw_reading(r)

    @staticmethod
    def notify_temp_hum_callback(_sender:'BleakGATTCharacteristic', payload:bytearray) -> None:
        _log.info('PRINT temp/hum: %s', payload)

    def on_connect(self) -> None: # pylint: disable=no-self-use
        self._received_readings = np.array([])
        if self._connected_handler is not None:
            self._connected_handler()

    def on_disconnect(self) -> None: # pylint: disable=no-self-use
        if self._disconnected_handler is not None:
            self._disconnected_handler()



def main() -> None:
    import time
    from artisanlib.types import SerialSettings
    # bench top
    colortrack_serial:SerialSettings = {
        'port': '/dev/slave',
        'baudrate': 9600,
        'bytesize': 8,
        'stopbits': 1,
        'parity': 'N',
        'timeout': 0.3}
    colorTrack = ColorTrack(serial=colortrack_serial)
    colorTrack.start()
    for _ in range(4):
        print('Color',colorTrack.getColor())
        time.sleep(1)
    colorTrack.stop()
    time.sleep(1)
    #print('thread alive?',colorTrack._thread.is_alive())

if __name__ == '__main__':
    main()
