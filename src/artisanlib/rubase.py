# -*- coding: utf-8 -*-
#
# ABOUT
# RUBASE CSV Roast Profile importer for Artisan

import os
import io
import csv

try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except:
    #pylint: disable = E, W, R, C
    from PyQt5.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport


# returns a dict containing all profile information contained in the given Rubase CSV file
def extractProfileRubaseCSV(file,aw):
    res = {} # the interpreted data set

    res["samplinginterval"] = 1.0
    # set profile date from the file name if it has the format "IKAWA yyyy-mm-dd hhmmss.csv"
    filename = os.path.basename(file)
    res["title"] = filename

    with io.open(file, 'r', newline="",encoding='utf-8') as csvFile:
        data = csv.reader(csvFile,delimiter=',')
        #read file header
        header_row = next(data)
        header = ["time","BT","Fan","Heater","RoR","Drum","Humidity","ET","Pressure"]
        
        fan = None # holds last processed fan event value
        fan_last = None # holds the fan event value before the last one
        heater = None # holds last processed heater event value
        heater_last = None # holds the heater event value before the last one
        fan_event = False # set to True if a fan event exists
        heater_event = False # set to True if a heater event exists
        
        specialevents = []
        specialeventstype = []
        specialeventsvalue = []
        specialeventsStrings = []
        timex = []
        temp1 = []
        temp2 = []
        extra1 = []
        extra2 = []
        extra3 = []
        extra4 = []
        extra5 = []
        extra6 = []
        timeindex = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actal index used
        
    
    
        i = 0
        for row in data:
            items = list(zip(header, row))
            item = {}
            for (name, value) in items:
                item[name] = value.strip()
                
            # take i as time in seconds
            timex.append(i)
            
            et = -1
            try:
                et = float(item['ET'])
            except Exception: # pylint: disable=broad-except
                pass
            temp1.append(et)
            
            bt = -1
            try:
                bt = float(item['BT'])
                # after 2min we mark DRY if not auto adjusted
                if timeindex[1] == 0 and i>60 and (not aw.qmc.phasesbuttonflag) and bt >= aw.qmc.phases[1]:
                    timeindex[1] = max(0,i)
            except Exception: # pylint: disable=broad-except
                pass
            temp2.append(bt)
            
            heater = -1
            try:
                heater = float(item['Heater'])
            except Exception: # pylint: disable=broad-except
                pass
            extra1.append(heater)
    
            fan = -1
            try:
                fan = float(item['Fan'])
            except Exception: # pylint: disable=broad-except
                pass
            extra2.append(fan)
    
            humidity = -1
            try:
                humidity = float(item['Humidity'])
            except Exception: # pylint: disable=broad-except
                pass
            extra3.append(humidity)
    
            pressure = -1
            try:
                pressure = float(item['Pressure'])
            except Exception: # pylint: disable=broad-except
                pass
            extra4.append(pressure)
    
            drum = -1
            try:
                drum = float(item['Drum'])
            except Exception: # pylint: disable=broad-except
                pass
            extra5.append(drum)
            
            extra6.append(-1)
            
            if "Fan" in item:
                try:
                    v = float(item["Fan"])
                    if v != fan:
                        # fan value changed
                        if fan_last is not None and v == fan_last:
                            # just a fluctuation, we remove the last added fan value again
                            fan_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 0)
                            del specialeventsvalue[fan_last_idx]
                            del specialevents[fan_last_idx]
                            del specialeventstype[fan_last_idx]
                            del specialeventsStrings[fan_last_idx]
                            fan = fan_last
                            fan_last = None
                        else:
                            fan_last = fan
                            fan = v
                            fan_event = True
                            v = v/10. + 1
                            specialeventsvalue.append(v)
                            specialevents.append(i)
                            specialeventstype.append(0)
                            specialeventsStrings.append("{}".format(float(item["Fan"])) + "%")
                    else:
                        fan_last = None
                except Exception: # pylint: disable=broad-except
                    pass
            if "Heater" in item:
                try:
                    v = int(round(float(item["Heater"])))
                    if heater is None or v != heater:
                        # heater value changed
                        if heater_last is not None and v == heater_last:
                            # just a fluctuation, we remove the last added heater value again
                            heater_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 3)
                            del specialeventsvalue[heater_last_idx]
                            del specialevents[heater_last_idx]
                            del specialeventstype[heater_last_idx]
                            del specialeventsStrings[heater_last_idx]
                            heater = heater_last
                            heater_last = None
                        else:
                            heater_last = heater
                            heater = v
                            heater_event = True
                            v = v/10. + 1
                            specialeventsvalue.append(v)
                            specialevents.append(i)
                            specialeventstype.append(3)
                            specialeventsStrings.append("{}".format(float(item["Heater"])) + "%")
                    else:
                        heater_last = None
                except Exception: # pylint: disable=broad-except
                    pass
            i = i + 1
     
    # mark CHARGE
# not sure if index 1 holds the correct data
#    try:
#        start = int(header_row[1])
#        if start != 0:
#            timeindex[0] = max(0,start)
#    except:
#        pass
    if timeindex[0] == -1:
        timeindex[0] = 0
    # mark FCs
    try:
        timeindex[2] = max(0,int(header_row[19]))
    except Exception: # pylint: disable=broad-except
        pass
    # mark SCs
    try:
        timeindex[4] = max(0,int(header_row[21]))
    except Exception: # pylint: disable=broad-except
        pass
# not sure if index 23 holds the correct data
#    # mark DROP
#    try:
#        end = int(header_row[23])
#        if end != 0:
#            timeindex[6] = max(0,min(end,len(timex)-1))
#    except:
#        pass
    if timeindex[6] == 0:
        timeindex[6] = max(0,len(timex)-1)
    
    res["mode"] = 'C'
            
    res["timex"] = timex
    res["temp1"] = temp1
    res["temp2"] = temp2
    res["timeindex"] = timeindex
    
    res["extradevices"] = [25,25,25]
    res["extratimex"] = [timex[:],timex[:],timex[:]]
    
    res["extraname1"] = ["{3}","Humidity","{1}"]
    res["extratemp1"] = [extra1,extra3,extra5]
    res["extramathexpression1"] = ["","",""]
    
    res["extraname2"] = ["{0}","Pressure",""]
    res["extratemp2"] = [extra2,extra4,extra6]
    res["extramathexpression2"] = ["","",""]
    
    if len(specialevents) > 0:
        res["specialevents"] = specialevents
        res["specialeventstype"] = specialeventstype
        res["specialeventsvalue"] = specialeventsvalue
        res["specialeventsStrings"] = specialeventsStrings
        if heater_event or fan_event:
            # first set etypes to defaults
            res["etypes"] = [QApplication.translate("ComboBox", "Air",None),
                             QApplication.translate("ComboBox", "Drum",None),
                             QApplication.translate("ComboBox", "Damper",None),
                             QApplication.translate("ComboBox", "Burner",None),
                             "--"]
            # update
            if fan_event:
                res["etypes"][0] = "Fan"
            if heater_event:
                res["etypes"][3] = "Heater"        
    
    return res
                