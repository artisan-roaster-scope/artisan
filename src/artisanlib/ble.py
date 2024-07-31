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
# Marko Luther, 2023


from enum import Enum
import logging
from typing import Final, Optional, Tuple, List, Callable, Any, Type

try:
    from PyQt6 import QtCore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6 import QtBluetooth # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5 import QtCore # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5 import QtBluetooth # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


_log: Final[logging.Logger] = logging.getLogger(__name__)

UUID = str

class BLE_CHAR_TYPE(Enum):
    BLE_CHAR_NOTIFY = 'BLE_CHAR_NOTIFY'
    BLE_CHAR_WRITE = 'BLE_CHAR_WRITE'
    BLE_CHAR_NOTIFY_WRITE = 'BLE_CHAR_NOTIFY_WRITE'


class BleSDK(QtCore.QObject): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class ()
    weightChanged = QtCore.pyqtSignal(float)
    batteryChanged = QtCore.pyqtSignal(int)
    deviceDisconnected = QtCore.pyqtSignal()
    dataReceived = QtCore.pyqtSignal(bytes)

    # the uuid_service_char_tuples is a list of tuples of the form (service_uuid, char_uuid)
    # with service_uuid the services to connect to and char_uuid the characteristic uuid we register for write
    # at this service
    # if device_names are given, connections ar only made to devices with (partial-)matching names (fast)
    # if device_names are not given, connections are made to every discovered device with the required UUIDs (slow)
    # connected is called on successful connect
    # stop is called on disconnect
    # sendHeartbeat is called every two seconds while connected
    def __init__(self,
                uuid_service_char_tuples:List[Tuple[UUID, List[Tuple[UUID, BLE_CHAR_TYPE]]]],
                processData : Callable[[Callable[[Optional[bytes]], None], bytes], Tuple[Optional[float], Optional[int]]],
                sendHeartbeat : Optional[Callable[[Callable[[Optional[bytes]],None]], None]] = None,
                sendStop : Optional[Callable[[Callable[[Optional[bytes]],None]], None]] = None,
                connected : Optional[Callable[[], None]] = None,
                device_names:Optional[List[str]] = None) -> None:
        super().__init__()

#        self.__managing_thread: Optional[QtCore.QThread] = None

        self.CHUNK_SIZE:Final[int] = 20

        cp = QtBluetooth.QLowEnergyConnectionParameters()
        _log.debug('max interval: %s', cp.maximumInterval())
        _log.debug('min interval: %s', cp.minimumInterval())
        _log.debug('supervisionTimeout: %s', cp.supervisionTimeout())
        _log.debug('latency: %s', cp.latency())

        self.device_names:Optional[List[str]] = device_names

        self.UUID_SERVICE_CHAR_TUPLES=[]
        for (uuid_servive, uuid_char_list) in uuid_service_char_tuples:
            for (uuid_char, ble_write_type) in uuid_char_list:
                self.UUID_SERVICE_CHAR_TUPLES.append((QtBluetooth.QBluetoothUuid(uuid_servive),(QtBluetooth.QBluetoothUuid(uuid_char),ble_write_type)) )

        self.service_uuid:Optional[QtBluetooth.QBluetoothUuid] = None
        self.char_uuid:List[Tuple[QtBluetooth.QBluetoothUuid, BLE_CHAR_TYPE]] = []

        self.processData: Callable[[Callable[[Optional[bytes]], None], bytes], Tuple[Optional[float], Optional[int]]] = processData
        self.sendHeartbeat: Optional[Callable[[Callable[[Optional[bytes]],None]], None]] = sendHeartbeat
        self.sendStop: Optional[Callable[[Callable[[Optional[bytes]],None]], None]] = sendStop
        self.connected: Optional[Callable[[], None]] = connected

        self.ENABLE_NOTIFICATION_VALUE:QtCore.QByteArray = QtCore.QByteArray.fromHex(b'0100') # OFF type: ignore
        self.DISABLE_NOTIFICATION_VALUE:QtCore.QByteArray = QtCore.QByteArray.fromHex(b'0000') # OFF type: ignore

        self.m_deviceDiscoveryAgent:QtBluetooth.QBluetoothDeviceDiscoveryAgent = QtBluetooth.QBluetoothDeviceDiscoveryAgent()
        self.m_deviceDiscoveryAgent.setLowEnergyDiscoveryTimeout(500)
        self.m_deviceDiscoveryAgent.deviceDiscovered.connect(self.addDevice)
        self.m_deviceDiscoveryAgent.errorOccurred.connect(self.scanError)
        self.m_deviceDiscoveryAgent.finished.connect(self.onScanFinished)
        self.m_deviceDiscoveryAgent.canceled.connect(self.onScanFinished)

        self.m_device:Optional[QtBluetooth.QBluetoothDeviceInfo] = None
        self.m_control:Optional[QtBluetooth.QLowEnergyController] = None
        self.m_service:Optional[QtBluetooth.QLowEnergyService] = None

        self.m_notificationDesc:QtBluetooth.QLowEnergyDescriptor = QtBluetooth.QLowEnergyDescriptor()
        self.m_readCharacteristic:QtBluetooth.QLowEnergyCharacteristic = QtBluetooth.QLowEnergyCharacteristic()
        self.m_writeCharacteristic:QtBluetooth.QLowEnergyCharacteristic = QtBluetooth.QLowEnergyCharacteristic()
        # plint: disable=maybe-no-member
        self.m_writemode:QtBluetooth.QLowEnergyService.WriteMode = QtBluetooth.QLowEnergyService.WriteMode.WriteWithoutResponse # was QtBluetooth.QLowEnergyService.WriteMode() => 0 in PyQt5, but fails on PyQt6

        self.m_connected:bool = False

        self.dataReceived.connect(self.dataReceivedProcessing)

#    def set_managing_thread(self, thread: QtCore.QThread) -> None:
#        self.__managing_thread = thread

    def stop_managing_thread(self) -> None:
        pass
#        if self.__managing_thread:
#            self.__managing_thread.quit()
#            self.__managing_thread.wait()
#            self.__managing_thread = None
#        _log.debug('managing_thread stopped: %s', self.__managing_thread)

    def disconnectDiscovery(self) -> None:
        _log.debug('disconnectDiscovery()')
        self.m_deviceDiscoveryAgent.deviceDiscovered.disconnect()
        self.m_deviceDiscoveryAgent.errorOccurred.disconnect()
        self.m_deviceDiscoveryAgent.finished.disconnect()
        self.m_deviceDiscoveryAgent.canceled.disconnect()

    def removeDevice(self) -> None:
        self.m_device = None

    def removeControl(self) -> None:
        try:
            if self.m_control is not None:
                self.m_control.discoveryFinished.disconnect()
                self.m_control.connected.disconnect()
                self.m_control.disconnected.disconnect()
                self.m_control.disconnectFromDevice()
                self.m_control.deleteLater()
        except Exception: # pylint: disable=broad-except
            pass
        finally:
            self.m_control = None

    def removeService(self) -> None:
        try:
            self.service_uuid = None
            self.char_uuid = []
            if self.m_service is not None:
                self.m_service.stateChanged.disconnect()
                self.m_service.characteristicChanged.disconnect()
                self.m_service.characteristicRead.disconnect()
                self.m_service.errorOccurred.disconnect()
                self.m_service.descriptorWritten.disconnect()
                self.m_service.deleteLater()
        except Exception: # pylint: disable=broad-except
            pass
        finally:
            self.m_service = None

#--------

    @QtCore.pyqtSlot(bytes)
    def dataReceivedProcessing(self, data:Optional[bytes] = None) -> None:
#        _log.debug("data received: %s", data)
        if data is None:
            data = b''
        res_w, res_b = self.processData(self.write, data)
        if res_w is not None:
            self.weightChanged.emit(res_w)
        if res_b is not None:
            self.batteryChanged.emit(res_b)

    def write(self, data:Optional[bytes] = None) -> None:
        _log.debug('write data: %s', data)
        if data is None:
            data = b'' #bytearray()
        if (self.m_service and self.m_writeCharacteristic.isValid()):
            if len(data) > self.CHUNK_SIZE:
                sentBytes = 0
                while sentBytes < len(data):
                    self.m_service.writeCharacteristic(self.m_writeCharacteristic,data[sentBytes:sentBytes + self.CHUNK_SIZE],self.m_writemode) # OFF type: ignore # "bytearray" is incompatible with "QByteArray"
                    sentBytes += self.CHUNK_SIZE
#                    if self.m_writemode == QtBluetooth.QLowEnergyService.WriteMode.WriteWithResponse:
#                        pass
            else:
                self.m_service.writeCharacteristic(self.m_writeCharacteristic,data,self.m_writemode) # OFF type: ignore # "bytearray" is incompatible with "QByteArray"

    def update_connected(self,connected:bool) -> None:
        _log.debug('update_connected(%s)', connected)
        try:
            if connected != self.m_connected:
                self.m_connected = connected
    #            self.connectedChanged.emit(connected)
                if self.m_connected:
                    if self.m_device:
                        _log.info('connected to %s', self.m_device.name())
                    if self.connected is not None:
                        self.connected()
                elif self.m_device:
                    _log.info('disconnected from %s', self.m_device.name())
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    @QtCore.pyqtSlot()
    def heartbeat(self) -> None:
        if self.m_connected and self.sendHeartbeat is not None:
#            _log.debug("send heartbeat")
            self.sendHeartbeat(self.write)
            QtCore.QTimer.singleShot(2000, self.heartbeat)

    @QtCore.pyqtSlot('QLowEnergyDescriptor','QByteArray')
    def descriptorWrittenSlot(self, descriptor:QtBluetooth.QLowEnergyDescriptor, newValue:QtCore.QByteArray) -> None:
        if descriptor.isValid():
            if newValue == self.ENABLE_NOTIFICATION_VALUE:
                # notifications enabled
                self.heartbeat()
            elif self.m_control is not None and newValue == self.DISABLE_NOTIFICATION_VALUE:
                # notifications disabled
                self.m_control.disconnectFromDevice()

    def searchCharacteristic(self) -> None:
        # plint: disable=maybe-no-member
        _log.debug('searchCharacteristic()')
        try:
            if self.m_service:
                for c in self.m_service.characteristics():
                    if c.isValid():
                        for (uuid_char, ble_write_type) in self.char_uuid:
                            # we register write only for the given char_uuid associated to the service uuid we are connected to
                            if (c.uuid() == uuid_char and
                                    ble_write_type in (
                                        BLE_CHAR_TYPE.BLE_CHAR_NOTIFY_WRITE,
                                        BLE_CHAR_TYPE.BLE_CHAR_WRITE) and
                                ((c.properties() & QtBluetooth.QLowEnergyCharacteristic.PropertyType.WriteNoResponse) or
                                        (c.properties() & QtBluetooth.QLowEnergyCharacteristic.PropertyType.Write))):
                                self.m_writeCharacteristic = c
                                self.update_connected(True)
                                # plint: disable=maybe-no-member
                                if c.properties() & QtBluetooth.QLowEnergyCharacteristic.PropertyType.WriteNoResponse:
                                    self.m_writemode=QtBluetooth.QLowEnergyService.WriteMode.WriteWithoutResponse
                                else:
                                    self.m_writemode=QtBluetooth.QLowEnergyService.WriteMode.WriteWithResponse
                            if (c.uuid() == uuid_char and
                                    ble_write_type in (
                                        BLE_CHAR_TYPE.BLE_CHAR_NOTIFY_WRITE,
                                        BLE_CHAR_TYPE.BLE_CHAR_NOTIFY)):

                                # remove this hack once PyQt6.1 is fixed:
                                # following line fails on PyQt6.1 as the constructor for QBluetoothUuid(DescriptorType) is missing
                                self.m_notificationDesc = c.descriptor(QtBluetooth.QBluetoothUuid(QtBluetooth.QBluetoothUuid.DescriptorType.ClientCharacteristicConfiguration))
                                # thus we use the string constructor for now
    #                            self.m_notificationDesc = c.descriptor(QtBluetooth.QBluetoothUuid('{00002902-0000-1000-8000-00805f9b34fb}'))

                                if self.m_notificationDesc.isValid():
                                    self.m_service.descriptorWritten.connect(self.descriptorWrittenSlot)
                                    self.m_service.writeDescriptor(self.m_notificationDesc,self.ENABLE_NOTIFICATION_VALUE)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    @QtCore.pyqtSlot('QLowEnergyCharacteristic','QByteArray')
    def onCharacteristicChanged(self,_:QtBluetooth.QLowEnergyCharacteristic, value:QtCore.QByteArray) -> None:
#        print("Characteristic Changed {values}".format(values=value))
        self.dataReceived.emit(value.data()) # convert QByteArray to Python byte array

    @QtCore.pyqtSlot('QLowEnergyCharacteristic','QByteArray')
    def onCharacteristicRead(self,_:QtBluetooth.QLowEnergyCharacteristic, value:QtCore.QByteArray) -> None:
#        print("Characteristic Read:  {values}".format(values=value))
        pass

    # a simplified version of the above
    @QtCore.pyqtSlot('QLowEnergyService::ServiceState')
    def onServiceStateChanged(self, s:QtBluetooth.QLowEnergyService.ServiceState) -> None:
        _log.debug('onServiceStateChanged(%s)',s)
        # pylint: disable=maybe-no-member
        if s == QtBluetooth.QLowEnergyService.ServiceState.DiscoveryRequired and self.m_service is not None:
            self.m_service.discoverDetails()
        elif s == QtBluetooth.QLowEnergyService.ServiceState.ServiceDiscovered:
            self.searchCharacteristic()
#        elif s == QtBluetooth.QLowEnergyService.ServiceState.InvalidService:
#            # A service can become invalid when it looses the connection to the underlying device.
#            # Even though the connection may be lost it retains its last information.
#            # An invalid service cannot become valid anymore even if the connection to the device is re-established
#            pass
#        elif s == QtBluetooth.QLowEnergyService.ServiceState.RemoteServiceDiscovering:
#            pass
#        elif s == QtBluetooth.QLowEnergyService.ServiceState.LocalService:
#            pass

    @QtCore.pyqtSlot('QLowEnergyService::ServiceError')
    def serviceError(self, error:QtBluetooth.QLowEnergyService.ServiceError) -> None:
        _log.debug('serviceError: %s', error)
        if self.m_service is not None:
            _log.debug('onSeviceErrorOccurred: %s', self.m_service.error())
        self.removeService()
        self.update_connected(False)

    @QtCore.pyqtSlot()
    def onServiceScanDone(self) -> None:
        _log.debug('onServiceScanDone()')
        if self.m_control is not None:
            for uuid in self.m_control.services():
                for (uuid_servive, (uuid_char, ble_write_type)) in self.UUID_SERVICE_CHAR_TUPLES:
                    if uuid_servive is not None and uuid_servive == uuid:
                        _log.debug('createServiceObject(%s)', uuid.toString())
                        self.service_uuid = uuid_servive
                        self.char_uuid.append((uuid_char, ble_write_type))
                        if self.m_control is not None:
                            self.m_service = self.m_control.createServiceObject(uuid)
                            if self.m_service is not None:
                                self.m_service.stateChanged.connect(self.onServiceStateChanged, type=QtCore.Qt.ConnectionType.QueuedConnection)  # type: ignore
                                self.m_service.characteristicChanged.connect(self.onCharacteristicChanged, type=QtCore.Qt.ConnectionType.QueuedConnection)  # type: ignore
                                self.m_service.characteristicRead.connect(self.onCharacteristicRead, type=QtCore.Qt.ConnectionType.QueuedConnection)  # type: ignore
                                self.m_service.errorOccurred.connect(self.serviceError, type=QtCore.Qt.ConnectionType.QueuedConnection)  # type: ignore
        # pylint: disable=maybe-no-member
        if self.m_service is not None and self.m_service.state() == QtBluetooth.QLowEnergyService.ServiceState.DiscoveryRequired:
            self.m_service.discoverDetails() # this is required on PyQt 5.2.2 as onServiceStateChanged() is not called automatically
        else:
            self.searchCharacteristic()

    @QtCore.pyqtSlot()
    def onDeviceConnected(self) -> None:
        _log.debug('onDeviceConnected')
        if self.m_control is not None:
            self.m_control.discoverServices()

    @QtCore.pyqtSlot()
    def onDeviceDisconnected(self) -> None:
        _log.debug('onDeviceDisconnected')
        self.update_connected(False)
        self.removeService()
        self.removeControl()
#        self.removeDevice() # we keep the current device and only remove it on next scanDevice()
#  this allows to reconnect using connectCurrentDevice()
        self.deviceDisconnected.emit()

    def connectCurrentDevice(self) -> None:
        if self.m_device is not None:
            _log.debug('connectCurrentDevice: %s', self.m_device.name())
            self.m_control = QtBluetooth.QLowEnergyController.createCentral(self.m_device)
            if self.m_control is not None:
                # QueuedConnection required in the following for Windows. See: https://forum.qt.io/topic/109558/bluetooth-low-energy-scanner-discover-service-details/9
                self.m_control.discoveryFinished.connect(self.onServiceScanDone, type=QtCore.Qt.ConnectionType.QueuedConnection) # type: ignore
                self.m_control.connected.connect(self.onDeviceConnected, type=QtCore.Qt.ConnectionType.QueuedConnection) # type: ignore
                self.m_control.disconnected.connect(self.onDeviceDisconnected, type=QtCore.Qt.ConnectionType.QueuedConnection) # type: ignore
                self.m_control.connectToDevice()
        else:
            self.deviceDisconnected.emit()

    @QtCore.pyqtSlot('QBluetoothDeviceDiscoveryAgent::Error')
    def scanError(self, error:QtBluetooth.QBluetoothDeviceDiscoveryAgent.Error) -> None: # pylint: disable=no-self-use
        _log.debug('scanError: %s', error)

    @QtCore.pyqtSlot()
    def onScanFinished(self) -> None:
        _log.debug('onScanFinished()')
        if self.m_device is None:
            self.onDeviceDisconnected()
        else:
            self.connectCurrentDevice()

    @staticmethod
    def deviceHasService(device:QtBluetooth.QBluetoothDeviceInfo, service_uuid:QtBluetooth.QBluetoothUuid) -> bool:
        try:
            services = device.serviceUuids()
            has_service:bool = services is not None and len(services)>0 and service_uuid in services
            if has_service:
                _log.debug('deviceHasService(%s, %s)', device.name(), service_uuid.toString())
            return has_service
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
            return False

    @QtCore.pyqtSlot('QBluetoothDeviceInfo')
    def addDevice(self, device:QtBluetooth.QBluetoothDeviceInfo) -> None:
        # pylint: disable=maybe-no-member
        if self.m_device is None and device.coreConfigurations() & QtBluetooth.QBluetoothDeviceInfo.CoreConfiguration.LowEnergyCoreConfiguration:
            # a BLE device
            _log.debug('discovered BLE device "%s" (%s))', device.name(), device.deviceUuid().toString())
            m_device = QtBluetooth.QBluetoothDeviceInfo(device)
            if self.device_names is None:
                _log.debug('check device for matching services')
                for (uuid_service, _) in self.UUID_SERVICE_CHAR_TUPLES:
                    if self.deviceHasService(m_device, uuid_service):
                        _log.debug('device service match')
                        self.m_device = m_device
                        break
            elif any((dn and dn in m_device.name()) for dn in self.device_names):
                _log.debug('device name match')
                self.m_device = m_device
            if self.m_device is not None:
                # we found our device and stop scanning
                self.m_deviceDiscoveryAgent.stop()
                _log.debug("discovered LE Device name: '%s',  device: %s, rssi: %s", self.m_device.name(), self.m_device.deviceUuid().toString(), self.m_device.rssi())
            else:
                _log.debug('no matching service found')

#----------------

    # disconnect from all signals
    def disconnectDevice(self) -> None:
        _log.debug('disconnectDevice()')
        self.update_connected(False) # is this productive!?
        if self.sendStop is not None:
            self.sendStop(self.write)
        if self.m_notificationDesc.isValid() and self.m_service is not None:
            self.m_service.writeDescriptor(self.m_notificationDesc,self.DISABLE_NOTIFICATION_VALUE)
        self.dataReceived.disconnect()
        self.disconnectDiscovery()
        self.onDeviceDisconnected()

    @QtCore.pyqtSlot()
    def scanDevices(self) -> None:
        _log.debug('scanDevices()')
        if self.m_device is not None:
            _log.debug('avoid scanning and reconnect previously discovered device')
            self.connectCurrentDevice()
        else:
            self.m_device = None
            try:
                # fails on PyQt5, works on PyQt6:
                # pylint: disable=maybe-no-member
                self.m_deviceDiscoveryAgent.start(QtBluetooth.QBluetoothDeviceDiscoveryAgent.DiscoveryMethod.LowEnergyMethod)
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
                # works on PyQt5, fails on PyQt6:
                QBluetoothDeviceDiscoveryAgent_LowEnergyMethod = 2
                self.m_deviceDiscoveryAgent.start(
                    QtBluetooth.QBluetoothDeviceDiscoveryAgent.DiscoveryMethod(
                        QBluetoothDeviceDiscoveryAgent_LowEnergyMethod))

class BleInterface(BleSDK):
    """Creates a BKE SDK instance # disabled: and runs it in its own QThread
    """

    def __new__(cls:Type[Any], # type: ignore[misc]
                uuid_service_char_tuples:List[Tuple[UUID, List[Tuple[UUID, BLE_CHAR_TYPE]]]],
                processData : Callable[[Callable[[Optional[bytes]], None], bytes], Tuple[Optional[float], Optional[int]]],
                *args:Any, **kwargs:Any) -> BleSDK:
#        __instance = BleSDK(uuid_service_char_tuples, processData, *args, **kwargs)
#        managing_thread_reference = QtCore.QThread()
#        managing_thread_reference.finished.connect(managing_thread_reference.deleteLater)
#        __instance.set_managing_thread(managing_thread_reference)
#        __instance.moveToThread(managing_thread_reference)
#        managing_thread_reference.start()
#        return __instance
        return BleSDK(uuid_service_char_tuples, processData, *args, **kwargs)


def main() -> None:
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
            acaia.DEVICE_NAME_LUNAR2021,
            acaia.DEVICE_NAME_PYXIS
        ])
    ble.scanDevices()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
