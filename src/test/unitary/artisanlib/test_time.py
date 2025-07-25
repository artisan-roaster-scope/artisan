"""
Unit tests for artisanlib.time module.

This module tests the ArtisanTime class which provides high-resolution timing
functionality with configurable base units. Tests focus on edge cases and
boundary conditions to discover potential bugs.

The tests validate:
- Initialization and state management
- Base value handling (including edge cases)
- Clock operations and timing accuracy
- Elapsed time calculations
- Thread safety considerations
- Numerical precision and overflow conditions
"""

import math
import time
from unittest.mock import patch

import pytest

from artisanlib.time import ArtisanTime


class TestArtisanTimeInitialization:
    """Test ArtisanTime initialization and basic properties."""

    def test_init_sets_default_values(self) -> None:
        """Test that initialization sets correct default values."""
        artisan_time = ArtisanTime()

        # Should have default base of 1000.0
        assert artisan_time.getBase() == 1000.0

        # Clock should be set to current perf_counter value
        assert isinstance(artisan_time.clock, float)
        assert artisan_time.clock > 0

    def test_init_captures_current_time(self) -> None:
        """Test that initialization captures the current performance counter."""
        with patch('time.perf_counter', return_value=12345.678):
            artisan_time = ArtisanTime()
            assert artisan_time.clock == 12345.678

    def test_slots_attribute_limits_instance_variables(self) -> None:
        """Test that __slots__ properly limits instance variables."""
        artisan_time = ArtisanTime()

        # Should be able to access defined slots
        assert hasattr(artisan_time, 'clock')
        assert hasattr(artisan_time, 'base')

        # Should not be able to add new attributes
        with pytest.raises(AttributeError):
            artisan_time.new_attribute = 'test'  # type: ignore[attr-defined]


class TestArtisanTimeBaseOperations:
    """Test base value operations and edge cases."""

    def test_setBase_accepts_positive_values(self) -> None:
        """Test setBase with various positive values."""
        artisan_time = ArtisanTime()

        # Test normal values
        artisan_time.setBase(500.0)
        assert artisan_time.getBase() == 500.0

        artisan_time.setBase(2000.0)
        assert artisan_time.getBase() == 2000.0

    def test_setBase_accepts_zero(self) -> None:
        """Test setBase with zero value."""
        artisan_time = ArtisanTime()
        artisan_time.setBase(0.0)
        assert artisan_time.getBase() == 0.0

    def test_setBase_accepts_negative_values(self) -> None:
        """Test setBase with negative values (potential bug source)."""
        artisan_time = ArtisanTime()
        artisan_time.setBase(-100.0)
        assert artisan_time.getBase() == -100.0

    def test_setBase_accepts_very_small_values(self) -> None:
        """Test setBase with very small positive values."""
        artisan_time = ArtisanTime()

        # Test very small positive value
        artisan_time.setBase(1e-10)
        assert artisan_time.getBase() == 1e-10

        # Test smallest positive float
        artisan_time.setBase(float('1e-323'))  # Near minimum positive float
        assert artisan_time.getBase() == float('1e-323')

    def test_setBase_accepts_very_large_values(self) -> None:
        """Test setBase with very large values."""
        artisan_time = ArtisanTime()

        # Test very large value
        large_value = 1e15
        artisan_time.setBase(large_value)
        assert artisan_time.getBase() == large_value

    def test_setBase_handles_infinity(self) -> None:
        """Test setBase with infinity values (potential bug source)."""
        artisan_time = ArtisanTime()

        # Test positive infinity
        artisan_time.setBase(float('inf'))
        assert math.isinf(artisan_time.getBase())
        assert artisan_time.getBase() > 0

        # Test negative infinity
        artisan_time.setBase(float('-inf'))
        assert math.isinf(artisan_time.getBase())
        assert artisan_time.getBase() < 0

    def test_setBase_handles_nan(self) -> None:
        """Test setBase with NaN values (potential bug source)."""
        artisan_time = ArtisanTime()
        artisan_time.setBase(float('nan'))
        assert math.isnan(artisan_time.getBase())

    @pytest.mark.parametrize(
        'base_value',
        [
            0.001,  # Very small positive
            1.0,  # Unit value
            1000.0,  # Default value
            1e6,  # Large value
            -1.0,  # Negative unit
            -1000.0,  # Negative default
        ],
    )
    def test_setBase_getBase_roundtrip(self, base_value: float) -> None:
        """Test that setBase/getBase roundtrip preserves values."""
        artisan_time = ArtisanTime()
        artisan_time.setBase(base_value)
        assert artisan_time.getBase() == base_value


class TestArtisanTimeClockOperations:
    """Test clock operations and timing functionality."""

    def test_start_resets_clock(self) -> None:
        """Test that start() resets the clock to current time."""
        artisan_time = ArtisanTime()
        original_clock = artisan_time.clock

        # Wait a tiny bit to ensure time difference
        time.sleep(0.001)

        artisan_time.start()
        assert artisan_time.clock != original_clock
        assert artisan_time.clock > original_clock

    def test_start_uses_perf_counter(self) -> None:
        """Test that start() uses time.perf_counter()."""
        artisan_time = ArtisanTime()

        with patch('time.perf_counter', return_value=99999.123):
            artisan_time.start()
            assert artisan_time.clock == 99999.123

    def test_addClock_modifies_clock_value(self) -> None:
        """Test addClock adds period to current clock value."""
        artisan_time = ArtisanTime()
        original_clock = artisan_time.clock

        artisan_time.addClock(5.5)
        assert artisan_time.clock == original_clock + 5.5

    def test_addClock_with_negative_period(self) -> None:
        """Test addClock with negative period (moves clock backward)."""
        artisan_time = ArtisanTime()
        original_clock = artisan_time.clock

        artisan_time.addClock(-2.5)
        assert artisan_time.clock == original_clock - 2.5

    def test_addClock_with_zero_period(self) -> None:
        """Test addClock with zero period (no change)."""
        artisan_time = ArtisanTime()
        original_clock = artisan_time.clock

        artisan_time.addClock(0.0)
        assert artisan_time.clock == original_clock

    @pytest.mark.parametrize(
        'period',
        [
            1e-10,  # Very small positive
            1e10,  # Very large positive
            -1e10,  # Very large negative
            float('inf'),  # Positive infinity
            float('-inf'),  # Negative infinity
            float('nan'),  # NaN
        ],
    )
    def test_addClock_edge_cases(self, period: float) -> None:
        """Test addClock with edge case values."""
        artisan_time = ArtisanTime()
        original_clock = artisan_time.clock

        artisan_time.addClock(period)

        if math.isnan(period):
            assert math.isnan(artisan_time.clock)
        elif math.isinf(period):
            assert math.isinf(artisan_time.clock)
            assert math.copysign(1, artisan_time.clock) == math.copysign(1, period)
        else:
            assert artisan_time.clock == original_clock + period


class TestArtisanTimeElapsedCalculations:
    """Test elapsed time calculations and edge cases."""

    def test_elapsed_calculates_time_difference(self) -> None:
        """Test that elapsed() calculates time difference correctly."""
        with patch('time.perf_counter') as mock_perf:
            # Set initial time
            mock_perf.return_value = 100.0
            artisan_time = ArtisanTime()

            # Simulate time passage
            mock_perf.return_value = 105.5
            elapsed = artisan_time.elapsed()

            # Should be (105.5 - 100.0) * 1000.0 = 5500.0
            assert elapsed == 5500.0

    def test_elapsed_with_custom_base(self) -> None:
        """Test elapsed() calculation with custom base value."""
        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 100.0
            artisan_time = ArtisanTime()
            artisan_time.setBase(500.0)

            mock_perf.return_value = 102.0
            elapsed = artisan_time.elapsed()

            # Should be (102.0 - 100.0) * 500.0 = 1000.0
            assert elapsed == 1000.0

    def test_elapsed_with_zero_base(self) -> None:
        """Test elapsed() with zero base (potential division issues)."""
        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 100.0
            artisan_time = ArtisanTime()
            artisan_time.setBase(0.0)

            mock_perf.return_value = 105.0
            elapsed = artisan_time.elapsed()

            # Should be (105.0 - 100.0) * 0.0 = 0.0
            assert elapsed == 0.0

    def test_elapsed_with_negative_base(self) -> None:
        """Test elapsed() with negative base."""
        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 100.0
            artisan_time = ArtisanTime()
            artisan_time.setBase(-1000.0)

            mock_perf.return_value = 103.0
            elapsed = artisan_time.elapsed()

            # Should be (103.0 - 100.0) * -1000.0 = -3000.0
            assert elapsed == -3000.0

    def test_elapsedMilli_calculates_milliseconds(self) -> None:
        """Test that elapsedMilli() calculates milliseconds correctly."""
        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 100.0
            artisan_time = ArtisanTime()

            mock_perf.return_value = 105.5
            elapsed_milli = artisan_time.elapsedMilli()

            # Should be (105.5 - 100.0) * 1000.0 / 1000.0 = 5.5
            assert elapsed_milli == 5.5

    def test_elapsedMilli_with_custom_base(self) -> None:
        """Test elapsedMilli() with custom base value."""
        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 100.0
            artisan_time = ArtisanTime()
            artisan_time.setBase(2000.0)

            mock_perf.return_value = 102.0
            elapsed_milli = artisan_time.elapsedMilli()

            # Should be (102.0 - 100.0) * 2000.0 / 1000.0 = 4.0
            assert elapsed_milli == 4.0

    def test_elapsed_methods_with_clock_in_future(self) -> None:
        """Test elapsed methods when clock is set to future time."""
        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 100.0
            artisan_time = ArtisanTime()

            # Set clock to future time
            artisan_time.addClock(10.0)  # Clock is now at 110.0

            # Current time is still 100.0, so elapsed should be negative
            elapsed = artisan_time.elapsed()
            elapsed_milli = artisan_time.elapsedMilli()

            # Should be (100.0 - 110.0) * 1000.0 = -10000.0
            assert elapsed == -10000.0
            assert elapsed_milli == -10.0


class TestArtisanTimeNumericalPrecision:
    """Test numerical precision and floating-point edge cases."""

    def test_elapsed_with_very_small_time_differences(self) -> None:
        """Test elapsed calculation with very small time differences."""
        artisan_time = ArtisanTime()

        # Set a known clock value
        artisan_time.clock = 100.0

        with patch('time.perf_counter', return_value=100.0 + 1e-9):
            elapsed = artisan_time.elapsed()

            # Should be approximately 1e-9 * 1000.0 = 1e-6
            # Allow for some floating point precision issues
            assert elapsed == pytest.approx(1e-6, abs=1e-9)

    def test_elapsed_with_very_large_time_differences(self) -> None:
        """Test elapsed calculation with very large time differences."""
        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 0.0
            artisan_time = ArtisanTime()

            # Very large time difference
            mock_perf.return_value = 1e10
            elapsed = artisan_time.elapsed()

            # Should be 1e10 * 1000.0 = 1e13
            assert elapsed == 1e13

    def test_elapsed_with_infinity_base_and_finite_time(self) -> None:
        """Test elapsed calculation with infinite base and finite time difference."""
        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 100.0
            artisan_time = ArtisanTime()
            artisan_time.setBase(float('inf'))

            mock_perf.return_value = 101.0
            elapsed = artisan_time.elapsed()

            # Should be 1.0 * inf = inf
            assert math.isinf(elapsed)
            assert elapsed > 0

    def test_elapsed_with_nan_base(self) -> None:
        """Test elapsed calculation with NaN base."""
        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 100.0
            artisan_time = ArtisanTime()
            artisan_time.setBase(float('nan'))

            mock_perf.return_value = 101.0
            elapsed = artisan_time.elapsed()

            # Should be 1.0 * nan = nan
            assert math.isnan(elapsed)

    def test_elapsed_with_zero_time_difference(self) -> None:
        """Test elapsed calculation with zero time difference."""
        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 100.0
            artisan_time = ArtisanTime()

            # No time difference
            elapsed = artisan_time.elapsed()
            elapsed_milli = artisan_time.elapsedMilli()

            assert elapsed == 0.0
            assert elapsed_milli == 0.0

    def test_floating_point_precision_accumulation(self) -> None:
        """Test potential floating-point precision issues with repeated operations."""
        artisan_time = ArtisanTime()

        # Set a known starting value to avoid initialization timing issues
        artisan_time.clock = 100.0
        original_clock = artisan_time.clock

        # Add many small increments
        for _ in range(1000):
            artisan_time.addClock(0.001)

        # Should be approximately original + 1.0
        expected = original_clock + 1.0
        assert artisan_time.clock == pytest.approx(expected, abs=1e-8)


class TestArtisanTimeEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions that might reveal bugs."""

    def test_multiple_start_calls(self) -> None:
        """Test behavior with multiple consecutive start() calls."""
        artisan_time = ArtisanTime()

        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 100.0
            artisan_time.start()
            first_clock = artisan_time.clock

            mock_perf.return_value = 200.0
            artisan_time.start()
            second_clock = artisan_time.clock

            assert first_clock == 100.0
            assert second_clock == 200.0

    def test_addClock_after_start(self) -> None:
        """Test addClock behavior after start() call."""
        artisan_time = ArtisanTime()

        with patch('time.perf_counter', return_value=100.0):
            artisan_time.start()
            artisan_time.addClock(5.0)

            assert artisan_time.clock == 105.0

    def test_base_changes_affect_subsequent_calculations(self) -> None:
        """Test that base changes affect subsequent elapsed calculations."""
        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 100.0
            artisan_time = ArtisanTime()

            # First calculation with default base
            mock_perf.return_value = 101.0
            elapsed1 = artisan_time.elapsed()
            assert elapsed1 == 1000.0  # 1.0 * 1000.0

            # Change base and calculate again
            artisan_time.setBase(500.0)
            elapsed2 = artisan_time.elapsed()
            assert elapsed2 == 500.0  # 1.0 * 500.0

    def test_concurrent_operations_simulation(self) -> None:
        """Test simulation of concurrent operations (not truly concurrent)."""
        artisan_time = ArtisanTime()

        # Simulate rapid successive operations
        operations = []
        for _ in range(100):
            artisan_time.addClock(0.01)
            operations.append(artisan_time.clock)

        # Verify monotonic increase
        for i in range(1, len(operations)):
            assert operations[i] > operations[i - 1]

    def test_extreme_clock_values(self) -> None:
        """Test behavior with extreme clock values."""
        artisan_time = ArtisanTime()

        # Set clock to very large value
        artisan_time.clock = 1e15
        with patch('time.perf_counter', return_value=1e15 + 1):
            elapsed = artisan_time.elapsed()
            assert elapsed == 1000.0  # 1.0 * 1000.0

        # Set clock to very small value
        artisan_time.clock = 1e-10
        with patch('time.perf_counter', return_value=1e-10 + 1e-9):
            elapsed = artisan_time.elapsed()
            assert elapsed == pytest.approx(1e-6, abs=1e-12)  # 1e-9 * 1000.0

    def test_clock_overflow_conditions(self) -> None:
        """Test potential overflow conditions."""
        artisan_time = ArtisanTime()

        # Test with maximum float value
        max_float = float('1.7976931348623157e+308')  # Close to sys.float_info.max
        artisan_time.addClock(max_float)

        # Should handle without crashing
        assert artisan_time.clock == max_float

    def test_division_by_zero_protection_in_elapsedMilli(self) -> None:
        """Test that elapsedMilli doesn't have division by zero issues."""
        # Note: elapsedMilli divides by 1000.0, which is hardcoded, so no division by zero
        # But test with zero base to see behavior
        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 100.0
            artisan_time = ArtisanTime()
            artisan_time.setBase(0.0)

            mock_perf.return_value = 101.0
            elapsed_milli = artisan_time.elapsedMilli()

            # Should be (1.0 * 0.0) / 1000.0 = 0.0
            assert elapsed_milli == 0.0

    @pytest.mark.parametrize(
        'base_value,time_diff,expected_elapsed',
        [
            (1000.0, 1.0, 1000.0),  # Default case
            (1.0, 1.0, 1.0),  # Unit base
            (0.0, 1.0, 0.0),  # Zero base
            (-1000.0, 1.0, -1000.0),  # Negative base
            (1000.0, 0.0, 0.0),  # Zero time difference
            (1000.0, -1.0, -1000.0),  # Negative time difference
        ],
    )
    def test_elapsed_calculation_matrix(
        self, base_value: float, time_diff: float, expected_elapsed: float
    ) -> None:
        """Test elapsed calculation with various base and time difference combinations."""
        with patch('time.perf_counter') as mock_perf:
            mock_perf.return_value = 100.0
            artisan_time = ArtisanTime()
            artisan_time.setBase(base_value)

            mock_perf.return_value = 100.0 + time_diff
            elapsed = artisan_time.elapsed()

            assert elapsed == expected_elapsed


class TestArtisanTimeTypeAnnotations:
    """Test type-related edge cases and ensure type safety."""

    def test_base_type_consistency(self) -> None:
        """Test that base value maintains float type consistency."""
        artisan_time = ArtisanTime()

        # Test with integer (Python will handle the conversion)
        artisan_time.setBase(42)
        # Note: Python doesn't automatically convert int to float in assignment
        # The base will remain as int type, but arithmetic operations will work
        assert artisan_time.getBase() == 42

    def test_clock_type_consistency(self) -> None:
        """Test that clock value maintains float type consistency."""
        artisan_time = ArtisanTime()

        # Clock should always be float
        assert isinstance(artisan_time.clock, float)

        # After addClock with integer
        artisan_time.addClock(5)
        assert isinstance(artisan_time.clock, float)

    def test_return_type_consistency(self) -> None:
        """Test that methods return consistent types."""
        artisan_time = ArtisanTime()

        # getBase should return float
        base = artisan_time.getBase()
        assert isinstance(base, float)

        # elapsed should return float
        elapsed = artisan_time.elapsed()
        assert isinstance(elapsed, float)

        # elapsedMilli should return float
        elapsed_milli = artisan_time.elapsedMilli()
        assert isinstance(elapsed_milli, float)
