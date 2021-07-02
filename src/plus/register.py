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

import sys
import os
import shelve
import dbm
import portalocker
from pathlib import Path

from PyQt5.QtCore import QSemaphore

from plus import config, util

register_semaphore = QSemaphore(1)

uuid_cache_path = util.getDirectory(config.uuid_cache,share=True)
uuid_cache_path_lock = util.getDirectory(config.uuid_cache + "_lock",share=True)


def addPathShelve(uuid,path,fh):
    config.logger.debug("register: addPathShelve(%s,%s,_fh_)",uuid,path)
    try:
        with shelve.open(uuid_cache_path) as db:
            db[uuid] = str(path)
        config.logger.debug("register: DB type: %s", str(dbm.whichdb(uuid_cache_path)))
    except Exception as e:
        _, _, exc_tb = sys.exc_info()
        config.logger.error("register: Exception in addPathShelve(%s,%s) line: %s shelve.open (1) %s",str(uuid),str(path),exc_tb.tb_lineno,e)
        try:
            # in case we couldn't open the shelve file as  "shelve.open db type could not be determined"
            # remove all files name uuid_cache_path with any extension as we do not know which extension is choosen by shelve
            config.logger.info("register: clean uuid cache %s",str(uuid_cache_path))
            # note that this deletes all "uuid" files including those for the Viewer and other files of that name prefix like uuid.db.org!!
            for p in Path(Path(uuid_cache_path).parent).glob("{}*".format(config.uuid_cache)):
                if str(p) != uuid_cache_path_lock:
                    # if not the lock file, delete:
                    p.unlink()
            # try again to acccess/create the shelve file
            with shelve.open(uuid_cache_path) as db:
                db[uuid] = str(path)
            config.logger.info("register: Generated db type: %s", str(dbm.whichdb(uuid_cache_path)))
        except Exception as e:
            config.logger.error("register: Exception in addPathShelve(%s,%s) line: %s shelve.open (2) %s",str(uuid),str(path),exc_tb.tb_lineno,e)                    
    finally:
        fh.flush()
        os.fsync(fh.fileno())

# register the path for the given uuid, assuming it points to the .alog profile containing that uuid
def addPath(uuid,path):
    config.logger.debug("register: addPath(%s,%s)",uuid,path)
    try:
        register_semaphore.acquire(1)
        config.logger.debug("register:addPath(%s,%s)",str(uuid),str(path))
        with portalocker.Lock(uuid_cache_path_lock, timeout=0.5) as fh:
            addPathShelve(uuid,path,fh)
    except portalocker.exceptions.LockException as e:
        _, _, exc_tb = sys.exc_info()
        config.logger.info("register: LockException in addPath(%s,%s) line: %s %s",str(uuid),str(path),exc_tb.tb_lineno,e)
        # we couldn't fetch this lock. It seems to be blocked forever (from a crash?)
        # we remove the lock file and retry with a shorter timeout
        try:
            config.logger.info("register: clean lock %s",str(uuid_cache_path))
            Path(uuid_cache_path_lock).unlink()
            config.logger.debug("retry register:addPath(%s,%s)",str(uuid),str(path))
            with portalocker.Lock(uuid_cache_path_lock, timeout=0.3) as fh:
                addPathShelve(uuid,path,fh)
        except portalocker.exceptions.LockException as e:
            _, _, exc_tb = sys.exc_info()
            config.logger.error("register: LockException in addPath(%s,%s) line: %s %s",str(uuid),str(path),exc_tb.tb_lineno,e)
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            config.logger.error("register: Exception in addPath(%s,%s) line: %s %s",str(uuid),str(path),exc_tb.tb_lineno,e)
    except Exception as e:
        _, _, exc_tb = sys.exc_info()
        config.logger.error("register: Exception in addPath(%s,%s) line: %s %s",str(uuid),str(path),exc_tb.tb_lineno,e)
    finally:
        if register_semaphore.available() < 1:
            register_semaphore.release(1)  
    
# returns None if given uuid is not registered, otherwise the registered path
def getPath(uuid):
    config.logger.debug("register: getPath(%s)",uuid)
    try:
        register_semaphore.acquire(1)
        config.logger.debug("register:getPath(%s)",str(uuid))
        with portalocker.Lock(uuid_cache_path_lock, timeout=0.5) as fh:
            try:
                with shelve.open(uuid_cache_path) as db:
                    try:
                        res_path = str(db[uuid])
                        config.logger.debug("register:getPath(%s): %s",str(uuid),res_path)
                        return res_path
                    except:
                        return None
            except Exception as e:
                _, _, exc_tb = sys.exc_info()
                config.logger.error("register: Exception in getPath(%s) line: %s shelve.open %s",str(uuid),exc_tb.tb_lineno,e)
                return None
            finally:
                fh.flush()
                os.fsync(fh.fileno())
    except portalocker.exceptions.LockException as e:
        _, _, exc_tb = sys.exc_info()
        config.logger.info("register: LockException in getPath(%s) line: %s %s",uuid,exc_tb.tb_lineno,e)
        # we couldn't fetch this lock. It seems to be blocked forever (from a crash?)
        # we remove the lock file and retry with a shorter timeout
        try:
            config.logger.info("register: clean lock %s",str(uuid_cache_path_lock))
            Path(uuid_cache_path_lock).unlink()
            config.logger.debug("retry register:getPath(%s)",str(uuid))
            with portalocker.Lock(uuid_cache_path_lock, timeout=0.3) as fh:
                try:
                    with shelve.open(uuid_cache_path) as db:
                        try:
                            res_path = str(db[uuid])    
                            config.logger.debug("register:getPath(%s): %s",str(uuid),res_path)
                            return res_path
                        except:
                            return None
                except Exception as e:
                    _, _, exc_tb = sys.exc_info()
                    config.logger.error("register: Exception in getPath(%s) line: %s shelve.open %s",str(uuid),exc_tb.tb_lineno,e)
                    return None
                finally:
                    fh.flush()
                    os.fsync(fh.fileno())
        except portalocker.exceptions.LockException as e:
            _, _, exc_tb = sys.exc_info()
            config.logger.error("register: LockException in getPath(%s) line: %s %s",str(uuid),exc_tb.tb_lineno,e)
            return None
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            config.logger.error("register: Exception in getPath(%s) line: %s %s",str(uuid),exc_tb.tb_lineno,e)
            return None
    except Exception as e:
        _, _, exc_tb = sys.exc_info()
        config.logger.error("register: Exception in getPath(%s) line: %s %s",str(uuid),exc_tb.tb_lineno,e)
        return None
    finally:
        if register_semaphore.available() < 1:
            register_semaphore.release(1)


# scanns all .alog files for uuids and registers them in the cache
def scanDir(path=None):
    config.logger.debug("register: scanDir(%s)",path)
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
                addPath(d[config.uuid_tag],currentFile) # @UndefinedVariable
    except Exception as e:
        config.logger.error("register: Exception in scanDir() %s",e)


