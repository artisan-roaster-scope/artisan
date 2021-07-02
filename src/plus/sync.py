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

import os
import sys
import shelve
import dbm
import portalocker
from pathlib import Path
import requests

from PyQt5.QtCore import QSemaphore, QTimer
from PyQt5.QtWidgets import QApplication

from plus import config, util, connection, controller, roast



#### Sync Cache

# holding all roast UUIDs under sync with the server
# shared cache between the Artisan and the ArtisanViewer app

sync_cache_semaphore = QSemaphore(1)

def getSyncName():
    if config.account_nr is None or config.account_nr == 0:
        fn = config.sync_cache
    else:
        fn = config.sync_cache + str(config.account_nr)
    return fn

# if lock is True, return the path of the corresponding lock file
def getSyncPath(lock=False):
    fn = getSyncName()
    if lock:
        fn = fn + "_lock"
    return util.getDirectory(fn,share=True)


def addSyncShelve(uuid,modified_at,fh):
    config.logger.debug("sync: addSyncShelve(%s,%s,_fh_)",uuid,modified_at)
    try:
        with shelve.open(getSyncPath()) as db:
            db[uuid] = modified_at
        config.logger.debug("sync: DB type: %s", str(dbm.whichdb(getSyncPath())))
    except Exception as e:
        _, _, exc_tb = sys.exc_info()
        config.logger.error("sync: Exception in addSyncShelve(%s,%s) line: %s shelve.open (1) %s",str(uuid),str(modified_at),exc_tb.tb_lineno,e)
        try:
            # in case we couldn't open the shelve file as  "shelve.open db type could not be determined"
            # remove all files name getSyncPath() with any extension as we do not know which extension is choosen by shelve
            config.logger.info("register: clean uuid cache %s",str(getSyncPath()))
            # note that this deletes all "uuid" files including those for the Viewer and other files of that name prefix like uuid.db.org!!
            sync_lock_file = getSyncPath(lock=True)
            for p in Path(Path(getSyncPath()).parent).glob("{}*".format(getSyncName())):
                if str(p) != sync_lock_file:
                    # if not the lock file, delete:
                    p.unlink()
            # try again to acccess/create the shelve file
            with shelve.open(getSyncPath()) as db:
                db[uuid] = modified_at
            config.logger.debug("sync: DB type: %s", str(dbm.whichdb(getSyncPath())))
        except Exception as e:
            config.logger.error("register: Exception in addPathShelve(%s,%s) line: %s shelve.open (2) %s",str(uuid),str(modified_at),exc_tb.tb_lineno,e)          
    finally:
        fh.flush()
        os.fsync(fh.fileno())

# register the modified_at timestamp (EPOC as float with milliseoncds) for the given uuid, assuming it holds the last timepoint modifications were last synced with the server
def addSync(uuid,modified_at):
    try:
        sync_cache_semaphore.acquire(1)
        config.logger.debug("sync:addSync(%s,%s)", str(uuid), str(modified_at))
        with portalocker.Lock(getSyncPath(lock=True), timeout=0.5) as fh:
            addSyncShelve(uuid,modified_at,fh)
    except portalocker.exceptions.LockException as e:
        _, _, exc_tb = sys.exc_info()
        config.logger.info("sync: LockException in addSync(%s,%s) line: %s %s",str(uuid), str(modified_at),exc_tb.tb_lineno,e)
        # we couldn't fetch this lock. It seems to be blocked forever (from a crash?)
        # we remove the lock file and retry with a shorter timeout
        try:
            lock_path = Path(getSyncPath(lock=True))
            config.logger.info("sync: clean lock %s",str(lock_path))
            lock_path.unlink()
            config.logger.debug("retry sync:addSync(%s,%s)",str(uuid), str(modified_at))
            with portalocker.Lock(lock_path, timeout=0.3) as fh:
                addSyncShelve(uuid,modified_at,fh)
        except portalocker.exceptions.LockException as e:
            _, _, exc_tb = sys.exc_info()
            config.logger.error("sync: LockException in addSync(%s,%s) line: %s %s",str(uuid),str(modified_at),exc_tb.tb_lineno,e)
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            config.logger.error("sync: Exception in addSync(%s,%s) line: %s %s",str(uuid),uuid(modified_at),exc_tb.tb_lineno,e)
    except Exception as e:
        _, _, exc_tb = sys.exc_info()
        config.logger.error("sync: Exception in addSync(%s,%s) line: %s %s",str(uuid),uuid(modified_at),exc_tb.tb_lineno,e)
    finally:
        if sync_cache_semaphore.available() < 1:
            sync_cache_semaphore.release(1)  
    
# returns None if given uuid is not registered for syncing, otherwise the last modified_at timestamp in EPOC milliseconds
def getSync(uuid):
    try:
        sync_cache_semaphore.acquire(1)
        config.logger.debug("sync:getSync(%s)", str(uuid))
        with portalocker.Lock(getSyncPath(lock=True), timeout=0.5) as fh:
            try:
                with shelve.open(getSyncPath()) as db:
                    try:
                        ts = db[uuid]
                        config.logger.debug(" -> sync:getSync = " + str(ts))
                        return ts
                    except:
                        config.logger.debug(" -> sync:getSync = None")
                        return None
            except Exception as e:
                _, _, exc_tb = sys.exc_info()
                config.logger.error("sync: Exception in getSync(%s) line: %s shelve.open %s",str(uuid),exc_tb.tb_lineno,e)
                return None
            finally:
                fh.flush()
                os.fsync(fh.fileno())
    except portalocker.exceptions.LockException as e:
        config.logger.info("sync: LockException in getSync(%s) line: %s %s",str(uuid),exc_tb.tb_lineno,e)
        # we couldn't fetch this lock. It seems to be blocked forever (from a crash?)
        # we remove the lock file and retry with a shorter timeout
        try:
            lock_path = Path(getSyncPath(lock=True))
            config.logger.info("sync: clean lock %s",str(lock_path))
            lock_path.unlink()
            config.logger.debug("retry sync:getSync(%s)",str(uuid))
            with portalocker.Lock(getSyncPath(lock=True), timeout=0.3) as fh:
                try:
                    with shelve.open(getSyncPath()) as db:
                        try:
                            ts = db[uuid]
                            config.logger.debug(" -> sync:getSync = " + str(ts))
                            return ts
                        except:
                            config.logger.debug(" -> sync:getSync = None")
                            return None
                except Exception as e:
                    _, _, exc_tb = sys.exc_info()
                    config.logger.error("sync: Exception in getSync(%s) line: %s shelve.open %s",str(uuid),exc_tb.tb_lineno,e)
                    return None
                finally:
                    fh.flush()
                    os.fsync(fh.fileno())
        except portalocker.exceptions.LockException as e:
            _, _, exc_tb = sys.exc_info()
            config.logger.error("sync: LockException in getSync(%s) line: %s %s",str(uuid),exc_tb.tb_lineno,e)
            return None
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            config.logger.error("sync: Exception in getSync(%s) line: %s %s",str(uuid),exc_tb.tb_lineno,e)
            return None
    except Exception as e:
        _, _, exc_tb = sys.exc_info()
        config.logger.error("sync: Exception in getSync(%s) line: %s %s",str(uuid),exc_tb.tb_lineno,e)
        return None
    finally:
        if sync_cache_semaphore.available() < 1:
            sync_cache_semaphore.release(1)
            
def delSync(uuid):
    try:
        sync_cache_semaphore.acquire(1)
        config.logger.debug("sync:delSync(%s)", str(uuid))
        with portalocker.Lock(getSyncPath(lock=True), timeout=0.5) as fh:
            try:
                with shelve.open(getSyncPath()) as db:
                    del db[uuid]
            except KeyError as e:
                _, _, exc_tb = sys.exc_info()
                config.logger.debug("sync: Exception in delSync(%s) line: %s KeyError %s",str(uuid),exc_tb.tb_lineno,e)
            except Exception as e:
                _, _, exc_tb = sys.exc_info()
                config.logger.error("sync: Exception in delSync(%s) line: %s shelve.open %s",str(uuid),exc_tb.tb_lineno,e)
            finally:
                fh.flush()
                os.fsync(fh.fileno())
    except portalocker.exceptions.LockException as e:
        config.logger.info("sync: LockException in delSync(%s) line: %s %s",str(uuid),exc_tb.tb_lineno,e)
        # we couldn't fetch this lock. It seems to be blocked forever (from a crash?)
        # we remove the lock file and retry with a shorter timeout
        try:
            lock_path = Path(getSyncPath(lock=True))
            config.logger.info("sync: clean lock %s",str(lock_path))
            lock_path.unlink()
            config.logger.debug("retry sync:delSync(%s)",str(uuid))
            with portalocker.Lock(getSyncPath(lock=True), timeout=0.3) as fh:
                try:
                    with shelve.open(getSyncPath()) as db:
                        del db[uuid]
                except KeyError:
                    config.logger.debug("sync: Exception in delSync(%s) line: %s KeyError %s",str(uuid),exc_tb.tb_lineno,e)
                except Exception as e:
                    _, _, exc_tb = sys.exc_info()
                    config.logger.error("sync: Exception in delSync(%s) line: %s shelve.open %s",str(uuid),exc_tb.tb_lineno,e)
                finally:
                    fh.flush()
                    os.fsync(fh.fileno())
        except portalocker.exceptions.LockException as e:
            _, _, exc_tb = sys.exc_info()
            config.logger.error("sync: LockException in delSync(%s) line: %s %s",str(uuid),exc_tb.tb_lineno,e)
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            config.logger.debug("sync: Exception in delSync(%s) line: %s %s",str(uuid),exc_tb.tb_lineno,e)
    except Exception as e:
        _, _, exc_tb = sys.exc_info()
        config.logger.debug("sync: Exception in delSync(%s) line: %s %s",str(uuid),exc_tb.tb_lineno,e)
    finally:
        if sync_cache_semaphore.available() < 1:
            sync_cache_semaphore.release(1)


#### Sync Record Cache (tracking of changes to partial attributes synced bidirectional)

# we cache the sync record hash before local edits (and after server updates are received) to be able to decide later if local changes have been applied
# if cached_sync_record_hash is None (cleared) the syncing is forced

sync_record_semaphore = QSemaphore(1) # protecting access to the cached_plus_sync_record_hash
cached_sync_record_hash = None # hash over the sync record
cached_sync_record = None # the actual sync record the hash is computed over to be able to compute the differences 
    # to the current sync record and send only those in updates


# called before local edits can start to remember the original state of the sync record
# if provided, roast_record is assumed to be a full roast record as provided by roast.getRoast(), otherwise the roast record is taken from the current data
def setSyncRecordHash(sync_record = None, h = None):
    global cached_sync_record_hash, cached_sync_record
    try:
        config.logger.debug("sync:setSyncRecordHash()")
        sync_record_semaphore.acquire(1)
        if sync_record is not None and h is not None:
            cached_sync_record = sync_record
            cached_sync_record_hash = h
        else:
            cached_sync_record,cached_sync_record_hash = roast.getSyncRecord()
    except Exception as e:
        config.logger.error("sync: Exception in setSyncRecordHash() %s",e)
    finally:
        if sync_record_semaphore.available() < 1:
            sync_record_semaphore.release(1)  

def clearSyncRecordHash():
    global cached_sync_record_hash, cached_sync_record
    try:
        config.logger.debug("sync:clearSyncRecordHash()")
        sync_record_semaphore.acquire(1)
        cached_sync_record_hash = None
        cached_sync_record = None
    except Exception as e:
        config.logger.error("sync: Exception in clearSyncRecordHash() %s",e)
    finally:
        if sync_record_semaphore.available() < 1:
            sync_record_semaphore.release(1) 

# verifies if the given roast_records hash (or the one of the current roast data)
#   equals the cached_sync_record_hash
# if provided, roast_record is assumed to be a full roast record as provided by roast.getRoast()
def syncRecordUpdated(roast_record = None):
    global cached_sync_record_hash
    try:
        config.logger.debug("sync:syncRecordUpdated(%s)",roast_record)
        sync_record_semaphore.acquire(1)
        _,current_sync_record_hash = roast.getSyncRecord(roast_record)
        res = cached_sync_record_hash != current_sync_record_hash
        config.logger.debug("sync:syncRecordUpdated() => %s",res)
        return res
    except Exception as e:
        config.logger.error("sync: Exception in syncRecordUpdated() %s",e)
        return False
    finally:
        if sync_record_semaphore.available() < 1:
            sync_record_semaphore.release(1)   

# returns the roast_record with all attributes, but for the roast_id, with the same value as in the current cached_sync_record removed
# the result is the roast_record with all unchanged attributes, which do not need to synced on updates, removed
def diffCachedSyncRecord(roast_record):
    global cached_sync_record
    try:
        config.logger.debug("sync:diffCachedSyncRecord()")
        sync_record_semaphore.acquire(1)
        if cached_sync_record is None or roast_record is None:
            return roast_record
        else:
            res = dict(roast_record) # make a copy of the given roast_record
            keys_with_equal_values = [] 
            # entries with values equal on server and client do not need to be synced
            for key, value in cached_sync_record.items():
                if key != "roast_id" and key in res and res[key] == value:
                    del res[key]
                    keys_with_equal_values.append(key)
            # for items where we supress zero values we need to force the propagate of zeros in case on server there is no zero established yet
            for key in roast.sync_record_zero_supressed_attributes:
                if key in cached_sync_record and cached_sync_record[key] and key not in res \
                        and key not in keys_with_equal_values: # not if data is euqal on both sides and thus the key got deleted from res in the step before
                    # we explicitly set the value of key to 0 dispite it is part of the sync_record_zero_supressed_attributes
                    # to sync back the local 0 value with the non-zero value currently on the server
                    res[key] = 0
            # for items where we supress empty string values we need to force the propagate of empty strings in case on server there is no zero established yet
            for key in roast.sync_record_empty_string_supressed_attributes:
                if key in cached_sync_record and cached_sync_record[key] and key not in res \
                        and key not in keys_with_equal_values: # not if data is euqal on both sides and thus the key got deleted from res in the step before
                    # we explicitly set the value of key to "" dispite it is part of the sync_record_empty_string_supressed_attributes
                    # to sync back the local "" value with the non-zero value currently on the server
                    res[key] = ""
            return res
    except Exception as e:
        config.logger.error("sync: Exception in diffCachedSyncRecord() %s",e)
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
    global cached_sync_record
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
            if aw.qmc.plus_coffee is not None:
                aw.qmc.plus_blend_label = None
                aw.qmc.plus_blend_spec = None
                aw.qmc.plus_blend_spec_labels = None
        if "blend" in data and data["blend"] is not None and "label" in data["blend"] and "ingredients" in data["blend"] \
               and data["blend"]["ingredients"]:
            try:
                ingredients = []
                for i in data["blend"]["ingredients"]:
                    entry = {}
                    entry["ratio"] = i["ratio"]
                    entry["coffee"] = i["coffee"]["hr_id"]  # just the hr_id as a string and not the full object
                    if "ratio_num" in i and i["ratio_num"] is not None:
                        entry["ratio_num"] = i["ratio_num"]
                    if "ratio_denom" in i and i["ratio_denom"] is not None:
                        entry["ratio_denom"] = i["ratio_denom"]
                    ingredients.append(entry)
                blend_spec = {
                    "label": data["blend"]["label"],
                    "ingredients": ingredients}
                blend_spec_labels = [i["coffee"]["label"] for i in data["blend"]["ingredients"]]
                aw.qmc.plus_blend_spec = blend_spec
                aw.qmc.plus_blend_spec_labels = blend_spec_labels
                dirty = True
            except Exception:
                pass
            if aw.qmc.plus_blend_spec is not None:
                aw.qmc.plus_coffee = None
                aw.qmc.plus_coffee_label = None
        
        # ensure that location is None if neither coffee nor blend is set
        if aw.qmc.plus_coffee is None and aw.qmc.plus_blend_spec is None and aw.qmc.plus_store is not None:
            aw.qmc.plus_store = None
        
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
        if "density_roasted" in data and data["density_roasted"] != aw.qmc.density_roasted[0]:
            aw.qmc.density_roasted[0] = data["density_roasted"]
            dirty = True  
        if "moisture" in data and data["moisture"] != aw.qmc.density_roasted[0]:
            aw.qmc.moisture_roasted = data["moisture"]
            dirty = True
        if "temperature" in data and data["temperature"] != aw.qmc.ambientTemp:
            aw.qmc.ambientTemp = data["temperature"]
            dirty = True
        if "pressure" in data and data["pressure"] != aw.qmc.ambient_pressure:
            aw.qmc.ambient_pressure = data["pressure"]
            dirty = True
        if "humidity" in data and data["humidity"] != aw.qmc.ambient_humidity:
            aw.qmc.ambient_humidity = data["humidity"]
            dirty = True
        if "roastersize" in data and data["roastersize"] != aw.qmc.roastersize:
            aw.qmc.roastersize = data["roastersize"]
            dirty = True
        if "roasterheating" in data and data["roasterheating"] != aw.qmc.roasterheating:
            aw.qmc.roasterheating = data["roasterheating"]
            dirty = True
        setSyncRecordHash() # here the sync record is taken form the profiles data after application of the recieved server updates
        # not that this sync record does not contain null values not transferred for attributes from the server side
        # to fix this, we will update that sync record with all attributes not in the server data set to null values
        # this forces those non-null values from the profile to be transmitted to the server on next sync
        updated_record = {}
        for key, value in cached_sync_record.items():
            if not (key in data):
                # we explicitly add the implicit null value (0 or "") for that key
                if key in roast.sync_record_zero_supressed_attributes and value != 0:
                    updated_record[key] = 0
                elif key in roast.sync_record_empty_string_supressed_attributes and value != "":
                    updated_record[key] = ""
            else:
                updated_record[key] = value
        cached_sync_record,cached_sync_record_hash = roast.getSyncRecord(updated_record)
        setSyncRecordHash(cached_sync_record,cached_sync_record_hash)
        
    except Exception as e:
        config.logger.error("sync: Exception in applyServerUpdates() %s",e)
    finally: 
        if title_changed:
            aw.setTitleSignal.emit(aw.qmc.title,True) # we force an updatebackground to ensure proper repainting
        if dirty:
            aw.qmc.fileDirty()
            aw.sendmessageSignal.emit(QApplication.translate("Plus","Updated data received from artisan.plus", None),True,None)
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
        config.logger.debug("sync:fetchServerUpdate() -> status: %s",status)
        config.logger.debug("sync:fetchServerUpdate() -> data: %s",res)
        
        if status == 204: # NO CONTENT: data on server is older then ours
            config.logger.debug("sync:fetchServerUpdate() -> 204 data on server is older")
            #no newer data found on server, do nothing; controller.is_synced() might report an unsynced status
            # if file modification date is newer than what is known on the version from the server via the sync cache
            
            if file is not None and getSync(uuid) is None:
                config.logger.debug("sync: -> file not in sync cache yet, we need to fetch the servers modification date and add the profile to the sync cache")
                # we recurse to get a 200 with the last_modification date from the server for this record to add it to the sync cache automatically
                fetchServerUpdate(uuid)
            pass
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
                
                if getSync(uuid) is None and "modified_at" in r :
                    addSync(uuid,util.ISO86012epoch(r["modified_at"]))
                    config.logger.debug("sync: -> added profile automatically to sync cache")
                
                if file_last_modified is not None:
                    config.logger.debug("sync: -> file last_modified date: %s",util.epoch2ISO8601(file_last_modified))
                if "modified_at" in r and file_last_modified is not None and util.ISO86012epoch(r["modified_at"])>file_last_modified:
                    applyServerUpdates(r)
                else:
                    config.logger.debug("sync: -> data received from server was older!?")
                    config.logger.debug("sync: -> file last_modified epoch: %s",file_last_modified)
                    config.logger.debug("sync: -> server last_modified epoch: %s",util.ISO86012epoch(r["modified_at"]))
                    config.logger.debug("sync: -> server last_modified date: %s",r["modified_at"])
    except requests.exceptions.ConnectionError as e: # more general: requests.exceptions.RequestException
        config.logger.debug("sync: -> connection error in fetchServerUpdate(), disconnecting: %s",e)
        # we disconnect, but keep the queue running to let it automatically reconnect if possible
        controller.disconnect(remove_credentials = False, stop_queue=False)
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("sync: Exception in fetchServerUpdate() in line %s: %s",exc_tb.tb_lineno,e)
    finally:
        aw.editgraphdialog = None # stop block opening the Roast Properties dialog while syncing from the server
        config.app_window.updatePlusStatusSignal.emit() # @UndefinedVariable


# updates from server are only requested if connected (the uuid does not have to be in the sync cache; this allows roasts to be "rediscovered" once the 
# sync cache got lost). This behavior was changed from requiring an exsisting sync record in commit from 23.1.2020
# https://github.com/artisan-roaster-scope/artisan/commit/62880a7c10051638b2171406da918f5a98f04631
# "adds roast profiles automatic to the plus syncing game if not yet part of it but there is already a record on the platform"

# this function might be called from a thread (eg. via QTimer)
def getUpdate(uuid,file=None):
    config.logger.info("sync:getUpdate(" + str(uuid) + "," + str(file) + ")")
    if uuid is not None:
        aw = config.app_window
        if aw.editgraphdialog is None and controller.is_connected():
            try:
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
        computed_sync_record,computed_sync_record_hash = roast.getSyncRecord(rr)
        if aw.qmc.plus_sync_record_hash is None or aw.qmc.plus_sync_record_hash != computed_sync_record_hash:
            # the sync record of the loaded profile is not consistent or missing, offline changes (might) have been applied
            aw.qmc.fileDirty() # set file dirty flag
            clearSyncRecordHash() # clear sync record hash cash to trigger an upload of the modified plus sync record on next save
        else:
            setSyncRecordHash(sync_record = computed_sync_record, h = computed_sync_record_hash) # we remember that consistent state to be able to detect future modifications
        getUpdate(aw.qmc.roastUUID,aw.curFile) # now we check for updates on the server side
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("sync: Exception in sync() line %s: %s",exc_tb.tb_lineno,e)
