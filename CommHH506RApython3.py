#!/usr/bin/env python
# This program shows how to read Omega HH506RA thermocouple meter T1 and T2 with Python 3.x
#####################################################################################

# REQUIREMENTS
# python 3.x: http://www.python.org/ftp/python/
# pyserial for python 2.6: http://sourceforge.net/projects/pyserial/files/pyserial/2.6/
# javacomm: http://www.xpl4java.org/xPL4Java/javacomm.html
# Java JDK or JRE:  http://java.sun.com/javase/downloads/index.jsp


# 2012-04-06: Updated to run on Python v3.x (ML)

import serial
import time
import binascii


def main():
    
    print("use CTRL + C to interrupt program\n")
    delay = 1           # set interval of seconds between each reading
    port = '/dev/tty.usbserial-A2001Epn'
     
    id = HH506RAid(port,delay)
    while True:   
        t1,t2 = HH506RAtemperature(port,delay,id)
        print("T1 = " + str(t1) + "    " + "T2 = " +str(t2) + "\n")
        time.sleep(delay)
        

def HH506RAid(port,delay):
    try:
        ser = serial.Serial(port, baudrate=2400, bytesize=7, parity='E', stopbits=1, timeout=1)	
        sync = None
        while sync != b"Err\r\n":
            ser.write(b"\r\n") # seems that on Python3/OSX standard LF is added (might by different on Windows!)
            sync = ser.read(5)
            time.sleep(1)
        ser.write(b"%000R")
        id = ser.read(5)[0:3]
        ser.close()
        return id
    except serial.SerialException as e:
        print(e)
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
        ser.write("#".encode('ascii') + id + "N\r".encode('ascii'))
        ser.write(b"#" + id + b"N\r")
        r = ser.read(14)
        ser.close()
        return hex2temp(r[0:5]), hex2temp(r[6:11])
    except serial.SerialException as e:
        print(e)
        return 0,0

main()
