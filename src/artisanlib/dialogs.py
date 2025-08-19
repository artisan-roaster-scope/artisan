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
import re

try:
    from PyQt6.QtCore import Qt, QEvent, QSettings, pyqtSlot, pyqtSignal, QRegularExpression # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QWidget, QDialog, QMessageBox, QDialogButtonBox, QTextEdit,  # @UnusedImport @Reimport  @UnresolvedImport
                QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QLayout, QTableWidget, QHeaderView, QPushButton)  # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QKeySequence, QAction, QIntValidator, QTextCharFormat, QTextCursor, QColor  # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import Qt, QEvent, QSettings, pyqtSlot, pyqtSignal, QRegularExpression # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QWidget, QAction, QDialog, QMessageBox, QDialogButtonBox, QTextEdit, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
                QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QLayout, QTableWidget, QHeaderView, QPushButton) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QKeySequence, QIntValidator, QTextCharFormat, QTextCursor, QColor # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.widgets import MyQComboBox, ClickableQLineEdit
from artisanlib.util import comma2dot, float2float, float2floatWeightVolume, convertWeight, weight_units

from typing import Optional, List, Tuple, cast, Callable, TYPE_CHECKING
from typing import Final  # Python <=3.7
if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    from PyQt6.QtWidgets import QPushButton # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent, QKeyEvent, QShowEvent, QTextCursor  # pylint: disable=unused-import
    from PyQt6.QtCore import QTimerEvent, QEvent, QObject # pylint: disable=unused-import

_log: Final[logging.Logger] = logging.getLogger(__name__)

class ArtisanDialog(QDialog): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class

    __slots__ = ['aw', 'dialogbuttons']

    def __init__(self, parent:Optional[QWidget], aw:'ApplicationWindow') -> None:
        super().__init__(parent)  # pyrefly: ignore[bad-argument-count]
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

    @staticmethod
    def setButtonTranslations(btn: Optional['QPushButton'], txt:str, trans:str) -> None:
        if btn is not None:
            current_trans = btn.text()
            if txt == current_trans:
                # if standard qtbase translations fail, revert to artisan translations
                current_trans = trans
            if txt != current_trans:
                btn.setText(current_trans)

    @pyqtSlot()
    def cancelDialog(self) -> None:  # ESC key
#        self.reject() # this does not call any closeEvent in subclasses!
        self.dialogbuttons.rejected.emit()

    @pyqtSlot('QCloseEvent')
    def closeEvent(self,_:Optional['QCloseEvent']) -> None:
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
    def __init__(self, parent:Optional[QWidget], aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        if str(platform.system()) == 'Windows':
            windowFlags = self.windowFlags()
#            windowFlags |= Qt.WindowType.CustomizeWindowHint # turn off default window title hints
            windowFlags |= Qt.WindowType.WindowMinMaxButtonsHint  # add min/max combo
            self.setWindowFlags(windowFlags)

# if modal=False the message box is not rendered as native dialog on macOS!
class ArtisanMessageBox(QMessageBox): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class

    __slots__ = ['timeout', 'currentTime']

    def __init__(self, parent:Optional[QWidget] = None, title:Optional[str] = None, text:Optional[str] = None, timeout:int = 0, modal:bool = True) -> None:
        super().__init__(parent) # pyrefly: ignore[bad-argument-count]
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

        # Load the help content
        self.phelp = QTextEdit()
        self.phelp.setHtml(content)
        self.phelp.setReadOnly(True)

        # Initialize search state variables
        self.matches: List[QTextCursor] = []
        self.current_match_index = 0
        self.previous_search_term = ''

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(QApplication.translate('Label', 'Enter text to search'))

        # Connect Enter key to search and navigate results
        self.search_input.returnPressed.connect(self.doSearch)

        # Show only the ArtisanDialog standard OK button
        self.dialogbuttons.removeButton(self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel))

        # Connect the OK button to handleClose()
        okButton = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if okButton:
            okButton.clicked.connect(self.handleClose)

        # Build the dialog layout
        homeLabel = QLabel()
        homeLabel.setText(f"{QApplication.translate('Label', 'For more details visit')} <a href='https://artisan-scope.org/help/'>artisan-scope.org/help/</a>")
        homeLabel.setOpenExternalLinks(True)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(homeLabel)
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.search_input)
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)
        hLayout = QVBoxLayout()
        hLayout.addWidget(self.phelp)
        hLayout.addLayout(buttonLayout)
        self.setLayout(hLayout)

    def keyPressEvent(self, event: Optional['QKeyEvent']) -> None:
        if event is not None:
            key = event.key()
            # uncomment next lines to find the integer value and name of a key
            #key_name = QKeySequence(key).toString(QKeySequence.SequenceFormat.PortableText)
            #_log.info(f'{key=}, {key_name=}')

            modifiers = event.modifiers()
            # Ctrl+F puts focus in the search box
            if key == Qt.Key.Key_F and modifiers == Qt.KeyboardModifier.ControlModifier:
                self.search_input.setFocus()
            # Esc closes dialog
            elif key == Qt.Key.Key_Escape:
                self.handleClose()
            # Enter/Return only when Ok button or self.phelp has focus
            elif key in {Qt.Key.Key_Enter, Qt.Key.Key_Return}:
                focused_widget = self.focusWidget()
                okButton = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
                if focused_widget is okButton or focused_widget is self.phelp:
                    self.handleClose()
            else:
                super().keyPressEvent(event)

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _: Optional['QCloseEvent'] = None) -> None:
        self.handleClose()

    @pyqtSlot()
    def handleClose(self) -> None:
        settings = QSettings()
        # Save window geometry
        settings.setValue('HelpGeometry', self.saveGeometry())
        self.accept()

    def doSearch(self) -> None:
        # Always start by clearing extra selections and any active text selection
        self.phelp.setExtraSelections([])
        tc = self.phelp.textCursor()
        tc.clearSelection()
        self.phelp.setTextCursor(tc)

        search_term = self.search_input.text().strip()

        # Clear highlights and state when search term is empty
        if search_term == '':
            self.matches = []
            self.previous_search_term = ''
            return

        # Do a fresh search when a new search_term is entered
        if self.previous_search_term.lower() != search_term.lower():
            self.previous_search_term = search_term
            self.current_match_index = 0
            self.matches = []

            # Create a case-insensitive regular expression.
            regex = QRegularExpression(re.escape(search_term))
            regex.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)

            # Start at the beginning of the document.
            cursor = self.phelp.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)

            # Collect all matches.
            for _ in range(1000):  # arbitrarily large limit, better than while True, should always exit via break
                found = self.phelp.document().find(regex, cursor)  # type: ignore  #self.phelp.document() will never be None
                if found.isNull():
                    break
                self.matches.append(found)
                cursor.setPosition(found.selectionEnd())
        else:
            # For repeated searches with the same search_term, cycle to the next match
            if not self.matches:
                # No matches found, ensure all highlights and selections are cleared
                self.phelp.setExtraSelections([])
                tc = self.phelp.textCursor()
                tc.clearSelection()
                self.phelp.setTextCursor(tc)
                return
            self.current_match_index = (self.current_match_index + 1) % len(self.matches)

        extraSelections = []
        match_text = 'black'
        current_match_highlight = '#A6FF00'
        extra_matches_highlight = 'yellow'

        if self.matches:
            # Highlight all matches, the current match in current_match_highlight and all others in extra_matches_highlight
            for i, matchCursor in enumerate(self.matches):
                selection = QTextEdit.ExtraSelection()
                selection.cursor = matchCursor  # pyrefly: ignore[bad-assignment]
                fmt:QTextCharFormat = QTextCharFormat()
                fmt.setForeground(QColor(match_text))
                if i == self.current_match_index:
                    fmt.setBackground(QColor(current_match_highlight))
                else:
                    fmt.setBackground(QColor(extra_matches_highlight))
                if self.aw.app.darkmode:
                    fmt.setForeground(QColor('black'))
                selection.format = fmt # pyrefly: ignore[bad-assignment]
                extraSelections.append(selection)
            # Move the visible cursor to the current match and clear its active selection
            self.phelp.setTextCursor(self.matches[self.current_match_index])
            tc = self.phelp.textCursor()
            tc.clearSelection()
            self.phelp.setTextCursor(tc)
        else:
            # No matches found: ensure extra selections are cleared
            extraSelections = []
            self.phelp.setExtraSelections(extraSelections)
            # Also clear any active selection
            tc = self.phelp.textCursor()
            tc.clearSelection()
            self.phelp.setTextCursor(tc)
            return

        self.phelp.setExtraSelections(extraSelections)


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
                self.ports = [p for p in comports if (p[0] not in ['/dev/cu.Bluetooth-PDA-Sync', '/dev/cu.debug-console', '/dev/cu.wlan-debug',
                    '/dev/cu.Bluetooth-Modem','/dev/tty.Bluetooth-PDA-Sync','/dev/tty.Bluetooth-Modem',
                    '/dev/cu.Bluetooth-Incoming-Port', '/dev/tty.Bluetooth-Incoming-Port'
                    ])]
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

class ArtisanSliderLCDinputDlg(ArtisanDialog):

    def __init__(self, parent:QWidget, aw:'ApplicationWindow', value:int, value_min:int, value_max:int, title:Optional[str] = None) -> None:
        super().__init__(parent, aw)
        self.value:Optional[int] = None
        if title is None:
            title = ''
        self.setWindowTitle(title)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.accept)
        self.dialogbuttons.rejected.connect(self.reject)

        self.label = QLabel(title)

        self.valueEdit = QLineEdit(str(value))
        self.valueEdit.setFixedWidth(50)
        self.valueEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.valueEdit.setValidator(QIntValidator(value_min, value_max, self.valueEdit))
        self.valueEdit.selectAll()
        self.valueEdit.setFocus()

        valueLayout = QHBoxLayout()
        valueLayout.addStretch()
        valueLayout.addWidget(self.label)
        valueLayout.addWidget(self.valueEdit)
        valueLayout.addStretch()

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.dialogbuttons)

        mainLayout = QVBoxLayout()
        mainLayout.addStretch()
        mainLayout.addLayout(valueLayout)
        mainLayout.addStretch()
        mainLayout.addLayout(buttonsLayout)
        mainLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.setLayout(mainLayout)

    @pyqtSlot()
    def accept(self) -> None:
        self.value = int(self.valueEdit.text())
        super().accept()


##########################################################################
#####################  VIEW Tare  ########################################
##########################################################################


class tareDlg(ArtisanDialog):
    tare_updated_signal = pyqtSignal()  # signalled after tare data table got updated

    def __init__(self, parent:ArtisanDialog, aw:'ApplicationWindow', get_scale_weight: Callable[[], Optional[float]]) -> None:
        super().__init__(parent, aw)
        self.parent_dialog = parent
        self.get_scale_weight = get_scale_weight
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Containers'))

        self.taretable = QTableWidget()
        self.taretable.setTabKeyNavigation(True)
        self.createTareTable()

        self.taretable.itemSelectionChanged.connect(self.selectionChanged)

        addButton = QPushButton(QApplication.translate('Button','Add'))
        addButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.delButton = QPushButton(QApplication.translate('Button','Delete'))
        self.delButton.setDisabled(True)
        self.delButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        addButton.clicked.connect(self.addTare)
        self.delButton.clicked.connect(self.delTare)

        okButton = QPushButton(QApplication.translate('Button','OK'))
        cancelButton = QPushButton(QApplication.translate('Button','Cancel'))
        cancelButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        okButton.clicked.connect(self.accept)
        cancelButton.clicked.connect(self.reject)
        contentbuttonLayout = QHBoxLayout()
        contentbuttonLayout.addStretch()
        contentbuttonLayout.addWidget(addButton)
        contentbuttonLayout.addWidget(self.delButton)
        contentbuttonLayout.addStretch()

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(okButton)
        layout = QVBoxLayout()
        layout.addWidget(self.taretable)
        layout.addLayout(contentbuttonLayout)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)
        self.setMinimumWidth(230)
        self.setMinimumHeight(250)

    @pyqtSlot()
    def selectionChanged(self) -> None:
        if len(self.taretable.selectedRanges()) > 0:
            self.delButton.setDisabled(False)
        else:
            self.delButton.setDisabled(False)

    @pyqtSlot()
    def accept(self) -> None:
        self.saveTareTable()
        self.tare_updated_signal.emit()
        self.close()
        super().accept()

    # weight is always in g
    def setTableRow(self, row:int, name:str, weight:float) -> None:
        name_widget = QLineEdit()
        name_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
        name_widget.setText(name)
        weight_widget = ClickableQLineEdit()
        weight_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
        # NOTE: we support container weights up to 5kg (11,023lb)
        if self.aw.qmc.weight[2] == 'g':
            weight_widget.setText(str(int(round(weight))))
            weight_widget.setValidator(QIntValidator(0,9999, weight_widget))
        elif self.aw.qmc.weight[2] == 'Kg':
            w = convertWeight(weight,0,weight_units.index(self.aw.qmc.weight[2]))
            weight_widget.setText(f'{float2floatWeightVolume(w):g}')
            weight_widget.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, weight_widget)) # the max limit has to be high enough otherwise the connected signals are not send!

        else:
            w = convertWeight(weight,0,weight_units.index(self.aw.qmc.weight[2]))
            weight_widget.setText(f'{float2floatWeightVolume(w):g}')
            weight_widget.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, weight_widget))
        weight_widget.editingFinished.connect(self.weightEdited)
        self.taretable.setCellWidget(row, 0, name_widget)
        self.taretable.setCellWidget(row, 1, weight_widget)

    @pyqtSlot(bool)
    def addTare(self, _:bool = False) -> None:
        rows = self.taretable.rowCount()
        self.taretable.setRowCount(rows + 1)
        weight = self.get_scale_weight() # read value from scale in 'g' (or None)
        if weight is None or weight < 0:
            weight = 0
        #add widgets to the table
        self.setTableRow(rows, QApplication.translate('Label', 'container'), weight)

    @pyqtSlot(bool)
    def delTare(self, _:bool = False) -> None:
        selected = self.taretable.selectedRanges()
        if len(selected) > 0:
            bindex = selected[0].topRow()
            if bindex >= 0:
                self.taretable.removeRow(bindex)

    def saveTareTable(self) -> None:
        tars = self.taretable.rowCount()
        names:List[str] = []
        weights:List[float] = []
        for i in range(tars):
            nameWidget = cast(QLineEdit, self.taretable.cellWidget(i,0))
            name = nameWidget.text()
            weightWidget = cast(QLineEdit, self.taretable.cellWidget(i,1))
            weight:float = 0
            try:
                w = convertWeight(float(comma2dot(weightWidget.text())),weight_units.index(self.aw.qmc.weight[2]),0)
                weight = float2float(w) # stored in g as floats with one decimals
            except Exception: # pylint: disable=broad-except
                pass
            names.append(name)
            weights.append(weight)
        self.aw.qmc.container_names = names
        self.aw.qmc.container_weights = weights

    @pyqtSlot()
    def weightEdited(self) -> None:
        sender = self.sender()
        if sender and isinstance(sender, QLineEdit): # pyrefly: ignore[invalid-argument]
            text = sender.text().strip()
            if text == '':
                w:Optional[float] = self.get_scale_weight() # read value from scale in 'g'
                sender.setText(str(w if w is not None and w > 0 else 0))
            elif self.aw.qmc.weight[2] == 'Kg':
                # if container weight in kg, but input value > 10, we interpret it as in g
                w = float(comma2dot(text))
                if w > 10:
                    w = convertWeight(w,0,weight_units.index(self.aw.qmc.weight[2]))
                    sender.setText(f'{float2floatWeightVolume(w):g}')

    def createTareTable(self) -> None:
        self.taretable.clear()
        self.taretable.setRowCount(len(self.aw.qmc.container_names))
        self.taretable.setColumnCount(2)
        unit:str = self.aw.qmc.weight[2].lower()
        self.taretable.setHorizontalHeaderLabels([QApplication.translate('Table','Name'),
                                                         f"{QApplication.translate('Table','Weight')} ({unit})"])
        self.taretable.setAlternatingRowColors(True)
        self.taretable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.taretable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.taretable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.taretable.setShowGrid(True)
        vheader: Optional[QHeaderView] = self.taretable.verticalHeader()
        if vheader is not None:
            vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        for i, cn in enumerate(self.aw.qmc.container_names):
            #add widgets to the table
            self.setTableRow(i, cn, self.aw.qmc.container_weights[i])

        header: Optional[QHeaderView] = self.taretable.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.taretable.setColumnWidth(1,80)
