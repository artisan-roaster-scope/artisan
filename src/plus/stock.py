#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# stock.py
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

import json
import time

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSemaphore, QTimer


from artisanlib.util import d as decode, encodeLocal

from plus import config, connection, util, controller

stock_semaphore = QSemaphore(1) # protects access to the stock_cache file and the stock dict

stock_cache_path = util.getDirectory(config.stock_cache)

stock = None # holds the dict with the current stock data (coffees, blends,..)

import threading

################### 
# stock cache update
# 

# updates the stock cache

def update():
    update_thread = threading.Thread(target=update_blocking)
    update_thread.start()
    
def update_blocking():
    global stock
    config.logger.debug("stock:update_blocking()")
    if stock is None:
        load()
    try:
        stock_semaphore.acquire(1)
        fetch_enabled = config.connected and (stock is None or ("retrieved" in stock and (time.time() - stock["retrieved"]) > config.stock_cache_expiration))
    finally:
        if stock_semaphore.available() < 1:
            stock_semaphore.release(1)
    if fetch_enabled:
        res = fetch()
        if res:
            save()
    else:
        config.logger.debug("stock: -> stock valid")

# requests stock data from server and fills the stock cache
def fetch():
    global stock
    config.logger.info("stock:fetch()")
    try:
        # fetch from server
        d = connection.getData(config.stock_url)
        config.logger.debug("stock: -> %s",d.status_code)
        j = d.json()
        if "success" in j and j["success"] and "result" in j and j["result"]:
            try:
                stock_semaphore.acquire(1)
                stock = j["result"]
                stock["retrieved"] = time.time()
                config.logger.debug("stock: -> retrieved")
                config.logger.debug("stock = %s"%stock)
            finally:
                if stock_semaphore.available() < 1:
                    stock_semaphore.release(1)
            controller.reconnected()
            return True
        else:
            return False
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("stock: -> failure line %s: %s",exc_tb.tb_lineno,e)
#        import traceback
#        tr=traceback.format_exc()
#        aw = config.app_window
#        aw.qmc.adderror(str(tr))
        controller.disconnect(remove_credentials = False, stop_queue = False)
        return False
            

################### 
# stock cache access
# 

# save stock data to local file cache
def save():
    global stock
    config.logger.debug("stock:save()")
    try:
        stock_semaphore.acquire(1)
        if stock is not None:
            with open(stock_cache_path, 'w') as f:
                json.dump(stock, f)                
    except Exception as e:
        config.logger.error("stock: Exception in save() %s",e)
    finally:
        if stock_semaphore.available() < 1:
            stock_semaphore.release(1)
    
# load stock data from local file cache
def load():
    global stock
    config.logger.info("stock:load()")
    try:
        stock_semaphore.acquire(1)
        with open(stock_cache_path) as f:
            stock = json.load(f)
    except Exception as e:
        config.logger.debug("stock: Exception in load() %s",e) # the stock_cache is created on first save()
    finally:
        if stock_semaphore.available() < 1:
            stock_semaphore.release(1)


################### 
# convert between blend dict and list representation

def blend2list(blend_dict):
    try:
        if blend_dict and "label" in blend_dict and "ingredients" in blend_dict and len(blend_dict["ingredients"]) > 1:
            return [encodeLocal(blend_dict["label"]), [ [encodeLocal(i["coffee"]), i["ratio"]] for i in blend_dict["ingredients"]] ]
        else:
            return None
    except:
        return None
    
def list2blend(blend_list):
    try:
        if blend_list and len(blend_list) == 2 and len(blend_list[1])>1:
            d = {}
            d["label"] = decode(blend_list[0])
            d["ingredients"] = [{"coffee": decode(i[0]), "ratio": i[1]} for i in blend_list[1]]
            return d
        else:
            return None
    except:
        return None


################### 
# coffee and blend stock access and rendering

unit_translations_singular  = {
    "bag": QApplication.translate("Plus", "bag",None),
    "box": QApplication.translate("Plus", "box",None),
    "barrel": QApplication.translate("Plus", "barrel",None)
}
unit_translations_plural  = {
    "bag": QApplication.translate("Plus", "bags",None),
    "box": QApplication.translate("Plus", "boxes",None),
    "barrel": QApplication.translate("Plus", "barrels",None)
}


def renderAmount(amount,default_unit = None,target_unit_idx = 0):
    res = ""
    # first try to convert to default_unit
    try:
        unit_size = int(default_unit["size"])
        if amount > unit_size:
            a = amount // unit_size
            if a > 1:
                u = unit_translations_plural[default_unit["name"]]
            else:
                u = unit_translations_singular[default_unit["name"]]
            res = "{}{}".format(int(round(a)),u)
    except:
        pass
    # if we could not convert to default_unit type, we convert to the weightunit
    if not res:
        # we convert the amount from Kg to the target_unit
        w = config.app_window.convertWeight(amount,1,target_unit_idx) # @UndefinedVariable
        if w < 1 and target_unit_idx == 1:
            # we convert Kg to the smaller unit g for readability
            w = config.app_window.convertWeight(amount,1,target_unit_idx-1) # @UndefinedVariable
            target_unit = config.app_window.qmc.weight_units[target_unit_idx-1] # @UndefinedVariable
        elif w > 999 and target_unit_idx == 0:
            # we convert g to the larger unit Kg for readability
            w = config.app_window.convertWeight(amount,1,target_unit_idx+1) # @UndefinedVariable
            target_unit = config.app_window.qmc.weight_units[target_unit_idx+1] # @UndefinedVariable
        else:
            target_unit = config.app_window.qmc.weight_units[target_unit_idx] # @UndefinedVariable
        if w > 9:
            w = int(round(w)) # we truncate all decimals
        else:
            w = config.app_window.float2float(w,1) # @UndefinedVariable # we keep one decimal 
        res = "{0:g}{1}".format(w,target_unit)
    return res

#================== 
# Stores
#   store:  <storeLabel,locationID>

def makeStoreDict(location_hr_id,location_label):
    return {'location_hr_id': location_hr_id, 'location_label': location_label}

def getStoreLabel(store):
    return store[0]
    
def getStoreId(store):
    return store[1]

# returns the list of stores defined in stock
def getStores(acquire_lock=True):
    global stock
    config.logger.debug("stock:getStores()")
    try:
        if acquire_lock:
            stock_semaphore.acquire(1)
        if stock is not None and "coffees" in stock:
            res = {}
            for c in stock["coffees"]:
                if "stock" in c:
                    for s in c["stock"]:
                        res[s["location_label"]] = s["location_hr_id"]
            return sorted(res.items(), key=lambda x: getStoreLabel(x))
        else:
            return []
    finally:
        if acquire_lock and stock_semaphore.available() < 1:
            stock_semaphore.release(1)

# given a list of stores, returns a list of labels to populate the stores popup
def getStoreLabels(stores):
    return [getStoreLabel(s) for s in stores if getStoreId(s) is not None]
    
# returns the position of store id in stores or None if store not in the stores
def getStorePosition(storeId,stores):
    try:
        return [getStoreId(s) for s in stores if getStoreId(s) is not None].index(storeId)
    except:
        return None
    

    
#================== 
# Coffees
#   coffee:  <coffeeLabel,[coffeeDict,stockDict]>

def getCoffeeLabel(coffee):
    return coffee[0]

def getCoffeeCoffeeDict(coffee):
    return coffee[1][0]

def getCoffeeStockDict(coffee):
    return coffee[1][1]
    
def getCoffeeId(coffee):
    return getCoffeeCoffeeDict(coffee)["hr_id"]
    
def getCoffeesLabels(coffees):
    return [getCoffeeLabel(c) for c in coffees]

def coffee2beans(coffee):
    c = getCoffeeCoffeeDict(coffee)
    if "origin" in c:
        origin = QApplication.translate("Countries", c["origin"],None)
    else:
        origin = ""
    if "label" in c:
        label = c["label"]
        if origin:
            label = " " + label
    else:
        label = ""
    processing = ""
    if "processing" in c:
        processing = ' {}'.format(c["processing"])
    grade = ""
    if "grade" in c:
        grade = ' {}'.format(c["grade"])
    varietals = ""
    if "varietals" in c and len(c["varietals"]):
        varietals = ' ({})'.format(', '.join(c["varietals"]))
    bean = '{}{}{}'.format(processing,grade,varietals)
    if bean:
        bean = "," + bean
    year = ""
    if "crop_date" in c:
        cy = c["crop_date"]
        picked = None
        landed = None
        if "picked" in cy and len(cy["picked"]) > 0:
            picked = cy["picked"][0]
        if "landed" in cy and len(cy["landed"]) > 0:
            landed = cy["landed"][0]
        if picked and not landed:
            year = ', {:d}'.format(picked)
        elif landed and not picked:
            year = ', {:d}'.format(landed)
        elif picked and landed:
            year = ', {:d}/{:d}'.format(picked,landed)
    return '{}{}{}{}'.format(origin,label,bean,year)

def getCoffees(weight_unit_idx,store=None):
    global stock
    config.logger.debug("stock:getCoffees(%s,%s)",weight_unit_idx,store)
    try:
        stock_semaphore.acquire(1)
        if stock is not None and "coffees" in stock:
            res = {}
            for c in stock["coffees"]:
                try:
                    origin = ""
                    if "origin" in c:
                        origin = QApplication.translate("Countries", c["origin"],None)
                        if "crop_date" in c:
                            cy = c["crop_date"]
                            picked = None
                            if "picked" in cy and len(cy["picked"]) > 0 and cy["picked"][0] is not None:
                                origin += ' {:d}'.format(cy["picked"][0])
                        origin += ", "
                    label = c["label"]
                    if "default_unit" in c:
                        default_unit = c["default_unit"]
                    else:
                        default_unit = None
                    for s in c["stock"]:
                        if store is None or ("location_hr_id" in s and s["location_hr_id"] == store):
                            if "location_label" in s:
                                location = s["location_label"]
                                if "amount" in s:
                                    amount = s["amount"]
                                    if amount > 0: # TODO: check here the machines capacity limits
                                        # add location only if this coffee is available in several locations
                                        if store:
                                            loc = ""
                                        else:
                                            loc = location + ", "
                                        res[origin + label + " (" + loc + renderAmount(amount,default_unit,weight_unit_idx) + ")"] = [c,s]
                                else:
                                    if store:
                                        res[origin + label] = [c,s]
                                    else:
                                        res[origin + label + " (" + location + ")"] = [c,s]
                except:
                    pass
            return sorted(res.items(), key=lambda x: x[0])
        else:
            return []
    finally:
        if stock_semaphore.available() < 1:
            stock_semaphore.release(1)

# returns the position of coffee hr_id in coffees or None if coffee not in the coffees
def getCoffeePosition(coffeeId,coffees):
    try:
        return [getCoffeeId(c) for c in coffees].index(coffeeId)
    except:
        return None
        # returns the position of coffee id in coffees or None if store not in the stores
     
# returns the position in coffees which matches the given coffeeId and stockId and None if no match is found
def getCoffeeStockPosition(coffeeId,stockId,coffees):
    res = [i for i, c in enumerate(coffees) if getCoffeeCoffeeDict(c)["hr_id"] == coffeeId and getCoffeeStockDict(c)["location_hr_id"] == stockId]
    if len(res)>0:
        return res[0]
    else:
        return None

# returns the coffee and stock dicts of the given coffeeId and storeId or None
def getCoffeeStore(coffeeId,storeId,acquire_lock=True):
    global stock
    try:
        if acquire_lock:
            stock_semaphore.acquire(1)
        coffee = [c for c in stock["coffees"] if c["hr_id"] == coffeeId][0]
        return [(coffee,s) for s in coffee["stock"] if s["location_hr_id"] == storeId][0]
    except: # we end up here if there is no stock available
        return None, None
    finally:
        if acquire_lock and stock_semaphore.available() < 1:
            stock_semaphore.release(1)

#================== 
# Blends
#   blend:  <blendLabel,[blendDict,stockDict,maxAmount,coffeeLabelDict]>
#     with
#   coffeeLabelDict: {<CoffeeId>:<CoffeeLabel>}

def getBlendLabel(blend):
    return blend[0]

def getBlendBlendDict(blend):
    return blend[1][0]

def getBlendStockDict(blend):
    return blend[1][1]

def getBlendMaxAmount(blend):
    return blend[1][2]

def getBlendCoffeeLabelDict(blend):
    return blend[1][3]
    
def getBlendId(blend):
    return getBlendBlendDict(blend)["hr_id"]

def getBlendLabels(blends):
    return [getBlendLabel(c) for c in blends]         
  
def blend2beans(blend,weight_unit_idx,weightIn = 0):
    res = []
    try:
        blends = getBlendBlendDict(blend)
        sorted_ingredients = sorted(blends["ingredients"], key=lambda x:x["ratio"],reverse=True)
        for i in sorted_ingredients:
            c = getBlendCoffeeLabelDict(blend)[i["coffee"]]            
            if weightIn:
                w = ", {}{}".format(config.app_window.float2float(i["ratio"]*weightIn,2),config.app_window.qmc.weight_units[weight_unit_idx]) # @UndefinedVariable
            else:
                w = ""
            res.append('{}%{} {}'.format(int(round(i["ratio"]*100)),w,c))
    except:
        pass
    return res

# this one extends the blend dict by moisture, density and screensize min/max, if it can be computed from its components
def getBlends(weight_unit_idx,store=None):
    global stock
    config.logger.debug("stock:getBlends(%s,%s)",weight_unit_idx,store)
    try:
        stock_semaphore.acquire(1)
        if stock is not None and "blends" in stock:
            res = {}
            if store == None:
                stores = [getStoreId(s) for s in getStores(acquire_lock=False)]
            else:
                stores = [store]   
            for s in stores:
                location_label = ""
                for blend in stock["blends"]:
                    try:
                        coffeeLabels = {}
                        if "ingredients" in blend: 
                            amount = None
                            moisture = [] # for each ingredients we list its moisture*ratio, if the moisture is known
                            density = []  # for each ingredients we list its density*ratio, if the density is known
                            screen = []   # for each ingredients we list the screen_size tuple {'min':x,'max':y}
                            for i in blend["ingredients"]:
                                coffee = i["coffee"]
                                ratio = i["ratio"]
                                cd, sd = getCoffeeStore(coffee,s,acquire_lock=False) # if no stock of this coffee is available this returns None
                                if ratio > 0:
                                    if "moisture" in cd and cd["moisture"] is not None and cd["moisture"] > 0:
                                        moisture.append(cd["moisture"]*ratio)
                                    if "density" in cd and cd["density"] is not None and cd["density"] > 0:
                                        density.append(cd["density"]*ratio)
                                    if "screen_size" in cd and cd["screen_size"] is not None and len(cd["screen_size"]) > 0:
                                        screen.append(cd["screen_size"])
                                i["label"] = cd["label"] # add label of coffee to ingredient
                                stock_amount = sd["amount"]   # if sd is None, this fails
                                if location_label == "":
                                    location_label = sd["location_label"]
                                a = stock_amount / ratio
                                if amount:
                                    amount = min(a,amount)
                                else:
                                    amount = a
                                coffeeLabels[coffee] = coffee2beans([coffee,[cd,sd]])
                            # only if the moisture of all components is known, we can estimate the moisture of this blend
                            if len(blend["ingredients"]) == len(moisture):
                                blend["moisture"] = config.app_window.float2float(sum(moisture),1)  # @UndefinedVariable
                            # only if the density of all components is known, we can estimate the density of this blend
                            if len(blend["ingredients"]) == len(density):
                                blend["density"] = config.app_window.float2float(sum(density),1)  # @UndefinedVariable
                            if len(blend["ingredients"]) == len(screen):
                                sizes = []
                                for sc in screen:
                                    if "min" in sc:
                                        sizes.append(sc["min"])
                                    if "max" in sc:
                                        sizes.append(sc["max"])
                                if len(sizes) > 0:
                                    min_size = min(sizes)
                                    max_size = max(sizes)
                                    blend["screen_min"] = min_size
                                    if max_size != min_size:
                                        blend["screen_max"] = max_size
                            if amount and amount > 0: # TODO: check here with machines capacity                    
                                # add location only if this coffee is available in several locations
                                if store:
                                    loc = ""
                                else:
                                    loc = location_label + ", "
                                label = blend["label"] + " (" + loc + renderAmount(amount,target_unit_idx=weight_unit_idx) + ")"
                                res[label] = [blend,sd,amount,coffeeLabels]
                    except: # we end up here if a coffee is out of stock and thus cd and sd are None
                        pass
            return sorted(res.items(), key=lambda x: x[0])
        else:
            return []
    finally:
        if stock_semaphore.available() < 1:
            stock_semaphore.release(1)

# returns True if blendSpec of the form
#   {"label": <blend-name>, "ingredients": [{"coffee": <hr_id>, "ratio": <n>}, .. ,{"coffee":<hr_id>, "ratio": <n>}]}
# matches the blendDict in the coffee hr_ids and ratios and the blend label
def matchBlendDict(blendSpec, blendDict, sameLabel=True):
    if blendSpec is None or blendDict is None:
        return False
    else:
        if (not sameLabel or blendSpec["label"] == blendDict["label"]) and len(blendSpec["ingredients"]) == len(blendDict["ingredients"]) and len(blendSpec["ingredients"]) > 0:
            return all([i1["coffee"]==i2["coffee"] and i1["ratio"]==i2["ratio"] for (i1,i2) in (zip(blendSpec["ingredients"],blendDict["ingredients"]))])
        else:
            return False
    
        
# returns the position in blends which matches the given blendId and stockId and None if no match is found
def getBlendSpecStockPosition(blendSpec,stockId,blends):
    res = [i for i, b in enumerate(blends) if \
       matchBlendDict(blendSpec,getBlendBlendDict(b)) and \
       getBlendStockDict(b)["location_hr_id"] == stockId]
    if len(res)>0:
        return res[0]
    else:
        # check again, but now ignore label (thus allow renaming of blend names)
        res = [i for i, b in enumerate(blends) if \
           matchBlendDict(blendSpec,getBlendBlendDict(b),sameLabel=False) and \
           getBlendStockDict(b)["location_hr_id"] == stockId]
        if len(res)>0:
            return res[0]
        else:
            return None 
        
