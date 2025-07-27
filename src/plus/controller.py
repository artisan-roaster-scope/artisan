#
# controller.py
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
    from PyQt6.QtCore import QSemaphore, QTimer, Qt, pyqtSlot # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QWidget, QApplication, QMessageBox # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import QSemaphore, QTimer, Qt, pyqtSlot # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


import platform
import threading
import logging
from typing import Final, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import

from plus import config, connection, stock, queue, sync, roast, util


_log: Final[logging.Logger] = logging.getLogger(__name__)

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
def is_synced() -> bool:
    aw = config.app_window
    if aw is not None:
        if aw.qmc.roastUUID is None:
            # not in sync if no roastUUID and saved to file or (OFF and not saved yet but at least 5min in length)
            return not (bool(aw.curFile) or
                (not aw.qmc.flagon and
                    (len(aw.qmc.timex)>0 and ((aw.qmc.timex[-1] - (aw.qmc.timex[aw.qmc.timeindex[0]] if aw.qmc.timeindex[0] != -1 else 0)) > 5*60))))
        return bool(sync.getSync(aw.qmc.roastUUID))
    return False


def start(app_window:'ApplicationWindow') -> None:
    config.app_window = app_window
    QTimer.singleShot(2, connect)


# toggles between connected and disconnected modes. If connected and
# not is_synced() send current data to server
def toggle(app_window:'ApplicationWindow') -> None:
    _log.debug('toggle()')
    config.app_window = app_window
    if app_window is not None and app_window.plus_account is None:  # @UndefinedVariable
        connect()
        if (
            is_connected()
            and is_synced() # current profile under sync
            and app_window.curFile is not None
        ):  # @UndefinedVariable
            sync.sync()
    elif config.connected:
        if not is_synced() and app_window.qmc.checkSaved(allow_discard=False):
            # we (manually) turn syncing for the current roast on
            queue.addRoast()
        else:
            # a CTR-click (COMMAND on macOS) logs out and
            # discards the credentials
            modifiers = QApplication.keyboardModifiers()
            disconnect(
                interactive=True,
                remove_credentials=(modifiers == Qt.KeyboardModifier.ControlModifier),
                keepON=False,
            )
    else:
        disconnect(
            remove_credentials=False,
            stop_queue=True,
            interactive=True,
            keepON=False,
        )


# if clear_on_failure is set, credentials are removed if connect fails
# NOTE: authentify might be called from outside the GUI thread (interactive must be False in this case!)
@pyqtSlot()
def connect(clear_on_failure: bool =False, interactive: bool = True) -> None:
    if not is_connected():
        _log.debug(
            'connect(%s,%s)', clear_on_failure, interactive
        )
        aw = config.app_window
        try:
            connect_semaphore.acquire(1)
            if aw is not None:

#                if platform.system().startswith('Windows'):
#                    import keyring.backends.Windows  # @UnusedImport
#                elif platform.system() == 'Darwin':
#                    import keyring.backends.macOS  # @UnusedImport @UnresolvedImport
#                else:
#                    import keyring.backends.SecretService  # @UnusedImport
                import keyring  # @Reimport # imported last to make py2app work

#                connection.setKeyring()
                account = aw.plus_account
                if account is None:
                    account = aw.plus_email
                    if isinstance(
                        # pylint: disable=protected-access
                        threading.current_thread(), threading._MainThread # type: ignore
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
                    aw.plus_account is None
                    or config.passwd is None
                ):  # @UndefinedVariable
                    # ask user for credentials
                    import plus.login

                    login, passwd, remember, res = plus.login.plus_login(
                        aw,
                        aw,
                        aw.plus_email,
                        config.passwd,
                        aw.plus_remember_credentials,
                    )  # @UndefinedVariable
                    if res:  # Login dialog not Canceled
                        aw.plus_remember_credentials = remember
                        # store credentials
                        aw.plus_account = login
                        if remember:
                            aw.plus_email = login
                        else:
                            aw.plus_email = None
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
                                    aw.sendmessageSignal.emit(
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
            if aw is not None:
                if aw.plus_account is None:  # @UndefinedVariable
                    if interactive:
                        aw.sendmessageSignal.emit(
                            QApplication.translate('Plus', 'Login aborted'),
                            True,
                            None,
                        )  # @UndefinedVariable
                else:
                    success = connection.authentify()
                    if success:
                        config.connected = success
                        aw.sendmessageSignal.emit(
                            f"{aw.plus_account} {QApplication.translate('Plus', 'authentified')}",
                            True,
                            None,
                        )  # @UndefinedVariable
                        aw.sendmessageSignal.emit(
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
                            aw.resetDonateCounter()
                        except Exception as e:  # pylint: disable=broad-except
                            _log.exception(e)
                    elif clear_on_failure:
                        connection.clearCredentials()
                        aw.sendmessageSignal.emit(
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
                            aw.plus_account is not None
                        ):  # @UndefinedVariable
                            message = (
                                f'{aw.plus_account} {message}'
                            )  # @UndefinedVariable
                        aw.sendmessageSignal.emit(
                            message, True, None
                        )  # @UndefinedVariable
        except Exception as e:  # pylint: disable=broad-except
            if interactive:
                _log.debug(e)
            if clear_on_failure:
                connection.clearCredentials()
                if interactive and aw is not None:
                    aw.sendmessageSignal.emit(
                        QApplication.translate(
                            'Plus', 'artisan.plus turned off'
                        ),
                        True,
                        None,
                    )
            elif aw is not None:
                if interactive:
                    aw.sendmessageSignal.emit(
                        QApplication.translate(
                            'Plus', "Couldn't connect to artisan.plus"
                        ),
                        True,
                        None,
                    )
                if (aw.plus_account is not None and queue.queue is None):
                    # connect failed (most likely due to network issues)
                    # we anyhow initialize the queue if not yet done to get roasts queued up
                    try:
                        queue.start()  # start the outbox queue to initialize it
                    except Exception as ex:  # pylint: disable=broad-except
                        _log.exception(ex)
                config.connected = False
        finally:
            if connect_semaphore.available() < 1:
                connect_semaphore.release(1)
        if aw is not None:
            aw.updatePlusStatusSignal.emit()  # @UndefinedVariable
        if interactive and is_connected():
            QTimer.singleShot(2000, stock.update)


# show a dialog to have the user confirm the disconnect action
def disconnect_confirmed() -> bool:
    string = QApplication.translate('Plus', 'Disconnect artisan.plus?')
    aw = config.app_window
    assert isinstance(aw, QWidget) # pyrefly: ignore
#    reply = QMessageBox.question(
#        aw,
#        QApplication.translate('Plus', 'Disconnect?'),
#        string,
#        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
#    )
#    return QMessageBox.StandardButton.Ok == reply
    mbox = QMessageBox() #(aw) # only without super this one shows the native dialog on macOS under Qt 6.6.2
    mbox.setText(string)
    util.setPlusIcon(mbox)
    mbox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    res = mbox.exec()
    return QMessageBox.StandardButton.Yes == res


# if keepON is set (the default), the credentials are not removed at all and
# just the connected flag is toggled to keep plus in ON (dark-grey) state
def disconnect(
    remove_credentials: bool = True,
    stop_queue: bool = True,
    interactive: bool = False,
    keepON: bool = True
) -> None:
    _log.debug(
        'disconnect(%s,%s,%s,%s)',
        remove_credentials,
        stop_queue,
        interactive,
        keepON,
    )
    if (is_connected() or is_on()) and (
        not interactive or disconnect_confirmed()
    ):
        aw = config.app_window
        try:
            connect_semaphore.acquire(1)
            # disconnect
            config.connected = False
            # remove credentials
            if not keepON:
                connection.clearCredentials(
                    remove_from_keychain=remove_credentials
                )
            if aw is not None:
                if not keepON:
                    aw.plus_user_id = None # if this is cleared, the Scheduler cannot filter by user in this ON (dark-grey) state
                if remove_credentials:
                    aw.sendmessageSignal.emit(
                        QApplication.translate(
                            'Plus', 'artisan.plus turned off'
                        ),
                        True,
                        None,
                    )
                else:
                    aw.sendmessageSignal.emit(
                        QApplication.translate(
                            'Plus', 'artisan.plus disconnected'
                        ),
                        True,
                        None,
                    )
            if stop_queue:
                queue.stop()  # stop the outbox queue
            _log.info('artisan.plus disconnected')
        finally:
            if connect_semaphore.available() < 1:
                connect_semaphore.release(1)
        if aw is not None:
            aw.updatePlusStatusSignal.emit()  # @UndefinedVariable
            aw.disconnectPlusSignal.emit()  # @UndefinedVariable


def reconnected() -> None:
    if not is_connected():
        try:
            connect_semaphore.acquire(1)
            config.connected = True
            _log.info('artisan.plus reconnected')
        finally:
            if connect_semaphore.available() < 1:
                connect_semaphore.release(1)
        aw = config.app_window
        if aw is not None:
            aw.updatePlusStatusSignal.emit()  # @UndefinedVariable
        if is_connected():
            queue.start()  # restart the outbox queue


# if plus is ON and synced, computes the sync record hash, updates the
# sync record cache and returns the sync record hash
# otherwise return None
# this function is called by filesave() and returns the sync_record hash
# to be added to the saved file
def updateSyncRecordHashAndSync() -> Optional[str]:
    try:
        _log.debug('updateSyncRecordHashAndSync()')
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
