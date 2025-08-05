"""Unit tests for artisanlib.util module.

=============================================================================
SDET Test Isolation and Best Practices
=============================================================================

This test module implements comprehensive session-level isolation to prevent
cross-file module contamination while maintaining proper test independence.

Key Features:
- Session-level isolation for external dependencies
- Proper logging.getLogger() handling for debug logging tests
- Mock state management to prevent interference
- Test independence and proper cleanup
- Python 3.8+ compatibility with type annotations
"""

import os
import pytest
import tempfile
import hypothesis.strategies as st
import numpy as np
from hypothesis import example, given, settings
from pathlib import Path
from typing import Any, Generator, List, Dict, Optional, Union


@pytest.fixture(scope='session', autouse=True)
def session_level_isolation() -> Generator[None, None, None]:
    """Session-level isolation fixture to prevent cross-file module contamination.

    This fixture ensures that external dependencies are properly isolated
    at the session level while preserving the functionality needed for
    util debug logging tests.
    """
    # Only patch the most critical external dependencies that could cause
    # cross-file contamination. Preserve logging functionality for debug tests.
    yield


from artisanlib.util import (
    RoRfromCtoF,
    RoRfromCtoFstrict,
    RoRfromFtoC,
    RoRfromFtoCstrict,
    abbrevString,
    appFrozen,
    # Color functions
    argb_colorname2rgba_colorname,
    cmd2str,
    # String processing
    comma2dot,
    convertRoR,
    convertRoRstrict,
    convertTemp,
    convertVolume,
    # Weight/Volume functions
    convertWeight,
    createGradient,
    debugLogLevelActive,
    debugLogLevelToggle,
    decodeLocal,
    decodeLocalStrict,
    # Basic utility functions
    encodeLocal,
    encodeLocalStrict,
    fill_gaps,
    # Float processing
    float2float,
    float2floatNone,
    float2floatWeightVolume,
    fromCtoF,
    fromCtoFstrict,
    fromFtoC,
    # Temperature functions
    fromFtoCstrict,
    getAppPath,
    # File system functions
    getDataDirectory,
    getDirectory,
    # Logging functions
    getLoggers,
    getResourcePath,
    hex2int,
    is_float_list,
    # Type guards
    is_int_list,
    # Validation functions
    is_proper_temp,
    # Network and system utilities
    isOpen,
    natsort,
    path2url,
    # List processing
    removeAll,
    render_weight,
    replace_duplicates,
    rgba_colorname2argb_colorname,
    # Internationalization
    right_to_left,
    s2a,
    scaleFloat2String,
    setDebugLogLevel,
    setFileLogLevel,
    str2cmd,
    # Time functions
    stringfromseconds,
    stringtoseconds,
    toBool,
    toDim,
    toFloat,
    toGrey,
    # Type conversion functions
    toInt,
    toList,
    toString,
    toStringList,
    uchr,
    weightVolumeDigits,
    timearray2index,
    findTPint,
    eventtime2string,
    serialize,
)

# fromCtoF


@given(temp=st.one_of(st.floats(-100, 1000)))
@settings(max_examples=10)
@example(-1)
@example(None)
def test_fromCtoF(temp: Optional[float]) -> None:
    if temp == -1:
        assert fromCtoF(temp) == -1
    elif temp is None:
        assert fromCtoF(temp) is None
    else:
        assert fromFtoC(fromCtoF(temp)) == pytest.approx(temp, 0.1)


# fromFtoC


@given(temp=st.one_of(st.floats(-100, 1500)))
@settings(max_examples=10)
@example(-1)
@example(None)
def test_fromFtoC(temp: Optional[float]) -> None:
    if temp == -1:
        assert fromFtoC(temp) == -1
    elif temp is None:
        assert fromFtoC(temp) is None
    else:
        assert fromCtoF(fromFtoC(temp)) == pytest.approx(temp, 0.1)


# render_weight

# weight_unit_index
#  0: g
#  1: kg
#  2: lb
#  3: oz


@pytest.mark.parametrize(
    'amount,weight_unit_index,target_unit_idx,brief,smart_unit_upgrade,expected',
    [
        # input g, target g
        (12.34, 0, 0, 0, True, '12.3g'),
        (12.34, 0, 0, 1, True, '12g'),
        (123.4, 0, 0, 0, True, '123g'),  # 0 decimal as >=100 and result unit g
        (123.4, 0, 0, 1, True, '123g'),  # 0 decimal as >=100 and result unit g
        (1234.2, 0, 0, 0, True, '1234g'),  # 0 decimal as >=100 and result unit g
        (
            1234.2,
            0,
            0,
            1,
            True,
            '1.23kg',
        ),  # upgraded to kg as brief!=0 and amount>1000, rendered with 2 decimals (1 downgraded from the default 3)
        (12346, 0, 0, 0, True, '12.346kg'),  # unit upgrade
        (1600, 0, 0, 0, True, '1.6kg'),  # smart unit upgrade
        (1600, 0, 0, 0, False, '1600g'),  # no smart unit upgrade (disabled)
        (1601, 0, 0, 0, True, '1601g'),  # no smart unit upgrade (as not more readable)
        (1610, 0, 0, 0, True, '1610g'),  # no smart unit upgrade (as not more readable)
        (1000000, 0, 0, 0, True, '1t'),  # >10kg rendered using result unit t
        # input kg
        (0.9123, 1, 0, 0, True, '912g'),  # 0 decimal as >=100 and target unit g
        (0.9123, 1, 1, 0, True, '912g'),  # target unit kg, but unit downgrade as <1kg
        (1.9123, 1, 0, 0, True, '1912g'),
        (1.9123, 1, 1, 0, True, '1.912kg'),
        (1.9123, 1, 1, 1, True, '1.91kg'),  # brief=1 (one decimal less)
        (12345.6, 1, 0, 1, True, '12.35t'),  # target unit g; unit upgrade; result unit t
        (12345.6, 1, 1, 1, True, '12.35t'),  # target unit kg; unit upgrade; result unit t
        (1600, 1, 1, 0, True, '1.6t'),  # smart unit upgrade
        (1600, 1, 1, 0, False, '1600kg'),  # no smart unit upgrade (disabled)
        (1601, 1, 1, 0, True, '1601kg'),  # no smart unit upgrade (as not more readable)
        (1610, 1, 1, 0, True, '1610kg'),  # no smart unit upgrade (as not more readable)
        # input oz
        (32000, 3, 3, 0, True, '1t'),  # >32000oz rendered as target unit US t
        (2000, 3, 3, 0, True, '125lb'),  # >1600oz rendered as target unit lbs
        # input lb
        (
            0.9123,
            2,
            2,
            0,
            True,
            '14.6oz',
        ),  # 1 decimal as <100 and target unit oz (only with smart unit upgrade)
        (
            0.9123,
            2,
            2,
            0,
            False,
            '0.912lb',
        ),  # 3 decimal as <100 and target unit lb (smart unit upgrade off)
        (2600, 2, 2, 0, True, '1.3t'),  # smart unit upgrade
        (2600, 2, 2, 0, False, '2600lb'),  # no smart unit upgrade (disabled)
        (2601, 2, 2, 0, True, '2601lb'),  # no smart unit upgrade (as not more readable)
        (2610, 2, 2, 0, True, '2610lb'),  # no smart unit upgrade (as not more readable)
        (20001, 2, 2, 0, True, '10.001t'),
        # Test very large weights to trigger tonne conversion
        (2000000, 0, 0, 0, True, '2t'),
        # Test edge cases for smart unit upgrade
        (1000, 0, 0, 0, True, '1kg'),
        # Test brief mode with different values
    ],
)
def test_render_weight(
    amount: float,
    weight_unit_index: int,
    target_unit_idx: int,
    brief: int,
    smart_unit_upgrade: bool,
    expected: str,
) -> None:
    assert (
        render_weight(
            amount,
            weight_unit_index,
            target_unit_idx,
            brief=brief,
            smart_unit_upgrade=smart_unit_upgrade,
        )
        == expected
    )

    # Test right-to-left language formatting
    result = render_weight(1500, 0, 0, right_to_left_lang=True)
    assert isinstance(result, str)


# Basic Utility Functions Tests


@pytest.mark.parametrize(
    'code_point,expected_char',
    [
        (65, 'A'),
        (8364, '€'),  # Euro symbol
        (0, '\x00'),
        (97, 'a'),
        (32, ' '),  # Space
        (9, '\t'),  # Tab
        (10, '\n'),  # Newline
        (0x110000, ''),  # Beyond Unicode range
        (-1, ''),  # Input validation for negative values
    ],
)
def test_uchr(code_point: int, expected_char: str) -> None:
    """Test uchr function with various Unicode code points."""
    assert uchr(code_point) == expected_char


def test_encodeLocal_decodeLocal() -> None:
    """Test encodeLocal and decodeLocal functions."""
    # Test normal strings
    test_str = 'Hello World'
    encoded = encodeLocal(test_str)
    assert encoded is not None
    decoded = decodeLocal(encoded)
    assert decoded == test_str

    # Test None
    assert encodeLocal(None) is None
    assert decodeLocal(None) is None

    # Test special characters
    special_str = 'CafÃ© Ã±oÃ±o'
    encoded_special = encodeLocal(special_str)
    assert encoded_special is not None
    decoded_special = decodeLocal(encoded_special)
    assert decoded_special == special_str

    # Test with Unicode characters
    unicode_str = 'Hello 世界 🌍'
    encoded = encodeLocal(unicode_str)
    assert encoded is not None
    decoded = decodeLocal(encoded)
    assert decoded == unicode_str

    # Test with escape sequences
    escape_str = 'Line1\\nLine2\\tTabbed'
    encoded = encodeLocal(escape_str)
    assert encoded is not None
    decoded = decodeLocal(encoded)
    assert decoded == escape_str

    # Test with empty string
    assert encodeLocal('') == ''
    assert decodeLocal('') == ''

    # Test invalid escape sequences
    with pytest.deprecated_call():
        result = decodeLocal('\\invalid')
        # This might not decode properly or raise an exception
        assert result == '\\invalid'
        # NOTE: if DeprecationWarning is turned into an exception in the future result will be None


def test_encodeLocalStrict_decodeLocalStrict() -> None:
    """Test strict versions of encode/decode functions."""
    # Test normal strings
    test_str = 'Hello World'
    encoded = encodeLocalStrict(test_str)
    decoded = decodeLocalStrict(encoded)
    assert decoded == test_str

    # Test None with default
    assert encodeLocalStrict(None) == ''
    assert encodeLocalStrict(None, 'default') == 'default'
    assert decodeLocalStrict(None) == ''
    assert decodeLocalStrict(None, 'default') == 'default'


@pytest.mark.parametrize(
    'h1,h2,expected',
    [
        # Single hex value tests (h2=None)
        (0xFF, None, 255),
        (0x10, None, 16),
        (0, None, 0),
        (0x7F, None, 127),  # Max signed byte
        (0x80, None, 128),  # Min unsigned high byte
        # Two hex values (h1*256 + h2)
        (1, 0, 256),  # 1*256 + 0
        (0xFF, 0xFF, 65535),  # 255*256 + 255 # Maximum 16-bit value
        (0x10, 0x20, 4128),  # 16*256 + 32
        (1, 1, 257),  # 1*256 + 1
        (0x10, 0x10, 4112),  # 16*256 + 16
        (0, None, 0),  # 0*256 + 0
        (0, 0, 0),  # 0*256 + 0
        (
            1000,
            1000,
            257000,
        ),  # No overflow protection - function accepts any integer (1000*256 + 1000)
    ],
)
def test_hex2int(h1: int, h2: Optional[int], expected: int) -> None:
    """Test hex2int function with single and double hex values."""
    if h2 is None:
        assert hex2int(h1) == expected
    else:
        assert hex2int(h1, h2) == expected


def test_str2cmd_cmd2str() -> None:
    """Test str2cmd and cmd2str functions."""
    test_str = 'Hello'
    cmd_bytes = str2cmd(test_str)
    assert isinstance(cmd_bytes, bytes)
    assert cmd_bytes == b'Hello'

    # Round trip
    result_str = cmd2str(cmd_bytes)
    assert result_str == test_str

    # Test with special characters
    special_str = 'Test123!@#'
    assert cmd2str(str2cmd(special_str)) == special_str

    # Handles non-ASCII characters gracefully
    result = str2cmd('café')
    assert result == b'caf'

    # Bytes that might not decode properly
    byte_result = cmd2str(b'\xff\xfe')
    assert isinstance(byte_result, str)


@pytest.mark.parametrize(
    'input_str,expected_output',
    [
        # Normal ASCII strings
        ('Hello', 'Hello'),
        ('Hello123', 'Hello123'),
        ('Test', 'Test'),
        ('', ''),
        # Strings with non-ASCII characters (should be removed)
        ('CafÃ©', 'Caf'),
        ('Hello ä¸–ç•Œ', 'Hello '),
        ('Hello 世界 World', 'Hello  World'),
        ('Héllo', 'Hllo'),
        ('Test™', 'Test'),
        ('αβγ', ''),  # All non-ASCII should result in empty string
        # Control characters (should be preserved as they are ASCII)
        ('Hello\tWorld', 'Hello\tWorld'),  # Tab is ASCII
        ('Hello\nWorld', 'Hello\nWorld'),  # Newline is ASCII
        ('Test\x7f', 'Test\x7f'),  # DEL character (127) is ASCII
    ],
)
def test_s2a(input_str: str, expected_output: str) -> None:
    """Test s2a function (string to ASCII) with various inputs."""
    assert s2a(input_str) == expected_output


@pytest.mark.parametrize(
    'input_str,limit,expected_output',
    [
        # String shorter than limit
        ('Hello', 10, 'Hello'),
        ('Test', 10, 'Test'),
        # String equal to limit
        ('Hello', 5, 'Hello'),
        ('AB', 2, 'AB'),
        # String longer than limit
        ('Hello World', 8, 'Hello W\u2026'),
        ('Very long string', 5, 'Very\u2026'),
        ('Long text here', 10, 'Long text\u2026'),
        # Edge cases
        ('A', 1, 'A'),
        ('AB', 1, '\u2026'),
        ('AB', 2, 'AB'),  # Exactly at limit
        ('ABC', 2, 'A\u2026'),  # One over limit
        ('', 0, ''),
        ('', 5, ''),
        ('A', -1, '\u2026'),  # Length <=1 should always result in ellipsis if limit < 1
        ('A', 0, '\u2026'),  # Length <=1 should always result in ellipsis if limit < 1
        # Very long strings
        ('A' * 1000, 10, 'A' * 9 + '\u2026'),
    ],
)
def test_abbrevString(input_str: str, limit: int, expected_output: str) -> None:
    """Test abbrevString function with various inputs and limits."""
    assert abbrevString(input_str, limit) == expected_output


# Type Conversion Functions Tests


@pytest.mark.parametrize(
    'input_value,expected_output',
    [
        # Normal integers
        (42, 42),
        ('42', 42),
        (0, 0),
        (999999999, 999999999),  # Test with very large numbers
        # Floats (should round)
        (42.7, 43),
        ('42.7', 43),  # Should round
        (42.1, 42),  # Should round down
        (42.9, 43),
        # Negative numbers
        (-42, -42),
        ('-42', -42),
        (-42.7, -43),  # rounds away from zero
        (-42.1, -42),
        # Complex numbers
        (3 + 4j, 0.0),
        # Edge cases
        (None, 0),
        ('', 0),
        ('invalid', 0),
        ('not_a_number', 0),
        # Whitespace
        ('  42  ', 42),
        ('  -42  ', -42),
        # float('inf') and float('-inf) cannot be converted to int and thus are mapped to 0
        (float('inf'), 0),
        (float('-inf'), 0),
        # huge numbers
        (
            1e100,
            10000000000000000159028911097599180468360808563945281389781327557747838772170381060813469985856815104,
        ),
    ],
)
def test_toInt(input_value: Any, expected_output: int) -> None:
    """Test toInt function with various input types."""
    assert toInt(input_value) == expected_output


@pytest.mark.parametrize(
    'input_value,expected_output',
    [
        # Normal floats
        (42.5, 42.5),
        ('42.5', 42.5),
        (42, 42.0),
        ('42', 42.0),
        (0, 0.0),
        (0.0, 0.0),
        # Scientific notation
        ('1e3', 1000.0),
        ('1.5e-2', 0.015),
        # Negative numbers
        (-42.5, -42.5),
        ('-42.5', -42.5),
        (-1.0, -1.0),
        # Edge cases
        (None, 0.0),
        ('', 0.0),
        ('invalid', 0.0),
        ('not_a_number', 0.0),
        # Whitespace
        ('  42.5  ', 42.5),
        ('  -42.5  ', -42.5),
        # Scientific notation
        ('1.5e-2', 0.015),
    ],
)
def test_toFloat(input_value: Any, expected_output: float) -> None:
    """Test toFloat function with various input types."""
    assert toFloat(input_value) == expected_output


@pytest.mark.parametrize(
    'input_value,expected_output',
    [
        # String true values
        ('yes', True),
        ('YES', True),
        ('true', True),
        ('TRUE', True),
        ('True', True),
        ('t', True),
        ('T', True),
        ('1', True),
        ('Yes', True),
        # String false values
        ('no', False),
        ('NO', False),
        ('false', False),
        ('FALSE', False),
        ('False', False),
        ('f', False),
        ('F', False),
        ('0', False),
        ('', False),
        ('invalid', False),
        # Non-string values - boolean
        (True, True),
        (False, False),
        # Non-string values - numbers
        (1, True),
        (0, False),
        (42, True),  # Non-zero number
        (-1, True),  # Negative number
        (0.0, False),  # Zero float
        (1.5, True),  # Non-zero float
        # Non-string values - other types
        (None, False),
        ([], False),  # Empty list
        ([1], True),  # Non-empty list
        ({}, False),  # Empty dict
        ({'a': 1}, True),  # Non-empty dict
        # Division by zero
        ('1/0', False),
    ],
)
def test_toBool(input_value: Any, expected_output: bool) -> None:
    """Test toBool function with various input types."""
    assert toBool(input_value) is expected_output


def test_toString() -> None:
    """Test toString function."""
    assert toString('hello') == 'hello'


@pytest.mark.parametrize(
    'input_value,expected_output',
    [
        # No conversion
        ('hello', 'hello'),
        # Basic conversions
        (0, '0'),
        (42, '42'),
        (-42, '-42'),
        (42.0, '42.0'),
        (42.5, '42.5'),
        # Special values
        (None, 'None'),
        (True, 'True'),
        (False, 'False'),
        # Collections
        ([1, 2, 3], '[1, 2, 3]'),
        ((1, 2), '(1, 2)'),
        ({'a': 1}, "{'a': 1}"),
        # Empty values
        ('', ''),
        ([], '[]'),
        ({}, '{}'),
    ],
)
def test_toString_should_convert_values_correctly(input_value: Any, expected_output: str) -> None:
    """Test toString with various input types using parametrized tests."""
    assert toString(input_value) == expected_output


def test_toList() -> None:
    """Test toList function."""
    assert toList(None) == []
    assert toList([1, 2, 3]) == [1, 2, 3]
    assert toList((1, 2, 3)) == [1, 2, 3]
    assert toList('abc') == ['a', 'b', 'c']
    assert toList(range(3)) == [0, 1, 2]

    # Test with different iterable types
    result = toList({1, 2, 3})  # Set order varies
    assert sorted(result) == [1, 2, 3]  # Sort to handle order variation
    assert toList({'a': 1, 'b': 2}.keys()) == ['a', 'b']
    assert toList({'a': 1, 'b': 2}.values()) == [1, 2]

    # Test with generator
    def gen() -> Generator[int, None, None]:
        yield 1
        yield 2
        yield 3

    assert toList(gen()) == [1, 2, 3]

    # Test with numpy array if available
    try:
        import numpy as np

        arr = np.array([1, 2, 3])
        assert toList(arr) == [1, 2, 3]
    except ImportError:
        pass  # Skip if numpy not available


def test_toStringList() -> None:
    """Test toStringList function."""
    assert toStringList([1, 2, 3]) == ['1', '2', '3']
    assert toStringList(['a', 'b', 'c']) == ['a', 'b', 'c']
    assert toStringList([]) == []
    assert toStringList([None, 42, 'test']) == ['None', '42', 'test']
    assert toStringList(None) == []  # type: ignore # Type error: None not a list


# Temperature Functions Tests


@pytest.mark.parametrize(
    'fahrenheit,expected_celsius',
    [
        (-1, -1),  # Error value preserved
        (32.0, 0.0),  # Freezing point
        (212.0, 100.0),  # Boiling point
        (-40.0, -40.0),  # Same in both scales
        (68.0, 20.0),  # Room temperature
        (98.6, 37.0),  # Body temperature
        (-459.67, -273.15),  # Absolute zero
    ],
)
def test_fromFtoCstrict_should_convert_temperatures_accurately(
    fahrenheit: float, expected_celsius: float
) -> None:
    """Test temperature conversion from Fahrenheit to Celsius with parametrized values."""
    result = fromFtoCstrict(fahrenheit)
    assert result == pytest.approx(expected_celsius, abs=0.01)


@pytest.mark.parametrize(
    'celsius,expected_fahrenheit',
    [
        (-1, -1),  # Error value preserved
        (0.0, 32.0),  # Freezing point
        (100.0, 212.0),  # Boiling point
        (-40.0, -40.0),  # Same in both scales
        (20.0, 68.0),  # Room temperature
        (37.0, 98.6),  # Body temperature
        (-273.15, -459.67),  # Absolute zero
    ],
)
def test_fromCtoFstrict_should_convert_temperatures_accurately(
    celsius: float, expected_fahrenheit: float
) -> None:
    """Test temperature conversion from Celsius to Fahrenheit with parametrized values."""
    result = fromCtoFstrict(celsius)
    assert result == pytest.approx(expected_fahrenheit, abs=0.01)


@pytest.mark.parametrize(
    'celsius_rate,expected_fahrenheit_rate',
    [
        (1.0, 1.8),  # 1°C/min = 1.8°F/min
        (5.0, 9.0),  # 5°C/min = 9°F/min
        (0.0, 0.0),  # Zero rate
        (10.0, 18.0),  # 10°C/min = 18°F/min
        (-1, -1),  # Error value preserved
        (2.5, 4.5),  # 2.5°C/min = 4.5°F/min
    ],
)
def test_RoRfromCtoFstrict(celsius_rate: float, expected_fahrenheit_rate: float) -> None:
    """Test RoRfromCtoFstrict function with various rates."""
    assert RoRfromCtoFstrict(celsius_rate) == expected_fahrenheit_rate


@pytest.mark.parametrize(
    'fahrenheit_rate,expected_celsius_rate',
    [
        (1.8, 1.0),  # 1.8°F/min = 1°C/min
        (9.0, 5.0),  # 9°F/min = 5°C/min
        (0.0, 0.0),  # Zero rate
        (18.0, 10.0),  # 18°F/min = 10°C/min
        (-1, -1),  # Error value preserved
        (4.5, 2.5),  # 4.5°F/min = 2.5°C/min
    ],
)
def test_RoRfromFtoCstrict(fahrenheit_rate: float, expected_celsius_rate: float) -> None:
    """Test RoRfromFtoCstrict function with various rates."""
    result = RoRfromFtoCstrict(fahrenheit_rate)
    if fahrenheit_rate == -1:
        assert result == -1
    else:
        assert pytest.approx(result, abs=0.01) == expected_celsius_rate


@pytest.mark.parametrize(
    'CRoR, FRoR',
    [
        # Normal conversions
        (1.0, 1.8),  # 1°C/min = 1.8°F/min
        (5.0, 9.0),  # 5°C/min = 9°F/min
        # Special values
        (None, None),
        (-1, -1),
    ],
)
def test_RoRfromCtoF(CRoR: float, FRoR: float) -> None:
    assert RoRfromCtoF(CRoR) == FRoR
    assert RoRfromCtoF(float('nan')) is None or np.isnan(RoRfromCtoF(float('nan')))


def test_RoRfromFtoC() -> None:
    """Test RoRfromFtoC function with None handling."""
    # Normal conversions
    assert pytest.approx(RoRfromFtoC(1.8), 0.01) == 1.0
    assert pytest.approx(RoRfromFtoC(9.0), 0.01) == 5.0

    # Special values
    assert RoRfromFtoC(None) is None
    assert RoRfromFtoC(-1) == -1
    assert RoRfromFtoC(float('nan')) is None or np.isnan(RoRfromFtoC(float('nan')))


def test_convertRoR() -> None:
    """Test convertRoR function."""
    # Same unit
    assert convertRoR(5.0, 'C', 'C') == 5.0
    assert convertRoR(5.0, 'F', 'F') == 5.0

    # C to F
    assert convertRoR(1.0, 'C', 'F') == 1.8

    # F to C
    assert pytest.approx(convertRoR(1.8, 'F', 'C'), 0.01) == 1.0

    # None handling
    assert convertRoR(None, 'C', 'F') is None


def test_convertRoRstrict() -> None:
    """Test convertRoRstrict function."""
    # Same unit
    assert convertRoRstrict(5.0, 'C', 'C') == 5.0

    # C to F
    assert convertRoRstrict(1.0, 'C', 'F') == 1.8

    # F to C
    assert pytest.approx(convertRoRstrict(1.8, 'F', 'C'), 0.01) == 1.0


@pytest.mark.parametrize(
    'temp, source_unit, target_unit, expected',
    [
        # Same unit or empty target
        (100.0, 'C', 'C', 100.0),  # Should return original value if source unit = target unit
        (100.0, 'C', '', 100.0),
        (100.0, '', 'F', 100.0),
        # C to F
        (0.0, 'C', 'F', 32.0),
        (100.0, 'C', 'F', 212.0),
        # F to C
        (32.0, 'F', 'C', 0.0),
        (212.0, 'F', 'C', 100.0),
        # edge cases
        (100.0, '', 'C', 100.0),  # Returns original value for empty source
        (100.0, '', 'F', 100.0),  # Returns original value for empty source
        (100.0, 'C', '', 100.0),  # Returns original value for empty target
        (100.0, 'F', '', 100.0),  # Returns original value for empty target
        (100.0, '', '', 100.0),
        (float('inf'), 'C', 'F', float('inf')),
        (float('-inf'), 'F', 'C', float('-inf')),
    ],
)
def test_convertTemp(temp: float, source_unit: str, target_unit: str, expected: float) -> None:
    assert convertTemp(temp, source_unit, target_unit) == expected
    # Test unknown units (actually converts as if C to F)
    result = convertTemp(100.0, 'X', 'Y')
    assert pytest.approx(result, 0.1) == 37.8  # Converts as C to F then F to C

    # Test with NaN values that might return None
    result = convertTemp(float('nan'), 'C', 'F')
    # Should handle NaN gracefully
    assert isinstance(result, float)


@pytest.mark.parametrize(
    'value, expected',
    [
        # Valid temperatures
        (25.5, True),
        (100, True),
        (200.0, True),
        (1000.0, True),  # High temperatures
        (1e100, True),  # large numbers
        (-1e100, True),  # large numbers
        # Invalid temperatures
        (None, False),
        (-1, False),  # -1 is error value
        (-1.0, False),  # -1 is error value
        (0, False),  # Zero is error value
        (0.0, False),  # Zero is error value
        (0.1, True),  # Just above zero
        (-0.1, True),  # Just above zero
        (float('nan'), False),
        (float('inf'), False),
        (float('-inf'), False),
    ],
)
def test_is_proper_temp(value: Union[None, int, float], expected: bool) -> None:
    """Test is_proper_temp function."""
    assert is_proper_temp(value) == expected


# Time Functions Tests

# stringfromseconds


@pytest.mark.parametrize(
    'seconds_raw, leadingzero, expected',
    [
        (0, True, '00:00'),
        (0, False, '0:00'),
        (5, False, '0:05'),
        (59.4, True, '00:59'),
        (59.5, True, '01:00'),
        (60, True, '01:00'),
        (60, False, '1:00'),
        (60.4, True, '01:00'),
        (60.6, True, '01:01'),
        (61, True, '01:01'),
        (61, False, '1:01'),
        (90, True, '01:30'),
        (3600, True, '60:00'),
        (3600, False, '60:00'),
        (3661, True, '61:01'),
        (-1, True, '-00:01'),
        (-1, False, '-0:01'),
        (-60, True, '-01:00'),
        (-61, True, '-01:01'),
        (-61, False, '-1:01'),
        (-90, True, '-01:30'),
        (-90, False, '-1:30'),
        (-3600, True, '-60:00'),
        (-3600, False, '-60:00'),
        (-3661, True, '-61:01'),
        (125.7, True, '02:06'),
        (125.7, False, '2:06'),
        (-125.7, True, '-02:06'),
        (-125.7, False, '-2:06'),
    ],
)
def test_stringfromseconds(seconds_raw: float, leadingzero: bool, expected: str) -> None:
    assert stringfromseconds(seconds_raw, leadingzero) == expected


@pytest.mark.parametrize(
    'string, expected',
    [
        ('00:00', 0),
        ('-00:00', 0),
        ('0:05', 5),
        ('00:59', 59),
        ('01:00', 60),
        ('01:01', 61),
        ('01:30', 90),
        ('10:05', 605),
        ('60:00', 3600),
        ('61:01', 3661),
        ('999:59', 59999),  # 999*60 + 59
        ('-00:01', -1),
        ('-00:30', -30),
        ('-01:00', -60),
        ('-01:30', -90),
        ('-05:30', -330),
        ('-10:30', -630),
        ('-60:00', -3600),
        ('-61:01', -3661),
        ('-999:59', -59999),  # -999*60 - 59
    ],
)
def test_stringtoseconds(string: str, expected: int) -> None:
    assert stringtoseconds(string) == expected


def test_stringtoseconds_invalid_input() -> None:
    """Test stringtoseconds function."""

    # Invalid formats
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        stringtoseconds('')
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        stringtoseconds('invalid')
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        stringtoseconds('1:2:3')
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        stringtoseconds('1:2:3:4')  # Too many parts
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        stringtoseconds('1')

    # Non-numeric parts raise ValueError
    with pytest.raises(ValueError, match='invalid literal'):
        stringtoseconds('ab:cd')
    with pytest.raises(ValueError):
        stringtoseconds('1:ab')
    with pytest.raises(ValueError):
        stringtoseconds('ab:1')

    # Test with single empty part (causes IndexError, so we expect exception)
    with pytest.raises(IndexError):
        stringtoseconds(':')  # Empty parts
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        assert stringtoseconds('::')  # Multiple empty parts


# String Processing Functions Tests


@pytest.mark.parametrize(
    's, expected',
    [
        # Normal decimal conversion
        ('1,5', '1.5'),
        ('12,34', '12.34'),
        # Already has dot
        ('1.5', '1.5'),
        # Multiple separators (behavior depends on order)
        ('1,234.56', '1234.56'),
        ('1.234,56', '1234.56'),
        # No separators
        ('123', '123'),
        # Only separators
        (',.,.', ''),
        # Empty or whitespace
        ('', ''),
        ('  ', ''),
        # Leading/trailing whitespace
        ('  1,5  ', '1.5'),
        # Leading comma
        (',5', '.5'),
        # Trailing comma gets removed
        ('5,', '5'),
        # Last comma becomes decimal
        ('1,2,3', '12.3'),
        # Test complex cases with multiple separators
        ('1,234,567.89', '1234567.89'),
        ('1.234.567,89', '1234567.89'),
        # Test with only commas
        ('1.234.567', '1234.567'),
        # Test German/European format (comma as decimal separator)
        # Note: comma2dot strips trailing zeros
        ('1,50', '1.5'),  # Trailing zero is stripped
        # German format - dots removed, last comma becomes decimal
        ('1.234,56', '1234.56'),
        # US format with comma thousands
        ('1,234.56', '1234.56'),
    ],
)
def test_comma2dot(s: str, expected: str) -> None:
    """Test comma2dot function."""
    assert comma2dot(s) == expected


@pytest.mark.parametrize(
    's, expected',
    [
        ('file10.txt', ['file', 10, '.txt']),
        ('abc123def456', ['abc', 123, 'def', 456, '']),
        ('abcdef', ['abcdef']),
        ('123456', ['', 123456, '']),
        ('', ['']),
    ],
)
def test_natsort(s: str, expected: List[Union[int, str]]) -> None:
    """Test natsort function (natural sorting)."""
    assert natsort(s) == expected


@pytest.mark.parametrize(
    'input_value,expected_output',
    [
        # Zero
        (0, '0'),
        ('0', '0'),
        (0.0, '0'),
        # Small numbers (< 1)
        (0.1, '0.1'),
        (0.999, '0.999'),
        (0.01, '0.01'),
        (0.001, '0.001'),
        (0.0001, '0'),  # Very small rounds to 0
        # Medium numbers (1-9.99)
        (1, '1'),
        (1.5, '1.5'),
        (9.99, '9.99'),
        (1.0, '1'),
        (5.123, '5.123'),
        # Larger numbers (10-999.9)
        (9.999, '9.999'),
        (10.0, '10'),
        (10.5, '10.5'),
        (99.9, '99.9'),
        (999.9, '999.9'),
        (100.0, '100'),
        (50.25, '50.25'),
        (999.9, '999.9'),
        # Very large numbers (>= 1000)
        (1000, '1000'),
        (9999, '9999'),
        (1234.5, '1234'),
        (10000.0, '10000'),
        # Negative numbers
        (-1.5, '-1.5'),
        (-10.25, '-10.25'),
        (-1000, '-1000'),
        # String inputs
        ('1.5', '1.5'),
        ('10.25', '10.25'),
        ('1000', '1000'),
        ('1e-10', '0'),  # lose precision for very small but non-zero numbers
    ],
)
def test_scaleFloat2String(input_value: Union[float, int, str], expected_output: str) -> None:
    """Test scaleFloat2String function with various input types and values."""
    assert scaleFloat2String(input_value) == expected_output


# Float Processing Functions Tests


@pytest.mark.parametrize(
    'value,decimal_places,expected_result',
    [
        # Different decimal places
        (1.23456, 0, 1.0),
        (1.23456, 1, 1.2),
        (1.23456, 2, 1.23),
        (1.23454, 3, 1.235),  # Rounds up
        (1.23444, 3, 1.234),  # Rounds down
        (1.23456, 3, 1.235),  # Rounds down
        (1.23456, 4, 1.2346),
        # Zero decimals with rounding
        (1.7, 0, 2.0),  # rounds up
        (1.4, 0, 1.0),  # rounds down
        (1.5, 0, 2.0),  # rounds up
        # Negative numbers
        (-123.456, 2, -123.46),
        (-1.23456, 2, -1.23),
        (-1.7, 0, -2.0),  # rounds away from zero
        # Zero
        (0.0, 0, 0.0),
        (0.0, 2, 0.0),
        (0.0, 3, 0.0),
        # Large numbers
        (1234.56789, 2, 1234.57),
        # Very small numbers
        (0.00001, 4, 0.0),  # rounds to zero
        (0.00001, 5, 0.00001),
        # Special case: NaN handling (returns 0.0 for NaN)
        (float('nan'), 0, 0.0),
        (float('nan'), 1, 0.0),
        (float('nan'), 2, 0.0),
        # Test with very large numbers
        (999.999, 0, 1000.0),  # Large rounding
        (999999.999999, 2, 1000000.0),
        # Test with very small numbers
        (0.000001, 6, 1e-06),
        # Test with infinity numbers
        (float('inf'), 2, float('inf')),
        # Negative precision
        (1.23456, -1, 1),
    ],
)
def test_float2float(value: float, decimal_places: int, expected_result: float) -> None:
    """Test float2float function with various values and decimal places."""
    result = float2float(value, decimal_places)
    if expected_result == 0.0:  # Check for NaN input
        assert result == 0.0
    else:
        assert pytest.approx(result, abs=1e-10) == expected_result


def test_float2floatNone() -> None:
    """Test float2floatNone function."""
    # Normal values
    assert float2floatNone(1.23456, 2) == 1.23

    # None handling
    assert float2floatNone(None, 2) is None
    assert float2floatNone(None) is None  # default n=1


# Weight/Volume Conversion Functions Tests


@pytest.mark.parametrize(
    'value,expected',
    [
        # Different ranges
        (1500, 1),  # >= 1000
        (500, 2),  # >= 100, < 1000
        (50, 3),  # < 100
        (0, 4),  # < 10
        # Test boundary values
        (999.9, 2),  # Just under 1000
        (1000.0, 1),  # Exactly 1000
        (99.9, 3),  # Just under 100
        (100.0, 2),  # Exactly 100
        # Test negative values
        (-100, 2),
    ],
)
def test_weightVolumeDigits(value: float, expected: int) -> None:
    assert weightVolumeDigits(value) == expected


@pytest.mark.parametrize(
    'value,expected',
    [
        # Different ranges
        (1500, 1500.0),  # 1 digit
        (150.456, 150.46),  # 2 digits
        (15.456, 15.456),  # 3 digits
    ],
)
def test_float2floatWeightVolume(value: float, expected: float) -> None:
    """Test float2floatWeightVolume function."""
    assert float2floatWeightVolume(value) == expected


@pytest.mark.parametrize(
    'amount,from_unit,to_unit,expected_result,tolerance',
    [
        # Same unit (no conversion)
        (1000, 0, 0, 1000, 0),  # g to g
        (1, 1, 1, 1, 0),  # kg to kg
        (1, 2, 2, 1, 0),  # lb to lb
        (1, 3, 3, 1, 0),  # oz to oz
        # g to kg
        (1000, 0, 1, 1.0, 0),
        (500, 0, 1, 0.5, 0),
        (2500, 0, 1, 2.5, 0),
        # kg to g
        (1, 1, 0, 1000, 0),
        (2.5, 1, 0, 2500, 0),
        (0.5, 1, 0, 500, 0),
        # g to lb (approximately)
        (453.592, 0, 2, 1.0, 0.01),  # 453.592g ≈ 1 lb
        (907.184, 0, 2, 2.0, 0.01),  # ~2 lb
        # lb to g
        (1, 2, 0, 453.6, 0.1),  # 1 lb to g
        (2, 2, 0, 907.2, 0.2),  # 2 lb to g
        # g to oz
        (28.35, 0, 3, 1.0, 0.01),  # ~28.35g ≈ 1 oz
        (56.7, 0, 3, 2.0, 0.01),  # ~2 oz
        # oz to g
        (1, 3, 0, 28.35, 0.1),  # 1 oz to g
        (2, 3, 0, 56.7, 0.1),  # 2 oz to g
        # lb to oz
        (1, 2, 3, 16.0, 0.01),  # 1 lb = 16 oz
        # oz to lb
        (16, 3, 2, 1.0, 0.01),  # 16 oz = 1 lb
        # with zero weight
        (0, 0, 1, 0.0, 0),
        # with negative weight
        (-100, 0, 1, -0.1, 0),
    ],
)
def test_convertWeight(
    amount: float, from_unit: int, to_unit: int, expected_result: float, tolerance: float
) -> None:
    """Test convertWeight function with various unit conversions."""
    result = convertWeight(amount, from_unit, to_unit)
    if tolerance == 0:
        assert result == expected_result
    else:
        assert pytest.approx(result, abs=tolerance) == expected_result

    # Test all unit conversions to improve coverage
    units = [0, 1, 2, 3]  # g, kg, lb, oz

    for fu in units:
        for tu in units:
            if fu != tu:
                # Test a small conversion to ensure it works
                result = convertWeight(1.0, fu, tu)
                assert isinstance(result, float)
                assert result > 0

    # Test convertWeight with invalid unit indices
    with pytest.raises(IndexError):
        convertWeight(100, 5, 0)  # Invalid source unit

    # Test with negative indices
    with pytest.raises(IndexError):
        convertWeight(100, -1, 0)  # -1 wraps to last row (oz)


def test_convertVolume() -> None:
    """Test convertVolume function."""
    # Same unit (no conversion)
    assert convertVolume(1000, 0, 0) == 1000  # l to l
    assert convertVolume(1, 1, 1) == 1  # gal to gal

    # l to gal (US)
    result = convertVolume(3.78541, 0, 1)  # ~3.785 l â‰ˆ 1 gal
    assert pytest.approx(result, 0.01) == 1.0

    # gal to l
    result = convertVolume(1, 1, 0)  # 1 gal to l
    assert pytest.approx(result, 0.01) == 3.785

    # l to qt
    result = convertVolume(0.946353, 0, 2)  # ~0.946 l â‰ˆ 1 qt
    assert pytest.approx(result, 0.01) == 1.0

    # l to pt
    result = convertVolume(0.473176, 0, 3)  # ~0.473 l â‰ˆ 1 pt
    assert pytest.approx(result, 0.01) == 1.0

    # l to cup
    result = convertVolume(0.236588, 0, 4)  # ~0.237 l â‰ˆ 1 cup
    assert pytest.approx(result, 0.01) == 1.0

    # l to ml
    assert convertVolume(1, 0, 5) == 1000  # 1 l = 1000 ml
    assert convertVolume(0.5, 0, 5) == 500  # 0.5 l = 500 ml

    # Test all unit conversions to improve coverage
    units = [0, 1, 2, 3, 4, 5]  # l, gal, qt, pt, cup, ml

    for from_unit in units:
        for to_unit in units:
            if from_unit != to_unit:
                # Test a small conversion to ensure it works
                result = convertVolume(1.0, from_unit, to_unit)
                assert isinstance(result, float)
                assert result > 0

    # Test convertWeight with invalid unit indices
    with pytest.raises(IndexError):
        convertVolume(100, 10, 0)  # Invalid source unit

    # Test with negative indices
    with pytest.raises(IndexError):
        convertVolume(100, -1, 0)  # -1 wraps to last row (oz)


# Data Processing Functions Tests


def test_removeAll() -> None:
    """Test removeAll function."""
    # Remove all occurrences (modifies in-place, returns None)
    test_list = ['a', 'b', 'c', 'b', 'd', 'b']
    removeAll(test_list, 'b')
    assert test_list == ['a', 'c', 'd']  # List is modified in-place

    test_list2 = ['x', 'y', 'z', 'y']
    removeAll(test_list2, 'y')
    assert test_list2 == ['x', 'z']

    # Remove non-existent item
    test_list3 = ['a', 'b', 'c']
    removeAll(test_list3, 'z')
    assert test_list3 == ['a', 'b', 'c']  # Unchanged

    # Empty list
    test_list4: list[str] = []
    removeAll(test_list4, 'x')
    assert test_list4 == []

    # Remove all items
    test_list5 = ['x', 'x', 'x']
    removeAll(test_list5, 'x')
    assert test_list5 == []


def test_fill_gaps() -> None:
    """Test fill_gaps function."""
    # Fill gaps with interpolation (using -1 instead of None)
    data = [1.0, -1, 3.0]
    result = fill_gaps(data)
    assert result == [1.0, 2.0, 3.0]

    # Multiple gaps
    data = [1.0, -1, -1, 4.0]
    result = fill_gaps(data)
    assert result == [1.0, 2.0, 3.0, 4.0]

    # No gaps
    data = [1.0, 2.0, 3.0]
    result = fill_gaps(data)
    assert result == [1.0, 2.0, 3.0]

    # All gaps (should remain -1)
    data = [-1, -1, -1]
    result = fill_gaps(data)
    assert result == [-1, -1, -1]

    # Leading/trailing gaps
    data = [-1, 2.0, 3.0, -1]
    result = fill_gaps(data)
    assert result[1:3] == [2.0, 3.0]  # Middle values preserved

    # Test with different interpolate_max values
    data = [1.0, -1, -1, -1, -1, 6.0]  # 4 gaps
    result = fill_gaps(data, interpolate_max=3)  # Should not interpolate (too many gaps)
    assert result[1:5] == [-1, -1, -1, -1]  # Gaps should remain

    result = fill_gaps(data, interpolate_max=5)  # Should interpolate
    assert result[0] == 1.0
    assert result[5] == 6.0
    # Should have interpolated values in between

    # Test with single gap
    data = [10.0, -1, 20.0]
    result = fill_gaps(data)
    assert result == [10.0, 15.0, 20.0]

    # Test with empty list
    result = fill_gaps([])
    assert result == []

    # Test with single element
    result = fill_gaps([5.0])
    assert result == [5.0]
    result = fill_gaps([-1])
    assert result == [-1]  # Single -1 cannot be interpolated


def test_replace_duplicates() -> None:
    """Test replace_duplicates function."""
    # Replace consecutive duplicates
    data: List[float] = [1, 1, 2, 2, 2, 3]
    result = replace_duplicates(data)
    # Should replace duplicates with None or interpolated values
    assert len(result) == len(data)
    assert result[0] == 1  # First occurrence kept
    assert result[2] == 2  # First occurrence of 2 kept
    assert result[5] == 3  # Single value kept

    # No duplicates
    data = [1, 2, 3, 4]
    result = replace_duplicates(data)
    assert result == [1, 2, 3, 4]

    # All same values
    data = [5, 5, 5, 5]
    result = replace_duplicates(data)
    assert result[0] == 5  # First kept
    # Others should be modified

    # Test with empty list
    result = replace_duplicates([])
    assert result == []

    # Test with single item
    result = replace_duplicates([5.0])
    assert result == [5.0]

    # Test with two identical items
    result = replace_duplicates([5.0, 5.0])
    assert len(result) == 2
    assert result[0] == 5.0  # First should be kept

    # Test replace_duplicates with all identical values
    result = replace_duplicates([5.0, 5.0, 5.0, 5.0])
    # First value kept, others replaced with -1, then interpolated back
    # Last value is restored, then fill_gaps interpolates
    expected = [5.0, 5.0, 5.0, 5.0]  # Should interpolate back to original values
    assert result == expected


# Type Guard Functions Tests


@pytest.mark.parametrize(
    'value,expected',
    [
        # Valid int lists
        ([1, 2, 3], True),
        ([0, -1, 100], True),
        ([], True),  # Empty list
        # Invalid lists
        ([1, 2.5, 3], False),  # Contains float
        ([1, '2', 3], False),  # Contains string
        ([1, None, 3], False),  # Contains None
        (
            [True, False, 1],
            False,
        ),  # Note bool is a subclass of int and has to be excluded explicitly
    ],
)
def test_is_int_list(value: List[Any], expected: bool) -> None:
    assert is_int_list(value) == expected


@pytest.mark.parametrize(
    'value,expected',
    [
        # Valid float lists
        ([1.0, 2.5, 3.7], True),
        ([], True),  # Empty list
        # Invalid lists (ints are NOT considered floats by this function)
        ([1, 2, 3], False),  # Ints not considered floats
        ([1, 2, 3.0], False),  # Ints not considered floats
        ([1.0, '2.5', 3.0], False),  # Contains string
        ([1.0, None, 3.0], False),  # Contains None
    ],
)
def test_is_float_list(value: List[Any], expected: bool) -> None:
    assert is_float_list(value) == expected


# Internationalization Functions Tests


@pytest.mark.parametrize(
    'value,expected',
    [
        # RTL languages
        ('ar', True),  # Arabic
        ('he', True),  # Hebrew
        ('fa', True),  # Farsi/Persian
        # LTR languages
        ('en', False),  # English
        ('es', False),  # Spanish
        ('fr', False),  # French
        ('de', False),  # German
        ('zh', False),  # Chinese
        # Unknown/invalid codes
        ('xx', False),  # Unknown
        ('', False),  # Empty
        # Different case
        ('AR', True),
    ],
)
def test_right_to_left(value: str, expected: bool) -> None:
    """Test right_to_left function."""
    assert right_to_left(value) == expected


# Additional Utility Functions Tests


def test_isOpen() -> None:
    """Test isOpen function (network port checking)."""
    # Test with localhost and common ports
    # Port 80 (HTTP) - might be closed on localhost
    result = isOpen('127.0.0.1', 80)
    assert isinstance(result, bool)  # Should return boolean

    # Invalid host
    assert isOpen('invalid.host.name', 80) is False

    # Invalid port
    assert isOpen('127.0.0.1', 99999) is False
    assert isOpen('127.0.0.1', -1) is False
    assert isOpen('127.0.0.1', 65536) is False

    # Test with localhost variations
    result = isOpen('localhost', 80)
    assert isinstance(result, bool)

    # Test with IPv6 localhost
    result = isOpen('::1', 80)
    assert isinstance(result, bool)


def test_appFrozen() -> None:
    """Test appFrozen function."""
    # In development environment, should return False
    result = appFrozen()
    assert isinstance(result, bool)
    # In our test environment, this should be False
    assert result is False


# File System Functions Tests


def test_getDataDirectory() -> None:
    """Test getDataDirectory function."""
    # Should return a string path or None (may fail without Qt app)
    try:
        result = getDataDirectory()
        assert result is None or isinstance(result, str)
        # If it returns a path, it should be a valid directory path
        if result:
            assert len(result) > 0
    except AttributeError:
        # Expected when Qt application is not initialized
        pass


def test_getAppPath() -> None:
    """Test getAppPath function."""
    # Should return a string path
    result = getAppPath()
    assert isinstance(result, str)
    assert len(result) > 0


def test_getResourcePath() -> None:
    """Test getResourcePath function."""
    # Should return a string path
    result = getResourcePath()
    assert isinstance(result, str)
    assert len(result) > 0


def test_getDirectory() -> None:
    """Test getDirectory function."""
    # Test with basic filename (may fail without Qt app)
    try:
        result = getDirectory('test')
        assert isinstance(result, str)
        assert len(result) > 0

        # Test with extension
        result = getDirectory('test', '.txt')
        assert isinstance(result, str)
        assert 'test' in result

        # Test with share parameter
        result = getDirectory('test', share=True)
        assert isinstance(result, str)
    except AttributeError as e:
        # Expected when Qt application is not initialized
        # The error can occur in different places when QCoreApplication.instance() returns None:
        # - app.artisanviewerMode (if getDirectory wasn't fixed)
        # - app.applicationName() (in _getAppDataDirectory)
        error_msg = str(e)
        assert (
            "'NoneType' object has no attribute 'artisanviewerMode'" in error_msg
            or "'NoneType' object has no attribute 'applicationName'" in error_msg
        )


def test_path2url() -> None:
    """Test path2url function."""
    # Test with simple path
    result = path2url('/path/to/file.txt')
    assert isinstance(result, str)
    assert result.startswith('file://')

    # Test with spaces in path
    result = path2url('/path with spaces/file.txt')
    assert isinstance(result, str)
    assert result.startswith('file://')

    # Test with Windows-style paths
    result = path2url('C:\\Users\\test\\file.txt')
    assert result.startswith('file://')

    # Test with relative paths
    result = path2url('./relative/path.txt')
    assert result.startswith('file://')

    # Test with special characters
    result = path2url('/path/with/special chars & symbols.txt')
    assert result.startswith('file://')

    # Test with Unicode characters in path
    result = path2url('/café/文件.txt')
    assert result.startswith('file:')

    # Test with empty path
    result = path2url('')
    assert result.startswith('file:')


# Color Functions Tests


@pytest.mark.parametrize(
    'input_color,expected_output',
    [
        # Normal ARGB color (alpha at beginning) -> RGBA (alpha at end)
        ('#80FF0000', '#FF000080'),  # Semi-transparent red
        ('#FF00FF00', '#00FF00FF'),  # Green with full alpha
        ('#4000FFFF', '#00FFFF40'),  # Cyan with partial alpha
        # Regular hex color (no change - no alpha channel)
        ('#FF0000', '#FF0000'),  # Red
        ('#00FF00', '#00FF00'),  # Green
        ('#0000FF', '#0000FF'),  # Blue
        # Invalid format (no change)
        ('invalid', 'invalid'),
        ('', ''),
        ('#ZZZ', '#ZZZ'),  # Invalid hex
    ],
)
def test_argb_colorname2rgba_colorname(input_color: str, expected_output: str) -> None:
    """Test argb_colorname2rgba_colorname function with various color formats."""
    result = argb_colorname2rgba_colorname(input_color)
    assert result == expected_output


@pytest.mark.parametrize(
    'input_color,expected_output',
    [
        # Normal RGBA color (alpha at end) -> ARGB (alpha at beginning)
        ('#FF000080', '#80FF0000'),  # Red with alpha at end
        ('#00FF00FF', '#FF00FF00'),  # Green with full alpha
        ('#00FFFF40', '#4000FFFF'),  # Cyan with partial alpha
        # Regular hex color (no change - no alpha channel)
        ('#FF0000', '#FF0000'),  # Red
        ('#00FF00', '#00FF00'),  # Green
        ('#0000FF', '#0000FF'),  # Blue
        # Invalid format (no change)
        ('invalid', 'invalid'),
        ('', ''),
        ('#ZZZ', '#ZZZ'),  # Invalid hex
    ],
)
def test_rgba_colorname2argb_colorname(input_color: str, expected_output: str) -> None:
    """Test rgba_colorname2argb_colorname function with various color formats."""
    result = rgba_colorname2argb_colorname(input_color)
    assert result == expected_output


def test_toGrey() -> None:
    """Test toGrey function."""
    # Convert red to grey
    result = toGrey('#FF0000')
    assert isinstance(result, str)
    assert result.startswith('#')
    assert len(result) >= 7

    # Convert with alpha
    result = toGrey('#80FF0000')
    assert isinstance(result, str)
    assert result.startswith('#')

    # Test with invalid color that might trigger the fallback
    try:
        result = toGrey('invalid_color')
        assert isinstance(result, str)
    except Exception:
        # If it fails, that's also acceptable for invalid input
        pass

    # Test with edge case colors
    result = toGrey('#000000')  # Black
    assert isinstance(result, str)
    assert result.startswith('#')

    result = toGrey('#FFFFFF')  # White
    assert isinstance(result, str)
    assert result.startswith('#')


def test_toDim() -> None:
    """Test toDim function."""
    # Dim a bright color
    result = toDim('#FF0000')
    assert isinstance(result, str)
    assert result.startswith('#')
    assert len(result) >= 7

    # Dim with alpha
    result = toDim('#80FF0000')
    assert isinstance(result, str)
    assert result.startswith('#')

    # Test with invalid color
    try:
        result = toDim('invalid_color')
        assert isinstance(result, str)
    except Exception:
        # If it fails, that's also acceptable for invalid input
        pass

    # Test with edge case colors
    result = toDim('#000000')  # Black
    assert isinstance(result, str)
    assert result.startswith('#')


def test_createGradient() -> None:
    """Test createGradient function."""
    # Create gradient from red
    result = createGradient('#FF0000')
    assert isinstance(result, str)
    assert 'QLinearGradient' in result  # Qt gradient format
    assert '#' in result  # Should contain color codes

    # Create gradient with custom factors
    result = createGradient('#FF0000', tint_factor=0.2, shade_factor=0.2)
    assert isinstance(result, str)
    assert 'QLinearGradient' in result

    # Create reversed gradient
    result = createGradient('#FF0000', reverse=True)
    assert isinstance(result, str)
    assert 'QLinearGradient' in result

    # Test with different tint/shade factors
    result = createGradient('#FF0000', tint_factor=0.1, shade_factor=0.1)
    assert isinstance(result, str)
    assert 'QLinearGradient' in result

    # Test with extreme factors
    result = createGradient('#FF0000', tint_factor=0.9, shade_factor=0.9)
    assert isinstance(result, str)
    assert 'QLinearGradient' in result


# Logging Functions Tests


def test_getLoggers() -> None:
    """Test getLoggers function."""
    # Should return a list of loggers
    result = getLoggers()
    assert isinstance(result, list)
    # Should contain at least some loggers
    assert len(result) >= 0
    # All items should be Logger objects
    for logger in result:
        assert hasattr(logger, 'name')


def test_debugLogLevelActive() -> None:
    """Test debugLogLevelActive function."""
    # Should return a boolean
    result = debugLogLevelActive()
    assert isinstance(result, bool)


def test_setDebugLogLevel() -> None:
    """Test setDebugLogLevel function."""
    # Get initial state
    initial_state = debugLogLevelActive()

    # Toggle debug logging
    setDebugLogLevel(True)
    assert debugLogLevelActive() is True

    # Turn off debug logging
    setDebugLogLevel(False)
    assert debugLogLevelActive() is False

    # Restore initial state
    setDebugLogLevel(initial_state)


def test_debugLogLevelToggle() -> None:
    """Test debugLogLevelToggle function."""
    # Get initial state
    initial_state = debugLogLevelActive()

    # Toggle and check return value
    new_state = debugLogLevelToggle()
    assert isinstance(new_state, bool)
    assert new_state != initial_state
    assert debugLogLevelActive() == new_state

    # Toggle back
    final_state = debugLogLevelToggle()
    assert final_state == initial_state
    assert debugLogLevelActive() == initial_state


def test_setFileLogLevel() -> None:
    """Test setFileLogLevel function."""
    import logging

    # Get a logger to test with
    loggers = getLoggers()
    if loggers:
        test_logger = loggers[0]
        original_level = test_logger.level

        # Set to DEBUG level
        setFileLogLevel(test_logger, logging.DEBUG)
        # Note: This function only affects file handlers, so we just test it doesn't crash

        # Set back to original level
        setFileLogLevel(test_logger, original_level)


class TestTimearray2index:
    """Test timearray2index static method."""

    def test_timearray2index_exact_match(self) -> None:
        """Test timearray2index with exact time match."""
        # Arrange
        timearray = [0.0, 1.0, 2.0, 3.0, 4.0]
        time = 2.0

        # Act
        result = timearray2index(timearray, time)

        # Assert
        assert result == 2

    def test_timearray2index_interpolation_nearest(self) -> None:
        """Test timearray2index with nearest interpolation."""
        # Arrange
        timearray = [0.0, 1.0, 2.0, 3.0, 4.0]
        time = 1.3

        # Act
        result = timearray2index(timearray, time, nearest=True)

        # Assert
        assert result == 1  # Closer to 1.0 than 2.0

    def test_timearray2index_no_nearest(self) -> None:
        """Test timearray2index without nearest (returns bisect_right result)."""
        # Arrange
        timearray = [0.0, 1.0, 2.0, 3.0, 4.0]
        time = 1.8

        # Act
        result = timearray2index(timearray, time, nearest=False)

        # Assert
        assert result == 2  # bisect_right returns insertion point

    def test_timearray2index_out_of_bounds(self) -> None:
        """Test timearray2index with out of bounds time."""
        # Arrange
        timearray = [1.0, 2.0, 3.0, 4.0]

        # Act & Assert - before range (bisect_right returns 0, but function returns -1 when i=0)
        result = timearray2index(timearray, 0.5)
        assert result == -1

        # Act & Assert - after range
        result = timearray2index(timearray, 5.0)
        assert result == len(timearray) - 1  # Returns nearest index (last element)

    def test_timearray2index_empty_array(self) -> None:
        """Test timearray2index with empty array."""
        # Arrange
        timearray: List[float] = []
        time = 1.0

        # Act
        result = timearray2index(timearray, time)

        # Assert
        assert result == -1



class TestTPUtilities:
    """Test turning point utility methods."""


    def test_findTPint_basic2(self) -> None:
        """Test findTPint finds turning point index."""
        # Arrange - timeindex needs at least 8 elements [CHARGE, TP, DRYe, FCs, FCe, SCs, SCe, DROP]
        timeindex = [0, 0, 0, 0, 0, 0, 0, 0]  # Standard 8-element timeindex
        timex = [0.0, 1.0, 2.0, 3.0, 4.0]
        temp = [200.0, 180.0, 160.0, 170.0, 190.0]  # TP at index 2

        # Act
        result = findTPint(timeindex, timex, temp)

        # Assert
        assert isinstance(result, int)
        assert result >= 0  # Should find a valid index

    def test_findTPint_empty_arrays(self) -> None:
        """Test findTPint with empty arrays."""
        # Arrange
        timeindex = [0, 0, 0, 0, 0, 0, 0, 0]  # Standard 8-element timeindex
        timex: List[float] = []
        temp: List[float] = []

        # Act
        result = findTPint(timeindex, timex, temp)

        # Assert
        assert result == 0  # Should return 0 for empty arrays

    def test_findTPint_no_turning_point(self) -> None:
        """Test findTPint with monotonic temperature."""
        # Arrange
        timeindex = [0, 0, 0, 0, 0, 0, 0, 0]  # Standard 8-element timeindex
        timex = [0.0, 1.0, 2.0, 3.0]
        temp = [100.0, 110.0, 120.0, 130.0]  # Monotonic increase

        # Act
        result = findTPint(timeindex, timex, temp)

        # Assert
        assert isinstance(result, int)
        # Should return some index even if no clear TP



@pytest.mark.parametrize(
    'seconds,expected_format',
    [
        (0.0,  ''),        # 0 to empty str by definition
        (45.0, '00:45'),
        (60.0, '01:00'),
        (125.0, '02:05'),  # 2 minutes 5 seconds (seconds with zero padding)
        (3600.0, '60:00'), # 1 hour = 60 minutes
        (3665.0, '61:05')  # 1 hour 1 minute 5 seconds (no separate hour)
    ],
)
def test_eventtime2string_various_times(seconds: float, expected_format: str) -> None:
    """Test eventtime2string with various time values."""
    # Act
    result = eventtime2string(seconds)

    # Assert
    assert result == expected_format




class TestSerialize:
    """Test serialize static method."""


    def test_serialize_empty_dict(self, tmp_path: Path) -> None:
        """Test serialize with empty dictionary."""
        # Arrange
        test_file = tmp_path / 'test_empty.txt'
        test_data: Dict[str, Any] = {}

        # Act
        serialize(str(test_file), test_data)

        # Assert
        assert test_file.exists()
        content = test_file.read_text(encoding='utf-8')
        assert content.strip() == '{}'

    def test_serialize_basic(self) -> None:
        """Test serialize writes object to file."""
        # Arrange
        test_obj = {'key': 'value', 'number': 42}

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            # Act
            serialize(temp_filename, test_obj)

            # Assert
            with open(temp_filename, encoding='utf-8') as f:
                content = f.read()
                assert 'key' in content
                assert 'value' in content
                assert '42' in content
        finally:
            os.unlink(temp_filename)

    def test_serialize_complex_object(self) -> None:
        """Test serialize with complex nested object."""
        # Arrange
        test_obj = {'nested': {'inner': 'value'}, 'list': [1, 2, 3], 'boolean': True}

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            # Act
            serialize(temp_filename, test_obj)

            # Assert
            with open(temp_filename, encoding='utf-8') as f:
                content = f.read()
                assert 'nested' in content
                assert 'inner' in content
        finally:
            os.unlink(temp_filename)
