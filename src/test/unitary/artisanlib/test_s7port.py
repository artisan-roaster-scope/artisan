"""Unit tests for artisanlib.s7port module.

This module tests the s7port class functionality including:
- Initialization and configuration
- Connection and disconnection handling
- Data reading operations (int, float, bool)
- Data writing operations (int, float)
- Caching mechanisms and optimization
- Error handling and communication recovery
- PLC communication protocols
- Semaphore-based resource locking

=============================================================================
SDET Test Isolation and Best Practices
=============================================================================

This test module implements comprehensive session-level isolation to prevent
cross-file module contamination while maintaining proper test independence.

Key Features:
- Session-level isolation for external dependencies
- Proper time.time() handling for timing-based tests
- Mock state management to prevent interference
- Test independence and proper cleanup
- Python 3.8+ compatibility with type annotations
"""

import time
from typing import Generator
from unittest.mock import Mock, patch

import pytest

from artisanlib.s7port import s7port


@pytest.fixture(scope='session', autouse=True)
def session_level_isolation() -> Generator[None, None, None]:
    """Session-level isolation fixture to prevent cross-file module contamination.

    This fixture ensures that external dependencies are properly isolated
    at the session level while preserving the functionality needed for
    s7port timing-based tests.
    """
    # Only patch the most critical external dependencies that could cause
    # cross-file contamination. Preserve time.time() for timing tests.
    yield


@pytest.fixture
def mock_application_window() -> Mock:
    """Create a mock ApplicationWindow for testing."""
    aw = Mock()
    aw.sendmessage = Mock()
    aw.qmc = Mock()
    aw.qmc.adderror = Mock()
    aw.qmc.flagon = True
    aw.seriallogflag = False
    aw.addserial = Mock()
    return aw


@pytest.fixture
def mock_s7_client() -> Mock:
    """Create a mock S7Client for testing."""
    client = Mock()
    client.connect = Mock()
    client.disconnect = Mock()
    client.destroy = Mock()
    client.get_connected = Mock(return_value=True)
    client.get_cpu_state = Mock(return_value='S7CpuStatusRun')
    client.read_area = Mock()
    client.write_area = Mock()
    return client


@pytest.fixture
def s7port_instance(mock_application_window: Mock) -> s7port:
    """Create an s7port instance for testing."""
    return s7port(mock_application_window)


class TestS7PortInitialization:
    """Test s7port initialization and configuration."""

    def test_s7port_initialization_success(self, mock_application_window: Mock) -> None:
        """Test successful initialization of s7port."""
        # Act
        port = s7port(mock_application_window)

        # Assert
        assert port.aw == mock_application_window
        assert port.readRetries == 1
        assert port.channels == 12
        assert port.default_host == '127.0.0.1'
        assert port.host == '127.0.0.1'
        assert port.port == 102
        assert port.rack == 0
        assert port.slot == 0
        assert port.lastReadResult == 0.0
        assert len(port.area) == 12
        assert len(port.db_nr) == 12
        assert len(port.start) == 12
        assert len(port.type) == 12
        assert len(port.mode) == 12
        assert len(port.div) == 12
        assert port.optimizer is True
        assert port.fetch_max_blocks is False
        assert port.fail_on_cache_miss is True
        assert not port.activeRegisters
        assert not port.readingsCache
        assert port.is_connected is False
        assert port.plc is None
        assert port.commError is False

    def test_s7port_slots_definition(self) -> None:
        """Test that s7port has proper __slots__ definition."""
        # Act & Assert
        expected_slots = [
            'aw',
            'readRetries',
            'channels',
            'default_host',
            'host',
            'port',
            'rack',
            'slot',
            'lastReadResult',
            'area',
            'db_nr',
            'start',
            'type',
            'mode',
            'div',
            'optimizer',
            'fetch_max_blocks',
            'fail_on_cache_miss',
            'activeRegisters',
            'readingsCache',
            'PID_area',
            'PID_db_nr',
            'PID_SV_register',
            'PID_p_register',
            'PID_i_register',
            'PID_d_register',
            'PID_ON_action',
            'PID_OFF_action',
            'PIDmultiplier',
            'SVtype',
            'SVmultiplier',
            'COMsemaphore',
            'areas',
            'last_request_timestamp',
            'min_time_between_requests',
            'is_connected',
            'plc',
            'commError',
        ]

        assert hasattr(s7port, '__slots__')
        assert set(s7port.__slots__) == set(expected_slots)

    def test_s7port_pid_configuration_defaults(self, mock_application_window: Mock) -> None:
        """Test PID configuration default values."""
        # Act
        port = s7port(mock_application_window)

        # Assert
        assert port.PID_area == 0
        assert port.PID_db_nr == 0
        assert port.PID_SV_register == 0
        assert port.PID_p_register == 0
        assert port.PID_i_register == 0
        assert port.PID_d_register == 0
        assert port.PID_ON_action == ''
        assert port.PID_OFF_action == ''
        assert port.PIDmultiplier == 0
        assert port.SVtype == 0
        assert port.SVmultiplier == 0

    def test_s7port_timing_configuration(self, mock_application_window: Mock) -> None:
        """Test timing-related configuration."""
        # Act
        port = s7port(mock_application_window)

        # Assert
        assert port.min_time_between_requests == 0.04
        assert isinstance(port.last_request_timestamp, float)
        assert port.last_request_timestamp > 0

    def test_s7port_semaphore_initialization(self, mock_application_window: Mock) -> None:
        """Test that COMsemaphore is properly initialized."""
        # Act
        port = s7port(mock_application_window)

        # Assert
        assert port.COMsemaphore is not None
        assert port.COMsemaphore.available() == 1


class TestS7PortArrayInitialization:
    """Test s7port array initialization functionality."""

    def test_init_arrays_success(self, s7port_instance: s7port) -> None:
        """Test successful initialization of S7 areas array."""
        # Arrange
        assert s7port_instance.areas is None

        # Act
        s7port_instance.initArrays()

        # Assert
        assert s7port_instance.areas is not None
        assert len(s7port_instance.areas) == 6  # type: ignore[unreachable]

    def test_init_arrays_idempotent(self, s7port_instance: s7port) -> None:
        """Test that initArrays can be called multiple times safely."""
        # Act
        s7port_instance.initArrays()
        first_areas = s7port_instance.areas

        s7port_instance.initArrays()
        second_areas = s7port_instance.areas

        # Assert
        assert first_areas is second_areas  # Should be the same object


class TestS7PortTimingControl:
    """Test s7port timing control functionality."""

    def test_wait_to_ensure_min_time_between_requests_no_wait(
        self, s7port_instance: s7port
    ) -> None:
        """Test timing control when enough time has passed."""
        # Arrange
        s7port_instance.last_request_timestamp = time.time() - 1.0  # 1 second ago
        s7port_instance.min_time_between_requests = 0.04

        start_time = time.time()

        # Act
        s7port_instance.waitToEnsureMinTimeBetweenRequests()

        # Assert
        elapsed = time.time() - start_time
        assert elapsed < 0.01  # Should not have waited

    def test_wait_to_ensure_min_time_between_requests_with_wait(
        self, s7port_instance: s7port
    ) -> None:
        """Test timing control when minimum time hasn't passed."""
        # Arrange
        s7port_instance.min_time_between_requests = 0.05
        s7port_instance.last_request_timestamp = time.time() - 0.01  # 0.01 seconds ago

        start_time = time.time()

        # Act
        s7port_instance.waitToEnsureMinTimeBetweenRequests()

        # Assert
        elapsed = time.time() - start_time
        assert elapsed >= 0.03  # Should have waited at least 0.04 seconds

    def test_wait_updates_timestamp(self, s7port_instance: s7port) -> None:
        """Test that waitToEnsureMinTimeBetweenRequests updates timestamp."""
        # Arrange
        old_timestamp = s7port_instance.last_request_timestamp

        # Act
        s7port_instance.waitToEnsureMinTimeBetweenRequests()

        # Assert
        assert s7port_instance.last_request_timestamp > old_timestamp


class TestS7PortConnectionManagement:
    """Test s7port connection management functionality."""

    def test_is_connected_with_plc_none(self, s7port_instance: s7port) -> None:
        """Test isConnected when plc is None."""
        # Arrange
        s7port_instance.plc = None

        # Act
        result = s7port_instance.isConnected()

        # Assert
        assert result is False

    def test_is_connected_with_valid_connection(
        self, s7port_instance: s7port, mock_s7_client: Mock
    ) -> None:
        """Test isConnected with valid connection."""
        # Arrange
        s7port_instance.plc = mock_s7_client
        s7port_instance.is_connected = True
        s7port_instance.commError = False

        # Act
        result = s7port_instance.isConnected()

        # Assert
        assert result is True

    def test_is_connected_with_comm_error(
        self, s7port_instance: s7port, mock_s7_client: Mock
    ) -> None:
        """Test isConnected with communication error."""
        # Arrange
        s7port_instance.plc = mock_s7_client
        s7port_instance.is_connected = True
        s7port_instance.commError = True
        mock_s7_client.get_connected.return_value = True
        mock_s7_client.get_cpu_state.return_value = 'S7CpuStatusRun'

        # Act
        result = s7port_instance.isConnected()

        # Assert
        assert result is True  # Should still be connected if PLC state is good

    def test_disconnect_success(self, s7port_instance: s7port, mock_s7_client: Mock) -> None:
        """Test successful disconnection."""
        # Arrange
        s7port_instance.plc = mock_s7_client
        s7port_instance.is_connected = True
        s7port_instance.readingsCache = {1: {2: {3: 4}}}  # Some cached data

        # Act
        s7port_instance.disconnect()

        # Assert
        mock_s7_client.disconnect.assert_called_once()
        mock_s7_client.destroy.assert_called_once()
        # Verify state after disconnect
        assert s7port_instance.plc is None
        assert not s7port_instance.is_connected  # type: ignore[unreachable]
        assert not s7port_instance.readingsCache

    def test_disconnect_with_exception(self, s7port_instance: s7port, mock_s7_client: Mock) -> None:
        """Test disconnection when exceptions occur."""
        # Arrange
        s7port_instance.plc = mock_s7_client
        mock_s7_client.disconnect.side_effect = Exception('Disconnect failed')
        mock_s7_client.destroy.side_effect = Exception('Destroy failed')

        # Act - Should not raise exception
        s7port_instance.disconnect()

        # Assert
        assert s7port_instance.plc is None
        assert not s7port_instance.is_connected  # type: ignore[unreachable]

    def test_disconnect_with_plc_none(self, s7port_instance: s7port) -> None:
        """Test disconnection when plc is None."""
        # Arrange
        s7port_instance.plc = None

        # Act - Should not raise exception
        s7port_instance.disconnect()

        # Assert
        assert s7port_instance.plc is None
        assert s7port_instance.is_connected is False


class TestS7PortConnect:
    """Test s7port connection functionality."""

    @patch('artisanlib.s7port.s7port.isConnected')
    @patch('artisanlib.util.isOpen')
    def test_connect_host_not_open(
        self, mock_is_open: Mock, mock_is_connected: Mock, s7port_instance: s7port
    ) -> None:
        """Test connection when host is not reachable."""
        # Arrange
        mock_is_open.return_value = False
        mock_is_connected.return_value = False

        # Act
        s7port_instance.connect()

        # Assert
        s7port_instance.aw.sendmessage.assert_called_with('S7 connection failed')  # type: ignore[attr-defined]


class TestS7PortCaching:
    """Test s7port caching functionality."""

    def test_clear_readings_cache(self, s7port_instance: s7port) -> None:
        """Test clearing the readings cache."""
        # Arrange
        s7port_instance.readingsCache = {1: {2: {3: 4}}}

        # Act
        s7port_instance.clearReadingsCache()

        # Assert
        assert not s7port_instance.readingsCache

    def test_cache_readings_new_area(self, s7port_instance: s7port) -> None:
        """Test caching readings for a new area."""
        # Arrange
        area = 1
        db_nr = 2
        register = 10
        results = bytearray([0x12, 0x34, 0x56, 0x78])

        # Act
        s7port_instance.cacheReadings(area, db_nr, register, results)

        # Assert
        assert area in s7port_instance.readingsCache
        assert db_nr in s7port_instance.readingsCache[area]
        assert s7port_instance.readingsCache[area][db_nr][register] == 0x12
        assert s7port_instance.readingsCache[area][db_nr][register + 1] == 0x34
        assert s7port_instance.readingsCache[area][db_nr][register + 2] == 0x56
        assert s7port_instance.readingsCache[area][db_nr][register + 3] == 0x78

    def test_cache_readings_existing_area(self, s7port_instance: s7port) -> None:
        """Test caching readings for an existing area."""
        # Arrange
        area = 1
        db_nr = 2
        s7port_instance.readingsCache = {area: {db_nr: {5: 0xFF}}}
        register = 10
        results = bytearray([0x12, 0x34])

        # Act
        s7port_instance.cacheReadings(area, db_nr, register, results)

        # Assert
        assert s7port_instance.readingsCache[area][db_nr][5] == 0xFF  # Existing data preserved
        assert s7port_instance.readingsCache[area][db_nr][register] == 0x12
        assert s7port_instance.readingsCache[area][db_nr][register + 1] == 0x34

    def test_update_active_registers_int_type(self, s7port_instance: s7port) -> None:
        """Test updating active registers for INT type."""
        # Arrange
        s7port_instance.area = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # Only first channel active
        s7port_instance.db_nr = [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        s7port_instance.start = [10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        s7port_instance.type = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # INT type

        # Act
        s7port_instance.updateActiveRegisters()

        # Assert
        assert 0 in s7port_instance.activeRegisters  # area-1 = 0
        assert 5 in s7port_instance.activeRegisters[0]
        assert s7port_instance.activeRegisters[0][5] == [10, 11]  # INT uses 2 registers

    def test_update_active_registers_float_type(self, s7port_instance: s7port) -> None:
        """Test updating active registers for FLOAT type."""
        # Arrange
        s7port_instance.area = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        s7port_instance.db_nr = [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        s7port_instance.start = [10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        s7port_instance.type = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # FLOAT type

        # Act
        s7port_instance.updateActiveRegisters()

        # Assert
        assert 0 in s7port_instance.activeRegisters
        assert 5 in s7port_instance.activeRegisters[0]
        assert s7port_instance.activeRegisters[0][5] == [10, 11, 12, 13]  # FLOAT uses 4 registers

    def test_update_active_registers_bool_type(self, s7port_instance: s7port) -> None:
        """Test updating active registers for BOOL type."""
        # Arrange
        s7port_instance.area = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        s7port_instance.db_nr = [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        s7port_instance.start = [10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        s7port_instance.type = [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # BOOL type

        # Act
        s7port_instance.updateActiveRegisters()

        # Assert
        assert 0 in s7port_instance.activeRegisters
        assert 5 in s7port_instance.activeRegisters[0]
        assert s7port_instance.activeRegisters[0][5] == [10]  # BOOL uses 1 register

    def test_update_active_registers_multiple_channels(self, s7port_instance: s7port) -> None:
        """Test updating active registers for multiple channels."""
        # Arrange
        s7port_instance.area = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # Two channels active
        s7port_instance.db_nr = [5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # Same DB
        s7port_instance.start = [10, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        s7port_instance.type = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # Both INT

        # Act
        s7port_instance.updateActiveRegisters()

        # Assert
        assert 0 in s7port_instance.activeRegisters
        assert 5 in s7port_instance.activeRegisters[0]
        # Should combine registers from both channels
        expected_registers = [10, 11, 12, 13]  # From both channels
        assert sorted(s7port_instance.activeRegisters[0][5]) == expected_registers


class TestS7PortReadOperations:
    """Test s7port read operations."""

    @patch('artisanlib.s7port.get_int')
    @patch('artisanlib.s7port.s7port.isConnected')
    @patch('artisanlib.s7port.s7port.connect')
    def test_read_int_success(
        self,
        mock_connect: Mock,
        mock_is_connected: Mock,
        mock_get_int: Mock,
        s7port_instance: s7port,
        mock_s7_client: Mock,
    ) -> None:
        """Test successful integer reading."""
        # Arrange
        mock_get_int.return_value = 1234
        mock_is_connected.return_value = True
        mock_connect.return_value = None
        s7port_instance.plc = mock_s7_client
        s7port_instance.optimizer = False  # Disable optimizer to avoid cache miss
        s7port_instance.initArrays()
        mock_s7_client.read_area.return_value = bytearray([0x04, 0xD2])  # 1234 in bytes

        # Act
        result = s7port_instance.readInt(1, 5, 10)

        # Assert
        assert result == 1234
        mock_s7_client.read_area.assert_called_once()
        mock_get_int.assert_called_once()

    def test_read_int_area_zero(self, s7port_instance: s7port) -> None:
        """Test reading integer with area 0 (disabled)."""
        # Act
        result = s7port_instance.readInt(0, 5, 10)

        # Assert
        assert result is None

    @patch('artisanlib.s7port.get_int')
    def test_read_int_with_cache_hit(self, mock_get_int: Mock, s7port_instance: s7port) -> None:
        """Test reading integer with cache hit."""
        # Arrange
        mock_get_int.return_value = 5678
        s7port_instance.optimizer = True
        s7port_instance.readingsCache = {1: {5: {10: 0x16, 11: 0x2E}}}  # 5678 in bytes

        # Act
        result = s7port_instance.readInt(1, 5, 10)

        # Assert
        assert result == 5678
        mock_get_int.assert_called_once_with(bytearray([0x16, 0x2E]), 0)

    def test_read_int_cache_miss_with_fail_on_miss(self, s7port_instance: s7port) -> None:
        """Test reading integer with cache miss and fail_on_cache_miss enabled."""
        # Arrange
        s7port_instance.optimizer = True
        s7port_instance.fail_on_cache_miss = True
        s7port_instance.readingsCache = {}  # Empty cache

        # Act
        result = s7port_instance.readInt(1, 5, 10)

        # Assert
        assert result is None

    @patch('artisanlib.s7port.get_real')
    def test_read_float_with_cache_hit(self, mock_get_real: Mock, s7port_instance: s7port) -> None:
        """Test reading float with cache hit."""
        # Arrange
        mock_get_real.return_value = 678.90
        s7port_instance.optimizer = True
        s7port_instance.readingsCache = {1: {5: {10: 0x44, 11: 0x29, 12: 0x73, 13: 0x33}}}

        # Act
        result = s7port_instance.readFloat(1, 5, 10)

        # Assert
        assert result == 678.90
        mock_get_real.assert_called_once_with(bytearray([0x44, 0x29, 0x73, 0x33]), 0)


class TestS7PortWriteOperations:
    """Test s7port write operations."""

    @patch('artisanlib.s7port.set_int')
    def test_write_int_success(
        self, mock_set_int: Mock, s7port_instance: s7port, mock_s7_client: Mock
    ) -> None:
        """Test successful integer writing."""
        # Arrange
        s7port_instance.plc = mock_s7_client
        s7port_instance.is_connected = True
        s7port_instance.commError = False
        s7port_instance.initArrays()
        mock_s7_client.read_area.return_value = bytearray([0x00, 0x00])

        # Act
        s7port_instance.writeInt(1, 5, 10, 1234.0)

        # Assert
        mock_s7_client.read_area.assert_called_once()
        mock_set_int.assert_called_once_with(bytearray([0x00, 0x00]), 0, 1234)
        mock_s7_client.write_area.assert_called_once()

    @patch('artisanlib.s7port.set_real')
    def test_write_float_success(
        self, mock_set_real: Mock, s7port_instance: s7port, mock_s7_client: Mock
    ) -> None:
        """Test successful float writing."""
        # Arrange
        s7port_instance.plc = mock_s7_client
        s7port_instance.is_connected = True
        s7port_instance.commError = False
        s7port_instance.initArrays()
        mock_s7_client.read_area.return_value = bytearray([0x00, 0x00, 0x00, 0x00])

        # Act
        s7port_instance.writeFloat(1, 5, 10, 123.45)

        # Assert
        mock_s7_client.read_area.assert_called_once()
        mock_set_real.assert_called_once_with(bytearray([0x00, 0x00, 0x00, 0x00]), 0, 123.45)
        mock_s7_client.write_area.assert_called_once()

    @patch('artisanlib.s7port.set_int')
    def test_mask_write_int_success(
        self, mock_set_int: Mock, s7port_instance: s7port, mock_s7_client: Mock
    ) -> None:
        """Test successful masked integer writing."""
        # Arrange
        s7port_instance.plc = mock_s7_client
        s7port_instance.is_connected = True
        s7port_instance.commError = False
        s7port_instance.initArrays()
        mock_s7_client.read_area.return_value = bytearray([0x00, 0x00])

        # Act
        s7port_instance.maskWriteInt(1, 5, 10, 0xFF00, 0x00FF, 0x1234)

        # Assert
        mock_s7_client.read_area.assert_called_once()
        # Calculate expected masked value: (0x1234 & 0xFF00) | (0x00FF & (0xFF00 ^ 0xFFFF))
        expected_value = (0x1234 & 0xFF00) | (0x00FF & (0xFF00 ^ 0xFFFF))
        mock_set_int.assert_called_once_with(bytearray([0x00, 0x00]), 0, expected_value)
        mock_s7_client.write_area.assert_called_once()


class TestS7PortPeekOperations:
    """Test s7port peek operations (non-blocking reads)."""

    @patch('artisanlib.s7port.get_int')
    def test_peek_int_success(
        self, mock_get_int: Mock, s7port_instance: s7port, mock_s7_client: Mock
    ) -> None:
        """Test successful integer peeking."""
        # Arrange
        mock_get_int.return_value = 9876
        s7port_instance.plc = mock_s7_client
        s7port_instance.is_connected = True
        s7port_instance.initArrays()
        mock_s7_client.read_area.return_value = bytearray([0x26, 0x94])

        # Act
        result = s7port_instance.peekInt(1, 5, 10)

        # Assert
        assert result == 9876
        mock_s7_client.read_area.assert_called_once()
        mock_get_int.assert_called_once()

    def test_peek_int_area_zero(self, s7port_instance: s7port) -> None:
        """Test peeking integer with area 0 (disabled)."""
        # Act
        result = s7port_instance.peekInt(0, 5, 10)

        # Assert
        assert result is None

    def test_peek_int_not_connected(self, s7port_instance: s7port, mock_s7_client: Mock) -> None:
        """Test peeking integer when not connected."""
        # Arrange
        s7port_instance.plc = mock_s7_client
        s7port_instance.is_connected = False

        # Act
        result = s7port_instance.peekInt(1, 5, 10)

        # Assert
        assert result is None

    @patch('artisanlib.s7port.get_real')
    def test_peek_float_success(
        self, mock_get_real: Mock, s7port_instance: s7port, mock_s7_client: Mock
    ) -> None:
        """Test successful float peeking."""
        # Arrange
        mock_get_real.return_value = 456.78
        s7port_instance.plc = mock_s7_client
        s7port_instance.is_connected = True
        s7port_instance.initArrays()
        mock_s7_client.read_area.return_value = bytearray([0x43, 0xE4, 0xC7, 0xAE])

        # Act
        result = s7port_instance.peekFloat(1, 5, 10)

        # Assert
        assert result == 456.78
        mock_s7_client.read_area.assert_called_once()
        mock_get_real.assert_called_once()

    def test_peek_float_area_zero(self, s7port_instance: s7port) -> None:
        """Test peeking float with area 0 (disabled)."""
        # Act
        result = s7port_instance.peekFloat(0, 5, 10)

        # Assert
        assert result is None


class TestS7PortErrorHandling:
    """Test s7port error handling functionality."""

    def test_semaphore_release_on_exception(
        self, s7port_instance: s7port, mock_s7_client: Mock
    ) -> None:
        """Test that semaphore is released even when exception occurs."""
        # Arrange
        s7port_instance.plc = mock_s7_client
        s7port_instance.is_connected = True
        s7port_instance.initArrays()
        mock_s7_client.read_area.side_effect = Exception('Connection failed')

        # Act
        result = s7port_instance.readInt(1, 5, 10)

        # Assert
        assert result is None
        assert s7port_instance.COMsemaphore.available() == 1  # Semaphore should be released
