"""
Check Combo Box
---------------
A QComboBox subclass designed for multiple item selection.
The combo box popup allows the user to check/uncheck multiple items at
once.
"""

# by Aleš Erjavec
# downloaded from https://gist.github.com/ales-erjavec/7624dd1d183dfbfb3354600b285abb94

import sys

from PyQt5.QtCore import Qt, QEvent, QRect, QTimer, pyqtSignal

from PyQt5.QtGui import (
    QPalette, QFontMetrics, QBrush, QColor, QPixmap, QIcon
)
from PyQt5.QtWidgets import (
    QComboBox, QAbstractItemView, QAbstractItemDelegate, QStyledItemDelegate,
    QApplication, QStyle, QStyleOption, QStyleOptionComboBox,
    QStyleOptionMenuItem, QStyleOptionViewItem, QStylePainter
)


class CheckComboBox(QComboBox):
    """
    A QComboBox allowing multiple item selection.
    """
    
    flagChanged=pyqtSignal(int,bool)
    

    class ComboItemDelegate(QStyledItemDelegate):
        """
        Helper styled delegate (mostly based on existing private Qt's
        delegate used by the QComboBox). Used to style the popup like a
        list view (e.g windows style).
        """
        def isSeparator(self, index):
            return str(index.data(Qt.AccessibleDescriptionRole)) == "separator"

        def paint(self, painter, option, index):
            if option.widget is not None:
                style = option.widget.style()
            else:
                style = QApplication.style()

            option = QStyleOptionViewItem(option)
            option.showDecorationSelected = True

            # option.state &= ~QStyle.State_HasFocus & ~QStyle.State_MouseOver
            if self.isSeparator(index):
                opt = QStyleOption()
                opt.rect = QRect(option.rect)
                if isinstance(option.widget, QAbstractItemView):
                    opt.rect.setWidth(option.widget.viewport().width())
                style.drawPrimitive(QStyle.PE_IndicatorToolBarSeparator,
                                    opt, painter, option.widget)
            else:
                super(CheckComboBox.ComboItemDelegate, self).paint(painter, option, index)

    class ComboMenuDelegate(QAbstractItemDelegate):
        """
        Helper styled delegate (mostly based on existing private Qt's
        delegate used by the QComboBox). Used to style the popup like a
        menu. (e.g osx aqua style).
        """
        def isSeparator(self, index):
            return str(index.data(Qt.AccessibleDescriptionRole)) == "separator"

        def paint(self, painter, option, index):
            menuopt = self._getMenuStyleOption(option, index)
            if option.widget is not None:
                style = option.widget.style()
            else:
                style = QApplication.style()
            style.drawControl(QStyle.CE_MenuItem, menuopt, painter,
                              option.widget)

        def sizeHint(self, option, index):
            menuopt = self._getMenuStyleOption(option, index)
            if option.widget is not None:
                style = option.widget.style()
            else:
                style = QApplication.style()
            return style.sizeFromContents(
                QStyle.CT_MenuItem, menuopt, menuopt.rect.size(),
                option.widget
            )

        def _getMenuStyleOption(self, option, index):
            menuoption = QStyleOptionMenuItem()
            palette = option.palette.resolve(QApplication.palette("QMenu"))
            foreground = index.data(Qt.ForegroundRole)
            if isinstance(foreground, (QBrush, QColor, QPixmap)):
                foreground = QBrush(foreground)
                palette.setBrush(QPalette.Text, foreground)
                palette.setBrush(QPalette.ButtonText, foreground)
                palette.setBrush(QPalette.WindowText, foreground)

            background = index.data(Qt.BackgroundRole)
            if isinstance(background, (QBrush, QColor, QPixmap)):
                background = QBrush(background)
                palette.setBrush(QPalette.Background, background)

            menuoption.palette = palette

            decoration = index.data(Qt.DecorationRole)
            if isinstance(decoration, QIcon):
                menuoption.icon = decoration

            if self.isSeparator(index):
                menuoption.menuItemType = QStyleOptionMenuItem.Separator
            else:
                menuoption.menuItemType = QStyleOptionMenuItem.Normal

            if index.flags() & Qt.ItemIsUserCheckable:
                menuoption.checkType = QStyleOptionMenuItem.NonExclusive
            else:
                menuoption.checkType = QStyleOptionMenuItem.NotCheckable

            check = index.data(Qt.CheckStateRole)
            menuoption.checked = check == Qt.Checked

            if option.widget is not None:
                menuoption.font = option.widget.font()
            else:
                menuoption.font = QApplication.font("QMenu")

            menuoption.maxIconWidth = option.decorationSize.width() + 4
            menuoption.rect = option.rect
            menuoption.menuRect = option.rect

            menuoption.menuHasCheckableItems = True
            menuoption.tabWidth = 0
            # TODO: self.displayText(QVariant, QLocale)
            # TODO: Why is this not a QStyledItemDelegate?
            display = index.data(Qt.DisplayRole)
            if isinstance(display, str):
                menuoption.text = display
            else:
                menuoption.text = str(display)

            menuoption.fontMetrics = QFontMetrics(menuoption.font)
            state = option.state & (QStyle.State_MouseOver |
                                    QStyle.State_Selected |
                                    QStyle.State_Active)

            if index.flags() & Qt.ItemIsEnabled:
                state = state | QStyle.State_Enabled
                menuoption.palette.setCurrentColorGroup(QPalette.Active)
            else:
                state = state & ~QStyle.State_Enabled
                menuoption.palette.setCurrentColorGroup(QPalette.Disabled)

            if menuoption.checked:
                state = state | QStyle.State_On
            else:
                state = state | QStyle.State_Off

            menuoption.state = state
            return menuoption

    def __init__(self, parent=None, placeholderText="", separator=", ",
                 **kwargs):
        super(CheckComboBox, self).__init__(parent, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)

        self.__popupIsShown = False
        self.__supressPopupHide = False
        self.__blockMouseReleaseTimer = QTimer(self, singleShot=True)
        self.__initialMousePos = None
        self.__separator = separator
        self.__placeholderText = placeholderText
        self.__updateItemDelegate()

    def mousePressEvent(self, event):
        """Reimplemented."""
        self.__popupIsShown = False
        super(CheckComboBox, self).mousePressEvent(event)
        if self.__popupIsShown:
            self.__initialMousePos = self.mapToGlobal(event.pos())
            self.__blockMouseReleaseTimer.start(
                QApplication.doubleClickInterval())

    def changeEvent(self, event):
        """Reimplemented."""
        if event.type() == QEvent.StyleChange:
            self.__updateItemDelegate()
        super(CheckComboBox, self).changeEvent(event)

    def showPopup(self):
        """Reimplemented."""
        super(CheckComboBox, self).showPopup()
        view = self.view()
        view.installEventFilter(self)
        view.viewport().installEventFilter(self)
        self.__popupIsShown = True

    def hidePopup(self):
        """Reimplemented."""
        self.view().removeEventFilter(self)
        self.view().viewport().removeEventFilter(self)
        self.__popupIsShown = False
        self.__initialMousePos = None
        super(CheckComboBox, self).hidePopup()
        self.view().clearFocus()

    def eventFilter(self, obj, event):
        """Reimplemented."""
        if self.__popupIsShown and \
                event.type() == QEvent.MouseMove and \
                self.view().isVisible() and self.__initialMousePos is not None:
            diff = obj.mapToGlobal(event.pos()) - self.__initialMousePos
            if diff.manhattanLength() > 9 and \
                    self.__blockMouseReleaseTimer.isActive():
                self.__blockMouseReleaseTimer.stop()
            # pass through

        if self.__popupIsShown and \
                event.type() == QEvent.MouseButtonRelease and \
                self.view().isVisible() and \
                self.view().rect().contains(event.pos()) and \
                self.view().currentIndex().isValid() and \
                self.view().currentIndex().flags() & Qt.ItemIsSelectable and \
                self.view().currentIndex().flags() & Qt.ItemIsEnabled and \
                self.view().currentIndex().flags() & Qt.ItemIsUserCheckable and \
                self.view().visualRect(self.view().currentIndex()).contains(event.pos()) and \
                not self.__blockMouseReleaseTimer.isActive():
            model = self.model()
            index = self.view().currentIndex()
            state = model.data(index, Qt.CheckStateRole)
            model.setData(index,
                          Qt.Checked if state == Qt.Unchecked else Qt.Unchecked,
                          Qt.CheckStateRole)
            self.view().update(index)
            self.update()
            self.flagChanged.emit(index.row(),state == Qt.Unchecked)
            return True

        if self.__popupIsShown and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Space:
                # toogle the current items check state
                model = self.model()
                index = self.view().currentIndex()
                flags = model.flags(index)
                state = model.data(index, Qt.CheckStateRole)
                if flags & Qt.ItemIsUserCheckable and \
                        flags & Qt.ItemIsTristate:
                    state = Qt.CheckState((int(state) + 1) % 3)
                elif flags & Qt.ItemIsUserCheckable:
                    state = Qt.Checked if state != Qt.Checked else Qt.Unchecked
                model.setData(index, state, Qt.CheckStateRole)
                self.view().update(index)
                self.update()
                self.flagChanged.emit(index.row(),state != Qt.Unchecked)
                return True
            # TODO: handle Qt.Key_Enter, Key_Return?

        return super(CheckComboBox, self).eventFilter(obj, event)

    def paintEvent(self, event):
        """Reimplemented."""
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        painter.drawComplexControl(QStyle.CC_ComboBox, option)
        # draw the icon and text
        checked = self.checkedIndices()
        if checked:
            items = [self.itemText(i) for i in checked]
            option.currentText = self.__separator.join(items)
        else:
            option.currentText = self.__placeholderText
            option.palette.setCurrentColorGroup(QPalette.Disabled)

        option.currentIcon = QIcon()
        painter.drawControl(QStyle.CE_ComboBoxLabel, option)

    def itemCheckState(self, index):
        """
        Return the check state for item at `index`
        Parameters
        ----------
        index : int
        Returns
        -------
        state : Qt.CheckState
        """
        state = self.itemData(index, role=Qt.CheckStateRole)
        if isinstance(state, int):
            return Qt.CheckState(state)
        else:
            return Qt.Unchecked

    def setItemCheckState(self, index, state):
        """
        Set the check state for item at `index` to `state`.
        Parameters
        ----------
        index : int
        state : Qt.CheckState
        """
        self.setItemData(index, state, Qt.CheckStateRole)

    def checkedIndices(self):
        """
        Return a list of indices of all checked items.
        Returns
        -------
        indices : List[int]
        """
        return [i for i in range(self.count())
                if self.itemCheckState(i) == Qt.Checked]

    def setPlaceholderText(self, text):
        """
        Set the placeholder text.
        This text is displayed on the checkbox when there are no checked
        items.
        Parameters
        ----------
        text : str
        """
        if self.__placeholderText != text:
            self.__placeholderText = text
            self.update()

    def placeholderText(self):
        """
        Return the placeholder text.
        Returns
        -------
        text : str
        """
        return self.__placeholderText

    def wheelEvent(self, event):
        """Reimplemented."""
        event.ignore()

    def keyPressEvent(self, event):
        """Reimplemented."""
        # Override the default QComboBox behavior
        if event.key() == Qt.Key_Down and event.modifiers() & Qt.AltModifier:
            self.showPopup()
            return

        ignored = {Qt.Key_Up, Qt.Key_Down,
                   Qt.Key_PageDown, Qt.Key_PageUp,
                   Qt.Key_Home, Qt.Key_End}

        if event.key() in ignored:
            event.ignore()
            return

        super(CheckComboBox, self).keyPressEvent(event)

    def __updateItemDelegate(self):
        opt = QStyleOptionComboBox()
        opt.initFrom(self)
        if self.style().styleHint(QStyle.SH_ComboBox_Popup, opt, self):
            delegate = CheckComboBox.ComboMenuDelegate(self)
        else:
            delegate = CheckComboBox.ComboItemDelegate(self)
        self.setItemDelegate(delegate)


def example():
    app = QApplication(list(sys.argv))
    cb = CheckComboBox(placeholderText="None")
    model = cb.model()
    cb.addItem("First")
    model.item(0).setCheckable(True)
    cb.addItem("Second")
    model.item(1).setCheckable(True)
    cb.addItem("Third")
    model.item(2).setCheckable(True)
    cb.insertSeparator(3)
    cb.addItem("Fourth - Disabled")
    model.item(4).setEnabled(False)
    cb.show()
    cb.raise_()

    return app.exec_()

if __name__ == "__main__":
    sys.exit(example())