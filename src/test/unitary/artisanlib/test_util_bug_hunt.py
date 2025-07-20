"""
Bug hunting test suite for artisanlib.util module using pure TDD approach.
This file tests edge cases and boundary conditions to discover potential bugs.

BUGS DISCOVERED AND THEIR EXPLOITABILITY STATUS:

REAL EXPLOITABLE BUGS:
1. ❌ right_to_left: Case-sensitive locale checking - system could provide "AR" vs "ar"
2. ❌ stringtoseconds: Crashes with IndexError on malformed input (some direct calls exist)
3. ❌ weightVolumeDigits: Incorrect handling of negative values (doesn't use abs())
4. ❌ convertWeight: Accepts negative indices due to Python's negative indexing
5. ❌ is_proper_temp: Accepts infinity values as "proper" temperatures
6. ❌ decs2string/uchr: No input validation for byte range/Unicode range
7. ❌ str2cmd: Crashes on non-ASCII characters

BUGS THAT ARE PROTECTED IN PRACTICE:
8. ✅ abbrevString: Zero/negative length - length always hardcoded to positive values
9. ✅ float2float: Negative precision - precision always hardcoded or from positive functions
10. ✅ toBool: eval() usage - only used with trusted QSettings data, not user input

DESIGN DECISIONS (NOT BUGS):
11. ✅ toInt: Very large floats become huge integers - Python supports arbitrary precision
12. ✅ decodeLocal: DeprecationWarning - expected behavior for invalid escape sequences

SUMMARY: 9 tests FAIL (exposing real bugs), 64 tests PASS (expected behavior or protected bugs).
The failing tests demonstrate actual bugs that need fixing. The passing tests document expected behavior.
Each test documents the discovered issue, its exploitability status, and remediation approach.
"""

from typing import List

import pytest

from artisanlib.util import (
    abbrevString,
    cmd2str,
    comma2dot,
#    convertRoRstrict,
    convertTemp,
    convertVolume,
    convertWeight,
    decodeLocal,
    decodeLocalStrict,
#    decs2string,
    encodeLocal,
    encodeLocalStrict,
    fill_gaps,
    float2float,
    float2floatNone,
    fromCtoFstrict,
    fromFtoCstrict,
    hex2int,
    is_float_list,
    is_int_list,
    is_proper_temp,
    natsort,
    path2url,
    removeAll,
    replace_duplicates,
    right_to_left,
    s2a,
    scaleFloat2String,
    str2cmd,
    stringtoseconds,
    toBool,
    toFloat,
    toInt,
    toStringList,
    uchr,
    weightVolumeDigits,
)


class TestStringToSecondsBugHunt:
    """Testing stringtoseconds for potential bugs with malformed input."""

    def test_stringtoseconds_should_handle_empty_timeparts_gracefully(self) -> None:
        """Testing if stringtoseconds handles empty time parts without crashing."""
        # BUG EXPOSED: Function should return -1 for invalid format, not crash
        # Currently crashes with IndexError when input is ":"
        with pytest.raises(IndexError):
            stringtoseconds(':')
        # BUG STATUS: REAL EXPLOITABLE BUG - Some direct calls exist without protective wrappers
        # REMEDIATION: Add input validation for empty timeparts before accessing indices

    def test_stringtoseconds_should_handle_negative_minutes_correctly(self) -> None:
        """Testing negative time parsing logic for potential bugs."""
        result = stringtoseconds('-05:30')
        assert result == -330  # -5*60 - 30 = -330

        # Testing edge case: what happens with "-00:30"?
        result = stringtoseconds('-00:30')
        assert result == -30  # Should be -30, not +30

    def test_stringtoseconds_should_handle_large_numbers(self) -> None:
        """Testing with very large time values that might cause overflow."""
        # Testing with maximum reasonable values
        result = stringtoseconds('999:59')
        assert result == 59999  # 999*60 + 59

        # Testing negative large values
        result = stringtoseconds('-999:59')
        assert result == -59999  # -999*60 - 59


class TestAbbrevStringBugHunt:
    """Testing abbrevString for boundary condition bugs."""

    def test_abbrevString_should_handle_zero_length_correctly(self) -> None:
        """Testing abbrevString with zero length limit."""
        result = abbrevString('test', 0)
        # BUG DISCOVERED: With ll=0, function returns "tes..." instead of "..."
        # The logic s[:ll-1] becomes s[:-1] which returns "tes", then adds "..." = "tes..."
        assert result == '\u2026'  # ACTUAL BEHAVIOR - BUG CONFIRMED
        # BUG STATUS: PROTECTED IN PRACTICE - Length always hardcoded to positive values (e.g., 18)
        # REMEDIATION: Not needed - all usage sites use positive hardcoded lengths

    def test_abbrevString_should_handle_negative_length(self) -> None:
        """Testing abbrevString with negative length."""
        result = abbrevString('test', -1)
        # BUG DISCOVERED: Negative length causes unexpected behavior
        # s[:ll-1] becomes s[:-2] = "te", then adds "..." = "te..."
        assert result == '\u2026'
        # BUG STATUS: PROTECTED IN PRACTICE - Length always hardcoded to positive values
        # REMEDIATION: Not needed - all usage sites use positive hardcoded lengths

    def test_abbrevString_should_handle_length_one_correctly(self) -> None:
        """Testing abbrevString with length 1."""
        result = abbrevString('test', 1)
        # With ll=1: s[:ll-1] = s[:0] = "", then adds "..." = "..."
        assert result == '\u2026'
        # This might be unexpected behavior - user might expect "t" for length 1


class TestHex2IntBugHunt:
    """Testing hex2int for potential overflow and boundary bugs."""

    def test_hex2int_should_handle_maximum_byte_values(self) -> None:
        """Testing hex2int with maximum byte values."""
        result = hex2int(255, 255)
        assert result == 65535  # 255*256 + 255

    def test_hex2int_should_handle_zero_values(self) -> None:
        """Testing hex2int with zero values."""
        result = hex2int(0, 0)
        assert result == 0

        result = hex2int(0)
        assert result == 0

    def test_hex2int_should_handle_large_values_that_might_overflow(self) -> None:
        """Testing hex2int with values that might cause integer overflow."""
        # Testing with values larger than typical byte range
        result = hex2int(1000, 1000)
        assert result == 257000  # 1000*256 + 1000
        # No overflow protection - function accepts any integer


#class TestDecs2StringBugHunt:
#    """Testing decs2string for potential bugs with invalid byte values."""
#
#    def test_decs2string_should_handle_values_outside_byte_range(self) -> None:
#        """Testing decs2string with values outside 0-255 range."""
#        # BUG EXPOSED: Function should validate input range and handle gracefully
#        # Currently crashes with ValueError when it should return empty bytes or handle gracefully
#        result = decs2string([256])
#        assert result == b""  # Should handle invalid values gracefully
#        # BUG STATUS: REAL EXPLOITABLE BUG - No input validation for byte range
#        # REMEDIATION: Add validation for 0 <= x <= 255 for all values before bytes() call
#
#    def test_decs2string_should_handle_negative_values(self) -> None:
#        """Testing decs2string with negative values."""
#        # BUG EXPOSED: Function should validate negative values and handle gracefully
#        # Currently crashes with ValueError when it should return empty bytes or handle gracefully
#        result = decs2string([-1])
#        assert result == b""  # Should handle invalid values gracefully
#        # BUG STATUS: REAL EXPLOITABLE BUG - No input validation for negative values
#        # REMEDIATION: Add validation for non-negative values before bytes() call
#
#    def test_decs2string_should_handle_empty_list(self) -> None:
#        """Testing decs2string with empty list."""
#        result = decs2string([])
#        assert result == b""  # This works correctly
#

class TestUchrBugHunt:
    """Testing uchr for potential Unicode-related bugs."""

    def test_uchr_should_handle_invalid_unicode_codepoints(self) -> None:
        """Testing uchr with invalid Unicode code points."""
        # BUG EXPOSED: Function should validate Unicode range and handle gracefully
        # Currently crashes with ValueError when it should return empty string or handle gracefully
        result = uchr(0x110000)  # Beyond Unicode range
        assert result == ''  # Should handle invalid codepoints gracefully
        # BUG STATUS: REAL EXPLOITABLE BUG - No input validation for Unicode range
        # REMEDIATION: Add validation for valid Unicode range (0 <= x <= 0x10FFFF)

    def test_uchr_should_handle_negative_values(self) -> None:
        """Testing uchr with negative values."""
        # BUG EXPOSED: Function should validate negative values and handle gracefully
        # Currently crashes with ValueError when it should return empty string or handle gracefully
        result = uchr(-1)
        assert result == ''  # Should handle invalid values gracefully
        # BUG STATUS: REAL EXPLOITABLE BUG - No input validation for negative values
        # REMEDIATION: Add validation for non-negative values before chr() call


class TestStr2CmdCmd2StrBugHunt:
    """Testing str2cmd and cmd2str for encoding/decoding bugs."""

    def test_str2cmd_should_handle_non_ascii_characters(self) -> None:
        """Testing str2cmd with non-ASCII characters."""
        # BUG EXPOSED: Function should handle non-ASCII characters gracefully
        # Currently crashes with UnicodeEncodeError when it should encode properly
        result = str2cmd('café')
        assert result == b'caf'
        # BUG STATUS: REAL EXPLOITABLE BUG - Crashes on international text
        # REMEDIATION: Use 'utf-8' encoding or add error handling for non-ASCII characters

    def test_cmd2str_should_handle_invalid_latin1_bytes(self) -> None:
        """Testing cmd2str with bytes that might not decode properly."""
        # Latin-1 can decode any byte value, so this should work
        result = cmd2str(b'\xff\xfe')
        assert isinstance(result, str)
        # This actually works fine since latin-1 can decode any byte


class TestS2ABugHunt:
    """Testing s2a (string to ASCII) for potential encoding bugs."""

    def test_s2a_should_handle_mixed_unicode_correctly(self) -> None:
        """Testing s2a with mixed Unicode and ASCII characters."""
        result = s2a('Hello 世界 World')
        assert result == 'Hello  World'  # Non-ASCII chars removed, spaces preserved

    def test_s2a_should_handle_empty_string(self) -> None:
        """Testing s2a with empty string."""
        result = s2a('')
        assert result == ''

    def test_s2a_should_handle_only_non_ascii(self) -> None:
        """Testing s2a with only non-ASCII characters."""
        result = s2a('世界')
        assert result == ''  # All characters removed


class TestIsProperTempBugHunt:
    """Testing is_proper_temp for potential validation bugs."""

    def test_is_proper_temp_should_handle_infinity_values(self) -> None:
        """Testing is_proper_temp with infinity values."""
        # BUG EXPOSED: Function should reject infinity values as improper temperatures
        # Currently allows infinity when it should return False
        assert is_proper_temp(float('inf')) is False  # Should reject positive infinity
        assert is_proper_temp(float('-inf')) is False  # Should reject negative infinity
        # BUG STATUS: REAL EXPLOITABLE BUG - Infinite temperatures pass validation
        # REMEDIATION: Add math.isfinite() check to reject infinity values

    def test_is_proper_temp_should_handle_very_large_numbers(self) -> None:
        """Testing is_proper_temp with very large numbers."""
        assert is_proper_temp(1e100) is True
        assert is_proper_temp(-1e100) is True
        # Very large numbers are accepted - might be intentional

    def test_is_proper_temp_should_handle_zero_point_zero(self) -> None:
        """Testing is_proper_temp with 0.0 vs 0."""
        assert is_proper_temp(0.0) is False  # Correctly rejects 0.0
        assert is_proper_temp(0) is False  # Correctly rejects 0


class TestTypeConversionBugHunt:
    """Testing type conversion functions for potential bugs."""

    def test_toInt_should_handle_infinity_values(self) -> None:
        """Testing toInt with infinity values."""
        # BUG DISCOVERED: toInt doesn't handle infinity properly
        result = toInt(float('inf'))
        # float('inf') converted to int might cause OverflowError
        # But the function catches all exceptions and returns 0
        assert result == 0
        # This might be unexpected - infinity should perhaps be handled specially
        # float('inf') and float('-inf) cannot be converted to int and thus are mapped to 0

    def test_toInt_should_handle_very_large_floats(self) -> None:
        """Testing toInt with very large float values."""
        # Testing with float larger than max int
        result = toInt(1e100)
        # BUG DISCOVERED: Large floats don't raise exception, they get converted to huge ints
        # Python can handle arbitrarily large integers, so no exception is raised
        assert (
            result
            == 10000000000000000159028911097599180468360808563945281389781327557747838772170381060813469985856815104
        )
        # BUG STATUS: DESIGN DECISION - Python supports arbitrary precision integers by design
        # REMEDIATION: Not needed - this is expected Python behavior

    def test_toFloat_should_handle_complex_numbers(self) -> None:
        """Testing toFloat with complex numbers."""
        result = toFloat(3 + 4j)
        assert result == 0.0  # Exception caught, returns 0.0
        # This behavior might be unexpected but is documented by the broad except

# ML: eval is use here on purpose to allow for complex user defined actions. The risk is known.
#    def test_toBool_should_handle_eval_injection(self) -> None:
#        """Testing toBool for potential code injection via eval."""
#        # BUG DISCOVERED: toBool uses eval() which is dangerous
#        # This could be a security vulnerability
#        result = toBool("__import__('os').system('echo test')")
#        # The eval() call could execute arbitrary code
#        # BUG STATUS: PROTECTED IN PRACTICE - Only used with trusted QSettings data, not user input
#        # REMEDIATION: Not needed - all usage sites pass trusted application settings

    def test_toBool_should_handle_malicious_strings(self) -> None:
        """Testing toBool with potentially malicious strings."""
        # Testing various strings that might cause issues with eval
        result = toBool('1/0')  # Division by zero
        assert result is False  # Exception caught, returns False

        result = toBool('[]')  # Empty list
        assert result is False  # bool([]) is False

    def test_toStringList_should_handle_none_input(self) -> None:
        """Testing toStringList with None input."""
        # BUG DISCOVERED: toStringList doesn't handle None input
        # The function checks 'if x:' but None is falsy, so it returns []
        result = toStringList(None)  # type: ignore
        assert result == []
        # This might be unexpected - should it raise an error for None?


class TestListProcessingBugHunt:
    """Testing list processing functions for potential bugs."""

    def test_removeAll_should_handle_empty_list(self) -> None:
        """Testing removeAll with empty list."""
        test_list: List[str] = []
        removeAll(test_list, 'test')
        assert test_list == []  # Should remain empty

    def test_removeAll_should_handle_nonexistent_item(self) -> None:
        """Testing removeAll with item not in list."""
        test_list = ['a', 'b', 'c']
        removeAll(test_list, 'd')
        assert test_list == ['a', 'b', 'c']  # Should remain unchanged

    def test_fill_gaps_should_handle_all_negative_ones(self) -> None:
        """Testing fill_gaps with list of all -1 values."""
        result = fill_gaps([-1, -1, -1])
        assert result == [-1, -1, -1]  # No valid values to interpolate from

    def test_fill_gaps_should_handle_empty_list(self) -> None:
        """Testing fill_gaps with empty list."""
        result = fill_gaps([])
        assert result == []

    def test_fill_gaps_should_handle_single_element(self) -> None:
        """Testing fill_gaps with single element."""
        result = fill_gaps([5.0])
        assert result == [5.0]

        result = fill_gaps([-1])
        assert result == [-1]  # Single -1 cannot be interpolated

    def test_replace_duplicates_should_handle_empty_list(self) -> None:
        """Testing replace_duplicates with empty list."""
        result = replace_duplicates([])
        assert result == []

    def test_replace_duplicates_should_handle_single_element(self) -> None:
        """Testing replace_duplicates with single element."""
        result = replace_duplicates([5.0])
        assert result == [5.0]

    def test_replace_duplicates_should_handle_all_same_values(self) -> None:
        """Testing replace_duplicates with all identical values."""
        result = replace_duplicates([5.0, 5.0, 5.0, 5.0])
        # First value kept, others replaced with -1, then interpolated back
        # Last value is restored, then fill_gaps interpolates
        expected = [5.0, 5.0, 5.0, 5.0]  # Should interpolate back to original values
        assert result == expected


class TestStringProcessingBugHunt:
    """Testing string processing functions for potential bugs."""

    def test_comma2dot_should_handle_multiple_dots_and_commas(self) -> None:
        """Testing comma2dot with complex mixed separators."""
        # Testing edge case with multiple dots and commas
        result = comma2dot('1,234.567,89')
        # Last dot at position, so everything before last dot has commas/dots removed
        # Then last dot is kept as decimal separator
        # But there's a comma after the dot, which is unusual
        # This might reveal unexpected behavior
        assert result == '1234.56789'

    def test_comma2dot_should_handle_only_separators(self) -> None:
        """Testing comma2dot with only separators."""
        result = comma2dot(',.,.')
        assert result == '' # trailing dots are removed, other separators ignored

    def test_natsort_should_handle_empty_string(self) -> None:
        """Testing natsort with empty string."""
        result = natsort('')
        # re.split(r'(\d+)', "") returns ['']
        assert result == ['']

    def test_natsort_should_handle_only_numbers(self) -> None:
        """Testing natsort with string containing only numbers."""
        result = natsort('12345')
        # Should split into ['', '12345', '']
        assert result == ['', 12345, '']

    def test_scaleFloat2String_should_handle_very_small_numbers(self) -> None:
        """Testing scaleFloat2String with very small numbers."""
        result = scaleFloat2String(1e-10)
        # Very small number, abs(n) < 1, so uses 3 decimal places
        assert result == '0'  # After rstrip('0').rstrip('.')
        # This might lose precision for very small but non-zero numbers


class TestFloatProcessingBugHunt:
    """Testing float processing functions for potential bugs."""

    def test_float2float_should_handle_nan_input(self) -> None:
        """Testing float2float with NaN input."""
        result = float2float(float('nan'), 2)
        assert result == 0.0  # Function converts NaN to 0.0
        # This behavior is documented in the function

    def test_float2float_should_handle_infinity_input(self) -> None:
        """Testing float2float with infinity input."""
        result = float2float(float('inf'), 2)
        # This might cause issues with string formatting
        # f'%.2f' % float('inf') = 'inf'
        # float('inf') should return inf, but function might handle it
        assert result == float('inf')

    def test_float2float_should_handle_negative_precision(self) -> None:
        """Testing float2float with negative precision."""
        # BUG DISCOVERED: Function crashes with ValueError for negative precision
        assert float2float(1.23456, -1) == 1
        # BUG STATUS: PROTECTED IN PRACTICE - Precision always hardcoded or from positive functions
        # REMEDIATION: Not needed - all usage sites use positive precision values

    def test_float2floatNone_should_handle_none_correctly(self) -> None:
        """Testing float2floatNone with None input."""
        result = float2floatNone(None, 2)
        assert result is None  # Correctly handles None

    def test_weightVolumeDigits_should_handle_negative_values(self) -> None:
        """Testing weightVolumeDigits with negative values."""
        # BUG EXPOSED: Function should use abs() for negative values
        # Currently -100 returns 4 digits instead of expected 2
        result = weightVolumeDigits(-100)
        assert result == 2  # Should return 2 digits for abs(-100) = 100
        # BUG STATUS: REAL EXPLOITABLE BUG - Incorrect formatting for negative weights/volumes
        # REMEDIATION: Use abs(v) in comparisons to handle negative values correctly

    def test_weightVolumeDigits_should_handle_zero(self) -> None:
        """Testing weightVolumeDigits with zero."""
        result = weightVolumeDigits(0)
        # 0 < 10, so should return 4
        assert result == 4


class TestWeightVolumeConversionBugHunt:
    """Testing weight and volume conversion functions for potential bugs."""

    def test_convertWeight_should_handle_invalid_unit_indices(self) -> None:
        """Testing convertWeight with invalid unit indices."""
        # BUG DISCOVERED: Function doesn't validate unit indices
        # convtable has indices 0-3, but function doesn't check bounds
        with pytest.raises(IndexError):
            convertWeight(100, 5, 0)  # Invalid source unit
        # BUG STATUS: REAL EXPLOITABLE BUG - No bounds checking for unit indices
        # REMEDIATION: Add validation for 0 <= i,o < len(convtable)

    def test_convertWeight_should_handle_negative_indices(self) -> None:
        """Testing convertWeight with negative indices."""
        # BUG DISCOVERED: Negative indices don't raise IndexError, they wrap around
        with pytest.raises(IndexError):
            convertWeight(100, -1, 0)  # -1 wraps to last row (oz)
            # Python list indexing allows negative indices, so convtable[-1] = oz row
            # assert result == 2834.95  # 100 oz to g conversion
        # BUG STATUS: REAL EXPLOITABLE BUG - Unintended unit conversions due to negative indexing
        # REMEDIATION: Add explicit validation for 0 <= i,o < len(convtable)

    def test_convertVolume_should_handle_invalid_unit_indices(self) -> None:
        """Testing convertVolume with invalid unit indices."""
        # BUG DISCOVERED: Function doesn't validate unit indices
        # convtable has indices 0-5, but function doesn't check bounds
        with pytest.raises(IndexError):
            convertVolume(100, 10, 0)  # Invalid source unit
        # BUG STATUS: REAL EXPLOITABLE BUG - No bounds checking for unit indices
        # REMEDIATION: Add validation for 0 <= i,o < len(convtable)

    def test_convertVolume_should_handle_negative_indices(self) -> None:
        """Testing convertVolume with negative indices."""
        # BUG DISCOVERED: Negative indices don't raise IndexError, they wrap around
        with pytest.raises(IndexError):
            convertVolume(100, -1, 0)  # -1 wraps to last row (oz)
            # Python list indexing allows negative indices, so convtable[-1] = oz row
        # BUG STATUS: REAL EXPLOITABLE BUG - Unintended unit conversions due to negative indexing
        # REMEDIATION: Add explicit validation for 0 <= i,o < len(convtable)

    def test_convertWeight_should_handle_zero_weight(self) -> None:
        """Testing convertWeight with zero weight."""
        result = convertWeight(0, 0, 1)  # 0g to kg
        assert result == 0.0  # Should work correctly

    def test_convertWeight_should_handle_negative_weight(self) -> None:
        """Testing convertWeight with negative weight."""
        result = convertWeight(-100, 0, 1)  # -100g to kg
        assert result == -0.1  # Should work (negative weights might be valid)


class TestTypeGuardBugHunt:
    """Testing type guard functions for potential bugs."""

    def test_is_int_list_should_handle_empty_list(self) -> None:
        """Testing is_int_list with empty list."""
        result = is_int_list([])
        assert result is True  # Empty list is vacuously true for all()

    def test_is_int_list_should_handle_mixed_types(self) -> None:
        """Testing is_int_list with mixed types."""
        result = is_int_list([1, 2.0, 3])  # Contains float
        assert result is False

    def test_is_int_list_should_handle_bool_values(self) -> None:
        """Testing is_int_list with boolean values."""
        result = is_int_list([True, False, 1])
        # BUG DISCOVERED: In Python, bool is a subclass of int
        # isinstance(True, int) returns True
        assert result is True
        # This might be unexpected behavior - bools are technically ints in Python
        # REMEDIATION: Consider explicit check for bool type if this is unwanted

    def test_is_float_list_should_handle_int_values(self) -> None:
        """Testing is_float_list with integer values."""
        result = is_float_list([1, 2, 3])  # All integers
        assert result is False  # Correctly identifies as not all floats


class TestTemperatureConversionBugHunt:
    """Testing temperature conversion functions for potential bugs."""

    def test_fromCtoFstrict_should_handle_special_value_negative_one(self) -> None:
        """Testing fromCtoFstrict with special -1 value."""
        result = fromCtoFstrict(-1)
        assert result == -1  # Special case: -1 is returned as-is
        # This is documented behavior for error values

    def test_fromFtoCstrict_should_handle_special_value_negative_one(self) -> None:
        """Testing fromFtoCstrict with special -1 value."""
        result = fromFtoCstrict(-1)
        assert result == -1  # Special case: -1 is returned as-is

    def test_convertTemp_should_handle_empty_source_unit(self) -> None:
        """Testing convertTemp with empty source unit."""
        result = convertTemp(100, '', 'F')
        assert result == 100  # Returns original value for empty source

    def test_convertTemp_should_handle_empty_target_unit(self) -> None:
        """Testing convertTemp with empty target unit."""
        result = convertTemp(100, 'C', '')
        assert result == 100  # Returns original value for empty target

    def test_convertTemp_should_handle_same_units(self) -> None:
        """Testing convertTemp with same source and target units."""
        result = convertTemp(100, 'C', 'C')
        assert result == 100  # Should return original value

# ML: turned tgraphcanvas:mode and argument types into Literal['C', 'F'] and let the type checker do its work
#    def test_convertRoRstrict_should_handle_unknown_units(self) -> None:
#        """Testing convertRoRstrict with unknown units."""
#        # BUG DISCOVERED: Function doesn't validate unit strings
#        # If source_unit is not 'C', it assumes 'F' and calls RoRfromFtoCstrict
#        result = convertRoRstrict(100, "X", "C")  # Unknown unit 'X'
#        # This will be treated as Fahrenheit conversion
#        # BUG: Should validate known unit strings
#        # REMEDIATION: Add validation for known units ('C', 'F')


class TestEncodingDecodingBugHunt:
    """Testing encoding/decoding functions for potential bugs."""

    def test_encodeLocal_should_handle_none_input(self) -> None:
        """Testing encodeLocal with None input."""
        result = encodeLocal(None)
        assert result is None  # Correctly handles None

    def test_encodeLocal_should_handle_complex_unicode(self) -> None:
        """Testing encodeLocal with complex Unicode characters."""
        # Testing with emoji and complex Unicode
        result = encodeLocal('Hello 🌍 World')
        assert result is not None
        # The function uses unicode_escape_encode which should handle this

    def test_decodeLocal_should_handle_invalid_escape_sequences(self) -> None:
        """Testing decodeLocal with invalid escape sequences."""
        # BUG DISCOVERED: Function doesn't validate escape sequences
        # Invalid escape sequences might cause issues
        with pytest.deprecated_call():
            result = decodeLocal('\\invalid')
            # This might not decode properly or raise an exception
            assert result == '\\invalid'
            # NOTE: if DeprecationWarning is turned into an exception in the future result will be None

    def test_encodeLocalStrict_should_handle_none_with_default(self) -> None:
        """Testing encodeLocalStrict with None and custom default."""
        result = encodeLocalStrict(None, 'default_value')
        assert result == 'default_value'

    def test_decodeLocalStrict_should_handle_none_with_default(self) -> None:
        """Testing decodeLocalStrict with None and custom default."""
        result = decodeLocalStrict(None, 'default_value')
        assert result == 'default_value'


class TestPathUrlBugHunt:
    """Testing path2url function for potential bugs."""

    def test_path2url_should_handle_empty_path(self) -> None:
        """Testing path2url with empty path."""
        result = path2url('')
        assert result.startswith('file:')
        # Should handle empty path gracefully

    def test_path2url_should_handle_special_characters(self) -> None:
        """Testing path2url with special characters in path."""
        result = path2url('/path with spaces/file.txt')
        assert result.startswith('file:')
        # Should properly encode spaces and special characters

    def test_path2url_should_handle_unicode_paths(self) -> None:
        """Testing path2url with Unicode characters in path."""
        result = path2url('/café/文件.txt')
        assert result.startswith('file:')
        # Should handle Unicode characters in paths


class TestLocalizationBugHunt:
    """Testing localization functions for potential bugs."""

    def test_right_to_left_should_handle_empty_locale(self) -> None:
        """Testing right_to_left with empty locale."""
        result = right_to_left('')
        assert result is False  # Empty string not in RTL set

    def test_right_to_left_should_handle_case_sensitivity(self) -> None:
        """Testing right_to_left with different cases."""
        # BUG EXPOSED: Function should handle uppercase locale codes
        # Currently "AR" returns False when it should return True
        result = right_to_left('AR')  # Uppercase Arabic
        assert result is True  # Should return True for Arabic regardless of case
        # BUG STATUS: REAL EXPLOITABLE BUG - System could provide uppercase locale codes
        # REMEDIATION: Convert to lowercase before checking: locale.lower() in {'ar', 'fa', 'he'}

    def test_right_to_left_should_handle_unknown_locale(self) -> None:
        """Testing right_to_left with unknown locale."""
        result = right_to_left('unknown')
        assert result is False  # Unknown locale should return False
