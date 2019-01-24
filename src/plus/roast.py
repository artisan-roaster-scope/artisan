#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# roast.py
#
# Copyright (c) 2018, Paul Holleis, Marko Luther
# All rights reserved.
# 
# 
# ABOUT
# This module connects to the artisan.plus inventory management service

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import hashlib

from plus import config, util


# given a profile dictionary extract key parameters to populate a Roast element
def getTemplate(bp):
    config.logger.debug("roast:getTemplate()")
    d = {}
    try: 
        aw = config.app_window
        
        util.addNum2dict(bp,"roastbatchnr",d,"batch_number",0,65534,0)
        if "batch_number" in d and d["batch_number"]:
            util.addString2dict(bp,"roastbatchprefix",d,"batch_prefix",50)
            util.addNum2dict(bp,"roastbatchpos",d,"batch_pos",0,255,0)
            
        if "roastepoch" in bp:
            d["date"] = util.epoch2ISO8601(bp["roastepoch"])

        if "weight" in bp:
            if bp["weight"][0]:
                try:
                    w = util.limitnum(0,65534,aw.convertWeight(bp["weight"][0],aw.qmc.weight_units.index(bp["weight"][2]),aw.qmc.weight_units.index("Kg")))
                    if w is not None:
                        d["start_weight"] = util.float2floatMin(w,3) # in kg
                except:
                    pass         
            if bp["weight"][1]:
                try:
                    w = util.limitnum(0,65534,aw.convertWeight(bp["weight"][1],aw.qmc.weight_units.index(bp["weight"][2]),aw.qmc.weight_units.index("Kg")))
                    if w is not None:
                        d["end_weight"] = util.float2floatMin(w,3) # in kg
                except:
                    pass
                
        if "volume" in bp:
            if bp["volume"][0]:
                try:
                    v = util.limitnum(0,65534,aw.convertWeight(bp["volume"][0],aw.qmc.volume_units.index(bp["volume"][2]),aw.qmc.volume_units.index("l")))
                    if v is not None:
                        d["volume_in"] = util.float2floatMin(v,3) # in liter
                except:
                    pass
            if bp["volume"][1]:
                try:
                    v = util.limitnum(0,65534,aw.convertWeight(bp["volume"][1],aw.qmc.volume_units.index(bp["volume"][2]),aw.qmc.volume_units.index("l")))
                    if v is not None:
                        d["volume_out"] = util.float2floatMin(v,3) # in liter
                except:
                    pass  
        
        util.add2dict(bp,config.uuid_tag,d,"id")            
        util.addNum2dict(bp,"moisture_roasted",d,"moisture",0,100,1)            
        util.addString2dict(bp,"title",d,"label",255)
        util.addString2dict(bp,"roastertype",d,"machine",50)
        util.addString2dict(bp,"machinesetup",d,"setup",50)
        util.addNum2dict(bp,"whole_color",d,"whole_color",0,255,0)
        util.addNum2dict(bp,"ground_color",d,"ground_color",0,255,0)       
                        
        if ("whole_color" in d or "ground_color" in d):  
            util.addString2dict(bp,"color_system",d,"color_system",25)

        if "computed" in bp:
            cp = bp["computed"]
            
            util.addAllTemp2dict(cp,d,[
                ("CHARGE_ET","charge_temp_ET"),
                ("CHARGE_BT","charge_temp"),
                ("TP_BT","TP_temp"),
                ("DRY_BT","DRY_temp"),
                ("FCs_BT","FCs_temp"),
                ("FCe_BT","FCe_temp"),
                ("DROP_BT","drop_temp"),
                ("DROP_ET","drop_temp_ET")])
            util.addAllTime2dict(cp,d,[
                "TP_time",
                "DRY_time",
                "FCs_time",
                "FCe_time",
                ("DROP_time","drop_time")])
                
            if "finishphasetime" in cp:
                util.addTime2dict(cp,"finishphasetime",d,"DEV_time")
                if "totaltime" in cp:
                    v = util.limitnum(0,100,util.float2floatMin(cp["finishphasetime"]/cp["totaltime"]*100,1))
                    if v is not None:
                        d["DEV_ratio"] = v

    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("roast: Exception in getTemplate() line %s: %s",exc_tb.tb_lineno,e)
    return d

def getRoast():
    d = {}
    try:
        config.logger.debug("roast:getRoast()")
        aw = config.app_window 
        p = aw.getProfile()
        
        d = getTemplate(p)
        
        # id => roast_id
        if "id" in d:
            d["roast_id"] = d["id"]
            del d["id"]
        
        # start_weight => amount
        if "start_weight" in d:
            d["amount"] = d["start_weight"]
            del d["start_weight"]
        else:
            d["amount"] = 0
            
        if "computed" in p:
            cp = p["computed"]
            util.addNum2dict(cp,"det",d,"CM_ETD",0,100,1)
            util.addNum2dict(cp,"dbt",d,"CM_BTD",0,100,1)                              

        if aw.qmc.plus_store:
            d["location"] = aw.qmc.plus_store
        if aw.qmc.plus_coffee:
            d["coffee"] = aw.qmc.plus_coffee
        else:
            d["coffee"] = None
        if aw.qmc.plus_blend_spec:
            d["blend"] = aw.qmc.plus_blend_spec
        else:
            d["blend"] = None
        
        util.addTemp2dict(p,"ambientTemp",d,"temperature")        
        util.addNum2dict(p,"ambient_pressure",d,"pressure",800,1200,1)
        util.addNum2dict(p,"ambient_humidity",d,"humidity",0,100,1)
        
        util.addString2dict(p,"roastingnotes",d,"notes",1023)
            
        if aw.qmc.background and aw.qmc.backgroundprofile:
            bp = aw.qmc.backgroundprofile
            template = getTemplate(bp)
            d["template"] = template
            
        # if profile is already saved, that modification date is send along to the server instead the timestamp
        # of the moment the record is queued
        if not aw.curFile is None:
            d["modified_at"] = util.epoch2ISO8601(util.getModificationDate(aw.curFile))
        
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("roast: Exception in getRoast() line %s: %s",exc_tb.tb_lineno,e)
        return {}
    return d

        
################
## Sync Record (roast properties synced bidirectional between the client and the server)

# returns the current plus record and a hash over the plus record
# if applied, r is assumed to contain the complete roast data as returned by roast.getRoast()
def getSyncRecord(r = None):
    try:
        config.logger.info("roast:getSyncRecord()")
        m = hashlib.sha256()
        d = {}
        if r is None:
            r = getRoast()
        attributes = [
            "roast_id",
            "location",
            "coffee",
            "blend",
            "label",
            "amount",
            "end_weight",
            "volume_in",
            "volume_out",
            "batch_number",
            "batch_prefix",
            "batch_pos", 
            "color_system",
            "whole_color",
            "ground_color",
            "moisture",
            "machine",
            "notes",                           
        ]
        # we take only the value of attributes to be synced back
        for a in attributes:
            if a in r:
                d[a] = r[a]
                m.update(str(r[a]).encode('utf-8'))
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("roast: Exception in getSyncRecord() in line %s: %s",exc_tb.tb_lineno,e)
    config.logger.debug("roast:getSyncRecord d -> %s",d)
    return d,m.hexdigest()

    