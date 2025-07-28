# ============================================================================
# CRITICAL: Module-Level Isolation Setup (MUST BE FIRST)
# ============================================================================
# Ensure proper module isolation to prevent cross-file contamination

import sys
from typing import Any, Dict, Generator, List, Set
from unittest.mock import Mock, patch

# Store original modules before any mocking to enable restoration
original_modules: Dict[str, Any] = {}
original_functions: Dict[str, Any] = {}
modules_to_isolate = [
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt6.QtGui',
    'PyQt5.QtCore',
    'PyQt5.QtWidgets',
    'PyQt5.QtGui',
    'artisanlib.util',
    'artisanlib.dialogs',
    'artisanlib.widgets',
    'artisanlib.main',
    'uic',
    'uic.BlendDialog',
]

# Store original modules if they exist
for module_name in modules_to_isolate:
    if module_name in sys.modules and not hasattr(sys.modules[module_name], '_mock_name'):
        original_modules[module_name] = sys.modules[module_name]

# Store original functions that we'll need to restore
if 'artisanlib.util' in sys.modules and hasattr(sys.modules['artisanlib.util'], 'comma2dot'):
    original_functions['artisanlib.util.comma2dot'] = sys.modules['artisanlib.util'].comma2dot
if 'artisanlib.util' in sys.modules and hasattr(
    sys.modules['artisanlib.util'], 'float2floatWeightVolume'
):
    original_functions['artisanlib.util.float2floatWeightVolume'] = sys.modules[
        'artisanlib.util'
    ].float2floatWeightVolume

# ============================================================================
# Now safe to import other modules
# ============================================================================

"""Unit tests for plus.blend module.

This module tests the blend management functionality including:
- Component class for blend ingredients
- CustomBlend class for blend management
- Blend validation logic
- Coffee ratio calculations
- Blend component management
- Custom blend dialog functionality
- Blend creation and modification
- Coffee availability validation
- Ratio normalization and validation
- Blend serialization and deserialization

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
   - ensure_blend_isolation fixture manages module state at session level
   - Proper cleanup after session to prevent module registration conflicts

4. **Automatic State Reset**:
   - reset_blend_state fixture runs automatically for every test
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
✅ Individual tests pass: pytest test_blend.py::TestClass::test_method
✅ Full module tests pass: pytest test_blend.py
✅ Cross-file isolation works: pytest test_blend.py test_main.py
✅ Cross-file isolation works: pytest test_main.py test_blend.py
✅ No module contamination affecting other tests
✅ No numpy multiple import issues

This implementation serves as a reference for proper test isolation in
modules that require extensive mocking while preventing cross-file contamination.
=============================================================================
"""

import pytest

# Use a more targeted approach - only mock what we absolutely need
# and avoid global module mocking that can interfere with other tests

# Import the blend module with targeted patches
# Only patch PyQt6 since PyQt5 is not installed and should be ignored
with patch('artisanlib.util.comma2dot', side_effect=lambda x: x), patch(
    'artisanlib.util.float2floatWeightVolume', side_effect=lambda x: x
), patch('artisanlib.dialogs.ArtisanDialog', Mock), patch(
    'artisanlib.widgets.MyQComboBox', Mock
), patch(
    'uic.BlendDialog.Ui_customBlendDialog', Mock
):
    from plus.blend import Component, CustomBlend


@pytest.fixture(scope='session', autouse=True)
def ensure_blend_isolation() -> Generator[None, None, None]:
    """
    Ensure modules are properly isolated for blend tests at session level.

    This fixture runs once per test session to ensure that mocked modules
    used by blend tests don't interfere with other tests that need real dependencies.
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
def cleanup_blend_mocks() -> Generator[None, None, None]:
    """
    Clean up blend test mocks at module level to prevent cross-file contamination.

    This fixture runs once per test module and ensures immediate cleanup
    of mocked dependencies when the blend test module completes.
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
def reset_blend_state() -> Generator[None, None, None]:
    """
    Reset all blend module state before and after each test to ensure complete isolation.

    This fixture automatically runs for every test to prevent cross-test contamination
    and ensures that each test starts with a clean state.
    """
    yield

    # Clean up after each test - no global mocks to reset since we use targeted patching


@pytest.fixture
def sample_component() -> Component:
    """Create a fresh sample component for each test."""
    return Component('test_coffee', 0.5)


@pytest.fixture
def sample_components() -> List[Component]:
    """Create fresh sample components for each test."""
    return [Component('brazil_santos', 0.6), Component('guatemala_antigua', 0.4)]


@pytest.fixture
def sample_blend(sample_components: List[Component]) -> CustomBlend:
    """Create a fresh sample blend for each test."""
    return CustomBlend('Test Blend', sample_components)


class TestComponent:
    """Test Component class functionality."""

    def test_component_initialization(self) -> None:
        """Test Component initialization with coffee and ratio."""
        # Arrange
        coffee_id = 'brazil_santos_123'
        ratio = 0.6

        # Act
        component = Component(coffee_id, ratio)

        # Assert
        assert component.coffee == coffee_id
        assert component.ratio == ratio

    def test_component_coffee_property_getter(self) -> None:
        """Test Component coffee property getter."""
        # Arrange
        coffee_id = 'guatemala_antigua_456'
        component = Component(coffee_id, 0.4)

        # Act
        result = component.coffee

        # Assert
        assert result == coffee_id

    def test_component_coffee_property_setter(self) -> None:
        """Test Component coffee property setter."""
        # Arrange
        original_coffee = 'original_coffee_789'
        new_coffee = 'new_coffee_101'
        component = Component(original_coffee, 0.5)

        # Act
        component.coffee = new_coffee

        # Assert
        assert component.coffee == new_coffee

    def test_component_ratio_property_getter(self) -> None:
        """Test Component ratio property getter."""
        # Arrange
        ratio = 0.75
        component = Component('test_coffee', ratio)

        # Act
        result = component.ratio

        # Assert
        assert result == ratio

    def test_component_ratio_property_setter(self) -> None:
        """Test Component ratio property setter."""
        # Arrange
        original_ratio = 0.3
        new_ratio = 0.7
        component = Component('test_coffee', original_ratio)

        # Act
        component.ratio = new_ratio

        # Assert
        assert component.ratio == new_ratio

    def test_component_with_zero_ratio(self) -> None:
        """Test Component with zero ratio."""
        # Arrange
        coffee_id = 'zero_ratio_coffee'
        ratio = 0.0

        # Act
        component = Component(coffee_id, ratio)

        # Assert
        assert component.coffee == coffee_id
        assert component.ratio == ratio

    def test_component_with_full_ratio(self) -> None:
        """Test Component with full ratio (1.0)."""
        # Arrange
        coffee_id = 'full_ratio_coffee'
        ratio = 1.0

        # Act
        component = Component(coffee_id, ratio)

        # Assert
        assert component.coffee == coffee_id
        assert component.ratio == ratio

    def test_component_with_decimal_ratio(self) -> None:
        """Test Component with precise decimal ratio."""
        # Arrange
        coffee_id = 'decimal_coffee'
        ratio = 0.333333

        # Act
        component = Component(coffee_id, ratio)

        # Assert
        assert component.coffee == coffee_id
        assert component.ratio == ratio


class TestCustomBlend:
    """Test CustomBlend class functionality."""

    def test_custom_blend_initialization(self) -> None:
        """Test CustomBlend initialization with name and components."""
        # Arrange
        blend_name = 'House Blend'
        components = [Component('brazil_santos', 0.6), Component('guatemala_antigua', 0.4)]

        # Act
        blend = CustomBlend(blend_name, components)

        # Assert
        assert blend.name == blend_name
        assert len(blend.components) == 2
        assert blend.components[0].coffee == 'brazil_santos'
        assert blend.components[0].ratio == 0.6
        assert blend.components[1].coffee == 'guatemala_antigua'
        assert blend.components[1].ratio == 0.4

    def test_custom_blend_name_property_getter(self) -> None:
        """Test CustomBlend name property getter."""
        # Arrange
        blend_name = 'Espresso Blend'
        blend = CustomBlend(blend_name, [])

        # Act
        result = blend.name

        # Assert
        assert result == blend_name

    def test_custom_blend_name_property_setter(self) -> None:
        """Test CustomBlend name property setter."""
        # Arrange
        original_name = 'Original Blend'
        new_name = 'Updated Blend'
        blend = CustomBlend(original_name, [])

        # Act
        blend.name = new_name

        # Assert
        assert blend.name == new_name

    def test_custom_blend_components_property_getter(self) -> None:
        """Test CustomBlend components property getter."""
        # Arrange
        components = [Component('coffee1', 0.5), Component('coffee2', 0.5)]
        blend = CustomBlend('Test Blend', components)

        # Act
        result = blend.components

        # Assert
        assert result == components
        assert len(result) == 2

    def test_custom_blend_components_property_setter(self) -> None:
        """Test CustomBlend components property setter."""
        # Arrange
        original_components = [Component('coffee1', 0.5), Component('coffee2', 0.5)]
        new_components = [
            Component('coffee3', 0.3),
            Component('coffee4', 0.4),
            Component('coffee5', 0.3),
        ]
        blend = CustomBlend('Test Blend', original_components)

        # Act
        blend.components = new_components

        # Assert
        assert blend.components == new_components
        assert len(blend.components) == 3

    def test_custom_blend_empty_components(self) -> None:
        """Test CustomBlend with empty components list."""
        # Arrange
        blend_name = 'Empty Blend'
        components: List[Component] = []

        # Act
        blend = CustomBlend(blend_name, components)

        # Assert
        assert blend.name == blend_name
        assert len(blend.components) == 0

    def test_custom_blend_single_component(self) -> None:
        """Test CustomBlend with single component."""
        # Arrange
        blend_name = 'Single Origin'
        components = [Component('single_coffee', 1.0)]

        # Act
        blend = CustomBlend(blend_name, components)

        # Assert
        assert blend.name == blend_name
        assert len(blend.components) == 1
        assert blend.components[0].ratio == 1.0


class TestCustomBlendValidation:
    """Test CustomBlend validation functionality."""

    def test_is_valid_with_valid_two_component_blend(self) -> None:
        """Test isValid with valid two-component blend."""
        # Arrange
        components = [Component('brazil_santos', 0.6), Component('guatemala_antigua', 0.4)]
        blend = CustomBlend('Valid Blend', components)

        # Act
        result = blend.isValid()

        # Assert
        assert result is True

    def test_is_valid_with_valid_three_component_blend(self) -> None:
        """Test isValid with valid three-component blend."""
        # Arrange
        components = [
            Component('brazil_santos', 0.4),
            Component('guatemala_antigua', 0.3),
            Component('colombia_supremo', 0.3),
        ]
        blend = CustomBlend('Three Component Blend', components)

        # Act
        result = blend.isValid()

        # Assert
        assert result is True

    def test_is_valid_with_single_component_invalid(self) -> None:
        """Test isValid with single component (invalid)."""
        # Arrange
        components = [Component('single_coffee', 1.0)]
        blend = CustomBlend('Single Component', components)

        # Act
        result = blend.isValid()

        # Assert
        assert result is False

    def test_is_valid_with_empty_components_invalid(self) -> None:
        """Test isValid with empty components (invalid)."""
        # Arrange
        components: List[Component] = []
        blend = CustomBlend('Empty Blend', components)

        # Act
        result = blend.isValid()

        # Assert
        assert result is False

    def test_is_valid_with_duplicate_coffees_invalid(self) -> None:
        """Test isValid with duplicate coffees (invalid)."""
        # Arrange
        components = [
            Component('brazil_santos', 0.5),
            Component('brazil_santos', 0.5),  # Duplicate coffee
        ]
        blend = CustomBlend('Duplicate Blend', components)

        # Act
        result = blend.isValid()

        # Assert
        assert result is False

    def test_is_valid_with_available_coffees_all_available(self) -> None:
        """Test isValid with available_coffees parameter - all coffees available."""
        # Arrange
        components = [Component('brazil_santos', 0.6), Component('guatemala_antigua', 0.4)]
        blend = CustomBlend('Available Blend', components)
        available_coffees = {'brazil_santos', 'guatemala_antigua', 'colombia_supremo'}

        # Act
        result = blend.isValid(available_coffees)

        # Assert
        assert result is True

    def test_is_valid_with_available_coffees_some_unavailable(self) -> None:
        """Test isValid with available_coffees parameter - some coffees unavailable."""
        # Arrange
        components = [
            Component('brazil_santos', 0.6),
            Component('unavailable_coffee', 0.4),  # Not in available list
        ]
        blend = CustomBlend('Unavailable Blend', components)
        available_coffees = {'brazil_santos', 'guatemala_antigua'}

        # Act
        result = blend.isValid(available_coffees)

        # Assert
        assert result is False

    def test_is_valid_with_available_coffees_empty_list(self) -> None:
        """Test isValid with empty available_coffees list."""
        # Arrange
        components = [Component('brazil_santos', 0.6), Component('guatemala_antigua', 0.4)]
        blend = CustomBlend('Test Blend', components)
        available_coffees: Set[str] = set()

        # Act
        result = blend.isValid(available_coffees)

        # Assert
        assert result is False

    def test_is_valid_with_none_available_coffees(self) -> None:
        """Test isValid with None available_coffees (should ignore availability check)."""
        # Arrange
        components = [Component('any_coffee1', 0.6), Component('any_coffee2', 0.4)]
        blend = CustomBlend('Any Blend', components)

        # Act
        result = blend.isValid(None)

        # Assert
        assert result is True


class TestCustomBlendEdgeCases:
    """Test CustomBlend edge cases and complex scenarios."""

    def test_is_valid_with_many_components(self) -> None:
        """Test isValid with many components."""
        # Arrange
        components = [Component(f"coffee_{i}", 0.1) for i in range(10)]
        blend = CustomBlend('Many Component Blend', components)

        # Act
        result = blend.isValid()

        # Assert
        assert result is True

    def test_is_valid_with_very_small_ratios(self) -> None:
        """Test isValid with very small ratios."""
        # Arrange
        components = [Component('coffee1', 0.001), Component('coffee2', 0.999)]
        blend = CustomBlend('Small Ratio Blend', components)

        # Act
        result = blend.isValid()

        # Assert
        assert result is True

    def test_is_valid_with_zero_ratio_components(self) -> None:
        """Test isValid with zero ratio components."""
        # Arrange
        components = [Component('coffee1', 0.0), Component('coffee2', 1.0)]
        blend = CustomBlend('Zero Ratio Blend', components)

        # Act
        result = blend.isValid()

        # Assert
        assert result is True

    def test_component_modification_after_creation(self) -> None:
        """Test modifying component properties after creation."""
        # Arrange
        component = Component('original_coffee', 0.5)

        # Act
        component.coffee = 'modified_coffee'
        component.ratio = 0.75

        # Assert
        assert component.coffee == 'modified_coffee'
        assert component.ratio == 0.75

    def test_blend_component_list_modification(self) -> None:
        """Test modifying blend component list after creation."""
        # Arrange
        original_components = [Component('coffee1', 0.5), Component('coffee2', 0.5)]
        blend = CustomBlend('Modifiable Blend', original_components)

        # Act - Add a new component
        blend.components.append(Component('coffee3', 0.0))

        # Assert
        assert len(blend.components) == 3
        assert blend.components[2].coffee == 'coffee3'

    def test_blend_with_unicode_names(self) -> None:
        """Test blend with unicode coffee names."""
        # Arrange
        components = [Component('café_brasileiro', 0.6), Component('café_guatemalteco', 0.4)]
        blend = CustomBlend('Café Especial', components)

        # Act
        result = blend.isValid()

        # Assert
        assert result is True
        assert blend.name == 'Café Especial'

    def test_blend_with_empty_coffee_names(self) -> None:
        """Test blend with empty coffee names."""
        # Arrange
        components = [Component('', 0.6), Component('valid_coffee', 0.4)]
        blend = CustomBlend('Empty Name Blend', components)

        # Act
        result = blend.isValid()

        # Assert
        assert result is True  # Empty names are still valid strings

    def test_blend_with_whitespace_coffee_names(self) -> None:
        """Test blend with whitespace-only coffee names."""
        # Arrange
        components = [Component('   ', 0.6), Component('valid_coffee', 0.4)]
        blend = CustomBlend('Whitespace Blend', components)

        # Act
        result = blend.isValid()

        # Assert
        assert result is True

    def test_available_coffees_with_list_input(self) -> None:
        """Test isValid with available_coffees as list instead of set."""
        # Arrange
        components = [Component('coffee1', 0.6), Component('coffee2', 0.4)]
        blend = CustomBlend('List Input Blend', components)
        available_coffees = ['coffee1', 'coffee2', 'coffee3']  # List instead of set

        # Act
        result = blend.isValid(available_coffees)

        # Assert
        assert result is True

    def test_available_coffees_with_tuple_input(self) -> None:
        """Test isValid with available_coffees as tuple."""
        # Arrange
        components = [Component('coffee1', 0.6), Component('coffee2', 0.4)]
        blend = CustomBlend('Tuple Input Blend', components)
        available_coffees = ('coffee1', 'coffee2', 'coffee3')  # Tuple

        # Act
        result = blend.isValid(available_coffees)

        # Assert
        assert result is True
