# -*- coding: utf-8 -*-
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
# Marko Luther, 2021

try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtWidgets import QSystemTrayIcon, QApplication, QMenu # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QIcon, QDesktopServices, QAction # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtCore import QTimer, pyqtSlot, QUrl, QObject # @UnusedImport @Reimport  @UnresolvedImport
except Exception:
    #pylint: disable = E, W, R, C
    from PyQt5.QtWidgets import QSystemTrayIcon, QApplication, QMenu, QAction # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QIcon, QDesktopServices # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtCore import QTimer, pyqtSlot, QUrl, QObject # @UnusedImport @Reimport  @UnresolvedImport

import os
import sys
import time
import logging
from typing import Final, Optional
from enum import Enum
from artisanlib.util import getResourcePath
import plus.util


_log: Final = logging.getLogger(__name__)

class NotificationType(Enum):
    ARTISAN_SYSTEM = 1 # issued by some internal Artisan activity
    ARTISAN_USER = 2   # issues with notify() Artisan Command
    PLUS_SYSTEM = 3    # an artisan.plus system notification
    PLUS_REMINDER = 4  # an artisan.plus reminder notification


class Notification():
    def __init__(self, title: str, message: str, notification_type: NotificationType, created: Optional[float] = None):
        self._title = title
        self._message = message
        self._type = notification_type
        if created is None:
            self._created = time.time()
        else:
            self._created = created
    
    @property
    def title(self):
        return self._title
    
    @property
    def message(self):
        return self._message
    
    @property
    def type(self):
        return self._type
    
    @property
    def created(self):
        return self._created


class NotificationManager(QObject):
    
    __slots__ = ( 'notification_timeout', 'notification_queue_max_length', 'notification_queue_max_age', 'tray_menu', 'tray_icon', 
                'notifications_available', 'notifications_enabled', 'notifications_visible', 'notifications_queue', 'active_notification' )

    def __init__(self):
        super().__init__()
        
        # time to display a notification
        self.notification_timeout: Final = 6000 # in ms
        # we keep the last n notifications in the tray icon menu
        self.notification_queue_max_length: Final = 5
        # notifications older then max_age are automatically removed from the try icon menu
        self.notification_queue_max_age: Final = 5*24*60*60 # in seconds (5 days = 5*24*60*60)
        
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_menu = QMenu()
        
        # notfication_available is true if the operating system supports notifications
        self.notifications_available = self.tray_icon.isSystemTrayAvailable() and self.tray_icon.supportsMessages()
        if self.notifications_available:
            # the tray icon is displayed only if notifications are supported by the system
            self.tray_icon.setIcon(self.artisanTrayIcon())
            self.tray_icon.setToolTip("Artisan Notifications")
            self.tray_icon.messageClicked.connect(self.messageClicked)
            #self.tray_icon.show() # if try_icon is not visible, notifications are not delivered       
            self.tray_icon.setContextMenu(self.tray_menu)
        
        self.notifications_enabled = True # if False, issued notification messages are ignored
        self.notifications_visible = True # if False, the tray_menu icon (and thus notifications) are not shown
        self.notifications_queue = [] # FIFO of Notification objects
        # the allocated menu actions
        self.notification_menu_actions = []
        # holds the currently displayed notification
        self.active_notification = None

    @staticmethod
    def artisanTrayIcon():
        basedir = os.path.join(getResourcePath(),"Icons")
        if sys.platform.startswith("darwin"):
            p = os.path.join(basedir, "artisan-trayicon.svg")
        else:
            p = os.path.join(basedir, "artisan-trayicon-large.svg")
        icon = QIcon(p)
        icon.setIsMask(True)
        return icon

    # returns the plus icon as QIcon
    @staticmethod
    def notificationPlusIcon():
        basedir = os.path.join(getResourcePath(),"Icons")
        if sys.platform.startswith("darwin"):
            p = os.path.join(basedir, "plus-notification.png")
        else:
            p = os.path.join(basedir, "plus-notification.svg")
        return QIcon(p)

    # returns the Artisan icon as QIcon
    @staticmethod
    def notificationArtisanIcon():
        basedir = os.path.join(getResourcePath(),"Icons")
        if sys.platform.startswith("darwin"):
            p = os.path.join(basedir, "artisan-notification.png")
        else:
            p = os.path.join(basedir, "artisan-notification.svg")
        return QIcon(p)
    
    @pyqtSlot()
    def messageClicked(self):
        try:
            if self.active_notification.type in [NotificationType.ARTISAN_SYSTEM, NotificationType.ARTISAN_USER]:
                # raise Artisan app
                app = QApplication.instance()
                if app is not None:
                    app.activateWindow()
            elif self.active_notification.type == NotificationType.PLUS_SYSTEM:
                # open artisan.plus
                QDesktopServices.openUrl(QUrl(plus.util.plusLink()))
            elif self.active_notification.type == NotificationType.PLUS_REMINDER:
                # open artisan.plus reminder tab
                QDesktopServices.openUrl(QUrl(plus.util.remindersLink()))
            self.removeNotificationItem(self.active_notification)
            self.active_notification = None
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
    
    def showNotifications(self):
        try:
            if self.notifications_available:
                self.notifications_visible = True
                if len(self.notifications_queue)>0:
                    self.tray_icon.show()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            
    def hideNotifications(self):
        try:
            if self.notifications_available:
                self.notifications_visible = False
                self.tray_icon.hide()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
    
    # if notifications are enabled, incoming notifications are presented to user
    def enableNotifications(self):
        self.notifications_enabled = True
    
    # if notfications are disabled, incoming notifications are just ignore
    def disableNotifications(self):
        self.notifications_enabled = False
    
    def getNotificationItems(self):
        return self.notifications_queue
    
    def addNotificationItem(self, notification: Notification):
        self.notifications_queue.append(notification)
        self.updateNotificationMenu()
    
    def removeNotificationItem(self, notification: Notification):
        self.notifications_queue.remove(notification)
        self.updateNotificationMenu()
    
    def clearNotificationQueue(self):
        self.notifications_queue = []

    def cleanNotificationQueue(self):
        try:
            # remove outdated entries
            age_limit = time.time() - self.notification_queue_max_age
            self.notifications_queue = [n for n in self.notifications_queue if n.created>age_limit]
            # limit the queue to maximal length
            self.notifications_queue = self.notifications_queue[max(0,len(self.notifications_queue)-self.notification_queue_max_length):]
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
    
    def updateNotificationMenu(self):
        try:
            self.cleanNotificationQueue()
            self.tray_menu.clear()
            self.notification_menu_actions = []
            if len(self.notifications_queue)>0 and self.notifications_visible:
                self.tray_icon.show()
                for n in reversed(self.notifications_queue):
                    menu_title = (n.title[:25] + '...') if len(n.title) > 25 else n.title
                    action = QAction(menu_title, visible=True, triggered=self.notificationItemSelected)
                    action.setData(n)
                    self.notification_menu_actions.append(action)                                
                    self.tray_menu.addAction(action)
            else:
                self.tray_icon.hide()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    @pyqtSlot(bool)
    def notificationItemSelected(self, _checked:bool = False):
        action = self.sender()
        n = action.data()
        self.setNotification(n, addToQueue=False)
        
    # actually presents the given notification to the user
    def showNotification(self, notification: Notification):
        try:
            icon = QSystemTrayIcon.MessageIcon.Information # NoIcon, Information, Warning, Critical
            if notification.type in [NotificationType.ARTISAN_SYSTEM, NotificationType.ARTISAN_USER]:
                icon = self.notificationArtisanIcon()
            elif notification.type in [NotificationType.PLUS_SYSTEM, NotificationType.PLUS_REMINDER]:
                icon = self.notificationPlusIcon()
            self.tray_icon.showMessage(notification.title, notification.message, icon, self.notification_timeout)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
    
    # set the given notification as the active one and shows it to the user
    def setNotification(self, notification: Notification, addToQueue:bool = True):
        _log.info("%s %s %s", notification.type.name, notification.title, notification.message)
        try:
            self.active_notification = notification
            if addToQueue:
                self.addNotificationItem(notification) # also shows tray_menu icon if self.notifications_visible
            # we set a timer to clear this notification after the presentation timeout
            QTimer.singleShot(self.notification_timeout, lambda : self.clearNotification(notification))
            self.showNotification(notification)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
    
    # clears the active notification if equal to the given one
    def clearNotification(self, notification: Notification):
        if self.active_notification == notification:
            self.active_notification = None

    # external API to send a notification to the user via the notification manager
    def sendNotificationMessage(self, title: str, message: str, notification_type: NotificationType):
        try:
            if self.notifications_available and self.notifications_enabled:
                n = Notification(title, message, notification_type)
                if self.active_notification is None:
                    self.setNotification(n)
                else:
                    # we delay the presentation of this new notification one time
                    QTimer.singleShot(self.notification_timeout, lambda : self.setNotification(n))
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)