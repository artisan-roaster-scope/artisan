#
# ABOUT
# Artisan Dialogs

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

import platform
import logging

try:
    from PyQt6.QtCore import Qt, QEvent, QSettings, pyqtSlot # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QWidget, QDialog, QMessageBox, QDialogButtonBox, QTextEdit,  # @UnusedImport @Reimport  @UnresolvedImport
                QHBoxLayout, QVBoxLayout, QLabel, QLineEdit)  # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QKeySequence, QAction  # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import Qt, QEvent, QSettings, pyqtSlot # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QWidget, QAction, QDialog, QMessageBox, QDialogButtonBox, QTextEdit, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
                QHBoxLayout, QVBoxLayout, QLabel, QLineEdit) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QKeySequence # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.widgets import MyQComboBox

from typing import Optional, List, Tuple, TYPE_CHECKING
from typing import Final  # Python <=3.7
if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    from PyQt6.QtWidgets import QPushButton # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent, QKeyEvent, QShowEvent  # pylint: disable=unused-import
    from PyQt6.QtCore import QTimerEvent, QEvent, QObject # pylint: disable=unused-import

_log: Final[logging.Logger] = logging.getLogger(__name__)

class ArtisanDialog(QDialog): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class

    __slots__ = ['aw', 'dialogbuttons']

    def __init__(self, parent:Optional[QWidget], aw:'ApplicationWindow') -> None:
        super().__init__(parent)
        self.aw = aw # the Artisan application window

        # IMPORTANT NOTE: if dialog items have to be access after it has been closed, this Qt.WidgetAttribute.WA_DeleteOnClose attribute
        # has to be set to False explicitly in its initializer (like in comportDlg) to avoid the early GC and one might
        # want to use a dialog.deleteLater() call to explicitly have the dialog and its widgets GCe
        # or rather use sip.delete(dialog) if the GC via .deleteLater() is prevented by a link to a parent object (parent not None)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

#        if platf == 'Windows':
# setting those Windows flags could be the reason for some instabilities on Windows
#            windowFlags = self.windowFlags()
#        #windowFlags &= ~Qt.WindowType.WindowContextHelpButtonHint # remove help button
#        #windowFlags &= ~Qt.WindowType.WindowMaximizeButtonHint # remove maximise button
#        #windowFlags &= ~Qt.WindowType.WindowMinMaxButtonsHint  # remove min/max combo
#        #windowFlags |= Qt.WindowType.WindowMinimizeButtonHint  # Add minimize  button
#        windowFlags |= Qt.WindowType.WindowSystemMenuHint  # Adds a window system menu, and possibly a close button
#            windowFlags |= Qt.WindowType.WindowMinMaxButtonsHint  # add min/max combo
#            self.setWindowFlags(windowFlags)

        # configure standard dialog buttons
        self.dialogbuttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,Qt.Orientation.Horizontal)
        okButton: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if okButton is not None:
            okButton.setDefault(True)
            okButton.setAutoDefault(True)
            okButton.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # to add to tab focus switch
        cancelButton: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancelButton is not None:
            cancelButton.setDefault(False)
            cancelButton.setAutoDefault(False)
            # add additional CMD-. shortcut to close the dialog
            cancelButton.setShortcut(QKeySequence('Ctrl+.'))
            # add additional CMD-W shortcut to close this dialog (ESC on Mac OS X)
    #        cancelAction = QAction(self, triggered=lambda _:self.dialogbuttons.rejected.emit())
            cancelAction = QAction(self)
            cancelAction.triggered.connect(self.cancelDialog)
            try:
                cancelAction.setShortcut(QKeySequence.StandardKey.Cancel)
            except Exception: # pylint: disable=broad-except
                pass
            cancelButton.addActions([cancelAction])
        for btn,txt,trans in [
                (okButton,'OK', QApplication.translate('Button','OK')),
                (cancelButton,'Cancel',QApplication.translate('Button','Cancel'))]:
            self.setButtonTranslations(btn,txt,trans)

    @pyqtSlot()
    def cancelDialog(self) -> None:
#        self.dialogbuttons.rejected.emit()
        self.reject()

    @staticmethod
    def setButtonTranslations(btn: Optional['QPushButton'], txt:str, trans:str) -> None:
        if btn is not None:
            current_trans = btn.text()
            if txt == current_trans:
                # if standard qtbase translations fail, revert to artisan translations
                current_trans = trans
            if txt != current_trans:
                btn.setText(current_trans)

    @pyqtSlot('QCloseEvent')
    def closeEvent(self,_:Optional['QCloseEvent'] = None) -> None:
        self.dialogbuttons.rejected.emit()

    def keyPressEvent(self, event: Optional['QKeyEvent']) -> None:
        if event is not None:
            key = int(event.key())
            #uncomment next line to find the integer value of a key
            #print(key)
            #modifiers = QApplication.keyboardModifiers()
            modifiers = event.modifiers()
            if key == 16777216 or (key == 87 and modifiers == Qt.KeyboardModifier.ControlModifier): #ESCAPE or CMD-W
                self.close()
            else:
                super().keyPressEvent(event)

class ArtisanResizeablDialog(ArtisanDialog):
    def __init__(self, parent:QWidget, aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        if str(platform.system()) == 'Windows':
            windowFlags = self.windowFlags()
            windowFlags |= Qt.WindowType.WindowMinMaxButtonsHint  # add min/max combo
            self.setWindowFlags(windowFlags)

# if modal=False the message box is not rendered as native dialog on macOS!
class ArtisanMessageBox(QMessageBox): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class

    __slots__ = ['timeout', 'currentTime']

    def __init__(self, parent:Optional[QWidget] = None, title:Optional[str] = None, text:Optional[str] = None, timeout:int = 0, modal:bool = True) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setText(text)
        self.setModal(modal)
        self.setIcon(QMessageBox.Icon.Information)
        self.setStandardButtons(QMessageBox.StandardButton.Ok)
        self.setDefaultButton(QMessageBox.StandardButton.Ok)

        self.timeout = timeout # configured timeout, defaults to 0 (no timeout)
        self.currentTime = 0 # counts seconds after timer start

    def showEvent(self, _:Optional['QShowEvent']) -> None:
        self.currentTime = 0
        if (self.timeout and self.timeout != 0):
            self.startTimer(1000)

    def timerEvent(self, _:Optional['QTimerEvent']) -> None:
        self.currentTime = self.currentTime + 1
        if self.currentTime >= self.timeout:
            self.done(0)

class HelpDlg(ArtisanDialog):
    def __init__(self, parent:QWidget, aw:'ApplicationWindow', title:str = '', content:str = '') -> None:
        super().__init__(parent, aw)
        self.setWindowTitle(title)
        self.setModal(False)

        settings = QSettings()
        if settings.contains('HelpGeometry'):
            self.restoreGeometry(settings.value('HelpGeometry'))

        phelp = QTextEdit()
        phelp.setHtml(content)
        phelp.setReadOnly(True)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.removeButton(self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel))
        self.dialogbuttons.accepted.connect(self.reject)

        homeLabel = QLabel()
        homeLabel.setText(f"{QApplication.translate('Label', 'For more details visit')} <a href='https://artisan-scope.org'>artisan-scope.org</a>")
        homeLabel.setOpenExternalLinks(True)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(homeLabel)
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)
        hLayout = QVBoxLayout()
        hLayout.addWidget(phelp)
        hLayout.addLayout(buttonLayout)
        self.setLayout(hLayout)
        okButton: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if okButton is not None:
            okButton.setFocus()

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        settings = QSettings()
        #save window geometry
        settings.setValue('HelpGeometry',self.saveGeometry())
        self.dialogbuttons.rejected.emit()

class ArtisanInputDialog(ArtisanDialog):

    __slots__ = ['url', 'inputLine']

    def __init__(self, parent:QWidget, aw:'ApplicationWindow', title:str = '', label:str = '') -> None:
        super().__init__(parent, aw)

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        self.url = ''

        self.setWindowTitle(title)
        self.setModal(True)
        self.setAcceptDrops(True)
        self.inputLine = QLineEdit(self.url)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        layout.addWidget(self.inputLine)
        layout.addWidget(self.dialogbuttons)
        self.setLayout(layout)
        self.setFixedHeight(self.sizeHint().height())
        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.rejected.connect(self.reject)
        self.dialogbuttons.accepted.connect(self.accept)
        okButton: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if okButton is not None:
            okButton.setFocus()

    @pyqtSlot()
    def accept(self) -> None:
        self.url = self.inputLine.text()
        super().accept()

    @staticmethod
    def dragEnterEvent(event:Optional['QDragEnterEvent']) -> None:
        if event is not None:
            mimeData = event.mimeData()
            if mimeData is not None:
                if mimeData.hasUrls():
                    event.accept()
                else:
                    event.ignore()

    def dropEvent(self, event:Optional['QDropEvent']) -> None:
        if event is not None:
            mimeData = event.mimeData()
            if mimeData is not None and mimeData.hasUrls():
                urls = mimeData.urls()
                if urls and len(urls)>0:
                    self.inputLine.setText(urls[0].toString())


class ArtisanComboBoxDialog(ArtisanDialog):

    __slots__ = [ 'idx', 'comboBox' ]

    def __init__(self, parent:QWidget, aw:'ApplicationWindow', title:str = '', label:str='', choices:Optional[List[str]] = None, default:int = -1) -> None:
        super().__init__(parent, aw)

        self.idx:Optional[int] = None

        self.setWindowTitle(title)
        self.setModal(True)
        self.comboBox = MyQComboBox()
        if choices is not None:
            self.comboBox.addItems(choices)
        self.comboBox.setCurrentIndex(default)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        layout.addWidget(self.comboBox)
        layout.addWidget(self.dialogbuttons)
        self.setLayout(layout)
        self.setFixedHeight(self.sizeHint().height())
        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.rejected.connect(self.reject)
        self.dialogbuttons.accepted.connect(self.accept)
        okButton: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if okButton is not None:
            okButton.setFocus()

    @pyqtSlot()
    def accept(self) -> None:
        self.idx = self.comboBox.currentIndex()
        QDialog.accept(self)


class PortComboBox(MyQComboBox):  # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class

    __slots__ = ['selection', 'select_device_name', 'ports','edited'] # save some memory by using slots

    # the given select_device_name is preferred (if a corresponding port is found) over the given selection port name
    def __init__(self, parent:Optional[QWidget] = None, selection:Optional[str] = None, select_device_name:Optional[str] = None) -> None:
        super().__init__(parent)
        self.installEventFilter(self)
        self.selection:Optional[str] = selection # just the port name (first element of one of the triples in self.ports)
        self.select_device_name:Optional[str] = select_device_name # device name (second element of one of the triples in self.ports)

        self.setEditable(True)

        # a list of triples as returned by serial.tools.list_ports
        self.ports:List[Tuple[str, Optional[str], str]] = []  # list of tuples (port, desc, hwid)
        self.updateMenu()
        self.edited:Optional[str] = None
        if self.selection is not None:
            self.setCurrentText(self.selection)
        self.currentIndexChanged.connect(self.setSelection)

        # we prefer the device name if available over the selection port
        try:
            if self.select_device_name is not None:
                pos = [p[1] for p in self.ports].index(self.select_device_name)
                self.setCurrentIndex(pos)
        except Exception: # pylint: disable=broad-except
            pass
        self.editTextChanged.connect(self.textEdited) # this has to be done after the setCurrentIndex above to avoid setting the self.edited to the currents ports name

    @pyqtSlot(str)
    def textEdited(self, txt:str) -> None:
        self.edited = txt

    def getSelection(self) -> Optional[str]:
        return self.edited or self.selection

    @pyqtSlot(int)
    def setSelection(self, i:int) -> None:
        if i >= 0:
            try:
                self.edited = None # reset the user text editing
                self.selection = self.ports[i][0]
            except Exception: # pylint: disable=broad-except
                pass

    def eventFilter(self, obj:Optional['QObject'], event:Optional['QEvent']) -> bool:
# the next prevents correct setSelection on Windows
#        if event.type() == QEvent.Type.FocusIn:
#            self.setSelection(self.currentIndex())
        if event is not None and event.type() == QEvent.Type.MouseButtonPress:
            self.updateMenu()
        return super().eventFilter(obj, event)

    def updateMenu(self) -> None:
        self.blockSignals(True)
        try:
            import serial.tools.list_ports
            # on older versions of pyserial list_ports.comports() returned a list of tuples (port, desc, hwid), current versions return a list of ListPortInfo objects
            comports = [(cp.device, cp.product, 'n/a') for cp in serial.tools.list_ports.comports()]
            if platform.system() == 'Darwin':
                self.ports = [p for p in comports if (p[0] not in ['/dev/cu.Bluetooth-PDA-Sync',
                    '/dev/cu.Bluetooth-Modem','/dev/tty.Bluetooth-PDA-Sync','/dev/tty.Bluetooth-Modem','/dev/cu.Bluetooth-Incoming-Port','/dev/tty.Bluetooth-Incoming-Port'])]
            else:
                self.ports = list(comports)
            if self.selection is not None and self.selection not in [p[0] for p in self.ports]:
                self.ports.append((self.selection,'',''))
            self.ports = sorted(self.ports,key=lambda p: p[0])
            self.clear()
            self.addItems([(p[1] if (p[1] is not None and p[1]!='n/a') else p[0]) for p in self.ports])
            try:
                if self.selection is not None:
                    pos = [p[0] for p in self.ports].index(self.selection)
                    self.setCurrentIndex(pos)
            except Exception: # pylint: disable=broad-except
                pass
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        self.blockSignals(False)


class ArtisanPortsDialog(ArtisanDialog):

    __slots__ = [ 'idx', 'comboBox' ]

    def __init__(self, parent:QWidget, aw:'ApplicationWindow', title:Optional[str] = None,
            label:Optional[str] = None,
            selection:Optional[str] = None,
            select_device_name:Optional[str] = None) -> None:
        super().__init__(parent, aw)
        self.idx:Optional[int] = None
        self.comboBox = PortComboBox(parent, selection, select_device_name)

        self.setWindowTitle(QApplication.translate('Message', 'Port Configuration') if title is None else title)
        self.setModal(True)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(QApplication.translate('Message', 'Comm Port') if label is None else label))
        layout.addWidget(self.comboBox)
        layout.addWidget(self.dialogbuttons)
        self.setLayout(layout)
        self.setFixedHeight(self.sizeHint().height())
        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.rejected.connect(self.reject)
        self.dialogbuttons.accepted.connect(self.accept)
        okButton: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if okButton is not None:
            okButton.setFocus()

    def getSelection(self) -> Optional[str]:
        return self.comboBox.getSelection()

    @pyqtSlot()
    def accept(self) -> None:
        self.idx = self.comboBox.currentIndex()
        QDialog.accept(self)
