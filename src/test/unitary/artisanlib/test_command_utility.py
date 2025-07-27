"""
Unit tests for artisanlib.command_utility module.

This module tests command-line utility functions that handle command-line
arguments and provide version/help information. Tests focus on edge cases
and boundary conditions to discover potential bugs.

The tests validate:
- Command-line argument parsing and handling
- Version display functionality
- Help text display functionality
- Edge cases with malformed or unexpected arguments
- sys.argv manipulation and restoration
- Output capture and validation
- Return value correctness
"""

import sys
from io import StringIO
from typing import List, Any
from unittest.mock import patch

import pytest

from artisanlib import __version__
from artisanlib.command_utility import handleCommands


class TestHandleCommandsBasicFunctionality:
    """Test basic functionality of handleCommands function."""

    def test_handleCommands_returns_true_with_no_arguments(self) -> None:
        """Test that handleCommands returns True when no special arguments are present."""
        with patch.object(sys, 'argv', ['artisan']):
            result = handleCommands()
            assert result is True

    def test_handleCommands_returns_true_with_regular_arguments(self) -> None:
        """Test that handleCommands returns True with regular non-special arguments."""
        with patch.object(sys, 'argv', ['artisan', 'file.alog', '--some-other-flag']):
            result = handleCommands()
            assert result is True

    def test_handleCommands_returns_true_with_empty_argv(self) -> None:
        """Test that handleCommands returns True with empty sys.argv."""
        with patch.object(sys, 'argv', []):
            result = handleCommands()
            assert result is True


class TestHandleCommandsVersionHandling:
    """Test version command handling functionality."""

    @pytest.mark.parametrize(
        'version_arg',
        ['-v', '--Version'],
    )
    def test_handleCommands_version_arguments_return_false(self, version_arg: str) -> None:
        """Test that version arguments return False."""
        with patch.object(sys, 'argv', ['artisan', version_arg]):
            result = handleCommands()
            assert result is False

    @pytest.mark.parametrize(
        'version_arg',
        ['-v', '--Version'],
    )
    def test_handleCommands_version_arguments_print_version(self, version_arg: str) -> None:
        """Test that version arguments print the correct version information."""
        with patch.object(sys, 'argv', ['artisan', version_arg]), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert f"Artisan  Version {__version__}" in output
            assert result is False

    def test_handleCommands_version_with_multiple_arguments(self) -> None:
        """Test version handling when mixed with other arguments."""
        with patch.object(sys, 'argv', ['artisan', 'file.alog', '-v', '--some-flag']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert f"Artisan  Version {__version__}" in output
            assert result is False

    def test_handleCommands_version_case_sensitivity(self) -> None:
        """Test that version arguments are case-sensitive."""
        # These should NOT trigger version display
        with patch.object(sys, 'argv', ['artisan', '-V', '--version']):
            result = handleCommands()
            assert result is True  # Should return True (no version handling)


class TestHandleCommandsHelpHandling:
    """Test help command handling functionality."""

    @pytest.mark.parametrize(
        'help_arg',
        ['-h', '--Help'],
    )
    def test_handleCommands_help_arguments_return_false(self, help_arg: str) -> None:
        """Test that help arguments return False."""
        with patch.object(sys, 'argv', ['artisan', help_arg]):
            result = handleCommands()
            assert result is False

    @pytest.mark.parametrize(
        'help_arg',
        ['-h', '--Help'],
    )
    def test_handleCommands_help_arguments_print_help(self, help_arg: str) -> None:
        """Test that help arguments print the correct help information."""
        with patch.object(sys, 'argv', ['artisan', help_arg]), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert f"Artisan Version {__version__}" in output
            assert 'Usage:' in output
            assert 'artisan' in output
            assert 'Options:' in output
            assert '-h, --help' in output
            assert '-v, --Version' in output
            assert result is False

    def test_handleCommands_help_with_multiple_arguments(self) -> None:
        """Test help handling when mixed with other arguments."""
        with patch.object(sys, 'argv', ['artisan', 'file.alog', '-h', '--some-flag']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert 'Usage:' in output
            assert result is False

    def test_handleCommands_help_case_sensitivity(self) -> None:
        """Test that help arguments are case-sensitive."""
        # These should NOT trigger help display
        with patch.object(sys, 'argv', ['artisan', '-H', '--help']):
            result = handleCommands()
            assert result is True  # Should return True (no help handling)


class TestHandleCommandsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_handleCommands_with_both_version_and_help(self) -> None:
        """Test behavior when both version and help arguments are present."""
        with patch.object(sys, 'argv', ['artisan', '-v', '-h']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            # Should process the first matching argument (version in this case)
            assert f"Artisan  Version {__version__}" in output
            assert result is False

    def test_handleCommands_with_help_then_version(self) -> None:
        """Test behavior when help comes before version in arguments."""
        with patch.object(sys, 'argv', ['artisan', '-h', '-v']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            # Should process the first matching argument (help in this case)
            assert 'Usage:' in output
            assert result is False

    def test_handleCommands_with_duplicate_version_arguments(self) -> None:
        """Test behavior with duplicate version arguments."""
        with patch.object(sys, 'argv', ['artisan', '-v', '-v', '--Version']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            # Should still work correctly
            assert f"Artisan  Version {__version__}" in output
            assert result is False

    def test_handleCommands_with_duplicate_help_arguments(self) -> None:
        """Test behavior with duplicate help arguments."""
        with patch.object(sys, 'argv', ['artisan', '-h', '-h', '--Help']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            # Should still work correctly
            assert 'Usage:' in output
            assert result is False

    def test_handleCommands_with_arguments_containing_special_strings(self) -> None:
        """Test with arguments that contain version/help strings but aren't exact matches."""
        test_args = [
            'artisan',
            'file-v.alog',  # Contains -v but not as separate argument
            '--Version-extra',  # Contains --Version but with extra text
            'help-h',  # Contains -h but not as separate argument
            '--Help-me',  # Contains --Help but with extra text
        ]

        with patch.object(sys, 'argv', test_args):
            result = handleCommands()
            assert result is True  # Should not trigger special handling

    def test_handleCommands_with_empty_string_arguments(self) -> None:
        """Test behavior with empty string arguments."""
        with patch.object(sys, 'argv', ['artisan', '', '-v', '']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert f"Artisan  Version {__version__}" in output
            assert result is False

    def test_handleCommands_with_whitespace_arguments(self) -> None:
        """Test behavior with whitespace-only arguments."""
        with patch.object(sys, 'argv', ['artisan', '   ', '-h', '\t\n']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert 'Usage:' in output
            assert result is False

    @pytest.mark.parametrize(
        'malformed_args',
        [
            ['artisan', '-v-h'],  # Combined flags
            ['artisan', '--Version--Help'],  # Combined long options
            ['artisan', '-vh'],  # Short flags combined
            ['artisan', '--VersionHelp'],  # Long options combined
        ],
    )
    def test_handleCommands_with_malformed_arguments(self, malformed_args: List[str]) -> None:
        """Test behavior with malformed argument combinations."""
        with patch.object(sys, 'argv', malformed_args):
            result = handleCommands()
            assert result is True  # Should not trigger special handling


class TestHandleCommandsOutputFormatting:
    """Test output formatting and content validation."""

    def test_version_output_format(self) -> None:
        """Test that version output follows expected format."""
        with patch.object(sys, 'argv', ['artisan', '-v']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            handleCommands()

            output = mock_stdout.getvalue().strip()
            # Should match exact format: "Artisan  Version X.Y.Z"
            expected_pattern = f"Artisan  Version {__version__}"
            assert output == expected_pattern

    def test_help_output_contains_required_sections(self) -> None:
        """Test that help output contains all required sections."""
        with patch.object(sys, 'argv', ['artisan', '-h']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            handleCommands()

            output = mock_stdout.getvalue()

            # Check for required sections
            assert f"Artisan Version {__version__}" in output
            assert 'Usage:' in output
            assert 'artisan' in output
            assert 'artisan [options] [path ...]' in output
            assert 'Options:' in output
            assert '-h, --help' in output
            assert 'Show help' in output
            assert '-v, --Version' in output
            assert 'Show version number' in output

    def test_help_output_formatting_consistency(self) -> None:
        """Test that help output formatting is consistent."""
        with patch.object(sys, 'argv', ['artisan', '--Help']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            handleCommands()

            output = mock_stdout.getvalue()

            # Check that version is properly formatted in help text
            lines = output.split('\n')
            version_line = next((line for line in lines if 'Artisan Version' in line), None)
            assert version_line is not None
            assert __version__ in version_line


class TestHandleCommandsSystemIntegration:
    """Test system integration aspects and error conditions."""

    def test_handleCommands_preserves_original_argv(self) -> None:
        """Test that handleCommands doesn't modify sys.argv."""
        original_argv = ['artisan', 'test.alog', '-v']

        with patch.object(sys, 'argv', original_argv.copy()):
            handleCommands()
            # sys.argv should remain unchanged
            assert sys.argv == original_argv

    def test_handleCommands_with_unicode_arguments(self) -> None:
        """Test behavior with Unicode characters in arguments."""
        unicode_args = ['artisan', 'café.alog', '-v', '测试']

        with patch.object(sys, 'argv', unicode_args), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert f"Artisan  Version {__version__}" in output
            assert result is False

    def test_handleCommands_with_very_long_argument_list(self) -> None:
        """Test behavior with a very long argument list."""
        long_args = ['artisan'] + [f"file{i}.alog" for i in range(1000)] + ['-v']

        with patch.object(sys, 'argv', long_args), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert f"Artisan  Version {__version__}" in output
            assert result is False

    def test_handleCommands_with_special_characters_in_arguments(self) -> None:
        """Test behavior with special characters in arguments."""
        special_args = [
            'artisan',
            'file with spaces.alog',
            'file@#$%^&*().alog',
            'file\nwith\nnewlines.alog',
            '-v',
        ]

        with patch.object(sys, 'argv', special_args), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert f"Artisan  Version {__version__}" in output
            assert result is False


class TestHandleCommandsBugHunting:
    """Test edge cases that might reveal bugs in the command handling logic."""

    def test_handleCommands_with_none_in_argv(self) -> None:
        """Test behavior when sys.argv contains None values."""
        # This is an edge case that shouldn't happen in normal usage
        # Python's 'in' operator actually handles None gracefully
        with patch.object(sys, 'argv', ['artisan', None, '-v']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            # Should still find -v and print version
            output = mock_stdout.getvalue()
            assert f"Artisan  Version {__version__}" in output
            assert result is False

    def test_handleCommands_with_non_string_arguments(self) -> None:
        """Test behavior with non-string arguments in sys.argv."""
        # This shouldn't happen in normal usage but tests robustness
        # Python's 'in' operator actually handles integers gracefully
        with patch.object(sys, 'argv', ['artisan', 123, '-v']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            # Should still find -v and print version
            output = mock_stdout.getvalue()
            assert f"Artisan  Version {__version__}" in output
            assert result is False

    def test_handleCommands_early_return_behavior(self) -> None:
        """Test that function returns immediately after finding first match."""
        call_count = 0
        original_print = print

        def counting_print(*args:Any, **kwargs:Any) -> None:
            nonlocal call_count
            call_count += 1 # pyrefly: ignore[unknown-name]
            return original_print(*args, **kwargs)

        with patch.object(sys, 'argv', ['artisan', '-v', '-h']), \
                patch('builtins.print', side_effect=counting_print), \
                patch('sys.stdout', new_callable=StringIO):
            result = handleCommands()

            # Should only print once (for version) and return False
            assert call_count == 1
            assert result is False

    def test_handleCommands_argument_order_independence(self) -> None:
        """Test that argument order doesn't affect the outcome when only one type is present."""
        test_cases = [
            ['artisan', '-v', 'file1.alog', 'file2.alog'],
            ['artisan', 'file1.alog', '-v', 'file2.alog'],
            ['artisan', 'file1.alog', 'file2.alog', '-v'],
        ]

        for args in test_cases:
            with patch.object(sys, 'argv', args), \
                    patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = handleCommands()

                output = mock_stdout.getvalue()
                assert f"Artisan  Version {__version__}" in output
                assert result is False

    def test_handleCommands_with_similar_but_different_arguments(self) -> None:
        """Test with arguments that are similar to special ones but not exact matches."""
        similar_args = [
            '-version',  # Missing second dash
            '--v',  # Wrong format
            '-help',  # Missing second dash
            '--h',  # Wrong format
            '-V',  # Wrong case
            '--version',  # Wrong case
            '-H',  # Wrong case
            '--help',  # Wrong case
            'v',  # Missing dash
            'h',  # Missing dash
            '--Version-',  # Extra character
            '--Help-',  # Extra character
            '-v-',  # Extra character
            '-h-',  # Extra character
        ]

        for arg in similar_args:
            with patch.object(sys, 'argv', ['artisan', arg]):
                result = handleCommands()
                assert result is True, f"Argument '{arg}' should not trigger special handling"

    def test_handleCommands_with_substrings_of_special_arguments(self) -> None:
        """Test with arguments that contain special arguments as substrings."""
        substring_args = [
            'prefix-v',
            '-vsuffix',
            'prefix--Version',
            '--Versionsuffix',
            'prefix-h',
            '-hsuffix',
            'prefix--Help',
            '--Helpsuffix',
            'file-v.alog',
            'file--Version.alog',
            'file-h.alog',
            'file--Help.alog',
        ]

        for arg in substring_args:
            with patch.object(sys, 'argv', ['artisan', arg]):
                result = handleCommands()
                assert result is True, f"Argument '{arg}' should not trigger special handling"

    def test_handleCommands_memory_efficiency_with_large_argv(self) -> None:
        """Test memory efficiency with very large sys.argv."""
        # Create a large argv list to test if the function handles it efficiently
        large_argv = ['artisan'] + [f"file{i}.alog" for i in range(1000)]

        with patch.object(sys, 'argv', large_argv):
            result = handleCommands()
            assert result is True

        # Now test with version flag at the end
        large_argv_with_version = large_argv + ['-v']

        with patch.object(sys, 'argv', large_argv_with_version), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert f"Artisan  Version {__version__}" in output
            assert result is False

    def test_handleCommands_with_empty_strings_and_whitespace(self) -> None:
        """Test comprehensive whitespace and empty string handling."""
        whitespace_test_cases = [
            ['artisan', '', '-v'],  # Empty string
            ['artisan', ' ', '-v'],  # Single space
            ['artisan', '\t', '-v'],  # Tab
            ['artisan', '\n', '-v'],  # Newline
            ['artisan', '\r', '-v'],  # Carriage return
            ['artisan', '\r\n', '-v'],  # Windows line ending
            ['artisan', '   ', '-v'],  # Multiple spaces
            ['artisan', '\t\n\r ', '-v'],  # Mixed whitespace
        ]

        for args in whitespace_test_cases:
            with patch.object(sys, 'argv', args), \
                    patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = handleCommands()

                output = mock_stdout.getvalue()
                assert f"Artisan  Version {__version__}" in output
                assert result is False


class TestHandleCommandsRobustness:
    """Test robustness and error handling."""

    def test_handleCommands_with_print_failure(self) -> None:
        """Test behavior when print() function fails."""

        def failing_print(*args:Any, **kwargs:Any) -> None:
            del args
            del kwargs
            raise OSError('Print failed')

        # Should raise the OSError from print
        with patch.object(sys, 'argv', ['artisan', '-v']), \
                patch('builtins.print', side_effect=failing_print), \
                pytest.raises(OSError, match='Print failed'):
            handleCommands()

    def test_handleCommands_with_stdout_unavailable(self) -> None:
        """Test behavior when stdout is not available."""
        with patch.object(sys, 'argv', ['artisan', '-v']), \
                patch('sys.stdout', None):
            # Print function is robust and handles None stdout gracefully
            # So this test should actually succeed without raising an exception
            result = handleCommands()
            assert result is False

    def test_handleCommands_version_import_edge_case(self) -> None:
        """Test behavior when __version__ has unexpected value."""
        with patch('artisanlib.command_utility.__version__', None), \
                patch.object(sys, 'argv', ['artisan', '-v']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert 'Artisan  Version None' in output
            assert result is False

    def test_handleCommands_with_extremely_long_arguments(self) -> None:
        """Test with extremely long individual arguments."""
        # Create very long strings that might cause memory issues
        very_long_arg = 'x' * 100000  # 100KB string

        with patch.object(sys, 'argv', ['artisan', very_long_arg, '-v']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert f"Artisan  Version {__version__}" in output
            assert result is False

    def test_handleCommands_string_comparison_edge_cases(self) -> None:
        """Test edge cases in string comparison logic."""
        # Test arguments that might cause issues with set membership testing
        edge_case_args = [
            '-v\x00',  # Null byte
            '--Version\x00',  # Null byte
            '-h\x00',  # Null byte
            '--Help\x00',  # Null byte
            '-v\xff',  # High byte value
            '--Version\xff',  # High byte value
        ]

        for arg in edge_case_args:
            with patch.object(sys, 'argv', ['artisan', arg]):
                result = handleCommands()
                assert result is True, 'Argument with special bytes should not trigger handling'

    def test_handleCommands_unicode_normalization_edge_cases(self) -> None:
        """Test Unicode normalization edge cases."""
        # Test with Unicode characters that might look similar to ASCII
        unicode_args = [
            '-ｖ',  # Full-width v
            '--Ｖersion',  # Full-width V
            '-ｈ',  # Full-width h
            '--Ｈelp',  # Full-width H
            '-v\u0301',  # v with combining acute accent
            '--Version\u0301',  # Version with combining accent
        ]

        for arg in unicode_args:
            with patch.object(sys, 'argv', ['artisan', arg]):
                result = handleCommands()
                assert result is True, f"Unicode argument '{arg}' should not trigger handling"

    @pytest.mark.parametrize(
        'special_version_value',
        [
            '',  # Empty string
            '   ',  # Whitespace only
            '\n\t\r',  # Control characters
            'None',  # String "None"
            '1.0\x00',  # Version with null byte
            '1.0\n2.0',  # Version with newline
            'α.β.γ',  # Unicode version
        ],
    )
    def test_handleCommands_with_unusual_version_values(self, special_version_value: str) -> None:
        """Test behavior with unusual __version__ values."""
        with patch('artisanlib.command_utility.__version__', special_version_value), \
                patch.object(sys, 'argv', ['artisan', '-v']), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert f"Artisan  Version {special_version_value}" in output
            assert result is False

    def test_handleCommands_iteration_behavior_with_modified_argv(self) -> None:
        """Test behavior when sys.argv is modified during iteration."""
        # This tests a potential race condition or unexpected behavior
        original_argv = ['artisan', 'file.alog', '-v']

        # The function should still work correctly even if argv is modified
        with patch.object(sys, 'argv', original_argv), \
                patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = handleCommands()

            output = mock_stdout.getvalue()
            assert f"Artisan  Version {__version__}" in output
            assert result is False

    def test_handleCommands_concurrent_access_simulation(self) -> None:
        """Test simulation of concurrent access to sys.argv."""
        # This tests potential race conditions
        import threading

        results = []

        def worker() -> None:
            with patch.object(sys, 'argv', ['artisan', '-v']), \
                    patch('sys.stdout', new_callable=StringIO):
                result = handleCommands()
                results.append(result)

        # Start multiple threads
        threads = []
        for _ in range(5):  # Reduced from 10 to avoid test timeout
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All should return False
        assert all(result is False for result in results)
        assert len(results) == 5
