#
# ABOUT
# artisan scope button styles
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

artisan_event_button_style: str = """
            QFrame {{
                background-color: {background_color};
                border-width: 0px;
            }}

            EventPushButton {{
                min-width: {min_width}px;
                min-height: {min_height}px;
                font-size: {default_font_size}pt;
                font-weight: bold;
                padding: {padding}px;
                border-style:solid;
                border-radius:4;
                border-color:grey;
                border-width:0;
                color: white;
            }}

            EventPushButton[Selected=true] {{
                font-size: {selected_font_size}pt;
                background-color:""" + createGradient('#d4336a') + """ ;
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
                background-color:""" + createGradient('#A61145') + """ ;
            }}
            EventPushButton[Selected=true]:!pressed:hover {{
                color: white;
                background-color:""" + createGradient('#cc0f50') + """ ;
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
                background-color:""" + createGradient('#116999') + """ ;
            }}
            MajorEventPushButton[Selected=false]:!pressed:hover {{
                background-color:""" + createGradient('#1985ba') + """ ;
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
                background-color:""" + createGradient('#147bb3') + """ ;
            }}
            MinorEventPushButton[Selected=false]:!pressed:hover {{
                background-color:""" + createGradient('#43a7cf') + """ ;
            }}

            AuxEventPushButton[Selected=false]:pressed {{
                background-color:""" + createGradient('#757575') + """ ;
            }}
            AuxEventPushButton[Selected=false]:!pressed:hover {{
                background-color:""" + createGradient('#9e9e9e') + """ ;
            }}
"""
