import pytest
import hypothesis.strategies as st
from hypothesis import given, example, settings

from artisanlib.util import fromCtoF, fromFtoC


# fromCtoF

def test_fromCtoF():
    assert fromCtoF(-1) == -1
    assert fromCtoF(None) == None

@given(temp=st.one_of(st.floats(-100,1000)))
@settings(max_examples=10)
@example(-1)
def test_fromCtoF(temp):
    if temp == -1:
        assert fromCtoF(temp) == -1
    else:
        assert fromFtoC(fromCtoF(temp)) == pytest.approx(temp, 0.1)

# fromFtoC

def test_fromFtoC():
    assert fromFtoC(-1) == -1
    assert fromFtoC(None) == None

@given(temp=st.one_of(st.floats(-100,1500)))
@settings(max_examples=10)
@example(-1)
def test_fromFtoC(temp):
    if temp == -1:
        assert fromFtoC(temp) == -1
    else:
        assert fromCtoF(fromFtoC(temp)) == pytest.approx(temp, 0.1)
