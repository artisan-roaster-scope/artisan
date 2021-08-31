#!/usr/bin/env python
# This program shows how to read TC4 aArtisan thermocouple meter T1, T2, T3 and T4 with Python
#####################################################################################


import serial
import time

def main():
    
    print("use CTRL + C to interrupt program\n")
    delay = 1           # set interval of seconds between each reading
    port = '/dev/cu.usbserial-AH01B8JA'
    
    
    sp = serial.Serial(port, baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=1)

    time.sleep(2) # wait until Arduino restarted after opening the serial port
    
    sp.flushInput()
    sp.flushOutput()
    
    # configure virtual TCs
    print(">CHAN;1234")
    sp.write(b"CHAN;1234\n")
    time.sleep(0.5) # give the serial port some time to read the data
    rl = sp.readline().decode('utf-8')[:-2]
    print(rl)
    if not rl.startswith("#"):
        print("initialization failed")
        return
    
    # configure units
    print(">UNIT;C")
    sp.write(b"UNIT;C\n")
    rl = sp.readline().decode('utf-8')[:-2]
    print(rl)
        
    while True:
        # read temperatures
        print(">READ")
        sp.write(b"READ\n")
        rl = sp.readline().decode('utf-8')[:-2]
        res = rl.rsplit(',')
        print("T1:%sC, T2:%sC, T3:%sC, T4:%sC"%(res[0],res[1],res[2],res[3]))
        time.sleep(delay)
        
    sp.close()	
    
main()
