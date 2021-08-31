#!/usr/bin/env python
#####################################################################################
# COMM TEST PROGRAM FOR CENTER 309 DATA LOGGER  (www.centertek.com)
# This program shows how to read Temp from a CENTER 309 thermometer data logger using T1 and T2
# USAGE: edit "COMx" port in temperature() at line 58, plug T1 and T2 thermocouples
# ##################################################################################################

# REQUIREMENTS
# python 2.6: http://www.python.org/ftp/python/2.6.6/python-2.6.6.msi
# pyserial for python 2.6: http://sourceforge.net/projects/pyserial/files/pyserial/2.6/
# javacomm: http://www.xpl4java.org/xPL4Java/javacomm.html
# Java JDK or JRE:  http://java.sun.com/javase/downloads/index.jsp


import serial
import time
import binascii
import platform

platf = str(platform.system())


def main():
    T1 = 0.0
    T2 = 0.0
    mode = "F"
    delay = 2            # set time between each reading in seconds

    print "Press <CTRL 'C'> to stop"
    #Read temperature in a forever loop to check operation    
    while True:    
        T1,T2,T3,T4,mode = temperature()                              # read T1,T2, and mode (C or F)
        string = "T1 = %.1f%s T2 = %.1f%s T3 = %.1f%s T4 = %.1f%s"%(T1,mode,T2,mode,T3,mode,T4,mode)    # format output string
        print string
        time.sleep(delay)                    # wait delay before next reading in while loop


def temperature():
##    
##    command = "\x4B" returns 4 bytes but unknown meaning
##    command = "\x41" returns 45 bytes (8x5 + 5 = 45) as follows:
##    
##    "\x02\x80\xYY\xYY\xYY\xYY\xYY\xAA"  \x80 means "Celsi" (if \x00 then "Faren") YYs unknown
##    "\xAA\xBB\xBB\xCC\xCC\xDD\xDD\x00"  Temprerature T1 = AAAA, T2=BBBB, T3= CCCC, T4 = DDDD
##    "\x00\x00\x00\x00\x00\x00\x00\x00"  unknown (possible data containers but found empty)
##    "\x00\x00\x00\x00\x00\x00\x00\x00"  unknown
##    "\x00\x00\x00\x00\x00\x00\x00\x00"  unknown
##    "\x00\x00\x00\x0E\x03"              The byte r[43] \x0E changes depending on what thermocouple(s) are connected.
##                                        If T1 thermocouple connected alone, then r[43]  = \x0E = 14
##                                        If T2 thermocouple connected alone, then r[43]  = \x0D = 13
##                                        If T1 + T2 thermocouples connected, then r[43]  = \x0C = 12
##                                        If T3 thermocouple connected alone, then r[43]  = \x0B = 11
##                                        If T4 thermocouple connected alone, then r[43]  = \x07 = 7
##                                        Note: Print r[43] if you want to find other connect-combinations
##    
##    
    serCENTER = None
    try:
        ##########   CHANGE HERE  "COMx" port to match your computer   ################################
        if platf == 'Windows':
            port = "COM13"
        else:
            port = "/dev/cu.SLAB_USBtoUART"
        serCENTER = serial.Serial(port, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
        
        command = "\x41"                  #this comand makes the meter answer back with 45 bytes
        serCENTER.write(command)
        r = serCENTER.read(45)
        serCENTER.close()
        
        if len(r) != 45:
            #Bad RX data
            return 0.,0.,"RX failed"
            

        #check that T1 and T2 are both plugged in        
        #if int(binascii.hexlify(r[43]),16) != 12:
            #T1 + T2 not plugged in
        #    return 0.,0.,"plug T1&T2!"

        mode = "X"
        checkmode = int(binascii.hexlify(r[1]),16)
        if checkmode == 128:
            mode = "C"          #Celsius
        elif checkmode == 0:
            mode = "F"          #Farenheit
        
        T1 = int(binascii.hexlify(r[7] + r[8]),16)
        T2 = int(binascii.hexlify(r[9] + r[10]),16)
        T3 = int(binascii.hexlify(r[11] + r[12]),16)        #aditional reference left that shows how to to read T3
        T4 = int(binascii.hexlify(r[13] + r[14]),16)        #aditional reference left that shows how to to read T4
        
        return T1/10.,T2/10.,T3/10.,T4/10.,mode
    
    except serial.SerialException, e:
        print "Serial port error" + str(e)
        
    finally:
        if serCENTER:
            serCENTER.close()

  
main()
