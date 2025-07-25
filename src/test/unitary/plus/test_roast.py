import pytest

from plus.stock import Blend, BlendIngredient
from plus.roast import trimBlendSpec

@pytest.fixture
def half_blend_ingredient1() -> BlendIngredient:
    return { 'coffee': 'Brazil Santos', 'ratio': 0.5 }

@pytest.fixture
def half_blend_ingredient2() -> BlendIngredient:
    return { 'coffee': 'Guatemala Rocket', 'ratio': 0.5 }

@pytest.fixture
def half_blend_ingredient2_empty_coffee() -> BlendIngredient:
    return { 'coffee': '', 'ratio': 0.5 }

@pytest.fixture
def half_blend_ingredient2_no_coffee() -> BlendIngredient:
    return { 'ratio': 0.5 } # type: ignore[typeddict-item] # broken BlendIngredient for testing



@pytest.fixture
def regular_blend(
        half_blend_ingredient1:BlendIngredient,
        half_blend_ingredient2:BlendIngredient) -> Blend:
    """Pytest fixture to create a Blend instance for testing."""
    return {
        'label':'Espresso Blend',
        'ingredients': [half_blend_ingredient1, half_blend_ingredient2]}

@pytest.fixture
def no_label_blend(
        half_blend_ingredient1:BlendIngredient,
        half_blend_ingredient2:BlendIngredient) -> Blend:
    """Pytest fixture to create a Blend instance for testing."""
    return {  # type: ignore[typeddict-item] # broken Blend for testing
        'ingredients': [half_blend_ingredient1, half_blend_ingredient2]}

@pytest.fixture
def empty_label_blend(
        half_blend_ingredient1:BlendIngredient,
        half_blend_ingredient2:BlendIngredient) -> Blend:
    """Pytest fixture to create a Blend instance for testing."""
    return {
        'label':'',
        'ingredients': [half_blend_ingredient1, half_blend_ingredient2]}

@pytest.fixture
def ingredient2_empty_coffee_blend(
        half_blend_ingredient1:BlendIngredient,
        half_blend_ingredient2_empty_coffee:BlendIngredient) -> Blend:
    """Pytest fixture to create a Blend instance for testing."""
    return {
        'label':'Espresso Blend',
        'ingredients': [half_blend_ingredient1, half_blend_ingredient2_empty_coffee]}

@pytest.fixture
def ingredient2_no_coffee_blend(
        half_blend_ingredient1:BlendIngredient,
        half_blend_ingredient2_no_coffee:BlendIngredient) -> Blend:
    """Pytest fixture to create a Blend instance for testing."""
    return {
        'label':'Espresso Blend',
        'ingredients': [half_blend_ingredient1, half_blend_ingredient2_no_coffee]}



# trimBlendSpec

def test_trimBlendSpec_regular_blend(regular_blend:Blend) -> None:
    assert trimBlendSpec(regular_blend) is not None

def test_trimBlendSpec_no_label_blend(no_label_blend:Blend) -> None:
    assert trimBlendSpec(no_label_blend) is None

def test_trimBlendSpec_empty_label_blend(empty_label_blend:Blend) -> None:
    assert trimBlendSpec(empty_label_blend) is None

def test_trimBlendSpec_ingredient2_empty_coffee_blend(ingredient2_empty_coffee_blend:Blend) -> None:
    assert trimBlendSpec(ingredient2_empty_coffee_blend) is None

def test_trimBlendSpec_ingredient2_no_coffee_blend(ingredient2_no_coffee_blend:Blend) -> None:
    assert trimBlendSpec(ingredient2_no_coffee_blend) is None
