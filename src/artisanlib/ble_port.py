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
# Marko Luther, 2024

import asyncio
import logging
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakCharacteristicNotFoundError

try:
    from PyQt6.QtCore import QObject # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QObject # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.async_comm import AsyncLoopThread

from typing import Optional, Callable, Union, Dict, List, Set, Tuple, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice # pylint: disable=unused-import
    from bleak.backends.scanner import AdvertisementData # pylint: disable=unused-import
    from bleak.backends.characteristic import BleakGATTCharacteristic  # pylint: disable=unused-import

_log = logging.getLogger(__name__)



## the interface to the BLEAK lib providing only basic services, but ensures that BLEAK runs in a separate thread/asyncloop and
## prevents overlapping scan-connects that can lead to crashes
class BLE:

    _scan_and_connect_lock: asyncio.Lock = asyncio.Lock()
    _terminate_scan_event = asyncio.Event()
    _asyncLoopThread:Optional[AsyncLoopThread] = None

    def __del__(self) -> None:
        self.close()

    # close() needs to be called on terminating the app to get rid of the singular thread/asyncloop running the bleak scan and connect
    def close(self) -> None:
        if hasattr(self, '_asyncLoopThread') and self._asyncLoopThread is not None:
            del self._asyncLoopThread
            self._asyncLoopThread = None

    def terminate_scan(self) -> None:
        self._terminate_scan_event.set()

    # returns True if the given device name matches with the devices name or the local_name of the advertisement
    # returns True also in case the local_name is None, but the given service_uuid is within ad.service_uuids
    @staticmethod
    def name_match(bd:'BLEDevice', ad:'AdvertisementData', device_name:str, case_sensitive:bool, service_uuid:Optional[str]) -> bool:
        return ((bd.name is not None and (bd.name.startswith(device_name) if
                    case_sensitive else bd.name.casefold().startswith(device_name.casefold()))) or
                (ad.local_name is not None and (ad.local_name.startswith(device_name) if
                    case_sensitive else ad.local_name.casefold().startswith(device_name.casefold()))) or
                (ad.local_name is None and service_uuid is not None and
                    service_uuid.casefold() in (uuid.casefold() for uuid in ad.service_uuids)))

    # matches the discovered BLEDevice and AdvertisementData
    # returns True on success and False otherwise, as well as the service_uuid str of the matching device_description
    def description_match(self, bd:'BLEDevice', ad:'AdvertisementData',
            device_descriptions:Dict[Optional[str],Optional[Set[str]]], case_sensitive:bool) -> Tuple[bool, Optional[str]]:
        for service_uuid, device_names in device_descriptions.items():
            if device_names is None or any(self.name_match(bd,ad,device_name,case_sensitive, service_uuid) for device_name in device_names):
                return True, service_uuid
        return False, None


    # returns discovered_bd and service_uuid on success, or None
    async def _scan(self,
            device_descriptions:Dict[Optional[str],Optional[Set[str]]],
            blacklist:Set[str],
            case_sensitive:bool,
            scan_timeout:float,
            address:Optional[str]) -> 'Tuple[Optional[BLEDevice], Optional[str]]':
        try:
            async with asyncio.timeout(scan_timeout): # type:ignore[attr-defined]
                async with BleakScanner() as scanner:
                    self._terminate_scan_event.clear()
                    async for bd, ad in scanner.advertisement_data():
                        if self._terminate_scan_event.is_set():
                            return None, None
#                        _log.debug("device %s, (%s): %s", bd.name, ad.local_name, ad.service_uuids)
                        if bd.address not in blacklist and (address is None or bd.address == address):
                            res:bool
                            res_service_uuid:Optional[str]
                            res, res_service_uuid = self.description_match(bd,ad,device_descriptions,case_sensitive)
                            if res:
                                _log.debug('BLE device match')
                                # we return the first discovered device that matches the given device descriptions
                                return bd, res_service_uuid
        except asyncio.TimeoutError:
            _log.debug('timeout on BLE scanning')
        return None, None

    # pylint: disable=too-many-positional-arguments
    async def _scan_and_connect(self,
                device_descriptions:Dict[Optional[str],Optional[Set[str]]],
                blacklist:Set[str], # client addresses to ignore
                case_sensitive:bool,
                disconnected_callback:Optional[Callable[[BleakClient], None]],
                scan_timeout:float, connect_timeout:float,
                address:Optional[str] = None # if given, connect only to the device with this ble address
                ) -> Tuple[Optional[BleakClient], Optional[str]]:
        async with self._scan_and_connect_lock:
            # the lock ensures that only one scan/connect operation is running at any time
            # as trying to establish a connection to two devices at the same time
            # can cause errors
            discovered_bd:Optional[BLEDevice] = None
            service_uuid:Optional[str] = None
            discovered_bd, service_uuid = await self._scan(device_descriptions, blacklist, case_sensitive, scan_timeout, address)
            if discovered_bd is None:
                return None, None
            client = BleakClient(
                        discovered_bd,
                        disconnected_callback=disconnected_callback,
                        service=([service_uuid] if service_uuid is not None else None),
                        timeout=connect_timeout)
            try:
                async with asyncio.timeout(connect_timeout): # type:ignore[attr-defined]
                    await client.connect()
            except asyncio.TimeoutError:
                _log.debug('timeout on connect')
                return None, None
            _log.debug('BLE client is_connected')
            return client, service_uuid

##
    def write(self, client:BleakClient, write_uuid:str, message:bytes, response:bool = False) -> None:
        if hasattr(self, '_asyncLoopThread') and self._asyncLoopThread is not None and client.is_connected:
            # NOTE: we don't wait for a result not to block the bleak write loop
            junk_size = 20
            for i in range(0, len(message), junk_size):
                # send message in junks of just 20 bytes (minimum BLE mtu size)
                asyncio.run_coroutine_threadsafe(
                    client.write_gatt_char(write_uuid, message[i:i+junk_size], response=response),
                    self._asyncLoopThread.loop)

    def read(self, client:BleakClient, read_uuid:str) -> Optional[bytes]:
        if hasattr(self, '_asyncLoopThread') and self._asyncLoopThread is not None and client.is_connected:
            fut = asyncio.run_coroutine_threadsafe(
                    client.read_gatt_char(read_uuid),
                    self._asyncLoopThread.loop)
            try:
                return bytes(fut.result())
            except Exception: # pylint: disable=broad-except
                #raise fut.exception() from e # type: ignore[misc]
                _log.error('exception in read: %s', fut.exception())
        return None

    def scan_and_connect(self,
            device_descriptions: Dict[Optional[str],Optional[Set[str]]],
            blacklist:Set[str], # list of client addresses to ignore as they don't offer the required service
            case_sensitive:bool=True,
            disconnected_callback:Optional[Callable[[BleakClient], None]] = None,
            scan_timeout:float=6,
            connect_timeout:float=6,
            address:Optional[str] = None # if given, connect only to the device with this ble address
            ) -> Tuple[Optional[BleakClient], Optional[str]]:
        if hasattr(self, '_asyncLoopThread') and self._asyncLoopThread is None:
            self._asyncLoopThread = AsyncLoopThread()
        assert self._asyncLoopThread is not None
        fut = asyncio.run_coroutine_threadsafe(
                self._scan_and_connect(
                    device_descriptions,
                    blacklist,
                    case_sensitive,
                    disconnected_callback,
                    scan_timeout,
                    connect_timeout,
                    address),
                self._asyncLoopThread.loop)
        try:
            return fut.result()
        except Exception: # pylint: disable=broad-except
            #raise fut.exception() from e # type: ignore[misc]
            _log.error('exception in scan_and_connect: %s', fut.exception())
            return None, None

    def disconnect_ble(self, client:'BleakClient') -> bool:
        if hasattr(self, '_asyncLoopThread') and self._asyncLoopThread is not None:
            # don't wait for completion not to block caller (note: ble device will not be discovered until fully disconnected)
            asyncio.run_coroutine_threadsafe(client.disconnect(), self._asyncLoopThread.loop)
        return False

    def start_notify(self, client:BleakClient, uuid:str, callback: 'Callable[[BleakGATTCharacteristic, bytearray], Union[None, Awaitable[None]]]') -> None:
        if hasattr(self, '_asyncLoopThread') and self._asyncLoopThread is not None and client.is_connected:
            fut = asyncio.run_coroutine_threadsafe(
                    client.start_notify(uuid, callback),
                    self._asyncLoopThread.loop)
            try:
                fut.result()
            except Exception:  # pylint: disable=broad-except
                #raise fut.exception() from e # type: ignore[misc]
                _log.error('exception in start_notify: %s', fut.exception())

    def stop_notify(self, client:'BleakClient', uuid:str) -> None:
        if hasattr(self, '_asyncLoopThread') and self._asyncLoopThread is not None and client.is_connected:
            fut = asyncio.run_coroutine_threadsafe(
                client.stop_notify(uuid),
                self._asyncLoopThread.loop)
            try:
                fut.result()
            except Exception:  # pylint: disable=broad-except
                #raise fut.exception() from e # type: ignore[misc]
                _log.error('exception in stop_notify: %s', fut.exception())

ble = BLE() # unique to module



#####



class ClientBLE(QObject): # pyright:ignore[reportGeneralTypeIssues] # error: Argument to class must be a base class

# NOTE: __slots__ are incompatible with multiple inheritance mixings in subclasses (e.g. with QObject)
#    __slots__ = [ '_running', '_async_loop_thread', '_ble_client', '_connected_service_uuid', '_disconnected_event',
#                    '_active_notification_uuids',
#                    '_device_descriptions', '_notifications', '_writers', '_readers', '_heartbeat_frequency',
#                    '_logging'  ]

    def __init__(self) -> None:
        super().__init__()
        # internals
        self._running:bool                                   = False           # if True we keep reconnecting
        self._async_loop_thread: Optional[AsyncLoopThread]   = None            # the asyncio AsyncLoopThread object
        self._ble_client:Optional[BleakClient]               = None
        self._connected_service_uuid:Optional[str]           = None            # set to the service UUID we are connected to
        self._disconnected_event:asyncio.Event               = asyncio.Event() # event set on disconnect
        self._active_notification_uuids:Set[str]             = set() # uuids of characteristics were notification are active

        # configuration
        self._device_descriptions:Dict[Optional[str],Optional[Set[str]]] = {}
        self._notifications:Dict[str, Callable[[BleakGATTCharacteristic, bytearray], None]] = {}
        self._writers:Dict[str, List[str]] = {} # associates a service UUID with a list of write characteristics
        self._readers:Dict[str, List[str]] = {} # associates a service UUID with a list of read characteristics
        self._heartbeat_frequency : float = 0 # heartbeat frequency in seconds; heartbeat ends if not >0
        self._logging = False  # if True device communication is logged


    ##

    def start_notifications(self) -> None:
        for notify_uuid, callback in self._notifications.items():
            if self._ble_client is not None and self._ble_client.is_connected and \
                    self._ble_client.services.get_characteristic(notify_uuid):
                try:
                    ble.start_notify(self._ble_client, notify_uuid, callback)
                    self._active_notification_uuids.add(notify_uuid)
                    _log.debug('notification on characteristic %s started', notify_uuid)
                except BleakCharacteristicNotFoundError:
                    _log.debug('start_notifications: characteristic %s not found', notify_uuid)

    # Notifications are stopped automatically on disconnect, so this method does not need to be called
    # unless notifications need to be stopped before the device disconnects
    def stop_notifications(self) -> None:
        for notify_uuid in self._active_notification_uuids:
            if self._ble_client is not None and self._ble_client.is_connected:
                try:
                    ble.stop_notify(self._ble_client, notify_uuid)
                    _log.debug('notifications on %s stopped', notify_uuid)
                except BleakCharacteristicNotFoundError:
                    _log.debug('start_notifications: characteristic %s not found', notify_uuid)
        self._active_notification_uuids = set()

    def _disconnect(self) -> None:
        if self._ble_client is not None and self._ble_client.is_connected:
            ble.disconnect_ble(self._ble_client)

    # returns the service UUID connected to or None
    def connected(self) -> Optional[str]:
        if self._ble_client is not None and self._ble_client.is_connected:
            return self._connected_service_uuid
        return None


    # connect and re-connect while self._running to BLE
    async def _connect(self, case_sensitive:bool=True, scan_timeout:float=6, connect_timeout:float=6, address:Optional[str] = None) -> None:
        blacklist:Set[str] = set()
        while self._running:
            # scan and connect
            # NOTE: re-connecting a bleak client by address on reconnect can lead to instabilities thus we re-scan always
            service_uuid:Optional[str]
            self._connected_service_uuid = None
            self._ble_client, service_uuid = ble.scan_and_connect(
                                    self._device_descriptions,
                                    blacklist,
                                    case_sensitive,
                                    self.disconnected_callback,
                                    scan_timeout,
                                    connect_timeout,
                                    address)
            if service_uuid is not None and self._ble_client is not None and self._ble_client.is_connected:
                # validate correct service
                try:
                    for service in self._ble_client.services:
                        if service.uuid.casefold() == service_uuid.casefold():
                            # client offers the service that was requests
                            self._connected_service_uuid = service_uuid
                            break
                except Exception as e: # pylint: disable=broad-except
                    _log.error(e)
                if self._connected_service_uuid is None:
                    # the client does not offer our service thus we put its
                    # address on the blacklist to be ignore on next discover
                    # and disconnect
                    ##blacklist.add(self._ble_client.address) # we don't blacklist as the searched for service might just not yet be discovered
                    self._disconnect()
                    self._ble_client = None
                else:
                    # successfully connected
                    self.on_connect()
            if self._ble_client is not None:
                # start notifications
                self.start_notifications()
                # await disconnect
                self._disconnected_event.clear()
                await self._disconnected_event.wait()
                _log.debug('BLE reconnect')
            await asyncio.sleep(0.1)

    # release the async lock _disconnected_event after disconnect triggered to enable the automatic reconnect
    async def set_event(self) -> None:
        # if still connected, wait somewhat until really disconnected
        while self._ble_client is not None and self._ble_client.is_connected:
            await asyncio.sleep(0.05)
        self._disconnected_event.set()

    # this seems only to be called if disconnect from device received and not if disconnecting via API calls
    def disconnected_callback(self, _client:BleakClient) -> None:
        self.stop_notifications()
        self.on_disconnect()
        if hasattr(self, '_async_loop_thread') and self._async_loop_thread is not None:
            asyncio.run_coroutine_threadsafe(self.set_event(), self._async_loop_thread.loop)

    def send(self, message:bytes, response:bool = False, write_characteristic:Optional[str] = None) -> None:
        if self._ble_client is not None and self._connected_service_uuid is not None and self._connected_service_uuid in self._writers:
            if self._logging:
                _log.debug('send to %s: %s', self._writers[self._connected_service_uuid], message)
            write_chars = self._writers[self._connected_service_uuid]
            wc:Optional[str] = None
            if write_characteristic is None:
                # if there is no explicit write_characteristic specified thus we write to the only registered as writer
                if len(write_chars) == 1:
                    wc = write_chars[0]
            elif write_characteristic in write_chars:
                wc = write_characteristic
            if wc is None:
                if write_characteristic is None:
                    _log.debug('send failed. No unique write characteristic registered for service %s', self._connected_service_uuid)
                else:
                    _log.debug('send failed. Characteristic %s not registered for write for service %s', write_characteristic, self._connected_service_uuid)
            else:
                ble.write(self._ble_client, wc, message, response)

    def read(self, read_characteristic:Optional[str] = None) -> Optional[bytes]:
        if self._ble_client is not None and self._connected_service_uuid is not None and self._connected_service_uuid in self._readers:
            if self._logging:
                _log.debug('receive from %s', self._readers[self._connected_service_uuid])
            read_chars = self._readers[self._connected_service_uuid]
            rc:Optional[str] = None
            if read_characteristic is None:
                # if there is no explicit read_characteristic specified thus we read from the only registered as reader
                if len(read_chars) == 1:
                    rc = read_chars[0]
            elif read_characteristic in read_chars:
                rc = read_characteristic
            if rc is None:
                if read_characteristic is None:
                    _log.debug('read failed. No unique read characteristic registered for service %s', self._connected_service_uuid)
                else:
                    _log.debug('read failed. Characteristic %s not registered for read for service %s', read_characteristic, self._connected_service_uuid)
            else:
                return ble.read(self._ble_client, rc)
        return None

    async def _keep_alive(self) -> None:
        while self._heartbeat_frequency > 0 and self._running:
            await asyncio.sleep(self._heartbeat_frequency)
            self.heartbeat()

    async def _connect_and_keep_alive(self,case_sensitive:bool,scan_timeout:float, connect_timeout:float, address:Optional[str] = None) -> None:
        await asyncio.gather(
            self._connect(case_sensitive,scan_timeout,connect_timeout, address),
            self._keep_alive())


    def scan(self, scan_timeout:float = 3.0) -> 'List[Tuple[BLEDevice, AdvertisementData]]':
        try:
            if not hasattr(self, '_async_loop_thread') or self._async_loop_thread is None:
                self._running = True # enable automatic reconnects
                self._async_loop_thread = AsyncLoopThread()
                # run scan in async loop
                coro = BleakScanner.discover(
                    timeout=scan_timeout,
                    return_adv=True)
                res = asyncio.run_coroutine_threadsafe(
                    coro,
                    self._async_loop_thread.loop).result()
                _log.debug('scan_ble ended')
                if res:
                    return list(res.values())
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        return []


    def start(self, case_sensitive:bool=True, scan_timeout:float=6, connect_timeout:float=6, address:Optional[str] = None) -> None:
        _log.debug('start')
        if self._running:
            _log.error('BLE client already running')
        else:
            try:
                if not hasattr(self, '_async_loop_thread') or self._async_loop_thread is None:
                    self._running = True # enable automatic reconnects
                    self._async_loop_thread = AsyncLoopThread()
                    # run _connect in async loop
                    asyncio.run_coroutine_threadsafe(
                        self._connect_and_keep_alive(case_sensitive, scan_timeout, connect_timeout, address),
                        self._async_loop_thread.loop)
                    _log.debug('BLE client started')
                    self.on_start()
            except Exception as e:  # pylint: disable=broad-except
                _log.exception(e)


    def stop(self) -> None:
        _log.debug('stop')
        if self._running:
            self._running = False # disable automatic reconnects
            if self._ble_client is None:
                ble.terminate_scan() # we stop ongoing scanning
            self._disconnect()
            self._async_loop_thread = None
            self._ble_client = None
            self._connected_service_uuid = None
            _log.debug('BLE client stopped')
            self.on_stop()
        else:
            _log.error('BLE client not running')



    ## external API

    # configurations

    def setLogging(self, b:bool) -> None:
        self._logging = b

    # clears device descriptions used to match services
    def init_device_description(self) -> None:
        self._device_descriptions = {}

    # adds the device description (service UUID and name) to the list of matchers used to filter discovered
    # clients. Any name added with to an associated UUID will create a match. Associating a service UUID with
    # an empty name (None) will match independent of the discovered clients name, as long as the a service with
    # the specified service UUID is supported. The empty service UUID (None) matches with any discovered client of the associated names.
    # If both, serviceUUID and device name are not given (both set to None), any service matches.
    # The initial device description as generated on init_device_description() does not match anything.
    def add_device_description(self, service_uuid:Optional[str] = None, device_name:Optional[str] = None) -> None:
        if service_uuid is None and device_name is None:
            self._device_descriptions = {}
        elif device_name is None:
            self._device_descriptions[service_uuid] = None
        elif service_uuid not in self._device_descriptions:
            self._device_descriptions[service_uuid] = { device_name }
        elif self._device_descriptions[service_uuid] is not None:
            self._device_descriptions[service_uuid].add(device_name) # type:ignore

    def add_notify(self, notify_uuid:str, callback:'Callable[[BleakGATTCharacteristic, bytearray], None]') -> None:
        self._notifications[notify_uuid] = callback

    def add_write(self, service_uuid:str, write_uuid:str) -> None:
        if service_uuid in self._writers:
            self._writers[service_uuid].append(write_uuid)
        else:
            self._writers[service_uuid] = [write_uuid]

    def add_read(self, service_uuid:str, read_uuid:str) -> None:
        if service_uuid in self._readers:
            self._readers[service_uuid].append(read_uuid)
        else:
            self._readers[service_uuid] = [read_uuid]

    def set_heartbeat(self, frequency:float) -> None:
        self._heartbeat_frequency = frequency

    # to be implemented by subclasses

    def on_start(self) -> None: # pylint: disable=no-self-use
        ...
    def on_connect(self) -> None: # pylint: disable=no-self-use
        ...
    def on_disconnect(self) -> None: # pylint: disable=no-self-use
        ...
    def on_stop(self) -> None: # pylint: disable=no-self-use
        ...
    def heartbeat(self) -> None: # pylint: disable=no-self-use
        ...
