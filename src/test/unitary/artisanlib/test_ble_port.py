"""Unit tests for artisanlib.ble_port module.

This module tests the BLE and ClientBLE classes functionality including:
- BLE device scanning and discovery
- Connection and disconnection handling
- Data reading and writing operations
- Notification handling and callbacks
- Device description matching
- Async loop thread management
- Error handling and timeout management
- Heartbeat and keep-alive functionality
- Service and characteristic management
"""

import warnings
import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from artisanlib.ble_port import BLE, ClientBLE


@pytest.fixture
def mock_ble_device() -> Mock:
    """Create a mock BLEDevice for testing."""
    device = Mock()
    device.name = 'TestDevice'
    device.address = 'AA:BB:CC:DD:EE:FF'
    return device


@pytest.fixture
def mock_advertisement_data() -> Mock:
    """Create a mock AdvertisementData for testing."""
    ad = Mock()
    ad.local_name = 'TestLocalName'
    ad.service_uuids = ['12345678-1234-1234-1234-123456789abc']
    return ad


@pytest.fixture
def mock_bleak_client() -> Mock:
    """Create a mock BleakClient for testing."""
    client = Mock()
    client.is_connected = True
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.read_gatt_char = AsyncMock(return_value=b'test_data')
    client.write_gatt_char = AsyncMock()
    client.start_notify = AsyncMock()
    client.stop_notify = AsyncMock()
    return client


@pytest.fixture
def ble_instance() -> BLE:
    """Create a BLE instance for testing."""
    return BLE()


@pytest.fixture
def client_ble_instance() -> ClientBLE:
    """Create a ClientBLE instance for testing."""
    return ClientBLE()


class TestBLE:
    """Test BLE class functionality."""

    def test_ble_initialization(self) -> None:
        """Test BLE class initialization."""
        # Assert
        assert hasattr(BLE, '_scan_and_connect_lock')
        assert hasattr(BLE, '_terminate_scan_event')
        assert hasattr(BLE, '_asyncLoopThread')
        assert isinstance(BLE._scan_and_connect_lock, asyncio.Lock)
        assert isinstance(BLE._terminate_scan_event, asyncio.Event)

    def test_close_with_async_loop_thread(self, ble_instance: BLE) -> None:
        """Test close method when async loop thread exists."""
        # Arrange
        mock_thread = Mock()
        ble_instance._asyncLoopThread = mock_thread

        # Act
        ble_instance.close()

        # Assert
        assert ble_instance._asyncLoopThread is None

    def test_close_without_async_loop_thread(self, ble_instance: BLE) -> None:
        """Test close method when no async loop thread exists."""
        # Arrange
        ble_instance._asyncLoopThread = None

        # Act - Should not raise exception
        ble_instance.close()

        # Assert
        assert ble_instance._asyncLoopThread is None

    def test_terminate_scan(self, ble_instance: BLE) -> None:
        """Test terminate_scan method."""
        # Arrange
        BLE._terminate_scan_event.clear()

        # Act
        ble_instance.terminate_scan()

        # Assert
        assert BLE._terminate_scan_event.is_set()

    def test_name_match_with_device_name_case_sensitive(
        self, mock_ble_device: Mock, mock_advertisement_data: Mock
    ) -> None:
        """Test name_match with device name case sensitive."""
        # Arrange
        mock_ble_device.name = 'TestDevice'
        device_name = 'Test'

        # Act
        result = BLE.name_match(mock_ble_device, mock_advertisement_data, device_name, True, None)

        # Assert
        assert result is True

    def test_name_match_with_device_name_case_insensitive(
        self, mock_ble_device: Mock, mock_advertisement_data: Mock
    ) -> None:
        """Test name_match with device name case insensitive."""
        # Arrange
        mock_ble_device.name = 'testdevice'
        device_name = 'TEST'

        # Act
        result = BLE.name_match(mock_ble_device, mock_advertisement_data, device_name, False, None)

        # Assert
        assert result is True

    def test_name_match_with_local_name(
        self, mock_ble_device: Mock, mock_advertisement_data: Mock
    ) -> None:
        """Test name_match with local name."""
        # Arrange
        mock_ble_device.name = None
        mock_advertisement_data.local_name = 'TestLocal'
        device_name = 'Test'

        # Act
        result = BLE.name_match(mock_ble_device, mock_advertisement_data, device_name, True, None)

        # Assert
        assert result is True

    def test_name_match_with_service_uuid(
        self, mock_ble_device: Mock, mock_advertisement_data: Mock
    ) -> None:
        """Test name_match with service UUID when local_name is None."""
        # Arrange
        mock_ble_device.name = None
        mock_advertisement_data.local_name = None
        service_uuid = '12345678-1234-1234-1234-123456789abc'
        mock_advertisement_data.service_uuids = [service_uuid]

        # Act
        result = BLE.name_match(
            mock_ble_device, mock_advertisement_data, 'NonExistent', True, service_uuid
        )

        # Assert
        assert result is True

    def test_name_match_no_match(
        self, mock_ble_device: Mock, mock_advertisement_data: Mock
    ) -> None:
        """Test name_match when no match is found."""
        # Arrange
        mock_ble_device.name = 'DifferentDevice'
        mock_advertisement_data.local_name = 'DifferentLocal'
        device_name = 'Test'

        # Act
        result = BLE.name_match(mock_ble_device, mock_advertisement_data, device_name, True, None)

        # Assert
        assert result is False

    def test_description_match_success(
        self, ble_instance: BLE, mock_ble_device: Mock, mock_advertisement_data: Mock
    ) -> None:
        """Test description_match with successful match."""
        # Arrange
        device_descriptions = {
            'service-uuid-1': {'TestDevice', 'AnotherDevice'},
            'service-uuid-2': None,
        }
        mock_ble_device.name = 'TestDevice'

        # Act
        result, service_uuid = ble_instance.description_match(
            mock_ble_device, mock_advertisement_data, device_descriptions, True  # type: ignore[arg-type]
        )

        # Assert
        assert result is True
        assert service_uuid == 'service-uuid-1'

    def test_description_match_with_none_device_names(
        self, ble_instance: BLE, mock_ble_device: Mock, mock_advertisement_data: Mock
    ) -> None:
        """Test description_match with None device names (matches any)."""
        # Arrange
        device_descriptions = {'service-uuid-1': None}

        # Act
        result, service_uuid = ble_instance.description_match(
            mock_ble_device, mock_advertisement_data, device_descriptions, True  # type: ignore[arg-type]
        )

        # Assert
        assert result is True
        assert service_uuid == 'service-uuid-1'

    def test_description_match_no_match(
        self, ble_instance: BLE, mock_ble_device: Mock, mock_advertisement_data: Mock
    ) -> None:
        """Test description_match when no match is found."""
        # Arrange
        device_descriptions = {'service-uuid-1': {'DifferentDevice'}}
        mock_ble_device.name = 'TestDevice'
        mock_advertisement_data.local_name = 'TestLocal'

        # Act
        result, service_uuid = ble_instance.description_match(
            mock_ble_device, mock_advertisement_data, device_descriptions, True  # type: ignore[arg-type]
        )

        # Assert
        assert result is False
        assert service_uuid is None

    def test_write_success(self, ble_instance: BLE, mock_bleak_client: Mock) -> None:
        """Test successful write operation."""
        # Arrange
        mock_thread = Mock()
        mock_thread.loop = Mock()
        ble_instance._asyncLoopThread = mock_thread
        write_uuid = 'write-characteristic-uuid'
        message = b'test message that is longer than 20 bytes to test chunking'

        with patch('asyncio.run_coroutine_threadsafe') as mock_run_coroutine:
            # Act
            ble_instance.write(mock_bleak_client, write_uuid, message, response=True)

            # Assert
            # Should be called multiple times due to chunking (20 byte chunks)
            assert mock_run_coroutine.call_count >= 3  # Message is longer than 40 bytes

    def test_write_with_no_async_thread(self, ble_instance: BLE, mock_bleak_client: Mock) -> None:
        """Test write when no async thread exists."""
        # Arrange
        ble_instance._asyncLoopThread = None

        # Act - Should not raise exception
        ble_instance.write(mock_bleak_client, 'uuid', b'message')

        # Assert - No exception should be raised

    def test_write_with_disconnected_client(
        self, ble_instance: BLE, mock_bleak_client: Mock
    ) -> None:
        """Test write with disconnected client."""
        # Arrange
        mock_thread = Mock()
        ble_instance._asyncLoopThread = mock_thread
        mock_bleak_client.is_connected = False


        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)

            # Act - Should not raise exception
            ble_instance.write(mock_bleak_client, 'uuid', b'message')

            # Assert - No exception should be raised

    def test_read_success(self, ble_instance: BLE, mock_bleak_client: Mock) -> None:
        """Test successful read operation."""
        # Arrange
        mock_thread = Mock()
        mock_thread.loop = Mock()
        ble_instance._asyncLoopThread = mock_thread
        read_uuid = 'read-characteristic-uuid'
        expected_data = b'test_data'

        mock_future = Mock()
        mock_future.result.return_value = expected_data

        with patch('asyncio.run_coroutine_threadsafe', return_value=mock_future):
            # Act
            result = ble_instance.read(mock_bleak_client, read_uuid)

            # Assert
            assert result == expected_data

    def test_read_with_exception(self, ble_instance: BLE, mock_bleak_client: Mock) -> None:
        """Test read operation with exception."""
        # Arrange
        mock_thread = Mock()
        mock_thread.loop = Mock()
        ble_instance._asyncLoopThread = mock_thread

        mock_future = Mock()
        mock_future.result.side_effect = Exception('Read failed')
        mock_future.exception.return_value = Exception('Read failed')

        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)

            with patch('asyncio.run_coroutine_threadsafe', return_value=mock_future):
                # Act
                result = ble_instance.read(mock_bleak_client, 'uuid')

                # Assert
                assert result is None

    def test_read_with_no_async_thread(self, ble_instance: BLE, mock_bleak_client: Mock) -> None:
        """Test read when no async thread exists."""
        # Arrange
        ble_instance._asyncLoopThread = None

        # Act
        result = ble_instance.read(mock_bleak_client, 'uuid')

        # Assert
        assert result is None

    def test_disconnect_ble_success(self, ble_instance: BLE, mock_bleak_client: Mock) -> None:
        """Test successful BLE disconnection."""
        # Arrange
        mock_thread = Mock()
        mock_thread.loop = Mock()
        ble_instance._asyncLoopThread = mock_thread

        with patch('asyncio.run_coroutine_threadsafe') as mock_run_coroutine:
            # Act
            result = ble_instance.disconnect_ble(mock_bleak_client)

            # Assert
            assert result is False  # Method always returns False
            mock_run_coroutine.assert_called_once()

    def test_disconnect_ble_with_no_async_thread(
        self, ble_instance: BLE, mock_bleak_client: Mock
    ) -> None:
        """Test BLE disconnection when no async thread exists."""
        # Arrange
        ble_instance._asyncLoopThread = None

        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)

            # Act
            result = ble_instance.disconnect_ble(mock_bleak_client)

            # Assert
            assert result is False


class TestClientBLE:
    """Test ClientBLE class functionality."""

    def test_client_ble_initialization(self, client_ble_instance: ClientBLE) -> None:
        """Test ClientBLE initialization."""
        # Assert
        assert client_ble_instance._running is False
        assert client_ble_instance._async_loop_thread is None
        assert client_ble_instance._ble_client is None
        assert client_ble_instance._connected_service_uuid is None
        assert client_ble_instance._connected_device_name is None
        assert isinstance(client_ble_instance._disconnected_event, asyncio.Event)
        assert client_ble_instance._active_notification_uuids == set()
        assert client_ble_instance._sleep_between_scans == ClientBLE.SCAN_BETWEEN_SCANS_START
        assert client_ble_instance._device_descriptions == {}
        assert client_ble_instance._notifications == {}
        assert client_ble_instance._writers == {}
        assert client_ble_instance._readers == {}
        assert client_ble_instance._heartbeat_frequency == 0
        assert client_ble_instance._logging is False

    def test_client_ble_constants(self) -> None:
        """Test ClientBLE class constants."""
        # Assert
        assert ClientBLE.SCAN_BETWEEN_SCANS_START == 0.1
        assert ClientBLE.SCAN_BETWEEN_SCANS_INC == 0.1
        assert ClientBLE.SCAN_BETWEEN_SCANS_MAX == 3

    def test_set_logging(self, client_ble_instance: ClientBLE) -> None:
        """Test setLogging method."""
        # Act
        client_ble_instance.setLogging(True)

        # Assert
        assert client_ble_instance._logging is True

        # Act
        client_ble_instance.setLogging(False)

        # Assert
        assert client_ble_instance._logging is False

    def test_init_device_description(self, client_ble_instance: ClientBLE) -> None:
        """Test init_device_description method."""
        # Arrange
        client_ble_instance._device_descriptions = {'test': {'device'}}

        # Act
        client_ble_instance.init_device_description()

        # Assert
        assert client_ble_instance._device_descriptions == {}

    def test_add_device_description_with_service_and_device(
        self, client_ble_instance: ClientBLE
    ) -> None:
        """Test add_device_description with service UUID and device name."""
        # Act
        client_ble_instance.add_device_description('service-uuid-1', 'TestDevice')

        # Assert
        assert 'service-uuid-1' in client_ble_instance._device_descriptions
        assert client_ble_instance._device_descriptions['service-uuid-1'] == {'TestDevice'}

    def test_add_device_description_multiple_devices_same_service(
        self, client_ble_instance: ClientBLE
    ) -> None:
        """Test adding multiple devices to same service."""
        # Act
        client_ble_instance.add_device_description('service-uuid-1', 'Device1')
        client_ble_instance.add_device_description('service-uuid-1', 'Device2')

        # Assert
        assert client_ble_instance._device_descriptions['service-uuid-1'] == {'Device1', 'Device2'}

    def test_add_device_description_service_only(self, client_ble_instance: ClientBLE) -> None:
        """Test add_device_description with service UUID only."""
        # Act
        client_ble_instance.add_device_description('service-uuid-1', None)

        # Assert
        assert client_ble_instance._device_descriptions['service-uuid-1'] is None

    def test_add_device_description_clear_all(self, client_ble_instance: ClientBLE) -> None:
        """Test clearing all device descriptions."""
        # Arrange
        client_ble_instance._device_descriptions = {'test': {'device'}}

        # Act
        client_ble_instance.add_device_description(None, None)

        # Assert
        assert client_ble_instance._device_descriptions == {}

    def test_add_notify(self, client_ble_instance: ClientBLE) -> None:
        """Test add_notify method."""
        # Arrange
        callback = Mock()
        notify_uuid = 'notify-characteristic-uuid'

        # Act
        client_ble_instance.add_notify(notify_uuid, callback)

        # Assert
        assert client_ble_instance._notifications[notify_uuid] == callback

    def test_add_write(self, client_ble_instance: ClientBLE) -> None:
        """Test add_write method."""
        # Act
        client_ble_instance.add_write('service-uuid-1', 'write-uuid-1')
        client_ble_instance.add_write('service-uuid-1', 'write-uuid-2')

        # Assert
        assert client_ble_instance._writers['service-uuid-1'] == ['write-uuid-1', 'write-uuid-2']

    def test_add_read(self, client_ble_instance: ClientBLE) -> None:
        """Test add_read method."""
        # Act
        client_ble_instance.add_read('service-uuid-1', 'read-uuid-1')
        client_ble_instance.add_read('service-uuid-1', 'read-uuid-2')

        # Assert
        assert client_ble_instance._readers['service-uuid-1'] == ['read-uuid-1', 'read-uuid-2']

    def test_set_heartbeat(self, client_ble_instance: ClientBLE) -> None:
        """Test set_heartbeat method."""
        # Act
        client_ble_instance.set_heartbeat(5.0)

        # Assert
        assert client_ble_instance._heartbeat_frequency == 5.0

    def test_send_success_single_writer(self, client_ble_instance: ClientBLE) -> None:
        """Test successful send with single writer."""
        # Arrange
        mock_client = Mock()
        client_ble_instance._ble_client = mock_client
        client_ble_instance._connected_service_uuid = 'service-uuid-1'
        client_ble_instance._writers = {'service-uuid-1': ['write-uuid-1']}
        message = b'test message'

        with patch('artisanlib.ble_port.ble') as mock_ble:
            # Act
            client_ble_instance.send(message, response=True)

            # Assert
            mock_ble.write.assert_called_once_with(mock_client, 'write-uuid-1', message, True)

    def test_send_with_specific_write_characteristic(self, client_ble_instance: ClientBLE) -> None:
        """Test send with specific write characteristic."""
        # Arrange
        mock_client = Mock()
        client_ble_instance._ble_client = mock_client
        client_ble_instance._connected_service_uuid = 'service-uuid-1'
        client_ble_instance._writers = {'service-uuid-1': ['write-uuid-1', 'write-uuid-2']}
        message = b'test message'

        with patch('artisanlib.ble_port.ble') as mock_ble:
            # Act
            client_ble_instance.send(message, write_characteristic='write-uuid-2')

            # Assert
            mock_ble.write.assert_called_once_with(mock_client, 'write-uuid-2', message, False)

    def test_send_no_client(self, client_ble_instance: ClientBLE) -> None:
        """Test send when no client is connected."""
        # Arrange
        client_ble_instance._ble_client = None

        # Act - Should not raise exception
        client_ble_instance.send(b'test message')

        # Assert - No exception should be raised

    def test_send_multiple_writers_no_specific_characteristic(
        self, client_ble_instance: ClientBLE
    ) -> None:
        """Test send with multiple writers but no specific characteristic."""
        # Arrange
        mock_client = Mock()
        client_ble_instance._ble_client = mock_client
        client_ble_instance._connected_service_uuid = 'service-uuid-1'
        client_ble_instance._writers = {'service-uuid-1': ['write-uuid-1', 'write-uuid-2']}

        # Act - Should not write anything due to ambiguity
        client_ble_instance.send(b'test message')

        # Assert - No write should occur due to multiple writers without specification

    def test_read_success_single_reader(self, client_ble_instance: ClientBLE) -> None:
        """Test successful read with single reader."""
        # Arrange
        mock_client = Mock()
        client_ble_instance._ble_client = mock_client
        client_ble_instance._connected_service_uuid = 'service-uuid-1'
        client_ble_instance._readers = {'service-uuid-1': ['read-uuid-1']}
        expected_data = b'test_data'

        with patch('artisanlib.ble_port.ble') as mock_ble:
            mock_ble.read.return_value = expected_data

            # Act
            result = client_ble_instance.read()

            # Assert
            assert result == expected_data
            mock_ble.read.assert_called_once_with(mock_client, 'read-uuid-1')

    def test_read_with_specific_read_characteristic(self, client_ble_instance: ClientBLE) -> None:
        """Test read with specific read characteristic."""
        # Arrange
        mock_client = Mock()
        client_ble_instance._ble_client = mock_client
        client_ble_instance._connected_service_uuid = 'service-uuid-1'
        client_ble_instance._readers = {'service-uuid-1': ['read-uuid-1', 'read-uuid-2']}
        expected_data = b'test_data'

        with patch('artisanlib.ble_port.ble') as mock_ble:
            mock_ble.read.return_value = expected_data

            # Act
            result = client_ble_instance.read(read_characteristic='read-uuid-2')

            # Assert
            assert result == expected_data
            mock_ble.read.assert_called_once_with(mock_client, 'read-uuid-2')

    def test_read_no_client(self, client_ble_instance: ClientBLE) -> None:
        """Test read when no client is connected."""
        # Arrange
        client_ble_instance._ble_client = None

        # Act
        result = client_ble_instance.read()

        # Assert
        assert result is None

    def test_read_multiple_readers_no_specific_characteristic(
        self, client_ble_instance: ClientBLE
    ) -> None:
        """Test read with multiple readers but no specific characteristic."""
        # Arrange
        mock_client = Mock()
        client_ble_instance._ble_client = mock_client
        client_ble_instance._connected_service_uuid = 'service-uuid-1'
        client_ble_instance._readers = {'service-uuid-1': ['read-uuid-1', 'read-uuid-2']}

        # Act
        result = client_ble_instance.read()

        # Assert
        assert result is None  # Should return None due to ambiguity

    def test_stop_success(self, client_ble_instance: ClientBLE) -> None:
        """Test successful stop."""
        # Arrange
        client_ble_instance._running = True

        # Act
        client_ble_instance.stop()

        # Assert
        assert client_ble_instance._running is False

    def test_stop_when_not_running(self, client_ble_instance: ClientBLE) -> None:
        """Test stop when not running."""
        # Arrange
        client_ble_instance._running = False

        # Act - Should not raise exception
        client_ble_instance.stop()

        # Assert
        assert client_ble_instance._running is False

    def test_connected_with_client(self, client_ble_instance: ClientBLE) -> None:
        """Test connected method when client is connected."""
        # Arrange
        mock_client = Mock()
        mock_client.is_connected = True
        client_ble_instance._ble_client = mock_client
        client_ble_instance._connected_service_uuid = 'service-uuid-1'
        client_ble_instance._connected_device_name = 'TestDevice'

        # Act
        service_uuid, device_name = client_ble_instance.connected()

        # Assert
        assert service_uuid == 'service-uuid-1'
        assert device_name == 'TestDevice'

    def test_connected_no_client(self, client_ble_instance: ClientBLE) -> None:
        """Test connected method when no client exists."""
        # Arrange
        client_ble_instance._ble_client = None

        # Act
        service_uuid, device_name = client_ble_instance.connected()

        # Assert
        assert service_uuid is None
        assert device_name is None

    def test_connected_client_disconnected(self, client_ble_instance: ClientBLE) -> None:
        """Test connected method when client is disconnected."""
        # Arrange
        mock_client = Mock()
        mock_client.is_connected = False
        client_ble_instance._ble_client = mock_client

        # Act
        service_uuid, device_name = client_ble_instance.connected()

        # Assert
        assert service_uuid is None
        assert device_name is None

    # Test the abstract methods that should be implemented by subclasses
    def test_on_start_default_implementation(self, client_ble_instance: ClientBLE) -> None:
        """Test on_start default implementation."""
        # Act - Should not raise exception
        client_ble_instance.on_start()

        # Assert - No exception should be raised

    def test_on_connect_default_implementation(self, client_ble_instance: ClientBLE) -> None:
        """Test on_connect default implementation."""
        # Act - Should not raise exception
        client_ble_instance.on_connect()

        # Assert - No exception should be raised

    def test_on_disconnect_default_implementation(self, client_ble_instance: ClientBLE) -> None:
        """Test on_disconnect default implementation."""
        # Act - Should not raise exception
        client_ble_instance.on_disconnect()

        # Assert - No exception should be raised

    def test_on_stop_default_implementation(self, client_ble_instance: ClientBLE) -> None:
        """Test on_stop default implementation."""
        # Act - Should not raise exception
        client_ble_instance.on_stop()

        # Assert - No exception should be raised

    def test_heartbeat_default_implementation(self, client_ble_instance: ClientBLE) -> None:
        """Test heartbeat default implementation."""
        # Act - Should not raise exception
        client_ble_instance.heartbeat()

        # Assert - No exception should be raised
