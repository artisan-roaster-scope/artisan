#!/usr/bin/python
# -*- coding: utf-8 -*-

from bottle import default_app, request, abort, route, template, static_file, get, TEMPLATE_PATH
from gevent import Timeout, signal as gsignal, kill
from gevent.pywsgi import WSGIServer
#from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from platform import system as psystem

if psystem() != 'Windows':
    from signal import SIGQUIT

from multiprocessing import Process as mProcess

from json import dumps as jdumps
from requests import get as rget

import time as libtime


wsocks = [] # list of open web sockets
process = None
port = None
nonesymbol = "--"
timecolor="#FFF"
timebackground="#000"
btcolor="#00007F"
btbackground="#CCCCCC"
etcolor="#FF0000"
etbackground="#CCCCCC"
showet = True
showbt = True
static_path = ""
        
# pickle hack:
def work(p,rp,nonesym,timec,timebg,btc,btbg,etc,etbg,showetflag,showbtflag):
    global port, static_path, nonesymbol, timecolor, timebackground, btcolor, btbackground, etcolor, etbackground, showbt, showet
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
    s = WSGIServer(("0.0.0.0", p), default_app(), handler_class=WebSocketHandler)
    s.serve_forever()
        
def startWeb(p,resourcePath,nonesym,timec,timebg,btc,btbg,etc,etbg,showetflag,showbtflag):
    global port, process, static_path, nonesymbol, timecolor, timebackground, btcolor, btbackground, etcolor, etbackground, showet, showbt
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
    
    # start the server in a separate process
    # using multiprocessing
    process = mProcess(name='WebLCDs',target=work,args=(
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
        showbtflag,))
    process.start()
    
    libtime.sleep(4)
    
    # check successful start
    url = "http://127.0.0.1:" + str(port) + "/status"
    r = rget(url,timeout=2)
    
    if r.status_code == 200:
        return True
    else:
        return False
    
def stopWeb():
    global wsocks, process
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
                    wsocks.remove(ws)
                else:
                    ws.send(msg)
        except Exception:
            wsocks.remove(ws)

# route to push new data to the client
@route('/send', method='POST')
def send():
    send_all(jdumps(request.json))

# route that establishes the websocket between the Artisan app and the clients
@route('/websocket')
def handle_websocket():
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')
    wsocks.append(wsock)
    while True:
        try:
            if wsock.closed:
                wsocks.remove(wsock)
                break
            else:
                message = wsock.receive()
                if message is None:
                    wsocks.remove(wsock)
                    break
        except Exception:
            wsocks.remove(wsock)
            break
            
@route('/status')
def status():
    return "1"
    
# route to serve the static page
@route('/artisan')
def index():
    if not (showbt and showet):
        showspace_str = "inline"
    else:
        showspace_str = "none"
    if showbt:
        showbt_str = "inline"
    else:
        showbt_str = "none"
    if showet:
        showet_str = "inline"
    else:
        showet_str = "none"
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

