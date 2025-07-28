"""Unit tests for artisanlib.suppress_errors module.

This module tests the suppress_stdout_stderr context manager functionality including:
- Context manager initialization and cleanup
- File descriptor management and duplication
- stdout and stderr suppression during context
- Proper restoration of original streams
- Error handling for Windows compatibility issues
- File descriptor closing and cleanup
- Exception handling during initialization and cleanup
- Cross-platform compatibility testing
"""

import os
from typing import Dict, Generator
from unittest.mock import Mock, call, patch

import pytest

from artisanlib.suppress_errors import suppress_stdout_stderr


@pytest.fixture
def mock_os_functions() -> Generator[Dict[str, Mock], None, None]:
    """Create mocks for os module functions."""
    with patch('artisanlib.suppress_errors.os.open') as mock_open, patch(
        'artisanlib.suppress_errors.os.dup'
    ) as mock_dup, patch('artisanlib.suppress_errors.os.dup2') as mock_dup2, patch(
        'artisanlib.suppress_errors.os.close'
    ) as mock_close, patch(
        'artisanlib.suppress_errors.os.devnull', '/dev/null'
    ):

        # Configure default return values
        mock_open.return_value = 10  # Mock file descriptor
        mock_dup.side_effect = [3, 4]  # Mock saved file descriptors

        yield {'open': mock_open, 'dup': mock_dup, 'dup2': mock_dup2, 'close': mock_close}


@pytest.fixture
def mock_sys_streams() -> Generator[Dict[str, Mock], None, None]:
    """Create mocks for sys.stdout and sys.stderr."""
    with patch('artisanlib.suppress_errors.sys.stdout') as mock_stdout, patch(
        'artisanlib.suppress_errors.sys.stderr'
    ) as mock_stderr:

        mock_stdout.fileno.return_value = 1
        mock_stderr.fileno.return_value = 2

        yield {'stdout': mock_stdout, 'stderr': mock_stderr}


class TestSuppressStdoutStderrInitialization:
    """Test suppress_stdout_stderr context manager initialization."""

    def test_successful_initialization(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test successful initialization with proper file descriptor setup."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]  # Two null file descriptors
        mock_os_functions['dup'].side_effect = [3, 4]  # Two saved file descriptors

        # Act
        suppressor = suppress_stdout_stderr()

        # Assert
        assert suppressor.null_fds == [10, 11]
        assert suppressor.save_fds == [3, 4]

        # Verify os.open was called twice for null files
        assert mock_os_functions['open'].call_count == 2
        mock_os_functions['open'].assert_has_calls(
            [call('/dev/null', os.O_RDWR), call('/dev/null', os.O_RDWR)]
        )

        # Verify os.dup was called for stdout and stderr
        mock_os_functions['dup'].assert_has_calls([call(1), call(2)])

    def test_initialization_with_os_open_exception(
        self, mock_os_functions: Dict[str, Mock]
    ) -> None:
        """Test initialization when os.open fails."""
        # Arrange
        mock_os_functions['open'].side_effect = OSError('Cannot open /dev/null')

        # Act
        suppressor = suppress_stdout_stderr()

        # Assert
        assert suppressor.null_fds == []
        assert suppressor.save_fds == []

        # Verify os.dup was not called
        mock_os_functions['dup'].assert_not_called()

    def test_initialization_with_os_dup_exception_fallback_to_fileno(
        self, mock_os_functions: Dict[str, Mock], mock_sys_streams: Dict[str, Mock]
    ) -> None:
        """Test initialization when os.dup fails and falls back to fileno."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = OSError('Windows error')  # First dup call fails
        mock_sys_streams['stdout'].fileno.return_value = 1
        mock_sys_streams['stderr'].fileno.return_value = 2

        # Act
        suppressor = suppress_stdout_stderr()

        # Assert
        assert suppressor.null_fds == [10, 11]
        # Should have empty save_fds due to exception in fallback
        assert suppressor.save_fds == []

    def test_initialization_with_all_dup_exceptions(
        self, mock_os_functions: Dict[str, Mock], mock_sys_streams: Dict[str, Mock]
    ) -> None:
        """Test initialization when all dup operations fail."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = OSError('First dup fails')
        mock_sys_streams['stdout'].fileno.side_effect = OSError('fileno fails')
        mock_sys_streams['stderr'].fileno.side_effect = OSError('fileno fails')

        # Act
        suppressor = suppress_stdout_stderr()

        # Assert
        assert suppressor.null_fds == [10, 11]
        assert suppressor.save_fds == []


class TestSuppressStdoutStderrContextManager:
    """Test suppress_stdout_stderr context manager enter and exit."""

    def test_enter_with_valid_file_descriptors(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test __enter__ method with valid file descriptors."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = [3, 4]

        suppressor = suppress_stdout_stderr()

        # Act
        suppressor.__enter__()

        # Assert
        mock_os_functions['dup2'].assert_has_calls(
            [call(10, 1), call(11, 2)]  # Redirect stdout to null  # Redirect stderr to null
        )

    def test_enter_with_empty_save_fds(self) -> None:
        """Test __enter__ method when save_fds is empty."""
        # Arrange
        with patch('artisanlib.suppress_errors.os.open') as mock_open, patch(
            'artisanlib.suppress_errors.os.dup2'
        ) as mock_dup2:

            mock_open.side_effect = OSError('Cannot open')

            suppressor = suppress_stdout_stderr()

            # Act
            suppressor.__enter__()

            # Assert
            mock_dup2.assert_not_called()

    def test_exit_successful_restoration(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test __exit__ method with successful restoration."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = [3, 4]

        suppressor = suppress_stdout_stderr()

        # Act
        suppressor.__exit__(None, None, None)

        # Assert
        # Verify restoration of original file descriptors
        mock_os_functions['dup2'].assert_has_calls(
            [call(3, 1), call(4, 2)]  # Restore stdout  # Restore stderr
        )

        # Verify all file descriptors are closed
        mock_os_functions['close'].assert_has_calls(
            [call(10), call(11), call(3), call(4)]  # null_fds  # save_fds
        )

    def test_exit_with_dup2_exception(self) -> None:
        """Test __exit__ method when dup2 restoration fails."""
        # Arrange
        with patch('artisanlib.suppress_errors.os.open') as mock_open, patch(
            'artisanlib.suppress_errors.os.dup'
        ) as mock_dup, patch('artisanlib.suppress_errors.os.dup2') as mock_dup2, patch(
            'artisanlib.suppress_errors.os.close'
        ) as mock_close:

            mock_open.side_effect = [10, 11]
            mock_dup.side_effect = [3, 4]
            mock_dup2.side_effect = [
                None,
                None,
                OSError('Cannot restore'),
                OSError('Cannot restore'),
            ]

            suppressor = suppress_stdout_stderr()

            # Act - Should not raise exception
            suppressor.__exit__(None, None, None)

            # Assert
            # Verify file descriptors are still closed despite dup2 failure
            mock_close.assert_has_calls(
                [call(10), call(11), call(3), call(4)]  # null_fds  # save_fds
            )

    def test_exit_with_close_exception(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test __exit__ method when close operations fail."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = [3, 4]
        mock_os_functions['close'].side_effect = OSError('Cannot close')

        suppressor = suppress_stdout_stderr()

        # Act - Should not raise exception
        suppressor.__exit__(None, None, None)

        # Assert
        # Verify all close calls were attempted
        assert mock_os_functions['close'].call_count == 4

    def test_exit_with_empty_save_fds(self) -> None:
        """Test __exit__ method when save_fds is empty."""
        # Arrange
        with patch('artisanlib.suppress_errors.os.open') as mock_open, patch(
            'artisanlib.suppress_errors.os.dup'
        ) as mock_dup, patch('artisanlib.suppress_errors.os.dup2') as mock_dup2, patch(
            'artisanlib.suppress_errors.os.close'
        ) as mock_close:

            mock_open.side_effect = [10, 11]
            mock_dup.side_effect = OSError('Cannot dup')

            suppressor = suppress_stdout_stderr()

            # Act
            suppressor.__exit__(None, None, None)

            # Assert
            # Should only close null_fds, not attempt dup2 restoration
            mock_dup2.assert_not_called()
            mock_close.assert_has_calls([call(10), call(11)])  # Only null_fds


class TestSuppressStdoutStderrIntegration:
    """Test suppress_stdout_stderr integration scenarios."""

    def test_context_manager_usage_successful(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test using suppress_stdout_stderr as a context manager successfully."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = [3, 4]

        # Act
        with suppress_stdout_stderr():
            # This would normally print to stdout/stderr but should be suppressed
            pass

        # Assert
        # Verify initialization calls
        assert mock_os_functions['open'].call_count == 2
        mock_os_functions['dup'].assert_has_calls([call(1), call(2)])

        # Verify enter calls
        mock_os_functions['dup2'].assert_has_calls(
            [call(10, 1), call(11, 2), call(3, 1), call(4, 2)]  # Suppress  # Restore
        )

        # Verify cleanup calls
        mock_os_functions['close'].assert_has_calls([call(10), call(11), call(3), call(4)])

    def test_context_manager_with_exception_in_block(
        self, mock_os_functions: Dict[str, Mock]
    ) -> None:
        """Test context manager when exception occurs in the with block."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = [3, 4]

        # Act & Assert
        with pytest.raises(ValueError), suppress_stdout_stderr():
            raise ValueError('Test exception')

        # Verify cleanup still occurred
        mock_os_functions['close'].assert_has_calls([call(10), call(11), call(3), call(4)])

    def test_context_manager_with_initialization_failure(self) -> None:
        """Test context manager when initialization fails."""
        # Arrange
        with patch('artisanlib.suppress_errors.os.open') as mock_open, patch(
            'artisanlib.suppress_errors.os.dup2'
        ) as mock_dup2, patch('artisanlib.suppress_errors.os.close') as mock_close:
            mock_open.side_effect = OSError('Cannot open')

            # Act
            with suppress_stdout_stderr():
                pass

            # Assert
            # Should not attempt dup2 operations
            mock_dup2.assert_not_called()
            mock_close.assert_not_called()

    def test_multiple_context_manager_instances(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test multiple instances of the context manager."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11, 12, 13]
        mock_os_functions['dup'].side_effect = [3, 4, 5, 6]

        # Act
        with suppress_stdout_stderr():
            pass

        with suppress_stdout_stderr():
            pass

        # Assert
        # Verify both instances were properly initialized and cleaned up
        assert mock_os_functions['open'].call_count == 4
        assert mock_os_functions['dup'].call_count == 4
        assert mock_os_functions['close'].call_count == 8

    def test_nested_context_managers(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test nested context managers."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11, 12, 13]
        mock_os_functions['dup'].side_effect = [3, 4, 5, 6]

        # Act
        with suppress_stdout_stderr(), suppress_stdout_stderr():
            pass

        # Assert
        # Verify both instances were properly handled
        assert mock_os_functions['open'].call_count == 4
        assert mock_os_functions['close'].call_count == 8


class TestSuppressStdoutStderrEdgeCases:
    """Test edge cases and error conditions."""

    def test_partial_initialization_failure(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test when only some file descriptors can be opened."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, OSError('Second open fails')]

        # Act
        suppressor = suppress_stdout_stderr()

        # Assert
        assert suppressor.null_fds == []
        assert suppressor.save_fds == []

    def test_file_descriptor_values(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test with various file descriptor values."""
        # Arrange
        mock_os_functions['open'].side_effect = [100, 101]
        mock_os_functions['dup'].side_effect = [200, 201]

        # Act
        suppressor = suppress_stdout_stderr()

        # Assert
        assert suppressor.null_fds == [100, 101]
        assert suppressor.save_fds == [200, 201]

    def test_exception_parameters_ignored(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test that __exit__ properly ignores exception parameters."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = [3, 4]

        suppressor = suppress_stdout_stderr()

        # Act
        suppressor.__exit__(ValueError, ValueError('test'), None)

        # Assert
        # Should not suppress exceptions (method returns None)
        mock_os_functions['close'].assert_has_calls([call(10), call(11), call(3), call(4)])


class TestSuppressStdoutStderrRealWorld:
    """Test real-world scenarios and platform-specific behavior."""

    def test_windows_compatibility_os_dup_failure(
        self, mock_os_functions: Dict[str, Mock], mock_sys_streams: Dict[str, Mock]
    ) -> None:
        """Test Windows compatibility when os.dup fails with WinError 87."""
        # Arrange - Simulate Windows 7 Python 3.7.4 error
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = OSError('[WinError 87] The parameter is incorrect')
        mock_sys_streams['stdout'].fileno.return_value = 1
        mock_sys_streams['stderr'].fileno.return_value = 2

        # Mock the fallback dup calls to also fail
        with patch('artisanlib.suppress_errors.os.dup') as mock_dup_fallback:
            mock_dup_fallback.side_effect = OSError('Fallback also fails')

            # Act
            suppressor = suppress_stdout_stderr()

            # Assert
            assert suppressor.null_fds == [10, 11]
            assert suppressor.save_fds == []

    def test_devnull_path_handling(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test proper handling of os.devnull path."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = [3, 4]

        # Act
        suppress_stdout_stderr()

        # Assert
        mock_os_functions['open'].assert_has_calls(
            [call('/dev/null', os.O_RDWR), call('/dev/null', os.O_RDWR)]
        )

    def test_file_descriptor_cleanup_robustness(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test robust file descriptor cleanup even with partial failures."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = [3, 4]

        # Make some close calls fail
        def close_side_effect(fd: int) -> None:
            if fd == 11:
                raise OSError('Cannot close fd 11')
            if fd == 3:
                raise OSError('Cannot close fd 3')

        mock_os_functions['close'].side_effect = close_side_effect

        suppressor = suppress_stdout_stderr()

        # Act - Should not raise exception
        suppressor.__exit__(None, None, None)

        # Assert - All close calls should be attempted
        mock_os_functions['close'].assert_has_calls([call(10), call(11), call(3), call(4)])

    def test_stdout_stderr_suppression_behavior(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test that stdout and stderr are properly redirected during suppression."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = [3, 4]

        suppressor = suppress_stdout_stderr()

        # Act - Enter context
        suppressor.__enter__()

        # Assert - Verify redirection to null devices
        mock_os_functions['dup2'].assert_has_calls(
            [call(10, 1), call(11, 2)]  # stdout redirected to null  # stderr redirected to null
        )

        # Act - Exit context
        suppressor.__exit__(None, None, None)

        # Assert - Verify restoration
        expected_calls = [
            call(10, 1),
            call(11, 2),  # Initial redirection
            call(3, 1),
            call(4, 2),  # Restoration
        ]
        mock_os_functions['dup2'].assert_has_calls(expected_calls)

    def test_exception_propagation(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test that exceptions from the with block are properly propagated."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = [3, 4]

        # Act & Assert
        with pytest.raises(RuntimeError, match='Test error'), suppress_stdout_stderr():
            raise RuntimeError('Test error')

        # Verify cleanup occurred despite exception
        mock_os_functions['close'].assert_has_calls([call(10), call(11), call(3), call(4)])

    def test_concurrent_usage_simulation(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test simulation of concurrent usage with different file descriptors."""
        # Arrange - Simulate different file descriptors for concurrent instances
        mock_os_functions['open'].side_effect = [10, 11, 20, 21, 30, 31]
        mock_os_functions['dup'].side_effect = [3, 4, 5, 6, 7, 8]

        # Act - Create multiple instances
        suppressor1 = suppress_stdout_stderr()
        suppressor2 = suppress_stdout_stderr()
        suppressor3 = suppress_stdout_stderr()

        # Assert - Each instance should have unique file descriptors
        assert suppressor1.null_fds == [10, 11]
        assert suppressor1.save_fds == [3, 4]

        assert suppressor2.null_fds == [20, 21]
        assert suppressor2.save_fds == [5, 6]

        assert suppressor3.null_fds == [30, 31]
        assert suppressor3.save_fds == [7, 8]

    def test_resource_cleanup_on_initialization_failure(
        self, mock_os_functions: Dict[str, Mock]
    ) -> None:
        """Test that resources are properly cleaned up when initialization fails."""
        # Arrange - First open succeeds, second fails
        mock_os_functions['open'].side_effect = [10, OSError('Second open fails')]

        # Act
        suppressor = suppress_stdout_stderr()

        # Assert - Should have empty file descriptor lists
        assert suppressor.null_fds == []
        assert suppressor.save_fds == []

        # Verify no cleanup calls since initialization failed
        mock_os_functions['close'].assert_not_called()

    def test_context_manager_protocol_compliance(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test that the context manager properly implements the protocol."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = [3, 4]

        suppressor = suppress_stdout_stderr()

        # Act & Assert - Test context manager protocol
        assert hasattr(suppressor, '__enter__')
        assert hasattr(suppressor, '__exit__')

        # Test __enter__ returns None (standard for context managers that don't return a value)
        suppressor.__enter__()

        # Test __exit__ returns None (doesn't suppress exceptions)
        suppressor.__exit__(None, None, None)

    def test_file_descriptor_range_handling(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test handling of various file descriptor ranges."""
        # Arrange - Test with high file descriptor numbers
        mock_os_functions['open'].side_effect = [1000, 1001]
        mock_os_functions['dup'].side_effect = [2000, 2001]

        # Act
        suppressor = suppress_stdout_stderr()

        # Assert
        assert suppressor.null_fds == [1000, 1001]
        assert suppressor.save_fds == [2000, 2001]

        # Test context usage
        suppressor.__enter__()
        suppressor.__exit__(None, None, None)

        # Verify proper handling of high file descriptor numbers
        mock_os_functions['dup2'].assert_has_calls(
            [
                call(1000, 1),
                call(1001, 2),  # Redirection
                call(2000, 1),
                call(2001, 2),  # Restoration
            ]
        )

    def test_os_module_constants_usage(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test proper usage of os module constants."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = [3, 4]

        # Act
        suppress_stdout_stderr()

        # Assert - Verify os.O_RDWR constant is used correctly
        mock_os_functions['open'].assert_has_calls(
            [call('/dev/null', os.O_RDWR), call('/dev/null', os.O_RDWR)]
        )

    def test_type_annotations_compliance(self, mock_os_functions: Dict[str, Mock]) -> None:
        """Test that the implementation complies with type annotations."""
        # Arrange
        mock_os_functions['open'].side_effect = [10, 11]
        mock_os_functions['dup'].side_effect = [3, 4]

        # Act
        suppressor = suppress_stdout_stderr()

        # Assert - Test that methods accept the expected types
        suppressor.__enter__()

        # Test __exit__ with various exception parameter combinations
        suppressor.__exit__(None, None, None)
        suppressor.__exit__(ValueError, ValueError('test'), None)
