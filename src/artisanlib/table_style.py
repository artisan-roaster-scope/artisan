#
# ABOUT
# artisan table styles
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


from artisanlib.util import createGradient

def horizontal_header_style(darkmode:bool) -> str:
    return f"""
            QHeaderView::section {{
                background-color: {createGradient('#717171') if darkmode else createGradient('#C1C1C1')};
                color: {'#CCCCCC' if darkmode else 'white'};
                border: 1px solid {'#7c7c7c' if darkmode else '#CcCcCc'};
                font-weight: bold;
            }}
            QTableWidget > QHeaderView::section {{
                padding: 2px;
            }}
            QTableWidget > QHeaderView::section:hover {{
                background-color: {createGradient('#818181') if darkmode else createGradient('#E1E1E1')};
            }}
            QTableWidget > QHeaderView::section:first {{
                border-top-left-radius: 10px;
            }}
            QTableWidget > QHeaderView::section:last {{
                border-top-right-radius: 10px;
            }}
    """

def vertical_header_style(darkmode:bool) -> str:
    return f"""
            QHeaderView::section {{
                background-color: {createGradient('#717171', left_to_right=True) if darkmode else createGradient('#C1C1C1', left_to_right=True)};
                color: {'#CCCCCC' if darkmode else 'white'};
                border: 1px solid {'#7c7c7c' if darkmode else '#CcCcCc'};
                font-weight: normal;
            }}
            QTableWidget > QHeaderView::section {{
                padding-right: 6px;
            }}
            QTableWidget > QHeaderView::section:hover {{
                background-color: {createGradient('#818181', left_to_right=True) if darkmode else createGradient('#E1E1E1', left_to_right=True)};
            }}
            QTableWidget > QHeaderView::section:checked, QHeaderView::section:selected {{
                font-weight: bold;
                background-color: {createGradient('#515151', left_to_right=True) if darkmode else createGradient('#A1A1A1', left_to_right=True)};
            }}
            QTableWidget > QHeaderView::section:first {{
                border-top-left-radius: 10px;
            }}
            QTableWidget > QHeaderView::section:last {{
                border-bottom-left-radius: 10px;
            }}
        """
