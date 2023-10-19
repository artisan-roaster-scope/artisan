import pytest
import hypothesis.strategies as st
from hypothesis import given, example, settings
from typing import Optional

from artisanlib.util import fromCtoF, fromFtoC


# fromCtoF

@given(temp=st.one_of(st.floats(-100,1000)))
@settings(max_examples=10)
@example(-1)
@example(None)
def test_fromCtoF(temp:Optional[float]) -> None:
    if temp == -1:
        assert fromCtoF(temp) == -1
    elif temp is None:
        assert fromCtoF(temp) is None
    else:
        assert fromFtoC(fromCtoF(temp)) == pytest.approx(temp, 0.1)

# fromFtoC

@given(temp=st.one_of(st.floats(-100,1500)))
@settings(max_examples=10)
@example(-1)
@example(None)
def test_fromFtoC(temp:Optional[float]) -> None:
    if temp == -1:
        assert fromFtoC(temp) == -1
    elif temp is None:
        assert fromFtoC(temp) is None
    else:
        assert fromCtoF(fromFtoC(temp)) == pytest.approx(temp, 0.1)
