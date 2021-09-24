# -*- coding: utf-8 -*-

from artisanlib.util import createGradient

artisan_event_button_style = """
            QPushButton {{ 
                min-width: {min_width};
                font-size: {default_font_size};
                font-weight: bold;
                padding: 3px;
                border-style:solid;
                border-radius:4;
                border-color:grey;
                border-width:0;
                color: white;
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
            

            QPushButton[Selected=true] {{
                font-size: {selected_font_size};
                background-color:""" + createGradient('#d4336a') + """ ;
            }}
            QPushButton[Selected=true]:flat {{
                color: darkgrey;
                background-color: #f9e2ea;
            }}
            QPushButton[Selected=true]:flat:!pressed:hover {{
                color: #F5F5F5;
                background-color: #e687a8;
            }}
            QPushButton[Selected=true]:flat:pressed {{
                color: #EEEEEE;
                background-color: #d4336a;
            }}
            QPushButton[Selected=true]:!flat:pressed {{
                color: white;
                background-color:""" + createGradient('#A61145') + """ ;
            }}
            QPushButton[Selected=true]:!pressed:hover {{
                color: white;
                background-color:""" + createGradient('#cc0f50') + """ ;
            }}
            
            
            AuxEventPushButton[Selected=false]:pressed {{
                background-color:""" + createGradient('#757575') + """ ;
            }}
            AuxEventPushButton[Selected=false]:!pressed:hover {{
                background-color:""" + createGradient('#9e9e9e') + """ ;
            }}
"""