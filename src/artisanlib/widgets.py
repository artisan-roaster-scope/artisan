#!/usr/bin/env python3

# ABOUT
# Artisan Dialogs

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2020

from artisanlib.util import stringtoseconds

from PyQt5.QtCore import (Qt, pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import (QLabel, QComboBox, QTextEdit, QDoubleSpinBox, QTableWidgetItem, QSizePolicy, QLCDNumber, QGroupBox)
from PyQt5.QtGui import QFontMetrics

class MyQComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super(MyQComboBox, self).__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)

    def wheelEvent(self, *args, **kwargs):
        if self.hasFocus():
            return QComboBox.wheelEvent(self, *args, **kwargs)

class MyQDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super(MyQDoubleSpinBox, self).__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, *args, **kwargs):
        if self.hasFocus():
            return QDoubleSpinBox.wheelEvent(self, *args, **kwargs)
            
    # we re-direct the mouse double-click event to the standard mouse press event and add
    # the (at least in PyQt 5.12.2/5.12.3) missing mouse release event
    # which had the effect that a double click an DoubleSpinBox arrow in the Cup Profile dialog
    # leads to a non-terminating sequence of setvalue() calls until the end of the spinner is reached.
    # Note: a triple click still has this effect
    def mouseDoubleClickEvent(self, event):
        super(MyQDoubleSpinBox, self).mouseReleaseEvent(event)
        super(MyQDoubleSpinBox, self).mouseDoubleClickEvent(event)
        super(MyQDoubleSpinBox, self).mouseReleaseEvent(event)

class MyTableWidgetItemQLineEdit(QTableWidgetItem):
    __slots__ = ['sortKey'] # save some memory by using slots
    def __init__(self, sortKey):
        #call custom constructor with UserType item type
        #QTableWidgetItem.__init__(self, "", QTableWidgetItem.UserType)
        super(QTableWidgetItem,self).__init__("", QTableWidgetItem.UserType)
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    def __lt__(self, other):
        a = self.sortKey.text()
        b = other.sortKey.text()
        if len(a) == 5 and len(b) == 5 and a[2] == ":" and b[2] == ":":
            # we compare times
            return stringtoseconds(a) < stringtoseconds(b)
        else:
            try:
                # if those are numbers
                return int(a) < int(b)
            except:
                # else we do a string compare
                return a < b

class MyTableWidgetItemQTime(QTableWidgetItem):
    __slots__ = ['sortKey'] # save some memory by using slots
    def __init__(self, sortKey):
        #call custom constructor with UserType item type
        #QTableWidgetItem.__init__(self, "", QTableWidgetItem.UserType)
        super(QTableWidgetItem,self).__init__("", QTableWidgetItem.UserType)
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    def __lt__(self, other):
        a = self.sortKey.time().minute() * 60 + self.sortKey.time().second()
        b = other.sortKey.time().minute() * 60 + other.sortKey.time().second()
        return a < b

class MyTableWidgetItemNumber(QTableWidgetItem):
    __slots__ = ['sortKey'] # save some memory by using slots
    def __init__(self, text, sortKey):
        super(QTableWidgetItem,self).__init__(text, QTableWidgetItem.UserType)
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    def __lt__(self, other):
        return self.sortKey < other.sortKey
  
class MyTableWidgetItemQCheckBox(QTableWidgetItem):
    __slots__ = ['sortKey'] # save some memory by using slots
    def __init__(self, sortKey):
        #call custom constructor with UserType item type
        super(QTableWidgetItem,self).__init__("", QTableWidgetItem.UserType)
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    def __lt__(self, other):
        return self.sortKey.isChecked() < other.sortKey.isChecked()
        
class MyTableWidgetItemQComboBox(QTableWidgetItem):
    __slots__ = ['sortKey'] # save some memory by using slots
    def __init__(self, sortKey):
        #call custom constructor with UserType item type
        super(QTableWidgetItem,self).__init__("", QTableWidgetItem.UserType)
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    def __lt__(self, other):
        return str(self.sortKey.currentText()) < str(other.sortKey.currentText())

# QLabel that automatically resizes its text font
class MyQLabel(QLabel):
    __slots__ = [] # save some memory by using slots
    def __init__(self, *args, **kargs):
        super(MyQLabel, self).__init__(*args, **kargs)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored))
        self.setMinSize(14)

    def setMinSize(self, minfs):
        f = self.font()
        f.setPixelSize(minfs)
        br = QFontMetrics(f).boundingRect(self.text())
        self.setMinimumSize(br.width(), br.height())

    def resizeEvent(self, event):
        super(MyQLabel, self).resizeEvent(event)
        if not self.text():
            return
        #--- fetch current parameters ----
        f = self.font()
        cr = self.contentsRect()
        #--- iterate to find the font size that fits the contentsRect ---
        dw = event.size().width() - event.oldSize().width()   # width change
        dh = event.size().height() - event.oldSize().height() # height change
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
            else: # label is shrinking
                if br.height() > cr.height() or br.width() > cr.width():
                    fs -= 1
                else:
                    break
            if fs < 1: break
        #--- update font size --- 
        self.setFont(f)


class ClickableQLabel(QLabel):
    clicked = pyqtSignal()
    left_clicked = pyqtSignal()
    right_clicked = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super(ClickableQLabel, self).__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        self.clicked.emit()
        if event.button() == Qt.LeftButton:
            self.left_clicked.emit()
        elif event.button() == Qt.RightButton:
            self.right_clicked.emit()

class ClickableQGroupBox(QGroupBox):
    clicked = pyqtSignal()
    left_clicked = pyqtSignal()
    right_clicked = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super(ClickableQGroupBox, self).__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        self.clicked.emit()
        if event.button() == Qt.LeftButton:
            self.left_clicked.emit()
        elif event.button() == Qt.RightButton:
            self.right_clicked.emit()

class MyQLCDNumber(QLCDNumber):
    clicked = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super(MyQLCDNumber, self).__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        self.clicked.emit()


# this one emits a clicked event on right-clicks and an editingFinished event when the text was changed and the focus got lost
class ClickableTextEdit(QTextEdit):
    clicked = pyqtSignal()
    editingFinished = pyqtSignal()
    receivedFocus = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super(ClickableTextEdit, self).__init__(*args, **kwargs)
        self._changed = False
        self.setTabChangesFocus(True)
        self.textChanged.connect(self._handle_text_changed)
        
    def mousePressEvent(self, event):
        super(ClickableTextEdit, self).mousePressEvent(event)
        if event.modifiers() == Qt.ControlModifier:
            self.clicked.emit()

    def focusInEvent(self, event):
        super(ClickableTextEdit, self).focusInEvent(event)
        self.receivedFocus.emit()

    def focusOutEvent(self, event):
        if self._changed:
            self.editingFinished.emit()
        super(ClickableTextEdit, self).focusOutEvent(event)

    @pyqtSlot()
    def _handle_text_changed(self):
        self._changed = True

    def setTextChanged(self, state=True):
        self._changed = state

    def setNewPlainText(self, text):
        QTextEdit.setPlainText(self, text)
        self._changed = False
