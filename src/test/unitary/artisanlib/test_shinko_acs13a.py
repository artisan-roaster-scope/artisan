"""ACS-13A wire format, including a frame captured from a CMA-connected controller."""

import unittest

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
