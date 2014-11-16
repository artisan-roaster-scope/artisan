#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# list_ports_osx.py
#
# Copyright (c) 2013, Paul Holleis, Marko Luther
# All rights reserved.
# 
# 
# LICENSE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# List all of the callout devices in OS/X by querying IOKit.
# See the following for a reference of how to do this:
# http://developer.apple.com/library/mac/#documentation/DeviceDrivers/Conceptual/WorkingWSerial/WWSerial_SerialDevs/SerialDevices.html#//apple_ref/doc/uid/TP30000384-CIHGEAFD
# More help from darwin_hid.py
# Also see the 'IORegistryExplorer' for an idea of what we are actually searching

import ctypes
from ctypes import util
import re

iokit = ctypes.cdll.LoadLibrary(ctypes.util.find_library('IOKit'))
cf = ctypes.cdll.LoadLibrary(ctypes.util.find_library('CoreFoundation'))

kIOMasterPortDefault = ctypes.c_void_p.in_dll(iokit, "kIOMasterPortDefault")
kCFAllocatorDefault = ctypes.c_void_p.in_dll(cf, "kCFAllocatorDefault")

kCFStringEncodingMacRoman = 0

iokit.IOServiceMatching.restype = ctypes.c_void_p

iokit.IOServiceGetMatchingServices.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
iokit.IOServiceGetMatchingServices.restype = ctypes.c_void_p

iokit.IORegistryEntryGetParentEntry.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

iokit.IORegistryEntryCreateCFProperty.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32]
iokit.IORegistryEntryCreateCFProperty.restype = ctypes.c_void_p

iokit.IORegistryEntryGetPath.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
iokit.IORegistryEntryGetPath.restype = ctypes.c_void_p

iokit.IORegistryEntryGetName.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
iokit.IORegistryEntryGetName.restype = ctypes.c_void_p

iokit.IOObjectGetClass.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
iokit.IOObjectGetClass.restype = ctypes.c_void_p

iokit.IOObjectRelease.argtypes = [ctypes.c_void_p]


cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int32]
cf.CFStringCreateWithCString.restype = ctypes.c_void_p

cf.CFStringGetCStringPtr.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
cf.CFStringGetCStringPtr.restype = ctypes.c_char_p

cf.CFNumberGetValue.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p]
cf.CFNumberGetValue.restype = ctypes.c_void_p

def get_string_property(device_t, prop):
    """ Search the given device for the specified string property
    
    @param device_t Device to search
    @param prop String to search for.
    @return Python string containing the value, or None if not found.
    """
    key = cf.CFStringCreateWithCString(
        kCFAllocatorDefault,
        prop.encode("mac_roman"),
        kCFStringEncodingMacRoman
    )

    CFContainer = iokit.IORegistryEntryCreateCFProperty(
        device_t,
        key,
        kCFAllocatorDefault,
        0
    );

    output = None

    if CFContainer:
        output = cf.CFStringGetCStringPtr(CFContainer, 0)    
        
    if output:
        return output.decode("utf-8")
    else:
        return  None

def get_int_property(device_t, prop):
    """ Search the given device for the specified string prop
    
    @param device_t Device to search
    @param prop String to search for.
    @return Python string containing the value, or None if not found.
    """
    key = cf.CFStringCreateWithCString(
        kCFAllocatorDefault,
        prop.encode("mac_roman"),
        kCFStringEncodingMacRoman
    )

    CFContainer = iokit.IORegistryEntryCreateCFProperty(
        device_t,
        key,
        kCFAllocatorDefault,
        0
    );

    number = ctypes.c_uint16()

    if CFContainer:
        cf.CFNumberGetValue(CFContainer, 2, ctypes.byref(number))

    return number.value

def IORegistryEntryGetName(device):
    pathname = ctypes.create_string_buffer(100) # TODO: Is this ok?
    iokit.IOObjectGetClass(
        device,
        ctypes.byref(pathname)
    )

    return pathname.value

def GetParentDeviceByType(device, parent_type):
    """ Find the first parent of a device that implements the parent_type
        @param IOService Service to inspect
        @return Pointer to the parent type, or None if it was not found.
    """
    # First, try to walk up the IOService tree to find a parent of this device that is a IOUSBDevice.
    while IORegistryEntryGetName(device) != parent_type:

        parent = ctypes.c_void_p()
        response = iokit.IORegistryEntryGetParentEntry(
            device,
            "IOService".encode("mac_roman"),
            ctypes.byref(parent)
        )

        # If we weren't able to find a parent for the device, we're done.
        if response != 0:
            return None

        device = parent

    return device

def GetIOServicesByType(service_type):
    """
    """
    serial_port_iterator = ctypes.c_void_p()

    iokit.IOServiceGetMatchingServices(
        kIOMasterPortDefault,
        iokit.IOServiceMatching(service_type),
        ctypes.byref(serial_port_iterator)
    )

    services = []
    while iokit.IOIteratorIsValid(serial_port_iterator):
        service = iokit.IOIteratorNext(serial_port_iterator)
        if not service:
            break
        services.append(service)

    iokit.IOObjectRelease(serial_port_iterator)

    return services

def comports():
    # Scan for all iokit serial ports
    services = GetIOServicesByType(b'IOSerialBSDClient')

    ports = []
    for service in services:
        info = []

        # First, add the callout device file.
        info.append(get_string_property(service, "IOCalloutDevice"))

        # If the serial port is implemented by a
        usb_device = GetParentDeviceByType(service, b"IOUSBDevice")
        if usb_device != None:
            info.append(get_string_property(usb_device, "USB Product Name"))

            info.append(
                "USB VID:PID=%x:%x SNR=%s"%(
                get_int_property(usb_device, "idVendor"),
                get_int_property(usb_device, "idProduct"),
                get_string_property(usb_device, "USB Serial Number"))
            )
        else:
            info.append('')
            info.append('')

        ports.append(info)

    return ports

# test
if __name__ == '__main__':
    for port, desc, hwid in sorted(comports()):
        print("%s: %s [%s]") % (port, desc, hwid)
