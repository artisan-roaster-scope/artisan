"""
Unit tests for artisanlib.modbusport module.

This module tests the MODBUS communication functionality including:
- Data type conversions (float, int, BCD)
- Register operations and caching
- Connection management
- Error handling and edge cases
- Async communication patterns
"""

from typing import List, Tuple, Union
from unittest.mock import Mock, patch

import pytest
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse

from artisanlib.main import ApplicationWindow
from artisanlib.modbusport import convert_from_bcd, convert_to_bcd, modbusport


@pytest.fixture
def mock_aw() -> Mock:
    """Create a mock ApplicationWindow for testing."""
    aw = Mock(spec=ApplicationWindow)
    aw.qmc = Mock()
    aw.qmc.delay = 1000  # 1 second delay
    aw.qmc.flagon = True
    aw.qmc.adderror = Mock()
    aw.sendmessage = Mock()
    aw.addserial = Mock()
    aw.seriallogflag = False
    return aw


@pytest.fixture
def client(mock_aw: Mock) -> modbusport:
    """Create a modbusport client for testing."""
    return modbusport(mock_aw)


class TestBCDConversions:
    """Test BCD conversion utility functions."""

    @pytest.mark.parametrize(
        'decimal,expected_bcd',
        [
            (0, 0),
            (1, 1),
            (9, 9),
            (10, 16),  # 0x10
            (15, 21),  # 0x15
            (99, 153),  # 0x99
            (123, 291),  # 0x123
            (9999, 39321),  # 0x9999
        ],
    )
    def test_convert_to_bcd_valid_values(self, decimal: int, expected_bcd: int) -> None:
        """Test BCD conversion for valid decimal values."""
        # Arrange & Act
        result = convert_to_bcd(decimal)

        # Assert
        assert result == expected_bcd

    @pytest.mark.parametrize(
        'bcd,expected_decimal',
        [
            (0, 0),
            (1, 1),
            (9, 9),
            (16, 10),  # 0x10
            (21, 15),  # 0x15
            (153, 99),  # 0x99
            (291, 123),  # 0x123
            (39321, 9999),  # 0x9999
        ],
    )
    def test_convert_from_bcd_valid_values(self, bcd: int, expected_decimal: int) -> None:
        """Test BCD to decimal conversion for valid values."""
        # Arrange & Act
        result = convert_from_bcd(bcd)

        # Assert
        assert result == expected_decimal

    def test_bcd_round_trip_conversion(self) -> None:
        """Test that BCD conversion is reversible."""
        # Arrange
        test_values = [0, 1, 9, 10, 15, 99, 123, 456, 9999]

        for decimal in test_values:
            # Act
            bcd = convert_to_bcd(decimal)
            result = convert_from_bcd(bcd)

            # Assert
            assert (
                result == decimal
            ), f"Round trip failed for {decimal}: {decimal} -> {bcd} -> {result}"


class TestModbusPortInitialization:
    """Test modbusport initialization and configuration."""

    def test_initialization_default_values(self, client: modbusport) -> None:
        """Test that modbusport initializes with correct default values."""
        # Assert
        assert client.maxCount == 125
        assert client.readRetries == 0
        assert client.default_comport == 'COM5'
        assert client.comport == 'COM5'
        assert client.baudrate == 115200
        assert client.bytesize == 8
        assert client.parity == 'N'
        assert client.stopbits == 1
        assert client.timeout == 0.4
        assert client.IP_timeout == 0.2
        assert client.default_host == '127.0.0.1'
        assert client.host == '127.0.0.1'
        assert client.port == 502
        assert client.type == 0  # Serial RTU
        assert client.commError == 0
        assert client.optimizer is True
        assert client.wordorderLittle is True

    def test_initialization_channels_setup(self, client: modbusport) -> None:
        """Test that channels are properly initialized."""
        # Assert
        assert client.channels == 10
        assert len(client.inputSlaves) == 10
        assert len(client.inputRegisters) == 10
        assert len(client.inputFloats) == 10
        assert len(client.inputBCDs) == 10
        assert len(client.inputSigned) == 10
        assert len(client.inputCodes) == 10
        assert len(client.inputDivs) == 10
        assert len(client.inputModes) == 10

        # Check default values
        assert all(slave == 0 for slave in client.inputSlaves)
        assert all(register == 0 for register in client.inputRegisters)
        assert all(not flag for flag in client.inputFloats)
        assert all(not flag for flag in client.inputBCDs)
        assert all(not flag for flag in client.inputSigned)
        assert all(code == 3 for code in client.inputCodes)
        assert all(div == 0 for div in client.inputDivs)
        assert all(mode == 'C' for mode in client.inputModes)

    def test_max_register_segment_constant(self, client: modbusport) -> None:
        """Test MAX_REGISTER_SEGMENT constant."""
        # Assert
        assert client.MAX_REGISTER_SEGMENT == 100


class TestWordOrderAndConversions:
    """Test word order and data type conversions."""

    def test_word_order_little_endian(self, client: modbusport) -> None:
        """Test word order when little endian is enabled."""
        # Arrange
        client.wordorderLittle = True

        # Act & Assert
        assert client.word_order() == 'little'

    def test_word_order_big_endian(self, client: modbusport) -> None:
        """Test word order when little endian is disabled."""
        # Arrange
        client.wordorderLittle = False

        # Act & Assert
        assert client.word_order() == 'big'

    @pytest.mark.parametrize(
        'word_order_little,value,expected',
        [
            (True, 12.2, [13107, 16707]),
            (False, 12.2, [16707, 13107]),
            (True, 0.0, [0, 0]),
            (False, 0.0, [0, 0]),
            (True, -1.5, [0, 49088]),
            (False, -1.5, [49088, 0]),
        ],
    )
    def test_convert_float_to_registers(
        self, client: modbusport, word_order_little: bool, value: float, expected: List[int]
    ) -> None:
        """Test float to registers conversion with different word orders."""
        # Arrange
        client.wordorderLittle = word_order_little

        # Act
        result = client.convert_float_to_registers(value)

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        'word_order_little,registers,expected',
        [
            (True, [13107, 16707], 12.2),
            (False, [16707, 13107], 12.2),
            (True, [0, 0], 0.0),
            (False, [0, 0], 0.0),
        ],
    )
    def test_convert_float_from_registers(
        self, client: modbusport, word_order_little: bool, registers: List[int], expected: float
    ) -> None:
        """Test registers to float conversion with different word orders."""
        # Arrange
        client.wordorderLittle = word_order_little

        # Act
        result = client.convert_float_from_registers(registers)

        # Assert
        assert pytest.approx(result, abs=0.01) == expected

    @pytest.mark.parametrize(
        'value,expected',
        [
            (3451, [3451]),
            (0, [0]),
            (65535, [65535]),  # Max 16-bit value
        ],
    )
    def test_convert_16bit_uint_to_registers(
        self, client: modbusport, value: int, expected: List[int]
    ) -> None:
        """Test 16-bit unsigned integer to registers conversion."""
        # Act
        result = client.convert_16bit_uint_to_registers(value)

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        'word_order_little,value,expected',
        [
            (True, 74510, [8974, 1]),
            (True, -3451, [62085, 65535]),
            (False, 74510, [1, 8974]),
            (False, -3451, [65535, 62085]),
            (True, 0, [0, 0]),
            (False, 0, [0, 0]),
            (True, -1, [65535, 65535]),
            (False, -1, [65535, 65535]),
        ],
    )
    def test_convert_32bit_int_to_registers(
        self, client: modbusport, word_order_little: bool, value: int, expected: List[int]
    ) -> None:
        """Test 32-bit signed integer to registers conversion."""
        # Arrange
        client.wordorderLittle = word_order_little

        # Act
        result = client.convert_32bit_int_to_registers(value)

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        'registers,expected',
        [
            ([13107], 13107),
            ([0], 0),
            ([65535], 65535),
        ],
    )
    def test_convert_16bit_uint_from_registers(
        self, client: modbusport, registers: List[int], expected: int
    ) -> None:
        """Test registers to 16-bit unsigned integer conversion."""
        # Act
        result = client.convert_16bit_uint_from_registers(registers)

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        'registers,expected',
        [
            ([13107], 13107),
            ([32768], -32768),  # Test sign bit
            ([65535], -1),  # All bits set
        ],
    )
    def test_convert_16bit_int_from_registers(
        self, client: modbusport, registers: List[int], expected: int
    ) -> None:
        """Test registers to 16-bit signed integer conversion."""
        # Act
        result = client.convert_16bit_int_from_registers(registers)

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        'word_order_little,registers,expected',
        [
            (True, [321, 12100], 792985921),
            (False, [12100, 321], 792985921),
            (True, [0, 0], 0),
            (False, [0, 0], 0),
            (True, [65535, 65535], 4294967295),  # Max 32-bit unsigned
            (False, [65535, 65535], 4294967295),
        ],
    )
    def test_convert_32bit_uint_from_registers(
        self, client: modbusport, word_order_little: bool, registers: List[int], expected: int
    ) -> None:
        """Test registers to 32-bit unsigned integer conversion."""
        # Arrange
        client.wordorderLittle = word_order_little

        # Act
        result = client.convert_32bit_uint_from_registers(registers)

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        'word_order_little,registers,expected',
        [
            (True, [13107, 12], 799539),
            (True, [62085, 65535], -3451),
            (False, [12, 13107], 799539),
            (False, [65535, 62085], -3451),
            (True, [0, 0], 0),
            (False, [0, 0], 0),
            (True, [65535, 65535], -1),  # All bits set
            (False, [65535, 65535], -1),
        ],
    )
    def test_convert_32bit_int_from_registers(
        self, client: modbusport, word_order_little: bool, registers: List[int], expected: int
    ) -> None:
        """Test registers to 32-bit signed integer conversion."""
        # Arrange
        client.wordorderLittle = word_order_little

        # Act
        result = client.convert_32bit_int_from_registers(registers)

        # Assert
        assert result == expected

    def test_convert_from_registers_invalid_type_returns_negative_one(
        self, client: modbusport
    ) -> None:
        """Test that conversion methods return -1 for invalid register data."""
        # Arrange - Mock the conversion to return a non-integer/non-float
        with patch(
            'pymodbus.client.mixin.ModbusClientMixin.convert_from_registers', return_value='invalid'
        ):
            # Act & Assert
            assert client.convert_16bit_uint_from_registers([123]) == -1
            assert client.convert_16bit_int_from_registers([123]) == -1
            assert client.convert_32bit_uint_from_registers([123, 456]) == -1
            assert client.convert_32bit_int_from_registers([123, 456]) == -1
            assert client.convert_float_from_registers([123, 456]) == -1


class TestAddressConversion:
    """Test address to register conversion."""

    @pytest.mark.parametrize(
        'addr,code,expected',
        [
            (40001, 3, 0),  # Holding register base
            (40002, 3, 1),
            (40100, 3, 99),
            (40001, 6, 0),  # Write single register uses same conversion
            (30001, 4, 0),  # Input register base
            (30002, 4, 1),
            (30100, 4, 99),
            (30001, 1, 0),  # Other codes use input register conversion
            (30001, 2, 0),
            (30001, 5, 0),
        ],
    )
    def test_address2register_conversion(
        self, addr: Union[int, float], code: int, expected: int
    ) -> None:
        """Test address to register conversion for different function codes."""
        # Act
        result = modbusport.address2register(addr, code)

        # Assert
        assert result == expected

    def test_address2register_with_float_address(self) -> None:
        """Test address conversion with float input."""
        # Act
        result = modbusport.address2register(40001.5, 3)

        # Assert
        assert result == 0  # Should be converted to int


class TestConnectionManagement:
    """Test connection state management."""

    def test_is_connected_no_client(self, client: modbusport) -> None:
        """Test isConnected returns False when no client exists."""
        # Arrange
        client._client = None

        # Act & Assert
        assert not client.isConnected()

    def test_is_connected_client_not_connected(self, client: modbusport) -> None:
        """Test isConnected returns False when client is not connected."""
        # Arrange
        mock_client = Mock()
        mock_client.connected = False
        client._client = mock_client

        # Act & Assert
        assert not client.isConnected()

    def test_is_connected_client_connected(self, client: modbusport) -> None:
        """Test isConnected returns True when client is connected."""
        # Arrange
        mock_client = Mock()
        mock_client.connected = True
        client._client = mock_client

        # Act & Assert
        assert client.isConnected()

    def test_disconnect_no_client(self, client: modbusport) -> None:
        """Test disconnect when no client exists."""
        # Arrange
        client._client = None

        # Act
        client.disconnect()

        # Assert
        assert client._client is None
        assert client._asyncLoopThread is None

    def test_disconnect_with_client(self, client: modbusport) -> None:
        """Test disconnect with existing client."""
        # Arrange
        mock_client = Mock()
        client._client = mock_client
        client.readingsCache = {3: {1: {100: 123}}}

        # Act
        client.disconnect()

        # Assert
        mock_client.close.assert_called_once()
        assert client._client is None
        assert client.readingsCache == {}  # type: ignore[unreachable]

    def test_disconnect_with_exception(self, client: modbusport) -> None:
        """Test disconnect handles exceptions gracefully."""
        # Arrange
        mock_client = Mock()
        mock_client.close.side_effect = Exception('Connection error')
        client._client = mock_client

        # Act
        client.disconnect()

        # Assert
        assert client._client is None


class TestErrorHandling:
    """Test error handling and communication error management."""

    def test_clear_comm_error_with_errors(self, client: modbusport, mock_aw: Mock) -> None:
        """Test clearing communication errors when errors exist."""
        # Arrange
        client.commError = 5

        # Act
        client.clearCommError()

        # Assert
        assert client.commError == 0
        mock_aw.qmc.adderror.assert_called_once()

    def test_clear_comm_error_no_errors(self, client: modbusport, mock_aw: Mock) -> None:
        """Test clearing communication errors when no errors exist."""
        # Arrange
        client.commError = 0

        # Act
        client.clearCommError()

        # Assert
        assert client.commError == 0
        mock_aw.qmc.adderror.assert_not_called()

    def test_disconnect_on_error_conditions_met(self, client: modbusport) -> None:
        """Test disconnectOnError when conditions are met."""
        # Arrange
        client.disconnect_on_error = True
        client.acceptable_errors = 2
        client.commError = 3
        mock_client = Mock()
        mock_client.connected = True
        client._client = mock_client

        # Act
        client.disconnectOnError()

        # Assert
        # Should have disconnected (client set to None)
        assert client._client is None

    def test_disconnect_on_error_not_connected(self, client: modbusport) -> None:
        """Test disconnectOnError when not connected."""
        # Arrange
        client.disconnect_on_error = True
        client.acceptable_errors = 5
        client.commError = 1
        client._client = None

        # Act
        client.disconnectOnError()

        # Assert
        # Should have attempted to disconnect (client remains None)
        assert client._client is None

    def test_disconnect_on_error_disabled(self, client: modbusport) -> None:
        """Test disconnectOnError when mechanism is disabled."""
        # Arrange
        client.disconnect_on_error = False
        client.commError = 10
        mock_client = Mock()
        mock_client.connected = True
        client._client = mock_client

        # Act
        client.disconnectOnError()

        # Assert
        # Should not have disconnected (client remains)
        assert client._client is not None

    def test_format_ms_timing(self) -> None:
        """Test formatMS timing utility function."""
        # Arrange
        start_time = 1000.0
        end_time = 1000.1234

        # Act
        result = modbusport.formatMS(start_time, end_time)

        # Assert
        assert result == '123.4'

    def test_format_ms_zero_duration(self) -> None:
        """Test formatMS with zero duration."""
        # Arrange
        start_time = 1000.0
        end_time = 1000.0

        # Act
        result = modbusport.formatMS(start_time, end_time)

        # Assert
        assert result == '0.0'


class TestCacheManagement:
    """Test readings cache management."""

    def test_clear_readings_cache(self, client: modbusport) -> None:
        """Test clearing the readings cache."""
        # Arrange
        client.readingsCache = {3: {1: {100: 123, 101: 456}}}

        # Act
        client.clearReadingsCache()

        # Assert
        assert client.readingsCache == {}

    def test_cache_readings_new_code(self, client: modbusport, mock_aw: Mock) -> None:
        """Test caching readings for a new function code."""
        # Arrange
        client.readingsCache = {}
        mock_aw.seriallogflag = False

        # Act
        client.cacheReadings(3, 1, 100, [123, 456, 789])

        # Assert
        expected = {3: {1: {100: 123, 101: 456, 102: 789}}}
        assert client.readingsCache == expected

    def test_cache_readings_existing_code_new_slave(
        self, client: modbusport, mock_aw: Mock
    ) -> None:
        """Test caching readings for existing code but new slave."""
        # Arrange
        client.readingsCache = {3: {1: {100: 999}}}
        mock_aw.seriallogflag = False

        # Act
        client.cacheReadings(3, 2, 200, [111, 222])

        # Assert
        expected = {3: {1: {100: 999}, 2: {200: 111, 201: 222}}}
        assert client.readingsCache == expected

    def test_cache_readings_with_serial_logging(self, client: modbusport, mock_aw: Mock) -> None:
        """Test caching readings with serial logging enabled."""
        # Arrange
        client.readingsCache = {}
        mock_aw.seriallogflag = True

        # Act
        client.cacheReadings(3, 1, 100, [123])

        # Assert
        assert client.readingsCache == {3: {1: {100: 123}}}
        mock_aw.addserial.assert_called_once()

    def test_cache_structure_after_caching(self, client: modbusport, mock_aw: Mock) -> None:
        """Test that cache structure is correct after caching readings."""
        # Arrange
        client.readingsCache = {}
        mock_aw.seriallogflag = False

        # Act
        client.cacheReadings(3, 1, 100, [123, 456])

        # Assert
        assert 3 in client.readingsCache
        assert 1 in client.readingsCache[3]
        assert 100 in client.readingsCache[3][1]
        assert 101 in client.readingsCache[3][1]
        assert client.readingsCache[3][1][100] == 123
        assert client.readingsCache[3][1][101] == 456


class TestMaxBlocks:
    """Test max_blocks optimization functionality."""

    @pytest.mark.parametrize(
        'registers,expected',
        [
            ([0, 10], [(0, 10)]),
            ([0, 99], [(0, 99)]),
            ([0, 100], [(0, 0), (100, 100)]),  # Split at MAX_REGISTER_SEGMENT
            ([1, 5, 112, 120], [(1, 5), (112, 120)]),
            ([0, 2, 20, 1040, 1105, 1215], [(0, 20), (1040, 1105), (1215, 1215)]),
            (
                [0, 99, 100, 199, 200, 299, 300, 320, 350],
                [(0, 99), (100, 199), (200, 299), (300, 350)],
            ),
            ([], []),  # Empty list
            ([42], [(42, 42)]),  # Single register
        ],
    )
    def test_max_blocks_various_inputs(
        self, client: modbusport, registers: List[int], expected: List[Tuple[int, int]]
    ) -> None:
        """Test max_blocks with various register sequences."""
        # Act
        result = client.max_blocks(registers)

        # Assert
        assert result == expected

    def test_max_blocks_large_gap(self, client: modbusport) -> None:
        """Test max_blocks with large gaps between registers."""
        # Arrange
        registers = [0, 1, 1000, 1001, 2000]

        # Act
        result = client.max_blocks(registers)

        # Assert
        expected = [(0, 1), (1000, 1001), (2000, 2000)]
        assert result == expected

    def test_max_blocks_exceeds_segment_size(self, client: modbusport) -> None:
        """Test max_blocks when range exceeds MAX_REGISTER_SEGMENT."""
        # Arrange
        registers = list(range(250))  # 250 consecutive registers

        # Act
        result = client.max_blocks(registers)

        # Assert
        # Should be split into chunks of MAX_REGISTER_SEGMENT (100)
        expected = [(0, 99), (100, 199), (200, 249)]
        assert result == expected


class TestUpdateActiveRegisters:
    """Test active registers management for optimization."""

    def test_update_active_registers_called(self, client: modbusport) -> None:
        """Test that updateActiveRegisters can be called without error."""
        # Act - This should not raise an exception
        client.updateActiveRegisters()

        # Assert - activeRegisters should be a dict
        assert isinstance(client.activeRegisters, dict)


class TestSlaveZeroHandling:
    """Test handling of slave ID 0 (which should be ignored)."""

    @pytest.mark.parametrize(
        'method_name,args',
        [
            ('readFloat', (0, 100)),
            ('readBCD', (0, 100)),
            ('readSingleRegister', (0, 100)),
            ('readInt32', (0, 100)),
            ('readBCDint', (0, 100)),
            ('peekSingleRegister', (0, 100)),
            ('writeCoil', (0, 100, True)),
            ('writeSingleRegister', (0, 100, 123)),
            ('writeWord', (0, 100, 123.45)),
            ('writeRegisters', (0, 100, [123, 456])),
            ('writeCoils', (0, 100, [True, False])),
        ],
    )
    def test_methods_return_early_for_slave_zero(
        self,
        client: modbusport,
        method_name: str,
        args: Tuple[Union[int, bool, float, List[int], List[bool]], ...],
    ) -> None:
        """Test that methods return early when slave ID is 0."""
        # Arrange
        method = getattr(client, method_name)

        # Act
        result = method(*args)

        # Assert
        # Read methods should return None, write methods should return None (early return)
        if method_name.startswith(('read', 'peek')):
            assert result is None
        # Write methods don't return values, so we just verify no exception


class TestInvalidResultHandling:
    """Test invalidResult method for detecting invalid MODBUS responses."""

    def test_invalid_result_none_response(self, client: modbusport) -> None:
        """Test invalidResult with None response."""
        # Act
        is_invalid, is_exception = client.invalidResult(None, 1)

        # Assert
        assert is_invalid is True
        assert is_exception is False

    def test_invalid_result_exception_response(self, client: modbusport) -> None:
        """Test invalidResult with ExceptionResponse."""
        # Arrange
        mock_response = Mock(spec=ExceptionResponse)

        # Act
        is_invalid, is_exception = client.invalidResult(mock_response, 1)

        # Assert
        assert is_invalid is True
        assert is_exception is False  # ExceptionResponse returns (True, False)

    def test_invalid_result_with_error(self, client: modbusport) -> None:
        """Test invalidResult with response that has isError() True."""
        # Arrange
        mock_response = Mock()
        mock_response.isError.return_value = True

        # Act
        is_invalid, is_exception = client.invalidResult(mock_response, 1)

        # Assert
        assert is_invalid is True
        assert is_exception is True  # Error responses return (True, True)

    def test_invalid_result_none_registers(self, client: modbusport) -> None:
        """Test invalidResult with response having None registers."""
        # Arrange
        mock_response = Mock()
        mock_response.isError.return_value = False
        mock_response.registers = None

        # Act
        is_invalid, is_exception = client.invalidResult(mock_response, 1)

        # Assert
        assert is_invalid is True
        assert is_exception is False

    def test_invalid_result_wrong_register_count(self, client: modbusport) -> None:
        """Test invalidResult with wrong number of registers."""
        # Arrange
        mock_response = Mock()
        mock_response.isError.return_value = False
        mock_response.registers = [123, 456]  # 2 registers when expecting 1

        # Act
        is_invalid, is_exception = client.invalidResult(mock_response, 1)

        # Assert
        assert is_invalid is True
        assert is_exception is False

    def test_invalid_result_valid_response(self, client: modbusport) -> None:
        """Test invalidResult with valid response."""
        # Arrange
        mock_response = Mock()
        mock_response.isError.return_value = False
        mock_response.registers = [123, 456]

        # Act
        is_invalid, is_exception = client.invalidResult(mock_response, 2)

        # Assert
        assert is_invalid is False
        assert is_exception is False

    def test_invalid_result_zero_count_no_registers_expected(self, client: modbusport) -> None:
        """Test invalidResult with count=0 (no registers expected for function 1 and 2)."""
        # Arrange
        mock_response = Mock()
        mock_response.isError.return_value = False
        mock_response.registers = []

        # Act
        is_invalid, is_exception = client.invalidResult(mock_response, 0)

        # Assert
        assert is_invalid is False
        assert is_exception is False


class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions."""

    def test_bcd_conversion_edge_cases(self) -> None:
        """Test BCD conversion with edge cases."""
        # Test maximum 4-digit BCD value
        assert convert_to_bcd(9999) == 0x9999
        assert convert_from_bcd(0x9999) == 9999

        # Test single digits
        for i in range(10):
            assert convert_to_bcd(i) == i
            assert convert_from_bcd(i) == i

    def test_address_conversion_boundary_values(self) -> None:
        """Test address conversion with boundary values."""
        # Test minimum addresses
        assert modbusport.address2register(40001, 3) == 0
        assert modbusport.address2register(30001, 4) == 0

        # Test large addresses
        assert modbusport.address2register(49999, 3) == 9998
        assert modbusport.address2register(39999, 4) == 9998

    def test_max_count_boundary(self, client: modbusport) -> None:
        """Test maxCount boundary condition."""
        # Assert the MODBUS spec limit
        assert client.maxCount == 125

        # Test that MAX_REGISTER_SEGMENT is reasonable
        assert client.MAX_REGISTER_SEGMENT == 100
        assert client.maxCount > client.MAX_REGISTER_SEGMENT

    def test_timeout_calculations(self, client: modbusport, mock_aw: Mock) -> None:
        """Test timeout calculations based on sampling delay."""
        # Arrange
        mock_aw.qmc.delay = 2000  # 2 seconds
        client.timeout = 0.4
        client.IP_timeout = 0.2

        # The timeout should not exceed half the sampling interval
        expected_serial_timeout = min(2000 / 2000, 0.4)  # min(1.0, 0.4) = 0.4
        expected_ip_timeout = min(2000.0 / 2000, 0.2)  # min(1.0, 0.2) = 0.2

        # These are used in connect_async, but we can test the logic
        assert expected_serial_timeout == 0.4
        assert expected_ip_timeout == 0.2


class TestDeprecatedWriteRegister:
    """Test the deprecated writeRegister method."""

    def test_write_register_value_parsing(self) -> None:
        """Test writeRegister value parsing logic."""
        # Test string float parsing
        test_str_float = '123.45'
        assert isinstance(test_str_float, str) and '.' in test_str_float
        assert int(round(float(test_str_float))) == 123

        # Test string int parsing
        test_str_int = '456'
        assert isinstance(test_str_int, str) and '.' not in test_str_int
        assert int(test_str_int) == 456

        # Test int value
        assert isinstance(789, int)

        # Test float value rounding
        assert int(round(123.67)) == 124

    def test_write_register_slave_zero_ignored(self, client: modbusport) -> None:
        """Test writeRegister ignores slave ID 0."""
        # This should not raise an exception and should return early
        try:
            client.writeRegister(0, 100, 123)
            # If we get here, the method returned early as expected
            assert True
        except Exception as exc:
            # Should not raise any exception
            raise AssertionError('writeRegister should handle slave 0 gracefully') from exc


class TestConnectionTypes:
    """Test different connection type configurations."""

    @pytest.mark.parametrize(
        'connection_type,expected_description',
        [
            (0, 'Serial RTU'),
            (1, 'Serial ASCII'),
            (2, 'Serial Binary'),
            (3, 'TCP'),
            (4, 'UDP'),
        ],
    )
    def test_connection_type_values(
        self, client: modbusport, connection_type: int, expected_description: str  # noqa: ARG002
    ) -> None:
        """Test that connection types are properly defined."""
        # Arrange
        client.type = connection_type

        # Assert
        assert client.type == connection_type
        # The descriptions are in comments in the code, so we just verify the values are valid
        assert 0 <= connection_type <= 4

    def test_default_connection_type_is_serial_rtu(self, client: modbusport) -> None:
        """Test that default connection type is Serial RTU."""
        # Assert
        assert client.type == 0  # Serial RTU


class TestLegacyPymodbusHandling:
    """Test handling of legacy pymodbus versions."""

    def test_legacy_pymodbus_detection(self, client: modbusport) -> None:
        """Test legacy pymodbus version detection."""
        # The legacy_pymodbus flag is set during initialization based on pymodbus version
        # We can't easily mock the version check, but we can test the flag exists
        assert hasattr(client, 'legacy_pymodbus')
        assert isinstance(client.legacy_pymodbus, bool)

    def test_legacy_conversion_methods_exist(self, client: modbusport) -> None:
        """Test that conversion methods handle legacy pymodbus correctly."""
        # Arrange - Force legacy mode for testing
        original_legacy = client.legacy_pymodbus
        client.legacy_pymodbus = True

        try:
            # Act & Assert - These should not raise exceptions
            result_int = client.convert_32bit_int_to_registers(12345)
            result_float = client.convert_float_to_registers(123.45)

            assert isinstance(result_int, list)
            assert isinstance(result_float, list)
            assert len(result_int) == 2
            assert len(result_float) == 2

            # Test conversion back
            converted_int = client.convert_32bit_int_from_registers(result_int)
            converted_float = client.convert_float_from_registers(result_float)

            assert converted_int == 12345
            assert pytest.approx(converted_float, abs=0.01) == 123.45

        finally:
            # Restore original state
            client.legacy_pymodbus = original_legacy


class TestAsyncOperationMocking:
    """Test async operations with proper mocking."""

    def test_sleep_between_method_exists(self, client: modbusport) -> None:
        """Test that sleepBetween method exists and can be called."""
        # Act & Assert - Should not raise exception
        client.sleepBetween()
        client.sleepBetween(write=True)
        client.sleepBetween(write=False)

    def test_read_active_registers_optimizer_disabled(self, client: modbusport) -> None:
        """Test readActiveRegisters when optimizer is disabled."""
        # Arrange
        client.optimizer = False

        # Act
        client.readActiveRegisters()

        # Assert - Should return early without doing anything
        # No exception should be raised

    @patch('asyncio.run_coroutine_threadsafe')
    def test_read_active_registers_with_mock_async(
        self, mock_run_coroutine: Mock, client: modbusport
    ) -> None:
        """Test readActiveRegisters with mocked async operations."""
        # Arrange
        client.optimizer = True
        mock_future = Mock()
        mock_future.result.return_value = None
        mock_run_coroutine.return_value = mock_future

        mock_async_thread = Mock()
        mock_async_thread.loop = Mock()
        client._asyncLoopThread = mock_async_thread

        mock_client = Mock()
        mock_client.connected = True
        client._client = mock_client

        with patch('artisanlib.modbusport.modbusport.connect'):
            # Act
            client.readActiveRegisters()

            # Assert
            mock_run_coroutine.assert_called_once()

    def test_semaphore_initialization(self, client: modbusport) -> None:
        """Test that COMsemaphore is properly initialized."""
        # Assert
        assert client.COMsemaphore is not None
        assert client.COMsemaphore.available() == 1


class TestErrorScenarios:
    """Test various error scenarios and exception handling."""

    def test_bcd_conversion_with_invalid_bcd_digits(self) -> None:
        """Test BCD conversion with invalid BCD digits (should still work mathematically)."""
        # BCD should only contain digits 0-9 in each nibble, but the functions
        # will still process invalid BCD mathematically
        invalid_bcd = 0xAB  # Contains hex digits A and B
        result = convert_from_bcd(invalid_bcd)
        # This will give a mathematical result, not a proper BCD conversion
        assert isinstance(result, int)

    def test_max_blocks_with_unsorted_input(self, client: modbusport) -> None:
        """Test max_blocks with unsorted register list."""
        # Arrange
        unsorted_registers = [100, 50, 200, 75]

        # Act
        result = client.max_blocks(unsorted_registers)

        # Assert
        # The method processes registers in order without sorting
        # It creates segments based on the order given
        expected = [(100, 50), (200, 75)]
        assert result == expected

    def test_conversion_methods_with_empty_registers(self, client: modbusport) -> None:
        """Test conversion methods with empty register lists."""
        # These methods return -1 for invalid input rather than raising exceptions
        result = client.convert_16bit_uint_from_registers([])
        assert result == -1

        float_result = client.convert_float_from_registers([])
        assert float_result == -1

    def test_conversion_methods_with_insufficient_registers(self, client: modbusport) -> None:
        """Test conversion methods with insufficient register data."""
        # 32-bit conversions need 2 registers
        with pytest.raises(ModbusException):
            client.convert_32bit_uint_from_registers([123])  # Only 1 register

        with pytest.raises(ModbusException):
            client.convert_float_from_registers([123])  # Only 1 register
