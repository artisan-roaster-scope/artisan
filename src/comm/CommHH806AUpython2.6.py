#!/usr/bin/env python
# This program shows how to read Omega HH806AU thermocouple meter T1 and T2 with Python 2.6
#####################################################################################

# REQUIREMENTS
# python 2.6.2: http://www.python.org/ftp/python/2.6.2/python-2.6.2.msi
# pyserial for python 2.6: http://sourceforge.net/projects/pyserial/files/pyserial/2.6
# javacomm: http://www.xpl4java.org/xPL4Java/javacomm.html
# Java JDK or JRE:  http://java.sun.com/javase/downloads/index.jsp



import serial
import time
import binascii


def main():
    
    print "use CTRL + C to interrupt program\n"
    delay = 1           # set interval of seconds between each reading
    
    while True:    
        t1,t2 = HH806AUtemperature()
        print "T1 = " + str(t1) + "    " + "T2 = " +str(t2) + "\n"
        time.sleep(delay)

def HH806AUtemperature():
    try:
        ser = serial.Serial('COM11', baudrate=19200, bytesize=8, parity='E', stopbits=1, timeout=1)	
        command = "#0A0000NA2\r\n" 
        ser.write(command)
        r = ser.read(14) 
        ser.close()

        #convert to binary to hex string
        s1 = binascii.hexlify(r[5] + r[6])
        s2 = binascii.hexlify(r[10]+ r[11])

        #we convert the strings to integers. Divide by 10.0 (decimal position)
        t1 = int(s1,16)/10. 
        t2 = int(s2,16)/10. 

        return t1, t2
    except serial.SerialException, e:
        print e
        return 0,0

main()
