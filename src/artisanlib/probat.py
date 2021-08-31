# -*- coding: utf-8 -*-
#
# ABOUT
# Probat Middleware support for Artisan

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
# Marko Luther, 2019

from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST
import requests

CONNECT_TIMEOUT = 0.5 # in seconds
READ_TIMEOUT = 0.5 # in seconds

DISCOVER_PORT = 24711
DISCOVER_BODY = "ROASTER_MIDDLEWARE_DISCOVERY"
GET_ROASTERS = "/api/roasters"
GET_DATA = "/api/roasters/{id}/data"


class ProbatMiddleware():
    """ this class handles the communications with the Probat Middleware"""
    def __init__(self):
        self.probat_middleware_endpoint = None
        self.probat_middleware_ID = None
        self.probat_middleware_name = None

    # discover the Probat Middleware within the local area network via a broadcast message and
    # returns IP and port of its endpoint
    @staticmethod
    def discover():
        s = socket(AF_INET, SOCK_DGRAM) #create UDP socket
        s.bind(('', 0))
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1) #this is a broadcast socket
        s.settimeout(.5)
        s.sendto(DISCOVER_BODY.encode('utf-8'), ('<broadcast>', DISCOVER_PORT))
        s.settimeout(.5)
        data, addr = s.recvfrom(1024) # buffer size is 1024 bytes
        port = data.decode('ascii')
        ip = addr[0]
        return ip, port
    
    @staticmethod
    def getHeaders():
        headers = {"user-agent": "Artisan"}
        headers["Accept-Encoding"] = "deflate, compress, gzip" # identity should not be in here!
        return headers

    def getJSON(self,url):
        r = requests.get(url,
            headers = self.getHeaders(),
            timeout = (CONNECT_TIMEOUT,READ_TIMEOUT))
        r.raise_for_status()
        return r.json()

    # returns the list of roasters sorted by ID
    def getRoasters(self):
        if self.probat_middleware_endpoint is not None:
            try:
                return sorted(self.getJSON(self.probat_middleware_endpoint + GET_ROASTERS), key=lambda x:x["id"])                
            except Exception: # pylint: disable=broad-except
                return []
        else:
            return []

    def isConnected(self):
        return bool(self.probat_middleware_ID is not None and self.probat_middleware_name)

    # returns True if connected and False otherwise
    def connect(self):
        if self.probat_middleware_endpoint is None:
            ip,port = self.discover()
            if port is None or ip is None:
                self.probat_middleware_endpoint = None
            else:
                self.probat_middleware_endpoint = "http://{}:{}".format(ip,port)
        if self.probat_middleware_ID is None or self.probat_middleware_name is None:
            roasters = self.getRoasters()
            if len(roasters):
                self.probat_middleware_ID = roasters[0]["id"]
                self.probat_middleware_name = roasters[0]["name"]
            else:
                self.probat_middleware_ID = None
                self.probat_middleware_name = None
        return self.isConnected()

    def disconnect(self):
        self.probat_middleware_ID = None
        self.probat_middleware_name = None
        self.probat_middleware_endpoint = None
    
    # returns None if not connected and the ReST URL to GET data from the connected roaster otherwise
    def getRoasterURL(self):
        if self.probat_middleware_endpoint is not None and self.isConnected():
            return self.probat_middleware_endpoint + GET_DATA.format(id=self.probat_middleware_ID)
        return None
    
    def getRoasterName(self):
        return self.probat_middleware_name