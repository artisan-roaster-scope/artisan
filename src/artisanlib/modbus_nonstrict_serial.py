#
# ABOUT
# MODBUS HACK for pymodbus 3.7.x reconstructing the non-strict mode of v3.6.x
# see https://github.com/pymodbus-dev/pymodbus/discussions/2322

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

from pymodbus.client import ModbusSerialClient
from pymodbus.logging import Log
from typing import TYPE_CHECKING

try:
    import serial

    PYSERIAL_MISSING = False
except ImportError:
    PYSERIAL_MISSING = True
    if TYPE_CHECKING:  # always False at runtime
        # type checkers do not understand the Raise RuntimeError in __init__()
        import serial

class ModbusSerialClientNonStrict(ModbusSerialClient):
    def connect(self) -> bool:
        """Connect to the modbus serial server."""
        if self.socket:
            return True
        try:
            self.socket = serial.serial_for_url( # type:ignore[reportAttributeAccessIssue,unused-ignore]
                self.comm_params.host,
                timeout=self.comm_params.timeout_connect,
                bytesize=self.comm_params.bytesize,
                stopbits=self.comm_params.stopbits,
                baudrate=self.comm_params.baudrate,
                parity=self.comm_params.parity,
                exclusive=True,
            )
# ONLY DIFF to the original connect method of pymodbus 3.7.x is
#   not to set the inter_byte_timeout as this seems to disturb communication
#   with some hardware on Windows
#   by default pymodbus v3.7 sets a calculated inter_byte_timeout on connect()
#   here we prevent this by commenting the next line
#            self.socket.inter_byte_timeout = self.inter_byte_timeout
            self.last_frame_end = None
        # except serial.SerialException as msg:
        # pyserial raises undocumented exceptions like termios
        except Exception as msg:  # pylint: disable=broad-exception-caught
            Log.error('{}', msg) # type:ignore[no-untyped-call]
            self.close() # type:ignore[no-untyped-call]
        return self.socket is not None
