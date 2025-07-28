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
    'artisanlib.util',
    'artisanlib.main',
    'artisanlib.__version__',
    'plus.config',
    'plus.account',
    'plus.util',
    'requests',
    'requests.exceptions',
    'keyring',
    'dateutil.parser',
]

# Store original modules if they exist
for module_name in modules_to_isolate:
    if module_name in sys.modules and not hasattr(sys.modules[module_name], '_mock_name'):
        original_modules[module_name] = sys.modules[module_name]

# ============================================================================
# Now safe to import other modules
# ============================================================================

"""Unit tests for plus.connection module.

This module tests the network connection functionality including:
- Token management with semaphore protection
- Authentication and credential handling
- HTTP request/response operations (GET, POST, PUT)
- Header generation with user agent and authorization
- Data compression and decompression
- SSL verification and timeout configuration
- Error handling and retry logic
- Session token renewal on 401 errors
- Keyring integration for credential storage
- JSON data serialization and handling
- Request logging and debugging

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
   - ensure_connection_isolation fixture manages module state at session level
   - Proper cleanup after session to prevent module registration conflicts

4. **Automatic State Reset**:
   - reset_connection_state fixture runs automatically for every test
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
✅ Individual tests pass: pytest test_connection.py::TestClass::test_method
✅ Full module tests pass: pytest test_connection.py
✅ Cross-file isolation works: pytest test_connection.py test_main.py
✅ Cross-file isolation works: pytest test_main.py test_connection.py
✅ No module contamination affecting other tests
✅ No numpy multiple import issues

This implementation serves as a reference for proper test isolation in
modules that require extensive mocking while preventing cross-file contamination.
=============================================================================
"""

import pytest


# Create a mock QSemaphore class that behaves properly
class MockQSemaphore:
    def __init__(self, initial_count: int = 1) -> None:
        self._count = initial_count
        self.acquire = Mock()
        self.release = Mock()
        self.available = Mock(return_value=0)  # Default to acquired state

    def __call__(self, *args: Any, **kwargs: Any) -> 'MockQSemaphore':
        del args, kwargs  # Unused arguments
        return self


# Import the connection module with targeted patches
# Only patch PyQt6 since PyQt5 is not installed and should be ignored
with patch('artisanlib.__version__', '2.8.4'), patch(
    'artisanlib.util.getDirectory', return_value='/test/cache/path'
), patch('plus.config.app_name', 'artisan.plus'), patch(
    'plus.config.auth_url', 'https://artisan.plus/api/v1/accounts/users/authenticate'
), patch(
    'plus.config.verify_ssl', True
), patch(
    'plus.config.connect_timeout', 6
), patch(
    'plus.config.read_timeout', 6
), patch(
    'plus.config.compress_posts', True
), patch(
    'plus.config.post_compression_threshold', 500
), patch(
    'plus.config.token', None
), patch(
    'plus.config.nickname', None
), patch(
    'plus.config.passwd', None
), patch(
    'plus.config.connected', False
), patch(
    'plus.config.app_window', None
), patch(
    'PyQt6.QtCore.QSemaphore', MockQSemaphore
), patch(
    'requests.get', Mock()
), patch(
    'requests.post', Mock()
), patch(
    'requests.put', Mock()
), patch(
    'keyring.get_password', Mock()
), patch(
    'keyring.delete_password', Mock()
):
    from plus import connection


@pytest.fixture(autouse=True)
def isolated_test_environment() -> Generator[None, None, None]:
    """Provide completely isolated test environment for each test."""
    # Use patch.dict to ensure complete isolation from other test files
    with patch.dict(
        'sys.modules',
        {
            'PyQt6.QtCore': Mock(),
            'PyQt5.QtCore': Mock(),
            'artisanlib.util': Mock(),
            'artisanlib.main': Mock(),
            'plus.config': Mock(),
            'plus.account': Mock(),
            'plus.util': Mock(),
            'requests': Mock(),
            'requests.exceptions': Mock(),
            'keyring': Mock(),
            'dateutil.parser': Mock(),
        },
        clear=False,
    ):
        # Configure Qt mocks with proper QSemaphore behavior
        def create_mock_qsemaphore(*args: Any, **kwargs: Any) -> Mock:
            del args
            del kwargs
            mock_sem = Mock()
            mock_sem.acquire = Mock()
            mock_sem.release = Mock()
            mock_sem.available = Mock(return_value=0)  # Default to acquired state
            return mock_sem

        sys.modules['PyQt6.QtCore'].QSemaphore = create_mock_qsemaphore # type: ignore[attr-defined]
        sys.modules['PyQt5.QtCore'].QSemaphore = create_mock_qsemaphore # type: ignore[attr-defined]

        # Configure config mock with default values
        config_mock = sys.modules['plus.config']
        config_mock.app_name = 'artisan.plus'  # type: ignore[attr-defined]
        config_mock.auth_url = 'https://artisan.plus/api/v1/accounts/users/authenticate'  # type: ignore[attr-defined]
        config_mock.verify_ssl = True # type: ignore[attr-defined]
        config_mock.connect_timeout = 6 # type: ignore[attr-defined]
        config_mock.read_timeout = 6 # type: ignore[attr-defined]
        config_mock.compress_posts = True # type: ignore[attr-defined]
        config_mock.post_compression_threshold = 500 # type: ignore[attr-defined]
        config_mock.token = None  # type: ignore[attr-defined]
        config_mock.nickname = None # type: ignore[attr-defined]
        config_mock.passwd = None # type: ignore[attr-defined]
        config_mock.connected = False # type: ignore[attr-defined]
        config_mock.app_window = None # type: ignore[attr-defined]

        yield


@pytest.fixture(scope='session', autouse=True)
def ensure_connection_isolation() -> Generator[None, None, None]:
    """
    Ensure modules are properly isolated for connection tests at session level.

    This fixture runs once per test session to ensure that mocked modules
    used by connection tests don't interfere with other tests that need real dependencies.
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
def cleanup_connection_mocks() -> Generator[None, None, None]:
    """
    Clean up connection test mocks at module level to prevent cross-file contamination.

    This fixture runs once per test module and ensures immediate cleanup
    of mocked dependencies when the connection test module completes.
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


@pytest.fixture
def mock_qsemaphore() -> Mock:
    """Create a fresh mock QSemaphore for each test."""
    mock_sem = Mock()
    mock_sem.acquire = Mock()
    mock_sem.release = Mock()
    mock_sem.available = Mock(return_value=0)  # Default to 0 (acquired state)
    # Ensure available() returns an integer, not a Mock
    mock_sem.available.return_value = 0
    return mock_sem


@pytest.fixture
def mock_app_window() -> Mock:
    """Create a fresh mock application window for each test."""
    mock_aw = Mock()
    # Reset mock state to ensure fresh instance
    mock_aw.reset_mock()

    # Configure default attributes and behaviors
    mock_aw.plus_account = 'test@example.com'
    mock_aw.qmc = Mock()
    mock_aw.qmc.operator = None
    mock_aw.get_os = Mock(return_value=('macOS', '13.0', 'x86_64'))
    mock_aw.updateLimitsSignal = Mock()
    mock_aw.updateLimitsSignal.emit = Mock()

    # Add locale support for header generation
    mock_aw.locale_str = 'en_US'

    return mock_aw


@pytest.fixture(autouse=True)
def reset_connection_state() -> Generator[None, None, None]:
    """Reset connection module state before and after each test to ensure complete isolation."""
    # Store original values
    original_token = getattr(connection.config, 'token', None)
    original_nickname = getattr(connection.config, 'nickname', None)
    original_app_window = getattr(connection.config, 'app_window', None)
    original_connected = getattr(connection.config, 'connected', False)
    original_passwd = getattr(connection.config, 'passwd', None)

    # Reset semaphore mocks if they exist and are actually mocks
    if hasattr(connection, 'token_semaphore'):
        if hasattr(connection.token_semaphore, 'acquire') and hasattr(
            connection.token_semaphore.acquire, 'reset_mock'
        ):
            connection.token_semaphore.acquire.reset_mock() # pyright: ignore[reportAttributeAccessIssue] # ty: ignore
        if hasattr(connection.token_semaphore, 'release') and hasattr(
            connection.token_semaphore.release, 'reset_mock'
        ):
            connection.token_semaphore.release.reset_mock() # pyright: ignore[reportAttributeAccessIssue] # ty: ignore

    yield

    # Restore original values
    connection.config.token = original_token
    connection.config.nickname = original_nickname
    connection.config.app_window = original_app_window
    connection.config.connected = original_connected
    connection.config.passwd = original_passwd


@pytest.fixture
def mock_response() -> Mock:
    """Create a fresh mock HTTP response for each test."""
    mock_resp = Mock()
    # Reset mock state to ensure fresh instance
    mock_resp.reset_mock()

    # Configure default attributes and behaviors
    mock_resp.status_code = 200
    mock_resp.headers = {'content-type': 'application/json'}
    mock_resp.elapsed = Mock()
    mock_resp.elapsed.total_seconds = Mock(return_value=0.5)
    mock_resp.json = Mock(return_value={'success': True})
    return mock_resp


@pytest.fixture
def sample_auth_response() -> Dict[str, Any]:
    """Create fresh sample authentication response data for each test."""
    return {
        'success': True,
        'result': {
            'token': 'test_token_123',
            'user': {
                'nickname': 'TestUser',
                'account': {
                    'id': 'account_123',
                    'subscription': {'paidUntil': '2024-12-31T23:59:59Z'},
                    'limit': {'rlimit': 1000, 'rused': 50},
                },
            },
        },
        'notifications': {'unqualified': 5, 'machines': ['Machine1', 'Machine2']},
    }


class TestTokenManagement:
    """Test token management functionality."""

    def test_set_token_basic_functionality(
        self, reset_connection_state: None, mock_qsemaphore: Mock
    ) -> None:
        """Test setToken with basic token and nickname."""
        del reset_connection_state
        # Arrange
        test_token = 'test_token_456'
        test_nickname = 'TestNickname'

        with patch('plus.connection.token_semaphore', mock_qsemaphore), patch(
            'plus.connection.config'
        ) as mock_config:
            mock_config.app_window = None

            # Act
            connection.setToken(test_token, test_nickname)

            # Assert
            mock_qsemaphore.acquire.assert_called_once_with(1)
            mock_qsemaphore.release.assert_called_once_with(1)
            assert mock_config.token == test_token
            assert mock_config.nickname == test_nickname

    def test_set_token_with_app_window_operator_update(
        self, mock_app_window: Mock, mock_qsemaphore: Mock
    ) -> None:
        """Test setToken updates operator when app window is available."""
        # Arrange
        test_token = 'test_token_789'
        test_nickname = 'OperatorName'

        with patch('plus.connection.token_semaphore', mock_qsemaphore), patch(
            'plus.connection.config'
        ) as mock_config:

            mock_config.app_window = mock_app_window

            # Act
            connection.setToken(test_token, test_nickname)

            # Assert
            assert mock_app_window.qmc.operator == test_nickname

    def test_set_token_without_nickname(self, mock_qsemaphore: Mock) -> None:
        """Test setToken with token only (no nickname)."""
        # Arrange
        test_token = 'token_only_123'

        with patch('plus.connection.token_semaphore', mock_qsemaphore), patch(
            'plus.connection.config'
        ) as mock_config:

            mock_config.app_window = None

            # Act
            connection.setToken(test_token)

            # Assert
            assert mock_config.token == test_token
            assert mock_config.nickname is None

    def test_set_token_semaphore_protection(self, mock_qsemaphore: Mock) -> None:
        """Test setToken properly manages semaphore protection."""
        # Arrange
        test_token = 'semaphore_test_token'
        mock_qsemaphore.available.return_value = 0  # Semaphore is acquired

        with patch('plus.connection.token_semaphore', mock_qsemaphore), patch(
            'plus.connection.config'
        ) as mock_config:

            mock_config.app_window = None

            # Act
            connection.setToken(test_token)

            # Assert
            mock_qsemaphore.acquire.assert_called_once_with(1)
            mock_qsemaphore.release.assert_called_once_with(1)

    def test_set_token_no_release_when_available(self, mock_qsemaphore: Mock) -> None:
        """Test setToken doesn't release semaphore when already available."""
        # Arrange
        test_token = 'no_release_token'
        mock_qsemaphore.available.return_value = 1  # Semaphore is available

        with patch('plus.connection.token_semaphore', mock_qsemaphore), patch(
            'plus.connection.config'
        ) as mock_config:

            mock_config.app_window = None

            # Act
            connection.setToken(test_token)

            # Assert
            mock_qsemaphore.acquire.assert_called_once_with(1)
            # Should not call release since semaphore is available
            mock_qsemaphore.release.assert_not_called()


class TestCredentialManagement:
    """Test credential management functionality."""

    def test_clear_credentials_with_keychain_removal(self, mock_app_window: Mock) -> None:
        """Test clearCredentials with keychain removal."""
        # Arrange
        with patch('plus.connection.config') as mock_config, patch(
            'keyring.delete_password'
        ) as mock_delete_password:

            mock_config.app_window = mock_app_window
            mock_config.app_name = 'artisan.plus'
            mock_config.token = 'test_token'
            mock_config.nickname = 'test_nickname'
            mock_config.passwd = 'test_password'
            mock_config.account_nr = 123

            # Act
            connection.clearCredentials(remove_from_keychain=True)

            # Assert
            mock_delete_password.assert_called_once_with('artisan.plus', 'test@example.com')
            assert mock_config.token is None
            assert mock_config.nickname is None
            assert mock_config.passwd is None
            assert mock_config.account_nr is None

    def test_clear_credentials_without_keychain_removal(self, mock_app_window: Mock) -> None:
        """Test clearCredentials without keychain removal."""
        # Arrange
        with patch('plus.connection.config') as mock_config, patch(
            'keyring.delete_password'
        ) as mock_delete_password:

            mock_config.app_window = mock_app_window
            mock_config.token = 'test_token'
            mock_config.nickname = 'test_nickname'
            mock_config.passwd = 'test_password'
            mock_config.account_nr = 123

            # Act
            connection.clearCredentials(remove_from_keychain=False)

            # Assert
            mock_delete_password.assert_not_called()
            assert mock_config.token is None
            assert mock_config.nickname is None
            assert mock_config.passwd is None
            assert mock_config.account_nr is None

    def test_clear_credentials_keychain_exception_handling(self, mock_app_window: Mock) -> None:
        """Test clearCredentials handles keychain exceptions gracefully."""
        # Arrange
        with patch('plus.connection.config') as mock_config, patch(
            'keyring.delete_password', side_effect=Exception('Keychain error')
        ):

            mock_config.app_window = mock_app_window
            mock_config.token = 'test_token'

            # Act & Assert - Should not raise exception
            connection.clearCredentials(remove_from_keychain=True)

            # Should still clear config values despite keychain error
            assert mock_config.token is None

    def test_clear_credentials_no_app_window(self) -> None:
        """Test clearCredentials when no app window is available."""
        # Arrange
        with patch('plus.connection.config') as mock_config, patch(
            'keyring.delete_password'
        ) as mock_delete_password:

            mock_config.app_window = None
            mock_config.token = 'test_token'

            # Act
            connection.clearCredentials(remove_from_keychain=True)

            # Assert
            mock_delete_password.assert_not_called()
            assert mock_config.token is None


class TestHeaderGeneration:
    """Test HTTP header generation functionality."""

    def test_get_headers_authorized_with_token(self, mock_app_window: Mock) -> None:
        """Test getHeaders with authorization and token."""
        # Arrange
        with patch('plus.connection.config') as mock_config, patch(
            'plus.connection.__version__', '2.8.0'
        ), patch('plus.connection.getToken', return_value='auth_token_123'):

            mock_config.app_window = mock_app_window

            # Act
            headers = connection.getHeaders(authorized=True, decompress=True)

            # Assert
            assert 'user-agent' in headers
            assert 'Artisan/2.8.0' in headers['user-agent']
            assert 'macOS' in headers['user-agent']
            assert 'Accept-Charset' in headers
            assert headers['Accept-Charset'] == 'utf-8'
            assert 'Authorization' in headers
            assert headers['Authorization'] == 'Bearer auth_token_123'
            assert 'Accept-Encoding' in headers
            assert 'gzip' in headers['Accept-Encoding']
            assert 'Accept-Language' in headers
            assert headers['Accept-Language'] == 'en-us'

    def test_get_headers_unauthorized(self, mock_app_window: Mock) -> None:
        """Test getHeaders without authorization."""
        # Arrange
        with patch('plus.connection.config') as mock_config, patch(
            'artisanlib.__version__', '2.8.0'
        ):

            mock_config.app_window = mock_app_window
            mock_config.token = 'auth_token_123'

            # Act
            headers = connection.getHeaders(authorized=False, decompress=True)

            # Assert
            assert 'Authorization' not in headers
            assert 'user-agent' in headers
            assert 'Accept-Charset' in headers

    def test_get_headers_no_decompression(self, mock_app_window: Mock) -> None:
        """Test getHeaders without decompression support."""
        # Arrange
        with patch('plus.connection.config') as mock_config, patch(
            'artisanlib.__version__', '2.8.0'
        ):

            mock_config.app_window = mock_app_window
            mock_config.token = 'auth_token_123'

            # Act
            headers = connection.getHeaders(authorized=True, decompress=False)

            # Assert
            assert 'Accept-Encoding' not in headers
            assert 'Authorization' in headers

    def test_get_headers_no_app_window(self) -> None:
        """Test getHeaders when no app window is available."""
        # Arrange
        with patch('plus.connection.config') as mock_config:
            mock_config.app_window = None

            # Act
            headers = connection.getHeaders(authorized=True, decompress=True)

            # Assert
            # When no app_window is available, getHeaders returns empty dict
            assert headers == {}


class TestDataCompression:
    """Test data compression and header generation."""

    def test_get_headers_and_data_with_compression(self) -> None:
        """Test getHeadersAndData with compression enabled."""
        # Arrange
        large_data = {'key': 'x' * 1000}  # Large data to trigger compression
        jsondata = json.dumps(large_data, ensure_ascii=False).encode('utf8')

        with patch('plus.connection.getHeaders', return_value={'base': 'header'}), patch(
            'plus.connection.config'
        ) as mock_config:

            mock_config.post_compression_threshold = 500

            # Act
            headers, postdata = connection.getHeadersAndData(True, True, jsondata, 'POST')

            # Assert
            assert headers['Content-Type'] == 'application/json; charset=utf-8'
            assert 'Idempotency-Key' in headers
            assert headers['Content-Encoding'] == 'gzip'
            assert len(postdata) < len(jsondata)  # Compressed data should be smaller

    def test_get_headers_and_data_without_compression(self) -> None:
        """Test getHeadersAndData without compression."""
        # Arrange
        small_data = {'key': 'small'}
        jsondata = json.dumps(small_data, ensure_ascii=False).encode('utf8')

        with patch('plus.connection.getHeaders', return_value={'base': 'header'}), patch(
            'plus.connection.config'
        ) as mock_config:

            mock_config.post_compression_threshold = 500

            # Act
            headers, postdata = connection.getHeadersAndData(True, True, jsondata, 'POST')

            # Assert
            assert headers['Content-Type'] == 'application/json; charset=utf-8'
            assert 'Idempotency-Key' in headers
            assert 'Content-Encoding' not in headers
            assert postdata == jsondata  # Data should be unchanged

    def test_get_headers_and_data_put_request(self) -> None:
        """Test getHeadersAndData with PUT request (no idempotency key)."""
        # Arrange
        data = {'key': 'value'}
        jsondata = json.dumps(data, ensure_ascii=False).encode('utf8')

        with patch('plus.connection.getHeaders', return_value={'base': 'header'}):

            # Act
            headers, postdata = connection.getHeadersAndData(True, False, jsondata, 'PUT')

            # Assert
            assert headers['Content-Type'] == 'application/json; charset=utf-8'
            assert 'Idempotency-Key' not in headers
            assert postdata == jsondata

    def test_get_headers_and_data_compression_disabled(self) -> None:
        """Test getHeadersAndData with compression disabled."""
        # Arrange
        large_data = {'key': 'x' * 1000}
        jsondata = json.dumps(large_data, ensure_ascii=False).encode('utf8')

        with patch('plus.connection.getHeaders', return_value={'base': 'header'}):

            # Act
            headers, postdata = connection.getHeadersAndData(True, False, jsondata, 'POST')

            # Assert
            assert 'Content-Encoding' not in headers
            assert postdata == jsondata  # Data should not be compressed


class TestSendData:
    """Test sendData functionality."""

    def test_send_data_post_success(self, mock_response: Mock) -> None:
        """Test sendData with successful POST request."""
        # Arrange
        url = 'https://api.example.com/data'
        data = {'test': 'data'}

        with patch(
            'plus.connection.getHeadersAndData',
            return_value=({'Content-Type': 'application/json'}, b'{"test":"data"}'),
        ), patch('plus.connection.requests.post', return_value=mock_response) as mock_post, patch(
            'plus.connection.config'
        ) as mock_config:

            mock_config.verify_ssl = True
            mock_config.connect_timeout = 6
            mock_config.read_timeout = 6

            # Act
            result = connection.sendData(url, data, 'POST', authorized=True)

            # Assert
            assert result == mock_response
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]['verify'] is True
            assert call_args[1]['timeout'] == (6, 6)

    def test_send_data_put_success(self, mock_response: Mock) -> None:
        """Test sendData with successful PUT request."""
        # Arrange
        url = 'https://api.example.com/data'
        data = {'test': 'data'}

        with patch(
            'plus.connection.getHeadersAndData',
            return_value=({'Content-Type': 'application/json'}, b'{"test":"data"}'),
        ), patch('plus.connection.requests.put', return_value=mock_response) as mock_put, patch(
            'plus.connection.config'
        ) as mock_config:

            mock_config.verify_ssl = True
            mock_config.connect_timeout = 6
            mock_config.read_timeout = 6

            # Act
            result = connection.sendData(url, data, 'PUT', authorized=True)

            # Assert
            assert result == mock_response
            mock_put.assert_called_once()

    def test_send_data_401_retry_success(self, mock_response: Mock) -> None:
        """Test sendData handles 401 error with retry."""
        # Arrange
        url = 'https://api.example.com/data'
        data = {'test': 'data'}

        # First response is 401, second is success
        mock_401_response = Mock()
        mock_401_response.status_code = 401
        mock_401_response.elapsed = Mock()
        mock_401_response.elapsed.total_seconds = Mock(return_value=0.3)

        with patch(
            'plus.connection.getHeadersAndData',
            return_value=({'Content-Type': 'application/json'}, b'{"test":"data"}'),
        ), patch(
            'plus.connection.requests.post', side_effect=[mock_401_response, mock_response]
        ) as mock_post, patch(
            'plus.connection.authentify', return_value=True
        ) as mock_auth, patch(
            'plus.connection.config'
        ) as mock_config:

            mock_config.verify_ssl = True
            mock_config.connect_timeout = 6
            mock_config.read_timeout = 6

            # Act
            result = connection.sendData(url, data, 'POST', authorized=True)

            # Assert
            assert result == mock_response
            assert mock_post.call_count == 2  # Original call + retry
            mock_auth.assert_called_once()

    def test_send_data_401_retry_failed_auth(self) -> None:
        """Test sendData handles 401 error with failed re-authentication."""
        # Arrange
        url = 'https://api.example.com/data'
        data = {'test': 'data'}

        mock_401_response = Mock()
        mock_401_response.status_code = 401
        mock_401_response.elapsed = Mock()
        mock_401_response.elapsed.total_seconds = Mock(return_value=0.3)

        with patch(
            'plus.connection.getHeadersAndData',
            return_value=({'Content-Type': 'application/json'}, b'{"test":"data"}'),
        ), patch(
            'plus.connection.requests.post', return_value=mock_401_response
        ) as mock_post, patch(
            'plus.connection.authentify', return_value=False
        ) as mock_auth, patch(
            'plus.connection.config'
        ) as mock_config:

            mock_config.verify_ssl = True
            mock_config.connect_timeout = 6
            mock_config.read_timeout = 6

            # Act
            result = connection.sendData(url, data, 'POST', authorized=True)

            # Assert
            assert result == mock_401_response
            assert mock_post.call_count == 1  # Only original call, no retry
            mock_auth.assert_called_once()

    def test_send_data_unauthorized_request(self) -> None:
        """Test sendData with unauthorized request (no 401 retry)."""
        # Arrange
        url = 'https://api.example.com/data'
        data = {'test': 'data'}

        mock_401_response = Mock()
        mock_401_response.status_code = 401
        mock_401_response.elapsed = Mock()
        mock_401_response.elapsed.total_seconds = Mock(return_value=0.3)

        with patch(
            'plus.connection.getHeadersAndData',
            return_value=({'Content-Type': 'application/json'}, b'{"test":"data"}'),
        ), patch(
            'plus.connection.requests.post', return_value=mock_401_response
        ) as mock_post, patch(
            'plus.connection.authentify'
        ) as mock_auth, patch(
            'plus.connection.config'
        ) as mock_config:

            mock_config.verify_ssl = True
            mock_config.connect_timeout = 6
            mock_config.read_timeout = 6

            # Act
            result = connection.sendData(url, data, 'POST', authorized=False)

            # Assert
            assert result == mock_401_response
            assert mock_post.call_count == 1  # Only original call
            mock_auth.assert_not_called()  # No retry for unauthorized requests
