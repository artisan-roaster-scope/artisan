"""Unit tests for artisanlib.device_registry module.

Tests the device list extraction, category sets, and helper functions.
All data is static — no Qt, no fixtures, no mocks.
"""

from artisanlib.device_registry import (DEVICES, DEVICE_INFO, BINARY_DEVICES,
    NON_SERIAL_DEVICES, NON_TEMP_DEVICES, PHIDGET_DEVICES, SPECIAL_DEVICES,
    get_device_name, is_binary_device, is_non_serial_device,
    is_non_temp_device, is_phidget_device, is_special_device)


def test_devices_length() -> None:
    assert len(DEVICES) == 206


def test_device_id_is_index_plus_one() -> None:
    assert get_device_name(1) == 'Omega HH806AU'
    assert get_device_name(18) == 'NONE'
    assert get_device_name(138) == 'Kaleido BT/ET'
    assert DEVICES[205] == '+MQTT 1112'


def test_get_device_name_edge_cases() -> None:
    assert get_device_name(1) == DEVICES[0]
    assert get_device_name(206) == DEVICES[205]


def test_phidget_devices() -> None:
    for did in PHIDGET_DEVICES:
        assert is_phidget_device(did)
        assert is_non_serial_device(did)
    assert not is_phidget_device(138)
    assert not is_phidget_device(1)


def test_known_non_serial_devices() -> None:
    assert is_non_serial_device(138)
    assert is_non_serial_device(142)
    assert not is_non_serial_device(1)


def test_all_devices_index_consistent() -> None:
    for i, name in enumerate(DEVICES):
        assert get_device_name(i + 1) == name


def test_special_devices() -> None:
    assert is_special_device(18)
    assert is_special_device(25)
    assert is_special_device(50)
    assert not is_special_device(138)


def test_binary_devices() -> None:
    assert len(BINARY_DEVICES) > 0
    for did in BINARY_DEVICES:
        assert is_binary_device(did)
    assert not is_binary_device(138)


def test_device_info_populated() -> None:
    assert len(DEVICE_INFO) == 206
    info = DEVICE_INFO[138]
    assert info['name'] == 'Kaleido BT/ET'
    assert info['index'] == 137


def test_category_sets_no_overlap_serial_vs_non_serial() -> None:
    known_serial = {1, 2, 3}
    for did in known_serial:
        assert not is_non_serial_device(did)
