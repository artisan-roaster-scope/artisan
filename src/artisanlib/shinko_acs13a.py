"""Read-only Shinko standard serial protocol support for the ACS-13A."""


FUJI_ROYAL_TIMER_MASK = 0x2000


def read_request(item:str, instrument_number:int) -> bytes:
    if len(item) != 4 or any(c not in '0123456789ABCDEF' for c in item):
        raise ValueError('ACS-13A item must be four uppercase hexadecimal digits')
    if not 0 <= instrument_number <= 94:
        raise ValueError('ACS-13A instrument number must be between 0 and 94')
    body = bytes((0x20 + instrument_number, 0x20, 0x20)) + item.encode('ascii')
    checksum = f'{-sum(body) & 0xff:02X}'.encode('ascii')
    return b'\x02' + body + checksum + b'\x03'


def parse_read_response(response:bytes, item:str, instrument_number:int) -> int:
    if len(response) != 15:
        raise ValueError('Incomplete ACS-13A read response')
    if response[:4] != bytes((0x06, 0x20 + instrument_number, 0x20, 0x20)) or response[4:8] != item.encode('ascii') or response[-1] != 0x03:
        raise ValueError('Unexpected ACS-13A read response')
    checksum = f'{-sum(response[1:-3]) & 0xff:02X}'.encode('ascii')
    if response[-3:-1] != checksum:
        raise ValueError('Invalid ACS-13A read checksum')
    try:
        return int(response[8:12], 16)
    except ValueError as exc:
        raise ValueError('Invalid ACS-13A read value') from exc


def pv_request(instrument_number:int) -> bytes:
    return read_request('0080', instrument_number)


def parse_pv_response(response:bytes, instrument_number:int) -> int:
    value = parse_read_response(response, '0080', instrument_number)
    return value - 0x10000 if value & 0x8000 else value


def timer_state(status:int) -> bool:
    """Observed Fuji Royal timer contact in status item 0085 bit 13."""
    return bool(status & FUJI_ROYAL_TIMER_MASK)
