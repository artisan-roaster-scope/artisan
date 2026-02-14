artisan_slider_style_dark = """
            QSlider::groove:vertical:focus {{
                background: #3a3a5a;
                border: 0.5px solid #4a4a6a;
                width: 3px;
                border-radius: 5px;
            }}
            QSlider::sub-page:vertical:focus {{
                background: #3a3a5a;
                border: 0.5px solid #4a4a6a;
                width: 85px;
                border-radius: 5px;
            }}
            QSlider::groove:vertical {{
                background: #2a2a4a;
                border: 0.5px solid #3a3a5a;
                width: 3px;
                border-radius: 5px;
            }}
            QSlider::sub-page:vertical {{
                background: #2a2a4a;
                border: 0.5px solid #3a3a5a;
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
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4a4a6a, stop:1 #2a2a4a);
                border: 0.5px solid #5a5a7a;
                height: 10px;
                margin-top: -1px;
                margin-bottom: -1px;
                margin-left: -15px;
                margin-right: -15px;
                border-radius: 5px;
            }}
            QSlider::handle:vertical:!hover:focus {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5a5a7a, stop:1 #3a3a5a);
                border: 1px solid #6a6a8a;
                border-radius: 5px;
            }}
            QSlider::handle:vertical:hover:focus {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6a6a8a, stop:1 #4a4a6a);
                border: 1px solid #7a7a9a;
                border-radius: 5px;
            }}
            QSlider::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5a5a7a, stop:1 #3a3a5a);
                border: 1px solid #6a6a8a;
                border-radius: 5px;
            }}
            QSlider::sub-page:vertical:disabled {{
                background: #2a2a3a;
                border-color: #3a3a4a;
            }}
            QSlider::add-page:vertical:disabled {{
                background: #1a1a2e;
                border-color: #2a2a3e;
            }}
            QSlider::handle:vertical:disabled {{
                background: #2a2a3a;
                border: 1px solid #3a3a4a;
                border-radius: 5px;
            }}
"""

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
