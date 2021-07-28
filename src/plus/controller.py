#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# controller.py
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

from artisanlib import __version__
from artisanlib import __revision__
from artisanlib import __build__

#import keyring.backends.file
#import keyring.backends.Gnome
#import keyring.backends.Google
#import keyring.backends.pyfs
#import keyring.backends.kwallet
#import keyring.backends.multi

import threading


import platform
if platform.system().startswith("Windows") or platform.system() == 'Darwin':
    import keyring.backends.fail # @UnusedImport
    try:
        import keyring.backends.macOS # @UnusedImport @UnresolvedImport
        keyring.set_keyring(keyring.backends.macOS.Keyring())
    except:
        import keyring.backends.OS_X # @UnusedImport @UnresolvedImport
        keyring.set_keyring(keyring.backends.OS_X.Keyring())
    import keyring.backends.SecretService # @UnusedImport
    import keyring.backends.Windows # @UnusedImport
import keyring # @Reimport # imported last to make py2app work


from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QSemaphore, QTimer, Qt

from plus import config, connection, stock, queue, sync, roast, util

connect_semaphore = QSemaphore(1)

def is_connected():
    try:
        connect_semaphore.acquire(1)
        return config.connected
    finally:
        if connect_semaphore.available() < 1:
            connect_semaphore.release(1)

# artisan.plus is on as soon as an account id has been established
# Note that artisan.plus might be on, while not being connected due to connectivity issues
def is_on():
    aw = config.app_window
    if aw is None:
        return False
    else:
        return aw.plus_account is not None

# returns True if current profile is under sync (i.e. in the sync-cache) or no profile is loaded currently
def is_synced():
    aw = config.app_window
    if aw.qmc.roastUUID is None:
        return not bool(aw.curFile)
    else:
        res = sync.getSync(aw.qmc.roastUUID)
        return bool(res)
            
def start(app_window):
    config.app_window = app_window
    QTimer.singleShot(2,lambda : connect())

# toggles between connected and disconnected modes. If connected and not is_synced() uploades current data to server
def toggle(app_window):
    config.logger.info("controller:toggle()")
    config.app_window = app_window
    modifiers = QApplication.keyboardModifiers()
    if modifiers == (Qt.AltModifier | Qt.ControlModifier):
        # ALT+CTR-CLICK (OPTION+COMMAND on macOS) toggles the plus debug logging 
        util.debugLogToggle()
    elif modifiers == Qt.AltModifier:
        # ALT-click (OPTION on macOS) sends the log file by email
        util.sendLog()
    else:
        if config.app_window.plus_account is None: # @UndefinedVariable
            connect()
            if is_connected() and is_synced() and config.app_window.curFile is not None: # @UndefinedVariable
                sync.sync()         
        else:
            if config.connected:
                if is_synced():
                    # a CTR-click (COMMAND on macOS) logs out and discards the credentials
                    disconnect(interactive=True,remove_credentials=(modifiers == Qt.ControlModifier),keepON=False)
                else:
                    # we (manually) turn syncing for the current roast on
                    if app_window.qmc.checkSaved(allow_discard=False):
                        queue.addRoast()
            else:
                disconnect(remove_credentials = False, stop_queue = True, interactive = True, keepON=False)

# if clear_on_failure is set, credentials are removed if connect fails
def connect(clear_on_failure=False,interactive=True):
    if not is_connected():
        config.logger.info("controller:connect(%s,%s)",clear_on_failure,interactive)
        try:
            connect_semaphore.acquire(1)
            if config.app_window is not None:
                connection.setKeyring()
                account = config.app_window.plus_account
                if account is None:
                    account = config.app_window.plus_email
                    if isinstance(threading.current_thread(), threading._MainThread):
                        # this is dangerous and should only be done while running in the main GUI thread as a consequence are GUI actions which might crash in other threads
                        interactive = True
                if account is not None: # @UndefinedVariable
                    try:
                        # try-catch as the keyring might not work
                        config.passwd = keyring.get_password(config.app_name, account) # @UndefinedVariable
                        if config.passwd is None:
                            config.logger.debug("controller: -> keyring.get_password returned None")
                        else:
                            config.logger.debug("controller: -> keyring passwd received")
                    except Exception as e:
                        config.logger.error("controller: keyring Exception %s",e)
                if interactive and (config.app_window.plus_account is None or config.passwd is None): # @UndefinedVariable
                    # ask user for credentials
                    import plus.login
                    login,passwd,remember,res = plus.login.plus_login(config.app_window,config.app_window.plus_email,config.passwd,config.app_window.plus_remember_credentials) # @UndefinedVariable
                    if res: # Login dialog not Canceled
                        config.app_window.plus_remember_credentials = remember
                        # store credentials
                        config.app_window.plus_account = login
                        if remember:
                            config.app_window.plus_email = login
                        else:
                            config.app_window.plus_email = None                    
                        # store the passwd in the keychain
                        if login is not None and passwd is not None and remember:
                            try:
                                # try-catch as the keyring might not work
                                keyring.set_password(config.app_name, login, passwd)
                                config.logger.debug("controller: -> keyring set password (%s)",login)
                            except Exception as e:
                                config.logger.error("controller: keyring Exception %s",e)
                                if not platform.system().startswith("Windows") and platform.system() != 'Darwin':
                                    # on Linux remind to install the gnome-keyring
                                    config.app_window.sendmessageSignal.emit(QApplication.translate("Plus","Keyring error: Ensure that gnome-keyring is installed.",None),True,None) # @UndefinedVariable 
                        config.passwd = passwd # remember password in memory for this session
            if config.app_window.plus_account is None: # @UndefinedVariable
                if interactive:
                    config.app_window.sendmessageSignal.emit(QApplication.translate("Plus","Login aborted",None),True,None) # @UndefinedVariable
            else:
                success = connection.authentify()
                if success:
                    config.connected = success
                    config.app_window.sendmessageSignal.emit(config.app_window.plus_account + " " + QApplication.translate("Plus","authentified",None),True,None) # @UndefinedVariable
                    config.app_window.sendmessageSignal.emit(QApplication.translate("Plus","Connected to artisan.plus",None),True,None)  # @UndefinedVariable
                    config.logger.info("Artisan v%s (%s, %s) connected",str(__version__),str(__revision__),str(__build__))
                    try:
                        queue.start() # start the outbox queue
                    except Exception:
                        pass
                    try:
                        config.app_window.resetDonateCounter()
                    except Exception:
                        pass
                else:
                    if clear_on_failure:
                        connection.clearCredentials()
                        config.app_window.sendmessageSignal.emit(QApplication.translate("Plus","artisan.plus turned off",None),True,None)  # @UndefinedVariable
                    elif interactive:
                        message = QApplication.translate("Plus","Authentication failed",None)
                        if not config.app_window.plus_account is None: # @UndefinedVariable
                            message = config.app_window.plus_account + " " + message # @UndefinedVariable
                        config.app_window.sendmessageSignal.emit(message,True,None) # @UndefinedVariable
        except Exception as e:
            if interactive:
                config.logger.error("controller: connect Exception %s",e)
            if clear_on_failure:
                connection.clearCredentials()
                if interactive:
                    config.app_window.sendmessageSignal.emit(QApplication.translate("Plus","artisan.plus turned off",None),True,None)
            else:
                if interactive:
                    config.app_window.sendmessageSignal.emit(QApplication.translate("Plus","Couldn't connect to artisan.plus",None),True,None)
                config.connected = False
        finally:
            if connect_semaphore.available() < 1:
                connect_semaphore.release(1)
        config.app_window.updatePlusStatusSignal.emit() # @UndefinedVariable
        if interactive and is_connected():
            stock.update()

# show a dialog to have the user confirm the disconnect action
def disconnect_confirmed():
    string = QApplication.translate("Plus","Disconnect artisan.plus?", None)
    aw = config.app_window
    reply = QMessageBox.question(aw,QApplication.translate("Plus","Disconnect?", None),string,
                                QMessageBox.Ok | QMessageBox.Cancel)
    if reply == QMessageBox.Ok:
        return True
    else:
        return False

# if keepON is set (the default), the credentials are not removed at all and just the connected flag is toggled to keep plus in ON (dark-grey) state
def disconnect(remove_credentials = True, stop_queue = True, interactive = False, keepON=True):
    config.logger.info("controller:disconnect(%s,%s,%s,%s)",remove_credentials,stop_queue,interactive,keepON)
    if (is_connected() or is_on()) and (not interactive or disconnect_confirmed()):
        try:
            connect_semaphore.acquire(1)
            # disconnect
            config.connected = False
            # remove credentials
            if not keepON:
                connection.clearCredentials(remove_from_keychain=remove_credentials)
            if remove_credentials:
                config.app_window.sendmessageSignal.emit(QApplication.translate("Plus","artisan.plus turned off",None),True,None)
            else:
                config.app_window.sendmessageSignal.emit(QApplication.translate("Plus","artisan.plus disconnected",None),True,None)
            if stop_queue:
                queue.stop() # stop the outbox queue
        finally:
            if connect_semaphore.available() < 1:
                connect_semaphore.release(1)
        config.app_window.updatePlusStatusSignal.emit() # @UndefinedVariable
        
def reconnected():
    if not is_connected():
        config.logger.info("controller:reconnected()")
        try:
            connect_semaphore.acquire(1)
            config.connected = True            
        finally:
            if connect_semaphore.available() < 1:
                connect_semaphore.release(1)
        config.app_window.updatePlusStatusSignal.emit() # @UndefinedVariable
        if is_connected():
            queue.start() # restart the outbox queue
    
# if on and synced, computes the sync record hash, updates the sync record cache and returns the sync record hash
# otherwise return None
# this function is called by filesave() and returns the sync_record hash to be added to the saved file
def updateSyncRecordHashAndSync():
    try:
        config.logger.info("controller:updateSyncRecordHashAndSync()")
        if is_on():
            roast_record = roast.getRoast()
            sync_record,sync_record_hash = roast.getSyncRecord(roast_record)
            if is_synced(): # check if profile is under sync already
                server_updates_modified_at = sync.getApplidedServerUpdatesModifiedAt()
                if server_updates_modified_at is not None and "roast_id" in roast_record:
                    sync.addSync(roast_record["roast_id"],server_updates_modified_at)
                    sync.setApplidedServerUpdatesModifiedAt(None)        
                # artisan.plus is ON and the profile is under sync
                if sync.syncRecordUpdated(roast_record):
                    # we push updates on the sync record back to the server via the queue
                    queue.addRoast(sync_record)
            elif "roast_id" in roast_record and queue.full_roast_in_queue(roast_record["roast_id"]):
                # in case this roast is not yet in sync cache as it has not been successfully uploaded, but a corresponding full roast
                # record is already in the uploading queue we add this updating sync_record also to the queue
                queue.addRoast(sync_record)
            return sync_record_hash
        else:
            return None
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("controller: Exception in updateSyncRecordHashAndSync() line %s: %s",exc_tb.tb_lineno,e)
        return None
