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

from pathlib import Path
from persistqueue import Queue
import threading
import time

from PyQt5.QtWidgets import QApplication

from plus import config, util, roast, connection, sync, controller

queue_path = util.getDirectory(config.outbox_cache)


queue = Queue(queue_path)

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
            config.logger.debug("queue: looking for next item to be fetched")
            if item is None:
                item = queue.get()
            time.sleep(config.queue_task_delay)
            config.logger.debug("queue: -> worker processing item: %s",item)
            iters = config.queue_retries + 1
            keepTask = False
            while iters > 0:
                config.logger.debug("queue: -> remaining iterations: %s",iters)
                r = None
                try:
                    r = connection.sendData(item["url"],item["data"],item["verb"])
                    r.raise_for_status()
                    iters = 0
                    # successfully transmitted, we add/update the roasts UUID sync-cache
                    if "roast_id" in item["data"] and "modified_at" in item["data"]:
                        # we update the plus status icon if the given roast_id was not yet in the sync cache and thus new
                        if sync.getSync(item["data"]["roast_id"]) is None:
                            sync.addSync(item["data"]["roast_id"],util.ISO86012epoch(item["data"]["modified_at"]))
                            config.app_window.updatePlusStatusSignal.emit() # @UndefinedVariable
                        else:
                            sync.addSync(item["data"]["roast_id"],util.ISO86012epoch(item["data"]["modified_at"]))
                except Exception as e:
                    config.logger.debug("queue: -> task failed: %s",e)
                    if r is not None:
                        config.logger.debug("queue: -> status code %s",r.status_code)
                    if r is not None and r.status_code == 401: # authentication failed
                        controller.disconnect(remove_credentials = False)
                        iters = 0 # we don't retry and keep the task item
                        keepTask = True
                    elif r is not None and r.status_code == 409: # conflict
                        iters = 0 # we don't retry, but remove the task as it is faulty
                    else: # 500 internal server error, 429 Client Error: Too Many Requests, 404 Client Error: Not Found or others
                        # something went wrong we don't mark this task as done and retry
                        iters = iters - 1
                        time.sleep(config.queue_retry_delay)                        
            if not keepTask:
                # we call task_done to remove the item from the queue
                queue.task_done()
                item = None
                config.logger.debug("queue: -> task done")                
            config.logger.debug("queue: end of run:while paused=%s",self.paused)

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
    config.logger.info("queue:stop()")
    worker_thread.pause()


################


# called on completed roasts with roast data
# if roast_record is given, we assume an update is queue, otherwise a new roast is queued
#   a full roast_record requires at least
#      - roast_id
#      - date
#      - amount
#   an update only the roast_id
def addRoast(roast_record = None):
    global queue
    try:
        config.logger.info("queue:addRoast()")
        if roast_record == None:
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
            queue.put({
                "url": config.roast_url,
                "data": r,
                "verb": "POST"})
            config.logger.debug("queue: -> roast queued up")
            config.logger.debug("queue: -> qsize: %s",queue.qsize())
            sync.setSyncRecordHash(r)
        else:
            config.logger.debug("queue: -> roast not queued as mandatory info missing")
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("queue: Exception in addRoast() in line %s: %s",exc_tb.tb_lineno,e)
    

        
