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

from PyQt5.QtCore import (Qt)
from PyQt5.QtWidgets import (QLabel, QComboBox, QDoubleSpinBox, QTableWidgetItem, QSizePolicy)
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
            return aw.qmc.stringtoseconds(a) < aw.qmc.stringtoseconds(b)
        else:
            try:
                # if those are numbers
                return int(a) < int(b)
            except:
                # else we do a string compare
                return a < b
      
class MyTableWidgetItemInt(QTableWidgetItem):
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
