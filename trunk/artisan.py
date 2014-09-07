#!/usr/bin/env python
"""
Start the application.
"""

import sys
import os
# supress any console/error-log output on all platforms, but Mac OS X
if not sys.platform.startswith("darwin"):
    sys.stderr = sys.stdout = os.devnull

from artisanlib import main

if __name__ == '__main__':
    main.main()


# EOF
