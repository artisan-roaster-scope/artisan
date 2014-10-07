#!/usr/bin/python
# -*- coding: utf-8 -*-

from bottle import default_app, request, Bottle, abort, route, template, static_file, get, TEMPLATE_PATH, debug
import gevent
import signal
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
import multiprocessing
import json
import requests

app = default_app() #Bottle()
wsocks = [] # list of open web sockets
server = None
process = None
port = None
timecolor="#FFF",
timebackground="#000",
btcolor="#00007F",
btbackground="#CCCCCC",
etcolor="#FF0000",
etbackground="#CCCCCC"
showet = True
showbt = True
        
def startWeb(p,resourcePath,timec,timebg,btc,btbg,etc,etbg,showetflag,showbtflag):
    global port, server, process, TEMPLATE_PATH, static_path, timecolor, timebackground, btcolor, btbackground, etcolor, etbackground, showet, showbt
    try:
        port = p
        static_path = resourcePath
        TEMPLATE_PATH.insert(0,resourcePath)
        timecolor = timec
        timebackground = timebg
        btcolor = btc
        btbackground = btbg
        etcolor = etc
        etbackground = etbg
        showet = showetflag
        showbt = showbtflag
        server = WSGIServer(("0.0.0.0", port), app, handler_class=WebSocketHandler)
        gevent.signal(signal.SIGQUIT, gevent.kill)
        # start the server in a separate process
        process = multiprocessing.Process(target=server.serve_forever)
        process.start()
        
        # check successful start
        url = "http://127.0.0.1:" + str(port) + "/artisan/status"
        r = requests.get(url,timeout=0.5)
        if r.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
#        print(e)
#        import traceback
#        import sys
#        traceback.print_exc(file=sys.stdout)
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
    server = None

from gevent import Timeout
class TooLong(Exception):
    pass
time_to_wait = 1 # seconds
    
def send_all(msg):
    global wsocks
    socks = wsocks[:]
    for ws in socks:
        try:
            with Timeout(time_to_wait, TooLong):
                if ws.closed:
                    wsocks.remove(ws)
                else:
                    ws.send(msg)
        except:
            wsocks.remove(ws)

# route to push new data to the client
@route('/send', method='POST')
def send():
    send_all(json.dumps(request.json))

# route that establishes the websocket between the Artisan app and the clients
@route('/websocket')
def handle_websocket():
    global wsocks
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
        except Exception: #WebSocketError:
            wsocks.remove(wsock)
            break
            
@route('/artisan/status')
def status():
    return "1"
    
# route to serve the static page
@route('/artisan')
def index():
    if showbt:
        showbt_str = "inline"
    else:
        showbt_str = "none"
    if showet:
        showet_str = "inline"
    else:
        showet_str = "none"
    return template('artisan',
        port=str(port),
        timecolor=timecolor,
        timebackground=timebackground,
        btcolor=btcolor,
        btbackground=btbackground,
        etcolor=etcolor,
        etbackground=etbackground,
        showbt=showbt_str,
        showet=showet_str)

        
# Static Routes

@get('/<filename:re:.*\.js>')
def javascripts(filename):
    return static_file(filename, root=static_path)

#@get('/<filename:re:.*\.css>')
#def stylesheets(filename):
#    return static_file(filename, root='static/css')
#
#@get('/<filename:re:.*\.(jpg|png|gif|ico)>')
#def images(filename):
#    return static_file(filename, root='static/img')

@get('/<filename:re:.*\.(eot|ttf|woff|svg)>')
def fonts(filename):
    return static_file(filename, root=static_path)

