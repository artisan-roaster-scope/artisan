#!/usr/bin/env python3

import time, random
from struct import unpack
from multiprocessing import Pipe
import threading
from platform import system
import usb.core
import usb.util


class AillioR1:
    AILLIO_VID = 0x0483
    AILLIO_PID = 0x5741
    AILLIO_PID_REV3 = 0xa27e
    AILLIO_ENDPOINT_WR = 0x3
    AILLIO_ENDPOINT_RD = 0x81
    AILLIO_INTERFACE = 0x1
    AILLIO_CONFIGURATION = 0x1
    AILLIO_DEBUG = 1
    AILLIO_CMD_INFO1 = [0x30, 0x02]
    AILLIO_CMD_INFO2 = [0x89, 0x01]
    AILLIO_CMD_STATUS1 = [0x30, 0x01]
    AILLIO_CMD_STATUS2 = [0x30, 0x03]
    AILLIO_CMD_PRS = [0x30, 0x01, 0x00, 0x00]
    AILLIO_CMD_HEATER_INCR = [0x34, 0x01, 0xaa, 0xaa]
    AILLIO_CMD_HEATER_DECR = [0x34, 0x02, 0xaa, 0xaa]
    AILLIO_CMD_FAN_INCR = [0x31, 0x01, 0xaa, 0xaa]
    AILLIO_CMD_FAN_DECR = [0x31, 0x02, 0xaa, 0xaa]
    AILLIO_STATE_OFF = 0x00
    AILLIO_STATE_PH = 0x02
    AILLIO_STATE_CHARGE = 0x04
    AILLIO_STATE_ROASTING = 0x06
    AILLIO_STATE_COOLING = 0x08
    AILLIO_STATE_SHUTDOWN = 0x09

    def __init__(self, debug=True):
        self.simulated = False
        self.AILLIO_DEBUG = debug
        self.__dbg('init')
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
        self.r1state = 0
        self.worker_thread = None
        self.worker_thread_run = True
        self.roast_number = -1
        self.fan_rpm = 0

    def __del__(self):
        if not self.simulated:
            self.__close()

    def __dbg(self, msg):
        if self.AILLIO_DEBUG and self.simulated != True:
            try:
                print('AillioR1: ' + msg)
            except IOError:
                pass

    def __open(self):
        if self.simulated:
            return
        if self.usbhandle is not None:
            return
        self.usbhandle = usb.core.find(idVendor=self.AILLIO_VID,
                                       idProduct=self.AILLIO_PID)
        if self.usbhandle is None:
            self.usbhandle = usb.core.find(idVendor=self.AILLIO_VID,
                                           idProduct=self.AILLIO_PID_REV3)
        if self.usbhandle is None:
            raise IOError("not found or no permission")
        self.__dbg('device found!')
        if not system().startswith("Windows"):
            if self.usbhandle.is_kernel_driver_active(self.AILLIO_INTERFACE):
                try:
                    self.usbhandle.detach_kernel_driver(self.AILLIO_INTERFACE)
                except Exception:
                    self.usbhandle = None
                    raise IOError("unable to detach kernel driver")
        try:
            config = self.usbhandle.get_active_configuration()
            if config.bConfigurationValue != self.AILLIO_CONFIGURATION:
                self.usbhandle.set_configuration(configuration=self.AILLIO_CONFIGURATION)
        except Exception:
            self.usbhandle = None
            raise IOError("unable to configure")

        try:
            usb.util.claim_interface(self.usbhandle, self.AILLIO_INTERFACE)
        except Exception:
            self.usbhandle = None
            raise IOError("unable to claim interface")
        self.__sendcmd(self.AILLIO_CMD_INFO1)
        reply = self.__readreply(32)
        sn = unpack('h', reply[0:2])[0]
        firmware = unpack('h', reply[24:26])[0]
        self.__dbg('serial number: ' + str(sn))
        self.__dbg('firmware version: ' + str(firmware))
        self.__sendcmd(self.AILLIO_CMD_INFO2)
        reply = self.__readreply(36)
        self.roast_number = unpack('>I', reply[27:31])[0]
        self.__dbg('number of roasts: ' + str(self.roast_number))
        self.parent_pipe, self.child_pipe = Pipe()
        self.worker_thread = threading.Thread(target=self.__updatestate,
                                              args=(self.child_pipe,))
        self.worker_thread.start()

    def __close(self):
        if self.simulated:
            return
        if self.usbhandle is not None:
            try:
                usb.util.release_interface(self.usbhandle,
                                           self.AILLIO_INTERFACE)
                usb.util.dispose_resources(self.usbhandle)
            except Exception:
                pass
            self.usbhandle = None

        if self.worker_thread:
            self.worker_thread_run = False
            self.worker_thread.join()
            self.parent_pipe.close()
            self.child_pipe.close()
            self.worker_thread = None

    def get_roast_number(self):
        self.__getstate()
        return self.roast_number
    
    def get_bt(self):
        self.__getstate()
        return self.bt

    def get_dt(self):
        self.__getstate()
        return self.dt

    def get_heater(self):
        self.__dbg('get_heater')
        self.__getstate()
        return self.heater

    def get_fan(self):
        self.__dbg('get_fan')
        self.__getstate()
        return self.fan

    def get_fan_rpm(self):
        self.__dbg('get_fan_rpm')
        self.__getstate()
        return self.fan_rpm

    def get_drum(self):
        self.__getstate()
        return self.drum

    def get_voltage(self):
        self.__getstate()
        return self.voltage

    def get_bt_ror(self):
        self.__getstate()
        return self.bt_ror

    def get_exit_temperature(self):
        self.__getstate()
        return self.exitt

    def get_state_string(self):
        self.__getstate()
        return self.state_str

    def get_state(self):
        self.__getstate()
        return self.r1state

    def set_heater(self, value):
        self.__dbg('set_heater ' + str(value))
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
            for _ in range(d):
                self.parent_pipe.send(self.AILLIO_CMD_HEATER_DECR)
        else:
            for _ in range(d):
                self.parent_pipe.send(self.AILLIO_CMD_HEATER_INCR)
        self.heater = value
        
    def set_fan(self, value):
        self.__dbg('set_fan ' + str(value))
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
            for _ in range(0, d):
                self.parent_pipe.send(self.AILLIO_CMD_FAN_DECR)
        else:
            for _ in range(0, d):
                self.parent_pipe.send(self.AILLIO_CMD_FAN_INCR)
        self.fan = value
        
    def set_drum(self, value):
        self.__dbg('set_drum ' + str(value))
        value = int(value)
        if value < 1:
            value = 1
        elif value > 9:
            value = 9
        self.parent_pipe.send([0x32, 0x01, value, 0x00])
        self.drum = value
        
    def prs(self):
        self.__dbg('PRS')
        self.parent_pipe.send(self.AILLIO_CMD_PRS)

    def __updatestate(self, p):
        while self.worker_thread_run:
            state1 = state2 = []
            try:
                self.__dbg('updatestate')
                self.__sendcmd(self.AILLIO_CMD_STATUS1)
                state1 = self.__readreply(64)
                self.__sendcmd(self.AILLIO_CMD_STATUS2)
                state2 = self.__readreply(64)
            except Exception:
                pass
            if p.poll():
                cmd = p.recv()
                self.__sendcmd(cmd)
            if len(state1) + len(state2) == 128:
                p.send(state1 + state2)
            time.sleep(0.1)

    def __getstate(self):
        self.__dbg('getstate')
        if self.simulated:
            if random.random() > 0.05:
                return
            self.bt += random.random()
            self.bt_ror += random.random()
            self.dt += random.random()
            self.exitt += random.random()
            self.fan = random.random() * 10
            self.heater = random.random() * 8
            self.drum = random.random() * 8
            self.irt = random.random()
            self.pcbt = random.random()
            self.fan_rpm += random.random()
            self.voltage = 240
            self.coil_fan = 0
            self.coil_fan2 = 0
            self.pht = 0
            self.r1state = self.AILLIO_STATE_ROASTING
            self.state_str = "roasting"
            return
        self.__open()
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
            self.r1state = state[29]
            self.irt = round(unpack('f', state[32:36])[0], 1)
            self.pcbt = round(unpack('f', state[36:40])[0], 1)
            self.fan_rpm = unpack('h', state[44:46])[0]
            self.voltage = unpack('h', state[48:50])[0]
            self.coil_fan = round(unpack('i', state[52:56])[0], 1)
            self.__dbg('BT: ' + str(self.bt))
            self.__dbg('BT RoR: ' + str(self.bt_ror))
            self.__dbg('DT: ' + str(self.dt))
            self.__dbg('exit temperature ' + str(self.exitt))
            self.__dbg('PCB temperature: ' + str(self.irt))
            self.__dbg('IR temperature: ' + str(self.pcbt))
            self.__dbg('voltage: ' + str(self.voltage))
            self.__dbg('coil fan: ' + str(self.coil_fan))
            self.__dbg('fan: ' + str(self.fan))
            self.__dbg('heater: ' + str(self.heater))
            self.__dbg('drum speed: ' + str(self.drum))
            self.__dbg('time: ' + str(self.minutes) + ':' + str(self.seconds))

        state = state[64:]
        self.coil_fan2 = round(unpack('i', state[32:36])[0], 1)
        self.pht = unpack('B', state[40:41])[0]
        self.__dbg('pre-heat temperature: ' + str(self.pht))
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
        elif self.r1state == self.AILLIO_STATE_SHUTDOWN:
            self.state_str = "shutdown"
        self.__dbg('state: ' + self.state_str)
        self.__dbg('second coil fan: ' + str(self.coil_fan2))

    def __sendcmd(self, cmd):
        self.__dbg('sending command: ' + str(cmd))
        self.usbhandle.write(self.AILLIO_ENDPOINT_WR, cmd)

    def __readreply(self, length):
        return self.usbhandle.read(self.AILLIO_ENDPOINT_RD, length)


if __name__ == "__main__":
    R1 = AillioR1(debug=True)
    while True:
        R1.get_heater()
        time.sleep(0.1)
