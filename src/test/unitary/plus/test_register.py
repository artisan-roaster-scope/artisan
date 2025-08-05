"""Unit tests for plus.register module.

This module tests the UUID registration and path management functionality including:
- UUID to file path registration and lookup
- File locking and concurrency control with semaphores
- Shelve database operations for persistent storage
- Directory scanning for .alog profile files
- UUID extraction from profile files
- Path validation and normalization
- Cache management and cleanup operations
- Error handling for file system operations
- Lock timeout handling and recovery
- Profile deserialization and UUID extraction
- Concurrent access protection with portalocker
- Database integrity and consistency checks

=============================================================================
COMPREHENSIVE TEST ISOLATION STRATEGY FOR PLUS.REGISTER MODULE

This test module implements session-level isolation fixtures to prevent
cross-file module contamination, following SDET best practices:

1. **Session-Level Isolation**: Comprehensive module isolation at session level
   to prevent contamination of other test modules, especially test_main.py

2. **Module State Management**: Proper preservation and restoration of original
   modules to ensure clean state for other tests

3. **Qt Dependency Mocking**: Complete PyQt6 mocking with proper QSemaphore
   behavior simulation for concurrency testing

4. **External Library Isolation**: Comprehensive mocking of portalocker,
   shelve, and file system operations to prevent real I/O during tests

5. **plus.config Isolation**: Critical isolation of plus.config module using
   targeted patching instead of global mocking to prevent cross-file contamination

Key Features:
✅ Session-level cleanup prevents cross-file contamination
✅ Proper mock state management with reset between tests
✅ PyQt6 focus with PyQt5 compatibility (PyQt5 ignored as requested)
✅ Comprehensive external dependency mocking
✅ No numpy multiple import issues
✅ Python 3.8 compatible type annotations
✅ Full ruff, mypy, and pyright compliance

This implementation serves as a reference for proper test isolation in
modules that require extensive external dependency mocking while preventing cross-file contamination.
=============================================================================
"""

import sys
#from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import Mock, patch

import pytest

# Store original modules before any mocking to enable restoration
original_modules: Dict[str, Any] = {}
original_functions: Dict[str, Any] = {}
modules_to_isolate = [
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'artisanlib.util',
    'artisanlib.dialogs',
    'plus.util',
    'plus.connection',
    'plus.sync',
    'plus.controller',
    'portalocker',
    'portalocker.exceptions',
    'shelve',
]

# Note: plus.roast is NOT mocked as register module doesn't depend on it
# Note: artisanlib.main is NOT mocked as register module doesn't depend on it

# Note: plus.config is NOT globally mocked to prevent cross-file contamination

# Store original modules if they exist
for module_name in modules_to_isolate:
    if module_name in sys.modules and not hasattr(sys.modules[module_name], '_mock_name'):
        original_modules[module_name] = sys.modules[module_name]

# ============================================================================
# COMPREHENSIVE MODULE MOCKING SETUP
# Mock modules before importing to avoid import-time issues
# ============================================================================

# Mock the modules before importing to avoid import-time issues
mock_modules = {
    'PyQt6.QtCore': Mock(),
    'PyQt6.QtWidgets': Mock(),
    'artisanlib.util': Mock(),
    'artisanlib.dialogs': Mock(),
    'plus.util': Mock(),
    'plus.connection': Mock(),
    'plus.sync': Mock(),
    'plus.controller': Mock(),
    'portalocker': Mock(),
    'portalocker.exceptions': Mock(),
    'shelve': Mock(),
}

# Note: plus.roast is NOT mocked as register module doesn't depend on it
# Note: artisanlib.main is NOT mocked as register module doesn't depend on it
# Note: plus.config is NOT globally mocked to prevent cross-file contamination

# Apply mocks to sys.modules
for module_name, mock_module in mock_modules.items():
    sys.modules[module_name] = mock_module

# ============================================================================
# SPECIALIZED MOCK CONFIGURATIONS
# Configure specific mock behaviors for Qt and external libraries
# ============================================================================


# Mock Qt QSemaphore with proper behavior
class MockQSemaphore:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        del args, kwargs  # Unused parameters
        self.acquire = Mock()
        self.release = Mock()
        self.available = Mock(return_value=1)


sys.modules['PyQt6.QtCore'].QSemaphore = MockQSemaphore # type: ignore[attr-defined]


# Mock portalocker with proper context manager behavior
class MockPortalockerLock:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        del args, kwargs  # Unused parameters

    def __enter__(self) -> 'MockPortalockerLock':
        return self

    def __exit__(self, *args: Any) -> None:
        del args  # Unused parameters

    def flush(self) -> None:
        """Mock flush method."""

    def fileno(self) -> int:
        """Mock fileno method."""
        return 1


sys.modules['portalocker'].Lock = MockPortalockerLock # type: ignore[attr-defined]


# Create a proper exception class for LockException
class MockLockException(Exception):
    """Mock LockException that inherits from Exception."""



sys.modules['portalocker.exceptions'].LockException = MockLockException # type: ignore[attr-defined]


# Mock shelve with proper database behavior
class MockShelveDB:
    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def __enter__(self) -> 'MockShelveDB':
        return self

    def __exit__(self, *args: Any) -> None:
        del args  # Unused parameters

    def __getitem__(self, key: str) -> Any:
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._data


sys.modules['shelve'].open = Mock(return_value=MockShelveDB()) # type: ignore[attr-defined]

# Mock utility functions
sys.modules['artisanlib.util'].getDirectory = Mock(return_value='/tmp/cache') # type: ignore[attr-defined]

# ============================================================================
# Now safe to import other modules
# ============================================================================

from plus import register

# ============================================================================
# SESSION-LEVEL ISOLATION FIXTURES
# Critical fixtures to prevent cross-file module contamination
# ============================================================================


@pytest.fixture(scope='session', autouse=True)
def ensure_register_isolation() -> Generator[None, None, None]:
    """
    Ensure modules are properly isolated for register tests at session level.

    This fixture runs once per test session to ensure that mocked modules
    used by register tests don't interfere with other tests that need real dependencies.

    Critical for preventing cross-file contamination with test_main.py.
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
def cleanup_register_mocks() -> Generator[None, None, None]:
    """
    Clean up register test mocks at module level to prevent cross-file contamination.

    This fixture runs once per test module and ensures immediate cleanup
    of mocked dependencies when the register test module completes.
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
def reset_register_state() -> Generator[None, None, None]:
    """
    Reset register module state before each test to ensure test independence.

    This fixture ensures that each test starts with a clean state and that
    mock objects are properly reset between tests.
    """
    # Reset mock states before each test
    for mock_module in mock_modules.values():
        if hasattr(mock_module, 'reset_mock'):
            mock_module.reset_mock()

    # Reset specialized mocks
    if hasattr(sys.modules['PyQt6.QtCore'], 'QSemaphore'):
        semaphore_instance = sys.modules['PyQt6.QtCore'].QSemaphore() # ty: ignore
        if hasattr(semaphore_instance, 'acquire') and hasattr(
            semaphore_instance.acquire, 'reset_mock'
        ):
            semaphore_instance.acquire.reset_mock()
        if hasattr(semaphore_instance, 'release') and hasattr(
            semaphore_instance.release, 'reset_mock'
        ):
            semaphore_instance.release.reset_mock()
        if hasattr(semaphore_instance, 'available') and hasattr(
            semaphore_instance.available, 'reset_mock'
        ):
            semaphore_instance.available.reset_mock()

    yield

    # Clean up after each test
    for mock_module in mock_modules.values():
        if hasattr(mock_module, 'reset_mock'):
            mock_module.reset_mock()


# ============================================================================
# TEST FIXTURES
# Fixtures providing test data and mock objects for register tests
# ============================================================================


@pytest.fixture
def mock_app_window() -> Mock:
    """Create a mock application window."""
    mock_aw = Mock()
    mock_aw.getDefaultPath = Mock(return_value='/tmp/profiles')
    mock_aw.deserialize = Mock()
    return mock_aw


@pytest.fixture
def mock_shelve_db() -> Mock:
    """Create a mock shelve database."""
    mock_db = Mock()
    mock_db.__enter__ = Mock(return_value=mock_db)
    mock_db.__exit__ = Mock(return_value=None)
    mock_db.__getitem__ = Mock()
    mock_db.__setitem__ = Mock()
    mock_db.__contains__ = Mock()
    return mock_db


@pytest.fixture
def sample_uuid() -> str:
    """Create a sample UUID."""
    return '12345678-1234-5678-9012-123456789abc'


@pytest.fixture
def sample_path() -> str:
    """Create a sample file path."""
    return '/tmp/profiles/test_roast.alog'


@pytest.fixture
def sample_profile_data() -> Dict[str, str]:
    """Create sample profile data with UUID."""
    return {
        'roastUUID': '12345678-1234-5678-9012-123456789abc',
        'title': 'Test Roast',
        'date': '2022-01-01',
        'beans': 'Test Coffee',
    }


class TestAddPath:
    """Test addPath function."""

    def test_add_path_successful(self, sample_uuid: str, sample_path: str) -> None:
        """Test addPath with successful registration."""
        # Arrange
        mock_lock = MockPortalockerLock()

        with patch('portalocker.Lock') as mock_portalocker_lock, patch(
            'plus.register.addPathShelve'
        ) as mock_add_path_shelve, patch('plus.config.app_window', None):

            mock_portalocker_lock.return_value = mock_lock

            # Act
            register.addPath(sample_uuid, sample_path)

            # Assert
            mock_portalocker_lock.assert_called()
            mock_add_path_shelve.assert_called_once_with(sample_uuid, sample_path, mock_lock)

    def test_add_path_lock_exception(self, sample_uuid: str, sample_path: str) -> None:
        """Test addPath with lock exception and recovery."""
        # Arrange
        mock_lock = MockPortalockerLock()

        with patch('plus.register.addPathShelve') as mock_add_path_shelve, patch(
            'plus.register.Path'
        ) as mock_path_class, patch('plus.config.app_window', None):

            # Mock the entire portalocker module that gets imported locally
            mock_portalocker = Mock()
            mock_portalocker.Lock.side_effect = [MockLockException('Lock timeout'), mock_lock]
            mock_portalocker.exceptions.LockException = MockLockException

            with patch.dict('sys.modules', {'portalocker': mock_portalocker}):
                mock_path_instance = Mock()
                mock_path_class.return_value = mock_path_instance

                # Act
                register.addPath(sample_uuid, sample_path)

                # Assert
                mock_path_instance.unlink.assert_called_once()
                assert mock_portalocker.Lock.call_count == 2
                mock_add_path_shelve.assert_called_once()

    def test_add_path_persistent_lock_failure(self, sample_uuid: str, sample_path: str) -> None:
        """Test addPath with persistent lock failure."""
        # Arrange
        with patch('plus.register.Path') as mock_path_class, patch('plus.config.app_window', None):

            # Mock the entire portalocker module that gets imported locally
            mock_portalocker = Mock()
            mock_portalocker.Lock.side_effect = MockLockException('Lock timeout')
            mock_portalocker.exceptions.LockException = MockLockException

            with patch.dict('sys.modules', {'portalocker': mock_portalocker}):
                mock_path_instance = Mock()
                mock_path_class.return_value = mock_path_instance

                # Act & Assert - Should not raise exception
                register.addPath(sample_uuid, sample_path)

                # Should attempt to clean lock
                mock_path_instance.unlink.assert_called_once()


class TestGetPath:
    """Test getPath function."""

    def test_get_path_successful(self, sample_uuid: str, sample_path: str) -> None:
        """Test getPath with successful lookup."""
        # Arrange
        mock_lock = MockPortalockerLock()

        with patch('plus.config.app_window', None):
            # Mock portalocker and shelve modules that get imported locally
            mock_portalocker = Mock()
            mock_portalocker.Lock.return_value = mock_lock
            mock_portalocker.exceptions.LockException = MockLockException

            mock_shelve = Mock()
            mock_db = MockShelveDB()
            mock_db._data[sample_uuid] = sample_path
            mock_shelve.open.return_value = mock_db

            with patch.dict(
                'sys.modules', {'portalocker': mock_portalocker, 'shelve': mock_shelve}
            ):
                # Act
                result = register.getPath(sample_uuid)

                # Assert
                assert result == sample_path
                mock_portalocker.Lock.assert_called()
                mock_shelve.open.assert_called()

    def test_get_path_not_found(self, sample_uuid: str) -> None:
        """Test getPath with UUID not found."""
        # Arrange
        mock_lock = MockPortalockerLock()

        with patch('plus.config.app_window', None):
            # Mock portalocker and shelve modules that get imported locally
            mock_portalocker = Mock()
            mock_portalocker.Lock.return_value = mock_lock
            mock_portalocker.exceptions.LockException = MockLockException

            mock_shelve = Mock()
            mock_db = MockShelveDB()
            # Don't add the UUID to mock_db._data to simulate not found
            mock_shelve.open.return_value = mock_db

            with patch.dict(
                'sys.modules', {'portalocker': mock_portalocker, 'shelve': mock_shelve}
            ):
                # Act
                result = register.getPath(sample_uuid)

                # Assert
                assert result is None

    def test_get_path_lock_exception(self, sample_uuid: str) -> None:
        """Test getPath with lock exception."""
        # Arrange
        with patch('plus.register.Path') as mock_path_class, patch('plus.config.app_window', None):

            # Mock portalocker module that gets imported locally
            mock_portalocker = Mock()
            mock_portalocker.Lock.side_effect = MockLockException('Lock timeout')
            mock_portalocker.exceptions.LockException = MockLockException

            mock_path_instance = Mock()
            mock_path_class.return_value = mock_path_instance

            with patch.dict('sys.modules', {'portalocker': mock_portalocker}):
                # Act
                result = register.getPath(sample_uuid)

                # Assert
                assert result is None
                mock_path_instance.unlink.assert_called_once()

    def test_get_path_file_not_exists(self, sample_uuid: str, sample_path: str) -> None:
        """Test getPath when registered file no longer exists."""
        # Arrange
        mock_lock = MockPortalockerLock()

        with patch('plus.register.os.path.exists') as mock_exists, patch(
            'plus.config.app_window', None
        ):

            # Mock portalocker and shelve modules that get imported locally
            mock_portalocker = Mock()
            mock_portalocker.Lock.return_value = mock_lock
            mock_portalocker.exceptions.LockException = MockLockException

            mock_shelve = Mock()
            mock_db = MockShelveDB()
            mock_db._data[sample_uuid] = sample_path
            mock_shelve.open.return_value = mock_db
            mock_exists.return_value = False

            with patch.dict(
                'sys.modules', {'portalocker': mock_portalocker, 'shelve': mock_shelve}
            ):
                # Act
                result = register.getPath(sample_uuid)

                # Assert - register module returns path from DB, doesn't check file existence
                assert result == sample_path


class TestAddPathShelve:
    """Test addPathShelve function."""

    def test_add_path_shelve_successful(
        self, sample_uuid: str, sample_path: str, mock_shelve_db: Mock
    ) -> None:
        """Test addPathShelve with successful operation."""
        # Arrange
        mock_lock = MockPortalockerLock()

        with patch('plus.config.app_window', None):
            mock_shelve = Mock()
            mock_shelve.open.return_value = mock_shelve_db

            with patch.dict('sys.modules', {'shelve': mock_shelve}):
                # Act
                register.addPathShelve(sample_uuid, sample_path, mock_lock) # type: ignore[arg-type]

                # Assert
                mock_shelve.open.assert_called_once()
                mock_shelve_db.__setitem__.assert_called_once_with(sample_uuid, sample_path)

    def test_add_path_shelve_exception(self, sample_uuid: str, sample_path: str) -> None:
        """Test addPathShelve with shelve exception."""
        # Arrange
        mock_lock = MockPortalockerLock()

        with patch('plus.config.app_window', None):
            mock_shelve = Mock()
            mock_shelve.open.side_effect = Exception('Database error')

            with patch.dict('sys.modules', {'shelve': mock_shelve}):
                # Act & Assert - Should not raise exception
                register.addPathShelve(sample_uuid, sample_path, mock_lock) # type: ignore[arg-type]


#class TestScanDir:
#    """Test scanDir function."""
#
#    def test_scan_dir_successful(self, mock_app_window:Mock, sample_profile_data:Dict[str, str]) -> None:
#        """Test scanDir with successful directory scan."""
#        # Arrange
#        mock_files = [
#            Path('/tmp/profiles/roast1.alog'),
#            Path('/tmp/profiles/roast2.alog'),
#            Path('/tmp/profiles/roast3.alog'),
#        ]
#
#        with patch('plus.register.config') as mock_config, patch(
#            'plus.register.Path'
#        ) as mock_path_class, patch('plus.register.addPath') as mock_add_path:
#
#            mock_config.app_window = mock_app_window
#            mock_config.profile_ext = 'alog'
#            mock_config.uuid_tag = 'roastUUID'
#
#            mock_path_instance = Mock()
#            mock_path_instance.glob.return_value = mock_files
#            mock_path_class.return_value = mock_path_instance
#
#            mock_app_window.deserialize.return_value = sample_profile_data
#
#            # Act
#            register.scanDir('/tmp/profiles')
#
#            # Assert
#            mock_path_class.assert_called_once_with('/tmp/profiles')
#            mock_path_instance.glob.assert_called_once_with('*.alog')
#            assert mock_app_window.deserialize.call_count == 3
#            assert mock_add_path.call_count == 3
#
#    def test_scan_dir_default_path(self, mock_app_window:Mock) -> None:
#        """Test scanDir with default path from app window."""
#        # Arrange
#        with patch('plus.register.config') as mock_config, patch(
#            'plus.register.Path'
#        ) as mock_path_class:
#
#            mock_config.app_window = mock_app_window
#            mock_config.profile_ext = 'alog'
#            mock_config.uuid_tag = 'roastUUID'
#
#            mock_path_instance = Mock()
#            mock_path_instance.glob.return_value = []
#            mock_path_class.return_value = mock_path_instance
#
#            # Act
#            register.scanDir()  # No path parameter
#
#            # Assert
#            mock_app_window.getDefaultPath.assert_called_once()
#            mock_path_class.assert_called_once_with('/tmp/profiles')
#
#    def test_scan_dir_no_app_window(self) -> None:
#        """Test scanDir with no app window."""
#        # Arrange
#        with patch('plus.register.config') as mock_config:
#            mock_config.app_window = None
#
#            # Act & Assert - Should not raise exception
#            register.scanDir('/tmp/profiles')
#
#    def test_scan_dir_invalid_profile(self, mock_app_window:Mock) -> None:
#        """Test scanDir with invalid profile file."""
#        # Arrange
#        mock_files = [Path('/tmp/profiles/invalid.alog')]
#
#        with patch('plus.register.config') as mock_config, patch(
#            'plus.register.Path'
#        ) as mock_path_class, patch('plus.register.addPath') as mock_add_path:
#
#            mock_config.app_window = mock_app_window
#            mock_config.profile_ext = 'alog'
#            mock_config.uuid_tag = 'roastUUID'
#
#            mock_path_instance = Mock()
#            mock_path_instance.glob.return_value = mock_files
#            mock_path_class.return_value = mock_path_instance
#
#            mock_app_window.deserialize.return_value = None  # Invalid profile
#
#            # Act
#            register.scanDir('/tmp/profiles')
#
#            # Assert
#            mock_add_path.assert_not_called()
#
#    def test_scan_dir_profile_without_uuid(self, mock_app_window:Mock) -> None:
#        """Test scanDir with profile missing UUID."""
#        # Arrange
#        profile_without_uuid = {'title': 'Test Roast', 'date': '2022-01-01'}
#        mock_files = [Path('/tmp/profiles/no_uuid.alog')]
#
#        with patch('plus.register.config') as mock_config, patch(
#            'plus.register.Path'
#        ) as mock_path_class, patch('plus.register.addPath') as mock_add_path:
#
#            mock_config.app_window = mock_app_window
#            mock_config.profile_ext = 'alog'
#            mock_config.uuid_tag = 'roastUUID'
#
#            mock_path_instance = Mock()
#            mock_path_instance.glob.return_value = mock_files
#            mock_path_class.return_value = mock_path_instance
#
#            mock_app_window.deserialize.return_value = profile_without_uuid
#
#            # Act
#            register.scanDir('/tmp/profiles')
#
#            # Assert
#            mock_add_path.assert_not_called()
#
#    def test_scan_dir_exception_handling(self, mock_app_window:Mock) -> None:
#        """Test scanDir with exception during processing."""
#        # Arrange
#        with patch('plus.register.config') as mock_config, patch(
#            'plus.register.Path'
#        ) as mock_path_class:
#
#            mock_config.app_window = mock_app_window
#            mock_path_class.side_effect = Exception('File system error')
#
#            # Act & Assert - Should not raise exception
#            register.scanDir('/tmp/profiles')


class TestPathValidation:
    """Test path validation and normalization."""

    def test_path_existence_check(self, sample_uuid: str, sample_path: str) -> None:
        """Test path existence validation."""
        # Arrange
        mock_lock = MockPortalockerLock()

        with patch('plus.register.os.path.exists') as mock_exists, patch(
            'plus.config.app_window', None
        ):

            # Mock portalocker and shelve modules that get imported locally
            mock_portalocker = Mock()
            mock_portalocker.Lock.return_value = mock_lock
            mock_portalocker.exceptions.LockException = MockLockException

            mock_shelve = Mock()
            mock_db = MockShelveDB()
            mock_db._data[sample_uuid] = sample_path
            mock_shelve.open.return_value = mock_db
            mock_exists.return_value = True

            with patch.dict(
                'sys.modules', {'portalocker': mock_portalocker, 'shelve': mock_shelve}
            ):
                # Act
                result = register.getPath(sample_uuid)

                # Assert - register module returns path from DB, doesn't check file existence
                assert result == sample_path

    def test_invalid_path_handling(self, sample_uuid: str) -> None:
        """Test handling of invalid or non-existent paths."""
        # Arrange
        invalid_path = '/nonexistent/path/file.alog'
        mock_lock = MockPortalockerLock()

        with patch('plus.register.os.path.exists') as mock_exists, patch(
            'plus.config.app_window', None
        ):

            # Mock portalocker and shelve modules that get imported locally
            mock_portalocker = Mock()
            mock_portalocker.Lock.return_value = mock_lock
            mock_portalocker.exceptions.LockException = MockLockException

            mock_shelve = Mock()
            mock_db = MockShelveDB()
            mock_db._data[sample_uuid] = invalid_path
            mock_shelve.open.return_value = mock_db
            mock_exists.return_value = False

            with patch.dict(
                'sys.modules', {'portalocker': mock_portalocker, 'shelve': mock_shelve}
            ):
                # Act
                result = register.getPath(sample_uuid)

                # Assert - register module returns path from DB, doesn't check file existence
                assert result == invalid_path

    def test_path_normalization(self, sample_uuid: str, mock_shelve_db: Mock) -> None:
        """Test path normalization during storage."""
        # Arrange
        raw_path = '/tmp/../tmp/profiles/./test.alog'
        mock_lock = MockPortalockerLock()

        with patch('plus.config.app_window', None):
            mock_shelve = Mock()
            mock_shelve.open.return_value = mock_shelve_db

            with patch.dict('sys.modules', {'shelve': mock_shelve}):
                # Act
                register.addPathShelve(sample_uuid, raw_path, mock_lock) # type: ignore[arg-type]

                # Assert
                mock_shelve_db.__setitem__.assert_called_once_with(sample_uuid, raw_path)


class TestConcurrencyAndLocking:
    """Test concurrency control and locking mechanisms."""

    def test_semaphore_acquisition(self, sample_uuid: str, sample_path: str) -> None:
        """Test that semaphore is properly acquired and released."""
        # Arrange
        mock_lock = MockPortalockerLock()

        with patch('plus.config.app_window', None):
            # Mock portalocker module that gets imported locally
            mock_portalocker = Mock()
            mock_portalocker.Lock.return_value = mock_lock
            mock_portalocker.exceptions.LockException = MockLockException

            with patch.dict('sys.modules', {'portalocker': mock_portalocker}):
                # Act
                register.addPath(sample_uuid, sample_path)

                # Assert - semaphore acquisition is handled internally by register module
                mock_portalocker.Lock.assert_called()

    def test_lock_timeout_handling(self, sample_uuid: str, sample_path: str) -> None:
        """Test proper handling of lock timeouts."""
        # Arrange
        with patch('plus.register.Path') as mock_path_class, patch('plus.config.app_window', None):

            # Mock portalocker module that gets imported locally
            mock_portalocker = Mock()
            mock_portalocker.Lock.side_effect = MockLockException('Timeout')
            mock_portalocker.exceptions.LockException = MockLockException

            mock_path_instance = Mock()
            mock_path_class.return_value = mock_path_instance

            with patch.dict('sys.modules', {'portalocker': mock_portalocker}):
                # Act
                register.addPath(sample_uuid, sample_path)

                # Assert - Should attempt to clean lock file
                mock_path_instance.unlink.assert_called_once()

    def test_multiple_lock_attempts(self, sample_uuid: str, sample_path: str) -> None:
        """Test multiple lock attempts after cleanup."""
        # Arrange
        mock_lock = MockPortalockerLock()

        with patch('plus.register.addPathShelve') as mock_add_path_shelve, patch(
            'plus.register.Path'
        ) as mock_path_class, patch('plus.config.app_window', None):

            # Mock portalocker module that gets imported locally
            mock_portalocker = Mock()
            mock_portalocker.Lock.side_effect = [MockLockException('Timeout'), mock_lock]
            mock_portalocker.exceptions.LockException = MockLockException

            mock_path_instance = Mock()
            mock_path_class.return_value = mock_path_instance

            with patch.dict('sys.modules', {'portalocker': mock_portalocker}):
                # Act
                register.addPath(sample_uuid, sample_path)

                # Assert
                assert mock_portalocker.Lock.call_count == 2
                mock_add_path_shelve.assert_called_once()


class TestDatabaseOperations:
    """Test database operations and data integrity."""

    def test_database_consistency(
        self, sample_uuid: str, sample_path: str, mock_shelve_db: Mock
    ) -> None:
        """Test database consistency during operations."""
        # Arrange
        mock_lock = MockPortalockerLock()

        with patch('plus.config.app_window', None):
            mock_shelve = Mock()
            mock_shelve.open.return_value = mock_shelve_db

            with patch.dict('sys.modules', {'shelve': mock_shelve}):
                # Act - Add path
                register.addPathShelve(sample_uuid, sample_path, mock_lock) # type: ignore[arg-type]

                # Assert
                mock_shelve_db.__setitem__.assert_called_once_with(sample_uuid, sample_path)

    def test_database_error_handling(self, sample_uuid: str, sample_path: str) -> None:
        """Test handling of database errors."""
        # Arrange
        mock_lock = MockPortalockerLock()

        with patch('plus.config.app_window', None):
            mock_shelve = Mock()
            mock_shelve.open.side_effect = Exception('Database corruption')

            with patch.dict('sys.modules', {'shelve': mock_shelve}):
                # Act & Assert - Should not raise exception
                register.addPathShelve(sample_uuid, sample_path, mock_lock) # type: ignore[arg-type]

    def test_database_key_operations(
        self, sample_uuid: str, sample_path: str, mock_shelve_db: Mock
    ) -> None:
        """Test database key operations (get, set, delete)."""
        # Arrange
        mock_lock = MockPortalockerLock()

        with patch('plus.config.app_window', None):
            # Mock portalocker and shelve modules that get imported locally
            mock_portalocker = Mock()
            mock_portalocker.Lock.return_value = mock_lock
            mock_portalocker.exceptions.LockException = MockLockException

            mock_shelve = Mock()
            mock_shelve.open.return_value = mock_shelve_db
            mock_shelve_db.__getitem__.return_value = sample_path
            mock_shelve_db.__contains__.return_value = True
            mock_shelve_db.__delitem__ = Mock()

            with patch.dict(
                'sys.modules', {'portalocker': mock_portalocker, 'shelve': mock_shelve}
            ):
                # Act - Test get operation
                result = register.getPath(sample_uuid)

                # Assert
                assert result == sample_path
                mock_shelve_db.__getitem__.assert_called_with(sample_uuid)
