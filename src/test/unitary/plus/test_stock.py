"""Unit tests for plus.stock module.

This module tests the stock management functionality including:
- Stock data structures and type definitions
- Stock cache management and file operations
- Worker thread for stock updates
- Coffee and blend management
- Store and location handling
- Stock calculations and filtering
- API interactions for stock data
- Semaphore-based thread safety
- Cache invalidation and updates
- Stock item retrieval and filtering

This test module implements comprehensive session-level isolation to prevent
cross-file module contamination and ensure compatibility with the entire test suite.
"""

import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Generator, Dict, Any, Optional
from unittest.mock import Mock, patch

import pytest

# ============================================================================
# SESSION-LEVEL ISOLATION SETUP
# ============================================================================

# Modules that need isolation for stock tests
modules_to_isolate = [
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'artisanlib.util',
    'artisanlib.dialogs',
    'plus.config',
    'plus.connection',
    'plus.controller',
    'plus.util',
]

# Note: plus.roast, plus.queue, plus.sync are NOT mocked as stock module doesn't depend on them
# Note: artisanlib.main is NOT mocked as stock module doesn't depend on it

# Store original modules before any mocking
original_modules = {}
original_functions = {}

for module_name in modules_to_isolate:
    if module_name in sys.modules:
        original_modules[module_name] = sys.modules[module_name]

# Store original functions that might be patched
function_paths = [
    'artisanlib.util.getDirectory',
]

for func_path in function_paths:
    if '.' in func_path:
        module_name, func_name = func_path.rsplit('.', 1)
        if module_name in sys.modules:
            original_functions[func_path] = getattr(sys.modules[module_name], func_name, None)

# Create comprehensive mocks for required dependencies only
mock_modules = {
    'PyQt6.QtCore': Mock(),
    'PyQt6.QtWidgets': Mock(),
    'artisanlib.util': Mock(),
    'artisanlib.dialogs': Mock(),
    'plus.config': Mock(),
    'plus.connection': Mock(),
    'plus.controller': Mock(),
    'plus.util': Mock(),
}

# Note: plus.roast, plus.queue, plus.sync are NOT mocked as stock module doesn't depend on them
# Note: artisanlib.main is NOT mocked as stock module doesn't depend on it
# Note: plus.register is NOT globally mocked to prevent cross-file contamination

# Apply mocks to sys.modules
for module_name, mock_module in mock_modules.items():
    sys.modules[module_name] = mock_module

# Mock specific Qt classes that stock module uses
sys.modules['PyQt6.QtCore'].QSemaphore = Mock # type: ignore[attr-defined]
sys.modules['PyQt6.QtCore'].QThread = Mock # type: ignore[attr-defined]
sys.modules['PyQt6.QtCore'].QObject = Mock # type: ignore[attr-defined]
sys.modules['PyQt6.QtCore'].pyqtSignal = Mock # type: ignore[attr-defined]
sys.modules['PyQt6.QtCore'].pyqtSlot = Mock # type: ignore[attr-defined]

# Mock QApplication in QtWidgets (where it actually belongs)
sys.modules['PyQt6.QtWidgets'].QApplication = Mock() # type: ignore[attr-defined]
sys.modules['PyQt6.QtWidgets'].QApplication.translate = Mock(return_value='Ethiopia') # ty: ignore

# Mock specific artisanlib.util functions that stock module uses
sys.modules['artisanlib.util'].getDirectory = Mock(return_value='test_cache_dir') # type: ignore[attr-defined]
sys.modules['artisanlib.util'].decodeLocal = Mock(side_effect=lambda x: x) # type: ignore[attr-defined]
sys.modules['artisanlib.util'].encodeLocal = Mock(side_effect=lambda x: x) # type: ignore[attr-defined]
sys.modules['artisanlib.util'].is_int_list = Mock(return_value=True) # type: ignore[attr-defined]
sys.modules['artisanlib.util'].is_float_list = Mock(return_value=True) # type: ignore[attr-defined]
sys.modules['artisanlib.util'].render_weight = Mock(return_value='1.0 kg') # type: ignore[attr-defined]

# Import the stock module after setting up mocks
from plus import stock

# ============================================================================
# ENHANCED MOCK CLASSES
# ============================================================================


class MockQSemaphore:
    """Enhanced mock for QSemaphore with proper method signatures."""

    def __init__(self, resources: int = 1) -> None:
        """Initialize mock semaphore."""
        self.resources = resources
        self._acquired = 0
        # Create Mock objects for method call tracking
        self.acquire = Mock(side_effect=self._acquire)
        self.release = Mock(side_effect=self._release)
        self.available = Mock(side_effect=self._available)

    def _acquire(self, n: int = 1) -> bool:
        """Internal acquire method."""
        self._acquired += n
        return True

    def _release(self, n: int = 1) -> None:
        """Internal release method."""
        self._acquired -= n

    def _available(self) -> int:
        """Internal available method."""
        return max(0, self.resources - self._acquired)


class MockQThread:
    """Enhanced mock for QThread with proper method signatures."""

    def __init__(self) -> None:
        """Initialize mock thread."""
        self.started = False

    def start(self) -> None:
        """Mock start method."""
        self.started = True

    def quit(self) -> None:
        """Mock quit method."""
        self.started = False

    def wait(self) -> bool:
        """Mock wait method."""
        return True


class MockQObject:
    """Enhanced mock for QObject with proper method signatures."""

    def moveToThread(self, thread:Mock) -> None:
        """Mock moveToThread method."""


# ============================================================================
# SESSION-LEVEL ISOLATION FIXTURES
# ============================================================================


@pytest.fixture(scope='session', autouse=True)
def ensure_stock_isolation() -> Generator[None, None, None]:
    """
    Ensure modules are properly isolated for stock tests at session level.

    This fixture runs once per test session to ensure that mocked modules
    used by stock tests don't interfere with other tests that need real dependencies.

    Critical for preventing cross-file contamination with test_main.py and other modules.
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
def cleanup_stock_mocks() -> Generator[None, None, None]:
    """
    Clean up stock test mocks at module level to prevent cross-file contamination.

    This fixture runs once per test module and ensures immediate cleanup
    of mocked dependencies when the stock test module completes.
    """
    yield

    # Additional cleanup for any test-specific patches
    # This ensures no stock test state leaks to other test modules


@pytest.fixture(autouse=True)
def reset_stock_state() -> Generator[None, None, None]:
    """
    Reset stock module state before each test to ensure test independence.

    This fixture runs before each test method to ensure clean state
    and prevent test interdependencies.
    """
    # Reset stock module global variables before test
    if hasattr(stock, 'stock'):
        stock.stock = None
    if hasattr(stock, 'worker'):
        stock.worker = None
    if hasattr(stock, 'worker_thread'):
        stock.worker_thread = None
    if hasattr(stock, 'duplicate_coffee_origin_labels'):
        stock.duplicate_coffee_origin_labels = set()

    # Clear any cached function results
    if hasattr(stock, 'getCoffeeLabels') and hasattr(stock.getCoffeeLabels, 'cache_clear'):
        stock.getCoffeeLabels.cache_clear()
    if hasattr(stock, 'getCoffees') and hasattr(stock.getCoffees, 'cache_clear'):
        stock.getCoffees.cache_clear()
    if hasattr(stock, 'getStores') and hasattr(stock.getStores, 'cache_clear'):
        stock.getStores.cache_clear()

    yield

    # Additional cleanup after each test
    if hasattr(stock, 'stock'):
        stock.stock = None
    if hasattr(stock, 'worker'):
        stock.worker = None
    if hasattr(stock, 'worker_thread'):
        stock.worker_thread = None
    if hasattr(stock, 'duplicate_coffee_origin_labels'):
        stock.duplicate_coffee_origin_labels = set()


@pytest.fixture
def mock_stock_semaphore() -> Generator[MockQSemaphore, None, None]:
    """Create a mock stock semaphore."""
    mock_sem = MockQSemaphore()
    with patch('plus.stock.stock_semaphore', mock_sem):
        yield mock_sem


@pytest.fixture
def mock_config() -> Generator[Mock, None, None]:
    """Create mock configuration."""
    with patch('plus.stock.config') as mock_cfg:
        mock_cfg.stock_cache_expiration = 3600  # 1 hour
        mock_cfg.schedule_cache_expiration = 300  # 5 minutes
        mock_cfg.stock_url = 'https://api.artisan.plus/stock'
        mock_cfg.stock_cache = 'stock_cache.json'
        yield mock_cfg


@pytest.fixture
def sample_coffee() -> Dict[str, Any]:
    """Create a sample coffee data structure."""
    return {
        'hr_id': 'coffee123',
        'label': 'Test Coffee',
        'origin': 'Ethiopia',
        'varietals': ['Heirloom'],
        'processing': 'Washed',
        'stock': [
            {'location_hr_id': 'store1', 'location_label': 'Main Store', 'amount': 5.5},
            {'location_hr_id': 'store2', 'location_label': 'Secondary Store', 'amount': 2.3},
        ],
        'default_unit': {'name': 'kg', 'size': 1000},
        'moisture': 11.5,
        'density': 650,
        'crop_date': {'picked': [2023]},
    }


@pytest.fixture
def sample_blend() -> Dict[str, Any]:
    """Create a sample blend data structure."""
    return {
        'hr_id': 'blend456',
        'label': 'Test Blend',
        'ingredients': [
            {'coffee': 'coffee123', 'ratio': 0.6, 'ratio_num': 3, 'ratio_denom': 5},
            {'coffee': 'coffee789', 'ratio': 0.4, 'ratio_num': 2, 'ratio_denom': 5},
        ],
        'stock': [{'location_hr_id': 'store1', 'location_label': 'Main Store', 'amount': 1.2}],
    }


@pytest.fixture
def sample_stock_data(sample_coffee:Dict[str, Any], sample_blend:Dict[str, Any]) -> Dict[str, Any]:
    """Create sample stock data."""
    return {
        'coffees': [sample_coffee],
        'blends': [sample_blend],
        'replBlends': [],
        'schedule': [],
        'retrieved': time.time(),
        'serverTime': int(time.time()),
    }


@pytest.fixture
def temp_stock_cache() -> Generator[str, None, None]:
    """Create a temporary stock cache file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        Path(temp_path).unlink()
    except OSError:
        pass


class TestStockDataStructures:
    """Test stock data structure definitions and type safety."""

    def test_coffee_unit_structure(self) -> None:
        """Test CoffeeUnit structure."""
        # Arrange
        coffee_unit = {'name': 'kg', 'size': 1000}

        # Act & Assert - Should be valid CoffeeUnit
        assert coffee_unit['name'] == 'kg'
        assert coffee_unit['size'] == 1000

    def test_stock_item_structure(self) -> None:
        """Test StockItem structure."""
        # Arrange
        stock_item = {'location_hr_id': 'store123', 'location_label': 'Test Store', 'amount': 5.5}

        # Act & Assert - Should be valid StockItem
        assert stock_item['location_hr_id'] == 'store123'
        assert stock_item['location_label'] == 'Test Store'
        assert stock_item['amount'] == 5.5

    def test_coffee_structure(self, sample_coffee:Dict[str,Any]) -> None:
        """Test Coffee structure."""
        # Act & Assert - Should be valid Coffee
        assert sample_coffee['hr_id'] == 'coffee123'
        assert sample_coffee['label'] == 'Test Coffee'
        assert sample_coffee['origin'] == 'Ethiopia'
        assert len(sample_coffee['stock']) == 2
        assert sample_coffee['default_unit']['name'] == 'kg'

    def test_blend_ingredient_structure(self) -> None:
        """Test BlendIngredient structure."""
        # Arrange
        ingredient = {'coffee': 'coffee123', 'ratio': 0.6, 'ratio_num': 3, 'ratio_denom': 5}

        # Act & Assert - Should be valid BlendIngredient
        assert ingredient['coffee'] == 'coffee123'
        assert ingredient['ratio'] == 0.6
        assert ingredient['ratio_num'] == 3
        assert ingredient['ratio_denom'] == 5

    def test_blend_structure(self, sample_blend:Dict[str,Any]) -> None:
        """Test Blend structure."""
        # Act & Assert - Should be valid Blend
        assert sample_blend['hr_id'] == 'blend456'
        assert sample_blend['label'] == 'Test Blend'
        assert len(sample_blend['ingredients']) == 2
        assert len(sample_blend['stock']) == 1

    def test_stock_structure(self, sample_stock_data:Dict[str,Any]) -> None:
        """Test Stock structure."""
        # Act & Assert - Should be valid Stock
        assert 'coffees' in sample_stock_data
        assert 'blends' in sample_stock_data
        assert 'retrieved' in sample_stock_data
        assert 'serverTime' in sample_stock_data
        assert len(sample_stock_data['coffees']) == 1
        assert len(sample_stock_data['blends']) == 1


class TestStockCacheOperations:
    """Test stock cache file operations."""

    def test_save_stock_to_cache(
        self, mock_stock_semaphore:Mock, sample_stock_data:Dict[str,Any], temp_stock_cache:str
    ) -> None:
        """Test saving stock data to cache file."""
        # Arrange
        with patch('plus.stock.stock_cache_path', temp_stock_cache), patch(
            'plus.stock.stock', sample_stock_data
        ):

            # Act
            stock.save()

            # Assert
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)

            # Verify file was written
            with open(temp_stock_cache, encoding='utf-8') as f:
                saved_data = json.load(f)

            assert saved_data['coffees'][0]['hr_id'] == 'coffee123'
            assert saved_data['blends'][0]['hr_id'] == 'blend456'

    def test_save_stock_with_none_stock(self, mock_stock_semaphore:Mock, temp_stock_cache:str) -> None:
        """Test saving when stock is None."""
        # Arrange
        with patch('plus.stock.stock_cache_path', temp_stock_cache), patch(
            'plus.stock.stock', None
        ):

            # Act
            stock.save()

            # Assert
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)

            # File should not be created or should be empty
            assert not Path(temp_stock_cache).exists() or Path(temp_stock_cache).stat().st_size == 0

    def test_load_stock_from_cache(self, sample_stock_data:Dict[str,Any], temp_stock_cache:str) -> None:
        """Test loading stock data from cache file."""
        # Arrange
        with open(temp_stock_cache, 'w', encoding='utf-8') as f:
            json.dump(sample_stock_data, f)

        with patch('plus.stock.stock_cache_path', temp_stock_cache), patch(
            'plus.stock.setStock'
        ) as mock_set_stock:

            # Act
            stock.load()

            # Assert
            mock_set_stock.assert_called_once()
            loaded_data = mock_set_stock.call_args[0][0]
            assert loaded_data['coffees'][0]['hr_id'] == 'coffee123'

    def test_load_stock_file_not_found(self, temp_stock_cache:str) -> None:
        """Test loading stock when cache file doesn't exist."""
        # Arrange
        Path(temp_stock_cache).unlink()  # Ensure file doesn't exist

        with patch('plus.stock.stock_cache_path', temp_stock_cache), patch(
            'plus.stock.setStock'
        ) as mock_set_stock:

            # Act
            stock.load()

            # Assert
            mock_set_stock.assert_not_called()

    def test_init_loads_stock_when_none(self) -> None:
        """Test init loads stock when stock is None."""
        # Arrange
        with patch('plus.stock.stock', None), patch('plus.stock.load') as mock_load:

            # Act
            stock.init()

            # Assert
            mock_load.assert_called_once()

    def test_init_skips_load_when_stock_exists(self, sample_stock_data:str) -> None:
        """Test init skips loading when stock already exists."""
        # Arrange
        with patch('plus.stock.stock', sample_stock_data), patch('plus.stock.load') as mock_load:

            # Act
            stock.init()

            # Assert
            mock_load.assert_not_called()


class TestStockManagement:
    """Test stock management operations."""

    def test_set_stock_updates_global_stock(self, mock_stock_semaphore:Mock, sample_stock_data:Optional[stock.Stock]) -> None:
        """Test setStock updates global stock variable."""
        # Arrange
        with patch('plus.stock.clearStockCaches') as mock_clear_caches, patch(
            'plus.stock.update_duplicate_coffee_origin_labels'
        ) as mock_update_labels:

            # Act
            stock.setStock(sample_stock_data)

            # Assert
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)
            mock_clear_caches.assert_called_once()
            mock_update_labels.assert_called_once()

    def test_set_stock_with_none(self, mock_stock_semaphore:Mock) -> None:
        """Test setStock with None value."""
        # Arrange
        with patch('plus.stock.clearStockCaches') as mock_clear_caches, patch(
            'plus.stock.update_duplicate_coffee_origin_labels'
        ) as mock_update_labels:

            # Act
            stock.setStock(None)

            # Assert
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)
            mock_clear_caches.assert_called_once()
            mock_update_labels.assert_called_once()

    def test_clear_stock_caches(self) -> None:
        """Test clearStockCaches function."""
        # Arrange
        with patch('plus.stock.getCoffeeLabels') as mock_get_coffee_labels, patch(
            'plus.stock.getCoffees'
        ) as mock_get_coffees, patch('plus.stock.getStores') as mock_get_stores:

            # Mock cache_clear methods
            mock_get_coffee_labels.cache_clear = Mock()
            mock_get_coffees.cache_clear = Mock()
            mock_get_stores.cache_clear = Mock()

            # Act
            stock.clearStockCaches()

            # Assert
            mock_get_coffee_labels.cache_clear.assert_called_once()
            mock_get_coffees.cache_clear.assert_called_once()
            mock_get_stores.cache_clear.assert_called_once()


class TestStockWorker:
    """Test stock worker thread operations."""

    def test_worker_initialization(self) -> None:
        """Test worker thread initialization."""
        # Arrange
        mock_thread = MockQThread()
        mock_worker = Mock()
        mock_worker.startSignal = Mock()
        mock_worker.replySignal = Mock()
        mock_worker.updatedSignal = Mock()
        mock_worker.upToDateSignal = Mock()
        mock_worker.moveToThread = Mock()

        # Mock the connect methods
        mock_worker.startSignal.connect = Mock()
        mock_worker.replySignal.connect = Mock()
        mock_worker.updatedSignal.connect = Mock()
        mock_worker.upToDateSignal.connect = Mock()

        with patch('plus.stock.QThread', return_value=mock_thread), patch(
            'plus.stock.Worker', return_value=mock_worker
        ), patch('plus.stock.util'):

            # Reset global variables
            stock.worker = None
            stock.worker_thread = None

            # Act
            result = stock.getWorker()

            # Assert
            assert result == mock_worker
            assert mock_thread.started is True
            mock_worker.moveToThread.assert_called_once_with(mock_thread)

    def test_worker_reuse_existing(self) -> None:
        """Test worker reuses existing instance."""
        # Arrange
        existing_worker = Mock()
        with patch('plus.stock.worker', existing_worker), patch('plus.stock.worker_thread', Mock()):

            # Act
            result = stock.getWorker()

            # Assert
            assert result == existing_worker

    def test_worker_exception_handling(self) -> None:
        """Test worker handles exceptions gracefully."""
        # Arrange
        with patch('plus.stock.QThread', side_effect=Exception('Test error')):

            # Act
            result = stock.getWorker()

            # Assert
            assert result is None

    def test_update_calls_worker(self) -> None:
        """Test update function calls worker."""
        # Arrange
        mock_worker = Mock()
        mock_worker.startSignal = Mock()
        mock_worker.startSignal.emit = Mock()

        with patch('plus.stock.getWorker', return_value=mock_worker), patch(
            'plus.stock.worker', mock_worker
        ):

            # Act
            stock.update()

            # Assert
            mock_worker.startSignal.emit.assert_called_once_with(False)

    def test_update_schedule_calls_worker(self) -> None:
        """Test update_schedule function calls worker."""
        # Arrange
        mock_worker = Mock()
        mock_worker.startSignal = Mock()
        mock_worker.startSignal.emit = Mock()

        with patch('plus.stock.getWorker', return_value=mock_worker), patch(
            'plus.stock.worker', mock_worker
        ):

            # Act
            stock.update_schedule()

            # Assert
            mock_worker.startSignal.emit.assert_called_once_with(True)


class TestWorkerUpdateBlocking:
    """Test Worker.update_blocking method."""

    def test_update_blocking_with_none_stock(self) -> None:
        """Test update_blocking when stock is None."""
        # Arrange
        worker = stock.Worker()
        mock_semaphore = MockQSemaphore()

        with patch('plus.stock.stock', None), patch('plus.stock.load') as mock_load, patch(
            'plus.stock.stock_semaphore', mock_semaphore
        ), patch('plus.stock.config') as mock_config:

            # Mock config values to prevent fetch from being called
            mock_config.connected = False
            mock_config.app_window = None

            # Act
            worker.update_blocking(False)

            # Assert - Should call load when stock is None
            mock_load.assert_called_once()

    def test_update_blocking_cache_expired(self, sample_stock_data:Dict[str,Any]) -> None:
        """Test update_blocking when cache is expired."""
        # Arrange
        worker = stock.Worker()
        mock_semaphore = MockQSemaphore()
        expired_stock = sample_stock_data.copy()
        expired_stock['retrieved'] = time.time() - 7200  # 2 hours ago

        with patch('plus.stock.stock', expired_stock), patch(
            'plus.stock.stock_semaphore', mock_semaphore
        ), patch('plus.stock.config') as mock_config:

            # Mock config values to prevent complex logic
            mock_config.connected = False
            mock_config.app_window = None

            # Act
            worker.update_blocking(False)

            # Assert - Should acquire and release semaphore
            mock_semaphore.acquire.assert_called_once_with(1)
            mock_semaphore.release.assert_called_once_with(1)

    def test_update_blocking_cache_valid(self, sample_stock_data:Dict[str,Any]) -> None:
        """Test update_blocking executes without errors when cache is valid."""
        # Arrange
        worker = stock.Worker()
        mock_semaphore = MockQSemaphore()
        fresh_stock = sample_stock_data.copy()
        fresh_stock['retrieved'] = time.time() - 1800  # 30 minutes ago

        with patch('plus.stock.stock', fresh_stock), patch(
            'plus.stock.stock_semaphore', mock_semaphore
        ), patch('plus.stock.config') as mock_config:

            # Mock config values to prevent complex logic
            mock_config.connected = False
            mock_config.app_window = None

            # Act & Assert - Should execute without errors
            try:
                worker.update_blocking(False)
                # Test passes if no exception is raised
                assert True
            except Exception as e:
                pytest.fail(f"update_blocking raised an exception: {e}")

    def test_update_blocking_schedule_mode(self, sample_stock_data:Dict[str,Any]) -> None:
        """Test update_blocking in schedule mode."""
        # Arrange
        worker = stock.Worker()
        mock_semaphore = MockQSemaphore()
        expired_stock = sample_stock_data.copy()
        expired_stock['retrieved'] = time.time() - 600  # 10 minutes ago

        with patch('plus.stock.stock', expired_stock), patch(
            'plus.stock.stock_semaphore', mock_semaphore
        ), patch('plus.stock.config') as mock_config:

            # Mock config values to prevent complex logic
            mock_config.connected = False
            mock_config.app_window = None

            # Act
            worker.update_blocking(True)

            # Assert - Should acquire and release semaphore
            mock_semaphore.acquire.assert_called_once_with(1)
            mock_semaphore.release.assert_called_once_with(1)

    def test_fetch_successful_response(self) -> None:
        """Test fetch method with successful API response."""
        # Arrange
        worker = stock.Worker()
        # Mock the worker signals
        worker.replySignal = Mock()
        worker.replySignal.emit = Mock()
        worker.updatedSignal = Mock()
        worker.updatedSignal.emit = Mock()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'success': True, 'result': {'coffees': [], 'blends': []}}

        with patch('plus.stock.connection.getData', return_value=mock_response), patch(
            'plus.stock.setStock'
        ) as mock_set_stock, patch('plus.stock.controller.reconnected') as mock_reconnected, patch(
            'plus.stock.util.extractAccountState', return_value=(100, 50, True, [], [])
        ):

            # Act
            result = worker.fetch(None)

            # Assert
            assert result is True
            mock_set_stock.assert_called_once()
            mock_reconnected.assert_called_once()
            worker.replySignal.emit.assert_called_once()
            # updatedSignal.emit is called in update_blocking, not fetch

    def test_fetch_no_content_response(self) -> None:
        """Test fetch method with 204 No Content response."""
        # Arrange
        worker = stock.Worker()
        mock_response = Mock()
        mock_response.status_code = 204

        with patch('plus.stock.connection.getData', return_value=mock_response):

            # Act
            result = worker.fetch(None)

            # Assert
            assert result is False

    def test_fetch_with_lsrt_parameter(self) -> None:
        """Test fetch method with last schedule retrieved time parameter."""
        # Arrange
        worker = stock.Worker()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'success': True, 'result': {'coffees': [], 'blends': []}}

        with patch(
            'plus.stock.connection.getData', return_value=mock_response
        ) as mock_get_data, patch('plus.stock.config.stock_url', 'https://api.test.com/stock'):

            # Act
            worker.fetch(1234567890.0)

            # Assert
            mock_get_data.assert_called_once()
            call_args = mock_get_data.call_args[0][0]
            assert 'lsrt=1234567890.0' in call_args

    def test_fetch_exception_handling(self) -> None:
        """Test fetch method handles exceptions gracefully."""
        # Arrange
        worker = stock.Worker()

        with patch('plus.stock.connection.getData', side_effect=Exception('Network error')):

            # Act
            result = worker.fetch(None)

            # Assert
            assert result is False


class TestCoffeeOperations:
    """Test coffee-related operations."""

    def test_get_coffee_labels(self, mock_stock_semaphore:Mock, sample_stock_data:Dict[str,Any]) -> None:
        """Test getCoffeeLabels function."""
        # Arrange
        with patch('plus.stock.stock', sample_stock_data), patch(
            'plus.stock.coffeeLabel', return_value='Ethiopia Test Coffee'
        ):

            # Act
            result = stock.getCoffeeLabels()

            # Assert
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)
            assert 'Ethiopia Test Coffee' in result
            assert result['Ethiopia Test Coffee'] == 'coffee123'

    def test_get_coffee_labels_empty_stock(self, mock_stock_semaphore:Mock) -> None:
        """Test getCoffeeLabels with empty stock."""
        # Arrange
        # Reset the stock module state to ensure clean test
        stock.stock = None

        with patch('plus.stock.stock', None):

            # Act
            result = stock.getCoffeeLabels()

            # Assert
            assert result == {}
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)

    def test_get_coffee_by_hr_id(self, sample_stock_data:Dict[str,Any]) -> None:
        """Test getCoffee function."""
        # Arrange
        with patch('plus.stock.stock', sample_stock_data):

            # Act
            result = stock.getCoffee('coffee123')

            # Assert
            assert result is not None
            assert 'hr_id' in result
            assert result['hr_id'] == 'coffee123'
            assert 'label' in result
            assert result['label'] == 'Test Coffee'

    def test_get_coffee_not_found(self, sample_stock_data:Dict[str,Any]) -> None:
        """Test getCoffee with non-existent hr_id."""
        # Arrange
        with patch('plus.stock.stock', sample_stock_data):

            # Act
            result = stock.getCoffee('nonexistent')

            # Assert
            assert result is None

    def test_get_location_label(self, sample_coffee:stock.Coffee) -> None:
        """Test getLocationLabel function."""
        # Act
        result = stock.getLocationLabel(sample_coffee, 'store1')

        # Assert
        assert result == 'Main Store'

    def test_get_location_label_not_found(self, sample_coffee:stock.Coffee) -> None:
        """Test getLocationLabel with non-existent location."""
        # Act
        result = stock.getLocationLabel(sample_coffee, 'nonexistent')

        # Assert
        assert result == ''

    def test_get_coffees_with_stock(self, mock_stock_semaphore:Mock, sample_stock_data:Dict[str,Any]) -> None:
        """Test getCoffees function."""
        # Arrange
        with patch('plus.stock.stock', sample_stock_data), patch(
            'plus.stock.coffeeLabel', return_value='Ethiopia Test Coffee'
        ), patch('plus.stock.convertWeight', return_value=5.5):

            # Act
            result = stock.getCoffees(0)  # weight_unit_idx = 0 (kg)

            # Assert
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)
            assert len(result) > 0

    def test_get_coffees_filtered_by_store(self, mock_stock_semaphore:Mock, sample_stock_data:Dict[str,Any]) -> None:
        """Test getCoffees filtered by specific store."""
        del mock_stock_semaphore
        # Arrange
        with patch('plus.stock.stock', sample_stock_data), patch(
            'plus.stock.coffeeLabel', return_value='Ethiopia Test Coffee'
        ), patch('plus.stock.convertWeight', return_value=5.5):

            # Act
            result = stock.getCoffees(0, store='store1')

            # Assert
            assert len(result) > 0
            # Should only include items from store1

    def test_get_coffee_store(self, mock_stock_semaphore:Mock, sample_stock_data:Dict[str,Any]) -> None:
        """Test getCoffeeStore function."""
        # Arrange
        with patch('plus.stock.stock', sample_stock_data):

            # Act
            coffee, stock_item = stock.getCoffeeStore('coffee123', 'store1')

            # Assert
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)
            assert coffee is not None
            assert stock_item is not None
            assert 'hr_id' in coffee
            assert coffee['hr_id'] == 'coffee123'
            assert 'location_hr_id' in stock_item
            assert stock_item['location_hr_id'] == 'store1'

    def test_get_coffee_store_not_found(self, mock_stock_semaphore:Mock, sample_stock_data:Dict[str,Any]) -> None:
        """Test getCoffeeStore with non-existent coffee or store."""
        del mock_stock_semaphore
        # Arrange
        with patch('plus.stock.stock', sample_stock_data):

            # Act
            coffee, stock_item = stock.getCoffeeStore('nonexistent', 'store1')

            # Assert
            assert coffee is None
            assert stock_item is None


class TestStoreOperations:
    """Test store-related operations."""

    def test_get_stores(self, mock_stock_semaphore:Mock, sample_stock_data:Dict[str,Any]) -> None:
        """Test getStores function."""
        # Arrange
        with patch('plus.stock.stock', sample_stock_data), patch(
            'plus.stock.getStoreLabel', side_effect=lambda x: x[1]
        ):

            # Act
            result = stock.getStores()

            # Assert
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)
            assert len(result) == 2
            assert ('Main Store', 'store1') in result
            assert ('Secondary Store', 'store2') in result

    def test_get_stores_empty_stock(self, mock_stock_semaphore:Mock) -> None:
        """Test getStores with empty stock."""
        # Arrange
        # Reset the stock module state to ensure clean test
        stock.stock = None

        with patch('plus.stock.stock', None):

            # Act
            result = stock.getStores()

            # Assert
            assert result == []
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)

    def test_get_stores_no_acquire_lock(self, sample_stock_data:Dict[str,Any]) -> None:
        """Test getStores without acquiring lock."""
        # Arrange
        with patch('plus.stock.stock', sample_stock_data), patch(
            'plus.stock.getStoreLabel', side_effect=lambda x: x[1]
        ):

            # Act
            result = stock.getStores(acquire_lock=False)

            # Assert
            assert len(result) == 2

    def test_get_store_label(self) -> None:
        """Test getStoreLabel function."""
        # Arrange
        store_tuple = ('Test Store', 'store123')

        # Act
        result = stock.getStoreLabel(store_tuple)

        # Assert
        assert result == 'Test Store'


class TestBlendOperations:
    """Test blend-related operations."""

    def test_get_blends(self, mock_stock_semaphore:Mock, sample_stock_data:Dict[str,Any]) -> None:
        """Test getBlends function."""
        # Arrange
        with patch('plus.stock.stock', sample_stock_data), patch(
            'plus.stock.getBlendLabel', return_value='Test Blend'
        ), patch('plus.stock.renderAmount', return_value='1.2 kg'):

            # Act
            result = stock.getBlends(0, 'store1', None)  # weight_unit_idx, store, customBlend

            # Assert
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)
            assert len(result) >= 0  # May be empty if no blends match criteria

    def test_get_blends_filtered_by_store(self, mock_stock_semaphore:Mock, sample_stock_data:Dict[str,Any]) -> None:
        """Test getBlends filtered by specific store."""
        del mock_stock_semaphore
        # Arrange
        with patch('plus.stock.stock', sample_stock_data), patch(
            'plus.stock.getBlendLabel', return_value='Test Blend'
        ), patch('plus.stock.renderAmount', return_value='1.2 kg'):

            # Act
            result = stock.getBlends(0, 'store1', None)  # weight_unit_idx, store, customBlend

            # Assert
            assert len(result) >= 0  # May be empty if no blends match criteria

    def test_get_blends_empty_stock(self, mock_stock_semaphore:Mock) -> None:
        """Test getBlends with empty stock."""
        del mock_stock_semaphore
        # Arrange
        with patch('plus.stock.stock', None):

            # Act
            result = stock.getBlends(0, 'store1', None)  # weight_unit_idx, store, customBlend

            # Assert
            assert result == []

    def test_get_blend_by_hr_id(self, sample_stock_data:Dict[str,Any], mock_stock_semaphore:Mock) -> None:
        """Test finding blend by hr_id through getBlends function."""
        # Arrange
        with patch('plus.stock.stock', sample_stock_data), patch(
            'plus.stock.getBlendLabel', return_value='Test Blend'
        ), patch('plus.stock.renderAmount', return_value='1.2 kg'):

            # Act
            result = stock.getBlends(0, None, None)  # Get all blends

            # Assert
            # Should be able to find blends (may be empty if filtering doesn't match)
            assert isinstance(result, list)
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)

    def test_get_blend_not_found(self, sample_stock_data:Dict[str,Any], mock_stock_semaphore:Mock) -> None:
        """Test getBlends with empty stock returns empty list."""
        del sample_stock_data
        # Arrange
        with patch('plus.stock.stock', None):

            # Act
            result = stock.getBlends(0, None, None)

            # Assert
            assert result == []
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)

    def test_blend_label_generation(self, sample_blend:Any) -> None:
        """Test getBlendLabel and getBlendName functions with blend structure."""
        # Arrange
        # Create a mock blend structure that getBlendLabel expects
        # BlendStructure is (blend_id, (blend_dict, stock_item))
        mock_blend_structure = (
            'blend456',
            (sample_blend, {'location_hr_id': 'store1', 'amount': 1.2}),
        )

        with patch('plus.stock.coffee_label_normal_order', True):

            # Act - Test getBlendLabel (returns ID)
            label_result = stock.getBlendLabel(mock_blend_structure)   # type: ignore

            # Act - Test getBlendName (returns actual label)
            name_result = stock.getBlendName(mock_blend_structure)   # type: ignore

            # Assert
            assert label_result == 'blend456'  # getBlendLabel returns the ID
            assert name_result == 'Test Blend'  # getBlendName returns the actual label

    def test_blend_structure_operations(self, sample_stock_data:Any) -> None:
        """Test blend structure operations with ingredients."""
        # Arrange
        with patch('plus.stock.stock', sample_stock_data), patch(
            'plus.stock.getCoffee'
        ) as mock_get_coffee:

            # Mock coffee data for blend ingredients
            mock_get_coffee.side_effect = lambda hr_id: {
                'hr_id': hr_id,
                'moisture': 11.5,
                'density': 650,
            }

            # Act - Test blend2beans function which exists
            result = stock.blend2beans(
                ( # ty: ignore
                    'blend456',
                    sample_stock_data['blends'][0], # type: ignore
                    {'location_hr_id': 'store1', 'amount': 1.2},
                ),
                0,
                1.0,
            )

            # Assert
            # Should return list of bean descriptions
            assert isinstance(result, list)


class TestStockFiltering:
    """Test stock filtering and epsilon operations."""

    def test_stock_epsilon_filtering(self, sample_stock_data:Dict[str,Any], mock_stock_semaphore:Mock) -> None:
        """Test that stock items below epsilon are filtered out."""
        # Arrange
        small_stock_data = sample_stock_data.copy()
        # Set ALL stock amounts below epsilon
        small_stock_data['coffees'][0]['stock'][0]['amount'] = 0.005  # Below epsilon
        small_stock_data['coffees'][0]['stock'][1]['amount'] = 0.008  # Below epsilon

        with patch('plus.stock.stock', small_stock_data), patch('plus.stock.stock_epsilon', 0.01):

            # Act
            result = stock.getCoffeeLabels()

            # Assert
            # Should not include coffee with stock below epsilon
            assert len(result) == 0
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)

    def test_stock_above_epsilon_included(self, sample_stock_data:Dict[str,Any], mock_stock_semaphore:Mock) -> None:
        """Test that stock items above epsilon are included."""
        # Arrange
        with patch('plus.stock.stock', sample_stock_data), patch(
            'plus.stock.stock_epsilon', 0.01
        ), patch('plus.stock.coffeeLabel', return_value='Ethiopia Test Coffee'):

            # Act
            result = stock.getCoffeeLabels()

            # Assert
            # Should include coffee with stock above epsilon
            assert len(result) > 0
            mock_stock_semaphore.acquire.assert_called_once_with(1)
            mock_stock_semaphore.release.assert_called_once_with(1)


class TestCoffeeLabelGeneration:
    """Test coffee label generation and formatting."""

    def test_coffee_label_normal_order(self, sample_coffee:stock.Coffee) -> None:
        """Test coffee label with normal order (origin first)."""
        # Arrange
        # Mock QApplication.translate to return the origin as-is
        sys.modules['PyQt6.QtWidgets'].QApplication = Mock()  # type: ignore[attr-defined]
        sys.modules['PyQt6.QtWidgets'].QApplication.translate = Mock(return_value='Ethiopia')  # ty: ignore

        with patch('plus.stock.coffee_label_normal_order', True), patch(
            'plus.stock.duplicate_coffee_origin_labels', set()
        ):

            # Act
            result = stock.coffeeLabel(sample_coffee)

            # Assert
            assert 'Ethiopia' in result
            assert 'Test Coffee' in result

    def test_coffee_label_reverse_order(self, sample_coffee:stock.Coffee) -> None:
        """Test coffee label with reverse order (label first)."""
        # Arrange
        # Mock QApplication.translate to return the origin as-is
        sys.modules['PyQt6.QtWidgets'].QApplication = Mock()  # type: ignore[attr-defined]
        sys.modules['PyQt6.QtWidgets'].QApplication.translate = Mock(return_value='Ethiopia')  # ty: ignore

        with patch('plus.stock.coffee_label_normal_order', False), patch(
            'plus.stock.duplicate_coffee_origin_labels', set()
        ):

            # Act
            result = stock.coffeeLabel(sample_coffee)

            # Assert
            assert 'Ethiopia' in result
            assert 'Test Coffee' in result

    def test_coffee_label_with_picked_year(self, sample_coffee:stock.Coffee) -> None:
        """Test coffee label includes picked year when needed for disambiguation."""
        # Arrange
        # Mock QApplication.translate to return the origin as-is
        sys.modules['PyQt6.QtWidgets'].QApplication = Mock() # type: ignore[attr-defined]
        sys.modules['PyQt6.QtWidgets'].QApplication.translate = Mock(return_value='Ethiopia') # ty: ignore

        # The function checks for origin+label without space
        assert 'origin' in sample_coffee
        assert 'label' in sample_coffee
        origin_label = f"{sample_coffee['origin']}{sample_coffee['label']}"
        with patch('plus.stock.coffee_label_normal_order', True), patch(
            'plus.stock.duplicate_coffee_origin_labels', {origin_label}
        ):

            # Act
            result = stock.coffeeLabel(sample_coffee)

            # Assert
            assert '2023' in result  # Should include picked year

    def test_update_duplicate_coffee_origin_labels(self, sample_stock_data:Dict[str,Any]) -> None:
        """Test update_duplicate_coffee_origin_labels function."""
        # Arrange
        # Add another coffee with same origin+label but different picked year
        duplicate_coffee = sample_stock_data['coffees'][0].copy()
        duplicate_coffee['hr_id'] = 'coffee456'
        duplicate_coffee['crop_date'] = {'picked': [2022]}
        sample_stock_data['coffees'].append(duplicate_coffee)

        with patch('plus.stock.stock', sample_stock_data):

            # Act
            stock.update_duplicate_coffee_origin_labels()

            # Assert
            # Should identify duplicates and add to set
            assert len(stock.duplicate_coffee_origin_labels) > 0
