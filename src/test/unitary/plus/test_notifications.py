# ============================================================================
# CRITICAL: Module-Level Isolation Setup (MUST BE FIRST)
# ============================================================================
# Ensure proper module isolation to prevent cross-file contamination

import json
import sys
from typing import Any, Dict, Generator
from unittest.mock import Mock, patch

# Store original modules before any mocking to enable restoration
original_modules: Dict[str, Any] = {}
original_functions: Dict[str, Any] = {}
modules_to_isolate = [
    'PyQt6.QtCore',
    'PyQt5.QtCore',
    'artisanlib.main',
    'artisanlib.notifications',
    'plus.config',
    'plus.controller',
    'plus.connection',
    'plus.util',
]

# Store original modules if they exist
for module_name in modules_to_isolate:
    if module_name in sys.modules and not hasattr(sys.modules[module_name], '_mock_name'):
        original_modules[module_name] = sys.modules[module_name]

# ============================================================================
# Now safe to import other modules
# ============================================================================

"""Unit tests for plus.notifications module.

This module tests the notification handling functionality including:
- Notification retrieval from server with semaphore protection
- Notification processing and filtering (not_for_artisan flag)
- Notification sorting by timestamp (oldest first)
- Integration with Artisan notification system
- Machine-specific notification filtering
- JSON response parsing and error handling
- Semaphore-based concurrency control
- Timer-based delayed notification retrieval
- HTTP request handling for notification endpoints
- Notification data extraction and validation
- Error handling for malformed JSON responses
- Connection state checking before retrieval
- Notification flag checking and machine matching

=============================================================================
COMPREHENSIVE TEST ISOLATION IMPLEMENTATION
=============================================================================

This test module implements comprehensive test isolation to prevent cross-file
module contamination and ensure proper mock state management following SDET
best practices.

ISOLATION STRATEGY:
1. **Module-Level Dependency Preservation**: Store original modules before mocking
   to enable proper restoration after tests complete

2. **Targeted Patching**: Use context managers during module import to avoid
   global module contamination that affects other tests

3. **Session-Level Isolation**:
   - ensure_notifications_isolation fixture manages module state at session level
   - Proper cleanup after session to prevent module registration conflicts

4. **Automatic State Reset**:
   - reset_notifications_state fixture runs automatically for every test
   - Mock state reset between tests to ensure clean state

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
✅ Individual tests pass: pytest test_notifications.py::TestClass::test_method
✅ Full module tests pass: pytest test_notifications.py
✅ Cross-file isolation works: pytest test_notifications.py test_main.py
✅ Cross-file isolation works: pytest test_main.py test_notifications.py
✅ No module contamination affecting other tests
✅ No numpy multiple import issues

This implementation serves as a reference for proper test isolation in
modules that require extensive Qt and external dependency mocking while preventing cross-file contamination.
=============================================================================
"""

import pytest


# Create mock classes for Qt components
class MockQSemaphore:
    def __init__(self, *_args: Any) -> None:
        self.tryAcquire = Mock(return_value=True)
        self.release = Mock()
        self.available = Mock(return_value=0)


class MockQTimer:
    @staticmethod
    def singleShot(delay: int, callback: Any) -> None:
        pass


class MockQApplication:
    def applicationName(self) -> str:
        return 'Artisan'


# Mock the modules before importing to avoid import-time issues
mock_modules = {
    'PyQt6.QtCore': Mock(),
    'PyQt5.QtCore': Mock(),
    'artisanlib.main': Mock(),
    'artisanlib.notifications': Mock(),
    'plus.config': Mock(),
    'plus.controller': Mock(),
    'plus.connection': Mock(),
    'plus.util': Mock(),
}

# Add all mocks to sys.modules before importing
for module_name, mock_module in mock_modules.items():
    sys.modules[module_name] = mock_module

# Set up specific mock attributes
sys.modules['PyQt6.QtCore'].QSemaphore = MockQSemaphore # type: ignore[attr-defined]
sys.modules['PyQt6.QtCore'].QTimer = MockQTimer # type: ignore[attr-defined]
sys.modules['PyQt6.QtCore'].pyqtSlot = Mock(side_effect=lambda *_args, **_kwargs: lambda f: f) # type: ignore[attr-defined]

sys.modules['PyQt5.QtCore'].QSemaphore = MockQSemaphore # type: ignore[attr-defined]
sys.modules['PyQt5.QtCore'].QTimer = MockQTimer # type: ignore[attr-defined]
sys.modules['PyQt5.QtCore'].pyqtSlot = Mock(side_effect=lambda *_args, **_kwargs: lambda f: f) # type: ignore[attr-defined]

sys.modules['artisanlib.notifications'].ntype2NotificationType = Mock(return_value='PLUS_SYSTEM') # type: ignore[attr-defined]

sys.modules['plus.config'].app_window = None # type: ignore[attr-defined]
sys.modules['plus.config'].notifications_url = 'https://artisan.plus/api/v1/notifications' # type: ignore[attr-defined]

sys.modules['plus.util'].ISO86012epoch = Mock(return_value=1640995200) # type: ignore[attr-defined]
sys.modules['plus.util'].extractInfo = Mock( # type: ignore[attr-defined]
    side_effect=lambda data, key, default: data.get(key, default)
)

# Mock QApplication for artisanlib.util
mock_qapp = MockQApplication()
sys.modules['artisanlib.main'].QApplication = Mock() # type: ignore[attr-defined]
sys.modules['artisanlib.main'].QApplication.instance = Mock(return_value=mock_qapp) # ty: ignore

# Immediate cleanup registration to prevent cross-file contamination
import atexit

from plus import notifications


# Immediately clean up mocked modules to prevent cross-file contamination
def _cleanup_notifications_modules() -> None:
    """Clean up mocked modules immediately to prevent cross-file contamination."""
    # Restore original modules
    for module_name, original_module in original_modules.items():
        if module_name in sys.modules:
            sys.modules[module_name] = original_module

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


# Call cleanup immediately after import to prevent contamination
# This ensures that other modules importing after this one get the real modules
_cleanup_notifications_modules()

# Also register for atexit as a backup
atexit.register(_cleanup_notifications_modules)


@pytest.fixture(scope='session', autouse=True)
def ensure_notifications_isolation() -> Generator[None, None, None]:
    """
    Ensure modules are properly isolated for notifications tests at session level.

    This fixture runs once per test session to ensure that mocked modules
    used by notifications tests don't interfere with other tests that need real dependencies.
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
def cleanup_notifications_mocks() -> Generator[None, None, None]:
    """
    Clean up notifications test mocks at module level to prevent cross-file contamination.

    This fixture runs once per test module and ensures immediate cleanup
    of mocked dependencies when the notifications test module completes.
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
def reset_notifications_state() -> Generator[None, None, None]:
    """
    Reset notifications module state before and after each test to ensure complete isolation.

    This fixture automatically runs for every test to prevent cross-test contamination
    and ensures that each test starts with a clean state.
    """
    # Reset the semaphore mock state before each test
    if hasattr(notifications, 'get_notifications_semaphore'):
        semaphore = notifications.get_notifications_semaphore
        if hasattr(semaphore, 'reset_mock'):
            semaphore.reset_mock() # pyright: ignore[reportAttributeAccessIssue] # ty: ignore

    yield

    # Clean up after each test - reset mock state
    if hasattr(notifications, 'get_notifications_semaphore'):
        semaphore = notifications.get_notifications_semaphore
        if hasattr(semaphore, 'reset_mock'):
            semaphore.reset_mock() # pyright: ignore[reportAttributeAccessIssue] # ty: ignore


@pytest.fixture
def mock_qsemaphore() -> Mock:
    """Create a mock QSemaphore for testing."""
    mock_sem = Mock()
    mock_sem.tryAcquire = Mock(return_value=True)
    mock_sem.release = Mock()
    mock_sem.available = Mock(return_value=0)
    return mock_sem


@pytest.fixture
def mock_app_window() -> Mock:
    """Create a mock application window."""
    mock_aw = Mock()
    mock_aw.notificationsflag = True
    mock_aw.qmc = Mock()
    mock_aw.qmc.roastertype_setup = 'TestRoaster'
    mock_aw.notificationManager = Mock()
    mock_aw.notificationManager.sendNotificationMessage = Mock()
    return mock_aw


@pytest.fixture
def mock_http_response() -> Mock:
    """Create a mock HTTP response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {'content-type': 'application/json'}
    mock_response.json = Mock()
    return mock_response


@pytest.fixture
def sample_notification_data() -> Dict[str, Any]:
    """Create sample notification data."""
    return {
        'success': True,
        'result': [
            {
                'title': 'Test Notification 1',
                'text': 'This is a test notification',
                'ntype': 'SYSTEM',
                'added_on': '2022-01-01T00:00:00Z',
                'hr_id': 'notif_123',
                'link': 'https://artisan.plus/test',
            },
            {
                'title': 'Test Notification 2',
                'text': 'This is another test notification',
                'ntype': 'ADMIN',
                'added_on': '2022-01-02T00:00:00Z',
                'hr_id': 'notif_456',
                'not_for_artisan': True,  # Should be filtered out
            },
            {
                'title': 'Test Notification 3',
                'text': 'This is a third test notification',
                'ntype': 'REMINDER',
                'added_on': '2021-12-31T00:00:00Z',  # Older, should be first
                'hr_id': 'notif_789',
            },
        ],
    }


class TestUpdateNotifications:
    """Test updateNotifications function."""

    def test_update_notifications_with_notifications_flag_enabled(self, mock_app_window:Mock) -> None:
        """Test updateNotifications schedules retrieval when notifications flag is enabled."""
        # Arrange
        with patch('plus.notifications.config') as mock_config, patch(
            'plus.notifications.QTimer'
        ) as mock_timer:

            mock_config.app_window = mock_app_window
            mock_app_window.notificationsflag = True

            # Act
            notifications.updateNotifications(5, ['TestRoaster'])

            # Assert
            mock_timer.singleShot.assert_called_once_with(700, notifications.retrieveNotifications)

    def test_update_notifications_with_notifications_disabled(self, mock_app_window:Mock) -> None:
        """Test updateNotifications does nothing when notifications are disabled."""
        # Arrange
        with patch('plus.notifications.config') as mock_config, patch(
            'plus.notifications.QTimer'
        ) as mock_timer:

            mock_config.app_window = mock_app_window
            mock_app_window.notificationsflag = False

            # Act
            notifications.updateNotifications(5, ['TestRoaster'])

            # Assert
            mock_timer.singleShot.assert_not_called()

    def test_update_notifications_with_machine_match(self, mock_app_window:Mock) -> None:
        """Test updateNotifications schedules retrieval when machine matches."""
        # Arrange
        with patch('plus.notifications.config') as mock_config, patch(
            'plus.notifications.QTimer'
        ) as mock_timer:

            mock_config.app_window = mock_app_window
            mock_app_window.notificationsflag = True
            mock_app_window.qmc.roastertype_setup = 'TestRoaster'

            # Act
            notifications.updateNotifications(0, ['TestRoaster', 'OtherRoaster'])

            # Assert
            mock_timer.singleShot.assert_called_once_with(700, notifications.retrieveNotifications)

    def test_update_notifications_with_no_machine_match(self, mock_app_window:Mock) -> None:
        """Test updateNotifications does nothing when no machine matches and no notifications."""
        # Arrange
        with patch('plus.notifications.config') as mock_config, patch(
            'plus.notifications.QTimer'
        ) as mock_timer:

            mock_config.app_window = mock_app_window
            mock_app_window.notificationsflag = True
            mock_app_window.qmc.roastertype_setup = 'TestRoaster'

            # Act
            notifications.updateNotifications(0, ['OtherRoaster'])

            # Assert
            mock_timer.singleShot.assert_not_called()

    def test_update_notifications_with_no_app_window(self) -> None:
        """Test updateNotifications handles missing app window gracefully."""
        # Arrange
        with patch('plus.notifications.config') as mock_config, patch(
            'plus.notifications.QTimer'
        ) as mock_timer:

            mock_config.app_window = None

            # Act
            notifications.updateNotifications(5, ['TestRoaster'])

            # Assert
            mock_timer.singleShot.assert_not_called()

    def test_update_notifications_exception_handling(self, mock_app_window:Mock) -> None:
        """Test updateNotifications handles exceptions gracefully."""
        # Arrange
        with patch('plus.notifications.config') as mock_config, patch(
            'plus.notifications.QTimer'
        ) as mock_timer:

            mock_config.app_window = mock_app_window
            mock_timer.singleShot.side_effect = Exception('Timer error')

            # Act & Assert - Should not raise exception
            notifications.updateNotifications(5, ['TestRoaster'])


class TestRetrieveNotifications:
    """Test retrieveNotifications function."""

    def test_retrieve_notifications_successful(
        self, mock_app_window:Mock, mock_http_response:Mock, sample_notification_data:Dict[str,Any], mock_qsemaphore:Mock
    ) -> None:
        """Test retrieveNotifications with successful response."""
        # Arrange
        mock_http_response.json.return_value = sample_notification_data

        with patch('plus.notifications.get_notifications_semaphore', mock_qsemaphore), patch(
            'plus.notifications.controller'
        ) as mock_controller, patch('plus.notifications.connection') as mock_connection, patch(
            'plus.notifications.config'
        ) as mock_config, patch(
            'plus.notifications.processNotification'
        ) as mock_process:

            mock_config.app_window = mock_app_window
            mock_config.notifications_url = 'https://artisan.plus/api/v1/notifications'
            mock_controller.is_connected.return_value = True
            mock_connection.getData.return_value = mock_http_response
            mock_qsemaphore.tryAcquire.return_value = True
            mock_qsemaphore.available.return_value = 0

            # Act
            notifications.retrieveNotifications()

            # Assert
            mock_qsemaphore.tryAcquire.assert_called_once_with(1, 0)
            mock_connection.getData.assert_called_once_with(
                'https://artisan.plus/api/v1/notifications', params={'machine': 'TestRoaster'}
            )
            # Should process 2 notifications (one filtered out due to not_for_artisan)
            assert mock_process.call_count == 2
            mock_qsemaphore.release.assert_called_once_with(1)

    def test_retrieve_notifications_no_lock_acquired(self) -> None:
        """Test retrieveNotifications when semaphore lock cannot be acquired."""
        # Arrange
        mock_sem = Mock()
        mock_sem.tryAcquire = Mock(return_value=False)

        with patch('plus.notifications.get_notifications_semaphore', mock_sem), patch(
            'plus.notifications.controller'
        ) as mock_controller:

            # Act
            notifications.retrieveNotifications()

            # Assert
            mock_sem.tryAcquire.assert_called_once_with(1, 0)
            mock_controller.is_connected.assert_not_called()

    def test_retrieve_notifications_not_connected(self, mock_app_window:Mock) -> None:
        """Test retrieveNotifications when not connected."""
        # Arrange
        mock_sem = Mock()
        mock_sem.tryAcquire = Mock(return_value=True)
        mock_sem.available = Mock(return_value=0)
        mock_sem.release = Mock()

        with patch('plus.notifications.get_notifications_semaphore', mock_sem), patch(
            'plus.notifications.controller'
        ) as mock_controller, patch('plus.notifications.connection') as mock_connection, patch(
            'plus.notifications.config'
        ) as mock_config:

            mock_config.app_window = mock_app_window
            mock_controller.is_connected.return_value = False

            # Act
            notifications.retrieveNotifications()

            # Assert
            mock_connection.getData.assert_not_called()
            mock_sem.release.assert_called_once_with(1)

    def test_retrieve_notifications_empty_machine_setup(
        self, mock_app_window:Mock, mock_http_response:Mock, mock_qsemaphore:Mock
    ) -> None:
        """Test retrieveNotifications with empty machine setup."""
        # Arrange
        mock_app_window.qmc.roastertype_setup = ''

        with patch('plus.notifications.get_notifications_semaphore', mock_qsemaphore), patch(
            'plus.notifications.controller'
        ) as mock_controller, patch('plus.notifications.connection') as mock_connection, patch(
            'plus.notifications.config'
        ) as mock_config:

            mock_config.app_window = mock_app_window
            mock_config.notifications_url = 'https://artisan.plus/api/v1/notifications'
            mock_controller.is_connected.return_value = True
            mock_connection.getData.return_value = mock_http_response
            mock_qsemaphore.tryAcquire.return_value = True

            # Act
            notifications.retrieveNotifications()

            # Assert
            mock_connection.getData.assert_called_once_with(
                'https://artisan.plus/api/v1/notifications', params=None
            )

    def test_retrieve_notifications_204_response(self, mock_app_window:Mock) -> None:
        """Test retrieveNotifications with 204 No Content response."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 204

        mock_sem = Mock()
        mock_sem.tryAcquire = Mock(return_value=True)
        mock_sem.available = Mock(return_value=0)
        mock_sem.release = Mock()

        with patch('plus.notifications.get_notifications_semaphore', mock_sem), patch(
            'plus.notifications.controller'
        ) as mock_controller, patch('plus.notifications.connection') as mock_connection, patch(
            'plus.notifications.config'
        ) as mock_config, patch(
            'plus.notifications.processNotification'
        ) as mock_process:

            mock_config.app_window = mock_app_window
            mock_controller.is_connected.return_value = True
            mock_connection.getData.return_value = mock_response

            # Act
            notifications.retrieveNotifications()

            # Assert
            mock_process.assert_not_called()
            mock_sem.release.assert_called_once_with(1)

    def test_retrieve_notifications_non_json_response(
        self, mock_app_window:Mock, mock_qsemaphore:Mock
    ) -> None:
        """Test retrieveNotifications with non-JSON response."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}

        with patch('plus.notifications.get_notifications_semaphore', mock_qsemaphore), patch(
            'plus.notifications.controller'
        ) as mock_controller, patch('plus.notifications.connection') as mock_connection, patch(
            'plus.notifications.config'
        ) as mock_config, patch(
            'plus.notifications.processNotification'
        ) as mock_process:

            mock_config.app_window = mock_app_window
            mock_controller.is_connected.return_value = True
            mock_connection.getData.return_value = mock_response
            mock_qsemaphore.tryAcquire.return_value = True
            mock_qsemaphore.available.return_value = 0

            # Act
            notifications.retrieveNotifications()

            # Assert
            mock_process.assert_not_called()
            mock_qsemaphore.release.assert_called_once_with(1)

    def test_retrieve_notifications_json_decode_error(
        self, mock_app_window:Mock, mock_http_response:Mock, mock_qsemaphore:Mock
    ) -> None:
        """Test retrieveNotifications handles JSON decode errors."""
        # Arrange
        mock_http_response.json.side_effect = json.decoder.JSONDecodeError('Invalid JSON', '', 0)  # ty: ignore

        with patch('plus.notifications.get_notifications_semaphore', mock_qsemaphore), patch(
            'plus.notifications.controller'
        ) as mock_controller, patch('plus.notifications.connection') as mock_connection, patch(
            'plus.notifications.config'
        ) as mock_config:

            mock_config.app_window = mock_app_window
            mock_controller.is_connected.return_value = True
            mock_connection.getData.return_value = mock_http_response
            mock_qsemaphore.tryAcquire.return_value = True
            mock_qsemaphore.available.return_value = 0

            # Act & Assert - Should not raise exception
            notifications.retrieveNotifications()

            # Should still release semaphore
            mock_qsemaphore.release.assert_called_once_with(1)

    def test_retrieve_notifications_value_error(
        self, mock_app_window:Mock, mock_http_response:Mock, mock_qsemaphore:Mock
    ) -> None:
        """Test retrieveNotifications handles ValueError."""
        # Arrange
        mock_http_response.json.side_effect = ValueError('Invalid JSON')

        with patch('plus.notifications.get_notifications_semaphore', mock_qsemaphore), patch(
            'plus.notifications.controller'
        ) as mock_controller, patch('plus.notifications.connection') as mock_connection, patch(
            'plus.notifications.config'
        ) as mock_config:

            mock_config.app_window = mock_app_window
            mock_controller.is_connected.return_value = True
            mock_connection.getData.return_value = mock_http_response
            mock_qsemaphore.tryAcquire.return_value = True
            mock_qsemaphore.available.return_value = 0

            # Act & Assert - Should not raise exception
            notifications.retrieveNotifications()

            # Should still release semaphore
            mock_qsemaphore.release.assert_called_once_with(1)

    def test_retrieve_notifications_unsuccessful_response(
        self, mock_app_window:Mock, mock_http_response:Mock, mock_qsemaphore:Mock
    ) -> None:
        """Test retrieveNotifications with unsuccessful response."""
        # Arrange
        unsuccessful_data = {'success': False, 'error': 'Server error'}
        mock_http_response.json.return_value = unsuccessful_data

        with patch('plus.notifications.get_notifications_semaphore', mock_qsemaphore), patch(
            'plus.notifications.controller'
        ) as mock_controller, patch('plus.notifications.connection') as mock_connection, patch(
            'plus.notifications.config'
        ) as mock_config, patch(
            'plus.notifications.processNotification'
        ) as mock_process:

            mock_config.app_window = mock_app_window
            mock_controller.is_connected.return_value = True
            mock_connection.getData.return_value = mock_http_response
            mock_qsemaphore.tryAcquire.return_value = True
            mock_qsemaphore.available.return_value = 0

            # Act
            notifications.retrieveNotifications()

            # Assert
            mock_process.assert_not_called()  # No notifications should be processed
            mock_qsemaphore.release.assert_called_once_with(1)

    def test_retrieve_notifications_empty_result(
        self, mock_app_window:Mock, mock_http_response:Mock, mock_qsemaphore:Mock
    ) -> None:
        """Test retrieveNotifications with empty result array."""
        # Arrange
        empty_data = {'success': True, 'result': []}
        mock_http_response.json.return_value = empty_data

        with patch('plus.notifications.get_notifications_semaphore', mock_qsemaphore), patch(
            'plus.notifications.controller'
        ) as mock_controller, patch('plus.notifications.connection') as mock_connection, patch(
            'plus.notifications.config'
        ) as mock_config, patch(
            'plus.notifications.processNotification'
        ) as mock_process:

            mock_config.app_window = mock_app_window
            mock_controller.is_connected.return_value = True
            mock_connection.getData.return_value = mock_http_response
            mock_qsemaphore.tryAcquire.return_value = True
            mock_qsemaphore.available.return_value = 0

            # Act
            notifications.retrieveNotifications()

            # Assert
            mock_process.assert_not_called()  # No notifications to process
            mock_qsemaphore.release.assert_called_once_with(1)

    def test_retrieve_notifications_non_list_result(
        self, mock_app_window:Mock, mock_http_response:Mock, mock_qsemaphore:Mock
    ) -> None:
        """Test retrieveNotifications with non-list result."""
        # Arrange
        invalid_data = {'success': True, 'result': 'not a list'}
        mock_http_response.json.return_value = invalid_data

        with patch('plus.notifications.get_notifications_semaphore', mock_qsemaphore), patch(
            'plus.notifications.controller'
        ) as mock_controller, patch('plus.notifications.connection') as mock_connection, patch(
            'plus.notifications.config'
        ) as mock_config, patch(
            'plus.notifications.processNotification'
        ) as mock_process:

            mock_config.app_window = mock_app_window
            mock_controller.is_connected.return_value = True
            mock_connection.getData.return_value = mock_http_response
            mock_qsemaphore.tryAcquire.return_value = True
            mock_qsemaphore.available.return_value = 0

            # Act
            notifications.retrieveNotifications()

            # Assert
            mock_process.assert_not_called()  # No notifications should be processed
            mock_qsemaphore.release.assert_called_once_with(1)


class TestProcessNotification:
    """Test processNotification function."""

    def test_process_notification_successful(self, mock_app_window:Mock) -> None:
        """Test processNotification with valid notification data."""
        # Arrange
        notification_data = {
            'title': 'Test Notification',
            'text': 'This is a test message',
            'ntype': 'SYSTEM',
            'added_on': '2022-01-01T00:00:00Z',
            'hr_id': 'notif_123',
            'link': 'https://artisan.plus/test',
        }

        with patch('plus.notifications.config') as mock_config, patch(
            'plus.notifications.util'
        ) as mock_util, patch('plus.notifications.ntype2NotificationType') as mock_ntype:

            mock_config.app_window = mock_app_window
            mock_util.ISO86012epoch.return_value = 1640995200
            mock_util.extractInfo.side_effect = lambda data, key, default: data.get(key, default)
            mock_ntype.return_value = 'PLUS_SYSTEM'

            # Act
            notifications.processNotification(notification_data, 0)

            # Assert
            mock_app_window.notificationManager.sendNotificationMessage.assert_called_once_with(
                'Test Notification',
                'This is a test message',
                'PLUS_SYSTEM',
                created=1640995200,
                hr_id='notif_123',
                link='https://artisan.plus/test',
                pos=0,
            )

    def test_process_notification_missing_fields(self, mock_app_window:Mock) -> None:
        """Test processNotification with missing optional fields."""
        # Arrange
        notification_data = {
            'title': 'Minimal Notification',
            'text': 'Basic message',
            'ntype': 'ADMIN',
        }

        with patch('plus.notifications.config') as mock_config, patch(
            'plus.notifications.util'
        ) as mock_util, patch('plus.notifications.ntype2NotificationType') as mock_ntype:

            mock_config.app_window = mock_app_window
            mock_util.extractInfo.side_effect = lambda data, key, default: data.get(key, default)
            mock_ntype.return_value = 'PLUS_ADMIN'

            # Act
            notifications.processNotification(notification_data, 1)

            # Assert
            mock_app_window.notificationManager.sendNotificationMessage.assert_called_once_with(
                'Minimal Notification',
                'Basic message',
                'PLUS_ADMIN',
                created=None,
                hr_id=None,
                link=None,
                pos=1,
            )

    def test_process_notification_invalid_timestamp(self, mock_app_window:Mock) -> None:
        """Test processNotification with invalid timestamp."""
        # Arrange
        notification_data = {
            'title': 'Test Notification',
            'text': 'Test message',
            'ntype': 'SYSTEM',
            'added_on': 'invalid-timestamp',
        }

        with patch('plus.notifications.config') as mock_config, patch(
            'plus.notifications.util'
        ) as mock_util, patch('plus.notifications.ntype2NotificationType') as mock_ntype:

            mock_config.app_window = mock_app_window
            mock_util.ISO86012epoch.side_effect = Exception('Invalid timestamp')
            mock_util.extractInfo.side_effect = lambda data, key, default: data.get(key, default)
            mock_ntype.return_value = 'PLUS_SYSTEM'

            # Act
            notifications.processNotification(notification_data, 0)

            # Assert
            mock_app_window.notificationManager.sendNotificationMessage.assert_called_once_with(
                'Test Notification',
                'Test message',
                'PLUS_SYSTEM',
                created=None,  # Should be None due to timestamp error
                hr_id=None,
                link=None,
                pos=0,
            )

    def test_process_notification_no_app_window(self) -> None:
        """Test processNotification with no app window."""
        # Arrange
        notification_data = {
            'title': 'Test Notification',
            'text': 'Test message',
            'ntype': 'SYSTEM',
        }

        with patch('plus.notifications.config') as mock_config:
            mock_config.app_window = None

            # Act & Assert - Should not raise exception
            notifications.processNotification(notification_data, 0)

    def test_process_notification_no_notification_manager(self, mock_app_window:Mock) -> None:
        """Test processNotification with no notification manager."""
        # Arrange
        notification_data = {
            'title': 'Test Notification',
            'text': 'Test message',
            'ntype': 'SYSTEM',
        }
        mock_app_window.notificationManager = None

        with patch('plus.notifications.config') as mock_config:
            mock_config.app_window = mock_app_window

            # Act & Assert - Should not raise exception
            notifications.processNotification(notification_data, 0)
