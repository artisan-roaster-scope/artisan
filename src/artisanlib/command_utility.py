#
# ABOUT
# Handling of Commandline Utility Functions

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# FilePhil, 2020

from artisanlib import __version__
import sys

def handleCommands():
    """ Handles incoming commands and decides on an action.

    args -- given command line arguments
    return -- if the action requires the application, return true
    """

    for arg in sys.argv:

        if arg in ('-v', '--Version'):
            print (f'Artisan  Version {__version__}')

            return False

        if arg in ('-h', '--Help'):
            # To write a text that is not indented
            # the text must be written like this
            helpText ="""
Artisan  Version {}

Usage:
artisan
artisan [options] [path ...]


One path to a file may be specified. If there is an
existing Artisan window the path will be opened in the
viewer mode.

Options:
    -h, --help    Show help
    -v, --Version Show version number
"""

            print(helpText)
            return False

    return True
