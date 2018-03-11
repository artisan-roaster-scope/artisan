#!/usr/bin/env python

import usb.core
import usb.util
import time
from struct import pack, unpack
from multiprocessing import Process, Pipe

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
    AILLIO_CMD_HEATER_INCR = [0x34, 0x01, 0xaa, 0xaa]
    AILLIO_CMD_HEATER_DECR = [0x34, 0x02, 0xaa, 0xaa]
    AILLIO_CMD_FAN_INCR = [0x31, 0x01, 0xaa, 0xaa]
    AILLIO_CMD_FAN_DECR = [0x31, 0x02, 0xaa, 0xaa]
    AILLIO_STATE_OFF = 0x00
    AILLIO_STATE_PH  = 0x02
    AILLIO_STATE_CHARGE = 0x04
    AILLIO_STATE_ROASTING = 0x06
    AILLIO_STATE_COOLING = 0x08

    def __init__(self, debug=True):
        self.AILLIO_DEBUG = debug
        self.__dbg__('init')
        self.usbhandle = None
        self.bt = 0
        self.dt = 0
        self.heater = 0
        self.fan = 0
        self.bt_ror = 0
        self.drum = 0
        self.voltage = 0
        self.exitt = 0
        self.state_str = ""
        self.p = None

    def __del__(self):
        self.__close__()

    def __dbg__(self, msg):
        if self.AILLIO_DEBUG:
            print('AillioR1: ' + msg)

    def __open__(self):
        if self.usbhandle is not None:
            return
        self.usbhandle = usb.core.find(idVendor=self.AILLIO_VID,
                                       idProduct=self.AILLIO_PID)
        if self.usbhandle is None:
            raise IOError("not found or no permission")
        self.__dbg__('device found!')
        if self.usbhandle.is_kernel_driver_active(self.AILLIO_INTERFACE):
            try:
                self.usbhandle.detach_kernel_driver(self.AILLIO_INTERFACE)
            except:
                raise IOError("unable to detach kernel driver")
        try:
            self.usbhandle.set_configuration(configuration=1)
        except:
            raise IOError("unable to configure")

        try:
            usb.util.claim_interface(self.usbhandle, self.AILLIO_INTERFACE)
        except:
            raise IOError("unable to claim interface")
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
        self.parent_pipe, self.child_pipe = Pipe()
        self.p = Process(target=self.__updatestate__, args=(self.child_pipe,))
        self.p.start()
        
    def __close__(self):
        if self.usbhandle is not None:
            try:
                usb.util.release_interface(self.usbhandle,
                                           self.AILLIO_INTERFACE)
                usb.util.dispose_resources(self.usbhandle)
            except:
                pass
            self.usbhandle = None

        if self.p:
            self.p.terminate()
            self.parent_pipe.close()
            self.child_pipe.close()

    def get_bt(self):
        self.__getstate__()
        return self.bt

    def get_dt(self):
        self.__getstate__()
        return self.dt

    def get_heater(self):
        self.__dbg__('get_heater')
        self.__getstate__()
        return self.heater
    
    def get_fan(self):
        self.__dbg__('get_fan')
        self.__getstate__()
        return self.fan

    def get_drum(self):
        self.__getstate__()
        return self.drum
    
    def get_voltage(self):
        self.__getstate__()
        return self.voltage

    def get_bt_ror(self):
        self.__getstate__()
        return self.bt_ror

    def get_exit_temperature(self):
        self.__getstate__()
        return self.exitt

    def get_state_string(self):
        self.__getstate__()
        return self.state_str

    def set_heater(self, value):
        self.__dbg__('set_heater ' + str(value))
        value = int(value)
        if value < 0:
            value = 0
        elif value > 9:
            value = 9
        h = self.get_heater()
        d = abs(h - value)
        if d <= 0:
            return
        if d > 9:
            d = 9
        if h > value:
            for i in range(d):
                self.parent_pipe.send(self.AILLIO_CMD_HEATER_DECR)
        else:
            for i in range(d):
                self.parent_pipe.send(self.AILLIO_CMD_HEATER_INCR)

    def set_fan(self, value):
        self.__dbg__('set_fan ' + str(value))
        value = int(value)
        if value < 1:
            value = 1
        elif value > 12:
            value = 12 
        f = self.get_fan()
        d = abs(f - value)
        if d <= 0:
            return
        if d > 11:
            d = 11
        if f > value:
            for i in range(0, d+1):
                self.parent_pipe.send(self.AILLIO_CMD_FAN_DECR)
        else:
            for i in range(0, d+1):
                self.parent_pipe.send(self.AILLIO_CMD_FAN_INCR)
 

    def set_drum(self, value):
        self.__dbg__('set_drum ' + str(value))
        if value < 1:
            value = 1
        elif value > 9:
            value = 9 
        self.parent_pipe.send([0x32, 0x01, value, 0x00])

    def prs(self):
        self.__dbg__('PRS')
        self.parent_pipe.send(self.AILLIO_CMD_PRS)

    def __updatestate__(self, p):
        while True:
            self.__dbg__('updatestate')
            self.__sendcmd__(self.AILLIO_CMD_STATUS1)
            state1 = self.__readreply__(64)
            self.__sendcmd__(self.AILLIO_CMD_STATUS2)
            state2 = self.__readreply__(64)
            if p.poll():
                cmd = p.recv()
                self.__sendcmd__(cmd)
            if len(state1) + len(state2) == 128:
                p.send(state1 + state2)
            time.sleep(0.1)
        pipe.close()

        
    def __getstate__(self):
        self.__open__()
        self.__dbg__('getstate')
        if not self.parent_pipe.poll():
            return
        state = self.parent_pipe.recv()
        valid = state[41]
        # Heuristic to find out if the data is valid
        # It looks like we get a different message every 15 seconds
        # when we're not roasting.  Ignore this message for now.
        if valid == 10:
            self.bt = round(unpack('f', state[0:4])[0], 1)
            self.bt_ror = round(unpack('f', state[4:8])[0], 1)
            self.dt = round(unpack('f', state[8:12])[0], 1)
            self.exitt = round(unpack('f', state[16:20])[0], 1)
            self.minutes = state[24]
            self.seconds = state[25]
            self.fan = state[26]
            self.heater = state[27]
            self.drum = state[28]
            self.irt = round(unpack('f', state[32:36])[0], 1)
            self.pcbt = round(unpack('f', state[36:40])[0], 1)
            self.fan_rpm = unpack('h', state[44:46])[0]
            self.voltage = unpack('h', state[48:50])[0]
            self.coil_fan = round(unpack('i', state[52:56])[0], 1)
            self.__dbg__('BT: ' + str(self.bt))
            self.__dbg__('BT RoR: ' + str(self.bt_ror))
            self.__dbg__('DT: ' + str(self.dt))
            self.__dbg__('exit temperature ' + str(self.exitt))
            self.__dbg__('PCB temperature: ' + str(self.irt))
            self.__dbg__('IR temperature: ' + str(self.pcbt))
            self.__dbg__('voltage: ' + str(self.voltage))
            self.__dbg__('coil fan: ' + str(self.coil_fan))
            self.__dbg__('fan: ' + str(self.fan))
            self.__dbg__('heater: ' + str(self.heater))
            self.__dbg__('drum speed: ' + str(self.drum))
            self.__dbg__('time: ' + str(self.minutes) + ':' + str(self.seconds))

        state = state[64:]
        self.coil_fan2 = round(unpack('i', state[32:36])[0], 1)
        self.pht = unpack('B', state[40:41])[0]
        self.r1state = unpack('B', state[42:43])[0]
        self.__dbg__('pre-heat temperature: ' + str(self.pht))
        if self.r1state == self.AILLIO_STATE_OFF:
            self.state_str = "off"
        elif self.r1state == self.AILLIO_STATE_PH:
            self.state_str = "pre-heating to " + str(self.pht) + "C"
        elif self.r1state == self.AILLIO_STATE_CHARGE:
            self.state_str = "charge"
        elif self.r1state == self.AILLIO_STATE_ROASTING:
            self.state_str = "roasting"
        elif self.r1state == self.AILLIO_STATE_COOLING:
            self.state_str = "cooling"
        self.__dbg__('state: ' + self.state_str)
        self.__dbg__('second coil fan: ' + str(self.coil_fan2))


    def __sendcmd__(self, cmd):
        self.__dbg__('sending command: ' + str(cmd))
        self.usbhandle.write(self.AILLIO_ENDPOINT_WR, cmd)

    def __readreply__(self, length):
        return self.usbhandle.read(self.AILLIO_ENDPOINT_RD, length)


if __name__ == "__main__":
    R1 = AillioR1(debug=True)
    while True:
        R1.get_heater()
        time.sleep(0.1)
