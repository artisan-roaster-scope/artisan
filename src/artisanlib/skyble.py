#
# ABOUT
# Skywalker V2 support for Artisan through Skycommand dongle
#

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# programming by Tilau

import logging
import threading
from typing import Final, TYPE_CHECKING

from artisanlib.ble_port import ClientBLE

if TYPE_CHECKING:
    from bleak.backends.characteristic import BleakGATTCharacteristic  # pylint: disable=unused-import
    from collections.abc import Callable  # pylint: disable=unused-import

_log: Final[logging.Logger] = logging.getLogger(__name__)


class SkyBLE(ClientBLE):

    # Skywalker V1 Skycommand ESP32 custom service and characteristics
    # download esp32 S3 4Mb flash here https://github.com/ThankGod886/SkywalkerRoasterLab/tree/main/CONTROLLER

    SKYCOMMAND_NAME:Final[str]    = 'ESP32_Skycommand_BLE'                  # advertised name prefix
    SKYCOMMAND_SERVICE:Final[str] = '6e400001-b5a3-f393-e0a9-e50e24dcca9e'  # advertised service UUID
    SKYCOMMAND_NOTIFY:Final[str]  = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'  # TC4 telemetry (RX)
    SKYCOMMAND_WRITE:Final[str]   = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'  # TC4 commands (TX)

    # TC4 protocol
    POLL_S:Final[float]  = 1.0          # READ poll cadence (keep <= sample interval / 2)
    CMD_TERM:Final[str]  = '\n'         # commands are LF-terminated
    LINE_TERM:Final[bytes] = b'\r\n'    # telemetry lines are CRLF-terminated
    CHAN_INIT:Final[str] = 'CHAN;1200'  # logical->physical channel map (Artisan default)
    READ_CMD:Final[str]  = 'READ'       # request one CSV telemetry line

    # output channels
    OT_BURNER:Final[int]  = 1
    OT_AIRFLOW:Final[int] = 2
    OT_DRUM:Final[int]    = 3
    OT_EXHAUST:Final[int] = 4
    CLAMP:Final[dict[int,tuple[int,int]]] = {
        OT_BURNER:  (0, 100),
        OT_AIRFLOW: (0, 100),
        OT_DRUM:    (60, 100),
        OT_EXHAUST: (1, 4),
    }

    # CSV field order (physical probe swap: field[2] = bean (BT), field[1] = drum (ET))
    IDX_AMBIENT:Final[int] = 0
    IDX_ET:Final[float]      = 1
    IDX_BT:Final[float]      = 2
    IDX_BURNER:Final[int]  = 3   # OT1 duty echo
    IDX_AIRFLOW:Final[int] = 4   # OT2 duty echo

    def __init__(self,
                    connected_handler:'Callable[[], None]|None' = None,
                    disconnected_handler:'Callable[[], None]|None' = None) -> None:
        super().__init__()

        # handlers
        self._connected_handler = connected_handler
        self._disconnected_handler = disconnected_handler

        # latest telemetry (Celsius / %), guarded by _lock as the sampling thread reads it
        self._lock = threading.Lock()
        self._buf = bytearray()
        self._ambient:int = -1
        self._bt:float = -1.0
        self._et:float = -1.0
        self._burner:int = -1
        self._airflow:int = -1

        self.add_device_description(self.SKYCOMMAND_SERVICE, self.SKYCOMMAND_NAME)
        self.add_notify(self.SKYCOMMAND_NOTIFY, self.notify_callback)
        self.add_write(self.SKYCOMMAND_SERVICE, self.SKYCOMMAND_WRITE)
        # poll READ on the ClientBLE heartbeat (no-op while disconnected)
        self.set_heartbeat(self.POLL_S)
        _log.info("Skycommand BLE initialized, poll %.1fs", self.POLL_S)

    # ── command TX ────────────────────────────────────────────────────────────
    # expected syntax is "command,value"
    @classmethod
    def _normalize(cls, cmd:str) -> str:
        _log.info("Skycommand normalizing : %s", cmd)
        head, sep, val = cmd.strip().partition(',')
        if sep and head.upper().startswith('OT'):
            try:
                channel = int(head[2:])
                duty = int(float(val))
            except ValueError:
                return cmd.strip()
            lo, hi = cls.CLAMP.get(channel, (0, 100))
            return f'{head};{max(lo, min(hi, duty))}'
        return cmd.strip()

    # send a raw TC4 command, e.g. "OT1,50" (burner), "OT2,80" (airflow)
    def send_command(self, cmd:str) -> None: # type:ignore[override]
        _log.info("Skycommand sending command: %s", cmd)
        if not cmd:
            return
        msg = self._normalize(cmd)
        _log.info('Skycommand TX: %s', msg)
        super().send((msg + self.CMD_TERM).encode())

    # ── telemetry RX ──────────────────────────────────────────────────────────
    # runs in the ClientBLE async loop thread
    def notify_callback(self, _sender:'BleakGATTCharacteristic', data:bytearray) -> None:
        # the bridge may fragment or coalesce frames, so accumulate then split on CRLF
        _log.info("Skycommand received notification")
        self._buf.extend(data)
        while self.LINE_TERM in self._buf:
            line, _, rest = self._buf.partition(self.LINE_TERM)
            self._buf = bytearray(rest)
            self._parse(bytes(line))

    # received telemetry is a CSV line: "ambient,et,bt[,burner,airflow]"
    # avoid to erase current value if there is a parsing error, use previous value instead
    def _parse(self, line:bytes) -> None:
        with self._lock:
            et:float = self._et
            bt:float = self._bt
            ambient:int = self._ambient
            burner:int = self._burner
            airflow:int = self._airflow
        try:
            parts = line.decode('ascii', 'ignore').split(',')
            ambient = int(parts[self.IDX_AMBIENT])
            et = float(parts[self.IDX_ET])
            bt = float(parts[self.IDX_BT])
            _log.info('Skycommand parsed line: ambient=%d, et=%.1f, bt=%.1f', ambient, et, bt)
        except (ValueError, IndexError):
            _log.info('Skycommand unparsable line: %r', line)
            return
        # actuator duty echoes (optional fields)
        try:
            burner = int(float(parts[self.IDX_BURNER]))
        except (ValueError, IndexError):
            pass
        try:
            airflow = int(float(parts[self.IDX_AIRFLOW]))
        except (ValueError, IndexError):
            pass
        with self._lock:
            self._ambient = ambient
            self._et = et
            self._bt = bt
            self._burner = burner
            self._airflow = airflow

    # ── device contract (Celsius / % accessors, like the other BLE devices) ───
    def getBTET(self) -> tuple[float,float]:
        with self._lock:
            return self._bt, self._et

    def getBT(self) -> float:
        with self._lock:
            return self._bt

    def getET(self) -> float:
        with self._lock:
            return self._et

    def getAmbient(self) -> float:
        with self._lock:
            return float(self._ambient)

    # burner (OT1) and airflow (OT2) duty echoes (%) for the extra device channel
    def getPF(self) -> tuple[float,float]:
        with self._lock:
            return float(self._burner), float(self._airflow)

    # ── ClientBLE hooks ───────────────────────────────────────────────────────
    def on_connect(self) -> None:
        # init the TC4 channel map, then assert burner OFF (safety: connecting
        # alone leaves the burner at a default high duty)
        self.send_command(self.CHAN_INIT)
#        self.send_command(f'OT{self.OT_BURNER},0')
        if self._connected_handler is not None:
            self._connected_handler()

    def on_disconnect(self) -> None:
        with self._lock:
            self._buf = bytearray()
            self._bt = self._et = self._ambient = -1
            self._burner = self._airflow = -1
        if self._disconnected_handler is not None:
            self._disconnected_handler()

    def heartbeat(self) -> None:
        # poll one telemetry line (nothing streams unsolicited)
        self.send_command(self.READ_CMD)
