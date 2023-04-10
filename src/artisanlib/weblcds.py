#
# ABOUT
# WebLCDs for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2023

from bottle import default_app, request, abort, route, template, static_file, get, TEMPLATE_PATH # type: ignore
from gevent import Timeout, kill # type: ignore

# what is the exact difference between the next too?
#from gevent import signal as gsignal # works only up to gevent v1.4.0
#from gevent.signal import signal as gsignal # works on gevent v1.4.0 and newer
from gevent import signal_handler as gsignal # type: ignore # works on gevent v1.4.0 and newer

from gevent.pywsgi import WSGIServer # type: ignore
#from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler # type: ignore
from platform import system as psystem

if psystem() != 'Windows':
    from signal import SIGQUIT

import multiprocessing as mp

from json import dumps as jdumps
from requests import get as rget

import time as libtime
from typing import Any, List


wsocks: List[Any] = [] # list of open web sockets
process = None
port = None
nonesymbol = '--'
timecolor='#FFF'
timebackground='#000'
btcolor='#00007F'
btbackground='#CCCCCC'
etcolor='#FF0000'
etbackground='#CCCCCC'
showet = True
showbt = True
static_path = ''

# pickle hack:
def work(p,rp,nonesym,timec,timebg,btc,btbg,etc,etbg,showetflag,showbtflag):
    global port, static_path, nonesymbol, timecolor, timebackground, btcolor, btbackground, etcolor, etbackground, showbt, showet # pylint: disable=global-statement
    port = p
    static_path = rp
    nonesymbol = nonesym
    timecolor = timec
    timebackground = timebg
    btcolor = btc
    btbackground = btbg
    etcolor = etc
    etbackground = etbg
    showet = showetflag
    showbt = showbtflag
    TEMPLATE_PATH.insert(0,rp)
    s = WSGIServer(('0.0.0.0', p), default_app(), handler_class=WebSocketHandler)
    s.serve_forever()

def startWeb(p,resourcePath,nonesym,timec,timebg,btc,btbg,etc,etbg,showetflag,showbtflag):
    global port, process, static_path, nonesymbol, timecolor, timebackground, btcolor, btbackground, etcolor, etbackground, showet, showbt # pylint: disable=global-statement
    port = p
    static_path = resourcePath
    nonesymbol = nonesym
    timecolor = timec
    timebackground = timebg
    btcolor = btc
    btbackground = btbg
    etcolor = etc
    etbackground = etbg
    showet = showetflag
    showbt = showbtflag
    if psystem() != 'Windows':
        gsignal(SIGQUIT, kill)

    process = mp.Process(name='WebLCDs',target=work,args=(
        port,
        resourcePath,
        nonesym,
        timec,
        timebg,
        btc,
        btbg,
        etc,
        etbg,
        showetflag,
        showbtflag))
    process.start()

    libtime.sleep(4)

    if process.is_alive():
        # check successful start
        url = f'http://127.0.0.1:{port}/status'
        r = rget(url,timeout=2)

        return bool(r.status_code == 200)
    return False

def stopWeb():
    global wsocks, process # pylint: disable=global-statement
    for ws in wsocks:
        ws.close()
    wsocks = []
    if process:
        process.terminate()
        process.join()
        process = None

class TooLong(Exception):
    pass
time_to_wait = 1 # seconds

def send_all(msg):
    socks = wsocks[:]
    for ws in socks:
        try:
            with Timeout(time_to_wait, TooLong):
                if ws.closed:
                    try:
                        wsocks.remove(ws)
                    except Exception: # pylint: disable=broad-except
                        pass
                else:
                    ws.send(msg)
        except Exception: # pylint: disable=broad-except
            try:
                wsocks.remove(ws)
            except Exception: # pylint: disable=broad-except
                pass

# route to push new data to the client
@route('/send', method='POST')
def send():
    send_all(jdumps(request.json))

# route that establishes the websocket between the Artisan app and the clients
@route('/websocket')
def handle_websocket():
    wsock = request.environ.get('wsgi.websocket')  # @UndefinedVariable
    if not wsock:
        abort(400, 'Expected WebSocket request.')
    wsocks.append(wsock)
    while True:
        try:
            if wsock.closed:
                try:
                    wsocks.remove(wsock)
                except Exception: # pylint: disable=broad-except
                    pass
                break
            message = wsock.receive()
            if message is None:
                try:
                    wsocks.remove(wsock)
                except Exception: # pylint: disable=broad-except
                    pass
                break
        except Exception: # pylint: disable=broad-except
            try:
                wsocks.remove(wsock)
            except Exception: # pylint: disable=broad-except
                pass
            break

@route('/status')
def status():
    return '1'

# route to serve the static page
@route('/artisan')
def index():
    showspace_str = 'inline' if not (showbt and showet) else 'none'
    showbt_str = 'inline' if showbt else 'none'
    showet_str = 'inline' if showet else 'none'
    return template('artisan.tpl',
        port=str(port),
        nonesymbol=nonesymbol,
        timecolor=timecolor,
        timebackground=timebackground,
        btcolor=btcolor,
        btbackground=btbackground,
        etcolor=etcolor,
        etbackground=etbackground,
        showbt=showbt_str,
        showet=showet_str,
        showspace=showspace_str)


# Static Routes

@get(r'/<filename:re:.*\.js>')
def javascripts(filename):
    return static_file(filename, root=static_path)

@get(r'/<filename:re:.*\.(eot|ttf|woff|svg)>')
def fonts(filename):
    return static_file(filename, root=static_path)
