#!/usr/bin/env python

import usb1

# TODO:
#    1) Figure out the VID/PID/endpoints/ports/interface
#    2) Figure out how to communicate with the device
#    3) Figure out if we can communicate async or if we need a special process
#    4) 

class AillioR1:
    AILLIO_USB_VID = 0x0483
    AILLIO_USB_PID = 0x5781
    AILLIO_USB_ENDPOINT = 0x12
    AILLIO_USB_INTERFACE = 0x1
    AILLIO_DEBUG = 1

    def __init__(self):
        self.__dbg__('init')
        self.usbctx = usb1.USBContext()
        self.usbhandle = None

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
            self.AILLIO_USB_VID, self.AILLIO_USB_PID,
            skip_on_error=True)
        if self.usbhandle is None:
            self.__msg__('device NOT found')
            return
        self.__dbg__('device found!')
        self.usbhandle.claimInterface(self.AILLIO_USB_INTERACE)

    def __close__(self):
        if self.usbhandle is not None:
            self.usbhandle.releaseInterface(self.AILLIO_USB_INTERACE)
            self.usbhandle.close()
        
    def start(self):
        self.__open__()
        self.__dbg__('start')
        pass

    def stop(self):
        self.__open__()
        self.__dbg__('stop')
        pass

    def setstate(self, heater=None, fan=None, drum=None):
        self.__dbg__('setstate')
        pass

    def getstate(self):
        self.__dbg__('getstate')
        pass


if __name__ == "__main__":
    R1 = AillioR1()
    R1.start()
    R1.setstate()
    R1.getstate()
    R1.stop()
