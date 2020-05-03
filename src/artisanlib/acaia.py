#!/usr/bin/env python3

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

class AcaiaBLE(object):

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
        self.battery = None
        self.firmware = None # on connect this is set to a tripel of ints, (major, minor, patch)-version
        self.unit = 2 # 1: kg, 2: g, 5: ounce
        self.max_weight = 0 # in g
    
    def reset(self):
        self.__init__()

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

    # should be send every 3-5sec
    # this seems not to be essential for the acaia. The Pearl disconnects from time to time, the Lunar never!?
    def sendHeartbeat(self,write):
        self.sendMessage(write,self.MSG_SYSTEM,b'\x02,\x00')

    def sendStop(self,write):
        self.sendMessage(write,self.MSG_SYSTEM,b'\x00,\x00')

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
        self.sendEvent(write,
            bytes([ # pairs of key/setting
                    0,  # weight id
                    5,  # 0, 1, 3, 5, 7, 15, 31, 63, 127  # weight argument (speed of notifications in 1/10 sec)
                       # 5 or 7 seems to be good values for this app in Artisan
#                    1,   # battery id
#                    255, #2,  # battery argument (if 0 : fast, 1 : slow)
#                    2,  # timer id
#                    255, #5,  # timer argument
#                    3,  # key (not used)
#                    255, #4   # setting (not used)
                ])
                )

    def parseInfo(self,data):
#        if len(data)>1:
#            data[1]
        if len(data)>4:
            self.firmware = (data[2],data[3],data[4])
            #print("{}.{}.{}".format(self.firmware[0],self.firmware[1],self.firmware[2]))
        # passwd_set
#        if len(data)>5:
#            data[5]
#        if len(data)>6:
#            data[6]
   
    # returns length of consumed data or -1 on error
    def parseWeightEvent(self,payload):
        if len(payload) < self.EVENT_WEIGHT_LEN:
            return -1
        else:
            # first 4 bytes encode the weight as unsigned long
            value = ((payload[3] & 0xff) << 24) + \
                ((payload[2] & 0xff) << 16) + ((payload[1] & 0xff) << 8) + (payload[0] & 0xff)
            
            unit = payload[4]

            if unit == 1:
                value /= 10
            elif unit == 2:
                value /= 100
            elif unit == 3:
                value /= 1000
            elif unit == 4:
                value /= 10000
            
            # convert received weight data to g
            if self.unit == 1: # kg
                value = value * 1000
            elif self.unit == 5: # lbs
                value = value * 28.3495
            
            #stable = (payload[5] & 0x01) != 0x01
            
            # if 2nd bit of payload[5] is set, the reading is negative
            if (payload[5] & 0x02) == 0x02:
                value *= -1

            # if value is fresh and reading is stable
            if value != self.weight: # and stable:
                self.weight = value
            
            return self.EVENT_WEIGHT_LEN
    
    def parseBatteryEvent(self,payload):
        if len(payload) < self.EVENT_BATTERY_LEN:
            return -1
        else:
            b = payload[0]
            if 0 <= b and b <= 100:
                self.battery = int(payload[0])
                #print("bat","{}%".format(self.battery))
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
                
    def parseStatus(self,payload):
        # battery level (7 bits of first byte) + TIMER_START (1bit)
        if payload and len(payload) > 0:
            self.battery = int(payload[0] & ~(1 << 7))
            #print("bat","{}%".format(self.battery))
        # unit (7 bits of second byte) + CD_START (1bit)
        if payload and len(payload) > 1:
            self.unit = int(payload[1] & ~(1 << 7))
        # mode (7 bits of third byte) + tare (1bit)
        # sleep (4th byte), 0:off, 1:5sec, 2:10sec, 3:20sec, 4:30sec, 5:60sec
        # key disabled (5th byte), touch key setting 0: off , 1:On
        # sound (6th byte), beep setting 0 : off 1: on
        # resolution (7th byte), 0 : default, 1 : high
        # max weight (8th byte)
        if payload and len(payload) > 7:
            self.max_weight = (payload[7] + 1) * 1000

    def parseScaleData(self,write,msgType,data):
        if msgType == self.MSG_INFO:
            self.parseInfo(data)
            self.sendId(write)
        elif msgType == self.MSG_STATUS:
            self.parseStatus(data)
            if not self.notificationConfSent:
                self.confNotifications(write)
        elif msgType == self.MSG_EVENT:
            self.parseScaleEvents(data)

    # returns None or new weight data as first result and
    # None or new battery level as second result
    def processData(self,write,data):
        data = data.data() # convert QByteArray to Python byte array
        if len(data) == 3 and data[0] == self.HEADER1 and data[1] == self.HEADER2:
            # data package contains just the header (alternately send with payload)
            self.msgType = data[2]
            # we now expect a data package belonging to this header
            return None, None
        elif self.msgType is None and len(data)>3 and data[0] == self.HEADER1 and data[1] == self.HEADER2:
            # a complete package containing header and payload
            self.msgType = data[2]
            data = data[3:]
        # otherwise we might have received a payload package belonging to the header we previously received
        # in any case data now contains the package without the first 3 bytes (magic1, magic2, msgType)
        
        old_weight = self.weight
        old_battery = self.battery

        if self.msgType != None:
            msgCRC = data[-2:]
            if msgCRC != self.crc(data[:-2]):
#                print("CRC check failed")
                return None, None
            else:
                offset = 0
                if self.msgType in [self.MSG_STATUS, self.MSG_EVENT, self.MSG_INFO]:
                    l = data[0]
                    if l == 0:
                        l = 1
                    offset = 1
                elif self.msgType == self.MSG_SYSTEM:
                    l = 2
                    return None, None # we ignore system messages
                else:
                    l = 2
                if len(data) < (l + 2):
#                    print("Invalid data length")
                    return None, None
                self.parseScaleData(write,self.msgType,data[offset:offset+l-1]);
            self.msgType = None # message consumed completely
            
        if old_weight == self.weight:
            w = None # weight did not change
        else:
            w = self.weight
        if old_battery == self.battery:
            b = None # battery did not change
        else:
            b = self.battery
        return w,b

