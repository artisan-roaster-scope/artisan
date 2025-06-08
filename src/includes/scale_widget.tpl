<!doctype html>
<html id="html">

<!-- 

TODO:
- fixes

DONE:
- enable cancel click per api
- add timer
- show loss for type 1
- improve dialog
- outer bar (total_percent)
- zoom feature (>99%)
- communication back to artisan
  - dialog on click: yes / no; send "cancelled" on yes
- add some typings
- websocket communication
- general layout, strings, responsive
- integrate SVGs
- states 0, 1, 3, 4
- state 2, main percent display
- dark mode, incl. change of svg icons
- buckets
- show loss (state: done && percent != 0)

Receives data in the shape of
{ 
    id:str (blend component / roast batch nr) | max 6 characters
    title:str
    subtitle:str
    batchsize:str | max ~6 characters
    weight:str | max 6 characters
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
}
-->

<head>
    <meta charset="utf-8" />
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-status-bar-style" content="black">
    <meta name="mobile-web-app-title" content="{{window_title}}">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;600">
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
    <script type="text/javascript" src="fitty_patched.js"></script>
    <script type="text/javascript">
        // @ts-check

        // if true, will use port 5555, otherwise {{port}}
        const RUNON5555 = false;

        // how often the websocket will be tried if not open in ms
        const WEBSOCKET_RECONNECT_INTERVAL = 10000;

        // if true, scale is red if percent > 102.5 and frame is red if total_percent > 100
        const USERED = false;

        // in %; show "100%" if within 5g for 5kg, 20g for 20kg, ...
        const TARGET_DEVIATION = 0.1;


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
         * timer: number, loss: string, allow_click: 0 | 1 } } */
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

        function getAllElements() {
            elements.html = document.getElementsByTagName('html')[0];

            for (const prop of ['id', 'batchsize', 'scale_rect',
                'percent', 'zoom', 'zoom2', 'scale_for_clipping',
                'scale_icon_done', 'scale_icon_initial',
                'blend_percent', 'buckets_grid_part',
                'weight', 'scale_icon_image', 'bucket_on_scale',
                'coffee_svg', 'roast_svg', 'done_svg', 'cancel_svg',
                'dialog_cancel_svg', 'dialog_close_icon',
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
            for (const prop of ['cancel_dialog', 'text_dialog']) {
                const el = document.getElementById(prop);
                if (el) {
                    dialogs[prop] = /** @type HTMLDialogElement */(el);
                }
            }

            for (const prop of ['title', 'buckets_images', 'subtitle']) {
                multiElements[prop] = document.getElementsByName(prop);
            }
        }

        function setInitialStyles() {
            elements.html.style.backgroundColor = BACKGROUND;
            elements.bucket_on_scale.style.backgroundColor = BACKGROUND;
            elements.bucket_on_scale.style.color = PERCENTCOLOR;
            elements.percent.style.color = PERCENTCOLOR;
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
            elements.zoom2.style.display = 'none';
            elements.scale_for_clipping.style.display = 'none';
            elements.outer_frame.style.background = '#b5b5b5';
        }

        function setTexts() {
            for (const prop of ['id', 'batchsize', 'weight', 'blend_percent']) {
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
                        } else {
                            elements.bucket_on_scale.style.display = 'block';
                            elements.bucket_on_scale.style.backgroundColor = ABLUE;
                            elements.bucket_on_scale.style.border = '1.2vmin solid white';
                            elements.percent.style.color = 'white';
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
                            elements.percent.classList.remove('big-font-roasted');
                            elements.percent.classList.add('big-font');
                            // main scale
                            if (parsedData.percent >= 0) {
                                // display bucket on scale and %
                                elements.scale_rect.style.display = 'block';
                                elements.bucket_on_scale.style.display = 'block';
                                elements.percent.style.display = 'block';
                                elements.percent.innerHTML = parsedData.percent.toFixed(0) + '%';
                                elements.percent.style.color = PERCENTCOLOR;
                                elements.bucket_on_scale.style.border = BORDER;
                                elements.bucket_on_scale.style.top = BUCKETPOSITION;
                                elements.bucket_on_scale.style.left = BUCKETPOSITION;
                                elements.percent.style.fontSize = '32cqmin';

                                if (parsedData.percent <= 99) {
                                    // normal count until 99%
                                    elements.scale_rect.style.background = `linear-gradient(0deg, ${ABLUE} 0 ${parsedData.percent}%, #b5b5b5 ${parsedData.percent}% 100%)`;
                                    if (parsedData.percent >= 95) {
                                        elements.timer_progress.style.setProperty('--progress-color', 'white');
                                    }
                                } else if (Math.abs(100 - (Math.round(parsedData.percent * 100) / 100)) < TARGET_DEVIATION) {
                                    // special display if [99.99, 100.01]%
                                    elements.scale_rect.style.backgroundColor = ABLUE;
                                    elements.timer_progress.style.setProperty('--progress-color', 'white');
                                    elements.bucket_on_scale.style.color = 'white';
                                    elements.bucket_on_scale.style.backgroundColor = ABLUE;
                                    elements.bucket_on_scale.style.border = '2vmin solid white';
                                    elements.bucket_on_scale.style.top = 'calc(12% - 2vmin)';
                                    elements.bucket_on_scale.style.left = 'calc(12% - 2vmin)';
                                    elements.percent.style.color = 'white';
                                    elements.percent.style.fontSize = '28cqmin';
                                } else {
                                    // zoom for >99% (and != 100)
                                    elements.scale_rect.style.backgroundColor = ABLUE;
                                    elements.timer_progress.style.setProperty('--progress-color', 'white');
                                    elements.percent.style.display = 'none';
                                    if (parsedData.percent < 100) {
                                        const zoomsize = (100 * (parsedData.percent - 99)).toFixed(2);
                                        elements.zoom.style.display = 'block';
                                        elements.zoom.style.height = `${zoomsize}%`;
                                        elements.zoom.style.width = elements.zoom.style.height;
                                    } else if (parsedData.percent < 102.5 || !USERED) {
                                        // overflow
                                        elements.bucket_on_scale.style.backgroundColor = ABLUE;
                                        const zoomsize = 76 + (parsedData.percent - 100 + 0.1) * 24;
                                        elements.scale_for_clipping.style.display = 'block';
                                        elements.scale_for_clipping.style.background = 'none';
                                        elements.zoom2.style.display = 'block';
                                        elements.zoom2.style.height = `${zoomsize.toFixed(2)}%`;
                                        elements.zoom2.style.width = elements.zoom2.style.height;
                                        const zoomperc = (100 - zoomsize) / 2;
                                        // const topleft = `calc(${zoomperc.toFixed(2)}% - 0.25vmin)`;
                                        elements.zoom2.style.top = `${zoomperc.toFixed(2)}%`;
                                        elements.zoom2.style.left = elements.zoom2.style.top;
                                    } else {
                                        // overflow max
                                        elements.bucket_on_scale.style.backgroundColor = ABLUE;
                                        elements.scale_for_clipping.style.display = 'block';
                                        elements.scale_for_clipping.style.backgroundColor = ARED;
                                        elements.zoom2.style.display = 'none';
                                    }
                                }
                            } else {
                                elements.bucket_on_scale.style.display = 'none';
                                elements.percent.style.display = 'none';
                            }
                        } else if (parsedData.type === 1) {
                            elements.percent.innerHTML = parsedData.loss;
                            elements.percent.classList.add('big-font-roasted');
                            elements.percent.classList.remove('big-font');
                            elements.percent.style.color = 'white';
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
                    default:
                        break;
                }

                if (parsedData.total_percent > 0) {
                    if (parsedData.total_percent <= 100 || !USERED) {
                        const perc = parsedData.total_percent.toFixed(2);
                        elements.outer_frame.style.background = `linear-gradient(0deg, ${ABLUE} 0 ${perc}%, #b5b5b5 ${perc}% 100%)`;
                    } else {
                        let perc = (200 - parsedData.total_percent).toFixed(2);
                        if (parsedData.total_percent > 200) {
                            let perc = '0';
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
            } else if (ws && ws.readyState === ws.OPEN) {
                ws.send('clicked');
            }
        }

        function processDefinitiveClick(returnValue) {
            console.log(`Dialog, click = ${returnValue}`);
            if (returnValue === 'cancel' && ws.readyState === ws.OPEN) {
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
            // if (showingTimerDialog) {
            //     // showingTimerDialog.close();
            //     showingTimerDialog = undefined;
            //     if (allowClick && !showingCancelDialog && !showingMessageDialog) {
            //         // timeout, otherwise, proessClick will be called with the current click
            //         setTimeout(() => {
            //             document.body.addEventListener("click", processClick);
            //             if (websocket === null) {
            //                 wsConnect();
            //             }
            //         }, 100);
            //     }
            // }
        }

        function openTimerDialog(seconds) {
            // document.body.removeEventListener("click", processClick);
            // showingTimerDialog = dialogs.timer_dialog;
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
            // showingTimerDialog.showModal();
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

            // dialogs.timer_dialog.addEventListener("close", () => {
            //     showingMessageDialog = undefined;
            //     if (allowClick && !showingCancelDialog) {
            //         // timeout, otherwise, proessClick will be called with the current click
            //         setTimeout(() => {
            //             document.body.addEventListener("click", processClick);
            //             if (websocket === null) {
            //                 wsConnect();
            //             }
            //         }, 100);
            //     }
            // });

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
            // dialogs.text_dialog.addEventListener("close", () => closeMessageDialog());

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

        window.addEventListener('DOMContentLoaded', async () => {
            updateColorScheme();
            resetStyles();

            setupClickDialog();

            // fitty(elements.id, { minSize: 14, multiLine: false });
            fitty(elements.id, { minSize: 14, multiLine: false }, elements.batchsize);

            // initial state before anything is received
            usedata({ data: '{"type":0,"state":0,"id":"","title":"","subtitle":"","batchsize":"","weight":"","percent":0,"bucket":0,"blend_percent":"","total_percent":0}' });

            // TODO remove test data
            // usedata({ data: '{"id":"","title":"Peru 2021, Negrisa","subtitle":"Negrisa, Peru","batchsize":"500g","weight":"","percent":0,"state":0,"bucket":0,"blend_percent":"","total_percent":0,"type":0}' });
            // usedata({ data: '{ "id": "Batch 12", "title": "Custom Blend", "subtitle": "Huehuetenango, Guatemela", "batchsize": "12kg", "weight": "1.23kg", "percent": 99, "state": 2, "bucket": 1, "blend_percent": "33%", "total_percent": 77.123, "type": 0}' });
            // usedata({ data: '{"type":0,"state":2,"percent":50,"weight":"6,00kg","bucket":1,"id":"2/3","title":"Mount Kenia","batchsize":"12kg","subtitle":"Kenia Mount Kenia Selection"}' });
            // usedata({ data: '{"type":0,"state":2,"percent":99,"weight":"120g","bucket":1,"id":"2/3","title":"Mount Kenia","batchsize":"12kg","subtitle":"Kenia Mount Kenia Selection"}' });
            // usedata({ data: '{"type":1,"state":0,"title":"Mount Kenia","batchsize":"12kg"}' });
            // usedata({ data: '{"type":1,"state":1,"title":"Mount Kenia","batchsize":"12kg"}' });
            // usedata({ data: '{"type":0,"state":3,"id":"2/3","blend_percent":"33%","title":"Mount Kenia","batchsize":"12kg"}' });
            // usedata({ data: ' {"type":0,"state":2,"percent":99,"weight":"120g","bucket":3,"id":"2/3","blend_percent":"33%","title":"Mount Kenia","batchsize":"12kg","subtitle":"Kenia Mount Kenia Selection"}' });
            // await new Promise(r => setTimeout(r, 2000));
            // usedata({ data: '{"type":0,"state":3,"weight":"12,1kg","bucket":1,"id":"2/3","blend_percent":"33%","title":"Mount Kenia","batchsize":"12kg","subtitle":""}' });
            // usedata({ data: '{"type":0,"state":0,"title":"Disconnected!","batchsize":"12kg","subtitle":"Kenia Mount Kenia Selection"}' });
            // usedata({ data: '{"type":1,"state":3,"id":"P312","percent":-14,"title":"Custom Blend","batchsize":"12kg","weight":"10,3kg"}' });
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

        wsConnect();
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
            /* position: absolute; */
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
            /* margin-bottom: 20px; */
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
            right: -30%;
            width: 15%;

            bottom: 5cqmin;
            right: -32cqmin;
            width: 20cqmin;
        }

        .bucket-img {
            display: none;
            width: 100%;
            height: 100%;
            line-height: 100%;
            margin-top: 20px;
        }

        .scale-rect {
            /* transition: background 0.5s ease-in-out; */
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
            /* minus titlerow and subtitlerow and some 10px; different in portrait */
            /* max-height: calc(100vh - 2*(16px + max(60px, min(7vh, 7vw))) - 10px); */
            /* max-width: calc(100vw - 50%); */
        }

        .scale-icon {
            position: relative;
            min-height: 130px;
            min-width: 130px;
            margin-left: auto;
            margin-right: auto;
            aspect-ratio: 1 / 1;
            /* minus titlerow and subtitlerow and some 10px; different in portrait */
            /* max-height: calc(100vh - 2*(16px + max(60px, min(7vh, 7vw))) - 10px); */
            /* max-width: calc(100vw - 50%); */
        }

        .scale-icon-image {
            width: 100%;
            height: 100%;
        }

        .big-font {
            /* fallback if container query not supported */
            font-size: calc(max(min(11vw, 20vh), 23px));
            text-align: center;
            font-weight: 300;
        }

        @container scale (min-width: 0px) {
            .big-font {
                font-size: 32cqmin;
            }

            .big-font-roasted {
                font-size: 19cqmin;
            }
        }

        .bucket-on-scale {
            position: absolute;
            width: 76%;
            height: 76%;
            border: 0.5vmin solid #515151;
            border-radius: 100%;
            align-content: center;
        }

        .percent {
            margin-top: auto;
            margin-bottom: auto;
            background: none;
        }


        /* @media (orientation: landscape) { */
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

        /* @media (orientation: portrait) { */
        @media (max-aspect-ratio: 1 / 1) {
            .title-separate {
                display: block;
                margin: 10px 0;
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
            /* text-align: right; */
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
            margin-left: -0.25vmin;
            margin-top: -0.25vmin;
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
            /* border-radius: 30%; */
            background: none;
            margin-left: auto;
            margin-right: auto;
            /* margin-top: 3%; */
            width: 90%;
            height: 5%;
            position: absolute;
            left: 5%;
            top: 3%;
        }

        progress::-webkit-progress-value {
            background-color: var(--progress-color, #2098c7);
            /* border-radius: 30%; */
            /* transition: width 0.4s ease-in; */
        }

        progress::-webkit-progress-bar {
            background: none;
            /* border-radius: 30%; */
        }

        progress::-moz-progress-bar {
            background-color: var(--progress-color, #2098c7);
            /* border-radius: 30%; */
            /* transition: width 0.4s ease-in; */
        }

        progress {
            color: var(--progress-color, #2098c7);
        }
    </style>
</head>

<body style="height: 100%; margin: 0;">
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
                        <div class="scale-rect" id="scale_rect">
                            <progress id="timer_progress" value="0" max="100"></progress>
                            <div class="scale-for-clipping scale-rect" id="scale_for_clipping">
                                <span class="zoom2" id="zoom2"></span>
                            </div>
                            <span class="bucket-on-scale" id="bucket_on_scale">
                                <span class="percent big-font" id="percent"></span>
                                <span class="zoom" id="zoom"></span>
                            </span>
                            <div class="scale-icon" id="scale_icon_done">
                                <div style="padding: 10%;">
                                    <svg id="done_svg" xmlns="http://www.w3.org/2000/svg" height="100%" viewBox="0 0 24 24" width="100%" version="1.1">
                                        <path d="M 12,24 C 10.34001,24 8.7801,23.685 7.32,23.055 5.8599,22.425 4.59,21.57 3.51,20.49 2.43,19.41 1.575,18.14001 0.945,16.68 0.315,15.21999 0,13.6599 0,12 0,10.3401 0.315,8.7801 0.945,7.32 1.575,5.8599 2.43,4.59 3.51,3.51 4.59,2.43 5.85999,1.575 7.32,0.945 8.78001,0.315 10.3401,0 12,0 c 1.6599,0 3.2199,0.315 4.68,0.945 1.4601,0.63 2.73,1.485 3.81,2.565 1.08,1.08 1.935,2.34999 2.565,3.81 C 23.685,8.78001 24,10.3401 24,12 c 0,1.6599 -0.315,3.2199 -0.945,4.68 -0.63,1.4601 -1.485,2.73 -2.565,3.81 -1.08,1.08 -2.34999,1.935 -3.81,2.565 C 15.21999,23.685 13.6599,24 12,24 Z m 0,-2.4 c 2.67999,0 4.95,-0.93 6.81,-2.79 C 20.67,16.95 21.6,14.6799 21.6,12 21.6,9.3201 20.67,7.05 18.81,5.19 16.95,3.33 14.6799,2.4 12,2.4 9.3201,2.4 7.05,3.33 5.19,5.19 3.33,7.05 2.4,9.3201 2.4,12 c 0,2.6799 0.93,4.95 2.79,6.81 1.86,1.86 4.1301,2.79 6.81,2.79 z" />
                                        <path d="M 5.7433189,10.913879 9.7221742,15.090493 18.256681,6.1263883 19.584193,7.5211956 9.7221742,17.873612 4.4158072,12.308686 Z" />
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
                        </div>
                        <div class="scale-icon" id="scale_icon_initial">
                            <div style="padding: 10%;">
                                <svg id="coffee_svg" xmlns="http://www.w3.org/2000/svg" height="100%" width="100%" viewBox="0 0 24 24" version="1.1">
                                    <path d="m 18.058268,1.3537015 -0.21609,2.2832667 c -0.350574,3.7082256 -2.763274,6.9876308 -5.839799,9.2243758 l -0.01822,0.01306 -0.01562,0.01306 C 9.2104639,15.051029 6.6207441,18.291377 6.7147194,22.2626 l 0.015621,0.656081 0.5779685,0.309812 c 2.076787,1.113254 4.4964181,0.917066 6.4774981,0.0755 l 0.0052,-0.0027 0.0052,-0.0027 c 4.438967,-1.934291 7.322209,-6.276217 8.284223,-10.796629 l 0.0027,-0.0052 v -0.0052 C 22.73096,9.3217298 22.420375,5.4379502 19.731748,2.9204784 Z m 1.327771,5.5220153 c 0.601562,1.61051 0.850323,3.3997742 0.492058,5.1574452 -0.830702,3.903108 -3.362184,7.623064 -6.982566,9.200649 -1.238328,0.523622 -2.61278,0.549269 -3.8115311,0.169222 0.280726,-2.617579 2.0719881,-5.014949 4.2748761,-6.743028 l -0.03124,0.02343 c 2.660501,-1.934292 4.936436,-4.619453 6.058275,-7.8078152 z M 12.966393,0.01818579 c -0.925104,0.067731 -1.829386,0.2994813 -2.660768,0.637859 l -0.0079,0.0026 -0.0079,0.0026 C 5.8899855,2.5298191 3.0096757,6.7805688 1.9799463,11.215137 l -0.0026,0.0027 v 0.0052 c -0.7172515,3.202891 -0.4800738,7.145722 2.1868921,9.755303 l 1.7131498,1.676626 0.197868,-2.387373 c 0.2431628,-2.956689 2.2018207,-5.63092 4.6081218,-7.581341 l -0.04426,0.03644 c 2.697958,-1.967483 5.161311,-4.6391812 6.137054,-8.0912075 l 0.02343,-0.088518 0.0104,-0.088518 c 0.02,-0.178251 0.2826,-0.8864649 0.393237,-1.6766572 0.05465,-0.3950962 0.08931,-0.8748368 -0.161291,-1.4033646 C 16.798013,0.85936199 16.2115,0.47213049 15.640983,0.34869619 14.757216,0.06263809 13.85212,-0.04679981 12.967019,0.01811639 Z m 0.151,2.25207481 c 0.639112,-0.047574 1.26772,0.025272 1.848448,0.2160899 -0.05467,0.3603986 -0.307026,0.9563754 -0.393124,1.7104839 l 0.03384,-0.1770335 C 13.821408,6.8004038 11.748646,9.1257928 9.3110199,10.903459 l -0.02343,0.01562 -0.02343,0.01822 c -1.947221,1.578252 -3.699161,3.649708 -4.6706391,6.0896 -0.5950036,-1.664229 -0.8216107,-3.509611 -0.4191565,-5.308472 1.894e-4,-8.46e-4 -1.897e-4,-0.0017 0,-0.0027 0.8913924,-3.8295272 3.4173686,-7.4559072 6.9929627,-8.9768409 0.0017,-7.611e-4 0.0035,-0.00184 0.0052,-0.0026 0.629168,-0.2535333 1.290328,-0.4166905 1.944823,-0.4653444 z"
                                        style="stroke-width:1.33298" />
                                </svg>
                                <svg id="coffee_svg_dark" xmlns="http://www.w3.org/2000/svg" height="100%" width="100%" viewBox="0 0 24 24" version="1.1">
                                    <path d="m 13.029677,0.03317241 c -0.923629,0.06770452 -1.826471,0.29936172 -2.656529,0.63760445 l -0.0079,0.0026 -0.0079,0.0026 C 5.964477,2.5438037 3.0887537,6.7928576 2.0606635,11.225656 l -0.00261,0.0027 v 0.0052 c -0.7161051,3.201616 -0.4793049,7.142872 2.1834152,9.751412 l 1.2108023,1.300795 0.1350989,-2.761582 c 0.2427759,-2.955454 2.0916797,-5.467134 4.4941481,-7.416777 v 0 c 2.693664,-1.966733 5.241247,-4.1860974 6.215437,-7.6367467 0.464003,-1.5651538 0.550527,-1.668068 0.217505,-0.9527232 0,0 0.258352,-0.3525437 0.183175,-0.9763056 C 16.752195,2.1466589 16.685955,1.8691394 16.474153,1.2638468 16.288365,0.90293534 16.070465,0.53238355 15.700013,0.36359792 14.93301,-0.03784328 13.913996,-0.03174027 13.030305,0.03315 Z"
                                        style="stroke-width:1.35914" />
                                    <path d="m 17.968345,1.7142133 -0.216522,2.2469151 c -0.351277,3.6491875 -2.76882,6.8763806 -5.851519,9.0775156 l -0.01825,0.01286 -0.01567,0.01286 c -2.7636114,2.129121 -5.3585289,5.317878 -5.2643653,9.225877 l 0.015655,0.645635 0.5791291,0.304879 c 2.0809561,1.095532 4.5054432,0.902465 6.4905002,0.0743 l 0.0052,-0.0027 0.0052,-0.0027 c 4.447879,-1.903497 7.336905,-6.176293 8.30085,-10.624738 l 0.0027,-0.0051 v -0.0051 C 22.65044,9.5552666 22.33923,5.7333203 19.645207,3.2559287 Z"
                                        style="stroke-width:1.36845" />
                                </svg>
                                <svg id="roast_svg" xmlns="http://www.w3.org/2000/svg" height="100%" width="100%" viewBox="0 0 24 24" version="1.1">
                                    <path d="m 6.0641245,0 3.092364,3.1753912 C 7.8803075,3.5122648 6.7207514,4.0668126 5.7523523,4.8096853 4.1032548,6.0744096 2.9861783,7.931656 2.9868219,10.021637 v 0.03017 c 0.00147,0.05842 0.00431,0.117629 0.00754,0.175993 -5.468e-4,0.01658 -0.00503,0.01017 -0.00503,0.02765 v 8.915244 H 21.010849 V 10.25545 c 0,-0.259793 7.7e-5,-0.04599 -0.005,-0.05279 0.0027,-0.04342 0.0058,-0.08728 0.0076,-0.130734 l 0.0026,-0.02514 v -0.02514 c 0,-2.087921 -1.118622,-3.9470978 -2.768878,-5.2119508 C 17.293267,4.0781533 16.150188,3.5309428 14.896406,3.1930394 l 3.104978,-3.190452 z m 5.9364165,5.3803237 c 1.866514,-2.574e-4 3.533505,0.5908483 4.680446,1.4708133 1.144301,0.877403 1.754137,1.97902 1.757354,3.157756 -0.0018,0.0346 -0.0046,0.06848 -0.0076,0.103083 l -0.0076,0.088 0.005,0.088 c 0.0072,0.137131 0.0061,0.146463 0.0076,0.198623 v 6.109422 h -3.233188 c 0.09321,-0.05975 0.196139,-0.10836 0.284097,-0.17347 0.924311,-0.684276 1.56388,-1.703676 1.566326,-2.858598 v -0.005 c 3.32e-4,-0.08643 -0.0032,-0.172775 -0.01004,-0.258957 l -0.05531,-0.711515 H 7.0474943 l -0.080453,0.683852 c -0.010259,0.08768 -0.017298,0.173316 -0.020113,0.261467 v 0.02523 c 6.086e-4,1.157007 0.6406642,2.178415 1.5663272,2.863619 0.08796,0.06512 0.190899,0.113715 0.284096,0.17347 H 5.5640339 v -6.298005 c 9.183e-4,-0.01443 0.00448,-0.0075 0.00503,-0.02263 l 0.00251,-0.0704 -0.00503,-0.06789 c -0.00283,-0.03971 -0.00366,-0.07845 -0.00503,-0.118169 C 5.5612564,8.838615 6.1717997,7.733639 7.3189979,6.853674 8.4661935,5.9736821 10.133055,5.3830913 12.000857,5.3828339 Z M 8.8246345,14.13183 h 6.3507835 c -0.144391,0.364588 -0.205356,0.750004 -0.608434,1.048401 -0.62375,0.461763 -1.539552,0.776831 -2.566907,0.776882 -1.027394,-4e-5 -1.943235,-0.315119 -2.5669075,-0.776882 -0.402652,-0.297355 -0.463539,-0.68353 -0.607968,-1.047822 z m -8.377173,4.993247 v 2.524171 c 0,0.857335 0.5532863,1.498617 1.1112582,1.845403 C 2.1166916,23.841385 2.7581932,24 3.4468597,24 H 20.55314 c 0.688667,0 1.330117,-0.158602 1.88814,-0.505349 0.557972,-0.346747 1.111258,-0.988055 1.111258,-1.845403 v -2.524171 h -2.574501 v 2.204932 c -0.09469,0.04024 -0.222707,0.09554 -0.424897,0.09554 H 3.4468597 c -0.2020984,0 -0.3300512,-0.05535 -0.4247929,-0.09526 V 19.125231 Z M 8.7215255,8.19374 c -0.920886,0 -1.7071521,0.720835 -1.7071521,1.63674 0,0.915892 0.7862271,1.639185 1.7071521,1.639185 0.920887,0 1.7095995,-0.723345 1.7095995,-1.639185 0,-0.915892 -0.7887385,-1.63674 -1.7095995,-1.63674 z m 0,1.028295 c 0.397079,0 0.678819,0.283864 0.678819,0.608432 0,0.324555 -0.28174,0.608432 -0.678819,0.608432 -0.397078,0 -0.676309,-0.283865 -0.676309,-0.608432 0,-0.324555 0.279231,-0.608432 0.676309,-0.608432 z" />
                                </svg>
                                <svg id="roast_svg_dark" xmlns="http://www.w3.org/2000/svg" height="100%" width="100%" viewBox="0 0 24 24" version="1.1">
                                    <path d="M 6.0640892,2e-7 9.156515,3.1753931 C 7.880332,3.5122675 6.7207331,4.0667278 5.7523326,4.8096018 4.103232,6.0743284 2.9861052,7.9314838 2.9867487,10.021471 v 0.03017 c 0.00147,0.05842 0.00431,0.117629 0.00754,0.175992 -5.468e-4,0.01658 -0.00503,0.01017 -0.00503,0.02765 v 8.915236 H 21.010812 v -8.915233 c 0,-0.2597932 7.1e-5,-0.04601 -0.005,-0.05279 0.0027,-0.04342 0.0058,-0.08728 0.0076,-0.130737 l 0.0026,-0.02514 v -0.02514 c 0,-2.0879272 -1.117839,-3.9470141 -2.768098,-5.2118695 C 17.294008,4.0780633 16.150262,3.5309041 14.896477,3.1930001 l 3.104998,-3.190478 z m 5.9359478,5.3803176 c 1.866518,-3.167e-4 3.534437,0.7269375 4.68138,1.807686 1.144304,1.077602 1.754184,2.429153 1.757402,3.8768462 -0.0018,0.04249 -0.0046,0.08322 -0.0076,0.125714 l -0.0076,0.110626 0.005,0.105594 c 0.0073,0.168429 0.006,0.179808 0.0076,0.243875 v 7.504788 H 15.203087 5.56377 v -7.736092 c 9.269e-4,-0.01774 0.00448,-0.009 0.00503,-0.02765 l 0.00251,-0.08549 -0.00503,-0.08296 C 5.56345,11.174485 5.56262,11.126225 5.56125,11.077433 5.5609896,9.6276868 6.1714495,8.2712798 7.3186499,7.1905308 8.46585,6.1097825 10.132223,5.3831614 12.000028,5.3828448 Z"
                                        style="opacity:0.8" />
                                    <path d=" m 0.44744,19.125068 v 2.524176 c 0,0.857336 0.5532873,1.49862 1.1112602,1.845406 C 2.1166732,23.841385 2.758176,24 3.4468437,24 H 20.553156 c 0.688668,0 1.330119,-0.158602 1.888144,-0.50535 0.557973,-0.346747 1.11126,-0.988057 1.11126,-1.845406 v -2.524176 h -2.574507 c -2.541687,0.03043 -15.414223,0.03043 -17.9560029,1.55e-4 z" />
                                    <path d="M 7.0403371,13.377146 H 17.066091 c -0.227943,0.924259 -0.324186,1.901319 -0.960509,2.657783 -0.984695,1.170606 -2.430439,1.969326 -4.052288,1.969458 C 10.431386,18.004284 8.98558,17.205535 8.00101,16.034929 7.3653572,15.281109 7.2692373,14.302123 7.0412314,13.378614 Z"
                                        style="opacity:0.2" />
                                    <path d=" m 8.662057,8.4412488 c -0.728578,0 -1.3506479,0.59482 -1.3506479,1.350608 0,0.7557772 0.6220399,1.3526252 1.3506479,1.3526252 0.728579,0 1.352586,-0.59689 1.352586,-1.3526252 0,-0.755777 -0.624027,-1.350608 -1.352586,-1.350608 z"
                                        style="opacity:0.2" />
                                    <path d=" m 12.000037,5.3803179 v 0.00257 c -1.867805,3.167e-4 -3.534178,0.7269378 -4.6813779,1.8076859 -1.1472003,1.080748 -1.757661,2.437156 -1.7574036,3.8869032 0.00142,0.04879 0.00219,0.09705 0.00502,0.145821 l 0.00502,0.08296 -0.00245,0.08549 c -5.535e-4,0.01868 -0.00412,0.0099 -0.00502,0.02765 v 7.736092 h 9.6393185 3.233218 v -7.504784 c -0.0015,-0.06407 -2.81e-4,-0.07545 -0.0076,-0.243875 l -0.005,-0.105593 0.0076,-0.110627 c 0.003,-0.04249 0.0058,-0.08322 0.0076,-0.125713 C 18.435762,9.6172048 17.825864,8.2656538 16.68156,7.1880518 15.534617,6.1073033 13.866698,5.3800489 12.00018,5.3803655 Z M 8.661223,8.4400588 c 0.728559,0 1.352623,0.596844 1.352623,1.352622 0,0.7557352 -0.624044,1.3526232 -1.352623,1.3526232 -0.728608,0 -1.3501072,-0.596846 -1.3501072,-1.3526232 0,-0.755788 0.6215302,-1.352622 1.3501072,-1.352622 z M 7.0421004,13.377883 H 17.066084 c -0.227943,0.924259 -0.324088,1.901012 -0.960412,2.657476 -0.984695,1.170606 -2.430987,1.968461 -4.052837,1.968591 C 10.430928,18.003847 8.984569,17.205965 7.999999,16.035359 7.364345,15.281539 7.2701065,14.301392 7.0421004,13.377883 Z" />
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>

                <div>
                    <div class="subtitle title-separate" id="subtitle2" name="subtitle"></div>
                    <div class="subtitlerow" id="subtitlerow">
                        <span class="blend-percent" id="blend_percent"></span>
                        <span class="subtitle title-top" id="subtitle1" name="subtitle"></span>
                        <span class="weight" id="weight"></span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>

</html>