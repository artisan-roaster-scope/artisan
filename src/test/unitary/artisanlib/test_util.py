import pytest
import hypothesis.strategies as st
from hypothesis import given, example, settings
from typing import Optional

from artisanlib.util import fromCtoF, fromFtoC, render_weight


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


# render_weight

# weight_unit_index
#  0: g
#  1: kg
#  2: lb
#  3: oz

@pytest.mark.parametrize('amount,weight_unit_index,target_unit_idx,brief,smart_unit_upgrade,expected', [
    # input g, target g
    (12.34, 0, 0, 0, True, '12.3g'),
    (12.34, 0, 0, 1, True, '12g'),
    (123.4, 0, 0, 0, True, '123g'),     # 0 decimal as >=100 and result unit g
    (123.4, 0, 0, 1, True, '123g'),     # 0 decimal as >=100 and result unit g
    (1234.2, 0, 0, 0, True, '1234g'),   # 0 decimal as >=100 and result unit g
    (1234.2, 0, 0, 1, True, '1.23kg'),  # upgraded to kg as brief!=0 and amount>1000, rendered with 2 decimals (1 downgraded from the default 3)
    (12346, 0, 0, 0, True, '12.346kg'), # unit upgrade
    (1600, 0, 0, 0, True, '1.6kg'),     # smart unit upgrade
    (1600, 0, 0, 0, False, '1600g'),    # no smart unit upgrade (disabled)
    (1601, 0, 0, 0, True, '1601g'),     # no smart unit upgrade (as not more readable)
    (1610, 0, 0, 0, True, '1610g'),     # no smart unit upgrade (as not more readable)
    (1000000, 0, 0, 0, True, '1t'),     # >10kg rendered using result unit t
    # input kg
    (0.9123, 1, 0, 0, True, '912g'),    # 0 decimal as >=100 and target unit g
    (0.9123, 1, 1, 0, True, '912g'),    # target unit kg, but unit downgrade as <1kg
    (1.9123, 1, 0, 0, True, '1912g'),
    (1.9123, 1, 1, 0, True, '1.912kg'),
    (1.9123, 1, 1, 1, True, '1.91kg'),  # brief=1 (one decimal less)
    (12345.6, 1, 0, 1, True, '12.35t'), # target unit g; unit upgrade; result unit t
    (12345.6, 1, 1, 1, True, '12.35t'), # target unit kg; unit upgrade; result unit t
    (1600, 1, 1, 0, True, '1.6t'),      # smart unit upgrade
    (1600, 1, 1, 0, False, '1600kg'),   # no smart unit upgrade (disabled)
    (1601, 1, 1, 0, True, '1601kg'),    # no smart unit upgrade (as not more readable)
    (1610, 1, 1, 0, True, '1610kg'),    # no smart unit upgrade (as not more readable)
    # input oz
    (32000, 3, 3, 0, True, '1t'),       # >32000oz rendered as target unit US t
    (2000, 3, 3, 0, True, '125lb'),     # >1600oz rendered as target unit lbs

    # input lb
    (0.9123, 2, 2, 0, True, '14.6oz'),   # 1 decimal as <100 and target unit oz (only with smart unit upgrade)
    (0.9123, 2, 2, 0, False, '0.912lb'), # 3 decimal as <100 and target unit lb (smart unit upgrade off)
    (2600, 2, 2, 0, True, '1.3t'),       # smart unit upgrade
    (2600, 2, 2, 0, False, '2600lb'),    # no smart unit upgrade (disabled)
    (2601, 2, 2, 0, True, '2601lb'),     # no smart unit upgrade (as not more readable)
    (2610, 2, 2, 0, True, '2610lb'),     # no smart unit upgrade (as not more readable)
    ])
def test_render_weight(amount:float, weight_unit_index:int,
        target_unit_idx:int, brief:int, smart_unit_upgrade:bool, expected:str) -> None:
    assert render_weight(amount, weight_unit_index, target_unit_idx,
            brief=brief, smart_unit_upgrade=smart_unit_upgrade) == expected
