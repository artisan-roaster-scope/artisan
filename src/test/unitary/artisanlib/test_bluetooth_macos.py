"""
Unit tests for the artisanlib.bluetooth_macos module.

The module re-establishes a stale macOS Bluetooth serial port by removing the pairing of the
machine and pairing it again. These tests cover the platform independent parts:

- the derivation of a serial port name from a Bluetooth device name, which is how a configured
  port is associated with the paired device serving it (no device address or name is hard coded
  anywhere, the association is derived from the port the user configured)
- the lookup of the paired device of a port against a faked IOBluetooth
- that the repair reports a failure instead of raising if the port does not belong to a paired
  Bluetooth device
"""

import sys
from typing import Any

import pytest

from artisanlib.bluetooth_macos import (
    available,
    device_name_to_port_name,
    paired_device_for_port,
    port_matches_device_name,
    repair_serial_port,
)


class TestPortNameDerivation:
    """macOS derives the name of a Bluetooth serial port from the name of the device."""

    @pytest.mark.parametrize(('device_name', 'expected'), [
        ('Roaster', 'Roaster'),
        ('Roaster_SRSv6', 'Roaster_SRSv6'),
        ('My Roaster', 'My-Roaster'),        # spaces are replaced
        ('Kaleido M6/M10', 'Kaleido-M6-M10'),# as are the characters invalid in a port name
        ('BT:Serial', 'BT-Serial'),
    ])
    def test_device_name_to_port_name(self, device_name:str, expected:str) -> None:
        assert device_name_to_port_name(device_name) == expected

    @pytest.mark.parametrize(('port', 'device_name'), [
        ('/dev/cu.Roaster_SRSv6', 'Roaster_SRSv6'),
        ('/dev/tty.Roaster_SRSv6', 'Roaster_SRSv6'),
        ('/dev/cu.My-Roaster', 'My Roaster'),
        ('/dev/cu.Roaster-SPPDev', 'Roaster'),   # a device with a named serial service
        ('/dev/cu.Roaster-SerialPort', 'Roaster'),
    ])
    def test_matching_ports(self, port:str, device_name:str) -> None:
        assert port_matches_device_name(port, device_name)

    @pytest.mark.parametrize(('port', 'device_name'), [
        ('/dev/cu.usbserial-FTFKDA5O', 'Roaster_SRSv6'), # a USB serial port
        ('/dev/cu.Roaster_SRSv6', 'Some Other Machine'),
        ('/dev/cu.RoasterX', 'Roaster'),                 # not a service suffix
        ('COM4', 'Roaster'),                             # not a macOS port path
        ('', 'Roaster'),
        ('/dev/cu.Roaster', None),
        ('/dev/cu.Roaster', ''),
    ])
    def test_non_matching_ports(self, port:str, device_name:str|None) -> None:
        assert not port_matches_device_name(port, device_name)


class FakeDevice:
    """Stands in for an IOBluetoothDevice."""

    def __init__(self, name:str, address:str = '00-11-22-33-44-55') -> None:
        self._name = name
        self._address = address
        self.removed = False

    def name(self) -> str:
        return self._name

    def addressString(self) -> str:  # noqa: N802 # the Objective-C selector name
        return self._address

    def remove(self) -> None:
        self.removed = True


def _fake_iobluetooth(devices:list[FakeDevice]) -> Any:
    """Builds a stand-in for the IOBluetooth module exposing the paired devices."""
    device_class = type('IOBluetoothDevice', (), {'pairedDevices': staticmethod(lambda: devices)})
    return type('IOBluetooth', (), {'IOBluetoothDevice': device_class})


class TestPairedDeviceLookup:

    def test_finds_the_device_serving_the_port(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        roaster = FakeDevice('Roaster_SRSv6')
        monkeypatch.setitem(sys.modules, 'IOBluetooth',
                _fake_iobluetooth([FakeDevice('Keyboard'), roaster, FakeDevice('Mouse')]))
        assert paired_device_for_port('/dev/cu.Roaster_SRSv6') is roaster

    def test_returns_none_for_a_usb_serial_port(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        monkeypatch.setitem(sys.modules, 'IOBluetooth',
                _fake_iobluetooth([FakeDevice('Roaster_SRSv6')]))
        assert paired_device_for_port('/dev/cu.usbserial-FTFKDA5O') is None

    def test_returns_none_without_paired_devices(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        monkeypatch.setitem(sys.modules, 'IOBluetooth', _fake_iobluetooth([]))
        assert paired_device_for_port('/dev/cu.Roaster_SRSv6') is None

    def test_a_failing_framework_does_not_raise(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        broken = type('IOBluetooth', (), {})  # no IOBluetoothDevice attribute
        monkeypatch.setitem(sys.modules, 'IOBluetooth', broken)
        assert paired_device_for_port('/dev/cu.Roaster_SRSv6') is None


class TestRepair:

    def test_repair_of_a_port_without_paired_device(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        """A port that is not served by a paired device is reported, not repaired."""
        monkeypatch.setitem(sys.modules, 'IOBluetooth', _fake_iobluetooth([]))
        assert repair_serial_port('/dev/cu.usbserial-FTFKDA5O') is False

    def test_the_pairing_is_not_removed_without_a_match(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        """A device that does not serve the port must never be unpaired."""
        other = FakeDevice('Some Other Machine')
        monkeypatch.setitem(sys.modules, 'IOBluetooth', _fake_iobluetooth([other]))
        assert repair_serial_port('/dev/cu.Roaster_SRSv6') is False
        assert not other.removed


class TestAvailability:

    def test_not_available_off_macos(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        monkeypatch.setattr(sys, 'platform', 'win32')
        assert not available()

    def test_availability_follows_the_framework_on_macos(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        monkeypatch.setattr(sys, 'platform', 'darwin')
        monkeypatch.setitem(sys.modules, 'IOBluetooth', _fake_iobluetooth([]))
        assert available()
