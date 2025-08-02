# ============================================================================
# CRITICAL: Module-Level Isolation Setup (MUST BE FIRST)
# ============================================================================
# Ensure proper module isolation to prevent cross-file contamination

import datetime
import os
import sys
from pathlib import Path
import tempfile
from typing import Any, Dict, Generator
from unittest.mock import Mock, patch

# Store original modules before any mocking to enable restoration
original_modules: Dict[str, Any] = {}
original_functions: Dict[str, Any] = {}
modules_to_isolate = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'artisanlib.util',
    'plus.config',
]

# Store original modules if they exist
for module_name in modules_to_isolate:
    if module_name in sys.modules and not hasattr(sys.modules[module_name], '_mock_name'):
        original_modules[module_name] = sys.modules[module_name]

# ============================================================================
# Now safe to import other modules
# ============================================================================

"""Unit tests for plus.util module.

This module tests the utility functions for the plus package including:
- File modification date retrieval
- Date/time conversion functions (datetime, epoch, ISO8601)
- Temperature conversion utilities (F to C, RoR conversions)
- Number and text limiting functions
- Dictionary manipulation utilities
- URL generation for web links
- Account state extraction from responses
- GMT offset calculation
- Language detection
- Plus icon handling

=============================================================================
COMPREHENSIVE TEST ISOLATION IMPLEMENTATION
=============================================================================

This test module implements comprehensive test isolation to prevent cross-file
module contamination and ensure proper mock state management following SDET
best practices.

ISOLATION STRATEGY:
1. **Module-Level Dependency Preservation**: Store original modules before mocking
   to enable proper restoration after tests complete

2. **Minimal Mocking**: The plus.util module has minimal external dependencies,
   so minimal mocking is needed

3. **Session-Level Isolation**:
   - ensure_util_isolation fixture manages module state at session level
   - Proper cleanup after session to prevent module registration conflicts

4. **Automatic State Reset**:
   - reset_util_state fixture runs automatically for every test
   - Clean state management between tests

5. **Cross-File Contamination Prevention**:
   - Module restoration prevents contamination of other tests
   - Proper cleanup of mocked dependencies
   - Works correctly when run with other test files (verified)

PYTHON 3.8 COMPATIBILITY:
- Uses typing.Any, typing.Dict, typing.Generator instead of built-in generics
- Avoids walrus operator and other Python 3.9+ features
- Compatible type annotations throughout
- Proper Generator typing for fixtures

VERIFICATION:
✅ Individual tests pass: pytest test_plus_util.py::TestClass::test_method
✅ Full module tests pass: pytest test_plus_util.py
✅ Cross-file isolation works: pytest test_plus_util.py test_main.py
✅ Cross-file isolation works: pytest test_main.py test_plus_util.py
✅ No module contamination affecting other tests
✅ No numpy multiple import issues

This implementation serves as a reference for proper test isolation in
modules that test utility functionality while preventing cross-file contamination.
=============================================================================
"""

import numpy as np
import pytest

from plus import util


@pytest.fixture(scope='session', autouse=True)
def ensure_util_isolation() -> Generator[None, None, None]:
    """
    Ensure modules are properly isolated for util tests at session level.

    This fixture runs once per test session to ensure that mocked modules
    used by util tests don't interfere with other tests that need real dependencies.
    """
    yield

    # Restore original modules immediately after session to prevent contamination
    for module_name, original_module in original_modules.items():
        if module_name in sys.modules:
            sys.modules[module_name] = original_module

    # Restore original functions
    for func_path, original_func in original_functions.items():
        if '.' in func_path:
            module_name, func_name = func_path.rsplit('.', 1)
            if module_name in sys.modules:
                setattr(sys.modules[module_name], func_name, original_func)

    # Clean up any remaining mocked modules that weren't originally present
    modules_to_clean = [
        module_name
        for module_name in modules_to_isolate
        if module_name not in original_modules
        and module_name in sys.modules
        and hasattr(sys.modules[module_name], '_mock_name')
    ]

    for module_name in modules_to_clean:
        del sys.modules[module_name]


@pytest.fixture(scope='module', autouse=True)
def cleanup_util_mocks() -> Generator[None, None, None]:
    """
    Clean up util test mocks at module level to prevent cross-file contamination.

    This fixture runs once per test module and ensures immediate cleanup
    of mocked dependencies when the util test module completes.
    """
    yield

    # Immediately restore original modules when this test module completes
    for module_name, original_module in original_modules.items():
        if module_name in sys.modules:
            sys.modules[module_name] = original_module

    # Restore original functions
    for func_path, original_func in original_functions.items():
        if '.' in func_path:
            module_name, func_name = func_path.rsplit('.', 1)
            if module_name in sys.modules:
                setattr(sys.modules[module_name], func_name, original_func)

    # Clean up mocked modules that weren't originally present
    modules_to_clean = [
        module_name
        for module_name in modules_to_isolate
        if module_name not in original_modules
        and module_name in sys.modules
        and hasattr(sys.modules[module_name], '_mock_name')
    ]

    for module_name in modules_to_clean:
        del sys.modules[module_name]


@pytest.fixture(autouse=True)
def reset_util_state() -> Generator[None, None, None]:
    """
    Reset util module state before and after each test to ensure complete isolation.

    This fixture automatically runs for every test to prevent cross-test contamination
    and ensures that each test starts with a clean state.
    """
    yield

    # Clean up after each test - no specific state to reset for util module
    # The util module doesn't maintain global state, so no cleanup needed


@pytest.fixture
def mock_app_window() -> Mock:
    """Create a mock application window."""
    mock_aw: Mock = Mock()
    mock_aw.qmc = Mock()
    mock_aw.qmc.mode = 'C'  # Default to Celsius
    mock_aw.plus_account = Mock()
    mock_aw.plus_language = 'en'
    mock_aw.updateLimits = Mock()
    return mock_aw


@pytest.fixture
def mock_config_app_window(mock_app_window: Mock) -> Generator[Mock, None, None]:
    """Mock the config.app_window."""
    with patch('plus.util.config.app_window', mock_app_window):
        yield mock_app_window


@pytest.fixture
def temp_file() -> Generator[str, None, None]:
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b'test content')
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


class TestFileOperations:
    """Test file-related utility functions."""

    def test_get_modification_date_existing_file(self, temp_file: str) -> None:
        """Test getting modification date of existing file."""
        # Act
        mod_date = util.getModificationDate(temp_file)

        # Assert
        assert mod_date is not None
        assert isinstance(mod_date, float)
        assert mod_date > 0

    def test_get_modification_date_nonexistent_file(self) -> None:
        """Test getting modification date of non-existent file."""
        # Act
        mod_date = util.getModificationDate('/nonexistent/file.txt')

        # Assert
        assert mod_date is None


class TestDateTimeConversions:
    """Test date/time conversion utilities."""

    def test_datetime2iso8601_conversion(self) -> None:
        """Test datetime to ISO8601 string conversion."""
        # Arrange
        dt = datetime.datetime(2023, 10, 15, 14, 30, 45, 123456, tzinfo=datetime.timezone.utc)

        # Act
        iso_string = util.datetime2ISO8601(dt)

        # Assert
        assert iso_string == '2023-10-15T14:30:45.123Z'

    def test_iso8601_to_datetime_conversion(self) -> None:
        """Test ISO8601 string to datetime conversion."""
        # Arrange
        iso_string = '2023-10-15T14:30:45.123Z'

        # Act
        dt = util.ISO86012datetime(iso_string)

        # Assert
        assert isinstance(dt, datetime.datetime)
        assert dt.year == 2023
        assert dt.month == 10
        assert dt.day == 15
        assert dt.hour == 14
        assert dt.minute == 30
        assert dt.second == 45

    def test_datetime2epoch_conversion(self) -> None:
        """Test datetime to epoch conversion."""
        # Arrange
        dt = datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

        # Act
        epoch = util.datetime2epoch(dt)

        # Assert
        assert isinstance(epoch, float)
        assert epoch == dt.timestamp()

    def test_epoch2datetime_conversion(self) -> None:
        """Test epoch to datetime conversion."""
        # Arrange
        epoch = 1672531200.0  # 2023-01-01 00:00:00 UTC

        # Act
        dt = util.epoch2datetime(epoch)

        # Assert
        assert isinstance(dt, datetime.datetime)
        assert dt.tzinfo == datetime.timezone.utc
        assert dt.year == 2023
        assert dt.month == 1
        assert dt.day == 1

    def test_epoch2iso8601_conversion(self) -> None:
        """Test epoch to ISO8601 string conversion."""
        # Arrange
        epoch = 1672531200.0  # 2023-01-01 00:00:00 UTC

        # Act
        iso_string = util.epoch2ISO8601(epoch)

        # Assert
        assert isinstance(iso_string, str)
        assert iso_string.startswith('2023-01-01T00:00:00')
        assert iso_string.endswith('Z')

    def test_iso8601_to_epoch_conversion(self) -> None:
        """Test ISO8601 string to epoch conversion."""
        # Arrange
        iso_string = '2023-01-01T00:00:00.000Z'

        # Act
        epoch = util.ISO86012epoch(iso_string)

        # Assert
        assert isinstance(epoch, float)

    def test_get_gmt_offset(self) -> None:
        """Test GMT offset calculation."""
        # Act
        offset = util.getGMToffset()

        # Assert
        assert isinstance(offset, int)
        # Offset should be reasonable (between -12 and +14 hours in seconds)
        assert -43200 <= offset <= 50400


class TestTemperatureConversions:
    """Test temperature conversion utilities."""

    def test_from_f_to_c_normal_temperature(self) -> None:
        """Test Fahrenheit to Celsius conversion with normal temperature."""
        # Arrange
        fahrenheit = 212.0  # Boiling point of water

        # Act
        celsius = util.fromFtoC(fahrenheit)

        # Assert
        assert celsius == pytest.approx(100.0, rel=1e-9)

    def test_from_f_to_c_freezing_point(self) -> None:
        """Test Fahrenheit to Celsius conversion at freezing point."""
        # Arrange
        fahrenheit = 32.0  # Freezing point of water

        # Act
        celsius = util.fromFtoC(fahrenheit)

        # Assert
        assert celsius == pytest.approx(0.0, rel=1e-9)

    def test_from_f_to_c_none_value(self) -> None:
        """Test Fahrenheit to Celsius conversion with None value."""
        # Act
        result = util.fromFtoC(None)

        # Assert
        assert result is None

    def test_from_f_to_c_invalid_value(self) -> None:
        """Test Fahrenheit to Celsius conversion with invalid value."""
        # Act
        result = util.fromFtoC(-1)

        # Assert
        assert result == -1

    def test_from_f_to_c_nan_value(self) -> None:
        """Test Fahrenheit to Celsius conversion with NaN value."""
        # Act
        result = util.fromFtoC(np.nan)

        # Assert
        assert np.isnan(result)

    def test_temp2c_fahrenheit_mode(self, mock_config_app_window: Mock) -> None:
        """Test temperature conversion to Celsius in Fahrenheit mode."""
        # Arrange
        mock_config_app_window.qmc.mode = 'F'
        temperature = 212.0

        # Act
        result = util.temp2C(temperature)

        # Assert
        assert result == pytest.approx(100.0, rel=1e-9)

    def test_temp2c_celsius_mode(self, mock_config_app_window: Mock) -> None:
        """Test temperature conversion to Celsius in Celsius mode."""
        # Arrange
        mock_config_app_window.qmc.mode = 'C'
        temperature = 100.0

        # Act
        result = util.temp2C(temperature)

        # Assert
        assert result == 100.0

    def test_temp2c_explicit_fahrenheit_mode(self) -> None:
        """Test temperature conversion with explicit Fahrenheit mode."""
        # Arrange
        temperature = 212.0

        # Act
        result = util.temp2C(temperature, mode='F')

        # Assert
        assert result == pytest.approx(100.0, rel=1e-9)

    def test_temp2c_none_temperature(self) -> None:
        """Test temperature conversion with None temperature."""
        # Act
        result = util.temp2C(None)

        # Assert
        assert result is None

    def test_temp_diff2c_fahrenheit_mode(self, mock_config_app_window: Mock) -> None:
        """Test temperature difference conversion in Fahrenheit mode."""
        # Arrange
        mock_config_app_window.qmc.mode = 'F'
        temp_diff = 18.0  # 18°F difference = 10°C difference

        # Act
        result = util.tempDiff2C(temp_diff)

        # Assert
        assert result == pytest.approx(10.0, rel=1e-9)

    def test_temp_diff2c_celsius_mode(self, mock_config_app_window: Mock) -> None:
        """Test temperature difference conversion in Celsius mode."""
        # Arrange
        mock_config_app_window.qmc.mode = 'C'
        temp_diff = 10.0

        # Act
        result = util.tempDiff2C(temp_diff)

        # Assert
        assert result == 10.0

    def test_temp_diff2c_invalid_values(self, mock_config_app_window: Mock) -> None:
        """Test temperature difference conversion with invalid values."""
        # Arrange
        mock_config_app_window.qmc.mode = 'F'

        # Act & Assert
        assert util.tempDiff2C(-1) == -1
        assert util.tempDiff2C(None) is None
        assert np.isnan(util.tempDiff2C(np.nan))

    def test_ror_from_f_to_c_normal_value(self) -> None:
        """Test RoR Fahrenheit to Celsius conversion with normal value."""
        # Arrange
        ror_fahrenheit = 18.0  # 18°F/min = 10°C/min

        # Act
        ror_celsius = util.RoRfromFtoC(ror_fahrenheit)

        # Assert
        assert ror_celsius == pytest.approx(10.0, rel=1e-9)

    def test_ror_from_f_to_c_none_value(self) -> None:
        """Test RoR Fahrenheit to Celsius conversion with None value."""
        # Act
        result = util.RoRfromFtoC(None)

        # Assert
        assert result is None

    def test_ror_from_f_to_c_invalid_value(self) -> None:
        """Test RoR Fahrenheit to Celsius conversion with invalid value."""
        # Act
        result = util.RoRfromFtoC(-1)

        # Assert
        assert result == -1

    def test_ror_temp2c_fahrenheit_mode(self, mock_config_app_window: Mock) -> None:
        """Test RoR temperature conversion in Fahrenheit mode."""
        # Arrange
        mock_config_app_window.qmc.mode = 'F'
        ror_temp = 18.0

        # Act
        result = util.RoRtemp2C(ror_temp)

        # Assert
        assert result == pytest.approx(10.0, rel=1e-9)

    def test_ror_temp2c_celsius_mode(self, mock_config_app_window: Mock) -> None:
        """Test RoR temperature conversion in Celsius mode."""
        # Arrange
        mock_config_app_window.qmc.mode = 'C'
        ror_temp = 10.0

        # Act
        result = util.RoRtemp2C(ror_temp)

        # Assert
        assert result == 10.0


class TestNumberAndTextLimiting:
    """Test number and text limiting utilities."""

    def test_float2float_min_integer_result(self) -> None:
        """Test float2floatMin returns integer when possible."""
        # Arrange
        with patch('plus.util.config.app_window') as mock_aw, patch(
            'plus.util.float2float', return_value=5.0
        ):
            mock_aw.return_value = Mock()

            # Act
            result = util.float2floatMin(5.0, 1)

            # Assert
            assert result == 5
            assert isinstance(result, int)

    def test_float2float_min_float_result(self) -> None:
        """Test float2floatMin returns float when necessary."""
        # Arrange
        with patch('plus.util.config.app_window') as mock_aw, patch(
            'plus.util.float2float', return_value=5.5
        ):
            mock_aw.return_value = Mock()

            # Act
            result = util.float2floatMin(5.5, 1)

            # Assert
            assert result == 5.5
            assert isinstance(result, float)

    def test_float2float_min_none_input(self) -> None:
        """Test float2floatMin with None input."""
        # Act
        result = util.float2floatMin(None, 1)

        # Assert
        assert result is None

    def test_limitnum_within_range(self) -> None:
        """Test limitnum with value within range."""
        # Act
        result = util.limitnum(0.0, 100.0, 50.0)

        # Assert
        assert result == 50.0

    def test_limitnum_below_minimum(self) -> None:
        """Test limitnum with value below minimum."""
        # Act
        result = util.limitnum(10.0, 100.0, 5.0)

        # Assert
        assert result is None

    def test_limitnum_above_maximum(self) -> None:
        """Test limitnum with value above maximum."""
        # Act
        result = util.limitnum(0.0, 100.0, 150.0)

        # Assert
        assert result is None

    def test_limitnum_none_input(self) -> None:
        """Test limitnum with None input."""
        # Act
        result = util.limitnum(0.0, 100.0, None)

        # Assert
        assert result is None

    def test_limitnum_none_limits(self) -> None:
        """Test limitnum with None limits."""
        # Act
        result = util.limitnum(None, None, 50.0)

        # Assert
        assert result == 50.0

    def test_limittemp_valid_temperature(self) -> None:
        """Test limittemp with valid temperature."""
        # Act
        result = util.limittemp(25.0)

        # Assert
        assert result == 25.0

    def test_limittemp_too_high(self) -> None:
        """Test limittemp with temperature too high."""
        # Act
        result = util.limittemp(1500.0)

        # Assert
        assert result is None

    def test_limittemp_too_low(self) -> None:
        """Test limittemp with temperature too low."""
        # Act
        result = util.limittemp(-100.0)

        # Assert
        assert result is None

    def test_limittemp_none_input(self) -> None:
        """Test limittemp with None input."""
        # Act
        result = util.limittemp(None)

        # Assert
        assert result is None

    def test_limittemp_nan_input(self) -> None:
        """Test limittemp with NaN input."""
        # Act
        result = util.limittemp(np.nan)

        # Assert
        assert result is None

    def test_limittime_valid_time(self) -> None:
        """Test limittime with valid time."""
        # Act
        result = util.limittime(1800.0)  # 30 minutes

        # Assert
        assert result == 1800.0

    def test_limittime_too_high(self) -> None:
        """Test limittime with time too high."""
        # Act
        result = util.limittime(7200.0)  # 2 hours

        # Assert
        assert result is None

    def test_limittime_negative(self) -> None:
        """Test limittime with negative time."""
        # Act
        result = util.limittime(-100.0)

        # Assert
        assert result is None

    def test_limittime_none_input(self) -> None:
        """Test limittime with None input."""
        # Act
        result = util.limittime(None)

        # Assert
        assert result is None

    def test_limittext_within_limit(self) -> None:
        """Test limittext with text within limit."""
        # Act
        result = util.limittext(10, 'Hello')

        # Assert
        assert result == 'Hello'

    def test_limittext_exceeds_limit(self) -> None:
        """Test limittext with text exceeding limit."""
        # Act
        result = util.limittext(5, 'Hello World')

        # Assert
        assert result == 'Hello..'

    def test_limittext_none_input(self) -> None:
        """Test limittext with None input."""
        # Act
        result = util.limittext(10, None)

        # Assert
        assert result is None

    def test_limittext_empty_string(self) -> None:
        """Test limittext with empty string."""
        # Act
        result = util.limittext(10, '')

        # Assert
        assert result == ''


class TestDataExtraction:
    """Test data extraction utilities."""

    def test_extract_info_string_value(self) -> None:
        """Test extractInfo with string value."""
        # Arrange
        data = {'key': 'value'}

        # Act
        result = util.extractInfo(data, 'key', 'default')

        # Assert
        assert result == 'value'

    def test_extract_info_empty_string(self) -> None:
        """Test extractInfo with empty string."""
        # Arrange
        data = {'key': ''}

        # Act
        result = util.extractInfo(data, 'key', 'default')

        # Assert
        assert result == 'default'

    def test_extract_info_integer_value(self) -> None:
        """Test extractInfo with integer value."""
        # Arrange
        data = {'key': 42}

        # Act
        result = util.extractInfo(data, 'key', 0)

        # Assert
        assert result == 42

    def test_extract_info_float_value(self) -> None:
        """Test extractInfo with float value."""
        # Arrange
        data = {'key': 3.14}

        # Act
        result = util.extractInfo(data, 'key', 0.0)

        # Assert
        assert result == 3.14

    def test_extract_info_missing_key(self) -> None:
        """Test extractInfo with missing key."""
        # Arrange
        data = {'other_key': 'value'}

        # Act
        result = util.extractInfo(data, 'key', 'default')

        # Assert
        assert result == 'default'

    def test_extract_info_none_default(self) -> None:
        """Test extractInfo with None default."""
        # Arrange
        data = {'other_key': 'value'}

        # Act
        result = util.extractInfo(data, 'key', None)

        # Assert
        assert result is None


class TestLanguageAndAccountState:
    """Test language detection and account state utilities."""

    def test_get_language_with_app_window(self, mock_config_app_window: Mock) -> None:
        """Test getLanguage with app window available."""
        # Arrange
        mock_config_app_window.plus_language = 'de'

        # Act
        result = util.getLanguage()

        # Assert
        assert result == 'de'

    def test_get_language_without_app_window(self) -> None:
        """Test getLanguage without app window."""
        # Arrange
        with patch('plus.util.config.app_window', None):
            # Act
            result = util.getLanguage()

            # Assert
            assert result == 'en'

    def test_get_language_exception_handling(self, mock_config_app_window: Mock) -> None:
        """Test getLanguage with exception handling."""
        # Arrange
        mock_config_app_window.plus_account = None

        # Act
        result = util.getLanguage()

        # Assert
        assert result == 'en'

    def test_extract_account_state_complete_response(self) -> None:
        """Test extractAccountState with complete response."""
        # Arrange
        response = {
            'ol': {'rlimit': 100.0, 'rused': 50.0},
            'pu': 'premium',
            'notifications': {'unqualified': 5, 'machines': ['machine1', 'machine2']},
        }

        # Act
        rlimit, rused, pu, notifications, machines = util.extractAccountState(response)

        # Assert
        assert rlimit == 100.0
        assert rused == 50.0
        assert pu == 'premium'
        assert notifications == 5
        assert machines == ['machine1', 'machine2']

    def test_extract_account_state_empty_response(self) -> None:
        """Test extractAccountState with empty response."""
        # Act
        rlimit, rused, pu, notifications, machines = util.extractAccountState({})

        # Assert
        assert rlimit == -1.0
        assert rused == -1.0
        assert pu == ''
        assert notifications == 0
        assert machines == []

    def test_extract_account_state_partial_response(self) -> None:
        """Test extractAccountState with partial response."""
        # Arrange
        response = {'ol': {'rlimit': 200.0}, 'pu': 'basic'}

        # Act
        rlimit, rused, pu, notifications, machines = util.extractAccountState(response)

        # Assert
        assert rlimit == 200.0
        assert rused == -1.0
        assert pu == 'basic'
        assert notifications == 0
        assert machines == []

    def test_update_limits_from_response(self, mock_config_app_window: Mock) -> None:
        """Test updateLimitsFromResponse function."""
        # Arrange
        response = {
            'ol': {'rlimit': 150.0, 'rused': 75.0},
            'pu': 'premium',
            'notifications': {'unqualified': 3, 'machines': ['test_machine']},
        }

        # Act
        util.updateLimitsFromResponse(response)

        # Assert
        mock_config_app_window.updateLimits.assert_called_once_with(
            150.0, 75.0, 'premium', 3, ['test_machine']
        )


class TestWebLinks:
    """Test web link generation utilities."""

    def test_plus_link(self) -> None:
        """Test plusLink URL generation."""
        # Arrange
        with patch('plus.util.config.web_base_url', 'https://artisan.plus'):
            # Act
            result = util.plusLink()

            # Assert
            assert result == 'https://artisan.plus/'

    def test_store_link(self) -> None:
        """Test storeLink URL generation."""
        # Arrange
        with patch('plus.util.config.web_base_url', 'https://artisan.plus'):
            # Act
            result = util.storeLink('store123')

            # Assert
            assert result == 'https://artisan.plus/stores;id=store123'

    def test_coffee_link(self) -> None:
        """Test coffeeLink URL generation."""
        # Arrange
        with patch('plus.util.config.web_base_url', 'https://artisan.plus'):
            # Act
            result = util.coffeeLink('coffee456')

            # Assert
            assert result == 'https://artisan.plus/coffees;id=coffee456'

    def test_blend_link(self) -> None:
        """Test blendLink URL generation."""
        # Arrange
        with patch('plus.util.config.web_base_url', 'https://artisan.plus'):
            # Act
            result = util.blendLink('blend789')

            # Assert
            assert result == 'https://artisan.plus/blends;id=blend789'

    def test_roast_link(self) -> None:
        """Test roastLink URL generation."""
        # Arrange
        with patch('plus.util.config.web_base_url', 'https://artisan.plus'):
            # Act
            result = util.roastLink('roast101')

            # Assert
            assert result == 'https://artisan.plus/roasts;id=roast101'

    def test_reminders_link(self) -> None:
        """Test remindersLink URL generation."""
        # Arrange
        with patch('plus.util.config.web_base_url', 'https://artisan.plus'):
            # Act
            result = util.remindersLink()

            # Assert
            assert result == 'https://artisan.plus/reminders'

    def test_scheduler_link(self) -> None:
        """Test schedulerLink URL generation."""
        # Arrange
        with patch('plus.util.config.web_base_url', 'https://artisan.plus'):
            # Act
            result = util.schedulerLink()

            # Assert
            assert result == 'https://artisan.plus/schedule'


class TestPlusIcon:
    """Test plus icon handling utilities."""

    def test_set_plus_icon_with_app_style(self) -> None:
        """Test setPlusIcon with app style available."""
        # Arrange
        mock_mbox = Mock()
        mock_app_style = Mock()
        mock_app_style.pixelMetric.return_value = 48

        with patch('plus.util.getResourcePath', return_value=str(Path('/path/to/resources'))), patch(
            'plus.util.QApplication.style', return_value=mock_app_style
        ), patch('plus.util.QIcon') as mock_qicon, patch('plus.util.QSize') as mock_qsize:

            mock_icon = Mock()
            mock_pixmap = Mock()
            mock_icon.pixmap.return_value = mock_pixmap
            mock_qicon.return_value = mock_icon

            # Act
            util.setPlusIcon(mock_mbox)

            # Assert
            mock_qicon.assert_called_once_with(str(Path('/path/to/resources/Icons/plus-notification.svg')))
            mock_qsize.assert_called_once_with(48, 48)
            mock_mbox.setIconPixmap.assert_called_once_with(mock_pixmap)

    def test_set_plus_icon_without_app_style(self) -> None:
        """Test setPlusIcon without app style available."""
        # Arrange
        mock_mbox = Mock()

        with patch('plus.util.getResourcePath', return_value=str(Path('/path/to/resources'))), patch(
            'plus.util.QApplication.style', return_value=None
        ), patch('plus.util.QIcon') as mock_qicon, patch('plus.util.QSize') as mock_qsize:

            mock_icon = Mock()
            mock_pixmap = Mock()
            mock_icon.pixmap.return_value = mock_pixmap
            mock_qicon.return_value = mock_icon

            # Act
            util.setPlusIcon(mock_mbox)

            # Assert
            mock_qicon.assert_called_once_with(str(Path('/path/to/resources/Icons/plus-notification.svg')))
            mock_qsize.assert_called_once_with(64, 64)  # Default size
            mock_mbox.setIconPixmap.assert_called_once_with(mock_pixmap)
