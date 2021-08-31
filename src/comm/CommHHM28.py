#!/usr/bin/env python
# This program shows how to read Omega HHM28[6] multimeter with Python 2.6[7]
#####################################################################################

# REQUIREMENTS
# python 2.6.2: http://www.python.org/ftp/python/2.6.2/python-2.6.2.msi
# pyserial for python 2.6: http://sourceforge.net/projects/pyserial/files/pyserial/2.5/pyserial-2.5-rc1.win32.exe/download
# javacomm: http://www.xpl4java.org/xPL4Java/javacomm.html
# Java JDK or JRE:  http://java.sun.com/javase/downloads/index.jsp


import serial
import time


def main():
    
    print "use CTRL + C to interrupt program\n"
    delay = 1           # set interval of seconds between each reading
    while True:    
        r,symbols = read()
        if len(r): 
            print "V = " , r, symbols   #print value and attached symbols
        time.sleep(delay)

#FRAME  = [1A,2B,3C,4D,5E,6F,7G,8H,9I,10J,11K,12L,13M,14N]  ALPHA = Data part of byte; Numbers are used in frame to identify byte order
def read():
    try:
        ser = serial.Serial(port="COM1", baudrate=2400, bytesize=8, parity='N', stopbits=1, timeout=1)
        #keep reading till the first byte of next frame (till we read an actual 1 in 1A )
        for i in range(28):  #any number > 14 will be OK     
            r = ser.read(1)
            if len(r):
                fb = (ord(r[0]) & 0xf0) >> 4
                if fb == 1:
                    r2 = ser.read(13)   #read the remaining 13 bytes to get 14 bytes
                    ser.close()
                    break
                
        #create 14 byte frame 
        frame = r + r2
        if len(frame) == 14:
            #extract data from frame in to a list containing the hex string values of the data
            data = []
            for i in range(14):
                data.append(hex((ord(frame[i]) & 0x0f))[2:])

            #decimal values are BC + DE + FG + HI   
            digits = [data[1]+data[2],data[3]+data[4],data[5]+data[6],data[7]+data[8]]

            #find sign 
            sign = ""   # +
            if (int(digits[0],16) & 0x80) >> 7:
                sign = "-"
                
            #find location of decimal point
            for i in range(4):
                if (int(digits[i],16) & 0x80) >> 7:
                    dec = i
                    digits[i] = hex(int(digits[i],16) & 0x7f)[2:]  #remove decimal point
                    if len(digits[i]) < 2:
                        digits[i] = "0" + digits[i]
            #find value from table
            table = {"7d":"0","05":"1","5b":"2","1f":"3","27":"4","3e":"5",
                     "7e":"6","15":"7","7f":"8","3f":"9","00":" ","68":"L"} 
            val = ""
            for i in range(4):
                val += table[digits[i]]
                
            number = ".".join((val[:dec],val[dec:]))  #add the decimal point

            #find symbols
            tablesymbols = [
                            ["AC","","Auto","RS232"],
                            ["u","n","k","diode"],
                            ["m","%","M","Beep"],
                            ["F","Ohm","Relative","Hold"],
                            ["A","V","Hz","Low Batt"]
                            ]
            masks = [0x08,0x04,0x02,0x01]
            nbytes = [0,9,10,11,12]
            symbols = ""
            for p in range(5):
                for i in range(4):
                    if (int(data[nbytes[p]],16) & masks[i]):
                        symbols += tablesymbols[p][i]  + " "              
                
            return sign + number, symbols
        else:
            ser.close()
            return "0"
    
    except serial.SerialException, e:
        print e
        return 0,0

main()
