#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    #signals
    statusInfoChanged = QtCore.pyqtSignal(str , bool)
    dataReceived = QtCore.pyqtSignal(QtCore.QByteArray)
    connectedChanged = QtCore.pyqtSignal(bool)
    servicesChanged=QtCore.pyqtSignal(list)
    currentServiceChanged = QtCore.pyqtSignal(int)
    weightChanged=QtCore.pyqtSignal(float)
    deviceDisconnected=QtCore.pyqtSignal()
    
    def __init__(self, service_uuid, char_uuid, processData):
        super().__init__()
        self.SERVICE_UUID = QtBluetooth.QBluetoothUuid(service_uuid)
        self.CHAR_UUID = QtBluetooth.QBluetoothUuid(char_uuid)
        self.processData = processData
        
        self.m_deviceDiscoveryAgent = QtBluetooth.QBluetoothDeviceDiscoveryAgent()
        self.m_notificationDesc = QtBluetooth.QLowEnergyDescriptor()
        self.m_control = None
        #self.m_servicesUuid = QtBluetooth.QBluetoothUuid()
        self.m_servicesUuid = []
        self.m_service = QtBluetooth.QLowEnergyService
        self.m_readCharacteristic = QtBluetooth.QLowEnergyCharacteristic()
        self.m_writeCharacteristic = QtBluetooth.QLowEnergyCharacteristic()
        self.m_writemode = QtBluetooth.QLowEnergyService.WriteMode()
        
        self.m_device = None # bound to the device if discovered
        self.m_services = []
        self.m_currentService = None
        self.m_connected = False
        self.m_readTimer = None

        self.m_deviceDiscoveryAgent.setLowEnergyDiscoveryTimeout(500)
        self.m_deviceDiscoveryAgent.deviceDiscovered.connect(self.addDevice)
        self.m_deviceDiscoveryAgent.error.connect(self.onDeviceScanError)
        self.m_deviceDiscoveryAgent.finished.connect(self.onScanFinished)
        self.m_deviceDiscoveryAgent.canceled.connect(self.onScanFinished)
        self.dataReceived.connect(self.printDataReceived)

    def printDataReceived(self,data=QtCore.QByteArray):
#        print("received data:{data}".format(data =data))
        res = self.processData(self.write, data)
        if res is not None:
            self.weightChanged.emit(res)

    def update_connected(self,connected=bool):
        if connected != self.m_connected:
            self.m_connected = connected
            self.connectedChanged.emit(connected)

    def setCurrentService(self,currentService = int):
        if self.m_currentService == currentService:
            return
        self.update_currentService(currentService)
        self.m_currentService = currentService
        self.currentServiceChanged.emit(currentService)

    def scanDevices(self):
        self.m_device = None
        self.m_deviceDiscoveryAgent.start(QtBluetooth.QBluetoothDeviceDiscoveryAgent.DiscoveryMethod(2))
#        print("Scanning for devices...")

    def read(self):
        if(self.m_service and self.m_readCharacteristic.isValid()):
            self.m_service.readCharacteristic(self.m_readCharacteristic)
        
    def write(self,data=bytearray()):
#        print("BLEInterface write :{datawrite}".format(datawrite=data))
        if(self.m_service and self.m_writeCharacteristic.isValid()):
            if(len(data) > 20):
                sentBytes = 0
                while sentBytes < len(data):
                    self.m_service.writeCharacteristic(self.m_writeCharacteristic,data[sentBytes:sentBytes + 20],self.m_writemode)
                    sentBytes+=20
                    if self.m_writemode == QtBluetooth.QLowEnergyService.WriteWithResponse:
                        pass
                        if self.m_service.error() != QtBluetooth.QLowEnergyService.NoError:
                            return
            else:
                self.m_service.writeCharacteristic(self.m_writeCharacteristic,data,self.m_writemode)
    
    def deviceHasService(self,device,service_uuid):
        if device is None:
            return False
        else:
            services = device.serviceUuids()
            return services and len(services)>0 and service_uuid in services[0]
        
    def addDevice(self, device):
        if device.coreConfigurations() & QtBluetooth.QBluetoothDeviceInfo.LowEnergyCoreConfiguration:
#            print("Discovered LE Device name: {name} ,Address: {address} ".format(name=device.name(),address=device.address().toString()))
            m_device = QtBluetooth.QBluetoothDeviceInfo(device)
            if self.deviceHasService(m_device,self.SERVICE_UUID):
                # we found our device and stop scanning
                self.m_device = m_device
                self.m_deviceDiscoveryAgent.stop()
#            else:
#                print("Low Energy device found. Scanning more...")

    def onScanFinished(self):
#        print("Scan finished!")
        if self.m_device is None:
#            print("Can't find any BLE device")
            self.deviceDisconnected.emit()
            return
        else:
            self.connectCurrentDevice()
    
    def onDeviceScanError(self,error):
        pass
#        if error == QtBluetooth.QBluetoothDeviceDiscoveryAgent.PoweredOffError:
#            print("The Bluetooth adaptor is powered off power it on before discovery")
#        elif error == QtBluetooth.QBluetoothDeviceDiscoveryAgent.InputOutputError:
#            print("Writing or reading from the device resulted in an error")
#        else:
#            print("An unknown error has occurred")

    def connectCurrentDevice(self):
        if self.m_device is None:
            self.deviceDisconnected.emit()
            return
        if self.m_control:
            self.m_control.disconnectFromDevice()
            self.m_control = None
        self.m_control = QtBluetooth.QLowEnergyController(self.m_device)
        self.m_control.serviceDiscovered.connect(self.onServiceDiscovered)
        self.m_control.discoveryFinished.connect(self.onServiceScanDone)
        self.m_control.error.connect(self.onControllerError)
        self.m_control.connected.connect(self.onDeviceConnected)
        self.m_control.disconnected.connect(self.onDeviceDisconnected)
        self.m_control.connectToDevice()
    
    def onDeviceConnected(self):
        self.m_servicesUuid.clear()
        self.m_services.clear()
        self.m_currentService = None
        self.servicesChanged.emit(self.m_services)
        self.m_control.discoverServices()

    def onDeviceDisconnected(self):
        self.update_connected(False)
        self.statusInfoChanged.emit("Device disconnected",False)
#        print("Remote device disconnected")
        self.deviceDisconnected.emit()
       
    def onServiceDiscovered(self,_=QtBluetooth.QBluetoothUuid()):
        self.statusInfoChanged.emit("Service discovered. Waiting for service scan to be done...", True)

    def onServiceScanDone(self):
        self.m_servicesUuid = self.m_control.services()
        if len(self.m_servicesUuid)==0:
            self.statusInfoChanged.emit("Can't find any services.", True)
#            print("Can't find any services.")
        else:
            self.m_services.clear()
            for uuid in self.m_servicesUuid:
                self.m_services.append(uuid.toString())
            self.servicesChanged.emit(self.m_services)
            self.m_currentService = -1 #to force call update_currentService(once)
            self.setCurrentService(0)
            self.statusInfoChanged.emit("All services discovered.", True)
#            print("All services discovered.")
            
            pos = None
            for i in range(len(self.m_servicesUuid)):
#                print(i,self.m_servicesUuid[i])
                if self.SERVICE_UUID == self.m_servicesUuid[i]:
                    pos = i
                    break
            if pos is None:
                pass
#                print("service characteristic not found")
            else:
                self.setCurrentService(pos)

    def disconnectDevice(self):
        if self.m_readTimer is not None:
            self.m_readTimer.deleteLater()
        self.m_readTimer=None
        if self.m_device is None:
            return
        if self.m_notificationDesc.isValid() and self.m_service:
            self.m_service.writeDescriptor(self.m_notificationDesc,bytearray([0,0]))
        self.m_control.disconnectFromDevice()
        self.m_service = None

    def onControllerError(self,_=QtBluetooth.QLowEnergyController.error):
        self.statusInfoChanged.emit("Cannot connect to remote device.", False)
#        print("Controller Error")

    def onCharacteristicChanged(self,_=QtBluetooth.QLowEnergyCharacteristic,value=QtCore.QByteArray):
#        print("Characteristic Changed {values}".format(values=value))
        self.dataReceived.emit(value)

    def onCharacteristicWrite(self,c=QtBluetooth.QLowEnergyCharacteristic,value=QtCore.QByteArray):
#        print("characteristic Written: {values}".format(values=value))
        pass

    def onCharacteristicRead(self,_=QtBluetooth.QLowEnergyCharacteristic,value=QtCore.QByteArray):
#        print("Characteristic Read:  {values}".format(values=value))
        self.dataReceived.emit(value)

    def update_currentService(self,indx=int):
        self.m_service = None
        if indx>=0 and len(self.m_servicesUuid)>indx:
            self.m_service = self.m_control.createServiceObject(self.m_servicesUuid[indx])
        if not self.m_service:
            self.statusInfoChanged.emit("Service not found.", False)
#            print("Service not found.")
            self.deviceDisconnected.emit()
            return
        self.m_service.stateChanged.connect(self.onServiceStateChanged)
        self.m_service.characteristicChanged.connect(self.onCharacteristicChanged)
        self.m_service.characteristicRead.connect(self.onCharacteristicRead)
        self.m_service.characteristicWritten.connect(self.onCharacteristicWrite)
        self.m_service.error.connect(self.serviceError)
        if self.m_service.state() == QtBluetooth.QLowEnergyService.DiscoveryRequired:
            self.statusInfoChanged.emit("Connecting to service...",True)
#            print("Connecting to service... gatt:{gatt}".format(gatt=self.m_service.serviceUuid()))
            self.m_service.discoverDetails()
        else:
            self.searchCharacteristic()

    def searchCharacteristic(self):
#        print("searchCharacteristic")
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
                    if c.properties() & QtBluetooth.QLowEnergyCharacteristic.Read:
                        self.m_readCharacteristic=c
                        if not self.m_readTimer:
                            self.m_readTimer=QtCore.QTimer()
                            self.m_readTimer.timeout.connect(self.read)
                            self.m_readTimer.start(3000)
                    self.m_notificationDesc = c.descriptor(QtBluetooth.QBluetoothUuid(0x2902))
                    #print(QtBluetooth.QBluetoothUuid(0x2902).toString())
                    if self.m_notificationDesc.isValid():
                        #print("notificationCharacteristic")
                        #print(bytearray([1,0]))
                        self.m_service.writeDescriptor(self.m_notificationDesc,bytearray([1,0]))

    def onServiceStateChanged(self,s=QtBluetooth.QLowEnergyService.ServiceState):
#        print('service state changed , state: {state}'.format(state=s) )
        if s == QtBluetooth.QLowEnergyService.ServiceDiscovered:
            self.searchCharacteristic()

    def serviceError(self,e=QtBluetooth.QLowEnergyService.ServiceError):
#        print("Service error: {error}".format(error = e))
        pass
