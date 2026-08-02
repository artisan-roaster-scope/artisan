#
# ABOUT
# handling of commandline utility functions
#
# COPYRIGHT (C) 2010-2026 The artisan team represented by
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
#
# AUTHOR
# FilePhil, 2023

from artisanlib import __version__
import sys

def handleCommands() -> bool:
    """ Handles incoming commands and decides on an action.

    args -- given command line arguments
    return -- if the action requires the application, return true
    """

    for arg in sys.argv:

        if arg in {'-v', '--Version'}:
            print (f'Artisan  Version {__version__}')

            return False

        if arg in {'-h', '--Help'}:
            # To write a text that is not indented
            # the text must be written like this
            helpText = """
Artisan Version {}

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

            print(helpText.format(__version__))
            return False

    return True
