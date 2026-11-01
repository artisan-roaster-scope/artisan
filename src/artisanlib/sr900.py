#
# ABOUT
# SR900 roaster BLE support for artisan scope
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

# SR900 roaster BLE driver, built on Artisan's ClientBLE (see ble_port.py).
#
# Frames are fixed 34 byte messages with a trailing checksum over bytes 1..30.
# After connecting, a MAC address request is sent; its response carries the MAC
# from which the per-connection command token is derived. Until that token is
# known the roaster ignores all commands, thus commands issued before the
# handshake completed are queued and flushed once the token arrives.
#
# NOTE on threading: ClientBLE runs the connect/keep alive loop and the loop that
# dispatches the notifications on two different threads, and a write is scheduled
# on the notification loop while the caller blocks waiting for it. Writing from
# notify_callback() thus blocks the very loop that has to carry out the write and
# ends in a BLE timeout 5s later. Everything the handshake response triggers is for
# that reason deferred to heartbeat(), which runs on the other loop.
#
# Control model: MANUAL roast. The fan/heat sliders map to FAN_SET/HEAT_SET
# (levels 0..9) while START carries the firmware roast and cool timers, in minutes.
#
# Ending a roast takes two commands on this roaster, and the machine defaults put them
# on the two Artisan events that mean the same thing:
#   DROP     -> sr900(cool), COOL_DN, which runs the cooling cycle. The roaster keeps
#               reporting ROASTING throughout, see processData()
#   COOL END -> sr900(stop), STOP_ROAST, which returns it to idle once the roaster is cool
#               enough to accept it, see STOP_RETRY_MARGIN_SECS
# OFF issues the stop too, so that a heater or fan is never left running unsupervised. A stop
# refused there cannot be retried, the client being torn down right after, but the refusal
# means the roaster is still cooling, which is the safe state to leave it in.
# The firmware roast timer is thus only a backstop and a long roast time is wanted. MAX_ROAST_TIME
# minutes is the longest confirmed to start; the roaster ignores a START it does not like without
# any response at all, so roasttime is clamped rather than risking a silent refusal. The cool time
# does not enter into it. Both timers are settable via sr900(roasttime,<minutes>) and
# sr900(cooltime,<minutes>).
#
# A *profile* roast should be run logging-only, as the firmware reasserts its schedule
# every minute and would revert any slider writes, thus PROFILE_ROAST/SEND_PROFILE are
# intentionally not implemented. Neither are ROAST_SET/COOLTIME_SET, which apply only
# before a roast started, the START message carrying the same two timers anyway.
#
# The auto stop ends the roast at a fixed bean temperature (see AUTO_STOP_TEMP), carried
# by byte 17 of START and by nothing else, so sr900(autostop,<T>) only stages a value that
# the next start applies. It ships OFF: the roaster is driven from Artisan here, where the
# roast level is the user's to pick, and any armed target silently caps a dark roast.
# Being a code interpreted by the roaster it needs no unit conversion, unlike an Artisan
# alarm, whose limit a machine setup file could only ship in one of the two temperature modes.
#
# Temperatures are reported in Fahrenheit. A status frame carries three fields, which
# are two sensors and a selector:
#  * bytes 17/18, the EXTERNAL probe, inserted through the side into the bean mass,
#    hence BT.
#  * bytes 19/20, the INTERNAL sensor sitting in the base next to the heating element.
#    Under heat it rises ~35F in 8s and peaks the very sample the element switches off,
#    while the external probe lags and keeps climbing after, so this is a fast air
#    temperature next to the element, hence ET. It reads a few degrees above the
#    external probe at idle.
#  * bytes 15/16, whichever of the two the roaster settings select, +64 in the settings
#    byte selecting EXTERNAL. This field only ever mirrors one of the other two and
#    follows the selection as it changes. The driver reads the two sensors directly and
#    ignores it, so that BT is the bean probe whatever the roaster happens to be set to.
# Both are reported as received, without clamping or substituting missing readings.
#
# NOTE: every message here is confirmed against hardware.

from collections.abc import Callable
import logging
import random
import time as libtime
from typing import TYPE_CHECKING, Final, override

from artisanlib.ble_port import ClientBLE

if TYPE_CHECKING:
    from bleak.backends.characteristic import BleakGATTCharacteristic

_log: Final[logging.Logger] = logging.getLogger(__name__)


# -- BLE addressing -----------------------------------------------------------

# data service carrying the roast messages
SR900_SERVICE_UUID: Final[str] = '0000df00-0000-1000-8000-00805f9b34fb'
SR900_WRITE_UUID: Final[str] = '0000df02-0000-1000-8000-00805f9b34fb'
SR900_NOTIFY_UUID: Final[str] = '0000df01-0000-1000-8000-00805f9b34fb'

# SR900 BLE name prefix
DEVICE_NAME_SR900: Final[str] = 'SR900'


# -- wire protocol ------------------------------------------------------------

FRAME_LEN: Final[int] = 34
STX: Final[int] = 0x20
RESERVED: Final[bytes] = bytes((0x53, 0x45, 0x51, 0x4F))  # "SEQO"
ETX_LO: Final[int] = 0x30
ETX_HI: Final[int] = 0x03
CHECKSUM_POS: Final[int] = 31

# request type ids -> (byte5, byte6)
HEAT_SET: Final[tuple[int,int]] = (0, 1)
FAN_SET: Final[tuple[int,int]] = (0, 2)
START_ROAST: Final[tuple[int,int]] = (0, 21)
COOL_DN: Final[tuple[int,int]] = (0, 24)
STOP_ROAST: Final[tuple[int,int]] = (0, 25)
MAC_ADDRESS_REQ: Final[tuple[int,int]] = (0, 38)
SETTINGS: Final[tuple[int,int]] = (0, 43)

# response type ids (byte 6)
RES_ROASTER_STATUS: Final[int] = 33
RES_ROASTER_STARTED: Final[int] = 34
RES_COOLER_STARTED: Final[int] = 35
RES_ROASTER_FINISHED: Final[int] = 36
RES_MAC_ADDRESS: Final[int] = 39
RES_SETTINGS_ACK: Final[int] = 28

# auto stop target -> Which_Roast code (0: OFF), keyed by both the Fahrenheit and the
# Celsius target, which the roaster's own dropdown offers as labels of the same entry.
# The two ranges do not overlap, so sr900(autostop,<T>) takes either unit
AUTO_STOP_TEMP: Final[dict[int, int]] = {
    0: 0,
    410: 6, 420: 7, 430: 8, 440: 9, 450: 16, 470: 17,      # F
    210: 6, 216: 7, 221: 8, 227: 9, 235: 16, 243: 17,      # C, as labelled by the roaster
}

# firmware roast and cool timers carried by START, in minutes.
# 15 is the longest roast time confirmed to start against hardware, with the auto stop both OFF and
# armed, and matches the maximum the roaster's own app offers on its roast time slider. A START
# carrying a value the firmware rejects draws no response of any kind, so roasttime is clamped to
# MAX_ROAST_TIME rather than failing silently
DEFAULT_ROAST_TIME: Final[int] = 15
MAX_ROAST_TIME: Final[int] = 15
DEFAULT_COOL_TIME: Final[int] = 4

# fan level cool() commands after COOL_DN. 3 is what the roaster's own cooling cycle settles on and
# what the manufacturer's app therefore gets, confirmed in fullcap.pcapng across three cooldowns.
# Higher is not better here: roasted beans leave the roast a good deal lighter than they went in and
# too much air lifts them out of the chamber
DEFAULT_COOL_FAN: Final[int] = 3

# firmware auto stop target in F, a key of AUTO_STOP_TEMP; 0 is OFF and the default, so
# that nothing cuts a roast short that the user did not ask for. sr900(autostop,<T>) arms
# it, 470 being the highest target the roaster offers
DEFAULT_AUTO_STOP: Final[int] = 0

# how many heartbeats to wait for the settings acknowledgement before giving up on it
# and sending the queued commands anyway; observed to arrive after 3 to 4 seconds
SETTINGS_ACK_TICKS: Final[int] = 8

# a STOP is refused while the roaster is still hot: it answers with COOLER_STARTED and carries on
# cooling rather than shutting down. The refusal also (re)starts the cooling cycle, so a STOP re-issued
# faster than the cool time keeps restarting it and the roaster can never reach idle to accept the stop
# (observed against hardware: six STOPs 5s apart each answered COOLER_STARTED, with the roaster's own
# elapsed counter resetting each time). The retry interval must therefore exceed the cool time, which
# is why it is derived from it rather than fixed
STOP_RETRY_MARGIN_SECS: Final[int] = 30 # added to the cool time before a STOP is re-issued
STOP_RETRY_LIMIT: Final[int] = 10

# the firmware refuses a START carrying a heater or fan level of 0
MIN_LEVEL: Final[int] = 1

# mains voltage as configured on the roaster -> settings byte contribution
VOLTAGE_BITS: Final[tuple[int, ...]] = (1, 2, 4) # 0: <113V, 1: 113-118V, 2: >118V
VOLTAGE_DEFAULT: Final[int] = 1

# roaster state (status byte 21)
STATE_IDLE: Final[int] = 0
STATE_ROASTING: Final[int] = 1
STATE_COOLING: Final[int] = 2

# how often (in seconds) heartbeat() runs. It re-issues the MAC address request
# while the handshake did not complete, the SR900 being known to drop the first
# request after connect, and completes the handshake once the token arrived
HEARTBEAT_INTERVAL: Final[float] = 1

# how many heartbeats to wait for a MAC address response before re-issuing the request. The reply
# arrives in about a second; re-issuing at that cadence races it, and because the response carries no
# echo of the random bytes it was derived from there is no way to tell which request it answers. A
# reply matched against the wrong random bytes yields a wrong token, which the roaster then ignores
# for the whole connection without any error (observed against hardware). Waiting several heartbeats
# makes an outstanding request the exception rather than the norm
MAC_RETRY_TICKS: Final[int] = 4

# after this many MAC address requests went unanswered the connection is assumed unusable - typically
# the notification subscription silently failed, in which case no response can ever be delivered - and
# the client is disconnected so that ClientBLE rescans and builds a fresh connection
MAC_RETRY_LIMIT: Final[int] = 3

# once the handshake completed, a commanded fan or heater level must show up in the status frames,
# which report the actual levels in every state. If it does not within this many heartbeats the token
# is wrong and every command is being discarded, so the connection is torn down and rebuilt
TOKEN_CHECK_TICKS: Final[int] = 6


def new_frame() -> bytearray:
    b = bytearray(FRAME_LEN)
    b[0] = STX
    b[1:5] = RESERVED
    b[32] = ETX_LO
    b[33] = ETX_HI
    return b


def fill_random(b: bytearray, start: int, end: int) -> None:
    # fill [start..end] inclusive with random padding; those bytes are part of the checksum
    for i in range(start, end + 1):
        b[i] = random.randint(0, 255)


def finalize(b: bytearray) -> bytearray:
    # compute and write the checksum over bytes 1..30; to be called last
    b[CHECKSUM_POS] = sum(b[1:31]) & 0xFF
    return b


def compute_command_token(mac: bytes, rnd: list[int]) -> list[int]:
    # per-connection token carried in bytes 1..4 of every non MAC request frame
    #   token[i] = (MAC[5-i] * rnd[i]) & 0xFF
    # where a MAC byte that is 0 or a power of two is incremented by one first
    bump = {0, 2, 4, 8, 16, 32, 64, 128}
    out = []
    for i, mb in enumerate([mac[5], mac[4], mac[3], mac[2]]):
        factor = mb + 1 if mb in bump else mb
        out.append((factor * (rnd[i] if i < len(rnd) else 0)) & 0xFF)
    return out


def encode_settings_byte(altitude: int = 0, voltage: int = VOLTAGE_DEFAULT) -> int:
    # external thermistor +64, above 3000ft +8, >118V +4, 113-118V +2, <113V +1.
    # The thermistor bit is not configurable: Artisan reports the selected thermistor
    # as BT and only the external probe sits in the bean mass, thus selecting the
    # internal one here would silently turn BT into a second air temperature
    n = 64
    if altitude:
        n += 8
    n += VOLTAGE_BITS[voltage if 0 <= voltage < len(VOLTAGE_BITS) else VOLTAGE_DEFAULT]
    return n


def be16(d: bytes, i: int) -> int:
    return d[i] * 256 + d[i + 1]


class SR900_BLE(ClientBLE):

    def __init__(self,
                connected_handler:Callable[[], None]|None = None,
                disconnected_handler:Callable[[], None]|None = None) -> None:
        super().__init__()

        # register SR900 UUIDs
        self.add_device_description(SR900_SERVICE_UUID, DEVICE_NAME_SR900)
        self.add_notify(SR900_NOTIFY_UUID, self.notify_callback)
        self.add_write(SR900_SERVICE_UUID, SR900_WRITE_UUID)

        # handlers
        self.connected_handler:Callable[[], None]|None = connected_handler
        self.disconnected_handler:Callable[[], None]|None = disconnected_handler

        # roaster side configuration pushed on connect and on every change, to be
        # set from the machine defaults via sr900(altitude,<n>)/sr900(voltage,<n>)
        self._altitude:int = 0
        self._voltage:int = VOLTAGE_DEFAULT

        # firmware auto stop target in F (see the note at the top)
        self._auto_stop_f:int = DEFAULT_AUTO_STOP

        # firmware roast and cool timers in minutes, as carried by START
        self._roast_time:int = DEFAULT_ROAST_TIME
        self._cool_time:int = DEFAULT_COOL_TIME

        # fan level commanded by cool(), see DEFAULT_COOL_FAN
        self._cool_fan_level:int = DEFAULT_COOL_FAN

        # the cooler runs; not derivable from the status frame, see processData()
        self._cooling:bool = False

        # a stop was asked for and the roaster has not reported itself finished yet
        self._stop_requested:bool = False
        self._stop_attempts:int = 0
        self._stop_waited:int = 0

        # handshake state
        self._mac:bytes|None = None
        self._mac_req_rnd:list[int]|None = None
        self._command_token:list[int]|None = None
        # the handshake runs over several heartbeats, see heartbeat()
        self._mac_waited:int = 0
        self._mac_attempts:int = 0
        self._settings_pushed:bool = False
        self._settings_acked:bool = False
        self._settings_waited:int = 0
        self._handshake_done:bool = False
        # commands issued before the handshake completed, flushed once it is done
        self._pending:list[tuple[str,int]] = []
        # a fan/heater level was commanded and is awaiting confirmation in a status frame; until it
        # arrives there is no evidence the command token is accepted, see check_token()
        self._token_confirmed:bool = False
        self._token_waited:int = 0

        # last levels commanded, applied by a subsequent start
        self._last_heat_level:int = 1
        self._last_fan_level:int = 1
        # set once the respective level has actually been commanded, so that check_token()
        # compares only against channels we did in fact write
        self._fan_commanded:bool = False
        self._heat_commanded:bool = False

        self.TX:float = 0
        self.ET:float = -1
        self.BT:float = -1
        self.heater:int = -1
        self.fan:int = -1
        self.state:int = -1
        self.roast_time:int = -1 # roast time in seconds as reported by the roaster

        # drives the MAC address request retry and completes the handshake
        self.set_heartbeat(HEARTBEAT_INTERVAL)

#-----

    # The roaster state as the two flags serialport.SR900() polls it for to drive the autoCHARGE
    # and the autoDROP, see comm.py. A fluid bed is charged into a cold chamber and its BT rises
    # monotonically from ambient, so there is no BT break for the generic autoCHARGE detection to
    # find and CHARGE has to come from the roaster itself. Both are true whether the state was
    # entered by our own command or at the roaster, and also when Artisan connects to a roast
    # that is already under way, for which the roaster sends no STARTED at all

    # True while the roaster reports that it is roasting
    @property
    def isRoasting(self) -> bool:
        return self.state == STATE_ROASTING

    # True while the cooler runs, see processData() on why this is not the status byte alone
    @property
    def isCooling(self) -> bool:
        return self.state == STATE_COOLING

    def clearData(self) -> None:
        self._cooling = False
        self.ET = -1
        self.BT = -1
        self.heater = -1
        self.fan = -1
        self.state = -1
        self.roast_time = -1

    ### ClientBLE interface

    @override
    def on_connect(self) -> None:
        # start the handshake; the reply carries the MAC from which the command token is derived.
        # NOTE: this needs the notifications established, which ClientBLE._connect() arranges by
        # signalling on_connect() after start_notifications(). That call cannot report a failed
        # subscription though, and a subscription can fail (observed: bleak raising
        # "The operation was canceled by the user" on a connect the roaster then dropped), leaving a
        # link on which no response can ever arrive. heartbeat() therefore treats unanswered MAC
        # requests as a dead connection and tears it down, see MAC_RETRY_LIMIT
        self._mac_attempts = 0
        self._mac_waited = 0
        self.request_mac()

    @override
    def on_disconnect(self) -> None:
        self._mac = None
        self._mac_req_rnd = None
        self._command_token = None
        self._mac_waited = 0
        self._mac_attempts = 0
        self._fan_commanded = False
        self._heat_commanded = False
        self._settings_pushed = False
        self._settings_acked = False
        self._settings_waited = 0
        self._handshake_done = False
        self._token_confirmed = False
        self._token_waited = 0
        self._stop_requested = False
        self._pending = []
        self.clearData()
        if self.disconnected_handler is not None:
            self.disconnected_handler()

    # NOTE: this and on_connect() are the only places the driver may write from besides
    # the GUI thread; a write issued from notify_callback() deadlocks, see the note on
    # threading at the top. Everything the MAC address response triggers happens here
    @override
    def heartbeat(self) -> None:
        if self.connected()[0] is None:
            return
        if self._command_token is None:
            # the roaster did not answer our MAC address request yet. Wait several heartbeats before
            # re-issuing: the reply takes about a second and carries no echo of the random bytes it
            # was derived from, so a request re-issued at that cadence races the answer and can leave
            # the token derived from the wrong bytes, which the roaster then silently ignores forever
            self._mac_waited += 1
            if self._mac_waited >= MAC_RETRY_TICKS:
                self._mac_waited = 0
                if self._mac_attempts >= MAC_RETRY_LIMIT:
                    # no answer after several attempts. The notification subscription most likely
                    # failed, in which case no response can ever arrive on this link; drop it so
                    # ClientBLE rescans and connects again
                    _log.error('no MAC address response after %s requests, dropping the connection',
                                self._mac_attempts)
                    self.reconnect()
                else:
                    _log.info('no response to the MAC address request yet, retrying')
                    self.request_mac()
        elif not self._settings_pushed:
            self._settings_pushed = True
            # push the roaster side configuration
            self.push_settings()
        elif not (self._settings_acked or self._settings_waited >= SETTINGS_ACK_TICKS):
            # hold the queued commands back until the roaster acknowledged the settings
            # write. One sent before that acknowledgement, which takes the roaster 3 to 4
            # seconds, was observed being dropped silently and without a response
            self._settings_waited += 1
        elif not self._handshake_done:
            self._handshake_done = True
            # flush the commands that were issued before the handshake completed
            pending = self._pending
            self._pending = []
            for target, value in pending:
                self.send_msg(target, value)
            # only now is the roaster known to answer us
            if self.connected_handler is not None:
                self.connected_handler()
        elif self._stop_requested:
            self._stop_waited += 1
            if self._stop_waited >= self.stop_retry_ticks():
                self._stop_waited = 0
                if self._stop_attempts >= STOP_RETRY_LIMIT:
                    _log.info('SR900 stop not acted on after %s attempts, giving up',
                                self._stop_attempts)
                    self._stop_requested = False
                else:
                    self._stop_attempts += 1
                    self.send_command(self.mac_cmd(STOP_ROAST))
        # NOTE: kept out of the chain above so that it cannot starve the stop retry
        if self._handshake_done and not self._token_confirmed:
            self.check_token()

    # a refused STOP restarts the roaster's cooling cycle, so re-issuing one faster than the cool
    # time keeps the roaster cooling forever and it never reaches the idle state that would let it
    # accept the stop. The retry therefore waits out the cool time plus a margin
    def stop_retry_ticks(self) -> int:
        return int((self._cool_time * 60 + STOP_RETRY_MARGIN_SECS) / HEARTBEAT_INTERVAL)

    # drops the BLE link so that ClientBLE's connect loop rescans and builds a fresh connection.
    # on_disconnect() resets the handshake state
    def reconnect(self) -> None:
        self._disconnect()

    # The roaster reports the actual fan and heater levels in every status frame, in every state.
    # A level we commanded must therefore show up there; if it does not, the command token is not
    # being accepted and every command is being silently discarded. That failure is otherwise
    # invisible - status keeps arriving, temperatures keep updating, the LCDs stay live - and it
    # persists for the whole connection, so the link is dropped and rebuilt instead.
    # Runs once per connection only: during a roast the roaster drives the levels itself (it forces
    # the heater to 0 when cooling), so a later mismatch would not mean the token went bad
    def check_token(self) -> None:
        if not (self._fan_commanded or self._heat_commanded):
            # nothing was commanded, so there is nothing to check against
            self._token_confirmed = True
            return
        if self.fan == -1 or self.heater == -1:
            return # no status frame carrying the levels seen yet
        # compare only the channels actually written; the other one carries the roaster's own
        # setting, which we have no expectation about
        if ((not self._fan_commanded or self.fan == self._last_fan_level) and
                (not self._heat_commanded or self.heater == self._last_heat_level)):
            self._token_confirmed = True
            self._token_waited = 0
            return
        self._token_waited += 1
        if self._token_waited >= TOKEN_CHECK_TICKS:
            self._token_waited = 0
            _log.error('SR900 commanded fan/heat %s/%s not reflected by the roaster (reports %s/%s); '
                        'the command token is not being accepted, reconnecting',
                        (self._last_fan_level if self._fan_commanded else '-'),
                        (self._last_heat_level if self._heat_commanded else '-'),
                        self.fan, self.heater)
            self.reconnect()

#-----

    def request_mac(self) -> None:
        self._mac_attempts += 1
        frame = new_frame()
        frame[5], frame[6] = MAC_ADDRESS_REQ
        fill_random(frame, 7, 30) # bytes 7..10 are RND1..4
        self._mac_req_rnd = [frame[7], frame[8], frame[9], frame[10]]
        finalize(frame)
        # the MAC request keeps the reserved bytes; the token is not applied here
        self.raw_send(frame)

    def raw_send(self, frame:bytearray) -> None:
        # the roaster only acts on acknowledged writes and expects the complete frame in
        # one GATT write, thus the chunk size is pinned to the full frame length here
        if self._logging:
            _log.info('send: %s', bytes(frame).hex())
        self.send(bytes(frame), response=True, write_characteristic=SR900_WRITE_UUID, chunk=FRAME_LEN)

    def send_command(self, frame:bytearray) -> None:
        # every command but the MAC request carries the per-connection token in bytes 1..4
        if self._command_token is None:
            _log.debug('command dropped, handshake not completed')
            return
        frame[1:5] = bytes(self._command_token)
        finalize(frame)
        self.raw_send(frame)

    def mac_cmd(self, type_ids:tuple[int,int]) -> bytearray:
        b = new_frame()
        b[5], b[6] = type_ids
        b[7:13] = self._mac or bytes(6)
        fill_random(b, 13, 30)
        return finalize(b)

    def value_cmd(self, type_ids:tuple[int,int], value:int) -> bytearray:
        b = new_frame()
        b[5], b[6] = type_ids
        b[7:13] = self._mac or bytes(6)
        b[13] = value & 0xFF
        fill_random(b, 14, 30)
        return finalize(b)

#----- control

    # the command interface addressed by the sr900(<target>[,<value>]) Artisan IO Command
    #   heat,<0..9>     set the heater level        fan,<0..9>   set the fan level
    #   start           start a manual roast        stop         stop roaster and cooler
    #   cool            switch to cooling, cutting the heater and opening the fan up
    #   coolfan,<1..9>  fan level cool() commands, see DEFAULT_COOL_FAN
    #   roasttime,<min> / cooltime,<min>   the firmware timers carried by the next start
    #   autostop,<T>    firmware cutoff at a bean temperature in F or C, 0 is OFF
    #   altitude,<0|1>  0: below 3000ft, 1: above    voltage,<0|1|2>  0: <113V, 1: 113-118V, 2: >118V
    def send_msg(self, target:str, value:int = 0) -> None:
        if not self._handshake_done:
            # the handshake did not complete yet; queue the command
            self._pending.append((target, value))
            return
        if target == 'heat':
            self.set_heat(value)
        elif target == 'fan':
            self.set_fan(value)
        elif target == 'start':
            self.start_roast()
        elif target == 'stop':
            self.stop_roast()
        elif target == 'cool':
            self.cool()
        elif target == 'autostop':
            self.set_auto_stop(value)
        elif target == 'roasttime':
            self._roast_time = min(MAX_ROAST_TIME, max(1, value))
            if value > MAX_ROAST_TIME:
                _log.info('SR900 roast time %s above the %s minute maximum, clamped',
                            value, MAX_ROAST_TIME)
        elif target == 'cooltime':
            self._cool_time = max(1, value)
        elif target == 'coolfan':
            self._cool_fan_level = min(9, max(MIN_LEVEL, value))
        elif target == 'altitude':
            self.set_altitude(value)
        elif target == 'voltage':
            self.set_voltage(value)
        else:
            _log.info('SR900 command <%s> not recognized', target)

    # HEAT_SET does not fit value_cmd(): byte 14 is agenticRoast and has to be 0, where
    # value_cmd() would random-fill it as padding
    def heat_cmd(self, level:int) -> bytearray:
        b = new_frame()
        b[5], b[6] = HEAT_SET
        b[7:13] = self._mac or bytes(6)
        b[13] = level & 0xFF
        b[14] = 0 # agenticRoast
        fill_random(b, 15, 30)
        return finalize(b)

    def set_heat(self, level:int) -> None:
        self._last_heat_level = level & 0xFF
        self._heat_commanded = True
        self.send_command(self.heat_cmd(level))

    def set_fan(self, level:int) -> None:
        self._last_fan_level = level & 0xFF
        self._fan_commanded = True
        self.send_command(self.value_cmd(FAN_SET, level))

    def start_manual(self, roast_time:int, cool_time:int, heat_level:int,
                    fan_level:int, auto_stop_f:int = 0,
                    cooling_fan_level:int = 0) -> None:
        b = new_frame()
        # WhichManualRoast. 0 selects a plain manual start, 2 being used only when
        # abandoning a profile roast. Do NOT send 1: with it the roaster accepts a roast
        # time of 10 but silently ignores one of 15, answering with no ROASTER_STARTED,
        # and it reports back a heater level that was never commanded
        b[5] = 0
        b[6] = START_ROAST[1]
        b[7:13] = self._mac or bytes(6)
        b[13] = roast_time & 0xFF
        b[14] = cool_time & 0xFF
        b[15] = heat_level & 0xFF
        b[16] = fan_level & 0xFF
        b[17] = AUTO_STOP_TEMP.get(auto_stop_f, 0) # firmware auto stop target
        b[18] = cooling_fan_level & 0xFF
        fill_random(b, 19, 30)
        self.send_command(finalize(b))

    # start a manual roast at the levels last set via set_heat()/set_fan(). The heater and
    # fan hardware does not energize from HEAT_SET/FAN_SET alone, a START_ROAST is required.
    # The levels are clamped as the roaster refuses a START carrying a heater or fan level
    # of 0, ignoring it silently just as it ignores an out of range roast time.
    # A level not commanded on this connection is taken from the roaster's status frames instead,
    # which at idle report the levels last set; the driver's own defaults of 1 would otherwise
    # override them (observed: a queued fan 9 lost on reconnect started the roast at fan 1)
    def start_roast(self) -> None:
        heat_level = (self._last_heat_level if self._heat_commanded or self.heater < 0 else self.heater)
        fan_level = (self._last_fan_level if self._fan_commanded or self.fan < 0 else self.fan)
        self.start_manual(roast_time=self._roast_time, cool_time=self._cool_time,
                        heat_level=max(MIN_LEVEL, heat_level),
                        fan_level=max(MIN_LEVEL, fan_level),
                        auto_stop_f=self._auto_stop_f)

    # the target is given in F or in C, see AUTO_STOP_TEMP
    def set_auto_stop(self, auto_stop_f:int) -> None:
        # takes effect on the next start_roast(); the firmware reads the target from START
        if auto_stop_f in AUTO_STOP_TEMP:
            self._auto_stop_f = auto_stop_f
        else:
            _log.info('SR900 auto stop target <%s> not one of %s', auto_stop_f,
                        sorted(AUTO_STOP_TEMP))

    # NOTE: both push only on a change, the handshake having pushed the defaults already

    def set_altitude(self, altitude:int) -> None:
        if self._altitude != int(bool(altitude)):
            self._altitude = int(bool(altitude))
            self.push_settings()

    def set_voltage(self, voltage:int) -> None:
        if not 0 <= voltage < len(VOLTAGE_BITS):
            _log.info('SR900 voltage setting <%s> out of range', voltage)
        elif self._voltage != voltage:
            self._voltage = voltage
            self.push_settings()

    # NOTE: not named stop() as that is ClientBLE's connection teardown
    def stop_roast(self) -> None:
        # the roaster refuses this while the beans are hot, see STOP_RETRY_MARGIN_SECS, thus the
        # request is remembered and heartbeat() re-issues it until it is acted on
        self._stop_requested = True
        self._stop_attempts = 1
        self._stop_waited = 0
        self.send_command(self.mac_cmd(STOP_ROAST))

    # The manufacturer's app sends COOL_DN and nothing else, leaving the roaster to settle on
    # heater 0 / fan 3 by itself. The heater cut and the fan level are nevertheless commanded
    # explicitly here so that a DROP always lands on one known state, whatever the levels the
    # roast was running at and whatever the roaster would otherwise drift to
    def cool(self) -> None:
        self.send_command(self.mac_cmd(COOL_DN))
        # force the element off rather than waiting on the roaster to do it. Sent as bare
        # frames so that _last_heat_level/_last_fan_level keep the levels the roast ended on,
        # which is what a subsequent start_roast() should resume from
        self.send_command(self.heat_cmd(0))
        self.send_command(self.value_cmd(FAN_SET, self._cool_fan_level))

    def push_settings(self) -> None:
        b = new_frame()
        b[5] = encode_settings_byte(self._altitude, self._voltage)
        b[6] = SETTINGS[1]
        b[7:13] = self._mac or bytes(6)
        fill_random(b, 13, 30)
        self.send_command(finalize(b))

    def start_sampling(self) -> None:
        # start the BLE loop
        self.start()

    # NOTE: not named disconnect() as that would shadow QObject.disconnect()
    def stop_sampling(self, recording:bool, _after_drop:bool) -> None:
        try:
            if recording:
                # only on OFF while recording the roast is terminated, as a heater or fan
                # left running would otherwise keep running unsupervised
                self.stop_roast()
                libtime.sleep(.3)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        self.stop()

#----- incoming

    def notify_callback(self, _characteristic:'BleakGATTCharacteristic', data:bytearray) -> None:
        d = bytes(data)
        if self._logging:
            _log.info('received: %s', d.hex())
        if len(d) != FRAME_LEN or d[0] != STX:
            _log.debug('notify_callback() unexpected frame length or start byte')
            return
        if (d[32] | (d[33] << 8)) != (ETX_LO | (ETX_HI << 8)):
            _log.debug('notify_callback() ETX check failed')
            return
        if (sum(d[1:31]) & 0xFF) != d[CHECKSUM_POS]:
            _log.debug('notify_callback() checksum check failed')
            return
        try:
            self.processData(d)
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)

    def processData(self, d:bytes) -> None:
        type_id = d[6]

        if type_id == RES_MAC_ADDRESS:
            self._mac = d[7:13]
            if self._mac_req_rnd is not None:
                self._command_token = compute_command_token(self._mac, self._mac_req_rnd)
            # temperatures ride along in the MAC response
            self.BT = be16(d, 13)
            self.ET = be16(d, 15)
            # NOTE: nothing is sent from here, heartbeat() picks the handshake up

        elif type_id == RES_ROASTER_STATUS:
            started = d[21]
            # the roaster keeps reporting ROASTING while the cooler runs, thus the cooling
            # state is tracked from the COOLER_STARTED response instead of the status byte
            self.state = (STATE_COOLING if self._cooling and started == STATE_ROASTING else started)
            # bytes 13/14 carry the roaster's actual output in every state, not only while roasting:
            # at idle they report the levels last commanded, and during the post-roast cooldown the
            # roaster's own settings (observed: fan 2, heater 0). Taking them unconditionally keeps
            # the readback curves and LCDs live throughout, and gives check_token() its evidence
            self.fan = d[13]
            self.heater = d[14]
            self.BT = be16(d, 17) # EXTERNAL probe, in the bean mass
            self.ET = be16(d, 19) # INTERNAL sensor, next to the heating element
            # NOTE: bytes 15/16 hold whichever of the two the roaster settings select and are
            # ignored here, so that BT stays the bean probe whatever the roaster is set to
            self.roast_time = d[22] * 60 + d[23]

        elif type_id == RES_SETTINGS_ACK:
            self._settings_acked = True
        elif type_id == RES_ROASTER_STARTED:
            self._cooling = False
            self._stop_requested = False # a roast was started, the stop is stale
            self.state = STATE_ROASTING
        elif type_id == RES_COOLER_STARTED:
            self._cooling = True
            self.state = STATE_COOLING
        elif type_id == RES_ROASTER_FINISHED:
            self._cooling = False
            self._stop_requested = False
            self.state = STATE_IDLE
