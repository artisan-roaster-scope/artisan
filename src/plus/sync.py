#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# sync.py
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

import shelve
from pathlib import Path

from PyQt5.QtCore import QSemaphore, QTimer
from PyQt5.QtWidgets import QApplication

from plus import config, util, connection, controller, roast


#### Sync Cache

# holding all roast UUIDs under sync with the server

sync_cache_semaphore = QSemaphore(1)

def getSyncPath():
    if config.account_nr is None or config.account_nr == 0:
        return util.getDirectory(config.sync_cache)
    else:
        return util.getDirectory(config.sync_cache + str(config.account_nr))

# register the modified_at timestamp (EPOC as float with milliseoncds) for the given uuid, assuming it holds the last timepoint modifications were last synced with the server
def addSync(uuid,modified_at):
    try:
        config.logger.debug("sync:addSync(" + str(uuid) + "," + str(modified_at) + ")")
        sync_cache_semaphore.acquire(1)
        with shelve.open(getSyncPath()) as db:
            db[uuid] = modified_at
    except Exception as e:
        config.logger.error("sync: Exception in addSync() %s",e)
    finally:
        if sync_cache_semaphore.available() < 1:
            sync_cache_semaphore.release(1)  
    
# returns None if given uuid is not registered for syncing, otherwise the last modified_at timestamp in EPOC milliseconds
def getSync(uuid):
    try:
        config.logger.debug("sync:getSync(" + str(uuid) + ")")
        sync_cache_semaphore.acquire(1)
        with shelve.open(getSyncPath()) as db:
            try:
                ts = db[uuid]
                config.logger.debug(" -> sync:getSync = " + str(ts))
                return ts
            except:
                config.logger.debug(" -> sync:getSync = None")
                return None
    except Exception as e:
        config.logger.error("sync: Exception in getSync() %s",e)
        return None
    finally:
        if sync_cache_semaphore.available() < 1:
            sync_cache_semaphore.release(1)
            
def delSync(uuid):
    try:
        config.logger.debug("sync:delSync(" + str(uuid) + ")")
        sync_cache_semaphore.acquire(1)
        with shelve.open(getSyncPath()) as db:
            del db[uuid]
    except Exception as e:
        config.logger.error("sync: Exception in delSync() %s",e)
    finally:
        if sync_cache_semaphore.available() < 1:
            sync_cache_semaphore.release(1)              


#### Sync Record Cache (tracking of changes to partial attributes synced bidirectional)

# we cache the sync record hash before local edits to be able to decide later if local changes have been applied

sync_record_semaphore = QSemaphore(1) # protecting access to the cached_plus_sync_record_hash
cached_sync_record_hash = None # hash over the sync record


# called before local edits can start to remember the original state of the sync record
# if provided, roast_record is assumed to be a full roast record as provided by roast.getRoast()
def setSyncRecordHash(roast_record = None):
    global cached_sync_record_hash
    try:
        config.logger.debug("sync:setSyncRecordHash()")
        sync_record_semaphore.acquire(1)
        _,cached_sync_record_hash = roast.getSyncRecord(roast_record)
    except Exception as e:
        config.logger.error("sync: Exception in setSyncRecordHash() %s",e)
    finally:
        if sync_record_semaphore.available() < 1:
            sync_record_semaphore.release(1)  

def clearSyncRecordHash():
    global cached_sync_record_hash
    try:
        config.logger.debug("sync:clearSyncRecordHash()")
        sync_record_semaphore.acquire(1)
        cached_sync_record_hash = None
    except Exception as e:
        config.logger.error("sync: Exception in clearSyncRecordHash() %s",e)
    finally:
        if sync_record_semaphore.available() < 1:
            sync_record_semaphore.release(1) 

# if provided, roast_record is assumed to be a full roast record as provided by roast.getRoast()
def syncRecordUpdated(roast_record = None):
    try:
        config.logger.debug("sync:syncRecordUpdated()")
        sync_record_semaphore.acquire(1)
        _,current_sync_record_hash = roast.getSyncRecord(roast_record)
        return cached_sync_record_hash != current_sync_record_hash
    except Exception as e:
        config.logger.error("sync: Exception in syncRecordUpdated() %s",e)
        return False
    finally:
        if sync_record_semaphore.available() < 1:
            sync_record_semaphore.release(1)   



#### Server Updates (applying updates to the current "sync record" from server)

applied_server_updates_modified_at_semaphore = QSemaphore(1) # protecting access to the applied_server_updates_modified_at
applied_server_updates_modified_at = None

def setApplidedServerUpdatesModifiedAt(modified_at):
    global applied_server_updates_modified_at
    try:
        config.logger.debug("sync:setApplidedServerUpdatesModifiedAt()")
        applied_server_updates_modified_at_semaphore.acquire(1)
        applied_server_updates_modified_at = modified_at
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("roast: Exception in setApplidedServerUpdatesModifiedAt() line %s: %s",exc_tb.tb_lineno,e)
    finally:
        if applied_server_updates_modified_at_semaphore.available() < 1:
            applied_server_updates_modified_at_semaphore.release(1)

def getApplidedServerUpdatesModifiedAt():
    global applied_server_updates_modified_at
    try:
        config.logger.debug("sync:getApplidedServerUpdatesModifiedAt()")
        applied_server_updates_modified_at_semaphore.acquire(1)
        return applied_server_updates_modified_at
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("roast: Exception in clearApplidedServerUpdatesModifiedAt() line %s: %s",exc_tb.tb_lineno,e)
        return None
    finally:
        if applied_server_updates_modified_at_semaphore.available() < 1:
            applied_server_updates_modified_at_semaphore.release(1)        
            


# the values of "syncable" properties in data are applied to the apps variables directly 
# if the contained UUID
def applyServerUpdates(data):
    dirty = False
    title_changed = False
    try:
        config.logger.debug("sync:applyServerUpdates()")
        config.logger.debug("sync: -> apply: %s",data)
        aw = config.app_window
        
        if "amount" in data and data["amount"] is not None:
            w = aw.convertWeight(data["amount"],aw.qmc.weight_units.index("Kg"),aw.qmc.weight_units.index(aw.qmc.weight[2]))
            if w != aw.qmc.weight[0]:
                aw.qmc.weight[0] = w
                dirty = True
        if "end_weight" in data and data["end_weight"] is not None:
            w = aw.convertWeight(data["end_weight"],aw.qmc.weight_units.index("Kg"),aw.qmc.weight_units.index(aw.qmc.weight[2]))
            if w != aw.qmc.weight[1]:
                aw.qmc.weight[1] = w
                dirty = True
        if "batch_number" in data and data["batch_number"] != aw.qmc.roastbatchnr:
            aw.qmc.roastbatchnr = data["batch_number"]
            dirty = True
            title_changed = True
        if "batch_prefix" in data and data["batch_prefix"] != aw.qmc.roastbatchprefix:
            aw.qmc.roastbatchprefix = data["batch_prefix"]
            dirty = True
            title_changed = True
        if "batch_pos" in data and data["batch_pos"] != aw.qmc.roastbatchpos:
            aw.qmc.roastbatchpos = data["batch_pos"]
            dirty = True
            title_changed = True            
        if "label" in data and data["label"] != aw.qmc.title:
            aw.qmc.title = data["label"]
            dirty = True
            title_changed = True
        
        if "location" in data and data["location"] is not None:
            if "hr_id" in data["location"] and data["location"]["hr_id"] != aw.qmc.plus_store:
                aw.qmc.plus_store = data["location"]["hr_id"]
                dirty = True
            if "label" in data["location"] and data["location"]["label"] != aw.qmc.plus_store_label:
                aw.qmc.plus_store_label = data["location"]["label"]
                dirty = True
        if "coffee" in data and data["coffee"] is not None:
            if "hr_id" in data["coffee"] and data["coffee"]["hr_id"] != aw.qmc.plus_coffee:
                aw.qmc.plus_coffee = data["coffee"]["hr_id"]
                dirty = True  
            if "label" in data["coffee"] and data["coffee"]["label"] != aw.qmc.plus_coffee_label:
                aw.qmc.plus_coffee_label = data["coffee"]["label"]
                dirty = True       
        if "blend" in data and data["blend"] is not None and "label" in data["blend"] and "ingredients" in data["blend"] \
               and data["blend"]["ingredients"]:
            try:
                ingredients = data["blend"]["ingredients"]
                blend_spec = {
                    "label": data["blend"]["label"], 
                    "ingredients": [{"coffee": i["coffee"]["hr_id"], "ratio": i["ratio"]} for i in ingredients]}
                blend_spec_labels = [i["coffee"]["label"] for i in ingredients]
                aw.qmc.plus_blend_spec = blend_spec
                aw.qmc.plus_blend_spec_labels = blend_spec_labels
                dirty = True
            except:
                pass
        if "color_system" in data and data["color_system"] != aw.qmc.color_systems[aw.qmc.color_system_idx]: 
            try:                   
                aw.qmc.color_system_idx = aw.qmc.color_systems.index(data["color_system"])
                dirty = True
            except: # cloud color system not known by Artisan client
                pass
        if "ground_color" in data and data["ground_color"] != aw.qmc.ground_color:
            aw.qmc.ground_color = data["ground_color"]
            dirty = True
        if "whole_color" in data and data["whole_color"] != aw.qmc.whole_color:
            aw.qmc.whole_color = data["whole_color"]
            dirty = True            
        if "machine" in data and data["machine"] != aw.qmc.roastertype:
            aw.qmc.roastertype = data["machine"]
            dirty = True
        if "notes" in data and data["notes"] != aw.qmc.roastingnotes:
            aw.qmc.roastingnotes = data["notes"]
            dirty = True
        if "volume_in" in data and data["volume_in"] is not None:
            v = aw.convertVolume(data["volume_in"],aw.qmc.volume_units.index("l"),aw.qmc.volume_units.index(aw.qmc.volume[2]))
            if w != aw.qmc.volume[0]:
                aw.qmc.volume[0] = v
                dirty = True
        if "volume_out" in data and data["volume_out"] is not None:
            v = aw.convertVolume(data["volume_out"],aw.qmc.volume_units.index("l"),aw.qmc.volume_units.index(aw.qmc.volume[2]))
            if w != aw.qmc.volume[1]:
                aw.qmc.volume[1] = v
                dirty = True            
    except Exception as e:
        config.logger.error("sync: Exception in applyServerUpdates() %s",e)
    finally: 
        if title_changed:
            aw.setTitleSignal.emit(aw.qmc.title,True) # we force an updatebackground to ensure proper repainting   
        if dirty:
            aw.qmc.safesaveflag = True
            aw.sendmessageSignal.emit(QApplication.translate("Plus","Updated data received from artisan.plus", None))
            if "modified_at" in data: # we remember the timestamp of the applied server updates
                setApplidedServerUpdatesModifiedAt(data["modified_at"])


#### Server Sync (fetching data from server)

# internal function fetching the update from server and then unblock the Properties Dialog and update the plus icon
def fetchServerUpdate(uuid,file=None):
    aw = config.app_window
    try:
        config.logger.debug("sync:fetchServerUpdate() -> requesting update from server (file: %s)",file)         
        last_modified = ""
        if file is not None:
            file_last_modified = util.getModificationDate(file)
            # if file modification data is newer than what we have in our sync cache (as the file was externally modified),
            # we update our sync cache
#            addSync(uuid,file_last_modified)
#   don't update the sync cache timestamp here as the changes might not have been submitted to the server yet
        else:
            file_last_modified = None
        if file_last_modified is not None:
            last_modified = "?modified_at=" + str(int(round(file_last_modified*1000)))
        res = connection.getData(config.roast_url + "/" + uuid + last_modified)
        status = res.status_code
        if status == 204: # NO CONTENT: data on server is older then ours
            config.logger.debug("sync:fetchServerUpdate() -> 204 data on server is older")
            pass # we do nothing
        elif status == 404:
            try:
                data = res.json()
                if "success" in data and not data["success"]:
                    config.logger.debug("sync:fetchServerUpdate() -> 404 roast record deleted on server")
                    # data not found on server, remove UUID from sync cache
                    delSync(uuid)
                # else there must be another cause of the 404
                else:
                    config.logger.debug("sync:fetchServerUpdate() -> 404 server error")
            except:
                pass
        elif status == 200: # data on server is newer than ours => update with data from server
            config.logger.debug("sync:fetchServerUpdate() -> 200 data on server is newer")
            data = res.json()
            if "result" in data:
                r = data["result"]                
                config.logger.debug("sync: -> fetch: %s",r)
                if file_last_modified is not None:
                    config.logger.debug("sync: -> file last_modified date: %s",util.epoch2ISO8601(file_last_modified))
                if "modified_at" in r and file_last_modified is not None and util.ISO86012epoch(r["modified_at"])>file_last_modified:                    
                    applyServerUpdates(r)
                else:
                    config.logger.debug("sync: -> data received from server was older!?")
                    config.logger.debug("sync: -> file last_modified epoch: %s",file_last_modified)
                    config.logger.debug("sync: -> server last_modified epoch: %s",util.ISO86012epoch(r["modified_at"]))
                    config.logger.debug("sync: -> server last_modified date: %s",r["modified_at"])
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("sync: Exception in fetchServerUpdate() in line %s: %s",exc_tb.tb_lineno,e)
    finally:
        aw.editgraphdialog = None # stop block opening the Roast Properties dialog while syncing from the server
        config.app_window.updatePlusStatusSignal.emit()


# updates from server are only requested if connected and the uuid is in the sync cache
# this function might be called from a thread (eg. via QTimer)
def getUpdate(uuid,file=None):
    config.logger.info("sync:getUpdate(" + str(uuid) + "," + str(file) + ")")
    if uuid is not None:
        aw = config.app_window
        if aw.editgraphdialog is None and controller.is_connected():
            try:
                sync_cache_timestamp = getSync(uuid)
                if sync_cache_timestamp is not None:
                    aw.editgraphdialog = False # block opening the Roast Properties dialog while syncing from the server
                    aw.updatePlusStatusSignal.emit() # show syncing icon
                    QTimer.singleShot(2,lambda : fetchServerUpdate(uuid,file))
            except Exception as e:
                config.logger.error("sync: Exception in getUpdate() %s",e)


#### Sync Action as issued on profile load and turning plus on

def sync():
    try:
        config.logger.info("sync:sync()")
        aw = config.app_window
        rr = roast.getRoast()
        _,computed_sync_record_hash = roast.getSyncRecord(rr)
        if aw.qmc.plus_sync_record_hash is None or aw.qmc.plus_sync_record_hash != computed_sync_record_hash:
            # the sync record of the loaded profile is not consistent or missing, offline changes (might) have been applied
            aw.qmc.safesaveflag = True # set file dirty flag
            clearSyncRecordHash() # clear sync record hash cash to trigger an upload of the modified plus sync record on next save
        else:
            setSyncRecordHash(rr) # we remember that consistent state to be able to detect future modifications
        getUpdate(aw.qmc.roastUUID,aw.curFile) # now we check for updates on the server side
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("sync: Exception in sync() line %s: %s",exc_tb.tb_lineno,e)
