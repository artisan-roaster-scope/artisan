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

#import keyring.backends.file
#import keyring.backends.Gnome
#import keyring.backends.Google
#import keyring.backends.pyfs
#import keyring.backends.kwallet
#import keyring.backends.multi
#import keyring.backends.fail
import keyring.backends.OS_X
import keyring.backends.SecretService
import keyring.backends.Windows
import keyring # @Reimport # imported last to make py2app work
import platform


from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSemaphore, QTimer

from plus import config, connection, stock, queue, sync, roast

connect_semaphore = QSemaphore(1)

def is_connected():
    try:
        connect_semaphore.acquire(1)
        return config.connected
    finally:
        if connect_semaphore.available() < 1:
            connect_semaphore.release(1)

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
    if config.app_window.plus_account is None: # @UndefinedVariable
        connect()
        if is_connected() and is_synced() and config.app_window.curFile is not None: # @UndefinedVariable
            sync.sync()         
    else:
        if config.connected:
            if is_synced():
                disconnect()
            else:
                # we (manually) turn syncing for the current roast on
                if app_window.qmc.checkSaved():
                    queue.addRoast()
        else:
            connect(True) # we try to re-connect and disconnect on failure

def connect(clear_on_failure = False):
    config.logger.info("controller:connect(%s)",clear_on_failure)
    if not config.connected:
        try:
            connect_semaphore.acquire(1)
            if config.app_window is not None:
                try:
#                    config.logger.debug("controller: keyring.get_keyring() %s",keyring.get_keyring())       
                    #HACK set keyring backend explicitly
                    if platform.system().startswith("Windows"):
                        keyring.set_keyring(keyring.backends.Windows.WinVaultKeyring())   # @UndefinedVariable                  
                    elif platform.system() == 'Darwin':
                        keyring.set_keyring(keyring.backends.OS_X.Keyring())
                    else: # Linux
                        keyring.set_keyring(keyring.backends.SecretService()) 
                except Exception as e:
                    config.logger.error("controller: keyring Exception %s",e)
                if config.app_window.plus_account is not None: # @UndefinedVariable
                    try:
                        # try-catch as the keyring might not work
                        config.passwd = keyring.get_password(config.app_name, config.app_window.plus_account) # @UndefinedVariable
                        if config.passwd is None:
                            config.logger.debug("controller: -> keyring.get_password returned None")
                        else:
                            config.logger.debug("controller: -> keyring passwd received")
                    except Exception as e:
                        config.logger.error("controller: keyring Exception %s",e)
                if config.app_window.plus_account is None or config.passwd is None: # @UndefinedVariable
                    # ask user for credentials
                    import plus.login
                    login,passwd,remember = plus.login.plus_login(config.app_window,config.app_window.plus_email,config.app_window.plus_remember_credentials) # @UndefinedVariable
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
                            config.logger.debug("controller: -> keyring set (%s)",passwd)
                        except Exception as e:
                            config.logger.error("controller: keyring Exception %s",e)
                    config.passwd = passwd # remember password in memory for this session
            if config.app_window.plus_account is None: # @UndefinedVariable
                config.app_window.sendmessage(QApplication.translate("Plus","Login aborted",None)) # @UndefinedVariable
            else:
                success = connection.authentify()
                if success:
                    config.connected = success
                    config.app_window.sendmessage(config.app_window.plus_account + " " + QApplication.translate("Plus","authentified",None)) # @UndefinedVariable
                    config.app_window.sendmessage(QApplication.translate("Plus","Connected to artisan.plus",None))  # @UndefinedVariable
                    try:
                        queue.start() # start the outbox queue
                    except:
                        pass
                else:
                    if clear_on_failure:
                        connection.clearCredentials()
                        config.app_window.sendmessage(QApplication.translate("Plus","artisan.plus turned off",None))  # @UndefinedVariable
                    else:
                        message = QApplication.translate("Plus","Authentification failed",None)
                        if not config.app_window.plus_account is None: # @UndefinedVariable
                            message = config.app_window.plus_account + " " + message # @UndefinedVariable
                        config.app_window.sendmessage(message) # @UndefinedVariable
        except Exception as e:
            config.logger.error("controller: connect Exception %s",e)
            if clear_on_failure:
                connection.clearCredentials()
                config.app_window.sendmessage(QApplication.translate("Plus","artisan.plus turned off",None)) # @UndefinedVariable
            else:
                config.app_window.sendmessage(QApplication.translate("Plus","Couldn't connect to artisan.plus",None)) # @UndefinedVariable
                config.connected = False
        finally:
            if connect_semaphore.available() < 1:
                connect_semaphore.release(1)
        config.app_window.updatePlusStatus() # @UndefinedVariable
        stock.update()

def disconnect(remove_credentials = True):
    config.logger.info("controller:disconnect(%s)",remove_credentials)
    if is_connected():
        try:
            connect_semaphore.acquire(1)
            # disconnect
            config.connected = False
            # remove credentials
            if remove_credentials:
                connection.clearCredentials()                
                config.app_window.sendmessage(QApplication.translate("Plus","artisan.plus turned off",None)) # @UndefinedVariable              
            else:
                config.app_window.sendmessage(QApplication.translate("Plus","artisan.plus disconnected",None)) # @UndefinedVariable
            queue.stop() # stop the outbox queue
        finally:
            if connect_semaphore.available() < 1:
                connect_semaphore.release(1)
        config.app_window.updatePlusStatus() # @UndefinedVariable 
        
def reconnected():
    if not is_connected():
        config.logger.info("controller:reconnected()")
        try:
            connect_semaphore.acquire(1)
            config.connected = True            
        finally:
            if connect_semaphore.available() < 1:
                connect_semaphore.release(1)
        config.app_window.updatePlusStatus() # @UndefinedVariable
        if is_connected():
            queue.start() # stop the outbox queue

# if connected and synced, computes the sync record hash, updates the sync record cache and returns the sync record hash
# otherwise return None
# this function is called by filesave() and returns the sync_record hash to be added to the saved file
def updateSyncRecordHashAndSync():
    try:
        config.logger.info("controller:updateSyncRecordHashAndSync()")
        if is_connected():
            roast_record = roast.getRoast()
            sync_record,sync_record_hash = roast.getSyncRecord(roast_record)
            if is_synced():
                server_updates_modified_at = sync.getApplidedServerUpdatesModifiedAt()
                if server_updates_modified_at is not None and "roast_id" in roast_record:
                    sync.addSync(roast_record["roast_id"],server_updates_modified_at)
                    sync.setApplidedServerUpdatesModifiedAt(None)        
                # we are connected and the profile is under sync
                if sync.syncRecordUpdated(roast_record):
                    # we push updates on the sync record back to the server
                    queue.addRoast(sync_record)
            return sync_record_hash
        else:
            return None
    except Exception as e:
        import sys
        _, _, exc_tb = sys.exc_info()
        config.logger.error("controller: Exception in updateSyncRecordHashAndSync() line %s: %s",exc_tb.tb_lineno,e)
