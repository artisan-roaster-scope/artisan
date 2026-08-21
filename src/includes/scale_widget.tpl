<!doctype html>
<html id="html">

<!-- 
Receives data in the shape of
{ 
    id:str (blend component / roast batch nr) | max 6 characters
    title:str
    subtitle:str
    batchsize:str | max ~6 characters
    weight:str | max 6 characters
    final_weight:str | max 6 characters
    percent: float
    state:int (0:disconnected, 1:connected, 2:weighing, 3:done, 4:canceled)
    bucket: int (0,1,2)
    blend_percent: str | max ~6 characters
    total_percent: float
    type:int (0:green, 1: roasted, 2:defects)
    message: str
    loss: str (for type 1)
    timer: int (in seconds)
    allow_click: 0 | 1
    accuracy: float (0: no zoom; 0-10% start of zoom)
}
-->

<head>
    <meta charset="utf-8" />
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-status-bar-style" content="black">
    <meta name="mobile-web-app-title" content="{{window_title}}">
    <!-- use local fonts -->
    <!-- <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;600"> -->
    <title>{{window_title}}</title>
    <noscript>
        <style type="text/css">
            .nojsnoshow {
                display: none;
            }
        </style>
        <div class="noscriptmsg">
            This display cannot work without JavaScript turned on, sorry!
        </div>
    </noscript>

    <!-- load local fonts  -->
    <style type='text/css'>
        /* roboto-300 */
        @font-face {
            font-family: 'Roboto';
            font-style: normal;
            font-weight: 300;
            font-stretch: 100%;
            src: url('roboto-300.woff2') format('woff2');
        }

        /* roboto-regular */
        @font-face {
            font-family: 'Roboto';
            font-style: normal;
            font-weight: 400;
            src: url('roboto-regular.woff2') format('woff2');
        }

        /* roboto-600 */
        @font-face {
            font-family: 'Roboto';
            font-style: normal;
            font-weight: 600;
            src: url('roboto-600.woff2') format('woff2');
        }
    </style>

    <script type="text/javascript" src="fitty_patched.js"></script>
    <script type="text/javascript">
        // @ts-check

        // if true, will not use a websocket but display some manual inputs
        const NOWEBSOCKET = false;
        let final_weight = 0.8;

        // if true, will use port 5555, otherwise {{port}}
        const RUNON5555 = false;

        // how often the websocket will be tried if not open in ms
        const WEBSOCKET_RECONNECT_INTERVAL = 10000;

        // how long the initial dialog (click to go fullscreen) is displayed
        // it is only shown on mobile devices (~90% hit rate)
        // if 0, it will not be displayed
        const CLICK_FOR_FULLSCREEN_DISPLAY_TIME_MS = 2000;

        // if true, scale is red if percent > 102.5 and frame is red if total_percent > 100
        const USERED = false;

        // in %; show "100%" if within +/- TARGET_DEVIATION; for 0.1, this is 5g for 5kg, 20g for 20kg, ...
        // 0.5 aligns with the rounded 100% dispolay value
        const TARGET_DEVIATION = 0.5;


        /** @type WebSocket | null */
        let websocket;
        /** @type WebSocket */
        let ws;

        /** @type { {[name: string]: HTMLElement} } */
        const elements = {};
        /** @type { {[name: string]: NodeListOf<HTMLElement>} } */
        const multiElements = {};
        /** @type { {[name: string]: HTMLDialogElement} } */
        const dialogs = {};

        const ABLUE = '#2098c7';
        const ARED = '#c70c49';
        let DARKMODE = false;
        let BACKGROUND = 'white';
        let PERCENTCOLOR = 'black';
        let TITLECOLOR = '515151';
        let BUCKETCOLOR = 'rgb(50, 50, 50)';
        let BORDER = '0.5vmin solid #515151';
        let BUCKETPOSITION = 'calc(12% - 0.75vmin)';

        const DISCONNECTED = 0;
        const CONNECTED = 1;
        const WEIGHING = 2;
        const DONE = 3;
        const CANCELLED = 4;

        const TYPE_GREEN = 0;
        const TYPE_ROASTED = 1;
        const TYPE_DEFECTS = 2;

        /** @type { { data: string } } */
        let lastdata;

        /** @type { { id: string, title: string, subtitle: string,
         * batchsize: string, weight: string, percent: number,
         * state: DISCONNECTED | CONNECTED | WEIGHING | DONE | CANCELLED,
         * bucket: 0 | 1 | 2, blend_percent: string, total_percent: number,
         * type: TYPE_GREEN | TYPE_ROASTED | TYPE_DEFECTS, message: string,
         * timer: number, loss: string, allow_click: 0 | 1, accuracy: number } } */
        let parsedData;

        /** @type HTMLDialogElement | undefined */
        let showingMessageDialog = undefined;
        /** @type HTMLDialogElement | undefined */
        let showingCancelDialog = undefined;
        /** @type HTMLDialogElement | undefined */
        let showingTimerDialog = undefined;
        let timerVal = 0;
        let interval;

        let allowClick = false;
        let accuracy = 10;

        function getAllElements() {
            elements.html = document.getElementsByTagName('html')[0];

            for (const prop of ['id', 'batchsize', 'scale_rect',
                'percent', 'zoom', 'zoom2', 'scale_for_clipping',
                'scale_icon_done', 'scale_icon_initial',
                'blend_percent', 'buckets_grid_part',
                'weight', 'final_weight', 'scale_icon_image', 'bucket_on_scale',
                'coffee_svg', 'roast_svg', 'done_svg', 'cancel_svg',
                'dialog_cancel_svg', 'dialog_close_icon', 'dialog_fullscreen_svg',
                'dialog_text', 'dialog_svg',
                'coffee_svg_dark', 'roast_svg_dark',
                'outer_frame', 'outerdiv',
                'timer_progress']) {
                // 'cancel_button', 'ok_button']) {
                const el = document.getElementById(prop);
                if (el) {
                    elements[prop] = el;
                }
            }
            for (const prop of ['cancel_dialog', 'text_dialog', 'fullscreen_dialog']) {
                const el = document.getElementById(prop);
                if (el) {
                    dialogs[prop] = /** @type HTMLDialogElement */(el);
                }
            }

            for (const prop of ['title', 'buckets_images', 'subtitle']) {
                multiElements[prop] = document.getElementsByName(prop);
            }

            // TODO remove test slider BEGIN
            if (NOWEBSOCKET) {
                const finalweight = document.getElementById('testfinalweight');
                if (finalweight) {
                    finalweight.addEventListener('input', (e) => {
                        final_weight = parseFloat(e.target?.['value'] || '0.8');
                        const perc = parsedData.percent || 85;
                        const accuracy = parsedData.accuracy ?? 10;
                        const finalWeightStr = final_weight.toFixed(1) + 'kg';
                        const remainingWeightStr = (1 - perc / 100) * final_weight > 0.5 ? (-(1 - perc / 100) * final_weight).toFixed(1) + 'kg' : (-(1 - perc / 100) * final_weight * 1000).toFixed(0) + 'g';
                        const json = { accuracy, type: 0, state: 2, percent: perc, weight: remainingWeightStr, final_weight: finalWeightStr, bucket: 2, id: '2/3', blend_percent: '33%', title: 'Mount "Huehuetenango"', batchsize: '12kg', subtitle: 'Kenia "Mount Huehuetenango" Selection', /* timer: 5 */ };
                        usedata({ data: JSON.stringify(json) });
                    });
                }
                const slider = document.getElementById('testpercent');
                if (slider) {
                    slider.addEventListener('input', (e) => {
                        const perc = parseFloat(e.target?.['value'] || '1');
                        parsedData.percent = perc;
                        const finalWeightStr = final_weight.toFixed(1) + 'kg';
                        const remainingWeightStr = (1 - perc / 100) * final_weight > 0.5 ? (-(1 - perc / 100) * final_weight).toFixed(1) + 'kg' : (-(1 - perc / 100) * final_weight * 1000).toFixed(0) + 'g';
                        const json = { accuracy, type: 0, state: 2, percent: perc, weight: remainingWeightStr, final_weight: finalWeightStr, bucket: 2, id: '2/3', blend_percent: '33%', title: 'Mount "Huehuetenango"', batchsize: '12kg', subtitle: 'Kenia "Mount Huehuetenango" Selection', /* timer: 5 */ };
                        usedata({ data: JSON.stringify(json) });
                    });
                }
                const accuracyInput = document.getElementById('testaccuracy');
                if (accuracyInput) {
                    accuracyInput.addEventListener('input', (e) => {
                        accuracy = parseFloat(e.target?.['value'] ?? '10');
                        parsedData.accuracy = accuracy;
                        const finalWeightStr = final_weight.toFixed(1) + 'kg';
                        const perc = lastdata ? JSON.parse(lastdata.data).percent || 85 : 85;
                        const remainingWeightStr = (1 - perc / 100) * final_weight > 0.5 ? (-(1 - perc / 100) * final_weight).toFixed(1) + 'kg' : (-(1 - perc / 100) * final_weight * 1000).toFixed(0) + 'g';
                        const json = { accuracy, type: 0, state: 2, percent: perc, weight: remainingWeightStr, final_weight: finalWeightStr, bucket: 2, id: '2/3', blend_percent: '33%', title: 'Mount "Huehuetenango"', batchsize: '12kg', subtitle: 'Kenia "Mount Huehuetenango" Selection', /* timer: 5 */ };
                        usedata({ data: JSON.stringify(json) });
                    });
                }
            } else {
                document.getElementById('testfinalweightspan')?.remove();
                document.getElementById('testpercentspan')?.remove();
                document.getElementById('testaccuracyspan')?.remove();
            }
            // END
        }

        function setInitialStyles() {
            elements.html.style.backgroundColor = BACKGROUND;
            elements.bucket_on_scale.style.backgroundColor = BACKGROUND;
            elements.bucket_on_scale.style.color = PERCENTCOLOR;
            elements.percent.style.color = PERCENTCOLOR;
            elements.weight.style.color = PERCENTCOLOR;
            elements.bucket_on_scale.style.border = BORDER;
            elements.bucket_on_scale.style.top = BUCKETPOSITION;
            elements.bucket_on_scale.style.left = BUCKETPOSITION;
            elements.scale_rect.style.border = BORDER;
            multiElements.title.forEach(el => el.style.color = TITLECOLOR);
            multiElements.subtitle.forEach(el => el.style.color = TITLECOLOR);
            multiElements.buckets_images.forEach(el => el.style.display = 'none');
            elements.buckets_grid_part.style.stroke = BUCKETCOLOR;
            elements.dialog_svg.style.display = 'none';
            if (DARKMODE) {
                elements.outerdiv.style.background = '#515151';
            } else {
                elements.outerdiv.style.background = '#fefefe';
            }
        }

        function resetStyles() {
            elements.coffee_svg.style.display = 'none';
            elements.coffee_svg_dark.style.display = 'none';
            elements.roast_svg.style.display = 'none';
            elements.roast_svg_dark.style.display = 'none';
            elements.done_svg.style.display = 'none';
            elements.cancel_svg.style.display = 'none';
            elements.scale_icon_initial.className = "scale-icon";
            elements.scale_icon_initial.style.display = 'none';
            elements.scale_icon_initial.style.backgroundColor = 'rgba(0, 0, 0, 0)';
            elements.scale_rect.style.background = 'none';
            elements.scale_rect.style.backgroundColor = 'rgba(0, 0, 0, 0)';
            elements.bucket_on_scale.style.backgroundColor = BACKGROUND;
            elements.zoom.style.display = 'none';
            elements.zoom.style.position = 'absolute';
            elements.zoom2.style.display = 'none';
            elements.scale_for_clipping.style.display = 'none';
            elements.outer_frame.style.background = '#b5b5b5';
            elements.percent.style.color = 'black';
            elements.weight.style.color = 'black';
            // elements.percent.style.top = '-10%';
        }

        function setTexts() {
            for (const prop of ['id', 'batchsize', 'weight', 'final_weight', 'blend_percent']) {
                elements[prop].textContent = parsedData[prop] || '';
            }
            for (const prop of ['title', 'subtitle',]) {
                // there are 2 of each (only one ever displayed)
                multiElements[prop].forEach(el => el.textContent = parsedData[prop] || '');
            }
            for (const prop of ['percent']) {
                if (Number.isFinite(parsedData[prop])) {
                    elements[prop].textContent = Math.round(parsedData[prop]) + '%';
                } else {
                    elements[prop].textContent = '';
                }
            }
        }

        const usedata = (/** @type { { data: string } } */ evt) => {
            lastdata = evt;
            parsedData = JSON.parse(evt.data);

            if (parsedData) {
                resetStyles();
                setTexts();

                accuracy = parsedData.accuracy ?? 10;

                allowClick = !!parsedData.allow_click;
                if (allowClick && !showingTimerDialog && !showingCancelDialog && !showingMessageDialog) {
                    document.body.addEventListener("click", processClick);
                } else if (!allowClick) {
                    document.body.removeEventListener("click", processClick);
                }

                // display number of buckets
                for (let i = 0; i < multiElements.buckets_images.length; i++) {
                    const el = multiElements.buckets_images[i];
                    if (el && el.style) {
                        el.style.display = i < (parsedData.bucket || 0) ? 'block' : 'none';
                    }
                }

                elements.timer_progress.style.setProperty('--progress-color', '#2098c7');

                switch (parsedData.state) {
                    case DISCONNECTED:
                        elements.scale_rect.style.display = 'none';
                        elements.scale_icon_initial.style.display = 'block';
                        elements.scale_icon_done.style.display = 'none';
                        elements.scale_icon_initial.style.fill = '#e5e5e5';
                        if (parsedData.type === TYPE_GREEN || parsedData.type === TYPE_DEFECTS) {
                            if (DARKMODE) {
                                elements.coffee_svg_dark.style.display = 'block';
                            } else {
                                elements.coffee_svg.style.display = 'block';
                            }
                        } else if (parsedData.type === TYPE_ROASTED) {
                            if (DARKMODE) {
                                elements.roast_svg_dark.style.display = 'block';
                            } else {
                                elements.roast_svg.style.display = 'block';
                            }
                        }
                        break;

                    case CONNECTED:
                        elements.scale_rect.style.display = 'none';
                        elements.scale_icon_initial.className = "scale-icon scale-rect";
                        elements.scale_icon_initial.style.display = 'block';
                        elements.scale_icon_initial.style.backgroundColor = '#cbcbcb';
                        elements.scale_icon_initial.style.fill = BACKGROUND;
                        elements.scale_icon_done.style.display = 'none';
                        elements.bucket_on_scale.style.display = 'none';
                        if (parsedData.type === TYPE_GREEN || parsedData.type === TYPE_DEFECTS) {
                            if (DARKMODE) {
                                elements.coffee_svg_dark.style.display = 'block';
                            } else {
                                elements.coffee_svg.style.display = 'block';
                            }
                        } else if (parsedData.type === TYPE_ROASTED) {
                            if (DARKMODE) {
                                elements.roast_svg_dark.style.display = 'block';
                            } else {
                                elements.roast_svg.style.display = 'block';
                            }
                        }
                        break;

                    case DONE:
                        elements.scale_rect.style.display = 'block';
                        elements.scale_rect.style.backgroundColor = ABLUE;
                        elements.timer_progress.style.setProperty('--progress-color', 'white');

                        if (!parsedData.percent) {
                            elements.scale_icon_done.style.display = 'block';
                            elements.scale_icon_done.style.fill = 'white';
                            elements.done_svg.style.display = 'block';
                            elements.bucket_on_scale.style.display = 'none';
                            elements.bucket_on_scale.style.border = BORDER;
                            elements.percent.style.color = 'black';
                            elements.weight.style.color = 'black';
                        } else {
                            elements.bucket_on_scale.style.display = 'block';
                            elements.bucket_on_scale.style.backgroundColor = ABLUE;
                            elements.bucket_on_scale.style.border = '1.2vmin solid white';
                            elements.percent.style.color = 'white';
                            elements.weight.style.color = 'white';
                        }
                        closeTimerDialog();
                        if (parsedData.timer) {
                            openTimerDialog(parsedData.timer);
                        }
                        break;

                    case CANCELLED:
                        elements.scale_rect.style.display = 'block';
                        elements.scale_rect.style.backgroundColor = ABLUE;
                        elements.timer_progress.style.setProperty('--progress-color', 'white');
                        elements.scale_icon_done.style.display = 'block';
                        elements.scale_icon_done.style.fill = 'white';
                        elements.bucket_on_scale.style.display = 'none';
                        elements.cancel_svg.style.display = 'block';
                        closeTimerDialog();
                        if (parsedData.timer) {
                            openTimerDialog(parsedData.timer);
                        }
                        break;

                    case WEIGHING:
                        // green
                        if (parsedData.type === 0) {
                            closeTimerDialog();
                            if (parsedData.timer) {
                                openTimerDialog(parsedData.timer);
                            }
                            elements.percent.classList.replace('big-font-roasted', 'big-font');
                            // main scale
                            if (parsedData.percent >= 0) {
                                // display bucket on scale and %
                                elements.scale_rect.style.display = 'block';
                                elements.bucket_on_scale.style.display = 'block';
                                elements.percent.style.display = 'block';
                                if (parsedData.weight) {
                                    elements.percent.innerHTML = parsedData.percent.toFixed(0) + '%';
                                } else {
                                    elements.percent.innerHTML = '';
                                }
                                elements.percent.style.color = PERCENTCOLOR;
                                elements.weight.style.color = PERCENTCOLOR;
                                elements.bucket_on_scale.style.border = BORDER;
                                elements.bucket_on_scale.style.top = BUCKETPOSITION;
                                elements.bucket_on_scale.style.left = BUCKETPOSITION;
                                elements.percent.style.lineHeight = '30.5cqmin';
                                elements.percent.style.fontSize = '24cqmin';
                                elements.percent.style.fontWeight = '400';
                                elements.percent.style.top = '0';
                                elements.weight.style.display = 'block';
                                elements.percent.classList.remove('fade-out');
                                elements.weight.classList.remove('zoom-weight');
                                elements.zoom.classList.remove('fade-in');

                                if (parsedData.percent < Math.min(100 - accuracy, 100 - TARGET_DEVIATION)) {
                                    // normal count until (100-accuracy)%
                                    elements.scale_rect.style.background = `linear-gradient(0deg, ${ABLUE} 0 ${parsedData.percent}%, #b5b5b5 ${parsedData.percent}% 100%)`;
                                    if (parsedData.percent >= 5) {
                                        elements.timer_progress.style.setProperty('--progress-color', 'white');
                                    }
                                } else if (Math.abs(100 - (Math.round(parsedData.percent * 100) / 100)) < TARGET_DEVIATION) {
                                    // special display if [99.9, 100.1]% (if TARGET_DEVIATION is 0.1)
                                    // elements.scale_rect.style.backgroundColor = ABLUE;
                                    elements.timer_progress.style.setProperty('--progress-color', 'white');
                                    elements.bucket_on_scale.style.color = 'white';
                                    elements.bucket_on_scale.style.backgroundColor = ABLUE;
                                    elements.bucket_on_scale.style.border = '2vmin solid white';
                                    elements.bucket_on_scale.style.top = 'calc(12% - 2.25vmin)';
                                    elements.bucket_on_scale.style.left = 'calc(12% - 1.75vmin)';
                                    elements.percent.style.color = 'white';
                                    elements.weight.style.color = 'white';
                                    elements.percent.style.fontSize = '24cqmin';
                                    elements.percent.style.fontWeight = '400';
                                    elements.weight.style.display = 'none';
                                    elements.percent.style.top = '30%';
                                } else {
                                    // ZOOM for >(100 - accuracy)% (and != 100)

                                    // if (elements.scale_rect.style.background !== ABLUE) {
                                    //     let p = parsedData.percent;
                                    //     const inc = (100 - parsedData.percent) / 10;
                                    //     const ntrvl = setInterval(() => {
                                    //         if (p < 100) {
                                    //             elements.scale_rect.style.background = `linear-gradient(0deg, ${ABLUE} 0 ${p}%, #b5b5b5 ${p}% 100%)`;
                                    //             p += inc;
                                    //         } else {
                                    //             elements.scale_rect.style.background = ABLUE;
                                    //             clearInterval(ntrvl);
                                    //         }
                                    //     }, 25);
                                    // }
                                    elements.scale_rect.style.background = ABLUE;

                                    if (parsedData.percent >= 97.5) {
                                        elements.weight.style.color = 'white';
                                    }

                                    elements.timer_progress.style.setProperty('--progress-color', 'white');
                                    // elements.percent.style.display = 'none';
                                    // elements.weight.classList.add('zoom-weight');
                                    if (parsedData.percent < 100) {
                                        const zoomsize = 100 * (parsedData.percent - (100 - accuracy)) / accuracy;
                                        // elements.percent.innerHTML = '&nbsp;';
                                        elements.percent.classList.add('fade-out');
                                        elements.zoom.style.height = `${zoomsize.toFixed(2)}%`;
                                        elements.zoom.style.width = elements.zoom.style.height;
                                        elements.zoom.style.top = (50 - zoomsize / 2).toFixed(2) + '%';
                                        elements.zoom.style.left = elements.zoom.style.top;
                                        elements.zoom.style.display = 'block';
                                    } else if (parsedData.percent < 102.5 || !USERED) {
                                        // overflow (TODO check value according to accuracy)
                                        elements.bucket_on_scale.style.backgroundColor = ABLUE;
                                        const zoomsize = 76 + (parsedData.percent - 100 + 0.1) * 24;
                                        elements.scale_for_clipping.style.display = 'block';
                                        elements.scale_for_clipping.style.background = 'none';
                                        elements.zoom2.style.display = 'block';
                                        elements.zoom2.style.height = `${zoomsize.toFixed(2)}%`;
                                        elements.zoom2.style.width = elements.zoom2.style.height;
                                        const zoomperc = (100 - zoomsize) / 2;
                                        elements.zoom2.style.top = `${zoomperc.toFixed(2)}%`;
                                        elements.zoom2.style.left = elements.zoom2.style.top;
                                        elements.percent.style.color = 'white';
                                    } else {
                                        // overflow max
                                        elements.bucket_on_scale.style.backgroundColor = ABLUE;
                                        elements.scale_for_clipping.style.display = 'block';
                                        elements.scale_for_clipping.style.backgroundColor = ARED;
                                        elements.zoom2.style.display = 'none';
                                        elements.percent.style.color = 'white';
                                    }
                                }
                            } else {
                                elements.bucket_on_scale.style.display = 'none';
                                elements.percent.style.display = 'none';
                                elements.weight.style.display = 'none';
                            }
                        } else if (parsedData.type === 1) {
                            // roasted
                            elements.percent.innerHTML = parsedData.loss;
                            elements.percent.classList.replace('big-font', 'big-font-roasted');
                            elements.percent.style.color = 'white';
                            elements.weight.style.color = 'white';
                            if (!parsedData.weight) {
                                elements.weight.innerHTML = '&nbsp;';
                            }
                            elements.percent.style.display = 'block';
                            elements.scale_rect.style.display = 'block';
                            elements.scale_rect.style.backgroundColor = ABLUE;
                            elements.timer_progress.style.setProperty('--progress-color', 'white');
                            elements.bucket_on_scale.style.display = 'block';
                            elements.bucket_on_scale.style.backgroundColor = ABLUE;
                            elements.bucket_on_scale.style.border = '3vmin solid white';
                            elements.bucket_on_scale.style.top = 'calc(12% - 3vmin)';
                            elements.bucket_on_scale.style.left = 'calc(12% - 3vmin)';
                        }
                        break;
                    default:
                        break;
                }

                document.documentElement.style.setProperty('--last-percent-foreground-color', document.documentElement.style.getPropertyValue('--percent-foreground-color'));
                document.documentElement.style.setProperty('--percent-foreground-color', elements.percent.style.color);

                if (parsedData.total_percent > 0) {
                    if (parsedData.total_percent <= 100 || !USERED) {
                        const perc = parsedData.total_percent.toFixed(2);
                        elements.outer_frame.style.background = `linear-gradient(0deg, ${ABLUE} 0 ${perc}%, #b5b5b5 ${perc}% 100%)`;
                    } else {
                        let perc = (200 - parsedData.total_percent).toFixed(2);
                        if (parsedData.total_percent > 200) {
                            perc = '0';
                        }
                        elements.outer_frame.style.background = `linear-gradient(0deg, ${ABLUE} 0 ${perc}%, ${ARED} ${perc}% 100%)`;
                    }
                }

                if (parsedData.message) {
                    openMessageDialog(parsedData.message);
                } else if (showingMessageDialog) {
                    closeMessageDialog();
                }
            }
        };

        function processClick() {
            if (parsedData.state === WEIGHING) {
                openCancelDialog();
            } else if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send('clicked');
            }
        }

        function processDefinitiveClick(returnValue) {
            console.log(`Dialog, click = ${returnValue}`);
            if (returnValue === 'cancel' && ws.readyState === WebSocket.OPEN) {
                ws.send('cancelled');
            }
        }

        function openCancelDialog() {
            document.body.removeEventListener("click", processClick);
            showingCancelDialog = dialogs.cancel_dialog;
            dialogs.cancel_dialog.showModal();
        }

        function closeTimerDialog() {
            clearInterval(interval);
            elements.timer_progress.style.display = 'none';
        }

        function openTimerDialog(seconds) {
            timerVal = 0;
            elements.timer_progress['value'] = timerVal;
            elements.timer_progress['max'] = seconds;
            interval = setInterval(() => {
                timerVal += 0.25;
                elements.timer_progress['value'] = timerVal;
                if (timerVal >= seconds) {
                    closeTimerDialog();
                }
            }, 250);
            elements.timer_progress.style.display = 'block';
        }

        function openMessageDialog(text) {
            document.body.removeEventListener("click", processClick);
            if (showingMessageDialog) {
                showingMessageDialog.close();
            }
            showingMessageDialog = dialogs.text_dialog;
            elements.dialog_text.textContent = text;
            dialogs.text_dialog.showModal();
        }

        function closeMessageDialog() {
            if (showingMessageDialog) {
                showingMessageDialog.close();
            }
            elements.dialog_text.style.display = 'block';
            elements.dialog_svg.style.display = 'none';
        }

        function closeCancelDialog(text) {
            if (showingCancelDialog) {
                showingCancelDialog.close(text);
                processDefinitiveClick(text);
            }
        }

        function openErrorDialog(text) {
            if (text === 'No connection') {
                elements.dialog_text.style.display = 'none';
                elements.dialog_svg.style.display = 'block';
            } else {
                elements.dialog_text.style.display = 'block';
                elements.dialog_svg.style.display = 'none';
            }
            openMessageDialog(text);
        }

        function closeErrorDialog() {
            closeMessageDialog();
        }

        function setupClickDialog() {
            // cancel dialog
            elements.dialog_cancel_svg.addEventListener("click", () => closeCancelDialog('cancel'));
            elements.dialog_close_icon.addEventListener("click", () => closeCancelDialog('dialogCancelled'));

            dialogs.cancel_dialog.addEventListener("close", () => {
                showingCancelDialog = undefined;
                if (allowClick && !showingMessageDialog) {
                    // timeout, otherwise, proessClick will be called with the current click
                    setTimeout(() => {
                        document.body.addEventListener("click", processClick);
                        if (websocket === null) {
                            wsConnect();
                        }
                    }, 100);
                }
            });

            if (allowClick) {
                // catch click on whole screen
                document.body.addEventListener("click", processClick);
            }

            // error / message dialog
            dialogs.text_dialog.addEventListener("click", () => closeMessageDialog());
        }

        // adapted from https://stackoverflow.com/a/60971231
        function setColorScheme(scheme) {
            switch (scheme) {
                case 'dark':
                    DARKMODE = true;
                    BACKGROUND = '#515151';
                    PERCENTCOLOR = 'white';
                    BUCKETCOLOR = '#bfbfbf';
                    TITLECOLOR = '#f2f2f2';
                    BORDER = '1vmin solid #737373';
                    BUCKETPOSITION = 'calc(12% - 0.75vmin)';
                    break;
                case 'light':
                default:
                    DARKMODE = false;
                    BACKGROUND = 'white';
                    PERCENTCOLOR = 'black';
                    BUCKETCOLOR = 'rgb(50, 50, 50)';
                    TITLECOLOR = '#515151';
                    BORDER = '0.5vmin solid #515151';
                    BUCKETPOSITION = 'calc(12% - 0.25vmin)';
                    break;
            }
            setInitialStyles();
            if (lastdata) {
                usedata(lastdata);
            }
        }

        function getPreferredColorScheme() {
            if (window.matchMedia) {
                if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                    return 'dark';
                } else {
                    return 'light';
                }
            }
            return 'light';
        }

        function updateColorScheme() {
            getAllElements();
            setInitialStyles();

            setColorScheme(getPreferredColorScheme());
        }

        if (window.matchMedia) {
            const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
            colorSchemeQuery.addEventListener('change', updateColorScheme);
        }

        function enterFullScreen() {
            if (!document.fullscreenElement) {
                document.getElementById('outer_frame')?.requestFullscreen({ navigationUI: 'hide' });
            }
        }

        // https://stackoverflow.com/a/67909182
        function isTouchEventsEnabled() {
            // Bug in FireFox+Windows 10, navigator.maxTouchPoints is incorrect when script is running inside frame.
            const navigator = (window.top || window).navigator;
            const maxTouchPoints = Number.isFinite(navigator.maxTouchPoints) ? navigator.maxTouchPoints : navigator['msMaxTouchPoints'];
            if (Number.isFinite(maxTouchPoints)) {
                // Windows 10 system reports that it supports touch, even though it actually doesn't (ignore msMaxTouchPoints === 256).
                return maxTouchPoints > 0 && maxTouchPoints !== 256;
            }
            return 'ontouchstart' in window;
        }

        window.addEventListener('DOMContentLoaded', async () => {
            updateColorScheme();
            resetStyles();

            setupClickDialog();

            fitty(elements.id, { minSize: 14, multiLine: false }, elements.batchsize);

            // initial state before anything is received
            usedata({ data: '{"type":0,"state":0,"id":"","title":"","subtitle":"","batchsize":"","weight":"","final_weight":"","percent":0,"bucket":0,"blend_percent":"","total_percent":0}' });

            if (CLICK_FOR_FULLSCREEN_DISPLAY_TIME_MS && !document.fullscreenElement && (navigator['userAgentData']?.mobile || isTouchEventsEnabled())) {
                elements.dialog_fullscreen_svg.addEventListener("click", enterFullScreen);
                dialogs.fullscreen_dialog.showModal();
                setTimeout(() => {
                    dialogs.fullscreen_dialog.close();
                }, CLICK_FOR_FULLSCREEN_DISPLAY_TIME_MS);
            }

            if (NOWEBSOCKET) {
                const type = 0;
                const state = 2;
                const loss = '11.4%';
                let perc = 85;
                const final_weight = 0.8;
                let remainingWeightStr = (1 - perc / 100) * final_weight > 0.5 ? (-(1 - perc / 100) * final_weight).toFixed(1) + 'kg' : (-(1 - perc / 100) * final_weight * 1000).toFixed(0) + 'g';
                // remainingWeightStr = '';
                const finalWeightStr = final_weight.toFixed(1) + 'kg';
                const json = { accuracy, type, state, percent: perc, weight: remainingWeightStr, final_weight: finalWeightStr, bucket: 2, id: '2/3', blend_percent: '33%', title: 'Mount "Huehuetenango"', batchsize: '12kg', subtitle: 'Kenia "Mount Huehuetenango" Selection', loss, /* timer: 5 */ };
                usedata({ data: JSON.stringify(json) });
            }
        });

        function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        let wsConnectInterval;

        function wsConnect() {
            if (websocket) {
                sleep(500);
                websocket.close(3333);
                sleep(500);
            }

            if (RUNON5555) {
                websocket = new WebSocket("ws://localhost:5555/websocket");
            } else {
                websocket = new WebSocket("ws://" + location.host.split(":")[0] + ":{{port}}/websocket");
            }

            websocket.onopen = () => {
                if (websocket) {
                    if (typeof wsConnectInterval !== 'undefined') {
                        clearInterval(wsConnectInterval);
                    }
                    ws = websocket;
                    websocket.send('');
                }
            };

            websocket.onmessage = usedata;

            websocket.onclose = function (evt) {
                if (evt.code === 3333) {
                    console.log('ws closed before reopen, ok');
                    websocket = null;
                } else {
                    websocket = null;
                    console.log('ws connection error');
                    openErrorDialog('No connection');
                    if (typeof wsConnectInterval !== 'undefined') {
                        clearInterval(wsConnectInterval);
                    }
                    wsConnectInterval = setInterval(() => {
                        wsConnect();
                    }, WEBSOCKET_RECONNECT_INTERVAL);
                }
            };

            websocket.onerror = function (evt) {
                if (websocket && websocket.readyState == 1) {
                    console.log('ws error: ', evt);
                    openErrorDialog('No connection');
                    if (typeof wsConnectInterval !== 'undefined') {
                        clearInterval(wsConnectInterval);
                    }
                    wsConnectInterval = setInterval(() => {
                        wsConnect();
                    }, WEBSOCKET_RECONNECT_INTERVAL);
                }
            };
        }

        if (!NOWEBSOCKET) {
            wsConnect();
        }
    </script>

    <style type='text/css'>
        html {
            width: 100%;
            height: 100%;
            position: relative;
            font-family: 'Roboto', sans-serif;
        }

        .noscriptmsg {
            font-size: 15px;
            color: #c70c49;
            text-align: center;
            margin-top: 20px;
        }

        .outer-frame {
            padding: 15px;
            background: #b5b5b5;
            height: calc(100% - 30px);
        }

        .outerdiv {
            height: 100%;
            display: flex;
            align-items: center;
            border-radius: 20px;
        }

        .maindiv {
            width: 100%;
            display: flex;
            flex-direction: column;
            flex-wrap: nowrap;
            justify-content: space-between;
            height: 100%;
            /* restrict aspect ratio to avoid too much whitespace */
            max-height: calc(1.75 * 100vw);
        }

        .titlerow,
        .subtitlerow {
            display: flex;
            position: relative;
            justify-content: space-between;
            align-items: center;
            white-space: nowrap;
            font-weight: 600;
            margin: 0 10px;
            line-height: max(50px, 20px + 3vh, min(6.5vh, 6.5vw));
            min-height: max(50px, 20px + 3vmax, min(6.5vh, 6.5vw));
        }

        .titlerow {
            margin-bottom: 8px;
            margin-top: 5px;
        }

        .subtitlerow {
            margin-top: 8px;
            margin-bottom: 5px;
        }

        .title,
        .subtitle {
            width: 100%;
            text-align: center;
            font-size: max(32px, min(6vh, 6vw));
            min-height: max(32px, min(6.5vh, 6.5vw));
            text-overflow: ellipsis;
            overflow: hidden;
            font-weight: 600;
            color: #515151;
        }

        .subtitle {
            font-weight: 300;
        }

        .title-separate {
            display: none;
            margin-top: 30px;
        }

        .id,
        .batchsize,
        .blend-percent,
        .weight {
            color: #bfbfbf;
            font-size: calc(20px + 3vmin);
            font-weight: 600;
        }

        .batchsize,
        .blend-percent,
        .weight {
            /* 6 characters with each width ~height/2 (= font-size/2) */
            min-width: calc(3 * (20px + 3vmax));
        }

        .idcontainer {
            min-width: calc(3 * (20px + 3vmax));
            max-width: calc(3 * (20px + 3vmax));
            width: calc(3 * (20px + 3vmax));
            white-space: nowrap;
            display: inline-block;
        }

        .id,
        .blend-percent {
            text-align: left;
        }

        .id {
            overflow: hidden;
            text-overflow: ellipsis;
            vertical-align: middle;
            display: inline-block;
        }

        .batchsize,
        .weight {
            text-align: right;
        }

        .scale-div {
            text-align: center;
        }

        .buckets-grid-part {
            position: absolute;
            display: inline-flex;
            justify-content: center;
            align-content: space-evenly;
            flex-wrap: wrap;
            fill: none;

            /* fallbacks for browser that don't understand container size queries */
            bottom: 45px;
            right: -25%;
            width: 15%;

            bottom: 5cqmin;
            right: -26cqmin;
            width: 19cqmin;
        }

        .bucket-img {
            display: none;
            width: 100%;
            height: 100%;
            line-height: 100%;
            margin-top: 20px;
        }

        .scale-rect {
            container-type: inline-size;
            container-name: scale;
            position: relative;
            min-height: 130px;
            min-width: 130px;
            border: 0.5vmin solid #515151;
            border-radius: 8%;
            margin-left: auto;
            margin-right: auto;
            aspect-ratio: 1 / 1;
        }

        .scale-icon {
            position: relative;
            min-height: 130px;
            min-width: 130px;
            margin-left: auto;
            margin-right: auto;
            aspect-ratio: 1 / 1;
        }

        .scale-icon-image {
            width: 100%;
            height: 100%;
        }

        .big-font {
            /* fallback if container query not supported */
            font-size: calc(max(min(9vw, 9vh), 23px));
            text-align: center;
            font-weight: 300;
        }

        .big-font-weight {
            /* fallback if container query not supported */
            font-size: calc(max(min(11vw, 11vh), 11px));
            text-align: center;
            font-weight: 300;
        }

        @container scale (min-width: 0px) {
            .big-font {
                font-size: 32cqmin;
            }

            .big-font-weight {
                font-size: 12cqmin;
            }

            .big-font-roasted {
                font-size: 19cqmin;
                font-weight: 400;
            }
        }

        .bucket-on-scale {
            position: absolute;
            width: 76%;
            height: 76%;
            border: 0.5vmin solid #515151;
            border-radius: 100%;
            /* align-content: center; */
            display: block;
            /* align-items: center; */
        }

        .percent {
            /* margin-top: auto; */
            /* margin-bottom: auto; */
            /* top: -10%; */
            position: relative;
            background: none;
            z-index: 4;
        }

        .percent.big-font-weight {
            margin-top: 13%;
        }

        .zoom-weight {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }


        @media (min-aspect-ratio: 55 / 46) {

            .scale-rect,
            .scale-icon {
                max-width: inherit;
                max-height: calc(100vh - 2*(31px + max(60px, min(7vh, 7vw))) - 10px);
            }
        }

        @media (max-aspect-ratio: 55 / 46) {

            .scale-rect,
            .scale-icon {
                max-width: calc(100vw - 50%);
                max-height: inherit;
            }

            .title,
            .subtitle {
                white-space: nowrap;
            }
        }

        @media (max-aspect-ratio: 1 / 1) {
            .title-separate {
                display: block;
                margin: 10px 7px;
            }

            .title-top {
                display: none;
            }

            .id,
            .batchsize,
            .blend-percent,
            .weight {
                min-width: initial;
            }
        }

        @media (max-aspect-ratio: 9/10) {
            .title.title-separate {
                margin-top: 15px;
            }

            .subtitle.title-separate {
                margin-bottom: 30px;
            }
        }

        @media (max-aspect-ratio: 90/115) {
            .title.title-separate {
                margin-top: 30px;
            }

            .subtitle.title-separate {
                margin-bottom: 50px;
            }
        }

        @media (max-aspect-ratio: 9/13) {
            .title.title-separate {
                margin-top: 60px;
            }
        }

        @media (max-aspect-ratio: 9/14) {
            .title.title-separate {
                margin-top: 90px;
            }
        }

        /* dialog background */
        dialog::backdrop {
            opacity: 0.5;
            background-color: black;
        }

        .dialog-svg-container {
            height: 150px;
            width: 150px;
            margin: 0 auto;
            padding: 30px;
            padding-bottom: 25px;
        }

        .dialog-close-icon {
            margin-left: auto;
            width: fit-content;
            font-size: 50px;
            line-height: 24px;
            cursor: pointer;
        }

        .scale-for-clipping {
            overflow: hidden;
            width: 100%;
            height: 100%;
            margin-left: 0;
            margin-top: 0;
            border: none;
            border-radius: 7%;
        }

        .zoom {
            width: 30px;
            height: 30px;
            background-color: #2098c7;
            margin: auto;
            border-radius: 100%;
        }

        .zoom2 {
            height: 76%;
            width: 76%;
            position: absolute;
            top: calc(12% - 0.25vmin);
            left: calc(12% - 0.25vmin);
            border-radius: 100%;
            background-color: #6fccff;
        }

        progress {
            accent-color: var(--progress-color, #2098c7);
            -webkit-appearance: none;
            appearance: none;
            border: none;
            background: none;
            margin-left: auto;
            margin-right: auto;
            width: 90%;
            height: 5%;
            position: absolute;
            left: 5%;
            bottom: 3%;
        }

        progress::-webkit-progress-value {
            background-color: var(--progress-color, #2098c7);
        }

        progress::-webkit-progress-bar {
            background: none;
        }

        progress::-moz-progress-bar {
            background-color: var(--progress-color, #2098c7);
        }

        progress {
            color: var(--progress-color, #2098c7);
        }

        @keyframes fade-out {
            0% {
                opacity: 1;
                color: var(--last-percent-foreground-color, white);
            }

            30% {
                color: var(--last-percent-foreground-color, white);
            }

            70% {
                color: #2098c7;
            }

            100% {
                color: #2098c7;
                font-size: 0;
            }
        }

        #percent.fade-out {
            animation: fade-out 0.7s ease-out forwards;
        }

        /* @keyframes fade-in {
            0% {
                opacity: 0;
            }

            100% {
                opacity: 1;
            }
        }

        #zoom.fade-in {
            animation: fade-in 0.7s ease-out forwards;
        } */
    </style>
</head>

<body style="height: 100%; margin: 0;">
    <dialog closedby="any" id="fullscreen_dialog" style="border-radius: 10px;" class="nojsnoshow">
        <div class="dialog-svg-container">
            <svg id="dialog_fullscreen_svg" height="100%" viewBox="0 0 24 24" width="100%" version="1.1"
                xmlns="http://www.w3.org/2000/svg" style="fill: #2098c7; cursor: pointer">
                <path d="M 0,24 V 13.71429 h 3.4285715 v 6.85714 H 10.285714 V 24 Z M 20.571427,10.28571 V 3.42857 H 13.714286 V 0 H 24 v 10.28571 z" />
            </svg>
        </div>
    </dialog>
    <dialog closedby="any" id="cancel_dialog" style="border-radius: 10px;" class="nojsnoshow">
        <div class="dialog-close-icon" id="dialog_close_icon">&cross;</div>
        <div class="dialog-svg-container">
            <svg id="dialog_cancel_svg" xmlns="http://www.w3.org/2000/svg" height="100%" viewBox="0 0 24 24" width="100%" version="1.1" style="fill: #ff5151; cursor: pointer">
                <path d="M 7.68,18 12,13.68 16.32,18 18,16.32 13.68,12 18,7.68 16.32,6 12,10.32 7.68,6 6,7.68 10.32,12 6,16.32 Z M 12,24 Q 9.51,24 7.32,23.055 5.13,22.11 3.51,20.49 1.89,18.87 0.945,16.68 0,14.49 0,12 0,9.51 0.945,7.32 1.89,5.13 3.51,3.51 5.13,1.89 7.32,0.945 9.51,0 12,0 14.49,0 16.68,0.945 18.87,1.89 20.49,3.51 22.11,5.13 23.055,7.32 24,9.51 24,12 q 0,2.49 -0.945,4.68 -0.945,2.19 -2.565,3.81 -1.62,1.62 -3.81,2.565 Q 14.49,24 12,24 Z m 0,-2.4 q 4.02,0 6.81,-2.79 Q 21.6,16.02 21.6,12 21.6,7.98 18.81,5.19 16.02,2.4 12,2.4 7.98,2.4 5.19,5.19 2.4,7.98 2.4,12 2.4,16.02 5.19,18.81 7.98,21.6 12,21.6 Z M 12,12 Z" />
            </svg>
        </div>
    </dialog>
    <dialog closedby="any" id="text_dialog" style="border-radius: 10px;" class="nojsnoshow">
        <div class="dialog-text-container" style="cursor: pointer;">
            <div id="dialog_svg" style="fill: #c70c49;">
                <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px">
                    <path d="M792-56 686-160H260q-92 0-156-64T40-380q0-77 47.5-137T210-594q3-8 6-15.5t6-16.5L56-792l56-56 736 736-56 56ZM260-240h346L284-562q-2 11-3 21t-1 21h-20q-58 0-99 41t-41 99q0 58 41 99t99 41Zm185-161Zm419 191-58-56q17-14 25.5-32.5T840-340q0-42-29-71t-71-29h-60v-80q0-83-58.5-141.5T480-720q-27 0-52 6.5T380-693l-58-58q35-24 74.5-36.5T480-800q117 0 198.5 81.5T760-520q69 8 114.5 59.5T920-340q0 39-15 72.5T864-210ZM593-479Z" />
                </svg>
            </div>
            <div id="dialog_text">Error</div>
        </div>
    </dialog>
    <div class="outer-frame nojsnoshow" id="outer_frame">
        <div class="outerdiv" id="outerdiv">
            <div class="maindiv">
                <div>
                    <div class="titlerow" id="titlerow">
                        <span class="idcontainer" id="idcontainer">
                            <span class="id" id="id"></span>
                        </span>
                        <span class="title title-top" id="title1" name="title"></span>
                        <span class="batchsize" id="batchsize"></span>
                    </div>
                    <div class="title title-separate" id="title2" name="title"></div>
                </div>
                <div class="scale-and-buckets" id="scale_and_buckets">
                    <div class="scale-div">
                        <!-- // TODO remove test slider BEGIN -->
                        <!-- if NOWEBSOCKET -->
                        <span id="testfinalweightspan" style="position: absolute; left: 20px; top: calc(50% - 80px); height: 30px;">FinalWeight: <input type="number" id="testfinalweight" step="1" min="0" max="150" value="0.8"></span>
                        <span id="testaccuracyspan" style="position: absolute; left: 20px; top: calc(50% - 40px); height: 30px;">Accuracy: <input type="number" id="testaccuracy" step="1" min="0" max="10" value="10"></span>
                        <span id="testpercentspan" style="position: absolute; left: 20px; top: 50%; height: 30px;">Percent: <input type="number" id="testpercent" min="0" step="0.5" value="85" style="width: 80px;"></span>
                        <!-- // END -->
                        <div class="scale-rect" id="scale_rect">
                            <div class="scale-for-clipping scale-rect" id="scale_for_clipping">
                                <span class="zoom2" id="zoom2"></span>
                            </div>
                            <span class="bucket-on-scale" id="bucket_on_scale">
                                <span class="percent big-font-weight" id="weight"></span>
                                <span class="percent big-font" id="percent"></span>
                                <span class="zoom" id="zoom"></span>
                            </span>
                            <div class="scale-icon" id="scale_icon_done">
                                <div style="padding: 10%;">
                                    <svg id="done_svg" xmlns="http://www.w3.org/2000/svg" height="100%" viewBox="0 0 24 24" width="100%" version="1.1">
                                        <path d="M 12,24 C 10.34001,24 8.7801,23.685 7.32,23.055 5.8599,22.425 4.59,21.57 3.51,20.49 2.43,19.41 1.575,18.14001 0.945,16.68 0.315,15.21999 0,13.6599 0,12 0,10.3401 0.315,8.7801 0.945,7.32 1.575,5.8599 2.43,4.59 3.51,3.51 4.59,2.43 5.85999,1.575 7.32,0.945 8.78001,0.315 10.3401,0 12,0 c 1.6599,0 3.2199,0.315 4.68,0.945 1.4601,0.63 2.73,1.485 3.81,2.565 1.08,1.08 1.935,2.34999 2.565,3.81 C 23.685,8.78001 24,10.3401 24,12 c 0,1.6599 -0.315,3.2199 -0.945,4.68 -0.63,1.4601 -1.485,2.73 -2.565,3.81 -1.08,1.08 -2.34999,1.935 -3.81,2.565 C 15.21999,23.685 13.6599,24 12,24 Z m 0,-2.4 c 2.67999,0 4.95,-0.93 6.81,-2.79 C 20.67,16.95 21.6,14.6799 21.6,12 21.6,9.3201 20.67,7.05 18.81,5.19 16.95,3.33 14.6799,2.4 12,2.4 9.3201,2.4 7.05,3.33 5.19,5.19 3.33,7.05 2.4,9.3201 2.4,12 c 0,2.6799 0.93,4.95 2.79,6.81 1.86,1.86 4.1301,2.79 6.81,2.79 z" />
                                        <path d="M 9.8520512,17.954633 4.2484998,12.092527 5.922783,10.400489 9.9151482,14.402878 18.089213,6.0453675 19.7515,7.7014195 Z" />
                                    </svg>
                                    <svg id="cancel_svg" xmlns="http://www.w3.org/2000/svg" height="100%" viewBox="0 0 24 24" width="100%" version="1.1">
                                        <path d="M 7.68,18 12,13.68 16.32,18 18,16.32 13.68,12 18,7.68 16.32,6 12,10.32 7.68,6 6,7.68 10.32,12 6,16.32 Z M 12,24 Q 9.51,24 7.32,23.055 5.13,22.11 3.51,20.49 1.89,18.87 0.945,16.68 0,14.49 0,12 0,9.51 0.945,7.32 1.89,5.13 3.51,3.51 5.13,1.89 7.32,0.945 9.51,0 12,0 14.49,0 16.68,0.945 18.87,1.89 20.49,3.51 22.11,5.13 23.055,7.32 24,9.51 24,12 q 0,2.49 -0.945,4.68 -0.945,2.19 -2.565,3.81 -1.62,1.62 -3.81,2.565 Q 14.49,24 12,24 Z m 0,-2.4 q 4.02,0 6.81,-2.79 Q 21.6,16.02 21.6,12 21.6,7.98 18.81,5.19 16.02,2.4 12,2.4 7.98,2.4 5.19,5.19 2.4,7.98 2.4,12 2.4,16.02 5.19,18.81 7.98,21.6 12,21.6 Z M 12,12 Z" />
                                    </svg>
                                </div>
                            </div>
                            <div class="buckets-grid-part" id="buckets_grid_part">
                                <div name="buckets_images" style="margin-top: 15cqmin;">
                                    <svg width="100%" height="100%" version="1.0" viewBox="0 0 24 24"
                                        xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg">
                                        <path d="M 10.360146,0.48878671 C 5.8839144,0.59904451 2.2122471,1.1209314 0.94655416,1.8229061 0.74782493,1.9350015 0.57417803,2.0875248 0.51822514,2.2051331 l -0.0463058,0.091881 v 1.0989028 c 0,1.20181 -0.003859,1.1540316 0.1157646,1.2992044 0.18329395,0.2205156 0.75439926,0.4906472 1.43933986,0.6799231 l 0.2141645,0.058804 0.042447,0.233379 c 0.4418349,2.4844758 0.7235287,4.7447606 0.9473403,7.6004376 0.1871528,2.396269 0.3087056,5.365879 0.3087056,7.572873 0,0.600905 0.00772,0.832446 0.025082,0.909627 0.310635,1.255101 5.9522299,2.089385 11.2716138,1.668568 3.00795,-0.237054 5.178536,-0.839797 5.556701,-1.541772 l 0.05595,-0.101069 0.01351,-0.588042 c 0.0077,-0.323423 0.02508,-1.021722 0.03666,-1.552797 0.138918,-6.301234 0.468847,-11.2224063 0.904893,-13.479016 0.08296,-0.4244925 0.121553,-0.5862039 0.144706,-0.6082555 0.01158,-0.011026 0.135059,-0.055129 0.272047,-0.099232 1.030305,-0.3252605 1.514587,-0.5751782 1.66894,-0.8618485 0.03666,-0.071668 0.03859,-0.1029073 0.03859,-1.1962971 0,-1.102578 0,-1.1246296 -0.04052,-1.1981348 C 23.06531,1.4020888 19.611667,0.7331915 14.932847,0.53288983 13.466496,0.47041041 11.747391,0.45387174 10.360146,0.48878671 Z"
                                            style="stroke-width:0.818999" />
                                        <path d="m 0.51822514,2.5155887 c 0,0 7.51866326,1.0044227 11.40038886,1.0063705 3.881725,0.00195 11.56924,-1.0192345 11.56924,-1.0192345"
                                            style="stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter" />
                                        <path d="m 2.4639743,5.5606455 c 0,0 6.576432,0.8087701 9.9337807,0.8107181 3.357349,0.002 9.09117,-0.7649286 9.09117,-0.7649286"
                                            style="stroke-width:0.93;stroke-linecap:round;stroke-linejoin:miter" />
                                    </svg>
                                </div>
                                <div name="buckets_images" style="margin-top: 15cqmin;">
                                    <svg width="100%" height="100%" version="1.0" viewBox="0 0 24 24"
                                        xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg">
                                        <path d="M 10.360146,0.48878671 C 5.8839144,0.59904451 2.2122471,1.1209314 0.94655416,1.8229061 0.74782493,1.9350015 0.57417803,2.0875248 0.51822514,2.2051331 l -0.0463058,0.091881 v 1.0989028 c 0,1.20181 -0.003859,1.1540316 0.1157646,1.2992044 0.18329395,0.2205156 0.75439926,0.4906472 1.43933986,0.6799231 l 0.2141645,0.058804 0.042447,0.233379 c 0.4418349,2.4844758 0.7235287,4.7447606 0.9473403,7.6004376 0.1871528,2.396269 0.3087056,5.365879 0.3087056,7.572873 0,0.600905 0.00772,0.832446 0.025082,0.909627 0.310635,1.255101 5.9522299,2.089385 11.2716138,1.668568 3.00795,-0.237054 5.178536,-0.839797 5.556701,-1.541772 l 0.05595,-0.101069 0.01351,-0.588042 c 0.0077,-0.323423 0.02508,-1.021722 0.03666,-1.552797 0.138918,-6.301234 0.468847,-11.2224063 0.904893,-13.479016 0.08296,-0.4244925 0.121553,-0.5862039 0.144706,-0.6082555 0.01158,-0.011026 0.135059,-0.055129 0.272047,-0.099232 1.030305,-0.3252605 1.514587,-0.5751782 1.66894,-0.8618485 0.03666,-0.071668 0.03859,-0.1029073 0.03859,-1.1962971 0,-1.102578 0,-1.1246296 -0.04052,-1.1981348 C 23.06531,1.4020888 19.611667,0.7331915 14.932847,0.53288983 13.466496,0.47041041 11.747391,0.45387174 10.360146,0.48878671 Z"
                                            style="stroke-width:0.818999" />
                                        <path d="m 0.51822514,2.5155887 c 0,0 7.51866326,1.0044227 11.40038886,1.0063705 3.881725,0.00195 11.56924,-1.0192345 11.56924,-1.0192345"
                                            style="stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter" />
                                        <path d="m 2.4639743,5.5606455 c 0,0 6.576432,0.8087701 9.9337807,0.8107181 3.357349,0.002 9.09117,-0.7649286 9.09117,-0.7649286"
                                            style="stroke-width:0.93;stroke-linecap:round;stroke-linejoin:miter" />
                                    </svg>
                                </div>
                            </div>
                            <progress id="timer_progress" value="0" max="100"></progress>
                        </div>
                        <div class="scale-icon" id="scale_icon_initial">
                            <div style="padding: 10%;">
				<svg id="coffee_svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="m18.058 1.354-.216 2.283c-.35 3.708-2.763 6.988-5.84 9.224l-.018.013-.015.013c-2.759 2.164-5.348 5.404-5.254 9.376l.015.656.578.31c2.077 1.113 4.497.917 6.478.075l.005-.003.005-.002c4.44-1.935 7.322-6.277 8.284-10.797l.003-.005v-.005c.648-3.17.337-7.054-2.351-9.572Zm1.328 5.522c.602 1.61.85 3.4.492 5.157-.83 3.903-3.362 7.623-6.982 9.2a5.55 5.55 0 0 1-3.812.17c.28-2.618 2.072-5.015 4.275-6.743l-.031.023c2.66-1.934 4.936-4.619 6.058-7.807zM12.966.018c-.925.068-1.829.3-2.66.638l-.008.003-.008.002c-4.4 1.869-7.28 6.12-8.31 10.554l-.003.003v.005c-.717 3.203-.48 7.146 2.187 9.755l1.713 1.677.198-2.387c.243-2.957 2.202-5.631 4.608-7.582l-.044.037c2.698-1.968 5.161-4.64 6.137-8.092l.024-.088.01-.089c.02-.178.283-.886.393-1.676.055-.395.09-.875-.161-1.404C16.798.86 16.212.472 15.64.35a7 7 0 0 0-2.674-.33Zm.151 2.252a4.8 4.8 0 0 1 1.849.216c-.055.36-.307.957-.393 1.71l.034-.176c-.786 2.78-2.858 5.106-5.296 6.883l-.023.016-.024.018c-1.947 1.579-3.699 3.65-4.67 6.09-.595-1.664-.822-3.51-.42-5.309v-.002c.892-3.83 3.418-7.456 6.993-8.977l.006-.003a6.5 6.5 0 0 1 1.944-.465z" style="stroke-width:1.33298"/></svg>
				<svg id="coffee_svg_dark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M13.03.033c-.924.068-1.827.3-2.657.638l-.008.002-.008.003C5.964 2.544 3.09 6.793 2.061 11.226l-.003.002v.006c-.716 3.201-.48 7.142 2.183 9.751l1.211 1.3.135-2.76c.243-2.956 2.092-5.468 4.495-7.418 2.693-1.966 5.24-4.186 6.215-7.636.464-1.565.55-1.668.217-.953 0 0 .259-.353.184-.976.054-.395-.012-.673-.224-1.278-.186-.361-.404-.732-.774-.9-.767-.402-1.786-.396-2.67-.33Z" style="stroke-width:1.35914"/><path d="m17.968 1.714-.216 2.247c-.351 3.65-2.769 6.877-5.852 9.078l-.018.013-.016.012c-2.763 2.13-5.358 5.318-5.264 9.226l.016.646.579.305c2.08 1.095 4.505.902 6.49.074l.006-.003.005-.002c4.448-1.904 7.337-6.177 8.3-10.625l.003-.005v-.005c.65-3.12.338-6.942-2.356-9.42Z" style="stroke-width:1.36845"/></svg>
                                <svg id="roast_svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="m6.064 0 3.092 3.175c-1.276.337-2.435.892-3.404 1.635-1.649 1.264-2.766 3.122-2.765 5.212v.03q.002.087.007.176c0 .016-.005.01-.005.027v8.916h18.022v-8.916c0-.26 0-.046-.005-.052q.005-.066.007-.131l.003-.025v-.025c0-2.088-1.119-3.947-2.769-5.212-.954-.732-2.097-1.28-3.35-1.617L18 .003zm5.937 5.38c1.866 0 3.533.591 4.68 1.471 1.144.878 1.754 1.98 1.757 3.158l-.007.103-.008.088.005.088c.007.137.006.146.008.199v6.109h-3.233c.093-.06.196-.108.284-.173.924-.685 1.564-1.704 1.566-2.859v-.005a3 3 0 0 0-.01-.259l-.055-.712h-9.94l-.081.684q-.015.131-.02.262v.025c0 1.157.64 2.178 1.566 2.864.088.065.191.113.284.173H5.564v-6.298c.001-.014.005-.007.005-.023l.003-.07-.005-.068q-.004-.059-.005-.118c0-1.18.61-2.285 1.757-3.165s2.814-1.47 4.682-1.471Zm-3.176 8.752h6.35c-.144.364-.205.75-.608 1.048-.624.462-1.54.777-2.567.777s-1.943-.315-2.567-.777c-.402-.297-.463-.683-.608-1.048zM.447 19.125v2.524c0 .858.554 1.499 1.112 1.846.558.346 1.2.505 1.888.505h17.106c.689 0 1.33-.159 1.888-.505.558-.347 1.112-.988 1.112-1.846v-2.524h-2.575v2.205c-.095.04-.223.096-.425.096H3.447c-.202 0-.33-.056-.425-.096v-2.205ZM8.722 8.194c-.921 0-1.708.72-1.708 1.636s.787 1.64 1.708 1.64 1.71-.724 1.71-1.64-.79-1.636-1.71-1.636m0 1.028c.397 0 .678.284.678.608 0 .325-.281.609-.678.609-.398 0-.677-.284-.677-.609 0-.324.28-.608.677-.608"/></svg>
				<svg id="roast_svg_dark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="m6.064 0 3.093 3.175c-1.277.337-2.436.892-3.405 1.635C4.103 6.074 2.986 7.93 2.987 10.02v.03q.002.09.007.177c0 .016-.005.01-.005.027v8.916h18.022v-8.916c0-.26 0-.046-.005-.053q.005-.065.007-.13l.003-.025v-.026c0-2.087-1.118-3.947-2.768-5.211-.954-.732-2.098-1.28-3.352-1.617l3.105-3.19zM12 5.38c1.867 0 3.534.727 4.681 1.808 1.145 1.078 1.755 2.43 1.758 3.877l-.008.126-.007.11.005.106c.007.168.006.18.007.244v7.504H5.563V11.42c.002-.017.005-.009.006-.027l.002-.086-.005-.083q-.003-.073-.005-.146c0-1.45.61-2.806 1.758-3.886C8.466 6.11 10.132 5.383 12 5.383Z" style="opacity:.8"/><path d="M.447 19.125v2.524c0 .858.554 1.499 1.112 1.846.558.346 1.2.505 1.888.505h17.106c.689 0 1.33-.159 1.888-.505.558-.347 1.112-.988 1.112-1.846v-2.524h-2.575c-2.542.03-15.414.03-17.956 0z"/><path d="M7.04 13.377h10.026c-.228.924-.324 1.901-.96 2.658-.985 1.17-2.43 1.97-4.053 1.97s-3.067-.8-4.052-1.97c-.636-.754-.732-1.733-.96-2.656ZM8.662 8.441c-.729 0-1.35.595-1.35 1.35 0 .757.621 1.353 1.35 1.353s1.353-.596 1.353-1.352-.624-1.35-1.353-1.35" style="opacity:.2"/><path d="M12 5.38v.003c-1.868 0-3.534.727-4.681 1.808S5.56 9.628 5.56 11.077q.002.075.005.146l.005.083-.002.086c0 .018-.004.01-.005.027v7.736h12.872v-7.504c-.001-.064 0-.076-.007-.244l-.005-.106.007-.11.008-.126c-.003-1.448-.613-2.8-1.757-3.877C15.535 6.108 13.867 5.38 12 5.38ZM8.661 8.44c.729 0 1.353.597 1.353 1.353 0 .755-.624 1.352-1.353 1.352-.728 0-1.35-.597-1.35-1.352s.622-1.353 1.35-1.353m-1.619 4.938h10.024c-.228.924-.324 1.9-.96 2.657-.985 1.171-2.431 1.969-4.053 1.969S8.985 17.206 8 16.035c-.636-.753-.73-1.734-.958-2.657"/></svg>
                            </div>
                        </div>
                    </div>
                </div>

                <div>
                    <div class="subtitle title-separate" id="subtitle2" name="subtitle"></div>
                    <div class="subtitlerow" id="subtitlerow">
                        <span class="blend-percent" id="blend_percent"></span>
                        <span class="subtitle title-top" id="subtitle1" name="subtitle"></span>
                        <span class="weight" id="final_weight"></span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>

</html>