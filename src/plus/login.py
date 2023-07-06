#
# login.py
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
    from PyQt6.QtWidgets import (
        QApplication, # @UnusedImport @Reimport  @UnresolvedImport
        QCheckBox, # @UnusedImport @Reimport  @UnresolvedImport
        QGroupBox, # @UnusedImport @Reimport  @UnresolvedImport
        QHBoxLayout, # @UnusedImport @Reimport  @UnresolvedImport
        QVBoxLayout, # @UnusedImport @Reimport  @UnresolvedImport
        QLabel, # @UnusedImport @Reimport  @UnresolvedImport
        QLineEdit, # @UnusedImport @Reimport  @UnresolvedImport
        QDialogButtonBox, # @UnusedImport @Reimport  @UnresolvedImport
        QWidget # @UnusedImport @Reimport  @UnresolvedImport
    )
    from PyQt6.QtCore import Qt, pyqtSlot # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QKeySequence, QAction # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #pylint: disable = E, W, R, C
    from PyQt5.QtWidgets import ( # type: ignore
        QApplication, # @UnusedImport @Reimport  @UnresolvedImport
        QCheckBox, # @UnusedImport @Reimport  @UnresolvedImport
        QGroupBox, # @UnusedImport @Reimport  @UnresolvedImport
        QHBoxLayout, # @UnusedImport @Reimport  @UnresolvedImport
        QVBoxLayout, # @UnusedImport @Reimport  @UnresolvedImport
        QLabel, # @UnusedImport @Reimport  @UnresolvedImport
        QLineEdit, # @UnusedImport @Reimport  @UnresolvedImport
        QDialogButtonBox, # @UnusedImport @Reimport  @UnresolvedImport
        QAction, # @UnusedImport @Reimport  @UnresolvedImport
        QWidget # @UnusedImport @Reimport  @UnresolvedImport
    )
    from PyQt5.QtCore import Qt, pyqtSlot # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QKeySequence # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

import logging
from artisanlib.dialogs import ArtisanDialog
from plus import config
from typing import Optional, Tuple, TYPE_CHECKING
from typing_extensions import Final  # Python <=3.7

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import

_log: Final[logging.Logger] = logging.getLogger(__name__)

class Login(ArtisanDialog):

    __slots__ = [ 'login', 'passwd', 'remember', 'linkRegister', 'linkResetPassword', 'textPass', 'textName', 'rememberCheckbox' ]


    def __init__(
        self,
        parent:QWidget,
        aw:'ApplicationWindow',
        email:Optional[str] = None,
        saved_password:Optional[str] = None,
        remember_credentials: bool = True,
    ) -> None:
        super().__init__(parent,aw)

        self.login:Optional[str] = None
        self.passwd:Optional[str] = None
        self.remember:bool = remember_credentials

        self.linkRegister = QLabel(
            f'<small><a href="{config.register_url}">{QApplication.translate("Plus", "Register")}</a></small>'
        )
        self.linkRegister.setOpenExternalLinks(True)
        self.linkResetPassword = QLabel(
            f'<small><a href="{config.reset_passwd_url}">{QApplication.translate("Plus", "Reset Password")}</a></small>'
        )
        self.linkResetPassword.setOpenExternalLinks(True)

        self.dialogbuttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.setButtonTranslations(
            self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok),
            'OK',
            QApplication.translate('Button', 'OK'),
        )
        self.setButtonTranslations(
            self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel),
            'Cancel',
            QApplication.translate('Button', 'Cancel'),
        )

        self.dialogbuttons.accepted.connect(self.setCredentials)
        self.dialogbuttons.rejected.connect(self.reject)
        self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel).setDefault(True)
        # add additional CMD-. shortcut to close the dialog
        self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel).setShortcut(
            QKeySequence('Ctrl+.')
        )
        # add additional CMD-W shortcut to close this dialog
        cancelAction:QAction = QAction(self)
        cancelAction.triggered.connect(self.reject)
        cancelAction.setShortcut(QKeySequence.StandardKey.Cancel)
        self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel).addActions(
            [cancelAction]
        )

        self.textPass:QLineEdit = QLineEdit(self)
        self.textPass.setEchoMode(QLineEdit.EchoMode.Password)
        self.textPass.setPlaceholderText(
            QApplication.translate('Plus', 'Password')
        )

        self.textName:QLineEdit = QLineEdit(self)
        self.textName.setPlaceholderText(
            QApplication.translate('Plus', 'Email')
        )
        self.textName.textChanged.connect(self.textChanged)
        if email is not None:
            self.textName.setText(email)

        self.textPass.textChanged.connect(self.textChanged)

        self.rememberCheckbox = QCheckBox(
            QApplication.translate('Plus', 'Remember')
        )
        self.rememberCheckbox.setChecked(self.remember)
        self.rememberCheckbox.stateChanged.connect(self.rememberCheckChanged)

        credentialsLayout:QVBoxLayout = QVBoxLayout(self)
        credentialsLayout.addWidget(self.textName)
        credentialsLayout.addWidget(self.textPass)
        credentialsLayout.addWidget(self.rememberCheckbox)

        credentialsGroup:QGroupBox = QGroupBox()
        credentialsGroup.setLayout(credentialsLayout)

        buttonLayout:QHBoxLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)
        buttonLayout.addStretch()

        linkLayout:QHBoxLayout = QHBoxLayout()
        linkLayout.addStretch()
        linkLayout.addWidget(self.linkRegister)
        linkLayout.addStretch()
        linkLayout.addWidget(self.linkResetPassword)
        linkLayout.addStretch()

        layout:QVBoxLayout = QVBoxLayout(self)
        layout.addWidget(credentialsGroup)
        layout.addLayout(linkLayout)
        layout.addLayout(buttonLayout)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok).setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

        if saved_password is not None:
            self.passwd = saved_password
            self.textPass.setText(self.passwd)
            self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel).setDefault(
                False
            )
            self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok).setDefault(True)
            self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    @pyqtSlot()
    def reject(self) -> None:
        self.login = self.textName.text()
        super().reject()

    @pyqtSlot(int)
    def rememberCheckChanged(self, i:int) -> None:
        self.remember = bool(i)

    def isInputReasonable(self) -> bool:
        login = self.textName.text()
        passwd = self.textPass.text()
        return (
            len(passwd) >= config.min_passwd_len
            and len(login) >= config.min_login_len
            and '@' in login
            and '.' in login
        )

    @pyqtSlot(str)
    def textChanged(self, _:str) -> None:
        if self.isInputReasonable():
            self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel).setDefault(
                False
            )
            self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok).setDefault(True)
            self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel).setDefault(True)
            self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok).setDefault(False)
            self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    @pyqtSlot()
    def setCredentials(self) -> None:
        self.login = self.textName.text()
        self.passwd = self.textPass.text()
        self.accept()


def plus_login(
    window: QWidget,
    aw: 'ApplicationWindow',
    email: Optional[str] = None,
    saved_password: Optional[str] = None,
    remember_credentials: bool = True
) -> Tuple[Optional[str], Optional[str], bool, int]:
    _log.debug('plus_login()')
    ld = Login(window, aw, email, saved_password, remember_credentials)
    ld.setWindowTitle('plus')
    ld.setWindowFlags(Qt.WindowType.Sheet)
    ld.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
    res:int = ld.exec()
    login_processed:Optional[str] = ld.login.strip() if ld.login is not None else None
    return login_processed, ld.passwd, ld.remember, res
