#!/usr/bin/env python
#####################################################################################
# COMM TEST PROGRAM FOR CENTER 309 DATA LOGGER  (www.centertek.com)
# This program shows how to read Temp from a CENTER 309 thermometer data logger using T1 and T2
# USAGE: edit "COMx" port in temperature() at line 58, plug T1 and T2 thermocouples
# ##################################################################################################

# REQUIREMENTS
# python 3.x: http://www.python.org/ftp/python/
# pyserial for python 2.6: http://sourceforge.net/projects/pyserial/files/pyserial/2.6/
# javacomm: http://www.xpl4java.org/xPL4Java/javacomm.html
# Java JDK or JRE:  http://java.sun.com/javase/downloads/index.jsp


import serial
import time
import platform

platf = str(platform.system())


def main():
    T1 = 0.0
    T2 = 0.0
    mode = "F"
    delay = 2            # set time between each reading in seconds

    print("Press <CTRL 'C'> to stop")
    #Read temperature in a forever loop to check operation    
    while True:    
        T1,T2,mode = temperature()                              # read T1,T2, and mode (C or F)
        string = "T1 = %.1f%s T2 = %.1f%s"%(T1,mode,T2,mode)    # format output string
        print(string)
        time.sleep(delay)                    # wait delay before next reading in while loop


def temperature():
##    
##    command = "\x4B" returns 4 bytes model number, 309 or 304
##    command = "\x41" returns 45 bytes (8x5 + 5 = 45) as follows:
##    
##    "\x02                               frame start, 1 byte
##    "\x80                               status of logger, bit7=Celsi/Faren, bit6=batter low, bit5=Hold, bit4=REL, bit3=T1-T2, bit2:1=Max/Min, bit0=recording
##     \xYY\                              status of logger, bit7=auto_off, bit6:1=not used, bit0=Memory_full
##     \xYY\xYY\xYY\xYY\                  T1_State to T4_State, 4 bytes, not used
##    "\xAA\xAA\xBB\xBB\xCC\xCC\xDD\xDD"  Temprerature T1 = AAAA, T2=BBBB, T3= CCCC, T4 = DDDD, 4 words; /10 or /1
##    "\x00\x00\x00\x00\x00\x00\x00\x00"  T1_rel to T4_rel, 4 words, high byte first
##    "\x00\x00\x00\x00\x00\x00\x00\x00"  T1_min to T4_min, 4 words, high byte first
##    "\x00\x00\x00\x00\x00\x00\x00\x00"  T1_max to T4_max, 4 words, high byte first
##    "\x00                               40th byte, Channel_OL_set, bit3:0=T4-T1
##    "\x00                               41th byte, Rel_OL_set, bit3:0=T4-T1                                
##    "\x00                               42th byte, Max_OL_set, bit3:0=T4-T1
##    "\x00                               43th byte, Min_OL_set, bit3:0=T4-T1
##    "\x0E                               44th byte, Channel_X1_X10, bit3:0=T4-T1, x1 or x10
##    "\x03                               45th byte, frame end, 1 byte
##    
    serCENTER = None
    try:
        ##########   CHANGE HERE  "COMx" port to match your computer   ################################
        if platf == 'Windows':
            port = "COM13"
        else:
            port = "/dev/cu.SLAB_USBtoUART"
        serCENTER = serial.Serial(port, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
        
        command = b"\x41"                  #this comand makes the meter answer back with 45 bytes
        serCENTER.write(command)
        r = serCENTER.read(45)
        serCENTER.close()
        
        if len(r) != 45:
            #Bad RX data
            return 0.,0.,"RX failed"

        #check that T1 and T2 are both plugged in 
        #print(binascii.hexlify(r[43]))       
        #if int(binascii.hexlify(r[43].encode('utf-8')),16) != 12:
        #    #T1 + T2 not plugged in
        #    return 0.,0.,"plug T1&T2!"

        mode = "X"
        checkmode = int(r[1])
        if checkmode == 128:
            mode = "C"          #Celsius
        elif checkmode == 0:
            mode = "F"          #Farenheit
        
        T1 = int(r[7]*256 + r[8])
        T2 = int(r[9]*256 + r[10])
        #T3 = int(binascii.hexlify(r[11] + r[12]),16)        #aditional reference left that shows how to to read T3
        #T4 = int(binascii.hexlify(r[13] + r[14]),16)        #aditional reference left that shows how to to read T4
        
        return T1/10.,T2/10.,mode
    
    except serial.SerialException as e:
        print("Serial port error" + str(e))
        
    finally:
        if serCENTER:
            serCENTER.close()

  
main()
