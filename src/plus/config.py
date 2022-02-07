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
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#import logging
#from logging.handlers import RotatingFileHandler
from typing import Optional
try:
    from typing import Final
except ImportError:
    # for Python 3.7:
    from typing_extensions import Final


try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtWidgets import QMainWindow # @UnusedImport @Reimport  @UnresolvedImport
except Exception:
    #pylint: disable = E, W, R, C
    from PyQt5.QtWidgets import QMainWindow # @UnusedImport @Reimport  @UnresolvedImport

# Constants
app_name: Final = "artisan.plus"
profile_ext: Final = "alog"
uuid_tag: Final = "roastUUID"

# Serivce URLs

# # LOCAL SETUP
#api_base_url         = "https://localhost:62602/api/v1"
#web_base_url         = "https://localhost:8088"

# # CLOUD SETUP
api_base_url: Final = "https://artisan.plus/api/v1"
web_base_url: Final = "https://artisan.plus"

shop_base_url: Final = "https://shop.artisan.plus"

register_url: Final = web_base_url + "/register"
reset_passwd_url: Final = web_base_url + "/resetPassword"
auth_url: Final = api_base_url + "/accounts/users/authenticate"
stock_url: Final = api_base_url + "/acoffees"
roast_url: Final = api_base_url + "/aroast"
notifications_url: Final = api_base_url + "/notifications"

# Connection configurations

#verify_ssl       = False
verify_ssl: Final = True
connect_timeout: Final = 2  # in seconds
read_timeout: Final = 4  # in seconds
min_passwd_len: Final = 4
min_login_len: Final = 6
compress_posts: Final = True
# post_compression_threshold holds the number in bytes before compression
# kicks in
# (data smaller than this are always send uncompressed via POST)
post_compression_threshold: Final = 500

# Authentication configuration

# do not authentify successfully after max_days after the subscription expired
expired_subscription_max_days: Final = 90

# Cache and queue parameters

stock_cache_expiration: Final = 30  # expiration period in seconds

queue_start_delay: Final = 5  # startup time of queue in seconds
# delay between tasks in seconds (cycling interval of the queue)
queue_task_delay: Final = 0.7
queue_retries: Final = 2  # number of retries (should be >=0)
queue_retry_delay: Final = 30  # time between retries in seconds
# queque_put_timeout indicates the number of seconds to wait on putting
# a new item into the queue (unused for now)
queue_put_timeout: Final = 0.5


# AppData

# the stock cache reflects the current coffee stock of the account and
# gets automatically synced with the cloud
stock_cache: Final = "cache"

# the uuid register that associates UUIDs with local filepaths where to
# locate the corresponding Artisan profiles
uuid_cache: Final = "uuids"

# the account register that associates account ids with a local running
# account number
# Note: the account_cache file is shared between the main Artisan and the
# ArtisanViewer app, protected by a filelock
account_cache: Final = "account"

# the account nr locally assocated to the current account, or None
account_nr: Optional[int] = None

# the sync register that associates UUIDs with last known modification dates
# modified_at for profiles uploaded/synced automatially
# Note: the sync_cache file is shared between the main Artisan and the
# ArtisanViewer app, protected by a filelock
sync_cache: Final = "sync"

# the outbox queues the outgoing PUSH/PUT data requests
# Note: the outbox_cache file is shared between the main Artisan and the
# ArtisanViewer app, NOT protected by ab extra filelock
outbox_cache: Final = "outbox"


# Runtime variables

app_window = None  # handle to the main Artisan application window
#   if set, app_window.plus_login holds the current login account if any and
#   app_window.updatePlusIcon() is a function that updates the toolbar
#   plus service connection indicator icon
connected = False  # connection status
passwd : Optional[str] = None
# the session token
token: Optional[str] = None
# login nickname assigned on login with session token
nickname: Optional[str] = None
