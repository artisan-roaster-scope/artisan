"""Unit tests for artisanlib.phidgets module.

This module tests the PhidgetManager class functionality including:
- Phidget device manager initialization and cleanup
- Device attach and detach event handling
- Channel management and reservation system
- Hub port device handling and VINT device management
- Serial port and channel matching algorithms
- Remote and local device filtering
- Thread-safe access with semaphore protection
- Device discovery and availability tracking
- Hub port blocking and unblocking logic
- Error handling and exception management
"""

from typing import Any, Dict, Generator
from unittest.mock import Mock, patch

import pytest

from artisanlib.phidgets import PhidgetManager


@pytest.fixture(autouse=True)
def reset_test_state() -> Generator[None, None, None]:
    """Reset all test state before each test to ensure test independence."""
    yield
    # Clean up after each test - no specific cleanup needed for this module


@pytest.fixture
def mock_manager() -> Generator[Mock, None, None]:
    """Create a fresh mock Phidget Manager for each test."""
    with patch('artisanlib.phidgets.Manager') as mock:
        mock_instance = Mock()
        # Reset all mock state to ensure fresh instance
        mock_instance.reset_mock()
        mock_instance.setOnAttachHandler = Mock()
        mock_instance.setOnDetachHandler = Mock()
        mock_instance.open = Mock()
        mock_instance.close = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_qsemaphore() -> Generator[Mock, None, None]:
    """Create a fresh mock QSemaphore for each test."""
    with patch('artisanlib.phidgets.QSemaphore') as mock:
        mock_instance = Mock()
        # Reset and configure mock state
        mock_instance.reset_mock()
        mock_instance.available = Mock(return_value=0)  # Changed to 0 so release() will be called
        mock_instance.acquire = Mock()
        mock_instance.release = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_device_class() -> Generator[Mock, None, None]:
    """Create fresh mock DeviceClass constants for each test."""
    with patch('artisanlib.phidgets.DeviceClass') as mock:
        mock.reset_mock()
        mock.PHIDCLASS_HUB = 1
        mock.PHIDCLASS_VINT = 2
        yield mock


@pytest.fixture
def mock_device_id() -> Generator[Mock, None, None]:
    """Create fresh mock DeviceID constants for each test."""
    with patch('artisanlib.phidgets.DeviceID') as mock:
        mock.reset_mock()
        mock.PHIDID_HUB0000 = 100
        mock.PHIDID_DIGITALINPUT_PORT = 101
        mock.PHIDID_DIGITALOUTPUT_PORT = 102
        mock.PHIDID_VOLTAGEINPUT_PORT = 103
        mock.PHIDID_VOLTAGERATIOINPUT_PORT = 104
        yield mock


@pytest.fixture
def mock_phidget_channel() -> Mock:
    """Create a fresh mock Phidget channel for each test."""
    channel = Mock()
    # Reset mock state to ensure fresh instance
    channel.reset_mock()

    # Configure default return values
    channel.getDeviceSerialNumber.return_value = 12345
    channel.getHubPort.return_value = 0
    channel.getChannel.return_value = 0
    channel.getChannelClassName.return_value = 'PhidgetTemperatureSensor'
    channel.getDeviceID.return_value = 200
    channel.getIsLocal.return_value = True
    channel.getIsHubPortDevice.return_value = 1
    channel.getDeviceClass.return_value = 2
    channel.getHub.return_value = 1000

    # Mock parent device
    parent = Mock()
    parent.reset_mock()
    parent.getDeviceClass.return_value = 2  # Not a hub
    channel.getParent.return_value = parent

    return channel


@pytest.fixture
def phidget_manager_instance(
    mock_manager: Mock, mock_qsemaphore: Mock  # noqa: ARG001
) -> PhidgetManager:
    """Create a fresh PhidgetManager instance for each test."""
    manager = PhidgetManager()
    # Replace the real semaphore with our mock
    manager.managersemaphore = mock_qsemaphore
    # Ensure fresh state for each test
    manager.attachedPhidgetChannels = {}
    return manager


@pytest.fixture
def isolated_phidget_channels() -> Dict[Any, Any]:
    """Provide an isolated dictionary for phidget channels for each test."""
    return {}


class TestPhidgetManagerInitialization:
    """Test PhidgetManager initialization and cleanup."""

    def test_phidget_manager_initialization(
        self, phidget_manager_instance: PhidgetManager, mock_manager: Mock, mock_qsemaphore: Mock
    ) -> None:
        """Test PhidgetManager initialization."""
        # Assert
        assert phidget_manager_instance.attachedPhidgetChannels == {}
        assert phidget_manager_instance.managersemaphore == mock_qsemaphore
        assert phidget_manager_instance.manager == mock_manager

        # Verify manager setup
        mock_manager.setOnAttachHandler.assert_called_once()
        mock_manager.setOnDetachHandler.assert_called_once()
        mock_manager.open.assert_called_once()

    def test_phidget_manager_close(
        self, phidget_manager_instance: PhidgetManager, mock_manager: Mock
    ) -> None:
        """Test PhidgetManager close method."""
        # Arrange
        phidget_manager_instance.attachedPhidgetChannels = {'test': True} # pyrefly: ignore

        # Act
        phidget_manager_instance.close()

        # Assert
        mock_manager.close.assert_called_once()
        assert phidget_manager_instance.attachedPhidgetChannels == {}


class TestPhidgetManagerEventHandlers:
    """Test PhidgetManager attach and detach event handlers."""

    def test_attach_handler_non_hub_device(
        self,
        phidget_manager_instance: PhidgetManager,
        mock_device_class: Mock,  # noqa: ARG002
        mock_phidget_channel: Mock,
    ) -> None:
        """Test attach handler with non-hub device."""
        # Arrange
        mock_phidget_channel.getParent.return_value.getDeviceClass.return_value = 2  # Not a hub
        initial_count = len(phidget_manager_instance.attachedPhidgetChannels)

        # Act
        phidget_manager_instance.attachHandler(Mock(), mock_phidget_channel)

        # Assert
        assert len(phidget_manager_instance.attachedPhidgetChannels) == initial_count + 1
        assert mock_phidget_channel in phidget_manager_instance.attachedPhidgetChannels

    def test_attach_handler_hub_device(
        self,
        phidget_manager_instance: PhidgetManager,
        mock_device_class: Mock,
        mock_phidget_channel: Mock,
    ) -> None:
        """Test attach handler with hub device (should not add)."""
        # Arrange
        mock_phidget_channel.getParent.return_value.getDeviceClass.return_value = (
            mock_device_class.PHIDCLASS_HUB
        )
        initial_count = len(phidget_manager_instance.attachedPhidgetChannels)

        # Act
        phidget_manager_instance.attachHandler(Mock(), mock_phidget_channel)

        # Assert
        assert len(phidget_manager_instance.attachedPhidgetChannels) == initial_count
        assert mock_phidget_channel not in phidget_manager_instance.attachedPhidgetChannels

    def test_attach_handler_with_exception(
        self, phidget_manager_instance: PhidgetManager, mock_phidget_channel: Mock
    ) -> None:
        """Test attach handler with exception."""
        # Arrange
        mock_phidget_channel.getParent.side_effect = Exception('Test exception')

        # Act - Should not raise exception
        phidget_manager_instance.attachHandler(Mock(), mock_phidget_channel)

        # Assert - No exception should be raised

    def test_detach_handler_success(
        self, phidget_manager_instance: PhidgetManager, mock_phidget_channel: Mock
    ) -> None:
        """Test detach handler success."""
        # Arrange
        phidget_manager_instance.attachedPhidgetChannels[mock_phidget_channel] = True

        # Act
        phidget_manager_instance.detachHandler(Mock(), mock_phidget_channel)

        # Assert
        assert mock_phidget_channel not in phidget_manager_instance.attachedPhidgetChannels

    def test_detach_handler_with_exception(
        self, phidget_manager_instance: PhidgetManager, mock_phidget_channel: Mock
    ) -> None:
        """Test detach handler with exception."""
        # Arrange
        mock_phidget_channel.getDeviceSerialNumber.side_effect = Exception('Test exception')
        phidget_manager_instance.attachedPhidgetChannels[mock_phidget_channel] = True

        # Act - Should not raise exception
        phidget_manager_instance.detachHandler(Mock(), mock_phidget_channel)

        # Assert - No exception should be raised


class TestPhidgetManagerChannelManagement:
    """Test PhidgetManager channel management functionality."""

    def test_add_channel_simple(
        self,
        phidget_manager_instance: PhidgetManager,
        mock_phidget_channel: Mock,
    ) -> None:
        """Test adding a simple channel."""
        # Act
        phidget_manager_instance.addChannel(mock_phidget_channel)

        # Assert
        assert mock_phidget_channel in phidget_manager_instance.attachedPhidgetChannels
        assert phidget_manager_instance.attachedPhidgetChannels[mock_phidget_channel] is True

    def test_add_channel_with_hub_port_blocking(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock  # noqa: ARG002
    ) -> None:
        """Test adding channel with hub port blocking logic."""
        # Arrange
        # Create a VINT device (not hub port device)
        vint_channel = Mock()
        vint_channel.getHub.return_value = 1000
        vint_channel.getHubPort.return_value = 1
        vint_channel.getIsHubPortDevice.return_value = 0  # VINT device

        # Create a hub port device on same hub/port
        hub_port_channel = Mock()
        hub_port_channel.getHub.return_value = 1000
        hub_port_channel.getHubPort.return_value = 1
        hub_port_channel.getIsHubPortDevice.return_value = 1  # Hub port device

        # Add hub port device first
        phidget_manager_instance.attachedPhidgetChannels[hub_port_channel] = True

        # Act - Add VINT device
        phidget_manager_instance.addChannel(vint_channel)

        # Assert
        assert (
            phidget_manager_instance.attachedPhidgetChannels[hub_port_channel] is False
        )  # Should be blocked
        assert phidget_manager_instance.attachedPhidgetChannels[vint_channel] is True

    def test_add_channel_vint_device_blocks_hub_port(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock  # noqa: ARG002
    ) -> None:
        """Test adding hub port device when VINT device exists."""
        # Arrange
        # Create a VINT device
        vint_channel = Mock()
        vint_channel.getHub.return_value = 1000
        vint_channel.getHubPort.return_value = 1
        vint_channel.getIsHubPortDevice.return_value = 0  # VINT device

        # Add VINT device first
        phidget_manager_instance.attachedPhidgetChannels[vint_channel] = True

        # Create a hub port device on same hub/port
        hub_port_channel = Mock()
        hub_port_channel.getHub.return_value = 1000
        hub_port_channel.getHubPort.return_value = 1
        hub_port_channel.getIsHubPortDevice.return_value = 1  # Hub port device

        # Act - Add hub port device
        phidget_manager_instance.addChannel(hub_port_channel)

        # Assert
        assert (
            phidget_manager_instance.attachedPhidgetChannels[hub_port_channel] is False
        )  # Should be blocked

    def test_add_channel_with_exception_in_hub_logic(
        self,
        phidget_manager_instance: PhidgetManager,
        mock_phidget_channel: Mock,
        mock_qsemaphore: Mock,
    ) -> None:
        """Test adding channel with exception in hub logic."""
        # Arrange
        mock_phidget_channel.getHub.side_effect = Exception('Hub exception')

        # Act
        phidget_manager_instance.addChannel(mock_phidget_channel)

        # Assert
        assert mock_phidget_channel in phidget_manager_instance.attachedPhidgetChannels
        mock_qsemaphore.release.assert_called_with(1)

    def test_add_channel_semaphore_exception_handling(
        self,
        phidget_manager_instance: PhidgetManager,
        mock_phidget_channel: Mock,
        mock_qsemaphore: Mock,
    ) -> None:
        """Test add channel with semaphore exception handling."""
        # Arrange
        mock_qsemaphore.acquire.side_effect = Exception('Semaphore exception')

        # Act - Should not raise exception
        phidget_manager_instance.addChannel(mock_phidget_channel)

        # Assert
        mock_qsemaphore.release.assert_called_with(1)

    def test_delete_channel_simple(
        self,
        phidget_manager_instance: PhidgetManager,
        mock_phidget_channel: Mock,
        mock_qsemaphore: Mock,
    ) -> None:
        """Test deleting a simple channel."""
        # Arrange
        phidget_manager_instance.attachedPhidgetChannels[mock_phidget_channel] = True

        # Act
        phidget_manager_instance.deleteChannel(mock_phidget_channel)

        # Assert
        assert mock_phidget_channel not in phidget_manager_instance.attachedPhidgetChannels
        mock_qsemaphore.acquire.assert_called_with(1)
        mock_qsemaphore.release.assert_called_with(1)

    def test_delete_channel_vint_device_unblocks_hub_ports(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock  # noqa: ARG002
    ) -> None:
        """Test deleting VINT device unblocks hub port devices."""
        # Arrange
        # Create a VINT device
        vint_channel = Mock()
        vint_channel.getHub.return_value = 1000
        vint_channel.getHubPort.return_value = 1
        vint_channel.getIsHubPortDevice.return_value = 0  # VINT device

        # Create blocked hub port devices on same hub/port
        hub_port_channel1 = Mock()
        hub_port_channel1.getHub.return_value = 1000
        hub_port_channel1.getHubPort.return_value = 1
        hub_port_channel1.getIsHubPortDevice.return_value = 1

        hub_port_channel2 = Mock()
        hub_port_channel2.getHub.return_value = 1000
        hub_port_channel2.getHubPort.return_value = 1
        hub_port_channel2.getIsHubPortDevice.return_value = 1

        # Set up initial state
        phidget_manager_instance.attachedPhidgetChannels[vint_channel] = True
        phidget_manager_instance.attachedPhidgetChannels[hub_port_channel1] = False  # Blocked
        phidget_manager_instance.attachedPhidgetChannels[hub_port_channel2] = False  # Blocked

        # Act - Delete VINT device
        phidget_manager_instance.deleteChannel(vint_channel)

        # Assert
        assert vint_channel not in phidget_manager_instance.attachedPhidgetChannels
        assert (
            phidget_manager_instance.attachedPhidgetChannels[hub_port_channel1] is True
        )  # Unblocked
        assert (
            phidget_manager_instance.attachedPhidgetChannels[hub_port_channel2] is True
        )  # Unblocked

    def test_delete_channel_with_hub_exception(
        self,
        phidget_manager_instance: PhidgetManager,
        mock_phidget_channel: Mock,
        mock_qsemaphore: Mock,
    ) -> None:
        """Test deleting channel with hub exception."""
        # Arrange
        phidget_manager_instance.attachedPhidgetChannels[mock_phidget_channel] = True
        mock_phidget_channel.getHub.side_effect = Exception('Hub exception')

        # Act
        phidget_manager_instance.deleteChannel(mock_phidget_channel)

        # Assert
        assert mock_phidget_channel not in phidget_manager_instance.attachedPhidgetChannels
        mock_qsemaphore.release.assert_called_with(1)

    def test_delete_channel_semaphore_exception_handling(
        self,
        phidget_manager_instance: PhidgetManager,
        mock_phidget_channel: Mock,
        mock_qsemaphore: Mock,
    ) -> None:
        """Test delete channel with semaphore exception handling."""
        # Arrange
        phidget_manager_instance.attachedPhidgetChannels[mock_phidget_channel] = True
        mock_qsemaphore.acquire.side_effect = Exception('Semaphore exception')

        # Act - Should not raise exception
        phidget_manager_instance.deleteChannel(mock_phidget_channel)

        # Assert
        mock_qsemaphore.release.assert_called_with(1)


class TestPhidgetManagerChannelRetrieval:
    """Test PhidgetManager channel retrieval functionality."""

    def test_get_channel_exact_match(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock
    ) -> None:
        """Test getting channel with exact match."""
        # Arrange
        channel = Mock()
        channel.getDeviceSerialNumber.return_value = 12345
        channel.getHubPort.return_value = 1
        channel.getChannel.return_value = 0
        channel.getChannelClassName.return_value = 'PhidgetTemperatureSensor'
        channel.getDeviceID.return_value = 200
        channel.getIsLocal.return_value = True
        channel.getIsHubPortDevice.return_value = 1
        channel.getDeviceClass.return_value = 2

        phidget_manager_instance.attachedPhidgetChannels[channel] = True

        # Act
        result = phidget_manager_instance.getChannel(
            serial=12345,
            port=1,
            channel=0,
            phidget_class_name='PhidgetTemperatureSensor',
            device_id=200,
            remote=False,
            remoteOnly=False,
        )

        # Assert
        assert result == channel
        mock_qsemaphore.acquire.assert_called_with(1)
        mock_qsemaphore.release.assert_called_with(1)

    def test_get_channel_hub_device(
        self,
        phidget_manager_instance: PhidgetManager,
        mock_device_id: Mock,
        mock_qsemaphore: Mock,  # noqa: ARG002
    ) -> None:
        """Test getting channel for hub device."""
        # Arrange
        channel = Mock()
        channel.getDeviceSerialNumber.return_value = 12345
        channel.getHubPort.return_value = 1
        channel.getChannel.return_value = 0
        channel.getChannelClassName.return_value = 'PhidgetDigitalInput'
        channel.getDeviceID.return_value = mock_device_id.PHIDID_HUB0000
        channel.getIsLocal.return_value = True
        channel.getIsHubPortDevice.return_value = 1
        channel.getDeviceClass.return_value = 2

        phidget_manager_instance.attachedPhidgetChannels[channel] = True

        # Act
        result = phidget_manager_instance.getChannel(
            serial=12345,
            port=1,
            channel=0,
            phidget_class_name='PhidgetDigitalInput',
            device_id=mock_device_id.PHIDID_HUB0000,
            remote=False,
            remoteOnly=False,
        )

        # Assert
        assert result == channel

    def test_get_channel_usb_device(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock  # noqa: ARG002
    ) -> None:
        """Test getting channel for USB device (port 0)."""
        # Arrange
        channel = Mock()
        channel.getDeviceSerialNumber.return_value = 12345
        channel.getHubPort.return_value = 0  # USB device
        channel.getChannel.return_value = 0
        channel.getChannelClassName.return_value = 'PhidgetTemperatureSensor'
        channel.getDeviceID.return_value = 200
        channel.getIsLocal.return_value = True
        channel.getIsHubPortDevice.return_value = 0  # Not hub port device
        channel.getDeviceClass.return_value = 2

        phidget_manager_instance.attachedPhidgetChannels[channel] = True

        # Act
        result = phidget_manager_instance.getChannel(
            serial=12345,
            port=None,
            channel=0,
            phidget_class_name='PhidgetTemperatureSensor',
            device_id=200,
            remote=False,
            remoteOnly=False,
        )

        # Assert
        assert result == channel

    def test_get_channel_remote_device(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock  # noqa: ARG002
    ) -> None:
        """Test getting remote channel."""
        # Arrange
        channel = Mock()
        channel.getDeviceSerialNumber.return_value = 12345
        channel.getHubPort.return_value = 1
        channel.getChannel.return_value = 0
        channel.getChannelClassName.return_value = 'PhidgetTemperatureSensor'
        channel.getDeviceID.return_value = 200
        channel.getIsLocal.return_value = False  # Remote device
        channel.getIsHubPortDevice.return_value = 1
        channel.getDeviceClass.return_value = 2

        phidget_manager_instance.attachedPhidgetChannels[channel] = True

        # Act
        result = phidget_manager_instance.getChannel(
            serial=12345,
            port=1,
            channel=0,
            phidget_class_name='PhidgetTemperatureSensor',
            device_id=200,
            remote=True,
            remoteOnly=True,
        )

        # Assert
        assert result == channel

    def test_get_channel_no_match(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock  # noqa: ARG002
    ) -> None:
        """Test getting channel with no match."""
        # Arrange
        channel = Mock()
        channel.getDeviceSerialNumber.return_value = 12345
        channel.getHubPort.return_value = 1
        channel.getChannel.return_value = 0
        channel.getChannelClassName.return_value = 'PhidgetTemperatureSensor'
        channel.getDeviceID.return_value = 200
        channel.getIsLocal.return_value = True
        channel.getIsHubPortDevice.return_value = 1
        channel.getDeviceClass.return_value = 2

        phidget_manager_instance.attachedPhidgetChannels[channel] = True

        # Act
        result = phidget_manager_instance.getChannel(
            serial=99999,
            port=1,
            channel=0,  # Different serial
            phidget_class_name='PhidgetTemperatureSensor',
            device_id=200,
            remote=False,
            remoteOnly=False,
        )

        # Assert
        assert result is None

    def test_get_channel_with_exception(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock
    ) -> None:
        """Test getting channel with exception."""
        # Arrange
        channel = Mock()
        channel.getDeviceSerialNumber.side_effect = Exception('Test exception')
        phidget_manager_instance.attachedPhidgetChannels[channel] = True

        # Act
        result = phidget_manager_instance.getChannel(
            serial=12345,
            port=1,
            channel=0,
            phidget_class_name='PhidgetTemperatureSensor',
            device_id=200,
            remote=False,
            remoteOnly=False,
        )

        # Assert
        assert result is None
        mock_qsemaphore.release.assert_called_with(1)

    def test_reserve_serial_port_success(self, phidget_manager_instance: PhidgetManager) -> None:
        """Test reserving serial port successfully."""
        # Arrange
        channel = Mock()

        with patch(
            'artisanlib.phidgets.PhidgetManager.getChannel', return_value=channel
        ) as mock_get_channel, patch(
            'artisanlib.phidgets.PhidgetManager.reserveChannel'
        ) as mock_reserve_channel:

            # Act
            phidget_manager_instance.reserveSerialPort(
                serial=12345,
                port=1,
                channel=0,
                phidget_class_name='PhidgetTemperatureSensor',
                device_id=200,
                remote=False,
                remoteOnly=False,
            )

            # Assert
            mock_get_channel.assert_called_once_with(
                12345, 1, 0, 'PhidgetTemperatureSensor', 200, False, False
            )
            mock_reserve_channel.assert_called_once_with(channel)

    def test_reserve_serial_port_no_channel(self, phidget_manager_instance: PhidgetManager) -> None:
        """Test reserving serial port when no channel found."""
        # Arrange
        with patch(
            'artisanlib.phidgets.PhidgetManager.getChannel', return_value=None
        ) as mock_get_channel, patch(
            'artisanlib.phidgets.PhidgetManager.reserveChannel'
        ) as mock_reserve_channel:

            # Act
            phidget_manager_instance.reserveSerialPort(
                serial=12345,
                port=1,
                channel=0,
                phidget_class_name='PhidgetTemperatureSensor',
                device_id=200,
            )

            # Assert
            mock_get_channel.assert_called_once_with(
                12345, 1, 0, 'PhidgetTemperatureSensor', 200, False, False
            )
            mock_reserve_channel.assert_not_called()


class TestPhidgetManagerChannelReservation:
    """Test PhidgetManager channel reservation functionality."""

    def test_reserve_channel_simple(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock
    ) -> None:
        """Test reserving a simple channel."""
        # Arrange
        channel = Mock()
        channel.getIsHubPortDevice.return_value = 0  # Not a hub port device
        phidget_manager_instance.attachedPhidgetChannels[channel] = True

        # Act
        phidget_manager_instance.reserveChannel(channel)

        # Assert
        assert phidget_manager_instance.attachedPhidgetChannels[channel] is False
        mock_qsemaphore.acquire.assert_called_with(1)
        mock_qsemaphore.release.assert_called_with(1)

    def test_reserve_channel_hub_port_device(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock  # noqa: ARG002
    ) -> None:
        """Test reserving hub port device reserves all channels on same hub/port."""
        # Arrange
        hub_channel = Mock()
        hub_channel.getIsHubPortDevice.return_value = 1  # Hub port device
        hub_channel.getHub.return_value = 1000
        hub_channel.getHubPort.return_value = 1

        other_channel = Mock()
        other_channel.getHub.return_value = 1000
        other_channel.getHubPort.return_value = 1

        phidget_manager_instance.attachedPhidgetChannels[hub_channel] = True
        phidget_manager_instance.attachedPhidgetChannels[other_channel] = True

        # Act
        phidget_manager_instance.reserveChannel(hub_channel)

        # Assert
        assert phidget_manager_instance.attachedPhidgetChannels[hub_channel] is False
        assert phidget_manager_instance.attachedPhidgetChannels[other_channel] is False

    def test_reserve_channel_not_in_dict(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock
    ) -> None:
        """Test reserving channel not in attached channels dict."""
        # Arrange
        channel = Mock()

        # Act - Should not raise exception
        phidget_manager_instance.reserveChannel(channel)

        # Assert
        mock_qsemaphore.release.assert_called_with(1)

    def test_reserve_channel_with_exception(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock
    ) -> None:
        """Test reserving channel with exception."""
        # Arrange
        channel = Mock()
        channel.getIsHubPortDevice.side_effect = Exception('Test exception')
        phidget_manager_instance.attachedPhidgetChannels[channel] = True

        # Act - Should not raise exception
        phidget_manager_instance.reserveChannel(channel)

        # Assert
        mock_qsemaphore.release.assert_called_with(1)


class TestPhidgetManagerDeviceMatching:
    """Test PhidgetManager device matching functionality."""

    def test_get_first_matching_phidget_success(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock
    ) -> None:
        """Test getting first matching Phidget successfully."""
        # Arrange
        channel = Mock()
        channel.getDeviceSerialNumber.return_value = 12345
        channel.getHubPort.return_value = 1
        channel.getChannel.return_value = 0
        channel.getChannelClassName.return_value = 'PhidgetTemperatureSensor'
        channel.getDeviceID.return_value = 200
        channel.getIsLocal.return_value = True
        channel.getIsHubPortDevice.return_value = 1
        channel.getDeviceClass.return_value = 2

        phidget_manager_instance.attachedPhidgetChannels[channel] = True

        # Act
        serial, port = phidget_manager_instance.getFirstMatchingPhidget(
            phidget_class_name='PhidgetTemperatureSensor',
            device_id=200,
            channel=0,
            remote=False,
            remoteOnly=False,
        )

        # Assert
        assert serial == 12345
        assert port == 1
        mock_qsemaphore.acquire.assert_called_with(1)
        mock_qsemaphore.release.assert_called_with(1)

    def test_get_first_matching_phidget_hub_device(
        self,
        phidget_manager_instance: PhidgetManager,
        mock_device_id: Mock,
        mock_qsemaphore: Mock,  # noqa: ARG002
    ) -> None:
        """Test getting first matching hub device."""
        # Arrange
        channel = Mock()
        channel.getDeviceSerialNumber.return_value = 12345
        channel.getHubPort.return_value = 2
        channel.getChannel.return_value = 0
        channel.getChannelClassName.return_value = 'PhidgetDigitalInput'
        channel.getDeviceID.return_value = mock_device_id.PHIDID_HUB0000
        channel.getIsLocal.return_value = True
        channel.getIsHubPortDevice.return_value = 1
        channel.getDeviceClass.return_value = 2

        phidget_manager_instance.attachedPhidgetChannels[channel] = True

        # Act
        serial, port = phidget_manager_instance.getFirstMatchingPhidget(
            phidget_class_name='PhidgetDigitalInput',
            device_id=mock_device_id.PHIDID_HUB0000,
            channel=2,  # For hub devices, channel parameter matches hub port
            remote=False,
            remoteOnly=False,
        )

        # Assert
        assert serial == 12345
        assert port == 2

    def test_get_first_matching_phidget_usb_device(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock  # noqa: ARG002
    ) -> None:
        """Test getting first matching USB device."""
        # Arrange
        channel = Mock()
        channel.getDeviceSerialNumber.return_value = 12345
        channel.getHubPort.return_value = 0  # USB device
        channel.getChannel.return_value = 0
        channel.getChannelClassName.return_value = 'PhidgetTemperatureSensor'
        channel.getDeviceID.return_value = 200
        channel.getIsLocal.return_value = True
        channel.getIsHubPortDevice.return_value = 0  # Not hub port device
        channel.getDeviceClass.return_value = 2

        phidget_manager_instance.attachedPhidgetChannels[channel] = True

        # Act
        serial, port = phidget_manager_instance.getFirstMatchingPhidget(
            phidget_class_name='PhidgetTemperatureSensor',
            device_id=200,
            channel=0,
            remote=False,
            remoteOnly=False,
        )

        # Assert
        assert serial == 12345
        assert port is None  # USB devices return None for port

    def test_get_first_matching_phidget_with_filters(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock  # noqa: ARG002
    ) -> None:
        """Test getting first matching Phidget with serial and hubport filters."""
        # Arrange
        channel1 = Mock()
        channel1.getDeviceSerialNumber.return_value = 11111
        channel1.getHubPort.return_value = 1
        channel1.getChannel.return_value = 0
        channel1.getChannelClassName.return_value = 'PhidgetTemperatureSensor'
        channel1.getDeviceID.return_value = 200
        channel1.getIsLocal.return_value = True
        channel1.getIsHubPortDevice.return_value = 1
        channel1.getDeviceClass.return_value = 2

        channel2 = Mock()
        channel2.getDeviceSerialNumber.return_value = 22222
        channel2.getHubPort.return_value = 2
        channel2.getChannel.return_value = 0
        channel2.getChannelClassName.return_value = 'PhidgetTemperatureSensor'
        channel2.getDeviceID.return_value = 200
        channel2.getIsLocal.return_value = True
        channel2.getIsHubPortDevice.return_value = 1
        channel2.getDeviceClass.return_value = 2

        phidget_manager_instance.attachedPhidgetChannels[channel1] = True
        phidget_manager_instance.attachedPhidgetChannels[channel2] = True

        # Act
        serial, port = phidget_manager_instance.getFirstMatchingPhidget(
            phidget_class_name='PhidgetTemperatureSensor',
            device_id=200,
            channel=0,
            remote=False,
            remoteOnly=False,
            serial=22222,  # Filter by specific serial
            hubport=2,  # Filter by specific hub port
        )

        # Assert
        assert serial == 22222
        assert port == 2

    def test_get_first_matching_phidget_no_match(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock  # noqa: ARG002
    ) -> None:
        """Test getting first matching Phidget with no match."""
        # Arrange
        channel = Mock()
        channel.getDeviceSerialNumber.return_value = 12345
        channel.getHubPort.return_value = 1
        channel.getChannel.return_value = 0
        channel.getChannelClassName.return_value = 'PhidgetTemperatureSensor'
        channel.getDeviceID.return_value = 200
        channel.getIsLocal.return_value = True
        channel.getIsHubPortDevice.return_value = 1
        channel.getDeviceClass.return_value = 2

        phidget_manager_instance.attachedPhidgetChannels[channel] = False  # Not available

        # Act
        serial, port = phidget_manager_instance.getFirstMatchingPhidget(
            phidget_class_name='PhidgetTemperatureSensor',
            device_id=200,
            channel=0,
            remote=False,
            remoteOnly=False,
        )

        # Assert
        assert serial is None
        assert port is None

    def test_get_first_matching_phidget_sorted_by_serial(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock  # noqa: ARG002
    ) -> None:
        """Test that matching Phidgets are sorted by serial number."""
        # Arrange
        channel1 = Mock()
        channel1.getDeviceSerialNumber.return_value = 99999  # Higher serial
        channel1.getHubPort.return_value = 1
        channel1.getChannel.return_value = 0
        channel1.getChannelClassName.return_value = 'PhidgetTemperatureSensor'
        channel1.getDeviceID.return_value = 200
        channel1.getIsLocal.return_value = True
        channel1.getIsHubPortDevice.return_value = 1
        channel1.getDeviceClass.return_value = 2

        channel2 = Mock()
        channel2.getDeviceSerialNumber.return_value = 11111  # Lower serial
        channel2.getHubPort.return_value = 2
        channel2.getChannel.return_value = 0
        channel2.getChannelClassName.return_value = 'PhidgetTemperatureSensor'
        channel2.getDeviceID.return_value = 200
        channel2.getIsLocal.return_value = True
        channel2.getIsHubPortDevice.return_value = 1
        channel2.getDeviceClass.return_value = 2

        phidget_manager_instance.attachedPhidgetChannels[channel1] = True
        phidget_manager_instance.attachedPhidgetChannels[channel2] = True

        # Act
        serial, port = phidget_manager_instance.getFirstMatchingPhidget(
            phidget_class_name='PhidgetTemperatureSensor',
            device_id=200,
            channel=0,
            remote=False,
            remoteOnly=False,
        )

        # Assert
        assert serial == 11111  # Should return the lower serial number first
        assert port == 2

    def test_get_first_matching_phidget_with_exception(
        self, phidget_manager_instance: PhidgetManager, mock_qsemaphore: Mock
    ) -> None:
        """Test getting first matching Phidget with exception."""
        # Arrange
        channel = Mock()
        channel.getDeviceSerialNumber.side_effect = Exception('Test exception')
        phidget_manager_instance.attachedPhidgetChannels[channel] = True

        # Act
        serial, port = phidget_manager_instance.getFirstMatchingPhidget(
            phidget_class_name='PhidgetTemperatureSensor',
            device_id=200,
            channel=0,
            remote=False,
            remoteOnly=False,
        )

        # Assert
        assert serial is None
        assert port is None
        mock_qsemaphore.release.assert_called_with(1)
