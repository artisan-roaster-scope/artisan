#!/usr/bin/env python3

# ABOUT
# WebSocket support for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2020

from websocket import create_connection
import json
import random

from PyQt5.QtWidgets import QApplication


class wsport(object):
    def __init__(self,aw):
        self.aw = aw
        
        # connects to "ws://<host>:<port>/<path>"
        self.host = '127.0.0.1' # the TCP host
        self.port = 8090 # the TCP port
        self.path = "WebSocket"
        self.machineID = 0
        
        self.timeout = 0.4
        
        self.ws = None

    def connect(self):
        if not self.is_connected():
            try:
                error = ""
                try:
                    self.ws = create_connection("ws://{}:{}/{}".format(self.host,self.port,self.path)) # ,sslopt={"check_hostname": False})
                    self.ws.settimeout(self.timeout)
                except Exception as e1:
                    error = e1
                    # we retry without the port
                    self.ws = create_connection("ws://{}/{}".format(self.host,self.port,self.path)) # ,sslopt={"check_hostname": False})                    
                self.aw.sendmessage(QApplication.translate("Message","WebSocket connected", None))
            except Exception:
                self.aw.qmc.adderror(QApplication.translate("Error Message","WebSocket connection failed: {}",None).format(error))
    
    def is_connected(self):
        return self.ws != None and self.ws.connected
            
    def disconnect(self):
        if self.is_connected():
            self.ws.close()
            self.ws = None
    
    # takes a request as dict to be send as JSON
    # and returns a dict generated from the JSON response
    # or None on exception
    def send(self,request):
        self.connect()
        id = random.randint(1,99999)
        request["id"] = id
        request["roasterID"] = self.machineID
        self.ws.send(json.dumps(request))
        response = json.loads(self.ws.recv())
        if response is not None and "id" in response:
            if response["id"] == id:
                return response
            else:
                return None
    