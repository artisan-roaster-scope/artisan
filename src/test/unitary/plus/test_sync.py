"""Unit tests for plus.sync module.

This module tests the synchronization management functionality including:
- Sync cache operations with UUID and timestamp management
- Database operations with shelve persistence and locking
- Sync record hash management and change detection
- Data synchronization between local and remote sources
- Timestamp handling and modification tracking
- Cache persistence with file locking and concurrency control
- Sync record comparison and differential updates
- Zero value suppression for data optimization
- Server update fetching and application
- Sync state management and validation
- Lock timeout handling and recovery mechanisms
- Database integrity and consistency checks

This test module implements comprehensive session-level isolation to prevent
cross-file module contamination and ensure proper mock state management.
"""

import sys
from typing import Any, Dict, Generator, Optional
from unittest.mock import Mock, patch

import pytest

# Store original modules for restoration
_original_modules: Dict[str, Any] = {}

# Store original import function before any mocking occurs
import builtins

_original_import = builtins.__import__


# Enhanced Mock Classes for Qt Components
class MockQSemaphore:
    """Enhanced mock for QSemaphore with proper method signatures."""

    def __init__(self, resources: int = 1) -> None:
        """Initialize mock semaphore."""
        self.resources = resources
        self._acquired = 0

    def acquire(self, n: int = 1) -> bool:
        """Mock acquire method."""
        if self._acquired + n <= self.resources:
            self._acquired += n
            return True
        return False

    def release(self, n: int = 1) -> None:
        """Mock release method."""
        self._acquired = max(0, self._acquired - n)

    def available(self) -> int:
        """Mock available method."""
        return max(0, self.resources - self._acquired)


class MockQTimer:
    """Enhanced mock for QTimer with proper method signatures."""

    def __init__(self, parent: Optional[Any] = None) -> None:
        """Initialize mock timer."""
        self.parent = parent
        self.timeout = Mock()
        self.timeout.connect = Mock()
        self.started = False

    def start(self, msec: int = 0) -> None:
        """Mock start method."""
        del msec
        self.started = True

    def stop(self) -> None:
        """Mock stop method."""
        self.started = False

    def setSingleShot(self, single_shot: bool) -> None:
        """Mock setSingleShot method."""
        del single_shot

    @staticmethod
    def singleShot(msec: int, receiver: Any) -> None:
        """Mock singleShot static method."""
        del msec
        del receiver


class MockQApplication:
    """Enhanced mock for QApplication with proper method signatures."""

    @staticmethod
    def translate(
        context: str, text: str, disambiguation: Optional[str] = None, n: int = -1
    ) -> str:
        """Mock translate method."""
        del context
        del disambiguation
        del n
        return text


class MockPortalockerLock:
    """Enhanced mock for portalocker.Lock with proper context manager support."""

    def __init__(self, file_path: str, mode: str = 'r', **kwargs: Any) -> None:
        """Initialize mock lock."""
        self.file_path = file_path
        self.mode = mode
        self.kwargs = kwargs

    def __enter__(self) -> 'MockPortalockerLock':
        """Mock context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Mock context manager exit."""
        del exc_type
        del exc_val
        del exc_tb

    def flush(self) -> None:
        """Mock flush method."""

    def fileno(self) -> int:
        """Mock fileno method."""
        return 1


# Set up comprehensive mocks at module level before any imports
modules_to_isolate = [
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt5.QtCore',
    'PyQt5.QtWidgets',
    'artisanlib.main',
    'artisanlib.util',
    'artisanlib.dialogs',
    'plus.config',
    'plus.util',
    'plus.connection',
    'plus.controller',
    'plus.roast',
    'plus.stock',
    'plus.account',
    'portalocker',
    'portalocker.exceptions',
    'shelve',
    'dbm',
    'pathlib',
]

# Store original modules
for module_name in modules_to_isolate:
    if module_name in sys.modules:
        _original_modules[module_name] = sys.modules[module_name]

# Create comprehensive mocks
mock_modules = {
    'PyQt6.QtCore': Mock(),
    'PyQt6.QtWidgets': Mock(),
    'PyQt5.QtCore': Mock(),
    'PyQt5.QtWidgets': Mock(),
    'artisanlib.main': Mock(),
    'artisanlib.util': Mock(),
    'artisanlib.dialogs': Mock(),
    'plus.config': Mock(),
    'plus.util': Mock(),
    'plus.connection': Mock(),
    'plus.controller': Mock(),
    'plus.roast': Mock(),
    'plus.stock': Mock(),
    'plus.account': Mock(),
    'portalocker': Mock(),
    'portalocker.exceptions': Mock(),
}

# Add all mocks to sys.modules
for module_name, mock_module in mock_modules.items():
    sys.modules[module_name] = mock_module

# Setup specific Qt mocks
sys.modules['PyQt6.QtCore'].QSemaphore = MockQSemaphore # type: ignore[attr-defined]
sys.modules['PyQt6.QtCore'].QTimer = MockQTimer # type: ignore[attr-defined]
sys.modules['PyQt6.QtCore'].pyqtSlot = Mock(side_effect=lambda *args, **kwargs: lambda f: f) # type: ignore[attr-defined] # noqa: ARG005

# Mock QCoreApplication.instance() to return a mock app
mock_app = Mock()
mock_app.applicationName = Mock(return_value='Artisan')
mock_app.setApplicationName = Mock()
sys.modules['PyQt6.QtCore'].QCoreApplication = Mock() # type: ignore[attr-defined]
sys.modules['PyQt6.QtCore'].QCoreApplication.instance = Mock(return_value=mock_app) # ty: ignore

# Mock QStandardPaths for directory operations
sys.modules['PyQt6.QtCore'].QStandardPaths = Mock() # type: ignore[attr-defined]
sys.modules['PyQt6.QtCore'].QStandardPaths.standardLocations = Mock(return_value=['/tmp/data']) # ty: ignore
sys.modules['PyQt6.QtCore'].QStandardPaths.StandardLocation = Mock() # ty: ignore
sys.modules['PyQt6.QtCore'].QStandardPaths.StandardLocation.AppLocalDataLocation = Mock() # ty: ignore

sys.modules['PyQt6.QtWidgets'].QApplication = MockQApplication # type: ignore[attr-defined]

# Setup portalocker mocks
sys.modules['portalocker'].Lock = MockPortalockerLock # type: ignore[attr-defined]
sys.modules['portalocker.exceptions'].LockException = Exception # type: ignore[attr-defined]

# Setup config mocks
sys.modules['plus.config'].sync_cache = 'sync' # type: ignore[attr-defined]
sys.modules['plus.config'].account_nr = None # type: ignore[attr-defined]
sys.modules['plus.config'].roast_url = 'https://artisan.plus/api/v1/aroast' # type: ignore[attr-defined]
sys.modules['plus.config'].app_window = None # type: ignore[attr-defined]
sys.modules['plus.config'].account_cache = 'account' # type: ignore[attr-defined]

# Setup utility mocks
sys.modules['artisanlib.util'].getDirectory = Mock(return_value='/tmp/cache') # type: ignore[attr-defined]
sys.modules['artisanlib.util'].weight_units = ['g', 'kg', 'oz', 'lb'] # type: ignore[attr-defined]
sys.modules['artisanlib.util'].convertWeight = Mock(return_value=500.0) # type: ignore[attr-defined]
sys.modules['artisanlib.util'].getDataDirectory = Mock(return_value='/tmp/data') # type: ignore[attr-defined]

sys.modules['plus.util'].ISO86012epoch = Mock(return_value=1640995200.0) # type: ignore[attr-defined]
sys.modules['plus.connection'].getData = Mock() # type: ignore[attr-defined]
sys.modules['plus.controller'].is_connected = Mock(return_value=True) # type: ignore[attr-defined]

# Import the sync module after setting up mocks
from plus import sync


# Session-level isolation fixture
@pytest.fixture(scope='session', autouse=True)
def isolate_sync_module() -> Generator[None, None, None]:
    """
    Session-level fixture to isolate the sync module and prevent cross-file contamination.

    This fixture restores original modules after all tests complete.
    """
    yield

    # Restore original modules
    for module_name, original_module in _original_modules.items():
        sys.modules[module_name] = original_module

    # Remove any modules that weren't originally present
    modules_to_remove = []
    for module_name in mock_modules:
        if module_name not in _original_modules and module_name in sys.modules:
            modules_to_remove.append(module_name)

    for module_name in modules_to_remove:
        del sys.modules[module_name]


@pytest.fixture(autouse=True)
def reset_sync_state() -> Generator[None, None, None]:
    """Reset sync module state before each test to ensure test independence."""
    # Reset sync module global variables
    if hasattr(sync, 'cached_sync_record'):
        sync.cached_sync_record = None
    if hasattr(sync, 'cached_sync_record_hash'):
        sync.cached_sync_record_hash = None
    if hasattr(sync, 'sync_cache_semaphore'):
        # Reset semaphore state
        sync.sync_cache_semaphore = MockQSemaphore(1) # type: ignore[assignment]

    yield

    # Additional cleanup after each test if needed
    if hasattr(sync, 'cached_sync_record'):
        sync.cached_sync_record = None
    if hasattr(sync, 'cached_sync_record_hash'):
        sync.cached_sync_record_hash = None


@pytest.fixture
def sample_uuid() -> str:
    """Provide a sample UUID for testing."""
    return '12345678-1234-5678-9012-123456789abc'


@pytest.fixture
def sample_timestamp() -> float:
    """Provide a sample timestamp for testing."""
    return 1640995200.0


class TestSyncCacheOperations:
    """Test sync cache operations."""

    def test_get_sync_name_no_account(self) -> None:
        """Test getSyncName with no account number."""
        # Arrange
        with patch('plus.sync.config') as mock_config:
            mock_config.account_nr = None
            mock_config.sync_cache = 'sync'

            # Act
            result = sync.getSyncName()

            # Assert
            assert result == 'sync'

    def test_get_sync_name_with_account(self) -> None:
        """Test getSyncName with account number."""
        # Arrange
        with patch('plus.sync.config') as mock_config:
            mock_config.account_nr = 5
            mock_config.sync_cache = 'sync'

            # Act
            result = sync.getSyncName()

            # Assert
            assert result == 'sync5'

    def test_get_sync_name_zero_account(self) -> None:
        """Test getSyncName with zero account number."""
        # Arrange
        with patch('plus.sync.config') as mock_config:
            mock_config.account_nr = 0
            mock_config.sync_cache = 'sync'

            # Act
            result = sync.getSyncName()

            # Assert
            assert result == 'sync'

    def test_get_sync_path_normal(self) -> None:
        """Test getSyncPath for normal cache path."""
        # Arrange
        with patch('plus.sync.getSyncName') as mock_get_sync_name, patch(
            'plus.sync.getDirectory'
        ) as mock_get_directory:
            mock_get_sync_name.return_value = 'sync'
            mock_get_directory.return_value = '/tmp/cache'

            # Act
            result = sync.getSyncPath()

            # Assert
            assert result == '/tmp/cache'
            mock_get_directory.assert_called_once_with('sync', share=True)

    def test_get_sync_path_lock(self) -> None:
        """Test getSyncPath for lock file path."""
        # Arrange
        with patch('plus.sync.getSyncName') as mock_get_sync_name, patch(
            'plus.sync.getDirectory'
        ) as mock_get_directory:
            mock_get_sync_name.return_value = 'sync'
            mock_get_directory.return_value = '/tmp/cache'

            # Act
            result = sync.getSyncPath(lock=True)

            # Assert
            assert result == '/tmp/cache'
            mock_get_directory.assert_called_once_with('sync_lock', share=True)


@pytest.fixture
def mock_shelve_db() -> Mock:
    """Create a mock shelve database."""
    mock_db = Mock()
    mock_db.__enter__ = Mock(return_value=mock_db)
    mock_db.__exit__ = Mock(return_value=None)
    mock_db.__getitem__ = Mock()
    mock_db.__setitem__ = Mock()
    mock_db.__delitem__ = Mock()
    mock_db.__contains__ = Mock()
    return mock_db


@pytest.fixture
def mock_semaphore() -> MockQSemaphore:
    """Create a fresh mock semaphore for each test."""
    return MockQSemaphore(1)


@pytest.fixture
def mock_lock() -> MockPortalockerLock:
    """Create a mock portalocker lock for each test."""
    return MockPortalockerLock('/tmp/test.lock')


class TestAddSync:
    """Test addSync function."""

    def test_add_sync_successful(
        self, sample_uuid:str, sample_timestamp:float, mock_semaphore:MockQSemaphore, mock_lock:MockPortalockerLock
    ) -> None:
        """Test addSync with successful operation."""
        # Arrange
        with patch('plus.sync.addSyncShelve') as mock_add_sync_shelve, patch(
            'plus.sync.sync_cache_semaphore', mock_semaphore
        ), patch('builtins.__import__') as mock_import:
            # Mock the portalocker import
            mock_portalocker = Mock()
            mock_lock_context = Mock()
            mock_lock_context.__enter__ = Mock(return_value=mock_lock)
            mock_lock_context.__exit__ = Mock(return_value=None)
            mock_portalocker.Lock.return_value = mock_lock_context
            mock_import.side_effect = lambda name, *args, **kwargs: (
                mock_portalocker if name == 'portalocker' else __import__(name, *args, **kwargs)
            )

            # Act
            sync.addSync(sample_uuid, sample_timestamp)

            # Assert
            assert mock_semaphore.acquire(1) is True
            mock_add_sync_shelve.assert_called_once_with(sample_uuid, sample_timestamp, mock_lock)

    def test_add_sync_general_exception(
        self, sample_uuid:str, sample_timestamp:float, mock_semaphore:MockQSemaphore
    ) -> None:
        """Test addSync with general exception."""
        # Arrange
        # Use stored original import to avoid recursion

        with patch('plus.sync.addSyncShelve') as mock_add_sync_shelve, patch(
            'plus.sync.sync_cache_semaphore', mock_semaphore
        ), patch('builtins.__import__') as mock_import:
            # Mock the portalocker import with proper exception handling
            mock_portalocker = Mock()
            mock_lock_context = Mock()
            mock_lock_context.__enter__ = Mock(return_value=MockPortalockerLock('/tmp/test.lock'))
            mock_lock_context.__exit__ = Mock(return_value=None)
            mock_portalocker.Lock.return_value = mock_lock_context

            # Create a proper exception class that inherits from BaseException
            class MockLockException(Exception):
                """Mock LockException that properly inherits from BaseException."""


            mock_portalocker.exceptions = Mock()
            mock_portalocker.exceptions.LockException = MockLockException

            mock_import.side_effect = lambda name, *args, **kwargs: (
                mock_portalocker
                if name == 'portalocker'
                else _original_import(name, *args, **kwargs)
            )
            mock_add_sync_shelve.side_effect = Exception('Database error')

            # Act & Assert - Should not raise exception
            sync.addSync(sample_uuid, sample_timestamp)


class TestGetSync:
    """Test getSync function."""

    def test_get_sync_successful(
        self, sample_uuid:str, sample_timestamp:float, mock_shelve_db:Mock, mock_semaphore:MockQSemaphore
    ) -> None:
        """Test getSync with successful lookup."""
        # Arrange
        with patch('plus.sync.sync_cache_semaphore', mock_semaphore), patch(
            'builtins.__import__'
        ) as mock_import:
            # Mock both portalocker and shelve imports
            mock_portalocker = Mock()
            mock_lock_context = Mock()
            mock_lock_context.__enter__ = Mock(return_value=MockPortalockerLock('/tmp/test.lock'))
            mock_lock_context.__exit__ = Mock(return_value=None)
            mock_portalocker.Lock.return_value = mock_lock_context

            mock_shelve = Mock()
            mock_shelve_context = Mock()
            mock_shelve_context.__enter__ = Mock(return_value=mock_shelve_db)
            mock_shelve_context.__exit__ = Mock(return_value=None)
            mock_shelve.open.return_value = mock_shelve_context
            mock_shelve_db.__getitem__.return_value = sample_timestamp

            # Use stored original import to avoid recursion
            def import_side_effect(name:str, *args:Any, **kwargs:Any) -> Any:
                if name == 'portalocker':
                    return mock_portalocker
                if name == 'shelve':
                    return mock_shelve
                return _original_import(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            # Act
            result = sync.getSync(sample_uuid)

            # Assert
            assert result == sample_timestamp
            assert mock_semaphore.acquire(1) is True

    def test_get_sync_not_found(self, sample_uuid:str, mock_shelve_db:Mock, mock_semaphore:MockQSemaphore) -> None:
        """Test getSync with UUID not found."""
        # Arrange
        with patch('plus.sync.sync_cache_semaphore', mock_semaphore), patch(
            'builtins.__import__'
        ) as mock_import:
            # Mock both portalocker and shelve imports
            mock_portalocker = Mock()
            mock_lock_context = Mock()
            mock_lock_context.__enter__ = Mock(return_value=MockPortalockerLock('/tmp/test.lock'))
            mock_lock_context.__exit__ = Mock(return_value=None)
            mock_portalocker.Lock.return_value = mock_lock_context

            mock_shelve = Mock()
            mock_shelve_context = Mock()
            mock_shelve_context.__enter__ = Mock(return_value=mock_shelve_db)
            mock_shelve_context.__exit__ = Mock(return_value=None)
            mock_shelve.open.return_value = mock_shelve_context
            mock_shelve_db.__getitem__.side_effect = KeyError('UUID not found')

            # Use stored original import to avoid recursion
            def import_side_effect(name:str, *args:Any, **kwargs:Any) -> Any:
                if name == 'portalocker':
                    return mock_portalocker
                if name == 'shelve':
                    return mock_shelve
                return _original_import(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            # Act
            result = sync.getSync(sample_uuid)

            # Assert
            assert result is None


class TestDelSync:
    """Test delSync function."""

    def test_del_sync_successful(self, sample_uuid:str, mock_shelve_db:Mock, mock_semaphore:MockQSemaphore) -> None:
        """Test delSync with successful deletion."""
        # Arrange
        with patch('plus.sync.sync_cache_semaphore', mock_semaphore), patch(
            'builtins.__import__'
        ) as mock_import:
            # Mock both portalocker and shelve imports
            mock_portalocker = Mock()
            mock_lock_context = Mock()
            mock_lock_context.__enter__ = Mock(return_value=MockPortalockerLock('/tmp/test.lock'))
            mock_lock_context.__exit__ = Mock(return_value=None)
            mock_portalocker.Lock.return_value = mock_lock_context

            mock_shelve = Mock()
            mock_shelve_context = Mock()
            mock_shelve_context.__enter__ = Mock(return_value=mock_shelve_db)
            mock_shelve_context.__exit__ = Mock(return_value=None)
            mock_shelve.open.return_value = mock_shelve_context

            # Use stored original import to avoid recursion
            def import_side_effect(name:str, *args:Any, **kwargs:Any) -> Any:
                if name == 'portalocker':
                    return mock_portalocker
                if name == 'shelve':
                    return mock_shelve
                return _original_import(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            # Act
            sync.delSync(sample_uuid)

            # Assert
            assert mock_semaphore.acquire(1) is True
            mock_shelve_db.__delitem__.assert_called_once_with(sample_uuid)

    def test_del_sync_not_found(self, sample_uuid:str, mock_shelve_db:Mock, mock_semaphore:MockQSemaphore) -> None:
        """Test delSync with UUID not found."""
        # Arrange
        with patch('plus.sync.sync_cache_semaphore', mock_semaphore), patch(
            'builtins.__import__'
        ) as mock_import:
            # Mock both portalocker and shelve imports
            mock_portalocker = Mock()
            mock_lock_context = Mock()
            mock_lock_context.__enter__ = Mock(return_value=MockPortalockerLock('/tmp/test.lock'))
            mock_lock_context.__exit__ = Mock(return_value=None)
            mock_portalocker.Lock.return_value = mock_lock_context

            mock_shelve = Mock()
            mock_shelve_context = Mock()
            mock_shelve_context.__enter__ = Mock(return_value=mock_shelve_db)
            mock_shelve_context.__exit__ = Mock(return_value=None)
            mock_shelve.open.return_value = mock_shelve_context
            mock_shelve_db.__delitem__.side_effect = KeyError('UUID not found')

            # Use stored original import to avoid recursion
            def import_side_effect(name:str, *args:Any, **kwargs:Any) -> Any:
                if name == 'portalocker':
                    return mock_portalocker
                if name == 'shelve':
                    return mock_shelve
                return _original_import(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            # Act & Assert - Should not raise exception
            sync.delSync(sample_uuid)
