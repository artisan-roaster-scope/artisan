#
# ABOUT
# Thermoworks Bluedot Thermometer support for Artisan
# see https://github.com/lamroger/artisan-websocket-bluedot

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
# Marko Luther, 2025

import logging
from typing import Optional, Final, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from bleak.backends.characteristic import BleakGATTCharacteristic  # pylint: disable=unused-import


from artisanlib.ble_port import ClientBLE


_log = logging.getLogger(__name__)


class BlueDOT(ClientBLE):

    # Thermoworks Bluedot Thermometer service and characteristics UUIDs
    BlueDOT_NAME:Final[str] = 'BlueDOT'
    #BlueDOT_SERVICE_UUID:Final[str] = '???'
    BlueDOT_NOTIFY_UUID:Final[str] = '783f2991-23e0-4bdc-ac16-78601bd84b39'


    def __init__(self,
                    connected_handler:Optional[Callable[[], None]] = None,
                    disconnected_handler:Optional[Callable[[], None]] = None) -> None:
        super().__init__()

        # handlers
        self.connected_handler:Optional[Callable[[], None]] = connected_handler
        self.disconnected_handler:Optional[Callable[[], None]] = disconnected_handler

        # configuration
        self._logging = False         # if True device communication is logged

        # readings
        self._BT:float = -1
        self._ET:float = -1

        # register BlueDOT UUIDs
        self.add_device_description(
            #self.BlueDOT_SERVICE_UUID,
            self.BlueDOT_NAME)
        self.add_notify(self.BlueDOT_NOTIFY_UUID, self.notify_callback)

    def setLogging(self, b:bool) -> None:
        self._logging = b

    def reset_readings(self) -> None:
        self._BT = -1
        self._ET = -1


    def on_connect(self) -> None:
        if self.connected_handler is not None:
            self.connected_handler()

    def on_disconnect(self) -> None:
        self.reset_readings()
        if self.disconnected_handler is not None:
            self.disconnected_handler()


    def notify_callback(self, _sender:'BleakGATTCharacteristic', data:bytearray) -> None:
        if self._logging:
            _log.debug('notify: %s', data)
        if len(data) > 4:
            BT = ((data[1] & 0xFF) |
                    ((data[2] & 0xFF) << 8) |
                    ((data[3] & 0xFF) << 16) |
                    ((data[4] & 0xFF) << 24))
            # BLE delivers a new reading about every 0.5sec which we average
            self._BT = (BT if self._BT == -1 else (2*BT + self._BT)/3)


    def getBT(self) -> float:
        return self._BT

    def getET(self) -> float:
        return self._ET
