#
# ABOUT
# MT-SICS scale support for artisan scope
#
# MT-SICS (Mettler Toledo Standard Interface Command Set) is a widely used,
# published serial protocol spoken by many bench, shipping/parcel, and
# laboratory scales -- not just a single model or product line. This module
# adds support for MT-SICS Level 0 (the minimal command subset: SI, SIR, Z),
# connected over a real serial/USB-CDC port, as an additional scale option
# alongside the existing Acaia Bluetooth/Serial support.
#
# COPYRIGHT (C) 2010-2026 The artisan team represented by
#   Marko Luther <marko.luther@gmx.net> (maintainer) and all contributors
#
# LICENSE
# This program or module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# MAINTAINER
# Marko Luther, 2026
#
# AUTHOR
# proposed by a user, based on real-world use with a Mettler Toledo BC60

import re
import time
import asyncio
import logging
from collections.abc import Callable
from typing import override, Final, TYPE_CHECKING

from artisanlib.async_comm import AsyncComm
from artisanlib.scale import Scale, ScaleSpecs, STATE_ACTION

if TYPE_CHECKING:
    from artisanlib.atypes import SerialSettings # pylint: disable=unused-import

_log: Final[logging.Logger] = logging.getLogger(__name__)


### MT-SICS Level 0 wire protocol

# Serial defaults. Baud is the one setting that commonly varies by scale/site
# configuration (e.g. Setup > Communications > Serial > Baud on a BC60);
# 9600 is both a very common factory default for this class of scale and the
# MT-SICS default. Unlike Acaia's fixed 115200, this may need to become a
# user-configurable setting once a scale that uses a different baud shows up
# in the field -- flagged as an open question in the accompanying proposal.
SERIAL_BAUDRATE: Final[int] = 9600
SERIAL_BYTESIZE: Final[int] = 8
SERIAL_STOPBITS: Final[int] = 1
SERIAL_PARITY: Final[str] = 'N'
# NOTE: keep this short. A large value here (pyserial's read() blocks until
# EITHER the requested byte count arrives OR this timeout elapses, then
# returns whatever it has) combined with a scale that streams lines slower
# than that byte count fills can cause readings to batch up and arrive in
# delayed bursts instead of streaming smoothly -- confirmed in the field.
# This mirrors AcaiaSerial's own SERIAL_TIMEOUT, which uses the same short
# value for the same reason ("short read timeout so the thread can
# poll-and-exit").
SERIAL_TIMEOUT: Final[float] = 0.1

_UNIT_TO_GRAMS: Final[dict[str, float]] = {
    'g': 1.0,
    'kg': 1000.0,
    'lb': 453.59237,
    'oz': 28.349523125,
}

# Typical MT-SICS Level 0 weight response, whitespace-tolerant:
#   "S S      453.60 g"    stable reading, plain decimal + unit
#   "S D      453.60 g"    dynamic / not-yet-stable reading
# <value> additionally allows an optional colon (e.g. "12:07.50") to cover a
# combined pound:ounce format some scales -- confirmed on a real Mettler
# Toledo BC60 configured for US shipping use -- report instead of a plain
# decimal, e.g.:
#   "S S    0:00.00 lb:oz"   0 lb, 0.00 oz (stable zero reading)
#   "S D   12:07.50 lb:oz"   12 lb, 7.50 oz, not yet settled
_WEIGHT_LINE_RE: Final[re.Pattern[str]] = re.compile(r'^\S+\s+(\S)\s+([+-]?[\d:]+\.?\d*)\s+(\S+)\s*$')


def _parse_lb_oz(value_str: str) -> float:
    """Parses a Toledo/MT-SICS combined pound:ounce value like '0:00.00' or
    '12:07.50' (12 lb 7.5 oz) into total ounces."""
    sign = -1.0 if value_str.startswith('-') else 1.0
    value_str = value_str.lstrip('+-')
    pounds_str, _, ounces_str = value_str.partition(':')
    pounds = float(pounds_str) if pounds_str else 0.0
    ounces = float(ounces_str) if ounces_str else 0.0
    return sign * (pounds * 16.0 + ounces)


def parse_weight_line(line: str) -> tuple[float, bool] | None:
    """Returns (weight_in_grams, scale_reported_stable) or None if `line`
    isn't a weight response (e.g. it's an ACK, an error, or noise)."""
    m = _WEIGHT_LINE_RE.match(line.strip())
    if not m:
        return None
    status, value_s, unit_s = m.groups()
    unit = unit_s.lower()
    scale_reported_stable = status.upper() == 'S'
    if unit in ('lb:oz', 'lb-oz', 'lboz'):
        try:
            total_oz = _parse_lb_oz(value_s)
        except ValueError:
            return None
        return total_oz * _UNIT_TO_GRAMS['oz'], scale_reported_stable
    if unit not in _UNIT_TO_GRAMS:
        _log.warning('unrecognized unit %r in line %r -- ignoring reading', unit_s, line)
        return None
    try:
        value = float(value_s)
    except ValueError:
        return None
    return value * _UNIT_TO_GRAMS[unit], scale_reported_stable


class LocalStabilityFilter:
    """MT-SICS's continuous streaming command (SIR) is explicitly allowed to
    report a reading before the scale has mechanically settled -- the S/D
    flag it returns reflects the scale's own real-time judgement, not a
    guarantee. Some scales (shipping/parcel scales in particular, tuned for
    speed over precision) rarely or never flag a reading 'S' through that
    fast path.

    As a fallback, this treats a reading as stable if EITHER the scale
    itself says so, OR the same value has repeated (within a hair of
    floating-point noise) for at least MIN_STABLE_DURATION_S of continuous
    *wall-clock* time. A minimum elapsed time -- not just a repeat count --
    matters: at typical streaming rates two samples can land under 150ms
    apart, so a momentary pause mid-motion (e.g. while lifting a container
    off the platform, rather than removing it in one clean motion) can
    otherwise coincidentally produce two near-identical readings and get
    misclassified as a genuinely settled 'stable' value when the object is
    still partway off the scale. That's been confirmed as a real, if subtle,
    failure mode in a real-world deployment of this same logic, hence the
    time-based (not sample-count-based) requirement here from the start."""

    MIN_STABLE_DURATION_S: Final[float] = 0.5
    EPSILON_G: Final[float] = 0.05

    def __init__(self) -> None:
        self._last_value: float | None = None
        self._streak_start_ts: float | None = None

    def classify(self, weight_g: float, scale_reported_stable: bool, ts: float | None = None) -> bool:
        if ts is None:
            ts = time.monotonic()
        if self._last_value is not None and abs(weight_g - self._last_value) <= self.EPSILON_G:
            assert self._streak_start_ts is not None
        else:
            self._streak_start_ts = ts
        self._last_value = weight_g
        inferred_stable = (ts - self._streak_start_ts) >= self.MIN_STABLE_DURATION_S
        return scale_reported_stable or inferred_stable


class MTSICSProtocol:
    """Implements MT-SICS Level 0 (SI/SIR/Z) framing on top of the byte
    stream supplied by MTSICSAsync/AsyncComm."""

    def __init__(
        self,
        send_message: Callable[[bytes], None],
        weight_changed: Callable[[float, bool], None],
    ) -> None:
        self._send_message = send_message
        self._weight_changed = weight_changed
        self._stability = LocalStabilityFilter()
        self._logging = False
        # MT-SICS Level 0 has no standard self-identification command
        # (unlike Acaia's INFO/STATUS handshake), so these are fixed,
        # conservative defaults rather than auto-detected values -- see the
        # accompanying proposal for discussion on exposing these as a user
        # setting instead.
        self.max_weight: float = 100 * 1000  # g
        self.readability: float = 1  # g
        self.repeatability: float = 20  # g

    def setLogging(self, b: bool) -> None:
        self._logging = b

    def on_connect(self) -> None:
        # a fresh filter per connection: stale state from before a drop
        # shouldn't influence the first readings of a new connection
        self._stability = LocalStabilityFilter()
        if self._logging:
            _log.debug('starting MT-SICS continuous streaming (SIR)')
        self._send_message(b'SIR\r\n')

    def send_tare(self) -> None:
        if self._logging:
            _log.debug('send tare/zero (Z)')
        self._send_message(b'Z\r\n')

    def get_max_weight(self) -> float:
        return self.max_weight

    def get_readability(self) -> float:
        return self.readability

    def get_repeatability(self) -> float:
        return self.repeatability

    async def read_msg(self, stream: asyncio.StreamReader) -> None:
        raw = await stream.readuntil(b'\n')
        try:
            text = raw.decode('ascii', errors='replace')
        except Exception:  # pylint: disable=broad-except
            return
        if not text.strip():
            return
        if self._logging:
            _log.debug('MT-SICS -> %r', text)
        parsed = parse_weight_line(text)
        if parsed is None:
            return
        weight_g, scale_reported_stable = parsed
        stable = self._stability.classify(weight_g, scale_reported_stable)
        self._weight_changed(weight_g, stable)


class MTSICSAsync(AsyncComm):

    __slots__ = [ 'outer_connected_handler', 'outer_disconnected_handler', 'protocol' ]

    def __init__(
        self,
        weight_changed: Callable[[float, bool], None],
        serial: 'SerialSettings | None' = None,
        connected_handler: Callable[[], None] | None = None,
        disconnected_handler: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(serial=serial, connected_handler=self.connected_handler, disconnected_handler=self.disconnected_handler)
        self.outer_connected_handler: Callable[[], None] | None = connected_handler
        self.outer_disconnected_handler: Callable[[], None] | None = disconnected_handler
        self.protocol: MTSICSProtocol = MTSICSProtocol(self.send_message, weight_changed)

    @override
    async def read_msg(self, stream: asyncio.StreamReader) -> None:
        await self.protocol.read_msg(stream)

    ###

    def get_max_weight(self) -> float:
        return self.protocol.get_max_weight()

    def get_readability(self) -> float:
        return self.protocol.get_readability()

    def get_repeatability(self) -> float:
        return self.protocol.get_repeatability()

    ###

    def send_message(self, payload: bytes) -> None:
        self.send(payload)

    def send_tare(self) -> None:
        self.protocol.send_tare()

    ###

    def connected_handler(self) -> None:
        self.protocol.on_connect()
        if self.outer_connected_handler is not None:
            self.outer_connected_handler()

    def disconnected_handler(self) -> None:
        if self.outer_disconnected_handler is not None:
            self.outer_disconnected_handler()


### Artisan Scale

class MTSICSSerial(Scale): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class

    def __init__(
        self,
        model: int,
        ident: str | None,
        name: str | None,
        connected_handler: Callable[[], None] | None = None,
        disconnected_handler: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(model, ident, name)
        self.scale_connected = False
        self.outer_connected_handler = connected_handler
        self.outer_disconnected_handler = disconnected_handler
        self.mtsics: MTSICSAsync | None = None

    @override
    def is_connected(self) -> bool:
        return self.scale_connected

    @override
    def scan(self) -> None:
        import serial.tools.list_ports # pylint: disable=import-outside-toplevel
        comports: ScaleSpecs = [((cp.product if cp.product is not None else cp.device), cp.device) for cp in serial.tools.list_ports.comports()]
        self.scanned_signal.emit(comports)

    @override
    def connect_scale(self, device_logging: bool) -> None:
        if self.ident is not None:
            from artisanlib.atypes import SerialSettings # pylint: disable=import-outside-toplevel
            mtsics_serial = SerialSettings(
                port = self.ident,
                baudrate = SERIAL_BAUDRATE,
                bytesize = SERIAL_BYTESIZE,
                stopbits = SERIAL_STOPBITS,
                parity = SERIAL_PARITY,
                timeout = SERIAL_TIMEOUT,
                clear_HUPCL = False)
            self.mtsics = MTSICSAsync(
                self.weight_changed,
                serial = mtsics_serial,
                connected_handler = self.connected_handler,
                disconnected_handler = self.disconnected_handler)
            self.mtsics.protocol.setLogging(device_logging)
            self.mtsics.setLogging(device_logging)
            self.mtsics.start()

    @override
    def disconnect_scale(self) -> None:
        if self.mtsics is not None:
            self.mtsics.stop()
            self.on_disconnect() # not called automatically by disconnecting via mtsics.stop(), only called automatically if the scale itself disconnects
            self.mtsics = None

    @override
    def tare_scale(self) -> None:
        if self.mtsics is not None:
            self.mtsics.send_tare()

    @override
    def max_weight(self) -> float:
        if self.mtsics is not None:
            return self.mtsics.get_max_weight()
        return 100000

    @override
    def readability(self) -> float:
        if self.mtsics is not None:
            return self.mtsics.get_readability()
        return 1

    @override
    def repeatability(self) -> float:
        if self.mtsics is not None:
            return self.mtsics.get_repeatability()
        return 20

    # MT-SICS Level 0 has no equivalent of Acaia's LED/beep user-feedback
    # commands, so there is nothing to forward here.
    @override
    def signal_user(self, action: STATE_ACTION) -> None:
        del action

    ###

    def weight_changed(self, new_value: float, stable: bool) -> None:
        self.weight_changed_signal.emit(new_value, stable)

    def on_connect(self) -> None:
        self.scale_connected = True
        self.connected_signal.emit()

    def on_disconnect(self) -> None:
        self.scale_connected = False
        self.disconnected_signal.emit()

    ###

    def connected_handler(self) -> None:
        self.on_connect()
        if self.outer_connected_handler is not None:
            self.outer_connected_handler()

    def disconnected_handler(self) -> None:
        self.on_disconnect()
        if self.outer_disconnected_handler is not None:
            self.outer_disconnected_handler()
