#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ABOUT
# IKAWA CSV Roast Profile importer

import time as libtime
import os
import io
import csv
import re
            
from PyQt5.QtCore import QDateTime,Qt
from PyQt5.QtWidgets import QApplication

from artisanlib.util import encodeLocal

# returns a dict containing all profile information contained in the given IKAWA CSV file
def extractProfileIkawaCSV(file):
    res = {} # the interpreted data set

    res["samplinginterval"] = 1.0

    # set profile date from the file name if it has the format "IKAWA yyyy-mm-dd hhmmss.csv"
    filename = os.path.basename(file)
    p = re.compile('IKAWA \d{4,4}-\d{2,2}-\d{2,2} \d{6,6}.csv')
    if p.match(filename):
        s = filename[6:-4] # the extracted date time string
        date = QDateTime.fromString(s,"yyyy-MM-dd HHmmss")
        res["roastdate"] = encodeLocal(date.date().toString())
        res["roastisodate"] = encodeLocal(date.date().toString(Qt.ISODate))
        res["roasttime"] = encodeLocal(date.time().toString())
        res["roastepoch"] = int(date.toTime_t())
        res["roasttzoffset"] = libtime.timezone

    csvFile = io.open(file, 'r', newline="",encoding='utf-8')
    data = csv.reader(csvFile,delimiter=',')
    #read file header
    header = next(data)
    
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
    timeindex = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actal index used
    i = 0
    for row in data:
        i = i + 1
        items = list(zip(header, row))
        item = {}
        for (name, value) in items:
            item[name] = value.strip()
        # take i as time in seconds
        timex.append(i)
        if 'temp set' in item:
            temp1.append(float(item['temp set']))
        else:
            temp1.append(-1)
        if 'exaust temp' in item:
            temp2.append(float(item['exaust temp']))
        else:
            temp2.append(-1)
        # mark CHARGE
        if not timeindex[0] > -1 and 'state' in item and item['state'] == 'doser open':
            timeindex[0] = i
        # mark DROP
        if timeindex[6] == 0 and 'state' in item and item['state'] == 'cooling':
            timeindex[6] = i
        # add RPM and RPM/100
        if 'fan speed (RPM)' in item:
            rpm = float(item['fan speed (RPM)'])
            extra1.append(rpm)
            extra2.append(rpm/100)
        else:
            extra2.append(-1)
            extra2.append(-1)
        
        if "fan set (%)" in item:
            try:
                v = float(item["fan set (%)"])
                if v != fan:
                    # fan value changed
                    if v == fan_last:
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
                        specialeventsStrings.append(item["fan set (%)"] + "%")
                else:
                    fan_last = None
            except Exception as e:
                pass
        if "heater power (%)" in item:
            try:
                v = float(item["heater power (%)"])
                if v != heater:
                    # heater value changed
                    if v == heater_last:
                        # just a fluctuation, we remove the last added heater value again
                        heater_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 3)
                        del specialeventsvalue[heater_last_idx]
                        del specialevents[heater_last_idx]
                        del specialeventstype[heater_last_idx]
                        del specialeventsStrings[heater_last_idx]
                        heater = heater_last
                        heaster_last = None
                    else:
                        heater_last = heater
                        heater = v
                        heater_event = True
                        v = v/10. + 1
                        specialeventsvalue.append(v)
                        specialevents.append(i)
                        specialeventstype.append(3)
                        specialeventsStrings.append(item["heater power (%)"] + "%")
                else:
                    heater_last = None
            except:
                pass
    csvFile.close()
            
    res["timex"] = timex
    res["temp1"] = temp1
    res["temp2"] = temp2
    res["timeindex"] = timeindex
    
    res["extradevices"] = [25]
    res["extratimex"] = [timex]
    
    res["extraname1"] = ["RPM"]
    res["extratemp1"] = [extra1]
    res["extramathexpression1"] = [""]
    
    res["extraname2"] = ["RPM/100"]
    res["extratemp2"] = [extra2]
    res["extramathexpression2"] = ["Y3/100"]
    
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

#        
#    # extract general profile information
#    general_sh = book.sheet_by_index(0)
#    if general_sh.nrows >= 1:
#        general_data = dict(zip([x.value for x in general_sh.row(0)],general_sh.row(1)))
#        
#        res["samplinginterval"] = 1.0
#        
#        if 'Id-Tag' in general_data:
#            try:
#                id_tag = general_data['Id-Tag'].value
#                batch_prefix = id_tag.rstrip('0123456789')
#                batch_number = int(id_tag[len(batch_prefix):])
#                res["roastbatchprefix"] = batch_prefix
#                res["roastbatchnr"] = batch_number
#            except:
#                pass
#        for tag,label in zip(
#            ['Profile','Lot name','Machine','Roast technician','Sensorial notes','Roasting notes'],
#            ['title','beans','roastertype','operator','cuppingnotes','roastingnotes']):
#            if tag in general_data:
#                try:
#                    value = str(general_data[tag].value)
#                    res[label] = value
#                except:
#                    pass
#        if 'Date' in general_data:
#            try:
#                raw_date = general_data['Date'].value
#                date_tuple = xlrd.xldate_as_tuple(raw_date, book.datemode)
#                date = QDateTime(*date_tuple)
#                res["roastdate"] = encodeLocal(date.date().toString())
#                res["roastisodate"] = encodeLocal(date.date().toString(Qt.ISODate))
#                res["roasttime"] = encodeLocal(date.time().toString())
#                res["roastepoch"] = int(date.toTime_t())
#                res["roasttzoffset"] = libtime.timezone
#            except:
#                pass
#        if 'Ambient temp.' in general_data:
#            try:
#                value = general_data['Ambient temp.'].value
#                res['ambientTemp'] = float(value)
#            except:
#                pass
#        if 'Start weight' in general_data or 'End weight' in general_data:
#            cropster_weight_units = ["G","KG","LBS","OZ"]
#            artisan_weight_units = ["g","Kg","lb","oz"]
#            weight = [0,0,artisan_weight_units[0]]
#            try:
#                value = general_data['End weight unit'].value
#                idx = cropster_weight_units.index(value)
#                weight[2] = artisan_weight_units[idx]
#            except:
#                pass
#            try:
#                value = general_data['Start weight unit'].value
#                idx = cropster_weight_units.index(value)
#                weight[2] = artisan_weight_units[idx]
#            except:
#                pass
#            try:
#                value = general_data['Start weight'].value
#                weight[0] = value
#            except:
#                pass
#            try:
#                value = general_data['End weight'].value
#                weight[1] = value
#            except:
#                pass
#            res["weight"] = weight
#    # BT:
#    try:
#        BT_idx = sheet_names.index("Curve - Bean temp.")
#        BT_sh = book.sheet_by_index(BT_idx)
#        if BT_sh.ncols >= 1:
#            time = BT_sh.col(0)
#            temp = BT_sh.col(1)
#            if len(time) > 0 and len(temp) > 0 and len(time) == len(temp):
#                if "FAHRENHEIT" in str(temp[0].value):
#                    res["mode"] = 'F'
#                else:
#                    res["mode"] = 'C'
#                res["timex"] = [t.value for t in time[1:]]
#                res["temp2"] = [t.value for t in temp[1:]]
#                res["temp1"] = [-1]*len(res["timex"])
#                res["timeindex"] = [0,0,0,0,0,0,len(res["timex"])-1,0]
#    except:
#        pass
#    # ET
#    try:
#        ET_idx = sheet_names.index("Curve - Env. temp.")
#        ET_sh = book.sheet_by_index(ET_idx)
#        if ET_sh.ncols >= 1:
#            time = ET_sh.col(0)
#            temp = ET_sh.col(1)
#            if len(time) > 0 and len(temp) > 0 and len(time) == len(temp):
#                if "FAHRENHEIT" in str(temp[0].value):
#                    res["mode"] = 'F'
#                else:
#                    res["mode"] = 'C'
#                res["temp1"] = [t.value for t in temp[1:]]
#                if len(res["timex"]) != len(res["temp1"]):
#                    res["timex"] = [t.value for t in time[1:]]
#                if "temp2" not in res or len(res["temp2"]) != len(res["timex"]):
#                    res["temp2"] = [-1]*len(res["timex"])
#                res["timeindex"] = [0,0,0,0,0,0,len(res["timex"])-1,0]
#    except:
#        pass
#    # extra temperature curves
#    channel = 1 # toggle between channel 1 and 2 to be filled with extra temperature curve data
#    for sn in sheet_names:
#        if sn.startswith("Curve") and "temp." in sn and sn != "Curve - Bean temp." and sn != "Curve - Env. temp.":
#            try:
#                extra_curve_name = sn.split("Curve - ")
#                if len(extra_curve_name) > 1:
#                    extra_curve_name = extra_curve_name[1].split("temp.")
#                    extra_curve_name = extra_curve_name[0]
#                else:
#                    extra_curve_name = extra_curve_name[0]
#                CT_idx = sheet_names.index(sn)
#                CT_sh = book.sheet_by_index(CT_idx)
#                if CT_sh.ncols >= 1:
#                    time = CT_sh.col(0)
#                    temp = CT_sh.col(1)
#                    if len(time) > 0 and len(temp) > 0 and len(time) == len(temp):
#                        if "extradevices" not in res:
#                            res["extradevices"] = []
#                        if "extraname1" not in res:
#                            res["extraname1"] = []
#                        if "extraname2" not in res:
#                            res["extraname2"] = []
#                        if "extratimex" not in res:
#                            res["extratimex"] = []
#                        if "extratemp1" not in res:
#                            res["extratemp1"] = []
#                        if "extratemp2" not in res:
#                            res["extratemp2"] = []
#                        if "extramathexpression1" not in res:
#                            res["extramathexpression1"] = []
#                        if "extramathexpression2" not in res:
#                            res["extramathexpression2"] = []
#                        if channel == 1:
#                            channel = 2
#                            res["extradevices"].append(25)
#                            res["extraname1"].append(extra_curve_name)
#                            res["extratimex"].append([t.value for t in time[1:]])
#                            res["extratemp1"].append([t.value for t in temp[1:]])
#                            res["extramathexpression1"].append("")
#                        elif (len(time) -1) == len(res["extratimex"][-1]): # only if time lengths is same as of channel 1
#                            channel = 1
#                            res["extraname2"].append(extra_curve_name)
#                            res["extratemp2"].append([t.value for t in temp[1:]])
#                            res["extramathexpression2"].append("")
#            except:
#                pass    
#    if "extraname1" in res and "extraname2" in res and len(res["extraname1"]) != len(res["extraname2"]):
#        # we add an empty second extra channel if needed
#        res["extraname2"].append("Extra 2")
#        res["extratemp2"].append([-1]*len(res["extratemp1"][-1]))
#        res["extramathexpression2"].append("")
#    # add events
#    try:
#        COMMENTS_idx = sheet_names.index("Comments")
#        COMMENTS_sh = book.sheet_by_index(COMMENTS_idx)
#        gas_event = False # set to True if a Gas event exists
#        airflow_event = False # set to True if an Airflow event exists
#        specialevents = []
#        specialeventstype = []
#        specialeventsvalue = []
#        specialeventsStrings = []
#        if COMMENTS_sh.ncols >= 4:        
#            takeClosest = lambda num,collection:min(collection,key=lambda x:abs(x-num))
#            for r in range(COMMENTS_sh.nrows):
#                if r>0:
#                    try:
#                        time = COMMENTS_sh.cell(r, 0).value
#                        comment_type = COMMENTS_sh.cell(r, 2).value
#                        if comment_type not in ["Turning point"]: # TP is ignored as it is automatically assigned
#                            comment_value = COMMENTS_sh.cell(r, 3).value                    
#                            c = takeClosest(time,res["timex"])
#                            timex_idx = res["timex"].index(c)
#                            if comment_type == "Color change":
#                                res["timeindex"][1] = timex_idx
#                            elif comment_type == "First crack":
#                                res["timeindex"][2] = timex_idx
#                            elif comment_type == "Second crack":
#                                res["timeindex"][4] = timex_idx
#                            else:
#                                specialevents.append(timex_idx)
#                                if comment_type == "Airflow":
#                                    airflow_event = True
#                                    specialeventstype.append(0)
#                                elif comment_type == "Gas":
#                                    gas_event = True
#                                    specialeventstype.append(3)
#                                else:
#                                    specialeventstype.append(4)
#                                try:
#                                    v = float(comment_value)
#                                    v = v/10. + 1
#                                    specialeventsvalue.append(v)
#                                except:
#                                    specialeventsvalue.append(0)
#                                if comment_type not in ["Airflow","Gas","Comment"]:
#                                    specialeventsStrings.append(comment_type)
#                                else:
#                                    specialeventsStrings.append(comment_value)
#                    except:
#                        pass
#        if len(specialevents) > 0:
#            res["specialevents"] = specialevents
#            res["specialeventstype"] = specialeventstype
#            res["specialeventsvalue"] = specialeventsvalue
#            res["specialeventsStrings"] = specialeventsStrings
#            if gas_event or airflow_event:
#                # first set etypes to defaults
#                res["etypes"] = [QApplication.translate("ComboBox", "Air",None),
#                                 QApplication.translate("ComboBox", "Drum",None),
#                                 QApplication.translate("ComboBox", "Damper",None),
#                                 QApplication.translate("ComboBox", "Burner",None),
#                                 "--"]
#                # update
#                if airflow_event:
#                   res["etypes"][0] = "Airflow"
#                if gas_event:
#                   res["etypes"][3] = "Gas"
                