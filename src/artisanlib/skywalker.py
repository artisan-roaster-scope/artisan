#
# ABOUT
# Skywalker V2 "Cyberroaster" (ITOP FIR radiant electric drum) support for Artisan
#
# Minimal, additive device for the Cyberroaster fork. Talks to the roaster's
# TC4-over-BLE bridge (model "TD5325A"): reads BT/ET telemetry and drives the
# burner / airflow / drum outputs (OT channels).
#
# Transport: subclasses artisanlib.ble_port.ClientBLE, so discovery connects to
# the FIRST device that broadcasts the FF00 service with the "TD5325A" name
# prefix (no stored peripheral UUID). Reconnect and the macOS single-loop
# constraint are handled by ClientBLE.
#
# Protocol (TC4 over BLE):
#   FF01 (notify) : CSV telemetry "ambient,ET,BT,burner,airflow,...", CRLF-ended.
#                   Emitted ONLY in response to a READ command (nothing streams
#                   unsolicited), so we poll READ on the ClientBLE heartbeat.
#   FF02 (write)  : LF-terminated TC4 commands (CHAN, READ, OTn,<duty>).
#   On connect we init the channel map (CHAN;1200) and assert OT1,0 — connecting
#   alone leaves the burner at a default high duty, so burner-off is a safety must.

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

import logging
import threading
from typing import Final, TYPE_CHECKING

from artisanlib.ble_port import ClientBLE

if TYPE_CHECKING:
    from bleak.backends.characteristic import BleakGATTCharacteristic  # pylint: disable=unused-import
    from collections.abc import Callable  # pylint: disable=unused-import

_log: Final[logging.Logger] = logging.getLogger(__name__)


class Skywalker(ClientBLE):

    # Skywalker V2 TC4-over-BLE bridge (TD5325A) service and characteristics
    SKYWALKER_NAME:Final[str]    = 'TD5325A'                                # advertised name prefix
    SKYWALKER_SERVICE:Final[str] = '0000ff00-0000-1000-8000-00805f9b34fb'  # advertised service UUID
    SKYWALKER_NOTIFY:Final[str]  = '0000ff01-0000-1000-8000-00805f9b34fb'  # TC4 telemetry (RX)
    SKYWALKER_WRITE:Final[str]   = '0000ff02-0000-1000-8000-00805f9b34fb'  # TC4 commands (TX)

    # TC4 protocol
    POLL_S:Final[float]  = 1.0          # READ poll cadence (keep <= sample interval / 2)
    CMD_TERM:Final[str]  = '\n'         # commands are LF-terminated
    LINE_TERM:Final[bytes] = b'\r\n'    # telemetry lines are CRLF-terminated
    CHAN_INIT:Final[str] = 'CHAN;1200'  # logical->physical channel map (Artisan default)
    READ_CMD:Final[str]  = 'READ'       # request one CSV telemetry line

    # OT output channels
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
    IDX_ET:Final[int]      = 1
    IDX_BT:Final[int]      = 2
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
        self._ambient:float = -1
        self._bt:float = -1
        self._et:float = -1
        self._burner:float = -1
        self._airflow:float = -1

        self.add_device_description(self.SKYWALKER_SERVICE, self.SKYWALKER_NAME)
        self.add_notify(self.SKYWALKER_NOTIFY, self.notify_callback)
        self.add_write(self.SKYWALKER_SERVICE, self.SKYWALKER_WRITE)
        # poll READ on the ClientBLE heartbeat (no-op while disconnected)
        self.set_heartbeat(self.POLL_S)

    # ── command TX ────────────────────────────────────────────────────────────
    @classmethod
    def _normalize(cls, cmd:str) -> str:
        # TC4 firmware wants an integer duty (OT2,25 not OT2,25.0) and rejects
        # out-of-range values, so coerce and clamp 'OTn,<duty>'.
        head, sep, val = cmd.strip().partition(',')
        if sep and head.upper().startswith('OT'):
            try:
                channel = int(head[2:])
                duty = int(float(val))
            except ValueError:
                return cmd.strip()
            lo, hi = cls.CLAMP.get(channel, (0, 100))
            return f'{head},{max(lo, min(hi, duty))}'
        return cmd.strip()

    # send a raw TC4 command, e.g. "OT1,50" (burner), "OT2,80" (airflow)
    def send(self, cmd:str) -> None: # type:ignore[override]
        if not cmd:
            return
        msg = self._normalize(cmd)
        if self._logging:
            _log.debug('TX: %s', msg)
        super().send((msg + self.CMD_TERM).encode())

    # ── telemetry RX ──────────────────────────────────────────────────────────
    # runs in the ClientBLE async loop thread
    def notify_callback(self, _sender:'BleakGATTCharacteristic', data:bytearray) -> None:
        if self._logging:
            _log.debug('notify: %s', data)
        # the bridge may fragment or coalesce frames, so accumulate then split on CRLF
        self._buf.extend(data)
        while self.LINE_TERM in self._buf:
            line, _, rest = self._buf.partition(self.LINE_TERM)
            self._buf = bytearray(rest)
            self._parse(bytes(line))

    def _parse(self, line:bytes) -> None:
        try:
            parts = line.decode('ascii', 'ignore').split(',')
            ambient = float(parts[self.IDX_AMBIENT])
            et = float(parts[self.IDX_ET])
            bt = float(parts[self.IDX_BT])
        except (ValueError, IndexError):
            _log.debug('unparsable TC4 line: %r', line)
            return
        # actuator duty echoes (optional fields)
        try:
            burner = int(float(parts[self.IDX_BURNER]))
        except (ValueError, IndexError):
            burner = -1
        try:
            airflow = int(float(parts[self.IDX_AIRFLOW]))
        except (ValueError, IndexError):
            airflow = -1
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
            return self._ambient

    # burner (OT1) and airflow (OT2) duty echoes (%) for the extra device channel
    def getPF(self) -> tuple[float,float]:
        with self._lock:
            return self._burner, self._airflow

    # ── ClientBLE hooks ───────────────────────────────────────────────────────
    def on_connect(self) -> None:
        # init the TC4 channel map, then assert burner OFF (safety: connecting
        # alone leaves the burner at a default high duty)
        self.send(self.CHAN_INIT)
        self.send(f'OT{self.OT_BURNER},0')
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
        self.send(self.READ_CMD)
