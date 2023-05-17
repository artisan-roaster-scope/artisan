#
# ABOUT
# Acaia scale support for Artisan

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

import logging
from typing import List, Optional, Union, Tuple, Callable
from typing_extensions import Final  # Python <=3.7


from artisanlib.ble import UUID, BLE_CHAR_TYPE

_log: Final[logging.Logger] = logging.getLogger(__name__)


class AcaiaBLE():

    # Acaia Pearl, Lunar:
    DEVICE_NAME_PEARL:Final[str] = 'PROCHBT'
    DEVICE_NAME_LUNAR:Final[str] = 'ACAIA'
    SERVICE_UUID_LEGACY:Final[UUID] = '00001820-0000-1000-8000-00805f9b34fb'
    CHAR_UUID_LEGACY:Final[Tuple[str, BLE_CHAR_TYPE]] = ('00002a80-0000-1000-8000-00805f9b34fb', BLE_CHAR_TYPE.BLE_CHAR_NOTIFY_WRITE)

    # Acaia Pearl (2021):
    DEVICE_NAME_PEARL2021:Final[str] = 'PEARL-'
    SERVICE_UUID:Final[UUID] = '49535343-FE7D-4AE5-8FA9-9FAFD205E455'
    CHAR_UUID:Final[Tuple[UUID, BLE_CHAR_TYPE]] = ('49535343-1E4D-4BD9-BA61-23C647249616', BLE_CHAR_TYPE.BLE_CHAR_NOTIFY)
    CHAR_UUID_WRITE:Final[Tuple[UUID, BLE_CHAR_TYPE]] = ('49535343-8841-43F4-A8D4-ECBE34729BB3', BLE_CHAR_TYPE.BLE_CHAR_WRITE)

    # Acaia Pearl S:
    DEVICE_NAME_PEARLS:Final[str] = 'PEARLS'

    # Acaia Lunar (2021):
    DEVICE_NAME_LUNAR2021:Final[str] = 'LUNAR-'

    # Acaia Pyxis:
    DEVICE_NAME_PYXIS:Final[str] = 'PYXIS'


    HEADER1:Final[int]      = 0xef
    HEADER2:Final[int]      = 0xdd

    MSG_SYSTEM:Final[int] = 0
    MSG_TARE:Final[int] = 4
    MSG_INFO:Final[int] = 7
    MSG_STATUS:Final[int] = 8
    MSG_IDENTIFY:Final[int] = 11
    MSG_EVENT:Final[int] = 12
    MSG_TIMER:Final[int] = 13

    EVENT_WEIGHT:Final[int] = 5
    EVENT_BATTERY:Final[int] = 6
    EVENT_TIMER:Final[int] = 7
    EVENT_KEY:Final[int] = 8
    EVENT_ACK:Final[int] = 11

    EVENT_WEIGHT_LEN:Final[int] = 6
    EVENT_BATTERY_LEN:Final[int] = 1
    EVENT_TIMER_LEN:Final[int] = 3
    EVENT_KEY_LEN:Final[int] = 1
    EVENT_ACK_LEN:Final[int] = 2

    TIMER_START:Final[int] = 0
    TIMER_STOP:Final[int] = 1
    TIMER_PAUSE:Final[int] = 2

    TIMER_STATE_STOPPED:Final[int] = 0
    TIMER_STATE_STARTED:Final[int] = 1
    TIMER_STATE_PAUSED:Final[int] = 2

    # Acaia Protocol Parser
    E_PRS_CHECKHEADER1:Final[int] = 0
    E_PRS_CHECKHEADER2:Final[int] = 1
    E_PRS_CMDID:Final[int] = 2
    E_PRS_CMDDATA:Final[int] = 3
    E_PRS_CHECKSUM1:Final[int] = 4
    E_PRS_CHECKSUM2:Final[int] = 5

    NEW_CMD_SYSTEM_SA:Final[int] = 0
    NEW_CMD_INFO_A:Final[int] = 7
    NEW_CMD_STATUS_A:Final[int] = 8
    NEW_CMD_EVENT_SA:Final[int] = 12

    protocolParseStep:int = E_PRS_CHECKHEADER1
    protocolParseBuf:List[int] = []
    protocolParseCMD:int = 0
    protocolParseDataIndex:int = 0
    protocolParseDataLen:int = 0
    protocolParseCRC:List[int] = []


    def __init__(self) -> None:

        self.notificationConfSentFast:bool = False
        self.notificationConfSentSlow:bool = False
        # holds msgType on messages split in header and payload
        self.msgType:Optional[int] = None
        self.weight:Optional[float] = None
        self.battery:Optional[int] = None
        self.firmware:Optional[Tuple[int,int,int]] = None # on connect this is set to a triple of integers, (major, minor, patch)-version
        self.unit:int = 2 # 1: kg, 2: g, 5: ounce
        self.max_weight:int = 0 # in g

    def resetProtocolParser(self) -> None:
        self.protocolParseStep = self.E_PRS_CHECKHEADER1
        self.protocolParseBuf = []
        self.protocolParseCRC = []
        self.protocolParseCMD = 0
        self.protocolParseDataLen = 0
        self.protocolParseDataIndex = 0

    def acaiaProtocolParser(self, write:Callable[[Optional[bytes]],None], dataIn) -> None:
        for c_in in dataIn:
            if self.protocolParseStep==self.E_PRS_CHECKHEADER1:
                if c_in == self.HEADER1:
                    self.protocolParseStep=self.E_PRS_CHECKHEADER2
            elif self.protocolParseStep == self.E_PRS_CHECKHEADER2:
                if c_in == self.HEADER2:
                    self.protocolParseStep=self.E_PRS_CMDID
                else:
                    self.resetProtocolParser()
            elif self.protocolParseStep == self.E_PRS_CMDID:
                self.protocolParseCMD=c_in
                # In these commands the data len is determined by the next byte, so assign 255
                if self.protocolParseCMD == self.NEW_CMD_SYSTEM_SA:
                    self.protocolParseDataLen=255
                elif self.protocolParseCMD == self.NEW_CMD_INFO_A:
                    self.protocolParseDataLen = 255
                elif self.protocolParseCMD == self.NEW_CMD_STATUS_A:
                    self.protocolParseDataLen = 255
                elif self.protocolParseCMD == self.NEW_CMD_EVENT_SA:
                    self.protocolParseDataLen = 255
                self.protocolParseStep = self.E_PRS_CMDDATA
            elif self.protocolParseStep == self.E_PRS_CMDDATA:
                if self.protocolParseDataIndex==0 and self.protocolParseDataLen==255:
                    self.protocolParseDataLen = c_in
                self.protocolParseBuf.append(c_in)
                self.protocolParseDataIndex+=1

                if self.protocolParseDataIndex==self.protocolParseDataLen:
                    self.protocolParseStep=self.E_PRS_CHECKSUM1
                if self.protocolParseDataIndex > 20:
                    self.resetProtocolParser()
            elif self.protocolParseStep == self.E_PRS_CHECKSUM1:
                self.protocolParseCRC.append(c_in)
                self.protocolParseStep = self.E_PRS_CHECKSUM2
            elif self.protocolParseStep == self.E_PRS_CHECKSUM2:
                self.protocolParseCRC.append(c_in)
                cal_crc=self.crc(self.protocolParseBuf)
                if cal_crc[0] == self.protocolParseCRC[0] and cal_crc[1] == self.protocolParseCRC[1]:
                    self.msgType=self.protocolParseCMD
                    data = self.protocolParseBuf[:] # copy buffer
                    self.resetProtocolParser() # reset buffer already before parseScaleData() as it might hang
                    # when protocol parsing success, call original data parser
                    self.parseScaleData(write, self.msgType, bytes(data))
                    self.msgType = None  # message consumed completely

                self.resetProtocolParser()


    def reset(self):
        self.__init__() # type: ignore # pylint: disable=unnecessary-dunder-call

    # return a bytearray of len 2 containing the even and odd CRCs over the given payload
    @staticmethod
    def crc(payload:Union[bytes,List[int]]) -> bytes:
        cksum1 = 0
        cksum2 = 0
        for i, _ in enumerate(payload):
            if (i % 2) == 0:
                cksum1 = (cksum1 + payload[i]) & 0xFF
            else:
                cksum2 = (cksum2 + payload[i]) & 0xFF
        return bytes([cksum1,cksum2])

    # constructs message bytearray of the given type (int) and payload (bytearray) by adding headers and CRCs
    def message(self, tp:int, payload:bytes) -> bytes:
        return bytes([self.HEADER1,self.HEADER2,tp]) + payload + self.crc(payload)

    def sendMessage(self, write:Callable[[Optional[bytes]],None], tp:int , payload:bytes) -> None:
        msg = self.message(tp,payload)
        write(msg)

    # should be send every 3-5sec
    def sendHeartbeat(self, write:Callable[[Optional[bytes]],None]) -> None:
        self.sendMessage(write, self.MSG_SYSTEM, b'\x02\x00')

    def sendStop(self, write:Callable[[Optional[bytes]],None]) -> None:
        self.sendMessage(write,self.MSG_SYSTEM,b'\x00\x00')

    def sendTare(self, write:Callable[[Optional[bytes]],None]) -> None:
        self.sendMessage(write,self.MSG_TARE,b'\x00')

    def sendTimerCommand(self, write:Callable[[Optional[bytes]],None], cmd:bytes) -> None:
        self.sendMessage(write, self.MSG_TIMER, b'\x00' + cmd)

    def sendId(self, write:Callable[[Optional[bytes]],None]) -> None:
        self.sendMessage(write,self.MSG_IDENTIFY,b'\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d\x2d')
        # non-legacy id message
        # self.sendMessage(write,self.MSG_IDENTIFY,b'\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x31\x32\x33\x34')

    def sendEvent(self, write:Callable[[Optional[bytes]],None], payload:bytes) -> None:
        self.sendMessage(write, self.MSG_EVENT, bytes([len(payload)+1]) + payload)

    # configure notifications
    def confNotificationsSlow(self, write:Callable[[Optional[bytes]],None]) -> None:
        _log.debug('confNotificationsSlow(_)')
        self.notificationConfSentSlow = True
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

    def confNotificationsFast(self, write:Callable[[Optional[bytes]],None]) -> None:
        _log.debug('confNotificationsFast(_)')
        self.notificationConfSentFast = True
        self.sendEvent(write,
            bytes([ # pairs of key/setting
                    0,  # weight id
                    1,  # 0, 1, 3, 5, 7, 15, 31, 63, 127  # weight argument (speed of notifications in 1/10 sec)
                       # 5 or 7 seems to be good values for this app in Artisan
#                    1,   # battery id
#                    255, #2,  # battery argument (if 0 : fast, 1 : slow)
#                    2,  # timer id
#                    255, #5,  # timer argument
#                    3,  # key (not used)
#                    255, #4   # setting (not used)
                ])
                )

    def parseInfo(self, data:bytes) -> None:
        _log.debug('parseInfo(_)')
#        if len(data)>1:
#            print(data[1])
        if len(data)>4:
            self.firmware = (data[2],data[3],data[4])
            _log.debug('firmware: %s', self.firmware)
            #print("{}.{}.{}".format(self.firmware[0],self.firmware[1],self.firmware[2]))
        # passwd_set
#        if len(data)>5:
#            print(data[5])
#        if len(data)>6:
#            print(data[6])

    # returns length of consumed data or -1 on error
    def parseWeightEvent(self, payload:bytes) -> int:
        if len(payload) < self.EVENT_WEIGHT_LEN:
            return -1
        # first 4 bytes encode the weight as unsigned long
        value:float = ((payload[3] & 0xff) << 24) + \
            ((payload[2] & 0xff) << 16) + ((payload[1] & 0xff) << 8) + (payload[0] & 0xff)

        div = payload[4]

        if div == 1:
            value /= 10
        elif div == 2:
            value /= 100
        elif div == 3:
            value /= 1000
        elif div == 4:
            value /= 10000

        # convert received weight data to g
        if self.unit == 1: # kg
            value = value * 1000
        elif self.unit == 5: # oz
            value = value * 28.3495

        #stable = (payload[5] & 0x01) != 0x01

        # if 2nd bit of payload[5] is set, the reading is negative
        if (payload[5] & 0x02) == 0x02:
            value *= -1

        # if value is fresh and reading is stable
        if value != self.weight: # and stable:
            self.weight = value
#            _log.debug("new weight: %s", self.weight)

        return self.EVENT_WEIGHT_LEN

    def parseBatteryEvent(self, payload:bytes) -> int:
#        _log.debug("parseBatteryEvent(_)")
        if len(payload) < self.EVENT_BATTERY_LEN:
            return -1
        b = payload[0]
        if 0 <= b <= 100:
            self.battery = int(payload[0])
            #print("bat","{}%".format(self.battery))
            _log.debug('battery: %s', self.battery)
        return self.EVENT_BATTERY_LEN

    def parseTimerEvent(self, payload:bytes) -> int:
        if len(payload) < self.EVENT_TIMER_LEN:
            return -1
#            print("minutes",payload[0])
#            print("seconds",payload[1])
#            print("mseconds",payload[2])
        value = ((payload[0] & 0xff) * 60) + payload[1] + payload[2] / 10.
        _log.debug('parseTimerEvent(_): %sm%s%sms, %s',payload[0],payload[1],payload[2], value)
        return self.EVENT_TIMER_LEN

    def parseAckEvent(self, payload:bytes) -> int:
        if len(payload) < self.EVENT_ACK_LEN:
            return -1
        return self.EVENT_ACK_LEN

    def parseKeyEvent(self, payload:bytes) -> int:
        _log.debug('parseKeyEvent(_)')
        if len(payload) < self.EVENT_KEY_LEN:
            return -1
        return self.EVENT_KEY_LEN

    def parseScaleEvent(self, payload:bytes, write:Callable[[Optional[bytes]],None]) -> int:
        if payload and len(payload) > 0:
            event = payload[1]
            payload = payload[2:]
            val = -1
            if event == self.EVENT_WEIGHT:
                val = self.parseWeightEvent(payload)
                if not self.notificationConfSentSlow:
                    # after receiving the first weight quick,
                    # we slow down the weight notificatinos
                    self.confNotificationsSlow(write)
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
            return val + 1
        return -1

    def parseScaleEvents(self, payload:bytes, write:Callable[[Optional[bytes]],None]) -> None:
        if payload and len(payload) > 0:
            pos = self.parseScaleEvent(payload, write)
            if pos > -1:
                self.parseScaleEvents(payload[pos+1:], write)

    def parseStatus(self, payload:bytes) -> None:
        _log.debug('parseStatus(_,_)')

        # battery level (7 bits of first byte) + TIMER_START (1bit)
        if payload and len(payload) > 0:
            self.battery = int(payload[1] & ~(1 << 7))
            _log.debug('battery: %s%%', self.battery)
            #print("bat","{}%".format(self.battery))
        # unit (7 bits of second byte) + CD_START (1bit)
        if payload and len(payload) > 1:
            self.unit = int(payload[2] & 0x7F)
            _log.debug('unit: %s', self.unit)

        # mode (7 bits of third byte) + tare (1bit)
        # sleep (4th byte), 0:off, 1:5sec, 2:10sec, 3:20sec, 4:30sec, 5:60sec
        # key disabled (5th byte), touch key setting 0: off , 1:On
        # sound (6th byte), beep setting 0 : off 1: on
        # resolution (7th byte), 0 : default, 1 : high
        # max weight (8th byte)
        if payload and len(payload) > 7:
            self.max_weight = (payload[7] + 1) * 1000
            _log.debug('max_weight: %s', self.max_weight)

    def parseScaleData(self, write:Callable[[Optional[bytes]],None], msgType:int, data:bytes) -> None:
        if msgType == self.MSG_INFO:
            self.parseInfo(data)
            if not self.notificationConfSentFast:
                self.sendId(write)
        elif msgType == self.MSG_STATUS:
            self.parseStatus(data)
            if not self.notificationConfSentFast:
                # we configure the scale to receive the initial
                # weight notification as fast as possible
                self.confNotificationsFast(write)
        elif msgType == self.MSG_EVENT:
            self.parseScaleEvents(data, write)

    # returns None or new weight data as first result and
    # None or new battery level as second result
    def processData(self, write:Callable[[Optional[bytes]],None], data:bytes) -> Tuple[Optional[float], Optional[int]]:

        old_weight = self.weight
        old_battery = self.battery
        self.acaiaProtocolParser(write, data)

        w = None if old_weight == self.weight else self.weight
        b = None if old_battery == self.battery else self.battery
        return w,b
