#
# ABOUT
# artisan scope dialogs
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
# Marko Luther, 2023

from contextlib import contextmanager
from collections.abc import Generator, Callable
from typing import override, Any, TYPE_CHECKING


if TYPE_CHECKING:
    from PyQt6.QtCore import QCoreApplication, QObject # pylint: disable=unused-import
    from PyQt6.QtGui import QWheelEvent, QMouseEvent, QFocusEvent, QResizeEvent, QKeyEvent # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget, QTimeEdit, QCheckBox, QComboBox, QCompleter # pylint: disable=unused-import
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import

from PyQt6.QtCore import (Qt, pyqtSignal, pyqtSlot, QLine, QEvent,
    QByteArray, QPropertyAnimation, QEasingCurve, QLocale)
from PyQt6.QtCore import pyqtProperty, QSize # Xtype: ignore[attr-defined]
from PyQt6.QtWidgets import (QApplication, QSplitter, QSplitterHandle, QLabel, QComboBox, QLineEdit, QTextEdit, QPlainTextEdit, QDoubleSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QSizePolicy, QLCDNumber, QGroupBox, QFrame, QSlider, QStyle, QStyleOptionSlider, QListView, QToolButton, QSpinBox,
    QTabWidget, QTabBar)
from PyQt6.QtGui import QPen, QPainter, QFontMetrics, QColor, QCursor, QEnterEvent, QPaintEvent, QIcon

from artisanlib.util import stringtoseconds, createGradient,getStyleIconPath
from artisanlib.styles import text_edit_style, artisan_minor_push_button_style



@contextmanager
def wait_cursor() -> Generator[None]:
    try:
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        yield
    finally:
        QApplication.restoreOverrideCursor()

# not used
#def adjust_combobox_width(combo: QComboBox) -> None:
#    fm = QFontMetrics(combo.font())
#    text_width = fm.horizontalAdvance(combo.currentText())
#    # Add padding for the arrow and borders
#    padding = 35
#    combo.setFixedWidth(text_width + padding)


def adjust_combobox_dropdown_width(combobox:QComboBox) -> None:
    # Find the maximum width needed for the items
    max_width = 0
    font_metrics = combobox.fontMetrics()

    for i in range(combobox.count()):
        item_text = combobox.itemText(i)
        # Add a small padding (e.g., 30px) for the scrollbar and text margins
        item_width = font_metrics.horizontalAdvance(item_text) + 30
        max_width = max(max_width, item_width)

    # Apply the width to the dropdown view container
    view = combobox.view()
    if view is not None:
        view.setMinimumWidth(max_width)

class MyQComboBox(QComboBox):
    def __init__(self, parent:'QWidget|None' = None, **kwargs:dict[Any,Any]) -> None:
        super().__init__(parent, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

    @override
    def wheelEvent(self, e:'QWheelEvent|None') -> None:
        if self.hasFocus():
            super().wheelEvent(e)

# coffee and blend ComboBox which toggles the weight unit on holding the ALT/OPTION modifier key on open
class StockComboBox(MyQComboBox):
    def __init__(self, parent:'QWidget|None', get_current_unit:Callable[[], int]|None = None, get_items:Callable[[int], list[str]]|None = None) -> None:
        super().__init__(parent)
        self.inverted:bool = False # is True if the weight units were inverted before
        self.get_current_unit:Callable[[], int]|None = get_current_unit
        self.get_items:Callable[[int], list[str]]|None = get_items

    def set_get_current_unit(self, f:Callable[[], int]) -> None:
        self.get_current_unit = f

    def set_get_items(self, f:Callable[[int], list[str]]) -> None:
        self.get_items = f

    def resetInverted(self) -> None:
        self.inverted = False

    @override
    def mousePressEvent(self, e:'QMouseEvent|None') -> None:
        modifier_pressed = QApplication.keyboardModifiers() == Qt.KeyboardModifier.AltModifier
        if self.get_current_unit is not None and self.get_items is not None and (modifier_pressed or self.inverted):
            # with ALT (Win) / OPTION (macOS) pressed we rewrite the popup menu indicating weights in imperial units if metric units were selected and vice versa
            default_unit:int = self.get_current_unit()
            unit:int = 0 # g
            if self.inverted and not modifier_pressed:
                # we revert to the original units
                unit = default_unit
            elif default_unit < 2:
                # if default unit is g or kg we convert to oz, otherwise to g
                unit = 3
            items = self.get_items(unit)
            for i in range(self.count()):
                if len(items) > i:
                    self.setItemText(i, items[i])
            self.inverted = not self.inverted
        super().mousePressEvent(e)


class RoastsComboBox(MyQComboBox):
    def __init__(self, parent:'QWidget') -> None:
        super().__init__(parent)
        self.installEventFilter(self)
        self.selection:str|None = None
        self.edited:str|None = None
        self.editTextChanged.connect(self.textEdited)
        self.setEditable(True)
        line_edit = self.lineEdit()
        if line_edit:
            line_edit.setClearButtonEnabled(True)
        completer: QCompleter|None = self.completer()
        if completer is not None:
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseSensitive)
#        self.setMouseTracking(False)
        self.recent_roasts_menu_list:Callable[[], list[str]]|None = None

    def init(self, recent_roasts_menu_list:Callable[[], list[str]], selection:str|None) -> None:
        self.setView(QListView())
        self.recent_roasts_menu_list = recent_roasts_menu_list
        self.selection = selection # just the roast title
        self.edited = selection
        self.updateMenu()

    @pyqtSlot(str)
    def textEdited(self, txt:str) -> None:
        cleaned = ' '.join(txt.split())
        self.edited = cleaned

    def getSelection(self) -> str|None:
        return self.edited or self.selection

    def setSelection(self, i:int) -> None:
        if i >= 0:
            try:
                self.edited = None # reset the user text editing
            except Exception: # pylint: disable=broad-except
                pass

    @override
    def eventFilter(self, a0:'QObject|None' = None, a1:QEvent|None = None) -> bool:
        del a0
# the next prevents correct setSelection on Windows
#        if a1.type() == QEvent.Type.FocusIn:
#            self.setSelection(self.currentIndex())
        if a1 is not None and a1.type() == QEvent.Type.MouseButtonPress:
            self.updateMenu()
#            return True # stops processing # popup not drawn if this line is added
#        return super().eventFilter(a0, a1) # this seems to slow down things on Windows and not necessary anyhow
        return False # cont processing

    # the first entry is always just the current text edit line
    def updateMenu(self) -> None:
        if self.recent_roasts_menu_list is not None:
            self.blockSignals(True)
            try:
    #            roasts = self.aw.recentRoastsMenuList()
                roasts = self.recent_roasts_menu_list()
                self.clear()
                if self.edited is None:
                    self.addItems(roasts)
                else:
                    self.addItems([self.edited] + roasts)
            except Exception: # pylint: disable=broad-except
                pass
            self.blockSignals(False)


class MyContentLimitedQComboBox(MyQComboBox): # pylint: disable=too-few-public-methods  # pyright: ignore [reportGeneralTypeIssues]# Argument to class must be a base class
    def __init__(self, parent:'QWidget|None' = None, **kwargs:dict[Any,Any]) -> None:
        super().__init__(parent, **kwargs)
        # setting max number visible limit
        self.setMaxVisibleItems(20)
        # ensure Qt style for this widget
        self.setStyleSheet('combobox-popup: 0;')
        # add scroll barspacer
        view = self.view()
        if view is not None:
            view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

# Spin box with mouse wheel / touch pad scrolling disabled
class MyQSpinBox(QSpinBox):
    def __init__(self, parent:'QWidget|None' = None, **kwargs:dict[str,Any]) -> None:
        super().__init__(parent, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setLocale(QLocale('C'))

    @override
    def wheelEvent(self, e:'QWheelEvent|None') -> None: # pylint: disable=no-self-use # used as slot
        del e

class MyQDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent:'QWidget|None' = None, **kwargs:dict[str,Any]) -> None:
        super().__init__(parent, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setLocale(QLocale('C'))

    @override
    def wheelEvent(self, e:'QWheelEvent|None') -> None:
        if self.hasFocus():
            super().wheelEvent(e)

    # we re-direct the mouse double-click event to the standard mouse press event and add
    # the (at least in PyQt 5.12.2/5.12.3) missing mouse release event
    # which had the effect that a double click an DoubleSpinBox arrow in the Cup Profile dialog
    # leads to a non-terminating sequence of setvalue() calls until the end of the spinner is reached.
    # Note: a triple click still has this effect
    @override
    def mouseDoubleClickEvent(self, a0:'QMouseEvent|None') -> None:
        super().mouseReleaseEvent(a0)
        super().mouseDoubleClickEvent(a0)
        super().mouseReleaseEvent(a0)



#class TabBarDescenderFixStyle(QProxyStyle):
#    def sizeFromContents(self, contents_type: QStyle.ContentsType,
#                         option: QStyleOption, size: QSize,
#                         widget: QWidget) -> QSize:
#
#        # Get the standard size calculated by the Fusion style
#        s = super().sizeFromContents(contents_type, option, size, widget)
#
#        # Check if the requested content type is a TabBar Tab
#        if contents_type == QStyle.ContentsType.CT_TabBarTab and widget:
#            fm = QFontMetrics(widget.font())
#            # Explicitly add the descent (and a safety buffer) to the height
#            s.setHeight(s.height() + fm.descent() + 2)
#
#        return s

# adds extra vertical spacing to avoid clipping of tab labels
class SpaciousTabBar(QTabBar):
    def __init__(self, parent:'QWidget|None' = None, **kwargs:dict[Any,Any]) -> None:
        super().__init__(parent, **kwargs)
        self.currentChanged.connect(self.handle_tab_change)

    def handle_tab_change(self, index:int) -> None:
        del index
        # Clears internal caches and tells the layout engine to poll hints again
        self.updateGeometry()

    @override
    def tabSizeHint(self, index: int) -> QSize:
        size = super().tabSizeHint(index)
        size.setHeight(size.height() + 5)  # Example padding adjustment
        return size

    @override
    def minimumTabSizeHint(self, index: int) -> QSize:
        return self.tabSizeHint(index)

# fixes clipping of decenders of tab labels in Fusion style by adding some vertical padding
class ArtisanQTabWidget(QTabWidget):
    def __init__(self, parent:'QWidget|None' = None, **kwargs:dict[Any,Any]) -> None:
        super().__init__(parent, **kwargs)
        app = QApplication.instance()
        if app is not None and app.style().name().lower() in {'fusion', 'windows', 'windowsvista'}: # type: ignore[attr-defined]
            # increase tab height to prevent vertical clipping of descenders observed on Windows/Fusion-style
            self.setTabBar(SpaciousTabBar())
# alternative fix, which alters tab height to font size + safety buffer (somewhat smaller than original design)
#            self.fix_style = TabBarDescenderFixStyle()
#            self.tabBar().setStyle(self.fix_style)


class MyQTableWidget(QTableWidget):
    def __init__(self, parent:'QWidget|None' = None, **kwargs:dict[Any,Any]) -> None:
        super().__init__(parent, **kwargs)
        self.installEventFilter(self)
        self.cursor_navigation:bool = True

    #keyboard presses. There must not be widgets (pushbuttons, comboboxes, etc) in focus in order to work
    @override
    def keyPressEvent(self, e: 'QKeyEvent|None') -> None:
        if e is not None and e.key() == Qt.Key.Key_Tab and self.cursor_navigation:
            self.cursor_navigation = False
            self.setCurrentCell(max(-1,self.currentRow()-1), 0)
        super().keyPressEvent(e)

    @override
    def eventFilter(self, object:'QObject|None', event:'QEvent|None') -> bool: # pylint: disable=redefined-builtin # noqa: A002 # Function argument `object` is shadowing a Python builtin
        # pylint: disable=c-extension-no-member
        try:
            if event is not None and event.type() == QEvent.Type.KeyPress:
                key = event.key()  # type:ignore[attr-defined] # "QEvent" has no attribute "key"
                if key == Qt.Key.Key_Left:
                    self.cursor_navigation = True
                    vheader = self.verticalHeader()
                    if vheader is not None:
                        vheader.setFocus()
                elif key == Qt.Key.Key_Right:
                    self.cursor_navigation = False
                    current_row = self.currentRow()
                    cellWidget = self.cellWidget(current_row,0)
                    if cellWidget is not None:
                        cellWidget.setFocus()
        except Exception: # pylint: disable=broad-except
            pass
        return super().eventFilter(object, event)



class MyTableWidgetItemQLineEdit(QTableWidgetItem):
    __slots__ = ['sortKey'] # save some memory by using slots
    def __init__(self, sortKey:QLineEdit) -> None:
        #call custom constructor with UserType item type
        super().__init__('', 1001) #QTableWidgetItem.ItemType.UserType)
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    @override
    def __lt__(self, other:'MyTableWidgetItemQLineEdit') -> bool: # type: ignore[override]
        a = self.sortKey.text()
        b = other.sortKey.text()
        try:
            if len(a) == 5 and len(b) == 5 and a[2] == ':' and b[2] == ':':
                # we compare times (not that stringtoseconds can still throw an exception on malformed input)
                return stringtoseconds(a) < stringtoseconds(b)
            # if those are numbers
            return int(a) < int(b)
        except Exception: # pylint: disable=broad-except
            # else we do a string compare
            return a < b

class MyTableWidgetItemQTime(QTableWidgetItem):
    __slots__ = ['sortKey'] # save some memory by using slots
    def __init__(self, sortKey:'QTimeEdit') -> None:
        #call custom constructor with UserType item type
        super().__init__('', 1002) #QTableWidgetItem.ItemType.UserType)
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    @override
    def __lt__(self, other:'MyTableWidgetItemQTime') -> bool: # type: ignore[override]
        a = self.sortKey.time().minute() * 60 + self.sortKey.time().second()
        b = other.sortKey.time().minute() * 60 + other.sortKey.time().second()
        return a < b

class MyTableWidgetItemNumber(QTableWidgetItem):
    __slots__ = ['sortKey'] # save some memory by using slots
    def __init__(self, text:str, sortKey:float) -> None:
        super().__init__(text, 1003) #QTableWidgetItem.ItemType.UserType)
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    @override
    def __lt__(self, other:'MyTableWidgetItemNumber') -> bool: # type: ignore[override]
        return self.sortKey < other.sortKey

class MyTableWidgetItemQCheckBox(QTableWidgetItem):
    __slots__ = ['sortKey'] # save some memory by using slots
    def __init__(self, sortKey:'QCheckBox') -> None:
        #call custom constructor with UserType item type
        super().__init__('', 1004) #QTableWidgetItem.ItemType.UserType)
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    @override
    def __lt__(self, other:'MyTableWidgetItemQCheckBox') -> bool:  # type: ignore[override]
        return self.sortKey.isChecked() < other.sortKey.isChecked()

class MyTableWidgetItemQComboBox(QTableWidgetItem):
    __slots__ = ['sortKey'] # save some memory by using slots
    def __init__(self, sortKey:'QComboBox') -> None:
        #call custom constructor with UserType item type
        super().__init__('', 1005) # QTableWidgetItem.ItemType.UserType)
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    @override
    def __lt__(self, other:'MyTableWidgetItemQComboBox') -> bool: # type: ignore[override]
        return str(self.sortKey.currentText()) < str(other.sortKey.currentText())


# Slider which does not move if slider widget is clicked, only if slider bar is clicked
class SliderUnclickable(QSlider):
    focus_in = pyqtSignal()
    focus_out = pyqtSignal()

    @override
    def keyPressEvent(self, ev:'QKeyEvent|None') -> None:
        if ev is not None and ev.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            return
        super().keyPressEvent(ev)

    @override
    def mousePressEvent(self, ev:'QMouseEvent|None') -> None:
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        slider_style:QStyle|None = self.style()
        if ev is not None and slider_style is not None:
            pressedControl = slider_style.hitTestComplexControl(QStyle.ComplexControl.CC_Slider, opt, ev.pos(), self)
            #if pressedControl in {QStyle.SubControl.SC_SliderGroove, QStyle.SubControl.SC_SliderHandle, QStyle.SubControl.SC_ScrollBarSubLine}:
            if pressedControl is not QStyle.SubControl.SC_None:
                super().mousePressEvent(ev)

    @override
    def focusInEvent(self, a0:'QFocusEvent|None') -> None:
        super().focusInEvent(a0)
        if a0 is not None:
            self.focus_in.emit()

    @override
    def focusOutEvent(self, a0:'QFocusEvent|None') -> None:
        super().focusOutEvent(a0)
        if a0 is not None:
            self.focus_out.emit()


# QLabel that automatically resizes its text font
class MyQLabel(QLabel):
    def __init__(self, text: str|None = None, parent: 'QWidget|None' = None, flags: Qt.WindowType = Qt.WindowType.Widget) -> None:
        super().__init__(text, parent, flags)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Ignored))
        self.setMinSize(14)

    def setMinSize(self, minfs:int) -> None:
        f = self.font()
        f.setPixelSize(minfs)
        br = QFontMetrics(f).boundingRect(self.text())
        self.setMinimumSize(br.width(), br.height())

    @override
    def resizeEvent(self, a0:'QResizeEvent|None') -> None:
        super().resizeEvent(a0)
        if a0 is not None:
            if not self.text():
                return
            #--- fetch current parameters ----
            f = self.font()
            cr = self.contentsRect()
            #--- iterate to find the font size that fits the contentsRect ---
            dw = a0.size().width() - a0.oldSize().width()   # width change
            dh = a0.size().height() - a0.oldSize().height() # height change
            fs = max(f.pixelSize(), 1)
            while True:
                f.setPixelSize(fs)
                br =  QFontMetrics(f).boundingRect(self.text())
                if dw >= 0 and dh >= 0: # label is expanding
                    if br.height() <= cr.height() and br.width() <= cr.width():
                        fs += 1
                    else:
                        f.setPixelSize(max(fs - 1, 1)) # backtrack
                        break
                # label is shrinking
                elif br.height() > cr.height() or br.width() > cr.width():
                    fs -= 1
                else:
                    break
                if fs < 1:
                    break
            #--- update font size ---
            self.setFont(f)

# wider border than styles.py:line_edit_style (used in login/roest-setup dialogs)
class StyledQLineEdit(QLineEdit):
    def __init__(self, parent: 'QWidget|None' = None) -> None:
        super().__init__(parent)
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
        self.setStyleSheet(lineEditstyle)

class ClickableQLabel(QLabel):
    clicked = pyqtSignal()
    left_clicked = pyqtSignal()
    right_clicked = pyqtSignal()

    @override
    def mousePressEvent(self, ev:'QMouseEvent|None') -> None:
        super().mousePressEvent(ev)
        if ev is not None:
            self.clicked.emit()
            if ev.button() == Qt.MouseButton.LeftButton:
                self.left_clicked.emit()
            elif ev.button() == Qt.MouseButton.RightButton:
                self.right_clicked.emit()

class ClickableQGroupBox(QGroupBox):
    clicked = pyqtSignal()
    left_clicked = pyqtSignal()
    right_clicked = pyqtSignal()

    @override
    def mousePressEvent(self, event:'QMouseEvent|None') -> None:
        super().mousePressEvent(event)
        if event is not None:
            self.clicked.emit()
            if event.button() == Qt.MouseButton.LeftButton:
                self.left_clicked.emit()
            elif event.button() == Qt.MouseButton.RightButton:
                self.right_clicked.emit()

class MyQLCDNumber(QLCDNumber):
    clicked = pyqtSignal()
    left_clicked = pyqtSignal()
    right_clicked = pyqtSignal()
    double_clicked = pyqtSignal()

    @override
    def mousePressEvent(self, a0:'QMouseEvent|None') -> None:
        super().mousePressEvent(a0)
        if a0 is not None:
            self.clicked.emit()
            if a0.button() == Qt.MouseButton.LeftButton:
                self.left_clicked.emit()
            elif a0.button() == Qt.MouseButton.RightButton:
                self.right_clicked.emit()

    @override
    def mouseDoubleClickEvent(self, a0:'QMouseEvent|None') -> None:
        super().mousePressEvent(a0)
        if a0 is not None:
            self.double_clicked.emit()

class ClickableLCDFrame(QFrame):
    clicked = pyqtSignal()
    left_clicked = pyqtSignal()
    right_clicked = pyqtSignal()

    @override
    def mousePressEvent(self, a0:'QMouseEvent|None') -> None:
        super().mousePressEvent(a0)
        if a0 is not None:
            self.clicked.emit()
            if a0.button() == Qt.MouseButton.LeftButton:
                self.left_clicked.emit()
            elif a0.button() == Qt.MouseButton.RightButton:
                self.right_clicked.emit()


class ArtisanTextEdit(QTextEdit):
    def __init__(self, darkmode:bool = False, parent:'QWidget|None' = None, **kwargs:dict[Any,Any]) -> None:
        super().__init__(parent, **kwargs)
        self.update_style(darkmode)

    def update_style(self,
            darkmode:bool,
            background_color: str|None = None,
            selection_background_color: str|None = None,
            border_color: str|None = None,
            color: str|None = None) -> None:
        self.setStyleSheet(text_edit_style(darkmode, background_color, selection_background_color, border_color, color))


class ArtisanPlainTextEdit(QPlainTextEdit):
    def __init__(self, darkmode:bool = False, parent:'QWidget|None' = None, **kwargs:dict[Any,Any]) -> None:
        super().__init__(parent, **kwargs)
        self.update_style(darkmode)

    def update_style(self,
            darkmode:bool,
            background_color: str|None = None,
            selection_background_color: str|None = None,
            border_color: str|None = None,
            color: str|None = None) -> None:
        self.setStyleSheet(text_edit_style(darkmode, background_color, selection_background_color, border_color, color))

# this one emits a clicked event on right-clicks and an editingFinished event when the text was changed and the focus got lost
class ClickableTextEdit(ArtisanPlainTextEdit):
    clicked = pyqtSignal()
    editingFinished = pyqtSignal()
    receivedFocus = pyqtSignal()

    def __init__(self, darkmode:bool = False, parent:'QWidget|None' = None, **kwargs:dict[str,Any]) -> None:
        super().__init__(darkmode, parent, **kwargs)
        self._changed = False
        self.setTabChangesFocus(True)
        self.textChanged.connect(self._handle_text_changed)

    @override
    def mousePressEvent(self, e:'QMouseEvent|None') -> None:
        super().mousePressEvent(e)
        if e is not None and e.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.clicked.emit()

    @override
    def focusInEvent(self, e:'QFocusEvent|None') -> None:
        super().focusInEvent(e)
        if e is not None:
            self.receivedFocus.emit()

    @override
    def focusOutEvent(self, e:'QFocusEvent|None') -> None:
        if e is not None and self._changed:
            self.editingFinished.emit()
        super().focusOutEvent(e)

    @pyqtSlot()
    def _handle_text_changed(self) -> None:
        self._changed = True

    def setTextChanged(self, state:bool = True) -> None:
        self._changed = state

    def setNewPlainText(self, text:str) -> None:
        self.setPlainText(text)
        self._changed = False

# this one emits a clicked event on right-clicks and an editingFinished event when the text was changed and the focus got lost
class ClickableQLineEdit(QLineEdit):
    clicked = pyqtSignal()
    editingFinished = pyqtSignal()
    receivedFocus = pyqtSignal()

    def __init__(self, parent:'QWidget|None' = None, **kwargs:dict[str,Any]) -> None:
        super().__init__(parent, **kwargs)
        self._changed = False
        self.textChanged.connect(self._handle_text_changed)

    @override
    def mousePressEvent(self, a0:'QMouseEvent|None') -> None:
        super().mousePressEvent(a0)
        if a0 is not None and a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.clicked.emit()

    @override
    def focusInEvent(self, a0:'QFocusEvent|None') -> None:
        super().focusInEvent(a0)
        if a0 is not None:
            self.receivedFocus.emit()

    @override
    def focusOutEvent(self, a0:'QFocusEvent|None') -> None:
        if a0 is not None and self._changed:
            self.editingFinished.emit()
        super().focusOutEvent(a0)

    @pyqtSlot()
    def _handle_text_changed(self) -> None:
        self._changed = True

    def setTextChanged(self, state:bool = True) -> None:
        self._changed = state

    def setNewText(self, text:str) -> None:
        QLineEdit.setText(self, text)
        self._changed = False


# Event Buttons

class ArtisanMinorPushButton(QPushButton):
    def __init__(self, text:str, light_icon:str|None = None, dark_icon:str|None = None, dark:bool = False, parent:'QWidget|None' = None) -> None:
        super().__init__(text, parent)
        self.setStyleSheet(artisan_minor_push_button_style(dark))
        if dark_icon is None:
            dark_icon = light_icon
        if dark and dark_icon is not None:
            self.setIconSize(QSize(14,14))
            self.setIcon(QIcon(getStyleIconPath(dark_icon)))
        elif light_icon is not None:
            self.setIconSize(QSize(14,14))
            self.setIcon(QIcon(getStyleIconPath(light_icon)))
        self.setMaximumSize(self.sizeHint())
        self.setMinimumSize(self.minimumSizeHint())

# selector is a stylesheet property selector like "[Selected=true]"
# state is a stylesheet pseudo state restriction like ":!pressed:hover"
# color and background are valid color string like "#e687a8", "white" or
#   "QLinearGradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2b88ba, stop: 1 #126ea1)"
# font_size is an integer interpreted in pt
def pushButtonColorStyle(
        class_name: str,
        selector: str='',
        state: str='',
        color:str|None = None,
        background:str|None = None,
        font_size:int|None = None) -> str:
    color = ('' if color is None else f'color:{color};')
    background = ('' if background is None else f'background-color:{background};')
    font_size_str = ('' if font_size is None else f'font-size:{font_size}pt;')
    return f'{class_name}{selector}{state}{{{color}{background}{font_size_str}}}'

class EventPushButton(QPushButton):
    def __init__(self, text:str, parent:'QWidget|None' = None, background_color:str = '#777777') -> None:
        super().__init__(text, parent)
        self.default_background_color = background_color
        self.default_style = pushButtonColorStyle('*',
            selector='[Selected=false]',
            state=':!flat:!hover:!pressed',
            background=createGradient(background_color))
        self.setStyleSheet(self.default_style)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setProperty('Selected', False)

    def setSelected(self, b:bool) -> None:
        self.setProperty('Selected', b)
        # Update the style
#        self.setStyle(self.style()) # this seems not to work any longer to update selected style of buttons in Qt 6.9.2
        self.setStyleSheet(self.styleSheet()) # this works in Qt 6.9.2 to update the selected style of buttons


class MajorEventPushButton(EventPushButton): # pylint: disable=too-few-public-methods
    def __init__(self, text:str, parent:'QWidget|None' = None, background_color:str = '#147bb3') -> None:
        super().__init__(text, parent, background_color)


class AnimatedMajorEventPushButton(MajorEventPushButton):
    def __init__(self, text:str, parent:'QWidget|None' = None, background_color:str = '#147bb3') -> None:
        super().__init__(text, parent, background_color)

        # we make the dark animation color slightly darker than the background:
        anim_dark_color = QColor(background_color).lighter(80)
        # and the lighter
        anim_light_color = QColor(anim_dark_color).lighter(180)
        # we reduce the staturation slightly:
        anim_light_color = QColor.fromHsv(
            anim_light_color.hslHue(),
            max(0,anim_light_color.saturation()-80),
            anim_light_color.value(),
            anim_light_color.alpha())

        selected_anim_dark_color = QColor('#d4336a').lighter(80)
        selected_anim_light_color = QColor('#d4336a').lighter(120)
        # we reduce the staturation slightly:
        selected_anim_light_color = QColor.fromHsv(
            selected_anim_light_color.hslHue(),
            max(0,selected_anim_light_color.saturation()-70),
            selected_anim_light_color.value(),
            selected_anim_light_color.alpha())

        byar = QByteArray()
        byar.append(b'zcolor')

        self.animating = False

        self.animation = QPropertyAnimation(self, byar)
        self.animation.setStartValue(anim_dark_color)
        self.animation.setKeyValueAt(0.2, anim_dark_color)
        self.animation.setKeyValueAt(0.55, anim_light_color)
        self.animation.setKeyValueAt(0.8, anim_dark_color)
        self.animation.setEndValue(anim_dark_color)
        self.animation.setDuration(1200)
        self.animation.setLoopCount(-1)
        self.animation.setEasingCurve(QEasingCurve.Type.OutInCubic)

        self.selected_animation = QPropertyAnimation(self, byar)
        self.selected_animation.setStartValue(selected_anim_dark_color)
        self.selected_animation.setKeyValueAt(0.2, selected_anim_dark_color)
        self.selected_animation.setKeyValueAt(0.55, selected_anim_light_color)
        self.selected_animation.setKeyValueAt(0.8, selected_anim_dark_color)
        self.selected_animation.setEndValue(selected_anim_dark_color)
        self.selected_animation.setDuration(1200)
        self.selected_animation.setLoopCount(-1)
        self.selected_animation.setEasingCurve(QEasingCurve.Type.OutInCubic)


    @override
    def setSelected(self, b:bool) -> None:
        super().setSelected(b)
        if self.animating:
            # we stop the running animation and restart it to adjust to the changed selected state
            self.stopAnimation()
            self.startAnimation()

    def startAnimation(self) -> None:
        if self.property('Selected'):
            self.selected_animation.start()
        else:
            self.animation.start()
        self.animating = True

    def stopAnimation(self) -> None:
        self.animation.stop()
        self.selected_animation.stop()
        self.setStyleSheet(self.styleSheet())
        self.animating = False

    # pylint: disable=no-self-use
    def getBackColor(self) -> QColor:
        return QColor()

    def setBackColor(self, color:QColor) -> None:
        self.setStyleSheet(f'QPushButton:!flat:!pressed{{background-color:{color.name()};}}')

    zcolor = pyqtProperty(QColor, getBackColor, setBackColor)

class MinorEventPushButton(EventPushButton): # pylint: disable=too-few-public-methods
    def __init__(self, text:str, parent:'QWidget|None' = None, background_color:str = '#4c97c3') -> None:
        super().__init__(text, parent, background_color)

class AuxEventPushButton(EventPushButton): # pylint: disable=too-few-public-methods
    def __init__(self, text:str, parent:'QWidget|None' = None, background_color:str = '#bdbdbd') -> None:
        super().__init__(text, parent, background_color)



###

# only vertical mode supported by SplitterHandler for now
class SplitterHandle(QSplitterHandle):

    def __init__(self, *args:Any, **kwargs:Any) -> None:
        super().__init__(*args, **kwargs)
        self.pen_color_normal = QColor(150, 150, 150)
        self.pen_color_hover_lightmode = QColor(110, 110, 110)
        self.pen_color_hover_darkmode = QColor(190, 190, 190)
        self.pen_color = self.pen_color_normal

    @override
    def enterEvent(self, event:QEnterEvent|None) -> None:
        if event is not None:
            app:QCoreApplication|None = QApplication.instance()
            if app is not None and app.darkmode: # type: ignore[attr-defined]
                self.pen_color = self.pen_color_hover_darkmode
            else:
                self.pen_color = self.pen_color_hover_lightmode
            self.repaint()

    @override
    def leaveEvent(self, a0:QEvent|None) -> None:
        if a0 is not None:
            self.pen_color = self.pen_color_normal
            self.repaint()

    @override
    def paintEvent(self, a0:QPaintEvent|None) -> None:
        super().paintEvent(a0)
        painter = QPainter(self)
        pen = QPen()
        pen.setColor(self.pen_color)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setRenderHint(painter.RenderHint.Antialiasing)

        h = self.height()
        hh = int(round(h/2))
        ww = int(round(self.width()/2))

        x0 = ww - h
        x1 = ww + h

        painter.drawLines(
            QLine(x0, hh + 2, x1, hh + 2),
            QLine(x0, hh - 2, x1, hh - 2))


# only vertical mode supported by SplitterHandler for now
class Splitter(QSplitter):
    def __init__(self, *args:Any, **kwargs:Any):
        super().__init__(*args, *kwargs)
        self.setHandleWidth(10)

    @override
    def createHandle(self) -> QSplitterHandle:
        return SplitterHandle(self.orientation(), self)


class FixedRatio2ToolButton(QToolButton):
    def __init__(self, parent:'QWidget|None' = None) -> None:
        super().__init__(parent)
        # Set a policy that allows expansion, then enable height-for-width
        policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    # pylint: disable=no-self-use
    @override
    def hasHeightForWidth(self) -> bool:
        return True

    # pylint: disable=no-self-use
    @override
    def heightForWidth(self, a0: int) -> int:
        # 2:1 ratio
        return int(round(a0/2))

    # Ensure the default size hint also respects the aspect ratio
    @override
    def sizeHint(self) -> QSize:
        hint = super().sizeHint()
        # Maintain aspect ratio based on the default width hint
        hint.setHeight(self.heightForWidth(hint.width()))
        return hint
