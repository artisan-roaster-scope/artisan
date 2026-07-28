# ABOUT
# required to run pytest on CI

# COPYRIGHT (C) 2010-2026 The Artisan team represented by
#   Marko Luther <marko.luther@gmx.net> (maintainer) and all contributors
#
# LICENSE
# This program or module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# MAINTAINER
# Marko Luther, 2026

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
