# required to run pytest on CI


import sys
import pytest
import numpy as np # pylint: disable=unused-import
import scipy.optimize # need to import globally to avoid reimport # pylint: disable=unused-import
from typing import Any


####
# allow for platform specific testing
# see https://docs.pytest.org/en/stable/example/markers.html#marking-platform-specific-tests-with-pytest
# use @pytest.mark.darwin, @pytest.mark.linux, @pytest.mark.win32

ALL = set('darwin linux win32'.split())

def pytest_runtest_setup(item:Any) -> None:
    supported_platforms = ALL.intersection(mark.name for mark in item.iter_markers())
    plat = sys.platform
    if supported_platforms and plat not in supported_platforms:
        pytest.skip(f"cannot run on platform {plat}")

# register platform markers
def pytest_configure(config:Any) -> None:
    for plat in ALL:
        config.addinivalue_line(
            'markers', f"{plat}: mark test to run only on named platform")
