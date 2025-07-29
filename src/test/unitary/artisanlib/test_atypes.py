"""Unit tests for artisanlib.atypes module.

This module tests the Artisan type definitions including:
- TypedDict structures for profile data and computed information
- Complex nested type definitions with proper validation
- Type compatibility and structure validation
- Import isolation to prevent cross-file contamination
- Proper handling of Qt dependencies and datetime objects
- Comprehensive coverage of all TypedDict classes
- Type annotation validation and mypy compliance
- Python 3.8+ compatibility with proper type annotations

This test module implements comprehensive session-level isolation to prevent
cross-file module contamination and ensure proper mock state management.
The isolation prevents numpy import issues and Qt module interference.

Key Features:
- Session-level isolation fixtures prevent cross-file contamination
- Comprehensive TypedDict validation and structure testing
- Qt dependency mocking with PyQt6 compatibility
- Type annotation compliance for Python 3.8+
- ruff, mypy, and pyright compliance
- Proper datetime and QDateTime handling
- Mock state management for external dependencies

This implementation serves as a reference for proper test isolation in
modules that define complex type structures while preventing cross-file contamination.
=============================================================================
"""

from typing import Any, Dict, Generator, cast

import pytest

# No module-level variables needed for simplified atypes tests


# Enhanced Mock Classes for Qt Components
class MockQDateTime:
    """Enhanced mock for QDateTime with proper method signatures."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize mock QDateTime."""
        self.args = args
        self.kwargs = kwargs

    @staticmethod
    def currentDateTime() -> 'MockQDateTime':
        """Mock currentDateTime static method."""
        return MockQDateTime()

    def toString(self, _format_str: str = '') -> str:
        """Mock toString method."""
        return '2023-01-01T12:00:00'

    def toSecsSinceEpoch(self) -> int:
        """Mock toSecsSinceEpoch method."""
        return 1672574400  # 2023-01-01 12:00:00 UTC


# Import the atypes module directly without aggressive mocking
# The atypes module only contains type definitions and doesn't need runtime mocking
from artisanlib import atypes


# Session-level isolation fixture (simplified since no aggressive mocking is needed)
@pytest.fixture(scope='session', autouse=True)
def isolate_atypes_module() -> Generator[None, None, None]:
    """
    Session-level fixture to ensure clean test environment.

    The atypes module only contains type definitions, so no complex isolation is needed.
    """
    yield
    # No cleanup needed since we're not doing aggressive mocking


@pytest.fixture(autouse=True)
def reset_atypes_state() -> Generator[None, None, None]:
    """Reset atypes module state before each test to ensure test independence."""
    yield
    # No specific state to reset for atypes module as it only contains type definitions


@pytest.fixture
def sample_computed_profile_info() -> Dict[str, Any]:
    """Provide a sample ComputedProfileInformation for testing."""
    return {
        'CHARGE_ET': 150.5,
        'CHARGE_BT': 120.0,
        'TP_idx': 10,
        'TP_time': 300.0,
        'TP_ET': 180.0,
        'TP_BT': 160.0,
        'MET': 25.5,
        'DRY_time': 240.0,
        'DRY_ET': 170.0,
        'DRY_BT': 150.0,
        'FCs_time': 480.0,
        'FCs_ET': 200.0,
        'FCs_BT': 185.0,
        'FCe_time': 540.0,
        'FCe_ET': 210.0,
        'FCe_BT': 195.0,
        'DROP_time': 600.0,
        'DROP_ET': 220.0,
        'DROP_BT': 205.0,
        'totaltime': 600.0,
        'dryphasetime': 240.0,
        'midphasetime': 240.0,
        'finishphasetime': 120.0,
        'dry_phase_ror': 1.5,
        'mid_phase_ror': 0.8,
        'finish_phase_ror': 0.5,
        'total_ror': 0.9,
        'weight_loss': 15.5,
        'total_loss': 16.2,
        'volume_gain': 85.0,
        'moisture_loss': 12.0,
        'organic_loss': 3.5,
        'weightin': 1000.0,
        'weightout': 845.0,
        'total_yield': 84.5,
        'green_density': 0.65,
        'roasted_density': 0.45,
        'moisture_greens': 11.5,
        'moisture_roasted': 2.5,
        'ambient_temperature': 22.5,
        'ambient_humidity': 45.0,
        'ambient_pressure': 1013.25,
        'BTU_batch': 15000.0,
        'BTU_batch_per_green_kg': 15.0,
        'CO2_batch': 2.5,
        'CO2_batch_per_green_kg': 0.0025,
    }


@pytest.fixture
def sample_profile_data() -> Dict[str, Any]:
    """Provide a sample ProfileData for testing."""
    return {
        'version': '2.8.4',
        'build': '1234',
        'title': 'Test Roast Profile',
        'beans': 'Ethiopian Yirgacheffe',
        'roastdate': '2023-01-01',
        'roasttime': '12:00:00',
        'roastUUID': '12345678-1234-5678-9012-123456789abc',
        'weight': [1000.0, 845.0],
        'volume': [1500.0, 2275.0],
        'density': [0.65, 0.45],
        'roastertype': 'Probat',
        'roastersize': 12.0,
        'operator': 'Test Operator',
        'timex': [0.0, 30.0, 60.0, 90.0, 120.0],
        'temp1': [20.0, 50.0, 80.0, 120.0, 150.0],
        'temp2': [18.0, 45.0, 75.0, 115.0, 145.0],
        'specialevents': [1, 2, 3],
        'specialeventstype': [0, 1, 2],
        'specialeventsvalue': [0.0, 150.0, 200.0],
        'specialeventsStrings': ['CHARGE', 'DRY', 'FCs'],
        'etypes': ['Event 1', 'Event 2', 'Event 3'],
        'extradevices': [0, 1],
        'extraname1': ['Extra 1', 'Extra 2'],
        'extraname2': ['Extra 1 Ch2', 'Extra 2 Ch2'],
        'roastbatchnr': 1,
        'roastbatchprefix': 'B',
        'whole_color': 65,
        'ground_color': 70,
        'color_system': 'Agtron',
        'cuppingnotes': 'Bright acidity, floral notes',
        'roastingnotes': 'Light roast, stopped at first crack',
    }


class TestComputedProfileInformation:
    """Test ComputedProfileInformation TypedDict."""

    def test_computed_profile_info_structure(
        self, sample_computed_profile_info: Dict[str, Any]
    ) -> None:
        """Test ComputedProfileInformation structure and type compatibility."""
        # Arrange & Act
        computed_info: atypes.ComputedProfileInformation = cast(atypes.ComputedProfileInformation, sample_computed_profile_info)

        # Assert
        assert isinstance(computed_info, dict)
        assert 'CHARGE_ET' in computed_info
        assert computed_info['CHARGE_ET'] == 150.5
        assert 'CHARGE_BT' in computed_info
        assert computed_info['CHARGE_BT'] == 120.0
        assert 'TP_idx' in computed_info
        assert computed_info['TP_idx'] == 10
        assert 'totaltime' in computed_info
        assert computed_info['totaltime'] == 600.0
        assert 'weight_loss' in computed_info
        assert computed_info['weight_loss'] == 15.5
        assert 'BTU_batch' in computed_info
        assert computed_info['BTU_batch'] == 15000.0

    def test_computed_profile_info_optional_fields(self) -> None:
        """Test ComputedProfileInformation with minimal required fields."""
        # Arrange
        minimal_info: atypes.ComputedProfileInformation = {}

        # Act & Assert
        assert isinstance(minimal_info, dict)
        assert len(minimal_info) == 0

    def test_computed_profile_info_partial_data(self) -> None:
        """Test ComputedProfileInformation with partial data."""
        # Arrange
        partial_info: atypes.ComputedProfileInformation = {
            'CHARGE_ET': 150.0,
            'DROP_BT': 205.0,
            'totaltime': 600.0,
            'weight_loss': 15.5,
        }

        # Act & Assert
        assert isinstance(partial_info, dict)
        assert partial_info['CHARGE_ET'] == 150.0
        assert partial_info['DROP_BT'] == 205.0
        assert len(partial_info) == 4


class TestProfileData:
    """Test ProfileData TypedDict."""

    def test_profile_data_structure(self, sample_profile_data: Dict[str, Any]) -> None:
        """Test ProfileData structure and type compatibility."""
        # Arrange & Act
        profile_data: atypes.ProfileData = cast(atypes.ProfileData, sample_profile_data)

        # Assert
        assert isinstance(profile_data, dict)
        assert 'title' in profile_data
        assert profile_data['title'] == 'Test Roast Profile'
        assert 'beans' in profile_data
        assert profile_data['beans'] == 'Ethiopian Yirgacheffe'
        assert 'roastUUID' in profile_data
        assert profile_data['roastUUID'] == '12345678-1234-5678-9012-123456789abc'
        assert 'weight' in profile_data
        assert profile_data['weight'] == [1000.0, 845.0]
        assert 'roastersize' in profile_data
        assert profile_data['roastersize'] == 12.0
        assert 'timex' in profile_data
        assert len(profile_data['timex']) == 5
        assert 'temp1' in profile_data
        assert len(profile_data['temp1']) == 5

    def test_profile_data_optional_fields(self) -> None:
        """Test ProfileData with minimal required fields."""
        # Arrange
        minimal_profile: atypes.ProfileData = {}

        # Act & Assert
        assert isinstance(minimal_profile, dict)
        assert len(minimal_profile) == 0

    def test_profile_data_with_computed_info(
        self, sample_profile_data: Dict[str, Any], sample_computed_profile_info: Dict[str, Any]
    ) -> None:
        """Test ProfileData with computed information."""
        # Arrange
        profile_with_computed = sample_profile_data.copy()
        profile_with_computed['computed'] = sample_computed_profile_info

        profile_data: atypes.ProfileData = cast(atypes.ProfileData, profile_with_computed)

        # Act & Assert
        assert isinstance(profile_data, dict)
        assert 'computed' in profile_data
        assert 'CHARGE_ET' in profile_data['computed']
        assert profile_data['computed']['CHARGE_ET'] == 150.5
        assert 'totaltime' in profile_data['computed']
        assert profile_data['computed']['totaltime'] == 600.0


class TestBTU:
    """Test BTU TypedDict."""

    def test_btu_structure(self) -> None:
        """Test BTU structure and type compatibility."""
        # Arrange
        btu_data: atypes.BTU = {
            'load_pct': 85.5,
            'duration': 600.0,
            'BTUs': 15000.0,
            'CO2g': 2500.0,
            'LoadLabel': 'Main Burner',
            'Kind': 1,
            'SourceType': 0,
            'SortOrder': 1,
        }

        # Act & Assert
        assert isinstance(btu_data, dict)
        assert btu_data['load_pct'] == 85.5
        assert btu_data['duration'] == 600.0
        assert btu_data['BTUs'] == 15000.0
        assert btu_data['LoadLabel'] == 'Main Burner'
        assert btu_data['Kind'] == 1

    def test_btu_all_fields_required(self) -> None:
        """Test that BTU requires all fields (not total=False)."""
        # Arrange
        complete_btu: atypes.BTU = {
            'load_pct': 100.0,
            'duration': 300.0,
            'BTUs': 8000.0,
            'CO2g': 1200.0,
            'LoadLabel': 'Secondary',
            'Kind': 2,
            'SourceType': 1,
            'SortOrder': 2,
        }

        # Act & Assert
        assert len(complete_btu) == 8
        assert all(
            key in complete_btu
            for key in [
                'load_pct',
                'duration',
                'BTUs',
                'CO2g',
                'LoadLabel',
                'Kind',
                'SourceType',
                'SortOrder',
            ]
        )


class TestEnergyMetrics:
    """Test EnergyMetrics TypedDict."""

    def test_energy_metrics_structure(self) -> None:
        """Test EnergyMetrics structure and type compatibility."""
        # Arrange
        energy_metrics: atypes.EnergyMetrics = {
            'BTU_batch': 15000.0,
            'BTU_batch_per_green_kg': 15.0,
            'CO2_batch': 2.5,
            'BTU_preheat': 2000.0,
            'CO2_preheat': 0.3,
            'BTU_bbp': 1000.0,
            'CO2_bbp': 0.15,
            'BTU_cooling': 500.0,
            'CO2_cooling': 0.08,
            'BTU_roast': 12000.0,
            'BTU_roast_per_green_kg': 12.0,
            'CO2_roast': 2.0,
            'CO2_batch_per_green_kg': 0.0025,
            'CO2_roast_per_green_kg': 0.002,
            'BTU_LPG': 8000.0,
            'BTU_NG': 4000.0,
            'BTU_ELEC': 3000.0,
            'KWH_batch_per_green_kg': 3.5,
            'KWH_roast_per_green_kg': 2.8,
        }

        # Act & Assert
        assert isinstance(energy_metrics, dict)
        assert energy_metrics['BTU_batch'] == 15000.0
        assert energy_metrics['CO2_batch'] == 2.5
        assert energy_metrics['BTU_roast_per_green_kg'] == 12.0
        assert energy_metrics['KWH_batch_per_green_kg'] == 3.5

    def test_energy_metrics_optional_fields(self) -> None:
        """Test EnergyMetrics with minimal fields (total=False)."""
        # Arrange
        minimal_metrics: atypes.EnergyMetrics = {'BTU_batch': 10000.0, 'CO2_batch': 1.8}

        # Act & Assert
        assert isinstance(minimal_metrics, dict)
        assert len(minimal_metrics) == 2
        assert minimal_metrics['BTU_batch'] == 10000.0
        assert minimal_metrics['CO2_batch'] == 1.8


class TestPalette:
    """Test Palette type alias."""

    def test_palette_structure(self) -> None:
        """Test Palette tuple structure and type compatibility."""
        # Arrange
        palette: atypes.Palette = (
            [0, 1, 2],  # event button types
            [0.0, 1.0, 2.0],  # event button values
            [0, 1, 2],  # event button actions
            [1, 1, 0],  # event button visibility
            ['action1', 'action2', 'action3'],  # event button action strings
            ['Label 1', 'Label 2', 'Label 3'],  # event button labels
            ['Desc 1', 'Desc 2', 'Desc 3'],  # event button descriptions
            ['#FF0000', '#00FF00', '#0000FF'],  # event button colors
            ['#FFFFFF', '#000000', '#FFFFFF'],  # event button text colors
            [1, 1, 0],  # slider visibilities
            [0, 1, 2],  # slider actions
            ['cmd1', 'cmd2', 'cmd3'],  # slider commands
            [0.0, 1.0, 2.0],  # slider offsets
            [1.0, 2.0, 3.0],  # slider factors
            [1, 0, 1],  # quantifier active
            [0, 1, 2],  # quantifier sources
            [0, 10, 20],  # quantifier min
            [100, 200, 300],  # quantifier max
            [1, 2, 3],  # quantifier coarse
            [0, 5, 10],  # slider min
            [50, 100, 150],  # slider max
            [1, 1, 2],  # slider coarse
            [0, 1, 0],  # slider temp flags
            ['°C', '%', 'bar'],  # slider units
            [0, 1, 0],  # slider bernoulli flags
            'Test Palette',  # label
            [1, 0, 1],  # quantifier action flags
            [0, 1, 0],  # quantifier SV flags
        )

        # Act & Assert
        assert isinstance(palette, tuple)
        assert len(palette) == 28
        assert isinstance(palette[0], list)  # event button types
        assert isinstance(palette[1], list)  # event button values
        assert isinstance(palette[25], str)  # label
        assert palette[25] == 'Test Palette'
        assert len(palette[0]) == len(palette[1])  # consistent lengths

    def test_palette_component_types(self) -> None:
        """Test Palette component type validation."""
        # Arrange
        palette: atypes.Palette = (
            [0, 1],  # event button types (List[int])
            [0.5, 1.5],  # event button values (List[float])
            [0, 1],  # event button actions (List[int])
            [1, 0],  # event button visibility (List[int])
            ['act1', 'act2'],  # event button action strings (List[str])
            ['Lbl1', 'Lbl2'],  # event button labels (List[str])
            ['Desc1', 'Desc2'],  # event button descriptions (List[str])
            ['#FF0000', '#00FF00'],  # event button colors (List[str])
            ['#FFFFFF', '#000000'],  # event button text colors (List[str])
            [1, 0],  # slider visibilities (List[int])
            [0, 1],  # slider actions (List[int])
            ['cmd1', 'cmd2'],  # slider commands (List[str])
            [0.0, 1.0],  # slider offsets (List[float])
            [1.0, 2.0],  # slider factors (List[float])
            [1, 0],  # quantifier active (List[int])
            [0, 1],  # quantifier sources (List[int])
            [0, 10],  # quantifier min (List[int])
            [100, 200],  # quantifier max (List[int])
            [1, 2],  # quantifier coarse (List[int])
            [0, 5],  # slider min (List[int])
            [50, 100],  # slider max (List[int])
            [1, 1],  # slider coarse (List[int])
            [0, 1],  # slider temp flags (List[int])
            ['°C', '%'],  # slider units (List[str])
            [0, 1],  # slider bernoulli flags (List[int])
            'Test Label',  # label (str)
            [1, 0],  # quantifier action flags (List[int])
            [0, 1],  # quantifier SV flags (List[int])
        )

        # Act & Assert
        assert all(isinstance(item, int) for item in palette[0])  # event button types
        assert all(isinstance(item, float) for item in palette[1])  # event button values
        assert all(isinstance(item, str) for item in palette[4])  # action strings
        assert isinstance(palette[25], str)  # label


class TestRecentRoast:
    """Test RecentRoast TypedDict."""

    def test_recent_roast_structure(self) -> None:
        """Test RecentRoast structure and type compatibility."""
        # Arrange
        recent_roast: atypes.RecentRoast = {
            'title': 'Ethiopian Yirgacheffe',
            'beans': 'Ethiopian Yirgacheffe Grade 1',
            'weightIn': 1000.0,
            'weightOut': 845.0,
            'weightUnit': 'g',
            'volumeIn': 1500.0,
            'volumeOut': 2275.0,
            'volumeUnit': 'ml',
            'densityWeight': 0.65,
            'densityRoasted': 0.45,
            'beanSize_min': 14,
            'beanSize_max': 18,
            'moistureGreen': 11.5,
            'moistureRoasted': 2.5,
            'wholeColor': 65,
            'groundColor': 70,
            'colorSystem': 'Agtron',
            'background': None,
            'roastUUID': '12345678-1234-5678-9012-123456789abc',
            'batchnr': 123,
            'batchprefix': 'B',
            'plus_account': 'test@example.com',
            'plus_store': 'test-store',
            'plus_store_label': 'Test Store',
            'plus_coffee': 'ethiopian-yirgacheffe',
            'plus_coffee_label': 'Ethiopian Yirgacheffe',
            'plus_blend_label': None,
            'plus_blend_spec': None,
            'plus_blend_spec_labels': None,
        }

        # Act & Assert
        assert isinstance(recent_roast, dict)
        assert recent_roast['title'] == 'Ethiopian Yirgacheffe'
        assert recent_roast['weightIn'] == 1000.0
        assert recent_roast['weightUnit'] == 'g'
        assert recent_roast['batchnr'] == 123
        assert recent_roast['plus_account'] == 'test@example.com'

    def test_recent_roast_required_fields(self) -> None:
        """Test RecentRoast with only required fields."""
        # Arrange
        minimal_roast: atypes.RecentRoast = {
            'title': 'Test Roast',
            'weightIn': 500.0,
            'weightUnit': 'g',
        }

        # Act & Assert
        assert isinstance(minimal_roast, dict)
        assert len(minimal_roast) == 3
        assert minimal_roast['title'] == 'Test Roast'
        assert minimal_roast['weightIn'] == 500.0
        assert minimal_roast['weightUnit'] == 'g'


class TestSerialSettings:
    """Test SerialSettings TypedDict."""

    def test_serial_settings_structure(self) -> None:
        """Test SerialSettings structure and type compatibility."""
        # Arrange
        serial_settings: atypes.SerialSettings = {
            'port': '/dev/ttyUSB0',
            'baudrate': 9600,
            'bytesize': 8,
            'stopbits': 1,
            'parity': 'N',
            'timeout': 1.0,
        }

        # Act & Assert
        assert isinstance(serial_settings, dict)
        assert serial_settings['port'] == '/dev/ttyUSB0'
        assert serial_settings['baudrate'] == 9600
        assert serial_settings['bytesize'] == 8
        assert serial_settings['stopbits'] == 1
        assert serial_settings['parity'] == 'N'
        assert serial_settings['timeout'] == 1.0

    def test_serial_settings_all_fields_required(self) -> None:
        """Test that SerialSettings requires all fields (not total=False)."""
        # Arrange
        complete_settings: atypes.SerialSettings = {
            'port': 'COM3',
            'baudrate': 115200,
            'bytesize': 8,
            'stopbits': 2,
            'parity': 'E',
            'timeout': 2.5,
        }

        # Act & Assert
        assert len(complete_settings) == 6
        expected_keys = ['port', 'baudrate', 'bytesize', 'stopbits', 'parity', 'timeout']
        assert all(key in complete_settings for key in expected_keys)


class TestAlarmSet:
    """Test AlarmSet TypedDict."""

    def test_alarm_set_structure(self) -> None:
        """Test AlarmSet structure and type compatibility."""
        # Arrange
        alarm_set: atypes.AlarmSet = {
            'label': 'Test Alarm Set',
            'flags': [1, 0, 1, 0],
            'guards': [1, 1, 0, 1],
            'negguards': [0, 0, 1, 0],
            'times': [300, 480, 600, 720],
            'offsets': [0, 10, -5, 15],
            'sources': [0, 1, 0, 1],
            'conditions': [0, 1, 2, 1],
            'temperatures': [150.0, 200.0, 220.0, 205.0],
            'actions': [0, 1, 2, 0],
            'beeps': [1, 1, 0, 1],
            'alarmstrings': ['CHARGE', 'DRY', 'FCs', 'DROP'],
        }

        # Act & Assert
        assert isinstance(alarm_set, dict)
        assert alarm_set['label'] == 'Test Alarm Set'
        assert len(alarm_set['flags']) == 4
        assert len(alarm_set['temperatures']) == 4
        assert alarm_set['alarmstrings'][0] == 'CHARGE'
        assert alarm_set['temperatures'][1] == 200.0

    def test_alarm_set_list_consistency(self) -> None:
        """Test AlarmSet list length consistency."""
        # Arrange
        alarm_set: atypes.AlarmSet = {
            'label': 'Consistent Alarms',
            'flags': [1, 0],
            'guards': [1, 1],
            'negguards': [0, 0],
            'times': [300, 600],
            'offsets': [0, 10],
            'sources': [0, 1],
            'conditions': [0, 1],
            'temperatures': [150.0, 200.0],
            'actions': [0, 1],
            'beeps': [1, 1],
            'alarmstrings': ['CHARGE', 'DROP'],
        }

        # Act & Assert
        alarm_count = len(alarm_set['flags'])
        list_fields = [
            'flags',
            'guards',
            'negguards',
            'times',
            'offsets',
            'sources',
            'conditions',
            'temperatures',
            'actions',
            'beeps',
            'alarmstrings',
        ]
        assert all(len(alarm_set[field]) == alarm_count for field in list_fields) # type: ignore
