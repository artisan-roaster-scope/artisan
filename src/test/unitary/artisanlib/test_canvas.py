import pytest
import hypothesis.strategies as st
from hypothesis import given, settings

from artisanlib.canvas import tgraphcanvas

@pytest.mark.parametrize('test_input,expected', [
    (-80, -9.0),
    (-1, -1.1),
    (0, 0),
    (1, 1.1),
    (43, 5.3),
    (82, 9.2)])
def test_eventsExternal2InternalValue(test_input:int, expected:float) -> None:
    assert tgraphcanvas.eventsExternal2InternalValue(test_input) == expected

@pytest.mark.parametrize('test_input,expected', [
    (None, 0),
    (-9.0, -80),
    (-8.21, -72),
    (-6.26, -53),
    (-3.6, -26),
    (-1.0, 0),
    (-0.2, 0),
    (0.35, 0),
    (1.0, 0),
    (1.1, 1),
    (5.3, 43),
    (9.2, 82)
    ])
def test_eventsInternal2ExternalValue(test_input:float, expected:int) -> None:
    assert tgraphcanvas.eventsInternal2ExternalValue(test_input) == expected


@given(value=st.one_of(st.integers(-100,100)))
@settings(max_examples=10)
def test_eventsExternal2Internal2ExternalValue(value:int) -> None:
    assert tgraphcanvas.eventsInternal2ExternalValue(tgraphcanvas.eventsExternal2InternalValue(value)) == value


@given(value=st.one_of(st.floats(-11,11)))
@settings(max_examples=10)
def test_eventsInternal2External2InternalValue(value:float) -> None:
    if -1 <= value <= 1:
        assert tgraphcanvas.eventsExternal2InternalValue(tgraphcanvas.eventsInternal2ExternalValue(value)) == 0
    else:
        assert tgraphcanvas.eventsExternal2InternalValue(tgraphcanvas.eventsInternal2ExternalValue(value)) == round(value,1)
