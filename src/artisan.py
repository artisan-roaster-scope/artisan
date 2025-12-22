#!/usr/bin/env python3
"""Start the application.
"""

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
