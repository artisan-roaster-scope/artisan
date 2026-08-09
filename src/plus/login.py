#
# login.py
#
# ABOUT
# This module connects to the artisan platform
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
# Marko Luther


import os
import logging
from typing import override, Final, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import

from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, # QCheckBox,
    QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QWidget)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QKeySequence, QAction


from artisanlib.util import getResourcePath
from artisanlib.dialogs import ArtisanDialog
from plus import config


_log: Final[logging.Logger] = logging.getLogger(__name__)

class Login(ArtisanDialog):

    __slots__ = [ 'login', 'passwd', #'remember',
        'linkRegister', 'linkResetPassword', 'textPass', 'textName' #, 'rememberCheckbox'
        ]


    def __init__(
        self,
        parent:QWidget,
        aw:'ApplicationWindow',
        email:str|None = None,
        saved_password:str|None = None,
        _remember_credentials: bool = True,
    ) -> None:
        super().__init__(parent,aw)

        self.login:str|None = None
        self.passwd:str|None = None
#        self.remember:bool = remember_credentials

        basedir = os.path.join(getResourcePath(),'Icons')
        register_icon_path = os.path.join(basedir, ('user-add-01-stroke-rounded-dark.svg' if aw.app.darkmode else 'user-add-01-stroke-rounded-light.svg'))
        self.register_icon = QSvgWidget(register_icon_path)
        self.register_icon.setMaximumSize(13,13)

        self.linkRegister = QLabel(
            f'<sub>{QApplication.translate('Plus','An artisan account unlocks more features.')} <a href="{config.register_url}">{QApplication.translate('Plus', 'Register')}</a></sub>'
        )
        self.linkRegister.setOpenExternalLinks(True)
        self.linkRegister.setStyleSheet(f"""
            QLabel {{
                color: {('#DDDDDD' if aw.app.darkmode else '#333333')};
            }}
        """)

        self.linkResetPassword = QLabel(
            f'<small><a href="{config.reset_passwd_url}">{QApplication.translate('Plus', 'Forgot Password')}</a></small>'
        )
        self.linkResetPassword.setOpenExternalLinks(True)

        sign_in_label = QLabel(f'<small>{QApplication.translate('Plus', 'Sign in to your artisan account')}</small>')
        sign_in_label.setStyleSheet(f"""
            QLabel {{
                color: {('#DDDDDD' if aw.app.darkmode else '#333333')};
            }}
        """)

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

        self.ok_button = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if self.ok_button is not None:
            self.ok_button.setEnabled(False)
            self.ok_button.setFocusPolicy(
                Qt.FocusPolicy.StrongFocus
            )
        self.cancel_button = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel)
        if self.cancel_button is not None:
            self.cancel_button.setDefault(True)
            # add additional CMD-. shortcut to close the dialog
            self.cancel_button.setShortcut(
                QKeySequence('Ctrl+.')
            )
            # add additional CMD-W shortcut to close this dialog
            cancelAction:QAction = QAction(self)
            cancelAction.triggered.connect(self.reject)
            cancelAction.setShortcut(QKeySequence.StandardKey.Cancel)
            self.cancel_button.addActions(
                [cancelAction]
            )

        lineEditstyle = """
            QLineEdit {
                border-radius: 10px;
                padding: 5px;
                border-color: palette(window);
                border-width: 2px;
                border-style: solid;
                background-color: palette(base);
            }
            QLineEdit:focus {
                border-color: palette(Accent);
            }
        """

        self.textPass:QLineEdit = QLineEdit(self)
        self.textPass.setMinimumWidth(230)
        self.textPass.setStyleSheet(lineEditstyle)


        self.textPass.setEchoMode(QLineEdit.EchoMode.Password)
        self.textPass.setPlaceholderText(
            QApplication.translate('Plus', 'Password')
        )

        self.textName:QLineEdit = QLineEdit(self)
        self.textName.setMinimumWidth(230)
        self.textName.setStyleSheet(lineEditstyle)

        self.textName.setPlaceholderText(
            QApplication.translate('Plus', 'Email')
        )
        self.textName.textChanged.connect(self.textChanged)
        if email is not None:
            self.textName.setText(email)

        self.textPass.textChanged.connect(self.textChanged)


#        self.rememberCheckbox = QCheckBox(
#            QApplication.translate('Plus', 'Remember')
#        )
#        self.rememberCheckbox.setChecked(self.remember)
#        self.rememberCheckbox.stateChanged.connect(self.rememberCheckChanged)
#
#        rememberLayout:QHBoxLayout = QHBoxLayout()
#        rememberLayout.addStretch()
#        rememberLayout.addWidget(self.rememberCheckbox)
#        rememberLayout.addStretch()

        registerIconLayout = QVBoxLayout()
        registerIconLayout.addStretch()
        registerIconLayout.addWidget(self.register_icon)
        registerIconLayout.addStretch()
        registerIconLayout.setContentsMargins(0, 5, 0, 0) # (left, top, right, bottom)

        linkRegisterLayout = QHBoxLayout()
        linkRegisterLayout.addStretch()
        linkRegisterLayout.addLayout(registerIconLayout)
        linkRegisterLayout.addWidget(self.linkRegister)
        linkRegisterLayout.addStretch()

        registerGroup:QGroupBox = QGroupBox()
        registerGroup.setLayout(linkRegisterLayout)
        linkRegisterLayout.setContentsMargins(6, 0, 6, 3) # (left, top, right, bottom)

        linkResetLayout = QHBoxLayout()
        linkResetLayout.addStretch()
        linkResetLayout.addWidget(self.linkResetPassword)

        credentialsLayout = QVBoxLayout(self)
        credentialsLayout.addWidget(self.textName)
        credentialsLayout.addWidget(self.textPass)
        credentialsLayout.addLayout(linkResetLayout)
#        credentialsLayout.addLayout(rememberLayout)

        credentialsGroup:QGroupBox = QGroupBox()
        credentialsGroup.setLayout(credentialsLayout)
        credentialsLayout.setContentsMargins(20, 20, 20, 5) # (left, top, right, bottom)



        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)
        buttonLayout.addStretch()

        signinLayout = QHBoxLayout()
        signinLayout.addStretch()
        signinLayout.addWidget(sign_in_label)
        signinLayout.addStretch()

        layout:QVBoxLayout = QVBoxLayout(self)
        layout.addLayout(signinLayout)
        layout.addWidget(credentialsGroup)
        layout.addSpacing(5)
        layout.addLayout(buttonLayout)
        layout.setSpacing(10)
        layout.addWidget(registerGroup)
#        layout.setContentsMargins(15, 15, 15, 15) # (left, top, right, bottom)

        if saved_password is not None:
            self.passwd = saved_password
            self.textPass.setText(self.passwd)
            if self.cancel_button is not None:
                self.cancel_button.setDefault(False)
            if self.ok_button is not None:
                self.ok_button.setDefault(True)
                self.ok_button.setEnabled(True)

    @pyqtSlot()
    @override
    def reject(self) -> None:
        self.login = self.textName.text()
        super().reject()

#    @pyqtSlot(int)
#    def rememberCheckChanged(self, i:int) -> None:
#        self.remember = bool(i)

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
            if self.cancel_button is not None:
                self.cancel_button.setDefault(False)
            if self.ok_button is not None:
                self.ok_button.setDefault(True)
                self.ok_button.setEnabled(True)
        else:
            if self.cancel_button is not None:
                self.cancel_button.setDefault(True)
            if self.ok_button is not None:
                self.ok_button.setDefault(False)
                self.ok_button.setEnabled(False)

    @pyqtSlot()
    def setCredentials(self) -> None:
        self.login = self.textName.text()
        self.passwd = self.textPass.text()
        self.accept()


def plus_login(
    window: QWidget,
    aw: 'ApplicationWindow',
    email: str|None = None,
    saved_password: str|None = None,
    remember_credentials: bool = True
) -> tuple[str|None, str|None, bool, int]:
    _log.debug('plus_login()')

    ld = Login(window, aw, email, saved_password, remember_credentials)
    ld.setWindowTitle('plus')
    ld.setWindowFlags(Qt.WindowType.Sheet)
    ld.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
    res:int = ld.exec()
    login_processed:str|None = ld.login.strip() if ld.login is not None else None
    passwd = ld.passwd
#    remember = ld.remember
    ld.destroy()
    del ld
    return login_processed, passwd, True, res
