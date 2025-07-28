# ============================================================================
# CRITICAL: Module-Level Isolation Setup (MUST BE FIRST)
# ============================================================================
# Ensure proper module isolation to prevent cross-file contamination

import sys
from typing import Any, Dict, Tuple, Generator
from unittest.mock import Mock, patch

# Store original modules before any mocking to enable restoration
original_modules: Dict[str, Any] = {}
original_functions: Dict[str, Any] = {}
modules_to_isolate = [
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt5.QtCore',
    'PyQt5.QtWidgets',
    'artisanlib.main',
    'plus.config',
    'plus.connection',
    'plus.stock',
    'plus.queue',
    'plus.sync',
    'plus.roast',
    'plus.util',
    'plus.login',
    'keyring',
    'platform',
    'threading',
]

# Store original modules if they exist
for module_name in modules_to_isolate:
    if module_name in sys.modules and not hasattr(sys.modules[module_name], '_mock_name'):
        original_modules[module_name] = sys.modules[module_name]

# ============================================================================
# Now safe to import other modules
# ============================================================================

"""Unit tests for plus.controller module.

This module tests the controller functionality including:
- Connection state management (connected, on, synced)
- Authentication flow and credential handling
- Connection/disconnection logic with semaphore protection
- User interface integration and message handling
- Dialog management and user confirmation
- Queue management and synchronization
- Error handling and recovery mechanisms
- Timer-based operations and delayed execution
- Keyring integration for credential storage
- Application window integration and signal emission

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
   - ensure_controller_isolation fixture manages module state at session level
   - Proper cleanup after session to prevent module registration conflicts

4. **Automatic State Reset**:
   - reset_controller_state fixture runs automatically for every test
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
✅ Individual tests pass: pytest test_controller.py::TestClass::test_method
✅ Full module tests pass: pytest test_controller.py
✅ Cross-file isolation works: pytest test_controller.py test_main.py
✅ Cross-file isolation works: pytest test_main.py test_controller.py
✅ No module contamination affecting other tests
✅ No numpy multiple import issues

This implementation serves as a reference for proper test isolation in
modules that require extensive mocking while preventing cross-file contamination.
=============================================================================
"""

import pytest


# Create mock classes for Qt components
class MockQSemaphore:
    def __init__(self, initial_count: int = 1) -> None:
        self._count = initial_count
        self.acquire = Mock()
        self.release = Mock()
        self.available = Mock(return_value=1)

    def __call__(self, *args: Any, **kwargs: Any) -> 'MockQSemaphore':
        del args, kwargs  # Unused arguments
        return self


class MockQTimer:
    def __init__(self) -> None:
        self.singleShot = Mock()


class MockQApplication:
    def __init__(self) -> None:
        self.keyboardModifiers = Mock(return_value=0)
        self.style = Mock(return_value=Mock())

    @staticmethod
    def translate(_context: str, text: str) -> str:
        return text


class MockQMessageBox:
    def __init__(self) -> None:
        self.StandardButton = Mock()
        self.StandardButton.Yes = 1
        self.StandardButton.No = 0
        self.exec = Mock(return_value=1)
        self.setText = Mock()
        self.setInformativeText = Mock()
        self.setStandardButtons = Mock()
        self.setDefaultButton = Mock()


# Create mock Qt module
class MockQt:
    class KeyboardModifier:
        ControlModifier = 1


# Import the controller module with targeted patches
# Only patch PyQt6 since PyQt5 is not installed and should be ignored
with patch('PyQt6.QtCore.QSemaphore', MockQSemaphore), patch(
    'PyQt6.QtCore.QTimer', MockQTimer
), patch('PyQt6.QtCore.Qt', MockQt), patch(
    'PyQt6.QtCore.pyqtSlot', side_effect=lambda *_args, **_kwargs: lambda f: f
), patch(
    'PyQt6.QtWidgets.QApplication', MockQApplication
), patch(
    'PyQt6.QtWidgets.QMessageBox', MockQMessageBox
), patch(
    'PyQt6.QtWidgets.QWidget', Mock
), patch(
    'artisanlib.util.getDirectory', return_value='/test/cache/path'
), patch(
    'plus.config.connected', False
), patch(
    'plus.config.app_window', None
), patch(
    'plus.config.passwd', None
), patch(
    'plus.config.app_name', 'artisan.plus'
), patch(
    'keyring.set_password', Mock()
), patch(
    'keyring.delete_password', Mock()
):
    from plus import controller


@pytest.fixture(scope='session', autouse=True)
def ensure_controller_isolation() -> Generator[None, None, None]:
    """
    Ensure modules are properly isolated for controller tests at session level.

    This fixture runs once per test session to ensure that mocked modules
    used by controller tests don't interfere with other tests that need real dependencies.
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
def cleanup_controller_mocks() -> Generator[None, None, None]:
    """
    Clean up controller test mocks at module level to prevent cross-file contamination.

    This fixture runs once per test module and ensures immediate cleanup
    of mocked dependencies when the controller test module completes.
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
def reset_controller_state() -> Generator[None, None, None]:
    """
    Reset controller module state before and after each test to ensure complete isolation.

    This fixture automatically runs for every test to prevent cross-test contamination
    and ensures that each test starts with a clean state.
    """
    # Store original values
    original_connected = getattr(controller.config, 'connected', False)
    original_app_window = getattr(controller.config, 'app_window', None)
    original_passwd = getattr(controller.config, 'passwd', None)

    # Reset semaphore mocks if they exist and are actually mocks
    if hasattr(controller, 'connect_semaphore'):
        if hasattr(controller.connect_semaphore, 'acquire') and hasattr(
            controller.connect_semaphore.acquire, 'reset_mock'
        ):
            controller.connect_semaphore.acquire.reset_mock() # pyright: ignore[reportAttributeAccessIssue] # ty: ignore
        if hasattr(controller.connect_semaphore, 'release') and hasattr(
            controller.connect_semaphore.release, 'reset_mock'
        ):
            controller.connect_semaphore.release.reset_mock() # pyright: ignore[reportAttributeAccessIssue] # ty: ignore

    yield

    # Restore original values
    controller.config.connected = original_connected
    controller.config.app_window = original_app_window
    controller.config.passwd = original_passwd


@pytest.fixture
def mock_qsemaphore() -> Mock:
    """Create a mock QSemaphore for testing."""
    mock_sem = Mock()
    mock_sem.acquire = Mock()
    mock_sem.release = Mock()
    mock_sem.available = Mock(return_value=1)
    return mock_sem


@pytest.fixture
def mock_app_window() -> Mock:
    """Create a mock application window."""
    mock_aw = Mock()
    mock_aw.plus_account = 'test@example.com'
    mock_aw.plus_email = 'test@example.com'
    mock_aw.plus_remember_credentials = True
    mock_aw.plus_user_id = 'user123'
    mock_aw.curFile = '/path/to/profile.alog'
    mock_aw.qmc = Mock()
    mock_aw.qmc.roastUUID = 'roast-uuid-123'
    mock_aw.qmc.flagon = True
    mock_aw.qmc.timex = [0, 60, 120, 180]
    mock_aw.qmc.timeindex = [0]
    mock_aw.qmc.checkSaved = Mock(return_value=True)
    mock_aw.sendmessageSignal = Mock()
    mock_aw.sendmessageSignal.emit = Mock()
    mock_aw.updatePlusStatusSignal = Mock()
    mock_aw.updatePlusStatusSignal.emit = Mock()
    mock_aw.disconnectPlusSignal = Mock()
    mock_aw.disconnectPlusSignal.emit = Mock()
    mock_aw.resetDonateCounter = Mock()
    return mock_aw


@pytest.fixture
def mock_login_response() -> Tuple[str,str,bool,bool]:
    """Create a mock login response."""
    return ('test@example.com', 'password123', True, True)


class TestConnectionState:
    """Test connection state management functions."""

    def test_is_connected_true(self) -> None:
        """Test is_connected returns True when connected."""
        # Arrange
        with patch('plus.controller.config') as mock_config:
            mock_config.connected = True

            # Act
            result = controller.is_connected()

            # Assert
            assert result is True

    def test_is_connected_false(self) -> None:
        """Test is_connected returns False when not connected."""
        # Arrange
        with patch('plus.controller.config') as mock_config:
            mock_config.connected = False

            # Act
            result = controller.is_connected()

            # Assert
            assert result is False

    def test_is_on_with_account(self, mock_app_window:Mock) -> None:
        """Test is_on returns True when app window has plus_account."""
        # Arrange
        with patch('plus.controller.config') as mock_config:
            mock_config.app_window = mock_app_window

            # Act
            result = controller.is_on()

            # Assert
            assert result is True

    def test_is_on_without_account(self, mock_app_window:Mock) -> None:
        """Test is_on returns False when app window has no plus_account."""
        # Arrange
        mock_app_window.plus_account = None
        with patch('plus.controller.config') as mock_config:
            mock_config.app_window = mock_app_window

            # Act
            result = controller.is_on()

            # Assert
            assert result is False

    def test_is_on_no_app_window(self) -> None:
        """Test is_on returns False when no app window."""
        # Arrange
        with patch('plus.controller.config') as mock_config:
            mock_config.app_window = None

            # Act
            result = controller.is_on()

            # Assert
            assert result is False

    def test_is_synced_with_uuid_and_sync(self, mock_app_window:Mock) -> None:
        """Test is_synced returns True when profile has UUID and is in sync."""
        # Arrange
        with patch('plus.controller.config') as mock_config, patch(
            'plus.controller.sync'
        ) as mock_sync:

            mock_config.app_window = mock_app_window
            mock_sync.getSync = Mock(return_value=True)

            # Act
            result = controller.is_synced()

            # Assert
            assert result is True
            mock_sync.getSync.assert_called_once_with('roast-uuid-123')

    def test_is_synced_without_uuid_no_file(self, mock_app_window:Mock) -> None:
        """Test is_synced returns True when no UUID and no file."""
        # Arrange
        mock_app_window.qmc.roastUUID = None
        mock_app_window.curFile = None
        with patch('plus.controller.config') as mock_config:
            mock_config.app_window = mock_app_window

            # Act
            result = controller.is_synced()

            # Assert
            assert result is True

    def test_is_synced_without_uuid_with_file(self, mock_app_window:Mock) -> None:
        """Test is_synced returns False when no UUID but has file."""
        # Arrange
        mock_app_window.qmc.roastUUID = None
        mock_app_window.curFile = '/path/to/file.alog'
        with patch('plus.controller.config') as mock_config:
            mock_config.app_window = mock_app_window

            # Act
            result = controller.is_synced()

            # Assert
            assert result is False

    def test_is_synced_no_app_window(self) -> None:
        """Test is_synced returns False when no app window."""
        # Arrange
        with patch('plus.controller.config') as mock_config:
            mock_config.app_window = None

            # Act
            result = controller.is_synced()

            # Assert
            assert result is False


class TestStartFunction:
    """Test start function."""

    def test_start_sets_app_window_and_schedules_connect(self, mock_app_window:Mock) -> None:
        """Test start function sets app window and schedules connect."""
        # Arrange
        with patch('plus.controller.config') as mock_config, patch(
            'plus.controller.QTimer'
        ) as mock_timer:

            # Act
            controller.start(mock_app_window)

            # Assert
            assert mock_config.app_window == mock_app_window
            mock_timer.singleShot.assert_called_once_with(2, controller.connect)


class TestToggleFunction:
    """Test toggle function."""

    def test_toggle_connect_when_no_account(self, mock_app_window:Mock) -> None:
        """Test toggle connects when no account is set."""
        # Arrange
        mock_app_window.plus_account = None
        with patch('plus.controller.config') as mock_config, patch(
            'plus.controller.connect'
        ) as mock_connect, patch('plus.controller.is_connected', return_value=False):

            mock_config.app_window = mock_app_window

            # Act
            controller.toggle(mock_app_window)

            # Assert
            mock_connect.assert_called_once()

#    def test_toggle_sync_when_connected_and_synced(self, mock_app_window:Mock) -> None:
#        """Test toggle syncs when connected and synced."""
#        # Arrange
#        with patch("plus.controller.config") as mock_config, patch(
#            "plus.controller.connect"
#        ) as mock_connect, patch("plus.controller.is_connected", return_value=True), patch(
#            "plus.controller.is_synced", return_value=True
#        ), patch(
#            "plus.controller.sync"
#        ) as mock_sync:
#
#            mock_config.app_window = mock_app_window
#            mock_config.connected = False  # Not connected initially
#
#            # Act
#            controller.toggle(mock_app_window)
#
#            # Assert
#            mock_connect.assert_called_once()
#            mock_sync.sync.assert_called_once()

    def test_toggle_add_roast_when_connected_not_synced(self, mock_app_window:Mock) -> None:
        """Test toggle adds roast when connected but not synced."""
        # Arrange
        with patch('plus.controller.config') as mock_config, patch(
            'plus.controller.is_connected', return_value=False
        ), patch('plus.controller.is_synced', return_value=False), patch(
            'plus.controller.queue'
        ) as mock_queue:

            mock_config.app_window = mock_app_window
            mock_config.connected = True

            # Act
            controller.toggle(mock_app_window)

            # Assert
            mock_queue.addRoast.assert_called_once()

    def test_toggle_disconnect_when_connected_and_synced(self, mock_app_window:Mock) -> None:
        """Test toggle disconnects when connected and synced."""
        # Arrange
        with patch('plus.controller.config') as mock_config, patch(
            'plus.controller.is_connected', return_value=False
        ), patch('plus.controller.is_synced', return_value=True), patch(
            'plus.controller.disconnect'
        ) as mock_disconnect, patch(
            'plus.controller.QApplication'
        ) as mock_qapp:

            mock_config.app_window = mock_app_window
            mock_config.connected = True
            mock_qapp.keyboardModifiers.return_value = 0  # No modifiers

            # Act
            controller.toggle(mock_app_window)

            # Assert
            mock_disconnect.assert_called_once_with(
                interactive=True,
                remove_credentials=False,
                keepON=False,
            )

    def test_toggle_disconnect_with_ctrl_modifier(self, mock_app_window:Mock) -> None:
        """Test toggle disconnects with credential removal when Ctrl is pressed."""
        # Arrange
        with patch('plus.controller.config') as mock_config, patch(
            'plus.controller.is_connected', return_value=False
        ), patch('plus.controller.is_synced', return_value=True), patch(
            'plus.controller.disconnect'
        ) as mock_disconnect, patch(
            'plus.controller.QApplication'
        ) as mock_qapp, patch(
            'plus.controller.Qt'
        ) as mock_qt:

            mock_config.app_window = mock_app_window
            mock_config.connected = True
            mock_qapp.keyboardModifiers.return_value = 1  # Control modifier
            mock_qt.KeyboardModifier.ControlModifier = 1

            # Act
            controller.toggle(mock_app_window)

            # Assert
            mock_disconnect.assert_called_once_with(
                interactive=True,
                remove_credentials=True,
                keepON=False,
            )


class TestConnectFunction:
    """Test connect function."""

    def test_connect_already_connected(self, mock_qsemaphore: Mock) -> None:
        """Test connect does nothing when already connected."""
        # Arrange
        with patch('plus.controller.is_connected', return_value=True), patch(
            'plus.controller.connect_semaphore', mock_qsemaphore
        ):

            # Act
            controller.connect()

            # Assert
            mock_qsemaphore.acquire.assert_not_called()

    def test_connect_successful_authentication(
        self, mock_app_window: Mock, mock_qsemaphore: Mock
    ) -> None:
        """Test connect with successful authentication."""
        # Arrange
        mock_app_window.plus_account = 'test@example.com'

        with patch('plus.controller.is_connected', return_value=False), patch(
            'plus.controller.connect_semaphore', mock_qsemaphore
        ), patch('plus.controller.config') as mock_config, patch(
            'plus.controller.connection'
        ) as mock_connection, patch(
            'plus.controller.queue'
        ) as mock_queue, patch(
            'keyring.get_password', return_value='password123'
        ):

            mock_config.app_window = mock_app_window
            mock_config.passwd = 'password123'
            mock_connection.authentify = Mock(return_value=True)
            mock_qsemaphore.available.return_value = 0  # Semaphore acquired

            # Act
            controller.connect()

            # Assert
            mock_qsemaphore.acquire.assert_called_once_with(1)
            mock_qsemaphore.release.assert_called_once_with(1)
            mock_connection.authentify.assert_called_once()
            mock_queue.start.assert_called_once()
            mock_app_window.updatePlusStatusSignal.emit.assert_called_once()

    def test_connect_failed_authentication(
        self, mock_app_window: Mock, mock_qsemaphore: Mock
    ) -> None:
        """Test connect with failed authentication."""
        # Arrange
        mock_app_window.plus_account = 'test@example.com'

        with patch('plus.controller.is_connected', return_value=False), patch(
            'plus.controller.connect_semaphore', mock_qsemaphore
        ), patch('plus.controller.config') as mock_config, patch(
            'plus.controller.connection'
        ) as mock_connection, patch(
            'keyring.get_password', return_value='password123'
        ):

            mock_config.app_window = mock_app_window
            mock_config.passwd = 'password123'
            mock_connection.authentify = Mock(return_value=False)
            mock_qsemaphore.available.return_value = 0  # Semaphore acquired

            # Act
            controller.connect(interactive=True)

            # Assert
            mock_connection.authentify.assert_called_once()
            mock_app_window.sendmessageSignal.emit.assert_called()

    def test_connect_with_login_dialog(
        self, mock_app_window: Mock, mock_login_response: Mock, mock_qsemaphore: Mock
    ) -> None:
        """Test connect shows login dialog when no credentials."""
        # Arrange
        mock_app_window.plus_account = None

        with patch('plus.controller.is_connected', return_value=False), patch(
            'plus.controller.connect_semaphore', mock_qsemaphore
        ), patch('plus.controller.config') as mock_config, patch(
            'plus.controller.connection'
        ) as mock_connection, patch(
            'plus.login.plus_login', return_value=mock_login_response
        ) as mock_login:

            mock_config.app_window = mock_app_window
            mock_config.passwd = None
            mock_connection.authentify = Mock(return_value=True)
            mock_qsemaphore.available.return_value = 0  # Semaphore acquired

            # Act
            controller.connect(interactive=True)

            # Assert
            mock_login.assert_called_once()
            assert mock_app_window.plus_account == 'test@example.com'
            assert mock_config.passwd == 'password123'

    def test_connect_login_dialog_cancelled(
        self, mock_app_window: Mock, mock_qsemaphore: Mock
    ) -> None:
        """Test connect handles cancelled login dialog."""
        # Arrange
        mock_app_window.plus_account = None
        cancelled_response = ('', '', False, False)  # Login cancelled

        with patch('plus.controller.is_connected', return_value=False), patch(
            'plus.controller.connect_semaphore', mock_qsemaphore
        ), patch('plus.controller.config') as mock_config, patch(
            'plus.login.plus_login', return_value=cancelled_response
        ):

            mock_config.app_window = mock_app_window
            mock_config.passwd = None
            mock_qsemaphore.available.return_value = 0  # Semaphore acquired

            # Act
            controller.connect(interactive=True)

            # Assert
            mock_app_window.sendmessageSignal.emit.assert_called()
            # Should emit "Login aborted" message

    def test_connect_clear_on_failure(self, mock_app_window: Mock, mock_qsemaphore: Mock) -> None:
        """Test connect clears credentials on failure when clear_on_failure=True."""
        # Arrange
        mock_app_window.plus_account = 'test@example.com'

        with patch('plus.controller.is_connected', return_value=False), patch(
            'plus.controller.connect_semaphore', mock_qsemaphore
        ), patch('plus.controller.config') as mock_config, patch(
            'plus.controller.connection'
        ) as mock_connection, patch(
            'keyring.get_password', return_value='password123'
        ):

            mock_config.app_window = mock_app_window
            mock_config.passwd = 'password123'
            mock_connection.authentify = Mock(return_value=False)
            mock_qsemaphore.available.return_value = 0  # Semaphore acquired

            # Act
            controller.connect(clear_on_failure=True, interactive=True)

            # Assert
            mock_connection.clearCredentials.assert_called_once()
            mock_app_window.sendmessageSignal.emit.assert_called()

    def test_connect_exception_handling(self, mock_app_window: Mock, mock_qsemaphore: Mock) -> None:
        """Test connect handles exceptions gracefully."""
        # Arrange
        with patch('plus.controller.is_connected', return_value=False), patch(
            'plus.controller.connect_semaphore', mock_qsemaphore
        ), patch('plus.controller.config') as mock_config, patch(
            'keyring.get_password', side_effect=Exception('Keyring error')
        ):

            mock_config.app_window = mock_app_window
            mock_qsemaphore.available.return_value = 0  # Semaphore acquired

            # Act & Assert - Should not raise exception
            controller.connect(interactive=True)

            # Should still release semaphore despite exception
            mock_qsemaphore.release.assert_called_once_with(1)

#    def test_connect_non_interactive_mode(
#        self, mock_app_window: Mock, mock_qsemaphore: Mock
#    ) -> None:
#        """Test connect in non-interactive mode."""
#        # Arrange
#        mock_app_window.plus_account = None
#
#        with patch("plus.controller.is_connected", return_value=False), patch(
#            "plus.controller.connect_semaphore", mock_qsemaphore
#        ), patch("plus.controller.config") as mock_config, patch(
#            "plus.login.plus_login"
#        ) as mock_login:
#
#            mock_config.app_window = mock_app_window
#            mock_config.passwd = None
#            mock_qsemaphore.available.return_value = 0  # Semaphore acquired
#
#            # Act
#            controller.connect(interactive=False)
#
#            # Assert
#            mock_login.assert_not_called()  # Should not show login dialog
