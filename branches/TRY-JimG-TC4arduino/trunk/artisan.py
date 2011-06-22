#!/usr/bin/env python

__version__ = u"0.5.1"


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
# 2) http://ftp3.ie.freebsd.org/pub/trolltech/pub/qt/source/qt-win-opensource-4.7.1-mingw.exe
# add to Path environment variable the bin directory of Qt. Example ;C:\Qt\14.7.1\bin

#   JAVA TO SUPPORT PYSERIAL LIBRARY
# 3) Java JDK or JRE:  http://java.sun.com/javase/downloads/index.jsp
# 4) javacomm: http://www.xpl4java.org/xPL4Java/javacomm.html
# follow the instruction in the README file. Copy and paste files as instructed

#  PYTHON 2.6.6
# 5) python 2.6: http://www.python.org/ftp/python/2.6.6/python-2.6.6.msi
# (add to Path the environment variable the bin directory of Python. Example ;E:\Python26

#   EXTRA PYTHON LIBRARIES NEEDED (install after installing python 2.6.6)
# 6) pyserial for python 2.6: http://sourceforge.net/projects/pyserial/files/pyserial/2.5/pyserial-2.5-rc1.win32.exe/download
# 7) http://sourceforge.net/projects/numpy/files/NumPy/1.5.1/numpy-1.5.1-win32-superpack-python2.6.exe/download
# 8) http://sourceforge.net/projects/scipy/files/scipy/0.9.0rc1/scipy-0.9.0rc1-win32-superpack-python2.6.exe/download
# 9) http://sourceforge.net/projects/matplotlib/files/matplotlib/matplotlib-1.0.1/matplotlib-1.0.1.win32-py2.6.exe/download
# 10) pyqt4 for python 2.6: http://www.riverbankcomputing.co.uk/static/Downloads/PyQt4/PyQt-Py2.6-x64-gpl-4.8.3-1.exe
 
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
import time as libtime
import glob
import os
import warnings
import string as libstring
import cgi
import codecs
import numpy
import array
import struct
from scipy import fft
from scipy import interpolate as inter
 
from PyQt4.QtGui import (QLayout, QAction, QApplication,QWidget,QMessageBox,QLabel,QMainWindow,QFileDialog,QInputDialog,QGroupBox,QDialog,QLineEdit,
                         QSizePolicy,QGridLayout,QVBoxLayout,QHBoxLayout,QPushButton,QDialogButtonBox,QLCDNumber,QKeySequence,QSpinBox,QComboBox,
                         QSlider,QDockWidget,QTabWidget,QStackedWidget,QTextEdit,QTextBlock,QPrintDialog,QPrinter,QPalette,QImage,
                         QPixmap,QColor,QColorDialog,QPalette,QFrame,QImageReader,QRadioButton,QCheckBox,QDesktopServices,QIcon,
                         QStatusBar,QRegExpValidator,QDoubleValidator,QIntValidator,QPainter,QImage,QFont,QBrush,QRadialGradient,
                         QStyleFactory,QTableWidget,QTableWidgetItem,QMenu,QCursor,QDoubleSpinBox )
from PyQt4.QtCore import (QLibraryInfo,QTranslator,QLocale,QFileInfo,Qt,PYQT_VERSION_STR, QT_VERSION_STR,SIGNAL,QTime,QTimer,QString,QFile,QIODevice,QTextStream,QSettings,SLOT,
                          QRegExp,QDate,QUrl,QDir,QVariant,Qt,QPoint,QRect,QSize,QStringList,QEvent,QDateTime,QThread,QMutex)
from PyQt4.QtNetwork import (QHostAddress, QTcpServer, QTcpSocket)


from matplotlib.figure import Figure
from matplotlib.colors import cnames as cnames
import matplotlib.patches as patches
import matplotlib.transforms as transforms
import matplotlib.font_manager as font_manager
import matplotlib.path as mpath
import matplotlib.ticker as ticker
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
import matplotlib as mpl
	
platf = unicode(platform.system())


#######################################################################################
#################### Main Application  ################################################
#######################################################################################

app = QApplication(sys.argv)
app.setApplicationName("Artisan")                                       #needed by QSettings() to store windows geometry in operating system
app.setOrganizationName("YourQuest")                                    #needed by QSettings() to store windows geometry in operating system
app.setOrganizationDomain("p.code.google.com")                          #needed by QSettings() to store windows geometry in operating system 
if platf == 'Windows':
    app.setWindowIcon(QIcon("artisan.png"))

#Localization support
settings = QSettings()
locale = settings.value('locale').toString()
if locale == "":
    locale = QLocale.system().name()
    settings.setValue('locale', locale)

qtTranslator = QTranslator()
#load Qt default translations from QLibrary
if qtTranslator.load("qt_" + locale, QLibraryInfo.location(QLibraryInfo.TranslationsPath)): 
    app.installTranslator(qtTranslator)
#find Qt default translations in Mac binary
elif qtTranslator.load("qt_" + locale, QApplication.applicationDirPath() + "/../translations"):
    app.installTranslator(qtTranslator)
#load Artisan translations
appTranslator = QTranslator()
#find application translations in source folder
if appTranslator.load("artisan_" + locale, "translations"): 
    app.installTranslator(appTranslator)
#find application translations in Mac binary
elif appTranslator.load("artisan_" + locale, QApplication.applicationDirPath() + "/../translations"):
    app.installTranslator(appTranslator)
    
#Constants with translations have to be loaded after the translations
from const import UIconst
    
#######################################################################################
#################### GRAPH DRAWING WINDOW  ############################################
#######################################################################################
  
        	
class tgraphcanvas(FigureCanvas):
    def __init__(self,parent):

        #default palette of colors
        self.palette = {"background":u'white',"grid":u'green',"ylabel":u'black',"xlabel":u'black',"title":u'black',"rect1":u'green',
                        "rect2":u'orange',"rect3":u'#996633',"et":u'red',"bt":u'#00007f',"deltaet":u'orange',
                        "deltabt":u'blue',"markers":u'black',"text":u'black',"watermarks":u'yellow',"Cline":u'blue'}
        
        self.artisanflavordefaultlabels = [QApplication.translate("Textbox", "Acidity",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "After Taste",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Clean Cup",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Head",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Fragance",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Sweetness",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Aroma",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Balance",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Body",None, QApplication.UnicodeUTF8)]

        self.SCCAflavordefaultlabels = [QApplication.translate("Textbox", "Sour",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Flavor",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Critical\nStimulus",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Aftertaste",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Bitter",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Astringency",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Solubles\nConcentration",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Mouthfeel",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Other",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Aromatic\nComplexity",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Roast\nColor",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Aromatic\nPungency",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Sweet",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Acidity",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "pH",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Balance",None, QApplication.UnicodeUTF8)]


        self.CQIflavordefaultlabels =  [QApplication.translate("Textbox", "Fragance",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Aroma",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Flavor",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Acidity",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Body",None, QApplication.UnicodeUTF8),
                                        QApplication.translate("Textbox", "Aftertaste",None, QApplication.UnicodeUTF8)]

        self.SweetMariasflavordefaultlabels = [QApplication.translate("Textbox", "Dry Fragrance",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Uniformity",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Complexity",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Clean Cup",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Sweetness",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Finished",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Body",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Flavor",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Brightness",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Wet Aroma",None, QApplication.UnicodeUTF8)]
        
        self.Cflavordefaultlabels = [QApplication.translate("Textbox", "Fragrance",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Aroma",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Taste",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Nose",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Aftertaste",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Body",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Acidity",None, QApplication.UnicodeUTF8)]
        
        self.Eflavordefaultlabels = [QApplication.translate("Textbox", "Fragrance-Aroma",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Acidity",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Flavor",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Body",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Aftertaste",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Balance",None, QApplication.UnicodeUTF8)]


        self.coffeegeekflavordefaultlabels = [QApplication.translate("Textbox", "Aroma",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Acidity",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Mouthfeel",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Flavour",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Aftertaste",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Balance",None, QApplication.UnicodeUTF8)]


        self.Intelligentsiaflavordefaultlabels = [QApplication.translate("Textbox", "Sweetness",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Acidity",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Body",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Finish",None, QApplication.UnicodeUTF8)]

        self.IstitutoInternazionaleAssaggiatoriCaffe = [QApplication.translate("Textbox", "Roast Color",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Crema Texture",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Crema Volume",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Fragrance",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Body",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Acidity",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Bitterness",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Defects",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Aroma Intensity",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Aroma Persistence",None, QApplication.UnicodeUTF8),
                                            QApplication.translate("Textbox", "Balance",None, QApplication.UnicodeUTF8)]


        
        self.flavorlabels = list(self.artisanflavordefaultlabels)
        #Initial flavor parameters. 
        self.flavors = [5.,5.,5.,5.,5.,5.,5.,5.,5.]
        self.flavorstartangle = 90

        #F = Fahrenheit; C = Celsius
        self.mode = u"F"
        self.errorlog = []

        # default delay between readings in miliseconds
        self.delay = 1000

        #watermarks limits: dryphase1, dryphase2, midphase, and finish phase Y limits
        self.phases_fahrenheit_defaults = [200,300,390,450]
        self.phases_celsius_defaults = [95,150,200,230]
        self.phases = list(self.phases_fahrenheit_defaults)
        #this flag makes the main push buttons DryEnd, and FCstart change the phases[1] and phases[2] respectively
        self.phasesbuttonflag = 0 #0 no change; 1 make the DRY and FC buttons change the phases during roast automatically

        #statistics flags selects to display: stat. time, stat. bar, stat. flavors, stat. area
        self.statisticsflags = [1,1,1,1]
        #conditions to estimate bad flavor:dry[min,max],mid[min,max],finish[min,max] in seconds
        self.statisticsconditions = [180,360,180,600,180,360]
        #records length in seconds of total time [0], dry phase [1],mid phase[2],finish phase[3]
        self.statisticstimes = [0,0,0,0]

        #DEVICES
        self.device = 18                                    # default device selected to None (18)
        self.devices = ["Omega HH806AU",                    # device labels (used in Dialog config)
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
                       "EXTECH 421509",
                       "Omega HH802U",
                       "Omega HH309",
                       "NONE",
                       "+ArduinoTC4",
                       "TE VA18B",
                       "+309_34",
                       "+FUJI DUTY %",
                       "Omega HHM28[6]",
                       "+204_34",
                       "+Virtual" 
                       ]

        #extra devices
        self.extradevices = []                                      # list with indexes for extra devices
        self.extratimex = []                                        # individual time for each extra device (more accurate). List of lists (2 dimension)
        self.extradevicecolor1 = []                                 # extra line 1 color. list with colors. 
        self.extradevicecolor2 = []                                 # extra line 2 color. list with colors.
        self.extratemp1,self.extratemp2 = [],[]                     # extra temp1, temp2. List of lists
        self.extratemp1lines,self.extratemp2lines = [],[]           # lists with extra lines for speed drawing
        self.extraname1,self.extraname2 = [],[]                     # name of labels for line (like ET or BT) - legend
        self.extramathexpression1,self.extramathexpression2 = [],[]           # list with user defined math evaluating strings. Example "2*cos(x)"

        #holds math expressions to plot
        self.plotcurves=[u"",u"",u"",u"",u"",u""]
        self.plotcurvecolor = [u"black",u"black",u"black",u"black",u"black",u"black"]
 
        self.fig = Figure() 
            
        #figure back color
        if platf == 'Darwin':
            self.backcolor ="#EEEEEE"
        else:
            self.backcolor = "white"
        self.fig.patch.set_facecolor(self.backcolor)
        self.fig.patch.set_edgecolor(self.backcolor)
        
        self.ax = self.fig.add_subplot(111, axisbg= self.palette["background"])
        
        #legend location
        self.legendloc = 2
        self.fig.subplots_adjust(
            # all values in percen            top=0.93, # the top of the subplots of the figure (default: 0.9)
            bottom=0.1, # the bottom of the subplots of the figure (default: 0.1)
            left=0.068, # the left side of the subplots of the figure (default: 0.125)
            right=.95) # the right side of the subplots of the figure (default: 0.9
        FigureCanvas.__init__(self, self.fig)

        # set the parent widget
        self.setParent(parent)
        # we define the widget as 
        FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)

        # the rate of chage of temperature
        self.rateofchange1 = 0.0
        self.rateofchange2 = 0.0
        
        # multiplication factor to increment sensitivity of rateofchange
        self.sensitivity = 10 # was 20
        #read and plot on/off flag
        self.flagon = False
        #log flag that tells to log ET when using device 18 (manual mode)
        self.manuallogETflag = 0
        
        self.roastpropertiesflag = 1  #resets roast properties if not zero
        self.title = QApplication.translate("Scope Title", "Roaster Scope",None, QApplication.UnicodeUTF8)
        self.ambientTemp = 0.
        #relative humidity percentage [0], corresponding temperature [1], temperature unit [2]
        self.bag_humidity = [0.,0.]

        #list to store the time of each reading. Most IMPORTANT variable.
        self.timex = []

        #lists to store temps and rates of change. Second most IMPORTANT variables. All need same dimension.
        #self.temp1 = ET ; self.temp2 = BT; self.delta1 = deltaMET; self.delta2 = deltaBT
        self.temp1,self.temp2,self.delta1, self.delta2 = [],[],[],[]        
        self.unfiltereddelta1, self.unfiltereddelta2 = [],[]
        
        #indexes for START[0],Dryend[1],FCs[2],FCe[3],SCs[4],SCe[5], and DROP[6]
        #Example: Use as self.timex[self.timeindex[1]] to get the time of DryeEnd
        #Example: Use self.temp2[self.timeindex[4]] to get the BT temperature of SCs
        
        self.timeindex = [-1,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actal index used

        #applies a Y(x) function to ET or BT 
        self.ETfunction,self.BTfunction = u"",u""           

        #prevents accidentally deleting a finished profile. Activated at [DROP]
        self.safesaveflag = False

        #background profile
        self.background = False
        self.backgroundDetails = False
        self.backgroundeventsflag = False
        self.backgroundpath = ""
        self.temp1B,self.temp2B,self.timeB = [],[],[]
        self.timeindexB = [-1,0,0,0,0,0,0]
        self.backgroundEvents = [] #indexes of background events
        self.backgroundEtypes = []
        self.backgroundEvalues = []
        self.backgroundEStrings = []
        self.backgroundalpha = 0.3
        self.backgroundwidth = 2
        self.backgroundmetcolor = self.palette["et"]
        self.backgroundbtcolor = self.palette["bt"]
        self.backgroundstyle = "-"
        self.backmoveflag = 1
        self.detectBackgroundEventTime = 20 #seconds    	
        self.backgroundReproduce = False
        self.Betypes = [QApplication.translate("Scope Annotation", "None",None, QApplication.UnicodeUTF8),
                        QApplication.translate("Scope Annotation", "Power",None, QApplication.UnicodeUTF8),
                        QApplication.translate("Scope Annotation", "Damper",None, QApplication.UnicodeUTF8),
                        QApplication.translate("Scope Annotation", "Fan",None, QApplication.UnicodeUTF8)]
        self.backgroundFlavors = []
        self.flavorbackgroundflag = False
        
        # projection variables of change of rate
        self.HUDflag = 0
        self.ETtarget = 350
        self.BTtarget = 250
        self.hudETpid = [20,60,13]    # HUD pid: p = 20, i = 60, d = 13
        self.pidpreviouserror = 0  # temporary storage of pid error

        #General notes. Accessible through "edit graph properties" of graph menu. WYSIWYG viewer/editor.
        self.roastertype = u""
        self.operator = u""
        self.roastingnotes = u""
        self.cuppingnotes = u""
        self.roastdate = QDate.currentDate()
        self.beans = u""

        #flags to show projections, draw Delta ET, and draw Delta BT        
        self.projectFlag = False
        self.DeltaETflag = False
        self.DeltaBTflag = False
        self.deltafilter = 5

        # projection variables of change of rate
        self.projectionconstant = 1
        self.projectionmode = 0     # 0 = linear; 1 = newton
        
        #[0]weight in, [1]weight out, [2]units (string)
        self.weight = [0,0,u"g"]
        #[0]volume in, [1]volume out, [2]units (string)
        self.volume = [0,0,u"l"]
        #[0]probe weight, [1]weight unit, [2]probe volume, [3]volume unit
        self.density = [0,u"g",0,u"l"]
        
        #stores _indexes_ of self.timex to record events. Use as self.timex[self.specialevents[x]] to get the time of an event
        # use self.temp2[self.specialevents[x]] to get the BT temperature of an event.
        self.specialevents = []
        #ComboBox text event types. They can be modified in eventsDlg()
        self.etypes = [QApplication.translate("ComboBox", "None",None, QApplication.UnicodeUTF8),
                       QApplication.translate("ComboBox", "Power",None, QApplication.UnicodeUTF8),
                       QApplication.translate("ComboBox", "Damper",None, QApplication.UnicodeUTF8),
                       QApplication.translate("ComboBox", "Fan",None, QApplication.UnicodeUTF8)]
        #default etype settings to restore 
        self.etypesdefault = [QApplication.translate("ComboBox", "None",None, QApplication.UnicodeUTF8),
                              QApplication.translate("ComboBox", "Power",None, QApplication.UnicodeUTF8),
                              QApplication.translate("ComboBox", "Damper",None, QApplication.UnicodeUTF8),
                              QApplication.translate("ComboBox", "Fan",None, QApplication.UnicodeUTF8)]
        #stores the type of each event as index of self.etypes. None = 0, Power = 1, etc. 
        self.specialeventstype = []
        #stores text string descriptions for each event. 
        self.specialeventsStrings = []
        #event values are from 0-10
        self.eventsvalues =  [u"",u"0",u"1",u"2",u"3",u"4",u"5",u"6",u"7",u"8",u"9",u"10"]
        #stores the value for each event
        self.specialeventsvalue = []
        #flag that makes the events location type bars (horizontal bars) appear on the plot. flag read on redraw()
        self.eventsGraphflag = 1
        #flag that shows events in the graph
        self.eventsshowflag = 1

        #Temperature Alarms lists. Data is writen in  alarmDlg 
        self.alarmtime = []    # times after which each alarm becomes efective. Usage: self.timeindex[self.alarmtime[i]]
        self.alarmflag = []    # 0 = OFF; 1 = ON flags
        # alarmstate is set to 'not triggered' on reset()
        self.alarmstate = []   # 1=triggered, 0=not triggered. Needed so that the user does not have to turn the alarms ON next roast after alarm being used once.
        self.alarmsource = []   # 0 = ET , 1= BT
        self.alarmtemperature = []  # set temperature number (example 500)
        self.alarmaction = []       # 0 = open a window; 1 = call program with a filepath equal to alarmstring
        self.alarmstrings = []      # text descriptions, action to take, or filepath to call another program
        
        # set initial limits for X and Y axes. But they change after reading the previous seetings at aw.settingsload()
        self.ylimit = 750
        self.ylimit_min = 0        
        self.endofx = 60
        self.startofx = 0
        self.keeptimeflag = 1
        self.xgrid = 120   #initial time separation; 120 = 2 minutes        
        self.ygrid = 50    #initial temperature separation
        self.gridstyles =    ["-","--","-.",":"," "]  #solid,dashed,dash-dot,dotted,None
        self.gridlinestyle = 0
        self.gridthickness = 1
        self.gridalpha = .3
        self.xrotation = 0
        
        #height of statistics bar
        self.statisticsheight = 650
        self.statisticsupper = 655
        self.statisticslower = 617

        # autosave
        self.autosaveflag = 0
        self.autosaveprefix = QApplication.translate("Autosave Prefix", "edit-text",None, QApplication.UnicodeUTF8)
        self.autosavepath = u""
        
        #used to place correct height of text to avoid placing text over text (annotations)
        self.ystep = 45
        
        self.ax.set_xlim(self.startofx, self.endofx)
        self.ax.set_ylim(self.ylimit_min,self.ylimit)

        # disable figure autoscale
        self.ax.set_autoscale_on(False)

        #set grid + axle labels + title
        self.ax.grid(True,color=self.palette["grid"],linestyle = self.gridstyles[self.gridlinestyle],linewidth = self.gridthickness,alpha = self.gridalpha)
            
        self.ax.set_ylabel(self.mode,size=16,color = self.palette["ylabel"])
        self.ax.set_xlabel(u'Time',size=16,color = self.palette["xlabel"])
        self.ax.set_title(self.title,size=20,color=self.palette["title"])

        #put a right tick on the graph
        for tick in self.ax.yaxis.get_major_ticks():
            tick.label2On = True

        #change label colors
        for label in self.ax.yaxis.get_ticklabels():
            label.set_color(self.palette["ylabel"])

        for label in self.ax.xaxis.get_ticklabels():
            label.set_color(self.palette["xlabel"])            
        

        # generates first "empty" plot (lists are empty) of temperature and deltaT
        self.l_temp1, = self.ax.plot(self.timex, self.temp1,color=self.palette["et"],linewidth=2,label=unicode(QApplication.translate("Scope Label", "ET", None, QApplication.UnicodeUTF8)))
        self.l_temp2, = self.ax.plot(self.timex, self.temp2,color=self.palette["bt"],linewidth=2,label=unicode(QApplication.translate("Scope Label", "BT", None, QApplication.UnicodeUTF8)))
        self.l_delta1, = self.ax.plot(self.timex, self.delta1,color=self.palette["deltaet"],linewidth=2,label=unicode(QApplication.translate("Scope Label", "DeltaET", None, QApplication.UnicodeUTF8)))
        self.l_delta2, = self.ax.plot(self.timex, self.delta2,color=self.palette["deltabt"],linewidth=2,label=unicode(QApplication.translate("Scope Label", "DeltaBT", None, QApplication.UnicodeUTF8)))

        # add legend to plot.
        handles = [self.l_temp1,self.l_temp2,self.l_delta1,self.l_delta2]
        labels = [QApplication.translate("Scope Label", "ET", None, QApplication.UnicodeUTF8),QApplication.translate("Scope Label", "BT", None, QApplication.UnicodeUTF8),QApplication.translate("Scope Label", "DeltaET", None, QApplication.UnicodeUTF8),QApplication.translate("Scope Label", "DeltaBT", None, QApplication.UnicodeUTF8)]
        self.ax.legend(handles,labels,loc=self.legendloc,ncol=4,prop=font_manager.FontProperties(size=10),fancybox=True)

        #Create x axis labels in minutes:seconds instead of seconds
        self.xaxistosm()

        ###########################  TIME  CLOCK     ##########################        
        # create an object time to measure and record time (in miliseconds) 
    
        self.timeclock = QTime()
        self.timeclock.setHMS(0,0,0,0)

        ############################  Thread Server #################################################
        #server that spawns a thread dynamically to sample temperature (press button ON to make a thread press OFF button to kill it) 
        self.threadserver = Athreadserver()
    	
        ##########################     Designer variables       #################################
        self.designerflag = False
        self.designerconnections = [0,0,0,0]   #mouse event ids
        self.mousepress = None
        self.indexpoint = 0
        self.workingline = 2  #selects ET or BT
        self.eventtimecopy = []
        self.specialeventsStringscopy = []
        self.specialeventsvaluecopy = []
        self.specialeventstypecopy = []
        self.currentx = 0               #used to add point when right click
        self.currenty = 0               #used to add point when right click
        self.designertimeinit = [50,300,540,560,660,700,800]
        if self.mode == u"C":
                                      #CH, DE, Fcs,Fce,Scs,Sce,Drop  
            self.designertemp1init = [290,290,290,290,290,290,290]
            self.designertemp2init = [200,150,200,210,220,225,240]   #CHARGE,DRY END,FCs, FCe,SCs,SCe,DROP
        elif self.mode == u"F":
            self.designertemp1init = [500,500,500,500,500,500,500]
            self.designertemp2init = [380,300,390,395,410,412,420]
        self.BTsplinedegree = 3
        self.ETsplinedegree = 1
        self.reproducedesigner = 0      #flag to add events to help reproduce (replay) the profile: 0 = none; 1 = sv; 2 = ramp

        ###########################         wheel graph variables     ################################
        #data containers for wheel
        self.wheelnames,self.segmentlengths,self.segmentsalpha,self.wheellabelparent,self.wheelcolor = [],[],[],[],[]

        #crerate starting wheel
        wheels = [4,6,12,50]
        for i in range(len(wheels)):
            w,a,c,co = [],[],[],[]
            for x in range(wheels[i]):
                w.append("W%i %i"%(i+1,x+1))
                a.append(0.3)
                c.append(0)
                color = QColor()
                color.setHsv((360/wheels[i])*x,255,255,255)
                co.append(unicode(color.name()))

            self.wheelnames.append(w)
            self.segmentsalpha.append(a)
            self.segmentlengths.append([100./len(self.wheelnames[i])]*len(self.wheelnames[i]))
            self.wheellabelparent.append(c)
            self.wheelcolor.append(co)
            
        #properties
        #store radius of each circle as percentage(sum of all must at all times add up to 100.0%)
        self.wradii = [25.,20.,20.,35.]
        #starting angle for each circle (0-360). 
        self.startangle = [0,0,0,0]
        #text projection: 0 = Flat, 1 = perpendicular to center, 2 = radial from center
        self.projection = [0,1,1,2]
        self.wheeltextsize = [10,10,10,10]
        self.wheelcolorpattern = 0                  #pattern
        self.wheeledge = .02                        #overlaping decorative edge
        self.wheellinewidth = 1
        self.wheellinecolor = u"black"               #initial color of lines

        self.samplingflag = False

    #NOTE: empty Figure is initialy drawn at the end of aw.settingsload()        
    #################################    FUNCTIONS    ###################################
    #####################################################################################
        

    #runs from GUI thread     
    def updategraphics(self):
        try:
            if len(self.timex):        
                aw.lcd2.display("%.1f"%self.temp1[-1])            # ET
                aw.lcd3.display("%.1f"%self.temp2[-1])            # BT
                aw.lcd4.display("%.1f"%self.rateofchange1)        # rate of change MET (degress per minute)
                aw.lcd5.display("%.1f"%self.rateofchange2)        # rate of change BT (degrees per minute)
                
                if self.device == 0:                              #extra LCDs for pid  
                    aw.lcd6.display(aw.ser.currentpidsv)
                    aw.lcd7.display(aw.ser.dutycycle)

            #display new-updated canvas
            self.fig.canvas.draw()

            #check if HUD is ON
            if self.HUDflag:
                aw.showHUD[aw.HUDfunction]() 

            #check alarms
            if self.device != 18:
                for i in range(len(self.alarmflag)):
                    #if alarm on, and not triggered, and time is after set time:
                    if self.alarmflag[i] and not self.alarmstate[i] and self.timeindex[self.alarmtime[i]]:    
                        if self.alarmsource[i] == 0:                        #check ET
                            if self.temp1[-1] > self.alarmtemperature[i]:
                                self.setalarm(i)
                        elif self.alarmsource[i] == 1:                      #check BT
                            if self.temp2[-1] > self.alarmtemperature[i]:
                                self.setalarm(i)

        except Exception,e:
            self.flagon = False
            self.adderror(QApplication.translate("Error Message","Exception Error: updategraphics() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return
        
    def updateLCDtime(self):
        if self.flagon:
            tx = self.timeclock.elapsed()/1000.
            if self.timeindex[0] != -1:
                ts = tx - self.timex[self.timeindex[0]]
            else:
                ts = tx             
            nextreading = 1000. - 1000.*(tx%1.)
            aw.lcd1.display(QString(self.stringfromseconds(int(ts))))
            QTimer.singleShot(nextreading,self.updateLCDtime)

    def toggleHUD(self):
        #OFF
        if self.HUDflag:
            self.viewProjection()
            self.HUDflag = False
            aw.button_18.setStyleSheet("QPushButton { background-color: #b5baff }")
            aw.stack.setCurrentIndex(0)
            self.resetlines()
            aw.sendmessage(QApplication.translate("Message Area","HUD OFF", None, QApplication.UnicodeUTF8))
            
        #ON
        else:
            if len(self.temp2) > 1:  #Need this because viewProjections use rate of change (two values needed)
                #load
                img = QPixmap().grabWidget(self)
                aw.HUD.setPixmap(img)
                
                self.HUDflag = True
                aw.button_18.setStyleSheet("QPushButton { background-color: #60ffed }")
                aw.stack.setCurrentIndex(1)
                aw.sendmessage(QApplication.translate("Message Area","HUD ON", None, QApplication.UnicodeUTF8))
            else:
                aw.sendmessage(QApplication.translate("Message Area","Need some data for HUD to work", None, QApplication.UnicodeUTF8))
        aw.soundpop()        

    def resetlines(self):
        linecount = 2  + 2*len(self.extradevices)       #ET + BT + extradevices
        if self.DeltaETflag:  #delta ET
            linecount += 1
        if self.DeltaBTflag: #delta BT
            linecount += 1
        if self.background:
            linecount += 2   #background ET + background BT = 2
        self.ax.lines = self.ax.lines[0:linecount]
        
    def setalarm(self,alarmnumber):
        if self.alarmaction[alarmnumber] == 0:
            self.alarmstate[alarmnumber] = 1    #turn off flag as it has been read
            QMessageBox.information(self,QApplication.translate("MessageBox", "Alarm notice",None, QApplication.UnicodeUTF8),self.alarmstrings[alarmnumber])
            aw.soundpop()
        elif self.alarmaction[alarmnumber] == 1:
            self.alarmstate[alarmnumber] = 1 #turn off flag as it has been read
            try:
                fname = unicode(self.alarmstrings[alarmnumber])
                QDesktopServices.openUrl(QUrl(u"file:///" + unicode(QDir().current().absolutePath()) + u"/" + fname, QUrl.TolerantMode))
                aw.sendmessage(QApplication.translate("Message Area","Alarm is calling: %1",None, QApplication.UnicodeUTF8).arg(self.alarmstrings[alarmnumber]))
            except Exception,e:
                self.adderror(QApplication.translate("Error Message","Exception Error: setalarm() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
                return  

    def playbackevent(self):
        #needed when using device NONE
        if len(self.timex):
            #find time distances
            for i in range(len(self.backgroundEvents)):
                timed = int(self.timeB[self.backgroundEvents[i]] - self.timeclock.elapsed()/1000.)                 
                if  timed > 0 and timed < self.detectBackgroundEventTime:
                    #write text message
                    message = "> " +  self.stringfromseconds(timed) + " [" + self.etypes[self.backgroundEtypes[i]] 
                    message += "] [" + self.eventsvalues[self.backgroundEvalues[i]] + "] : " + self.backgroundEStrings[i]
                    #rotate colors to get attention
                    if timed%2:
                        aw.messagelabel.setStyleSheet("background-color:'transparent';")
                    else:
                        aw.messagelabel.setStyleSheet("background-color:'yellow';")
                        
                    aw.sendmessage(message)
                    break
                
                elif timed == 0:
                    #for devices that support automatic roaster control
                    #if Fuji PID
                    if self.device == 0:

                        # COMMAND SET STRINGS
                        #  (adjust the SV PID to the float VALUE1)
                        # SETRS::VALUE1::VALUE2::VALUE3  (VALUE1 = target SV. float VALUE2 = time to reach int VALUE 1 (ramp) in minutes. int VALUE3 = hold (soak) time in minutes)

                        # IMPORTANT: VALUES are for controlling ET only (not BT). The PID should control ET not BT. The PID should be connected to ET only.
                        # Therefore, these values don't reflect a BT defined profile. They define an ET profile.
                        # They reflect the changes in ET, which indirectly define BT after some time lag
                        
                        # There are two ways to record a roast. One is by changing Set Values (SV) during the roast,
                        # the other is by using ramp/soaks segments (RS). 
                        # Examples:
                        
                        # SETSV::560.3           sets an SV value of 560.3F in the PID at the time of the recorded background event
                        
                        # SETRS::440.2::2::0     starts Ramp Soak mode so that it reaches 440.2F in 2 minutes and holds (soaks) 440.2F for zero minutes
                        
                        # SETRS::300.0::2::3::SETRS::540.0::6::0::SETRS::560.0::4::0::SETRS::560::0::0   
                        #       this command has 4 comsecutive commands inside (4 segments)
                        #       1 SETRS::300.0::2::3 reach 300.0F in 2 minutes and hold it for 3 minutes (ie. total dry phase time = 5 minutes)
                        #       2 SETRS::540.0::6::0 then reach 540.0F in 6 minutes and hold it there 0 minutes (ie. total mid phase time = 6 minutes )
                        #       3 SETRS::560.0::4::0 then reach 560.0F in 4 minutes and hold it there 0 minutes (ie. total finish phase time = 4 minutes)
                        #       4 SETRS::560::0::0 then do nothing (because ramp time and soak time are both 0)
                        #       END ramp soak mode
                        
                        
                        if "::" in self.backgroundEStrings[i]:   
                            aw.pid.replay(self.backgroundEStrings[i])
                            libtime.sleep(.5)  #avoid possible close times (rounding off) 
                            
                    #future Arduino
                    #if self.device == 19:

                        
                #delete message
                else:
                    text = str(aw.messagelabel.text())
                    if len(text):
                        if text[0] == ">":
                           aw.sendmessage("")
                           aw.messagelabel.setStyleSheet("background-color:'transparent';")

    #make a projection of change of rate of BT on the graph
    def viewProjection(self):

        self.resetlines()

        if self.projectionmode == 0:
            #calculate the temperature endpoint at endofx acording to the latest rate of change
            BTprojection = self.temp2[-1] + self.rateofchange2*(self.endofx - self.timex[-1]+ 120)/60.
            ETprojection = self.temp1[-1] + self.rateofchange1*(self.endofx - self.timex[-1]+ 120)/60.
            #plot projections
            self.ax.plot([self.timex[-1],self.endofx + 120 ], [self.temp2[-1], BTprojection],color =  self.palette["bt"],
                             linestyle = '-.', linewidth= 8, alpha = .3)
            self.ax.plot([self.timex[-1],self.endofx + 120 ], [self.temp1[-1], ETprojection],color =  self.palette["et"],
                             linestyle = '-.', linewidth= 8, alpha = .3)
            
        elif self.projectionmode == 1:
            # Under Test. Newton's Law of Cooling
            # This comes from the formula of heating (with ET) a cool (colder) object (BT).
            # The difference equation (discrete with n elements) is: DeltaT = T(n+1) - T(n) = K*(ET - BT)
            # The formula is a natural decay towards ET. The closer BT to ET, the smaller the change in DeltaT
            # projectionconstant is a multiplier factor. It depends on
            # 1 Damper or fan. Heating by convection is _faster_ than heat by conduction,
            # 2 Mass of beans. The heavier the mass, the _slower_ the heating of BT
            # 3 Gas or electric power: gas heats BT _faster_ because of hoter air.
            # Every roaster will have a different constantN.

            den = self.temp1[-1] - self.temp2[-1]  #denominator ETn - BTn 
            if den > 0: # if ETn > BTn
                #get x points
                xpoints = list(numpy.arange (self.timex[-1],self.endofx + 120, self.delay/1000.))  #do two minutes after endofx (+ 120 seconds)
                #get y points
                ypoints = [self.temp2[-1]]                              	    # start initializing with last BT
                K =  self.projectionconstant*self.rateofchange2/den/60.                 # multiplier
                for i in range(len(xpoints)-1):                                     # create new points from previous points 
                    DeltaT = K*(self.temp1[-1]- ypoints[-1])                        # DeltaT = K*(ET - BT)
                    ypoints.append(ypoints[-1]+ DeltaT)                             # add DeltaT to the next ypoint                        
                    
                #plot ET level (straight line) and BT curve
                self.ax.plot([self.timex[-1],self.endofx + 120 ], [self.temp1[-1], self.temp1[-1]],color =  self.palette["et"],
                             linestyle = '-.', linewidth= 3, alpha = .5)
                self.ax.plot(xpoints, ypoints, color =  self.palette["bt"],linestyle = '-.', linewidth= 3, alpha = .5)                  

    # this function is called from the HUD DLg and reports the linear time (straight line) it would take to reach a temperature target
    # acording to the current rate of change
    def getTargetTime(self):
        
        if self.rateofchange1 > 0:
            ETreachTime = (self.ETtarget - self.temp1[-1])/(self.rateofchange1/60.)
        else:
            ETreachTime = -1
            
        if self.rateofchange2 > 0:
            BTreachTime = (self.BTtarget - self.temp2[-1])/(self.rateofchange2/60.)
        else:
            BTreachTime = -1

        return ETreachTime, BTreachTime

    #single variable (x) mathematical expression evaluator for user defined functions to convert sensor readings from HHM28 multimeter
    #example: eval_math_expression("pow(e,2*cos(x))",.3) returns 6.75763501
    def eval_math_expression(self,mathexpression,x):
        if mathexpression == "":
            return x
        
        #Since eval() is very powerful, for security reasons, only the functions in this dictionary will be allowed
        mathdictionary = {"sin":math.sin,"cos":math.cos,"tan":math.tan,"pow":math.pow,"exp":math.exp,"pi":math.pi,"e":math.e,
                          "abs":abs,"acos":math.acos,"asin":math.asin,"atan":math.atan,"log":math.log,"radians":math.radians,
                          "sqrt":math.sqrt,"atan2":math.atan,"degrees":math.degrees}
        try:
            x = float(x)
            mathdictionary['x'] = x         #add x to the math dictionary assigning the key "x" to its float value
            #if Ys in expression
            if "Y" in mathexpression:
                #extract Ys
                Yval = []                   #extract value number example Y9 = 9
                mlen = len(mathexpression)
                for i in range(mlen):
                    if mathexpression[i] == "Y":
                        #find Y number
                        if i+1 < mlen:                          #check for out of range
                            if mathexpression[i+1].isdigit():
                                number = mathexpression[i+1]
                            else:
                                number = "1"
                        #check for double digit
                        if i+2 < mlen:
                            if mathexpression[i+2].isdigit() and mathexpression[i+1].isdigit():
                                number += mathexpression[i+2]
                        Yval.append(number)
                            
                #build Ys float values
                if len(self.timex) > 1:
                    Y = [self.temp1[-1],self.temp2[-1]]
                    for i in range(len(self.extradevices)):
                        Y.append(self.extratemp1[i][-1])
                        Y.append(self.extratemp2[i][-1])
                    #add Ys and their value to math dictionary 
                    for i in range(len(Yval)):
                        mathdictionary["Y"+ Yval[i]] = Y[int(Yval[i])-1]
                else:
                    for i in range(len(Yval)):
                        mathdictionary["Y"+ Yval[i]] = 0                    
                            
            return eval(mathexpression,{"__builtins__":None},mathdictionary)
            
        except Exception,e:
            self.adderror(QApplication.translate("Error Message", "Exception: eval_math_expression() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return 0

    #creates X axis labels ticks in mm:ss instead of seconds     
    def xaxistosm(self):
        if self.timeindex[0] != -1 and self.timeindex[0] < len(self.timex):
            starttime = self.timex[self.timeindex[0]]
        else:
            starttime = 0
          
        #majorlocator = ticker.IndexLocator(self.xgrid, starttime)          	        #IndexLocator does not work righ when updating (new value)self.endofx
        #majorlocator = ticker.MultipleLocator(self.xgrid)      	    	    	#MultipleLocator does not provide an offset for startime
            
        if self.xgrid == 0:
            self.xgrid = 60
        mfactor1 =  float(2. + int(starttime)/int(self.xgrid))
        mfactor2 =  float(2. + int(self.endofx)/int(self.xgrid))

        majorloc = numpy.arange(starttime-(self.xgrid*mfactor1),  starttime+(self.xgrid*mfactor2), self.xgrid)
        minorloc = numpy.arange(starttime-(self.xgrid*mfactor1),  starttime+(self.xgrid*mfactor2), self.xgrid/6.)
        
        map(round,majorloc)
        map(round,minorloc)

        majorlocator = ticker.FixedLocator(majorloc)        
        minorlocator = ticker.FixedLocator(minorloc)
        
        self.ax.xaxis.set_minor_locator(minorlocator)      
        self.ax.xaxis.set_major_locator(majorlocator)
        self.ax.yaxis.set_minor_locator(ticker.MultipleLocator(10))

        formatter = ticker.FuncFormatter(self.formtime)
        self.ax.xaxis.set_major_formatter(formatter)

        #adjust the length of the major ticks
        for i in self.ax.get_xticklines() + self.ax.get_yticklines():
            i.set_markersize(10)
            #i.set_markeredgewidth(2)   #adjust the width

        for i in self.ax.xaxis.get_minorticklines() + self.ax.yaxis.get_minorticklines():
            i.set_markersize(5)        
                
        for label in self.ax.xaxis.get_ticklabels():
            label.set_rotation(self.xrotation)

    #used by xaxistosm(). Provides also negative time
    def formtime(self,x,pos):
        if self.timeindex[0] != -1 and self.timeindex[0] < len(self.timex):
            starttime = self.timex[self.timeindex[0]]
        else:
            starttime = 0
            
        if x >=  starttime:
            m,s = divmod((x - round(starttime)), 60)  #**NOTE**: divmod() returns here type numpy.float64, which could create problems
            #print type(m),type(s)                    #it is used in: formatter = ticker.FuncFormatter(self.formtime) in xaxistosm()
            s = int(round(s))
            m = int(m)
            
            if s >= 59:
                return '%d'%(m+1)
            elif abs(s - 30) < 1:
                return '%d.5'%m
            elif s > 1:
                return  '%d:%02d'%(m,s)
            else:
                return '%d'%m
            
        else:
            m,s = divmod(abs(x - round(starttime)), 60)
            s = int(round(s))
            m = int(m)
            
            if s >= 59:
                return '-%d'%(m+1)
            elif abs(s-30) < 1:
                return '-%d.5'%m
            elif s > 1:
                return  '-%d:%02d'%(m,s)
            else:
                return '-%d'%m
            
    def reset_and_redraw(self):
        self.reset()
        self.redraw()
        
    #Resets graph. Called from reset button. Deletes all data
    def reset(self):
        #prevents deleting accidentally a finished roast
        if self.safesaveflag== True:
            string = QApplication.translate("MessageBox","Do you want to save the profile?", None, QApplication.UnicodeUTF8)
            reply = QMessageBox.warning(self,QApplication.translate("MessageBox Caption","Profile unsaved", None, QApplication.UnicodeUTF8),string,
                                QMessageBox.Reset |QMessageBox.Save|QMessageBox.Cancel)
            if reply == QMessageBox.Reset :
                self.safesaveflag == False
            elif reply == QMessageBox.Cancel:            
                aw.sendmessage(QApplication.translate("Message Area","Reset has been cancelled",None, QApplication.UnicodeUTF8))
                return
            elif reply == QMessageBox.Save:
                aw.fileSave(None)
                return
            
        if self.HUDflag:
            self.toggleHUD()
            
        self.ax = self.fig.add_subplot(111, axisbg=self.palette["background"])
        self.ax.set_title(self.title,size=20,color=self.palette["title"])  
        
        #reset all variables that need to be reset
        self.flagon = False
        self.rateofchange1 = 0.0
        self.rateofchange2 = 0.0
        self.temp1, self.temp2, self.delta1, self.delta2, self.timex = [],[],[],[],[]
        self.unfiltereddelta1,self.unfiltereddelta2 = [],[]
        self.timeindex = [-1,0,0,0,0,0,0]
        self.specialevents=[]
        if not self.keeptimeflag:
            self.endofx = 60
        aw.lcd1.display("00:00")
        aw.lcd2.display("0.0")
        aw.lcd3.display("0.0")
        aw.lcd4.display("0.0")
        aw.lcd5.display("0.0")
        aw.lcd6.display("0.0")
        aw.lcd7.display("0.0")
        aw.sendmessage(QApplication.translate("Message Area","Scope has been reset",None, QApplication.UnicodeUTF8))
        aw.button_3.setDisabled(False)
        aw.button_4.setDisabled(False)
        aw.button_5.setDisabled(False)
        aw.button_6.setDisabled(False)
        aw.button_7.setDisabled(False)
        aw.button_8.setDisabled(False)
        aw.button_9.setDisabled(False)
        aw.button_19.setDisabled(False)        
        aw.button_3.setFlat(False)
        aw.button_4.setFlat(False)
        aw.button_5.setFlat(False)
        aw.button_6.setFlat(False)
        aw.button_7.setFlat(False)
        aw.button_8.setFlat(False)
        aw.button_9.setFlat(False)
        aw.button_19.setFlat(False)
        aw.button_1.setText(QApplication.translate("Scope Button", "ON",None, QApplication.UnicodeUTF8)) 
        aw.button_1.setStyleSheet(aw.pushbuttonstyles["OFF"])

        self.title = QApplication.translate("Scope Title", "Roaster Scope",None, QApplication.UnicodeUTF8)
        aw.setWindowTitle(aw.windowTitle)

        if self.roastpropertiesflag:
            self.roastingnotes = u""
            self.cuppingnotes = u""
            self.beans = u""
            self.weight = [0,0,u"g"]
            self.volume = [0,0,u"l"]
            self.ambientTemp = 0.
            
        self.roastdate = QDate.currentDate()            
        self.errorlog = []

        self.specialevents = []
        self.specialeventstype = [] 
        self.specialeventsStrings = []        
        self.specialeventsvalue = []
        aw.eNumberSpinBox.setValue(0)
        aw.lineEvent.setText("")      
        aw.etypeComboBox.setCurrentIndex(0)
        aw.valueComboBox.setCurrentIndex(0)    
        aw.curFile = None                 #current file name
        self.ystep = 45     	    	  #used to find length of arms in annotations  

        #Designer variables
        self.indexpoint = 0
        self.rightclickcid = 0
        self.workingline = 2            #selects ET or BT
        self.currentx = 0               #used to add point when right click
        self.currenty = 0               #used to add point when right click
        self.designertemp1init = []
        self.designertemp2init = []
        if self.mode == u"C":
                                      #CH, DE, Fcs,Fce,Scs,Sce,Drop  
            self.designertemp1init = [290,290,290,290,290,290,290]
            self.designertemp2init = [200,150,200,210,220,225,240]   
        elif self.mode == u"F":
            self.designertemp1init = [500,500,500,500,500,500,500]
            self.designertemp2init = [380,300,390,395,410,412,420]
        self.disconnect_designer()  #sets designer flag false
        self.setCursor(Qt.ArrowCursor)

        #extra devices
        for i in range(len(self.extradevices)):            
            self.extratimex[i],self.extratemp1[i],self.extratemp2[i] = [],[],[]
        
        #reset alarms that have been triggered
        self.alarmstate = [0]*len(self.alarmflag)  #0 = not triggered; 1 = triggered

        #reset cupping flavor values
        self.flavors = [5.]*len(self.flavorlabels)

        self.samplingflag = False

        self.redraw()
        aw.soundpop()
        
    #Redraws data   
    def redraw(self):
        try:
            
            #avoid redrawing in middle of sampling
            count = 0
            while self.samplingflag:
                libtime.sleep(.05)
                count += 1
                if count == 150:
                    self.samplingflag = False

            self.samplingflag = True
            
            self.fig.clf()   #wipe out figure
            self.ax = self.fig.add_subplot(111, axisbg=self.palette["background"])
            #Set axes same as in __init__
            if self.endofx == 0:            #fixes possible condition of endofx being ZERO when application starts (after aw.settingsload)
                self.endofx = 60
            self.ax.set_xlim(self.startofx, self.endofx)
            self.ax.set_ylim(self.ylimit_min, self.ylimit)
            self.ax.set_autoscale_on(False)
            self.ax.grid(True,color=self.palette["grid"],linestyle=self.gridstyles[self.gridlinestyle],linewidth = self.gridthickness,alpha = self.gridalpha)
            self.ax.set_ylabel(self.mode,size=16,color =self.palette["ylabel"])
            self.ax.set_xlabel('Time',size=16,color = self.palette["xlabel"])
            self.ax.set_title(self.title,size=20,color=self.palette["title"])
            for tick in self.ax.yaxis.get_major_ticks():
                tick.label2On = True
            self.ax.yaxis.set_major_locator(ticker.MultipleLocator(self.ygrid))
                
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

            if self.eventsGraphflag:
                # make blended transformations to help identify EVENT types
                if self.mode == "C":
                    step = 5
                    start = 20
                else:
                    step = 10
                    start = 60
                jump = 20
                for i in range(len(self.etypes)):
                    rectEvent = patches.Rectangle((0,self.phases[0]-start-jump), width=1, height = step, transform=trans, color=self.palette["rect1"],alpha=.3)
                    self.ax.add_patch(rectEvent)
                    if self.mode == "C":
                        jump -= 10
                    else:
                        jump -= 20
                        
            ##### ET,BT curves
            self.l_temp1, = self.ax.plot(self.timex, self.temp1,color=self.palette["et"],linewidth=2,label=unicode(QApplication.translate("Scope Label", "ET", None, QApplication.UnicodeUTF8)))
            self.l_temp2, = self.ax.plot(self.timex, self.temp2,color=self.palette["bt"],linewidth=2,label=unicode(QApplication.translate("Scope Label", "BT", None, QApplication.UnicodeUTF8)))

            ##### Extra devices-curves
            self.extratemp1lines,self.extratemp2lines = [],[]
            for i in range(len(self.extratimex)):
                self.extratemp1lines.append(self.ax.plot(self.extratimex[i], self.extratemp1[i],color=self.extradevicecolor1[i],linewidth=2,label= self.extraname1[i])[0])
                self.extratemp2lines.append(self.ax.plot(self.extratimex[i], self.extratemp2[i],color=self.extradevicecolor2[i],linewidth=2,label= self.extraname2[i])[0])

            #check BACKGROUND flag
            if self.background: 
                #check to see if there is both a profile loaded and a background loaded
                if self.timeindex[0] != -1 and self.timeindexB[0] != -1 and self.backmoveflag:
                    if self.timex[self.timeindex[0]] != self.timeB[self.timeindexB[0]]:
                        #align the background profile so they both plot with the same CHARGE time
                        difference = self.timex[self.timeindex[0]] - self.timeB[self.timeindexB[0]]
                        if difference > 0:
                            self.movebackground(u"left",-difference)
                        elif difference < 0:
                            self.movebackground(u"right",difference)
                        self.backmoveflag = 0
                    
                #draw background
                self.l_back1, = self.ax.plot(self.timeB, self.temp1B,color=self.backgroundmetcolor,linewidth=self.backgroundwidth,
                                             linestyle=self.backgroundstyle,alpha=self.backgroundalpha,label=unicode(QApplication.translate("Scope Label", "BackgroundET", None, QApplication.UnicodeUTF8)))
                self.l_back2, = self.ax.plot(self.timeB, self.temp2B,color=self.backgroundbtcolor,linewidth=self.backgroundwidth,
                                             linestyle=self.backgroundstyle,alpha=self.backgroundalpha,label=unicode(QApplication.translate("Scope Label", "BackgroundBT", None, QApplication.UnicodeUTF8)))

                #check backgroundevents flag	
                if self.backgroundeventsflag:
                    if self.mode == "F":
                        height = 50
                    else:
                        height = 20
                    for p in range(len(self.backgroundEvents)):
                        st1 = unicode(self.Betypes[self.backgroundEtypes[p]][0] + self.eventsvalues[self.backgroundEvalues[p]])                   
                        if self.temp1B[self.backgroundEvents[p]] > self.temp2B[self.backgroundEvents[p]]:
                            temp = self.temp1B[self.backgroundEvents[p]]
                        else:
                            temp = self.temp2B[self.backgroundEvents[p]]
                        self.ax.annotate(st1, xy=(self.timeB[self.backgroundEvents[p]], temp),
                                            xytext=(self.timeB[self.backgroundEvents[p]], temp+height),
                                            fontsize=10,color=self.palette["text"],arrowprops=dict(arrowstyle='wedge',color="yellow",
                                            alpha=self.backgroundalpha,relpos=(0,0)),alpha=self.backgroundalpha)                        

                #check backgroundDetails flag
                if self.backgroundDetails:
                    #if there is a profile loaded with CHARGE, then save time to get the relative time
                    if self.timeindex[0] != -1:   #verify it exists before loading it, otherwise the list could go out of index
                        startB = self.timex[self.timeindex[0]]
                    else:
                        startB = 0

                    #if background CHARGE exists
                    if self.timeindexB[0] != -1: 
                        st1 = unicode(self.stringfromseconds(self.timeB[self.timeindexB[0]] - startB))
                        self.ax.annotate(u"%.1f"%(self.temp2B[self.timeindexB[0]]), xy=(self.timeB[self.timeindexB[0]],self.temp2B[self.timeindexB[0]]),
                                         xytext=(self.timeB[self.timeindexB[0]],self.temp2B[self.timeindexB[0]] + 50),fontsize=10,color=self.palette["text"],
                                         arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)
                        
                        self.ax.annotate(st1, xy=(self.timeB[self.timeindexB[0]],self.temp2B[self.timeindexB[0]]),
                                         xytext=(self.timeB[self.timeindexB[0]]+5,self.temp2B[self.timeindexB[0]] - 100),fontsize=10,color=self.palette["text"],
                                         arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)

                        if self.timeindexB[1]:
                            st1 = unicode(self.stringfromseconds(self.timeB[self.timeindexB[1]]- startB))
                            self.ax.annotate(u"%.1f"%(self.temp2B[self.timeindexB[1]]), xy=(self.timeB[self.timeindexB[1]],self.temp2B[self.timeindexB[1]]),
                                             xytext=(self.timeB[self.timeindexB[1]]-5,self.temp2B[self.timeindexB[1]]+50),fontsize=10,color=self.palette["text"],
                                             arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)
                            self.ax.annotate(st1, xy=(self.timeB[self.timeindexB[1]],self.temp2B[self.timeindexB[1]]),
                                             xytext=(self.timeB[self.timeindexB[1]],self.temp2B[self.timeindexB[1]]-50),fontsize=10,color=self.palette["text"],
                                             arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)
                            
                        if self.timeindexB[2]:
                            st1 = unicode(self.stringfromseconds(self.timeB[self.timeindexB[2]]-startB))
                            self.ax.annotate(u"%.1f"%(self.temp2B[self.timeindexB[2]]), xy=(self.timeB[self.timeindexB[2]],self.temp2B[self.timeindexB[2]]),
                                             xytext=(self.timeB[self.timeindexB[2]]-5,self.temp2B[self.timeindexB[2]]+50),fontsize=10,color=self.palette["text"],
                                             arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)
                            self.ax.annotate(st1, xy=(self.timeB[self.timeindexB[2]],self.temp2B[self.timeindexB[2]]),
                                             xytext=(self.timeB[self.timeindexB[2]],self.temp2B[self.timeindexB[2]]-50),fontsize=10,color=self.palette["text"],
                                             arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)
                            
                        if self.timeindexB[3]:
                            st1 = unicode(self.stringfromseconds(self.timeB[self.timeindexB[3]]-startB))          
                            self.ax.annotate(u"%.1f"%(self.temp2B[self.timeindexB[3]]), xy=(self.timeB[self.timeindexB[3]],self.temp2B[self.timeindexB[3]]),
                                             xytext=(self.timeB[self.timeindexB[3]]-5,self.temp2B[self.timeindexB[3]]+70),fontsize=10,color=self.palette["text"],
                                             arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)              
                            self.ax.annotate(st1, xy=(self.timeB[self.timeindexB[3]],self.temp2B[self.timeindexB[3]]),
                                             xytext=(self.timeB[self.timeindexB[3]],self.temp2B[self.timeindexB[3]]-80),fontsize=10, color=self.palette["text"],
                                             arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)
                            
                        if self.timeindexB[4]:
                            st1 = unicode(self.stringfromseconds(self.timeB[self.timeindexB[4]]-startB))
                            self.ax.annotate(u"%.1f"%(self.temp2B[self.timeindexB[4]]), xy=(self.timeB[self.timeindexB[4]],self.temp2B[self.timeindexB[4]]),
                                             xytext=(self.timeB[self.timeindexB[4]]-5,self.temp2B[self.timeindexB[4]]+90),fontsize=10,color=self.palette["text"],
                                             arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)      
                            self.ax.annotate(st1, xy=(self.timeB[self.timeindexB[4]],self.temp2B[self.timeindexB[4]]),
                                             xytext=(self.timeB[self.timeindexB[4]],self.temp2B[self.timeindexB[4]]-110),fontsize=10,color=self.palette["text"],
                                             arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)
                            
                        if self.timeindexB[5]:
                            st1 = unicode(self.stringfromseconds(self.timeB[self.timeindexB[5]]-startB))
                            self.ax.annotate(u"%.1f"%(self.timeB[self.timeindexB[5]]), xy=(self.timeB[self.timeindexB[5]],self.temp2B[self.timeindexB[5]]),
                                             xytext=(self.timeB[self.timeindexB[5]]-5,self.temp2B[self.timeindexB[5]]+50),fontsize=10,color=self.palette["text"],
                                             arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)                
                            self.ax.annotate(st1, xy=(self.timeB[self.timeindexB[5]],self.temp2B[self.timeindexB[5]]),
                                             xytext=(self.timeB[self.timeindexB[5]],self.temp2B[self.timeindexB[5]]-40),fontsize=10,color=self.palette["text"],
                                             arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)
                            
                        if self.timeindexB[6]:
                            st1 = unicode(self.stringfromseconds(self.timeB[self.timeindexB[6]]-startB))
                            self.ax.annotate(u"%.1f"%(self.temp2B[self.timeindexB[6]]), xy=(self.timeB[self.timeindexB[6]],self.temp2B[self.timeindexB[6]]),
                                             xytext=(self.timeB[self.timeindexB[6]]-5,self.temp2B[self.timeindexB[6]]+70),color=self.palette["text"],
                                             arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),fontsize=10,alpha=self.backgroundalpha)
                            self.ax.annotate(st1, xy=(self.timeB[self.timeindexB[6]],self.temp2B[self.timeindexB[6]]),
                                             xytext=(self.timeB[self.timeindexB[6]],self.temp2B[self.timeindexB[6]]-80),fontsize=10,color=self.palette["text"],
                                             arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=self.backgroundalpha),alpha=self.backgroundalpha)

                #END of Background
               
            #populate delta ET (self.delta1) and delta BT (self.delta2)
            d1,d2,d3,d4=[],[],[],[]
            delta1, delta2 = 0.,0.
            for i in range(len(self.timex)-1):
                timed = self.timex[i+1] - self.timex[i]
                if timed:
                    delta1 = 60.*((self.temp1[i+1] - self.temp1[i]) / timed) #degrees pre minute
                    delta2 = 60.*((self.temp2[i+1] - self.temp2[i]) / timed)

                    #inputs
                    d1.append(delta1)
                    d2.append(delta2)
                    
                    if self.deltafilter:
                        if i > (self.deltafilter-1):
                            #smooth DeltaBT/DeltaET by using FIR filter of X pads.
                            #d1 and d2 are inputs, while d3 and d4 are outputs  
                            #Use only current and past input values. Don't feed parts of outputs d3 d4 to filter
                            a1,a2 = 0.,0.
                            for k in range(self.deltafilter):
                                a1 += d1[-(k+1)]
                                a2 += d2[-(k+1)]
                            #outputs
                            d3.append(float(self.sensitivity)*(a1/float(self.deltafilter)))
                            d4.append(float(self.sensitivity)*(a2/float(self.deltafilter)))
                        else:
                            d3.append(0.) 
                            d4.append(0.)
                               
            if self.deltafilter:
                self.delta1 = d3
                self.delta2 = d4
            else:
                self.delta1 = d1
                self.delta2 = d2
                    
            #this is needed because DeltaBT and DeltaET need 2 values of timex (difference) but they also need same dimension in order to plot
            #equalize dimensions if needed
            lt,ld =  len(self.timex),len(self.delta2)
            if lt != ld:
                if lt > ld:
                    for x in range(lt - ld):
                        if ld:
                            self.delta1.append(self.delta1[-1])
                            self.delta2.append(self.delta2[-1])
                        else:
                            self.delta1.append(0.)
                            self.delta2.append(0.)                        
                if lt < ld:
                    self.delta1 = self.delta1[:lt]                
                    self.delta2 = self.delta2[:lt]                

            ##### DeltaET,DeltaBT curves
            if self.DeltaETflag:
                self.l_delta1, = self.ax.plot(self.timex, self.delta1,color=self.palette["deltaet"],linewidth=2,label=unicode(QApplication.translate("Scope Label", "DeltaET", None, QApplication.UnicodeUTF8)))
            if self.DeltaBTflag:
                self.l_delta2, = self.ax.plot(self.timex, self.delta2,color=self.palette["deltabt"],linewidth=2,label=unicode(QApplication.translate("Scope Label", "DeltaBT", None, QApplication.UnicodeUTF8)))
            
            handles = [self.l_temp1,self.l_temp2]
            labels = [unicode(QApplication.translate("Scope Label", "ET", None, QApplication.UnicodeUTF8)),unicode(QApplication.translate("Scope Label", "BT", None, QApplication.UnicodeUTF8))]

            #add Rate of Change if flags are True
            if  self.DeltaETflag:
                handles.append(self.l_delta1)
                labels.append(unicode(QApplication.translate("Scope Label", "DeltaET", None, QApplication.UnicodeUTF8)))
                
            if  self.DeltaBTflag:
                handles.append(self.l_delta2)
                labels.append(unicode(QApplication.translate("Scope Label", "DeltaBT", None, QApplication.UnicodeUTF8)))

            ndevices = len(self.extradevices)
            if ndevices:
                for i in range(ndevices):
                    handles.append(self.extratemp1lines[i])
                    handles.append(self.extratemp2lines[i])
                    labels.append(self.extraname1[i])
                    labels.append(self.extraname2[i])
                    
            #write legend
            self.ax.legend(handles,labels,loc=self.legendloc,ncol=4,prop=font_manager.FontProperties(size=10),fancybox=True)

            if not self.designerflag:    
                #Add markers for CHARGE           
                if self.timeindex[0] != -1:
                    #anotate temperature

                    self.ax.annotate(u"%.1f"%(self.temp2[self.timeindex[0]]), xy=(self.timex[self.timeindex[0]],self.temp2[self.timeindex[0]]),
                                    xytext=(self.timex[self.timeindex[0]],self.temp2[self.timeindex[0]]+self.ystep),
                                    color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)
                    #anotate time
                    self.ax.annotate(QApplication.translate("Scope Annotation", "START 00:00", None, QApplication.UnicodeUTF8), xy=(self.timex[self.timeindex[0]],self.temp2[self.timeindex[0]]),
                                     xytext=(self.timex[self.timeindex[0]],self.temp2[self.timeindex[0]]-self.ystep),
                                     color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)
                #Add Dry End markers            
                if self.timeindex[1]:
                    self.ystep = self.findtextgap(self.temp2[self.timeindex[0]],self.temp2[self.timeindex[1]])
                    st1 = QApplication.translate("Scope Annotation","DE %1", None, QApplication.UnicodeUTF8).arg(unicode(self.stringfromseconds(self.timex[self.timeindex[1]]-self.timex[self.timeindex[0]])))
                    #anotate temperature
                    self.ax.annotate(u"%.1f"%(self.temp2[self.timeindex[1]]), xy=(self.timex[self.timeindex[1]],self.temp2[self.timeindex[1]]),
                                    xytext=(self.timex[self.timeindex[1]],self.temp2[self.timeindex[1]] + self.ystep), 
                                    color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)
                    #anotate time
                    self.ax.annotate(st1, xy=(self.timex[self.timeindex[1]],self.temp2[self.timeindex[1]]),
                                    xytext=(self.timex[self.timeindex[1]],self.temp2[self.timeindex[1]] - self.ystep),
                                    color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)            
                #Add 1Cs markers
                if self.timeindex[2]:
                    if self.timeindex[1]: #if dryend
                        self.ystep = self.findtextgap(self.temp2[self.timeindex[1]],self.temp2[self.timeindex[2]])
                    else:
                        self.ystep = self.findtextgap(self.temp2[self.timeindex[0]],self.temp2[self.timeindex[2]])
                    st1 = QApplication.translate("Scope Annotation","FCs %1", None, QApplication.UnicodeUTF8).arg(unicode(self.stringfromseconds(self.timex[self.timeindex[2]]-self.timex[self.timeindex[0]])))
                    #anotate temperature
                    self.ax.annotate(u"%.1f"%(self.temp2[self.timeindex[2]]), xy=(self.timex[self.timeindex[2]],self.temp2[self.timeindex[2]]),
                                    xytext=(self.timex[self.timeindex[2]],self.temp2[self.timeindex[2]] + self.ystep), 
                                    color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)
                    #anotate time
                    self.ax.annotate(st1, xy=(self.timex[self.timeindex[2]],self.temp2[self.timeindex[2]]),
                                    xytext=(self.timex[self.timeindex[2]],self.temp2[self.timeindex[2]] - self.ystep),
                                    color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)
                #Add 1Ce markers
                if self.timeindex[3]:
                    self.ystep = self.findtextgap(self.temp2[self.timeindex[2]],self.temp2[self.timeindex[3]])
                    st1 = QApplication.translate("Scope Annotation","FCe %1", None, QApplication.UnicodeUTF8).arg(unicode(self.stringfromseconds(self.timex[self.timeindex[3]]-self.timex[self.timeindex[0]])))
                    #anotate temperature
                    self.ax.annotate(u"%.1f"%(self.temp2[self.timeindex[3]]), xy=(self.timex[self.timeindex[3]],self.temp2[self.timeindex[3]]),
                                    xytext=(self.timex[self.timeindex[3]],self.temp2[self.timeindex[3]] + self.ystep),
                                    color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)
                    #anotate time
                    self.ax.annotate(st1, xy=(self.timex[self.timeindex[3]],self.temp2[self.timeindex[3]]),
                                    xytext=(self.timex[self.timeindex[3]],self.temp2[self.timeindex[3]]-self.ystep),
                                    color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)
                    #add a water mark if FCs
                    if self.timeindex[2]:
                        self.ax.axvspan(self.timex[self.timeindex[2]],self.timex[self.timeindex[3]], facecolor=self.palette["watermarks"], alpha=0.2)

                #Add 2Cs markers
                if self.timeindex[4]:
                    if self.timeindex[3]:
                        self.ystep = self.findtextgap(self.temp2[self.timeindex[3]],self.temp2[self.timeindex[4]])
                    else:
                        self.ystep = self.findtextgap(self.temp2[self.timeindex[2]],self.temp2[self.timeindex[4]])
                    st1 = QApplication.translate("Scope Annotation","SCs %1", None, QApplication.UnicodeUTF8).arg(unicode(self.stringfromseconds(self.timex[self.timeindex[4]]-self.timex[self.timeindex[0]])))
                    self.ax.annotate(u"%.1f"%(self.temp2[self.timeindex[4]]), xy=(self.timex[self.timeindex[4]],self.temp2[self.timeindex[4]]),
                                    xytext=(self.timex[self.timeindex[4]],self.temp2[self.timeindex[4]] + self.ystep),
                                    color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)      
                    self.ax.annotate(st1, xy=(self.timex[self.timeindex[4]],self.temp2[self.timeindex[4]]),
                                     xytext=(self.timex[self.timeindex[4]],self.temp2[self.timeindex[4]]-self.ystep),
                                     color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)
                #Add 2Ce markers
                if self.timeindex[5]:
                    self.ystep = self.findtextgap(self.temp2[self.timeindex[4]],self.temp2[self.timeindex[5]])
                    st1 =  QApplication.translate("Scope Annotation","SCe %1", None, QApplication.UnicodeUTF8).arg(unicode(self.stringfromseconds(self.timex[self.timeindex[5]]-self.timex[self.timeindex[0]])))
                    #anotate temperature
                    self.ax.annotate(u"%.1f"%(self.temp2[self.timeindex[5]]), xy=(self.timex[self.timeindex[5]],self.temp2[self.timeindex[5]]),
                                    xytext=(self.timex[self.timeindex[5]],self.temp2[self.timeindex[5]] + self.ystep),
                                    color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)
                    #anotate time
                    self.ax.annotate(st1, xy=(self.timex[self.timeindex[5]],self.temp2[self.timeindex[5]]),
                                    xytext=(self.timex[self.timeindex[5]],self.temp2[self.timeindex[5]] - self.ystep),
                                    color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)
                    #do water mark if SCs
                    if self.timeindex[4]:
                        self.ax.axvspan(self.timex[self.timeindex[4]],self.timex[self.timeindex[5]], facecolor=self.palette["watermarks"], alpha=0.2)

                #Add DROP markers
                if self.timeindex[6]:
                    if self.timeindex[5]:
                        self.ystep = self.findtextgap(self.temp2[self.timeindex[5]],self.temp2[self.timeindex[6]])
                    elif self.timeindex[4]:
                        self.ystep = self.findtextgap(self.temp2[self.timeindex[4]],self.temp2[self.timeindex[6]])
                    elif self.timeindex[3]:
                        self.ystep = self.findtextgap(self.temp2[self.timeindex[3]],self.temp2[self.timeindex[6]])
                    elif self.timeindex[2]:
                        self.ystep = self.findtextgap(self.temp2[self.timeindex[2]],self.temp2[self.timeindex[6]])
                    elif self.timeindex[1]:
                        self.ystep = self.findtextgap(self.temp2[self.timeindex[1]],self.temp2[self.timeindex[6]])
                    else:
                        self.ystep = self.findtextgap(self.temp2[self.timeindex[0]],self.temp2[self.timeindex[6]])                
                        
                    st1 = QApplication.translate("Scope Annotation","END %1", None, QApplication.UnicodeUTF8).arg(unicode(self.stringfromseconds(self.timex[self.timeindex[6]]-self.timex[self.timeindex[0]])))
                    #anotate temperature
                    self.ax.annotate(u"%.1f"%(self.temp2[self.timeindex[6]]), xy=(self.timex[self.timeindex[6]],self.temp2[self.timeindex[6]]),
                                    xytext=(self.timex[self.timeindex[6]],self.temp2[self.timeindex[6]] + self.ystep),
                                    color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)
                    #anotate time
                    self.ax.annotate(st1, xy=(self.timex[self.timeindex[6]],self.temp2[self.timeindex[6]]),
                                     xytext=(self.timex[self.timeindex[6]],self.temp2[self.timeindex[6]] - self.ystep),
                                     color=self.palette["text"],arrowprops=dict(arrowstyle='->',color=self.palette["text"],alpha=0.4),fontsize=10,alpha=1.)
                    
                    self.writestatistics()

            if self.eventsshowflag:
                Nevents = len(self.specialevents)                    
                #write events
                if self.mode == "F":
                    lim = self.phases[0]-80
                else:
                    lim = self.phases[0]-40
                    
                #two modes of drawing events. The first mode aligns the events annotations to a bar height so that they can be visually identified by type. 
                # the second mode places the events without height order.
                
                #Check eventsGraphflag and self.ylimit_min to see if there is enough height room           
                if self.eventsGraphflag and self.ylimit_min <= lim:
                    char1 = self.etypes[0][0]
                    char2 = self.etypes[1][0]
                    char3 = self.etypes[2][0]
                    char4 = self.etypes[3][0]

                    if self.mode == "F":
                        row = {char1:self.phases[0]-20,char2:self.phases[0]-40,char3:self.phases[0]-60,char4:self.phases[0]-80}
                    else:
                        row = {char1:self.phases[0]-10,char2:self.phases[0]-20,char3:self.phases[0]-30,char4:self.phases[0]-40}

                    #draw lines of color between events of the same type to help identify areas of events.
                    #count (as length of the list) and collect their times for each different type. Each type will have a different plot height 
                    netypes=[[],[],[],[]]
                    for i in range(Nevents):
                        if self.specialeventstype[i] == 0:
                            netypes[0].append(self.timex[self.specialevents[i]])
                        elif self.specialeventstype[i] == 1:
                            netypes[1].append(self.timex[self.specialevents[i]])
                        elif self.specialeventstype[i] == 2:
                            netypes[2].append(self.timex[self.specialevents[i]])
                        elif self.specialeventstype[i] == 3:
                            netypes[3].append(self.timex[self.specialevents[i]])
                            
                    letters = self.etypes[0][0]+self.etypes[1][0]+self.etypes[2][0]+self.etypes[3][0]   #"NPDF" fisrt letter for each type (None, Power, Damper, Fan)
                    colors = [self.palette["rect2"],self.palette["rect3"]] #rotating colors
                    for p in range(len(letters)):    
                        if len(netypes[p]) > 1:
                            for i in range(len(netypes[p])-1):
                                 #draw differentiating color bars between events and place then in a different height acording with type
                                 rect = patches.Rectangle( (netypes[p][i], row[letters[p]]), width = (netypes[p][i+1]-netypes[p][i]), height = step, color = colors[i%2],alpha=0.5)
                                 self.ax.add_patch(rect)
                                 
                    # annotate event
                    for i in range(Nevents):
                        firstletter = self.etypes[self.specialeventstype[i]][0]
                        secondletter = self.eventsvalues[self.specialeventsvalue[i]]
                        #some times ET is not drawn (ET = 0) when using device NONE
                        if self.temp1[int(self.specialevents[i])] >= self.temp2[int(self.specialevents[i])]:
                            self.ax.annotate(firstletter + secondletter, xy=(self.timex[int(self.specialevents[i])], self.temp1[int(self.specialevents[i])]),
                                             xytext=(self.timex[int(self.specialevents[i])],row[firstletter]),alpha=1.,
                                             color=self.palette["text"],arrowprops=dict(arrowstyle='-',color=self.palette["et"],alpha=0.4,relpos=(0,0)),fontsize=8,backgroundcolor='yellow')                    
                        else:
                            self.ax.annotate(firstletter + secondletter, xy=(self.timex[int(self.specialevents[i])], self.temp2[int(self.specialevents[i])]),
                                         xytext=(self.timex[int(self.specialevents[i])],row[firstletter]),alpha=1.,
                                         color=self.palette["text"],arrowprops=dict(arrowstyle='-',color=self.palette["bt"],alpha=0.4,relpos=(0,0)),fontsize=8,backgroundcolor='yellow')
                                
                # Second mode: old style mode (just attached the events to the graph without ordering height by type)   
                else:
                    for i in range(Nevents):
                        firstletter = self.etypes[self.specialeventstype[i]][0]                
                        secondletter = self.eventsvalues[self.specialeventsvalue[i]]
                        if self.mode == "F":
                            height = 50
                        else:
                            height = 20
                        #some times ET is not drawn (ET = 0) when using device NONE
                        if self.temp1[int(self.specialevents[i])] > self.temp2[int(self.specialevents[i])]:
                            temp = self.temp1[int(self.specialevents[i])]
                        else:
                            temp = self.temp2[int(self.specialevents[i])]
                        self.ax.annotate(firstletter + secondletter, xy=(self.timex[int(self.specialevents[i])], temp),
                                         xytext=(self.timex[int(self.specialevents[i])],temp+height),alpha=0.9,
                                         color=self.palette["text"],arrowprops=dict(arrowstyle='-',color=self.palette["bt"],alpha=0.4,relpos=(0,0)),fontsize=8,backgroundcolor='yellow')

                #if recorder on        
                if self.flagon:             
                    #update to last event
                    if Nevents:
                        aw.etypeComboBox.setCurrentIndex(self.specialeventstype[Nevents-1])
                        aw.valueComboBox.setCurrentIndex(self.specialeventsvalue[Nevents-1])
                    else:
                        aw.etypeComboBox.setCurrentIndex(0)
                        aw.valueComboBox.setCurrentIndex(0)
                    aw.eNumberSpinBox.setValue(Nevents)

            #update Y label colors
            for label in self.ax.yaxis.get_ticklabels():
                label.set_color(self.palette["ylabel"])

            #update X ticks, labels, and colors        
            self.xaxistosm()

            #ready to plot    
            self.fig.canvas.draw()     

            # if designer ON
            if self.designerflag:
                if self.background:                
                    self.ax.lines = self.ax.lines[2:]
                if len(self.timex):
                    self.redrawdesigner()
                    
            self.samplingflag = False
            
        except Exception,e:
            self.adderror(QApplication.translate("Error Message","Exception Error: redraw() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

        finally:
            self.samplingflag = False


    # adjusts height of annotations
    #supporting function for self.redraw() used to find best height of annotations in graph to avoid annotating over previous annotations (unreadable) when close to each other
    #oldpoint height1, newpoint height2. The previously used arrow step (length-height of arm) is self.ystep (which changes value in self.redraw())
    def findtextgap(self,height1,height2):
        if self.mode == "F":
            init = 44  #was 50  (original values were too high)
            gap = 22  #was 30
            for i in range(init,110):  # was 90
                if abs((height1 + self.ystep) - (height2+i)) > gap and abs((height1-self.ystep) - (height2-i)) > gap:
                    break
        else:
            init = 20  #was 40
            gap = 11   #was 20
            for i in range(init,54):  # was 90
                if abs((height1 + self.ystep) - (height2+i)) > gap and abs((height1-self.ystep) - (height2-i)) > gap:
                    break
        return i  #return height of arm
               
    # used to convert time from int seconds to string (like in the LCD clock timer). input int, output string xx:xx
    def stringfromseconds(self, seconds):
        if seconds >= 0:
            return "%02d:%02d"% divmod(seconds, 60)
        else:
            #usually the timex[timeindex[0]] is alreday taken away in seconds before calling stringfromseconds()
            negtime = abs(seconds)
            return "-%02d:%02d"% divmod(negtime, 60)
        
    #Converts a string into a seconds integer. Use for example to interpret times from Roaster Properties Dlg inputs
    #acepted formats: "00:00","-00:00"
    def stringtoseconds(self, string):
        timeparts = string.split(":")
        if len(timeparts) != 2:
            aw.sendmessage(QApplication.translate("Message Area","Time format error encountered", None, QApplication.UnicodeUTF8))
            return -1
        else:
            if timeparts[0][0] != "-":  #if number is positive
                seconds = int(timeparts[1])
                seconds += int(timeparts[0])*60
                return seconds
            else:
                seconds = int(timeparts[0])*60
                seconds -= int(timeparts[1])
                return seconds    #return negative number            
   
    def fromFtoC(self,Ffloat):
        return (Ffloat-32.0)*(5.0/9.0)

    def fromCtoF(self,CFloat):
        return (CFloat*9.0/5.0)+32.0

    #sets the graph display in Fahrenheit mode
    def fahrenheitMode(self):
        self.ylimit = 750
        #change watermarks limits. dryphase1, dryphase2, midphase, and finish phase Y limits
        for i in range(4):
            self.phases[i] = int(round(self.fromCtoF(self.phases[i])))          
        self.ax.set_ylabel("F",size=16,color = self.palette["ylabel"]) #Write "F" on Y axis
        self.mode = u"F"
        if aw: # during initialization aw is still None
            aw.FahrenheitAction.setDisabled(True)
            aw.CelsiusAction.setEnabled(True)
            aw.ConvertToFahrenheitAction.setDisabled(True)
            aw.ConvertToCelsiusAction.setEnabled(True) 

    #sets the graph display in Celsius mode
    def celsiusMode(self):
        self.ylimit = 400
        #change watermarks limits. dryphase1, dryphase2, midphase, and finish phase Y limits
        for i in range(4):
            self.phases[i] = int(round(self.fromFtoC(self.phases[i])))
        self.ax.set_ylabel("C",size=16,color = self.palette["ylabel"]) #Write "C" on Y axis
        self.mode = u"C"
        if aw: # during initialization aw is still None
            aw.CelsiusAction.setDisabled(True)
            aw.FahrenheitAction.setEnabled(True)
            aw.ConvertToCelsiusAction.setDisabled(True)
            aw.ConvertToFahrenheitAction.setEnabled(True)  

    def fahrenheitModeRedraw(self):
        self.fahrenheitMode()
        self.redraw()

    def celsiusModeRedraw(self):
        self.celsiusMode()
        self.redraw()


    #converts a loaded profile to a different temperature scale. t input is the requested mode (F or C).
    def convertTemperature(self,t):
        #verify there is a loaded profile
        profilelength = len(self.timex)
        if profilelength > 0:
            if t == u"F":
                string = QApplication.translate("MessageBox", "Convert profile data to Fahrenheit?",None, QApplication.UnicodeUTF8)
                reply = QMessageBox.question(self,QApplication.translate("MessageBox Caption", "Convert Profile Temperature",None, QApplication.UnicodeUTF8),string,
                        QMessageBox.Yes|QMessageBox.Cancel)
                if reply == QMessageBox.Cancel:
                    return 
                elif reply == QMessageBox.Yes:
                    if self.mode == u"C":
                        aw.CelsiusAction.setDisabled(True)
                        aw.FahrenheitAction.setEnabled(True)
                        aw.ConvertToCelsiusAction.setDisabled(True)
                        aw.ConvertToFahrenheitAction.setEnabled(True)
                        for i in range(profilelength):
                            self.temp1[i] = self.fromCtoF(self.temp1[i])    #ET
                            self.temp2[i] = self.fromCtoF(self.temp2[i])    #BT
                            if self.device != 18:
                                self.delta1[i] = self.fromCtoF(self.delta1[i])  #Delta ET
                                self.delta2[i] = self.fromCtoF(self.delta2[i])  #Delta BT

                        self.ambientTemp = self.fromCtoF(self.ambientTemp)  #ambient temperature
                        self.bag_humidity[1] = self.fromCtoF(self.bag_humidity[1]) #bag humidity temperature

                        for i in range(len(self.timeB)):
                            self.temp1B[i] = self.fromCtoF(self.temp1B[i])
                            self.temp2B[i] = self.fromCtoF(self.temp2B[i])
                                
                        self.fahrenheitMode()
                        aw.sendmessage(QApplication.translate("Message Area","Profile changed to Fahrenheit", None, QApplication.UnicodeUTF8))

                    else:
                        QMessageBox.information(self,QApplication.translate("MessageBox Caption", "Convert Profile Temperature",None, QApplication.UnicodeUTF8),
                                                QApplication.translate("MessageBox", "Unable to comply. You already are in Fahrenheit", None, QApplication.UnicodeUTF8))
                        aw.sendmessage(QApplication.translate("Message Area","Profile not changed", None, QApplication.UnicodeUTF8))
                        return

            elif t == u"C":
                string = QApplication.translate("MessageBox", "Convert profile data to Celsius?",None, QApplication.UnicodeUTF8)
                reply = QMessageBox.question(self,QApplication.translate("MessageBox Caption", "Convert Profile Temperature",None, QApplication.UnicodeUTF8),string,
                        QMessageBox.Yes|QMessageBox.Cancel)
                if reply == QMessageBox.Cancel:
                    return 
                elif reply == QMessageBox.Yes:
                    if self.mode == u"F":    
                        aw.ConvertToFahrenheitAction.setDisabled(True)
                        aw.ConvertToCelsiusAction.setEnabled(True) 
                        aw.FahrenheitAction.setDisabled(True)
                        aw.CelsiusAction.setEnabled(True)   
                        for i in range(profilelength):
                            self.temp1[i] = self.fromFtoC(self.temp1[i])    #ET
                            self.temp2[i] = self.fromFtoC(self.temp2[i])    #BT
                            if self.device != 18:
                                self.delta1[i] = self.fromFtoC(self.delta1[i])  #Delta ET
                                self.delta2[i] = self.fromFtoC(self.delta2[i])  #Delta BT

                        self.ambientTemp = self.fromFtoC(self.ambientTemp)  #ambient temperature
                        self.bag_humidity[1] = self.fromFtoC(self.bag_humidity[1])  #bag humidity temperature                        
                        
                        for i in range(len(self.timeB)):
                            self.temp1B[i] = self.fromFtoC(self.temp1B[i]) #ET B
                            self.temp2B[i] = self.fromFtoC(self.temp2B[i]) #BT B
                                
                    else:
                        QMessageBox.information(self,QApplication.translate("MessageBox Caption", "Convert Profile Temperature",None, QApplication.UnicodeUTF8),
                                                QApplication.translate("MessageBox", "Unable to comply. You already are in Celsius",None, QApplication.UnicodeUTF8))
                        aw.sendmessage(QApplication.translate("Message Area","Profile not changed", None, QApplication.UnicodeUTF8))
                        return

                    self.celsiusMode()
                    aw.sendmessage(QApplication.translate("Message Area","Profile changed to Celsius", None, QApplication.UnicodeUTF8))
                    
            self.redraw()

        else:
             QMessageBox.information(self,QApplication.translate("MessageBox Caption", "Convert Profile Scale",None, QApplication.UnicodeUTF8),
                                          QApplication.translate("MessageBox", "No profile data found",None, QApplication.UnicodeUTF8))
                                    

    #selects color mode: input 1=color mode; input 2=black and white mode (printing); input 3 = customize colors
    def changeGColor(self,color):
        #COLOR (option 1) Default
        palette1 = {"background":u'white',"grid":u'green',"ylabel":u'black',"xlabel":u'black',"title":u'black',"rect1":u'green',
                        "rect2":u'orange',"rect3":u'#996633',"et":u'red',"bt":u'#00007f',"deltaet":u'orange',
                        "deltabt":u'blue',"markers":u'black',"text":u'black',"watermarks":u'yellow',"Cline":u'blue'}

        #BLACK & WHITE (option 2) best for printing
        palette2 = {"background":u'white',"grid":u'grey',"ylabel":u'black',"xlabel":u'black',"title":u'black',"rect1":u'lightgrey',
                   "rect2":u'darkgrey',"rect3":u'grey',"et":u'black',"bt":u'black',"deltaet":u'grey',
                   "deltabt":u'grey',"markers":u'grey',"text":u'black',"watermarks":u'lightgrey',"Cline":u'grey'}
        
        #load selected dictionary
        if color == 1:
            aw.sendmessage(QApplication.translate("Message Area","Colors set to defaults", None, QApplication.UnicodeUTF8))
            for key in palette1.keys():
                self.palette[key] = palette1[key]
            
        if color == 2:
            aw.sendmessage(QApplication.translate("Message Area","Colors set to grey", None, QApplication.UnicodeUTF8))
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
                self.palette["et"] = unicode(dialog.metLabel.text())
                self.palette["bt"] = unicode(dialog.btLabel.text())
                self.palette["deltaet"] = unicode(dialog.deltametLabel.text())
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
        #create a new name ax1 instead of ax (ax is used when plotting profiles)
        
        self.ax1 = self.fig.add_subplot(111, projection='polar', axisbg=self.backcolor) #) radar green axisbg='#d5de9c'

        #find number of divisions
        nflavors = len(self.flavors)      #last value of nflavors is used to close circle (same as flavors[0])
            
        g_angle = numpy.arange(self.flavorstartangle,(360.+self.flavorstartangle),(360./nflavors))  #angles in degree
        self.ax1.set_thetagrids(g_angle)
        self.ax1.set_rmax(1.)
        self.ax1.set_autoscale_on(False)
        self.ax1.grid(True,linewidth=1.,color='black')


        #create water marks 6-7 anf 8-9
        self.ax1.bar(.1, .1, width=2.*pi, bottom=.6,color="green",linewidth=0.,alpha = .1)
        self.ax1.bar(.1, .1, width=2.*pi, bottom=.8,color="green",linewidth=0.,alpha = .1)

        #delete degrees ticks to anotate flavor characteristics 
        for tick in self.ax1.xaxis.get_major_ticks():
            tick.label1On = False

        #rename yaxis 
        locs = self.ax1.get_yticks()
        labels = []
        for i in range(len(locs)):
                stringlabel = str(locs[i]*10.)
                labels.append(stringlabel)              
        self.ax1.set_yticklabels(labels,color=self.palette["xlabel"])
                    
        step = 2.*pi/nflavors
        angles = [math.radians(self.flavorstartangle)]   #angles in radians
        for i in range(nflavors-1): angles.append(angles[-1] + step)

        #To close circle we need one more element. angle and values need same dimension in order to plot. 
        plotf = self.flavors[:]
        plotf.append(self.flavors[0])
        #normalize flavor values to 0-1 range
        for i in range(len(plotf)):
            plotf[i] /= 10.
        angles.append(angles[-1]+step)
        
        #anotate labels
        for i in range(len(self.flavorlabels)):
            if angles[i] > 2.*pi or angles[i] < 0.:
                p,angles[i] = divmod(angles[i],(2.*pi))
            if angles[i] <= (pi/2.) or angles[i] >= (1.5*pi): #if < 90 or smaller than 270 degress
                ha = "left"
            else:
                ha = "right"
            self.ax1.annotate(self.flavorlabels[i] + u" = " + unicode(u"%.2f"%self.flavors[i]),xy =(angles[i],.9),
                              xytext=(angles[i],1.1),horizontalalignment=ha,verticalalignment='bottom')
            
        score = 0.
        for i in range(nflavors):   
            score += self.flavors[i]
        score /= (nflavors)
        score *= 10.
        
        txt = u"%.2f" %score
        self.ax1.text(0.,0.,txt,fontsize=20,color="blue",horizontalalignment="center",bbox={"facecolor":"yellow", "alpha":0.3, "pad":10})

        #add background to plot if found
        if self.background:
            if self.flavorbackgroundflag:
                backgroundplotf = self.backgroundFlavors[:]
                backgroundplotf.append(self.backgroundFlavors[0])
                #normalize flavor values to 0-1 range
                for i in range(len(backgroundplotf)):
                    backgroundplotf[i] /= 10.

                self.ax1.plot(angles,backgroundplotf,color="orange",alpha=.5)
                #needs matplotlib 1.0.0+
                if mpl.__version__.split(".")[0] == '1':
                    self.ax1.fill_between(angles,0,backgroundplotf, facecolor="yellow", alpha=0.1, interpolate=True)
                
        #add to plot
        self.ax1.plot(angles,plotf,color="blue")
        
        #needs matplotlib 1.0.0+
        if mpl.__version__.split(".")[0] == '1':
            self.ax1.fill_between(angles,0,plotf, facecolor='green', alpha=0.1, interpolate=True)

        self.fig.canvas.draw()


    def findCenterWheelTextAngle(self,t):
        if t > 360 or t < 0:
            p,t = divmod(t,360)

        if t == 360. or t == 0.:
            return 270.
        #check cuadrants
        elif t < 90. and t > 0. or t > 360.:                #cuadrant 1
             return 270.+t
        elif t <= 180. and t >= 90.:            #cuadrant 2
             return t-90.
        elif t < 270. and t > 180.:             #cuadrant 3
             return t+90.
        else:                                 #cuadrant 4
            return t-270.

    def findRadialWheelTextAngle(self,t):
        if t > 360 or t < 0:
            p,t = divmod(t,360)
            
        if t <= 90. and t > 0. or t > 270.:    
            return t
        else:
            return 180.+t
       

    def drawWheel(self):
        try:
            pi = numpy.pi
            rad = 360./(2*pi)
            self.fig.clf()
            #create a new name ax1 instead of ax
            self.ax2 = self.fig.add_subplot(111, projection='polar', axisbg=self.backcolor)
            self.ax2.set_rmax(1.)
            self.ax2.set_autoscale_on(True)
            self.ax2.grid(False)

            #delete degrees ticks to anotate flavor characteristics 
            for tick in self.ax2.xaxis.get_major_ticks():
                tick.label1On = False
            #delete yaxis 
            locs = self.ax2.get_yticks()
            labels = [""]*len(locs)           
            self.ax2.set_yticklabels(labels)

            names = self.wheelnames[:]
            Wradii = self.wradii[:]
            startangle = self.startangle[:]
            projection = self.projection[:]

            #calculate text orientation
            wheels = len(names)

            if not wheels:
                self.fig.canvas.draw()
                return
            
            n,textangles,textloc = [],[],[]
            for i in range(wheels):
                l,tloc = [],[]
                count = self.startangle[i]
                #calculate text orientation
                for p in range(len(names[i])):
                    if projection[i] == 0:
                        l.append(0)
                    elif projection[i] == 1:
                        l.append(self.findCenterWheelTextAngle(3.6*self.segmentlengths[i][p]/2. + count))
                    elif projection[i] == 2:
                        l.append(self.findRadialWheelTextAngle(3.6*self.segmentlengths[i][p]/2. + count))
                    tloc.append((3.6*self.segmentlengths[i][p]/2. + count)/rad)
                    count += self.segmentlengths[i][p]*3.6

                textloc.append(tloc) 	    
                textangles.append(l)                   
                Wradii[i] = float(Wradii[i])/100.                   #convert radii to float between 0-1 range
                startangle[i] = startangle[i]/rad                 #convert angles to radians
                n.append(len(names[i]))                             #store the number of names for each wheel 

            
            #store the absolute len-radius origin of each circle
            lbottom = [0.]
            count = 0.
            for i in range(wheels-1):
                count += Wradii[i]
                lbottom.append(count)
         
            Wradiitext = [Wradii[0]/2.]
            for i in range(wheels-1):
                Wradiitext.append(lbottom[i+1] + Wradii[i+1]/2.)     #store absolute len-radius for text in each circle
                Wradii[i] += self.wheeledge    	    	    	        #create extra color edge between wheels by overlaping wheels
            #Generate Wheel graph    
            bar = []                                        	#holds bar-graphs (wheels)
            div = 2*pi/100.
            for z in range(len(n)):            
                #create wheel
                theta,segmentwidth,radii,colors = [],[],[],[]
                count = startangle[z]
                for i in range(n[z]):
                    theta.append(count)
                    count += div*self.segmentlengths[z][i]
                    segmentwidth.append(div*self.segmentlengths[z][i])                
                    radii.append(Wradii[z])                                
                bar.append(self.ax2.bar(theta, radii, width=segmentwidth, bottom=lbottom[z],edgecolor=self.wheellinecolor,linewidth=self.wheellinewidth))
                count = 0
                #set color, alpha, and text
                for r,bar[z] in zip(radii, bar[z]):
                    bar[z].set_facecolor(self.wheelcolor[z][count])
                    bar[z].set_alpha(self.segmentsalpha[z][count])
                    self.ax2.annotate(names[z][count],xy=(textloc[z][count],Wradiitext[z]),xytext=(textloc[z][count],Wradiitext[z]),
                        rotation=textangles[z][count],horizontalalignment="center",verticalalignment="center",fontsize=self.wheeltextsize[z])
                    count += 1  
            self.fig.canvas.draw()            

        except ValueError,e:
            self.adderror(QApplication.translate("Error Message", "Value Error: drawWheel() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

        except Exception,e:
            self.adderror(QApplication.translate("Error Message", "Exception Error: drawWheel() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

    def makewheelcolorpattern(self): 
        for x in range(len(self.wheelcolor)):
            wlen = len(self.wheelcolor[x])
            for i in range(wlen):
                color = QColor()
                color.setHsv((360/wlen)*i*self.wheelcolorpattern,255,255,255)
                self.wheelcolor[x][i] = unicode(color.name())
        
    # sets parent and corrects segment lengths so that child fits inside parent (multiple children can be set to same parent)
    # input: z = index of parent in previus wheel    # x = wheel number    # i = index of element in wheel x
    def setwheelchild(self,z,x,i):
        #set same start angle
        self.startangle[x] = self.startangle[x-1]
        self.wheellabelparent[x][i] = z

        #adjust lengths
        for x in range(1,len(self.segmentlengths)):
            nsegments = len(self.segmentlengths[x])        
            parentanglecount = 0
            for i in range(nsegments):
                if  self.wheellabelparent[x][i]:                                                  #if parent selected (otherwise 0) 
                    parentindex = self.wheellabelparent[x][i]                                     #parent index
                    if self.wheellabelparent[x][i] == parentindex:                                #if match
                        parentangle = self.segmentlengths[x-1][self.wheellabelparent[x][i]-1]     #find parent angle (in %)
                        #find number of labels with same parent
                        count = self.wheellabelparent[x].count(parentindex)                       #count number of labels with same parent
                        self.segmentlengths[x][i] = parentangle/count                             #divide parent angle between children

                        #calculate last total angle
                        if i < nsegments-1:
                            parentanglecount += self.segmentlengths[x][i]

                        #adjust rest of angles to get 100 % coverage
                        for a in range(i+1,nsegments):
                            self.segmentlengths[x][a] = (100-parentanglecount)/(nsegments-(i+1))

    #adjusts size of all segements of the graph based on child parent relation
    #expects all segments to have a parent except in the first wheel
    def setWheelHierarchy(self):
        #check for not stablished relashionships (will cause graph plotting problems) and give warning
        for x in range(1,len(self.wheellabelparent)):
            for i in range(len(self.wheellabelparent[x])):
                if self.wheellabelparent[x][i] == 0:
                    QMessageBox.information(self,u"Wheel Hierarchy Problem",
                    "Please assign a  a parent to wheel #%i element#%i: \n\n%s"%(x+1,i+1,self.wheelnames[x][i]))
                    return        
        
        #adjust top wheel and make all segments equal
        for i in range(len(self.segmentlengths[-1])):
            self.segmentlengths[-1][i] = 100./len(self.segmentlengths[-1])

        #adjust lower wheels based on previous wheels
        for p in range(len(self.wheellabelparent)-1,0,-1):
            nsegments = len(self.wheellabelparent[p])
            nparentsegments = len(self.wheellabelparent[p-1])
            angles = [0]*nparentsegments
            for x in range(nparentsegments):
                for i in range(nsegments):
                    if self.wheellabelparent[p][i]-1 == x:
                        angles[x] += self.segmentlengths[p][i]

            #adjust angle length of parents proportionaly          
            for i in range(nparentsegments):
                self.segmentlengths[p-1][i] = angles[i]

        self.drawWheel() 
##########################################################################################################################                                   


    #Turns ON/OFF flag self.flagon to read and plot. Called from push button_1. 
    def OnMonitor(self):
        if not self.flagon:
            if self.designerflag: return
            
            self.threadserver.createSampleThread()
            
            aw.sendmessage(QApplication.translate("Message Area","Scope recording...", None, QApplication.UnicodeUTF8))
            aw.button_1.setStyleSheet(aw.pushbuttonstyles["ON"])            
            aw.button_1.setText(QApplication.translate("Scope Button", "OFF",None, QApplication.UnicodeUTF8)) # text means click to turn OFF (it is ON)                   
            aw.soundpop()
            
            if not len(self.timex):
                self.timeclock.start()   #set time to the current computer time
                self.updateLCDtime()
            else:
                self.updateLCDtime()
                
        else:
            self.flagon = False
            aw.button_1.setStyleSheet(aw.pushbuttonstyles["OFF"])
            aw.soundpop()
            aw.sendmessage(QApplication.translate("Message Area","Scope stopped", None, QApplication.UnicodeUTF8))
            aw.button_1.setText(QApplication.translate("Scope Button", "ON",None, QApplication.UnicodeUTF8))
            libtime.sleep(.5)  #give time for thread to close


    #Records charge (put beans in) marker. called from push button 'Charge'
    def markCharge(self):
        if self.flagon:
            if self.device != 18:
                if len(self.timex) >= 3:
                    self.timeindex[0] = len(self.timex)-1
                else:
                    message = QApplication.translate("Message Area","Not enough variables collected yet. Try again in a few seconds", None, QApplication.UnicodeUTF8)
            #device 18  = manual mode        
            else:
                tx = self.timeclock.elapsed()/1000.
                et,bt = aw.ser.NONE()
                if bt != 1 and et != -1:  #cancel
                    self.drawmanual(et,bt,tx)
                    self.timeindex[0] = len(self.timex)-1
                else:
                    return
                
            self.xaxistosm()    
            
            message = QApplication.translate("Message Area","Roast time starts now 00:00 BT = %1",None, QApplication.UnicodeUTF8).arg(unicode(self.temp2[self.timeindex[0]]) + self.mode)
            aw.sendmessage(message) 
            aw.button_8.setDisabled(True)
            aw.button_8.setFlat(True)            

            aw.soundpop()
            self.redraw()
            
        else:
            message = QApplication.translate("Message Area","Scope is OFF", None, QApplication.UnicodeUTF8)
            aw.sendmessage(message)

    def markDryEnd(self):
        if self.flagon:
            if self.device != 18:
                self.timeindex[1] = len(self.timex)-1
            else:
                tx = self.timeclock.elapsed()/1000.
                et,bt = aw.ser.NONE()
                if et != -1 and bt != -1:
                    self.drawmanual(et,bt,tx)
                    self.timeindex[1] = len(self.timex)-1
                else:
                    return
                
            if aw.qmc.phasesbuttonflag:     
                self.phases[1] = int(round(self.temp2[self.timeindex[1]]))                

            aw.button_19.setDisabled(True)
            aw.button_19.setFlat(True)
            
            st1 = self.stringfromseconds(self.timex[self.timeindex[1]]-self.timex[self.timeindex[0]])
            st2 = "%.1f "%self.temp2[self.timeindex[1]] + self.mode
            message = QApplication.translate("Message Area","[DRY END] recorded at %1 BT = %2", None, QApplication.UnicodeUTF8).arg(st1).arg(st2)
            #set message at bottom
            aw.sendmessage(message)
            aw.soundpop()
            self.redraw()
                        
        else:
            message = QApplication.translate("Message Area","Scope is OFF", None, QApplication.UnicodeUTF8)
            aw.sendmessage(message)

    #redord 1C start markers of BT. called from push button_3 of application window
    def mark1Cstart(self):
        if self.flagon:
            # record 1Cs only if Charge mark has been done
            if self.device != 18:                
                self.timeindex[2] = len(self.timex)-1
            else:
                tx = self.timeclock.elapsed()/1000.
                et,bt = aw.ser.NONE()
                if et != -1 and bt != -1:
                    self.drawmanual(et,bt,tx)                               
                    self.timeindex[2] = len(self.timex)-1
                else:
                    return

            if aw.qmc.phasesbuttonflag:     
                self.phases[2] = int(round(self.temp2[self.timeindex[2]]))
            
            aw.button_3.setDisabled(True)
            aw.button_3.setFlat(True)
            
            st1 = self.stringfromseconds(self.timex[self.timeindex[2]]-self.timex[self.timeindex[0]])
            st2 = "%.1f "%self.temp2[self.timeindex[2]] + self.mode
            message = QApplication.translate("Message Area","[FC START] recorded at %1 BT = %2", None, QApplication.UnicodeUTF8).arg(st1).arg(st2)            
            aw.sendmessage(message)
            aw.soundpop()
            self.redraw()
            
        else:
            message = QApplication.translate("Message Area","Scope is OFF", None, QApplication.UnicodeUTF8)
            aw.sendmessage(message)
        
    #record 1C end markers of BT. called from button_4 of application window
    def mark1Cend(self):
        if self.flagon:
 
            if self.device != 18:
                self.timeindex[3] = len(self.timex)-1
            else:
                tx = self.timeclock.elapsed()/1000.
                et,bt = aw.ser.NONE()
                if et != -1 and bt != -1:
                    self.drawmanual(et,bt,tx)                           
                    self.timeindex[3] = len(self.timex)-1
                else:
                    return                    

            aw.button_4.setDisabled(True)
            aw.button_4.setFlat(True)
            
            st1 = self.stringfromseconds(self.timex[self.timeindex[3]]-self.timex[self.timeindex[0]])                           
            st2 = "%.1f "%self.temp2[self.timeindex[3]] + self.mode
            message = QApplication.translate("Message Area","[FC END] recorded at %1 BT = %2", None, QApplication.UnicodeUTF8).arg(st1).arg(st2)
            aw.sendmessage(message)
            aw.soundpop()
            self.redraw()
            
        else:
            message = QApplication.translate("Message Area","Scope is OFF", None, QApplication.UnicodeUTF8)
            aw.sendmessage(message)

    #record 2C start markers of BT. Called from button_5 of application window
    def mark2Cstart(self):
        if self.flagon:
            if self.device != 18:
                self.timeindex[4] = len(self.timex)-1
            else:
                tx = self.timeclock.elapsed()/1000.
                et,bt = aw.ser.NONE()
                if et != -1 and bt != -1:
                    self.drawmanual(et,bt,tx)                           
                    self.timeindex[4] = len(self.timex)-1
                else:
                    return              

            aw.button_5.setDisabled(True)
            aw.button_5.setFlat(True)

            st1 = self.stringfromseconds(self.timex[self.timeindex[4]]-self.timex[self.timeindex[0]])
            st2 = "%.1f "%self.temp2[self.timeindex[4]] + self.mode            
            message = QApplication.translate("Message Area","[SC START] recorded at %1 BT = %2", None, QApplication.UnicodeUTF8).arg(st1).arg(st2)
            aw.sendmessage(message)
            aw.soundpop()
            self.redraw()
            
        else:
            message = QApplication.translate("Message Area","Scope is OFF", None, QApplication.UnicodeUTF8)
            aw.sendmessage(message)            
       
    #record 2C end markers of BT. Called from button_6  of application window
    def mark2Cend(self):
        if self.flagon:
            
            if self.device != 18:                
                self.timeindex[5] = len(self.timex)-1
            else:
                tx = self.timeclock.elapsed()/1000.
                et,bt = aw.ser.NONE()
                if et != -1 and bt != -1:
                    self.drawmanual(et,bt,tx)                           
                    self.timeindex[5] = len(self.timex)-1
                else:
                    return
                
            aw.button_6.setDisabled(True)
            aw.button_6.setFlat(True)

            st1 = self.stringfromseconds(self.timex[self.timeindex[5]]-self.timex[self.timeindex[0]])
            st2 = "%.1f "%self.temp2[self.timeindex[5]] + self.mode
            message = QApplication.translate("Message Area","[SC END] recorded at %1 BT = %2", None, QApplication.UnicodeUTF8).arg(st1).arg(st2)
            aw.sendmessage(message)            
            aw.soundpop()
            self.redraw()
            
        else:
            message = QApplication.translate("Message Area","Scope is OFF", None, QApplication.UnicodeUTF8)
            aw.sendmessage(message)            

    #record end of roast (drop of beans). Called from push button 'Drop'
    def markDrop(self):
        if self.flagon:
            if self.device != 18:        
                self.timeindex[6] = len(self.timex)-1
            else:
                tx = self.timeclock.elapsed()/1000.
                et,bt = aw.ser.NONE()
                if et != -1 and bt != -1:
                    self.drawmanual(et,bt,tx)
                    self.timeindex[6] = len(self.timex)-1
                else:
                    return
                
            aw.button_9.setDisabled(True)
            aw.button_9.setFlat(True)
            
            st1 = self.stringfromseconds(self.timex[self.timeindex[6]]-self.timex[self.timeindex[0]])
            st2 = "%.1f "%self.temp2[self.timeindex[6]] + self.mode
            message = QApplication.translate("Message Area","Roast ended at %1 BT = %2", None, QApplication.UnicodeUTF8).arg(st1).arg(st2)
            aw.sendmessage(message)
            aw.soundpop()
            self.redraw()
            
            #prevents accidentally deleting a finished roast
            self.safesaveflag = True
        else:
            message = QApplication.translate("Message Area","Scope is OFF", None, QApplication.UnicodeUTF8)
            aw.sendmessage(message)
            

    #Marks location in graph of special events. For example change a fan setting.
    #Uses the position of the time index (variable self.timex) as location in time           
    def EventRecord(self):
        try:
            if self.flagon:
                #[EVENT] push button feedback
                aw.button_11.setFlat(True)
                aw.button_11.setDisabled(True)
                QTimer.singleShot(2000, self.restorebutton_11)
                
                Nevents = len(self.specialevents)
                #if in manual mode record first the last point in self.timex[]
                if self.device == 18:
                    tx = self.timeclock.elapsed()/1000.
                    et,bt = aw.ser.NONE()
                    if bt != 1 and et != -1:              
                        self.drawmanual(et,bt,tx)                        
                    else:
                        return
                #i = index number of the event (current length of the time list)           
                i = len(self.timex)-1

                self.specialevents.append(i)
                self.specialeventstype.append(0)            
                self.specialeventsStrings.append(str(Nevents+1))
                self.specialeventsvalue.append(0)               
                
                temp = unicode(self.temp2[i])
                timed = self.stringfromseconds(self.timex[i])

                message = QApplication.translate("Message Area","Event # %1 recorded at BT = %2 Time = %3", None, QApplication.UnicodeUTF8).arg(unicode(Nevents+1)).arg(temp).arg(timed)
                aw.sendmessage(message)
                #write label in mini recorder if flag checked
                if aw.minieventsflag:
                    aw.eNumberSpinBox.setValue(Nevents+1)
                    aw.etypeComboBox.setCurrentIndex(self.specialeventstype[Nevents-1])
                    aw.valueComboBox.setCurrentIndex(self.specialeventsvalue[Nevents-1])
                    aw.lineEvent.setText(self.specialeventsStrings[Nevents])
                    
                self.redraw()     
                aw.soundpop()

            else:
                aw.sendmessage(QApplication.translate("Message Area","Timer is OFF", None, QApplication.UnicodeUTF8))

        except Exception,e:
            self.adderror(QApplication.translate("Error Message", "Exception Error: EventRecord() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

    #called from controlling devices when roasting to record steps (commands) and produce a profile later
    def DeviceEventRecord(self,command):
        if self.flagon:
            #number of events
            Nevents = len(self.specialevents)
            #index number            
            i = len(self.timex)-1
            if i > 0:
                self.specialevents.append(i)                                     # store absolute time index
                self.specialeventstype.append(0)                                 # set type (to the first index 0)          
                self.specialeventsStrings.append(command)                        # store the command in the string section of events (not a binary string)   
                self.specialeventsvalue.append(0)                                # empty
                temp = unicode(self.temp2[i])
                if self.timeindex[0] != -1:
                    start = self.timex[self.timeindex[0]]
                else:
                    start = 0
                timed = self.stringfromseconds(self.timex[i]-start)
                message = QApplication.translate("Message Area","Computer Event # %1 recorded at BT = %2 Time = %3", None, QApplication.UnicodeUTF8).arg(unicode(Nevents+1)).arg(temp).arg(timed)
                aw.sendmessage(message)
                #write label in mini recorder if flag checked
                if aw.minieventsflag:
                    aw.eNumberSpinBox.setValue(Nevents+1)
                    aw.etypeComboBox.setCurrentIndex(self.specialeventstype[Nevents-1])
                    aw.valueComboBox.setCurrentIndex(self.specialeventsvalue[Nevents-1])
                    aw.lineEvent.setText(self.specialeventsStrings[Nevents])
                self.redraw()

    # Writes information about the finished profile in the graph
    def writestatistics(self):
        
        TP_index = aw.findTP()
        if self.timeindex[1] and aw.qmc.phasesbuttonflag:
            #manual dryend available
            dryEndTime = self.timex[self.timeindex[1]]
            BTdrycross = self.temp2[self.timeindex[1]]
            dryEndIndex = self.timeindex[1]
        else:
            #find when dry phase ends 
            dryEndIndex = aw.findDryEnd(TP_index)
            dryEndTime = self.timex[dryEndIndex]
            BTdrycross = self.temp2[dryEndIndex]  

        #if DROP             
        if self.timeindex[6]:
            totaltime = int(self.timex[self.timeindex[6]]-self.timex[self.timeindex[0]])
            if totaltime == 0:
                aw.sendmessage(QApplication.translate("Message Area","Statistics cancelled: need complete profile [CHARGE] + [DROP]", None, QApplication.UnicodeUTF8))
                return
                        
            self.statisticstimes[0] = totaltime
            #if 1Ce use middle point of 1Cs and 1Ce            
            if self.timex[self.timeindex[3]]:
                
                dryphasetime = int(dryEndTime - self.timex[self.timeindex[0]])
                midphasetime = int(self.timex[self.timeindex[2]] - dryEndTime)
                finishphasetime = int(self.timex[self.timeindex[6]]- self.timex[self.timeindex[2]])
                                   
            else: #very light roast)
                #use 1Cs (start of 1C) as 1C
                dryphasetime = int(dryEndTime - self.timex[self.timeindex[0]])
                midphasetime = int(self.timex[self.timeindex[2]] - dryEndTime)     
                finishphasetime = int(self.timex[self.timeindex[6]] - self.timex[self.timeindex[2]])
                
            self.statisticstimes[1] = dryphasetime
            self.statisticstimes[2] = midphasetime
            self.statisticstimes[3] = finishphasetime

            #dry time string
            st1 = self.stringfromseconds(dryphasetime)

            #mid time string
            st2 = self.stringfromseconds(midphasetime)               

            #finish time string
            st3 = self.stringfromseconds(finishphasetime)

            #calculate the positions for the statistics elements
            ydist = self.ylimit - self.ylimit_min
            statisticsbarheight = ydist/80
            statisticsheight = self.ylimit - (0.13 * ydist)
            statisticsupper = statisticsheight + statisticsbarheight + 2
            statisticslower = statisticsheight - statisticsbarheight - ydist / 50.
            
            if self.statisticsflags[1]:
                
                #Draw finish phase rectangle
                #chech to see if end of 1C exists. If so, use half between start of 1C and end of 1C. Otherwise use only the start of 1C
                rect = patches.Rectangle( (self.timex[self.timeindex[2]], statisticsheight), width = finishphasetime, height = statisticsbarheight,
                                            color = self.palette["rect3"],alpha=0.5)
                self.ax.add_patch(rect)
                
                # Draw mid phase rectangle
                rect = patches.Rectangle( (self.timex[self.timeindex[0]]+dryphasetime, statisticsheight), width = midphasetime, height = statisticsbarheight,
                                          color = self.palette["rect2"],alpha=0.5)
                self.ax.add_patch(rect)

                # Draw dry phase rectangle
                rect = patches.Rectangle( (self.timex[self.timeindex[0]], statisticsheight), width = dryphasetime, height = statisticsbarheight,
                                          color = self.palette["rect1"],alpha=0.5)
                self.ax.add_patch(rect)

            
            dryphaseP = dryphasetime*100/totaltime
            midphaseP = midphasetime*100/totaltime
            finishphaseP = finishphasetime*100/totaltime
                        
            #find Lowest Point in BT
            LP = 1000 
            if TP_index >= 0:
                LP = self.temp2[TP_index]

            if self.statisticsflags[0]:            
                self.ax.text(self.timex[self.timeindex[0]]+ dryphasetime/3,statisticsupper,st1 + u" "+ unicode(int(dryphaseP))+u"%",color=self.palette["text"])
                self.ax.text(self.timex[self.timeindex[0]]+ dryphasetime+midphasetime/3,statisticsupper,st2+ " " + unicode(int(midphaseP))+u"%",color=self.palette["text"])
                self.ax.text(self.timex[self.timeindex[0]]+ dryphasetime+midphasetime+finishphasetime/3,statisticsupper,st3 + u" " + unicode(int(finishphaseP))+ u"%",color=self.palette["text"])

            if self.statisticsflags[2]:
                (st1,st2,st3) = aw.defect_estimation()

                rates_of_changes = aw.RoR(TP_index,dryEndIndex)

                st1 = st1 + " (%.1f "%rates_of_changes[0]  + QApplication.translate("Scope Label", "deg/min",None, QApplication.UnicodeUTF8) + ")"
                st2 = st2 + " (%.1f "%rates_of_changes[1]  + QApplication.translate("Scope Label", "deg/min",None, QApplication.UnicodeUTF8) + ")"
                st3 = st3 + " (%.1f "%rates_of_changes[2]  + QApplication.translate("Scope Label", "deg/min",None, QApplication.UnicodeUTF8) + ")"
        
                #Write flavor estimation
                self.ax.text(self.timex[self.timeindex[0]] + dryphasetime/2-len(st1)*8/2,statisticslower,st1,color=self.palette["text"],fontsize=11)
                self.ax.text(self.timex[self.timeindex[0]] + dryphasetime+midphasetime/2-len(st2)*8/2,statisticslower,st2,color=self.palette["text"],fontsize=11)
                self.ax.text(self.timex[self.timeindex[0]] + dryphasetime+midphasetime+finishphasetime/2-len(st3)*8/2,statisticslower,st3,color=self.palette["text"],fontsize=11)

            if self.statisticsflags[3]:
                #calculate AREA under BT and ET
                AccBT = 0.0
                AccMET = 0.0

                #find the index of time when the roasts starts and finish 
                for i in range(len(self.timex)):
                    if self.timex[i] > self.timex[self.timeindex[0]]:
                        break            
                for j in range(len(self.timex)):
                    if self.timex[j] > self.timex[self.timeindex[6]]:
                        break

                for k in range(i,j):
                    timeD = self.timex[k+1] - self.timex[k]
                    AccBT += self.temp2[k]*timeD
                    AccMET += self.temp1[k]*timeD
                    
                deltaAcc = int(AccMET) - int(AccBT)
                        
                lowestBT = u"%.1f"%LP
                #timeLP = unicode(self.stringfromseconds(self.timex[k] - self.timex[self.timeindex[0]]))
                timez = self.stringfromseconds(self.timex[self.timeindex[6]]-self.timex[self.timeindex[0]])
                #end temperature

                strline = QApplication.translate("Scope Label", "[BT = %1 - %2] [ETarea - BTarea = %3] [Time = %4]", None,
                          QApplication.UnicodeUTF8).arg(lowestBT + self.mode).arg(u"%.1f"%self.temp2[self.timeindex[6]] + self.mode).arg(unicode(deltaAcc)).arg(timez)                              
                            
                #text metrics 
                #if self.mode == u"C":
                #    dist = -47
                #    dist = -100
                #else:
                #    dist = -90
                #self.ax.text(-100,dist, strline,color = self.palette["text"],fontsize=11)
                
                #alternative
                #factor = (aw.qmc.ylimit - aw.qmc.ylimit_min) / 10.8
                #self.ax.text(0,aw.qmc.ylimit_min - factor, strline,color = self.palette["text"],fontsize=11)
                
                # even better: use xlabel
                self.ax.set_xlabel(strline,size=11,color = aw.qmc.palette["text"])
            else:
                self.ax.set_xlabel(QApplication.translate("Scope Label", "Time",None, QApplication.UnicodeUTF8),size=16,color = self.palette["xlabel"])

    #used in EventRecord()
    def restorebutton_11(self):
        aw.button_11.setDisabled(False)
        aw.button_11.setFlat(False)        

            
    #called from markdryen(), markcharge(), mark1Cstart(), etc when using device 18 (manual mode)
    def drawmanual(self,et,bt,tx):
        self.temp1.append(et)
        self.l_temp1.set_data(self.timex, self.temp1)
        self.temp2.append(bt)
        self.timex.append(tx)
        self.l_temp2.set_data(self.timex, self.temp2)
               
    def movebackground(self,direction,step):
        lt = len(self.timeB)
        le = len(self.temp1B)
        lb = len(self.temp2B)
        #all background curves must have same dimension in order to plot. Check just in case.
        if lt > 1 and lt == le and lb == le:
            if  direction == u"up":
                for i in range(lt):
                    self.temp1B[i] += step
                    self.temp2B[i] += step
                                    
            elif direction == u"left":
                for i in range(lt):
                    self.timeB[i] -= step
                                   
            elif direction == u"right":
                for i in range(lt):
                    self.timeB[i] += step
                
            elif direction == u"down":
                for i in range(lt):
                    self.temp1B[i] -= step
                    self.temp2B[i] -= step
                    
        else:
            aw.sendmessage(QApplication.translate("Message Area","Unable to move background", None, QApplication.UnicodeUTF8))
            return

    #points are used to draw interpolation
    def findpoints(self):
        #if profile found
        if self.timeindex[0] != -1:
            Xpoints = []                        #make temporary lists to hold the values to return
            Ypoints = []
            
            #start point from begining of time
            Xpoints.append(self.timex[0])
            Ypoints.append(self.temp2[0])
            #input beans (CHARGE)
            Xpoints.append(self.timex[self.timeindex[0]])
            Ypoints.append(self.temp2[self.timeindex[0]])

            #find indexes of lowest point and dryend            
            LPind = aw.findTP()
            DE = aw.findDryEnd()

            if LPind < DE:
                Xpoints.append(self.timex[LPind])
                Ypoints.append(self.temp2[LPind])
                Xpoints.append(self.timex[DE])
                Ypoints.append(self.temp2[DE])
            else:
                Xpoints.append(self.timex[DE])
                Ypoints.append(self.temp2[DE])                
                Xpoints.append(self.timex[LPind])
                Ypoints.append(self.temp2[LPind])
                
            if self.temp2[self.timeindex[1]] > self.timex[DE] and self.temp2[self.timeindex[1]] > self.timex[LPind]:
                Xpoints.append(self.timex[self.timeindex[1]])
                Ypoints.append(self.temp2[self.timeindex[1]])
            if self.timeindex[2]:
                Xpoints.append(self.timex[self.timeindex[2]])
                Ypoints.append(self.temp2[self.timeindex[2]])
            if self.timeindex[3]:
                Xpoints.append(self.timex[self.timeindex[3]])
                Ypoints.append(self.temp2[self.timeindex[3]])            
            if self.timeindex[4]:
                Xpoints.append(self.timex[self.timeindex[4]])
                Ypoints.append(self.temp2[self.timeindex[4]])       
            if self.timeindex[5]:
                Xpoints.append(self.timex[self.timeindex[5]])
                Ypoints.append(self.temp2[self.timeindex[5]])
            if self.timeindex[6]:
                Xpoints.append(self.timex[self.timeindex[6]])
                Ypoints.append(self.temp2[self.timeindex[6]])            
            
            #end point
            if self.timex[self.timeindex[6]] != self.timex[-1]:
                Xpoints.append(self.timex[-1])
                Ypoints.append(self.temp2[-1])
                
            return Xpoints,Ypoints
        
        else:
            aw.sendmessage(QApplication.translate("Message Area","No finished profile found", None, QApplication.UnicodeUTF8))
            return [],[]

    #collects info about the univariate interpolation
    def univariateinfo(self):
        try:
            
            Xpoints,Ypoints = self.findpoints()  #from lowest point to avoid many coeficients
            equ = inter.UnivariateSpline(Xpoints, Ypoints)
            coeffs = equ.get_coeffs().tolist()
            knots = equ.get_knots().tolist()
            resid = equ.get_residual()
            roots = equ.roots().tolist()

            #interpretation of coefficients: http://www.sagenb.org/home/pub/1708/
            #spline=[ans[0,i]+(x-xi)*(ans[1,i]+(x-xi)*(ans[2,i]+(x-xi)*ans[3,i]/3)/2) for i,xi in enumerate(a[:-1])]
            
            string = "<b>" + QApplication.translate("MessageBox","Polynomial coefficients (Horner form):",
                                                    None, QApplication.UnicodeUTF8) + "</b><br><br>"
            string += str(coeffs) + "<br><br>"
            string += "<b>" + QApplication.translate("MessageBox","Knots:",
                                                     None, QApplication.UnicodeUTF8) + "</b><br><br>"
            string += str(knots)+ "<br><br>"
            string += "<b>" + QApplication.translate("MessageBox","Residual:",
                                                     None, QApplication.UnicodeUTF8) + "</b><br><br>"
            string += str(resid)  + "<br><br>"      
            string += "<b>" + QApplication.translate("MessageBox","Roots:",
                                                     None, QApplication.UnicodeUTF8) + "</b><br><br>"
            string += str(roots)
            
            QMessageBox.information(self,QApplication.translate("MessageBox Caption","Profile information",None, QApplication.UnicodeUTF8),string)

        except ValueError,e:
            self.adderror(QApplication.translate("Error Message","Value Error: univariateinfo() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

        except Exception,e:
            self.adderror(QApplication.translate("Error Message","Exception Error: univariateinfo() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return  
                                   
    #interpolation type        
    def univariate(self):
        try:           
            Xpoints,Ypoints = self.findpoints()  
            
            func = inter.UnivariateSpline(Xpoints, Ypoints)
            
            xa = numpy.array(self.timex)
            newX = func(xa).tolist()
               
            self.ax.plot(self.timex, newX, color="black", linestyle = '-.', linewidth=3)            
            self.ax.plot(Xpoints, Ypoints, "ro")
            
            self.fig.canvas.draw()

        except ValueError:
            self.adderror(QApplication.translate("Error Message","value Error: univariate() ",None, QApplication.UnicodeUTF8))
            return

        except Exception:
            self.adderror(QApplication.translate("Error Message","Exception: univariate() ",None, QApplication.UnicodeUTF8))
            return  
            
    def drawinterp(self,mode):
        try:
            
            Xpoints,Ypoints = self.findpoints() #from 0 origin
            func = inter.interp1d(Xpoints, Ypoints, kind=mode)
            newY = func(self.timex)          
            self.ax.plot(self.timex, newY, color="black", linestyle = '-.', linewidth=3)            
            self.ax.plot(Xpoints, Ypoints, "ro")
            
            self.fig.canvas.draw()

        except ValueError,e:
            self.adderror(QApplication.translate("Error Message","value error in drawinterp() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

        except Exception,e:
            self.adderror(QApplication.translate("Error Message","Exception: drawinterp() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return        

    # predicate that returns true if the given temperature reading is out of range
    def outOfRange(self,t):
        if self.mode == "C":
            return t < 1. or t > 500.
        else:
            return t < 1. or t > 800.
        
    # return -1 for probes not connected with output outside of range: -25 to 700 or 
    # the previous values if available
    def filterDropOuts(self,t1,t2):
        if self.outOfRange(t1):
            if len(self.timex) > 2:
                t1 = self.temp1[-1]
            else:
                t1 = -1
        if self.outOfRange(t2):
            if len(self.timex) > 2:
                t2 = self.temp2[-1]
            else:
                t2 = -1
                
        return t1,t2

    #selects closest time INDEX in self.timex from a given input float seconds
    def time2index(self,seconds):
        #find where given seconds crosses aw.qmc.timex
        if len(self.timex):                           #check that time is not empty just in case
            #if input seconds longer than available time return last index
            if  seconds > self.timex[-1]:
                return len(self.timex)-1

            #if given input seconds smaller than first time return first index
            if seconds < self.timex[0]:
                return 0
            
            for i in range(len(self.timex)):
                # first find the index i where seconds crosses timex
                if self.timex[i] > seconds:
                    break

            #look around    
            choice1 = abs(self.timex[i] - seconds)
            choice2 = abs(self.timex[i-1] - seconds)

            #return closest (smallest) index
            if choice1 <= choice2:  
                return i
            elif choice2 < choice1:
                return i-1

    #selects closest time INDEX in self.timeB from a given input float seconds
    def backgroundtime2index(self,seconds):
        #find where given seconds crosses aw.qmc.timex
        if len(self.timeB):                           #check that time is not empty just in case
            #if input seconds longer than available time return last index
            if  seconds > self.timeB[-1]:
                return len(self.timeB)-1

            #if given input seconds smaller than first time return first index
            if seconds < self.timeB[0]:
                return 0
            
            for i in range(len(self.timeB)):
                # first find the index i where seconds crosses timex
                if self.timeB[i] > seconds:
                    break

            #look around    
            choice1 = abs(self.timeB[i] - seconds)
            choice2 = abs(self.timeB[i-1] - seconds)

            #return closest (smallest) index
            if choice1 <= choice2:  
                return i
            elif choice2 < choice1:
                return i-1

    #updates list self.timeindex when found an _OLD_ profile without self.timeindex (new version)
    def timeindexupdate(self,times):
        #          START            DRYEND          FCs             FCe         SCs         SCe         DROP
#        times = [self.startend[0],self.dryend[0],self.varC[0],self.varC[2],self.varC[4],self.varC[6],self.startend[2]]
        for i in range(len(times)):               
            if times[i]:
                self.timeindex[i] = self.time2index(times[i])
            else:
                self.timeindex[i] = 0


    #updates list self.timeindexB when found an _OLD_ profile without self.timeindexB 
    def timebackgroundindexupdate(self,times):
##        #          STARTB            DRYENDB          FCsB       FCeB         SCsB         SCeB               DROPB
##        times = [self.startendB[0],self.dryendB[0],self.varCB[0],self.varCB[2],self.varCB[4],self.varCB[6],self.startendB[2]]
        for i in range(len(times)):               
            if times[i]:
                self.timeindexB[i] = self.backgroundtime2index(times[i])
            else:
                self.timeindexB[i] = 0

    #adds errors
    def adderror(self,error):
        timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
        #keep a max of 500 errors
        if len(self.errorlog) > 499:
            self.errorlog = self.errorlog[1:]
        self.errorlog.append(timez + " " + error)
        aw.sendmessage(error)

    ####################  PROFILE DESIGNER   ###################################################################################
    #launches designer	
    def designer(self):       
        if len(self.timex):
            reply = QMessageBox.question(self,QApplication.translate("MessageBox Caption","Designer Start",None, QApplication.UnicodeUTF8),
                                         QApplication.translate("MessageBox","Importing a profile in to Designer will decimate\nall data except the main [points].\nContinue?",None, QApplication.UnicodeUTF8),
                                         QMessageBox.Yes|QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.initfromprofile()
                self.connect_designer()
                return
            elif reply == QMessageBox.Cancel:
                return #exit

        #if no profile found
        self.reset()
        self.connect_designer()
        self.designerinit()       
        
    #used to start designer from scracth (not from a loaded profile)	
    def designerinit(self):
        #init start vars        #CH, DE, Fcs,Fce,Scs,Sce,Drop
        self.designertimeinit = [50,300,540,570,660,700,800]
        if self.mode == u"C":
                                      #CH, DE, Fcs,Fce,Scs,Sce,Drop  
            self.designertemp1init = [290.,290.,290.,290.,290.,290.,290.]
            self.designertemp2init = [200.,150.,200.,210.,220.,225.,240.]   #CHARGE,DRY END,FCs, FCe,SCs,SCe,DROP
        elif self.mode == u"F":
            self.designertemp1init = [500.,500.,500.,500.,500.,500.,500.]
            self.designertemp2init = [380.,300.,390.,395.,410.,412.,420.]

        #check x limits
        if self.endofx < 960:
            self.endofx = 960
            self.redraw()

        self.timex,self.temp1,self.temp2 = [],[],[]
        for i in range(len(self.timeindex)):
            self.timex.append(self.designertimeinit[i])
            self.temp1.append(self.designertemp1init[i])
            self.temp2.append(self.designertemp2init[i])
            self.timeindex[i] = i

        self.redrawdesigner()

    #loads main points from a profile so that they can be edited
    def initfromprofile(self):
        if self.timeindex[0] == -1 or self.timeindex[6] == 0:
            QMessageBox.information(self,QApplication.translate("MessageBox Caption","Designer Init",None, QApplication.UnicodeUTF8),
                                    QApplication.translate("MessageBox","Unable to start designer.\nProfile missing [CHARGE] or [DROP]",None, QApplication.UnicodeUTF8))
            self.disconnect_designer()
            return()

        #save events. They will be deleted on qmc.reset()
        self.specialeventsStringscopy = self.specialeventsStrings[:]
        self.specialeventsvaluecopy = self.specialeventsvalue[:]
        self.specialeventstypecopy = self.specialeventstype[:]
        self.eventtimecopy = []
        for i in range(len(self.specialevents)):
            #save relative time of events
            self.eventtimecopy.append(self.timex[self.specialevents[i]]-self.timex[self.timeindex[0]])

        #find lowest point from profile to be converted
        lpindex = aw.findTP()
        if lpindex != -1 and not lpindex in self.timeindex:
            lptime  = self.timex[lpindex]
            lptemp2 = self.temp2[lpindex]
        else:
            lpindex = -1
        
        timeindexhold = [self.timex[self.timeindex[0]],0,0,0,0,0,0]
        timez,t1,t2 = [self.timex[self.timeindex[0]]],[self.temp1[self.timeindex[0]]],[self.temp2[self.timeindex[0]]]    #first CHARGE point
        for i in range(1,len(self.timeindex)):
            if self.timeindex[i]:                           # fill up empty lists with main points (FCs, etc). match from timeindex
                timez.append(self.timex[self.timeindex[i]])  #add time
                t1.append(self.temp1[self.timeindex[i]])    #add temp1
                t2.append(self.temp2[self.timeindex[i]])    #add temp2
                timeindexhold[i] =  self.timex[self.timeindex[i]]


        #it is possible the user may use the flag to revert to 60 seconds endofx when doing a reset
        endofxold  = self.endofx               
        self.reset()                                            #erase profile and screen
        #restore endofx limit
        self.endofx = endofxold
        self.xaxistosm()
                
        self.timex,self.temp1,self.temp2 = timez[:],t1[:],t2[:]  #copy lists back after reset() with the main points

        self.timeindexupdate(timeindexhold) #create new timeindex[]

        #add lowest point as extra point
        if lpindex != -1:
            self.currentx = lptime
            self.currenty = lptemp2
            self.addpoint()
        
        self.redrawdesigner()                                   #redraw the designer screen
        
    #redraws designer
    def redrawdesigner(self):    
        #reset (clear) plot
        if self.background:
            self.ax.lines = self.ax.lines[0:4]
        else:
            self.ax.lines = []
            
        #create statistics bar
        #calculate the positions for the statistics elements
        ydist = self.ylimit - self.ylimit_min
        statisticsheight = self.ylimit - (0.13 * ydist)
        
        #add statistics bar
        self.ax.plot([self.timex[self.timeindex[0]],self.timex[self.timeindex[1]]],[statisticsheight,statisticsheight],color = self.palette["rect1"],alpha=.5,linewidth=5) 
        self.ax.plot([self.timex[self.timeindex[1]],self.timex[self.timeindex[2]]],[statisticsheight,statisticsheight],color = self.palette["rect2"],alpha=.5,linewidth=5) 
        self.ax.plot([self.timex[self.timeindex[2]],self.timex[self.timeindex[6]]],[statisticsheight,statisticsheight],color = self.palette["rect3"],alpha=.5,linewidth=5) 

        #add phase division lines
        ylist = [self.ylimit,0]
        self.ax.plot([self.timex[self.timeindex[0]],self.timex[self.timeindex[0]]],ylist,color = self.palette["grid"],alpha=.3,linewidth=3,linestyle="--") 
        self.ax.plot([self.timex[self.timeindex[1]],self.timex[self.timeindex[1]]],ylist,color = self.palette["grid"],alpha=.3,linewidth=3,linestyle="--")
        self.ax.plot([self.timex[self.timeindex[2]],self.timex[self.timeindex[2]]],ylist,color = self.palette["grid"],alpha=.3,linewidth=3,linestyle="--") 
        self.ax.plot([self.timex[self.timeindex[6]],self.timex[self.timeindex[6]]],ylist,color = self.palette["grid"],alpha=.3,linewidth=3,linestyle="--") 

        if self.timex[-1] < self.endofx:
            self.endofx = self.timex[-1] + 120
            self.xaxistosm()

        if self.BTsplinedegree >= len(self.timex):  #max 5 or less. Cannot biger than points
            self.BTsplinedegree = len(self.timex)-1

        if self.ETsplinedegree >= len(self.timex):  #max 5 or less. Cannot biger than points
            self.ETsplinedegree = len(self.timex)-1

        func = inter.UnivariateSpline(self.timex,self.temp2, k = self.BTsplinedegree )
        func2 = inter.UnivariateSpline(self.timex,self.temp1, k = self.ETsplinedegree )
        timez = numpy.arange(self.timex[0],self.timex[-1],1).tolist()
        #convert all time values to temperature
        btvals = func(timez).tolist()
        etvals = func2(timez).tolist()

        #add curves
        self.ax.plot(timez, btvals, color=self.palette["bt"], linestyle = '-', linewidth=2)
        self.ax.plot(timez, etvals, color=self.palette["et"], linestyle = '-', linewidth=2)

        #add markers (big circles) '0'
        self.ax.plot(self.timex,self.temp2,color = self.palette["bt"],marker = "o",picker=10,linestyle='',markersize=8)     #picker = 10 means 10 points tolerance
        self.ax.plot(self.timex,self.temp1,color = self.palette["et"],marker = "o",picker=10,linestyle='',markersize=8)

        #plot
        self.fig.canvas.draw()
       
    #CONTEXT MENU  = Right click
    def on_press(self,event):
        if event.inaxes != self.ax: return
        if event.button != 3: return   #select right click only
        
        self.releaseMouse()
        self.mousepress = False
        self.setCursor(Qt.OpenHandCursor)
        
        self.currentx = event.xdata 
        self.currenty = event.ydata
        
        designermenu = QMenu(self)
        
        configAction = QAction(QApplication.translate("Contextual Menu", "Designer Config...",None, QApplication.UnicodeUTF8),self)
        self.connect(configAction,SIGNAL("triggered()"),self.desconfig)
        designermenu.addAction(configAction)

        backgroundAction = QAction(UIconst.ROAST_MENU_BACKGROUND,self)
        self.connect(backgroundAction,SIGNAL("triggered()"),aw.background)
        designermenu.addAction(backgroundAction)  

        designermenu.addSeparator()  

        addpointAction = QAction(QApplication.translate("Contextual Menu", "Add point",None, QApplication.UnicodeUTF8),self)
        self.connect(addpointAction,SIGNAL("triggered()"),self.addpoint)
        designermenu.addAction(addpointAction)
        
        removepointAction = QAction(QApplication.translate("Contextual Menu", "Remove point",None, QApplication.UnicodeUTF8),self)
        self.connect(removepointAction,SIGNAL("triggered()"),self.removepoint)
        designermenu.addAction(removepointAction)        

        designermenu.addSeparator()  

        resetAction = QAction(QApplication.translate("Contextual Menu", "Reset Designer",None, QApplication.UnicodeUTF8),self)
        self.connect(resetAction,SIGNAL("triggered()"),self.reset_designer)
        designermenu.addAction(resetAction)

        exitAction = QAction(QApplication.translate("Contextual Menu", "Exit Designer",None, QApplication.UnicodeUTF8),self)
        self.connect(exitAction,SIGNAL("triggered()"),aw.stopdesigner)
        designermenu.addAction(exitAction)

        designermenu.exec_(QCursor.pos())        

    def on_pick(self,event):
        self.setCursor(Qt.ClosedHandCursor)
        
        self.indexpoint = event.ind
        self.mousepress = True
        
        line = event.artist
        #identify which line is being edited
        ydata = line.get_ydata()
        if ydata[1] == self.temp1[1]:  
            self.workingline = 1
        else:
            self.workingline = 2


    #handles when releasing mouse   
    def on_release(self,event):
        self.mousepress = False
        self.setCursor(Qt.OpenHandCursor)

    #handler for moving point
    def on_motion(self,event):
        if not event.inaxes: return
        try:                
            if self.mousepress:                                 #if mouse clicked
                self.timex[self.indexpoint] = event.xdata
                if self.workingline == 1:
                    self.temp1[self.indexpoint] = event.ydata
                else:
                    self.temp2[self.indexpoint] = event.ydata

                #check point going over point
                #check to the left    
                if self.indexpoint > 0:
                    if abs(self.timex[self.indexpoint] - self.timex[self.indexpoint - 1]) < 10.:
                        self.unrarefy_designer()
                        return
                #check to the right
                if self.indexpoint <= len(self.timex)-2:
                    if abs(self.timex[self.indexpoint] - self.timex[self.indexpoint + 1]) < 10.:
                        self.unrarefy_designer()
                        return                    

                #check for possible CHARGE time moving
                if self.indexpoint == self.timeindex[0]:
                    self.xaxistosm()

                #redraw
                self.redrawdesigner()
                return
            
            if type(event.xdata):                       #outside graph type is None
                for i in range(len(self.timex)):
                    if abs(event.xdata - self.timex[i]) < 7.:
                        if i in self.timeindex:
                            if abs(self.temp2[i] - event.ydata) < 10:
                                self.ax.plot(self.timex[i],self.temp2[i],color = "orange",marker = "o",alpha = .3,markersize=30)
                                self.fig.canvas.draw()
                                QTimer.singleShot(600, self.redrawdesigner)
                            elif abs(self.temp1[i] - event.ydata) < 10:
                                self.ax.plot(self.timex[i],self.temp1[i],color = "orange",marker = "o",alpha = .3,markersize=30)                                                                               
                                self.fig.canvas.draw()
                                QTimer.singleShot(600, self.redrawdesigner)
                            index = self.timeindex.index(i)
                            if index == 0:
                                timez = self.stringfromseconds(0)
                                aw.messagelabel.setText("<font style=\"BACKGROUND-COLOR: #f07800\">" + QApplication.translate("Message Area", "[ CHARGE ]",None, QApplication.UnicodeUTF8) + "</font> " + timez)
                            elif index == 1:
                                timez = self.stringfromseconds(self.timex[self.timeindex[1]] - self.timex[self.timeindex[0]])
                                aw.messagelabel.setText("<font style=\"BACKGROUND-COLOR: orange\">" + QApplication.translate("Message Area", "[ DRY END ]",None, QApplication.UnicodeUTF8) + "</font> " + timez)
                            elif index == 2:
                                timez = self.stringfromseconds(self.timex[self.timeindex[2]] - self.timex[self.timeindex[0]])
                                aw.messagelabel.setText("<font style=\"BACKGROUND-COLOR: orange\">" + QApplication.translate("Message Area", "[ FC START ]",None, QApplication.UnicodeUTF8) + "</font> " + timez)
                            elif index == 3:
                                timez = self.stringfromseconds(self.timex[self.timeindex[3]] - self.timex[self.timeindex[0]])                                
                                aw.messagelabel.setText("<font style=\"BACKGROUND-COLOR: orange\">" + QApplication.translate("Message Area", "[ FC END ]",None, QApplication.UnicodeUTF8) + "</font> " + timez)
                            elif index == 4:
                                timez = self.stringfromseconds(self.timex[self.timeindex[4]] - self.timex[self.timeindex[0]])
                                aw.messagelabel.setText("<font style=\"BACKGROUND-COLOR: orange\">" + QApplication.translate("Message Area", "[ SC START ]",None, QApplication.UnicodeUTF8) + "</font> " + timez)
                            elif index == 5:
                                timez = self.stringfromseconds(self.timex[self.timeindex[5]] - self.timex[self.timeindex[0]])
                                aw.messagelabel.setText("<font style=\"BACKGROUND-COLOR: orange\">" + QApplication.translate("Message Area", "[ SC END ]",None, QApplication.UnicodeUTF8) + "</font> " + timez)
                            elif index == 6:
                                timez = self.stringfromseconds(self.timex[self.timeindex[6]] - self.timex[self.timeindex[0]])
                                aw.messagelabel.setText("<font style=\"BACKGROUND-COLOR: #f07800\">" + QApplication.translate("Message Area", "[ DROP ]",None, QApplication.UnicodeUTF8) + "</font> " + timez)
                            break
                        else:
                            if abs(self.temp2[i] - event.ydata) < 10:
                                self.ax.plot(self.timex[i],self.temp2[i],color = "blue",marker = "o",alpha = .3,markersize=30)
                                self.fig.canvas.draw()
                                QTimer.singleShot(600, self.redrawdesigner)
                            elif abs(self.temp1[i] - event.ydata) < 10:
                                self.ax.plot(self.timex[i],self.temp1[i],color = "blue",marker = "o",alpha = .3,markersize=30)                                                                               
                                self.fig.canvas.draw()
                                QTimer.singleShot(600, self.redrawdesigner)
                            timez = self.stringfromseconds(self.timex[i] - self.timex[self.timeindex[0]])
                            aw.messagelabel.setText("<font style=\"BACKGROUND-COLOR: lightblue\">%s</font> "%timez)
                            break
                    else:
                        totaltime = self.timex[self.timeindex[6]] - self.timex[self.timeindex[0]]
                        dryphasetime = self.timex[self.timeindex[1]] - self.timex[self.timeindex[0]]
                        midphasetime = self.timex[self.timeindex[2]] - self.timex[self.timeindex[1]]
                        finishphasetime = self.timex[self.timeindex[6]] - self.timex[self.timeindex[2]]

                        if totaltime:
                            dryphaseP = int(dryphasetime*100./totaltime)
                            midphaseP = int(midphasetime*100./totaltime)
                            finishphaseP = int(finishphasetime*100./totaltime)
                        else:
                            return
                        
                        dryramp = self.temp2[self.timeindex[1]] - self.temp2[self.timeindex[0]]
                        midramp = self.temp2[self.timeindex[2]] - self.temp2[self.timeindex[1]]
                        finishramp = self.temp2[self.timeindex[6]] - self.temp2[self.timeindex[2]]

                        if dryphasetime:
                            dryroc = u" %.1f d/m"%((dryramp/dryphasetime)*60.)
                        else:
                            dryroc = u" 0 d/m"

                        if midphasetime:
                            midroc = u" %.1f d/m"%((midramp/midphasetime)*60.)
                        else:
                            midroc = u" 0 d/m"

                        if finishphasetime:
                            finishroc = u" %.1f d/m"%((finishramp/finishphasetime)*60.)
                        else:
                            finishroc = 0
                            
                        margin = "&nbsp;&nbsp;&nbsp;"
                        string1 = " <font color = \"white\" style=\"BACKGROUND-COLOR: %s\">%s %s %s %i%% %s %s %s</font>"%(self.palette["rect1"],
                                  margin,self.stringfromseconds(dryphasetime),margin, dryphaseP, margin,dryroc,margin)
                        string2 = " <font color = \"white\" style=\"BACKGROUND-COLOR: %s\">%s %s %s %i%% %s %s %s</font>"%(self.palette["rect2"],
                                  margin,self.stringfromseconds(midphasetime),margin,midphaseP,margin,midroc,margin)
                        string3 = " <font color = \"white\" style=\"BACKGROUND-COLOR: %s\">%s %s %s %i%% %s %s %s</font>"%(self.palette["rect3"],
                                  margin,self.stringfromseconds(finishphasetime),margin,finishphaseP,margin,finishroc,margin)
                        aw.messagelabel.setText(string1+string2+string3)

        except Exception,e:
            self.unrarefy_designer()
            self.adderror(QApplication.translate("Error Message", "Exception: designer on_motion() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return                            

    #this is used in on_motion() to try to prevent points crossing over points 
    def unrarefy_designer(self):
        for i in range(len(self.timex)-1):
            if abs(self.timex[i]-self.timex[i+1]) < 20:
                self.timex[i+1] = self.timex[i] + 20
            self.disconnect_designer()
            self.connect_designer()

    def addpoint(self):
        try:
            #current x, and y is obtained when doing right click in mouse: on_press()
            
            if self.currentx > self.timex[-1]:       #if point is beyond max timex (all the way to the right)
                #find closest line
                d1 = abs(self.temp1[-1] - self.currenty)
                d2 = abs(self.temp2[-1] - self.currenty)
                if d2 < d1:
                    self.temp2.append(self.currenty)
                    self.temp1.append(self.temp1[-1])
                else:
                    self.temp2.append(self.temp2[-1])
                    self.temp1.append(self.currenty)
                    
                self.timex.append(self.currentx)
                #no need to update time index
                
                self.redrawdesigner()
                return 0                  

            elif self.currentx < self.timex[0]:         #if point is bellow min timex (all the way to the left)
                #find closest line
                d1 = abs(self.temp1[0] - self.currenty)
                d2 = abs(self.temp2[0] - self.currenty)
                if d2 < d1:
                    self.temp2.insert(0,self.currenty)
                    self.temp1.insert(0,self.temp1[0])
                else:
                    self.temp2.insert(0,self.temp2[0])
                    self.temp1.insert(0,self.currenty)
                    
                self.timex.insert(0,self.currentx)
                
                #update timeindex
                if self.timeindex[0] != -1:   #we update timeindex[0] different
                    self.timeindex[0] += 1
                for u in range(1,len(self.timeindex)):
                    if self.timeindex[u]:
                        self.timeindex[u] += 1
                        
                self.redrawdesigner()
                return len(self.timex)-1   #return index received from Designer Dialog Config to asign index to timeindex)
                    
            else:                                           #mid range
                #find index
                for i in range(len(self.timex)):
                    if self.timex[i] > self.currentx:  
                        break
                #find closest line
                d1 = abs(self.temp1[i] - self.currenty)
                d2 = abs(self.temp2[i] - self.currenty)
                if d2 < d1:
                    self.temp2.insert(i,self.currenty)
                    self.temp1.insert(i,self.temp1[i])
                else:
                    self.temp2.insert(i,self.temp2[i])
                    self.temp1.insert(i,self.currenty)

                self.timex.insert(i,self.currentx)

                #update timeindex
                for x in range(len(self.timeindex)):
                    if self.timeindex[x] >= i:
                        self.timeindex[x] += 1

                self.redrawdesigner()
                return i
            
        except Exception,e:
            self.adderror(QApplication.translate("Error Message", "Exception: designer addpoint() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return 

    #removes point
    def removepoint(self):        
        try:
            #current x, and y is obtained when doing right click in mouse: on_press()
            #find index
            for i in range(len(self.timex)):
                if self.timex[i] > self.currentx:
                    break
            #find closest point
            if abs(self.timex[i]- self.currentx) < abs(self.timex[i-1] - self.currentx):
                index = i
            else:
                index = i-1

            #check if if it is a landmark point
            if index in self.timeindex:
                whichone = self.timeindex.index(index)
                if whichone == 0 or whichone == 6:  #if charge or drop
                    return
                self.timeindex[whichone] = 0
                
            self.timex.pop(index)        
            self.temp1.pop(index)
            self.temp2.pop(index)

            for x in range(len(self.timeindex)):                            
                if self.timeindex[x] > index: #decrease time index by one when above the index taken out
                    self.timeindex[x] -= 1
                        
            self.redrawdesigner()
                    
        except Exception,e:
            self.adderror(QApplication.translate("Error Message", "Exception: designer removepoint() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return                 

    #finds a proper index location for a time that does not exists yet.
    def designerfindindex(self,time):
        if time < aw.qmc.timex[0]:
            return 0
        elif time > aw.qmc.timex[-1]:
            return len(aw.qmc.timex)-1
        else:
            for i in range(len(aw.qmc.timex)):
                if time == aw.qmc.timex[i]:
                    return i
                if aw.qmc.timex[i] > time:
                    return i-1

                               
    #converts from a designer profile to a normal profile	        
    def convert_designer(self):
        try:
            #create functions        
            funcBT = inter.UnivariateSpline(self.timex,self.temp2, k = self.BTsplinedegree )
            funcET = inter.UnivariateSpline(self.timex,self.temp1, k = self.ETsplinedegree )

            #create longer list of time values
            timez = numpy.arange(self.timex[0],self.timex[-1],1).tolist()

            #convert all time values to temperature
            btvals = funcBT(timez).tolist()
            etvals = funcET(timez).tolist()

            #find new indexes for events
            for i in range(len(self.specialevents)):
                for p in range(len(timez)):
                    if timez[p] > self.timex[self.specialevents[i]]:
                        self.specialevents[i] = p
                        break

            #save landmarks        
            maintimes = []
            for i in range(len(self.timeindex)):
                maintimes.append(self.timex[self.timeindex[i]])

            self.timex = timez[:]
            self.temp1 = etvals[:]
            self.temp2 = btvals[:]
                            
            self.timeindexupdate(maintimes)
        
            #check and restore carried over events
            if len(self.eventtimecopy):
                for i in range(len(self.eventtimecopy)):
                    self.specialevents.append(self.time2index(self.eventtimecopy[i] + self.timex[self.timeindex[0]]))
                self.specialeventsStrings = self.specialeventsStringscopy[:]
                self.specialeventsvalue = self.specialeventsvaluecopy[:]
                self.specialeventstype = self.specialeventstypecopy[:]
                
            self.disconnect_designer()           

            #create playback events
            if self.reproducedesigner:
                functioncall = [0,
                                self.designer_create_BT_rateofchange,
                                self.designer_create_ET_rateofchange,
                                self.designer_create_sv_command,
                                self.designer_create_ramp_command]
                
                functioncall[self.reproducedesigner]()
                
            self.redraw()        
            aw.sendmessage(QApplication.translate("Message Area", "New profile created",None, QApplication.UnicodeUTF8))
            
        except ValueError:
            self.adderror(QApplication.translate("Error Message", "Value Error: createFromDesigner() ",None, QApplication.UnicodeUTF8))
            return

        except Exception,e:
            self.adderror(QApplication.translate("Error Message", "Exception: createFromDesigner() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

    #activates mouse events	
    def connect_designer(self):
        if not self.designerflag:
            self.designerflag = True
            aw.designerAction.setChecked(True)
            self.setCursor(Qt.OpenHandCursor)
            self.mousepress = None
            #create mouse events. Note: keeping the ids inside a list helps protect against extrange python behaviour.
            self.designerconnections = [0,0,0,0]
            self.designerconnections[0] = self.fig.canvas.mpl_connect('pick_event', self.on_pick)
            self.designerconnections[1] = self.fig.canvas.mpl_connect('button_release_event', self.on_release)
            self.designerconnections[2] = self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
            self.designerconnections[3] = self.fig.canvas.mpl_connect('button_press_event', self.on_press)
            #this is needed to prevent complaints from inter.UnivariateSpline() -used in redraw()- in extreme cases of difficulty
            warnings.simplefilter('ignore', UserWarning)

    #deactivates mouse events    
    def disconnect_designer(self):
        for i in range(len(self.designerconnections)):
            if self.designerconnections[i]:
                self.fig.canvas.mpl_disconnect(self.designerconnections[i])
        self.setCursor(Qt.ArrowCursor)
        self.designerflag = False
        aw.designerAction.setChecked(False)
        warnings.simplefilter('default', UserWarning)
              
    #launches designer config Window    
    def desconfig(self):
        dialog = designerconfigDlg(self)
        dialog.show()

    def reset_designer(self):
        self.reset()
        self.disconnect_designer()
        self.connect_designer()
        self.designerinit()

    #saves next BT rate of change till next landmark as an event (example idea for arduino TC4)
    def designer_create_BT_rateofchange(self):
        self.deleteEvents()
        lastindexused = 0
        for i in range(1,len(self.timeindex)):
            if self.timeindex[i]:
                difftemp = self.temp2[self.timeindex[i]] - self.temp2[self.timeindex[lastindexused]]
                difftime = (self.timex[self.timeindex[i]] - self.timex[self.timeindex[lastindexused]])/60.
                if difftime:
                    string = QApplication.translate("Event String", "BT %1 d/m for %2",None, QApplication.UnicodeUTF8).arg("%.1f"%(difftemp/difftime)).arg(self.stringfromseconds(self.timex[self.timeindex[i]]-self.timex[self.timeindex[lastindexused]]))
                    self.specialevents.append(self.timeindex[lastindexused])                                     
                    self.specialeventstype.append(0)                                           
                    self.specialeventsStrings.append(string)                          
                    self.specialeventsvalue.append(0)
                    lastindexused = i
                    
    #saves next BT rate of change till next landmark as an event (example idea for arduino TC4)
    def designer_create_ET_rateofchange(self):
        self.deleteEvents()
        lastindexused = 0
        for i in range(1,len(self.timeindex)):
            if self.timeindex[i]:
                difftemp = self.temp1[self.timeindex[i]] - self.temp1[self.timeindex[lastindexused]]
                difftime = (self.timex[self.timeindex[i]] - self.timex[self.timeindex[lastindexused]])/60.
                if difftime:
                    string = QApplication.translate("Event String", "ET %1 d/m for %2",None, QApplication.UnicodeUTF8).arg("%.1f"%(difftemp/difftime)).arg(self.stringfromseconds(self.timex[self.timeindex[i]]-self.timex[self.timeindex[lastindexused]]))
                    self.specialevents.append(self.timeindex[lastindexused])                                     
                    self.specialeventstype.append(0)                                           
                    self.specialeventsStrings.append(string)                          
                    self.specialeventsvalue.append(0)
                    lastindexused = i
                    
    def deleteEvents(self):
        self.specialevents = []                                    
        self.specialeventstype = []                                           
        self.specialeventsStrings = []                          
        self.specialeventsvalue = []        

    #this is used to create a string in pid language to reproduce the profile from Designer
    #NOTE: pid runs ET (temp1)    
    def designer_create_ramp_command(self):
        tempinits = []
        minutes_segments = []
        
        #ramp times in minutes
        minsDryPhase = unicode(int(abs(self.timex[self.timeindex[0]] - self.timex[self.timeindex[1]])/60))
        minsMidPhase = unicode(int(abs(self.timex[self.timeindex[1]] - self.timex[self.timeindex[2]])/60)) 
        minsFinishPhase = unicode(int(abs(self.timex[self.timeindex[2]] - self.timex[self.timeindex[6]])/60))

        #target temps for ET
        tempinits.append(u"%.1f"%self.temp1[self.timeindex[1]])
        tempinits.append(u"%.1f"%self.temp1[self.timeindex[2]])
        tempinits.append(u"%.1f"%self.temp1[self.timeindex[6]])

        minutes_segments.append(minsDryPhase)
        minutes_segments.append(minsMidPhase)
        minutes_segments.append(minsFinishPhase)

        command = u""
        for i in range(3):
            command += u"SETRS::" + tempinits[i] + u"::" + minutes_segments[i] + u"::0::"
        command += u"SETRS::" + tempinits[-1] + u"::0::0"

        self.clean_old_pid_commands()

        #do only one event but with all segments            
        self.specialevents.append(0)                                     
        self.specialeventstype.append(0)                                           
        self.specialeventsStrings.append(command)                          
        self.specialeventsvalue.append(0)                                   

    #this is used to create a string in ET temp language to reproduce the profile from Designer    
    def designer_create_sv_command(self):
        self.clean_old_pid_commands()
        for i in range(len(self.timeindex)-1):
            command = u"SETSV::%.1f"%self.temp1[self.timeindex[i+1]]           
            if i > 0 and self.timeindex[i]:
                self.specialevents.append(self.timeindex[i])                    
                self.specialeventstype.append(0)                                           
                self.specialeventsStrings.append(command)                          
                self.specialeventsvalue.append(0)

    #verifies there are no previos machine commands on events
    def clean_old_pid_commands(self):
        #check for possible preloaded machine commands
        target = 0
        if len(self.specialevents):
            for i in range(len(self.specialevents)):
                if "::" in self.specialeventsStrings[i]:
                    self.specialevents.pop(i)
                    self.specialeventstype.pop(i)
                    self.specialeventsStrings.pop(i)
                    self.specialeventsvalue.pop(i)
                    target = 1
                    break     #break or the index i can become larger than the new shorted length of specialevents
        if target:
           self.clean_old_pid_commands() 


                
#######################################################################################
#####   temporary hack for windows till better solution found about toolbar icon problem with py2exe and svg
#######################################################################################
           
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
###     Sample thread
########################################################################################
    
class SampleThread(QThread):
    def _init_(self,parent = None):
        super(SampleThread,self)._init_(parent)

    # sample devices at interval self.delay miliseconds.  
    def sample(self):
        try:
            
            #apply sampling interval here                
            libtime.sleep(aw.qmc.delay/1000.)

            #avoid sampling while redrawing. synchronization.
            count = 0
            while aw.qmc.samplingflag:
                libtime.sleep(.05)
                count += 1
                if count == 100:
                    return
                
            aw.qmc.samplingflag = True
            
            #if using a meter (thermocouple device)
            if aw.qmc.device != 18:
                #read time, ET (t1) and BT (t2) TEMPERATURE
                tx,t1,t2 = aw.ser.devicefunctionlist[aw.qmc.device]()  #use a list of functions (a different one for each device) with index aw.qmc.device
                if len(aw.qmc.ETfunction):
                    t1 = aw.qmc.eval_math_expression(aw.qmc.ETfunction,t1)
                if len(aw.qmc.BTfunction):
                    t2 = aw.qmc.eval_math_expression(aw.qmc.BTfunction,t2)

                #filter droputs 
                if aw.qmc.mode == "C":
                    limit = 500.
                else:
                    limit = 800.
                if  t1 < 1. or t1 > limit:
                    if len(aw.qmc.timex) > 2:
                        t1 = aw.qmc.temp1[-1]
                    else:
                        t1 = -1.
                if t2 < 1. or t2 > limit:
                    if len(aw.qmc.timex) > 2:
                        t2 = aw.qmc.temp2[-1]
                    else:
                        t2 = -1.       
                                                        
                #HACK to deal with the issue that sometimes BT and ET values are magically exchanged
                #check if the readings of t1 and t2 got swapped by some unknown magic, by comparing them to the previous ones
                if len(aw.qmc.timex) > 2 and t1 == aw.qmc.temp2[-1] and t2 == aw.qmc.temp1[-1]:
                    #let's better swap the readings (also they are just repeating the previous ones)
                    aw.qmc.temp2.append(t1)
                    aw.qmc.temp1.append(t2)
                else:
                    #the readings seem to be "in order"
                    aw.qmc.temp2.append(t2)
                    aw.qmc.temp1.append(t1)

                aw.qmc.timex.append(tx)

                # update lines data using the lists with new data
                aw.qmc.l_temp1.set_data(aw.qmc.timex, aw.qmc.temp1)
                aw.qmc.l_temp2.set_data(aw.qmc.timex, aw.qmc.temp2)
                
                #we need a minimum of two readings to calculate rate of change
                if len(aw.qmc.timex) > 2:
                    timed = aw.qmc.timex[-1] - aw.qmc.timex[-2]   #time difference between last two readings
                    #calculate Delta T = (changeTemp/ChangeTime)*60. =  degress per minute;
                    aw.qmc.rateofchange1 = ((aw.qmc.temp1[-1] - aw.qmc.temp1[-2])/timed)*60.  #delta ET (degress/minute)
                    aw.qmc.rateofchange2 = ((aw.qmc.temp2[-1] - aw.qmc.temp2[-2])/timed)*60.  #delta  BT (degress/minute)
                    
                    aw.qmc.unfiltereddelta1.append(aw.qmc.rateofchange1)
                    aw.qmc.unfiltereddelta2.append(aw.qmc.rateofchange2)
                        
                    #######   filter deltaBT deltaET
                    if aw.qmc.deltafilter:
                        if len(aw.qmc.timex) > aw.qmc.deltafilter:   #detafilter is an int = number of pads
                            a1,a2 = 0.,0.
                            for k in range(aw.qmc.deltafilter):
                                a1 += aw.qmc.unfiltereddelta1[-(k+1)]
                                a2 += aw.qmc.unfiltereddelta2[-(k+1)]
                            aw.qmc.rateofchange1 = a1/float(aw.qmc.deltafilter)
                            aw.qmc.rateofchange2 = a2/float(aw.qmc.deltafilter)
                            
                    rateofchange1plot = float(aw.qmc.sensitivity)*aw.qmc.rateofchange1   
                    rateofchange2plot = float(aw.qmc.sensitivity)*aw.qmc.rateofchange2

                else:
                    aw.qmc.unfiltereddelta1.append(0.)
                    aw.qmc.unfiltereddelta2.append(0.)                    
                    aw.qmc.rateofchange1,aw.qmc.rateofchange2,rateofchange1plot,rateofchange2plot = 0.,0.,0.,0.

                # append new data to the rateofchange

                aw.qmc.delta1.append(rateofchange1plot)
                aw.qmc.delta2.append(rateofchange2plot)
                                           
                if aw.qmc.DeltaETflag:
                    aw.qmc.l_delta1.set_data(aw.qmc.timex, aw.qmc.delta1)
                if aw.qmc.DeltaBTflag:
                    aw.qmc.l_delta2.set_data(aw.qmc.timex, aw.qmc.delta2)

                #readjust xlimit of plot if needed
                if  aw.qmc.timex[-1] > (aw.qmc.endofx - 45):            # if difference is smaller than 30 seconds
                    aw.qmc.endofx = int(aw.qmc.timex[-1] + 180)         # increase x limit by 3 minutes
                    aw.qmc.ax.set_xlim(aw.qmc.startofx,aw.qmc.endofx)
                    aw.qmc.xaxistosm()
                
                if aw.qmc.projectFlag:
                    aw.qmc.viewProjection()                   
                if aw.qmc.background and aw.qmc.backgroundReproduce:
                    aw.qmc.playbackevent()

                ##############  if using more than one device
                ndevices = len(aw.qmc.extradevices)
                if ndevices:
                    if len(aw.extraser) == len(aw.qmc.extradevices) == len(aw.qmc.extratemp1) == len(aw.qmc.extratemp1lines):
                        for i in range(ndevices):
                            extratx,extrat2,extrat1 = aw.extraser[i].devicefunctionlist[aw.qmc.extradevices[i]]()
                            if len(aw.qmc.extramathexpression1[i]):
                                extrat1 = aw.qmc.eval_math_expression(aw.qmc.extramathexpression1[i],extrat1)
                            if len(aw.qmc.extramathexpression2[i]):
                                extrat2 = aw.qmc.eval_math_expression(aw.qmc.extramathexpression2[i],extrat2)
                            aw.qmc.extratemp1[i].append(extrat1)
                            aw.qmc.extratemp2[i].append(extrat2)                        
                            aw.qmc.extratimex[i].append(extratx)
                            # update extra lines 
                            aw.qmc.extratemp1lines[i].set_data(aw.qmc.extratimex[i], aw.qmc.extratemp1[i])
                            aw.qmc.extratemp2lines[i].set_data(aw.qmc.extratimex[i], aw.qmc.extratemp2[i])

         
            #############    if using DEVICE 18 (no device). Manual mode
            # temperatures are entered when pressing push buttons like for example at aw.qmc.markDryEnd()        
            else:
                tx = int(aw.qmc.timeclock.elapsed()/1000.) 
                #readjust xlimit of plot if needed
                if  tx > (aw.qmc.endofx - 45):            # if difference is smaller than 45 seconds  
                    aw.qmc.endofx = tx + 180              # increase x limit by 3 minutes (180)
                    aw.qmc.ax.set_xlim(aw.qmc.startofx,aw.qmc.endofx)
                    aw.qmc.xaxistosm()   
                aw.qmc.resetlines()
                #add to plot a vertical time line
                aw.qmc.ax.plot([tx,tx], [aw.qmc.ylimit_min,aw.qmc.ylimit],color = aw.qmc.palette["Cline"],linestyle = '-', linewidth= 1, alpha = .7)
                
            aw.qmc.samplingflag = False

            #update screen in main GUI thread
            self.emit(SIGNAL("updategraphics"))
            
        except Exception,e:
            aw.qmc.flagon = False
            aw.qmc.samplingflag = False
            aw.qmc.adderror(QApplication.translate("Error Message","Exception Error: sample() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return
        
        finally:
            aw.qmc.samplingflag = False
     
              
    def run(self):
        timedelay = aw.qmc.delay/1000.
        if not aw.qmc.flagon:
            return
        while True:
            if aw.qmc.flagon:
                #collect information
                self.sample()
            else:
                if aw.ser.SP.isOpen():
                    aw.ser.closeport()            
                self.quit()
                QApplication.processEvents()
                break  #thread ends

#########################################################################################################
###     Artisan thread Server
#########################################################################################################            


class Athreadserver(QWidget):
    def _init_(self,parent = None):
        super(Athreadserver,self)._init_(parent)

    def createSampleThread(self):
        if aw.qmc.flagon == False:
            aw.qmc.flagon = True
            thread = SampleThread(self)
            QApplication.processEvents()

            #delete when finished to save memory 
            self.connect(thread,SIGNAL("finished"),thread,SLOT("deleteLater()"))
            #self.connect(thread,SIGNAL("terminated()"),thread,SLOT("deleteLater()"))            
            #connect graphics to GUI thread
            self.connect(thread, SIGNAL("updategraphics"),aw.qmc.updategraphics)
            thread.start()
            thread.wait(300)    #needed in some Win OS

    def createTCPserver(self):
        pass


##################################################################################################################
###   TCP server for remote operation
##################################################################################################################

            




########################################################################################                            
#################### MAIN APPLICATION WINDOW ###########################################
########################################################################################
            
class ApplicationWindow(QMainWindow):
    def __init__(self, parent = None):
            
        #############################  Define variables that need to exist before calling settingsload()
        self.curFile = None
        self.MaxRecentFiles = 10
        self.recentFileActs = []
        self.applicationDirectory =  QDir().current().absolutePath()
        super(ApplicationWindow, self).__init__(parent)

        #flag to reset Qsettings
        self.resetqsettings = 0

        # self.profilepath is obteined at dirstruct() and points to profiles/year/month. file-open/save will point to profilepath
        self.profilepath = u""

        # on the Mac preferences should be stored outside of applications in the users ~/Library/Preferences path
        if platf == u'Darwin':
            preference_path = QDir().homePath().append(QString("/Library/Preferences//"))
            preference_dir = QDir()
            preference_dir.setPath(preference_path)
            if not preference_dir.exists():
                QDir().mkpath(preference_path)
            QDir().setCurrent(preference_path)
        
        #checks executable directory. dirstruct() checks or creates: /profile/year/month directory to store profiles
        self.dirstruct()        
        
        #defaults the users profile path to the standard profilepath (incl. month/year subdirectories)
        self.userprofilepath = self.profilepath
        
        self.printer = QPrinter()
        self.printer.setPageSize(QPrinter.Letter)
        
        self.main_widget = QWidget(self)
        #set a minimum size (main window can be bigger but never smaller)
        self.main_widget.setMinimumWidth(811)
        #self.main_widget.setMinimumHeight(670)
       
        ####      create Matplotlib canvas widget
        #resolution
        self.dpi = 80
        self.qmc = tgraphcanvas(self.main_widget)

        ####    HUD   
        self.HUD = QLabel()  #main canvas for hud widget
        #This is a list of different HUD functions. 
        self.showHUD = [self.showHUDmetrics, self.showHUDthermal]
        #this holds the index of the HUD functions above
        self.HUDfunction = 0

        self.sound = soundcrack(QWidget)
        
        self.stack = QStackedWidget()
        self.stack.addWidget(self.qmc)
        self.stack.addWidget(self.HUD)
        self.stack.addWidget(self.sound)
        self.stack.setCurrentIndex(0)
        #events config
        self.eventsbuttonflag = 1
        self.minieventsflag = 1   #minieditor flag
       
        #create a serial port object
        self.ser = serialport()
        #list with extra serial ports
        self.extraser = []
        #extra comm port settings 
        self.extracomport,self.extrabaudrate,self.extrabytesize,self.extraparity,self.extrastopbits,self.extratimeout = [],[],[],[],[],[]
        
        # create a PID object
        self.pid = FujiPID()
        
        self.soundflag = 0

        #lcd1 = time, lcd2 = met, lcd3 = bt, lcd4 = roc et, lcd5 = roc bt, lcd6 = sv 
        self.lcdpaletteB = { "timer":u'black',"et":'black',"bt":'black',"deltaet":'black',"deltabt":'black',"sv":'black'}
        self.lcdpaletteF = { "timer":u'white',"et":'white',"bt":'white',"deltaet":'white',"deltabt":'white',"sv":'white'}

    	#user defined event buttons
        self.extraeventslabels,self.extraeventsdescriptions, self.extraeventstypes,self.extraeventsvalues = [],[],[],[]  #hold string,string,index,index
        self.extraeventsactionstrings,self.extraeventsactions,self.extraeventsvisibility = [],[],[] #hold string,index,index

        # set window title
        self.windowTitle = unicode(QApplication.translate("Application Title", "Artisan %1",None, QApplication.UnicodeUTF8).arg(str(__version__)))
        self.setWindowTitle(self.windowTitle)
        for i in range(self.MaxRecentFiles):
            self.recentFileActs.append(
                    QAction(self, visible=False,
                            triggered=self.openRecentFile))


        #######################    MENUS SECTION ##################################################
        ###############  create Top MENUS 
        
        self.fileMenu = self.menuBar().addMenu(UIconst.FILE_MENU)
        self.editMenu = self.menuBar().addMenu(UIconst.EDIT_MENU)
        self.GraphMenu = self.menuBar().addMenu(UIconst.ROAST_MENU)
        self.ConfMenu = self.menuBar().addMenu(UIconst.CONF_MENU)
        self.ToolkitMenu = self.menuBar().addMenu(UIconst.TOOLKIT_MENU)
        self.helpMenu = self.menuBar().addMenu(UIconst.HELP_MENU)

        #FILE menu
        newRoastAction = QAction(UIconst.FILE_MENU_NEW,self)
        
        newRoastAction.setShortcut(QKeySequence.New)
        self.connect(newRoastAction,SIGNAL("triggered()"),self.newRoast)
        self.fileMenu.addAction(newRoastAction)
        
        fileLoadAction = QAction(UIconst.FILE_MENU_OPEN,self)
        fileLoadAction.setShortcut(QKeySequence.Open)
        self.connect(fileLoadAction,SIGNAL("triggered()"),self.fileLoad)
        self.fileMenu.addAction(fileLoadAction)
        
        self.openRecentMenu = self.fileMenu.addMenu(UIconst.FILE_MENU_OPENRECENT)
        for i in range(self.MaxRecentFiles):
            self.openRecentMenu.addAction(self.recentFileActs[i])
        self.updateRecentFileActions()

        importMenu = self.fileMenu.addMenu(UIconst.FILE_MENU_IMPORT)

        fileImportAction = QAction(QApplication.translate("Menu", "Artisan...",None, QApplication.UnicodeUTF8),self)
        self.connect(fileImportAction,SIGNAL("triggered()"),self.fileImport)
        importMenu.addAction(fileImportAction)  
        
        importHH506RAAction = QAction(QApplication.translate("Menu", "HH506RA...",None, QApplication.UnicodeUTF8),self)
        self.connect(importHH506RAAction,SIGNAL("triggered()"),self.importHH506RA)
        importMenu.addAction(importHH506RAAction)

        importK202Action = QAction(QApplication.translate("Menu", "K202...",None, QApplication.UnicodeUTF8),self)
        self.connect(importK202Action,SIGNAL("triggered()"),self.importK202)
        importMenu.addAction(importK202Action)
        
        self.fileMenu.addMenu(importMenu)    
        
        self.fileMenu.addSeparator()  

        fileSaveAction = QAction(UIconst.FILE_MENU_SAVE,self)
        fileSaveAction.setShortcut(QKeySequence.Save)
        self.connect(fileSaveAction,SIGNAL("triggered()"),lambda b=0:self.fileSave(self.curFile))
        self.fileMenu.addAction(fileSaveAction)    
        
        fileSaveAsAction = QAction(UIconst.FILE_MENU_SAVEAS,self)
        self.connect(fileSaveAsAction,SIGNAL("triggered()"),lambda b=0:self.fileSave(None))
        self.fileMenu.addAction(fileSaveAsAction)  
        
        self.fileMenu.addSeparator()    
        
        fileExportAction = QAction(UIconst.FILE_MENU_EXPORT,self)
        self.connect(fileExportAction,SIGNAL("triggered()"),self.fileExport)
        self.fileMenu.addAction(fileExportAction)  

        
        self.fileMenu.addSeparator()    

        saveGraphMenu = self.fileMenu.addMenu(UIconst.FILE_MENU_SAVEGRAPH)

        fullsizeAction = QAction(UIconst.FILE_MENU_SAVEGRAPH_FULL_SIZE,self)
        self.connect(fullsizeAction,SIGNAL("triggered()"),lambda x=0,y=1:self.resize(x,y))
        saveGraphMenu.addAction(fullsizeAction)

        saveGraphMenuHB = saveGraphMenu.addMenu(QApplication.translate("Menu", "Home-Barista.com",None, QApplication.UnicodeUTF8))
        saveGraphMenuCG = saveGraphMenu.addMenu(QApplication.translate("Menu", "CoffeeGeek.com",None, QApplication.UnicodeUTF8))
        saveGraphMenuPC = saveGraphMenu.addMenu(QApplication.translate("Menu", "PlanetCafe.fr",None, QApplication.UnicodeUTF8))
        saveGraphMenuRC = saveGraphMenu.addMenu(QApplication.translate("Menu", "RiktigtKaffe.se",None, QApplication.UnicodeUTF8))

        HomeBaristaActionLow = QAction(UIconst.FILE_MENU_SAVEGRAPH_LOW_QUALITY,self)
        self.connect(HomeBaristaActionLow,SIGNAL("triggered()"),lambda x=700,y=0:self.resize(x,y))
        saveGraphMenuHB.addAction(HomeBaristaActionLow)

        HomeBaristaActionHigh = QAction(UIconst.FILE_MENU_SAVEGRAPH_HIGH_QUALITY,self)
        self.connect(HomeBaristaActionHigh,SIGNAL("triggered()"),lambda x=700,y=1:self.resize(x,y))
        saveGraphMenuHB.addAction(HomeBaristaActionHigh)

        CoffeeGeekActionLow = QAction(UIconst.FILE_MENU_SAVEGRAPH_LOW_QUALITY,self)
        self.connect(CoffeeGeekActionLow,SIGNAL("triggered()"),lambda x=500,y=0:self.resize(x,y))
        saveGraphMenuCG.addAction(CoffeeGeekActionLow)

        CoffeeGeekActionHigh = QAction(UIconst.FILE_MENU_SAVEGRAPH_HIGH_QUALITY,self)
        self.connect(CoffeeGeekActionHigh,SIGNAL("triggered()"),lambda x=500,y=1:self.resize(x,y))
        saveGraphMenuCG.addAction(CoffeeGeekActionHigh)

        PlanetCafeActionLow = QAction(UIconst.FILE_MENU_SAVEGRAPH_LOW_QUALITY,self)
        self.connect(PlanetCafeActionLow,SIGNAL("triggered()"),lambda x=600,y=0:self.resize(x,y))
        saveGraphMenuPC.addAction(PlanetCafeActionLow)

        PlanetCafeActionHigh = QAction(UIconst.FILE_MENU_SAVEGRAPH_HIGH_QUALITY,self)
        self.connect(PlanetCafeActionHigh,SIGNAL("triggered()"),lambda x=600,y=1:self.resize(x,y))
        saveGraphMenuPC.addAction(PlanetCafeActionHigh)

        RiktigtKaffeActionLow = QAction(UIconst.FILE_MENU_SAVEGRAPH_LOW_QUALITY,self)
        self.connect(RiktigtKaffeActionLow,SIGNAL("triggered()"),lambda x=620,y=0:self.resize(x,y))
        saveGraphMenuRC.addAction(RiktigtKaffeActionLow)

        RiktigtKaffeActionHigh = QAction(UIconst.FILE_MENU_SAVEGRAPH_HIGH_QUALITY,self)
        self.connect(RiktigtKaffeActionHigh,SIGNAL("triggered()"),lambda x=620,y=1:self.resize(x,y))
        saveGraphMenuRC.addAction(RiktigtKaffeActionHigh)

        htmlAction = QAction(UIconst.FILE_MENU_HTMLREPORT,self)
        self.connect(htmlAction,SIGNAL("triggered()"),self.htmlReport)
        htmlAction.setShortcut("Ctrl+R")
        self.fileMenu.addAction(htmlAction)
        
        self.fileMenu.addSeparator()
        
        printAction = QAction(UIconst.FILE_MENU_PRINT,self)
        printAction.setShortcut(QKeySequence.Print)
        self.connect(printAction,SIGNAL("triggered()"),self.filePrint)
        self.fileMenu.addAction(printAction)
        
        # EDIT menu
        self.cutAction = QAction(UIconst.EDIT_MENU_CUT,self)
        self.cutAction.setShortcut(QKeySequence.Cut)
        self.editMenu.addAction(self.cutAction)
        self.connect(self.cutAction,SIGNAL("triggered()"),self.on_actionCut_triggered)
        self.copyAction = QAction(UIconst.EDIT_MENU_COPY,self)
        self.copyAction.setShortcut(QKeySequence.Copy)
        self.editMenu.addAction(self.copyAction)
        self.connect(self.copyAction,SIGNAL("triggered()"),self.on_actionCopy_triggered)
        self.pasteAction = QAction(UIconst.EDIT_MENU_PASTE,self)
        self.pasteAction.setShortcut(QKeySequence.Paste)
        self.editMenu.addAction(self.pasteAction)
        self.connect(self.pasteAction,SIGNAL("triggered()"),self.on_actionPaste_triggered)        

        # ROAST menu
        editGraphAction = QAction(UIconst.ROAST_MENU_PROPERTIES,self)
        self.connect(editGraphAction ,SIGNAL("triggered()"),self.editgraph)
        self.GraphMenu.addAction(editGraphAction)

        backgroundAction = QAction(UIconst.ROAST_MENU_BACKGROUND,self)
        self.connect(backgroundAction,SIGNAL("triggered()"),self.background)
        self.GraphMenu.addAction(backgroundAction)  

        flavorAction = QAction(UIconst.ROAST_MENU_CUPPROFILE,self)
        self.connect(flavorAction ,SIGNAL("triggered()"),self.flavorchart)
        self.GraphMenu.addAction(flavorAction)
        
        self.GraphMenu.addSeparator()
        
        temperatureMenu = self.GraphMenu.addMenu(UIconst.ROAST_MENU_TEMPERATURE)
        
        self.ConvertToFahrenheitAction = QAction(UIconst.ROAST_MENU_CONVERT_TO_FAHRENHEIT,self)
        self.connect(self.ConvertToFahrenheitAction,SIGNAL("triggered()"),lambda t="F":self.qmc.convertTemperature(t))
        temperatureMenu.addAction(self.ConvertToFahrenheitAction)

        self.ConvertToCelsiusAction = QAction(UIconst.ROAST_MENU_CONVERT_TO_CELSIUS,self)
        self.connect(self.ConvertToCelsiusAction,SIGNAL("triggered()"),lambda t="C":self.qmc.convertTemperature(t))
        temperatureMenu.addAction(self.ConvertToCelsiusAction)

        self.FahrenheitAction = QAction(UIconst.ROAST_MENU_FAHRENHEIT_MODE,self)
        self.connect(self.FahrenheitAction,SIGNAL("triggered()"),self.qmc.fahrenheitModeRedraw)
        temperatureMenu.addAction(self.FahrenheitAction)

        self.CelsiusAction = QAction(UIconst.ROAST_MENU_CELSIUS_MODE,self)
        self.connect(self.CelsiusAction,SIGNAL("triggered()"),self.qmc.celsiusModeRedraw)
        temperatureMenu.addAction(self.CelsiusAction)
        
        if self.qmc.mode == u"F":
            self.FahrenheitAction.setDisabled(True)
            self.ConvertToFahrenheitAction.setDisabled(True)
        else:
            self.CelsiusAction.setDisabled(True)
            self.ConvertToCelsiusAction.setDisabled(True)

        # CONFIGURATION menu
        deviceAction = QAction(UIconst.CONF_MENU_DEVICE, self)
        self.connect(deviceAction,SIGNAL("triggered()"),self.deviceassigment)
        self.ConfMenu.addAction(deviceAction) 
        
        commportAction = QAction(UIconst.CONF_MENU_SERIALPORT,self)
        self.connect(commportAction,SIGNAL("triggered()"),self.setcommport)
        self.ConfMenu.addAction(commportAction)

        calibrateDelayAction = QAction(UIconst.CONF_MENU_SAMPLING,self)
        self.connect(calibrateDelayAction,SIGNAL("triggered()"),self.calibratedelay)
        self.ConfMenu.addAction(calibrateDelayAction)

        self.ConfMenu.addSeparator()

        eventsAction = QAction(UIconst.CONF_MENU_EVENTS,self)
        self.connect(eventsAction,SIGNAL("triggered()"),self.eventsconf)
        self.ConfMenu.addAction(eventsAction)        

        alarmAction = QAction(UIconst.CONF_MENU_ALARMS,self)
        self.connect(alarmAction,SIGNAL("triggered()"),self.alarmconfig)
        self.ConfMenu.addAction(alarmAction) 

        self.ConfMenu.addSeparator()
        
        phasesGraphAction = QAction(UIconst.CONF_MENU_PHASES,self)
        self.connect(phasesGraphAction,SIGNAL("triggered()"),self.editphases)
        self.ConfMenu.addAction(phasesGraphAction)
       
        StatisticsAction = QAction(UIconst.CONF_MENU_STATISTICS,self)
        self.connect(StatisticsAction,SIGNAL("triggered()"),self.showstatistics)
        self.ConfMenu.addAction(StatisticsAction)     

        WindowconfigAction = QAction(UIconst.CONF_MENU_AXES,self)
        self.connect(WindowconfigAction,SIGNAL("triggered()"),self.Windowconfig)
        self.ConfMenu.addAction(WindowconfigAction) 

        self.ConfMenu.addSeparator()

        colorsAction = QAction(UIconst.CONF_MENU_COLORS,self)
        self.connect(colorsAction,SIGNAL("triggered()"),lambda x=3:self.qmc.changeGColor(x))
        self.ConfMenu.addAction(colorsAction)

        autosaveAction = QAction(UIconst.CONF_MENU_AUTOSAVE,self)
        self.connect(autosaveAction,SIGNAL("triggered()"),self.autosaveconf)
        self.ConfMenu.addAction(autosaveAction) 

        self.ConfMenu.addSeparator()

        languageMenu = self.ConfMenu.addMenu(UIconst.CONF_MENU_LANGUAGE)

        FrenchLanguage = QAction(UIconst.CONF_MENU_FRENCH,self)
        self.connect(FrenchLanguage,SIGNAL("triggered()"),lambda lang="fr":self.changelocale(lang))
        languageMenu.addAction(FrenchLanguage)

        EnglishLanguage = QAction(UIconst.CONF_MENU_ENGLISH,self)
        self.connect(EnglishLanguage,SIGNAL("triggered()"),lambda lang="en":self.changelocale(lang))
        languageMenu.addAction(EnglishLanguage) 

        GermanLanguage = QAction(UIconst.CONF_MENU_GERMAN,self)
        self.connect(GermanLanguage,SIGNAL("triggered()"),lambda lang="de":self.changelocale(lang))
        languageMenu.addAction(GermanLanguage)

        SpanishLanguage = QAction(UIconst.CONF_MENU_SPANISH,self)
        self.connect(SpanishLanguage,SIGNAL("triggered()"),lambda lang="es":self.changelocale(lang))
        languageMenu.addAction(SpanishLanguage) 

        SwedishLanguage = QAction(UIconst.CONF_MENU_SWEDISH,self)
        self.connect(SwedishLanguage,SIGNAL("triggered()"),lambda lang="sv":self.changelocale(lang))
        languageMenu.addAction(SwedishLanguage) 

        # TOOLKIT menu
        self.designerAction = QAction(UIconst.TOOLKIT_MENU_DESIGNER,self)
        self.connect(self.designerAction ,SIGNAL("triggered()"),self.designerTriggered)
        self.designerAction.setCheckable(True)
        self.designerAction.setChecked(self.qmc.designerflag)
        self.ToolkitMenu.addAction(self.designerAction)

        calculatorAction = QAction(UIconst.TOOLKIT_MENU_CALCULATOR,self)
        self.connect(calculatorAction,SIGNAL("triggered()"),self.calculator)
        self.ToolkitMenu.addAction(calculatorAction)   

        wheelAction = QAction(UIconst.TOOLKIT_MENU_WHEELGRAPH,self)
        self.connect(wheelAction,SIGNAL("triggered()"),self.graphwheel)
        self.ToolkitMenu.addAction(wheelAction)   

        hudAction = QAction(UIconst.TOOLKIT_MENU_EXTRAS,self)
        self.connect(hudAction,SIGNAL("triggered()"),self.hudset)
        self.ToolkitMenu.addAction(hudAction)


        # HELP menu
        helpAboutAction = QAction(UIconst.HELP_MENU_ABOUT,self)
        self.connect(helpAboutAction,SIGNAL("triggered()"),self.helpAbout)
        self.helpMenu.addAction(helpAboutAction)

        helpDocumentationAction = QAction(UIconst.HELP_MENU_DOCUMENTATION,self)
        self.connect(helpDocumentationAction,SIGNAL("triggered()"),self.helpHelp)
        self.helpMenu.addAction(helpDocumentationAction)        

        KshortCAction = QAction(UIconst.HELP_MENU_KEYBOARDSHORTCUTS,self)
        self.connect(KshortCAction,SIGNAL("triggered()"),self.viewKshortcuts)
        self.helpMenu.addAction(KshortCAction)

        errorAction = QAction(UIconst.HELP_MENU_ERRORS,self)
        self.connect(errorAction,SIGNAL("triggered()"),self.viewErrorLog)
        self.helpMenu.addAction(errorAction)

        messageAction = QAction(UIconst.HELP_MENU_MESSAGES,self)
        self.connect(messageAction,SIGNAL("triggered()"),self.viewMessageLog)
        self.helpMenu.addAction(messageAction)

        resetAction = QAction(UIconst.HELP_MENU_RESET,self)
        self.connect(resetAction,SIGNAL("triggered()"),self.resetApplication)
        self.helpMenu.addAction(resetAction)

        ############################## WIDGETS SECTION ########################################
       
        #create a Label object to display program status information
        self.messagelabel = QLabel()
        self.messagelabel.setIndent(10)
        
        self.pushbuttonstyles = {"OFF":"QPushButton {font-size: 16pt; font-weight: bold; color: lightgrey; background-color: #43d300}",
                                 "ON":"QPushButton {font-size: 16pt; font-weight: bold; color: yellow; background-color: red }",
                                 "DRY END":"QPushButton {font-size: 10pt; font-weight: bold; color: white; background-color: orange  }",
                                 "CHARGE":"QPushButton {font-size: 10pt; font-weight: bold; color: white; background-color: #f07800 }",                                 
                                 "FC START":"QPushButton {font-size: 10pt; font-weight: bold; color: white; background-color: orange  }",
                                 "FC END":"QPushButton {font-size: 10pt; font-weight: bold; color: white; background-color: orange }",
                                 "SC START":"QPushButton {font-size: 10pt; font-weight: bold; color: white; background-color: orange }",
                                 "SC END":"QPushButton {font-size: 10pt; font-weight: bold; color: white; background-color: orange }",
                                 "RESET":"QPushButton {font-size: 10pt; font-weight: bold; color: purple; background-color: white }",
                                 "HUD_OFF":"QPushButton {font-size: 10pt; font-weight: bold; color: white; background-color: #b5baff  }",
                                 "HUD_ON":"QPushButton {font-size: 10pt; font-weight: bold; color: white; background-color: #60ffed   }",                                 
                                 "EVENT":"QPushButton {font-size: 10pt; font-weight: bold; color: black; background-color: yellow }",                                 
                                 "DROP":"QPushButton {font-size: 10pt; font-weight: bold; color: white; background-color: #f07800 }",
                                 "PID":"QPushButton {font-size: 10pt; font-weight: bold; color: white; background-color: #92C3FF }",
                                 "SV +":"QPushButton {font-size: 10pt; font-weight: bold; color: white; background-color: #ffaaff }",
                                 "SV -":"QPushButton {font-size: 10pt; font-weight: bold; color: white; background-color: lightblue }",
                                 "SELECTED":"QPushButton {font-size: 12pt; font-weight: bold; color: yellow; background-color: #6D4824 }"  #keyboard moves
                                 }                                 
                        
        #create START STOP buttons        
        self.button_1 = QPushButton(QApplication.translate("Scope Button", "ON", None, QApplication.UnicodeUTF8))
        self.button_1.setFocusPolicy(Qt.NoFocus)
        self.button_1.setToolTip(QApplication.translate("Tooltip", "Starts recording", None, QApplication.UnicodeUTF8))
        self.button_1.setStyleSheet(self.pushbuttonstyles["OFF"])
        self.button_1.setMinimumHeight(50)
        self.connect(self.button_1, SIGNAL("clicked()"), self.qmc.OnMonitor)

        #create 1C START, 1C END, 2C START and 2C END buttons
        self.button_3 = QPushButton(QApplication.translate("Scope Button", "FC\nSTART", None, QApplication.UnicodeUTF8))
        self.button_3.setFocusPolicy(Qt.NoFocus)
        self.button_3.setStyleSheet(self.pushbuttonstyles["FC START"])        
        self.button_3.setMinimumHeight(50)
        self.button_3.setToolTip(QApplication.translate("Tooltip", "Marks the begining of First Crack (FC)", None, QApplication.UnicodeUTF8))
        self.connect(self.button_3, SIGNAL("clicked()"), self.qmc.mark1Cstart)

        self.button_4 = QPushButton(QApplication.translate("Scope Button", "FC\nEND", None, QApplication.UnicodeUTF8))
        self.button_4.setFocusPolicy(Qt.NoFocus)
        self.button_4.setStyleSheet(self.pushbuttonstyles["FC END"])
        self.button_4.setMinimumHeight(50)
        self.button_4.setToolTip(QApplication.translate("Tooltip", "Marks the end of First Crack (FC)", None, QApplication.UnicodeUTF8))
        self.connect(self.button_4, SIGNAL("clicked()"), self.qmc.mark1Cend)

        self.button_5 = QPushButton(QApplication.translate("Scope Button", "SC\nSTART", None, QApplication.UnicodeUTF8))
        self.button_5.setFocusPolicy(Qt.NoFocus)
        self.button_5.setStyleSheet(self.pushbuttonstyles["SC START"])
        self.button_5.setMinimumHeight(50)
        self.button_5.setToolTip(QApplication.translate("Tooltip", "Marks the begining of Second Crack (SC)", None, QApplication.UnicodeUTF8))
        self.connect(self.button_5, SIGNAL("clicked()"), self.qmc.mark2Cstart)

        self.button_6 = QPushButton(QApplication.translate("Scope Button", "SC\nEND", None, QApplication.UnicodeUTF8))
        self.button_6.setFocusPolicy(Qt.NoFocus)
        self.button_6.setStyleSheet(self.pushbuttonstyles["SC END"])
        self.button_6.setMinimumHeight(50)
        self.button_6.setToolTip(QApplication.translate("Tooltip", "Marks the end of Second Crack (SC)", None, QApplication.UnicodeUTF8))
        self.connect(self.button_6, SIGNAL("clicked()"), self.qmc.mark2Cend)

        #create RESET button
        self.button_7 = QPushButton(QApplication.translate("Scope Button", "RESET", None, QApplication.UnicodeUTF8))
        self.button_7.setFocusPolicy(Qt.NoFocus)
        self.button_7.setStyleSheet(self.pushbuttonstyles["RESET"])
        self.button_7.setMaximumSize(90, 45)
        self.button_7.setToolTip(QApplication.translate("Tooltip", "Resets Graph and Time", None, QApplication.UnicodeUTF8))
        self.connect(self.button_7, SIGNAL("clicked()"), self.qmc.reset_and_redraw)

        #create CHARGE button
        self.button_8 = QPushButton(QApplication.translate("Scope Button", "CHARGE", None, QApplication.UnicodeUTF8))
        self.button_8.setFocusPolicy(Qt.NoFocus)
        self.button_8.setStyleSheet(self.pushbuttonstyles["CHARGE"])
        self.button_8.setMinimumHeight(50)
        self.button_8.setToolTip(QApplication.translate("Tooltip", "Marks the begining of the roast (beans in)", None, QApplication.UnicodeUTF8))
        self.connect(self.button_8, SIGNAL("clicked()"), self.qmc.markCharge)

        #create DROP button
        self.button_9 = QPushButton(QApplication.translate("Scope Button", "DROP", None, QApplication.UnicodeUTF8))
        self.button_9.setFocusPolicy(Qt.NoFocus)
        self.button_9.setStyleSheet(self.pushbuttonstyles["DROP"])
        self.button_9.setMinimumHeight(50)
        self.button_9.setToolTip(QApplication.translate("Tooltip", "Marks the end of the roast (drop beans)", None, QApplication.UnicodeUTF8))
        self.connect(self.button_9, SIGNAL("clicked()"), self.qmc.markDrop)

        #create PID control button
        self.button_10 = QPushButton(QApplication.translate("Scope Button", "PID", None, QApplication.UnicodeUTF8))
        self.button_10.setFocusPolicy(Qt.NoFocus)
        self.button_10.setStyleSheet(self.pushbuttonstyles["PID"])        
        self.button_10.setMaximumSize(90, 45)
        self.connect(self.button_10, SIGNAL("clicked()"), self.PIDcontrol)        

        #create EVENT record button
        self.button_11 = QPushButton(QApplication.translate("Scope Button", "EVENT", None, QApplication.UnicodeUTF8))
        self.button_11.setFocusPolicy(Qt.NoFocus)
        self.button_11.setStyleSheet(self.pushbuttonstyles["EVENT"])                
        self.button_11.setMinimumHeight(50)
        self.button_11.setToolTip(QApplication.translate("Tooltip", "Marks an Event", None, QApplication.UnicodeUTF8))
        self.connect(self.button_11, SIGNAL("clicked()"), self.qmc.EventRecord) 
        
    	#create PID+5 button
        self.button_12 = QPushButton(QApplication.translate("Scope Button", "SV +5", None, QApplication.UnicodeUTF8))
        self.button_12.setFocusPolicy(Qt.NoFocus)
        self.button_12.setStyleSheet(self.pushbuttonstyles["SV +"])        
        self.button_12.setMaximumSize(90, 50)
        self.button_12.setMinimumHeight(50)
        self.button_12.setToolTip(QApplication.translate("Tooltip", "Increases the current SV value by 5", None, QApplication.UnicodeUTF8))

        #create PID+10 button
        self.button_13 = QPushButton(QApplication.translate("Scope Button", "SV +10", None, QApplication.UnicodeUTF8))
        self.button_13.setFocusPolicy(Qt.NoFocus)
        self.button_13.setStyleSheet(self.pushbuttonstyles["SV +"])        
        self.button_13.setMaximumSize(90, 50)
        self.button_13.setMinimumHeight(50)
        self.button_13.setToolTip(QApplication.translate("Tooltip", "Increases the current SV value by 10", None, QApplication.UnicodeUTF8))

        #create PID+20 button
        self.button_14 = QPushButton(QApplication.translate("Scope Button", "SV +20", None, QApplication.UnicodeUTF8))
        self.button_14.setFocusPolicy(Qt.NoFocus)
        self.button_14.setStyleSheet(self.pushbuttonstyles["SV +"])        
        self.button_14.setMaximumSize(90, 50)
        self.button_14.setMinimumHeight(50)
        self.button_14.setToolTip(QApplication.translate("Tooltip", "Increases the current SV value by 20", None, QApplication.UnicodeUTF8))

        #create PID-20 button
        self.button_15 = QPushButton(QApplication.translate("Scope Button", "SV -20", None, QApplication.UnicodeUTF8))
        self.button_15.setFocusPolicy(Qt.NoFocus)
        self.button_15.setStyleSheet(self.pushbuttonstyles["SV -"])        
        self.button_15.setMaximumSize(90, 50)
        self.button_15.setMinimumHeight(50)
        self.button_15.setToolTip(QApplication.translate("Tooltip", "Decreases the current SV value by 20", None, QApplication.UnicodeUTF8))

        #create PID-10 button
        self.button_16 = QPushButton(QApplication.translate("Scope Button", "SV -10", None, QApplication.UnicodeUTF8))
        self.button_16.setFocusPolicy(Qt.NoFocus)
        self.button_16.setStyleSheet(self.pushbuttonstyles["SV -"])        
        self.button_16.setMaximumSize(90, 50)
        self.button_16.setMinimumHeight(50)
        self.button_16.setToolTip(QApplication.translate("Tooltip", "Decreases the current SV value by 10", None, QApplication.UnicodeUTF8))

        #create PID-5 button
        self.button_17 = QPushButton(QApplication.translate("Scope Button", "SV -5", None, QApplication.UnicodeUTF8))
        self.button_17.setFocusPolicy(Qt.NoFocus)
        self.button_17.setStyleSheet(self.pushbuttonstyles["SV -"])        
        self.button_17.setMaximumSize(90, 50)
        self.button_17.setMinimumHeight(50)
        self.button_17.setToolTip(QApplication.translate("Tooltip", "Decreases the current SV value by 5", None, QApplication.UnicodeUTF8))
        
        #create HUD button
        self.button_18 = QPushButton(QApplication.translate("Scope Button", "HUD", None, QApplication.UnicodeUTF8))
        self.button_18.setFocusPolicy(Qt.NoFocus)
        self.button_18.setStyleSheet(self.pushbuttonstyles["HUD_OFF"])        
        self.button_18.setMaximumSize(90, 45)
        self.button_18.setContentsMargins(0,0,0,0)
        self.connect(self.button_18, SIGNAL("clicked()"), self.qmc.toggleHUD)
        self.button_18.setToolTip(QApplication.translate("Tooltip", "Turns ON/OFF the HUD", None, QApplication.UnicodeUTF8))

        #create DRY button
        self.button_19 = QPushButton(QApplication.translate("Scope Button", "DRY\nEND", None, QApplication.UnicodeUTF8))
        self.button_19.setFocusPolicy(Qt.NoFocus)
        self.button_19.setStyleSheet(self.pushbuttonstyles["DRY END"])        
        #self.button_19.setMaximumSize(90, 50)
        self.button_19.setMinimumHeight(50)
        self.button_19.setToolTip(QApplication.translate("Tooltip", "Marks the end of the Dry phase (DRYEND)", None, QApplication.UnicodeUTF8))
        self.connect(self.button_19, SIGNAL("clicked()"), self.qmc.markDryEnd)
 
        #connect PID sv easy buttons
        self.connect(self.button_12, SIGNAL("clicked()"),lambda x=5: self.pid.adjustsv(x))
        self.connect(self.button_13, SIGNAL("clicked()"),lambda x=10: self.pid.adjustsv(x))
        self.connect(self.button_14, SIGNAL("clicked()"),lambda x=20: self.pid.adjustsv(x))
        self.connect(self.button_15, SIGNAL("clicked()"),lambda x=-20: self.pid.adjustsv(x))
        self.connect(self.button_16, SIGNAL("clicked()"),lambda x=-10: self.pid.adjustsv(x))
        self.connect(self.button_17, SIGNAL("clicked()"),lambda x=-5: self.pid.adjustsv(x))

        # NavigationToolbar VMToolbar
        ntb = VMToolbar(self.qmc, self.main_widget)
        #ntb.setMinimumHeight(45)
        
        #create LCD displays
        #RIGHT COLUMN
        self.lcd1 = QLCDNumber() # time
        self.lcd1.setSegmentStyle(2)
        self.lcd1.setMinimumHeight(40)
        self.lcd1.setMinimumWidth(100)
        self.lcd2 = QLCDNumber() # Temperature MET
        self.lcd2.setSegmentStyle(2)   
        self.lcd2.setMinimumHeight(35)
        self.lcd3 = QLCDNumber() # Temperature BT
        self.lcd3.setSegmentStyle(2)
        self.lcd3.setMinimumHeight(35)
        self.lcd4 = QLCDNumber() # rate of change MET
        self.lcd4.setSegmentStyle(2)
        self.lcd4.setMinimumHeight(35)
        self.lcd5 = QLCDNumber() # rate of change BT
        self.lcd5.setSegmentStyle(2)
        self.lcd5.setMinimumHeight(35)
        self.lcd6 = QLCDNumber() # pid sv
        self.lcd6.setSegmentStyle(2)
        self.lcd6.setMinimumHeight(35) 
        self.lcd7 = QLCDNumber() # pid power % duty cycle
        self.lcd7.setSegmentStyle(2)
        self.lcd7.setMinimumHeight(35)
        #self.lcd1.setStyleSheet("QLCDNumber { }")

        self.lcd1.display("00:00")
        self.lcd2.display("0.0")
        self.lcd3.display("0.0")
        self.lcd4.display("0.0")
        self.lcd5.display("0.0")
        self.lcd6.display("0.0")
        self.lcd7.display("0.0")

        self.lcd1.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(self.lcdpaletteF["timer"],self.lcdpaletteB["timer"]))
        self.lcd2.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(self.lcdpaletteF["et"],self.lcdpaletteB["et"]))
        self.lcd3.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(self.lcdpaletteF["bt"],self.lcdpaletteB["bt"]))
        self.lcd4.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(self.lcdpaletteF["deltaet"],self.lcdpaletteB["deltaet"]))
        self.lcd5.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(self.lcdpaletteF["deltabt"],self.lcdpaletteB["deltabt"]))
        self.lcd6.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(self.lcdpaletteF["sv"],self.lcdpaletteB["sv"]))
        self.lcd7.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(self.lcdpaletteF["sv"],self.lcdpaletteB["sv"]))
        
        self.lcd1.setMaximumSize(90, 45)
        self.lcd2.setMaximumSize(90, 45)
        self.lcd3.setMaximumSize(90, 45)
        self.lcd4.setMaximumSize(90, 45)
        self.lcd5.setMaximumSize(90, 45)
        self.lcd6.setMaximumSize(90, 45)
        self.lcd7.setMaximumSize(90, 45)

        self.lcd1.setToolTip(QApplication.translate("Tooltip", "Timer",None, QApplication.UnicodeUTF8))
        self.lcd2.setToolTip(QApplication.translate("Tooltip", "ET Temperature",None, QApplication.UnicodeUTF8))
        self.lcd3.setToolTip(QApplication.translate("Tooltip", "BT Temperature",None, QApplication.UnicodeUTF8))
        self.lcd4.setToolTip(QApplication.translate("Tooltip", "ET/time (degrees/min)",None, QApplication.UnicodeUTF8))
        self.lcd5.setToolTip(QApplication.translate("Tooltip", "BT/time (degrees/min)",None, QApplication.UnicodeUTF8))
        self.lcd6.setToolTip(QApplication.translate("Tooltip", "Value of SV in PID",None, QApplication.UnicodeUTF8))
        self.lcd7.setToolTip(QApplication.translate("Tooltip", "PID power %",None, QApplication.UnicodeUTF8))

        #MET
        label2 = QLabel()
        label2.setText("<font color='black'><b>" + QApplication.translate("Label", "ET",None, QApplication.UnicodeUTF8) + "<\b></font>")
        label2.setAlignment(Qt.AlignRight)
        label2.setIndent(5)
        #BT
        label3 = QLabel()
        label3.setAlignment(Qt.AlignRight)
        label3.setText("<font color='black'><b>" + QApplication.translate("Label", "BT",None, QApplication.UnicodeUTF8) + "<\b></font>")
        label3.setIndent(5)
        #DELTA MET
        label4 = QLabel()
        label4.setAlignment(Qt.AlignRight)
        label4.setText("<font color='black'><b>" + QApplication.translate("Label", "DeltaET",None, QApplication.UnicodeUTF8) + "<\b></font>")
        label4.setIndent(5)
        # DELTA BT
        label5 = QLabel()
        label5.setAlignment(Qt.AlignRight)       
        label5.setText("<font color='black'><b>" + QApplication.translate("Label", "DeltaBT",None, QApplication.UnicodeUTF8) + "<\b></font>")
        label5.setIndent(5)
        # pid sv
        self.label6 = QLabel()
        self.label6.setAlignment(Qt.AlignRight)
        self.label6.setText("<font color='black'><b>" + QApplication.translate("Label", "PID SV",None, QApplication.UnicodeUTF8) + "<\b></font>")
        self.label6.setIndent(5)
        # pid power % duty cycle
        self.label7 = QLabel()
        self.label7.setAlignment(Qt.AlignRight)
        self.label7.setText("<font color='black'><b>" + QApplication.translate("Label", "PID %",None, QApplication.UnicodeUTF8) + "<\b></font>")
        self.label7.setIndent(5)

        # Stores messages up to 500        
        self.messagehist = []

        #only leave operational the control button if the device is Fuji PID
        #the SV buttons are activated from the PID control panel 
        self.button_10.setVisible(False)
        self.label6.setVisible(False)
        self.lcd6.setVisible(False)
        self.label7.setVisible(False)
        self.lcd7.setVisible(False)
            
        self.button_12.setVisible(False)
        self.button_13.setVisible(False)
        self.button_14.setVisible(False)
        self.button_15.setVisible(False)
        self.button_16.setVisible(False)
        self.button_17.setVisible(False)

        #### EVENT MINI EDITOR: View&Edits events without opening roast properties Dlg.
        self.eventlabel = QLabel(QApplication.translate("Label","Event #<b>0 </b>", None, QApplication.UnicodeUTF8))
        self.eventlabel.setIndent(5)
        self.eNumberSpinBox = QSpinBox()
        
        self.eNumberSpinBox.setFocusPolicy(Qt.NoFocus)
        self.eNumberSpinBox.setAlignment(Qt.AlignCenter)
        self.eNumberSpinBox.setToolTip(QApplication.translate("Tooltip", "Number of events found", None, QApplication.UnicodeUTF8))
        self.eNumberSpinBox.setRange(0,20)
        self.connect(self.eNumberSpinBox, SIGNAL("valueChanged(int)"),self.changeEventNumber)
        self.eNumberSpinBox.setMaximumWidth(40)
        self.lineEvent = QLineEdit()
        self.lineEvent.setFocusPolicy(Qt.ClickFocus)
        self.lineEvent.setMinimumWidth(200)
            
        self.eventlabel.setStyleSheet("background-color:'yellow';")

        self.etypeComboBox = QComboBox()
        self.etypeComboBox.setToolTip(QApplication.translate("Tooltip", "Type of event", None, QApplication.UnicodeUTF8))
        self.etypeComboBox.setFocusPolicy(Qt.NoFocus)
        self.etypeComboBox.addItems(self.qmc.etypes)
        
        self.valueComboBox = QComboBox()
        self.valueComboBox.setToolTip(QApplication.translate("Tooltip", "Value of event", None, QApplication.UnicodeUTF8))
        self.valueComboBox.setFocusPolicy(Qt.NoFocus)
        self.valueComboBox.addItems(self.qmc.eventsvalues)
        self.valueComboBox.setMaximumWidth(50)

        regextime = QRegExp(r"^-?[0-5][0-9]:[0-5][0-9]$")
        self.etimeline = QLineEdit()
        self.etimeline.setValidator(QRegExpValidator(regextime,self))
        self.etimeline.setFocusPolicy(Qt.ClickFocus)
        self.etimeline.setMaximumWidth(50)
        
        #create EVENT mini button
        self.buttonminiEvent = QPushButton(QApplication.translate("Button", "Update", None, QApplication.UnicodeUTF8))
        self.buttonminiEvent.setFocusPolicy(Qt.NoFocus)
        self.connect(self.buttonminiEvent, SIGNAL("clicked()"), self.miniEventRecord)
        self.buttonminiEvent.setToolTip(QApplication.translate("Tooltip", "Updates the event", None, QApplication.UnicodeUTF8))

        #### CUSTOM events buttons
        self.buttonlist = []
        
        #Create LOWER BUTTONS Widget layout QDialogButtonBox to stack all lower buttons
        self.lowerbuttondialog = QDialogButtonBox(Qt.Horizontal)
        self.lowerbuttondialog.setCenterButtons(True)
        #initiate configuration
        self.lowerbuttondialog.addButton(self.button_1,QDialogButtonBox.ActionRole)
        self.lowerbuttondialog.addButton(self.button_8,QDialogButtonBox.ActionRole)
        self.lowerbuttondialog.addButton(self.button_19,QDialogButtonBox.ActionRole)
        self.lowerbuttondialog.addButton(self.button_3,QDialogButtonBox.ActionRole)
        self.lowerbuttondialog.addButton(self.button_4,QDialogButtonBox.ActionRole)
        self.lowerbuttondialog.addButton(self.button_5,QDialogButtonBox.ActionRole)
        self.lowerbuttondialog.addButton(self.button_6,QDialogButtonBox.ActionRole)
        self.lowerbuttondialog.addButton(self.button_9,QDialogButtonBox.ActionRole)
        self.lowerbuttondialog.addButton(self.button_11,QDialogButtonBox.ActionRole)

        # set the focus on the main widget
        self.main_widget.setFocus()

        # set the central widget of MainWindow to main_widget
        self.setCentralWidget(self.main_widget)   
        
        #list of functions to chose from (using left-right keyboard arrow)
        self.keyboardmove  = [self.qmc.reset_and_redraw,self.qmc.toggleHUD,self.qmc.OnMonitor,self.qmc.markCharge,self.qmc.markDryEnd,self.qmc.mark1Cstart,self.qmc.mark1Cend,
                             self.qmc.mark2Cstart,self.qmc.mark2Cend,self.qmc.markDrop,self.qmc.EventRecord]
        
        #current function above
        self.keyboardmoveindex = 0
        #state flag for above. It is initialized by pressing SPACE or left-right arrows
        self.keyboardmoveflag = 0

        ####################   APPLICATION WINDOW (AW) LAYOUT  ##############################################
        
        mainlayout = QVBoxLayout(self.main_widget)
        mainlayout.setMargin(0)
        mainlayout.setSpacing(0)
        
        level1layout = QHBoxLayout()   # matplotlib toolbox + HUD button + reset button + LCD Timer

        level3layout = QHBoxLayout()   # PID buttons, graph, temperature LCDs
        
        EventsLayout = QHBoxLayout()
        EventsLayout.setMargin(0)
        EventsLayout.setSpacing(0)       
        LCDlayout = QVBoxLayout()    
        pidbuttonLayout = QVBoxLayout()
             
        #EVENT MINIEDITOR layout        
        EventsLayout.addWidget(self.eventlabel)
        EventsLayout.addSpacing(5)
        EventsLayout.addWidget(self.etimeline)
        EventsLayout.addSpacing(5)
        EventsLayout.addWidget(self.lineEvent)  
        EventsLayout.addSpacing(5)
        EventsLayout.addWidget(self.etypeComboBox)
        EventsLayout.addSpacing(5)
        EventsLayout.addWidget(self.valueComboBox)
        EventsLayout.addSpacing(5)
        EventsLayout.addWidget(self.eNumberSpinBox)        
        EventsLayout.addSpacing(5)      
        EventsLayout.addWidget(self.buttonminiEvent)
        self.EventsGroupLayout = QGroupBox()        
        self.EventsGroupLayout.setLayout(EventsLayout)
 
        #place control buttons + LCDs inside vertical button layout manager
        LCDlayout.addWidget(label2)
        LCDlayout.addWidget(self.lcd2)
        LCDlayout.addStretch()   
        LCDlayout.addWidget(label3)
        LCDlayout.addWidget(self.lcd3)
        LCDlayout.addStretch()
        LCDlayout.addWidget(self.label6)
        LCDlayout.addWidget(self.lcd6)
        LCDlayout.addStretch()
        LCDlayout.addWidget(self.label7)
        LCDlayout.addWidget(self.lcd7)
        LCDlayout.addStretch()
        LCDlayout.addWidget(label4)
        LCDlayout.addWidget(self.lcd4)
        LCDlayout.addStretch()   
        LCDlayout.addWidget(label5)
        LCDlayout.addWidget(self.lcd5)
        LCDlayout.addStretch()   
                      
        #PID Buttons       
        pidbuttonLayout.addWidget(self.button_14)       
        pidbuttonLayout.addWidget(self.button_13)
        pidbuttonLayout.addWidget(self.button_12)
        pidbuttonLayout.addWidget(self.button_17)
        pidbuttonLayout.addWidget(self.button_16)
        pidbuttonLayout.addWidget(self.button_15)

    	#level 1
        level1layout.addWidget(ntb)
        level1layout.addSpacing(15)
        level1layout.addWidget(self.button_10)
        level1layout.addSpacing(15)
        level1layout.addWidget(self.button_18)
        level1layout.addSpacing(15)
        level1layout.addWidget(self.button_7)
        level1layout.addSpacing(20)
        level1layout.addWidget(self.lcd1)

        #level 3
        level3layout.addLayout(pidbuttonLayout,0)
        level3layout.addWidget(self.stack,1)
        level3layout.addLayout(LCDlayout,2)
        
        mainlayout.addLayout(level1layout)       
        mainlayout.addWidget(self.messagelabel)
        mainlayout.addLayout(level3layout)
        mainlayout.addWidget(self.lowerbuttondialog)
        mainlayout.addSpacing(10)
        mainlayout.addWidget(self.EventsGroupLayout)

###################################   APPLICATION WINDOW (AW) FUNCTIONS  ####################################
    def setdpi(self,dpi):
        if aw:
            self.qmc.fig.set_dpi(dpi)
            #move widget to update display
            self.showFullScreen()
            self.showNormal()        

    #call from user configured event buttons    
    def recordextraevent(self,ee):
        if self.qmc.flagon:
            self.qmc.EventRecord()
            self.qmc.specialeventstype[-1] = self.extraeventstypes[ee]    
            self.qmc.specialeventsvalue[-1] = self.extraeventsvalues[ee]
            self.qmc.specialeventsStrings[-1] = self.extraeventsdescriptions[ee]
            
            self.setminieditor2lastevent()
            self.qmc.redraw()
            
            if self.extraeventsactions[ee]:   	#0 = None; 1= Serial Command; 2= Call program; 3= Multiple Event
                if self.extraeventsactions[ee] == 1:                    
                    aw.extraeventsactionstrings[ee] = str(aw.extraeventsactionstrings[ee])                        
                    extraeventsactionstringscopy = ""
                    #example a2b_uu("Hello") sends Hello in binary format instead of ASCII
                    if "a2b_uu" in aw.extraeventsactionstrings[ee]:
                        aw.extraeventsactionstrings[ee] = aw.extraeventsactionstrings[ee][(len("a2b_uu")+1):]  # removes function-name + char ( 
                        aw.extraeventsactionstrings[ee] = aw.extraeventsactionstrings[ee][:1]                 # removes )  
                        extraeventsactionstringscopy = binascii.a2b_uu(aw.extraeventsactionstrings[ee])
                    if extraeventsactionstringscopy:
                        self.ser.sendTXcommand(extraeventsactionstringscopy)                
                    else:    
                        self.ser.sendTXcommand(aw.extraeventsactionstrings[ee])
                                                    
                elif aw.extraeventsactions[ee] == 2:
                    try:
                        fname = unicode(self.extraeventsactionstrings[ee])
                        QDesktopServices.openUrl(QUrl(u"file:///" + unicode(QDir().current().absolutePath()) + u"/" + fname, QUrl.TolerantMode))            
                    except Exception,e:
                        self.qmc.adderror(QApplication.translate("Error Message","Exception Error: recordextraevent() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
                elif aw.extraeventsactions[ee] == 3:
                    events = aw.extraeventsactionstrings[ee].split(",")
                    for i in range(len(events)):
                        buttonnumber = int(events[i])-1
                        if aw.extraeventsactions[buttonnumber] != 3:   #avoid calling other buttons with multiple actions to avoid possible infinite loops
                            self.recordextraevent(buttonnumber)
                    
        else:
            self.sendmessage(QApplication.translate("Message Area","Timer is OFF", None, QApplication.UnicodeUTF8))

    def resetApplication(self):
        string = QApplication.translate("MessageBox","Do you want to reset all settings?", None, QApplication.UnicodeUTF8)
        reply = QMessageBox.warning(self,QApplication.translate("MessageBox Caption","Factory Reset", None, QApplication.UnicodeUTF8),string,
                            QMessageBox.Reset | QMessageBox.Cancel)
        if reply == QMessageBox.Reset :
            #raise flag. Next time app will open, the settings (bad settings) will not be loaded.
            self.resetqsettings = 1
            self.close()
        elif reply == QMessageBox.Cancel:            
            return
             
    def on_actionCut_triggered(self,checked=None):
        try:
            app.activeWindow().focusWidget().cut()
        except:
            pass
        
    def on_actionCopy_triggered(self,checked=None):
        try:
            app.activeWindow().focusWidget().copy()
        except:
            pass
        
    def on_actionPaste_triggered(self,checked=None):
        try:
            app.activeWindow().focusWidget().paste()
        except:
            pass
            
    def sendmessage(self,message):
        #keep a max of 100 messages
        if len(self.messagehist) > 99:
            self.messagehist = self.messagehist[1:]
        timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz ")))    #zzz = miliseconds
        self.messagehist.append(timez + message)
        self.messagelabel.setText(message)

    def update_extraeventbuttons_visibility(self):
        for i in range(len(self.buttonlist)):
            if self.extraeventsvisibility[i]:
                self.buttonlist[i].setVisible(True)
            else:
                self.buttonlist[i].setVisible(False)
    
    def update_minieventline_visibility(self):
        if self.minieventsflag:
            self.etypeComboBox.setVisible(True)
            self.valueComboBox.setVisible(True)
            self.eventlabel.setVisible(True)
            self.buttonminiEvent.setVisible(True)
            self.lineEvent.setVisible(True)
            self.eNumberSpinBox.setVisible(True)
            self.etimeline.setVisible(True)
            self.EventsGroupLayout.setVisible(True)
        else:
            self.lineEvent.setVisible(False)
            self.etypeComboBox.setVisible(False)
            self.valueComboBox.setVisible(False)
            self.eventlabel.setVisible(False)
            self.buttonminiEvent.setVisible(False)
            self.eNumberSpinBox.setVisible(False)
            self.etimeline.setVisible(False)
            self.EventsGroupLayout.setVisible(False)            

    #keyboard presses. There must not be widgets (pushbuttons, comboboxes, etc) in focus in order to work 
    def keyPressEvent(self,event):    
        key = int(event.key())
        #uncomment next line to find the integer value of a key
        #keyboard move keys
        if key == 32:                       #SELECTS ACTIVE BUTTON
            self.moveKbutton("space")
        if key == 16777220:                 #TURN ON/OFF KEYBOARD MOVES
            self.releaseminieditor()
            self.moveKbutton("enter")
        if key == 16777216: 	    	    #ESCAPE 	
            self.releaseminieditor()          
        elif key == 16777234:               #MOVES CURRENT BUTTON LEFT
            self.moveKbutton("left")
        elif key == 16777236:               #MOVES CURRENT BUTTON RIGHT
            self.moveKbutton("right")
        elif key == 83:                     #letter S (future automatic save)
            self.automaticsave()          
        else:
            QWidget.keyPressEvent(self, event)

    
    def releaseminieditor(self):
        if self.minieventsflag:
            self.eNumberSpinBox.releaseKeyboard()
            self.lineEvent.releaseKeyboard()
            self.etimeline.releaseKeyboard()
            self.etypeComboBox.releaseKeyboard()
            self.valueComboBox.releaseKeyboard()
            self.lineEvent.clearFocus()            
            self.valueComboBox.clearFocus()
            self.etimeline.clearFocus()

    def moveKbutton(self,command):
        #"Enter" toggles ON/OFF keyboard    
        if command =="enter":
            if self.keyboardmoveflag == 0:                                     
                #turn on
                self.keyboardmoveflag = 1
                self.keyboardmoveindex = 2
                self.sendmessage(QApplication.translate("Message Area","Keyboard moves turned ON", None, QApplication.UnicodeUTF8))
                self.button_1.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                
            elif self.keyboardmoveflag == 1:                  
                # turn off 
                self.keyboardmoveflag = 0
                # clear all
                self.sendmessage(QApplication.translate("Message Area","Keyboard moves turned OFF", None, QApplication.UnicodeUTF8))
                if self.qmc.flagon:    
                    self.button_1.setStyleSheet(self.pushbuttonstyles["ON"])
                else:
                    self.button_1.setStyleSheet(self.pushbuttonstyles["OFF"])                 
                self.button_8.setStyleSheet(self.pushbuttonstyles["CHARGE"])
                self.button_19.setStyleSheet(self.pushbuttonstyles["DRY END"])
                self.button_3.setStyleSheet(self.pushbuttonstyles["FC START"])
                self.button_4.setStyleSheet(self.pushbuttonstyles["FC END"])
                self.button_5.setStyleSheet(self.pushbuttonstyles["SC START"])
                self.button_6.setStyleSheet(self.pushbuttonstyles["SC END"])
                self.button_9.setStyleSheet(self.pushbuttonstyles["DROP"])
                self.button_11.setStyleSheet(self.pushbuttonstyles["EVENT"])
                self.button_7.setStyleSheet(self.pushbuttonstyles["RESET"])
                if self.qmc.HUDflag:
                    self.button_18.setStyleSheet(self.pushbuttonstyles["HUD_ON"])
                else:    
                    self.button_18.setStyleSheet(self.pushbuttonstyles["HUD_OFF"])

        #if moves on              
        if self.keyboardmoveflag:       
            if command == "space":
                self.keyboardmove[self.keyboardmoveindex]()   #apply button command
                #behaviour rules after pressing a button
                #if RESET is pressed jump to ON     
                if self.keyboardmoveindex == 0:
                    self.keyboardmoveindex = 2
                    self.button_1.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                    self.button_7.setStyleSheet(self.pushbuttonstyles["RESET"])
                #if less than EVENT jump forward to the right once automatically    
                elif self.keyboardmoveindex > 1:
                    self.moveKbutton("right")
                    
            #command left-right: moves button          
            else:
                # self.button_1 = ON, self.button_8 = CHARGE, self.button_19 = DRYEND, self.button_3 = FC START, self.button_4 = FC END,
                # self.button_5 = SC START, self.button_6 = SC END, self.button_9 = DROP,self.button_11 = EVENT,
                # self.button_7 = RESET, self.button_18 = HUD
                
                #Check current index (location)
                #location in button RESET    
                if self.keyboardmoveindex == 0:
                    if command == "left":
                        self.button_18.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.button_7.setStyleSheet(self.pushbuttonstyles["RESET"])
                        self.keyboardmoveindex = 1
                    if command == "right":
                        if self.eventsbuttonflag:
                            self.button_11.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                            self.keyboardmoveindex = 10
                        if not self.eventsbuttonflag:
                            self.button_9.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                            self.keyboardmoveindex = 9
                    self.button_7.setStyleSheet(self.pushbuttonstyles["RESET"])
                #location in button HUD    
                elif self.keyboardmoveindex == 1:   
                    if command == "left":
                        self.keyboardmoveindex = 2
                        if self.qmc.HUDflag:
                            self.button_18.setStyleSheet(self.pushbuttonstyles["HUD_ON"])
                        else:    
                            self.button_18.setStyleSheet(self.pushbuttonstyles["HUD_OFF"])
                        self.button_1.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                    elif command == "right":
                        self.button_7.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 0 
                        if self.qmc.HUDflag:
                            self.button_18.setStyleSheet(self.pushbuttonstyles["HUD_ON"])
                        else:    
                            self.button_18.setStyleSheet(self.pushbuttonstyles["HUD_OFF"])
                
                #location in button ON/OFF
                elif self.keyboardmoveindex == 2:
                    if command == "right":
                        self.button_8.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 3                        
                        if self.qmc.flagon:    
                            self.button_1.setStyleSheet(self.pushbuttonstyles["ON"])
                        else:
                            self.button_1.setStyleSheet(self.pushbuttonstyles["OFF"])                        
                    elif command == "left": #jump to HUD (close circle)
                        self.keyboardmoveindex = 1
                        self.button_18.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        if self.qmc.flagon:    
                            self.button_1.setStyleSheet(self.pushbuttonstyles["ON"])
                        else:
                            self.button_1.setStyleSheet(self.pushbuttonstyles["OFF"])                        
                #location in button CHARGE
                elif self.keyboardmoveindex == 3:
                    if command == "right":
                        self.button_19.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 4
                    elif command == "left":
                        self.button_1.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 2
                    self.button_8.setStyleSheet(self.pushbuttonstyles["CHARGE"])
                    
                #location in button DRY END    
                elif self.keyboardmoveindex == 4:
                    if command == "right":
                        self.button_3.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 5
                    elif command == "left":
                        self.button_8.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 3
                    self.button_19.setStyleSheet(self.pushbuttonstyles["DRY END"])
                    
                #location in button FC START    
                elif self.keyboardmoveindex == 5:
                    if command == "right":
                        self.button_4.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 6
                    elif command == "left":
                        self.button_19.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 4
                    self.button_3.setStyleSheet(self.pushbuttonstyles["FC START"])
                   
                #location in button FC END        
                elif self.keyboardmoveindex == 6:    
                    if command == "right":
                        self.button_5.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 7
                    elif command == "left":
                        self.button_3.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 5
                    self.button_4.setStyleSheet(self.pushbuttonstyles["FC END"])
                        
                #location in button SC START        
                elif self.keyboardmoveindex == 7:
                    if command == "right":
                        self.button_6.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 8
                    elif command == "left":
                        self.button_4.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 6
                    self.button_5.setStyleSheet(self.pushbuttonstyles["SC START"])
                       
                #location in button SC END    
                elif self.keyboardmoveindex == 8:
                    if command == "right":
                        self.button_9.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 9
                    elif command == "left":
                        self.button_5.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 7
                    self.button_6.setStyleSheet(self.pushbuttonstyles["SC END"])
                        
                #location in button DROP    
                elif self.keyboardmoveindex == 9:
                    if command == "right":
                        if self.eventsbuttonflag:
                            self.button_11.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                            self.keyboardmoveindex = 10                            
                        else:
                            self.button_7.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                            self.keyboardmoveindex = 0
                    elif command == "left":
                        self.button_6.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.keyboardmoveindex = 8
                        
                    self.button_9.setStyleSheet(self.pushbuttonstyles["DROP"])
                    
                #location in button EVENT    
                elif self.keyboardmoveindex == 10:
                    if command == "right":
                            self.button_7.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                            self.button_11.setStyleSheet(self.pushbuttonstyles["EVENT"])
                            self.keyboardmoveindex = 0                            
                    if command == "left":
                        self.button_9.setStyleSheet(self.pushbuttonstyles["SELECTED"])
                        self.button_11.setStyleSheet(self.pushbuttonstyles["EVENT"])
                        self.keyboardmoveindex = 9

                            
    #sound feedback when pressing a push button
    def soundpop(self):
        if self.soundflag:
            try:
                import pyaudio
            except ImportError:
                return False

            p = pyaudio.PyAudio()
            stream = p.open(rate=44100, channels=1, format=pyaudio.paFloat32, output=True)
            stream.write(array.array('f',(.25 * math.sin(i / 10.) for i in range(44100))))
            stream.close()
            p.terminate()
            
    #automatation of filename when saving a file through keyboard shortcut. Speeds things up for batch roasting. 
    def automaticsave(self):
        try:
            if self.qmc.autosavepath and self.qmc.autosaveflag:
                filename = self.qmc.autosaveprefix + u"-"
                filename += unicode(QDateTime.currentDateTime().toString(QString("dd-MM-yy_hhmm")))
                filename += u".txt"
                oldDir = unicode(QDir.current())           
                newdir = QDir.setCurrent(self.qmc.autosavepath)
                #write
                self.serialize(QString(filename),self.getProfile())
                #restore dirs
                QDir.setCurrent(oldDir)

                self.sendmessage(QApplication.translate("Message Area","Profile %1 saved in: %2", None, QApplication.UnicodeUTF8).arg(filename).arg(self.qmc.autosavepath))
                self.qmc.safesaveflag = False

                return filename

            else:
                self.sendmessage(QApplication.translate("Message Area","Empty path or box unchecked in Autosave", None, QApplication.UnicodeUTF8))
                self.autosaveconf()               

        except IOError,e:
            self.qmc.adderror(QApplication.translate("Error Message", "IO Error: automaticsave() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
          
    def viewKshortcuts(self):
        string = QApplication.translate("MessageBox", "<b>[ENTER]</b> = Turns ON/OFF Keyboard Shortcuts",None, QApplication.UnicodeUTF8) + "<br><br>"
        string += QApplication.translate("MessageBox", "<b>[SPACE]</b> = Choses current button",None, QApplication.UnicodeUTF8) + "<br><br>"  
        string += QApplication.translate("MessageBox", "<b>[LEFT]</b> = Move to the left",None, QApplication.UnicodeUTF8) + "<br><br>"
        string += QApplication.translate("MessageBox", "<b>[RIGHT]</b> = Move to the right",None, QApplication.UnicodeUTF8) + "<br><br>"
        string += QApplication.translate("MessageBox", "<b>[s]</b> = Autosave",None, QApplication.UnicodeUTF8) + "<br><br>"
        string += QApplication.translate("MessageBox", "<b>[CRTL N]</b> = Autosave + Reset + ON",None, QApplication.UnicodeUTF8) + "<br><br>"

        QMessageBox.information(self,QApplication.translate("MessageBox Caption", "Keyboard Shotcuts",None, QApplication.UnicodeUTF8),string)
            

    #sets minieditor 2 last event	
    def setminieditor2lastevent(self):
       self.lineEvent.setText(self.qmc.specialeventsStrings[-1])
       self.valueComboBox.setCurrentIndex(self.qmc.specialeventsvalue[-1])
       self.etypeComboBox.setCurrentIndex(self.qmc.specialeventstype[-1])
       timez = self.qmc.stringfromseconds(int(self.qmc.timex[aw.qmc.specialevents[-1]]-self.qmc.timex[aw.qmc.timeindex[0]]))       
       self.etimeline.setText(timez)

    #moves events in minieditor         	
    def changeEventNumber(self):
       if self.qmc.designerflag:
           return
       #check
       lenevents = len(self.qmc.specialevents)
       currentevent = self.eNumberSpinBox.value()
       self.eventlabel.setText(QApplication.translate("Label", "Event #<b>%1 </b>",None, QApplication.UnicodeUTF8).arg(currentevent))
       if currentevent == 0:
           self.lineEvent.setText("")
           self.valueComboBox.setCurrentIndex(0)
           self.etypeComboBox.setCurrentIndex(0)
           self.etimeline.setText("")
           self.qmc.resetlines()
           self.qmc.fig.canvas.draw()
           return
       if currentevent > lenevents:
           self.eNumberSpinBox.setValue(lenevents)
           return
       else:
           self.lineEvent.setText(self.qmc.specialeventsStrings[currentevent-1])
           timez = self.qmc.stringfromseconds(int(self.qmc.timex[aw.qmc.specialevents[currentevent-1]]-self.qmc.timex[aw.qmc.timeindex[0]]))
           self.etimeline.setText(timez)
           self.valueComboBox.setCurrentIndex(self.qmc.specialeventsvalue[currentevent-1])
           self.etypeComboBox.setCurrentIndex(self.qmc.specialeventstype[currentevent-1])
           etimeindex = self.qmc.specialevents[currentevent-1]
           #plot little dot 
           self.qmc.resetlines() #clear old
           #plot highest ET or BT (sometimes only BT is plot (et is zero))
           if currentevent:
               if self.qmc.temp1[etimeindex] > self.qmc.temp2[etimeindex]:
                   self.qmc.ax.plot(self.qmc.timex[etimeindex], self.qmc.temp1[etimeindex], "o", color = self.qmc.palette["et"])
               else:
                   self.qmc.ax.plot(self.qmc.timex[etimeindex], self.qmc.temp2[etimeindex], "o", color = self.qmc.palette["bt"])
               
           self.qmc.fig.canvas.draw()

    #updates events from mini edtitor	
    def miniEventRecord(self):
        lenevents = self.eNumberSpinBox.value()
        if lenevents:
            self.qmc.specialeventstype[lenevents-1] = self.etypeComboBox.currentIndex()
            self.qmc.specialeventsvalue[lenevents-1] = self.valueComboBox.currentIndex()
            self.qmc.specialeventsStrings[lenevents-1] = unicode(self.lineEvent.text())
            self.qmc.specialevents[lenevents-1] = self.qmc.time2index(self.qmc.timex[self.qmc.timeindex[0]]+ self.qmc.stringtoseconds(unicode(self.etimeline.text())))

            self.lineEvent.clearFocus()
            self.eNumberSpinBox.clearFocus()
            self.etimeline.clearFocus()                        

            self.qmc.redraw()
            
            #plot highest ET or BT (sometimes only BT is plot (et is zero))
            etimeindex = self.qmc.specialevents[lenevents-1]
            if self.qmc.temp1[etimeindex] > self.qmc.temp2[etimeindex]:
                self.qmc.ax.plot(self.qmc.timex[etimeindex], self.qmc.temp1[etimeindex], "o", color = self.qmc.palette["et"])
            else:
                self.qmc.ax.plot(self.qmc.timex[etimeindex], self.qmc.temp2[etimeindex], "o", color = self.qmc.palette["bt"])
               
            self.qmc.fig.canvas.draw()

            string = ""
            if len(self.qmc.specialeventsStrings[lenevents-1]) > 5:
                string += self.qmc.specialeventsStrings[lenevents-1][0:5]
                string += "..."

            message = QApplication.translate("Message Area","Event #%1:  %2 has been updated", None, QApplication.UnicodeUTF8).arg(str(lenevents)).arg(string)
            self.sendmessage(message)
        
    def strippedName(self, fullFileName):
        return unicode(QFileInfo(fullFileName).fileName())
        
    def strippedDir(self, fullFileName):
        return unicode(QFileInfo(fullFileName).dir().dirName())

    def setCurrentFile(self, fileName):
        self.curFile = fileName
        if self.curFile:
            self.setWindowTitle(("%s - " + self.windowTitle) % self.strippedName(self.curFile))
            settings = QSettings()
            files = settings.value('recentFileList').toStringList()
            try:
                files.removeAll(fileName)
            except ValueError:
                pass
            files.insert(0, fileName)
            del files[self.MaxRecentFiles:]
            settings.setValue('recentFileList', files)
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, ApplicationWindow):
                    widget.updateRecentFileActions()
        else:
            self.setWindowTitle(self.windowTitle)
 
    def updateRecentFileActions(self):
        settings = QSettings()
        files = settings.value('recentFileList').toStringList()
        strippedNames = map(self.strippedName,files)
        numRecentFiles = min(len(files), self.MaxRecentFiles)
 
        for i in range(numRecentFiles):
            strippedName = self.strippedName(files[i])
            if strippedNames.count(strippedName) > 1:
                text = "&%s (%s)" % (strippedName, self.strippedDir(files[i]))
            else:
                text = "&%s" % strippedName
            self.recentFileActs[i].setText(text)
            self.recentFileActs[i].setData(files[i])
            self.recentFileActs[i].setVisible(True)
 
        for j in range(numRecentFiles, self.MaxRecentFiles):
            self.recentFileActs[j].setVisible(False)
 
    def openRecentFile(self):
        action = self.sender()
        if action:
            self.loadFile(action.data().toString())
 
    def getDefaultPath(self):
        userprofilepath_dir = QDir()
        userprofilepath_dir.setPath(self.userprofilepath)
        userprofilepath_elements = userprofilepath_dir.absolutePath().split("/") # directories as QStrings
        profilepath_dir = QDir()
        profilepath_dir.setPath(self.profilepath)
        profilepath_elements = profilepath_dir.absolutePath().split("/")
        #compare profilepath with userprofilepath (modulo the last two segments which are month/year respectively)
        if len(userprofilepath_elements) == len(profilepath_elements) and len(userprofilepath_elements) > 1 and reduce(lambda x,y: x and y, map(lambda x : x[0] == x[1], zip(userprofilepath_elements[:-2],profilepath_elements[:-2]))):
            return self.profilepath
        else:
            return self.userprofilepath
            
    def setDefaultPath(self,file):
        if file:
            filepath_dir = QDir()
            filepath_dir.setPath(file)
            filepath_elements = filepath_dir.absolutePath().split("/")[:-1] # directories as QStrings (without the filename)
            self.userprofilepath = unicode(reduce(lambda x,y: x + '/' + y, filepath_elements) + "/")
                
    #the central OpenFileDialog function that should always be called. Besides triggering the file dialog it
    #reads and sets the actual directory
    def ArtisanOpenFileDialog(self,msg="Open",ext="*",path=None):
        if path == None:   
            path = self.getDefaultPath() 
        file = unicode(QFileDialog.getOpenFileName(self,msg,path,ext))
        self.setDefaultPath(file)
        return unicode(file)
 
    #the central SaveFileDialog function that should always be called. Besides triggering the file dialog it
    #reads and sets the actual directory
    def ArtisanSaveFileDialog(self,msg=QApplication.translate("MessageBox Caption","Save",None, QApplication.UnicodeUTF8),ext="*.txt",path=None):
        if path == None:
            path = self.getDefaultPath() 
        file = unicode(QFileDialog.getSaveFileName(self,msg,path,ext))
        self.setDefaultPath(file)
        return file
 
    #the central ExistingDirectoryDialog function that should always be called. Besides triggering the file dialog it
    #reads and sets the actual directory
    def ArtisanExistingDirectoryDialog(self,msg=QApplication.translate("MessageBox Caption","Select Directory",None, QApplication.UnicodeUTF8),path=None):
        if path == None:
            path = self.getDefaultPath() 
        file = unicode(QFileDialog.getExistingDirectory(self,msg,path))
        self.setDefaultPath(file)
        return file
        
    def newRoast(self):
        #stop current roast (if any)
        if self.qmc.flagon:
            if self.qmc.timeindex[0] == -1:
                self.sendmessage(QApplication.translate("Message Area","No profile found", None, QApplication.UnicodeUTF8))
                return
            #mark drop if not yet done
            if self.qmc.timeindex[6] == 0:
                self.qmc.markDrop()
            #invoke "OFF"
            self.qmc.OffMonitor()
            
            #store, reset and redraw
            if self.qmc.autosavepath and self.qmc.autosaveflag:
                #if autosave mode active we just save automatic
                filename = self.automaticsave()
            else:
                self.sendmessage(QApplication.translate("Message Area","Empty path or box unchecked in Autosave", None, QApplication.UnicodeUTF8))
                self.autosaveconf()
                return
            self.qmc.reset_and_redraw()
            #start new roast
            self.qmc.OnMonitor()

            self.sendmessage(QApplication.translate("Message Area","%1 has been saved. New roast has started", None, QApplication.UnicodeUTF8).arg(filename))
        else:
            self.qmc.OnMonitor()
            
    def fileLoad(self):
        fileName = self.ArtisanOpenFileDialog()
        if fileName:
            self.loadFile(fileName)
 
    #loads stored profiles. Called from file menu
    def loadFile(self,filename):
        f = None
        old_mode = self.qmc.mode
        
        try:       
            f = QFile(unicode(filename))
            if not f.open(QIODevice.ReadOnly):
                raise IOError, unicode(f.errorString())    
            stream = QTextStream(f)
            self.qmc.reset()

            firstChar = stream.read(1)
            if firstChar == "{":    
                f.close()       
                self.setProfile(self.deserialize(filename)) 
            else:      
                self.sendmessage(QApplication.translate("Message Area","Invalid artisan format", None, QApplication.UnicodeUTF8))

            aw.qmc.backmoveflag = 1 # this ensures that an already loaded profile gets aligned to the one just loading

            #change Title
            self.qmc.ax.set_title(self.qmc.title, size=20, color= self.qmc.palette["title"])

            #update etypes combo box
            self.etypeComboBox.clear()
            self.etypeComboBox.addItems(self.qmc.etypes)
            
            #Plot everything
            self.qmc.redraw()

            message =  QApplication.translate("Message Area","%1  loaded ", None, QApplication.UnicodeUTF8).arg(unicode(filename))
            self.sendmessage(message)
            
            self.setCurrentFile(filename)
                
        except IOError,e:
            #import traceback
            #traceback.print_exc(file=sys.stdout)
            self.qmc.adderror(QApplication.translate("Error Message", "IO Error: fileload() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

        except ValueError,e:
            #import traceback
            #traceback.print_exc(file=sys.stdout)
            self.qmc.adderror(QApplication.translate("Error Message", "Value Error: fileload() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

        except Exception,e:
            #import traceback
            #traceback.print_exc(file=sys.stdout)
            self.qmc.adderror(QApplication.translate("Error Message", "Exception Error: loadFile() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return
        
        finally:
            if f:
                f.close()


    # Loads background profile
    def loadbackground(self,filename):
        try:        
            f = QFile(unicode(filename))
            if not f.open(QIODevice.ReadOnly):
                raise IOError, unicode(f.errorString())
            stream = QTextStream(f)
            
            firstChar = stream.read(1)
            if firstChar == "{":            
                f.close()
                profile = self.deserialize(filename)
                self.qmc.timeB = profile["timex"]
                self.qmc.temp1B = profile["temp1"]
                self.qmc.temp2B = profile["temp2"]
                self.qmc.backgroundEvents = profile["specialevents"]
                self.qmc.backgroundEtypes = profile["specialeventstype"]
                self.qmc.backgroundEvalues = profile["specialeventsvalue"]
                self.qmc.backgroundEStrings = profile["specialeventsStrings"]
                self.qmc.backgroundFlavors = profile["flavors"]
                #if old format < 0.5.0 version  (identified by numbers less than 1.). convert
                if self.qmc.backgroundFlavors[0] < 1. and self.qmc.backgroundFlavors[-1] < 1.:
                    l = len(self.qmc.backgroundFlavors)
                    for i in range(l):
                        self.qmc.backgroundFlavors[i] *= 10.
                    self.qmc.backgroundFlavors = self.qmc.backgroundFlavors[:(l-1)]
                if "etypes" in profile:
                    self.qmc.Betypes = profile["etypes"]
                if "timeindex" in profile:
                    self.qmc.timeindexB = profile["timeindex"]          #if new profile found with variable timeindex
                else:                                                   #old profile format
                    if "startend" in profile:
                        startendB = profile["startend"]
                        varCB = profile["cracks"]
                        if "dryend" in profile:
                            dryendB = profile["dryend"]
                        else:
                            dryendB = [0,0]
                        times = []
                        times.append(startendB[0])
                        times.append(dryend[0])
                        times.append(varCB[0])
                        times.append(varCB[2])
                        times.append(varCB[4])
                        times.append(varCB[6])
                        times.append(startendB[2])                    
                        self.qmc.timebackgroundindexupdate(times[:])

            else:      
                self.sendmessage(QApplication.translate("Message Area", "Invalid artisan format",None, QApplication.UnicodeUTF8))

            message =  QApplication.translate("Message Area", "Background %1 loaded successfully %2",None, QApplication.UnicodeUTF8).arg(unicode(filename)).arg(unicode(self.qmc.stringfromseconds(self.qmc.timeB[self.qmc.timeindexB[6]])))
            self.sendmessage(message)

        except IOError,e:
            self.qmc.adderror(QApplication.translate("Error Message", "IO Error: loadbackground() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

        except ValueError,e:
            self.qmc.adderror(QApplication.translate("Error Message", "Value Error: loadbackground() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

        except Exception,e:
            self.qmc.adderror(QApplication.translate("Error Message", "Exception Error: loadbackground() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return
        
        finally:
            if f:
                f.close()
                
    def eventtime2string(self,time):
        if time == 0.0:
            return ""
        else:
            return "%02d:%02d"% divmod(time,60)
            
    #read Artisan CSV    
    def importCSV(self,filename):
        import csv
        csvFile = file(filename,"rb")
        data = csv.reader(csvFile,delimiter='\t')
        #read file header
        header = data.next()
        self.qmc.roastdate = QDate.fromString(header[0].split('Date:')[1],"dd'.'MM'.'yyyy")
        unit = header[1].split('Unit:')[1]
        #set temperature mode
        if unit == u"F" and self.qmc.mode == u"C":
            self.qmc.fahrenheitMode()
        if unit == u"C" and self.qmc.mode == u"F":
            self.qmc.celsiusMode()                        
        zero_t = 0
        #read column headers
        fields = data.next() 
        extra_fields = fields[5:] # colums after 'Event'
        # add devices if needed
        for i in range(max(0,(len(extra_fields) / 2) - len(aw.qmc.extradevices))):
            aw.addDevice()
        # set extra device names # NOTE: eventuelly we want to set/change the names only for devices that were just added in the line above!?
        for i in range(len(extra_fields)):
            if i % 2 == 1:
                # odd
                aw.qmc.extraname2[i/2 + 1] = extra_fields[i] 
            else:
                # even
                aw.qmc.extraname1[i/2] = extra_fields[i]
            
        #read data
        last_time = None
        for row in data:
            items = zip(fields, row)
            item = {}
            for (name, value) in items:
                item[name] = value.strip()
            #add one measurement
            timez = float(self.qmc.stringtoseconds(item['Time1']))
            if not last_time or last_time < timez:
                self.qmc.timex.append(timez)
                self.qmc.temp1.append(float(item['ET']))
                self.qmc.temp2.append(float(item['BT']))
                for j in range(len(extra_fields)):
                    if j % 2 == 1:
                        # odd
                        aw.qmc.extratemp2[j/2].append(float(item[extra_fields[j]]))
                    else:
                        # even
                        aw.qmc.extratimex[j/2].append(timez)
                        aw.qmc.extratemp1[j/2].append(float(item[extra_fields[j]]))
            last_time = timez
        csvFile.close()
        #swap temperature curves if needed such that BT is the lower and ET the upper one
        if len(self.qmc.temp2) > 0 and len(self.qmc.temp1) > 0 and (reduce (lambda x,y:x + y, self.qmc.temp2)) > reduce (lambda x,y:x + y, self.qmc.temp1):
            tmp = self.qmc.temp1
            self.qmc.temp1 = self.qmc.temp2
            self.qmc.temp2 = tmp                
        #set events
        CHARGE = aw.qmc.stringtoseconds(header[2].split('CHARGE:')[1])
        if CHARGE > 0:
            aw.qmc.timeindex[0] = self.time2index(CHARGE)
        DRYe = aw.qmc.stringtoseconds(header[4].split('DRYe:')[1])
        if DRYe > 0:
            aw.qmc.timeindex[1] = self.time2index(DRYe)
        FCs = aw.qmc.stringtoseconds(header[5].split('FCs:')[1])
        if FCs > 0:
            aw.qmc.timeindex[2] = self.time2index(FCs)
        FCe = aw.qmc.stringtoseconds(header[6].split('FCe:')[1])        
        if FCe > 0:
            aw.qmc.timeindex[3] = self.time2index(FCe)
        SCs = aw.qmc.stringtoseconds(header[7].split('SCs:')[1])
        if SCs > 0:
            aw.qmc.timeindex[4] = self.time2index(SCs)
        SCe = aw.qmc.stringtoseconds(header[8].split('SCe:')[1])
        if SCe> 0:
            aw.qmc.timeindex[5] = self.time2index(SCe) 
        DROP = aw.qmc.stringtoseconds(header[9].split('DROP:')[1])           
        if DROP > 0:
            aw.qmc.timeindex[6] = self.time2index(DROP)
        self.qmc.endofx = self.qmc.timex[-1]
        self.sendmessage(QApplication.translate("Message Area","HH506RA file loaded successfully", None, QApplication.UnicodeUTF8))
        self.qmc.redraw()
        
    def addDevice(self):
        aw.qmc.extradevices.append(1)
        aw.qmc.extradevicecolor1.append(u"black") #init color to black
        aw.qmc.extradevicecolor2.append(u"black")
        aw.qmc.extraname1.append("Extra 1")
        aw.qmc.extraname2.append("Extra 2")     
        aw.qmc.extramathexpression1.append(u"")
        aw.qmc.extramathexpression2.append(u"")
        
        #create new serial port (but don't open it yet). Store initial settings                                   
        self.extraser.append(serialport()) 
        self.extracomport.append("COM1")
        self.extrabaudrate.append(9600)
        self.extrabytesize.append(8)
        self.extraparity.append("E")
        self.extrastopbits.append(1)
        self.extratimeout.append(1)

    	#add new line variables
        aw.qmc.extratimex.append([])        
        aw.qmc.extratemp1.append([])
        aw.qmc.extratemp2.append([])

        #add two extra lines in figure for extra ET and extra BT
        l = len(aw.qmc.extradevices)-1  #new line index
        aw.qmc.extratemp1lines.append(aw.qmc.ax.plot(aw.qmc.extratimex[l], aw.qmc.extratemp1[l],color=aw.qmc.extradevicecolor1[l],linewidth=2,label= aw.qmc.extraname1[l])[0])
        aw.qmc.extratemp2lines.append(aw.qmc.ax.plot(aw.qmc.extratimex[l], aw.qmc.extratemp2[l],color=aw.qmc.extradevicecolor2[l],linewidth=2,label= aw.qmc.extraname2[l])[0])
            
    #Write readings to Artisan csv file
    def exportCSV(self,filename):
        if len(aw.qmc.timex) > 0:
            CHARGE = aw.qmc.timex[aw.qmc.timeindex[0]] 
            TP_index = self.findTP()
            TP = 0.
            if TP_index and TP_index < len(self.qmc.timex):
                TP = self.qmc.timex[TP_index]
            dryEndIndex = self.findDryEnd(TP_index)
            if self.qmc.timeindex[1]:
                #manual dryend available
                DRYe = self.qmc.timex[aw.qmc.timeindex[1]]
            else:
                #we use the dryEndIndex respecting the dry phase
                if dryEndIndex < len(self.qmc.timex):
                    DRYe = self.qmc.timex[dryEndIndex]
                else:
                    DRYe = 0.
            if self.qmc.timeindex[2]:
                FCs = self.qmc.timex[self.qmc.timeindex[2]]
            else:
                FCs = 0
            if self.qmc.timeindex[3]:
                FCe = self.qmc.timex[self.qmc.timeindex[3]]
            else:
                FCe = 0
            if self.qmc.timeindex[4]:
                SCs = self.qmc.timex[self.qmc.timeindex[4]]
            else:
                SCs = 0
            if self.qmc.timeindex[5]:
                SCe = self.qmc.timex[self.qmc.timeindex[5]]
            else:
                SCe = 0
            if self.qmc.timeindex[6]:
                DROP = self.qmc.timex[self.qmc.timeindex[6]]
            else:
                DROP = 0
            events = [     
                [CHARGE,"Charge",False],
                [TP,"TP",False],      
                [DRYe,"Dry End",False], 
                [FCs,"FCs",False],
                [FCe,"FCe",False],
                [SCs,"SCs",False],
                [SCe,"SCe",False],
                [DROP, "Drop",False],
                ]
                
            import csv
            csvFile= file(filename, "wb")
            writer= csv.writer(csvFile,delimiter='\t')
            writer.writerow([
                "Date:" + self.qmc.roastdate.toString("dd'.'MM'.'yyyy"),
                "Unit:" + self.qmc.mode,
                "CHARGE:" + self.eventtime2string(CHARGE),
                "TP:" + self.eventtime2string(TP),
                "DRYe:" + self.eventtime2string(DRYe),
                "FCs:" + self.eventtime2string(FCs),
                "FCe:" + self.eventtime2string(FCe),
                "SCs:" + self.eventtime2string(SCs),
                "SCe:" + self.eventtime2string(SCe),
                "DROP:" + self.eventtime2string(DROP)])     
            writer.writerow(['Time1','Time2','BT','ET','Event'] + reduce(lambda x,y: x + [unicode(y[0]),unicode(y[1])], zip(aw.qmc.extraname1[0:len(aw.qmc.extradevices)],aw.qmc.extraname2[0:len(aw.qmc.extradevices)]),[]))
                
            last_time = None
            for i in range(len(self.qmc.timex)):
                if CHARGE > 0. and self.qmc.timex[i] >= CHARGE:
                    time2 = "%02d:%02d"% divmod(self.qmc.timex[i] - CHARGE, 60)
                else:
                    time2 = "" 
                event = ""               
                for e in range(len(events)):
                    if not events[e][2] and int(round(self.qmc.timex[i])) == int(round(events[e][0])):
                        event = events[e][1]
                        events[e][2] = True
                        break
                time1 = "%02d:%02d"% divmod(self.qmc.timex[i],60)
                if not last_time or last_time != time1:
                    extratemps = []
                    for j in range(len(aw.qmc.extradevices)):
                        extratemps.append(aw.qmc.extratemp1[j][i])
                        extratemps.append(aw.qmc.extratemp2[j][i])
                    writer.writerow([time1,time2,self.qmc.temp2[i],self.qmc.temp1[i],event] + extratemps)
                last_time = time1
            csvFile.close()
            
                
    #Write object to file
    def serialize(self,filename,obj):
        f = codecs.open(unicode(filename), 'w+', encoding='utf-8')
        f.write(repr(obj))
        f.close()
    
    #Read object from file 
    def deserialize(self,filename):
        obj = None
        if os.path.exists(unicode(filename)):
            f = codecs.open(unicode(filename), 'r', encoding='utf-8')
            obj=eval(f.read())
            f.close()
        return obj

    #used by fileLoad()
    def setProfile(self,profile):
        old_mode = self.qmc.mode
        if "mode" in profile:
            self.qmc.mode = unicode(profile["mode"])
        #convert modes only if needed comparing the new uploaded mode to the old one.
        #otherwise it would incorrectly convert the uploaded phases
        if self.qmc.mode == u"F" and old_mode == "C":
            self.qmc.fahrenheitMode()
        if self.qmc.mode == u"C" and old_mode == "F":
            self.qmc.celsiusMode()
        if "flavors" in profile:
            self.qmc.flavors = [float(fl) for fl in profile["flavors"]]
            
        #if old format < 0.5.0 version  (identified by numbers less than 1.). convert
        if self.qmc.flavors[0] < 1. and self.qmc.flavors[-1] < 1.:
            l = len(self.qmc.flavors)
            for i in range(l):
                self.qmc.flavors[i] *= 10.
            self.qmc.flavors = self.qmc.flavors[:(l-1)]
            
        if "flavorlabels" in profile:
            self.qmc.flavorlabels = QStringList(profile["flavorlabels"])
        for i in range(len(self.qmc.flavorlabels)):
            self.qmc.flavorlabels[i] = unicode(self.qmc.flavorlabels[i])

        if "flavorstartangle" in profile:
            self.qmc.flavorstartangle = int(profile["flavorstartangle"])
            
        if "title" in profile:
            self.qmc.title = unicode(profile["title"])
        else:            
            self.qmc.title = u"Roaster Scope"
        if "beans" in profile:
            self.qmc.beans = unicode(profile["beans"])
        else:
            self.qmc.beans = u""
        if "weight" in profile:
            self.qmc.weight = profile["weight"]
        else:
            self.qmc.weight = [0,0,u"g"]
        if "volume" in profile:
            self.qmc.volume = profile["volume"]
        else:
            self.qmc.volume = [0,0,u"l"]
        if "density" in profile:
            self.qmc.density = profile["density"]
        else:
            self.qmc.density = [0,u"g",0,u"l"]
        if "roastertype" in profile:
            self.qmc.roastertype = unicode(profile["roastertype"])
        else:
            self.qmc.roastertype = u""
        if "operator" in profile:
            self.qmc.operator = unicode(profile["operator"])
        else:
            self.qmc.operator = u""
        if "roastdate" in profile:
            self.qmc.roastdate = QDate.fromString(profile["roastdate"])
        if "specialevents" in profile:
            self.qmc.specialevents = profile["specialevents"]
        else:
            self.qmc.specialevents = []
        if "specialeventstype" in profile:
            self.qmc.specialeventstype = profile["specialeventstype"]
        else:  
            self.qmc.specialeventstype = []
        if "specialeventsvalue" in profile:
            self.qmc.specialeventsvalue = profile["specialeventsvalue"]
        else:
            self.qmc.specialeventsvalue = []          
        if "specialeventsStrings" in profile:
            self.qmc.specialeventsStrings = profile["specialeventsStrings"]
        else:
            self.qmc.specialeventsStrings = []
        if "etypes" in profile:
            self.qmc.etypes = profile["etypes"]
            
        if "roastingnotes" in profile:
            self.qmc.roastingnotes = unicode(profile["roastingnotes"])
        else:
            self.qmc.roastingnotes = u""
        if "cuppingnotes" in profile:
            self.qmc.cuppingnotes = unicode(profile["cuppingnotes"])
        else:
            self.qmc.cuppingnotes = u""
        if "timex" in profile:
            self.qmc.timex = profile["timex"]
        if "temp1" in profile:
            self.qmc.temp1 = profile["temp1"]
        if "temp2" in profile:
            self.qmc.temp2 = profile["temp2"]
        if "phases" in profile:
            self.qmc.phases = profile["phases"]
        if "ymax" in profile:
            self.qmc.ylimit = int(profile["ymax"])
        if "xmin" in profile:
            self.qmc.startofx = int(profile["xmin"])
        if "xmax" in profile:
            self.qmc.endofx = int(profile["xmax"])
        else:
            #Set the xlimits
            if self.qmc.timex:
                self.qmc.endofx = self.qmc.timex[-1] + 40         
        if "ambientTemp" in profile:
            self.qmc.ambientTemp = profile["ambientTemp"]

        if "bag_humidity" in profile:
            self.qmc.bag_humidity = profile["bag_humidity"]   
        else:
            self.qmc.bag_humidity = [0.,0.]
        #extra devices    
        if "extratimex" in profile:   
            self.qmc.extratimex = profile["extratimex"]     
            if "extratemp1" in profile:       
                self.qmc.extratemp1 = profile["extratemp1"]
            if "extratemp2" in profile:
                self.qmc.extratemp2 = profile["extratemp2"]
            if "extradevices" in profile:
                self.qmc.extradevices = profile["extradevices"]
            if "extraname1" in profile:
                self.qmc.extraname1 = profile["extraname1"]
            if "extraname2" in profile:
                self.qmc.extraname2 = profile["extraname2"]
            if "extramathexpression1" in profile:
                self.qmc.extramathexpression1 = profile["extramathexpression1"]
            if "extramathexpression2" in profile:
                self.qmc.extramathexpression2 = profile["extramathexpression2"]
            if "extradevicecolor1" in profile:
                self.qmc.extradevicecolor1 = profile["extradevicecolor1"]
            if "extradevicecolor2" in profile:
                self.qmc.extradevicecolor2 = profile["extradevicecolor2"]
            
        if "timeindex" in profile:
            self.qmc.timeindex = profile["timeindex"]
        else:
            ###########      OLD PROFILE FORMAT
            if "startend" in profile:
                startend = [float(fl) for fl in profile["startend"]]  
            else:
                startend = [0.,0.,0.,0.]
            if "dryend" in profile:
                dryend = profile["dryend"]
            else:
                dryend = [0.,0.]
            if "cracks" in profile:
                varC = [float(fl) for fl in profile["cracks"]]
            else:
                varC = [0.,0.,0.,0.,0.,0.,0.,0.]
            times = []
            times.append(startend[0])
            times.append(dryend[0])
            times.append(varC[0])
            times.append(varC[2])
            times.append(varC[4])
            times.append(varC[6])
            times.append(startend[2])
            #convert to new profile
            self.qmc.timeindexupdate(times)
            
    #used by filesave()
    #wrap values in unicode(.) if and only if those are of type string
    def getProfile(self):
        profile = {}
        profile["mode"] = self.qmc.mode
        profile["timeindex"] = self.qmc.timeindex
        profile["flavors"] = self.qmc.flavors
        profile["flavorlabels"] = [unicode(fl) for fl in self.qmc.flavorlabels]
        profile["flavorstartangle"] = self.qmc.flavorstartangle
        profile["title"] = unicode(self.qmc.title)
        profile["beans"] = unicode(self.qmc.beans)
        profile["weight"] = self.qmc.weight
        profile["volume"] = self.qmc.volume
        profile["density"] = self.qmc.density
        profile["roastertype"] = unicode(self.qmc.roastertype)
        profile["operator"] = unicode(self.qmc.operator)
        profile["roastdate"] = unicode(self.qmc.roastdate.toString())
        profile["specialevents"] = self.qmc.specialevents
        profile["specialeventstype"] = self.qmc.specialeventstype
        profile["specialeventsvalue"] = self.qmc.specialeventsvalue
        profile["specialeventsStrings"] = [unicode(ses) for ses in self.qmc.specialeventsStrings]
        profile["etypes"] = [unicode(et) for et in self.qmc.etypes]
        profile["roastingnotes"] = unicode(self.qmc.roastingnotes)
        profile["cuppingnotes"] = unicode(self.qmc.cuppingnotes)
        profile["timex"] = self.qmc.timex
        profile["temp1"] = self.qmc.temp1
        profile["temp2"] = self.qmc.temp2
        profile["phases"] = self.qmc.phases        
        profile["ymax"] = self.qmc.ylimit
        profile["xmin"] = self.qmc.startofx
        profile["xmax"] = self.qmc.endofx       
        profile["ambientTemp"] = self.qmc.ambientTemp
        profile["bag_humidity"] = self.qmc.bag_humidity
        profile["extradevices"] = self.qmc.extradevices
        profile["extraname1"] = self.qmc.extraname1        
        profile["extraname2"] = self.qmc.extraname2 
        profile["extramathexpression1"] = self.qmc.extramathexpression1
        profile["extramathexpression2"] = self.qmc.extramathexpression2        
        profile["extratimex"] = self.qmc.extratimex
        profile["extratemp1"] = self.qmc.extratemp1
        profile["extratemp2"] = self.qmc.extratemp2
        profile["extradevicecolor1"] = self.qmc.extradevicecolor1
        profile["extradevicecolor2"] = self.qmc.extradevicecolor2
        
        return profile
    
    #saves recorded profile in hard drive. Called from file menu 
    def fileSave(self,fname):
        try:         
            filename = fname
            if not filename:
                 filename = self.ArtisanSaveFileDialog(msg=QApplication.translate("MessageBox Caption", "Save Profile",None, QApplication.UnicodeUTF8)) 
            if filename:
                #write
                self.serialize(filename,self.getProfile())
                self.setCurrentFile(filename)
                self.sendmessage(QApplication.translate("Message Area","Profile saved", None, QApplication.UnicodeUTF8))

                self.qmc.safesaveflag = False
            else:
                self.sendmessage(QApplication.translate("Message Area","Cancelled", None, QApplication.UnicodeUTF8))
        except IOError,e:
            self.qmc.adderror(QApplication.translate("Error Message", "IO Error on filesave(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return
            
    def fileExport(self):
        try:         
            filename = aw.ArtisanSaveFileDialog(msg=QApplication.translate("MessageBox Caption", "Export CSV",None, QApplication.UnicodeUTF8),ext="*.csv")
            if filename:
                self.exportCSV(filename)
                self.sendmessage(QApplication.translate("Message Area","Readings exported", None, QApplication.UnicodeUTF8))
            else:
                self.sendmessage(QApplication.translate("Message Area","Cancelled", None, QApplication.UnicodeUTF8))
        except IOError,e:
            self.qmc.adderror(QApplication.translate("Error Message", "IO Error on fileExport(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return
            
    def fileImport(self):
        try:         
            filename = aw.ArtisanOpenFileDialog(msg=QApplication.translate("MessageBox Caption", "Import CSV",None, QApplication.UnicodeUTF8))
            if filename:
                self.importCSV(filename)
                self.sendmessage(QApplication.translate("Message Area","Readings imported", None, QApplication.UnicodeUTF8))
            else:
                self.sendmessage(QApplication.translate("Message Area","Cancelled", None, QApplication.UnicodeUTF8))
        except IOError,e:
            self.qmc.adderror(QApplication.translate("Error Message", "IO Error on fileImport(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))        
            return

    #loads the settings at the start of application. See the oppposite closeEvent()
    def settingsLoad(self):
        try: 
            settings = QSettings()
            if settings.contains("resetqsettings"):
                self.resetqsettings = settings.value("resetqsettings",self.resetqsettings).toInt()[0]
                if self.resetqsettings:
                    self.resetqsettings = 0
                    self.qmc.redraw()
                    return  #don't load any more settings. They could be bad (corrupted). Stop here.
                
            #restore geometry
            self.restoreGeometry(settings.value("Geometry").toByteArray())
            #restore mode
            old_mode = self.qmc.mode
            self.qmc.mode = unicode(settings.value("Mode",self.qmc.mode).toString())
            #convert modes only if needed comparing the new uploaded mode to the old one.
            #otherwise it would incorrectly convert the uploaded phases
            if self.qmc.mode == u"F" and old_mode == "C":
                    self.qmc.fahrenheitMode()
            if self.qmc.mode == u"C" and old_mode == "F":
                self.qmc.celsiusMode()

            #restore device
            settings.beginGroup("Device")
            self.qmc.device = settings.value("id",self.qmc.device).toInt()[0]
            
            #only leave operational the control button if the device is Fuji PID
            #the SV buttons are activated from the PID control panel 
            if self.qmc.device == 0:
                self.button_10.setVisible(True)
                self.label6.setVisible(True)
                self.lcd6.setVisible(True)
                self.label7.setVisible(True)
                self.lcd7.setVisible(True)
            
            if settings.contains("controlETpid"):
                self.ser.controlETpid = map(lambda x:x.toInt()[0],settings.value("controlETpid").toList())
            if settings.contains("readBTpid"):
                self.ser.readBTpid = map(lambda x:x.toInt()[0],settings.value("readBTpid").toList())
            if settings.contains("arduinoETChannel"):
                self.ser.arduinoETChannel = settings.value("arduinoETChannel").toString()[0]
            if settings.contains("arduinoBTChannel"):
                self.ser.arduinoBTChannel = settings.value("arduinoBTChannel").toString()[0]
            settings.endGroup()

            #restore phases
            if settings.contains("Phases"):
                self.qmc.phases = map(lambda x:x.toInt()[0],settings.value("Phases").toList())
            if settings.contains("phasesbuttonflag"):
                self.qmc.phasesbuttonflag = settings.value("phasesbuttonflag",self.qmc.phasesbuttonflag).toInt()[0]   
            #restore Events settings
            settings.beginGroup("events")
            self.eventsbuttonflag = settings.value("eventsbuttonflag",int(self.eventsbuttonflag)).toInt()[0]
            self.minieventsflag = settings.value("minieventsflag",int(self.minieventsflag)).toInt()[0]
            self.qmc.eventsGraphflag = settings.value("eventsGraphflag",int(self.qmc.eventsGraphflag)).toInt()[0]
            if settings.contains("etypes"):
                self.qmc.etypes = settings.value("etypes",self.qmc.etypes).toStringList()
            if settings.contains("eventsshowflag"):
                aw.qmc.eventsshowflag  = settings.value("eventsshowflag",int(self.qmc.eventsshowflag)).toInt()[0]
            settings.endGroup()
            
    	    #restore statistics
            if settings.contains("Statistics"):
                self.qmc.statisticsflags = map(lambda x:x.toInt()[0],settings.value("Statistics").toList())
            if settings.contains("StatisticsConds"):
                self.qmc.statisticsconditions = map(lambda x:x.toInt()[0],settings.value("StatisticsConds").toList())

            #restore delay
            self.qmc.delay = settings.value("Delay",int(self.qmc.delay)).toInt()[0]
            #restore colors
            for (k, v) in settings.value("Colors").toMap().items():
                self.qmc.palette[unicode(k)] = unicode(v.toString())
                
            if settings.contains("LCDColors"):
                for (k, v) in settings.value("LCDColors").toMap().items():
                    self.lcdpaletteB[unicode(k)] = unicode(v.toString())
            if settings.contains("LEDColors"):
                for (k, v) in settings.value("LEDColors").toMap().items():
                    self.lcdpaletteF[unicode(k)] = unicode(v.toString())

            #restore flavors
            self.qmc.flavorlabels = settings.value("Flavors",self.qmc.flavorlabels).toStringList()
            self.qmc.flavors = [5.]*len(self.qmc.flavorlabels)
            if settings.contains("flavorstartangle"): 
                self.qmc.flavorstartangle = settings.value("flavorstartangle",int(self.qmc.flavorstartangle)).toInt()[0]
            
            #restore serial port     
            settings.beginGroup("SerialPort")
            self.ser.comport = unicode(settings.value("comport",self.ser.comport).toString())
            self.ser.baudrate = settings.value("baudrate",int(self.ser.baudrate)).toInt()[0]
            self.ser.bytesize = settings.value("bytesize",self.ser.bytesize).toInt()[0]       
            self.ser.stopbits = settings.value("stopbits",self.ser.stopbits).toInt()[0]
            self.ser.parity = unicode(settings.value("parity",self.ser.parity).toString())
            self.ser.timeout = settings.value("timeout",self.ser.timeout).toInt()[0]
            settings.endGroup()
            
            #restore alarms
            settings.beginGroup("Alarms")
            if settings.contains("alarmtime"):
                self.qmc.alarmtime = map(lambda x:x.toInt()[0],settings.value("alarmtime").toList())                                                    
                self.qmc.alarmflag = map(lambda x:x.toInt()[0],settings.value("alarmflag").toList())
                self.qmc.alarmsource = map(lambda x:x.toInt()[0],settings.value("alarmsource").toList())
                self.qmc.alarmtemperature = map(lambda x:x.toInt()[0],settings.value("alarmtemperature").toList())
                self.qmc.alarmaction = map(lambda x:x.toInt()[0],settings.value("alarmaction").toList())
                self.qmc.alarmstrings = list(settings.value("alarmstrings",self.qmc.alarmstrings).toStringList())
                self.qmc.alarmstate = [0]*len(self.qmc.alarmflag)
            settings.endGroup()

            #restore pid settings
            settings.beginGroup("PXR")
            for key in self.pid.PXR.keys():
                if type(self.pid.PXR[key][0]) == type(float()):
                    self.pid.PXR[key][0] = settings.value(key,self.pid.PXR[key]).toDouble()[0]
                elif type(self.pid.PXR[key][0]) == type(int()):
                    self.pid.PXR[key][0] = settings.value(key,self.pid.PXR[key]).toInt()[0]
            settings.endGroup()
            settings.beginGroup("PXG4")
            for key in self.pid.PXG4.keys():
                if type(self.pid.PXG4[key][0]) == type(float()):
                    self.pid.PXG4[key][0] = settings.value(key,self.pid.PXG4[key][0]).toDouble()[0]
                elif type(self.pid.PXG4[key][0]) == type(int()):
                    self.pid.PXG4[key][0] = settings.value(key,self.pid.PXG4[key][0]).toInt()[0]
            settings.endGroup()
            settings.beginGroup("RoC")
            self.qmc.DeltaETflag = settings.value("DeltaET",self.qmc.DeltaETflag).toBool()
            self.qmc.DeltaBTflag = settings.value("DeltaBT",self.qmc.DeltaBTflag).toBool()
            self.qmc.deltafilter = settings.value("deltafilter",self.qmc.deltafilter).toInt()[0]
            self.qmc.sensitivity = settings.value("Sensitivity",self.qmc.sensitivity).toInt()[0]
            if self.qmc.sensitivity > 10: self.qmc.sensitivity = 10
            
            settings.endGroup()
            settings.beginGroup("HUD")
            self.qmc.projectFlag = settings.value("Projection",self.qmc.projectFlag).toBool()
            self.qmc.projectionmode = settings.value("ProjectionMode",self.qmc.projectionmode).toInt()[0]
            self.qmc.ETtarget = settings.value("ETtarget",self.qmc.ETtarget).toInt()[0]
            self.qmc.BTtarget = settings.value("BTtarget",self.qmc.BTtarget).toInt()[0]            
            self.HUDfunction = settings.value("Mode",self.HUDfunction).toInt()[0]
            if settings.contains("hudETpid"):
                self.qmc.hudETpid = map(lambda x:x.toInt()[0],settings.value("hudETpid").toList())
            settings.endGroup()
            settings.beginGroup("Sound")
            self.soundflag = settings.value("Beep",self.soundflag).toInt()[0]
            settings.endGroup()
            #saves max-min temp limits of graph
            settings.beginGroup("Axis")
            self.qmc.startofx = settings.value("xmin",self.qmc.startofx).toInt()[0]
            self.qmc.endofx = settings.value("xmax",self.qmc.endofx).toInt()[0]
            #fixes Windows OS sometimes saving endofx as 0 
            if self.qmc.endofx < 60 or self.qmc.endofx > 1800:
                self.qmc.enofx = 60
            self.qmc.ylimit_min = settings.value("ymin",self.qmc.ylimit_min).toInt()[0]            
            self.qmc.ylimit = settings.value("ymax",self.qmc.ylimit).toInt()[0]
            self.qmc.keeptimeflag = settings.value("keepTimeLimit",self.qmc.keeptimeflag).toInt()[0]
            self.qmc.legendloc = settings.value("legendloc",self.qmc.legendloc).toInt()[0]
            settings.endGroup()
            settings.beginGroup("RoastProperties")
            self.qmc.operator = unicode(settings.value("operator",self.qmc.operator).toString())
            self.qmc.roastertype = unicode(settings.value("roastertype",self.qmc.roastertype).toString())
            self.qmc.density[2] = settings.value("densitySampleVolume",self.qmc.density[2]).toInt()[0]
            self.qmc.density[3] = unicode(settings.value("densitySampleVolumeUnit",self.qmc.density[3]).toString())
            settings.endGroup()
            self.userprofilepath = unicode(settings.value("profilepath",self.userprofilepath).toString())
 
            settings.beginGroup("ExtraDev")
            if settings.contains("extradevices"):
                self.qmc.extradevices = map(lambda x:x.toInt()[0],settings.value("extradevices").toList())
                self.qmc.extraname1 = list(settings.value("extraname1",self.qmc.extraname1).toStringList())
                self.qmc.extraname2 = list(settings.value("extraname2",self.qmc.extraname2).toStringList())
                self.qmc.extramathexpression1 = list(settings.value("extramathexpression1",self.qmc.extramathexpression1).toStringList())
                self.qmc.extramathexpression2 = list(settings.value("extramathexpression2",self.qmc.extramathexpression2).toStringList())
                self.qmc.extradevicecolor1 = list(settings.value("extradevicecolor1",self.qmc.extradevicecolor1).toStringList())
                self.qmc.extradevicecolor2 = list(settings.value("extradevicecolor2",self.qmc.extradevicecolor2).toStringList())
                #convert Qstrings to unicode
                for i in range(len(self.qmc.extradevicecolor1)):
                    self.qmc.extraname1[i] = unicode(self.qmc.extraname1[i])
                    self.qmc.extraname2[i] = unicode(self.qmc.extraname2[i])
                    self.qmc.extramathexpression1[i] = unicode(self.qmc.extramathexpression1[i])
                    self.qmc.extramathexpression2[i] = unicode(self.qmc.extramathexpression2[i])
                    self.qmc.extradevicecolor1[i] = unicode(self.qmc.extradevicecolor1[i])
                    self.qmc.extradevicecolor2[i] = unicode(self.qmc.extradevicecolor2[i])                    
            
            #create empty containers
            for i in range(len(self.qmc.extradevices)):
                self.qmc.extratemp1.append([])
                self.qmc.extratemp2.append([])
                self.qmc.extratimex.append([])
                #init empty lines
                self.qmc.extratemp1lines.append(self.qmc.ax.plot(self.qmc.extratimex[i], self.qmc.extratemp1[i],color="black",linewidth=2,label= self.qmc.extraname1[i])[0])
                self.qmc.extratemp2lines.append(self.qmc.ax.plot(self.qmc.extratimex[i], self.qmc.extratemp2[i],color="black",linewidth=2,label= self.qmc.extraname1[i])[0])
            settings.endGroup()

            # Extra com ports
            settings.beginGroup("ExtraComm")
            if settings.contains("extracomport"):
                self.extracomport = list(settings.value("extracomport",self.extracomport).toStringList())
                self.extrabaudrate = map(lambda x:x.toInt()[0],settings.value("extrabaudrate").toList())
                self.extrabytesize = map(lambda x:x.toInt()[0],settings.value("extrabytesize").toList())
                self.extraparity = list(settings.value("extraparity",self.extraparity).toStringList())
                self.extrastopbits = map(lambda x:x.toInt()[0],settings.value("extrastopbits").toList())
                self.extratimeout = map(lambda x:x.toInt()[0],settings.value("extratimeout").toList())
                #convert Qstrings to unicode                
                for i in range(len(self.extracomport)):                
                    self.extracomport[i] = unicode(self.extracomport[i])
                    self.extraparity[i] = unicode(self.extraparity[i])
                    #create serial port objects
                    self.extraser.append(serialport())                    
                #configure extra com ports 
                for i in range(len(aw.extraser)):
                    aw.extraser[i].comport = unicode(aw.extracomport[i])
                    aw.extraser[i].baudrate = aw.extrabaudrate[i]
                    aw.extraser[i].bytesize = aw.extrabytesize[i]
                    aw.extraser[i].parity = unicode(aw.extraparity[i])
                    aw.extraser[i].stopbits = aw.extrastopbits[i]
                    aw.extraser[i].timeout = aw.extratimeout[i]
            settings.endGroup()

            if settings.contains("BTfunction"):
                self.qmc.BTfunction = unicode(settings.value("BTfunction",self.qmc.BTfunction).toString())
                self.qmc.ETfunction = unicode(settings.value("ETfunction",self.qmc.ETfunction).toString())

            if settings.contains("plotcurves"):
                self.qmc.plotcurves = list(settings.value("plotcurves",self.qmc.plotcurves).toStringList())
                self.qmc.plotcurvecolor = list(settings.value("plotcurvecolor",self.qmc.plotcurvecolor).toStringList())
                for i in range(len(self.qmc.plotcurves)):
                    self.qmc.plotcurves[i] = unicode(self.qmc.plotcurves[i])
                    self.qmc.plotcurvecolor[i] = unicode(self.qmc.plotcurvecolor[i])

            settings.beginGroup("ExtraEventButtons")                    
            if settings.contains("extraeventsactions"):
                self.extraeventstypes = map(lambda x:x.toInt()[0],settings.value("extraeventstypes").toList())
                self.extraeventsvalues = map(lambda x:x.toInt()[0],settings.value("extraeventsvalues").toList())
                self.extraeventsactions = map(lambda x:x.toInt()[0],settings.value("extraeventsactions").toList())
                self.extraeventsvisibility = map(lambda x:x.toInt()[0],settings.value("extraeventsvisibility").toList())
                self.extraeventsactionstrings = list(settings.value("extraeventsactionstrings",self.extraeventsactionstrings).toStringList())
                self.extraeventslabels = list(settings.value("extraeventslabels",self.extraeventslabels).toStringList())
                self.extraeventsdescriptions= list(settings.value("extraeventsdescriptions",self.extraeventsdescriptions).toStringList())
                
                for i in range(len(self.extraeventsactionstrings)):
                    self.extraeventsactionstrings[i] = unicode(self.extraeventsactionstrings[i])
                    self.extraeventslabels[i] = unicode(self.extraeventslabels[i])
                    self.extraeventsdescriptions[i] = unicode(self.extraeventsdescriptions[i])
                #create buttons                    
                for i in range(len(self.extraeventstypes)):
                    self.buttonlist.append(QPushButton())
                    self.buttonlist[i].setFocusPolicy(Qt.NoFocus)
                    self.buttonlist[i].setStyleSheet(self.pushbuttonstyles["EVENT"]) 
                    self.buttonlist[i].setMinimumHeight(50)
                    self.buttonlist[i].setText(self.extraeventslabels[i])
                    self.connect(self.buttonlist[i], SIGNAL("clicked()"), lambda ee=i:self.recordextraevent(ee))
                    self.lowerbuttondialog.addButton(self.buttonlist[i],QDialogButtonBox.ActionRole)
                self.update_extraeventbuttons_visibility()
            settings.endGroup()
            
            settings.beginGroup("grid")             
            if settings.contains("xgrid"):
                self.qmc.xgrid = settings.value("xgrid",self.qmc.xgrid).toInt()[0]
                self.qmc.ygrid = settings.value("ygrid",self.qmc.ygrid).toInt()[0]
                self.qmc.gridthickness = settings.value("gridthickness",self.qmc.gridthickness).toInt()[0]
                self.qmc.xrotation = settings.value("xrotation",self.qmc.xrotation).toInt()[0]
                self.qmc.gridlinestyle = settings.value("gridlinestyle",self.qmc.gridlinestyle).toInt()[0]
                self.qmc.gridalpha = settings.value("gridalpha",self.qmc.gridalpha).toDouble()[0]
            settings.endGroup()

            if settings.contains("roastpropertiesflag"):            	
            	self.qmc.roastpropertiesflag = settings.value("roastpropertiesflag",self.qmc.roastpropertiesflag).toInt()[0]


            # set visibility of mini event line
            self.update_minieventline_visibility()

            #update visibility of main event button
            if self.eventsbuttonflag:
                self.button_11.setVisible(True)
            else:
                self.button_11.setVisible(False)

            
            #update display
            self.qmc.redraw()

        except Exception,e:
            QMessageBox.information(self,QApplication.translate("Error Message", "Exception: settingsLoad()",None, QApplication.UnicodeUTF8),unicode(e))
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
            previous_mode = unicode(settings.value("Mode",self.qmc.mode).toString())
            settings.setValue("Mode",self.qmc.mode)
            #save device
            settings.beginGroup("Device")
            settings.setValue("id",self.qmc.device)
            settings.setValue("controlETpid",self.ser.controlETpid)
            settings.setValue("readBTpid",self.ser.readBTpid)
            settings.setValue("arduinoETChannel",self.ser.arduinoETChannel)
            settings.setValue("arduinoBTChannel",self.ser.arduinoBTChannel)
            settings.endGroup()
            #save of phases is done in the phases dialog
            #only if mode was changed (and therefore the phases values have been converted)
            #we update the defaults here
            if previous_mode != self.qmc.mode:
                #save phases
                settings.setValue("Phases",aw.qmc.phases)            
            #save phasesbuttonflag
            settings.setValue("phasesbuttonflag",self.qmc.phasesbuttonflag)
            #save statistics
            settings.setValue("Statistics",self.qmc.statisticsflags)
            settings.setValue("StatisticsConds",self.qmc.statisticsconditions)
            #save Events settings
            settings.beginGroup("events")
            settings.setValue("eventsbuttonflag",self.eventsbuttonflag)
            settings.setValue("minieventsflag",self.minieventsflag)
            settings.setValue("eventsGraphflag",self.qmc.eventsGraphflag)
            settings.setValue("etypes",self.qmc.etypes)
            settings.setValue("eventsshowflag",aw.qmc.eventsshowflag)
            settings.endGroup()            
            #save delay
            settings.setValue("Delay",self.qmc.delay)
            #save colors
            settings.setValue("Colors",self.qmc.palette)
            settings.setValue("LCDColors",self.lcdpaletteB)
            settings.setValue("LEDColors",self.lcdpaletteF)            
            #save flavors
            settings.setValue("Flavors",self.qmc.flavorlabels)
            settings.setValue("flavorstartangle",self.qmc.flavorstartangle)
            #soundflag
            settings.setValue("sound",self.soundflag)
            #save serial port
            settings.beginGroup("SerialPort")
            settings.setValue("comport",self.ser.comport)
            settings.setValue("baudrate",self.ser.baudrate)
            settings.setValue("bytesize",self.ser.bytesize)
            settings.setValue("stopbits",self.ser.stopbits)
            settings.setValue("parity",self.ser.parity)
            settings.setValue("timeout",self.ser.timeout)            
            settings.endGroup()
            #save pid settings (only key and value[0])
            settings.beginGroup("PXR")
            for key in self.pid.PXR.keys():
                settings.setValue(key,self.pid.PXR[key][0])
            settings.endGroup()
            settings.beginGroup("PXG4")
            for key in self.pid.PXG4.keys():            
                settings.setValue(key,self.pid.PXG4[key][0])
            settings.endGroup()
            settings.beginGroup("RoC")
            settings.setValue("DeltaET",self.qmc.DeltaETflag)
            settings.setValue("DeltaBT",self.qmc.DeltaBTflag)
            settings.setValue("Sensitivity",self.qmc.sensitivity)
            settings.setValue("deltafilter",self.qmc.deltafilter)
            settings.endGroup()
            settings.beginGroup("HUD")
            settings.setValue("Projection",self.qmc.projectFlag)
            settings.setValue("ProjectionMode",self.qmc.projectionmode)
            settings.setValue("ETtarget",self.qmc.ETtarget)
            settings.setValue("BTtarget",self.qmc.BTtarget)
            settings.setValue("Mode",self.HUDfunction)
            settings.setValue("hudETpid",self.qmc.hudETpid)
            settings.endGroup()
            settings.beginGroup("Sound")
            settings.setValue("Beep",self.soundflag)
            settings.endGroup()
            settings.beginGroup("Axis")
            settings.setValue("xmin",self.qmc.startofx)
            settings.setValue("xmax",self.qmc.endofx)
            settings.setValue("ymax",self.qmc.ylimit)
            settings.setValue("ymin",self.qmc.ylimit_min)
            settings.setValue("keepTimeLimit",self.qmc.keeptimeflag)
            settings.setValue("legendloc",self.qmc.legendloc )
            settings.endGroup()
            settings.beginGroup("RoastProperties")
            settings.setValue("operator",self.qmc.operator)
            settings.setValue("roastertype",self.qmc.roastertype)
            settings.setValue("densitySampleVolume",self.qmc.density[2])
            settings.setValue("densitySampleVolumeUnit",self.qmc.density[3])
            settings.endGroup()
            #save alarms
            settings.beginGroup("Alarms")
            settings.setValue("alarmtime",self.qmc.alarmtime)                                                                
            settings.setValue("alarmflag",self.qmc.alarmflag)            
            settings.setValue("alarmsource",self.qmc.alarmsource)
            settings.setValue("alarmtemperature",self.qmc.alarmtemperature)
            settings.setValue("alarmaction",self.qmc.alarmaction)
            settings.setValue("alarmstrings",self.qmc.alarmstrings)
            settings.endGroup()
            settings.setValue("profilepath",self.userprofilepath)
            #save extra devices
            settings.beginGroup("ExtraDev")
            settings.setValue("extradevices",self.qmc.extradevices)                
            settings.setValue("extradevicecolor1",self.qmc.extradevicecolor1)                                                                
            settings.setValue("extradevicecolor2",self.qmc.extradevicecolor2)
            settings.setValue("extraname1",self.qmc.extraname1)
            settings.setValue("extraname2",self.qmc.extraname2)
            settings.setValue("extramathexpression1",self.qmc.extramathexpression1)
            settings.setValue("extramathexpression2",self.qmc.extramathexpression2)
            settings.endGroup()
            #save extra serial comm ports settings
            settings.beginGroup("ExtraComm")
            settings.setValue("extracomport",self.extracomport)                                                                
            settings.setValue("extrabaudrate",self.extrabaudrate)                                                                
            settings.setValue("extrabytesize",self.extrabytesize)                                                                
            settings.setValue("extraparity",self.extraparity)                                                                
            settings.setValue("extrastopbits",self.extrastopbits)                                                                
            settings.setValue("extratimeout",self.extratimeout)
            settings.endGroup()
            settings.setValue("BTfunction",self.qmc.BTfunction)                                                                
            settings.setValue("ETfunction",self.qmc.ETfunction)                                                                

            settings.setValue("resetqsettings",self.resetqsettings)

            settings.setValue("plotcurves",self.qmc.plotcurves)                                                                
            settings.setValue("plotcurvecolor",self.qmc.plotcurvecolor)
            
            #custom event buttons
            settings.beginGroup("ExtraEventButtons")
            settings.setValue("extraeventstypes",self.extraeventstypes)
            settings.setValue("extraeventsvalues",self.extraeventsvalues)
            settings.setValue("extraeventsactionstrings",self.extraeventsactionstrings)
            settings.setValue("extraeventsactions",self.extraeventsactions)
            settings.setValue("extraeventsdescriptions",self.extraeventsdescriptions)
            settings.setValue("extraeventsvisibility",self.extraeventsvisibility)
            settings.setValue("extraeventslabels",self.extraeventslabels)
            settings.endGroup()
            
            settings.beginGroup("grid")
            settings.setValue("xgrid",self.qmc.xgrid)
            settings.setValue("ygrid",self.qmc.ygrid)
            settings.setValue("gridlinestyle",self.qmc.gridlinestyle)
            settings.setValue("gridthickness",self.qmc.gridthickness)
            settings.setValue("gridalpha",self.qmc.gridalpha)
            settings.setValue("xrotation",self.qmc.xrotation)
            settings.endGroup()

            settings.setValue("roastpropertiesflag",self.qmc.roastpropertiesflag)
         
           
        except Exception,e:
            self.qmc.adderror(QApplication.translate("Error Message", "Exception: closeEvent() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))            

    def filePrint(self):

        tempFile = tempfile.TemporaryFile()
        aw.qmc.fig.savefig(tempFile.name)
        image = QImage(tempFile.name)
        
        if image.isNull():
            return
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
<title>""" + unicode(QApplication.translate("HTML Report Template", "Roasting Report", None, QApplication.UnicodeUTF8)) + """</title>
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
<th>""" + unicode(QApplication.translate("HTML Report Template", "Date:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$datetime</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "Beans:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$beans</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "Weight:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$weight</td>
</tr>
<tr>
<th></th>
<td>$degree</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "Volume:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$volume</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "Roaster:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$roaster</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "Operator:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$operator</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "Cupping:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$cup</td>
</tr>
</table>
</td>
<td>
<table width="180">
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "Charge:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$charge</td>
</tr>
<tr>
<th>TP:</th>
<td>$TP</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "DRY:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$DRY</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "FCs:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$FCs</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "FCe:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$FCe</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "SCs:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$SCs</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "SCe:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$SCe</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "Drop:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$drop</td>
</tr>
</table>
</td>
<td>
<table width="210">
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "Dry phase:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$dry_phase</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "Mid phase:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$mid_phase</td>
</tr>
<tr>
<th>""" + unicode(QApplication.translate("HTML Report Template", "Finish phase:", None, QApplication.UnicodeUTF8)) + """</th>
<td>$finish_phase</td>
</tr>
</table>
</td>
</tr>
</table>
</center>
</td>
<td>
<center><b>""" + unicode(QApplication.translate("HTML Report Template", "Roasting Notes", None, QApplication.UnicodeUTF8)) + """</b></center>
$roasting_notes
</td>
</tr>
<tr>
<td style="vertical-align:middle" align="center"><img alt='roast graph' width="650" src='$graph_image'/></td>
<td style="vertical-align:middle" align="center"><img alt='flavor graph' width="550" src='$flavor_image'/></td>
</tr>
<tr>
<td><center><b>""" + unicode(QApplication.translate("HTML Report Template", "Events", None, QApplication.UnicodeUTF8)) + """</b></center><br/>
$specialevents
</td>
<td><center><b>""" + unicode(QApplication.translate("HTML Report Template", "Cupping Notes", None, QApplication.UnicodeUTF8)) + """</b></center>
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
        charge = "--"
        if self.qmc.timeindex[0] != -1:
            charge = "BT " + "%.1f"%self.qmc.temp2[self.qmc.timeindex[0]] + "&deg;" + self.qmc.mode  + "<br/>ET " + "%.1f"%self.qmc.temp1[self.qmc.timeindex[0]] + "&deg;" + self.qmc.mode
        TP_index = self.findTP()
        TP_time_idx = None
        if TP_index > 0 and len(aw.qmc.timex) > 0:
            TP_time_idx = TP_index
        dryEndIndex = self.findDryEnd(TP_index)
        rates_of_changes = aw.RoR(TP_index,dryEndIndex)
        
        if self.qmc.timeindex[1]:
            #manual dryend available
            DRY_time_idx = self.qmc.timeindex[1]
        else:
            #we use the dryEndIndex respecting the dry phase
            if dryEndIndex < len(aw.qmc.timex):
                DRY_time_idx = dryEndIndex      
            else:
                DRY_time_idx = 0
        evaluations = aw.defect_estimation()        
        self.qmc.redraw()   
        if platf == u'Darwin':
            graph_image = "artisan-graph.svg"
            aw.qmc.fig.savefig(graph_image)
        else:
            #resize GRAPH image to 600 pixels width
            tempFile = tempfile.TemporaryFile()
            aw.qmc.fig.savefig(tempFile.name)
            image = QImage(tempFile.name)
            image = image.scaledToWidth(650,1)
            #save GRAPH image
            graph_image = "artisan-graph.png"
            image.save(graph_image)
        #obtain flavor chart image
        self.qmc.flavorchart()
        if platf == u'Darwin':
            flavor_image = "artisan-flavor.svg"
            aw.qmc.fig.savefig(flavor_image)
        else:
            #resize FLAVOR image to 400 pixels width
            tempFile = tempfile.TemporaryFile()
            aw.qmc.fig.savefig(tempFile.name)
            image = QImage(tempFile.name)
            image = image.scaledToWidth(550,1)
            #save GRAPH image
            flavor_image = "artisan-flavor.png"
            image.save(flavor_image)
        weight_loss = aw.weight_loss(self.qmc.weight[0],self.qmc.weight[1])
        volume_gain = aw.weight_loss(self.qmc.volume[1],self.qmc.volume[0])
        #return screen to GRAPH profile mode
        self.qmc.redraw()
        html = libstring.Template(HTML_REPORT_TEMPLATE).safe_substitute(
            title=cgi.escape(unicode(self.qmc.title)),
            datetime=unicode(self.qmc.roastdate.toString()), #alt: unicode(self.qmc.roastdate.toString('MM.dd.yyyy')),
            beans=beans,
            weight=self.volume_weight2html(self.qmc.weight[0],self.qmc.weight[2],weight_loss),
            degree=aw.roast_degree(weight_loss),
            volume=self.volume_weight2html(self.qmc.volume[0],self.qmc.volume[2],volume_gain),
            roaster=cgi.escape(self.qmc.roastertype),
            operator=cgi.escape(self.qmc.operator),
            cup=str(self.cuppingSum()),
            charge=charge,
            TP=self.event2html(TP_time_idx),
            DRY=self.event2html(DRY_time_idx),
            FCs=self.event2html(self.qmc.timeindex[2]),
            FCe=self.event2html(self.qmc.timeindex[3]),
            SCs=self.event2html(self.qmc.timeindex[4]),
            SCe=self.event2html(self.qmc.timeindex[5]),
            drop=self.event2html(self.qmc.timeindex[6]),
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
            QDesktopServices.openUrl(QUrl(u"file:///" + unicode(QDir().current().absolutePath()) + u"/Artisanreport.html", QUrl.TolerantMode))            
        except IOError,e:
            self.qmc.adderror(QApplication.translate("Error Message", "IO Error: htmlReport() %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return
        finally:
            if f:
                f.close()  
                
    def cuppingSum(self):
##        sum = 10 # includes the correction to have a maximum of 100
##        for i in range(len(self.qmc.flavors)):
##            sum += int(aw.qmc.flavors[i])
##        return sum
##        
        score = 0.
        nflavors = len(self.qmc.flavors)
        for i in range(nflavors):   
            score += self.qmc.flavors[i]
        score /= (nflavors)
        score *= 10.
        return score

    def volume_weight2html(self,amount,unit,change):
        if amount:
            return unicode(amount) + unit + " (" + "%.1f"%change + "%)"
        else:
            return "--"
                
    def phase2html(self,time,RoR,eval):
        if self.qmc.statisticstimes[0] > 0 and time and time > 0:
            return self.qmc.stringfromseconds(time) + " (%.2f" %(time*100./self.qmc.statisticstimes[0])+ "%)<br/>" + "%.1f deg/min"%RoR + "<br/>" + eval
        else:
            return "--"
            
    def event2html(self,time_idx):
        if time_idx:
            timez = self.qmc.timex[time_idx]
            temp = self.qmc.temp2[time_idx]
            if self.qmc.timeindex[0] != -1:
                start = self.qmc.timex[self.qmc.timeindex[0]]
            else:
                start = 0    
            return self.qmc.stringfromseconds(timez - start)+ " (%.1f"%temp + "&deg;" + self.qmc.mode + ")"
        else:
            return "--"
            
    def specialevents2html(self): 
        html = ""  
        if self.qmc.specialevents and len(self.qmc.specialevents) > 0:
            html += '<center>\n<table cellpadding="2">\n'
            if self.qmc.timeindex[0] != -1:
                start = self.qmc.timex[self.qmc.timeindex[0]]
            else:
                start = 0
            for i in range(len(self.qmc.specialevents)):
                html += ("<tr>"+
                     "\n<td>" + unicode(i+1) + "</td><td>[" +
                     self.qmc.stringfromseconds(int(self.qmc.timex[self.qmc.specialevents[i]] - start)) +
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
        
    # converts times (values of timex) to indices
    def time2index(self,time):
        for i in range(len(aw.qmc.timex)):
            if aw.qmc.timex[i] > time:
                return i
        return -1
        
    #returns the index of the lowest point in BT; return -1 if no such value found
    def findTP(self):  
        
        TP  = 1000
        idx = 0
        start = 0
        end = len(aw.qmc.timex)
        # try to consider only indices until the roast end and not beyond
        EOR_index = end
        if aw.qmc.timeindex[6]:
            EOR_index = aw.qmc.timeindex[6]
        if EOR_index > start and EOR_index < end:
            end = EOR_index
        # try to consider only indices until FCs and not beyond
        FCs_index = end
        if aw.qmc.timeindex[2]:
            FCs_index = aw.qmc.timeindex[2]
        if FCs_index > start and FCs_index < end:
            end = FCs_index
        # try to consider only indices from start of roast on and not before
        SOR_index = start
        if aw.qmc.timeindex[0] != -1:
            SOR_index = aw.qmc.timeindex[0] 
        if SOR_index > start and SOR_index < end:
            start = SOR_index
        for i in range(end - 1, start -1, -1):
            if aw.qmc.temp2[i] < TP:
                TP = aw.qmc.temp2[i]
                idx = i
        return idx
        
    
    def defect_estimation_phase(self,phase_length,lower_limit,upper_limit,short_taste,optimal_taste,long_taste):
        result = optimal_taste
        third_of_optimal_phase = (upper_limit - lower_limit) / 3.0
        if phase_length < lower_limit:
            result = short_taste
        elif phase_length > upper_limit:
            result = long_taste
        elif phase_length < lower_limit + third_of_optimal_phase:
            result = short_taste + '/' + result
        elif phase_length > upper_limit - third_of_optimal_phase:
            result = result + '/' + long_taste
        return result
    
    #Flavor defect estimation chart for each leg. Thanks to Jim Schulman 
    def defect_estimation(self):    
        dryphasetime = aw.qmc.statisticstimes[1]
        midphasetime = aw.qmc.statisticstimes[2]
        finishphasetime = aw.qmc.statisticstimes[3]
        PerfectPhase = QApplication.translate("Flavor Scope Label", "OK",None, QApplication.UnicodeUTF8)
        ShortDryingPhase = QApplication.translate("Flavor Scope Label", "Grassy",None, QApplication.UnicodeUTF8)
        LongDryingPhase = QApplication.translate("Flavor Scope Label", "Leathery",None, QApplication.UnicodeUTF8)
        ShortTo1CPhase = QApplication.translate("Flavor Scope Label", "Toasty",None, QApplication.UnicodeUTF8)
        LongTo1CPhase = QApplication.translate("Flavor Scope Label", "Bready",None, QApplication.UnicodeUTF8)
        ShortFinishPhase = QApplication.translate("Flavor Scope Label", "Acidic",None, QApplication.UnicodeUTF8)
        LongFinishPhase = QApplication.translate("Flavor Scope Label", "Flat",None, QApplication.UnicodeUTF8)        
        #CHECK CONDITIONS                
        #if dry phase time < 3 mins (180 seconds) or less than 26% of the total time
        #  => ShortDryingPhase
        #if dry phase time > 6 mins or more than 40% of the total time
        #  => LongDryingPhase
        st1 = self.defect_estimation_phase(dryphasetime,aw.qmc.statisticsconditions[0],aw.qmc.statisticsconditions[1],ShortDryingPhase,PerfectPhase,LongDryingPhase)

        #if mid phase time < 5 minutes
        #  => ShortTo1CPhase        
        #if mid phase time > 10 minutes
        #  => LongTo1CPhase
        st2 = self.defect_estimation_phase(midphasetime,aw.qmc.statisticsconditions[2],aw.qmc.statisticsconditions[3],ShortTo1CPhase,PerfectPhase,LongTo1CPhase)

        #if finish phase is less than 3 mins
        #  => ShortFinishPhase
        #if finish phase is over 6 minutes
        #  => LongFinishPhase
        st3 = self.defect_estimation_phase(finishphasetime,aw.qmc.statisticsconditions[4],aw.qmc.statisticsconditions[5],ShortFinishPhase,PerfectPhase,LongFinishPhase)
        
        return (st1,st2,st3)
    
    #returns the index of the end of the dry phase (returns -1 if dry end cannot be determined)
    #if given, starts at TP_index and looks forward, otherwise it looks backwards from end of roast (EoR)

    #find index with smallest abs() difference between aw.qmc.phases[1] and BT (temp2)
    def findDryEnd(self,TP_index=None):
        sd = 1000
        nsd = 1000
        index = 0
        start = 0
        end = len(aw.qmc.timex)
        # try to consider only indices until the roast end and not beyond
        EOR_index = end
        if aw.qmc.timeindex[6]:
            EOR_index = aw.qmc.timeindex[6]
        if EOR_index > start and EOR_index < end:
            end = EOR_index
        # try to consider only indices until FCs and not beyond
        FCs_index = end
        if aw.qmc.timeindex[2]:
            FCs_index = aw.qmc.timeindex[6]
        if FCs_index > start and FCs_index < end:
            end = FCs_index
        # try to consider only indices from start of roast on and not before
        SOR_index = start
        if aw.qmc.timeindex[0] != -1:
            SOR_index = aw.qmc.timeindex[0] 
        if SOR_index > start and SOR_index < end:
            start = SOR_index
        # try to consider only indices from TP of roast on and not before
        TP = TP_index
        # if TP not yet computed, let's try to compute it
        if TP == None:
            TP = self.findTP()
        if TP > start and TP < end:
            start = TP
        for i in range(end -1, start -1, -1):
             nsd = abs(aw.qmc.temp2[i]- aw.qmc.phases[1])
             if nsd < sd:
                 sd = nsd
                 index = i
        return index
      
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
        if aw.qmc.timeindex[2]:
            if midphasetime and BTdrycross:
                rc2 = ((aw.qmc.temp2[aw.qmc.timeindex[2]] - BTdrycross)/midphasetime)*60.
            if finishphasetime:
                rc3 = ((aw.qmc.temp2[aw.qmc.timeindex[6]]- aw.qmc.temp2[aw.qmc.timeindex[2]])/finishphasetime)*60.
        return (rc1,rc2,rc3)    
        
    def viewErrorLog(self):
        error = errorDlg(self)
        error.show()

    def viewMessageLog(self):
        message = messageDlg(self)
        message.show()        
        
    def helpAbout(self):
        coredevelopers = u"<br>Rafael Cobo <br> Marko Luther <br> Sebastien Delgrande"
        contributors =  u"<br>" + QApplication.translate(u"About", u"%1, linux binary",None, QApplication.UnicodeUTF8).arg(u"Lukas Kolbe")
        contributors += u"<br>" + QApplication.translate(u"About", u"%1, documentation",None, QApplication.UnicodeUTF8).arg(u"Rich Helms")
        contributors += u"<br>" + QApplication.translate(u"About", u"%1, TEVA18B support",None, QApplication.UnicodeUTF8).arg(u"Markus Wagner")
        contributors += u"<br>" + QApplication.translate(u"About", u"%1, Swedish localization",None, QApplication.UnicodeUTF8).arg(u"Martin Kral")
        contributors += u"<br>" + QApplication.translate(u"About", u"%1, Spanish localization",None, QApplication.UnicodeUTF8).arg(u"Bluequijote")
        contributors += u"<br>" + QApplication.translate(u"About", u"%1, Arduino/TC4",None, QApplication.UnicodeUTF8).arg(u"Jim G.")
        contributors += u"<br>" + QApplication.translate(u"About", u"%1, Arduino/TC4",None, QApplication.UnicodeUTF8).arg(u"Marcio Carneiro")
        box = QMessageBox()
        
        #create a html QString
        box.about(self,
                QApplication.translate("About", "About",None, QApplication.UnicodeUTF8),
                u"""<b>{0}</b> {1} 
                <p>
                <b>Python:</b> [ {2} ]
                <b>Qt:</b> [ {3} ]
                <b>PyQt:</b> [ {4} ]
                <b>OS:</b/>[ {5} ]
                </p>
                <p>
                <b>{6}</b> {7}
                </p>
                <p>
                <b>{8}</b> {9}
                </p>""".format(
                QApplication.translate("About", "Version:",None, QApplication.UnicodeUTF8),
                __version__,
                platform.python_version(),
                QT_VERSION_STR,
                PYQT_VERSION_STR,
                platf,
                QApplication.translate("About", "Core developers:",None, QApplication.UnicodeUTF8),
                coredevelopers,
                QApplication.translate("About", "Contributors:",None, QApplication.UnicodeUTF8),
                contributors))
                
    def helpHelp(self):
        QDesktopServices.openUrl(QUrl(u"http://coffeetroupe.com/artisandocs/", QUrl.TolerantMode))

    def calibratedelay(self):
        calSpinBox = QDoubleSpinBox()
        calSpinBox.setRange(1.,30.)
        calSpinBox.setValue(self.qmc.delay/1000.)
        secondsdelay, ok = QInputDialog.getDouble(self,
                QApplication.translate("MessageBox Caption", "Sampling Interval",None, QApplication.UnicodeUTF8),
                QApplication.translate("MessageBox", "Seconds",None, QApplication.UnicodeUTF8),
                calSpinBox.value(),1.,30.)
        if ok:
            self.qmc.delay = int(secondsdelay*1000.) 	    	            

    def setcommport(self):
        dialog = comportDlg(self)
        if dialog.exec_():
            self.ser.comport = unicode(dialog.comportEdit.currentText())                #unicode() changes QString to a python string
            self.ser.baudrate = int(dialog.baudrateComboBox.currentText())              #int changes QString to int
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
        
    def Windowconfig(self):
        dialog = WindowsDlg(self)
        dialog.show()
        
    def autosaveconf(self):
        dialog = autosaveDlg(self)
        dialog.show()        

    def calculator(self):
        dialog = calculatorDlg(self)
        dialog.show()

    def graphwheel(self):
        dialog = WheelDlg(self)
        dialog.show()

    def background(self):
        dialog = backgroundDLG(self)
        dialog.show()       

    def flavorchart(self):
        dialog = flavorDlg(self)
        dialog.show()

    def designerTriggered(self):
        if self.qmc.designerflag:
            self.stopdesigner()
        else:
            self.startdesigner()
    
    def startdesigner(self):
        self.qmc.designer()

    def stopdesigner(self):  
        self.qmc.reset()
        
    def editgraph(self):
        dialog = editGraphDlg(self)
        dialog.show()

    def editphases(self):
        dialog = phasesGraphDlg(self)
        dialog.show()
        
    def eventsconf(self):
        dialog = EventsDlg(self)
        dialog.show()
        
    def alarmconfig(self):
        if self.qmc.device != 18:
            dialog = AlarmDlg(self)
            dialog.show()
        else:
            QMessageBox.information(self,QApplication.translate("MessageBox Caption", "Alarm Config",None, QApplication.UnicodeUTF8),
                                    QApplication.translate("MessageBox", "Alarms are not available for device None",None, QApplication.UnicodeUTF8))

    def changelocale(self,languagelocale):
        settings = QSettings()
        settings.setValue('locale', languagelocale)
        QMessageBox.information(self,QApplication.translate("MessageBox Caption", "Switch Language",None, QApplication.UnicodeUTF8),
                                QApplication.translate("MessageBox","Language successfully changed. Restart the application.",None, QApplication.UnicodeUTF8))

    # takes the weight of the green and roasted coffee as floats and
    # returns the weight loss in percentage as float
    def weight_loss(self,green,roasted):
      if float(green) == 0.0 or float(green) < float(roasted):
        return 0.
      else:
        return 100. * ((float(green) - float(roasted)) / float(green))


    # from RoastMagazine (corrected by substracting 1% based on experience)
    # http://www.roastmagazine.com/resources/Roasting101_Articles/Roast_SeptOct05_LightRoasting.pdf
    def roast_degree(self,percent):
        if percent < 13.5:
            return ""
        elif percent < 14.5:
            return QApplication.translate("Label", "City",None, QApplication.UnicodeUTF8)
        elif percent < 15.5:
            return QApplication.translate("Label", "City+",None, QApplication.UnicodeUTF8)
        elif percent < 16.5:
            return QApplication.translate("Label", "Full City",None, QApplication.UnicodeUTF8)
        elif percent < 17.5:
            return QApplication.translate("Label", "Full City+",None, QApplication.UnicodeUTF8)
        elif percent < 18.5:
            return QApplication.translate("Label", "Light French",None, QApplication.UnicodeUTF8)
        else:
            return QApplication.translate("Label", "French",None, QApplication.UnicodeUTF8)
            
    def importK202(self):
        try:
            filename = aw.ArtisanOpenFileDialog(msg=QApplication.translate("MessageBox Caption","Import K202 CSV",None, QApplication.UnicodeUTF8))
            if  filename == "":
                return
            self.qmc.reset()
            f = QFile(filename)
            if not f.open(QIODevice.ReadOnly):
                raise IOError, unicode(f.errorString())
                return
            import csv
            csvFile = file(filename,"rb")
            csvReader = csv.DictReader(csvFile,["Date","Time","T1","T1unit","T2","T2unit"],delimiter='\t')            
            zero_t = None
            roastdate = None
            unit = None
            for item in csvReader:
                try:
                    #set date
                    if not roastdate:
                        roastdate = QDate.fromString(item['Date'],"dd'.'MM'.'yyyy")
                        self.qmc.roastdate = roastdate
                    #set zero
                    if not zero_t:
                        date = QDate.fromString(item['Date'],"dd'.'MM'.'yyyy")
                        zero = QDateTime()
                        zero.setDate(date)
                        zero.setTime(QTime.fromString(item['Time'],"hh':'mm':'ss"))
                        zero_t = zero.toTime_t()
                    #set temperature mode
                    if not unit:
                        unit = item['T1unit']
                        if unit == u"F" and self.qmc.mode == u"C":
                            self.qmc.fahrenheitMode()
                        if unit == u"C" and self.qmc.mode == u"F":
                            self.qmc.celsiusMode()
                    #add one measurement
                    dt = QDateTime()
                    dt.setDate(QDate.fromString(item['Date'],"dd'.'MM'.'yyyy"))
                    dt.setTime(QTime.fromString(item['Time'],"hh':'mm':'ss"))
                    self.qmc.timex.append(float(dt.toTime_t() - zero_t))
                    self.qmc.temp1.append(float(item['T1'].replace(',','.')))
                    self.qmc.temp2.append(float(item['T2'].replace(',','.')))
                except ValueError:
                    pass
            csvFile.close()
            #swap temperature curves if needed such that BT is the lower and ET the upper one
            if (reduce (lambda x,y:x + y, self.qmc.temp2)) > reduce (lambda x,y:x + y, self.qmc.temp1):
                tmp = self.qmc.temp1
                self.qmc.temp1 = self.qmc.temp2
                self.qmc.temp2 = tmp
            self.qmc.endofx = self.qmc.timex[-1]
            self.sendmessage(QApplication.translate("Message Area","K202 file loaded successfully", None, QApplication.UnicodeUTF8))
            self.qmc.redraw()
 
        except IOError,e:
            self.qmc.adderror(QApplication.translate("Error Message","IO Error: importK202(): %1 ", None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return            

        except ValueError,e:
            self.qmc.adderror(QApplication.translate("Error Message","Value Error: importK202(): %1 ", None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

            
    def importHH506RA(self):
        try:
            filename = aw.ArtisanOpenFileDialog(msg=QApplication.translate("MessageBox Caption","Import HH506RA CSV", None, QApplication.UnicodeUTF8))
            if  filename == "":
                return
            self.qmc.reset()
            f = QFile(filename)
            if not f.open(QIODevice.ReadOnly):
                raise IOError, unicode(f.errorString())
                return
                
            import csv
            csvFile = file(filename,"rb")
            data = csv.reader(csvFile,delimiter='\t')
            #read file header
            header = data.next()
            zero = QDateTime()
            date = QDate.fromString(header[0].split('Date:')[1],"yyyy'/'MM'/'dd")
            self.qmc.roastdate = date
            zero.setDate(date)
            zero.setTime(QTime.fromString(header[1].split('Time:')[1],"hh':'mm':'ss"))
            zero_t = zero.toTime_t()
            #read column headers
            fields = data.next() 
            unit = None
            #read data
            for row in data:
                items = zip(fields, row)
                item = {}
                for (name, value) in items:
                    item[name] = value.strip()
                #set temperature mode
                if not unit:
                    unit = item['Unit']
                    if unit == u"F" and self.qmc.mode == u"C":
                        self.qmc.fahrenheitMode()
                    if unit == u"C" and self.qmc.mode == u"F":
                        self.qmc.celsiusMode()
                #add one measurement
                dt = QDateTime()
                dt.setDate(QDate.fromString(item['Date'],"yyyy'/'MM'/'dd"))
                dt.setTime(QTime.fromString(item['Time'],"hh':'mm':'ss"))
                self.qmc.timex.append(float(dt.toTime_t() - zero_t))
                self.qmc.temp1.append(float(item['T1']))
                self.qmc.temp2.append(float(item['T2']))
            csvFile.close()
            #swap temperature curves if needed such that BT is the lower and ET the upper one
            if (reduce (lambda x,y:x + y, self.qmc.temp2)) > reduce (lambda x,y:x + y, self.qmc.temp1):
                tmp = self.qmc.temp1
                self.qmc.temp1 = self.qmc.temp2
                self.qmc.temp2 = tmp
            self.qmc.endofx = self.qmc.timex[-1]
            self.sendmessage(QApplication.translate("Message Area","HH506RA file loaded successfully", None, QApplication.UnicodeUTF8))
            self.qmc.redraw()
 
        except IOError,e:
            self.qmc.adderror(QApplication.translate("Error Message","IO Error: importHH506RA(): %1 ", None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return            

        except ValueError,e:
            self.qmc.adderror(QApplication.translate("Error Message","Value Error: importHH506RA(): %1 ", None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return


    #checks or creates directory structure
    def dirstruct(self):
        currentdir = QDir().current()     #selects the current dir
        if not currentdir.exists(QApplication.translate("Directory","profiles", None, QApplication.UnicodeUTF8)):
            profilesdir = currentdir.mkdir(QApplication.translate("Directory","profiles",None, QApplication.UnicodeUTF8))

        #check/create 'other' directory inside profiles/
        otherpath = QString(QApplication.translate("Directory","profiles", None, QApplication.UnicodeUTF8) + "/" + QApplication.translate("Directory","other", None, QApplication.UnicodeUTF8))
        if not currentdir.exists(otherpath):
            yeardir = currentdir.mkdir(otherpath)
            
        #find current year,month
        date =  QDate.currentDate()       
        
        #check / create year dir 
        yearpath = QString(QApplication.translate("Directory","profiles", None, QApplication.UnicodeUTF8) + "/" + unicode(date.year()))
        if not currentdir.exists(yearpath):
            yeardir = currentdir.mkdir(yearpath)

        #check /create month dir to store profiles
        monthpath = QString(QApplication.translate("Directory","profiles", None, QApplication.UnicodeUTF8) + "/" + unicode(date.year()) + u"/" + unicode(date.month()))
        if not currentdir.exists(monthpath):
            monthdir = currentdir.mkdir(monthpath)
        if  self.profilepath == u"":   
            self.profilepath = monthpath

    #resizes and saves graph to a new width w 
    def resize(self,w,transformationmode):
        try: 
            tempFile = tempfile.TemporaryFile()
            aw.qmc.fig.savefig(tempFile.name)
            image = QImage(tempFile.name)

            if w != 0:        
                image = image.scaledToWidth(w,transformationmode)
        
            filename = aw.ArtisanSaveFileDialog(msg=QApplication.translate("MessageBox Caption","Save Image for Web", None, QApplication.UnicodeUTF8),ext="*.png")            
            if filename:
                if u".png" not in filename:
                    filename += u".png"

                image.save(filename)
                
                x = image.width()
                y = image.height()

                self.sendmessage(QApplication.translate("Message Area","%1  size(%2,%3) saved", None, QApplication.UnicodeUTF8).arg(unicode(filename)).arg(unicode(x)).arg(unicode(y)))

        except IOError,e:
            self.qmc.adderror(QApplication.translate("Error Message","IO Error: resize() %1 ", None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

    #displays Dialog for the setting of the HUD
    def hudset(self):
        hudDl = HUDDlg(self)
        hudDl.show()        
        
    def showHUDmetrics(self):
        ETreachTime,BTreachTime = self.qmc.getTargetTime()
        
        if ETreachTime > 0 and BTreachTime < 5940:
            text1 =  QApplication.translate("Scope Label","%1 to reach ET target %2", None, QApplication.UnicodeUTF8).arg(self.qmc.stringfromseconds(int(ETreachTime))).arg(unicode(self.qmc.ETtarget) + self.qmc.mode)
        else:
            text1 =  QApplication.translate("Scope Label","%1 to reach ET target %2", None, QApplication.UnicodeUTF8).arg("xx:xx").arg(unicode(self.qmc.ETtarget) + self.qmc.mode)
            
        if BTreachTime > 0 and BTreachTime < 5940:    
            text2 =  QApplication.translate("Scope Label","%1 to reach BT target %2", None, QApplication.UnicodeUTF8).arg(self.qmc.stringfromseconds(int(BTreachTime))).arg(unicode(self.qmc.BTtarget) + self.qmc.mode)
        else:
            text2 =  QApplication.translate("Scope Label","%1 to reach BT target %2", None, QApplication.UnicodeUTF8).arg("xx:xx").arg(unicode(self.qmc.BTtarget) + self.qmc.mode)

        ####   ET pid    ######
        error = self.qmc.ETtarget - self.qmc.temp1[-1]
        differror = error - self.qmc.pidpreviouserror
        difftime = self.qmc.timex[-1] - self.qmc.timex[-2]
        if not difftime: difftime = 0.01
        proportionalterm = self.qmc.hudETpid[0]*error
        integralterm = self.qmc.hudETpid[1]*differror*difftime
        derivativeterm = self.qmc.hudETpid[2]*differror/difftime
        self.qmc.pidpreviouserror = error
        MV = proportionalterm + integralterm + derivativeterm   # Manipulated Variable
        if MV > 100.:MV = 100.
        elif MV < 0.:MV = 0.
        MVV = int(round(MV))
        pidstring = "ET pid = %i "%MVV
        ##### end of ET pid
        
        img = QPixmap().grabWidget(self.qmc)

        Wwidth = self.qmc.size().width()
        Wheight = self.qmc.size().height()

        #Draw begins               
        p = QPainter(img)        
        #chose font
        font = QFont('Utopia', 14, -1)
        p.setFont(font)
        p.setOpacity(0.6)
        p.setPen(QColor("slategrey"))
        #p.setPen(QColor(self.qmc.palette["text"]))
        p.drawText(QPoint(Wwidth/7,Wheight - Wheight/6),QString(text1))
        
        #p.setPen(QColor(self.qmc.palette["bt"]))
        p.drawText(QPoint(Wwidth/7,Wheight - Wheight/8),QString(text2))

        p.drawText(QPoint(Wwidth/2+20,Wheight - Wheight/8),QString(pidstring))
        
        delta = QApplication.translate("Scope Label","ET - BT = %1", None, QApplication.UnicodeUTF8).arg("%.1f"%(self.qmc.temp1[-1] - self.qmc.temp2[-1]))
        p.drawText(QPoint(Wwidth/2+20,Wheight - Wheight/6),QString(delta))

        p.drawRect(Wwidth/2+140, Wheight - Wheight/8 -12, 100, 12)
        p.fillRect(Wwidth/2+140, Wheight - Wheight/8 - 12, MVV, 12, QColor("pink"))
  
        p.end()
        self.HUD.setPixmap(img)
       
    def showHUDthermal(self): 
        img = QPixmap().grabWidget(aw.qmc)        
        p = QPainter(img)
        Wwidth= aw.qmc.size().width()
        Wheight = aw.qmc.size().height()
       
        p.setOpacity(1)
        p.setPen(QColor(96,255,237)) #color the rectangle the same as HUD button
        p.drawRect(10,10, Wwidth - 20, Wheight - 20)

        if self.qmc.mode == "F" and self.qmc.temp1:
            ETradius = int(self.qmc.temp1[-1]/3)
            BTradius = int(self.qmc.temp2[-1]/3)
        elif self.qmc.mode == "C" and self.qmc.temp1:
            ETradius = int(self.qmc.fromCtoF(self.qmc.temp1[-1]/3))
            BTradius = int(self.qmc.fromCtoF(self.qmc.temp2[-1]/3))            
        else:
            ETradius = 50
            BTradius = 50
    
        Tradius = 300
        p.setOpacity(0.5)
        
        g = QRadialGradient(Wwidth/2, Wheight/2, ETradius)
        
        beanbright =  100 - ETradius
        if beanbright < 0: beanbright = 0
        g.setColorAt(0.0, QColor(240,255,beanbright) )  #bean center
        
        g.setColorAt(.5, Qt.yellow)
        g.setColorAt(.8, Qt.red)
        g.setColorAt(1.,QColor("lightgrey"))
        p.setBrush(QBrush(g))
        #draw thermal circle
        p.setPen(0)
        p.drawEllipse (Wwidth/2 -Tradius/2 , Wheight/2 - Tradius/2 , Tradius,Tradius)

        #draw ET circle
        p.setBrush(0)
        p.setPen(QColor("black"))
        p.drawEllipse (Wwidth/2 -ETradius/2 , Wheight/2 - ETradius/2 , ETradius,ETradius)
        #draw BT circle
        p.drawEllipse (Wwidth/2 -BTradius/2 , Wheight/2 - BTradius/2 , BTradius,BTradius)

        delta = QApplication.translate("Scope Label","ET - BT = %1%2", None, QApplication.UnicodeUTF8).arg("%.1f"%(self.qmc.temp1[-1] - self.qmc.temp2[-1])).arg(self.qmc.mode)
        p.setFont(QFont('Utopia', 14, -1))
        p.drawText(QPoint(Wwidth/2,Wheight/2),QString(delta))
        
        p.end()
        self.HUD.setPixmap(img)

    #used by WheelGraphDlg()
    #wrap values in unicode(.) if and only if those are of type string
    def getWheelGraph(self):
        wheel = {}
        #convert labels to unicode
        for i in range(len(self.qmc.wheelnames)):
            for x in range(len(self.qmc.wheelnames[i])):
                self.qmc.wheelnames[i][x]= unicode(self.qmc.wheelnames[i][x])
        #two dimension lists        
        wheel["wheelnames"] = self.qmc.wheelnames
        wheel["segmentlengths"] = self.qmc.segmentlengths
        wheel["segmentsalpha"] = self.qmc.segmentsalpha
        wheel["wradii"] = self.qmc.wradii
        wheel["startangle"] = self.qmc.startangle
        wheel["projection"] = self.qmc.projection
        wheel["wheeltextsize"] = self.qmc.wheeltextsize 
        wheel["wheelcolor"] = self.qmc.wheelcolor
        wheel["wheelparent"] = self.qmc.wheellabelparent
        wheel["wheeledge"] = self.qmc.wheeledge
        wheel["wheellinewidth"] = self.qmc.wheellinewidth
        wheel["wheellinecolor"] = self.qmc.wheellinecolor
        return wheel  

    def loadWheel(self,filename):         
        try:
            f = QFile(unicode(filename))
            if not f.open(QIODevice.ReadOnly):
                raise IOError, unicode(f.errorString())
            stream = QTextStream(f)
            firstChar = stream.read(1)
            if firstChar == "{":            
                f.close()
                wheel = aw.deserialize(filename)
                self.qmc.wheelnames = wheel["wheelnames"]
                self.qmc.segmentlengths = wheel["segmentlengths"]
                self.qmc.segmentsalpha = wheel["segmentsalpha"]
                self.qmc.wradii = wheel["wradii"]
                self.qmc.startangle = wheel["startangle"]
                self.qmc.projection = wheel["projection"]
                self.qmc.wheeltextsize = wheel["wheeltextsize"] 
                self.qmc.wheelcolor = wheel["wheelcolor"]
                self.qmc.wheellabelparent = wheel["wheelparent"]
                self.qmc.wheeledge = wheel["wheeledge"]
                self.qmc.wheellinewidth = wheel["wheellinewidth"]
                self.qmc.wheellinecolor = wheel["wheellinecolor"]
            else:
                message = QApplication.translate("Message Area","Invalid Wheel graph format", None, QApplication.UnicodeUTF8)
                self.sendmessage(message)
                return
            message =QApplication.translate("Message Area","Wheel Graph succesfully open", None, QApplication.UnicodeUTF8)
            self.sendmessage(message)

        except IOError,e:
            self.qmc.adderror(QApplication.translate("Error Message","IO Error: loadWheel() %1 ", None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

        except ValueError,e:
            self.qmc.adderror(QApplication.translate("Error Message","Value Error: loadWheel() %1 ", None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

        except Exception,e:
            self.qmc.adderror(QApplication.translate("Error Message","Exception Error: loadWheel() %1 ", None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return
        
        finally:
            if f:
                f.close()

##########################################################################
#####################     HUD  EDIT DLG     ##############################
##########################################################################
        
class HUDDlg(QDialog):
    def __init__(self, parent = None):
        super(HUDDlg,self).__init__(parent)

        self.setWindowTitle(QApplication.translate("Form Caption","Extras", None, QApplication.UnicodeUTF8))
        self.setModal(True)

        self.status = QStatusBar()
        self.status.setSizeGripEnabled(False)
        self.status.showMessage(QApplication.translate("StatusBar","Ready", None, QApplication.UnicodeUTF8),1000)

        #### TAB 1
        
        # keep old values to be restored on Cancel
        self.org_DeltaET = aw.qmc.DeltaETflag
        self.org_DeltaBT = aw.qmc.DeltaBTflag
        self.org_Sensitivity = aw.qmc.sensitivity
        self.org_Projection = aw.qmc.projectFlag
        
        ETLabel = QLabel(QApplication.translate("Label", "ET Target",None, QApplication.UnicodeUTF8))
        ETLabel.setAlignment(Qt.AlignRight)
        BTLabel = QLabel(QApplication.translate("Label", "BT Target",None, QApplication.UnicodeUTF8))
        BTLabel.setAlignment(Qt.AlignRight)        
        modeLabel = QLabel(QApplication.translate("Label", "Mode",None, QApplication.UnicodeUTF8))
        modeLabel.setAlignment(Qt.AlignRight)
        ETPIDLabel = QLabel(QApplication.translate("Label", "ET p-i-d",None, QApplication.UnicodeUTF8))
        pidhelpButton = QPushButton(QApplication.translate("Button","pid Help",None, QApplication.UnicodeUTF8))
        pidhelpButton.setMaximumWidth(60)
        self.connect(pidhelpButton,SIGNAL("clicked()"),self.showpidhelp)
    
        #delta ET    
        self.DeltaET = QCheckBox(QApplication.translate("CheckBox", "DeltaET",None, QApplication.UnicodeUTF8))
        if aw.qmc.DeltaETflag == True:
            self.DeltaET.setChecked(True)
        else:
            self.DeltaET.setChecked(False)

        #delta BT   
        self.DeltaBT = QCheckBox(QApplication.translate("CheckBox", "DeltaBT",None, QApplication.UnicodeUTF8))        
        if aw.qmc.DeltaBTflag == True:
            self.DeltaBT.setChecked(True)
        else:
            self.DeltaBT.setChecked(False)
            
        filterlabel = QLabel(QApplication.translate("Label", "Filter",None, QApplication.UnicodeUTF8))
        #DeltaFilter holds the number of pads in filter  
        self.DeltaFilter = QSpinBox()
        self.DeltaFilter.setRange(0,20)
        self.DeltaFilter.setValue(aw.qmc.deltafilter)
        self.connect(self.DeltaFilter ,SIGNAL("valueChanged(int)"),lambda i=0:self.changeDeltaFilter(i)) 
    	
        #show projection
        self.projectCheck = QCheckBox(QApplication.translate("CheckBox", "Projection",None, QApplication.UnicodeUTF8))
        projectionmodeLabel = QLabel(QApplication.translate("Label", "Mode",None, QApplication.UnicodeUTF8))
        self.projectionmodeComboBox = QComboBox()
        self.projectionmodeComboBox.addItems([QApplication.translate("ComboBox","linear",None, QApplication.UnicodeUTF8),
                                              QApplication.translate("ComboBox","newton",None, QApplication.UnicodeUTF8)])
        self.projectionmodeComboBox.setCurrentIndex(aw.qmc.projectionmode)
        self.connect(self.projectionmodeComboBox,SIGNAL("currentIndexChanged(int)"),lambda i=self.projectionmodeComboBox.currentIndex() :self.changeProjectionMode(i))

        if aw.qmc.projectFlag == True:
            self.projectCheck.setChecked(True)
        else:
            self.projectCheck.setChecked(False)
            
        self.connect(self.DeltaET,SIGNAL("stateChanged(int)"),lambda i=0:self.changeDeltaET(i))         #toggle
        self.connect(self.DeltaBT,SIGNAL("stateChanged(int)"),lambda i=0:self.changeDeltaBT(i))         #toggle
        self.connect(self.projectCheck,SIGNAL("stateChanged(int)"),lambda i=0:self.changeProjection(i)) #toggle
            
        sensitivityValues = map(unicode,range(0,11))  #range(0,11) = 0-10
        self.sensitivitylabel  = QLabel(QApplication.translate("Label", "Sensitivity",None, QApplication.UnicodeUTF8))                          
        self.sensitivityComboBox = QComboBox()
        self.sensitivityComboBox.addItems(sensitivityValues)
        self.sensitivityComboBox.setCurrentIndex(sensitivityValues.index(unicode(aw.qmc.sensitivity)))
        self.connect(self.sensitivityComboBox,SIGNAL("currentIndexChanged(int)"),self.changeSensitivity)
                        
        self.modeComboBox = QComboBox()
        self.modeComboBox.setMaximumWidth(100)
        self.modeComboBox.setMinimumWidth(55)
        self.modeComboBox.addItems([QApplication.translate("ComboBox","metrics",None, QApplication.UnicodeUTF8),
                                    QApplication.translate("ComboBox","thermal",None, QApplication.UnicodeUTF8)])
        self.modeComboBox.setCurrentIndex(aw.HUDfunction)
        
        self.ETlineEdit = QLineEdit(str(aw.qmc.ETtarget))           
        self.BTlineEdit = QLineEdit(str(aw.qmc.BTtarget))
        self.ETlineEdit.setValidator(QIntValidator(0, 1000, self.ETlineEdit))
        self.BTlineEdit.setValidator(QIntValidator(0, 1000, self.BTlineEdit))
        self.ETlineEdit.setMaximumWidth(60)
        self.BTlineEdit.setMaximumWidth(60)

        self.ETpidP = QLineEdit(str(aw.qmc.hudETpid[0]))
        self.ETpidI = QLineEdit(str(aw.qmc.hudETpid[1]))
        self.ETpidD = QLineEdit(str(aw.qmc.hudETpid[2]))
        self.ETpidP.setValidator(QIntValidator(0, 1000, self.ETpidP))
        self.ETpidI.setValidator(QIntValidator(0, 1000, self.ETpidI))
        self.ETpidD.setValidator(QIntValidator(0, 1000, self.ETpidD))
        self.ETpidP.setMaximumWidth(60)
        self.ETpidI.setMaximumWidth(60)
        self.ETpidD.setMaximumWidth(60)

        okButton = QPushButton(QApplication.translate("Button","OK",None, QApplication.UnicodeUTF8))  
        cancelButton = QPushButton(QApplication.translate("Button","Cancel",None, QApplication.UnicodeUTF8))   
        cancelButton.setFocusPolicy(Qt.NoFocus)     
        self.connect(cancelButton,SIGNAL("clicked()"),self.close)
        self.connect(okButton,SIGNAL("clicked()"),self.updatetargets)
                                             
        hudLayout = QGridLayout()
        hudLayout.addWidget(ETLabel,0,0)
        hudLayout.addWidget(self.ETlineEdit,0,1)
        hudLayout.addWidget(BTLabel,0,2)
        hudLayout.addWidget(self.BTlineEdit,0,3)
        hudLayout.addWidget(ETPIDLabel,1,0)
        hudLayout.addWidget(self.ETpidP,1,1)
        hudLayout.addWidget(self.ETpidI,1,2)
        hudLayout.addWidget(self.ETpidD,1,3)
        hudLayout.addWidget(modeLabel,2,0)
        hudLayout.addWidget(self.modeComboBox,2,1)
        hudLayout.addWidget(pidhelpButton,2,3)
        
        rorLayout = QGridLayout()
        rorLayout.addWidget(self.projectCheck,0,0)
        rorLayout.addWidget(self.projectionmodeComboBox,0,1)
        rorLayout.addWidget(self.DeltaET,1,0)
        rorLayout.addWidget(self.DeltaBT,1,1)
        
        rorBoxLayout = QHBoxLayout()
        rorBoxLayout.addLayout(rorLayout)
        rorBoxLayout.addStretch()
        
        sensitivityLayout = QHBoxLayout()
        sensitivityLayout.addWidget(self.sensitivitylabel)
        sensitivityLayout.addWidget(self.sensitivityComboBox)
        sensitivityLayout.addWidget(filterlabel)
        sensitivityLayout.addWidget(self.DeltaFilter)
        sensitivityLayout.addStretch()
        
        curvesLayout = QVBoxLayout()
        curvesLayout.addLayout(rorBoxLayout)
        curvesLayout.addLayout(sensitivityLayout)
        
        rorGroupLayout = QGroupBox(QApplication.translate("GroupBox","Curves",None, QApplication.UnicodeUTF8))        
        rorGroupLayout.setLayout(curvesLayout)
        
        hudGroupLayout = QGroupBox(QApplication.translate("GroupBox","HUD",None, QApplication.UnicodeUTF8))
        hudGroupLayout.setLayout(hudLayout)       
                               
        tab1Layout = QVBoxLayout()
        tab1Layout.addWidget(rorGroupLayout)
        tab1Layout.addWidget(hudGroupLayout)

        #tab2
        #Equation plotter
        equlabel = QLabel(QApplication.translate("Label", "Y(x)",None, QApplication.UnicodeUTF8))
        self.equedit1 = QLineEdit(aw.qmc.plotcurves[0])
        self.equedit2 = QLineEdit(aw.qmc.plotcurves[1])
        self.equedit3 = QLineEdit(aw.qmc.plotcurves[2])
        self.equedit4 = QLineEdit(aw.qmc.plotcurves[3])
        self.equedit5 = QLineEdit(aw.qmc.plotcurves[4])
        self.equedit6 = QLineEdit(aw.qmc.plotcurves[5])
        color1Button = QPushButton("Color")
        color1Button.setFocusPolicy(Qt.NoFocus)
        self.connect(color1Button, SIGNAL("clicked()"),lambda x=0: self.setcurvecolor(x))
        color2Button = QPushButton("Color")
        color2Button.setFocusPolicy(Qt.NoFocus)
        self.connect(color2Button, SIGNAL("clicked()"),lambda x=1: self.setcurvecolor(x))
        color3Button = QPushButton("Color")
        color3Button.setFocusPolicy(Qt.NoFocus)
        self.connect(color3Button, SIGNAL("clicked()"),lambda x=2: self.setcurvecolor(x))
        color4Button = QPushButton("Color")
        color4Button.setFocusPolicy(Qt.NoFocus)
        self.connect(color4Button, SIGNAL("clicked()"),lambda x=3: self.setcurvecolor(x))
        color5Button = QPushButton("Color")
        color5Button.setFocusPolicy(Qt.NoFocus)
        self.connect(color5Button, SIGNAL("clicked()"),lambda x=4: self.setcurvecolor(x))
        color6Button = QPushButton("Color")
        color6Button.setFocusPolicy(Qt.NoFocus)
        self.connect(color6Button, SIGNAL("clicked()"),lambda x=5: self.setcurvecolor(x))

        equdrawbutton = QPushButton(QApplication.translate("Button","Plot",None, QApplication.UnicodeUTF8))
        equdrawbutton.setFocusPolicy(Qt.NoFocus)
        self.connect(equdrawbutton,SIGNAL("clicked()"),self.plotequ)
        equbackgroundbutton = QPushButton(QApplication.translate("Button","Set Plot 1 as background",None, QApplication.UnicodeUTF8))
        equbackgroundbutton.setFocusPolicy(Qt.NoFocus)
        self.connect(equbackgroundbutton ,SIGNAL("clicked()"),self.setbackgroundequ1)
        
        saveImgButton = QPushButton(QApplication.translate("Button","Save Image",None, QApplication.UnicodeUTF8))
        saveImgButton.setFocusPolicy(Qt.NoFocus)
        saveImgButton.setToolTip(QApplication.translate("Tooltip","Save image using current graph size to a png format",None, QApplication.UnicodeUTF8))
        self.connect(saveImgButton, SIGNAL("clicked()"),lambda x=0,i=1:aw.resize(x,i))

        helpcurveButton = QPushButton(QApplication.translate("Button","Help",None, QApplication.UnicodeUTF8))
        helpcurveButton.setFocusPolicy(Qt.NoFocus)
        self.connect(helpcurveButton, SIGNAL("clicked()"),self.showcurvehelp)
        
        curveLayout = QGridLayout()
        curveLayout.addWidget(self.equedit1,0,0)
        curveLayout.addWidget(color1Button,0,1)
        curveLayout.addWidget(self.equedit2,1,0)
        curveLayout.addWidget(color2Button,1,1)
        curveLayout.addWidget(self.equedit3,2,0)
        curveLayout.addWidget(color3Button,2,1)
        curveLayout.addWidget(self.equedit4,3,0)
        curveLayout.addWidget(color4Button,3,1)
        curveLayout.addWidget(self.equedit5,4,0)
        curveLayout.addWidget(color5Button,4,1)
        curveLayout.addWidget(self.equedit6,5,0)
        curveLayout.addWidget(color6Button,5,1)

        curvebuttonlayout = QHBoxLayout()
        curvebuttonlayout.addWidget(equdrawbutton)      
        curvebuttonlayout.addWidget(saveImgButton)        
        curvebuttonlayout.addWidget(helpcurveButton)        
        
        tab2Layout = QVBoxLayout()
        tab2Layout.addWidget(equlabel)      
        tab2Layout.addLayout(curveLayout)
        tab2Layout.addLayout(curvebuttonlayout)
        tab2Layout.addWidget(equbackgroundbutton)

        ##### TAB 3
        self.interpCheck = QCheckBox(QApplication.translate("CheckBox","Interpolation",None, QApplication.UnicodeUTF8))
        self.connect(self.interpCheck,SIGNAL("stateChanged(int)"),lambda i=0:self.interpolation(i)) #toggle
        
        self.interpComboBox = QComboBox()
        self.interpComboBox.setMaximumWidth(100)
        self.interpComboBox.setMinimumWidth(55)
        self.interpComboBox.addItems([QApplication.translate("ComboBox","linear",None, QApplication.UnicodeUTF8),
                                      QApplication.translate("ComboBox","cubic",None, QApplication.UnicodeUTF8),
                                      QApplication.translate("ComboBox","nearest",None, QApplication.UnicodeUTF8)])
        self.interpComboBox.setToolTip(QApplication.translate("Tooltip", "linear: linear interpolation\ncubic: 3rd order spline interpolation\nnearest: y value of the nearest point", None, QApplication.UnicodeUTF8))
        self.connect(self.interpComboBox,SIGNAL("currentIndexChanged(int)"),lambda i=self.interpComboBox.currentIndex() :self.changeInterpolationMode(i))

       
        """
         'linear'  : linear interpolation
         'cubic'   : 3rd order spline interpolation
         'nearest' : take the y value of the nearest point
        """

        self.univarCheck = QCheckBox(QApplication.translate("CheckBox", "Univariate",None, QApplication.UnicodeUTF8))
        self.connect(self.univarCheck,SIGNAL("stateChanged(int)"),lambda i=0:self.univar(i)) #toggle

        univarButton = QPushButton(QApplication.translate("Button","Info",None, QApplication.UnicodeUTF8))
        univarButton.setFocusPolicy(Qt.NoFocus)
        univarButton.setMaximumSize(50, 30)
        self.connect(univarButton,SIGNAL("clicked()"),self.showunivarinfo)
        
        tab3Layout = QVBoxLayout()
        interLayout = QGridLayout()
        interLayout.addWidget(self.interpCheck,0,0)
        interLayout.addWidget(self.interpComboBox,0,1)
        
        interGroupLayout = QGroupBox(QApplication.translate("GroupBox","Interpolate",None, QApplication.UnicodeUTF8))
        interGroupLayout.setLayout(interLayout)

        uniLayout = QHBoxLayout()
        uniLayout.addWidget(self.univarCheck,0)
        uniLayout.addWidget(univarButton,1)

        univarGroupLayout = QGroupBox(QApplication.translate("GroupBox","Univariate",None, QApplication.UnicodeUTF8))
        univarGroupLayout.setLayout(uniLayout)

        tab3Layout.addWidget(interGroupLayout)
        tab3Layout.addWidget(univarGroupLayout)

        ##### TAB 4
        self.soundCheck = QCheckBox(QApplication.translate("CheckBox", "Beep",None, QApplication.UnicodeUTF8))
        if aw.soundflag:
            self.soundCheck.setChecked(True)
        else:
            self.soundCheck.setChecked(False)    
        self.connect(self.soundCheck,SIGNAL("stateChanged(int)"),lambda i=0:self.soundset(i)) #toggle

        mikeButton = QPushButton(QApplication.translate("Button","Test Mike",None, QApplication.UnicodeUTF8))             
        mikeButton.setFocusPolicy(Qt.NoFocus)        
        self.connect(mikeButton,SIGNAL("clicked()"),self.showsound)

        self.showsoundflag = 0
        
        tab4Layout = QHBoxLayout()
        tab4Layout.addWidget(self.soundCheck)
        tab4Layout.addWidget(mikeButton)

    	#### TAB 5

        
        self.styleComboBox = QComboBox()
        available = map(QString, QStyleFactory.keys())
        available = map(unicode,available)
        self.styleComboBox.addItems(available)
        
        styleButton = QPushButton(QApplication.translate("Button","Set style",None, QApplication.UnicodeUTF8))
        styleButton.setFocusPolicy(Qt.NoFocus)   
        styleButton.setMaximumWidth(90)
        self.connect(styleButton,SIGNAL("clicked()"),self.setappearance)
        
        self.resolutionSpinBox = QSpinBox()
        self.resolutionSpinBox.setRange(40,120)
        self.resolutionSpinBox.setSingleStep(5)
        self.resolutionSpinBox.setValue(aw.dpi)

        resButton = QPushButton(QApplication.translate("Button","Set Resolution",None, QApplication.UnicodeUTF8))
        resButton.setFocusPolicy(Qt.NoFocus)
        #resButton.setMaximumWidth(120)        
        self.connect(resButton,SIGNAL("clicked()"),self.changedpi)

        defresButton = QPushButton(QApplication.translate("Button","Default Resolution",None, QApplication.UnicodeUTF8))
        defresButton.setFocusPolicy(Qt.NoFocus)
        #defresButton.setMaximumWidth(120)        
        self.connect(defresButton,SIGNAL("clicked()"),self.setdefaultres)
                
        tab5Layout = QVBoxLayout()
        tab5Layout.addWidget(self.styleComboBox)    	
        tab5Layout.addWidget(styleButton)
        tab5Layout.addWidget(self.resolutionSpinBox)
        tab5Layout.addWidget(resButton)
        tab5Layout.addWidget(defresButton)



        ############################  TABS LAYOUT
        TabWidget = QTabWidget()
        
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        TabWidget.addTab(C1Widget,QApplication.translate("Tab","HUD",None, QApplication.UnicodeUTF8))

        C2Widget = QWidget()
        C2Widget.setLayout(tab2Layout)
        TabWidget.addTab(C2Widget,QApplication.translate("Tab","Plotter",None, QApplication.UnicodeUTF8))
        
        C3Widget = QWidget()
        C3Widget.setLayout(tab3Layout)
        TabWidget.addTab(C3Widget,QApplication.translate("Tab","Math",None, QApplication.UnicodeUTF8))

        C4Widget = QWidget()
        C4Widget.setLayout(tab4Layout)
        TabWidget.addTab(C4Widget,QApplication.translate("Tab","Sound",None, QApplication.UnicodeUTF8))

        C5Widget = QWidget()
        C5Widget.setLayout(tab5Layout)
        TabWidget.addTab(C5Widget,QApplication.translate("Tab","Style",None, QApplication.UnicodeUTF8))

        
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(cancelButton)
        buttonsLayout.addWidget(okButton)


        #incorporate layouts
        Slayout = QVBoxLayout()
        Slayout.addWidget(self.status,0)
        Slayout.addWidget(TabWidget,1)
        Slayout.addStretch()
        Slayout.addLayout(buttonsLayout)
        
        Slayout.setSizeConstraint(QLayout.SetFixedSize)

        self.setLayout(Slayout)

    def showpidhelp(self):
        QDesktopServices.openUrl(QUrl(u"http://en.wikipedia.org/wiki/PID_controller", QUrl.TolerantMode))        

    def changedpi(self):
        try:
            value = self.resolutionSpinBox.value()
            aw.setdpi(value)
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "changedpi(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))

    def setdefaultres(self):
        self.resolutionSpinBox.setValue(80)
        self.changedpi()

    def showcurvehelp(self):

        string1  = "<UL><LI><b>abs(x)</b> " +  QApplication.translate("MessageBox","Return the absolute value of x.",None, QApplication.UnicodeUTF8)
        string1 += "<LI><b>acos(x)</b> " +     QApplication.translate("MessageBox","Return the arc cosine (measured in radians) of x.",None, QApplication.UnicodeUTF8)   
        string1 += "<LI><b>asin(x)</b> " +     QApplication.translate("MessageBox","Return the arc sine (measured in radians) of x.",None, QApplication.UnicodeUTF8)
        string1 += "<LI><b>atan(x)</b> " +     QApplication.translate("MessageBox","Return the arc tangent (measured in radians) of x.",None, QApplication.UnicodeUTF8) 
        string1 += "<LI><b>cos(x)</b> "  +     QApplication.translate("MessageBox","Return the cosine of x (measured in radians).",None, QApplication.UnicodeUTF8)
        string1 += "<LI><b>degrees(x)</b> " +  QApplication.translate("MessageBox", "Convert angle x from radians to degrees.",None, QApplication.UnicodeUTF8) 
        string1 += "<LI><b>exp(x)</b> " +     QApplication.translate("MessageBox", "Return e raised to the power of x.",None, QApplication.UnicodeUTF8)
        string1 += "<LI><b>log(x[, base])</b> "+ QApplication.translate("MessageBox", "Return the logarithm of x to the given base. ",None, QApplication.UnicodeUTF8) 
        string1 += "<LI><b>log10(x)</b> " +   QApplication.translate("MessageBox", "Return the base 10 logarithm of x.",None, QApplication.UnicodeUTF8) 
        string1 += "<LI><b>pow(x, y)</b> " +   QApplication.translate("MessageBox", "Return x**y (x to the power of y).",None, QApplication.UnicodeUTF8)
        string1 += "<LI><b>radians(x)</b> " +  QApplication.translate("MessageBox", "Convert angle x from degrees to radians.",None, QApplication.UnicodeUTF8) 
        string1 += "<LI><b>sin(x)</b> " +      QApplication.translate("MessageBox", "Return the sine of x (measured in radians).",None, QApplication.UnicodeUTF8)
        string1 += "<LI><b>sqrt(x)</b> " +     QApplication.translate("MessageBox", "Return the square root of x.",None, QApplication.UnicodeUTF8) 
        string1 += "<LI><b>tan(x)</b> " +      QApplication.translate("MessageBox", "Return the tangent of x (measured in radians).",None, QApplication.UnicodeUTF8) 
        string1 += "</UL>"

        string2 = "<UL><LI><b>x</b>" 
        string2 += "<LI><b>Y1</b> " + QApplication.translate("MessageBox", "ET curve",None, QApplication.UnicodeUTF8) 
        string2 += "<LI><b>Y2</b> " +  QApplication.translate("MessageBox", "BT curve",None, QApplication.UnicodeUTF8)
        string2 += "<LI><b>Y3</b> " +  QApplication.translate("MessageBox", "Extra devices #1 curve 1",None, QApplication.UnicodeUTF8) 
        string2 += "<LI><b>Y4</b> " +  QApplication.translate("MessageBox", "Extra devices #1 curve 2",None, QApplication.UnicodeUTF8)
        string2 += "<LI><b>Y5</b> " +  QApplication.translate("MessageBox", "Extra devices #2 curve 1",None, QApplication.UnicodeUTF8)
        string2 += "<LI><b>Y6</b> " +  QApplication.translate("MessageBox", "Extra devices #2 curve 2",None, QApplication.UnicodeUTF8)
        string2 += "</UL>"

        #format help
        string3 = "<TABLE  WIDTH=550><TR><TH>"
        string3 += QApplication.translate("MessageBox",  "MATHEMATICAL FUNCTIONS",None, QApplication.UnicodeUTF8)
        string3 += "</TH><TH>"
        string3 += QApplication.translate("MessageBox",  "SYMBOLIC VARIABLES",None, QApplication.UnicodeUTF8)
        string3 += "</TH></TR><TR><TD NOWRAP>" + string1 + "</TD><TD>" + string2 + "</TD></TR></TABLE>"

        QMessageBox.information(self,QApplication.translate("MessageBox Caption", "Plotter Functions",None, QApplication.UnicodeUTF8),string3)


    def setcurvecolor(self,x):
        try:
            colorf = QColorDialog.getColor(QColor(aw.qmc.plotcurvecolor[x]),self)
            if colorf.isValid():
                colorname = unicode(colorf.name())
                aw.qmc.plotcurvecolor[x] = colorname

            self.plotequ()
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "setcurvecolor(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))

    def setbackgroundequ1(self):
        try:
            equ = unicode(self.equedit1.text())
            aw.qmc.plotcurves[0] = equ
            if len(equ):
                aw.qmc.resetlines()
                #create x range
                x_range = range(aw.qmc.startofx,aw.qmc.endofx)
                #create y range
                y_range = []
                for i in range(len(x_range)):
                    y_range.append(self.eval_curve_expression(equ,x_range[i]))

            aw.qmc.timeB = x_range[:]
            aw.qmc.temp1B = y_range[:]
            aw.qmc.temp2B = [-100]*len(x_range) 
            aw.qmc.background = True
            aw.qmc.redraw()        
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "setbackgroundequ1(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))

    def plotequ(self):
        try:
            EQU = [unicode(self.equedit1.text()),unicode(self.equedit2.text()),
                   unicode(self.equedit3.text()),unicode(self.equedit4.text()),
                   unicode(self.equedit5.text()),unicode(self.equedit6.text())]
            aw.qmc.plotcurves = EQU[:]
            aw.qmc.resetlines()                           
            for e in range(5):
                #create x range
                x_range = range(aw.qmc.startofx,aw.qmc.endofx)
                #create y range
                y_range = []
                for i in range(len(x_range)):
                    y_range.append(self.eval_curve_expression(EQU[e],x_range[i]))
                aw.qmc.ax.plot(x_range, y_range, color=aw.qmc.plotcurvecolor[e], linestyle = '-', linewidth=1)
            aw.qmc.fig.canvas.draw()
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "plotequ(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))

    def eval_curve_expression(self,mathexpression,x):
        if len(mathexpression):
            if mathexpression[0] == "#":
                return
            #Since eval() is very powerful, for security reasons, only the functions in this dictionary will be allowed
            mathdictionary = {"sin":math.sin,"cos":math.cos,"tan":math.tan,"pow":math.pow,"exp":math.exp,"pi":math.pi,"e":math.e,
                              "abs":abs,"acos":math.acos,"asin":math.asin,"atan":math.atan,"log":math.log,"radians":math.radians,
                              "sqrt":math.sqrt,"atan2":math.atan,"degrees":math.degrees}
            try:
                x = float(x)
                mathdictionary['x'] = x         #add x to the math dictionary assigning the key "x" to its float value
                #if Ys in expression
                if "Y" in mathexpression:
                    #extract Ys
                    Yval = []                   #extract value number example Y9 = 9
                    mlen = len(mathexpression)
                    for i in range(mlen):
                        if mathexpression[i] == "Y":
                            #find Y number
                            if i+1 < mlen:                          #check for out of range
                                if mathexpression[i+1].isdigit():
                                    number = mathexpression[i+1]
                                else:
                                    number = "1"
                            #check for double digit
                            if i+2 < mlen:
                                if mathexpression[i+2].isdigit() and mathexpression[i+1].isdigit():
                                    number += mathexpression[i+2]
                            Yval.append(number)
                                
                    #build Ys float values
                    if len(aw.qmc.timex) > 1:
                        index = aw.qmc.time2index(x)
                        Y = [aw.qmc.temp1[index],aw.qmc.temp2[index]]
                        if len(aw.qmc.extratimex):
                            if len(aw.qmc.extratimex[0]):
                                for i in range(len(aw.qmc.extradevices)):
                                    Y.append(aw.qmc.extratemp1[i][index])
                                    Y.append(aw.qmc.extratemp2[i][index])

                        
                        #add Ys and their value to math dictionary 
                        for i in range(len(Yval)):
                            mathdictionary["Y"+ Yval[i]] = Y[int(Yval[i])-1]
                    else:
                        for i in range(len(Yval)):
                            mathdictionary["Y"+ Yval[i]] = 0                    
                                
                return eval(mathexpression,{"__builtins__":None},mathdictionary)
            
            except Exception,e:
                aw.qmc.adderror(QApplication.translate("Error Message", "Plotter: %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
                return 0
        
    def setappearance(self):
        try:
            aw.style = unicode(self.styleComboBox.currentText())
            app.setStyle(aw.style)
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "setappearance(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
        
    def showsound(self):
        try:
            warnings.simplefilter('ignore', Warning) #for Complex warning 
            aw.sendmessage(QApplication.translate("Message Area","Testing Mike...", None, QApplication.UnicodeUTF8))
            aw.stack.setCurrentIndex(2)
            aw.sound.opensound()
            for i in range(80):
                msg = str(80-i)
                self.status.showMessage(msg,500)
                aw.sound.blitsound()
            aw.stack.setCurrentIndex(0)
            aw.sound.closesound()
            aw.sendmessage("")
            warnings.simplefilter('default', Warning)
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "showsound(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
        
             
    def saveinterp(self):
        pass

    def showunivarinfo(self):
        if aw.qmc.timeindex[6]:
            aw.qmc.univariateinfo()
        else:
            self.status.showMessage(QApplication.translate("StatusBar","Need to load a finished profile first", None, QApplication.UnicodeUTF8),5000)     
                   
    def univar(self,i):
        if self.univarCheck.isChecked():
            #check for finished roast
            if aw.qmc.timeindex[6]:
                aw.qmc.univariate()
            else:
                self.status.showMessage(QApplication.translate("StatusBar","Need to load a finished profile first", None, QApplication.UnicodeUTF8),5000)
                self.univarCheck.setChecked(False)               
        else:
            aw.qmc.resetlines()
            aw.qmc.redraw()                

    def interpolation(self,i):
        mode = unicode(self.interpComboBox.currentText())
        if self.interpCheck.isChecked():
            #check for finished roast
            if aw.qmc.timeindex[6]:
                aw.qmc.drawinterp(mode)
            else:
                self.status.showMessage(QApplication.translate("StatusBar","Need to load a finished profile first", None, QApplication.UnicodeUTF8),5000)
                self.interpCheck.setChecked(False)
                
        else:
            aw.qmc.resetlines()
            aw.qmc.redraw()

    def soundset(self,i):
        if aw.soundflag == 0:
            aw.soundflag = 1
            aw.sendmessage(QApplication.translate("Message Area","Sound turned ON", None, QApplication.UnicodeUTF8))
            aw.soundpop()
        else:
            aw.soundflag = 0
            aw.sendmessage(QApplication.translate("Message Area","Sound turned OFF", None, QApplication.UnicodeUTF8))

            
    def changeDeltaET(self,i):
        aw.qmc.DeltaETflag = not aw.qmc.DeltaETflag
        aw.qmc.redraw()

    def changeDeltaFilter(self,i):
        try:
            aw.qmc.deltafilter = self.DeltaFilter.value()
            aw.qmc.redraw()
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "changeDeltaFilter(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
        
    def changeDeltaBT(self,i):
        aw.qmc.DeltaBTflag = not aw.qmc.DeltaBTflag
        aw.qmc.redraw()
        
    def changeProjection(self,i):
        aw.qmc.projectFlag = not aw.qmc.projectFlag
        if not aw.qmc.projectFlag:
            #erase old projections
            aw.qmc.resetlines()    
        
    def changeSensitivity(self):
        try:
            aw.qmc.sensitivity = int(self.sensitivityComboBox.currentText())
            aw.qmc.redraw()
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "changeSensitivity(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
        
    def changeProjectionMode(self,i):
        aw.qmc.projectionmode = i

    def changeInterpolationMode(self,i):
        aw.qmc.resetlines()
        aw.qmc.redraw()
        self.interpolation(i)

    #cancel button
    def close(self):    
        #restore settings
        aw.qmc.DeltaETflag = self.org_DeltaET
        aw.qmc.DeltaBTflag = self.org_DeltaBT
        aw.qmc.sensitivity = self.org_Sensitivity
        aw.qmc.projectFlag = self.org_Projection
        aw.qmc.resetlines()
        aw.qmc.redraw()
        self.accept()

    #button OK
    def updatetargets(self):
        mode = unicode(self.modeComboBox.currentText())
        if mode == QApplication.translate("ComboBox","metrics", None, QApplication.UnicodeUTF8):
            aw.HUDfunction = 0
        elif mode == QApplication.translate("ComboBox","thermal", None, QApplication.UnicodeUTF8):
            aw.HUDfunction = 1
        aw.qmc.ETtarget = int(self.ETlineEdit.text())
        aw.qmc.BTtarget = int(self.BTlineEdit.text())

        aw.qmc.hudETpid[0] = int(self.ETpidP.text())
        aw.qmc.hudETpid[1] = int(self.ETpidI.text())
        aw.qmc.hudETpid[2] = int(self.ETpidD.text())

        string = QApplication.translate("Message Area","[ET target = %1] [BT target =   (%2]", None, QApplication.UnicodeUTF8).arg(unicode(aw.qmc.ETtarget)).arg(unicode(aw.qmc.BTtarget))
        aw.sendmessage(string)
        aw.qmc.resetlines()
        aw.qmc.redraw()
        self.accept()

    #closing dialog
    def closeEvent(self, event):
        self.close()
        self.accept()
        aw.qmc.resetlines()
        aw.qmc.redraw()        
        aw.stack.setCurrentIndex(0)
        
########################################################################################            
#####################  ROAST PROPERTIES EDIT GRAPH DLG  ################################
########################################################################################        
        
class editGraphDlg(QDialog):
    def __init__(self, parent = None):
        super(editGraphDlg,self).__init__(parent)

        self.setModal(True)

        self.setWindowTitle(QApplication.translate("Form Caption","Roast Properties",None, QApplication.UnicodeUTF8))

        regextime = QRegExp(r"^-?[0-5][0-9]:[0-5][0-9]$")
        regexweight = QRegExp(r"^[0-9]{1,3}[.0-9]{1,2}$")

        #MARKERS
        chargelabel  = QLabel("<b>" + QApplication.translate("Label", "CHARGE",None, QApplication.UnicodeUTF8) + "</b>")
        chargelabel.setStyleSheet("background-color:'#f07800';")

        self.chargeedit = QLineEdit(aw.qmc.stringfromseconds(0))
        self.chargeeditcopy = aw.qmc.stringfromseconds(0)
        self.chargeedit.setValidator(QRegExpValidator(regextime,self))
        self.chargeedit.setMaximumWidth(50)
        self.chargeedit.setMinimumWidth(50)
        chargelabel.setBuddy(self.chargeedit)

        drylabel  = QLabel("<b>" + QApplication.translate("Label", "DRY END",None, QApplication.UnicodeUTF8) + "</b>")
        drylabel.setStyleSheet("background-color:'orange';")
        
        if aw.qmc.timeindex[1]:
            t2 = int(aw.qmc.timex[aw.qmc.timeindex[1]]-aw.qmc.timex[aw.qmc.timeindex[0]])
        else:
            t2 = 0
        self.dryedit = QLineEdit(aw.qmc.stringfromseconds(t2))
        self.dryeditcopy = aw.qmc.stringfromseconds(t2)
        self.dryedit.setValidator(QRegExpValidator(regextime,self))
        self.dryedit.setMaximumWidth(50)
        self.dryedit.setMinimumWidth(50)
        drylabel.setBuddy(self.dryedit)
 
        Cstartlabel = QLabel("<b>" + QApplication.translate("Label","FC START",None, QApplication.UnicodeUTF8) + "</b>")
        Cstartlabel.setStyleSheet("background-color:'orange';")
        if aw.qmc.timeindex[2]:
            t3 = int(aw.qmc.timex[aw.qmc.timeindex[2]]-aw.qmc.timex[aw.qmc.timeindex[0]])
        else:
            t3 = 0
        self.Cstartedit = QLineEdit(aw.qmc.stringfromseconds(t3))
        self.Cstarteditcopy = aw.qmc.stringfromseconds(t3)
        self.Cstartedit.setValidator(QRegExpValidator(regextime,self))
        self.Cstartedit.setMaximumWidth(50)
        self.Cstartedit.setMinimumWidth(50)
        Cstartlabel.setBuddy(self.Cstartedit)
        
        Cendlabel = QLabel("<b>" + QApplication.translate("Label","FC END",None, QApplication.UnicodeUTF8) + "</b>")
        Cendlabel.setStyleSheet("background-color:'orange';")
        if aw.qmc.timeindex[3]:
            t4 = int(aw.qmc.timex[aw.qmc.timeindex[3]]-aw.qmc.timex[aw.qmc.timeindex[0]])
        else:
            t4 = 0
        self.Cendedit = QLineEdit(aw.qmc.stringfromseconds(t4))
        self.Cendeditcopy = aw.qmc.stringfromseconds(t4)
        self.Cendedit.setValidator(QRegExpValidator(regextime,self))
        self.Cendedit.setMaximumWidth(50)
        self.Cendedit.setMinimumWidth(50)
        Cendlabel.setBuddy(self.Cendedit)
   
        CCstartlabel = QLabel("<b>" + QApplication.translate("Label","SC START",None, QApplication.UnicodeUTF8) + "</b>")
        CCstartlabel.setStyleSheet("background-color:'orange';")
        if aw.qmc.timeindex[4]:
            t5 = int(aw.qmc.timex[aw.qmc.timeindex[4]]-aw.qmc.timex[aw.qmc.timeindex[0]])
        else:
            t5 = 0
        self.CCstartedit = QLineEdit(aw.qmc.stringfromseconds(t5))
        self.CCstarteditcopy = aw.qmc.stringfromseconds(t5)
        self.CCstartedit.setValidator(QRegExpValidator(regextime,self))
        self.CCstartedit.setMaximumWidth(50)
        self.CCstartedit.setMinimumWidth(50)
        CCstartlabel.setBuddy(self.CCstartedit)

        CCendlabel = QLabel("<b>" + QApplication.translate("Label","SC END",None, QApplication.UnicodeUTF8) + "</b>")
        CCendlabel.setStyleSheet("background-color:'orange';")
        if aw.qmc.timeindex[5]:
            t6 = int(aw.qmc.timex[aw.qmc.timeindex[5]]-aw.qmc.timex[aw.qmc.timeindex[0]])
        else:
            t6 = 0
        self.CCendedit = QLineEdit(aw.qmc.stringfromseconds(t6))
        self.CCendeditcopy = aw.qmc.stringfromseconds(t6)
        self.CCendedit.setValidator(QRegExpValidator(regextime,self))
        self.CCendedit.setMaximumWidth(50)
        self.CCendedit.setMinimumWidth(50)
        CCendlabel.setBuddy(self.CCendedit)
        
        droplabel = QLabel("<b>" + QApplication.translate("Label", "DROP",None, QApplication.UnicodeUTF8) + "</b>")
        droplabel.setStyleSheet("background-color:'#f07800';")
        if aw.qmc.timeindex[6]:
            t7 = int(aw.qmc.timex[aw.qmc.timeindex[6]]-aw.qmc.timex[aw.qmc.timeindex[0]])
        else:
            t7 = 0
        self.dropedit = QLineEdit(aw.qmc.stringfromseconds(t7))
        self.dropeditcopy = aw.qmc.stringfromseconds(t7)
        self.dropedit.setValidator(QRegExpValidator(regextime,self))
        self.dropedit.setMaximumWidth(50)
        self.dropedit.setMinimumWidth(50)
        droplabel.setBuddy(self.dropedit)

        self.roastproperties = QCheckBox(QApplication.translate("CheckBox","Delete Roast properties on Reset", None, QApplication.UnicodeUTF8))
        if aw.qmc.roastpropertiesflag:
            self.roastproperties.setChecked(True)
        else:            self.roastproperties.setChecked(False)
        self.connect(self.roastproperties,SIGNAL("stateChanged(int)"),self.roastpropertiesChanged)  

        # EVENTS
        #table for showing events
        self.eventtable = QTableWidget()
        self.eventtable.setTabKeyNavigation(True)
        self.eventtablecopy = []
        self.createEventTable()

        self.neweventTableButton = QPushButton(QApplication.translate("Button", "Add",None, QApplication.UnicodeUTF8))
        self.neweventTableButton.setFocusPolicy(Qt.NoFocus)
        self.neweventTableButton.setMaximumSize(self.neweventTableButton.sizeHint())
        self.neweventTableButton.setMinimumSize(self.neweventTableButton.minimumSizeHint())
        self.connect(self.neweventTableButton,SIGNAL("clicked()"),self.addEventTable)

        self.deleventTableButton = QPushButton(QApplication.translate("Button", "Delete",None, QApplication.UnicodeUTF8))
        self.deleventTableButton.setFocusPolicy(Qt.NoFocus)
        self.deleventTableButton.setMaximumSize(self.deleventTableButton.sizeHint())
        self.deleventTableButton.setMinimumSize(self.deleventTableButton.minimumSizeHint())
        self.connect(self.deleventTableButton,SIGNAL("clicked()"),self.deleteEventTable)
        

        #DATA Table
        self.datatable = QTableWidget()
        self.datatable.setTabKeyNavigation(True)
        self.createDataTable()        
           
        #TITLE
        titlelabel = QLabel("<b>" + QApplication.translate("Label", "Title",None, QApplication.UnicodeUTF8) + "</b>")
        self.titleedit = QLineEdit(aw.qmc.title)
        #Date
        datelabel1 = QLabel("<b>" + QApplication.translate("Label", "Date",None, QApplication.UnicodeUTF8) + "</b>")
        date = aw.qmc.roastdate.toString()
        dateedit = QLineEdit(date)
        dateedit.setReadOnly(True)
        dateedit.setStyleSheet("background-color:'lightgrey'")

        #Beans
        beanslabel = QLabel("<b>" + QApplication.translate("Label", "Beans",None, QApplication.UnicodeUTF8) + "</b>")
        self.beansedit = QTextEdit()
        self.beansedit.setMaximumHeight(100)

        self.beansedit.setPlainText(QString(aw.qmc.beans))

        #roaster
        self.roaster = QLineEdit(aw.qmc.roastertype)

        #operator
        self.operator = QLineEdit(aw.qmc.operator)
        
        #weight
        weightlabel = QLabel("<b>" + QApplication.translate("Label", "Weight",None, QApplication.UnicodeUTF8) + "</b>")
        weightinlabel = QLabel(QApplication.translate("Label", " in",None, QApplication.UnicodeUTF8))
        weightoutlabel = QLabel(QApplication.translate("Label", " out",None, QApplication.UnicodeUTF8))
        inw = str(aw.qmc.weight[0])
        outw = str(aw.qmc.weight[1])
        self.weightinedit = QLineEdit(inw) 
        
        self.weightinedit.setValidator(QDoubleValidator(0., 9999., 1, self.weightinedit))
        self.weightinedit.setMinimumWidth(55)
        self.weightinedit.setMaximumWidth(55)
        self.weightoutedit = QLineEdit(outw)
        self.weightoutedit.setValidator(QDoubleValidator(0., 9999., 1, self.weightoutedit))
        self.weightoutedit.setMinimumWidth(55)
        self.weightoutedit.setMaximumWidth(55)
        self.weightpercentlabel = QLabel(QApplication.translate("Label", " %",None, QApplication.UnicodeUTF8))
        self.weightpercentlabel.setMinimumWidth(45)
        self.weightpercentlabel.setMaximumWidth(45)
        self.roastdegreelabel = QLabel("")
        self.roastdegreelabel.setMinimumWidth(80)
        self.roastdegreelabel.setMaximumWidth(80)

        self.percent()
        self.connect(self.weightoutedit,SIGNAL("editingFinished()"),self.percent)
        self.connect(self.weightinedit,SIGNAL("editingFinished()"),self.percent)
        
        self.unitsComboBox = QComboBox()
        self.unitsComboBox.setMaximumWidth(60)
        self.unitsComboBox.setMinimumWidth(60)
        self.unitsComboBox.addItems([QApplication.translate("ComboBox", "g", None, QApplication.UnicodeUTF8),
                                     QApplication.translate("ComboBox", "Kg", None, QApplication.UnicodeUTF8)])
        if aw.qmc.weight[2] == QApplication.translate("ComboBox", "g", None, QApplication.UnicodeUTF8):
            self.unitsComboBox.setCurrentIndex(0)
        else:
            self.unitsComboBox.setCurrentIndex(1)
        
        #volume
        volumelabel = QLabel("<b>" + QApplication.translate("Label", "Volume",None, QApplication.UnicodeUTF8) + "</b>")
        volumeinlabel = QLabel(QApplication.translate("Label", " in",None, QApplication.UnicodeUTF8))
        volumeoutlabel = QLabel(QApplication.translate("Label", " out",None, QApplication.UnicodeUTF8))
        inv = str(aw.qmc.volume[0])
        outv = str(aw.qmc.volume[1])
        self.volumeinedit = QLineEdit(inv) 
        
        self.volumeinedit.setValidator(QDoubleValidator(0., 9999., 1, self.volumeinedit))
        self.volumeinedit.setMinimumWidth(55)
        self.volumeinedit.setMaximumWidth(55)
        self.volumeoutedit = QLineEdit(outv)
        self.volumeoutedit.setValidator(QDoubleValidator(0., 9999., 1, self.volumeoutedit))
        self.volumeoutedit.setMinimumWidth(55)
        self.volumeoutedit.setMaximumWidth(55)
        self.volumepercentlabel = QLabel(QApplication.translate("Label", " %",None, QApplication.UnicodeUTF8))
        self.volumepercentlabel.setMinimumWidth(45)
        self.volumepercentlabel.setMaximumWidth(45)

        self.volume_percent()
        self.connect(self.volumeoutedit,SIGNAL("editingFinished()"),self.volume_percent)
        self.connect(self.volumeinedit,SIGNAL("editingFinished()"),self.volume_percent)
        
        self.volumeUnitsComboBox = QComboBox()
        self.volumeUnitsComboBox.setMaximumWidth(60)
        self.volumeUnitsComboBox.setMinimumWidth(60)
        self.volumeUnitsComboBox.addItems([QApplication.translate("ComboBox", "ml",None, QApplication.UnicodeUTF8),
                                           QApplication.translate("ComboBox", "l",None, QApplication.UnicodeUTF8)])        
        if aw.qmc.volume[2] == QApplication.translate("ComboBox", "ml",None, QApplication.UnicodeUTF8):
            self.volumeUnitsComboBox.setCurrentIndex(0)
        else:
            self.volumeUnitsComboBox.setCurrentIndex(1)
                        
        self.calculateddensitylabel = QLabel("")
        self.connect(self.weightoutedit,SIGNAL("editingFinished()"),self.calculated_density)
        self.connect(self.weightinedit,SIGNAL("editingFinished()"),self.calculated_density)
        self.connect(self.volumeoutedit,SIGNAL("editingFinished()"),self.calculated_density)
        self.connect(self.volumeinedit,SIGNAL("editingFinished()"),self.calculated_density)
        self.connect(self.volumeUnitsComboBox,SIGNAL("currentIndexChanged(int)"),self.calculated_density)
        self.connect(self.unitsComboBox,SIGNAL("currentIndexChanged(int)"),self.calculated_density)

        #density
        bean_density_label = QLabel("<b>" + QApplication.translate("Label", "Density",None, QApplication.UnicodeUTF8) + "</b>")
        self.bean_density_weight_edit = QLineEdit(str(aw.qmc.density[0]))
        self.bean_density_weight_edit.setValidator(QDoubleValidator(0., 9999., 1,self.bean_density_weight_edit))
        self.bean_density_weight_edit.setMinimumWidth(55)
        self.bean_density_weight_edit.setMaximumWidth(55)
        self.bean_density_weightUnitsComboBox = QComboBox()
        self.bean_density_weightUnitsComboBox.setMaximumWidth(60)
        self.bean_density_weightUnitsComboBox.setMinimumWidth(60)
        self.bean_density_weightUnitsComboBox.addItems([QApplication.translate("ComboBox", "g",None, QApplication.UnicodeUTF8),
                                                        QApplication.translate("ComboBox", "Kg",None, QApplication.UnicodeUTF8)])        
        if aw.qmc.density[1] == QApplication.translate("ComboBox", "g",None, QApplication.UnicodeUTF8):
            self.bean_density_weightUnitsComboBox.setCurrentIndex(0)
        else:
            self.bean_density_weightUnitsComboBox.setCurrentIndex(1)
        bean_density_per_label = QLabel(QApplication.translate("Label", "per",None, QApplication.UnicodeUTF8))
        self.bean_density_volume_edit = QLineEdit(str(aw.qmc.density[2]))
        self.bean_density_volume_edit.setValidator(QDoubleValidator(0., 9999., 1,self.bean_density_volume_edit))
        self.bean_density_volume_edit.setMinimumWidth(55)
        self.bean_density_volume_edit.setMaximumWidth(55)
        self.bean_density_volumeUnitsComboBox = QComboBox()
        self.bean_density_volumeUnitsComboBox.setMaximumWidth(60)
        self.bean_density_volumeUnitsComboBox.setMinimumWidth(60)
        self.bean_density_volumeUnitsComboBox.addItems([QApplication.translate("ComboBox", "ml",None, QApplication.UnicodeUTF8),
                                                        QApplication.translate("ComboBox", "l",None, QApplication.UnicodeUTF8)])        
        if aw.qmc.density[3] == QApplication.translate("ComboBox", "ml",None, QApplication.UnicodeUTF8):
            self.bean_density_volumeUnitsComboBox.setCurrentIndex(0)
        else:
            self.bean_density_volumeUnitsComboBox.setCurrentIndex(1)

        self.standarddensitylabel = QLabel("")
        self.standard_density()
        self.connect(self.bean_density_volume_edit,SIGNAL("editingFinished()"),self.standard_density)
        self.connect(self.bean_density_weight_edit,SIGNAL("editingFinished()"),self.standard_density)


        #bag humidity
        bag_humidity_label = QLabel("<b>" + QApplication.translate("Label", "Storage Humidity",None, QApplication.UnicodeUTF8) + "</b>")
        bag_humidity_unitslabel = QLabel(aw.qmc.mode)
        bag_humidity_unit_label = QLabel(QApplication.translate("Label", "%",None, QApplication.UnicodeUTF8))
        self.humidity_edit = QLineEdit()
        self.humidity_edit.setText(unicode(aw.qmc.bag_humidity[0]))
        self.humidity_edit.setMaximumWidth(50)
        self.humidity_edit.setValidator(QDoubleValidator(0., 100., 1, self.humidity_edit))
        bag_humidity_at_label = QLabel(QApplication.translate("Label", "at",None, QApplication.UnicodeUTF8))
        self.bag_temp_edit = QLineEdit( )
        self.bag_temp_edit.setText(unicode(aw.qmc.bag_humidity[1]))
        self.bag_temp_edit.setMaximumWidth(50)
        self.bag_temp_edit.setValidator(QDoubleValidator(0., 200., 1, self.bag_temp_edit))
        self.bag_humiditity_tempUnitsComboBox = QComboBox()
        self.bag_humiditity_tempUnitsComboBox.setMaximumWidth(60)
        self.bag_humiditity_tempUnitsComboBox.setMinimumWidth(60)
        

        #Ambient temperature (uses display mode as unit (F or C)
        ambientlabel = QLabel("<b>" + QApplication.translate("Label", "Ambient Temperature",None, QApplication.UnicodeUTF8) + "</b>")
        ambientunitslabel = QLabel(aw.qmc.mode)
        self.ambientedit = QLineEdit( )
        self.ambientedit.setText(unicode( aw.qmc.ambientTemp))
        self.ambientedit.setMaximumWidth(50)
        self.ambientedit.setValidator(QDoubleValidator(0., 200., 1, self.ambientedit))        
        self.ambientedit_tempUnitsComboBox = QComboBox()
        self.ambientedit_tempUnitsComboBox.setMaximumWidth(60)
        self.ambientedit_tempUnitsComboBox.setMinimumWidth(60)
  
        # NOTES
        roastertypelabel = QLabel()
        roastertypelabel.setText("<b>" + QApplication.translate("Label", "Roaster",None, QApplication.UnicodeUTF8) + "</b>")

        operatorlabel = QLabel()
        operatorlabel.setText("<b>" + QApplication.translate("Label", "Operator",None, QApplication.UnicodeUTF8) + "</b>")

        roastinglabel = QLabel("<b>" + QApplication.translate("Label", "Roasting Notes",None, QApplication.UnicodeUTF8) + "</b>")
        self.roastingeditor = QTextEdit()
        self.roastingeditor.setPlainText(QString(aw.qmc.roastingnotes))

        cuppinglabel = QLabel("<b>" + QApplication.translate("Label", "Cupping Notes",None, QApplication.UnicodeUTF8) + "</b>")
        self.cuppingeditor =  QTextEdit()
        self.cuppingeditor.setPlainText(QString(aw.qmc.cuppingnotes))
        

        # Save button
        saveButton = QPushButton(QApplication.translate("Button", "OK",None, QApplication.UnicodeUTF8))
        self.connect(saveButton, SIGNAL("clicked()"),self, SLOT("accept()"))
        #the size of Buttons on the Mac is too small with 70,30 and ok with sizeHint/minimumSizeHint
        saveButton.setMaximumSize(saveButton.sizeHint())
        saveButton.setMinimumSize(saveButton.minimumSizeHint()) 
        
        #Cancel Button
        cancelButton = QPushButton(QApplication.translate("Button", "Cancel",None, QApplication.UnicodeUTF8))
        cancelButton.setFocusPolicy(Qt.NoFocus)
        self.connect(cancelButton, SIGNAL("clicked()"),self, SLOT("reject()"))
        #cancelButton.setMaximumSize(70, 30)
        cancelButton.setMaximumSize(cancelButton.sizeHint())
        cancelButton.setMinimumSize(cancelButton.minimumSize())

        ##### LAYOUTS

        timeLayout = QGridLayout()
        timeLayout.addWidget(chargelabel,0,0)
        timeLayout.addWidget(drylabel,0,1)
        timeLayout.addWidget(Cstartlabel,0,2)
        timeLayout.addWidget(Cendlabel,0,3)
        timeLayout.addWidget(CCstartlabel,0,4)
        timeLayout.addWidget(CCendlabel,0,5)
        timeLayout.addWidget(droplabel,0,6)
        timeLayout.addWidget(self.chargeedit,1,0)
        timeLayout.addWidget(self.dryedit,1,1)
        timeLayout.addWidget(self.Cstartedit,1,2)
        timeLayout.addWidget(self.Cendedit,1,3)
        timeLayout.addWidget(self.CCstartedit,1,4)
        timeLayout.addWidget(self.CCendedit,1,5)
        timeLayout.addWidget(self.dropedit,1,6)
        
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
        weightLayout.addWidget(weightlabel)
        weightLayout.addSpacing(18)
        weightLayout.addWidget(self.unitsComboBox)
        weightLayout.addSpacing(15)
        weightLayout.addWidget(self.weightinedit)
        weightLayout.addSpacing(1)
        weightLayout.addWidget(weightinlabel)
        weightLayout.addSpacing(15)
        weightLayout.addWidget(self.weightoutedit)
        weightLayout.addSpacing(1)
        weightLayout.addWidget(weightoutlabel)
        weightLayout.addSpacing(15)
        weightLayout.addWidget(self.weightpercentlabel)  
        weightLayout.addSpacing(10)
        weightLayout.addWidget(self.roastdegreelabel)  
        weightLayout.addStretch()  

        volumeLayout = QHBoxLayout()
        volumeLayout.setSpacing(0)
        volumeLayout.addWidget(volumelabel)
        volumeLayout.addSpacing(14)
        volumeLayout.addWidget(self.volumeUnitsComboBox)
        volumeLayout.addSpacing(15)
        volumeLayout.addWidget(self.volumeinedit)
        volumeLayout.addSpacing(1)
        volumeLayout.addWidget(volumeinlabel)
        volumeLayout.addSpacing(15)
        volumeLayout.addWidget(self.volumeoutedit)
        volumeLayout.addSpacing(1)
        volumeLayout.addWidget(volumeoutlabel)
        volumeLayout.addSpacing(15)
        volumeLayout.addWidget(self.volumepercentlabel)  
        volumeLayout.addStretch()  

        densityLayout = QHBoxLayout()
        densityLayout.setSpacing(0)
        densityLayout.addWidget(bean_density_label)
        densityLayout.addSpacing(13)
        densityLayout.addWidget(self.bean_density_weightUnitsComboBox)
        densityLayout.addSpacing(15)
        densityLayout.addWidget(self.bean_density_weight_edit)
        densityLayout.addSpacing(15)
        densityLayout.addWidget(bean_density_per_label)
        densityLayout.addSpacing(15)
        densityLayout.addWidget(self.bean_density_volumeUnitsComboBox)
        densityLayout.addSpacing(15)
        densityLayout.addWidget(self.bean_density_volume_edit)
        densityLayout.addSpacing(20)
        densityLayout.addWidget(self.standarddensitylabel)
        densityLayout.addStretch()  
        
        humidityLayout = QHBoxLayout()
        humidityLayout.addWidget(bag_humidity_label)
        humidityLayout.addWidget(self.humidity_edit)
        humidityLayout.addWidget(bag_humidity_unit_label)
        humidityLayout.addSpacing(15)
        humidityLayout.addWidget(bag_humidity_at_label)
        humidityLayout.addSpacing(15)
        humidityLayout.addWidget(self.bag_temp_edit)
        humidityLayout.addWidget(bag_humidity_unitslabel)
        humidityLayout.addStretch()
        
        ambientLayout = QHBoxLayout()
        ambientLayout.addWidget(ambientlabel)
        ambientLayout.addWidget(self.ambientedit)
        ambientLayout.addWidget(ambientunitslabel)
        ambientLayout.addStretch()
  	
        anotationLayout = QVBoxLayout()
        anotationLayout.addWidget(roastinglabel)
        anotationLayout.addWidget(self.roastingeditor)
        anotationLayout.addWidget(cuppinglabel)
        anotationLayout.addWidget(self.cuppingeditor)

        okLayout = QHBoxLayout()        
        okLayout.addStretch()
        okLayout.addWidget(cancelButton,0)
        okLayout.addWidget(saveButton,1)
        okLayout.setContentsMargins(0, 0, 0, 0) # left, top, right, bottom       

        timeLayoutBox = QHBoxLayout()
        timeLayoutBox.addLayout(timeLayout)
        timeLayoutBox.addStretch()
        
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(timeLayoutBox)
        
        timeGroupLayout = QGroupBox(QApplication.translate("GroupBox", "Times",None, QApplication.UnicodeUTF8))
        timeGroupLayout.setLayout(mainLayout)

        eventbuttonLayout = QHBoxLayout()
        eventbuttonLayout.addStretch()  
        eventbuttonLayout.addWidget(self.deleventTableButton)
        eventbuttonLayout.addWidget(self.neweventTableButton)

        #tab 1
        self.tab1aLayout = QVBoxLayout()
        self.tab1aLayout.addWidget(timeGroupLayout)
        self.tab1aLayout.addLayout(textLayout)
        self.tab1aLayout.addLayout(weightLayout)
        self.tab1aLayout.addLayout(volumeLayout)
        self.tab1aLayout.addLayout(densityLayout)
        tab1bLayout = QVBoxLayout()
        tab1bLayout.addLayout(humidityLayout)
        tab1bLayout.addLayout(ambientLayout)
        tab1bLayout.addStretch()  
        tab1Layout = QVBoxLayout()
        tab1Layout.setContentsMargins(5, 0, 5, 0) # left, top, right, bottom
        tab1Layout.setMargin(0)
        tab1Layout.addLayout(self.tab1aLayout)
        tab1Layout.addLayout(tab1bLayout)
        tab1Layout.addWidget(self.roastproperties)
        
        self.calculated_density()


        #tab 2
        tab2Layout = QVBoxLayout()
        tab2Layout.addLayout(anotationLayout)
        tab2Layout.setContentsMargins(5, 0, 5, 0) # left, top, right, bottom
        tab2Layout.setMargin(0)
 
        #tab3 events
        tab3Layout = QVBoxLayout()
        tab3Layout.addWidget(self.eventtable)
        tab3Layout.addLayout(eventbuttonLayout)
        tab3Layout.setContentsMargins(5, 0, 5, 0) # left, top, right, bottom
        tab3Layout.setMargin(0)

        #tab 4 data
        tab4Layout = QVBoxLayout()
        tab4Layout.addWidget(self.datatable) 
        tab4Layout.setContentsMargins(5, 0, 5, 0) # left, top, right, bottom 
        tab4Layout.setMargin(0)      
        
        #tabwidget
        self.TabWidget = QTabWidget()
        
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        self.TabWidget.addTab(C1Widget,QApplication.translate("Tab", "General",None, QApplication.UnicodeUTF8))
        
        C2Widget = QWidget()
        C2Widget.setLayout(tab2Layout)
        self.TabWidget.addTab(C2Widget,QApplication.translate("Tab", "Notes",None, QApplication.UnicodeUTF8))

        C3Widget = QWidget()
        C3Widget.setLayout(tab3Layout)
        self.TabWidget.addTab(C3Widget,QApplication.translate("Tab", "Events",None, QApplication.UnicodeUTF8))

        C4Widget = QWidget()
        C4Widget.setLayout(tab4Layout)
        self.TabWidget.addTab(C4Widget,QApplication.translate("Tab", "Data",None, QApplication.UnicodeUTF8))
        
        #incorporate layouts
        totallayout = QVBoxLayout()
        totallayout.addWidget(self.TabWidget)
        totallayout.addLayout(okLayout)        
        totallayout.setMargin(10)      

        #totallayout.addStretch()
        #totallayout.addLayout(buttonsLayout)
               
        self.setLayout(totallayout)

    def roastpropertiesChanged(self):
        if self.roastproperties.isChecked():
            aw.qmc.roastpropertiesflag = 1
        else:
            aw.qmc.roastpropertiesflag = 0

    def createDataTable(self):
        self.datatable.clear()
        ndata = len(aw.qmc.timex)
        self.datatable.setRowCount(ndata)
        self.datatable.setColumnCount(6)
        self.datatable.setHorizontalHeaderLabels([QApplication.translate("Table", "Abs Time",None, QApplication.UnicodeUTF8),
                                                  QApplication.translate("Table", "Rel Time",None, QApplication.UnicodeUTF8),
                                                  QApplication.translate("Table", "ET",None, QApplication.UnicodeUTF8),
                                                  QApplication.translate("Table", "BT",None, QApplication.UnicodeUTF8),
                                                  QApplication.translate("Table", "DeltaBT (d/m)",None, QApplication.UnicodeUTF8),
                                                  QApplication.translate("Table", "DeltaET (d/m)",None, QApplication.UnicodeUTF8)])
        self.datatable.setAlternatingRowColors(True)
        self.datatable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.datatable.setSelectionBehavior(QTableWidget.SelectRows)
        self.datatable.setSelectionMode(QTableWidget.SingleSelection)
        self.datatable.setShowGrid(True)
        for i in range(ndata):
            Atime = QTableWidgetItem("%.03f"%aw.qmc.timex[i])
            Rtime = QTableWidgetItem(aw.qmc.stringfromseconds(int(round(aw.qmc.timex[i]-aw.qmc.timex[aw.qmc.timeindex[0]]))))
            ET = QTableWidgetItem("%.02f"%aw.qmc.temp1[i])
            BT = QTableWidgetItem("%.02f"%aw.qmc.temp2[i])
            if i > 1 and (aw.qmc.timex[i]-aw.qmc.timex[i-1]):
                deltaET = QTableWidgetItem("%.02f"%(60*(aw.qmc.temp1[i]-aw.qmc.temp1[i-1])/(aw.qmc.timex[i]-aw.qmc.timex[i-1])))
                deltaBT = QTableWidgetItem("%.02f"%(60*(aw.qmc.temp2[i]-aw.qmc.temp2[i-1])/(aw.qmc.timex[i]-aw.qmc.timex[i-1])))
            else:
                deltaET = QTableWidgetItem("00:00")
                deltaBT = QTableWidgetItem("00:00")
            if i:                
                    #identify by color and add notation
                if i == aw.qmc.timeindex[0]:
                    Rtime.setBackgroundColor(QColor('#f07800'))
                    text = QApplication.translate("Table", "%1 START",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                    Rtime.setText(text)
                elif i == aw.qmc.timeindex[1]:
                    Rtime.setBackgroundColor(QColor('orange'))
                    text = QApplication.translate("Table", "%1 DRY END",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                    Rtime.setText(text)
                elif i == aw.qmc.timeindex[2]:
                    Rtime.setBackgroundColor(QColor('orange'))
                    text = QApplication.translate("Table", "%1 FC START",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                    Rtime.setText(text)
                elif i == aw.qmc.timeindex[3]:
                    Rtime.setBackgroundColor(QColor('orange'))
                    text = QApplication.translate("Table", "%1 FC END",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                    Rtime.setText(text)
                elif i == aw.qmc.timeindex[4]:
                    Rtime.setBackgroundColor(QColor('orange'))
                    text = QApplication.translate("Table", "%1 SC START",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                    Rtime.setText(text)
                elif i == aw.qmc.timeindex[5]:
                    Rtime.setBackgroundColor(QColor('orange'))
                    text = QApplication.translate("Table", "%1 SC END",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                    Rtime.setText(text)
                elif i == aw.qmc.timeindex[6]:
                    Rtime.setBackgroundColor(QColor('#f07800'))
                    text = QApplication.translate("Table", "%1 END",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                    Rtime.setText(text)
                    
            if i in aw.qmc.specialevents:
                    Rtime.setBackgroundColor(QColor('yellow'))
                    index = aw.qmc.specialevents.index(i)
                    text = QApplication.translate("Table", "%1 EVENT #%2 %3%4",None, QApplication.UnicodeUTF8).arg(Rtime.text()).arg(str(index+1)).arg(aw.qmc.etypes[aw.qmc.specialeventstype[index]][0]).arg(str(aw.qmc.specialeventsvalue[index]-1))
                    Rtime.setText(text)
                
            self.datatable.setItem(i,0,Atime) 
            self.datatable.setItem(i,1,Rtime)
            self.datatable.setItem(i,2,ET)
            self.datatable.setItem(i,3,BT)
            self.datatable.setItem(i,4,deltaBT)
            self.datatable.setItem(i,5,deltaET)
            
    def createEventTable(self):
        self.eventtable.clear()
        nevents = len(aw.qmc.specialevents)        
        self.eventtable.setRowCount(nevents)
        self.eventtable.setColumnCount(4)
        self.eventtable.setHorizontalHeaderLabels([QApplication.translate("Table", "Time", None, QApplication.UnicodeUTF8),
                                                   QApplication.translate("Table", "Description", None, QApplication.UnicodeUTF8),
                                                   QApplication.translate("Table", "Type", None, QApplication.UnicodeUTF8),
                                                   QApplication.translate("Table", "Value", None, QApplication.UnicodeUTF8)])
        self.eventtable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.eventtable.setSelectionBehavior(QTableWidget.SelectRows)
        self.eventtable.setSelectionMode(QTableWidget.SingleSelection)
        regextime = QRegExp(r"^-?[0-5][0-9]:[0-5][0-9]$")
        self.eventtable.setShowGrid(True) 
        #populate table
        for i in range(nevents):
            #create widgets
            typeComboBox = QComboBox()
            typeComboBox.addItems(aw.qmc.etypes)
            typeComboBox.setCurrentIndex(aw.qmc.specialeventstype[i])
            valueComboBox = QComboBox()
            valueComboBox.addItems(aw.qmc.eventsvalues)
            valueComboBox.setCurrentIndex(aw.qmc.specialeventsvalue[i])
            timeline = QLineEdit()
            timez = aw.qmc.stringfromseconds(int(aw.qmc.timex[aw.qmc.specialevents[i]]-aw.qmc.timex[aw.qmc.timeindex[0]]))
            self.eventtablecopy.append(unicode(timez)) 
            timeline.setText(timez)
            timeline.setValidator(QRegExpValidator(regextime,self))
            stringline = QLineEdit(aw.qmc.specialeventsStrings[i])

            #add widgets to the table
            self.eventtable.setCellWidget(i,0,timeline)
            self.eventtable.setCellWidget(i,1,stringline)
            self.eventtable.setCellWidget(i,2,typeComboBox)
            self.eventtable.setCellWidget(i,3,valueComboBox)

    def saveEventTable(self):
        nevents  = self.eventtable.rowCount() 
        for i in range(nevents):
            timez = self.eventtable.cellWidget(i,0)
            if self.eventtablecopy[i] !=  unicode(timez.text()):
                aw.qmc.specialevents[i] = aw.qmc.time2index(aw.qmc.timex[aw.qmc.timeindex[0]]+ aw.qmc.stringtoseconds(unicode(timez.text())))                
            description = self.eventtable.cellWidget(i,1)
            aw.qmc.specialeventsStrings[i] = unicode(description.text())
            etype = self.eventtable.cellWidget(i,2)
            aw.qmc.specialeventstype[i] = etype.currentIndex()
            evalue = self.eventtable.cellWidget(i,3)            
            aw.qmc.specialeventsvalue[i] = evalue.currentIndex()

    def addEventTable(self):
        if len(aw.qmc.timex):
            aw.qmc.specialevents.append(len(aw.qmc.timex)-1)   #qmc.specialevents holds indexes in qmx.timex. Initialize event index
            aw.qmc.specialeventstype.append(0)
            aw.qmc.specialeventsStrings.append(str(len(aw.qmc.specialevents)))
            aw.qmc.specialeventsvalue.append(0)
            self.createEventTable()
            aw.qmc.redraw()

            message = QApplication.translate("Message Area","Event #%1 added", None, QApplication.UnicodeUTF8).arg(str(len(aw.qmc.specialevents))) 
            aw.sendmessage(message)
        else:
            message = QApplication.translate("Message Area","No profile found", None, QApplication.UnicodeUTF8)
            aw.sendmessage(message)            
            
    def deleteEventTable(self):
        if len(aw.qmc.specialevents):
             aw.qmc.specialevents.pop()
             aw.qmc.specialeventstype.pop()
             aw.qmc.specialeventsStrings.pop()
             aw.qmc.specialeventsvalue.pop()
             self.createEventTable()
             aw.qmc.redraw()
             
             message = QApplication.translate("Message Area"," Event #%1 deleted", None, QApplication.UnicodeUTF8).arg(str(len(aw.qmc.specialevents)+1))
             aw.sendmessage(message)
        else:
             message = QApplication.translate("Message Area","No events found", None, QApplication.UnicodeUTF8)  
             aw.sendmessage(message)            
             
    def percent(self):
        if float(self.weightoutedit.text()) != 0.0:
            percent = aw.weight_loss(float(self.weightinedit.text()),float(self.weightoutedit.text()))
        else:
            percent = 0.
        percentstring =  "%.1f" %(percent) + "%"
        self.weightpercentlabel.setText(QString(percentstring))    #weight percent loss
        roastdegreestring = ""
        if percent > 0.:
            roastdegreestring = aw.roast_degree(percent)
        self.roastdegreelabel.setText(QString(roastdegreestring))
        
    def volume_percent(self):
        if float(self.volumeoutedit.text()) != 0.0:
            percent = aw.weight_loss(float(self.volumeoutedit.text()),float(self.volumeinedit.text()))
        else:
            percent = 0.
        percentstring =  "%.1f" %(percent) + "%"
        self.volumepercentlabel.setText(QString(percentstring))    #volume percent gain
        
    def calculated_density(self):
        volumein = float(self.volumeinedit.text())
        volumeout = float(self.volumeoutedit.text())
        weightin = float(self.weightinedit.text())
        weightout = float(self.weightoutedit.text())
        if volumein != 0.0 and volumeout and weightin != 0.0 and weightout != 0.0:
            if self.volumeUnitsComboBox.currentText() == QApplication.translate("ComboBox","ml", None, QApplication.UnicodeUTF8) :
                volumein = volumein / 1000.0
                volumeout = volumeout / 1000.0      
            if self.unitsComboBox.currentText() != QApplication.translate("ComboBox","g", None, QApplication.UnicodeUTF8) :
                weightin = weightin * 1000.0
                weightout = weightout * 1000.0
            din = (weightin / volumein) 
            dout = (weightout / volumeout)
            if din > 1 and dout > 1:
                self.calculateddensitylabel.setText(QApplication.translate("Label","                 Density in: %1  g/l   =>   Density out: %2 g/l", None, QApplication.UnicodeUTF8).arg(din).arg(dout))                
                self.tab1aLayout.addWidget(self.calculateddensitylabel)
            else:
                self.calculateddensitylabel.setText("")
                self.tab1aLayout.removeWidget(self.calculateddensitylabel)
        else:
            self.calculateddensitylabel.setText("")
            self.tab1aLayout.removeWidget(self.calculateddensitylabel)
        
    def standard_density(self):
        volume = float(self.bean_density_volume_edit.text())
        weight = float(self.bean_density_weight_edit.text())
        if volume != 0.0 and weight != 0.0:
            if self.bean_density_volumeUnitsComboBox.currentText() == QApplication.translate("ComboBox","ml", None, QApplication.UnicodeUTF8) :
                volume = volume / 1000.0
            if self.bean_density_weightUnitsComboBox.currentText() != QApplication.translate("ComboBox","g", None, QApplication.UnicodeUTF8) :
                weight = weight * 1000.0
            self.standarddensitylabel.setText(QApplication.translate("Label","(%1 g/l)", None, QApplication.UnicodeUTF8).arg((weight / volume)))
        else:
            self.standarddensitylabel.setText("")
        
                
    def accept(self):
        #check for graph
        if len(aw.qmc.timex):   
            # check CHARGE (with index aw.qmc.timeindex[0])
            if aw.qmc.timeindex[0] == -1:
                aw.qmc.timeindex[0] = 0
                start = 0                   #relative start time
            else:
                start = aw.qmc.timex[aw.qmc.timeindex[0]]
            
            if self.chargeeditcopy != unicode(self.chargeedit.text()):
                if aw.qmc.stringtoseconds(unicode(self.chargeedit.text())) > 0:
                    startindex = aw.qmc.time2index( aw.qmc.stringtoseconds(unicode(self.chargeedit.text())))
                    aw.qmc.timeindex[0] = startindex
                    aw.qmc.xaxistosm()
            if self.dryeditcopy != unicode(self.dryedit.text()):
                if aw.qmc.stringtoseconds(unicode(self.dryedit.text())) > 0:
                    dryindex = aw.qmc.time2index( start + aw.qmc.stringtoseconds(unicode(self.dryedit.text())))
                    aw.qmc.timeindex[1] = dryindex
            if self.Cstarteditcopy != unicode(self.Cstartedit.text()):
                if aw.qmc.stringtoseconds(unicode(self.Cstartedit.text())) > 0:
                    fcsindex = aw.qmc.time2index( start + aw.qmc.stringtoseconds(unicode(self.Cstartedit.text())))
                    aw.qmc.timeindex[2] = fcsindex
            if self.Cendeditcopy != unicode(self.Cendedit.text()):
                if aw.qmc.stringtoseconds(unicode(self.Cendedit.text())) > 0:
                    fceindex = aw.qmc.time2index( start + aw.qmc.stringtoseconds(unicode(self.Cendedit.text())))
                    aw.qmc.timeindex[3] = fceindex
            if self.CCstarteditcopy != unicode(self.CCstartedit.text()):
                if aw.qmc.stringtoseconds(unicode(self.CCstartedit.text())) > 0:
                    scsindex = aw.qmc.time2index( start + aw.qmc.stringtoseconds(unicode(self.CCstartedit.text())))
                    aw.qmc.timeindex[4] = scsindex
            if self.CCendeditcopy != unicode(self.CCendedit.text()):        
                if aw.qmc.stringtoseconds(unicode(self.CCendedit.text())) > 0:
                    sceindex = aw.qmc.time2index( start + aw.qmc.stringtoseconds(unicode(self.CCendedit.text())))
                    aw.qmc.timeindex[5] = sceindex
            if self.dropeditcopy != unicode(self.dropedit.text()):
                if aw.qmc.stringtoseconds(unicode(self.dropedit.text())) > 0:
                    dropindex = aw.qmc.time2index( start + aw.qmc.stringtoseconds(unicode(self.dropedit.text())))
                    aw.qmc.timeindex[6] = dropindex

            if aw.qmc.phasesbuttonflag:   
                # adjust phases by DryEnd and FCs events
                if aw.qmc.timeindex[1]:
                    aw.qmc.phases[1] = int(round(aw.qmc.temp2[aw.qmc.timeindex[1]]))  
                if aw.qmc.timeindex[2]:
                    aw.qmc.phases[2] = int(round(aw.qmc.temp2[aw.qmc.timeindex[2]]))                                                   

            
            self.saveEventTable()


        # Update Title
        aw.qmc.ax.set_title(unicode(self.titleedit.text()),size=20,color=aw.qmc.palette["title"])
        aw.qmc.title = unicode(self.titleedit.text())
        # Update beans
        aw.qmc.beans = unicode(self.beansedit.toPlainText())
        #update roaster
        aw.qmc.roaster = unicode(self.roaster.text())

        #update weight
        try:
            aw.qmc.weight[0] = float(self.weightinedit.text())
        except:
            aw.qmc.weight[0] = 0
        try:
            aw.qmc.weight[1] = float(self.weightoutedit.text())
        except:
            aw.qmc.weight[1] = 0
        aw.qmc.weight[2] = unicode(self.unitsComboBox.currentText())
        
        #update volume
        try:
            aw.qmc.volume[0] = float(self.volumeinedit.text())
        except:
            aw.qmc.volume[0] = 0
        try:
            aw.qmc.volume[1] = float(self.volumeoutedit.text())
        except:
            aw.qmc.volume[1] = 0
        aw.qmc.volume[2] = unicode(self.volumeUnitsComboBox.currentText())

        #update density
        try:
            aw.qmc.density[0] = float(self.bean_density_weight_edit.text())
        except:
            aw.qmc.density[0] = 0
        aw.qmc.density[1] = unicode(self.bean_density_weightUnitsComboBox.currentText())
        try:
            aw.qmc.density[2] = float(self.bean_density_volume_edit.text())
        except: 
            aw.qmc.density[2] = 0
        aw.qmc.density[3] = unicode(self.bean_density_volumeUnitsComboBox.currentText())

        #update humidity
        try:
            aw.qmc.bag_humidity[0] = float(self.humidity_edit.text())
        except:
            aw.qmc.bag_humidity[0] = 0
        try:
            aw.qmc.bag_humidity[1] = float(self.bag_temp_edit.text())
        except:
            aw.qmc.bag_humidity[1] = 0

    	#update ambient temperature
        try:
            aw.qmc.ambientTemp = float(unicode(self.ambientedit.text()))
        except:
            aw.qmc.ambientTemp = 0
         
        #update notes
        aw.qmc.roastertype = unicode(self.roaster.text())
        aw.qmc.operator = unicode(self.operator.text())
        aw.qmc.roastingnotes = unicode(self.roastingeditor.toPlainText())
        aw.qmc.cuppingnotes = unicode(self.cuppingeditor.toPlainText())
           
        aw.sendmessage(QApplication.translate("Message Area","Roast properties updated but profile not saved to disk", None, QApplication.UnicodeUTF8))            
        aw.qmc.redraw()
        self.close()




##########################################################################
#####################  VIEW ERROR LOG DLG  ###############################
##########################################################################

        
class errorDlg(QDialog):
    def __init__(self, parent = None):
        super(errorDlg,self).__init__(parent)
        self.setWindowTitle(QApplication.translate("Form Caption","Error Log", None, QApplication.UnicodeUTF8))

        #convert list of errors to an html string
        htmlerr = "version = " +__version__ +"<br><br>"
        for i in range(len(aw.qmc.errorlog)):
            htmlerr += "<b>" + str(len(aw.qmc.errorlog)-i) + "</b> <i>" + aw.qmc.errorlog[-i-1] + "</i><br><br>"

        enumber = len(aw.qmc.errorlog)
    
        labelstr =  "<b>"+ QApplication.translate("Label","Number of errors found %1", None, QApplication.UnicodeUTF8).arg(unicode(enumber)) + "</b>"

        elabel = QLabel(labelstr)
        errorEdit = QTextEdit()
        errorEdit.setHtml(htmlerr)
        errorEdit.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(elabel,0)
        layout.addWidget(errorEdit,1)
                               
        self.setLayout(layout)

##########################################################################
#####################  MESSAGE HISTORY DLG  ##############################
##########################################################################
        
class messageDlg(QDialog):
    def __init__(self, parent = None):
        super(messageDlg,self).__init__(parent)
        self.setWindowTitle(QApplication.translate("Form Caption","Message History", None, QApplication.UnicodeUTF8))

        #convert list of messages to an html string
        htmlmessage = ""
        for i in range(len(aw.messagehist)):
            htmlmessage += "<b>" + str(len(aw.messagehist)-i) + "</b> <i>" + aw.messagehist[-i-1] + "</i><br><br>"

        linenumber = len(aw.messagehist)
        labelstr =  QApplication.translate("Label", "Last stacked messages",None, QApplication.UnicodeUTF8)
        mlabel = QLabel(labelstr)
        messageEdit = QTextEdit()
        messageEdit.setHtml(htmlmessage)
        messageEdit.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(mlabel,0)
        layout.addWidget(messageEdit,1)
                               
        self.setLayout(layout)


##########################################################################
#####################  AUTOSAVE DLG  #####################################
##########################################################################
        
class autosaveDlg(QDialog):
    def __init__(self, parent = None):
        super(autosaveDlg,self).__init__(parent)        
        self.setModal(True)
        self.setWindowTitle(QApplication.translate("Form Caption","Keyboard Autosave [s]", None, QApplication.UnicodeUTF8))
        
        self.prefixEdit = QLineEdit(aw.qmc.autosaveprefix)
        self.prefixEdit.setToolTip(QApplication.translate("Tooltip", "Automatic generated name = This text + date + time",None, QApplication.UnicodeUTF8))

        self.autocheckbox = QCheckBox(QApplication.translate("CheckBox","Autosave [s]", None, QApplication.UnicodeUTF8))
        self.autocheckbox.setToolTip(QApplication.translate("Tooltip", "ON/OFF of automatic saving when pressing keyboard letter [s]",None, QApplication.UnicodeUTF8))
        
        if aw.qmc.autosaveflag:
            self.autocheckbox.setChecked(True)
        else:
            self.autocheckbox.setChecked(False)

        okButton = QPushButton(QApplication.translate("Button","OK", None, QApplication.UnicodeUTF8))  
        cancelButton = QPushButton(QApplication.translate("Button","Cancel", None, QApplication.UnicodeUTF8))
        cancelButton.setFocusPolicy(Qt.NoFocus)

        pathButton = QPushButton(QApplication.translate("Button","Path", None, QApplication.UnicodeUTF8))        
        pathButton.setFocusPolicy(Qt.NoFocus)
        self.pathEdit = QLineEdit(unicode(aw.qmc.autosavepath))
        self.pathEdit.setToolTip(QApplication.translate("Tooltip", "Sets the directory to store batch profiles when using the letter [s]",None, QApplication.UnicodeUTF8))
        
        self.connect(cancelButton,SIGNAL("clicked()"),self.close)        
        self.connect(okButton,SIGNAL("clicked()"),self.autoChanged)  
        self.connect(pathButton,SIGNAL("clicked()"),self.getpath)  

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()  
        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(okButton)
        
        autolayout = QGridLayout()
        autolayout.addWidget(self.autocheckbox,0,0)
        autolayout.addWidget(self.prefixEdit,0,1)
        autolayout.addWidget(pathButton,1,0)
        autolayout.addWidget(self.pathEdit,1,1)
        
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(autolayout)
        mainLayout.addStretch()
        mainLayout.addLayout(buttonLayout)
        
        self.setLayout(mainLayout)

    def getpath(self):
        filename = aw.ArtisanExistingDirectoryDialog(msg=QApplication.translate("Form Caption","AutoSave Path", None, QApplication.UnicodeUTF8))
        self.pathEdit.setText(filename)
        
    def autoChanged(self):
        if self.autocheckbox.isChecked(): 
            aw.qmc.autosaveflag = 1
            aw.qmc.autosaveprefix = self.prefixEdit.text()

            message = QApplication.translate("Message Area","Autosave ON. Prefix: %1").arg(self.prefixEdit.text())
            aw.sendmessage(message)
            aw.qmc.autosavepath = unicode(self.pathEdit.text())
        else:
            aw.qmc.autosaveflag = 0
            message = QApplication.translate("Message Area","Autosave OFF", None, QApplication.UnicodeUTF8)
            aw.sendmessage(message)            
        self.close()
        
##########################################################################
#####################  WINDOW PROPERTIES DLG  ############################
##########################################################################
        
class WindowsDlg(QDialog):
    def __init__(self, parent = None):
        super(WindowsDlg,self).__init__(parent)
        self.setWindowTitle(QApplication.translate("Form Caption","Axes",None, QApplication.UnicodeUTF8))
        
        self.setModal(True)

        ylimitLabel = QLabel(QApplication.translate("Label", "Max",None, QApplication.UnicodeUTF8))
        ylimitLabel_min = QLabel(QApplication.translate("Label", "Min",None, QApplication.UnicodeUTF8))
        xlimitLabel = QLabel(QApplication.translate("Label", "Max",None, QApplication.UnicodeUTF8))
        xlimitLabel_min = QLabel(QApplication.translate("Label", "Min",None, QApplication.UnicodeUTF8))
        self.ylimitEdit = QLineEdit()
        self.ylimitEdit.setMaximumWidth(100)
        self.ylimitEdit_min = QLineEdit()
        self.ylimitEdit_min.setMaximumWidth(100)
        
        self.xlimitEdit = QLineEdit()
        self.xlimitEdit.setMaximumWidth(100)        
        self.xlimitEdit_min = QLineEdit()
        self.xlimitEdit_min.setMaximumWidth(100)        

        self.ylimitEdit.setValidator(QIntValidator(0, 1000, self.ylimitEdit))
        self.ylimitEdit_min.setValidator(QIntValidator(-1000, 1000, self.ylimitEdit_min))
        regextime = QRegExp(r"^[0-5][0-9]:[0-5][0-9]$")
        self.xlimitEdit.setValidator(QRegExpValidator(regextime,self))
        self.xlimitEdit_min.setValidator(QRegExpValidator(regextime,self))

        self.ylimitEdit.setText(unicode(aw.qmc.ylimit))
        self.ylimitEdit_min.setText(unicode(aw.qmc.ylimit_min))
        self.xlimitEdit.setText(aw.qmc.stringfromseconds(aw.qmc.endofx))
        self.xlimitEdit_min.setText(aw.qmc.stringfromseconds(aw.qmc.startofx))

        xrotationlabel = QLabel(QApplication.translate("Label", "Rotation",None, QApplication.UnicodeUTF8))
        self.xrotationSpinBox = QSpinBox()
        self.xrotationSpinBox.setRange(0,90)
        self.xrotationSpinBox.setSingleStep(5)
        self.xrotationSpinBox.setValue(aw.qmc.xrotation)
        self.connect(self.xrotationSpinBox, SIGNAL("valueChanged(int)"),self.changexrotation)
        self.xrotationSpinBox.setMaximumWidth(40)

        self.legendComboBox = QComboBox()
        self.legendComboBox.setMaximumWidth(160)
        legendlocs = [QApplication.translate("ComboBox", "upper right",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "upper left",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "lower left",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "lower right",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "right",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "center left",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "center right",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "lower center",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "upper center",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "center",None, QApplication.UnicodeUTF8)]
        self.legendComboBox.addItems(legendlocs)
        self.legendComboBox.setCurrentIndex(aw.qmc.legendloc-1)
        self.connect(self.legendComboBox,SIGNAL("currentIndexChanged(int)"),self.changelegendloc)

        self.timeflag = QCheckBox(QApplication.translate("CheckBox", "Keep Max time after RESET",None, QApplication.UnicodeUTF8))
        if aw.qmc.keeptimeflag:
            self.timeflag.setChecked(True)
        else:
            self.timeflag.setChecked(False)

        timegridlabel = QLabel(QApplication.translate("Label", "Step",None, QApplication.UnicodeUTF8))
        self.xaxislencombobox = QComboBox()
        timelocs =   [QApplication.translate("ComboBox", "30 seconds",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "1 minute",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "2 minute",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "3 minute",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "4 minute",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "5 minute",None, QApplication.UnicodeUTF8)]
        self.xaxislencombobox.addItems(timelocs)
        self.timeconversion = [30,60,120,180,240,300]
        self.xaxislencombobox.setCurrentIndex(self.timeconversion.index(aw.qmc.xgrid))
        self.connect(self.xaxislencombobox,SIGNAL("currentIndexChanged(int)"),self.xaxislenloc)

        ygridlabel = QLabel(QApplication.translate("Label", "Step",None, QApplication.UnicodeUTF8))
        self.ygridSpinBox = QSpinBox()
        self.ygridSpinBox.setRange(5,100)
        self.ygridSpinBox.setSingleStep(5)
        self.ygridSpinBox.setValue (aw.qmc.ygrid)
        self.connect(self.ygridSpinBox, SIGNAL("valueChanged(int)"),self.changeygrid)
        self.ygridSpinBox.setMaximumWidth(40)

        linestylegridlabel = QLabel(QApplication.translate("Label", "Style",None, QApplication.UnicodeUTF8))
        self.gridstylecombobox = QComboBox()
        gridstyles = [QApplication.translate("ComboBox", "solid",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "dashed",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "dashed-dot",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "dotted",None, QApplication.UnicodeUTF8),
                      QApplication.translate("ComboBox", "None",None, QApplication.UnicodeUTF8)]
        self.gridstylecombobox.addItems(gridstyles) 
        self.gridstylecombobox.setCurrentIndex(aw.qmc.gridlinestyle)
        self.connect(self.gridstylecombobox,SIGNAL("currentIndexChanged(int)"),self.changegridstyle)

        gridthicknesslabel = QLabel(QApplication.translate("Label", "Width",None, QApplication.UnicodeUTF8))
        self.gridwidthSpinBox = QSpinBox()
        self.gridwidthSpinBox.setRange(1,5)
        self.gridwidthSpinBox.setValue(aw.qmc.gridthickness)
        self.connect(self.gridwidthSpinBox, SIGNAL("valueChanged(int)"),self.changegridwidth)
        self.gridwidthSpinBox.setMaximumWidth(40)       

        gridalphalabel = QLabel(QApplication.translate("Label", "Opaqueness",None, QApplication.UnicodeUTF8))
        self.gridalphaSpinBox = QSpinBox()
        self.gridalphaSpinBox.setRange(1,10)
        self.gridalphaSpinBox.setValue(int(aw.qmc.gridalpha*10))
        self.connect(self.gridalphaSpinBox, SIGNAL("valueChanged(int)"),self.changegridalpha)
        self.gridalphaSpinBox.setMaximumWidth(40)
        
        okButton = QPushButton(QApplication.translate("Button","OK",None, QApplication.UnicodeUTF8))  
        cancelButton = QPushButton(QApplication.translate("Button","Cancel",None, QApplication.UnicodeUTF8))
        cancelButton.setFocusPolicy(Qt.NoFocus)
        resetButton = QPushButton(QApplication.translate("Button","Defaults",None, QApplication.UnicodeUTF8))
        resetButton.setFocusPolicy(Qt.NoFocus)

        self.connect(cancelButton,SIGNAL("clicked()"),self.close)
        self.connect(okButton,SIGNAL("clicked()"),self.updatewindow)
        self.connect(resetButton,SIGNAL("clicked()"),self.reset)
        
        xlayout = QGridLayout()
        xlayout.addWidget(xlimitLabel_min,0,0)
        xlayout.addWidget(self.xlimitEdit_min,0,1)
        xlayout.addWidget(xlimitLabel,0,2)
        xlayout.addWidget(self.xlimitEdit,0,3)
        xlayout.addWidget(timegridlabel,1,0)
        xlayout.addWidget(self.xaxislencombobox,1,1)
        xlayout.addWidget(self.timeflag,1,3)
        xlayout.addWidget(xrotationlabel,2,0)
        xlayout.addWidget( self.xrotationSpinBox,2,1)
        
        ylayout = QGridLayout()
        ylayout.addWidget(ylimitLabel_min,0,0)
        ylayout.addWidget(self.ylimitEdit_min,0,1)
        ylayout.addWidget(ylimitLabel,0,2)
        ylayout.addWidget(self.ylimitEdit,0,3)
        ylayout.addWidget(ygridlabel,1,0)
        ylayout.addWidget(self.ygridSpinBox,1,1)
        
        legentlayout = QHBoxLayout()
        legentlayout.addWidget(self.legendComboBox,0,Qt.AlignLeft)
                                     
        graphgridlayout = QGridLayout() 
        graphgridlayout.addWidget(linestylegridlabel,1,0)
        graphgridlayout.addWidget(self.gridstylecombobox,1,1,Qt.AlignLeft)
        graphgridlayout.addWidget(gridthicknesslabel,1,2)
        graphgridlayout.addWidget(self.gridwidthSpinBox,1,3,Qt.AlignLeft)
        graphgridlayout.addWidget(gridalphalabel,2,0)
        graphgridlayout.addWidget(self.gridalphaSpinBox,2,1,Qt.AlignLeft)
        
        xGroupLayout = QGroupBox(QApplication.translate("GroupBox","Time Axis",None, QApplication.UnicodeUTF8))
        xGroupLayout.setLayout(xlayout)
        yGroupLayout = QGroupBox(QApplication.translate("GroupBox","Temperature Axis",None, QApplication.UnicodeUTF8))
        yGroupLayout.setLayout(ylayout)                                     
        legendLayout = QGroupBox(QApplication.translate("GroupBox","Legend Location",None, QApplication.UnicodeUTF8))
        legendLayout.setLayout(legentlayout)
        GridGroupLayout = QGroupBox(QApplication.translate("GroupBox","Grid",None, QApplication.UnicodeUTF8))
        GridGroupLayout.setLayout(graphgridlayout)       
                                     
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(resetButton)
        buttonLayout.addStretch()  
        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(okButton)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(xGroupLayout)
        mainLayout.addWidget(yGroupLayout)
        mainLayout.addWidget(legendLayout)
        mainLayout.addWidget(GridGroupLayout)
                                     
        mainLayout.addStretch()
        mainLayout.addLayout(buttonLayout)
        
        self.setLayout(mainLayout)

    def changexrotation(self):
        aw.qmc.xrotation = self.xrotationSpinBox.value()
        aw.qmc.xaxistosm()       
        aw.qmc.redraw()    	

    def changegridalpha(self):
        aw.qmc.gridalpha = self.gridalphaSpinBox.value()/10.
        aw.qmc.redraw()
        
    def changegridwidth(self):
        aw.qmc.gridthickness = self.gridwidthSpinBox.value()
        aw.qmc.redraw()
        
    def changegridstyle(self):
        aw.qmc.gridlinestyle = self.gridstylecombobox.currentIndex()
        aw.qmc.redraw()

    def changelegendloc(self):
        aw.qmc.legendloc = self.legendComboBox.currentIndex() + 1
        aw.qmc.redraw()

    def xaxislenloc(self):
        aw.qmc.xgrid = self.timeconversion[self.xaxislencombobox.currentIndex()]
        aw.qmc.xaxistosm()       
        aw.qmc.redraw()

    def changeygrid(self):
        aw.qmc.ygrid = self.ygridSpinBox.value()
        aw.qmc.redraw()
                               
    def updatewindow(self):
        aw.qmc.ylimit = int(self.ylimitEdit.text())
        aw.qmc.ylimit_min = int(self.ylimitEdit_min.text())
        aw.qmc.endofx = aw.qmc.stringtoseconds(unicode(self.xlimitEdit.text()))     
        aw.qmc.startofx = aw.qmc.stringtoseconds(unicode(self.xlimitEdit_min.text()))
        if self.timeflag.isChecked():
            aw.qmc.keeptimeflag = 1
        else:
            aw.qmc.keeptimeflag = 0

        aw.qmc.redraw()
        
        string = QApplication.translate("Message Area","ylimit = (%1,%2) xlimit = (%3,%4)",None, QApplication.UnicodeUTF8).arg(unicode(self.ylimitEdit_min.text())).arg(unicode(self.ylimitEdit.text())).arg(unicode(self.xlimitEdit_min.text())).arg(unicode(self.xlimitEdit.text()))                                        
        aw.sendmessage(string)

        self.close()
        
    def reset(self):
        self.xlimitEdit.setText(aw.qmc.stringfromseconds(60))
        self.xlimitEdit_min.setText(aw.qmc.stringfromseconds(0))
        if aw.qmc.mode == u"F":
            self.ylimitEdit.setText(u"750")
            self.ylimitEdit_min.setText(u"0")
        else:
            self.ylimitEdit.setText(u"400")
            self.ylimitEdit_min.setText(u"0")

##########################################################################
#####################  ROAST CALCULATOR DLG   ############################
##########################################################################
        
class calculatorDlg(QDialog):
    def __init__(self, parent = None):
        super(calculatorDlg,self).__init__(parent)
        self.setWindowTitle(QApplication.translate("Form Caption","Roast Calculator",None, QApplication.UnicodeUTF8))
       
        #RATE OF CHANGE
        self.result1 = QLabel(QApplication.translate("Label", "Enter two times along profile",None, QApplication.UnicodeUTF8))
        self.result2 = QLabel()
        self.result2.setStyleSheet("background-color:'lightgrey';")

        startlabel = QLabel(QApplication.translate("Label", "Start (00:00)",None, QApplication.UnicodeUTF8))
        endlabel = QLabel(QApplication.translate("Label", "End (00:00)",None, QApplication.UnicodeUTF8))
        self.startEdit = QLineEdit()
        self.endEdit = QLineEdit()
        regextime = QRegExp(r"^[0-5][0-9]:[0-5][0-9]$")
        self.startEdit.setValidator(QRegExpValidator(regextime,self))
        self.endEdit.setValidator(QRegExpValidator(regextime,self))
        
        self.connect(self.startEdit,SIGNAL("editingFinished()"),self.calculateRC)
        self.connect(self.endEdit,SIGNAL("editingFinished()"),self.calculateRC)

        nevents = len(aw.qmc.specialevents)
        events_found = [QApplication.translate("ComboBox","Event #0",None, QApplication.UnicodeUTF8)]
        for i in range(nevents):
            events_found.append(QApplication.translate("ComboBox","Event #%1",None, QApplication.UnicodeUTF8).arg(str(i+1)))
            
        self.eventAComboBox = QComboBox()
        self.eventAComboBox.addItems(events_found)
        self.connect(self.eventAComboBox,SIGNAL("currentIndexChanged(int)"),self.calcEventRC)

        self.eventBComboBox = QComboBox()
        self.eventBComboBox.addItems(events_found)
        self.connect(self.eventBComboBox,SIGNAL("currentIndexChanged(int)"),self.calcEventRC)


        #TEMPERATURE CONVERSION
        flabel = QLabel(QApplication.translate("Label", "Fahrenheit",None, QApplication.UnicodeUTF8))
        clabel = QLabel(QApplication.translate("Label", "Celsius",None, QApplication.UnicodeUTF8))
        self.faEdit = QLineEdit()
        self.ceEdit = QLineEdit()                
        self.faEdit.setValidator(QDoubleValidator(-999., 9999., 2, self.faEdit))
        self.ceEdit.setValidator(QDoubleValidator(-999., 9999., 2, self.ceEdit))
        self.connect(self.faEdit,SIGNAL("editingFinished()"),lambda x="FtoC":self.convertTemp(x))
        self.connect(self.ceEdit,SIGNAL("editingFinished()"),lambda x="CtoF":self.convertTemp(x))

        #WEIGHT CONVERSION
        self.WinComboBox = QComboBox()
        weightunits = [QApplication.translate("ComboBox","g",None, QApplication.UnicodeUTF8),
                       QApplication.translate("ComboBox","Kg",None, QApplication.UnicodeUTF8),
                       QApplication.translate("ComboBox","lb",None, QApplication.UnicodeUTF8)]
        self.WinComboBox.addItems(weightunits)
        self.WinComboBox.setMaximumWidth(80)
        self.WinComboBox.setMinimumWidth(80)
        self.WoutComboBox = QComboBox()
        self.WoutComboBox.setMaximumWidth(80)
        self.WoutComboBox.setMinimumWidth(80)
        self.WoutComboBox.addItems(weightunits)
        self.WoutComboBox.setCurrentIndex(2)
        self.WinEdit = QLineEdit()
        self.WoutEdit = QLineEdit()
        self.WinEdit.setMaximumWidth(70)
        self.WoutEdit.setMaximumWidth(70)
        #self.WinEdit.setMinimumWidth(60)
        #self.WoutEdit.setMinimumWidth(60)
        self.WinEdit.setValidator(QDoubleValidator(0., 99999., 2, self.WinEdit))
        self.WoutEdit.setValidator(QDoubleValidator(0., 99999., 2, self.WoutEdit))
        self.connect(self.WinEdit,SIGNAL("editingFinished()"),lambda x="ItoO":self.convertWeight(x))
        self.connect(self.WoutEdit,SIGNAL("editingFinished()"),lambda x="OtoI":self.convertWeight(x))

        #VOLUME CONVERSION
        self.VinComboBox = QComboBox()
        volumeunits = [QApplication.translate("ComboBox","liter",None, QApplication.UnicodeUTF8),
                       QApplication.translate("ComboBox","gallon",None, QApplication.UnicodeUTF8),
                       QApplication.translate("ComboBox","quart",None, QApplication.UnicodeUTF8),
                       QApplication.translate("ComboBox","pint",None, QApplication.UnicodeUTF8),
                       QApplication.translate("ComboBox","cup",None, QApplication.UnicodeUTF8),
                       QApplication.translate("ComboBox","cm^3",None, QApplication.UnicodeUTF8)]
        self.VinComboBox.addItems(volumeunits )
        self.VinComboBox.setMaximumWidth(80)
        self.VinComboBox.setMinimumWidth(80)
        self.VoutComboBox = QComboBox()
        self.VoutComboBox.setMaximumWidth(80)
        self.VoutComboBox.setMinimumWidth(80)
        self.VoutComboBox.addItems(volumeunits )
        self.VoutComboBox.setCurrentIndex(4)
        self.VinEdit = QLineEdit()
        self.VoutEdit = QLineEdit()
        self.VinEdit.setMaximumWidth(70)
        self.VoutEdit.setMaximumWidth(70)
        #self.VinEdit.setMinimumWidth(60)
        #self.VoutEdit.setMinimumWidth(60)
        self.VinEdit.setValidator(QDoubleValidator(0., 99999., 2, self.VinEdit))
        self.VoutEdit.setValidator(QDoubleValidator(0., 99999., 2, self.VoutEdit))
        self.connect(self.VinEdit,SIGNAL("editingFinished()"),lambda x="ItoO":self.convertVolume(x))
        self.connect(self.VoutEdit,SIGNAL("editingFinished()"),lambda x="OtoI":self.convertVolume(x))
        
        #LAYOUTS
        #Rate of chage
        calrcLayout = QGridLayout()
        calrcLayout.addWidget(startlabel,0,0)
        calrcLayout.addWidget(endlabel,0,1)
        calrcLayout.addWidget(self.startEdit,1,0)
        calrcLayout.addWidget(self.endEdit,1,1)
        calrcLayout.addWidget(self.eventAComboBox ,2,0)
        calrcLayout.addWidget(self.eventBComboBox ,2,1)
        
        
        rclayout = QVBoxLayout()
        rclayout.addWidget(self.result1,0)
        rclayout.addWidget(self.result2,1)
        rclayout.addLayout(calrcLayout,2)


        #temperature conversion
        tempLayout = QGridLayout()        
        tempLayout.addWidget(flabel,0,0)
        tempLayout.addWidget(clabel,0,1)
        tempLayout.addWidget(self.faEdit,1,0)
        tempLayout.addWidget(self.ceEdit,1,1)

        #weight conversions
        weightLayout = QHBoxLayout()
        weightLayout.addWidget(self.WinComboBox)
        weightLayout.addWidget(self.WinEdit)
        weightLayout.addWidget(self.WoutEdit)
        weightLayout.addWidget(self.WoutComboBox)

        #volume conversions
        volumeLayout = QHBoxLayout()
        volumeLayout.addWidget(self.VinComboBox)
        volumeLayout.addWidget(self.VinEdit)
        volumeLayout.addWidget(self.VoutEdit)
        volumeLayout.addWidget(self.VoutComboBox)


        RoCGroup = QGroupBox(QApplication.translate("GroupBox","Rate of Change",None, QApplication.UnicodeUTF8))
        RoCGroup.setLayout(rclayout)
        
        tempConvGroup = QGroupBox(QApplication.translate("GroupBox","Temperature Conversion",None, QApplication.UnicodeUTF8))
        tempConvGroup.setLayout(tempLayout)
        
        weightConvGroup = QGroupBox(QApplication.translate("GroupBox","Weight Conversion",None, QApplication.UnicodeUTF8))
        weightConvGroup.setLayout(weightLayout)

        volumeConvGroup = QGroupBox(QApplication.translate("GroupBox","Volume Conversion",None, QApplication.UnicodeUTF8))
        volumeConvGroup.setLayout(volumeLayout)

        #main
        mainlayout = QVBoxLayout()
        mainlayout.setSpacing(10)
        mainlayout.addWidget(RoCGroup)
        mainlayout.addWidget(tempConvGroup)
        mainlayout.addWidget(weightConvGroup)
        mainlayout.addWidget(volumeConvGroup)
        mainlayout.addStretch()  
        
        self.setLayout(mainlayout)

    def calcEventRC(self):
        nevents = len(aw.qmc.specialevents)
        Aevent = int(self.eventAComboBox.currentIndex())
        Bevent = int(self.eventBComboBox.currentIndex())
        if Aevent <= nevents and Bevent <= nevents and Aevent and Bevent:
            if aw.qmc.timeindex[0] != -1:
                start = aw.qmc.timex[aw.qmc.timeindex[0]]
            else:
                start = 0
            self.startEdit.setText(aw.qmc.stringfromseconds(aw.qmc.timex[aw.qmc.specialevents[Aevent-1]] - start))        
            self.endEdit.setText(aw.qmc.stringfromseconds(aw.qmc.timex[aw.qmc.specialevents[Bevent-1]] - start))
            self.calculateRC()

    
    #calculate rate of change        
    def calculateRC(self):
        if len(aw.qmc.timex)>2:
            if not len(self.startEdit.text()) or not len(self.endEdit.text()):
                #empty field
                return
            starttime = aw.qmc.stringtoseconds(unicode(self.startEdit.text()))
            endtime = aw.qmc.stringtoseconds(unicode(self.endEdit.text()))

            if starttime == -1 or endtime == -1:
                self.result1.setText(QApplication.translate("Label", "Time syntax error. Time not valid",None, QApplication.UnicodeUTF8))
                self.result2.setText("")
                return

            if  endtime > aw.qmc.timex[-1] or endtime < starttime:
                self.result1.setText(QApplication.translate("Label", "Error: End time smaller than Start time",None, QApplication.UnicodeUTF8))
                self.result2.setText("")
                return
            
            if aw.qmc.timeindex[0] != -1:
                start = aw.qmc.timex[aw.qmc.timeindex[0]]
            else:
                start = 0
                
            startindex = aw.qmc.time2index(starttime + start)
            endindex = aw.qmc.time2index(endtime + start)
            
            
            #delta
            deltatime = aw.qmc.timex[endindex] -  aw.qmc.timex[startindex]
            deltatemperature = aw.qmc.temp2[endindex] - aw.qmc.temp2[startindex]
            if deltatime == 0:
                deltaseconds = 0
            else:
                deltaseconds = deltatemperature/deltatime
            deltaminutes = deltaseconds*60.
        
            string1 = QApplication.translate("Label", "Best approximation was made from %1 to %2",None, QApplication.UnicodeUTF8).arg(aw.qmc.stringfromseconds(aw.qmc.timex[startindex]- start)).arg(aw.qmc.stringfromseconds(aw.qmc.timex[endindex]- start))
            string2 = QApplication.translate("Label", "deg/sec = %1    deg/min = <b>%2<\b>",None, QApplication.UnicodeUTF8).arg(u"%.2f"%(deltaseconds)).arg(u"%.2f"%(deltaminutes))
            
            self.result1.setText(string1)        
            self.result2.setText(string2)

##            #plot visual line
##            if aw.qmc.designerflag == False:
##                aw.qmc.resetlines()
##                aw.qmc.ax.plot([aw.qmc.timex[startindex],aw.qmc.timex[endindex]],[aw.qmc.temp2[startindex],aw.qmc.temp2[endindex]],
##                                color = aw.qmc.palette["grid"],marker = "^",linestyle="--",markersize=8, linewidth=3, alpha = .7)
##                aw.qmc.fig.canvas.draw()            
        else:
            self.result1.setText(QApplication.translate("Label", "No profile found",None, QApplication.UnicodeUTF8))  
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
                        [453.591999,   0.45359237, 1.                ]     # lb
                    ]
        
        if x == "ItoO":
           inx = float(unicode(self.WinEdit.text()))
           outx = inx*convtable[self.WinComboBox.currentIndex()][self.WoutComboBox.currentIndex()]
           self.WoutEdit.setText(u"%.2f"%outx)
            
        elif x == "OtoI":
           outx = float(unicode(self.WoutEdit.text()))
           inx = outx*convtable[self.WoutComboBox.currentIndex()][self.WinComboBox.currentIndex()]
           self.WinEdit.setText(u"%.2f"%inx)

    def convertVolume(self,x):
                        #liter          gal             qt              pt              cup             cm^3
        convtable = [
                        [1.,            0.26417205,     1.05668821,     2.11337643,     4.22675284,     1000.                ],    # liter
                        [3.78541181,    1.,             4.,             8.,             16,             3785.4117884         ],    # gallon
                        [0.94635294,    0.25,           1.,             2.,             4.,             946.352946           ],    # quart
                        [0.47317647,    0.125,          0.5,            1.,             2.,             473.176473           ],    # pint
                        [0.23658823,    0.0625,         0.25,           0.5,            1.,             236.5882365          ],    # cup
                        [0.001,         2.6417205e-4,   1.05668821e-3,  2.11337641e-3,  4.2267528e-3,   1.                   ]     # cm^3          
                    ]
        
        if x == "ItoO":
           inx = float(unicode(self.VinEdit.text()))
           outx = inx*convtable[self.VinComboBox.currentIndex()][self.VoutComboBox.currentIndex()]
           self.VoutEdit.setText(u"%.3f"%outx)
            
        elif x == "OtoI":
           outx = float(unicode(self.VoutEdit.text()))
           inx = outx*convtable[self.VoutComboBox.currentIndex()][self.VinComboBox.currentIndex()]
           self.VinEdit.setText(u"%.3f"%inx)
       
  
##########################################################################
#####################  EVENTS CONFIGURATION DLG     ######################
##########################################################################
#accessed through menu conf
        
class EventsDlg(QDialog):
    def __init__(self, parent = None):
        super(EventsDlg,self).__init__(parent)

        self.setWindowTitle(QApplication.translate("Form Caption","Events",None, QApplication.UnicodeUTF8))
        self.setModal(True)

        ## TAB 1
        self.eventsbuttonflag = QCheckBox(QApplication.translate("CheckBox","Button",None, QApplication.UnicodeUTF8))
        if aw.eventsbuttonflag:
            self.eventsbuttonflag.setChecked(True)
        else:
            self.eventsbuttonflag.setChecked(False)
        self.connect(self.eventsbuttonflag,SIGNAL("stateChanged(int)"),self.eventsbuttonflagChanged)  

        self.eventsshowflagbox = QCheckBox(QApplication.translate("CheckBox","Show",None, QApplication.UnicodeUTF8))
        if aw.qmc.eventsshowflag:
            self.eventsshowflagbox.setChecked(True)
        else:
            self.eventsshowflagbox.setChecked(False)
        self.connect(self.eventsshowflagbox,SIGNAL("stateChanged(int)"),self.eventsshowflagChanged)  

        
        self.minieventsflag = QCheckBox(QApplication.translate("CheckBox","Mini Editor",None, QApplication.UnicodeUTF8))
        self.minieventsflag.setToolTip(QApplication.translate("Tooltip","Allows to enter a description of the last event",None, QApplication.UnicodeUTF8))
        if aw.minieventsflag:
            self.minieventsflag.setChecked(True)
        else:
            self.minieventsflag.setChecked(False)
        self.connect(self.minieventsflag,SIGNAL("stateChanged(int)"),self.minieventsflagChanged)
        
        self.eventsGraphflag = QCheckBox(QApplication.translate("CheckBox","Type Bars",None, QApplication.UnicodeUTF8))
        if aw.qmc.eventsGraphflag:
            self.eventsGraphflag.setChecked(True)
        else:
            self.eventsGraphflag.setChecked(False)
        self.connect(self.eventsGraphflag,SIGNAL("stateChanged(int)"),self.eventsGraphflagChanged)

        typelabel1 = QLabel(QApplication.translate("Label", "1",None, QApplication.UnicodeUTF8))
        typelabel2 = QLabel(QApplication.translate("Label", "2",None, QApplication.UnicodeUTF8))
        typelabel3 = QLabel(QApplication.translate("Label", "3",None, QApplication.UnicodeUTF8))
        typelabel4 = QLabel(QApplication.translate("Label", "4",None, QApplication.UnicodeUTF8))
        
        self.etype0 = QLineEdit(aw.qmc.etypes[0])
        self.etype1 = QLineEdit(aw.qmc.etypes[1])
        self.etype2 = QLineEdit(aw.qmc.etypes[2])
        self.etype3 = QLineEdit(aw.qmc.etypes[3])
        
        okButton = QPushButton(QApplication.translate("Button","OK",None, QApplication.UnicodeUTF8))  
        closeButton = QPushButton(QApplication.translate("Button","Cancel",None, QApplication.UnicodeUTF8))
        defaultButton = QPushButton(QApplication.translate("Button","Defaults",None, QApplication.UnicodeUTF8))
        okButton.setMaximumWidth(100)
        #closeButton.setMaximumWidth(100)
        #defaultButton.setMaximumWidth(100)
        closeButton.setFocusPolicy(Qt.NoFocus)
        defaultButton.setFocusPolicy(Qt.NoFocus)
        
        self.connect(closeButton,SIGNAL("clicked()"),self, SLOT("reject()"))
        self.connect(okButton,SIGNAL("clicked()"),self.updatetypes)
        self.connect(defaultButton,SIGNAL("clicked()"),self.settypedefault)

        ###  TAB 2
        #table for showing events
        self.eventbuttontable = QTableWidget()
        self.eventbuttontable.setTabKeyNavigation(True)
        self.createEventbuttonTable()

        addButton = QPushButton(QApplication.translate("Button","Add",None, QApplication.UnicodeUTF8))
        addButton.setToolTip(QApplication.translate("Tooltip","Add new extra Event button",None, QApplication.UnicodeUTF8))
        #addButton.setMaximumWidth(100)
        addButton.setFocusPolicy(Qt.NoFocus)
        self.connect(addButton, SIGNAL("clicked()"),self.insertextraeventbutton)

        delButton = QPushButton(QApplication.translate("Button","Delete",None, QApplication.UnicodeUTF8))
        delButton.setToolTip(QApplication.translate("Tooltip","Delete the last extra Event button",None, QApplication.UnicodeUTF8))
        #delButton.setMaximumWidth(100)
        delButton.setFocusPolicy(Qt.NoFocus)
        self.connect(delButton, SIGNAL("clicked()"),self.delextraeventbutton)

        savetableButton = QPushButton(QApplication.translate("Button","Update",None, QApplication.UnicodeUTF8))
        savetableButton.setToolTip(QApplication.translate("Tooltip","Save table",None, QApplication.UnicodeUTF8))
        #savetableButton.setMaximumWidth(100)
        savetableButton.setFocusPolicy(Qt.NoFocus)
        self.connect(savetableButton, SIGNAL("clicked()"),self.savetableextraeventbutton)

        helpButton = QPushButton(QApplication.translate("Button","Help",None, QApplication.UnicodeUTF8))
        helpButton.setToolTip(QApplication.translate("Tooltip","Show help",None, QApplication.UnicodeUTF8))
        #helpButton.setMaximumWidth(100)
        helpButton.setFocusPolicy(Qt.NoFocus)
        self.connect(helpButton, SIGNAL("clicked()"),self.showEventbuttonhelp)
                
        #### tab1 layout
        typeLayout0 = QHBoxLayout()
        typeLayout0.addWidget(typelabel1)
        typeLayout0.addWidget(self.etype0)
        
        typeLayout1 = QHBoxLayout()
        typeLayout1.addWidget(typelabel2)
        typeLayout1.addWidget(self.etype1)
        
        typeLayout2 = QHBoxLayout()
        typeLayout2.addWidget(typelabel3)
        typeLayout2.addWidget(self.etype2)
        
        typeLayout3 = QHBoxLayout()
        typeLayout3.addWidget(typelabel4)
        typeLayout3.addWidget(self.etype3)

        typelayout = QGridLayout()
        typelayout.addLayout(typeLayout0,0,0)
        typelayout.addLayout(typeLayout1,0,1)
        typelayout.addLayout(typeLayout2,1,0)
        typelayout.addLayout(typeLayout3,1,1)
        typelayout.addWidget(defaultButton,2,0)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(closeButton)
        buttonLayout.addWidget(okButton)

        TypeGroupLayout = QGroupBox(QApplication.translate("GroupBox","Event Types",None, QApplication.UnicodeUTF8))
        TypeGroupLayout.setLayout(typelayout)

        FlagsLayout = QHBoxLayout()
        FlagsLayout.addWidget(self.eventsbuttonflag)
        FlagsLayout.addWidget(self.eventsshowflagbox)
        FlagsLayout.addWidget(self.minieventsflag)
        FlagsLayout.addWidget(self.eventsGraphflag)

        tab1layout = QVBoxLayout()
        tab1layout.addLayout(FlagsLayout)
        tab1layout.addWidget(TypeGroupLayout)

        ### tab2 layout
        tab2layout = QVBoxLayout()
        tab2layout.addWidget(self.eventbuttontable)
        tab2buttonlayout = QHBoxLayout()    
        tab2buttonlayout.addWidget(addButton)
        tab2buttonlayout.addWidget(delButton)
        tab2buttonlayout.addStretch()
        tab2buttonlayout.addWidget(savetableButton)
        tab2buttonlayout.addWidget(helpButton)        
        tab2layout.addLayout(tab2buttonlayout)  
        
###########################################
        #tab layout
        TabWidget = QTabWidget()
        
        C1Widget = QWidget()
        C1Widget.setLayout(tab1layout)
        TabWidget.addTab(C1Widget,QApplication.translate("Tab","Config",None, QApplication.UnicodeUTF8))

        C2Widget = QWidget()
        C2Widget.setLayout(tab2layout)
        TabWidget.addTab(C2Widget,QApplication.translate("Tab","Buttons",None, QApplication.UnicodeUTF8))        
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(TabWidget)
        mainLayout.addLayout(buttonLayout)

        
        mainLayout.setMargin(0)      

        self.setLayout(mainLayout)

    def createEventbuttonTable(self):
        self.eventbuttontable.clear()
        nbuttons = len(aw.extraeventstypes) 
        if nbuttons:
            self.eventbuttontable.setRowCount(nbuttons)
            self.eventbuttontable.setColumnCount(7)
            self.eventbuttontable.setHorizontalHeaderLabels([QApplication.translate("Table","Label",None, QApplication.UnicodeUTF8),
                                                             QApplication.translate("Table","Description",None, QApplication.UnicodeUTF8),
                                                             QApplication.translate("Table","Type",None, QApplication.UnicodeUTF8),
                                                             QApplication.translate("Table","Value",None, QApplication.UnicodeUTF8),
                                                             QApplication.translate("Table","Action",None, QApplication.UnicodeUTF8),
                                                             QApplication.translate("Table","Documentation",None, QApplication.UnicodeUTF8),
                                                             QApplication.translate("Table","Visibility",None, QApplication.UnicodeUTF8)])
            self.eventbuttontable.setAlternatingRowColors(True)
            self.eventbuttontable.setEditTriggers(QTableWidget.NoEditTriggers)
            self.eventbuttontable.setSelectionBehavior(QTableWidget.SelectRows)
            self.eventbuttontable.setSelectionMode(QTableWidget.SingleSelection)
            self.eventbuttontable.setShowGrid(True)
            visibility = [QApplication.translate("ComboBox","OFF",None, QApplication.UnicodeUTF8),
                          QApplication.translate("ComboBox","ON",None, QApplication.UnicodeUTF8)]
            for i in range(nbuttons):
                #label
                labeledit = QLineEdit( unicode(aw.extraeventslabels[i]))
                #description
                descriptionedit = QLineEdit(unicode(aw.extraeventsdescriptions[i]))
                #type
                typeComboBox =  QComboBox()
                typeComboBox.addItems(aw.qmc.etypes)
                typeComboBox.setCurrentIndex(aw.extraeventstypes[i])
                self.connect(typeComboBox,SIGNAL("currentIndexChanged(int)"),lambda z=1,i=i:self.settypeeventbutton(z,i))
                #value    	
                valueComboBox =  QComboBox()
                valueComboBox.addItems(aw.qmc.eventsvalues)
                valueComboBox.setCurrentIndex(aw.extraeventsvalues[i])
                self.connect(valueComboBox,SIGNAL("currentIndexChanged(int)"),lambda z=1,i=i:self.setvalueeventbutton(z,i))
                #action
                actionComboBox = QComboBox()
                actionComboBox.addItems([QApplication.translate("ComboBox","None",None, QApplication.UnicodeUTF8),
                                    	 QApplication.translate("ComboBox","Serial command",None, QApplication.UnicodeUTF8),
                                         QApplication.translate("ComboBox","Call program",None, QApplication.UnicodeUTF8),
                                         QApplication.translate("ComboBox","Multiple Event",None, QApplication.UnicodeUTF8)])
                actionComboBox.setCurrentIndex(aw.extraeventsactions[i])
                self.connect(actionComboBox,SIGNAL("currentIndexChanged(int)"),lambda z=1,i=i:self.setactioneventbutton(z,i))
                #action description
                actiondescriptionedit = QLineEdit(unicode(aw.extraeventsactionstrings[i]))
                #visibility
                visibilityComboBox =  QComboBox()
                visibilityComboBox.addItems(visibility)
                visibilityComboBox.setCurrentIndex(aw.extraeventsvisibility[i])
                self.connect(visibilityComboBox,SIGNAL("currentIndexChanged(int)"),lambda z=1,i=i:self.setvisibilitytyeventbutton(z,i))                
                
                #add widgets to the table
                self.eventbuttontable.setCellWidget(i,0,labeledit)                
                self.eventbuttontable.setCellWidget(i,1,descriptionedit)                
                self.eventbuttontable.setCellWidget(i,2,typeComboBox)
                self.eventbuttontable.setCellWidget(i,3,valueComboBox)
                self.eventbuttontable.setCellWidget(i,4,actionComboBox)
                self.eventbuttontable.setCellWidget(i,5,actiondescriptionedit)
                self.eventbuttontable.setCellWidget(i,6,visibilityComboBox)

    def savetableextraeventbutton(self):
        for i in range(len(aw.extraeventstypes)):            
            labeledit = self.eventbuttontable.cellWidget(i,0)
            label = unicode(labeledit.text())
            if "\\n" in label:              #make multiple line text if "\n" found in label string
                parts = label.split("\\n")
                label = chr(10).join(parts)
            aw.extraeventslabels[i] = label
            aw.buttonlist[i].setText(aw.extraeventslabels[i])
            
            descriptionedit = self.eventbuttontable.cellWidget(i,1)
            aw.extraeventsdescriptions[i] = unicode(descriptionedit.text())
            
            actiondescriptionedit = self.eventbuttontable.cellWidget(i,5)
            ades = unicode(actiondescriptionedit.text())
    
            aw.extraeventsactionstrings[i] = ades 
            aw.sendmessage(QApplication.translate("Message Area","Custom Event buttons configuration saved", None, QApplication.UnicodeUTF8))        

    def setvisibilitytyeventbutton(self,z,i):
        actioncombobox = self.eventbuttontable.cellWidget(i,6)
        aw.extraeventsvisibility[i] = actioncombobox.currentIndex()
        aw.update_extraeventbuttons_visibility()

    def setactioneventbutton(self,z,i):
        actioncombobox = self.eventbuttontable.cellWidget(i,4)
        aw.extraeventsactions[i] = actioncombobox.currentIndex()
    	
    def setvalueeventbutton(self,z,i):
        valuecombobox = self.eventbuttontable.cellWidget(i,3)
        aw.extraeventsvalues[i] = valuecombobox.currentIndex()
        aw.buttonlist[i].setText(unicode(aw.qmc.etypes[aw.extraeventstypes[i]][0])+unicode(aw.qmc.eventsvalues[aw.extraeventsvalues[i]]))        

    def settypeeventbutton(self,z,i):
        typecombobox = self.eventbuttontable.cellWidget(i,2)
        aw.extraeventstypes[i] = typecombobox.currentIndex()
        aw.buttonlist[i].setText(unicode(aw.qmc.etypes[aw.extraeventstypes[i]][0])+unicode(aw.qmc.eventsvalues[aw.extraeventsvalues[i]]))        

    def delextraeventbutton(self):
        bindex = len(aw.extraeventstypes)-1
        selected = self.eventbuttontable.selectedRanges()
        if len(selected) > 0:
            bindex = selected[0].topRow()
        if bindex >= 0:
            aw.extraeventslabels.pop(bindex)
            aw.extraeventsdescriptions.pop(bindex)
            aw.extraeventstypes.pop(bindex)
            aw.extraeventsvalues.pop(bindex)
            aw.extraeventsactions.pop(bindex)
            aw.extraeventsactionstrings.pop(bindex)
            aw.extraeventsvisibility.pop(bindex)
            
            self.createEventbuttonTable()  #update table
            aw.lowerbuttondialog.removeButton(aw.buttonlist[bindex])
            aw.buttonlist.pop(bindex)        
        aw.update_extraeventbuttons_visibility()

    def insertextraeventbutton(self):
        aw.extraeventsdescriptions.append("")
        aw.extraeventstypes.append(0)
        aw.extraeventsvalues.append(1)
        aw.extraeventsactions.append(0)
        aw.extraeventsactionstrings.append(u"")
        aw.extraeventsvisibility.append(1)
        initialtext = unicode(aw.qmc.etypes[aw.extraeventstypes[-1]][0])+unicode(aw.qmc.eventsvalues[aw.extraeventsvalues[-1]])
        aw.extraeventslabels.append(initialtext)

        self.createEventbuttonTable() 

        aw.buttonlist.append(QPushButton())
        bindex = len(aw.buttonlist)-1
        aw.buttonlist[bindex].setFocusPolicy(Qt.NoFocus)
        aw.buttonlist[bindex].setStyleSheet("font-size: 10pt; font-weight: bold; color: black; background-color: yellow ") 
        aw.buttonlist[bindex].setMaximumSize(90, 50)
        aw.buttonlist[bindex].setMinimumHeight(50)
        aw.buttonlist[bindex].setText(initialtext)        
        aw.connect(aw.buttonlist[bindex], SIGNAL("clicked()"), lambda ee=bindex:aw.recordextraevent(ee))        
        aw.lowerbuttondialog.addButton(aw.buttonlist[bindex],QDialogButtonBox.ActionRole)

        aw.update_extraeventbuttons_visibility()

    def eventsbuttonflagChanged(self):
        if self.eventsbuttonflag.isChecked():
            aw.button_11.setVisible(True)
            aw.eventsbuttonflag = 1
        else:
            aw.button_11.setVisible(False)            
            aw.eventsbuttonflag = 0
            self.minieventsflag.setChecked(False)

    def eventsshowflagChanged(self):
        if self.eventsshowflagbox.isChecked():
            aw.qmc.eventsshowflag = 1
        else:
            aw.qmc.eventsshowflag = 0
        aw.qmc.redraw()        
            
    def minieventsflagChanged(self):
        if self.minieventsflag.isChecked():
            aw.minieventsflag = 1
        else:
            aw.minieventsflag = 0
        aw.update_minieventline_visibility()

    def eventsGraphflagChanged(self):
        if self.eventsGraphflag.isChecked():
            aw.qmc.eventsGraphflag = 1
            #check limits and adjust bottom part if needed
            if aw.qmc.mode == "F":
                lim = aw.qmc.phases[0]-80
            else:
                lim = aw.qmc.phases[0]-40
                
            if   aw.qmc.ylimit_min > lim:
                aw.qmc.ylimit_min = lim
                
            aw.qmc.redraw()
        else:
            aw.qmc.eventsGraphflag = 0
            aw.qmc.redraw()            
          
    def updatetypes(self):
        if len(unicode(self.etype0.text())) and len(unicode(self.etype1.text())) and len(unicode(self.etype2.text())) and len(unicode(self.etype3.text())):
            aw.qmc.etypes[0] = unicode(self.etype0.text())
            aw.qmc.etypes[1] = unicode(self.etype1.text())
            aw.qmc.etypes[2] = unicode(self.etype2.text())
            aw.qmc.etypes[3] = unicode(self.etype3.text())

            #update mini editor
            aw.etypeComboBox.clear()
            aw.etypeComboBox.addItems(aw.qmc.etypes)
        
            aw.qmc.redraw()
            self.savetableextraeventbutton()
            aw.sendmessage(QApplication.translate("Message Area","Event configuration saved", None, QApplication.UnicodeUTF8))
            self.close()
        else:
            aw.sendmessage(QApplication.translate("Message Area","Found empty event type box", None, QApplication.UnicodeUTF8))    
            
    def settypedefault(self):
        aw.qmc.etypes = aw.qmc.etypesdefault
        self.etype0.setText(aw.qmc.etypesdefault[0])
        self.etype1.setText(aw.qmc.etypesdefault[1])
        self.etype2.setText(aw.qmc.etypesdefault[2])
        self.etype3.setText(aw.qmc.etypesdefault[3])

    def showEventbuttonhelp(self):
        string  = QApplication.translate("MessageBox", "<b>Button Label</b> Enter \\n to create labels with multiple lines.",None, QApplication.UnicodeUTF8) + "<br><br>"
        string += QApplication.translate("MessageBox", "<b>Event Description</b> Description of the Event to be recorded.",None, QApplication.UnicodeUTF8) + "<br><br>"  
        string += QApplication.translate("MessageBox", "<b>Event type</b> Type of event to be recorded.",None, QApplication.UnicodeUTF8) + "<br><br>"
        string += QApplication.translate("MessageBox", "<b>Event value</b> Value of event (1-10) to be recorded",None, QApplication.UnicodeUTF8) + "<br><br>"
        string += QApplication.translate("MessageBox", "<b>Action</b> Perform an action at the time of the event",None, QApplication.UnicodeUTF8) + "<br><br>"
        string += QApplication.translate("MessageBox", "<b>Action description</b> Depends on the Action type:",None, QApplication.UnicodeUTF8) + "<br><br>&nbsp;&nbsp;"
        string += QApplication.translate("MessageBox", "Serial command: ASCII serial command or binary a2b_uu(serial command)",None, QApplication.UnicodeUTF8) + "<br><br>&nbsp;&nbsp;"
        string += QApplication.translate("MessageBox", "Call program: A program/script path (absolute or relative)",None, QApplication.UnicodeUTF8) + "<br><br>&nbsp;&nbsp;"
        string += QApplication.translate("MessageBox", "Multiple Event: Adds events of other button numbers separated by a comma: 1,2,3, etc.",None, QApplication.UnicodeUTF8) + "<br><br>"
        string += QApplication.translate("MessageBox", "<b>Button Visibility</b> Hides/shows button",None, QApplication.UnicodeUTF8) + "<br><br>"
        QMessageBox.information(self,QApplication.translate("MessageBox Caption", "Event custom buttons",None, QApplication.UnicodeUTF8),string)
        
##########################################################################
#####################  PHASES GRAPH EDIT DLG  ############################
##########################################################################
        
class phasesGraphDlg(QDialog):
    def __init__(self, parent = None):
        super(phasesGraphDlg,self).__init__(parent)

        self.setWindowTitle(QApplication.translate("Form Caption","Roast Phases",None, QApplication.UnicodeUTF8))
        self.setModal(True)
        
        self.phases = list(aw.qmc.phases)

        dryLabel = QLabel(QApplication.translate("Label", "Dry",None, QApplication.UnicodeUTF8))
        midLabel = QLabel(QApplication.translate("Label", "Mid",None, QApplication.UnicodeUTF8))
        finishLabel = QLabel(QApplication.translate("Label", "Finish",None, QApplication.UnicodeUTF8))

        self.startdry = QSpinBox()
        self.enddry = QSpinBox()
        self.startmid = QSpinBox()
        self.endmid = QSpinBox()
        self.startfinish = QSpinBox()
        self.endfinish = QSpinBox()
                
        self.events2phases()
        
        if aw.qmc.mode == u"F":
             self.startdry
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

        self.getphases()

        self.pushbuttonflag = QCheckBox(QApplication.translate("CheckBox","Auto Adjusted",None, QApplication.UnicodeUTF8))
        if aw.qmc.phasesbuttonflag:
            self.pushbuttonflag.setChecked(True)
        else:
            self.pushbuttonflag.setChecked(False)
        self.connect(self.pushbuttonflag,SIGNAL("stateChanged(int)"),self.pushbuttonflagChanged)  
            
        okButton = QPushButton(QApplication.translate("Button","OK",None, QApplication.UnicodeUTF8))  
        cancelButton = QPushButton(QApplication.translate("Button","Cancel",None, QApplication.UnicodeUTF8))
        setDefaultButton = QPushButton(QApplication.translate("Button","Defaults",None, QApplication.UnicodeUTF8))
        
        cancelButton.setFocusPolicy(Qt.NoFocus)
        setDefaultButton.setFocusPolicy(Qt.NoFocus)
        
        self.connect(cancelButton,SIGNAL("clicked()"),self.cancel)
        self.connect(okButton,SIGNAL("clicked()"),self.updatephases)
        self.connect(setDefaultButton,SIGNAL("clicked()"),self.setdefault)
                                     
        phaseLayout = QGridLayout()
        phaseLayout.addWidget(dryLabel,0,0,Qt.AlignRight)
        phaseLayout.addWidget(self.startdry,0,1)
        phaseLayout.addWidget(self.enddry,0,2)
        phaseLayout.addWidget(midLabel,1,0,Qt.AlignRight)
        phaseLayout.addWidget(self.startmid,1,1)
        phaseLayout.addWidget(self.endmid,1,2)
        phaseLayout.addWidget(finishLabel,2,0,Qt.AlignRight)
        phaseLayout.addWidget(self.startfinish,2,1)
        phaseLayout.addWidget(self.endfinish,2,2)

        boxedPhaseLayout = QHBoxLayout()
        boxedPhaseLayout.addStretch()
        boxedPhaseLayout.addLayout(phaseLayout)
        boxedPhaseLayout.addStretch()

        boxedPhaseFlagLayout = QHBoxLayout()
        boxedPhaseFlagLayout.addStretch()
        boxedPhaseFlagLayout.addWidget(self.pushbuttonflag)
        boxedPhaseFlagLayout.addStretch()
                
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(setDefaultButton)
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(cancelButton)
        buttonsLayout.addWidget(okButton)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(boxedPhaseLayout)
        mainLayout.addLayout(boxedPhaseFlagLayout)
        mainLayout.addStretch()
        mainLayout.addLayout(buttonsLayout)
        
        mainLayout.setSizeConstraint(QLayout.SetFixedSize)

        self.setLayout(mainLayout)
        aw.qmc.redraw()
        
    def savePhasesSettings(self):
        if not aw.qmc.phasesbuttonflag:
            settings = QSettings()
            #save phases
            settings.setValue("Phases",aw.qmc.phases)
        
    def events2phases(self):
        if aw.qmc.phasesbuttonflag:
            # adjust phases by DryEnd and FCs events
            if aw.qmc.timeindex[1]:
                aw.qmc.phases[1] = int(round(aw.qmc.temp2[aw.qmc.timeindex[1]]))  
                self.enddry.setDisabled(True)
                self.startmid.setDisabled(True)
            if aw.qmc.timeindex[2]:
                aw.qmc.phases[2] = int(round(aw.qmc.temp2[aw.qmc.timeindex[2]]))
                self.endmid.setDisabled(True)
                self.startfinish.setDisabled(True)

    def pushbuttonflagChanged(self,i):
        if i:
            aw.qmc.phasesbuttonflag = 1
            self.events2phases()
            self.getphases()
            aw.qmc.redraw()
        else:
            aw.qmc.phasesbuttonflag = 0
            self.enddry.setEnabled(True)
            self.startmid.setEnabled(True)
            self.endmid.setEnabled(True)
            self.startfinish.setEnabled(True)
        
    def updatephases(self):
        aw.qmc.phases[0] = self.startdry.value()
        aw.qmc.phases[1] = self.enddry.value()
        aw.qmc.phases[2] = self.endmid.value()
        aw.qmc.phases[3] = self.endfinish.value()
        if self.pushbuttonflag.isChecked():
            aw.qmc.phasesbuttonflag = 1
        else:
            aw.qmc.phasesbuttonflag = 0
        aw.qmc.redraw()
        self.savePhasesSettings()
        self.close()
        
    def cancel(self):
        aw.qmc.phases = list(self.phases)
        aw.qmc.redraw()
        self.savePhasesSettings()
        self.close()
        
    def getphases(self):
        self.startdry.setValue(aw.qmc.phases[0])
        self.enddry.setValue(aw.qmc.phases[1])
        self.endmid.setValue(aw.qmc.phases[2])
        self.endfinish.setValue(aw.qmc.phases[3])

    def setdefault(self):
        if aw.qmc.mode == u"F":
            aw.qmc.phases = list(aw.qmc.phases_fahrenheit_defaults)
        elif aw.qmc.mode == u"C":
            aw.qmc.phases = list(aw.qmc.phases_celsius_defaults)
        self.events2phases()
        self.getphases()

        aw.sendmessage(QApplication.translate("Message Area","Phases changed to %1 default: %2)",None, QApplication.UnicodeUTF8).arg(aw.qmc.mode).arg(unicode(aw.qmc.phases)))
        aw.qmc.redraw()

############################################################################        
#####################   FLAVOR STAR PROPERTIES DIALOG   ####################
############################################################################
        
class flavorDlg(QDialog):
    def __init__(self, parent = None):
        super(flavorDlg,self).__init__(parent)

        #avoid questionm mark context help
        flags = self.windowFlags()
        helpFlag = Qt.WindowContextHelpButtonHint
        flags = flags & (~helpFlag)
        self.setWindowFlags(flags)
        
        self.setWindowTitle(QApplication.translate("Form Caption","Cup Profile",None, QApplication.UnicodeUTF8))        
        self.setModal(True)
        aw.lowerbuttondialog.setVisible(False)
        aw.EventsGroupLayout.setVisible(False)

        defaultlabel = QLabel(QApplication.translate("Label","Default",None, QApplication.UnicodeUTF8))
        self.defaultcombobox = QComboBox()
        self.defaultcombobox.addItems(["","Artisan","SCCA","CQI","SweetMarias","C","E","CoffeeGeek","Intelligentsia","Istituto Internazionale Assaggiatori Caffe"])
        self.defaultcombobox.setCurrentIndex(0)
        self.connect(self.defaultcombobox, SIGNAL("currentIndexChanged(int)"),self.setdefault)

        self.flavortable = QTableWidget()
        self.flavortable.setTabKeyNavigation(True)
        self.createFlavorTable()

        leftButton = QPushButton("<")
        leftButton.setFocusPolicy(Qt.NoFocus)
        self.connect(leftButton, SIGNAL("clicked()"),lambda x=0:self.move(x))

        rightButton = QPushButton(">")
        rightButton.setFocusPolicy(Qt.NoFocus)
        self.connect(rightButton, SIGNAL("clicked()"),lambda x=1:self.move(x))

        addButton = QPushButton(QApplication.translate("Button","Add",None, QApplication.UnicodeUTF8))
        addButton.setFocusPolicy(Qt.NoFocus)
        self.connect(addButton, SIGNAL("clicked()"),self.addlabel)

        delButton = QPushButton(QApplication.translate("Button","Del",None, QApplication.UnicodeUTF8))
        delButton.setFocusPolicy(Qt.NoFocus)
        self.connect(delButton, SIGNAL("clicked()"),self.poplabel)
        
        saveImgButton = QPushButton(QApplication.translate("Button","Save Image",None, QApplication.UnicodeUTF8))
        saveImgButton.setFocusPolicy(Qt.NoFocus)
        self.connect(saveImgButton, SIGNAL("clicked()"),lambda x=0,i=1:aw.resize(x,i))

        backButton = QPushButton(QApplication.translate("Button","OK",None, QApplication.UnicodeUTF8))
        self.connect(backButton,SIGNAL("clicked()"),self.close)

        self.backgroundCheck = QCheckBox(QApplication.translate("CheckBox","Background", None, QApplication.UnicodeUTF8))
        if aw.qmc.flavorbackgroundflag:
            self.backgroundCheck.setChecked(True)
        self.connect(self.backgroundCheck, SIGNAL("clicked()"),self.showbackground)
        
        flavorLayout = QHBoxLayout()
        flavorLayout.addWidget(self.flavortable)     
        
        buttonsLayout = QGridLayout()
        buttonsLayout.addWidget(addButton,0,0)
        buttonsLayout.addWidget(delButton,0,1)        
        buttonsLayout.addWidget(defaultlabel,1,0)
        buttonsLayout.addWidget(self.defaultcombobox,1,1)
        buttonsLayout.addWidget(leftButton,2,0)
        buttonsLayout.addWidget(rightButton,2,1)
        buttonsLayout.addWidget(self.backgroundCheck,3,0)
        buttonsLayout.addWidget(saveImgButton,4,0)
        buttonsLayout.addWidget(backButton,4,1)
            
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(flavorLayout)
        mainLayout.addLayout(buttonsLayout)
        
        self.setLayout(mainLayout)

        #draw
        aw.qmc.flavorchart()
        
    def createFlavorTable(self):

        self.flavortable.clear()        
        nflavors = len(aw.qmc.flavorlabels)
        if nflavors:    
            self.flavortable.setRowCount(nflavors)
            self.flavortable.setColumnCount(2)
            self.flavortable.setHorizontalHeaderLabels([QApplication.translate("Table", "Label",None, QApplication.UnicodeUTF8),
                                                        QApplication.translate("Table", "Value",None, QApplication.UnicodeUTF8)])
            
            self.flavortable.setAlternatingRowColors(True)
            self.flavortable.setEditTriggers(QTableWidget.NoEditTriggers)
            self.flavortable.setSelectionBehavior(QTableWidget.SelectRows)
            self.flavortable.setSelectionMode(QTableWidget.SingleSelection)
            self.flavortable.setShowGrid(True)

            #populate table
            for i in range(nflavors):
                labeledit = QLineEdit(unicode(aw.qmc.flavorlabels[i]))            
                    
                valueSpinBox = QDoubleSpinBox()
                valueSpinBox.setRange(0.,10.)
                
                val  = aw.qmc.flavors[i]
                if aw.qmc.flavors[0] < 1. and aw.qmc.flavors[-1] < 1.: # < 0.5.0 version style compatibility
                    val *= 10.
                valueSpinBox.setValue(val)
                self.connect(valueSpinBox, SIGNAL("valueChanged(double)"),lambda z=1,x=i: self.setvalue(z,x))
                
                #add widgets to the table
                self.flavortable.setCellWidget(i,0,labeledit)
                self.flavortable.setCellWidget(i,1,valueSpinBox)

    def showbackground(self):
        if self.backgroundCheck.isChecked():
            if not aw.qmc.background:
                message = QApplication.translate("Message Area","Background not found", None, QApplication.UnicodeUTF8)
                aw.sendmessage(message)
                self.backgroundCheck.setChecked(False)
            else:
                if len(aw.qmc.backgroundFlavors) != len(aw.qmc.flavors):
                    message = QApplication.translate("Message Area","Background does not match number of labels", None, QApplication.UnicodeUTF8)
                    aw.sendmessage(message)
                    self.backgroundCheck.setChecked(False)
                else:
                    aw.qmc.flavorbackgroundflag = True
                    aw.qmc.flavorchart()
        else:
            aw.qmc.flavorbackgroundflag = False
            aw.qmc.flavorchart()            

    def move(self,x):
        if x == 0:
            aw.qmc.flavorstartangle += 5
        else:
            aw.qmc.flavorstartangle -= 5
        aw.qmc.flavorchart()

    def savetable(self):
        for i in range(len(aw.qmc.flavorlabels)):
            labeledit = self.flavortable.cellWidget(i,0)
            valueSpinBox = self.flavortable.cellWidget(i,1)

            label = unicode(labeledit.text())
            if "\\n" in label:              #make multiple line text if "\n" found in label string
                parts = label.split("\\n")
                label = chr(10).join(parts)
                
            aw.qmc.flavorlabels[i] = label
            aw.qmc.flavors[i] = valueSpinBox.value()

    def setvalue(self,z,x):
        valueSpinBox = self.flavortable.cellWidget(x,1)
        aw.qmc.flavors[x] = valueSpinBox.value()
        aw.qmc.flavorchart()        
            
    def setdefault(self):
        dindex =  self.defaultcombobox.currentIndex()
        #["","Artisan","SCCA","CQI","SweetMarias","C","E",coffeegeek,Intelligentsia]
        if dindex == 1:
            aw.qmc.flavorlabels = list(aw.qmc.artisanflavordefaultlabels)
            aw.qmc.flavorstartangle = 90
        elif dindex == 2:
            aw.qmc.flavorlabels = list(aw.qmc.SCCAflavordefaultlabels)
            aw.qmc.flavorstartangle = 90
        elif dindex == 3:
            aw.qmc.flavorlabels = list(aw.qmc.CQIflavordefaultlabels)
            aw.qmc.flavorstartangle = 90
        elif dindex == 4:
            aw.qmc.flavorlabels = list(aw.qmc.SweetMariasflavordefaultlabels)
            aw.qmc.flavorstartangle = 90
        elif dindex == 5:
            aw.qmc.flavorlabels = list(aw.qmc.Cflavordefaultlabels)
            aw.qmc.flavorstartangle = 90
        elif dindex == 6:
            aw.qmc.flavorlabels = list(aw.qmc.Eflavordefaultlabels)
            aw.qmc.flavorstartangle = 90
        elif dindex == 7:
            aw.qmc.flavorlabels = list(aw.qmc.coffeegeekflavordefaultlabels)
            aw.qmc.flavorstartangle = 90
        elif dindex == 8:
            aw.qmc.flavorlabels = list(aw.qmc.Intelligentsiaflavordefaultlabels)
            aw.qmc.flavorstartangle = 90
        elif dindex == 9:
            aw.qmc.flavorlabels = list(aw.qmc.IstitutoInternazionaleAssaggiatoriCaffe)
            aw.qmc.flavorstartangle = 90
            
        else:
            return
        aw.qmc.flavors = [5.]*len(aw.qmc.flavorlabels)
        self.createFlavorTable()        
        aw.qmc.flavorchart()

    def addlabel(self):
        fn = len(aw.qmc.flavors)
        aw.qmc.flavorlabels.append("???")
        aw.qmc.flavors.append(5.)
        self.createFlavorTable()
        aw.qmc.flavorchart()

    def poplabel(self):
        fn = len(aw.qmc.flavors)
        aw.qmc.flavors = aw.qmc.flavors[:(fn-1)]
        aw.qmc.flavorlabels = aw.qmc.flavorlabels[:(fn -1)]
        self.createFlavorTable()
        aw.qmc.flavorchart()

    def closeEvent(self, event):
        self.accept()
        aw.qmc.redraw()
        aw.lowerbuttondialog.setVisible(True)
        aw.update_minieventline_visibility()
        
    def close(self):
        self.savetable()
        aw.lowerbuttondialog.setVisible(True)
        aw.update_minieventline_visibility()
        self.accept()
        aw.qmc.redraw()

#################################################################
#################### BACKGROUND DIALOG  #########################
#################################################################

class backgroundDLG(QDialog):
    def __init__(self, parent = None):
        super(backgroundDLG,self).__init__(parent)
        self.setWindowTitle(QApplication.translate("Form Caption","Profile Background", None, QApplication.UnicodeUTF8))
        self.setModal(True)
        

    	#TAB 1
        self.pathedit = QLineEdit(aw.qmc.backgroundpath)
        self.pathedit.setStyleSheet("background-color:'lightgrey';")
        self.filename = u""
        
        self.backgroundCheck = QCheckBox(QApplication.translate("CheckBox","Show", None, QApplication.UnicodeUTF8))
        self.backgroundDetails = QCheckBox(QApplication.translate("CheckBox","Text", None, QApplication.UnicodeUTF8))
        self.backgroundeventsflag = QCheckBox(QApplication.translate("CheckBox","Events", None, QApplication.UnicodeUTF8))
        
        if aw.qmc.background:
            self.backgroundCheck.setChecked(True)
        else:
            self.backgroundCheck.setChecked(False)

        self.status = QStatusBar()
        self.status.setSizeGripEnabled(False)
        self.status.showMessage(QApplication.translate("StatusBar","Ready", None, QApplication.UnicodeUTF8),3000)

        if aw.qmc.backgroundDetails:
            self.backgroundDetails.setChecked(True)
        else:
            self.backgroundDetails.setChecked(False)

        if aw.qmc.backgroundeventsflag:
            self.backgroundeventsflag.setChecked(True)
        else:
            self.backgroundeventsflag.setChecked(False)
            

        loadButton = QPushButton(QApplication.translate("Button","Load", None, QApplication.UnicodeUTF8))
        loadButton.setFocusPolicy(Qt.NoFocus)

        delButton = QPushButton(QApplication.translate("Button","Delete", None, QApplication.UnicodeUTF8))
        delButton.setFocusPolicy(Qt.NoFocus)
        
        okButton = QPushButton(QApplication.translate("Button","OK", None, QApplication.UnicodeUTF8))
        
        selectButton =QPushButton(QApplication.translate("Button","Select Profile", None, QApplication.UnicodeUTF8))
        selectButton.setFocusPolicy(Qt.NoFocus)

        alignButton = QPushButton(QApplication.translate("Button","Align", None, QApplication.UnicodeUTF8))
        alignButton.setFocusPolicy(Qt.NoFocus)
        
        self.connect(loadButton, SIGNAL("clicked()"),self.load)
        self.connect(okButton, SIGNAL("clicked()"),self, SLOT("reject()"))        
        self.connect(selectButton, SIGNAL("clicked()"), self.selectpath)
        self.connect(alignButton, SIGNAL("clicked()"), self.timealign)

        self.speedSpinBox = QSpinBox()
        self.speedSpinBox.setRange(10,90)
        self.speedSpinBox.setSingleStep(10)
        self.speedSpinBox.setValue(30)
        
        intensitylabel =QLabel(QApplication.translate("Label", "Opaqueness",None, QApplication.UnicodeUTF8))
        intensitylabel.setAlignment(Qt.AlignRight)
        self.intensitySpinBox = QSpinBox()
        self.intensitySpinBox.setRange(1,9)
        self.intensitySpinBox.setSingleStep(1)
        self.intensitySpinBox.setValue(3)

        widthlabel =QLabel(QApplication.translate("Label", "Line Width",None, QApplication.UnicodeUTF8))
        widthlabel.setAlignment(Qt.AlignRight)
        self.widthSpinBox = QSpinBox()
        self.widthSpinBox.setRange(1,20)
        self.widthSpinBox.setSingleStep(1)
        self.widthSpinBox.setValue(2)

        stylelabel =QLabel(QApplication.translate("Label", "Line Style",None, QApplication.UnicodeUTF8))
        stylelabel.setAlignment(Qt.AlignRight)        
        self.styleComboBox = QComboBox()
        self.styleComboBox.addItems([QApplication.translate("ComboBox","-",None, QApplication.UnicodeUTF8),
                                     QApplication.translate("ComboBox","--",None, QApplication.UnicodeUTF8),
                                     QApplication.translate("ComboBox",":",None, QApplication.UnicodeUTF8),
                                     QApplication.translate("ComboBox","-.",None, QApplication.UnicodeUTF8),
                                     QApplication.translate("ComboBox","steps",None, QApplication.UnicodeUTF8)])
        self.styleComboBox.setCurrentIndex(0)


        colors = [u""]
        for key in cnames:
            colors.append(unicode(key))
        colors.sort()
        colors.insert(0,u"et")
        colors.insert(1,u"bt")
        colors.pop(2)
        
        btcolorlabel = QLabel(QApplication.translate("Label", "BT Color",None, QApplication.UnicodeUTF8))
        btcolorlabel.setAlignment(Qt.AlignRight)        
        self.btcolorComboBox = QComboBox()
        self.btcolorComboBox.addItems(colors)
        self.btcolorComboBox.setCurrentIndex(1)

        metcolorlabel = QLabel(QApplication.translate("Label", "ET Color",None, QApplication.UnicodeUTF8))
        metcolorlabel.setAlignment(Qt.AlignRight)        
        self.metcolorComboBox = QComboBox()
        self.metcolorComboBox.addItems(colors)
        self.metcolorComboBox.setCurrentIndex(0)
        
        self.upButton = QPushButton(QApplication.translate("Button","Up",None, QApplication.UnicodeUTF8))
        self.upButton.setFocusPolicy(Qt.NoFocus)
        self.downButton = QPushButton(QApplication.translate("Button","Down",None, QApplication.UnicodeUTF8))
        self.downButton.setFocusPolicy(Qt.NoFocus)
        self.leftButton = QPushButton(QApplication.translate("Button","Left",None, QApplication.UnicodeUTF8))
        self.leftButton.setFocusPolicy(Qt.NoFocus)
        self.rightButton = QPushButton(QApplication.translate("Button","Right",None, QApplication.UnicodeUTF8))
        self.rightButton.setFocusPolicy(Qt.NoFocus)


        self.connect(self.backgroundDetails, SIGNAL("clicked()"),self.readChecks)
        self.connect(self.backgroundeventsflag, SIGNAL("clicked()"),self.readChecks)
        self.connect(delButton, SIGNAL("clicked()"),self.delete)
        self.connect(self.upButton, SIGNAL("clicked()"), lambda m= "up": self.move(m))
        self.connect(self.downButton, SIGNAL("clicked()"), lambda m="down": self.move(m))
        self.connect(self.leftButton, SIGNAL("clicked()"), lambda m="left": self.move(m))
        self.connect(self.rightButton, SIGNAL("clicked()"),lambda m="right": self.move(m))
        self.connect(self.intensitySpinBox, SIGNAL("valueChanged(int)"),self.adjustintensity)
        self.connect(self.widthSpinBox, SIGNAL("valueChanged(int)"),self.adjustwidth)
        self.connect(self.btcolorComboBox, SIGNAL("currentIndexChanged(QString)"),lambda color="", curve = "bt": self.adjustcolor(color,curve))
        self.connect(self.metcolorComboBox, SIGNAL("currentIndexChanged(QString)"),lambda color= "", curve = "et": self.adjustcolor(color,curve))
        self.connect(self.styleComboBox, SIGNAL("currentIndexChanged(QString)"),self.adjuststyle)

        #TAB 2 EVENTS
        #table for showing events
        self.eventtable = QTableWidget()
        self.eventtable.setTabKeyNavigation(True)
        self.createEventTable()
        
        #TAB 3 DATA
        #table for showing data
        self.datatable = QTableWidget()
        self.datatable.setTabKeyNavigation(True)
        self.createDataTable()
        
    	#TAB 4
        self.backgroundReproduce = QCheckBox(QApplication.translate("CheckBox","Playback Aid Mode",None, QApplication.UnicodeUTF8))    
        if aw.qmc.backgroundReproduce:
            self.backgroundReproduce.setChecked(True)
        else:
            self.backgroundReproduce.setChecked(False)    	
        self.connect(self.backgroundReproduce, SIGNAL("stateChanged(int)"),self.setreproduce)

        etimelabel =QLabel(QApplication.translate("Label", "Text warning time (seconds)",None, QApplication.UnicodeUTF8))
        self.etimeSpinBox = QSpinBox()
        self.etimeSpinBox.setRange(1,60)
        self.etimeSpinBox.setValue(aw.qmc.detectBackgroundEventTime)
        self.connect(self.etimeSpinBox, SIGNAL("valueChanged(int)"),self.setreproduce)
        
        #LAYOUT MANAGERS
        movelayout = QGridLayout()
        movelayout.addWidget(self.upButton,0,1)
        movelayout.addWidget(self.leftButton,1,0)
        movelayout.addWidget(self.speedSpinBox,1,1)
        movelayout.addWidget(self.rightButton,1,2)
        movelayout.addWidget(self.downButton,2,1)

        checkslayout = QHBoxLayout()
        checkslayout.addWidget(self.backgroundCheck)
        checkslayout.addWidget(self.backgroundDetails)
        checkslayout.addWidget(self.backgroundeventsflag)
        
        
        layout = QGridLayout()
        layout.addWidget(selectButton,0,0)
        layout.addWidget(self.pathedit,0,1)
        layout.addWidget(loadButton,1,0)
        layout.addWidget(delButton,1,1)
        layout.addWidget(widthlabel,2,0)
        layout.addWidget(self.widthSpinBox,2,1)
        layout.addWidget(intensitylabel,3,0)
        layout.addWidget(self.intensitySpinBox,3,1)
        layout.addWidget(metcolorlabel,4,0)
        layout.addWidget(self.metcolorComboBox,4,1)
        layout.addWidget(btcolorlabel,5,0)
        layout.addWidget(self.btcolorComboBox,5,1)
        layout.addWidget(stylelabel,6,0)
        layout.addWidget(self.styleComboBox,6,1)
        
        upperlayout = QVBoxLayout()
        upperlayout.addLayout(movelayout)
        upperlayout.addLayout(checkslayout)         
        upperlayout.addLayout(layout) 
        
        layoutBoxed = QHBoxLayout()
        layoutBoxed.addStretch()
        layoutBoxed.addLayout(upperlayout)
        layoutBoxed.addStretch()

        alignButtonBoxed = QHBoxLayout()
        alignButtonBoxed.addStretch()
        alignButtonBoxed.addWidget(alignButton)
        
        tab1layout = QVBoxLayout()
        tab1layout.addLayout(layoutBoxed)  
        tab1layout.addStretch()
        tab1layout.addLayout(alignButtonBoxed)
        tab1layout.setContentsMargins(5, 0, 5, 0) # left, top, right, bottom 
        tab1layout.setMargin(0)      

        tab2layout = QVBoxLayout()
        tab2layout.addWidget(self.eventtable)
        tab2layout.setContentsMargins(5, 0, 5, 0) # left, top, right, bottom 
        tab2layout.setMargin(0)      

        tab3layout = QVBoxLayout()
        tab3layout.addWidget(self.datatable)
        tab3layout.setContentsMargins(5, 0, 5, 0) # left, top, right, bottom 
        tab3layout.setMargin(0)      
        
        tab4layout = QGridLayout()
        tab4layout.addWidget(self.backgroundReproduce,0,0)
        tab4layout.addWidget(etimelabel,1,0)
        tab4layout.addWidget(self.etimeSpinBox,1,1)
        tab4layout.setContentsMargins(5, 0, 5, 0) # left, top, right, bottom 
        tab4layout.setMargin(0)      
       
        #tab layout
        TabWidget = QTabWidget()
        
        C1Widget = QWidget()
        C1Widget.setLayout(tab1layout)
        TabWidget.addTab(C1Widget,QApplication.translate("Tab","Config",None, QApplication.UnicodeUTF8))

        C2Widget = QWidget()
        C2Widget.setLayout(tab2layout)
        TabWidget.addTab(C2Widget,QApplication.translate("Tab","Events",None, QApplication.UnicodeUTF8))

        C3Widget = QWidget()
        C3Widget.setLayout(tab3layout)
        TabWidget.addTab(C3Widget,QApplication.translate("Tab","Data",None, QApplication.UnicodeUTF8))

        C4Widget = QWidget()
        C4Widget.setLayout(tab4layout)
        TabWidget.addTab(C4Widget,QApplication.translate("Tab","Playback",None, QApplication.UnicodeUTF8))
        
        
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(okButton)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.status)
        mainLayout.addWidget(TabWidget) 
        mainLayout.addLayout(buttonLayout)    
        mainLayout.setMargin(0)      

        self.setLayout(mainLayout)

    def setreproduce(self):
        if aw.qmc.background:
            aw.qmc.detectBackgroundEventTime = self.etimeSpinBox.value()
                        
            if self.backgroundReproduce.isChecked():
                aw.qmc.backgroundReproduce = True
                msg = QApplication.translate("StatusBar","Playback Aid set ON at %1 secs",None, QApplication.UnicodeUTF8).arg(str(aw.qmc.detectBackgroundEventTime))
            else:
                aw.qmc.backgroundReproduce = False
                msg = QApplication.translate("StatusBar","Playback Aid set OFF",None, QApplication.UnicodeUTF8)
                aw.messagelabel.setStyleSheet("background-color:'transparent';")
                
            self.status.showMessage(msg,5000)
        else:
            self.backgroundReproduce.setChecked(False)
            self.status.showMessage(QApplication.translate("StatusBar","No profile background found",None, QApplication.UnicodeUTF8),5000)


    def timealign(self):
        if aw.qmc.timeindex[0] != -1:
            start = aw.qmc.timex[aw.qmc.timeindex[0]]
        else:
            start = 0

        if aw.qmc.timeindexB[0] != -1:
            startB = aw.qmc.timeB[aw.qmc.timeindexB[0]]
        else:
            startB = 0

        btime = startB
        ptime = start
        
        difference = ptime - btime
        if difference > 0:
           aw.qmc.movebackground("right",abs(difference))
        elif difference < 0:
           aw.qmc.movebackground("left",abs(difference))
        
        aw.qmc.redraw()

    def adjuststyle(self):
        
        self.status.showMessage(QApplication.translate("StatusBar","Processing...",None, QApplication.UnicodeUTF8),5000)
        #block button
        self.styleComboBox.setDisabled(True) 
        aw.qmc.backgroundstyle = unicode(self.styleComboBox.currentText())
        aw.qmc.redraw()
        #reactivate button
        self.styleComboBox.setDisabled(False)
        self.status.showMessage(QApplication.translate("StatusBar","Ready",None, QApplication.UnicodeUTF8),5000)         

    def adjustcolor(self,color,curve):
        color = str(color)
        self.status.showMessage(QApplication.translate("StatusBar","Processing...",None, QApplication.UnicodeUTF8),5000)
     
        self.btcolorComboBox.setDisabled(True)
        self.metcolorComboBox.setDisabled(True)
        
        if curve == u"et":
            if color == u"et":
                aw.qmc.backgroundmetcolor = aw.qmc.palette["et"]
            elif color == u"bt":
                aw.qmc.backgroundmetcolor = aw.qmc.palette["bt"]
            else:
                aw.qmc.backgroundmetcolor = color
                
        elif curve == u"bt":
            if color == u"bt":
                aw.qmc.backgroundbtcolor = aw.qmc.palette["bt"]
            elif color == u"et":
                aw.qmc.backgroundbtcolor = aw.qmc.palette["et"]                
            else:
                aw.qmc.backgroundbtcolor = color

        aw.qmc.redraw()
        self.btcolorComboBox.setDisabled(False)
        self.metcolorComboBox.setDisabled(False)
        self.status.showMessage(QApplication.translate("StatusBar","Ready",None, QApplication.UnicodeUTF8),5000) 

    def adjustwidth(self):
        
        self.status.showMessage(QApplication.translate("StatusBar","Processing...",None, QApplication.UnicodeUTF8),5000)
        #block button
        self.widthSpinBox.setDisabled(True)
        aw.qmc.backgroundwidth = self.widthSpinBox.value()
        aw.qmc.redraw()
        #reactivate button
        self.widthSpinBox.setDisabled(False)
        self.status.showMessage(QApplication.translate("StatusBar","Ready",None, QApplication.UnicodeUTF8),5000)        

    def adjustintensity(self):
        
        self.status.showMessage(QApplication.translate("StatusBar","Processing...",None, QApplication.UnicodeUTF8),5000)
        #block button
        self.intensitySpinBox.setDisabled(True)
        aw.qmc.backgroundalpha = self.intensitySpinBox.value()/10.
        aw.qmc.redraw()
        #reactivate button
        self.intensitySpinBox.setDisabled(False)
        self.status.showMessage(QApplication.translate("StatusBar","Ready",None, QApplication.UnicodeUTF8),5000)   
        
    def delete(self):
        
        self.status.showMessage(QApplication.translate("StatusBar","Processing...",None, QApplication.UnicodeUTF8),5000)
        self.pathedit.setText(u"")
        self.backgroundDetails.setChecked(False)
        self.backgroundCheck.setChecked(False)
        self.backgroundeventsflag.setChecked(False)
        
        aw.qmc.temp1B, aw.qmc.temp2B, aw.qmc.timeB = [],[],[]
        aw.qmc.backgroundEvents, aw.qmc.backgroundEtypes = [],[]
        aw.qmc.backgroundEvalues, aw.qmc.backgroundEStrings,aw.qmc.backgroundFlavors = [],[],[]
        aw.qmc.timeindexB = [-1,0,0,0,0,0,0]
        self.eventtable.clear()
        self.datatable.clear()
        aw.qmc.dryendB = [0.,0.]
        aw.qmc.background = False
        aw.qmc.backgroundDetails = False
        aw.qmc.backgroundeventsflag = False
        aw.qmc.backmoveflag = 1
        aw.qmc.redraw()
        
        self.status.showMessage(QApplication.translate("StatusBar","Ready",None, QApplication.UnicodeUTF8),5000)   
        
    def move(self,m):        
         self.status.showMessage(QApplication.translate("StatusBar","Processing...",None, QApplication.UnicodeUTF8),5000)
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
         self.createEventTable()
         self.createDataTable()
         
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
            
         self.status.showMessage(QApplication.translate("StatusBar","Ready",None, QApplication.UnicodeUTF8),5000)       

    def readChecks(self):
        self.status.showMessage(QApplication.translate("StatusBar","Processing...",None, QApplication.UnicodeUTF8),5000)
        if self.backgroundCheck.isChecked():
            aw.qmc.background = True
        else:
            aw.qmc.background = False
            
        if  self.backgroundDetails.isChecked():
            aw.qmc.backgroundDetails = True
        else:
            aw.qmc.backgroundDetails = False

        if self.backgroundeventsflag.isChecked():
            aw.qmc.backgroundeventsflag = True
        else:
            aw.qmc.backgroundeventsflag = False            
            
        aw.qmc.redraw()
        self.status.showMessage(QApplication.translate("StatusBar","Ready",None, QApplication.UnicodeUTF8),5000)   
        

    def selectpath(self):
        filename = aw.ArtisanOpenFileDialog()
        self.pathedit.setText(filename)
        self.filename = filename

    def load(self):        
        if unicode(self.pathedit.text()) == "":
            self.status.showMessage(QApplication.translate("StatusBar","Empty file path",None, QApplication.UnicodeUTF8),5000)   
            return
        self.status.showMessage(QApplication.translate("StatusBar","Reading file...",None, QApplication.UnicodeUTF8),5000)   
        aw.qmc.backgroundpath = unicode(self.pathedit.text())
        aw.loadbackground(unicode(self.pathedit.text()))
        self.backgroundCheck.setChecked(True)
        self.backgroundDetails.setChecked(True)
        self.backgroundeventsflag.setChecked(True)
        self.readChecks()
        self.createEventTable()
        self.createDataTable()

    def createEventTable(self):
        self.eventtable.clear()
        ndata = len(aw.qmc.backgroundEvents)
        if ndata:
            self.eventtable.setRowCount(ndata)
            self.eventtable.setColumnCount(4)
            self.eventtable.setHorizontalHeaderLabels([QApplication.translate("Table","Time",None, QApplication.UnicodeUTF8),
                                                       QApplication.translate("Table","Description",None, QApplication.UnicodeUTF8),
                                                       QApplication.translate("Table","Type",None, QApplication.UnicodeUTF8),
                                                       QApplication.translate("Table","Value",None, QApplication.UnicodeUTF8)])
            self.eventtable.setAlternatingRowColors(True)
            self.eventtable.setEditTriggers(QTableWidget.NoEditTriggers)
            self.eventtable.setSelectionBehavior(QTableWidget.SelectRows)
            self.eventtable.setSelectionMode(QTableWidget.SingleSelection)
            self.eventtable.setShowGrid(True)

            if aw.qmc.timeindex[0] != -1:
                start = aw.qmc.timex[aw.qmc.timeindex[0]]
            else:
                start = 0

            for i in range(ndata):
                timez = QTableWidgetItem(aw.qmc.stringfromseconds(int(aw.qmc.timeB[aw.qmc.backgroundEvents[i]]-start)))
                description = QTableWidgetItem(aw.qmc.backgroundEStrings[i])
                etype = QTableWidgetItem(aw.qmc.Betypes[aw.qmc.backgroundEtypes[i]])
                evalue = QTableWidgetItem(aw.qmc.eventsvalues[aw.qmc.backgroundEvalues[i]])

                #add widgets to the table
                self.eventtable.setItem(i,0,timez)
                self.eventtable.setItem(i,1,description)
                self.eventtable.setItem(i,2,etype)
                self.eventtable.setItem(i,3,evalue)            


    def createDataTable(self):
        self.datatable.clear()
        ndata = len(aw.qmc.timeB)
        
        if aw.qmc.timeindex[0] != -1:
            start = aw.qmc.timex[aw.qmc.timeindex[0]]
        else:
            start = 0
            
        if ndata:    
            self.datatable.setRowCount(ndata)
            self.datatable.setColumnCount(6)
            self.datatable.setHorizontalHeaderLabels([QApplication.translate("Table","Abs Time",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","Rel Time",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","ET",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","BT",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","DeltaBT (d/m)",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","DeltaET (d/m)",None, QApplication.UnicodeUTF8)])
            self.datatable.setAlternatingRowColors(True)
            self.datatable.setEditTriggers(QTableWidget.NoEditTriggers)
            self.datatable.setSelectionBehavior(QTableWidget.SelectRows)
            self.datatable.setSelectionMode(QTableWidget.SingleSelection)
            self.datatable.setShowGrid(True)
            for i in range(ndata):
                Atime = QTableWidgetItem("%.03f"%aw.qmc.timeB[i])
                Rtime = QTableWidgetItem(aw.qmc.stringfromseconds(int(round(aw.qmc.timeB[i]-start))))
                ET = QTableWidgetItem("%.02f"%aw.qmc.temp1B[i])
                BT = QTableWidgetItem("%.02f"%aw.qmc.temp2B[i])
                if i:
                    deltaET = QTableWidgetItem("%.02f"%(60*(aw.qmc.temp1B[i]-aw.qmc.temp1B[i-1])/(aw.qmc.timeB[i]-aw.qmc.timeB[i-1])))
                    deltaBT = QTableWidgetItem("%.02f"%(60*(aw.qmc.temp2B[i]-aw.qmc.temp2B[i-1])/(aw.qmc.timeB[i]-aw.qmc.timeB[i-1])))
                else:
                    deltaET = QTableWidgetItem("00:00")
                    deltaBT = QTableWidgetItem("00:00")
                if i:                
                        #identify by color and add notation
                    if i == aw.qmc.timeindexB[0] != -1:
                        Rtime.setBackgroundColor(QColor('#f07800'))
                        text = QApplication.translate("Table", "%1 START",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                        Rtime.setText(text)
                    elif i == aw.qmc.timeindexB[1]:
                        Rtime.setBackgroundColor(QColor('orange'))
                        text = QApplication.translate("Table", "%1 DRY END",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                        Rtime.setText(text)
                    elif i == aw.qmc.timeindexB[2]:
                        Rtime.setBackgroundColor(QColor('orange'))
                        text = Rtime.text()
                        text = QApplication.translate("Table", "%1 FC START",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                        Rtime.setText(text)
                    elif i == aw.qmc.timeindexB[3]:
                        Rtime.setBackgroundColor(QColor('orange'))
                        text = QApplication.translate("Table", "%1 DRY END",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                        Rtime.setText(text)
                    elif i == aw.qmc.timeindexB[4]:
                        Rtime.setBackgroundColor(QColor('orange'))
                        text = QApplication.translate("Table", "%1 SC START",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                        Rtime.setText(text)
                    elif i == aw.qmc.timeindexB[5]:
                        Rtime.setBackgroundColor(QColor('orange'))
                        text = QApplication.translate("Table", "%1 SC END",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                        Rtime.setText(text)
                    elif i == aw.qmc.timeindexB[6]:
                        Rtime.setBackgroundColor(QColor('#f07800'))
                        text = QApplication.translate("Table", "%1 END",None, QApplication.UnicodeUTF8).arg(Rtime.text())
                        Rtime.setText(text)
                    elif i in aw.qmc.backgroundEvents:
                        Rtime.setBackgroundColor(QColor('yellow'))
                        index = aw.qmc.backgroundEvents.index(i)
                        text = QApplication.translate("Table", "%1 EVENT #%2 %3%4",None, QApplication.UnicodeUTF8).arg(Rtime.text()).arg(str(index+1)).arg(aw.qmc.Betypes[aw.qmc.backgroundEtypes[index]][0]).arg(str(aw.qmc.backgroundEvalues[index]-1))
                        Rtime.setText(text)
                    
                self.datatable.setItem(i,0,Atime) 
                self.datatable.setItem(i,1,Rtime)
                self.datatable.setItem(i,2,ET)
                self.datatable.setItem(i,3,BT)
                self.datatable.setItem(i,4,deltaBT)
                self.datatable.setItem(i,5,deltaET)

#############################################################################
################  Statistics DIALOG ########################
#############################################################################
            
class StatisticsDLG(QDialog):       
    def __init__(self, parent = None):
        super(StatisticsDLG,self).__init__(parent)
        self.setWindowTitle(QApplication.translate("Form Caption","Statistics",None, QApplication.UnicodeUTF8))
        self.setModal(True)

        regextime = QRegExp(r"^[0-5][0-9]:[0-5][0-9]$")

        self.timez = QCheckBox(QApplication.translate("CheckBox","Time",None, QApplication.UnicodeUTF8))
        self.bar = QCheckBox(QApplication.translate("CheckBox","Bar",None, QApplication.UnicodeUTF8))
        self.flavor = QCheckBox(QApplication.translate("CheckBox","Evaluation",None, QApplication.UnicodeUTF8))
        self.area = QCheckBox(QApplication.translate("CheckBox","Characteristics",None, QApplication.UnicodeUTF8))
                
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

        drylabel =QLabel(QApplication.translate("Label", "Dry",None, QApplication.UnicodeUTF8))
        midlabel =QLabel(QApplication.translate("Label", "Mid",None, QApplication.UnicodeUTF8))
        finishlabel =QLabel(QApplication.translate("Label", "Finish",None, QApplication.UnicodeUTF8))
        minf = QLabel(QApplication.translate("Label", "Min",None, QApplication.UnicodeUTF8))
        maxf = QLabel(QApplication.translate("Label", "Max",None, QApplication.UnicodeUTF8))

        #temp fix for possible bug aw.qmc.statisticsflags=[] > empty list out of range
        if aw.qmc.statisticsflags:
            if aw.qmc.statisticsflags[0]:
                self.timez.setChecked(True)
            if aw.qmc.statisticsflags[1]:
                self.bar.setChecked(True)
            if aw.qmc.statisticsflags[2]:
                self.flavor.setChecked(True)
            if aw.qmc.statisticsflags[3]:
                self.area.setChecked(True)
        else:
            aw.qmc.statisticsflags = [1,1,1,1]
            
        self.connect(self.timez,SIGNAL("stateChanged(int)"),lambda x=0: self.changeStatisticsflag(x,0)) 
        self.connect(self.bar,SIGNAL("stateChanged(int)"),lambda x=0: self.changeStatisticsflag(x,1)) 
        self.connect(self.flavor,SIGNAL("stateChanged(int)"),lambda x=0: self.changeStatisticsflag(x,2)) 
        self.connect(self.area,SIGNAL("stateChanged(int)"),lambda x=0: self.changeStatisticsflag(x,3)) 


        okButton = QPushButton(QApplication.translate("Button","OK",None, QApplication.UnicodeUTF8))
        resetButton = QPushButton(QApplication.translate("Button","Defaults",None, QApplication.UnicodeUTF8))
        self.connect(okButton, SIGNAL("clicked()"),self, SLOT("accept()"))
        self.connect(resetButton, SIGNAL("clicked()"),self.initialsettings)   
        
        flagsLayout = QGridLayout()
        flagsLayout.addWidget(self.timez,0,0)
        flagsLayout.addWidget(self.bar,0,1)
        flagsLayout.addWidget(self.flavor,0,2)
        flagsLayout.addWidget(self.area,0,3)
        
        layout = QGridLayout()
        layout.addWidget(minf,0,1)
        layout.addWidget(maxf,0,2)

        layout.addWidget(drylabel,1,0,Qt.AlignRight)
        layout.addWidget(self.mindryedit,1,1)
        layout.addWidget(self.maxdryedit,1,2)
        layout.addWidget(midlabel,2,0,Qt.AlignRight)
        layout.addWidget(self.minmidedit,2,1)
        layout.addWidget(self.maxmidedit,2,2)
        layout.addWidget(finishlabel,3,0,Qt.AlignRight)
        layout.addWidget(self.minfinishedit,3,1)
        layout.addWidget(self.maxfinishedit,3,2)
        
        resetButton.setFocusPolicy(Qt.NoFocus)
        
        eventsGroupLayout = QGroupBox(QApplication.translate("GroupBox","Evaluation",None, QApplication.UnicodeUTF8))
        eventsGroupLayout.setLayout(layout)
        
        displayGroupLayout = QGroupBox(QApplication.translate("GroupBox","Display",None, QApplication.UnicodeUTF8))
        displayGroupLayout.setLayout(flagsLayout)
        
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(resetButton)
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(okButton)
                
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(displayGroupLayout)
        mainLayout.addWidget(eventsGroupLayout)
        mainLayout.addStretch()
        mainLayout.addLayout(buttonsLayout)
        
        mainLayout.setSizeConstraint(QLayout.SetFixedSize)

        self.setLayout(mainLayout)        

        
    def changeStatisticsflag(self,value,i):
        aw.qmc.statisticsflags[i] = value
        aw.qmc.redraw()

            
    def initialsettings(self):
        aw.qmc.statisticsconditions = [180,360,180,600,180,360]        
        self.close()
        aw.showstatistics()

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
            
            if self.timez.isChecked(): 
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
        self.mutex = QMutex()
        
        #default initial settings. They are changed by settingsload() at initiation of program acording to the device chosen
        self.comport = u"COM4"      #NOTE: this string should not be translated. It is an argument for lib Pyserial
        self.baudrate = 9600
        self.bytesize = 8
        self.parity= 'O'
        self.stopbits = 1
        self.timeout=1

        #serial port for ET/BT
        self.SP  = serial.Serial()

        #list of comm ports available after Scan
        self.commavailable = []

        ##### SPECIAL METER FLAGS ########

        #stores the id of the meter HH506RA as a string
        self.HH506RAid = "X"

        #select PID type that controls the roaster. 
        self.controlETpid = [0,1]        # [type 0 = FujiPXG 1= FujiPXR3, second number is unitID] Can be changed in device menu. Reads/Controls ET
        self.readBTpid = [1,2]           # [type 0 = FujiPXG 1= FujiPXR3 2 = None, second number is unitID] Can be changed in device menu. Reads BT

        #initial message flag for CENTER 309 meter
        self.CENTER309flag = 0

        #Initialization for ARDUINO and TC4 meter
        self.arduinoETChannel = "1"
        self.arduinoBTChannel = "2"
        self.ArduinoIsInitialized = 0
        self.ArduinoUnit = ""


        #list of functions calls to read temperature for devices.
        # device 0 (with index 0 bellow) is Fuji Pid
        # device 1 (with index 1 bellow) is Omega HH806
        # device 2 (with index 2 bellow) is omega HH506
        # etc
        self.devicefunctionlist = [self.fujitemperature,    #0
                                   self.HH806AU,            #1
                                   self.HH506RA,            #2
                                   self.CENTER309,          #3
                                   self.CENTER306,          #4
                                   self.CENTER305,          #5
                                   self.CENTER304,          #6
                                   self.CENTER303,          #7
                                   self.CENTER302,          #8
                                   self.CENTER301,          #9
                                   self.CENTER300,          #10
                                   self.VOLTCRAFTK204,      #11
                                   self.VOLTCRAFTK202,      #12
                                   self.VOLTCRAFT300K,      #13
                                   self.VOLTCRAFT302KJ,     #14
                                   self.EXTECH421509,       #15
                                   self.HH802U,             #16
                                   self.HH309,              #17
                                   self.NONE,               #18
                                   self.ARDUINOTC4,         #19
                                   self.TEVA18B,            #20
                                   self.CENTER309_34,       #21
                                   self.fujidutycycle,      #22
                                   self.HHM28,              #23
                                   self.K204_34,            #24
                                   self.virtual             #25
                                   ]

        #temporary storage to pass values. Holds extra T3 and T4 values for center 309
        self.extra309T3 = 0.
        self.extra309T4 = 0.
        self.extra309TX = 0.

        #temporary storage to pass values. Holds the power % ducty cycle of Fuji PIDs  and ET-BT      
        self.dutycycle = 0.
        self.dutycycleTX = 0.
        self.fujiETBT = 0.
        self.currentpidsv = 0.

#################################################


    #finds time, ET and BT when using Fuji PID. Updates sv (set value) LCD. Finds power duty cycle
    def fujitemperature(self):
        
        #update ET SV LCD 6
        self.currentpidsv = aw.pid.readcurrentsv()

        # get the temperature for ET. RS485 unit ID (1)
        t1 = aw.pid.gettemperature(1)/10.  #Need to divide by 10 beacuse using 1 decimal point in Fuji (ie. received 843 = 84.3)
        #get time of temperature reading in seconds from start; .elapsed() returns miliseconds
        tx = aw.qmc.timeclock.elapsed()/1000.

        #if Fuji for BT is not None (0= PXG, 1 = PXR, 2 = None)
        if self.readBTpid[0] != 2:                    
            # get the temperature for BT. RS485 unit ID (2)
            t2 = aw.pid.gettemperature(2)/10.
        else:
            t2 = 0.

        #get current duty cycle and update LCD 7
        self.dutycycle = aw.pid.readdutycycle()
        self.dutycycleTX = tx
        if t2:
            aw.qmc.fujiETBT = t1-t2
        else:
            aw.qmc.fujiETBT = 0.
        
        return tx,t1,t2


    def virtual(self):
        tx = aw.qmc.timeclock.elapsed()/1000.
        return tx,1.,1.

    #especial function that collects extra duty cycle % and ET minus BT while keeping compatibility
    def fujidutycycle(self):
        #return saved readings from device 0
        return aw.ser.dutycycleTX, aw.ser.dutycycle, aw.ser.fujiETBT   

    def HH506RA(self):
        
        t2,t1 = self.HH506RAtemperature()
        tx = aw.qmc.timeclock.elapsed()/1000.

        return tx,t2,t1

    def HH806AU(self):

         t2,t1 = self.HH806AUtemperature()
         tx = aw.qmc.timeclock.elapsed()/1000.

         return tx,t2,t1

    def HH802U(self):

         t2,t1 = self.HH806AUtemperature()
         tx = aw.qmc.timeclock.elapsed()/1000.

         return tx,t2,t1

    def HH309(self):
         t2,t1 = self.CENTER309temperature()
         tx = aw.qmc.timeclock.elapsed()/1000.

         return tx,t2,t1   

    def CENTER309(self):

         t2,t1 = self.CENTER309temperature()
         tx = aw.qmc.timeclock.elapsed()/1000.

         return tx,t2,t1         

    #especial function that collects extra T3 and T4 from center 309 while keeping compatibility
    def CENTER309_34(self):
         #return saved readings collected at self.CENTER309temperature()
         return aw.ser.extra309TX,aw.ser.extra309T3,aw.ser.extra309T4 

    def CENTER306(self):

         t2,t1 = self.CENTER306temperature()
         tx = aw.qmc.timeclock.elapsed()/1000.

         return tx,t2,t1
        
    def CENTER305(self):

         t2,t1 = self.CENTER306temperature()
         tx = aw.qmc.timeclock.elapsed()/1000.

         return tx,t2,t1

    def CENTER304(self):

         t2,t1 = self.CENTER309temperature()
         tx = aw.qmc.timeclock.elapsed()/1000.

         return tx,t2,t1         


    def CENTER303(self):

         t2,t1 = self.CENTER303temperature()
         tx = aw.qmc.timeclock.elapsed()/1000.

         return tx,t2,t1    

    def CENTER302(self):

         t2,t1 = self.CENTER303temperature()
         tx = aw.qmc.timeclock.elapsed()/1000.

         return tx,t2,t1  

    def CENTER301(self):

         t2,t1 = self.CENTER303temperature()
         tx = aw.qmc.timeclock.elapsed()/1000.

         return tx,t2,t1

    def CENTER300(self):

         t2,t1 = self.CENTER303temperature()
         tx = aw.qmc.timeclock.elapsed()/1000.

         return tx,t2,t1  
        
    def VOLTCRAFTK204(self):
        
         t2,t1 = self.CENTER309temperature()
         tx = aw.qmc.timeclock.elapsed()/1000.
         
         return tx,t2,t1

    #especial function that collects extra T3 and T4 from Vol K204 while keeping compatibility
    def K204_34(self):
         #return saved readings collected at self.CENTER309temperature()
         return aw.ser.extra309TX,aw.ser.extra309T3,aw.ser.extra309T4 

    def VOLTCRAFTK202(self):
        
         t2,t1 = self.CENTER306temperature()
         tx = aw.qmc.timeclock.elapsed()/1000.
         
         return tx,t2,t1
        
    def VOLTCRAFT300K(self):
        
         t2,t1 = self.CENTER303temperature()
         tx = aw.qmc.timeclock.elapsed()/1000.
         
         return tx,t2,t1

    def VOLTCRAFT302KJ(self):
        
         t2,t1 = self.CENTER303temperature()
         tx = aw.qmc.timeclock.elapsed()/1000.
         
         return tx,t2,t1
        
    def EXTECH421509(self):
        
        t2,t1 = self.HH506RAtemperature()
        tx = aw.qmc.timeclock.elapsed()/1000.

        return tx,t2,t1

    def NONE(self):
        tx = aw.qmc.timeclock.elapsed()/1000.        
        t2,t1 = self.NONE()
        
        return tx,t2,t1

    def ARDUINOTC4(self):
        t2,t1 = self.ARDUINOTC4temperature()
        tx = aw.qmc.timeclock.elapsed()/1000.

        return tx,t2,t1

    def TEVA18B(self):
        t2,t1 = self.TEVA18Btemperature()
        tx = aw.qmc.timeclock.elapsed()/1000.

        return tx,t2,t1

    #multimeter
    def HHM28(self):
        val,symbols= self.HHM28multimeter()  #NOTE: val and symbols are type strings
        tx = aw.qmc.timeclock.elapsed()/1000.

        #temporary fix to display the output
        aw.sendmessage(val + symbols)

        if "L" in val:  #L = Out of Range
            return tx, 0., 0.
##        else:
##            #read quantifier symbols
##            if "n" in symbols:
##                val /= 1000000000.
##            elif "u" in symbols:
##                val /= 1000000.
##            elif "m" in symbols:
##                val /= 1000.
##            elif "k" in symbols:
##                val *= 1000.
##            elif "M" in symbols:
##                val *= 1000000.

            ### not finished
        else:
            return tx, 0., float(val)   #send a 0. as second reading because the meter only returns one reading
############################################################################        
        
    def openport(self):
        try:
            #self.closeport()
            self.confport()
            self.ArduinoIsInitialized = 0  # Assume the Arduino has to be reinitialized
            self.ArduinoUnit = ""

            #open port
            if not self.SP.isOpen():
                self.SP.open()
               
        except serial.SerialException,e:
            self.SP.close()
            error = QApplication.translate("Error Message","Serial Exception: Unable to open serial port ",None, QApplication.UnicodeUTF8)
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)

    #loads configuration to ports
    def confport(self):
        self.SP.setPort(self.comport)
        self.SP.setBaudrate(self.baudrate)
        self.SP.setByteSize(self.bytesize)
        self.SP.setParity(self.parity)
        self.SP.setStopbits(self.stopbits)
        self.SP.setTimeout(self.timeout)

    def closeport(self):
        self.SP.close()
            
    def closeEvent(self):
        try:        
           self.closeport() 
        except serial.SerialException,e:
            pass
        
    # function used by Fuji PIDs
    def sendFUJIcommand(self,binstring,nbytes):
        try:
            self.mutex.lock()            
            if not self.SP.isOpen():
                self.openport()                   
            if self.SP.isOpen():
                self.SP.flushInput()
                self.SP.flushOutput()
                self.SP.write(binstring)
                r = self.SP.read(nbytes)
                #serTX.close()
                libtime.sleep(0.035)                     #this gurantees a minimum of 35 miliseconds between readings (for all Fujis)
                lenstring = len(r)
                if lenstring:
                    # CHECK FOR RECEIVED ERROR CODES
                    if ord(r[1]) == 128:
                            if ord(r[2]) == 1:
                                 errorcode = QApplication.translate("Error Message"," F80h, ERROR 1: A nonexistent function code was specified. Please check the function code. ",None, QApplication.UnicodeUTF8)
                                 errorcode += QApplication.translate("Error Message","SendFUJIcommand(): ERROR 1 Illegal Function in unit %1 ",None, QApplication.UnicodeUTF8).arg(ord(command[0]))
                                 aw.qmc.adderror(errorcode)
                            if ord(r[2]) == 2:
                                 errorcode = QApplication.translate("Error Message","F80h, ERROR 2: Faulty address for coil or resistor: The specified relative address for the coil number or resistor\n number cannot be used by the specified function code. ",None, QApplication.UnicodeUTF8)
                                 errorcode += QApplication.translate("Error Message","SendFUJIcommand() ERROR 2 Illegal Address for unit %1 ",None, QApplication.UnicodeUTF8).arg(ord(command[0]))
                                 aw.qmc.adderror(errorcode)
                            if ord(r[2]) == 3:
                                 errorcode = QApplication.translate("Error Message","F80h, ERROR 3: Faulty coil or resistor number: The specified number is too large and specifies a range that does not contain\n coil numbers or resistor numbers.",None, QApplication.UnicodeUTF8)
                                 errorcode += QApplication.translate("Error Message","sendFUJIcommand(): ERROR 3 Illegal Data Value for unit %1 ",None, QApplication.UnicodeUTF8).arg(ord(command[0]))
                                 aw.qmc.adderror(errorcode)
                    else:
                        #Check crc16
                        crcRx =  int(binascii.hexlify(r[-1]+r[-2]),16)
                        crcCal1 = aw.pid.fujiCrc16(r[:-2]) 
                        if crcCal1 == crcRx:  
                            return r           #OK. Return r after it has been checked for errors
                        else:
                            aw.qmc.adderror(QApplication.translate("Error Message","Crc16 data corruption ERROR. TX does not match RX. Check wiring ",None, QApplication.UnicodeUTF8))
                            return "0"
                else:
                    aw.qmc.adderror(QApplication.translate("Error Message","No RX data received ",None, QApplication.UnicodeUTF8))
                    return u"0"
            else:
                return u"0"                                    
                
        except serial.SerialException,e:
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            error = QApplication.translate("Error Message","SerialException: ser.sendFUJIcommand() ",None, QApplication.UnicodeUTF8)
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)
            return "0"
        
        finally:
            self.mutex.unlock()
            
     #t2 and t1 from Omega HH806 or HH802 meter 
    def HH806AUtemperature(self):
        try:
            self.mutex.lock()
            
            if not self.SP.isOpen():
                self.openport()
                
            if self.SP.isOpen():
                self.SP.flushInput()
                self.SP.flushOutput()
                command = "#0A0000NA2\r\n"  #"#0A0101NA4\r\n"
                self.SP.write(command)
                r = self.SP.read(14) 

                if len(r) == 14:
                    #convert to binary to hex string
                    s1 = binascii.hexlify(r[5] + r[6])
                    s2 = binascii.hexlify(r[10]+ r[11])

                    #we convert the strings to integers. Divide by 10.0 (decimal position)
                    return int(s1,16)/10., int(s2,16)/10.
                else:
                    nbytes = len(r)
                    aw.qmc.adderror(QApplication.translate("Error Message","HH806AUtemperature(): %1 bytes received but 14 needed",None, QApplication.UnicodeUTF8).arg(nbytes))
                    if len(aw.qmc.timex) > 2:                           #if there are at least two completed readings
                        return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       # then new reading = last reading (avoid possible single errors) 
                    else:
                        return -1,-1                                    #return something out of scope to avoid function error (expects two values)

            else:
                if len(aw.qmc.timex) > 2:                           
                    return aw.qmc.temp1[-1], aw.qmc.temp2[-1]        
                else:
                    return -1,-1                                    
                                   
        except serial.SerialException, e:
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            error = QApplication.translate("Error Message","Serial Exception: ser.HH806AUtemperature() ",None, QApplication.UnicodeUTF8)
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)
            if len(aw.qmc.timex) > 2:                           
                return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
            else:
                return -1,-1                                    

        finally:
            self.mutex.unlock()
            
    #HH506RA Device
    #returns t1,t2 from Omega HH506 meter. By Marko Luther
    def HH506RAtemperature(self):
        #if initial id "X" has not changed then get a new one;
        if self.HH506RAid == "X":                                         
            self.HH506RAGetID()                       # obtain new id one time; self.HH506RAid should not be "X" any more
            if self.HH506RAid == "X":                 # if self.HH506RAGetID() went wrong and self.HH506RAid is still "X"
                aw.qmc.adderror(QApplication.translate("Error Message","HH506RAtemperature(): Unable to get id from HH506RA device ",None, QApplication.UnicodeUTF8))
                return -1,-1
           
        try:
            self.mutex.lock()
            
            if not self.SP.isOpen():
                self.openport()                    
               
            if self.SP.isOpen():
                self.SP.flushInput()
                self.SP.flushOutput()
                command = "#" + self.HH506RAid + "N\r\n"
                self.SP.write(command)
                r = self.SP.read(14)

                if len(r) == 14: 
                    #we convert the hex strings to integers. Divide by 10.0 (decimal position)
                    return int(r[1:5],16)/10., int(r[7:11],16)/10.                
                else:
                    nbytes = len(r)
                    aw.qmc.adderror(QApplication.translate("Error Message","HH506RAtemperature(): %1 bytes received but 14 needed",None, QApplication.UnicodeUTF8).arg(nbytes))               
                    if len(aw.qmc.timex) > 2:                           
                        return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
                    else:
                        return -1,-1 
            else:
                if len(aw.qmc.timex) > 2:                           
                    return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
                else:
                    return -1,-1 
                
        except serial.SerialException, e:
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            error = QApplication.translate("Error Message","Serial Exception: ser.HH506RAtemperature() ",None, QApplication.UnicodeUTF8)
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)
            if len(aw.qmc.timex) > 2:                           
                return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
            else:
                return -1,-1
            
        finally:
            self.mutex.unlock()
            
    #reads once the id of the HH506RA meter and stores it in the serial variable self.HH506RAid. Marko Luther.
    def HH506RAGetID(self):   
        try:
            self.mutex.lock()
            
            if not self.SP.isOpen():
                self.openport()                    
                
            if self.SP.isOpen():
                self.SP.flushInput()
                self.SP.flushOutput()
                sync = None
                while sync != "Err\r\n":
                    self.SP.write("\r\n")
                    sync = self.SP.read(5)
                    libtime.sleep(1)
                    
                self.SP.write("%000R")
                ID = self.SP.read(5)
                if len(ID) == 5:
                    self.HH506RAid =  ID[0:3]               # Assign new id to self.HH506RAid
                else:
                    nbytes = len(ID)
                    aw.qmc.adderror(QApplication.translate("Error Message","HH506RAGetID: %1 bytes received but 5 needed",None, QApplication.UnicodeUTF8).arg(nbytes))
                    
        except serial.SerialException, e:
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            error = QApplication.translate("Error Message","Serial Exception: ser.HH506RAGetID()",None, QApplication.UnicodeUTF8)
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)
            
        finally:
            self.mutex.unlock()
            
    def CENTER306temperature(self):
        try:
            self.mutex.lock()
            
            if not self.SP.isOpen():
                self.openport()                    
                
            if self.SP.isOpen():
                self.SP.flushInput()
                self.SP.flushOutput()
                command = "\x41"                 
                self.SP.write(command)
                r = self.SP.read(10)                                  #NOTE: different
                
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
                    error  = QApplication.translate("Error Message","CENTER306temperature(): %1 bytes received but 10 needed ",None, QApplication.UnicodeUTF8).arg(nbytes)
                    timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
                    #keep a max of 500 errors
                    if len(aw.qmc.errorlog) > 499:
                        aw.qmc.errorlog = aw.qmc.errorlog[1:]
                    aw.qmc.errorlog.append(timez + " " + error)                   
                    if len(aw.qmc.timex) > 2:                           
                        return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
                    else:
                        return -1,-1 
            else:
                if len(aw.qmc.timex) > 2:                           
                    return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
                else:
                    return -1,-1 
                     
        except serial.SerialException, e:
            error  = QApplication.translate("Error Message","Serial Exception: ser.CENTER306temperature() ",None, QApplication.UnicodeUTF8)
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)
            if len(aw.qmc.timex) > 2:                           
                return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
            else:
                return -1,-1
            
        finally:
            self.mutex.unlock()
            
    def NONE(self):
        dialogx = nonedevDlg( )
        if dialogx.exec_():
            ET = int(dialogx.etEdit.text())
            BT = int(dialogx.btEdit.text())
            aw.lcd2.display(ET)                               # ET
            aw.lcd3.display(BT)
            return ET,BT
        else:
            return -1,-1
            
    def CENTER303temperature(self):
        try:
            self.mutex.lock()
            
            if not self.SP.isOpen():
                self.openport()                    
                
            if self.SP.isOpen():
                self.SP.flushInput()
                self.SP.flushOutput()
                command = "\x41"                 
                self.SP.write(command)
                r = self.SP.read(8)                                   #NOTE: different
                
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
                    error = QApplication.translate("Error Message","CENTER303temperature(): %i bytes received but 8 needed ",None, QApplication.UnicodeUTF8).arg(nbytes)
                    timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
                    #keep a max of 500 errors
                    if len(aw.qmc.errorlog) > 499:
                        aw.qmc.errorlog = aw.qmc.errorlog[1:]
                    aw.qmc.errorlog.append(timez + " " + error)
                    if len(aw.qmc.timex) > 2:                           
                        return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
                    else:
                        return -1,-1 
            else:
                if len(aw.qmc.timex) > 2:                           
                    return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
                else:
                    return -1,-1 
            
        except serial.SerialException, e:
            error = QApplication.translate("Error Message","Serial Exception: ser.CENTER303temperature()",None, QApplication.UnicodeUTF8)
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)
            if len(aw.qmc.timex) > 2:                           
                return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
            else:
                return -1,-1
            
        finally:
            self.mutex.unlock()
            
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
        ##                                        THIS ONLY WORKS WHEN TEMPERATURE < 200. If T >= 200 r[43] changes

        try:
            self.mutex.lock()
            
            if not self.SP.isOpen():
                self.openport()
                
            if self.SP.isOpen():
                self.SP.flushInput()
                self.SP.flushOutput()
                command = "\x41"
                self.SP.write(command)
                r = self.SP.read(45)

                if len(r) == 45:
                    T1 = int(binascii.hexlify(r[7] + r[8]),16)/10.
                    T2 = int(binascii.hexlify(r[9] + r[10]),16)/10.
                    #save these variables if using T3 and T4
                    self.extra309T3 = int(binascii.hexlify(r[11] + r[12]),16)/10.
                    self.extra309T4 = int(binascii.hexlify(r[13] + r[14]),16)/10.
                    self.extra309TX = aw.qmc.timeclock.elapsed()/1000.
                    return T1,T2
                
                else:
                    nbytes = len(r)
                    aw.qmc.adderror(QApplication.translate("Error Message","ser.CENTER309(): %1 bytes received but 45 needed ",None, QApplication.UnicodeUTF8).arg(nbytes))            
                    if len(aw.qmc.timex) > 2:                           
                        return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
                    else:
                        return -1,-1 
            else:
                    if len(aw.qmc.timex) > 2:                           
                        return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
                    else:
                        return -1,-1
                                
        except serial.SerialException, e:
            error  = QApplication.translate("Error Message","Serial Exception: ser.CENTER309temperature() ",None, QApplication.UnicodeUTF8)
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)
            if len(aw.qmc.timex) > 2:                           
                return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
            else:
                return -1,-1

        finally:
            self.mutex.unlock()
            
    def ARDUINOTC4temperature(self):
        try:
            self.mutex.lock()
            
            if not self.SP.isOpen():
                self.openport()
                libtime.sleep(3)

                #Reinitialize Arduino in case communication was interupted
                self.ArduinoIsInitialized = 0
                self.ArduinoUnit = ""
                
            if self.SP.isOpen():

                if not self.ArduinoIsInitialized:
                    self.SP.flushInput()
                    self.SP.flushOutput()

                    command = "CHAN;" + self.arduinoETChannel + self.arduinoBTChannel + "00\n"  
                    self.SP.write(command)

                    try:
                        result = ""
                        result = self.SP.readline()

                        if (not result == "" and not result.startswith("#")):
                            raise
                        elif result.startswith("#"):
                            self.ArduinoIsInitialized = 1
                            self.ArduinoUnit = ""  # For good measure...
                    except:
                        aw.qmc.errorlog.append(QApplication.translate("Error Message","Arduino could not set channels: ser.ARDUINOTC4temperature() ",None, QApplication.UnicodeUTF8)) + result

                if not self.ArduinoUnit == aw.qmc.mode:
                    self.SP.flushInput()
                    self.SP.flushOutput()
                
                    command = "UNIT;" + aw.qmc.mode + "\n"   #Set units
                    self.ArduinoUnit = aw.qmc.mode
                    self.SP.write(command)

                    try:
                        result = ""
                        result = self.SP.readline()
                        if (not result == "" and not result.startswith("#")):
                            raise
                    except:
                        aw.qmc.errorlog.append(QApplication.translate("Error Message","Arduino could not set temperature unit: ser.ARDUINOTC4temperature() ",None, QApplication.UnicodeUTF8)) + result
                        self.ArduinoUnit = ""

                self.SP.flushInput()
                self.SP.flushOutput()

                command = "READ\n"  #Read command. Will used set channels and units
                self.SP.write(command)
                                
                res = self.SP.readline().rsplit(',')  # a list [t0,t1,t2] with t0 = ambient; t1 = ET; t2 = BT (for now)
                t0 = 0 
                if len(aw.qmc.timex) > 2:                           
                    t1 = aw.qmc.temp1[-1]
                    t2 = aw.qmc.temp2[-1]     
                else:
                    t1 = t2 = -1
                try:
                    t0 = float(res[0])
                except:
                    pass
                try:
                    t1 = float(res[1])
                except:
                    pass
                try:
                    t2 = float(res[2])
                except:
                    pass
                if t0 and not self.ArduinoIsInitialized:
                    aw.qmc.ambientTemp = t0
                    
                return t1, t2

        except serial.SerialException, e:
            error = QApplication.translate("Error Message","Serial Exception: ser.ARDUINOTC4temperature() ",None, QApplication.UnicodeUTF8)
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]

            aw.qmc.errorlog.append(timez + " " + error)
            if len(aw.qmc.timex) > 2:                           
                return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
            else:
                return -1,-1
            
        finally:
            self.mutex.unlock()
            
    def TEVA18Bconvert(self, seg):
        if seg == 0x7D:
            return 0
        elif seg == 0x05:
            return 1
        elif seg == 0x5B:
            return 2
        elif seg == 0x1F:
            return 3
        elif seg == 0x27:
            return 4
        elif seg == 0x3E:
            return 5
        elif seg == 0x7E:
            return 6
        elif seg == 0x15:
            return 7
        elif seg == 0x7F:
            return 8
        elif seg == 0x3F:
            return 9
        else:
            return -1

    def TEVA18Btemperature(self):
        try:
            self.mutex.lock()
            
            run = 1
            counter = 0
            
            while(run):
                
                #MaWa
                #really interesting:
                #need this sleep. without artisan hungs after 20 to 40 seconds.
                #seems like iam running the loop forever, forever .... with sleep it is ok
                #seen this sometimes in communication between threads in C or C++. --> volatile problem?
                if counter > 0:
                    libtime.sleep(1)
                
                counter = counter + 1
            
                if not self.SP.isOpen():
                    self.openport()    
                    libtime.sleep(2)
                    
                if self.SP.isOpen():
                    self.SP.flushInput()

                    r = self.SP.read(14)
                    
                    if len(r) != 14:
                        continue

#                    s200 = binascii.hexlify(r[0])
                    s201 = binascii.hexlify(r[1])
                    s202 = binascii.hexlify(r[2])
                    s203 = binascii.hexlify(r[3])
                    s204 = binascii.hexlify(r[4])
                    s205 = binascii.hexlify(r[5])
                    s206 = binascii.hexlify(r[6])
                    s207 = binascii.hexlify(r[7])
                    s208 = binascii.hexlify(r[8])
    #                s209 = binascii.hexlify(r[9])
    #                s210 = binascii.hexlify(r[10])
    #                s211 = binascii.hexlify(r[11])
    #                s212 = binascii.hexlify(r[12])
                    s213 = binascii.hexlify(r[13])
               
 #                   t200 = int(s200,16)
                    t201 = int(s201,16)
                    t202 = int(s202,16)
                    t203 = int(s203,16)
                    t204 = int(s204,16)
                    t205 = int(s205,16)
                    t206 = int(s206,16)
                    t207 = int(s207,16)
                    t208 = int(s208,16)
    #                t209 = int(s209,16)
    #                t210 = int(s210,16)
    #                t211 = int(s211,16)
    #                t212 = int(s212,16)
                    t213 = int(s213,16)

                    # is meter in temp mode?
                    # first check byte order
                    if(((t213 & 0xf0) >> 4) != 14):
                        #ERROR try again .....
                        continue

                    elif(((t213 & 0x0f) & 0x02) != 2 ):
                        #ERROR
                        # device seems not to be in temp mode, break here
                        raise ValueError
                    
                    # convert
                    bNegative = 0
                    iDivisor = 0

                    # first lets check the byte order
                    # seg1 bytes
                    if (((t201 & 0xf0) >> 4) == 2) and (((t202 & 0xf0) >> 4 ) == 3):
                        seg1 = ((t201 & 0x0f) << 4) + (t202 & 0x0f)
                    else:
                        continue
                        
                    # seg2 bytes
                    if (((t203 & 0xf0) >> 4) == 4) and (((t204 & 0xf0) >> 4 ) == 5):
                        seg2 = ((t203 & 0x0f) << 4) + (t204 & 0x0f)
                    else:
                        continue
                        
                    # seg3 bytes
                    if (((t205 & 0xf0) >> 4) == 6) and (((t206 & 0xf0) >> 4 ) == 7):
                        seg3 = ((t205 & 0x0f) << 4) + (t206 & 0x0f)
                    else:
                        continue
                        
                    # seg4 bytes
                    if (((t207 & 0xf0) >> 4) == 8) and (((t208 & 0xf0) >> 4 ) == 9):
                        seg4 = ((t207 & 0x0f) << 4) + (t208 & 0x0f)
                    else:
                        continue
                        
                    # is negative?
                    if (seg1 & 0x80):
                        bNegative = 1
                        seg1 = seg1 & ~0x80
                    # check divisor
                    if (seg2 & 0x80):
                        iDivisor = 1000.
                        seg2 = seg2 & ~0x80
                    elif (seg3 & 0x80):
                        iDivisor = 100.
                        seg3 = seg3 & ~0x80        
                    elif (seg4 & 0x80):
                        iDivisor = 10.
                        seg4 = seg4 & ~0x80
                        
                    iValue = 0
                    fReturn = 0
                    
                    i = self.TEVA18Bconvert(seg1)
                    if ( i < 0 ):
                        # recv nonsense, try again
                        continue

                    iValue = i * 1000

                    i = self.TEVA18Bconvert(seg2)
                    if ( i < 0 ):
                        # recv nonsense, try again
                        continue

                    iValue = iValue + (i * 100)
                    i = self.TEVA18Bconvert(seg3)
                    
                    if ( i < 0 ):
                        # recv nonsense, try again
                        continue

                    iValue = iValue + (i * 10)
                    i = self.TEVA18Bconvert(seg4)
                    
                    if ( i < 0 ):
                        # recv nonsense, try again
                        continue
                    
                    iValue = iValue + i
                    
                    # what about the divisor?
                    if( iDivisor > 0 ):
                        fReturn = iValue / iDivisor
                    # is value negative?
                    if( fReturn ):
                        if( bNegative ):
                            fReturn = fReturn * (-1)
                    
                    #ok seems we got valid value
                    # break loop here
                    run = 0
                
            #Since the meter reads only one temperature, send 0 as ET and fReturn as BT
            if fReturn:
                return 0.,fReturn    #  **** RETURN T HERE  ******
            else:
                raise ValueError

        except ValueError:
            error  = QApplication.translate("Error Message","Value Error: ser.TEVA18Btemperature() ",None, QApplication.UnicodeUTF8)
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)
            if len(aw.qmc.timex) > 2:                           
                return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
            else:
                return -1,-1 
        
        except serial.SerialException:
            error  = QApplication.translate("Error Message","Serial Exception: ser.TEVA18Btemperature() ",None, QApplication.UnicodeUTF8)
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)
            if len(aw.qmc.timex) > 2:                           
                return aw.qmc.temp1[-1], aw.qmc.temp2[-1]       
            else:
                return -1,-1 

        finally:
            self.mutex.unlock()
            
    def HHM28multimeter(self):
        # This meter sends a continuos frame byte by byte. It only transmits data. It does not receive commands.
        # A frame is composed of 14 ordered bytes. A byte is represented bellow enclosed in "XX"
        # FRAME  = ["1A","2B","3C","4D","5E","6F","7G","8H","9I","10J","11K","12L","13M","14N"]
        # The first 4 bits of each byte are dedicated to identify the byte in the frame by using a number.
        # The last 4 bits of each byte are dedicated to carry Data. Depending on the byte number, the meaning of data changes.
        # Bytes 2,3,4,5,6,7,8,9 carry data bits that represent actual segments of the four LCD numbers of the meter display.
        # Bytes 1,10,11,12,13 carry data bits that represent other symbols like F (for Farad), u (for micro), M (for Mega), etc, of the meter display

        try:
            self.mutex.lock()
            
            if not self.SP.isOpen():
                self.openport()                    
                
            if self.SP.isOpen():
                self.SP.flushInput()
                self.SP.flushOutput()

            r, r2 = "",""
            #keep reading till the first byte of next frame (till we read an actual 1 in 1A )
            for i in range(28):  #any number > 14 will be OK     
                r = self.SP.read(1)
                if len(r):
                    fb = (ord(r[0]) & 0xf0) >> 4
                    if fb == 1:
                        r2 = self.SP.read(13)   #read the remaining 13 bytes to get 14 bytes
                        break
                else:
                    raise ValueError, unicode("No Data received")
                    
    
            frame = r + r2
            
            #check bytes
            for i in range(14):
                number  = fb = (ord(frame[i]) & 0xf0) >> 4
                if number != i+1:
                    #find device index
                    raise ValueError, unicode("Data corruption")

            if len(frame) == 14:
                #extract data from frame in to a list containing the hex string values of the data
                data = []
                for i in range(14):
                    data.append(hex((ord(frame[i]) & 0x0f))[2:])

                #The four LCD digits are BC + DE + FG + HI   
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
                table = {"00":" ","68":"L","7d":"0","05":"1","5b":"2","1f":"3",
                         "27":"4","3e":"5","7e":"6","15":"7","7f":"8","3f":"9"} 
                val = ""
                #some erros found in values: "38","5d",0A,etc
                for i in range(4):
                    if digits[i] in table:
                        val += table[digits[i]]
                    else:
                        raise ValueError, unicode("Data corruption")
                    
                number = ".".join((val[:dec],val[dec:]))  #add the decimal point

                #find symbols
                tablesymbols = [
                                ["AC","","",""],    	    	#["AC","","Auto","RS232"]
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
                            symbols += " " + tablesymbols[p][i]            
                return (sign + number), symbols
            else:
                raise ValueError, unicode("Needed 14 bytes but only received %i"%(len(frame)))

        
        except ValueError,e:
            error  = QApplication.translate("Error Message","Value Error: ser.HHM28multimeter() ",None, QApplication.UnicodeUTF8)
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)
            #find device index
            if aw.qmc.device == 23:
                if len(aw.qmc.temp1):
                    return str(aw.qmc.temp1[-1]),str(aw.qmc.temp2[-1])
                else:
                    return "0",""
            else:
                index = aw.qmc.extradevices.index(23)
                if len(aw.qmc.extratemp1[i]):
                    return str(aw.qmc.extratemp1[index][-1]),str(aw.qmc.temp2[index][-1])
                else:
                    return "0",""
        
        except serial.SerialException:
            error  = QApplication.translate("Error Message","Serial Exception: ser.HHM28multimeter() ",None, QApplication.UnicodeUTF8)
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)
            return "0",""
        
        finally:
            self.mutex.unlock()

    #sends a command to the ET/BT device
    def sendTXcommand(self,command):
        try:
            self.mutex.lock()
            
            if not self.SP.isOpen():
                self.openport()
                libtime.sleep(3)
                
                #Reinitialize Arduino in case communication was interrupted
                if aw.qmc.device == 19:
                    self.ArduinoIsInitialized = 0
                    self.ArduinoUnit
                    
            if self.SP.isOpen():
                if (aw.qmc.device == 19 and not command.endswith("\n")):
                    command += "\n"
                    
                self.SP.write(command)

        except serial.SerialException:
            error  = QApplication.translate("Error Message","Serial Exception: ser.sendTXcommand() ",None, QApplication.UnicodeUTF8)
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)
        
        finally:
            self.mutex.unlock()

    #Example function
    #NOT USED YET, maybe FUTURE Arduino?
    #sends a command to the ET/BT device and receives data of length nbytes 
    def sendTXRXcommand(self,command,nbytes):
        try:
            self.mutex.lock()
            self.SP.write(command)
            r = self.SP.read(nbytes)            
            if len(r) == nbytes:
                return r
            else:
                return "ERR"

        except serial.SerialException:
            error  = QApplication.translate("Error Message","Serial Exception: ser.sendTXRXcommand() ",None, QApplication.UnicodeUTF8)
            timez = unicode(QDateTime.currentDateTime().toString(QString("hh:mm:ss.zzz")))    #zzz = miliseconds
            #keep a max of 500 errors
            if len(aw.qmc.errorlog) > 499:
                aw.qmc.errorlog = aw.qmc.errorlog[1:]
            aw.qmc.errorlog.append(timez + " " + error)
        
        finally:
            self.mutex.unlock()
            
#########################################################################
#############  DESIGNER CONFIG DIALOG ###################################                                   
###############################################################
class designerconfigDlg(QDialog):
    def __init__(self, parent = None):
        super(designerconfigDlg,self).__init__(parent)
        self.setWindowTitle(QApplication.translate("Form Caption","Designer Config",None, QApplication.UnicodeUTF8))

        #landmarks
        charge = QLabel(QApplication.translate("Label", "CHARGE",None, QApplication.UnicodeUTF8))
        charge.setStyleSheet("background-color: #f07800")
        self.dryend = QCheckBox(QApplication.translate("CheckBox","DRY END",None, QApplication.UnicodeUTF8))
        self.dryend.setStyleSheet("background-color: orange")
        self.fcs = QCheckBox(QApplication.translate("CheckBox","FC START",None, QApplication.UnicodeUTF8))
        self.fcs.setStyleSheet("background-color: orange")
        self.fce = QCheckBox(QApplication.translate("CheckBox","FC END",None, QApplication.UnicodeUTF8))
        self.fce.setStyleSheet("background-color: orange")
        self.scs = QCheckBox(QApplication.translate("CheckBox","SC START",None, QApplication.UnicodeUTF8))
        self.scs.setStyleSheet("background-color: orange")
        self.sce = QCheckBox(QApplication.translate("CheckBox","SC END",None, QApplication.UnicodeUTF8))
        self.sce.setStyleSheet("background-color: orange")
        drop = QLabel(QApplication.translate("Label", "DROP",None, QApplication.UnicodeUTF8))
        drop.setStyleSheet("background-color: #f07800")


        self.loadconfigflags()
        
        self.connect(self.dryend, SIGNAL("stateChanged(int)"),lambda x=0: self.changeflags(x,1))
        self.connect(self.fcs, SIGNAL("stateChanged(int)"),lambda x=0: self.changeflags(x,2))
        self.connect(self.fce, SIGNAL("stateChanged(int)"),lambda x=0: self.changeflags(x,3))
        self.connect(self.scs, SIGNAL("stateChanged(int)"),lambda x=0: self.changeflags(x,4))
        self.connect(self.sce, SIGNAL("stateChanged(int)"),lambda x=0: self.changeflags(x,5))

        if aw.qmc.timeindex[0] != -1:
            start = aw.qmc.timex[aw.qmc.timeindex[0]]
        else:
            start = 0

        self.Edit0 = QLineEdit(aw.qmc.stringfromseconds(0))
        self.Edit0.setEnabled(False)

        if aw.qmc.timeindex[1]:
            self.Edit1 = QLineEdit(aw.qmc.stringfromseconds(aw.qmc.timex[aw.qmc.timeindex[1]] - start))      
        else:
            self.Edit1 = QLineEdit(aw.qmc.stringfromseconds(0))                                       
        if aw.qmc.timeindex[2]:
            self.Edit2 = QLineEdit(aw.qmc.stringfromseconds(aw.qmc.timex[aw.qmc.timeindex[2]] - start))      
        else:
            self.Edit2 = QLineEdit(aw.qmc.stringfromseconds(0))                                       
        if aw.qmc.timeindex[3]:
            self.Edit3 = QLineEdit(aw.qmc.stringfromseconds(aw.qmc.timex[aw.qmc.timeindex[3]] - start))      
        else:
            self.Edit3 = QLineEdit(aw.qmc.stringfromseconds(0))                                       
        if aw.qmc.timeindex[4]:
            self.Edit4 = QLineEdit(aw.qmc.stringfromseconds(aw.qmc.timex[aw.qmc.timeindex[4]] - start))      
        else:
            self.Edit4 = QLineEdit(aw.qmc.stringfromseconds(0))                                       
        if aw.qmc.timeindex[5]:
            self.Edit5 = QLineEdit(aw.qmc.stringfromseconds(aw.qmc.timex[aw.qmc.timeindex[5]] - start))      
        else:
            self.Edit5 = QLineEdit(aw.qmc.stringfromseconds(0))                                       
        if aw.qmc.timeindex[6]:
            self.Edit6 = QLineEdit(aw.qmc.stringfromseconds(aw.qmc.timex[aw.qmc.timeindex[6]] - start))      
        else:
            self.Edit6 = QLineEdit(aw.qmc.stringfromseconds(0))
        self.Edit6.setEnabled(False)

        self.Edit1copy = self.Edit1.text()            
        self.Edit2copy = self.Edit1.text()            
        self.Edit3copy = self.Edit1.text()            
        self.Edit4copy = self.Edit1.text()            
        self.Edit5copy = self.Edit1.text()                      
       
        regextime = QRegExp(r"^-?[0-5][0-9]:[0-5][0-9]$")
        self.Edit0.setValidator(QRegExpValidator(regextime,self))
        self.Edit1.setValidator(QRegExpValidator(regextime,self))
        self.Edit2.setValidator(QRegExpValidator(regextime,self))
        self.Edit3.setValidator(QRegExpValidator(regextime,self))
        self.Edit4.setValidator(QRegExpValidator(regextime,self))
        self.Edit5.setValidator(QRegExpValidator(regextime,self))
        self.Edit6.setValidator(QRegExpValidator(regextime,self))
        
        self.Edit0.setMaximumWidth(50)
        self.Edit1.setMaximumWidth(50)
        self.Edit2.setMaximumWidth(50)
        self.Edit3.setMaximumWidth(50)
        self.Edit4.setMaximumWidth(50)
        self.Edit5.setMaximumWidth(50)
        self.Edit6.setMaximumWidth(50)

        splinelabel = QLabel(QApplication.translate("Label", "Curviness",None, QApplication.UnicodeUTF8))
        etcurviness = QLabel(QApplication.translate("Label", "ET",None, QApplication.UnicodeUTF8))
        btcurviness = QLabel(QApplication.translate("Label", "BT",None, QApplication.UnicodeUTF8))
        etcurviness.setAlignment(Qt.AlignRight)
        btcurviness.setAlignment(Qt.AlignRight)
        self.ETsplineComboBox = QComboBox()
        self.ETsplineComboBox.setMaximumWidth(30)                                  
        self.ETsplineComboBox.addItems(["1","2","3","4","5"])
        self.ETsplineComboBox.setCurrentIndex(aw.qmc.ETsplinedegree - 1)
        self.connect(self.ETsplineComboBox,SIGNAL("currentIndexChanged(int)"), self.redrawcurviness)

        self.BTsplineComboBox = QComboBox()
        self.BTsplineComboBox.setMaximumWidth(30)                                  
        self.BTsplineComboBox.addItems(["1","2","3","4","5"])
        self.BTsplineComboBox.setCurrentIndex(aw.qmc.BTsplinedegree - 1)
        self.connect(self.BTsplineComboBox,SIGNAL("currentIndexChanged(int)"), self.redrawcurviness)


        reproducelabel = QLabel(QApplication.translate("Label", "Events Playback",None, QApplication.UnicodeUTF8))
        self.reproduceComboBox = QComboBox()
        self.reproduceComboBox.addItems([QApplication.translate("ComboBox","None",None, QApplication.UnicodeUTF8),
                                         QApplication.translate("ComboBox","BT Rate of Change",None, QApplication.UnicodeUTF8),
                                         QApplication.translate("ComboBox","ET Rate of Change",None, QApplication.UnicodeUTF8),
                                         QApplication.translate("ComboBox","Machine SV commands",None, QApplication.UnicodeUTF8),
                                         QApplication.translate("ComboBox","Machine Ramp command",None, QApplication.UnicodeUTF8)])
        self.reproduceComboBox.setCurrentIndex(aw.qmc.reproducedesigner)
        self.connect(self.reproduceComboBox,SIGNAL("currentIndexChanged(int)"), self.changereproducemode)

        saveButton = QPushButton(QApplication.translate("Button","Update",None, QApplication.UnicodeUTF8))
        self.connect(saveButton, SIGNAL("clicked()"), self.settimes)
        #saveButton.setMaximumWidth(50)
        
        defaultButton = QPushButton(QApplication.translate("Button","Reset",None, QApplication.UnicodeUTF8))
        self.connect(defaultButton, SIGNAL("clicked()"), self.reset)
        closeButton = QPushButton(QApplication.translate("Button","Close",None, QApplication.UnicodeUTF8))
        self.connect(closeButton, SIGNAL("clicked()"),self, SLOT("accept()"))
               
        convertButton = QPushButton(QApplication.translate("Button","Create",None, QApplication.UnicodeUTF8))
        self.connect(convertButton, SIGNAL("clicked()"),self.create)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(defaultButton)
        buttonLayout.addWidget(closeButton)
        buttonLayout.addWidget(convertButton) 
           
        marksLayout = QGridLayout()  
        marksLayout.addWidget(charge,0,0)
        marksLayout.addWidget(self.Edit0,0,1)
        marksLayout.addWidget(self.dryend,1,0)
        marksLayout.addWidget(self.Edit1,1,1)
        marksLayout.addWidget(self.fcs,2,0)
        marksLayout.addWidget(self.Edit2,2,1)
        marksLayout.addWidget(self.fce,3,0)
        marksLayout.addWidget(self.Edit3,3,1)
        marksLayout.addWidget(self.scs,4,0)
        marksLayout.addWidget(self.Edit4,4,1)
        marksLayout.addWidget(self.sce,5,0)
        marksLayout.addWidget(self.Edit5,5,1)
        marksLayout.addWidget(drop,6,0)
        marksLayout.addWidget(self.Edit6,6,1)
        marksLayout.addWidget(saveButton,7,1)

        curvinessLayout = QHBoxLayout()
        curvinessLayout.addWidget(etcurviness)
        curvinessLayout.addWidget(self.ETsplineComboBox)
        curvinessLayout.addWidget(btcurviness)        
        curvinessLayout.addWidget(self.BTsplineComboBox)                                 

        modLayout = QGridLayout()
        modLayout.addWidget(splinelabel,0,0)
        modLayout.addLayout(curvinessLayout,0,1)        
        modLayout.addWidget(reproducelabel,1,0)
        modLayout.addWidget(self.reproduceComboBox,1,1)
        
        marksGroupLayout = QGroupBox(QApplication.translate("GroupBox","Initial Times",None, QApplication.UnicodeUTF8))
        marksGroupLayout.setLayout(marksLayout)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(marksGroupLayout)
        mainLayout.addLayout(modLayout)
        mainLayout.addLayout(buttonLayout)
        
        self.setLayout(mainLayout)

    def changereproducemode(self):
        aw.qmc.reproducedesigner = self.reproduceComboBox.currentIndex()
        
    def redrawcurviness(self):
        ETcurviness = int(self.ETsplineComboBox.currentText())
        BTcurviness = int(self.BTsplineComboBox.currentText())
                                        
        timepoints = len(aw.qmc.timex)
                                          
        if (timepoints - ETcurviness) >= 1:
            aw.qmc.ETsplinedegree = ETcurviness
        else:
            aw.qmc.ETsplinedegree = len(aw.qmc.timex)-1
            self.ETsplineComboBox.setCurrentIndex(aw.qmc.ETsplinedegree-1)
            ms = QApplication.translate("MessageBox","Not enough time points for an ET curviness of %1. Set curviness to %2",None, QApplication.UnicodeUTF8).arg(ETcurviness).arg(aw.qmc.ETsplinedegree)
            QMessageBox.information(self,QApplication.translate("MessageBox Caption","Designer Config",None, QApplication.UnicodeUTF8),ms) 

        if (timepoints - BTcurviness) >= 1:
            aw.qmc.BTsplinedegree = BTcurviness
        else:
            aw.qmc.BTsplinedegree = len(aw.qmc.timex)-1
            self.BTsplineComboBox.setCurrentIndex(aw.qmc.BTsplinedegree-1)
            ms = QApplication.translate("MessageBox","Not enough time points for an BT curviness of %1. Set curviness to %2",None, QApplication.UnicodeUTF8).arg(BTcurviness).arg(aw.qmc.BTsplinedegree)
            QMessageBox.information(self,QApplication.translate("MessageBox Caption","Designer Config",None, QApplication.UnicodeUTF8),ms) 
                                          
        aw.qmc.redrawdesigner()

    def settimes(self):
        #check input
        strings = [QApplication.translate("MessageBox","CHARGE",None, QApplication.UnicodeUTF8),
                   QApplication.translate("MessageBox","DRY END",None, QApplication.UnicodeUTF8),
                   QApplication.translate("MessageBox","FC START",None, QApplication.UnicodeUTF8),
                   QApplication.translate("MessageBox","FC END",None, QApplication.UnicodeUTF8),
                   QApplication.translate("MessageBox","SC START",None, QApplication.UnicodeUTF8),
                   QApplication.translate("MessageBox","SC END",None, QApplication.UnicodeUTF8),
                   QApplication.translate("MessageBox","DROP",None, QApplication.UnicodeUTF8)]
        timecheck = self.validatetime()
        if timecheck != 1000:
            st = QApplication.translate("MessageBox","Incorrect time format. Please recheck %1 time",None, QApplication.UnicodeUTF8).arg(strings[timecheck])
            QMessageBox.information(self,QApplication.translate("MessageBox Caption","Designer Config",None, QApplication.UnicodeUTF8),st)            
            return 1
        
        checkvalue = self.validatetimeorder()
        if checkvalue != 1000:
            st = QApplication.translate("MessageBox","Times need to be in ascending order. Please recheck %1 time",None, QApplication.UnicodeUTF8).arg(strings[checkvalue+1])
            QMessageBox.information(self,QApplication.translate("MessageBox Caption","Designer Config",None, QApplication.UnicodeUTF8),st)            
            return 1
        
        if self.dryend.isChecked():
            if self.Edit1.text() != self.Edit1copy:
                if aw.qmc.stringtoseconds(unicode(self.Edit1.text())):
                    timez = aw.qmc.stringtoseconds(unicode(self.Edit1.text()))+ aw.qmc.timex[aw.qmc.timeindex[0]]
                    aw.qmc.timeindex[1] = aw.qmc.designerfindindex(timez)
                    aw.qmc.timex[aw.qmc.timeindex[1]] = timez                
        if self.fcs.isChecked():
            if self.Edit2.text() != self.Edit2copy:
                if aw.qmc.stringtoseconds(unicode(self.Edit2.text())):
                    timez = aw.qmc.stringtoseconds(unicode(self.Edit2.text()))+ aw.qmc.timex[aw.qmc.timeindex[0]]
                    aw.qmc.timeindex[2] = aw.qmc.designerfindindex(timez)
                    aw.qmc.timex[aw.qmc.timeindex[2]] = timez 
        if self.fce.isChecked():
            if self.Edit3.text() != self.Edit3copy:
                if aw.qmc.stringtoseconds(unicode(self.Edit3.text())):
                    timez = aw.qmc.stringtoseconds(unicode(self.Edit3.text()))+ aw.qmc.timex[aw.qmc.timeindex[0]]
                    aw.qmc.timeindex[3] = aw.qmc.designerfindindex(timez)
                    aw.qmc.timex[aw.qmc.timeindex[3]] = timez 
        if self.scs.isChecked():
            if self.Edit4.text() != self.Edit4copy:
                if aw.qmc.stringtoseconds(unicode(self.Edit4.text())):
                    timez = aw.qmc.stringtoseconds(unicode(self.Edit4.text()))+ aw.qmc.timex[aw.qmc.timeindex[0]]
                    aw.qmc.timeindex[4] = aw.qmc.designerfindindex(timez)
                    aw.qmc.timex[aw.qmc.timeindex[4]] = timez 
        if self.sce.isChecked():
            if self.Edit5.text() != self.Edit5copy:
                if aw.qmc.stringtoseconds(unicode(self.Edit5.text())):
                    timez = aw.qmc.stringtoseconds(unicode(self.Edit5.text()))+ aw.qmc.timex[aw.qmc.timeindex[0]]
                    aw.qmc.timeindex[5] = aw.qmc.designerfindindex(timez)
                    aw.qmc.timex[aw.qmc.timeindex[5]] = timez 

        for i in range(1,6): #1-5
            aw.qmc.designertimeinit[i] = aw.qmc.timex[aw.qmc.timeindex[i]]

        aw.qmc.redrawdesigner()
        return 0
            
        
    #supporting function for settimes()
    def validatetimeorder(self):
        time = []
        checks = self.readchecks()
        time.append(aw.qmc.stringtoseconds(unicode(self.Edit0.text())) + aw.qmc.timex[aw.qmc.timeindex[0]])       
        time.append(aw.qmc.stringtoseconds(unicode(self.Edit1.text())) + aw.qmc.timex[aw.qmc.timeindex[0]])        
        time.append(aw.qmc.stringtoseconds(unicode(self.Edit2.text())) + aw.qmc.timex[aw.qmc.timeindex[0]])        
        time.append(aw.qmc.stringtoseconds(unicode(self.Edit3.text())) + aw.qmc.timex[aw.qmc.timeindex[0]])        
        time.append(aw.qmc.stringtoseconds(unicode(self.Edit4.text())) + aw.qmc.timex[aw.qmc.timeindex[0]])        
        time.append(aw.qmc.stringtoseconds(unicode(self.Edit5.text())) + aw.qmc.timex[aw.qmc.timeindex[0]])        
        time.append(aw.qmc.stringtoseconds(unicode(self.Edit6.text())) + aw.qmc.timex[aw.qmc.timeindex[0]])
        for i in range(len(time)-1):
            if time[i+1] <= time[i] and checks[i+1] != 0:
                return i
        return 1000
    
    def validatetime(self):
        strings = []
        strings.append(self.Edit0.text())
        strings.append(self.Edit1.text())
        strings.append(self.Edit2.text())
        strings.append(self.Edit3.text())
        strings.append(self.Edit4.text())
        strings.append(self.Edit5.text())
        strings.append(self.Edit6.text())
        for i in range(len(strings)):
            if len(unicode(strings[i])) < 5:
                return i
        else:
            return 1000
    
    #supporting function for settimes()       
    def readchecks(self):
        checks = [0,0,0,0,0,0,0]
        if self.dryend.isChecked(): 
            checks[1] = 1
        if self.fcs.isChecked():
            checks[2] = 1
        if self.fce.isChecked():
            checks[3] = 1
        if self.scs.isChecked():
            checks[4] = 1
        if self.sce.isChecked():
            checks[5] = 1
            
        return checks
                   
    def create(self):
        self.close()
        aw.qmc.convert_designer()

    #reset
    def reset(self):
        self.dryend.setChecked(True)
        self.fcs.setChecked(True)
        self.fce.setChecked(True)
        self.scs.setChecked(True)
        self.sce.setChecked(True)
        aw.qmc.reset_designer()        
        self.Edit0.setText(aw.qmc.stringfromseconds(0))
        self.Edit1.setText(aw.qmc.stringfromseconds(aw.qmc.designertimeinit[1]))
        self.Edit2.setText(aw.qmc.stringfromseconds(aw.qmc.designertimeinit[2]))
        self.Edit3.setText(aw.qmc.stringfromseconds(aw.qmc.designertimeinit[3]))
        self.Edit4.setText(aw.qmc.stringfromseconds(aw.qmc.designertimeinit[4]))
        self.Edit5.setText(aw.qmc.stringfromseconds(aw.qmc.designertimeinit[5]))
        self.Edit6.setText(aw.qmc.stringfromseconds(aw.qmc.designertimeinit[6]))
        aw.sendmessage(QApplication.translate("Message Area","Designer has been reset",None, QApplication.UnicodeUTF8)).arg()

    def loadconfigflags(self):
        if aw.qmc.timeindex[1]:
            self.dryend.setChecked(True)
        else:
            self.dryend.setChecked(False)
        if aw.qmc.timeindex[2]:
            self.fcs.setChecked(True)
        else:
            self.fcs.setChecked(False)
        if aw.qmc.timeindex[3]:
            self.fce.setChecked(True)
        else:
            self.fce.setChecked(False)
        if aw.qmc.timeindex[4]:
            self.scs.setChecked(True)
        else:
            self.scs.setChecked(False)
        if aw.qmc.timeindex[5]:
            self.sce.setChecked(True)
        else:
            self.sce.setChecked(False)

    #adds deletes landmarks        
    def changeflags(self,x,idi):
        if self.validatetimeorder() != 1000:
            if idi == 1:
                self.dryend.setChecked(False)
            elif idi == 2:
                self.fcs.setChecked(False)
            elif idi == 3:
                self.fce.setChecked(False)
            elif idi == 4:
                self.scs.setChecked(False)
            elif idi == 5:
                self.sce.setChecked(False)

            strings = [QApplication.translate("MessageBox","CHARGE",None, QApplication.UnicodeUTF8),
                       QApplication.translate("MessageBox","DRY END",None, QApplication.UnicodeUTF8),
                       QApplication.translate("MessageBox","FC START",None, QApplication.UnicodeUTF8),
                       QApplication.translate("MessageBox","FC END",None, QApplication.UnicodeUTF8),
                       QApplication.translate("MessageBox","SC START",None, QApplication.UnicodeUTF8),
                       QApplication.translate("MessageBox","SC END",None, QApplication.UnicodeUTF8),
                       QApplication.translate("MessageBox","DROP",None, QApplication.UnicodeUTF8)]
            st = QApplication.translate("MessageBox","Times need to be in ascending order. Please recheck %1 time",None, QApplication.UnicodeUTF8).arg(strings[idi])
            QMessageBox.information(self,QApplication.translate("MessageBox Caption","Designer Config",None, QApplication.UnicodeUTF8),st)    
            return
        
        #idi = id index
        if aw.qmc.timeindex[idi]:                    
            #ERASE mark point
            aw.qmc.currentx = aw.qmc.timex[aw.qmc.timeindex[idi]]
            aw.qmc.currenty = aw.qmc.temp2[aw.qmc.timeindex[idi]]
            aw.qmc.removepoint()
        else:
            #ADD mark point
            if idi == 1:
                timez = aw.qmc.stringtoseconds(unicode(self.Edit1.text())) + aw.qmc.timex[aw.qmc.timeindex[0]]
            if idi == 2:
                timez = aw.qmc.stringtoseconds(unicode(self.Edit2.text())) + aw.qmc.timex[aw.qmc.timeindex[0]]
            if idi == 3:
                timez = aw.qmc.stringtoseconds(unicode(self.Edit3.text())) + aw.qmc.timex[aw.qmc.timeindex[0]]
            if idi == 4:
                timez = aw.qmc.stringtoseconds(unicode(self.Edit4.text())) + aw.qmc.timex[aw.qmc.timeindex[0]]
            if idi == 5:
                timez = aw.qmc.stringtoseconds(unicode(self.Edit5.text())) + aw.qmc.timex[aw.qmc.timeindex[0]]

            tempindex = aw.qmc.designerfindindex(timez)
            temp = aw.qmc.temp2[tempindex]
            aw.qmc.currentx = timez 
            aw.qmc.currenty = temp
            newindex = aw.qmc.addpoint()
            aw.qmc.timeindex[idi] = newindex
       
               
#########################################################################
#############  NONE DEVICE DIALOG #######################################                                   
#########################################################################

#inputs temperature            
class nonedevDlg(QDialog):
    def __init__(self, parent = None):
        super(nonedevDlg,self).__init__(parent)
        self.setWindowTitle(QApplication.translate("Form Caption","Manual Temperature Logger",None, QApplication.UnicodeUTF8))
       
        if len(aw.qmc.timex):
            if aw.qmc.manuallogETflag:
                etval = str(int(aw.qmc.temp1[-1]))
            else:
                etval = "0"
            btval = str(int(aw.qmc.temp2[-1])) 
        else:
            etval = "0"
            btval = "0"
        
        self.etEdit = QLineEdit(etval)
        btlabel = QLabel(QApplication.translate("Label", "BT",None, QApplication.UnicodeUTF8))
        self.btEdit = QLineEdit(btval)
        self.etEdit.setValidator(QIntValidator(0, 1000, self.etEdit))
        self.btEdit.setValidator(QIntValidator(0, 1000, self.btEdit))

        self.ETbox = QCheckBox(QApplication.translate("CheckBox","ET",None, QApplication.UnicodeUTF8))
        if aw.qmc.manuallogETflag == True:
            self.ETbox.setChecked(True)
            
        else:
            self.ETbox.setChecked(False)
            self.etEdit.setVisible(False)            
           
        self.connect(self.ETbox,SIGNAL("stateChanged(int)"),self.changemanuallogETflag)

        okButton = QPushButton(QApplication.translate("Button","OK",None, QApplication.UnicodeUTF8))
        cancelButton = QPushButton(QApplication.translate("Button","Cancel",None, QApplication.UnicodeUTF8))
        cancelButton.setFocusPolicy(Qt.NoFocus)

        self.connect(okButton, SIGNAL("clicked()"),self, SLOT("accept()"))
        self.connect(cancelButton, SIGNAL("clicked()"),self, SLOT("reject()"))
        
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()  
        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(okButton)
        
        grid = QGridLayout()
        grid.addWidget(self.ETbox,0,0)
        grid.addWidget(self.etEdit,0,1)
        
        grid.addWidget(btlabel,1,0)
        grid.addWidget(self.btEdit,1,1)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(grid)
        mainLayout.addStretch()  
        mainLayout.addLayout(buttonLayout)
        
        self.setLayout(mainLayout)

    def changemanuallogETflag(self):
        if self.ETbox.isChecked():
            aw.qmc.manuallogETflag = 1
            self.etEdit.setVisible(True)
        else:
            aw.qmc.manuallogETflag = 0
            self.etEdit.setVisible(False)

        
                
#########################################################################
#############  SERIAL PORT CONFIGURATION DIALOG #########################                                   
#########################################################################

            
class comportDlg(QDialog):
    def __init__(self, parent = None):
        super(comportDlg,self).__init__(parent)
        self.setWindowTitle(QApplication.translate("Form Caption","Serial Ports Configuration",None, QApplication.UnicodeUTF8))
              
        self.setModal(True)

        ##########################    TAB 1 WIDGETS        
        comportlabel =QLabel(QApplication.translate("Label", "Comm Port", None, QApplication.UnicodeUTF8))
        self.comportEdit = QComboBox()
        self.comportEdit.addItems([aw.ser.comport])
        self.comportEdit.setEditable(True)
        comportlabel.setBuddy(self.comportEdit)

        baudratelabel = QLabel(QApplication.translate("Label", "Baud Rate", None, QApplication.UnicodeUTF8))
        self.baudrateComboBox = QComboBox()
        baudratelabel.setBuddy(self.baudrateComboBox)
        self.bauds = ["2400","9600","19200","57600"]
        self.baudrateComboBox.addItems(self.bauds)
        self.baudrateComboBox.setCurrentIndex(self.bauds.index(str(aw.ser.baudrate)))
                   
        bytesizelabel = QLabel(QApplication.translate("Label", "Byte Size",None, QApplication.UnicodeUTF8))
        self.bytesizeComboBox = QComboBox()
        bytesizelabel.setBuddy(self.bytesizeComboBox)
        self.bytesizes = ["7","8"]
        self.bytesizeComboBox.addItems(self.bytesizes)
        self.bytesizeComboBox.setCurrentIndex(self.bytesizes.index(str(aw.ser.bytesize)))

        paritylabel = QLabel(QApplication.translate("Label", "Parity",None, QApplication.UnicodeUTF8))
        self.parityComboBox = QComboBox()
        paritylabel.setBuddy(self.parityComboBox)
        #0 = Odd, E = Even, N = None. NOTE: These strings cannot be translated as they are arguments to the lib pyserial.
        self.parity = ["O","E","N"]
        self.parityComboBox.addItems(self.parity)
        self.parityComboBox.setCurrentIndex(self.parity.index(aw.ser.parity))

        stopbitslabel = QLabel(QApplication.translate("Label", "Stopbits",None, QApplication.UnicodeUTF8))
        self.stopbitsComboBox = QComboBox()
        stopbitslabel.setBuddy(self.stopbitsComboBox)
        self.stopbits = ["0","1","2"]
        self.stopbitsComboBox.addItems(self.stopbits)
        self.stopbitsComboBox.setCurrentIndex(aw.ser.stopbits)
        
        timeoutlabel = QLabel(QApplication.translate("Label", "Timeout",None, QApplication.UnicodeUTF8))
        self.timeoutEdit = QLineEdit(str(aw.ser.timeout))
        self.timeoutEdit.setValidator(QIntValidator(0,5,self.timeoutEdit))


        self.messagelabel = QLabel()
        
        okButton = QPushButton(QApplication.translate("Button","OK",None, QApplication.UnicodeUTF8))
        cancelButton = QPushButton(QApplication.translate("Button","Cancel",None, QApplication.UnicodeUTF8))
        cancelButton.setFocusPolicy(Qt.NoFocus)
        scanButton = QPushButton(QApplication.translate("Button","Scan for Ports",None, QApplication.UnicodeUTF8))
        scanButton.setFocusPolicy(Qt.NoFocus)

        self.connect(okButton, SIGNAL("clicked()"),self, SLOT("accept()"))
        self.connect(cancelButton, SIGNAL("clicked()"),self, SLOT("reject()"))
        self.connect(scanButton, SIGNAL("clicked()"), self.scanforport)        

        ##########################    TAB 2  WIDGETS   EXTRA DEVICES
        self.serialtable = QTableWidget()
        self.serialtable.setTabKeyNavigation(True)
        self.createserialTable()

        #tab1 layout
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(scanButton)
        buttonLayout.addStretch()  
        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(okButton)


        grid = QGridLayout()
        grid.addWidget(comportlabel,0,0,Qt.AlignRight)
        grid.addWidget(self.comportEdit,0,1)
        grid.addWidget(baudratelabel,1,0,Qt.AlignRight)
        grid.addWidget(self.baudrateComboBox,1,1)
        grid.addWidget(bytesizelabel,2,0,Qt.AlignRight)
        grid.addWidget(self.bytesizeComboBox,2,1)
        grid.addWidget(paritylabel,3,0,Qt.AlignRight)
        grid.addWidget(self.parityComboBox,3,1)
        grid.addWidget(stopbitslabel,4,0,Qt.AlignRight)
        grid.addWidget(self.stopbitsComboBox,4,1)
        grid.addWidget(timeoutlabel,5,0,Qt.AlignRight)
        grid.addWidget(self.timeoutEdit,5,1)
        grid.addWidget(self.messagelabel,6,1)
        
        gridBoxLayout = QHBoxLayout()
        gridBoxLayout.addLayout(grid)
        gridBoxLayout.addStretch()  
        
        tab1Layout = QVBoxLayout()
        tab1Layout.addLayout(gridBoxLayout)
        tab1Layout.addStretch()  


        #LAYOUT TAB 2
        tab2Layout = QVBoxLayout()
        tab2Layout.addWidget(self.serialtable)

        #tab widget
        TabWidget = QTabWidget()
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        TabWidget.addTab(C1Widget,QApplication.translate("Tab","ET/BT",None, QApplication.UnicodeUTF8))

        C2Widget = QWidget()
        C2Widget.setLayout(tab2Layout)
        TabWidget.addTab(C2Widget,QApplication.translate("Tab","Extra",None, QApplication.UnicodeUTF8))

        #incorporate layouts
        Mlayout = QVBoxLayout()
        Mlayout.addWidget(TabWidget)
        Mlayout.addLayout(buttonLayout)
        
        self.setLayout(Mlayout)

    def createserialTable(self):
        try:
            self.serialtable.clear()        
            ndevices = len(aw.qmc.extradevices)
            if ndevices:    
                self.serialtable.setRowCount(ndevices)
                self.serialtable.setColumnCount(7)
                self.serialtable.setHorizontalHeaderLabels([QApplication.translate("Table","Device",None, QApplication.UnicodeUTF8),
                                                            QApplication.translate("Table","Comm Port",None, QApplication.UnicodeUTF8),
                                                            QApplication.translate("Table","Baud Rate",None, QApplication.UnicodeUTF8),
                                                            QApplication.translate("Table","Byte Size",None, QApplication.UnicodeUTF8),
                                                            QApplication.translate("Table","Parity",None, QApplication.UnicodeUTF8),
                                                            QApplication.translate("Table","Stopbits",None, QApplication.UnicodeUTF8),
                                                            QApplication.translate("Table","Timeout",None, QApplication.UnicodeUTF8)])
                self.serialtable.setAlternatingRowColors(True)
                self.serialtable.setEditTriggers(QTableWidget.NoEditTriggers)
                self.serialtable.setSelectionBehavior(QTableWidget.SelectRows)
                self.serialtable.setSelectionMode(QTableWidget.SingleSelection)
                self.serialtable.setShowGrid(True)

                for i in range(ndevices):
                    device = QTableWidgetItem(aw.qmc.devices[aw.qmc.extradevices[i]-1])    #type identification of the device. Non editable

                    comportComboBox =  QComboBox()
                    comportComboBox.addItems(aw.extracomport)
                    comportComboBox.setCurrentIndex(i)

                    baudComboBox =  QComboBox()
                    baudComboBox.addItems(self.bauds)
                    if str(aw.extrabaudrate[i]) in self.bauds:
                        baudComboBox.setCurrentIndex(self.bauds.index(str(aw.extrabaudrate[i])))

                    byteComboBox =  QComboBox()
                    byteComboBox.addItems(self.bytesizes)
                    if str(aw.extrabytesize[i]) in self.bytesizes:
                        byteComboBox.setCurrentIndex(self.bytesizes.index(str(aw.extrabytesize[i])))

                    parityComboBox =  QComboBox()
                    parityComboBox.addItems(self.parity)
                    if aw.extraparity[i] in self.parity:
                        parityComboBox.setCurrentIndex(self.parity.index(aw.extraparity[i]))
                  
                    #self.connect(baudComboBox,SIGNAL("currentIndexChanged(int)"),lambda z=1,x=i:self.setextradevice(z,x))
                     
                    stopbitsComboBox =  QComboBox()
                    stopbitsComboBox.addItems(self.stopbits)
                    if str(aw.extrastopbits[i]) in self.stopbits:
                        stopbitsComboBox.setCurrentIndex(self.stopbits.index(str(aw.extrastopbits[i])))

                    timeoutEdit = QLineEdit(str(aw.extratimeout[i]))
                    timeoutEdit.setValidator(QIntValidator(0,5,timeoutEdit))

                    #add widgets to the table
                    self.serialtable.setItem(i,0,device)              
                    self.serialtable.setCellWidget(i,1,comportComboBox)
                    self.serialtable.setCellWidget(i,2,baudComboBox)                
                    self.serialtable.setCellWidget(i,3,byteComboBox)
                    self.serialtable.setCellWidget(i,4,parityComboBox)              
                    self.serialtable.setCellWidget(i,5,stopbitsComboBox)              
                    self.serialtable.setCellWidget(i,6,timeoutEdit)              
        except Exception,e:
             aw.qmc.adderror(QApplication.translate("Error Message", "createserialTable(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))


    def saveserialtable(self):
        try:
            
            ndevices = len(aw.qmc.extradevices)
            for i in range(ndevices):
                
                comportComboBox =  self.serialtable.cellWidget(i,1)
                aw.extracomport[i] = unicode(comportComboBox.currentText())

                baudComboBox =  self.serialtable.cellWidget(i,2)
                aw.extrabaudrate[i] = int(baudComboBox.currentText())

                byteComboBox =  self.serialtable.cellWidget(i,3)
                aw.extrabytesize[i] = int(byteComboBox.currentText())

                parityComboBox =  self.serialtable.cellWidget(i,4)
                aw.extraparity[i] = unicode(parityComboBox.currentText())

                stopbitsComboBox =  self.serialtable.cellWidget(i,5)
                aw.extrastopbits[i] = int(stopbitsComboBox.currentText())

                timeoutEdit = self.serialtable.cellWidget(i,6)
                aw.extratimeout[i] = int(timeoutEdit.text())

            #create serial ports for each extra device
            nserial = len(aw.extraser)
            if ndevices != nserial:
                aw.extraser = [serialport()]*ndevices

            #load the settings for the extra serial ports found
            for i in range(ndevices):
                aw.extraser[i].SP.setPort(unicode(aw.extracomport[i]))
                aw.extraser[i].SP.setBaudrate(aw.extrabaudrate[i])
                aw.extraser[i].SP.setByteSize(aw.extrabytesize[i])
                aw.extraser[i].SP.setParity(unicode(aw.extraparity[i]))
                aw.extraser[i].SP.setStopbits(aw.extrastopbits[i])
                aw.extraser[i].SP.setTimeout(aw.extratimeout[i])

        except Exception,e:
             aw.qmc.adderror(QApplication.translate("Error Message", "saveserialtable(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))

           
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

        #save extra serial ports by reading the serial extra table
        self.saveserialtable()
        
        try:
            #check here comport errors
            if not comport:
                raise comportError
            if not timeout:
                raise timeoutError
            #add more checks here

            aw.sendmessage(QApplication.translate("Message Area","Serial Port Settings: %1, %2, %3, %4, %5, %6", None, QApplication.UnicodeUTF8).arg(comport).arg(baudrate).arg(bytesize).arg(parity).arg(stopbits).arg(timeout))
                        
        except comportError,e:
            aw.qmc.adderror(QApplication.translate("Error Message","Comport Error: Invalid Comm entry ", None, QApplication.UnicodeUTF8))
            self.comportEdit.selectAll()
            self.comportEdit.setFocus()           
            return

        except timeoutError,e:
            aw.qmc.adderror(QApplication.translate("Error Message","Timeout Error: Invalid Timeout entry ", None, QApplication.UnicodeUTF8))
            self.timeoutEdit.selectAll()
            self.timeoutEdit.setFocus()           
            return
        
        QDialog.accept(self)


    def scanforport(self):
        try:
            aw.ser.closeport()
            
            available = []      
            if platf in ('Windows', 'Microsoft'):
                #scans serial ports in Windows computer
                for i in range(100):
                    try:
                        s = serial.Serial(i)
                        available.append(s.portstr)
                        s.close()  
                    except serial.SerialException,e:
                        pass
                    
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
                    ("/dev/ttyS", "Standard serial port", "serial"), 
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
                self.sendmessage(QApplication.translate("Message Area","Port scan on this platform not yet supported", None, QApplication.UnicodeUTF8))

            #set comboBoxes                        
            self.comportEdit.clear()
            self.comportEdit.addItems(available)
            if len(available):
                if aw.ser.comport in available:
                    self.comportEdit.setCurrentIndex(available.index(aw.ser.comport))
                else:    
                    self.comportEdit.setCurrentIndex(len(available)-1)
                aw.ser.commavailable = available[:]
                for i in range(len(aw.qmc.extradevices)):
                    comportComboBox =  self.serialtable.cellWidget(i,1)
                    comportComboBox.clear()
                    comportComboBox.addItems(aw.ser.commavailable)
                    if aw.extracomport[i] in aw.ser.commavailable:
                        comportComboBox.setCurrentIndex(aw.ser.commavailable.index(aw.extracomport[i]))
                    else:    
                        comportComboBox.setCurrentIndex(len(aw.ser.commavailable)-1)                

        except Exception,e:
             aw.qmc.adderror(QApplication.translate("Error Message", "scanforport(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))

    def closeserialports(self):
        if aw.ser.SP.isOpen():
            aw.ser.SP.close()

#################################################################################            
##################   Device assignments DIALOG for reading temperature   ########
#################################################################################
                
class DeviceAssignmentDLG(QDialog):       
    def __init__(self, parent = None):
        super(DeviceAssignmentDLG,self).__init__(parent)
        self.setWindowTitle(QApplication.translate("Form Caption","Device Assignment", None, QApplication.UnicodeUTF8))
        
        self.setModal(True)

        ################ TAB 1   WIDGETS
        
        self.nonpidButton = QRadioButton(QApplication.translate("Radio Button","Device", None, QApplication.UnicodeUTF8))
        self.pidButton = QRadioButton(QApplication.translate("Radio Button","PID", None, QApplication.UnicodeUTF8))
        self.arduinoButton = QRadioButton(QApplication.translate("Radio Button","Arduino (TC4)", None, QApplication.UnicodeUTF8))

        #As a main device, don't show the devices that start with a "+"
        dev = aw.qmc.devices[:]
        limit = len(dev)
        for k in range(limit):
            for i in range(len(dev)):
                if dev[i][0] == "+":
                    dev.pop(i)              #pop() will make the list smaller 
                    break 
                
        sorted_devices = sorted(dev)
        self.devicetypeComboBox = QComboBox()
        self.devicetypeComboBox.addItems(sorted_devices)
        
        controllabel =QLabel(QApplication.translate("Label", "Control ET",None, QApplication.UnicodeUTF8))                            
        self.controlpidtypeComboBox = QComboBox()
        self.controlpidunitidComboBox = QComboBox()

        ## No need to translate (also used later)            
        self.controlpidtypeComboBox.addItems(["Fuji PXG",
                                              "Fuji PXR"])
        self.controlpidunitidComboBox.addItems(["1","2"])

        label1 = QLabel(QApplication.translate("Label", "Type",None, QApplication.UnicodeUTF8)) 
        label2 = QLabel(QApplication.translate("Label", "Unit ID",None, QApplication.UnicodeUTF8))

        btlabel =QLabel(QApplication.translate("Label", "Read BT",None, QApplication.UnicodeUTF8))                            
        self.btpidtypeComboBox = QComboBox()
        self.btpidunitidComboBox = QComboBox()
        self.btpidtypeComboBox.addItems([QApplication.translate("ComboBox","Fuji PXG",None, QApplication.UnicodeUTF8),
                                         QApplication.translate("ComboBox","Fuji PXR",None, QApplication.UnicodeUTF8),
                                         QApplication.translate("ComboBox","None",None, QApplication.UnicodeUTF8)])
        self.btpidunitidComboBox.addItems(["2","1"])

        #Arduino TC4 channel config
        arduinoChannels = ["None","1","2","3","4"]
        arduinoETLabel =QLabel(QApplication.translate("Label", "ET Channel",None, QApplication.UnicodeUTF8))                            
        self.arduinoETComboBox = QComboBox()
        self.arduinoETComboBox.addItems(arduinoChannels)

        arduinoBTLabel =QLabel(QApplication.translate("Label", "BT Channel",None, QApplication.UnicodeUTF8))                            
        self.arduinoBTComboBox = QComboBox()
        self.arduinoBTComboBox.addItems(arduinoChannels)

        #check previous settings for radio button
        if aw.qmc.device == 0:
            self.pidButton.setChecked(True)
        elif aw.qmc.device == 19:
            self.arduinoButton.setChecked(True)
        else:
            self.nonpidButton.setChecked(True)
            selected_device_index = 0
            try:
                selected_device_index = sorted_devices.index(aw.qmc.devices[aw.qmc.device - 1])            
            except Exception:
                pass
            self.devicetypeComboBox.setCurrentIndex(selected_device_index)           
                
        self.controlpidtypeComboBox.setCurrentIndex(aw.ser.controlETpid[0])
        self.btpidtypeComboBox.setCurrentIndex(aw.ser.readBTpid[0])

        self.arduinoETComboBox.setCurrentIndex(arduinoChannels.index(aw.ser.arduinoETChannel))
        self.arduinoBTComboBox.setCurrentIndex(arduinoChannels.index(aw.ser.arduinoBTChannel))

        if aw.ser.controlETpid[1] == 1 :       # control is PXG4
            self.controlpidunitidComboBox.setCurrentIndex(0)
        else:
            self.controlpidunitidComboBox.setCurrentIndex(1)
        if aw.ser.readBTpid[1] == 1:
            self.btpidunitidComboBox.setCurrentIndex(1)
        else:
            self.btpidunitidComboBox.setCurrentIndex(0)

        okButton = QPushButton(QApplication.translate("Button","OK",None, QApplication.UnicodeUTF8))
        cancelButton = QPushButton(QApplication.translate("Button","Cancel",None, QApplication.UnicodeUTF8))
        cancelButton.setFocusPolicy(Qt.NoFocus)
        self.connect(okButton, SIGNAL("clicked()"),self, SLOT("accept()"))
        self.connect(cancelButton, SIGNAL("clicked()"),self, SLOT("reject()"))        


        ##########################    TAB 2  WIDGETS   "EXTRA DEVICES"
        #table for showing data
        self.devicetable = QTableWidget()
        self.devicetable.setTabKeyNavigation(True)
        self.createDeviceTable()

        addButton = QPushButton(QApplication.translate("Button","Add",None, QApplication.UnicodeUTF8))
        addButton.setFocusPolicy(Qt.NoFocus)
        addButton.setMinimumWidth(100)
        addButton.setMaximumWidth(100)
        self.connect(addButton, SIGNAL("clicked()"),self.adddevice)   
        
        resetButton = QPushButton(QApplication.translate("Button","Reset",None, QApplication.UnicodeUTF8))
        resetButton.setFocusPolicy(Qt.NoFocus)
        resetButton.setMinimumWidth(100)
        resetButton.setMaximumWidth(100)
        self.connect(resetButton, SIGNAL("clicked()"),self.resetextradevices)

        delButton = QPushButton(QApplication.translate("Button","Delete",None, QApplication.UnicodeUTF8))
        delButton.setFocusPolicy(Qt.NoFocus)
        delButton.setMinimumWidth(100)
        delButton.setMaximumWidth(100)
        self.connect(delButton, SIGNAL("clicked()"),self.deldevice)               

        ###########################  TAB 3 WIDGETS "ADVANCED"
        labelETadvanced = QLabel(QApplication.translate("Label", "ET Y(x)",None, QApplication.UnicodeUTF8)) 
        labelBTadvanced = QLabel(QApplication.translate("Label", "BT Y(x)",None, QApplication.UnicodeUTF8)) 
        self.ETfunctionedit = QLineEdit(unicode(aw.qmc.ETfunction))            
        self.BTfunctionedit = QLineEdit(unicode(aw.qmc.BTfunction))            


        #LAYOUT TAB 1
        grid = QGridLayout()

        grid.addWidget(self.nonpidButton,0,0)
        grid.addWidget(self.devicetypeComboBox,0,1)
        
        grid.addWidget(self.pidButton,2,0)
        grid.addWidget(self.arduinoButton,3,0)        

        gridBox = QHBoxLayout()
        gridBox.addLayout(grid)
        gridBox.addStretch()
        
        PIDgrid = QGridLayout()

        PIDgrid.addWidget(label1,0,1)
        PIDgrid.addWidget(label2,0,2)
        PIDgrid.addWidget(controllabel,1,0,Qt.AlignRight)
        PIDgrid.addWidget(self.controlpidtypeComboBox,1,1)
        PIDgrid.addWidget(self.controlpidunitidComboBox,1,2)
                                   
        PIDgrid.addWidget(btlabel,2,0,Qt.AlignRight)
        PIDgrid.addWidget(self.btpidtypeComboBox,2,1)
        PIDgrid.addWidget(self.btpidunitidComboBox,2,2)
        
        PIDBox = QHBoxLayout()
        PIDBox.addLayout(PIDgrid)
        PIDBox.addStretch()
        
        PIDGroupLayout = QGroupBox(QApplication.translate("GroupBox","PID",None, QApplication.UnicodeUTF8))
        PIDGroupLayout.setLayout(PIDBox)

        arduinogrid = QGridLayout()

        arduinogrid.addWidget(arduinoETLabel,1,0,Qt.AlignRight)
        arduinogrid.addWidget(self.arduinoETComboBox,1,1)
        arduinogrid.addWidget(arduinoBTLabel,2,0,Qt.AlignRight)
        arduinogrid.addWidget(self.arduinoBTComboBox,2,1)
        
        arduinoBox = QHBoxLayout()
        arduinoBox.addLayout(arduinogrid)
        arduinoBox.addStretch()
        
        arduinoGroupLayout = QGroupBox(QApplication.translate("GroupBox","Arduino (TC4)",None, QApplication.UnicodeUTF8))
        arduinoGroupLayout.setLayout(arduinoBox)        

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()  
        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(okButton)
        
        tab1Layout = QVBoxLayout()
        tab1Layout.addLayout(gridBox)
        tab1Layout.addWidget(PIDGroupLayout)
        tab1Layout.addWidget(arduinoGroupLayout)
        
        tab1Layout.addWidget(labelETadvanced)
        tab1Layout.addWidget(self.ETfunctionedit)
        tab1Layout.addWidget(labelBTadvanced)
        tab1Layout.addWidget(self.BTfunctionedit)
        
        tab1Layout.addStretch()  

        bLayout = QHBoxLayout()
        bLayout.addWidget(addButton)
        bLayout.addWidget(delButton)
        bLayout.addStretch()
        bLayout.addSpacing(10)
        bLayout.addWidget(resetButton)
        
        #LAYOUT TAB 2
        tab2Layout = QVBoxLayout()
        tab2Layout.addWidget(self.devicetable)
        tab2Layout.addLayout(bLayout)

        #tab widget
        TabWidget = QTabWidget()
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        TabWidget.addTab(C1Widget,QApplication.translate("Tab","ET/BT",None, QApplication.UnicodeUTF8))

        C2Widget = QWidget()
        C2Widget.setLayout(tab2Layout)
        TabWidget.addTab(C2Widget,QApplication.translate("Tab","Extra",None, QApplication.UnicodeUTF8))

        #incorporate layouts
        Mlayout = QVBoxLayout()
        Mlayout.addWidget(TabWidget)
        Mlayout.addLayout(buttonLayout)
        
        self.setLayout(Mlayout)

    def createDeviceTable(self):
        try:

            self.devicetable.clear()        
            ndevices = len(aw.qmc.extradevices)
            if ndevices:    
                self.devicetable.setRowCount(ndevices)
                self.devicetable.setColumnCount(7)
                self.devicetable.setHorizontalHeaderLabels([QApplication.translate("Table", "Device",None, QApplication.UnicodeUTF8),
                                                            QApplication.translate("Table", "Color 1",None, QApplication.UnicodeUTF8),
                                                            QApplication.translate("Table", "Color 2",None, QApplication.UnicodeUTF8),
                                                            QApplication.translate("Table", "Label 1",None, QApplication.UnicodeUTF8),
                                                            QApplication.translate("Table", "Label 2",None, QApplication.UnicodeUTF8),
                                                            QApplication.translate("Table", "y1(x)",None, QApplication.UnicodeUTF8),
                                                            QApplication.translate("Table", "y2(x)",None, QApplication.UnicodeUTF8)])
                
                self.devicetable.setAlternatingRowColors(True)
                self.devicetable.setEditTriggers(QTableWidget.NoEditTriggers)
                self.devicetable.setSelectionBehavior(QTableWidget.SelectRows)
                self.devicetable.setSelectionMode(QTableWidget.SingleSelection)
                self.devicetable.setShowGrid(True)

                #populate table
                devices = aw.qmc.devices[:]  
                devices = sorted(devices)
                #devices.insert(0,"")         #add empty space for PID
                for i in range(ndevices):
                    typeComboBox =  QComboBox()
                    typeComboBox.addItems(sorted(devices))
                    typeComboBox.setCurrentIndex(devices.index(aw.qmc.devices[aw.qmc.extradevices[i]-1]))

                    color1Button = QPushButton(QApplication.translate("Button","Set",None, QApplication.UnicodeUTF8))
                    color1Button.setFocusPolicy(Qt.NoFocus)
                    self.connect(color1Button, SIGNAL("clicked()"),lambda l = 1, c = i: self.setextracolor(l,c))

                    color2Button = QPushButton(QApplication.translate("Button","Set",None, QApplication.UnicodeUTF8))
                    color2Button.setFocusPolicy(Qt.NoFocus)
                    self.connect(color2Button, SIGNAL("clicked()"),lambda l = 2, c = i: self.setextracolor(l,c))

                    name1edit = QLineEdit(unicode(aw.qmc.extraname1[i]))            
                    name2edit = QLineEdit(unicode(aw.qmc.extraname2[i]))

                    mexpr1edit = QLineEdit(unicode(aw.qmc.extramathexpression1[i]))
                    mexpr2edit = QLineEdit(unicode(aw.qmc.extramathexpression2[i]))
                    mexpr1edit.setToolTip(QApplication.translate("Tooltip","Example: 100 + 2*x",None, QApplication.UnicodeUTF8))
                    mexpr2edit.setToolTip(QApplication.translate("Tooltip","Example: 100 + x",None, QApplication.UnicodeUTF8))
                    
                    #add widgets to the table
                    self.devicetable.setCellWidget(i,0,typeComboBox)
                    self.devicetable.setCellWidget(i,1,color1Button)
                    self.devicetable.setCellWidget(i,2,color2Button)              
                    self.devicetable.setCellWidget(i,3,name1edit)              
                    self.devicetable.setCellWidget(i,4,name2edit)              
                    self.devicetable.setCellWidget(i,5,mexpr1edit)              
                    self.devicetable.setCellWidget(i,6,mexpr2edit)              

        except Exception,e:
             aw.qmc.adderror(QApplication.translate("Error Message", "createDeviceTable(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))


    #adds extra device
    def adddevice(self):
        try:
            self.savedevicetable()
            #addDevice() is located in aw so that the same function can be used in init after dynamically loading settings
            aw.addDevice()
            self.createDeviceTable()
            aw.qmc.redraw()
        except Exception,e:
             aw.qmc.adderror(QApplication.translate("Error Message", "adddevice(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
        
    def deldevice(self):
        try:
            bindex = len(aw.qmc.extradevices)-1
            selected = self.devicetable.selectedRanges()
            if len(selected) > 0:
                bindex = selected[0].topRow()
            if bindex >= 0:
                self.delextradevice(bindex)
        except Exception,e:
             aw.qmc.adderror(QApplication.translate("Error Message", "deldevice(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
             

    def resetextradevices(self):
        try:
            aw.qmc.extradevices = []                                      
            aw.qmc.extratimex = []                                        
            aw.qmc.extradevicecolor1 = []                                  
            aw.qmc.extradevicecolor2 = []                                
            aw.qmc.extratemp1,aw.qmc.extratemp2 = [],[]                     
            aw.qmc.extratemp1lines,aw.qmc.extratemp2lines = [],[]           
            aw.qmc.extraname1,aw.qmc.extraname2 = [],[]                     
            aw.qmc.extramathexpression1,aw.qmc.extramathexpression2 = [],[]           
            aw.ser.extraSP = []
            #EXTRA COMM PORTS VARIABLES
            aw.ser.extracomport,aw.ser.extrabaudrate,aw.ser.extrabytesize,aw.ser.extraparity,aw.ser.extrastopbits,aw.ser.extratimeout = [],[],[],[],[],[]
            self.createDeviceTable()
            aw.qmc.redraw()
            
        except Exception,e:
             aw.qmc.adderror(QApplication.translate("Error Message", "resetextradevices(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
        
    def delextradevice(self,x):
        try:           
            aw.qmc.extradevices.pop(x)
            aw.qmc.extradevicecolor1.pop(x)
            aw.qmc.extradevicecolor2.pop(x)
            aw.qmc.extratimex.pop(x)
            aw.qmc.extratemp1.pop(x)
            aw.qmc.extratemp2.pop(x)
            aw.qmc.extratemp1lines.pop(x)
            aw.qmc.extratemp2lines.pop(x)
            aw.qmc.extraname1.pop(x)
            aw.qmc.extraname2.pop(x)
            aw.qmc.extramathexpression1.pop(x)
            aw.qmc.extramathexpression2.pop(x)
            
            #pop serial port settings
            aw.extracomport.pop(x)
            aw.extrabaudrate.pop(x)
            aw.extrabytesize.pop(x)
            aw.extraparity.pop(x)
            aw.extrastopbits.pop(x)
            aw.extratimeout.pop(x)
            if aw.extraser[x].SP.isOpen():
                aw.extraser[x].SP.close()
            aw.extraser.pop(x)
            self.createDeviceTable()
            aw.qmc.redraw()
        except Exception,e:
             aw.qmc.adderror(QApplication.translate("Error Message", "delextradevice(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
        
    def savedevicetable(self):
        try:
            for i in range(len(aw.qmc.extradevices)):
                typecombobox = self.devicetable.cellWidget(i,0)
                name1edit = self.devicetable.cellWidget(i,3)
                name2edit = self.devicetable.cellWidget(i,4)
                mexpr1edit = self.devicetable.cellWidget(i,5)
                mexpr2edit = self.devicetable.cellWidget(i,6)
                
                aw.qmc.extradevices[i] = aw.qmc.devices.index(unicode(typecombobox.currentText())) + 1
                aw.qmc.extraname1[i] = unicode(name1edit.text())
                aw.qmc.extraname2[i] = unicode(name2edit.text())
                aw.qmc.extramathexpression1[i] = unicode(mexpr1edit.text())
                aw.qmc.extramathexpression2[i] = unicode(mexpr2edit.text())       
            
            #update legend
            aw.qmc.redraw()

        except Exception,e:
             aw.qmc.adderror(QApplication.translate("Error Message", "savedevicetable(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
        
    def setextracolor(self,l,i):
        try:
            #line 1
            if l == 1:
                colorf = QColorDialog.getColor(QColor(aw.qmc.extradevicecolor1[i]),self)
                if colorf.isValid():
                    colorname = unicode(colorf.name())
                    aw.qmc.extradevicecolor1[i] = colorname
            #line 2
            elif l == 2:
                colorf = QColorDialog.getColor(QColor(aw.qmc.extradevicecolor2[i]),self)
                if colorf.isValid():
                    colorname = unicode(colorf.name())
                    aw.qmc.extradevicecolor2[i] = colorname            
        except Exception,e:
             aw.qmc.adderror(QApplication.translate("Error Message", "setextracolor(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))

    def accept(self):
        try:    
            message = "Device left empty"
            
            # by default switch PID buttons/LCDs off
            aw.button_10.setVisible(False)
            aw.label6.setVisible(False)
            aw.lcd6.setVisible(False)
            aw.label7.setVisible(False)
            aw.lcd7.setVisible(False)
                
            if self.pidButton.isChecked():
                # 0 = PXG, 1 = PXR - Not translated
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
                elif str(self.btpidtypeComboBox.currentText()) == "None":
                    aw.ser.readBTpid[0] = 2
                    str2 = "None"            
                aw.ser.readBTpid[1] =  int(str(self.btpidunitidComboBox.currentText()))

                aw.qmc.device = 0
                self.comport = "COM4"
                self.baudrate = 9600
                self.bytesize = 8
                self.parity= 'O'
                self.stopbits = 1
                self.timeout=1

                message = QApplication.translate("Message Area","PID to control ET set to %1 %2" + \
                                                 " ; PID to read BT set to %3 %4", None, QApplication.UnicodeUTF8).arg(str1).arg(str(aw.ser.controlETpid[1])).arg(str2).arg(str(aw.ser.readBTpid[1]))
                
                aw.button_10.setVisible(True)
                aw.label6.setVisible(True)
                aw.lcd6.setVisible(True)
                aw.label7.setVisible(True)
                aw.lcd7.setVisible(True)

            if self.arduinoButton.isChecked():
                aw.ser.arduinoETChannel = str(self.arduinoETComboBox.currentText())
                aw.ser.arduinoBTChannel = str(self.arduinoBTComboBox.currentText())
                
                meter = "Arduino (TC4)"
                aw.qmc.device = 19
                #aw.ser.comport = "/dev/ttyACM0"
                aw.ser.baudrate = 19200
                aw.ser.bytesize = 8
                aw.ser.parity= 'N'
                aw.ser.stopbits = 1
                aw.ser.timeout=1
                message = QApplication.translate("Message Area","Device set to %1. Now, check Serial Port settings", None, QApplication.UnicodeUTF8).arg(meter)
                
            if self.nonpidButton.isChecked():
                meter = str(self.devicetypeComboBox.currentText())
                message = QApplication.translate("Error Message","device err",None,QApplication.UnicodeUTF8)

                if meter == "Omega HH806AU":
                    aw.qmc.device = 1
                    #aw.ser.comport = "COM11"
                    aw.ser.baudrate = 19200
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'E'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)

                elif meter == "Omega HH506RA":
                    aw.qmc.device = 2
                    #aw.ser.comport = "/dev/tty.usbserial-A2001Epn"
                    aw.ser.baudrate = 2400
                    aw.ser.bytesize = 7
                    aw.ser.parity= 'E'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)
                    
                elif meter == "CENTER 309":
                    aw.qmc.device = 3
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)

                elif meter == "CENTER 306":
                    aw.qmc.device = 4
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1                
                    message = QApplication.translate("Message Area","Device set to %1. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)

                elif meter == "CENTER 305":
                    aw.qmc.device = 5
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to CENTER 305, which is equivalent to CENTER 306. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)
                    
                elif meter == "CENTER 304":
                    aw.qmc.device = 6
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1, which is equivalent to CENTER 309. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)

                elif meter == "CENTER 303":
                    aw.qmc.device = 7
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)

                elif meter == "CENTER 302":
                    aw.qmc.device = 8
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1, which is equivalent to CENTER 303. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)
                    
                elif meter == "CENTER 301":
                    aw.qmc.device = 9
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1, which is equivalent to CENTER 303. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)

                elif meter == "CENTER 300":
                    aw.qmc.device = 10
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1, which is equivalent to CENTER 303. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)
                    
                elif meter == "VOLTCRAFT K204":
                    aw.qmc.device = 11
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1, which is equivalent to CENTER 309. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)

                elif meter == "VOLTCRAFT K202":
                    aw.qmc.device = 12
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1, which is equivalent to CENTER 306. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)

                elif meter == "VOLTCRAFT 300K":
                    aw.qmc.device = 13
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1, which is equivalent to CENTER 303. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)

                elif meter == "VOLTCRAFT 302KJ":
                    aw.qmc.device = 14
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1, which is equivalent to CENTER 303. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)

                elif meter == "EXTECH 421509":
                    aw.qmc.device = 15
                    #aw.ser.comport = "/dev/tty.usbserial-A2001Epn"
                    aw.ser.baudrate = 2400
                    aw.ser.bytesize = 7
                    aw.ser.parity= 'E'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1, which is equivalent to Omega HH506RA. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)
                                    
                elif meter == "Omega HH802U":
                    aw.qmc.device = 16
                    #aw.ser.comport = "COM11"
                    aw.ser.baudrate = 19200
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'E'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1, which is equivalent to Omega HH806AU. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)

                elif meter == "Omega HH309":
                    aw.qmc.device = 17
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1. Now, chose serial port", None, QApplication.UnicodeUTF8).arg(meter)

                #special device manual mode. No serial settings.    
                elif meter == "NONE":
                    aw.qmc.device = 18
                    message = QApplication.translate("Message Area","Device set to %1", None, QApplication.UnicodeUTF8).arg(meter)
                    st = ""
                    if aw.qmc.delay != 1000:
                        aw.qmc.delay = 1000
                        st += ". Sampling rate changed to 1 second"
                    message = QApplication.translate("Message Area","Device set to %1%2", None, QApplication.UnicodeUTF8).arg(meter).arg(st)

                elif meter == "TE VA18B":
                    aw.qmc.device = 20
                    #aw.ser.comport = "COM7"
                    aw.ser.baudrate = 2400
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=2
                    message = QApplication.translate("Message Area","Device set to %1. Now, check Serial Port settings", None, QApplication.UnicodeUTF8).arg(meter)

                elif meter == "+309_34":
                    aw.qmc.device = 21
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = ""  #empty message especial device

                elif meter == "+FUJI DUTY%":
                    aw.qmc.device = 22
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'E'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = ""   #empty message especial device
                    
                elif meter == "Omega HHM28[6]":
                    aw.qmc.device = 23
                    #aw.ser.comport = "COM1"
                    aw.ser.baudrate = 2400
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = QApplication.translate("Message Area","Device set to %1. Now, check Serial Port settings", None, QApplication.UnicodeUTF8).arg(meter)

                elif meter == "+204_34":
                    aw.qmc.device = 24
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = ""  #empty message especial device

                elif meter == "+Virtual":
                    aw.qmc.device = 25
                    #aw.ser.comport = "COM4"
                    aw.ser.baudrate = 9600
                    aw.ser.bytesize = 8
                    aw.ser.parity= 'N'
                    aw.ser.stopbits = 1
                    aw.ser.timeout=1
                    message = ""  #empty message especial device

                #set of different serial settings modes options
                ssettings = [[9600,8,'O',1,1],[19200,8,'E',1,1],[2400,7,'E',1,1],[9600,8,'N',1,1],[19200,8,'N',1,1,],[2400,8,'N',1,1],[9600,8,'E',1,1]]
                #map device index to a setting mode
                devssettings = [0,1,2,3,3,3,3,3,3,3,3,3,3,3,3,2,1,3,0,4,5,3,6,5,3,3]  #0-25
                    
                self.savedevicetable()
                #init serial settings of extra devices
                for i in range(len(aw.qmc.extradevices)):
                    dsettings = ssettings[devssettings[aw.qmc.extradevices[i]]]
                    aw.extrabaudrate[i] = dsettings[0]
                    aw.extrabytesize[i] = dsettings[1]
                    aw.extraparity[i] = dsettings[2]
                    aw.extrastopbits[i] = dsettings[3]
                    aw.extratimeout[i] = dsettings[4]  
                    
                aw.button_10.setVisible(False)
                aw.button_12.setVisible(False)
                aw.button_13.setVisible(False)
                aw.button_14.setVisible(False)
                aw.button_15.setVisible(False)
                aw.button_16.setVisible(False)
                aw.button_17.setVisible(False)
                aw.label6.setVisible(False)
                aw.lcd6.setVisible(False)
                aw.label7.setVisible(False)
                aw.lcd7.setVisible(False)
           
            aw.qmc.ETfunction = unicode(self.ETfunctionedit.text())
            aw.qmc.BTfunction = unicode(self.BTfunctionedit.text())

            #save any extra devices here
            self.savedevicetable()
            
            aw.sendmessage(message)

            #open serial conf Dialog        
            if (self.nonpidButton.isChecked() or self.arduinoButton.isChecked()):
                if meter != "NONE":
                    aw.setcommport()
            else:
                aw.setcommport()

            self.close()

        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "device accept((): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))

############################################################
#######################  CUSTOM COLOR DIALOG  ##############
############################################################

class graphColorDlg(QDialog):
    def __init__(self, parent = None):
        super(graphColorDlg,self).__init__(parent)
        self.setWindowTitle(QApplication.translate("Form Caption","Colors", None, QApplication.UnicodeUTF8))
        frameStyle = QFrame.Sunken | QFrame.Panel


        ## Translation: Right now the default palette colors are not translated (as they are used as-is)
        ##              We will add a translation list.
        
        #TAB1
        self.backgroundLabel = QLabel(aw.qmc.palette["background"])
        self.backgroundLabel.setPalette(QPalette(QColor(aw.qmc.palette["background"])))
        self.backgroundLabel.setAutoFillBackground(True)
        self.backgroundButton = QPushButton(QApplication.translate("Button","Background", None, QApplication.UnicodeUTF8))
        self.backgroundButton.setFocusPolicy(Qt.NoFocus)
        self.backgroundLabel.setFrameStyle(frameStyle)
        self.connect(self.backgroundButton, SIGNAL("clicked()"), lambda var=self.backgroundLabel,color="background": self.setColor("Background",var,color))

        
        self.gridLabel =QLabel(aw.qmc.palette["grid"])
        self.gridLabel.setPalette(QPalette(QColor(aw.qmc.palette["grid"])))
        self.gridLabel.setAutoFillBackground(True)
        self.gridButton = QPushButton(QApplication.translate("Button","Grid", None, QApplication.UnicodeUTF8))
        self.gridButton.setFocusPolicy(Qt.NoFocus)
        self.gridLabel.setFrameStyle(frameStyle)
        self.connect(self.gridButton, SIGNAL("clicked()"), lambda var=self.gridLabel, color= "grid": self.setColor("Grid",var,color))


        self.titleLabel =QLabel(aw.qmc.palette["title"])
        self.titleLabel.setPalette(QPalette(QColor(aw.qmc.palette["title"])))
        self.titleLabel.setAutoFillBackground(True)
        self.titleButton = QPushButton(QApplication.translate("Button","Title", None, QApplication.UnicodeUTF8))
        self.titleButton.setFocusPolicy(Qt.NoFocus)
        self.titleLabel.setFrameStyle(frameStyle)
        self.connect(self.titleButton, SIGNAL("clicked()"), lambda var=self.titleLabel,color="title": self.setColor("Title",var,color))
        
        
        self.yLabel =QLabel(aw.qmc.palette["ylabel"])
        self.yLabel.setPalette(QPalette(QColor(aw.qmc.palette["ylabel"])))
        self.yLabel.setAutoFillBackground(True)
        self.yButton = QPushButton(QApplication.translate("Button","Y Label", None, QApplication.UnicodeUTF8))
        self.yButton.setFocusPolicy(Qt.NoFocus)
        self.yLabel.setFrameStyle(frameStyle)
        self.connect(self.yButton, SIGNAL("clicked()"), lambda var=self.yLabel,color="ylabel": self.setColor("Y Label",var,color))

        
        self.xLabel =QLabel(aw.qmc.palette["xlabel"])
        self.xLabel.setPalette(QPalette(QColor(aw.qmc.palette["xlabel"])))
        self.xLabel.setAutoFillBackground(True)
        self.xButton = QPushButton(QApplication.translate("Button","X Label", None, QApplication.UnicodeUTF8))
        self.xButton.setFocusPolicy(Qt.NoFocus)
        self.xLabel.setFrameStyle(frameStyle)
        self.connect(self.xButton, SIGNAL("clicked()"), lambda var=self.xLabel,color="xlabel": self.setColor("X Label",var,color))

        
        self.rect1Label =QLabel(aw.qmc.palette["rect1"])
        self.rect1Label.setPalette(QPalette(QColor(aw.qmc.palette["rect1"])))
        self.rect1Label.setAutoFillBackground(True)
        self.rect1Button = QPushButton(QApplication.translate("Button","Dry Phase", None, QApplication.UnicodeUTF8))
        self.rect1Button.setFocusPolicy(Qt.NoFocus)
        self.rect1Label.setFrameStyle(frameStyle)
        self.connect(self.rect1Button, SIGNAL("clicked()"), lambda var=self.rect1Label,color="rect1": self.setColor("Dry Phase",var,color))

        
        self.rect2Label =QLabel(aw.qmc.palette["rect2"])
        self.rect2Label.setPalette(QPalette(QColor(aw.qmc.palette["rect2"])))
        self.rect2Label.setAutoFillBackground(True)
        self.rect2Button = QPushButton(QApplication.translate("Button","Mid FC Phase", None, QApplication.UnicodeUTF8))
        self.rect2Button.setFocusPolicy(Qt.NoFocus)
        self.rect2Label.setFrameStyle(frameStyle)
        self.connect(self.rect2Button, SIGNAL("clicked()"), lambda var=self.rect2Label,color="rect2": self.setColor("Mid FC Phase",var,color))

        
        self.rect3Label =QLabel(aw.qmc.palette["rect3"])
        self.rect3Label.setPalette(QPalette(QColor(aw.qmc.palette["rect3"])))
        self.rect3Label.setAutoFillBackground(True)
        self.rect3Button = QPushButton(QApplication.translate("Button","Finish Phase", None, QApplication.UnicodeUTF8))
        self.rect3Button.setFocusPolicy(Qt.NoFocus)
        self.rect3Label.setFrameStyle(frameStyle)
        self.connect(self.rect3Button, SIGNAL("clicked()"), lambda var=self.rect3Label,color="rect3": self.setColor("Finish Phase",var,color))

        
        self.metLabel =QLabel(aw.qmc.palette["et"])
        self.metLabel.setPalette(QPalette(QColor(aw.qmc.palette["et"])))
        self.metLabel.setAutoFillBackground(True)
        self.metButton = QPushButton(QApplication.translate("Button","ET", None, QApplication.UnicodeUTF8))
        self.metButton.setFocusPolicy(Qt.NoFocus)
        self.metLabel.setFrameStyle(frameStyle)
        self.connect(self.metButton, SIGNAL("clicked()"), lambda var=self.metLabel,color="et": self.setColor("ET",var,color))

        
        self.btLabel =QLabel(aw.qmc.palette["bt"])
        self.btLabel.setPalette(QPalette(QColor(aw.qmc.palette["bt"])))
        self.btLabel.setAutoFillBackground(True)
        self.btButton = QPushButton(QApplication.translate("Button","BT", None, QApplication.UnicodeUTF8))
        self.btButton.setFocusPolicy(Qt.NoFocus)
        self.btLabel.setFrameStyle(frameStyle)
        self.connect(self.btButton, SIGNAL("clicked()"), lambda var=self.btLabel,color="bt": self.setColor("BT",var,color))

        
        self.deltametLabel =QLabel(aw.qmc.palette["deltaet"])
        self.deltametLabel.setPalette(QPalette(QColor(aw.qmc.palette["deltaet"])))
        self.deltametLabel.setAutoFillBackground(True)
        self.deltametButton = QPushButton(QApplication.translate("Button","DeltaET", None, QApplication.UnicodeUTF8))
        self.deltametButton.setFocusPolicy(Qt.NoFocus)
        self.deltametLabel.setFrameStyle(frameStyle)
        self.connect(self.deltametButton, SIGNAL("clicked()"), lambda var=self.deltametLabel,color="deltaet": self.setColor("DeltaET",var,color))

        
        self.deltabtLabel =QLabel(aw.qmc.palette["deltabt"])
        self.deltabtLabel.setPalette(QPalette(QColor(aw.qmc.palette["deltabt"])))
        self.deltabtLabel.setAutoFillBackground(True)
        self.deltabtButton = QPushButton(QApplication.translate("Button","DeltaBT", None, QApplication.UnicodeUTF8))
        self.deltabtButton.setFocusPolicy(Qt.NoFocus)
        self.deltabtLabel.setFrameStyle(frameStyle)
        self.connect(self.deltabtButton, SIGNAL("clicked()"), lambda var=self.deltabtLabel,color="deltabt": self.setColor("DeltaBT",var,color))

        
        self.markersLabel =QLabel(aw.qmc.palette["markers"])
        self.markersLabel.setPalette(QPalette(QColor(aw.qmc.palette["markers"])))
        self.markersLabel.setAutoFillBackground(True)
        self.markersButton = QPushButton(QApplication.translate("Button","Markers", None, QApplication.UnicodeUTF8))
        self.markersButton.setFocusPolicy(Qt.NoFocus)
        self.markersLabel.setFrameStyle(frameStyle)
        self.connect(self.markersButton, SIGNAL("clicked()"), lambda var=self.markersLabel,color="markers": self.setColor("Markers",var,color))

        
        self.textLabel =QLabel(aw.qmc.palette["text"])
        self.textLabel.setPalette(QPalette(QColor(aw.qmc.palette["text"])))
        self.textLabel.setAutoFillBackground(True)
        self.textButton = QPushButton(QApplication.translate("Button","Text", None, QApplication.UnicodeUTF8))
        self.textButton.setFocusPolicy(Qt.NoFocus)
        self.textLabel.setFrameStyle(frameStyle)
        self.connect(self.textButton, SIGNAL("clicked()"), lambda var=self.textLabel,color="text": self.setColor("Text",var,color))

        self.watermarksLabel =QLabel(aw.qmc.palette["watermarks"])
        self.watermarksLabel.setPalette(QPalette(QColor(aw.qmc.palette["watermarks"])))
        self.watermarksLabel.setAutoFillBackground(True)
        self.watermarksButton = QPushButton(QApplication.translate("Button","Watermarks", None, QApplication.UnicodeUTF8))
        self.watermarksButton.setFocusPolicy(Qt.NoFocus)
        self.watermarksLabel.setFrameStyle(frameStyle)
        self.connect(self.watermarksButton, SIGNAL("clicked()"), lambda var=self.watermarksLabel,color="watermarks": self.setColor("Watermarks",var,color))
        
        self.ClineLabel =QLabel(aw.qmc.palette["Cline"])
        self.ClineLabel.setPalette(QPalette(QColor(aw.qmc.palette["Cline"])))
        self.ClineLabel.setAutoFillBackground(True)
        self.ClineButton = QPushButton(QApplication.translate("Button","C Lines", None, QApplication.UnicodeUTF8))
        self.ClineButton.setFocusPolicy(Qt.NoFocus)
        self.ClineLabel.setFrameStyle(frameStyle)
        self.connect(self.ClineButton, SIGNAL("clicked()"), lambda var=self.ClineLabel,color="Cline": self.setColor("C Lines",var,color))

        okButton = QPushButton(QApplication.translate("Button","OK", None, QApplication.UnicodeUTF8))
        self.connect(okButton, SIGNAL("clicked()"),self, SLOT("accept()"))   

        defaultsButton = QPushButton(QApplication.translate("Button","Defaults", None, QApplication.UnicodeUTF8))
        defaultsButton.setFocusPolicy(Qt.NoFocus)
        self.connect(defaultsButton, SIGNAL("clicked()"),lambda x=1:self.recolor(x))   
        
        greyButton = QPushButton(QApplication.translate("Button","Grey", None, QApplication.UnicodeUTF8))
        greyButton.setFocusPolicy(Qt.NoFocus)
        self.connect(greyButton, SIGNAL("clicked()"),lambda x=2:self.recolor(x))             

        #TAB 2
        lcd1label = QLabel(QApplication.translate("Label", "Timer",None, QApplication.UnicodeUTF8))
        lcd2label = QLabel(QApplication.translate("Label", "ET",None, QApplication.UnicodeUTF8))
        lcd3label = QLabel(QApplication.translate("Label", "BT",None, QApplication.UnicodeUTF8))
        lcd4label = QLabel(QApplication.translate("Label", "Delta ET",None, QApplication.UnicodeUTF8))
        lcd5label = QLabel(QApplication.translate("Label", "Delta BT",None, QApplication.UnicodeUTF8))
        lcd6label = QLabel(QApplication.translate("Label", "SV",None, QApplication.UnicodeUTF8))

        #use indexes to translate
        self.lcdcolors = ["","grey","darkGrey","slateGrey","lightGray","black","white","transparent"]     #this one is not to be translated as arguments need to be in English
        lcdcolorstranslate = [u"",
                              QApplication.translate("ComboBox","grey",None, QApplication.UnicodeUTF8),
                              QApplication.translate("ComboBox","Dark Grey",None, QApplication.UnicodeUTF8),
                              QApplication.translate("ComboBox","Slate Grey",None, QApplication.UnicodeUTF8),
                              QApplication.translate("ComboBox","Light Gray",None, QApplication.UnicodeUTF8),
                              QApplication.translate("ComboBox","Black",None, QApplication.UnicodeUTF8),
                              QApplication.translate("ComboBox","White",None, QApplication.UnicodeUTF8),
                              QApplication.translate("ComboBox","Transparent",None, QApplication.UnicodeUTF8)]  # translated
        
        self.lcd1colorComboBox =  QComboBox()
        self.lcd1colorComboBox.addItems(lcdcolorstranslate)
        self.connect(self.lcd1colorComboBox, SIGNAL("currentIndexChanged(QString)"),lambda text = self.lcd1colorComboBox.currentText(),flag = 2,x=1:self.paintlcds(text,flag,x))

        self.lcd2colorComboBox =  QComboBox()
        self.lcd2colorComboBox.addItems(lcdcolorstranslate)
        self.connect(self.lcd2colorComboBox, SIGNAL("currentIndexChanged(QString)"),lambda text = self.lcd2colorComboBox.currentText(),flag = 2,x=2:self.paintlcds(text,flag,x))
    
        self.lcd3colorComboBox =  QComboBox()
        self.lcd3colorComboBox.addItems(lcdcolorstranslate)
        self.connect(self.lcd3colorComboBox, SIGNAL("currentIndexChanged(QString)"),lambda text = self.lcd3colorComboBox.currentText(),flag = 2,x=3:self.paintlcds(text,flag,x))
    
        self.lcd4colorComboBox =  QComboBox()
        self.lcd4colorComboBox.addItems(lcdcolorstranslate)
        self.connect(self.lcd4colorComboBox, SIGNAL("currentIndexChanged(QString)"),lambda text = self.lcd4colorComboBox.currentText(),flag = 2,x=4:self.paintlcds(text,flag,x))
    
        self.lcd5colorComboBox =  QComboBox()
        self.lcd5colorComboBox.addItems(lcdcolorstranslate)
        self.connect(self.lcd5colorComboBox, SIGNAL("currentIndexChanged(QString)"),lambda text = self.lcd5colorComboBox.currentText(),flag = 2,x=5:self.paintlcds(text,flag,x))
    
        self.lcd6colorComboBox =  QComboBox()
        self.lcd6colorComboBox.addItems(lcdcolorstranslate)
        self.connect(self.lcd6colorComboBox, SIGNAL("currentIndexChanged(QString)"),lambda text = self.lcd6colorComboBox.currentText(),flag = 2,x=6:self.paintlcds(text,flag,x))

        lcd1backButton = QPushButton(QApplication.translate("Button","Background",None, QApplication.UnicodeUTF8))
        self.connect(lcd1backButton, SIGNAL("clicked()"),lambda text =0,flag=0,x=1:self.paintlcds(text,flag,x))
        lcd2backButton = QPushButton("Background")
        self.connect(lcd2backButton, SIGNAL("clicked()"),lambda text =0,flag=0,x=2:self.paintlcds(text,flag,x))   
        lcd3backButton = QPushButton("Background")
        self.connect(lcd3backButton, SIGNAL("clicked()"),lambda text =0,flag=0,x=3:self.paintlcds(text,flag,x))   
        lcd4backButton = QPushButton("Background")
        self.connect(lcd4backButton, SIGNAL("clicked()"),lambda text =0,flag=0,x=4:self.paintlcds(text,flag,x))   
        lcd5backButton = QPushButton("Background")
        self.connect(lcd5backButton, SIGNAL("clicked()"),lambda text =0,flag=0,x=5:self.paintlcds(text,flag,x))   
        lcd6backButton = QPushButton("Background")
        self.connect(lcd6backButton, SIGNAL("clicked()"),lambda text =0,flag=0,x=6:self.paintlcds(text,flag,x))   

        lcd1LEDButton = QPushButton(QApplication.translate("Button","LED",None, QApplication.UnicodeUTF8))
        self.connect(lcd1LEDButton, SIGNAL("clicked()"),lambda text =0,flag=1,x=1:self.paintlcds(text,flag,x))
        lcd2LEDButton = QPushButton("LED")
        self.connect(lcd2LEDButton, SIGNAL("clicked()"),lambda text =0,flag=1,x=2:self.paintlcds(text,flag,x))   
        lcd3LEDButton = QPushButton("LED")
        self.connect(lcd3LEDButton, SIGNAL("clicked()"),lambda text =0,flag=1,x=3:self.paintlcds(text,flag,x))   
        lcd4LEDButton = QPushButton("LED")
        self.connect(lcd4LEDButton, SIGNAL("clicked()"),lambda text =0,flag=1,x=4:self.paintlcds(text,flag,x))   
        lcd5LEDButton = QPushButton("LED")
        self.connect(lcd5LEDButton, SIGNAL("clicked()"),lambda text =0,flag=1,x=5:self.paintlcds(text,flag,x))   
        lcd6LEDButton = QPushButton("LED")
        self.connect(lcd6LEDButton, SIGNAL("clicked()"),lambda text =0,flag=1,x=6:self.paintlcds(text,flag,x))   

        self.lcd1spinbox = QSpinBox()
        self.lcd1spinbox.setSingleStep(10) 
        self.lcd1spinbox.setMaximum(359)
        self.lcd1spinbox.setWrapping(True)
        self.connect(self.lcd1spinbox, SIGNAL("valueChanged(int)"),lambda val=self.lcd1spinbox.value(),lcd=1:self.setLED(val,lcd))
        
        self.lcd2spinbox = QSpinBox()
        self.lcd2spinbox.setSingleStep(10)
        self.lcd2spinbox.setWrapping(True)
        self.lcd2spinbox.setMaximum(359)
        self.connect(self.lcd2spinbox, SIGNAL("valueChanged(int)"),lambda val=self.lcd2spinbox.value(),lcd=2:self.setLED(val,lcd))
        
        self.lcd3spinbox = QSpinBox()
        self.lcd3spinbox.setSingleStep(10)
        self.lcd3spinbox.setWrapping(True)
        self.lcd3spinbox.setMaximum(359)
        self.connect(self.lcd3spinbox, SIGNAL("valueChanged(int)"),lambda val=self.lcd3spinbox.value(),lcd=3:self.setLED(val,lcd))

        self.lcd4spinbox = QSpinBox()
        self.lcd4spinbox.setSingleStep(10)
        self.lcd4spinbox.setWrapping(True)
        self.lcd4spinbox.setMaximum(359)
        self.connect(self.lcd4spinbox, SIGNAL("valueChanged(int)"),lambda val=self.lcd4spinbox.value(),lcd=4:self.setLED(val,lcd))

        self.lcd5spinbox = QSpinBox()
        self.lcd5spinbox.setSingleStep(10)
        self.lcd1spinbox.setWrapping(True)
        self.lcd5spinbox.setMaximum(359)
        self.connect(self.lcd5spinbox, SIGNAL("valueChanged(int)"),lambda val=self.lcd5spinbox.value(),lcd=5:self.setLED(val,lcd))

        self.lcd6spinbox = QSpinBox()
        self.lcd6spinbox.setSingleStep(10)
        self.lcd1spinbox.setWrapping(True)
        self.lcd6spinbox.setMaximum(359)
        self.connect(self.lcd6spinbox, SIGNAL("valueChanged(int)"),lambda val=self.lcd6spinbox.value(),lcd=6:self.setLED(val,lcd))


        LCDdefaultButton = QPushButton(QApplication.translate("Button","B/W",None, QApplication.UnicodeUTF8))
        self.connect(LCDdefaultButton, SIGNAL("clicked()"),self.setLCDdefaults)
        
        #LAYOUTS
        #tab1 layout
        grid = QGridLayout()
        grid.setColumnStretch(1,10)
        grid.setColumnMinimumWidth(1,200)
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
                
        defaultsLayout = QHBoxLayout()
        defaultsLayout.addStretch()
        defaultsLayout.addWidget(greyButton)
        defaultsLayout.addWidget(defaultsButton)
        defaultsLayout.addWidget(okButton)
        
        grid.addLayout(defaultsLayout,16,1)

        graphLayout = QVBoxLayout()
        graphLayout.addLayout(grid)

        #tab 2
        lcdlayout = QVBoxLayout()
        
        lcd1layout = QHBoxLayout()
        lcd1layout.addWidget(lcd1backButton,0)
        lcd1layout.addWidget(self.lcd1colorComboBox,1)
        lcd1layout.addWidget(lcd1LEDButton,2)
        lcd1layout.addWidget(self.lcd1spinbox,3)
        
        lcd2layout = QHBoxLayout()        
        lcd2layout.addWidget(lcd2backButton,0)
        lcd2layout.addWidget(self.lcd2colorComboBox,1)
        lcd2layout.addWidget(lcd2LEDButton,2)
        lcd2layout.addWidget(self.lcd2spinbox,3)

        lcd3layout = QHBoxLayout()
        lcd3layout.addWidget(lcd3backButton,0)
        lcd3layout.addWidget(self.lcd3colorComboBox,1)
        lcd3layout.addWidget(lcd3LEDButton,2)
        lcd3layout.addWidget(self.lcd3spinbox,3)

        lcd4layout = QHBoxLayout()
        lcd4layout.addWidget(lcd4backButton,0)
        lcd4layout.addWidget(self.lcd4colorComboBox,1)
        lcd4layout.addWidget(lcd4LEDButton,2)
        lcd4layout.addWidget(self.lcd4spinbox,3)

        lcd5layout = QHBoxLayout()
        lcd5layout.addWidget(lcd5backButton,0)
        lcd5layout.addWidget(self.lcd5colorComboBox,1)
        lcd5layout.addWidget(lcd5LEDButton,2)
        lcd5layout.addWidget(self.lcd5spinbox,3)

        lcd6layout = QHBoxLayout()
        lcd6layout.addWidget(lcd6backButton,0)
        lcd6layout.addWidget(self.lcd6colorComboBox,1)
        lcd6layout.addWidget(lcd6LEDButton,2)
        lcd6layout.addWidget(self.lcd6spinbox,3)

        LCD1GroupLayout = QGroupBox(QApplication.translate("GroupBox","Timer LCD",None, QApplication.UnicodeUTF8))
        LCD1GroupLayout.setLayout(lcd1layout)
        
        LCD2GroupLayout = QGroupBox(QApplication.translate("GroupBox","ET LCD",None, QApplication.UnicodeUTF8))
        LCD2GroupLayout.setLayout(lcd2layout)
        
        LCD3GroupLayout = QGroupBox(QApplication.translate("GroupBox","BT LCD",None, QApplication.UnicodeUTF8))
        LCD3GroupLayout.setLayout(lcd3layout)
        
        LCD4GroupLayout = QGroupBox(QApplication.translate("GroupBox","Delta ET LCD",None, QApplication.UnicodeUTF8))
        LCD4GroupLayout.setLayout(lcd4layout)
        
        LCD5GroupLayout = QGroupBox(QApplication.translate("GroupBox","Delta BT LCD",None, QApplication.UnicodeUTF8))
        LCD5GroupLayout.setLayout(lcd5layout)
        
        LCD6GroupLayout = QGroupBox(QApplication.translate("GroupBox","PID SV & POWER % LCD",None, QApplication.UnicodeUTF8))
        LCD6GroupLayout.setLayout(lcd6layout)

        buttonlayout  = QHBoxLayout()
        buttonlayout.addStretch()
        buttonlayout.addWidget(LCDdefaultButton)

        lcdlayout.addWidget(LCD1GroupLayout)
        lcdlayout.addWidget(LCD2GroupLayout)
        lcdlayout.addWidget(LCD3GroupLayout)
        lcdlayout.addWidget(LCD4GroupLayout)
        lcdlayout.addWidget(LCD5GroupLayout)
        lcdlayout.addWidget(LCD6GroupLayout)
        lcdlayout.addLayout(buttonlayout)

        ###################################        

        TabWidget = QTabWidget()
        
        C1Widget = QWidget()
        C1Widget.setLayout(graphLayout)
        TabWidget.addTab(C1Widget,QApplication.translate("Tab","Graph",None, QApplication.UnicodeUTF8))
        
        C2Widget = QWidget()
        C2Widget.setLayout(lcdlayout)
        TabWidget.addTab(C2Widget,QApplication.translate("Tab","LCDs",None, QApplication.UnicodeUTF8))      
      
        okLayout = QHBoxLayout()
        okLayout.addStretch()
        okLayout.addWidget(okButton)
        okLayout.setMargin(0)
        okLayout.setContentsMargins(0, 0, 0, 0)
        TabWidget.setContentsMargins(0, 0, 0, 0)
        C1Widget.setContentsMargins(0, 0, 0, 0)
        C2Widget.setContentsMargins(0, 0, 0, 0)
        graphLayout.setMargin(0)
        
        #incorporate layouts
        Mlayout = QVBoxLayout()
        Mlayout.addWidget(TabWidget)
        Mlayout.addLayout(okLayout)
        Mlayout.setMargin(10)
        
        Mlayout.setSizeConstraint(QLayout.SetFixedSize)

        self.setLayout(Mlayout)

    def setLCDdefaults(self):
        aw.lcdpaletteB["timer"] = u"black"
        aw.lcdpaletteF["timer"] = u"white"
        aw.lcdpaletteB["et"] = u"black"
        aw.lcdpaletteF["et"] = u"white"
        aw.lcdpaletteB["bt"] = u"black"
        aw.lcdpaletteF["bt"] = u"white"
        aw.lcdpaletteB["deltaet"] = u"black"
        aw.lcdpaletteF["deltaet"] = u"white"
        aw.lcdpaletteB["deltabt"] = u"black"
        aw.lcdpaletteF["deltabt"] = u"white"
        aw.lcdpaletteB["sv"] = u"black"
        aw.lcdpaletteF["sv"] = u"white"
        aw.lcd1.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["timer"],aw.lcdpaletteB["timer"]))
        aw.lcd2.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["et"],aw.lcdpaletteB["et"]))
        aw.lcd3.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["bt"],aw.lcdpaletteB["bt"]))
        aw.lcd4.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["deltaet"],aw.lcdpaletteB["deltaet"]))
        aw.lcd5.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["deltabt"],aw.lcdpaletteB["deltabt"]))
        aw.lcd6.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["sv"],aw.lcdpaletteB["sv"]))
        aw.lcd7.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["sv"],aw.lcdpaletteB["sv"]))
        
    def setLED(self,hue,lcd):
        if lcd == 1:
            color = QColor(aw.lcdpaletteF["timer"])
            color.setHsv(hue,255,255,255)
            aw.lcdpaletteF["timer"] = unicode(color.name())
            aw.lcd1.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["timer"],aw.lcdpaletteB["timer"]))
        elif lcd == 2:
            color = QColor(aw.lcdpaletteF["et"])
            color.setHsv(hue,255,255,255)
            aw.lcdpaletteF["et"] = unicode(color.name())
            aw.lcd2.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["et"],aw.lcdpaletteB["et"]))
        elif lcd == 3:
            color = QColor(aw.lcdpaletteF["bt"])
            color.setHsv(hue,255,255,255)
            aw.lcdpaletteF["bt"] = unicode(color.name())
            aw.lcd3.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["bt"],aw.lcdpaletteB["bt"]))
        elif lcd == 4:
            color = QColor(aw.lcdpaletteF["deltaet"])
            color.setHsv(hue,255,255,255)
            aw.lcdpaletteF["deltaet"] = unicode(color.name())
            aw.lcd4.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["deltaet"],aw.lcdpaletteB["deltaet"]))
        elif lcd == 5:
            color = QColor(aw.lcdpaletteF["deltabt"])
            color.setHsv(hue,255,255,255)
            aw.lcdpaletteF["deltabt"] = unicode(color.name())
            aw.lcd5.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["deltabt"],aw.lcdpaletteB["deltabt"]))
        elif lcd == 6:
            color = QColor(aw.lcdpaletteF["sv"])
            color.setHsv(hue,255,255,255)
            aw.lcdpaletteF["sv"] = unicode(color.name())
            aw.lcd6.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["sv"],aw.lcdpaletteB["sv"]))
            aw.lcd7.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["sv"],aw.lcdpaletteB["sv"]))
            
            
    def paintlcds(self,text,flag,lcdnumber):
        if lcdnumber ==1:
            if flag == 0:
                aw.lcdpaletteB["timer"] = unicode((QColorDialog.getColor(QColor(aw.lcdpaletteB["timer"]),self)).name())
            elif flag == 1:
                aw.lcdpaletteF["timer"] = unicode((QColorDialog.getColor(QColor(aw.lcdpaletteF["timer"]),self)).name())
            elif flag == 2 and text:
                aw.lcdpaletteB["timer"] = self.lcdcolors[self.lcd1colorComboBox.currentIndex()]
            aw.lcd1.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["timer"],aw.lcdpaletteB["timer"]))
            
        if lcdnumber ==2:
            if flag == 0:
                aw.lcdpaletteB["et"] = unicode((QColorDialog.getColor(QColor(aw.lcdpaletteB["et"]),self)).name())
            elif flag == 1:
                aw.lcdpaletteF["et"] = unicode((QColorDialog.getColor(QColor(aw.lcdpaletteF["et"]),self)).name())
            elif flag == 2 and text:
                aw.lcdpaletteB["et"] = self.lcdcolors[self.lcd2colorComboBox.currentIndex()]
            aw.lcd2.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["et"],aw.lcdpaletteB["et"]))
            
        if lcdnumber ==3:
            if flag == 0:
                aw.lcdpaletteB["bt"] = unicode((QColorDialog.getColor(QColor(aw.lcdpaletteB["bt"]),self)).name())
            elif flag == 1:
                aw.lcdpaletteF["bt"] = unicode((QColorDialog.getColor(QColor(aw.lcdpaletteF["bt"]),self)).name())
            elif flag == 2 and text:
                aw.lcdpaletteB["bt"] = self.lcdcolors[self.lcd3colorComboBox.currentIndex()]
            aw.lcd3.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["bt"],aw.lcdpaletteB["bt"]))
            
        if lcdnumber ==4:
            if flag == 0:
                aw.lcdpaletteB["deltaet"] = unicode((QColorDialog.getColor(QColor(aw.lcdpaletteB["deltaet"]),self)).name())
            elif flag == 1:
                aw.lcdpaletteF["deltaet"] = unicode((QColorDialog.getColor(QColor(aw.lcdpaletteF["deltaet"]),self)).name())
            elif flag == 2 and text:
                aw.lcdpaletteB["deltaet"] = self.lcdcolors[self.lcd4colorComboBox.currentIndex()]
            aw.lcd4.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["deltaet"],aw.lcdpaletteB["deltaet"]))
        if lcdnumber ==5:
            if flag == 0:
                aw.lcdpaletteB["deltabt"] = unicode((QColorDialog.getColor(QColor(aw.lcdpaletteB["deltabt"]),self)).name())
            elif flag == 1:
                aw.lcdpaletteF["deltabt"] = unicode((QColorDialog.getColor(QColor(aw.lcdpaletteF["deltabt"]),self)).name())
            elif flag == 2 and text:
                aw.lcdpaletteB["deltabt"] = self.lcdcolors[self.lcd5colorComboBox.currentIndex()]
            aw.lcd5.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["deltabt"],aw.lcdpaletteB["deltabt"]))            
        if lcdnumber ==6:
            if flag == 0:
                aw.lcdpaletteB["sv"] = unicode((QColorDialog.getColor(QColor(aw.lcdpaletteB["sv"]),self)).name())
            elif flag == 1:
                aw.lcdpaletteF["sv"] = unicode((QColorDialog.getColor(QColor(aw.lcdpaletteF["sv"]),self)).name())
            elif flag == 2 and text:
                aw.lcdpaletteB["sv"] = self.lcdcolors[self.lcd6colorComboBox.currentIndex()]
            aw.lcd6.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["sv"],aw.lcdpaletteB["sv"]))            
            aw.lcd7.setStyleSheet("QLCDNumber { color: %s; background-color: %s;}"%(aw.lcdpaletteF["sv"],aw.lcdpaletteB["sv"]))            
            
        
    # adds a new event to the Dlg
    def recolor(self, x):
        aw.qmc.changeGColor(x)
        
        self.gridLabel.setText(aw.qmc.palette["grid"])
        self.gridLabel.setPalette(QPalette(QColor(aw.qmc.palette["grid"])))
        
        self.backgroundLabel.setText(aw.qmc.palette["background"])
        self.backgroundLabel.setPalette(QPalette(QColor(aw.qmc.palette["background"])))

        self.titleLabel.setText(aw.qmc.palette["title"])
        self.titleLabel.setPalette(QPalette(QColor(aw.qmc.palette["title"])))
        
        self.yLabel.setText(aw.qmc.palette["ylabel"])
        self.yLabel.setPalette(QPalette(QColor(aw.qmc.palette["ylabel"])))
        
        self.xLabel.setText(aw.qmc.palette["xlabel"])
        self.xLabel.setPalette(QPalette(QColor(aw.qmc.palette["xlabel"])))
        
        self.rect1Label.setText(aw.qmc.palette["rect1"])
        self.rect1Label.setPalette(QPalette(QColor(aw.qmc.palette["rect1"])))
        
        self.rect2Label.setText(aw.qmc.palette["rect2"])
        self.rect2Label.setPalette(QPalette(QColor(aw.qmc.palette["rect2"])))
        
        self.rect3Label.setText(aw.qmc.palette["rect3"])
        self.rect3Label.setPalette(QPalette(QColor(aw.qmc.palette["rect3"])))
        
        self.metLabel.setText(aw.qmc.palette["et"])
        self.metLabel.setPalette(QPalette(QColor(aw.qmc.palette["et"])))
        
        self.btLabel.setText(aw.qmc.palette["bt"])
        self.btLabel.setPalette(QPalette(QColor(aw.qmc.palette["bt"])))
        
        self.deltametLabel.setText(aw.qmc.palette["deltaet"])
        self.deltametLabel.setPalette(QPalette(QColor(aw.qmc.palette["deltaet"])))
        
        self.deltabtLabel.setText(aw.qmc.palette["deltabt"])
        self.deltabtLabel.setPalette(QPalette(QColor(aw.qmc.palette["deltabt"])))
        
        self.markersLabel.setText(aw.qmc.palette["markers"])
        self.markersLabel.setPalette(QPalette(QColor(aw.qmc.palette["markers"])))
        
        self.textLabel.setText(aw.qmc.palette["text"])
        self.textLabel.setPalette(QPalette(QColor(aw.qmc.palette["text"])))

        self.watermarksLabel.setText(aw.qmc.palette["watermarks"])
        self.watermarksLabel.setPalette(QPalette(QColor(aw.qmc.palette["watermarks"])))
        
        self.ClineLabel.setText(aw.qmc.palette["Cline"])
        self.ClineLabel.setPalette(QPalette(QColor(aw.qmc.palette["Cline"])))
                        
    def setColor(self,title,var,color):
        labelcolor = QColor(aw.qmc.palette[color])
        colorf = QColorDialog.getColor(labelcolor,self)
        if colorf.isValid(): 
            aw.qmc.palette[color] = unicode(colorf.name())
            var.setText(colorf.name())
            var.setPalette(QPalette(colorf))
            var.setAutoFillBackground(True)            
            aw.qmc.fig.canvas.redraw()
            aw.sendmessage(QApplication.translate("Message Area","Color of %1 set to %2", None, QApplication.UnicodeUTF8).arg(title).arg(str(aw.qmc.palette[color])))


############################################################
#######################  WHEEL GRAPH CONFIG DIALOG  ########
############################################################

class WheelDlg(QDialog):
    def __init__(self, parent = None):
        super(WheelDlg,self).__init__(parent)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate("Form Caption","Wheel Graph Editor",None, QApplication.UnicodeUTF8))

        aw.lowerbuttondialog.setVisible(False)
        aw.EventsGroupLayout.setVisible(False)
    	
        #table for alarms
        self.datatable = QTableWidget()
        self.createdatatable()

        #table for labels
        self.labeltable = QTableWidget()
        
        self.labelCloseButton = QPushButton(QApplication.translate("Button","Close Label properties",None, QApplication.UnicodeUTF8))
        #self.labelCloseButton.setMaximumWidth(160)
        self.connect(self.labelCloseButton, SIGNAL("clicked()"),self.closelabels)

        self.labelResetButton = QPushButton(QApplication.translate("Button","Reset Parents",None, QApplication.UnicodeUTF8))
        self.labelResetButton.setToolTip(QApplication.translate("Tooltip","Erases wheel parent hierarchy",None, QApplication.UnicodeUTF8))
        #self.labelResetButton.setMaximumWidth(160)
        self.connect(self.labelResetButton, SIGNAL("clicked()"),self.resetlabelparents)
        self.labelwheelx = 0   #index of wheel being edited on labeltable

        self.hierarchyButton = QPushButton(QApplication.translate("Button","Reverse Hierarchy",None, QApplication.UnicodeUTF8))
        self.hierarchyButton.setToolTip(QApplication.translate("Tooltip","Sets graph hierarchy child->parent instead of parent->child",None, QApplication.UnicodeUTF8))
        #self.hierarchyButton.setMaximumWidth(100)
        self.connect(self.hierarchyButton, SIGNAL("clicked()"),aw.qmc.setWheelHierarchy)

        self.labeltable.setVisible(False)        
        self.labelCloseButton.setVisible(False)
        self.labelResetButton.setVisible(False)
        
        txtlabel = QLabel(QApplication.translate("Label","Text",None, QApplication.UnicodeUTF8))
        txtButtonplus = QPushButton(QApplication.translate("Button","+",None, QApplication.UnicodeUTF8))
        txtButtonplus.setToolTip(QApplication.translate("Tooltip","Increase size of text in all the graph",None, QApplication.UnicodeUTF8))
        #txtButtonplus.setMaximumWidth(30)
        self.connect(txtButtonplus, SIGNAL("clicked()"),lambda x = 1: self.changetext(x))
        txtButtonminus = QPushButton(QApplication.translate("Button","-",None, QApplication.UnicodeUTF8))
        txtButtonminus.setToolTip(QApplication.translate("Tooltip","Decrease size of text in all the graph",None, QApplication.UnicodeUTF8))
        #txtButtonminus.setMaximumWidth(30)
        self.connect(txtButtonminus, SIGNAL("clicked()"),lambda x = 0: self.changetext(x))

        edgelabel = QLabel(QApplication.translate("Label","Edge",None, QApplication.UnicodeUTF8))
        self.edgeSpinBox = QSpinBox()
        self.edgeSpinBox.setToolTip(QApplication.translate("Tooltip","Decorative edge beween wheels",None, QApplication.UnicodeUTF8))
        #self.edgeSpinBox.setMaximumWidth(80)
        self.edgeSpinBox.setRange(0,5)
        self.edgeSpinBox.setValue(int(aw.qmc.wheeledge*100))
        self.connect(self.edgeSpinBox, SIGNAL("valueChanged(int)"),self.setedge)

        linewidthlabel = QLabel(QApplication.translate("Label","Line",None, QApplication.UnicodeUTF8))
        self.linewidthSpinBox = QSpinBox()
        self.linewidthSpinBox.setToolTip(QApplication.translate("Tooltip","Line thickness",None, QApplication.UnicodeUTF8))
        #self.linewidthSpinBox.setMaximumWidth(80)
        self.linewidthSpinBox.setRange(0,20)
        self.linewidthSpinBox.setValue(aw.qmc.wheellinewidth)
        self.connect(self.linewidthSpinBox, SIGNAL("valueChanged(int)"),self.setlinewidth)

        linecolor = QPushButton(QApplication.translate("Button","Line Color",None, QApplication.UnicodeUTF8))
        linecolor.setToolTip(QApplication.translate("Tooltip","Line color",None, QApplication.UnicodeUTF8))
        #linecolor.setMaximumWidth(100)
        self.connect(linecolor, SIGNAL("clicked()"),self.setlinecolor)
        
        colorlabel = QLabel(QApplication.translate("Label","Color pattern",None, QApplication.UnicodeUTF8))    	
        self.colorSpinBox = QSpinBox()
        self.colorSpinBox.setToolTip(QApplication.translate("Tooltip","Apply color pattern to whole graph",None, QApplication.UnicodeUTF8))
        #self.colorSpinBox.setMaximumWidth(80)
        self.colorSpinBox.setRange(0,255)
        self.colorSpinBox.setValue(aw.qmc.wheelcolorpattern)
        self.colorSpinBox.setWrapping(True)
        self.connect(self.colorSpinBox, SIGNAL("valueChanged(int)"),self.setcolorpattern)

        addButton = QPushButton(QApplication.translate("Button","Add",None, QApplication.UnicodeUTF8))
        addButton.setToolTip(QApplication.translate("Tooltip","Add new wheel",None, QApplication.UnicodeUTF8))
        #addButton.setMaximumWidth(100)
        self.connect(addButton, SIGNAL("clicked()"),self.insertwheel)

        rotateLeftButton = QPushButton(QApplication.translate("Button","<",None, QApplication.UnicodeUTF8))
        rotateLeftButton.setToolTip(QApplication.translate("Tooltip","Rotate graph 1 degree counter clockwise",None, QApplication.UnicodeUTF8))
        #rotateLeftButton.setMaximumWidth(30)
        self.connect(rotateLeftButton, SIGNAL("clicked()"),lambda x = 1: self.rotatewheels(x))
        
        rotateRightButton = QPushButton(QApplication.translate("Button",">",None, QApplication.UnicodeUTF8))
        rotateRightButton.setToolTip(QApplication.translate("Tooltip","Rotate graph 1 degree clockwise",None, QApplication.UnicodeUTF8))
        #rotateRightButton.setMaximumWidth(30)
        self.connect(rotateRightButton, SIGNAL("clicked()"),lambda x = 0: self.rotatewheels(x))

        saveButton = QPushButton(QApplication.translate("Button","Save File",None, QApplication.UnicodeUTF8))
        #saveButton.setMaximumWidth(100)
        self.connect(saveButton, SIGNAL("clicked()"),self.fileSave)
        saveButton.setToolTip(QApplication.translate("Tooltip","Save graph to a text file.wg",None, QApplication.UnicodeUTF8))
        
        saveImgButton = QPushButton(QApplication.translate("Button","Save Img",None, QApplication.UnicodeUTF8))
        saveImgButton.setToolTip(QApplication.translate("Tooltip","Save image using current graph size to a png format",None, QApplication.UnicodeUTF8))
        #saveImgButton.setMaximumWidth(100)
        self.connect(saveImgButton, SIGNAL("clicked()"),lambda x=0,i=1:aw.resize(x,i))

        openButton = QPushButton(QApplication.translate("Button","Open",None, QApplication.UnicodeUTF8))
        openButton.setToolTip(QApplication.translate("Tooltip","open graph file.wg",None, QApplication.UnicodeUTF8))
        #openButton.setMaximumWidth(100)
        self.connect(openButton, SIGNAL("clicked()"),self.loadWheel)

        closeButton = QPushButton(QApplication.translate("Button","Close",None, QApplication.UnicodeUTF8))
        closeButton.setToolTip(QApplication.translate("Tooltip","Close wheel graph editor",None, QApplication.UnicodeUTF8))
        #closeButton.setMaximumWidth(100)
        self.connect(closeButton, SIGNAL("clicked()"),self.close)

        aw.qmc.drawWheel()

        label1layout = QVBoxLayout()
        label2layout = QHBoxLayout()
        label1layout.addWidget(self.labeltable)
        label2layout.addWidget(self.labelCloseButton)
        label2layout.addWidget(self.labelResetButton)
        label1layout.addLayout(label2layout)

        self.labelGroupLayout = QGroupBox(QApplication.translate("GroupBox","Label Properties",None, QApplication.UnicodeUTF8))       
        self.labelGroupLayout.setLayout(label1layout)
        self.labelGroupLayout.setVisible(False)
        
        buttonlayout = QHBoxLayout()
        buttonlayout.addWidget(openButton)
        buttonlayout.addWidget(saveButton)
        buttonlayout.addWidget(saveImgButton)
        buttonlayout.addWidget(closeButton)

        configlayout =  QHBoxLayout()
        configlayout.addWidget(colorlabel)
        configlayout.addWidget(self.colorSpinBox)        
        configlayout.addWidget(txtlabel)
        configlayout.addWidget(txtButtonplus)
        configlayout.addWidget(txtButtonminus)

        configlayout.addWidget(edgelabel)
        configlayout.addWidget(self.edgeSpinBox)
        configlayout.addWidget(linewidthlabel)
        configlayout.addWidget(self.linewidthSpinBox)
        configlayout.addWidget(linecolor)

        controlLayout = QHBoxLayout()
        controlLayout.addWidget(addButton)
        controlLayout.addWidget(rotateLeftButton)
        controlLayout.addWidget(rotateRightButton)
        controlLayout.addWidget(self.hierarchyButton)

        mainlayout = QVBoxLayout()
        mainlayout.addWidget(self.datatable)
        mainlayout.addWidget(self.labelGroupLayout)
        mainlayout.addLayout(controlLayout)
        mainlayout.addLayout(configlayout)
        mainlayout.addLayout(buttonlayout)
        self.setLayout(mainlayout)

    #creates config table for wheel with index x
    def createlabeltable(self,x):
        self.labelwheelx = x                    #wheel being edited                             
        self.labelGroupLayout.setVisible(True)
        self.labeltable.setVisible(True)
        self.labelCloseButton.setVisible(True)
        self.labelResetButton.setVisible(True)

        self.labeltable.clear()        
        nlabels = len(aw.qmc.wheelnames[x])
        if nlabels:    
            self.labeltable.setRowCount(nlabels)
            self.labeltable.setColumnCount(5)
            self.labeltable.setHorizontalHeaderLabels([QApplication.translate("Table","Label",None, QApplication.UnicodeUTF8),
                                                       QApplication.translate("Table","Parent",None, QApplication.UnicodeUTF8),
                                                       QApplication.translate("Table","Width",None, QApplication.UnicodeUTF8),
                                                       QApplication.translate("Table","Color",None, QApplication.UnicodeUTF8),
                                                       QApplication.translate("Table","Opaqueness",None, QApplication.UnicodeUTF8)])
            self.labeltable.setAlternatingRowColors(True)
            self.labeltable.setEditTriggers(QTableWidget.NoEditTriggers)
            self.labeltable.setSelectionBehavior(QTableWidget.SelectRows)
            self.labeltable.setSelectionMode(QTableWidget.SingleSelection)
            self.labeltable.setShowGrid(True)
            #populate table
            for i in range(nlabels):
                label = QTableWidgetItem(aw.qmc.wheelnames[x][i])

                parentComboBox =  QComboBox()
                if x > 0:
                    items = aw.qmc.wheelnames[x-1][:]
                    items.insert(0,"")
                    parentComboBox.addItems(items)
                    if aw.qmc.wheellabelparent[x][i]:
                        parentComboBox.setCurrentIndex(aw.qmc.wheellabelparent[x][i])
                else:
                    parentComboBox.addItems([])
                self.connect(parentComboBox,SIGNAL("currentIndexChanged(int)"),lambda z=1,x=x,i=i:self.setwheelchild(z,x,i))
                
                labelwidthSpinBox = QDoubleSpinBox()
                labelwidthSpinBox.setRange(1.,100.)
                labelwidthSpinBox.setValue(aw.qmc.segmentlengths[x][i])
                labelwidthSpinBox.setSuffix("%")
                self.connect(labelwidthSpinBox, SIGNAL("valueChanged(double)"),lambda z=1,x=x,u=i: self.setlabelwidth(z,x,u))

                colorButton = QPushButton("Set Color")
                self.connect(colorButton, SIGNAL("clicked()"),lambda x =x,i=i: self.setsegmentcolor(x,i))

                alphaSpinBox = QSpinBox()
                alphaSpinBox.setRange(0,10)
                alphaSpinBox.setValue(int(aw.qmc.segmentsalpha[x][i]*10))
                self.connect(alphaSpinBox, SIGNAL("valueChanged(int)"),lambda z=1,x=x,u=i: self.setsegmentalpha(z,x,u))
               
                #add widgets to the table
                self.labeltable.setItem(i,0,label)
                self.labeltable.setCellWidget(i,1,parentComboBox)                  
                self.labeltable.setCellWidget(i,2,labelwidthSpinBox)
                self.labeltable.setCellWidget(i,3,colorButton)
                self.labeltable.setCellWidget(i,4,alphaSpinBox)


    def setsegmentcolor(self,x,i):
        colorf = QColorDialog.getColor(QColor(aw.qmc.wheelcolor[x][i]),self)
        if colorf.isValid():
            colorname = unicode(colorf.name())
            aw.qmc.wheelcolor[x][i] = colorname      #add new color to label
            
            self.createdatatable()                           #update main table with label names (label::color)
            aw.qmc.drawWheel()

    #sets a uniform color in wheel
    def setwheelcolor(self,x):
        colorf = QColorDialog.getColor(QColor(aw.qmc.wheelcolor[x][0]),self)
        if colorf.isValid():
            colorname = unicode(colorf.name())
            for i in range(len(aw.qmc.wheelcolor[x])):                  
                aw.qmc.wheelcolor[x][i] =  colorname
                
        self.createdatatable()                           
        aw.qmc.drawWheel()

    #sets color pattern (many colors) in wheel    
    def setwheelcolorpattern(self,z,x):
        wsb =  self.datatable.cellWidget(x,9)
        wpattern = wsb.value()        
        wlen = len(aw.qmc.wheelcolor[x])
        for i in range(wlen):
            color = QColor()
            color.setHsv((360/wlen)*i*wpattern,255,255,255)
            aw.qmc.wheelcolor[x][i] = unicode(color.name())
        aw.qmc.drawWheel()

    #sets color pattern (many colors) for whole graph    
    def setcolorpattern(self):
        aw.qmc.wheelcolorpattern = self.colorSpinBox.value()
        if aw.qmc.wheelcolorpattern:
            for x in range(len(aw.qmc.wheelcolor)):
                wlen = len(aw.qmc.wheelcolor[x])
                for i in range(wlen):
                    color = QColor()
                    color.setHsv((360/wlen)*i*aw.qmc.wheelcolorpattern,255,255,255)
                    aw.qmc.wheelcolor[x][i] = unicode(color.name())

            aw.qmc.drawWheel()
        
    def setsegmentalpha(self,z,x,u):
        aw.qmc.segmentsalpha[x][u] = float(z/10.) 
        aw.qmc.drawWheel()

    #rotate whole graph 
    def rotatewheels(self,x):
        if x == 1: #left,counterclockwise
            for i in range(len(aw.qmc.startangle)):
                aw.qmc.startangle[i] += 1
        elif x == 0: #right,clockwise
            for i in range(len(aw.qmc.startangle)):              
                aw.qmc.startangle[i] -= 1
        aw.qmc.drawWheel()

    #z= new width%, x= wheel number index, u = index of segment in the wheel    
    def setlabelwidth(self,z,x,u):
        newwidth = z
        oldwidth = aw.qmc.segmentlengths[x][u]
        diff = newwidth - oldwidth
        l = len(aw.qmc.segmentlengths[x])
        for i in range(l):
            if i != u:
                if diff > 0:
                    aw.qmc.segmentlengths[x][i] -= abs(float(diff))/(l-1)
                else:
                    aw.qmc.segmentlengths[x][i] += abs(float(diff))/(l-1)
        aw.qmc.segmentlengths[x][u] = newwidth
        aw.qmc.drawWheel()

    #input: z = index of parent in previus wheel; x = wheel number; i = index of element in wheel
    def setwheelchild(self,z,x,i):
        aw.qmc.setwheelchild(z,x,i)
        aw.qmc.drawWheel()
        self.createdatatable() #update data table        

    #deletes parent-child relation in a wheel. It obtains the wheel index by self.labelwheelx
    def resetlabelparents(self):
        x = self.labelwheelx
        nsegments = len(aw.qmc.wheellabelparent[x])
        for i in range(nsegments):
            aw.qmc.wheellabelparent[x][i] = 0
            aw.qmc.segmentlengths[x][i] = 100./nsegments
            
        aw.qmc.drawWheel()
        self.createlabeltable(x)

    #adjust decorative edge between wheels
    def setedge(self):
        aw.qmc.wheeledge = float(self.edgeSpinBox.value())/100.
        aw.qmc.drawWheel()

    #adjusts line thickness
    def setlinewidth(self):
        aw.qmc.wheellinewidth = self.linewidthSpinBox.value()
        aw.qmc.drawWheel()

    #sets line color
    def setlinecolor(self):
        colorf = QColorDialog.getColor(QColor(aw.qmc.wheellinecolor),self)
        if colorf.isValid():
            colorname = unicode(colorf.name())
            aw.qmc.wheellinecolor = colorname      #add new color to label            
            aw.qmc.drawWheel()

    #makes not visible the wheel config table 
    def closelabels(self):
        self.labelGroupLayout.setVisible(False)
        self.labeltable.setVisible(False)
        self.labelCloseButton.setVisible(False)
        self.labelResetButton.setVisible(False)

    #creates graph table    
    def createdatatable(self):
        self.datatable.clear()        
        ndata = len(aw.qmc.wheelnames)
        if ndata:    
            self.datatable.setRowCount(ndata)
            self.datatable.setColumnCount(10)
            self.datatable.setHorizontalHeaderLabels([QApplication.translate("Table","Delete Wheel",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","Edit Labels",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","Update Labels",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","Properties",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","Radius",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","Starting angle",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","Txt Projection",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","Text size",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","Color",None, QApplication.UnicodeUTF8),
                                                      QApplication.translate("Table","Color Pattern",None, QApplication.UnicodeUTF8)])
            self.datatable.setAlternatingRowColors(True)
            self.datatable.setEditTriggers(QTableWidget.NoEditTriggers)
            self.datatable.setSelectionBehavior(QTableWidget.SelectRows)
            self.datatable.setSelectionMode(QTableWidget.SingleSelection)
            self.datatable.setShowGrid(True)

            #populate table
            for i in range(ndata):
                delButton = QPushButton(QApplication.translate("Button","Delete",None, QApplication.UnicodeUTF8))
                self.connect(delButton, SIGNAL("clicked()"),lambda x = i: self.popwheel(x))

                labelsedit = QLineEdit(unicode(",".join(aw.qmc.wheelnames[i])))

                updateButton = QPushButton(QApplication.translate("Button","Update",None, QApplication.UnicodeUTF8))
                self.connect(updateButton, SIGNAL("clicked()"),lambda x = i: self.updatelabels(x))

                setButton = QPushButton(QApplication.translate("Button","Wheel Properties",None, QApplication.UnicodeUTF8))
                self.connect(setButton, SIGNAL("clicked()"),lambda x = i: self.createlabeltable(x))                
                               
                widthSpinBox = QDoubleSpinBox()
                widthSpinBox.setRange(1.,100.)
                widthSpinBox.setValue(aw.qmc.wradii[i])
                widthSpinBox.setSuffix("%")
                self.connect(widthSpinBox, SIGNAL("valueChanged(double)"),lambda z=1,x=i: self.setwidth(z,x))

                angleSpinBox = QSpinBox()
                angleSpinBox.setSuffix(QApplication.translate("SpinBox"," dg",None, QApplication.UnicodeUTF8))
                angleSpinBox.setRange(0,359)
                angleSpinBox.setWrapping(True)
                angleSpinBox.setValue(aw.qmc.startangle[i])
                self.connect(angleSpinBox, SIGNAL("valueChanged(int)"),lambda z=1,x=i: self.setangle(z,x))

                projectionComboBox =  QComboBox()
                projectionComboBox.addItems([QApplication.translate("ComboBox","Flat",None, QApplication.UnicodeUTF8),
                                             QApplication.translate("ComboBox","Perpendicular",None, QApplication.UnicodeUTF8),
                                             QApplication.translate("ComboBox","Radial",None, QApplication.UnicodeUTF8)])
                projectionComboBox.setCurrentIndex(aw.qmc.projection[i])
                self.connect(projectionComboBox,SIGNAL("currentIndexChanged(int)"),lambda z=1,x=i:self.setprojection(z,x))

                txtSpinBox = QSpinBox()
                txtSpinBox.setRange(1,30)
                txtSpinBox.setValue(aw.qmc.wheeltextsize[i])
                self.connect(txtSpinBox, SIGNAL("valueChanged(int)"),lambda z=1,x=i: self.setTextsizeX(z,x))                

                colorButton = QPushButton(QApplication.translate("Button","Set Color",None, QApplication.UnicodeUTF8))
                self.connect(colorButton, SIGNAL("clicked()"),lambda x =i: self.setwheelcolor(x))

                colorSpinBox = QSpinBox()
                colorSpinBox.setRange(0,255)
                colorSpinBox.setWrapping(True)
                self.connect(colorSpinBox, SIGNAL("valueChanged(int)"),lambda z=1,x=i,: self.setwheelcolorpattern(z,x))

                
                #add widgets to the table
                self.datatable.setCellWidget(i,0,delButton)
                self.datatable.setCellWidget(i,1,labelsedit)
                self.datatable.setCellWidget(i,2,updateButton)                
                self.datatable.setCellWidget(i,3,setButton)                
                self.datatable.setCellWidget(i,4,widthSpinBox)
                self.datatable.setCellWidget(i,5,angleSpinBox)
                self.datatable.setCellWidget(i,6,projectionComboBox)
                self.datatable.setCellWidget(i,7,txtSpinBox)
                self.datatable.setCellWidget(i,8,colorButton)
                self.datatable.setCellWidget(i,9,colorSpinBox)

    #reads label edit box for wheel with index x, and updates labels 
    def updatelabels(self,x):
        labelsedit =  self.datatable.cellWidget(x,1)
        text  = unicode(labelsedit.text())
        if "\\n" in text:              #make multiple line text if "\n" found in label string
            parts = text.split("\\n")
            text = chr(10).join(parts)
        newwheellabels = text.strip().split(",")
        newnlabels = len(newwheellabels)
        oldnlabels = len(aw.qmc.wheelnames[x])
        
        #adjust segments len and alpha for each wheel if number of labels changed
        if oldnlabels != newnlabels:
            aw.qmc.segmentlengths[x] = [100./newnlabels]*newnlabels                    
            aw.qmc.segmentsalpha[x] = [.3]*newnlabels
            aw.qmc.wheellabelparent[x] = [0]*newnlabels
            aw.qmc.wheelcolor[x] = [aw.qmc.wheelcolor[x][0]]*newnlabels
            
        aw.qmc.wheelnames[x] = newwheellabels[:]        
        aw.qmc.drawWheel()        

    #sets radii for a wheel. z is a variable dummy with no meaning but passed by the Qt inner workings
    def setwidth(self,z,x):
        widthSpinBox = self.datatable.cellWidget(x,4)
        newwidth = widthSpinBox.value()
        oldwidth = aw.qmc.wradii[x]
        diff = newwidth - oldwidth
        l = len(aw.qmc.wradii)
        for i in range(l):
            if i != x:
                if diff > 0:
                    aw.qmc.wradii[i] -= abs(float(diff))/(l-1)
                else:
                    aw.qmc.wradii[i] += abs(float(diff))/(l-1)

        aw.qmc.wradii[x] = newwidth
        
        #Need 100.0% coverage. Correct for numerical floating point rounding errors:
        count = 0.            
        for i in range(len(aw.qmc.wradii)):
            count +=  aw.qmc.wradii[i]
        diff = 100. - count
        if diff  != 0.:
            if diff > 0.000:  #if count smaller
                aw.qmc.wradii[x] += abs(diff)
            else:
                aw.qmc.wradii[x] -= abs(diff)
                
        aw.qmc.drawWheel()

    #sets starting angle (rotation) for a wheel with index x
    def setangle(self,z,x):
        angleSpinBox = self.datatable.cellWidget(x,5)
        aw.qmc.startangle[x] = angleSpinBox.value()
        aw.qmc.drawWheel()

    #sets text projection style for a wheel with index x
    def setprojection(self,z,x):
        projectionComboBox = self.datatable.cellWidget(x,6)
        aw.qmc.projection[x] = projectionComboBox.currentIndex()
        aw.qmc.drawWheel()

    #chages text size in wheel with index x
    def setTextsizeX(self,z,x):
        txtSpinBox = self.datatable.cellWidget(x,7)
        aw.qmc.wheeltextsize[x] = txtSpinBox.value()
        aw.qmc.drawWheel()

    #changes size of text in whole graph
    def changetext(self,x):
        for i in range(len(aw.qmc.wheeltextsize)):
            if x == 1:
                aw.qmc.wheeltextsize[i] += 1
            else:
                aw.qmc.wheeltextsize[i] -= 1
        aw.qmc.drawWheel()

    #adds new top wheel 
    def insertwheel(self):
        ndata = len(aw.qmc.wradii)
        if ndata:
            count = 0.
            for i in range(ndata):
                aw.qmc.wradii[i] = 100./(ndata+1)
                count += aw.qmc.wradii[i]
            aw.qmc.wradii.append(100.-count)
        else:
            aw.qmc.wradii.append(100.)
        #find number of labels of most outer wheel (last)
        if len(aw.qmc.wheelnames):
            nwheels = len(aw.qmc.wheelnames[-1])
        else:                                       #if no wheels
            nwheels = 3
        wn,sl,sa,wlp,co = [],[],[],[],[]
        for i in range(nwheels+1):
            wn.append("W%i %i"%(len(aw.qmc.wheelnames)+1,i+1))
            sl.append(100./(nwheels+1))
            sa.append(.3)
            wlp.append(0)
            color = QColor()
            color.setHsv((360/(nwheels+1))*i,255,255,255)
            co.append(unicode(color.name()))       
            
        aw.qmc.wheelnames.append(wn)
        aw.qmc.segmentlengths.append(sl)
        aw.qmc.segmentsalpha.append(sa)
        aw.qmc.wheellabelparent.append(wlp)
        aw.qmc.startangle.append(0)
        aw.qmc.projection.append(2)
        aw.qmc.wheeltextsize.append(10)
        aw.qmc.wheelcolor.append(co)

        self.createdatatable()
        aw.qmc.drawWheel()

    #deletes wheel with index x
    def popwheel(self,x):
        #correct raius of other wheels (to use 100% coverage)
        width = aw.qmc.wradii[x]
        l = len(aw.qmc.wradii)
        for i in range(l):
            if i != x:
                aw.qmc.wradii[i] += float(width)/(l-1)
        
        aw.qmc.wheelnames.pop(x)
        aw.qmc.wradii.pop(x)
        aw.qmc.startangle.pop(x)
        aw.qmc.projection.pop(x)
        aw.qmc.wheeltextsize.pop(x)
        aw.qmc.segmentlengths.pop(x)
        aw.qmc.segmentsalpha.pop(x)
        aw.qmc.wheellabelparent.pop(x)
        aw.qmc.wheelcolor.pop(x)
        
        self.createdatatable()
        aw.qmc.drawWheel()

    def fileSave(self):
        try:
            filename = aw.ArtisanSaveFileDialog(msg=QApplication.translate("MessageBox Caption","Save Wheel graph",None, QApplication.UnicodeUTF8),ext="*.wg")
            if filename:
                #write
                aw.serialize(filename,aw.getWheelGraph())
                aw.sendmessage(QApplication.translate("Message Area","Wheel Graph saved",None, QApplication.UnicodeUTF8))
        except IOError,e:
            aw.qmc.adderror(QApplication.translate("Error Message","IO Error: Wheel graph filesave(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            return

    def loadWheel(self):        
        filename = aw.ArtisanOpenFileDialog(msg=QApplication.translate("MessageBox Caption","Open Wheel Graph",None, QApplication.UnicodeUTF8),ext="*.wg")
        aw.loadWheel(filename)
        self.createdatatable()
        aw.qmc.drawWheel()

    def closeEvent(self, event):    
        aw.qmc.redraw()
        aw.lowerbuttondialog.setVisible(True)
        if aw.minieventsflag:
            aw.EventsGroupLayout.setVisible(True)
           
############################################################
#######################  ALARM DIALOG  #####################
############################################################

class AlarmDlg(QDialog):
    def __init__(self, parent = None):
        super(AlarmDlg,self).__init__(parent)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate("Form Caption","Alarms",None, QApplication.UnicodeUTF8))

        #table for alarms
        self.alarmtable = QTableWidget()
        self.alarmtable.setTabKeyNavigation(True)
        self.createalarmtable()        

        allonButton = QPushButton(QApplication.translate("Button","All On",None, QApplication.UnicodeUTF8))
        self.connect(allonButton,  SIGNAL("clicked()"), lambda flag=1: self.alarmson(flag))
        allonButton.setFocusPolicy(Qt.NoFocus)

        alloffButton = QPushButton(QApplication.translate("Button","All Off",None, QApplication.UnicodeUTF8))
        self.connect(alloffButton, SIGNAL("clicked()"), lambda flag=0: self.alarmson(flag))
        alloffButton.setFocusPolicy(Qt.NoFocus)

        addButton = QPushButton(QApplication.translate("Button","Add",None, QApplication.UnicodeUTF8))
        self.connect(addButton, SIGNAL("clicked()"),self.addalarm)
        addButton.setMaximumWidth(100)
        addButton.setMinimumWidth(100)
        addButton.setFocusPolicy(Qt.NoFocus)

        deleteButton = QPushButton(QApplication.translate("Button","Delete",None, QApplication.UnicodeUTF8))
        self.connect(deleteButton, SIGNAL("clicked()"),self.deletealarm)
        deleteButton.setMaximumWidth(100)
        deleteButton.setMinimumWidth(100)
        deleteButton.setFocusPolicy(Qt.NoFocus)

        saveButton = QPushButton(QApplication.translate("Button","OK",None, QApplication.UnicodeUTF8))
        self.connect(saveButton, SIGNAL("clicked()"),self.closealarms)

        tablelayout = QVBoxLayout()
        buttonlayout = QHBoxLayout()
        mainlayout = QVBoxLayout()

        tablelayout.addWidget(self.alarmtable)
        buttonlayout.addWidget(addButton)
        buttonlayout.addWidget(deleteButton)
        buttonlayout.addStretch()
        buttonlayout.addSpacing(10)
        buttonlayout.addWidget(alloffButton)        
        buttonlayout.addWidget(allonButton)
        buttonlayout.addSpacing(10)
        buttonlayout.addStretch()
        buttonlayout.addWidget(saveButton)

        mainlayout.addLayout(tablelayout)
        mainlayout.addLayout(buttonlayout)

        self.setLayout(mainlayout)

    def alarmson(self,flag):
        for i in range(len(aw.qmc.alarmflag)):
            if flag == 1:
                aw.qmc.alarmflag[i] = 1
            else:
                aw.qmc.alarmflag[i] = 0
        self.createalarmtable()

    def addalarm(self):
        #self.savealarms()
        aw.qmc.alarmtime.append(1)
        aw.qmc.alarmflag.append(1)
        aw.qmc.alarmsource.append(1)
        aw.qmc.alarmtemperature.append(500)
        aw.qmc.alarmaction.append(0)
        aw.qmc.alarmstrings.append(QApplication.translate("Alarm","Enter description",None, QApplication.UnicodeUTF8))
        self.createalarmtable()

        aw.qmc.alarmstate = [0]*len(aw.qmc.alarmflag)   # 0 = not triggered
        
    def deletealarm(self):        
        nalarms = len(aw.qmc.alarmflag)
        if nalarms:
            # check for selection            
            selected = self.alarmtable.selectedRanges()
            if selected and len(selected) > 0:
                selected_row = selected[0].topRow()
                aw.qmc.alarmtime = aw.qmc.alarmtime[0:selected_row] + aw.qmc.alarmtime[selected_row + 1:]
                aw.qmc.alarmflag = aw.qmc.alarmflag[0:selected_row] + aw.qmc.alarmflag[selected_row + 1:]
                aw.qmc.alarmsource = aw.qmc.alarmsource[0:selected_row] + aw.qmc.alarmsource[selected_row + 1:]
                aw.qmc.alarmtemperature = aw.qmc.alarmtemperature[0:selected_row] + aw.qmc.alarmtemperature[selected_row + 1:]
                aw.qmc.alarmaction = aw.qmc.alarmaction[0:selected_row] + aw.qmc.alarmaction[selected_row + 1:]
                aw.qmc.alarmstrings = aw.qmc.alarmstrings[0:selected_row] + aw.qmc.alarmstrings[selected_row + 1:]
            else:
                # nothing selected, we pop the last element
                aw.qmc.alarmtime.pop()                                                                
                aw.qmc.alarmflag.pop()            
                aw.qmc.alarmsource.pop()
                aw.qmc.alarmtemperature.pop()
                aw.qmc.alarmaction.pop()
                aw.qmc.alarmstrings.pop()
            self.createalarmtable()

            aw.qmc.alarmstate = [0]*len(aw.qmc.alarmflag)    # 0 = not triggered

        if not len(aw.qmc.alarmflag):
            if self.alarmtable.rowCount():
                self.alarmtable.setRowCount(0)
       
    def closealarms(self):
        self.savealarms()
        self.accept()
        
    def savealarms(self):
        nalarms = self.alarmtable.rowCount()
        for i in range(nalarms):
            timez =  self.alarmtable.cellWidget(i,0)
            aw.qmc.alarmtime[i] = int(unicode(timez.currentIndex()))                                       
            flag = self.alarmtable.cellWidget(i,1)
            aw.qmc.alarmflag[i] = int(unicode(flag.currentIndex()))
            atype = self.alarmtable.cellWidget(i,2)
            aw.qmc.alarmsource[i] = int(unicode(atype.currentIndex()))
            temp = self.alarmtable.cellWidget(i,3)
            aw.qmc.alarmtemperature[i] = int(unicode(temp.text()))
            action = self.alarmtable.cellWidget(i,4)
            aw.qmc.alarmaction[i] = int(unicode(action.currentIndex()))
            description = self.alarmtable.cellWidget(i,5)
            aw.qmc.alarmstrings[i] = unicode(description.text())

            aw.qmc.alarmstate = [0]*len(aw.qmc.alarmflag)    # 0 = not triggered

               
    def createalarmtable(self):
        self.alarmtable.clear()        
        nalarms = len(aw.qmc.alarmtemperature)
        if nalarms:    
            self.alarmtable.setRowCount(nalarms)
            self.alarmtable.setColumnCount(6)
            self.alarmtable.setHorizontalHeaderLabels([QApplication.translate("Table","From",None, QApplication.UnicodeUTF8),
                                                       QApplication.translate("Table","Status",None, QApplication.UnicodeUTF8),
                                                       QApplication.translate("Table","Source",None, QApplication.UnicodeUTF8),
                                                       QApplication.translate("Table","Temperature",None, QApplication.UnicodeUTF8),
                                                       QApplication.translate("Table","Action",None, QApplication.UnicodeUTF8),
                                                       QApplication.translate("Table","Description",None, QApplication.UnicodeUTF8)])
            self.alarmtable.setAlternatingRowColors(True)
            self.alarmtable.setEditTriggers(QTableWidget.NoEditTriggers)
            self.alarmtable.setSelectionBehavior(QTableWidget.SelectRows)
            self.alarmtable.setSelectionMode(QTableWidget.SingleSelection)
            self.alarmtable.setShowGrid(True)

            #populate table
            for i in range(nalarms):
                #Effective time from
                timeComboBox = QComboBox()
                timeComboBox.addItems([QApplication.translate("ComboBox","CHARGE",None, QApplication.UnicodeUTF8),
                                       QApplication.translate("ComboBox","DRY END",None, QApplication.UnicodeUTF8),
                                       QApplication.translate("ComboBox","FC START",None, QApplication.UnicodeUTF8),
                                       QApplication.translate("ComboBox","FC END",None, QApplication.UnicodeUTF8),
                                       QApplication.translate("ComboBox","SC START",None, QApplication.UnicodeUTF8),
                                       QApplication.translate("ComboBox","DROP",None, QApplication.UnicodeUTF8)])
                timeComboBox.setCurrentIndex(aw.qmc.alarmtime[i])
                                            
                #flag
                flagComboBox = QComboBox()
                flagComboBox.addItems([QApplication.translate("ComboBox","OFF",None, QApplication.UnicodeUTF8),
                                       QApplication.translate("ComboBox","ON",None, QApplication.UnicodeUTF8)])
                flagComboBox.setCurrentIndex(aw.qmc.alarmflag[i])

                #type
                typeComboBox = QComboBox()
                typeComboBox.addItems([QApplication.translate("ComboBox","ET",None, QApplication.UnicodeUTF8),
                                       QApplication.translate("ComboBox","BT",None, QApplication.UnicodeUTF8)])
                typeComboBox.setCurrentIndex(aw.qmc.alarmsource[i])

                #temperature
                tempedit = QLineEdit(unicode(aw.qmc.alarmtemperature[i]))
                tempedit.setValidator(QIntValidator(0, 1000,tempedit))

                #action
                actionComboBox = QComboBox()
                actionComboBox.addItems([QApplication.translate("ComboBox","Pop up window",None, QApplication.UnicodeUTF8),
                                         QApplication.translate("ComboBox","Call program",None, QApplication.UnicodeUTF8)])
                actionComboBox.setCurrentIndex(aw.qmc.alarmaction[i])
                    
                #text description
                descriptionedit = QLineEdit(unicode(aw.qmc.alarmstrings[i]))

                #add widgets to the table
                self.alarmtable.setCellWidget(i,0,timeComboBox)                
                self.alarmtable.setCellWidget(i,1,flagComboBox)
                self.alarmtable.setCellWidget(i,2,typeComboBox)
                self.alarmtable.setCellWidget(i,3,tempedit)
                self.alarmtable.setCellWidget(i,4,actionComboBox)                
                self.alarmtable.setCellWidget(i,5,descriptionedit)



# UNDER WORK 
#######################################################################################
#################### COFFEE CRACK  DETECTOR PROJECT ###################################
#######################################################################################

class soundcrack(FigureCanvas):
    def __init__(self,parent):
        
        self.fig = Figure(facecolor=u'lightgrey')
        
        FigureCanvas.__init__(self, self.fig)

        self.ax = self.fig.add_subplot(111, axisbg="black")
        self.ax.grid(True,linewidth=2,color="green")
        
        self.ax.set_xlim(0,5500)
        self.ax.set_ylim(-1,1)

        #make first empty plot of frequency
        self.Freqline, = self.ax.plot([], [], animated=True, lw=1,color = "#78E800")
        #make first empty plot of rms amplitude     
        self.Ampline, = self.ax.plot([], [], animated=True, lw=2,color = "orange")
        self.N_SAMPLES = 1024
        self.SAMPLING_RATE = 11025
        self.amplitudeThreshold = .6
        self.fig.canvas.draw()
        self.background = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        self.ampsensitivity = 10
                         
        self.freqs = numpy.fft.fftfreq(self.N_SAMPLES,1./self.SAMPLING_RATE)[:self.N_SAMPLES/2] #X axis
        
        self.stream = None
        self.pa = None
        self.ON = 0

    def reset(self):
        self.fig.clf()   #wipe out figure
        self.ax = self.fig.add_subplot(111, axisbg="black")
        self.ax.grid(True,linewidth=2,color="green")
        self.ax.set_xlim(0,5500)
        self.ax.set_ylim(-1,1)
        self.fig.canvas.draw()
        self.background = self.fig.canvas.copy_from_bbox(self.ax.bbox)
                                 
    def crackdetedted(self):
        pass

    #updates animated display
    def blitsound(self):   
        if self.ON:
            self.fig.canvas.restore_region(self.background)
            F,amplitude = self.getsound()
            amplitude *= self.ampsensitivity
            self.Freqline.set_data(self.freqs,F)
            self.Ampline.set_data([0,5500],[amplitude,amplitude])
            self.ax.draw_artist(self.Freqline)
            self.ax.draw_artist(self.Ampline)       
            self.fig.canvas.blit(self.ax.bbox)

    def opensound(self):
        try:
            import pyaudio
        except ImportError:
            return False
        self.reset()
        self.ON = 1    
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=pyaudio.paInt16, channels=1, rate=self.SAMPLING_RATE,
                     input=True, frames_per_buffer=self.N_SAMPLES)

    def closesound(self):
        self.ON = 0
        self.stream.close()
        self.pa.terminate()
        
    def getsound(self):

        #F[m] = m*SAMPLING_RATE/N_SAMPLES   (List with magnitudes of frequencies) Y axis
        
        block = self.stream.read(self.N_SAMPLES)        
        
        count = len(block)/2
        formatS = "%dh"%(count)    
        audio_data  = struct.unpack( formatS, block )

        sum_squares = 0
        naudio = []
        for sample in audio_data:
            n = sample /32768.            #normalize        
            naudio.append(n)            
            sum_squares += n*n

        F = fft(naudio)[:self.N_SAMPLES/2]  
        amplitude =  math.sqrt( sum_squares / count )    #rms
        
        return F,amplitude  


#########################################################################
######################## FUJI PXR CONTROL DIALOG  #######################
#########################################################################

class PXRpidDlgControl(QDialog):
    def __init__(self, parent = None):
        super(PXRpidDlgControl,self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.setWindowTitle(QApplication.translate("Form Caption","Fuji PXR PID control",None, QApplication.UnicodeUTF8))

        #create Ramp Soak control button colums

        self.labelrs1 = QLabel()
        self.labelrs1.setMargin(5)
        self.labelrs1.setStyleSheet("background-color:'#CCCCCC';")
        self.labelrs1.setText("<font color='white'><b>" + QApplication.translate("Label", "Ramp Soak HH:MM<br>(1-4)",None, QApplication.UnicodeUTF8) + "<\b></font>")
        self.labelrs1.setMaximumSize(120, 62)

        self.labelrs2 = QLabel()
        self.labelrs2.setMargin(5)
        self.labelrs2.setStyleSheet("background-color:'#CCCCCC';")
        self.labelrs2.setText("<font color='white'><b>" + QApplication.translate("Label", "Ramp Soak HH:MM<br>(5-8)",None, QApplication.UnicodeUTF8) + "<\b></font>")
        self.labelrs2.setMaximumSize(120, 62)

        labelpattern = QLabel(QApplication.translate("Label", "Ramp/Soak Pattern",None, QApplication.UnicodeUTF8))
        self.patternComboBox =  QComboBox()
        self.patternComboBox.addItems(["1-4","5-8","1-8"])
        self.patternComboBox.setCurrentIndex(aw.pid.PXR["rampsoakpattern"][0])

        self.status = QStatusBar()
        self.status.setSizeGripEnabled(False)
        self.status.showMessage(QApplication.translate("StatusBar","Ready",None, QApplication.UnicodeUTF8),5000)

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
        button_getall = QPushButton(QApplication.translate("Button","Read Ra/So values",None, QApplication.UnicodeUTF8))
        button_rson =  QPushButton(QApplication.translate("Button","RampSoak ON",None, QApplication.UnicodeUTF8))        
        button_rsoff =  QPushButton(QApplication.translate("Button","RampSoak OFF",None, QApplication.UnicodeUTF8))
        button_standbyON = QPushButton(QApplication.translate("Button","PID OFF",None, QApplication.UnicodeUTF8))
        button_standbyOFF = QPushButton(QApplication.translate("Button","PID ON",None, QApplication.UnicodeUTF8))
        button_exit = QPushButton(QApplication.translate("Button","Close",None, QApplication.UnicodeUTF8))

        self.connect(self.patternComboBox,SIGNAL("currentIndexChanged(int)"),self.paintlabels)
        self.connect(button_getall, SIGNAL("clicked()"), self.getallsegments)
        self.connect(button_rson, SIGNAL("clicked()"), lambda flag=1: self.setONOFFrampsoak(flag))
        self.connect(button_rsoff, SIGNAL("clicked()"), lambda flag=0: self.setONOFFrampsoak(flag))
        self.connect(button_standbyON, SIGNAL("clicked()"), lambda flag=1: self.setONOFFstandby(flag))
        self.connect(button_standbyOFF, SIGNAL("clicked()"), lambda flag=0: self.setONOFFstandby(flag))
        self.connect(button_exit, SIGNAL("clicked()"),self, SLOT("reject()"))

        #TAB 2
        tab2svbutton = QPushButton(QApplication.translate("Button","Write SV",None, QApplication.UnicodeUTF8))
        tab2cancelbutton = QPushButton(QApplication.translate("Button","Cancel",None, QApplication.UnicodeUTF8))
        tab2easyONsvbutton = QPushButton(QApplication.translate("Button","Turn ON SV buttons",None, QApplication.UnicodeUTF8))
        tab2easyONsvbutton.setStyleSheet("QPushButton { background-color: #ffaaff}")
        tab2easyOFFsvbutton = QPushButton(QApplication.translate("Button","Turn OFF SV buttons",None, QApplication.UnicodeUTF8))
        tab2easyOFFsvbutton.setStyleSheet("QPushButton { background-color: lightblue}")
        tab2getsvbutton = QPushButton(QApplication.translate("Button","Read current SV value",None, QApplication.UnicodeUTF8))
        self.readsvedit = QLineEdit()
        self.connect(tab2svbutton, SIGNAL("clicked()"),self.setsv)
        self.connect(tab2getsvbutton, SIGNAL("clicked()"),self.getsv)
        self.connect(tab2cancelbutton, SIGNAL("clicked()"),self, SLOT("reject()"))
        self.connect(tab2easyONsvbutton, SIGNAL("clicked()"), lambda flag=1: aw.pid.activateONOFFeasySV(flag))
        self.connect(tab2easyOFFsvbutton, SIGNAL("clicked()"), lambda flag=0: aw.pid.activateONOFFeasySV(flag))
        svwarning1 = QLabel("<CENTER><b>" + QApplication.translate("Label", "WARNING",None, QApplication.UnicodeUTF8) + "</b><br>"
                            + QApplication.translate("Label", "Writing eeprom memory",None, QApplication.UnicodeUTF8) + "<br>"
                            + QApplication.translate("Label", "<u>Max life</u> 10,000 writes",None, QApplication.UnicodeUTF8) + "<br>"
                            + QApplication.translate("Label", "Infinite read life.",None, QApplication.UnicodeUTF8) + "</CENTER>")
        svwarning2 = QLabel("<CENTER><b>" + QApplication.translate("Label", "WARNING",None, QApplication.UnicodeUTF8) + "</b><br>"
                            + QApplication.translate("Label", "After <u>writing</u> an adjustment,<br>never power down the pid<br>for the next 5 seconds <br>or the pid may never recover.",None, QApplication.UnicodeUTF8) + "<br>"
                            + QApplication.translate("Label", "Read operations manual",None, QApplication.UnicodeUTF8) + "</CENTER>")
        self.svedit = QLineEdit()
        self.svedit.setValidator(QDoubleValidator(0., 999., 1, self.svedit))
        
        #TAB 3
        button_p = QPushButton(QApplication.translate("Button","Set p",None, QApplication.UnicodeUTF8))
        button_i = QPushButton(QApplication.translate("Button","Set i",None, QApplication.UnicodeUTF8))
        button_d = QPushButton(QApplication.translate("Button","Set d",None, QApplication.UnicodeUTF8))
        plabel =  QLabel(QApplication.translate("Label", "p",None, QApplication.UnicodeUTF8))
        ilabel =  QLabel(QApplication.translate("Label", "i",None, QApplication.UnicodeUTF8))
        dlabel =  QLabel(QApplication.translate("Label", "d",None, QApplication.UnicodeUTF8))
        self.pedit = QLineEdit(str(aw.pid.PXR["p"][0]))
        self.iedit = QLineEdit(str(aw.pid.PXR["i"][0]))
        self.dedit = QLineEdit(str(aw.pid.PXR["d"][0]))
        self.pedit.setMaximumWidth(60)
        self.iedit.setMaximumWidth(60)
        self.dedit.setMaximumWidth(60)
        self.pedit.setValidator(QDoubleValidator(0., 999., 1, self.pedit))
        self.iedit.setValidator(QIntValidator(0, 3200, self.iedit))
        self.dedit.setValidator(QDoubleValidator(0., 999.0, 1, self.dedit))
        button_autotuneON = QPushButton(QApplication.translate("Button","Autotune ON",None, QApplication.UnicodeUTF8))
        button_autotuneOFF = QPushButton(QApplication.translate("Button","Autotune OFF",None, QApplication.UnicodeUTF8))
        button_readpid = QPushButton(QApplication.translate("Button","Read PID values",None, QApplication.UnicodeUTF8))
        tab3cancelbutton = QPushButton(QApplication.translate("Button","Cancel",None, QApplication.UnicodeUTF8))

        self.connect(button_autotuneON, SIGNAL("clicked()"), lambda flag=1: self.setONOFFautotune(flag))
        self.connect(button_autotuneOFF, SIGNAL("clicked()"), lambda flag=0: self.setONOFFautotune(flag))
        self.connect(button_p, SIGNAL("clicked()"), lambda var=u"p": self.setpid(var))
        self.connect(button_i, SIGNAL("clicked()"), lambda var=u"i": self.setpid(var))
        self.connect(button_d, SIGNAL("clicked()"), lambda var=u"d": self.setpid(var))
        self.connect(tab3cancelbutton, SIGNAL("clicked()"),self, SLOT("reject()"))
        self.connect(button_readpid, SIGNAL("clicked()"), self.getpid)

        #TAB4
        #table for setting segments
        self.segmenttable = QTableWidget()
        self.createsegmenttable()


        #****************************   TAB5 WIDGETS
        ETthermolabel = QLabel(QApplication.translate("Label","ET Thermocouple type",None, QApplication.UnicodeUTF8))
        BTthermolabel = QLabel(QApplication.translate("Label","BT Thermocouple type",None, QApplication.UnicodeUTF8))
        BTthermolabelnote = QLabel(QApplication.translate("Label","NOTE: BT Thermocouple type is not stored in the Artisan seetings",None, QApplication.UnicodeUTF8))
        self.ETthermocombobox = QComboBox()
        self.BTthermocombobox = QComboBox()
        self.thermotypes = ["J","K","R","B","S","T","E","N"]
        conversiontoindex = [2,3,4,5,6,7,8,12]  #converts fuji PID types to indexes
        self.ETthermocombobox.addItems(self.thermotypes)
        self.BTthermocombobox.addItems(self.thermotypes)
        self.ETthermocombobox.setCurrentIndex(conversiontoindex.index(aw.pid.PXG4["pvinputtype"][0]))
        setETthermocouplebutton = QPushButton(QApplication.translate("Button","Set",None, QApplication.UnicodeUTF8))
        setBTthermocouplebutton = QPushButton(QApplication.translate("Button","Set",None, QApplication.UnicodeUTF8))
        getETthermocouplebutton = QPushButton(QApplication.translate("Button","Read",None, QApplication.UnicodeUTF8))
        getBTthermocouplebutton = QPushButton(QApplication.translate("Button","Read",None, QApplication.UnicodeUTF8))
        setETthermocouplebutton.setMaximumWidth(80)
        getETthermocouplebutton.setMaximumWidth(80)
        setBTthermocouplebutton.setMaximumWidth(80)
        getBTthermocouplebutton.setMaximumWidth(80)
        self.connect(setETthermocouplebutton, SIGNAL("clicked()"), lambda PID="ET": self.setthermocoupletype(PID))
        self.connect(setBTthermocouplebutton, SIGNAL("clicked()"), lambda PID="BT": self.setthermocoupletype(PID))        
        self.connect(getETthermocouplebutton, SIGNAL("clicked()"), lambda PID="ET": self.readthermocoupletype(PID))
        self.connect(getBTthermocouplebutton, SIGNAL("clicked()"), lambda PID="BT": self.readthermocoupletype(PID))

        PointButtonET = QPushButton(QApplication.translate("Button","Set ET PID to 1 decimal point",None, QApplication.UnicodeUTF8))
        PointButtonBT = QPushButton(QApplication.translate("Button","Set BT PID to 1 decimal point",None, QApplication.UnicodeUTF8))
        PointButtonET.setMaximumWidth(180)
        PointButtonBT.setMaximumWidth(180)
        pointlabel = QLabel(QApplication.translate("Label","Artisan uses 1 decimal point",None, QApplication.UnicodeUTF8))
        self.connect(PointButtonET, SIGNAL("clicked()"), lambda PID="ET": self.setpoint(PID))
        self.connect(PointButtonBT, SIGNAL("clicked()"), lambda PID="BT": self.setpoint(PID))
        
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
        
        tab4layout = QVBoxLayout()
        tab4layout.addWidget(self.segmenttable)


        #tab5
        thermolayout = QGridLayout()
        thermolayout.addWidget(ETthermolabel,0,0)
        thermolayout.addWidget(self.ETthermocombobox,0,1)
        thermolayout.addWidget(getETthermocouplebutton,0,2)
        thermolayout.addWidget(setETthermocouplebutton,0,3)
        thermolayout.addWidget(BTthermolabel,1,0)
        thermolayout.addWidget(self.BTthermocombobox,1,1)
        thermolayout.addWidget(getBTthermocouplebutton,1,2)
        thermolayout.addWidget(setBTthermocouplebutton,1,3)

        tab5Layout = QVBoxLayout()
        tab5Layout.addStretch()
        tab5Layout.addLayout(thermolayout)
        tab5Layout.addWidget(BTthermolabelnote)
        tab5Layout.addStretch()
        tab5Layout.addWidget(pointlabel)
        tab5Layout.addWidget(PointButtonET)
        tab5Layout.addWidget(PointButtonBT)
        tab5Layout.addStretch()

        ###################################        

        TabWidget = QTabWidget()
        
        C1Widget = QWidget()
        C1Widget.setLayout(buttonMasterLayout)
        TabWidget.addTab(C1Widget,QApplication.translate("Tab","RS",None, QApplication.UnicodeUTF8))
        
        C2Widget = QWidget()
        C2Widget.setLayout(svlayout)
        TabWidget.addTab(C2Widget,QApplication.translate("Tab","SV",None, QApplication.UnicodeUTF8))

        C3Widget = QWidget()
        C3Widget.setLayout(tab3layout)
        TabWidget.addTab(C3Widget,QApplication.translate("Tab","pid",None, QApplication.UnicodeUTF8))

        C4Widget = QWidget()
        C4Widget.setLayout(tab4layout)
        TabWidget.addTab(C4Widget,QApplication.translate("Tab","Set RS",None, QApplication.UnicodeUTF8))        

        C5Widget = QWidget()
        C5Widget.setLayout(tab5Layout)
        TabWidget.addTab(C5Widget,QApplication.translate("Tab","Extra",None, QApplication.UnicodeUTF8))


        #incorporate layouts
        Mlayout = QVBoxLayout()
        Mlayout.addWidget(self.status,0)
        Mlayout.addWidget(TabWidget,1)
        self.setLayout(Mlayout)

    def setpoint(self,PID):
        command = ""
        try:
            if PID == "ET":
                command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["decimalposition"][1],1)
            elif PID == "BT":
                if aw.ser.readBTpid[0] == 0:
                    command = aw.pid.message2send(aw.ser.readBTpid[1],6,aw.pid.PXG4["decimalposition"][1],1)                
                elif aw.ser.readBTpid[0] == 1:
                    command = aw.pid.message2send(aw.ser.readBTpid[1],6,aw.pid.PXR["decimalposition"][1],1)                
            r = aw.ser.sendFUJIcommand(command,8)   
            #check response from pid and update message on main window
            if r == command:                       
                message = QApplication.translate("StatusBar","Decimal position successfully set to 1",None,QApplication.UnicodeUTF8)
                self.status.showMessage(message, 5000)
            else:
                self.status.showMessage(QApplication.translate("StatusBar","Problem setting decimal position",None,QApplication.UnicodeUTF8),5000)
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "setpoint(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))

    def setthermocoupletype(self,PID):
        conversiontoindex = [2,3,4,5,6,7,8,12] #2=J,3=K,4=R,5=B,6=S,7=T,8=E,12=N
        command = ""
        try:
            if PID == "ET":
                index = self.ETthermocombobox.currentIndex()
                value = conversiontoindex[index]
                command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["pvinputtype"][1],value)                
            elif PID == "BT":
                index = self.BTthermocombobox.currentIndex()
                value = conversiontoindex[index]
                if aw.ser.readBTpid[0] == 0:
                    command = aw.pid.message2send(aw.ser.readBTpid[1],6,aw.pid.PXG4["pvinputtype"][1],value)                
                elif aw.ser.readBTpid[0] == 1:
                    command = aw.pid.message2send(aw.ser.readBTpid[1],6,aw.pid.PXR["pvinputtype"][1],value)                
                
            r = aw.ser.sendFUJIcommand(command,8)
            #check response from pid and update message on main window
            if r == command:
                if PID == "ET":   
                    aw.pid.PXG4["pvinputtype"][0] = conversiontoindex[self.ETthermocombobox.currentIndex()]
                elif PID == "BT":
                    pass #this info is not stored
                        
                message = QApplication.translate("StatusBar","Thermocouple type successfully set",None,QApplication.UnicodeUTF8)
                self.status.showMessage(message, 5000)
            else:
                self.status.showMessage(QApplication.translate("StatusBar","Problem setting thermocouple type",None,QApplication.UnicodeUTF8),5000)
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "setthermocoupletype(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))

    def readthermocoupletype(self,PID):
        conversiontoindex = [2,3,4,5,6,7,8,12] #2=J,3=K,4=R,5=B,6=S,7=T,8=E,12=N
        command = ""
        try:
            if PID == "ET":
                command = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXR["pvinputtype"][1],1)
            elif PID == "BT":
                if aw.ser.readBTpid[0] == 0:
                    command = aw.pid.message2send(aw.ser.readBTpid[1],3,aw.pid.PXG4["pvinputtype"][1],1)
                elif aw.ser.readBTpid[0] == 1:
                    command = aw.pid.message2send(aw.ser.readBTpid[1],3,aw.pid.PXR["pvinputtype"][1],1)
            if command:
                Thtype = aw.pid.readoneword(command)
                if Thtype in conversiontoindex:      #0-16 range
                    if PID == "ET":
                        aw.pid.PXR["pvinputtype"][0] = Thtype
                    elif PID == "BT":
                        if aw.ser.readBTpid[0] == 0:
                            aw.pid.PXG4["pvinputtype"][0] = Thtype
                        elif aw.ser.readBTpid[0] == 1:
                            aw.pid.PXR["pvinputtype"][0] = Thtype             
                    self.status.showMessage(self.thermotypes[conversiontoindex.index(Thtype)],5000)       
                else:                    
                    self.status.showMessage(QApplication.translate("StatusBar","Problem reading thermocouple type",None,QApplication.UnicodeUTF8),5000)
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "readthermocoupletype(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            

    def paintlabels(self):
        
        str1 = u"T = " + unicode(aw.pid.PXR["segment1sv"][0]) + u"\nRamp = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment1ramp"][0])) + u"\nSoak = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment1soak"][0]))
        str2 = u"T = " + unicode(aw.pid.PXR["segment2sv"][0]) + u"\nRamp = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment2ramp"][0])) + u"\nSoak = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment2soak"][0]))
        str3 = u"T = " + unicode(aw.pid.PXR["segment3sv"][0]) + u"\nRamp = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment3ramp"][0])) + u"\nSoak = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment3soak"][0]))
        str4 = u"T = " + unicode(aw.pid.PXR["segment4sv"][0]) + u"\nRamp = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment4ramp"][0])) + u"\nSoak = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment4soak"][0]))
        str5 = u"T = " + unicode(aw.pid.PXR["segment5sv"][0]) + u"\nRamp = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment5ramp"][0])) + u"\nSoak = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment5soak"][0]))
        str6 = u"T = " + unicode(aw.pid.PXR["segment6sv"][0]) + u"\nRamp = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment6ramp"][0])) + u"\nSoak = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment6soak"][0]))
        str7 = u"T = " + unicode(aw.pid.PXR["segment7sv"][0]) + u"\nRamp = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment7ramp"][0])) + u"\nSoak = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment7soak"][0]))
        str8 = u"T = " + unicode(aw.pid.PXR["segment8sv"][0]) + u"\nRamp = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment8ramp"][0])) + u"\nSoak = " + unicode(aw.qmc.stringfromseconds(aw.pid.PXR["segment8soak"][0]))

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
        self.status.showMessage(QApplication.translate("StatusBar","setting autotune...",None, QApplication.UnicodeUTF8),500)
        command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["autotuning"][1],flag)
        #TX and RX
        r = aw.ser.sendFUJIcommand(command,8)
        if len(r) == 8:
            if flag == 0:
                aw.pid.PXR["autotuning"][0] = 0
                self.status.showMessage(QApplication.translate("StatusBar","Autotune successfully turned OFF",None, QApplication.UnicodeUTF8),5000)
            if flag == 1:
                aw.pid.PXR["autotuning"][0] = 1
                self.status.showMessage(QApplication.translate("StatusBar","Autotune successfully turned ON",None, QApplication.UnicodeUTF8),5000) 
        else:
            mssg = QApplication.translate("StatusBar","setONOFFautotune() problem ",None, QApplication.UnicodeUTF8)
            self.status.showMessage(mssg,5000)
            aw.qmc.adderror(QApplication.translate("Error Message","setONOFFautotune(): bad response",None, QApplication.UnicodeUTF8))
        
    def setONOFFstandby(self,flag):
        #standby ON (pid off) will reset: rampsoak modes/autotuning/self tuning
        #flag = 0 standby OFF, flag = 1 standby ON (pid off)
        self.status.showMessage(QApplication.translate("StatusBar","wait...",None, QApplication.UnicodeUTF8),500)
        command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["runstandby"][1],flag)
        #TX and RX
        r = aw.ser.sendFUJIcommand(command,8)
        if r == command:               
            if flag == 1:
                message = QApplication.translate("StatusBar","PID OFF",None, QApplication.UnicodeUTF8)     #put pid in standby 1 (pid on)
                aw.pid.PXR["runstandby"][0] = 1
            elif flag == 0:
                message = QApplication.translate("StatusBar","PID ON",None, QApplication.UnicodeUTF8)      #put pid in standby 0 (pid off)
                aw.pid.PXR["runstandby"][0] = 0
        else:
            mssg = QApplication.translate("StatusBar","setONOFFstandby(): problem ",None, QApplication.UnicodeUTF8)
            self.status.showMessage(mssg,5000)
            aw.qmc.adderror(mssg)

    def setsv(self):
        if self.svedit.text() != "":
            newSVvalue = int(float(self.svedit.text())*10) #multiply by 10 because of decimal point
            command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["sv0"][1],newSVvalue)
            r = aw.ser.sendFUJIcommand(command,8)
            if r == command:
                message = QApplication.translate("StatusBar"," SV successfully set to %1",None, QApplication.UnicodeUTF8).arg(self.svedit.text())
                aw.pid.PXR["sv0"][0] = float(self.svedit.text())
                self.status.showMessage(message,5000)
                #record command as an Event 
                strcommand = u"SETSV::"+ unicode("%.1f"%(newSVvalue/10.))
                aw.qmc.DeviceEventRecord(strcommand)
            else:
                mssg = QApplication.translate("StatusBar","setsv(): unable to set sv",None, QApplication.UnicodeUTF8)
                self.status.showMessage(mssg,5000)
                aw.qmc.adderror(mssg)                
        else:
            self.status.showMessage(QApplication.translate("StatusBar","Empty SV box",None, QApplication.UnicodeUTF8),5000)

    def getsv(self):
        temp = aw.pid.readcurrentsv()
        if temp != -1:
            aw.pid.PXR["sv0"][0] =  temp
            aw.lcd6.display(aw.pid.PXR["sv0"][0])
            self.readsvedit.setText(unicode(aw.pid.PXR["sv0"][0]))           
        else:
            self.status.showMessage(QApplication.translate("StatusBar","Unable to read SV",None, QApplication.UnicodeUTF8),5000)

            
    def checkrampsoakmode(self):
        msg = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXR["rampsoakmode"][1],1)
        currentmode = aw.pid.readoneword(msg)
        aw.pid.PXR["rampsoakstartend"][0] = currentmode
        if currentmode == 0:
            mode = [u"0",
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8)]
        elif currentmode == 1:
            mode = [u"1",
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8)]
        elif currentmode == 2:
            mode = [u"2",
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8)]
        elif currentmode == 3:
            mode = [u"3",
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8)]
        elif currentmode == 4:
            mode = [u"4",
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8)]
        elif currentmode == 5:
            mode = [u"5",
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8)]
        elif currentmode == 6:
            mode = [u"6",
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8)]
        elif currentmode == 7:
            mode = [u"7",
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8)]
        elif currentmode == 8:
            mode = [u"8",
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8)]
        elif currentmode == 9:
            mode = [u"9",
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8)]
        elif currentmode == 10:
            mode = [u"10",
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8)]
        elif currentmode == 11:
            mode = [u"11",
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8)]
        elif currentmode == 12:
            mode = [u"12",
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8)]
        elif currentmode == 13:
            mode = [u"13",
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8)]
        elif currentmode == 14:
            mode = [u"14",
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None, QApplication.UnicodeUTF8)]
        elif currentmode == 15:
            mode = [u"15",
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None, QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None, QApplication.UnicodeUTF8)]
        else:
            return -1

        string =  QApplication.translate("MessageBox","The rampsoak-mode tells how to start and end the ramp/soak",None, QApplication.UnicodeUTF8) + "\n\n"
        string += QApplication.translate("MessageBox","Your rampsoak mode in this pid is:",None, QApplication.UnicodeUTF8) + "\n\n"
        string += QApplication.translate("MessageBox","Mode = %1",None, QApplication.UnicodeUTF8).arg(mode[0]) + "\n"
        string += QApplication.translate("MessageBox","-----------------------------------------------------------------------",None, QApplication.UnicodeUTF8) + "\n"
        string += QApplication.translate("MessageBox","Start to run from PV value: %1",None, QApplication.UnicodeUTF8).arg(mode[1]) + "\n"
        string += QApplication.translate("MessageBox","End output status at the end of ramp/soak: %1",None, QApplication.UnicodeUTF8).arg(mode[2]) + "\n"
        string += QApplication.translate("MessageBox","Output status while ramp/soak opearion set to OFF: %1",None, QApplication.UnicodeUTF8).arg(mode[3]) + "\n"
        string += QApplication.translate("MessageBox","\nRepeat Operation at the end: %1",None, QApplication.UnicodeUTF8).arg(mode[4]) + "\n"
        string += QApplication.translate("MessageBox","-----------------------------------------------------------------------",None, QApplication.UnicodeUTF8) + "\n\n"
        string += QApplication.translate("MessageBox","Recomended Mode = 0",None, QApplication.UnicodeUTF8) + "\n\n"
        string += QApplication.translate("MessageBox","If you need to change it, change it now and come back later",None, QApplication.UnicodeUTF8) + "\n"
        string += QApplication.translate("MessageBox","Use the Parameter Loader Software by Fuji if you need to\n\n",None, QApplication.UnicodeUTF8) + "\n\n\n"
        string += QApplication.translate("MessageBox","Continue?",None, QApplication.UnicodeUTF8)
 

    def setONOFFrampsoak(self,flag):         
        #flag =0 OFF, flag = 1 ON, flag = 2 hold
        
        #set rampsoak pattern ON
        if flag == 1:
            check = self.checkrampsoakmode()
            if check == 0:
                self.status.showMessage(QApplication.translate("StatusBar","Ramp/Soak operation cancelled",None, QApplication.UnicodeUTF8), 5000)
                return
            elif check == -1:
                self.status.showMessage(QApplication.translate("StatusBar","No RX data",None, QApplication.UnicodeUTF8), 5000)
                
            self.status.showMessage(QApplication.translate("StatusBar","Setting RS ON...",None, QApplication.UnicodeUTF8),500)
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
                    self.status.showMessage(QApplication.translate("StatusBar","Need to change pattern mode...",None, QApplication.UnicodeUTF8),1000)
                    command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["rampsoakpattern"][1],selectedmode)
                    r = aw.ser.sendFUJIcommand(command,8)
                    if len(r) == 8:
                        self.status.showMessage(QApplication.translate("StatusBar","Pattern has been changed. Wait 5 secs.",None, QApplication.UnicodeUTF8), 500)
                        aw.pid.PXR["rampsoakpattern"][0] = selectedmode
                    else:
                        self.status.showMessage(QApplication.translate("StatusBar","Pattern could not be changed",None, QApplication.UnicodeUTF8), 5000)
                        return
                #combobox mode matches pid mode
                #set ramp soak mode ON
                command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["rampsoak"][1],flag)
                r = aw.ser.sendFUJIcommand(command,8)
                if r == command:
                    #record command as an Event if flag = 1
                    if flag == 1:
                        self.status.showMessage(QApplication.translate("StatusBar","RS ON and running...",None, QApplication.UnicodeUTF8), 5000)
                        #ramp soak pattern. 0=executes 1 to 4; 1=executes 5 to 8; 2=executes 1 to 8
                        pattern =[[1,4],[5,8],[1,8]]
                        start = pattern[aw.pid.PXR["rampsoakpattern"][0]][0]
                        end = pattern[aw.pid.PXR["rampsoakpattern"][0]][1]+1
                        strcommand = u"SETRS"
                        result = u""
                        for i in range(start,end):
                            svkey = u"segment"+str(i)+"sv"
                            rampkey = u"segment"+str(i)+"ramp"
                            soakkey = u"segment"+str(i)+"soak"
                            strcommand += u"::" + unicode(aw.pid.PXR[svkey][0]) + u"::" + unicode(aw.pid.PXR[rampkey][0]) + u"::" + unicode(aw.pid.PXR[soakkey][0])+u"::"
                            result += strcommand
                            strcommand = u"SETRS"
                        result = result.strip(u"::")
                        aw.qmc.DeviceEventRecord(result)
                    elif fag == 0:
                        self.status.showMessage(QApplication.translate("StatusBar","RS turned OFF",None, QApplication.UnicodeUTF8), 5000)
                    elif fag == 2:
                        self.status.showMessage(QApplication.translate("StatusBar","RS on HOLD mode",None, QApplication.UnicodeUTF8), 5000)
                else:
                    self.status.showMessage(QApplication.translate("StatusBar","RampSoak could not be changed",None, QApplication.UnicodeUTF8), 5000)
            else:
                mssg = QApplication.translate("StatusBar","setONOFFrampsoak(): problem ",None, QApplication.UnicodeUTF8)
                self.status.showMessage(mssg,5000)
                aw.qmc.adderror(mssg)
                  
        #set ramp soak OFF       
        elif flag == 0:
            self.status.showMessage(QApplication.translate("StatusBar","setting RS OFF...",None, QApplication.UnicodeUTF8),500)
            command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["rampsoak"][1],flag)
            r = aw.ser.sendFUJIcommand(command,8)
            if r == command:
                self.status.showMessage(QApplication.translate("StatusBar","RS successfully turned OFF",None, QApplication.UnicodeUTF8), 5000)
                aw.pid.PXR["rampsoak"][0] = flag
            else:
                mssg = QApplication.translate("StatusBar","setONOFFrampsoak(): Ramp Soak could not be set OFF",None, QApplication.UnicodeUTF8)
                self.status.showMessage(mssg,5000)
                aw.qmc.adderror(mssg)

    def getsegment(self, idn):
        svkey = u"segment" + unicode(idn) + u"sv"
        svcommand = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXR[svkey][1],1)
        sv = aw.pid.readoneword(svcommand)
        if sv == -1:
            mssg = QApplication.translate("StatusBar","getsegment(): problem reading sv ",None, QApplication.UnicodeUTF8)
            self.status.showMessage(mssg,5000)
            aw.qmc.adderror(mssg)
            return -1
        aw.pid.PXR[svkey][0] = sv/10.              #divide by 10 because the decimal point is not sent by the PID

        rampkey = u"segment" +unicode(idn) + u"ramp"
        rampcommand = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXR[rampkey][1],1)
        ramp = aw.pid.readoneword(rampcommand)
        if ramp == -1:
            mssg = QApplication.translate("StatusBar","getsegment(): problem reading ramp ",None, QApplication.UnicodeUTF8)
            self.status.showMessage(mssg,5000)
            aw.qmc.adderror(mssg)
            return -1
        aw.pid.PXR[rampkey][0] = ramp/10.
        
        soakkey = u"segment" + unicode(idn) + u"soak"
        soakcommand = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXR[soakkey][1],1)
        soak = aw.pid.readoneword(soakcommand)
        if soak == -1:
            mssg = QApplication.translate("StatusBar","getsegment(): problem reading soak ",None, QApplication.UnicodeUTF8)
            self.status.showMessage(mssg,5000)
            aw.qmc.adderror(mssg)
            return -1
            return -1
        aw.pid.PXR[soakkey][0] = soak/10.


    #get all Ramp Soak values for all 8 segments                                  
    def getallsegments(self):
        for i in range(8):
            msg = u"Reading Ramp/Soak #" + unicode(i+1)
            self.status.showMessage(msg,500)
            k = self.getsegment(i+1)
            if k == -1:
                mssg = QApplication.translate("StatusBar","getallsegments(): problem reading R/S ",None, QApplication.UnicodeUTF8)
                self.status.showMessage(mssg,5000)
                aw.qmc.adderror(mssg)
                return
            self.paintlabels()
            
        self.status.showMessage(QApplication.translate("StatusBar","Finished reading Ramp/Soak val.",None, QApplication.UnicodeUTF8),5000)
        
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
            
        self.status.showMessage(QApplication.translate("StatusBar","Finished reading pid values",None, QApplication.UnicodeUTF8),5000)
        

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
            message = QApplication.translate("StatusBar","%1 successfully send to pid ",None, QApplication.UnicodeUTF8).arg(var)
            self.status.showMessage(message,5000)
            if var == u"p":
                aw.pid.PXR["p"][0] = p
            elif var == u"i":
                aw.pid.PXR["i"][0] = i
            elif var == u"d":
                aw.pid.PXR["i"][0] = d
            
        else:
            mssg = QApplication.translate("StatusBar","setpid(): There was a problem setting %1",None, QApplication.UnicodeUTF8).arg(var) 
            self.status.showMessage(mssg,5000)        
            aw.qmc.adderror(mssg)

    def createsegmenttable(self):
        self.segmenttable.setRowCount(8)
        self.segmenttable.setColumnCount(4)
        self.segmenttable.setHorizontalHeaderLabels([QApplication.translate("Table","SV",None, QApplication.UnicodeUTF8),
                                                     QApplication.translate("Table","Ramp HH:MM",None, QApplication.UnicodeUTF8),
                                                     QApplication.translate("Table","Soak HH:MM",None, QApplication.UnicodeUTF8),""])
        self.segmenttable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.segmenttable.setSelectionBehavior(QTableWidget.SelectRows)
        self.segmenttable.setSelectionMode(QTableWidget.SingleSelection)
        self.segmenttable.setShowGrid(True)
        regextime = QRegExp(r"^-?[0-5][0-9]:[0-5][0-9]$")                
            
        #populate table
        for i in range(8):
            #create widgets
            svkey = u"segment" + unicode(i+1) + u"sv"
            rampkey = u"segment" + unicode(i+1) + u"ramp"
            soakkey = u"segment" + unicode(i+1) + u"soak"
            
            svedit = QLineEdit(unicode(aw.pid.PXR[svkey][0]))
            svedit.setValidator(QDoubleValidator(0., 999., 1, svedit))
            rampedit = QLineEdit(unicode(aw.qmc.stringfromseconds(aw.pid.PXR[rampkey][0])))
            rampedit.setValidator(QRegExpValidator(regextime,self))
            soakedit  = QLineEdit(unicode(aw.qmc.stringfromseconds(aw.pid.PXR[soakkey][0])))
            soakedit.setValidator(QRegExpValidator(regextime,self))
            setButton = QPushButton(QApplication.translate("Button","Set",None, QApplication.UnicodeUTF8))
            self.connect(setButton,SIGNAL("clicked()"),lambda idn =i:self.setsegment(i))
            #add widgets to the table
            self.segmenttable.setCellWidget(i,0,svedit)
            self.segmenttable.setCellWidget(i,1,rampedit)
            self.segmenttable.setCellWidget(i,2,soakedit)
            self.segmenttable.setCellWidget(i,3,setButton)


    #idn = id number, sv = float set value, ramp = ramp value, soak = soak value
    def setsegment(self,i):
        idn = i+1
        svedit =  self.segmenttable.cellWidget(i,0)
        rampedit = self.segmenttable.cellWidget(i,1)
        soakedit = self.segmenttable.cellWidget(i,2)

        sv = float(svedit.text())
        ramp = aw.qmc.stringtoseconds(unicode(rampedit.text()))
        soak = aw.qmc.stringtoseconds(unicode(soakedit.text())) 

        svkey = u"segment" + unicode(idn) + u"sv"
        svcommand = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR[svkey][1],int(sv*10))
        r1 = aw.ser.sendFUJIcommand(svcommand,8)

        libtime.sleep(0.1) #important time between writings
        
        rampkey = u"segment" + unicode(idn) + u"ramp"
        rampcommand = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR[rampkey][1],ramp)
        r2 = aw.ser.sendFUJIcommand(rampcommand,8)

        libtime.sleep(0.1) #important time between writings
 
        soakkey = u"segment" + unicode(idn) + u"soak"
        soakcommand = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR[soakkey][1],soak)
        r3 = aw.ser.sendFUJIcommand(soakcommand,8)
    
        #check if OK
        if len(r1) == 8 and len(r2) == 8 and len(r3) == 8:
            aw.pid.PXR[svkey][0] = sv
            aw.pid.PXR[rampkey][0] = ramp
            aw.pid.PXR[soakkey][0] = soak
            self.paintlabels()
            self.status.showMessage(QApplication.translate("StatusBar","Ramp/Soak successfully writen",None, QApplication.UnicodeUTF8),5000) 
        else:
            aw.qmc.adderror(QApplication.translate("Error Message","Segment values could not be writen into PID",None, QApplication.UnicodeUTF8))

        
############################################################################
######################## FUJI PXG4 PID CONTROL DIALOG ######################
############################################################################
    
class PXG4pidDlgControl(QDialog):
    def __init__(self, parent = None):
        super(PXG4pidDlgControl,self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.setWindowTitle(QApplication.translate("Form Caption","Fuji PXG PID Control",None, QApplication.UnicodeUTF8))

        self.status = QStatusBar()
        self.status.setSizeGripEnabled(False)
        self.status.showMessage(QApplication.translate("StatusBar","Ready",None, QApplication.UnicodeUTF8),5000)

        #*************    TAB 1 WIDGETS
        labelrs1 = QLabel()
        labelrs1.setMargin(5)
        labelrs1.setStyleSheet("background-color:'#CCCCCC';")
        labelrs1.setText("<font color='white'><b>" + QApplication.translate("Label", "Ramp Soak (MM:SS)<br>(1-7)",None, QApplication.UnicodeUTF8) + "<\b></font>")
        #labelrs1.setMaximumSize(90, 42)
        #labelrs1.setMinimumHeight(50)

        labelrs2 = QLabel()
        labelrs2.setMargin(5)
        labelrs2.setStyleSheet("background-color:'#CCCCCC';")
        labelrs2.setText("<font color='white'><b>" + QApplication.translate("Label", "Ramp Soak (MM:SS)<br>(8-16)",None, QApplication.UnicodeUTF8) + "<\b></font>")
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
       
        self.patternComboBox =  QComboBox()
        self.patternComboBox.addItems(["1-4","5-8","1-8","9-12","13-16","9-16","1-16"])
        self.patternComboBox.setCurrentIndex(aw.pid.PXG4["rampsoakpattern"][0])
        self.connect(self.patternComboBox,SIGNAL("currentIndexChanged(int)"),self.paintlabels)
        
        self.paintlabels()

        patternlabel = QLabel(QApplication.translate("Label","Pattern",None, QApplication.UnicodeUTF8))
        patternlabel.setAlignment(Qt.AlignRight)
        button_getall = QPushButton(QApplication.translate("Button","Read RS values",None, QApplication.UnicodeUTF8))
        button_rson =  QPushButton(QApplication.translate("Button","RampSoak ON",None, QApplication.UnicodeUTF8))        
        button_rsoff =  QPushButton(QApplication.translate("Button","RampSoak OFF",None, QApplication.UnicodeUTF8))
        button_exit = QPushButton(QApplication.translate("Button","Close",None, QApplication.UnicodeUTF8))
        button_exit2 = QPushButton(QApplication.translate("Button","Close",None, QApplication.UnicodeUTF8))
        button_standbyON = QPushButton(QApplication.translate("Button","PID OFF",None, QApplication.UnicodeUTF8))
        button_standbyOFF = QPushButton(QApplication.translate("Button","PID ON",None, QApplication.UnicodeUTF8))
        
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
        labelsv.setText("<font color='white'><b>" + QApplication.translate("Label", "SV (7-0)",None, QApplication.UnicodeUTF8) + "<\b></font>")
        labelsv.setMaximumSize(100, 42)
        labelsv.setMinimumHeight(50)
        
        labelsvedit = QLabel()
        labelsvedit.setMargin(10)
        labelsvedit.setStyleSheet("background-color:'#CCCCCC';")
        labelsvedit.setText("<font color='white'><b>" + QApplication.translate("Label", "Write",None, QApplication.UnicodeUTF8) + "<\b></font>")
        labelsvedit.setMaximumSize(100, 42)
        labelsvedit.setMinimumHeight(50)
        
        button_sv1 =QPushButton(QApplication.translate("Button","Write SV1",None, QApplication.UnicodeUTF8))
        button_sv2 =QPushButton(QApplication.translate("Button","Write SV2",None, QApplication.UnicodeUTF8))
        button_sv3 =QPushButton(QApplication.translate("Button","Write SV3",None, QApplication.UnicodeUTF8))
        button_sv4 =QPushButton(QApplication.translate("Button","Write SV4",None, QApplication.UnicodeUTF8))
        button_sv5 =QPushButton(QApplication.translate("Button","Write SV5",None, QApplication.UnicodeUTF8))
        button_sv6 =QPushButton(QApplication.translate("Button","Write SV6",None, QApplication.UnicodeUTF8))
        button_sv7 =QPushButton(QApplication.translate("Button","Write SV7",None, QApplication.UnicodeUTF8))

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

        tab2svbutton = QPushButton(QApplication.translate("Button","Write SV",None, QApplication.UnicodeUTF8))
        tab2cancelbutton = QPushButton(QApplication.translate("Button","Cancel",None, QApplication.UnicodeUTF8))
        tab2easyONsvbutton = QPushButton(QApplication.translate("Button","ON SV buttons",None, QApplication.UnicodeUTF8))
        tab2easyONsvbutton.setStyleSheet("QPushButton { background-color: 'lightblue'}")
        tab2easyOFFsvbutton = QPushButton(QApplication.translate("Button","OFF SV buttons",None, QApplication.UnicodeUTF8))
        tab2easyOFFsvbutton.setStyleSheet("QPushButton { background-color:'#ffaaff' }")
        tab2getsvbutton = QPushButton(QApplication.translate("Button","Read SV (7-0)",None, QApplication.UnicodeUTF8))
        
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

        #****************   TAB 3 WIDGETS
        plabel = QLabel()
        plabel.setMargin(10)
        plabel.setStyleSheet("background-color:'#CCCCCC';")
        plabel.setText("<font color='white'><b>" + QApplication.translate("Label", "P",None, QApplication.UnicodeUTF8) + "<\b></font>")
        plabel.setMaximumSize(50, 42)
        plabel.setMinimumHeight(50)

        ilabel = QLabel()
        ilabel.setMargin(10)
        ilabel.setStyleSheet("background-color:'#CCCCCC';")
        ilabel.setText("<font color='white'><b>" + QApplication.translate("Label", "I",None, QApplication.UnicodeUTF8) + "<\b></font>")
        ilabel.setMaximumSize(50, 42)
        ilabel.setMinimumHeight(50)
        
        dlabel = QLabel()
        dlabel.setMargin(10)
        dlabel.setStyleSheet("background-color:'#CCCCCC';")
        dlabel.setText("<font color='white'><b>" + QApplication.translate("Label", "D",None, QApplication.UnicodeUTF8) + "<\b></font>")
        dlabel.setMaximumSize(50, 42)
        dlabel.setMinimumHeight(50)

        wlabel = QLabel()
        wlabel.setMargin(10)
        wlabel.setStyleSheet("background-color:'#CCCCCC';")
        wlabel.setText("<font color='white'><b>" + QApplication.translate("Label", "Write",None, QApplication.UnicodeUTF8) + "<\b></font>")
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
        
        pid1button = QPushButton(QApplication.translate("Button","pid 1",None, QApplication.UnicodeUTF8))
        pid2button = QPushButton(QApplication.translate("Button","pid 2",None, QApplication.UnicodeUTF8))
        pid3button = QPushButton(QApplication.translate("Button","pid 3",None, QApplication.UnicodeUTF8))
        pid4button = QPushButton(QApplication.translate("Button","pid 4",None, QApplication.UnicodeUTF8))
        pid5button = QPushButton(QApplication.translate("Button","pid 5",None, QApplication.UnicodeUTF8))
        pid6button = QPushButton(QApplication.translate("Button","pid 6",None, QApplication.UnicodeUTF8))
        pid7button = QPushButton(QApplication.translate("Button","pid 7",None, QApplication.UnicodeUTF8))
        pidreadallbutton = QPushButton(QApplication.translate("Button","Read All",None, QApplication.UnicodeUTF8))
        autotuneONbutton = QPushButton(QApplication.translate("Button","Auto Tune ON",None, QApplication.UnicodeUTF8))
        autotuneOFFbutton = QPushButton(QApplication.translate("Button","Auto Tune OFF",None, QApplication.UnicodeUTF8))
        cancel3button = QPushButton(QApplication.translate("Button","Cancel",None, QApplication.UnicodeUTF8))
        
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

        #****************************   TAB4 WIDGETS
        #table for setting segments
        self.segmenttable = QTableWidget()
        self.createsegmenttable()

        #****************************   TAB5 WIDGETS
        ETthermolabel = QLabel(QApplication.translate("Label","ET Thermocouple type",None, QApplication.UnicodeUTF8))
        BTthermolabel = QLabel(QApplication.translate("Label","BT Thermocouple type",None, QApplication.UnicodeUTF8))
        BTthermolabelnote = QLabel(QApplication.translate("Label","NOTE: BT Thermocouple type is not stored in the Artisan seetings",None, QApplication.UnicodeUTF8))
        self.ETthermocombobox = QComboBox()
        self.BTthermocombobox = QComboBox()
        self.thermotypes = ["J","K","R","B","S","T","E","N"]
        conversiontoindex = [2,3,4,5,6,7,8,12]  #converts fuji PID types to indexes
        self.ETthermocombobox.addItems(self.thermotypes)
        self.BTthermocombobox.addItems(self.thermotypes)
        self.ETthermocombobox.setCurrentIndex(conversiontoindex.index(aw.pid.PXG4["pvinputtype"][0]))
        setETthermocouplebutton = QPushButton(QApplication.translate("Button","Set",None, QApplication.UnicodeUTF8))
        setBTthermocouplebutton = QPushButton(QApplication.translate("Button","Set",None, QApplication.UnicodeUTF8))
        getETthermocouplebutton = QPushButton(QApplication.translate("Button","Read",None, QApplication.UnicodeUTF8))
        getBTthermocouplebutton = QPushButton(QApplication.translate("Button","Read",None, QApplication.UnicodeUTF8))
        setETthermocouplebutton.setMaximumWidth(80)
        getETthermocouplebutton.setMaximumWidth(80)
        setBTthermocouplebutton.setMaximumWidth(80)
        getBTthermocouplebutton.setMaximumWidth(80)
        self.connect(setETthermocouplebutton, SIGNAL("clicked()"), lambda PID="ET": self.setthermocoupletype(PID))
        self.connect(setBTthermocouplebutton, SIGNAL("clicked()"), lambda PID="BT": self.setthermocoupletype(PID))        
        self.connect(getETthermocouplebutton, SIGNAL("clicked()"), lambda PID="ET": self.readthermocoupletype(PID))
        self.connect(getBTthermocouplebutton, SIGNAL("clicked()"), lambda PID="BT": self.readthermocoupletype(PID))


        PointButtonET = QPushButton(QApplication.translate("Button","Set ET PID to 1 decimal point",None, QApplication.UnicodeUTF8))
        PointButtonBT = QPushButton(QApplication.translate("Button","Set BT PID to 1 decimal point",None, QApplication.UnicodeUTF8))
        timeunitsbutton = QPushButton(QApplication.translate("Button","Set ET PID to MM:SS time units",None, QApplication.UnicodeUTF8))
        PointButtonET.setMaximumWidth(180)
        PointButtonBT.setMaximumWidth(180)
        timeunitsbutton.setMaximumWidth(180)
        pointlabel = QLabel(QApplication.translate("Label","Artisan uses 1 decimal point",None, QApplication.UnicodeUTF8))
        timelabel = QLabel(QApplication.translate("Label","Artisan Fuji PXG uses MINUTES:SECONDS units in Ramp/Soaks",None, QApplication.UnicodeUTF8))
        self.connect(PointButtonET, SIGNAL("clicked()"), lambda PID="ET": self.setpoint(PID))
        self.connect(PointButtonBT, SIGNAL("clicked()"), lambda PID="BT": self.setpoint(PID))
        self.connect(timeunitsbutton, SIGNAL("clicked()"), self.settimeunits)

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

        tab4layout = QVBoxLayout()
        tab4layout.addWidget(self.segmenttable)

        #tab5
        thermolayout = QGridLayout()
        thermolayout.addWidget(ETthermolabel,0,0)
        thermolayout.addWidget(self.ETthermocombobox,0,1)
        thermolayout.addWidget(getETthermocouplebutton,0,2)
        thermolayout.addWidget(setETthermocouplebutton,0,3)
        thermolayout.addWidget(BTthermolabel,1,0)
        thermolayout.addWidget(self.BTthermocombobox,1,1)
        thermolayout.addWidget(getBTthermocouplebutton,1,2)
        thermolayout.addWidget(setBTthermocouplebutton,1,3)

        tab5Layout = QVBoxLayout()
        tab5Layout.addStretch()
        tab5Layout.addLayout(thermolayout)
        tab5Layout.addWidget(BTthermolabelnote)
        tab5Layout.addStretch()
        tab5Layout.addWidget(pointlabel)
        tab5Layout.addWidget(PointButtonET)
        tab5Layout.addWidget(PointButtonBT)
        tab5Layout.addStretch()
        tab5Layout.addWidget(timelabel)
        tab5Layout.addWidget(timeunitsbutton)
        tab5Layout.addStretch()

                
        ############################
        TabWidget = QTabWidget()
        
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        TabWidget.addTab(C1Widget,QApplication.translate("Tab","RS",None, QApplication.UnicodeUTF8))
        
        C2Widget = QWidget()
        C2Widget.setLayout(tab2Layout)
        TabWidget.addTab(C2Widget,QApplication.translate("Tab","SV",None, QApplication.UnicodeUTF8))

        C3Widget = QWidget()
        C3Widget.setLayout(tab3MasterLayout)
        TabWidget.addTab(C3Widget,QApplication.translate("Tab","PID",None, QApplication.UnicodeUTF8))

        C4Widget = QWidget()
        C4Widget.setLayout(tab4layout)
        TabWidget.addTab(C4Widget,QApplication.translate("Tab","Set RS",None, QApplication.UnicodeUTF8))

        C5Widget = QWidget()
        C5Widget.setLayout(tab5Layout)
        TabWidget.addTab(C5Widget,QApplication.translate("Tab","Extra",None, QApplication.UnicodeUTF8))
        
        #incorporate layouts
        layout = QVBoxLayout()
        layout.addWidget(self.status,0)
        layout.addWidget(TabWidget,1)
        self.setLayout(layout)


    def settimeunits(self):
        try:
            command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["timeunits"][1],1)
            r = aw.ser.sendFUJIcommand(command,8)   
            #check response from pid and update message on main window
            if r == command:                       
                message = QApplication.translate("StatusBar","Time Units successfully set to MM:SS",None,QApplication.UnicodeUTF8)
                self.status.showMessage(message, 5000)
            else:
                self.status.showMessage(QApplication.translate("StatusBar","Problem setting time units",None,QApplication.UnicodeUTF8),5000)    
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "settimeunits(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))

    def setpoint(self,PID):
        command = ""
        try:
            if PID == "ET":
                command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["decimalposition"][1],1)
            elif PID == "BT":
                if aw.ser.readBTpid[0] == 0:
                    command = aw.pid.message2send(aw.ser.readBTpid[1],6,aw.pid.PXG4["decimalposition"][1],1)                
                elif aw.ser.readBTpid[0] == 1:
                    command = aw.pid.message2send(aw.ser.readBTpid[1],6,aw.pid.PXR["decimalposition"][1],1)                
            r = aw.ser.sendFUJIcommand(command,8)   
            #check response from pid and update message on main window
            if r == command:                       
                message = QApplication.translate("StatusBar","Decimal position successfully set to 1",None,QApplication.UnicodeUTF8)
                self.status.showMessage(message, 5000)
            else:
                self.status.showMessage(QApplication.translate("StatusBar","Problem setting decimal position",None,QApplication.UnicodeUTF8),5000)
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "setpoint(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))

    def setthermocoupletype(self,PID):
        conversiontoindex = [2,3,4,5,6,7,8,12] #2=J,3=K,4=R,5=B,6=S,7=T,8=E,12=N
        command = ""
        try:
            if PID == "ET":
                index = self.ETthermocombobox.currentIndex()
                value = conversiontoindex[index]
                command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["pvinputtype"][1],value)                
            elif PID == "BT":
                index = self.BTthermocombobox.currentIndex()
                value = conversiontoindex[index]
                if aw.ser.readBTpid[0] == 0:
                    command = aw.pid.message2send(aw.ser.readBTpid[1],6,aw.pid.PXG4["pvinputtype"][1],value)                
                elif aw.ser.readBTpid[0] == 1:
                    command = aw.pid.message2send(aw.ser.readBTpid[1],6,aw.pid.PXR["pvinputtype"][1],value)                
                
            r = aw.ser.sendFUJIcommand(command,8)
            #check response from pid and update message on main window
            if r == command:
                if PID == "ET":   
                    aw.pid.PXG4["pvinputtype"][0] = conversiontoindex[self.ETthermocombobox.currentIndex()]
                elif PID == "BT":
                    pass #this info is not stored
                        
                message = QApplication.translate("StatusBar","Thermocouple type successfully set",None,QApplication.UnicodeUTF8)
                self.status.showMessage(message, 5000)
            else:
                self.status.showMessage(QApplication.translate("StatusBar","Problem setting thermocouple type",None,QApplication.UnicodeUTF8),5000)
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "setthermocoupletype(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))

    def readthermocoupletype(self,PID):
        conversiontoindex = [2,3,4,5,6,7,8,12] #2=J,3=K,4=R,5=B,6=S,7=T,8=E,12=N
        command = ""
        try:
            if PID == "ET":
                command = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4["pvinputtype"][1],1)
            elif PID == "BT":
                if aw.ser.readBTpid[0] == 0:
                    command = aw.pid.message2send(aw.ser.readBTpid[1],3,aw.pid.PXG4["pvinputtype"][1],1)
                elif aw.ser.readBTpid[0] == 1:
                    command = aw.pid.message2send(aw.ser.readBTpid[1],3,aw.pid.PXR["pvinputtype"][1],1)  
            if command:
                Thtype = aw.pid.readoneword(command)
                if Thtype in conversiontoindex:      #0-16 range
                    if PID == "ET":
                        aw.pid.PXG4["pvinputtype"][0] = Thtype
                        self.ETthermocombobox.setCurrentIndex(conversiontoindex.index(Thtype))
                    elif PID == "BT":
                        if aw.ser.readBTpid[0] == 0:
                            aw.pid.PXG4["pvinputtype"][0] = Thtype
                        elif aw.ser.readBTpid[0] == 1:
                            aw.pid.PXR["pvinputtype"][0] = Thtype
                        self.BTthermocombobox.setCurrentIndex(conversiontoindex.index(Thtype))
                    self.status.showMessage(self.thermotypes[conversiontoindex.index(Thtype)],5000)       
                else:                    
                    self.status.showMessage(QApplication.translate("StatusBar","Problem reading thermocouple type",None,QApplication.UnicodeUTF8),5000)
        except Exception,e:
            aw.qmc.adderror(QApplication.translate("Error Message", "readthermocoupletype(): %1 ",None, QApplication.UnicodeUTF8).arg(unicode(e)))
            
        
    def paintlabels(self):
        #read values of computer variables (not the actual pid values) to place in buttons
        str1 = QApplication.translate("Label","1 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment1sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment1ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment1soak"][0])))
        str2 = QApplication.translate("Label","2 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment2sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment2ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment2soak"][0])))
        str3 = QApplication.translate("Label","3 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment3sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment3ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment3soak"][0])))
        str4 = QApplication.translate("Label","4 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment4sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment4ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment4soak"][0])))
        str5 = QApplication.translate("Label","5 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment5sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment5ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment5soak"][0])))
        str6 = QApplication.translate("Label","6 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment6sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment6ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment6soak"][0])))
        str7 = QApplication.translate("Label","7 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment7sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment7ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment7soak"][0])))
        str8 = QApplication.translate("Label","8 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment8sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment8ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment8soak"][0])))
        str9 = QApplication.translate("Label","9 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment9sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment9ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment9soak"][0])))
        str10 = QApplication.translate("Label","10 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment10sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment10ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment10soak"][0])))
        str11 = QApplication.translate("Label","11 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment11sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment11ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment11soak"][0])))
        str12 = QApplication.translate("Label","12 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment12sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment12ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment12soak"][0])))
        str13 = QApplication.translate("Label","13 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment13sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment13ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment13soak"][0])))
        str14 = QApplication.translate("Label","14 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment14sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment14ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment14soak"][0])))
        str15 = QApplication.translate("Label","15 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment15sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment15ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment15soak"][0])))
        str16 = QApplication.translate("Label","16 [T %1] [R %2] [S %3]",None,QApplication.UnicodeUTF8).arg(unicode(aw.pid.PXG4["segment16sv"][0])).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment16ramp"][0]))).arg(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4["segment16soak"][0])))

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
                string = QApplication.translate("MessageBox","Current sv = %1. Change now to sv = %2?",None,QApplication.UnicodeUTF8).arg(unicode(N)).arg(unicode(svn))
                reply = QMessageBox.question(self,QApplication.translate("MessageBox Caption","Change svN",None,QApplication.UnicodeUTF8),string,
                                    QMessageBox.Yes|QMessageBox.Cancel)
                if reply == QMessageBox.Yes:
                    #change variable svN
                    command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["selectsv"][1],svn)
                    r = aw.ser.sendFUJIcommand(command,8)
                    
                    #check response from pid and update message on main window
                    if r == command:
                        aw.pid.PXG4["selectsv"][0] = svn
                        key = u"sv" + unicode(svn)
                        message = QApplication.translate("StatusBar","SV%1 set to %2",None,QApplication.UnicodeUTF8).arg(unicode(svn)).arg(unicode(aw.pid.PXG4[key][0]))
                        aw.lcd6.display(unicode(aw.pid.PXG4[key][0]))
                        self.status.showMessage(message, 5000)
                    else:
                        self.status.showMessage(QApplication.translate("StatusBar","Problem setting SV",None,QApplication.UnicodeUTF8),5000)
                elif reply == QMessageBox.Cancel:
                    self.status.showMessage(QApplication.translate("StatusBar","Cancelled svN change",None,QApplication.UnicodeUTF8),5000)
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
                mssg = QApplication.translate("StatusBar","PID already using sv%1",None,QApplication.UnicodeUTF8).arg(unicode(N))
                self.status.showMessage(mssg,1000)
        else:
            mssg = QApplication.translate("StatusBar","setNsv(): bad response",None,QApplication.UnicodeUTF8)
            self.status.showMessage(mssg,1000)
            aw.qmc.adderror(mssg)

        
    #selects an sv   
    def setNpid(self,pidn):
        # read current sv N
        command = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4["selectedpid"][1],1)
        N = aw.pid.readoneword(command)
        if N != -1:
            aw.pid.PXG4["selectedpid"][0] = N
            # if current svN is different than requested svN
            if N != pidn:
                string = QApplication.translate("MessageBox","Current pid = %1. Change now to pid =%2?",None,QApplication.UnicodeUTF8).arg(unicode(N)).arg(unicode(pidn))
                reply = QMessageBox.question(self,QApplication.translate("MessageBox Caption","Change svN",None,QApplication.UnicodeUTF8),string,
                                    QMessageBox.Yes|QMessageBox.Cancel)
                if reply == QMessageBox.Yes:
                    #change variable svN
                    command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["selectedpid"][1],pidn)
                    r = aw.ser.sendFUJIcommand(command,8)
                    
                    #check response from pid and update message on main window
                    if r == command:
                        aw.pid.PXG4["selectedpid"][0] = pidn
                        key = u"sv" + unicode(pidn)
                        message = QApplication.translate("StatusBar","pid%1 changed to %2",None,QApplication.UnicodeUTF8).arg(unicode(pidn)).arg(unicode(aw.pid.PXG4[key][0]))
                        self.status.showMessage(message, 5000)
                    else:
                        mssg = QApplication.translate("StatusBar","setNpid(): bad confirmation",None,QApplication.UnicodeUTF8)
                        self.status.showMessage(mssg,1000)
                        aw.qmc.adderror(mssg)
                        
                elif reply == QMessageBox.Cancel:
                    self.status.showMessage(QApplication.translate("StatusBar","Cancelled pid change",None,QApplication.UnicodeUTF8),5000)
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
                mssg = QApplication.translate("StatusBar","PID was already using pid %1",None,QApplication.UnicodeUTF8).arg(unicode(N))
                self.status.showMessage(mssg,1000)
        else:
            mssg = QApplication.translate("StatusBar","setNpid(): Unable to set pid %1 ",None,QApplication.UnicodeUTF8).arg(unicode(N))
            self.status.showMessage(mssg,1000)
            aw.qmc.adderror(mssg)

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
                 message = QApplication.translate("StatusBar","SV%1 successfully set to %2",None,QApplication.UnicodeUTF8).arg(unicode(i)).arg(unicode(self.sv1edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNsv(1)
                 aw.lcd6.display(unicode(self.sv1edit.text()))
            elif i == 2:
                 aw.pid.PXG4[svkey][0] = float(self.sv2edit.text())
                 message = QApplication.translate("StatusBar","SV%1 successfully set to %2",None,QApplication.UnicodeUTF8).arg(unicode(i)).arg(unicode(self.sv2edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNsv(2)
                 aw.lcd6.display(unicode(self.sv2edit.text()))
            elif i == 3:
                 aw.pid.PXG4[svkey][0] = float(self.sv3edit.text())
                 message = QApplication.translate("StatusBar","SV%1 successfully set to %2",None,QApplication.UnicodeUTF8).arg(unicode(i)).arg(unicode(self.sv3edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNsv(3)
                 aw.lcd6.display(unicode(self.sv3edit.text()))
            elif i == 4:
                 aw.pid.PXG4[svkey][0] = float(self.sv4edit.text())
                 message = QApplication.translate("StatusBar","SV%1 successfully set to %2",None,QApplication.UnicodeUTF8).arg(unicode(i)).arg(unicode(self.sv4edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNsv(4)
                 aw.lcd6.display(unicode(self.sv4edit.text()))
            elif i == 5:
                 aw.pid.PXG4[svkey][0] = float(self.sv5edit.text())
                 message = QApplication.translate("StatusBar","SV%1 successfully set to %2",None,QApplication.UnicodeUTF8).arg(unicode(i)).arg(unicode(self.sv5edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNsv(5)
                 aw.lcd6.display(unicode(self.sv5edit.text()))
            elif i == 6:
                 aw.pid.PXG4[svkey][0] = float(self.sv6edit.text())
                 message = QApplication.translate("StatusBar","SV%1 successfully set to %2",None,QApplication.UnicodeUTF8).arg(unicode(i)).arg(unicode(self.sv6edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNsv(6)
                 aw.lcd6.display(unicode(self.sv6edit.text()))
            elif i == 7:
                 aw.pid.PXG4[svkey][0] = float(self.sv7edit.text())
                 message = QApplication.translate("StatusBar","SV%1 successfully set to %2",None,QApplication.UnicodeUTF8).arg(unicode(i)).arg(unicode(self.sv7edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNsv(7)
                 aw.lcd6.display(unicode(self.sv7edit.text()))

            #record command as an Event 
            strcommand = u"SETSV::" + unicode("%.1f"%(newSVvalue/10.))
            aw.qmc.DeviceEventRecord(strcommand)

        else:
            mssg = QApplication.translate("StatusBar","setsv(): Unable to set SV ",None,QApplication.UnicodeUTF8)
            self.status.showMessage(mssg,5000)
            aw.qmc.adderror(mssg)

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
        i = aw.ser.sendFUJIcommand(commandi,8)
        d = aw.ser.sendFUJIcommand(commandd,8)
        
        #verify it went ok
        if len(p) == 8 and len(i)==8 and len(d) == 8:
            if k == 1:               
                 aw.pid.PXG4[pkey][0] = float(self.p1edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i1edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d1edit.text())
                 message = (QApplication.translate("StatusBar","pid #%1 successfully set to (%2,%3,%4)",None,
                                                   QApplication.UnicodeUTF8)).arg(unicode(k)).arg(unicode(self.p1edit.text())).arg(unicode(self.i1edit.text())).arg(unicode(self.d1edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNpid(1)
            elif k == 2:
                 aw.pid.PXG4[pkey][0] = float(self.p2edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i2edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d2edit.text())
                 message = (QApplication.translate("StatusBar","pid #%1 successfully set to (%2,%3,%4)",None,
                                                   QApplication.UnicodeUTF8)).arg(unicode(k)).arg(unicode(self.p2edit.text())).arg(unicode(self.i2edit.text())).arg(unicode(self.d2edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNpid(2)
            elif k == 3:
                 aw.pid.PXG4[pkey][0] = float(self.p3edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i3edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d3edit.text())
                 message = (QApplication.translate("StatusBar","pid #%1 successfully set to (%2,%3,%4)",None,
                                                   QApplication.UnicodeUTF8)).arg(unicode(k)).arg(unicode(self.p3edit.text())).arg(unicode(self.i3edit.text())).arg(unicode(self.d3edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNpid(3)
            elif k == 4:
                 aw.pid.PXG4[pkey][0] = float(self.p4edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i4edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d4edit.text())
                 message = (QApplication.translate("StatusBar","pid #%1 successfully set to (%2,%3,%4)",None,
                                                   QApplication.UnicodeUTF8)).arg(unicode(k)).arg(unicode(self.p4edit.text())).arg(unicode(self.i4edit.text())).arg(unicode(self.d4edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNpid(4)
            elif k == 5:
                 aw.pid.PXG4[pkey][0] = float(self.p5edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i5edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d5edit.text())
                 message = (QApplication.translate("StatusBar","pid #%1 successfully set to (%2,%3,%4)",None,
                                                   QApplication.UnicodeUTF8)).arg(unicode(k)).arg(unicode(self.p5edit.text())).arg(unicode(self.i5edit.text())).arg(unicode(self.d5edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNpid(5)
            elif k == 6:
                 aw.pid.PXG4[pkey][0] = float(self.p6edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i6edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d6edit.text())
                 message = (QApplication.translate("StatusBar","pid #%1 successfully set to (%2,%3,%4)",None,
                                                   QApplication.UnicodeUTF8)).arg(unicode(k)).arg(unicode(self.p6edit.text())).arg(unicode(self.i6edit.text())).arg(unicode(self.d6edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNpid(6)
            elif k == 7:
                 aw.pid.PXG4[pkey][0] = float(self.p7edit.text())
                 aw.pid.PXG4[ikey][0] = float(self.i7edit.text())
                 aw.pid.PXG4[dkey][0] = float(self.d7edit.text())
                 message = (QApplication.translate("StatusBar","pid #%1 successfully set to (%2,%3,%4)",None,
                                                   QApplication.UnicodeUTF8)).arg(unicode(k)).arg(unicode(self.p7edit.text())).arg(unicode(self.i7edit.text())).arg(unicode(self.d7edit.text()))
                 self.status.showMessage(message,5000)
                 self.setNpid(7) 
        else:
            lp = len(p)
            li = len(i)
            ld = len(d)
            mssg = QApplication.translate("StatusBar","pid command failed. Bad data at pid%1 (8,8,8): (%2,%3,%4) ",None,
                                                   QApplication.UnicodeUTF8).arg(unicode(k)).arg(unicode(lp)).arg(unicode(li)).arg(unicode(ld))
            self.status.showMessage(mssg,5000)
            aw.qmc.adderror(mssg)


    def getallpid(self):
        for k in range(1,8):
            pkey = u"p" + unicode(k)
            ikey = u"i" + unicode(k)
            dkey = u"d" + unicode(k)

            msg = QApplication.translate("StatusBar","sending commands for p%1 i%2 d%3",None,
                                                   QApplication.UnicodeUTF8).arg(unicode(k)).arg(unicode(k)).arg(unicode(k))
            self.status.showMessage(msg,1000)
            commandp = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4[pkey][1],1)
            p = aw.pid.readoneword(commandp)/10.
            commandi = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4[ikey][1],1)
            i = aw.pid.readoneword(commandi)/10.
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
                    mssg = pkey + u"=" + unicode(p) + u" " + ikey + u"=" + unicode(i) + u" " + dkey + u"=" + unicode(d) # No translation needed here
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
                mssg = QApplication.translate("StatusBar","getallpid(): Unable to read pid values ",None,QApplication.UnicodeUTF8)
                self.status.showMessage(mssg,5000)
                aw.qmc.adderror(mssg)
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

            mssg = QApplication.translate("StatusBar","PID is using pid = %1",None,QApplication.UnicodeUTF8).arg(unicode(N))
            self.status.showMessage(mssg,5000)
        else:
            mssg = QApplication.translate("StatusBar","getallpid(): Unable to read current sv ",None,QApplication.UnicodeUTF8)
            self.status.showMessage(mssg,5000)
            aw.qmc.adderror(mssg)
            
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

        mssg = QApplication.translate("StatusBar","PID is using SV = %1",None,QApplication.UnicodeUTF8).arg(unicode(N))
        self.status.showMessage(mssg,5000)
         
    def checkrampsoakmode(self):
        msg = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4["rampsoakmode"][1],1)
        currentmode = aw.pid.readoneword(msg)
        aw.pid.PXG4["rampsoakmode"][0] = currentmode
        if currentmode == 0:
            mode = [u"0",
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8)]
        elif currentmode == 1:
            mode = [u"1",
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8)]
        elif currentmode == 2:
            mode = [u"2",
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8)]
        elif currentmode == 3:
            mode = [u"3",
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8)]
        elif currentmode == 4:
            mode = [u"4",
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8)]
        elif currentmode == 5:
            mode = [u"5",
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8)]
        elif currentmode == 6:
            mode = [u"6",
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8)]
        elif currentmode == 7:
            mode = [u"7",
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8)]
        elif currentmode == 8:
            mode = [u"8",
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8)]
        elif currentmode == 9:
            mode = [u"9",
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8)]
        elif currentmode == 10:
            mode = [u"10",
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8)]
        elif currentmode == 11:
            mode = [u"11",
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8)]
        elif currentmode == 12:
            mode = [u"12",
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8)]
        elif currentmode == 13:
            mode = [u"13",
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","CONTINUOUS CONTROL",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8)]
        elif currentmode == 14:
            mode = [u"14",
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","OFF",None,QApplication.UnicodeUTF8)]
        elif currentmode == 15:
            mode = [u"15",
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","STANDBY MODE",None,QApplication.UnicodeUTF8),
                    QApplication.translate("MessageBox","ON",None,QApplication.UnicodeUTF8)]
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
        
        reply = QMessageBox.question(self,QApplication.translate("MessageBox Caption","Ramp Soak start-end mode",None,QApplication.UnicodeUTF8),string,
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
                self.status.showMessage(QApplication.translate("StatusBar","Ramp/Soak operation cancelled",None,QApplication.UnicodeUTF8), 5000)
                return
            elif check == -1:
                self.status.showMessage(QApplication.translate("StatusBar","No RX data",None,QApplication.UnicodeUTF8), 5000)
                
            self.status.showMessage(QApplication.translate("StatusBar","Setting RS ON...",None,QApplication.UnicodeUTF8),500)

            selectedmode = self.patternComboBox.currentIndex()
            msg = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4["rampsoakpattern"][1],1)
            currentmode = aw.pid.readoneword(msg)
            aw.pid.PXG4["rampsoakpattern"][0] = currentmode
            
            if currentmode != selectedmode:
                #set mode in pid to match the mode selected in the combobox
                self.status.showMessage(QApplication.translate("StatusBar","Need to change pattern mode...",None,QApplication.UnicodeUTF8),1000)
                command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["rampsoakpattern"][1],selectedmode)
                r = aw.ser.sendFUJIcommand(command,8)
                if len(r) == 8:
                    self.status.showMessage(QApplication.translate("StatusBar","Pattern has been changed. Wait 5 secs.",None,QApplication.UnicodeUTF8), 500)
                    aw.pid.PXG4["rampsoakpattern"][0] = selectedmode
                else:
                    self.status.showMessage(QApplication.translate("StatusBar","Pattern could not be changed",None,QApplication.UnicodeUTF8), 5000)
                    return
            #combobox mode matches pid mode
            #set ramp soak mode ON/OFF
            command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["rampsoak"][1],flag)
            r = aw.ser.sendFUJIcommand(command,8)
            if r == command:
                #record command as an Event if flag = 1
                if flag == 1:
                    self.status.showMessage(QApplication.translate("StatusBar","RS ON and running...",None,QApplication.UnicodeUTF8), 5000)
                    pattern =[[1,4],[5,8],[1,8],[9,12],[13,16],[9,16],[1,16]]
                    start = pattern[aw.pid.PXG4["rampsoakpattern"][0]][0]
                    end = pattern[aw.pid.PXG4["rampsoakpattern"][0]][1]+1
                    strcommand = u"SETRS"
                    result = u""
                    for i in range(start,end):
                        svkey = u"segment"+str(i)+"sv"
                        rampkey = u"segment"+str(i)+"ramp"
                        soakkey = u"segment"+str(i)+"soak"
                        strcommand += u"::" + unicode(aw.pid.PXG4[svkey][0]) + u"::" + unicode(aw.pid.PXG4[rampkey][0]) + u"::" + unicode(aw.pid.PXG4[soakkey][0])+u"::"
                        result += strcommand
                        strcommand = u"SETRS"
                    result = result.strip(u"::")
                    aw.qmc.DeviceEventRecord(result)
                elif fag == 0:
                    self.status.showMessage(QApplication.translate("StatusBar","RS turned OFF",None,QApplication.UnicodeUTF8), 5000)
                elif fag == 2:
                    self.status.showMessage(QApplication.translate("StatusBar","RS on HOLD mode",None,QApplication.UnicodeUTF8), 5000)
            else:
                self.status.showMessage(QApplication.translate("StatusBar","RampSoak could not be changed",None,QApplication.UnicodeUTF8), 5000)
                
        #set ramp soak OFF       
        elif flag == 0:
            self.status.showMessage(QApplication.translate("StatusBar","setting RS OFF...",None,QApplication.UnicodeUTF8),500)
            command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["rampsoak"][1],flag)
            r = aw.ser.sendFUJIcommand(command,8)
            if r == command:
                self.status.showMessage(QApplication.translate("StatusBar","RS successfully turned OFF",None,QApplication.UnicodeUTF8), 5000)
                aw.pid.PXG4["rampsoak"][0] = flag
            else:
                self.status.showMessage(QApplication.translate("StatusBar","Ramp Soak could not be set OFF",None,QApplication.UnicodeUTF8), 5000)

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
                message = QApplication.translate("Message Area","Pattern changed to %1", None, QApplication.UnicodeUTF8).arg(patterns[aw.pid.PXG4CH4["rampsoakpattern"][0]])
            else:
                message = QApplication.translate("Message Area","Pattern did not changed",None, QApplication.UnicodeUTF8)
            aw.sendmessage(message)
        elif onoff == 1:            
            aw.sendmessage(QApplication.translate("Message Area","Ramp/Soak was found ON! Turn it off before changing the pattern", None, QApplication.UnicodeUTF8))
        elif onoff == 2:
            aw.sendmessage(QApplication.translate("Message Area","Ramp/Soak was found in Hold! Turn it off before changing the pattern", None, QApplication.UnicodeUTF8))

    def setONOFFstandby(self,flag):
        #standby ON (pid off) will reset: rampsoak modes/autotuning/self tuning
        #flag = 0 standby OFF, flag = 1 standby ON (pid off)
        self.status.showMessage(QApplication.translate("StatusBar","wait...",None, QApplication.UnicodeUTF8),500)
        command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["runstandby"][1],flag)
        #TX and RX
        r = aw.ser.sendFUJIcommand(command,8)
                        
        if r == command and flag == 1:
            message = QApplication.translate("StatusBar","PID set to OFF",None, QApplication.UnicodeUTF8)     #put pid in standby 1 (pid on)
            aw.pid.PXG4["runstandby"][0] = 1
        elif r == command and flag == 0:
            message = QApplication.translate("StatusBar","PID set to ON",None, QApplication.UnicodeUTF8)      #put pid in standby 0 (pid off)
            aw.pid.PXG4["runstandby"][0] = 0
        else:
            message = QApplication.translate("StatusBar","Unable",None, QApplication.UnicodeUTF8)
        if r:
            self.status.showMessage(message,5000)
        else:
            self.status.showMessage(QApplication.translate("StatusBar","No data received",None, QApplication.UnicodeUTF8),5000)            


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
        aw.pid.PXG4[rampkey][0] = ramp
        
        soakkey = u"segment" + unicode(idn) + u"soak"
        soakcommand = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4[soakkey][1],1)
        soak = aw.pid.readoneword(soakcommand)
        if soak == -1:
            return -1
        aw.pid.PXG4[soakkey][0] = soak

    #get all Ramp Soak values for all 8 segments                                  
    def getallsegments(self):
        for i in range(1,17):
            msg = QApplication.translate("StatusBar","Reading Ramp/Soak %1 ...",None, QApplication.UnicodeUTF8).arg(unicode(i))
            self.status.showMessage(msg,500)
            k = self.getsegment(i)
            libtime.sleep(0.03)
            if k == -1:
                self.status.showMessage(QApplication.translate("StatusBar","problem reading Ramp/Soak",None, QApplication.UnicodeUTF8),5000)
                return
            self.paintlabels()
        self.status.showMessage(QApplication.translate("StatusBar","Finished reading Ramp/Soak val.",None, QApplication.UnicodeUTF8),5000)
        self.createsegmenttable()
        
    def setONOFFautotune(self,flag):
        self.status.showMessage(QApplication.translate("StatusBar","setting autotune...",None, QApplication.UnicodeUTF8),500)
        #read current pidN
        command = aw.pid.message2send(aw.ser.controlETpid[1],3,aw.pid.PXG4["selectedpid"][1],1)
        N = aw.pid.readoneword(command)
        aw.pid.PXG4["selectedpid"][0] = N

        string = QApplication.translate("StatusBar","Current pid = %1. Proceed with autotune command?",None, QApplication.UnicodeUTF8).arg(unicode(N))
        reply = QMessageBox.question(self,QApplication.translate("MessageBox Caption","Ramp Soak start-end mode",None, QApplication.UnicodeUTF8),string,
                            QMessageBox.Yes|QMessageBox.Cancel)
        if reply == QMessageBox.Cancel:
            self.status.showMessage(QApplication.translate("StatusBar","Autotune cancelled",None, QApplication.UnicodeUTF8),5000)
            return 0
        elif reply == QMessageBox.Yes:
            command = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4["autotuning"][1],flag)
            #TX and RX
            r = aw.ser.sendFUJIcommand(command,8)
            if len(r) == 8:
                if flag == 0:
                    aw.pid.PXG4["autotuning"][0] = 0
                    self.status.showMessage(QApplication.translate("StatusBar","Autotune successfully turned OFF",None, QApplication.UnicodeUTF8),5000)
                if flag == 1:
                    aw.pid.PXG4["autotuning"][0] = 1
                    self.status.showMessage(QApplication.translate("StatusBar","Autotune successfully turned ON",None, QApplication.UnicodeUTF8),5000) 
            else:
                self.status.showMessage(QApplication.translate("StatusBar","UNABLE to set Autotune",None, QApplication.UnicodeUTF8),5000) 

    def createsegmenttable(self):
        self.segmenttable.setRowCount(16)
        self.segmenttable.setColumnCount(4)
        self.segmenttable.setHorizontalHeaderLabels([QApplication.translate("StatusBar","SV",None, QApplication.UnicodeUTF8),
                                                     QApplication.translate("StatusBar","Ramp (MM:SS)",None, QApplication.UnicodeUTF8),
                                                     QApplication.translate("StatusBar","Soak (MM:SS)",None, QApplication.UnicodeUTF8),""])
        self.segmenttable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.segmenttable.setSelectionBehavior(QTableWidget.SelectRows)
        self.segmenttable.setSelectionMode(QTableWidget.SingleSelection)
        self.segmenttable.setShowGrid(True)
        regextime = QRegExp(r"^-?[0-5][0-9]:[0-5][0-9]$")
        #populate table
        for i in range(16):
            #create widgets
            svkey = u"segment" + unicode(i+1) + u"sv"
            rampkey = u"segment" + unicode(i+1) + u"ramp"
            soakkey = u"segment" + unicode(i+1) + u"soak"
            
            svedit = QLineEdit(unicode(aw.pid.PXG4[svkey][0]))
            svedit.setValidator(QDoubleValidator(0., 999., 1, svedit))
            rampedit = QLineEdit(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4[rampkey][0])))
            rampedit.setValidator(QRegExpValidator(regextime,self))    
            soakedit  = QLineEdit(unicode(aw.qmc.stringfromseconds(aw.pid.PXG4[soakkey][0])))
            soakedit.setValidator(QRegExpValidator(regextime,self))    
            setButton = QPushButton(QApplication.translate("Button","Set",None, QApplication.UnicodeUTF8))
            self.connect(setButton,SIGNAL("clicked()"),lambda i =i:self.setsegment(i))
            #add widgets to the table
            self.segmenttable.setCellWidget(i,0,svedit)
            self.segmenttable.setCellWidget(i,1,rampedit)
            self.segmenttable.setCellWidget(i,2,soakedit)
            self.segmenttable.setCellWidget(i,3,setButton)

    #idn = id number, sv = float set value, ramp = ramp value, soak = soak value
    def setsegment(self,i):
        idn = i+1
        svedit =  self.segmenttable.cellWidget(i,0)
        rampedit = self.segmenttable.cellWidget(i,1)
        soakedit = self.segmenttable.cellWidget(i,2)

        sv = float(svedit.text())
        ramp = aw.qmc.stringtoseconds(unicode(rampedit.text()))
        soak = aw.qmc.stringtoseconds(unicode(soakedit.text()))

        svkey = u"segment" + unicode(idn) + u"sv"
        svcommand = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4[svkey][1],int(sv*10))
        r1 = aw.ser.sendFUJIcommand(svcommand,8)

        libtime.sleep(0.1) #important time between writings
        rampkey = u"segment" + unicode(idn) + u"ramp"
        rampcommand = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4[rampkey][1],ramp)
        r2 = aw.ser.sendFUJIcommand(rampcommand,8)

        libtime.sleep(0.1) #important time between writings
        soakkey = u"segment" + unicode(idn) + u"soak"
        soakcommand = aw.pid.message2send(aw.ser.controlETpid[1],6,aw.pid.PXG4[soakkey][1],soak)
        r3 = aw.ser.sendFUJIcommand(soakcommand,8)
      
        #check if OK
        if len(r1) == 8 and len(r2) == 8 and len(r3) == 8:
            aw.pid.PXG4[svkey][0] = sv
            aw.pid.PXG4[rampkey][0] = ramp
            aw.pid.PXG4[soakkey][0] = soak
            self.paintlabels()
            self.status.showMessage(QApplication.translate("StatusBar","Ramp/Soak successfully writen",None, QApplication.UnicodeUTF8),5000) 
        else:
            aw.qmc.adderror(QApplication.translate("Error Message","Segment values could not be written into PID",None, QApplication.UnicodeUTF8))


###################################################################################
##########################  FUJI PID CLASS DEFINITION  ############################
###################################################################################
        
# This class can work for either one Fuji PXR or one Fuji PXG. It is used for the controlling PID only.
# NOTE: There is only one controlling PID. The second pid is only used for reading BT and therefore,
# there is no need to create a second PID object since the second pid all it does is read temperature (always use the same command).
# All is needed for the second pid is its unit id number stored in aw.qmc.device[].
# The command to read T is the always the same for PXR and PXG but with the unit ID changed.

class FujiPID(object):
    def __init__(self):
        
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

                   ############ CH3 These are 7 pid storage locations
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
                  #the time to reach sv is called ramp 
                  #the time to hold the temperature at sv is called soak 
                  "timeunits": [1,41562],  #0=hh.MM (hour:min)  1=MM.SS (min:sec)                             # PXG has two time formats HH:MM (factory default) and MM:SS 
                  # Example. Dry roast phase. selects 3 or 4 minutes                                          # PXG needs to have parameter TIMU set to 1 (MM:SS)
                  "segment1sv": [270.0,41581],"segment1ramp": [180,41582],"segment1soak": [0,41583],          # See PXG Manual chapter 6: Ramp/Soak Time Units to set the parameter TIMU    
                  "segment2sv": [300.0,41584],"segment2ramp": [180,41585],"segment2soak": [0,41586],         
                  "segment3sv": [350.0,41587],"segment3ramp": [180,41588],"segment3soak": [0,41589],
                  "segment4sv": [400.0,41590],"segment4ramp": [180,41591],"segment4soak": [0,41591],
                  # Example. Phase to 1C. selects 6 or 8 mins
                  "segment5sv": [530.0,41593],"segment5ramp": [180,41594],"segment5soak": [0,41595],
                  "segment6sv": [530.0,41596],"segment6ramp": [180,41597],"segment6soak": [0,41598],
                  "segment7sv": [540.0,41599],"segment7ramp": [180,41600],"segment7soak": [0,41601],
                  "segment8sv": [540.0,41602],"segment8ramp": [180,41603],"segment8soak": [0,41604],
                  "segment9sv": [550.0,41605],"segment9ramp": [180,41606],"segment9soak": [0,41607],
                  "segment10sv": [550.0,41608],"segment10ramp": [180,41609],"segment10soak": [0,41610],
                  "segment11sv": [560.0,41611],"segment11ramp": [180,41612],"segment11soak": [0,41613],
                  "segment12sv": [560.0,41614],"segment12ramp": [180,41615],"segment12soak": [0,41616],
                  # Eaxample. Finish phase. selects 3 mins for regular coffee or 5 mins for espresso
                  "segment13sv": [570.0,41617],"segment13ramp": [180,41618],"segment13soak": [0,41619],
                  "segment14sv": [570.0,41620],"segment14ramp": [180,41621],"segment14soak": [0,41622],
                  "segment15sv": [580.0,41623],"segment15ramp": [180,41624],"segment15soak": [0,41625],
                  "segment16sv": [580.0,41626],"segment16ramp": [180,41627],"segment16soak": [0,41628],
                  # "rampsoakmode" 0-15 = 1-16 IMPORTANT: Factory setting is 3 (BAD). Set it up to number 0 or it will
                  # sit on stanby (SV blinks) at the end till rampsoakmode changes. It will appear as if the PID broke (unresponsive)
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
                  "pv?":[31001],"sv?":[0,31002],"alarm?":[31007],"fault?":[31008],"stat?":[31041],"mv1":[0,31042]
                  }

        # "KEY": [VALUE,MEMORY ]
        self.PXR = {"autotuning":[0,41005],
                    "segment1sv":[100.0,41057],"segment1ramp":[3,41065],"segment1soak":[0,41066], #PXR uses only HH:MM time format but stored as minutes in artisan
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
                    "pvinputtype":[3,41016],
                    #READ ONLY
                    #current pv
                    "pv?":[0,31001],
                    #current sv on display (during ramp soak it changes)
                    "sv?":[0,31002],
                    #rampsoak current running position (1-8)
                    "segment?":[0,31009],
                    "mv1":[0,30004]   	    	    	#duty cycle rx -300 to 10300  = -3.00% to 103.00% (divide by 100.)
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
            aw.button_12.setVisible(False)
            aw.button_13.setVisible(False)
            aw.button_14.setVisible(False)
            aw.button_15.setVisible(False)
            aw.button_16.setVisible(False)
            aw.button_17.setVisible(False)            

            
        #turn on
        elif flag == 1:
            A = QLabel()
            reply = QMessageBox.question(A,QApplication.translate("MessageBox Caption","Activate PID front buttons",None, QApplication.UnicodeUTF8),
                                         QApplication.translate("MessageBox","Remember SV memory has a finite\nlife of ~10,000 writes.\n\nProceed?",None, QApplication.UnicodeUTF8),
                                         QMessageBox.Yes|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return 
            elif reply == QMessageBox.Yes:
                aw.button_12.setVisible(True)
                aw.button_13.setVisible(True)
                aw.button_14.setVisible(True)
                aw.button_15.setVisible(True)
                aw.button_16.setVisible(True)
                aw.button_17.setVisible(True)
                

    def readcurrentsv(self):
        #if control pid is fuji PXG4
        if aw.ser.controlETpid[0] == 0:        
            command = self.message2send(aw.ser.controlETpid[1],4,self.PXG4["sv?"][1],1)
        #or if control pid is fuji PXR
        elif aw.ser.controlETpid[0] == 1:
            command = self.message2send(aw.ser.controlETpid[1],4,self.PXR["sv?"][1],1)
        val = self.readoneword(command)/10.
        if val != -0.1:
            return val
        else:
            return -1
 
    def readdutycycle(self):
        #if control pid is fuji PXG4
        if aw.ser.controlETpid[0] == 0:        
            command = self.message2send(aw.ser.controlETpid[1],4,self.PXG4["mv1"][1],1)
        #or if control pid is fuji PXR
        elif aw.ser.controlETpid[0] == 1:
            command = self.message2send(aw.ser.controlETpid[1],4,self.PXR["mv1"][1],1)            
        val = self.readoneword(command)/100.
        if val != -0.01:
            return val
        else:
            return -1


    #turns ON turns OFF current ramp soak mode
    #flag =0 OFF, flag = 1 ON, flag = 2 hold
    #A ramp soak pattern defines a whole profile. They have a minimum of 4 segments.       
    def setrampsoak(self,flag):
        #Fuji PXG 
        if aw.ser.controlETpid[0] == 0:         
            command = self.message2send(aw.ser.controlETpid[1],6,self.PXG4["rampsoak"][1],flag)
        #Fuji PXR    
        elif aw.ser.controlETpid[0] == 1:
            command = self.message2send(aw.ser.controlETpid[1],6,self.PXR["rampsoak"][1],flag)
            
        r = aw.ser.sendFUJIcommand(command,8)
        #if OK
        if r == command:
            if flag == 1:
                aw.sendmessage(QApplication.translate("Message Area","RS ON and running...", None, QApplication.UnicodeUTF8))
            elif flag == 0:
                aw.sendmessage(QApplication.translate("Message Area","RS OFF", None, QApplication.UnicodeUTF8))
            else:           
                aw.sendmessage(QApplication.translate("Message Area","RS on HOLD", None, QApplication.UnicodeUTF8))
        else:
            aw.qmc.adderror(QApplication.translate("Error Message","RampSoak could not be changed",None, QApplication.UnicodeUTF8))

           
    #sets a new sv value              
    def setsv(self,value):
        #Fuji PXG 
        if aw.ser.controlETpid[0] == 0: 
            #send command to the current sv (1-7)
            svkey = u"sv"+ unicode(aw.pid.PXG4["selectsv"][0]) #current sv
            command = self.message2send(aw.ser.controlETpid[1],6,self.PXG4[svkey][1],int(value*10))
            r = aw.ser.sendFUJIcommand(command,8)
            #check response
            if r == command:
                           
                # [Not sure the following will translate or even format properly... Need testing!]
                message = QApplication.translate("Message Area","PXG sv#%1 set to %2",None, QApplication.UnicodeUTF8).arg(self.PXG4["selectsv"][0]).arg("%.1f" % float(value))
                aw.sendmessage(message)
                self.PXG4[svkey][0] = value
                #record command as an Event 
                strcommand = u"SETSV::" + unicode("%.1f"%float(value))
                aw.qmc.DeviceEventRecord(strcommand)
                aw.lcd6.display(u"%.1f"%float(value))
            else:
                aw.qmc.adderror(QApplication.translate("Error Message","setPXGsv(): bad response from PID",None, QApplication.UnicodeUTF8))
                return -1
        #Fuji PXR    
        elif aw.ser.controlETpid[0] == 1:  
            command = self.message2send(aw.ser.controlETpid[1],6,aw.pid.PXR["sv0"][1],int(value*10))
            r = aw.ser.sendFUJIcommand(command,8)
            #check response
            if r == command:
                # [Not sure the following will translate or even format properly... Need testing!]           
                message = QApplication.translate("Message Area","PXR sv set to %1",None, QApplication.UnicodeUTF8).arg("%.1f" % float(value))
                aw.pid.PXR["sv0"][0] = value
                aw.sendmessage(message)
                #record command as an Event 
                strcommand = u"SETSV::" + unicode("%.1f"%float(value))
                aw.qmc.DeviceEventRecord(strcommand)
                aw.lcd6.display(u"%.1f"%float(value))

            else:
                aw.qmc.adderror(QApplication.translate("Error Message","setPXRsv(): bad response from PID",None, QApplication.UnicodeUTF8))
                return -1


    #used to set up or down SV by diff degrees from current sv setting      
    def adjustsv(self,diff):
        currentsv = self.readcurrentsv()
        if currentsv != -1:
            newsv = int((currentsv + diff)*10.)          #multiply by 10 because we use a decimal point          

            #   if control pid is fuji PXG
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
                        message = QApplication.translate("Message Area","SV%1 changed from %2 to %3)",None, QApplication.UnicodeUTF8).arg(unicode(N)).arg(unicode(currentsv)).arg(unicode(newsv/10.))
                        aw.sendmessage(message)
                        self.PXG4[svkey][0] = newsv/10
                        
                        #record command as an Event to replay (not binary as it needs to be stored in a text file)
                        strcommand = u"SETSV::" + unicode("%.1f"%(newsv/10.))
                        aw.qmc.DeviceEventRecord(strcommand)
                        aw.lcd6.display(u"%.1f"%float(newsv/10.))   
                    else:
                        msg = QApplication.translate("Message Area","Unable to set sv%1",None, QApplication.UnicodeUTF8).arg(unicode(N))
                        aw.sendmessage(msg)       

            #   or if control pid is fuji PXR
            elif aw.ser.controlETpid[0] == 1:
                command = self.message2send(aw.ser.controlETpid[1],6,self.PXR["sv0"][1],newsv)
                r = aw.ser.sendFUJIcommand(command,8)
                if len(r) == 8:
                    message = QApplication.translate("Message Area"," SV changed from %1 to %2)",None, QApplication.UnicodeUTF8).arg(unicode(currentsv)).arg(unicode(newsv/10.))                           
                    aw.sendmessage(message)
                    self.PXR["sv0"][0] = newsv/10

                    #record command as an Event to replay (not binary as it needs to be stored in a text file)
                    strcommand = u"SETSV::" + unicode("%.1f"%(newsv/10.))
                    aw.qmc.DeviceEventRecord(strcommand)
                    aw.lcd6.display(u"%.1f"%float(newsv/10.))   

                else:
                    aw.sendmessage(QApplication.translate("Message Area","Unable to set sv", None, QApplication.UnicodeUTF8))
        else:
            aw.sendmessage(QApplication.translate("Message Area","Unable to set new sv", None, QApplication.UnicodeUTF8))


    #format of the input string Command: COMMAND::VALUE1::VALUE2::VALUE3::ETC        
    def replay(self,CommandString):
        parts = CommandString.split("::")
        command = parts[0]
        values = parts[1:]
                 
        if command == "SETSV":
            self.setsv(float(values[0]))
            return
        elif command == "SETRS":
            self.replaysetrs(CommandString)
            return

    #example of command string with four segments (minimum for Fuji PIDs)
    # SETRS::270.0::3::0::SETRS::300.0::3::0::SETRS::350.0::3::0::SETRS::400.0::3::0
    def replaysetrs(self,CommandString):
        segments =CommandString.split("SETRS")
        if segments[0] == "":
            segments = segments[1:]          #remove first empty [""] list [[""],[etc]]
        if segments[-1] == "":
            segments = segments[:-1]          #remove last empty [""] list [[etc][""]]
        n = len(segments)
        
        #if parts is < 4, make it compatible with Fuji PID (4 segments needed)
        if n < 4:            
            for i in range(4-n):
                #last temperature
                lasttemp = segments[-1].split("::")[1]
                #create a string with 4 segments ("SETRS" alredy removed) 
                string = "::" + lasttemp + u"::0::0"   #add zero ramp time and zero soak time
                segments.append(string)
                
        rs = []
        changeflag = 0
        for i in range(n):
            rs.append(segments[i].split("::"))
            if rs[i][0] == "":          #remove first empty u"" [u"",u"300.5",u"3",u"0",u""] if one found
                rs[i] = rs[i][1:]
            if rs[i][-1] == "":          #remove last empty u"" [u"300.5",u"3",u"0",u""] if one found
                rs[i] = rs[i][:-1]
            
            if len(rs[i]) == 3:
                svkey = "segment" + str(i+1) + "sv"
                rampkey = "segment" + str(i+1) + "ramp"
                soakkey = "segment" + str(i+1) + "soak"
                if aw.ser.controlETpid[0] == 0:             #PXG4
                    if not n%4 or n > 16:
                        aw.qmc.adderror(QApplication.translate("Error Message","PXG4 replaysetrs() Error: Invalid segment count: %1",None, QApplication.UnicodeUTF8).arg(n))
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
                elif aw.ser.controlETpid[0] == 1:           #PXR
                    if not n%4 or n > 8:
                        aw.qmc.adderror(QApplication.translate("Error Message","PXR replaysetrs() Error: Invalid segment count: %1",None, QApplication.UnicodeUTF8).arg(n))
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
                aw.qmc.adderror(QApplication.translate("Error Message","replaysetrs() Error: Need three SETRS values (float,int,int)",None, QApplication.UnicodeUTF8))
                return
        #start ramp soak ON
        self.setrampsoak(1)
        
    #idn = id number, sv = float set value, ramp = ramp value, soak = soak value
    #used in replaysetrs()    
    def setsegment(self,idn,sv,ramp,soak):

        svkey = u"segment" + unicode(idn) + u"sv"
        rampkey = u"segment" + unicode(idn) + u"ramp"
        soakkey = u"segment" + unicode(idn) + u"soak"
        
        if aw.ser.controlETpid[0] == 0:
            svcommand = self.message2send(aw.ser.controlETpid[1],6,self.PXG4[svkey][1],int(sv*10))
            rampcommand = self.message2send(aw.ser.controlETpid[1],6,self.PXG4[rampkey][1],ramp)
            soakcommand = self.message2send(aw.ser.controlETpid[1],6,self.PXG4[soakkey][1],soak)
        elif  aw.ser.controlETpid[0] == 1:
            svcommand = self.message2send(aw.ser.controlETpid[1],6,self.PXR[svkey][1],int(sv*10))
            rampcommand = self.message2send(aw.ser.controlETpid[1],6,self.PXR[rampkey][1],ramp)
            soakcommand = self.message2send(aw.ser.controlETpid[1],6,self.PXR[soakkey][1],soak)
            
        r1 = self.sendFUJIcommand(svcommand,8)
        libtime.sleep(0.11) #important time between writings
        r2 = self.sendFUJIcommand(rampcommand,8)
        libtime.sleep(0.11) #important time between writings        
        r3 = self.sendFUJIcommand(soakcommand,8)
      
        #check if OK
        if len(r1)!=8 or len(r2)!=8 or len(r3)!=8:
            aw.qmc.adderror(QApplication.translate("Error Message","pid: Segment values could not be writen into PID",None, QApplication.UnicodeUTF8))

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
            errorcode = QApplication.translate("Error Message","pid.readoneword(): %1 RX bytes received (7 needed) for unit ID=%2",None, QApplication.UnicodeUTF8).arg(len(r)).arg(ord(command[0]))
            aw.qmc.adderror(errorcode)            
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

aw = None # this is to ensure that the variable aw is already defined during application initialization
aw = ApplicationWindow()
aw.settingsLoad()
aw.show()
#the following line is to trap numpy warnings that occure in the Cup Profile dialog if all values are set to 0
with numpy.errstate(invalid='ignore'):
    app.exec_()

##############################################################################################################################################
##############################################################################################################################################
