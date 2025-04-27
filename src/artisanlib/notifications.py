#
# ABOUT
# Artisan Notification System

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2023

try:
    from PyQt6.QtWidgets import QSystemTrayIcon, QApplication, QMenu # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QIcon, QDesktopServices, QAction # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtCore import QTimer, pyqtSlot, QUrl, QObject, QDateTime, QLocale # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtWidgets import QSystemTrayIcon, QApplication, QMenu, QAction # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QIcon, QDesktopServices # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtCore import QTimer, pyqtSlot, QUrl, QObject, QDateTime, QLocale # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

import os
import sys
import time
import logging
from datetime import datetime, timezone
from enum import Enum, unique
from artisanlib.util import getResourcePath
from artisanlib.qtsingleapplication import QtSingleApplication
import plus.util
import plus.connection
import plus.config

from typing import Final, Optional, List, Union

_log: Final[logging.Logger] = logging.getLogger(__name__)

@unique
class NotificationType(Enum):
    ARTISAN_SYSTEM = 1 # issued by some internal Artisan activity
    ARTISAN_USER = 2   # issues with notify() Artisan Command
    PLUS_SYSTEM = 3    # an artisan.plus system notification
    PLUS_REMINDER = 4  # an artisan.plus reminder notification
    PLUS_ADMIN = 5     # an artisan.plus admin message
    PLUS_ADVERT = 6    # an artisan.plus advertisement

# maps an artisan.plus notification ntype type string to the corresponding Artisan NotificationType
def ntype2NotificationType(ntype:str) -> NotificationType:
    ntype = ntype.upper()
    if ntype == 'ADMIN':
        return NotificationType.PLUS_ADMIN
    if ntype == 'ADVERT':
        return NotificationType.PLUS_ADVERT
    if ntype == 'REMINDER':
        return NotificationType.PLUS_REMINDER
    return NotificationType.PLUS_SYSTEM

# for notifications received from artisan.plus id is set to the notifications hr_id to be able to confirm its processing on click
# created is the timestamp as EPOCH indicating when this notification was created
class Notification:
    def __init__(self, title: str, message: str, notification_type: NotificationType, created: Optional[float] = None, hr_id: Optional[str] = None, link: Optional[str] = None) -> None:
        self._title:str = title
        self._message:str = message
        self._type:NotificationType = notification_type
        self._created:float
        if created is None:
            self._created = time.time()
        else:
            self._created = created
        self._id:Optional[str] = hr_id
        self._link:Optional[str] = link

    @property
    def title(self) -> str:
        return self._title

    @property
    def message(self) -> str:
        return self._message

    @property
    def type(self) -> NotificationType: # noqa: A003
        return self._type

    @property
    def created(self) -> float:
        return self._created

    @property
    def id(self)-> Optional[str]: # noqa: A003
        return self._id

    @property
    def link(self) -> Optional[str]: # noqa: A003
        return self._link

    def formatedTitle(self) -> str:
        seconds_to = time.time() - self._created
        if seconds_to < 24*60*60:
            # create within last 24h
            return self._title
        if seconds_to < 7*24*60*60:
            # created within the past 7 days
            dt = QDateTime.fromSecsSinceEpoch(int(round(self._created)))
            day_name = QLocale().standaloneDayName(dt.date().dayOfWeek(), QLocale.FormatType.LongFormat)
            return f'{self._title} ({day_name})'
        # created more than 7 days ago
        ll = QLocale()
        dt = QDateTime.fromSecsSinceEpoch(int(round(self._created)))
        short_date = ll.toString(dt.date(), ll.dateFormat(QLocale.FormatType.NarrowFormat))
        return f'{self._title} ({short_date})'


# data a datetime.datetime object representing the timestamp of the acknowledgement by the user
def sendPlusNotificationSeen(hr_id:str, date:datetime) -> None:
    _log.debug('sendPlusNotificationSeen(%s,%s)', hr_id, date.isoformat())
    try:
        plus.connection.sendData(
            f'{plus.config.notifications_url}/seen/{hr_id}',
            { 'date' : date.isoformat()},
            'PUT')
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)


class NotificationManager(QObject): # pyright: ignore [reportGeneralTypeIssues]

    __slots__ = ( 'notification_timeout', 'notification_queue_max_length', 'notification_queue_max_age',
                'tray_menu', 'tray_icon', 'notifications_available', 'notifications_enabled', 'notifications_visible',
                'notifications_queue', 'active_notification', 'notification_menu_actions' )

    def __init__(self) -> None:
        super().__init__()

        # time to display a notification
        self.notification_timeout: Final = 12000 # 6000 # in ms
        # we keep the last n notifications in the tray icon menu
        self.notification_queue_max_length: Final = 5
        # notifications older then queue_max_age are automatically removed from the try icon menu and newly received not even added to the queue
        self.notification_queue_max_age: Final = 30*24*60*60 # in seconds (30 days = 30*24*60*60)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_menu = QMenu()

        # notfication_available is true if the operating system supports notifications
        self.notifications_available = self.tray_icon.isSystemTrayAvailable() and self.tray_icon.supportsMessages()
        if self.notifications_available:
            # the tray icon is displayed only if notifications are supported by the system
            self.tray_icon.setIcon(self.artisanTrayIcon())
            self.tray_icon.setToolTip('Artisan Notifications')
            self.tray_icon.messageClicked.connect(self.messageClicked)
            #self.tray_icon.show() # if try_icon is not visible, notifications are not delivered
            self.tray_icon.setContextMenu(self.tray_menu)

        self.notifications_enabled = True # if False, issued notification messages are ignored
        self.notifications_visible = True # if False, the tray_menu icon (and thus notifications) are not shown
        self.notifications_queue:List[Notification] = [] # FIFO of Notification objects. Note: notification ids of all queued notifications are unique if given (not None)
        # the allocated menu actions
        self.notification_menu_actions:List[QAction] = []
        # holds the currently displayed notification
        self.active_notification:Optional[Notification] = None

    @staticmethod
    def artisanTrayIcon() -> QIcon:
        basedir = os.path.join(getResourcePath(),'Icons')
        if sys.platform.startswith('darwin'):
            p = os.path.join(basedir, 'artisan-trayicon.svg')
        else:
            p = os.path.join(basedir, 'artisan-trayicon-large.svg')
        icon = QIcon(p)
        icon.setIsMask(True)
        return icon

    # returns the plus icon as QIcon
    @staticmethod
    def notificationPlusIcon() -> QIcon:
        basedir = os.path.join(getResourcePath(),'Icons')
        if sys.platform.startswith('darwin'):
            p = os.path.join(basedir, 'plus-notification.png')
        else:
            p = os.path.join(basedir, 'plus-notification.svg')
        return QIcon(p)

    # returns the Artisan icon as QIcon
    @staticmethod
    def notificationArtisanIcon() -> QIcon:
        basedir = os.path.join(getResourcePath(),'Icons')
        if sys.platform.startswith('darwin'):
            p = os.path.join(basedir, 'artisan-notification.png')
        else:
            p = os.path.join(basedir, 'artisan-notification.svg')
        return QIcon(p)

    @pyqtSlot()
    def messageClicked(self) -> None:
        try:
            if self.active_notification:
                try:
                    if self.active_notification.type in [NotificationType.ARTISAN_SYSTEM, NotificationType.ARTISAN_USER]:
                        # raise Artisan app
                        app = QApplication.instance()
                        if app is not None:
                            assert isinstance(app, QtSingleApplication)
                            app.activateWindow()
                    elif self.active_notification.type in [NotificationType.PLUS_SYSTEM, NotificationType.PLUS_ADMIN, NotificationType.PLUS_ADVERT]:
                        if self.active_notification.link is None:
                            # open artisan.plus
                            QDesktopServices.openUrl(QUrl(plus.util.plusLink()))
                        else:
                            try:
                                QDesktopServices.openUrl(QUrl(self.active_notification.link))
                            except Exception:  # pylint: disable=broad-except
                                # if given link URL is not valid still open artisan.plus
                                QDesktopServices.openUrl(QUrl(plus.util.plusLink()))
                    elif self.active_notification.type == NotificationType.PLUS_REMINDER:
                        # open artisan.plus reminder tab
                        QDesktopServices.openUrl(QUrl(plus.util.remindersLink()))
                except Exception:  # pylint: disable=broad-except
                    pass
                if self.active_notification.id:
                    n = self.active_notification.id # bind the number here such that is available after clearing active_notification
                    QTimer.singleShot(500, lambda : sendPlusNotificationSeen(n, datetime.now(timezone.utc)))
                self.removeNotificationItem(self.active_notification)
                self.active_notification = None
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    def showNotifications(self) -> None:
        try:
            if self.notifications_available:
                self.notifications_visible = True
                if len(self.notifications_queue)>0:
                    self.tray_icon.show()
                    self.updateNotificationMenu()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    def hideNotifications(self) -> None:
        try:
            if self.notifications_available:
                self.notifications_visible = False
                self.tray_icon.hide()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    # if notifications are enabled, incoming notifications are presented to user
    def enableNotifications(self) -> None:
        self.notifications_enabled = True

    # if notifications are disabled, incoming notifications are just ignore
    def disableNotifications(self) -> None:
        self.notifications_enabled = False

    def getNotificationItems(self) -> List[Notification]:
        return self.notifications_queue

    def addNotificationItem(self, notification: Notification) -> None:
        _log.debug('addNotificationItem()')
        self.notifications_queue.append(notification)
        self.updateNotificationMenu()

    def removeNotificationItem(self, notification: Notification) -> None:
        self.notifications_queue.remove(notification)
        self.updateNotificationMenu()

    def clearNotificationQueue(self) -> None:
        self.notifications_queue = []

    def isNotificationInQueue(self, hr_id:Optional[str]) -> bool:
        return not id and any(n.id == hr_id for n in self.getNotificationItems()) # type: ignore

    def cleanNotificationQueue(self) -> None:
        try:
            # remove outdated entries
            age_limit = time.time() - self.notification_queue_max_age
            self.notifications_queue = [n for n in self.notifications_queue if n.created>age_limit]
            # limit the queue to maximal length
            self.notifications_queue = self.notifications_queue[max(0,len(self.notifications_queue)-self.notification_queue_max_length):]
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    def updateNotificationMenu(self) -> None:
        _log.debug('updateNotificationMenu()')
        try:
            self.cleanNotificationQueue()
            self.tray_menu.clear()
            self.notification_menu_actions = []
            if len(self.notifications_queue)>0 and self.notifications_visible:
                self.tray_icon.show()

                for n in reversed(self.notifications_queue):
                    title = n.formatedTitle()
                    menu_title = (title[:25] + '...') if len(title) > 25 else title
#                    action = QAction(menu_title, visible=True, triggered=self.notificationItemSelected)
                    action = QAction(menu_title)
                    action.triggered.connect(self.notificationItemSelected)
                    action.setData(n)
                    self.notification_menu_actions.append(action)
                    self.tray_menu.addAction(action)
            else:
                self.tray_icon.hide()
#                try:
#                    app = QApplication.instance()
#                    app.setBadgeNumber(0) # type: ignore # "QCoreApplication" has no attribute "setBadgeNumber"
#                except Exception: # pylint: disable=broad-except
#                    pass # setBadgeNumber only supported by Qt 6.5 and newer
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    @pyqtSlot(bool)
    def notificationItemSelected(self, _checked:bool = False) -> None:
        action = self.sender()
        if action is not None and hasattr(action, 'data'):
            n = action.data()
            self.setNotification(n, addToQueue=False)

    # actually presents the given notification to the user
    def showNotification(self, notification: Notification) -> None:
        _log.debug('showNotification(%s)',notification)
        try:
            icon:Union[QIcon, QSystemTrayIcon.MessageIcon] = QSystemTrayIcon.MessageIcon.Information # NoIcon, Information, Warning, Critical
            if notification.type in [NotificationType.ARTISAN_SYSTEM, NotificationType.ARTISAN_USER]:
                icon = self.notificationArtisanIcon()
            elif notification.type in [
                    NotificationType.PLUS_SYSTEM,
                    NotificationType.PLUS_REMINDER,
                    NotificationType.PLUS_ADMIN,
                    NotificationType.PLUS_ADMIN]:
                icon = self.notificationPlusIcon()
            self.tray_icon.showMessage(notification.formatedTitle(), notification.message, icon, self.notification_timeout)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    # set the given notification as the active one and shows it to the user
    def setNotification(self, notification: Notification, addToQueue:bool = True) -> None:
        _log.info('setNotification(%s, %s, %s, %s)', notification.type.name, notification.formatedTitle(), notification.message, addToQueue)
        try:
            self.active_notification = notification
            if addToQueue:
                self.addNotificationItem(notification) # also shows tray_menu icon if self.notifications_visible
            # we set a timer to clear this notification after the presentation timeout
#            QTimer.singleShot(self.notification_timeout, lambda : self.clearNotification(notification))
            self.showNotification(notification)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    # clears the active notification if equal to the given one
    def clearNotification(self, notification: Notification) -> None:
        if self.active_notification == notification:
            self.active_notification = None

    # external API to send a notification to the user via the notification manager
    def sendNotificationMessage(self,
            title: str,
            message: str,
            notification_type: NotificationType,
            created:Optional[float] = None,
            hr_id: Optional[str] = None,
            link: Optional[str] = None,
            pos:int = 0) -> None:
        _log.debug('sendNotificationMessage(%s,%s,%s,%s)', title, message, notification_type, hr_id)
        try:
            if self.notifications_available and self.notifications_enabled:
                n = Notification(title, message, notification_type, created=created, hr_id=hr_id, link=link)
                if time.time()-self.notification_queue_max_age < n.created:
                    if self.active_notification is None:
                        self.setNotification(n)
                    else:
                        # we delay the presentation of this new notification one time
                        QTimer.singleShot(self.notification_timeout*pos, lambda : self.setNotification(n))
                else:
                    _log.info('outdated notification discarded: %s',n.formatedTitle())
            elif not self.notifications_available:
                _log.debug('notifications not available')
            elif not self.notifications_enabled:
                _log.debug('notifications disabled')
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
