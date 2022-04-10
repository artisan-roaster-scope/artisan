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
            QSlider::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc);
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
