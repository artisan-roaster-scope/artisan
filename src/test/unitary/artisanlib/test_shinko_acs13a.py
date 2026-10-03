"""ACS-13A wire format, including a frame captured from a CMA-connected controller."""

import unittest

from artisanlib.shinko_acs13a import parse_pv_response, pv_request


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
