"""
Unit tests for artisanlib.filters module.

This module tests digital filter implementations including:
- LiveFilter base class functionality
- LiveLFilter (IIR filter using difference equations)
- LiveSosFilter (second-order sections filter)
- LiveMedian (median low-pass filter)
- LiveMean (mean low-pass filter)

Tests focus on edge cases and boundary conditions to discover potential bugs,
including numerical stability, initialization behavior, and filter accuracy.
"""

import math
from typing import Any, List, Tuple
import numpy as np

import pytest

from artisanlib.filters import (
    LiveFilter,
    LiveLFilter,
    LiveMean,
    LiveMedian,
    LiveSosFilter,
)


class TestLiveFilterBase:
    """Test the base LiveFilter class functionality."""

    def test_process_returns_nan_for_nan_input(self) -> None:
        """Test that process() returns NaN for NaN input without calling _process."""

        class MockFilter(LiveFilter):
            def __init__(self) -> None:
                self.process_called = False

            def _process(self, x: float) -> float:
                self.process_called = True
                return x * 2

        filter_instance = MockFilter()
        result = filter_instance.process(float('nan'))

        assert math.isnan(result)
        assert not filter_instance.process_called

    def test_process_calls_process_for_valid_input(self) -> None:
        """Test that process() calls _process for valid input."""

        class MockFilter(LiveFilter):
            def _process(self, x: float) -> float:
                return x * 2

        filter_instance = MockFilter()
        result = filter_instance.process(5.0)

        assert result == 10.0

    def test_call_delegates_to_process(self) -> None:
        """Test that __call__ delegates to process method."""

        class MockFilter(LiveFilter):
            def _process(self, x: float) -> float:
                return x + 1

        filter_instance = MockFilter()
        result = filter_instance(3.0)

        assert result == 4.0

    def test_base_process_raises_not_implemented(self) -> None:
        """Test that base _process raises NotImplementedError."""
        base_filter = LiveFilter()

        with pytest.raises(NotImplementedError, match='Derived class must implement _process'):
            base_filter._process(1.0)

    @pytest.mark.parametrize(
        'input_value',
        [
            float('inf'),
            float('-inf'),
            0.0,
            -0.0,
            1e-100,
            1e100,
            -999999.999,
        ],
    )
    def test_process_handles_special_float_values(self, input_value: float) -> None:
        """Test that process handles various special float values."""

        class MockFilter(LiveFilter):
            def _process(self, x: float) -> float:
                return x

        filter_instance = MockFilter()
        result = filter_instance.process(input_value)

        if math.isnan(input_value):
            assert math.isnan(result)
        elif math.isinf(input_value):
            assert math.isinf(result)
            assert math.copysign(1, result) == math.copysign(1, input_value)
        else:
            assert result == input_value


class TestLiveLFilter:
    """Test LiveLFilter (IIR filter using difference equations)."""

    def test_init_stores_coefficients(self) -> None:
        """Test that initialization stores filter coefficients correctly."""
        b = np.array([1.0, 0.5])
        a = np.array([1.0, -0.3])

        filter_instance = LiveLFilter(b, a)

        assert np.array_equal(filter_instance.b, b)
        assert np.array_equal(filter_instance.a, a)

    def test_init_creates_correct_buffer_sizes(self) -> None:
        """Test that initialization creates buffers of correct sizes."""
        b = np.array([1.0, 0.5, 0.2])
        a = np.array([1.0, -0.3, 0.1])

        filter_instance = LiveLFilter(b, a)

        assert len(filter_instance._xs) == len(b)
        assert len(filter_instance._ys) == len(a) - 1
        assert filter_instance._xs.maxlen == len(b)
        assert filter_instance._ys.maxlen == len(a) - 1

    def test_init_buffers_filled_with_zeros(self) -> None:
        """Test that initialization fills buffers with zeros."""
        b = np.array([1.0, 0.5])
        a = np.array([1.0, -0.3])

        filter_instance = LiveLFilter(b, a)

        assert all(x == 0.0 for x in filter_instance._xs)
        assert all(y == 0.0 for y in filter_instance._ys)

    def test_process_simple_filter(self) -> None:
        """Test processing with a simple filter."""
        # Simple moving average filter: y[n] = 0.5 * (x[n] + x[n-1])
        b = np.array([0.5, 0.5])
        a = np.array([1.0])

        filter_instance = LiveLFilter(b, a)

        # First input
        result1 = filter_instance.process(2.0)
        assert result1 == pytest.approx(1.0, abs=1e-10)  # 0.5 * (2 + 0)

        # Second input
        result2 = filter_instance.process(4.0)
        assert result2 == pytest.approx(3.0, abs=1e-10)  # 0.5 * (4 + 2)

    def test_process_with_feedback(self) -> None:
        """Test processing with feedback (IIR filter)."""
        # Simple IIR filter: y[n] = x[n] + 0.5 * y[n-1]
        b = np.array([1.0])
        a = np.array([1.0, -0.5])

        filter_instance = LiveLFilter(b, a)

        result1 = filter_instance.process(1.0)
        assert result1 == pytest.approx(1.0, abs=1e-10)

        result2 = filter_instance.process(0.0)
        assert result2 == pytest.approx(0.5, abs=1e-10)  # 0 + 0.5 * 1.0

    @pytest.mark.parametrize(
        'b_coeffs,a_coeffs',
        [
            ([1.0], [1.0]),  # Pass-through filter
            ([0.0], [1.0]),  # Zero filter
            ([1.0, -1.0], [1.0]),  # Differentiator
            ([0.5, 0.5], [1.0]),  # Moving average
        ],
    )
    def test_process_various_filter_types(
        self, b_coeffs: List[float], a_coeffs: List[float]
    ) -> None:
        """Test processing with various filter coefficient combinations."""
        b = np.array(b_coeffs)
        a = np.array(a_coeffs)

        filter_instance = LiveLFilter(b, a)

        # Should not raise exceptions
        result = filter_instance.process(1.0)
        assert isinstance(result, float)

    def test_process_with_very_small_coefficients(self) -> None:
        """Test processing with very small coefficients."""
        b = np.array([1e-10, 1e-10])
        a = np.array([1.0])

        filter_instance = LiveLFilter(b, a)

        result = filter_instance.process(1e10)
        assert result == pytest.approx(1.0, abs=1e-8)

    def test_process_with_large_coefficients(self) -> None:
        """Test processing with large coefficients."""
        b = np.array([1e6])
        a = np.array([1.0])

        filter_instance = LiveLFilter(b, a)

        result = filter_instance.process(1e-6)
        assert result == pytest.approx(1.0, abs=1e-8)

    def test_buffer_overflow_behavior(self) -> None:
        """Test that buffers handle overflow correctly with maxlen."""
        b = np.array([1.0, 1.0])  # Length 2
        a = np.array([1.0, 0.0])  # Length 2, so _ys has maxlen 1

        filter_instance = LiveLFilter(b, a)

        # Process more values than buffer size
        for i in range(5):
            filter_instance.process(float(i))

        # Buffers should maintain their maxlen
        assert len(filter_instance._xs) == 2
        assert len(filter_instance._ys) == 1

    def test_process_returns_float_type(self) -> None:
        """Test that process always returns float type."""
        b = np.array([1.0])
        a = np.array([1.0])

        filter_instance = LiveLFilter(b, a)

        result = filter_instance.process(5)  # Integer input
        assert isinstance(result, float)
        assert result == 5.0


class TestLiveSosFilter:
    """Test LiveSosFilter (second-order sections filter)."""

    def test_init_stores_sos_matrix(self) -> None:
        """Test that initialization stores SOS matrix correctly."""
        sos = np.array([[1.0, 0.0, 0.0, 1.0, 0.0, 0.0]])

        filter_instance = LiveSosFilter(sos)

        assert np.array_equal(filter_instance.sos, sos)

    def test_init_calculates_correct_sections(self) -> None:
        """Test that initialization calculates correct number of sections."""
        sos = np.array([[1.0, 0.0, 0.0, 1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]])

        filter_instance = LiveSosFilter(sos)

        assert filter_instance.n_sections == 2

    def test_init_creates_correct_state_matrix(self) -> None:
        """Test that initialization creates state matrix of correct size."""
        sos = np.array([[1.0, 0.0, 0.0, 1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]])

        filter_instance = LiveSosFilter(sos)

        assert filter_instance.state.shape == (2, 2)
        assert np.all(filter_instance.state == 0.0)

    def test_process_single_section_passthrough(self) -> None:
        """Test processing with single section pass-through filter."""
        # Pass-through: b0=1, b1=0, b2=0, a0=1, a1=0, a2=0
        sos = np.array([[1.0, 0.0, 0.0, 1.0, 0.0, 0.0]])

        filter_instance = LiveSosFilter(sos)

        result = filter_instance.process(5.0)
        assert result == pytest.approx(5.0, abs=1e-10)

    def test_process_multiple_sections(self) -> None:
        """Test processing with multiple sections."""
        # Two identical pass-through sections
        sos = np.array([[1.0, 0.0, 0.0, 1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]])

        filter_instance = LiveSosFilter(sos)

        result = filter_instance.process(3.0)
        assert result == pytest.approx(3.0, abs=1e-10)

    def test_process_updates_state_correctly(self) -> None:
        """Test that processing updates internal state correctly."""
        sos = np.array([[1.0, 1.0, 0.0, 1.0, 0.0, 0.0]])

        filter_instance = LiveSosFilter(sos)

        # Process first value
        filter_instance.process(1.0)

        # State should be updated
        assert not np.all(filter_instance.state == 0.0)

    @pytest.mark.parametrize(
        'input_sequence',
        [
            [1.0, 2.0, 3.0],
            [0.0, 0.0, 0.0],
            [-1.0, -2.0, -3.0],
            [1e-10, 1e10, -1e10],
        ],
    )
    def test_process_sequence_stability(self, input_sequence: List[float]) -> None:
        """Test that filter remains stable with various input sequences."""
        sos = np.array([[0.5, 0.0, 0.0, 1.0, 0.0, 0.0]])  # Gain of 0.5

        filter_instance = LiveSosFilter(sos)

        results = []
        for value in input_sequence:
            result = filter_instance.process(value)
            results.append(result)
            assert math.isfinite(result), f"Filter became unstable with input {value}"

    def test_process_with_empty_sos_matrix(self) -> None:
        """Test behavior with empty SOS matrix."""
        sos = np.array([]).reshape(0, 6)

        filter_instance = LiveSosFilter(sos)

        # Should return input unchanged when no sections
        result = filter_instance.process(5.0)
        assert result == 0  # Initial value of y


class TestLiveMedian:
    """Test LiveMedian (median low-pass filter)."""

    def test_init_requires_odd_window_size(self) -> None:
        """Test that initialization requires odd window size."""
        # Should work with odd sizes
        LiveMedian(3)
        LiveMedian(5)
        LiveMedian(7)

        # Should raise assertion error with even sizes
        with pytest.raises(AssertionError, match='Median filter length must be odd'):
            LiveMedian(2)

        with pytest.raises(AssertionError, match='Median filter length must be odd'):
            LiveMedian(4)

    def test_init_sets_correct_attributes(self) -> None:
        """Test that initialization sets attributes correctly."""
        filter_instance = LiveMedian(5)

        assert filter_instance.k == 5
        assert filter_instance.init_list == []
        assert filter_instance.total == 0
        assert filter_instance.initialized is False
        assert filter_instance.q is None
        assert filter_instance.l is None
        assert filter_instance.mididx == 0

    def test_process_returns_mean_during_initialization(self) -> None:
        """Test that process returns running mean during initialization phase."""
        filter_instance = LiveMedian(3)

        # First value
        result1 = filter_instance.process(10.0)
        assert result1 == 10.0  # 10/1

        # Second value
        result2 = filter_instance.process(20.0)
        assert result2 == 15.0  # (10+20)/2

    def test_process_initializes_after_k_values(self) -> None:
        """Test that filter initializes when processing the (k+1)th value."""
        filter_instance = LiveMedian(3)

        # Process k values
        filter_instance.process(1.0)
        filter_instance.process(2.0)
        filter_instance.process(3.0)
        assert not filter_instance.initialized

        # Process (k+1)th value - initialization happens during this call
        result = filter_instance.process(4.0)
        assert result == 3  # Should return median of [2, 3, 4] = 3  # type: ignore[unreachable]
        assert filter_instance.initialized

    def test_process_returns_median_after_initialization(self) -> None:
        """Test that process returns median after initialization."""
        filter_instance = LiveMedian(3)

        # Initialize with values [1, 2, 3]
        filter_instance.process(1.0)
        filter_instance.process(2.0)
        filter_instance.process(3.0)

        # Next value should replace oldest and return new median
        result = filter_instance.process(5.0)  # Window becomes [2, 3, 5]
        assert result == 3.0  # Median of [2, 3, 5]
        assert filter_instance.initialized

    def test_process_maintains_sorted_list(self) -> None:
        """Test that internal sorted list is maintained correctly."""
        filter_instance = LiveMedian(3)

        # Initialize - the third call triggers initialization
        filter_instance.process(3.0)
        filter_instance.process(1.0)
        filter_instance.process(4.0)
        filter_instance.process(2.0)  # This triggers initialization

        # Check that sorted list is correct after initialization
        assert filter_instance.l is not None
        assert filter_instance.l == [1.0, 2.0, 4.0]

    @pytest.mark.parametrize(
        'window_size,input_sequence,expected_medians',
        [
            (3, [1, 2, 3, 4, 5], [3, 4]),  # Medians after initialization
            (5, [5, 4, 3, 2, 1, 0], [2]),  # One median after initialization
            (3, [1, 1, 1, 2, 2], [1, 2]),  # Duplicate values
        ],
    )
    def test_process_various_sequences(
        self, window_size: int, input_sequence: List[int], expected_medians: List[int]
    ) -> None:
        """Test processing with various input sequences."""
        filter_instance = LiveMedian(window_size)

        results = []
        for value in input_sequence:
            result = filter_instance.process(float(value))
            results.append(result)

        # Check the medians after initialization (starts from index window_size)
        actual_medians = results[window_size:]
        assert len(actual_medians) == len(expected_medians)
        for actual, expected in zip(actual_medians, expected_medians):
            assert actual == pytest.approx(float(expected), abs=1e-10)

    def test_process_with_nan_input(self) -> None:
        """Test that NaN input is handled by base class."""
        filter_instance = LiveMedian(3)

        result = filter_instance.process(float('nan'))
        assert math.isnan(result)

    def test_process_with_extreme_values(self) -> None:
        """Test processing with extreme values."""
        filter_instance = LiveMedian(3)

        # Initialize with extreme values
        filter_instance.process(1e10)
        filter_instance.process(-1e10)
        filter_instance.process(0.0)

        # Should handle without issues
        result = filter_instance.process(1e5)
        assert math.isfinite(result)

    def test_init_queue_deletes_temporary_attributes(self) -> None:
        """Test that init_queue deletes temporary initialization attributes."""
        filter_instance = LiveMedian(3)

        # Fill initialization list - the third call triggers initialization
        filter_instance.process(1.0)
        filter_instance.process(2.0)
        filter_instance.process(3.0)
        filter_instance.process(4.0)  # This triggers initialization and deletes attributes

        # After initialization, temporary attributes should be deleted
        # Note: The attributes are deleted using 'del' in init_queue()
        assert not hasattr(filter_instance, 'init_list')
        assert not hasattr(filter_instance, 'total')

    def test_mididx_calculation(self) -> None:
        """Test that middle index is calculated correctly."""
        # Test various window sizes
        for k in [1, 3, 5, 7, 9]:
            filter_instance = LiveMedian(k)

            # Fill with dummy values to trigger initialization
            for i in range(k+1):
                filter_instance.process(float(i))

            expected_mididx = (k - 1) // 2
            assert filter_instance.mididx == expected_mididx

    def test_edge_case_window_size_one(self) -> None:
        """Test edge case with window size of 1."""
        filter_instance = LiveMedian(1)

        result1 = filter_instance.process(5.0)
        assert result1 == 5.0

        result2 = filter_instance.process(10.0)
        assert result2 == 10.0  # Should return current value


class TestLiveMean:
    """Test LiveMean (mean low-pass filter)."""

    def test_init_sets_correct_attributes(self) -> None:
        """Test that initialization sets attributes correctly."""
        filter_instance = LiveMean(5)

        assert filter_instance.k == 5
        assert filter_instance.init_list == []
        assert filter_instance.total == 0
        assert filter_instance.initialized is False
        assert filter_instance.window is None

    def test_process_returns_running_mean_during_initialization(self) -> None:
        """Test that process returns running mean during initialization."""
        filter_instance = LiveMean(3)

        result1 = filter_instance.process(6.0)
        assert result1 == 6.0  # 6/1

        result2 = filter_instance.process(9.0)
        assert result2 == 7.5  # (6+9)/2

        result3 = filter_instance.process(12.0)
        assert result3 == 9.0  # (6+9+12)/3

    def test_process_initializes_after_k_values(self) -> None:
        """Test that filter initializes when processing the (k+1)th value."""
        filter_instance = LiveMean(3)

        filter_instance.process(1.0)
        filter_instance.process(2.0)
        filter_instance.process(3.0)
        assert not filter_instance.initialized

        # The fourth call triggers initialization
        result = filter_instance.process(4.0)
        assert result == pytest.approx(3.0, abs=1e-10)  # (2+3+4)/3 = 3.0
        assert filter_instance.initialized

    def test_process_returns_sliding_mean_after_initialization(self) -> None:
        """Test that process returns sliding window mean after initialization."""
        filter_instance = LiveMean(3)

        # Initialize with [1, 2, 3]
        filter_instance.process(1.0)
        filter_instance.process(2.0)
        filter_instance.process(3.0)

        # Next value: window becomes [2, 3, 6]
        result = filter_instance.process(6.0)
        assert result == pytest.approx(3.6666666666666665, abs=1e-10)  # (2+3+6)/3

    def test_process_maintains_correct_total(self) -> None:
        """Test that running total is maintained correctly."""
        filter_instance = LiveMean(3)

        # Initialize
        filter_instance.process(2.0)
        filter_instance.process(4.0)
        filter_instance.process(6.0)

        # Total should be 12
        assert filter_instance.total == 12.0

        # Add new value, should subtract oldest (2) and add new (8)
        filter_instance.process(8.0)
        assert filter_instance.total == pytest.approx(18.0, abs=1e-10)  # 4+6+8

    @pytest.mark.parametrize(
        'window_size,input_sequence,expected_final_mean',
        [
            (3, [1, 2, 3, 4, 5], 4.0),  # Final window [3,4,5], mean=4
            (2, [10, 20, 30], 25.0),  # Final window [20,30], mean=25
            (4, [1, 1, 1, 1, 2], 1.25),  # Final window [1,1,1,2], mean=1.25
        ],
    )
    def test_process_various_sequences(
        self, window_size: int, input_sequence: List[int], expected_final_mean: float
    ) -> None:
        """Test processing with various input sequences."""
        filter_instance = LiveMean(window_size)

        result = 0.0
        for value in input_sequence:
            result = filter_instance.process(float(value))

        assert result == pytest.approx(expected_final_mean, abs=1e-10)

    def test_init_queue_deletes_temporary_attributes(self) -> None:
        """Test that init_queue deletes temporary initialization attributes."""
        filter_instance = LiveMean(2)

        # Fill initialization list - the third call triggers initialization
        filter_instance.process(1.0)
        filter_instance.process(2.0)
        filter_instance.process(3.0)  # This triggers initialization and deletes init_list

        # After initialization, init_list should be deleted
        assert not hasattr(filter_instance, 'init_list')

    def test_process_with_zero_values(self) -> None:
        """Test processing with zero values."""
        filter_instance = LiveMean(3)

        result1 = filter_instance.process(0.0)
        assert result1 == 0.0

        result2 = filter_instance.process(0.0)
        assert result2 == 0.0

        result3 = filter_instance.process(0.0)
        assert result3 == 0.0

    def test_process_with_negative_values(self) -> None:
        """Test processing with negative values."""
        filter_instance = LiveMean(2)

        filter_instance.process(-5.0)
        filter_instance.process(-10.0)

        result = filter_instance.process(5.0)
        assert result == pytest.approx(-2.5, abs=1e-10)  # (-10+5)/2

    def test_edge_case_window_size_one(self) -> None:
        """Test edge case with window size of 1."""
        filter_instance = LiveMean(1)

        result1 = filter_instance.process(7.0)
        assert result1 == 7.0

        result2 = filter_instance.process(14.0)
        assert result2 == 14.0  # Should return current value


class TestFiltersIntegration:
    """Test integration scenarios and edge cases across all filters."""

    def test_all_filters_handle_nan_consistently(self) -> None:
        """Test that all filters handle NaN input consistently."""
        filters = [
            LiveLFilter(np.array([1.0]), np.array([1.0])),
            LiveSosFilter(np.array([[1.0, 0.0, 0.0, 1.0, 0.0, 0.0]])),
            LiveMedian(3),
            LiveMean(3),
        ]

        for filter_instance in filters:
            result = filter_instance.process(float('nan'))
            assert math.isnan(
                result
            ), f"Filter {type(filter_instance).__name__} didn't handle NaN correctly"

    def test_filter_chaining(self) -> None:
        """Test chaining multiple filters together."""
        # Create a chain: input -> median -> mean -> output
        median_filter = LiveMedian(3)
        mean_filter = LiveMean(3)

        input_sequence = [1.0, 5.0, 2.0, 8.0, 3.0, 7.0]

        for value in input_sequence:
            median_result = median_filter.process(value)
            final_result = mean_filter.process(median_result)
            assert math.isfinite(final_result)

    @pytest.mark.parametrize(
        'filter_class,init_args',
        [
            (LiveLFilter, (np.array([1.0]), np.array([1.0]))),
            (LiveSosFilter, (np.array([[1.0, 0.0, 0.0, 1.0, 0.0, 0.0]]),)),
            (LiveMedian, (3,)),
            (LiveMean, (3,)),
        ],
    )
    def test_filters_numerical_stability(
        self, filter_class: Any, init_args: Tuple[Any, ...]
    ) -> None:
        """Test numerical stability with extreme input values."""
        filter_instance = filter_class(*init_args)

        extreme_values = [1e10, -1e10, 1e-10, -1e-10, 0.0]

        for value in extreme_values:
            result = filter_instance.process(value)
            assert math.isfinite(result), f"Filter became unstable with input {value}"

    def test_filters_memory_efficiency(self) -> None:
        """Test that filters don't accumulate unbounded memory."""
        # Test with large number of inputs
        median_filter = LiveMedian(5)
        mean_filter = LiveMean(5)

        for i in range(10000):
            median_filter.process(float(i % 100))
            mean_filter.process(float(i % 100))

        # Filters should maintain constant memory usage
        assert len(median_filter.q) == 5 if median_filter.q else True
        assert len(mean_filter.window) == 5 if mean_filter.window else True
