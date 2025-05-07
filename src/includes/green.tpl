<!doctype html>
<html lang="en">

<!-- 
Receives data in the shape of
{ 
  percent: 12.3, // number, [-1, 200]; -1: no bucket; 0: bucket
  weight: "20.4kg", // string, max 14 characters
  buckets: 2, // number, undefined or [0, 5]
  total_percent: 80.3, // number, undefined or [0, 200]
  total_weight: "55.3kg", // string, max 6 characters
  title: "Burundi A1", // string, "" removes title, null/undefined ignores; max ~50 characters
}
-->

<head>
    <meta charset="utf-8" />
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black">
    <meta name="apple-mobile-web-app-title" content="Artisan">
    <title>Task Green</title>
    <script type="text/javascript">
        var ws = new WebSocket("ws://localhost:5555/websocket");
        ws.onopen = function () {
            ws.send('');
        };
        ws.onmessage = function (evt) {
            const OVERFLOW_METHOD = 2; // 1 or 2

            var data = JSON.parse(evt.data);
            const scaleEl = document.getElementById('scale_rect');
            const bucketEl = document.getElementById('bucket');
            const percentEl = document.getElementById('percent_text');
            const totalPartEl = document.getElementById('total_grid_part');
            const totalPercentEl = document.getElementById('total_percent_text');
            const totalScaleEl = document.getElementById('total_rect');
            const scaleOverflowEl = document.getElementById('scale_rect_overflow');
            const overflowEl = document.getElementById('overflow');
            const gridEl = document.getElementById('grid_container');
            const bucketsPartEl = document.getElementById('buckets_grid_part');
            const titleEl = document.getElementById('title');
            const bucketsImagesEls = document.getElementsByName('bucket_img');

            gridEl.style['grid-template-columns'] = 'auto';

            scaleOverflowEl.style.display = 'none';
            overflowEl.style.display = 'none';
            totalPartEl.style.display = 'none';
            bucketsPartEl.style.display = 'none';
            bucketEl.style.color = '#515151';
            bucketEl.style['background-color'] = 'white';
            percentEl.style.color = 'black';
            totalPercentEl.style.color = 'black';
            totalScaleEl.style.background = 'none';

            if (data) {
                // title
                if (data.title || data.title === '') {
                    titleEl.textContent = data.title;
                }

                // switch on/off: total bar | main scale | buckets
                if (data.buckets) {
                    bucketsPartEl.style.display = 'flex';
                    if (data.total_percent >= 0) {
                        gridEl.style['grid-template-columns'] = '60px auto 60px';
                        totalPartEl.style.display = 'block';
                    } else {
                        gridEl.style['grid-template-columns'] = 'auto 60px';
                    }
                } else if (data.total_percent >= 0) {
                    gridEl.style['grid-template-columns'] = '60px auto';
                    totalPartEl.style.display = 'block';
                } else {
                    gridEl.style['grid-template-columns'] = 'auto';
                }

                // display number of buckets
                for (let i = 0; i < bucketsImagesEls.length; i++) {
                    const el = bucketsImagesEls[i];
                    if (el && el.style) {
                        el.style.display = i < (data.buckets || 0) ? 'block' : 'none';
                    }
                }

                // main scale
                if (data.percent >= 0) {
                    // display bucket and %
                    bucketEl.style.display = 'flex';
                    percentEl.style.display = 'block';
                    percentEl.innerHTML = data.percent.toFixed(0) + '%';

                    if (data.percent > 0) {
                        if (data.percent <= 100) {
                            scaleEl.style.background = 'linear-gradient(0deg, #2098c7 0 ' + data.percent + '%, white ' + data.percent + '% 100%)';
                            if (data.percent === 100) {
                                bucketEl.style.color = 'white';
                                bucketEl.style['background-color'] = '#2098c7';
                                percentEl.style.color = 'white';
                            }
                        } else {
                            // overflow
                            bucketEl.style.color = 'white';
                            bucketEl.style['background-color'] = '#cd0750';
                            percentEl.style.color = 'white';
                            scaleEl.style.background = 'none';

                            if (OVERFLOW_METHOD === 1) {
                                scaleOverflowEl.style.display = 'block';
                                let ind = (data.percent - 100) + '%';
                                if (ind > 50) ind = 50;
                                const indent = ind + '%';
                                scaleOverflowEl.style.top = indent;
                                scaleOverflowEl.style.bottom = indent;
                                scaleOverflowEl.style.left = indent;
                                scaleOverflowEl.style.right = indent;
                            } else {
                                overflowEl.style.display = 'block';
                                let ind2 = (100 - ((data.percent - 100) * 2 + 45)) / 2;
                                let indent2 = ind2 + '%';
                                if (ind2 < 0) {
                                    overflowEl.style['border-radius'] = '3%';
                                    indent2 = 0;
                                } else {
                                    overflowEl.style['border-radius'] = '100%';
                                }
                                overflowEl.style.top = indent2;
                                overflowEl.style.bottom = indent2;
                                overflowEl.style.left = indent2;
                                overflowEl.style.right = indent2;
                            }
                        }
                    }
                } else {
                    bucketEl.style.display = 'none';
                    percentEl.style.display = 'none';
                }

                // total bar (left side)
                if (data.total_percent >= 0) {
                    totalPercentEl.style.display = 'block';
                    totalPercentEl.innerHTML = data.total_percent.toFixed(0) + '%';

                    if (data.total_percent > 0) {
                        if (data.total_percent <= 100) {
                            totalScaleEl.style.background = 'linear-gradient(0deg, #2098c7 0 ' + data.total_percent + '%, white ' + data.total_percent + '% 100%)';
                            if (data.total_percent === 100) {
                                totalPercentEl.style.color = 'white';
                            }
                        } else {
                            // overlap
                            totalPercentEl.style.color = 'white';
                            totalScaleEl.style.background = '#cd0750';
                            // TODO
                        }
                    }
                } else {
                    totalPercentEl.style.display = 'none';
                }
            }

            if (parseFloat(data.weight) >= 0) {
                document.getElementById('weight_text').innerHTML = data.weight;
            } else {
                document.getElementById('weight_text').innerHTML = '';
            }
            if (parseFloat(data.total_weight) >= 0) {
                document.getElementById('total_weight_text').innerHTML = data.total_weight;
            } else {
                document.getElementById('total_weight_text').innerHTML = '';
            }
        };
    </script>
    <style type='text/css'>
        html {
            background-color: white;
            width: 100%;
            height: 100%;
            position: relative;
            font-family: sans-serif;
        }

        .title {
            font-size: 23px;
            text-align: center;
            margin-top: 10px;
            white-space: nowrap;
            font-family: sans-serif;
        }

        .scale_div {
            position: relative;
        }

        .grid_container {
            display: grid;
            grid-template-columns: auto;
            padding: 10px;
        }

        @media(orientation:landscape) {
            .scale_rect {
                max-height: calc(100vh - 140px);
            }
        }

        .scale_rect {
            /* transition: background 0.5s ease-in-out; */
            position: relative;
            min-height: 150px;
            min-width: 150px;
            border: 5px solid #515151;
            border-radius: 5%;
            margin-left: auto;
            margin-right: auto;
            aspect-ratio: 1 / 1;
        }

        .scale_rect_overflow {
            display: none;
            transition: width 0.5s ease-in-out;
            background-color: #2098c7;
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            top: 0;
            border-radius: 5%;
        }

        .bucket {
            position: absolute;
            background-color: white;
            width: 45%;
            height: 45%;
            top: calc(27.5% - 5px);
            left: calc(27.5% - 5px);
            border: 5px solid #515151;
            border-radius: 100%;
            display: none;
            align-content: center;
            justify-content: center;
        }

        .overflow {
            color: white;
            background-color: #cd0750;
            display: flex;
            z-index: -1;
            position: absolute;
            border-radius: 100%;
        }

        .percent_text {
            /* font-family: sans-serif; */
            margin-top: auto;
            margin-bottom: auto;
            background: none;
        }

        .big_font {
            font-size: calc(max(min(10vw, 10vh), 23px));
            text-align: center;
        }

        .smaller_big_font {
            font-size: 20px;
        }

        .weight_text {
            margin-top: 5px;
            text-align: center;
            /* font-family: sans-serif; */
        }

        .buckets_grid_part {
            /* background-color: green; */
            display: flex;
            justify-content: center;
            align-content: space-evenly;
            flex-wrap: wrap;
            width: 60px;
            margin-left: auto;
            margin-right: auto;
        }

        .bucket_img {
            display: none;
            margin-right: 10px;
        }

        .total_grid_part {
            display: none;
            width: 60px;
        }

        .total_rect {
            position: relative;
            /* reduce by 2x border width */
            height: calc(100% - 10px);
            width: 45px;
            border: 5px solid #515151;
            border-radius: 15px;
            display: flex;
            justify-content: center;
            align-content: center;
            flex-wrap: wrap;
        }

        .total_weight_text {
            background: none;
            text-align: center;
            margin-top: 10px;
        }
    </style>
</head>

<body>
    <div class="title" id="title"></div>

    <div class="grid_container" id="grid_container">
        <div class="total_grid_part" id="total_grid_part">
            <div class="total_rect" id="total_rect">
                <span class="total_percent_text smaller_big_font" id="total_percent_text"></span>
            </div>
            <div class="total_weight_text smaller_big_font" id="total_weight_text">
            </div>
        </div>

        <div class="scale_div">
            <div class="scale_rect" id="scale_rect">
                <div class="scale_rect_overflow" id="scale_rect_overflow"></div>
                <span class="bucket" id="bucket">
                    <span class="percent_text big_font" id="percent_text"></span>
                </span>
                <span class="overflow" id="overflow">
                </span>
            </div>
        </div>

        <div class="buckets_grid_part" id="buckets_grid_part">
            <div class="bucket_img" name="bucket_img"><img src="bucket.svg" height="30" width="28" alt="bucket"></div>
            <div class="bucket_img" name="bucket_img"><img src="bucket.svg" height="30" width="28" alt="bucket"></div>
            <div class="bucket_img" name="bucket_img"><img src="bucket.svg" height="30" width="28" alt="bucket"></div>
            <div class="bucket_img" name="bucket_img"><img src="bucket.svg" height="30" width="28" alt="bucket"></div>
            <div class="bucket_img" name="bucket_img"><img src="bucket.svg" height="30" width="28" alt="bucket"></div>
        </div>
    </div>

    <div class="weight_text big_font" id="weight_text">
    </div>

    <!-- <script src="jquery-1.11.1.min.js"></script> -->
    <!-- <script>
        $(document).ready(function () {
            $(window).load(function () {
                $('#artisan').bigtext();
            });
        });
    </script> -->
</body>

</html>