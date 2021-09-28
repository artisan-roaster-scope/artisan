# -*- coding: utf-8 -*-
#
# ABOUT
# BLE support for Artisan

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
# Marko Luther, 2019


import logging
from typing import Final
from enum import Enum

try:
    #pylint: disable = E, W, R, C
    from PyQt6 import QtCore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6 import QtBluetooth # @UnusedImport @Reimport  @UnresolvedImport
except Exception:
    #pylint: disable = E, W, R, C
    from PyQt5 import QtCore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5 import QtBluetooth # @UnusedImport @Reimport  @UnresolvedImport


_log: Final = logging.getLogger(__name__)


class BLE_CHAR_TYPE(Enum):
    BLE_CHAR_NOTIFY = 'BLE_CHAR_NOTIFY'
    BLE_CHAR_WRITE = 'BLE_CHAR_WRITE'
    BLE_CHAR_NOTIFY_WRITE = 'BLE_CHAR_NOTIFY_WRITE'


class BleInterface(QtCore.QObject):
    weightChanged = QtCore.pyqtSignal(float)
    batteryChanged = QtCore.pyqtSignal(int)
    deviceDisconnected = QtCore.pyqtSignal()
    dataReceived = QtCore.pyqtSignal(QtCore.QByteArray)
    
    # the uuid_service_char_tuples is a list of tuples of the form (service_uuid, char_uuid)
    # with service_uuid the services to connect to and char_uuid the characteristic uuid we register for write
    # at this service
    # if device_names are given, connections ar only made to devices with (partial-)matching names (fast)
    # if device_names are not given, connections are made to every discovered device with the required UUIDs (slow)
    def __init__(self, uuid_service_char_tuples, processData, sendHeartbeat, sendStop, reset, device_names=None):
        super().__init__()
        
        cp = QtBluetooth.QLowEnergyConnectionParameters()
        _log.debug("max interval: %s", cp.maximumInterval())
        _log.debug("min interval: %s", cp.minimumInterval())
        _log.debug("supervisionTimeout: %s", cp.supervisionTimeout())
        _log.debug("latency: %s", cp.latency())
        
        self.device_names = device_names

        self.UUID_SERVICE_CHAR_TUPLES=[]
        for (uuid_servive, uuid_char_list) in uuid_service_char_tuples:
            for (uuid_char, ble_write_type) in uuid_char_list:
                self.UUID_SERVICE_CHAR_TUPLES.append((QtBluetooth.QBluetoothUuid(uuid_servive),(QtBluetooth.QBluetoothUuid(uuid_char),ble_write_type)) )

        self.service_uuid = None
        self.char_uuid = None

        self.processData = processData
        self.sendHeartbeat = sendHeartbeat
        self.sendStop = sendStop
        self.reset = reset
        
        self.QBluetoothDeviceDiscoveryAgent_LowEnergyMethod = 2
        self.ENABLE_NOTIFICATION_VALUE = QtCore.QByteArray.fromHex(b"0100")
        self.DISABLE_NOTIFICATION_VALUE = QtCore.QByteArray.fromHex(b"0000")

        self.m_deviceDiscoveryAgent = QtBluetooth.QBluetoothDeviceDiscoveryAgent()
        self.m_deviceDiscoveryAgent.setLowEnergyDiscoveryTimeout(500)
        self.m_deviceDiscoveryAgent.deviceDiscovered.connect(self.addDevice)
        self.m_deviceDiscoveryAgent.finished.connect(self.onScanFinished)
        self.m_deviceDiscoveryAgent.canceled.connect(self.onScanFinished)

        self.m_device = None
        self.m_control = None
        self.m_service = None

        self.m_notificationDesc = QtBluetooth.QLowEnergyDescriptor()
        self.m_readCharacteristic = QtBluetooth.QLowEnergyCharacteristic()
        self.m_writeCharacteristic = QtBluetooth.QLowEnergyCharacteristic()
        self.m_writemode = QtBluetooth.QLowEnergyService.WriteMode()

        self.m_connected = False
        self.m_readTimer = None
        
        self.dataReceived.connect(self.dataReceivedProcessing)
        

    def removeDevice(self):
        self.m_device = None
    
    def removeControl(self):
        try:
            self.m_control.discoveryFinished.disconnect()
            self.m_control.connected.disconnect()
            self.m_control.disconnected.disconnect()
            self.m_control.deleteLater()
        except Exception: # pylint: disable=broad-except
            pass
        finally:
            self.m_control = None
            
    def removeService(self):
        try:
            self.service_uuid = None
            self.char_uuid = None
            self.m_service.stateChanged.disconnect()
            self.m_service.characteristicChanged.disconnect()
            self.m_service.characteristicRead.disconnect()
            self.m_service.deleteLater()
        except Exception: # pylint: disable=broad-except
            pass
        finally:
            self.m_service = None

#--------

    @QtCore.pyqtSlot("QByteArray")
    def dataReceivedProcessing(self,data=QtCore.QByteArray):
#        _log.debug("data received: %s", data)
        res_w, res_b = self.processData(self.write, data)
        if res_w is not None:
            self.weightChanged.emit(res_w)
        if res_b is not None:
            self.batteryChanged.emit(res_b)

    def read(self):
        if(self.m_service and self.m_readCharacteristic.isValid()):
            self.m_service.readCharacteristic(self.m_readCharacteristic)
        
    def write(self,data=bytearray()):
#        _log.debug("write data: %s", data)
        if (self.m_service and self.m_writeCharacteristic.isValid()):
            if (len(data) > 20):
                sentBytes = 0
                while sentBytes < len(data):
                    self.m_service.writeCharacteristic(self.m_writeCharacteristic,data[sentBytes:sentBytes + 20],self.m_writemode)
                    sentBytes+=20
                    if self.m_writemode == QtBluetooth.QLowEnergyService.WriteWithResponse:
                        pass
            else:
                self.m_service.writeCharacteristic(self.m_writeCharacteristic,data,self.m_writemode)

    def update_connected(self,connected=bool):
        _log.debug("update_connected(%s)", connected)
        if connected != self.m_connected:
            self.m_connected = connected
#            self.connectedChanged.emit(connected)
            if self.m_connected:
                if self.m_device:
                    _log.info("connected to %s", self.m_device.name())
                self.reset()
            elif self.m_device:
                _log.info("disconnected from %s", self.m_device.name())

    def heartbeat(self):
        if self.m_connected:
#            _log.debug("send heartbeat")
            self.sendHeartbeat(self.write)
            QtCore.QTimer.singleShot(2000,self.heartbeat)

    @QtCore.pyqtSlot("QLowEnergyDescriptor","QByteArray")
    def descriptorWrittenSlot(self,descriptor,newValue):
        if descriptor.isValid():
            if newValue == self.ENABLE_NOTIFICATION_VALUE:
                # notifications enabled
                self.heartbeat()
            elif newValue == self.DISABLE_NOTIFICATION_VALUE:
                # notifications disabled
                self.m_control.disconnectFromDevice()

    def searchCharacteristic(self):
        _log.debug("searchCharacteristic()")
        if self.m_service:
            for c in self.m_service.characteristics():
                if c.isValid():
                    for (uuid_char, ble_write_type) in self.char_uuid:
                        # we register write only for the given char_uuid associated to the service uuid we are connected to
                        if (c.uuid() == uuid_char and 
                                (ble_write_type in (
                                    BLE_CHAR_TYPE.BLE_CHAR_NOTIFY_WRITE,
                                    BLE_CHAR_TYPE.BLE_CHAR_WRITE))):
                            if ((c.properties() & QtBluetooth.QLowEnergyCharacteristic.WriteNoResponse) or 
                                    (c.properties() & QtBluetooth.QLowEnergyCharacteristic.Write)):
                                self.m_writeCharacteristic = c
                                self.update_connected(True)
                                if c.properties() & QtBluetooth.QLowEnergyCharacteristic.WriteNoResponse:
                                    self.m_writemode=QtBluetooth.QLowEnergyService.WriteWithoutResponse
                                else:
                                    self.m_writemode=QtBluetooth.QLowEnergyService.WriteWithResponse
                        if c.uuid() == uuid_char and (
                                ble_write_type in (
                                    BLE_CHAR_TYPE.BLE_CHAR_NOTIFY_WRITE,
                                    BLE_CHAR_TYPE.BLE_CHAR_NOTIFY)):
                            self.m_notificationDesc = c.descriptor(QtBluetooth.QBluetoothUuid(QtBluetooth.QBluetoothUuid.ClientCharacteristicConfiguration))
                            if self.m_notificationDesc.isValid():
                                self.m_service.descriptorWritten.connect(self.descriptorWrittenSlot)
                                self.m_service.writeDescriptor(self.m_notificationDesc,self.ENABLE_NOTIFICATION_VALUE)

    @QtCore.pyqtSlot("QLowEnergyCharacteristic","QByteArray")
    def onCharacteristicChanged(self,_=QtBluetooth.QLowEnergyCharacteristic,value=QtCore.QByteArray):
#        print("Characteristic Changed {values}".format(values=value))
        self.dataReceived.emit(value)

    @QtCore.pyqtSlot("QLowEnergyCharacteristic","QByteArray")
    def onCharacteristicRead(self,_=QtBluetooth.QLowEnergyCharacteristic,value=QtCore.QByteArray):
#        print("Characteristic Read:  {values}".format(values=value))
        pass

    @QtCore.pyqtSlot("QLowEnergyService::ServiceState")
    def onServiceStateChanged(self,s):
        _log.debug("onServiceStateChanged(%s)", s)
        if s == QtBluetooth.QLowEnergyService.ServiceDiscovered:
            self.searchCharacteristic()

    @QtCore.pyqtSlot()
    def onServiceScanDone(self):
        _log.debug("onServiceScanDone()")
        for uuid in self.m_control.services():
            for (uuid_servive, (uuid_char, ble_write_type)) in self.UUID_SERVICE_CHAR_TUPLES:
                if uuid_servive is not None:
                    if uuid_servive == uuid:
                        _log.debug("createServiceObject(%s)", uuid.toString())
                        self.service_uuid = uuid_servive
                        if not self.char_uuid:
                            self.char_uuid = []
                        self.char_uuid.append((uuid_char, ble_write_type))
                        self.m_service = self.m_control.createServiceObject(uuid)
                        self.m_service.stateChanged.connect(self.onServiceStateChanged)
                        self.m_service.characteristicChanged.connect(self.onCharacteristicChanged)
                        self.m_service.characteristicRead.connect(self.onCharacteristicRead)
        if self.m_service is not None and self.m_service.state() == QtBluetooth.QLowEnergyService.DiscoveryRequired:
            self.m_service.discoverDetails()
        else:
            self.searchCharacteristic()
                
    @QtCore.pyqtSlot()
    def onDeviceConnected(self):
        _log.debug("onDeviceConnected")
        self.m_control.discoverServices()

    @QtCore.pyqtSlot()
    def onDeviceDisconnected(self):
        _log.debug("onDeviceDisconnected")
        self.update_connected(False)
        self.removeService()
        self.removeControl()
        self.removeDevice()
        self.deviceDisconnected.emit()

    def connectCurrentDevice(self):
        if self.m_device is not None:
            _log.debug("connectCurrentDevice: %s", self.m_device.name())
            self.m_control = QtBluetooth.QLowEnergyController(self.m_device)
            self.m_control.discoveryFinished.connect(self.onServiceScanDone)
            self.m_control.connected.connect(self.onDeviceConnected)
            self.m_control.disconnected.connect(self.onDeviceDisconnected)
            self.m_control.connectToDevice()
        else:
            self.deviceDisconnected.emit()
        
    @QtCore.pyqtSlot()
    def onScanFinished(self):
        _log.debug("onScanFinished()")
        if self.m_device is None:
            self.onDeviceDisconnected()
        else:
            self.connectCurrentDevice()

    @staticmethod
    def deviceHasService(device, service_uuid):
        if device is None:
            return False
        services = device.serviceUuids()
        has_service = services and len(services)>0 and service_uuid in services[0]
        if has_service:
            _log.debug("deviceHasService(%s, %s)", device.name(), service_uuid.toString())
        return has_service

    @QtCore.pyqtSlot("QBluetoothDeviceInfo")
    def addDevice(self, device):
#        _log.debug("addDevice()")
        if self.m_device is None and device.coreConfigurations() & QtBluetooth.QBluetoothDeviceInfo.LowEnergyCoreConfiguration:
#            _log.debug("discovered LE Device name: %s,  address: %s", device.name(), device.address().toString())
            m_device = QtBluetooth.QBluetoothDeviceInfo(device)            
            if self.device_names is None:
                _log.debug("check device for matching services")
                for (uuid_service, _) in self.UUID_SERVICE_CHAR_TUPLES:
                    if self.deviceHasService(m_device, uuid_service):
                        _log.debug("device service match")
                        self.m_device = m_device
                        # we found our device and stop scanning
                        self.m_deviceDiscoveryAgent.stop()
                        return
            elif any((dn and dn in m_device.name()) for dn in self.device_names):
                _log.debug("device name match")
                self.m_device = m_device
                # we found our device and stop scanning
                self.m_deviceDiscoveryAgent.stop()

#----------------

    def disconnectDevice(self):
        _log.debug("disconnectDevice()")
        self.update_connected(False) # is this productive!?
        self.sendStop(self.write)
        if self.m_notificationDesc.isValid() and self.m_service is not None:
            self.m_service.writeDescriptor(self.m_notificationDesc,self.DISABLE_NOTIFICATION_VALUE)
            self.onDeviceDisconnected()
        else:
            if self.m_control is not None:
                self.m_control.disconnectFromDevice()

    def scanDevices(self):
        _log.debug("scanDevices()")
        self.m_device = None
        self.m_deviceDiscoveryAgent.start(
            QtBluetooth.QBluetoothDeviceDiscoveryAgent.DiscoveryMethod(
                self.QBluetoothDeviceDiscoveryAgent_LowEnergyMethod))


def main():
    import sys
    app = QtCore.QCoreApplication(sys.argv)
    from artisanlib.acaia import AcaiaBLE
    acaia = AcaiaBLE()
    ble = BleInterface(
        [(acaia.SERVICE_UUID_LEGACY,
            [acaia.CHAR_UUID_LEGACY]),
         (acaia.SERVICE_UUID,
            [
                acaia.CHAR_UUID, 
                acaia.CHAR_UUID_WRITE
            ])],
        acaia.processData,
        acaia.sendHeartbeat,
        acaia.sendStop,
        acaia.reset,
        [
            acaia.DEVICE_NAME_LUNAR, 
            acaia.DEVICE_NAME_PEARL, 
            acaia.DEVICE_NAME_PEARL2021,
            acaia.DEVICE_NAME_PEARLS,
            acaia.DEVICE_NAME_OTHERS
        ])
    ble.scanDevices()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()