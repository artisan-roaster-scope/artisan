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

import shelve
import portalocker

from PyQt5.QtCore import QSemaphore

from plus import config, util


#### Account Cache

# holding all account ids associated to a (local) running number
# shared cache between the Artisan and the ArtisanViewer app

account_cache_semaphore = QSemaphore(1)

# shared resource between the Artisan and ArtisanViewer app protected by a file lock
account_cache_path = util.getDirectory(config.account_cache,share=True)
account_cache_lock_path = util.getDirectory(config.account_cache + "_lock",share=True)

# register the given account_id and assign it a fresh number if not yet registered
# returns the number associated to account_id or None on error
def setAccount(account_id):
    try:
        config.logger.debug("account:setAccount(" + str(account_id) + ")")
        account_cache_semaphore.acquire(1)
        with portalocker.Lock(account_cache_lock_path, timeout=1) as _:
            with shelve.open(account_cache_path) as db:
                if account_id in db:
                    return db[account_id]
                else:
                    new_nr = len(db)
                    db[account_id] = new_nr
                    return new_nr
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("account: Exception in setAccount() line %s: %s",exc_tb.tb_lineno,e)
        return None
    finally:
        if account_cache_semaphore.available() < 1:
            account_cache_semaphore.release(1)

