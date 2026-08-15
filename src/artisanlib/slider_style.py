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

artisan_slider_style = """
    QSlider::groove:vertical:focus {{
        background: #888;
        border: 0.5px solid #666;
        width: 3px;
        border-radius: 5px;
    }}
    QSlider::sub-page:vertical:focus {{
        background: 888;
        border: 0.5px solid #666;
        width: 85px;
        border-radius: 5px;
    }}
    QSlider::groove:vertical {{
        background: #ddd;
        border: 0.5px solid #aaa;
        width: 3px;
        border-radius: 5px;
    }}
    QSlider::sub-page:vertical {{
        background: #ddd;
        border: 0.5px solid #aaa;
        width: 85px;
        border-radius: 5px;
    }}
    QSlider::add-page:vertical {{
        background: {color};
        border: 1px solid {color};
        width: 5px;
        border-radius: 2px;
    }}
    QSlider::handle:vertical {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fff, stop:1 #eee);
        border: 0.5px solid #ddd;
        height: 10px;
        margin-top: -1px;
        margin-bottom: -1px;
        margin-left: -15px;
        margin-right: -15px;
        border-radius: 5px;
    }}
    QSlider::handle:vertical:!hover:focus {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ddd, stop:1 #888);
        border: 1px solid #555;
        border-radius: 5px;
    }}
    QSlider::handle:vertical:hover:focus {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ddd, stop:1 #777);
        border: 1px solid #555;
        border-radius: 5px;
    }}
    QSlider::handle:vertical:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ddd);
        border: 1px solid #ccc;
        border-radius: 5px;
    }}
    QSlider::sub-page:vertical:disabled {{
        background: #bbb;
        border-color: #999;
    }}
    QSlider::add-page:vertical:disabled {{
        background: #eee;
        border-color: #999;
    }}
    QSlider::handle:vertical:disabled {{
        background: #eee;
        border: 1px solid #aaa;
        border-radius: 5px;
    }}
"""

# params:
#   title_color
#   color
#   background_color
artisan_slider_frame_style = """
    QGroupBox {{
        color: {color};
        background-color: {background_color};
        border: 0px solid gray;
        border-width: 0px;
        padding-top: 12px;
        padding-bottom: 5px;
        padding-left: 0px;
        padding-right: 0px;
    }}
    QGroupBox::title {{
        color: {title_color};
        background-color: {background_color};
        subcontrol-origin: margin;
        subcontrol-position: top center;
    }}
"""
