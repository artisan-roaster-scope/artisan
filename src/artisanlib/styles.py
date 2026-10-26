#
# ABOUT
# artisan scope styles
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

import os
import functools
from pathlib import Path
from artisanlib.util import createGradient, getResourcePath


# button styles


# dialog buttons style

@functools.lru_cache
def artisan_dialog_button_style(is_dark_mode:bool, accent_name:str, accent_hover:str, accent_pressed:str) -> str:
    # Define contrasting background shades depending on Dark/Light configurations
    if is_dark_mode:
        bg_color = '#2c2c2c'        # Dark slate gray
        bg_hover = '#3a3a3a'
        bg_pressed = '#1e1e1e'
        border_color = '#454545'
        text_color = '#ffffff'
    else:
        bg_color = '#ececec'        # Clean canvas light grey
        bg_hover = '#e2e2e2'
        bg_pressed = '#d2d2d2'
        border_color = '#dcdcdc'
        text_color = '#000000'

    return f"""
            QDialogButtonBox QPushButton {{
                background-color: {bg_color};
                outline: none;
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 3px 16px;
                font-size: 13px;
                color: {text_color};
                min-width: 60px;
                height: 20px;
            }}
            QDialogButtonBox QPushButton:hover {{
                background-color: {bg_hover};
            }}
            QDialogButtonBox QPushButton:pressed {{
                background-color: {bg_pressed};
            }}
            QDialogButtonBox QPushButton:default {{
                background-color: {accent_name};
                border: 1px solid {accent_name};
                color: #ffffff;
            }}
            QDialogButtonBox QPushButton:default:hover {{
                background-color: {accent_hover};
                border-color: {accent_hover};
            }}
            QDialogButtonBox QPushButton:default:pressed {{
                background-color: {accent_pressed};
                border-color: {accent_pressed};
            }}
            QDialogButtonBox QPushButton:disabled {{
                background-color: {'#5F5F5F' if is_dark_mode else '#DFDFDF'};
                color: {'#AEAEA3' if is_dark_mode else '#8E8E93'};
                border: 0;
            }}
    """

@functools.lru_cache
def artisan_push_button_style(dark:bool=False) -> str:
    return f"""
        QPushButton {{
            background-color: #4c97c3;
            color: #FFFFFF;
            border: 0px solid;
            border-radius: 14px;
            padding: 6px 10px;
        }}
        QPushButton#plus_button {{
            border-radius: 13px;
        }}
        QPushButton#minus_button {{
            border-radius: 13px;
        }}
        QPushButton:hover {{
            background-color: #43a7cf;
        }}
        QPushButton:pressed {{
            background-color: #1985ba;
        }}
        QPushButton:disabled {{
            background-color: {'#555F5F5F' if dark else '#DFDFDF'};
            color: {'#AEAEA3' if dark else '#8E8E93'};
        }}
    """

@functools.lru_cache
def artisan_minor_push_button_style(dark:bool=False, large:bool=False) -> str:
    return f"""
        QPushButton {{
            background-color: {'#52525250' if dark else '#B7B7B7'};
            color: {'#DEDEDE' if dark else '#FFFFFF'};
            border: {'1px solid #4A4A4A' if dark else '0px solid'};
            border-radius: {'14px' if large else '12px'};
            padding: {'3px' if dark else '4px'} 10px;
        }}
        QPushButton:hover {{
            background-color: {'#AA5B5B5B' if dark else '#C7C7C7'};
        }}
        QPushButton:pressed {{
            background-color: {'#AA6B6B6B' if dark else '#979797'};
        }}
        QPushButton:disabled {{
            background-color: {'#55303030' if dark else '#E8E8E8'};
            color: {'#8F8F8F' if dark else '#8E8E93'};
        }}
    """

@functools.lru_cache
def link_push_button_style(dark:bool=False) -> str:
    return f"""
        QPushButton {{
            background-color: {'#52525250' if dark else '#B7B7B7'};
            color: {'#DEDEDE' if dark else '#FFFFFF'};
            border: 0px solid;
            border-radius: 10px;
            padding: 4px 0px;
            max-height: 10px;
            text-align: left;
            padding-right: 10px;
            padding-left: 10px;
        }}
        QPushButton:hover {{
            background-color: {'#AA5B5B5B' if dark else '#C7C7C7'};
        }}
        QPushButton:pressed {{
            background-color: {'#AA6B6B6B' if dark else '#979797'};
        }}
        QPushButton:disabled {{
            background-color: {'#AA383838' if dark else '#E8E8E8'};
            color: {'#8F8F8F' if dark else '#8E8E93'};
        }}
    """

@functools.lru_cache
def tool_button_icon_style(dark:bool, light_icon:str, dark_icon:str, border_width:int = 3, border_radius:int = 7) -> str:
    icon_path = Path.as_posix(Path(os.path.join(getResourcePath(),'Icons'),
        dark_icon if dark else light_icon))
    disabled_icon_path = Path.as_posix(Path(os.path.join(getResourcePath(),'Icons'),
        light_icon if dark else dark_icon))
    return f"""
        QToolButton {{
            background-color: transparent;
            outline: none;
            border: {border_width}px solid;
            border-radius: {border_radius}px;
            border-color: transparent;
            image: url({icon_path});
        }}
        QToolButton:disabled {{
            image: url({disabled_icon_path});
        }}
        QToolButton:hover {{
            background-color: {'#AA555555' if dark else '#E0E0E0'};
        }}
        QToolButton:pressed {{
            background-color: {'#AA777777' if dark else '#D0D0D0'};
        }}
"""

@functools.lru_cache
def artisan_event_button_style(min_width:int, min_height:int, padding:int, default_font_size:int, selected_font_size:int) -> str:
    return f"""
    EventPushButton {{
        min-width: {min_width}px;
        min-height: {min_height}px;
        font-size: {default_font_size}px;
        font-weight: bold;
        padding: {padding}px;
        border-style:solid;
        border-radius:4;
        border-color:grey;
        border-width:0;
        color: white;
    }}

    EventPushButton[Selected=true] {{
        font-size: {selected_font_size}px;
        background-color: {createGradient('#d4336a')};
    }}
    EventPushButton[Selected=true]:flat {{
        color: darkgrey;
        background-color: #f9e2ea;
    }}
    EventPushButton[Selected=true]:flat:!pressed:hover {{
        color: #F5F5F5;
        background-color: #e687a8;
    }}
    EventPushButton[Selected=true]:flat:pressed {{
        color: #EEEEEE;
        background-color: #d4336a;
    }}
    EventPushButton[Selected=true]:!flat:pressed {{
        color: white;
        background-color: {createGradient('#A61145')};
    }}
    EventPushButton[Selected=true]:!pressed:hover {{
        color: white;
        background-color: {createGradient('#cc0f50')};
    }}

    MajorEventPushButton[Selected=false]:flat {{
        color: darkgrey;
        background-color: #E0E0E0;
    }}
    MajorEventPushButton[Selected=false]:flat:!pressed:hover {{
        color: #F5F5F5;
        background-color: #CDCDCD;
    }}
    MajorEventPushButton[Selected=false]:flat:pressed {{
        color: #EEEEEE;
        background-color: #9E9E9E;
    }}
    MajorEventPushButton[Selected=false]:!flat:pressed {{
        color: #EEEEEE;
        background-color: {createGradient('#116999')};
    }}
    MajorEventPushButton[Selected=false]:!pressed:hover {{
        background-color: {createGradient('#1985ba')};
    }}

    MinorEventPushButton[Selected=false]:flat {{
        color: #BDBDBD;
        background-color: #EEEEEE;
    }}
    MinorEventPushButton[Selected=false]:flat:!pressed:hover {{
        color: #F5F5F5;
        background-color: #DDDDDD;
    }}
    MinorEventPushButton[Selected=false]:flat:pressed {{
        color: #EEEEEE;
        background-color: #BEBEBE;
    }}
    MinorEventPushButton[Selected=false]:!flat:pressed {{
        color: #EEEEEE;
        background-color: {createGradient('#147bb3')};
    }}
    MinorEventPushButton[Selected=false]:!pressed:hover {{
        background-color: {createGradient('#43a7cf')};
    }}

    AuxEventPushButton[Selected=false]:pressed {{
        background-color: {createGradient('#757575')};
    }}
    AuxEventPushButton[Selected=false]:!pressed:hover {{
        background-color: {createGradient('#9e9e9e')};
    }}
"""


@functools.lru_cache
def push_button_style(simulator:bool, button:str, min_width:int, font_size:int, border_radius:int) -> str:
    # defaults for regular mode:
    color = '#FCFCFC'
    color_disabled = 'darkgrey'
    color_pressed = '#EEEEEE'
    color_hovered = 'white'
    # defaults for simulator mode:
    background_color = 'white'
    background_color_disabled = '#E0E0E0'
    background_color_pressed = '#EEEEEE'
    background_color_hovered = '#F5F5F5'

    if button == 'RESET':
        background_color = '#4c97c3'
        background_color_disabled = 'lightgrey'
        background_color_pressed = '#1985ba'
        background_color_hovered = '#43a7cf'
    elif button == 'OFF':
        if simulator:
            color = '#147bb3'
            color_pressed = '#116D98'
            color_hovered = '#1985ba'
        else:
            background_color = '#3979ae'
            background_color_disabled = '#E0E0E0'
            background_color_pressed = '#116D98'
            background_color_hovered = '#1985ba'
    elif button == 'ON':
        if simulator:
            color = '#cc0f50'
            color_pressed = '#c70d49'
            color_hovered = '#d4336a'
        else:
            background_color = '#cc0f50'
            background_color_disabled = '#E0E0E0'
            background_color_pressed = '#c70d49'
            background_color_hovered = '#d4336a'
    elif button == 'STOP':
        if simulator:
            color = '#147bb3'
            color_pressed = '#116999'
            color_hovered = '#1985ba'
        else:
            background_color = '#3979ae'
            background_color_disabled = '#E0E0E0'
            background_color_pressed = '#116999'
            background_color_hovered = '#1985ba'
    elif button == 'PID':
        background_color = '#4c97c3'
        background_color_disabled = 'lightgrey'
        background_color_pressed = '#1985ba'
        background_color_hovered = '#43a7cf'
    elif button == 'PIDactive':
        background_color = '#cc0f50'
        background_color_disabled = 'lightgrey'
        background_color_pressed = '#c70d49'
        background_color_hovered = '#d4336a'
    return f"""
        QPushButton {{
            min-width: {min_width}px;
            padding-left: 8px;
            padding-right: 8px;
            border-style: solid;
            border-radius: {border_radius}px;
            border-color: grey;
            border-width: 0;
            font-size: {font_size}px;
            font-family: 'Nunito';
            font-weight: 800;
            color: {color};
            background-color: {background_color};
        }}
        QPushButton:!enabled {{
            color: {color_disabled};
            background-color: {background_color_disabled};
        }}
        QPushButton:pressed {{
            color: {color_pressed};
            background-color: {background_color_pressed};
        }}
        QPushButton:hover:!pressed {{
            color: {color_hovered};
            background-color: {background_color_hovered};
        }}
    """

@functools.lru_cache
def artisan_sv_plus_push_button_style(min_width:int, font_size:int, border_radius:int) -> str:
    return f"""
    QPushButton {{
        min-width: {min_width}px;
        border-style: solid;
        border-radius: {border_radius}px;
        border-color:grey;
        border-width:0;
        font-size: {font_size}px;
        font-weight: bold;
        color:white;
        background-color: {createGradient('#db5785')};
    }}
    QPushButton:pressed {{
        color: #EEEEEE;
        background-color: {createGradient('#d4336a')};
    }}
    QPushButton:hover:!pressed {{
        color: white;
        background-color: {createGradient('#e480a2')};
    }}
"""

@functools.lru_cache
def artisan_sv_minus_push_button_style(min_width:int, font_size:int, border_radius:int) -> str:
    return f"""
    QPushButton {{
        min-width: {min_width}px;
        border-style: solid;
        border-radius: {border_radius}px;
        border-color: grey;
        border-width: 0;
        font-size: {font_size}px;
        font-weight: bold;
        color: white;
        background-color: {createGradient('#64b7d8')};
    }}
    QPushButton:pressed {{
        color:#EEEEEE;
        background-color: {createGradient('#43a7cf')};
    }}
    QPushButton:hover:!pressed {{
        color:white;
        background-color: {createGradient('#85cae1')};
    }}
"""



# slider styles


@functools.lru_cache
def artisan_slider_style(dark:bool, color:str) -> str:
    return f"""
    QSlider::groove:vertical:focus {{
        background: {'#ddd' if dark else '#888'};
        border: 0.5px solid {'#aaa' if dark else '#666'};
        width: 3px;
        border-radius: 5px;
    }}
    QSlider::sub-page:vertical:focus {{
        background: {'#ddd' if dark else '#888'};
        border: 0.5px solid {'#aaa' if dark else '#666'};
        width: 85px;
        border-radius: 5px;
    }}
    QSlider::groove:vertical {{
        background: {'#888' if dark else '#ddd'};
        border: 0.5px solid {'#666'if dark else '#aaa'};
        width: 3px;
        border-radius: 5px;
    }}
    QSlider::sub-page:vertical {{
        background: {'#888' if dark else '#ddd'};
        border: 0.5px solid {'#666' if dark else '#aaa'};
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
        background: {'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #888, stop:1 #777)' if dark else 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fff, stop:1 #eee)'};
        border: 0.5px solid {'#666' if dark else '#ddd'};
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
        background: {'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #999, stop:1 #888)' if dark else 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ddd)'};
        border: 1px solid {'#777' if dark else '#ccc'};
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

@functools.lru_cache
def artisan_slider_frame_style(title_color:str, color:str, background_color:str) -> str:
    return f"""
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


@functools.lru_cache
def scroller_style(darkmode:bool) -> str:
    return f"""
    QScrollBar:vertical {{
        background-color: transparent;
        margin: 0px 0px 0px 8px;
        border-radius: 4px;
        width: 18px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {'#444444' if darkmode else '#BBBBBB'};
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {'#555555' if darkmode else '#A0A0A0'};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        background: none;
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background-color: transparent;
        margin: 8px 0px 0px 0px;
        border-radius: 4px;
        height: 18px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {'#444444' if darkmode else '#BBBBBB'};
        min-width: 20px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {'#555555' if darkmode else '#A0A0A0'};
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        background: none;
        height: 0px;
    }}
"""

# table styles

@functools.lru_cache
def table_style(darkmode:bool) -> str:
    return f"""
    QTableWidget {{
        border: none;
        border-radius: 6px;
        background-color: transparent;
    }}

    QTableView {{
        selection-background-color: {'#555555' if darkmode else '#DDDDDD'};
        selection-color: {'white' if darkmode else 'black'};
    }}

    QHeaderView {{
        background-color: transparent;
    }}
    QTableView QTableCornerButton::section {{
        background-color: transparent;
        border: none;
    }}

    QAbstractScrollArea::corner {{
        background-color: transparent;
        border: none;
    }}

    {scroller_style(darkmode)}

"""

@functools.lru_cache
def horizontal_header_style(darkmode:bool) -> str:
    return f"""
            QHeaderView::section {{
                background-color: {'#444444' if darkmode else '#FAFAFA'};
                color: {'#DDDDDD' if darkmode else '#555555'};
                border: 1px solid {'#333333' if darkmode else '#DDDDDD'};
                font-weight: bold;
            }}
            QTableWidget > QHeaderView::section {{
                padding: 2px;
            }}
            QTableWidget > QHeaderView::section:hover {{
                background-color: {'#818181' if darkmode else '#E1E1E1'};
            }}
            QTableWidget > QHeaderView::section:first {{
                border-top-left-radius: 10px;
            }}
            QTableWidget > QHeaderView::section:last {{
                border-top-right-radius: 10px;
            }}
    """

@functools.lru_cache
def vertical_header_style(darkmode:bool) -> str:
    return f"""
            QHeaderView::section {{
                background-color: {'#444444' if darkmode else '#FAFAFA'};
                color: {'#DDDDDD' if darkmode else '#555555'};
                border: 1px solid {'#333333' if darkmode else '#DDDDDD'};
                font-weight: normal;
            }}
            QTableWidget > QHeaderView::section {{
                padding-right: 6px;
            }}
            QTableWidget > QHeaderView::section:hover {{
                background-color: {'#818181' if darkmode else '#E1E1E1'};
            }}
            QTableWidget > QHeaderView::section:checked, QHeaderView::section:selected {{
                font-weight: bold;
                background-color: {'#515151' if darkmode else '#D1D1D1'};
            }}
            QTableWidget > QHeaderView::section:first {{
                border-top-left-radius: 10px;
            }}
            QTableWidget > QHeaderView::section:last {{
                border-bottom-left-radius: 10px;
            }}
        """


# Text edit styles

@functools.lru_cache
def text_edit_style(
        darkmode:bool,
        background_color: str|None = None,
        selection_background_color: str|None = None,
        border_color: str|None = None,
        color: str|None = None) -> str:
    return f"""
            QTextEdit, QPlainTextEdit, ClickableTextEdit {{
                background-color: {background_color if background_color is not None else 'palette(base)'};
                {f'selection-background-color: {selection_background_color};' if selection_background_color is not None else ''}
                color: {color if color is not None else 'palette(text)'};
                padding: 2px;
                border-radius: 10px;
                border-width: 1px;
                border-style: solid;
                border-color: {border_color if border_color is not None else 'rgb(216, 216, 216)'};
            }}
            QTextEdit:focus, QPlainTextEdit:focus, ClickableTextEdit:focus {{
                border-color: palette(accent);
            }}
            {scroller_style(darkmode)}
    """

# Line edit style


@functools.lru_cache
def line_edit_style(dark:bool = False, bold:bool = False, color:str = 'palette(text)', background_color:str = 'palette(base)', selection_background_color: str|None = None) -> str:
    return f"""
        QLineEdit {{
            font-weight: {'bold' if bold else 'normal'};
            border: 1px solid {'#555555' if dark else '#D6D6D6'};
            border-radius: 5px;
            color: {color};
            background-color: {background_color};
            {f'selection-background-color: {selection_background_color};' if selection_background_color is not None else ''}
            padding: 2px 5px 2px 5px; }}
        QLineEdit:focus {{
            border-color: palette(accent);
        }}
        QLineEdit:disabled {{
            border-color: {'#555555' if dark else '#b6b6b6'};
            color: {'#AEAEA3' if dark else '#8E8E93'};
            background-color: {'#5F5F5F' if dark else '#DFDFDF'};
        }}
    """


# Spin box style


@functools.lru_cache
def spin_box_style(dark:bool = False) -> str:
    up_icon_path = Path.as_posix(Path(os.path.join(getResourcePath(),'Icons'),
        ('arrow-up-01-stroke-rounded-white.svg' if dark else 'arrow-up-01-stroke-rounded.svg')))
    down_icon_path = Path.as_posix(Path(os.path.join(getResourcePath(),'Icons'),
        ('arrow-down-01-stroke-rounded-white.svg' if dark else 'arrow-down-01-stroke-rounded.svg')))
    up_icon_path_disabled = Path.as_posix(Path(os.path.join(getResourcePath(),'Icons'),
        ('arrow-up-01-stroke-rounded-light.svg' if dark else 'arrow-up-01-stroke-rounded-dark.svg')))
    down_icon_path_disabled = Path.as_posix(Path(os.path.join(getResourcePath(),'Icons'),
        ('arrow-down-01-stroke-rounded-light.svg' if dark else 'arrow-down-01-stroke-rounded-dark.svg')))
    return f"""
        QSpinBox, QDoubleSpinBox, QTimeEdit {{
            background-color: palette(base);
            border: 1px solid {'#555555' if dark else '#D6D6D6'};
            border-radius: 5px;
            padding-top: 2px;
            padding-bottom: 2px;
            color: palette(text);
            selection-background-color: palette(highlight);
        }}
        QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {{
            border-color: palette(accent);
            outline: none;
        }}
        QSpinBox:disabled, QDoubleSpinBox:disabled, QTimeEdit:disabled {{
            border-color: {'#555555' if dark else '#b6b6b6'};
            color: {'#AEAEA3' if dark else '#8E8E93'};
            background-color: {'#5F5F5F' if dark else '#DFDFDF'};
        }}
        QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button
        QTimeEdit:up-button, QTimeEdit::down-button {{
            background-color: transparent;
            subcontrol-origin: border;
            width: 16px;
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button,
        QTimeEdit::up-buton, QTimeEdit::up-button {{
            subcontrol-position: top right;
            subcontrol-origin: margin;
            border-top-right-radius: 4px;
            border-left: 1px solid {'#555555' if dark else '#D6D6D6'};
            border-bottom: 0px solid {'#555555' if dark else '#D6D6D6'};
            width: 15px;
            margin: 0px; /* Forces macOS to drop internal layout margins */
            margin-right: 1px;
            /* Shift the up button down slightly to cover the native 1-2px gap */
            position: relative;
            top: 1px;
        }}
        QSpinBox::up-button:focus, QDoubleSpinBox::up-button:focus, QTimeEdit::up-button:focus,
        QSpinBox::down-button:focus, QDoubleSpinBox::down-button:focus, QTimeEdit::down-button-focus {{
            border-color: palette(accent);
        }}

        QSpinBox::down-button, QDoubleSpinBox::down-button,
        QTimeEdit::down-button {{
            subcontrol-position: bottom right;
            subcontrol-origin: margin;
            border-bottom-right-radius: 4px;
            border-left: 1px solid {'#555555' if dark else '#D6D6D6'};
            border-top: 0px solid {'#555555' if dark else '#D6D6D6'};
            width: 15px;
            margin: 0px; /* Forces macOS to drop internal layout margins */
            margin-right: 1px;
            margin-bottom: 1px;
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover,
        QTimeEdit::up-button:hover, QTimeEdit::down-button:hover {{
            background-color: {'#454545' if dark else '#ececec'};
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow,
        QTimeEdit::up-arrow {{
            image: url({up_icon_path}); /* Replace with your resource path or use sub-pixel drawing */
            width: 9px;
            height: 9px;
        }}
        QSpinBox::up-arrow:disabled, QSpinBox::up-arrow:off, QDoubleSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:off,
        QTimeEdit::up-arrow:disabled, QTimeEdit::up-arrow:off {{
            image: url({up_icon_path_disabled});
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow,
        QTimeEdit:down-arrow {{
            image: url({down_icon_path});
            width: 9px;
            height: 9px;
        }}
        QSpinBox::down-arrow:disabled, QSpinBox::down-arrow:off, QDoubleSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:off,
        QTimeEdit::down-arrow:disabled, QTimeEdit::down-arrow:off  {{
            image: url({down_icon_path_disabled});
        }}
"""


# events editor style


@functools.lru_cache
def events_editor_style(dark:bool, background_color:str, line_edit_color:str) -> str:
    return f"""
    QGroupBox {{
        background-color: {background_color};
        border-width: 10px;
        border-style:solid;
        border-radius: 0;
        border-color: {background_color};
    }}
    QLabel#eventlabel {{
        background-color: {background_color if dark else '#F3F3F3'};
        color: {'#F3F3F3' if dark else '#333333'};
        border-width: 1;
        border-color: {'#F3F3F3' if dark else '#333333'};
        border-style:solid;
        border-radius: 6;
        min-height: 25px;
        max-height: 25px;
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
        border-color: {'#777777' if dark else '#b6b6b6'};
    }}
    QLineEdit:focus {{
        border: 1px solid palette(accent);
        padding: 2px 5px 2px 5px;
    }}
    QLineEdit#etimeline {{
        min-width: 50px;
    }}
    QLineEdit#valueEdit {{
        min-width: 25px;
    }}
    QSpinBox {{
        background-color: #E9E9E9;
        color: black;
        min-height: 25px;
        border-radius: 4;
        padding: 0px 5px;
    }}
    QPushButton#minieventleft {{
        background-color: {createGradient('#494949', alpha='55') if dark else createGradient('#E9E9E9')};
        color: { '#F3F3F3' if dark else '#333333' };
        border-top-left-radius: 10px;
        border-bottom-left-radius: 10px;
        min-width: 50px;
        min-height: 25px;
    }}
    QPushButton#minieventleft:pressed {{
        background-color: {createGradient('#696969', alpha='55') if dark else createGradient('#C9C9C9')};
    }}
    QPushButton#minieventleft:hover:!pressed {{
        background-color: {createGradient('#393939', alpha='55') if dark else createGradient('#F0F0F0')};
    }}
    QPushButton#minieventright {{
        background-color: {createGradient('#494949', alpha='55') if dark else createGradient('#E9E9E9')};
        color: { '#F3F3F3' if dark else '#333333' };
        border-width: 0;
        border-top-right-radius: 10px;
        border-bottom-right-radius: 10px;
        min-width: 50px;
        min-height: 25px;
    }}
    QPushButton#minieventright:pressed {{
        background-color: {createGradient('#696969', alpha='55') if dark else createGradient('#C9C9C9')};
    }}
    QPushButton#minieventright:hover:!pressed {{
        background-color: {createGradient('#393939', alpha='55') if dark else createGradient('#F0F0F0')};
    }}
    QPushButton#buttonminiEvent {{
        background-color: {createGradient('#494949', alpha='55') if dark else createGradient('#E9E9E9')};
        border-radius: 6px;
        color: { '#F3F3F3' if dark else '#333333' };
        min-width: 100px;
        min-height: 25px;
        border-width: 0;
    }}
    QPushButton#buttonminiEvent:pressed {{
        background-color: {createGradient('#696969', alpha='55') if dark else createGradient('#C9C9C9')};
    }}
    QPushButton#buttonminiEvent:hover:!pressed {{
        background-color: {createGradient('#393939', alpha='55') if dark else createGradient('#F0F0F0')};
    }}
"""


# toolbar style

@functools.lru_cache
def toolbar_style(color:str, background_color:str, border_color:str, selected_background_color:str) -> str:
    return f"""
        QToolBar {{
            background-color: {background_color};
            border: 0px solid;
            color: {color};
            spacing: 0px;
            margin: 0px;
        }}
        QToolBar::separator {{
            background-color: transparent;
        }}
        QToolButton:checked {{
            background-color: {selected_background_color};
        }}
        QToolButton:hover {{
            border-color: {border_color};
        }}
        QToolButton:checked:hover {{
            border-color: {border_color};
            background-color: {selected_background_color};
        }}
        QToolButton {{
            border-width: 1px;
            border-style: solid;
            border-radius: 5px;
            border-color: transparent;
            margin: 0px;
            padding: 1px;
            background-color: transparent;
        }}
    """



# ComboBox style

@functools.lru_cache
def combobox_style(dark:bool, down_arrow_icon_path:str, font_weight:str = 'normal',
        dark_background_color:str = '#57393939',
        view_dark_background_color:str = '#C7393939') -> str:
    return f"""
    QComboBox {{
        combobox-popup: 0;
        border: 1px solid {'#555555' if dark else '#b6b6b6'};
        border-radius: 5px;
        padding: 3px 10px 3px 8px;
        background: {dark_background_color if dark else 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #F5F5F5)'};
        color: {'#f5f5f5' if dark else '#333333'};
        font-weight: {font_weight};
        min-height: 22px;
        max-height: 22px;
    }}
    QComboBox:editable {{
        background: {'#882e2e2e' if dark else '#ffffff'};
    }}
    QComboBox:on {{
        border-color: palette(accent);
    }}
    QComboBox:hover {{
        border: 1px solid palette(accent);
    }}
    QComboBox:focus {{
        border: 1px solid palette(accent);
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left-width: 0px;
        border-top-right-radius: 5px;
        border-bottom-right-radius: 5px;
        margin-right:5px;
    }}
    QComboBox::down-arrow {{
        image: url({down_arrow_icon_path});
        width: 15px;
        height: 15px;
    }}
    QComboBox QAbstractItemView {{
        border: 1px solid {'#3a3a3a' if dark else '#D1D1D1'};
        border-radius: 6px;
        background-color: {view_dark_background_color if dark else '#FFFFFF'};
        color: {'#f5f5f5' if dark else '#333333'};
        selection-background-color: palette(accent);
        selection-color: #FFFFFF;
        font-weight: normal;
        outline: 0px;
        padding: 4px 0px;
    }}
    QComboBox QAbstractItemView::item:!enabled {{
        color: #CCCCCC;
    }}
    QComboBox QListView::item {{
        height: 24px;
        padding-left: 8px;
        background-color: transparent;
    }}
    QComboBox QListView::item:selected {{
        background-color: palette(accent);
        color: #FFFFFF;
        border-radius: 0px;
    }}
"""



# QLCD styles


@functools.lru_cache
def qlcd_style(color:str, background_color:str, border:bool) -> str:
    return f"""
        QLCDNumber, MyQLCDNumber {{
            border-width: {'1' if border else '0'};
            border-color: {color};
            border-radius: 8;
            color: {color};
            background-color: {background_color};
        }}
"""



# separator line style

@functools.lru_cache
def separator_line_style(dark:bool) -> str:
    return f"""
        QFrame[frameShape="4"] {{
            border: none;
            max-height: 2px;
            background-color: {'rgb(55, 55, 55)' if dark else 'rgb(216, 216, 216)'};
        }}
    """


# tool button frame style

@functools.lru_cache
def tool_button_frame_style(dark:bool) -> str:
    return f"""
        QFrame {{
            border-width: 1px;
            border-style: solid;
            border-color: {'rgb(65, 65, 65)' if dark else '#BBBBBB'};
            border-radius: 15px;
            background-color: {'#AA606060' if dark else '#F3F3F3'};
        }}
        QFrame:hover {{
            background-color: {'#AA707070' if dark else '#E0E0E0'};
        }}
        QFrame:pressed {{
            background-color: {'#AA777777' if dark else '#D0D0D0'};
        }}
        QFrame:disabled {{
            background-color: {'#555F5F5F' if dark else '#DFDFDF'};
            border-color: {'#555F5F5F' if dark else '#DFDFDF'};
        }}
    """

# dashboard style

# if group_border_class is True a background image is loaded
@functools.lru_cache
def dashboard_style(dark:bool, group_border_class:bool, canvas_color:str) -> str:
    return f"""
    QLabel {{
        background-color: transparent;
        border-style: none;
        border-width: 0px;
        color: {'#EEEEEE' if dark else 'rgb(102, 102, 102)'};
    }}
    QLabel:disabled {{
        color: {'#8F8F8F' if dark else '#8E8E93'};
    }}
    QGroupBox {{
        color: palette(buttontext);
        border-style:solid;
        border-width: 2px;
        border-radius: 18px;
        border-color: {('rgb(35, 35, 35)' if group_border_class else 'rgba(65, 65, 65, 50%)') if dark else
            ('rgb(240, 240, 240)' if group_border_class else 'rgb(210, 210, 210)')};
        background-color: {('rgba(41, 41, 41, 90%)' if dark else 'rgba(240, 240, 240, 90%)') if group_border_class
            else ('rgba(41, 41, 41, 50%)' if dark else 'rgba(240, 240, 240, 80%)')};
    }}
    QGroupBox:title {{
        top: 7px;
        left: 7px;
        color: rgb(40, 153, 199);
    }}

    QStackedWidget {{
        background-color: {canvas_color if group_border_class else 'transparent'};
    }}
    QGroupBox#inventory_group {{
        padding-top: 10px;
        border-width: 1px;
        border-style:solid;
        border-color: {'rgb(65, 65, 65)' if dark else 'rgb(216, 216, 216)'};
        border-radius: 10px;
        background-color: {'rgba(50, 50, 50, 60%)' if dark else 'rgb(245, 245, 245)'};
    }}
    QWidget#inventory_page {{
        background-color: {('rgba(50, 50, 50, 98%)' if group_border_class else 'transparent') if dark else 'rgb(245, 245, 245)'};
    }}
    QWidget#no_inventory_page {{
        background-color: {('rgba(50, 50, 50, 98%)' if group_border_class else 'transparent') if dark else 'rgb(245, 245, 245)'};
    }}
"""
