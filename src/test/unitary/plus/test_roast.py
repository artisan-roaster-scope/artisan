"""Unit tests for plus.roast module.

This module tests the roast management functionality including:
- Roast template generation from profile data
- Roast data extraction and formatting
- Blend specification trimming
- Sync record generation and hashing
- Profile data conversion and validation
- Temperature and time data handling
- Energy consumption and CO2 data processing
- Roast metadata management
- Background profile template handling
- Data suppression and filtering logic
"""

import sys
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

# Create comprehensive mocks to avoid circular imports and Qt dependencies
mock_modules = {
    'PyQt6.QtCore': Mock(),
    'plus.config': Mock(),
    'plus.connection': Mock(),
    'plus.controller': Mock(),
    'plus.util': Mock(),
    'plus.queue': Mock(),
    'plus.sync': Mock(),
    'plus.stock': Mock(),
    'artisanlib.util': Mock(),
    'artisanlib.atypes': Mock(),
}

# Add all mocks to sys.modules before importing
for module_name, mock_module in mock_modules.items():
    sys.modules[module_name] = mock_module

# Mock specific functions
mock_util = Mock()
mock_util.weight_units = ['g', 'kg', 'lb', 'oz']
mock_util.convertWeight = Mock(return_value=1000.0)
sys.modules['artisanlib.util'] = mock_util

from plus.roast import getRoast, getSyncRecord, getTemplate, trimBlendSpec
from plus.stock import Blend, BlendIngredient


@pytest.fixture
def half_blend_ingredient1() -> BlendIngredient:
    return {'coffee': 'Brazil Santos', 'ratio': 0.5}


@pytest.fixture
def half_blend_ingredient2() -> BlendIngredient:
    return {'coffee': 'Guatemala Rocket', 'ratio': 0.5}


@pytest.fixture
def half_blend_ingredient2_empty_coffee() -> BlendIngredient:
    return {'coffee': '', 'ratio': 0.5}


@pytest.fixture
def half_blend_ingredient2_no_coffee() -> BlendIngredient:
    return {'ratio': 0.5}  # type: ignore[typeddict-item] # broken BlendIngredient for testing


@pytest.fixture
def regular_blend(
    half_blend_ingredient1: BlendIngredient, half_blend_ingredient2: BlendIngredient
) -> Blend:
    """Pytest fixture to create a Blend instance for testing."""
    return {
        'label': 'Espresso Blend',
        'ingredients': [half_blend_ingredient1, half_blend_ingredient2],
    }


@pytest.fixture
def no_label_blend(
    half_blend_ingredient1: BlendIngredient, half_blend_ingredient2: BlendIngredient
) -> Blend:
    """Pytest fixture to create a Blend instance for testing."""
    return {  # type: ignore[typeddict-item] # broken Blend for testing
        'ingredients': [half_blend_ingredient1, half_blend_ingredient2]
    }


@pytest.fixture
def empty_label_blend(
    half_blend_ingredient1: BlendIngredient, half_blend_ingredient2: BlendIngredient
) -> Blend:
    """Pytest fixture to create a Blend instance for testing."""
    return {'label': '', 'ingredients': [half_blend_ingredient1, half_blend_ingredient2]}


@pytest.fixture
def ingredient2_empty_coffee_blend(
    half_blend_ingredient1: BlendIngredient, half_blend_ingredient2_empty_coffee: BlendIngredient
) -> Blend:
    """Pytest fixture to create a Blend instance for testing."""
    return {
        'label': 'Espresso Blend',
        'ingredients': [half_blend_ingredient1, half_blend_ingredient2_empty_coffee],
    }


@pytest.fixture
def ingredient2_no_coffee_blend(
    half_blend_ingredient1: BlendIngredient, half_blend_ingredient2_no_coffee: BlendIngredient
) -> Blend:
    """Pytest fixture to create a Blend instance for testing."""
    return {
        'label': 'Espresso Blend',
        'ingredients': [half_blend_ingredient1, half_blend_ingredient2_no_coffee],
    }


# trimBlendSpec


def test_trimBlendSpec_regular_blend(regular_blend: Blend) -> None:
    assert trimBlendSpec(regular_blend) is not None


def test_trimBlendSpec_no_label_blend(no_label_blend: Blend) -> None:
    assert trimBlendSpec(no_label_blend) is None


def test_trimBlendSpec_empty_label_blend(empty_label_blend: Blend) -> None:
    assert trimBlendSpec(empty_label_blend) is None


def test_trimBlendSpec_ingredient2_empty_coffee_blend(
    ingredient2_empty_coffee_blend: Blend,
) -> None:
    assert trimBlendSpec(ingredient2_empty_coffee_blend) is None


def test_trimBlendSpec_ingredient2_no_coffee_blend(ingredient2_no_coffee_blend: Blend) -> None:
    assert trimBlendSpec(ingredient2_no_coffee_blend) is None


# Additional comprehensive test fixtures and classes


@pytest.fixture
def mock_app_window() -> Mock:
    """Create a mock application window."""
    mock_aw = Mock()
    mock_aw.qmc = Mock()
    mock_aw.qmc.mode = 'C'  # Celsius mode
    mock_aw.qmc.plus_store = 'store123'
    mock_aw.qmc.plus_coffee = 'coffee456'
    mock_aw.qmc.plus_blend_spec = None
    mock_aw.qmc.backgroundprofile = None
    mock_aw.qmc.calcFlavorChartScoreFromFlavors = Mock(return_value=75.5)
    mock_aw.curFile = '/path/to/profile.alog'
    mock_aw.plus_readonly = False
    mock_aw.getProfile = Mock()
    return mock_aw


@pytest.fixture
def sample_profile_data() -> Dict[str, Any]:
    """Create sample profile data."""
    return {
        'roastbatchnr': 42,
        'roastbatchprefix': 'TEST',
        'roastbatchpos': 1,
        'title': 'Test Roast',
        'roastertype': 'Test Roaster',
        'machinesetup': 'Standard Setup',
        'roastingnotes': 'Test notes',
        'cuppingnotes': 'Great cupping',
        'ambientTemp': 22.5,
        'ambient_pressure': 1013,
        'ambient_humidity': 65,
        'moisture_roasted': 11.5,
        'whole_color': 85,
        'ground_color': 90,
        'color_system': 'Agtron',
        'mode': 'C',
        'computed': {
            'CHARGE_ET': 180.0,
            'CHARGE_BT': 175.0,
            'TP_BT': 195.0,
            'DRY_BT': 160.0,
            'FCs_BT': 205.0,
            'FCe_BT': 215.0,
            'DROP_BT': 220.0,
            'DROP_ET': 225.0,
            'TP_time': 120.0,
            'DRY_time': 300.0,
            'FCs_time': 480.0,
            'FCe_time': 540.0,
            'DROP_time': 600.0,
            'fcs_ror': 2.5,
            'det': 5.0,
            'dbt': 3.0,
            'BTU_ELEC': 1500.0,
            'BTU_batch': 2000.0,
            'CO2_batch': 500.0,
        },
        'flavors': [75, 80, 70, 85],
        'flavors_total_correction': 0.0,
        'start_weight': 1000.0,
        'end_weight': 850.0,
        'defects_weight': 10.0,
        'density_roasted': [400.0],
        'roastersize': 5.0,
        'roasterheating': 'Gas',
    }


@pytest.fixture
def sample_blend_spec_comprehensive() -> Dict[str, Any]:
    """Create comprehensive sample blend specification."""
    return {
        'label': 'Test Blend',
        'ingredients': [
            {'coffee': 'coffee123', 'ratio': 0.6, 'ratio_num': 3, 'ratio_denom': 5},
            {'coffee': 'coffee456', 'ratio': 0.4, 'ratio_num': 2, 'ratio_denom': 5},
        ],
        'extra_field': 'should_be_removed',
    }


class TestRoastTemplateGeneration:
    """Test roast template generation from profile data."""

    def test_get_template_basic_data(self, sample_profile_data: Dict[str, Any]) -> None:
        """Test getTemplate with basic profile data."""
        # Arrange
        with patch('plus.roast.util') as mock_util:
            mock_util.addNum2dict = Mock()
            mock_util.addString2dict = Mock()
            mock_util.add2dict = Mock()
            mock_util.addTemp2dict = Mock()
            mock_util.addAllTemp2dict = Mock()
            mock_util.addAllTime2dict = Mock()
            mock_util.addRoRTemp2dict = Mock()

            # Act
            result = getTemplate(sample_profile_data)  # type: ignore[arg-type]

            # Assert
            assert isinstance(result, dict)
            mock_util.addNum2dict.assert_called()
            mock_util.addString2dict.assert_called()

    def test_get_template_background_mode(self, sample_profile_data: Dict[str, Any]) -> None:
        """Test getTemplate with background=True."""
        # Arrange
        with patch('plus.roast.util') as mock_util:
            mock_util.addNum2dict = Mock()
            mock_util.addString2dict = Mock()
            mock_util.add2dict = Mock()
            mock_util.addTemp2dict = Mock()
            mock_util.addAllTemp2dict = Mock()
            mock_util.addAllTime2dict = Mock()
            mock_util.addRoRTemp2dict = Mock()

            # Act
            result = getTemplate(sample_profile_data, background=True)  # type: ignore[arg-type]

            # Assert
            assert isinstance(result, dict)
            # Should pass mode parameter for background profiles
            mock_util.addTemp2dict.assert_called()

    def test_get_template_exception_handling(self) -> None:
        """Test getTemplate handles exceptions gracefully."""
        # Arrange
        invalid_profile = {'invalid': 'data'}

        with patch('plus.roast.util') as mock_util:
            mock_util.addNum2dict = Mock(side_effect=Exception('Test error'))
            mock_util.addString2dict = Mock()
            mock_util.add2dict = Mock()

            # Act
            result = getTemplate(invalid_profile)  # type: ignore[arg-type]

            # Assert
            assert isinstance(result, dict)
            # Should continue despite exceptions

    def test_get_template_computed_data(self, sample_profile_data: Dict[str, Any]) -> None:
        """Test getTemplate processes computed data correctly."""
        # Arrange
        with patch('plus.roast.util') as mock_util:
            mock_util.addNum2dict = Mock()
            mock_util.addString2dict = Mock()
            mock_util.add2dict = Mock()
            mock_util.addTemp2dict = Mock()
            mock_util.addAllTemp2dict = Mock()
            mock_util.addAllTime2dict = Mock()
            mock_util.addRoRTemp2dict = Mock()

            # Act
            getTemplate(sample_profile_data)  # type: ignore[arg-type]

            # Assert
            mock_util.addAllTemp2dict.assert_called()
            mock_util.addAllTime2dict.assert_called()
            mock_util.addRoRTemp2dict.assert_called()

    def test_get_template_missing_computed_data(self) -> None:
        """Test getTemplate with missing computed data."""
        # Arrange
        profile_without_computed = {'title': 'Test'}

        with patch('plus.roast.util') as mock_util:
            mock_util.addNum2dict = Mock()
            mock_util.addString2dict = Mock()
            mock_util.add2dict = Mock()
            mock_util.addTemp2dict = Mock()
            mock_util.addAllTemp2dict = Mock()
            mock_util.addAllTime2dict = Mock()
            mock_util.addRoRTemp2dict = Mock()

            # Act
            result = getTemplate(profile_without_computed)  # type: ignore[arg-type]

            # Assert
            assert isinstance(result, dict)
            # Should not call computed data methods
            mock_util.addAllTemp2dict.assert_not_called()


class TestBlendSpecTrimming:
    """Test blend specification trimming functionality."""

    def test_trim_blend_spec_valid_blend(
        self, sample_blend_spec_comprehensive: Dict[str, Any]
    ) -> None:
        """Test trimBlendSpec with valid blend specification."""
        # Act
        result = trimBlendSpec(sample_blend_spec_comprehensive)  # type: ignore[arg-type]

        # Assert
        assert result is not None
        assert result['label'] == 'Test Blend'
        assert 'ingredients' in result
        assert len(result['ingredients']) == 2
        assert 'extra_field' not in result  # Should be removed

    def test_trim_blend_spec_ingredient_fields(
        self, sample_blend_spec_comprehensive: Dict[str, Any]
    ) -> None:
        """Test trimBlendSpec preserves correct ingredient fields."""
        # Act
        result = trimBlendSpec(sample_blend_spec_comprehensive)  # type: ignore[arg-type]

        # Assert
        assert result is not None
        ingredient = result['ingredients'][0]
        assert ingredient['coffee'] == 'coffee123'
        assert ingredient['ratio'] == 0.6
        assert 'ratio_num' in ingredient
        assert ingredient['ratio_num'] == 3
        assert 'ratio_denom' in ingredient
        assert ingredient['ratio_denom'] == 5

    def test_trim_blend_spec_exception_handling(self) -> None:
        """Test trimBlendSpec handles exceptions gracefully."""
        # Arrange
        invalid_blend = None

        # Act
        result = trimBlendSpec(invalid_blend)  # type: ignore[arg-type]

        # Assert
        assert result is None


class TestGetRoast:
    """Test getRoast functionality."""

    def test_get_roast_basic_functionality(
        self, mock_app_window: Mock, sample_profile_data: Dict[str, Any]
    ) -> None:
        """Test getRoast basic functionality."""
        # Arrange
        mock_app_window.getProfile.return_value = sample_profile_data

        with patch('plus.roast.config.app_window', mock_app_window), patch(
            'plus.roast.getTemplate', return_value={'template': 'data'}
        ) as mock_get_template, patch('plus.roast.util') as mock_util:

            mock_util.addTempDiff2dict = Mock()
            mock_util.addAllNum2dict = Mock()
            mock_util.addString2dict = Mock()
            mock_util.float2floatMin = Mock(return_value=75.5)
            mock_util.getModificationDate = Mock(return_value=1234567890.0)
            mock_util.epoch2ISO8601 = Mock(return_value='2023-01-01T00:00:00.000Z')

            # Act
            result = getRoast()

            # Assert
            assert isinstance(result, dict)
            mock_get_template.assert_called_once_with(sample_profile_data)

    def test_get_roast_with_coffee_selection(
        self, mock_app_window: Mock, sample_profile_data: Dict[str, Any]
    ) -> None:
        """Test getRoast with coffee selection."""
        # Arrange
        mock_app_window.getProfile.return_value = sample_profile_data
        mock_app_window.qmc.plus_coffee = 'coffee123'
        mock_app_window.qmc.plus_blend_spec = None

        with patch('plus.roast.config.app_window', mock_app_window), patch(
            'plus.roast.getTemplate', return_value={'id': 'roast123', 'start_weight': 1000}
        ), patch('plus.roast.util') as mock_util:

            mock_util.addTempDiff2dict = Mock()
            mock_util.addAllNum2dict = Mock()
            mock_util.addString2dict = Mock()
            mock_util.float2floatMin = Mock(return_value=75.5)
            mock_util.getModificationDate = Mock(return_value=None)

            # Act
            result = getRoast()

            # Assert
            assert result['coffee'] == 'coffee123'
            assert result['blend'] is None
            assert result['roast_id'] == 'roast123'
            assert result['amount'] == 1000

    def test_get_roast_with_blend_selection(
        self,
        mock_app_window: Mock,
        sample_profile_data: Dict[str, Any],
        sample_blend_spec_comprehensive: Dict[str, Any],
    ) -> None:
        """Test getRoast with blend selection."""
        # Arrange
        mock_app_window.getProfile.return_value = sample_profile_data
        mock_app_window.qmc.plus_coffee = None
        mock_app_window.qmc.plus_blend_spec = sample_blend_spec_comprehensive

        with patch('plus.roast.config.app_window', mock_app_window), patch(
            'plus.roast.getTemplate', return_value={'start_weight': 1000}
        ), patch(
            'plus.roast.trimBlendSpec', return_value={'label': 'Test Blend'}
        ) as mock_trim_blend, patch(
            'plus.roast.util'
        ) as mock_util:

            mock_util.addTempDiff2dict = Mock()
            mock_util.addAllNum2dict = Mock()
            mock_util.addString2dict = Mock()
            mock_util.float2floatMin = Mock(return_value=75.5)
            mock_util.getModificationDate = Mock(return_value=None)

            # Act
            result = getRoast()

            # Assert
            assert result['coffee'] is None
            assert result['blend'] == {'label': 'Test Blend'}
            mock_trim_blend.assert_called_once_with(sample_blend_spec_comprehensive)

    def test_get_roast_with_background_profile(
        self, mock_app_window: Mock, sample_profile_data: Dict[str, Any]
    ) -> None:
        """Test getRoast with background profile."""
        # Arrange
        background_profile = {'title': 'Background Profile'}
        mock_app_window.getProfile.return_value = sample_profile_data
        mock_app_window.qmc.backgroundprofile = background_profile

        with patch('plus.roast.config.app_window', mock_app_window), patch(
            'plus.roast.getTemplate'
        ) as mock_get_template, patch('plus.roast.util') as mock_util:

            mock_get_template.side_effect = [
                {'main': 'template'},  # First call for main profile
                {'background': 'template'},  # Second call for background profile
            ]
            mock_util.addTempDiff2dict = Mock()
            mock_util.addAllNum2dict = Mock()
            mock_util.addString2dict = Mock()
            mock_util.float2floatMin = Mock(return_value=75.5)
            mock_util.getModificationDate = Mock(return_value=None)

            # Act
            result = getRoast()

            # Assert
            assert result['template'] == {'background': 'template'}
            assert mock_get_template.call_count == 2
            # Second call should be with background=True
            mock_get_template.assert_any_call(background_profile, background=True)

    def test_get_roast_exception_handling(self, mock_app_window: Mock) -> None:
        """Test getRoast handles exceptions gracefully."""
        # Arrange
        mock_app_window.getProfile.side_effect = Exception('Test error')

        with patch('plus.roast.config.app_window', mock_app_window):

            # Act
            result = getRoast()

            # Assert
            assert result == {}

    def test_get_roast_location_clearing(
        self, mock_app_window: Mock, sample_profile_data: Dict[str, Any]
    ) -> None:
        """Test getRoast clears location when no coffee or blend selected."""
        # Arrange
        mock_app_window.getProfile.return_value = sample_profile_data
        mock_app_window.qmc.plus_coffee = None
        mock_app_window.qmc.plus_blend_spec = None
        mock_app_window.qmc.plus_store = 'store123'

        with patch('plus.roast.config.app_window', mock_app_window), patch(
            'plus.roast.getTemplate', return_value={}
        ), patch('plus.roast.util') as mock_util:

            mock_util.addTempDiff2dict = Mock()
            mock_util.addAllNum2dict = Mock()
            mock_util.addString2dict = Mock()
            mock_util.float2floatMin = Mock(return_value=75.5)
            mock_util.getModificationDate = Mock(return_value=None)

            # Act
            result = getRoast()

            # Assert
            assert result['location'] is None
            assert result['coffee'] is None
            assert result['blend'] is None


class TestGetSyncRecord:
    """Test getSyncRecord functionality."""

    def test_get_sync_record_with_roast_data(self) -> None:
        """Test getSyncRecord with provided roast data."""
        # Arrange
        roast_data = {
            'roast_id': 'roast123',
            'location': 'store456',
            'coffee': 'coffee789',
            'amount': 1000,
            'batch_number': 42,
            'label': 'Test Roast',
            'extra_field': 'should_be_ignored',
        }

        # Act
        sync_record, hash_value = getSyncRecord(roast_data)

        # Assert
        assert isinstance(sync_record, dict)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 hash length
        assert 'roast_id' in sync_record
        assert 'location' in sync_record
        assert 'coffee' in sync_record
        assert 'amount' in sync_record
        assert 'extra_field' not in sync_record  # Should be filtered out

    def test_get_sync_record_without_roast_data(self) -> None:
        """Test getSyncRecord without provided roast data."""
        # Arrange
        with patch(
            'plus.roast.getRoast', return_value={'roast_id': 'test123', 'amount': 500}
        ) as mock_get_roast:

            # Act
            sync_record, hash_value = getSyncRecord()

            # Assert
            mock_get_roast.assert_called_once()
            assert isinstance(sync_record, dict)
            assert isinstance(hash_value, str)

    def test_get_sync_record_hash_consistency(self) -> None:
        """Test getSyncRecord produces consistent hashes for same data."""
        # Arrange
        roast_data = {'roast_id': 'roast123', 'amount': 1000, 'batch_number': 42}

        # Act
        sync_record1, hash1 = getSyncRecord(roast_data)
        sync_record2, hash2 = getSyncRecord(roast_data)

        # Assert
        assert hash1 == hash2
        assert sync_record1 == sync_record2

    def test_get_sync_record_hash_different_for_different_data(self) -> None:
        """Test getSyncRecord produces different hashes for different data."""
        # Arrange
        roast_data1 = {'roast_id': 'roast123', 'amount': 1000}
        roast_data2 = {'roast_id': 'roast456', 'amount': 1000}

        # Act
        sync_record1, hash1 = getSyncRecord(roast_data1)
        sync_record2, hash2 = getSyncRecord(roast_data2)

        # Assert
        assert hash1 != hash2
        assert sync_record1 != sync_record2

    def test_get_sync_record_exception_handling(self) -> None:
        """Test getSyncRecord handles exceptions gracefully."""
        # Arrange
        with patch('plus.roast.getRoast', side_effect=Exception('Test error')):

            # Act
            sync_record, hash_value = getSyncRecord()

            # Assert
            assert sync_record == {}
            assert isinstance(hash_value, str)

    def test_get_sync_record_filters_sync_attributes(self) -> None:
        """Test getSyncRecord only includes sync record attributes."""
        # Arrange
        roast_data = {
            'roast_id': 'roast123',  # Should be included
            'location': 'store456',  # Should be included
            'coffee': 'coffee789',  # Should be included
            'amount': 1000,  # Should be included
            'batch_number': 42,  # Should be included
            'label': 'Test Roast',  # Should be included
            'notes': 'Test notes',  # Should be included
            'random_field': 'value',  # Should be excluded
            'another_field': 123,  # Should be excluded
        }

        # Act
        sync_record, hash_value = getSyncRecord(roast_data)

        # Assert
        # Check that only sync attributes are included
        expected_fields = {
            'roast_id',
            'location',
            'coffee',
            'amount',
            'batch_number',
            'label',
            'notes',
        }
        actual_fields = set(sync_record.keys())
        assert expected_fields.issubset(actual_fields)
        assert 'random_field' not in sync_record
        assert 'another_field' not in sync_record
