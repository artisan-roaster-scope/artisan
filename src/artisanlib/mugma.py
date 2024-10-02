#
# ABOUT
# Mugma support for Artisan

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
from typing import Final, Optional, Callable

from artisanlib.async_comm import AsyncComm

_log: Final[logging.Logger] = logging.getLogger(__name__)

class Mugma(AsyncComm):

    __slots__ = [ 'device_logging', '_bt', '_et', '_heater', '_fan', '_catalyzer', '_sv' ]

    def __init__(self, host:str = '127.0.0.1', port:int = 1504, device_logging:bool = False,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None) -> None:

        self.device_logging = device_logging

        super().__init__(host, port, None, connected_handler, disconnected_handler)

        # current readings
        self._et:float = -1         # environmental temperature in °C
        self._bt:float = -1         # bean temperature in °C
        self._fan:float = -1        # fan speed in % [0-100]
        self._heater:float = -1     # heater power in % [0-100]
        self._catalyzer:float = -1  # catalyzer heating power in %
        self._sv:float = -1         # target temperature (SV) in °C


    # external API to access machine state

    def getET(self) -> float:
        return self._et
    def getBT(self) -> float:
        return self._bt
    def getFan(self) -> float:
        return self._fan
    def getHeater(self) -> float:
        return self._heater
    def getCatalyzer(self) -> float:
        return self._catalyzer
    def getSV(self) -> float:
        return self._sv

    def resetReadings(self) -> None:
        self._bt = -1
        self._et = -1
        self._heater = -1
        self._fan = -1
        self._catalyzer = -1
        self._sv = -1


    # asyncio read implementation

    # https://www.oreilly.com/library/view/using-asyncio-in/9781492075325/ch04.html
    async def read_msg(self, stream: asyncio.StreamReader) -> None:
        # read line
        try:
            data:bytes = await stream.readline()
            if self.device_logging:
                _log.info('data: %s', data)
            reading = data.decode('utf-8').strip().split(',')
            if len(reading) > 9 and reading[0] == '1':
                # system status received
                self._et = float(reading[4]) / 10
                self._bt = float(reading[5]) / 10
                self._fan = int(reading[6])  # investigate: should this also be divided by 10!?
                self._heater = float(reading[7]) / 10
                self._catalyzer = float(reading[8]) / 10
                self._sv = float(reading[9]) / 10
        except ValueError:
            # buffer overrun
            pass



def main() -> None:
    import time
    mugma = Mugma(host = '127.0.0.1', port = 1504)
    mugma.start()
    for _ in range(4):
        print('>>> hallo')
        print('BT',mugma.getBT())
        time.sleep(1)
    mugma.stop()
    time.sleep(1)
    #print('thread alive?',mugma._thread.is_alive())

if __name__ == '__main__':
    main()
