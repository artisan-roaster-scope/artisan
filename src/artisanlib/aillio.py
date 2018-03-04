#!/usr/bin/env python

import usb1
import hexdump
import time
from struct import pack, unpack

class AillioR1:
    AILLIO_VID = 0x0483
    AILLIO_PID = 0x5741
    AILLIO_ENDPOINT_WR = 0x3
    AILLIO_ENDPOINT_RD = 0x81
    AILLIO_INTERFACE = 0x1
    AILLIO_DEBUG = 1
    AILLIO_CMD_INFO1 = [ 0x30, 0x02 ]
    AILLIO_CMD_INFO2 = [ 0x89, 0x01 ]
    AILLIO_CMD_STATUS1 = [ 0x30, 0x01 ]
    AILLIO_CMD_STATUS2 = [ 0x30, 0x03 ]
    AILLIO_CMD_PRS = [ 0x30, 0x01, 0x00, 0x00 ]
    AILLIO_STATE_OFF = 0x00
    AILLIO_STATE_PH  = 0x02
    AILLIO_STATE_CHARGE = 0x04
    AILLIO_STATE_ROASTING = 0x06
    AILLIO_STATE_COOLING = 0x08

    def __init__(self):
        self.__dbg__('init')
        self.usbctx = usb1.USBContext()
        self.usbhandle = None
        self.bt = 0
        self.dt = 0
        self.heater = 0
        self.fan = 0

    def __del__(self):
        self.__close__()
        self.usbctx.close()

    def __dbg__(self, msg):
        if self.AILLIO_DEBUG:
            print('AillioR1: ' + msg)

    def __msg__(self, msg):
        print('AillioR1: ' + msg)
        
    def __open__(self):
        if self.usbhandle is not None:
            return
        self.usbhandle = self.usbctx.openByVendorIDAndProductID(
            self.AILLIO_VID, self.AILLIO_PID,
            skip_on_error=True)
        if self.usbhandle is None:
            self.__msg__('device NOT found')
            return
        self.__dbg__('device found!')
        try:
            self.usbhandle.detachKernelDriver(self.AILLIO_INTERFACE)
        except:
            pass
        self.usbhandle.setConfiguration(1)
        self.usbhandle.claimInterface(self.AILLIO_INTERFACE)
        self.__sendcmd__(self.AILLIO_CMD_INFO1)
        reply = self.__readreply__(32)
        sn = unpack('h', reply[0:2])[0]
        firmware = unpack('h', reply[24:26])[0]
        self.__dbg__('serial number: ' + str(sn))
        self.__dbg__('firmware version: ' + str(firmware))
        self.__sendcmd__(self.AILLIO_CMD_INFO2)
        reply = self.__readreply__(36)
        roast_number = unpack('>I', reply[27:31])[0]
        self.__dbg__('number of roasts: ' + str(roast_number))
        
    def __close__(self):
        if self.usbhandle is not None:
            self.usbhandle.releaseInterface(self.AILLIO_INTERFACE)
            self.usbhandle.close()

    def setstate(self, heater=None, fan=None, drum=None):
        self.__dbg__('setstate')
        pass

    def get_bt(self):
        self.__getstate__()
        return self.bt

    def get_dt(self):
        self.__getstate__()
        return self.dt

    def get_heater(self):
        self.__dbg__('get_heater')
        self.__getstate__()
        if self.heater < 100:
            return 0
        elif self.heater < 300:
            return 1
        elif self.heater < 600:
            return 2
        elif self.heater < 800:
            return 3
        elif self.heater < 1250:
            return 4
        elif self.heater < 1400:
            return 5
        elif self.heater < 1600:
            return 6
        elif self.heater < 1900:
            return 7
        elif self.heater < 2000:
            return 8
        else:
            return 9

    def get_fan(self):
        self.__dbg__('get_fan')
        self.__getstate__()
        if self.fan == 0:
            return 0
        elif self.fan < 800:
            return 1
        elif self.fan < 1000:
            return 2
        elif self.fan < 1200:
            return 3
        elif self.fan < 1450:
            return 4
        elif self.fan < 1650:
            return 5
        elif self.fan < 1800:
            return 6
        elif self.fan < 2000:
            return 7
        elif self.fan < 2100:
            return 8
        elif self.fan < 2300:
            return 9
        elif self.fan < 3100:
            return 10
        elif self.fan < 3600:
            return 11
        else:
            return 12

    def get_drum(self):
        self.__getstate__()
        return self.drum
    
    def get_voltage(self):
        self.__getstate__()
        return self.voltage

    def get_dt_ror(self):
        self.__getstate__()
        return self.dt_ror

    def get_bt_ror(self):
        self.__getstate__()
        return self.bt_ror

    def __getstate__(self):
        self.__open__()
        self.__dbg__('getstate')
        self.__sendcmd__(self.AILLIO_CMD_STATUS1)
        state = self.__readreply__(64)
        valid = unpack('B', state[41:42])[0]
        # Heuristic to find out if the data is valid
        # It looks like we get a different message every 15 seconds
        # when we're not roasting.  Ignore this message for now.
        while valid != 10:
            time.sleep(1)
            self.__sendcmd__(self.AILLIO_CMD_STATUS1)
            state = self.__readreply__(64)
            valid = unpack('B', state[41:42])[0]
        self.bt = round(unpack('f', state[0:4])[0], 1)
        self.bt_ror = round(unpack('f', state[4:8])[0], 1)
        self.dt = round(unpack('f', state[8:12])[0], 1)
        self.dt_ror = round(unpack('f', state[12:16])[0], 1)
        self.pcbt = round(unpack('f', state[32:36])[0], 1)
        self.irt = round(unpack('f', state[36:40])[0], 1)
        self.seconds = unpack('h', state[42:44])[0]
        self.minutes = self.seconds / 60
        self.seconds = self.seconds % 60
        self.fan = unpack('h', state[44:46])[0]
        self.drum = 0
        self.voltage = unpack('h', state[48:50])[0]
        self.heater = unpack('H', state[50:52])[0]
        self.coil_fan = round(unpack('i', state[52:56])[0], 1)
        self.__dbg__('BT: ' + str(self.bt))
        self.__dbg__('BT RoR: ' + str(self.bt_ror))
        self.__dbg__('DT: ' + str(self.dt))
        self.__dbg__('DT RoR: ' + str(self.dt_ror))
        self.__dbg__('PCB temperature: ' + str(self.irt))
        self.__dbg__('IR temperature: ' + str(self.pcbt))
        self.__dbg__('voltage: ' + str(self.voltage))
        self.__dbg__('coil fan: ' + str(self.coil_fan))
        self.__dbg__('fan: ' + str(self.fan))
        self.__dbg__('heater: ' + str(self.heater))
        self.__dbg__('drum speed: ' + str(self.drum))
        self.__dbg__('time: ' + str(self.minutes) + ':' + str(self.seconds))

#        print "1---------------"
 #       for i in range(16, 32, 4):
  #          uk1 = round(unpack('i', state[i:i+4])[0], 1)
   #         uk2 = round(unpack('f', state[i:i+4])[0], 1)
    #        print str(i) + ': ' + hexdump.dump(state[i:i+4])
     #   print '40: ' + hexdump.dump(state[40:42])
#        print '46: ' + hexdump.dump(state[46:48])
 #       print '56: ' + hexdump.dump(state[56:60])
  #      print '60: ' + hexdump.dump(state[60:64])
        self.__sendcmd__(self.AILLIO_CMD_STATUS2)
        state = self.__readreply__(64)
        self.coil_fan2 = round(unpack('i', state[32:36])[0], 1)
        self.pht = unpack('B', state[40:41])[0]
        self.r1state = unpack('B', state[42:43])[0]
        self.__dbg__('pre-heat temperature: ' + str(self.pht))
        if self.r1state == self.AILLIO_STATE_OFF:
            self.__dbg__('state: off')
        elif self.r1state == self.AILLIO_STATE_PH:
            self.__dbg__('state: pre-heating')
        elif self.r1state == self.AILLIO_STATE_CHARGE:
            self.__dbg__('state: charge')
        elif self.r1state == self.AILLIO_STATE_ROASTING:
            self.__dbg__('state: roasting')
        elif self.r1state == self.AILLIO_STATE_COOLING:
            self.__dbg__('state: cooling')
        self.__dbg__('second coil fan: ' + str(self.coil_fan2))

    def __sendcmd__(self, cmd):
        self.__dbg__('sending command: ' + str(cmd))
        self.usbhandle.bulkWrite(self.AILLIO_ENDPOINT_WR, cmd)

    def __readreply__(self, length):
        return self.usbhandle.bulkRead(self.AILLIO_ENDPOINT_RD, length,
                                       timeout=1000)


if __name__ == "__main__":
    R1 = AillioR1()
    while True:
        R1.get_bt()
        time.sleep(1)
        print 'heater: ' + str(R1.get_heater())
