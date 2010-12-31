#!/usr/bin/env python
#
# version 00002: readjust length graph on the fly + display digital readouts + cosmetic changes
# version 00003: added buttons + knob.
# version 00004: start with PID PXG4 and PXR3 class frame.

# version 00005: start to add menus frame
# version 00006: This version is for two Fuji PIDs connected in the same RS485 network (unit id 1 and unit id 2)
#                unit 1 gives the MET; unit 2 gives BT
# version 00007: rearrange buttons in sequential order + add notations in graph
# version 00008: repair reset function + add clock calibration function
# version 00009: add function to load stored profile files for harddrive and function to save profiles
# version 00010: add graphic interface to set up serial comm port
# version 00011: start PID commands programmming (*UNFINISHED)
# version 00012: adds especial events recorder button
# version 00013: adds graph color modes black/white or custom
# version 00014: adds printing in file menu
# version 00015: saves settings (colors + serial port) in a txt file automatically upon closing the program application
# version 00016: changes format of stored profiles to add events data (incompatible with previos versions)
# version 00017: adds celsius/farenheit modes option in graph menu
# version 00018: plots x axis in mins:seconds
# version 00019: imports HH506RA files (dual thermocouple meter)
# version 00020: updates editgraph Dlg (edit graph properties in graph menu) and load/save file methods
# version 00021: adds device option in configuration menu, flavor labels editing, and phase Dlg (in Graph menu)
# version 00022: adds compatibility with device Omega HH806AU thermocouple meters through conf-device menu
# version 00023: adds html report in file menu
# version 00024: adds directory fucntion dirstruct() to organize profiles by .profile/year/month
#                profiles are saved with extension .txt 
# version 00025: adds save graph in file menu with options to resize for Home-Barista.com and CoffeeGeek.com
# version 00026: adds background profiles in Graph menu
# version 00027: UPDATE to python 2.6.6 and new python libs; See REQUIREMENTS FOR WINDOWS for python version libraries
#                To update: remove your old python installation and install new one (2.6.6). Then install python libs on top.
# version 00028: improve flavor star graph
# version 00029: adds support for Omega HH506RA (reported to work also as Extech 421509). Thanks to Marko Luther.
# version 00030: FINISHED PXR3 control Dlg 
# version 00031: FINISHED PXG4 control Dlg and enhanced background options
# END OF ALPHA.  BEGINNING BETA TESTING 

__version__ = u"0.1.1"


# ABOUT
# This program shows how to plot the temperature and its rate of change from a Fuji PID or a dual thermocouple meter

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#

# REQUIREMENTS FOR WINDOWS (installation order is important). FOR LINUX USE THE MATCHING LINUX VERSION FILES

#   OPTIONAL COMPILER TO INSTALL QT FROM SOURCE OR MAKE CHANGES TO QT SOURCE IN FUTURE
# 1) http://sourceforge.net/projects/mingw/files/Automated%20MinGW%20Installer/MinGW%205.1.6/MinGW-5.1.6.exe/download
#  After installation, edit system variable Path, right click My computer-properties-advanced, to include the bin directory of MinGW.
#  Example, add to Path ;C:\MINgw\bin     (; is important)

#   QT GRAPHIC INTERFACE
# 2) http://ftp3.ie.freebsd.org/pub/trolltech/pub/qt/source/qt-win-opensource-4.6.0-mingw.exe
# add to Path environment variable the bin directory of Qt. Example ;C:\Qt\4.6.0\bin

#   JAVA TO SUPPORT PYSERIAL LIBRARY
# 3) Java JDK or JRE:  http://java.sun.com/javase/downloads/index.jsp
# 4) javacomm: http://www.xpl4java.org/xPL4Java/javacomm.html
# follow the instruction in the README file. Copy and paste files as instructed

#  PYTHON 2.6.6
# 5) python 2.6: http://www.python.org/ftp/python/2.6.6/python-2.6.6.msi
# (add to Path the environment variable the bin directory of Python. Example ;E:\Python26

#   EXTRA PYTHON LIBRARIES NEEDED (install after installing python 2.6.6)
# 6) pyserial for python 2.6: http://sourceforge.net/projects/pyserial/files/pyserial/2.5/pyserial-2.5-rc1.win32.exe/download
#    NOTE: at the present time, numpy 1.5 is incompatible with py2exe. Instead, use numpy 1.3 if compiling for Win executable
# 7) http://sourceforge.net/projects/numpy/files/NumPy/1.3.0/numpy-1.3.0-win32-superpack-python2.6.exe/download 
# 8) http://sourceforge.net/projects/matplotlib/files/matplotlib/matplotlib-0.99.1/
# 9) pyqt4 for python 2.6: http://pyqwt.sourceforge.net/support/PyQt-Py2.6-gpl-4.5.4-1.exe


#########################   POLICIES  ###########################################################################
# 1  STRINGS
#
# When possible, use QString and Unicode characters in user inputs. Use ASCII only for serial comm (raw data).
# There are two ways to create a unicode string: u"one way" and unicode("second way").
# There are two ways to create a QString: QString("one way") and the return of QTfunction()
# There are several ways to create ASCII strings: "one way", str("second way"), and return of python function().
# Inmideately convert ascii strings to Unicode at return of functions by using unicode().
# There is 7 bits Ascii, and then there is 8 bit Western Europe Ascii.
# WARNING: If an ascii str contains characters outside the 7 bit range, Python raises UnicodeEncodeError exception.
#################################################################################################################


import sys
import platform
import serial
import math
import binascii
import tempfile
import time
import glob
import os
import string
import cgi
import codecs


from PyQt4.QtGui import (QAction, QApplication,QWidget,QMessageBox,QLabel,QMainWindow,QFileDialog,QInputDialog,QDialog,QLineEdit,
                         QSizePolicy,QGridLayout,QVBoxLayout,QHBoxLayout,QPushButton,QLCDNumber,QKeySequence,QSpinBox,QComboBox,
                         QSlider,QDockWidget,QTabWidget,QTextEdit,QTextBlock,QPrintDialog,QPrinter,QPainter,QImage,QPixmap,QColor,
                         QColorDialog,QPalette,QFrame,QImageReader,QRadioButton,QCheckBox,QDesktopServices,QIcon,QStatusBar,
                         QRegExpValidator,QDoubleValidator,QIntValidator)
from PyQt4.QtCore import (Qt,PYQT_VERSION_STR, QT_VERSION_STR,SIGNAL,QTime,QTimer,QString,QFile,QIODevice,QTextStream,QSettings,SLOT,
                          QRegExp,QDate,QUrl,QDir,QVariant)


from matplotlib.figure import Figure
from matplotlib.colors import cnames as cnames
import matplotlib.patches as patches
import matplotlib.transforms as transforms
import matplotlib.font_manager as font_manager
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar


platf = unicode(platform.system())


#######################################################################################
#################### GRAPH DRAWING WINDOW  ############################################
#######################################################################################

class tgraphcanvas(FigureCanvas):
    def __init__(self,parent):

        #default palette of colors
        self.palette = {"background":u'white',"grid":u'green',"ylabel":u'black',"xlabel":u'black',"title":u'black',"rect1":u'green',
                        "rect2":u'orange',"rect3":u'#996633',"met":u'red',"bt":u'#00007f',"deltamet":u'orange',
                        "deltabt":u'blue',"markers":u'black',"text":u'black',"watermarks":u'yellow',"Cline":u'brown'}
        
        self.flavorlabels = [u'Acidity',u'After taste',u'Clean cup',u'Head',u'Fragance',u'Sweetness',u'Aroma',u'Balance',u'Body']
        

        #F = Fahrenheit; C = Celsius
        self.mode = u"F"
        self.errorlog = []

        # default delay between readings in miliseconds
        self.delay = 5000

        #watermarks limits: dryphase1, dryphase2, midphase, and finish phase Y limits
        self.phases = [200,300,390,450]

        #statistics flags selects to display: stat. time, stat. bar, stat. flavors, stat. area
        self.statisticsflags = [1,1,1,1]
        #conditions to estimate bad flavor:dry[min,max],mid[min,max],finish[min,max] in seconds
        self.statisticsconditions = [180,360,180,600,180,360]
        #records length in seconds of total time [0], dry phase [1],mid phase[2],finish phase[3]
        self.statisticstimes = [0,0,0,0]

        #list of functions calls to read temperature for devices.
        # device 0 (with index 0 bellow) is Fuji Pid
        # device 1 (with index 1 bellow) is Omega HH806
        # device 2 (with index 2 bellow) is omega HH506 ; Logger Extech 421509 has been reported to be the same as Omega HH506RA
        self.device = 0 
        self.devicefunctionlist = [self.fujitemperature,
                                   self.HH806AU,
                                   self.HH506RA,
                                   self.CENTER309,
                                   self.CENTER306,
                                   self.CENTER305,
                                   self.CENTER304,
                                   self.CENTER303,
                                   self.CENTER302,
                                   self.CENTER301,
                                   self.CENTER300,
                                   self.VOLTCRAFTK204,
                                   self.VOLTCRAFTK202,
                                   self.VOLTCRAFT300K,
                                   self.VOLTCRAFT302KJ,
                                   self.EXTECH421509
                                   ]
        
        self.fig = Figure(facecolor=u'lightgrey')
        self.ax = self.fig.add_subplot(111, axisbg= self.palette["background"])
        FigureCanvas.__init__(self, self.fig)

        # set the parent widget
        self.setParent(parent)
        # we define the widget as expandable
        FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
        
        # the rate of chage of temperature
        self.rateofchange1 = 0.0
        self.rateofchange2 = 0.0
        # multiplication factor to increment sensitivity of rateofchange
        self.sensitivity = 20.0      
        #read and plot on/off flag
        self.flagon = False
        self.flagclock = False
        
        self.title = u"Roaster Scope"

        #list to store the time of each reading. Most IMPORTANT variable.
        self.timex = []

        #lists to store temps and rates of change. Second most IMPORTANT variables. All need same dimension.
        #self.temp1 = MET ; self.temp2 = BT; self.delta1 = deltaMET; self.delta2 = deltaBT
        self.temp1,self.temp2,self.delta1, self.delta2 = [],[],[],[]
        
        #variables to record 1C and 2C. Store as list of 8 elements:
        #1C start time [0],1C start Temp [1],1C end time [2],1C end temp [3],2C start time [4], 2C start Temp [5],
        #2C end time [6], 2C end temp [7]
        self.varC = [0.,0.,0.,0.,0.,0.,0.,0.]
        #variable to mark the begining and end of the roast [starttime [0], starttempBT [1], endtime [2],endtempBT [3]]
        self.startend = [0.,0.,0.,0.]

        #background profile
        self.background = False
        self.backgroundDetails = False
        self.backgroundpath = ""
        self.backgroundET,self.backgroundBT,self.timeB = [],[],[]
        self.startendB,self.varCB = [0.,0.,0.,0.],[0.,0.,0.,0.,0.,0.,0.,0.]
        self.backgroundalpha = 0.3
        self.backgroundwidth = 2
        self.backgroundmetcolor = self.palette["met"]
        self.backgroundbtcolor = self.palette["bt"]
        self.backgroundstyle = "-"
        self.backmoveflag = 1

        #Initial flavor parameters. 
        self.flavors = [.5,.5,.5,.5,.5,.5,.5,.5,.5,.5]

        # projection variables of change of rate
        self.HUDcounter = 1
        self.HUDflag = 0
        self.ETtarget = 350
        self.BTtarget = 250

        #General notes. Accessible through "edit graph properties" of graph menu. WYSIWYG viewer/editor.
        self.roastertype = u""
        self.operator = u""
        self.roastingnotes = u""
        self.cuppingnotes = u""
        self.roastdate = QDate.currentDate()
        self.beans = u""
        #[0]weight in, [1]weight out, [2]units (string)
        self.weight = [0,0,u"g"]
        
        #stores _indexes_ of self.timex to record events. Use as self.timex[self.specialevents[x]] to get the time of an event
        # use self.temp2[self.specialevents[x]] to get the BT temperature of an event
        self.specialevents = []
        #stores text descriptions for each event. Max 10
        self.specialeventsStrings = [u"1",u"2",u"3",u"4",u"5",u"6",u"7",u"8",u"9",u"10"]

        # set limits for X and Y axes. Default is in Farenheit units
        self.ylimit = 750
        self.endofx = 60
        self.startofx = 0
        
        #height of statistics bar
        self.statisticsheight = 650
        self.statisticsupper = 655
        self.statisticslower = 617
        
        self.ax.set_xlim(self.startofx, self.endofx)
        self.ax.set_ylim(0,self.ylimit)

        # disable figure autoscale
        self.ax.set_autoscale_on(False)

        #set grid + axle labels + title
        self.ax.grid(True,linewidth=2,color=self.palette["grid"])
            
        self.ax.set_ylabel(self.mode,size=16,color = self.palette["ylabel"])
        self.ax.set_xlabel(u'Time',size=16,color = self.palette["xlabel"])
        self.ax.set_title(self.title,size=20,color=self.palette["title"],fontweight='bold')

        #put a right tick on the graph
        for tick in self.ax.yaxis.get_major_ticks():
            tick.label2On = True

        #change label colors
        for label in self.ax.yaxis.get_ticklabels():
            label.set_color(self.palette["ylabel"])

        for label in self.ax.xaxis.get_ticklabels():
            label.set_color(self.palette["xlabel"])            

        
        #Create x axis labels in minutes:seconds instead of seconds
        self.xaxistosm()

        # make a blended transformation to help identify MOISTURE control phase
        trans = transforms.blended_transform_factory(self.ax.transAxes,self.ax.transData)
        rect1 = patches.Rectangle((0,self.phases[0]), width=1, height=(self.phases[1] - self.phases[0]),
                                  transform=trans, color=self.palette["rect1"],alpha=0.3)
        self.ax.add_patch(rect1)

        # make a blended transformation to help identify ROAST phase
        rect2 = patches.Rectangle((0,self.phases[1]), width=1, height=(self.phases[2] - self.phases[1]),
                                  transform=trans, color=self.palette["rect2"],alpha=0.3)
        self.ax.add_patch(rect2)

        # make a blended transformation to help identify FINISH phase. other color #885500
        rect3 = patches.Rectangle((0,self.phases[2]), width=1, height=(self.phases[3] - self.phases[2]),
                                  transform=trans, color=self.palette["rect3"],alpha=0.3)
        self.ax.add_patch(rect3)

        # mark the base lines for DeltaBT
        self.ax.axhline(y=50, linestyle = ':',color = self.palette["grid"])

        self.delta1, self.delta2 = [],[]

        # generates first "empty" plot of temperature and deltaT
        self.l_temp1, = self.ax.plot(self.timex, self.temp1,color=self.palette["met"],linewidth=2)
        self.l_temp2, = self.ax.plot(self.timex, self.temp2,color=self.palette["bt"],linewidth=2)
        self.l_delta1, = self.ax.plot(self.timex, self.delta1,color=self.palette["deltamet"],linewidth=2)
        self.l_delta2, = self.ax.plot(self.timex, self.delta2,color=self.palette["deltabt"],linewidth=2)

        # add legend to plot.
        handles = [self.l_temp1,self.l_temp2,self.l_delta1,self.l_delta2]
        labels = [u"ET",u"BT",u"DeltaET",u"DeltaBT"]
        self.ax.legend(handles,labels,loc=2,ncol=4,prop=font_manager.FontProperties(size=10),fancybox=True)

        # draw of the Figure
        self.fig.canvas.draw()

        ###########################  TIME  CLOCK     ##########################
        # NOTE: there are two times that can cause confusion: one is a trigger-timer to trigger timerevent at every
        # delay (ie. read temp, update graph, etc.), and then this one (self.timeclock), which
        # is used to record temperature-reading-time in self.timex[]. It is also used to display time in the LCD.
        
        # create an object time to measure and record time (in miliseconds) 
    
        self.timeclock = QTime()

        ############################    TRIGGER  TIMER       ##################################
        # start a Qtimer object (Qt) with delay (self.delay 5000 millisecs). This calls event handler timerEvent() on every delay.
        # do not confuse this timer with self.timeclock (above), which is used to log clock time and put it in the LCD.
        # This timer just triggers timerEvent at every self.delay (ie. reads temperature at every delay, updates graph, etc).
        
        self.timerid = self.startTimer(self.delay)

        # DESCRIPTION of TRIGGER TIMER
        # Python26/Lib/site-packages/PyQt4/doc/html/qobject.html#startTimer
        # int QObject.startTimer (self, int interval)
        # Starts a timer and returns a timer identifier, or returns zero if it could not start a timer.
        # A timer event will occur every interval milliseconds until killTimer() is called. If interval is 0,
        # then the timer event occurs once every time there are no more window system events to process.
        
        # The virtual timerEvent() function is called with the QTimerEvent event parameter class when a timer
        # event occurs. Reimplement this function to get timer events. If multiple timers are running, the QTimerEvent.timerId()
        # can be used to find out which timer was activated.


    #event handler from startTimer()
    def timerEvent(self, evt):
                                   
        if self.flagon:
            #read timer, ET (t2) and BT (t1) TEMPERATURE
            tx,t2,t1 = self.devicefunctionlist[self.device]()  #use a list of functions (a different one for each device) with index self.device

            self.timex.append(tx)
            self.temp2.append(t2)
            self.temp1.append(t1)

            #we need a minimum of two readings to calculate rate of change
            if len(self.timex) > 2:
                timed = self.timex[-1] - self.timex[-2]   #time difference between last two readings
                #calculate Delta T = (changeTemp/ChangeTime) =  degress per second;
                self.rateofchange1 = (self.temp1[-1] - self.temp1[-2]) / timed  #delta ET (degress / second)
                self.rateofchange2 = (self.temp2[-1] - self.temp2[-2]) / timed  #delta  BT (degress / second)
                rateofchange1plot = 100 + self.sensitivity*self.rateofchange1   #lift to plot on the graph at Temp = 100
                rateofchange2plot = 50 + self.sensitivity*self.rateofchange2    #lift to plot on the grpah at Temp  = 50
            else:
                self.rateofchange1 = 100.
                self.rateofchange2 = 50.
                rateofchange1plot = 0
                rateofchange2plot = 0
            # append new data to the rateofchange
            self.delta1.append(rateofchange1plot)
            self.delta2.append(rateofchange2plot)
                        
            # update lines data using the lists with new data
            self.l_temp1.set_data(self.timex, self.temp1)
            self.l_temp2.set_data(self.timex, self.temp2)
            self.l_delta1.set_data(self.timex, self.delta1)
            self.l_delta2.set_data(self.timex, self.delta2)

            #readjust xlimit of plot if needed
            if  self.timex[-1] > (self.endofx - 45):            # if difference is smaller than 30 seconds  
                self.endofx = int(self.timex[-1] + 180)         # increase x limit by 3 minutes
                self.ax.set_xlim(self.startofx,self.endofx)
                self.xaxistosm()

            #update LCDs
            if self.flagclock:
                ts = tx - self.startend[0]
                st2 = self.stringfromseconds(ts)
                timelcd = QString(st2)
                aw.lcd1.display(timelcd)

            else:
                ts = tx
                st2 = self.stringfromseconds(ts)
                timelcd = QString(st2)
                aw.lcd1.display(timelcd)                
                
            aw.lcd2.display(t1)                          # MET
            aw.lcd3.display(t2)                          # BT
            aw.lcd4.display(int(self.rateofchange1*60))       # rate of change MET (degress per minute)
            aw.lcd5.display(int(self.rateofchange2*60))       # rate of change BT (degrees per minute)

               
            #update the graph
            self.fig.canvas.draw()

            #display projection of delta BT
            if self.HUDflag:
                self.viewHUD()

    def toggleHUD(self):
        if self.HUDflag:
            self.HUDflag = False
            aw.button_18.setStyleSheet("QPushButton { background-color: #b5baff }")
            aw.HUDstatus.showMessage(u"HUD OFF",3000)
            self.ax.lines = self.ax.lines[0:5]

        else:
            self.HUDflag = True
            aw.button_18.setStyleSheet("QPushButton { background-color: #60ffed }")
            aw.HUDstatus.showMessage(u"HUD ON",3000)
            aw.hudshow()

    #make a projection of change of rate of BT on the graph
    def viewHUD(self):
        #calculate the temperature endpoint at endofx acording to the latest rate of change
        BTprojection = self.temp2[-1] + self.rateofchange2*(self.endofx - self.timex[-1]+ 120)
        ETprojection = self.temp1[-1] + self.rateofchange1*(self.endofx - self.timex[-1]+ 120)
        #plot proyections
        self.ax.plot([self.timex[-1],self.endofx + 120 ], [self.temp2[-1], BTprojection],color =  self.palette["bt"], linestyle = '-.', linewidth= 8, alpha = .3)
        self.ax.plot([self.timex[-1],self.endofx + 120 ], [self.temp1[-1], ETprojection],color =  self.palette["met"], linestyle = '-.', linewidth= 8, alpha = .3)

        #erase every three trigger events to make it look like a radar
        l,p = divmod(self.HUDcounter,3)
        if p == 0:
            self.ax.lines = self.ax.lines[0:5]
            
        self.HUDcounter += 1

        if self.rateofchange1 > 0:
            ETreachTime = (self.ETtarget - self.temp1[-1])/self.rateofchange1
        else:
            ETreachTime = -1
            
        if self.rateofchange2 > 0:
            BTreachTime = (self.BTtarget - self.temp2[-1])/self.rateofchange2
        else:
            BTreachTime = -1
            
        if ETreachTime > 0 and ETreachTime < 5940:
            stringET = u"[ " + self.stringfromseconds(int(ETreachTime)) + u" to reach ET target " + unicode(self.ETtarget) + self.mode +  u" ] "
        else:
            stringET = u"[ XX:XX to reach ET target " + unicode(self.ETtarget) + self.mode +  u" ] "
            
        if BTreachTime > 0 and BTreachTime < 5940:    
            stringBT = u"[ " + self.stringfromseconds(int(BTreachTime)) + u" to reach BT target " + unicode(self.BTtarget) + self.mode + u" ] "
        else:
            stringBT = u"[ XX:XX to reach BT target " + unicode(self.BTtarget) + self.mode + u" ] "

        string = stringET + stringBT
        aw.HUDstatus.showMessage(string,10000)



    #finds time, ET and BT when using Fuji PID
    def fujitemperature(self):
        # get the temperature for BT. RS485 unit ID (2)
        t2 = aw.pid.gettemperature(2)/10.
        #get time of each temperature reading in seconds from start; .elapsed() returns miliseconds
        tx = self.timeclock.elapsed()/1000.
        # get the temperature for MET. RS485 unit ID (1)
        t1 = aw.pid.gettemperature(1)/10.  #Need to divide by 10 beacuse using 1 decimal point in Fuji (ie. received 843 = 84.3)
                
        return tx,t2,t1

    def HH506RA(self):
        
        t2,t1 = aw.ser.HH506RAtemperature()
        tx = self.timeclock.elapsed()/1000.

        return tx,t2,t1

    def HH806AU(self):

         t2,t1 = aw.ser.HH806AUtemperature()
         tx = self.timeclock.elapsed()/1000.

         return tx,t2,t1

    def CENTER309(self):

         t2,t1 = aw.ser.CENTER309temperature()
         tx = self.timeclock.elapsed()/1000.

         return tx,t2,t1         

    def CENTER306(self):

         t2,t1 = aw.ser.CENTER306temperature()
         tx = self.timeclock.elapsed()/1000.

         return tx,t2,t1
        
    def CENTER305(self):

         t2,t1 = aw.ser.CENTER306temperature()
         tx = self.timeclock.elapsed()/1000.

         return tx,t2,t1

    def CENTER304(self):

         t2,t1 = aw.ser.CENTER309temperature()
         tx = self.timeclock.elapsed()/1000.

         return tx,t2,t1         


    def CENTER303(self):

         t2,t1 = aw.ser.CENTER303temperature()
         tx = self.timeclock.elapsed()/1000.

         return tx,t2,t1    

    def CENTER302(self):

         t2,t1 = aw.ser.CENTER303temperature()
         tx = self.timeclock.elapsed()/1000.

         return tx,t2,t1  

    def CENTER301(self):

         t2,t1 = aw.ser.CENTER303temperature()
         tx = self.timeclock.elapsed()/1000.

         return tx,t2,t1

    def CENTER300(self):

         t2,t1 = aw.ser.CENTER303temperature()
         tx = self.timeclock.elapsed()/1000.

         return tx,t2,t1  
        
    def VOLTCRAFTK204(self):
        
         t2,t1 = aw.ser.CENTER309temperature()
         tx = self.timeclock.elapsed()/1000.
         
         return tx,t2,t1

    def VOLTCRAFTK202(self):
        
         t2,t1 = aw.ser.CENTER306temperature()
         tx = self.timeclock.elapsed()/1000.
         
         return tx,t2,t1
        
    def VOLTCRAFT300K(self):
        
         t2,t1 = aw.ser.CENTER303temperature()
         tx = self.timeclock.elapsed()/1000.
         
         return tx,t2,t1

    def VOLTCRAFT302KJ(self):
        
         t2,t1 = aw.ser.CENTER303temperature()
         tx = self.timeclock.elapsed()/1000.
         
         return tx,t2,t1
        
    def EXTECH421509(self):
        
        t2,t1 = aw.ser.HH506RAtemperature()
        tx = self.timeclock.elapsed()/1000.

        return tx,t2,t1

    #creates X axis labels ticks in mm:ss acording to the endofx limit
    def xaxistosm(self):
        #aligns the 00:00 with the start of the roast if it exists    
        if int(self.startend[0]):
            LLL = int(self.endofx/60)
            newlocs = [self.startend[0]]
            for i in range(LLL):    
                newlocs.append(newlocs[-1]+60)              
            self.ax.xaxis.set_ticks(newlocs)

        #rename xaxis ticks in mins:secs
        locs = self.ax.get_xticks()
        labels = []
        for i in range(len(locs)):
                stringlabel = unicode(self.minutesfromseconds(locs[i]-int(self.startend[0])))
                labels.append(stringlabel)              
        self.ax.set_xticklabels(labels,color=self.palette["xlabel"],horizontalalignment='center')

        #update label colors
        for label in self.ax.xaxis.get_ticklabels():
            label.set_color(self.palette["xlabel"])  
        
    #Resets graph. Called from reset button. Deletes all data
    def reset(self):
        self.ax = self.fig.add_subplot(111, axisbg=self.palette["background"])
        self.ax.set_title(self.title,size=20,color=self.palette["title"],fontweight='bold')  

        #reset all variables that need to be reseted
        self.flagon = False
        self.flagclock = False
        self.rateofchange1 = 0.0
        self.rateofchange2 = 0.0
        self.sensitivity = 20.0      
        self.temp1, self.temp2, self.delta1, self.delta2, self.timex = [],[],[],[],[]
        self.varC = [0.,0.,0.,0.,0.,0.,0.,0.]
        self.startend = [0.,0.,0.,0.]
        self.specialevents=[]
        self.endofx = 60
        self.startofx = 0
        aw.lcd1.display(0.0)
        aw.lcd2.display(0.0)
        aw.lcd3.display(0.0)
        aw.lcd4.display(0.0)
        aw.lcd5.display(0.0)
        aw.messagelabel.setText(u"Scope has been resetted")
        aw.button_1.setDisabled(False)
        aw.button_2.setDisabled(False)        
        aw.button_3.setDisabled(False)
        aw.button_4.setDisabled(False)
        aw.button_5.setDisabled(False)
        aw.button_6.setDisabled(False)
        aw.button_7.setDisabled(False)
        aw.button_8.setDisabled(False)
        aw.button_9.setDisabled(False)
        aw.button_1.setFlat(False)
        aw.button_2.setFlat(False)
        aw.button_3.setFlat(False)
        aw.button_4.setFlat(False)
        aw.button_5.setFlat(False)
        aw.button_6.setFlat(False)
        aw.button_7.setFlat(False)
        aw.button_8.setFlat(False)
        aw.button_9.setFlat(False)
        
        self.roastertype = u""
        self.operator = u""
        self.roastingnotes = u""
        self.cuppingnotes = u""
        self.errorlog = []
        self.weight = [0,0,u"g"]
        self.specialevents = []
        self.specialeventsStrings = [u"1",u"2",u"3",u"4",u"5",u"6",u"7",u"8",u"9",u"10"]
        self.roastdate = QDate.currentDate()

        #restart() clock 
        self.timeclock.restart()
        
        self.redraw()

        self.HUDcounter = 1

    #Redraws data   
    def redraw(self):
        self.fig.clf()   #wipe out figure
        self.ax = self.fig.add_subplot(111, axisbg=self.palette["background"])
        #Set axes same as in __init__
        self.ax.set_xlim(self.startofx, self.endofx)
        self.ax.set_ylim(0, self.ylimit)
        self.ax.set_autoscale_on(False)
        self.ax.grid(True,linewidth=2,color=self.palette["grid"])
        self.ax.set_ylabel(self.mode,size=16,color =self.palette["ylabel"])
        self.ax.set_xlabel('Time',size=16,color = self.palette["xlabel"])
        self.ax.set_title(self.title,size=20,color=self.palette["title"],fontweight='bold')
        for tick in self.ax.yaxis.get_major_ticks():
            tick.label2On = True
            
        #draw water marks for dry phase region, mid phase region, and finish phase region
        trans = transforms.blended_transform_factory(self.ax.transAxes,self.ax.transData)
        rect1 = patches.Rectangle((0,self.phases[0]), width=1, height=(self.phases[1]-self.phases[0]),
                                  transform=trans, color=self.palette["rect1"],alpha=0.3)
        self.ax.add_patch(rect1)
        rect2 = patches.Rectangle((0,self.phases[1]), width=1, height=(self.phases[2]-self.phases[1]),
                                  transform=trans, color=self.palette["rect2"],alpha=0.3)
        self.ax.add_patch(rect2)
        rect3 = patches.Rectangle((0,self.phases[2]), width=1, height=(self.phases[3] - self.phases[2]),
                                  transform=trans, color=self.palette["rect3"],alpha=0.3)
        self.ax.add_patch(rect3)
        self.ax.axhline(y=50, linestyle = ':',color = self.palette["grid"])

        ##### ET,BT curves
        self.l_temp1, = self.ax.plot(self.timex, self.temp1,color=self.palette["met"],linewidth=2)
        self.l_temp2, = self.ax.plot(self.timex, self.temp2,color=self.palette["bt"],linewidth=2)

        #check BACKGROUND flag
        if self.background:
            #check to see if there is both a profile loaded and a background loaded
            if self.startend[0] and self.startendB[0] and (self.startend[0] != self.startendB[0]) and self.backmoveflag:
                #align the background profile so they both plot with the same CHARGE time
                difference = self.startend[0] - self.startendB[0]
                if difference > 0:
                    self.movebackground(u"left",difference)
                elif difference < 0:
                    self.movebackground(u"right",difference)
                self.backmoveflag = 0
                
            #draw background
            self.l_back1, = self.ax.plot(self.timeB, self.backgroundET,color=self.backgroundmetcolor,linewidth=self.backgroundwidth,
                                         linestyle=self.backgroundstyle,alpha=self.backgroundalpha)
            self.l_back2, = self.ax.plot(self.timeB, self.backgroundBT,color=self.backgroundbtcolor,linewidth=self.backgroundwidth,
                                         linestyle=self.backgroundstyle,alpha=self.backgroundalpha)

            #check backgroundDetails flag
            if self.backgroundDetails:
                st1 = unicode(self.stringfromseconds(self.startendB[0]-self.startend[0]))
                self.ax.annotate(u"%.1f"%(self.startendB[1]), xy=(self.startendB[0], self.startendB[1]),xytext=(self.startendB[0]-5,self.startendB[1]+50),fontsize=10,
                                 color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),
                                 alpha=self.backgroundalpha)
                
                self.ax.annotate(st1, xy=(self.startendB[0], self.startendB[1]),xytext=(self.startendB[0]+5,self.startendB[1]-100),fontsize=10,
                                 color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),
                                alpha=self.backgroundalpha)
                
                if self.varCB[0]:
                    st1 = unicode(self.stringfromseconds(self.varCB[0]-self.startend[0]))
                    self.ax.annotate(u"%.1f"%(self.varCB[1]), xy=(self.varCB[0], self.varCB[1]),xytext=(self.varCB[0]-5,self.varCB[1]+50),fontsize=10,
                                     color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),
                                     alpha=self.backgroundalpha)
                    self.ax.annotate(st1, xy=(self.varCB[0], self.varCB[1]),xytext=(self.varCB[0],self.varCB[1]-50),fontsize=10,
                                     color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),
                                     alpha=self.backgroundalpha)
                    
                if self.varCB[2]:
                    st1 = unicode(self.stringfromseconds(self.varCB[2]-self.startend[0]))          
                    self.ax.annotate(u"%.1f"%(self.varCB[3]), xy=(self.varCB[2], self.varCB[3]),xytext=(self.varCB[2]-5,self.varCB[3]+70),fontsize=10,
                                     color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),
                                     alpha=self.backgroundalpha)              
                    self.ax.annotate(st1, xy=(self.varCB[2], self.varCB[3]),xytext=(self.varCB[2],self.varCB[3]-80),fontsize=10,
                                    color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),
                                     alpha=self.backgroundalpha)
                    
                if self.varCB[4]:
                    st1 = unicode(self.stringfromseconds(self.varCB[4]-self.startend[0]))
                    self.ax.annotate(u"%.1f"%(self.varCB[5]), xy=(self.varCB[4], self.varCB[5]),xytext=(self.varCB[4]-5,self.varCB[5]+90),fontsize=10,
                                     color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),
                                     alpha=self.backgroundalpha)      
                    self.ax.annotate(st1, xy=(self.varCB[4], self.varCB[5]),xytext=(self.varCB[4],self.varCB[5]-110),fontsize=10,
                                    color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),
                                     alpha=self.backgroundalpha)
                    
                if self.varCB[6]:
                    st1 = unicode(self.stringfromseconds(self.varCB[6]-self.startend[0]))
                    self.ax.annotate(u"%.1f"%(self.varCB[7]), xy=(self.varCB[6], self.varCB[7]),xytext=(self.varCB[6]-5,self.varCB[7]+50),fontsize=10,
                                     color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),
                                     alpha=self.backgroundalpha)                
                    self.ax.annotate(st1, xy=(self.varCB[6], self.varCB[7]),xytext=(self.varCB[6],self.varCB[7]-40),fontsize=10,
                                     color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),
                                     alpha=self.backgroundalpha)
                    
                if self.startendB[2]:
                    st1 = unicode(self.stringfromseconds(self.startendB[2]-self.startend[0]))
                    self.ax.annotate(u"%.1f"%(self.startendB[3]), xy=(self.startendB[2], self.startendB[3]),xytext=(self.startendB[2]-5,self.startendB[3]+70),
                                     color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),fontsize=10,
                                    alpha=self.backgroundalpha)
                    self.ax.annotate(st1, xy=(self.startendB[2], self.startendB[3]),xytext=(self.startendB[2],self.startendB[3]-80),fontsize=10,
                                 color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)

            #END of Background
            
        #populate delta BT (self.delta2) and delta MET (self.delta1)
        self.delta1,self.delta2,d1,d2=[],[],[],[]
        for i in range(len(self.timex)-1):
            #print i, self.qmc.temp1[i+1], self.qmc.temp1[i]
            timed = self.timex[i+1] - self.timex[i]
            d1 = self.sensitivity*((self.temp1[i+1] - self.temp1[i]) / timed) + 100
            d2 = self.sensitivity*((self.temp2[i+1] - self.temp2[i]) / timed) + 50
            self.delta1.append(d1)
            self.delta2.append(d2)
        #this is needed because DeltaBT and DeltaET need 2 values of timex (difference) but they also need same dimension in order to plot
        if len(self.timex) > len(self.delta1):
            self.delta1.append(d1)
            self.delta2.append(d2)

        ##### DeltaET,DeltaBT curves
        self.l_delta1, = self.ax.plot(self.timex, self.delta1,color=self.palette["deltamet"],linewidth=2)
        self.l_delta2, = self.ax.plot(self.timex, self.delta2,color=self.palette["deltabt"],linewidth=2)
        
        handles = [self.l_temp1,self.l_temp2,self.l_delta1,self.l_delta2] # for leyend
        labels = [u"ET",u"BT",u"DeltaET",u"DeltaBT"]                          # for leyend
        
        #write legend
        self.ax.legend(handles,labels,loc=2,ncol=4,prop=font_manager.FontProperties(size=10),fancybox=True)
    
        #Add markers for CHARGE
        if self.startend[0]:
            #anotate temperature
            self.ax.annotate(u"%.1f"%(self.startend[1]), xy=(self.startend[0], self.startend[1]),xytext=(self.startend[0]-5,
                                self.startend[1]+50),color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
            #anotate time
            self.ax.annotate(u"START 00:00", xy=(self.startend[0], self.startend[1]),xytext=(self.startend[0]+5,
                                self.startend[1]-100),color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
            
        #Add 1Cs markers
        if self.varC[0]:
            st1 = u"1CS " + unicode(self.stringfromseconds(self.varC[0]-self.startend[0]))
            #anotate temperature
            self.ax.annotate(u"%.1f"%(self.varC[1]), xy=(self.varC[0], self.varC[1]),xytext=(self.varC[0]-5,
                                self.varC[1]+50), color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
            #anotate time
            self.ax.annotate(st1, xy=(self.varC[0], self.varC[1]),xytext=(self.varC[0],self.varC[1]-50),
                                 color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
        #Add 1Ce markers
        if self.varC[2]:
            st1 = u"1CE " + unicode(self.stringfromseconds(self.varC[2]-self.startend[0]))
            #anotate temperature
            self.ax.annotate(u"%.1f"%(self.varC[3]), xy=(self.varC[2], self.varC[3]),xytext=(self.varC[2]-5,
                                self.varC[3]+70),color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
            #anotate time
            self.ax.annotate(st1, xy=(self.varC[2], self.varC[3]),xytext=(self.varC[2],self.varC[3]-80),
                                color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
            #add a water mark
            self.ax.axvspan(self.varC[0], self.varC[2], facecolor=self.palette["watermarks"], alpha=0.2)

        #Add 2Cs markers
        if self.varC[4]:
            st1 = u"2CS " + unicode(self.stringfromseconds(self.varC[4]-self.startend[0]))
            self.ax.annotate(u"%.1f"%(self.varC[5]), xy=(self.varC[4], self.varC[5]),xytext=(self.varC[4]-5,
                                self.varC[5]+90),color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)      
            self.ax.annotate(st1, xy=(self.varC[4], self.varC[5]),xytext=(self.varC[4],self.varC[5]-110),
                                 color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
        #Add 2Ce markers
        if self.varC[6]:
            st1 =  u"2CE " + unicode(self.stringfromseconds(self.varC[6]-self.startend[0]))
            #anotate temperature
            self.ax.annotate(u"%.1f"%(self.varC[7]), xy=(self.varC[6], self.varC[7]),xytext=(self.varC[6]-5,
                                self.varC[7]+50),color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
            #anotate time
            self.ax.annotate(st1, xy=(self.varC[6], self.varC[7]),xytext=(self.varC[6],self.varC[7]-40),
                                 color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
            #do water mark
            self.ax.axvspan(self.varC[4], self.varC[6], facecolor=self.palette["watermarks"], alpha=0.2)
            #make vertical line in the MIDDLE of 2Cs and 2Ce
            middle = (self.varC[4]+self.varC[6])/2
            self.ax.axvline(x=middle, ymin=0, ymax=1,color=self.palette["Cline"])
        #Add DROP markers
        if self.startend[2]:
            st1 = u"END " + unicode(self.stringfromseconds(self.startend[2]-self.startend[0]))
            #anotate temperature
            self.ax.annotate(u"%.1f"%(self.startend[3]), xy=(self.startend[2], self.startend[3]),xytext=(self.startend[2]-5,
                                self.startend[3]+70),color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
            #anotate time
            self.ax.annotate(st1, xy=(self.startend[2], self.startend[3]),xytext=(self.startend[2],self.startend[3]-80),
                                 color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
            
            self.writestatistics()
            
            #write events
            Nevents = len(self.specialevents)
            for i in range(Nevents):
                self.ax.annotate(u"e" + str(i+1), xy=(self.timex[int(self.specialevents[i])], self.temp2[int(self.specialevents[i])]),
                                 xytext=(self.timex[int(self.specialevents[i])]-15,self.temp2[int(self.specialevents[i])]+ 40),alpha=0.8,
                                 color=self.palette["text"],arrowprops=dict(arrowstyle='-',color=self.palette["text"],alpha=0.4),fontsize=12)
                
        #update X label names and colors        
        self.xaxistosm()

        #update Y label colors
        for label in self.ax.yaxis.get_ticklabels():
            label.set_color(self.palette["ylabel"])

        #ready to plot    
        self.fig.canvas.draw()     

    # used to put time in LCD timer. input int, output string
    def stringfromseconds(self, seconds):
        mins, secs = divmod(seconds,60)
        if secs < 10:
            st2 = unicode(int(mins)) + u":" + u"0" + unicode(int(secs))
        else:
            st2 = unicode(int(mins))+ u":" + unicode(int(secs))
        if mins < 10:
            st2 =u"0" + st2
        return st2

    #Converts a string into seconds integer. Use for example to interpret times from Roaster Properties Dlg inputs
    #acepted formats: "00:00:00","00:00","0:00"
    def stringtoseconds(self, string):
        try:
            seconds = 0
            length = len(string)
            if length > 8:
                raise ValueError, u"Invalid time format, too long."                
            
            if length > 0 and string[-1].isdigit():
                seconds += int(string[-1])
                
            if length > 1 and string[-2].isdigit():
                if int(string[-2]) > 5:
                    raise ValueError,u"Invalid seconds xx:59 max"
                seconds += 10*int(string[-2])

            if length > 2 and string[-3] != ":":
                raise ValueError, u"invalid time format mm:ss (: separator missing)"
            
            if length > 3 and string[-4].isdigit():            
                seconds += 60*int(string[-4])
                
            if length > 4 and string[-5].isdigit():
                if int(string[-5]) > 5:
                    raise ValueError,u"Invalid minutes 59:xx max"                
                seconds += 600*int(string[-5])

            if length > 5 and string[-6] != ":":
                raise ValueError, u"invalid time format hh:mm:ss (: separators missing)"
                
            if length > 6 and string[-7].isdigit():
                seconds += 3600*int(string[-7])
                
            if length > 7 and string[-8].isdigit():
                seconds += 36000*int(string[-8])
            return seconds

        except ValueError,e:
            aw.messagelabel.setText(unicode(e))
            aw.qmc.errorlog.append(u"stringfromseconds(): input error " + unicode(e))
            return -1          


    # used to create minutes labels in the X axis. input int, output string
    def minutesfromseconds(self, seconds):
        mins, secs = divmod(seconds,60)
        if not int(self.startend[0]):
            if secs < 10:
                st2 = str(int(mins)) + ":" + "0" + str(int(secs))
            else:
                st2 = str(int(mins))+ ":" + str(int(secs))
        else:
            st2 = unicode(int(mins))
        return st2

    def fromFtoC(self,Ffloat):
        return (Ffloat-32.0)*(5.0/9.0)

    def fromCtoF(self,CFloat):
        return (CFloat*9.0/5.0)+32.0

    #sets the graph display in Fahrenheit mode
    def fahrenheitMode(self):
        self.mode = u"F"
        self.ylimit = 750
        #change watermarks limits. dryphase1, dryphase2, midphase, and finish phase Y limits
        self.phases = [200,300,390,450]
        self.ax.set_ylabel(self.mode,size=16,color = self.palette["ylabel"]) #Write "F" on Y axis
        self.statisticsheight = 650
        self.statisticsupper = 655
        self.statisticslower = 617
        self.redraw()


    #sets the graph display in Celsius mode
    def celsiusMode(self):
        self.mode = u"C"
        self.ylimit = 400
        #change watermarks limits. dryphase1, dryphase2, midphase, and finish phase Y limits
        self.phases = [95,150,200,230]
        self.ax.set_ylabel(self.mode,size=16,color = self.palette["ylabel"]) #Write "C" on Y axis
        self.statisticsheight = 341
        self.statisticsupper = 346
        self.statisticslower = 325
        self.redraw()

    #converts a loaded profile to a different temperature scale. t input is the requested mode (F or C).
    def convertTemperature(self,t):
        #verify there is a loaded profile
        profilelength = len(self.timex)
        if profilelength > 0:
            if t == u"F":
                string = u"Convert profile data to Fahrenheit?"
                reply = QMessageBox.question(self,u"Convert Profile Temperature",string,
                        QMessageBox.Yes|QMessageBox.Cancel)
                if reply == QMessageBox.Cancel:
                    return 
                elif reply == QMessageBox.Yes:
                    if self.mode == u"C":
                        for i in range(profilelength):
                            self.temp1[i] = self.fromCtoF(self.temp1[i])    #ET
                            self.temp2[i] = self.fromCtoF(self.temp2[i])    #BT
                            self.delta1[i] = self.fromCtoF(self.delta1[i])  #Delta ET
                            self.delta2[i] = self.fromCtoF(self.delta2[i])  #Delta BT
                            
                        self.varC[1] =   self.fromCtoF(self.varC[1])        #1C start temp
                        self.varC[3] =   self.fromCtoF(self.varC[3])        #1C end temp
                        self.varC[5] =   self.fromCtoF(self.varC[5])        #2C start temp
                        self.varC[7] =   self.fromCtoF(self.varC[7])        #2C end temp
                        self.startend[1] = self.fromCtoF(self.startend[1])  #CHARGE temp
                        self.startend[3] = self.fromCtoF(self.startend[3])  #DROP temp

                        backgroundlength = len(self.timeB)
                        if backgroundlength > 0:
                            for i in range(backgroundlength):
                                self.backgroundET[i] = self.fromCtoF(self.backgroundET[i])
                                self.backgroundBT[i] = self.fromCtoF(self.backgroundBT[i])                           
                                
                            self.varCB[1] =   self.fromCtoF(self.varCB[1])       #1C start temp B
                            self.varCB[3] =   self.fromCtoF(self.varCB[3])       #1C end temp B
                            self.varCB[5] =   self.fromCtoF(self.varCB[5])       #2C start temp B
                            self.varCB[7] =   self.fromCtoF(self.varCB[7])       #2C end temp B
                            self.startendB[1] = self.fromCtoF(self.startendB[1]) #CHARGE temp B
                            self.startendB[3] = self.fromCtoF(self.startendB[3]) #DROP temp B

                        self.fahrenheitMode()
                        aw.messagelabel.setText(u"Profile changed to Fahrenheit")

                    else:
                        QMessageBox.information(self,u"Convert Profile Temperature",
                                                u"Unable to comply. You already are in Fahrenheit")
                        aw.messagelabel.setText(u"Profile not changed")
                        return

            elif t == u"C":
                string = u"Convert profile data to Celsius?"
                reply = QMessageBox.question(self,u"Convert Profile Temperature",string,
                        QMessageBox.Yes|QMessageBox.Cancel)
                if reply == QMessageBox.Cancel:
                    return 
                elif reply == QMessageBox.Yes:
                    if self.mode == u"F":         
                        for i in range(profilelength):
                            self.temp1[i] = self.fromFtoC(self.temp1[i])    #ET
                            self.temp2[i] = self.fromFtoC(self.temp2[i])    #BT
                            self.delta1[i] = self.fromFtoC(self.delta1[i])  #Delta ET
                            self.delta2[i] = self.fromFtoC(self.delta2[i])  #Delta BT
                            
                        self.varC[1] =   self.fromFtoC(self.varC[1])        #1C start temp
                        self.varC[3] =   self.fromFtoC(self.varC[3])        #1C end temp
                        self.varC[5] =   self.fromFtoC(self.varC[5])        #2C start temp
                        self.varC[7] =   self.fromFtoC(self.varC[7])        #2C end temp
                        self.startend[1] = self.fromFtoC(self.startend[1])  #CHARGE temp
                        self.startend[3] = self.fromFtoC(self.startend[3])  #DROP temp
                        
                        backgroundlength = len(self.timeB)
                        if backgroundlength > 0:
                            for i in range(backgroundlength):
                                self.backgroundET[i] = self.fromFtoC(self.backgroundET[i]) #ET B
                                self.backgroundBT[i] = self.fromFtoC(self.backgroundBT[i]) #BT B                          
                                
                            self.varCB[1] =   self.fromFtoC(self.varCB[1])       #1C start temp B
                            self.varCB[3] =   self.fromFtoC(self.varCB[3])       #1C end temp B
                            self.varCB[5] =   self.fromFtoC(self.varCB[5])       #2C start temp B
                            self.varCB[7] =   self.fromFtoC(self.varCB[7])       #2C end temp B
                            self.startendB[1] = self.fromFtoC(self.startendB[1]) #CHARGE temp B
                            self.startendB[3] = self.fromFtoC(self.startendB[3]) #DROP temp B
                    else:
                        QMessageBox.information(self,u"Convert Profile Temperature",
                                                u"Unable to comply. You already are in Celsius")
                        aw.messagelabel.setText(u"Profile not changed")
                        return

                    self.celsiusMode()
                    aw.messagelabel.setText(u"Profile changed to Celsius")
                    
            self.redraw()

        else:
             QMessageBox.information(self,u"Convert Profile Scale","No profile data found")
                                    

    #selects color mode: input 1=color mode; input 2=black and white mode (printing); input 3 = customize colors
    def changeGColor(self,color):
        #COLOR (option 1) Default
        palette1 = {"background":u'white',"grid":u'green',"ylabel":u'black',"xlabel":u'black',"title":u'black',"rect1":u'green',
                        "rect2":u'orange',"rect3":u'#996633',"met":u'red',"bt":u'#00007f',"deltamet":u'orange',
                        "deltabt":u'blue',"markers":u'black',"text":u'black',"watermarks":u'yellow',"Cline":u'brown'}

        #BLACK & WHITE (option 2) best for printing
        palette2 = {"background":u'white',"grid":u'grey',"ylabel":u'black',"xlabel":u'black',"title":u'black',"rect1":u'lightgrey',
                   "rect2":u'darkgrey',"rect3":u'grey',"met":u'black',"bt":u'black',"deltamet":u'grey',
                   "deltabt":u'grey',"markers":u'grey',"text":u'black',"watermarks":u'lightgrey',"Cline":u'grey'}
        
        #load selected dictionary
        if color == 1:
            for key in palette1.keys():
                self.palette[key] = palette1[key]
            
        if color == 2:
            for key in palette1.keys():
                self.palette[key] = palette2[key]
                
        if color == 3:
            dialog = graphColorDlg(self)
            if dialog.exec_():
                self.palette["background"] = unicode(dialog.backgroundLabel.text())
                self.palette["grid"] = unicode(dialog.gridLabel.text())
                self.palette["ylabel"] = unicode(dialog.yLabel.text())
                self.palette["xlabel"] = unicode(dialog.xLabel.text())
                self.palette["title"] = unicode(dialog.titleLabel.text())
                self.palette["rect1"] = unicode(dialog.rect1Label.text())
                self.palette["rect2"] = unicode(dialog.rect2Label.text())
                self.palette["rect3"] = unicode(dialog.rect3Label.text())
                self.palette["met"] = unicode(dialog.metLabel.text())
                self.palette["bt"] = unicode(dialog.btLabel.text())
                self.palette["deltamet"] = unicode(dialog.deltametLabel.text())
                self.palette["deltabt"] = unicode(dialog.deltabtLabel.text())
                self.palette["markers"] = unicode(dialog.markersLabel.text())
                self.palette["text"] = unicode(dialog.textLabel.text())
                self.palette["watermarks"] = unicode(dialog.watermarksLabel.text())
                self.palette["Cline"] = unicode(dialog.ClineLabel.text())

        #update screen with new colors
        self.fig.canvas.redraw()
            
    #draws a polar star graph to score cupping. It does not delete any profile data.            
    def flavorchart(self):
            pi = math.pi
            self.fig.clf()
            #create a new name ax1 instead of ax
            self.ax1 = self.fig.add_subplot(111, projection='polar', axisbg='white')
            g_angle = range(10,360,40) 
            self.ax1.set_thetagrids(g_angle)
            self.ax1.set_rmax(1.)
            self.ax1.set_autoscale_on(False)
            self.ax1.grid(True,linewidth=2,color='grey')
            
            #delete degrees ticks to anotate flavor characteristics 
            for tick in self.ax1.xaxis.get_major_ticks():
                tick.label1On = False

            #rename yaxis 
            locs = self.ax1.get_yticks()
            labels = []
            for i in range(len(locs)):
                    stringlabel = str(int(locs[i]*10))
                    labels.append(stringlabel)              
            self.ax1.set_yticklabels(labels,color=self.palette["xlabel"])
                        
            angles = [pi/2.]
            for i in range(9): angles.append(angles[-1] + 2.*pi/9.)
            

            #anotate labels
            self.ax1.annotate(self.flavorlabels[0] + u" - " + unicode(int(self.flavors[0]*10)),xy =(angles[0],.9),
                              xytext=(angles[0],1.1),horizontalalignment='left',verticalalignment='bottom')
            self.ax1.annotate(self.flavorlabels[1]+ u" - " + unicode(int(self.flavors[1]*10)),xy=(angles[1],.9),
                              xytext=(angles[1],1.1),horizontalalignment='right',verticalalignment='bottom')
            self.ax1.annotate(self.flavorlabels[2]+ u" - " + unicode(int(self.flavors[2]*10)),xy=(angles[2],.9),
                              xytext=(angles[2],1.1),horizontalalignment='right',verticalalignment='bottom')
            self.ax1.annotate(self.flavorlabels[3]+ u" - " + unicode(int(self.flavors[3]*10)),xy=(angles[3],.9),
                              xytext=(angles[3],1.1),horizontalalignment='right',verticalalignment='bottom')
            self.ax1.annotate(self.flavorlabels[4]+ u" - " + unicode(int(self.flavors[4]*10)),
                              xy=(angles[4],.9),xytext=(angles[4],1.1),horizontalalignment='right',verticalalignment='bottom')
            self.ax1.annotate(self.flavorlabels[5]+ u" - " + unicode(int(self.flavors[5]*10)),xy=(angles[5],.9),
                              xytext=(angles[5],1.1),horizontalalignment='left',verticalalignment='bottom')
            self.ax1.annotate(self.flavorlabels[6]+ u" - " + unicode(int(self.flavors[6]*10)),xy=(angles[6],.9),
                              xytext=(angles[6],1.1),horizontalalignment='left',verticalalignment='bottom')
            self.ax1.annotate(self.flavorlabels[7]+ u" - " + unicode(int(self.flavors[7]*10)),xy=(angles[7],.9),
                              xytext=(angles[7],1.1),horizontalalignment='left',verticalalignment='bottom')
            self.ax1.annotate(self.flavorlabels[8]+ u" - " + unicode(int(self.flavors[8]*10)),xy=(angles[8],.9),
                              xytext=(angles[8],1.1),horizontalalignment='left',verticalalignment='bottom')

            #Needs same dimension in order to plot. To close circle we may need one more element. 
            if len(angles) < len(self.flavors):
                angles.append(angles[-1])  

            score = 0.
            for i in range(9):
                score += self.flavors[i]
            score /= 9.
            score *= 100.
            
            txt = u"%.2f" %score

            self.ax1.annotate(txt,xy=(0.0,0.0),xytext=(0.0,0.0),horizontalalignment='center',verticalalignment='bottom',color='black')
            
            #fill in between with color: needs matplotlib version 1.0+
            #commented out to go back to matplotlib 0.99.1
            #self.ax1.fill_between(angles,0,self.flavors, facecolor='blue', alpha=0.1, interpolate=True)
               
            self.ax1.plot(angles,self.flavors)
            self.fig.canvas.draw()
            

    #Turns ON flag self.flagon to read and plot. Called from push button_1. 
    def OnMonitor(self):
        #Call start() to start the first measurement if no data collected
        if not len(self.timex):
            self.timeclock.start()        
        self.flagon = True
        aw.messagelabel.setText(u"Scope recording...")     
        aw.button_1.setDisabled(True)                     #button ON
        aw.button_1.setStyleSheet("QPushButton { background-color: #c4ff00}")
        
    #Turns OFF flag to read and plot. Called from push button_2. It tells when to stop recording
    def OffMonitor(self):
        self.flagon = False
        aw.messagelabel.setText(u"Scope stopped")
        aw.button_1.setDisabled(False)
        aw.button_1.setStyleSheet("QPushButton { background-color: #43d300 }")
        
    #Records charge (put beans in) marker. called from push button 'Charge'
    def markCharge(self):
        if self.flagon:
            if len(self.timex) >= 3:
                
                self.flagclock = True
                self.startend[0] = self.timeclock.elapsed()/1000.
                self.startend[1] = self.temp2[-1]

                # put a white marker on graph
                rect = patches.Rectangle( (self.startend[0]-1,0), width=.1, height=self.temp2[-1], color = self.palette["text"])
                self.ax.add_patch(rect)

                #anotate(value,xy=arrowtip-coordinates, xytext=text-coordinates, color, type)
                self.ax.annotate(u"%.1f"%(self.startend[1]), xy=(self.startend[0], self.startend[1]),xytext=(self.startend[0]-5,
                                self.startend[1]+50),color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
                #anotate time
                self.ax.annotate(u"START 00:00", xy=(self.startend[0], self.startend[1]),xytext=(self.startend[0]+5,
                                self.startend[1]-50),color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)

                message = u"Roast time starts now. 00:00 BT = " + unicode(self.startend[1]) + self.mode

                aw.label1.setStyleSheet("background-color:'#FF9966';")
                aw.label1.setText( "<font color='black'><b>Roast time<\b></font>")

                aw.button_8.setDisabled(True)
                aw.button_8.setFlat(True)
            else:
                message = u"Not enough variables collected yet. Try again in a few seconds"
        else:
            message = u"Scope is OFF"
            
        aw.messagelabel.setText(message)

    #redord 1C start markers of BT. called from push button_3 of application window
    def mark1Cstart(self):
        if self.flagon:
            # record 1Cs only if Charge mark has been done
            if self.startend[0]:
                
                self.varC[0] = self.timeclock.elapsed()/1000.
                self.varC[1] = self.temp2[-1]
                
                #calculate time elapsed since charge time
                st1 = u"1CS " + self.stringfromseconds(self.varC[0]-self.startend[0])
                #anotate temperature
                self.ax.annotate(u"%.1f"%(self.varC[1]), xy=(self.varC[0], self.varC[1]),xytext=(self.varC[0]-5,
                                self.varC[1]+50), color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
                #anotate time
                self.ax.annotate(st1, xy=(self.varC[0], self.varC[1]),xytext=(self.varC[0],self.varC[1]-50),
                                 color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)

                aw.button_3.setDisabled(True)
                aw.button_3.setFlat(True)
                
                message = u"1C START recorded at " + st1 + u" BT = " + unicode(self.varC[1]) + self.mode
            
            else:
                message = u"Charge mark is missing. Do that first"
        else:
            message = u"Scope is OFF"

        #set message at bottom
        aw.messagelabel.setText(message)

    #record 1C end markers of BT. called from button_4 of application window
    def mark1Cend(self):
        if self.flagon:
            # record only if 1Cs has been saved
            if self.varC[0]:
                self.varC[2] = self.timeclock.elapsed()/1000.
                self.varC[3] = self.temp2[-1]
                
                #calculate time elapsed since charge time
                st1 = u"1CE " + self.stringfromseconds(self.varC[2]-self.startend[0]) 
                #anotate temperature
                self.ax.annotate(u"%.1f"%(self.varC[3]), xy=(self.varC[2], self.varC[3]),xytext=(self.varC[2]-5,
                                self.varC[3]+70),color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
                #anotate time
                self.ax.annotate(st1, xy=(self.varC[2], self.varC[3]),xytext=(self.varC[2],self.varC[3]-80),
                                color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)

                self.ax.axvspan(self.varC[0], self.varC[2], facecolor=self.palette["watermarks"], alpha=0.2)

                aw.button_4.setDisabled(True)
                aw.button_4.setFlat(True)

                message = u"1C END recorded at " + st1 + " BT = " + unicode(self.varC[3]) + self.mode
            else:
                message = u"1Cs mark missing. Do that first"
        else:
            message = u"Scope is OFF"
            
        aw.messagelabel.setText(message)
        
    #record 2C start markers of BT. Called from button_5 of application window
    def mark2Cstart(self):
        if self.flagon:
            self.varC[4] = self.timeclock.elapsed()/1000.
            self.varC[5] = self.temp2[-1]
            
            st1 = u"2CS " + self.stringfromseconds(self.varC[4]-self.startend[0]) 
            self.ax.annotate(u"%.1f"%(self.varC[5]), xy=(self.varC[4], self.varC[5]),xytext=(self.varC[4]-5,
                                self.varC[5]+90),color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)      
            self.ax.annotate(st1, xy=(self.varC[4], self.varC[5]),xytext=(self.varC[4],self.varC[5]-110),
                                 color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)

            aw.button_5.setDisabled(True)
            aw.button_5.setFlat(True)

            message = u"2C START recorded at " + st1 + " BT = " + unicode(self.varC[5]) + self.mode
        else:
            message = u"Scope is OFF"
            
        aw.messagelabel.setText(message)
        
    #record 2C end markers of BT. Called from button_6  of application window
    def mark2Cend(self):
        if self.flagon:
            # record only if 1Cs has been saved
            if self.varC[4]:
                
                self.varC[6] = self.timeclock.elapsed()/1000. 
                self.varC[7] = self.temp2[-1]
                    
                st1 =  u"2CE " + self.stringfromseconds(self.varC[6]-self.startend[0])
                #anotate temperature
                self.ax.annotate(u"%.1f"%(self.varC[7]), xy=(self.varC[6], self.varC[7]),xytext=(self.varC[6]-5,
                                self.varC[7]+50),color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
                #anotate time
                self.ax.annotate(st1, xy=(self.varC[6], self.varC[7]),xytext=(self.varC[6],self.varC[7]-40),
                                 color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)


                self.ax.axvspan(self.varC[4], self.varC[6], facecolor=self.palette["watermarks"], alpha=0.2)

                aw.button_6.setDisabled(True)
                aw.button_6.setFlat(True)

                message = u"2C END recorded at " + st1 + " BT = " + unicode(self.varC[7]) + self.mode
            else:
                message = u"2Cs mark missing. Do that first"
        else:
            message = u"Scope is OFF"
            
        aw.messagelabel.setText(message)            

    #record end of roast (drop of beans). Called from push button 'Drop'
    def markDrop(self):
        if self.flagon:
        
            self.startend[2] = self.timeclock.elapsed()/1000.
            self.startend[3] = self.temp2[-1]
            
            st1 = u"END " + self.stringfromseconds(self.startend[2]-self.startend[0]) 
            #anotate temperature
            self.ax.annotate(u"%.1f"%(self.startend[3]), xy=(self.startend[2], self.startend[3]),xytext=(self.startend[2]-5,
                                self.startend[3]+70),color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
            #anotate time
            self.ax.annotate(st1, xy=(self.startend[2], self.startend[3]),xytext=(self.startend[2],self.startend[3]-80),
                                 color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=0.8)
            
            self.writestatistics()
            
            aw.label1.setStyleSheet("background-color:'#66FF66';")
            aw.label1.setText( "<font color='black'><b>Monitor time<\b></font>")
            
            aw.button_9.setDisabled(True)
            aw.button_9.setFlat(True)
            
            message = u"Roast ENDED at " + st1 + " BT = " + unicode(self.startend[-1]) + self.mode

        else:
            message = u"Scope is OFF"
            
        aw.messagelabel.setText(message)

    # Writes information about the finished profile in the graph
    def writestatistics(self):
        TP_index = aw.findTP()
        #find when dry phase ends 
        dryEndIndex = aw.findDryEnd(TP_index)
        BTdrycross = self.temp2[dryEndIndex]
        
        #self.varC [1C starttime[0],1C startTemp[1],  1C endtime[2],1C endtemp[3],  2C starttime[4], 2C startTemp[5],  2C endtime[6], 2C endtemp[7]]
        #self.startend [starttime[0], starttempBT[1], endtime[2],endtempBT[3]]      
        if self.startend[2]:
            totaltime = int(self.startend[2]-self.startend[0])
            self.statisticstimes[0] = totaltime
            #if 1Ce use middle point of 1Cs and 1Ce            
            if self.varC[2]:
                
                dryphasetime = int(self.timex[dryEndIndex] - self.startend[0])
                midphasetime = int(self.varC[0] - self.timex[dryEndIndex])
                finishphasetime = int(self.startend[2]- self.varC[0])
                                   
            else: #very light roast)
                #use 1Cs (start of 1C) as 1C
                dryphasetime = int(self.timex[dryEndIndex] - self.startend[0])
                midphasetime = int(self.varC[0] - self.timex[dryEndIndex])     
                finishphasetime = int(self.startend[2] - self.varC[0])
                
            self.statisticstimes[1] = dryphasetime
            self.statisticstimes[2] = midphasetime
            self.statisticstimes[3] = finishphasetime

            #dry time string
            st1 = self.stringfromseconds(dryphasetime)

            #mid time string
            st2 = self.stringfromseconds(midphasetime)               

            #finish time string
            st3 = self.stringfromseconds(finishphasetime)

            if self.statisticsflags[1]:
                #Draw finish phase rectangle
                #chech to see if end of 1C exists. If so, use half between start of 1C and end of 1C. Otherwise use only the start of 1C
                rect = patches.Rectangle( (self.varC[0], self.statisticsheight), width = finishphasetime, height = 5,
                                            color = self.palette["rect3"],alpha=0.5)
                self.ax.add_patch(rect)
                
                # Draw mid phase rectangle
                rect = patches.Rectangle( (self.startend[0]+dryphasetime, self.statisticsheight), width = midphasetime, height = 5,
                                          color = self.palette["rect2"],alpha=0.5)
                self.ax.add_patch(rect)

                # Draw dry phase rectangle
                rect = patches.Rectangle( (self.startend[0], self.statisticsheight), width = dryphasetime, height = 5,
                                          color = self.palette["rect1"],alpha=0.5)
                self.ax.add_patch(rect)


            dryphaseP = dryphasetime*100/totaltime
            midphaseP = midphasetime*100/totaltime
            finishphaseP = finishphasetime*100/totaltime

            if self.statisticsflags[0]:            
                self.ax.text(self.startend[0]+ dryphasetime/3,self.statisticsupper,st1 + u" "+ unicode(int(dryphaseP))+u"%",color=self.palette["text"])
                self.ax.text(self.startend[0]+ dryphasetime+midphasetime/3,self.statisticsupper,st2+ " " + unicode(int(midphaseP))+u"%",color=self.palette["text"])
                self.ax.text(self.startend[0]+ dryphasetime+midphasetime+finishphasetime/3,self.statisticsupper,st3 + u" " + unicode(int(finishphaseP))+ u"%",color=self.palette["text"])

            if self.statisticsflags[2]:
                (st1,st2,st3) = aw.defect_estimation()

                #find Lowest Point in BT
                LP = 1000 
                if TP_index >= 0:
                    LP = self.temp2[TP_index]
                    
                rates_of_changes = aw.RoR(TP_index,dryEndIndex)

                st1 += u"  (%.1f deg/min)"%rates_of_changes[0]
                st2 += u"  (%.1f deg/min)"%rates_of_changes[1]
                st3 += u"  (%.1f deg/min)"%rates_of_changes[2]
        
                #Write flavor estimation
                self.ax.text(self.startend[0],self.statisticslower,st1,color=self.palette["text"],fontsize=11)
                self.ax.text(self.startend[0]+ dryphasetime,self.statisticslower,st2,color=self.palette["text"],fontsize=11)
                self.ax.text(self.startend[0]+ dryphasetime+midphasetime,self.statisticslower,st3,color=self.palette["text"],fontsize=11)

            if self.statisticsflags[3]:          
                #calculate AREA under BT and ET
                AccBT = 0.0
                AccMET = 0.0

                #find the index of time when the roasts starts and finish 
                for i in range(len(self.timex)):
                    if self.timex[i] > self.startend[0]:
                        break            
                for j in range(len(self.timex)):
                    if self.timex[j] > self.startend[2]:
                        break

                for k in range(i,j):
                    timeD = self.timex[k+1] - self.timex[k]
                    AccBT += self.temp2[k]*timeD
                    AccMET += self.temp1[k]*timeD
                    
                deltaAcc = int(AccMET) - int(AccBT)
                        
                lowestBT = u"%.1f"%LP
                timeLP = unicode(self.stringfromseconds(self.timex[k] - self.startend[0]))
                time = self.stringfromseconds(self.startend[2]-self.startend[0])
                #end temperature 
                
                strline = (u"[BT = " + lowestBT + self.mode + u" - " + u"%.1f"%self.startend[3] + self.mode +
                            u"] [ETarea - BTarea = " + unicode(deltaAcc) + u"] [Time = " +time +u"]")
                            
                #text metrics 
                if self.mode == u"C":
                    dist = -47
                else:
                    dist = -90
                self.ax.text(-100,dist, strline,color = self.palette["text"],fontsize=11)

    #Marks location in graph of special events. For example change a fan setting.
    #Uses the position of the time index (variable self.timex) as location in time
    def EventRecord(self):
        i = len(self.timex)-1
        if i > 0:
            self.specialevents.append(i)
            Nevents = len(self.specialevents)
            temp = unicode(self.temp2[i])
            time = self.stringfromseconds(self.timex[i])
            message = u"Event number "+ unicode(Nevents) + u"recorded at " + unicode(Nevents) +u" BT = " + temp + u" Time = " + time
            aw.messagelabel.setText(message)
            self.ax.text(self.timex[i],self.temp2[i],Nevents,color=self.palette["text"])


    def movebackground(self,direction,step):
        lt = len(self.timeB)
        le = len(self.backgroundET)
        lb = len(self.backgroundBT)
        #all background curves must have same dimension in order to plot. Check just in case.
        if lt > 1 and lt == le and lb == le:
            if  direction == u"up":
                for i in range(lt):
                    self.backgroundET[i] += step
                    self.backgroundBT[i] += step
                    
                if self.varCB[1]:
                   self.varCB[1] += step
                if self.varCB[3]:
                   self.varCB[3] += step
                if self.varCB[5]:
                   self.varCB[5] += step
                if self.varCB[7]:
                   self.varCB[7] += step
                self.startendB[1] += step
                self.startendB[3] += step
                
            elif direction == u"left":
                for i in range(lt):
                    self.timeB[i] -= step
                    
                if self.varCB[0]:
                   self.varCB[0] -= step
                if self.varCB[2]:
                   self.varCB[2] -= step
                if self.varCB[4]:
                   self.varCB[4] -= step
                if self.varCB[6]:
                   self.varCB[6] -= step
                self.startendB[0] -= step
                self.startendB[2] -= step
                
            elif direction == u"right":
                for i in range(lt):
                    self.timeB[i] += step
                    
                if self.varCB[0]:
                   self.varCB[0] += step
                if self.varCB[2]:
                   self.varCB[2] += step
                if self.varCB[4]:
                   self.varCB[4] += step
                if self.varCB[6]:
                   self.varCB[6] += step
                self.startendB[0] += step
                self.startendB[2] += step
                    
            elif direction == u"down":
                for i in range(lt):
                    self.backgroundET[i] -= step
                    self.backgroundBT[i] -= step
                    
                if self.varCB[1]:
                   self.varCB[1] -= step
                if self.varCB[3]:
                   self.varCB[3] -= step
                if self.varCB[5]:
                   self.varCB[5] -= step
                if self.varCB[7]:
                   self.varCB[7] -= step  
                self.startendB[1] -= step
                self.startendB[3] -= step    
        else:
            aw.messagelabel.setText(u"unable to move background")
            return

#######################################################################################
#####   temporary hack for windows till better solution found about toolbar icon problem
#####   with py2exe and svg

# changed "NavigationToolbar" for "VMToolbar" in ApplicationWindow
        
class VMToolbar(NavigationToolbar):
    def __init__(self, plotCanvas, parent):
        NavigationToolbar.__init__(self, plotCanvas, parent)


    def _icon(self, name):
        #dirty hack to use exclusively .png and thus avoid .svg usage
        #because .exe generation is problematic with .svg
        if platf != u'Darwin':
            name = name.replace('.svg','.png')
        return QIcon(os.path.join(self.basedir, name))
    

########################################################################################                            
#################### MAIN APPLICATION WINDOW ###########################################
########################################################################################
            
class ApplicationWindow(QMainWindow):
    def __init__(self, parent = None):
        self.applicationDirectory =  QDir().current().absolutePath()
        super(ApplicationWindow, self).__init__(parent)
        # set window title
        self.setWindowTitle(u"Artisan " + __version__)        

        # self.profilepath is obteined at dirstruct() and points to profiles/year/month. file-open/save will point to profilepath
        self.profilepath = u""

        # on the Mac preferences should be stored outside of applications in the users ~/Library/Preferences path
        if platf == u'Darwin':
            preference_path = QDir().homePath().append(QString("/Library/Preferences/Artisan/"))
            preference_dir = QDir()
            preference_dir.setPath(preference_path)
            if not preference_dir.exists():
                QDir().mkpath(preference_path)
            QDir().setCurrent(preference_path)
        
        #checks executable directory. dirstruct() checks or creates: /profile/year/month directory to store profiles
        self.dirstruct()
        
        self.printer = QPrinter()
        self.printer.setPageSize(QPrinter.Letter)
        
        self.main_widget = QWidget(self)
        #set a minimum size (main window can be bigger but never smaller)
        self.main_widget.setMinimumWidth(811)
        self.main_widget.setMinimumHeight(670)

        # create MASTER grid layout manager to place all widgets
        gl = QGridLayout(self.main_widget)
                
        #create vertical/horizontal boxes layout managers for buttons,etc
        buttonVVbl = QVBoxLayout()
        buttonHHbl = QHBoxLayout()
        pidHHbl = QHBoxLayout()
        
        #create Matplotlib canvas widget 
        self.qmc = tgraphcanvas(self.main_widget)


        ###################################################################
        # NavigationToolbar VMToolbar
        ntb = VMToolbar(self.qmc, self.main_widget)

        
        #########################################################
        #create a serial port object
        self.ser = serialport()
        # create a PID object
        self.pid = FujiPID()
        

        ###################################################################################
        #restore SETTINGS  after creating serial port, tgraphcanvas, and PID. 
        self.settingsLoad()        
        
        #create a Label object to display program status information
        self.messagelabel = QLabel()
        
        self.HUDstatus = QStatusBar()
        self.HUDstatus.setSizeGripEnabled(False)
        self.HUDstatus .setStyleSheet("background-color:'lightgrey';")

        #create START STOP buttons        
        self.button_1 = QPushButton("ON")
        self.button_1.setStyleSheet("QPushButton { background-color: #43d300 }")
        self.button_1.setMaximumSize(90, 50)
        self.button_1.setMinimumHeight(50)
        self.button_1.setToolTip("<font color=red size=2><b>" + "Press here to Start monitoring" + "</font></b>")
        self.connect(self.button_1, SIGNAL("clicked()"), self.qmc.OnMonitor)

        self.button_2 = QPushButton("OFF")
        self.button_2.setStyleSheet("QPushButton { background-color: #ff664b }")
        self.button_2.setMaximumSize(90, 50)
        self.button_2.setMinimumHeight(50)
        self.button_2.setToolTip("<font color=red size=2><b>" + "Press here to Stop monitoring" + "</font></b>")
        self.connect(self.button_2, SIGNAL("clicked()"), self.qmc.OffMonitor)

        #create 1C START, 1C END, 2C START and 2C END buttons
        self.button_3 = QPushButton("1C START")
        self.button_3.setStyleSheet("QPushButton { background-color: orange }")
        self.button_3.setMaximumSize(90, 50)
        self.button_3.setMinimumHeight(50)
        self.button_3.setToolTip("Press here to mark begining of 1C crack")
        self.connect(self.button_3, SIGNAL("clicked()"), self.qmc.mark1Cstart)

        self.button_4 = QPushButton("1C END")
        self.button_4.setStyleSheet("QPushButton { background-color: orange }")
        self.button_4.setMaximumSize(90, 50)
        self.button_4.setMinimumHeight(50)
        self.button_4.setToolTip("Press here to mark the end of 1C")
        self.connect(self.button_4, SIGNAL("clicked()"), self.qmc.mark1Cend)

        self.button_5 = QPushButton("2C START")
        self.button_5.setStyleSheet("QPushButton { background-color: orange }")
        self.button_5.setMaximumSize(90, 50)
        self.button_5.setMinimumHeight(50)
        self.button_5.setToolTip("Press here to mark the begining of 2C")
        self.connect(self.button_5, SIGNAL("clicked()"), self.qmc.mark2Cstart)

        self.button_6 = QPushButton("2C END")
        self.button_6.setStyleSheet("QPushButton { background-color: orange }")
        self.button_6.setMaximumSize(90, 50)
        self.button_6.setMinimumHeight(50)
        self.button_6.setToolTip("Press here to mark the end of 2C")
        self.connect(self.button_6, SIGNAL("clicked()"), self.qmc.mark2Cend)

        #create RESET button
        self.button_7 = QPushButton("RESET")
        self.button_7.setStyleSheet("QPushButton { background-color: white }")
        self.button_7.setMaximumSize(90, 50)
        self.button_7.setMinimumHeight(50)
        self.button_7.setToolTip("<font color=red size=2><b>" + "Reset graphs and time" + "</font></b>")
        self.connect(self.button_7, SIGNAL("clicked()"), self.qmc.reset)

        #create CHARGE button
        self.button_8 = QPushButton("CHARGE")
        self.button_8.setStyleSheet("QPushButton { background-color: #f07800 }")
        self.button_8.setMaximumSize(90, 50)
        self.button_8.setMinimumHeight(50)
        self.button_8.setToolTip("<font color=red size=2><b>" + "Press here to mark the begining of the roast" + "</font></b>")
        self.connect(self.button_8, SIGNAL("clicked()"), self.qmc.markCharge)

        #create DROP button
        self.button_9 = QPushButton("DROP")
        self.button_9.setStyleSheet("QPushButton { background-color: #f07800 }")
        self.button_9.setMaximumSize(90, 50)
        self.button_9.setMinimumHeight(50)
        self.button_9.setToolTip("<font color=red size=2><b>" + "Press here to Stop monitoring" + "</font></b>")
        self.connect(self.button_9, SIGNAL("clicked()"), self.qmc.markDrop)

        #create PID control button
        self.button_10 = QPushButton("PID")
        self.button_10.setStyleSheet("QPushButton { background-color: '#92C3FF'}")
        self.button_10.setMaximumSize(90, 50)
        self.button_10.setMinimumHeight(50)
        self.connect(self.button_10, SIGNAL("clicked()"), self.PIDcontrol)        

        #create Event record button
        self.button_11 = QPushButton("Event")
        self.button_11.setStyleSheet("QPushButton { background-color: yellow}")
        self.button_11.setMaximumSize(90, 50)
        self.button_11.setMinimumHeight(50)
        self.connect(self.button_11, SIGNAL("clicked()"), self.qmc.EventRecord) 

        #create PID+5 button
        self.button_12 = QPushButton("SV +5")
        self.button_12.setStyleSheet("QPushButton { background-color: #ffaaff}")
        self.button_12.setMaximumSize(90, 50)
        self.button_12.setMinimumHeight(50)
        #self.connect(self.button_12, SIGNAL("clicked()"), )
        #create PID+10 button
        self.button_13 = QPushButton("SV +10")
        self.button_13.setStyleSheet("QPushButton { background-color: #ffaaff}")
        self.button_13.setMaximumSize(90, 50)
        self.button_13.setMinimumHeight(50)
        #self.connect(self.button_13, SIGNAL("clicked()"),)
        #create PID+20 button
        self.button_14 = QPushButton("SV +20")
        self.button_14.setStyleSheet("QPushButton { background-color: #ffaaff}")
        self.button_14.setMaximumSize(90, 50)
        self.button_14.setMinimumHeight(50)
        #self.connect(self.button_14, SIGNAL("clicked()"),)
        #create PID-20 button
        self.button_15 = QPushButton("SV -20")
        self.button_15.setStyleSheet("QPushButton { background-color: lightblue}")
        self.button_15.setMaximumSize(90, 50)
        self.button_15.setMinimumHeight(50)
        #self.connect(self.button_15, SIGNAL("clicked()"),)
        #create PID-10 button
        self.button_16 = QPushButton("SV -10")
        self.button_16.setStyleSheet("QPushButton { background-color: lightblue}")
        self.button_16.setMaximumSize(90, 50)
        self.button_16.setMinimumHeight(50)
        #self.connect(self.button_16, SIGNAL("clicked()"),)
        #create PID-5 button
        self.button_17 = QPushButton("SV -5")
        self.button_17.setStyleSheet("QPushButton { background-color: lightblue}")
        self.button_17.setMaximumSize(90, 50)
        self.button_17.setMinimumHeight(50)

        #create HUD button
        self.button_18 = QPushButton("HUD")
        self.button_18.setStyleSheet("QPushButton { background-color: #b5baff }")
        self.button_18.setMaximumSize(90, 50)
        self.button_18.setMinimumHeight(50)
        self.button_18.setToolTip("<font color=red size=2><b>" +"BT projection" + "</font></b>")
        self.connect(self.button_18, SIGNAL("clicked()"), self.qmc.toggleHUD)

        #connect PID sv easy buttons
        self.connect(self.button_12, SIGNAL("clicked()"),lambda x=5: self.pid.adjustsv(x))
        self.connect(self.button_13, SIGNAL("clicked()"),lambda x=10: self.pid.adjustsv(x))
        self.connect(self.button_14, SIGNAL("clicked()"),lambda x=20: self.pid.adjustsv(x))
        self.connect(self.button_15, SIGNAL("clicked()"),lambda x=-20: self.pid.adjustsv(x))
        self.connect(self.button_16, SIGNAL("clicked()"),lambda x=-10: self.pid.adjustsv(x))
        self.connect(self.button_17, SIGNAL("clicked()"),lambda x=-5: self.pid.adjustsv(x))
        
        #only leave operational the control button if the device is Fuji PID
        #the SV buttons are activated from the PID control panel 
        if self.qmc.device > 0:
            self.button_10.setDisabled(True)
            self.button_10.setFlat(True)
            
        self.button_12.setDisabled(True)
        self.button_13.setDisabled(True)
        self.button_14.setDisabled(True)
        self.button_15.setDisabled(True)
        self.button_16.setDisabled(True)
        self.button_17.setDisabled(True)            
        self.button_12.setFlat(True)
        self.button_13.setFlat(True)
        self.button_14.setFlat(True)
        self.button_15.setFlat(True)
        self.button_16.setFlat(True)
        self.button_17.setFlat(True)
        
        #create LCD displays
        #RIGHT COLUMN
        self.lcd1 = QLCDNumber() # time
        self.lcd2 = QLCDNumber() # Temperature MET
        self.lcd3 = QLCDNumber() # Temperature BT
        self.lcd4 = QLCDNumber() # rate of change MET
        self.lcd5 = QLCDNumber() # rate of change BT
        self.lcd6 = QLCDNumber() # pid sv
        
        self.lcd1.setStyleSheet("QLCDNumber { background-color: black }")
        self.lcd2.setStyleSheet("QLCDNumber { background-color: black }")
        self.lcd3.setStyleSheet("QLCDNumber { background-color: black }")
        self.lcd4.setStyleSheet("QLCDNumber { background-color: black }")
        self.lcd5.setStyleSheet("QLCDNumber { background-color: black }")
        self.lcd6.setStyleSheet("QLCDNumber { background-color: black }")
        
        #create labels for LCDs
        #time
        self.label1 = QLabel()
        #self.label1.setStyleSheet("background-color:'#CCCCCC';")
        self.label1.setText( "<font color='black'><b>Time<\b></font>")
        #MET
        label2 = QLabel()
        #label2.setStyleSheet("background-color:'#CCCCCC';")
        label2.setText( "<font color='black'><b>E.T.<\b></font>")
        #BT
        label3 = QLabel()
        #label3.setStyleSheet("background-color:'#CCCCCC';")
        label3.setText( "<font color='black'><b>B.T.<\b></font>")
        #DELTA MET
        label4 = QLabel()
        #label4.setStyleSheet("background-color:'#CCCCCC';")
        label4.setText( "<font color='black'><b>Delta E.T.<\b></font>")
        # DELTA BT
        label5 = QLabel()
        #label5.setStyleSheet("background-color:'#CCCCCC';")
        label5.setText( "<font color='black'><b>Delta B.T.<\b></font>")
        # pid sv
        label6 = QLabel()
        #label6.setStyleSheet("background-color:'#CCCCCC';")
        label6.setText( "<font color='black'><b>PID S.V.<\b></font>")

        #place control buttons + LCDs inside vertical button layout manager      
        buttonVVbl.addWidget(label6)
        buttonVVbl.addWidget(self.lcd6)
        buttonVVbl.addWidget(label2)
        buttonVVbl.addWidget(self.lcd2)
        buttonVVbl.addWidget(label3)
        buttonVVbl.addWidget(self.lcd3)
        buttonVVbl.addWidget(label4)
        buttonVVbl.addWidget(self.lcd4)
        buttonVVbl.addWidget(label5)
        buttonVVbl.addWidget(self.lcd5)

        
        #place mark buttons inside the horizontal button layout manager
        
        buttonHHbl.addWidget(self.button_1)
        buttonHHbl.addWidget(self.button_8)
        buttonHHbl.addWidget(self.button_3)
        buttonHHbl.addWidget(self.button_4)
        buttonHHbl.addWidget(self.button_5)
        buttonHHbl.addWidget(self.button_6)
        buttonHHbl.addWidget(self.button_9)
        buttonHHbl.addWidget(self.button_2)
        buttonHHbl.addWidget(self.button_11)

        # place pid button + LCDs in pid layout manager
        pidHHbl.addWidget(self.button_10)
        pidHHbl.addWidget(self.button_12)
        pidHHbl.addWidget(self.button_13)
        pidHHbl.addWidget(self.button_14)
        pidHHbl.addWidget(self.button_15)
        pidHHbl.addWidget(self.button_16)
        pidHHbl.addWidget(self.button_17)
        pidHHbl.addWidget(self.button_18)
        pidHHbl.addWidget(self.button_7)

        #pack all into the grid MASTER layout manager (widget,row,column)
        gl.addWidget(ntb,0,0)
        gl.addWidget(self.lcd1,0,1)  #timer LCD
        gl.addWidget(self.messagelabel,1,0) #add a message label to give program feedback to user
        gl.addLayout(pidHHbl,2,0)  #pid button + LCDS
        gl.addWidget(self.HUDstatus,3,0)
        gl.addWidget(self.qmc,4,0)
        gl.addLayout(buttonVVbl,4,1) #place buttonlayout manager inside grid box layout manager
        gl.addLayout(buttonHHbl,5,0) #place buttonlayout manager inside grid box layout manager

        ###############  create MENUS 
        self.fileMenu = self.menuBar().addMenu("&File")
        self.GraphMenu = self.menuBar().addMenu("&Roast")
        self.ConfMenu = self.menuBar().addMenu("&Conf")
        self.helpMenu = self.menuBar().addMenu("&Help")
        #FILE menu
        fileLoadAction = QAction("Open Profile",self)
        fileLoadAction.setShortcut(QKeySequence.Open)
        self.connect(fileLoadAction,SIGNAL("triggered()"),self.fileLoad)
        self.fileMenu.addAction(fileLoadAction)
        
        fileSaveAction = QAction("Save Profile",self)
        fileSaveAction.setShortcut(QKeySequence.Save)
        self.connect(fileSaveAction,SIGNAL("triggered()"),self.fileSave)
        self.fileMenu.addAction(fileSaveAction)        

        saveGraphMenu = self.fileMenu.addMenu("Save Graph Image")

        fullsizeAction = QAction("Full size",self)
        self.connect(fullsizeAction,SIGNAL("triggered()"),lambda x=0,y=1:self.resize(x,y))
        saveGraphMenu.addAction(fullsizeAction)

        saveGraphMenuHB = saveGraphMenu.addMenu("Home-Barista.com")
        saveGraphMenuCG = saveGraphMenu.addMenu("CoffeeGeek.com")

        HomeBaristaActionLow = QAction("Low quality",self)
        self.connect(HomeBaristaActionLow,SIGNAL("triggered()"),lambda x=700,y=0:self.resize(x,y))
        saveGraphMenuHB.addAction(HomeBaristaActionLow)

        HomeBaristaActionHigh = QAction("High quality",self)
        self.connect(HomeBaristaActionHigh,SIGNAL("triggered()"),lambda x=700,y=1:self.resize(x,y))
        saveGraphMenuHB.addAction(HomeBaristaActionHigh)

        CoffeeGeekActionLow = QAction("Low quality",self)
        self.connect(CoffeeGeekActionLow,SIGNAL("triggered()"),lambda x=500,y=0:self.resize(x,y))
        saveGraphMenuCG.addAction(CoffeeGeekActionLow)

        CoffeeGeekActionHigh = QAction("High quality",self)
        self.connect(CoffeeGeekActionHigh,SIGNAL("triggered()"),lambda x=500,y=1:self.resize(x,y))
        saveGraphMenuCG.addAction(CoffeeGeekActionHigh)

        printAction = QAction("Print Graph Image",self)
        printAction.setShortcut(QKeySequence.Print)
        self.connect(printAction,SIGNAL("triggered()"),self.filePrint)
        self.fileMenu.addAction(printAction)

        htmlAction = QAction("Create HTML Report",self)
        self.connect(htmlAction,SIGNAL("triggered()"),self.htmlReport)
        htmlAction.setShortcut("Ctrl+R")
        self.fileMenu.addAction(htmlAction)

        importMenu = self.fileMenu.addMenu("Import other formats")

        importHH506RAAction = QAction("HH506RA",self)
        self.connect(importHH506RAAction,SIGNAL("triggered()"),self.importHH506RA)
        importMenu.addAction(importHH506RAAction)

        self.fileMenu.addMenu(importMenu)       


        # ROAST menu
        editGraphAction = QAction("Roast properties",self)
        self.connect(editGraphAction ,SIGNAL("triggered()"),self.editgraph)
        self.GraphMenu.addAction(editGraphAction)

        flavorAction = QAction("View Flavor",self)
        self.connect(flavorAction ,SIGNAL("triggered()"),self.flavorchart)
        self.GraphMenu.addAction(flavorAction)

        temperatureMenu = self.GraphMenu.addMenu("Temperature")
        colorMenu = self.GraphMenu.addMenu("Color")
        
        graphModeAction1 = QAction("Default Color mode",self)
        self.connect(graphModeAction1,SIGNAL("triggered()"),lambda x=1:self.qmc.changeGColor(x))
        colorMenu.addAction(graphModeAction1)

        graphModeAction2 = QAction("Black and White color mode",self)
        self.connect(graphModeAction2,SIGNAL("triggered()"),lambda x=2:self.qmc.changeGColor(x))
        colorMenu.addAction(graphModeAction2)

        graphModeAction3 = QAction("Customize colors",self)
        self.connect(graphModeAction3,SIGNAL("triggered()"),lambda x=3:self.qmc.changeGColor(x))
        colorMenu.addAction(graphModeAction3)

        ConvertToFahrenheitAction = QAction("Convert profile to Fahrenheit",self)
        self.connect(ConvertToFahrenheitAction,SIGNAL("triggered()"),lambda t="F":self.qmc.convertTemperature(t))
        temperatureMenu.addAction(ConvertToFahrenheitAction)

        ConvertToCelsiusAction = QAction("Convert profile to Celsius",self)
        self.connect(ConvertToCelsiusAction,SIGNAL("triggered()"),lambda t="C":self.qmc.convertTemperature(t))
        temperatureMenu.addAction(ConvertToCelsiusAction)

        FahrenheitAction = QAction("Set Display in Fahrenheit Mode",self)
        self.connect(FahrenheitAction,SIGNAL("triggered()"),self.qmc.fahrenheitMode)
        temperatureMenu.addAction(FahrenheitAction)

        CelsiusAction = QAction("Set Display in Celsius Mode",self)
        self.connect(CelsiusAction,SIGNAL("triggered()"),self.qmc.celsiusMode)
        temperatureMenu.addAction(CelsiusAction)

        phasesGraphAction = QAction("Phases",self)
        self.connect(phasesGraphAction,SIGNAL("triggered()"),self.editphases)
        self.GraphMenu.addAction(phasesGraphAction)
       
        StatisticsAction = QAction("Statistics",self)
        self.connect(StatisticsAction,SIGNAL("triggered()"),self.showstatistics)
        self.GraphMenu.addAction(StatisticsAction)     


        calculatorAction = QAction("Calculator",self)
        self.connect(calculatorAction,SIGNAL("triggered()"),self.calculator)
        self.GraphMenu.addAction(calculatorAction)   

        backgroundAction = QAction("Profile Background",self)
        self.connect(backgroundAction,SIGNAL("triggered()"),self.background)
        self.GraphMenu.addAction(backgroundAction)  

        hudAction = QAction("HUD targets",self)
        self.connect(hudAction,SIGNAL("triggered()"),self.hudshow)
        self.GraphMenu.addAction(hudAction)  
        
        # CONFIGURATION menu
        deviceAction = QAction("Device", self)
        self.connect(deviceAction,SIGNAL("triggered()"),self.deviceassigment)
        self.ConfMenu.addAction(deviceAction) 
        
        commportAction = QAction("Serial Port",self)
        self.connect(commportAction,SIGNAL("triggered()"),self.setcommport)
        self.ConfMenu.addAction(commportAction)

        calibrateDelayAction = QAction("Set time interval between readings",self)
        self.connect(calibrateDelayAction,SIGNAL("triggered()"),self.calibratedelay)
        self.ConfMenu.addAction(calibrateDelayAction)

        
        # HELP menu
        helpAboutAction = QAction("About",self)
        self.connect(helpAboutAction,SIGNAL("triggered()"),self.helpAbout)
        self.helpMenu.addAction(helpAboutAction)

        helpDocumentationAction = QAction("Documentation",self)
        self.connect(helpDocumentationAction,SIGNAL("triggered()"),self.helpHelp)
        self.helpMenu.addAction(helpDocumentationAction)        

        errorAction = QAction("Error log",self)
        self.connect(errorAction,SIGNAL("triggered()"),self.viewErrorLog)
        self.helpMenu.addAction(errorAction)

        # set the focus on the main widget
        self.main_widget.setFocus()

        # set the central widget of MainWindow to main_widget
        self.setCentralWidget(self.main_widget)   


    #loads stored profiles. Called from file menu        
    def fileLoad(self):
        f = None
        try:        
            fname = unicode(QFileDialog.getOpenFileName(self,"Load Profile",self.profilepath,"*.txt"))
            self.qmc.reset()

            f = QFile(fname)
            if not f.open(QIODevice.ReadOnly):
                raise IOError, unicode(f.errorString())
            
            stream = QTextStream(f)

            #variables to read on the text file are initialized as empty lists
            self.qmc.varC,self.qmc.startend, self.qmc.timex, self.qmc.temp1, self.qmc.temp2, self.qmc.flavors = [],[],[],[],[],[]

            #Read first line. STARTEND tag
            line = stream.readLine().trimmed()
            if not line.startsWith(u"[[MODE]]"):
                raise ValueError, u" Invalid Artisan file format: MODE tag missing"
            line = stream.readLine().trimmed()
            self.qmc.mode = unicode(line)        
            
            line = stream.readLine()
            if not line.startsWith(u"[[STARTEND]]"):
                raise ValueError, u" Invalid Artisan file format: STARTEND tag missing"

            #Read second line with the STARTEND values
            line = stream.readLine().trimmed()
            parts = line.split(u"    ")
            if parts.count() != 4:
                raise ValueError, u"invalid STARTEND values"
            else:
                for i in range(4):
                    self.qmc.startend.append(float(parts[i]))

            #Read third line. CRACKS tag
            line = stream.readLine().trimmed()                    
            if not line.startsWith(u"[[CRACKS]]"):
                raise ValueError, u" Invalid Artisan file format: CRACKS tag missing"

            #Read fourth line with CRACKS values
            line = stream.readLine().trimmed() 
            parts = line.split(u"    ")
            if parts.count() != 8:
                raise ValueError, u"invalid CRACK values"
            else:
                for i in range(8):
                    self.qmc.varC.append(float(parts[i]))

            #Read fith line. FLAVORS tag
            line = stream.readLine().trimmed()                    
            if not line.startsWith(u"[[FLAVORS]]"):
                raise ValueError, u" Invalid Artisan file format: FLAVORS tag missing"

            #Read six line with FLAVOR values
            line = stream.readLine().trimmed()
            parts = line.split(u"    ")
            if parts.count() != 10:
                raise ValueError, u"invalid FLAVOR values"
            else:
                for i in range(10):
                    self.qmc.flavors.append(float(parts[i]))
            #add 10th flavor to close the circle gap when drawing STAR graph
            self.qmc.flavors.append(self.qmc.flavors[0])
            
            #Read FLAVORS-LABEL tag
            line = stream.readLine().trimmed()
            if not line.startsWith(u"[[FLAVOR-LABELS]]"):
                raise ValueError, u"FLAVOR LABELS tag missing"
            #Read FLAVOR-LABEL values
            line = stream.readLine().trimmed()
            parts = line.split(u";;;")
            if parts.count() != 9:
                raise ValueError, u"Incorrect N flavors found"
            for i in range(9):
                self.qmc.flavorlabels[i] = unicode(parts[i])

            #read next line TITLE tag
            line = stream.readLine().trimmed()                   
            if not line.startsWith(u"[[TITLE]]"):
                raise ValueError, u" Invalid Artisan file format: TITLE tag missing"

            #Read next line beans type
            line = stream.readLine().trimmed()
            self.qmc.title = unicode(line)            

            #read next line BEANS tag
            line = stream.readLine().trimmed()                   
            if not line.startsWith(u"[[BEANS]]"):
                raise ValueError, u" Invalid Artisan file format: BEANS tag missing"

            #Read next line beans type
            line = stream.readLine().trimmed()
            self.qmc.beans = unicode(line)           

            #read next line WEIGHT tag
            line = stream.readLine().trimmed()
            if not line.startsWith(u"[[WEIGHT]]"):
                raise ValueError, u" Invalid Artisan file format: WEIGHT tag missing"

            #Read Weight
            line = stream.readLine().trimmed()
            parts = line.split(u"    ")
            if parts.count() != 3:
                raise ValueError, u"Weight needs three values"
            else:
                self.qmc.weight[0] = int(parts[0])
                self.qmc.weight[1] = int(parts[1])
                self.qmc.weight[2] = unicode(parts[2])
                
            #read next line ROASTER-TYPE tag
            line = stream.readLine().trimmed()                  
            if not line.startsWith(u"[[ROASTER-TYPE]]"):
                raise ValueError, u" Invalid Artisan file format: ROASTER-TYPE tag missing"

            #Read next line roaster type
            line = stream.readLine().trimmed()
            self.qmc.roastertype = unicode(line)
            
            #read next line OPERATOR tag
            line = stream.readLine().trimmed()                   
            if line.startsWith(u"[[OPERATOR]]"):
                #Read next line roaster type
                line = stream.readLine().trimmed()
                self.qmc.operator = unicode(line)
                line = stream.readLine().trimmed() 
                
            #Read date tag
            if not line.startsWith(u"[[DATE]]"):
                raise ValueError, u" Invalid Artisan file format: DATE tag missing"            
            #Read date
            line = stream.readLine().trimmed()
            self.qmc.roastdate = QDate.fromString(line)

            #Read event tag
            line = stream.readLine().trimmed()                   
            if not line.startsWith(u"[[EVENTS]]"):
                raise ValueError, u" Invalid Artisan file format: DATE tag missing"
            
            #Read events contents
            line = stream.readLine().trimmed()
            parts = line.split(u"    ")
            eventn = parts.count()              #number of events
            if unicode(parts[0]).isdigit():
                for i in range(eventn):
                    self.qmc.specialevents.append(int(parts[i]))
                #read events data
            line = stream.readLine().trimmed()
            if not line.startsWith(u"[[EVENTS-DATA]]"):
                raise ValueError, u" Invalid Artisan file format: DATA tag missing"
            if len(self.qmc.specialevents):
                for i in range(len(self.qmc.specialevents)):
                        self.qmc.specialeventsStrings[i] = unicode(stream.readLine().trimmed())               
            else:
                stream.readLine() #read blank line
            #Read roasting notes tag
            line = stream.readLine().trimmed()                   
            if not line.startsWith(u"[[ROASTING-NOTES]]"):
                raise ValueError, u" Invalid Artisan file format: ROASTING-NOTES tag missing"            

            #Read Roasting notes
            while not stream.atEnd():
                line = stream.readLine().trimmed()                   
                if line.startsWith(u"[[CUPPING-NOTES]]"):
                    break
                self.qmc.roastingnotes += unicode(line) + u"\n"

            #Read cuping notes
            while not stream.atEnd():
                line = stream.readLine().trimmed()                  
                if line.startsWith(u"[[DATA]]"):
                    break
                self.qmc.cuppingnotes += unicode(line) + u"\n"
                
            #Read DATA values till the end of the file
            while not stream.atEnd():
                line = stream.readLine().trimmed()
                parts = line.split(u"    ")
                if parts.count() != 3:
                    raise ValueError, u"invalid DATA values"
                else:
                    self.qmc.timex.append(float(parts[0]))
                    self.qmc.temp1.append(float(parts[1]))
                    self.qmc.temp2.append(float(parts[2]))

            #CLOSE FILE
            f.close()

            #select mode        
            if self.qmc.mode == u"F":
                self.qmc.fahrenheitMode()
            if self.qmc.mode == u"C":
                self.qmc.celsiusMode()

            #Set the xlimits
            if self.qmc.timex:
                self.qmc.endofx = self.qmc.timex[-1] + 40

            #change Title
            self.qmc.ax.set_title(self.qmc.title, size=20, color= self.qmc.palette["title"], fontweight='bold')
        
            #Plot everything
            self.qmc.redraw()

            message =  unicode(fname) + u" loaded successfully"
            self.messagelabel.setText(message)
            
            self.editgraph()

        except IOError,e:
            self.messagelabel.setText(u"error in fileload() " + unicode(e) + u" ")
            aw.qmc.errorlog.append(u"Unable to open file " + unicode(e))
            return

        except ValueError,e:
            self.messagelabel.setText(unicode(e))
            self.qmc.errorlog.append(u"value error in fileload() " + unicode(e))
            return
        
        finally:
            if f:
                f.close()


    # Loads background profile
    def loadbackground(self,fname):
        try:        
            f = QFile(fname)
            if not f.open(QIODevice.ReadOnly):
                raise IOError, unicode(f.errorString())
            stream = QTextStream(f)
            
            #variables to read on the text file are initialized as empty lists
            self.qmc.backgroundET,self.qmc.backgroundBT,self.qmc.timeB = [],[],[]
            self.qmc.startendB,self.qmc.varCB = [],[]
            
            #Read first line. STARTEND tag
            line = stream.readLine().trimmed()
            if not line.startsWith(u"[[MODE]]"):
                raise ValueError, u" Invalid Artisan file format: MODE tag missing"
            line = stream.readLine()       
            line = stream.readLine()
            if not line.startsWith(u"[[STARTEND]]"):
                raise ValueError, u" Invalid Artisan file format: STARTEND tag missing"
            #Read second line with the STARTEND values
            line = stream.readLine().trimmed()
            parts = line.split(u"    ")
            if parts.count() != 4:
                raise ValueError, u"invalid STARTEND values"
            else:
                for i in range(4):
                    self.qmc.startendB.append(float(parts[i]))
                    
            #Read third line. CRACKS tag
            line = stream.readLine().trimmed()                    
            if not line.startsWith(u"[[CRACKS]]"):
                raise ValueError, u" Invalid Artisan file format: CRACKS tag missing"
            #Read fourth line with CRACKS values
            line = stream.readLine().trimmed() 
            parts = line.split(u"    ")
            if parts.count() != 8:
                raise ValueError, u"invalid CRACK values"
            else:
                for i in range(8):
                    self.qmc.varCB.append(float(parts[i]))

            #Read fith line. FLAVORS tag
            line = stream.readLine().trimmed()                    
            if not line.startsWith(u"[[FLAVORS]]"):
                raise ValueError, u" Invalid Artisan file format: FLAVORS tag missing"
            #Read six line with FLAVOR values
            line = stream.readLine().trimmed() 
            #pass
            #Read FLAVORS-LABEL tag
            line = stream.readLine().trimmed()
            if not line.startsWith(u"[[FLAVOR-LABELS]]"):
                raise ValueError, u"FLAVOR LABELS tag missing"
            #Read FLAVOR-LABEL values
            line = stream.readLine().trimmed()
            #read next line TITLE tag
            line = stream.readLine().trimmed()                   
            if not line.startsWith(u"[[TITLE]]"):
                raise ValueError, u" Invalid Artisan file format: TITLE tag missing"
            #Read next line beans type
            line = stream.readLine()
            #read next line BEANS tag
            line = stream.readLine().trimmed()                  
            if not line.startsWith(u"[[BEANS]]"):
                raise ValueError, u" Invalid Artisan file format: BEANS tag missing"
            #Read next line beans type
            line = stream.readLine().trimmed()
            #read next line WEIGHT tag
            line = stream.readLine().trimmed()                  
            if not line.startsWith(u"[[WEIGHT]]"):
                raise ValueError, u" Invalid Artisan file format: WEIGHT tag missing"
            #Read next weight
            line = stream.readLine()
            #read next line ROASTER-TYPE tag
            line = stream.readLine().trimmed()                   
            if not line.startsWith(u"[[ROASTER-TYPE]]"):
                raise ValueError, u" Invalid Artisan file format: ROASTER-TYPE tag missing"
            #Read next line roaster type
            line = stream.readLine()
            #Read data tag
            line = stream.readLine().trimmed()                   
            if not line.startsWith(u"[[DATE]]"):
                raise ValueError, u" Invalid Artisan file format: DATE tag missing"            
            #Read date
            line = stream.readLine()
            #Read event tag
            line = stream.readLine().trimmed()                   
            if not line.startsWith(u"[[EVENTS]]"):
                raise ValueError, u" Invalid Artisan file format: DATE tag missing"            
            #Read events contents
            line = stream.readLine().trimmed()

            parts = line.split(u"    ")
            specialevents = parts.count()              #number of events

            #read events data
            line = stream.readLine().trimmed()
            if not line.startsWith(u"[[EVENTS-DATA]]"):
                raise ValueError, u" Invalid Artisan file format: DATA tag missing"
            
            if specialevents:
                for i in range(specialevents):
                    stream.readLine()                             
            else:
                stream.readLine() #read a blank line
                
            #Read roasting notes tag
            line = stream.readLine().trimmed()
            if not line.startsWith(u"[[ROASTING-NOTES]]"):
                raise ValueError, u" Invalid Artisan file format: ROASTING-NOTES tag missing"            
            #Read Roasting notes
            while not stream.atEnd():
                line = stream.readLine().trimmed()                   
                if line.startsWith(u"[[CUPPING-NOTES]]"):
                    break
            #Read cuping notes
            while not stream.atEnd():
                line = stream.readLine().trimmed()                   
                if line.startsWith(u"[[DATA]]"):
                    break
                
            #Read DATA values till the end of the file
            while not stream.atEnd():
                line = stream.readLine().trimmed()
                parts = line.split(u"    ")
                if parts.count() != 3:
                    raise ValueError, u"invalid DATA values"
                else:
                    self.qmc.timeB.append(float(parts[0]))
                    self.qmc.backgroundET.append(float(parts[1]))
                    self.qmc.backgroundBT.append(float(parts[2]))
            #CLOSE FILE
            f.close()

            message =  u"Background " + unicode(fname) + u" loaded successfully"
            self.messagelabel.setText(message)

        except IOError,e:
            self.messagelabel.setText(u"error in fileload() " + unicode(e) + u" ")
            aw.qmc.errorlog.append(u"Unable to open file " + unicode(e) )
            return

        except ValueError,e:
            self.messagelabel.setText(unicode(e))
            self.qmc.errorlog.append(u"value error in fileload() " + unicode(e))
            return
        
        finally:
            if f:
                f.close()

    #saves recorded profile in hard drive. Called from file menu 
    def fileSave(self):
        f = None
        try:         
            filename = unicode(QFileDialog.getSaveFileName(self,"Save Profile",self.profilepath,"*.txt"))
            if filename:
                if u".txt" not in filename:
                    filename += u".txt"
                f = open(filename, 'w')
                f.write(u"[[MODE]]\n")
                f.write(self.qmc.mode)
                f.write(u"\n[[STARTEND]]\n")
                for i in range(4):
                    f.write(unicode(self.qmc.startend[i]) + u"    ")       
                f.write(u"\n[[CRACKS]]\n")
                for i in range(8):
                    f.write(unicode(self.qmc.varC[i]) + u"    ")
                f.write(u"\n[[FLAVORS]]\n")
                for i in range(10):
                    f.write(unicode(self.qmc.flavors[i])+ u"    ")
                f.write(u"\n[[FLAVOR-LABELS]]\n")
                for i in range(8):
                    f.write(self.qmc.flavorlabels[i] + u";;;")
                f.write(self.qmc.flavorlabels[i+1])
                f.write(u"\n[[TITLE]]\n")
                f.write(self.qmc.title)
                f.write(u"\n[[BEANS]]\n")
                f.write(self.qmc.beans)
                f.write(u"\n[[WEIGHT]]\n")
                for i in range(3):
                    f.write(unicode(self.qmc.weight[i]))
                    f.write(u"    ")
                f.write(u"\n[[ROASTER-TYPE]]\n")
                f.write(self.qmc.roastertype)
                f.write(u"\n[[OPERATOR]]\n")
                f.write(self.qmc.operator)
                f.write(u"\n[[DATE]]\n")
                f.write(unicode(self.qmc.roastdate.toString()))            
                f.write(u"\n[[EVENTS]]\n")
                if len(self.qmc.specialevents):
                    for i in range(len(self.qmc.specialevents)):
                        f.write(unicode(self.qmc.specialevents[i]) + u"    ")
                else:
                    f.write(u"")
                f.write(u"\n[[EVENTS-DATA]]\n")
                if len(self.qmc.specialevents):
                    for i in range(len(self.qmc.specialevents)):
                        f.write(self.qmc.specialeventsStrings[i] + u"\n")
                else:
                    f.write(u"\n")
                f.write(u"[[ROASTING-NOTES]]\n")
                f.write(self.qmc.roastingnotes)
                f.write(u"\n[[CUPPING-NOTES]]\n")
                f.write(self.qmc.cuppingnotes)
                f.write(u"\n[[DATA]]\n")
                for i in range(len(self.qmc.timex)):
                    f.write( u"%.2f"%self.qmc.timex[i] + u"    " + u"%.1f"%self.qmc.temp1[i] + u"    " + u"%.1f"%self.qmc.temp2[i] + u"\n")

                f.close()
                self.messagelabel.setText(u"Profile saved to FILE:  " + filename)
            else:
                self.messagelabel.setText(u"Profile NOT saved")        

        except IOError,e:
            self.messagelabel.setText(u"Error in filesave() " + unicode(e) + u" ")
            aw.qmc.errorlog.append(u"Error in filesave() " + unicode(e))
            return
        finally:
            if f:
                f.close()


    #loads the settings at the start of application. See the oppposite closeEvent()
    def settingsLoad(self):
        try:
        
            settings = QSettings()
            #restore geometry
            self.restoreGeometry(settings.value("Geometry").toByteArray())     
            #restore mode
            self.qmc.mode = unicode(settings.value("Mode",self.qmc.mode).toString())
            if self.qmc.mode == u"F":
                self.qmc.fahrenheitMode()
            if self.qmc.mode == u"C":
                self.qmc.celsiusMode()
            #restore device
            settings.beginGroup("Device");
            self.qmc.device = settings.value("id",self.qmc.device).toInt()[0]
            if settings.contains("controlETpid"):
                self.ser.controlETpid = map(lambda x:x.toInt()[0],settings.value("controlETpid").toList())
            if settings.contains("readBTpid"):
                self.ser.readBTpid = map(lambda x:x.toInt()[0],settings.value("readBTpid").toList())
            settings.endGroup()
            #restore phases
            if settings.contains("Phases"):
                self.qmc.phases = map(lambda x:x.toInt()[0],settings.value("Phases").toList())
            #restore statistics
            if settings.contains("Statistics"):
                self.qmc.statisticsflags = map(lambda x:x.toInt()[0],settings.value("Statistics").toList())
            #restore delay
            self.qmc.delay = settings.value("Delay",int(self.qmc.delay)).toInt()[0]
            
            #restore colors
            for (k, v) in settings.value("Colors").toMap().items():
                self.qmc.palette[unicode(k)] = unicode(v.toString())
            #update colors
            self.qmc.redraw()
            
            #restore flavors
            self.qmc.flavorlabels = settings.value("Flavors",self.qmc.flavorlabels).toStringList()
            #restore serial port     
            settings.beginGroup("SerialPort");
            self.ser.comport = unicode(settings.value("comport",self.ser.comport).toString())
            self.ser.baudrate = settings.value("baudrate",int(self.ser.baudrate)).toInt()[0]
            self.ser.bytesize = settings.value("bytesize",self.ser.bytesize).toInt()[0]       
            self.ser.stopbits = settings.value("stopbits",self.ser.stopbits).toInt()[0]
            self.ser.parity = unicode(settings.value("parity",self.ser.parity).toString())
            self.ser.timeout = settings.value("timeout",self.ser.timeout).toInt()[0]
            settings.endGroup();

            #restore pid settings
            settings.beginGroup("PXR");
            for key in self.pid.PXR.keys():
                if type(self.pid.PXR[key][0]) == type(float()):
                    self.pid.PXR[key][0] = settings.value(key,self.pid.PXR[key]).toDouble()[0]
                elif type(self.pid.PXR[key][0]) == type(int()):
                    self.pid.PXR[key][0] = settings.value(key,self.pid.PXR[key]).toInt()[0]
            settings.endGroup()
            settings.beginGroup("PXG4");
            for key in self.pid.PXG4.keys():
                if type(self.pid.PXG4[key][0]) == type(float()):
                    self.pid.PXG4[key][0] = settings.value(key,self.pid.PXG4[key][0]).toDouble()[0]
                elif type(self.pid.PXG4[key][0]) == type(int()):
                    self.pid.PXG4[key][0] = settings.value(key,self.pid.PXG4[key][0]).toInt()[0]
            settings.endGroup()
            
            #need to update timer delay (otherwise it uses default 5 seconds)
            self.qmc.killTimer(self.qmc.timerid) 
            self.qmc.timerid = self.qmc.startTimer(self.qmc.delay)


        except Exception,e:
            print e
            self.qmc.errorlog.append(u"Error loading settings " + unicode(e))         
            return                            


    #Saves the settings when closing application. See the oppposite settingsLoad()
    def closeEvent(self, event):

        #save window geometry and position. See QSettings documentation.
        #This information is often stored in the system registry on Windows,
        #and in XML preferences files on Mac OS X. On Unix systems, in the absence of a standard,
        #many applications (including the KDE applications) use INI text files
        
        try:
            settings = QSettings()
            #save window geometry
            settings.setValue("Geometry",QVariant(self.saveGeometry()))
            #save mode
            settings.setValue("Mode",self.qmc.mode)
            #save device
            settings.beginGroup("Device");
            settings.setValue("id",self.qmc.device)
            settings.setValue("controlETpid",self.ser.controlETpid)
            settings.setValue("readBTpid",self.ser.readBTpid)
            settings.endGroup();
            #save phases
            settings.setValue("Phases",self.qmc.phases)
            #save statistics
            settings.setValue("Statistics",self.qmc.statisticsflags)
            #save delay
            settings.setValue("Delay",self.qmc.delay)
            #save colors
            settings.setValue("Colors",self.qmc.palette)
            #save flavors
            settings.setValue("Flavors",self.qmc.flavorlabels)
            #save serial port
            settings.beginGroup("SerialPort");
            settings.setValue("comport",self.ser.comport)
            settings.setValue("baudrate",self.ser.baudrate)
            settings.setValue("bytesize",self.ser.bytesize)
            settings.setValue("stopbits",self.ser.stopbits)
            settings.setValue("parity",self.ser.parity)
            settings.setValue("timeout",self.ser.timeout)            
            settings.endGroup();
            #save pid settings (only key and value[0])
            settings.beginGroup("PXR");
            for key in self.pid.PXR.keys():
                settings.setValue(key,self.pid.PXR[key][0])
            settings.endGroup()
            settings.beginGroup("PXG4");
            for key in self.pid.PXG4.keys():            
                settings.setValue(key,self.pid.PXG4[key][0])
            settings.endGroup()
            
        except Exception,e:
            self.qmc.errorlog.append("Error saving settings " + str(e))   
            

    def filePrint(self):

        tempFile = tempfile.TemporaryFile()
        aw.qmc.fig.savefig(tempFile.name)
        image = QImage(tempFile.name)
        
        if image.isNull():
            return

        if self.printer is None:
            self.printer = QPrinter(QPrinter.HighResolution)
            self.printer.setPageSize(QPrinter.Letter)

        if self.printer is None:
            self.printer = QPrinter(QPrinter.HighResolution)
            self.printer.setPageSize(QPrinter.Letter)
        form = QPrintDialog(self.printer, self)
        if form.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = image.size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(),size.height())

            painter.setWindow(image.rect()) #scale to fit page
            if isinstance(image, QPixmap):
                painter.drawPixmap(0,0,image)
            else:
                painter.drawImage(0, 0, image)

    def htmlReport(self):
        HTML_REPORT_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
       "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<title>Roasting Report</title>
<style type="text/css">
td { 
  vertical-align: top;
  padding: 0px 0px 0px 5px;
}
th {
  text-align: right;
  vertical-align: top;
}
</style>
</head>
<body>
<center>
<h1>$title</h1>

<table border="1" cellpadding="10">
<tr>
<td>
<center>
<table>
<tr>
<td>
<table width="220">
<tr>
<th>Date:</th>
<td>$datetime</td>
</tr>
<tr>
<th>Beans:</th>
<td>$beans</td>
</tr>
<tr>
<th>Weight:</th>
<td>$weight</td>
</tr>
<tr>
<th>Roaster:</th>
<td>$roaster</td>
</tr>
<tr>
<th>Operator:</th>
<td>$operator</td>
</tr>
</table>
</td>
<td>
<table width="180">
<tr>
<th>Charge:</th>
<td>$charge</td>
</tr>
<tr>
<th>TP:</th>
<td>$TP</td>
</tr>
<tr>
<th>FCs:</th>
<td>$FCs</td>
</tr>
<tr>
<th>FCe:</th>
<td>$FCe</td>
</tr>
<tr>
<th>SCs:</th>
<td>$SCs</td>
</tr>
<tr>
<th>SCe:</th>
<td>$SCe</td>
</tr>
<tr>
<th>Drop:</th>
<td>$drop</td>
</tr>
</table>
</td>
<td>
<table width="210">
<tr>
<th>Dry phase:</th>
<td>$dry_phase</td>
</tr>
<tr>
<th>Mid phase:</th>
<td>$mid_phase</td>
</tr>
<tr>
<th>Finish phase:</th>
<td>$finish_phase</td>
</tr>
</table>
</td>
</tr>
</table>
</center>
</td>
<td>
<center><b>Roasting Notes</b></center>
$roasting_notes
</td>
</tr>
<tr>
<td style="vertical-align:middle" align="center"><img alt='roast graph' src='$graph_image'/></td>
<td style="vertical-align:middle" align="center"><img alt='flavor graph' src='$flavor_image'/></td>
</tr>
<tr>
<td><center><b>Events</b></center><br/>
$specialevents
</td>
<td><center><b>Cupping Notes</b></center>
$cupping_notes
</td>
</tr>
</table>
</center>
</body>
</html>
        """
        beans = cgi.escape(self.qmc.beans)
        if len(beans) > 43:
            beans = beans[:41] + "&hellip;"
        TP_index = self.findTP()
        TP_time = TP_temp = None
        if TP_index >= 0:
            TP_time = aw.qmc.timex[TP_index]            
            TP_temp = aw.qmc.temp2[TP_index]
        dryEndIndex = self.findDryEnd(TP_index)
        rates_of_changes = aw.RoR(TP_index,dryEndIndex)
        evaluations = aw.defect_estimation()        
        #print graph
        self.qmc.redraw()        
        #resize GRAPH image to 600 pixels width
        tempFile = tempfile.TemporaryFile()
        aw.qmc.fig.savefig(tempFile.name)
        image = QImage(tempFile.name)
        image = image.scaledToWidth(600,1)
        #save GRAPH image
        graph_image = "artisan-graph.png"
        image.save(graph_image)
        #obtain flavor chart image
        self.qmc.flavorchart()
        #resize FLAVOR image to 400 pixels width
        tempFile = tempfile.TemporaryFile()
        aw.qmc.fig.savefig(tempFile.name)
        image = QImage(tempFile.name)
        image = image.scaledToWidth(500,1)
        #save GRAPH image
        flavor_image = "artisan-flavor.png"
        image.save(flavor_image)
        #return screen to GRAPH profile mode
        self.qmc.redraw()
        html = string.Template(HTML_REPORT_TEMPLATE).safe_substitute(
            title=cgi.escape(self.qmc.title),
            datetime=unicode(self.qmc.roastdate.toString()), #alt: unicode(self.qmc.roastdate.toString('MM.dd.yyyy')),
            beans=beans,
            weight=unicode(self.qmc.weight[0]) + self.qmc.weight[2] + " (" + "%.1f" % aw.weight_loss(self.qmc.weight[0],self.qmc.weight[1]) + "%)",
            roaster=cgi.escape(self.qmc.roastertype),
            operator=cgi.escape(self.qmc.operator),
            charge="BT " + "%.1f"%self.qmc.startend[1] + "&deg;" + self.qmc.mode  + "<br/>ET " + "%.1f"%self.ETfromseconds(self.qmc.startend[0]) + "&deg;" + self.qmc.mode,
            TP=self.event2html(TP_time,TP_temp),
            FCs=self.event2html(self.qmc.varC[0],self.qmc.varC[1]),
            FCe=self.event2html(self.qmc.varC[2],self.qmc.varC[3]),
            SCs=self.event2html(self.qmc.varC[4],self.qmc.varC[5]),
            SCe=self.event2html(self.qmc.varC[6],self.qmc.varC[7]),
            drop=self.event2html(self.qmc.startend[2],self.qmc.startend[3]),
            dry_phase=self.phase2html(self.qmc.statisticstimes[1],rates_of_changes[0],evaluations[0]),
            mid_phase=self.phase2html(self.qmc.statisticstimes[2],rates_of_changes[1],evaluations[1]),
            finish_phase=self.phase2html(self.qmc.statisticstimes[3],rates_of_changes[2],evaluations[2]),
            roasting_notes=self.note2html(self.qmc.roastingnotes),
            graph_image=graph_image,
            flavor_image=flavor_image,
            specialevents=self.specialevents2html(),
            cupping_notes=self.note2html(self.qmc.cuppingnotes))
        f = None
        try:      
            f = codecs.open("Artisanreport.html", 'w', encoding='utf-8')
            for i in range(len(html)):
                f.write(html[i])
            f.close()
            QDesktopServices.openUrl(QUrl("file:///" + QDir().current().absolutePath() + "/Artisanreport.html", QUrl.TolerantMode))            
        except IOError,e:
            self.messagelabel.setText("Error in htmlReport() " + str(e) + " ")
            aw.qmc.errorlog.append("Error in htmlReport() " + str(e))
            return
        finally:
            if f:
                f.close()  
                
    def phase2html(self,time,RoR,eval):
        if self.qmc.statisticstimes[0] > 0 and time and time > 0:
            return self.qmc.stringfromseconds(time) + " (%.2f" %(time*100./self.qmc.statisticstimes[0])+ "%)<br/>" + "%.1f deg/min"%RoR + "<br/>" + eval
        else:
            return "--"
            
    def event2html(self,time,temp):
        if time:
            return self.qmc.stringfromseconds(time - self.qmc.startend[0])+ " (%.1f"%temp + "&deg;" + self.qmc.mode + ")"
        else:
            return "--"
            
    def specialevents2html(self): 
        html = ""  
        if self.qmc.specialevents and len(self.qmc.specialevents) > 0:
            html += '<center>\n<table cellpadding="2">\n'
            for i in range(len(self.qmc.specialevents)):
                html += ("<tr>"+
                     "\n<td>" + unicode(i+1) + "</td><td>[" +
                     self.qmc.stringfromseconds(int(self.qmc.timex[self.qmc.specialevents[i]]-self.qmc.startend[0])) +
                     "</td><td>at " + "%.1f"%self.qmc.temp2[self.qmc.specialevents[i]] + self.qmc.mode +
                     "]</td><td>" + self.qmc.specialeventsStrings[i] +"</td></tr>\n")     
            html += '</table>\n</center>'
        return html
            
    def note2html(self,notes):
        notes_html = ""
        for i in range(len(notes)):
            #if notes[i] == " ":
            #    notes_html += " &nbsp "
            if ord(notes[i]) == 9:
                notes_html += " &nbsp&nbsp&nbsp&nbsp "                         
            elif notes[i] == "\n":
                notes_html += "<br/>\n"
            else:           
                notes_html += notes[i]
        return notes_html
    

    #finds closest Bean Temperature in aw.qmc.temp2 given an input time. timex and temp2 always have same dimension
    def BTfromseconds(self,seconds):
        if len(aw.qmc.timex):
            #find when input time crosses timex
            for i in range(len(aw.qmc.timex)):
                if aw.qmc.timex[i] > seconds:
                    break
            return float(aw.qmc.temp2[i-1])           #return the BT temperature
        else:
            return 0.0
            
    #finds closest Environmental Temperature in aw.qmc.temp1 given an input time. timex and temp1 always have same dimension
    def ETfromseconds(self,seconds):
        if len(aw.qmc.timex):
            #find when input time crosses timex
            for i in range(len(aw.qmc.timex)):
                if aw.qmc.timex[i] > seconds:
                    break
            return float(aw.qmc.temp1[i-1])           #return the ET temperature
        else:
            return 0.0
        
    # converts times (values of timex) to indices in aw.qmc.temp1 and aw.qmc.temp2
    def time2index(self,time):
        for i in range(len(aw.qmc.timex)):
            if aw.qmc.timex[i] == time:
                return i
        return -1
        
    #returns the index of the lowest point in BT; return -1 if no such value found
    def findTP(self):
        end = len(aw.qmc.temp2) - 1
        # try to consider only indices until the roast end and not beyond
        if aw.qmc.startend[2] > 0.:
            end = self.time2index(aw.qmc.startend[2])
        if end > 0:
            TP = aw.qmc.temp2[0]
            idx = -1
            for i in range(end, 0, -1):
                if aw.qmc.temp2[i] < TP:
                    TP = aw.qmc.temp2[i]
                    idx = i
            return idx
        else:
            return -1
    
    #Flavor defect estimation chart for each leg. Thanks to Jim Schulman 
    def defect_estimation(self):    
        dryphasetime = aw.qmc.statisticstimes[1]
        midphasetime = aw.qmc.statisticstimes[2]
        finishphasetime = aw.qmc.statisticstimes[3]
        ShortDryingPhase = "Grassy"
        LongDryingPhase = "Leathery"
        ShortTo1CPhase = "Toasty"
        LongTo1CPhase = "Bready"
        ShortFinishPhase = "Acidic"
        LongFinishPhase = "Flat"        
        st1 = st2 = st3 = 'OK'
        #CHECK CONDITIONS                
        #if dry phase time < 3 mins (180 seconds) or less than 26% of the total time
        if dryphasetime < aw.qmc.statisticsconditions[0]:
            st1 = ShortDryingPhase
        #if dry phase time > 6 mins or more than 40% of the total time
        elif dryphasetime > aw.qmc.statisticsconditions[1]:
            st1 = LongDryingPhase

        #if mid phase time < 5 minutes
        if midphasetime < aw.qmc.statisticsconditions[2]:
            st2 = ShortTo1CPhase
        #if mid phase time > 10 minutes
        elif midphasetime > aw.qmc.statisticsconditions[3]:
            st2 = LongTo1CPhase

        #if finish phase is less than 3 mins
        if finishphasetime < aw.qmc.statisticsconditions[4]:
            st3 = ShortFinishPhase
        #if finish phase is over 6 minutes
        elif finishphasetime > aw.qmc.statisticsconditions[5]:
            st3 = LongFinishPhase
        return (st1,st2,st3)
    
    #returns the index of the end of the dry phase (returns -1 if dry end cannot be determined)
    #if given, starts at TP_index and looks forward, otherwise it looks backwards from end of roast (EoR)
    def findDryEnd(self,TP_index=None):
        idx = -1
        end = len(aw.qmc.temp2)
        # try to consider only indices until the roast end and not beyond
        if aw.qmc.startend[2] > 0.:
            end = self.time2index(aw.qmc.startend[2])            
        TP = TP_index
        # if TP not yet computed, let's try to compute it
        if not TP:
            TP = self.findTP()
            if TP < 0:
                TP = None
        if TP:
          for i in range(TP,end):
              #count from TP forward (low temps towards high temps)
              if aw.qmc.temp2[i] > aw.qmc.phases[1]:
                  idx = i
                  break
          return idx                
        else:
          for i in range(end):
              #count from the back [-i] (high temps towards low temps)
              if aw.qmc.temp2[-i] < aw.qmc.phases[1] and i > 0:
                  idx = i
                  break
          if idx < 0:
              return idx
          else:
              return len(aw.qmc.temp2) - idx
        
    #Find rate of change of each phase. TP_index (by aw.findTP()) is the index of the TP and dryEndIndex that of the end of drying (by aw.findDryEnd())
    def RoR(self,TP_index,dryEndIndex):
        dryphasetime = aw.qmc.statisticstimes[1]
        midphasetime = aw.qmc.statisticstimes[2]
        finishphasetime = aw.qmc.statisticstimes[3]
        BTdrycross = None
        rc1 = rc2 = rc3 = 0.
        if dryEndIndex > -1 and dryEndIndex < len(aw.qmc.temp2):
            BTdrycross = aw.qmc.temp2[dryEndIndex]
        if BTdrycross and TP_index < 1000 and TP_index > -1 and dryphasetime and TP_index < len(aw.qmc.temp2):
            LP = aw.qmc.temp2[TP_index]
            rc1 = ((BTdrycross - LP) / (dryphasetime - aw.qmc.timex[TP_index]))*60.
        if aw.qmc.varC[0]:
            if midphasetime and BTdrycross:
                rc2 = ((aw.qmc.varC[1] - BTdrycross)/midphasetime)*60.
            if finishphasetime:
                rc3 = ((aw.qmc.startend[3] - aw.qmc.varC[1])/finishphasetime)*60.
        return (rc1,rc2,rc3)    
        
    def viewErrorLog(self):
        error = errorDlg(self)
        error.show()

    def hudshow(self):
        hud = HUDDlg(self)
        hud.show()        
        
    def helpAbout(self):
        creditsto = "<br>Rafael Cobo <br> Marko Luther"
        box = QMessageBox()
        #create a html QString
        box.about(self,
                "Platform",
                """<b>Version:</b> {0} 
                <p>
                <b>Python:</b> [ {1} ]
                <b>Qt:</b> [ {2} ]
                <b>PyQt:</b> [ {3} ]
                <b>OS:</b/>[ {4} ]
                </p>
                <p>
                <b>Credits:</b> {5}
                </p>""".format(
                __version__,
                platform.python_version(),
                QT_VERSION_STR,
                PYQT_VERSION_STR,
                platf,
                creditsto))

    def helpHelp(self):
        QDesktopServices.openUrl(QUrl("file:///" + self.applicationDirectory + "/index.html", QUrl.TolerantMode))

    def calibratedelay(self):
        calSpinBox = QSpinBox()
        calSpinBox.setRange(1,30)
        calSpinBox.setValue(self.qmc.delay/1000)
        secondsdelay, ok = QInputDialog.getInteger(self,
                "Sampling period", "Enter seconds:",
                calSpinBox.value(),1,30)
        if ok:
            self.qmc.killTimer(self.qmc.timerid) 
            self.qmc.delay = secondsdelay*1000
            self.qmc.timerid = self.qmc.startTimer(self.qmc.delay)

    def setcommport(self):
        dialog = comportDlg(self)
        if dialog.exec_():
            self.ser.comport = unicode(dialog.comportEdit.currentText())                #str changes QString to a python string
            self.ser.baudrate = int(dialog.baudrateComboBox.currentText())          #int changes QString to int
            self.ser.bytesize = int(dialog.bytesizeComboBox.currentText())
            self.ser.stopbits = int(dialog.stopbitsComboBox.currentText())
            self.ser.parity = unicode(dialog.parityComboBox.currentText())
            self.ser.timeout = int(dialog.timeoutEdit.text())


    def PIDcontrol(self):
        if self.ser.controlETpid[0] == 0:
            dialog = PXG4pidDlgControl(self)
        elif self.ser.controlETpid[0] == 1:
            dialog = PXRpidDlgControl(self)
        #modeless style dialog 
        dialog.show()


    def deviceassigment(self):
        dialog = DeviceAssignmentDLG(self)
        dialog.show()        

    def showstatistics(self):
        dialog = StatisticsDLG(self)
        dialog.show()

    def calculator(self):
        dialog = calculatorDlg(self)
        dialog.show()

    def background(self):
        dialog = backgroundDLG(self)
        dialog.show()       

    def flavorchart(self):
        dialog = flavorDlg(self)
        dialog.show()
        
    def editgraph(self):
        dialog = editGraphDlg(self)
        dialog.show()

    def editphases(self):
        dialog = phasesGraphDlg(self)
        dialog.show()
        
    # takes the weight of the green and roasted coffee as floats and
    # returns the weight loos in percentage as float
    def weight_loss(self,green,roasted):
      if float(green) == 0.0 or float(green) < float(roasted):
        return 0.
      else:
        return 100. * ((float(green) - float(roasted)) / float(green))

    def importHH506RA(self):
        try:
            fname = u""
            fname = QFileDialog.getOpenFileName(self,u"Load Profile for a HH506RA")
            if  fname == "":
                return
            self.qmc.reset()
            f = QFile(fname)
            if not f.open(QIODevice.ReadOnly):
                raise IOError, unicode(f.errorString())
                return
            stream = QTextStream(f)

            #variables to read on the text file are initialized as empty lists
            self.qmc.timex, self.qmc.temp1, self.qmc.temp2 = [],[],[]

            #Read first line
            lino = 0
            line = stream.readLine().trimmed()
            regex = QRegExp(r"\s")
            parts = line.split(regex)
            if parts.count() != 3:
                raise ValueError, u"invalid header values"
            else:
                self.qmc.title = unicode(parts[0])
            line = stream.readLine().trimmed()
            line = stream.readLine().trimmed()

            parts = line.split(regex, QString.SkipEmptyParts)
            if parts[2] == u"F":
                self.qmc.fahrenheitMode()
            if parts[2] == u"C":
                self.qmc.celsiusMode()

            value = float(self.qmc.stringtoseconds(str(parts[8])))
            zero = value - self.qmc.startend[0]

            self.qmc.timex.append(float(self.qmc.stringtoseconds(str(parts[8]))-zero))
            self.qmc.temp1.append(float(parts[1])- self.qmc.startend[0])
            self.qmc.temp2.append(float(parts[4])- self.qmc.startend[0])

            #Read DATA values till the end of the file
            while not stream.atEnd():
                line = stream.readLine().trimmed()                   
                parts = line.split(regex, QString.SkipEmptyParts)
                if parts.count() != 9:
                    raise ValueError, u"invalid data values"
                newtime = float(self.qmc.stringtoseconds(unicode(parts[8])))-zero
                self.qmc.timex.append(newtime)
                self.qmc.temp1.append(float(parts[1]))
                self.qmc.temp2.append(float(parts[4]))
            
            f.close()
            if (reduce (lambda x,y:x + y, self.qmc.temp2)) > reduce (lambda x,y:x + y, self.qmc.temp1):
                tmp = self.qmc.temp1
                self.qmc.temp1 = self.qmc.temp2
                self.qmc.temp2 = tmp
            self.qmc.endofx = self.qmc.timex[-1]
            self.messagelabel.setText(u"HH506RA file loaded successfully")
            self.qmc.redraw()

        except IOError,e:
            self.messagelabel.setText(unicode(e))
            self.qmc.errorlog.append(u"file error in importHH506RA(): " + unicode(e))
            return            

        except ValueError,e:
            self.messagelabel.setText(unicode(e))
            self.qmc.errorlog.append(u"value error in importHH506RA(): " + unicode(e))
            return


    #checks or creates directory structure
    def dirstruct(self):
        currentdir = QDir().current()     #selects the current dir
        if not currentdir.exists(u"profiles"):
            profilesdir = currentdir.mkdir(u"profiles")

        #check/create 'other' directory inside profiles/
        otherpath = QString(u"profiles/other")
        if not currentdir.exists(otherpath):
            yeardir = currentdir.mkdir(otherpath)
            
        #find current year,month
        date =  QDate.currentDate()       
        
        #check / create year dir 
        yearpath = QString(u"profiles/" + unicode(date.year()))
        if not currentdir.exists(yearpath):
            yeardir = currentdir.mkdir(yearpath)

        #check /create month dir to store profiles
        monthpath = QString(u"profiles/" + unicode(date.year()) + u"/" + unicode(date.month()))
        if not currentdir.exists(monthpath):
            monthdir = currentdir.mkdir(monthpath)
        self.profilepath = monthpath

    #resizes and saves graph to a new width x 
    def resize(self,w,transformationmode):
        try: 
            tempFile = tempfile.TemporaryFile()
            aw.qmc.fig.savefig(tempFile.name)
            image = QImage(tempFile.name)

            if w != 0:        
                image = image.scaledToWidth(w,transformationmode)
        
            filename = unicode(QFileDialog.getSaveFileName(self,"Save Image for web","","*.png"))
            if filename:
                if u".png" not in filename:
                    filename += u".png"
                    
            image.save(filename)
            
            x = image.width()
            y = image.height()
            
            self.messagelabel.setText(filename + u" (" + unicode(x) + u"x" + unicode(y) + u") saved")

        except IOError,e:
            self.messagelabel.setText(u"Error in resize() " + unicode(e) + u" ")
            aw.qmc.errorlog.append(u"Error in resize() " + unicode(e))
            return
                                        
########################################################################################            
#####################  ROAST PROPERTIES EDIT GRAPH DLG  ################################
########################################################################################        
        
class editGraphDlg(QDialog):
    def __init__(self, parent = None):
        super(editGraphDlg,self).__init__(parent)

        self.setWindowTitle(u"Roast properties")

        regextime = QRegExp(r"^[0-9]{1,2}:[0-9]{1,2}$")
        regexweight = QRegExp(r"^[0-9]{1,3}[.0-9]{1,2}$")

        #MARKERS
        chargelabel  = QLabel("<b>CHARGE</b>")
        chargelabel.setStyleSheet("background-color:'#f07800';")
        self.chargeedit = QLineEdit(aw.qmc.stringfromseconds(int(aw.qmc.startend[0])))
        self.chargeedit.setValidator(QRegExpValidator(regextime,self))
        self.chargeedit.setMaximumWidth(50)
        chargelabel.setBuddy(self.chargeedit)
        
        Cstartlabel = QLabel("<b>1C START</b>")
        Cstartlabel.setStyleSheet("background-color:'orange';")
        self.Cstartedit = QLineEdit(aw.qmc.stringfromseconds(int(aw.qmc.varC[0])))
        self.Cstartedit.setValidator(QRegExpValidator(regextime,self))
        self.Cstartedit.setMaximumWidth(50)
        Cstartlabel.setBuddy(self.Cstartedit)
        
        Cendlabel = QLabel("<b>1C END</b>")
        Cendlabel.setStyleSheet("background-color:'orange';")
        self.Cendedit = QLineEdit(aw.qmc.stringfromseconds(int(aw.qmc.varC[2])))
        self.Cendedit.setValidator(QRegExpValidator(regextime,self))
        self.Cendedit.setMaximumWidth(50)
        Cendlabel.setBuddy(self.Cendedit)
   
        CCstartlabel = QLabel("<b>2C START</b>")
        CCstartlabel.setStyleSheet("background-color:'orange';")
        self.CCstartedit = QLineEdit(aw.qmc.stringfromseconds(int(aw.qmc.varC[4])))
        self.CCstartedit.setValidator(QRegExpValidator(regextime,self))
        self.CCstartedit.setMaximumWidth(50)
        CCstartlabel.setBuddy(self.CCstartedit)

        CCendlabel = QLabel("<b>2C END</b>")
        CCendlabel.setStyleSheet("background-color:'orange';")
        self.CCendedit = QLineEdit(aw.qmc.stringfromseconds(int(aw.qmc.varC[6])))
        self.CCendedit.setValidator(QRegExpValidator(regextime,self))
        self.CCendedit.setMaximumWidth(50)
        CCendlabel.setBuddy(self.CCendedit)
        
        droplabel = QLabel("<b>DROP</b>")
        droplabel.setStyleSheet("background-color:'#f07800';")
        self.dropedit = QLineEdit(aw.qmc.stringfromseconds(int(aw.qmc.startend[2])))
        self.dropedit.setValidator(QRegExpValidator(regextime,self))
        self.dropedit.setMaximumWidth(50)
        droplabel.setBuddy(self.dropedit)
        
        # EVENTS 
        ntlines = len(aw.qmc.specialevents)         #number of events found
        nslines = len(aw.qmc.specialeventsStrings)  #number of descriptions for each event

        msg1label = QLabel("Times are from begining of data (absolute)")
        msg1label.setAlignment(Qt.AlignLeft)

        #Dynamic content of events depending on number of events found    
        if ntlines > 0 and nslines > 0:
            time1 = aw.qmc.stringfromseconds(int(aw.qmc.timex[int(aw.qmc.specialevents[0])]))
            self.line1b = QLineEdit(time1)
            self.line1b.setValidator(QRegExpValidator(regextime,self))
            self.line1b.setMaximumWidth(50)
            self.line1 = QLineEdit(aw.qmc.specialeventsStrings[0])
        if ntlines > 1 and nslines > 1:
            time2 = aw.qmc.stringfromseconds(int(aw.qmc.timex[int(aw.qmc.specialevents[1])]))
            self.line2b = QLineEdit(time2)
            self.line2b.setValidator(QRegExpValidator(regextime,self))
            self.line2b.setMaximumWidth(50)
            self.line2 = QLineEdit(aw.qmc.specialeventsStrings[1])
        if ntlines > 2 and nslines > 2:
            time3 = aw.qmc.stringfromseconds(int(aw.qmc.timex[int(aw.qmc.specialevents[2])]))
            self.line3b = QLineEdit(time3)
            self.line3b.setValidator(QRegExpValidator(regextime,self))
            self.line3b.setMaximumWidth(50)
            self.line3 = QLineEdit(aw.qmc.specialeventsStrings[2])
        if ntlines > 3 and nslines > 3:
            time4 = aw.qmc.stringfromseconds(int(aw.qmc.timex[int(aw.qmc.specialevents[3])]))
            self.line4b = QLineEdit(time4)
            self.line4b.setValidator(QRegExpValidator(regextime,self))
            self.line4b.setMaximumWidth(50)
            self.line4 = QLineEdit(aw.qmc.specialeventsStrings[3])
        if ntlines > 4 and nslines > 4:
            time5 = aw.qmc.stringfromseconds(int(aw.qmc.timex[int(aw.qmc.specialevents[4])]))
            self.line5b = QLineEdit(time5)
            self.line5b.setValidator(QRegExpValidator(regextime,self))
            self.line5b.setMaximumWidth(50)
            self.line5 = QLineEdit(aw.qmc.specialeventsStrings[4])
        if ntlines > 5 and nslines > 5:
            time6 = aw.qmc.stringfromseconds(int(aw.qmc.timex[int(aw.qmc.specialevents[5])]))
            self.line6b = QLineEdit(time6)
            self.line6b.setValidator(QRegExpValidator(regextime,self))
            self.line6b.setMaximumWidth(50)
            self.line6 = QLineEdit(time6 + u" " + aw.qmc.specialeventsStrings[5])
        if ntlines > 6 and nslines > 6:
            time7 = aw.qmc.stringfromseconds(int(aw.qmc.timex[int(aw.qmc.specialevents[6])]))
            self.line7b = QLineEdit(time7)
            self.line7b.setValidator(QRegExpValidator(regextime,self))
            self.line7b.setMaximumWidth(50)
            self.line7 = QLineEdit(time6 + u" " + aw.qmc.specialeventsStrings[6])
        if ntlines > 7 and nslines > 7:
            time8 = aw.qmc.stringfromseconds(int(aw.qmc.timex[int(aw.qmc.specialevents[7])]))
            self.line8b = QLineEdit(time8)
            self.line8b.setValidator(QRegExpValidator(regextime,self))
            self.line8b.setMaximumWidth(50)
            self.line8 = QLineEdit(time8 + u" " + aw.qmc.specialeventsStrings[7])
        if ntlines > 8 and nslines > 8:
            time9 = aw.qmc.stringfromseconds(int(aw.qmc.timex[int(aw.qmc.specialevents[8])]))
            self.line9b = QLineEdit(time9)
            self.line9b.setValidator(QRegExpValidator(regextime,self))
            self.line9b.setMaximumWidth(50)
            self.line9 = QLineEdit(time9 + u" " + aw.qmc.specialeventsStrings[8])
        if ntlines > 9 and nslines > 9:
            time10 = aw.qmc.stringfromseconds(int(aw.qmc.timex[int(aw.qmc.specialevents[9])]))
            self.line10b = QLineEdit(time10)
            self.line10b.setValidator(QRegExpValidator(regextime,self))
            self.line10b.setMaximumWidth(50)
            self.line10 = QLineEdit(time10 + u" " + aw.qmc.specialeventsStrings[9])

        numberlabel1 = QLabel("Event 1")
        numberlabel2 = QLabel("Event 2")
        numberlabel3 = QLabel("Event 3")
        numberlabel4 = QLabel("Event 4")
        numberlabel5 = QLabel("Event 5")
        numberlabel6 = QLabel("Event 6")
        numberlabel7 = QLabel("Event 7")
        numberlabel8 = QLabel("Event 8")
        numberlabel9 = QLabel("Event 9")
        numberlabel10 = QLabel("Event 10")
        numberlabel1.setStyleSheet("background-color:'yellow';")
        numberlabel2.setStyleSheet("background-color:'yellow';")
        numberlabel3.setStyleSheet("background-color:'yellow';")
        numberlabel4.setStyleSheet("background-color:'yellow';")
        numberlabel5.setStyleSheet("background-color:'yellow';")
        numberlabel6.setStyleSheet("background-color:'yellow';")
        numberlabel7.setStyleSheet("background-color:'yellow';")
        numberlabel8.setStyleSheet("background-color:'yellow';")
        numberlabel9.setStyleSheet("background-color:'yellow';")
        numberlabel10.setStyleSheet("background-color:'yellow';")
        
        eventsLayout = QGridLayout()
        eventsLayout.addWidget(msg1label,0,1)

        if ntlines:
            eventsLayout.addWidget(numberlabel1,1,0)
            eventsLayout.addWidget(self.line1b,1,1)
            eventsLayout.addWidget(self.line1,1,2)
        if ntlines > 1:
            eventsLayout.addWidget(numberlabel2,2,0)
            eventsLayout.addWidget(self.line2b,2,1)
            eventsLayout.addWidget(self.line2,2,2)
        if ntlines > 2:
            eventsLayout.addWidget(numberlabel3,3,0)
            eventsLayout.addWidget(self.line3b,3,1)
            eventsLayout.addWidget(self.line3,3,2)
        if ntlines >3:
            eventsLayout.addWidget(numberlabel4,4,0)
            eventsLayout.addWidget(self.line4b,4,1)
            eventsLayout.addWidget(self.line4,4,2)
        if ntlines >4:
            eventsLayout.addWidget(numberlabel5,5,0)
            eventsLayout.addWidget(self.line5b,5,1)
            eventsLayout.addWidget(self.line5,5,2)
        if ntlines >5:
            eventsLayout.addWidget(numberlabel6,6,0)
            eventsLayout.addWidget(self.line6b,6,1)
            eventsLayout.addWidget(self.line6,6,2)
        if ntlines >6:
            eventsLayout.addWidget(numberlabel7,7,0)
            eventsLayout.addWidget(self.line7b,7,1)
            eventsLayout.addWidget(self.line7,7,2)
        if ntlines >7:
            eventsLayout.addWidget(numberlabel8,8,0)
            eventsLayout.addWidget(self.line8b,8,1)
            eventsLayout.addWidget(self.line8,8,2)
        if ntlines >8:
            eventsLayout.addWidget(numberlabel9,9,0)
            eventsLayout.addWidget(self.line9b,9,1)
            eventsLayout.addWidget(self.line9,9,2)
        if ntlines >9:
            eventsLayout.addWidget(numberlabel10,10,0)
            eventsLayout.addWidget(self.line10b,10,1)
            eventsLayout.addWidget(self.line10,10,2)

        
        neweventButton = QPushButton("New")
        neweventButton.setFocusPolicy(Qt.NoFocus)
        neweventButton.setMaximumSize(70, 30)
        self.connect(neweventButton,SIGNAL("clicked()"),self.addevent)

        deleventButton = QPushButton("Delete")
        deleventButton.setFocusPolicy(Qt.NoFocus)
        deleventButton.setMaximumSize(70, 30)
        self.connect(deleventButton,SIGNAL("clicked()"),self.delevent)
        
        if len(aw.qmc.timex) < 1:
            deleventButton.setDisabled(True)
            neweventButton.setDisabled(True)
            
        #TITLE
        titlelabel = QLabel("<b>Title</b>")
        self.titleedit = QLineEdit(aw.qmc.title)
        #Date
        datelabel1 = QLabel("<b>Date</b>")
        date = aw.qmc.roastdate.toString()
        dateedit = QLineEdit(date)
        dateedit.setReadOnly(True)
        dateedit.setStyleSheet("background-color:'lightgrey'")

        #Beans
        beanslabel = QLabel("<b>Beans</b>")
        self.beansedit = QLineEdit(aw.qmc.beans)

        #roaster
        self.roaster = QLineEdit(aw.qmc.roastertype)

        #operator
        self.operator = QLineEdit(aw.qmc.operator)
        
        #weight
        weightlabel = QLabel("<b>Weight</b> ")
        weightinlabel = QLabel(" in")
        weightoutlabel = QLabel(" out")
        inw = str(aw.qmc.weight[0])
        outw = str(aw.qmc.weight[1])
        self.weightinedit = QLineEdit(inw)
        
        #self.weightinedit.setValidator(QDoubleValidator(0., 9999., 1, self.weightinedit))
        self.weightinedit.setMinimumWidth(50)
        self.weightinedit.setMaximumWidth(50)
        self.weightoutedit = QLineEdit(outw)
        #self.weightoutedit.setValidator(QDoubleValidator(0., 9999., 1, self.weightoutedit))
        self.weightoutedit.setMinimumWidth(50)
        self.weightoutedit.setMaximumWidth(50)
        self.weightpercentlabel = QLabel(" %")
        self.weightpercentlabel.setMinimumWidth(45)
        self.weightpercentlabel.setMaximumWidth(45)

        self.percent()
        self.connect(self.weightoutedit,SIGNAL("editingFinished()"),self.percent)
        self.connect(self.weightinedit,SIGNAL("editingFinished()"),self.percent)


        self.unitsComboBox = QComboBox()
        self.unitsComboBox.setMaximumWidth(60)
        self.unitsComboBox.setMinimumWidth(55)
        self.unitsComboBox.addItems(["g","Kg"])


        # NOTES
        roastertypelabel = QLabel()
        roastertypelabel.setText("<b>Roaster<\b>")

        operatorlabel = QLabel()
        operatorlabel.setText("<b>Operator<\b>")

        roastinglabel = QLabel("<b>Roasting Notes<\b>")
        self.roastingeditor = QTextEdit()
        self.roastingeditor.setPlainText(QString(aw.qmc.roastingnotes))

        cupinglabel = QLabel("<b>Cuping Notes<\b>")
        self.cupingeditor =  QTextEdit()
        self.cupingeditor.setPlainText(QString(aw.qmc.cuppingnotes))
        

        # Save button
        saveButton = QPushButton("Update")
        saveButton.setFocusPolicy(Qt.NoFocus)
        self.connect(saveButton, SIGNAL("clicked()"),self, SLOT("accept()"))
        saveButton.setMaximumSize(70, 30)
        if len(aw.qmc.timex) < 1:
            saveButton.setDisabled(True)
        
        #Cancel Button
        cancelButton = QPushButton("Cancel")
        cancelButton.setFocusPolicy(Qt.NoFocus)
        self.connect(cancelButton, SIGNAL("clicked()"),self, SLOT("reject()"))
        cancelButton.setMaximumSize(70, 30)

        ##### LAYOUTS

        timeLayout = QGridLayout()
        timeLayout.addWidget(chargelabel,0,0)
        timeLayout.addWidget(Cstartlabel,0,1)
        timeLayout.addWidget(Cendlabel,0,2)
        timeLayout.addWidget(CCstartlabel,0,3)
        timeLayout.addWidget(CCendlabel,0,4)
        timeLayout.addWidget(droplabel,0,5)
        timeLayout.addWidget(self.chargeedit,1,0)
        timeLayout.addWidget(self.Cstartedit,1,1)
        timeLayout.addWidget(self.Cendedit,1,2)
        timeLayout.addWidget(self.CCstartedit,1,3)
        timeLayout.addWidget(self.CCendedit,1,4)
        timeLayout.addWidget(self.dropedit,1,5)

        eventbuttonLayout = QHBoxLayout()
        eventbuttonLayout.addWidget(neweventButton,0)
        eventbuttonLayout.addWidget(deleventButton,1)
        
        textLayout = QGridLayout()
        textLayout.addWidget(datelabel1,0,0)
        textLayout.addWidget(dateedit,0,1)
        textLayout.addWidget(titlelabel,1,0)
        textLayout.addWidget(self.titleedit,1,1)
        textLayout.addWidget(beanslabel,2,0)
        textLayout.addWidget(self.beansedit,2,1)
        textLayout.addWidget(roastertypelabel,3,0)
        textLayout.addWidget(self.roaster,3,1)
        textLayout.addWidget(operatorlabel,4,0)
        textLayout.addWidget(self.operator,4,1)

        weightLayout = QHBoxLayout()
        weightLayout.setSpacing(0)

        weightLayout.addWidget(weightlabel,0)
        weightLayout.addSpacing(10)
        weightLayout.addWidget(self.unitsComboBox,1)
        weightLayout.addSpacing(40)
        weightLayout.addWidget(self.weightinedit,2)
        weightLayout.addWidget(weightinlabel,3)
        weightLayout.addSpacing(10)
        weightLayout.addWidget(self.weightoutedit,4)
        weightLayout.addWidget(weightoutlabel,5)
        weightLayout.addSpacing(10)
        weightLayout.addWidget(self.weightpercentlabel,6)
        
        anotationLayout = QVBoxLayout()
        anotationLayout.addWidget(roastinglabel,0)
        anotationLayout.addWidget(self.roastingeditor,1)
        anotationLayout.addWidget(cupinglabel,2)
        anotationLayout.addWidget(self.cupingeditor,3)

        okLayout = QHBoxLayout()
        okLayout.addWidget(cancelButton,0)
        okLayout.addWidget(saveButton,1)

        totalLayout = QVBoxLayout()
        totalLayout.addLayout(timeLayout,0)
        totalLayout.addLayout(eventsLayout,1)
        totalLayout.addLayout(eventbuttonLayout,2)
        totalLayout.addLayout(textLayout,3)
        totalLayout.addLayout(weightLayout,4)
        totalLayout.addLayout(anotationLayout,5)
        totalLayout.addLayout(okLayout,6)

        self.setLayout(totalLayout)
        
    def percent(self):
        if float(self.weightoutedit.text()) != 0.0:
            percent = aw.weight_loss(float(self.weightinedit.text()),float(self.weightoutedit.text()))
        else:
            percent = 0.
        percentstring =  "%.1f" %(percent) + "%"
        self.weightpercentlabel.setText(QString(percentstring))    #weight percent loss
        
                
    def accept(self):
        #check for graph
        if len(aw.qmc.timex):   
            # update graph time variables
            #varC = 1C start time [0],1C start Temp [1],1C end time [2],1C end temp [3],2C start time [4], 2C start Temp [5],2C end time [6], 2C end temp [7]
            #startend = [starttime [0], starttempBT [1], endtime [2],endtempBT [3]]
            aw.qmc.startend[0] = self.choice(aw.qmc.stringtoseconds(unicode(self.chargeedit.text())))   #CHARGE   time
            aw.qmc.varC[0] = self.choice(aw.qmc.stringtoseconds(unicode(self.Cstartedit.text())))       #1C START time
            aw.qmc.varC[2] = self.choice(aw.qmc.stringtoseconds(unicode(self.Cendedit.text())))         #1C END   time
            aw.qmc.varC[4] = self.choice(aw.qmc.stringtoseconds(unicode(self.CCstartedit.text())))      #2C START time
            aw.qmc.varC[6] = self.choice(aw.qmc.stringtoseconds(unicode(self.CCendedit.text())))        #2C END   time
            aw.qmc.startend[2] = self.choice(aw.qmc.stringtoseconds(unicode(self.dropedit.text())))     #DROP     time
            #find corresponding temperatures
            aw.qmc.startend[1] = aw.BTfromseconds(aw.qmc.startend[0])                             #CHARGE   temperature
            aw.qmc.varC[1] = aw.BTfromseconds(aw.qmc.varC[0])                                     #1C START temperature
            aw.qmc.varC[3] = aw.BTfromseconds(aw.qmc.varC[2])                                     #1C END   temperature
            aw.qmc.varC[5] = aw.BTfromseconds(aw.qmc.varC[4])                                     #2C START temperature
            aw.qmc.varC[7] = aw.BTfromseconds(aw.qmc.varC[6])                                     #2C END   temperature
            aw.qmc.startend[3] = aw.BTfromseconds(aw.qmc.startend[2])                                                        

            #update events             
            ntlines = len(aw.qmc.specialevents)         #number of events found            
            if ntlines > 0:
                aw.qmc.specialevents[0] = aw.qmc.timex.index(self.choice(aw.qmc.stringtoseconds(unicode(self.line1b.text()))))
                aw.qmc.specialeventsStrings[0] = unicode(self.line1.text())
            if ntlines > 1:
                aw.qmc.specialevents[1] = aw.qmc.timex.index(self.choice(aw.qmc.stringtoseconds(unicode(self.line2b.text()))))
                aw.qmc.specialeventsStrings[1] = unicode(self.line2.text())
            if ntlines > 2:
                aw.qmc.specialevents[2] = aw.qmc.timex.index(self.choice(aw.qmc.stringtoseconds(unicode(self.line3b.text()))))
                aw.qmc.specialeventsStrings[2] = unicode(self.line3.text())
            if ntlines > 3:
                aw.qmc.specialevents[3] = aw.qmc.timex.index(self.choice(aw.qmc.stringtoseconds(unicode(self.line4b.text()))))
                aw.qmc.specialeventsStrings[3] = unicode(self.line4.text())
            if ntlines > 4:
                aw.qmc.specialevents[4] = aw.qmc.timex.index(self.choice(aw.qmc.stringtoseconds(unicode(self.line5b.text()))))
                aw.qmc.specialeventsStrings[4] = unicode(self.line5.text())
            if ntlines > 5:
                aw.qmc.specialevents[5] = aw.qmc.timex.index(self.choice(aw.qmc.stringtoseconds(unicode(self.line6b.text()))))
                aw.qmc.specialeventsStrings[5] = unicode(self.line6.text())
            if ntlines > 6:
                aw.qmc.specialevents[6] = aw.qmc.timex.index(self.choice(aw.qmc.stringtoseconds(unicode(self.line7b.text()))))
                aw.qmc.specialeventsStrings[6] = unicode(self.line7.text())
            if ntlines > 7:
                aw.qmc.specialevents[7] = aw.qmc.timex.index(self.choice(aw.qmc.stringtoseconds(unicode(self.line8b.text()))))
                aw.qmc.specialeventsStrings[7] = unicode(self.line8.text())
            if ntlines > 8:
                aw.qmc.specialevents[8] = aw.qmc.timex.index(self.choice(aw.qmc.stringtoseconds(unicode(self.line9b.text()))))
                aw.qmc.specialeventsStrings[8] = unicode(self.line9.text())
            if ntlines > 9:
                aw.qmc.specialevents[9] = aw.qmc.timex.index(self.choice(aw.qmc.stringtoseconds(unicode(self.line10b.text()))))
                aw.qmc.specialeventsStrings[9] = unicode(self.line10.text())

            # Update Title
            aw.qmc.ax.set_title(unicode(self.titleedit.text()),size=20,color=aw.qmc.palette["title"],fontweight='bold')
            aw.qmc.title = unicode(self.titleedit.text())
            # Update beans
            aw.qmc.beans = unicode(self.beansedit.text())
            #update roaster
            aw.qmc.roaster = unicode(self.roaster.text())

            #update weight
            if unicode(self.weightinedit.text()).isdigit():
                aw.qmc.weight[0] = int(self.weightinedit.text())
            else:
                pass
            if unicode(self.weightoutedit.text()).isdigit():
                aw.qmc.weight[1] = int(self.weightoutedit.text())
            else:
                pass
            aw.qmc.weight[2] = unicode(self.unitsComboBox.currentText())

            #update notes
            aw.qmc.roastertype = unicode(self.roaster.text())
            aw.qmc.operator = unicode(self.operator.text())
            aw.qmc.roastingnotes = unicode(self.roastingeditor.toPlainText())
            aw.qmc.cuppingnotes = unicode(self.cupingeditor.toPlainText())
           
            aw.messagelabel.setText(u"Graph properties updated (but profile not saved in hard-drive)")            
            aw.qmc.redraw()
            self.close()

            
        else:
            aw.messagelabel.setText(u"No data")
            self.close()
            

    #selects the closest match from the available data in timex for a given number of seconds.
    #this helps ploting an event in a recorded spot of the graph, so that we don't need to interpolate.
    #interpolation would cause plotting dimension problems because several graphs depend on the dimension of aw.qmc.timex
    def choice(self,seconds):
        if seconds == 0:
            return 0.0
        else:
            #find where given seconds crosses aw.qmc.timex
            if len(aw.qmc.timex):                           #check that time is not empty just in case
                if aw.qmc.timex[-1] < seconds:
                    aw.messagelabel.setText(u"Time out of reach")
                    return aw.qmc.timex[-1]

                for i in range(len(aw.qmc.timex)):                    
                    # first find the index i where seconds crosses timex
                    if aw.qmc.timex[i] >= seconds:
                        break

                choice1 = aw.qmc.timex[i]   # after
                choice2 = aw.qmc.timex[i-1] # before

                if (choice1 - seconds) < (choice2 - seconds):  #return closest of the two
                    return choice1
                else:
                    return choice2

            
    # adds a new event to the Dlg
    def addevent(self):
        self.accept()                       #saves edited events or notes before adding new event
        if len(aw.qmc.timex) > 1:
            aw.qmc.specialevents.append(0)
            self.close()
            aw.editgraph()
        else:
            aw.messagelabel.setText(u"Events need time and data")

    # pops an event from the Dlg
    def delevent(self):
        if len(aw.qmc.specialevents) > 0:
             aw.qmc.specialevents.pop()
             self.close()
             aw.editgraph()



##########################################################################
#####################  VIEW ERROR LOG DLG  ###############################
##########################################################################
        
class errorDlg(QDialog):
    def __init__(self, parent = None):
        super(errorDlg,self).__init__(parent)
        self.setWindowTitle("Error Log")

        #convert list of errors to an html string
        htmlerr = ""
        for i in range(len(aw.qmc.errorlog)):
            htmlerr += "<b>" + str(i+1) + "</b> <i>" + aw.qmc.errorlog[i] + "</i><br><br>"

        enumber = len(aw.qmc.errorlog)
        labelstr =  "Number of errors found <b>" + unicode(enumber) +"</b>"
        elabel = QLabel(labelstr)
        errorEdit = QTextEdit()
        errorEdit.setHtml(htmlerr)
        errorEdit.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(elabel,0)
        layout.addWidget(errorEdit,1)
                               
        self.setLayout(layout)

##########################################################################
#####################  ROAST CALCULATOR DLG   ############################
##########################################################################
        
class calculatorDlg(QDialog):
    def __init__(self, parent = None):
        super(calculatorDlg,self).__init__(parent)
        self.setWindowTitle("Roast calculator")

        usagelabel = QLabel("<center>USAGE: Press ENTER inside a box</center>")

        #RATE OF CHANGE
        rateofchangelabel = QLabel("<b>Rate of change</b>")
        self.result1 = QLabel("Enter two times along profile")
        self.result2 = QLabel()
        self.result2.setStyleSheet("background-color:'lightgrey';")

        startlabel = QLabel("Start (00:00)")
        endlabel = QLabel("End (00:00)")
        self.startEdit = QLineEdit()
        self.endEdit = QLineEdit()
        regextime = QRegExp(r"^[0-9]{1,2}:[0-9]{1,2}$")
        self.startEdit.setValidator(QRegExpValidator(regextime,self))
        self.endEdit.setValidator(QRegExpValidator(regextime,self))
        
        self.connect(self.startEdit,SIGNAL("returnPressed()"),self.calculateRC)
        self.connect(self.endEdit,SIGNAL("returnPressed()"),self.calculateRC)

        #TEMPERATURE CONVERSION
        tconversionLabel = QLabel("<b>Temperature conversion</b>")
        flabel = QLabel("Fahrenheit")
        clabel = QLabel("Celsius")
        self.faEdit = QLineEdit()
        self.ceEdit = QLineEdit()                
        self.faEdit.setValidator(QDoubleValidator(-999., 9999., 2, self.faEdit))
        self.ceEdit.setValidator(QDoubleValidator(-999., 9999., 2, self.ceEdit))
        self.connect(self.faEdit,SIGNAL("returnPressed()"),lambda x="FtoC":self.convertTemp(x))
        self.connect(self.ceEdit,SIGNAL("returnPressed()"),lambda x="CtoF":self.convertTemp(x))

        #WEIGHT CONVERSION
        wconversionLabel = QLabel("<b>Weight conversion</b>")
        self.inComboBox = QComboBox()
        self.inComboBox.addItems(["g","Kg","lb"])
        self.inComboBox.setMaximumWidth(50)
        self.outComboBox = QComboBox()
        self.outComboBox.setMaximumWidth(50)
        self.outComboBox.addItems(["g","Kg","lb"])
        self.outComboBox.setCurrentIndex(2)
        self.inEdit = QLineEdit()
        self.outEdit = QLineEdit()
        self.inEdit.setMaximumWidth(60)
        self.outEdit.setMaximumWidth(60)
        self.inEdit.setValidator(QDoubleValidator(0., 99999., 2, self.inEdit))
        self.outEdit.setValidator(QDoubleValidator(0., 99999., 2, self.outEdit))
        self.connect(self.inEdit,SIGNAL("returnPressed()"),lambda x="ItoO":self.convertWeight(x))
        self.connect(self.outEdit,SIGNAL("returnPressed()"),lambda x="OtoI":self.convertWeight(x))
        
        #LAYOUTS
        #Rate of chage
        calrcLayout = QGridLayout()
        calrcLayout.addWidget(startlabel,0,0)
        calrcLayout.addWidget(endlabel,0,1)
        calrcLayout.addWidget(self.startEdit,1,0)
        calrcLayout.addWidget(self.endEdit,1,1)
        
        rclayout = QVBoxLayout()
        rclayout.addWidget(rateofchangelabel,0)
        rclayout.addWidget(self.result1,1)
        rclayout.addWidget(self.result2,2)
        rclayout.addLayout(calrcLayout,3)

        #temperature conversion
        tempLayout = QGridLayout()        
        tempLayout.addWidget(flabel,0,0)
        tempLayout.addWidget(clabel,0,1)
        tempLayout.addWidget(self.faEdit,1,0)
        tempLayout.addWidget(self.ceEdit,1,1)

        #weight conversions
        weightLayout = QHBoxLayout()
        weightLayout.addWidget(self.inComboBox,0)
        weightLayout.addWidget(self.inEdit,1)
        weightLayout.addWidget(self.outEdit,2)
        weightLayout.addWidget(self.outComboBox,3)


        #main
        mainlayout = QVBoxLayout()
        mainlayout.setSpacing(10)
        mainlayout.addWidget(usagelabel,0)
        mainlayout.addLayout(rclayout,1)
        mainlayout.addWidget(tconversionLabel,2)
        mainlayout.addLayout(tempLayout,3)
        mainlayout.addWidget(wconversionLabel,4)
        mainlayout.addLayout(weightLayout,5)
        
        self.setLayout(mainlayout)

    #selects closest time INDEX in aw.qmc.timex from secons
    #used by calculate()
    def choice(self,seconds):
        if seconds == 0:
            return 0.0
        #find where given seconds crosses aw.qmc.timex
        if len(aw.qmc.timex):                           #check that time is not empty just in case
            if aw.qmc.timex[-1] < seconds:
                return aw.qmc.timex[-1]            
            for i in range(len(aw.qmc.timex)):
                # first find the index i where seconds crosses timex
                if aw.qmc.timex[i] > seconds:
                    break
            choice1 = aw.qmc.timex[i]   # after or equal
            choice2 = aw.qmc.timex[i-1] # before

            if (choice1-seconds) < (choice2-seconds):  #return closest INDEX 
                return i
            else:
                return i-1

    #calculate rate of change        
    def calculateRC(self):
        if len(aw.qmc.timex)>2:
            starttime = aw.qmc.stringtoseconds(unicode(self.startEdit.text()))
            endtime = aw.qmc.stringtoseconds(unicode(self.endEdit.text()))

            if starttime == -1 or endtime == -1:
                self.result1.setText("time sintax error. Time not valid")
                self.result2.setText("")
                return

            if  endtime > aw.qmc.timex[-1] or endtime < starttime:
                self.result1.setText("time profile error")
                self.result2.setText("")
                return

            #if profile has a CHARGE time (time is referenced to charge time)
            if aw.qmc.startend[0]:
                starttime += aw.qmc.startend[0]
                endtime += aw.qmc.startend[0]
                startindex = self.choice(starttime)
                endindex = self.choice(endtime)
                
            #if profile does not have a CHARGE time (time is absolute time)   
            else:
                startindex = self.choice(starttime)
                endindex = self.choice(endtime)

            #delta
            deltatime = float(aw.qmc.timex[endindex] -  aw.qmc.timex[startindex])
            deltatemperature = float(aw.qmc.temp2[endindex] - aw.qmc.temp2[startindex])
            if deltatime == 0:
                deltaseconds = 0
            else:
                deltaseconds = deltatemperature/deltatime
            deltaminutes = deltaseconds*60.
            
            if aw.qmc.startend[0]:
                string1 = ( u"Best approximation was made from " + aw.qmc.stringfromseconds(aw.qmc.timex[startindex]-aw.qmc.startend[0]) +
                            u" to " + aw.qmc.stringfromseconds(aw.qmc.timex[endindex]-aw.qmc.startend[0] ))
            else:
                string1 = (u"Best approximation was made from " + aw.qmc.stringfromseconds(aw.qmc.timex[startindex]) + u" to " +
                           aw.qmc.stringfromseconds(aw.qmc.timex[endindex]))
                
            string2 = u"deg/sec = " + u"%.2f"%(deltaseconds) + u"    deg/min = " + u"%.2f"%(deltaminutes)
            
            self.result1.setText(string1)        
            self.result2.setText(string2)
        else:
            self.result1.setText("No profile found")  
            self.result2.setText("")

    def convertTemp(self,x):
        if x == "FtoC":
           newC = aw.qmc.fromFtoC(float(str(self.faEdit.text())))
           result = u"%.2f"%newC
           self.ceEdit.setText(result)
            
        elif x == "CtoF":
           newF = aw.qmc.fromCtoF(float(str(self.ceEdit.text())))
           result = u"%.2f"%newF
           self.faEdit.setText(result)          

    def convertWeight(self,x):
        #                g,            kg,         lb
        convtable = [
                        [1.,           0.001,      0.00220462262     ],    # g
                        [1000,         1.,         2.205             ],    # Kg
                        [453.591999,   0.45359237, 1.                ]     #lb
                    ]
        
        if x == "ItoO":
           inx = float(unicode(self.inEdit.text()))
           outx = inx*convtable[self.inComboBox.currentIndex()][self.outComboBox.currentIndex()]
           self.outEdit.setText(u"%.2f"%outx)
            
        elif x == "OtoI":
           outx = float(unicode(self.outEdit.text()))
           inx = outx*convtable[self.outComboBox.currentIndex()][self.inComboBox.currentIndex()]
           self.inEdit.setText(u"%.2f"%inx)
           
##########################################################################
############################     HUD  DLG     ############################
##########################################################################
        
class HUDDlg(QDialog):
    def __init__(self, parent = None):
        super(HUDDlg,self).__init__(parent)

        self.setWindowTitle("HUD config")
        ETLabel = QLabel("ET target")
        BTLabel = QLabel("BT target")
        self.ETlineEdit = QLineEdit(str(aw.qmc.ETtarget))           
        self.BTlineEdit = QLineEdit(str(aw.qmc.BTtarget))
        self.ETlineEdit.setValidator(QIntValidator(0, 1000, self.ETlineEdit))
        self.BTlineEdit.setValidator(QIntValidator(0, 1000, self.BTlineEdit))

        okButton = QPushButton("OK")  
        cancelButton = QPushButton("Cancel")        
        self.connect(cancelButton,SIGNAL("clicked()"),self.close)
        self.connect(okButton,SIGNAL("clicked()"),self.updatetargets)
                                     
        hudLayout = QGridLayout()
        hudLayout.addWidget(ETLabel,0,0)
        hudLayout.addWidget(self.ETlineEdit,0,1)
        hudLayout.addWidget(BTLabel,1,0)
        hudLayout.addWidget(self.BTlineEdit,1,1)
        hudLayout.addWidget(okButton,2,0)
        hudLayout.addWidget(cancelButton,2,1)   
        self.setLayout(hudLayout)

    def updatetargets(self):
        aw.qmc.ETtarget = int(unicode(self.ETlineEdit.text()))
        aw.qmc.BTtarget = int(unicode(self.BTlineEdit.text()))
        string = u"[ET target = " + unicode(self.ETlineEdit.text()) + u"] [BT target = " + unicode(self.BTlineEdit.text()) + u"]"
        aw.HUDstatus.showMessage(string,3000)
        self.close()
        

##########################################################################
#####################  PHASES GRAPH EDIT DLG  ############################
##########################################################################
        
class phasesGraphDlg(QDialog):
    def __init__(self, parent = None):
        super(phasesGraphDlg,self).__init__(parent)

        self.setWindowTitle("Phases of roast")

        dryLabel = QLabel("Dry")
        midLabel = QLabel("Mid")
        finishLabel = QLabel("Finish")

        self.startdry = QSpinBox()
        self.enddry = QSpinBox()
        self.startmid = QSpinBox()
        self.endmid = QSpinBox()
        self.startfinish = QSpinBox()
        self.endfinish = QSpinBox()
        
        if aw.qmc.mode == u"F":
             self.startdry.setSuffix(" F")
             self.enddry.setSuffix(" F")
             self.startmid.setSuffix(" F")
             self.endmid.setSuffix(" F")
             self.startfinish.setSuffix(" F")
             self.endfinish.setSuffix(" F")

             self.startdry.setRange(0,1000)    #(min,max)
             self.enddry.setRange(0,1000)
             self.startmid.setRange(0,1000)
             self.endmid.setRange(0,1000)
             self.startfinish.setRange(0,1000)
             self.endfinish.setRange(0,1000)               
                                        
        elif aw.qmc.mode == u"C":
             self.startdry.setSuffix(" C")
             self.enddry.setSuffix(" C")
             self.startmid.setSuffix(" C")
             self.endmid.setSuffix(" C")
             self.startfinish.setSuffix(" C")
             self.endfinish.setSuffix(" C")

             self.startdry.setRange(0,1000)    #(min,max)
             self.enddry.setRange(0,1000)
             self.startmid.setRange(0,1000)
             self.endmid.setRange(0,1000)
             self.startfinish.setRange(0,1000)
             self.endfinish.setRange(0,1000)

        self.connect(self.enddry,SIGNAL("valueChanged(int)"),self.startmid.setValue)
        self.connect(self.startmid,SIGNAL("valueChanged(int)"),self.enddry.setValue)
        self.connect(self.endmid,SIGNAL("valueChanged(int)"),self.startfinish.setValue)
        self.connect(self.startfinish,SIGNAL("valueChanged(int)"),self.endmid.setValue)  


        self.startdry.setValue(aw.qmc.phases[0])
        self.enddry.setValue(aw.qmc.phases[1])
        self.startmid.setValue(aw.qmc.phases[1])
        self.endmid.setValue(aw.qmc.phases[2])
        self.startfinish.setValue(aw.qmc.phases[2])
        self.endfinish.setValue(aw.qmc.phases[3])


        okButton = QPushButton("OK")  
        cancelButton = QPushButton("Cancel")
        setDefaultButton = QPushButton("Default")
        
        self.connect(cancelButton,SIGNAL("clicked()"),self.close)
        self.connect(okButton,SIGNAL("clicked()"),self.updatephases)
        self.connect(setDefaultButton,SIGNAL("clicked()"),self.setdefault)
                                     
        phaseLayout = QGridLayout()
        phaseLayout.addWidget(dryLabel,0,0)
        phaseLayout.addWidget(self.startdry,0,1)
        phaseLayout.addWidget(self.enddry,0,2)
        phaseLayout.addWidget(midLabel,1,0)
        phaseLayout.addWidget(self.startmid,1,1)
        phaseLayout.addWidget(self.endmid,1,2)
        phaseLayout.addWidget(finishLabel,2,0)
        phaseLayout.addWidget(self.startfinish,2,1)
        phaseLayout.addWidget(self.endfinish,2,2)
        phaseLayout.addWidget(setDefaultButton,3,1)
        phaseLayout.addWidget(cancelButton,4,1)
        phaseLayout.addWidget(okButton,4,2)
                             
        self.setLayout(phaseLayout)

    def updatephases(self):
        aw.qmc.phases[0] = self.startdry.value()
        aw.qmc.phases[1] = self.enddry.value()
        aw.qmc.phases[2] = self.endmid.value()
        aw.qmc.phases[3] = self.endfinish.value()
        
        aw.qmc.redraw()
        self.close()

    def setdefault(self):
        if aw.qmc.mode == u"F":
            aw.qmc.phases = [200,300,390,450]
            aw.messagelabel.setText(u"Phases changed to F default: [200,300,390,450]")

        elif aw.qmc.mode == u"C":
            aw.qmc.phases = [95,150,200,230]
            aw.messagelabel.setText(u"Phases changed to C default: [95,150,200,230]")
        aw.qmc.redraw()
        self.close()

############################################################################        
#####################   FLAVOR STAR PROPERTIES DIALOG   ####################
############################################################################
        
class flavorDlg(QDialog):
    def __init__(self, parent = None):
        super(flavorDlg,self).__init__(parent)

        self.setWindowTitle("Cup Profile")

        self.line0edit = QLineEdit(aw.qmc.flavorlabels[0])        
        self.line1edit = QLineEdit(aw.qmc.flavorlabels[1])
        self.line2edit = QLineEdit(aw.qmc.flavorlabels[2])
        self.line3edit = QLineEdit(aw.qmc.flavorlabels[3])
        self.line4edit = QLineEdit(aw.qmc.flavorlabels[4])
        self.line5edit = QLineEdit(aw.qmc.flavorlabels[5])
        self.line6edit = QLineEdit(aw.qmc.flavorlabels[6])
        self.line7edit = QLineEdit(aw.qmc.flavorlabels[7])
        self.line8edit = QLineEdit(aw.qmc.flavorlabels[8])
        
        aciditySlider = QSlider(Qt.Horizontal)
        aciditySlider.setRange(0,10)
        aciditySlider.setTickInterval(1)
        aciditySlider.setValue((int(aw.qmc.flavors[0]*10.)))
        self.aciditySpinbox = QSpinBox()
        self.aciditySpinbox.setMaximum(10) 
        self.aciditySpinbox.setValue((int(aw.qmc.flavors[0]*10.)))

        aftertasteSlider = QSlider(Qt.Horizontal)
        aftertasteSlider.setRange(0,10)
        aftertasteSlider.setTickInterval(1)
        aftertasteSlider.setValue((int(aw.qmc.flavors[1]*10.)))
        self.aftertasteSpinbox = QSpinBox()
        self.aftertasteSpinbox.setMaximum(10) 
        self.aftertasteSpinbox.setValue((int(aw.qmc.flavors[1]*10.)))

        cleanupSlider = QSlider(Qt.Horizontal)
        cleanupSlider.setRange(0,10)
        cleanupSlider.setTickInterval(1)
        cleanupSlider.setValue((int(aw.qmc.flavors[2]*10.)))
        self.cleanupSpinbox = QSpinBox()
        self.cleanupSpinbox.setMaximum(10) 
        self.cleanupSpinbox.setValue((int(aw.qmc.flavors[2]*10.)))

        headSlider = QSlider(Qt.Horizontal)
        headSlider.setRange(0,10)
        headSlider.setTickInterval(1)
        headSlider.setValue((int(aw.qmc.flavors[3]*10.)))
        self.headSpinbox = QSpinBox()
        self.headSpinbox.setMaximum(10) 
        self.headSpinbox.setValue((int(aw.qmc.flavors[3]*10.)))
        
        fraganceSlider = QSlider(Qt.Horizontal)
        fraganceSlider.setRange(0,10)
        fraganceSlider.setTickInterval(1)
        fraganceSlider.setValue((int(aw.qmc.flavors[4]*10.)))
        self.fraganceSpinbox = QSpinBox()
        self.fraganceSpinbox.setMaximum(10) 

        self.fraganceSpinbox.setValue((int(aw.qmc.flavors[4]*10.)))

        sweetnessSlider = QSlider(Qt.Horizontal)
        sweetnessSlider.setRange(0,10)
        sweetnessSlider.setTickInterval(1)
        sweetnessSlider.setValue((int(aw.qmc.flavors[5]*10.)))
        self.sweetnessSpinbox = QSpinBox()
        self.sweetnessSpinbox.setMaximum(10) 
        self.sweetnessSpinbox.setValue((int(aw.qmc.flavors[5]*10.)))

        aromaSlider = QSlider(Qt.Horizontal)
        aromaSlider.setRange(0,10)
        aromaSlider.setTickInterval(1)
        aromaSlider.setValue((int(aw.qmc.flavors[6]*10.)))
        self.aromaSpinbox = QSpinBox()
        self.aromaSpinbox.setMaximum(10) 
        self.aromaSpinbox.setValue((int(aw.qmc.flavors[6]*10.)))
        
        balanceSlider = QSlider(Qt.Horizontal)
        balanceSlider.setRange(0,10)
        balanceSlider.setTickInterval(1)
        balanceSlider.setValue((int(aw.qmc.flavors[7]*10.)))
        self.balanceSpinbox = QSpinBox()
        self.balanceSpinbox.setMaximum(10) 
        self.balanceSpinbox.setValue((int(aw.qmc.flavors[7]*10.)))

        bodySlider = QSlider(Qt.Horizontal)
        bodySlider.setRange(0,10)
        bodySlider.setTickInterval(1)
        bodySlider.setValue((int(aw.qmc.flavors[8]*10.)))
        self.bodySpinbox = QSpinBox()
        self.bodySpinbox.setMaximum(10) 

        self.bodySpinbox.setValue((int(aw.qmc.flavors[8]*10.)))        


        backButton = QPushButton("Save and Close")
        cancelButton = QPushButton("Cancel")
        updatelabelsButton = QPushButton("Update labels")
        defaultButton = QPushButton("Default labels")
        
        self.connect(self.aciditySpinbox,SIGNAL("valueChanged(int)"),aciditySlider.setValue)
        self.connect(self.aciditySpinbox,SIGNAL("valueChanged(int)"), lambda val=self.aciditySpinbox.value(): self.adjustflavor(0,val))
        self.connect(self.aciditySpinbox,SIGNAL("valueChanged(int)"), lambda val=self.aciditySpinbox.value(): self.adjustflavor(9,val))
        self.connect(aciditySlider,SIGNAL("valueChanged(int)"),self.aciditySpinbox.setValue)
        self.connect(self.aciditySpinbox,SIGNAL("valueChanged(int)"),aw.qmc.flavorchart)
                     
        self.connect(self.aftertasteSpinbox,SIGNAL("valueChanged(int)"),aftertasteSlider.setValue)
        self.connect(aftertasteSlider,SIGNAL("valueChanged(int)"),self.aftertasteSpinbox.setValue)
        self.connect(self.aftertasteSpinbox,SIGNAL("valueChanged(int)"), lambda val=self.aftertasteSpinbox.value(): self.adjustflavor(1,val))
        self.connect(self.aftertasteSpinbox,SIGNAL("valueChanged(int)"),aw.qmc.flavorchart)


        self.connect(self.cleanupSpinbox,SIGNAL("valueChanged(int)"),cleanupSlider.setValue)
        self.connect(cleanupSlider,SIGNAL("valueChanged(int)"),self.cleanupSpinbox.setValue)
        self.connect(self.cleanupSpinbox,SIGNAL("valueChanged(int)"), lambda val=self.cleanupSpinbox.value(): self.adjustflavor(2,val))
        self.connect(self.cleanupSpinbox,SIGNAL("valueChanged(int)"),aw.qmc.flavorchart)


        self.connect(self.headSpinbox,SIGNAL("valueChanged(int)"),headSlider.setValue)
        self.connect(headSlider,SIGNAL("valueChanged(int)"),self.headSpinbox.setValue)
        self.connect(self.headSpinbox,SIGNAL("valueChanged(int)"), lambda val=self.headSpinbox.value(): self.adjustflavor(3,val))
        self.connect(self.headSpinbox,SIGNAL("valueChanged(int)"),aw.qmc.flavorchart)


        self.connect(self.fraganceSpinbox,SIGNAL("valueChanged(int)"),fraganceSlider.setValue)
        self.connect(fraganceSlider,SIGNAL("valueChanged(int)"),self.fraganceSpinbox.setValue)
        self.connect(self.fraganceSpinbox,SIGNAL("valueChanged(int)"), lambda val=self.fraganceSpinbox.value(): self.adjustflavor(4,val))
        self.connect(self.fraganceSpinbox,SIGNAL("valueChanged(int)"),aw.qmc.flavorchart)


        self.connect(self.sweetnessSpinbox,SIGNAL("valueChanged(int)"),sweetnessSlider.setValue)
        self.connect(sweetnessSlider,SIGNAL("valueChanged(int)"),self.sweetnessSpinbox.setValue)
        self.connect(self.sweetnessSpinbox,SIGNAL("valueChanged(int)"), lambda val=self.sweetnessSpinbox.value(): self.adjustflavor(5,val))
        self.connect(self.sweetnessSpinbox,SIGNAL("valueChanged(int)"),aw.qmc.flavorchart)


        self.connect(self.aromaSpinbox,SIGNAL("valueChanged(int)"),aromaSlider.setValue)
        self.connect(aromaSlider,SIGNAL("valueChanged(int)"),self.aromaSpinbox.setValue)
        self.connect(self.aromaSpinbox,SIGNAL("valueChanged(int)"), lambda val=self.aromaSpinbox.value(): self.adjustflavor(6,val))
        self.connect(self.aromaSpinbox,SIGNAL("valueChanged(int)"),aw.qmc.flavorchart)


        self.connect(self.balanceSpinbox,SIGNAL("valueChanged(int)"),balanceSlider.setValue)
        self.connect(balanceSlider,SIGNAL("valueChanged(int)"),self.balanceSpinbox.setValue)
        self.connect(self.balanceSpinbox,SIGNAL("valueChanged(int)"), lambda val=self.balanceSpinbox.value(): self.adjustflavor(7,val))
        self.connect(self.balanceSpinbox,SIGNAL("valueChanged(int)"),aw.qmc.flavorchart)


        self.connect(self.bodySpinbox,SIGNAL("valueChanged(int)"),bodySlider.setValue)
        self.connect(bodySlider,SIGNAL("valueChanged(int)"),self.bodySpinbox.setValue)
        self.connect(self.bodySpinbox,SIGNAL("valueChanged(int)"), lambda val=self.bodySpinbox.value(): self.adjustflavor(8,val))
        self.connect(self.bodySpinbox,SIGNAL("valueChanged(int)"),aw.qmc.flavorchart)

        
        self.connect(backButton,SIGNAL("clicked()"),self.close)
        self.connect(cancelButton,SIGNAL("clicked()"),self.cancel)
        self.connect(updatelabelsButton,SIGNAL("clicked()"),self.updatelabels)
        self.connect(defaultButton,SIGNAL("clicked()"),self.defaultlabels)

        flavorLayout = QGridLayout()
        flavorLayout.addWidget(self.line0edit,0,0)
        flavorLayout.addWidget(aciditySlider,0,1)
        flavorLayout.addWidget(self.aciditySpinbox,0,2)
        flavorLayout.addWidget(self.line1edit,1,0)
        flavorLayout.addWidget(aftertasteSlider,1,1)
        flavorLayout.addWidget(self.aftertasteSpinbox,1,2)
        flavorLayout.addWidget(self.line2edit,2,0)
        flavorLayout.addWidget(cleanupSlider,2,1)
        flavorLayout.addWidget(self.cleanupSpinbox,2,2)
        flavorLayout.addWidget(self.line3edit,3,0)
        flavorLayout.addWidget(headSlider,3,1)
        flavorLayout.addWidget(self.headSpinbox,3,2)
        flavorLayout.addWidget(self.line4edit,4,0)
        flavorLayout.addWidget(fraganceSlider,4,1)
        flavorLayout.addWidget(self.fraganceSpinbox,4,2)
        flavorLayout.addWidget(self.line5edit,5,0)
        flavorLayout.addWidget(sweetnessSlider,5,1)
        flavorLayout.addWidget(self.sweetnessSpinbox,5,2)
        flavorLayout.addWidget(self.line6edit,6,0)
        flavorLayout.addWidget(aromaSlider,6,1)
        flavorLayout.addWidget(self.aromaSpinbox,6,2)
        flavorLayout.addWidget(self.line7edit,7,0)
        flavorLayout.addWidget(balanceSlider,7,1)
        flavorLayout.addWidget(self.balanceSpinbox,7,2)
        flavorLayout.addWidget(self.line8edit,8,0)
        flavorLayout.addWidget(bodySlider,8,1)
        flavorLayout.addWidget(self.bodySpinbox,8,2)
        flavorLayout.addWidget(updatelabelsButton,9,0)
        flavorLayout.addWidget(backButton,9,1)
        flavorLayout.addWidget(defaultButton,10,0)
        flavorLayout.addWidget(cancelButton,10,1)
        
        self.setLayout(flavorLayout)
        aw.qmc.flavorchart()

    def updatelabels(self):
        aw.qmc.flavorlabels[0] = unicode(self.line0edit.displayText())
        aw.qmc.flavorlabels[1] = unicode(self.line1edit.displayText())
        aw.qmc.flavorlabels[2] = unicode(self.line2edit.displayText())
        aw.qmc.flavorlabels[3] = unicode(self.line3edit.displayText())
        aw.qmc.flavorlabels[4] = unicode(self.line4edit.displayText())
        aw.qmc.flavorlabels[5] = unicode(self.line5edit.displayText())
        aw.qmc.flavorlabels[6] = unicode(self.line6edit.displayText())
        aw.qmc.flavorlabels[7] = unicode(self.line7edit.displayText())
        aw.qmc.flavorlabels[8] = unicode(self.line8edit.displayText())   

        aw.qmc.flavorchart()

    def defaultlabels(self):
        aw.qmc.flavorlabels = [u'Acidity',u'After taste',u'Clean cup',u'Head',u'Fragance',u'Sweetness',u'Aroma',u'Balance',u'Body']
        
        aw.qmc.flavorchart()
        
    def adjustflavor(self,key,val):
        aw.qmc.flavors[key] = float(val)/10.

    def closeEvent(self, event):
        aw.qmc.redraw()
        self.accept()
        
    def close(self):
        self.updatelabels()
        aw.qmc.redraw()
        self.accept()

    def cancel(self):
        aw.qmc.redraw()
        self.accept()

#################################################################
#################### BACKGROUND DIALOG  #########################
#################################################################

class backgroundDLG(QDialog):
    def __init__(self, parent = None):
        super(backgroundDLG,self).__init__(parent)
        self.setWindowTitle("Profile background")

        self.pathedit = QLineEdit(aw.qmc.backgroundpath)
        self.pathedit.setStyleSheet("background-color:'lightgrey';")
        self.fname = u""
        
        self.backgroundCheck = QCheckBox("Show")
        self.backgroundDetails = QCheckBox("Text")
        
        if aw.qmc.background:
            self.backgroundCheck.setChecked(True)
        else:
            self.backgroundCheck.setChecked(False)

        self.status = QStatusBar()
        self.status.setSizeGripEnabled(False)
        self.status.showMessage("Ready",3000)

        if aw.qmc.backgroundDetails:
            self.backgroundDetails.setChecked(True)
        else:
            self.backgroundDetails.setChecked(False)

        loadButton = QPushButton("Load")
        delButton = QPushButton("Delete")
        cancelButton = QPushButton("Close")
        selectButton =QPushButton("Select Profile")
        
        self.connect(loadButton, SIGNAL("clicked()"),self.load)
        self.connect(cancelButton, SIGNAL("clicked()"),self, SLOT("reject()"))        
        self.connect(selectButton, SIGNAL("clicked()"), self.selectpath)

        self.speedSpinBox = QSpinBox()
        self.speedSpinBox.setRange(10,90)
        self.speedSpinBox.setSingleStep(10)
        self.speedSpinBox.setValue(30)
        
        intensitylabel =QLabel("Opaqueness")
        intensitylabel.setAlignment(Qt.AlignRight)
        self.intensitySpinBox = QSpinBox()
        self.intensitySpinBox.setRange(1,9)
        self.intensitySpinBox.setSingleStep(1)
        self.intensitySpinBox.setValue(3)

        widthlabel =QLabel("Line Width")
        widthlabel.setAlignment(Qt.AlignRight)
        self.widthSpinBox = QSpinBox()
        self.widthSpinBox.setRange(1,20)
        self.widthSpinBox.setSingleStep(1)
        self.widthSpinBox.setValue(2)

        stylelabel =QLabel("Line Style")
        stylelabel.setAlignment(Qt.AlignRight)        
        self.styleComboBox = QComboBox()
        self.styleComboBox.addItems(["-","--",":","-.","steps"])
        self.styleComboBox.setCurrentIndex(0)


        colors = [u""]
        for key in cnames:
            colors.append(unicode(key))
        colors.sort()
        colors.insert(0,u"met")
        colors.insert(1,u"bt")
        colors.pop(2)
        
        btcolorlabel = QLabel("BT color")
        btcolorlabel.setAlignment(Qt.AlignRight)        
        self.btcolorComboBox = QComboBox()
        self.btcolorComboBox.addItems(colors)
        self.btcolorComboBox.setCurrentIndex(1)

        metcolorlabel = QLabel("MET color")
        metcolorlabel.setAlignment(Qt.AlignRight)        
        self.metcolorComboBox = QComboBox()
        self.metcolorComboBox.addItems(colors)
        self.metcolorComboBox.setCurrentIndex(0)
        
        self.upButton = QPushButton("Up")
        self.downButton = QPushButton("Down")
        self.leftButton = QPushButton("Left")
        self.rightButton = QPushButton("Right")

        self.connect(self.backgroundCheck, SIGNAL("clicked()"),self.readChecks)
        self.connect(self.backgroundDetails, SIGNAL("clicked()"),self.readChecks)
        self.connect(delButton, SIGNAL("clicked()"),self.delete)
        self.connect(self.upButton, SIGNAL("clicked()"), lambda m= "up": self.move(m))
        self.connect(self.downButton, SIGNAL("clicked()"), lambda m="down": self.move(m))
        self.connect(self.leftButton, SIGNAL("clicked()"), lambda m="left": self.move(m))
        self.connect(self.rightButton, SIGNAL("clicked()"),lambda m="right": self.move(m))
        self.connect(self.intensitySpinBox, SIGNAL("valueChanged(int)"),self.adjustintensity)
        self.connect(self.widthSpinBox, SIGNAL("valueChanged(int)"),self.adjustwidth)
        self.connect(self.btcolorComboBox, SIGNAL("currentIndexChanged(QString)"),lambda color="", curve = "bt": self.adjustcolor(color,curve))
        self.connect(self.metcolorComboBox, SIGNAL("currentIndexChanged(QString)"),lambda color= "", curve = "met": self.adjustcolor(color,curve))
        self.connect(self.styleComboBox, SIGNAL("currentIndexChanged(QString)"),self.adjuststyle)
        

        movelayout = QGridLayout()
        movelayout.addWidget(self.upButton,0,1)
        movelayout.addWidget(self.leftButton,1,0)
        movelayout.addWidget(self.speedSpinBox,1,1)
        movelayout.addWidget(self.rightButton,1,2)
        movelayout.addWidget(self.downButton,2,1)

        layout = QGridLayout()
        layout.addWidget(selectButton,0,0)
        layout.addWidget(self.pathedit,0,1)
        layout.addWidget(loadButton,1,0)
        layout.addWidget(delButton,1,1)
        layout.addWidget(self.backgroundCheck,2,0)
        layout.addWidget(self.backgroundDetails,2,1)
        layout.addWidget(widthlabel,3,0)
        layout.addWidget(self.widthSpinBox,3,1)
        layout.addWidget(intensitylabel,4,0)
        layout.addWidget(self.intensitySpinBox,4,1)
        layout.addWidget(metcolorlabel,5,0)
        layout.addWidget(self.metcolorComboBox,5,1)
        layout.addWidget(btcolorlabel,6,0)
        layout.addWidget(self.btcolorComboBox,6,1)
        layout.addWidget(stylelabel,7,0)
        layout.addWidget(self.styleComboBox,7,1)
        layout.addWidget(cancelButton,8,1)

        mainlayout = QVBoxLayout()
        mainlayout.addWidget(self.status,0)
        mainlayout.addLayout(movelayout,1)
        mainlayout.addSpacing(30)
        mainlayout.addLayout(layout,2)
        
        self.setLayout(mainlayout)

    def adjuststyle(self):
        
        self.status.showMessage("Processing...",5000)
        #block button
        self.styleComboBox.setDisabled(True) 
        aw.qmc.backgroundstyle = unicode(self.styleComboBox.currentText())
        aw.qmc.redraw()
        #reactivate button
        self.styleComboBox.setDisabled(False)
        self.status.showMessage("Ready",5000)         

    def adjustcolor(self,color,curve):
        color = str(color)
        self.status.showMessage("Processing...",5000)
     
        self.btcolorComboBox.setDisabled(True)
        self.metcolorComboBox.setDisabled(True)
        
        if curve == u"met":
            if color == u"met":
                aw.qmc.backgroundmetcolor = aw.qmc.palette["met"]
            elif color == u"bt":
                aw.qmc.backgroundmetcolor = aw.qmc.palette["bt"]
            else:
                aw.qmc.backgroundmetcolor = color
                
        elif curve == u"bt":
            if color == u"bt":
                aw.qmc.backgroundbtcolor = aw.qmc.palette["bt"]
            elif color == u"met":
                aw.qmc.backgroundbtcolor = aw.qmc.palette["met"]                
            else:
                aw.qmc.backgroundbtcolor = color

        aw.qmc.redraw()
        self.btcolorComboBox.setDisabled(False)
        self.metcolorComboBox.setDisabled(False)
        self.status.showMessage("Ready",5000) 

    def adjustwidth(self):
        
        self.status.showMessage("Processing...",5000)
        #block button
        self.widthSpinBox.setDisabled(True)
        aw.qmc.backgroundwidth = self.widthSpinBox.value()
        aw.qmc.redraw()
        #reactivate button
        self.widthSpinBox.setDisabled(False)
        self.status.showMessage("Ready",5000)        

    def adjustintensity(self):
        
        self.status.showMessage("Processing...",5000)
        #block button
        self.intensitySpinBox.setDisabled(True)
        aw.qmc.backgroundalpha = self.intensitySpinBox.value()/10.
        aw.qmc.redraw()
        #reactivate button
        self.intensitySpinBox.setDisabled(False)
        self.status.showMessage("Ready",5000)   
        
    def delete(self):
        
        self.status.showMessage("Processing...",5000)
        self.pathedit.setText(u"")
        self.backgroundDetails.setChecked(False)
        self.backgroundCheck.setChecked(False)
        
        aw.qmc.backgroundET, aw.qmc.backgroundBT, aw.qmc.timeB = [],[],[]
        aw.qmc.startendB, aw.qmc.varCB = [0.,0.,0.,0.,0.,0.,0.,0.],[0.,0.,0.,0.]
        aw.qmc.background = False
        aw.qmc.backgroundDetails = False
        aw.qmc.backmoveflag = 1
        aw.qmc.redraw()
        
        self.status.showMessage("Ready",5000)   
        
    def move(self,m):        
         self.status.showMessage("Processing...",5000)
         #block button
         if m == "up":
             self.upButton.setDisabled(True)
         elif m == "down":
            self.downButton.setDisabled(True)
         elif m == "left":
            self.leftButton.setDisabled(True)
         elif m == "right":
            self.rightButton.setDisabled(True)

         step = self.speedSpinBox.value()
         aw.qmc.movebackground(m,step)
         
         aw.qmc.redraw()
         #activate button
         if m == "up":
             self.upButton.setDisabled(False)
         elif m == "down":
            self.downButton.setDisabled(False)
         elif m == "left":
            self.leftButton.setDisabled(False)
         elif m == "right":
            self.rightButton.setDisabled(False)
            
         self.status.showMessage("Ready",5000)       

    def readChecks(self):
        self.status.showMessage("Processing...",5000)
        if self.backgroundCheck.isChecked():
            aw.qmc.background = True
        else:
            aw.qmc.background = False
            
        if  self.backgroundDetails.isChecked():
            aw.qmc.backgroundDetails = True
        else:
            aw.qmc.backgroundDetails = False
            
        aw.qmc.redraw()
        self.status.showMessage("Ready",5000)   
        

    def selectpath(self):
        filename = unicode(QFileDialog.getOpenFileName(self,"Load Profile",aw.profilepath,"*.txt"))
        self.pathedit.setText(filename)
        self.fname = filename

    def load(self):        
        if unicode(self.pathedit.text()) == "":
            self.status.showMessage("Empty file path",5000)   
            return
        self.status.showMessage("Reading file...",5000)   
        aw.qmc.backgroundpath = unicode(self.pathedit.text())
        aw.loadbackground(unicode(self.pathedit.text()))
        self.backgroundCheck.setChecked(True)
        self.backgroundDetails.setChecked(True)
        self.readChecks()


#############################################################################
################  Statistics DIALOG ########################
#############################################################################
            
class StatisticsDLG(QDialog):       
    def __init__(self, parent = None):
        super(StatisticsDLG,self).__init__(parent)
        self.setWindowTitle("Chose statistics to display")

        regextime = QRegExp(r"^[0-9]{1,2}:[0-9]{1,2}$")

        self.time = QCheckBox("Time")
        self.bar = QCheckBox("Bar")
        self.flavor = QCheckBox("Flavor")
        self.area = QCheckBox("Text data")
        
        self.mindryedit = QLineEdit(aw.qmc.stringfromseconds(aw.qmc.statisticsconditions[0]))        
        self.maxdryedit = QLineEdit(aw.qmc.stringfromseconds(aw.qmc.statisticsconditions[1]))        
        self.minmidedit = QLineEdit(aw.qmc.stringfromseconds(aw.qmc.statisticsconditions[2]))        
        self.maxmidedit = QLineEdit(aw.qmc.stringfromseconds(aw.qmc.statisticsconditions[3]))        
        self.minfinishedit = QLineEdit(aw.qmc.stringfromseconds(aw.qmc.statisticsconditions[4]))        
        self.maxfinishedit = QLineEdit(aw.qmc.stringfromseconds(aw.qmc.statisticsconditions[5]))
        
        self.mindryedit.setValidator(QRegExpValidator(regextime,self))
        self.maxdryedit.setValidator(QRegExpValidator(regextime,self))
        self.minmidedit.setValidator(QRegExpValidator(regextime,self))
        self.maxmidedit.setValidator(QRegExpValidator(regextime,self))
        self.minfinishedit.setValidator(QRegExpValidator(regextime,self))
        self.maxfinishedit.setValidator(QRegExpValidator(regextime,self))

        drylabel =QLabel("Dry phase:")
        midlabel =QLabel("Dry phase:")
        finishlabel =QLabel("Dry phase:")
        flavor = QLabel("Set Flavor Conditions")
        minf = QLabel("Min")
        maxf = QLabel("Max")

        if aw.qmc.statisticsflags[0]:
            self.time.setChecked(True)
        if aw.qmc.statisticsflags[1]:
            self.bar.setChecked(True)
        if aw.qmc.statisticsflags[2]:
            self.flavor.setChecked(True)
        if aw.qmc.statisticsflags[3]:
            self.area.setChecked(True)

        okButton = QPushButton("OK")
        cancelButton = QPushButton("Cancel")
        resetButton = QPushButton("Reset to Default")
        self.connect(okButton, SIGNAL("clicked()"),self, SLOT("accept()"))
        self.connect(cancelButton, SIGNAL("clicked()"),self, SLOT("reject()"))   
        self.connect(resetButton, SIGNAL("clicked()"),self.initialsettings)   
        
        layout = QGridLayout()
        layout.addWidget(self.time,0,0)
        layout.addWidget(self.bar,0,1)
        layout.addWidget(self.flavor,1,0)
        layout.addWidget(self.area,1,1)

        layout.addWidget(flavor,2,0)
        layout.addWidget(minf,2,1)
        layout.addWidget(maxf,2,2)
        

        layout.addWidget(drylabel,3,0)
        layout.addWidget(self.mindryedit,3,1)
        layout.addWidget(self.maxdryedit,3,2)
        layout.addWidget(midlabel,4,0)
        layout.addWidget(self.minmidedit,4,1)
        layout.addWidget(self.maxmidedit,4,2)
        layout.addWidget(finishlabel,5,0)
        layout.addWidget(self.minfinishedit,5,1)
        layout.addWidget(self.maxfinishedit,5,2)
        
        layout.addWidget(resetButton,6,0)
        layout.addWidget(cancelButton,6,1)
        layout.addWidget(okButton,6,2)
        
        self.setLayout(layout)        

    def initialsettings(self):
        aw.qmc.statisticsconditions = [180,360,180,600,180,360]        
        self.close()
        aw.showstatisticsdlg()

    def accept(self):

        mindry = aw.qmc.stringtoseconds(unicode(self.mindryedit.text()))
        maxdry = aw.qmc.stringtoseconds(unicode(self.maxdryedit.text()))
        minmid = aw.qmc.stringtoseconds(unicode(self.minmidedit.text()))
        maxmid = aw.qmc.stringtoseconds(unicode(self.maxmidedit.text()))
        minfinish = aw.qmc.stringtoseconds(unicode(self.minfinishedit.text()))
        maxfinish = aw.qmc.stringtoseconds(unicode(self.maxfinishedit.text()))

        if mindry != -1 and maxdry != -1 and minmid != -1 and maxmid != -1 and minfinish != -1 and maxfinish != -1:
            aw.qmc.statisticsconditions[0] = mindry
            aw.qmc.statisticsconditions[1] = maxdry
            aw.qmc.statisticsconditions[2] = minmid
            aw.qmc.statisticsconditions[3] = maxmid
            aw.qmc.statisticsconditions[4] = minfinish
            aw.qmc.statisticsconditions[5] = maxfinish
            
            if self.time.isChecked(): 
                aw.qmc.statisticsflags[0] = 1
            else:
                aw.qmc.statisticsflags[0] = 0
                
            if self.bar.isChecked(): 
                aw.qmc.statisticsflags[1] = 1
            else:
                aw.qmc.statisticsflags[1] = 0
                
            if self.flavor.isChecked(): 
                aw.qmc.statisticsflags[2] = 1
            else:
                aw.qmc.statisticsflags[2] = 0
                
            if self.area.isChecked(): 
                aw.qmc.statisticsflags[3] = 1
            else:
                aw.qmc.statisticsflags[3] = 0

            aw.qmc.redraw()
            self.close()
        else:
            pass
                

###########################################################################################
##################### SERIAL PORT #########################################################
###########################################################################################
        
        
class serialport(object):
    """ this class handles the communications with all the devices"""
    
    def __init__(self):
        #default initial settings. They are changed by settingsload() at initiation of program
        self.comport = "COM4"
        self.baudrate = 9600
        self.bytesize = 8
        self.parity= 'O'
        self.stopbits = 1
        self.timeout=1

        #stores the id of the meter HH506RA as a string
        self.HH506RAid = "X"

        #select PID type that controls the roaster. 
        self.controlETpid = [0,1]        # [ 0 = FujiPXG 1= FujiPXR3, second number is unitID] Can be changed in PID menu. Reads/Controls ET
        self.readBTpid = [1,2]           # [ 0 = FujiPXG 1= FujiPXR3, second number is unitID] Can be changed in PID menu. Reads BT

        #initial message flag for CENTER 309 meter
        self.CENTER309flag = 0


    # function used by Fuji PIDs
    def sendFUJIcommand(self,binstring,nbytes):
        serTX = None
        try:
            serTX = serial.Serial(self.comport,baudrate = self.baudrate, bytesize = self.bytesize,
                                parity = self.parity, stopbits = self.stopbits, timeout=self.timeout)
            serTX.write(binstring)
            r = serTX.read(nbytes)
            serTX.close()
            lenstring = len(r)
            if lenstring:
                # CHECK FOR RECEIVED ERROR CODES
                if ord(r[1]) == 128:
                        if ord(r[2]) == 1:
                             errorcode = u" F80h, ERROR 1: A nonexistent function code was specified. Please check the function code. "
                             aw.messagelabel.setText(u"sendFUJIcommand(): ERROR 1 Illegal Function in unit %i" %ord(command[0]))
                             aw.qmc.errorlog.append(errorcode)
                        if ord(r[2]) == 2:
                             errorcode = u"F80h, ERROR 2: Faulty address for coil or resistor: The specified relative address for the coil number or resistor\n \
                                         number cannot be used by the specified function code."
                             aw.messagelabel.setText(u"sendFUJIcommand() ERROR 2 Illegal Address for unit %i"%(ord(command[0])))
                             aw.qmc.errorlog.append(errorcode)
                        if ord(r[2]) == 3:
                             errorcode = u"F80h, ERROR 3: Faulty coil or resistor number: The specified number is too large and specifies a range that does not contain\n \
                                          coil numbers or resistor numbers."
                             aw.messagelabel.setText(u"sendFUJIcommand(): ERROR 3 Illegal Data Value for unit %i"%(ord(command[0])))
                             aw.qmc.errorlog.append(errorcode)
                else:
                    #Check crc16
                    crcRx =  int(binascii.hexlify(r[-1]+r[-2]),16)
                    crcCal1 = aw.pid.fujiCrc16(r[:-2]) 
                    if crcCal1 == crcRx:  
                        return r           #OK. Return r after it has been checked for errors
                    else:
                        aw.messagelabel.setText(u"Crc16 data corruption ERROR. TX does not match RX. Check wiring")
                        aw.qmc.errorlog.append(u"Crc16 data corruption ERROR. TX does not match RX. Check wiring ")
                        return u"0"

            else:
                aw.messagelabel.setText(u"No RX data received")
                return u"0"                  #return "0" if something went wrong


        except serial.SerialException,e:
            aw.messagelabel.setText(u"ser.sendFUJIcommand(): Error in serial port" + unicode(e))
            aw.qmc.errorlog.append(u"ser.sendFUJIcommand): Error in serial port " + unicode(e))
            return u"0"
        
        finally:
            if serTX:
                serTX.close()


    #t2 and t1 from Omega HH806 meter 
    def HH806AUtemperature(self):
        serHH = None
        try:
            serHH = serial.Serial(self.comport, baudrate=self.baudrate, bytesize = self.bytesize, parity=self.parity,
                                stopbits = self.stopbits, timeout = self.timeout)
            
            command = "#0A0000NA2\r\n" 
            serHH.write(command)
            r = serHH.read(14) 
            serHH.close()

            if len(r) == 14:
                #convert to binary to hex string
                s1 = binascii.hexlify(r[5] + r[6])
                s2 = binascii.hexlify(r[10]+ r[11])

                #we convert the strings to integers. Divide by 10.0 (decimal position)
                t1 = int(s1,16)/10. 
                t2 = int(s2,16)/10. 

                return t1, t2
            else:
                aw.messagelabel.setText(u"No RX data from HH806AUtemperature()")
                aw.qmc.errorlog.append(u"No RX data from HH806AUtemperature() ")
                if len(aw.qmc.timex) > 2:
                    return aw.qmc.temp1[-1], aw.qmc.temp2[-1]
                else:
                    return -1,-1
        except serial.SerialException, e:
            aw.messagelabel.setText(u"ser.HH806AUtemperature(): " + unicode(e))
            aw.qmc.errorlog.append(u"ser.HH806AUtemperature(): " + unicode(e) )
            return -1,-1
        finally:
            if serHH:
                serHH.close()


    #HH506RA Device
    #returns t1,t2 from Omega HH506 meter. By Marko Luther
    def HH506RAtemperature(self):
        #if initial id "X" has not changed then get a new one;
        if self.HH506RAid == "X":                                         
            self.HH506RAGetID()                       # obtain new id one time; self.HH506RAid should not be "X" any more
            if self.HH506RAid == "X":                 # if self.HH506RAGetID() went wrong and self.HH506RAid is still "X" 
                aw.messagelabel.setText(u"unable to get id from HH506RA device")
                aw.qmc.errorlog.append(u"unable to get id from HH506RA device")
                return -1,-1
           
        serHH = None
        try:
            serHH = serial.Serial(self.comport, baudrate=self.baudrate, bytesize = self.bytesize, parity= self.parity,
                                  stopbits = self.stopbits, timeout = self.timeout)
            
            command = "#" + self.HH506RAid + "N\r\n"
            serHH.write(command)
            r = serHH.read(14)
            serHH.close()

            if len(r) == 14: 
                #we convert the hex strings to integers. Divide by 10.0 (decimal position)
                t1 = int(r[1:5],16)/10.
                t2 = int(r[7:11],16)/10.
                # return -1 for probes not connected with output outside of range: -50 to 800F
                if t1 < -50 or t1 > 800:
                    t1 = -1
                if t2 < -50 or t2 > 800:
                    t2 = -1
                return t1,t2
            
            else:
                aw.messagelabel.setText(u"No RX data from HH506RAtemperature()")
                aw.qmc.errorlog.append(u"No RX data from HH506RAtemperature()")
                
                if len(aw.qmc.timex) > 2:                           #if there are at least two completed readings
                    return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       # then new reading = last reading (avoid possible single errors) 
                else:
                    return -1,-1                                    #return something out of scope to avoid function error (expects two values)
        
        except serial.SerialException, e:
            aw.messagelabel.setText(u"ser.HH506RAtemperature(): " + unicode(e))
            aw.qmc.errorlog.append(u"ser.HH506RAtemperature(): " + unicode(e) )
            return -1,-1
        
        finally:
            if serHH:
                serHH.close()

            
    #reads once the id of the HH506RA meter and stores it in the serial variable self.HH506RAid. Marko Luther.
    def HH506RAGetID(self):
        serHH = None
        try:
            serHH = serial.Serial(self.comport, baudrate=self.baudrate, bytesize = self.bytesize, parity=self.parity,
                                stopbits=self.stopbits, timeout=self.timeout)                
            sync = None
            while sync != "Err\r\n":
                serHH.write("\r\n")
                sync = serHH.read(5)
                time.sleep(1)
                
            serHH.write("%000R")
            ID = serHH.read(5)
            if len(ID) == 5:
                self.HH506RAid =  ID[0:3]               # Assign new id to self.HH506RAid
            serHH.close()
        
        except serial.SerialException, e:
            aw.messagelabel.setText(u"ser.HH506RAGetID()" + unicode(e))
            aw.qmc.errorlog.append(u"ser.HH506RAGetID()" + unicode(e) )
            
        finally:
            if serHH:
                serHH.close()        


    def CENTER306temperature(self):
        serCENTER = None
        try:
            serCENTER = serial.Serial(self.comport, baudrate=self.baudrate, bytesize = self.bytesize, parity=self.parity,
                                    stopbits=self.stopbits, timeout=self.timeout)
            command = "\x41"                 
            serCENTER.write(command)
            r = serCENTER.read(10)                                  #NOTE: different
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
                nbytes = len(r)
                message = u"%i bytes received but 10 needed"%nbytes
                aw.messagelabel.setText(message)
                aw.qmc.errorlog.append(message)
                
                if len(aw.qmc.timex) > 2:                           #if there are at least two completed readings
                    return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       # then new reading = last reading (avoid possible single errors) 
                else:
                    return -1,-1                                    #return something out of scope to avoid function error (expects two values)

            
        
        except serial.SerialException, e:
            aw.messagelabel.setText(u"ser.CENTER306temperature()" + unicode(e))
            aw.qmc.errorlog.append(u"ser.CENTER306temperature()" + unicode(e) )
            return -1,-1
            
        finally:
            if serCENTER:
                serCENTER.close()

                
    def CENTER303temperature(self):
        serCENTER = None
        try:
            serCENTER = serial.Serial(self.comport, baudrate=self.baudrate, bytesize = self.bytesize, parity=self.parity,
                                    stopbits=self.stopbits, timeout=self.timeout)
            command = "\x41"                 
            serCENTER.write(command)
            r = serCENTER.read(8)                                   #NOTE: different
            serCENTER.close()
            
            if len(r) == 8:

                #DECIMAL POINT
                #if bit 2 of byte 3 = 1 then T1 = ####      (don't divide by 10)
                #if bit 2 of byte 3 = 0 then T1 = ###.#     ( / by 10)
                #if bit 5 of byte 3 = 1 then T2 = ####
                #if bit 5 of byte 3 = 0 then T2 = ###.#
                
                #extract bit 2, and bit 5 of BYTE 3
                b3bin = bin(ord(r[2]))[2:]              #bit"[7][6][5][4][3][2][1][0]"
                bit2 = b3bin[5]
                bit5 = b3bin[2]
                
                #extract T1
                B34 = binascii.hexlify(r[3]+r[4])
                if B34[0].isdigit():
                    T1 = float(B34)
                else:
                    T1 = float(B34[1:])
                    
                #extract T2
                B56 = binascii.hexlify(r[5]+r[6])
                if B56[0].isdigit():
                    T2 = float(B56)
                else:
                    T2 = float(B56[1:])

                #check decimal point
                if bit2 == "0":
                    T1 /= 10.
                if bit5 == "0":
                    T2 /= 10.

                return T1,T2

            else:
                nbytes = len(r)
                message = u"%i bytes received but 8 needed"%nbytes
                aw.messagelabel.setText(message)
                aw.qmc.errorlog.append(message)
                
                if len(aw.qmc.timex) > 2:                           #if there are at least two completed readings
                    return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       # then new reading = last reading (avoid possible single errors) 
                else:
                    return -1,-1                                    #return something out of scope to avoid function error (expects two values)
        
        except serial.SerialException, e:
            aw.messagelabel.setText(u"ser.CENTER303temperature()" + unicode(e))
            aw.qmc.errorlog.append(u"ser.CENTER303temperature()" + unicode(e) )
            return -1,-1
            
        finally:
            if serCENTER:
                serCENTER.close()
                
    def CENTER309temperature(self):  
        ##    command = "\x4B" returns 4 bytes . Model number.
        ##    command = "\x48" simulates HOLD button
        ##    command = "\x4D" simulates MAX/MIN button
        ##    command = "\x4E" simulates EXIT MAX/MIN button
        ##    command = "\x52" simulates TIME button
        ##    command = "\x43" simulates C/F button
        ##    command = "\x55" dump all memmory
        ##    command = "\x50" Load recorded data
        ##    command = "\x41" returns 45 bytes (8x5 + 5 = 45) as follows:
        ##    
        ##    "\x02\x80\xUU\xUU\xUU\xUU\xUU\xAA"  \x80 means "Celsi" (if \x00 then "Faren") UUs unknown
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
                
        serCENTER = None
        try:
            serCENTER = serial.Serial(self.comport, baudrate=self.baudrate, bytesize = self.bytesize, parity=self.parity,
                                    stopbits=self.stopbits, timeout=self.timeout)
            command = "\x41"                 
            serCENTER.write(command)
            r = serCENTER.read(45)
            serCENTER.close()
            
            if len(r) == 45:
                
                #check r[43]: Only allow T1 & T2 when two thermocouples are connected
                #Allow to plot when any other single thermocouple is connected

                Tcheck = int(binascii.hexlify(r[43]),16)
                if Tcheck != 12:
                    if Tcheck == 14:
                        if not self.CENTER309flag:
                            aw.messagelabel.setText(u"CENTER 309 connected: T1")
                            self.CENTER309flag = 1
                        T1 = int(binascii.hexlify(r[7] + r[8]),16)
                        T2 = 0.
                    elif Tcheck == 13:
                        if not self.CENTER309flag:
                            aw.messagelabel.setText(u"CENTER 309 connected: T2")
                            self.CENTER309flag = 1
                        T1 = 0.
                        T2 = int(binascii.hexlify(r[9] + r[10]),16)
                    elif Tcheck == 11:
                        if not self.CENTER309flag:
                            aw.messagelabel.setText(u"CENTER 309 connected: T3")
                            self.CENTER309flag = 1
                        T1 = 0.
                        T2 = int(binascii.hexlify(r[11] + r[12]),16)
                    elif Tcheck == 7:
                        if not self.CENTER309flag:
                            print 
                            aw.messagelabel.setText(u"CENTER 309 connected: T4")
                            self.CENTER309flag = 1
                        T1 = 0.
                        T2 = int(binascii.hexlify(r[13] + r[14]),16)
                    else:
                        aw.messagelabel.setText(u"Connections allowed: T1&T2, or T1, or T2, or T3, or T4")
                        T1 = 0.
                        T2 = 0.
                else:
                    if not self.CENTER309flag:
                        aw.messagelabel.setText(u"CENTER 309 connected: T1 & T2")
                        self.CENTER309flag = 1
                        
                    T1 = int(binascii.hexlify(r[7] + r[8]),16)
                    T2 = int(binascii.hexlify(r[9] + r[10]),16)
                    
                return T1/10.,T2/10.
            
            else:
                nbytes = len(r)
                message = u"%i bytes from CENTER309 but 45 needed"%nbytes
                aw.messagelabel.setText(message)
                aw.qmc.errorlog.append(message)
                
                if len(aw.qmc.timex) > 2:                           #if there are at least two completed readings
                    return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       # then new reading = last reading (avoid possible single errors) 
                else:
                    return -1,-1                                    #return something out of scope to avoid function error (expects two values)
        
        
        except serial.SerialException, e:
            aw.messagelabel.setText(u"ser.CENTER309temperature()" + unicode(e))
            aw.qmc.errorlog.append(u"ser.CENTER309temperature()" + unicode(e) )
            return -1,-1
            
        finally:
            if serCENTER:
                serCENTER.close()



#########################################################################
#############  SERIAL PORT DIALOG #######################################                                   
#########################################################################

            
class comportDlg(QDialog):
    def __init__(self, parent = None):
        super(comportDlg,self).__init__(parent)

        comportlabel =QLabel("&Comm Port:")
        self.comportEdit = QComboBox()
        self.comportEdit.addItems([aw.ser.comport])
        self.comportEdit.setEditable(True)
        comportlabel.setBuddy(self.comportEdit)
        
        baudratelabel = QLabel("&Baud Rate:")
        self.baudrateComboBox = QComboBox()
        baudratelabel.setBuddy(self.baudrateComboBox)
        self.baudrateComboBox.addItems(["2400","9600","19200"])
        if aw.ser.baudrate == 2400:
            self.baudrateComboBox.setCurrentIndex(0)
        elif aw.ser.baudrate == 9600:
            self.baudrateComboBox.setCurrentIndex(1)     
        elif aw.ser.baudrate == 19200:
            self.baudrateComboBox.setCurrentIndex(2)
        else:
            pass
                   
        bytesizelabel = QLabel("&Byte Size:")
        self.bytesizeComboBox = QComboBox()
        bytesizelabel.setBuddy(self.bytesizeComboBox)
        self.bytesizeComboBox.addItems(["8","7"])
        if aw.ser.bytesize == 8:
            self.bytesizeComboBox.setCurrentIndex(0)
        elif aw.ser.bytesize == 7:
            self.bytesizeComboBox.setCurrentIndex(1)
        else:
            pass

        paritylabel = QLabel("&Parity:")
        self.parityComboBox = QComboBox()
        paritylabel.setBuddy(self.parityComboBox)
        self.parityComboBox.addItems(["O","E","N"])
        if aw.ser.parity == "O":
            self.parityComboBox.setCurrentIndex(0)
        elif aw.ser.parity == "E":
            self.parityComboBox.setCurrentIndex(1)
        elif aw.ser.parity == "N":
            self.parityComboBox.setCurrentIndex(2)
        else:
            pass

        
        stopbitslabel = QLabel("&Stopbits:")
        self.stopbitsComboBox = QComboBox()
        stopbitslabel.setBuddy(self.stopbitsComboBox)
        self.stopbitsComboBox.addItems(["1","0","2"])
        if aw.ser.stopbits == 1:
            self.stopbitsComboBox.setCurrentIndex(0)
        elif aw.ser.stopbits == 0:
            self.stopbitsComboBox.setCurrentIndex(1)
        elif aw.ser.stopbits == 2:
            self.stopbitsComboBox.setCurrentIndex(2)
        else:
            pass
        
        timeoutlabel = QLabel("Timeout:")
        self.timeoutEdit = QLineEdit(str(aw.ser.timeout))
        regex = QRegExp(r"^[0-9]$")
        self.timeoutEdit.setValidator(QRegExpValidator(regex,self))

        self.messagelabel = QLabel()
        
        okButton = QPushButton("&OK")
        cancelButton = QPushButton("Cancel")
        scanButton = QPushButton("Scan for Ports")
        
        buttonLayout = QGridLayout()
        buttonLayout.addWidget(scanButton,0,0)
        buttonLayout.addWidget(okButton,1,0)
        buttonLayout.addWidget(cancelButton,1,1)


        grid = QGridLayout()
        grid.addWidget(comportlabel,0,0)
        grid.addWidget(self.comportEdit,0,1)
        grid.addWidget(baudratelabel,1,0)
        grid.addWidget(self.baudrateComboBox,1,1)
        grid.addWidget(bytesizelabel,2,0)
        grid.addWidget(self.bytesizeComboBox,2,1)
        grid.addWidget(paritylabel,3,0)
        grid.addWidget(self.parityComboBox,3,1)
        grid.addWidget(stopbitslabel,4,0)
        grid.addWidget(self.stopbitsComboBox,4,1)
        grid.addWidget(timeoutlabel,5,0)
        grid.addWidget(self.timeoutEdit,5,1)
        grid.addWidget(self.messagelabel,6,1)
        
        grid.addLayout(buttonLayout,7,1)
        self.setLayout(grid)

        self.connect(okButton, SIGNAL("clicked()"),self, SLOT("accept()"))
        self.connect(cancelButton, SIGNAL("clicked()"),self, SLOT("reject()"))
        self.connect(scanButton, SIGNAL("clicked()"), self.scanforport)
        self.setWindowTitle("Serial Communication Configuration")

    def accept(self):
        #validate serial parameter against input errors
        class comportError(Exception): pass
        class baudrateError(Exception): pass
        class bytesizeError(Exception): pass
        class parityError(Exception): pass
        class stopbitsError(Exception): pass
        class timeoutError(Exception): pass
        
        comport = unicode(self.comportEdit.currentText())
        baudrate = unicode(self.baudrateComboBox.currentText())
        bytesize = unicode(self.bytesizeComboBox.currentText())
        parity = unicode(self.parityComboBox.currentText())
        stopbits = unicode(self.stopbitsComboBox.currentText())
        timeout = unicode(self.timeoutEdit.text())
        
        try:
            #check here comport errors
            if not comport:
                raise comportError
            if not timeout:
                raise timeoutError
            #add more checks here
            
        except comportError,e:
            aw.qmc.errorlog.append(u"Invalid serial Comm entry " + unicode(e))
            self.messagelabel.setText(u"Invalid Comm entry")
            self.comportEdit.selectAll()
            self.comportEdit.setFocus()           
            return

        except timeoutError,e:
            aw.qmc.errorlog.append(u"Invalid serial Timeout entry" + unicode(e))
            self.messagelabel.setText(u"Invalid Timeout entry")
            self.timeoutEdit.selectAll()
            self.timeoutEdit.setFocus()           
            return
        
        QDialog.accept(self)


    def scanforport(self):
        available = []      
        if platf in ('Windows', 'Microsoft'):
            #scans serial ports in Windows computer
            for i in range(100):
                try:
                    s = serial.Serial(i)
                    available.append(s.portstr)
                    s.close()  
                except serial.SerialException,e:
                    aw.qmc.errorlog.append(u"Exception during port scan:" + unicode(e)) 
                
        elif platf == 'Darwin':
            #scans serial ports in Mac computer
            results={}
            for name in glob.glob("/dev/cu.*"):
                if name.upper().rfind("MODEM") < 0:
                    try:
                        with file(name, 'rw'):
                            available.append(name)
                    except Exception, e:
                        pass
                    
        elif platf == 'Linux':
            maxnum=9
            for prefix, description, klass in ( 
                ("/dev/cua", "Standard serial port", "serial"), 
                ("/dev/ttyUSB", "USB to serial convertor", "serial"),
                ("/dev/usb/ttyUSB", "USB to serial convertor", "serial"), 
                ("/dev/usb/tts/", "USB to serial convertor", "serial")
                ):
                for num in range(maxnum+1):
                    name=prefix+`num`
                    if not os.path.exists(name):
                        continue
                    try:
                        with file(name, 'rw'):
                            available.append(name)
                    except Exception, e:
                        pass
        else:
            self.messagelabel.setText("Port scan on this platform not yet supported")
                                
        self.comportEdit.clear()              
        self.comportEdit.addItems(available)
        if len(available) > 1:
            self.comportEdit.setCurrentIndex(1)


#################################################################################            
##################   Device assignments DIALOG for reading temperature   ########
#################################################################################
                
class DeviceAssignmentDLG(QDialog):       
    def __init__(self, parent = None):
        super(DeviceAssignmentDLG,self).__init__(parent)

        self.nonpidButton = QRadioButton("Device")
        self.pidButton = QRadioButton("PID")

        self.devicetypeComboBox = QComboBox()
        self.devicetypeComboBox.addItems(["Omega HH806AU",
                                          "Omega HH506RA",
                                          "CENTER 309",
                                          "CENTER 306",
                                          "CENTER 305",
                                          "CENTER 304",
                                          "CENTER 303",
                                          "CENTER 302",
                                          "CENTER 301",
                                          "CENTER 300",
                                          "VOLTCRAFT K204",
                                          "VOLTCRAFT K202",
                                          "VOLTCRAFT 300K",
                                          "VOLTCRAFT 302KJ",
                                          "EXTECH 421509"
                                          ])
        
        controllabel =QLabel("Control PID for ET:")                            
        self.controlpidtypeComboBox = QComboBox()
        self.controlpidunitidComboBox = QComboBox()
        self.controlpidtypeComboBox.addItems(["Fuji PXG","Fuji PXR"])
        self.controlpidunitidComboBox.addItems(["1","2"])

        label1 = QLabel("PID type") 
        label2 = QLabel("Unit ID number")

        btlabel =QLabel("PID to read BT:")                            
        self.btpidtypeComboBox = QComboBox()
        self.btpidunitidComboBox = QComboBox()
        self.btpidtypeComboBox.addItems(["Fuji PXG","Fuji PXR"])
        self.btpidunitidComboBox.addItems(["2","1"])

        #check previous pid settings for radio button
        if aw.qmc.device == 0:
            self.pidButton.setChecked(True)
            
        else:
            self.nonpidButton.setChecked(True)
            self.devicetypeComboBox.setCurrentIndex(aw.qmc.device - 1)            
                
        if aw.ser.controlETpid[0] == 0 :       # control is PXG4
            self.controlpidtypeComboBox.setCurrentIndex(0)
        else:
            self.controlpidtypeComboBox.setCurrentIndex(1)
        if aw.ser.readBTpid[0] == 0:
            self.btpidtypeComboBox.setCurrentIndex(0)
        else:
            self.btpidtypeComboBox.setCurrentIndex(1)
        if aw.ser.controlETpid[1] == 1 :       # control is PXG4
            self.controlpidunitidComboBox.setCurrentIndex(0)
        else:
            self.controlpidunitidComboBox.setCurrentIndex(1)
        if aw.ser.readBTpid[1] == 1:
            self.btpidunitidComboBox.setCurrentIndex(1)
        else:
            self.btpidunitidComboBox.setCurrentIndex(0)
                

        okButton = QPushButton("OK")
        cancelButton = QPushButton("Cancel")
        self.connect(okButton, SIGNAL("clicked()"),self, SLOT("accept()"))
        self.connect(cancelButton, SIGNAL("clicked()"),self, SLOT("reject()"))        

        self.setWindowTitle("Device Assignment")
        
        grid = QGridLayout()

        grid.addWidget(self.nonpidButton,0,0)
        grid.addWidget(self.devicetypeComboBox,0,1)
        
        grid.addWidget(self.pidButton,2,0)
        
        grid.addWidget(label1,3,1)
        grid.addWidget(label2,3,2)
        grid.addWidget(controllabel,4,0)
        grid.addWidget(self.controlpidtypeComboBox,4,1)
        grid.addWidget(self.controlpidunitidComboBox,4,2)
                                   
        grid.addWidget(btlabel,5,0)
        grid.addWidget(self.btpidtypeComboBox,5,1)
        grid.addWidget(self.btpidunitidComboBox,5,2)

        grid.addWidget(okButton,6,2)
        grid.addWidget(cancelButton,6,1)
        
        self.setLayout(grid)



    def accept(self):
        message = "Device left empty"
        if self.pidButton.isChecked():
            # 0 = PXG, 1 = PXR
            if str(self.controlpidtypeComboBox.currentText()) == "Fuji PXG":
                aw.ser.controlETpid[0] = 0
                str1 = "Fuji PXG"
                
            elif str(self.controlpidtypeComboBox.currentText()) == "Fuji PXR":
                aw.ser.controlETpid[0] = 1
                str1 = "Fuji PXR"
                
            aw.ser.controlETpid[1] =  int(str(self.controlpidunitidComboBox.currentText()))

            if str(self.btpidtypeComboBox.currentText()) == "Fuji PXG":
                aw.ser.readBTpid[0] = 0
                str2 = "Fuji PXG"
            elif str(self.btpidtypeComboBox.currentText()) == "Fuji PXR":
                aw.ser.readBTpid[0] = 1
                str2 = "Fuji PXR"
            aw.ser.readBTpid[1] =  int(str(self.btpidunitidComboBox.currentText()))

            aw.qmc.device = 0
            self.comport = "COM4"
            self.baudrate = 9600
            self.bytesize = 8
            self.parity= 'O'
            self.stopbits = 1
            self.timeout=1

            message = "PID to control ET set to " + str1 + " " + str(aw.ser.controlETpid[1]) + \
            " ; PID to read BT set to " + str2 + " " + str(aw.ser.readBTpid[1])
            
            aw.button_10.setDisabled(False)
            aw.button_10.setFlat(False)
            
        if self.nonpidButton.isChecked():
            meter = str(self.devicetypeComboBox.currentText())
            message = "device err"
            if meter == "Omega HH806AU":
                aw.qmc.device = 1
                aw.ser.comport = "COM11"
                aw.ser.baudrate = 19200
                aw.ser.bytesize = 8
                aw.ser.parity= 'E'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to " + meter + ". Now, chose serial port"

            elif meter == "Omega HH506RA":
                aw.qmc.device = 2
                aw.ser.comport = "/dev/tty.usbserial-A2001Epn"
                aw.ser.baudrate = 2400
                aw.ser.bytesize = 7
                aw.ser.parity= 'E'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to " + meter + ". Now, chose serial port"
                
            elif meter == "CENTER 309":
                aw.qmc.device = 3
                aw.ser.comport = "COM4"
                aw.ser.baudrate = 9600
                aw.ser.bytesize = 8
                aw.ser.parity= 'N'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to " + meter + ". Now, chose serial port"

            elif meter == "CENTER 306":
                aw.qmc.device = 4
                aw.ser.comport = "COM4"
                aw.ser.baudrate = 9600
                aw.ser.bytesize = 8
                aw.ser.parity= 'N'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to " + meter + ". Now, chose serial port"

            elif meter == "CENTER 305":
                aw.qmc.device = 5
                aw.ser.comport = "COM4"
                aw.ser.baudrate = 9600
                aw.ser.bytesize = 8
                aw.ser.parity= 'N'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to CENTER 305, which is equivalent to CENTER 306. Now, chose serial port"
                
            elif meter == "CENTER 304":
                aw.qmc.device = 6
                aw.ser.comport = "COM4"
                aw.ser.baudrate = 9600
                aw.ser.bytesize = 8
                aw.ser.parity= 'N'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to CENTER 304, which is equivalent to CENTER 309. Now, chose serial port"

            elif meter == "CENTER 303":
                aw.qmc.device = 7
                aw.ser.comport = "COM4"
                aw.ser.baudrate = 9600
                aw.ser.bytesize = 8
                aw.ser.parity= 'N'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to CENTER 303. Now, chose serial port"

            elif meter == "CENTER 302":
                aw.qmc.device = 8
                aw.ser.comport = "COM4"
                aw.ser.baudrate = 9600
                aw.ser.bytesize = 8
                aw.ser.parity= 'N'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to CENTER 302, which is equivalent to CENTER 303. Now, chose serial port"
                
            elif meter == "CENTER 301":
                aw.qmc.device = 9
                aw.ser.comport = "COM4"
                aw.ser.baudrate = 9600
                aw.ser.bytesize = 8
                aw.ser.parity= 'N'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to CENTER 301, which is equivalent to CENTER 303. Now, chose serial port"

            elif meter == "CENTER 300":
                aw.qmc.device = 10
                aw.ser.comport = "COM4"
                aw.ser.baudrate = 9600
                aw.ser.bytesize = 8
                aw.ser.parity= 'N'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to CENTER 300, which is equivalent to CENTER 303. Now, chose serial port"
                
            elif meter == "VOLTCRAFT K204":
                aw.qmc.device = 11
                aw.ser.comport = "COM4"
                aw.ser.baudrate = 9600
                aw.ser.bytesize = 8
                aw.ser.parity= 'N'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to VOLTCRAFT K204, which is equivalent to CENTER 309. Now, chose serial port"

            elif meter == "VOLTCRAFT K202":
                aw.qmc.device = 12
                aw.ser.comport = "COM4"
                aw.ser.baudrate = 9600
                aw.ser.bytesize = 8
                aw.ser.parity= 'N'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to VOLTCRAFT K202, which is equivalent to CENTER 306. Now, chose serial port"

            elif meter == "VOLTCRAFT 300K":
                aw.qmc.device = 13
                aw.ser.comport = "COM4"
                aw.ser.baudrate = 9600
                aw.ser.bytesize = 8
                aw.ser.parity= 'N'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to VOLTCRAFT 300K, which is equivalent to CENTER 303. Now, chose serial port"

            elif meter == "VOLTCRAFT 302KJ":
                aw.qmc.device = 14
                aw.ser.comport = "COM4"
                aw.ser.baudrate = 9600
                aw.ser.bytesize = 8
                aw.ser.parity= 'N'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to VOLTCRAFT 302KJ, which is equivalent to CENTER 303. Now, chose serial port"

            elif meter == "EXTECH 421509":
                aw.qmc.device = 15
                aw.ser.comport = "/dev/tty.usbserial-A2001Epn"
                aw.ser.baudrate = 2400
                aw.ser.bytesize = 7
                aw.ser.parity= 'E'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = "Device set to EXTECH 421509, which is equivalent to Omega HH506RA. Now, chose serial port"

            aw.button_10.setDisabled(True)
            aw.button_10.setFlat(True)
                        
        aw.messagelabel.setText(message)
            
        self.close()

############################################################
#######################  CUSTOM COLOR DIALOG  ##############
############################################################

class graphColorDlg(QDialog):
    def __init__(self, parent = None):
        super(graphColorDlg,self).__init__(parent)
        self.setWindowTitle("Graph colors")
        frameStyle = QFrame.Sunken | QFrame.Panel

        self.backgroundLabel =QLabel(aw.qmc.palette["background"])
        self.backgroundLabel.setPalette(QPalette(QColor(aw.qmc.palette["background"])))
        self.backgroundLabel.setAutoFillBackground(True)
        self.backgroundButton = QPushButton("Background")
        self.backgroundLabel.setFrameStyle(frameStyle)
        self.connect(self.backgroundButton, SIGNAL("clicked()"), lambda var=self.backgroundLabel,color=aw.qmc.palette["background"]: self.setColor(var,color))

        
        self.gridLabel =QLabel(aw.qmc.palette["grid"])
        self.gridLabel.setPalette(QPalette(QColor(aw.qmc.palette["grid"])))
        self.gridLabel.setAutoFillBackground(True)
        self.gridButton = QPushButton("Grid")
        self.gridLabel.setFrameStyle(frameStyle)
        self.connect(self.gridButton, SIGNAL("clicked()"), lambda var=self.gridLabel, color= aw.qmc.palette["grid"]: self.setColor(var,color))


        self.titleLabel =QLabel(aw.qmc.palette["title"])
        self.titleLabel.setPalette(QPalette(QColor(aw.qmc.palette["title"])))
        self.titleLabel.setAutoFillBackground(True)
        self.titleButton = QPushButton("Title")
        self.titleLabel.setFrameStyle(frameStyle)
        self.connect(self.titleButton, SIGNAL("clicked()"), lambda var=self.titleLabel,color=aw.qmc.palette["title"]: self.setColor(var,color))
        
        
        self.yLabel =QLabel(aw.qmc.palette["ylabel"])
        self.yLabel.setPalette(QPalette(QColor(aw.qmc.palette["ylabel"])))
        self.yLabel.setAutoFillBackground(True)
        self.yButton = QPushButton("Y Label")
        self.yLabel.setFrameStyle(frameStyle)
        self.connect(self.yButton, SIGNAL("clicked()"), lambda var=self.yLabel,color=aw.qmc.palette["ylabel"]: self.setColor(var,color))

        
        self.xLabel =QLabel(aw.qmc.palette["xlabel"])
        self.xLabel.setPalette(QPalette(QColor(aw.qmc.palette["xlabel"])))
        self.xLabel.setAutoFillBackground(True)
        self.xButton = QPushButton("X Label")
        self.xLabel.setFrameStyle(frameStyle)
        self.connect(self.xButton, SIGNAL("clicked()"), lambda var=self.xLabel,color=aw.qmc.palette["xlabel"]: self.setColor(var,color))

        
        self.rect1Label =QLabel(aw.qmc.palette["rect1"])
        self.rect1Label.setPalette(QPalette(QColor(aw.qmc.palette["rect1"])))
        self.rect1Label.setAutoFillBackground(True)
        self.rect1Button = QPushButton("Dry phase")
        self.rect1Label.setFrameStyle(frameStyle)
        self.connect(self.rect1Button, SIGNAL("clicked()"), lambda var=self.rect1Label,color=aw.qmc.palette["rect1"]: self.setColor(var,color))

        
        self.rect2Label =QLabel(aw.qmc.palette["rect2"])
        self.rect2Label.setPalette(QPalette(QColor(aw.qmc.palette["rect2"])))
        self.rect2Label.setAutoFillBackground(True)
        self.rect2Button = QPushButton("Mid 1C phase")
        self.rect2Label.setFrameStyle(frameStyle)
        self.connect(self.rect2Button, SIGNAL("clicked()"), lambda var=self.rect2Label,color=aw.qmc.palette["rect2"]: self.setColor(var,color))

        
        self.rect3Label =QLabel(aw.qmc.palette["rect3"])
        self.rect3Label.setPalette(QPalette(QColor(aw.qmc.palette["rect3"])))
        self.rect3Label.setAutoFillBackground(True)
        self.rect3Button = QPushButton("Finish phase")
        self.rect3Label.setFrameStyle(frameStyle)
        self.connect(self.rect3Button, SIGNAL("clicked()"), lambda var=self.rect3Label,color=aw.qmc.palette["rect3"]: self.setColor(var,color))

        
        self.metLabel =QLabel(aw.qmc.palette["met"])
        self.metLabel.setPalette(QPalette(QColor(aw.qmc.palette["met"])))
        self.metLabel.setAutoFillBackground(True)
        self.metButton = QPushButton("MET")
        self.metLabel.setFrameStyle(frameStyle)
        self.connect(self.metButton, SIGNAL("clicked()"), lambda var=self.metLabel,color=aw.qmc.palette["met"]: self.setColor(var,color))

        
        self.btLabel =QLabel(aw.qmc.palette["bt"])
        self.btLabel.setPalette(QPalette(QColor(aw.qmc.palette["bt"])))
        self.btLabel.setAutoFillBackground(True)
        self.btButton = QPushButton("BT")
        self.btLabel.setFrameStyle(frameStyle)
        self.connect(self.btButton, SIGNAL("clicked()"), lambda var=self.btLabel,color=aw.qmc.palette["bt"]: self.setColor(var,color))

        
        self.deltametLabel =QLabel(aw.qmc.palette["deltamet"])
        self.deltametLabel.setPalette(QPalette(QColor(aw.qmc.palette["deltamet"])))
        self.deltametLabel.setAutoFillBackground(True)
        self.deltametButton = QPushButton("Delta MET")
        self.deltametLabel.setFrameStyle(frameStyle)
        self.connect(self.deltametButton, SIGNAL("clicked()"), lambda var=self.deltametLabel,color=aw.qmc.palette["deltamet"]: self.setColor(var,color))

        
        self.deltabtLabel =QLabel(aw.qmc.palette["deltabt"])
        self.deltabtLabel.setPalette(QPalette(QColor(aw.qmc.palette["deltabt"])))
        self.deltabtLabel.setAutoFillBackground(True)
        self.deltabtButton = QPushButton("Delta BT")
        self.deltabtLabel.setFrameStyle(frameStyle)
        self.connect(self.deltabtButton, SIGNAL("clicked()"), lambda var=self.deltabtLabel,color=aw.qmc.palette["deltabt"]: self.setColor(var,color))

        
        self.markersLabel =QLabel(aw.qmc.palette["markers"])
        self.markersLabel.setPalette(QPalette(QColor(aw.qmc.palette["markers"])))
        self.markersLabel.setAutoFillBackground(True)
        self.markersButton = QPushButton("Markers")
        self.markersLabel.setFrameStyle(frameStyle)
        self.connect(self.markersButton, SIGNAL("clicked()"), lambda var=self.markersLabel,color=aw.qmc.palette["markers"]: self.setColor(var,color))

        
        self.textLabel =QLabel(aw.qmc.palette["text"])
        self.textLabel.setPalette(QPalette(QColor(aw.qmc.palette["text"])))
        self.textLabel.setAutoFillBackground(True)
        self.textButton = QPushButton("Text")
        self.textLabel.setFrameStyle(frameStyle)
        self.connect(self.textButton, SIGNAL("clicked()"), lambda var=self.textLabel,color=aw.qmc.palette["text"]: self.setColor(var,color))

        self.watermarksLabel =QLabel(aw.qmc.palette["watermarks"])
        self.watermarksLabel.setPalette(QPalette(QColor(aw.qmc.palette["watermarks"])))
        self.watermarksLabel.setAutoFillBackground(True)
        self.watermarksButton = QPushButton("Watermarks")
        self.watermarksLabel.setFrameStyle(frameStyle)
        self.connect(self.watermarksButton, SIGNAL("clicked()"), lambda var=self.watermarksLabel,color=aw.qmc.palette["watermarks"]: self.setColor(var,color))
        
        self.ClineLabel =QLabel(aw.qmc.palette["Cline"])
        self.ClineLabel.setPalette(QPalette(QColor(aw.qmc.palette["Cline"])))
        self.ClineLabel.setAutoFillBackground(True)
        self.ClineButton = QPushButton("C lines")
        self.ClineLabel.setFrameStyle(frameStyle)
        self.connect(self.ClineButton, SIGNAL("clicked()"), lambda var=self.ClineLabel,color=aw.qmc.palette["Cline"]: self.setColor(var,colorbbb))

        okButton = QPushButton("Update Colors")
        self.connect(okButton, SIGNAL("clicked()"),self, SLOT("accept()"))        

        grid = QGridLayout()

        grid.addWidget(self.backgroundButton,0,0)                                          
        grid.addWidget(self.backgroundLabel,0,1)

        grid.addWidget(self.titleButton,1,0)        
        grid.addWidget(self.titleLabel,1,1)
        
        grid.addWidget(self.gridButton,2,0)
        grid.addWidget(self.gridLabel,2,1)                                          

        
        grid.addWidget(self.metButton,3,0)
        grid.addWidget(self.metLabel,3,1)
        
        grid.addWidget(self.btButton,4,0)
        grid.addWidget(self.btLabel,4,1)
        
        grid.addWidget(self.deltametButton,5,0)
        grid.addWidget(self.deltametLabel,5,1)
        
        grid.addWidget(self.deltabtButton,6,0)
        grid.addWidget(self.deltabtLabel,6,1)
        
        grid.addWidget(self.yButton,7,0)
        grid.addWidget(self.yLabel,7,1)
        
        grid.addWidget(self.xButton,8,0)
        grid.addWidget(self.xLabel,8,1)
        
        grid.addWidget(self.rect1Button,9,0)
        grid.addWidget(self.rect1Label,9,1)
        
        grid.addWidget(self.rect2Button,10,0)
        grid.addWidget(self.rect2Label,10,1)
        
        grid.addWidget(self.rect3Button,11,0)
        grid.addWidget(self.rect3Label,11,1)

        grid.addWidget(self.markersButton,12,0)
        grid.addWidget(self.markersLabel,12,1)
        
        grid.addWidget(self.textButton,13,0)
        grid.addWidget(self.textLabel,13,1)
        
        grid.addWidget(self.watermarksButton,14,0)
        grid.addWidget(self.watermarksLabel,14,1)
        
        grid.addWidget(self.ClineButton,15,0)
        grid.addWidget(self.ClineLabel,15,1)
        
        grid.addWidget(okButton,16,1)

        self.setLayout(grid)

                        
    def setColor(self,var,color):
        labelcolor = QColor(color)
        colorf = QColorDialog.getColor(labelcolor,self)
        if colorf.isValid(): 
            var.setText(colorf.name())
            var.setPalette(QPalette(colorf))
            var.setAutoFillBackground(True)
        else:
            aw.messagelabel.setText(str(color) + " " + str(labelcolor))


            

#########################################################################
######################## FUJI PXR CONTROL DIALOG  #######################
#########################################################################

class PXRpidDlgControl(QDialog):
    def __init__(self, parent = None):
        super(PXRpidDlgControl,self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.setWindowTitle("Fuji PXR PID control")

        #create Ramp Soak control button colums

        self.labelrs1 = QLabel()
        self.labelrs1.setMargin(10)
        self.labelrs1.setStyleSheet("background-color:'#CCCCCC';")
        self.labelrs1.setText( "<font color='white'><b>Ramp/Soak<br>(1-4)<\b></font>")
        self.labelrs1.setMaximumSize(90, 62)

        self.labelrs2 = QLabel()
        self.labelrs2.setMargin(10)
        self.labelrs2.setStyleSheet("background-color:'#CCCCCC';")
        self.labelrs2.setText( "<font color='white'><b>Ramp/Soak<br>(5-8)<\b></font>")
        self.labelrs2.setMaximumSize(90, 62)

        labelpattern = QLabel("Ramp/Soak Pattern")
        self.patternComboBox =  QComboBox()
        self.patternComboBox.addItems(["1-4","5-8","1-8"])

        self.status = QStatusBar()
        self.status.setSizeGripEnabled(False)
        self.status.showMessage("Ready",5000)

        self.label_rs1 =  QLabel()
        self.label_rs2 =  QLabel()
        self.label_rs3 =  QLabel()
        self.label_rs4 =  QLabel()
        self.label_rs5 =  QLabel()
        self.label_rs6 =  QLabel()
        self.label_rs7 =  QLabel()
        self.label_rs8 =  QLabel()

        self.paintlabels()
        
        #update button and exit button
        button_getall = QPushButton("Read Ra/So values")
        button_rson =  QPushButton("RampSoak ON")        
        button_rsoff =  QPushButton("RampSoak OFF")
        button_standbyON = QPushButton("PID OFF")
        button_standbyOFF = QPushButton("PID ON")
        button_exit = QPushButton("Close")

        self.connect(self.patternComboBox,SIGNAL("currentIndexChanged(int)"),self.paintlabels)
        self.connect(button_getall, SIGNAL("clicked()"), self.getallsegments)
        self.connect(button_rson, SIGNAL("clicked()"), lambda flag=1: self.setONOFFrampsoak(flag))
        self.connect(button_rsoff, SIGNAL("clicked()"), lambda flag=0: self.setONOFFrampsoak(flag))
        self.connect(button_standbyON, SIGNAL("clicked()"), lambda flag=1: self.setONOFFstandby(flag))
        self.connect(button_standbyOFF, SIGNAL("clicked()"), lambda flag=0: self.setONOFFstandby(flag))
        self.connect(button_exit, SIGNAL("clicked()"),self, SLOT("reject()"))

        #TAB 2
        tab2svbutton = QPushButton("Write SV")
        tab2cancelbutton = QPushButton("Cancel")
        tab2easyONsvbutton = QPushButton("Turn ON SV buttons")
        tab2easyONsvbutton.setStyleSheet("QPushButton { background-color: #ffaaff}")
        tab2easyOFFsvbutton = QPushButton("Turn OFF SV buttons")
        tab2easyOFFsvbutton.setStyleSheet("QPushButton { background-color: lightblue}")
        tab2getsvbutton = QPushButton("Read current SV value")
        self.readsvedit = QLineEdit()
        self.connect(tab2svbutton, SIGNAL("clicked()"),self.setsv)
        self.connect(tab2getsvbutton, SIGNAL("clicked()"),self.getsv)
        self.connect(tab2cancelbutton, SIGNAL("clicked()"),self, SLOT("reject()"))
        self.connect(tab2easyONsvbutton, SIGNAL("clicked()"), lambda flag=1: aw.pid.activateONOFFeasySV(flag))
        self.connect(tab2easyOFFsvbutton, SIGNAL("clicked()"), lambda flag=0: aw.pid.activateONOFFeasySV(flag))
        svwarning1 = QLabel("<CENTER><b>WARNING</b><br>Writing eeprom memory<br><u>Max life</u> 10,000 writes<br>"
                            "Infinite read life.</CENTER>")
        svwarning2 = QLabel("<CENTER><b>WARNING</b><br>After <u>writing</u> an adjustment,<br>never power down the pid<br>"
                            "for the nex 5 seconds <br>or the pid may never recover.<br>Read operations manual</CENTER>")
        self.svedit = QLineEdit()
        self.svedit.setValidator(QDoubleValidator(0., 999., 1, self.svedit))
        
        #TAB 3
        button_p = QPushButton("Set p")
        button_i = QPushButton("Set i")
        button_d = QPushButton("Set d")
        plabel =  QLabel("p")
        ilabel =  QLabel("i")
        dlabel =  QLabel("d")
        self.pedit = QLineEdit(str(aw.pid.PXR["p"][0]))
        self.iedit = QLineEdit(str(aw.pid.PXR["i"][0]))
        self.dedit = QLineEdit(str(aw.pid.PXR["d"][0]))
        self.pedit.setMaximumWidth(60)
        self.iedit.setMaximumWidth(60)
        self.dedit.setMaximumWidth(60)
        self.pedit.setValidator(QDoubleValidator(0., 999., 1, self.pedit))
        self.iedit.setValidator(QIntValidator(0, 3200, self.iedit))
        self.dedit.setValidator(QDoubleValidator(0., 999.0, 1, self.dedit))
        button_autotuneON = QPushButton("Autotune ON")
        button_autotuneOFF = QPushButton("Autotune OFF")
        button_readpid = QPushButton("Read PID values")
        tab3cancelbutton = QPushButton("Cancel")

        self.connect(button_autotuneON, SIGNAL("clicked()"), lambda flag=1: self.setONOFFautotune(flag))
        self.connect(button_autotuneOFF, SIGNAL("clicked()"), lambda flag=0: self.setONOFFautotune(flag))
        self.connect(button_p, SIGNAL("clicked()"), lambda var=u"p": self.setpid(var))
        self.connect(button_i, SIGNAL("clicked()"), lambda var=u"i": self.setpid(var))
        self.connect(button_d, SIGNAL("clicked()"), lambda var=u"d": self.setpid(var))
        self.connect(tab3cancelbutton, SIGNAL("clicked()"),self, SLOT("reject()"))
        self.connect(button_readpid, SIGNAL("clicked()"), self.getpid)
        
        #create layouts
        tab1layout = QVBoxLayout()
        buttonMasterLayout = QGridLayout()
        buttonRampSoakLayout1 = QVBoxLayout()
        buttonRampSoakLayout2 = QVBoxLayout()
        tab3layout = QGridLayout()
        tab2layout = QVBoxLayout()
        svlayout = QGridLayout()

        #place rs buttoms in RampSoakLayout1
        buttonRampSoakLayout1.addWidget(self.labelrs1,0)
        buttonRampSoakLayout1.addWidget(self.label_rs1,1)
        buttonRampSoakLayout1.addWidget(self.label_rs2,2)
        buttonRampSoakLayout1.addWidget(self.label_rs3,3)
        buttonRampSoakLayout1.addWidget(self.label_rs4,4)

        buttonRampSoakLayout2.addWidget(self.labelrs2,0)
        buttonRampSoakLayout2.addWidget(self.label_rs5,1)
        buttonRampSoakLayout2.addWidget(self.label_rs6,2)
        buttonRampSoakLayout2.addWidget(self.label_rs7,3)        
        buttonRampSoakLayout2.addWidget(self.label_rs8,4)

        buttonMasterLayout.addLayout(buttonRampSoakLayout1,0,0)
        buttonMasterLayout.addLayout(buttonRampSoakLayout2,0,1)
        buttonMasterLayout.addWidget(labelpattern,1,0)
        buttonMasterLayout.addWidget(self.patternComboBox,1,1)
        buttonMasterLayout.addWidget(button_rson,2,0)
        buttonMasterLayout.addWidget(button_rsoff,2,1)
        buttonMasterLayout.addWidget(button_autotuneOFF,3,1)
        buttonMasterLayout.addWidget(button_autotuneON,3,0)
        buttonMasterLayout.addWidget(button_standbyOFF,4,0)
        buttonMasterLayout.addWidget(button_standbyON,4,1)
        buttonMasterLayout.addWidget(button_getall,5,0)
        buttonMasterLayout.addWidget(button_exit,5,1)

        #tab 2
        svlayout.addWidget(svwarning2,0,0)
        svlayout.addWidget(svwarning1,0,1)
        svlayout.addWidget(self.readsvedit,1,0)
        svlayout.addWidget(tab2getsvbutton,1,1)        
        svlayout.addWidget(self.svedit,2,0)
        svlayout.addWidget(tab2svbutton,2,1)
        svlayout.addWidget(tab2easyONsvbutton,3,0)
        svlayout.addWidget(tab2easyOFFsvbutton,3,1)
        svlayout.addWidget(tab2cancelbutton,4,1)

        #tab 3
        tab3layout.addWidget(plabel,0,0)
        tab3layout.addWidget(self.pedit,0,1)
        tab3layout.addWidget(button_p,0,2)
        tab3layout.addWidget(ilabel,1,0)
        tab3layout.addWidget(self.iedit,1,1)
        tab3layout.addWidget(button_i,1,2)
        tab3layout.addWidget(dlabel,2,0)
        tab3layout.addWidget(self.dedit,2,1)
        tab3layout.addWidget(button_d,2,2)        
        tab3layout.addWidget(button_autotuneON,3,1)
        tab3layout.addWidget(button_autotuneOFF,3,2)
        tab3layout.addWidget(button_readpid,4,1)
        tab3layout.addWidget(tab3cancelbutton,4,2)
        

        ###################################        

        TabWidget = QTabWidget()
        
        C1Widget = QWidget()
        C1Widget.setLayout(buttonMasterLayout)
        TabWidget.addTab(C1Widget,"RS")
        
        C2Widget = QWidget()
        C2Widget.setLayout(svlayout)
        TabWidget.addTab(C2Widget,"SV")

        C3Widget = QWidget()
        C3Widget.setLayout(tab3layout)
        TabWidget.addTab(C3Widget,"pid")
        

        #incorporate layouts
        Mlayout = QVBoxLayout()
        Mlayout.addWidget(self.status,0)
        Mlayout.addWidget(TabWidget,1)
        self.setLayout(Mlayout)



    def paintlabels(self):
        
        str1 = u"T= " + unicode(aw.pid.PXR["segment1sv"][0]) + u"\nRamp " + unicode(aw.pid.PXR["segment1ramp"][0]) + u"\nSoak " + unicode(aw.pid.PXR["segment1soak"][0])
        str2 = u"T= " + unicode(aw.pid.PXR["segment2sv"][0]) + u"\nRamp " + unicode(aw.pid.PXR["segment2ramp"][0]) + u"\nSoak " + unicode(aw.pid.PXR["segment2soak"][0])
        str3 = u"T= " + unicode(aw.pid.PXR["segment3sv"][0]) + u"\nRamp " + unicode(aw.pid.PXR["segment3ramp"][0]) + u"\nSoak " + unicode(aw.pid.PXR["segment3soak"][0])
        str4 = u"T= " + unicode(aw.pid.PXR["segment4sv"][0]) + u"\nRamp " + unicode(aw.pid.PXR["segment4ramp"][0]) + u"\nSoak " + unicode(aw.pid.PXR["segment4soak"][0])
        str5 = u"T= " + unicode(aw.pid.PXR["segment5sv"][0]) + u"\nRamp " + unicode(aw.pid.PXR["segment5ramp"][0]) + u"\nSoak " + unicode(aw.pid.PXR["segment5soak"][0])
        str6 = u"T= " + unicode(aw.pid.PXR["segment6sv"][0]) + u"\nRamp " + unicode(aw.pid.PXR["segment6ramp"][0]) + u"\nSoak " + unicode(aw.pid.PXR["segment6soak"][0])
        str7 = u"T= " + unicode(aw.pid.PXR["segment7sv"][0]) + u"\nRamp " + unicode(aw.pid.PXR["segment7ramp"][0]) + u"\nSoak " + unicode(aw.pid.PXR["segment7soak"][0])
        str8 = u"T= " + unicode(aw.pid.PXR["segment8sv"][0]) + u"\nRamp " + unicode(aw.pid.PXR["segment8ramp"][0]) + u"\nSoak " + unicode(aw.pid.PXR["segment8soak"][0])

        self.label_rs1.setText(QString(str1))
        self.label_rs2.setText(QString(str2))
        self.label_rs3.setText(QString(str3))
        self.label_rs4.setText(QString(str4))
        self.label_rs5.setText(QString(str5))
        self.label_rs6.setText(QString(str6))
        self.label_rs7.setText(QString(str7))
        self.label_rs8.setText(QString(str8))

        pattern = [[1,1,1,1,0,0,0,0],
                  [0,0,0,0,1,1,1,1],
                  [1,1,1,1,1,1,1,1]]

        aw.pid.PXR["rampsoakpattern"][0] = self.patternComboBox.currentIndex()

        if pattern[aw.pid.PXR["rampsoakpattern"][0]][0]:   
            self.label_rs1.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs1.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXR["rampsoakpattern"][0]][1]:
            self.label_rs2.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs2.setStyleSheet("background-color:white;")
            
        if pattern[aw.pid.PXR["rampsoakpattern"][0]][2]:   
            self.label_rs3.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs3.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXR["rampsoakpattern"][0]][3]:   
            self.label_rs4.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs4.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXR["rampsoakpattern"][0]][4]:   
            self.label_rs5.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs5.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXR["rampsoakpattern"][0]][5]:   
            self.label_rs6.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs6.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXR["rampsoakpattern"][0]][6]:   
            self.label_rs7.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs7.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXR["rampsoakpattern"][0]][7]:   
            self.label_rs8.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs8.setStyleSheet("background-color:white;")

            
    def setONOFFautotune(self,flag):
        self.status.showMessage(u"setting autotune...",500)
        command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["autotuning"][1],flag)
        #TX and RX
        r = aw.ser.sendFUJIcommand(command,8)
        if len(r) == 8:
            if flag == 0:
                aw.pid.PXR["autotuning"][0] = 0
                self.status.showMessage(u"Autotune successfully turned OFF",5000)
            if flag == 1:
                aw.pid.PXR["autotuning"][0] = 1
                self.status.showMessage(u"Autotune successfully turned ON",5000) 
        else:
            mssg = u"setONOFFautotune() problem "
            self.status.showMessage(mssg,5000)
            aw.qmc.errorlog.append(mssg)
        
    def setONOFFstandby(self,flag):
        #standby ON (pid off) will reset: rampsoak modes/autotuning/self tuning
        #flag = 0 standby OFF, flag = 1 standby ON (pid off)
        self.status.showMessage(u"wait...",500)
        command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["runstandby"][1],flag)
        #TX and RX
        r = aw.ser.sendFUJIcommand(command,8)
        if r == command:               
            if flag == 1:
                message = u"PID OFF"     #put pid in standby 1 (pid on)
                aw.pid.PXR["runstandby"][0] = 1
            elif flag == 0:
                message = u"PID ON"      #put pid in standby 0 (pid off)
                aw.pid.PXR["runstandby"][0] = 0
        else:
            mssg = u"setONOFFstandby() problem "
            self.status.showMessage(mssg,5000)
            aw.qmc.errorlog.append(mssg)

    def setsv(self):
        if self.svedit.text() != "":
            newSVvalue = int(float(self.svedit.text())*10) #multiply by 10 because of decimal point
            command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["sv0"][1],newSVvalue)
            r = aw.ser.sendFUJIcommand(command,8)
            if r == command:
                message = u" SV successfully set to " + self.svedit.text()
                aw.pid.PXR["sv0"][0] = float(self.svedit.text())
                aw.lcd6.display(aw.pid.PXR["sv0"][0])
                self.status.showMessage(message,5000)
            else:
                mssg = u"setsv(): unable to set sv"
                self.status.showMessage(mssg,5000)
                aw.qmc.errorlog.append(mssg)                
        else:
            self.status.showMessage(u"Empty SV box",5000)

    def getsv(self):
        temp = aw.pid.readcurrentsv()
        if temp != -1:
            aw.pid.PXR["sv0"][0] =  temp
            aw.lcd6.display(aw.pid.PXR["sv0"][0])
            self.readsvedit.setText(unicode(aw.pid.PXR["sv0"][0]))
        else:
            self.status.showMessage(u"Unable to read SV",5000)

            
    def checkrampsoakmode(self):
        msg = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXR["rampsoakmode"][1],1)
        currentmode = aw.pid.readoneword(msg)
        aw.pid.PXR["rampsoakstartend"][0] = currentmode
        if currentmode == 0:
            mode = [u"0",u"OFF",u"CONTINUOUS CONTROL",u"CONTINUOUS CONTROL",u"OFF"]
        elif currentmode == 1:
            mode = [u"1",u"OFF",u"CONTINUOUS CONTROL",u"CONTINUOUS CONTROL",u"ON"]
        elif currentmode == 2:
            mode = [u"2",u"OFF",u"CONTINUOUS CONTROL",u"STANDBY MODE",u"OFF"]
        elif currentmode == 3:
            mode = [u"3",u"OFF",u"CONTINUOUS CONTROL",u"STANDBY MODE",u"ON"]
        elif currentmode == 4:
            mode = [u"4",u"OFF",u"STANDBY MODE",u"CONTINUOUS CONTROL",u"OFF"]
        elif currentmode == 5:
            mode = [u"5",u"OFF",u"STANDBY MODE",u"CONTINUOUS CONTROL",u"ON"]
        elif currentmode == 6:
            mode = [u"6",u"OFF",u"STANDBY MODE",u"STANDBY MODE",u"OFF"]
        elif currentmode == 7:
            mode = [u"7",u"OFF",u"STANDBY MODE",u"STANDBY MODE",u"ON"]
        elif currentmode == 8:
            mode = [u"8",u"ON",u"CONTINUOUS CONTROL",u"CONTINUOUS CONTROL",u"OFF"]
        elif currentmode == 9:
            mode = [u"9",u"ON",u"CONTINUOUS CONTROL",u"CONTINUOUS CONTROL",u"ON"]
        elif currentmode == 10:
            mode = [u"10",u"ON",u"CONTINUOUS CONTROL",u"STANDBY MODE",u"OFF"]
        elif currentmode == 11:
            mode = [u"11",u"ON",u"CONTINUOUS CONTROL",u"STANDBY MODE",u"ON"]
        elif currentmode == 12:
            mode = [u"12",u"ON",u"STANDBY MODE",u"CONTINUOUS CONTROL",u"OFF"]
        elif currentmode == 13:
            mode = [u"13",u"ON","STANDBY MODE",u"CONTINUOUS CONTROL",u"ON"]
        elif currentmode == 14:
            mode = [u"14",u"ON",u"STANDBY MODE","STANDBY MODE",u"OFF"]
        elif currentmode == 15:
            mode = [u"15",u"ON",u"STANDBY MODE",u"STANDBY MODE",u"ON"]
        else:
            return -1

        string = u"The rampsoak-mode tells how to start and end the ramp/soak\n\n"
        string += u"Your rampsoak mode in this pid is:\n"
        string += u"\nMode = " + mode[0]
        string += u"\n-----------------------------------------------------------------------"
        string += u"\nStart to run from PV value: " + mode[1]
        string += u"\nEnd output status at the end of ramp/soak: " + mode[2]
        string += u"\nOutput status while ramp/soak opearion set to OFF: " + mode[3] 
        string += u"\nRepeat Operation at the end: " + mode[4]
        string += u"\n-----------------------------------------------------------------------"
        string += u"\n\nRecomended Mode = 0\n"
        string += u"\nIf you need to change it, change it now and come back later"
        string += u"\nUse the Parameter Loader Software by Fuji if you need to\n\n"
        string += u"\n\n\nContinue?" 
 
        reply = QMessageBox.question(self,u"Ramp Soak start-end mode",string,
                            QMessageBox.Yes|QMessageBox.Cancel)
        if reply == QMessageBox.Cancel:
            return 0
        elif reply == QMessageBox.Yes:
            return 1  

    def setONOFFrampsoak(self,flag):         
        #flag =0 OFF, flag = 1 ON, flag = 2 hold
        
        #set rampsoak pattern ON
        if flag == 1:
            check = self.checkrampsoakmode()
            if check == 0:
                self.status.showMessage(u"Ramp/Soak operation cancelled", 5000)
                return
            elif check == -1:
                self.status.showMessage(u"No RX data", 5000)
                
            self.status.showMessage(u"Setting RS ON...",500)
            #0 = 1-4
            #1 = 5-8
            #2 = 1-8
            selectedmode = self.patternComboBox.currentIndex()
            msg = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXR["rampsoakpattern"][1],1)
            currentmode = aw.pid.readoneword(msg)
            if currentmode != -1:
                aw.pid.PXR["rampsoakpattern"][0] = currentmode
                if currentmode != selectedmode:
                    #set mode in pid to match the mode selected in the combobox
                    self.status.showMessage(u"Need to change pattern mode...",1000)
                    command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["rampsoakpattern"][1],selectedmode)
                    r = aw.ser.sendFUJIcommand(command,8)
                    if len(r) == 8:
                        self.status.showMessage(u"Pattern has been changed. Wait 5 secs.", 500)
                        aw.pid.PXR["rampsoakpattern"][0] = selectedmode
                        time.sleep(5) #wait 5 seconds to set eeprom memory
                    else:
                        self.status.showMessage(u"Pattern could not be changed", 5000)
                        return
                #combobox mode matches pid mode
                #set ramp soak mode ON
                command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["rampsoak"][1],flag)
                r = aw.ser.sendFUJIcommand(command,8)
                if r == command:
                    self.status.showMessage(u"RS ON and running...", 5000)
                else:
                    self.status.showMessage(u"RampSoak could not be turned ON", 5000)
            else:
                mssg = u"setONOFFrampsoak() problem "
                self.status.showMessage(mssg,5000)
                aw.qmc.errorlog.append(mssg)
                  
        #set ramp soak OFF       
        elif flag == 0:
            self.status.showMessage(u"setting RS OFF...",500)
            command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["rampsoak"][1],flag)
            r = aw.ser.sendFUJIcommand(command,8)
            if r == command:
                self.status.showMessage(u"RS successfully turned OFF", 5000)
                aw.pid.PXR["rampsoak"][0] = flag
            else:
                mssg = u"Ramp Soak could not be set OFF"
                self.status.showMessage(mssg,5000)
                aw.qmc.errorlog.append(mssg)

    def getsegment(self, idn):
        svkey = u"segment" + unicode(idn) + u"sv"
        svcommand = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXR[svkey][1],1)
        sv = aw.pid.readoneword(svcommand)
        if sv == -1:
            mssg = u"getsegment(): problem reading sv "
            self.status.showMessage(mssg,5000)
            aw.qmc.errorlog.append(mssg)
            return -1
        aw.pid.PXR[svkey][0] = sv/10.              #divide by 10 because the decimal point is not sent by the PID

        rampkey = u"segment" +unicode(idn) + u"ramp"
        rampcommand = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXR[rampkey][1],1)
        ramp = aw.pid.readoneword(rampcommand)
        if ramp == -1:
            mssg = u"getsegment(): problem reading ramp "
            self.status.showMessage(mssg,5000)
            aw.qmc.errorlog.append(mssg)
            return -1
        aw.pid.PXR[rampkey][0] = ramp/10.
        
        soakkey = u"segment" + unicode(idn) + u"soak"
        soakcommand = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXR[soakkey][1],1)
        soak = aw.pid.readoneword(soakcommand)
        if soak == -1:
            mssg = u"getsegment(): problem reading soak "
            self.status.showMessage(mssg,5000)
            aw.qmc.errorlog.append(mssg)
            return -1
            return -1
        aw.pid.PXR[soakkey][0] = soak/10.


    #get all Ramp Soak values for all 8 segments                                  
    def getallsegments(self):
        for i in range(8):
            msg = u"Reading Ramp/Soak #" + unicode(i+1)
            self.status.showMessage(msg,500)
            k = self.getsegment(i+1)
            time.sleep(0.035)
            if k == -1:
                mssg = u"getallsegments(): problem reading R/S "
                self.status.showMessage(mssg,5000)
                aw.qmc.errorlog.append(mssg)
                return
            self.paintlabels()
            
        self.status.showMessage(u"Finished reading Ramp/Soak val.",5000)
        
    def getpid(self):        
        pcommand= aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXR["p"][1],1)
        p = aw.pid.readoneword(pcommand)/10.
        if p == -1 :
            return -1
        else:
            self.pedit.setText(str(p))
            aw.pid.PXR["p"][0] = p

        #i is int range 0-3200
        icommand = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXR["i"][1],1)
        i = aw.pid.readoneword(icommand)/10
        if i == -1:
            return -1
        else:
            self.iedit.setText(unicode(int(i)))
            aw.pid.PXR["i"][0] = i

        dcommand = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXR["d"][1],1)
        d = aw.pid.readoneword(dcommand)/10.
        if d == -1:
            return -1
        else:
            self.dedit.setText(unicode(d))
            aw.pid.PXR["d"][0] = d
            
        self.status.showMessage(u"Finished reading pid values",5000)
        

    def setpid(self,var):
        r = u""
        if var == u"p":
            if unicode(self.pedit.text()).isdigit():
                p = int(self.pedit.text())*10
                command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["p"][1],p)
                r = aw.ser.sendFUJIcommand(command,8)
            else:
                return -1
        elif var == u"i":
            if str(self.iedit.text()).isdigit():
                i = int(self.iedit.text())*10
                command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["i"][1],i)
                r = aw.ser.sendFUJIcommand(command,8)
            else:
                return -1
        elif var == u"d":
            if unicode(self.dedit.text()).isdigit():
                d = int(self.dedit.text())*10
                command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["d"][1],d)
                r = aw.ser.sendFUJIcommand(command,8)
            else:
                return -1
                
        if len(r) == 8:
            message = var + u" successfully send to pid "
            self.status.showMessage(message,5000)
            if var == u"p":
                aw.pid.PXR["p"][0] = p
            elif var == u"i":
                aw.pid.PXR["i"][0] = i
            elif var == u"d":
                aw.pid.PXR["i"][0] = d
            
        else:
            mssg = u"setpid(): There was a problem setting " + var 
            self.status.showMessage(mssg,5000)        
            aw.qmc.errorlog.append(mssg)


############################################################################
######################## FUJI PXG4 PID CONTROL DIALOG ######################
############################################################################
    
class PXG4pidDlgControl(QDialog):
    def __init__(self, parent = None):
        super(PXG4pidDlgControl,self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.setWindowTitle("Fuji PXG4 PID control")

        self.status = QStatusBar()
        self.status.setSizeGripEnabled(False)
        self.status.showMessage("Ready",5000)

        #*************    TAB 1 WIDGETS
        labelrs1 = QLabel()
        labelrs1.setMargin(10)
        labelrs1.setStyleSheet("background-color:'#CCCCCC';")
        labelrs1.setText( "<font color='white'><b>RampSoak<br>(1-7)<\b></font>")
        #labelrs1.setMaximumSize(90, 42)
        #labelrs1.setMinimumHeight(50)

        labelrs2 = QLabel()
        labelrs2.setMargin(10)
        labelrs2.setStyleSheet("background-color:'#CCCCCC';")
        labelrs2.setText( "<font color='white'><b>RampSoak<br>(8-16)<\b></font>")
        #labelrs2.setMaximumSize(90, 42)
        #labelrs2.setMinimumHeight(50)

        self.label_rs1 =  QLabel()
        self.label_rs2 =  QLabel()
        self.label_rs3 =  QLabel()
        self.label_rs4 =  QLabel()
        self.label_rs5 =  QLabel()
        self.label_rs6 =  QLabel()
        self.label_rs7 =  QLabel()
        self.label_rs8 =  QLabel()
        self.label_rs9 =  QLabel()
        self.label_rs10 =  QLabel()
        self.label_rs11 =  QLabel()
        self.label_rs12 =  QLabel()
        self.label_rs13 =  QLabel()
        self.label_rs14 =  QLabel()
        self.label_rs15 =  QLabel()
        self.label_rs16 =  QLabel()

        self.label_rs1.setMinimumWidth(170)
        self.label_rs2.setMinimumWidth(170)
        self.label_rs3.setMinimumWidth(170)
        self.label_rs4.setMinimumWidth(170)
        self.label_rs5.setMinimumWidth(170)
        self.label_rs6.setMinimumWidth(170)
        self.label_rs7.setMinimumWidth(170)
        self.label_rs8.setMinimumWidth(170)
        self.label_rs9.setMinimumWidth(170)
        self.label_rs10.setMinimumWidth(170)
        self.label_rs11.setMinimumWidth(170)
        self.label_rs12.setMinimumWidth(170)
        self.label_rs13.setMinimumWidth(170)
        self.label_rs14.setMinimumWidth(170)
        self.label_rs15.setMinimumWidth(170)
        self.label_rs16.setMinimumWidth(170)

        self.label_rs1.setMargin(10)
        self.label_rs2.setMargin(10)
        self.label_rs3.setMargin(10)
        self.label_rs4.setMargin(10)
        self.label_rs5.setMargin(10)
        self.label_rs6.setMargin(10)
        self.label_rs7.setMargin(10)
        self.label_rs8.setMargin(10)
        self.label_rs9.setMargin(10)
        self.label_rs10.setMargin(10)
        self.label_rs11.setMargin(10)
        self.label_rs12.setMargin(10)
        self.label_rs13.setMargin(10)
        self.label_rs14.setMargin(10)
        self.label_rs15.setMargin(10)
        self.label_rs16.setMargin(10)


        
        self.patternComboBox =  QComboBox()
        self.patternComboBox.addItems(["1-4","5-8","1-8","9-12","13-16","9-16","1-16"])
        
        self.paintlabels()

        patternlabel = QLabel("Pattern")
        patternlabel.setAlignment(Qt.AlignRight)
        button_getall = QPushButton("Read RS values")
        button_rson =  QPushButton("RampSoak ON")        
        button_rsoff =  QPushButton("RampSoak OFF")
        button_exit = QPushButton("Close")
        button_exit2 = QPushButton("Close")
        button_standbyON = QPushButton("PID OFF")
        button_standbyOFF = QPushButton("PID ON")
        
        self.connect(button_getall, SIGNAL("clicked()"), self.getallsegments)
        self.connect(button_rson, SIGNAL("clicked()"), lambda flag=1: self.setONOFFrampsoak(flag))
        self.connect(button_rsoff, SIGNAL("clicked()"), lambda flag=0: self.setONOFFrampsoak(flag))
        self.connect(button_standbyON, SIGNAL("clicked()"), lambda flag=1: self.setONOFFstandby(flag))
        self.connect(button_standbyOFF, SIGNAL("clicked()"), lambda flag=0: self.setONOFFstandby(flag))
        self.connect(button_exit, SIGNAL("clicked()"),self, SLOT("reject()"))
        self.connect(button_exit2, SIGNAL("clicked()"),self, SLOT("reject()"))

        #create layouts and place tab1 widgets inside 
        buttonRampSoakLayout1 = QVBoxLayout() #TAB1/COLUNM 1
        buttonRampSoakLayout1.setSpacing(10)
        buttonRampSoakLayout2 = QVBoxLayout() #TAB1/COLUMN 2 
        buttonRampSoakLayout2.setSpacing(10)
        
        #place rs labels in RampSoakLayout1 #TAB1/COLUNM 1
        buttonRampSoakLayout1.addWidget(labelrs1)
        buttonRampSoakLayout1.addWidget(self.label_rs1)
        buttonRampSoakLayout1.addWidget(self.label_rs2)
        buttonRampSoakLayout1.addWidget(self.label_rs3)
        buttonRampSoakLayout1.addWidget(self.label_rs4)
        
        buttonRampSoakLayout1.addWidget(self.label_rs5)
        buttonRampSoakLayout1.addWidget(self.label_rs6)
        buttonRampSoakLayout1.addWidget(self.label_rs7)        
        buttonRampSoakLayout1.addWidget(self.label_rs8)
    
        #place rs labels in RampSoakLayout2 #TAB1/COLUMN 2
        buttonRampSoakLayout2.addWidget(labelrs2)
        buttonRampSoakLayout2.addWidget(self.label_rs9)
        buttonRampSoakLayout2.addWidget(self.label_rs10)
        buttonRampSoakLayout2.addWidget(self.label_rs11)
        buttonRampSoakLayout2.addWidget(self.label_rs12)
        buttonRampSoakLayout2.addWidget(self.label_rs13)
        buttonRampSoakLayout2.addWidget(self.label_rs14)
        buttonRampSoakLayout2.addWidget(self.label_rs15)        
        buttonRampSoakLayout2.addWidget(self.label_rs16)


        # *************** TAB 2 WIDGETS
        labelsv = QLabel()
        labelsv.setMargin(10)
        labelsv.setStyleSheet("background-color:'#CCCCCC';")
        labelsv.setText( "<font color='white'><b>SV (7-0)<\b></font>")
        labelsv.setMaximumSize(100, 42)
        labelsv.setMinimumHeight(50)
        
        labelsvedit = QLabel()
        labelsvedit.setMargin(10)
        labelsvedit.setStyleSheet("background-color:'#CCCCCC';")
        labelsvedit.setText( "<font color='white'><b>Write<\b></font>")
        labelsvedit.setMaximumSize(100, 42)
        labelsvedit.setMinimumHeight(50)
        
        button_sv1 =QPushButton("Write SV1")
        button_sv2 =QPushButton("Write SV2")
        button_sv3 =QPushButton("Write SV3")
        button_sv4 =QPushButton("Write SV4")
        button_sv5 =QPushButton("Write SV5")
        button_sv6 =QPushButton("Write SV6")
        button_sv7 =QPushButton("Write SV7")

        self.connect(self.patternComboBox,SIGNAL("currentIndexChanged(int)"),self.paintlabels)
        self.connect(button_sv1, SIGNAL("clicked()"), lambda v=1: self.setsv(v))
        self.connect(button_sv2, SIGNAL("clicked()"), lambda v=2: self.setsv(v))
        self.connect(button_sv3, SIGNAL("clicked()"), lambda v=3: self.setsv(v))
        self.connect(button_sv4, SIGNAL("clicked()"), lambda v=4: self.setsv(v))
        self.connect(button_sv5, SIGNAL("clicked()"), lambda v=5: self.setsv(v))
        self.connect(button_sv6, SIGNAL("clicked()"), lambda v=6: self.setsv(v))
        self.connect(button_sv7, SIGNAL("clicked()"), lambda v=7: self.setsv(v))


        self.sv1edit = QLineEdit(QString(str(aw.pid.PXG4["sv1"][0])))
        self.sv2edit = QLineEdit(QString(str(aw.pid.PXG4["sv2"][0])))
        self.sv3edit = QLineEdit(QString(str(aw.pid.PXG4["sv3"][0])))
        self.sv4edit = QLineEdit(QString(str(aw.pid.PXG4["sv4"][0])))
        self.sv5edit = QLineEdit(QString(str(aw.pid.PXG4["sv5"][0])))
        self.sv6edit = QLineEdit(QString(str(aw.pid.PXG4["sv6"][0])))
        self.sv7edit = QLineEdit(QString(str(aw.pid.PXG4["sv7"][0])))
        
        self.sv1edit.setMaximumWidth(80)
        self.sv2edit.setMaximumWidth(80)
        self.sv3edit.setMaximumWidth(80)
        self.sv4edit.setMaximumWidth(80)
        self.sv5edit.setMaximumWidth(80)
        self.sv6edit.setMaximumWidth(80)
        self.sv7edit.setMaximumWidth(80)
        

        self.sv1edit.setValidator(QDoubleValidator(0., 999., 1, self.sv1edit))
        self.sv2edit.setValidator(QDoubleValidator(0., 999., 1, self.sv2edit))
        self.sv3edit.setValidator(QDoubleValidator(0., 999., 1, self.sv3edit))
        self.sv4edit.setValidator(QDoubleValidator(0., 999., 1, self.sv4edit))
        self.sv5edit.setValidator(QDoubleValidator(0., 999., 1, self.sv5edit))
        self.sv6edit.setValidator(QDoubleValidator(0., 999., 1, self.sv6edit))
        self.sv7edit.setValidator(QDoubleValidator(0., 999., 1, self.sv7edit))

        self.radiosv1 = QRadioButton()
        self.radiosv2 = QRadioButton()
        self.radiosv3 = QRadioButton()
        self.radiosv4 = QRadioButton()
        self.radiosv5 = QRadioButton()
        self.radiosv6 = QRadioButton()
        self.radiosv7 = QRadioButton()

        N = aw.pid.PXG4["selectsv"][0]
        if N == 1:
            self.radiosv1.setChecked(True)
        elif N == 2:
            self.radiosv2.setChecked(True)
        elif N == 3:
            self.radiosv3.setChecked(True)
        elif N == 4:
            self.radiosv4.setChecked(True)
        elif N == 5:
            self.radiosv5.setChecked(True)
        elif N == 6:
            self.radiosv6.setChecked(True)
        elif N == 7:
            self.radiosv7.setChecked(True)

        tab2svbutton = QPushButton("Write SV")
        tab2cancelbutton = QPushButton("Cancel")
        tab2easyONsvbutton = QPushButton("ON SV buttons")
        tab2easyONsvbutton.setStyleSheet("QPushButton { background-color: 'lightblue'}")
        tab2easyOFFsvbutton = QPushButton("OFF SV buttons")
        tab2easyOFFsvbutton.setStyleSheet("QPushButton { background-color:'#ffaaff' }")
        tab2getsvbutton = QPushButton("Read SV (7-0)")
        
        self.connect(tab2svbutton, SIGNAL("clicked()"),self.setsv)
        self.connect(tab2getsvbutton, SIGNAL("clicked()"),self.getallsv)
        self.connect(tab2cancelbutton, SIGNAL("clicked()"),self, SLOT("reject()"))
        self.connect(tab2easyONsvbutton, SIGNAL("clicked()"), lambda flag=1: aw.pid.activateONOFFeasySV(flag))
        self.connect(tab2easyOFFsvbutton, SIGNAL("clicked()"), lambda flag=0: aw.pid.activateONOFFeasySV(flag))
        self.connect(self.radiosv1,SIGNAL("clicked()"), lambda sv=1: self.setNsv(sv))
        self.connect(self.radiosv2,SIGNAL("clicked()"), lambda sv=2: self.setNsv(sv))
        self.connect(self.radiosv3,SIGNAL("clicked()"), lambda sv=3: self.setNsv(sv))
        self.connect(self.radiosv4,SIGNAL("clicked()"), lambda sv=4: self.setNsv(sv))
        self.connect(self.radiosv5,SIGNAL("clicked()"), lambda sv=5: self.setNsv(sv))
        self.connect(self.radiosv6,SIGNAL("clicked()"), lambda sv=6: self.setNsv(sv))
        self.connect(self.radiosv7,SIGNAL("clicked()"), lambda sv=7: self.setNsv(sv))

        #TAB 3
        plabel = QLabel()
        plabel.setMargin(10)
        plabel.setStyleSheet("background-color:'#CCCCCC';")
        plabel.setText( "<font color='white'><b>P<\b></font>")
        plabel.setMaximumSize(50, 42)
        plabel.setMinimumHeight(50)

        ilabel = QLabel()
        ilabel.setMargin(10)
        ilabel.setStyleSheet("background-color:'#CCCCCC';")
        ilabel.setText( "<font color='white'><b>I<\b></font>")
        ilabel.setMaximumSize(50, 42)
        ilabel.setMinimumHeight(50)
        
        dlabel = QLabel()
        dlabel.setMargin(10)
        dlabel.setStyleSheet("background-color:'#CCCCCC';")
        dlabel.setText( "<font color='white'><b>D<\b></font>")
        dlabel.setMaximumSize(50, 42)
        dlabel.setMinimumHeight(50)

        wlabel = QLabel()
        wlabel.setMargin(10)
        wlabel.setStyleSheet("background-color:'#CCCCCC';")
        wlabel.setText( "<font color='white'><b>Write<\b></font>")
        wlabel.setMaximumSize(50, 42)
        wlabel.setMinimumHeight(50)
        
        self.p1edit =  QLineEdit(QString(unicode(aw.pid.PXG4["p1"][0])))
        self.p2edit =  QLineEdit(QString(unicode(aw.pid.PXG4["p2"][0])))
        self.p3edit =  QLineEdit(QString(unicode(aw.pid.PXG4["p3"][0])))
        self.p4edit =  QLineEdit(QString(unicode(aw.pid.PXG4["p4"][0])))
        self.p5edit =  QLineEdit(QString(unicode(aw.pid.PXG4["p5"][0])))
        self.p6edit =  QLineEdit(QString(unicode(aw.pid.PXG4["p6"][0])))
        self.p7edit =  QLineEdit(QString(unicode(aw.pid.PXG4["p7"][0])))
        self.i1edit =  QLineEdit(QString(unicode(aw.pid.PXG4["i1"][0])))
        self.i2edit =  QLineEdit(QString(unicode(aw.pid.PXG4["i2"][0])))
        self.i3edit =  QLineEdit(QString(unicode(aw.pid.PXG4["i3"][0])))
        self.i4edit =  QLineEdit(QString(unicode(aw.pid.PXG4["i4"][0])))
        self.i5edit =  QLineEdit(QString(unicode(aw.pid.PXG4["i5"][0])))
        self.i6edit =  QLineEdit(QString(unicode(aw.pid.PXG4["i6"][0])))
        self.i7edit =  QLineEdit(QString(unicode(aw.pid.PXG4["i7"][0])))
        self.d1edit =  QLineEdit(QString(unicode(aw.pid.PXG4["d1"][0])))
        self.d2edit =  QLineEdit(QString(unicode(aw.pid.PXG4["d2"][0])))
        self.d3edit =  QLineEdit(QString(unicode(aw.pid.PXG4["d3"][0])))
        self.d4edit =  QLineEdit(QString(unicode(aw.pid.PXG4["d4"][0])))
        self.d5edit =  QLineEdit(QString(unicode(aw.pid.PXG4["d5"][0])))
        self.d6edit =  QLineEdit(QString(unicode(aw.pid.PXG4["d6"][0])))
        self.d7edit =  QLineEdit(QString(unicode(aw.pid.PXG4["d7"][0])))

        self.p1edit.setMaximumSize(50, 42)
        self.p2edit.setMaximumSize(50, 42)
        self.p3edit.setMaximumSize(50, 42)
        self.p4edit.setMaximumSize(50, 42)
        self.p5edit.setMaximumSize(50, 42)
        self.p6edit.setMaximumSize(50, 42)
        self.p7edit.setMaximumSize(50, 42)
        self.i1edit.setMaximumSize(50, 42)
        self.i2edit.setMaximumSize(50, 42)
        self.i3edit.setMaximumSize(50, 42)
        self.i4edit.setMaximumSize(50, 42)
        self.i5edit.setMaximumSize(50, 42)
        self.i6edit.setMaximumSize(50, 42)
        self.i7edit.setMaximumSize(50, 42)
        self.d1edit.setMaximumSize(50, 42)
        self.d2edit.setMaximumSize(50, 42)
        self.d3edit.setMaximumSize(50, 42)
        self.d4edit.setMaximumSize(50, 42)
        self.d5edit.setMaximumSize(50, 42)
        self.d6edit.setMaximumSize(50, 42)
        self.d7edit.setMaximumSize(50, 42)
        #p = 0-999.9
        self.p1edit.setValidator(QDoubleValidator(0., 999., 1, self.p1edit))
        self.p2edit.setValidator(QDoubleValidator(0., 999., 1, self.p2edit))
        self.p3edit.setValidator(QDoubleValidator(0., 999., 1, self.p3edit))
        self.p4edit.setValidator(QDoubleValidator(0., 999., 1, self.p4edit))
        self.p5edit.setValidator(QDoubleValidator(0., 999., 1, self.p5edit))
        self.p6edit.setValidator(QDoubleValidator(0., 999., 1, self.p6edit))
        self.p7edit.setValidator(QDoubleValidator(0., 999., 1, self.p7edit))
        #i are int 0-3200
        self.i1edit.setValidator(QIntValidator(0, 3200, self.i1edit))
        self.i2edit.setValidator(QIntValidator(0, 3200, self.i2edit))
        self.i3edit.setValidator(QIntValidator(0, 3200, self.i3edit))
        self.i4edit.setValidator(QIntValidator(0, 3200, self.i4edit))
        self.i5edit.setValidator(QIntValidator(0, 3200, self.i5edit))
        self.i6edit.setValidator(QIntValidator(0, 3200, self.i6edit))
        self.i7edit.setValidator(QIntValidator(0, 3200, self.i7edit))
        #d 0-999.9
        self.d1edit.setValidator(QDoubleValidator(0., 999., 1, self.d1edit))
        self.d2edit.setValidator(QDoubleValidator(0., 999., 1, self.d2edit))
        self.d3edit.setValidator(QDoubleValidator(0., 999., 1, self.d3edit))
        self.d4edit.setValidator(QDoubleValidator(0., 999., 1, self.d4edit))
        self.d5edit.setValidator(QDoubleValidator(0., 999., 1, self.d5edit))
        self.d6edit.setValidator(QDoubleValidator(0., 999., 1, self.d6edit))
        self.d7edit.setValidator(QDoubleValidator(0., 999., 1, self.d7edit))
        
        pid1button = QPushButton("pid 1")
        pid2button = QPushButton("pid 2")
        pid3button = QPushButton("pid 3")
        pid4button = QPushButton("pid 4")
        pid5button = QPushButton("pid 5")
        pid6button = QPushButton("pid 6")
        pid7button = QPushButton("pid 7")
        pidreadallbutton = QPushButton("Read All")
        autotuneONbutton = QPushButton("Auto Tune ON")
        autotuneOFFbutton = QPushButton("Auto Tune OFF")
        cancel3button = QPushButton("Cancel")
        
        self.radiopid1 = QRadioButton()
        self.radiopid2 = QRadioButton()
        self.radiopid3 = QRadioButton()
        self.radiopid4 = QRadioButton()
        self.radiopid5 = QRadioButton()
        self.radiopid6 = QRadioButton()
        self.radiopid7 = QRadioButton()

        self.connect(pidreadallbutton, SIGNAL("clicked()"),self.getallpid)
        self.connect(self.radiopid1,SIGNAL("clicked()"), lambda pid=1: self.setNpid(pid))
        self.connect(self.radiopid2,SIGNAL("clicked()"), lambda pid=2: self.setNpid(pid))
        self.connect(self.radiopid3,SIGNAL("clicked()"), lambda pid=3: self.setNpid(pid))
        self.connect(self.radiopid4,SIGNAL("clicked()"), lambda pid=4: self.setNpid(pid))
        self.connect(self.radiopid5,SIGNAL("clicked()"), lambda pid=5: self.setNpid(pid))
        self.connect(self.radiopid6,SIGNAL("clicked()"), lambda pid=6: self.setNpid(pid))
        self.connect(self.radiopid7,SIGNAL("clicked()"), lambda pid=7: self.setNpid(pid))
        self.connect(pid1button, SIGNAL("clicked()"), lambda v=1: self.setpid(v))
        self.connect(pid2button, SIGNAL("clicked()"), lambda v=2: self.setpid(v))
        self.connect(pid3button, SIGNAL("clicked()"), lambda v=3: self.setpid(v))
        self.connect(pid4button, SIGNAL("clicked()"), lambda v=4: self.setpid(v))
        self.connect(pid5button, SIGNAL("clicked()"), lambda v=5: self.setpid(v))
        self.connect(pid6button, SIGNAL("clicked()"), lambda v=6: self.setpid(v))
        self.connect(pid7button, SIGNAL("clicked()"), lambda v=7: self.setpid(v))
        self.connect(cancel3button, SIGNAL("clicked()"),self, SLOT("reject()"))
        self.connect(autotuneONbutton, SIGNAL("clicked()"), lambda flag=1: self.setONOFFautotune(flag))
        self.connect(autotuneOFFbutton, SIGNAL("clicked()"), lambda flag=0: self.setONOFFautotune(flag))
        
        # LAYOUTS        
        tab1Layout = QGridLayout() #TAB1
        tab1Layout.setSpacing(10)
        tab1Layout.setSizeConstraint(2)

        tab1Layout.addLayout(buttonRampSoakLayout1,0,0)
        tab1Layout.addLayout(buttonRampSoakLayout2,0,1)
        tab1Layout.addWidget(button_rson,1,0)
        tab1Layout.addWidget(button_rsoff,1,1)
        tab1Layout.addWidget(button_standbyOFF,2,0)
        tab1Layout.addWidget(button_standbyON,2,1)                             
        tab1Layout.addWidget(patternlabel,3,0)
        tab1Layout.addWidget(self.patternComboBox,3,1)
        tab1Layout.addWidget(button_getall,4,0)
        tab1Layout.addWidget(button_exit,4,1)

        tab2Layout = QGridLayout() #TAB2
        tab2Layout.setSpacing(10)
        tab2Layout.setSizeConstraint(2)
        
        tab2Layout.addWidget(labelsv,0,0)
        tab2Layout.addWidget(labelsvedit,0,1)
        tab2Layout.addWidget(self.sv7edit,1,0)
        tab2Layout.addWidget(button_sv7,1,1)
        tab2Layout.addWidget(self.sv6edit,2,0)       
        tab2Layout.addWidget(button_sv6,2,1)
        tab2Layout.addWidget(self.sv5edit,3,0)
        tab2Layout.addWidget(button_sv5,3,1)
        tab2Layout.addWidget(self.sv4edit,4,0)        
        tab2Layout.addWidget(button_sv4,4,1)
        tab2Layout.addWidget(self.sv3edit,5,0)
        tab2Layout.addWidget(button_sv3,5,1)
        tab2Layout.addWidget(self.sv2edit,6,0)        
        tab2Layout.addWidget(button_sv2,6,1)
        tab2Layout.addWidget(self.sv1edit,7,0)        
        tab2Layout.addWidget(button_sv1,7,1)
        tab2Layout.addWidget(self.radiosv7,1,2)
        tab2Layout.addWidget(self.radiosv6,2,2)
        tab2Layout.addWidget(self.radiosv5,3,2)
        tab2Layout.addWidget(self.radiosv4,4,2)
        tab2Layout.addWidget(self.radiosv3,5,2)
        tab2Layout.addWidget(self.radiosv2,6,2)
        tab2Layout.addWidget(self.radiosv1,7,2)
        
        tab2Layout.addWidget(tab2easyOFFsvbutton,8,0)
        tab2Layout.addWidget(tab2easyONsvbutton,8,1)
        tab2Layout.addWidget(tab2getsvbutton,9,0)
        tab2Layout.addWidget(button_exit2,9,1)

        tab3Layout = QGridLayout() #TAB3
        tab3Layout.setSpacing(10)
        tab3Layoutbutton = QGridLayout()
        tab3MasterLayout = QVBoxLayout()
        tab3MasterLayout.addLayout(tab3Layout,0)        
        tab3MasterLayout.addLayout(tab3Layoutbutton,1)        
        
        tab3Layout.addWidget(plabel,0,0)
        tab3Layout.addWidget(ilabel,0,1)
        tab3Layout.addWidget(dlabel,0,2)
        tab3Layout.addWidget(wlabel,0,3)
        
        tab3Layout.addWidget(self.p1edit,1,0)
        tab3Layout.addWidget(self.i1edit,1,1)
        tab3Layout.addWidget(self.d1edit,1,2)
        tab3Layout.addWidget(pid1button,1,3)
        tab3Layout.addWidget(self.p2edit,2,0)
        tab3Layout.addWidget(self.i2edit,2,1)
        tab3Layout.addWidget(self.d2edit,2,2)
        tab3Layout.addWidget(pid2button,2,3)
        tab3Layout.addWidget(self.p3edit,3,0)
        tab3Layout.addWidget(self.i3edit,3,1)
        tab3Layout.addWidget(self.d3edit,3,2)
        tab3Layout.addWidget(pid3button,3,3)
        tab3Layout.addWidget(self.p4edit,4,0)
        tab3Layout.addWidget(self.i4edit,4,1)
        tab3Layout.addWidget(self.d4edit,4,2)
        tab3Layout.addWidget(pid4button,4,3)
        tab3Layout.addWidget(self.p5edit,5,0)
        tab3Layout.addWidget(self.i5edit,5,1)
        tab3Layout.addWidget(self.d5edit,5,2)
        tab3Layout.addWidget(pid5button,5,3)
        tab3Layout.addWidget(self.p6edit,6,0)
        tab3Layout.addWidget(self.i6edit,6,1)
        tab3Layout.addWidget(self.d6edit,6,2)
        tab3Layout.addWidget(pid6button,6,3)
        tab3Layout.addWidget(self.p7edit,7,0)
        tab3Layout.addWidget(self.i7edit,7,1)
        tab3Layout.addWidget(self.d7edit,7,2)
        tab3Layout.addWidget(pid7button,7,3)
        
        tab3Layout.addWidget(self.radiopid1,1,4)
        tab3Layout.addWidget(self.radiopid2,2,4)
        tab3Layout.addWidget(self.radiopid3,3,4)
        tab3Layout.addWidget(self.radiopid4,4,4)
        tab3Layout.addWidget(self.radiopid5,5,4)
        tab3Layout.addWidget(self.radiopid6,6,4)
        tab3Layout.addWidget(self.radiopid7,7,4)

        tab3Layoutbutton.addWidget(autotuneONbutton,0,0)
        tab3Layoutbutton.addWidget(autotuneOFFbutton,0,1)        
        tab3Layoutbutton.addWidget(pidreadallbutton,1,0)
        tab3Layoutbutton.addWidget(cancel3button,1,1)

        
        ############################
        TabWidget = QTabWidget()
        
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        TabWidget.addTab(C1Widget,"RS")
        
        C2Widget = QWidget()
        C2Widget.setLayout(tab2Layout)
        TabWidget.addTab(C2Widget,"SV")

        C3Widget = QWidget()
        C3Widget.setLayout(tab3MasterLayout)
        TabWidget.addTab(C3Widget,"PID")

        #incorporate layouts
        layout = QVBoxLayout()
        layout.addWidget(self.status,0)
        layout.addWidget(TabWidget,1)
        self.setLayout(layout)

    def paintlabels(self):
        #read values of variables to place in buttons
        str1 = u"1 [T " + unicode(aw.pid.PXG4["segment1sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment1ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment1soak"][0])+u"]"
        str2 = u"2 [T " + unicode(aw.pid.PXG4["segment2sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment2ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment2soak"][0])+u"]"
        str3 = u"3 [T " + unicode(aw.pid.PXG4["segment3sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment3ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment3soak"][0])+u"]"
        str4 = u"4 [T " + unicode(aw.pid.PXG4["segment4sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment4ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment4soak"][0])+u"]"
        str5 = u"5 [T " + unicode(aw.pid.PXG4["segment5sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment5ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment5soak"][0])+u"]"
        str6 = u"6 [T " + unicode(aw.pid.PXG4["segment6sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment6ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment6soak"][0])+u"]"
        str7 = u"7 [T " + unicode(aw.pid.PXG4["segment7sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment7ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment7soak"][0])+u"]"
        str8 = u"8 [T " + unicode(aw.pid.PXG4["segment8sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment8ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment8soak"][0])+u"]"
        str9 = u"9 [T " + unicode(aw.pid.PXG4["segment9sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment9ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment9soak"][0])+u"]"
        str10 = u"10 [T " + unicode(aw.pid.PXG4["segment10sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment10ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment10soak"][0])+u"]"
        str11 = u"11 [T "+ unicode(aw.pid.PXG4["segment11sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment11ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment11soak"][0])+u"]"
        str12 = u"12 [T "+ unicode(aw.pid.PXG4["segment12sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment12ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment12soak"][0])+u"]"
        str13 = u"13 [T "+ unicode(aw.pid.PXG4["segment13sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment13ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment13soak"][0])+u"]"
        str14 = u"14 [T "+ unicode(aw.pid.PXG4["segment14sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment14ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment14soak"][0])+u"]"
        str15 = u"15 [T "+ unicode(aw.pid.PXG4["segment15sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment15ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment15soak"][0])+u"]"
        str16 = u"16 [T "+ unicode(aw.pid.PXG4["segment16sv"][0]) + u"] [R " + unicode(aw.pid.PXG4["segment16ramp"][0]) + u"] [S " + unicode(aw.pid.PXG4["segment16soak"][0])+u"]"

        self.label_rs1.setText(QString(str1))
        self.label_rs2.setText(QString(str2))
        self.label_rs3.setText(QString(str3))
        self.label_rs4.setText(QString(str4))
        self.label_rs5.setText(QString(str5))
        self.label_rs6.setText(QString(str6))
        self.label_rs7.setText(QString(str7))
        self.label_rs8.setText(QString(str8))
        self.label_rs9.setText(QString(str9))
        self.label_rs10.setText(QString(str10))
        self.label_rs11.setText(QString(str11))
        self.label_rs12.setText(QString(str12))
        self.label_rs13.setText(QString(str13))
        self.label_rs14.setText(QString(str14))
        self.label_rs15.setText(QString(str15))
        self.label_rs16.setText(QString(str16))

        pattern = [[1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],
                  [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0],
                  [1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0],
                  [0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0],
                  [0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1],
                  [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1],
                  [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]]

        aw.pid.PXG4["rampsoakpattern"][0] = self.patternComboBox.currentIndex()

        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][0]:   
            self.label_rs1.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs1.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][1]:
            self.label_rs2.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs2.setStyleSheet("background-color:white;")
            
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][2]:   
            self.label_rs3.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs3.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][3]:   
            self.label_rs4.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs4.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][4]:   
            self.label_rs5.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs5.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][5]:   
            self.label_rs6.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs6.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][6]:   
            self.label_rs7.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs7.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][7]:   
            self.label_rs8.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs8.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][8]:   
            self.label_rs9.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs9.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][9]:   
            self.label_rs10.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs10.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][10]:   
            self.label_rs11.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs11.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][11]:   
            self.label_rs12.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs12.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][12]:   
            self.label_rs13.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs13.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][13]:   
            self.label_rs14.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs14.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][14]:   
            self.label_rs15.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs15.setStyleSheet("background-color:white;")
        if pattern[aw.pid.PXG4["rampsoakpattern"][0]][15]:   
            self.label_rs16.setStyleSheet("background-color:'#FFCC99';")
        else:
            self.label_rs16.setStyleSheet("background-color:white;")

    #selects an sv   
    def setNsv(self,svn):
        # read current sv N
        command = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4["selectsv"][1],1)
        N = aw.pid.readoneword(command)
        
        # if current svN is different than requested svN
        if N != -1:
            if N != svn:
                string = u"Current sv = " + unicode(N) + u" .Change now to sv =" + unicode(svn) + u"?"
                reply = QMessageBox.question(self,u"Change svN",string,
                                    QMessageBox.Yes|QMessageBox.Cancel)
                if reply == QMessageBox.Yes:
                    #change variable svN
                    command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["selectsv"][1],svn)
                    r = aw.ser.sendFUJIcommand(command,8)
                    
                    #check response from pid and update message on main window
                    if r == command:
                        aw.pid.PXG4["selectsv"][0] = svn
                        key = u"sv" + unicode(svn)
                        message = u"SV" + unicode(svn) + u" set to " + unicode(aw.pid.PXG4[key][0])
                        aw.lcd6.display(aw.pid.PXG4[key][0])
                        self.status.showMessage(message, 5000)
                    else:
                        self.status.showMessage(u"Problem setting SV",5000)
                elif reply == QMessageBox.Cancel:
                    self.status.showMessage(u"Cancelled svN change",5000)
                    #set radio button
                    if N == 1:
                        self.radiosv1.setChecked(True)
                    elif N == 2:
                        self.radiosv2.setChecked(True)
                    elif N == 3:
                        self.radiosv3.setChecked(True)
                    elif N == 4:
                        self.radiosv4.setChecked(True)
                    elif N == 5:
                        self.radiosv5.setChecked(True)
                    elif N == 6:
                        self.radiosv6.setChecked(True)
                    elif N == 7:
                        self.radiosv7.setChecked(True)
                    return 
            else:
                mssg = u"PID already using sv" + unicode(N)
                self.status.showMessage(mssg,1000)
        else:
            mssg = u"setNsv(): bad response"
            self.status.showMessage(mssg,1000)
            aw.qmc.errorlog.append(mssg)

        
    #selects an sv   
    def setNpid(self,pidn):
        # read current sv N
        command = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4["selectedpid"][1],1)
        N = aw.pid.readoneword(command)
        if N != -1:
            aw.pid.PXG4["selectedpid"][0] = N
            # if current svN is different than requested svN
            if N != pidn:
                string = u"Current pid = " + unicode(N) + u" .Change now to pid =" + unicode(pidn) + u"?"
                reply = QMessageBox.question(self,"Change svN",string,
                                    QMessageBox.Yes|QMessageBox.Cancel)
                if reply == QMessageBox.Yes:
                    #change variable svN
                    command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["selectedpid"][1],pidn)
                    r = aw.ser.sendFUJIcommand(command,8)
                    
                    #check response from pid and update message on main window
                    if r == command:
                        aw.pid.PXG4["selectedpid"][0] = pidn
                        key = u"sv" + unicode(pidn)
                        message = u"pid" + unicode(pidn) + u" changed to " + unicode(aw.pid.PXG4[key][0])
                        self.status.showMessage(message, 5000)
                    else:
                        mssg = u"setNpid(): bad confirmation" 
                        self.status.showMessage(mssg,1000)
                        aw.qmc.errorlog.append(mssg)
                        
                elif reply == QMessageBox.Cancel:
                    self.status.showMessage(u"Cancelled pid change",5000)
                    #put back radio button
                    if N == 1:
                        self.radiosv1.setChecked(True)
                    elif N == 2:
                        self.radiosv2.setChecked(True)
                    elif N == 3:
                        self.radiosv3.setChecked(True)
                    elif N == 4:
                        self.radiosv4.setChecked(True)
                    elif N == 5:
                        self.radiosv5.setChecked(True)
                    elif N == 6:
                        self.radiosv6.setChecked(True)
                    elif N == 7:
                        self.radiosv7.setChecked(True)
                    return
            else:
                mssg = u"PID was already using pid " + unicode(N) 
                self.status.showMessage(mssg,1000)
        else:
            mssg = u"setNpid(): Unable to set pid " + unicode(N) + u" "
            self.status.showMessage(mssg,1000)
            aw.qmc.errorlog.append(mssg)

    #writes new value on sv(i)
    def setsv(self,i):
        #first get the new sv value from the correspondig edit ine
        if i == 1:
            if self.sv1edit.text() != u"":
                newSVvalue = int(float(self.sv1edit.text())*10.) #multiply by 10 because of decimal point. Then convert to int.
        elif i == 2:
            if self.sv2edit.text() != u"":
                newSVvalue = int(float(self.sv2edit.text())*10.) 
        elif i == 3:
            if self.sv3edit.text() != u"":
                newSVvalue = int(float(self.sv3edit.text())*10.)
        elif i == 4:
            if self.sv4edit.text() != u"":
                newSVvalue = int(float(self.sv4edit.text())*10.) 
        elif i == 5:
            if self.sv5edit.text() != u"":
                newSVvalue = int(float(self.sv5edit.text())*10.) 
        elif i == 6:
            if self.sv6edit.text() != u"":
                newSVvalue = int(float(self.sv6edit.text())*10.) 
        elif i == 7:
            if self.sv7edit.text() != u"":
                newSVvalue = int(float(self.sv7edit.text())*10.) 

        #send command to the right sv
        svkey = u"sv"+ unicode(i)
        command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4[svkey][1],newSVvalue)
        r = aw.ser.sendFUJIcommand(command,8)

        #verify it went ok
        if len(r) == 8:
            if i == 1:               
                 aw.pid.PXG4[svkey][0] = float(self.sv1edit.text())
                 message = u"SV" + unicode(i)+ u" successfully set to " + unicode(self.sv1edit.text())
                 self.status.showMessage(message,5000)
                 self.setNsv(1)
            elif i == 2:
                 aw.pid.PXG4[svkey][0] = float(self.sv2edit.text())
                 message = u"SV" + unicode(i)+ u" successfully set to " + unicode(self.sv2edit.text())
                 self.status.showMessage(message,5000)
                 self.setNsv(2)
            elif i == 3:
                 aw.pid.PXG4[svkey][0] = float(self.sv3edit.text())
                 message = u"SV" + unicode(i)+ u" successfully set to " + unicode(self.sv3edit.text())
                 self.status.showMessage(message,5000)
                 self.setNsv(3)
            elif i == 4:
                 aw.pid.PXG4[svkey][0] = float(self.sv4edit.text())
                 message = u"SV" + unicode(i)+ u" successfully set to " + unicode(self.sv4edit.text())
                 self.status.showMessage(message,5000)
                 self.setNsv(4)
            elif i == 5:
                 aw.pid.PXG4[svkey][0] = float(self.sv5edit.text())
                 message = u"SV" + unicode(i)+ u" successfully set to " + unicode(self.sv5edit.text())
                 self.status.showMessage(message,5000)
                 self.setNsv(5)
            elif i == 6:
                 aw.pid.PXG4[svkey][0] = float(self.sv6edit.text())
                 message = u"SV" + unicode(i)+ u" successfully set to " + unicode(self.sv6edit.text())
                 self.status.showMessage(message,5000)
                 self.setNsv(6)
            elif i == 7:
                 aw.pid.PXG4[svkey][0] = float(self.sv7edit.text())
                 message = u"SV" + unicode(i)+ u" successfully set to " + unicode(self.sv7edit.text())
                 self.status.showMessage(message,5000)
                 self.setNsv(7)

            #call 
        else:
            mssg = u"setsv(): Unable to set SV "
            self.status.showMessage(mssg,5000)
            aw.qmc.errorlog.append(mssg)

    #writes new values for p - i - d
    def setpid(self,k):
        #first get the new sv value from the correspondig edit ine
        if k == 1:
            if self.p1edit.text() != u"" and self.i1edit.text() != u"" and self.d1edit.text() != u"":
                newPvalue = int(float(self.p1edit.text())*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(self.i1edit.text())*10.)
                newDvalue = int(float(self.d1edit.text())*10.)
                
        elif k == 2:
            if self.p2edit.text() != u"" and self.i2edit.text() != u"" and self.d2edit.text() != u"":
                newPvalue = int(float(self.p2edit.text())*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(self.i2edit.text())*10.)
                newDvalue = int(float(self.d2edit.text())*10.) 
        elif k == 3:
            if self.p3edit.text() != u"" and self.i3edit.text() != u"" and self.d3edit.text() != u"":
                newPvalue = int(float(self.p3edit.text())*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(self.i3edit.text())*10.)
                newDvalue = int(float(self.d3edit.text())*10.)
        elif k == 4:
            if self.p4edit.text() != u"" and self.i4edit.text() != u"" and self.d4edit.text() != u"":
                newPvalue = int(float(self.p4edit.text())*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(self.i4edit.text())*10.)
                newDvalue = int(float(self.d4edit.text())*10.) 
        elif k == 5:
            if self.p5edit.text() != u"" and self.i5edit.text() != u"" and self.d5edit.text() != u"":
                newPvalue = int(float(self.p5edit.text())*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(self.i5edit.text())*10.)
                newDvalue = int(float(self.d5edit.text())*10.) 
        elif k == 6:
            if self.p6edit.text() != u"" and self.i6edit.text() != u"" and self.d6edit.text() != u"":
                newPvalue = int(float(self.p6edit.text())*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(self.i6edit.text())*10.)
                newDvalue = int(float(self.d6edit.text())*10.) 
        elif k == 7:
            if self.p7edit.text() != u"" and self.i7edit.text() != u"" and self.d7edit.text() != u"":
                newPvalue = int(float(self.p7edit.text())*10.) #multiply by 10 because of decimal point. Then convert to int.
                newIvalue = int(float(self.i7edit.text())*10.)
                newDvalue = int(float(self.d7edit.text())*10.) 

        #send command to the right sv
        pkey = u"p" + unicode(k)
        ikey = u"i" + unicode(k)
        dkey = u"d" + unicode(k)
        
        commandp = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4[pkey][1],newPvalue)
        commandi = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4[ikey][1],newIvalue)
        commandd = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4[dkey][1],newDvalue)

        p = aw.ser.sendFUJIcommand(commandp,8)
        time.sleep(0.035)
        i = aw.ser.sendFUJIcommand(commandi,8)
        time.sleep(0.035)
        d = aw.ser.sendFUJIcommand(commandd,8)
        
        #verify it went ok
        if len(p) == 8 and len(i)==8 and len(d) == 8:
            if k == 1:               
                 aw.pid.PXG4[pkey][0] = float(self.p1edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i1edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d1edit.text())
                 message = (u"pid #" + unicode(k)+ u" successfully set to (" + unicode(self.p1edit.text()) + u"," +
                            unicode(self.i1edit.text()) + u"," + unicode(self.d1edit.text())+ u")")              
                 self.status.showMessage(message,5000)
                 self.setNpid(1)
            elif k == 2:
                 aw.pid.PXG4[pkey][0] = float(self.p2edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i2edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d2edit.text())
                 message = (u"pid #" + unicode(k)+ u" successfully set to (" + unicode(self.p2edit.text())+ u"," +
                            unicode(self.i2edit.text()) + u"," + unicode(self.d2edit.text())+ u")")
                 self.status.showMessage(message,5000)
                 self.setNpid(2)
            elif k == 3:
                 aw.pid.PXG4[pkey][0] = float(self.p3edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i3edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d3edit.text())
                 message = (u"pid #" + unicode(k)+ u" successfully set to (" + unicode(self.p3edit.text()) + u"," +
                            unicode(self.i3edit.text()) + u"," + unicode(self.d3edit.text()) + u")")
                 self.status.showMessage(message,5000)
                 self.setNpid(3)
            elif k == 4:
                 aw.pid.PXG4[pkey][0] = float(self.p4edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i4edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d4edit.text())
                 message = (u"pid #" + unicode(k)+ u" successfully set to (" + unicode(self.p4edit.text()) + u"," +
                            unicode(self.i4edit.text()) + u"," + unicode(self.d4edit.text()) + u")")
                 self.status.showMessage(message,5000)
                 self.setNpid(4)
            elif k == 5:
                 aw.pid.PXG4[pkey][0] = float(self.p5edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i5edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d5edit.text())
                 message = (u"pid #" + unicode(k)+ u" successfully set to (" + unicode(self.p5edit.text()) + u"," +
                             unicode(self.i5edit.text()) + u"," + unicode(self.d5edit.text()) + u")")
                 self.status.showMessage(message,5000)
                 self.setNpid(5)
            elif k == 6:
                 aw.pid.PXG4[pkey][0] = float(self.p6edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i6edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d6edit.text())
                 message = (u"pid" + unicode(k) + u" successfully set to (" + unicode(self.p6edit.text()) + u"," +
                            unicode(self.i6edit.text()) + u"," + unicode(self.d6edit.text()) + u")")
                 self.status.showMessage(message,5000)
                 self.setNpid(6)
            elif k == 7:
                 aw.pid.PXG4[pkey][0] = float(self.p7edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i7edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d7edit.text())
                 message = (u"pid" + unicode(k)+ u" successfully set to (" + unicode(self.p7edit.text()) + u"," +
                            unicode(self.i7edit.text()) + u"," + unicode(self.d7edit.text()) + u")")
                 self.status.showMessage(message,5000)
                 self.setNpid(7) 
        else:
            lp = len(p)
            li = len(i)
            ld = len(d)
            mssg = u"pid command failed. Bad data at pid" + unicode(k) + u" (8,8,8): (" + unicode(lp)+ u"," + unicode(li)+u"," + unicode(ld) + u") "
            self.status.showMessage(mssg,5000)
            aw.qmc.errorlog.append(mssg)


    def getallpid(self):
        for k in range(1,8):
            pkey = u"p" + unicode(k)
            ikey = u"i" + unicode(k)
            dkey = u"d" + unicode(k)

            msg = u"sending commands for p" + unicode(k) + u" i" + unicode(k) + u" d" + unicode(k) 
            self.status.showMessage(msg,1000)
            commandp = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4[pkey][1],1)
            p = aw.pid.readoneword(commandp)/10.
            time.sleep(0.035)                    #need minimum time of 0.03 seconds before sending another message
            commandi = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4[ikey][1],1)
            i = aw.pid.readoneword(commandi)/10.
            time.sleep(0.035)
            commandd = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4[dkey][1],1)
            d = aw.pid.readoneword(commandd)/10.
            
            if p != -1 and i != -1 and d != -1:
                aw.pid.PXG4[pkey][0] = p
                aw.pid.PXG4[ikey][0] = i
                aw.pid.PXG4[dkey][0] = d
                
                if k == 1:
                    self.p1edit.setText(unicode(p))
                    self.i1edit.setText(unicode(i))
                    self.d1edit.setText(unicode(d))                
                    mssg = pkey + u"=" + unicode(p) + u" " + ikey + u"=" + unicode(i) + u" " + dkey + u"=" + unicode(d)
                    self.status.showMessage(mssg,1000)
                if k == 2:
                    self.p2edit.setText(unicode(p))
                    self.i2edit.setText(unicode(i))
                    self.d2edit.setText(unicode(d))                
                    mssg = pkey + u"=" + unicode(p) + u" " + ikey + u"=" + unicode(i) + u" " + dkey + u"=" + unicode(d)
                    self.status.showMessage(mssg,1000)
                elif k == 3:
                    self.p3edit.setText(unicode(p))
                    self.i3edit.setText(unicode(i))
                    self.d3edit.setText(unicode(d))                
                    mssg = pkey + u"=" + unicode(p) + u" " + ikey + u"=" + unicode(i) + u" " + dkey + u"=" + unicode(d)
                    self.status.showMessage(mssg,1000)
                elif k == 4:
                    self.p4edit.setText(unicode(p))
                    self.i4edit.setText(unicode(i))
                    self.d4edit.setText(unicode(d))                
                    mssg = pkey + u"=" + unicode(p) + u" " + ikey + u"=" + unicode(i) + u" " + dkey + u"=" + unicode(d)
                    self.status.showMessage(mssg,1000)
                elif k == 5:
                    self.p5edit.setText(unicode(p))
                    self.i5edit.setText(unicode(i))
                    self.d5edit.setText(unicode(d))                
                    mssg = pkey + u"=" + unicode(p) + u" " + ikey + u"=" + unicode(i) + u" " + dkey + u"=" + unicode(d)
                    self.status.showMessage(mssg,1000)
                elif k == 6:
                    self.p6edit.setText(unicode(p))
                    self.i6edit.setText(unicode(i))
                    self.d6edit.setText(unicode(d))                
                    mssg = pkey + u"=" + unicode(p) + u" " + ikey + u"=" + unicode(i) + u" " + dkey + u"=" + unicode(d)
                    self.status.showMessage(mssg,1000)
                elif k == 7:
                    self.p7edit.setText(unicode(p))
                    self.i7edit.setText(unicode(i))
                    self.d7edit.setText(unicode(d))                
                    mssg = pkey + u"=" + unicode(p) + u" " + ikey + u"=" + unicode(i) + u" " + dkey + u"=" + unicode(d)
                    self.status.showMessage(mssg,1000)
            else:
                mssg = u"getallpid(): Unable to read pid values "
                self.status.showMessage(mssg,5000)
                aw.qmc.errorlog.append(mssg)
                return
                
        #read current pidN
        command = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4["selectedpid"][1],1)
        N = aw.pid.readoneword(command)
        if N != -1:
            aw.pid.PXG4["selectedpid"][0] = N

            if N == 1:
                self.radiopid1.setChecked(True)
            elif N == 2:
                self.radiopid2.setChecked(True)
            elif N == 3:
                self.radiopid3.setChecked(True)
            elif N == 4:
                self.radiopid4.setChecked(True)
            elif N == 5:
                self.radiopid5.setChecked(True)
            elif N == 6:
                self.radiopid6.setChecked(True)
            elif N == 7:
                self.radiopid7.setChecked(True)

            mssg = u"PID is using pid = " + unicode(N)
            self.status.showMessage(mssg,5000)
        else:
            mssg = u"getallpid(): Unable to read current sv "
            self.status.showMessage(mssg,5000)
            aw.qmc.errorlog.append(mssg)
            
    def getallsv(self):
        for i in reversed(range(1,8)):
            svkey = u"sv" + unicode(i)
            command = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4[svkey][1],1)
            sv = aw.pid.readoneword(command)/10.
            aw.pid.PXG4[svkey][0] = sv
            if i == 1:
                self.sv1edit.setText(unicode(sv))
                mssg = svkey + u" = " + unicode(sv)
                self.status.showMessage(mssg,1000)
            elif i == 2:
                self.sv2edit.setText(str(sv))
                mssg = svkey + u" = " + unicode(sv)
                self.status.showMessage(mssg,1000)
            elif i == 3:
                mssg = svkey + u" = " + unicode(sv)
                self.status.showMessage(mssg,1000)
                self.sv3edit.setText(unicode(sv))
            elif i == 4:
                mssg = svkey + u" = " + unicode(sv)
                self.status.showMessage(mssg,1000)
                self.sv4edit.setText(str(sv))
            elif i == 5:
                mssg = svkey + u" = " + unicode(sv)
                self.status.showMessage(mssg,1000)
                self.sv5edit.setText(unicode(sv))
            elif i == 6:
                mssg = svkey + u" = " + unicode(sv)
                self.status.showMessage(mssg,1000)
                self.sv6edit.setText(unicode(sv))
            elif i == 7:
                mssg = svkey + u" = " + unicode(sv)
                self.status.showMessage(mssg,1000)
                self.sv7edit.setText(unicode(sv))

        #read current svN
        command = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4["selectsv"][1],1)
        N = aw.pid.readoneword(command)
        aw.pid.PXG4["selectsv"][0] = N

        if N == 1:
            self.radiosv1.setChecked(True)
        elif N == 2:
            self.radiosv2.setChecked(True)
        elif N == 3:
            self.radiosv3.setChecked(True)
        elif N == 4:
            self.radiosv4.setChecked(True)
        elif N == 5:
            self.radiosv5.setChecked(True)
        elif N == 6:
            self.radiosv6.setChecked(True)
        elif N == 7:
            self.radiosv7.setChecked(True)

        mssg = u"PID is using SV = " + unicode(N)
        self.status.showMessage(mssg,5000)
         
    def checkrampsoakmode(self):
        msg = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4["rampsoakmode"][1],1)
        currentmode = aw.pid.readoneword(msg)
        aw.pid.PXG4["rampsoakmode"][0] = currentmode
        if currentmode == 0:
            mode = [u"0",u"OFF",u"CONTINUOUS CONTROL",u"CONTINUOUS CONTROL",u"OFF"]
        elif currentmode == 1:
            mode = [u"1",u"OFF",u"CONTINUOUS CONTROL",u"CONTINUOUS CONTROL",u"ON"]
        elif currentmode == 2:
            mode = [u"2",u"OFF",u"CONTINUOUS CONTROL",u"STANDBY MODE",u"OFF"]
        elif currentmode == 3:
            mode = [u"3",u"OFF",u"CONTINUOUS CONTROL",u"STANDBY MODE",u"ON"]
        elif currentmode == 4:
            mode = [u"4",u"OFF",u"STANDBY MODE",u"CONTINUOUS CONTROL",u"OFF"]
        elif currentmode == 5:
            mode = [u"5",u"OFF",u"STANDBY MODE",u"CONTINUOUS CONTROL",u"ON"]
        elif currentmode == 6:
            mode = [u"6",u"OFF",u"STANDBY MODE",u"STANDBY MODE",u"OFF"]
        elif currentmode == 7:
            mode = [u"7",u"OFF",u"STANDBY MODE",u"STANDBY MODE",u"ON"]
        elif currentmode == 8:
            mode = [u"8",u"ON",u"CONTINUOUS CONTROL",u"CONTINUOUS CONTROL",u"OFF"]
        elif currentmode == 9:
            mode = [u"9",u"ON",u"CONTINUOUS CONTROL",u"CONTINUOUS CONTROL",u"ON"]
        elif currentmode == 10:
            mode = [u"10",u"ON",u"CONTINUOUS CONTROL",u"STANDBY MODE",u"OFF"]
        elif currentmode == 11:
            mode = [u"11",u"ON",u"CONTINUOUS CONTROL",u"STANDBY MODE",u"ON"]
        elif currentmode == 12:
            mode = [u"12",u"ON",u"STANDBY MODE",u"CONTINUOUS CONTROL",u"OFF"]
        elif currentmode == 13:
            mode = [u"13",u"ON",u"STANDBY MODE",u"CONTINUOUS CONTROL",u"ON"]
        elif currentmode == 14:
            mode = [u"14",u"ON",u"STANDBY MODE",u"STANDBY MODE",u"OFF"]
        elif currentmode == 15:
            mode = [u"15",u"ON",u"STANDBY MODE",u"STANDBY MODE",u"ON"]
        else:
            return -1

        string = u"The rampsoak-mode tells how to start and end the ramp/soak\n\n"
        string += u"Your rampsoak mode in this pid is:\n"
        string += u"\nMode = " + mode[0]
        string += u"\n-----------------------------------------------------------------------"
        string += u"\nStart to run from PV value: " + mode[1]
        string += u"\nEnd output status at the end of ramp/soak: " + mode[2]
        string += u"\nOutput status while ramp/soak opearion set to OFF: " + mode[3] 
        string += u"\nRepeat Operation at the end: " + mode[4]
        string += u"\n-----------------------------------------------------------------------"
        string += u"\n\nRecomended Mode = 0\n"
        string += u"\nIf you need to change it, change it now and come back later"
        string += u"\nUse the Parameter Loader Software by Fuji if you need to\n\n"
        string += u"\n\n\nContinue?" 
        
        reply = QMessageBox.question(self,u"Ramp Soak start-end mode",string,
                            QMessageBox.Yes|QMessageBox.Cancel)
        if reply == QMessageBox.Cancel:
            return 0
        elif reply == QMessageBox.Yes:
            return 1  


    def setONOFFrampsoak(self,flag):
        #warning check how it ends at "rampsoakend":[0,41081] can let pid inop till value changed    UNFINISHED
        
        # you can come out of this mode by putting the pid in standby (pid off) 
        #flag =0 OFF, flag = 1 ON, flag = 2 hold
        
        #set rampsoak pattern ON
        if flag == 1:
            check = self.checkrampsoakmode()
            if check == 0:
                self.status.showMessage(u"Ramp/Soak operation cancelled", 5000)
                return
            elif check == -1:
                self.status.showMessage(u"No RX data", 5000)
                
            self.status.showMessage(u"Setting RS ON...",500)

            selectedmode = self.patternComboBox.currentIndex()
            msg = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4["rampsoakpattern"][1],1)
            currentmode = aw.pid.readoneword(msg)
            aw.pid.PXG4["rampsoakpattern"][0] = currentmode
            
            if currentmode != selectedmode:
                #set mode in pid to match the mode selected in the combobox
                self.status.showMessage(u"Need to change pattern mode...",1000)
                command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["rampsoakpattern"][1],selectedmode)
                r = aw.ser.sendFUJIcommand(command,8)
                if len(r) == 8:
                    self.status.showMessage(u"Pattern has been changed. Wait 5 secs.", 500)
                    aw.pid.PXG4["rampsoakpattern"][0] = selectedmode
                    time.sleep(5) #wait 5 seconds to set eeprom memory
                else:
                    self.status.showMessage(u"Pattern could not be changed", 5000)
                    return
            #combobox mode matches pid mode
            #set ramp soak mode ON
            command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["rampsoak"][1],flag)
            r = aw.ser.sendFUJIcommand(command,8)
            if r == command:
                self.status.showMessage(u"RS ON and running...", 5000)
            else:
                self.status.showMessage(u"RampSoak could not be turned ON", 5000)
                
        #set ramp soak OFF       
        elif flag == 0:
            self.status.showMessage(u"setting RS OFF...",500)
            command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["rampsoak"][1],flag)
            r = aw.ser.sendFUJIcommand(command,8)
            if r == command:
                self.status.showMessage(u"RS successfully turned OFF", 5000)
                aw.pid.PXG4["rampsoak"][0] = flag
            else:
                self.status.showMessage("Ramp Soak could not be set OFF", 5000)

    def setpattern(self):
        #Need to make sure that RampSoak is not ON in order to change pattern:
        onoff = self.getONOFFrampsoak()
        if onoff == 0:
            aw.pid.PXG4["rampsoakpattern"][0] = self.patternComboBox.currentIndex()
            command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["rampsoakpattern"][1],aw.pid.PXG4["rampsoakpattern"][0])
            #TX and RX
            r = aw.ser.sendFUJIcommand(command,8)
            #check response from pid and update message on main window
            if r == command:
                patterns = ["1-4","5-8","1-8","9-12","13-16","9-16","1-16"]
                message = u"Pattern changed to " + patterns[aw.pid.PXG4CH4["rampsoakpattern"][0]]

            else:
                message = u"Pattern did not changed"
            aw.messagelabel.setText(message)
        elif onoff == 1:
            aw.messagelabel.setText(u"Ramp/Soak was found ON! Turn it off before changing the pattern")
        elif onoff == 2:
            aw.messagelabel.setText(u"Ramp/Soak was found in Hold! Turn it off before changing the pattern")
          

    def setONOFFstandby(self,flag):
        #standby ON (pid off) will reset: rampsoak modes/autotuning/self tuning
        #flag = 0 standby OFF, flag = 1 standby ON (pid off)
        self.status.showMessage(u"wait...",500)
        command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["runstandby"][1],flag)
        #TX and RX
        r = aw.ser.sendFUJIcommand(command,8)
                        
        if r == command and flag == 1:
            message = u"PID set to OFF"     #put pid in standby 1 (pid on)
            aw.pid.PXG4["runstandby"][0] = 1
        elif r == command and flag == 0:
            message = u"PID set to ON"      #put pid in standby 0 (pid off)
            aw.pid.PXG4["runstandby"][0] = 0
        else:
            message = u"Unable"
        if r:
            self.status.showMessage(message,5000)
        else:
            self.status.showMessage(u"No data received",5000)            


    def getsegment(self, idn):
        svkey = u"segment" + unicode(idn) + u"sv"
        svcommand = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4[svkey][1],1)
        
        sv = aw.pid.readoneword(svcommand)
        if sv == -1:
            return -1
        aw.pid.PXG4[svkey][0] = sv/10.              #divide by 10 because the decimal point is not sent by the PID
    
        rampkey = u"segment" + unicode(idn) + u"ramp"
        rampcommand = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4[rampkey][1],1)
        ramp = aw.pid.readoneword(rampcommand)
        if ramp == -1:
            return -1
        aw.pid.PXG4[rampkey][0] = ramp/10.
        
        soakkey = u"segment" + unicode(idn) + u"soak"
        soakcommand = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4[soakkey][1],1)
        soak = aw.pid.readoneword(soakcommand)
        if soak == -1:
            return -1
        aw.pid.PXG4[soakkey][0] = soak/10.

    #get all Ramp Soak values for all 8 segments                                  
    def getallsegments(self):
        for i in range(1,17):
            msg = u"Reading Ramp/Soak " + unicode(i) + u" ..."
            self.status.showMessage(msg,500)
            k = self.getsegment(i)
            time.sleep(0.03)
            if k == -1:
                self.status.showMessage(u"problem reading Ramp/Soak",5000)
                return
            self.paintlabels()
        self.status.showMessage(u"Finished reading Ramp/Soak val.",5000)

    def setONOFFautotune(self,flag):
        self.status.showMessage(u"setting autotune...",500)
        #read current pidN
        command = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4["selectedpid"][1],1)
        N = aw.pid.readoneword(command)
        aw.pid.PXG4["selectedpid"][0] = N

        string = u"Current pid = " + unicode(N) + u". Proceed with autotune command?"
        reply = QMessageBox.question(self,u"Ramp Soak start-end mode",string,
                            QMessageBox.Yes|QMessageBox.Cancel)
        if reply == QMessageBox.Cancel:
            self.status.showMessage(u"Autotune cancelled",5000)
            return 0
        elif reply == QMessageBox.Yes:
            command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["autotuning"][1],flag)
            #TX and RX
            r = aw.ser.sendFUJIcommand(command,8)
            if len(r) == 8:
                if flag == 0:
                    aw.pid.PXG4["autotuning"][0] = 0
                    self.status.showMessage(u"Autotune successfully turned OFF",5000)
                if flag == 1:
                    aw.pid.PXG4["autotuning"][0] = 1
                    self.status.showMessage(u"Autotune successfully turned ON",5000) 
            else:
                self.status.showMessage(u"UNABLE to set Autotune",5000) 

###################################################################################
##########################  FUJI PID CLASS DEFINITION  ############################
###################################################################################
        
# This class can work for either one Fuji PXR3 or one Fuji PXG4
# NOTE: There is only one controlling PID. The second pid is only used for reading BT and therefore,
# there is no need to create a second PID object since the second pid all it does is read temperature (always same command).
# All is needed for the second pid is its unit id number stored in aw.qmc.device[]. The command to read T is the same for PXR and PXG

class FujiPID(object):
    def __init__(self):
        
                   #Use a python dictionary data container for the parameters of each channel
                   #refer to Fuji PID instruction manual for more information about the parameters and channels
        
        #"KEY": [VALUE,MEMORY ADDRESS]
        self.PXG4={
                  ############ CH1  Selects controller modes 
                  # manual mode 0 = OFF(auto), 1 = ON(manual)
                  "manual": [0,41121],
                  #run or standby 0=OFF(during run), 1 = ON(during standby)
                  "runstandby": [0,41004],
                  #autotuning run command modes available 0=off, 1=on, 2=low
                  "autotuning": [0,41005],
                  #rampsoak command modes available 0=off, 1=run; 2=hold
                  "rampsoak": [0,41082],
                  #select SV sv1,...,sv7
                  "selectsv": [1,41221],
                  #selects PID number behaviour mode: pid1,...,pid7
                  "selectpid": [0,41222],

                  ############ CH2  Main operating pid parameters. 
                  #proportional band  P0 (0% to 999.9%)
                  "p": [5,41006],
                  #integration time i0 (0 to 3200.0 sec)
                  "i": [240,41007],
                  #differential time d0 (0.0 to 999.9 sec)
                  "d": [600,41008],

                   ############ CH3 These are 7 storage locations
                  "sv1": [300.0,41241], "p1": [5,41242], "i1": [240,41243], "d1": [60,41244],
                  "sv2": [350.0,41251], "p2": [5,41252], "i2": [240,41253], "d2": [60,41254],
                  "sv3": [400.0,41261], "p3": [5,41262], "i3": [240,41263], "d3": [60,41264],
                  "sv4": [450.0,41271], "p4": [5,41272], "i4": [240,41273], "d4": [60,41274],
                  "sv5": [500.0,41281], "p5": [5,41282], "i5": [240,41283], "d5": [60,41284],
                  "sv6": [550.0,41291], "p6": [5,41292], "i6": [240,41293], "d6": [60,41294],
                  "sv7": [575.0,41301], "p7": [5,41302], "i7": [240,41303], "d7": [60,41304],
                  "selectedpid":[7,41225],
                  
                  ############# CH4      Creates a pattern of temperatures (profiles) using ramp soak combination
                  #sv stands for Set Value (desired temperature value)
                  #the time to reach sv is called ramp (minutes)
                  #the time to hold the temperature at sv is called soak (minutes)
                  "timeunits": [1,41562],  #0=hh.MM (hour:min)  1=MM.SS (min:sec)
                  # Dry roast phase. selects 3 or 4 minutes
                  "segment1sv": [270.0,41581],"segment1ramp": [3,41582],"segment1soak": [0,41583],
                  "segment2sv": [300.0,41584],"segment2ramp": [3,41585],"segment2soak": [0,41586],
                  "segment3sv": [350.0,41587],"segment3ramp": [3,41588],"segment3soak": [0,41589],
                  "segment4sv": [400.0,41590],"segment4ramp": [3,41591],"segment4soak": [0,41591],
                  # Phase to 1C. selects 6 or 8 mins
                  "segment5sv": [530.0,41593],"segment5ramp": [5,41594],"segment5soak": [0,41595],
                  "segment6sv": [530.0,41596],"segment6ramp": [8,41597],"segment6soak": [0,41598],
                  "segment7sv": [540.0,41599],"segment7ramp": [5,41600],"segment7soak": [0,41601],
                  "segment8sv": [540.0,41602],"segment8ramp": [8,41603],"segment8soak": [0,41604],
                  "segment9sv": [550.0,41605],"segment9ramp": [5,41606],"segment9soak": [0,41607],
                  "segment10sv": [550.0,41608],"segment10ramp": [8,41609],"segment10soak": [0,41610],
                  "segment11sv": [560.0,41611],"segment11ramp": [5,41612],"segment11soak": [0,41613],
                  "segment12sv": [560.0,41614],"segment12ramp": [8,41615],"segment12soak": [0,41616],
                  # finish phase. selects 3 mins for regular coffee or 5 mins for espresso
                  "segment13sv": [570.0,41617],"segment13ramp": [3,41618],"segment13soak": [0,41619],
                  "segment14sv": [570.0,41620],"segment14ramp": [5,41621],"segment14soak": [0,41622],
                  "segment15sv": [580.0,41623],"segment15ramp": [3,41624],"segment15soak": [0,41625],
                  "segment16sv": [580.0,41626],"segment16ramp": [5,41627],"segment16soak": [0,41628],
                  # "rampsoakmode" 0-15 = 1-16 IMPORTANT: Factory setting is 3 (bad). Set it up to number 0 or it will
                  # sit on stanby (SV blinks) at the end till rampsoakmode changes. 
                  "rampsoakmode":[0,41081],
                  "rampsoakpattern": [6,41561],  #ramp soak activation pattern 0=(1-4) 1=(5-8) 2=(1-8) 3=(9-12) 4=(13-16) 5=(9-16) 6=(1-16)
                  
                  ################  CH5    Checks the ramp soak progress, control output, remaining time and other status functions
                  "stat":[41561], #reads only. 0=off,1=1ramp,2=1soak,3=2ramp,4=2soak,...31=16ramp,32=16soak,33=end
        
                  ################  CH6    Sets up the thermocouple type, input range, output range and other items for the controller
                  #input type: 0=NA,1=PT100ohms,2=J,3=K,4=R,5=B,6=S,7=T,8=E,12=N,13=PL2,15=(0-5volts),16=(1-5V),17=(0-10V),18=(2-10V),19=(0-100mV)
                  "pvinputtype": [3,41016],
                  "pvinputlowerlimit":[0,41018],
                  "pvinputupperlimit":[9999,41019],
                  "decimalposition": [1,41020],
                  "unitdisplay":[1,41345],         #0=Celsius; 1=Fahrenheit
                  
                  #################  CH7    Assigns functions for DI (digital input), DO (digital output), LED lamp and other controls
                  "rampslopeunit":[1,41432], #0=hour,1=min
                  "controlmethod":[0,41002],  #0=pid,2=fuzzy,2=self,3=pid2


                  #################  CH8     Sets the defect conditions for each type of alarm
                  #################  CH9     Sets the station number id and communication parameters of the PID controller
                  #################  CH10    Changes settings for valve control (here using SSR and not valve)
                  #################  CH11    Sets passwords
                  #################  CH12    Sets the parameters mask functions to hide parameters from the user, Sv0 = currently selected sv value in display

                  ################# READ ONLY MEMORY 
                  "pv?":[31001],"sv?":[0,31002],"alarm?":[31007],"fault?":[31008],"stat?":[31041]
                  }

        # "KEY": [VALUE,MEMORY ]
        self.PXR = {"autotuning":[0,41005],
                    "segment1sv":[100.0,41057],"segment1ramp":[3,41065],"segment1soak":[0,41066],
                    "segment2sv":[100.0,41058],"segment2ramp":[3,41067],"segment2soak":[0,41068],
                    "segment3sv":[100.0,41059],"segment3ramp":[3,41069],"segment3soak":[0,41070],
                    "segment4sv":[100.0,41060],"segment4ramp":[3,41071],"segment4soak":[0,41072],
                    "segment5sv":[100.0,41061],"segment5ramp":[3,41073],"segment5soak":[0,41074],
                    "segment6sv":[100.0,41062],"segment6ramp":[3,41075],"segment6soak":[0,41076],
                    "segment7sv":[100.0,41063],"segment7ramp":[3,41077],"segment7soak":[0,41078],
                    "segment8sv":[100.0,41064],"segment8ramp":[3,41079],"segment8soak":[0,41080],
                    #Tells what to do after finishing or how to start. See documentation under ramp soak pattern: 0-15 
                    "rampsoakmode":[0,41081],
                    #rampsoak command 0=OFF, 1= RUN, 2= HALTED, 3=END
                    "rampsoak":[0,41082],
                    #ramp soak pattern. 0=executes 1 to 4; 1=executes 5 to 8; 2=executes 1 to 8
                    "rampsoakpattern":[0,41083],
    
                    #PID=0,FUZZY=1,SELF=2
                    "controlmethod":[0,41002],
                    #sv set value
                    "sv0":[0,41003],
                    # run standby 0=RUN 1=STANDBY
                    "runstandby": [0,41004],
                    "p":[0,41006],
                    "i":[0,41007],
                    "d":[0,41008],
                    "decimalposition": [1,41020],
                    "svlowerlimit":[0,41031],
                    "svupperlimit":[0,41032],
                    
                    #READ ONLY
                    #current pv
                    "pv?":[0,31001],
                    #current sv on display (during ramp soak it changes)
                    "sv?":[0,31002],
                    #rampsoak current running position (0-17)
                    "segment?":[0,31009]
                    }
                    
                    
                      
    ##TX/RX FUNCTIONS
    #This function reads read-only memory (with 3xxxx memory we need function=4)
    #both PXR3 and PXG4 use the same memory location 31001 (3xxxx = read only)
    def gettemperature(self, stationNo):
        #we compose a message then we send it by using self.readoneword()
        return  self.readoneword(self.message2send(stationNo,4,31001,1))

    #activates the PID SV buttons in the main window to adjust the SV value. Called from the PID control pannels/SV tab
    def activateONOFFeasySV(self,flag):
        #turn off
        if flag == 0:            
            aw.button_12.setDisabled(True)
            aw.button_13.setDisabled(True)
            aw.button_14.setDisabled(True)
            aw.button_15.setDisabled(True)
            aw.button_16.setDisabled(True)
            aw.button_17.setDisabled(True)            
            aw.button_12.setFlat(True)
            aw.button_13.setFlat(True)
            aw.button_14.setFlat(True)
            aw.button_15.setFlat(True)
            aw.button_16.setFlat(True)
            aw.button_17.setFlat(True)
            
        #turn on
        elif flag == 1:
            A = QLabel()
            reply = QMessageBox.question(A,u"Activate PID front buttons",
                                         u"Remember SV memory has a finite\nlife of ~10,000 writes.\n\nProceed?",
                                         QMessageBox.Yes|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return 
            elif reply == QMessageBox.Yes:
                aw.button_12.setDisabled(False)
                aw.button_13.setDisabled(False)
                aw.button_14.setDisabled(False)
                aw.button_15.setDisabled(False)
                aw.button_16.setDisabled(False)
                aw.button_17.setDisabled(False)            
                aw.button_12.setFlat(False)
                aw.button_13.setFlat(False)
                aw.button_14.setFlat(False)
                aw.button_15.setFlat(False)
                aw.button_16.setFlat(False)
                aw.button_17.setFlat(False)
                

    def readcurrentsv(self):
        #if control pid is fuji PXG4
        if aw.ser.controlETpid[0] == 0:        
            command = self.message2send(aw.ser.controlETpid[1],4,self.PXG4["sv?"][1],1)
            val = float(self.readoneword(command)/10.)
            if val != -0.1:
                aw.lcd6.display(val)
                return val
            else:
                return -1

        #or if control pid is fuji PXR3
        elif aw.ser.controlETpid[0] == 1:
            command = self.message2send(aw.ser.controlETpid[1],4,self.PXR["sv?"][1],1)
            val = float(self.readoneword(command)/10.)
            if val != -0.1:
                self.PXR["sv"][0] =  val
                aw.lcd6.display(aw.pid.PXR["sv"][0])
                return aw.pid.PXR["sv"][0]
            else:
                return -1
            
    def adjustsv(self,diff):
        currentsv = self.readcurrentsv()
        if currentsv != -1:
            newsv = int((currentsv + diff)*10.)          #multiply by 10 because we use a decimal point          

            #   if control pid is fuji PXG4
            if aw.ser.controlETpid[0] == 0:
                # read the current svN (1-7) being used
                command = aw.pid.message2send(aw.ser.controlETpid[1],3,self.PXG4["selectsv"][1],1)
                N = aw.pid.readoneword(command)
                if N != -1:
                    self.PXG4["selectsv"][0] = N
                    svkey = u"sv" + unicode(N)
                    command = self.message2send(aw.ser.controlETpid[1],6,self.PXG4[svkey][1],newsv)
                    r = aw.ser.sendFUJIcommand(command,8)
                    if len(r) == 8:
                        message = u"SV" + unicode(N) + u" changed from " + unicode(currentsv) + u" to " + unicode(newsv/10.)
                        aw.messagelabel.setText(message)
                        aw.lcd6.display(newsv/10.)
                        self.PXG4[svkey][0] = newsv
                        
                    else:
                        msg = u"Unable to set sv" + unicode(N)
                        aw.messagelabel.setText(msg)       

            #   or if control pid is fuji PXR3
            elif aw.ser.controlETpid[0] == 1:
                command = self.message2send(aw.ser.controlETpid[1],6,self.PXR["sv0"][1],newsv)
                r = aw.ser.sendFUJIcommand(command,8)
                if len(r) == 8:
                    message = u" SV changed from " + unicode(currentsv) + u" to " + unicode(newsv/10.)
                    aw.messagelabel.setText(message)
                    aw.lcd6.display(newsv/10.)
                    self.PXR["sv"][0] = newsv
                else:
                    aw.messagelabel.setText(u"Unable to set sv")
        else:
            aw.messagelabel.setText(u"Unable to set new sv")

    def dec2HexRaw(self,decimal):
        # This method converts a decimal to a raw string appropiate for Fuji serial TX
        # Used to compose serial messages
        Nbytes = []
        while decimal:
           decimal, rem = divmod(decimal, 256)
           Nbytes.append(rem)
        Nbytes.reverse()
        if not Nbytes:
            Nbytes.append(0)
        #print Nbytes
        return  "".join(chr(b) for b in Nbytes)                

    def message2send(self, stationNo, FunctionCode, memory, Nword):
        # This method takes the arguments to compose a Fuji serial command and returns the complete raw string with crc16 included
        # memory must be given as the Resistor Number Engineering unit (example of memory = 41057 )

        #check to see if Nword is < 257. If it is, then add extra zero pad. 2^8 = 256 = 1 byte but 2 bytes always needed to send Nword
        if Nword < 257:
            pad1 = self.dec2HexRaw(0)
        else:
            pad1 = ""
        
        part1 = self.dec2HexRaw(stationNo)
        part2 = self.dec2HexRaw(FunctionCode)
        p,r = divmod(memory,10000)
        part3 = self.dec2HexRaw(r - 1)    
        part4 = self.dec2HexRaw(Nword)
        datastring = part1 + part2 + part3 + pad1 + part4
        
        # calculate the crc16 of all this data string
        crc16int = self.fujiCrc16(datastring)

        #convert crc16 to hex string to change the order of the 2 bytes from AB.CD to CD.AB to match Fuji requirements
        crc16hex= hex(crc16int)[2:]

        #we need 4 chars but sometimes we get only three or two because of abreviations by hex(). Therefore, add "0" if needed.
        ll = 4 - len(crc16hex)
        pad =["","0","00","000"]
        crc16hex = pad[ll] + crc16hex
        
        #change now from AB.CD to CD.AB and convert from hex string to int
        crc16end = int(crc16hex[2:]+crc16hex[:2],16)

        #now convert the crc16 from int to binary
        part5 = self.dec2HexRaw(crc16end)
        #return total sum of binary parts  (assembled message)
        return (datastring + part5)
    
    #input string command. Output integer (not binary string); used for example to read temperature or to obtain the value of a variable
    def readoneword(self,command):
        #takes an already formated command to read 1 word data and returns the response from the pid
        #SEND command and RECEIVE 7 bytes back
        r = aw.ser.sendFUJIcommand(command,7)
        if len(r) == 7:      
            # EVERYTHINK OK: convert data part binary string to hex representation
            s1 = binascii.hexlify(r[3] + r[4])
            #conversion from hex to dec
            return int(s1,16)
        else:
            #bad number of RX bytes 
            errorcode = u"pid.readoneword(): %i RX bytes received (7 needed) for unit ID=%i" %(len(r),ord(command[0]))
            aw.messagelabel.setText(errorcode)
            aw.qmc.errorlog.append(errorcode)            
            return -1

    #FUJICRC16 function calculates the CRC16 of the data. It expects a binary string as input and returns and int
    def fujiCrc16(self,string):  
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
            tmp = cr ^(ord(j))
            cr =(cr >> 8)^crc16tab[(tmp & 0xff)]

        return cr
        
###########################################################################################################################################
###########################################################################################################################################

app = QApplication(sys.argv)
app.setApplicationName("Artisan")                                       #needed by QSettings() to store windows geometry in operating system
app.setOrganizationName("YourQuest")                                    #needed by QSettings() to store windows geometry in operating system
app.setOrganizationDomain("questm3.groups.google.com")                  #needed by QSettings() to store windows geometry in operating system 
if platf == 'Windows':
    app.setWindowIcon(QIcon("artisan.png"))
aw = ApplicationWindow()
aw.show()
app.exec_()

##############################################################################################################################################
##############################################################################################################################################
