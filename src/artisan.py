#!/usr/bin/env python3
"""Start the application.
"""

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

import os
import warnings
from typing import Any

warnings.simplefilter('ignore', DeprecationWarning)

# limit the number of numpy threads to 1 to limit the total number of threads taking into account a potential performance reduction on array operations using blas,
# which should not be significant
os.environ['OMP_NUM_THREADS'] = '1'

# deactivate defusedexml in OPENPYXL as it might not be installed or bundled
os.environ['OPENPYXL_DEFUSEDXML'] = 'False'


from artisanlib import main, command_utility

# from pyinstaller 5.8:
class NullWriter:
    softspace = 0
    encoding:str = 'UTF-8'

    @staticmethod
    def write(*args:Any) -> None:
        pass

    @staticmethod
    def flush(*args:Any) -> None:
        pass

    # Some packages are checking if stdout/stderr is available (e.g., youtube-dl). For details, see #1883.
    @staticmethod
    def isatty() -> bool:
        return False

if __name__ == '__main__':

    # Manage commands that does not need to start the whole application
    if command_utility.handleCommands():
        main.main()


# EOF
