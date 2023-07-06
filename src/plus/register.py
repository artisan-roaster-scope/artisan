#
# register.py
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

from typing import Optional, TextIO
from typing_extensions import Final  # Python <=3.7


_log: Final[logging.Logger] = logging.getLogger(__name__)

register_semaphore = QSemaphore(1)

uuid_cache_path = getDirectory(config.uuid_cache, share=True)
uuid_cache_path_lock = getDirectory(
    f'{config.uuid_cache}_lock', share=True
)


def addPathShelve(uuid: str, path: str, fh:TextIO) -> None:
    _log.debug('addPathShelve(%s,%s,_fh_)', uuid, path)
    import dbm
    import shelve
    db:shelve.Shelf[str]
    try:
        with shelve.open(uuid_cache_path) as db:
            db[uuid] = str(path)
        _log.debug(
            'DB type: %s', str(dbm.whichdb(uuid_cache_path))
        )
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
        try:
            # in case we couldn't open the shelve file as  "shelve.open
            # db type could not be determined" remove all files name
            # uuid_cache_path with any extension as we do not know which
            # extension is chosen by shelve
            _log.info(
                'clean uuid cache %s', str(uuid_cache_path)
            )
            # note that this deletes all "uuid" files including those for the
            # Viewer and other files of that name prefix like uuid.db.org!!
            for p in Path(Path(uuid_cache_path).parent).glob(
                f'{config.uuid_cache}*'
            ):
                if str(p) != uuid_cache_path_lock:
                    # if not the lock file, delete:
                    p.unlink()
            # try again to access/create the shelve file
            with shelve.open(uuid_cache_path) as db:
                db[uuid] = str(path)
            _log.info(
                'Generated db type: %s',
                str(dbm.whichdb(uuid_cache_path)),
            )
        except Exception as ex:  # pylint: disable=broad-except
            _log.exception(ex)
    finally:
        fh.flush()
        os.fsync(fh.fileno())


# register the path for the given uuid, assuming it points to the .alog profile
# containing that uuid
def addPath(uuid: str, path: str) -> None:
    _log.debug('addPath(%s,%s)', uuid, path)
    import portalocker
    fh:TextIO
    try:
        register_semaphore.acquire(1)
        with portalocker.Lock(uuid_cache_path_lock, timeout=0.5) as fh:
            addPathShelve(uuid, path, fh)
    except portalocker.exceptions.LockException as e:
        _log.exception(e)
        # we couldn't fetch this lock. It seems to be blocked forever
        # (from a crash?)
        # we remove the lock file and retry with a shorter timeout
        try:
            _log.info('clean lock %s', str(uuid_cache_path))
            Path(uuid_cache_path_lock).unlink()
            _log.debug(
                'retry register:addPath(%s,%s)', str(uuid), str(path)
            )
            with portalocker.Lock(uuid_cache_path_lock, timeout=0.3) as fh:
                addPathShelve(uuid, path, fh)
        except Exception as ex:  # pylint: disable=broad-except
            _log.exception(ex)
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if register_semaphore.available() < 1:
            register_semaphore.release(1)


# returns None if given UUID is not registered, otherwise the registered path
def getPath(uuid: str) -> Optional[str]:
    _log.debug('getPath(%s)', uuid)
    import portalocker
    import shelve
    fh:TextIO
    db:shelve.Shelf[str]
    try:
        register_semaphore.acquire(1)
        with portalocker.Lock(uuid_cache_path_lock, timeout=0.5) as fh:
            try:
                with shelve.open(uuid_cache_path) as db:
                    try:
                        res_path = str(db[uuid])
                        _log.debug(
                            'getPath(%s): %s', str(uuid), res_path
                        )
                        return res_path
                    except Exception:  # pylint: disable=broad-except
                        return None
            except Exception as e:  # pylint: disable=broad-except
                _log.exception(e)
                return None
            finally:
                fh.flush()
                os.fsync(fh.fileno())
    except portalocker.exceptions.LockException as e:
        _log.exception(e)
        # we couldn't fetch this lock. It seems to be blocked forever
        # (from a crash?) we remove the lock file and retry with
        # a shorter timeout
        try:
            _log.info(
                'clean lock %s', str(uuid_cache_path_lock)
            )
            Path(uuid_cache_path_lock).unlink()
            _log.debug('retry register:getPath(%s)', str(uuid))
            with portalocker.Lock(uuid_cache_path_lock, timeout=0.3) as fh:
                try:
                    with shelve.open(uuid_cache_path) as db:
                        try:
                            res_path = str(db[uuid])
                            _log.debug(
                                'getPath(%s): %s', str(uuid), res_path
                            )
                            return res_path
                        except Exception:  # pylint: disable=broad-except
                            return None
                except Exception as ex:  # pylint: disable=broad-except
                    _log.exception(ex)
                    return None
                finally:
                    fh.flush()
                    os.fsync(fh.fileno())
        except Exception as ex:  # pylint: disable=broad-except
            _log.exception(ex)
            return None
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
        return None
    finally:
        if register_semaphore.available() < 1:
            register_semaphore.release(1)


# scans all .alog files for UUIDs and registers them in the cache
def scanDir(path: Optional[str] = None) -> None:
    _log.debug('scanDir(%s)', path)
    try:
        assert config.app_window is not None
        if path is None:
            # search the last used path
            currentDictory = Path(
                config.app_window.getDefaultPath()
            )  # @UndefinedVariable
        else:
            currentDictory = Path(path)
        for currentFile in currentDictory.glob(f'*.{config.profile_ext}'):
            d = config.app_window.deserialize(
                str(currentFile)
            )  # @UndefinedVariable
            if d is not None and isinstance(d, str) and config.uuid_tag in d:
                addPath(d[config.uuid_tag], str(currentFile))  # @UndefinedVariable
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
