#
# connection.py
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
    from PyQt6.QtCore import QSemaphore, QTimer, pyqtSlot # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import QSemaphore, QTimer, pyqtSlot # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from typing import List, Dict, Any
from typing_extensions import Final  # Python <=3.7

import logging

from artisanlib.notifications import ntype2NotificationType
from plus import config, controller, connection, util

_log: Final[logging.Logger] = logging.getLogger(__name__)


get_notifications_semaphore = QSemaphore(
    1
)  # protects access to retrieveNotifications() to avoid parallel requests


# if notifications > 0 the new notifications are retrieved and forwarded to the user
# should only be called from the GUI thread
def updateNotifications(notifications: int, machines:List[str]) -> None:
    _log.debug('updateNotifications(%s,%s)',notifications,machines)
    try:
        if config.app_window:
            aw = config.app_window
            # we fetch notifications if notifications are enabled within the Artisan settings, there are some unqualified notifications, or
            # our machine name is in the list of machines indicating that there is a qualified notification for us
            if aw.notificationsflag and (notifications>0 or aw.qmc.roastertype_setup in machines):
                # should happen with less delay (0.7s) then the stock.update() (2.5s) triggered controller.connect() to avoid duplicate fetching on startup
                QTimer.singleShot(700, retrieveNotifications)
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)

# fetches new notifications and forward them to the Artisan notification system
# sidecondition: at this point all pending notifications are delivered and the "notification" count on the server can be assumed to be 0
@pyqtSlot()
def retrieveNotifications() -> None:
    gotlock = get_notifications_semaphore.tryAcquire(1,0)
    # we try to catch a lock if available but we do not wait, if we fail we just skip this sampling round (prevents stacking of waiting calls)
    if gotlock:
        try:
            _log.info('retrieveNotifications()')
            if controller.is_connected():
                aw = config.app_window
                if aw is not None and aw.qmc.roastertype_setup != '':
                    params = {'machine': aw.qmc.roastertype_setup}
                else:
                    params = None
                # fetch from server
                d = connection.getData(config.notifications_url, params=params)
                _log.debug('-> %s', d.status_code)
                res = d.json()
                _log.debug('-> retrieved')
                _log.debug('notifications = %s', res)
                if ('success' in res
                        and res['success']
                        and 'result' in res
                        and res['result']
                        and isinstance(res['result'],list)):
                    # we remove notifications that are tagged not_for_artisan:True
                    results = [r for r in res['result'] if not ('not_for_artisan' in r and r['not_for_artisan'])]
                    sorted_results = sorted(results, key=lambda nd: (util.ISO86012epoch(nd['added_on']) if 'added_on' in nd else 0))
                    # we present the notfications in reverse order, oldest first
                    for i, n in enumerate(sorted_results):
                        processNotification(n, i)

                # NOTE: we do not updateLimitsFromResponse(res) here to avoid an infinite loop if
                # the server does not reset the notifications counter. Further notifications will be retrieved on next request
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if get_notifications_semaphore.available() < 1:
                get_notifications_semaphore.release(1)


# process the received plus notifications and hand them over to the Artisan notification system
def processNotification(plus_notification:Dict[str,Any], i:int) -> None:
    try:
        if config.app_window is not None:
            aw = config.app_window
            if aw.notificationManager:
                created = None
                try:
                    created = util.ISO86012epoch(plus_notification['added_on'])
                except Exception as e:  # pylint: disable=broad-except
                    _log.error(e)
                aw.notificationManager.sendNotificationMessage(
                    util.extractInfo(plus_notification, 'title', ''),
                    util.extractInfo(plus_notification, 'text', ''),
                    ntype2NotificationType(util.extractInfo(plus_notification, 'ntype', '')),
                    created = created,
                    hr_id = util.extractInfo(plus_notification, 'hr_id', None),
                    link = util.extractInfo(plus_notification, 'link', None),
                    pos = i)
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
