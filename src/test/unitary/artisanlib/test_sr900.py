"""Unit tests for artisanlib.sr900 module.

This module tests the Fresh Roast SR900 roaster BLE driver, including:
- the fixed 34 byte frame layout, its ETX marker and its checksum
- the per-connection command token derived from the MAC address response
- the roaster side settings byte (thermistor / altitude / mains voltage)
- the request builders for HEAT_SET, FAN_SET, START_ROAST, COOL_DN, STOP_ROAST,
  MAC_ADDRESS and SETTINGS, checked field by field against the wire format
- notification validation: frame length, start byte, ETX and checksum
- response decoding for status, started, cooler started, finished and MAC address
- the sr900(<target>[,<value>]) command dispatch, including the queue that holds
  commands back until the handshake completed
- the STOP retry interval, which has to outlast the roaster's cooling cycle
- the isRoasting/isCooling flags that drive the autoCHARGE/autoDROP in comm.py

The protocol values asserted here are taken from the manufacturer's own Windows
application, so a change that breaks one of these breaks the roaster.

NOTE: ClientBLE derives from QObject and cannot be constructed without a Qt object
and a BLE stack. The driver's protocol methods never touch either, so they are bound
onto a plain stand-in (see _make_driver) rather than mocking bleak and PyQt6 away.
=============================================================================
"""

import configparser
import pathlib
from types import MethodType, SimpleNamespace
from typing import Any

import pytest

from artisanlib import sr900
from artisanlib.sr900 import (SR900_BLE, AUTO_STOP_TEMP, CHECKSUM_POS, ETX_HI, ETX_LO, FRAME_LEN,
    RESERVED, STX, compute_command_token, encode_settings_byte, finalize, new_frame)

# a MAC with no byte that compute_command_token() has to bump, so that the plain
# multiplication is what gets tested
PLAIN_MAC: bytes = bytes((0xA1, 0xB2, 0xC3, 0xD5, 0xE7, 0xF9))

# the protocol methods bound onto the stand-in; see the note in the module docstring
_METHODS = ('processData', 'notify_callback', 'send_msg', 'send_command', 'raw_send', 'mac_cmd',
            'value_cmd', 'heat_cmd', 'set_heat', 'set_fan', 'start_manual', 'start_roast',
            'stop_roast', 'stop_retry_ticks', 'cool', 'push_settings', 'request_mac',
            'set_auto_stop', 'set_altitude', 'set_voltage', 'clearData')


def _make_driver(**overrides: Any) -> Any:
    """A stand-in carrying the real SR900_BLE protocol methods.

    The handshake is set up as completed with a known command token, which is what every
    method but request_mac() expects. Frames that would go out over BLE are collected in
    `sent` instead.
    """
    sent: list[bytes] = []
    d = SimpleNamespace(
        _logging=False,
        _mac=PLAIN_MAC,
        _mac_req_rnd=None,
        _command_token=[0x11, 0x22, 0x33, 0x44],
        _altitude=0,
        _voltage=sr900.VOLTAGE_DEFAULT,
        _auto_stop_f=sr900.DEFAULT_AUTO_STOP,
        _roast_time=sr900.DEFAULT_ROAST_TIME,
        _cool_time=sr900.DEFAULT_COOL_TIME,
        _cool_fan_level=sr900.DEFAULT_COOL_FAN,
        _cooling=False,
        _stop_requested=False,
        _stop_attempts=0,
        _stop_waited=0,
        _mac_attempts=0,
        _settings_acked=False,
        _handshake_done=True,
        _pending=[],
        _last_heat_level=1,
        _last_fan_level=1,
        _fan_commanded=False,
        _heat_commanded=False,
        TX=0,
        ET=-1,
        BT=-1,
        heater=-1,
        fan=-1,
        state=-1,
        roast_time=-1,
        sent=sent,
    )
    for name in _METHODS:
        setattr(d, name, MethodType(getattr(SR900_BLE, name), d))
    # collect what would be written rather than reaching for a BLE client
    d.send = MethodType(lambda _self, message, **_kwargs: sent.append(bytes(message)), d)
    for key, value in overrides.items():
        setattr(d, key, value)
    return d


def _response(type_id: int, fill: Any = None) -> bytes:
    """Build a well formed response frame of the given type."""
    b = new_frame()
    b[6] = type_id
    if fill is not None:
        fill(b)
    return bytes(finalize(b))


class TestFrameLayout:
    """The fixed 34 byte envelope every message shares."""

    def test_new_frame_envelope(self) -> None:
        b = new_frame()
        assert len(b) == FRAME_LEN == 34
        assert b[0] == STX == 0x20
        assert bytes(b[1:5]) == RESERVED == b'SEQO'
        # ETX is 816 (0x0330) stored little endian in the last two bytes
        assert (b[32], b[33]) == (ETX_LO, ETX_HI) == (0x30, 0x03)
        assert b[32] | (b[33] << 8) == 816
        assert all(v == 0 for v in b[5:32])

    def test_finalize_checksum_covers_bytes_1_to_30(self) -> None:
        b = new_frame()
        b[13] = 0xFF
        b[30] = 0x02
        finalize(b)
        assert b[CHECKSUM_POS] == sum(b[1:31]) & 0xFF
        assert CHECKSUM_POS == 31

    def test_finalize_ignores_bytes_outside_the_checksum_range(self) -> None:
        b = new_frame()
        finalize(b)
        before = b[CHECKSUM_POS]
        b[31] = before  # the checksum byte itself is not covered
        b[32] = ETX_LO
        b[33] = ETX_HI
        finalize(b)
        assert b[CHECKSUM_POS] == before

    def test_finalize_wraps_to_a_single_byte(self) -> None:
        b = new_frame()
        for i in range(5, 31):
            b[i] = 0xFF
        finalize(b)
        assert 0 <= b[CHECKSUM_POS] <= 0xFF

    def test_fill_random_stays_inside_its_range(self) -> None:
        b = new_frame()
        sr900.fill_random(b, 13, 30)
        assert all(b[i] == 0 for i in range(5, 13))
        assert b[31] == 0  # checksum not written yet
        assert (b[32], b[33]) == (ETX_LO, ETX_HI)

    def test_be16_is_big_endian(self) -> None:
        assert sr900.be16(bytes((0, 1, 0x02, 0x9B)), 2) == 0x029B #== 667


class TestCommandToken:
    """token[i] = (MAC[5-i] * RND[i]) & 0xFF, a MAC byte of 0 or a power of two bumped by one."""

    def test_plain_multiplication(self) -> None:
        rnd = [2, 3, 4, 5]
        token = compute_command_token(PLAIN_MAC, rnd)
        assert token == [
            (0xF9 * 2) & 0xFF,  # MAC[5] * RND1
            (0xE7 * 3) & 0xFF,  # MAC[4] * RND2
            (0xD5 * 4) & 0xFF,  # MAC[3] * RND3
            (0xC3 * 5) & 0xFF,  # MAC[2] * RND4
        ]

    @pytest.mark.parametrize('mac_byte', [0, 2, 4, 8, 16, 32, 64, 128])
    def test_zero_and_powers_of_two_are_bumped(self, mac_byte: int) -> None:
        mac = bytes((1, 1, 1, 1, 1, mac_byte))
        assert compute_command_token(mac, [3, 0, 0, 0])[0] == ((mac_byte + 1) * 3) & 0xFF

    def test_one_is_not_bumped(self) -> None:
        # 1 is deliberately absent from the bump set in the manufacturer's app
        assert compute_command_token(bytes((1, 1, 1, 1, 1, 1)), [7, 0, 0, 0])[0] == 7

    def test_token_is_four_bytes_in_range(self) -> None:
        token = compute_command_token(PLAIN_MAC, [200, 201, 202, 203])
        assert len(token) == 4
        assert all(0 <= v <= 0xFF for v in token)


class TestSettingsByte:
    """external thermistor +64, above 3000ft +8, >118V +4, 113-118V +2, <113V +1."""

    def test_defaults_select_the_external_thermistor(self) -> None:
        # the thermistor bit is fixed: only the external probe sits in the bean mass
        assert encode_settings_byte(altitude=0, voltage=1) == 64 + 2

    @pytest.mark.parametrize(('voltage', 'bits'), [(0, 1), (1, 2), (2, 4)])
    def test_voltage_bits(self, voltage: int, bits: int) -> None:
        assert encode_settings_byte(altitude=0, voltage=voltage) == 64 + bits

    def test_altitude_bit(self) -> None:
        assert encode_settings_byte(altitude=1, voltage=1) == 64 + 8 + 2

    def test_out_of_range_voltage_falls_back_to_the_default(self) -> None:
        default = encode_settings_byte(voltage=sr900.VOLTAGE_DEFAULT)
        assert encode_settings_byte(voltage=99) == default
        assert encode_settings_byte(voltage=-1) == default


class TestAutoStopTargets:
    """The Which_Roast codes the roaster's own auto stop dropdown offers."""

    def test_off_is_zero(self) -> None:
        assert AUTO_STOP_TEMP[0] == 0
        assert sr900.DEFAULT_AUTO_STOP == 0  # nothing cuts a roast short unasked

    @pytest.mark.parametrize(('fahrenheit', 'celsius', 'code'), [
        (410, 210, 6), (420, 216, 7), (430, 221, 8),
        (440, 227, 9), (450, 235, 16), (470, 243, 17)])
    def test_both_units_map_to_the_same_code(self, fahrenheit: int, celsius: int, code: int) -> None:
        assert AUTO_STOP_TEMP[fahrenheit] == code
        assert AUTO_STOP_TEMP[celsius] == code

    def test_the_two_unit_ranges_do_not_overlap(self) -> None:
        # sr900(autostop,<T>) can only take either unit while this holds
        fahrenheit = {410, 420, 430, 440, 450, 470}
        celsius = {210, 216, 221, 227, 235, 243}
        assert not (fahrenheit & celsius)


class TestRequestTypeIds:
    """Request and response type ids, as defined by the manufacturer's app."""

    def test_request_ids(self) -> None:
        assert sr900.HEAT_SET == (0, 1)
        assert sr900.FAN_SET == (0, 2)
        assert sr900.START_ROAST == (0, 21)
        assert sr900.COOL_DN == (0, 24)
        assert sr900.STOP_ROAST == (0, 25)
        assert sr900.MAC_ADDRESS_REQ == (0, 38)
        assert sr900.SETTINGS == (0, 43)

    def test_response_ids(self) -> None:
        assert sr900.RES_ROASTER_STATUS == 33
        assert sr900.RES_ROASTER_STARTED == 34
        assert sr900.RES_COOLER_STARTED == 35
        assert sr900.RES_ROASTER_FINISHED == 36
        assert sr900.RES_MAC_ADDRESS == 39


class TestRequestBuilders:
    """Every outgoing frame, field by field."""

    def test_mac_request_carries_the_random_bytes_and_keeps_the_reserved_bytes(self) -> None:
        d = _make_driver(_command_token=None)
        d.request_mac()
        frame = d.sent[0]
        assert len(frame) == FRAME_LEN
        assert (frame[5], frame[6]) == sr900.MAC_ADDRESS_REQ
        # the token is not applied to the MAC request, it is not known yet
        assert frame[1:5] == RESERVED
        assert d._mac_req_rnd == [frame[7], frame[8], frame[9], frame[10]]
        assert frame[CHECKSUM_POS] == sum(frame[1:31]) & 0xFF

    def test_every_other_request_carries_the_token_in_bytes_1_to_4(self) -> None:
        d = _make_driver()
        d.set_fan(5)
        frame = d.sent[0]
        assert list(frame[1:5]) == d._command_token
        assert frame[CHECKSUM_POS] == sum(frame[1:31]) & 0xFF

    def test_fan_set_layout(self) -> None:
        d = _make_driver()
        d.set_fan(7)
        frame = d.sent[0]
        assert (frame[5], frame[6]) == sr900.FAN_SET
        assert frame[7:13] == PLAIN_MAC
        assert frame[13] == 7

    def test_heat_set_zeroes_the_agentic_roast_byte(self) -> None:
        d = _make_driver()
        d.set_heat(4)
        frame = d.sent[0]
        assert (frame[5], frame[6]) == sr900.HEAT_SET
        assert frame[7:13] == PLAIN_MAC
        assert frame[13] == 4
        assert frame[14] == 0  # agenticRoast, must not be random padding

    def test_start_roast_layout(self) -> None:
        d = _make_driver(_last_heat_level=6, _last_fan_level=8,
                         _roast_time=12, _cool_time=3, _auto_stop_f=430)
        d.start_roast()
        frame = d.sent[0]
        assert frame[5] == 0  # WhichManualRoast: a plain manual start
        assert frame[6] == sr900.START_ROAST[1]
        assert frame[7:13] == PLAIN_MAC
        assert frame[13] == 12  # roast time, minutes
        assert frame[14] == 3   # cool time, minutes
        assert frame[15] == 6   # heater level
        assert frame[16] == 8   # fan level
        assert frame[17] == AUTO_STOP_TEMP[430]

    def test_start_roast_clamps_levels_the_firmware_refuses(self) -> None:
        # a START carrying a heater or fan level of 0 is ignored without any response
        d = _make_driver(_last_heat_level=0, _last_fan_level=0)
        d.start_roast()
        frame = d.sent[0]
        assert frame[15] == sr900.MIN_LEVEL
        assert frame[16] == sr900.MIN_LEVEL

    def test_start_roast_takes_uncommanded_levels_from_the_roaster(self) -> None:
        # nothing commanded on this connection: the reported levels win over the driver defaults
        d = _make_driver(fan=9, heater=3)
        d.start_roast()
        frame = d.sent[0]
        assert frame[15] == 3
        assert frame[16] == 9

    def test_start_roast_prefers_commanded_levels_over_the_readback(self) -> None:
        d = _make_driver(fan=9, heater=3, _last_fan_level=5, _fan_commanded=True)
        d.start_roast()
        frame = d.sent[0]
        assert frame[15] == 3  # heater not commanded, taken from the roaster
        assert frame[16] == 5  # fan commanded, taken from the command

    def test_start_roast_clamps_a_readback_of_0(self) -> None:
        d = _make_driver(fan=2, heater=0)
        d.start_roast()
        frame = d.sent[0]
        assert frame[15] == sr900.MIN_LEVEL
        assert frame[16] == 2

    def test_stop_and_cool_carry_only_the_mac(self) -> None:
        d = _make_driver(BT=100)
        d.stop_roast()
        frame = d.sent[0]
        assert (frame[5], frame[6]) == sr900.STOP_ROAST
        assert frame[7:13] == PLAIN_MAC

    def test_cool_cuts_the_heater_and_opens_the_fan(self) -> None:
        d = _make_driver(_cool_fan_level=3)
        d.cool()
        cool_dn, heat, fan = d.sent
        assert (cool_dn[5], cool_dn[6]) == sr900.COOL_DN
        assert (heat[5], heat[6]) == sr900.HEAT_SET
        assert heat[13] == 0
        assert (fan[5], fan[6]) == sr900.FAN_SET
        assert fan[13] == 3

    def test_cool_keeps_the_levels_the_roast_ended_on(self) -> None:
        # a subsequent start_roast() should resume from those, not from the cooling levels
        d = _make_driver(_last_heat_level=9, _last_fan_level=4)
        d.cool()
        assert d._last_heat_level == 9
        assert d._last_fan_level == 4

    def test_settings_frame_puts_the_settings_byte_in_byte_5(self) -> None:
        d = _make_driver(_altitude=1, _voltage=2)
        d.push_settings()
        frame = d.sent[0]
        assert frame[5] == encode_settings_byte(1, 2)
        assert frame[6] == sr900.SETTINGS[1]
        assert frame[7:13] == PLAIN_MAC


class TestNotifyCallbackValidation:
    """A frame that fails any check must be dropped without touching the readings."""

    def test_accepts_a_well_formed_frame(self) -> None:
        d = _make_driver()
        d.notify_callback(None, bytearray(_response(sr900.RES_ROASTER_STARTED)))
        assert d.state == sr900.STATE_ROASTING

    def test_rejects_a_wrong_length(self) -> None:
        d = _make_driver()
        d.notify_callback(None, bytearray(_response(sr900.RES_ROASTER_STARTED)[:-1]))
        assert d.state == -1

    def test_rejects_a_wrong_start_byte(self) -> None:
        d = _make_driver()
        frame = bytearray(_response(sr900.RES_ROASTER_STARTED))
        frame[0] = 0x21
        d.notify_callback(None, frame)
        assert d.state == -1

    def test_rejects_a_wrong_etx(self) -> None:
        d = _make_driver()
        frame = bytearray(_response(sr900.RES_ROASTER_STARTED))
        frame[33] = 0x04
        d.notify_callback(None, frame)
        assert d.state == -1

    def test_rejects_a_bad_checksum(self) -> None:
        d = _make_driver()
        frame = bytearray(_response(sr900.RES_ROASTER_STARTED))
        frame[CHECKSUM_POS] ^= 0xFF
        d.notify_callback(None, frame)
        assert d.state == -1


class TestProcessData:
    """Response decoding."""

    def test_status_reads_both_sensors_and_the_levels(self) -> None:
        d = _make_driver()

        def fill(b: bytearray) -> None:
            b[13] = 5           # fan
            b[14] = 7           # heater
            b[15], b[16] = 1, 0xF4   # the selector field, deliberately ignored
            b[17], b[18] = 0, 0xC8   # EXTERNAL probe -> BT, 200F
            b[19], b[20] = 0, 0xD2   # INTERNAL sensor -> ET, 210F
            b[21] = sr900.STATE_ROASTING
            b[22], b[23] = 4, 30     # 4:30 elapsed

        d.processData(_response(sr900.RES_ROASTER_STATUS, fill))
        assert (d.fan, d.heater) == (5, 7)
        assert d.BT == 200
        assert d.ET == 210
        assert d.state == sr900.STATE_ROASTING
        assert d.roast_time == 4 * 60 + 30

    def test_status_reports_the_levels_at_idle_too(self) -> None:
        # they carry the roaster's actual output in every state, which keeps the readback
        # curves live and gives check_token() its evidence
        d = _make_driver()

        def fill(b: bytearray) -> None:
            b[13] = 2
            b[14] = 0
            b[21] = sr900.STATE_IDLE

        d.processData(_response(sr900.RES_ROASTER_STATUS, fill))
        assert (d.fan, d.heater) == (2, 0)
        assert d.state == sr900.STATE_IDLE

    def test_status_reports_cooling_while_the_roaster_still_says_roasting(self) -> None:
        d = _make_driver(_cooling=True)

        def fill(b: bytearray) -> None:
            b[21] = sr900.STATE_ROASTING

        d.processData(_response(sr900.RES_ROASTER_STATUS, fill))
        assert d.state == sr900.STATE_COOLING

    def test_mac_response_derives_the_command_token(self) -> None:
        d = _make_driver(_command_token=None, _mac=None, _mac_req_rnd=[2, 3, 4, 5])

        def fill(b: bytearray) -> None:
            b[7:13] = PLAIN_MAC

        d.processData(_response(sr900.RES_MAC_ADDRESS, fill))
        assert d._mac == PLAIN_MAC
        assert d._command_token == compute_command_token(PLAIN_MAC, [2, 3, 4, 5])

    def test_mac_response_sends_nothing(self) -> None:
        # writing from the notification loop deadlocks it, see the threading note in the module
        d = _make_driver(_command_token=None, _mac_req_rnd=[1, 1, 1, 1])
        d.processData(_response(sr900.RES_MAC_ADDRESS, lambda b: b.__setitem__(slice(7, 13), PLAIN_MAC)))
        assert d.sent == []

    def test_cooler_started_marks_cooling(self) -> None:
        d = _make_driver()
        d.processData(_response(sr900.RES_COOLER_STARTED))
        assert d._cooling is True
        assert d.state == sr900.STATE_COOLING

    def test_roaster_started_clears_a_stale_stop(self) -> None:
        d = _make_driver(_cooling=True, _stop_requested=True)
        d.processData(_response(sr900.RES_ROASTER_STARTED))
        assert d._cooling is False
        assert d._stop_requested is False
        assert d.state == sr900.STATE_ROASTING

    def test_roaster_finished_returns_to_idle(self) -> None:
        d = _make_driver(_cooling=True, _stop_requested=True)
        d.processData(_response(sr900.RES_ROASTER_FINISHED))
        assert d._cooling is False
        assert d._stop_requested is False
        assert d.state == sr900.STATE_IDLE

    def test_an_unknown_type_is_ignored(self) -> None:
        d = _make_driver()
        d.processData(_response(99))
        assert d.state == -1
        assert d.BT == -1


class TestRoastStateFlags:
    """isRoasting/isCooling drive the autoCHARGE and autoDROP in comm.py."""

    def test_flags_follow_the_state(self) -> None:
        d = _make_driver()
        is_roasting = SR900_BLE.isRoasting.fget  # type: ignore[attr-defined]
        is_cooling = SR900_BLE.isCooling.fget    # type: ignore[attr-defined]
        assert not is_roasting(d) and not is_cooling(d)  # state -1, nothing known yet
        d.state = sr900.STATE_ROASTING
        assert is_roasting(d) and not is_cooling(d)
        d.state = sr900.STATE_COOLING
        assert not is_roasting(d) and is_cooling(d)
        d.state = sr900.STATE_IDLE
        assert not is_roasting(d) and not is_cooling(d)

    def test_a_roast_already_under_way_reports_roasting(self) -> None:
        # the roaster sends no STARTED for one of those, only status frames
        d = _make_driver()
        d.processData(_response(sr900.RES_ROASTER_STATUS,
                                lambda b: b.__setitem__(21, sr900.STATE_ROASTING)))
        assert SR900_BLE.isRoasting.fget(d) is True  # type: ignore[attr-defined]


class TestStopRetry:
    """A STOP refused while the roaster is hot is answered with COOLER_STARTED and restarts the
    cooling cycle, so re-issuing one faster than the cool time keeps the roaster cooling and it
    never reaches the idle state that would let it accept the stop. The retry therefore has to
    wait out the cool time, which is why it is derived from it rather than fixed.
    """

    def test_a_stop_goes_out_immediately_and_is_remembered(self) -> None:
        d = _make_driver()
        d.stop_roast()
        assert len(d.sent) == 1
        assert (d.sent[0][5], d.sent[0][6]) == sr900.STOP_ROAST
        assert d._stop_requested is True
        assert d._stop_attempts == 1
        assert d._stop_waited == 0

    @pytest.mark.parametrize('cool_time', [1, 3, 4, 9])
    def test_the_retry_interval_always_exceeds_the_cool_time(self, cool_time: int) -> None:
        # this is the property the whole mechanism exists for: retry sooner and the refusal
        # restarts the cooling cycle, and the roaster can never reach idle
        d = _make_driver(_cool_time=cool_time)
        assert d.stop_retry_ticks() * sr900.HEARTBEAT_INTERVAL > cool_time * 60

    def test_the_retry_interval_is_the_cool_time_plus_the_margin(self) -> None:
        d = _make_driver(_cool_time=4)
        expected = (4 * 60 + sr900.STOP_RETRY_MARGIN_SECS) / sr900.HEARTBEAT_INTERVAL
        assert d.stop_retry_ticks() == int(expected)

    def test_a_longer_cool_time_waits_longer(self) -> None:
        assert (_make_driver(_cool_time=9).stop_retry_ticks()
                > _make_driver(_cool_time=1).stop_retry_ticks())

    def test_a_started_roast_clears_a_pending_stop(self) -> None:
        # otherwise a stale stop from the previous roast would fire into the new one
        d = _make_driver(_stop_requested=True, _stop_attempts=3)
        d.processData(_response(sr900.RES_ROASTER_STARTED))
        assert d._stop_requested is False


class TestSendMsgDispatch:
    """The sr900(<target>[,<value>]) command interface."""

    def test_levels_are_remembered_for_a_later_start(self) -> None:
        d = _make_driver()
        d.send_msg('fan', 6)
        d.send_msg('heat', 3)
        assert d._last_fan_level == 6
        assert d._last_heat_level == 3
        assert d._fan_commanded is True
        assert d._heat_commanded is True

    def test_roast_time_is_clamped_to_the_maximum_the_firmware_accepts(self) -> None:
        d = _make_driver()
        d.send_msg('roasttime', 99)
        assert d._roast_time == sr900.MAX_ROAST_TIME
        d.send_msg('roasttime', 0)
        assert d._roast_time == 1

    def test_cool_fan_is_clamped_to_a_level_the_roaster_accepts(self) -> None:
        d = _make_driver()
        d.send_msg('coolfan', 0)
        assert d._cool_fan_level == sr900.MIN_LEVEL
        d.send_msg('coolfan', 99)
        assert d._cool_fan_level == 9

    def test_autostop_takes_either_unit_and_rejects_anything_else(self) -> None:
        d = _make_driver()
        d.send_msg('autostop', 450)
        assert d._auto_stop_f == 450
        d.send_msg('autostop', 221)  # a Celsius label
        assert d._auto_stop_f == 221
        d.send_msg('autostop', 999)  # not on the roaster's dropdown
        assert d._auto_stop_f == 221

    def test_settings_are_pushed_only_on_a_change(self) -> None:
        d = _make_driver(_altitude=0, _voltage=1)
        d.send_msg('voltage', 1)   # unchanged
        assert d.sent == []
        d.send_msg('voltage', 2)
        assert len(d.sent) == 1
        d.send_msg('altitude', 1)
        assert len(d.sent) == 2

    def test_an_out_of_range_voltage_is_rejected(self) -> None:
        d = _make_driver(_voltage=1)
        d.send_msg('voltage', 9)
        assert d._voltage == 1
        assert d.sent == []

    def test_an_unknown_target_is_ignored(self) -> None:
        d = _make_driver()
        d.send_msg('nonsense', 1)
        assert d.sent == []

    def test_commands_are_queued_until_the_handshake_completed(self) -> None:
        d = _make_driver(_handshake_done=False)
        d.send_msg('fan', 9)
        d.send_msg('heat', 1)
        assert d.sent == []
        assert d._pending == [('fan', 9), ('heat', 1)]

    def test_queued_commands_apply_in_order_once_flushed(self) -> None:
        d = _make_driver(_handshake_done=False)
        d.send_msg('fan', 9)
        d.send_msg('heat', 1)
        d._handshake_done = True
        for target, value in d._pending:
            d.send_msg(target, value)
        assert [(f[5], f[6]) for f in d.sent] == [sr900.FAN_SET, sr900.HEAT_SET]
        assert (d._last_fan_level, d._last_heat_level) == (9, 1)

    def test_a_command_without_a_token_is_dropped(self) -> None:
        d = _make_driver(_command_token=None)
        d.send_msg('fan', 5)
        assert d.sent == []


class TestMachineSetup:
    """The shipped machine setup, includes/Machines/Fresh Roast/SR900.aset.

    Its alarm block is a set of parallel comma separated lists that Artisan reads against the
    length of alarmflag, so one of them drifting out of step silently truncates the alarm set.
    """

    @staticmethod
    def _aset() -> 'configparser.RawConfigParser':
        path = (pathlib.Path(__file__).resolve().parents[3]
                / 'includes' / 'Machines' / 'Fresh Roast' / 'SR900.aset')
        assert path.is_file(), f'machine setup missing at {path}'
        # RawConfigParser: the file is a Qt ini and must not be interpolated
        parser = configparser.RawConfigParser()
        parser.optionxform = str  # type: ignore[method-assign,assignment] # keys are case sensitive
        parser.read(path, encoding='utf-8')
        return parser

    @staticmethod
    def _list(parser: 'configparser.RawConfigParser', section: str, key: str) -> list[str]:
        return [v.strip() for v in parser[section][key].split(',')]

    def test_device_ids(self) -> None:
        parser = self._aset()
        assert parser['Device']['id'] == '209'
        assert self._list(parser, 'ExtraDev', 'extradevices') == ['210', '211']

    def test_alarm_lists_are_all_the_same_length(self) -> None:
        parser = self._aset()
        keys = ('alarmaction', 'alarmbeep', 'alarmcond', 'alarmflag', 'alarmguard',
                'alarmnegguard', 'alarmoffset', 'alarmsource', 'alarmstrings',
                'alarmtemperature', 'alarmtime')
        lengths = {key: len(self._list(parser, 'Alarms', key)) for key in keys}
        assert len(set(lengths.values())) == 1, lengths

    def test_alarms_ship_disabled(self) -> None:
        # the user opts in, as the IKAWA setups do; nothing drives the roaster unasked
        parser = self._aset()
        assert set(self._list(parser, 'Alarms', 'alarmflag')) == {'0'}

    def test_alarm_chain_is_start_then_cool_end_then_off(self) -> None:
        parser = self._aset()
        # 7 START, 14 COOL END, 15 OFF (the alarm action combo index minus one)
        assert self._list(parser, 'Alarms', 'alarmaction') == ['7', '14', '15']
        # every one of them watches the roaster state, which is chan1 of the second
        # extra device: alarmsource 4 -> extradevices[(4-2)//2] == 211, even -> extratemp1
        assert set(self._list(parser, 'Alarms', 'alarmsource')) == {'4'}
        # all three compare for equality against a state code
        assert set(self._list(parser, 'Alarms', 'alarmcond')) == {'2'}
        # ROASTING, IDLE, IDLE
        assert self._list(parser, 'Alarms', 'alarmtemperature') == ['1', '0', '0']
        # from ON, from DROP, from COOL END. OFF hangs off COOL END rather than off DROP so
        # that it cannot run before the queued markCoolEnd() did, which would drop COOL END
        assert self._list(parser, 'Alarms', 'alarmtime') == ['9', '6', '7']

    def test_alarm_states_match_the_driver(self) -> None:
        parser = self._aset()
        roasting, cool_end, off = self._list(parser, 'Alarms', 'alarmtemperature')
        assert int(roasting) == sr900.STATE_ROASTING
        assert int(cool_end) == sr900.STATE_IDLE
        assert int(off) == sr900.STATE_IDLE

    def test_alarm_strings_are_comments_only(self) -> None:
        # processAlarm() splits the string on '#' and uses the part before it as the action
        # argument, which the event actions used here do not take
        parser = self._aset()
        for text in self._list(parser, 'Alarms', 'alarmstrings'):
            assert text.startswith('#')

    def test_sliders_drive_the_roaster_over_the_io_command(self) -> None:
        parser = self._aset()
        # slider action 11 is 'IO Command' in the unsorted sliderActionTypes list
        assert self._list(parser, 'Sliders', 'slideractions') == ['11', '0', '0', '11']
        commands = parser['Sliders']['slidercommands']
        assert 'sr900(fan,{})' in commands
        assert 'sr900(heat,{})' in commands
        # the fan may not be taken to 0: this is a fluid bed and the beans ride on the air.
        # The heater may, cutting the element mid roast is what cool() itself does; only a
        # START carrying a level of 0 is refused, and start_roast() clamps for that
        assert self._list(parser, 'Sliders', 'slidermin')[0] == str(sr900.MIN_LEVEL) == '1'
        assert self._list(parser, 'Sliders', 'slidermin')[3] == '0'
        assert self._list(parser, 'Sliders', 'slidermax')[0] == '9'
        assert self._list(parser, 'Sliders', 'slidermax')[3] == '9'

    def test_buttons_end_the_roast_in_two_steps(self) -> None:
        parser = self._aset()
        # button action 5 is 'IO Command' in the buttonActionTypes list
        actions = self._list(parser, 'DefaultButtons', 'buttonactions')
        assert actions[6] == '5' and actions[7] == '5'
        strings = self._list(parser, 'DefaultButtons', 'buttonactionstrings')
        assert strings[6] == 'sr900(cool)'   # DROP runs the cooling cycle
        assert strings[7] == 'sr900(stop)'   # COOL END returns the roaster to idle

    def test_generic_autodrop_is_off(self) -> None:
        # DROP comes from the roaster entering its cooling state, see comm.py. The generic BT
        # break detector misreads the BT stall and wobble at first crack as a drop (observed:
        # 399 -> 401 -> 399F right after FCs auto-DROPped a roast 8s into first crack)
        parser = self._aset()
        assert parser['events']['autoDrop'] == 'false'

    def test_fan_and_heater_quantifiers_follow_the_readback(self) -> None:
        # sr900(cool) sets heater 0 / fan 3 on the roaster without touching the sliders, so only
        # the quantifiers get those levels into the events (observed: the Fan/Heater events stayed
        # at 4/6 through cooling). They also pick up changes made at the roaster itself
        parser = self._aset()
        assert self._list(parser, 'Quantifiers', 'quantifieractive') == ['1', '0', '0', '1']
        # quantifiersource n -> extradevices[(n-2)//2] == 210, odd -> extratemp2 (Fan),
        # even -> extratemp1 (Heater)
        assert self._list(parser, 'Quantifiers', 'quantifiersource') == ['3', '0', '0', '2']
        # the levels are quantified over the slider ranges
        for key in ('min', 'max'):
            assert (self._list(parser, 'Quantifiers', f'quantifier{key}')
                    == self._list(parser, 'Sliders', f'slider{key}'))
        # never blocked after a slider move, or a DROP shortly after one would be missed
        assert self._list(parser, 'Quantifiers', 'eventquantifierSV') == ['1', '0', '0', '1']
        # the readback is recorded only, never sent back to the roaster
        assert set(self._list(parser, 'Quantifiers', 'eventquantifieraction')) == {'0'}


class TestClearData:
    """Readings are dropped on disconnect rather than going stale."""

    def test_clear_data_resets_every_reading(self) -> None:
        d = _make_driver(_cooling=True, ET=200, BT=190, heater=5, fan=6,
                         state=sr900.STATE_ROASTING, roast_time=120)
        d.clearData()
        assert d._cooling is False
        assert (d.ET, d.BT) == (-1, -1)
        assert (d.heater, d.fan) == (-1, -1)
        assert d.state == -1
        assert d.roast_time == -1
