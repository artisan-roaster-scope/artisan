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

try:
    from PyQt6.QtCore import QRegularExpression # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QRegularExpression # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from typing import Final, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtCore import QRegularExpressionMatch # pylint: disable=unused-import
    from artisanlib.types import SerialSettings # pylint: disable=unused-import
    import numpy.typing as npt # pylint: disable=unused-import


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
            _log.debug('received line: %s',line)
        match:QRegularExpressionMatch = self._color_regex.match(line.decode('ascii', errors='ignore'))
        if match.hasMatch() and match.hasCaptured(0):
            try:
                first_match:str = match.captured(0)
                value:float = float(first_match)
                self.register_reading(value)
            except Exception as e: # pylint: disable=broad-except
                _log.error(e)


def main() -> None:
    import time
    from artisanlib.types import SerialSettings
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
