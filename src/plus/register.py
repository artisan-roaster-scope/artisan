#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# register.py
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

from PyQt5.QtCore import QSemaphore

from plus import config, util

register_semaphore = QSemaphore(1)

uuid_cache_path = str((Path(util.getDataDirectory()) / config.uuid_cache).resolve())


# register the path for the given uuid, assuming it points to the .alog profile containing that uuid
def addPath(uuid,path):
    try:
        config.logger.debug("register:setPath(" + str(uuid) + "," + str(path) + ")")
        register_semaphore.acquire(1)
        with shelve.open(uuid_cache_path) as db:
            db[uuid] = path
    except Exception as e:
        config.logger.error("roast: Exception in addPath() %s",e)
    finally:
        if register_semaphore.available() < 1:
            register_semaphore.release(1)  
    
# returns None if given uuid is not registered, otherwise the registered path
def getPath(uuid):
    try:
        config.logger.debug("register:getPath(" + str(uuid) + ")")
        register_semaphore.acquire(1)
        with shelve.open(uuid_cache_path) as db:
            try:
                return db[uuid]
            except:
                return None
    except Exception as e:
        config.logger.error("roast: Exception in getPath() %s",e)
    finally:
        if register_semaphore.available() < 1:
            register_semaphore.release(1) 

# scanns all .alog files for uuids and registers them in the cache
def scanDir(path=None):
    try:
        config.logger.debug("register:scanDir(" + str(path) + ")")
        if path is None:
            # search the last used path
            currentDictory = Path(config.app_window.getDefaultPath()) # @UndefinedVariable
        else:
            currentDictory = Path(path)
        for currentFile in currentDictory.glob("*." + config.profile_ext):  
            d = config.app_window.deserialize(currentFile) # @UndefinedVariable
            if config.uuid_tag in d:
                add_path(d[config.uuid_tag],currentFile) # @UndefinedVariable
    except Exception as e:
        config.logger.error("roast: Exception in scanDir() %s",e)


