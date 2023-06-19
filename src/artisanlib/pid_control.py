#
# ABOUT
# Artisan PID Controllers (Fuji, DTA, Arduino TC4)

# LICENSEsvLen
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2023


###################################################################################
##########################  FUJI PID CLASS DEFINITION  ############################
###################################################################################

# This class can work for either one Fuji PXR or one Fuji PXG. It is used for the controlling PID only.
# NOTE: There is only one controlling PID. The second pid is only used for reading BT and therefore,
# there is no need to create a second PID object since the second pid all it does is read temperature (always use the same command).
# All is needed for the second pid is its unit id number stored in aw.qmc.device[].
# The command to read T is the always the same for PXR and PXG but with the unit ID changed.

import time as libtime
import numpy
import logging
from typing import Union, List, Dict, Optional, TYPE_CHECKING
from typing_extensions import Final  # Python <=3.7

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import

from artisanlib.util import decs2string, fromCtoF, fromFtoC, hex2int, str2cmd, stringfromseconds, cmd2str

try:
    from PyQt6.QtCore import pyqtSlot # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import pyqtSlot # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


_log: Final[logging.Logger] = logging.getLogger(__name__)

class FujiPID():
    def __init__(self,aw) -> None:
        self.aw = aw

        # follow background: if True, Artisan sends SV values taken from the current background profile if any
        self.followBackground = False
        self.lookahead = 0 # the lookahead in seconds
        self.rampsoak = False # True if RS is active
        self.sv:Optional[float] = None # the last sv send to the Fuji PID

        ## FUJI PXG input types
        ##0 (JPT 100'3f)
        ##1 (PT 100'3f)
        ##2 (J)
        ##3 (K)
        ##4 (R)
        ##5 (B)
        ##6 (S)
        ##7 (T)
        ##8 (E)
        ##9 (no function)
        ##10 (no function)
        ##11 (no function)
        ##12 (N)
        ##13 (PL- 2)
        ##14 (no function)
        ##15 (0V to 5V / 0mA to 20mA
        ##16 (1V to 5V/4mA to 20mA)
        ##17 (0mV to 10V)
        ##18 (2V to 10V)
        ##19 (0mV to 100mV)
        self.PXGthermotypes = ['JPT 100',#0
                            'PT 100',    #1
                            'J',         #2
                            'K',         #3
                            'R',         #4
                            'B',         #5
                            'S',         #6
                            'T',         #7
                            'E',         #8
                            'N',         #12
                            'PL-2',      #13
                            '0V-5V/0mA-20mA', #15
                            '1V-5V/4mA-20mA', #16
                            '0mV-10V',   #17
                            '2V to 10V', #18
                            '0mV-100mV'  #19
                            ]
        self.PXGconversiontoindex = [0,1,2,3,4,5,6,7,8,12,13,15,16,17,18,19]  #converts fuji PID PXG types to indexes
        self.PXFthermotypes = [
                            'PT 100-2 (0-500C)',    #8
                            'PT 100-3 (0-600C)',    #9
                            'PT 100-7 (-199-600C)', #13
                            'PT 100-8 (-200-850C)', #14
                            'J-1 (0-400C)',         #15
                            'J-2 (-20-400C)',       #16
                            'J-3 (0-800C)',         #17
                            'J-4 (-2000-1300C)',    #18
                            'K-1 (0-400C)',         #19
                            'K-2 (-20-500C)',       #20
                            'K-3 (0-800C)',         #21
                            'K-4 (-200-1300C)',     #22
                            'R',                    #23
                            'B',                    #24
                            'S',                    #25
                            'T-2 (-199-400C)',      #27
                            'E-1 (0-800C)',         #28
                            'E-2 (-150-800C)',      #29
                            'E-3 (-200-800C)',      #30
                            'N',                    #34
                            'PL-2',                 #36
                            '0V to 5V',             #37
                            '1V to 5V',             #38
                            '0V to 10V',            #39
                            '0mA to 20mA',          #42
                            '4mA to 20mA',          #43
                            ]
        self.PXFconversiontoindex = [8,9,13,14,15,16,17,18,19,20,21,22,23,24,25,27,28,29,30,34,36,37,38,39,42,43]  #converts fuji PID PXF types to indexes
        ## FUJI PXR input types
        ##0 (JPT 100'3f)
        ##1 (PT 100'3f)
        ##2 (J)
        ##3 (K)
        ##4 (R)
        ##5 (B)
        ##6 (S)
        ##7 (T)
        ##8 (E)
        ##12 (N)
        ##13 (PL- 2)
        ##15 (0V to 5V/0mA to 20mA)
        ##16 (1V to 5V/4mA to 20mA)
        ##17 (0mV to 10V)
        ##18 (2V to 10V)
        ##19 (0mV to 100mV)
        self.PXRthermotypes = [
                            'PT 100',   #1
                            'J',        #2
                            'K',        #3
                            'R',        #4
                            'B',        #5
                            'S',        #6
                            'T',        #7
                            'E',        #8
                            'N',        #12
                            'PL-2',     #13
                            '1V to 5V/4mA to 20mA' #16
                            ]
        self.PXRconversiontoindex = [1,2,3,4,5,6,7,8,12,13,16]  #converts fuji PID PXR types to indexes

        #refer to Fuji PID instruction manual for more information about the parameters and channels
        #dictionary "KEY": [VALUE,MEMORY_ADDRESS]
        self.PXG4:Dict[str, List[Union[float, int]]] = {
                  ############ CH1  Selects controller modes
                  # manual mode 0 = OFF(auto), 1 = ON(manual)
                  'manual': [0,41121],
                  #run or standby 0=OFF(during run), 1 = ON(during standby)
                  'runstandby': [0,41004],
                  #autotuning run command modes available 0=off, 1=on, 2=low
                  'autotuning': [0,41005],
                  #rampsoak command modes available 0=off, 1=run; 2=hold
                  'rampsoak': [0,41082],
                  #select SV sv1,...,sv7
                  'selectsv': [1,41221],
                  #selects PID number behaviour mode: pid1,...,pid7
                  'selectpid': [0,41222],
                  ############ CH2  Main operating pid parameters.
                  #proportional band  P0 (0% to 999.9%)
                  'p': [5,41006],
                  #integration time i0 (0 to 3200.0 sec)
                  'i': [240,41007],
                  #differential time d0 (0.0 to 999.9 sec)
                  'd': [60,41008],
                   ############ CH3 These are 7 pid storage locations
                  'sv1': [300.0,41241], 'p1': [5,41242], 'i1': [240,41243], 'd1': [60,41244],
                  'sv2': [350.0,41251], 'p2': [5,41252], 'i2': [240,41253], 'd2': [60,41254],
                  'sv3': [400.0,41261], 'p3': [5,41262], 'i3': [240,41263], 'd3': [60,41264],
                  'sv4': [450.0,41271], 'p4': [5,41272], 'i4': [240,41273], 'd4': [60,41274],
                  'sv5': [500.0,41281], 'p5': [5,41282], 'i5': [240,41283], 'd5': [60,41284],
                  'sv6': [550.0,41291], 'p6': [5,41292], 'i6': [240,41293], 'd6': [60,41294],
                  'sv7': [575.0,41301], 'p7': [5,41302], 'i7': [240,41303], 'd7': [60,41304],
                  'selectedpid':[7,41225],
                  ############# CH4      Creates a pattern of temperatures (profiles) using ramp soak combination
                  #sv stands for Set Value (desired temperature value)
                  #the time to reach sv is called ramp
                  #the time to hold the temperature at sv is called soak
                  'timeunits': [1,41562],  #0=hh.MM (hour:min)  1=MM.SS (min:sec)                             # PXG has two time formats HH:MM (factory default) and MM:SS
                  # Example. Dry roast phase. selects 3 or 4 minutes                                          # PXG needs to have parameter TIMU set to 1 (MM:SS)
                  'segment1sv': [270.0,41581],'segment1ramp': [180,41582],'segment1soak': [0,41583],          # See PXG Manual chapter 6: Ramp/Soak Time Units to set the parameter TIMU
                  'segment2sv': [300.0,41584],'segment2ramp': [180,41585],'segment2soak': [0,41586],
                  'segment3sv': [350.0,41587],'segment3ramp': [180,41588],'segment3soak': [0,41589],
                  'segment4sv': [400.0,41590],'segment4ramp': [180,41591],'segment4soak': [0,41592],
                  # Example. Phase to 1C. selects 6 or 8 mins
                  'segment5sv': [530.0,41593],'segment5ramp': [180,41594],'segment5soak': [0,41595],
                  'segment6sv': [530.0,41596],'segment6ramp': [180,41597],'segment6soak': [0,41598],
                  'segment7sv': [540.0,41599],'segment7ramp': [180,41600],'segment7soak': [0,41601],
                  'segment8sv': [540.0,41602],'segment8ramp': [180,41603],'segment8soak': [0,41604],
                  'segment9sv': [550.0,41605],'segment9ramp': [180,41606],'segment9soak': [0,41607],
                  'segment10sv': [550.0,41608],'segment10ramp': [180,41609],'segment10soak': [0,41610],
                  'segment11sv': [560.0,41611],'segment11ramp': [180,41612],'segment11soak': [0,41613],
                  'segment12sv': [560.0,41614],'segment12ramp': [180,41615],'segment12soak': [0,41616],
                  # Eaxample. Finish phase. selects 3 mins for regular coffee or 5 mins for espresso
                  'segment13sv': [570.0,41617],'segment13ramp': [180,41618],'segment13soak': [0,41619],
                  'segment14sv': [570.0,41620],'segment14ramp': [180,41621],'segment14soak': [0,41622],
                  'segment15sv': [580.0,41623],'segment15ramp': [180,41624],'segment15soak': [0,41625],
                  'segment16sv': [580.0,41626],'segment16ramp': [180,41627],'segment16soak': [0,41628],
                  # "rampsoakmode" 0-15 = 1-16 IMPORTANT: Factory setting is 3 (BAD). Set it up to number 0 or it will
                  # sit on stanby (SV blinks) at the end till rampsoakmode changes. It will appear as if the PID broke (unresponsive)
                  'rampsoakmode':[0,41081],
                  'rampsoakpattern': [6,41561],  #ramp soak activation pattern 0=(1-4) 1=(5-8) 2=(1-8) 3=(9-12) 4=(13-16) 5=(9-16) 6=(1-16)
                  ################  CH5    Checks the ramp soak progress, control output, remaining time and other status functions
                  'stat':[41561], #reads only. 0=off,1=1ramp,2=1soak,3=2ramp,4=2soak,...31=16ramp,32=16soak,33=end
                  ################  CH6    Sets up the thermocouple type, input range, output range and other items for the controller
                  #input type: 0=NA,1=PT100ohms,2=J,3=K,4=R,5=B,6=S,7=T,8=E,12=N,13=PL2,15=(0-5volts),16=(1-5V),17=(0-10V),18=(2-10V),19=(0-100mV)
                  'pvinputtype': [3,41016],
                  'pvinputlowerlimit':[0,41018],
                  'pvinputupperlimit':[9999,41019],
                  'decimalposition': [1,41020],
                  'unitdisplay':[1,41345],         #0=Celsius; 1=Fahrenheit
                  #################  CH7    Assigns functions for DI (digital input), DO (digital output), LED lamp and other controls
                  'rampslopeunit':[1,41432], #0=hour,1=min
                  'controlmethod':[0,41002],  #0=pid,2=fuzzy,2=self,3=pid2
                  #################  CH8     Sets the defect conditions for each type of alarm
                  #################  CH9     Sets the station number _id and communication parameters of the PID controller
                  #################  CH10    Changes settings for valve control
                  #################  CH11    Sets passwords
                  #################  CH12    Sets the parameters mask functions to hide parameters from the user
                  ################# READ ONLY MEMORY (address starts with digit 3)
                  'pv?':[0,31001],'sv?':[0,31002],'alarm?':[31007],'fault?':[31008],'stat?':[31041],'mv1':[0,31042]
                  }

        # "KEY": [VALUE,MEMORY_ADDRESS]
        self.PXR:Dict[str, List[Union[float, int]]] = {'autotuning':[0,41005],
                    'segment1sv':[100.0,41057],'segment1ramp':[3,41065],'segment1soak':[0,41066], #PXR uses only HH:MM time format but stored as minutes in artisan
                    'segment2sv':[100.0,41058],'segment2ramp':[3,41067],'segment2soak':[0,41068],
                    'segment3sv':[100.0,41059],'segment3ramp':[3,41069],'segment3soak':[0,41070],
                    'segment4sv':[100.0,41060],'segment4ramp':[3,41071],'segment4soak':[0,41072],
                    'segment5sv':[100.0,41061],'segment5ramp':[3,41073],'segment5soak':[0,41074],
                    'segment6sv':[100.0,41062],'segment6ramp':[3,41075],'segment6soak':[0,41076],
                    'segment7sv':[100.0,41063],'segment7ramp':[3,41077],'segment7soak':[0,41078],
                    'segment8sv':[100.0,41064],'segment8ramp':[3,41079],'segment8soak':[0,41080],
                    #Tells what to do after finishing or how to start. See documentation under ramp soak pattern: 0-15
                    'rampsoakmode':[0,41081],
                    #rampsoak command 0=OFF, 1= RUN, 2= HALTED, 3=END
                    'rampsoak':[0,41082],
                    #ramp soak pattern. 0=executes 1 to 4; 1=executes 5 to 8; 2=executes 1 to 8
                    'rampsoakpattern':[0,41083],
                    #PID=0,FUZZY=1,SELF=2
                    'controlmethod':[0,41002],
                    #sv set value
                    'sv0':[0,41003],
                    # run standby 0=RUN 1=STANDBY
                    'runstandby': [0,41004],
                    'p':[5,41006],
                    'i':[240,41007],
                    'd':[60,41008],
                    'decimalposition': [1,41020],
                    'svlowerlimit':[0,41031],
                    'svupperlimit':[0,41032],
                    'pvinputtype':[3,41016],
                    #READ ONLY
                    #current pv
                    'pv?':[0,31001],
                    #current sv on display (during ramp soak it changes)
                    'sv?':[0,31002],
                    #rampsoak current running position (1-8)
                    'segment?':[0,31009],
                    'mv1':[0,31004]   #duty cycle rx -300 to 10300  = -3.00% to 103.00%
                    }
        self.PXF:Dict[str, List[Union[float, int]]] = dict(self.PXG4)
        # initialize the PXF register numbers from the PXG and an offset of 1000
        for k in self.PXF: # pylint: disable=consider-iterating-dictionary,consider-using-dict-items
            if len(self.PXF[k]) > 1:
                self.PXF[k] = [self.PXF[k][0],self.PXF[k][1]+1000]
            else:
                self.PXF[k] = [self.PXF[k][0]+1000]

    #writes new values for p - i - d
    def setpidPXG(self,k,newPvalue,newIvalue,newDvalue):
        if k is not None and k > 0:
            #send command to the right sv
            pkey = 'p' + str(k)
            ikey = 'i' + str(k)
            dkey = 'd' + str(k)
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXG4[pkey][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,int(float(newPvalue)*10.))
                libtime.sleep(0.035)
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXG4[ikey][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,int(float(newIvalue)*10.))
                libtime.sleep(0.035)
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXG4[dkey][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,int(float(newDvalue)*10.))
                libtime.sleep(0.035)
                p = i = d = '        '
            else:
                commandp = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXG4[pkey][1],int(float(newPvalue)*10.))
                commandi = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXG4[ikey][1],int(float(newIvalue)*10.))
                commandd = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXG4[dkey][1],int(float(newDvalue)*10.))
                p = self.aw.ser.sendFUJIcommand(commandp,8)
                libtime.sleep(0.035)
                i = self.aw.ser.sendFUJIcommand(commandi,8)
                libtime.sleep(0.035)
                d = self.aw.ser.sendFUJIcommand(commandd,8)
                libtime.sleep(0.035)
            #verify it went ok
            if len(p) == 8 and len(i)==8 and len(d) == 8:
                self.aw.fujipid.PXG4[pkey][0] = float(newPvalue)
                self.aw.fujipid.PXG4[ikey][0] = float(newIvalue)
                self.aw.fujipid.PXG4[dkey][0] = float(newDvalue)
                message = QApplication.translate('StatusBar','pid #{0} successfully set to ({1},{2},{3})'
                                                       ).format(str(k),str(newPvalue),str(newIvalue),str(newDvalue))
                self.aw.sendmessage(message)
            else:
                lp = len(p)
                li = len(i)
                ld = len(d)
                message = QApplication.translate('StatusBar','pid command failed. Bad data at pid{0} (8,8,8): ({1},{2},{3}) '
                                                       ).format(str(k),str(lp),str(li),str(ld))
                self.aw.sendmessage(message)
                self.aw.qmc.adderror(message)

    #writes new values for p - i - d
    def setpidPXF(self,k,newPvalue,newIvalue,newDvalue):
        if k is not None and k > 0:
            #send command to the right sv
            pkey = 'p' + str(k)
            ikey = 'i' + str(k)
            dkey = 'd' + str(k)
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXF[pkey][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,int(float(newPvalue)*10.))
                libtime.sleep(0.035)
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXF[ikey][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,int(float(newIvalue)*10.))
                libtime.sleep(0.035)
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXF[dkey][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,int(float(newDvalue)*10.))
                libtime.sleep(0.035)
                p = i = d = '        '
            else:
                commandp = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXF[pkey][1],int(float(newPvalue)*10.))
                commandi = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXF[ikey][1],int(float(newIvalue)*10.))
                commandd = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXF[dkey][1],int(float(newDvalue)*10.))
                p = self.aw.ser.sendFUJIcommand(commandp,8)
                libtime.sleep(0.035)
                i = self.aw.ser.sendFUJIcommand(commandi,8)
                libtime.sleep(0.035)
                d = self.aw.ser.sendFUJIcommand(commandd,8)
                libtime.sleep(0.035)
            #verify it went ok
            if len(p) == 8 and len(i)==8 and len(d) == 8:
                self.aw.fujipid.PXF[pkey][0] = float(newPvalue)
                self.aw.fujipid.PXF[ikey][0] = float(newIvalue)
                self.aw.fujipid.PXF[dkey][0] = float(newDvalue)
                message = QApplication.translate('StatusBar','pid #{0} successfully set to ({1},{2},{3})'
                                                       ).format(str(k),str(newPvalue),str(newIvalue),str(newDvalue))
                self.aw.sendmessage(message)
            else:
                lp = len(p)
                li = len(i)
                ld = len(d)
                message = QApplication.translate('StatusBar','pid command failed. Bad data at pid{0} (8,8,8): ({1},{2},{3}) '
                                                       ).format(str(k),str(lp),str(li),str(ld))
                self.aw.sendmessage(message)
                self.aw.qmc.adderror(message)

    # updates and returns the current ramp soak mode
    def getCurrentRampSoakMode(self) -> Optional[int]:
        if self.aw.ser.controlETpid[0] == 0: # PXG
            register = self.aw.fujipid.PXG4['rampsoakmode'][1]
        elif self.aw.ser.controlETpid[0] == 1: # PXR
            register = self.aw.fujipid.PXR['rampsoakmode'][1]
        elif self.aw.ser.controlETpid[0] == 4: # PXF
            register = self.aw.fujipid.PXF['rampsoakmode'][1]
        else:
            return None
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(register,3)
            currentmode = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
        else:
            msg = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,register,1)
            currentmode = self.aw.fujipid.readoneword(msg)
        if self.aw.ser.controlETpid[0] == 0: # PXG
            self.aw.fujipid.PXG4['rampsoakmode'][0] = currentmode
        elif self.aw.ser.controlETpid[0] == 1: # PXR
            self.aw.fujipid.PXR['rampsoakmode'][0] = currentmode
        elif self.aw.ser.controlETpid[0] == 4: # PXF
            self.aw.fujipid.PXF['rampsoakmode'][0] = currentmode
        return currentmode

    def getCurrentPIDnumberPXG(self):
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(self.aw.fujipid.PXG4['selectedpid'][1],3)
            N = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
        else:
            command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,self.aw.fujipid.PXG4['selectedpid'][1],1)
            N = self.aw.fujipid.readoneword(command)
        libtime.sleep(0.035)
        return N

    def getCurrentPIDnumberPXF(self):
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(self.aw.fujipid.PXF['selectedpid'][1],3)
            N = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
        else:
            command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,self.aw.fujipid.PXF['selectedpid'][1],1)
            N = self.aw.fujipid.readoneword(command)
        libtime.sleep(0.035)
        return N

    def setpidPXR(self,var,v):
        r = ''
        if var == 'p':
            p = int(v*10)
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXR['p'][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,p)
                r = '        '
            else:
                command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXR['p'][1],p)
                r = self.aw.ser.sendFUJIcommand(command,8)
        elif var == 'i':
            i = int(v*10)
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXR['i'][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,i)
                r = '        '
            else:
                command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXR['i'][1],i)
                r = self.aw.ser.sendFUJIcommand(command,8)
        elif var == 'd':
            d = int(v*10)
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXR['d'][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,d)
                r = '        '
            else:
                command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXR['d'][1],d)
                r = self.aw.ser.sendFUJIcommand(command,8)

        if len(r) == 8:
            message = QApplication.translate('StatusBar','{0} successfully sent to pid ').format(var)
            self.aw.sendmessage(message)
            if var == 'p':
                self.aw.fujipid.PXR['p'][0] = int(v)
            elif var == 'i':
                self.aw.fujipid.PXR['i'][0] = int(v)
            elif var == 'd':
                self.aw.fujipid.PXR['d'][0] = int(v)
        else:
            message = QApplication.translate('StatusBar','setpid(): There was a problem setting {0}').format(var)
            self.aw.sendmessage(message)
            self.aw.qmc.adderror(message)

    def calcSV(self,tx):
        if self.aw.qmc.background:
            # Follow Background mode
            if self.aw.qmc.swapETBT: # we observe the BT
                res = self.aw.qmc.backgroundSmoothedBTat(tx + self.lookahead) # smoothed and approximated background
                if res == -1:
                    return None # no background value for that time point
                return res
            res = self.aw.qmc.backgroundSmoothedETat(tx + self.lookahead) # smoothed and approximated background
            if res == -1:
                return None # no background value for that time point
            return res
        return None

    ##TX/RX FUNCTIONS
    #This function reads read-only memory (with 3xxxx memory we need function=4)
    #both PXR3 and PXG4 use the same memory location 31001 (3xxxx = read only)
    # pidType: 0=PXG, 1=PXR, 2=None, 3=DTA, 4=PXF (here we support only 0, 1 and 4 for now)
    def gettemperature(self, pidType, stationNo):
        if pidType == 0:
            reg = self.PXG4['pv?'][1]
        elif pidType == 1:
            reg = self.PXR['pv?'][1]
        elif pidType == 4:
            reg = self.PXF['pv?'][1]
        else:
            return -1
        if self.aw.ser.useModbusPort:
            # we use the pymodbus implementation
            return self.aw.modbus.readSingleRegister(stationNo,self.aw.modbus.address2register(reg,4),4)
        #we compose a message then we send it by using self.readoneword()
        return self.readoneword(self.message2send(stationNo,4,reg,1))

    # activates the SV slider
    def activateONOFFsliderSV(self,flag):
        self.aw.pidcontrol.activateSVSlider(flag)

    def readcurrentsv(self):
        val:float = -0.1
        if self.aw.ser.useModbusPort:
            reg = None
            #if control pid is fuji PXG4
            if self.aw.ser.controlETpid[0] == 0:
                reg = self.aw.modbus.address2register(self.PXG4['sv?'][1],4)
            #or if control pid is fuji PXR
            elif self.aw.ser.controlETpid[0] == 1:
                reg = self.aw.modbus.address2register(self.PXR['sv?'][1],4)
            #or if control pid is fuji PXF
            elif self.aw.ser.controlETpid[0] == 4:
                reg = self.aw.modbus.address2register(self.PXF['sv?'][1],4)
            if reg is not None:
                res = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,4)
                if res is not None:
                    val = res/10.
        else:
            command = ''
            #if control pid is fuji PXG4
            if self.aw.ser.controlETpid[0] == 0:
                command = self.message2send(self.aw.ser.controlETpid[1],4,self.PXG4['sv?'][1],1)
            #or if control pid is fuji PXR
            elif self.aw.ser.controlETpid[0] == 1:
                command = self.message2send(self.aw.ser.controlETpid[1],4,self.PXR['sv?'][1],1)
            elif self.aw.ser.controlETpid[0] == 4:
                command = self.message2send(self.aw.ser.controlETpid[1],4,self.PXF['sv?'][1],1)
            res = self.readoneword(command)
            if res is not None:
                val = res/10.
        if val != -0.1:
            return val
        return -1

    # returns Fuji duty signal in the range 0-100 or -1
    def readdutycycle(self):
        v = None
        if self.aw.ser.useModbusPort:
            reg = None
            #if control pid is fuji PXG4
            if self.aw.ser.controlETpid[0] == 0:
                reg = self.aw.modbus.address2register(self.PXG4['mv1'][1],4)
            #or if control pid is fuji PXR
            elif self.aw.ser.controlETpid[0] == 1:
                reg = self.aw.modbus.address2register(self.PXR['mv1'][1],4)
            #or if control pid is fuji PXF
            elif self.aw.ser.controlETpid[0] == 4:
                reg = self.aw.modbus.address2register(self.PXF['mv1'][1],4)
            if reg is not None:
                v = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,4)
            else:
                return -1
        else:
            command = ''
            #if control pid is fuji PXG4
            if self.aw.ser.controlETpid[0] == 0:
                command = self.message2send(self.aw.ser.controlETpid[1],4,self.PXG4['mv1'][1],1)
                v = self.readoneword(command)
            #or if control pid is fuji PXR
            elif self.aw.ser.controlETpid[0] == 1:
                command = self.message2send(self.aw.ser.controlETpid[1],4,self.PXR['mv1'][1],1)
                v = self.readoneword(command)
            #or if control pid is fuji PXF
            elif self.aw.ser.controlETpid[0] == 4:
                command = self.message2send(self.aw.ser.controlETpid[1],4,self.PXF['mv1'][1],1)
                v = self.readoneword(command)
        # value out of range (possible a communication error)
        #return val range -3 to 103%. Check for possible decimal digit user settings
        if v is not None:
            if v >= 65236: # -3% to 0%
                return 0
            if v <= 10300: # <= 103%
                return v/100.
        return -1

    def getrampsoakmode(self):
        if self.aw.ser.controlETpid[0] == 0: #Fuji PXG
            register = self.PXG4['rampsoakpattern'][1]
        elif self.aw.ser.controlETpid[0] == 1: #Fuji PXR
            register = self.PXR['rampsoakpattern'][1]
        elif self.aw.ser.controlETpid[0] == 4: #Fuji PXF
            register = self.PXF['rampsoakpattern'][1]
        else:
            return 0
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(register,3)
            currentmode = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
        else:
            msg = self.message2send(self.aw.ser.controlETpid[1],3,register,1)
            currentmode = self.readoneword(msg)
        if self.aw.ser.controlETpid[0] == 0: #Fuji PXG
            self.PXG4['rampsoakpattern'][0] = currentmode
        elif self.aw.ser.controlETpid[0] == 1: #Fuji PXR
            self.PXR['rampsoakpattern'][0] = currentmode
        elif self.aw.ser.controlETpid[0] == 4: #Fuji PXF
            self.PXF['rampsoakpattern'][0] = currentmode
        return currentmode

    # returns True on success and Fails otherwise
    def setrampsoakmode(self,mode):
        if self.aw.ser.controlETpid[0] == 0: #Fuji PXG
            register = self.PXG4['rampsoakpattern'][1]
        elif self.aw.ser.controlETpid[0] == 1: #Fuji PXR
            register = self.PXR['rampsoakpattern'][1]
        elif self.aw.ser.controlETpid[0] == 4: #Fuji PXF
            register = self.PXF['rampsoakpattern'][1]
        else:
            return 0
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(register,3)
            self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,mode)
            r = ''
        else:
            command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,register,mode)
            r = self.aw.ser.sendFUJIcommand(command,8)
        if self.aw.ser.useModbusPort or len(r) == 8:
            if self.aw.ser.controlETpid[0] == 0: #Fuji PXG
                self.PXG4['rampsoakpattern'][0] = mode
            elif self.aw.ser.controlETpid[0] == 1: #Fuji PXR
                self.PXR['rampsoakpattern'][0] = mode
            elif self.aw.ser.controlETpid[0] == 4: #Fuji PXF
                self.PXF['rampsoakpattern'][0] = mode
            return True
        return False

    #turns ON turns OFF current ramp soak mode
    #flag =0 OFF, flag = 1 ON, flag = 2 hold
    #A ramp soak pattern defines a whole profile. They have a minimum of 4 segments.
    # returns True on success, False otherwise
    def setrampsoak(self,flag):
        register = None
        if self.aw.ser.controlETpid[0] == 0: #Fuji PXG
            register = self.PXG4['rampsoak'][1]
        elif self.aw.ser.controlETpid[0] == 1: #Fuji PXR
            register = self.PXR['rampsoak'][1]
        elif self.aw.ser.controlETpid[0] == 4: #Fuji PXF
            register = self.PXF['rampsoak'][1]
        if self.aw.ser.useModbusPort:
            if register is not None:
                reg = self.aw.modbus.address2register(register,6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,flag)
                if flag == 1:
                    self.aw.fujipid.rampsoak = True
                    self.aw.sendmessage(QApplication.translate('Message','RS ON'))
                elif flag == 0:
                    self.aw.fujipid.rampsoak = False
                    self.aw.sendmessage(QApplication.translate('Message','RS OFF'))
                else:
                    self.aw.sendmessage(QApplication.translate('Message','RS on HOLD'))
                return True
        elif register is not None:
            command = self.message2send(self.aw.ser.controlETpid[1],6,register,flag)
            r = self.aw.ser.sendFUJIcommand(command,8)
            #if OK
            if r == command:
                if flag == 1:
                    self.aw.fujipid.rampsoak = True
                    self.aw.sendmessage(QApplication.translate('Message','RS ON'))
                elif flag == 0:
                    self.aw.fujipid.rampsoak = False
                    self.aw.sendmessage(QApplication.translate('Message','RS OFF'))
                else:
                    self.aw.sendmessage(QApplication.translate('Message','RS on HOLD'))
                return True
            self.aw.qmc.adderror(QApplication.translate('Error Message','RampSoak could not be changed'))
            return False
        return False

    # returns True on success, False otherwise
    def setONOFFstandby(self,flag):
        _log.debug('setONOFFstandby(%s)',flag)
        #flag = 0 standby OFF, flag = 1 standby ON (pid off)
        #standby ON (pid off) will reset: rampsoak modes/autotuning/self tuning
        #Fuji PXG
        if self.aw.ser.controlETpid[0] == 0:
            register = self.aw.fujipid.PXG4['runstandby'][1]
        elif self.aw.ser.controlETpid[0] == 1:
            register = self.aw.fujipid.PXR['runstandby'][1]
        elif self.aw.ser.controlETpid[0] == 4:
            register = self.aw.fujipid.PXF['runstandby'][1]
        else:
            return 0
        r = None
        command = None
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(register,6)
            self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,flag)
        else:
            command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],6,register,flag)
            #TX and RX
            r = self.aw.ser.sendFUJIcommand(command,8)
        if self.aw.ser.useModbusPort or (command is not None and r == command):
            if self.aw.ser.controlETpid[0] == 0:
                self.aw.fujipid.PXG4['runstandby'][0] = flag
            elif self.aw.ser.controlETpid[0] == 1:
                self.aw.fujipid.PXR['runstandby'][0] = flag
            elif self.aw.ser.controlETpid[0] == 4:
                self.aw.fujipid.PXF['runstandby'][0] = flag
            return True
        mssg = QApplication.translate('Error Message','Exception:') + ' setONOFFstandby()'
        self.aw.qmc.adderror(mssg)
        return False

    def getONOFFstandby(self):
        if self.aw.ser.controlETpid[0] == 0:
            return self.aw.fujipid.PXG4['runstandby'][0]
        if self.aw.ser.controlETpid[0] == 1:
            return self.aw.fujipid.PXR['runstandby'][0]
        if self.aw.ser.controlETpid[0] == 4:
            return self.aw.fujipid.PXF['runstandby'][0]
        return None

    #sets a new sv value (if silent=False, no output nor event recording is done, if move is True the SV slider is moved)
    def setsv(self,value,silent=False,move=True):
        command = ''
        #Fuji PXG / PXF
        if self.aw.ser.controlETpid[0] in [0,4]:  # Fuji PXG or PXF
            if self.aw.ser.controlETpid[0] == 0:
                reg_dict = self.PXG4
            elif self.aw.ser.controlETpid[0] == 4:
                reg_dict = self.PXF
            else:
                return

            #send command to the current sv (1-7)

#            #-- experimental begin
#            # read the current svN (1-7) being used
#            if self.aw.ser.useModbusPort:
#                reg = self.aw.modbus.address2register(reg_dict["selectsv"][1],3)
#                N = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
#            else:
#                command = self.message2send(self.aw.ser.controlETpid[1],3,reg_dict["selectsv"][1],1)
#                N = self.readoneword(command)
#            if N > 0:
#                reg_dict["selectsv"][0] = N
#            #-- experimental end

            svkey = 'sv'+ str(reg_dict['selectsv'][0]) #current sv
            r = None
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(reg_dict[svkey][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,int(value*10))
            else:
#                value = int(round(value)) # not sure why this is needed, but a FUJI PXF seems not to work without this and value as full floating point numbers!?
# this hack seems not to help
                command = self.message2send(self.aw.ser.controlETpid[1],6,reg_dict[svkey][1],int(value*10))
                r = self.aw.ser.sendFUJIcommand(command,8)
            #check response
            if self.aw.ser.useModbusPort or (r is not None and r == command):
                if not silent:
                    # [Not sure the following will translate or even format properly... Need testing!]
                    message = QApplication.translate('Message','PXG/PXF sv#{0} set to {1}').format(reg_dict['selectsv'][0],'%.1f' % float(value)) # pylint: disable=consider-using-f-string
                    self.aw.sendmessage(message)
                    reg_dict[svkey][0] = value
                    #record command as an Event
                    strcommand = f'SETSV::{float(value):.1f}'
                    self.aw.qmc.DeviceEventRecord(strcommand)
                self.sv = value
                if move:
                    self.aw.moveSVslider(value,setValue=False)
            else:
                # error response
                Rx = ''
                if r is not None and len(r):
                    import binascii
                    Rx = cmd2str(binascii.hexlify(r))
                self.aw.qmc.adderror(QApplication.translate('Error Message','Exception:') + ' setsv(): Rx = ' + Rx)
        #Fuji PXR
        elif self.aw.ser.controlETpid[0] == 1:
            r = None
            if self.aw.ser.useModbusPort:
                reg = self.aw.modbus.address2register(self.aw.fujipid.PXR['sv0'][1],6)
                self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,int(value*10))
            else:
                command = self.message2send(self.aw.ser.controlETpid[1],6,self.aw.fujipid.PXR['sv0'][1],int(value*10))
                r = self.aw.ser.sendFUJIcommand(command,8)
            #check response
            if self.aw.ser.useModbusPort or (r is not None and r == command):
                if not silent:
                    # [Not sure the following will translate or even format properly... Need testing!]
                    message = QApplication.translate('Message','PXR sv set to {0}').format('%.1f' % float(value)) # pylint: disable=consider-using-f-string
                    self.aw.fujipid.PXR['sv0'][0] = value
                    self.aw.sendmessage(message)
                    #record command as an Event
                    strcommand = f'SETSV::{float(value):.1f}'
                    self.aw.qmc.DeviceEventRecord(strcommand)
                self.sv = value
                if move:
                    self.aw.moveSVslider(value,setValue=False)
            else:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Exception:') + ' setPXRsv()')

    #used to set up or down SV by diff degrees from current sv setting; if move is True the SV slider is moved
    def adjustsv(self,diff,move=True):
        currentsv = self.readcurrentsv()
        if currentsv != -1:
            newsv = int((currentsv + diff)*10.)          #multiply by 10 because we use a decimal point

            #   if control pid is fuji PXG or PXF
            if self.aw.ser.controlETpid[0] in [0,4]:
                if self.aw.ser.controlETpid[0] == 0:
                    reg_dict = self.PXG4
                elif self.aw.ser.controlETpid[0] == 4:
                    reg_dict = self.PXF
                else:
                    return
                # read the current svN (1-7) being used

                #-- experimental begin
                # read the current svN (1-7) being used
                if self.aw.ser.useModbusPort:
                    reg = self.aw.modbus.address2register(reg_dict['selectsv'][1],3)
                    N = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
                else:
                    command = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,reg_dict['selectsv'][1],1)
                    N = self.aw.fujipid.readoneword(command)
                if N > 0:
                    reg_dict['selectsv'][0] = N
                #-- experimental end

                svkey = 'sv'+ str(reg_dict['selectsv'][0]) #current sv
                r = None
                if self.aw.ser.useModbusPort:
                    reg = self.aw.modbus.address2register(reg_dict[svkey][1],6)
                    self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,newsv)
                else:
                    command = self.message2send(self.aw.ser.controlETpid[1],6,reg_dict[svkey][1],newsv)
                    r = self.aw.ser.sendFUJIcommand(command,8)
                if self.aw.ser.useModbusPort or (r is not None and len(r) == 8):
                    message = QApplication.translate('Message','SV{0} changed from {1} to {2})').format(str(N),str(currentsv),str(newsv/10.))
                    self.aw.sendmessage(message)
                    reg_dict[svkey][0] = newsv/10
                    #record command as an Event to replay (not binary as it needs to be stored in a text file)
                    strcommand = f'SETSV::{newsv/10.:.1f}'
                    self.aw.qmc.DeviceEventRecord(strcommand)
                    self.aw.lcd6.display(f'{float(newsv/10.):.1f}')
                    if move:
                        self.aw.moveSVslider(newsv/10.,setValue=False)
                else:
                    msg = QApplication.translate('Message','Unable to set sv{0}').format(str(N))
                    self.aw.sendmessage(msg)
            #   or if control pid is fuji PXR
            elif self.aw.ser.controlETpid[0] == 1:
                r = None
                if self.aw.ser.useModbusPort:
                    reg = self.aw.modbus.address2register(self.PXR['sv0'][1],6)
                    self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg,newsv)
                else:
                    command = self.message2send(self.aw.ser.controlETpid[1],6,self.PXR['sv0'][1],newsv)
                    r = self.aw.ser.sendFUJIcommand(command,8)
                if self.aw.ser.useModbusPort or (r is not None and len(r) == 8):
                    message = QApplication.translate('Message','SV changed from {0} to {1}').format(str(currentsv),str(newsv/10.))
                    self.aw.sendmessage(message)
                    self.PXR['sv0'][0] = newsv/10
                    #record command as an Event to replay (not binary as it needs to be stored in a text file)
                    strcommand = f'SETSV::{newsv/10.:.1f}'
                    self.aw.qmc.DeviceEventRecord(strcommand)
                    self.aw.lcd6.display(f'{float(newsv/10.):.1f}')
                    if move:
                        self.aw.moveSVslider(newsv/10.,setValue=False)
                else:
                    self.aw.sendmessage(QApplication.translate('Message','Unable to set sv'))
        else:
            self.aw.sendmessage(QApplication.translate('Message','Unable to set new sv'))

    #format of the input string Command: COMMAND::VALUE1::VALUE2::VALUE3::ETC
    def replay(self,CommandString):
        parts = CommandString.split('::')
        command = parts[0]
        values = parts[1:]
        if command == 'SETSV':
            self.setsv(float(values[0]))
            return
        if command == 'SETRS':
            self.replaysetrs(CommandString)

    #example of command string with four segments (minimum for Fuji PIDs)
    # SETRS::270.0::3::0::SETRS::300.0::3::0::SETRS::350.0::3::0::SETRS::400.0::3::0
    def replaysetrs(self,CommandString):
        segments =CommandString.split('SETRS')
        if len(segments[0]) == 0:
            segments = segments[1:]          #remove first empty [""] list [[""],[etc]]
        if len(segments[-1]) == 0:
            segments = segments[:-1]          #remove last empty [""] list [[etc][""]]
        n = len(segments)
        #if parts is < 4, make it compatible with Fuji PID (4 segments needed)
        if n < 4:
            for _ in range(4-n):
                #last temperature
                lasttemp = segments[-1].split('::')[1]
                #create a string with 4 segments ("SETRS" already removed)
                string = '::' + lasttemp + '::0::0'   #add zero ramp time and zero soak time
                segments.append(string)
        rs = []
        changeflag = 0
        for i in range(n):
            rs.append(segments[i].split('::'))
            if len(rs[i][0]) == 0:          #remove first empty "" [u"",u"300.5",u"3",u"0",u""] if one found
                rs[i] = rs[i][1:]
            if len(rs[i][-1]) == 0:          #remove last empty "" [u"300.5",u"3",u"0",u""] if one found
                rs[i] = rs[i][:-1]
            if len(rs[i]) == 3:
                svkey = 'segment' + str(i+1) + 'sv'
                rampkey = 'segment' + str(i+1) + 'ramp'
                soakkey = 'segment' + str(i+1) + 'soak'
                if self.aw.ser.controlETpid[0] == 0:             #PXG4
                    if not n%4 or n > 16:
                        self.aw.qmc.adderror((QApplication.translate('Error Message','Exception:') + ' PXG4 replaysetrs(): {0}').format(n))
                        return
                    if self.PXG4[svkey][0] != float(rs[i][0]):
                        self.PXG4[svkey][0] = float(rs[i][0])
                        changeflag = 1
                    if self.PXG4[rampkey][0] != int(rs[i][1]):
                        self.PXG4[rampkey][0] = int(rs[i][1])
                        changeflag = 1
                    if self.PXG4[soakkey][0] != int(rs[i][2]):
                        self.PXG4[soakkey][0] = int(rs[i][2])
                        changeflag = 1
                    if changeflag:
                        self.setsegment((i+1), self.PXG4[svkey][0], self.PXG4[rampkey][0] ,self.PXG4[soakkey][0])
                        changeflag = 0
                elif self.aw.ser.controlETpid[0] == 1:           #PXR
                    if not n%4 or n > 8:
                        self.aw.qmc.adderror((QApplication.translate('Error Message','Exception:') + ' PXR replaysetrs(): {0}').format(n))
                        return
                    if self.PXR[svkey][0] != float(rs[i][0]):
                        self.PXR[svkey][0] = float(rs[i][0])
                        changeflag = 1
                    if self.PXR[rampkey][0] != int(rs[i][1]):
                        self.PXR[rampkey][0] = int(rs[i][1])
                        changeflag = 1
                    if self.PXR[soakkey][0] != int(rs[i][2]):
                        self.PXR[soakkey][0] = int(rs[i][2])
                        changeflag = 1
                    if changeflag:
                        self.setsegment((i+1), self.PXR[svkey][0], self.PXR[rampkey][0] ,self.PXR[soakkey][0])
                        changeflag = 0
            else:
                self.aw.qmc.adderror(QApplication.translate('Error Message','Exception:') + ' replaysetrs()')
                return
        #start ramp soak ON
        self.setrampsoak(1)

    def getsegment(self, idn):
        if self.aw.ser.controlETpid[0] == 0:
            reg_dict = self.PXG4
        elif self.aw.ser.controlETpid[0] == 1:
            reg_dict = self.PXR
        elif self.aw.ser.controlETpid[0] == 4:
            reg_dict = self.PXF
        else:
            return
        svkey = 'segment' + str(idn) + 'sv'
        register = reg_dict[svkey][1]
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(register,3)
            sv = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
        else:
            svcommand = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,register,1)
            sv = self.aw.fujipid.readoneword(svcommand)
        if sv == -1:
            return
        reg_dict[svkey][0] = sv/10.              #divide by 10 because the decimal point is not sent by the PID

        rampkey = 'segment' + str(idn) + 'ramp'
        register = reg_dict[rampkey][1]
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(register,3)
            ramp = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
        else:
            rampcommand = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,register,1)
            ramp = self.aw.fujipid.readoneword(rampcommand)

        if ramp == -1:
            return
        reg_dict[rampkey][0] = ramp

        soakkey = 'segment' + str(idn) + 'soak'
        register = reg_dict[soakkey][1]
        if self.aw.ser.useModbusPort:
            reg = self.aw.modbus.address2register(register,3)
            soak = self.aw.modbus.readSingleRegister(self.aw.ser.controlETpid[1],reg,3)
        else:
            soakcommand = self.aw.fujipid.message2send(self.aw.ser.controlETpid[1],3,register,1)
            soak = self.aw.fujipid.readoneword(soakcommand)
        if soak == -1:
            return
        reg_dict[soakkey][0] = soak


    #idn = id number, sv = float set value, ramp = ramp value, soak = soak value
    #used in replaysetrs()
    def setsegment(self,idn,sv,ramp,soak):
        svkey = 'segment' + str(idn) + 'sv'
        rampkey = 'segment' + str(idn) + 'ramp'
        soakkey = 'segment' + str(idn) + 'soak'
        if self.aw.ser.useModbusPort:
            if self.aw.ser.controlETpid[0] == 0:
                reg1 = self.aw.modbus.address2register(self.PXG4[svkey][1],6)
                reg2 = self.aw.modbus.address2register(self.PXG4[rampkey][1],6)
                reg3 = self.aw.modbus.address2register(self.PXG4[soakkey][1],6)
            elif self.aw.ser.controlETpid[0] == 1:
                reg1 = self.aw.modbus.address2register(self.PXR[svkey][1],6)
                reg2 = self.aw.modbus.address2register(self.PXR[rampkey][1],6)
                reg3 = self.aw.modbus.address2register(self.PXR[soakkey][1],6)
            else:
                return
            self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg1,int(sv*10))
            libtime.sleep(0.11) #important time between writings
            self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg2,ramp)
            libtime.sleep(0.11) #important time between writings
            self.aw.modbus.writeSingleRegister(self.aw.ser.controlETpid[1],reg3,soak)
            r1 = r2 = r3 = '        '
        else:
            if self.aw.ser.controlETpid[0] == 0:
                svcommand = self.message2send(self.aw.ser.controlETpid[1],6,self.PXG4[svkey][1],int(sv*10))
                rampcommand = self.message2send(self.aw.ser.controlETpid[1],6,self.PXG4[rampkey][1],ramp)
                soakcommand = self.message2send(self.aw.ser.controlETpid[1],6,self.PXG4[soakkey][1],soak)
            elif self.aw.ser.controlETpid[0] == 1:
                svcommand = self.message2send(self.aw.ser.controlETpid[1],6,self.PXR[svkey][1],int(sv*10))
                rampcommand = self.message2send(self.aw.ser.controlETpid[1],6,self.PXR[rampkey][1],ramp)
                soakcommand = self.message2send(self.aw.ser.controlETpid[1],6,self.PXR[soakkey][1],soak)
            else:
                return
            r1 = self.aw.ser.sendFUJIcommand(svcommand,8)
            libtime.sleep(0.11) #important time between writings
            r2 = self.aw.ser.sendFUJIcommand(rampcommand,8)
            libtime.sleep(0.11) #important time between writings
            r3 = self.aw.ser.sendFUJIcommand(soakcommand,8)
        #check if OK
        if len(r1)!=8 or len(r2)!=8 or len(r3)!=8:
            self.aw.qmc.adderror(QApplication.translate('Error Message','Segment values could not be written into PID'))

    @staticmethod
    def dec2HexRaw(decimal):
        # This method converts a decimal to a raw string appropriate for Fuji serial TX
        # Used to compose serial messages
        Nbytes = []
        while decimal:
            decimal, rem = divmod(decimal, 256)
            Nbytes.append(rem)
        Nbytes.reverse()
        if not Nbytes:
            Nbytes.append(0)
        return decs2string(Nbytes)

    def message2send(self, stationNo, FunctionCode, memory, Nword):
        # This method takes the arguments to compose a Fuji serial command and returns the complete raw string with crc16 included
        # memory must be given as the Resistor Number Engineering unit (example of memory = 41057 )
        #check to see if Nword is < 257. If it is, then add extra zero pad. 2^8 = 256 = 1 byte but 2 bytes always needed to send Nword
        pad1 = self.dec2HexRaw(0) if Nword < 257 else decs2string('')
        part1 = self.dec2HexRaw(stationNo)
        part2 = self.dec2HexRaw(FunctionCode)
        _,r = divmod(memory,10000)
        part3 = self.dec2HexRaw(r - 1)
        part4 = self.dec2HexRaw(Nword)
        datastring = part1 + part2 + part3 + pad1 + part4
        # calculate the crc16 of all this data string
        crc16int = self.fujiCrc16(datastring)
        #convert crc16 to hex string to change the order of the 2 bytes from AB.CD to CD.AB to match Fuji requirements
        crc16hex= hex(crc16int)[2:]
        #we need 4 chars but sometimes we get only three or two because of abbreviations by hex(). Therefore, add "0" if needed.
        ll = 4 - len(crc16hex)
        pad =['','0','00','000']
        crc16hex = pad[ll] + crc16hex
        #change now from AB.CD to CD.AB and convert from hex string to int
        crc16end = int(crc16hex[2:]+crc16hex[:2],16)
        #now convert the crc16 from int to binary
        part5 = self.dec2HexRaw(crc16end)
        #return total sum of binary parts  (assembled message)
        return datastring + part5

    #input string command. Output integer (not binary string); used for example to read temperature or to obtain the value of a variable
    def readoneword(self,command):
        #takes an already formatted command to read 1 word data and returns the response from the pid
        #SEND command and RECEIVE 7 bytes back
        r = self.aw.ser.sendFUJIcommand(command,7)
        if len(r) == 7:
            # EVERYTHINK OK: convert data part binary string to hex representation
            s1 = hex2int(r[3],r[4])
            #conversion from hex to dec
            return s1
        #bad number of RX bytes
        errorcode = QApplication.translate('Error Message','pid.readoneword(): {0} RX bytes received (7 needed) for unit ID={1}').format(len(r),command[0])
        self.aw.qmc.adderror(errorcode)
        return -1

    #FUJICRC16 function calculates the CRC16 of the data. It expects a binary string as input and returns an int
    @staticmethod
    def fujiCrc16(string):
        crc16tab = (0x0000,
                    0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241, 0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
                    0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40, 0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880,
                    0xC841, 0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40, 0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0,
                    0x1C80, 0xDC41, 0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641, 0xD201, 0x12C0, 0x1380, 0xD341, 0x1100,
                    0xD1C1, 0xD081, 0x1040, 0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240, 0x3600, 0xF6C1, 0xF781, 0x3740,
                    0xF501, 0x35C0, 0x3480, 0xF441, 0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41, 0xFA01, 0x3AC0, 0x3B80,
                    0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840, 0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41, 0xEE01, 0x2EC0,
                    0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40, 0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640, 0x2200,
                    0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041, 0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
                    0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441, 0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80,
                    0xAE41, 0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840, 0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0,
                    0x7A80, 0xBA41, 0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40, 0xB401, 0x74C0, 0x7580, 0xB541, 0x7700,
                    0xB7C1, 0xB681, 0x7640, 0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041, 0x5000, 0x90C1, 0x9181, 0x5140,
                    0x9301, 0x53C0, 0x5280, 0x9241, 0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440, 0x9C01, 0x5CC0, 0x5D80,
                    0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40, 0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841, 0x8801, 0x48C0,
                    0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40, 0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41, 0x4400,
                    0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641, 0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040)
        cr=0xFFFF
        for j in string:
            tmp = cr ^(j)
            cr =(cr >> 8)^crc16tab[(tmp & 0xff)]
        return cr


###################################################################################
##########################  ARDUINO CLASS DEFINITION  ############################
###################################################################################

class PIDcontrol():
    __slots__ = [ 'aw', 'pidActive', 'sv', 'pidOnCHARGE', 'createEvents', 'loadRampSoakFromProfile', 'loadRampSoakFromBackground', 'svLen', 'svLabel',
            'svValues', 'svRamps', 'svSoaks', 'svActions', 'svBeeps', 'svDescriptions','svTriggeredAlarms', 'RSLen', 'RS_svLabels', 'RS_svValues', 'RS_svRamps', 'RS_svSoaks',
            'RS_svActions', 'RS_svBeeps', 'RS_svDescriptions', 'svSlider', 'svButtons', 'svMode', 'svLookahead', 'dutySteps', 'svSliderMin', 'svSliderMax', 'svValue',
            'dutyMin', 'dutyMax', 'pidKp', 'pidKi', 'pidKd', 'pOnE', 'pidSource', 'pidCycle', 'pidPositiveTarget', 'pidNegativeTarget', 'invertControl',
            'sv_smoothing_factor', 'sv_decay_weights', 'previous_svs', 'time_pidON', 'current_ramp_segment',  'current_soak_segment', 'ramp_soak_engaged',
            'RS_total_time', 'slider_force_move' ]

    def __init__(self, aw:'ApplicationWindow') -> None:
        self.aw:'ApplicationWindow' = aw
        self.pidActive:bool = False
        self.sv:Optional[float] = None # the last sv send to the Arduino
        #
        self.pidOnCHARGE:bool = False
        self.createEvents:bool = False
        self.loadRampSoakFromProfile:bool = False
        self.loadRampSoakFromBackground:bool = False
        self.svLen:Final[int] = 8 # should stay at 8 for compatibility reasons!
        self.svLabel:str = ''
        self.svValues: List[float]     = [0]*self.svLen      # sv temp as int per 8 channels
        self.svRamps: List[int]        = [0]*self.svLen      # seconds as int per 8 channels
        self.svSoaks: List[int]        = [0]*self.svLen      # seconds as int per 8 channels
        self.svActions: List[int]      = [-1]*self.svLen     # alarm action as int per 8 channels
        self.svBeeps: List[bool]       = [False]*self.svLen  # alarm beep as bool per 8 channels
        self.svDescriptions: List[str] = ['']*self.svLen     # alarm descriptions as string per 8 channels
        #
        self.svTriggeredAlarms = [False]*self.svLen # set to true once the corresponding alarm was triggered
        # extra RS sets:
        self.RSLen:Final[int] = 3 # can be changed to have less or more RSn sets
        self.RS_svLabels: List[str]       = ['']*self.RSLen                  # label of the RS set
        self.RS_svValues: List[List[float]] = [[0]*self.svLen]*self.RSLen      # sv temp as int per 8 channels
        self.RS_svRamps: List[List[int]]  = [[0]*self.svLen]*self.RSLen      # seconds as int per 8 channels
        self.RS_svSoaks: List[List[int]]  = [[0]*self.svLen]*self.RSLen      # seconds as int per 8 channels
        self.RS_svActions: List[List[int]]= [[-1]*self.svLen]*self.RSLen     # alarm action as int per 8 channels
        self.RS_svBeeps: List[List[bool]] = [[False]*self.svLen]*self.RSLen  # alarm beep as bool per 8 channels
        self.RS_svDescriptions: List[List[str]] = [['']*self.svLen]*self.RSLen     # alarm descriptions as string per 8 channels
        #
        self.svSlider:bool = False
        self.svButtons:bool = False
        self.svMode:int = 0 # 0: manual, 1: Ramp/Soak, 2: Follow (background profile)
        self.svLookahead:int = 0
        self.dutySteps:int = 1
        self.svSliderMin:int = 0
        self.svSliderMax:int = 230
        self.svValue:float = 180 # the value in the setSV textinput box of the PID dialog
        self.dutyMin:int = -100
        self.dutyMax:int = 100
        self.pidKp:float = 15.0
        self.pidKi:float = 0.01
        self.pidKd:float = 20.0
        # Proposional on Measurement mode see: http://brettbeauregard.com/blog/2017/06/introducing-proportional-on-measurement/
        self.pOnE:bool = True # True for Proposional on Error mode, False for Proposional on Measurement Mode
        # pidSource
        #   either the TC4 input channel from [1,..,4] if self.qmc.device == 19 (Arduino/TC4)
        #   in all other cases (HOTTOP, MODBUS,..), 1 is interpreted as BT and 2 as ET, 3 as 0xT1, 4 as 0xT2, 5 as 1xT1, ...
        self.pidSource:int = 1
        self.pidCycle:int = 1000
        # the positive target should increase with positive PID duty
        self.pidPositiveTarget:int = 0 # one of [0,1,..,4] with 0: None, 1,..,4: for slider event 1-4
        # the negative target should decrease with negative PID duty
        self.pidNegativeTarget:int = 0 # one of [0,1,..,4] with 0: None, 1,..,4: for slider event 1-4
        # if invertControl is True, a PID duty of 100% delivers 0% positive duty and a 0% PID duty delivers 100% positive duty
        self.invertControl:bool = False
        # PID sv smoothing
        self.sv_smoothing_factor:int = 0 # off if 0
        self.sv_decay_weights:Optional[List[float]] = None
        self.previous_svs:List[float] = []
        # time @ PID ON
        self.time_pidON:float = 0 # in monitoring mode, ramp-soak times are interperted w.r.t. the time after the PID was turned on and not the time after CHARGE as during recording
        self.current_ramp_segment:int = 0 # the RS segment currently active. Note that this is 1 based, 0 indicates that no segment has started yet
        self.current_soak_segment:int = 0 # the RS segment currently active. Note that this is 1 based, 0 indicates that no segment has started yet
        self.ramp_soak_engaged:int = 1 # set to 0, disengaged, after the RS pattern was processed fully
        self.RS_total_time:float = 0 # holds the total time of the current Ramp/Soak pattern

        self.slider_force_move:bool = True # if True move the slider independent of the slider position to fire slider action!

    @staticmethod
    def RStotalTime(ramps:List[int], soaks:List[int]) -> int:
        return sum(ramps) + sum(soaks)

    # returns 1 (True) if an external PID controller is in use (MODBUS or TC4 PID firmware)
    # and 0 (False) if the internal software PID is in charge
    # the returned value indicates the type of external PID control:
    #  0: internal PID
    #  1: MODBUS
    #  2: S7
    #  3: TC4
    #  4: Kaleido
    def externalPIDControl(self) -> int:
        # TC4 with PID firmware or MODBUS and SV register set or S7 and SV area set
        if self.aw.modbus.PID_slave_ID != 0:
            return 1
        if self.aw.s7.PID_area != 0:
            return 2
        if (self.aw.qmc.device == 19 and self.aw.qmc.PIDbuttonflag):
            return 3
        if (self.aw.qmc.device == 138 and self.aw.kaleidoPID):
            return 4
        return 0

    # v is from [-min,max]
    def setEnergy(self, v:float) -> None:
        try:
            if self.aw.pidcontrol.pidPositiveTarget:
                slidernr = self.aw.pidcontrol.pidPositiveTarget - 1
                vp = min(100,max(0,int(round(abs(100 - v) if self.aw.pidcontrol.invertControl else v))))
                # we need to map the duty [0%,100%] to the [slidermin,slidermax] range
                heat = int(round(float(numpy.interp(vp,[0,100],[self.aw.eventslidermin[slidernr],self.aw.eventslidermax[slidernr]]))))
                heat = self.aw.applySliderStepSize(slidernr, heat) # quantify by slider step size
                self.aw.addEventSignal.emit(heat,slidernr,self.createEvents,True,self.slider_force_move)
                self.aw.qmc.slider_force_move = False
            if self.aw.pidcontrol.pidNegativeTarget:
                slidernr = self.aw.pidcontrol.pidNegativeTarget - 1
                vn = min(0,max(-100,int(round(0 - v if self.aw.pidcontrol.invertControl else v))))
                # we need to map the duty [0%,-100%] to the [slidermin,slidermax] range
                cool = int(round(float(numpy.interp(vn,[-100,0],[self.aw.eventslidermax[slidernr],self.aw.eventslidermin[slidernr]]))))
                cool = self.aw.applySliderStepSize(slidernr, cool) # quantify by slider step size
                self.aw.addEventSignal.emit(cool,slidernr,self.createEvents,True,self.slider_force_move)
                self.slider_force_move = False
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    def conv2celsius(self) -> None:
        try:
            self.aw.qmc.rampSoakSemaphore.acquire(1)
            self.svValue = int(round(fromFtoC(self.svValue)))
            self.svSliderMin = int(round(fromFtoC(self.svSliderMin)))
            self.svSliderMax = int(round(fromFtoC(self.svSliderMax)))
            # establish ne limits on sliders
            self.aw.sliderSV.setMinimum(self.svSliderMin)
            self.aw.sliderSV.setMaximum(self.svSliderMax)
            self.aw.moveSVslider(self.svValue,setValue=False)
            self.pidKp = self.pidKp * (9/5.)
            self.pidKi = self.pidKi * (9/5.)
            self.pidKd = self.pidKd * (9/5.)
            for i in range(len(self.svValues)): # pylint: disable=consider-using-enumerate
                if self.svValues[i] != 0:
                    self.svValues[i] = fromFtoC(self.svValues[i])
            for n in range(len(self.RS_svValues)): # pylint: disable=consider-using-enumerate
                for j in range(len(self.RS_svValues[n])):
                    if self.RS_svValues[n][j] != 0:
                        self.RS_svValues[n][j] = fromFtoC(self.RS_svValues[n][j])
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if self.aw.qmc.rampSoakSemaphore.available() < 1:
                self.aw.qmc.rampSoakSemaphore.release(1)

    def conv2fahrenheit(self) -> None:
        try:
            self.aw.qmc.rampSoakSemaphore.acquire(1)
            self.svValue = fromCtoF(self.svValue)
            self.svSliderMin = int(round(fromCtoF(self.svSliderMin)))
            self.svSliderMax = int(round(fromCtoF(self.svSliderMax)))
            # establish ne limits on sliders
            self.aw.sliderSV.setMinimum(int(round(self.svSliderMin)))
            self.aw.sliderSV.setMaximum(int(round(self.svSliderMax)))
            self.aw.moveSVslider(self.svValue,setValue=False)
            self.pidKp = self.pidKp / (9/5.)
            self.pidKi = self.pidKi / (9/5.)
            self.pidKd = self.pidKd / (9/5.)
            for i in range(len(self.svValues)): # pylint: disable=consider-using-enumerate
                if self.svValues[i] != 0:
                    self.svValues[i] = fromCtoF(self.svValues[i])
            for n in range(len(self.RS_svValues)): # pylint: disable=consider-using-enumerate
                for j in range(len(self.RS_svValues[n])): # pylint: disable=consider-using-enumerate
                    if self.RS_svValues[n][j] != 0:
                        self.RS_svValues[n][j] = fromCtoF(self.RS_svValues[n][j])
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if self.aw.qmc.rampSoakSemaphore.available() < 1:
                self.aw.qmc.rampSoakSemaphore.release(1)

    def togglePID(self) -> None:
        if self.pidActive:
            self.pidOff()
        else:
            self.pidOn()

    # initializes the PID mode on PID ON and switch of mode
    def pidModeInit(self) -> None:
        if self.aw.qmc.flagon:
            self.current_ramp_segment = 0
            self.current_soak_segment = 0
            self.ramp_soak_engaged = 1
            self.RS_total_time = self.RStotalTime(self.svRamps,self.svSoaks)
            self.svTriggeredAlarms = [False]*self.svLen

            if self.aw.qmc.flagstart or len(self.aw.qmc.on_timex)<1:
                self.time_pidON = 0
            else:
                self.time_pidON = self.aw.qmc.on_timex[-1]
                if self.svMode == 1:
                    # turn the timer LCD color blue if in RS mode and not recording
                    self.aw.setTimerColor('rstimer')

    # the internal software PID should be configured on ON, but not be activated yet to warm it up
    def confSoftwarePID(self) -> None:
        if self.aw.pidcontrol.externalPIDControl() not in [1, 2, 4] and not(self.aw.qmc.device == 19 and self.aw.qmc.PIDbuttonflag) and self.aw.qmc.Controlbuttonflag:
            # software PID
            self.aw.qmc.pid.setPID(self.pidKp,self.pidKi,self.pidKd,self.pOnE)
            self.aw.qmc.pid.setLimits((-100 if self.aw.pidcontrol.pidNegativeTarget else 0),(100 if self.aw.pidcontrol.pidPositiveTarget else 0))
            self.aw.qmc.pid.setDutySteps(self.aw.pidcontrol.dutySteps)
            self.aw.qmc.pid.setDutyMin(self.aw.pidcontrol.dutyMin)
            self.aw.qmc.pid.setDutyMax(self.aw.pidcontrol.dutyMax)
            self.aw.qmc.pid.setControl(self.aw.pidcontrol.setEnergy)
            if self.aw.pidcontrol.svMode == 0:
                self.aw.pidcontrol.setSV(self.aw.sliderSV.value())

    # if send_command is False, the pidOn command is not forwarded to the external PID (TC4, Kaleido, ..)
    def pidOn(self, send_command:bool = True) -> None:
        if self.aw.qmc.flagon:
            if not self.pidActive:
                self.aw.sendmessage(QApplication.translate('StatusBar','PID ON'))
            self.pidModeInit()

            self.slider_force_move = True
            # TC4 hardware PID
            # MODBUS hardware PID
            if (self.aw.pidcontrol.externalPIDControl() == 1 and self.aw.modbus.PID_ON_action and self.aw.modbus.PID_ON_action != ''):
                self.aw.eventaction(4,self.aw.modbus.PID_ON_action)
                self.pidActive = True
                self.aw.buttonCONTROL.setStyleSheet(self.aw.pushbuttonstyles['PIDactive'])
            # S7 hardware PID
            elif (self.aw.pidcontrol.externalPIDControl() == 2 and self.aw.s7.PID_ON_action and self.aw.s7.PID_ON_action != ''):
                self.aw.eventaction(15,self.aw.s7.PID_ON_action)
                self.pidActive = True
                self.aw.buttonCONTROL.setStyleSheet(self.aw.pushbuttonstyles['PIDactive'])
            elif self.aw.qmc.device == 19 and self.aw.qmc.PIDbuttonflag: # ArduinoTC4 firmware PID
                if send_command and self.aw.ser.ArduinoIsInitialized:
                    self.confPID(self.pidKp,self.pidKi,self.pidKd,self.pidSource,self.pidCycle,self.aw.pidcontrol.pOnE) # first configure PID according to the actual settings
                    try:
                        #### lock shared resources #####
                        self.aw.ser.COMsemaphore.acquire(1)
                        if self.aw.ser.SP.is_open:
                            duty_min = min(100,max(0,self.aw.pidcontrol.dutyMin))
                            duty_max = min(100,max(0,self.aw.pidcontrol.dutyMax))
                            self.aw.ser.SP.write(str2cmd('PID;LIMIT;' + str(duty_min) + ';' + str(duty_max) + '\n'))
                            self.aw.ser.SP.write(str2cmd('PID;ON\n'))
                            self.pidActive = True
                            self.aw.buttonCONTROL.setStyleSheet(self.aw.pushbuttonstyles['PIDactive'])
                            self.aw.sendmessage(QApplication.translate('Message','PID turned on'))
                    finally:
                        if self.aw.ser.COMsemaphore.available() < 1:
                            self.aw.ser.COMsemaphore.release(1)
            elif self.aw.qmc.Controlbuttonflag and self.externalPIDControl() == 4 and self.aw.kaleido is not None:
                # Kaleido PID
                if send_command:
                    self.aw.kaleido.pidON()
                self.pidActive = True
                self.aw.qmc.pid.on()
                self.aw.buttonCONTROL.setStyleSheet(self.aw.pushbuttonstyles['PIDactive'])
            elif self.aw.qmc.Controlbuttonflag:
                # software PID
                self.aw.qmc.pid.setPID(self.pidKp,self.pidKi,self.pidKd,self.pOnE)
                self.aw.qmc.pid.setLimits((-100 if self.aw.pidcontrol.pidNegativeTarget else 0),(100 if self.aw.pidcontrol.pidPositiveTarget else 0))
                self.aw.qmc.pid.setDutySteps(self.aw.pidcontrol.dutySteps)
                self.aw.qmc.pid.setDutyMin(self.aw.pidcontrol.dutyMin)
                self.aw.qmc.pid.setDutyMax(self.aw.pidcontrol.dutyMax)
                self.aw.qmc.pid.setControl(self.aw.pidcontrol.setEnergy)
                if self.aw.pidcontrol.svMode == 0:
                    self.aw.pidcontrol.setSV(self.aw.sliderSV.value())
                self.pidActive = True
                self.aw.qmc.pid.on()
                self.aw.buttonCONTROL.setStyleSheet(self.aw.pushbuttonstyles['PIDactive'])
            if self.sv is None and self.svMode == 0: # only in manual SV mode we initialize the SV on PID ON
                self.setSV(self.svValue)

    # if send_command is False, the pidOff command is not forwarded to the external PID (TC4, Kaleido, ..)
    def pidOff(self, send_command:bool = True) -> None:
        if self.pidActive:
            self.aw.sendmessage(QApplication.translate('Message','PID OFF'))
        self.aw.setTimerColor('timer')
        if self.aw.qmc.flagon and not self.aw.qmc.flagstart:
            self.aw.qmc.setLCDtime(0)
        # MODBUS hardware PID
        if (self.aw.pidcontrol.externalPIDControl() == 1 and self.aw.modbus.PID_OFF_action and self.aw.modbus.PID_OFF_action != ''):
            self.aw.eventaction(4,self.aw.modbus.PID_OFF_action)
            if not self.aw.HottopControlActive:
                self.aw.buttonCONTROL.setStyleSheet(self.aw.pushbuttonstyles['PID'])
            self.pidActive = False
        # S7 hardware PID
        elif (self.aw.pidcontrol.externalPIDControl() == 2 and self.aw.s7.PID_OFF_action and self.aw.s7.PID_OFF_action != ''):
            self.aw.eventaction(15,self.aw.s7.PID_OFF_action)
            if not self.aw.HottopControlActive:
                self.aw.buttonCONTROL.setStyleSheet(self.aw.pushbuttonstyles['PID'])
            self.pidActive = False
        # TC4 hardware PID
        elif self.aw.qmc.device == 19 and self.aw.qmc.PIDbuttonflag and self.aw.qmc.Controlbuttonflag: # ArduinoTC4 firmware PID
            if send_command and self.aw.ser.ArduinoIsInitialized:
                try:
                    #### lock shared resources #####
                    self.aw.ser.COMsemaphore.acquire(1)
                    if self.aw.ser.SP.is_open:
                        self.aw.ser.SP.reset_input_buffer() # self.aw.ser.SP.flushInput() # deprecated in v3
                        self.aw.ser.SP.reset_output_buffer() # self.aw.ser.SP.flushOutput() # deprecated in v3
                        self.aw.ser.SP.write(str2cmd('PID;OFF\n'))
                        self.aw.sendmessage(QApplication.translate('Message','PID turned off'))
                finally:
                    if self.aw.ser.COMsemaphore.available() < 1:
                        self.aw.ser.COMsemaphore.release(1)
                if not self.aw.HottopControlActive:
                    self.aw.buttonCONTROL.setStyleSheet(self.aw.pushbuttonstyles['PID'])
                self.pidActive = False
        elif self.aw.qmc.Controlbuttonflag and self.externalPIDControl() == 4 and self.aw.kaleido is not None:
            # Kaleido PID
            if send_command:
                self.aw.kaleido.pidOFF()
            self.pidActive = False
            self.aw.qmc.pid.off()
            self.aw.buttonCONTROL.setStyleSheet(self.aw.pushbuttonstyles['PID'])
        elif self.aw.qmc.Controlbuttonflag:
            # software PID
            self.aw.qmc.pid.setControl(lambda _: None)
            self.pidActive = False
            self.aw.qmc.pid.off()
            if not self.aw.HottopControlActive:
                self.aw.buttonCONTROL.setStyleSheet(self.aw.pushbuttonstyles['PID'])

    @pyqtSlot(int)
    def sliderMinValueChanged(self, i:int) -> None:
        self.svSliderMin = i
        self.aw.sliderSV.setMinimum(self.svSliderMin)

    @pyqtSlot(int)
    def sliderMaxValueChanged(self, i:int) -> None:
        self.svSliderMax = i
        self.aw.sliderSV.setMaximum(self.svSliderMax)

    # returns SV (or None) wrt. to the ramp-soak table and the given time t
    # (used only internally)
    def svRampSoak(self, t:float) -> Optional[float]:
        try:
            self.aw.qmc.rampSoakSemaphore.acquire(1)
            if self.ramp_soak_engaged == 0:
                return None
            if self.aw.qmc.flagon and not self.aw.qmc.flagstart:
                self.aw.qmc.setLCDtime(self.RS_total_time-t)
            segment_end_time = 0 # the (end) time of the segments
            prev_segment_end_time = 0 # the (end) time of the previous segment
            segment_start_sv = 0. # the (target) sv of the segment
            prev_segment_start_sv = 0. # the (target) sv of the previous segment
            for i, v in enumerate(self.svValues):
                # Ramp
                if self.svRamps[i] != 0:
                    segment_end_time = segment_end_time + self.svRamps[i]
                    segment_start_sv = v
                    if segment_end_time > t:
                        # t is within the current segment
                        k = float(segment_start_sv - prev_segment_start_sv) / float(segment_end_time - prev_segment_end_time)
                        if self.current_ramp_segment != i+1:
                            self.aw.sendmessage(QApplication.translate('Message',f'Ramp {i+1}: in {stringfromseconds(self.svRamps[i])} to SV {int(round(v))}'))
                            self.current_ramp_segment = i+1
                        return prev_segment_start_sv + k*(t - prev_segment_end_time)
                prev_segment_end_time = segment_end_time
                prev_segment_start_sv = segment_start_sv
                # Soak
                if self.svSoaks[i] != 0:
                    segment_end_time = segment_end_time + self.svSoaks[i]
                    segment_start_sv = v
                    if segment_end_time > t:
                        prev_segment_start_sv = segment_start_sv # ensure that the segment sv is set even then the segments ramp is 00:00
                        # t is within the current segment
                        if self.current_soak_segment != i+1:
                            self.current_soak_segment = i+1
                            self.aw.sendmessage(QApplication.translate('Message',f'Soak {i+1}: for {stringfromseconds(self.svSoaks[i])} at SV {int(round(v))}'))
                        return prev_segment_start_sv
                prev_segment_end_time = segment_end_time
                prev_segment_start_sv = segment_start_sv
                if (self.current_ramp_segment > i or self.current_soak_segment > 1) and not self.svTriggeredAlarms[i]:
                    self.svTriggeredAlarms[i] = True
                    if self.svActions[i] > -1:
                        self.aw.qmc.processAlarmSignal.emit(0,self.svBeeps[i],self.svActions[i],self.svDescriptions[i])
            self.aw.sendmessage(QApplication.translate('Message','Ramp/Soak pattern finished'))
            self.aw.qmc.setLCDtime(0)
            self.ramp_soak_engaged = 0 # stop the ramp/soak process
            return None
        finally:
            if self.aw.qmc.rampSoakSemaphore.available() < 1:
                self.aw.qmc.rampSoakSemaphore.release(1)

    def smooth_sv(self, sv:float) -> float:
        if self.sv_smoothing_factor:
            # create or update smoothing decay weights
            if self.sv_decay_weights is None or len(self.sv_decay_weights) != self.sv_smoothing_factor: # recompute only on changes
                self.sv_decay_weights = list(numpy.arange(1,self.sv_smoothing_factor+1))
            # add new value
            self.previous_svs.append(sv)
            # throw away superfluous values
            self.previous_svs = self.previous_svs[-self.sv_smoothing_factor:]
            # compute smoothed output
            if len(self.previous_svs) >= self.sv_smoothing_factor:
                return float(numpy.average(self.previous_svs,weights=self.sv_decay_weights))
        return sv # no smoothing yet

    # returns None if in manual mode or no other sv (via ramp/soak or follow mode) defined
    def calcSV(self, tx:float) -> Optional[float]:
        if self.svMode == 1:
            # Ramp/Soak mode
            # actual time (after CHARGE) on recording and time after PID ON on monitoring:
            return self.svRampSoak(tx - self.time_pidON)
        if self.svMode == 2 and self.aw.qmc.background:
            # Follow Background mode
            if self.aw.qmc.device == 19 and self.aw.pidcontrol.externalPIDControl(): # in case we run TC4 with the PIDfirmware
                if int(self.aw.ser.arduinoETChannel) == self.pidSource: # we observe the ET
                    followCurveNr = 2
                elif int(self.aw.ser.arduinoBTChannel) == self.pidSource: # we observe the BT
                    followCurveNr = 1
                else:
                    # we do not know which extra background device curve holds the selcted PID source temperatures
                    return None
            else:
                followCurveNr = self.pidSource
            # followCurveNr indicates which curve the PID should follow (take the SV from)
            #  1: BT, 2: ET, 3: as 0xT1, 4: as 0xT2, 5: as 1xT1, ...

            if self.aw.qmc.timeindex[6] > 0: # after DROP, the SV configured in the dialog is returned (min/maxed)
                return max(self.aw.pidcontrol.svSliderMin, min(self.aw.pidcontrol.svSliderMax, self.aw.pidcontrol.svValue))
            if self.aw.qmc.timeindex[0] < 0: # before CHARGE, the CHARGE temp of the background profile is returned
                if self.aw.qmc.timeindexB[0] < 0:
                    # no CHARGE in background, return manual SV
                    return max(self.aw.pidcontrol.svSliderMin,(min(self.aw.pidcontrol.svSliderMax,self.aw.pidcontrol.svValue)))
                # if background contains a CHARGE event
                if followCurveNr == 1: # we observe the BT
                    res = self.aw.qmc.backgroundBTat(self.aw.qmc.timeB[self.aw.qmc.timeindexB[0]]) # approximated background
                elif followCurveNr == 2: # we observe the ET
                    res = self.aw.qmc.backgroundETat(self.aw.qmc.timeB[self.aw.qmc.timeindexB[0]]) # approximated background
                elif followCurveNr>2: # we observe an extra curve
                    res = self.aw.qmc.backgroundXTat(followCurveNr-3, self.aw.qmc.timeB[self.aw.qmc.timeindexB[0]])
                else:
                    return None
                if res == -1:
                    return None # no background value for that time point
                return self.smooth_sv(res)
            if ((not self.aw.qmc.timeB or tx+self.svLookahead > self.aw.qmc.timeB[-1]) or (self.aw.qmc.timeindexB[6] > 0 and tx+self.svLookahead > self.aw.qmc.timeB[self.aw.qmc.timeindexB[6]])):
                # if tx+self.svLookahead > last background data or background has a DROP and tx+self.svLookahead index is beyond that DROP index
                return None # "deactivate" background follow mode
            if followCurveNr == 1: # we observe the BT
                res = self.aw.qmc.backgroundSmoothedBTat(tx + self.svLookahead) # smoothed and approximated background
            elif followCurveNr == 2: # we observe the ET
                res = self.aw.qmc.backgroundSmoothedETat(tx + self.svLookahead) # smoothed and approximated background
            elif followCurveNr>2: # we observe an extra curve
                res = self.aw.qmc.backgroundXTat(followCurveNr-3, tx + self.svLookahead, smoothed=True)
            else:
                return None
            if res == -1:
                return None
            return self.smooth_sv(res)
        # return None in manual mode
        return None

    def setDutySteps(self, dutySteps:int) -> None:
        if self.aw.qmc.Controlbuttonflag and not self.aw.pidcontrol.externalPIDControl():
            self.aw.qmc.pid.setDutySteps(dutySteps)


    def setSV(self, sv:float, move:bool = True, init:bool = False) -> None:
#        if not move:
#            self.aw.sendmessage(QApplication.translate("Message","SV set to %s"%sv))
        if self.aw.pidcontrol.externalPIDControl() == 1:
            # MODBUS PID and Control ticked
            self.sv = max(0,sv)
            if move:
                self.aw.moveSVslider(sv,setValue=True)
            self.aw.modbus.setTarget(sv)
            self.sv = sv # remember last sv
        elif self.aw.pidcontrol.externalPIDControl() == 2:
            # S7 PID and Control ticked
            self.sv = max(0,sv)
            if move:
                self.aw.moveSVslider(sv,setValue=True)
            self.aw.s7.setTarget(sv,self.aw.s7.SVmultiplier)
            self.sv = sv # remember last sv
        elif self.aw.qmc.device == 19 and self.aw.pidcontrol.externalPIDControl():
            # ArduinoTC4 firmware PID
            if self.aw.ser.ArduinoIsInitialized:
                sv = max(0,self.aw.float2float(sv,2))
                if self.sv != sv: # nothing to do (avoid loops via moveslider!)
                    if move:
                        self.aw.moveSVslider(sv,setValue=True) # only move the slider
                        self.sv = sv # remember last sv
                    try:
                        #### lock shared resources #####
                        self.aw.ser.COMsemaphore.acquire(1)
                        if self.aw.ser.SP.is_open:
                            self.aw.ser.SP.reset_input_buffer() # self.aw.ser.SP.flushInput() # deprecated in v3
                            self.aw.ser.SP.reset_output_buffer() # self.aw.ser.SP.flushOutput() # deprecated in v3
                            self.aw.ser.SP.write(str2cmd('PID;SV;' + str(sv) +'\n'))
                            self.sv = sv # remember last sv
                    finally:
                        if self.aw.ser.COMsemaphore.available() < 1:
                            self.aw.ser.COMsemaphore.release(1)
        elif self.externalPIDControl() == 4 and self.aw.kaleido is not None:
            # Kaleido PID
            if move and self.aw.pidcontrol.svSlider:
                self.aw.moveSVslider(sv,setValue=True)
            self.aw.kaleido.setSV(sv)
            self.sv = sv # remember last sv
        elif self.aw.qmc.Controlbuttonflag:
            # in all other cases if the "Control" flag is ticked: software PID
            if move and self.aw.pidcontrol.svSlider:
                self.aw.moveSVslider(sv,setValue=True)
            self.aw.qmc.pid.setTarget(sv,init=init)
            self.sv = sv # remember last sv

    # set RS patterns from one of the RS sets
    def setRSpattern(self, n:int) -> None:
        try:
            self.aw.qmc.rampSoakSemaphore.acquire(1)
            if n < self.RSLen:
                self.svLabel = self.RS_svLabels[n]
                self.svValues = self.RS_svValues[n]
                self.svRamps = self.RS_svRamps[n]
                self.svSoaks = self.RS_svSoaks[n]
                self.svActions = self.RS_svActions[n]
                self.svBeeps = self.RS_svBeeps[n]
                self.svDescriptions = self.RS_svDescriptions[n]
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if self.aw.qmc.rampSoakSemaphore.available() < 1:
                self.aw.qmc.rampSoakSemaphore.release(1)

    # returns the first RS patterrn idx with label or None
    def findRSset(self, label:str) -> Optional[int]:
        try:
            self.aw.qmc.rampSoakSemaphore.acquire(1)
            return self.RS_svLabels.index(label)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            return None
        finally:
            if self.aw.qmc.rampSoakSemaphore.available() < 1:
                self.aw.qmc.rampSoakSemaphore.release(1)

    def adjustsv(self, diff:float) -> None:
        if self.sv is None or self.sv<0:
            self.sv = 0
        self.setSV(self.sv + diff,move=True)

    def activateSVSlider(self, flag:bool) -> None:
        if flag:
            self.aw.sliderGrpBoxSV.setVisible(True)
            self.aw.sliderSV.blockSignals(True)
            self.aw.sliderSV.setMinimum(self.svSliderMin)
            self.aw.sliderSV.setMaximum(self.svSliderMax)
            # we set the SV slider/lcd to the last SV issues or the minimum
            if self.aw.pidcontrol.sv is not None:
                sv = self.aw.pidcontrol.sv
            else:
                sv = min(self.svSliderMax, max(self.svSliderMin, self.aw.pidcontrol.svValue))
            sv = int(round(sv))
            self.aw.updateSVSliderLCD(sv)
            self.aw.sliderSV.setValue(sv)
            self.aw.sliderSV.blockSignals(False)
            self.svSlider = True
            self.aw.slidersAction.setEnabled(True)
        else:
            self.aw.sliderGrpBoxSV.setVisible(False)
            self.svSlider = False
            self.aw.slidersAction.setEnabled(any(self.aw.eventslidervisibilities))

    def activateONOFFeasySV(self, flag:bool) -> None:
        if flag:
            if self.aw.qmc.flagon:
                self.aw.buttonSVp5.setVisible(True)
                self.aw.buttonSVp10.setVisible(True)
                self.aw.buttonSVp20.setVisible(True)
                self.aw.buttonSVm20.setVisible(True)
                self.aw.buttonSVm10.setVisible(True)
                self.aw.buttonSVm5.setVisible(True)
        else:
            self.aw.buttonSVp5.setVisible(False)
            self.aw.buttonSVp10.setVisible(False)
            self.aw.buttonSVp20.setVisible(False)
            self.aw.buttonSVm20.setVisible(False)
            self.aw.buttonSVm10.setVisible(False)
            self.aw.buttonSVm5.setVisible(False)

    # just store the p-i-d configuration
    def setPID(self, kp:float, ki:float, kd:float, source:Optional[int] = None, cycle:Optional[int] = None, pOnE:bool = True) -> None:
        self.pidKp = kp
        self.pidKi = ki
        self.pidKd = kd
        self.pOnE = pOnE
        if source is not None:
            self.pidSource = source
        if cycle is not None:
            self.pidCycle = cycle

    # send conf to connected PID
    def confPID(self, kp:float, ki:float, kd:float, source:Optional[int] = None, cycle:Optional[int] = None, pOnE:bool = True) -> None:
        if self.aw.pidcontrol.externalPIDControl() == 1: # MODBUS (external) Control active
            self.aw.modbus.setPID(kp,ki,kd)
            self.pidKp = kp
            self.pidKi = ki
            self.pidKd = kd
            self.aw.sendmessage(QApplication.translate('Message','p-i-d values updated'))
        elif self.aw.pidcontrol.externalPIDControl() == 2: # S7 (external) Control active
            self.aw.s7.setPID(kp,ki,kd,self.aw.s7.PIDmultiplier)
            self.pidKp = kp
            self.pidKi = ki
            self.pidKd = kd
            self.aw.sendmessage(QApplication.translate('Message','p-i-d values updated'))
        elif self.aw.qmc.device == 19 and self.aw.pidcontrol.externalPIDControl(): # ArduinoTC4 firmware PID
            self.pidKp = kp
            self.pidKi = ki
            self.pidKd = kd
            self.pOnE = pOnE
            if source is not None and source in [1,2,3,4]:
                self.pidSource = source
            if self.aw.ser.ArduinoIsInitialized:
                try:
                    #### lock shared resources #####
                    self.aw.ser.COMsemaphore.acquire(1)
                    if self.aw.ser.SP.is_open:
                        self.aw.ser.SP.reset_input_buffer() # self.aw.ser.SP.flushInput() # deprecated in v3
                        self.aw.ser.SP.reset_output_buffer() # self.aw.ser.SP.flushOutput() # deprecated in v3
                        if pOnE:
                            self.aw.ser.SP.write(str2cmd('PID;T;' + str(kp) + ';' + str(ki) + ';' + str(kd) + '\n'))
                        else:
                            self.aw.ser.SP.write(str2cmd('PID;T_POM;' + str(kp) + ';' + str(ki) + ';' + str(kd) + '\n'))
                        if source is not None and source in [1,2,3,4]:
                            libtime.sleep(.03)
                            self.aw.ser.SP.write(str2cmd('PID;CHAN;' + str(source) + '\n'))
                        if cycle is not None:
                            libtime.sleep(.03)
                            self.aw.ser.SP.write(str2cmd('PID;CT;' + str(cycle) + '\n'))
                        self.aw.sendmessage(QApplication.translate('Message','p-i-d values updated'))
                finally:
                    if self.aw.ser.COMsemaphore.available() < 1:
                        self.aw.ser.COMsemaphore.release(1)
        elif self.aw.qmc.Controlbuttonflag: # in all other cases if the "Control" flag is ticked
            self.aw.qmc.pid.setPID(kp,ki,kd,pOnE)
            self.pidKp = kp
            self.pidKi = ki
            self.pidKd = kd
            self.pOnE = pOnE
            self.aw.qmc.pid.setLimits((-100 if self.aw.pidcontrol.pidNegativeTarget else 0),(100 if self.aw.pidcontrol.pidPositiveTarget else 0))
            if source is not None and source>0:
                self.pidSource = source
            self.aw.sendmessage(QApplication.translate('Message','p-i-d values updated'))

###################################################################################
##########################  DTA PID CLASS DEFINITION  ############################
###################################################################################
# documentation
# http://www.deltaww.hu/homersekletszabalyozok/DTA_series_temperature_controller_instruction_sheet_English.pdf
class DtaPID():
    def __init__(self,aw) -> None:
        self.aw = aw

        #refer to Delta instruction manual for more information
        #dictionary "KEY": [VALUE,ASCII_MEMORY_ADDRESS]  note: address contains hex alpha characters
        self.dtamem={
                  'pv': [0,'4700'],             # process value (temperature reading)
                  'sv': [100.0,'4701'],         # set point
                  'p': [5,'4708'],              # p value 0-9999
                  'i': [240,'4709'],            # i value 0-9999
                  'd': [60,'470A'],             # d value 0-9999
                  'duty' : [0,'471D'],          # duty
                  'sensortype': [0,'4710'],     # 0 = K type1; 1 = K type2; 2 = J type1; 3 = J type2
                                                # 4 = T type1; 5 = T type2; 6 = E ; 7 = N; 8 = R; 9 = S; 10 = B
                                                # 11 = JPT100 type1; 12 = JPT100 type2; 13 = PT100 type1; 14 = PT100 type2
                                                # 15 = PT100 type3; 16 = L ; 17 = U; 18 = Txk
                  'controlmethod':[0,'4711'],   # 0 = pid; 1 = ON/OFF; 2 = manual
                  'units':[1,'4717'],           # units C = 1; F = 2
                  'controlsetting':[1,'4719'],  # 1=Run; 0 = Stop
                  'error':[0,'472B']            # note: read only memory. Values:
                                                # 0 = Normal,1 = Initial process; 2 = Initial status;
                                                # 3 = sensor not connected; 4 = sensor input error
                                                # 5 = Exceeds max temperature; 6 = Number Internal error
                                                # 7 EEPROM error
                  }
    #command  string = ID (ADR)+ FUNCTION (CMD) + ADDRESS + NDATA + LRC_CHK
    def writeDTE(self,value,DTAaddress):
        newsv = hex(int(abs(float(str(value)))))[2:].upper()
        slaveID = self.aw.ser.controlETpid[1]
        if self.aw.ser.controlETpid[0] != 2: # control pid is not a DTA PID
            slaveID = self.aw.ser.readBTpid[1]
        command = self.aw.dtapid.message2send(slaveID,6,str(DTAaddress),newsv)
        self.aw.ser.sendDTAcommand(command)

    def message2send(self,unitID,FUNCTION,ADDRESS, NDATA):
        #compose command
        string_unitID = str(unitID).zfill(2)
        string_FUNCTION = str(FUNCTION).zfill(2)
        string_ADDRESS = ADDRESS                 #ADDRESS is a 4 char string
        string_NDATA = str(NDATA).zfill(4)
        cmd = string_unitID + string_FUNCTION + string_ADDRESS + string_NDATA
        checksum = hex(self.DTACalcChecksum(cmd))[2:].zfill(2).upper()
        return ':' + cmd + checksum + '\r\n'

    @staticmethod
    def DTACalcChecksum(string):
        def tobin(x, count=8):
            return ''.join([str((x>>y)&1) for y in range(count-1, -1, -1)])
        def twoscomp(num_str):
            return tobin(-int(num_str,2),len(num_str))
        length = len(string)
        # start at index 1 because of heading ':' cmd
        count = 0
        val = 0x00
        while count < length:
            val +=  int(string[count] + string[count+1], 16)  #string[count+1] goes out of range
            count += 2
        h_bs = bin(val)[2:]
        h2comp = twoscomp(h_bs)
        rval = int(h2comp,2)
        if (val & 0x80) == 0:
            return rval | 0x80
        return rval
