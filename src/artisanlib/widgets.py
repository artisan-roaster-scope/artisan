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

from contextlib import contextmanager
from collections.abc import Iterator
from typing import override, Any, TYPE_CHECKING

from artisanlib.util import stringtoseconds, createGradient

if TYPE_CHECKING:
    from PyQt6.QtCore import QCoreApplication, QObject # pylint: disable=unused-import
    from PyQt6.QtGui import QWheelEvent, QMouseEvent, QFocusEvent, QResizeEvent, QKeyEvent # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget, QTimeEdit, QCheckBox, QComboBox # pylint: disable=unused-import

from PyQt6.QtCore import (Qt, pyqtSignal, pyqtSlot, QLine, QEvent,
    QByteArray, QPropertyAnimation, QEasingCurve, QLocale)
from PyQt6.QtCore import pyqtProperty # type:ignore[attr-defined]
from PyQt6.QtWidgets import (QApplication, QSplitter, QSplitterHandle, QLabel, QComboBox, QLineEdit, QTextEdit, QDoubleSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QSizePolicy, QLCDNumber, QGroupBox, QFrame, QSlider, QStyle, QStyleOptionSlider)
from PyQt6.QtGui import QPen, QPainter, QFontMetrics, QColor, QCursor, QEnterEvent, QPaintEvent


@contextmanager
def wait_cursor() -> Iterator[None]:
    try:
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        yield
    finally:
        QApplication.restoreOverrideCursor()

class MyQComboBox(QComboBox):
    def __init__(self, parent:'QWidget|None' = None, **kwargs:dict[Any,Any]) -> None:
        super().__init__(parent, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

    @override
    def wheelEvent(self, e:'QWheelEvent|None') -> None:
        if self.hasFocus():
            super().wheelEvent(e)

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
    def __lt__(self, other:'MyTableWidgetItemQLineEdit') -> bool: # type: ignore[override] # ty:ignore[unused]
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
    def __lt__(self, other:'MyTableWidgetItemQTime') -> bool: # type: ignore[override] # ty:ignore[unused]
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
    def __lt__(self, other:'MyTableWidgetItemNumber') -> bool: # type: ignore[override] # ty:ignore[unused]
        return self.sortKey < other.sortKey

class MyTableWidgetItemQCheckBox(QTableWidgetItem):
    __slots__ = ['sortKey'] # save some memory by using slots
    def __init__(self, sortKey:'QCheckBox') -> None:
        #call custom constructor with UserType item type
        super().__init__('', 1004) #QTableWidgetItem.ItemType.UserType)
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    @override
    def __lt__(self, other:'MyTableWidgetItemQCheckBox') -> bool:  # type: ignore[override] # ty:ignore[unused]
        return self.sortKey.isChecked() < other.sortKey.isChecked()

class MyTableWidgetItemQComboBox(QTableWidgetItem):
    __slots__ = ['sortKey'] # save some memory by using slots
    def __init__(self, sortKey:'QComboBox') -> None:
        #call custom constructor with UserType item type
        super().__init__('', 1005) # QTableWidgetItem.ItemType.UserType)
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    @override
    def __lt__(self, other:'MyTableWidgetItemQComboBox') -> bool: # type: ignore[override] # ty:ignore[unused]
        return str(self.sortKey.currentText()) < str(other.sortKey.currentText())


# Slider which does not move if slider widget is clicked, only if slider bar is clicked
class SliderUnclickable(QSlider):
    focus_in = pyqtSignal()
    focus_out = pyqtSignal()

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


# this one emits a clicked event on right-clicks and an editingFinished event when the text was changed and the focus got lost
class ClickableTextEdit(QTextEdit):
    clicked = pyqtSignal()
    editingFinished = pyqtSignal()
    receivedFocus = pyqtSignal()

    def __init__(self, parent:'QWidget|None' = None, **kwargs:dict[str,Any]) -> None:
        super().__init__(parent, **kwargs)
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
        QTextEdit.setPlainText(self, text)
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
            if app is not None and app.darkmode: # type:ignore[attr-defined]
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
