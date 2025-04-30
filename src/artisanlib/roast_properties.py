#
# ABOUT
# Artisan Roast Properties Dialog

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

import sys
import math
import platform
import logging
from typing import Final, Optional, List, Set, Tuple, Dict, Callable, cast, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from artisanlib.atypes import RecentRoast, BTU
    from artisanlib.acaia import Acaia # noqa: F401 # pylint: disable=unused-import
    from plus.stock import Blend # noqa: F401  # pylint: disable=unused-import
    from PyQt6.QtWidgets import QLayout, QAbstractItemView, QCompleter # pylint: disable=unused-import
    from PyQt6.QtGui import QClipboard, QCloseEvent, QKeyEvent, QMouseEvent # pylint: disable=unused-import
    from PyQt6.QtCore import QObject, QMetaObject # pylint: disable=unused-import


# import artisan.plus modules
import plus.config  # @UnusedImport
import plus.util
import plus.stock
import plus.controller
import plus.queue
import plus.blend

#from artisanlib.suppress_errors import suppress_stdout_stderr
from artisanlib.util import (deltaLabelUTF8, stringfromseconds,stringtoseconds, toInt, toFloat, abbrevString,
        scaleFloat2String, comma2dot, weight_units, render_weight, weight_units_lower, volume_units, float2floatWeightVolume, float2float,
        convertWeight, convertVolume)
from artisanlib.dialogs import ArtisanDialog, ArtisanResizeablDialog, tareDlg
from artisanlib.widgets import MyQComboBox, ClickableQLabel, ClickableTextEdit, MyTableWidgetItemNumber


from uic import EnergyWidget # pyright: ignore[attr-defined] # pylint: disable=no-name-in-module
from uic import SetupWidget # pyright: ignore[attr-defined] # pylint: disable=no-name-in-module
from uic import MeasureDialog # pyright: ignore[attr-defined] # pylint: disable=no-name-in-module

_log: Final[logging.Logger] = logging.getLogger(__name__)

try:
    from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QRegularExpression, QSettings, QTimer, QEvent, QLocale, QSignalBlocker # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QColor, QIntValidator, QRegularExpressionValidator, QKeySequence, QPalette # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QWidget, QCheckBox, QComboBox, QDialogButtonBox, QGridLayout, # @UnusedImport @Reimport  @UnresolvedImport
                                 QHBoxLayout, QVBoxLayout, QHeaderView, QLabel, QLineEdit, QTextEdit, QListView,  # @UnusedImport @Reimport  @UnresolvedImport
                                 QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QSizePolicy, # @UnusedImport @Reimport  @UnresolvedImport
                                 QGroupBox, QToolButton, QFrame) # @UnusedImport @Reimport  @UnresolvedImport
#    from PyQt6 import sip # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QRegularExpression, QSettings, QTimer, QEvent, QLocale, QSignalBlocker # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QColor, QIntValidator, QRegularExpressionValidator, QKeySequence, QPalette # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QWidget, QCheckBox, QComboBox, QDialogButtonBox, QGridLayout, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
                                 QHBoxLayout, QVBoxLayout, QHeaderView, QLabel, QLineEdit, QTextEdit, QListView, # @UnusedImport @Reimport  @UnresolvedImport
                                 QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QSizePolicy, # @UnusedImport @Reimport  @UnresolvedImport
                                 QGroupBox, QToolButton, QFrame) # @UnusedImport @Reimport  @UnresolvedImport
#    try:
#        from PyQt5 import sip # type: ignore # @Reimport @UnresolvedImport @UnusedImport
#    except ImportError:
#        import sip  # type: ignore # @Reimport @UnresolvedImport @UnusedImport


########################################################################################
#####################  Volume Calculator DLG  ##########################################
########################################################################################

class volumeCalculatorDlg(ArtisanDialog):
    def __init__(self, parent:'editGraphDlg', aw:'ApplicationWindow', weightIn:Optional[float], weightOut:Optional[float],
            weightunit:int,volumeunit:int,
            inlineedit:QLineEdit,outlineedit:QLineEdit,tare:float) -> None: # weight in and out expected in g (int)

        self.parent_dialog = parent
        # weightunit 0:g, 1:Kg  volumeunit 0:ml, 1:l
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Volume Calculator'))

        if self.aw.scale.device is not None and self.aw.scale.device not in {'', 'None'}:
            self.scale_connected = True
        else:
            self.scale_connected = False

        self.weightIn:Optional[float] = weightIn
        self.weightOut:Optional[float] = weightOut

        # the units
        self.weightunit = weightunit
        self.volumeunit = volumeunit

        # the results
        self.inVolume:Optional[float] = None
        self.outVolume:Optional[float] = None

        # the QLineedits of the RoastProperties dialog to be updated
        self.inlineedit = inlineedit
        self.outlineedit = outlineedit

        # the current active tare
        self.tare = tare

        # Scale Weight
        self.scale_weight = self.parent_dialog.scale_weight
        self.scaleWeight = QLabel() # displays the current reading
        if self.parent_dialog.acaia is not None:
            self.update_scale_weight()
            self.parent_dialog.acaia.weight_changed_signal.connect(self.acaia_weight_changed)
            self.parent_dialog.acaia.battery_changed_signal.connect(self.acaia_battery_changed)
            self.parent_dialog.acaia.disconnected_signal.connect(self.acaia_disconnected)
        # Scale Battery
        self.scale_battery = self.parent_dialog.scale_battery

        # Unit Group
        unitvolumeLabel = QLabel('<b>' + QApplication.translate('Label','Unit') + '</b>')
        self.unitvolumeEdit = QLineEdit(f'{self.aw.qmc.volumeCalcUnit:g}')
#        self.unitvolumeEdit.setValidator(QIntValidator(0, 99999,self.unitvolumeEdit))
        self.unitvolumeEdit.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, self.unitvolumeEdit))
        self.unitvolumeEdit.setMinimumWidth(70)
        self.unitvolumeEdit.setMaximumWidth(70)
        self.unitvolumeEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        unitvolumeUnit = QLabel(QApplication.translate('Label','ml'))

        # unit button
        unitButton = QPushButton(QApplication.translate('Button', 'unit'))
        unitButton.clicked.connect(self.unitWeight)
        unitButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        unitLayout = QHBoxLayout()
        if self.scale_connected:
            unitLayout.addStretch()
        unitLayout.addWidget(self.scaleWeight)
        unitLayout.addStretch()
        unitLayout.addWidget(unitvolumeLabel)
        unitLayout.addWidget(self.unitvolumeEdit)
        unitLayout.addWidget(unitvolumeUnit)
        unitLayout.addStretch()
        if self.scale_connected:
            unitLayout.addWidget(unitButton)

        # In Group
        coffeeinunitweightLabel = QLabel('<b>' + QApplication.translate('Label','Unit Weight') + '</b>')
        self.coffeeinweightEdit = QLineEdit(self.aw.qmc.volumeCalcWeightInStr)
        self.coffeeinweightEdit.setMinimumWidth(70)
        self.coffeeinweightEdit.setMaximumWidth(70)
        self.coffeeinweightEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        coffeeinunitweightUnit = QLabel(QApplication.translate('Label','g'))

        coffeeinweightLabel = QLabel('<b>' + QApplication.translate('Label','Weight') + '</b>')
        self.coffeeinweight = QLineEdit()
        if self.weightIn:
            self.coffeeinweight.setText(f'{float2floatWeightVolume(self.weightIn):g}')
        self.coffeeinweight.setMinimumWidth(70)
        self.coffeeinweight.setMaximumWidth(70)
        self.coffeeinweight.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.coffeeinweight.setReadOnly(True)
        self.coffeeinweight.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if sys.platform.startswith('darwin'):
            self.coffeeinweight.setStyleSheet("border: 0.5px solid lightgrey; background-color:'lightgrey'")
        else:
            self.coffeeinweight.setStyleSheet("background-color:'lightgrey'")
        coffeeinweightUnit = QLabel(weight_units[weightunit])

        coffeeinvolumeLabel = QLabel('<b>' + QApplication.translate('Label','Volume') + '</b>')
        self.coffeeinvolume = QLineEdit()
        self.coffeeinvolume.setMinimumWidth(70)
        self.coffeeinvolume.setMaximumWidth(70)

        palette = QPalette()
        palette.setColor(self.coffeeinvolume.foregroundRole(), QColor('red'))
        self.coffeeinvolume.setPalette(palette)

        self.coffeeinvolume.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.coffeeinvolume.setReadOnly(True)
        self.coffeeinvolume.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        coffeeinvolumeUnit = QLabel(volume_units[volumeunit])

        # in button
        inButton = QPushButton(QApplication.translate('Button', 'in'))
        inButton.clicked.connect(self.inWeight)
        inButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        inGrid = QGridLayout()
        inGrid.addWidget(coffeeinweightLabel,0,0)
        inGrid.addWidget(self.coffeeinweight,0,1)
        inGrid.addWidget(coffeeinweightUnit,0,2)
        inGrid.addWidget(coffeeinvolumeLabel,1,0)
        inGrid.addWidget(self.coffeeinvolume,1,1)
        inGrid.addWidget(coffeeinvolumeUnit,1,2)

        volumeInLayout = QHBoxLayout()
        volumeInLayout.addWidget(coffeeinunitweightLabel)
        volumeInLayout.addWidget(self.coffeeinweightEdit)
        volumeInLayout.addWidget(coffeeinunitweightUnit)
        volumeInLayout.addSpacing(15)
        volumeInLayout.addLayout(inGrid)

        inButtonLayout = QHBoxLayout()
        inButtonLayout.addWidget(inButton)
        inButtonLayout.addStretch()

        volumeInVLayout = QVBoxLayout()
        volumeInVLayout.addLayout(volumeInLayout)
        if self.scale_connected:
            volumeInVLayout.addLayout(inButtonLayout)

        volumeInGroupLayout = QGroupBox(QApplication.translate('Label','Green'))
        volumeInGroupLayout.setLayout(volumeInVLayout)
        if weightIn is None:
            volumeInGroupLayout.setDisabled(True)

        self.resetInVolume()

        # Out Group
        coffeeoutunitweightLabel = QLabel('<b>' + QApplication.translate('Label','Unit Weight') + '</b>')
        self.coffeeoutweightEdit = QLineEdit(self.aw.qmc.volumeCalcWeightOutStr)
        self.coffeeoutweightEdit.setMinimumWidth(60)
        self.coffeeoutweightEdit.setMaximumWidth(60)
        self.coffeeoutweightEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        coffeeoutunitweightUnit = QLabel(QApplication.translate('Label','g'))

        coffeeoutweightLabel = QLabel('<b>' + QApplication.translate('Label','Weight') + '</b>')
        self.coffeeoutweight = QLineEdit()
        if self.weightOut:
            self.coffeeoutweight.setText(f'{float2floatWeightVolume(self.weightOut):g}')
        self.coffeeoutweight.setMinimumWidth(60)
        self.coffeeoutweight.setMaximumWidth(60)
        self.coffeeoutweight.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.coffeeoutweight.setReadOnly(True)
        if sys.platform.startswith('darwin'):
            self.coffeeoutweight.setStyleSheet("border: 0.5px solid lightgrey; background-color:'lightgrey'")
        else:
            self.coffeeoutweight.setStyleSheet("background-color:'lightgrey'")
        self.coffeeoutweight.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        coffeeoutweightUnit = QLabel(weight_units[weightunit])

        coffeeoutvolumeLabel = QLabel('<b>' + QApplication.translate('Label','Volume') + '</b>')
        self.coffeeoutvolume = QLineEdit()
        self.coffeeoutvolume.setMinimumWidth(60)
        self.coffeeoutvolume.setMaximumWidth(60)

        palette = QPalette()
        palette.setColor(self.coffeeoutvolume.foregroundRole(), QColor('red'))
        self.coffeeoutvolume.setPalette(palette)

        self.coffeeoutvolume.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.coffeeoutvolume.setReadOnly(True)
        self.coffeeoutvolume.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        coffeeoutvolumeUnit = QLabel(volume_units[volumeunit])

        # out button
        outButton = QPushButton(QApplication.translate('Button', 'out'))
        outButton.clicked.connect(self.outWeight)
        outButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        outGrid = QGridLayout()
        outGrid.addWidget(coffeeoutweightLabel,0,0)
        outGrid.addWidget(self.coffeeoutweight,0,1)
        outGrid.addWidget(coffeeoutweightUnit,0,2)
        outGrid.addWidget(coffeeoutvolumeLabel,1,0)
        outGrid.addWidget(self.coffeeoutvolume,1,1)
        outGrid.addWidget(coffeeoutvolumeUnit,1,2)

        volumeOutLayout = QHBoxLayout()
        volumeOutLayout.addWidget(coffeeoutunitweightLabel)
        volumeOutLayout.addWidget(self.coffeeoutweightEdit)
        volumeOutLayout.addWidget(coffeeoutunitweightUnit)
        volumeOutLayout.addSpacing(15)
        volumeOutLayout.addLayout(outGrid)

        outButtonLayout = QHBoxLayout()
        outButtonLayout.addWidget(outButton)
        outButtonLayout.addStretch()

        volumeOutVLayout = QVBoxLayout()
        volumeOutVLayout.addLayout(volumeOutLayout)
        if self.scale_connected:
            volumeOutVLayout.addLayout(outButtonLayout)

        volumeOutGroupLayout = QGroupBox(QApplication.translate('Label','Roasted'))
        volumeOutGroupLayout.setLayout(volumeOutVLayout)
        if weightOut is None:
            volumeOutGroupLayout.setDisabled(True)

        self.resetOutVolume()

        self.coffeeinweightEdit.editingFinished.connect(self.resetInVolume)
        self.coffeeoutweightEdit.editingFinished.connect(self.resetOutVolume)
        self.unitvolumeEdit.editingFinished.connect(self.resetVolume)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.updateVolumes)
        self.dialogbuttons.rejected.connect(self.close)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)

        mainlayout = QVBoxLayout()
        mainlayout.addLayout(unitLayout)
        mainlayout.addWidget(volumeInGroupLayout)
        mainlayout.addWidget(volumeOutGroupLayout)
        mainlayout.addLayout(buttonLayout)
        self.setLayout(mainlayout)
        self.coffeeinweightEdit.setFocus()

        self.parent_dialog.scaleWeightUpdated.connect(self.update_scale_weight)

        if self.aw.largeScaleLCDs_dialog is not None:
            self.aw.largeScaleLCDs_dialog.updateWeightUnit('g')

    @pyqtSlot()
    def acaia_disconnected(self) -> None:
        self.scale_weight = None
        self.scale_battery = None
        self.updateWeightLCD('----')

    def updateWeightLCD(self, txt_value:str, txt_unit:str = '') -> None:
        if self.aw.scale.device is not None and self.aw.scale.device not in {'', 'None'}:
            self.scaleWeight.setText('' if txt_value == '' else txt_value+txt_unit.lower())
            self.aw.qmc.updateLargeScaleLCDs(txt_value)

    @pyqtSlot(int)
    def acaia_battery_changed(self, b:int) -> None:
        self.scale_battery = b

    @pyqtSlot(int)
    def acaia_weight_changed(self, w:int) -> None:
        self.scale_weight = w
        self.update_scale_weight()

    @pyqtSlot(float)
    def update_scale_weight(self, weight:Optional[float] = None) -> None:
        try:
            if weight is not None:
                self.scale_weight = weight
            if self.scale_weight is not None and self.tare is not None:
                self.updateWeightLCD(f'{self.scale_weight - self.tare:.0f}','g')
            else:
                self.updateWeightLCD('----')
        except Exception as e: # pylint: disable=broad-except # the dialog might have been closed already and thus the qlabel might not exist anymore
            _log.exception(e)

    #keyboard presses. There must not be widgets (pushbuttons, comboboxes, etc) in focus in order to work
    def keyPressEvent(self, event: Optional['QKeyEvent']) -> None:
        if event is not None:
            key = int(event.key())
            if key == 16777220 and self.scale_connected: # ENTER key pressed
                v = self.retrieveWeight()
                if v and v != 0:
                    if self.unitvolumeEdit.hasFocus():
                        self.unitvolumeEdit.setText(f'{float2float(v):g}')
                    elif self.coffeeinweightEdit.hasFocus():
                        self.coffeeinweightEdit.setText(f'{float2float(v):g}')
                    elif self.coffeeoutweightEdit.hasFocus():
                        self.coffeeoutweightEdit.setText(f'{float2float(v):g}')
            else:
                super().keyPressEvent(event)

    def widgetWeight(self, widget:QLineEdit) -> None:
        w = self.retrieveWeight()
        if w is not None:
            v = float2floatWeightVolume(w)
            # updating this widget in a separate thread seems to be important on OS X 10.14 to avoid delayed updates and widget redraw problesm
            QTimer.singleShot(2,lambda : widget.setText(f'{float2float(v):g}'))

    @pyqtSlot(bool)
    def unitWeight(self, _:bool = False) -> None:
        self.widgetWeight(self.unitvolumeEdit)

    @pyqtSlot(bool)
    def inWeight(self, _:bool = False) -> None:
        QTimer.singleShot(1, self.setWidgetInWeight)
        QTimer.singleShot(10, self.resetInVolume)

    @pyqtSlot(bool)
    def outWeight(self, _:bool = False) -> None:
        QTimer.singleShot(1, self.setWidgetOutWeight)
        QTimer.singleShot(10, self.resetOutVolume)

    def retrieveWeight(self) -> Optional[float]:
        v = self.scale_weight
        if v is not None: # value received
            # subtract tare
            return v - self.tare
        return None

    @pyqtSlot()
    def resetVolume(self) -> None:
        self.resetInVolume()
        self.resetOutVolume()

    @pyqtSlot()
    def setWidgetInWeight(self) -> None:
        self.widgetWeight(self.coffeeinweightEdit)

    @pyqtSlot()
    def setWidgetOutWeight(self) -> None:
        self.widgetWeight(self.coffeeoutweightEdit)

    @pyqtSlot()
    def resetInVolume(self) -> None:
        try:
            line = self.coffeeinweightEdit.text()
            if self.weightIn is None or line is None or str(line).strip() == '':
                self.coffeeinvolume.setText('')
                self.inVolume = None
            else:
                inWeight:float = float(comma2dot(self.coffeeinweightEdit.text()))
                if inWeight == 0:
                    self.coffeeinvolume.setText('')
                    self.inVolume = None
                else:
                    self.inVolume = convertVolume(
                        convertWeight(self.weightIn,self.weightunit,0) * float(comma2dot(self.unitvolumeEdit.text())) / inWeight,
                        5,
                        self.volumeunit)
                    self.coffeeinvolume.setText(f'{float2floatWeightVolume(self.inVolume):g}')
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            self.inVolume = None
            self.coffeeinvolume.setText('')

    @pyqtSlot()
    def resetOutVolume(self) -> None:
        try:
            line = self.coffeeoutweightEdit.text()
            if self.weightOut is None or line is None or str(line).strip() == '':
                self.coffeeoutvolume.setText('')
                self.outVolume = None
            else:
                outWeight:float = float(comma2dot(str(self.coffeeoutweightEdit.text())))
                if outWeight == 0:
                    self.coffeeoutvolume.setText('')
                    self.outVolume = None
                else:
                    self.outVolume = convertVolume(
                        convertWeight(self.weightOut,self.weightunit,0) * float(comma2dot(str(self.unitvolumeEdit.text()))) / outWeight,
                        5,
                        self.volumeunit)
                    self.coffeeoutvolume.setText(f'{float2floatWeightVolume(self.outVolume):g}')
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            self.outVolume = None
            self.coffeeoutvolume.setText('')

    @pyqtSlot()
    def updateVolumes(self) -> None:
        if self.inVolume:
            self.inlineedit.setText(f'{float2floatWeightVolume(self.inVolume):g}')
        if self.outVolume:
            self.outlineedit.setText(f'{float2floatWeightVolume(self.outVolume):g}')
        self.parent_dialog.volume_percent()
        self.closeEvent(None)

    @pyqtSlot('QCloseEvent')
    def closeEvent(self,_:Optional['QCloseEvent'] = None) -> None:
        if self.aw.largeScaleLCDs_dialog is not None:
            self.aw.largeScaleLCDs_dialog.updateWeightUnit()

        try:
            self.parent_dialog.volumedialog = None
        except Exception: # pylint: disable=broad-except
            pass
        if self.unitvolumeEdit.text() and self.unitvolumeEdit.text() != '':
            self.aw.qmc.volumeCalcUnit = float(comma2dot(self.unitvolumeEdit.text()))
            self.aw.qmc.volumeCalcWeightInStr = comma2dot(self.coffeeinweightEdit.text())
            self.aw.qmc.volumeCalcWeightOutStr = comma2dot(self.coffeeoutweightEdit.text())
            self.parent_dialog.calculated_density()
        self.accept()

    @pyqtSlot()
    def close(self) -> bool:
        self.closeEvent(None)
        return True


########################################################################################
#####################  RECENT ROAST POPUP  #############################################

class RoastsComboBox(QComboBox): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class
    def __init__(self, parent:QWidget, aw:'ApplicationWindow', selection:Optional[str] = None) -> None:
        super().__init__(parent)
        self.aw:ApplicationWindow = aw
        self.installEventFilter(self)
        self.selection:Optional[str] = selection # just the roast title
        self.edited:Optional[str] = selection
        self.updateMenu()
        self.editTextChanged.connect(self.textEdited)
        self.setEditable(True)
        completer: Optional[QCompleter] = self.completer()
        if completer is not None:
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseSensitive)
#        self.setMouseTracking(False)

    @pyqtSlot(str)
    def textEdited(self, txt:str) -> None:
        cleaned = ' '.join(txt.split())
        self.edited = cleaned

    def getSelection(self) -> Optional[str]:
        return self.edited or self.selection

    def setSelection(self, i:int) -> None:
        if i >= 0:
            try:
                self.edited = None # reset the user text editing
            except Exception: # pylint: disable=broad-except
                pass

    def eventFilter(self, _obj:Optional['QObject'] = None, event:Optional[QEvent] = None) -> bool:
# the next prevents correct setSelection on Windows
#        if event.type() == QEvent.Type.FocusIn:
#            self.setSelection(self.currentIndex())
        if event is not None and event.type() == QEvent.Type.MouseButtonPress:
            self.updateMenu()
#            return True # stops processing # popup not drawn if this line is added
#        return super().eventFilter(obj, event) # this seems to slow down things on Windows and not necessary anyhow
        return False # cont processing

    # the first entry is always just the current text edit line
    def updateMenu(self) -> None:
        self.blockSignals(True)
        try:
            roasts = self.aw.recentRoastsMenuList()
            self.clear()
            if self.edited is None:
                self.addItems(roasts)
            else:
                self.addItems([self.edited] + roasts)
        except Exception: # pylint: disable=broad-except
            pass
        self.blockSignals(False)


########################################################################################
#####################  Roast Properties Dialog  ########################################


class editGraphDlg(ArtisanResizeablDialog):
    scaleWeightUpdated = pyqtSignal(float)
    connectScaleSignal = pyqtSignal()
    readScaleSignal = pyqtSignal()

    def __init__(self, parent:QWidget, aw:'ApplicationWindow', activeTab:int = 0) -> None:
        super().__init__(parent, aw)

        self.ETname = self.aw.qmc.device_name_subst(self.aw.ETname)
        self.BTname = self.aw.qmc.device_name_subst(self.aw.BTname)

        self.activeTab:int = activeTab

        self.setModal(True)
#        self.setWindowModality(Qt.WindowModality.WindowModal)
#        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle(QApplication.translate('Form Caption','Roast Properties'))

        # register per tab if all its widgets and data has been initialized
        # initialization of some tabs is delayed for efficiency reasons until they are opened for the first time
        self.tabInitialized:List[bool] = [False]*6 # 0: Roast, 1: Notes, 2: Events, 3: Data, 4: Energy, 5: Setup

        # we remember user modifications to revert to them on deselecting a plus element
        self.modified_beans:str = self.aw.qmc.beans
        self.modified_density_in_text:str = str(float2float(self.aw.qmc.density[0]))
        self.modified_volume_in_text:str = str(float2float(self.aw.qmc.volume[0]))
        self.modified_beansize_min_text:str = str(self.aw.qmc.beansize_min)
        self.modified_beansize_max_text:str = str(self.aw.qmc.beansize_max)
        self.modified_moisture_greens_text:str = str(self.aw.qmc.moisture_greens)

        # remember parameters set by plus_coffee/plus_blend on entering the dialog to enable a Cancel action
        self.org_beans:str = self.aw.qmc.beans
        self.org_density = self.aw.qmc.density
        self.org_density_roasted = self.aw.qmc.density_roasted
        self.org_beansize_min = self.aw.qmc.beansize_min
        self.org_beansize_max = self.aw.qmc.beansize_max
        self.org_moisture_greens = self.aw.qmc.moisture_greens

        self.org_title = self.aw.qmc.title
        self.org_title_show_always = self.aw.qmc.title_show_always

        self.org_weight = self.aw.qmc.weight
        self.org_volume = self.aw.qmc.volume

        self.org_roasted_defects_mode = self.aw.qmc.roasted_defects_mode

        self.setup_ui:Optional[SetupWidget.Ui_SetupWidget] = None # type:ignore[no-any-unimported,unused-ignore]

        self.pus_amount_selected = None

        self.helpdialog = None # energy help dialog

        self.batcheditmode = False # a click to the batch label enables the batcheditmode

        self.org_perKgRoastMode = self.aw.qmc.perKgRoastMode
        self.perKgRoastMode = self.aw.qmc.perKgRoastMode # if true only the amount during the roast and not the full batch (incl. preheat and BBP) are displayed), toggled by click on the result widget

        self.acaia:'Optional[Acaia]' = None # the BLE interface # noqa: UP037
        self.scale_weight:Optional[float] = None # weight received from a connected scale
        self.scale_battery:Optional[int] = None # battery level of the connected scale in %
        self.scale_set:Optional[float] = None # set weight for accumulation in g

        self.disconnecting = False # this is set to True to terminate the scale connection
        self.volumedialog:Optional[volumeCalculatorDlg] = None # link forward to the the Volume Calculator

        # other parameters remembered for Cancel operation
        self.org_specialevents = self.aw.qmc.specialevents[:]
        self.org_specialeventstype = self.aw.qmc.specialeventstype[:]
        self.org_specialeventsStrings = self.aw.qmc.specialeventsStrings[:]
        self.org_specialeventsvalue = self.aw.qmc.specialeventsvalue[:]
        self.org_timeindex = self.aw.qmc.timeindex[:]
        self.org_phases = self.aw.qmc.phases[:]

        self.org_ambientTemp = self.aw.qmc.ambientTemp
        self.org_ambient_humidity = self.aw.qmc.ambient_humidity
        self.org_ambient_pressure = self.aw.qmc.ambient_pressure

        self.org_roastpropertiesAutoOpenFlag = self.aw.qmc.roastpropertiesAutoOpenFlag
        self.org_roastpropertiesAutoOpenDropFlag = self.aw.qmc.roastpropertiesAutoOpenDropFlag

        # propulated by selecting a recent roast from the popup via recentRoastActivated()
        self.template_file:Optional[str] = None
        self.template_name:Optional[str] = None
        self.template_uuid:Optional[str] = None
        self.template_batchnr:Optional[int] = None
        self.template_batchprefix:Optional[str] = None

        regextime = QRegularExpression(r'^-?[0-9]?[0-9]?[0-9]:[0-5][0-9]$')
        #MARKERS
        chargelabel = QLabel('<b>' + QApplication.translate('Label', 'CHARGE') + '</b>')
        chargelabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        chargelabel.setStyleSheet("background-color:'#f07800';")
        self.chargeeditcopy = stringfromseconds(0)
        self.chargeedit = QLineEdit(self.chargeeditcopy)
#        self.chargeedit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.chargeedit.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.chargeedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.chargeedit.setMaximumWidth(50)
        self.chargeedit.setMinimumWidth(50)
        chargelabel.setBuddy(self.chargeedit)
        drylabel = QLabel('<b>' + QApplication.translate('Label', 'DRY END') + '</b>')
        drylabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        drylabel.setStyleSheet("background-color:'orange';")
        if self.aw.qmc.timeindex[1] and self.aw.qmc.timeindex[1] < len(self.aw.qmc.timex):
            t2 = self.aw.qmc.timex[self.aw.qmc.timeindex[1]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            t2 = 0
        self.dryeditcopy = stringfromseconds(t2)
        self.dryedit = QLineEdit(self.dryeditcopy)
        self.dryedit.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.dryedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.dryedit.setMaximumWidth(50)
        self.dryedit.setMinimumWidth(50)
        drylabel.setBuddy(self.dryedit)
        Cstartlabel = QLabel('<b>' + QApplication.translate('Label','FC START') + '</b>')
        Cstartlabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        Cstartlabel.setStyleSheet("background-color:'orange';")
        if self.aw.qmc.timeindex[2] and self.aw.qmc.timeindex[2] < len(self.aw.qmc.timex):
            t3 = self.aw.qmc.timex[self.aw.qmc.timeindex[2]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            t3 = 0
        self.Cstarteditcopy = stringfromseconds(t3)
        self.Cstartedit = QLineEdit(self.Cstarteditcopy)
#        self.Cstartedit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.Cstartedit.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.Cstartedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.Cstartedit.setMaximumWidth(50)
        self.Cstartedit.setMinimumWidth(50)
        Cstartlabel.setBuddy(self.Cstartedit)

        Cendlabel = QLabel('<b>' + QApplication.translate('Label','FC END') + '</b>')
        Cendlabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        Cendlabel.setStyleSheet("background-color:'orange';")
        if self.aw.qmc.timeindex[3] and self.aw.qmc.timeindex[3] < len(self.aw.qmc.timex):
            t4 = self.aw.qmc.timex[self.aw.qmc.timeindex[3]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            t4 = 0
        self.Cendeditcopy = stringfromseconds(t4)
        self.Cendedit = QLineEdit(self.Cendeditcopy)
#        self.Cendedit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.Cendedit.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.Cendedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.Cendedit.setMaximumWidth(50)
        self.Cendedit.setMinimumWidth(50)
        Cendlabel.setBuddy(self.Cendedit)
        CCstartlabel = QLabel('<b>' + QApplication.translate('Label','SC START') + '</b>')
        CCstartlabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        CCstartlabel.setStyleSheet("background-color:'orange';")
        if self.aw.qmc.timeindex[4] and self.aw.qmc.timeindex[4] < len(self.aw.qmc.timex):
            t5 = self.aw.qmc.timex[self.aw.qmc.timeindex[4]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            t5 = 0
        self.CCstarteditcopy = stringfromseconds(t5)
        self.CCstartedit = QLineEdit(self.CCstarteditcopy)
#        self.CCstartedit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.CCstartedit.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.CCstartedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.CCstartedit.setMaximumWidth(50)
        self.CCstartedit.setMinimumWidth(50)
        CCstartlabel.setBuddy(self.CCstartedit)
        CCendlabel = QLabel('<b>' + QApplication.translate('Label','SC END') + '</b>')
        CCendlabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        CCendlabel.setStyleSheet("background-color:'orange';")
        if self.aw.qmc.timeindex[5] and self.aw.qmc.timeindex[5] < len(self.aw.qmc.timex):
            t6 = self.aw.qmc.timex[self.aw.qmc.timeindex[5]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            t6 = 0
        self.CCendeditcopy = stringfromseconds(t6)
        self.CCendedit = QLineEdit(self.CCendeditcopy)
#        self.CCendedit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.CCendedit.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.CCendedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.CCendedit.setMaximumWidth(50)
        self.CCendedit.setMinimumWidth(50)
        CCendlabel.setBuddy(self.CCendedit)
        droplabel = QLabel('<b>' + QApplication.translate('Label', 'DROP') + '</b>')
        droplabel.setStyleSheet("background-color:'#f07800';")
        droplabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        if self.aw.qmc.timeindex[6] and self.aw.qmc.timeindex[6] < len(self.aw.qmc.timex):
            t7 = self.aw.qmc.timex[self.aw.qmc.timeindex[6]]-(0 if self.aw.qmc.timeindex[0] == -1 else self.aw.qmc.timex[self.aw.qmc.timeindex[0]])
        else:
            t7 = 0
        self.dropeditcopy = stringfromseconds(t7)
        self.dropedit = QLineEdit(self.dropeditcopy)
#        self.dropedit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.dropedit.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.dropedit.setValidator(QRegularExpressionValidator(regextime,self))
        self.dropedit.setMaximumWidth(50)
        self.dropedit.setMinimumWidth(50)
        droplabel.setBuddy(self.dropedit)
        coollabel = QLabel('<b>' + QApplication.translate('Label', 'COOL') + '</b>')
        coollabel.setStyleSheet("background-color:'#6666ff';")
        coollabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        if self.aw.qmc.timeindex[7] and self.aw.qmc.timeindex[7] < len(self.aw.qmc.timex):
            t8 = self.aw.qmc.timex[self.aw.qmc.timeindex[7]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        else:
            t8 = 0
        self.cooleditcopy = stringfromseconds(t8)
        self.cooledit = QLineEdit(self.cooleditcopy)
#        self.cooledit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cooledit.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.cooledit.setValidator(QRegularExpressionValidator(regextime,self))
        self.cooledit.setMaximumWidth(50)
        self.cooledit.setMinimumWidth(50)
        coollabel.setBuddy(self.cooledit)
        self.roastproperties = QCheckBox(QApplication.translate('CheckBox','Delete roast properties on RESET'))
        self.roastproperties.setChecked(bool(self.aw.qmc.roastpropertiesflag))
        self.roastproperties.stateChanged.connect(self.roastpropertiesChanged)
        self.roastpropertiesAutoOpen = QCheckBox(QApplication.translate('CheckBox','Open on CHARGE'))
        self.roastpropertiesAutoOpen.setChecked(bool(self.aw.qmc.roastpropertiesAutoOpenFlag))
        self.roastpropertiesAutoOpen.stateChanged.connect(self.roastpropertiesAutoOpenChanged)
        self.roastpropertiesAutoOpenDROP = QCheckBox(QApplication.translate('CheckBox','Open on DROP'))
        self.roastpropertiesAutoOpenDROP.setChecked(bool(self.aw.qmc.roastpropertiesAutoOpenDropFlag))
        self.roastpropertiesAutoOpenDROP.stateChanged.connect(self.roastpropertiesAutoOpenDROPChanged)
        # EVENTS
        #table for showing events
        self.eventtable = QTableWidget()
        self.eventtable.setTabKeyNavigation(True)
        self.clusterEventsButton = QPushButton(QApplication.translate('Button', 'Cluster'))
        self.clusterEventsButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.clusterEventsButton.setMaximumSize(self.clusterEventsButton.sizeHint())
        self.clusterEventsButton.setMinimumSize(self.clusterEventsButton.minimumSizeHint())
        self.clusterEventsButton.clicked.connect(self.clusterEvents)
        self.clearEventsButton = QPushButton(QApplication.translate('Button', 'Clear'))
        self.clearEventsButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.clearEventsButton.setMaximumSize(self.clearEventsButton.sizeHint())
        self.clearEventsButton.setMinimumSize(self.clearEventsButton.minimumSizeHint())
        self.clearEventsButton.clicked.connect(self.clearEvents)
        self.createalarmTableButton = QPushButton(QApplication.translate('Button', 'Create Alarms'))
        self.createalarmTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.createalarmTableButton.setMaximumSize(self.createalarmTableButton.sizeHint())
        self.createalarmTableButton.setMinimumSize(self.createalarmTableButton.minimumSizeHint())
        self.createalarmTableButton.clicked.connect(self.createAlarmEventTable)
        self.ordereventTableButton = QPushButton(QApplication.translate('Button', 'Order'))
        self.ordereventTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.ordereventTableButton.setMaximumSize(self.ordereventTableButton.sizeHint())
        self.ordereventTableButton.setMinimumSize(self.ordereventTableButton.minimumSizeHint())
        self.ordereventTableButton.clicked.connect(self.orderEventTable)
        self.neweventTableButton = QPushButton(QApplication.translate('Button', 'Add'))
        self.neweventTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.neweventTableButton.setMaximumSize(self.neweventTableButton.sizeHint())
        self.neweventTableButton.setMinimumSize(self.neweventTableButton.minimumSizeHint())
        self.neweventTableButton.clicked.connect(self.addEventTable)
        self.deleventTableButton = QPushButton(QApplication.translate('Button', 'Delete'))
        self.deleventTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.deleventTableButton.setMaximumSize(self.deleventTableButton.sizeHint())
        self.deleventTableButton.setMinimumSize(self.deleventTableButton.minimumSizeHint())
        self.deleventTableButton.clicked.connect(self.deleteEventTable)
        self.copyeventTableButton = QPushButton(QApplication.translate('Button', 'Copy Table'))
        self.copyeventTableButton.setToolTip(QApplication.translate('Tooltip','Copy table to clipboard, OPTION or ALT click for tabular text'))
        self.copyeventTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.copyeventTableButton.setMaximumSize(self.copyeventTableButton.sizeHint())
        self.copyeventTableButton.setMinimumSize(self.copyeventTableButton.minimumSizeHint())
        self.copyeventTableButton.clicked.connect(self.copyEventTabletoClipboard)

        #DATA Table
        self.datatable = QTableWidget()
        self.datatable.setTabKeyNavigation(True)
        self.copydataTableButton = QPushButton(QApplication.translate('Button', 'Copy Table'))
        self.copydataTableButton.setToolTip(QApplication.translate('Tooltip','Copy table to clipboard, OPTION or ALT click for tabular text'))
        self.copydataTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.copydataTableButton.setMaximumSize(self.copydataTableButton.sizeHint())
        self.copydataTableButton.setMinimumSize(self.copydataTableButton.minimumSizeHint())
        self.copydataTableButton.clicked.connect(self.copyDataTabletoClipboard)
        #TITLE
        titlelabel = QLabel('<b>' + QApplication.translate('Label', 'Title') + '</b>')
        self.titleedit = RoastsComboBox(self,self.aw, selection = self.aw.qmc.title)
        self.titleedit.setMinimumWidth(100)
        self.titleedit.setSizePolicy(QSizePolicy.Policy.MinimumExpanding,QSizePolicy.Policy.Fixed)
        self.titleedit.activated.connect(self.recentRoastActivated)
        self.titleedit.editTextChanged.connect(self.recentRoastEnabled)
        if self.aw.app.darkmode:
            if self.aw.qmc.palette['canvas'] is None or self.aw.qmc.palette['canvas'] == 'None':
                canvas_color = 'white'
            else:
                canvas_color = self.aw.qmc.palette['canvas'][:7]
            brightness_title = self.aw.QColorBrightness(QColor(self.aw.qmc.palette['title'][:7]))
            brightness_canvas = self.aw.QColorBrightness(QColor(canvas_color))
            # in dark mode we choose the darker color as background
            if brightness_title > brightness_canvas:
                backgroundcolor = QColor(canvas_color).name()
                color = QColor(self.aw.qmc.palette['title'][:7]).name()
            else:
                backgroundcolor = QColor(self.aw.qmc.palette['title'][:7]).name()
                color = QColor(canvas_color).name()
            self.titleedit.setStyleSheet(
                'QComboBox {padding-left: 2px; padding-right: 2px; padding-top: 1px;  font-weight: bold; background-color: ' + backgroundcolor + '; color: ' + color + ';} QComboBox QAbstractItemView {font-weight: normal;}')
        else:
            color = ''
            if self.aw.qmc.palette['title'] is not None and self.aw.qmc.palette['title'] != 'None':
                color = ' color: ' + QColor(self.aw.qmc.palette['title'][:7]).name() + ';'
            backgroundcolor = ''
            if self.aw.qmc.palette['canvas'] is not None and self.aw.qmc.palette['canvas'] != 'None':
                backgroundcolor = ' background-color: ' + QColor(self.aw.qmc.palette['canvas'][:7]).name() + ';'
            self.titleedit.setStyleSheet(
                'QComboBox {padding-left: 2px; padding-right: 2px; padding-top: 1px; font-weight: bold;' + color + backgroundcolor + '} QComboBox QAbstractItemView {font-weight: normal;}')
        self.titleedit.setView(QListView())
        self.titleShowAlwaysFlag = QCheckBox(QApplication.translate('CheckBox','Show Always'))
        self.titleShowAlwaysFlag.setChecked(self.aw.qmc.title_show_always)
        #Date
        datelabel1 = QLabel('<b>' + QApplication.translate('Label', 'Date') + '</b>')
        date = self.aw.qmc.roastdate.date().toString()
        date += ', ' + self.aw.qmc.roastdate.time().toString()[:-3]
        dateedit = QLineEdit(date)
        dateedit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        dateedit.setReadOnly(True)
        if self.aw.app.darkmode:
            dateedit.setStyleSheet('background-color: #757575; color : white;')
        else:
            dateedit.setStyleSheet('background-color: #eeeeee;')
        #Batch
        batchlabel = ClickableQLabel('<b>' + QApplication.translate('Label', 'Batch') + '</b>')
        batchlabel.right_clicked.connect(self.enableBatchEdit)
        self.batchLayout = QHBoxLayout()
        if self.aw.superusermode: # and self.aw.qmc.batchcounter > -1:
            self.defineBatchEditor()
        else:
            batch = ''
            if self.aw.qmc.roastbatchnr != 0:
                roastpos = ' (' + str(self.aw.qmc.roastbatchpos) + ')'
            else:
                roastpos = ''
            if self.aw.qmc.roastbatchnr == 0:
                batch = ''
            else:
                batch = self.aw.qmc.roastbatchprefix + str(self.aw.qmc.roastbatchnr) + roastpos
            self.batchedit = QLineEdit(batch)
            self.batchedit.setReadOnly(True)
            if self.aw.app.darkmode:
                self.batchedit.setStyleSheet('background-color: #757575; color : white;')
            else:
                self.batchedit.setStyleSheet('background-color: #eeeeee;')
            self.batchedit.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        #Beans
        beanslabel = QLabel('<b>' + QApplication.translate('Label', 'Beans') + '</b>')
        self.beansedit = ClickableTextEdit()
        self.beansedit.editingFinished.connect(self.beansEdited)

        if self.aw.qmc.beans is not None:
            self.beansedit.setNewPlainText(self.aw.qmc.beans)

        #weight
        green_label = QLabel('<b>' + QApplication.translate('Label', 'Green') + '</b>')
        roasted_label = QLabel('<b>' + QApplication.translate('Label', 'Roasted') + '</b>')
        weightlabel = QLabel('<b>' + QApplication.translate('Label', 'Weight') + '</b>')
        self.defectslabel = QLabel()
        inw = f'{float2floatWeightVolume(self.aw.qmc.weight[0]):g}'
        outw = f'{float2floatWeightVolume(self.aw.qmc.weight[1]):g}'
        self.weightinedit = QLineEdit(inw)
        self.weightinedit.setToolTip(QApplication.translate('Tooltip', 'batch size'))
        self.weightinedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, self.weightinedit))  # the max limit has to be high enough otherwise the connected signals are not send!
        self.weightinedit.setMinimumWidth(70)
        self.weightinedit.setMaximumWidth(70)
        self.weightinedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.weightoutedit = QLineEdit(outw)
        self.weightoutedit.setToolTip(QApplication.translate('Tooltip', 'weight of roasted coffee'))
        self.weightoutedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, self.weightoutedit))  # the max limit has to be high enough otherwise the connected signals are not send!
        self.weightoutedit.setMinimumWidth(70)
        self.weightoutedit.setMaximumWidth(70)
        self.weightoutedit.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.weightpercentlabel = QLabel('')
        self.weightpercentlabel.setToolTip(QApplication.translate('Tooltip', 'weight loss caused by roasting'))
        self.weightpercentlabel.setMinimumWidth(55)
        self.weightpercentlabel.setMaximumWidth(55)
        self.weightpercentlabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.percent()
        self.weightinedit.editingFinished.connect(self.weightineditChanged)
        self.weightoutedit.editingFinished.connect(self.weightouteditChanged)
        self.unitsComboBox = QComboBox()
        self.unitsComboBox.setToolTip(QApplication.translate('Tooltip', 'weight unit'))
        self.unitsComboBox.setMaximumWidth(60)
        self.unitsComboBox.setMinimumWidth(60)
        self.unitsComboBox.addItems(weight_units_lower)
        self.unitsComboBox.setCurrentIndex(weight_units.index(self.aw.qmc.weight[2]))
        self.unitsComboBox.currentIndexChanged.connect(self.changeWeightUnit)


        #defects
        dw = (self.aw.qmc.roasted_defects_weight if (self.aw.qmc.roasted_defects_mode or self.aw.qmc.roasted_defects_weight == 0) else
            (0 if self.aw.qmc.weight[1] == 0 else min(self.aw.qmc.weight[1], max(0, self.aw.qmc.weight[1] - self.aw.qmc.roasted_defects_weight))))
        defectsw = f'{float2floatWeightVolume(dw):g}'
        self.weightoutdefectsedit = QLineEdit()
        self.weightoutdefectsedit.setToolTip(QApplication.translate('Tooltip', 'weight of defects sorted from roasted coffee or weight of roasted coffee after defects have been removed'))
        if self.aw.qmc.roasted_defects_mode or defectsw != '0':
            self.weightoutdefectsedit.setText(defectsw)
        self.weightoutdefectsedit.setPlaceholderText(self.weightoutedit.text())
        self.weightoutdefectsedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, self.weightoutdefectsedit))  # the max limit has to be high enough otherwise the connected signals are not send!
        self.weightoutdefectsedit.setMinimumWidth(70)
        self.weightoutdefectsedit.setMaximumWidth(70)
        self.weightoutdefectsedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.weightoutdefects_unit_label = QLabel(self.aw.qmc.weight[2].lower())
        self.weightoutdefects_unit_label.setToolTip(QApplication.translate('Tooltip', 'weight unit of defects'))
        self.weightoutdefectspercentlabel = QLabel()
        self.weightoutdefectspercentlabel.setToolTip(QApplication.translate('Tooltip', 'weight loss caused by defects'))
        weightoutdefectsToggle = QPushButton('<>')
        weightoutdefectsToggle.setToolTip(QApplication.translate('Tooltip', 'toggle defects input mode'))
        weightoutdefectsToggle.setMaximumWidth(40)
        weightoutdefectsToggle.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        weightoutdefectsToggle.clicked.connect(self.toggleWeightOutDefects)
        self.weightoutdefectsedit.editingFinished.connect(self.weightoutdefectsChanged)
        self.defect_percent()

        #volume
        volumelabel = QLabel('<b>' + QApplication.translate('Label', 'Volume') + '</b>')
        inv = f'{float2floatWeightVolume(self.aw.qmc.volume[0]):g}'
        outv = f'{float2floatWeightVolume(self.aw.qmc.volume[1]):g}'
        self.volumeinedit = QLineEdit(inv)
        self.volumeinedit.setToolTip(QApplication.translate('Tooltip', 'batch volume'))
        self.volumeinedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999999., 4, self.volumeinedit)) # the max limit has to be high enough otherwise the connected signals are not send!
        self.volumeinedit.setMinimumWidth(70)
        self.volumeinedit.setMaximumWidth(70)
        self.volumeinedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.volumeoutedit = QLineEdit(outv)
        self.volumeoutedit.setToolTip(QApplication.translate('Tooltip', 'volume of roasted coffee'))
        self.volumeoutedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999999., 4, self.volumeoutedit)) # the max limit has to be high enough otherwise the connected signals are not send!
        self.volumeoutedit.setMinimumWidth(70)
        self.volumeoutedit.setMaximumWidth(70)
        self.volumeoutedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.volumepercentlabel = QLabel('')
        self.weightpercentlabel.setToolTip(QApplication.translate('Tooltip', 'volume increase caused by roasting'))
        self.volumepercentlabel.setMinimumWidth(55)
        self.volumepercentlabel.setMaximumWidth(55)
        self.volumepercentlabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.volumeoutedit.editingFinished.connect(self.volume_out_editing_finished)
        self.volumeinedit.editingFinished.connect(self.volume_in_editing_finished)
        self.volumeUnitsComboBox = QComboBox()
        self.volumeUnitsComboBox.setToolTip(QApplication.translate('Tooltip', 'volume unit'))
        self.volumeUnitsComboBox.setMaximumWidth(60)
        self.volumeUnitsComboBox.setMinimumWidth(60)
        self.volumeUnitsComboBox.addItems(volume_units)
        self.volumeUnitsComboBox.setCurrentIndex(volume_units.index(self.aw.qmc.volume[2]))
        self.volumeUnitsComboBox.currentIndexChanged.connect(self.changeVolumeUnit)
        self.unitsComboBox.currentIndexChanged.connect(self.calculated_density)
        #density
        bean_density_label = QLabel('<b>' + QApplication.translate('Label', 'Density') + '</b>')
        density_unit_label = QLabel('g/l')
        density_unit_label.setToolTip(QApplication.translate('Tooltip', 'density unit'))
        self.bean_density_in_edit = QLineEdit(f'{float2float(self.aw.qmc.density[0]):g}')
        self.bean_density_in_edit.setToolTip(QApplication.translate('Tooltip', 'batch density'))
        self.bean_density_in_edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999999., 1,self.bean_density_in_edit))
        self.bean_density_in_edit.setMinimumWidth(70)
        self.bean_density_in_edit.setMaximumWidth(70)
        self.bean_density_in_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.bean_density_out_edit = QLineEdit(f'{float2float(self.aw.qmc.density_roasted[0]):g}')
        self.bean_density_out_edit.setToolTip(QApplication.translate('Tooltip', 'density of roasted coffee'))
        self.bean_density_out_edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999999., 1,self.bean_density_out_edit))
        self.bean_density_out_edit.setMinimumWidth(70)
        self.bean_density_out_edit.setMaximumWidth(70)
        self.bean_density_out_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.bean_density_in_edit.editingFinished.connect(self.density_in_editing_finished)
        self.bean_density_out_edit.editingFinished.connect(self.density_out_editing_finished)
        self.densitypercentlabel = QLabel('')
        self.densitypercentlabel.setToolTip(QApplication.translate('Tooltip', 'density loss caused by roasting'))
        self.densitypercentlabel.setMinimumWidth(55)
        self.densitypercentlabel.setMaximumWidth(55)
        self.densitypercentlabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.organicpercentlabel = QLabel('')
        self.organicpercentlabel.setToolTip(QApplication.translate('Tooltip', 'loss of organic matters caused by roasting'))
        self.organicpercentlabel.setMinimumWidth(55)
        self.organicpercentlabel.setMaximumWidth(55)
        self.organicpercentlabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # volume calc button
        volumeCalcButton = QToolButton()
        volumeCalcButton.setToolTip(QApplication.translate('Tooltip', 'Volume calculator to determine coffee volume from sample weight measured in container of known volume'))
        volumeCalcButton.setText('...')

        volumeCalcButton.clicked.connect(self.volumeCalculatorTimer)
        #the size of Buttons on the Mac is too small with 70,30 and ok with sizeHint/minimumSizeHint
        volumeCalcButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # add to recent
        self.addRecentButton = QPushButton('+')
        self.addRecentButton.clicked.connect(self.addRecentRoast)
        self.addRecentButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.addRecentButton.setToolTip(QApplication.translate('Tooltip','Add roast properties to list of recent roasts'))

        # delete from recent
        self.delRecentButton = QPushButton('-')
        self.delRecentButton.clicked.connect(self.delRecentRoast)
        self.delRecentButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.delRecentButton.setToolTip(QApplication.translate('Tooltip','Remove roast properties from list of recent roasts'))

        self.recentRoastEnabled()

        #bean size
        bean_size_label = QLabel('<b>' + QApplication.translate('Label', 'Screen') + '</b>')
        self.bean_size_min_edit = QLineEdit(str(int(round(self.aw.qmc.beansize_min))))
        self.bean_size_min_edit.setToolTip(QApplication.translate('Tooltip', 'smallest screen size'))
        self.bean_size_min_edit.editingFinished.connect(self.beanSizeMinEdited)
        self.bean_size_min_edit.setValidator(QIntValidator(0,50,self.bean_size_min_edit))
        self.bean_size_min_edit.setMinimumWidth(25)
        self.bean_size_min_edit.setMaximumWidth(25)
        self.bean_size_min_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        bean_size_sep_label = QLabel('/')
        self.bean_size_max_edit = QLineEdit(str(int(round(self.aw.qmc.beansize_max))))
        self.bean_size_max_edit.setToolTip(QApplication.translate('Tooltip', 'largest screen size'))
        self.bean_size_max_edit.editingFinished.connect(self.beanSizeMaxEdited)
        self.bean_size_max_edit.setValidator(QIntValidator(0,50,self.bean_size_max_edit))
        self.bean_size_max_edit.setMinimumWidth(25)
        self.bean_size_max_edit.setMaximumWidth(25)
        self.bean_size_max_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        bean_size_unit_label = QLabel('18/64\u2033')
        #bean color
        color_label = QLabel('<b>' + QApplication.translate('Label', 'Color') + '</b>')
        whole_color_label = QLabel('<b>' + QApplication.translate('Label', 'Whole') + '</b>')
        self.whole_color_edit = QLineEdit(str(self.aw.qmc.whole_color))
        self.whole_color_edit.setToolTip(QApplication.translate('Tooltip', 'color measurement of whole roasted beans'))
        self.whole_color_edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 2, self.whole_color_edit))
        self.whole_color_edit.setMinimumWidth(70)
        self.whole_color_edit.setMaximumWidth(70)
        self.whole_color_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        ground_color_label = QLabel('<b>' + QApplication.translate('Label', 'Ground') + '</b>')
        self.ground_color_edit = QLineEdit(str(self.aw.qmc.ground_color))
        self.ground_color_edit.setToolTip(QApplication.translate('Tooltip', 'color measurement of ground roasted beans'))
        self.ground_color_edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 2, self.ground_color_edit))
        self.ground_color_edit.setMinimumWidth(70)
        self.ground_color_edit.setMaximumWidth(70)
        self.ground_color_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.bean_size_min_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.bean_size_max_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.colorSystemComboBox = QComboBox()
        self.colorSystemComboBox.setToolTip(QApplication.translate('Tooltip', 'color scale'))
        self.colorSystemComboBox.addItems(self.aw.qmc.color_systems)
        if isinstance(self.aw.qmc.color_system_idx, int):
            self.colorSystemComboBox.setCurrentIndex(self.aw.qmc.color_system_idx)
        else: # in older versions this could have been a string
            self.aw.qmc.color_system_idx = 0 # type: ignore[unreachable]
        #Greens Temp
        greens_temp_label = QLabel('<b>' + QApplication.translate('Label', 'Beans') + '</b>')
        greens_temp_unit_label = QLabel(self.aw.qmc.mode)
        self.greens_temp_edit = QLineEdit()
        self.greens_temp_edit.setToolTip(QApplication.translate('Tooltip', 'temperature of the green coffee'))
        self.greens_temp_edit.setText(f'{float2float(self.aw.qmc.greens_temp):g}')
        self.greens_temp_edit.setMaximumWidth(60)
        self.greens_temp_edit.setValidator(self.aw.createCLocaleDoubleValidator(-9999., 999999., 1, self.greens_temp_edit)) # range to 1000 needed to trigger editing_finished on input "12,2"
        self.greens_temp_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.greens_temp_edit.editingFinished.connect(self.greens_temp_editing_finished)
        greens_temp = QHBoxLayout()
        greens_temp.addStretch()
        #Moisture Greens
        moisture_label = QLabel('<b>' + QApplication.translate('Label', 'Moisture') + '</b>')
        moisture_greens_unit_label = QLabel(QApplication.translate('Label', '%'))
        moisture_greens_unit_label.setToolTip(QApplication.translate('Tooltip', 'moisture unit'))
        self.moisture_greens_edit = QLineEdit()
        self.moisture_greens_edit.setToolTip(QApplication.translate('Tooltip', 'batch moisture'))
        self.moisture_greens_edit.setText(f'{float2float(self.aw.qmc.moisture_greens):g}')
        self.moisture_greens_edit.setMaximumWidth(70)
        self.moisture_greens_edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 100., 1, self.moisture_greens_edit))
        self.moisture_greens_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        #bag humidity
        self.moisture_greens_edit.setToolTip(QApplication.translate('Tooltip', 'batch moisture'))
        self.moisture_roasted_edit = QLineEdit()
        self.moisture_roasted_edit.setToolTip(QApplication.translate('Tooltip', 'moisture of roasted coffee'))
        self.moisture_roasted_edit.setText(f'{float2float(self.aw.qmc.moisture_roasted):g}')
        self.moisture_roasted_edit.setMaximumWidth(70)
        self.moisture_roasted_edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 100., 1, self.moisture_roasted_edit))
        self.moisture_roasted_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.moisturepercentlabel = QLabel('')
        self.moisturepercentlabel.setToolTip(QApplication.translate('Tooltip', 'moisture loss caused by roasting'))
        self.moisturepercentlabel.setMinimumWidth(55)
        self.moisturepercentlabel.setMaximumWidth(55)
        self.moisturepercentlabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.moisture_greens_edit.editingFinished.connect(self.moistureEdited)
        self.moisture_roasted_edit.editingFinished.connect(self.moistureEdited)

        #Ambient temperature (uses display mode as unit (F or C)
        ambientlabel = QLabel('<b>' + QApplication.translate('Label', 'Ambient Conditions') + '</b>')
        ambientunitslabel = QLabel(self.aw.qmc.mode)
        ambient_humidity_unit_label = QLabel(QApplication.translate('Label', '%'))
        self.ambient_humidity_edit = QLineEdit()
        self.ambient_humidity_edit.setToolTip(QApplication.translate('Tooltip','ambient humidity'))
        self.ambient_humidity_edit.setText(f'{float2float(self.aw.qmc.ambient_humidity):g}')
        self.ambient_humidity_edit.setMinimumWidth(50)
        self.ambient_humidity_edit.setMaximumWidth(50)
        self.ambient_humidity_edit.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 1, self.ambient_humidity_edit))
        self.ambient_humidity_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.ambient_humidity_edit.editingFinished.connect(self.ambient_humidity_editing_finished)
        self.ambientedit = QLineEdit()
        self.ambientedit.setToolTip(QApplication.translate('Tooltip','ambient air temperature'))
        self.ambientedit.setText(f'{float2float(self.aw.qmc.ambientTemp):g}')
        self.ambientedit.setMinimumWidth(50)
        self.ambientedit.setMaximumWidth(50)
        self.ambientedit.setValidator(self.aw.createCLocaleDoubleValidator(-9999., 9999999., 1, self.ambientedit))  # larger range needed to trigger editing_finished
        self.ambientedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.ambientedit.editingFinished.connect(self.ambientedit_editing_finished)
        pressureunitslabel = QLabel('hPa')
        self.pressureedit = QLineEdit()
        self.pressureedit.setToolTip(QApplication.translate('Tooltip','ambient air pressure'))
        self.pressureedit.setText(f'{float2float(self.aw.qmc.ambient_pressure):g}')
        self.pressureedit.setMinimumWidth(55)
        self.pressureedit.setMaximumWidth(55)
        self.pressureedit.setValidator(self.aw.createCLocaleDoubleValidator(0, 9999999., 1, self.pressureedit))
        self.pressureedit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pressureedit.editingFinished.connect(self.pressureedit_editing_finished)
        ambient = QHBoxLayout()
        ambient.addWidget(self.ambient_humidity_edit)
        ambient.addSpacing(1)
        ambient.addWidget(ambient_humidity_unit_label)
        ambient.addSpacing(7)
        ambient.addWidget(self.ambientedit)
        ambient.addSpacing(1)
        ambient.addWidget(ambientunitslabel)
        ambient.addSpacing(7)
        ambient.addWidget(self.pressureedit)
        ambient.addSpacing(1)
        ambient.addWidget(pressureunitslabel)
        ambient.addStretch()
        self.organiclosslabel = QLabel()
        self.scaleWeight = QLabel()
        self.scaleWeight.setToolTip(QApplication.translate('Tooltip','weight measured by connected scale'))
        self.scaleWeightAccumulated = ClickableQLabel('')
        self.scaleWeightAccumulated.setToolTip(QApplication.translate('Tooltip','accumulated weight received from connected scale'))
        self.scaleWeightAccumulated.clicked.connect(self.resetScaleSet)
        # NOTES
        roastinglabel = QLabel('<b>' + QApplication.translate('Label', 'Roasting Notes') + '</b>')
        self.roastingeditor = QTextEdit()
#        self.roastingeditor.setMaximumHeight(125)
        if self.aw.qmc.roastingnotes is not None:
            self.roastingeditor.setPlainText(self.aw.qmc.roastingnotes)
        cuppinglabel = QLabel('<b>' + QApplication.translate('Label', 'Cupping Notes') + '</b>')
        self.cuppingeditor =  QTextEdit()
#        self.cuppingeditor.setMaximumHeight(125)
        if self.aw.qmc.cuppingnotes is not None:
            self.cuppingeditor.setPlainText(self.aw.qmc.cuppingnotes)
        # Flags
        self.heavyFC = QCheckBox(QApplication.translate('CheckBox','Heavy FC'))
        self.heavyFC.setChecked(self.aw.qmc.heavyFC_flag)
        self.heavyFC.stateChanged.connect(self.roastflagHeavyFCChanged)
        self.lowFC = QCheckBox(QApplication.translate('CheckBox','Low FC'))
        self.lowFC.setChecked(self.aw.qmc.lowFC_flag)
        self.lowFC.stateChanged.connect(self.roastflagLowFCChanged)
        self.lightCut = QCheckBox(QApplication.translate('CheckBox','Light Cut'))
        self.lightCut.setChecked(self.aw.qmc.lightCut_flag)
        self.lightCut.stateChanged.connect(self.roastflagLightCutChanged)
        self.darkCut = QCheckBox(QApplication.translate('CheckBox','Dark Cut'))
        self.darkCut.setChecked(self.aw.qmc.darkCut_flag)
        self.darkCut.stateChanged.connect(self.roastflagDarkCutChanged)
        self.drops = QCheckBox(QApplication.translate('CheckBox','Drops'))
        self.drops.setChecked(self.aw.qmc.drops_flag)
        self.drops.stateChanged.connect(self.roastflagDropsChanged)
        self.oily = QCheckBox(QApplication.translate('CheckBox','Oily'))
        self.oily.setChecked(self.aw.qmc.oily_flag)
        self.oily.stateChanged.connect(self.roastflagOilyChanged)
        self.uneven = QCheckBox(QApplication.translate('CheckBox','Uneven'))
        self.uneven.setChecked(self.aw.qmc.uneven_flag)
        self.tipping = QCheckBox(QApplication.translate('CheckBox','Tipping'))
        self.tipping.setChecked(self.aw.qmc.tipping_flag)
        self.scorching = QCheckBox(QApplication.translate('CheckBox','Scorching'))
        self.scorching.setChecked(self.aw.qmc.scorching_flag)
        self.divots = QCheckBox(QApplication.translate('CheckBox','Divots'))
        self.divots.setChecked(self.aw.qmc.divots_flag)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.accept)
        self.dialogbuttons.rejected.connect(self.closeEvent)

        # container tare
        self.tareComboBox = QComboBox()
        self.tareComboBox.setToolTip(QApplication.translate('Tooltip', 'container selector'))
#        self.tareComboBox.setMaximumWidth(80)
        self.tareComboBox.setMinimumWidth(80)
        self.updateTarePopup(adjust_index=False)
        self.tareComboBox.setCurrentIndex(self.aw.qmc.container_idx + 3)
        self.tareComboBox.currentIndexChanged.connect(self.tareChanged)

        # in button
        inButton = QPushButton(QApplication.translate('Button', 'in'))
        inButton.setToolTip(QApplication.translate('Tooltip', 'set scale weight as batch size'))
        inButton.clicked.connect(self.inWeight)
        #the size of Buttons on the Mac is too small with 70,30 and ok with sizeHint/minimumSizeHint
        inButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        inButton.setMinimumWidth(80)
        inButtonLayout = QHBoxLayout()
        inButtonLayout.addStretch()
        inButtonLayout.addWidget(inButton)
        inButtonLayout.addStretch()
        # out button
        outButton = QPushButton(QApplication.translate('Button', 'out'))
        outButton.setToolTip(QApplication.translate('Tooltip', 'set scale weight as weight of roasted coffee'))
        outButton.clicked.connect(self.outWeight)
        #the size of Buttons on the Mac is too small with 70,30 and ok with sizeHint/minimumSizeHint
        outButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        outButton.setMinimumWidth(80)
        outButtonLayout = QHBoxLayout()
        outButtonLayout.addStretch()
        outButtonLayout.addWidget(outButton)
        outButtonLayout.addStretch()

        # defects button
        self.defectsButton = QPushButton()
        self.defectsButton.setToolTip(QApplication.translate('Tooltip', 'set scale weight as weight of defects or yield'))
        self.defectsButton.setText(QApplication.translate('Button', 'defects') if self.aw.qmc.roasted_defects_mode else QApplication.translate('Button', 'yield'))
        self.defectsButton.clicked.connect(self.defectsWeight)
        #the size of Buttons on the Mac is too small with 70,30 and ok with sizeHint/minimumSizeHint
        self.defectsButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.defectsButton.setMinimumWidth(80)
        defectsButtonLayout = QHBoxLayout()
        defectsButtonLayout.addStretch()
        defectsButtonLayout.addWidget(self.defectsButton)
        defectsButtonLayout.addStretch()

        self.updateWeightOutDefectsLabel()

        # scan whole button
        scanWholeButton = QPushButton(QApplication.translate('Button', 'scan'))
        scanWholeButton.clicked.connect(self.scanWholeColor)
        scanWholeButton.setMinimumWidth(80)
        #the size of Buttons on the Mac is too small with 70,30 and ok with sizeHint/minimumSizeHint
        scanWholeButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # scan ground button
        scanGroundButton = QPushButton(QApplication.translate('Button', 'scan'))
        scanGroundButton.setMinimumWidth(80)
        scanGroundButton.clicked.connect(self.scanGroundColor)
        #the size of Buttons on the Mac is too small with 70,30 and ok with sizeHint/minimumSizeHint
        scanGroundButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # Ambient Temperature Source Selector
        self.ambientComboBox = QComboBox()
        self.ambientComboBox.addItems(self.buildAmbientTemperatureSourceList())
        self.ambientComboBox.setCurrentIndex(self.aw.qmc.ambientTempSource)
        self.ambientComboBox.currentIndexChanged.connect(self.ambientComboBoxIndexChanged)
        ambientSourceLabel = QLabel(QApplication.translate('Label', 'Ambient Source'))
        updateAmbientTemp = QPushButton(QApplication.translate('Button', 'update'))
        updateAmbientTemp.setToolTip(QApplication.translate('Tooltip','retreive ambient data from connected devices or calculate from selected profile curve'))
        updateAmbientTemp.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        updateAmbientTemp.clicked.connect(self.updateAmbientTemp)
        ##### LAYOUTS
        timeLayout = QGridLayout()
        timeLayout.setVerticalSpacing(3)
        timeLayout.setHorizontalSpacing(3)
        timeLayout.addWidget(chargelabel,0,0)
        timeLayout.addWidget(drylabel,0,1)
        timeLayout.addWidget(Cstartlabel,0,2)
        timeLayout.addWidget(Cendlabel,0,3)
        timeLayout.addWidget(CCstartlabel,0,4)
        timeLayout.addWidget(CCendlabel,0,5)
        timeLayout.addWidget(droplabel,0,6)
        timeLayout.addWidget(coollabel,0,7)
        timeLayout.addWidget(self.chargeedit,1,0,Qt.AlignmentFlag.AlignHCenter)
        timeLayout.addWidget(self.dryedit,1,1,Qt.AlignmentFlag.AlignHCenter)
        timeLayout.addWidget(self.Cstartedit,1,2,Qt.AlignmentFlag.AlignHCenter)
        timeLayout.addWidget(self.Cendedit,1,3,Qt.AlignmentFlag.AlignHCenter)
        timeLayout.addWidget(self.CCstartedit,1,4,Qt.AlignmentFlag.AlignHCenter)
        timeLayout.addWidget(self.CCendedit,1,5,Qt.AlignmentFlag.AlignHCenter)
        timeLayout.addWidget(self.dropedit,1,6,Qt.AlignmentFlag.AlignHCenter)
        timeLayout.addWidget(self.cooledit,1,7,Qt.AlignmentFlag.AlignHCenter)
        textLayout = QGridLayout()
        textLayout.setHorizontalSpacing(3)
        textLayout.setVerticalSpacing(2)
        textLayout.setContentsMargins(0,0,0,0)
        textLayout.addWidget(datelabel1,0,0)
        datebatch = QHBoxLayout()
        datebatch.addWidget(dateedit)
        datebatch.addSpacing(15)
        datebatch.addWidget(batchlabel)
        datebatch.addSpacing(7)
        datebatch.addLayout(self.batchLayout)
        if not self.aw.superusermode: # and self.aw.qmc.batchcounter > -1:
            self.batchLayout.addWidget(self.batchedit)
        textLayout.addLayout(datebatch,0,1)

        titleLine = QHBoxLayout()
        titleLine.addWidget(self.titleedit)
        titleLine.addWidget(self.addRecentButton)
        titleLine.addWidget(self.delRecentButton)
        titleLine.addSpacing(2)
        titleLine.addWidget(self.titleShowAlwaysFlag)

        self.template_line = QLabel('P249 Guatemala')
        template_font = self.template_line.font()
        template_font.setPointSize(template_font.pointSize() -1)
        self.template_line.setFont(template_font)

#PLUS
        self.plus_store_selected:Optional[str] = None # holds the hr_id of the store of the selected coffee or blend
        self.plus_store_selected_label:Optional[str] = None # the label of the selected store
        self.plus_coffee_selected:Optional[str] = None # holds the hr_id of the selected coffee
        self.plus_coffee_selected_label:Optional[str] = None # the label of the selected coffee
        self.plus_blend_selected_label:Optional[str] = None # the name of the selected blend
        self.plus_blend_selected_spec:Optional[Blend] = None # holds the blend dict specification of the selected blend
        self.plus_blend_selected_spec_labels:Optional[List[str]] = None # the list of coffee labels of the selected blend specification
        if self.aw.plus_account is not None:
            plus.stock.init() # we try to init the stock from the cache before populating the popups
            # variables populated by stock data as rendered in the corresponding popups
            self.plus_stores:Optional[List[Tuple[str, str]]] = None
            self.plus_coffees:Optional[List[Tuple[str, Tuple[plus.stock.Coffee, plus.stock.StockItem]]]] = None
            self.plus_blends:Optional[List[plus.stock.BlendStructure]] = None
            self.plus_default_store = self.aw.qmc.plus_default_store
            # current selected stock/coffee/blend _id
            if self.aw.qmc.plus_store is not None:
                self.plus_store_selected = self.aw.qmc.plus_store # holds the store corresponding to the plus_coffee_selected/plus_blend_selected
                self.plus_store_selected_label = self.aw.qmc.plus_store_label
            if self.aw.qmc.plus_coffee is not None:
                self.plus_coffee_selected = self.aw.qmc.plus_coffee
                self.plus_coffee_selected_label = self.aw.qmc.plus_coffee_label
            elif self.aw.qmc.plus_blend_spec is not None:
                self.plus_blend_selected_label = self.aw.qmc.plus_blend_label
                self.plus_blend_selected_spec = self.aw.qmc.plus_blend_spec
                self.plus_blend_selected_spec_labels = self.aw.qmc.plus_blend_spec_labels
            self.plus_amount_selected:Optional[float] = None # holds the max amount of the selected coffee/blend if known
            self.plus_amount_replace_selected:Optional[float] = None # holds the max amount of the selected coffee/blend incl. replacements if known
            plusCoffeeslabel = QLabel('<b>' + QApplication.translate('Label', 'Stock') + '</b>')
            self.plusStoreslabel = QLabel('<b>' + QApplication.translate('Label', 'Store') + '</b>')
            self.plusBlendslabel = QLabel('<b>' + QApplication.translate('Label', 'Blend') + '</b>')
            self.plus_stores_combo = MyQComboBox(self)
            self.plus_coffees_combo = CoffeesComboBox(self)
            self.plus_blends_combo = BlendsComboBox(self)
            self.plus_stores_combo.currentIndexChanged.connect(self.storeSelectionChanged)
            self.plus_coffees_combo.currentIndexChanged.connect(self.coffeeSelectionChanged)
            self.plus_blends_combo.currentIndexChanged.connect(self.blendSelectionChanged)
            self.plus_custom_blend_button = QToolButton()
            self.plus_custom_blend_button.setText('...')
            self.plus_custom_blend_button.clicked.connect(self.customBlendButton_triggered)
            self.plus_selected_line = QLabel()
            self.plus_selected_line.setOpenExternalLinks(True)
            label_font = self.plus_selected_line.font()
            label_font.setPointSize(label_font.pointSize() -2)
            self.plus_selected_line.setFont(label_font)
            # layouting
            self.plus_coffees_combo.setMinimumContentsLength(15)
            self.plus_blends_combo.setMinimumContentsLength(10)
            self.plus_stores_combo.setMinimumContentsLength(10)
            self.plus_stores_combo.setMaximumWidth(130)
            self.plus_coffees_combo.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
            self.plus_coffees_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            self.plus_blends_combo.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
            self.plus_blends_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            self.plus_stores_combo.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
            self.plus_stores_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            # plus widget row

            plusLineStores = QHBoxLayout()
            plusLineStores.addSpacing(10)
            plusLineStores.addWidget(self.plusStoreslabel)
            plusLineStores.addSpacing(5)
            plusLineStores.addWidget(self.plus_stores_combo)
            plusLineStores.setContentsMargins(0, 0, 0, 0) # left, top, right, bottom
            plusLineStores.setSpacing(5)

            self.plusLineStoresFrame = QFrame()
            self.plusLineStoresFrame.setLayout(plusLineStores)

            plusLine = QHBoxLayout()
            plusLine.addWidget(self.plus_coffees_combo)
            plusLine.addSpacing(10)
            plusLine.addWidget(self.plusBlendslabel)
            plusLine.addSpacing(4)
            plusLine.addWidget(self.plus_blends_combo)
            plusLine.addWidget(self.plus_custom_blend_button)
            plusLine.addWidget(self.plusLineStoresFrame)

            plusLine.setStretch(0, 3)
            plusLine.setStretch(4, 2)
            plusLine.setStretch(6, 1)

            self.label_origin_flag = QCheckBox(QApplication.translate('CheckBox','Standard bean labels'))
            self.label_origin_flag.setToolTip(QApplication.translate('Tooltip',"Beans are listed as 'origin, name' if ticked, otherwise as 'name, origin'"))
            self.label_origin_flag.setChecked(bool(plus.stock.coffee_label_normal_order))
            self.label_origin_flag.stateChanged.connect(self.labelOriginFlagChanged)

            selectedLineLayout = QHBoxLayout()
            selectedLineLayout.addWidget(self.plus_selected_line)
            selectedLineLayout.addStretch()
            selectedLineLayout.addWidget(self.label_origin_flag)
            textLayout.addLayout(selectedLineLayout,4,1)
            textLayout.addWidget(plusCoffeeslabel,5,0)
            textLayout.addLayout(plusLine,5,1)
            textLayoutPlusOffset = 2 # to insert the plus widget row, we move the remaining ones one step lower
        else:
            textLayoutPlusOffset = 0
        textLayout.addWidget(self.template_line,2,1)
        textLayout.addWidget(titlelabel,3,0)
        textLayout.addLayout(titleLine,3,1)
        textLayout.addWidget(beanslabel,4+textLayoutPlusOffset,0)
        textLayout.addWidget(self.beansedit,4+textLayoutPlusOffset,1)

        beanSizeLayout = QHBoxLayout()
        beanSizeLayout.setSpacing(2)
        beanSizeLayout.addStretch()
        beanSizeLayout.addWidget(self.bean_size_min_edit)
        beanSizeLayout.addWidget(bean_size_sep_label)
        beanSizeLayout.addWidget(self.bean_size_max_edit)
        beanSizeLayout.addStretch()

        propGrid = QGridLayout()
        propGrid.setContentsMargins(0,0,0,0)
        propGrid.setHorizontalSpacing(3)
        propGrid.setVerticalSpacing(0)
        propGrid.addWidget(green_label,0,1,Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        propGrid.addWidget(roasted_label,0,2,Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        propGrid.addWidget(self.organicpercentlabel,0,4,Qt.AlignmentFlag.AlignRight)
        propGrid.addWidget(self.organiclosslabel,0,5,1,3,Qt.AlignmentFlag.AlignLeft)
        propGrid.addWidget(self.scaleWeight,0,8,1,2,Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)

        propGrid.setRowMinimumHeight(1,self.volumeUnitsComboBox.minimumSizeHint().height())
        propGrid.addWidget(weightlabel,1,0,Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.weightinedit,1,1,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.weightoutedit,1,2,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.unitsComboBox,1,3)
        propGrid.addWidget(self.weightpercentlabel,1,4,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

        propGrid.setRowMinimumHeight(2,self.volumeUnitsComboBox.minimumSizeHint().height())
        propGrid.addWidget(self.defectslabel,2,0,Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(weightoutdefectsToggle,2,1,Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.weightoutdefectsedit,2,2,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.weightoutdefects_unit_label,2,3,Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.weightoutdefectspercentlabel,2,4,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

        propGrid.setColumnStretch(5,10)

        if self.aw.scale.device is not None and self.aw.scale.device not in {'', 'None'}:
            propGrid.addWidget(self.tareComboBox,1,6,1,2) # rowSpan=1, columnSpan=3
            propGrid.addLayout(inButtonLayout,1,8)
            propGrid.addLayout(outButtonLayout,1,9)
            propGrid.addLayout(defectsButtonLayout,2,9)


            if self.aw.scale.device == 'acaia' and not (platform.system() == 'Windows' and math.floor(toFloat(platform.release())) < 10):
                # BLE is not well supported under Windows versions before Windows 10
                try:
                    from artisanlib.acaia import Acaia
                    self.acaia = Acaia(
                        model = 1,
                        ident = None,
                        name = 'Acaia',
                        connected_handler=lambda : self.aw.sendmessageSignal.emit(QApplication.translate('Message', '{} connected').format('Acaia'),True,None),
                        disconnected_handler=lambda : self.aw.sendmessageSignal.emit(QApplication.translate('Message', '{} disconnected').format('Acaia'),True,None))
                    self.acaia.weight_changed_signal.connect(self.ble_weight_changed)
                    self.acaia.battery_changed_signal.connect(self.ble_battery_changed)
                    self.acaia.disconnected_signal.connect(self.ble_disconnected)
                    # start BLE loop
                    self.acaia.start()

                    self.updateWeightLCD('----')
                except Exception as e:  # pylint: disable=broad-except
                    _log.exception(e)
            elif self.aw.scale.device in {'KERN NDE','Shore 930'}:
                self.connectScaleSignal.connect(self.connectScaleLoop)
                QTimer.singleShot(2,lambda : self.connectScaleSignal.emit()) # pylint: disable= unnecessary-lambda

        propGrid.setRowMinimumHeight(3,volumeCalcButton.minimumSizeHint().height())
        propGrid.addWidget(volumelabel,3,0,Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.volumeinedit,3,1,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.volumeoutedit,3,2,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.volumeUnitsComboBox,3,3,Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.volumepercentlabel,3,4,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

        calcButtonLayout = QHBoxLayout()
        calcButtonLayout.addSpacing(5)
        calcButtonLayout.addWidget(volumeCalcButton)
        calcButtonLayout.addStretch()
        propGrid.addLayout(calcButtonLayout,3,5,Qt.AlignmentFlag.AlignVCenter)

        propGrid.addWidget(self.scaleWeightAccumulated,3,8,1,2,Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)

        propGrid.setRowMinimumHeight(4,self.volumeUnitsComboBox.minimumSizeHint().height())
        propGrid.addWidget(bean_density_label,4,0,Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.bean_density_in_edit,4,1,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.bean_density_out_edit,4,2,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(density_unit_label,4,3,Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.densitypercentlabel,4,4,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

        propGrid.addWidget(bean_size_label,4,7,Qt.AlignmentFlag.AlignVCenter)
        propGrid.addLayout(beanSizeLayout,4,8,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(bean_size_unit_label,4,9,Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)

        propGrid.setRowMinimumHeight(5,self.volumeUnitsComboBox.minimumSizeHint().height())
        propGrid.addWidget(moisture_label,5,0,Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.moisture_greens_edit,5,1,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.moisture_roasted_edit,5,2,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(moisture_greens_unit_label,5,3,Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.moisturepercentlabel,5,4,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(greens_temp_label,5,7,Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.greens_temp_edit,5,8,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(greens_temp_unit_label,5,9,Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)

        propGrid.setRowMinimumHeight(7,30)
        propGrid.addWidget(whole_color_label,7,1,Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        propGrid.addWidget(ground_color_label,7,2,Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)

        propGrid.addWidget(color_label,8,0)
        propGrid.addWidget(self.whole_color_edit,8,1,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.ground_color_edit,8,2,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        propGrid.addWidget(self.colorSystemComboBox,8,3,1,2) # rowSpan=1, columnSpan=2

        if self.aw.color.device is not None and self.aw.color.device != '' and self.aw.color.device not in ['None','Tiny Tonino', 'Classic Tonino']:
            propGrid.addWidget(scanWholeButton,8,6)
        if self.aw.color.device not in (None, '', 'None'):
            propGrid.addWidget(scanGroundButton,8,7)

        propGrid.addWidget(ambientSourceLabel,8,8,1,2,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        ambientGrid = QGridLayout()
        ambientGrid.setContentsMargins(0,0,0,0)
        ambientGrid.setHorizontalSpacing(3)
        ambientGrid.setVerticalSpacing(0)
        ambientGrid.addWidget(ambientlabel,2,0)
        ambientGrid.addLayout(ambient,2,2,1,5)
        ambientGrid.addWidget(updateAmbientTemp,2,10)
        ambientGrid.addWidget(self.ambientComboBox,2,11,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        ambientGrid.setColumnMinimumWidth(3, 11)
        ambientGrid.setColumnMinimumWidth(5, 11)
        ambientGrid.setColumnMinimumWidth(8, 11)
        roastFlagsLayout = QHBoxLayout()
        roastFlagsGrid = QGridLayout()
        roastFlagsGrid.addWidget(self.lowFC,0,0)
        roastFlagsGrid.addWidget(self.heavyFC,1,0)
        roastFlagsGrid.addWidget(self.lightCut,0,1)
        roastFlagsGrid.addWidget(self.darkCut,1,1)
        roastFlagsGrid.addWidget(self.drops,0,2)
        roastFlagsGrid.addWidget(self.oily,1,2)
        roastFlagsGrid.addWidget(self.uneven,0,3)
        roastFlagsGrid.addWidget(self.tipping,1,3)
        roastFlagsGrid.addWidget(self.scorching,0,4)
        roastFlagsGrid.addWidget(self.divots,1,4)
        roastFlagsLayout.addLayout(roastFlagsGrid)
        roastFlagsLayout.addStretch()
        anotationLayout = QVBoxLayout()
        anotationLayout.addWidget(roastinglabel)
        anotationLayout.addWidget(self.roastingeditor)
        anotationLayout.addLayout(roastFlagsLayout)
        anotationLayout.addWidget(cuppinglabel)
        anotationLayout.addWidget(self.cuppingeditor)
        okLayout = QHBoxLayout()
        okLayout.addWidget(self.roastproperties)
        okLayout.addStretch()
        okLayout.addSpacing(3)
        okLayout.addWidget(self.roastpropertiesAutoOpen)
        okLayout.addStretch()
        okLayout.addSpacing(3)
        okLayout.addWidget(self.roastpropertiesAutoOpenDROP)
        okLayout.addStretch()
        okLayout.addWidget(self.dialogbuttons)
        okLayout.setSpacing(10)
        okLayout.setContentsMargins(5, 15, 5, 15) # left, top, right, bottom
        timeLayoutBox = QHBoxLayout()
        timeLayoutBox.addStretch()
        timeLayoutBox.addLayout(timeLayout)
        timeLayoutBox.addStretch()
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(3, 3, 3, 3)
        eventbuttonLayout = QHBoxLayout()
        eventbuttonLayout.addWidget(self.copyeventTableButton)
        eventbuttonLayout.addWidget(self.createalarmTableButton)
        eventbuttonLayout.addStretch()
        eventbuttonLayout.addWidget(self.clusterEventsButton)
        eventbuttonLayout.addWidget(self.ordereventTableButton)
        eventbuttonLayout.addStretch()
        eventbuttonLayout.addWidget(self.clearEventsButton)
        eventbuttonLayout.addStretch()
        eventbuttonLayout.addWidget(self.deleventTableButton)
        eventbuttonLayout.addWidget(self.neweventTableButton)
        databuttonLayout = QHBoxLayout()
        databuttonLayout.addWidget(self.copydataTableButton)
        databuttonLayout.addStretch()
        #tab 1
        self.tab1aLayout = QVBoxLayout()
        self.tab1aLayout.setContentsMargins(0,0,0,0)
        self.tab1aLayout.setSpacing(0)
#        self.tab1aLayout.addLayout(mainLayout)
#        self.tab1aLayout.addStretch()
        self.tab1aLayout.addLayout(textLayout)
#        self.tab1aLayout.addStretch()
        self.tab1aLayout.setSpacing(8)
        self.tab1aLayout.addLayout(propGrid)
        self.tab1aLayout.addLayout(ambientGrid)
        tab1Layout = QVBoxLayout()
#        tab1Layout.addStretch()
        tab1Layout.setContentsMargins(5, 5, 5, 2) # left, top, right, bottom
        tab1Layout.addLayout(self.tab1aLayout)
        tab1Layout.setSpacing(0)
#        tab1Layout.addStretch()
        # set volume from density if given
        self.density_in_editing_finished()
        self.density_out_editing_finished()
        # set density from volume if given
        #tab 2
        tab2Layout = QVBoxLayout()
        tab2Layout.addLayout(anotationLayout)
        tab2Layout.setContentsMargins(5, 5, 5, 5) # left, top, right, bottom
        #tab3 events
        tab3Layout = QVBoxLayout()
        tab3Layout.addLayout(timeLayoutBox)
        tab3Layout.addWidget(self.eventtable)
        tab3Layout.addLayout(eventbuttonLayout)
        tab3Layout.setContentsMargins(5, 5, 5, 5) # left, top, right, bottom
        #tab 4 data
        tab4Layout = QVBoxLayout()
        tab4Layout.addWidget(self.datatable)
        tab4Layout.addLayout(databuttonLayout)
        tab4Layout.setContentsMargins(2, 5, 2, 5) # left, top, right, bottom
        #tabwidget
        self.TabWidget = QTabWidget()
        self.TabWidget.setContentsMargins(0,0,0,0)
        C1Widget = QWidget()
        C1Widget.setLayout(tab1Layout)
        self.TabWidget.addTab(C1Widget,QApplication.translate('Tab', 'Roast'))
        C2Widget = QWidget()
        C2Widget.setLayout(tab2Layout)
        self.TabWidget.addTab(C2Widget,QApplication.translate('Tab', 'Notes'))
        C3Widget = QWidget()
        C3Widget.setLayout(tab3Layout)
        self.TabWidget.addTab(C3Widget,QApplication.translate('Tab', 'Events'))
        C4Widget = QWidget()
        C4Widget.setLayout(tab4Layout)
        self.TabWidget.addTab(C4Widget,QApplication.translate('Tab', 'Data'))
        self.C5Widget = QWidget()
        self.TabWidget.addTab(self.C5Widget,QApplication.translate('Tab', 'Energy'))
        self.C6Widget = QWidget()
        self.TabWidget.addTab(self.C6Widget,QApplication.translate('Tab', 'Setup'))
        #
        self.TabWidget.currentChanged.connect(self.tabSwitched)
        #incorporate layouts
        totallayout = QVBoxLayout()
        totallayout.addWidget(self.TabWidget)
        totallayout.addLayout(okLayout)
        totallayout.setContentsMargins(10,10,10,0) # left, top, right, bottom
        totallayout.setSpacing(0)
        self.volume_percent()
        self.setLayout(totallayout)

        self.populatePlusCoffeeBlendCombos()

        self.titleedit.setFocus()

        self.updateTemplateLine()

        # set marks if needed
        self.checkWeightOut()
        self.checkVolumeOut()
        self.checkDensityOut()
        self.checkMoistureOut()

        settings = QSettings()
        if settings.contains('RoastGeometry'):
            self.restoreGeometry(settings.value('RoastGeometry'))
        else:
            self.resize(self.minimumSizeHint())


#PLUS
        self.updateStockSignalConnection:Optional[QMetaObject.Connection] = None
        self.stockWorker:Optional[plus.stock.Worker] = None
        try:
            if self.aw.plus_account is not None:
                if plus.controller.is_connected():
                    self.stockWorker= plus.stock.getWorker()
                    if self.stockWorker is not None:
                        self.updateStockSignalConnection = self.stockWorker.updatedSignal.connect(self.populatePlusCoffeeBlendCombos)
                        QTimer.singleShot(10, plus.stock.update)
                else: # we are in ON mode, but not connected, we connect which triggers a stock update if successful
                    plus.controller.connect(interactive=False)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        if platform.system() != 'Windows':
            ok_button: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button is not None:
                ok_button.setFocus()

        # we set the active tab with a QTimer after the tabbar has been rendered once, as otherwise
        # some tabs are not rendered at all on Windows using Qt v6.5.1 (https://bugreports.qt.io/projects/QTBUG/issues/QTBUG-114204?filter=allissues)
        QTimer.singleShot(50, self.setActiveTab)

    def updateWeightOutDefectsLabel(self) -> None:
        self.defectslabel.setText(f"<b>{QApplication.translate('Label', 'Defects')}</b>" if self.aw.qmc.roasted_defects_mode else
                f"<b>{QApplication.translate('Label', 'Yield')}</b>")
        self.defectsButton.setText(QApplication.translate('Button', 'defects') if self.aw.qmc.roasted_defects_mode else QApplication.translate('Button', 'yield'))


    @pyqtSlot(bool)
    def toggleWeightOutDefects(self, _:bool = False) -> None:
        self.aw.qmc.roasted_defects_mode = not self.aw.qmc.roasted_defects_mode
        self.updateWeightOutDefectsLabel()
        defects:float = 0
        if self.weightoutdefectsedit.text() != '':
            defects = float(comma2dot(self.weightoutdefectsedit.text()))
        weightout:float = 0
        if self.weightoutedit.text() != '':
            weightout = float(comma2dot(self.weightoutedit.text()))
        defects = min(weightout, max(defects, 0))
        dw = 0 if defects == 0 else weightout - defects
        dw_txt = f'{float2floatWeightVolume(dw):g}'
        if self.aw.qmc.roasted_defects_mode or dw_txt != '0':
            self.weightoutdefectsedit.setText(dw_txt)
        else:
            self.weightoutdefectsedit.setText('')
        self.defect_percent()

    def get_scale_weight(self) -> Optional[float]:
        return self.scale_weight

    @pyqtSlot()
    def setActiveTab(self) -> None:
        self.TabWidget.setCurrentIndex(self.activeTab)

## CUSTOM BLEND DIALOG

    @pyqtSlot(bool)
    def customBlendButton_triggered(self, _:bool = False) -> None:
        inWeight:float = float(comma2dot(str(self.weightinedit.text())))


        coffees = plus.stock.getCoffeeLabels()

        if len(coffees)>2:
            if self.aw.qmc.plus_custom_blend is not None and self.aw.qmc.plus_custom_blend.isValid(coffees.values()):
                blend = self.aw.qmc.plus_custom_blend
            else:
                coffee_tuples = sorted(coffees.items(), key=lambda x: x[0])
                blend = plus.blend.CustomBlend(QApplication.translate('Form Caption','Custom Blend'),[
                    plus.blend.Component(coffee_tuples[0][1], 0.5),
                    plus.blend.Component(coffee_tuples[1][1], 0.5)
                ])
            # only entries of coffees with stock in the selected store or in all stores if no store is selected) should be enabled in blend component coffee popups
            coffee_hr_ids_with_stock_in_store:Set[str] = set()
            if self.plus_coffees is not None:
                coffee_hr_ids_with_stock_in_store = {plus.stock.getCoffeeId(c) for c in self.plus_coffees if
                    # if there are multiple stores defined and non is selected, only coffees with stock in all stores are enabled in the blend component coffee popups
                    self.plus_stores is None or len(self.plus_stores) < 2 or self.plus_stores_combo.currentIndex() != 0 or len(plus.stock.getCoffeeCoffeeStocks(c)) == len(self.plus_stores)}

            res, total_weight = plus.blend.openCustomBlendDialog(self, self.aw, inWeight, self.aw.qmc.weight[2],
                    coffees, blend, coffee_hr_ids_with_stock_in_store)
            if res: # not canceled
                self.aw.qmc.plus_custom_blend = res
                self.populatePlusCoffeeBlendCombos() # we update the blend menu to reflect the current custom blend
                if self.aw.qmc.plus_custom_blend.name.strip() == '' and self.plus_blend_selected_spec is not None and 'hr_id' in self.plus_blend_selected_spec and self.plus_blend_selected_spec['hr_id'] == '':
                    # if the custom blend entry was selected before, which is now removed, we select the empty first entry
                    self.plus_blends_combo.setCurrentIndex(0)
                    self.blendSelectionChanged(0)
                # update inweight
                inw = f'{float2floatWeightVolume(total_weight):g}'
                self.weightinedit.setText(inw)
                self.weightineditChanged()

##

    def updateWeightLCD(self, txt_value:str, txt_unit:str = '', total:Optional[float] = None) -> None:
        if self.aw.scale.device is not None and self.aw.scale.device not in {'', 'None'}:
            self.scaleWeight.setText(txt_value+txt_unit.lower())
            total_txt, unit = self.updateScaleWeightAccumulated(total)
            self.scaleWeightAccumulated.setText(total_txt + unit.lower())
            if self.aw.largeScaleLCDs_dialog is not None:
                self.aw.largeScaleLCDs_dialog.updateWeightUnitTotal(unit)
            self.aw.qmc.updateLargeScaleLCDs(txt_value, total_txt)

    @pyqtSlot(bool)
    def SetupSetDefaults(self, _:bool = False) -> None:
        # set default machine settings from setup dialog
        if self.setup_ui is not None:
            self.aw.qmc.organization_setup = self.setup_ui.lineEditOrganization.text()
            self.aw.qmc.operator_setup = self.setup_ui.lineEditOperator.text()
            self.aw.qmc.roastertype_setup = self.setup_ui.lineEditMachine.text()
            self.aw.qmc.roastersize_setup = self.setup_ui.doubleSpinBoxRoasterSize.value()
            self.aw.qmc.last_batchsize = convertWeight(self.aw.qmc.roastersize_setup,1,0) # set last_batchsize to nominal batch size (kg) in g
            if self.weightinedit.text() == '0':
                nominal_batch_size = convertWeight(self.aw.qmc.roastersize_setup,1,weight_units.index(self.aw.qmc.weight[2]))
                inw = f'{float2floatWeightVolume(nominal_batch_size):g}'
                self.weightinedit.setText(inw)
            self.aw.qmc.roasterheating_setup = self.setup_ui.comboBoxHeating.currentIndex()
            self.aw.qmc.drumspeed_setup = self.setup_ui.lineEditDrumSpeed.text()
            self.populateSetupDefaults()
            self.setupEdited()
            self.aw.updateScheduleSignal.emit()

    @pyqtSlot(bool)
    def SetupDefaults(self, _:bool = False) -> None:
        # set default machine setup from settings
        if self.setup_ui is not None:
            self.setup_ui.lineEditOrganization.setText(self.aw.qmc.organization_setup)
            self.setup_ui.lineEditOperator.setText(self.aw.qmc.operator_setup)
            self.setup_ui.lineEditMachine.setText(self.aw.qmc.roastertype_setup)
            self.setup_ui.doubleSpinBoxRoasterSize.setValue(self.aw.qmc.roastersize_setup)
            self.setup_ui.comboBoxHeating.setCurrentIndex(self.aw.qmc.roasterheating_setup)
            self.setup_ui.lineEditDrumSpeed.setText(self.aw.qmc.drumspeed_setup)
            self.setupEdited()

    def enableBatchEdit(self) -> None:
        if not self.aw.superusermode and not self.batcheditmode:
            self.batcheditmode = True
            self.batchLayout.removeWidget(self.batchedit)
            self.defineBatchEditor()

    def defineBatchEditor(self) -> None:
        self.batchprefixedit = QLineEdit(self.aw.qmc.roastbatchprefix)
        self.batchcounterSpinBox = QSpinBox()
        self.batchcounterSpinBox.setRange(0,65534)
        self.batchcounterSpinBox.setSingleStep(1)
        self.batchcounterSpinBox.setValue(int(self.aw.qmc.roastbatchnr))
        self.batchcounterSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.batchposSpinBox = QSpinBox()
        self.batchposSpinBox.setRange(1,99)
        self.batchposSpinBox.setSingleStep(1)
        self.batchposSpinBox.setValue(int(self.aw.qmc.roastbatchpos))
        self.batchposSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.batchLayout.addWidget(self.batchprefixedit)
        self.batchLayout.addWidget(self.batchcounterSpinBox)
        self.batchLayout.addWidget(self.batchposSpinBox)

    @pyqtSlot()
    def readScale(self) -> None:
        if self.disconnecting:
            self.aw.scale.closeport()
            self.scale_weight = None
            self.scale_battery = None
        elif self.aw.scale.SP is None or not self.aw.scale.SP.is_open:
            self.connectScaleSignal.emit()
        else:
            w,_,_ = self.aw.scale.readWeight()
            if w != -1:
                self.scale_weight = w
            else:
                self.scale_weight = None
            self.update_scale_weight()
            if self.volumedialog is not None:
                self.scaleWeightUpdated.emit(w)
            self.readScaleSignal.emit()

    @pyqtSlot()
    def readScaleLoop(self) -> None:
        QTimer.singleShot(1000,self.readScale)

    @pyqtSlot()
    def connectScaleLoop(self) -> None:
        QTimer.singleShot(2000,self.connectScale)

    @pyqtSlot()
    def connectScale(self) -> None:
        if self.disconnecting:
            self.aw.scale.closeport()
        else:
            res = self.aw.scale.connect(error=False)
            if res:
                self.readScaleSignal.connect(self.readScaleLoop)
                QTimer.singleShot(2,lambda : self.readScaleSignal.emit()) # pylint: disable= unnecessary-lambda
            else:
                self.connectScaleSignal.emit()

    @pyqtSlot()
    def resetScaleSet(self) -> None:
        self.scale_set = None
        self.scaleWeightAccumulated.setText('')
        self.aw.qmc.updateLargeScaleLCDs(None, '')

    # takes total accumulated weight and renders it as text; returns the empty string if the total weight is not given
    def updateScaleWeightAccumulated(self,weight:Optional[float]=None) -> Tuple[str,str]:
        unit:str = ''
        v_formatted:str = ''
        if self.scale_set is not None and weight is not None:
            v = weight + self.scale_set
            if weight_units.index(self.aw.qmc.weight[2]) in {0, 1}:
                if v > 1000:
                    v_formatted = f'{v/1000:.2f}'
                    unit = 'kg'
                else:
                    v_formatted = f'{v:.0f}' # never show decimals for g
                    unit = 'g'
            # non-metric
            else:
                v = convertWeight(v,0,weight_units.index(self.aw.qmc.weight[2]))
                v_formatted = f'{v:.2f}'
                unit = self.aw.qmc.weight[2]
        return v_formatted, unit

    @pyqtSlot()
    def ble_disconnected(self) -> None:
        self.scale_weight = None
        self.scale_battery = None
        self.updateWeightLCD('----')

    @pyqtSlot(int)
    def ble_weight_changed(self, w:int) -> None:
        if w is not None:
            self.scale_weight = w
            self.update_scale_weight()

    @pyqtSlot(int)
    def ble_battery_changed(self, b:int) -> None:
        if b is not None:
            self.scale_battery = b
            self.update_scale_weight()

    def update_scale_weight(self) -> None:
        tare:float = 0
        try:
            tare_idx = self.tareComboBox.currentIndex() - 3
            if tare_idx > -1:
                tare = self.aw.qmc.container_weights[tare_idx]
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        if self.scale_weight is not None and tare is not None:
            v = self.scale_weight - tare # weight in g
            unit = weight_units.index(self.aw.qmc.weight[2])
            if unit == 0: # g selected
                # metric
                v_formatted = f'{v:.0f}' # never show decimals for g
            elif unit == 1: # kg selected
                # metric (always keep the accuracy to the g
                v_formatted = f'{v/1000:.3f}'
            # non-metric
            else:
                v = convertWeight(v,0,weight_units.index(self.aw.qmc.weight[2]))
                v_formatted = f'{v:.2f}'
            self.updateWeightLCD(v_formatted, self.aw.qmc.weight[2].lower(), self.scale_weight - tare)
        elif self.aw.scale.device is not None and self.aw.scale.device not in {'', 'None'}:
            self.updateWeightLCD('----')

    def updateTemplateLine(self) -> None:
        line = ''
        if self.template_file:
            if self.template_batchprefix:
                line = self.template_batchprefix
            if self.template_batchnr:
                line = line + str(self.template_batchnr)
            if self.template_name:
                if len(line) != 0:
                    line = line + ' '
                line = line + self.template_name
        if len(line) > 0:
            line = QApplication.translate('Label', 'Template') + ': ' + line
        self.template_line.setText(line)

    def updatePlusSelectedLine(self) -> None:
        try:
            if self.aw.app.darkmode:
                dark_mode_link_color = " style=\"color: #e5e9ec;\""
            else:
                dark_mode_link_color = ''
            line = ''
            if self.plus_coffee_selected is not None and self.plus_coffee_selected_label:
                line = f'<a href="{plus.util.coffeeLink(self.plus_coffee_selected)}"{dark_mode_link_color}>{self.plus_coffee_selected_label}</a>'
            elif self.plus_blend_selected_spec and self.plus_blend_selected_spec_labels:
                # limit to max 4 component links
                for i, ll in sorted(zip(self.plus_blend_selected_spec['ingredients'],self.plus_blend_selected_spec_labels), key=lambda tup:tup[0]['ratio'],reverse = True)[:4]:
                    if line:
                        line = line + ', '
                    c = f"<a href=\"{plus.util.coffeeLink(i['coffee'])}\"{dark_mode_link_color}>{abbrevString(ll, 18)}</a>"
                    line = line + str(int(round(i['ratio']*100))) + '% ' + c
            if line and len(line)>0 and self.plus_store_selected is not None and self.plus_store_selected_label is not None:
                line = line + f'  (<a href="{plus.util.storeLink(self.plus_store_selected)}"{dark_mode_link_color}>{self.plus_store_selected_label}</a>)'
            self.plus_selected_line.setText(line)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    @pyqtSlot()
    def beansEdited(self) -> None:
        self.modified_beans = self.beansedit.toPlainText()

    @pyqtSlot()
    def beanSizeMinEdited(self) -> None:
        self.modified_beansize_min_text = self.bean_size_min_edit.text()

    @pyqtSlot()
    def beanSizeMaxEdited(self) -> None:
        self.modified_beansize_max_text = self.bean_size_max_edit.text()

    @pyqtSlot()
    def moistureEdited(self) -> None:
        self.moisture_greens_edit.setText(comma2dot(str(self.moisture_greens_edit.text())))
        self.moisture_roasted_edit.setText(comma2dot(str(self.moisture_roasted_edit.text())))
        self.modified_moisture_greens_text = self.moisture_greens_edit.text()
        self.calculated_organic_loss()
        self.checkMoistureOut()

    def plus_popups_set_enabled(self, b:bool) -> None:
        if self.aw.plus_account is not None:
            try:
                self.plus_stores_combo.setEnabled(b)
                self.plus_coffees_combo.setEnabled(b)
                self.plus_blends_combo.setEnabled(b)
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)

    # storeIndex is the index of the selected entry in the popup
    @pyqtSlot()
    @pyqtSlot(int)
    def populatePlusCoffeeBlendCombos(self, storeIndex:Optional[int] = None) -> None:
        if self.aw.plus_account is not None:
            try: # this can crash if dialog got closed while this is processed in a different thread!
                self.plus_popups_set_enabled(False)

                #---- Stores

                if storeIndex is None or storeIndex == -1:
                    self.plus_stores = plus.stock.getStores()
                    try:
                        if len(self.plus_stores) == 1:
                            self.plus_default_store = plus.stock.getStoreId(self.plus_stores[0])
                        if len(self.plus_stores) < 2:
#                            self.plusStoreslabel.hide()
#                            self.plus_stores_combo.hide()
                            self.plusLineStoresFrame.hide()
                        else:
#                            self.plusStoreslabel.show()
#                            self.plus_stores_combo.show()
                            self.plusLineStoresFrame.show()
                    except Exception as e:  # pylint: disable=broad-except
                        _log.exception(e)
                    self.plus_stores_combo.blockSignals(True)
                    self.plus_stores_combo.clear()
                    store_items = plus.stock.getStoreLabels(self.plus_stores)
                    self.plus_stores_combo.addItems([''] + store_items)
                    p = (plus.stock.getStorePosition(self.plus_default_store,self.plus_stores) if self.plus_default_store is not None else None)
                    if p is None:
                        self.plus_stores_combo.setCurrentIndex(0)
                    else:
                        # we set to the default_store if available
                        self.plus_stores_combo.setCurrentIndex(p+1)
                    self.plus_stores_combo.blockSignals(False)

                storeIdx = self.plus_stores_combo.currentIndex()

                # we reset the store if a coffee or blend is selected and the selected store is not equal to the default store
                # we clean the coffee/blend selection as it does not fit
                if storeIdx > 0 and self.plus_stores is not None and len(self.plus_stores)>storeIdx-1:
                    selected_store = self.plus_stores[storeIdx-1]
                    selected_store_id = plus.stock.getStoreId(selected_store)
                    if (self.plus_coffee_selected or self.plus_blend_selected_spec) and self.plus_store_selected != selected_store_id:
                        self.defaultCoffeeData()
                        self.plus_amount_selected = None
                        self.plus_store_selected_label = None
                        if self.plus_coffee_selected:
                            self.plus_coffee_selected = None
                            self.plus_coffee_selected_label = None
                        if self.plus_blend_selected_spec:
                            self.plus_blend_selected_label = None
                            self.plus_blend_selected_spec = None
                            self.plus_blend_selected_spec_labels = None
                    self.plus_default_store = selected_store_id
                else:
                    self.plus_default_store = None

                mark_coffee_fields = False


                #---- Coffees

                self.plus_coffees = plus.stock.getCoffees(self.unitsComboBox.currentIndex(),self.plus_default_store)
                self.plus_coffees_combo.blockSignals(True)
                self.plus_coffees_combo.clear()
                self.plus_coffees_combo.resetInverted()
                coffee_items = plus.stock.getCoffeesLabels(self.plus_coffees)
                self.plus_coffees_combo.addItems([''] + coffee_items)

                p = None
                if self.plus_coffee_selected is not None and self.plus_store_selected is not None:
                    p = plus.stock.getCoffeeStockPosition(self.plus_coffee_selected,self.plus_store_selected,self.plus_coffees)
                if p is None:
                    # not in the current stock
                    self.plus_coffees_combo.setCurrentIndex(0)
                    #self.plus_coffee_selected = None # we don't "deselect" a coffee just because it is not in the popup!
                    self.plus_coffees_combo.blockSignals(False)
                else:
                    # if roast is complete (charge and drop are set)
                    if self.aw.qmc.timeindex[0] > -1 and self.aw.qmc.timeindex[6] > 0:
                        # we first change the index and then unblock signals to avoid properties being overwritten from the selected coffee
                        self.plus_coffees_combo.setCurrentIndex(p+1)
                        self.plus_coffees_combo.blockSignals(False)
                    else:
                        # if roast is not yet complete we unblock the signals before changing the index to get the coffee data be filled in
                        self.plus_coffees_combo.blockSignals(False)
                        self.plus_coffees_combo.setCurrentIndex(p+1)
                    mark_coffee_fields = True

                #---- Blends

                custom_blend:Optional[plus.stock.Blend] = None
                # if a valid custom_blend with a non-empty name exists, we add it to the blend popups
                if self.aw.qmc.plus_custom_blend is not None and self.aw.qmc.plus_custom_blend.name.strip() != '':
                    coffees = plus.stock.getCoffeeLabels()
                    if len(coffees)>2 and self.aw.qmc.plus_custom_blend.isValid(coffees.values()):
                        custom_blend = {
                            'hr_id': '',
                            'label': self.aw.qmc.plus_custom_blend.name.strip(),
                            'ingredients': [{'ratio': c.ratio, 'coffee': c.coffee} for c in self.aw.qmc.plus_custom_blend.components]}
                self.plus_blends = plus.stock.getBlends(self.unitsComboBox.currentIndex(),self.plus_default_store, custom_blend)
                self.plus_blends_combo.blockSignals(True)
                self.plus_blends_combo.clear()
                self.plus_blends_combo.resetInverted()
                blend_items = plus.stock.getBlendLabels(self.plus_blends)

                self.plus_blends_combo.addItems([''] + blend_items)

                if len(self.plus_blends) == 0:
                    self.plusBlendslabel.setVisible(False)
                    self.plus_blends_combo.setVisible(False)
                else:
                    self.plusBlendslabel.setVisible(True)
                    self.plus_blends_combo.setVisible(True)

                p = None
                if self.plus_blend_selected_spec is not None and self.plus_store_selected is not None:
                    p = plus.stock.getBlendSpecStockPosition(self.plus_blend_selected_spec,self.plus_store_selected,self.plus_blends)
                if p is None:
                    self.plus_blends_combo.setCurrentIndex(0)
                    #self.plus_blend_selected_spec = None # we don't deselect a blend just because it is not in the popup
                    self.plus_blends_combo.blockSignals(False)
                else:
                    # if roast is complete (charge and drop are set)
                    if self.aw.qmc.timeindex[0] > -1 and self.aw.qmc.timeindex[6] > 0:
                        # we first change the index and then unblock signals to avoid properties being overwritten from the selected blend
                        self.plus_blends_combo.setCurrentIndex(p+1)
                        self.plus_blends_combo.blockSignals(False)
                    else:
                        # if roast is not yet complete we unblock the signals before changing the index to get the blend data be filled in
                        self.plus_blends_combo.blockSignals(False)
                        self.plus_blends_combo.setCurrentIndex(p+1)
                    mark_coffee_fields = True

                self.markPlusCoffeeFields(mark_coffee_fields)
                self.updatePlusSelectedLine()
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
            finally:
                self.plus_popups_set_enabled(True)
                self.plus_stores_combo.blockSignals(False)
                self.plus_coffees_combo.blockSignals(False)
                self.plus_blends_combo.blockSignals(False)

    def markPlusCoffeeFields(self, b:bool) -> None:
        # for QTextEdit
        if b:
            if self.aw.app.darkmode:
                self.beansedit.setStyleSheet('QTextEdit { background-color: #0D658F; selection-background-color: darkgray; }')
            else:
                self.beansedit.setStyleSheet('QTextEdit { background-color: #e4f3f8; selection-background-color: darkgray;  }')
        else:
            self.beansedit.setStyleSheet('')
        # for QLineEdit
        if b:
            if self.aw.app.darkmode:
                qlineedit_marked_style = 'QLineEdit { background-color: #0D658F; selection-background-color: darkgray; }'
            else:
                qlineedit_marked_style = 'QLineEdit { background-color: #e4f3f8; selection-background-color: #424242; }'
            self.bean_density_in_edit.setStyleSheet(qlineedit_marked_style)
            self.bean_size_min_edit.setStyleSheet(qlineedit_marked_style)
            self.bean_size_max_edit.setStyleSheet(qlineedit_marked_style)
            self.moisture_greens_edit.setStyleSheet(qlineedit_marked_style)
        else:
            background_white_style = ''
            self.bean_density_in_edit.setStyleSheet(background_white_style)
            self.bean_size_min_edit.setStyleSheet(background_white_style)
            self.bean_size_max_edit.setStyleSheet(background_white_style)
            self.moisture_greens_edit.setStyleSheet(background_white_style)

    def updateTitle(self, prev_coffee_label:Optional[str], prev_blend_label:Optional[str]) -> None:
        titles_to_be_overwritten = [ '', QApplication.translate('Scope Title', 'Roaster Scope') ]
        if prev_coffee_label is not None:
            titles_to_be_overwritten.append(prev_coffee_label)
        if prev_blend_label is not None:
            titles_to_be_overwritten.append(prev_blend_label)
        if self.titleedit.currentText() in titles_to_be_overwritten:
            if self.plus_blend_selected_label is not None:
                self.titleedit.textEdited(self.plus_blend_selected_label)
                self.titleedit.setEditText(self.plus_blend_selected_label)
            elif self.plus_coffee_selected_label is not None:
                self.titleedit.textEdited(self.plus_coffee_selected_label)
                self.titleedit.setEditText(self.plus_coffee_selected_label)
            else:
                default_title = QApplication.translate('Scope Title', 'Roaster Scope')
                self.titleedit.textEdited(default_title)
                self.titleedit.setEditText(default_title)

    def updateBlendLines(self, blend:plus.stock.BlendStructure) -> None:
        if self.weightinedit.text() != '':
            weightIn = float(comma2dot(self.weightinedit.text()))
        else:
            weightIn = 0.0
        weight_unit_idx = self.unitsComboBox.currentIndex()
        blend_lines = plus.stock.blend2beans(blend,weight_unit_idx,weightIn)
        self.beansedit.clear()
        for ll in blend_lines:
            self.beansedit.append(ll)

    def fillBlendData(self, blend:plus.stock.BlendStructure, prev_coffee_label:Optional[str], prev_blend_label:Optional[str]) -> None:
        try:
            self.updateBlendLines(blend)
            keep_modified_moisture = self.modified_moisture_greens_text
            keep_modified_density = self.modified_density_in_text

            blend_dict = self.getBlendDictCurrentWeight(blend)

            moisture_txt = '0'
            try:
                if 'moisture' in blend_dict and blend_dict['moisture'] is not None:
                    moisture_txt = f"{blend_dict['moisture']:g}"
            except Exception:  # pylint: disable=broad-except
                pass
            self.moisture_greens_edit.setText(moisture_txt)
            density_txt = '0'
            try:
                if 'density' in blend_dict and blend_dict['density'] is not None:
                    density_txt = f"{float2float(blend_dict['density']):g}"
            except Exception:  # pylint: disable=broad-except
                pass
            self.bean_density_in_edit.setText(density_txt)
            screen_size_min = '0'
            screen_size_max = '0'
            try:
                if 'screen_min' in blend_dict and blend_dict['screen_min'] is not None:
                    screen_size_min = str(int(blend_dict['screen_min']))
                if 'screen_max' in blend_dict and blend_dict['screen_max'] is not None:
                    screen_size_max = str(int(blend_dict['screen_max']))
            except Exception:  # pylint: disable=broad-except
                pass
            self.bean_size_min_edit.setText(screen_size_min)
            self.bean_size_max_edit.setText(screen_size_max)
            # check if title should be changed (if still default, or equal to the previous selection:
            self.updateTitle(prev_coffee_label,prev_blend_label)
            self.markPlusCoffeeFields(True)
            self.density_in_editing_finished()
            self.moistureEdited()
            self.modified_density_in_text = keep_modified_density
            self.modified_moisture_greens_text = keep_modified_moisture
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

    # if current title is equal to default title or prev_coffee/blend_label, we set title from selected label
    def fillCoffeeData(self, coffee:Tuple[str, Tuple[plus.stock.Coffee, plus.stock.StockItem]],
            prev_coffee_label:Optional[str], prev_blend_label:Optional[str]) -> None:
        try:
            cd = plus.stock.getCoffeeCoffeeDict(coffee)
            self.beansedit.setPlainText(plus.stock.coffee2beans(cd))
            keep_modified_moisture = self.modified_moisture_greens_text
            keep_modified_density = self.modified_density_in_text
            moisture_txt = '0'
            try:
                if 'moisture' in cd and cd['moisture'] is not None:
                    moisture_txt = f"{cd['moisture']:g}"
            except Exception:  # pylint: disable=broad-except
                pass
            self.moisture_greens_edit.setText(moisture_txt)
            density_txt = '0'
            try:
                if 'density' in cd and cd['density'] is not None:
                    density_txt = f"{float2float(cd['density']):g}"
            except Exception: # pylint: disable=broad-except
                pass
            self.bean_density_in_edit.setText(density_txt)
            screen_size_min = '0'
            screen_size_max = '0'
            try:
                if 'screen_size' in cd and cd['screen_size'] is not None:
                    screen = cd['screen_size']
                    if 'min' in screen and screen['min'] is not None:
                        screen_size_min = str(int(screen['min']))
                    if 'max' in screen and screen['max'] is not None:
                        screen_size_max = str(int(screen['max']))
            except Exception:  # pylint: disable=broad-except
                pass
            self.bean_size_min_edit.setText(screen_size_min)
            self.bean_size_max_edit.setText(screen_size_max)
            self.updateTitle(prev_coffee_label,prev_blend_label)
            self.markPlusCoffeeFields(True)
            self.density_in_editing_finished()
            self.moistureEdited()
            self.modified_density_in_text = keep_modified_density
            self.modified_moisture_greens_text = keep_modified_moisture
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

    def defaultCoffeeData(self) -> None:
        self.beansedit.setPlainText(self.modified_beans)
        self.bean_density_in_edit.setText(self.modified_density_in_text)
        self.volumeinedit.setText(self.modified_volume_in_text)
        self.bean_size_min_edit.setText(self.modified_beansize_min_text)
        self.bean_size_max_edit.setText(self.modified_beansize_max_text)
        self.moisture_greens_edit.setText(self.modified_moisture_greens_text)
        self.markPlusCoffeeFields(False)
        self.density_in_editing_finished()
        self.moistureEdited()

    @pyqtSlot(int)
    def storeSelectionChanged(self, n:int) -> None:
        if n != -1:
            prev_coffee_label = self.plus_coffee_selected_label
            prev_blend_label = self.plus_blend_selected_label
            self.populatePlusCoffeeBlendCombos(n)
            self.updateTitle(prev_coffee_label, prev_blend_label)

    @pyqtSlot(int)
    def coffeeSelectionChanged(self, n:int) -> None:
        # check for previously selected blend label
        prev_coffee_label = self.plus_coffee_selected_label
        prev_blend_label = self.plus_blend_selected_label
        if n < 1 or self.plus_coffees is None:
            self.defaultCoffeeData()
            self.plus_store_selected = None
            self.plus_store_selected_label = None
            self.plus_coffee_selected = None
            self.plus_coffee_selected_label = None
            self.plus_amount_selected = None
            self.plus_amount_replace_selected = None
            self.updateTitle(prev_coffee_label,prev_blend_label)
        else:
            # reset blend and set new coffee
            self.plus_blends_combo.setCurrentIndex(0)
            selected_coffee = self.plus_coffees[n-1]
            sd = plus.stock.getCoffeeStockDict(selected_coffee)
            self.plus_store_selected = sd['location_hr_id']
            self.plus_store_selected_label = sd['location_label']
            cd = plus.stock.getCoffeeCoffeeDict(selected_coffee)
            self.plus_coffee_selected = cd.get('hr_id','')
            self.plus_coffee_selected_label = plus.stock.coffeeLabel(cd)
            self.plus_blend_selected_label = None
            self.plus_blend_selected_spec = None
            self.plus_blend_selected_spec_labels = None
            if 'amount' in plus.stock.getCoffeeStockDict(selected_coffee):
                self.plus_amount_selected = plus.stock.getCoffeeStockDict(selected_coffee)['amount']
            else:
                self.pus_amount_selected = None
            self.plus_amount_replace_selected = None
            self.fillCoffeeData(selected_coffee,prev_coffee_label,prev_blend_label)
        self.checkWeightIn()
        self.updatePlusSelectedLine()

    def getBlendDictCurrentWeight(self, blend:Tuple[str, Tuple[plus.stock.Blend, plus.stock.StockItem, float, Dict[str, str], float, List[Tuple[float, plus.stock.Blend]]]]) -> plus.stock.Blend:
        if self.weightinedit.text() != '':
            weightIn = float(comma2dot(self.weightinedit.text()))
        else:
            weightIn = 0.0
        weight_unit_idx = self.unitsComboBox.currentIndex()
        v = convertWeight(weightIn,weight_unit_idx,weight_units.index('Kg')) # v is weightIn converted to kg
        return plus.stock.getBlendBlendDict(blend,v)

    @pyqtSlot(int)
    def blendSelectionChanged(self, n:int) -> None:
        # check for previously selected blend label
        prev_coffee_label = self.plus_coffee_selected_label
        prev_blend_label = self.plus_blend_selected_label
        if n < 1 or self.plus_blends is None:
            self.defaultCoffeeData()
            self.plus_store_selected = None
            self.plus_store_selected_label = None
            self.plus_blend_selected_label = None
            self.plus_blend_selected_spec = None
            self.plus_blend_selected_spec_labels = None
            self.pus_amount_selected = None
            self.updateTitle(prev_coffee_label,prev_blend_label)
        else:
            # reset coffee and set new blend
            self.plus_coffees_combo.setCurrentIndex(0)
            selected_blend = self.plus_blends[n-1]
            bsd:plus.stock.StockItem = plus.stock.getBlendStockDict(selected_blend)
            self.plus_store_selected = bsd['location_hr_id']
            self.plus_store_selected_label = bsd['location_label']

            bd = self.getBlendDictCurrentWeight(selected_blend)
            self.plus_coffee_selected = None
            self.plus_blend_selected_label = bd['label']
            self.plus_blend_selected_spec = cast(plus.stock.Blend, dict(bd)) # make a copy of the blend dict
# UPDATE: we keep the hr_id in to be able to adjust the blend with its replacements if needed
#            # we trim the blend_spec to the external from
#            self.plus_blend_selected_spec.pop("hr_id", None) # remove the hr_id

            self.plus_blend_selected_spec_labels = [i.get('label','') for i in self.plus_blend_selected_spec['ingredients']]
            # remove labels from ingredients
            ingredients = []
            for i in self.plus_blend_selected_spec['ingredients']:
                entry:plus.stock.BlendIngredient = {'ratio': i['ratio'], 'coffee': i['coffee']}
                if 'ratio_num' in i and i['ratio_num'] is not None:
                    entry['ratio_num'] = i['ratio_num']
                if 'ratio_denom' in i and i['ratio_denom'] is not None:
                    entry['ratio_denom'] = i['ratio_denom']
                ingredients.append(entry)
            self.plus_blend_selected_spec['ingredients'] = ingredients
            self.plus_amount_selected = plus.stock.getBlendMaxAmount(selected_blend)
            self.plus_amount_replace_selected = plus.stock.getBlendReplaceMaxAmount(selected_blend)
            self.fillBlendData(selected_blend,prev_coffee_label,prev_blend_label)

        self.checkWeightIn()
        self.updatePlusSelectedLine()

    # keeps the weightoutdefectsedit placeholder text set along the weightoutedit text
    def weightouteditSetText(self, txt:str) -> None:
        self.weightoutedit.setText(txt)
        self.weightoutdefectsedit.setPlaceholderText(txt)

    # recentRoast activated from within RoastProperties dialog
    def recentRoastActivated(self, n:int) -> None:
        # note, the first item is the edited text!
        if 0 < n <= len(self.aw.recentRoasts):
            rr:RecentRoast = self.aw.recentRoasts[n-1]
            if 'title' in rr and rr['title'] is not None:
                self.titleedit.textEdited(rr['title'])
                self.titleedit.setEditText(rr['title'])
            if 'weightUnit' in rr and rr['weightUnit'] is not None:
                self.unitsComboBox.setCurrentIndex(weight_units.index(rr['weightUnit']))
            if 'weightIn' in rr and rr['weightIn'] is not None:
                self.weightinedit.setText(f"{rr['weightIn']:g}")
            # all of the following items might not be in the dict
            if 'beans' in rr and rr['beans'] is not None:
                self.beansedit.setPlainText(rr['beans'])
            if 'weightOut' in rr and rr['weightOut'] is not None:
                self.weightouteditSetText(f"{rr['weightOut']:g}")
            else:
                self.weightouteditSetText('0')
            if 'volumeIn' in rr and rr['volumeIn'] is not None:
                self.volumeinedit.setText(f"{rr['volumeIn']:g}")
            if 'volumeOut' in rr and rr['volumeOut'] is not None:
                self.volumeoutedit.setText(f"{rr['volumeOut']:g}")
            else:
                self.volumeoutedit.setText('0')
            if 'volumeUnit' in rr and rr['volumeUnit'] is not None:
                self.volumeUnitsComboBox.setCurrentIndex(volume_units.index(rr['volumeUnit']))
            if 'densityWeight' in rr and rr['densityWeight'] is not None:
                self.bean_density_in_edit.setText(f"{float2float(rr['densityWeight']):g}")
            if 'densityRoasted' in rr and rr['densityRoasted'] is not None:
                self.bean_density_out_edit.setText(f"{float2float(rr['densityRoasted']):g}")
            else:
                self.bean_density_out_edit.setText('0')
            if 'moistureGreen' in rr and rr['moistureGreen'] is not None:
                self.moisture_greens_edit.setText(f"{float2float(rr['moistureGreen']):g}")
            if 'moistureRoasted' in rr and rr['moistureRoasted'] is not None:
                self.moisture_roasted_edit.setText(f"{float2float(rr['moistureRoasted']):g}")
            else:
                self.moisture_roasted_edit.setText('0')
            if 'wholeColor' in rr and rr['wholeColor'] is not None:
                self.whole_color_edit.setText(str(rr['wholeColor']))
            else:
                self.whole_color_edit.setText('0')
            if 'groundColor' in rr and rr['groundColor'] is not None:
                self.ground_color_edit.setText(str(rr['groundColor']))
            else:
                self.ground_color_edit.setText('0')
            if 'colorSystem' in rr and rr['colorSystem'] is not None:
                if rr['colorSystem'] in self.aw.qmc.color_systems:
                    self.aw.qmc.color_system_idx = self.aw.qmc.color_systems.index(rr['colorSystem'])
                    self.colorSystemComboBox.setCurrentIndex(self.aw.qmc.color_system_idx)
                elif isinstance(rr['colorSystem'], int) and rr['colorSystem'] < len(self.aw.qmc.color_systems):  # type: ignore
                    # to stay compatible with older versions were rr['colorSystem'] was an index instead of the name of a system
                    self.aw.qmc.color_system_idx = rr['colorSystem'] # type: ignore[unreachable]
                    self.colorSystemComboBox.setCurrentIndex(self.aw.qmc.color_system_idx) # type:ignore[unused-ignore]

            # items added in v1.4 might not be in the data set of previous stored recent roasts
            if 'beanSize_min' in rr and rr['beanSize_min'] is not None:
                self.bean_size_min_edit.setText(str(int(rr['beanSize_min'])))
            if 'beanSize_max' in rr and rr['beanSize_max'] is not None:
                self.bean_size_max_edit.setText(str(int(rr['beanSize_max'])))
            # Note: the background profile will not be changed if recent roast is activated from Roast Properties
            if 'background' in rr and rr['background'] is not None:
                self.template_file = rr['background']
                if 'title' in rr and rr['title'] is not None:
                    self.template_name = rr['title']
                if 'roastUUID' in rr and rr['roastUUID'] is not None:
                    self.template_uuid = rr['roastUUID']
                if 'batchnr' in rr and rr['batchnr'] is not None:
                    self.template_batchnr = rr['batchnr']
                if 'batchprefix' in rr and rr['batchprefix'] is not None:
                    self.template_batchprefix = rr['batchprefix']
            else:
                self.template_file = None
                self.template_name = None
                self.template_uuid = None
                self.template_batchnr = None
                self.template_batchprefix = None
            self.updateTemplateLine()
            self.percent()

#PLUS
            if self.aw.plus_account is not None and 'plus_account' in rr and self.aw.plus_account == rr['plus_account']:
                if 'plus_store' in rr:
                    self.plus_store_selected = rr['plus_store']
                if 'plus_store_label' in rr:
                    self.plus_store_selected_label = rr['plus_store_label']
                self.plus_coffee_selected = rr.get('plus_coffee', None)
                if 'plus_coffee_label' in rr:
                    self.plus_coffee_selected_label = rr['plus_coffee_label']
                else:
                    self.plus_coffee_selected_label = None
                if 'plus_blend_spec' in rr:
                    self.plus_blend_selected_label = rr.get('plus_blend_label', None)
                    self.plus_blend_selected_spec = rr['plus_blend_spec']
                    if 'plus_blend_spec_labels' in rr:
                        self.plus_blend_selected_spec_labels = rr['plus_blend_spec_labels']
                else:
                    self.plus_blend_selected_label = None
                    self.plus_blend_selected_spec = None
                    self.plus_blend_selected_spec_labels = None
                if self.plus_store_selected is not None and self.plus_default_store is not None and self.plus_default_store != self.plus_store_selected:
                    self.plus_default_store = None # we reset the defaultstore
                # we now set the actual values from the stock
                self.populatePlusCoffeeBlendCombos()
                if self.plus_blend_selected_spec is not None and self.plus_blends is not None and 'hr_id' in self.plus_blend_selected_spec:
                    # try to apply blend replacement (blend recipe might have been updated on the server since this recent roast blend entry was established
                    # search for the position of blend/location hr_id combo in self.plus_blends and call blendSelectionChanged with pos+1
                    try:
                        pos_in_blends = next(i for i, b in enumerate(self.plus_blends) if \
                            plus.stock.getBlendId(b) == self.plus_blend_selected_spec['hr_id'] and
                            plus.stock.getBlendStockDict(b)['location_hr_id'] == self.plus_store_selected)
                        self.blendSelectionChanged(pos_in_blends+1)
                    except Exception:  # pylint: disable=broad-except
                        self.updatePlusSelectedLine()
                else:
                    # blend replacements not applied
                    self.updatePlusSelectedLine()

            self.aw.sendmessage(QApplication.translate('Message',f"Recent roast properties '{self.aw.recentRoastLabel(rr)}' set"))
        self.recentRoastEnabled()

    @pyqtSlot(str)
    def recentRoastEnabled(self,_:str = '') -> None:
        try:
            title = self.titleedit.currentText()
            weightIn = float(comma2dot(self.weightinedit.text()))
            # add new recent roast entry only if title is not default, beans is not empty and weight-in is not 0
            if title != QApplication.translate('Scope Title', 'Roaster Scope') and weightIn != 0:
                # enable "+" addRecentRoast button
                self.addRecentButton.setEnabled(True)
                self.delRecentButton.setEnabled(True)
            else:
                self.addRecentButton.setEnabled(False)
                self.delRecentButton.setEnabled(False)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            self.addRecentButton.setEnabled(False)
            self.delRecentButton.setEnabled(False)

    @pyqtSlot(bool)
    def delRecentRoast(self, _:bool = False) -> None:
        try:
            title = ' '.join(self.titleedit.currentText().split())
            weightIn = float(comma2dot(self.weightinedit.text()))
            weightUnit = self.unitsComboBox.currentText()
            if weightUnit == 'kg':
                weightUnit = 'Kg'
            self.aw.recentRoasts = self.aw.delRecentRoast(title,weightIn,weightUnit)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    @pyqtSlot(bool)
    def addRecentRoast(self, __:bool = False) -> None:
        try:
            title = ' '.join(self.titleedit.currentText().split())
            weightIn = float(comma2dot(str(self.weightinedit.text())))
            # add new recent roast entry only if title is not default, beans is not empty and weight-in is not 0
            if title != QApplication.translate('Scope Title', 'Roaster Scope') and weightIn != 0:
                beans = self.beansedit.toPlainText()
                weightUnit = self.unitsComboBox.currentText()
                if weightUnit == 'kg':
                    weightUnit = 'Kg'
                if self.volumeinedit.text() != '':
                    volumeIn = float(comma2dot(str(self.volumeinedit.text())))
                else:
                    volumeIn = 0
                volumeUnit = self.volumeUnitsComboBox.currentText()
                if self.bean_density_in_edit.text() != '':
                    densityWeight = float(comma2dot(str(self.bean_density_in_edit.text())))
                else:
                    densityWeight = 0
                if self.bean_size_min_edit.text() != '':
                    beanSize_min = int(round(float(comma2dot(self.bean_size_min_edit.text()))))
                else:
                    beanSize_min = 0
                if self.bean_size_max_edit.text() != '':
                    beanSize_max = int(round(float(comma2dot(self.bean_size_max_edit.text()))))
                else:
                    beanSize_max = 0
                if self.moisture_greens_edit.text() != '':
                    moistureGreen = float(comma2dot(self.moisture_greens_edit.text()))
                else:
                    moistureGreen = 0.0
                colorSystem = self.colorSystemComboBox.currentIndex()

                modifiers = QApplication.keyboardModifiers()
                weightOut = volumeOut = densityRoasted = moistureRoasted = wholeColor = groundColor = None
                if modifiers == Qt.KeyboardModifier.AltModifier:  #alt click
                    # we add weightOut, volumeOut, moistureRoasted, wholeColor, groundColor
                    weightOut = float(comma2dot(str(self.weightoutedit.text())))
                    volumeOut = float(comma2dot(str(self.volumeoutedit.text())))
                    densityRoasted = float(comma2dot(str(self.bean_density_out_edit.text())))
                    moistureRoasted = float(comma2dot(self.moisture_roasted_edit.text()))
                    wholeColor = int(round(float(self.whole_color_edit.text())))
                    groundColor = int(round(float(self.ground_color_edit.text())))

                rr = self.aw.createRecentRoast(
                    title,
                    beans,
                    weightIn,
                    weightUnit,
                    volumeIn,
                    volumeUnit,
                    densityWeight,
                    beanSize_min,
                    beanSize_max,
                    moistureGreen,
                    self.aw.qmc.color_systems[colorSystem],
                    self.aw.curFile, # could be empty
                    self.aw.qmc.roastUUID, # could be empty
                    self.aw.qmc.roastbatchnr, #self.batchcounterSpinBox # self.aw.superusermode and self.aw.qmc.batchcounter > -1
                    self.aw.qmc.roastbatchprefix,  #self.batchprefixedit
                    self.aw.plus_account,
                    self.plus_store_selected,
                    self.plus_store_selected_label,
                    self.plus_coffee_selected,
                    self.plus_coffee_selected_label,
                    self.plus_blend_selected_label,
                    self.plus_blend_selected_spec,
                    self.plus_blend_selected_spec_labels,
                    weightOut,
                    volumeOut,
                    densityRoasted,
                    moistureRoasted,
                    wholeColor,
                    groundColor
                    )
                self.aw.addRecentRoast(rr)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' addRecentRoast(): {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))



    # called on CANCEL or WINDOW_CLOSE; reverts state and calls clean_up_and_close()
    @pyqtSlot()
    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:

        # restore
        self.restoreAllEnergySettings()

        self.aw.qmc.beans = self.org_beans
        self.aw.qmc.density = self.org_density
        self.aw.qmc.density_roasted = self.org_density_roasted
        self.aw.qmc.beansize_min = self.org_beansize_min
        self.aw.qmc.beansize_max = self.org_beansize_max
        self.aw.qmc.moisture_greens = self.org_moisture_greens

        self.aw.qmc.weight = self.org_weight
        self.aw.qmc.volume = self.org_volume

        self.aw.qmc.roasted_defects_mode = self.org_roasted_defects_mode

        self.aw.qmc.perKgRoastMode = self.org_perKgRoastMode

        self.aw.qmc.specialevents = self.org_specialevents
        self.aw.qmc.specialeventstype = self.org_specialeventstype
        self.aw.qmc.specialeventsStrings = self.org_specialeventsStrings
        self.aw.qmc.specialeventsvalue = self.org_specialeventsvalue
        self.aw.qmc.timeindex = self.org_timeindex
        self.aw.qmc.phases = self.org_phases

        self.aw.qmc.ambientTemp = self.org_ambientTemp
        self.aw.qmc.ambient_humidity = self.org_ambient_humidity
        self.aw.qmc.ambient_pressure = self.org_ambient_pressure

        self.aw.qmc.roastpropertiesAutoOpenFlag = self.org_roastpropertiesAutoOpenFlag
        self.aw.qmc.roastpropertiesAutoOpenDropFlag = self.org_roastpropertiesAutoOpenDropFlag

        self.aw.qmc.clear_last_picked_event_selection()
        self.aw.eNumberSpinBox.setValue(0)

        self.aw.qmc.redraw_keep_view(recomputeAllDeltas=False)

        self.clean_up()
        super().reject()


    # called on CANCEL and WindowClose from closeEvent(), and on OK from accept()
    def clean_up(self) -> None:
        self.disconnecting = True
        if self.acaia is not None:
            try:
                self.acaia.battery_changed_signal.disconnect()
                self.acaia.weight_changed_signal.disconnect()
                self.acaia.disconnected_signal.disconnect()
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
            try:
                self.acaia.stop()
                self.updateWeightLCD('')
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
            self.acaia = None
        settings = QSettings()
        #save window geometry
        settings.setValue('RoastGeometry',self.saveGeometry())
        self.aw.editGraphDlg_activeTab = self.TabWidget.currentIndex()
        self.aw.editgraphdialog = None
        if self.stockWorker is not None and self.updateStockSignalConnection is not None:
            self.stockWorker.updatedSignal.disconnect(self.updateStockSignalConnection)

    # calcs volume (in ml) from density (in g/l) and weight (in g)
    @staticmethod
    def calc_volume(density:float, weight:float) -> float:
        return (1./density) * weight * 1000

    #keyboard presses. There must not be widgets (pushbuttons, comboboxes, etc) in focus in order to work
    def keyPressEvent(self, event: Optional['QKeyEvent']) -> None:
        if event is not None:
            key = int(event.key())
            #print(key)
            modifiers = event.modifiers()
            control_modifier = modifiers == Qt.KeyboardModifier.ControlModifier # command/apple k on macOS, CONTROL on Windows
            if event.matches(QKeySequence.StandardKey.Copy) and self.TabWidget.currentIndex() == 3: # datatable
                self.aw.copy_cells_to_clipboard(self.datatable,adjustment=1)
                self.aw.sendmessage(QApplication.translate('Message','Data table copied to clipboard'))
            if key == 16777220 and self.aw.scale.device not in (None, '', 'None'): # ENTER key pressed and scale connected
                if self.weightinedit.hasFocus():
                    self.inWeight(True,overwrite=True) # we don't add to current reading but overwrite
                elif self.weightoutedit.hasFocus():
                    self.outWeight(True,overwrite=True) # we don't add to current reading but overwrite
                elif self.weightoutdefectsedit.hasFocus():
                    self.defectsWeight(True,overwrite=True)
            elif key == 68 and control_modifier and self.TabWidget.currentIndex() == 0: #ctrl D on Roast tab => send scale weight to defects-weight field
                self.defectsWeight(True)
            elif key == 76 and control_modifier and self.TabWidget.currentIndex() == 0: #ctrl L on Roast tab => open volume calculator
                self.volumeCalculatorTimer(True)
            elif key == 73 and control_modifier and self.TabWidget.currentIndex() == 0: #ctrl I on Roast tab => send scale weight to in-weight field
                self.inWeight(True)
            elif key == 79 and control_modifier and self.TabWidget.currentIndex() == 0: #ctrl O on Roast tab => send scale weight to out-weight field
                self.outWeight(True)
            elif key == 80 and control_modifier and self.TabWidget.currentIndex() == 0: #ctrl P on Roast tab => send scale weight to in-weight field
                self.resetScaleSet()
            else:
                super().keyPressEvent(event)

    @staticmethod
    def container_menu_idx(i:int) -> int: # takes a container idx and returns the index of the corresponding menu item
        return i + 3 # skip <edit>, separator and empty index

    # if adjust_index is True (default), the self.aw.container_idx is updated to still point to the previous entry if possible
    # update tare popup
    def updateTarePopup(self, adjust_index:bool=True) -> None:
        prev_item_count = self.tareComboBox.count()
        with QSignalBlocker(self.tareComboBox): # blocking all signals, especially its currentIndexChanged connected to tareChanged which would lead to cycles
            self.tareComboBox.clear()
            self.tareComboBox.addItem(f"<{QApplication.translate('Label','edit')}>")
            self.tareComboBox.insertSeparator(2)
            self.tareComboBox.addItem('')
            self.tareComboBox.addItems(self.aw.qmc.container_names)
            width = self.tareComboBox.minimumSizeHint().width()
            view: Optional[QAbstractItemView] = self.tareComboBox.view()
            if view is not None:
                view.setMinimumWidth(width)
        if adjust_index:
            if self.tareComboBox.count() > prev_item_count:
                # if item list is longer (new items added), we select the last item
                self.aw.qmc.container_idx = self.tareComboBox.count() - 4
            if len(self.aw.qmc.container_weights) > self.aw.qmc.container_idx:
                self.tareComboBox.setCurrentIndex(self.container_menu_idx(self.aw.qmc.container_idx))
            else:
                self.tareComboBox.setCurrentIndex(2) # reset to the empty entry
                self.aw.qmc.container_idx = -1

    @pyqtSlot(int)
    def tareChanged(self, i:int) -> None:
        if i == 0:
            tareDLG = tareDlg(self,self.aw, self.get_scale_weight)
            tareDLG.tare_updated_signal.connect(self.updateTarePopup)
            tareDLG.show()
            self.tareComboBox.setCurrentIndex(self.aw.qmc.container_idx + 3)
        else:
            self.aw.qmc.container_idx = i - 3
            # update displayed scale weight
            self.update_scale_weight()

    @pyqtSlot(int)
    def changeWeightUnit(self, i:int) -> None:
        o = weight_units.index(self.aw.qmc.weight[2]) # previous unit index
        weightUnit = self.unitsComboBox.currentText()
        if weightUnit == 'kg':
            weightUnit = 'Kg'
        self.aw.qmc.weight = (self.aw.qmc.weight[0],self.aw.qmc.weight[1],weightUnit) # update weight unit
        # update defects unit label
        self.weightoutdefects_unit_label.setText(weightUnit.lower())
        for le in [self.weightinedit,self.weightoutedit,self.weightoutdefectsedit]:
            if le.text() and le.text() != '':
                wi = float(comma2dot(le.text()))
                if wi != 0.0:
                    converted = convertWeight(wi,o,i)
                    txt = f'{float2floatWeightVolume(converted):g}'
                    if le == self.weightoutedit:
                        self.weightouteditSetText(txt)
                    else:
                        le.setText(txt)
        self.calculated_density()
#PLUS
        self.populatePlusCoffeeBlendCombos() # update the plus stock popups to display the correct unit
        try:
            # weight unit changed, we update the selected blend in plus mode
            if self.plus_blends_combo.currentIndex() > 0:
                self.blendSelectionChanged(self.plus_blends_combo.currentIndex())
        except Exception: # pylint: disable=broad-except
            pass # self.plus_blends_combo might not be allocated
        try:
            if self.aw.largeScaleLCDs_dialog is not None:
                self.aw.largeScaleLCDs_dialog.reLayout()
            self.update_scale_weight()
        except Exception: # pylint: disable=broad-except
            pass # self.plus_blends_combo might not be allocated
        try:
            if self.aw.schedule_window is not None:
                # we need to ensure that an open completed item edit is cleared/closed not to use the wrong unit which might have changed here
                self.aw.schedule_window.cancel_completed_item_edit()
        except Exception: # pylint: disable=broad-except
            pass

    @pyqtSlot(int)
    def changeVolumeUnit(self, i:int) -> None:
        o = volume_units.index(self.aw.qmc.volume[2]) # previous unit index
        self.aw.qmc.volume = (self.aw.qmc.volume[0],self.aw.qmc.volume[1],self.volumeUnitsComboBox.currentText())
        for le in [self.volumeinedit,self.volumeoutedit]:
            if le.text() and le.text() != '':
                wi = float(comma2dot(le.text()))
                if wi != 0.0:
                    converted = convertVolume(wi,o,i)
                    le.setText(f'{float2floatWeightVolume(converted):g}')
#        self.calculated_density() # if just the unit changes, the density will not change as it is fixed now

    @pyqtSlot(int)
    def tabSwitched(self, i:int) -> None:
        if i in {0,1}: # Roast (always initialized in __init__()) # Notes (always initialized in __init__())
            self.saveEventTable()
        elif i == 2: # Events (only initialized on first opening that tab)
            self.createEventTable()
        elif i == 3: # Data (needs to be recreated every time as events might have been changed in tab "Events"
            self.saveEventTable()
            self.createDataTable()
        elif i == 4: # Energy (only initialized on creation)
            self.saveEventTable()
            self.initEnergyTab()
            self.updateMetricsLabel()
        elif i == 5: # Setup (only initialized on creation)
            self.saveEventTable()
            self.initSetupTab()

    ###### ENERGY TAB #####


    def initEnergyTab(self) -> None:
        # pylint: disable=attribute-defined-outside-init
        if not self.tabInitialized[4]:
            # fill Energy tab
            self.energy_ui = EnergyWidget.Ui_EnergyWidget()
            self.energy_ui.setupUi(self.C5Widget)

            self.btu_list:List[BTU] = []

            # remember parameters to enable a Cancel action
            self.org_loadlabels = self.aw.qmc.loadlabels.copy()
            self.org_loadratings = self.aw.qmc.loadratings.copy()
            self.org_ratingunits = self.aw.qmc.ratingunits.copy()
            self.org_sourcetypes = self.aw.qmc.sourcetypes.copy()
            self.org_load_etypes = self.aw.qmc.load_etypes.copy()
            self.org_presssure_percents = self.aw.qmc.presssure_percents.copy()
            self.org_loadevent_zeropcts = self.aw.qmc.loadevent_zeropcts.copy()
            self.org_loadevent_hundpcts = self.aw.qmc.loadevent_hundpcts.copy()
            self.org_meterlabels = self.aw.qmc.meterlabels.copy()
            self.org_meterunits = self.aw.qmc.meterunits.copy()
            self.org_meterfuels = self.aw.qmc.meterfuels.copy()
            self.org_metersources = self.aw.qmc.metersources.copy()
            self.org_preheatDuration = self.aw.qmc.preheatDuration
            self.org_preheatenergies = self.aw.qmc.preheatenergies.copy()
            self.org_betweenbatchDuration = self.aw.qmc.betweenbatchDuration
            self.org_betweenbatchenergies = self.aw.qmc.betweenbatchenergies.copy()
            self.org_coolingDuration = self.aw.qmc.coolingDuration
            self.org_coolingenergies = self.aw.qmc.coolingenergies.copy()
            self.org_betweenbatch_after_preheat = self.aw.qmc.betweenbatch_after_preheat
            self.org_electricEnergyMix = self.aw.qmc.electricEnergyMix
            self.org_gasMix = self.aw.qmc.gasMix

            ### reset UI text labels and tooltips for proper translation
            # hack to access the Qt automatic translation of the Help button
            db_help = QDialogButtonBox(QDialogButtonBox.StandardButton.Help)
            help_button: Optional[QPushButton] = db_help.button(QDialogButtonBox.StandardButton.Help)
            help_text_translated:str = 'Help'
            if help_button is not None:
                help_text_translated = help_button.text()
            self.energy_ui.helpButton.setText(help_text_translated)
            self.setButtonTranslations(self.energy_ui.helpButton,'Help',QApplication.translate('Button','Help'))
            self.energy_ui.tabWidget.setTabText(0,QApplication.translate('Tab','Details'))
            self.energy_ui.tabWidget.setTabText(1,QApplication.translate('Tab','Loads'))
            self.energy_ui.tabWidget.setTabText(2,QApplication.translate('Tab','Protocol'))
            self.energy_ui.resultunitLabel.setText(QApplication.translate('Label','Results in'))
            self.energy_ui.EnergyGroupBox.setTitle(QApplication.translate('GroupBox','Energy'))
            self.energy_ui.CO2GroupBox.setTitle(QApplication.translate('GroupBox','CO2').replace('CO2','CO₂'))
            # Details tab
            self.energy_ui.copyTableButton.setText(QApplication.translate('Button','Copy Table'))
            self.energy_ui.copyTableButton.setToolTip(QApplication.translate('Tooltip','Copy table to clipboard, OPTION or ALT click for tabular text'))
            item0 = self.energy_ui.datatable.horizontalHeaderItem(0)
            if item0 is not None:
                item0.setText(QApplication.translate('Table','Power'))
            item1 = self.energy_ui.datatable.horizontalHeaderItem(1)
            if item1 is not None:
                item1.setText(QApplication.translate('Table','Duration'))
            item2 = self.energy_ui.datatable.horizontalHeaderItem(2)
            if item2 is not None:
                item2.setText('BTU')
            item3 = self.energy_ui.datatable.horizontalHeaderItem(3)
            if item3 is not None:
                item3.setText(QApplication.translate('Table','CO2').replace('CO2','CO₂') + ' (g)')
            item4 = self.energy_ui.datatable.horizontalHeaderItem(4)
            if item4 is not None:
                item4.setText(QApplication.translate('Table','Load'))
            item5 = self.energy_ui.datatable.horizontalHeaderItem(5)
            if item5 is not None:
                item5.setText(QApplication.translate('Table','Source'))
            item6 = self.energy_ui.datatable.horizontalHeaderItem(6)
            if item6 is not None:
                item6.setText(QApplication.translate('Table','Kind'))
            vheader = self.energy_ui.datatable.verticalHeader()
            if vheader is not None:
                vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            # Loads tab
            self.energy_ui.loadsSetDefaultsButton.setText(QApplication.translate('Button','Save Defaults'))
            # hack to access the Qt automatic translation of the RestoreDefaults button
            db = QDialogButtonBox(QDialogButtonBox.StandardButton.RestoreDefaults)
            defaults_button: Optional[QPushButton] = db.button(QDialogButtonBox.StandardButton.RestoreDefaults)
            defaults_button_text_translated:str = 'Restore Defaults'
            if defaults_button is not None:
                defaults_button_text_translated = defaults_button.text()
            self.energy_ui.loadsDefaultsButtons.setText(defaults_button_text_translated)
            self.setButtonTranslations(self.energy_ui.loadsDefaultsButtons,'Restore Defaults',QApplication.translate('Button','Restore Defaults'))
            self.energy_ui.loadlabelsLabel.setText(QApplication.translate('Label','Label'))
            self.energy_ui.loadratingsLabel.setText(QApplication.translate('Label','Rating'))
            self.energy_ui.ratingunitsLabel.setText(QApplication.translate('Label','Unit'))
            self.energy_ui.sourcetypesLabel.setText(QApplication.translate('Label','Type'))
            self.energy_ui.eventsLabel.setText(QApplication.translate('Label','Event'))
            self.energy_ui.pressureLabel.setText(QApplication.translate('Label','Pressure %'))
            self.energy_ui.electricEnergyMixLabel.setText(QApplication.translate('Label','Electric Energy Mix:'))
            self.energy_ui.gasMixLabel.setText(QApplication.translate('Label','Gas Energy Mix:'))
            self.energy_ui.renewableLabel.setText(QApplication.translate('Label','Renewable'))
            self.energy_ui.renewableLabel2.setText(QApplication.translate('Label','Renewable'))
            self.energy_ui.gasMixLabel.setText(QApplication.translate('Label','Gas Energy Mix:'))
            self.energy_ui.meter1GroupBox.setTitle(QApplication.translate('Label','Meter 1'))
            self.energy_ui.meter2GroupBox.setTitle(QApplication.translate('Label','Meter 2'))
            self.energy_ui.meter1Label.setText(QApplication.translate('Label','Label'))
            self.energy_ui.meter2Label.setText(QApplication.translate('Label','Label'))
            self.energy_ui.meter1UnitLabel.setText(QApplication.translate('Label','Unit'))
            self.energy_ui.meter2UnitLabel.setText(QApplication.translate('Label','Unit'))
            self.energy_ui.meter1FuelLabel.setText(QApplication.translate('Label','Type'))
            self.energy_ui.meter2FuelLabel.setText(QApplication.translate('Label','Type'))
            self.energy_ui.meter1SourceLabel.setText(QApplication.translate('Label','Source'))
            self.energy_ui.meter2SourceLabel.setText(QApplication.translate('Label','Source'))
            # Protocol tab
            self.energy_ui.protocolSetDefaultsButton.setText(QApplication.translate('Button','Save Defaults'))
            self.energy_ui.protocolDefaultsButton.setText(QApplication.translate('Button','Restore Defaults'))
            self.energy_ui.protocolDefaultsButton.setText(defaults_button_text_translated)
            self.setButtonTranslations(self.energy_ui.protocolDefaultsButton,'Restore Defaults',QApplication.translate('Button','Restore Defaults'))
            self.energy_ui.preheatingLabel.setText(QApplication.translate('Label','Pre-Heating'))
            self.energy_ui.betweenBatchesLabel.setText(QApplication.translate('Label','Between Batches'))
            self.energy_ui.coolingLabel.setText(QApplication.translate('Label','Cooling'))
            self.energy_ui.BBPafterPreHeatcheckBox.setText(QApplication.translate('Label','Between Batches after Pre-Heating'))
            self.energy_ui.loadALabel.setText(self.formatLoadLabel('A'))
            self.energy_ui.loadBLabel.setText(self.formatLoadLabel('B'))
            self.energy_ui.loadCLabel.setText(self.formatLoadLabel('C'))
            self.energy_ui.loadDLabel.setText(self.formatLoadLabel('D'))
            self.energy_ui.timeUnitLabel.setText(QApplication.translate('Label','(mm:ss)'))
            self.energy_ui.loadAUnitLabel.setText('(BTU)')
            self.energy_ui.loadBUnitLabel.setText('(BTU)')
            self.energy_ui.loadCUnitLabel.setText('(BTU)')
            self.energy_ui.loadDUnitLabel.setText('(BTU)')
            self.energy_ui.durationLabel.setText(QApplication.translate('Label','Duration'))
            self.energy_ui.measuredEnergyLabel.setText(QApplication.translate('Label','Measured Energy or Output %'))

            # choose the unit to show results
            self.energy_ui.resultunitComboBox.addItems(self.aw.qmc.energyunits)

            #
            self.energy_ui.sourcetype0.addItems(self.aw.qmc.sourcenames)
            self.energy_ui.sourcetype1.addItems(self.aw.qmc.sourcenames)
            self.energy_ui.sourcetype2.addItems(self.aw.qmc.sourcenames)
            self.energy_ui.sourcetype3.addItems(self.aw.qmc.sourcenames)
            #
            etypes = [''] + self.aw.qmc.etypes[:4]
            self.energy_ui.events0.addItems(etypes)
            self.energy_ui.events1.addItems(etypes)
            self.energy_ui.events2.addItems(etypes)
            self.energy_ui.events3.addItems(etypes)
            #
            self.energy_ui.ratingunit0.addItems(self.aw.qmc.powerunits)
            self.energy_ui.ratingunit1.addItems(self.aw.qmc.powerunits)
            self.energy_ui.ratingunit2.addItems(self.aw.qmc.powerunits)
            self.energy_ui.ratingunit3.addItems(self.aw.qmc.powerunits)

            # meter1LabelLineEdit
            #
            self.energy_ui.meter1UnitComboBox.addItems(self.aw.qmc.meterunitnames)
            self.energy_ui.meter2UnitComboBox.addItems(self.aw.qmc.meterunitnames)
            self.energy_ui.meter1FuelComboBox.addItems(self.aw.qmc.sourcenames)
            self.energy_ui.meter2FuelComboBox.addItems(self.aw.qmc.sourcenames)
            #
            self.curvenames = []
            self.curvenames.append('')  # 'blank' top choice
            for i in range(len(self.aw.qmc.extradevices)):
                self.curvenames.append(self.aw.qmc.device_name_subst(self.aw.qmc.extraname1[i]))
                self.curvenames.append(self.aw.qmc.device_name_subst(self.aw.qmc.extraname2[i]))
            self.energy_ui.meter1SourceComboBox.clear()
            self.energy_ui.meter1SourceComboBox.addItems(self.curvenames)
            if self.aw.qmc.metersources[0] < len(self.curvenames):
                self.energy_ui.meter1SourceComboBox.setCurrentIndex(self.aw.qmc.metersources[0])
            self.energy_ui.meter2SourceComboBox.clear()
            self.energy_ui.meter2SourceComboBox.addItems(self.curvenames)
            if self.aw.qmc.metersources[1] < len(self.curvenames):
                self.energy_ui.meter2SourceComboBox.setCurrentIndex(self.aw.qmc.metersources[1])

            # input validators
            regextime = QRegularExpression(r'^$|^[0-9]?[0-9]?[0-9]:[0-5][0-9]$') # includes the empty string to trigger editingFinished
            self.energy_ui.preheatDuration.setValidator(QRegularExpressionValidator(regextime,self))
            self.energy_ui.betweenBatchesDuration.setValidator(QRegularExpressionValidator(regextime,self))
            self.energy_ui.coolingDuration.setValidator(QRegularExpressionValidator(regextime,self))

            # initialize
            self.updateEnergyTab()

            # connect signals
            self.energy_ui.helpButton.clicked.connect(self.showenergyhelp)

            self.energy_ui.tabWidget.currentChanged.connect(self.energyTabSwitched)

            self.energy_ui.copyTableButton.clicked.connect(self.copyEnergyDataTabletoClipboard)

            self.energy_ui.loadlabel0.editingFinished.connect(self.loadlabels_editingfinished)
            self.energy_ui.loadlabel1.editingFinished.connect(self.loadlabels_editingfinished)
            self.energy_ui.loadlabel2.editingFinished.connect(self.loadlabels_editingfinished)
            self.energy_ui.loadlabel3.editingFinished.connect(self.loadlabels_editingfinished)

            self.energy_ui.loadrating0.editingFinished.connect(self.loadratings_editingfinished)
            self.energy_ui.loadrating1.editingFinished.connect(self.loadratings_editingfinished)
            self.energy_ui.loadrating2.editingFinished.connect(self.loadratings_editingfinished)
            self.energy_ui.loadrating3.editingFinished.connect(self.loadratings_editingfinished)

            self.energy_ui.ratingunit0.currentIndexChanged.connect(self.ratingunits_currentindexchanged)
            self.energy_ui.ratingunit1.currentIndexChanged.connect(self.ratingunits_currentindexchanged)
            self.energy_ui.ratingunit2.currentIndexChanged.connect(self.ratingunits_currentindexchanged)
            self.energy_ui.ratingunit3.currentIndexChanged.connect(self.ratingunits_currentindexchanged)

            self.energy_ui.sourcetype0.currentIndexChanged.connect(self.sourcetypes_currentindexchanged)
            self.energy_ui.sourcetype1.currentIndexChanged.connect(self.sourcetypes_currentindexchanged)
            self.energy_ui.sourcetype2.currentIndexChanged.connect(self.sourcetypes_currentindexchanged)
            self.energy_ui.sourcetype3.currentIndexChanged.connect(self.sourcetypes_currentindexchanged)

            self.energy_ui.events0.currentIndexChanged.connect(self.load_etypes_currentindexchanged)
            self.energy_ui.events1.currentIndexChanged.connect(self.load_etypes_currentindexchanged)
            self.energy_ui.events2.currentIndexChanged.connect(self.load_etypes_currentindexchanged)
            self.energy_ui.events3.currentIndexChanged.connect(self.load_etypes_currentindexchanged)

            self.energy_ui.meter1LabelLineEdit.editingFinished.connect(self.meterlabels_editingfinished)
            self.energy_ui.meter2LabelLineEdit.editingFinished.connect(self.meterlabels_editingfinished)

            self.energy_ui.meter1UnitComboBox.currentIndexChanged.connect(self.meterunits_currentindexchanged)
            self.energy_ui.meter2UnitComboBox.currentIndexChanged.connect(self.meterunits_currentindexchanged)

            self.energy_ui.meter1FuelComboBox.currentIndexChanged.connect(self.meterfuels_currentindexchanged)
            self.energy_ui.meter2FuelComboBox.currentIndexChanged.connect(self.meterfuels_currentindexchanged)

            self.energy_ui.meter1SourceComboBox.currentIndexChanged.connect(self.metersources_currentindexchanged)
            self.energy_ui.meter2SourceComboBox.currentIndexChanged.connect(self.metersources_currentindexchanged)

            self.energy_ui.pressureCheckBox0.stateChanged.connect(self.pressureCheckBox_statechanged)
            self.energy_ui.pressureCheckBox1.stateChanged.connect(self.pressureCheckBox_statechanged)
            self.energy_ui.pressureCheckBox2.stateChanged.connect(self.pressureCheckBox_statechanged)
            self.energy_ui.pressureCheckBox3.stateChanged.connect(self.pressureCheckBox_statechanged)

            self.energy_ui.zeropcts0.valueChanged.connect(self.loadevent_zeropcts0_valuechanged)
            self.energy_ui.zeropcts1.valueChanged.connect(self.loadevent_zeropcts1_valuechanged)
            self.energy_ui.zeropcts2.valueChanged.connect(self.loadevent_zeropcts2_valuechanged)
            self.energy_ui.zeropcts3.valueChanged.connect(self.loadevent_zeropcts3_valuechanged)

            self.energy_ui.hundredpct0.valueChanged.connect(self.loadevent_hundpcts0_valuechanged)
            self.energy_ui.hundredpct1.valueChanged.connect(self.loadevent_hundpcts1_valuechanged)
            self.energy_ui.hundredpct2.valueChanged.connect(self.loadevent_hundpcts2_valuechanged)
            self.energy_ui.hundredpct3.valueChanged.connect(self.loadevent_hundpcts3_valuechanged)

            self.energy_ui.PreHeatToolButton.clicked.connect(self.preHeatToolButton_triggered)
            self.energy_ui.BetweenBatchesToolButton.clicked.connect(self.betweenBatchesToolButton_triggered)
            self.energy_ui.CoolingToolButton.clicked.connect(self.coolingToolButton_triggered)

            self.energy_ui.EnergyGroupBox.clicked.connect(self.toggleEnergyCO2Result)
            self.energy_ui.CO2GroupBox.clicked.connect(self.toggleEnergyCO2Result)

            self.loadsEdited()

            # Protocol

            self.energy_ui.preheatDuration.editingFinished.connect(self.preheatDuration_editingfinished)
            self.energy_ui.betweenBatchesDuration.editingFinished.connect(self.betweenBatchesDuration_editingfinished)
            self.energy_ui.coolingDuration.editingFinished.connect(self.coolingDuration_editingfinished)

            self.energy_ui.preheatenergies0.editingFinished.connect(self.preheatenergies_editingfinished)
            self.energy_ui.preheatenergies1.editingFinished.connect(self.preheatenergies_editingfinished)
            self.energy_ui.preheatenergies2.editingFinished.connect(self.preheatenergies_editingfinished)
            self.energy_ui.preheatenergies3.editingFinished.connect(self.preheatenergies_editingfinished)

            self.energy_ui.betweenbatchesenergy0.editingFinished.connect(self.betweenbatchenergies_editingfinished)
            self.energy_ui.betweenbatchesenergy1.editingFinished.connect(self.betweenbatchenergies_editingfinished)
            self.energy_ui.betweenbatchesenergy2.editingFinished.connect(self.betweenbatchenergies_editingfinished)
            self.energy_ui.betweenbatchesenergy3.editingFinished.connect(self.betweenbatchenergies_editingfinished)

            self.energy_ui.coolingenergies0.editingFinished.connect(self.coolingenergies_editingfinished)
            self.energy_ui.coolingenergies1.editingFinished.connect(self.coolingenergies_editingfinished)
            self.energy_ui.coolingenergies2.editingFinished.connect(self.coolingenergies_editingfinished)
            self.energy_ui.coolingenergies3.editingFinished.connect(self.coolingenergies_editingfinished)

            self.energy_ui.BBPafterPreHeatcheckBox.stateChanged.connect(self.betweenbatch_after_preheat_statechanged)

            self.energy_ui.electricEnergyMixSpinBox.valueChanged.connect(self.electric_energy_mix_valuechanged)
            self.energy_ui.gasMixSpinBox.valueChanged.connect(self.gas_energy_mix_valuechanged)

            self.energy_ui.resultunitComboBox.currentIndexChanged.connect(self.energyresultunitComboBox_indexchanged)

            self.protocolEdited()

            #
            self.energy_ui.loadsSetDefaultsButton.clicked.connect(self.setEnergyLoadDefaults)
            self.energy_ui.loadsDefaultsButtons.clicked.connect(self.restoreEnergyLoadDefaults)
            self.energy_ui.protocolSetDefaultsButton.clicked.connect(self.setEnergyProtocolDefaults)
            self.energy_ui.protocolDefaultsButton.clicked.connect(self.restoreEnergyProtocolDefaults)

            #
            self.tabInitialized[4] = True
        else:
            # we update all data as main or custom events might have changed in the other tabs
            self.saveMainEvents()
            self.updateMetricsLabel()
            self.createEnergyDataTable()
        # we always set the batch position on tab switch as it might have been changed in the first tab of the Roast Properties dialog
        self.energy_ui.roastbatchposLabel.setText(f"{QApplication.translate('Label','Batch')} #{self.aw.qmc.roastbatchpos}")

    def createEnergyDataTable(self) -> None:
        self.updateEnergyConfig()
        ndata = len(self.btu_list)
        self.energy_ui.datatable.setSortingEnabled(False) # deactivate sorting while populating not to mess up things
        self.energy_ui.datatable.setRowCount(0) # clears the table, but keeps the header intact
        self.energy_ui.datatable.setRowCount(ndata)

        item2 = self.energy_ui.datatable.horizontalHeaderItem(2)
        if item2 is not None:
            item2.setText(self.aw.qmc.energyunits[self.aw.qmc.energyresultunit_setup])

        for i in range(ndata):
            if self.btu_list[i]['Kind'] in {0, 2}:  #Preheat Measured, BBP Measured
                load_widget = MyTableWidgetItemNumber('',self.btu_list[i]['load_pct'])
            else:
                load_widget = MyTableWidgetItemNumber(f"{self.btu_list[i]['load_pct']:.1f}%",self.btu_list[i]['load_pct'])
            load_widget.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

            if self.btu_list[i]['Kind'] in {0, 2}:  #Preheat Measured, BBP Measured
                duration_mmss_widget = MyTableWidgetItemNumber('',0)
            else:
                duration_mmss_widget = MyTableWidgetItemNumber(stringfromseconds(self.btu_list[i]['duration']),self.btu_list[i]['duration'])
                duration_mmss_widget.setTextAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)

            BTUs = self.aw.qmc.convertHeat(self.btu_list[i]['BTUs'],'BTU',self.aw.qmc.energyunits[self.aw.qmc.energyresultunit_setup])
            BTUs_widget = MyTableWidgetItemNumber(scaleFloat2String(BTUs),BTUs)
            BTUs_widget.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

            CO2g = self.btu_list[i]['CO2g']
            CO2g_widget = MyTableWidgetItemNumber(scaleFloat2String(CO2g),CO2g)
            CO2g_widget.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

            Load_widget = QTableWidgetItem(self.btu_list[i]['LoadLabel'])
            Load_widget.setTextAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

            SourceType_widget = MyTableWidgetItemNumber(self.aw.qmc.sourcenames[self.btu_list[i]['SourceType']],self.btu_list[i]['SortOrder'])
            SourceType_widget.setTextAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)

            Kind_widget = MyTableWidgetItemNumber(self.aw.qmc.kind_list[self.btu_list[i]['Kind']],self.btu_list[i]['SortOrder'])
            Kind_widget.setTextAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

            self.energy_ui.datatable.setItem(i,0,load_widget)
            self.energy_ui.datatable.setItem(i,1,duration_mmss_widget)
            self.energy_ui.datatable.setItem(i,2,BTUs_widget)
            self.energy_ui.datatable.setItem(i,3,CO2g_widget)
            self.energy_ui.datatable.setItem(i,4,Load_widget)
            self.energy_ui.datatable.setItem(i,5,SourceType_widget)
            self.energy_ui.datatable.setItem(i,6,Kind_widget)

        header = self.energy_ui.datatable.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
#        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
#        self.energy_ui.datatable.resizeColumnsToContents()

#        # remember the columnwidth
#        for i in range(len(self.aw.qmc.energytablecolumnwidths)):
#            try:
#                w = self.aw.qmc.energytablecolumnwidths[i]
#                if i == 6:
#                    w = max(80,w)
#                self.energy_ui.datatable.setColumnWidth(i,w)
#            except:
#                pass

        self.energy_ui.datatable.setSortingEnabled(True)
        self.energy_ui.datatable.sortItems(6)

    # fills the energy tab widgets with the current energy config data
    def updateEnergyTab(self) -> None:
        self.energy_ui.resultunitComboBox.setCurrentIndex(self.aw.qmc.energyresultunit_setup)
        ## Details tab
        ## Loads tab
        # label
        self.energy_ui.loadlabel0.setText(self.aw.qmc.loadlabels[0])
        self.energy_ui.loadlabel1.setText(self.aw.qmc.loadlabels[1])
        self.energy_ui.loadlabel2.setText(self.aw.qmc.loadlabels[2])
        self.energy_ui.loadlabel3.setText(self.aw.qmc.loadlabels[3])
        # rating
        self.energy_ui.loadrating0.setText(str(self.aw.qmc.loadratings[0]) if self.aw.qmc.loadratings[0] != 0 else '')
        self.energy_ui.loadrating1.setText(str(self.aw.qmc.loadratings[1]) if self.aw.qmc.loadratings[1] != 0 else '')
        self.energy_ui.loadrating2.setText(str(self.aw.qmc.loadratings[2]) if self.aw.qmc.loadratings[2] != 0 else '')
        self.energy_ui.loadrating3.setText(str(self.aw.qmc.loadratings[3]) if self.aw.qmc.loadratings[3] != 0 else '')
        # unit
        self.energy_ui.ratingunit0.setCurrentIndex(self.aw.qmc.ratingunits[0])
        self.energy_ui.ratingunit1.setCurrentIndex(self.aw.qmc.ratingunits[1])
        self.energy_ui.ratingunit2.setCurrentIndex(self.aw.qmc.ratingunits[2])
        self.energy_ui.ratingunit3.setCurrentIndex(self.aw.qmc.ratingunits[3])
        # source
        self.energy_ui.sourcetype0.setCurrentIndex(self.aw.qmc.sourcetypes[0])
        self.energy_ui.sourcetype1.setCurrentIndex(self.aw.qmc.sourcetypes[1])
        self.energy_ui.sourcetype2.setCurrentIndex(self.aw.qmc.sourcetypes[2])
        self.energy_ui.sourcetype3.setCurrentIndex(self.aw.qmc.sourcetypes[3])
        # event
        self.energy_ui.events0.setCurrentIndex(self.aw.qmc.load_etypes[0])
        self.energy_ui.events1.setCurrentIndex(self.aw.qmc.load_etypes[1])
        self.energy_ui.events2.setCurrentIndex(self.aw.qmc.load_etypes[2])
        self.energy_ui.events3.setCurrentIndex(self.aw.qmc.load_etypes[3])
        # pressure percent
        self.energy_ui.pressureCheckBox0.setChecked(self.aw.qmc.presssure_percents[0])
        self.energy_ui.pressureCheckBox1.setChecked(self.aw.qmc.presssure_percents[1])
        self.energy_ui.pressureCheckBox2.setChecked(self.aw.qmc.presssure_percents[2])
        self.energy_ui.pressureCheckBox3.setChecked(self.aw.qmc.presssure_percents[3])
        # zeropcts
        self.energy_ui.zeropcts0.setValue(self.aw.qmc.loadevent_zeropcts[0])
        self.energy_ui.zeropcts1.setValue(self.aw.qmc.loadevent_zeropcts[1])
        self.energy_ui.zeropcts2.setValue(self.aw.qmc.loadevent_zeropcts[2])
        self.energy_ui.zeropcts3.setValue(self.aw.qmc.loadevent_zeropcts[3])
        # hundpcts
        self.energy_ui.hundredpct0.setValue(self.aw.qmc.loadevent_hundpcts[0])
        self.energy_ui.hundredpct1.setValue(self.aw.qmc.loadevent_hundpcts[1])
        self.energy_ui.hundredpct2.setValue(self.aw.qmc.loadevent_hundpcts[2])
        self.energy_ui.hundredpct3.setValue(self.aw.qmc.loadevent_hundpcts[3])
        # meters
        self.energy_ui.meter1LabelLineEdit.setText(self.aw.qmc.meterlabels[0])
        self.energy_ui.meter2LabelLineEdit.setText(self.aw.qmc.meterlabels[1])
        self.energy_ui.meter1UnitComboBox.setCurrentIndex(self.aw.qmc.meterunits[0])
        self.energy_ui.meter2UnitComboBox.setCurrentIndex(self.aw.qmc.meterunits[1])
        self.energy_ui.meter1FuelComboBox.setCurrentIndex(self.aw.qmc.meterfuels[0])
        self.energy_ui.meter2FuelComboBox.setCurrentIndex(self.aw.qmc.meterfuels[1])
        self.energy_ui.meter1SourceComboBox.setCurrentIndex(self.aw.qmc.metersources[0])
        self.energy_ui.meter2SourceComboBox.setCurrentIndex(self.aw.qmc.metersources[1])
        ## Protocol tab
        self.energy_ui.preheatDuration.setText(self.validateSeconds2Text(self.aw.qmc.preheatDuration))
        self.energy_ui.betweenBatchesDuration.setText(self.validateSeconds2Text(self.aw.qmc.betweenbatchDuration))
        self.energy_ui.coolingDuration.setText(self.validateSeconds2Text(self.aw.qmc.coolingDuration))
        self.energy_ui.preheatenergies0.setText(self.validatePctText(str(self.aw.qmc.preheatenergies[0])))
        self.energy_ui.preheatenergies1.setText(self.validatePctText(str(self.aw.qmc.preheatenergies[1])))
        self.energy_ui.preheatenergies2.setText(self.validatePctText(str(self.aw.qmc.preheatenergies[2])))
        self.energy_ui.preheatenergies3.setText(self.validatePctText(str(self.aw.qmc.preheatenergies[3])))
        self.energy_ui.betweenbatchesenergy0.setText(self.validatePctText(str(self.aw.qmc.betweenbatchenergies[0])))
        self.energy_ui.betweenbatchesenergy1.setText(self.validatePctText(str(self.aw.qmc.betweenbatchenergies[1])))
        self.energy_ui.betweenbatchesenergy2.setText(self.validatePctText(str(self.aw.qmc.betweenbatchenergies[2])))
        self.energy_ui.betweenbatchesenergy3.setText(self.validatePctText(str(self.aw.qmc.betweenbatchenergies[3])))
        self.energy_ui.coolingenergies0.setText(self.validatePctText(str(self.aw.qmc.coolingenergies[0])))
        self.energy_ui.coolingenergies1.setText(self.validatePctText(str(self.aw.qmc.coolingenergies[1])))
        self.energy_ui.coolingenergies2.setText(self.validatePctText(str(self.aw.qmc.coolingenergies[2])))
        self.energy_ui.coolingenergies3.setText(self.validatePctText(str(self.aw.qmc.coolingenergies[3])))
        self.energy_ui.BBPafterPreHeatcheckBox.setChecked(self.aw.qmc.betweenbatch_after_preheat)
        self.energy_ui.electricEnergyMixSpinBox.setValue(self.aw.qmc.electricEnergyMix)
        self.energy_ui.gasMixSpinBox.setValue(self.aw.qmc.gasMix)
        #
        self.updateEnergyLabels()
        self.updateEnergyUnitLabels()
        self.updateEnableZHpct()
        self.createEnergyDataTable()

    def updateLoadLabels(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.loadlabels[0] = self.energy_ui.loadlabel0.text()
        self.aw.qmc.loadlabels[1] = self.energy_ui.loadlabel1.text()
        self.aw.qmc.loadlabels[2] = self.energy_ui.loadlabel2.text()
        self.aw.qmc.loadlabels[3] = self.energy_ui.loadlabel3.text()
        if updateMetrics:
            self.updateMetricsLabel()
        self.updateEnergyLabels()

    def updateLoadRatings(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.loadratings[0] = toFloat(scaleFloat2String(self.energy_ui.loadrating0.text())) if len(self.energy_ui.loadrating0.text())>0 else 0
        self.aw.qmc.loadratings[1] = toFloat(scaleFloat2String(self.energy_ui.loadrating1.text())) if len(self.energy_ui.loadrating1.text())>0 else 0
        self.aw.qmc.loadratings[2] = toFloat(scaleFloat2String(self.energy_ui.loadrating2.text())) if len(self.energy_ui.loadrating2.text())>0 else 0
        self.aw.qmc.loadratings[3] = toFloat(scaleFloat2String(self.energy_ui.loadrating3.text())) if len(self.energy_ui.loadrating3.text())>0 else 0
        if updateMetrics:
            self.updateMetricsLabel()

    def updateLoadUnits(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.ratingunits[0] = self.energy_ui.ratingunit0.currentIndex()
        self.aw.qmc.ratingunits[1] = self.energy_ui.ratingunit1.currentIndex()
        self.aw.qmc.ratingunits[2] = self.energy_ui.ratingunit2.currentIndex()
        self.aw.qmc.ratingunits[3] = self.energy_ui.ratingunit3.currentIndex()
        if updateMetrics:
            self.updateMetricsLabel()

    def updateSourceTypes(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.sourcetypes[0] = self.energy_ui.sourcetype0.currentIndex()
        self.aw.qmc.sourcetypes[1] = self.energy_ui.sourcetype1.currentIndex()
        self.aw.qmc.sourcetypes[2] = self.energy_ui.sourcetype2.currentIndex()
        self.aw.qmc.sourcetypes[3] = self.energy_ui.sourcetype3.currentIndex()
        if updateMetrics:
            self.updateMetricsLabel()

    def updateLoadEvents(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.load_etypes[0] = self.energy_ui.events0.currentIndex()
        self.aw.qmc.load_etypes[1] = self.energy_ui.events1.currentIndex()
        self.aw.qmc.load_etypes[2] = self.energy_ui.events2.currentIndex()
        self.aw.qmc.load_etypes[3] = self.energy_ui.events3.currentIndex()
        if updateMetrics:
            self.updateMetricsLabel()

    def updatePressurePercent(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.presssure_percents[0] = self.energy_ui.pressureCheckBox0.isChecked()
        self.aw.qmc.presssure_percents[1] = self.energy_ui.pressureCheckBox1.isChecked()
        self.aw.qmc.presssure_percents[2] = self.energy_ui.pressureCheckBox2.isChecked()
        self.aw.qmc.presssure_percents[3] = self.energy_ui.pressureCheckBox3.isChecked()
        if updateMetrics:
            self.updateMetricsLabel()

    def updateMeterLabels(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.meterlabels[0] = self.energy_ui.meter1LabelLineEdit.text()
        self.aw.qmc.meterlabels[1] = self.energy_ui.meter2LabelLineEdit.text()
        if updateMetrics:
            self.updateMetricsLabel()
        self.updateEnergyLabels()

    def updateMeterUnits(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.meterunits[0] = self.energy_ui.meter1UnitComboBox.currentIndex()
        self.aw.qmc.meterunits[1] = self.energy_ui.meter2UnitComboBox.currentIndex()
        if updateMetrics:
            self.updateMetricsLabel()

    def updateMeterFuels(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.meterfuels[0] = self.energy_ui.meter1FuelComboBox.currentIndex()
        self.aw.qmc.meterfuels[1] = self.energy_ui.meter2FuelComboBox.currentIndex()
        if updateMetrics:
            self.updateMetricsLabel()

    def updateMeterSources(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.metersources[0] = self.energy_ui.meter1SourceComboBox.currentIndex()
        self.aw.qmc.metersources[1] = self.energy_ui.meter2SourceComboBox.currentIndex()
        if updateMetrics:
            self.updateMetricsLabel()

    def updateLoadPcts(self, updateMetrics:bool = True) -> None:
        # zeropcts
        self.aw.qmc.loadevent_zeropcts[0] = self.energy_ui.zeropcts0.value()
        self.aw.qmc.loadevent_zeropcts[1] = self.energy_ui.zeropcts1.value()
        self.aw.qmc.loadevent_zeropcts[2] = self.energy_ui.zeropcts2.value()
        self.aw.qmc.loadevent_zeropcts[3] = self.energy_ui.zeropcts3.value()
        # hundpcts
        self.aw.qmc.loadevent_hundpcts[0] = self.energy_ui.hundredpct0.value()
        self.aw.qmc.loadevent_hundpcts[1] = self.energy_ui.hundredpct1.value()
        self.aw.qmc.loadevent_hundpcts[2] = self.energy_ui.hundredpct2.value()
        self.aw.qmc.loadevent_hundpcts[3] = self.energy_ui.hundredpct3.value()
        if updateMetrics:
            self.updateMetricsLabel()

    def updatePreheatDuration(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.preheatDuration = self.validateText2Seconds(self.energy_ui.preheatDuration.text())
        self.energy_ui.preheatDuration.setText(self.validateSeconds2Text(self.aw.qmc.preheatDuration))
        if updateMetrics:
            self.updateMetricsLabel()

    def updateBetweenBatchesDuration(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.betweenbatchDuration = self.validateText2Seconds(self.energy_ui.betweenBatchesDuration.text())
        if updateMetrics:
            self.updateMetricsLabel()

    def updateCoolingDuration(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.coolingDuration = self.validateText2Seconds(self.energy_ui.coolingDuration.text())
        if updateMetrics:
            self.updateMetricsLabel()

    def updatePreheatEnergies(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.preheatenergies[0] = self.pctText2Num(self.energy_ui.preheatenergies0.text())
        self.aw.qmc.preheatenergies[1] = self.pctText2Num(self.energy_ui.preheatenergies1.text())
        self.aw.qmc.preheatenergies[2] = self.pctText2Num(self.energy_ui.preheatenergies2.text())
        self.aw.qmc.preheatenergies[3] = self.pctText2Num(self.energy_ui.preheatenergies3.text())
        if updateMetrics:
            self.updateMetricsLabel()

    def updateBetweenBatchesEnergies(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.betweenbatchenergies[0] = self.pctText2Num(self.energy_ui.betweenbatchesenergy0.text())
        self.aw.qmc.betweenbatchenergies[1] = self.pctText2Num(self.energy_ui.betweenbatchesenergy1.text())
        self.aw.qmc.betweenbatchenergies[2] = self.pctText2Num(self.energy_ui.betweenbatchesenergy2.text())
        self.aw.qmc.betweenbatchenergies[3] = self.pctText2Num(self.energy_ui.betweenbatchesenergy3.text())
        if updateMetrics:
            self.updateMetricsLabel()

    def updateCoolingEnergies(self, updateMetrics:bool = True) -> None:
        self.aw.qmc.coolingenergies[0] = self.pctText2Num(self.energy_ui.coolingenergies0.text())
        self.aw.qmc.coolingenergies[1] = self.pctText2Num(self.energy_ui.coolingenergies1.text())
        self.aw.qmc.coolingenergies[2] = self.pctText2Num(self.energy_ui.coolingenergies2.text())
        self.aw.qmc.coolingenergies[3] = self.pctText2Num(self.energy_ui.coolingenergies3.text())
        if updateMetrics:
            self.updateMetricsLabel()

    def updateBBPafterPreHeat(self) -> None:
        self.aw.qmc.betweenbatch_after_preheat = self.energy_ui.BBPafterPreHeatcheckBox.isChecked()
        self.updateMetricsLabel()

    def updateElectricEnergyMix(self) -> None:
        self.aw.qmc.electricEnergyMix = self.energy_ui.electricEnergyMixSpinBox.value()
        self.updateMetricsLabel()

    def updateGasMix(self) -> None:
        self.aw.qmc.gasMix = self.energy_ui.gasMixSpinBox.value()
        self.updateMetricsLabel()

    # fills the energy config data from the current energy tab widget values
    def updateEnergyConfig(self) -> None:
        if self.tabInitialized[4]:
            self.aw.qmc.energyresultunit_setup = self.energy_ui.resultunitComboBox.currentIndex()
            ## Details tab
            ## Loads tab
            # label
            self.updateLoadLabels(False)
            # rating
            self.updateLoadRatings(False)
            # unit
            self.updateLoadUnits(False)
            # source
            self.updateSourceTypes(False)
            # pressure percent
            self.updatePressurePercent(False)
            # event
            self.updateLoadEvents(False)
            # zeropcts & hundpcts
            self.updateLoadPcts(False)
            ## Protocol tab
            self.updatePreheatDuration(False)
            self.updateBetweenBatchesDuration(False)
            self.updateCoolingDuration(False)
            self.updatePreheatEnergies(False)
            self.updateBetweenBatchesEnergies(False)
            #
            self.updateMetricsLabel()

    def restoreAllEnergySettings(self) -> None:
        if self.tabInitialized[4]:
            self.aw.qmc.loadlabels = self.org_loadlabels.copy()
            self.aw.qmc.loadratings = self.org_loadratings.copy()
            self.aw.qmc.ratingunits = self.org_ratingunits.copy()
            self.aw.qmc.sourcetypes = self.org_sourcetypes.copy()
            self.aw.qmc.load_etypes = self.org_load_etypes.copy()
            self.aw.qmc.presssure_percents = self.org_presssure_percents.copy()
            self.aw.qmc.loadevent_zeropcts = self.org_loadevent_zeropcts.copy()
            self.aw.qmc.loadevent_hundpcts = self.org_loadevent_hundpcts.copy()
            self.aw.qmc.meterlables = self.org_meterlabels.copy()
            self.aw.qmc.meterunits = self.org_meterunits.copy()
            self.aw.qmc.meterfuels = self.org_meterfuels.copy()
            self.aw.qmc.metersources = self.org_metersources.copy()
            self.aw.qmc.preheatDuration = self.org_preheatDuration
            self.aw.qmc.preheatenergies = self.org_preheatenergies.copy()
            self.aw.qmc.betweenbatchDuration = self.org_betweenbatchDuration
            self.aw.qmc.betweenbatchenergies = self.org_betweenbatchenergies.copy()
            self.aw.qmc.coolinghDuration = self.org_coolingDuration
            self.aw.qmc.coolingenergies = self.org_coolingenergies.copy()
            self.aw.qmc.betweenbatch_after_preheat = self.org_betweenbatch_after_preheat
            self.aw.qmc.electricEnergyMix = self.org_electricEnergyMix
            self.aw.qmc.gasMix = self.org_gasMix

    def updateMetricsLabel(self) -> None:
        try:
            # update meter reads in case the meter units changed
            self.aw.qmc.getMeterReads()
            # Recaclulate the energy metrics
            metrics,self.btu_list = self.aw.qmc.calcEnergyuse(self.weightinedit.text()) # pylint: disable=attribute-defined-outside-init
            if len(metrics) > 0 and metrics['BTU_batch'] > 0:
                energy_unit = self.aw.qmc.energyunits[self.aw.qmc.energyresultunit_setup]
                #
                total_energy = scaleFloat2String(self.aw.qmc.convertHeat(metrics['BTU_batch'],'BTU',self.aw.qmc.energyunits[self.aw.qmc.energyresultunit_setup]))
                self.energy_ui.totalEnergyLabel.setText(f'{total_energy} {energy_unit}')
                #
                preheat_energy = scaleFloat2String(self.aw.qmc.convertHeat(metrics['BTU_preheat'],'BTU',self.aw.qmc.energyunits[self.aw.qmc.energyresultunit_setup]))
                self.energy_ui.preheatEnergyLabel.setText(f"{preheat_energy} {energy_unit} ({QApplication.translate('Label','Preheat')})")
                BBP_energy = scaleFloat2String(self.aw.qmc.convertHeat(metrics['BTU_bbp'],'BTU',self.aw.qmc.energyunits[self.aw.qmc.energyresultunit_setup]))
                self.energy_ui.BBPEnergyLabel.setText(f"{BBP_energy} {energy_unit} ({QApplication.translate('Label','BBP')})")
                roast_energy = scaleFloat2String(self.aw.qmc.convertHeat(metrics['BTU_roast'],'BTU',self.aw.qmc.energyunits[self.aw.qmc.energyresultunit_setup]))
                self.energy_ui.roastEnergyLabel.setText(f"{roast_energy} {energy_unit} ({QApplication.translate('Label','Roast')})")

                # a green weight is available
                if self.perKgRoastMode:
                    KWH_per_green = metrics['KWH_roast_per_green_kg']
                    mode = f" ({QApplication.translate('Label','Roast')})"
                else:
                    KWH_per_green = metrics['KWH_batch_per_green_kg']
                    mode = ''
                if KWH_per_green > 0:
                    if KWH_per_green < 1:
                        scaled_energy_kwh = f'{scaleFloat2String(KWH_per_green*1000.)} Wh'
                    else:
                        scaled_energy_kwh = str(scaleFloat2String(KWH_per_green)) + ' kWh'
                    self.energy_ui.EnergyPerKgCoffeeLabel.setText(f"{scaled_energy_kwh} {QApplication.translate('Label','per kg green coffee')}{mode}")
                # no weight is available
                else:
                    self.energy_ui.EnergyPerKgCoffeeLabel.setText('')

                #
                if metrics['CO2_batch'] >= 0:
                    scaled_co2_batch = f"{scaleFloat2String(metrics['CO2_batch'])}g" if metrics['CO2_batch']<1000 else f"{scaleFloat2String(metrics['CO2_batch']/1000.)}kg"
                    self.energy_ui.totalCO2Label.setText(f'{scaled_co2_batch}')
                    #
                    scaled_co2_preheat = f"{scaleFloat2String(metrics['CO2_preheat'])}g" if metrics['CO2_preheat']<1000 else f"{scaleFloat2String(metrics['CO2_preheat']/1000.)}kg"
                    self.energy_ui.preheatCO2label.setText(f"{scaled_co2_preheat} ({QApplication.translate('Label','Preheat')})")
                    scaled_co2_bbp = f"{scaleFloat2String(metrics['CO2_bbp'])}g" if metrics['CO2_bbp']<1000 else f"{scaleFloat2String(metrics['CO2_bbp']/1000.)}kg"
                    self.energy_ui.BBPCO2label.setText(f"{scaled_co2_bbp} ({QApplication.translate('Label','BBP')})")
                    scaled_co2_roast = f"{scaleFloat2String(metrics['CO2_roast'])}g" if metrics['CO2_roast']<1000 else f"{scaleFloat2String(metrics['CO2_roast']/1000.)}kg"
                    self.energy_ui.roastCO2label.setText(f"{scaled_co2_roast} ({QApplication.translate('Label','Roast')})")

                    # a green weight is available
                    if self.perKgRoastMode:
                        CO2_per_green = metrics['CO2_roast_per_green_kg']
                        mode = f" ({QApplication.translate('Label','Roast')})"
                    else:
                        CO2_per_green = metrics['CO2_batch_per_green_kg']
                        mode = ''
                    if CO2_per_green > 0:
                        if CO2_per_green < 1000:
                            scaled_co2_kg = f'{scaleFloat2String(CO2_per_green)}g'
                        else:
                            scaled_co2_kg = f'{scaleFloat2String(CO2_per_green/1000.)}kg'
                        self.energy_ui.CO2perKgCoffeeLabel.setText(f"{scaled_co2_kg} {QApplication.translate('Label','per kg green coffee')}{mode}")
                    # no weight is available
                    else:
                        self.energy_ui.CO2perKgCoffeeLabel.setText('')

            else:
                # clear result widgets
                self.energy_ui.totalEnergyLabel.setText('')
                self.energy_ui.preheatEnergyLabel.setText('')
                self.energy_ui.BBPEnergyLabel.setText('')
                self.energy_ui.roastEnergyLabel.setText('')

                self.energy_ui.EnergyPerKgCoffeeLabel.setText('')

                self.energy_ui.totalCO2Label.setText('')

                self.energy_ui.preheatCO2label.setText('')
                self.energy_ui.BBPCO2label.setText('')
                self.energy_ui.roastCO2label.setText('')

                self.energy_ui.CO2perKgCoffeeLabel.setText('')

        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message','Exception:') + ' updateMetricsLabel() {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @staticmethod
    def formatLoadLabel(tag:str, label:str = '') -> str:
        if len(label) > 0:
            return label
        return f"{QApplication.translate('Label','Load')} {tag}"

    def formatLoadUnitLabel(self, unit:int) -> str:
        return f'({self.aw.qmc.energyunits[unit]})'

    def updateEnergyLabels(self) -> None:
        self.energy_ui.loadALabel.setText(self.formatLoadLabel('A',self.aw.qmc.loadlabels[0]))
        self.energy_ui.loadBLabel.setText(self.formatLoadLabel('B',self.aw.qmc.loadlabels[1]))
        self.energy_ui.loadCLabel.setText(self.formatLoadLabel('C',self.aw.qmc.loadlabels[2]))
        self.energy_ui.loadDLabel.setText(self.formatLoadLabel('D',self.aw.qmc.loadlabels[3]))

    def updateEnergyUnitLabels(self) -> None:
        self.energy_ui.loadAUnitLabel.setText(self.formatLoadUnitLabel(self.energy_ui.ratingunit0.currentIndex()))
        self.energy_ui.loadBUnitLabel.setText(self.formatLoadUnitLabel(self.energy_ui.ratingunit1.currentIndex()))
        self.energy_ui.loadCUnitLabel.setText(self.formatLoadUnitLabel(self.energy_ui.ratingunit2.currentIndex()))
        self.energy_ui.loadDUnitLabel.setText(self.formatLoadUnitLabel(self.energy_ui.ratingunit3.currentIndex()))

    def updateEnableZHpct(self) -> None:
        for ew,zw in [
            (self.energy_ui.events0,self.energy_ui.zeropcts0),
            (self.energy_ui.events1,self.energy_ui.zeropcts1),
            (self.energy_ui.events2,self.energy_ui.zeropcts2),
            (self.energy_ui.events3,self.energy_ui.zeropcts3),
            ]:
            zw.setEnabled(ew.currentIndex() != 0)
        self.updateMetricsLabel()

    ##

    @pyqtSlot(bool)
    def setEnergyLoadDefaults(self, _:bool = False) -> None:
        # ensure that the data from the focused widget gets set
        focusWidget = QApplication.focusWidget()
        if focusWidget:
            focusWidget.clearFocus()
        self.aw.qmc.setEnergyLoadDefaults()
        self.loadsEdited()

    @pyqtSlot(bool)
    def restoreEnergyLoadDefaults(self, _:bool = False) -> None:
        self.aw.qmc.restoreEnergyLoadDefaults()
        self.updateEnergyTab()
        self.loadsEdited()

    @pyqtSlot(bool)
    def setEnergyProtocolDefaults(self, _:bool = False) -> None:
        # ensure that the data from the focused widget gets set
        focusWidget = QApplication.focusWidget()
        if focusWidget:
            focusWidget.clearFocus()
        self.aw.qmc.setEnergyProtocolDefaults()
        self.protocolEdited()

    @pyqtSlot(bool)
    def restoreEnergyProtocolDefaults(self, _:bool = False) -> None:
        self.aw.qmc.restoreEnergyProtocolDefaults()
        self.updateEnergyTab()
        self.protocolEdited()

    @pyqtSlot(bool)
    def copyEnergyDataTabletoClipboard(self, _:bool = False) -> None:
        import prettytable
        nrows = self.energy_ui.datatable.rowCount()
        ncols = self.energy_ui.datatable.columnCount()
        clipboard = ''
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.AltModifier:  #alt click
            tbl = prettytable.PrettyTable()
            fields = []
            for c in range(ncols):
                horizontalHeaderItem = self.energy_ui.datatable.horizontalHeaderItem(c)
                if horizontalHeaderItem is not None:
                    fields.append(horizontalHeaderItem.text())
            tbl.field_names = fields
            for i in range(nrows):
                rows = []
                for j in range(ncols):
                    item = self.energy_ui.datatable.item(i,j)
                    if item is not None:
                        rows.append(item.text())
                tbl.add_row(rows)
            clipboard = tbl.get_string()
        else:
            for c in range(ncols):
                horizontalHeaderItem = self.energy_ui.datatable.horizontalHeaderItem(c)
                if horizontalHeaderItem is not None:
                    clipboard += horizontalHeaderItem.text()
                    if c != (ncols-1):
                        clipboard += '\t'
            clipboard += '\n'
            for r in range(nrows):
                for j in range(ncols):
                    item = self.energy_ui.datatable.item(r,j)
                    if item is not None:
                        clipboard += item.text()
                    if j != (ncols-1):
                        clipboard += '\t'
                    else:
                        clipboard += '\n'
        # copy to the system clipboard
        sys_clip = QApplication.clipboard()
        if sys_clip is not None:
            sys_clip.setText(clipboard)
        self.aw.sendmessage(QApplication.translate('Message','Data table copied to clipboard'))

    ##

    # returns True if the energy loads in the dialog are different to the set defaults
    def energyLoadsModified(self) -> bool:
        return (
            self.aw.qmc.loadlabels != self.aw.qmc.loadlabels_setup or
            self.aw.qmc.loadratings != self.aw.qmc.loadratings_setup or
            self.aw.qmc.ratingunits != self.aw.qmc.ratingunits_setup or
            self.aw.qmc.sourcetypes != self.aw.qmc.sourcetypes_setup or
            self.aw.qmc.load_etypes != self.aw.qmc.load_etypes_setup or
            self.aw.qmc.presssure_percents != self.aw.qmc.presssure_percents_setup or
            self.aw.qmc.loadevent_zeropcts != self.aw.qmc.loadevent_zeropcts_setup or
            self.aw.qmc.loadevent_hundpcts != self.aw.qmc.loadevent_hundpcts_setup or
            self.aw.qmc.meterlabels != self.aw.qmc.meterlabels_setup or
            self.aw.qmc.meterunits != self.aw.qmc.meterunits_setup or
            self.aw.qmc.meterfuels != self.aw.qmc.meterfuels_setup or
            self.aw.qmc.metersources != self.aw.qmc.metersources_setup or
            self.aw.qmc.electricEnergyMix != self.aw.qmc.electricEnergyMix_setup or
            self.aw.qmc.gasMix != self.aw.qmc.gasMix_setup)

    # enables/disables the Defaults/SetDefaults buttons if loads values differ from their set defaults
    def loadsEdited(self) -> None:
        modified = self.energyLoadsModified()
        self.energy_ui.loadsSetDefaultsButton.setEnabled(modified)
        self.energy_ui.loadsDefaultsButtons.setEnabled(modified)

    ##

    @pyqtSlot()
    def loadlabels_editingfinished(self) -> None:
        w = self.sender()
        if w and isinstance(w, QLineEdit) and w.isModified():
            w.setText(w.text().strip())
            self.updateLoadLabels()
            self.loadsEdited()

    @pyqtSlot()
    def loadratings_editingfinished(self) -> None:
        w = self.sender()
        if w and isinstance(w, QLineEdit) and w.isModified():
            w.setText(self.validateNumText(w.text()))
            self.updateLoadRatings()
            self.updateEnergyLabels()
            self.loadsEdited()

    @pyqtSlot()
    def ratingunits_currentindexchanged(self) -> None:
        sender = self.sender()
        if isinstance(sender, QComboBox):
            try:
                i = [self.energy_ui.ratingunit0,self.energy_ui.ratingunit1,self.energy_ui.ratingunit2,self.energy_ui.ratingunit3].index(sender)
                self.aw.qmc.ratingunits[i] = sender.currentIndex()
                self.updateMetricsLabel()
                self.updateEnergyUnitLabels()
                self.loadsEdited()
            except Exception: # pylint: disable=broad-except
                pass

    @pyqtSlot()
    def sourcetypes_currentindexchanged(self) -> None:
        sender = self.sender()
        if isinstance(sender, QComboBox):
            try:
                i = [self.energy_ui.sourcetype0, self.energy_ui.sourcetype1, self.energy_ui.sourcetype2, self.energy_ui.sourcetype3].index(sender)
                self.aw.qmc.sourcetypes[i] = sender.currentIndex()
                self.updateMetricsLabel()
                self.loadsEdited()
            except Exception: # pylint: disable=broad-except
                pass

    @pyqtSlot()
    def load_etypes_currentindexchanged(self) -> None:
        sender = self.sender()
        if isinstance(sender, QComboBox):
            try:
                i = [self.energy_ui.events0, self.energy_ui.events1, self.energy_ui.events2, self.energy_ui.events3].index(sender)
                self.aw.qmc.load_etypes[i] = sender.currentIndex()
                zw = [self.energy_ui.zeropcts0, self.energy_ui.zeropcts1, self.energy_ui.zeropcts2, self.energy_ui.zeropcts3][i]
                zw.setEnabled(sender.currentIndex() != 0)
                self.updateMetricsLabel()
                self.loadsEdited()
            except Exception: # pylint: disable=broad-except
                pass

    @pyqtSlot(int)
    def pressureCheckBox_statechanged(self, _:int) -> None:
        sender = self.sender()
        if isinstance(sender, QCheckBox):
            try:
                i = [self.energy_ui.pressureCheckBox0, self.energy_ui.pressureCheckBox1, self.energy_ui.pressureCheckBox2, self.energy_ui.pressureCheckBox3].index(sender)
                self.aw.qmc.presssure_percents[i] = sender.isChecked()
                self.updateMetricsLabel()
                self.loadsEdited()
            except Exception: # pylint: disable=broad-except
                pass

    @pyqtSlot()
    def loadevent_zeropcts0_valuechanged(self) -> None:
        self.loadevent_pcts_valuechanged(0, 'zero',self.energy_ui.zeropcts0,self.energy_ui.hundredpct0)

    @pyqtSlot()
    def loadevent_zeropcts1_valuechanged(self) -> None:
        self.loadevent_pcts_valuechanged(1, 'zero',self.energy_ui.zeropcts1,self.energy_ui.hundredpct1)

    @pyqtSlot()
    def loadevent_zeropcts2_valuechanged(self) -> None:
        self.loadevent_pcts_valuechanged(2, 'zero',self.energy_ui.zeropcts2,self.energy_ui.hundredpct2)

    @pyqtSlot()
    def loadevent_zeropcts3_valuechanged(self) -> None:
        self.loadevent_pcts_valuechanged(3, 'zero',self.energy_ui.zeropcts3,self.energy_ui.hundredpct3)

    @pyqtSlot()
    def loadevent_hundpcts0_valuechanged(self) -> None:
        self.loadevent_pcts_valuechanged(0, 'hund',self.energy_ui.zeropcts0,self.energy_ui.hundredpct0)

    @pyqtSlot()
    def loadevent_hundpcts1_valuechanged(self) -> None:
        self.loadevent_pcts_valuechanged(1, 'hund',self.energy_ui.zeropcts1,self.energy_ui.hundredpct1)

    @pyqtSlot()
    def loadevent_hundpcts2_valuechanged(self) -> None:
        self.loadevent_pcts_valuechanged(2, 'hund',self.energy_ui.zeropcts2,self.energy_ui.hundredpct2)

    @pyqtSlot()
    def loadevent_hundpcts3_valuechanged(self) -> None:
        self.loadevent_pcts_valuechanged(3, 'hund',self.energy_ui.zeropcts3,self.energy_ui.hundredpct3)

    def loadevent_pcts_valuechanged(self, pos:int, field:str, zeropcts:QSpinBox, hundpcts:QSpinBox) -> None:
        if zeropcts.value() >= hundpcts.value():
            self.aw.sendmessage(QApplication.translate('Message','The 0% value must be less than the 100% value.'))
            QApplication.beep()
            if field == 'zero':
                zeropcts.setValue(hundpcts.value()-1)
                self.aw.qmc.loadevent_zeropcts[pos] = zeropcts.value()
            else:
                hundpcts.setValue(zeropcts.value()+1)
                self.aw.qmc.loadevent_hundpcts[pos] = hundpcts.value()
        else:
            self.aw.qmc.loadevent_zeropcts[pos] = zeropcts.value()
            self.aw.qmc.loadevent_hundpcts[pos] = hundpcts.value()
        self.updateMetricsLabel()
        self.loadsEdited()

    @pyqtSlot()
    def meterlabels_editingfinished(self) -> None:
        w = self.sender()
        if w and isinstance(w, QLineEdit) and w.isModified():
            w.setText(w.text().strip())
            self.updateMeterLabels()
            self.loadsEdited()

    @pyqtSlot()
    def meterunits_currentindexchanged(self) -> None:
        sender = self.sender()
        if isinstance(sender, QComboBox):
            try:
                i = [self.energy_ui.meter1UnitComboBox,self.energy_ui.meter2UnitComboBox].index(sender)
                self.aw.qmc.meterunits[i] = sender.currentIndex()
                self.updateMetricsLabel()
                self.updateMeterLabels()
                self.updateMeterUnits()
                self.loadsEdited()
            except Exception: # pylint: disable=broad-except
                pass

    @pyqtSlot()
    def meterfuels_currentindexchanged(self) -> None:
        sender = self.sender()
        if isinstance(sender, QComboBox):
            try:
                i = [self.energy_ui.meter1FuelComboBox,self.energy_ui.meter2FuelComboBox].index(sender)
                self.aw.qmc.meterfuels[i] = sender.currentIndex()
                self.updateMetricsLabel()
                self.updateMeterFuels()
                self.loadsEdited()
            except Exception: # pylint: disable=broad-except
                pass

    @pyqtSlot()
    def metersources_currentindexchanged(self) -> None:
        sender = self.sender()
        if isinstance(sender, QComboBox):
            try:
                i = [self.energy_ui.meter1SourceComboBox,self.energy_ui.meter2SourceComboBox].index(sender)
                self.aw.qmc.metersources[i] = sender.currentIndex()
                self.updateMetricsLabel()
                self.updateMeterSources()
                self.loadsEdited()
            except Exception: # pylint: disable=broad-except
                pass

    @pyqtSlot()
    def electric_energy_mix_valuechanged(self) -> None:
        self.updateElectricEnergyMix()
        self.loadsEdited()

    @pyqtSlot()
    def gas_energy_mix_valuechanged(self) -> None:
        self.updateGasMix()
        self.loadsEdited()

    #

    # returns True if the energy loads in the dialog are different to the set defaults
    def energyProtocolModified(self) -> bool:
        return (
            self.aw.qmc.preheatDuration != self.aw.qmc.preheatDuration_setup or
            self.aw.qmc.preheatenergies != self.aw.qmc.preheatenergies_setup or
            self.aw.qmc.betweenbatchDuration != self.aw.qmc.betweenbatchDuration_setup or
            self.aw.qmc.betweenbatchenergies != self.aw.qmc.betweenbatchenergies_setup or
            self.aw.qmc.coolingDuration != self.aw.qmc.coolingDuration_setup or
            self.aw.qmc.coolingenergies != self.aw.qmc.coolingenergies_setup or
            self.aw.qmc.betweenbatch_after_preheat != self.aw.qmc.betweenbatch_after_preheat_setup or
            self.aw.qmc.electricEnergyMix != self.aw.qmc.electricEnergyMix_setup or
            self.aw.qmc.gasMix != self.aw.qmc.gasMix_setup)

    # enables/disables the Defaults/SetDefaults buttons if loads values differ from their set defaults
    def protocolEdited(self) -> None:
        modified = self.energyProtocolModified()
        self.energy_ui.protocolSetDefaultsButton.setEnabled(modified)
        self.energy_ui.protocolDefaultsButton.setEnabled(modified)

    @pyqtSlot()
    def preheatDuration_editingfinished(self) -> None:
        self.updatePreheatDuration()
        self.protocolEdited()

    @pyqtSlot()
    def betweenBatchesDuration_editingfinished(self) -> None:
        self.updateBetweenBatchesDuration()
        self.protocolEdited()

    @pyqtSlot()
    def coolingDuration_editingfinished(self) -> None:
        self.updateCoolingDuration()
        self.protocolEdited()

    @pyqtSlot()
    def preheatenergies_editingfinished(self) -> None:
        for w in [self.energy_ui.preheatenergies0,
                    self.energy_ui.preheatenergies1,
                    self.energy_ui.preheatenergies2,
                    self.energy_ui.preheatenergies3]:
            if w.isModified():
                w.setText(self.validatePctText(w.text()))
        self.updatePreheatEnergies()
        self.protocolEdited()

    @pyqtSlot()
    def betweenbatchenergies_editingfinished(self) -> None:
        for w in [self.energy_ui.betweenbatchesenergy0,
                    self.energy_ui.betweenbatchesenergy1,
                    self.energy_ui.betweenbatchesenergy2,
                    self.energy_ui.betweenbatchesenergy3]:
            if w.isModified():
                w.setText(self.validatePctText(w.text()))
        self.updateBetweenBatchesEnergies()
        self.protocolEdited()

    @pyqtSlot()
    def coolingenergies_editingfinished(self) -> None:
        for w in [self.energy_ui.coolingenergies0,
                    self.energy_ui.coolingenergies1,
                    self.energy_ui.coolingenergies2,
                    self.energy_ui.coolingenergies3]:
            if w.isModified():
                w.setText(self.validatePctText(w.text()))
        self.updateCoolingEnergies()
        self.protocolEdited()

    @pyqtSlot(int)
    def betweenbatch_after_preheat_statechanged(self, _:int) -> None:
        self.updateBBPafterPreHeat()
        self.protocolEdited()

    #

    @pyqtSlot()
    def energyresultunitComboBox_indexchanged(self) -> None:
        self.aw.qmc.energyresultunit_setup = self.energy_ui.resultunitComboBox.currentIndex()
        self.updateMetricsLabel()
        if self.energy_ui.tabWidget.currentIndex() == 0:  # Detail (datatable) tab
            self.createEnergyDataTable()

    @pyqtSlot(int)
    def energyTabSwitched(self, i:int) -> None:
        # ensure that the data from the focused widget gets set
        focusWidget = QApplication.focusWidget()
        if focusWidget:
            focusWidget.clearFocus()
        if i == 0:
            self.createEnergyDataTable()
        elif self.tabInitialized[4]:
            # save column widths
            self.aw.qmc.energytablecolumnwidths = [self.energy_ui.datatable.columnWidth(c) for c in range(self.energy_ui.datatable.columnCount())]

    ######

    @staticmethod
    def validateText2Seconds(s:str) -> int:
        try:
            return stringtoseconds(s) if len(s) > 0 else 0
        except Exception:  # pylint: disable=broad-except
            return 0

    @staticmethod
    def validateSeconds2Text(seconds:float) -> str:
        return stringfromseconds(seconds) if seconds > 0 else ''

    @staticmethod
    def validateNumText(s:str) -> str:
        res = ''
        try:
            r = scaleFloat2String(toFloat(comma2dot(str(s))))
            if r != '0':
                res = str(r)
        except Exception: # pylint: disable=broad-except
            pass
        return res

    def validatePctText(self, s:str) -> str:
        res = ''
        try:
            if s == s.strip('%'):
                f = float2float(toFloat(comma2dot(str(s))),2)
                if f < 0:
                    res = str(abs(int(f*1000./10))) + '%'  # using 1000/10 to get around Pythons decimal error ex. .58*100 = 57.999
                else:
                    res = self.validateNumText(s)
            else:
                r = abs(toInt(toFloat(comma2dot(str(s.strip('%'))))))
                if r > 100:
                    res = '100%'
                elif r != 0:
                    res = str(r) + '%'
        except Exception: # pylint: disable=broad-except
            pass
        return res

    @staticmethod
    def pctText2Num(s:str) -> float:
        try:
            res:float
            if len(s) == 0:
                res = 0.
            elif s == s.strip('%'):
                res = toFloat(scaleFloat2String(s))
            else:
                # percentage values are stored as a negative decimal
                res = -float2float(toFloat(s.strip('%'))/100,2)
        except Exception: # pylint: disable=broad-except
            res = 0
        return res


    ###### SETUP TAB #####

    def populateSetupDefaults(self) -> None:
        if self.setup_ui is not None:
            self.setup_ui.labelOrganizationDefault.setText(self.aw.qmc.organization_setup)
            self.setup_ui.labelOperatorDefault.setText(self.aw.qmc.operator_setup)
            self.setup_ui.labelMachineSizeDefault.setText(f'{self.aw.qmc.roastertype_setup} {render_weight(self.aw.qmc.roastersize_setup, 1, weight_units.index(self.aw.qmc.weight[2]))}')
            self.setup_ui.labelHeatingDefault.setText(self.aw.qmc.heating_types[self.aw.qmc.roasterheating_setup])
            self.setup_ui.labelDrumSpeedDefault.setText(self.aw.qmc.drumspeed_setup)

    # returns True if the setup in the dialog is different to the set defaults
    def setupModified(self) -> bool:
        if self.setup_ui is None:
            return False
        return bool(
            self.setup_ui.lineEditOrganization.text() != self.aw.qmc.organization_setup or
            self.setup_ui.lineEditOperator.text() != self.aw.qmc.operator_setup  or
            self.setup_ui.lineEditMachine.text() != self.aw.qmc.roastertype_setup or
            self.setup_ui.doubleSpinBoxRoasterSize.value() != self.aw.qmc.roastersize_setup or
            self.setup_ui.comboBoxHeating.currentIndex() != self.aw.qmc.roasterheating_setup or
            self.setup_ui.lineEditDrumSpeed.text() != self.aw.qmc.drumspeed_setup)

    # enables/disables the Defaults/SetDefaults buttons if setup values differ from their set defaults
    @pyqtSlot()
    @pyqtSlot(int)
    def setupEdited(self,_idx:int = 0) -> None:
        if self.setup_ui is not None:
            modified = self.setupModified()
            self.setup_ui.SetDefaults.setEnabled(modified)
            self.setup_ui.Defaults.setEnabled(modified)

    def initSetupTab(self) -> None:
        if not self.tabInitialized[5]:
            # fill Setup tab
            self.setup_ui = SetupWidget.Ui_SetupWidget()
            self.setup_ui.setupUi(self.C6Widget)
            self.setup_ui.doubleSpinBoxRoasterSize.setLocale(QLocale('C'))
            # explicitly reset labels to have them translated with a controlled context
            self.setup_ui.doubleSpinBoxRoasterSize.setToolTip(QApplication.translate('Tooltip', 'The maximum nominal batch size of the machine in kg'))
            self.setup_ui.labelOrganization.setText(QApplication.translate('Label', 'Organization'))
            self.setup_ui.labelOperator.setText(QApplication.translate('Label', 'Operator'))
            self.setup_ui.groupBoxMachine.setTitle(QApplication.translate('Label', 'Machine'))
            self.setup_ui.labelMachine.setText(QApplication.translate('Label', 'Model'))
            self.setup_ui.labelHeating.setText(QApplication.translate('Label', 'Heating'))
            self.setup_ui.labelDrumSpeed.setText(QApplication.translate('Label', 'Drum Speed'))
            # populate defaults
            self.populateSetupDefaults()
            # populate comboBox
            self.setup_ui.comboBoxHeating.addItems(self.aw.qmc.heating_types)
            self.setup_ui.SetDefaults.setText(QApplication.translate('Button', 'Save Defaults'))
            # hack to access the Qt automatic translation of the RestoreDefaults button
            db = QDialogButtonBox(QDialogButtonBox.StandardButton.RestoreDefaults)
            defaults_button: Optional[QPushButton] = db.button(QDialogButtonBox.StandardButton.RestoreDefaults)
            if defaults_button is not None:
                defaults_button_text_translated = defaults_button.text()
                self.setup_ui.Defaults.setText(defaults_button_text_translated)
            self.setButtonTranslations(self.setup_ui.Defaults,'Restore Defaults',QApplication.translate('Button','Restore Defaults'))

            # fill dialog with data
            self.setup_ui.lineEditOrganization.setText(self.aw.qmc.organization)
            self.setup_ui.lineEditOperator.setText(self.aw.qmc.operator)
            self.setup_ui.lineEditMachine.setText(self.aw.qmc.roastertype)
            self.setup_ui.doubleSpinBoxRoasterSize.setValue(self.aw.qmc.roastersize)
            self.setup_ui.comboBoxHeating.setCurrentIndex(self.aw.qmc.roasterheating)
            self.setup_ui.lineEditDrumSpeed.setText(self.aw.qmc.drumspeed)

            # connect widget signals
            self.setup_ui.lineEditOrganization.editingFinished.connect(self.setupEdited)
            self.setup_ui.lineEditOperator.editingFinished.connect(self.setupEdited)
            self.setup_ui.lineEditMachine.editingFinished.connect(self.setupEdited)
            self.setup_ui.doubleSpinBoxRoasterSize.editingFinished.connect(self.setupEdited)
            self.setup_ui.comboBoxHeating.currentIndexChanged.connect(self.setupEdited)
            self.setup_ui.lineEditDrumSpeed.editingFinished.connect(self.setupEdited)

            # connect button signals
            self.setup_ui.SetDefaults.clicked.connect(self.SetupSetDefaults)
            self.setup_ui.Defaults.clicked.connect(self.SetupDefaults)

            # mark tab as initialized
            self.tabInitialized[5] = True

            # update button states
            self.setupEdited()

    @pyqtSlot(bool)
    def showenergyhelp(self, _:bool = False) -> None:
        from help import energy_help # pyright: ignore [attr-defined] # pylint: disable=no-name-in-module
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate('Form Caption','Energy Help'),
                energy_help.content())

    def closeHelp(self) -> None:
        self.aw.closeHelpDialog(self.helpdialog)

    @pyqtSlot(int)
    def roastflagHeavyFCChanged(self, i:int) -> None:
        if i:
            self.lowFC.setChecked(False)
    @pyqtSlot(int)
    def roastflagLowFCChanged(self, i:int) -> None:
        if i:
            self.heavyFC.setChecked(False)
    @pyqtSlot(int)
    def roastflagLightCutChanged(self, i:int) -> None:
        if i:
            self.darkCut.setChecked(False)
    @pyqtSlot(int)
    def roastflagDarkCutChanged(self, i:int) -> None:
        if i:
            self.lightCut.setChecked(False)
    @pyqtSlot(int)
    def roastflagDropsChanged(self, i:int) -> None:
        if i:
            self.oily.setChecked(False)
    @pyqtSlot(int)
    def roastflagOilyChanged(self, i:int) -> None:
        if i:
            self.drops.setChecked(False)

    @pyqtSlot(int)
    def ambientComboBoxIndexChanged(self, i:int) -> None:
        self.aw.qmc.ambientTempSource = i

    def buildAmbientTemperatureSourceList(self) -> List[str]:
        extra_names = []
        for i in range(len(self.aw.qmc.extradevices)):
            extra_names.append(str(i) + 'xT1: ' + self.aw.qmc.extraname1[i])
            extra_names.append(str(i) + 'xT2: ' + self.aw.qmc.extraname2[i])
        return ['',
                QApplication.translate('ComboBox','ET'),
                QApplication.translate('ComboBox','BT')] + extra_names

    @pyqtSlot(bool)
    def updateAmbientTemp(self, _:bool = False) -> None:
        self.aw.qmc.updateAmbientTemp()
        self.ambientedit.setText(f'{float2float(self.aw.qmc.ambientTemp):g}')
        self.ambientedit.repaint() # seems to be necessary in some PyQt versions!?
        self.ambient_humidity_edit.setText(f'{float2float(self.aw.qmc.ambient_humidity):g}')
        self.ambient_humidity_edit.repaint() # seems to be necessary in some PyQt versions!?
        self.pressureedit.setText(f'{float2float(self.aw.qmc.ambient_pressure):g}')
        self.pressureedit.repaint() # seems to be necessary in some PyQt versions!?

    @pyqtSlot(bool)
    def scanWholeColor(self, _:bool = False) -> None:
        v = self.aw.color.readColor()
        if v is not None and v > -1 and 0 <= v <= 250:
            self.aw.qmc.whole_color = v
            self.whole_color_edit.setText(str(v))

    @pyqtSlot(bool)
    def scanGroundColor(self, _:bool = False) -> None:
        v = self.aw.color.readColor()
        if v is not None and v > -1:
            v = max(0,min(250,v))
            self.aw.qmc.ground_color = v
            self.ground_color_edit.setText(str(v))

    @pyqtSlot(bool)
    def volumeCalculatorTimer(self, _:bool = False) -> None:
        QTimer.singleShot(1, self.volumeCalculator)

    def volumeCalculator(self) -> None:
        weightin:Optional[float] = None
        weightout:Optional[float] = None
        try:
            weightin = float(comma2dot(self.weightinedit.text()))
        except Exception: # pylint: disable=broad-except
            pass
        try:
            weightout = float(comma2dot(self.weightoutedit.text()))
        except Exception: # pylint: disable=broad-except
            pass
        k = 1.
        weightin = weightin * k if weightin is not None else None
        weightout = weightout * k if weightout is not None else None
        tare:float = 0
        try:
            tare_idx = self.tareComboBox.currentIndex() - 3
            if tare_idx > -1:
                tare = self.aw.qmc.container_weights[tare_idx]
        except Exception: # pylint: disable=broad-except
            pass
        self.volumedialog = volumeCalculatorDlg(self,self.aw,
            weightIn=weightin,
            weightOut=weightout,
            weightunit=self.unitsComboBox.currentIndex(),
            volumeunit=self.volumeUnitsComboBox.currentIndex(),
            inlineedit=self.volumeinedit,
            outlineedit=self.volumeoutedit,
            tare=tare)
        if self.volumedialog is not None:
            self.volumedialog.show()
            self.volumedialog.setFixedSize(self.volumedialog.size())

    @pyqtSlot(bool)
    def inWeight(self, _:bool, overwrite:bool = False) -> None:
        QTimer.singleShot(1,lambda : self.setWeight(self.weightinedit,self.bean_density_in_edit,self.moisture_greens_edit,overwrite))

    @pyqtSlot(bool)
    def outWeight(self, _:bool = False, overwrite:bool = False) -> None:
        QTimer.singleShot(1,lambda : self.setWeight(self.weightoutedit,self.bean_density_out_edit,self.moisture_roasted_edit,overwrite))

    @pyqtSlot(bool)
    def defectsWeight(self, _:bool = False, overwrite:bool = False) -> None:
        QTimer.singleShot(1,lambda : self.setWeight(self.weightoutdefectsedit,None,None,overwrite))

    def setWeight(self, weight_edit:QLineEdit, density_edit:Optional[QLineEdit], moisture_edit:Optional[QLineEdit], overwrite:bool = False) -> None:
        tare:float = 0
        try:
            tare_idx = self.tareComboBox.currentIndex() - 3
            if tare_idx > -1:
                tare = self.aw.qmc.container_weights[tare_idx]
        except Exception: # pylint: disable=broad-except
            pass
        #w,d,m = self.aw.scale.readWeight(self.scale_weight) # read value from scale in 'g'
        w = self.scale_weight
        d,m = -1,-1
        if w is not None and w > -1:
            w = w - tare
            wf = convertWeight(w,0,weight_units.index(self.aw.qmc.weight[2])) # convert to weight units
            current_w:float = 0
            try:
                current_w = float(comma2dot(weight_edit.text()))
            except Exception: # pylint: disable=broad-except
                pass
            if overwrite:
                new_w = wf
            else:
                new_w = current_w + wf # we add the new weight to the already existing one!
                self.scale_set = convertWeight(new_w,weight_units.index(self.aw.qmc.weight[2]),0) # convert to weight units
            QTimer.singleShot(2,lambda : self.updateWeightEdits(weight_edit,new_w))
        if density_edit is not None and d is not None and d > -1:
            density_edit.setText(f'{float2float(d):g}')
        if moisture_edit is not None and m is not None and m > -1:
            moisture_edit.setText(f'{float2float(m):g}')
        self.update_scale_weight()

    def updateWeightEdits(self, weight_edit:QLineEdit, w:float) -> None:
        unit = weight_units.index(self.aw.qmc.weight[2])
        if unit == 0: # g selected
            decimals = 1
        elif unit == 1: # kg selected
            decimals = 3
        else:
            decimals = 2
        weight_edit.setText(f'{float2float(w,decimals):g}')
        if weight_edit == self.weightinedit:
            self.weightineditChanged()
        elif weight_edit == self.weightoutedit:
            self.weightouteditChanged()
        elif weight_edit == self.weightoutdefectsedit:
            self.weightoutdefectsChanged()

    @pyqtSlot(int)
    def roastpropertiesChanged(self, _:int = 0) -> None:
        if self.roastproperties.isChecked():
            self.aw.qmc.roastpropertiesflag = 1
        else:
            self.aw.qmc.roastpropertiesflag = 0

    @pyqtSlot(int)
    def labelOriginFlagChanged(self, _:int = 0) -> None:
        plus.stock.coffee_label_normal_order = self.label_origin_flag.isChecked()
        self.populatePlusCoffeeBlendCombos()  # update the plus stock popups to display the correct bean label format

    @pyqtSlot(int)
    def roastpropertiesAutoOpenChanged(self, _:int = 0) -> None:
        if self.roastpropertiesAutoOpen.isChecked():
            self.aw.qmc.roastpropertiesAutoOpenFlag = 1
        else:
            self.aw.qmc.roastpropertiesAutoOpenFlag = 0

    @pyqtSlot(int)
    def roastpropertiesAutoOpenDROPChanged(self, _:int = 0) -> None:
        if self.roastpropertiesAutoOpenDROP.isChecked():
            self.aw.qmc.roastpropertiesAutoOpenDropFlag = 1
        else:
            self.aw.qmc.roastpropertiesAutoOpenDropFlag = 0

    def createDataTable(self) -> None:
        self.datatable.clear()
        ndata = min(len(self.aw.qmc.timex), len(self.aw.qmc.temp1), len(self.aw.qmc.temp2))
        self.datatable.setRowCount(ndata)
        columns = [QApplication.translate('Table', 'Time'),
                                                  self.ETname,
                                                  self.BTname,
                                                  deltaLabelUTF8 + self.ETname,
                                                  deltaLabelUTF8 + self.BTname]
        for i in range(len(self.aw.qmc.extratimex)):
            columns.append(self.aw.qmc.device_name_subst(self.aw.qmc.extraname1[i]))
            columns.append(self.aw.qmc.device_name_subst(self.aw.qmc.extraname2[i]))
        self.datatable.setColumnCount(len(columns))
        self.datatable.setHorizontalHeaderLabels(columns)
        self.datatable.setAlternatingRowColors(True)
        self.datatable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.datatable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.datatable.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection) # QTableWidget.SelectionMode.SingleSelection, ContiguousSelection, MultiSelection
        self.datatable.setShowGrid(True)
        vheader: Optional[QHeaderView] = self.datatable.verticalHeader()
        if vheader is not None:
            vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        offset:float = 0
        if self.aw.qmc.timeindex[0] > -1:
            offset = self.aw.qmc.timex[self.aw.qmc.timeindex[0]]

        for i in range(ndata):
            Rtime = QTableWidgetItem(stringfromseconds(self.aw.qmc.timex[i]-offset))
            Rtime.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            fmtstr = '%.1f' if self.aw.qmc.LCDdecimalplaces else '%.0f'
            ET = QTableWidgetItem(fmtstr%self.aw.qmc.temp1[i])
            BT = QTableWidgetItem(fmtstr%self.aw.qmc.temp2[i])
            ET.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            BT.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            deltaET_str = '--'
            try:
                if i > 0 and (self.aw.qmc.timex[i]-self.aw.qmc.timex[i-1]) and self.aw.qmc.temp1[i] != -1 and self.aw.qmc.temp1[i-1] != -1:
                    rateofchange1 = 60*(self.aw.qmc.temp1[i]-self.aw.qmc.temp1[i-1])/(self.aw.qmc.timex[i]-self.aw.qmc.timex[i-1])
                    if self.aw.qmc.DeltaETfunction is not None and len(self.aw.qmc.DeltaETfunction):
                        try:
                            rateofchange1 = self.aw.qmc.eval_math_expression(self.aw.qmc.DeltaETfunction,self.aw.qmc.timex[i],RTsname='R1',RTsval=rateofchange1)
                        except Exception: # pylint: disable=broad-except
                            pass
                    deltaET_str = f'{rateofchange1:.1f}'
            except Exception: # pylint: disable=broad-except
                pass
            deltaET = QTableWidgetItem(deltaET_str)
            deltaBT_str = '--'
            try:
                if i > 0 and (self.aw.qmc.timex[i]-self.aw.qmc.timex[i-1]) and self.aw.qmc.temp2[i] != -1 and self.aw.qmc.temp2[i-1] != -1:
                    rateofchange2 = 60*(self.aw.qmc.temp2[i]-self.aw.qmc.temp2[i-1])/(self.aw.qmc.timex[i]-self.aw.qmc.timex[i-1])
                    if self.aw.qmc.DeltaBTfunction is not None and len(self.aw.qmc.DeltaBTfunction):
                        try:
                            rateofchange2 = self.aw.qmc.eval_math_expression(self.aw.qmc.DeltaBTfunction,self.aw.qmc.timex[i],RTsname='R2',RTsval=rateofchange2)
                        except Exception: # pylint: disable=broad-except
                            pass
                    deltaBT_str = f'{rateofchange2:.1f}'
            except Exception: # pylint: disable=broad-except
                pass
            deltaBT = QTableWidgetItem(deltaBT_str)
            deltaET.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            deltaBT.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            text:str = ''
            if i in self.aw.qmc.specialevents:
                index = self.aw.qmc.specialevents.index(i)
                text = QApplication.translate('Table', '#{0} {1}{2}').format(
                    str(index+1),
                    self.aw.qmc.etypeAbbrev(self.aw.qmc.etypesf(self.aw.qmc.specialeventstype[index])),
                    self.aw.qmc.eventsvalues(self.aw.qmc.specialeventsvalue[index]))
            self.datatable.setItem(i,0,Rtime)
            tableitem: Optional[QTableWidgetItem]
            if i in self.aw.qmc.specialevents:
                tableitem = self.datatable.item(i,0)
                if tableitem is not None:
                    tableitem.setBackground(QColor('yellow'))

            #identify by color and add notation
            tableitem = self.datatable.item(i,0)
            if tableitem is not None:
                if i == self.aw.qmc.timeindex[0] and i != -1:
                    tableitem.setBackground(QColor('#f07800'))
                    text = QApplication.translate('Table', 'CHARGE')
                elif i == self.aw.qmc.timeindex[1] and i != 0:
                    tableitem.setBackground(QColor('orange'))
                    text = QApplication.translate('Table', 'DRY END')
                elif i == self.aw.qmc.timeindex[2] and i != 0:
                    tableitem.setBackground(QColor('orange'))
                    text = QApplication.translate('Table', 'FC START')
                elif i == self.aw.qmc.timeindex[3] and i != 0:
                    tableitem.setBackground(QColor('orange'))
                    text = QApplication.translate('Table', 'FC END')
                elif i == self.aw.qmc.timeindex[4] and i != 0:
                    tableitem.setBackground(QColor('orange'))
                    text = QApplication.translate('Table', 'SC START')
                elif i == self.aw.qmc.timeindex[5] and i != 0:
                    tableitem.setBackground(QColor('orange'))
                    text = QApplication.translate('Table', 'SC END')
                elif i == self.aw.qmc.timeindex[6] and i != 0:
                    tableitem.setBackground(QColor('#f07800'))
                    text = QApplication.translate('Table', 'DROP')
                elif i == self.aw.qmc.timeindex[7] and i != 0:
                    tableitem.setBackground(QColor('orange'))
                    text = QApplication.translate('Table', 'COOL')
            Rtime.setText(text + ' ' + Rtime.text())

            self.datatable.setItem(i,1,ET)
            self.datatable.setItem(i,2,BT)
            self.datatable.setItem(i,3,deltaET)
            self.datatable.setItem(i,4,deltaBT)
            j = 5
            value:float
            for k in range(len(self.aw.qmc.extratimex)):
                if len(self.aw.qmc.extratemp1) > k:
                    value = -1
                    if len(self.aw.qmc.extratemp1[k]) > i:
                        value = self.aw.qmc.extratemp1[k][i]
                    extra_qtw1 = QTableWidgetItem(fmtstr%value)
                    extra_qtw1.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                    self.datatable.setItem(i,j,extra_qtw1)
                    j = j + 1
                if len(self.aw.qmc.extratemp2) > k:
                    value = -1
                    if len(self.aw.qmc.extratemp2[k]) > i:
                        value = self.aw.qmc.extratemp2[k][i]
                    extra_qtw2 = QTableWidgetItem(fmtstr%value)
                    extra_qtw2.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                    self.datatable.setItem(i,j,extra_qtw2)
                    j = j + 1

        header: Optional[QHeaderView] = self.datatable.horizontalHeader()
        if header is not None:
            self.datatable.resizeColumnsToContents()
            for i in range(1,len(columns)):
                #header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                header.resizeSection(i, max(header.sectionSize(i) + 5, 65))

    def createEventTable(self, force:bool = False) -> None:
        if force or not self.tabInitialized[2]:
            try:
                #### lock shared resources #####
                self.aw.qmc.profileDataSemaphore.acquire(1)

                nevents = len(self.aw.qmc.specialevents)

                #self.eventtable.clear() # this crashes Ubuntu 16.04
        #        if nevents != 0:
        #            self.eventtable.clearContents() # this crashes Ubuntu 16.04 if device table is empty and also sometimes else
                self.eventtable.clearSelection() # this seems to work also for Ubuntu 16.04

                self.eventtable.setRowCount(nevents)
                self.eventtable.setColumnCount(6)
                self.eventtable.setHorizontalHeaderLabels([QApplication.translate('Table', 'Time'),
                                                           self.ETname,
                                                           self.BTname,
                                                           QApplication.translate('Table', 'Description'),
                                                           QApplication.translate('Table', 'Type'),
                                                           QApplication.translate('Table', 'Value')])
                self.eventtable.setAlternatingRowColors(True)
                self.eventtable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                self.eventtable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                self.eventtable.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)

                self.eventtable.setShowGrid(True)

                vheader: Optional[QHeaderView] = self.eventtable.verticalHeader()
                if vheader is not None:
                    vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
                regextime = QRegularExpression(r'^-?[0-9]?[0-9]?[0-9]:[0-5][0-9]$')
                etypes = self.aw.qmc.getetypes()
                #populate table
                for i in range(nevents):
                    #create widgets
                    typeComboBox = MyQComboBox()
                    typeComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
                    typeComboBox.addItems(etypes)
                    typeComboBox.setCurrentIndex(self.aw.qmc.specialeventstype[i])

                    fmtstr = '%.1f' if self.aw.qmc.LCDdecimalplaces else '%.0f'

                    etline = QLineEdit()
                    etline.setReadOnly(True)
                    etline.setAlignment(Qt.AlignmentFlag.AlignRight)
                    try:
                        ettemp = fmtstr%(self.aw.qmc.temp1[self.aw.qmc.specialevents[i]]) + self.aw.qmc.mode
                    except Exception: # pylint: disable=broad-except
                        ettemp = ''
                    etline.setText(ettemp)

                    btline = QLineEdit()
                    btline.setReadOnly(True)
                    btline.setAlignment(Qt.AlignmentFlag.AlignRight)
                    bttemp = fmtstr%(self.aw.qmc.temp2[self.aw.qmc.specialevents[i]]) + self.aw.qmc.mode
                    btline.setText(bttemp)

                    valueEdit = QLineEdit()
                    valueEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
                    valueEdit.setText(self.aw.qmc.eventsvalues(self.aw.qmc.specialeventsvalue[i]))

                    timeline = QLineEdit()
                    timeline.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    if self.aw.qmc.timeindex[0] > -1 and len(self.aw.qmc.timex) > self.aw.qmc.timeindex[0]:
                        timez = stringfromseconds(self.aw.qmc.timex[self.aw.qmc.specialevents[i]]-self.aw.qmc.timex[self.aw.qmc.timeindex[0]])
                    else:
                        timez = stringfromseconds(self.aw.qmc.timex[self.aw.qmc.specialevents[i]])
                    timeline.setText(timez)
                    timeline.setValidator(QRegularExpressionValidator(regextime,self))

                    try:
                        stringline = QLineEdit(self.aw.qmc.specialeventsStrings[i])
                    except Exception: # pylint: disable=broad-except
                        stringline = QLineEdit('')
                    #add widgets to the table
                    self.eventtable.setCellWidget(i,0,timeline)
                    self.eventtable.setCellWidget(i,1,etline)
                    self.eventtable.setCellWidget(i,2,btline)
                    self.eventtable.setCellWidget(i,3,stringline)
                    self.eventtable.setCellWidget(i,4,typeComboBox)
                    self.eventtable.setCellWidget(i,5,valueEdit)
                    valueEdit.setValidator(QIntValidator(0,self.aw.eventsMaxValue,self.eventtable.cellWidget(i,5)))
                header: Optional[QHeaderView] = self.eventtable.horizontalHeader()
                if header is not None:
                    #header.setStretchLastSection(True)
                    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
                    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
                    header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
                    header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
                    header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
                    header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
                # set width of temp / time columns
                self.eventtable.setColumnWidth(0,60)
                self.eventtable.setColumnWidth(1,65)
                self.eventtable.setColumnWidth(2,65)
                self.eventtable.setColumnWidth(5,55)
                # header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
            finally:
                if self.aw.qmc.profileDataSemaphore.available() < 1:
                    self.aw.qmc.profileDataSemaphore.release(1)
            self.tabInitialized[2] = True

    def saveEventTable(self) -> None:
        if self.tabInitialized[2]:
            try:
                #### lock shared resources #####
                self.aw.qmc.profileDataSemaphore.acquire(1)
                nevents = self.eventtable.rowCount()
                for i in range(nevents):
                    try:
                        timez = cast(QLineEdit, self.eventtable.cellWidget(i,0))
                        time_idx: int
                        if self.aw.qmc.timeindex[0] > -1:
                            time_idx = self.aw.qmc.time2index(self.aw.qmc.timex[self.aw.qmc.timeindex[0]]+ stringtoseconds(str(timez.text())))
                        else:
                            time_idx = self.aw.qmc.time2index(stringtoseconds(str(timez.text())))
                        description = cast(QLineEdit, self.eventtable.cellWidget(i,3))
                        etype = cast(MyQComboBox, self.eventtable.cellWidget(i,4))
                        evalue = cast(QLineEdit, self.eventtable.cellWidget(i,5))
                        self.aw.qmc.setEvent(i,
                            time_idx,
                            etype.currentIndex(),
                            description.text(),
                            self.aw.qmc.str2eventsvalue(evalue.text()))
                    except Exception: # pylint: disable=broad-except
                        pass
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
            finally:
                if self.aw.qmc.profileDataSemaphore.available() < 1:
                    self.aw.qmc.profileDataSemaphore.release(1)

    @pyqtSlot(bool)
    def copyDataTabletoClipboard(self, _:bool = False) -> None:
        self.aw.copy_cells_to_clipboard(self.datatable,adjustment=1)
        self.aw.sendmessage(QApplication.translate('Message','Data table copied to clipboard'))

    @pyqtSlot(bool)
    def copyEventTabletoClipboard(self, _:bool = False) -> None:
        import prettytable
        nrows = self.eventtable.rowCount()
        ncols = self.eventtable.columnCount()
        clipboard = ''
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.AltModifier:  #alt click
            tbl = prettytable.PrettyTable()
            fields = []
            for c in range(ncols):
                headeritem = self.eventtable.horizontalHeaderItem(c)
                if headeritem is not None:
                    fields.append(headeritem.text())
            tbl.field_names = fields
            for i in range(nrows):
                rows = []
                timeline = cast(QLineEdit, self.eventtable.cellWidget(i,0))
                rows.append(timeline.text())
                etline = cast(QLineEdit, self.eventtable.cellWidget(i,1))
                rows.append(etline.text())
                btline = cast(QLineEdit, self.eventtable.cellWidget(i,2))
                rows.append(btline.text())
                stringline = cast(QLineEdit, self.eventtable.cellWidget(i,3))
                rows.append(stringline.text())
                typeComboBox = cast(MyQComboBox, self.eventtable.cellWidget(i,4))
                rows.append(typeComboBox.currentText())
                valueEdit = cast(QLineEdit, self.eventtable.cellWidget(i,5))
                rows.append(valueEdit.text())
                tbl.add_row(rows)
            clipboard = tbl.get_string()
        else:
            for c in range(ncols):
                headeritem = self.eventtable.horizontalHeaderItem(c)
                if headeritem is not None:
                    clipboard += headeritem.text()
                    if c != (ncols-1):
                        clipboard += '\t'
            clipboard += '\n'
            for r in range(nrows):
                timeline = cast(QLineEdit, self.eventtable.cellWidget(r,0))
                etline = cast(QLineEdit, self.eventtable.cellWidget(r,1))
                btline = cast(QLineEdit, self.eventtable.cellWidget(r,2))
                stringline = cast(QLineEdit, self.eventtable.cellWidget(r,3))
                typeComboBox = cast(MyQComboBox, self.eventtable.cellWidget(r,4))
                valueEdit = cast(QLineEdit, self.eventtable.cellWidget(r,5))
                clipboard += timeline.text() + '\t'
                clipboard += etline.text() + '\t'
                clipboard += btline.text() + '\t'
                clipboard += stringline.text() + '\t'
                clipboard += typeComboBox.currentText() + '\t'
                clipboard += valueEdit.text() + '\n'
        # copy to the system clipboard
        sys_clip: Optional[QClipboard] = QApplication.clipboard()
        if sys_clip is not None:
            sys_clip.setText(clipboard)
        self.aw.sendmessage(QApplication.translate('Message','Event table copied to clipboard'))

    def createAlarmEventRows(self, rows:List[int]) -> None:
        for r in rows:
            TP = self.aw.findTP()
            if TP:
                self.aw.qmc.alarmflag.append(1)
                self.aw.qmc.alarmguard.append(-1)
                self.aw.qmc.alarmnegguard.append(-1)
                tx = self.aw.qmc.timex[self.aw.qmc.specialevents[r]] - self.aw.qmc.timex[TP]
                ev = 8 # TP
                if tx < 0: # events before TP are moved to CHARGE
                    tx = 1 # set to one second after
                    ev = 0 # CHARGE
                self.aw.qmc.alarmoffset.append(int(round(tx))) # seconds after TP
                self.aw.qmc.alarmtime.append(ev)
                self.aw.qmc.alarmcond.append(1) # rises above (we assume that BT always rises after TP)
                self.aw.qmc.alarmstate.append(-1) # not yet triggered
                self.aw.qmc.alarmsource.append(1) # 1=BT
                self.aw.qmc.alarmtemperature.append(float(round(self.aw.qmc.temp2[self.aw.qmc.specialevents[r]]))) # the BT trigger temperature
                self.aw.qmc.alarmaction.append(self.aw.qmc.specialeventstype[r] + 3) # 3,4,5,6 for slider 0-3
                self.aw.qmc.alarmbeep.append(0)
                self.aw.qmc.alarmstrings.append(str(int(self.aw.qmc.specialeventsvalue[r]*10 - 10)))

    @pyqtSlot(bool)
    def clusterEvents(self, _:bool = False) -> None:
        nevents = len(self.aw.qmc.specialevents)
        if nevents:
            self.aw.clusterEvents()
            self.createEventTable(force=True)
            self.aw.qmc.redraw(recomputeAllDeltas=False)
            self.aw.qmc.fileDirty()

    @pyqtSlot(bool)
    def clearEvents(self, _:bool = False) -> None:
        try:
            #### lock shared resources #####
            self.aw.qmc.profileDataSemaphore.acquire(1)
            nevents = len(self.aw.qmc.specialevents)
            if nevents:
                self.aw.qmc.clearEvents()
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if self.aw.qmc.profileDataSemaphore.available() < 1:
                self.aw.qmc.profileDataSemaphore.release(1)
        self.createEventTable(force=True)
        self.aw.qmc.redraw(recomputeAllDeltas=False)
        self.aw.qmc.fileDirty()

    @pyqtSlot(bool)
    def createAlarmEventTable(self, _:bool = False) -> None:
        if len(self.aw.qmc.specialevents):
            # check for selection
            selected = self.eventtable.selectedRanges()
            rows: List[int]
            if selected and len(selected) > 0:
                rows = []
                for s in selected:
                    top = s.topRow()
                    for x in range(s.rowCount()):
                        rows.append(top + x)
                #rows = [s.topRow() for s in selected]
                self.createAlarmEventRows(rows)
                message = QApplication.translate('Message','Alarms from events #{0} created').format(str([r+1 for r in rows]))
            else:
                rows = list(range(self.eventtable.rowCount()))
                self.createAlarmEventRows(rows)
                message = QApplication.translate('Message','Alarms from events #{0} created').format(str([r+1 for r in rows]))
            self.aw.sendmessage(message)
        else:
            message = QApplication.translate('Message','No events found')
            self.aw.sendmessage(message)

    @pyqtSlot(bool)
    def orderEventTable(self, _:bool = False) -> None:
        self.saveEventTable()
        self.orderEventTableLoop()
        self.aw.qmc.fileDirty()

    def orderEventTableLoop(self) -> None:
        nevents = len(self.aw.qmc.specialevents)
        if nevents:
            event_order_changed = self.aw.orderEvents()
            if event_order_changed:
                self.createEventTable(force=True)
                self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(bool)
    def addEventTable(self, _:bool = False) -> None:
        if len(self.aw.qmc.timex):
            self.saveEventTable()
            self.aw.qmc.addEvent(
                    len(self.aw.qmc.timex)-1,   #qmc.specialevents holds indexes in qmx.timex. Initialize event index
                    0,
                    str(len(self.aw.qmc.specialevents)),
                    0)
            self.createEventTable(force=True)
            self.aw.qmc.redraw(recomputeAllDeltas=False)
            message = QApplication.translate('Message','Event #{0} added').format(str(len(self.aw.qmc.specialevents)))
            self.aw.sendmessage(message)
        else:
            message = QApplication.translate('Message','No profile found')
            self.aw.sendmessage(message)

    @pyqtSlot(bool)
    def deleteEventTable(self, _:bool = False) -> None:
        if len(self.aw.qmc.specialevents):
            self.saveEventTable()
            # check for selection
            selected = self.eventtable.selectedRanges()
            if selected and len(selected) > 0:
                rows = []
                for s in selected:
                    top = s.topRow()
                    rows.extend(list(range(top,top+s.rowCount())))
                self.aw.qmc.deleteEvents(rows)
                message = QApplication.translate('Message',' Events #{0} deleted').format(str([r+1 for r in rows]))
            else:
                self.aw.qmc.popEvent()
                message = QApplication.translate('Message',' Event #{0} deleted').format(str(len(self.aw.qmc.specialevents)+1))
            self.aw.qmc.fileDirty()
            self.createEventTable(force=True)
            self.aw.qmc.redraw(recomputeAllDeltas=False)
            self.aw.sendmessage(message)
        else:
            message = QApplication.translate('Message','No events found')
            self.aw.sendmessage(message)

    # mark widget w if b holds otherwise unmark it
    def markWidget(self, w:QLineEdit, b:bool) -> None:
        if b:
            if self.aw.app.darkmode:
                w.setStyleSheet("""QLineEdit { background-color: #ad0427;  }""")
            else:
                w.setStyleSheet("""QLineEdit { color: #CC0F50; }""")
        else:
            w.setStyleSheet('')

    def checkWeightOut(self) -> None:
        try:
            wi = float(self.weightinedit.text())
            wo = float(self.weightoutedit.text())
            self.markWidget(self.weightoutedit,wi != 0 and wo != 0 and wo > wi)
        except Exception: # pylint: disable=broad-except
            # weightinedit or weightoutedit could be the empty string
            pass

    def checkVolumeOut(self) -> None:
        try:
            vi = float(self.volumeinedit.text())
            vo = float(self.volumeoutedit.text())
            self.markWidget(self.volumeoutedit,vi != 0 and vo != 0 and vo < vi)
        except Exception: # pylint: disable=broad-except
            # volumeinedit or volumeoutedit could be the empty string
            pass

    def checkDensityOut(self) -> None:
        try:
            di = float(self.bean_density_in_edit.text())
            do = float(self.bean_density_out_edit.text())
            self.markWidget(self.bean_density_out_edit,di != 0 and do != 0 and do > di)
        except Exception: # pylint: disable=broad-except
            # bean_density_in_out or bean_density_out_edit could be the empty string
            pass

    def checkMoistureOut(self) -> None:
        try:
            mi = float(self.moisture_greens_edit.text())
            mo = float(self.moisture_roasted_edit.text())
            self.markWidget(self.moisture_roasted_edit,mi != 0 and mo != 0 and mo > mi)
        except Exception: # pylint: disable=broad-except
            # moisture_greens_edit or moisture_roasted_edit could be the empty string
            pass

    @pyqtSlot()
    def weightouteditChanged(self) -> None:
        weight_in:float = 0
        weight_out:float = 0
        try:
            weight_out_text = comma2dot(self.weightoutedit.text().strip())
            if weight_out_text != '':
                weight_out = float(weight_out_text)
        except Exception: # pylint: disable=broad-except
            pass
        try:
            weight_in_text = comma2dot(self.weightinedit.text().strip())
            if weight_in_text != '':
                weight_in = float(weight_in_text)
        except Exception: # pylint: disable=broad-except
            pass
        if weight_units.index(self.aw.qmc.weight[2]) == 1 and weight_out > weight_in > 0:
            # if in kg and weight_out > weight_in, we interpret weight_out in g
            self.weightouteditSetText(f'{float2floatWeightVolume(convertWeight(weight_out,0,1)):g}')
        else:
            self.weightouteditSetText(comma2dot(self.weightoutedit.text().strip()))
        self.percent()
        self.defect_percent()
        if ((self.bean_density_out_edit.text() in {'0',''} and self.volumeoutedit.text() not in {'0',''} and self.weightoutedit.text().strip() not in {'0',''}) or
                (self.volumeoutedit.text() in {'0',''} and self.weightoutedit.text().strip() not in {'0',''})):
            self.calculated_density()
        self.density_out_editing_finished() # recalc volume_out
        if self.weightoutedit.text() != '' and float(self.weightoutedit.text()) != 0:
            self.density_out_editing_finished() # recalc volume_out
        # mark weightoutedit if higher than weightinedit
        self.checkWeightOut()

    @pyqtSlot()
    def weightoutdefectsChanged(self) -> None:
        weight_in:float = 0
        weight_out:float = 0
        defects:float = 0
        try:
            weight_out_text = comma2dot(self.weightoutedit.text().strip())
            if weight_out_text != '':
                weight_out = float(weight_out_text)
        except Exception: # pylint: disable=broad-except
            pass
        try:
            weight_in_text = comma2dot(self.weightinedit.text().strip())
            if weight_in_text != '':
                weight_in = float(weight_in_text)
        except Exception: # pylint: disable=broad-except
            pass
        try:
            defects_text = comma2dot(self.weightoutdefectsedit.text().strip())
            defects = float(defects_text)
            # if in defects mode and unit is kg and defects>50% of weight_out (or weight_in if weight_out is 0) we interpret the input in g
            if (self.aw.qmc.roasted_defects_mode and weight_units.index(self.aw.qmc.weight[2]) == 1 and
                ((defects > weight_out*0.5>0) or (weight_out == 0 and defects > weight_in*0.5>0))):
                defects = convertWeight(defects,0,1)
        except Exception: # pylint: disable=broad-except
            pass
        if weight_out > 0:
            defects = min(weight_out, max(0, defects)) # 0 <= defects <= weight_out
        else:
            defects = min(weight_in, max(0, defects)) # 0 <= defects <= weight_in
        dw_txt = f'{float2floatWeightVolume(defects):g}'
        if self.aw.qmc.roasted_defects_mode or dw_txt != '0':
            self.weightoutdefectsedit.setText(dw_txt)
        else:
            self.weightoutdefectsedit.setText('')
        self.defect_percent()

    def checkWeightIn(self) -> None:
        enough = True
        enough_replacement = False
        weightIn = 0.0
        try:
            weightIn = float(comma2dot(self.weightinedit.text()))
        except Exception: # pylint: disable=broad-except
            pass
        if self.plus_amount_selected is not None:
            try:
                # convert weight to kg
                weightUnit = self.unitsComboBox.currentText()
                if weightUnit == 'kg':
                    wc = weightIn
                else:
                    wc = convertWeight(weightIn,weight_units.index(weightUnit),weight_units.index('Kg'))
                if wc > self.plus_amount_selected:
                    enough = False
            except Exception: # pylint: disable=broad-except
                pass
        if self.plus_amount_replace_selected is not None:
            try:
                # convert weight to kg
                weightUnit = self.unitsComboBox.currentText()
                if weightUnit == 'kg':
                    wc = weightIn
                else:
                    wc = convertWeight(weightIn,weight_units.index(self.unitsComboBox.currentText()),weight_units.index('Kg'))
                if wc <= self.plus_amount_replace_selected:
                    enough_replacement = True
            except Exception: # pylint: disable=broad-except
                pass
        if enough:
            self.weightinedit.setStyleSheet('')
        elif self.aw.app.darkmode:
            self.weightinedit.setStyleSheet("""QLineEdit { background-color: #ad0427;  }""")
        elif enough_replacement:
            self.weightinedit.setStyleSheet("""QLineEdit { color: #0A5C90; }""")
        else:
            self.weightinedit.setStyleSheet("""QLineEdit { color: #CC0F50; }""")

    @pyqtSlot()
    def weightineditChanged(self) -> None:
        self.weightinedit.setText(comma2dot(str(self.weightinedit.text())))
        self.weightinedit.repaint()
        self.percent()
        self.defect_percent()
        keep_modified_density:Optional[str] = self.modified_density_in_text
        if ((self.bean_density_in_edit.text() in {'0',''} and self.volumeinedit.text() not in {'0',''} and self.weightinedit.text().strip() not in {'0',''}) or
                (self.volumeinedit.text() in {'0',''} and self.weightinedit.text().strip() not in {'0',''})):
            self.calculated_density()
            keep_modified_density = self.modified_density_in_text
        self.density_in_editing_finished() # recalc volume_in
        if keep_modified_density is not None:
            self.modified_density_in_text = keep_modified_density
        self.recentRoastEnabled()
        if self.aw.plus_account is not None:
            blend_idx = self.plus_blends_combo.currentIndex()
            if blend_idx > 0:
                self.blendSelectionChanged(blend_idx)
            coffee_idx = self.plus_coffees_combo.currentIndex()
            if coffee_idx > 0:
                self.coffeeSelectionChanged(coffee_idx)
        self.checkWeightOut()

    def density_percent(self) -> None:
        percent = 0.
        try:
            if self.bean_density_out_edit.text() != '' and float(comma2dot(self.bean_density_out_edit.text())) != 0.0:
                percent = self.aw.weight_loss(float(comma2dot(str(self.bean_density_in_edit.text()))),float(comma2dot(str(self.bean_density_out_edit.text()))))
        except Exception: # pylint: disable=broad-except
            pass
        if percent <= 0:
            self.densitypercentlabel.setText('')
        else:
            percentstring = f'-{float2float(percent, self.aw.percent_decimals)}%'
            self.densitypercentlabel.setText(percentstring)    #density percent loss

    def moisture_percent(self) -> None:
        percent = 0.
        try:
            m_roasted = float(comma2dot(str(self.moisture_roasted_edit.text())))
            if m_roasted != 0.0:
                percent = float(comma2dot(str(self.moisture_greens_edit.text()))) - m_roasted
        except Exception: # pylint: disable=broad-except
            pass
        if percent <= 0:
            self.moisturepercentlabel.setText('')
        else:
            percentstring = f'-{float2float(percent, self.aw.percent_decimals)}%'
            self.moisturepercentlabel.setText(percentstring)    #density percent loss

    def percent(self) -> None:
        percent = 0.
        try:
            if self.weightoutedit.text() != '' and float(comma2dot(self.weightoutedit.text())) != 0.0:
                percent = self.aw.weight_loss(float(comma2dot(self.weightinedit.text())),float(comma2dot(self.weightoutedit.text())))
        except Exception: # pylint: disable=broad-except
            pass
        if percent > 0:
            percentstring = f'-{float2float(percent, self.aw.percent_decimals)}%'
            self.weightpercentlabel.setText(percentstring)    #weight percent loss
        else:
            self.weightpercentlabel.setText('')

    def defect_percent(self) -> None:
        percent = 0.
        percentstring = ''
        try:
            defects:float = (float(comma2dot(self.weightoutdefectsedit.text())) if self.weightoutdefectsedit.text() != '' else 0)
            weight_out:float = (float(comma2dot(self.weightoutedit.text())) if self.weightoutedit.text() != '' else 0)
            if 0 <= defects <= weight_out:
                if self.aw.qmc.roasted_defects_mode:
                    percent = self.aw.weight_loss(weight_out,weight_out-defects)
                else:
                    percent = self.aw.weight_loss(weight_out,defects)
                if 100 > percent > 0:
                    percentstring = f'-{float2float(percent, self.aw.percent_decimals)}%'
        except Exception: # pylint: disable=broad-except
            pass
        self.weightoutdefectspercentlabel.setText(percentstring)    #defect weight percent

    @pyqtSlot()
    def volume_percent(self) -> None:
        self.volumeinedit.setText(comma2dot(self.volumeinedit.text()))
        self.volumeoutedit.setText(comma2dot(self.volumeoutedit.text()))
        self.modified_volume_in_text = str(self.volumeinedit.text())
        percent = 0.
        try:
            if self.volumeoutedit.text() != '' and float(comma2dot(self.volumeoutedit.text())) != 0.0:
                percent = self.aw.volume_increase(float(comma2dot(self.volumeinedit.text())),float(comma2dot(self.volumeoutedit.text())))
        except Exception: # pylint: disable=broad-except
            pass
        if percent == 0:
            self.volumepercentlabel.setText('')
        else:
            percentstring = f'{percent:.2f}%'
            self.volumepercentlabel.setText(percentstring)    #volume percent gain
        self.calculated_density()
        self.checkVolumeOut()

    # calculates density in g/l from weightin/weightout and volumein/volumeout
    def calc_density(self) -> Tuple[float,float]:
        din = dout = 0.0
        try:
            if self.volumeinedit.text() != '' and self.weightinedit.text() != '':
                volumein = float(comma2dot(self.volumeinedit.text()))
                weightin = float(comma2dot(self.weightinedit.text()))
                if volumein != 0.0 and weightin != 0.0:
                    vol_idx = volume_units.index(self.volumeUnitsComboBox.currentText())
                    volumein = convertVolume(volumein,vol_idx,0)
                    weight_idx = weight_units_lower.index(self.unitsComboBox.currentText())
                    weightin = convertWeight(weightin,weight_idx,0)
                    din = weightin / volumein
            if self.volumeoutedit.text() != ''  and self.weightoutedit.text() != '':
                volumeout = float(comma2dot(self.volumeoutedit.text()))
                weightout = float(comma2dot(self.weightoutedit.text()))
                if volumeout != 0.0 and weightout != 0.0:
                    vol_idx = volume_units.index(self.volumeUnitsComboBox.currentText())
                    volumeout = convertVolume(volumeout,vol_idx,0)
                    weight_idx = weight_units_lower.index(self.unitsComboBox.currentText())
                    weightout = convertWeight(weightout,weight_idx,0)
                    dout = weightout / volumeout
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        return din,dout

    @pyqtSlot(int)
    def calculated_density(self, _:int = 0) -> None:
        din, dout = self.calc_density()
        if din > 0.:
            # set also the green density if not yet set
            self.bean_density_in_edit.setText(f'{float2float(din):g}')
        if  dout > 0.:
            # set also the roasted density if not yet set
            self.bean_density_out_edit.setText(f'{float2float(dout):g}')
        self.density_percent()
        self.calculated_organic_loss()
        self.checkDensityOut()

    def calc_organic_loss(self) -> Tuple[float,float]:
        wloss = 0. # weight (moisture + organic)
        mloss = 0. # moisture
        try:
            if self.weightpercentlabel.text() and self.weightpercentlabel.text() != '':
                wloss = abs(float(comma2dot(self.weightpercentlabel.text()).split('%')[0]))
        except Exception: # pylint: disable=broad-except
            pass
        try:
            if self.moisturepercentlabel.text() and self.moisturepercentlabel.text() != '':
                mloss = abs(float(comma2dot(self.moisturepercentlabel.text()).split('%')[0]))
        except Exception: # pylint: disable=broad-except
            pass
        if mloss != 0. and wloss != 0.:
            return mloss, float2float(max(min(wloss - mloss,100),0),self.aw.percent_decimals)
        return 0., 0.

    def calculated_organic_loss(self) -> None:
        self.moisture_percent()
        mloss, oloss = self.calc_organic_loss()
        if oloss > 0. and mloss > 0.:
            self.organiclosslabel.setText(QApplication.translate('Label', 'organic material'))
            self.organicpercentlabel.setText(f'-{oloss}%')
        else:
            self.organiclosslabel.setText('')
            self.organicpercentlabel.setText('')

    @pyqtSlot()
    def greens_temp_editing_finished(self) -> None:
        self.greens_temp_edit.setText(comma2dot(str(self.greens_temp_edit.text())))

    @pyqtSlot()
    def ambientedit_editing_finished(self) -> None:
        self.ambientedit.setText(comma2dot(str(self.ambientedit.text())))

    @pyqtSlot()
    def ambient_humidity_editing_finished(self) -> None:
        self.ambient_humidity_edit.setText(comma2dot(str(self.ambient_humidity_edit.text())))

    @pyqtSlot()
    def pressureedit_editing_finished(self) -> None:
        self.pressureedit.setText(comma2dot(str(self.pressureedit.text())))

    @pyqtSlot()
    def density_in_editing_finished(self) -> None:
        self.bean_density_in_edit.setText(comma2dot(str(self.bean_density_in_edit.text())))
        self.modified_density_in_text = str(self.bean_density_in_edit.text())
        if self.bean_density_in_edit.text() != '':
            density_in = float(comma2dot(self.bean_density_in_edit.text()))
            if density_in != 0:
                if self.weightinedit.text() != '': # and self.volumeinedit.text().strip() in {'0',''}: # prefer to recompute volume which is seldom measured
                    # if density-in and weight-in is given, we re-calc volume-in:
                    weight_in = float(comma2dot(self.weightinedit.text()))
                    if weight_in != 0:
                        weight_in = convertWeight(weight_in,self.unitsComboBox.currentIndex(),weight_units.index('g'))
                        volume_in = weight_in / density_in # in g/l
                        # convert to selected volume unit
                        volume_in = convertVolume(volume_in,volume_units.index('l'),self.volumeUnitsComboBox.currentIndex())
                        self.volumeinedit.setText(f'{float2floatWeightVolume(volume_in):g}')
                        self.volume_percent()
                if self.volumeinedit.text() != '' and self.weightinedit.text().strip() in {'0',''}:
                    # if density-in and volume-in is given, we re-calc weight-in:
                    volume_in = float(comma2dot(self.volumeinedit.text()))
                    if volume_in != 0:
                        # convert volume in to l and calculate weight in
                        volume_in = convertVolume(volume_in,self.volumeUnitsComboBox.currentIndex(),volume_units.index('l'))
                        weight_in =  volume_in * density_in # in g/l
                        weight_in = convertWeight(weight_in,weight_units.index('g'),self.unitsComboBox.currentIndex())
                        self.weightinedit.setText(f'{float2floatWeightVolume(weight_in):g}')
                        self.percent()
                        self.calculated_organic_loss()
            else:
                self.volume_percent()

    @pyqtSlot()
    def density_out_editing_finished(self) -> None:
        self.bean_density_out_edit.setText(comma2dot(str(self.bean_density_out_edit.text())))
        if self.bean_density_out_edit.text() != '':
            density_out = float(self.bean_density_out_edit.text())
            if density_out != 0:
                if self.weightoutedit.text() != '': # and self.volumeoutedit.text().strip() in {'0',''}:
                    # if density-out and weight-out is given, we re-calc volume-out:
                    weight_out = float(comma2dot(self.weightoutedit.text()))
                    if weight_out != 0:
                        weight_out = convertWeight(weight_out,self.unitsComboBox.currentIndex(),weight_units.index('g'))
                        volume_out = weight_out / density_out # in g/l
                        # convert to selected volume unit
                        volume_out = convertVolume(volume_out,volume_units.index('l'),self.volumeUnitsComboBox.currentIndex())
                        self.volumeoutedit.setText(f'{float2floatWeightVolume(volume_out):g}')
                        self.volume_percent()
                if self.volumeoutedit.text() != '' and self.weightoutedit.text().strip() in {'0',''}:
                    # if density-out and volume-out is given, we re-calc weight-out:
                    volume_out = float(comma2dot(self.volumeoutedit.text()))
                    if volume_out != 0:
                        # convert volume out to l and calculate weight out
                        volume_out = convertVolume(volume_out,self.volumeUnitsComboBox.currentIndex(),volume_units.index('l'))
                        weight_out = volume_out * density_out # in g/l
                        weight_out = convertWeight(weight_out,weight_units.index('g'),self.unitsComboBox.currentIndex())
                        self.weightouteditSetText(f'{float2floatWeightVolume(weight_out):g}')
                        self.percent()
                        self.calculated_organic_loss()
            else:
                self.volume_percent()

    @pyqtSlot()
    def volume_in_editing_finished(self) -> None:
        self.volumeinedit.setText(comma2dot(str(self.volumeinedit.text())))
        if self.volumeinedit.text() != '':
            volume_in = float(self.volumeinedit.text())
            # convert volume in to l and calculate volume in
            volume_in = convertVolume(volume_in,self.volumeUnitsComboBox.currentIndex(),volume_units.index('l'))
            if volume_in != 0:
                if self.weightinedit.text() != '' and self.bean_density_in_edit.text().strip() in {'0',''}:
                    # if volume-in and weight-in is given, we re-calc density-in:
                    weight_in = float(comma2dot(self.weightinedit.text()))
                    if weight_in != 0:
                        weight_in = convertWeight(weight_in,self.unitsComboBox.currentIndex(),weight_units.index('g'))
                        density_in = weight_in / volume_in # in g/l
                        self.bean_density_in_edit.setText(f'{float2float(density_in):g}')
                        self.volume_percent()
                if self.bean_density_in_edit.text() != '' and self.weightinedit.text().strip() in {'0',''}:
                    # if volume-in and density-in is given, we re-calc weight-in:
                    density_in = float(comma2dot(self.bean_density_in_edit.text()))
                    if density_in != 0:
                        weight_in =  volume_in * density_in # in g/l
                        weight_in = convertWeight(weight_in,weight_units.index('g'),self.unitsComboBox.currentIndex())
                        self.weightinedit.setText(f'{float2floatWeightVolume(weight_in):g}')
                        self.percent()
                        self.calculated_organic_loss()
            else:
                self.volume_percent()

    @pyqtSlot()
    def volume_out_editing_finished(self) -> None:
        self.volumeoutedit.setText(comma2dot(str(self.volumeoutedit.text())))
        if self.volumeoutedit.text() != '':
            volume_out = float(self.volumeoutedit.text())
            # convert volume in to l and calculate volume in
            volume_out = convertVolume(volume_out,self.volumeUnitsComboBox.currentIndex(),volume_units.index('l'))
            if volume_out != 0:
                if self.weightoutedit.text() != '' and self.bean_density_out_edit.text().strip() in {'0',''}:
                    # if volume-out and weight-out is given, we re-calc density-out:
                    weight_out = float(comma2dot(self.weightoutedit.text()))
                    if weight_out != 0:
                        weight_out = convertWeight(weight_out,self.unitsComboBox.currentIndex(),weight_units.index('g'))
                        density_out = weight_out / volume_out # in g/l
                        self.bean_density_out_edit.setText(f'{float2float(density_out):g}')
                        self.volume_percent()
                if self.bean_density_out_edit.text() != '' and self.weightoutedit.text().strip() in {'0',''}:
                    # if volume-out and density-out is given, we re-calc weight-out:
                    density_out = float(comma2dot(self.bean_density_out_edit.text()))
                    if density_out != 0:
                        weight_out =  volume_out * density_out # in g/l
                        weight_out = convertWeight(weight_out,weight_units.index('g'),self.unitsComboBox.currentIndex())
                        self.weightouteditSetText(f'{float2floatWeightVolume(weight_out):g}')
                        self.percent()
                        self.calculated_organic_loss()
            else:
                self.volume_percent()

    def saveMainEvents(self) -> None:
        if self.chargeedit.text() == '':
            if self.aw.qmc.timeindex[0]>-1:
                # if charge was set before and got removed,
                # we keep xaxis limit the same but adjust to updated timeindex[0] mark
                self.aw.qmc.startofx -= self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
            self.aw.qmc.timeindex[0] = -1
        elif self.chargeeditcopy != str(self.chargeedit.text()):
            #if there is a CHARGE recorded and the time entered is positive. Use relative time
            if stringtoseconds(str(self.chargeedit.text())) > 0 and self.aw.qmc.timeindex[0] != -1:
                startindex = self.aw.qmc.time2index(self.aw.qmc.timex[self.aw.qmc.timeindex[0]] + stringtoseconds(str(self.chargeedit.text())))
                timeindex_before = self.aw.qmc.timeindex[0]
                self.aw.qmc.timeindex[0] = max(-1,startindex)
                self.aw.qmc.startofx += (self.aw.qmc.timex[self.aw.qmc.timeindex[0]] - self.aw.qmc.timex[timeindex_before])
            #if there is a CHARGE recorded and the time entered is negative. Use relative time
            elif stringtoseconds(str(self.chargeedit.text())) < 0 and self.aw.qmc.timeindex[0] != -1:
                relativetime = self.aw.qmc.timex[self.aw.qmc.timeindex[0]]-abs(stringtoseconds(str(self.chargeedit.text())))
                startindex = self.aw.qmc.time2index(relativetime)
                timeindex_before = self.aw.qmc.timeindex[0]
                self.aw.qmc.timeindex[0] = max(-1,startindex)
                self.aw.qmc.startofx += (self.aw.qmc.timex[self.aw.qmc.timeindex[0]] - self.aw.qmc.timex[timeindex_before])
            #if there is _no_ CHARGE recorded and the time entered is positive. Use absolute time
            elif stringtoseconds(str(self.chargeedit.text())) > 0 and self.aw.qmc.timeindex[0] == -1:
                startindex = self.aw.qmc.time2index(stringtoseconds(str(self.chargeedit.text())))
                self.aw.qmc.timeindex[0] = max(-1,startindex)
                self.aw.qmc.startofx += self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
            #if there is _no_ CHARGE recorded and the time entered is negative. ERROR
            elif stringtoseconds(str(self.chargeedit.text())) < 0 and self.aw.qmc.timeindex[0] == -1:
                self.aw.qmc.adderror(QApplication.translate('Error Message', 'Unable to move CHARGE to a value that does not exist'))
            self.chargeeditcopy = str(self.chargeedit.text())
        # check CHARGE (with index self.aw.qmc.timeindex[0])
        start: float
        if self.aw.qmc.timeindex[0] == -1:
            start = 0                   #relative start time
        else:
            start = self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
        if self.dryeditcopy != str(self.dryedit.text()):
            s = stringtoseconds(str(self.dryedit.text()))
            if s <= 0:
                self.aw.qmc.timeindex[1] = 0
            else:
                dryindex = self.aw.qmc.time2index(start + s)
                self.aw.qmc.timeindex[1] = max(0,dryindex)
            self.dryeditcopy = str(self.dryedit.text())
        if self.Cstarteditcopy != str(self.Cstartedit.text()):
            s = stringtoseconds(str(self.Cstartedit.text()))
            if s <= 0:
                self.aw.qmc.timeindex[2] = 0
            else:
                fcsindex = self.aw.qmc.time2index(start + s)
                self.aw.qmc.timeindex[2] = max(0,fcsindex)
            self.Cstarteditcopy = str(self.Cstartedit.text())
        if self.Cendeditcopy != str(self.Cendedit.text()):
            s = stringtoseconds(str(self.Cendedit.text()))
            if s <= 0:
                self.aw.qmc.timeindex[3] = 0
            else:
                fceindex = self.aw.qmc.time2index(start + s)
                self.aw.qmc.timeindex[3] = max(0,fceindex)
            self.Cendeditcopy = str(self.Cendedit.text())
        if self.CCstarteditcopy != str(self.CCstartedit.text()):
            s = stringtoseconds(str(self.CCstartedit.text()))
            if s <= 0:
                self.aw.qmc.timeindex[4] = 0
            else:
                scsindex = self.aw.qmc.time2index(start + s)
                self.aw.qmc.timeindex[4] = max(0,scsindex)
            self.CCstarteditcopy = str(self.CCstartedit.text())
        if self.CCendeditcopy != str(self.CCendedit.text()):
            s = stringtoseconds(str(self.CCendedit.text()))
            if s <= 0:
                self.aw.qmc.timeindex[5] = 0
            elif stringtoseconds(str(self.CCendedit.text())) > 0:
                sceindex = self.aw.qmc.time2index(start + s)
                self.aw.qmc.timeindex[5] = max(0,sceindex)
            self.CCendeditcopy = str(self.CCendedit.text())
        if self.dropeditcopy != str(self.dropedit.text()):
            s = stringtoseconds(str(self.dropedit.text()))
            if s <= 0:
                self.aw.qmc.timeindex[6] = 0
            else:
                dropindex = self.aw.qmc.time2index(start + s)
                self.aw.qmc.timeindex[6] = max(0,dropindex)
            self.dropeditcopy = str(self.dropedit.text())
        if self.cooleditcopy != str(self.cooledit.text()):
            s = stringtoseconds(str(self.cooledit.text()))
            if s <= 0:
                self.aw.qmc.timeindex[7] = 0
            else:
                coolindex = self.aw.qmc.time2index(start + s)
                self.aw.qmc.timeindex[7] = max(0,coolindex)
            self.cooleditcopy = str(self.cooledit.text())
        if self.aw.qmc.phasesbuttonflag:
            # adjust phases by DryEnd and FCs events
            if self.aw.qmc.timeindex[1]:
                self.aw.qmc.phases[1] = max(0,int(round(self.aw.qmc.temp2[self.aw.qmc.timeindex[1]])))
            if self.aw.qmc.timeindex[2]:
                self.aw.qmc.phases[2] = max(0,int(round(self.aw.qmc.temp2[self.aw.qmc.timeindex[2]])))

    @pyqtSlot()
    def accept(self) -> None:
        #check for graph
        if len(self.aw.qmc.timex):
            #prevents accidentally deleting a modified profile.
            self.aw.qmc.fileDirty()
            self.saveMainEvents()
            if self.aw.qmc.timeindex[0] != self.org_timeindex[0]:
                self.aw.qmc.xaxistosm(redraw=False) # we update axis if CHARGE event changed
                self.aw.qmc.timealign(redraw=False)

            self.saveEventTable()
            self.aw.orderEvents()
            self.aw.qmc.redraw_keep_view(recomputeAllDeltas=False)
        # Update Title
        self.aw.qmc.title = ' '.join(self.titleedit.currentText().split())
        self.aw.qmc.title_show_always = self.titleShowAlwaysFlag.isChecked()
        self.aw.qmc.container_idx = self.tareComboBox.currentIndex() - 3

#PLUS
        # Update Plus
        if self.aw.plus_account is not None:
            self.aw.qmc.plus_default_store = self.plus_default_store
            self.aw.qmc.plus_store = self.plus_store_selected
            self.aw.qmc.plus_store_label = self.plus_store_selected_label
            self.aw.qmc.plus_coffee = self.plus_coffee_selected
            self.aw.qmc.plus_coffee_label = self.plus_coffee_selected_label
            if self.aw.qmc.plus_coffee is None:
                self.aw.qmc.plus_coffee_label = None
                self.aw.qmc.plus_blend_label = self.plus_blend_selected_label
                self.aw.qmc.plus_blend_spec = self.plus_blend_selected_spec
                self.aw.qmc.plus_blend_spec_labels = self.plus_blend_selected_spec_labels
            else:
                self.aw.qmc.plus_blend_label = None
                self.aw.qmc.plus_blend_spec =  None
                self.aw.qmc.plus_blend_spec_labels = None
            # if weight unit changed we update the scheduler window if open
            if self.aw.schedule_window is not None and self.org_weight[2] != self.aw.qmc.weight[2]:
                self.aw.updateScheduleSignal.emit()

        # Update beans
        self.aw.qmc.beans = self.beansedit.toPlainText()
        #update ambient temperature source
        self.aw.qmc.ambientTempSource = self.ambientComboBox.currentIndex()
        #update weight
        w0:float
        w1:float
        w2 = self.aw.qmc.weight[2]
        try:
            w0 = float(comma2dot(self.weightinedit.text()))
        except Exception: # pylint: disable=broad-except
            w0 = 0
        if w0 == 0 and self.aw.qmc.last_batchsize == 0:
            self.aw.qmc.last_batchsize = convertWeight(self.aw.qmc.roastersize_setup,1,0)
            w0 = convertWeight(self.aw.qmc.roastersize_setup,1,weight_units.index(w2))
            w1 = 0
        else:
            self.aw.qmc.last_batchsize = convertWeight(w0,weight_units.index(w2),0) # remember last used batch size (in g)
        try:
            w1 = float(comma2dot(self.weightoutedit.text()))
        except Exception: # pylint: disable=broad-except
            w1 = 0
        w2 = self.unitsComboBox.currentText()

        # update defect weight
        try:
            dw = float(comma2dot(self.weightoutdefectsedit.text()))
        except Exception: # pylint: disable=broad-except
            dw = 0

        if self.aw.qmc.roasted_defects_mode:
            self.aw.qmc.roasted_defects_weight = dw
        elif w1 == 0:
            # if not self.aw.qmc.roasted_defects_mode and w1==0 and dw!=0, we set w1=yield and defects weight = 0
            w1 = dw
            self.aw.qmc.roasted_defects_weight = 0
        else:
            # we interpret dw as yield
            self.aw.qmc.roasted_defects_weight = min(w1, max(0, w1 - dw))

        # max 140kg green; roasted < green:
        if w2 == 'kg':
            w2 = 'Kg'
            if w0 > 140:
                w0 = 0
        elif (w2 == 'g' and w0 > 140*1000) or (w2 == 'lb' and w0 > 308.5) or (w2 == 'oz' and w0 > 4938):
            w0 = 0
        w1 = min(w0,w1)
        self.aw.qmc.roasted_defects_weight = min(self.aw.qmc.roasted_defects_weight,w0)
        self.aw.qmc.weight = (w0,w1,w2)


        #update volume
        #  first try to recompute volume in and out from weight/density if possible
        self.density_in_editing_finished()
        self.density_out_editing_finished()
        v0 = self.aw.qmc.volume[0]
        v1 = self.aw.qmc.volume[1]
        v2 = self.aw.qmc.volume[2]
        try:
            v0 = float(comma2dot(self.volumeinedit.text()))
        except Exception: # pylint: disable=broad-except
            v0 = 0
        try:
            v1 = float(comma2dot(self.volumeoutedit.text()))
        except Exception: # pylint: disable=broad-except
            v1 = 0
        v2 = self.volumeUnitsComboBox.currentText()
        self.aw.qmc.volume = (v0,v1,v2)
        #update density
        d0 = self.aw.qmc.density[0]
        try:
            d0 = float(comma2dot(self.bean_density_in_edit.text()))
        except Exception: # pylint: disable=broad-except
            d0 = 0
        self.aw.qmc.density = (d0, 'g', 1, 'l')
        dr0 = self.aw.qmc.density_roasted[0]
        try:
            dr0 = float(comma2dot(self.bean_density_out_edit.text()))
        except Exception: # pylint: disable=broad-except
            dr0 = 0
        self.aw.qmc.density_roasted = (dr0, 'g', 1, 'l')
        #update bean size
        try:
            self.aw.qmc.beansize_min = max(0, min(30, int(self.bean_size_min_edit.text())))
        except Exception: # pylint: disable=broad-except
            self.aw.qmc.beansize_min = 0
        try:
            self.aw.qmc.beansize_max = max(0, min(30, int(self.bean_size_max_edit.text())))
        except Exception: # pylint: disable=broad-except
            self.aw.qmc.beansize_max = 0
        if self.aw.qmc.beansize_min > self.aw.qmc.beansize_max:
            # swap order if needed
            self.aw.qmc.beansize_min, self.aw.qmc.beansize_max = self.aw.qmc.beansize_max, self.aw.qmc.beansize_min
        #update roastflags
        self.aw.qmc.heavyFC_flag = self.heavyFC.isChecked()
        self.aw.qmc.lowFC_flag = self.lowFC.isChecked()
        self.aw.qmc.lightCut_flag = self.lightCut.isChecked()
        self.aw.qmc.darkCut_flag = self.darkCut.isChecked()
        self.aw.qmc.drops_flag = self.drops.isChecked()
        self.aw.qmc.oily_flag = self.oily.isChecked()
        self.aw.qmc.uneven_flag = self.uneven.isChecked()
        self.aw.qmc.tipping_flag = self.tipping.isChecked()
        self.aw.qmc.scorching_flag = self.scorching.isChecked()
        self.aw.qmc.divots_flag = self.divots.isChecked()
        #update color
        try:
            self.aw.qmc.whole_color = int(round(float(str(self.whole_color_edit.text()))))
        except Exception: # pylint: disable=broad-except
            self.aw.qmc.whole_color = 0
        try:
            self.aw.qmc.ground_color = int(round(float(str(self.ground_color_edit.text()))))
        except Exception: # pylint: disable=broad-except
            self.aw.qmc.ground_color = 0
        self.aw.qmc.color_system_idx = self.colorSystemComboBox.currentIndex()
        #update beans temperature
        try:
            self.aw.qmc.greens_temp = float(comma2dot(str(self.greens_temp_edit.text())))
        except Exception: # pylint: disable=broad-except
            self.aw.qmc.greens_temp = 0.
        #update greens moisture
        try:
            self.aw.qmc.moisture_greens = float(comma2dot(str(self.moisture_greens_edit.text())))
        except Exception: # pylint: disable=broad-except
            self.aw.qmc.moisture_greens = 0.
        #update roasted moisture
        try:
            self.aw.qmc.moisture_roasted = float(comma2dot(str(self.moisture_roasted_edit.text())))
        except Exception: # pylint: disable=broad-except
            self.aw.qmc.moisture_roasted = 0.
        #update ambient temperature
        try:
            self.aw.qmc.ambientTemp = float(comma2dot(self.ambientedit.text()))
            if math.isnan(self.aw.qmc.ambientTemp):
                self.aw.qmc.ambientTemp = 0.0
        except Exception: # pylint: disable=broad-except
            self.aw.qmc.ambientTemp = 0.0
        #update ambient humidity
        try:
            self.aw.qmc.ambient_humidity = float(comma2dot(str(self.ambient_humidity_edit.text())))
        except Exception: # pylint: disable=broad-except
            self.aw.qmc.ambient_humidity = 0
        #update ambient pressure
        try:
            self.aw.qmc.ambient_pressure = float(comma2dot(str(self.pressureedit.text())))
        except Exception: # pylint: disable=broad-except
            self.aw.qmc.ambient_pressure = 0
        if self.tabInitialized[5] and self.setup_ui is not None:
            #update setup
            self.aw.qmc.organization = self.setup_ui.lineEditOrganization.text()
            self.aw.qmc.operator = self.setup_ui.lineEditOperator.text()
            self.aw.qmc.roastertype = self.setup_ui.lineEditMachine.text()
            self.aw.qmc.roastersize = self.setup_ui.doubleSpinBoxRoasterSize.value()
            self.aw.qmc.roasterheating = self.setup_ui.comboBoxHeating.currentIndex()
            self.aw.qmc.drumspeed = self.setup_ui.lineEditDrumSpeed.text()
        #update notes
        self.aw.qmc.roastingnotes = self.roastingeditor.toPlainText()
        self.aw.qmc.cuppingnotes = self.cuppingeditor.toPlainText()
        if self.aw.superusermode or self.batcheditmode:
            self.aw.qmc.roastbatchprefix = self.batchprefixedit.text()
            self.aw.qmc.roastbatchnr = self.batchcounterSpinBox.value()
            self.aw.qmc.roastbatchpos = self.batchposSpinBox.value()

        self.aw.qmc.perKgRoastMode = self.perKgRoastMode

        # if custom events were changed we clear the event flag position cache
        if self.aw.qmc.specialevents != self.org_specialevents:
            self.aw.qmc.l_event_flags_dict = {}
        # if events were changed we clear the event flag position cache
        if self.aw.qmc.timeindex != self.org_timeindex:
            self.aw.qmc.l_annotations_dict = {}

        if self.tabInitialized[4]:
            # save column widths
            self.aw.qmc.energytablecolumnwidths = [self.energy_ui.datatable.columnWidth(c) for c in range(self.energy_ui.datatable.columnCount())]

        self.aw.qmc.clear_last_picked_event_selection()
        self.aw.eNumberSpinBox.setValue(0)

        # load selected recent roast template in the background
        if self.aw.loadbackgroundUUID(self.template_file,self.template_uuid):
            try:
                self.aw.qmc.background = not self.aw.qmc.hideBgafterprofileload
                self.aw.qmc.timealign(redraw=False)
                self.aw.qmc.redraw_keep_view()
            except Exception: # pylint: disable=broad-except
                pass
        elif ((not self.aw.qmc.flagon) or
            (self.aw.qmc.specialevents != self.org_specialevents) or
            (self.aw.qmc.specialeventstype != self.org_specialeventstype) or
            (self.aw.qmc.specialeventsStrings != self.org_specialeventsStrings) or
            (self.aw.qmc.specialeventsvalue != self.org_specialeventsvalue) or
            (self.aw.qmc.timeindex != self.org_timeindex)):
            # we do a general redraw only if not sampling
            self.aw.qmc.redraw_keep_view(recomputeAllDeltas=False)
        elif (self.org_title != self.aw.qmc.title) or self.org_title_show_always != self.aw.qmc.title_show_always:
            # if title changed we at least update that one
            if self.aw.qmc.flagstart and not self.aw.qmc.title_show_always:
                self.aw.qmc.setProfileTitle('')
                self.aw.qmc.setProfileBackgroundTitle('')
                self.aw.qmc.fig.canvas.draw()
            else:
                self.aw.qmc.setProfileTitle(self.aw.qmc.title)
#                titleB = ''
                if self.aw.qmc.background and not (self.aw.qmc.title is None or self.aw.qmc.title == ''):
                    if self.aw.qmc.roastbatchnrB == 0:
                        titleB = self.aw.qmc.titleB
                    else:
                        titleB = self.aw.qmc.roastbatchprefixB + str(self.aw.qmc.roastbatchnrB) + ' ' + self.aw.qmc.titleB
                    self.aw.qmc.setProfileBackgroundTitle(titleB)
#                self.aw.qmc.updateBackground()
                self.aw.qmc.fig.canvas.draw()

        if not self.aw.qmc.flagon:
            self.aw.sendmessage(QApplication.translate('Message','Roast properties updated but profile not saved to disk'))
        # if recording, dirty and CHARGE and DROP set we send changes to artisan.plus if it is running and we are not in simmulator mode
        if (self.aw.qmc.flagstart and self.aw.qmc.safesaveflag and self.aw.qmc.timeindex[0] > -1 and self.aw.qmc.timeindex[6] > 0 and
                self.aw.plus_account is not None and not bool(self.aw.simulator)):
            try:
                plus.queue.addRoast()
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
        self.clean_up()
        super().accept()

    def getMeasuredvalues(self, title:str, func_updatefields:Callable[[],None],
            fields:List[QLineEdit], loadEnergy:List[float], func_updateduration:Callable[[],None],
            durationfield:QLineEdit, duration:float) -> None:
        loadLabels = ['']*4
        loadUnits = ['']*4
        loadValues = ['0']*4
        for i in range(4):
            loadLabels[i] = self.formatLoadLabel(chr(ord('A')+i),self.aw.qmc.loadlabels[i])
            if self.aw.qmc.load_etypes[i] > 0 and loadEnergy[i] >- 1:
                loadValues[i] = scaleFloat2String(loadEnergy[i])
                loadUnits[i] = self.aw.qmc.energyunits[self.aw.qmc.ratingunits[i]]
            else:
                loadValues[i] = '-'
                loadUnits[i] = '-'
        protocolDuration = self.validateSeconds2Text(duration)
        if protocolDuration == '':
            protocolDuration = '- : -'
        if self.openEnergyMeasuringDialog(title,loadLabels,loadValues,loadUnits,protocolDuration):
            # set values
            for i, field in enumerate(fields):
                if self.aw.qmc.load_etypes[i] > 0 and loadEnergy[i] > -1:
                    field.setText(self.validatePctText(str(loadEnergy[i])))
                    func_updatefields()
            durationfield.setText(protocolDuration)
            func_updateduration()

    @pyqtSlot()
    def toggleEnergyCO2Result(self) -> None:
        self.perKgRoastMode = not self.perKgRoastMode
        self.updateMetricsLabel()

    @pyqtSlot(bool)
    def preHeatToolButton_triggered(self, _:bool = False) -> None:
        title = QApplication.translate('Label','Pre-Heating')
        loadEnergy,_coolEnergy,duration,_coolDuration = self.aw.qmc.measureFromprofile()
        fields = [self.energy_ui.preheatenergies0,
                self.energy_ui.preheatenergies1,
                self.energy_ui.preheatenergies2,
                self.energy_ui.preheatenergies3]
        self.getMeasuredvalues(title, self.updatePreheatEnergies, fields, loadEnergy, self.updatePreheatDuration, self.energy_ui.preheatDuration, duration)

    @pyqtSlot(bool)
    def betweenBatchesToolButton_triggered(self, _:bool = False) -> None:
        title = QApplication.translate('Label','Between Batches')
        loadEnergy,_coolEnergy,duration,_coolDuration = self.aw.qmc.measureFromprofile()
        fields = [self.energy_ui.betweenbatchesenergy0,
                self.energy_ui.betweenbatchesenergy1,
                self.energy_ui.betweenbatchesenergy2,
                self.energy_ui.betweenbatchesenergy3]
        self.getMeasuredvalues(title, self.updateBetweenBatchesEnergies, fields, loadEnergy, self.updateBetweenBatchesDuration, self.energy_ui.betweenBatchesDuration, duration)

    @pyqtSlot(bool)
    def coolingToolButton_triggered(self, _:bool = False) -> None:
        title = QApplication.translate('Label','Cooling')
        _heatEnergy,loadEnergy,_heatDuration,duration = self.aw.qmc.measureFromprofile()
        fields = [self.energy_ui.coolingenergies0,
                self.energy_ui.coolingenergies1,
                self.energy_ui.coolingenergies2,
                self.energy_ui.coolingenergies3]
        self.getMeasuredvalues(title, self.updateCoolingEnergies, fields, loadEnergy, self.updateCoolingDuration, self.energy_ui.coolingDuration, duration)

    def openEnergyMeasuringDialog(self, title:str, loadLabels:List[str], loadValues:List[str], loadUnits:List[str], protocolDuration:str) -> int:
        dialog = EnergyMeasuringDialog(self, self.aw)
        layout: Optional[QLayout]  = dialog.layout()
        # set data
        dialog.ui.groupBox.setTitle(title)
        dialog.ui.loadAlabel.setText(loadLabels[0])
        dialog.ui.loadBlabel.setText(loadLabels[1])
        dialog.ui.loadClabel.setText(loadLabels[2])
        dialog.ui.loadDlabel.setText(loadLabels[3])
        dialog.ui.loadA.setText(loadValues[0])
        dialog.ui.loadB.setText(loadValues[1])
        dialog.ui.loadC.setText(loadValues[2])
        dialog.ui.loadD.setText(loadValues[3])
        dialog.ui.loadAunit.setText(loadUnits[0])
        dialog.ui.loadBunit.setText(loadUnits[1])
        dialog.ui.loadCunit.setText(loadUnits[2])
        dialog.ui.loadDunit.setText(loadUnits[3])
        dialog.ui.duration.setText(protocolDuration)
        # fixed height
        if layout is not None:
            layout.setSpacing(5)
        dialog.setFixedHeight(dialog.sizeHint().height())
#        res = dialog.exec()
#        #deleteLater() will not work here as the dialog is still bound via the parent
#        #dialog.deleteLater() # now we explicitly allow the dialog an its widgets to be GCed
#        # the following will immediately release the memory despite this parent link
#        QApplication.processEvents() # we ensure events concerning this dialog are processed before deletion
#        try: # sip not supported on older PyQt versions (RPi!)
#            sip.delete(dialog)
#            #print(sip.isdeleted(dialog))
#        except Exception: # pylint: disable=broad-except
#            pass
#        return res
        return dialog.exec()

class StockComboBox(MyQComboBox):
    def __init__(self, unitsComboBox:QComboBox, *args:Any, **kwargs:Any) -> None:
        super().__init__(*args, **kwargs)
        self.inverted:bool = False # is True if the weight units were inverted before
        self.unitsComboBox:QComboBox = unitsComboBox

    # to be overwritten by subclasses
    def getItems(self, _unit:int) -> List[str]: # pylint: disable=no-self-use
        return []

    def resetInverted(self) -> None:
        self.inverted = False

    def mousePressEvent(self, event:'Optional[QMouseEvent]') -> None:
        if self.unitsComboBox is not None and QApplication.keyboardModifiers() == Qt.KeyboardModifier.AltModifier or self.inverted:
            # with ALT (Win) / OPTION (macOS) pressed we rewrite the popup menu indicating weights in imperial units if metric units were selected and vice versa
            default_unit:int = self.unitsComboBox.currentIndex()
            unit:int = 0 # g
            if self.inverted:
                # we revert to the original units
                unit = default_unit
            elif default_unit < 2:
                # if default unit is g or kg we convert to oz, otherwise to g
                unit = 3
            items = self.getItems(unit)
            for i in range(self.count()):
                if len(items) > i:
                    self.setItemText(i, items[i])
            self.inverted = not self.inverted
        super().mousePressEvent(event)

class CoffeesComboBox(StockComboBox):
    def __init__(self, parent:editGraphDlg, *args:Any, **kwargs:Any) -> None:
        super().__init__(parent.unitsComboBox, *args, **kwargs)
        self.parentDialog = parent

    def getItems(self, unit:int) -> List[str]:
        plus_coffees = plus.stock.getCoffees(unit, self.parentDialog.plus_default_store)
        return [''] + plus.stock.getCoffeesLabels(plus_coffees)

class BlendsComboBox(StockComboBox):
    def __init__(self, parent:editGraphDlg, *args:Any, **kwargs:Any) -> None:
        super().__init__(parent.unitsComboBox, *args, **kwargs)
        self.parentDialog:editGraphDlg = parent

    def getItems(self, unit:int) -> List[str]:
        custom_blend:Optional[plus.stock.Blend] = None
        if self.parentDialog.aw.qmc.plus_custom_blend is not None and self.parentDialog.aw.qmc.plus_custom_blend.name.strip() != '':
            coffees = plus.stock.getCoffeeLabels()
            if len(coffees)>2 and self.parentDialog.aw.qmc.plus_custom_blend.isValid(coffees.values()):
                custom_blend = {
                    'hr_id': '',
                    'label': self.parentDialog.aw.qmc.plus_custom_blend.name.strip(),
                    'ingredients': [{'ratio': c.ratio, 'coffee': c.coffee} for c in self.parentDialog.aw.qmc.plus_custom_blend.components]}
        plus_blends = plus.stock.getBlends(unit,self.parentDialog.plus_default_store, custom_blend)
        blend_items:List[str] = plus.stock.getBlendLabels(plus_blends)
        return [''] + blend_items



########################################################################################
#####################  ENERGY Measuring Dialog  ########################################

class EnergyMeasuringDialog(ArtisanDialog):
    def __init__(self, parent:QWidget, aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.ui = MeasureDialog.Ui_setMeasureDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(QApplication.translate('Form Caption','Set Measure from Profile'))
        self.ui.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Apply)
        # hack to assign the Apply button the AcceptRole without losing default system translations
        applyButton = self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Apply)
        if applyButton is not None:
            self.ui.buttonBox.removeButton(applyButton)
            self.ui.buttonBox.addButton(applyButton.text(), QDialogButtonBox.ButtonRole.AcceptRole)
