#!/usr/bin/env python
# This program shows how to read Omega HH506RA thermocouple meter T1 and T2 with Python 2.6
#####################################################################################

# REQUIREMENTS
# python 3.x: http://www.python.org/ftp/python/
# pyserial for python 2.6: http://sourceforge.net/projects/pyserial/files/pyserial/2.6/
# javacomm: http://www.xpl4java.org/xPL4Java/javacomm.html
# Java JDK or JRE:  http://java.sun.com/javase/downloads/index.jsp


import serial
import time


def main():

    print('use CTRL + C to interrupt program\n')
    delay = 3           # set interval of seconds between each reading
    port = '/dev/cu.usbserial-FTFKDA5O'

    ser = serial.Serial(port, baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=1)


    while True:
        #v = fl.readlines(eol=serial.to_bytes("\r\n"))
        #v = ser.read()
        ser.write(b's') # only stable
        #ser.write(b"w") # any weight
        v = ser.readline()
        # b'          194 g  \r\n'
        print(v)
        time.sleep(delay)

main()
