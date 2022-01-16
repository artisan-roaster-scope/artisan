# -*- coding: utf-8 -*-
#
# connection.py
#
# Copyright (c) 2021, Paul Holleis, Marko Luther
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
    from PyQt6.QtCore import QSemaphore, QTimer # @UnusedImport @Reimport  @UnresolvedImport
except Exception:
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import QSemaphore, QTimer # @UnusedImport @Reimport  @UnresolvedImport

from typing import Final, List

import logging

from plus import config, controller, connection

_log: Final = logging.getLogger(__name__)


get_notifications_semaphore = QSemaphore(
    1
)  # protects access to retrieveNotifications() to avoid parallel requests


# if notifications > 0 the new notifications are retrieved and forwarded to the user
# should only be called from the GUI thread
def updateNotifications(notifications: int, machines: List[str]):
    _log.debug("updateNotifications(%s,%s)",notifications,machines)
    try:
        if config.app_window:
            aw = config.app_window
            if notifications>0 or aw.qmc.roastertype_setup in machines:
                 # should happen with less delay (0.7s) then the stock.update() (2.5s) triggered controller.connect() to avoid duplicate fetching on startup
                QTimer.singleShot(700, retrieveNotifications)
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)

# fetches new notifications and forward them to the Artisan notification system
# sidecondition: at this point all pending notifications are delivered and the "notification" count on the server can be assumed to be 0
def retrieveNotifications():
    _log.debug("retrieveNotifications() before lock")
    gotlock = get_notifications_semaphore.tryAcquire(1,0) # we try to catch a lock if available but we do not wait, if we fail we just skip this sampling round (prevents stacking of waiting calls)
    if gotlock:
        try:
            _log.info("retrieveNotifications()")
            if controller.is_connected():
                aw = config.app_window
                if aw.qmc.roastertype_setup != "":
                    params = {"machine": aw.qmc.roastertype_setup}
                else:
                    params = None
                # fetch from server
                d = connection.getData(config.notifications_url, params=params)
                _log.debug("-> %s", d.status_code)
                res = d.json()
                _log.debug("-> retrieved")
                _log.debug("notifications = %s", res)
                # if success = true and result
                
                # TO BE DONE: process result in order (order by what?)                
                # process new account state:
                # here we need to hand over the new notifications to the Artisan notification system
                
                # NOTE: we do not updateLimitsFromResponse(res) here to avoid an infinit loop if the server does not reset the notifications counter. Further notifications will be retrieved on next request
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if get_notifications_semaphore.available() < 1:
                get_notifications_semaphore.release(1)
    else:
        _log.debug("TEST: retrieveNotification() lock was blocked")

# notification types
#  ADMIN => PLUS_ADMIN (issued by the plus admin app)
#  ADVERT => PLUS_ADVERT (advertisement message issued by the plus system)
#  REMINDER => PLUS_REMINDER (issued by the plus reminder system)
#  SYSTEM => PLUS_SYSTEM (system message issued by the system)
                    
#{
#   "success":true,
#   "result":[
#      {
#         "title":"english title",
#         "text":"english text",
#         "ntype":"ADMIN",
#         "added_on":"2021-12-21T08:02:52.041Z",
#         "match":[
#            {
#               
#            }
#         ],
#         "notmatch":[
#            {
#               
#            }
#         ],
#         "created_at":"2021-12-21T08:02:52.042Z",
#         "updated_at":"2021-12-21T08:02:52.042Z",
#         "hr_id":"N1000",
#         "__v":0
#      }
#   ],
#   "error":"",
#   "pu":"2021-11-30T11:00:00.000Z",
#   "ol":{
#      "rlimit":500
#   },
#   "notifications":1
#}