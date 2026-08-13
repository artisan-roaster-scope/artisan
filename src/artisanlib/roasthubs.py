#
# ABOUT
# Profile upload to RoastHubs platform
#
# COPYRIGHT (C) 2010-2026 The artisan team represented by
#   Marko Luther <marko.luther@gmx.net> (maintainer) and all contributors
#
# LICENSE
# This program or module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# MAINTAINER
# Marko Luther, 2026
#
# AUTHOR
# Marko Luther, 2026


import logging
import asyncio
import aiohttp
import uuid
import concurrent.futures
from aiohttp_retry import RetryClient, ExponentialRetry
from collections.abc import Callable
from typing import Final, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from artisanlib.atypes import ProfileData # pylint: disable=unused-import
    from proto import artisan_roast_pb2 # pylint: disable=unused-import

from PyQt6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout,
    QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QLayout)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QKeySequence, QAction


from artisanlib import __version__
from artisanlib.util import roast_message
from artisanlib.dialogs import ArtisanDialog
from artisanlib.widgets import StyledQLineEdit

_log: Final[logging.Logger] = logging.getLogger(__name__)

SERVICE_NAME:Final[str] = 'RoastHubs'
#API_BASE_URL:Final[str] = 'http://0.0.0.0:8080' # test server
API_BASE_URL:Final[str] = 'https://api.roasthubs.com'
INGEST_ENDPOINT:Final[str] = 'v1/ingest/artisan'
POST_RETRIES:Final[int] = 4
RETRY_STATUSES:Final[set[int]] = {x for x in range(100, 600) if x not in {200,401,403}}
START_TIMEOUT:Final[float] = 0.5   # Base timeout time, then it exponentially grow (default: 0.1s)
#don't retry:
#  200: OK
#  401: Unauthorized (wrong token)
#  403: Forbidden (org_id/machine_id not supported)

async def send_roast(roast:'artisan_roast_pb2.Roast', token:str,
        on_success:Callable[[], None] | None,
        on_failure:Callable[[], None] | None) -> None:
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'Content-Type': 'application/protobuf',
                'User-Agent': f'artisan/{__version__}',
                'Accept-Encoding': 'deflate, compress, gzip',
                'Authorization': f'Bearer {token}',
                'Idempotency-Key': uuid.uuid4().hex
            }
            url=f"{API_BASE_URL}/{INGEST_ENDPOINT}"
            payload = roast.SerializeToString()
#            _log.debug("PRINT payload proto size: %s",len(payload))
            retry_options = ExponentialRetry(
                attempts=POST_RETRIES,
                statuses=RETRY_STATUSES,
                start_timeout=START_TIMEOUT,
                retry_all_server_errors=True) # retry on return code higher than 500 (internal server errors, gateway timeouts,..)
            retry_client = RetryClient(
                client_session=session,
                raise_for_status=False, # don't raise an exception for return codes higher than 400 (client request errors)
                retry_options=retry_options)
            try:
                async with retry_client.post(url, data=payload, headers=headers, compress=True, timeout=1) as response:
                    if response.status == 200:
                        _log.debug('profile uploaded successful to RoastHubs')
                        if on_success is not None:
                            on_success()
                    else:
                        _log.debug('profile to RoastHubs failed with status: %s', response.status)
                        if on_failure is not None:
                            on_failure()
            except TimeoutError as e:
                _log.debug('TimeoutError: %s',e)
    except Exception as e:  # pylint: disable=broad-except
        _log.error('exception in roasthubs:send_roast: %s', e)


def send_profile(
        profile:'ProfileData',
        org_id:str,
        machine_id:str,
        token:str,
        # filter conf
        interpolate_drops:bool = True,
        curvefilter:int = 3,
        medfilt_factor:int = 3,
        limit_ror:bool = True,
        ror_limit_min:int = 0,
        ror_limit_max:int = 170,
        delta_span_ET:int = 20,
        delta_span_BT:int = 20,
        medfilt_factor_RoR:int = 3,
        delta_ET_filter:int = 7,
        delta_BT_filter:int = 7,
        # handlers
        on_success:Callable[[], None] | None = None,
        on_failure:Callable[[], None] | None = None) -> None:
    if org_id != '' and machine_id != '' and token != '':
        # only if org_id and machin_id are not empty the connector is active
        roast:artisan_roast_pb2.Roast|None = roast_message( # pylint: disable=no-member
                profile,
                org_id=org_id,
                machine_id=machine_id,
                # filter conf
                interpolate_drops=interpolate_drops,
                smooth_curves=True,
                curvefilter=curvefilter,
                medfilt_factor=medfilt_factor,
                decay_smoothing_p=False, # optimal smoothing # qmc.optimalSmoothing
                limit_ror=limit_ror,
                ror_limit_min=ror_limit_min,
                ror_limit_max=ror_limit_max,
                delta_span_ET=delta_span_ET,
                delta_span_BT=delta_span_BT,
                medfilt_factor_RoR=medfilt_factor_RoR,
                delta_ET_filter=delta_ET_filter,
                delta_BT_filter=delta_BT_filter
            ) # pylint: disable=no-member
        if roast is not None:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                executor.submit(asyncio.run, send_roast(roast, token, on_success, on_failure))
        else:
            _log.error('generating profile payload failed')


##

# returns keyring key
def roasthubsKey(org_id:str, machine_id:str) -> str:
    return f'{org_id}:{machine_id}'

def get_token(org_id:str, machine_id:str) -> str:
    token:str = ''
    if org_id != '' and machine_id != '':
        try:
            import keyring
            retrieved_token = keyring.get_password(SERVICE_NAME, roasthubsKey(org_id, machine_id))
            if retrieved_token is not None:
                token = retrieved_token
        except Exception as e:  # pylint: disable=broad-except
            _log.error(e)
    return token

def set_token(org_id:str, machine_id:str, token:str) -> None:
    if token != '':
        try:
            import keyring
            keyring.set_password(SERVICE_NAME,
                roasthubsKey(org_id,machine_id),
                token)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)


##


class RoastHubsdialog(ArtisanDialog):

    __slots__ = [ 'org_id', 'machine_id', 'token' ]

    def __init__(self, aw:'ApplicationWindow') -> None:
        super().__init__(aw,aw)

        self.org_id:str = aw.roasthubs_org_id
        self.machine_id:str = aw.roasthubs_machine_id
        self.token:str = aw.roasthubs_token

        self.dialogbuttons.accepted.connect(self.setCredentials)
        self.dialogbuttons.rejected.connect(self.reject)

        self.ok_button = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        credentials_set = self.org_id != '' and self.machine_id != '' and self.token != ''
        if self.ok_button is not None:
            self.ok_button.setEnabled(credentials_set)
        self.cancel_button = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel)
        if self.cancel_button is not None:
            self.cancel_button.setDefault(not credentials_set)
            # add additional CMD-. shortcut to close the dialog
            self.cancel_button.setShortcut(QKeySequence('Ctrl+.'))
            # add additional CMD-W shortcut to close this dialog
            cancelAction:QAction = QAction(self)
            cancelAction.triggered.connect(self.reject)
            cancelAction.setShortcut(QKeySequence.StandardKey.Cancel)
            self.cancel_button.addActions([cancelAction])

        self.labelTitle:QLabel = QLabel('RoastHubs')

        self.textOrgId = StyledQLineEdit(self)
        self.textOrgId.setMinimumWidth(300)
        self.textOrgId.setPlaceholderText(QApplication.translate('Label','Organization ID'))
        self.textOrgId.setText(self.org_id)

        self.textMachineId = StyledQLineEdit(self)
        self.textMachineId.setMinimumWidth(300)
        self.textMachineId.setPlaceholderText(QApplication.translate('Label','Machine ID'))
        self.textMachineId.setText(self.machine_id)

        self.textSecret = StyledQLineEdit(self)
        self.textSecret.setPlaceholderText(QApplication.translate('Label','Token'))
        self.textSecret.setEchoMode(QLineEdit.EchoMode.Password)
        self.textSecret.setText(self.token)


        #

        self.textOrgId.textChanged.connect(self.textChanged)
        self.textMachineId.textChanged.connect(self.textChanged)
        self.textSecret.textChanged.connect(self.textChanged)

        #

        titleLabelLayout:QHBoxLayout = QHBoxLayout()
        titleLabelLayout.addStretch()
        titleLabelLayout.addWidget(self.labelTitle)
        titleLabelLayout.addStretch()

        credentialsLayout:QVBoxLayout = QVBoxLayout(self)
        credentialsLayout.addWidget(self.textOrgId)
        credentialsLayout.addWidget(self.textMachineId)
        credentialsLayout.addWidget(self.textSecret)

        credentialsGroup:QGroupBox = QGroupBox()
        credentialsGroup.setLayout(credentialsLayout)

        buttonLayout:QHBoxLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)
        buttonLayout.addStretch()

        layout:QVBoxLayout = QVBoxLayout(self)
        layout.addLayout(titleLabelLayout)
        layout.addWidget(credentialsGroup)
        layout.addLayout(buttonLayout)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # not resizable
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.setSizeGripEnabled(False)


    @pyqtSlot(str)
    def textChanged(self, _:str) -> None:
        credentials_available:bool = self.textOrgId.text() != '' and self.textMachineId.text() != '' and self.textSecret.text() != ''
        if self.ok_button is not None:
            self.ok_button.setDefault(credentials_available)
            self.ok_button.setEnabled(credentials_available)
        if self.cancel_button is not None:
            self.cancel_button.setDefault(not credentials_available)

    @pyqtSlot()
    def setCredentials(self) -> None:
        self.org_id = self.textOrgId.text()
        self.machine_id = self.textMachineId.text()
        self.token = self.textSecret.text()
        self.accept()

def setRoastHubsCredentials(aw:'ApplicationWindow', org_id:str, machine_id:str, token:str) -> None:
    aw.roasthubs_org_id = org_id.strip()
    aw.roasthubs_machine_id = machine_id.strip()
    aw.roasthubs_token = token.strip()
    set_token(aw.roasthubs_org_id, aw.roasthubs_machine_id, aw.roasthubs_token)


# returns True on success
def configureConnection(aw:'ApplicationWindow') -> bool:
    rd = RoastHubsdialog(aw)
    rd.setWindowFlags(Qt.WindowType.Sheet)
    rd.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
    if rd.exec():
        # login dialog not canceled
        try:
            setRoastHubsCredentials(aw, rd.org_id, rd.machine_id, rd.token)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        rd.destroy()
        del rd
        return True
    return False
