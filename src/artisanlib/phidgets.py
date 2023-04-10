#
# ABOUT
# Phidgets support for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2023

from Phidget22.Devices.Manager import Manager # type: ignore
from Phidget22.DeviceID import DeviceID # type: ignore
from Phidget22.DeviceClass import DeviceClass # type: ignore

import logging
from typing import Dict, Optional, TYPE_CHECKING
from typing_extensions import Final  # Python <=3.7

if TYPE_CHECKING:
    from Phidget22.Phidget import Phidget # type: ignore # pylint: disable=unused-import

try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtCore import QSemaphore # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import QSemaphore # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


_log: Final[logging.Logger] = logging.getLogger(__name__)


class PhidgetManager():

    def __init__(self) -> None:
        # a dictionary associating all physical attached Phidget channels
        # to their availability state:
        #    True: available for attach to a software channel
        #    False: occupied and connected to a software channel
        # access to this dict is protected by the managersemaphore and
        # should happen only via the methods addChannel and deleteChannel
        self.attachedPhidgetChannels:Dict['Phidget', bool] = {}
        self.managersemaphore = QSemaphore(1)
        self.manager = Manager()
        self.manager.setOnAttachHandler(self.attachHandler)
        self.manager.setOnDetachHandler(self.detachHandler)
        self.manager.open()
        _log.debug('PhidgetManager opened')

    def close(self):
        self.manager.close()
        self.attachedPhidgetChannels.clear()
        _log.debug('PhidgetManager closed')

    def attachHandler(self,_,attachedChannel):
        try:
            if attachedChannel.getParent().getDeviceClass() != DeviceClass.PHIDCLASS_HUB:
                # we do not add the hub itself
                self.addChannel(attachedChannel)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    def detachHandler(self,_,attachedChannel):
        try:
            self.deleteChannel(attachedChannel)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    def addChannel(self,channel):
#        _log.debug("addChannel: %s %s", channel, type(channel))
        try:
            self.managersemaphore.acquire(1)
            state = True
            try:
                # reserve all channels with the same hubport on the same hub
                hub = channel.getHub()
                hubport = channel.getHubPort()
                hupportdevice = bool(channel.getIsHubPortDevice() == 0) # it is not a direct hubport channel
                for k, _ in self.attachedPhidgetChannels.items():
                    try:
                        khub = k.getHub() # this might raise: "A Phidget channel object of the wrong channel class was passed into this API call."
                        khubport = k.getHubPort()
                        if khub == hub and khubport == hubport:
                            if hupportdevice:
                                if k.getIsHubPortDevice() != 0:
                                    self.attachedPhidgetChannels[k] = False
                                #else:
                                #  other is also a VINT device. Do nothing
                            elif k.getIsHubPortDevice() == 0:
                                # there is a port registered with connected VINT device we deactivate this hubport channel
                                state = False
                            #else:
                            #   do nothing
                    except Exception: # pylint: disable=broad-except
                        pass
            except Exception: # pylint: disable=broad-except
                pass # channel might fail on channel.getHub() like the USB 1048 Phidgets
            self.attachedPhidgetChannels[channel] = state
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if self.managersemaphore.available() < 1:
                self.managersemaphore.release(1)

    def deleteChannel(self,channel):
        _log.debug('deleteChannel: %s', channel)
        try:
            self.managersemaphore.acquire(1)
            # if channel is a VINT device, release all HUBport channels that were blocked by this VINT device
            try:
                hub = channel.getHub()
                hubport = channel.getHubPort()
                hupportdevice = bool(channel.getIsHubPortDevice() == 0) # it is not a direct hubport channel
                if hupportdevice:
                    for k, _ in self.attachedPhidgetChannels.items():
                        if k != channel:
                            try:
                                khub = k.getHub()
                                khubport = k.getHubPort()
                                if khub == hub and khubport == hubport:
                                    self.attachedPhidgetChannels[k] = True
                            except Exception: # pylint: disable=broad-except
                                #_log.exception(e)
                                pass
            except Exception: # pylint: disable=broad-except
                pass # raises an exception on non VINT Phidget modules
            self.attachedPhidgetChannels.pop(channel, None)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if self.managersemaphore.available() < 1:
                self.managersemaphore.release(1)

    def getChannel(self,serial,port,channel,phidget_class_name,device_id,remote,remoteOnly):
        try:
            self.managersemaphore.acquire(1)
            # we are looking for HUB ports
            hub = 1 if device_id in [DeviceID.PHIDID_HUB0000] else 0
            for k, _ in self.attachedPhidgetChannels.items():
                if k.getIsHubPortDevice() or k.getDeviceClass() == DeviceClass.PHIDCLASS_VINT:
                    kport = k.getHubPort()
                else:
                    kport = 0  # getHubPort() returns 0 for USB Phidgets!
                if k.getDeviceSerialNumber() == serial and (port is None or kport == port) and \
                    (hub or (k.getDeviceID() == device_id)) and \
                    ((remote and not remoteOnly) or (not remote and k.getIsLocal()) or (remote and remoteOnly and not k.getIsLocal())) and \
                    k.getChannelClassName() == phidget_class_name and \
                    k.getChannel() == channel:
                    return k
            return None
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            return None
        finally:
            if self.managersemaphore.available() < 1:
                self.managersemaphore.release(1)

    def reserveSerialPort(self,serial,port,channel,phidget_class_name,device_id,remote=False,remoteOnly=False):
        chnl = self.getChannel(serial,port,channel,phidget_class_name,device_id,remote,remoteOnly)
        self.reserveChannel(chnl)

    def releaseSerialPort(self,serial,port,channel,phidget_class_name,device_id,remote=False,remoteOnly=False):
        chnl = self.getChannel(serial,port,channel,phidget_class_name,device_id,remote,remoteOnly)
        self.releaseChannel(chnl)

    # should be called from the attach handler that binds this hardware channel to a software channel
    def reserveChannel(self,channel):
        _log.debug('reserveChannel: %s', channel)
        try:
            self.managersemaphore.acquire(1)
            if channel is not None and channel in self.attachedPhidgetChannels:
                self.attachedPhidgetChannels[channel] = False  # reserve channel
                if channel.getIsHubPortDevice():
                    hub = channel.getHub()
                    port = channel.getHubPort()
                    # reserve also all other channels with that hub/port combination
                    for k, _ in self.attachedPhidgetChannels.items():
                        try:
                            if k.getHub() == hub and k.getHubPort() == port:
                                self.attachedPhidgetChannels[k] = False
                        except Exception: # pylint: disable=broad-except
                            pass
                #else:
                #  not a HUB port
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if self.managersemaphore.available() < 1:
                self.managersemaphore.release(1)

    # should be called from the detach handler that releases this hardware channel from a software channel
    def releaseChannel(self,channel):
        _log.debug('releaseChannel: %s', channel)
        try:
            self.managersemaphore.acquire(1)
            if channel is not None and channel in self.attachedPhidgetChannels:
                self.attachedPhidgetChannels[channel] = True # channel again available for attach
                if channel.getIsHubPortDevice():
                    hub = channel.getHub()
                    port = channel.getHubPort()
                    # enable also all other channels with that hub/port combination
                    for k, _ in self.attachedPhidgetChannels.items():
                        try:
                            if k.getHub() == hub and k.getHubPort() == port:
                                self.attachedPhidgetChannels[k] = True
                        except Exception: # pylint: disable=broad-except
                            pass
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if self.managersemaphore.available() < 1:
                self.managersemaphore.release(1)

#    def print_list(self,items):
#        for k,v in items:
#            print(v,k.getDeviceSerialNumber(),k.getDeviceClass(),k.getDeviceClassName(),k.getDeviceName(),k.getDeviceSKU(),k.getChannelClassName(),k.getDeviceID(),k.getIsHubPortDevice(),"port: ",k.getHubPort(),"ch: ", k.getChannel(), "local: ", k.getIsLocal())
#
#    def print_list2(self,items):
#        for k in items:
#            print(k.getDeviceSerialNumber(),k.getChannelClassName(),k.getDeviceID(),k.getIsHubPortDevice(),"port: ", k.getHubPort(),"ch: ",k.getChannel(), "local: ", k.getIsLocal())

    # returns the first matching Phidget channel and reserves it
    def getFirstMatchingPhidget(self,phidget_class_name,device_id,channel=None,remote=False,remoteOnly=False,serial:Optional[int]=None,hubport=None):
        _log.debug('getFirstMatchingPhidget(%s,%s,%s,%s,%s,%s,%s)',phidget_class_name,device_id,channel,remote,remoteOnly,serial,hubport)
        try:
            self.managersemaphore.acquire(1)
            if device_id in [
                    DeviceID.PHIDID_HUB0000,
                    DeviceID.PHIDID_DIGITALINPUT_PORT,
                    DeviceID.PHIDID_DIGITALOUTPUT_PORT,
                    DeviceID.PHIDID_VOLTAGEINPUT_PORT,
                    DeviceID.PHIDID_VOLTAGERATIOINPUT_PORT]:
                # we are looking for HUB ports
                hub = 1
            else:
                hub = 0

#            self.print_list(self.attachedPhidgetChannels.items())

            # get list of all matching phidget channels
            matching_channels = [k for k, v in self.attachedPhidgetChannels.items() if v and \
                (hub or (k.getDeviceID() == device_id)) and \
                (serial is None or serial == k.getDeviceSerialNumber()) and \
                (hubport is None or hubport == k.getHubPort()) and \
                ((remote and not remoteOnly) or (not remote and k.getIsLocal()) or (remote and remoteOnly and not k.getIsLocal())) and \
                k.getChannelClassName() == phidget_class_name and \
                (channel is None or (not hub and channel == k.getChannel()) or (hub and k.getIsHubPortDevice() and k.getHubPort() == channel))]

#            self.print_list2(matching_channels)

            # sort by serial number (local first)
            matching_channels.sort(key=lambda x:(x.getDeviceSerialNumber(),x.getHubPort()))
            # return smallest / first item
            if len(matching_channels) > 0:
                p = matching_channels[0]
                if p.getIsHubPortDevice() or p.getDeviceClass() == DeviceClass.PHIDCLASS_VINT:
                    port = p.getHubPort()
                else:
                    port = None
                return p.getDeviceSerialNumber(), port
            return None, None
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            return None, None
        finally:
            if self.managersemaphore.available() < 1:
                self.managersemaphore.release(1)
