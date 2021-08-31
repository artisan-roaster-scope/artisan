#!/usr/bin/env python

import serial
import time
import binascii


import sys
        
if sys.version < '3':
    def stringp(x):
        return isinstance(x, basestring)
    def uchr(x):
        return unichr(x)
    def o(x): # converts char to byte
        return ord(x)
    def u(x): # convert to unicode string
        return unicode(x)
    def d(x):
        if x is not None:
            try:
                return codecs.unicode_escape_decode(x)[0]
            except Exception:
                return x
        else:
            return None
    def encodeLocal(x):
        if x is not None:
            return codecs.unicode_escape_encode(unicode(x))[0]
        else:
            return None
    def hex2int(h1,h2=""):
        return int(binascii.hexlify(h1+h2),16)
    def str2cmd(s):
        return s
    def cmd2str(c):
        return c
else:
    def stringp(x):
        return isinstance(x, str)
    def uchr(x):
        return chr(x)
    def o(x): # converts char to byte
        return x
    def u(x): # convert to unicode string
        return str(x)
    def d(x):
        if x is not None:
            return codecs.unicode_escape_decode(x)[0]
        else:
            return None
    def encodeLocal(x):
        if x is not None:
            return codecs.unicode_escape_encode(str(x))[0].decode("utf8")
        else:
            return None
    def hex2int(h1,h2=None):
        if h2:
            return int(h1*256 + h2)
        else:
            return int(h1)
    def str2cmd(s):
        return bytes(s,"ascii")
    def cmd2str(c):
        return str(c,"latin1")



def main():
    T1 = 0.0
    T2 = 0.0
    delay = 1            # set time between each reading in seconds

    port = "/dev/cu.usbserial-DA00PZ8J" # "FT230X Basic UART"
    serCENTER = serial.Serial(port, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1)

    #Read temperature in a forever loop to check operation    
    i = 0
    while True:
        print("--")
        print(i)
        T1,T2 = temperature(serCENTER)
        string = "T1 = %.1f T2 = %.1f"%(T1,T2)    # format output string
        print(string)
        time.sleep(delay)                    # wait delay before next reading in while loop
        i = i + 1

#def calc_checksum(s):
#    sum = 0
#    for c in s:
#        sum += ord(c)
#    sum = -(sum % 256)
#    return '%2X' % (sum & 0xFF)
    
def calc_checksum(s):
    return '%2X' % (-(sum(ord(c) for c in s) % 256) & 0xFF)
    
def temperature(serCENTER):
    print("temperature()")
    try:
        
#        command = "\x41"                  #this comand makes the meter answer back with 45 bytes
#        serCENTER.write(command)
        if not serCENTER.isOpen():
            serCENTER.open()

        serCENTER.flushInput()
        serCENTER.flushOutput()
        r = serCENTER.read(36)
#        serCENTER.close()
        print(len(r),r)

        
        if len(r) != 36:
            print("bad len data",len(r))
            if serCENTER.isOpen():
                serCENTER.close()
            return 0,0
        else:
            P0 = hex2int(r[0])
            P1 = hex2int(r[1])
            chksum = sum([hex2int(c) for c in r[:35]]) & 0xFF 
            P35 = hex2int(r[35])
            if P0 != 165 or P1 != 150 or P35 != chksum:
                print("bad rx data",P0,P1,P35,chksum)
                if serCENTER.isOpen():
                    serCENTER.close()
                return 0,0
            else:
                # check first two bytes and checksum and error (P31)
                print("master: ", hex2int(r[2]))
                print("slave: ", hex2int(r[3]))
                print("version: ", hex2int(r[4]))
                print("heater: ", hex2int(r[10]))
                print("fan1: ", hex2int(r[11]))
                print("fan2: ", hex2int(r[12]))
                T1 = hex2int(r[23],r[24]) # ET
                T2 = hex2int(r[25],r[26]) # BT
                
                # Hottop Plan
                # 1) add device "Hottop" (ET/BT)
                # 2) add device  "Hottop Heater/Fan" (providing main heater and fan setting)
                # print version on connect
                # if solenoid changes from 0 -> 1, trigger eject event
                #   on read!
                # if EJECT is pressed in Artisan, the solenoid should be opened automatically and the roast stopped
                # slider support for
                #   - heater
                #   - main fan
                
                # "Control" Button to take control if main device is Hottop
                
                # TODO:
                # - add cooling fan action
                # - add alarm actions
                
                # Remarks:
                # - both fans (cooling and main) seem to work always in parallel (manual or USB controlled)
                #   those fans are reported as FAN2/P12 on read and can be set only via FAN2/P12
                #   FAN1/P11 seems to be always 0 on read and does not react on write commands
                # - temperatures are reported using two bytes, but the values transmitted do not allow for a
                #   decimal places as eg. 201.2C is reported as 200 and not as 2012 that could be deviced by 10 on 
                #   USB computer side. This might be a design decision, but I still wonder if this is intended.
                # - if temp > PREHEAT temperature (BT70C?),
                #    releasing the control should not just shut up the roaster completely, but
                #    activate the standard cool-down procedure for safety reasons
                #    as disconnecting USB control around 200C and just shutting down drum and fans completely
                #    could provoke a roaster fire
                
                # further control of
                #   - main motor (on/off)  => button?
                
                # on ON: drum(1)
                #    => add a command to the CONTROL button in the event table
                # on DROP:  heater(0);fan(10);drum(1);heater(0);solenoid(1);stirrer(1)
                
    
                return float(T1),float(T2)
    
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stdout)
        _, _, exc_tb = sys.exc_info()
        print(exc_tb.tb_lineno, str(e))
        return 0,0
        
#    finally:
#        if serCENTER:
#            serCENTER.close()

  
main()
