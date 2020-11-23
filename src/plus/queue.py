#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# queue.py
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

import persistqueue
import threading
import time
from requests.exceptions import ConnectionError

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication

from plus import config, util, roast, connection, sync, controller

queue_path = util.getDirectory(config.outbox_cache,share=True)

app = QCoreApplication.instance()

queue = persistqueue.SQLiteQueue(queue_path,multithreading=True,auto_commit=False)
# auto_commit=False : we keep items in the queue if not explicit marked as task_done

# queue entries are dictionaries with entries
#   url   : the URL to send the request to
#   data  : the data dictionary that will be send in the body as JSON
#   verb  : the HTTP verb to be used (POST or PUT)

worker_thread = None


class Concur(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True  # OK for main to exit even if instance is still running
        self.paused = False  # start out non-paused
        self.state = threading.Condition()

    def addSyncItem(self,item):
        # successfully transmitted, we add/update the roasts UUID sync-cache
        if "roast_id" in item["data"] and "modified_at" in item["data"]:
            # we update the plus status icon
            sync.addSync(item["data"]["roast_id"],util.ISO86012epoch(item["data"]["modified_at"]))
            config.app_window.updatePlusStatusSignal.emit() # @UndefinedVariable
        
    def run(self):
        global queue
        config.logger.debug("queue:run()")
        time.sleep(config.queue_start_delay)
        self.resume() # unpause self
        item = None
        while True:
            time.sleep(config.queue_task_delay)
            with self.state:
                if self.paused:
                    self.state.wait() # block until notified
            config.logger.debug("queue: -> qsize: %s",queue.qsize())
            config.logger.debug("queue: looking for next item to be fetched")
            try:
                if item is None:
                    item = queue.get()
                time.sleep(config.queue_task_delay)
                config.logger.debug("queue: -> worker processing item: %s",item)
                iters = config.queue_retries + 1
                while iters > 0:
                    config.logger.debug("queue: -> remaining iterations: %s",iters)
                    r = None
                    try:
                        # we upload only full roast records, or partial updates in case the are under sync (registered in the sync cache)
                        if is_full_roast_record(item["data"]) or ("roast_id" in item["data"] and sync.getSync(item["data"]["roast_id"])):
                            controller.connect(clear_on_failure=False,interactive=False)
                            r = connection.sendData(item["url"],item["data"],item["verb"])
                            r.raise_for_status()
                            # successfully transmitted, we add/update the roasts UUID sync-cache
                            iters = 0
                            self.addSyncItem(item)
                            # if current roast was just successfully uploaded, we set the syncRecordHash to the full sync record
                            # to track further edits. Note we take a fresh (full) SyncRecord here as the uploaded record might contain only changed attributes
                            sr,h = roast.getSyncRecord()
                            if item["data"]["roast_id"] == sr["roast_id"]:
                                sync.setSyncRecordHash(sync_record = sr, h = h)
                        else:
                            # partial sync updates for roasts not registered for syncing are ignored
                            iters = 0
                    except ConnectionError as e:
                        try:
                            if controller.is_connected():
                                config.logger.debug("queue: -> connection error, disconnecting: %s",e)
                                # we disconnect
                                controller.disconnect(remove_credentials = False, stop_queue=True)
                        except:
                            pass
                        # we don't change the iter, but retry to connect after a delay in the next iteration
                        time.sleep(config.queue_retry_delay)
                    except Exception as e:
                        config.logger.debug("queue: -> task failed: %s",e)
                        if r is not None:
                            config.logger.debug("queue: -> status code %s",r.status_code)
                        else:
                            config.logger.debug("queue: -> no status code")
                        if r is not None and r.status_code == 401: # authentication failed
                            try:
                                if controller.is_connected():
                                    config.logger.debug("queue: -> connection error, disconnecting: %s",e)
                                    # we disconnect, but keep the queue running to let it automatically reconnect if possible
                                    controller.disconnect(remove_credentials = False, stop_queue=False)
                            except:
                                pass
                            iters = iters - 1
                            # we retry to connect after a delay in the next iteration
                            time.sleep(config.queue_retry_delay)
                        elif r is not None and r.status_code == 409: # conflict
                            iters = 0 # we don't retry, but remove the task as it is faulty
                        else: # 500 internal server error, 429 Client Error: Too Many Requests, 404 Client Error: Not Found or others
                            # something went wrong we don't mark this task as done and retry
                            iters = iters - 1
                            time.sleep(config.queue_retry_delay)                        
                # we call task_done to remove the item from the queue
                queue.task_done()
                item = None
                config.logger.debug("queue: -> task done")                
                config.logger.debug("queue: end of run:while paused=%s",self.paused)
            except Exception as e:
                pass

    def resume(self):
        config.logger.info("queue:resume()")
        with self.state:
            self.paused = False
            self.state.notify()  # unblock self if waiting

    def pause(self):
        config.logger.info("queue:pause()")
        with self.state:
            self.paused = True  # make self block and wait

        
def start():
    if app.artisanviewerMode:
        config.logger.info("queue:start(): queue not started in ArtisanViewer mode")
    else:
        global queue
        global worker_thread   
        config.logger.info("queue:start()")
        config.logger.debug("queue: -> qsize: %s",queue.qsize())
        if worker_thread is None:
            worker_thread = Concur()
            worker_thread.setDaemon(True) # a daemon thread is automatically killed on program exit
            worker_thread.start()
        else:
            worker_thread.resume()
    
# the queue worker thread cannot really be stopped, but we can pause it
def stop():
    if not app.artisanviewerMode:
        config.logger.info("queue:stop()")
        worker_thread.pause()

# check if a full roast record (one with date) with roast_id is in the queue
# this is used to add only items to the queue that are registered already in the sync cache
# but not yet uploaded as they are still in the queue
def full_roast_in_queue(roast_id):
    q = persistqueue.SQLiteQueue(queue_path,multithreading=True,auto_commit=False)
    try:
        while True:
            item = q.get(block=False)
            if "data" in item:
                r = item["data"]
                if is_full_roast_record(r) and roast_id == r["roast_id"]:
                    # there is a full roast record already in queue
                    break
        del q
        return True
    except: # we reached the end of the queue
        del q
        return False

################

# returns true if the given roast_record r is a full record containing all information (incl. the roast date) and not only an update
def is_full_roast_record(r):
    return "date" in r and r["date"] and "amount" in r and "roast_id" in r

# called on completed roasts with roast data
# if roast_record is given, we assume an update is queued, otherwise a new roast is queued
#   a full roast_record requires at least
#      - roast_id
#      - date
#      - amount
#   an update only the roast_id
def addRoast(roast_record = None):
    global queue
    try:
        config.logger.info("queue:addRoast()")
        if config.app_window.plus_readonly:
            config.logger.info("queue: -> roast not queued as users account access is readonly")
        else:
            if roast_record is None:
                r = roast.getRoast()
            else:
                r = roast_record
            # if modification date is not set yet, we add the current time as modified_at timestamp as float EPOCH with millisecond
            if not "modified_at" in r: 
                r["modified_at"] = util.epoch2ISO8601(time.time())
            config.logger.debug("queue: -> roast: %s",r)
            # check if all required data is available before queueing this up
            if "roast_id" in r and r["roast_id"] and \
               (roast_record is not None or ("date" in r and r["date"] and "amount" in r)): # amount can be 0 but has to be present
                # put in upload queue
                config.logger.debug("queue: -> put in queue")
                config.app_window.sendmessage(QApplication.translate("Plus","Queuing roast for upload to artisan.plus",None))    # @UndefinedVariable  
                if roast_record is not None:
                    # on updates only changed attributes w.r.t. the current cached sync record are uploaded
                    r = sync.diffCachedSyncRecord(r)
                queue.put({
                    "url": config.roast_url,
                    "data": r,
                    "verb": "POST"},
#                    timeout=config.queue_put_timeout # sql queue does not feature a timeout
                    )
                config.logger.debug("queue: -> roast queued up")
                config.logger.debug("queue: -> qsize: %s",queue.qsize())
            else:
                config.logger.debug("queue: -> roast not queued as mandatory info missing")
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("queue: Exception in addRoast() in line %s: %s",exc_tb.tb_lineno,e)
    

        
