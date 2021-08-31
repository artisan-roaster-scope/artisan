#!/usr/bin/env python
# This program shows how to read Omega HH506RA thermocouple meter T1 and T2 with Python 2.6
#####################################################################################

# REQUIREMENTS
# python 2.6.2: http://www.python.org/ftp/python/2.6.2/python-2.6.2.msi
# pyserial for python 2.6: http://sourceforge.net/projects/pyserial/files/pyserial/2.6/
# javacomm: http://www.xpl4java.org/xPL4Java/javacomm.html
# Java JDK or JRE:  http://java.sun.com/javase/downloads/index.jsp



import serial
import time
import binascii

def main():
    
    print "use CTRL + C to interrupt program\n"
    delay = 1           # set interval of seconds between each reading
    port = '/dev/tty.usbserial-A2001Epn'
    
    id = HH506RAid(port,delay)
    while True:    
        t1,t2 = HH506RAtemperature(port,delay,id)
        print "T1 = " + str(t1) + "    " + "T2 = " +str(t2) + "\n"
        time.sleep(delay)
        

def HH506RAid(port,delay):
    try:
        ser = serial.Serial(port, baudrate=2400, bytesize=7, parity='E', stopbits=1, timeout=1)	
        sync = None
        while sync != "Err\r\n":
            ser.write(b"\r")
            sync = ser.read(5)
            time.sleep(1)
            print(sync)
        ser.write("%000R")
        id = ser.read(5)[0:3]
        ser.close()
        return id
    except serial.SerialException, e:
        print e
        return "000"

def hex2temp(hex):
    if hex == '':
        return 0
    else:
        t = int(hex[1:],16)/10.0
        if hex[0:1] == '-':
            t = -t
        if t < -50 or t > 400:
            return 0
        else:
            return t

def HH506RAtemperature(port,delay,id):
    try:
        ser = serial.Serial(port, baudrate=2400, bytesize=7, parity='E', stopbits=1, timeout=1)	
        ser.write("#" + id + "N\r\n" )
        r = ser.read(14)
        ser.close()
        return hex2temp(r[0:5]), hex2temp(r[6:11])
    except serial.SerialException, e:
        print e
        return 0,0

main()
