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
from artisanlib.filters import LiveMean, LiveMedian

try:
    from PyQt6.QtCore import QRegularExpression # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QRegularExpression # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from typing import Final, Optional, Callable, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtCore import QRegularExpressionMatch # pylint: disable=unused-import
    from artisanlib.atypes import SerialSettings # pylint: disable=unused-import
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


    def __init__(self, mean_window_size:int, median_window_size:int,
                       connected_handler:Optional[Callable[[], None]] = None,
                       disconnected_handler:Optional[Callable[[], None]] = None):
        super().__init__()

        # handlers
        self._connected_handler = connected_handler
        self._disconnected_handler = disconnected_handler

        self.add_device_description(self.COLORTRACK_SERVICE_UUID, self.COLORTRACK_NAME)
        self.add_notify(self.COLORTRACK_READ_NOTIFY_LASER_UUID, self.notify_laser_callback)
        self.add_read(self.COLORTRACK_SERVICE_UUID, self.COLORTRACK_READ_NOTIFY_LASER_UUID)
#        self.add_notify(self.COLORTRACK_TEMP_HUM_READ_NOTIFY_UUID, self.notify_temp_hum_callback) # no callbacks received!?

#        # weights for averaging (length 20) # ColorTrack sends about 65 laser readings per second
#        self._weights:Final[npt.NDArray[np.float64]] = np.array(range(1, 20))
#        # received but not yet consumed readings (mapped)
#        self._received_readings:npt.NDArray[np.float64] = np.array([])

        # median window size needs to be odd
        self.medianfilter = LiveMedian(median_window_size if median_window_size % 2 == 1 else median_window_size+1)
        self.meanfilter = LiveMean(mean_window_size)
        self.median:float = -1
        self.mean:float = -1


    # maps received byte decimal value to ColorTrack readings in range 0-100
    @staticmethod
    def map_reading(x:int) -> float:
        return min(100, max(0, 3.402e-8 *x*x + 1.028e-6 * x - 0.0069))

    def register_reading(self, value:float) -> None:
#        self._received_readings = np.append(self._received_readings, value)
        self.median = self.medianfilter(value)
        self.mean = self.meanfilter(value)
        if self._logging:
            _log.info('register_reading: %s',value)

    # converts pairs of bytes of paloads to readings
    def register_readings(self, payload:bytearray) -> None:
        for i in range(0, len(payload), 2):
            if len(payload)>i+1:
                self.register_reading(self.map_reading(payload[i]*256 + payload[i+1]))



    # second result is the raw average
    def getColor(self) -> Tuple[float, float]:
#        read_res = self.read(self.COLORTRACK_READ_NOTIFY_LASER_UUID) # returns 20 bytes (same format as via the notifications)
#        _log.debug('getLaser: %s',read_res)

#        try:
#            number_of_readings = len(self._received_readings)
#            if number_of_readings == 1:
#                return float(self._received_readings[0]), float(self._received_readings[0])
#            if number_of_readings > 1:
#                # consume and average the readings
#                l = min(len(self._weights), number_of_readings)
#                res:float = float(np.average(self._received_readings[-l:], weights=self._weights[-l:]))
#                self._received_readings = np.array([])
#                return res, res
#        except Exception as e: # pylint: disable=broad-except
#            _log.exception(e)
#        return -1, -1

        return self.mean, self.median


    def notify_laser_callback(self, _sender:'BleakGATTCharacteristic', payload:bytearray) -> None:
        self.register_readings(payload)

#    @staticmethod
#    def notify_temp_hum_callback(_sender:'BleakGATTCharacteristic', payload:bytearray) -> None:
#        _log.info('temp/hum: %s', payload)

    def on_connect(self) -> None: # pylint: disable=no-self-use
#        self._received_readings = np.array([])
        if self._connected_handler is not None:
            self._connected_handler()

    def on_disconnect(self) -> None: # pylint: disable=no-self-use
        if self._disconnected_handler is not None:
            self._disconnected_handler()



def main() -> None:
    import time
    from artisanlib.atypes import SerialSettings
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
