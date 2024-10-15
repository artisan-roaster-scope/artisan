#
# ABOUT
# Santoker R BLE support for Artisan

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
# Marko Luther, 2024

import logging
from typing import Optional, Final, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from bleak.backends.characteristic import BleakGATTCharacteristic  # pylint: disable=unused-import


from artisanlib.ble_port import ClientBLE


_log = logging.getLogger(__name__)


class SantokerR(ClientBLE):

    # Santoker R (manual version) service and characteristics UUIDs
    SANTOKER_R_NAME:Final[str] = 'Santoker'
    SANTOKER_R_SERVICE_UUID:Final[str] = '0000fff0-0000-1000-8000-00805f9b34fb' # advertised service UUID
    SANTOKER_R_NOTIFY_UUID:Final[str] = '0000fff5-0000-1000-8000-00805f9b34fb'


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

        # register Santoker R UUIDs
        self.add_device_description(self.SANTOKER_R_SERVICE_UUID, self.SANTOKER_R_NAME)
        self.add_notify(self.SANTOKER_R_NOTIFY_UUID, self.notify_callback)

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
        if len(data) > 3:
            self._BT = int.from_bytes(data[0:2], 'big') / 10
            self._ET = int.from_bytes(data[2:4], 'big') / 10

    def getBT(self) -> float:
        return self._BT

    def getET(self) -> float:
        return self._ET
