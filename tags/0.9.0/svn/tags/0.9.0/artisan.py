#!/usr/bin/env python
"""
Start the application.
"""

from artisanlib import main
from multiprocessing import freeze_support
from platform import system
import imp
import sys
import os

if system() == "Windows" and (hasattr(sys, "frozen") # new py2exe
                            or hasattr(sys, "importers") # old py2exe
                            or imp.is_frozen("__main__")): # tools/freeze
    from multiprocessing import set_executable
    executable = os.path.join(os.path.dirname(sys.executable), 'artisan.exe')
    set_executable(executable)    
    del executable
#    set_executable(os.path.join(sys.exec_prefix, 'artisan.exe'))


if __name__ == '__main__':
    freeze_support()
    main.main()


# EOF
