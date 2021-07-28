#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# account.py
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


#### Account Cache

# holding all account ids associated to a (local) running account number
# shared cache between the Artisan and the ArtisanViewer app

account_cache_semaphore = QSemaphore(1)

# shared resource between the Artisan and ArtisanViewer app protected by a file lock
account_cache_path = util.getDirectory(config.account_cache,share=True)
account_cache_lock_path = util.getDirectory(config.account_cache + "_lock",share=True)


def setAccountShelve(account_id,fh):
    config.logger.debug("account: setAccountShelve(%s,_fh_)",account_id)
    try:
        with shelve.open(account_cache_path) as db:
            if account_id in db:
                return db[account_id]
            else:
                new_nr = len(db)
                db[account_id] = new_nr
                return new_nr
        config.logger.debug("account: DB type: %s", str(dbm.whichdb(account_cache_path)))
    except Exception as e:
        _, _, exc_tb = sys.exc_info()
        config.logger.error("account: Exception in setAccountShelve(%s) line (1): %s shelve.open %s",str(account_id),exc_tb.tb_lineno,e)
        try:
            # in case we couldn't open the shelve file as  "shelve.open db type could not be determined"
            # remove all files name account_cache_path with any extension as we do not know which extension is choosen by shelve
            config.logger.info("account: clean acount cache %s",str(account_cache_path))
            # note that this deletes all "account" files including those for the Viewer and other files of that name prefix like account.db.org!!
            for p in Path(Path(account_cache_path).parent).glob("{}*".format(config.account_cache)):
                if str(p) != account_cache_lock_path:
                    # if not the lock file, delete:
                    p.unlink()
            # try again to acccess/create the shelve file
            with shelve.open(account_cache_path) as db:
                if account_id in db:
                    return db[account_id]
                else:
                    new_nr = len(db)
                    db[account_id] = new_nr
                    return new_nr
            config.logger.info("acount: Generated db type: %s", str(dbm.whichdb(account_cache_path)))
        except Exception as e:
            config.logger.error("account: Exception in setAccountShelve(%s) line (2): %s shelve.open %s",str(account_id),exc_tb.tb_lineno,e)
            return None
    finally:
        fh.flush()
        os.fsync(fh.fileno())
                
# register the given account_id and assign it a fresh number if not yet registered
# returns the number associated to account_id or None on error
def setAccount(account_id):
    try:
        account_cache_semaphore.acquire(1)
        config.logger.debug("account:setAccount(%s)",str(account_id))
        with portalocker.Lock(account_cache_lock_path, timeout=0.5) as fh:
            return setAccountShelve(account_id,fh)
    except portalocker.exceptions.LockException as e:
        _, _, exc_tb = sys.exc_info()
        config.logger.info("account: LockException in setAccount(%s) line: %s %s",str(account_id),exc_tb.tb_lineno,e)
        # we couldn't fetch this lock. It seems to be blocked forever (from a crash?)
        # we remove the lock file and retry with a shorter timeout
        try:
            config.logger.info("acount: clean lock %s",str(account_cache_lock_path))
            Path(account_cache_lock_path).unlink()
            config.logger.debug("retry account:setAccount(%s)",str(account_id))
            with portalocker.Lock(account_cache_lock_path, timeout=0.3) as fh:
                return setAccountShelve(account_id,fh)
        except portalocker.exceptions.LockException as e:
            _, _, exc_tb = sys.exc_info()
            config.logger.error("account: LockException in setAccount(%s) line: %s %s",str(account_id),exc_tb.tb_lineno,e)
            return None
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            config.logger.error("account: Exception in setAccount(%s) line: %s %s",str(account_id),exc_tb.tb_lineno,e)
            return None
    except Exception as e:
        _, _, exc_tb = sys.exc_info()
        config.logger.error("account: Exception in setAccount(%s) line %s: %s",str(account_id),exc_tb.tb_lineno,e)
        return None
    finally:
        if account_cache_semaphore.available() < 1:
            account_cache_semaphore.release(1)

