#
# ABOUT
# macOS Bluetooth serial port repair for artisan scope
#
# A Bluetooth serial port on macOS can be left behind stale if the machine
# disappears (it is switched off, unplugged, or the host is suspended) while it
# is paired: the /dev/cu.<machine> device still exists and opens successfully,
# but there is no serial connection behind it any longer, so nothing is sent or
# received. Neither reopening the port, nor toggling Bluetooth, nor
# reconnecting the machine rebuilds it, and the Bluetooth daemon cannot be
# restarted while System Integrity Protection is engaged. Only removing the
# pairing destroys the stale device, after which pairing the machine again
# rebuilds a working serial port.
#
# This module performs that repair via the IOBluetooth framework: it removes
# the pairing, discovers the machine by an inquiry (pairing a device that was
# not discovered first fails) and pairs it again.
#
# NOTE: this is destructive by nature as it removes a pairing, thus it is only
# ever triggered explicitly by the user and never automatically.
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

# the IOBluetooth and objc modules are dynamically generated bridges to the Objective-C
# frameworks, whose members pyright cannot resolve either
# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false

import logging
import os
import sys
import time
from typing import Any, Final

_log = logging.getLogger(__name__)

# IOBluetooth and objc are dynamically generated bridges to the Objective-C frameworks whose
# members cannot be resolved statically, and the delegates below follow the pyobjc idioms of
# returning the result of objc.super().init() via self and of defining attributes in init()
# pylint: disable=no-member,self-cls-assignment,attribute-defined-outside-init


# macOS derives the name of a Bluetooth serial port from the name of the device and, if the
# device offers several serial services, the name of the service, replacing the characters
# that are not valid in a device name
_PORT_PREFIXES:Final[tuple[str, ...]] = ('/dev/cu.', '/dev/tty.')
_NAME_REPLACEMENTS:Final[dict[str,str]] = {' ': '-', '/': '-', ':': '-'}

_INQUIRY_LENGTH:Final[int] = 15    # in seconds
_INQUIRY_TIMEOUT:Final[float] = 25 # in seconds
_PAIRING_TIMEOUT:Final[float] = 30 # in seconds
_PORT_TIMEOUT:Final[float] = 15    # in seconds, time granted to macOS to create the port
_LEGACY_PIN:Final[str] = '0000'    # replied to devices requesting a PIN


# returns True if a Bluetooth serial port repair is offered on this platform
def available() -> bool:
    if not sys.platform.startswith('darwin'):
        return False
    try:
        import IOBluetooth # type:ignore[import-untyped,unused-ignore] # noqa: F401 # pylint: disable=import-error,unused-import
        return True
    except Exception: # pylint: disable=broad-except
        return False


# converts a Bluetooth device name into the name macOS derives its serial port from
def device_name_to_port_name(name:str) -> str:
    for char, replacement in _NAME_REPLACEMENTS.items():
        name = name.replace(char, replacement)
    return name


# returns True if the given port could be the serial port of a device of the given name
def port_matches_device_name(port:str, device_name:str|None) -> bool:
    if not port or not device_name:
        return False
    basename:str = port
    for prefix in _PORT_PREFIXES:
        if basename.startswith(prefix):
            basename = basename[len(prefix):]
            break
    else:
        return False # not a macOS serial port path
    expected:str = device_name_to_port_name(device_name)
    # a device offering several serial services is suffixed by the service name
    return basename == expected or basename.startswith(f'{expected}-')


# returns the paired IOBluetoothDevice serving the given serial port, or None if the port does
# not belong to a paired Bluetooth device (a USB serial port, or a device that is not paired)
def paired_device_for_port(port:str) -> Any:
    try:
        import IOBluetooth # type:ignore[import-untyped,unused-ignore] # pylint: disable=import-error
        devices = IOBluetooth.IOBluetoothDevice.pairedDevices() or []
        for device in devices:
            if port_matches_device_name(port, device.name()):
                return device
    except Exception as e: # pylint: disable=broad-except
        _log.error(e)
    return None


# discovers the device of the given address by an inquiry.
# Pairing a device that was not discovered before fails, thus a device that is to be paired
# again has to be rediscovered first (this is what the system Bluetooth settings do as well)
def _discover_device(address:str) -> Any:
    import objc # type:ignore[import-untyped,unused-ignore] # pylint: disable=import-error
    import IOBluetooth # type:ignore[import-untyped,unused-ignore] # pylint: disable=import-error
    from Foundation import NSObject, NSRunLoop, NSDate # type:ignore[import-not-found,attr-defined,unused-ignore,import-untyped] # pylint: disable=import-error,no-name-in-module

    class InquiryDelegate(NSObject): # type:ignore[misc,no-any-unimported] # pyright:ignore[reportUntypedBaseClass]
        def init(self) -> 'InquiryDelegate':
            self = objc.super(InquiryDelegate, self).init() # noqa: PLW0642 # the pyobjc init idiom
            self.device:Any = None
            self.completed:bool = False
            return self
        def deviceInquiryDeviceFound_device_(self, sender:Any, device:Any) -> None: # pylint: disable=no-self-use
            if str(device.addressString()).lower() == address.lower():
                self.device = device
                sender.stop()
        def deviceInquiryComplete_error_aborted_(self, _sender:Any, _error:int, _aborted:bool) -> None: # pylint: disable=no-self-use
            self.completed = True

    delegate = InquiryDelegate.alloc().init()
    inquiry = IOBluetooth.IOBluetoothDeviceInquiry.inquiryWithDelegate_(delegate)
    inquiry.setInquiryLength_(_INQUIRY_LENGTH)
    inquiry.setUpdateNewDeviceNames_(True)
    inquiry.start()
    deadline:float = time.time() + _INQUIRY_TIMEOUT
    while delegate.device is None and not delegate.completed and time.time() < deadline:
        NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.5))
    inquiry.stop()
    return delegate.device


# pairs the given (discovered) device, replying to a PIN or confirmation request of the device.
# Returns True if the device is paired afterwards
def _pair_device(device:Any) -> bool:
    import objc # type:ignore[import-untyped,unused-ignore] # pylint: disable=import-error
    import IOBluetooth # type:ignore[import-untyped,unused-ignore] # pylint: disable=import-error
    from Foundation import NSObject, NSRunLoop, NSDate # type:ignore[import-not-found,attr-defined,unused-ignore,import-untyped] # pylint: disable=import-error,no-name-in-module

    class PairDelegate(NSObject): # type:ignore[misc,no-any-unimported] # pyright:ignore[reportUntypedBaseClass]
        def init(self) -> 'PairDelegate':
            self = objc.super(PairDelegate, self).init() # noqa: PLW0642 # the pyobjc init idiom
            self.completed:bool = False
            self.error:Any = None
            return self
        def devicePairingPINCodeRequest_(self, sender:Any) -> None: # pylint: disable=no-self-use
            # legacy serial modules commonly use a fixed PIN
            sender.replyPINCode_PINCode_(len(_LEGACY_PIN), _LEGACY_PIN)
        def devicePairingUserConfirmationRequest_numericValue_(self, sender:Any, _value:int) -> None: # pylint: disable=no-self-use
            sender.replyUserConfirmation_(True)
        def devicePairingFinished_error_(self, _sender:Any, error:int) -> None: # pylint: disable=no-self-use
            self.error = error
            self.completed = True

    delegate = PairDelegate.alloc().init()
    pairing = IOBluetooth.IOBluetoothDevicePair.pairWithDevice_(device)
    pairing.setDelegate_(delegate)
    pairing.start()
    deadline:float = time.time() + _PAIRING_TIMEOUT
    while not delegate.completed and time.time() < deadline:
        NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.5))
    if delegate.error:
        _log.error('pairing failed with error %s', str(delegate.error))
    return bool(device.isPaired())


# waits until macOS created (or removed) the given serial port
def _await_port(port:str, exists:bool) -> bool:
    deadline:float = time.time() + _PORT_TIMEOUT
    while time.time() < deadline:
        if os.path.exists(port) == exists:
            return True
        time.sleep(0.5)
    return os.path.exists(port) == exists


# re-establishes the Bluetooth serial port of the machine connected to the given port by
# removing its pairing and pairing the machine again. Returns True if the port exists again.
# NOTE: this removes a pairing and thus must only be called on an explicit user request
def repair_serial_port(port:str) -> bool:
    device = paired_device_for_port(port)
    if device is None:
        _log.info('%s is not the serial port of a paired Bluetooth device', port)
        return False
    try:
        address:str = str(device.addressString())
        name:str = str(device.name())
        _log.info('repairing the Bluetooth serial port of %s (%s)', name, address)
        device.remove()
        if not _await_port(port, exists=False):
            _log.warning('%s still exists after removing the pairing of %s', port, name)
        discovered = _discover_device(address)
        if discovered is None:
            _log.warning('%s was not discovered, it might be switched off or out of range', name)
            return False
        if not _pair_device(discovered):
            _log.warning('%s could not be paired again', name)
            return False
        if not _await_port(port, exists=True):
            _log.warning('%s was paired again, but %s was not created', name, port)
            return False
        _log.info('the Bluetooth serial port %s of %s was re-established', port, name)
        return True
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)
        return False
