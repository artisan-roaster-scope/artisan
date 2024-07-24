#
# queue.py
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
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtCore import QCoreApplication, QObject, QThread, pyqtSlot, pyqtSignal # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import QCoreApplication, QObject, QThread, pyqtSlot, pyqtSignal # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.util import getDirectory
from plus import config, util, roast, connection, sync, controller
import threading
import time
import datetime
import json
import logging
from typing import Final, Any, List, Dict, Optional, TYPE_CHECKING  #for Python >= 3.9: can remove 'List' and 'Dict' since type hints can use the generic 'list' and 'dict'

if TYPE_CHECKING:
    import persistqueue # type:ignore[import-untyped] # pylint: disable=unused-import


_log: Final[logging.Logger] = logging.getLogger(__name__)

queue_path = getDirectory(config.outbox_cache, share=False)

app = QCoreApplication.instance()

queue:Optional['persistqueue.SQLiteQueue'] = None # type:ignore[no-any-unimported,unused-ignore] # holdes the persistqueue.SQLiteQueue, initialized by start()

# queue entries are dictionaries with entries
#   url   : the URL to send the request to
#   data  : the data dictionary that will be send in the body as JSON
#   verb  : the HTTP verb to be used (POST or PUT)

worker:Optional['Worker'] = None
worker_thread:Optional[QThread] = None


class Worker(QObject): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class
    startSignal = pyqtSignal()
    replySignal = pyqtSignal(float, float, str, int, list) # rlimit:float, rused:float, pu:str, notifications:int, machines:List[str]

    __slots__ = [ '_paused', '_state' ]

    def __init__(self) -> None:
        super().__init__()
        self._paused:bool = False  # start out non-paused
        self._state:threading.Condition = threading.Condition()

    @staticmethod
    def addSyncItem(item:Dict[str, Any]) -> None:
        # successfully transmitted, we add/update the roasts UUID sync-cache
        if 'roast_id' in item['data'] and 'modified_at' in item['data']:
            # we update the plus status icon
            sync.addSync(
                item['data']['roast_id'],
                util.ISO86012epoch(item['data']['modified_at']),
            )
            if config.app_window is not None:
                config.app_window.updatePlusStatusSignal.emit()  # @UndefinedVariable

    @pyqtSlot()
    def task(self) -> None:
        if queue is not None:
            from requests.exceptions import ConnectionError as RequestsConnectionError
            time.sleep(config.queue_start_delay)
            self.resume()  # unpause self
            item = None
            while True:
                time.sleep(config.queue_task_delay)
                with self._state:
                    if self._paused:
                        self._state.wait()  # block until notified
                _log.debug('-> qsize: %s', queue.qsize())
                _log.debug('looking for next item to be fetched')
                try:
                    if item is None:
                        item = queue.get()
                    time.sleep(config.queue_task_delay)
                    _log.debug(
                        '-> worker processing item: %s', item
                    )
                    iters = 1 # by default, if no modified_at timestamp is given (no roast; maybe just a lock schedule message) thus we don't retry this
                    if 'url' not in item:
                        # items without an url are discarded
                        iters = 0
                    if 'data' in item and 'modified_at' in item['data']:
                        item_age = time.time()-util.ISO86012epoch(item['data']['modified_at'])
                        if (config.queue_discard_after > 0 and item_age > config.queue_discard_after):
                            # old item scheduled to be removed from the queue
                            iters = 0
                            _log.debug('-> expired item %s removed from queue (%s min)',item['data']['roast_id'],int(round(item_age/60)))
                        else:
                            iters = config.queue_retries + 1
                    while iters > 0:
                        _log.debug(
                            '-> remaining iterations: %s', iters
                        )
                        r:Any = None
                        try:
                            # we upload only full roast records, or partial updates
                            # in case the are under sync
                            # (registered in the sync cache)
                            if is_full_roast_record(item['data']) or (
                                'roast_id' in item['data']
                                and sync.getSync(item['data']['roast_id'])
                            ):
                                controller.connect(
                                    clear_on_failure=False, interactive=False
                                )
                                r = connection.sendData(
                                    item['url'], item['data'], item['verb']
                                )
                                r.raise_for_status()
                                if config.app_window is not None:
                                    config.app_window.sendmessage(
                                        QApplication.translate(
                                            'Plus',
                                            'Roast successfully upload to {}'
                                        ).format(config.app_name)
                                    )  # @UndefinedVariable
                                # successfully transmitted, we add/update the
                                # roasts UUID sync-cache
                                self.addSyncItem(item)
                                # if current roast was just successfully uploaded,
                                # we set the syncRecordHash to the full sync record
                                # to track further edits. Note we take
                                # a fresh (full) SyncRecord here as the uploaded
                                # record might contain only changed attributes
                                sr, h = roast.getSyncRecord()
                                if item['data']['roast_id'] == sr['roast_id']:
                                    sync.setSyncRecordHash(sync_record=sr, h=h)
                                try:
                                    if r.status_code != 204 and r.headers['content-type'].strip().startswith('application/json'):
                                        response = r.json()
                                        if response:
                                            rlimit,rused,pu,notifications, machines = util.extractAccountState(response)
                                            self.replySignal.emit(rlimit,rused,pu,notifications,machines)

                                except json.decoder.JSONDecodeError as e:
                                    if not e.doc:
                                        _log.error('Empty response.')
                                    else:
                                        _log.error("Decoding error at char %s (line %s, col %s): '%s'", e.pos, e.lineno, e.colno, e.doc)
                                except ValueError:
                                    _log.error('Response content is not valid JSON')
                                except Exception as e:  # pylint: disable=broad-except
                                    _log.exception(e)
                            elif 'url' in item and item['url'].startswith(config.lock_schedule_url):
                                # this is not be a roast record, but a lock schedule message to be send to the server
                                controller.connect(
                                    clear_on_failure=False, interactive=False
                                )
                                r = connection.sendData(
                                    item['url'], item['data'], item['verb']
                                )
                                r.raise_for_status()
# maybe to much noise, this message would be send on each START
#                                if config.app_window is not None:
#                                    config.app_window.sendmessage(
#                                        QApplication.translate(
#                                            'Plus',
#                                            'Roast schedule of today locked on {}'
#                                        ).format(config.app_name)
#                                    )  # @UndefinedVariable

                            # partial sync updates for roasts not registered
                            # for syncing are ignored
                            iters = 0
                        except RequestsConnectionError as e:
                            try:
                                if controller.is_connected():
                                    _log.debug(
                                        ('-> connection error,'
                                         ' disconnecting: %s'),
                                        e,
                                    )
                                    # we disconnect
                                    controller.disconnect(
                                        remove_credentials=False, stop_queue=True
                                    )
                            except Exception as ex:  # pylint: disable=broad-except
                                _log.exception(ex)
                            # we don't change the iter, but retry to connect after
                            # a delay in the next iteration
                            time.sleep(config.queue_retry_delay)
                        except Exception as e:  # pylint: disable=broad-except
                            _log.debug('-> task failed: %s', e)
                            if r is not None:
                                _log.debug(
                                    '-> status code %s', r.status_code
                                )
                            else:
                                _log.debug('-> no status code')
                            if (
                                r is not None and r.status_code == 401
                            ):  # authentication failed
                                try:
                                    if controller.is_connected():
                                        _log.debug(
                                            ('-> connection error,'
                                             ' disconnecting: %s'),
                                            e,
                                        )
                                        # we disconnect, but keep the queue running
                                        # to let it automatically reconnect
                                        # if possible
                                        controller.disconnect(
                                            remove_credentials=False,
                                            stop_queue=False,
                                        )
                                except Exception as ex:  # pylint: disable=broad-except
                                    _log.exception(ex)
                                iters = iters - 1
                                # we retry to connect after a delay in the next
                                # iteration
                                time.sleep(config.queue_retry_delay)
                            elif (
                                r is not None and r.status_code == 409
                            ):  # conflict
                                # we don't retry, but remove the task
                                # as it is faulty
                                iters = 0
                            else:
                                # 500 internal server error, 429 Client Error:
                                # Too Many Requests, 404 Client Error: Not Found
                                # or others something went wrong we don't mark
                                # this task as done and retry
                                iters = iters - 1
                                time.sleep(2*config.queue_retry_delay)
                    # we call task_done to remove the item from the queue
                    queue.task_done()
                    item = None
                    _log.debug(
                        'end of run:while paused=%s', self._paused
                    )
                except Exception as e:  # pylint: disable=broad-except
                    _log.exception(e)

    def resume(self) -> None:
        _log.debug('resume()')
        with self._state:
            self._paused = False
            self._state.notify()  # unblock self if waiting

    def pause(self) -> None:
        _log.debug('pause()')
        with self._state:
            self._paused = True  # make self block and wait

# will be evaluated in GUI thread
def processReply(rlimit:float, rused:float, pu:str, notifications:int, machines:List[str]) -> None:
    try:
#        _log.debug('thread id', threading.get_ident())
        _log.debug('processReply(%s,%s,%s,%s,%s', rlimit, rused, pu, notifications, machines)
    except Exception:  # pylint: disable=broad-except
        pass

def start() -> None:
#    if app.artisanviewerMode:
#        _log.info(
#            "start(): queue not started in ArtisanViewer mode"
#        )
#        return
    global queue  # pylint: disable=global-statement
    global worker, worker_thread  # pylint: disable=global-statement

    if queue is None:
        # we initialize the queue
        import persistqueue
        queue = persistqueue.SQLiteQueue(
            queue_path, multithreading=True, auto_commit=False
        )
        # we keep items in the queue if not explicit marked as task_done:
        # auto_commit=False


    _log.debug('start()')
    if queue is not None:
        _log.debug('-> qsize: %s', queue.qsize())
    if worker_thread is None:
        worker = Worker()
        worker_thread = QThread()
        worker_thread.start()
        worker.moveToThread(worker_thread)
        worker.startSignal.connect(worker.task)
        worker.replySignal.connect(util.updateLimits)
        #app.aboutToQuit.connect(end)
        worker.startSignal.emit()
        _log.debug('queue started')
    elif worker is not None:
        worker.resume()
        _log.debug('queue resumed')


# the queue worker thread cannot really be stopped, but we can pause it
def stop() -> None:
    if worker is not None:
        worker.pause()
        _log.debug('queue stopped')


# check if a full roast record (one with date) with roast_id is in the queue
# this is used to add only items to the queue that are registered already in
# the sync cache but not yet uploaded as they are still in the queue
def full_roast_in_queue(roast_id: str) -> bool:
    import persistqueue
    q = persistqueue.SQLiteQueue(
        queue_path, multithreading=True, auto_commit=False
    )
    try:
        while True:
            item = q.get(block=False)
            if 'data' in item:
                r = item['data']
                if is_full_roast_record(r) and roast_id == r['roast_id']:
                    # there is a full roast record already in queue
                    break
        del q
        return True
    except Exception:  # pylint: disable=broad-except
        # we reached the end of the queue
        del q # noqa: F821
        return False


################

# returns true if the given roast_record r is a full record containing all
# information (incl. the roast date) and not only an update
def is_full_roast_record(r: Dict[str, Any]) -> bool:  #for Python >= 3.9 can replace 'Dict' with the generic type hint 'dict'
    return 'date' in r and r['date'] and 'amount' in r and 'roast_id' in r


# called on completed roasts with roast data
# if roast_record is given, we assume an update is queued, otherwise a new
# roast is queued
#   a full roast_record requires at least
#      - roast_id
#      - date
#      - amount
#   an update only the roast_id
def addRoast(roast_record:Optional[Dict[str, Any]] = None) -> None:
    try:
        _log.debug('addRoast()')
        if config.app_window is None:
            _log.info('config.app_window is None')
        elif config.app_window.plus_readonly:
            _log.info(
                '-> roast not queued as users'
                 ' account access is readonly'
            )
        elif queue is None:
            _log.info(
                '-> roast not queued as queue'
                 ' is not running'
            )
        else:
            r: Dict[str, Any]
            r = roast.getRoast() if roast_record is None else roast_record
            # if modification date is not set yet, we add the current time as
            # modified_at timestamp as float EPOCH with millisecond
            if 'modified_at' not in r:
                r['modified_at'] = util.epoch2ISO8601(time.time())
            _log.debug('-> roast: %s', r)
            # check if all required data is available before queueing this up
            if (
                'roast_id' in r
                and r['roast_id']
                and (
                    roast_record is not None
                    or ('date' in r and r['date'] and 'amount' in r)
                )
            ):  # amount can be 0 but has to be present
                # put in upload queue
                _log.debug('-> put in queue')
                config.app_window.sendmessage(
                    QApplication.translate(
                        'Plus',
                        'Queuing roast for upload to artisan.plus'
                    )
                )  # @UndefinedVariable
                rr: Dict[str, Any]
                if roast_record is not None:
                    # on updates only changed attributes w.r.t. the current
                    # cached sync record are uploaded
                    rr = sync.diffCachedSyncRecord(r)
                else:
                    rr = r
                # send zero values like 0 and '' for corresponding attributes as None to allow the server to clean those up
                rr = sync.surpress_zero_values(rr)
                queue.put(
                    {'url': config.roast_url, 'data': rr, 'verb': 'POST'},
                    # timeout=config.queue_put_timeout
                    # sql queue does not feature a timeout
                )
                _log.debug('-> roast queued up')
                if 'roast_id' in rr:
                    _log.info('roast queued: %s', rr['roast_id'])
                _log.debug('-> qsize: %s', queue.qsize())
            else:
                _log.debug(
                    '-> roast not queued as mandatory info missing'
                )
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)

def sendLockSchedule() -> None:
    try:
        _log.debug('sendLockSchedule()')
        if config.app_window is None:
            _log.info('config.app_window is None')
        elif config.app_window.plus_readonly:
            _log.info(
                '-> lockSchedule not queued as users'
                 ' account access is readonly'
            )
        elif queue is None:
            _log.info(
                '-> lockSchedule not queued as queue'
                 ' is not running'
            )
        else:
            queue.put(
                {'url': f'{config.lock_schedule_url}?today={datetime.datetime.now().astimezone().date()}', 'data': {}, 'verb': 'POST'},
                # timeout=config.queue_put_timeout
                # sql queue does not feature a timeout
            )
            _log.debug('-> lockSchedule queued up')
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
