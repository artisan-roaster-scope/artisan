#!/usr/bin/env python3

# ABOUT
# Artisan Roast Comparator

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2020

import sys
import platform
import numpy
import matplotlib.ticker as ticker
import matplotlib.transforms as transforms
import matplotlib.patheffects as PathEffects
from matplotlib import rcParams
if sys.platform.startswith("darwin"):
    # import module to detect if OS X dark mode is active or not
    import darkdetect # @UnresolvedImport

from artisanlib.util import deltaLabelUTF8, d, stringfromseconds, appFrozen, fromFtoC, fromCtoF, fill_gaps
from artisanlib.suppress_errors import suppress_stdout_stderr
from artisanlib.dialogs import ArtisanDialog
from artisanlib.widgets import MyQComboBox
from artisanlib.qcheckcombobox import CheckComboBox

with suppress_stdout_stderr():
    from matplotlib import cm

from PyQt5.QtCore import (Qt, pyqtSignal, pyqtSlot, QSettings, QFile, QTextStream, QUrl, 
    QCoreApplication, QFileInfo, QDate, QTime, QDateTime)
from PyQt5.QtGui import (QColor, QDesktopServices)
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QTableWidget, QPushButton, 
    QComboBox, QSizePolicy, QHBoxLayout, QVBoxLayout, QHeaderView, QTableWidgetItem, QCheckBox)


class RoastProfile():
    def __init__(self, aw, profile, filepath, color):
        self.aw = aw
        # state:
        self.visible = True
        self.aligned = True # if the profile could not be aligned it is not drawn
        self.active = True # if selected or all are unselected; active profiles are drawn in color, inactive profiles in gray
        self.color = color
        hslf = QColor.fromRgbF(*color).getHslF()
        self.gray = QColor.fromHslF(hslf[0],0,hslf[2],hslf[3]).getRgbF() # saturation set to 0
        self.label = ""
        self.title = ""
        #
        self.curve_visibilities = [True]* 5 # visibility of ET, BT, DeltaET, DeltaBT, events curves
        self.event_visibility = 0 # either 0, or the number of the event line that is to be shown
        #
        self.zorder = 0 # artists with higher zorders are drawn on top of others (0-9)
        # zorder offset is added per curve type: events1, events2, BT, ET, DeltaBT, DeltaET, custom events (only one of events1/events2 active!)
        self.zorder_offsets = [80,60,80,60,40,20,0]
        #
        self.alpha = [1, 0.7, 0.5, 0.4, 0.6] # color alpha per curve: BT, ET, DeltaBT, DeltaET, custom event (alpha of main events taken from the corresponding curve)
        self.alpha_dim_factor = 0.3 # factor to be multiplied to current alpha values for inactive curves
        #
        self.timeoffset = 0 # in seconds
        self.max_DeltaET = 1
        self.max_DeltaBT = 1
        self.startTimeIdx = 0 # start index: either index of CHARGE if set or 0, set by recompute()
        self.endTimeIdx = 0   # end index: either index of DROP or last index, set by recompute()
        self.min_time = 0 # the minimum display time of this profile after alignment
        self.max_time = 0 # the maximum display time of this profile after alignment
        # profile data:
        self.UUID = None
        self.filepath = filepath
        self.timeindex = [-1,0,0,0,0,0,0,0]
        self.timex = None
        self.temp1 = None # holds raw data with gaps filled on loading
        self.temp2 = None # holds raw data with gaps filled on loading
        # events as list of timeidx/value pairs per event type
        self.E1 = []
        self.E2 = []
        self.E3 = []
        self.E4 = []
        # (re-)computed data:
        self.stemp1 = None # smoothed from temp1 and cutted to visible data only on recompute
        self.stemp2 = None
        self.delta1 = None # based on smoothed stemp1, but not yet cutted data as computed in recompute, and RoR smoothing applied, then cutted to visible data
        self.delta2 = None
        self.events1 = None # ET temperatures of main events [CHARGE, DRY, FCs, FCe, SCs, SCe, DROP], None if not set
        self.events2 = None # BT temperatures of main events [CHARGE, DRY, FCs, FCe, SCs, SCe, DROP], None if not set
        self.events_timex = None # roast times of main events [CHARGE, DRY, FCs, FCe, SCs, SCe, DROP] in seconds, None if not set
        # artists
        self.l_temp1 = None
        self.l_temp2 = None
        self.l_delta1 = None
        self.l_delta2 = None
        self.l_mainEvents1 = None
        self.l_mainEvents2 = None
        self.l_events1 = None
        self.l_events2 = None
        self.l_events3 = None
        self.l_events4 = None
#        # delta clipping paths
#        self.l_delta1_clipping = None
#        self.l_delta2_clipping = None
        #
        # fill profile data:
        if "roastUUID" in profile:
            self.UUID = d(profile["roastUUID"])
        if "timex" in profile:
            self.timex = profile["timex"]
        if "temp1" in profile:
            self.temp1 = fill_gaps(profile["temp1"])
        if "temp2" in profile:
            self.temp2 = fill_gaps(profile["temp2"])
        if "timeindex" in profile:
            for i,ti in enumerate(profile["timeindex"]):
                if i < len(self.timeindex):
                    self.timeindex[i] = ti
        elif len(profile) > 0 and ("startend" in profile or "dryend" in profile or "cracks" in profile):
            try:
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
                for i in range(len(times)):
                    if times[i]:
                        self.timeindex[i] = self.aw.qmc.timearray2index(self.timex,times[i])
                    else:
                        self.timeindex[i] = 0
            except:
                pass
            ###########      END OLD PROFILE FORMAT
            
        # temperature conversion
        if "mode" in profile:
            m = str(profile["mode"])
        else:
            m = self.qmc.mode
        if "ambientTemp" in profile:
            self.ambientTemp = profile["ambientTemp"]
        else:
            if m == "C":
                self.ambientTemp = 20
            else:
                self.ambientTemp = 68
        if self.aw.qmc.mode == "C" and m == "F":
            self.temp1 = [fromFtoC(t) for t in self.temp1]
            self.temp2 = [fromFtoC(t) for t in self.temp2]
            self.ambientTemp = fromFtoC(self.ambientTemp)
        elif self.aw.qmc.mode == "F" and m == "C":
            self.temp1 = [fromCtoF(t) for t in self.temp1]
            self.temp2 = [fromCtoF(t) for t in self.temp2]
            self.ambientTemp = fromCtoF(self.ambientTemp)
        if "title" in profile:
            self.title = d(profile["title"])
        if "roastbatchnr" in profile and profile["roastbatchnr"] != 0:
            try:
                self.label = d(profile["roastbatchprefix"]) + str(int(profile["roastbatchnr"]))[:10]
            except:
                pass
        self.specialevents = None
        self.specialeventstype = None
        self.specialeventsvalue = None
        if "specialevents" in profile:
            self.specialevents = profile["specialevents"]
        if "specialeventstype" in profile:
            self.specialeventstype = profile["specialeventstype"]
        if "specialeventsvalue" in profile:
            self.specialeventsvalue = profile["specialeventsvalue"]
        # add metadata
        self.metadata = {}
        if "roastdate" in profile:
            try:
                date = QDate.fromString(d(profile["roastdate"]))
                if not date.isValid():
                    date = QDate.currentDate()
                if "roasttime" in profile:
                    try:
                        time = QTime.fromString(d(profile["roasttime"]))
                        self.metadata["roastdate"] = QDateTime(date,time)
                    except Exception:
                        self.metadata["roastdate"] = QDateTime(date)
                else:
                    self.metadata["roastdate"] = QDateTime(date)
            except Exception:
                pass
        # the new dates have the locale independent isodate format:
        if "roastisodate" in profile:
            try:
                date = QDate.fromString(d(profile["roastisodate"]),Qt.ISODate)
                if "roasttime" in profile:
                    try:
                        time = QTime.fromString(d(profile["roasttime"]))
                        self.metadata["roastdate"] = QDateTime(date,time)
                    except Exception:
                        self.metadata["roastdate"] = QDateTime(date)
                else:
                    self.metadata["roastdate"] = QDateTime(date)
            except Exception:
                pass
        if "roastepoch" in profile:
            try:
                self.metadata["roastdate"] = QDateTime.fromTime_t(profile["roastepoch"])
            except Exception:
                pass
        if "beans" in profile:
            self.metadata["beans"] = d(profile["beans"])
        if "weight" in profile and profile["weight"][0] != 0.0:
            w = profile["weight"][0]
            if d(profile["weight"][2]) != "g":
                w = self.aw.float2float(w,1)
            self.metadata["weight"] = "%g%s"%(w,d(profile["weight"][2]))
        if "moisture_greens" in profile and profile["moisture_greens"] != 0.0:
            self.metadata["moisture_greens"] = profile["moisture_greens"]
        if "ambientTemp" in profile:
            self.metadata["ambientTemp"] = "%g%s" % (self.aw.float2float(self.ambientTemp),self.aw.qmc.mode)          
        if "ambient_humidity" in profile:
            self.metadata["ambient_humidity"] = "%g%%" % self.aw.float2float(profile["ambient_humidity"])
        if "ambient_pressure" in profile:
            self.metadata["ambient_pressure"] = "%ghPa" % self.aw.float2float(profile["ambient_pressure"])
        if "computed" in profile and profile["computed"] is not None and "weight_loss" in profile["computed"] and \
                profile["computed"]["weight_loss"] is not None:
            self.metadata["weight_loss"] = "-%.1f%%" % profile["computed"]["weight_loss"]
        if "ground_color" in profile:
            self.metadata["ground_color"] = "#%s" % profile["ground_color"]
        if "computed" in profile and profile["computed"] is not None and "AUC" in profile["computed"] and profile["computed"]["AUC"] is not None and \
                profile["computed"]["AUC"] != 0:
            self.metadata["AUC"] = "%sC*min" % profile["computed"]["AUC"]
        if "roastingnotes" in profile:
            self.metadata["roastingnotes"] = d(profile["roastingnotes"])
        if "cuppingnotes" in profile:
            self.metadata["cuppingnotes"] = d(profile["cuppingnotes"])       
        # TP time in time since DROP
        if "computed" in profile and profile["computed"] is not None and "TP_time" in profile["computed"]:
            self.TP = profile["computed"]["TP_time"]
        else:
            self.TP = 0
        #
        self.recompute()
        self.draw()
        self.updateAlpha()
    
    # applies current smoothing values to temperature and delta curves
    def recompute(self):
        # we resample the temperatures to regular interval timestamps
        if self.timex is not None and self.timex and len(self.timex)>1:
            timex_lin = numpy.linspace(self.timex[0],self.timex[-1],len(self.timex))
        else:
            timex_lin = None
        decay_smoothing_p = (not self.aw.qmc.optimalSmoothing)
        self.stemp1 = self.aw.qmc.smooth_list(self.timex,self.temp1,window_len=self.aw.qmc.curvefilter,decay_smoothing=decay_smoothing_p,a_lin=timex_lin)
        self.stemp2 = self.aw.qmc.smooth_list(self.timex,self.temp2,window_len=self.aw.qmc.curvefilter,decay_smoothing=decay_smoothing_p,a_lin=timex_lin)
        # recompute deltas
        cf = self.aw.qmc.curvefilter*2 # we smooth twice as heavy for PID/RoR calcuation as for normal curve smoothing
        t1 = self.aw.qmc.smooth_list(self.timex,self.temp1,window_len=cf,decay_smoothing=decay_smoothing_p,a_lin=timex_lin)
        t2 = self.aw.qmc.smooth_list(self.timex,self.temp2,window_len=cf,decay_smoothing=decay_smoothing_p,a_lin=timex_lin)
        if self.timeindex[0]>-1:
            RoR_start = min(self.timeindex[0]+10, len(self.timex)-1)
        else:
            RoR_start = -1
        self.delta1, self.delta2 = self.aw.qmc.recomputeDeltas(self.timex,RoR_start,self.timeindex[6],t1,t2,optimalSmoothing=not decay_smoothing_p,timex_lin=timex_lin)
        # calculate start/end index
        self.startTimeIdx = (self.timeindex[0] if self.timeindex[0] != -1 else 0)
        self.endTimeIdx = (self.timeindex[6] if self.timeindex[6] != 0 else len(self.timex)-1)
        self.stemp1 = [None if i < self.startTimeIdx or i > self.endTimeIdx else t for i,t in enumerate(self.stemp1)]
        self.stemp2 = [None if i < self.startTimeIdx or i > self.endTimeIdx else t for i,t in enumerate(self.stemp2)]
        # calculate max deltas
        self.max_DeltaET = 1
        if len(self.delta1) > 0:
            try:
                self.max_DeltaET = max(filter(None,self.delta1))
            except:
                pass
        self.max_DeltaBT = 1
        if len(self.delta2) > 0:
            try:
                self.max_DeltaBT = max(filter(None,self.delta2))
            except:
                pass
        self.events1 = []
        self.events2 = []
        self.events_timex = []
        for ti in self.timeindex[:-1]:
            temp1 = self.stemp1[ti]
            temp2 = self.stemp2[ti]
            if (len(self.events1) == 0 and ti != -1) or ti > 0:
                self.events1.append(temp1)
                self.events2.append(temp2)
                self.events_timex.append(self.timex[ti])
            else:
                self.events1.append(None)
                self.events2.append(None)
                self.events_timex.append(None)
        # update special events
        if self.specialevents is not None and self.specialeventstype is not None and self.specialeventsvalue is not None:
            # calculated bot and top corresponding to the temperature positions of the event values 0 and 100
            if self.aw.qmc.clampEvents:
                top = 100
                bot = 0
            else:
                if self.aw.qmc.step100temp is None:
                    top = self.aw.qmc.phases[0]
                else:
                    top = self.aw.qmc.step100temp
                bot = self.aw.qmc.ylimit_min
            value_offset = bot
            value_factor = (top-bot)/100
            self.E1 = []
            self.E2 = []
            self.E3 = []
            self.E4 = []
            for i,e in enumerate(self.specialevents):
                try:
                    etime = self.timex[e]
                    # only draw events between CHARGE and DRY
                    if (self.timeindex[0] == -1 or e >= self.timeindex[0]) and (self.timeindex[6] == 0 or e <= self.timeindex[6]):
                        etype = self.specialeventstype[i]
                        evalue = self.aw.qmc.eventsInternal2ExternalValue(self.specialeventsvalue[i]) * value_factor + value_offset
                        if etype == 0:
                            self.E1.append((etime,evalue))
                        elif etype == 1:
                            self.E2.append((etime,evalue))
                        elif etype == 2:
                            self.E3.append((etime,evalue))
                        elif etype == 3:
                            self.E4.append((etime,evalue))
                except:
                    pass
            # add a last event at DROP/END to extend the lines to the end of roast
            end = (self.timex[-1] if self.timeindex[6] == 0 else self.timex[self.timeindex[6]])
            if self.E1: 
                self.E1.append((end,self.E1[-1][1]))
            if self.E2:
                self.E2.append((end,self.E2[-1][1]))
            if self.E3:
                self.E3.append((end,self.E3[-1][1]))
            if self.E4:
                self.E4.append((end,self.E4[-1][1]))
    
    def startTime(self):
        try:
            return self.timex[self.startTimeIdx]
        except:
            return 0
    
    def endTime(self):
        try:
            return self.timex[self.endTimeIdx]
        except:
            return self.timex[-1]
    
    def setVisible(self,b):
        self.visible = b
        self.updateVisibilities()
    
    def setVisibilities(self,visibilities,event_visibility):
        self.curve_visibilities = visibilities
        self.event_visibility = event_visibility
        self.updateVisibilities()
    
    def updateVisibilities(self):
        visibilities = self.curve_visibilities
        profile_visible = self.visible and self.aligned
        for i,l in enumerate([self.l_temp1,self.l_temp2,self.l_delta1,self.l_delta2]):
            l.set_visible(profile_visible and visibilities[i])
        #
        for i,l in enumerate([self.l_events1,self.l_events2,self.l_events3,self.l_events4]):
            l.set_visible(profile_visible and i+1 == self.event_visibility)
        #
        self.l_mainEvents1.set_visible(False)
        self.l_mainEvents2.set_visible(False)
        if profile_visible and visibilities[4]:
            if self.aw.qmc.swaplcds:
                # prefer the ET over BT
                if visibilities[0]: # ET visible
                    self.l_mainEvents1.set_visible(True) # place the main events on the ET
                    self.l_mainEvents2.set_visible(False)
                elif visibilities[1]: # BT visible
                    self.l_mainEvents2.set_visible(True) # place the main events on the BT
                    self.l_mainEvents1.set_visible(False)
            else:
                # prefer the BT over ET
                if visibilities[1]: # BT visible
                    self.l_mainEvents2.set_visible(True) # place the main events on the BT
                    self.l_mainEvents1.set_visible(False)
                elif visibilities[0]: # ET visible
                    self.l_mainEvents1.set_visible(True) # place the main events on the ET
                    self.l_mainEvents2.set_visible(False)

    def setZorder(self,zorder):
        self.zorder = zorder
        if self.aw.qmc.swaplcds:
            lines = [self.l_mainEvents1,self.l_mainEvents2,self.l_temp1,self.l_temp2,self.l_delta2,self.l_delta1]
        else:
            lines = [self.l_mainEvents2,self.l_mainEvents1,self.l_temp2,self.l_temp1,self.l_delta2,self.l_delta1]
        if self.aw.qmc.swapdeltalcds:
            lines[4] = self.l_delta1
            lines[5] = self.l_delta2
        for i,l in enumerate(lines):
            if l is not None:
                l.set_zorder(self.zorder + self.zorder_offsets[i])
        for l in [self.l_events1,self.l_events2,self.l_events3,self.l_events4]:
            if l is not None:
                l.set_zorder(self.zorder + self.zorder_offsets[6])
    
    # swap alpha values based on self.aw.qmc.swaplcds and self.aw.qmc.swapdeltalcds settings
    def updateAlpha(self):
        alpha = self.alpha[:]
        if self.aw.qmc.swaplcds:
            alpha[0] = self.alpha[1]
            alpha[1] = self.alpha[0]
        if self.aw.qmc.swapdeltalcds:
            alpha[2] = self.alpha[3]
            alpha[3] = self.alpha[2]
        for l,a in zip(
            [self.l_mainEvents2,self.l_temp2,self.l_mainEvents1,self.l_temp1,self.l_delta2,self.l_delta1,self.l_events1,self.l_events2,self.l_events3,self.l_events4],
            [alpha[0],alpha[0],alpha[1],alpha[1],alpha[2],alpha[3],alpha[4],alpha[4],alpha[4],alpha[4]]):
            if l is not None:
                l.set_alpha((a if self.active else a*self.alpha_dim_factor))
    
    def setActive(self,b):
        self.active = b
        self.updateAlpha()
        for l in [self.l_temp1,self.l_temp2,self.l_delta1,self.l_delta2,self.l_mainEvents1,self.l_mainEvents2,self.l_events1,self.l_events2,self.l_events3,self.l_events4]:
            if l is not None:
                if self.active:
                    l.set_color(self.color)
                else:
                    l.set_color(self.gray)
    
    def setTimeoffset(self,offset):
        self.timeoffset = offset
        tempTrans = self.getTempTrans()
        for l in [
            # shifting the temperature curves does not work for some curves that hold many points resulting some at the end being not displayed
            # thus we update the xdata explicitly below
            #self.l_temp1,self.l_temp2,
            self.l_mainEvents1,self.l_mainEvents2,self.l_events1,self.l_events2,self.l_events3,self.l_events4]:
            if l is not None:
                l.set_transform(tempTrans)

        tempTransZero = self.getTempTrans(0)
        for l in [self.l_temp1,self.l_temp2]:
            if l is not None:
                l.set_transform(tempTransZero) # we reset the transformation to avoid a double shift along the timeaxis
                l.set_xdata([x-offset if x is not None else None for x in self.timex])


        # shifting the delta curves does not work for some curves that hold many points resulting some at the end being not displayed
        # thus we update the xdata explicitly below        
#        deltaTrans = self.getDeltaTrans()
#        for l in [self.l_delta1,self.l_delta2]:
#            if l is not None:
#                l.set_transform(deltaTrans)
        deltaTransZero = self.getDeltaTrans(offset=0)
        for l in [self.l_delta1,self.l_delta2]:
            if l is not None:
                l.set_transform(deltaTransZero) # we reset the transformation to avoid a double shift along the timeaxis
                l.set_xdata([x-offset if x is not None else None for x in self.timex])
        
#        # update RoR clippings
#        self.l_delta1_clipping.set_transform(self.getDeltaTrans())
#        self.l_delta1.set_clip_path(self.l_delta1_clipping)
#        self.l_delta2_clipping.set_transform(self.getDeltaTrans())
#        self.l_delta2.set_clip_path(self.l_delta2_clipping)

    # returns the time transformation for the temperature curves
    def getTempTrans(self,offset=None):
        if offset is None:
            offset = self.timeoffset
        # transformation pipelines are processed from left to right so in "A + B" first transformation A then tranformation B is applied (on the result of A)
        # an artist transformation is supplied with data in data coordinates and should return data in display coordinates
        # ax.transData : transforms from data to display coordinates
        # transforms.Affine2D().translate() : applies its transformation
        return transforms.Affine2D().translate(-offset,0) + self.aw.qmc.ax.transData
    
    # returns the time transformation for the delta curves
    def getDeltaTrans(self,offset=None):
        if offset is None:
            offset = self.timeoffset
        return transforms.Affine2D().translate(-offset,0) + self.aw.qmc.delta_ax.transData
    
    def undraw(self):
        for l in [self.l_temp1,self.l_temp2,self.l_delta1,self.l_delta2,self.l_mainEvents1,self.l_mainEvents2,
                self.l_events1,self.l_events2,self.l_events3,self.l_events4]:
            try:
                l.remove()
            except:
                pass
        self.l_temp1 = None
        self.l_temp2 = None
        self.l_delta1 = None
        self.l_delta2 = None
        self.l_mainEvents1 = None
        self.l_mainEvents2 = None
        self.l_events1 = None
        self.l_events2 = None
        self.l_events3 = None
        self.l_events4 = None
        
    def draw(self):
        self.drawBT()
        self.drawET()
        self.drawDeltaBT()
        self.drawDeltaET()
        self.drawMainEvents1()
        self.drawMainEvents2()
        self.drawEvents1()
        self.drawEvents2()
        self.drawEvents3()
        self.drawEvents4()

    def drawBT(self):
        if self.timex is not None and self.stemp2 is not None:
            self.l_temp2, = self.aw.qmc.ax.plot(self.timex,self.stemp2,transform=self.getTempTrans(),markersize=self.aw.qmc.BTmarkersize,marker=self.aw.qmc.BTmarker,visible=(self.visible and self.aligned),
                sketch_params=None,path_effects=[PathEffects.withStroke(linewidth=self.aw.qmc.BTlinewidth+self.aw.qmc.patheffects,foreground=self.aw.qmc.palette["background"])],
                linewidth=self.aw.qmc.BTlinewidth,linestyle=self.aw.qmc.BTlinestyle,drawstyle=self.aw.qmc.BTdrawstyle,
                alpha=(self.alpha[0] if self.active else self.alpha[0]*self.alpha_dim_factor),
                color=(self.color if self.active else self.gray),
                label="{} {}".format(self.label,self.aw.arabicReshape(QApplication.translate("Label", "BT", None))))

    def drawET(self):
        if self.timex is not None and self.stemp1 is not None:
            self.l_temp1, = self.aw.qmc.ax.plot(self.timex,self.stemp1,transform=self.getTempTrans(),markersize=self.aw.qmc.ETmarkersize,marker=self.aw.qmc.ETmarker,visible=(self.visible and self.aligned),
                sketch_params=None,path_effects=[PathEffects.withStroke(linewidth=self.aw.qmc.ETlinewidth+self.aw.qmc.patheffects,foreground=self.aw.qmc.palette["background"])],
                linewidth=self.aw.qmc.ETlinewidth,linestyle=self.aw.qmc.ETlinestyle,drawstyle=self.aw.qmc.ETdrawstyle,
                alpha=(self.alpha[1] if self.active else self.alpha[1]*self.alpha_dim_factor),
                color=(self.color if self.active else self.gray),
                label="{} {}".format(self.label,self.aw.arabicReshape(QApplication.translate("Label", "ET", None))))

    def drawDeltaBT(self):
        if self.timex is not None and self.delta2 is not None:
            # we clip the RoR such that values below 0 are not displayed
#            self.l_delta2_clipping = patches.Rectangle((0,0),self.timex[self.endTimeIdx],self.max_DeltaBT, transform=self.getDeltaTrans())
            self.l_delta2, = self.aw.qmc.ax.plot(self.timex, self.delta2,transform=self.getDeltaTrans(),markersize=self.aw.qmc.BTdeltamarkersize,marker=self.aw.qmc.BTdeltamarker,visible=(self.visible and self.aligned),
                sketch_params=None,path_effects=[PathEffects.withStroke(linewidth=self.aw.qmc.BTdeltalinewidth+self.aw.qmc.patheffects,foreground=self.aw.qmc.palette["background"])],
                linewidth=self.aw.qmc.BTdeltalinewidth,linestyle=self.aw.qmc.BTdeltalinestyle,drawstyle=self.aw.qmc.BTdeltadrawstyle,
                alpha=(self.alpha[2] if self.active else self.alpha[2]*self.alpha_dim_factor),
#                clip_path=self.l_delta2_clipping,clip_on=True,
                color=(self.color if self.active else self.gray),
                label="{} {}".format(self.label,self.aw.arabicReshape(deltaLabelUTF8 + QApplication.translate("Label", "BT", None))))

    def drawDeltaET(self):
        if self.timex is not None and self.delta1 is not None:
            # we clip the RoR such that values below 0 are not displayed
#            self.l_delta1_clipping = patches.Rectangle((0,0),self.timex[self.endTimeIdx],self.max_DeltaET, transform=self.getDeltaTrans())
            self.l_delta1, = self.aw.qmc.ax.plot(self.timex, self.delta1,transform=self.getDeltaTrans(),markersize=self.aw.qmc.ETdeltamarkersize,marker=self.aw.qmc.ETdeltamarker,visible=(self.visible and self.aligned),
                sketch_params=None,path_effects=[PathEffects.withStroke(linewidth=self.aw.qmc.ETdeltalinewidth+self.aw.qmc.patheffects,foreground=self.aw.qmc.palette["background"])],
                linewidth=self.aw.qmc.ETdeltalinewidth,linestyle=self.aw.qmc.ETdeltalinestyle,drawstyle=self.aw.qmc.ETdeltadrawstyle,
                alpha=(self.alpha[3] if self.active else self.alpha[3]*self.alpha_dim_factor),
#                clip_path=self.l_delta1_clipping,clip_on=True,
                color=(self.color if self.active else self.gray),
                label="{} {}".format(self.label,self.aw.arabicReshape(deltaLabelUTF8 + QApplication.translate("Label", "ET", None))))

    def drawMainEvents1(self):
        if self.events_timex is not None and self.events1 is not None:
            self.l_mainEvents1, = self.aw.qmc.ax.plot(self.events_timex,self.events1,transform=self.getTempTrans(),
                markersize=self.aw.qmc.ETlinewidth + 3,marker="o",visible=(self.visible and self.aligned),
                sketch_params=None,
                path_effects=[PathEffects.withStroke(linewidth=self.aw.qmc.ETlinewidth+self.aw.qmc.patheffects,foreground=self.aw.qmc.palette["background"])],
                linewidth=0,linestyle='',
                alpha=(self.alpha[1] if self.active else self.alpha[1]*self.alpha_dim_factor),
                color=(self.color if self.active else self.gray),
#                picker=5, # deprecated in MPL 3.3.x
                picker=True,
                pickradius=5,
                label="{} {}".format(self.label,self.aw.arabicReshape(QApplication.translate("Label", "Events", None))))
            if self.aw.qmc.graphstyle == 1:
                self.l_mainEvents1.set_sketch_params(1,700,12)
    
    def drawMainEvents2(self):
        if self.events_timex is not None and self.events1 is not None:
            self.l_mainEvents2, = self.aw.qmc.ax.plot(self.events_timex,self.events2,transform=self.getTempTrans(),
                markersize=self.aw.qmc.BTlinewidth + 3,marker="o",visible=(self.visible and self.aligned),
                sketch_params=None,
                path_effects=[PathEffects.withStroke(linewidth=self.aw.qmc.BTlinewidth+self.aw.qmc.patheffects,foreground=self.aw.qmc.palette["background"])],
                linewidth=0,linestyle='',
                alpha=(self.alpha[0] if self.active else self.alpha[0]*self.alpha_dim_factor),
                color=(self.color if self.active else self.gray),
#                picker=5, # deprecated in MPL 3.3.x
                picker=True,
                pickradius=5,
                label="{} {}".format(self.label,self.aw.arabicReshape(QApplication.translate("Label", "Events", None))))
            if self.aw.qmc.graphstyle == 1:
                self.l_mainEvents2.set_sketch_params(4,800,20)
    
    # draw event lines n in [0,..,3]
    # returns line
    def drawEvents(self,events,n):
        if events:
            timex,values = zip(*events)
        else:
            timex,values = [],[]
        line, = self.aw.qmc.ax.plot(list(timex), list(values), color=(self.color if self.active else self.gray),
                linestyle="-",drawstyle="steps-post",linewidth = self.aw.qmc.Evaluelinethickness[n],
                alpha = (self.alpha[4] if self.active else self.alpha[4]*self.alpha_dim_factor),
                label = self.aw.qmc.etypesf(n))
        return line

    def drawEvents1(self):
        if self.E1 is not None:
            self.l_events1 = self.drawEvents(self.E1,0)
    
    def drawEvents2(self):
        if self.E2 is not None:
            self.l_events2 =  self.drawEvents(self.E2,1)
    
    def drawEvents3(self):
        if self.E3 is not None:
            self.l_events3 =  self.drawEvents(self.E3,2)
    
    def drawEvents4(self):
        if self.E4 is not None:
            self.l_events4 =  self.drawEvents(self.E4,3)


class CompareTableWidget(QTableWidget):
    deleteKeyPressed = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Delete,Qt.Key_Backspace]:
            self.deleteKeyPressed.emit()
        else:
            super().keyPressEvent(event)
        
    # fails in selectionChanged() if the first row header is clicked repeatedly and reports [0], [1],.. instead of [0],[],..
    def getselectedRowsFast(self):
        selectedRows = []
        for item in self.selectedItems():
            if item.row() not in selectedRows:
                selectedRows.append(item.row())
        if selectedRows == []:
            return self.getLastRow()
        else:
            return selectedRows
    
    def getLastRow(self):
        rows = self.rowCount()
        if rows > 0:
            return [rows-1]
        else:
            return []

class roastCompareDlg(ArtisanDialog):
    def __init__(self, parent = None, aw = None, foreground = None, background = None):
        super(roastCompareDlg,self).__init__(parent, aw)
        
        if platform.system() == 'Darwin':
            self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)
        
        self.setAcceptDrops(True)
        
        self.foreground = foreground
        self.background = background
        self.setWindowTitle(QApplication.translate("Form Caption","Comparator",None))
        self.maxentries = 10 # maxium number of profiles to be compared
        self.basecolors = list(cm.tab10(numpy.linspace(0,1,10)))  # @UndefinedVariable
        self.profiles = []
        self.label_number = 0
        # align line
        self.l_align = None
        # legend
        self.legend = None
        self.legendloc_pos = None
        # table
        self.profileTable = CompareTableWidget()
        self.createProfileTable()
        # buttons
        self.addButton = QPushButton(QApplication.translate("Button","Add",None))
        self.addButton.clicked.connect(self.add)
        self.addButton.setFocusPolicy(Qt.NoFocus)
        self.deleteButton = QPushButton(QApplication.translate("Button","Delete",None))
        self.deleteButton.setFocusPolicy(Qt.NoFocus)
        self.deleteButton.clicked.connect(self.delete)
        # configurations
        alignLabel = QLabel(QApplication.translate("Label","Align",None))
        self.alignnames = [
            QApplication.translate("Label","CHARGE", None),
            QApplication.translate("Label","TP", None),
            QApplication.translate("Label","DRY", None),
            QApplication.translate("Label","FCs", None),
            QApplication.translate("Label","FCe", None),
            QApplication.translate("Label","SCs", None),
            QApplication.translate("Label","SCe", None),
            QApplication.translate("Label","DROP", None),
            ]
        self.alignComboBox = MyQComboBox()
        self.alignComboBox.setFocusPolicy(Qt.NoFocus)
        self.alignComboBox.addItems(self.alignnames)
        self.alignComboBox.setCurrentIndex(self.aw.qmc.compareAlignEvent)
        self.alignComboBox.currentIndexChanged.connect(self.changeAlignEventidx)
        #
        self.etypes = self.aw.qmc.etypes[:-1]
        self.etypes.insert(0,"")
        self.eventsComboBox = MyQComboBox()
        self.eventsComboBox.setFocusPolicy(Qt.NoFocus)
        self.eventsComboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.eventsComboBox.addItems(self.etypes)
        self.eventsComboBox.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
        self.eventsComboBox.setCurrentIndex(self.aw.qmc.compareEvents)
        self.eventsComboBox.currentIndexChanged.connect(self.changeEventsidx)
        #
        self.cb = CheckComboBox(placeholderText="")
        self.cb.setFocusPolicy(Qt.NoFocus)
        self.model = self.cb.model()
        self.cb.addItem(QApplication.translate("Label","ET",None))
        self.model.item(0).setCheckable(True)
        self.cb.setItemCheckState(0,(Qt.Checked if self.aw.qmc.compareET else Qt.Unchecked))
        self.cb.addItem(QApplication.translate("Label","BT",None))
        self.model.item(1).setCheckable(True)
        self.cb.setItemCheckState(1,(Qt.Checked if self.aw.qmc.compareBT else Qt.Unchecked))
        self.cb.addItem(deltaLabelUTF8 + QApplication.translate("Label","ET",None))
        self.model.item(2).setCheckable(True)
        self.cb.setItemCheckState(2,(Qt.Checked if self.aw.qmc.compareDeltaET else Qt.Unchecked))
        self.cb.addItem(deltaLabelUTF8 + QApplication.translate("Label","BT",None))
        self.model.item(3).setCheckable(True)
        self.cb.setItemCheckState(3,(Qt.Checked if self.aw.qmc.compareDeltaBT else Qt.Unchecked))
        self.cb.insertSeparator(4)
        self.cb.addItem(QApplication.translate("CheckBox","Events",None))
        self.model.item(5).setCheckable(True)
        self.cb.setItemCheckState(5,(Qt.Checked if self.aw.qmc.compareMainEvents else Qt.Unchecked))
        self.cb.flagChanged.connect(self.flagChanged)
        
        settings1Layout = QHBoxLayout()
        settings1Layout.addStretch()
        settings1Layout.addWidget(alignLabel)
        settings1Layout.addSpacing(5)
        settings1Layout.addWidget(self.alignComboBox)
        settings1Layout.addStretch()
        
        settings2Layout = QHBoxLayout()
        settings2Layout.addWidget(self.cb)
        settings1Layout.addSpacing(2)
        settings2Layout.addWidget(self.eventsComboBox)
        
        settingsLayout = QVBoxLayout()
        settingsLayout.addLayout(settings2Layout)
        settingsLayout.addLayout(settings1Layout)
        
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addSpacing(10)
        buttonLayout.addWidget(self.deleteButton)
        buttonLayout.addStretch()
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(settingsLayout)
        mainLayout.addWidget(self.profileTable)
        mainLayout.addLayout(buttonLayout)
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(mainLayout)
        
        windowFlags = self.windowFlags()
        windowFlags |= Qt.Tool
        if platform.system() == 'Windows':
            windowFlags |= Qt.WindowMinimizeButtonHint  # Add minimize  button
        self.setWindowFlags(windowFlags)
        
        self.redraw()
        
        self.button_7_org_state_hidden = self.aw.button_7.isHidden() # RESET
        self.button_1_org_state_hidden = self.aw.button_1.isHidden() # ON/OFF
        self.button_2_org_state_hidden = self.aw.button_2.isHidden() # START/STOP
        self.button_10_org_state_hidden = self.aw.button_10.isHidden() # CONTROL
        self.button_18_org_state_hidden = self.aw.button_18.isHidden() # HUD
        
        self.disableButtons()
        self.aw.disableEditMenus(compare=True)
        
        self.pick_handler_id = self.aw.qmc.fig.canvas.mpl_connect('pick_event', self.onpick_event)
        
        settings = QSettings()
        if settings.contains("CompareGeometry"):
            self.restoreGeometry(settings.value("CompareGeometry"))
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and len(urls)>0:
            res = []
            for url in urls:
                if url.scheme() == "file":
                    filename = url.toString(QUrl.PreferLocalFile)
                    qfile = QFileInfo(filename)
                    file_suffix = qfile.suffix()
                    if file_suffix == "alog":
                        res.append(filename)
            if len(res) > 0:
                self.addProfiles(res)
    
    def enableButtons(self):
        if not self.button_7_org_state_hidden:
            self.aw.button_7.show() # RESET
        if not self.button_1_org_state_hidden:
            self.aw.button_1.show() # ON/OFF
        if not self.button_2_org_state_hidden:
            self.aw.button_2.show() # START/STOP
        if not self.button_10_org_state_hidden:
            self.aw.button_10.show() # CONTROL
        if not self.button_18_org_state_hidden:
            self.aw.button_18.show() # HUD
        
    def disableButtons(self):
        self.aw.button_7.hide() # RESET
        self.aw.button_1.hide() # ON/OFF
        self.aw.button_2.hide() # START/STOP
        self.aw.button_10.hide() # CONTROL
        self.aw.button_18.hide() # HUD
    
    ### DRAWING
    
    def onpick_event(self,event):
        p = next((p for p in self.profiles if event.artist in [p.l_mainEvents1,p.l_mainEvents2]), None)
        if p is not None:
            ind = event.ind[0]
            time = p.timex[p.timeindex[ind]]
            if p.timeindex[0] != -1:
                time -= p.timex[p.timeindex[0]]
            temp = self.aw.float2float(p.temp2[p.timeindex[ind]])
            if ind > 0:
                name_idx = ind + 1
            else:
                name_idx = ind
            event_name = self.alignnames[name_idx]
            event_name = self.aw.arabicReshape(event_name)
            self.aw.sendmessage("{}: {} @ {}, {}{}".format(p.label,event_name,stringfromseconds(time,leadingzero=False),temp,self.aw.qmc.mode))
        
    def clearCanvas(self):
    
        rcParams['path.effects'] = []
        if self.aw.qmc.graphstyle == 1:
            scale = 1
        else:
            scale = 0
        length = 700 # 100 (128 the default)
        randomness = 12 # 2 (16 default)
        rcParams['path.sketch'] = (scale, length, randomness)
                
        if self.aw.qmc.ax is None:
            self.aw.qmc.ax = self.aw.qmc.fig.add_subplot(111,facecolor=self.aw.qmc.palette["background"])
        if self.aw.qmc.delta_ax is None:
            self.aw.qmc.delta_ax = self.aw.qmc.ax.twinx()

        self.aw.qmc.fig.suptitle("")
        self.aw.qmc.ax.set_title("")
        self.aw.qmc.ax.clear()
        self.aw.qmc.ax.set_facecolor(self.aw.qmc.palette["background"])
        self.aw.qmc.delta_ax.clear()
        self.aw.qmc.ax.set_ylim(self.aw.qmc.ylimit_min, self.aw.qmc.ylimit)
        grid_axis = None
        if self.aw.qmc.temp_grid and self.aw.qmc.time_grid:
            grid_axis = 'both'
        elif self.aw.qmc.temp_grid:
            grid_axis = 'y'
        elif self.aw.qmc.time_grid:
            grid_axis = 'x'
        if grid_axis is not None:
            self.aw.qmc.ax.grid(True,axis=grid_axis,color=self.aw.qmc.palette["grid"],linestyle=self.aw.qmc.gridstyles[self.aw.qmc.gridlinestyle],linewidth = self.aw.qmc.gridthickness,alpha = self.aw.qmc.gridalpha,sketch_params=0,path_effects=[])

        prop = self.aw.mpl_fontproperties.copy()
        prop.set_size("small")
        fontprop_medium = self.aw.mpl_fontproperties.copy()
        fontprop_medium.set_size("medium")
        fontprop_large = self.aw.mpl_fontproperties.copy()
        fontprop_large.set_size("large")
        
        self.aw.qmc.ax.set_ylabel(self.aw.qmc.mode,color=self.aw.qmc.palette["ylabel"],rotation=0,labelpad=10,fontproperties=fontprop_large)
        self.aw.qmc.ax.set_xlabel(self.aw.arabicReshape(QApplication.translate("Label", "min",None)),color = self.aw.qmc.palette["xlabel"],fontproperties=fontprop_medium)

        tick_dir = 'inout'
        self.aw.qmc.ax.tick_params(\
            axis='x',           # changes apply to the x-axis
            which='both',       # both major and minor ticks are affected
            bottom=True,        # ticks along the bottom edge are on
            top=False,          # ticks along the top edge are off
            direction=tick_dir,
            labelbottom=True)   # labels along the bottom edge are on
        self.aw.qmc.ax.tick_params(\
            axis='y',           # changes apply to the y-axis
            which='both',       # both major and minor ticks are affected
            right=False,
            bottom=True,        # ticks along the bottom edge are on
            top=False,          # ticks along the top edge are off
            direction=tick_dir,
            labelbottom=True)   # labels along the bottom edge are on 
        
        for label in self.aw.qmc.ax.get_xticklabels() :
            label.set_fontproperties(prop)
        for label in self.aw.qmc.ax.get_yticklabels() :
            label.set_fontproperties(prop)

        # format temperature as int, not float in the cursor position coordinate indicator
        self.aw.qmc.ax.fmt_ydata = self.aw.qmc.fmt_data
        self.aw.qmc.ax.fmt_xdata = self.aw.qmc.fmt_timedata

        self.aw.qmc.ax.set_zorder(self.aw.qmc.delta_ax.get_zorder()+1) # put ax in front of delta_ax (which remains empty!)
        #create a second set of axes in the same position as self.ax
        self.aw.qmc.delta_ax.tick_params(\
            axis='y',           # changes apply to the y-axis
            which='both',       # both major and minor ticks are affected
            left=False,         # ticks along the left edge are off
            bottom=False,       # ticks along the bottom edge are off
            top=False,          # ticks along the top edge are off
            direction="inout", # tick_dir # this does not work as ticks are not drawn at all in ON mode with this!?
            labelright=True,
            labelleft=False,
            labelbottom=False)   # labels along the bottom edge are on

        self.aw.qmc.ax.patch.set_visible(True)
        self.aw.qmc.delta_ax.set_ylabel(self.aw.qmc.mode + self.aw.arabicReshape(QApplication.translate("Label", "/min", None)),color = self.aw.qmc.palette["ylabel"],fontproperties=fontprop_large)
        self.aw.qmc.delta_ax.set_ylim(self.aw.qmc.zlimit_min,self.aw.qmc.zlimit)
        self.aw.qmc.delta_ax.yaxis.set_major_locator(ticker.MultipleLocator(self.aw.qmc.zgrid))
        self.aw.qmc.delta_ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        for i in self.aw.qmc.delta_ax.get_yticklines():
            i.set_markersize(10)
        for i in self.aw.qmc.delta_ax.yaxis.get_minorticklines():
            i.set_markersize(5)
        for label in self.aw.qmc.delta_ax.get_yticklabels() :
            label.set_fontproperties(prop)

        # translate y-coordinate from delta into temp range to ensure the cursor position display (x,y) coordinate in the temp axis
        self.aw.qmc.delta_ax.fmt_ydata = self.aw.qmc.fmt_data
        self.aw.qmc.delta_ax.fmt_xdata = self.aw.qmc.fmt_timedata

        self.aw.qmc.ax.spines['top'].set_color("0.40")
        self.aw.qmc.ax.spines['bottom'].set_color("0.40")
        self.aw.qmc.ax.spines['left'].set_color("0.40")
        self.aw.qmc.ax.spines['right'].set_color("0.40")

        self.aw.qmc.ax.yaxis.set_major_locator(ticker.MultipleLocator(self.aw.qmc.ygrid))
        self.aw.qmc.ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        for i in self.aw.qmc.ax.get_yticklines():
            i.set_markersize(10)
        for i in self.aw.qmc.ax.yaxis.get_minorticklines():
            i.set_markersize(5)

        #update X ticks, labels, and colors
        self.aw.qmc.xaxistosm()
    
    # draw time alignment vertical line
    def drawAlignmentLine(self):
        self.l_align = self.aw.qmc.ax.axvline(0,
            color=self.aw.qmc.palette["grid"],
            linestyle=self.aw.qmc.gridstyles[self.aw.qmc.gridlinestyle],
            zorder=0,
            linewidth = self.aw.qmc.gridthickness*2,sketch_params=0,
            path_effects=[])
    
    def drawLegend(self):
        if self.aw.qmc.legendloc:
            if self.legend is None:
                if self.legendloc_pos is None:
                    loc = self.aw.qmc.legendloc
                else:
                    loc = self.legendloc_pos
            else:
                loc = self.legend._loc
            handles = []
            labels = []
            for p in self.profiles:
                if p.visible and p.aligned:
                    if self.aw.qmc.swaplcds:
                        lines = [p.l_temp1,p.l_temp2,p.l_delta1,p.l_delta2,p.l_events1,p.l_events2,p.l_events3,p.l_events4]
                    else:
                        lines = [p.l_temp2,p.l_temp1,p.l_delta2,p.l_delta1,p.l_events1,p.l_events2,p.l_events3,p.l_events4]
                    for l in lines:
                        if l.get_visible():
                            handles.append(l)
                            labels.append(p.label)
                            break
            if len(handles) > 0:
                prop = self.aw.mpl_fontproperties.copy()
                prop.set_size("x-small")
                self.legend = self.aw.qmc.ax.legend(handles,labels,loc=loc,
                    #ncol=ncol,
                    fancybox=True,prop=prop,shadow=False,frameon=True)
                try:
                    self.legend.set_in_layout(False) # remove legend from tight_layout calculation
                except: # set_in_layout not available in mpl<3.x
                    pass
                try:
                    self.legend.set_draggable(state=True,use_blit=True)  #,update='bbox')
                except: # not available in mpl<3.x
                    self.legend.draggable(state=True) # for mpl 2.x
                frame = self.legend.get_frame()
                frame.set_facecolor(self.aw.qmc.palette["legendbg"])
                frame.set_alpha(self.aw.qmc.alpha["legendbg"])
                frame.set_edgecolor(self.aw.qmc.palette["legendborder"])
                frame.set_linewidth(0.5)
                for line,text in zip(self.legend.get_lines(), self.legend.get_texts()):
                    text.set_color(line.get_color())
            else:
                if self.legend is not None:
                    self.legend.remove()
        else:
            if self.legend is not None:
                self.legend.remove()
            self.legend = None
    
    def repaint(self):
        self.drawLegend()
        self.aw.qmc.placelogoimage()
        self.aw.qmc.fig.canvas.draw()
        
    def redraw(self):
        self.clearCanvas()
        self.drawAlignmentLine()
        self.recompute()
        for rp in self.profiles:
            rp.draw()
            rp.updateAlpha()
        self.realign()
        self.updateZorders()
        self.repaint()
    
    ### Table
    
    def setProfileTableRow(self,i):
        profile = self.profiles[i]
        c = QColor.fromRgbF(*profile.color)
        color = QTableWidgetItem()
        color.setBackground(c)
        color.setFlags(Qt.ItemIsEnabled) # do not change background color on row selection of the color items
        self.profileTable.setItem(i,0,color)
        flag = QCheckBox()
        flag.setChecked(profile.visible)
        flag.stateChanged.connect(self.visibilityChanged)
        flagWidget = QWidget()
        flagLayout = QHBoxLayout(flagWidget)
        flagLayout.addWidget(flag)
        flagLayout.setAlignment(Qt.AlignCenter|Qt.AlignVCenter)
        flagLayout.setContentsMargins(0,0,0,0)
        self.profileTable.setCellWidget(i,1,flagWidget)
        title_item = QTableWidgetItem(profile.title)
        tooltip = self.renderToolTip(profile)
        if tooltip is not None and tooltip != "":
            title_item.setToolTip(tooltip)
        self.profileTable.setItem(i,2,title_item)
        header = QTableWidgetItem(profile.label)
        self.profileTable.setVerticalHeaderItem(i,header)
    
    def renderToolTip(self,profile):
        tooltip = ""
        if profile.metadata is not None:
            try:
                if "roastdate" in profile.metadata:
                    tooltip = profile.metadata["roastdate"].date().toString()
                    tooltip += ", " + profile.metadata["roastdate"].time().toString()[:-3]
                if "weight" in profile.metadata:
                    if tooltip != "":
                        tooltip += "\n"
                    tooltip += profile.metadata["weight"]
                if "beans" in profile.metadata:
                    if "weight" in profile.metadata:
                        tooltip += " "
                    elif tooltip != "":
                        tooltip += "\n"
                    tooltip += profile.metadata["beans"].strip()
                    if "moisture_greens" in profile.metadata:
                        tooltip += " (%g%%)" % self.aw.float2float(profile.metadata["moisture_greens"])
                if "ambientTemp" in profile.metadata:
                    if tooltip != "":
                        tooltip += "\n"
                    tooltip += profile.metadata["ambientTemp"]
                if "ambient_humidity" in profile.metadata:
                    if "ambientTemp" in profile.metadata:
                        tooltip += ", "
                    elif tooltip != "":
                        tooltip += "\n"
                    tooltip += profile.metadata["ambient_humidity"]
                if "ambient_pressure" in profile.metadata:
                    if "ambientTemp" in profile.metadata or "ambient_humidity" in profile.metadata:
                        tooltip += ", "
                    elif tooltip != "":
                        tooltip += "\n"
                    tooltip += profile.metadata["ambient_pressure"]
                if "weight_loss" in profile.metadata:
                    if tooltip != "":
                        tooltip += "\n"
                    tooltip += profile.metadata["weight_loss"]
                if "ground_color" in profile.metadata:
                    if "weight_loss" in profile.metadata:
                        tooltip += ", "
                    elif tooltip != "":
                        tooltip += "\n"
                    tooltip += profile.metadata["ground_color"]
                if "AUC" in profile.metadata:
                    if "weight_loss" in profile.metadata or "ground_color" in profile.metadata:
                        tooltip += ", "
                    elif tooltip != "":
                        tooltip += "\n"
                    tooltip += profile.metadata["AUC"]
                if "roastingnotes" in profile.metadata:
                    if tooltip != "":
                        tooltip += "\n"
                    tooltip += profile.metadata["roastingnotes"].strip()
                if "cuppingnotes" in profile.metadata:
                    if tooltip != "":
                        tooltip += "\n"
                    tooltip += profile.metadata["cuppingnotes"].strip()
            except:
#                import traceback
#                import sys
#                traceback.print_exc(file=sys.stdout)
                pass
        return tooltip.strip()
    
    def createProfileTable(self):
        try:
            self.profileTable.clear()
            self.profileTable.setTabKeyNavigation(True)
            self.profileTable.setColumnCount(3)
            self.profileTable.setAlternatingRowColors(True)
#            self.profileTable.setEditTriggers(QTableWidget.NoEditTriggers) # we allow the editing/renaming of items
            self.profileTable.setSelectionBehavior(QTableWidget.SelectRows)
            self.profileTable.setSelectionMode(QTableWidget.MultiSelection)
            self.profileTable.setShowGrid(False)
            self.profileTable.verticalHeader().setSectionResizeMode(2)
#            self.profileTable.horizontalHeader().setVisible(False)
            self.profileTable.setHorizontalHeaderLabels(["",
                                                         QApplication.translate("Label","ON",None),
                                                         QApplication.translate("Label","Title",None)])
            self.profileTable.horizontalHeader().sectionClicked.connect(self.columnHeaderClicked)
            self.profileTable.setCornerButtonEnabled(True) # click in the left header corner selects all entries in the table
            self.profileTable.setSortingEnabled(False)
            
            self.profileTable.verticalHeader().setSectionsMovable(True)
            self.profileTable.verticalHeader().setDragDropMode(QTableWidget.InternalMove)
            self.profileTable.verticalHeader().sectionMoved.connect(self.sectionMoved)
            self.profileTable.verticalHeader().sectionDoubleClicked.connect(self.tableSectionClicked)
            
            self.profileTable.itemSelectionChanged.connect(self.selectionChanged)
            self.profileTable.deleteKeyPressed.connect(self.deleteSelected)
            
            header = self.profileTable.horizontalHeader()
            header.setStretchLastSection(True)
            header.setMinimumSectionSize(10)       # color column size
            self.profileTable.setColumnWidth(0,10) # color column size
            header.setSectionResizeMode(0, QHeaderView.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            
            self.profileTable.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.profileTable.horizontalScrollBar().setEnabled(False)
            self.profileTable.setAutoScroll(False) # disable scrolling to selected cell

        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate("Error Message","Exception:",None) + " createProfileTable() {0}").format(str(ex)),exc_tb.tb_lineno)
    
    ### SLOTS
    
    @pyqtSlot(int)
    def columnHeaderClicked(self,i):
        if i == 1: # flag header clicked
            if all(p.visible for p in self.profiles):
                new_state = False
            else:
                new_state = True
            for r in range(self.profileTable.rowCount()):
                layout = self.profileTable.cellWidget(r,1).layout()
                flag = layout.itemAt(0).widget()
                flag.blockSignals(True)
                flag.setChecked(new_state)
                flag.blockSignals(False)
                self.profiles[r].setVisible(new_state)
            # update chart
            self.updateDeltaLimits()
            self.autoTimeLimits()
            self.repaint()
        elif i == 2: # title header clicked
            selected = self.profileTable.selectedRanges()
            if selected and len(selected) > 0:
                # disable selection
                self.profileTable.clearSelection()
            else:
                # select all
                self.profileTable.selectAll()
    
    @pyqtSlot(int,int,int)
    def sectionMoved(self,logicalIndex, oldVisualIndex, newVisualIndex):
        self.updateAlignMenu()
        self.realign(updateDeltaAxis=False)
        self.updateZorders()
        self.repaint()
    
    @pyqtSlot(int)
    def visibilityChanged(self,state):
        i = self.aw.findWidgetsRow(self.profileTable,self.sender(),1)
        self.profiles[i].setVisible(bool(state))
        self.updateDeltaLimits()
        self.autoTimeLimits()
        self.repaint()
    
    @pyqtSlot(int,bool)
    def flagChanged(self,i,b):
        if i == 0:
            self.aw.qmc.compareET = b
        elif i == 1:
            self.aw.qmc.compareBT = b
        elif i == 2:
            self.aw.qmc.compareDeltaET = b
        elif i == 3:
            self.aw.qmc.compareDeltaBT = b
        elif i == 5:
            self.aw.qmc.compareMainEvents = b
        self.updateDeltaLimits()
        self.updateVisibilities()
        self.repaint()
    
    @pyqtSlot(int)
    def changeAlignEventidx(self,i):
        if self.aw.qmc.compareAlignEvent != i:
            self.aw.qmc.compareAlignEvent = i
            self.realign()
            self.repaint()
    
    @pyqtSlot(int)
    def changeEventsidx(self,i):
        self.aw.qmc.compareEvents = i
        self.updateVisibilities()
        self.repaint()
    
    @pyqtSlot()
    def selectionChanged(self):
        selected = [self.aw.findWidgetsRow(self.profileTable,si,2) for si in self.profileTable.selectedItems()]
#        selected = self.profileTable.getselectedRowsFast() # does return [1],[2],[1],.. on repeated clicks on the row header of the first entry insteadd of [1],[0],[1],..
        for i,p in enumerate(self.profiles):
            if selected and not i in selected:
                p.setActive(False)
            else:
                p.setActive(True)
        self.updateProfileTableColors()
        self.repaint()
    
    @pyqtSlot(int)
    def tableSectionClicked(self,i):
        app = QCoreApplication.instance()
        fileURL = QUrl.fromLocalFile(self.profiles[i].filepath)
        if platform.system() == "Windows" and not app.artisanviewerMode:
            self.aw.app.sendMessage2ArtisanInstance(fileURL.toString(),app._viewer_id)
        else:
            QDesktopServices.openUrl(fileURL)

    @pyqtSlot()
    def deleteSelected(self):
        self.deleteProfiles(self.profileTable.getselectedRowsFast())
    
    @pyqtSlot(bool)
    def add(self,_=False):
        filenames = self.aw.reportFiles()
        if filenames:
            self.addProfiles(filenames)
            
    @pyqtSlot(bool)
    def delete(self,_=False):
        self.deleteProfiles(self.profileTable.getselectedRowsFast())

    ### UPDATE functions

    def updateDeltaLimits(self):
        # update delta max limit in auto mode
        if (self.aw.qmc.autodeltaxET or self.aw.qmc.autodeltaxBT):
            dmax = 0
            for rp in self.profiles:
                if rp.visible and rp.aligned:
                    if (self.cb.itemCheckState(2) == Qt.Checked and self.aw.qmc.autodeltaxET) or \
                        (self.cb.itemCheckState(2) == Qt.Checked and self.cb.itemCheckState(3) != Qt.Checked and self.aw.qmc.autodeltaxBT): # DeltaET
                        dmax = max(dmax,rp.max_DeltaET)
                    if (self.cb.itemCheckState(3) == Qt.Checked and self.aw.qmc.autodeltaxBT) or \
                        (self.cb.itemCheckState(3) == Qt.Checked and self.cb.itemCheckState(2) != Qt.Checked and self.aw.qmc.autodeltaxET) : # DeltaBT
                        dmax = max(dmax,rp.max_DeltaBT)
            if dmax > 0:
                self.aw.qmc.delta_ax.set_ylim(top=dmax) # we only autoadjust the upper limit
    
    def recompute(self):
        for rp in self.profiles:
            rp.recompute()
    
    def updateZorders(self):
        profiles = self.getProfilesVisualOrder()
        profiles.reverse()
        zorder = 0
        for rp in profiles:
            rp.setZorder(zorder)
            zorder += 1
    
    def updateVisibilities(self):
        for p in self.profiles:
            p.setVisibilities([
                self.cb.itemCheckState(0) == Qt.Checked, # ET
                self.cb.itemCheckState(1) == Qt.Checked, # BT
                self.cb.itemCheckState(2) == Qt.Checked, # DeltaET
                self.cb.itemCheckState(3) == Qt.Checked, # DeltaBT
                self.cb.itemCheckState(5) == Qt.Checked, # Main events
                ],self.aw.qmc.compareEvents)

    def updateAlignMenu(self):
        top = self.getTopProfileVisualOrder()
        if top:
            model = self.alignComboBox.model()
            for i in range(model.rowCount()):
                if len(top.timeindex) > i and ((i == 0 and top.timeindex[i] != -1) or (i==1 and top.TP != 0) or (i>1 and top.timeindex[i-1] > 0)):
                    model.item(i).setEnabled(True)
                else:
                    model.item(i).setEnabled(False)
    
    def updateProfileTableItems(self):
        for i,p in enumerate(self.profiles):
            w = self.profileTable.item(i,2)
            if w is not None:
                if p.aligned:
                    if sys.platform.startswith("darwin") and darkdetect.isDark() and appFrozen():
                        w.setForeground(Qt.white)
                    else:
                        w.setForeground(Qt.black)
                else:
                    w.setForeground(Qt.lightGray)
    
    def updateProfileTableColors(self):
        for i,p in enumerate(self.profiles):
            w = self.profileTable.item(i,0)
            if w is not None:
                if p.active:
                    c = QColor.fromRgbF(*p.color)
                else:
                    c = QColor.fromRgbF(*p.gray).lighter()
                w.setBackground(c)
    
    # align all profiles to the first one w.r.t. to the event self.aw.qmc.compareAlignEvent
    #   0:CHARGE, 1:TP, 2:DRY, 3:FCs, 4:FCe, 5:SCs, 6:SCe, 7:DROP
    def realign(self,updateDeltaAxis=True):
        if len(self.profiles) > 0:
            profiles = self.getProfilesVisualOrder()
            # align top profile to its CHARGE event or first reading to 00:00
            top = profiles[0] # profile on top of the table / chart
            delta = top.startTime()
            top.setTimeoffset(delta)
            top.aligned = True
            # we calculate the min/max timex to to show all data considering this alignment to automatically set the time axis limits
            top.min_time = 0
            top.max_time = top.endTime() - delta
            # align all other profiles to the top profile w.r.t. self.aw.qmc.compareAlignEvent
            if self.aw.qmc.compareAlignEvent == 0:
                refTime = 0
            elif self.aw.qmc.compareAlignEvent == 1: # TP
                refTime = top.TP
            elif self.aw.qmc.compareAlignEvent>1 and top.timeindex[self.aw.qmc.compareAlignEvent-1] > 0:
                refTime = top.timex[top.timeindex[self.aw.qmc.compareAlignEvent-1]] - delta
            else:
                # no reference point to align the other profiles too!
                if self.l_align is not None:
                    self.l_align.set_visible(False)
                return
            if self.l_align is not None:
                self.l_align.set_xdata(refTime)
                self.l_align.set_visible(True)
            for p in profiles[1:]:
                if (self.aw.qmc.compareAlignEvent == 0 and p.timeindex[0] != -1):
                    eventTime = p.timex[p.timeindex[self.aw.qmc.compareAlignEvent]]
                    delta = eventTime - refTime
                    p.setTimeoffset(delta)
                    p.aligned = True
                    p.min_time = refTime - eventTime + p.startTime()
                    p.max_time = p.endTime() - eventTime + refTime
                elif self.aw.qmc.compareAlignEvent==1 and p.TP > 0:
                    p_offset = 0
                    if p.timeindex[0]>-1:
                        p_offset = p.timex[p.timeindex[0]]
                    eventTime = p.TP + p_offset
                    delta = eventTime - refTime
                    p.setTimeoffset(delta)
                    p.aligned = True
                    p.min_time = refTime - eventTime + p.startTime()
                    p.max_time = p.endTime() - eventTime + refTime
                elif self.aw.qmc.compareAlignEvent>1 and p.timeindex[self.aw.qmc.compareAlignEvent-1] > 0:
                    eventTime = p.timex[p.timeindex[self.aw.qmc.compareAlignEvent-1]]
                    delta = eventTime - refTime
                    p.setTimeoffset(delta)
                    p.aligned = True
                    p.min_time = refTime - eventTime + p.startTime()
                    p.max_time = p.endTime() - eventTime + refTime
                elif (self.aw.qmc.compareAlignEvent == 0 or (self.aw.qmc.compareAlignEvent == 1 and top.TP == 0) or \
                        (self.aw.qmc.compareAlignEvent>1 and top.timeindex[self.aw.qmc.compareAlignEvent-1] == 0)):
                    # align to CHARGE or first reading
                    if p.timeindex[0] != -1:
                        eventTime = p.timex[p.timeindex[0]]
                    else:
                        eventTime = p.timex[0]
                    delta = eventTime - refTime
                    p.setTimeoffset(delta)
                    p.aligned = True
                    p.min_time = refTime - eventTime + p.startTime()
                    p.max_time = p.endTime() - eventTime + refTime
                else:
                    p.aligned = False
            self.updateVisibilities()
            self.autoTimeLimits()
            self.updateProfileTableItems()
            self.updateDeltaLimits()
    
    ### ADD/DELETE table items
    
    def addProfile(self,filename,active):
        try:
            self.profiles
            if len(self.profiles) < self.maxentries and not any(filename == p.filepath for p in self.profiles):
                f = QFile(filename)
                if not f.open(QFile.ReadOnly):
                    raise IOError(f.errorString())
                stream = QTextStream(f)
                firstChar = stream.read(1)
                if firstChar == "{":
                    f.close()
                    obj = self.aw.deserialize(filename)
                    # assign next color
                    rp = RoastProfile(self.aw,obj,filename,self.basecolors[0])
                    self.basecolors = self.basecolors[1:] # remove used color from list of available basecolors
                    # set default label number if no batch number is available
                    if rp.label == "":
                        self.label_number += 1
                        rp.label = str(self.label_number)
                    # set initially inactive if currently any another profile is selected
                    rp.setActive(active)
                    # add profile to the list
                    self.profiles.append(rp)
                    # add profile to the table
                    self.profileTable.setRowCount(len(self.profiles))
                    self.setProfileTableRow(len(self.profiles)-1)
        except:
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            pass
    
    def addProfiles(self,filenames):
        if filenames:
            selected = [self.aw.findWidgetsRow(self.profileTable,si,2) for si in self.profileTable.selectedItems()]
            for filename in filenames:
                self.addProfile(filename,not bool(selected))
            self.updateAlignMenu()
            self.realign()
            self.updateZorders()
            self.repaint()
    
    def deleteProfile(self,i):
        self.profileTable.removeRow(i)
        p = self.profiles[i]
        self.basecolors.append(p.color) # we add the color back to the list of available ones
        self.profiles.remove(p)
        p.undraw()
    
    def deleteProfiles(self,indices):
        if indices and len(indices) > 0:
            for i in sorted(indices,reverse=True):
                self.deleteProfile(i)
            self.updateAlignMenu()
            self.realign()
            self.updateZorders()
            self.repaint()
    
    ### Utility
    
    def getTopProfileVisualOrder(self):
        for i,p in enumerate(self.profiles):
            if self.profileTable.visualRow(i) == 0:
                return p
        return None
        
    def getProfilesVisualOrder(self):
        res = self.profiles[:]
        for i,p in enumerate(self.profiles):
            res[self.profileTable.visualRow(i)] = p
        return res
   
    def autoTimeLimits(self):
        if self.aw.qmc.autotimex:
            min_timex = None
            max_timex = None
            for p in self.profiles:
                if p.visible and p.aligned:
                    if min_timex is None:
                        min_timex = p.min_time
                    else:
                        min_timex = min(min_timex,p.min_time)
                    if max_timex is None:
                        max_timex = p.max_time
                    else:
                        max_timex = max(max_timex,p.max_time)
            if min_timex is not None and max_timex is not None:
                min_timex = min_timex - 30
                max_timex = max_timex + 30
                self.aw.qmc.xaxistosm(min_time=min_timex, max_time=max_timex)

    def closeEvent(self, _):
        #disconnect pick handler
        self.aw.qmc.fig.canvas.mpl_disconnect(self.pick_handler_id)
        #save window geometry
        settings = QSettings()
        settings.setValue("CompareGeometry",self.saveGeometry())
        self.aw.comparator = None
        self.aw.roastCompareAction.setChecked(False)
        self.aw.qmc.reset()
        if self.foreground is not None and self.foreground.strip() != "":
            self.aw.loadFile(self.foreground)
        if self.background is not None and self.background.strip() != "":
            self.aw.loadbackground(self.background)
            self.aw.qmc.background = True
            self.aw.qmc.timealign(redraw=False)
            self.aw.qmc.redraw()
        if (self.foreground is None or self.foreground.strip() == "") and (self.background is None or self.background.strip() == ""):
            #selected = [self.aw.findWidgetsRow(self.profileTable,si,2) for si in self.profileTable.selectedItems()]
            selected = self.profileTable.getselectedRowsFast()
            if len(selected) == 1:
                self.aw.loadFile(self.profiles[selected[0]].filepath)
        else:
            self.aw.qmc.timealign()
        self.enableButtons()
        self.aw.enableEditMenus()