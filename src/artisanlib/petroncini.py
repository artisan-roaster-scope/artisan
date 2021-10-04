# -*- coding: utf-8 -*-
#
# ABOUT
# Petroncini CSV Roast Profile importer for Artisan

import io
import csv
import time as libtime

from artisanlib.util import fill_gaps, encodeLocal

try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtCore import QDateTime, QDate, QTime, Qt # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except Exception:
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import QDateTime, QDate, QTime, Qt # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport

def replace_duplicates(data):
    lv = -1
    data_core = []
    for v in data:
        if v == lv:
            data_core.append(-1)
        else:
            data_core.append(v)
            lv = v
    # reconstruct first and last reading
    if len(data)>0:
        data_core[-1] = data[-1]
    return fill_gaps(data_core)

# returns a dict containing all profile information contained in the given IKAWA CSV file
def extractProfilePetronciniCSV(file,_):
    res = {} # the interpreted data set

    res["samplinginterval"] = 1.0

    with io.open(file, 'r', newline="",encoding='utf-8') as csvFile:
        data = csv.reader(csvFile,delimiter=';')
        #read file header
        next(data) # skip "Export path"
        next(data) # skip path
        header = [i.strip() for i in next(data)]
        
        roast_date = None
        power = None # holds last processed heater event value
        power_last = None # holds the heater event value before the last one
        power_event = False # set to True if a heater event exists
        specialevents = []
        specialeventstype = []
        specialeventsvalue = []
        specialeventsStrings = []
        timex = []
        temp1 = [] # outlet temperature as ET
        temp2 = [] # bean temperature
        extra1 = [] # inlet temperature
        extra2 = [] # burner percentage
        timeindex = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actal index used
        i = 0
        for row in data:
            if row == []:
                continue
            i = i + 1
            items = list(zip(header, row))
            item = {}
            for (name, value) in items:
                item[name] = value.strip()
            # take i as time in seconds
            timex.append(i)
            # extract roast_date
            if roast_date is None and 'Year' in item and 'Month' in item and 'Day' in item and 'Hour' in item and 'Minute' in item and 'Second' in item:
                try:
                    date = QDate(int(item['Year']),int(item['Month']),int(item['Day']))
                    time = QTime(int(item['Hour']),int(item['Minute']),int(item['Second']))
                    roast_date = QDateTime(date,time)
                except Exception:  # pylint: disable=broad-except
                    pass
            #
            if 'Outlet Temperature' in item:
                temp1.append(float(item['Outlet Temperature']))
            else:
                temp1.append(-1)
            if 'Beans Temperature' in item:
                temp2.append(float(item['Beans Temperature'].replace(",",".")))
            else:
                temp2.append(-1)
            # mark CHARGE
            if not timeindex[0] > -1:
                timeindex[0] = i
            # mark DROP
            if timeindex[0] > -1 and i>0:
                timeindex[6] = i-1
            # add ror, power, speed and pressure
            if 'Inlet Temperature' in item:
                extra1.append(float(item['Inlet Temperature']))
            else:
                extra1.append(-1)
            if 'Burner Percentage' in item:
                extra2.append(float(item['Burner Percentage']))
            else:
                extra2.append(-1)
    
            if "Burner Percentage" in item:
                try:
                    v = float(item["Burner Percentage"])
                    if v != power:
                        # power value changed
                        if v == power_last:
                            # just a fluctuation, we remove the last added power value again
                            power_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 3)
                            del specialeventsvalue[power_last_idx]
                            del specialevents[power_last_idx]
                            del specialeventstype[power_last_idx]
                            del specialeventsStrings[power_last_idx]
                            power = power_last
                            power_last = None
                        else:
                            power_last = power
                            power = v
                            power_event = True
                            v = v/10. + 1
                            specialeventsvalue.append(v)
                            specialevents.append(i)
                            specialeventstype.append(3)
                            specialeventsStrings.append(item["power"] + "%")
                    else:
                        power_last = None
                except Exception:  # pylint: disable=broad-except
                    pass
            
    res["timex"] = timex
    res["temp1"] = replace_duplicates(temp1)
    res["temp2"] = replace_duplicates(temp2)
    res["timeindex"] = timeindex
    
    res["extradevices"] = [25]
    res["extratimex"] = [timex[:]]
    
    res["extraname1"] = ["IT"]
    res["extratemp1"] = [extra1]
    res["extramathexpression1"] = [""]  
    
    res["extraname2"] = ["burner"]
    res["extratemp2"] = [replace_duplicates(extra2)]
    res["extramathexpression2"] = [""]
    
    
    # set date
    if roast_date is not None and roast_date.isValid():
        res["roastdate"] = encodeLocal(roast_date.date().toString())
        res["roastisodate"] = encodeLocal(roast_date.date().toString(Qt.DateFormat.ISODate))
        res["roasttime"] = encodeLocal(roast_date.time().toString())
        res["roastepoch"] = int(roast_date.toSecsSinceEpoch())
        res["roasttzoffset"] = libtime.timezone    
    
    if len(specialevents) > 0:
        res["specialevents"] = specialevents
        res["specialeventstype"] = specialeventstype
        res["specialeventsvalue"] = specialeventsvalue
        res["specialeventsStrings"] = specialeventsStrings
        if power_event:
            # first set etypes to defaults
            res["etypes"] = [QApplication.translate("ComboBox", "Air"),
                             QApplication.translate("ComboBox", "Drum"),
                             QApplication.translate("ComboBox", "Damper"),
                             QApplication.translate("ComboBox", "Burner"),
                             "--"]
    return res

# roast date raus lesen
                