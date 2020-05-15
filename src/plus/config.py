#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# config.py
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

import logging
from logging.handlers import RotatingFileHandler

from plus import util

# Constants

app_name         = "artisan.plus"
profile_ext      = "alog"
uuid_tag         = "roastUUID"

# Serivce URLs

## LOCAL SETUP
#api_base_url         = "https://localhost:62602/api/v1"
#web_base_url         = "https://localhost:8088"

## CLOUD SETUP
api_base_url         = "https://artisan.plus/api/v1"
web_base_url         = "https://artisan.plus"

shop_base_url         = "https://shop.artisan.plus"

register_url     = web_base_url + "/register"
reset_passwd_url = web_base_url + "/resetPassword"
auth_url         = api_base_url + "/accounts/users/authenticate"
stock_url        = api_base_url + "/acoffees"
roast_url        = api_base_url + "/aroast"

# Connection configurations

#verify_ssl       = False
verify_ssl       = True
connect_timeout  = 2 # in seconds
read_timeout     = 4 # in seconds
min_passwd_len   = 4
min_login_len    = 6
compress_posts   = True
post_compression_threshold = 500 # in bytes (data smaller than this are always send uncompressed via POST)

# Authentication configuration

# do not authentify successfully after max_days after the subscription expired
expired_subscription_max_days = 90

# Cache and queue parameters

stock_cache_expiration = 30 # expiration period in seconds

queue_start_delay = 5 # startup time of queue in seconds
queue_task_delay = 0.7 # delay between tasks in seconds (cycling interval of the queue)
queue_retries = 2 # number of retries (should be >=0)
queue_retry_delay = 30 # time between retries in seconds
queue_put_timeout = 0.5 # number of seconds to wait on putting a new item into the queue (unused for now)


# AppData

# the stock cache reflects the current coffee stock of the account and gets automatically synced with the cloud
stock_cache = "cache"

# the uuid register that associates UUIDs with local filepaths where to locate the corresponding Artisan profiles
uuid_cache = "uuids"

# the account register that associates account ids with a local running account number
# Note: the account_cache file is shared between the main Artisan and the ArtisanViewer app, protected by a filelock
account_cache = "account"

# the account nr locally assocated to the current account, or None
account_nr = None

# the sync register that associates UUIDs with last known modification dates modified_at for profiles uploaded/synced automatially
# Note: the sync_cache file is shared between the main Artisan and the ArtisanViewer app, protected by a filelock
sync_cache = "sync"

# the outbox queues the outgoing PUSH/PUT data requests
# Note: the outbox_cache file is shared between the main Artisan and the ArtisanViewer app, NOT protected by ab extra filelock
outbox_cache = "outbox"

# the log_file logs communication and other important events
log_file = "artisan_plus"

# logfile email destination
log_file_domain = "artisan.plus"
log_file_account = "logfile"


# Logging

log_file_path = util.getDirectory(log_file,".log")

logger = logging.getLogger("plus")
#logger.setLevel(logging.NOTSET)
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)
try:
    handler = RotatingFileHandler(log_file_path, maxBytes=200000, backupCount=1, encoding='utf-8')
    handler.setLevel(logging.INFO)
#    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s') # - %(name)s 
    handler.setFormatter(formatter)
    logger.addHandler(handler)
except: # if permission on the log file is denied, fail silently
    pass

## Usage:
##   config.logger.info("something")
##   config.logger.debug('%s iteration, item=%s', i, item)



# Runtime variables

app_window       = None     # handle to the main Artisan application window
                            #   if set, app_window.plus_login holds the current login account if any and
                            #   app_window.updatePlusIcon() is a function that updates the toolbar plus service connection indicator icon 
connected = False         # connection status
passwd = None
token = None              # the session token
nickname = None           # login nickname assigned on login with session token