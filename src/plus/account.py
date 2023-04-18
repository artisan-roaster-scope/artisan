#
# account.py
#
# Copyright (c) 2023, Paul Holleis, Marko Luther
# All rights reserved.
#
#
# ABOUT
# This module connects to the artisan.plus inventory management service

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""This module connects to the artisan.plus inventory management service."""

try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtCore import QSemaphore # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import QSemaphore # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from pathlib import Path
from artisanlib.util import getDirectory
from plus import config

import os
import logging
from typing import Optional
from typing_extensions import Final  # Python <=3.7

_log: Final[logging.Logger] = logging.getLogger(__name__)


####
# Account Cache
# holding all account ids associated to a (local) running account number
# shared cache between the Artisan and the ArtisanViewer app
account_cache_semaphore:QSemaphore = QSemaphore(1)

# shared resource between the Artisan and ArtisanViewer app protected
# by a file lock
account_cache_path:str = getDirectory(config.account_cache, share=True)
account_cache_lock_path:str = getDirectory(
    f'{config.account_cache}_lock', share=True
)


def setAccountShelve(account_id: str, fh) -> Optional[int]:
    _log.debug('setAccountShelve(%s,_fh_)', account_id)
    import dbm
    import shelve
    try:
        with shelve.open(account_cache_path) as db:
            if account_id in db:
                return db[account_id]
            new_nr = len(db)
            db[account_id] = new_nr
            try:
                _log.debug(
                    'DB type: %s', str(dbm.whichdb(account_cache_path))
                )
            except Exception:  # pylint: disable=broad-except
                pass
            return new_nr
    except Exception as ex:  # pylint: disable=broad-except
        _log.exception(ex)
        try:
            # in case we couldn't open the shelve file as "shelve.open db type
            # could not be determined" remove all files name account_cache
            # path with any extension as we do not know which extension is
            # chosen by shelve
            _log.info(
                'clean account cache %s', str(account_cache_path)
            )
            # note that this deletes all "account" files including those for
            # the Viewer and other files of that name prefix like
            # account.db.org!!
            for p in Path(Path(account_cache_path).parent).glob(
                f'{config.account_cache}*'
            ):
                if str(p) != account_cache_lock_path:
                    # if not the lock file, delete:
                    p.unlink()
            # try again to access/create the shelve file
            with shelve.open(account_cache_path) as db:
                if account_id in db:
                    return db[account_id]
                new_nr = len(db)
                db[account_id] = new_nr
                try:
                    _log.info(
                        'Generated db type: %s',
                        str(dbm.whichdb(account_cache_path)),
                    )
                except Exception:  # pylint: disable=broad-except
                    pass
                return new_nr
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
            return None
    finally:
        fh.flush()
        os.fsync(fh.fileno())


# register the given account_id and assign it a fresh number if not yet
# registered returns the number associated to account_id or None on error
def setAccount(account_id: str) -> Optional[int]:
    import portalocker
    try:
        account_cache_semaphore.acquire(1)
        _log.debug('setAccount(%s)', account_id)
        with portalocker.Lock(account_cache_lock_path, timeout=0.5) as fh:
            return setAccountShelve(account_id, fh)
    except portalocker.exceptions.LockException as e:
        _log.exception(e)
        # we couldn't fetch this lock. It seems to be blocked forever
        # we remove the lock file and retry with a shorter timeout
        _log.info(
            'clean lock %s', str(account_cache_lock_path)
        )
        Path(account_cache_lock_path).unlink()
        _log.debug(
            'retry setAccount(%s)', account_id
        )
        with portalocker.Lock(account_cache_lock_path, timeout=0.3) as fh:
            return setAccountShelve(account_id, fh)
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
        return None
    finally:
        if account_cache_semaphore.available() < 1:
            account_cache_semaphore.release(1)
