"""Read-only Shinko standard serial protocol support for the ACS-13A PV."""


def pv_request(instrument_number:int) -> bytes:
    if not 0 <= instrument_number <= 94:
        raise ValueError('ACS-13A instrument number must be between 0 and 94')
    body = bytes((0x20 + instrument_number, 0x20, 0x20)) + b'0080'
    checksum = f'{-sum(body) & 0xff:02X}'.encode('ascii')
    return b'\x02' + body + checksum + b'\x03'


def parse_pv_response(response:bytes, instrument_number:int) -> int:
    if len(response) != 15:
        raise ValueError('Incomplete ACS-13A PV response')
    if response[:4] != bytes((0x06, 0x20 + instrument_number, 0x20, 0x20)) or response[4:8] != b'0080' or response[-1] != 0x03:
        raise ValueError('Unexpected ACS-13A PV response')
    checksum = f'{-sum(response[1:-3]) & 0xff:02X}'.encode('ascii')
    if response[-3:-1] != checksum:
        raise ValueError('Invalid ACS-13A PV checksum')
    try:
        return int.from_bytes(bytes.fromhex(response[8:12].decode('ascii')), 'big', signed=True)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError('Invalid ACS-13A PV value') from exc
