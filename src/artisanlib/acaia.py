#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ABOUT
# Acaia scale support for Artisan

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
# Marko Luther, 2019

class AcaiaBLE():

    SERVICE_UUID = "00001820-0000-1000-8000-00805f9b34fb"
    CHAR_UUID =    "00002a80-0000-1000-8000-00805f9b34fb"
    
    HEADER1      = 0xef
    HEADER2      = 0xdd

    MSG_SYSTEM = 0
    MSG_TARE = 4
    MSG_INFO = 7
    MSG_STATUS = 8
    MSG_IDENTIFY = 11
    MSG_EVENT = 12
    MSG_TIMER = 13

    EVENT_WEIGHT = 5
    EVENT_BATTERY = 6
    EVENT_TIMER = 7
    EVENT_KEY = 8
    EVENT_ACK = 11

    EVENT_WEIGHT_LEN = 6
    EVENT_BATTERY_LEN = 1
    EVENT_TIMER_LEN = 3
    EVENT_KEY_LEN = 1
    EVENT_ACK_LEN = 2

    TIMER_START = 0
    TIMER_STOP = 1
    TIMER_PAUSE = 2

    TIMER_STATE_STOPPED = 0
    TIMER_STATE_STARTED = 1
    TIMER_STATE_PAUSED = 2
        
    def __init__(self):
        self.notificationConfSent = False
        # holds msgType on messages split in header and payload
        self.msgType = None
        self.weight = None

    # return a bytearray of len 2 containing the even and odd CRCs over the given payload
    def crc(self,payload):
        cksum1 = 0
        cksum2 = 0
        for i in range(len(payload)):
            if (i % 2) == 0:
                cksum1 = (cksum1 + payload[i]) & 0xFF
            else:
                cksum2 = (cksum2 + payload[i]) & 0xFF
        return bytes([cksum1,cksum2])

    # constructs message bytearray of the given type (int) and payload (bytearray) by adding headers and CRCs
    def message(self,tp, payload):
        return bytes([self.HEADER1,self.HEADER2,tp]) + payload + self.crc(payload)

    def sendMessage(self,write,tp,payload):
        msg = self.message(tp,payload)
        write(msg)

#    # should be send every 3sec
#    # seems useless with latest firmware
#    def sendHeartbeat(self,write):
#        self.sendMessage(write,self.MSG_SYSTEM,b'\x02,\x00')

    def sendTare(self,write):
        self.sendMessage(write,self.MSG_TARE,b'\x00')

    def sendTimerCommand(self,write,cmd):
        self.sendMessage(write,self.MSG_TIMER,b'\x00' + cmd)

    def sendId(self,write):
        self.sendMessage(write,self.MSG_IDENTIFY,b'\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d')

    def sendEvent(self,write,payload):
        self.sendMessage(write,self.MSG_EVENT,bytes([len(payload)+1]) + payload)

    # configure notifications
    def confNotifications(self,write):
        # seems to be ignored / not needed by Pearl
        self.sendEvent(write,
            bytes([ # pairs of key/setting
                    0,  # weight
                    5,  # weight argument (speed of notifications in 1/10 sec)
#                    1,  # battery
#                    2,  # battery argument (if 0 : fast, 1 : slow)
#                    2,  # timer
#                    5,  # timer argument
#                    3,  # key
#                    4   # setting
                ]))

    def parseInfo(self,data):
        pass
#        print("battery",data[4]) # most likely not the battery

    # returns length of consumed data or -1 on error
    def parseWeightEvent(self,payload):
        if len(payload) < self.EVENT_WEIGHT_LEN:
            return -1
        else:
            value = ((payload[1] & 0xff) << 8) + (payload[0] & 0xff)
            unit = payload[4] & 0xFF

            if unit == 1:
                value /= 10
            elif unit == 2:
                value /= 100
            elif unit == 3:
                value /= 1000
            elif unit == 4:
                value /= 10000

            if (payload[5] & 0x02) == 0x02:
                value *= -1

            if value != self.weight:
                self.weight = value

            return self.EVENT_WEIGHT_LEN
    
    def parseBatteryEvent(self,payload):
        if len(payload) < self.EVENT_BATTERY_LEN:
            return -1
        else:
#            print("battery: ", payload[0])
            return self.EVENT_BATTERY_LEN
    
    def parseTimerEvent(self,payload):
        if len(payload) < self.EVENT_TIMER_LEN:
            return -1
        else:
#            print("minutes",payload[0])
#            print("seconds",payload[1])
#            print("mseconds",payload[2])
            return self.EVENT_TIMER_LEN
    
    def parseAckEvent(self,payload):
        if len(payload) < self.EVENT_ACK_LEN:
            return -1
        else:
            return self.EVENT_ACK_LEN
    
    def parseKeyEvent(self,payload):
        if len(payload) < self.EVENT_KEY_LEN:
            return -1
        else:
            return self.EVENT_KEY_LEN

    def parseScaleEvent(self,payload):
        if payload and len(payload) > 0:
            event = payload[0]
            payload = payload[1:]
            val = -1
            if event == self.EVENT_WEIGHT:
                val = self.parseWeightEvent(payload)
            elif event == self.EVENT_BATTERY:
                val = self.parseBatteryEvent(payload)
            elif event == self.EVENT_TIMER:
                val = self.parseTimerEvent(payload)
            elif event == self.EVENT_ACK:
                val = self.parseAckEvent(payload)
            elif event == self.EVENT_KEY:
                val = self.parseKeyEvent(payload)
            else: 
                return -1
            if val < 0:
                return -1
            else:
                return val + 1
        else:
            return -1

    def parseScaleEvents(self,payload):
        if payload and len(payload) > 0:
            pos = self.parseScaleEvent(payload)
            if pos > -1:
                self.parseScaleEvents(payload[pos+1:])

    def parseScaleData(self,write,msgType,data):
        if msgType == self.MSG_INFO:
            self.parseInfo(data)
            self.sendId(write)
        elif msgType == self.MSG_STATUS:
            if not self.notificationConfSent:
                self.confNotifications(write)
        elif msgType == self.MSG_EVENT:
            self.parseScaleEvents(data)

    # returns None or new weight data
    def processData(self,write,data):
        data = data.data() # convert QByteArray to Python byte array
        if len(data) == 3 and data[0] == self.HEADER1 and data[1] == self.HEADER2:
            # data package contains just the header (alternately send with payload)
            self.msgType = data[2]
            # we now expect a data package belonging to this header
            return None
        elif self.msgType is None and len(data)>3 and data[0] == self.HEADER1 and data[1] == self.HEADER2:
            # a complete package containing header and payload
            self.msgType = data[2]
            data = data[3:]
        # otherwise we might have received a payload package belonging to the header we previously received
        # in any case data now contains the package without the first 3 bytes (magic1, magic2, msgType)
        
        old_weight = self.weight

        if self.msgType != None:
            msgCRC = data[-2:]
            if msgCRC != self.crc(data[:-2]):
#                print("CRC check failed")
                return None
            else:
                offset = 0
                if self.msgType in [self.MSG_STATUS, self.MSG_EVENT, self.MSG_INFO]:
                    l = data[0]
                    if l == 0:
                        l = 1
                    offset = 1
                elif self.msgType == self.MSG_SYSTEM:
                    l = 2
                    return # we ignore system messages
                else:
                    l = 2
                if len(data) < (l + 2):
#                    print("Invalid data length")
                    return None
                self.parseScaleData(write,self.msgType,data[offset:offset+l]);
            self.msgType = None # message consumed completely
            
        if old_weight == self.weight:
            return None # weight did not change
        else:
            return self.weight

