#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ABOUT
# Cropster XLS Roast Profile importer

import time as libtime
import xlrd
from PyQt5.QtCore import QDateTime, QDate, Qt# returns a dict containing all profile information contained in the given Cropster XLS file
from PyQt5.QtWidgets import QApplication

from artisanlib.util import encodeLocal

def extractProfileCropsterXLS(file):
    res = {} # the interpreted data set
    
    book = xlrd.open_workbook(file)
    
    sheet_names = book.sheet_names()
        
    # extract general profile information
    general_sh = book.sheet_by_index(0)
    if general_sh.nrows >= 1:
        general_data = dict(zip([x.value for x in general_sh.row(0)],general_sh.row(1)))
        
        res["samplinginterval"] = 1.0
        
        if 'Id-Tag' in general_data:
            try:
                id_tag = general_data['Id-Tag'].value
                batch_prefix = id_tag.rstrip('0123456789')
                batch_number = int(id_tag[len(batch_prefix):])
                res["roastbatchprefix"] = batch_prefix
                res["roastbatchnr"] = batch_number
            except:
                pass
        for tag,label in zip(
            ['Profile','Lot name','Machine','Roast technician','Sensorial notes','Roasting notes'],
            ['title','beans','roastertype','operator','cuppingnotes','roastingnotes']):
            if tag in general_data:
                try:
                    value = str(general_data[tag].value)
                    res[label] = value
                except:
                    pass
        if 'Date' in general_data:
            try:
                raw_date = general_data['Date'].value
                date_tuple = xlrd.xldate_as_tuple(raw_date, book.datemode)
                date = QDateTime(*date_tuple)
                res["roastdate"] = encodeLocal(date.date().toString())
                res["roastisodate"] = encodeLocal(date.date().toString(Qt.ISODate))
                res["roasttime"] = encodeLocal(date.time().toString())
                res["roastepoch"] = int(date.toTime_t())
                res["roasttzoffset"] = libtime.timezone
            except:
                pass
        if 'Ambient temp.' in general_data:
            try:
                value = general_data['Ambient temp.'].value
                res['ambientTemp'] = float(value)
            except:
                pass
        if 'Start weight' in general_data or 'End weight' in general_data:
            cropster_weight_units = ["G","KG","LBS","OZ"]
            artisan_weight_units = ["g","Kg","lb","oz"]
            weight = [0,0,artisan_weight_units[0]]
            try:
                value = general_data['End weight unit'].value
                idx = cropster_weight_units.index(value)
                weight[2] = artisan_weight_units[idx]
            except:
                pass
            try:
                value = general_data['Start weight unit'].value
                idx = cropster_weight_units.index(value)
                weight[2] = artisan_weight_units[idx]
            except:
                pass
            try:
                value = general_data['Start weight'].value
                weight[0] = value
            except:
                pass
            try:
                value = general_data['End weight'].value
                weight[1] = value
            except:
                pass
            res["weight"] = weight
    # BT:
    try:
        BT_idx = sheet_names.index("Curve - Bean temp.")
        BT_sh = book.sheet_by_index(BT_idx)
        if BT_sh.ncols >= 1:
            time = BT_sh.col(0)
            temp = BT_sh.col(1)
            if len(time) > 0 and len(temp) > 0 and len(time) == len(temp):
                if "FAHRENHEIT" in str(temp[0].value):
                    res["mode"] = 'F'
                else:
                    res["mode"] = 'C'
                res["timex"] = [t.value for t in time[1:]]
                res["temp2"] = [t.value for t in temp[1:]]
                res["temp1"] = [-1]*len(res["timex"])
                res["timeindex"] = [0,0,0,0,0,0,len(res["timex"])-1,0]
    except:
        pass
    # ET
    try:
        ET_idx = sheet_names.index("Curve - Env. temp.")
        ET_sh = book.sheet_by_index(ET_idx)
        if ET_sh.ncols >= 1:
            time = ET_sh.col(0)
            temp = ET_sh.col(1)
            if len(time) > 0 and len(temp) > 0 and len(time) == len(temp):
                if "FAHRENHEIT" in str(temp[0].value):
                    res["mode"] = 'F'
                else:
                    res["mode"] = 'C'
                res["temp1"] = [t.value for t in temp[1:]]
                if len(res["timex"]) != len(res["temp1"]):
                    res["timex"] = [t.value for t in time[1:]]
                if "temp2" not in res or len(res["temp2"]) != len(res["timex"]):
                    res["temp2"] = [-1]*len(res["timex"])
                res["timeindex"] = [0,0,0,0,0,0,len(res["timex"])-1,0]
    except:
        pass
    # extra temperature curves
    channel = 1 # toggle between channel 1 and 2 to be filled with extra temperature curve data
    for sn in sheet_names:
        if sn.startswith("Curve") and "temp." in sn and sn != "Curve - Bean temp." and sn != "Curve - Env. temp.":
            try:
                extra_curve_name = sn.split("Curve - ")
                if len(extra_curve_name) > 1:
                    extra_curve_name = extra_curve_name[1].split("temp.")
                    extra_curve_name = extra_curve_name[0]
                else:
                    extra_curve_name = extra_curve_name[0]
                CT_idx = sheet_names.index(sn)
                CT_sh = book.sheet_by_index(CT_idx)
                if CT_sh.ncols >= 1:
                    time = CT_sh.col(0)
                    temp = CT_sh.col(1)
                    if len(time) > 0 and len(temp) > 0 and len(time) == len(temp):
                        if "extradevices" not in res:
                            res["extradevices"] = []
                        if "extraname1" not in res:
                            res["extraname1"] = []
                        if "extraname2" not in res:
                            res["extraname2"] = []
                        if "extratimex" not in res:
                            res["extratimex"] = []
                        if "extratemp1" not in res:
                            res["extratemp1"] = []
                        if "extratemp2" not in res:
                            res["extratemp2"] = []
                        if "extramathexpression1" not in res:
                            res["extramathexpression1"] = []
                        if "extramathexpression2" not in res:
                            res["extramathexpression2"] = []
                        if channel == 1:
                            channel = 2
                            res["extradevices"].append(25)
                            res["extraname1"].append(extra_curve_name)
                            res["extratimex"].append([t.value for t in time[1:]])
                            res["extratemp1"].append([t.value for t in temp[1:]])
                            res["extramathexpression1"].append("")
                        elif (len(time) -1) == len(res["extratimex"][-1]): # only if time lengths is same as of channel 1
                            channel = 1
                            res["extraname2"].append(extra_curve_name)
                            res["extratemp2"].append([t.value for t in temp[1:]])
                            res["extramathexpression2"].append("")
            except:
                pass    
    if "extraname1" in res and "extraname2" in res and len(res["extraname1"]) != len(res["extraname2"]):
        # we add an empty second extra channel if needed
        res["extraname2"].append("Extra 2")
        res["extratemp2"].append([-1]*len(res["extratemp1"][-1]))
        res["extramathexpression2"].append("")
    # add events
    try:
        COMMENTS_idx = sheet_names.index("Comments")
        COMMENTS_sh = book.sheet_by_index(COMMENTS_idx)
        gas_event = False # set to True if a Gas event exists
        airflow_event = False # set to True if an Airflow event exists
        specialevents = []
        specialeventstype = []
        specialeventsvalue = []
        specialeventsStrings = []
        if COMMENTS_sh.ncols >= 4:        
            takeClosest = lambda num,collection:min(collection,key=lambda x:abs(x-num))
            for r in range(COMMENTS_sh.nrows):
                if r>0:
                    try:
                        time = COMMENTS_sh.cell(r, 0).value
                        comment_type = COMMENTS_sh.cell(r, 2).value
                        if comment_type not in ["Turning point"]: # TP is ignored as it is automatically assigned
                            comment_value = COMMENTS_sh.cell(r, 3).value                    
                            c = takeClosest(time,res["timex"])
                            timex_idx = res["timex"].index(c)
                            if comment_type == "Color change":
                                res["timeindex"][1] = timex_idx
                            elif comment_type == "First crack":
                                res["timeindex"][2] = timex_idx
                            elif comment_type == "Second crack":
                                res["timeindex"][4] = timex_idx
                            else:
                                specialevents.append(timex_idx)
                                if comment_type == "Airflow":
                                    airflow_event = True
                                    specialeventstype.append(0)
                                elif comment_type == "Gas":
                                    gas_event = True
                                    specialeventstype.append(3)
                                else:
                                    specialeventstype.append(4)
                                try:
                                    v = float(comment_value)
                                    v = v/10. + 1
                                    specialeventsvalue.append(v)
                                except:
                                    specialeventsvalue.append(0)
                                if comment_type not in ["Airflow","Gas","Comment"]:
                                    specialeventsStrings.append(comment_type)
                                else:
                                    specialeventsStrings.append(comment_value)
                    except:
                        pass
        if len(specialevents) > 0:
            res["specialevents"] = specialevents
            res["specialeventstype"] = specialeventstype
            res["specialeventsvalue"] = specialeventsvalue
            res["specialeventsStrings"] = specialeventsStrings
            if gas_event or airflow_event:
                # first set etypes to defaults
                res["etypes"] = [QApplication.translate("ComboBox", "Air",None),
                                 QApplication.translate("ComboBox", "Drum",None),
                                 QApplication.translate("ComboBox", "Damper",None),
                                 QApplication.translate("ComboBox", "Burner",None),
                                 "--"]
                # update
                if airflow_event:
                   res["etypes"][0] = "Airflow"
                if gas_event:
                   res["etypes"][3] = "Gas"
    except:
        pass
    return res
                