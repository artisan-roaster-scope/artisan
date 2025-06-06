#
# ABOUT
# Hottop 2k+ support for Artisan

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
# Marko Luther, 2023

import time
import logging
import asyncio

from typing import Final, Optional, Tuple, Callable

from artisanlib.atypes import SerialSettings
from artisanlib.async_comm import AsyncComm


_log: Final[logging.Logger] = logging.getLogger(__name__)


class Hottop(AsyncComm):
    HEADER:Final[bytes] = b'\xa5\x96' # 165, 150

    SEND_INTERVAL:Final[float] = 0.3 # in seconds (should be larger than >100ms and <1s; if machine does not receive anything within 1s it ejects the beans)

    # safety cut-off BT temperature
    BTcutoff:Final[int] = 220        # 220C = 428F (was 212C/413F before)
    BTleaveControl:Final[int] = 180  # 180C = 350F; the BT below which the control can be released; above the control cannot be released to avoid sudden stop at high temperatures

    __slots__ = [ '_bt', '_et', '_heater', '_main_fan', '_fan', '_solenoid', '_drum_motor', '_cooling_motor', '_control_active',
                    '_set_heater', '_set_fan', '_set_main_fan', '_set_solenoid', '_set_drum_motor', '_set_cooling_motor', '_last_write' ]


    def __init__(self, host:str = '127.0.0.1', port:int = 8080, serial:Optional['SerialSettings'] = None,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None) -> None:

        super().__init__(host, port, serial, connected_handler, disconnected_handler)

        # current readings
        self._bt:float = -1         # bean temperature in °C
        self._et:float = -1         # environmental temperature in °C
        self._heater:int = 0        # heater power in % [0-100]
        self._main_fan:int = 0      # fan speed in % [0-100]   # Hottop allows only values from 0-10!
        self._fan:int = 0           # cooling fan in % [0-100] # Hottop allows only values from 0-10!
        self._solenoid:int = 0      # 0: closed, 1: open
        self._drum_motor:int = 0    # 0: closed, 1: open
        self._cooling_motor:int = 0 # 0: closed, 1: open (stirrer)

        # control
        self._control_active = False # True while Artisan is controlling the Hottop
        # if a set value is -1 the corresponding process value is send
        self._set_heater:int = -1
        self._set_fan:int = -1
        self._set_main_fan:int = -1
        self._set_solenoid:int = -1
        self._set_drum_motor:int = -1
        self._set_cooling_motor:int = -1
        self._last_write = time.time()


    # message encoder/decoder

    def valid_message(self, message:bytearray) -> bool:
        return (len(message) == 36 and
            self.HEADER[0:2] == message[0:2] and
            (not self._verify_crc or int(message[35]) == sum(int(c) for c in message[:35]) & 0xFF))


    # asyncio read implementation

    # https://www.oreilly.com/library/view/using-asyncio-in/9781492075325/ch04.html
    async def read_msg(self, stream: asyncio.StreamReader) -> None:
        # look for the first header byte
        message = bytearray()
        await stream.readuntil(self.HEADER[0:1])
        # check for the second header byte
        if await stream.readexactly(1) != self.HEADER[1:2]:
            return
        message.extend(self.HEADER)
        # read the remainder of the message
        message_body = await stream.readexactly(34)
        message.extend(message_body)
        if self.valid_message(message):
            if self._logging:
                _log.info('valid message received: %s', message)
            #VERSION = int(message[4])               # => 1 (first released version)
            self._heater = int(message[10])
            self._fan = int(message[11])
            self._main_fan = int(message[12]) * 10   # machine returns 0-10
            self._et = int(message[23]) * 256 + int(message[24])
            self._bt = int(message[25]) * 256 + int(message[26])
            self._solenoid = int(message[16])
            self._drum_motor = int(message[17])
            self._cooling_motor = int(message[18])
            #CHAFF_TRAY = int(message[19])
            if self._control_active:
                # safety cut
                if self.BTcutoff <= self._bt:
                    self._set_heater = 0
                    #self._set_fan = 10
                    self._set_main_fan = 10
                    self._set_solenoid = 1
                    self._set_drum_motor = 1
                    self._set_cooling_motor = 1
                if time.time() > self._last_write + self.SEND_INTERVAL:
                    self.send_control()
        elif self._logging:
            _log.info('invalid message received: %s', message)

    def reset_readings(self) -> None:
        self._bt = -1
        self._et = -1
        self._heater = 0
        self._main_fan = 0
        self._fan = 0
        self._solenoid = 0
        self._drum_motor = 0
        self._cooling_motor = 0

    # prefers set_value, and returns get_value if set_value is -1. If both are -1, returns 0
    @staticmethod
    def newValue(set_value:int, get_value:int) -> int:
        if set_value != -1:
            return set_value
        if get_value != -1:
            return get_value
        return 0

    # message encoder
    def create_msg(self) -> bytes:
        cmd = bytearray([0x00]*36)
        cmd[0] = 0xA5
        cmd[1] = 0x96
        cmd[2] = 0xB0
        cmd[3] = 0xA0
        cmd[4] = 0x01
        cmd[5] = 0x01
        cmd[6] = 0x24
        cmd[10] = self.newValue(self._set_heater, self._heater)
        cmd[11] = int(round(self.newValue(self._set_fan, self._fan) / 10.))
        cmd[12] = int(round(self.newValue(self._set_main_fan, self._main_fan) / 10.))
        cmd[16] = self.newValue(self._set_solenoid, self._solenoid)
        cmd[17] = self.newValue(self._set_drum_motor, self._drum_motor)
        cmd[18] = self.newValue(self._set_cooling_motor, self._cooling_motor)
        cmd[35] = sum(list(cmd[:35])) & 0xFF # checksum
        return bytes(cmd)

    def send_control(self) -> None:
        self.send(self.create_msg())

    # External Interface

    def takeHottopControl(self) -> bool:
        if self._bt <= self.BTcutoff:
            self._control_active = True
            return True
        return False

    def releaseHottopControl(self) -> bool:
        if self._bt < self.BTleaveControl:
            self._control_active = False
            return True
        return False

    def hasHottopControl(self) -> bool:
        return self._control_active

    def getState(self) -> Tuple[float, float, int, int]:
        return self._bt, self._et, self._heater, self._main_fan

    # heater : int(0-100)
    # fan, main_fan : int(0-100) (will be converted to the internal int(0-10))
    # solenoid, drum_motor, cooling_motor : bool (will be converted to the internal 0 or 1)
    # all parameters are optional and default to None (meanging: don't change value)
    def setHottop(self, heater:Optional[int]=None, fan:Optional[int]=None, main_fan:Optional[int]=None,
            solenoid:Optional[bool]=None, drum_motor:Optional[bool]=None, cooling_motor:Optional[bool]=None) -> None:
        _log.debug('setHottop(heater: %s, fan: %s, main_fan: %s, solenoid: %s, drum_motor: %s, cooling_motor: %s)', heater, fan, main_fan, solenoid, drum_motor, cooling_motor)
        if self._control_active:
            if heater is not None:
                self._set_heater = max(0,min(heater,100))
            if fan is not None:
                self._set_fan = max(0,min(fan,100))
            if main_fan is not None:
                self._set_main_fan = max(0,min(main_fan,100))
            if solenoid is not None:
                self._set_solenoid = (1 if solenoid else 0)
            if drum_motor is not None:
                self._set_drum_motor = (1 if drum_motor else 0)
            if cooling_motor is not None:
                self._set_cooling_motor = (1 if cooling_motor else 0)

def main() -> None:
    hottop_serial = SerialSettings(
        port = '/dev/slave',
        baudrate = 9600,
        bytesize = 8,
        stopbits = 1,
        parity = 'N',
        timeout = 0.3)
    hottop = Hottop(serial=hottop_serial)
    hottop.start()
    for _ in range(4):
        hottop.setHottop(heater=35) # set power to 35%
        time.sleep(1)
        print('state',hottop.getState())
        time.sleep(1)
    hottop.stop()
    time.sleep(1)
    #print('thread alive?',hottop._thread.is_alive())

if __name__ == '__main__':
    main()
