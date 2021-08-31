#!/usr/bin/env python
#####################################################################################
# COMM TEST PROGRAM FOR CENTER 306 DATA LOGGER  (www.centertek.com)
# This program shows how to read Temp from a CENTER 306 thermometer data logger using T1 and T2
# USAGE: edit "COMx" port in temperature() at line 39, plug T1 and T2 thermocouples
# ##################################################################################################

# REQUIREMENTS
# python 2.6: http://www.python.org/ftp/python/2.6.6/python-2.6.6.msi
# pyserial for python 2.6: http://sourceforge.net/projects/pyserial/files/pyserial/2.6/
# javacomm: http://www.xpl4java.org/xPL4Java/javacomm.html
# Java JDK or JRE:  http://java.sun.com/javase/downloads/index.jsp


import serial
import time
import binascii


def main():
    T1 = 0.0
    T2 = 0.0
    delay = 2            # set time between each reading in seconds

    print "Press <CTRL 'C'> to stop"
    #Read temperature in a forever loop to check operation    
    while True:    
        T1,T2 = temperature()                               # read T1,T2
        string = "T1 = %.1f T2 = %.1f"%(T1,T2)              # format output string
        print string
        time.sleep(delay)                                   # wait delay before next reading in while loop


def temperature():
    
    serCENTER = None
    try:
        ##########   CHANGE HERE  "COMx" port to match your computer   ################################
        serCENTER = serial.Serial("COM13", baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
        
        command = "\x41"                  #this comand makes the meter answer back with 10 bytes
        serCENTER.write(command)
        r = serCENTER.read(10)
        serCENTER.close()
        
        if len(r) == 10:

            #DECIMAL POINT
            #if bit 2 of byte 3 = 1 then T1 = ####      (don't divide by 10)
            #if bit 2 of byte 3 = 0 then T1 = ###.#     ( / by 10)
            #if bit 5 of byte 3 = 1 then T2 = ####
            #if bit 5 of byte 3 = 0 then T2 = ###.#
            
            #extract bit 2, and bit 5 of BYTE 3
            b3bin = bin(ord(r[2]))[2:]          #bits string order "[7][6][5][4][3][2][1][0]"
            bit2 = b3bin[5]
            bit5 = b3bin[2]
            
            #extract T1
            B34 = binascii.hexlify(r[3]+r[4])
            if B34[0].isdigit():
                T1 = float(B34)
            else:
                T1 = float(B34[1:])
                
            #extract T2
            B78 = binascii.hexlify(r[7]+r[8])
            if B78[0].isdigit():
                T2 = float(B78)
            else:
                T2 = float(B78[1:])

            #check decimal point
            if bit2 == "0":
                T1 /= 10.
            if bit5 == "0":
                T2 /= 10.

            return T1,T2
        
        else:
            l = len(r)
            print "received only %i bytes, but needed 10"%l
    
    except serial.SerialException, e:
        print "Serial port error" + str(e)
        
    finally:
        if serCENTER:
            serCENTER.close()

  
main()
