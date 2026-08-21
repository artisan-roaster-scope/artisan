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

# params:
#   background_color
#   line_edit_color
#   down_arrow_icon_path

artisan_events_editor_style = """
    QGroupBox {{
        background-color: {background_color};
        border-width: 10px;
        border-style:solid;
        border-radius: 0;
        border-color: {background_color};
    }}
    QLabel#eventlabel {{
        background-color: #F3F3F3;
        color: #333333;
        border-width: 1;
        border-color: #333333;
        border-style:solid;
        border-radius: 4;
        min-height: 25px;
        min-width: 80px;
    }}
    QLineEdit {{
        background-color: {background_color};
        color: {line_edit_color};
        min-height: 25px;
        padding: 0px 5px;
        border-radius: 8px;
        border-width: 1px;
        border-style: solid;
        border-color: palette(dark);
    }}
    QLineEdit:focus {{
        border-color: {line_edit_color};
    }}
    QLineEdit#etimeline {{
        min-width: 50px;
    }}
    QLineEdit#valueEdit {{
        min-width: 30px;
    }}
    QComboBox {{
        background-color: #E9E9E9;
        color: black;
        min-height: 25px;
        border-radius: 4;
        padding: 0px 5px;
        min-width: 80px;
    }}
    QComboBox:hover {{
        background-color: #F5F5F5;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 15px;
        border-left-width: 1px;
        border-left-color: darkgray;
        border-left-style: solid;
        border-top-right-radius: 4;
        border-bottom-right-radius: 4;
    }}
    QComboBox::down-arrow {{
        image: url({down_arrow_icon_path});
        subcontrol-position: center;
        width: 30px;
    }}
    QComboBox::drop-down:button {{
        background-color: #E9E9E9;
        width: 30px;
    }}
    QComboBox::drop-down:pressed {{
        background-color: #A9A9A9;
        width: 30px;
    }}
    QComboBox::drop-down:hover {{
        background-color: #F5F5F5;
        width: 30px;
    }}
    QComboBox QAbstractItemView {{
        border-radius: 4;
        selection-background-color: lightgray;
    }}
    QSpinBox {{
        background-color: #E9E9E9;
        color: black;
        min-height: 25px;
        border-radius: 4;
        padding: 0px 5px;
    }}
    QPushButton#minieventleft {{
        background-color: """ + createGradient('#E9E9E9') + """;
        color: #333333;
        border-top-left-radius: 10px;
        border-bottom-left-radius: 10px;
        min-width: 50px;
        min-height: 25px;
    }}
    QPushButton#minieventleft:pressed {{
        background-color: """ + createGradient('#C9C9C9') + """;
    }}
    QPushButton#minieventleft:hover:!pressed {{
        background-color: """ + createGradient('#FFFFFF') + """;
    }}
    QPushButton#minieventright {{
        background-color: """ + createGradient('#E9E9E9') + """;
        color: #333333;
        border-width: 0;
        border-top-right-radius: 10px;
        border-bottom-right-radius: 10px;
        min-width: 50px;
        min-height: 25px;
    }}
    QPushButton#minieventright:pressed {{
        background-color: """ + createGradient('#C9C9C9') + """;
    }}
    QPushButton#minieventright:hover:!pressed {{
        background-color: """ + createGradient('#FFFFFF') + """;
    }}
    QPushButton#buttonminiEvent {{
        background-color: """ + createGradient('#A7A7A7') + """;
        border-radius: 10;
        color: white;
        min-width: 100px;
        min-height: 25px;
        border-width: 0;
    }}
    QPushButton#buttonminiEvent:pressed {{
        background-color: """ + createGradient('#888888') + """;
    }}
    QPushButton#buttonminiEvent:hover:!pressed {{
        background-color: """ + createGradient('#C7C7C7') + """;
    }}

"""
