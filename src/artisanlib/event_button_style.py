from artisanlib.util import createGradient

artisan_event_button_style_dark: str = """
            EventPushButton {{
                min-width: {min_width}px;
                min-height: {min_height}px;
                font-size: {default_font_size}pt;
                font-weight: bold;
                padding: {padding}px;
                border-style:solid;
                border-radius:4;
                border-color:#3a3a5a;
                border-width:0;
                color: #e0e0e0;
            }}

            EventPushButton[Selected=true] {{
                font-size: {selected_font_size}pt;
                background-color:""" + createGradient('#ff6b6b') + """ ;
            }}
            EventPushButton[Selected=true]:flat {{
                color: #9e9e9e;
                background-color: #2a2a4a;
            }}
            EventPushButton[Selected=true]:flat:!pressed:hover {{
                color: #e0e0e0;
                background-color: #4a2d3d;
            }}
            EventPushButton[Selected=true]:flat:pressed {{
                color: #e0e0e0;
                background-color: #ff6b6b;
            }}
            EventPushButton[Selected=true]:!flat:pressed {{
                color: white;
                background-color:""" + createGradient('#cc4444') + """ ;
            }}
            EventPushButton[Selected=true]:!pressed:hover {{
                color: white;
                background-color:""" + createGradient('#ff8888') + """ ;
            }}

            MajorEventPushButton[Selected=false]:flat {{
                color: #9e9e9e;
                background-color: #2a2a4a;
            }}
            MajorEventPushButton[Selected=false]:flat:!pressed:hover {{
                color: #e0e0e0;
                background-color: #3a3a5a;
            }}
            MajorEventPushButton[Selected=false]:flat:pressed {{
                color: #e0e0e0;
                background-color: #4a4a6a;
            }}
            MajorEventPushButton[Selected=false]:!flat:pressed {{
                color: #e0e0e0;
                background-color:""" + createGradient('#2d3d4a') + """ ;
            }}
            MajorEventPushButton[Selected=false]:!pressed:hover {{
                background-color:""" + createGradient('#42a5f5') + """ ;
            }}

            MinorEventPushButton[Selected=false]:flat {{
                color: #7a7a9a;
                background-color: #1a1a2e;
            }}
            MinorEventPushButton[Selected=false]:flat:!pressed:hover {{
                color: #e0e0e0;
                background-color: #2a2a4a;
            }}
            MinorEventPushButton[Selected=false]:flat:pressed {{
                color: #e0e0e0;
                background-color: #3a3a5a;
            }}
            MinorEventPushButton[Selected=false]:!flat:pressed {{
                color: #e0e0e0;
                background-color:""" + createGradient('#2d4a3e') + """ ;
            }}
            MinorEventPushButton[Selected=false]:!pressed:hover {{
                background-color:""" + createGradient('#4ecdc4') + """ ;
            }}

            AuxEventPushButton[Selected=false]:pressed {{
                background-color:""" + createGradient('#3a3a5a') + """ ;
            }}
            AuxEventPushButton[Selected=false]:!pressed:hover {{
                background-color:""" + createGradient('#4a4a6a') + """ ;
            }}
"""

artisan_event_button_style: str = """
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
