#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# login.py
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

from PyQt5.QtWidgets import QApplication,QCheckBox,QGroupBox,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit,QDialogButtonBox,QAction
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import (Qt,pyqtSlot)

from plus import config

from artisanlib.dialogs import ArtisanDialog

class Login(ArtisanDialog):
    def __init__(self, parent=None,email=None,saved_password=None,remember_credentials=True):
        super(Login, self).__init__(parent)
        
        self.login = None
        self.passwd = None
        self.remember = remember_credentials
        
        self.linkRegister = QLabel('<small><a href="' + config.register_url + '">' + QApplication.translate("Plus","Register",None) + '</a></small>')
        self.linkRegister.setOpenExternalLinks(True)
        self.linkResetPassword = QLabel('<small><a href="' + config.reset_passwd_url + '">' + QApplication.translate("Plus","Reset Password",None) + '</a></small>')
        self.linkResetPassword.setOpenExternalLinks(True)
        
        self.dialogbuttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,Qt.Horizontal)
        self.setButtonTranslations(self.dialogbuttons.button(QDialogButtonBox.Ok),"OK",QApplication.translate("Button","OK", None))
        self.setButtonTranslations(self.dialogbuttons.button(QDialogButtonBox.Cancel),"Cancel",QApplication.translate("Button","Cancel", None))
        
        self.dialogbuttons.accepted.connect(self.setCredentials)
        self.dialogbuttons.rejected.connect(self.reject)
        self.dialogbuttons.button(QDialogButtonBox.Ok).setEnabled(False)
        self.dialogbuttons.button(QDialogButtonBox.Cancel).setDefault(True)
        # add additional CMD-. shortcut to close the dialog
        self.dialogbuttons.button(QDialogButtonBox.Cancel).setShortcut(QKeySequence("Ctrl+."))
        # add additional CMD-W shortcut to close this dialog
        cancelAction = QAction(self, triggered=lambda _:self.reject())
        try:
            cancelAction.setShortcut(QKeySequence.Cancel)
        except:
            pass
        self.dialogbuttons.button(QDialogButtonBox.Cancel).addActions([cancelAction])
        
        self.textPass = QLineEdit(self)
        self.textPass.setEchoMode(QLineEdit.Password)
        self.textPass.setPlaceholderText(QApplication.translate("Plus","Password",None))
        
        self.textName = QLineEdit(self)
        self.textName.setPlaceholderText(QApplication.translate("Plus","Email",None))
        self.textName.textChanged.connect(self.textChanged)
        if email is not None:
            self.textName.setText(email)
        
        self.textPass.textChanged.connect(self.textChanged)
                
        self.rememberCheckbox = QCheckBox(QApplication.translate("Plus","Remember", None))
        self.rememberCheckbox.setChecked(self.remember)
        self.rememberCheckbox.stateChanged.connect(self.rememberCheckChanged)
        
        credentialsLayout = QVBoxLayout(self)
        credentialsLayout.addWidget(self.textName)
        credentialsLayout.addWidget(self.textPass)
        credentialsLayout.addWidget(self.rememberCheckbox)
        
        credentialsGroup = QGroupBox()
        credentialsGroup.setLayout(credentialsLayout)
        
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)
        buttonLayout.addStretch()
        
        linkLayout = QHBoxLayout()
        linkLayout.addStretch()
        linkLayout.addWidget(self.linkRegister)
        linkLayout.addStretch()
        linkLayout.addWidget(self.linkResetPassword)
        linkLayout.addStretch()
        
        layout = QVBoxLayout(self)
        layout.addWidget(credentialsGroup)
        layout.addLayout(linkLayout)
        layout.addLayout(buttonLayout)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        self.dialogbuttons.button(QDialogButtonBox.Ok).setFocusPolicy(Qt.StrongFocus)
        
        if saved_password is not None:
            self.passwd = saved_password
            self.textPass.setText(self.passwd)
            self.dialogbuttons.button(QDialogButtonBox.Cancel).setDefault(False)
            self.dialogbuttons.button(QDialogButtonBox.Ok).setDefault(True)
            self.dialogbuttons.button(QDialogButtonBox.Ok).setEnabled(True)
        
    @pyqtSlot()
    def reject(self):
        self.login = self.textName.text()
        super(Login,self).reject()

    @pyqtSlot(int)
    def rememberCheckChanged(self,i):
        self.remember = bool(i)
    
    def isInputReasonable(self):
        login = self.textName.text()
        passwd = self.textPass.text()
        return len(passwd) >= config.min_passwd_len and len(login) >= config.min_login_len and "@" in login and "." in login
    
    @pyqtSlot(str)
    def textChanged(self,_):
        if self.isInputReasonable():
            self.dialogbuttons.button(QDialogButtonBox.Cancel).setDefault(False)
            self.dialogbuttons.button(QDialogButtonBox.Ok).setDefault(True)
            self.dialogbuttons.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.dialogbuttons.button(QDialogButtonBox.Cancel).setDefault(True)
            self.dialogbuttons.button(QDialogButtonBox.Ok).setDefault(False)
            self.dialogbuttons.button(QDialogButtonBox.Ok).setEnabled(False)

    @pyqtSlot()
    def setCredentials(self):
        self.login = self.textName.text()
        self.passwd = self.textPass.text()
        self.accept()

def plus_login(window,email=None,saved_password=None,remember_credentials=True):
    l = Login(window,email,saved_password,remember_credentials)
    l.setWindowTitle("plus")
    l.setWindowFlags(Qt.Sheet)
    l.setAttribute(Qt.WA_DeleteOnClose, True)
    res = l.exec_()
    if l.login is not None:
        login_processed = l.login.strip()
    else:
        login_processed = None
    return login_processed,l.passwd,l.remember,res
