"""ACS-13A wire format, including a frame captured from a CMA-connected controller."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from PyQt6.QtCore import QCoreApplication

_app = QCoreApplication.instance() or QCoreApplication([])
_app.artisanviewerMode = False

from artisanlib.canvas import tgraphcanvas
from artisanlib.shinko_acs13a import parse_pv_response, parse_read_response, pv_request, read_request, timer_state


class ACS13AProtocolTests(unittest.TestCase):
    def test_pv_request_for_instrument_zero(self) -> None:
        self.assertEqual(pv_request(0), bytes.fromhex('02 20 20 20 30 30 38 30 44 38 03'))

    def test_captured_pv_response(self) -> None:
        response = bytes.fromhex('06 20 20 20 30 30 38 30 30 30 41 38 46 46 03')
        self.assertEqual(parse_pv_response(response, 0), 168)

    def test_rejects_corrupt_response(self) -> None:
        response = bytes.fromhex('06 20 20 20 30 30 38 30 30 30 41 38 46 45 03')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            parse_pv_response(response, 0)

    def test_fuji_royal_timer_status(self) -> None:
        self.assertEqual(read_request('0085', 0), bytes.fromhex('02 20 20 20 30 30 38 35 44 33 03'))
        off = bytes.fromhex('06 20 20 20 30 30 38 35 30 30 30 30 31 33 03')
        on = bytes.fromhex('06 20 20 20 30 30 38 35 32 30 30 30 31 31 03')
        self.assertFalse(timer_state(parse_read_response(off, '0085', 0)))
        self.assertTrue(timer_state(parse_read_response(on, '0085', 0)))

    def test_timer_on_marks_charge_after_manual_start(self) -> None:
        canvas = Mock()
        canvas.device = 209
        canvas.aw = SimpleNamespace(ser=SimpleNamespace(shinko_timer_sync=True,
            shinko_timer_on_event='CHARGE', shinko_timer_auto_start=True))
        canvas.flagstart = True
        canvas.timeindex = [-1, 0, 0, 0, 0, 0, 0, 0]

        tgraphcanvas.shinkoTimerStateTrigger(canvas, True)

        canvas.ToggleRecorder.assert_not_called()
        canvas.markShinkoTimerCharge.assert_called_once_with()

    def test_timer_events_can_leave_recording_under_manual_control(self) -> None:
        canvas = Mock()
        canvas.device = 209
        canvas.aw = SimpleNamespace(ser=SimpleNamespace(shinko_timer_sync=True,
            shinko_timer_on_event='CHARGE', shinko_timer_off_event='DROP',
            shinko_timer_auto_start=False, shinko_timer_auto_stop=False))
        canvas.flagstart = True
        canvas.timeindex = [0, 0, 0, 0, 0, 0, 0, 0]

        tgraphcanvas.shinkoTimerStateTrigger(canvas, False)

        canvas.markDrop.assert_called_once_with()
        canvas.ToggleRecorder.assert_not_called()
