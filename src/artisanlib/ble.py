#!/usr/bin/env python3

# ABOUT
# BLE support for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2019

from PyQt5 import QtCore
from PyQt5 import QtBluetooth


class BleInterface(QtCore.QObject):
    weightChanged=QtCore.pyqtSignal(float)
    batteryChanged=QtCore.pyqtSignal(int)
    deviceDisconnected=QtCore.pyqtSignal()
    dataReceived = QtCore.pyqtSignal(QtCore.QByteArray)

    def __init__(self,service_uuid, char_uuid, processData, sendHeartbeat, sendStop, reset):
        super().__init__()
        
#        cp = QtBluetooth.QLowEnergyConnectionParameters()
#        print("max interval",cp.maximumInterval())
#        print("min interval",cp.minimumInterval())
#        print("supervisionTimeout",cp.supervisionTimeout())
#        print("latency()",cp.latency())
        
        self.SERVICE_UUID = QtBluetooth.QBluetoothUuid(service_uuid)
        self.CHAR_UUID = QtBluetooth.QBluetoothUuid(char_uuid)
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
        
        self.dataReceived.connect(self.printDataReceived)
        

    def removeDevice(self):
        self.m_device = None
    
    def removeControl(self):
        try:
            self.m_control.discoveryFinished.disconnect()
            self.m_control.connected.disconnect()
            self.m_control.disconnected.disconnect()
            self.m_control.deleteLater()
        except:
            pass
        finally:
            self.m_control = None
            
    def removeService(self):
        try:
            self.m_service.stateChanged.disconnect()
            self.m_service.characteristicChanged.disconnect()
            self.m_service.characteristicRead.disconnect()
            self.m_service.deleteLater()
        except:
            pass
        finally:
            self.m_service = None

#--------

    @QtCore.pyqtSlot("QByteArray")
    def printDataReceived(self,data=QtCore.QByteArray):
#        print("received data:{data}".format(data =data))
        res_w, res_b = self.processData(self.write, data)
        if res_w is not None:
            self.weightChanged.emit(res_w)
        if res_b is not None:
            self.batteryChanged.emit(res_b)

    def read(self):
        if(self.m_service and self.m_readCharacteristic.isValid()):
            self.m_service.readCharacteristic(self.m_readCharacteristic)
        
    def write(self,data=bytearray()):
#        print("BLEInterface write :{datawrite}".format(datawrite=data))
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
        if connected != self.m_connected:
            self.m_connected = connected
#            self.connectedChanged.emit(connected)
            if self.m_connected:
                self.reset()

    def heartbeat(self):
        if self.m_connected:
            self.sendHeartbeat(self.write)
            QtCore.QTimer.singleShot(2000,lambda : self.heartbeat())

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
        if self.m_service:
            for c in self.m_service.characteristics():
                if c.isValid():
                    if c.properties() & QtBluetooth.QLowEnergyCharacteristic.WriteNoResponse or c.properties() & QtBluetooth.QLowEnergyCharacteristic.Write:
                        self.m_writeCharacteristic = c
                        self.update_connected(True)
                        if c.properties() & QtBluetooth.QLowEnergyCharacteristic.WriteNoResponse:
                            self.m_writemode=QtBluetooth.QLowEnergyService.WriteWithoutResponse
                        else:
                            self.m_writemode=QtBluetooth.QLowEnergyService.WriteWithResponse
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
#        print('service state changed , state: {state}'.format(state=s) )
        if s == QtBluetooth.QLowEnergyService.ServiceDiscovered:
            self.searchCharacteristic()

    @QtCore.pyqtSlot()
    def onServiceScanDone(self):
        for uuid in self.m_control.services():
            if self.SERVICE_UUID == uuid:
                self.m_service = self.m_control.createServiceObject(uuid)
                self.m_service.stateChanged.connect(self.onServiceStateChanged)
                self.m_service.characteristicChanged.connect(self.onCharacteristicChanged)
                self.m_service.characteristicRead.connect(self.onCharacteristicRead)
                break
        if self.m_service is not None and self.m_service.state() == QtBluetooth.QLowEnergyService.DiscoveryRequired:
            self.m_service.discoverDetails()
        else:
            self.searchCharacteristic()
                
    @QtCore.pyqtSlot()
    def onDeviceConnected(self):
        self.m_control.discoverServices()

    @QtCore.pyqtSlot()
    def onDeviceDisconnected(self):
        self.update_connected(False)
        self.removeService()
        self.removeControl()
        self.removeDevice()
        self.deviceDisconnected.emit()

    def connectCurrentDevice(self):
        if self.m_device is not None:
            self.m_control = QtBluetooth.QLowEnergyController(self.m_device)
            self.m_control.discoveryFinished.connect(self.onServiceScanDone)
            self.m_control.connected.connect(self.onDeviceConnected)
            self.m_control.disconnected.connect(self.onDeviceDisconnected)
            self.m_control.connectToDevice()
        else:
            self.deviceDisconnected.emit()
        
    @QtCore.pyqtSlot()
    def onScanFinished(self):
        if self.m_device is None:
            self.onDeviceDisconnected()
        else:
            self.connectCurrentDevice()

    def deviceHasService(self,device,service_uuid):
        if device is None:
            return False
        else:
            services = device.serviceUuids()
            return services and len(services)>0 and service_uuid in services[0]

    @QtCore.pyqtSlot("QBluetoothDeviceInfo")
    def addDevice(self, device):
        if self.m_device is None and device.coreConfigurations() & QtBluetooth.QBluetoothDeviceInfo.LowEnergyCoreConfiguration:
#            print("Discovered LE Device name: {name} ,Address: {address} ".format(name=device.name(),address=device.address().toString()))
            m_device = QtBluetooth.QBluetoothDeviceInfo(device)
            if self.deviceHasService(m_device,self.SERVICE_UUID):
                self.m_device = m_device
                # we found our device and stop scanning
                self.m_deviceDiscoveryAgent.stop()

#----------------

    def disconnectDevice(self):
        self.update_connected(False)
        self.sendStop(self.write)
        if self.m_notificationDesc.isValid() and self.m_service is not None:
            self.m_service.writeDescriptor(self.m_notificationDesc,self.DISABLE_NOTIFICATION_VALUE)
            self.onDeviceDisconnected()
        else:
            if self.m_control is not None:
                self.m_control.disconnectFromDevice()

    def scanDevices(self):
        self.m_device = None
        self.m_deviceDiscoveryAgent.start(
            QtBluetooth.QBluetoothDeviceDiscoveryAgent.DiscoveryMethod(
                self.QBluetoothDeviceDiscoveryAgent_LowEnergyMethod))


def main():
    import sys
    app = QtCore.QCoreApplication(sys.argv)
    from artisanlib.acaia import AcaiaBLE
    acaia = AcaiaBLE()
    ble = BleInterface(acaia.SERVICE_UUID,acaia.CHAR_UUID,acaia.processData,acaia.sendHeartbeat,acaia.sendStop,acaia.reset)
    ble.scanDevices()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()