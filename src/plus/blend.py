#
# blend.py
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
        QComboBox, # @UnusedImport @Reimport  @UnresolvedImport
        QLineEdit, # @UnusedImport @Reimport  @UnresolvedImport
        QDialogButtonBox, # @UnusedImport @Reimport  @UnresolvedImport
        QToolButton, # @UnusedImport @Reimport  @UnresolvedImport
        QTableWidget, # @UnusedImport @Reimport  @UnresolvedImport
        QStyle, # @UnusedImport @Reimport  @UnresolvedImport
        QHeaderView, # @UnusedImport @Reimport  @UnresolvedImport
    )
    from PyQt6.QtCore import Qt, pyqtSlot, QSize, QSettings # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QKeySequence, QAction, QIcon, QStandardItemModel # @UnusedImport @Reimport  @UnresolvedImport
#    from PyQt6 import sip # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #pylint: disable = E, W, R, C
    from PyQt5.QtWidgets import (  # type: ignore
        QApplication, # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, # @UnusedImport @Reimport  @UnresolvedImport
        QLineEdit, # @UnusedImport @Reimport  @UnresolvedImport
        QDialogButtonBox, # @UnusedImport @Reimport  @UnresolvedImport
        QToolButton, # @UnusedImport @Reimport  @UnresolvedImport
        QTableWidget, # @UnusedImport @Reimport  @UnresolvedImport
        QStyle, # @UnusedImport @Reimport  @UnresolvedImport
        QHeaderView, # @UnusedImport @Reimport  @UnresolvedImport
    )
    from PyQt5.QtCore import Qt, pyqtSlot, QSize, QSettings # type: ignore  # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QKeySequence, QIcon, QStandardItemModel # type: ignore  # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QAction # type: ignore  # @UnusedImport @Reimport  @UnresolvedImport
#    try:
#        from PyQt5 import sip # type: ignore  # @Reimport @UnresolvedImport @UnusedImport
#    except Exception: # pylint: disable=broad-except
#        import sip  # type: ignore # @Reimport @UnresolvedImport @UnusedImport

import logging
from artisanlib.util import comma2dot, float2floatWeightVolume
from artisanlib.dialogs import ArtisanDialog
from artisanlib.widgets import MyQComboBox
from uic import BlendDialog # OFF type: ignore[attr-defined] # pylint: disable=no-name-in-module
from typing import Final, Optional, List, Set, Collection, Dict, Tuple, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent, QKeyEvent # pylint: disable=unused-import

_log: Final[logging.Logger] = logging.getLogger(__name__)



########################################################################################
#####################  Component  ######################################################

# coffee is given by its hr_id
class Component:
    def __init__(self, coffee: str, ratio: float) -> None:
        self._coffee = coffee
        self._ratio = ratio

    @property
    def coffee(self) -> str:
        return self._coffee

    @coffee.setter
    def coffee(self, value:str) -> None:
        self._coffee = value

    @property
    def ratio(self) -> float:
        return self._ratio

    @ratio.setter
    def ratio(self, value:float) -> None:
        self._ratio = value


########################################################################################
#######################  CustomBlend  ##################################################

class CustomBlend:
    def __init__(self, name: str, components: List[Component]) -> None:
        self._name:str = name
        self._components:List[Component] = components

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value:str) -> None:
        self._name = value

    @property
    def components(self) -> List[Component]:
        return self._components

    @components.setter
    def components(self, value:List[Component]) -> None:
        self._components = value

    # a blend is valid if it
    #  - has at least 2 ingredients,
    #  - the component ratios of all ingredients sum up to 1,
    #  - there are no duplicates in the list of component coffees, and,
    #  - all component coffees are contained in the list of available_coffees (list of hr_ids as strings), if given
    def isValid(self, available_coffees: Optional[Collection[str]] = None) -> bool:
        component_coffees = [c.coffee for c in self._components]
        return (
            len(component_coffees)>1 and
            len(component_coffees) == len(set(component_coffees)) and
            (available_coffees is None or all(cc in available_coffees for cc in component_coffees))
        )

########################################################################################
#####################  Custom CustomBlend Dialog  ######################################

class CustomBlendDialog(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow', inWeight:float, weightUnit:str,
            coffees:Dict[str, str], blend:CustomBlend, coffee_hr_ids_with_stock_in_store:Set[str]) -> None:
        super().__init__(parent, aw)
        self.initialTotalWeight:float = inWeight
        self.inWeight:float = inWeight
        self.weightUnit:str = weightUnit
        self.coffee_hr_ids_with_stock_in_store:Set[str] = coffee_hr_ids_with_stock_in_store
        self.coffees:Dict[str, str] = coffees # dict associating coffee names to their hr_id
        self.coffee_ids:Dict[str, str] = {v: k for k, v in self.coffees.items()} # dict associating coffee hr_ids to their names
        self.sorted_coffees:List[Tuple[str, str]] = sorted(coffees.items(), key=lambda x: x[0]) # list of coffee name and hr_id tuples sorted by coffee name
        self.blend:CustomBlend = CustomBlend( # we create a new copy not to alter the original one
            blend.name.strip(),
            [Component(c.coffee, c.ratio) for c in blend.components])

        # configure UI
        self.ui = BlendDialog.Ui_customBlendDialog()
        self.ui.setupUi(self) # OFF type:ignore[no-untyped-call]
        self.setWindowTitle(QApplication.translate('Form Caption','Custom Blend'))
        self.ui.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Apply)
        # hack to assign the Apply button the AcceptRole without losing default system translations
        applyButton = self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Apply)
        if applyButton is not None:
            self.ui.buttonBox.removeButton(applyButton)
            self.applyButton = self.ui.buttonBox.addButton(applyButton.text(), QDialogButtonBox.ButtonRole.AcceptRole)

        cancelButton = self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Cancel)
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


        # populate widgets
        self.ui.lineEdit_name.setText(self.blend.name)
        self.ui.label_weight.setText(QApplication.translate('Label','Weight'))
        self.ui.lineEdit_weight.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, self.ui.lineEdit_weight))  # the max limit has to be high enough otherwise the connected signals are not send!
        inw = f'{float2floatWeightVolume(self.inWeight):g}'
        self.ui.lineEdit_weight.setText(inw)
        self.ui.label_unit.setText(self.weightUnit)
        self.updateComponentTable()
        self.updateAddButton()

        # connect widget signals
        self.ui.lineEdit_name.editingFinished.connect(self.nameChanged)
        self.ui.pushButton_add.clicked.connect(self.addComponent)
        self.ui.lineEdit_weight.editingFinished.connect(self.weighteditChanged)
        self.ui.lineEdit_weight.textChanged.connect(self.textChanged)

        settings = QSettings()
        if settings.contains('BlendGeometry'):
            self.restoreGeometry(settings.value('BlendGeometry'))

    @pyqtSlot()
    def cancelDialog(self) -> None: # ESC key
        self.reject()

    def keyPressEvent(self, event: Optional['QKeyEvent']) -> None:
        if event is not None:
            key = int(event.key())
            #uncomment next line to find the integer value of a key
            #print(key)
            #modifiers = QApplication.keyboardModifiers()
            modifiers = event.modifiers()
            if key == 16777216 or (key == 87 and modifiers == Qt.KeyboardModifier.ControlModifier): #ESCAPE or CMD-W
                self.reject()
            else:
                super().keyPressEvent(event)

    @pyqtSlot(str)
    def textChanged(self,s:str) -> None:
        if s == '': # content got cleared
            self.ui.lineEdit_weight.setText('0')
            self.ui.lineEdit_weight.repaint()
            self.weighteditChanged()

    @pyqtSlot()
    def nameChanged(self) -> None:
        self.blend.name = self.ui.lineEdit_name.text().strip()

    # as the total weight was explicitly updated by the user, we set the initialTotalWeight here
    @pyqtSlot()
    def weighteditChanged(self) -> None:
        try:
            weight = float(comma2dot(self.ui.lineEdit_weight.text())) # text could be a non-float!
            inw = f'{float2floatWeightVolume(weight):g}'
            self.ui.lineEdit_weight.setText(inw)
            self.ui.lineEdit_weight.repaint()
            self.initialTotalWeight = float(self.ui.lineEdit_weight.text())
            self.inWeight = self.initialTotalWeight
            self.updateComponentTable()
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)

    @pyqtSlot()
    def ratioChanged(self) -> None:
        i = self.aw.findWidgetsRow(self.ui.tableWidget,self.sender(), 0)
        if i is not None:
            ratioLineEdit = cast(QLineEdit, self.ui.tableWidget.cellWidget(i,0))
            ratio = max(0.0, float(ratioLineEdit.text()) / 100)
            self.blend.components[i].ratio = max(0.0, min(1.0, ratio))
            # if there are exactly two components, we calculate the ratio of the second component to 1
            if len(self.blend.components) == 2 and ratio < 1:
                self.blend.components[(i+1) % 2].ratio = max(0.0, min(1.0, 1 - ratio))
            self.updateComponentTable()

    @pyqtSlot()
    def weightChanged(self) -> None:
        i = self.aw.findWidgetsRow(self.ui.tableWidget,self.sender(), 1)
        if i is not None:
            weightLineEdit = cast(QLineEdit, self.ui.tableWidget.cellWidget(i,1))
            weight = float(comma2dot(weightLineEdit.text()))
            inw = f'{float2floatWeightVolume(weight):g}'
            weightLineEdit.setText(inw)
            if self.initialTotalWeight == 0:
                # we update the total weight
#                self.inWeight = sum(float(self.ui.tableWidget.cellWidget(j,1).text()) for j in range(self.ui.tableWidget.rowCount()))
                # we need a type assertion here:
                inWeight_sum:float = 0
                for j in range(self.ui.tableWidget.rowCount()):
                    cw = cast(QLineEdit, self.ui.tableWidget.cellWidget(j,1))
                    inWeight_sum += float(cw.text())
                self.inWeight = inWeight_sum
                inw = f'{float2floatWeightVolume(self.inWeight):g}'
                self.ui.lineEdit_weight.setText(inw)
                self.ui.lineEdit_weight.repaint()
            if self.inWeight != 0:
                # we update the ratio
                ratio = max(0.0, min(1.0, weight / self.inWeight))
                self.blend.components[i].ratio = ratio
                # if there are exactly two components, we calculate the ratio of the second component to 1
                if len(self.blend.components) == 2 and ratio < 1:
                    self.blend.components[(i+1) % 2].ratio = max(0.0, min(1.0, 1 - ratio))
                elif self.initialTotalWeight == 0:
                    # we calculate the ratio of all other components from their individual weight too
                    for j in range(self.ui.tableWidget.rowCount()):
                        if j != i: # for component i we already calculated the ratio
                            wLineEdit = cast(QLineEdit, self.ui.tableWidget.cellWidget(j,1))
                            weight = float(wLineEdit.text())
                            ratio = max(0.0, min(1.0, weight / self.inWeight))
                            self.blend.components[j].ratio = ratio
            self.updateComponentTable()

    @pyqtSlot(int)
    def componentCoffeeChanged(self,_:int) -> None:
        i = self.aw.findWidgetsRow(self.ui.tableWidget,self.sender(), 2)
        if i is not None:
            coffeecombobox = cast(QComboBox, self.ui.tableWidget.cellWidget(i,2))
            hr_id = self.coffees[coffeecombobox.currentText()]
            self.blend.components[i].coffee = hr_id

    ###

    @pyqtSlot(bool)
    def addComponent(self,_:bool) -> None:
        ratio = min(100.0, max(0.0, 1 - sum(c.ratio for c in self.blend.components)))
        blend_coffees = [c.coffee for c in self.blend.components]
        coffee = [hr_id for (c,hr_id) in self.sorted_coffees if hr_id not in blend_coffees][0]
        self.blend.components.append(Component(coffee,ratio))
        self.updateAddButton()
        self.updateComponentTable()

    @pyqtSlot(bool)
    def deleteComponent(self,_:bool) -> None:
        i = self.aw.findWidgetsRow(self.ui.tableWidget,self.sender(), 3)
        if i is not None:
            self.blend.components = self.blend.components[:i] + self.blend.components[i+1:]
            self.updateAddButton()
            self.updateComponentTable()

    def saveSettings(self) -> None:
        settings = QSettings()
        #save window geometry
        settings.setValue('BlendGeometry',self.saveGeometry())

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        self.reject()

    @pyqtSlot()
    def accept(self) -> None:
        self.saveSettings()
        super().accept()

    @pyqtSlot()
    def reject(self) -> None:
        self.saveSettings()
        super().reject()

    @pyqtSlot()
    def close(self) -> bool:
        self.closeEvent(None)
        return True

    def updateAddButton(self) -> None:
        self.ui.pushButton_add.setEnabled(len(self.coffees)>len(self.blend.components))

    # returns True if all component ratios sum up to (about) 1 and all individual ratios are above 0 and below 100
    def checkRatio(self) -> bool:
        ratios = [c.ratio for c in self.blend.components]
        return all(0 < r < 100 for r in ratios) and (-0.0009 < (1 - sum(ratios)) < 0.001)

    def updateComponentTable(self) -> None:
        try:
            self.ui.tableWidget.clear()
            self.ui.tableWidget.setTabKeyNavigation(False)

            columns = 4
            rows = len(self.blend.components)
            self.ui.tableWidget.setColumnCount(columns)
            self.ui.tableWidget.setRowCount(rows)

            self.ui.tableWidget.setHorizontalHeaderLabels(['%',
                                                           self.weightUnit,
                                                           QApplication.translate('Label','Beans'),
                                                           ''])
            self.ui.tableWidget.setAlternatingRowColors(False)
            self.ui.tableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.ui.tableWidget.setSelectionMode(QTableWidget.SelectionMode.NoSelection) # QTableWidget.SelectionMode.SingleSelection
            self.ui.tableWidget.setShowGrid(True)

            blend_coffees = [c.coffee for c in self.blend.components]

            ratio_correct = self.checkRatio()

            if self.applyButton is not None:
                self.applyButton.setEnabled(ratio_correct)

            for i, c in enumerate(self.blend.components):
                #ratio
                ratioedit = QLineEdit(f'{c.ratio*100:.1f}'.rstrip('0').rstrip('.'))
                ratioedit.setAlignment(Qt.AlignmentFlag.AlignRight)
                ratioedit.setMinimumWidth(40)
                ratioedit.setMaximumWidth(40)
                ratioedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 1, ratioedit))  # the max limit has to be high enough otherwise the connected signals are not send!
                if not ratio_correct:
                    ratioedit.setStyleSheet('QLineEdit { color: #CC0F50; }')
                self.ui.tableWidget.setCellWidget(i,0,ratioedit)
                ratioedit.editingFinished.connect(self.ratioChanged)

                #weight
                component_weight = c.ratio * self.inWeight
                weightedit = QLineEdit(f'{float2floatWeightVolume(component_weight):g}')
                weightedit.setAlignment(Qt.AlignmentFlag.AlignRight)
                weightedit.setMinimumWidth(70)
                weightedit.setMaximumWidth(70)
                weightedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, weightedit))  # the max limit has to be high enough otherwise the connected signals are not send!
                self.ui.tableWidget.setCellWidget(i,1,weightedit)
                weightedit.editingFinished.connect(self.weightChanged)

                #beans
                beansComboBox = MyQComboBox()
                beansComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
                # the popup contains all available coffees but the ones used already in the blend, but always contains the components coffee
                coffees_tuples = [(n, hr_id) for (n, hr_id) in self.sorted_coffees if hr_id == c.coffee or hr_id not in blend_coffees]
                coffees = [n for (n, hr_id) in coffees_tuples]

                beansComboBox.addItems(coffees)

                # disable items without stock in current selected store
                model = cast(QStandardItemModel, beansComboBox.model())
                if model is not None:
                    for r, (_,hr_id) in enumerate(coffees_tuples):
                        if hr_id not in self.coffee_hr_ids_with_stock_in_store:
                            item = model.item(r)
                            if item is not None:
                                item.setEnabled(False)

                beansComboBox.setCurrentIndex(coffees.index(self.coffee_ids[c.coffee]))
                self.ui.tableWidget.setCellWidget(i,2,beansComboBox)
                beansComboBox.currentIndexChanged.connect(self.componentCoffeeChanged)

                #delete
                if rows>2:
                    deleteButton = QToolButton()
                    app_style = QApplication.style()
                    if app_style is not None:
                        deleteButton.setIcon(QIcon(app_style.standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton))) #SP_TitleBarCloseButton
                    deleteButton.setIconSize(QSize(16,16))
                    deleteButton.setFixedSize(QSize(22, 22))
                    deleteButton.clicked.connect(self.deleteComponent)
                    self.ui.tableWidget.setCellWidget(i,3,deleteButton)

            header = self.ui.tableWidget.horizontalHeader()
            self.ui.tableWidget.resizeColumnsToContents()
            if header is not None:
                header.setStretchLastSection(False)
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
                header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            self.ui.tableWidget.setColumnWidth(3,22)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)


def openCustomBlendDialog(window:'QWidget', aw:'ApplicationWindow', inWeight:float, weightUnit:str,
        coffees:Dict[str, str], blend:CustomBlend, coffee_hr_ids_with_stock_in_store:Set[str]) -> Tuple[Optional[CustomBlend], float]:
    dialog = CustomBlendDialog(window, aw, inWeight, weightUnit, coffees, blend, coffee_hr_ids_with_stock_in_store)
    res = dialog.exec()
    blend_res:Optional[CustomBlend]
    if res:
        blend_res = dialog.blend
        total_weight = dialog.inWeight
    else:
        blend_res = None
        total_weight = inWeight

#    #deleteLater() will not work here as the dialog is still bound via the parent
#    #dialog.deleteLater() # now we explicitly allow the dialog an its widgets to be GCed
#    # the following will immediately release the memory despite this parent link
#    QApplication.processEvents() # we ensure events concerning this dialog are processed before deletion
#    try: # sip not supported on older PyQt versions (RPi!)
#        sip.delete(dialog)
#        #print(sip.isdeleted(dialog))
#    except Exception: # pylint: disable=broad-except
#        pass

    return blend_res, total_weight
