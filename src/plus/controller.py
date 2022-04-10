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
    from PyQt6.QtCore import QSemaphore, QTimer, Qt # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication, QMessageBox # @UnusedImport @Reimport  @UnresolvedImport
except Exception:
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import QSemaphore, QTimer, Qt # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication, QMessageBox # @UnusedImport @Reimport  @UnresolvedImport

import platform
import threading
import logging
try:
    from typing import Final
except ImportError:
    # for Python 3.7:
    from typing_extensions import Final



from plus import config, connection, stock, queue, sync, roast



_log: Final = logging.getLogger(__name__)

connect_semaphore = QSemaphore(1)

def is_connected() -> bool:
    return config.connected


# artisan.plus is on as soon as an account id has been established
# Note that artisan.plus might be on, while not being connected due to
# connectivity issues
def is_on() -> bool:
    aw = config.app_window
    if aw is None:
        return False
    return aw.plus_account is not None


# returns True if current profile is under sync (i.e. in the sync-cache) or
# no profile is loaded currently
def is_synced():
    aw = config.app_window
    if aw.qmc.roastUUID is None:
        return not bool(aw.curFile)
    res = sync.getSync(aw.qmc.roastUUID)
    return bool(res)


def start(app_window):
    config.app_window = app_window
    QTimer.singleShot(2, connect)


# toggles between connected and disconnected modes. If connected and
# not is_synced() send current data to server
def toggle(app_window):
    _log.info('toggle()')
    config.app_window = app_window
    if config.app_window.plus_account is None:  # @UndefinedVariable
        connect()
        if (
            is_connected()
            and is_synced()
            and config.app_window.curFile is not None
        ):  # @UndefinedVariable
            sync.sync()
    else:
        if config.connected:
            if is_synced():
                # a CTR-click (COMMAND on macOS) logs out and
                # discards the credentials
                modifiers = QApplication.keyboardModifiers()
                disconnect(
                    interactive=True,
                    remove_credentials=(modifiers == Qt.KeyboardModifier.ControlModifier),
                    keepON=False,
                )
            else:
                # we (manually) turn syncing for the current roast on
                if app_window.qmc.checkSaved(allow_discard=False):
                    queue.addRoast()
        else:
            disconnect(
                remove_credentials=False,
                stop_queue=True,
                interactive=True,
                keepON=False,
            )


# if clear_on_failure is set, credentials are removed if connect fails
# NOTE: authentify might be called from outside the GUI thread (interactive must be False in this case!)
def connect(clear_on_failure: bool =False, interactive: bool = True) -> None:
    if not is_connected():
        _log.info(
            'connect(%s,%s)', clear_on_failure, interactive
        )
        try:
            connect_semaphore.acquire(1)
            if config.app_window is not None:

                if platform.system().startswith('Windows'):
                    import keyring.backends.Windows  # @UnusedImport
                elif platform.system() == 'Darwin':
                    import keyring.backends.macOS  # @UnusedImport @UnresolvedImport
                else:
                    import keyring.backends.SecretService  # @UnusedImport
                import keyring  # @Reimport # imported last to make py2app work

                connection.setKeyring()
                account = config.app_window.plus_account
                if account is None:
                    account = config.app_window.plus_email
                    if isinstance(
                        # pylint: disable=protected-access
                        threading.current_thread(), threading._MainThread
                    ):  # this is dangerous and should only be done while
                        # running in the main GUI thread as a consequence are
                        # GUI actions which might crash in other threads
                        interactive = True
                if account is not None:  # @UndefinedVariable
                    try:
                        # try-catch as the keyring might not work
                        config.passwd = keyring.get_password(
                            config.app_name, account
                        )  # @UndefinedVariable
                        if config.passwd is None:
                            _log.debug(
                                '-> keyring.get_password'
                                 ' returned None'
                            )
                        else:
                            _log.debug(
                                '-> keyring passwd received'
                            )
                    except Exception as e:  # pylint: disable=broad-except
                        _log.exception(e)
                if interactive and (
                    config.app_window.plus_account is None
                    or config.passwd is None
                ):  # @UndefinedVariable
                    # ask user for credentials
                    import plus.login

                    login, passwd, remember, res = plus.login.plus_login(
                        config.app_window,
                        config.app_window.plus_email,
                        config.passwd,
                        config.app_window.plus_remember_credentials,
                    )  # @UndefinedVariable
                    if res:  # Login dialog not Canceled
                        config.app_window.plus_remember_credentials = remember
                        # store credentials
                        config.app_window.plus_account = login
                        if remember:
                            config.app_window.plus_email = login
                        else:
                            config.app_window.plus_email = None
                        # store the passwd in the keychain
                        if (
                            login is not None
                            and passwd is not None
                            and remember
                        ):
                            try:
                                # try-catch as the keyring might not work
                                keyring.set_password(
                                    config.app_name, login, passwd
                                )
                                _log.debug('keyring set password (%s)', login)
                            # pylint: disable=broad-except
                            except Exception as e:
                                _log.exception(e)
                                if (
                                    not platform.system().startswith('Windows')
                                    and platform.system() != 'Darwin'
                                ):
                                    # on Linux remind to install
                                    # the gnome-keyring
                                    config.app_window.sendmessageSignal.emit(
                                        QApplication.translate(
                                            'Plus',
                                            ('Keyring error: Ensure that'
                                             ' gnome-keyring is installed.')
                                        ),
                                        True,
                                        None,
                                    )  # @UndefinedVariable
                        # remember password in memory for this session
                        config.passwd = passwd
            if config.app_window.plus_account is None:  # @UndefinedVariable
                if interactive:
                    config.app_window.sendmessageSignal.emit(
                        QApplication.translate('Plus', 'Login aborted'),
                        True,
                        None,
                    )  # @UndefinedVariable
            else:
                success = connection.authentify()
                if success:
                    config.connected = success
                    config.app_window.sendmessageSignal.emit(
                        f'{config.app_window.plus_account} {QApplication.translate("Plus", "authentified")}',
                        True,
                        None,
                    )  # @UndefinedVariable
                    config.app_window.sendmessageSignal.emit(
                        QApplication.translate(
                            'Plus', 'Connected to artisan.plus'
                        ),
                        True,
                        None,
                    )  # @UndefinedVariable
                    _log.info('artisan.plus connected')
                    try:
                        queue.start()  # start the outbox queue
                    except Exception as e:  # pylint: disable=broad-except
                        _log.exception(e)
                    try:
                        config.app_window.resetDonateCounter()
                    except Exception as e:  # pylint: disable=broad-except
                        _log.exception(e)
                else:
                    if clear_on_failure:
                        connection.clearCredentials()
                        config.app_window.sendmessageSignal.emit(
                            QApplication.translate(
                                'Plus', 'artisan.plus turned off'
                            ),
                            True,
                            None,
                        )  # @UndefinedVariable
                    elif interactive:
                        message = QApplication.translate(
                            'Plus', 'Authentication failed'
                        )
                        if (
                            config.app_window.plus_account is not None
                        ):  # @UndefinedVariable
                            message = (
                                f'{config.app_window.plus_account} {message}'
                            )  # @UndefinedVariable
                        config.app_window.sendmessageSignal.emit(
                            message, True, None
                        )  # @UndefinedVariable
        except Exception as e:  # pylint: disable=broad-except
            if interactive:
                _log.exception(e)
            if clear_on_failure:
                connection.clearCredentials()
                if interactive:
                    config.app_window.sendmessageSignal.emit(
                        QApplication.translate(
                            'Plus', 'artisan.plus turned off'
                        ),
                        True,
                        None,
                    )
            else:
                if interactive:
                    config.app_window.sendmessageSignal.emit(
                        QApplication.translate(
                            'Plus', "Couldn't connect to artisan.plus"
                        ),
                        True,
                        None,
                    )
                config.connected = False
        finally:
            if connect_semaphore.available() < 1:
                connect_semaphore.release(1)
        config.app_window.updatePlusStatusSignal.emit()  # @UndefinedVariable
        if interactive and is_connected():
            QTimer.singleShot(2500, stock.update)


# show a dialog to have the user confirm the disconnect action
def disconnect_confirmed() -> bool:
    string = QApplication.translate('Plus', 'Disconnect artisan.plus?')
    aw = config.app_window
    reply = QMessageBox.question(
        aw,
        QApplication.translate('Plus', 'Disconnect?'),
        string,
        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
    )
    return bool(reply == QMessageBox.StandardButton.Ok)


# if keepON is set (the default), the credentials are not removed at all and
# just the connected flag is toggled to keep plus in ON (dark-grey) state
def disconnect(
    remove_credentials: bool = True,
    stop_queue: bool = True,
    interactive: bool = False,
    keepON: bool = True
) -> None:
    _log.info(
        'disconnect(%s,%s,%s,%s)',
        remove_credentials,
        stop_queue,
        interactive,
        keepON,
    )
    if (is_connected() or is_on()) and (
        not interactive or disconnect_confirmed()
    ):
        try:
            connect_semaphore.acquire(1)
            # disconnect
            config.connected = False
            # remove credentials
            if not keepON:
                connection.clearCredentials(
                    remove_from_keychain=remove_credentials
                )
            if remove_credentials:
                config.app_window.sendmessageSignal.emit(
                    QApplication.translate(
                        'Plus', 'artisan.plus turned off'
                    ),
                    True,
                    None,
                )
            else:
                config.app_window.sendmessageSignal.emit(
                    QApplication.translate(
                        'Plus', 'artisan.plus disconnected'
                    ),
                    True,
                    None,
                )
            if stop_queue:
                queue.stop()  # stop the outbox queue
        finally:
            if connect_semaphore.available() < 1:
                connect_semaphore.release(1)
        config.app_window.updatePlusStatusSignal.emit()  # @UndefinedVariable


def reconnected() -> None:
    if not is_connected():
        _log.info('reconnected()')
        try:
            connect_semaphore.acquire(1)
            config.connected = True
        finally:
            if connect_semaphore.available() < 1:
                connect_semaphore.release(1)
        config.app_window.updatePlusStatusSignal.emit()  # @UndefinedVariable
        if is_connected():
            queue.start()  # restart the outbox queue


# if on and synced, computes the sync record hash, updates the
# sync record cache and returns the sync record hash
# otherwise return None
# this function is called by filesave() and returns the sync_record hash
# to be added to the saved file
def updateSyncRecordHashAndSync() -> None:
    try:
        _log.info('updateSyncRecordHashAndSync()')
        if is_on():
            roast_record = roast.getRoast()
            sync_record, sync_record_hash = roast.getSyncRecord(roast_record)
            if is_synced():  # check if profile is under sync already
                server_updates_modified_at = (
                    sync.getApplidedServerUpdatesModifiedAt()
                )
                if (
                    server_updates_modified_at is not None
                    and 'roast_id' in roast_record
                ):
                    sync.addSync(
                        roast_record['roast_id'], server_updates_modified_at
                    )
                    sync.setApplidedServerUpdatesModifiedAt(None)
                # artisan.plus is ON and the profile is under sync
                if sync.syncRecordUpdated(roast_record):
                    # we push updates on the sync record back to the server
                    # via the queue
                    queue.addRoast(sync_record)
            elif 'roast_id' in roast_record and queue.full_roast_in_queue(
                roast_record['roast_id']
            ):
                # in case this roast is not yet in sync cache as it has
                # not been successfully uploaded, but a corresponding full
                # roast record is already in the uploading queue we add this
                # updating sync_record also to the queue
                queue.addRoast(sync_record)
            return sync_record_hash
        return None
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
        return None
