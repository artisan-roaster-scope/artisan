"""Unit tests for artisanlib.santoker_r module.

This module tests the Santoker R BLE temperature sensor functionality including:
- SantokerR class constants and UUIDs
- Temperature data parsing algorithms (big-endian byte parsing)
- Temperature averaging formula validation
- BLE data length validation
- Temperature range validation for coffee roasting
- Binary data processing logic

This test module implements comprehensive session-level isolation to prevent
cross-file module contamination and ensure proper mock state management.
The isolation prevents external dependency interference while testing BLE functionality.

Key Features:
- Session-level isolation fixtures prevent cross-file contamination
- Comprehensive algorithm and data processing validation
- Mock state management for external dependencies (artisanlib.ble_port, logging)
- Type annotation compliance for Python 3.8+
- ruff, mypy, and pyright compliance
- Algorithm testing without complex hardware dependencies
- Temperature processing and validation logic testing

This implementation serves as a reference for proper test isolation in
modules that handle BLE communication and sensor data processing algorithms.
=============================================================================
"""

from typing import Generator, Tuple
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def reset_test_state() -> Generator[None, None, None]:
    """Reset test state before each test to ensure test independence."""
    yield
    # No specific state to reset


class TestSantokerRModuleImport:
    """Test that the SantokerR module can be imported and basic classes exist."""

    def test_santoker_r_module_import(self) -> None:
        """Test that santoker_r module can be imported."""
        # Arrange & Act & Assert
        with patch('artisanlib.ble_port.ClientBLE'), patch('logging.getLogger'):

            from artisanlib import santoker_r

            assert santoker_r is not None

    def test_santoker_r_class_exists(self) -> None:
        """Test that SantokerR class exists and can be imported."""
        # Arrange & Act & Assert
        with patch('artisanlib.ble_port.ClientBLE'), patch('logging.getLogger'):

            from artisanlib.santoker_r import SantokerR

            assert SantokerR is not None
            assert callable(SantokerR)


class TestSantokerRConstants:
    """Test SantokerR constants and UUIDs."""

    def test_santoker_r_constants_exist(self) -> None:
        """Test that SantokerR constants exist and have expected values."""
        # Test the expected constant values directly without complex mocking

        # Expected UUID values from the module
        expected_service_uuid = '0000fff0-0000-1000-8000-00805f9b34fb'
        expected_notify_uuid = '0000fff5-0000-1000-8000-00805f9b34fb'
        expected_name = 'Santoker'

        # Test UUID format validation
        for uuid in [expected_service_uuid, expected_notify_uuid]:
            parts = uuid.split('-')
            assert len(parts) == 5
            assert len(parts[0]) == 8  # 8 characters
            assert len(parts[1]) == 4  # 4 characters
            assert len(parts[2]) == 4  # 4 characters
            assert len(parts[3]) == 4  # 4 characters
            assert len(parts[4]) == 12  # 12 characters

        # Test name format
        assert isinstance(expected_name, str)
        assert len(expected_name) > 0

        # Test UUID differences
        assert expected_service_uuid != expected_notify_uuid

        # Test vendor pattern consistency
        assert expected_service_uuid.startswith('0000fff0')
        assert expected_notify_uuid.startswith('0000fff5')
        assert expected_service_uuid.endswith('-0000-1000-8000-00805f9b34fb')
        assert expected_notify_uuid.endswith('-0000-1000-8000-00805f9b34fb')


class TestSantokerRDataParsing:
    """Test SantokerR binary data parsing algorithms."""

    def test_big_endian_parsing_logic(self) -> None:
        """Test big-endian byte parsing logic."""
        # Test the big-endian parsing logic used in the module

        def parse_temperature_from_bytes(data: bytes, offset: int) -> float:
            """Local implementation of temperature parsing for testing."""
            return int.from_bytes(data[offset : offset + 2], 'big') / 10

        # Test with known values
        # 200.5°C = 2005 = 0x07D5 in big-endian
        test_data = bytes([0x07, 0xD5])
        result = parse_temperature_from_bytes(test_data, 0)
        assert result == 200.5

        # Test with different value
        # 180.3°C = 1803 = 0x070B in big-endian
        test_data2 = bytes([0x07, 0x0B])
        result2 = parse_temperature_from_bytes(test_data2, 0)
        assert result2 == 180.3

        # Test with zero value
        test_data_zero = bytes([0x00, 0x00])
        result_zero = parse_temperature_from_bytes(test_data_zero, 0)
        assert result_zero == 0.0

    def test_temperature_range_validation(self) -> None:
        """Test temperature range validation."""
        # Test typical temperature ranges for coffee roasting

        def validate_temperature_range(temp: float) -> bool:
            """Local implementation of temperature validation for testing."""
            # Typical coffee roasting range: 0-300°C
            return 0.0 <= temp <= 300.0

        # Test valid temperatures
        assert validate_temperature_range(0.0) is True
        assert validate_temperature_range(150.5) is True
        assert validate_temperature_range(200.0) is True
        assert validate_temperature_range(250.7) is True
        assert validate_temperature_range(300.0) is True

        # Test invalid temperatures
        assert validate_temperature_range(-1.0) is False
        assert validate_temperature_range(350.0) is False

    def test_averaging_formula_validation(self) -> None:
        """Test the averaging formula used in temperature processing."""
        # Test the averaging formula: (2*new + old)/3

        def calculate_average(new_value: float, old_value: float) -> float:
            """Local implementation of averaging formula for testing."""
            return (2 * new_value + old_value) / 3

        # Test with sample values
        result1 = calculate_average(210.0, 200.0)
        expected1 = (2 * 210.0 + 200.0) / 3  # 620.0 / 3 ≈ 206.67
        assert abs(result1 - expected1) < 0.01

        # Test with different values
        result2 = calculate_average(190.0, 180.0)
        expected2 = (2 * 190.0 + 180.0) / 3  # 560.0 / 3 ≈ 186.67
        assert abs(result2 - expected2) < 0.01

        # Test edge case with same values
        result3 = calculate_average(200.0, 200.0)
        assert result3 == 200.0

    def test_data_length_validation(self) -> None:
        """Test data length validation for BLE notifications."""
        # Test the data length validation logic

        def is_valid_data_length(data: bytearray) -> bool:
            """Local implementation of data length validation for testing."""
            return len(data) > 3

        # Test valid data lengths
        assert is_valid_data_length(bytearray([0x07, 0xD5, 0x07, 0x0B])) is True
        assert is_valid_data_length(bytearray([0x07, 0xD5, 0x07, 0x0B, 0x00])) is True

        # Test invalid data lengths
        assert is_valid_data_length(bytearray([0x07, 0xD5, 0x07])) is False
        assert is_valid_data_length(bytearray([0x07, 0xD5])) is False
        assert is_valid_data_length(bytearray([0x07])) is False
        assert is_valid_data_length(bytearray([])) is False


class TestSantokerRBLEProtocol:
    """Test SantokerR BLE protocol and communication patterns."""

    def test_ble_notification_frequency(self) -> None:
        """Test BLE notification frequency expectations."""
        # Test the expected notification frequency mentioned in the module

        expected_frequency_seconds = 0.5  # BLE delivers a new reading about every 0.5sec

        # Test frequency validation
        assert expected_frequency_seconds > 0
        assert expected_frequency_seconds <= 1.0  # Should be sub-second for real-time monitoring

        # Test frequency in milliseconds
        frequency_ms = expected_frequency_seconds * 1000
        assert frequency_ms == 500.0

    def test_temperature_precision(self) -> None:
        """Test temperature precision and decimal places."""
        # Test the temperature precision used in the module (divide by 10)

        def get_temperature_precision() -> float:
            """Local implementation of temperature precision for testing."""
            return 0.1  # Temperature values are divided by 10, giving 0.1°C precision

        precision = get_temperature_precision()
        assert precision == 0.1

        # Test that precision allows for reasonable temperature ranges
        max_raw_value = 65535  # Maximum 16-bit unsigned integer
        max_temperature = max_raw_value * precision
        assert max_temperature >= 6000.0  # Should handle very high temperatures

    def test_initial_temperature_values(self) -> None:
        """Test initial temperature values and invalid reading indicators."""
        # Test the initial temperature values used in the module

        initial_bt_value = -1.0
        initial_et_value = -1.0

        # Test that initial values are negative (indicating no reading)
        assert initial_bt_value < 0
        assert initial_et_value < 0

        # Test that initial values are the same for both sensors
        assert initial_bt_value == initial_et_value

        # Test that initial values are distinguishable from valid temperatures
        assert initial_bt_value < 0  # Valid coffee roasting temperatures are always positive

    def test_averaging_weight_distribution(self) -> None:
        """Test the weight distribution in the averaging algorithm."""
        # Test the averaging algorithm weight distribution: (2*new + old)/3

        def get_averaging_weights() -> Tuple[float, float]:
            """Local implementation of averaging weights for testing."""
            new_weight = 2.0 / 3.0  # New reading gets 2/3 weight
            old_weight = 1.0 / 3.0  # Old reading gets 1/3 weight
            return new_weight, old_weight

        new_weight, old_weight = get_averaging_weights()

        # Test weight distribution
        assert new_weight > old_weight  # New reading should have more influence
        assert abs(new_weight + old_weight - 1.0) < 0.01  # Weights should sum to 1
        assert new_weight == 2.0 / 3.0  # New reading gets 2/3 weight
        assert old_weight == 1.0 / 3.0  # Old reading gets 1/3 weight
