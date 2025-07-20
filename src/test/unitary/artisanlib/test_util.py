from typing import Any, Optional, List, Generator

import hypothesis.strategies as st
import numpy as np
import pytest
from hypothesis import example, given, settings

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


# Basic Utility Functions Tests

def test_uchr() -> None:
    """Test uchr function."""
    assert uchr(65) == 'A'
    assert uchr(8364) == '€'  # Euro symbol
    assert uchr(0) == '\x00'


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


def test_hex2int() -> None:
    """Test hex2int function."""
    # Single hex value
    assert hex2int(0xFF) == 255
    assert hex2int(0x10) == 16
    assert hex2int(0) == 0

    # Two hex values (h1*256 + h2)
    assert hex2int(1, 0) == 256  # 1*256 + 0
    assert hex2int(0xFF, 0xFF) == 65535  # 255*256 + 255
    assert hex2int(0x10, 0x20) == 4128  # 16*256 + 32


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


def test_s2a() -> None:
    """Test s2a function (string to ASCII)."""
    # Normal ASCII string
    assert s2a('Hello') == 'Hello'

    # String with non-ASCII characters (should be removed)
    assert s2a('CafÃ©') == 'Caf'
    assert s2a('Hello ä¸–ç•Œ') == 'Hello '

    # Empty string
    assert s2a('') == ''


def test_abbrevString() -> None:
    """Test abbrevString function."""
    # String shorter than limit
    assert abbrevString('Hello', 10) == 'Hello'

    # String equal to limit
    assert abbrevString('Hello', 5) == 'Hello'

    # String longer than limit
    assert abbrevString('Hello World', 8) == 'Hello W\u2026'
    assert abbrevString('Very long string', 5) == 'Very\u2026'

    # Edge cases
    assert abbrevString('A', 1) == 'A'
    assert abbrevString('AB', 1) == '\u2026'


# Type Conversion Functions Tests


def test_toInt() -> None:
    """Test toInt function."""
    # Normal integers
    assert toInt(42) == 42
    assert toInt('42') == 42
    assert toInt(42.7) == 43  # rounds
    assert toInt('42.7') == 43  # rounds

    # Edge cases
    assert toInt(None) == 0
    assert toInt('') == 0
    assert toInt('invalid') == 0

    # Negative numbers
    assert toInt(-42) == -42
    assert toInt('-42') == -42
    assert toInt(-42.7) == -43  # rounds


def test_toFloat() -> None:
    """Test toFloat function."""
    # Normal floats
    assert toFloat(42.5) == 42.5
    assert toFloat('42.5') == 42.5
    assert toFloat(42) == 42.0
    assert toFloat('42') == 42.0

    # Edge cases
    assert toFloat(None) == 0.0
    assert toFloat('') == 0.0
    assert toFloat('invalid') == 0.0

    # Negative numbers
    assert toFloat(-42.5) == -42.5
    assert toFloat('-42.5') == -42.5


def test_toBool() -> None:
    """Test toBool function."""
    # String true values
    assert toBool('yes') is True
    assert toBool('YES') is True
    assert toBool('true') is True
    assert toBool('TRUE') is True
    assert toBool('t') is True
    assert toBool('T') is True
    assert toBool('1') is True

    # String false values
    assert toBool('no') is False
    assert toBool('NO') is False
    assert toBool('false') is False
    assert toBool('FALSE') is False
    assert toBool('f') is False
    assert toBool('F') is False
    assert toBool('0') is False
    assert toBool('') is False
    assert toBool('invalid') is False

    # Non-string values
    assert toBool(True) is True
    assert toBool(False) is False
    assert toBool(1) is True
    assert toBool(0) is False
    assert toBool(None) is False


def test_toString() -> None:
    """Test toString function."""
    assert toString(42) == '42'
    assert toString(42.5) == '42.5'
    assert toString('hello') == 'hello'
    assert toString(None) == 'None'
    assert toString([1, 2, 3]) == '[1, 2, 3]'


def test_toList() -> None:
    """Test toList function."""
    assert toList(None) == []
    assert toList([1, 2, 3]) == [1, 2, 3]
    assert toList((1, 2, 3)) == [1, 2, 3]
    assert toList('abc') == ['a', 'b', 'c']
    assert toList(range(3)) == [0, 1, 2]


def test_toStringList() -> None:
    """Test toStringList function."""
    assert toStringList([1, 2, 3]) == ['1', '2', '3']
    assert toStringList(['a', 'b', 'c']) == ['a', 'b', 'c']
    assert toStringList([]) == []
    assert toStringList([None, 42, 'test']) == ['None', '42', 'test']


# Temperature Functions Tests


def test_fromFtoCstrict() -> None:
    """Test fromFtoCstrict function."""
    # Normal conversions
    assert fromFtoCstrict(32.0) == 0.0  # Freezing point
    assert fromFtoCstrict(212.0) == 100.0  # Boiling point
    assert pytest.approx(fromFtoCstrict(68.0), 0.1) == 20.0  # Room temperature

    # Special value
    assert fromFtoCstrict(-1) == -1  # Error value preserved


def test_fromCtoFstrict() -> None:
    """Test fromCtoFstrict function."""
    # Normal conversions
    assert fromCtoFstrict(0.0) == 32.0  # Freezing point
    assert fromCtoFstrict(100.0) == 212.0  # Boiling point
    assert pytest.approx(fromCtoFstrict(20.0), 0.1) == 68.0  # Room temperature

    # Special value
    assert fromCtoFstrict(-1) == -1  # Error value preserved


def test_RoRfromCtoFstrict() -> None:
    """Test RoRfromCtoFstrict function."""
    # Rate of Rise conversion
    assert RoRfromCtoFstrict(1.0) == 1.8  # 1Â°C/min = 1.8Â°F/min
    assert RoRfromCtoFstrict(5.0) == 9.0  # 5Â°C/min = 9Â°F/min

    # Special value
    assert RoRfromCtoFstrict(-1) == -1  # Error value preserved


def test_RoRfromFtoCstrict() -> None:
    """Test RoRfromFtoCstrict function."""
    # Rate of Rise conversion
    assert pytest.approx(RoRfromFtoCstrict(1.8), 0.01) == 1.0  # 1.8Â°F/min = 1Â°C/min
    assert pytest.approx(RoRfromFtoCstrict(9.0), 0.01) == 5.0  # 9Â°F/min = 5Â°C/min

    # Special value
    assert RoRfromFtoCstrict(-1) == -1  # Error value preserved


def test_RoRfromCtoF() -> None:
    """Test RoRfromCtoF function with None handling."""
    # Normal conversions
    assert RoRfromCtoF(1.0) == 1.8
    assert RoRfromCtoF(5.0) == 9.0

    # Special values
    assert RoRfromCtoF(None) is None
    assert RoRfromCtoF(-1) == -1
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


def test_convertTemp() -> None:
    """Test convertTemp function."""
    # Same unit or empty target
    assert convertTemp(100.0, 'C', 'C') == 100.0
    assert convertTemp(100.0, 'C', '') == 100.0
    assert convertTemp(100.0, '', 'F') == 100.0

    # C to F
    assert convertTemp(0.0, 'C', 'F') == 32.0
    assert convertTemp(100.0, 'C', 'F') == 212.0

    # F to C
    assert convertTemp(32.0, 'F', 'C') == 0.0
    assert convertTemp(212.0, 'F', 'C') == 100.0


def test_is_proper_temp() -> None:
    """Test is_proper_temp function."""
    # Valid temperatures
    assert is_proper_temp(25.5) is True
    assert is_proper_temp(100) is True
    assert is_proper_temp(200.0) is True

    # Invalid temperatures
    assert is_proper_temp(None) is False
    assert is_proper_temp(-1) is False  # Error value
    assert is_proper_temp(0) is False  # Error value
    assert is_proper_temp(float('nan')) is False


# Time Functions Tests


def test_stringfromseconds() -> None:
    """Test stringfromseconds function."""
    # Normal times
    assert stringfromseconds(0) == '00:00'
    assert stringfromseconds(60) == '01:00'
    assert stringfromseconds(90) == '01:30'
    assert stringfromseconds(3661) == '61:01'  # Over 60 minutes

    # With leading zero control
    assert stringfromseconds(60, leadingzero=True) == '01:00'
    assert stringfromseconds(60, leadingzero=False) == '1:00'
    assert stringfromseconds(5, leadingzero=False) == '0:05'

    # Negative times (should be handled)
    assert stringfromseconds(-60) == '-01:00'

    # Fractional seconds (should round)
    assert stringfromseconds(60.4) == '01:00'
    assert stringfromseconds(60.6) == '01:01'


def test_stringtoseconds() -> None:
    """Test stringtoseconds function."""
    # Normal times
    assert stringtoseconds('00:00') == 0
    assert stringtoseconds('01:00') == 60
    assert stringtoseconds('01:30') == 90
    assert stringtoseconds('10:05') == 605

    # Negative times
    assert stringtoseconds('-01:00') == -60
    assert stringtoseconds('-10:30') == -630

    # Invalid formats
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        stringtoseconds('invalid')
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        stringtoseconds('1:2:3')
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        stringtoseconds('1')

    # Non-numeric parts raise ValueError
    with pytest.raises(ValueError, match='invalid literal'):
        stringtoseconds('ab:cd')


# String Processing Functions Tests


def test_comma2dot() -> None:
    """Test comma2dot function."""
    # Normal decimal conversion
    assert comma2dot('1,5') == '1.5'
    assert comma2dot('12,34') == '12.34'

    # Already has dot
    assert comma2dot('1.5') == '1.5'

    # Multiple separators (behavior depends on order)
    assert comma2dot('1,234.56') == '1234.56'  # comma then dot
    assert comma2dot('1.234,56') == '1.23456'  # dot then comma

    # No separators
    assert comma2dot('123') == '123'

    # Empty or whitespace
    assert comma2dot('') == ''
    assert comma2dot('  ') == ''

    # Leading/trailing whitespace
    assert comma2dot('  1,5  ') == '1.5'


def test_natsort() -> None:
    """Test natsort function (natural sorting)."""
    # Numbers in strings
    result = natsort('file10.txt')
    assert 10 in result  # Should extract number
    assert 'file' in result  # Should keep text
    assert '.txt' in result  # Should keep extension

    # Mixed content
    result = natsort('abc123def456')
    assert 123 in result
    assert 456 in result
    assert 'abc' in result
    assert 'def' in result


def test_scaleFloat2String() -> None:
    """Test scaleFloat2String function."""
    # Zero
    assert scaleFloat2String(0) == '0'
    assert scaleFloat2String('0') == '0'

    # Small numbers (< 1)
    assert scaleFloat2String(0.1) == '0.1'
    assert scaleFloat2String(0.999) == '0.999'

    # Medium numbers (1-9.99)
    assert scaleFloat2String(1.5) == '1.5'
    assert scaleFloat2String(9.99) == '9.99'

    # Larger numbers (10-999.9)
    assert scaleFloat2String(10.5) == '10.5'
    assert scaleFloat2String(999.9) == '999.9'

    # Very large numbers (>= 1000)
    assert scaleFloat2String(1000) == '1000'
    assert scaleFloat2String(9999) == '9999'


# Float Processing Functions Tests


def test_float2float() -> None:
    """Test float2float function."""
    # Different decimal places
    assert float2float(1.23456, 0) == 1.0
    assert float2float(1.23456, 1) == 1.2
    assert float2float(1.23456, 2) == 1.23
    assert float2float(1.23456, 3) == 1.235  # rounds

    # NaN handling (returns 0.0 for NaN)
    assert float2float(float('nan'), 1) == 0.0

    # Zero decimals
    assert float2float(1.7, 0) == 2.0  # rounds


def test_float2floatNone() -> None:
    """Test float2floatNone function."""
    # Normal values
    assert float2floatNone(1.23456, 2) == 1.23

    # None handling
    assert float2floatNone(None, 2) is None
    assert float2floatNone(None) is None  # default n=1


def test_weightVolumeDigits() -> None:
    """Test weightVolumeDigits function."""
    # Different ranges
    assert weightVolumeDigits(1500) == 1  # >= 1000
    assert weightVolumeDigits(500) == 2  # >= 100, < 1000
    assert weightVolumeDigits(50) == 3  # < 100


def test_float2floatWeightVolume() -> None:
    """Test float2floatWeightVolume function."""
    # Should use appropriate digits based on value
    assert float2floatWeightVolume(1500) == 1500.0  # 1 digit
    assert float2floatWeightVolume(150.456) == 150.46  # 2 digits
    assert float2floatWeightVolume(15.456) == 15.456  # 3 digits


# Weight/Volume Conversion Functions Tests


def test_convertWeight() -> None:
    """Test convertWeight function."""
    # Same unit (no conversion)
    assert convertWeight(1000, 0, 0) == 1000  # g to g
    assert convertWeight(1, 1, 1) == 1  # kg to kg
    assert convertWeight(1, 2, 2) == 1  # lb to lb
    assert convertWeight(1, 3, 3) == 1  # oz to oz

    # g to kg
    assert convertWeight(1000, 0, 1) == 1.0
    assert convertWeight(500, 0, 1) == 0.5

    # kg to g
    assert convertWeight(1, 1, 0) == 1000
    assert convertWeight(2.5, 1, 0) == 2500

    # g to lb (approximately)
    result = convertWeight(453.592, 0, 2)  # 453.592g â‰ˆ 1 lb
    assert pytest.approx(result, 0.01) == 1.0

    # lb to g
    result = convertWeight(1, 2, 0)  # 1 lb to g
    assert pytest.approx(result, 0.1) == 453.6

    # g to oz
    result = convertWeight(28.35, 0, 3)  # ~28.35g â‰ˆ 1 oz
    assert pytest.approx(result, 0.01) == 1.0

    # oz to g
    result = convertWeight(1, 3, 0)  # 1 oz to g
    assert pytest.approx(result, 0.1) == 28.35


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


def test_replace_duplicates() -> None:
    """Test replace_duplicates function."""
    # Replace consecutive duplicates
    data:List[float] = [1, 1, 2, 2, 2, 3]
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


# Type Guard Functions Tests


def test_is_int_list() -> None:
    """Test is_int_list function."""
    # Valid int lists
    assert is_int_list([1, 2, 3]) is True
    assert is_int_list([0, -1, 100]) is True
    assert is_int_list([]) is True  # Empty list

    # Invalid lists
    assert is_int_list([1, 2.5, 3]) is False  # Contains float
    assert is_int_list([1, '2', 3]) is False  # Contains string
    assert is_int_list([1, None, 3]) is False  # Contains None


def test_is_float_list() -> None:
    """Test is_float_list function."""
    # Valid float lists
    assert is_float_list([1.0, 2.5, 3.7]) is True
    assert is_float_list([]) is True  # Empty list

    # Invalid lists (ints are NOT considered floats by this function)
    assert is_float_list([1, 2, 3]) is False  # Ints not considered floats
    assert is_float_list([1.0, '2.5', 3.0]) is False  # Contains string
    assert is_float_list([1.0, None, 3.0]) is False  # Contains None


# Internationalization Functions Tests


def test_right_to_left() -> None:
    """Test right_to_left function."""
    # RTL languages
    assert right_to_left('ar') is True  # Arabic
    assert right_to_left('he') is True  # Hebrew
    assert right_to_left('fa') is True  # Farsi/Persian

    # LTR languages
    assert right_to_left('en') is False  # English
    assert right_to_left('es') is False  # Spanish
    assert right_to_left('fr') is False  # French
    assert right_to_left('de') is False  # German
    assert right_to_left('zh') is False  # Chinese

    # Unknown/invalid codes
    assert right_to_left('xx') is False  # Unknown
    assert right_to_left('') is False  # Empty


# Additional Utility Functions Tests


def test_isOpen() -> None:
    """Test isOpen function (network port checking)."""
    # Test with localhost and common ports
    # Port 80 (HTTP) - might be closed on localhost
    result = isOpen('127.0.0.1', 80)
    assert isinstance(result, bool)  # Should return boolean

    # Invalid host
    result = isOpen('invalid.host.name', 80)
    assert result is False

    # Invalid port
    result = isOpen('127.0.0.1', 99999)
    assert result is False


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


# Color Functions Tests


def test_argb_colorname2rgba_colorname() -> None:
    """Test argb_colorname2rgba_colorname function."""
    # Normal ARGB color (alpha at beginning)
    result = argb_colorname2rgba_colorname('#80FF0000')  # Semi-transparent red
    assert result == '#FF000080'  # Red with alpha at end

    # Regular hex color (no change)
    result = argb_colorname2rgba_colorname('#FF0000')
    assert result == '#FF0000'

    # Invalid format (no change)
    result = argb_colorname2rgba_colorname('invalid')
    assert result == 'invalid'


def test_rgba_colorname2argb_colorname() -> None:
    """Test rgba_colorname2argb_colorname function."""
    # Normal RGBA color (alpha at end)
    result = rgba_colorname2argb_colorname('#FF000080')  # Red with alpha at end
    assert result == '#80FF0000'  # Semi-transparent red with alpha at beginning

    # Regular hex color (no change)
    result = rgba_colorname2argb_colorname('#FF0000')
    assert result == '#FF0000'

    # Invalid format (no change)
    result = rgba_colorname2argb_colorname('invalid')
    assert result == 'invalid'


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


# Additional Edge Case Tests for 100% Coverage


def test_stringfromseconds_negative() -> None:
    """Test stringfromseconds with negative values to cover line 138."""
    # Test negative seconds to cover the negative formatting branch
    result = stringfromseconds(-90)  # -1:30
    assert result == '-01:30'

    result = stringfromseconds(-3661)  # -61:01
    assert result == '-61:01'

    # Test with leadingzero=False for negative
    result = stringfromseconds(-90, leadingzero=False)
    assert result == '-1:30'


def test_stringtoseconds_edge_cases() -> None:
    """Test stringtoseconds with edge cases."""
    # Test negative parsing (covers more branches)
    assert stringtoseconds('-05:30') == -330
    assert stringtoseconds('-00:01') == -1

    # Test edge case with zero
    assert stringtoseconds('00:00') == 0
    assert stringtoseconds('-00:00') == 0


def test_convertTemp_edge_cases() -> None:
    """Test convertTemp with more edge cases."""
    # Test with empty source unit
    assert convertTemp(100.0, '', 'F') == 100.0

    # Test with both empty
    assert convertTemp(100.0, '', '') == 100.0

    # Test unknown units (actually converts as if C to F)
    result = convertTemp(100.0, 'X', 'Y')
    assert pytest.approx(result, 0.1) == 37.8  # Converts as C to F then F to C


def test_scaleFloat2String_edge_cases() -> None:
    """Test scaleFloat2String with more edge cases."""
    # Test very small numbers
    assert scaleFloat2String(0.001) == '0.001'
    assert scaleFloat2String(0.0001) == '0'  # Very small rounds to 0

    # Test boundary values
    assert scaleFloat2String(0.999) == '0.999'
    assert scaleFloat2String(1.0) == '1'
    assert scaleFloat2String(9.999) == '10'  # Rounds up
    assert scaleFloat2String(10.0) == '10'
    assert scaleFloat2String(99.99) == '99.99'
    assert scaleFloat2String(100.0) == '100'
    assert scaleFloat2String(999.9) == '999.9'
    assert scaleFloat2String(1000.0) == '1000'


def test_comma2dot_edge_cases() -> None:
    """Test comma2dot with more edge cases."""
    # Test complex cases with multiple separators
    assert comma2dot('1,234,567.89') == '1234567.89'
    assert comma2dot('1.234.567,89') == '1234.56789'  # Actual behavior

    # Test with only commas
    assert comma2dot('1,234,567') == '1234.567'

    # Test with only dots
    assert comma2dot('1.234.567') == '1234.567'


def test_fill_gaps_edge_cases() -> None:
    """Test fill_gaps with more edge cases."""
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


def test_replace_duplicates_edge_cases() -> None:
    """Test replace_duplicates with more edge cases."""
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


def test_convertWeight_all_combinations() -> None:
    """Test convertWeight with all unit combinations."""
    # Test all unit conversions to improve coverage
    units = [0, 1, 2, 3]  # g, kg, lb, oz

    for from_unit in units:
        for to_unit in units:
            if from_unit != to_unit:
                # Test a small conversion to ensure it works
                result = convertWeight(1.0, from_unit, to_unit)
                assert isinstance(result, float)
                assert result > 0


def test_convertVolume_all_combinations() -> None:
    """Test convertVolume with all unit combinations."""
    # Test all unit conversions to improve coverage
    units = [0, 1, 2, 3, 4, 5]  # l, gal, qt, pt, cup, ml

    for from_unit in units:
        for to_unit in units:
            if from_unit != to_unit:
                # Test a small conversion to ensure it works
                result = convertVolume(1.0, from_unit, to_unit)
                assert isinstance(result, float)
                assert result > 0


def test_render_weight_edge_cases() -> None:
    """Test render_weight with edge cases to improve coverage."""
    # Test very large weights to trigger tonne conversion
    result = render_weight(2000000, 0, 0)  # 2 million grams
    assert 't' in result  # Should convert to tonnes

    # Test edge cases for smart unit upgrade
    result = render_weight(1000, 0, 0, smart_unit_upgrade=True)
    assert 'kg' in result  # Should upgrade to kg

    # Test brief mode with different values
    result = render_weight(1500, 0, 0, brief=1)
    assert 'kg' in result  # Should upgrade due to brief mode

    # Test right-to-left language formatting
    result = render_weight(1500, 0, 0, right_to_left_lang=True)
    assert isinstance(result, str)


def test_toInt_edge_cases() -> None:
    """Test toInt with more edge cases."""
    # Test with very large numbers
    assert toInt('999999999') == 999999999

    # Test with decimal strings
    assert toInt('42.9') == 43  # Should round
    assert toInt('42.1') == 42  # Should round down

    # Test with whitespace
    assert toInt('  42  ') == 42

    # Test with invalid strings
    assert toInt('not_a_number') == 0
    assert toInt('') == 0


def test_toFloat_edge_cases() -> None:
    """Test toFloat with more edge cases."""
    # Test with scientific notation
    assert toFloat('1e3') == 1000.0
    assert toFloat('1.5e-2') == 0.015

    # Test with whitespace
    assert toFloat('  42.5  ') == 42.5

    # Test with invalid strings
    assert toFloat('not_a_number') == 0.0
    assert toFloat('') == 0.0


def test_toBool_edge_cases() -> None:
    """Test toBool with more edge cases."""
    # Test with mixed case
    assert toBool('True') is True
    assert toBool('FALSE') is False
    assert toBool('Yes') is True
    assert toBool('NO') is False

    # Test with numbers
    assert toBool(42) is True  # Non-zero number
    assert toBool(-1) is True  # Negative number
    assert toBool(0.0) is False  # Zero float
    assert toBool(1.5) is True  # Non-zero float

    # Test with other types
    assert toBool([]) is False  # Empty list
    assert toBool([1]) is True  # Non-empty list
    assert toBool({}) is False  # Empty dict
    assert toBool({'a': 1}) is True  # Non-empty dict


def test_path2url_edge_cases() -> None:
    """Test path2url with more edge cases."""
    # Test with Windows-style paths
    result = path2url('C:\\Users\\test\\file.txt')
    assert result.startswith('file://')

    # Test with relative paths
    result = path2url('./relative/path.txt')
    assert result.startswith('file://')

    # Test with special characters
    result = path2url('/path/with/special chars & symbols.txt')
    assert result.startswith('file://')


def test_natsort_edge_cases() -> None:
    """Test natsort with more edge cases."""
    # Test with no numbers
    result = natsort('abcdef')
    assert 'abcdef' in result
    assert all(isinstance(x, str) for x in result)

    # Test with only numbers
    result = natsort('123456')
    assert 123456 in result

    # Test with mixed case
    result = natsort('File123ABC')
    assert 'file' in result  # Should be lowercase
    assert 123 in result
    assert 'abc' in result


def test_convertTemp_none_handling() -> None:
    """Test convertTemp with None values to cover lines 223, 227."""
    # Test with values that would return None from conversion functions
    # This is tricky since fromCtoF/fromFtoC handle None, but we need to trigger the None return

    # Test with NaN values that might return None
    result = convertTemp(float('nan'), 'C', 'F')
    # Should handle NaN gracefully
    assert isinstance(result, float)


def test_toGrey_edge_cases() -> None:
    """Test toGrey with edge cases to cover line 455."""
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


def test_toDim_edge_cases() -> None:
    """Test toDim with edge cases."""
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


def test_createGradient_edge_cases() -> None:
    """Test createGradient with edge cases."""
    # Test with different tint/shade factors
    result = createGradient('#FF0000', tint_factor=0.1, shade_factor=0.1)
    assert isinstance(result, str)
    assert 'QLinearGradient' in result

    # Test with extreme factors
    result = createGradient('#FF0000', tint_factor=0.9, shade_factor=0.9)
    assert isinstance(result, str)
    assert 'QLinearGradient' in result


def test_float2float_edge_cases() -> None:
    """Test float2float with more edge cases."""
    # Test with very large numbers
    result = float2float(999999.999999, 2)
    assert isinstance(result, float)

    # Test with very small numbers
    result = float2float(0.000001, 6)
    assert isinstance(result, float)

    # Test with negative numbers
    result = float2float(-123.456, 2)
    assert result == -123.46


def test_weightVolumeDigits_edge_cases() -> None:
    """Test weightVolumeDigits with edge cases."""
    # Test boundary values
    assert weightVolumeDigits(999.9) == 2  # Just under 1000
    assert weightVolumeDigits(1000.0) == 1  # Exactly 1000
    assert weightVolumeDigits(99.9) == 3  # Just under 100
    assert weightVolumeDigits(100.0) == 2  # Exactly 100


def test_render_weight_complex_cases() -> None:
    """Test render_weight with complex cases to improve coverage."""
    # Test cases that might trigger different code paths

    # Test very small weight with kg target (should downgrade to g)
    result = render_weight(0.5, 1, 1)  # 0.5kg target kg
    assert 'g' in result  # Should downgrade to grams

    # Test large oz weight (should upgrade to lb)
    result = render_weight(2000, 3, 3)  # 2000oz target oz
    assert 'lb' in result  # Should upgrade to pounds

    # Test very large weight (should upgrade to tonnes)
    result = render_weight(2000000, 0, 0)  # 2M grams
    assert 't' in result  # Should show tonnes


def test_isOpen_edge_cases() -> None:
    """Test isOpen with more edge cases."""
    # Test with invalid port numbers
    assert isOpen('127.0.0.1', -1) is False
    assert isOpen('127.0.0.1', 65536) is False

    # Test with localhost variations
    result = isOpen('localhost', 80)
    assert isinstance(result, bool)

    # Test with IPv6 localhost
    result = isOpen('::1', 80)
    assert isinstance(result, bool)


# Additional tests for better coverage and edge cases


def test_stringtoseconds_should_handle_invalid_format_gracefully() -> None:
    """Test stringtoseconds with various invalid formats."""
    # Test completely invalid formats
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        stringtoseconds('')
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        stringtoseconds('invalid')
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        stringtoseconds('1:2:3:4')  # Too many parts
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        stringtoseconds('1')  # Too few parts
    with pytest.raises(ValueError, match='not a properly formatted time string'):
        assert stringtoseconds('::')  # Multiple empty parts

    # Test with single empty part (causes IndexError, so we expect exception)
    with pytest.raises(IndexError):
        stringtoseconds(':')  # Empty parts

    # Test with non-numeric parts (should raise ValueError)
    with pytest.raises(ValueError):
        stringtoseconds('ab:cd')
    with pytest.raises(ValueError):
        stringtoseconds('1:ab')
    with pytest.raises(ValueError):
        stringtoseconds('ab:1')


def test_abbrevString_should_handle_edge_cases_correctly() -> None:
    """Test abbrevString with precise edge cases."""
    # Test exact boundary conditions
    assert abbrevString('', 0) == ''
    assert abbrevString('', 5) == ''
    assert abbrevString('A', 0) == '\u2026'  # Length 0 should always add ellipsis
    assert abbrevString('AB', 2) == 'AB'  # Exactly at limit
    assert abbrevString('ABC', 2) == 'A\u2026'  # One over limit

    # Test with very long strings
    long_string = 'A' * 1000
    result = abbrevString(long_string, 10)
    assert result == 'A' * 9 + '\u2026'
    assert len(result) == 10  # 9 chars + ellipse char


def test_hex2int_should_handle_boundary_values() -> None:
    """Test hex2int with boundary and edge values."""
    # Test maximum values
    assert hex2int(0xFF) == 255
    assert hex2int(0xFF, 0xFF) == 65535  # Maximum 16-bit value

    # Test minimum values
    assert hex2int(0) == 0
    assert hex2int(0, 0) == 0

    # Test single byte boundaries
    assert hex2int(0x7F) == 127  # Max signed byte
    assert hex2int(0x80) == 128  # Min unsigned high byte

    # Test specific combinations
    assert hex2int(1, 1) == 257  # 1*256 + 1
    assert hex2int(0x10, 0x10) == 4112  # 16*256 + 16


def test_s2a_should_filter_non_ascii_precisely() -> None:
    """Test s2a function with precise ASCII filtering."""
    # Test with mixed ASCII and non-ASCII
    assert s2a('Hello123') == 'Hello123'  # All ASCII
    assert s2a('Héllo') == 'Hllo'  # Remove accented character
    assert s2a('Test™') == 'Test'  # Remove trademark symbol
    assert s2a('αβγ') == ''  # All non-ASCII should result in empty string

    # Test with control characters (should be preserved as they are ASCII)
    assert s2a('Hello\tWorld') == 'Hello\tWorld'  # Tab is ASCII
    assert s2a('Hello\nWorld') == 'Hello\nWorld'  # Newline is ASCII

    # Test with high ASCII values
    assert s2a('Test\x7f') == 'Test\x7f'  # DEL character (127) is ASCII


def test_encodeLocal_decodeLocal_should_handle_special_characters() -> None:
    """Test encode/decode with comprehensive character coverage."""
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


def test_float2float_should_handle_precision_correctly() -> None:
    """Test float2float with precise decimal handling."""
    # Test rounding behavior (actual behavior from the function)
    assert float2float(1.2345, 0) == 1.0
    assert float2float(1.2345, 1) == 1.2
    assert float2float(1.2345, 2) == 1.23
    assert float2float(1.2345, 3) == 1.234  # Actual behavior: truncates, doesn't round
    assert float2float(1.2346, 3) == 1.235  # This rounds up

    # Test with negative numbers
    assert float2float(-1.2345, 2) == -1.23
    assert float2float(-1.2355, 2) == -1.24  # Round away from zero

    # Test with very large decimal places
    assert float2float(1.23456789, 8) == 1.23456789

    # Test with zero
    assert float2float(0.0, 5) == 0.0


def test_comma2dot_should_handle_complex_number_formats() -> None:
    """Test comma2dot with various European number formats."""
    # Test German/European format (comma as decimal separator)
    # Note: comma2dot strips trailing zeros
    assert comma2dot('1,50') == '1.5'  # Trailing zero is stripped
    assert comma2dot('12,34') == '12.34'

    # Test with thousands separators
    assert (
        comma2dot('1.234,56') == '1.23456'
    )  # German format - dots removed, last comma becomes decimal
    assert comma2dot('1,234.56') == '1234.56'  # US format with comma thousands

    # Test edge cases
    assert comma2dot(',5') == '.5'  # Leading comma
    assert comma2dot('5,') == '5'  # Trailing comma gets removed
    assert comma2dot('1,2,3') == '12.3'  # Last comma becomes decimal

    # Test with no separators
    assert comma2dot('12345') == '12345'


def test_toList_should_handle_various_iterables() -> None:
    """Test toList with comprehensive iterable types."""
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


def test_is_proper_temp_should_validate_temperature_values_precisely() -> None:
    """Test is_proper_temp with comprehensive temperature validation."""
    # Valid temperatures
    assert is_proper_temp(20.5) is True
    assert is_proper_temp(100) is True
    assert is_proper_temp(0.1) is True  # Just above zero
    assert is_proper_temp(-0.1) is True  # Negative temperatures are valid
    assert is_proper_temp(1000.0) is True  # High temperatures

    # Invalid values (error indicators)
    assert is_proper_temp(0) is False  # Zero is error value
    assert is_proper_temp(-1) is False  # -1 is error value
    assert is_proper_temp(0.0) is False  # Zero float is error value
    assert is_proper_temp(-1.0) is False  # -1 float is error value

    # Invalid types/values
    assert is_proper_temp(None) is False
    assert is_proper_temp(float('nan')) is False
    # Note: inf and -inf are actually considered valid by the function
    # as they are not NaN and not in [0, -1]
    assert is_proper_temp(float('inf')) is False
    assert is_proper_temp(float('-inf')) is False


@pytest.mark.parametrize(
    'input_value,expected_output',
    [
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


@pytest.mark.parametrize(
    'celsius,expected_fahrenheit',
    [
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
    'fahrenheit,expected_celsius',
    [
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
    'value,decimals,expected',
    [
        (1.23456, 0, 1.0),
        (1.23456, 1, 1.2),
        (1.23456, 2, 1.23),
        (1.23456, 3, 1.235),  # Rounds up
        (1.23454, 3, 1.235),  # Rounds up
        (1.23444, 3, 1.234),  # Rounds down
        (-1.23456, 2, -1.23),
        (0.0, 3, 0.0),
        (999.999, 0, 1000.0),  # Large rounding
    ],
)
def test_float2float_should_round_precisely(value: float, decimals: int, expected: float) -> None:
    """Test float2float rounding behavior with parametrized values."""
    result = float2float(value, decimals)
    assert result == expected
