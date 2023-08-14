#
# ABOUT
# Artisan Colors dialog

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

from artisanlib.util import deltaLabelUTF8
from artisanlib.dialogs import ArtisanDialog
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import

try:
    from PyQt6.QtCore import Qt, QTimer, pyqtSlot # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QColor, QFont, QPalette # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,  # @UnusedImport @Reimport  @UnresolvedImport
        QSizePolicy, QHBoxLayout, QVBoxLayout, QDialogButtonBox, QGridLayout, QGroupBox, # @UnusedImport @Reimport  @UnresolvedImport
        QLayout, QSpinBox, QTabWidget, QMessageBox) # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import Qt, QTimer, pyqtSlot # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QColor, QFont, QPalette # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QSizePolicy, QHBoxLayout, QVBoxLayout, QDialogButtonBox, QGridLayout, QGroupBox, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QLayout, QSpinBox, QTabWidget, QMessageBox) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


class graphColorDlg(ArtisanDialog):
    def __init__(self, parent:QWidget, aw:'ApplicationWindow', activeTab:int = 0) -> None:
        super().__init__(parent, aw)
        self.activeTab = activeTab
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False) # overwrite the ArtisanDialog class default here!!
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Colors'))
        titlefont = QFont()
        titlefont.setBold(True)
#        titlefont.setWeight(75)
        self.commonstyle = 'border-style: solid; border-width: 1px; border-radius: 4px; border-color: black; padding: 4px;'

        #TAB0
        profilecolorlabel = QLabel(QApplication.translate('Label','Profile Colors'))
        profilecolorlabel.setFont(titlefont)
        bgcolorlabel = QLabel(QApplication.translate('Label','Background Profile Colors'))
        bgcolorlabel.setFont(titlefont)
        profilecolorlabel.setMaximumSize(180,20)
        bgcolorlabel.setMaximumSize(180,20)
        profilecolorlabel.setMinimumSize(150,20)
        bgcolorlabel.setMinimumSize(150,20)

        self.metLabel = QLabel(QApplication.translate('Button','ET'))
        self.metLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.metButton = QPushButton()
        self.metButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.metButton.clicked.connect(self.setColorSlot)
        self.btLabel = QLabel(QApplication.translate('Button','BT'))
        self.btLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.btButton = QPushButton()
        self.btButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btButton.clicked.connect(self.setColorSlot)
        self.deltametLabel = QLabel(deltaLabelUTF8 + QApplication.translate('Button','ET'))
        self.deltametLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.deltametButton = QPushButton()
        self.deltametButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.deltametButton.clicked.connect(self.setColorSlot)
        self.deltabtLabel = QLabel(deltaLabelUTF8 + QApplication.translate('Button','BT'))
        self.deltabtLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.deltabtButton = QPushButton()
        self.deltabtButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.deltabtButton.clicked.connect(self.setColorSlot)

        self.bgmetLabel = QLabel(QApplication.translate('Button','ET'))
        self.bgmetLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.bgmetButton = QPushButton()
        self.bgmetButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.bgmetButton.clicked.connect(self.setbgColorSlot)
        self.bgbtLabel = QLabel(QApplication.translate('Button','BT'))
        self.bgbtLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.bgbtButton = QPushButton()
        self.bgbtButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.bgbtButton.clicked.connect(self.setbgColorSlot)
        self.bgdeltametLabel = QLabel(deltaLabelUTF8 + QApplication.translate('Button','ET'))
        self.bgdeltametLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.bgdeltametButton = QPushButton()
        self.bgdeltametButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.bgdeltametButton.clicked.connect(self.setbgColorSlot)
        self.bgdeltabtLabel = QLabel(deltaLabelUTF8 + QApplication.translate('Button','BT'))
        self.bgdeltabtLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.bgdeltabtButton = QPushButton()
        self.bgdeltabtButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.bgdeltabtButton.clicked.connect(self.setbgColorSlot)

        self.bgextraLabel = QLabel(QApplication.translate('Button','Extra 1'))
        self.bgextraLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.bgextra2Label = QLabel(QApplication.translate('Button','Extra 2'))
        self.bgextra2Label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.bgextraButton = QPushButton()
        self.bgextraButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.bgextraButton.clicked.connect(self.setbgColorSlot)
        self.bgextra2Button = QPushButton()
        self.bgextra2Button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.bgextra2Button.clicked.connect(self.setbgColorSlot)

        opaqbgLabel = QLabel(QApplication.translate('Label', 'Opaqueness'))
        opaqbgLabel.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.opaqbgSpinBox = QSpinBox()
        self.opaqbgSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.opaqbgSpinBox.setRange(1,10)
        self.opaqbgSpinBox.setSingleStep(1)
        self.opaqbgSpinBox.setValue(int(round(self.aw.qmc.backgroundalpha * 10)))
        self.opaqbgSpinBox.valueChanged.connect(self.adjustintensity)
        self.opaqbgSpinBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.opaqbgLayout = QHBoxLayout()
        self.opaqbgLayout.addWidget(opaqbgLabel)
        self.opaqbgLayout.addWidget(self.opaqbgSpinBox)

        #TAB1
        self.backgroundLabel = QLabel(QApplication.translate('Button','Background'))
        self.backgroundLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.backgroundButton = QPushButton()
        self.backgroundButton = self.colorButton(self.aw.qmc.palette['background'])
        self.backgroundButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.backgroundButton.clicked.connect(self.setColorSlot)
        self.gridLabel = QLabel(QApplication.translate('Button','Grid'))
        self.gridLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.gridButton = QPushButton()
        self.gridButton = self.colorButton(self.aw.qmc.palette['grid'])
        self.gridButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.gridButton.clicked.connect(self.setColorSlot)
        self.titleLabel = QLabel(QApplication.translate('Button','Title'))
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.titleButton = QPushButton()
        self.titleButton = self.colorButton(self.aw.qmc.palette['title'])
        self.titleButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.titleButton.clicked.connect(self.setColorSlot)
        self.yLabel = QLabel(QApplication.translate('Button','Y Label'))
        self.yLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.yButton = QPushButton()
        self.yButton = self.colorButton(self.aw.qmc.palette['ylabel'])
        self.yButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.yButton.clicked.connect(self.setColorSlot)
        self.xLabel = QLabel(QApplication.translate('Button','X Label'))
        self.xLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.xButton = self.colorButton(self.aw.qmc.palette['xlabel'])
        self.xButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.xButton.clicked.connect(self.setColorSlot)
        self.rect1Label = QLabel(QApplication.translate('Button','Drying Phase'))
        self.rect1Label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.rect1Button = QPushButton()
        self.rect1Button = self.colorButton(self.aw.qmc.palette['rect1'])
        self.rect1Button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.rect1Button.clicked.connect(self.setColorSlot)
        self.rect2Label = QLabel(QApplication.translate('Button','Maillard Phase'))
        self.rect2Label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.rect2Button = QPushButton()
        self.rect2Button = self.colorButton(self.aw.qmc.palette['rect2'])
        self.rect2Button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.rect2Button.clicked.connect(self.setColorSlot)
        self.rect3Label = QLabel(QApplication.translate('Button','Finishing Phase'))
        self.rect3Label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.rect3Button = QPushButton()
        self.rect3Button = self.colorButton(self.aw.qmc.palette['rect3'])
        self.rect3Button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.rect3Button.clicked.connect(self.setColorSlot)
        self.rect4Label = QLabel(QApplication.translate('Button','Cooling Phase'))
        self.rect4Label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.rect4Button = QPushButton()
        self.rect4Button = self.colorButton(self.aw.qmc.palette['rect4'])
        self.rect4Button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.rect4Button.clicked.connect(self.setColorSlot)
        self.rect5Label = QLabel(QApplication.translate('Button','Bars Bkgnd'))
        self.rect5Label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.rect5Button = QPushButton()
        self.rect5Button = self.colorButton(self.aw.qmc.palette['rect5'])
        self.rect5Button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.rect5Button.clicked.connect(self.setColorSlot)
        self.markersLabel = QLabel(QApplication.translate('Button','Markers'))
        self.markersLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.markersButton = QPushButton()
        self.markersButton = self.colorButton(self.aw.qmc.palette['markers'])
        self.markersButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.markersButton.clicked.connect(self.setColorSlot)
        self.textLabel = QLabel(QApplication.translate('Button','Text'))
        self.textLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.textButton = QPushButton()
        self.textButton = self.colorButton(self.aw.qmc.palette['text'])
        self.textButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.textButton.clicked.connect(self.setColorSlot)
        self.watermarksLabel = QLabel(QApplication.translate('Button','Watermarks'))
        self.watermarksLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.watermarksButton = QPushButton()
        self.watermarksButton = self.colorButton(self.aw.qmc.palette['watermarks'])
        self.watermarksButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.watermarksButton.clicked.connect(self.setColorSlot)
        self.timeguideLabel = QLabel(QApplication.translate('Button','Time Guide'))
        self.timeguideLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.timeguideButton = QPushButton()
        self.timeguideButton = self.colorButton(self.aw.qmc.palette['timeguide'])
        self.timeguideButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.timeguideButton.clicked.connect(self.setColorSlot)
        self.aucguideLabel = QLabel(QApplication.translate('Button','AUC Guide'))
        self.aucguideLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.aucguideButton = QPushButton()
        self.aucguideButton = self.colorButton(self.aw.qmc.palette['aucguide'])
        self.aucguideButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.aucguideButton.clicked.connect(self.setColorSlot)
        self.aucareaLabel = QLabel(QApplication.translate('Button','AUC Area'))
        self.aucareaLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.aucareaButton = QPushButton()
        self.aucareaButton = self.colorButton(self.aw.qmc.palette['aucarea'])
        self.aucareaButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.aucareaButton.clicked.connect(self.setColorSlot)
        self.legendbgLabel = QLabel(QApplication.translate('Button','Legend bkgnd'))
        self.legendbgLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.legendbgButton = QPushButton()
        self.legendbgButton = self.colorButton(self.aw.qmc.palette['legendbg'])
        self.legendbgButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.legendbgButton.clicked.connect(self.setColorSlot)
        self.legendbgSpinBox = QSpinBox()
        self.legendbgSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.legendbgSpinBox.setRange(1,10)
        self.legendbgSpinBox.setSingleStep(1)
        self.legendbgSpinBox.setValue(int(round(self.aw.qmc.alpha['legendbg'] * 10)))
        self.legendbgSpinBox.valueChanged.connect(self.adjustOpaqenesssSlot)
        self.legendbgSpinBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.legendbgButton.setSizePolicy(QSizePolicy.Policy.Expanding,self.legendbgButton.sizePolicy().verticalPolicy())
        self.legendbgLayout = QHBoxLayout()
        self.legendbgLayout.addWidget(self.legendbgButton)
        self.legendbgLayout.addWidget(self.legendbgSpinBox)
        self.legendborderLabel = QLabel(QApplication.translate('Button','Legend border'))
        self.legendborderLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.legendborderButton = QPushButton()
        self.legendborderButton = self.colorButton(self.aw.qmc.palette['legendborder'])
        self.legendborderButton.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.legendborderButton.clicked.connect(self.setColorSlot)

        self.canvasLabel = QLabel(QApplication.translate('Button','Canvas'))
        self.canvasLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.canvasButton = QPushButton()
        self.canvasButton = self.colorButton(self.aw.qmc.palette['canvas'])
        if str(self.aw.qmc.palette['canvas']) == 'None':
            self.canvasButton.setPalette(QPalette(QColor('#f0f0f0')))
        else:
            self.canvasButton.setPalette(QPalette(QColor(self.aw.qmc.palette['canvas'])))
        self.canvasButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.canvasButton.clicked.connect(self.setColorSlot)

        self.specialeventboxLabel = QLabel(QApplication.translate('Button','SpecialEvent Marker'))
        self.specialeventboxLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.specialeventboxButton = QPushButton()
        self.specialeventboxButton = self.colorButton(self.aw.qmc.palette['specialeventbox'])
        self.specialeventboxButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.specialeventboxButton.clicked.connect(self.setColorSlot)
        self.specialeventtextLabel = QLabel(QApplication.translate('Button','SpecialEvent Text'))
        self.specialeventtextLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.specialeventtextButton = QPushButton()
        self.specialeventtextButton = self.colorButton(self.aw.qmc.palette['specialeventtext'])
        self.specialeventtextButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.specialeventtextButton.clicked.connect(self.setColorSlot)
        self.bgeventmarkerLabel = QLabel(QApplication.translate('Button','Bkgd Event Marker'))
        self.bgeventmarkerLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.bgeventmarkerButton = QPushButton()
        self.bgeventmarkerButton = self.colorButton(self.aw.qmc.palette['bgeventmarker'])
        self.bgeventmarkerButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.bgeventmarkerButton.clicked.connect(self.setColorSlot)
        self.bgeventtextLabel = QLabel(QApplication.translate('Button','Bkgd Event Text'))
        self.bgeventtextLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.bgeventtextButton = QPushButton()
        self.bgeventtextButton = self.colorButton(self.aw.qmc.palette['bgeventtext'])
        self.bgeventtextButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.bgeventtextButton.clicked.connect(self.setColorSlot)
        self.mettextLabel = QLabel(QApplication.translate('Button','MET Text'))
        self.mettextLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.mettextButton = QPushButton()
        self.mettextButton = self.colorButton(self.aw.qmc.palette['mettext'])
        self.mettextButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.mettextButton.clicked.connect(self.setColorSlot)
        self.metboxLabel = QLabel(QApplication.translate('Button','MET Box'))
        self.metboxLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.metboxButton = QPushButton()
        self.metboxButton = self.colorButton(self.aw.qmc.palette['metbox'])
        self.metboxButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.metboxButton.clicked.connect(self.setColorSlot)
        self.analysismaskLabel = QLabel(QApplication.translate('Button','Analysis Mask'))
        self.analysismaskLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.analysismaskButton = QPushButton()
        self.analysismaskButton = self.colorButton(self.aw.qmc.palette['analysismask'])
        self.analysismaskButton.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.analysismaskButton.clicked.connect(self.setColorSlot)
        self.analysismaskSpinBox = QSpinBox()
        self.analysismaskSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.analysismaskSpinBox.setRange(1,10)
        self.analysismaskSpinBox.setSingleStep(1)
        self.analysismaskSpinBox.setValue(int(round(self.aw.qmc.alpha['analysismask'] * 10)))
        self.analysismaskSpinBox.valueChanged.connect(self.adjustOpaqenesssSlot)
        self.analysismaskLayout = QHBoxLayout()
        self.analysismaskButton.setSizePolicy(QSizePolicy.Policy.Expanding,self.analysismaskButton.sizePolicy().verticalPolicy())
        self.analysismaskLayout.addWidget(self.analysismaskButton)
        self.analysismaskLayout.addWidget(self.analysismaskSpinBox)
        self.statsanalysisbkgndLabel = QLabel(QApplication.translate('Button','Stats&Analysis Bkgnd'))
        self.statsanalysisbkgndLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.statsanalysisbkgndButton = QPushButton()
        self.statsanalysisbkgndButton = self.colorButton(self.aw.qmc.palette['statsanalysisbkgnd'])
        self.statsanalysisbkgndButton.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.statsanalysisbkgndButton.clicked.connect(self.setColorSlot)
        self.statsanalysisbkgndSpinBox = QSpinBox()
        self.statsanalysisbkgndSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.statsanalysisbkgndSpinBox.setRange(1,10)
        self.statsanalysisbkgndSpinBox.setSingleStep(1)
        self.statsanalysisbkgndSpinBox.setValue(int(round(self.aw.qmc.alpha['statsanalysisbkgnd'] * 10)))
        self.statsanalysisbkgndSpinBox.valueChanged.connect(self.adjustOpaqenesssSlot)
        self.statsanalysisbkgndSpinBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.statsanalysisbkgndLayout = QHBoxLayout()
        self.statsanalysisbkgndButton.setSizePolicy(QSizePolicy.Policy.Expanding,self.statsanalysisbkgndButton.sizePolicy().verticalPolicy())
        self.statsanalysisbkgndLayout.addWidget(self.statsanalysisbkgndButton)
        self.statsanalysisbkgndLayout.addWidget(self.statsanalysisbkgndSpinBox)

        #TAB2
        self.lcd1LEDButton = QPushButton(QApplication.translate('Button','Digits'))
        self.lcd1LEDButton.clicked.connect(self.paintlcdsSlot)
        self.lcd2LEDButton = QPushButton(QApplication.translate('Button','Digits'))
        self.lcd2LEDButton.clicked.connect(self.paintlcdsSlot)
        self.lcd3LEDButton = QPushButton(QApplication.translate('Button','Digits'))
        self.lcd3LEDButton.clicked.connect(self.paintlcdsSlot)
        self.lcd4LEDButton = QPushButton(QApplication.translate('Button','Digits'))
        self.lcd4LEDButton.clicked.connect(self.paintlcdsSlot)
        self.lcd5LEDButton = QPushButton(QApplication.translate('Button','Digits'))
        self.lcd5LEDButton.clicked.connect(self.paintlcdsSlot)
        self.lcd6LEDButton = QPushButton(QApplication.translate('Button','Digits'))
        self.lcd6LEDButton.clicked.connect(self.paintlcdsSlot)
        self.lcd7LEDButton = QPushButton(QApplication.translate('Button','Digits'))
        self.lcd7LEDButton.clicked.connect(self.paintlcdsSlot)
        self.lcd8LEDButton = QPushButton(QApplication.translate('Button','Digits'))
        self.lcd8LEDButton.clicked.connect(self.paintlcdsSlot)

        self.lcd1backButton = QPushButton(QApplication.translate('Button','Background'))
        self.lcd1backButton.clicked.connect(self.paintlcdsSlot)
        self.lcd2backButton = QPushButton(QApplication.translate('Button','Background'))
        self.lcd2backButton.clicked.connect(self.paintlcdsSlot)
        self.lcd3backButton = QPushButton(QApplication.translate('Button','Background'))
        self.lcd3backButton.clicked.connect(self.paintlcdsSlot)
        self.lcd4backButton = QPushButton(QApplication.translate('Button','Background'))
        self.lcd4backButton.clicked.connect(self.paintlcdsSlot)
        self.lcd5backButton = QPushButton(QApplication.translate('Button','Background'))
        self.lcd5backButton.clicked.connect(self.paintlcdsSlot)
        self.lcd6backButton = QPushButton(QApplication.translate('Button','Background'))
        self.lcd6backButton.clicked.connect(self.paintlcdsSlot)
        self.lcd7backButton = QPushButton(QApplication.translate('Button','Background'))
        self.lcd7backButton.clicked.connect(self.paintlcdsSlot)
        self.lcd8backButton = QPushButton(QApplication.translate('Button','Background'))
        self.lcd8backButton.clicked.connect(self.paintlcdsSlot)
        self.lcd1LEDButton.setMinimumWidth(80)
        self.lcd2LEDButton.setMinimumWidth(80)
        self.lcd3LEDButton.setMinimumWidth(80)
        self.lcd4LEDButton.setMinimumWidth(80)
        self.lcd5LEDButton.setMinimumWidth(80)
        self.lcd6LEDButton.setMinimumWidth(80)
        self.lcd7LEDButton.setMinimumWidth(80)
        self.lcd8LEDButton.setMinimumWidth(80)

        LCDdefaultButton = QPushButton(QApplication.translate('Button','B/W'))
        LCDdefaultButton.clicked.connect(self.setLCD_bw)

        #LAYOUTS
        #tab0 layout
        lines = QGridLayout()
        lines.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lines.setVerticalSpacing(1)
        lines.setColumnMinimumWidth(0,0)   #0,80
#        lines.setColumnMaximumWidth(0,30)
        lines.setColumnMinimumWidth(1,150)   #1,180
        lines.setColumnMinimumWidth(2,50)   #2,80
        lines.setColumnMinimumWidth(3,150)   #3,180

        lines.addWidget(profilecolorlabel,0,1)
        lines.addWidget(self.metButton,1,1)
        lines.addWidget(self.metLabel,1,0)
        lines.addWidget(self.btButton,2,1)
        lines.addWidget(self.btLabel,2,0)
        lines.addWidget(self.deltametButton,3,1)
        lines.addWidget(self.deltametLabel,3,0)
        lines.addWidget(self.deltabtButton,4,1)
        lines.addWidget(self.deltabtLabel,4,0)

        lines.addWidget(bgcolorlabel,0,3)
        lines.addWidget(self.bgmetButton,1,3)
        lines.addWidget(self.bgmetLabel,1,2)
        lines.addWidget(self.bgbtButton,2,3)
        lines.addWidget(self.bgbtLabel,2,2)
        lines.addWidget(self.bgdeltametButton,3,3)
        lines.addWidget(self.bgdeltametLabel,3,2)
        lines.addWidget(self.bgdeltabtButton,4,3)
        lines.addWidget(self.bgdeltabtLabel,4,2)
        lines.addWidget(self.bgextraButton,5,3)
        lines.addWidget(self.bgextraLabel,5,2)
        lines.addWidget(self.bgextra2Button,6,3)
        lines.addWidget(self.bgextra2Label,6,2)
        lines.addLayout(self.opaqbgLayout,7,3)

        graphlinesLayout = QVBoxLayout()
        graphlinesLayout.addLayout(lines)

        #tab1 layout
        grid = QGridLayout()
        grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
#        grid.setColumnStretch(1,12)
#        grid.setColumnStretch(3,12)
        grid.setVerticalSpacing(1)
        grid.setColumnMinimumWidth(0,80)
        grid.setColumnMinimumWidth(2,80)
        grid.setColumnMinimumWidth(1,110)  #1,80
        grid.setColumnMinimumWidth(3,110)  #3,80
        grid.addWidget(self.canvasButton,0,1)
        grid.addWidget(self.canvasLabel,0,0)
        grid.addWidget(self.backgroundButton,1,1)
        grid.addWidget(self.backgroundLabel,1,0)
        grid.addWidget(self.titleButton,2,1)
        grid.addWidget(self.titleLabel,2,0)
        grid.addWidget(self.gridButton,3,1)
        grid.addWidget(self.gridLabel,3,0)
        grid.addWidget(self.yButton,4,1)
        grid.addWidget(self.yLabel,4,0)
        grid.addWidget(self.xButton,5,1)
        grid.addWidget(self.xLabel,5,0)
        grid.addWidget(self.markersButton,6,1)
        grid.addWidget(self.markersLabel,6,0)
        grid.addWidget(self.textButton,7,1)
        grid.addWidget(self.textLabel,7,0)
        grid.addLayout(self.legendbgLayout,8,1)
        grid.addWidget(self.legendbgLabel,8,0)
        grid.addWidget(self.legendborderButton,9,1)
        grid.addWidget(self.legendborderLabel,9,0)
        grid.addWidget(self.watermarksButton,10,1)
        grid.addWidget(self.watermarksLabel,10,0)
        grid.addWidget(self.aucguideButton,11,1)
        grid.addWidget(self.aucguideLabel,11,0)
        grid.addWidget(self.aucareaButton,12,1)
        grid.addWidget(self.aucareaLabel,12,0)
        grid.addWidget(self.rect1Button,0,3)
        grid.addWidget(self.rect1Label,0,2)
        grid.addWidget(self.rect2Button,1,3)
        grid.addWidget(self.rect2Label,1,2)
        grid.addWidget(self.rect3Button,2,3)
        grid.addWidget(self.rect3Label,2,2)
        grid.addWidget(self.rect4Button,3,3)
        grid.addWidget(self.rect4Label,3,2)
        grid.addWidget(self.rect5Button,4,3)
        grid.addWidget(self.rect5Label,4,2)
        grid.addWidget(self.specialeventboxButton,5,3)
        grid.addWidget(self.specialeventboxLabel,5,2)
        grid.addWidget(self.specialeventtextButton,6,3)
        grid.addWidget(self.specialeventtextLabel,6,2)
        grid.addWidget(self.bgeventmarkerButton,7,3)
        grid.addWidget(self.bgeventmarkerLabel,7,2)
        grid.addWidget(self.bgeventtextButton,8,3)
        grid.addWidget(self.bgeventtextLabel,8,2)
        grid.addWidget(self.metboxButton,9,3)
        grid.addWidget(self.metboxLabel,9,2)
        grid.addWidget(self.mettextButton,10,3)
        grid.addWidget(self.mettextLabel,10,2)
        grid.addWidget(self.timeguideButton,11,3)
        grid.addWidget(self.timeguideLabel,11,2)
        grid.addLayout(self.analysismaskLayout,12,3)
        grid.addWidget(self.analysismaskLabel,12,2)
        grid.addLayout(self.statsanalysisbkgndLayout,13,3)
        grid.addWidget(self.statsanalysisbkgndLabel,13,2)
        graphLayout = QVBoxLayout()
        graphLayout.addLayout(grid)

        #tab 2 layout
        lcd1layout = QHBoxLayout()
        lcd1layout.addWidget(self.lcd1LEDButton,0)
        lcd1layout.addWidget(self.lcd1backButton,1)
        lcd2layout = QHBoxLayout()
        lcd2layout.addWidget(self.lcd2LEDButton,0)
        lcd2layout.addWidget(self.lcd2backButton,1)
        lcd3layout = QHBoxLayout()
        lcd3layout.addWidget(self.lcd3LEDButton,0)
        lcd3layout.addWidget(self.lcd3backButton,1)
        lcd4layout = QHBoxLayout()
        lcd4layout.addWidget(self.lcd4LEDButton,0)
        lcd4layout.addWidget(self.lcd4backButton,1)
        lcd5layout = QHBoxLayout()
        lcd5layout.addWidget(self.lcd5LEDButton,0)
        lcd5layout.addWidget(self.lcd5backButton,1)
        lcd6layout = QHBoxLayout()
        lcd6layout.addWidget(self.lcd6LEDButton,0)
        lcd6layout.addWidget(self.lcd6backButton,1)
        lcd7layout = QHBoxLayout()
        lcd7layout.addWidget(self.lcd7LEDButton,0)
        lcd7layout.addWidget(self.lcd7backButton,1)
        lcd8layout = QHBoxLayout()
        lcd8layout.addWidget(self.lcd8LEDButton,0)
        lcd8layout.addWidget(self.lcd8backButton,1)
        LCD1GroupLayout = QGroupBox(QApplication.translate('GroupBox','Timer LCD'))
        LCD1GroupLayout.setLayout(lcd1layout)
        lcd1layout.setContentsMargins(0,0,0,0)
        LCD2GroupLayout = QGroupBox(QApplication.translate('GroupBox','ET LCD'))
        LCD2GroupLayout.setLayout(lcd2layout)
        lcd2layout.setContentsMargins(0,0,0,0)
        LCD3GroupLayout = QGroupBox(QApplication.translate('GroupBox','BT LCD'))
        LCD3GroupLayout.setLayout(lcd3layout)
        lcd3layout.setContentsMargins(0,0,0,0)
        LCD4GroupLayout = QGroupBox(deltaLabelUTF8 + QApplication.translate('GroupBox','ET LCD'))
        LCD4GroupLayout.setLayout(lcd4layout)
        lcd4layout.setContentsMargins(0,0,0,0)
        LCD5GroupLayout = QGroupBox(deltaLabelUTF8 + QApplication.translate('GroupBox','BT LCD'))
        LCD5GroupLayout.setLayout(lcd5layout)
        lcd5layout.setContentsMargins(0,0,0,0)
        LCD6GroupLayout = QGroupBox(QApplication.translate('GroupBox','Extra Devices / PID SV LCD'))
        LCD6GroupLayout.setLayout(lcd6layout)
        lcd6layout.setContentsMargins(0,0,0,0)
        LCD7GroupLayout = QGroupBox(QApplication.translate('GroupBox','Ramp/Soak Timer LCD'))
        LCD7GroupLayout.setLayout(lcd7layout)
        lcd7layout.setContentsMargins(0,0,0,0)
        LCD8GroupLayout = QGroupBox(QApplication.translate('GroupBox','Slow Cooling Timer LCD'))
        LCD8GroupLayout.setLayout(lcd8layout)
        lcd8layout.setContentsMargins(0,0,0,0)

        buttonlayout = QHBoxLayout()
        buttonlayout.addStretch()
        buttonlayout.addWidget(LCDdefaultButton)
        buttonlayout.setContentsMargins(0,0,0,0)
        buttonlayout.setSpacing(0)

        lcdlayout1 = QVBoxLayout()
        lcdlayout1.addWidget(LCD2GroupLayout)
        lcdlayout1.addWidget(LCD3GroupLayout)
        lcdlayout1.addWidget(LCD1GroupLayout)
        lcdlayout1.addWidget(LCD6GroupLayout)
        lcdlayout2 = QVBoxLayout()
        lcdlayout2.addWidget(LCD4GroupLayout)
        lcdlayout2.addWidget(LCD5GroupLayout)
        lcdlayout2.addWidget(LCD7GroupLayout)
        lcdlayout2.addWidget(LCD8GroupLayout)
        lcdlayout = QHBoxLayout()
        lcdlayout.addLayout(lcdlayout1)
        lcdlayout.addLayout(lcdlayout2)
        lllayout = QVBoxLayout()
        lllayout.addLayout(lcdlayout)
        lllayout.addLayout(buttonlayout)
        lllayout.setContentsMargins(0,0,0,0)
        lllayout.setSpacing(5)

        ###################################
        self.TabWidget = QTabWidget()
        C0Widget = QWidget()
        C0Widget.setLayout(graphlinesLayout)
        self.TabWidget.addTab(C0Widget,QApplication.translate('Tab','Curves'))
        C1Widget = QWidget()
        C1Widget.setLayout(graphLayout)
        self.TabWidget.addTab(C1Widget,QApplication.translate('Tab','Graph'))
        C2Widget = QWidget()
        C2Widget.setLayout(lllayout)
        self.TabWidget.addTab(C2Widget,QApplication.translate('Tab','LCDs'))

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.accept)
        self.dialogbuttons.removeButton(self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel))
        resetButton = self.dialogbuttons.addButton(QDialogButtonBox.StandardButton.RestoreDefaults)
        if resetButton is not None:
            resetButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            resetButton.clicked.connect(self.recolor1)
            self.setButtonTranslations(resetButton,'Restore Defaults',QApplication.translate('Button','Restore Defaults'))

        greyButton = QPushButton(QApplication.translate('Button','Grey'))
        greyButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        greyButton.clicked.connect(self.recolor2)

        self.dialogbuttons.addButton(greyButton, QDialogButtonBox.ButtonRole.ActionRole)

        okLayout = QHBoxLayout()
        okLayout.addStretch()
        okLayout.addWidget(self.dialogbuttons)
        okLayout.setContentsMargins(10, 10, 10, 10)
        self.TabWidget.setContentsMargins(0, 0, 0, 0)
        C0Widget.setContentsMargins(5, 10, 5, 10)
        C1Widget.setContentsMargins(5, 10, 5, 10)
        C2Widget.setContentsMargins(5, 10, 5, 10)
        graphLayout.setContentsMargins(5,0,5,0)
        #incorporate layouts
        Mlayout = QVBoxLayout()
        Mlayout.addWidget(self.TabWidget)
        Mlayout.addLayout(okLayout)
        Mlayout.setContentsMargins(5,10,5,0)
        Mlayout.setSpacing(0)
        self.setLayout(Mlayout)
        self.setColorButtons()
        if platform.system() != 'Windows':
            ok_button = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button is not None:
                ok_button.setFocus()
        layout = self.layout()
        if layout is not None:
            layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize) # don't allow resizing

        # we set the active tab with a QTimer after the tabbar has been rendered once, as otherwise
        # some tabs are not rendered at all on Winwos using Qt v6.5.1 (https://bugreports.qt.io/projects/QTBUG/issues/QTBUG-114204?filter=allissues)
        QTimer.singleShot(10, self.setActiveTab)

    @pyqtSlot()
    def setActiveTab(self) -> None:
        self.TabWidget.setCurrentIndex(self.activeTab)

    @pyqtSlot('QCloseEvent')
    def closeEvent(self,_):
        self.aw.graphColorDlg_activeTab = self.TabWidget.currentIndex()

    @pyqtSlot(bool)
    def setLCD_bw(self,_):
        self.aw.setLCDsBW()
        self.setColorButtons()

#    def setLED(self,hue,lcd):
#        if lcd == 1:
#            color = QColor(self.aw.lcdpaletteF['timer'])
#            color.setHsv(hue,255,255,255)
#            self.aw.lcdpaletteF['timer'] = str(color.name())
#            self.aw.setTimerColor('timer')
#            if self.aw.largeLCDs_dialog:
#                self.aw.largeLCDs_dialog.updateStyles()
#        elif lcd == 2:
#            color = QColor(self.aw.lcdpaletteF['et'])
#            color.setHsv(hue,255,255,255)
#            self.aw.lcdpaletteF['et'] = str(color.name())
#            self.aw.lcd2.setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['et']}; background-color: {self.aw.lcdpaletteB['et']};}}")
#            if self.aw.largeLCDs_dialog:
#                self.aw.largeLCDs_dialog.updateStyles()
#        elif lcd == 3:
#            color = QColor(self.aw.lcdpaletteF['bt'])
#            color.setHsv(hue,255,255,255)
#            self.aw.lcdpaletteF['bt'] = str(color.name())
#            self.aw.lcd3.setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['bt']}; background-color: {self.aw.lcdpaletteB['bt']};}}")
#            if self.aw.largeLCDs_dialog:
#                self.aw.largeLCDs_dialog.updateStyles()
#        elif lcd == 4:
#            color = QColor(self.aw.lcdpaletteF['deltaet'])
#            color.setHsv(hue,255,255,255)
#            self.aw.lcdpaletteF['deltaet'] = str(color.name())
#            self.aw.lcd4.setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['deltaet']}; background-color: {self.aw.lcdpaletteB['deltaet']};}}")
#            if self.aw.largeDeltaLCDs_dialog:
#                self.aw.largeDeltaLCDs_dialog.updateStyles()
#        elif lcd == 5:
#            color = QColor(self.aw.lcdpaletteF['deltabt'])
#            color.setHsv(hue,255,255,255)
#            self.aw.lcdpaletteF['deltabt'] = str(color.name())
#            self.aw.lcd5.setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['deltabt']}; background-color: {self.aw.lcdpaletteB['deltabt']};}}")
#            if self.aw.largeDeltaLCDs_dialog:
#                self.aw.largeDeltaLCDs_dialog.updateStyles()
#        elif lcd == 6:
#            color = QColor(self.aw.lcdpaletteF['sv'])
#            color.setHsv(hue,255,255,255)
#            self.aw.lcdpaletteF['sv'] = str(color.name())
#            self.aw.lcd6.setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['sv']}; background-color: {self.aw.lcdpaletteB['sv']};}}")
#            self.aw.lcd7.setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['sv']}; background-color: {self.aw.lcdpaletteB['sv']};}}")
#            for i in range(len(self.aw.qmc.extradevices)):
#                self.aw.extraLCD1[i].setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['sv']}; background-color: {self.aw.lcdpaletteB['sv']};}}")
#                self.aw.extraLCD2[i].setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['sv']}; background-color: {self.aw.lcdpaletteB['sv']};}}")
#            if self.aw.largePIDLCDs_dialog:
#                self.aw.largePIDLCDs_dialog.updateStyles()
#            if self.aw.largeExtraLCDs_dialog:
#                self.aw.largeExtraLCDs_dialog.updateStyles()
#            if self.aw.largePhasesLCDs_dialog:
#                self.aw.largePhasesLCDs_dialog.updateStyles()

    @pyqtSlot(bool)
    def paintlcdsSlot(self,_):
        lcdButton = self.sender()
        if lcdButton in [self.lcd1LEDButton,self.lcd1backButton]:
            if lcdButton == self.lcd1backButton:
                self.setlcdColor(self.aw.lcdpaletteB,self.aw.lcdpaletteF,'timer')
            else:
                self.setlcdColor(self.aw.lcdpaletteF,self.aw.lcdpaletteB,'timer')
            self.aw.setTimerColor('timer')
            if self.aw.largeLCDs_dialog:
                self.aw.largeLCDs_dialog.updateStyles()
        if lcdButton in [self.lcd2LEDButton,self.lcd2backButton]:
            if lcdButton == self.lcd2backButton:
                self.setlcdColor(self.aw.lcdpaletteB,self.aw.lcdpaletteF,'et')
            else:
                self.setlcdColor(self.aw.lcdpaletteF,self.aw.lcdpaletteB,'et')
            self.aw.lcd2.setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['et']}; background-color: {self.aw.lcdpaletteB['et']};}}")
            if self.aw.largeLCDs_dialog:
                self.aw.largeLCDs_dialog.updateStyles()
        if lcdButton in [self.lcd3LEDButton,self.lcd3backButton]:
            if lcdButton == self.lcd3backButton:
                self.setlcdColor(self.aw.lcdpaletteB,self.aw.lcdpaletteF,'bt')
            else:
                self.setlcdColor(self.aw.lcdpaletteF,self.aw.lcdpaletteB,'bt')
            self.aw.lcd3.setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['bt']}; background-color: {self.aw.lcdpaletteB['bt']};}}")
            if self.aw.largeLCDs_dialog:
                self.aw.largeLCDs_dialog.updateStyles()
        if lcdButton in [self.lcd4LEDButton,self.lcd4backButton]:
            if lcdButton == self.lcd4backButton:
                self.setlcdColor(self.aw.lcdpaletteB,self.aw.lcdpaletteF,'deltaet')
            else:
                self.setlcdColor(self.aw.lcdpaletteF,self.aw.lcdpaletteB,'deltaet')
            self.aw.lcd4.setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['deltaet']}; background-color: {self.aw.lcdpaletteB['deltaet']};}}")
            if self.aw.largeDeltaLCDs_dialog:
                self.aw.largeDeltaLCDs_dialog.updateStyles()
        if lcdButton in [self.lcd5LEDButton,self.lcd5backButton]:
            if lcdButton == self.lcd5backButton:
                self.setlcdColor(self.aw.lcdpaletteB,self.aw.lcdpaletteF,'deltabt')
            else:
                self.setlcdColor(self.aw.lcdpaletteF,self.aw.lcdpaletteB,'deltabt')
            self.aw.lcd5.setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['deltabt']}; background-color: {self.aw.lcdpaletteB['deltabt']};}}")
            if self.aw.largeDeltaLCDs_dialog:
                self.aw.largeDeltaLCDs_dialog.updateStyles()
        if lcdButton in [self.lcd6LEDButton,self.lcd6backButton]:
            if lcdButton == self.lcd6backButton:
                self.setlcdColor(self.aw.lcdpaletteB,self.aw.lcdpaletteF,'sv')
            else:
                self.setlcdColor(self.aw.lcdpaletteF,self.aw.lcdpaletteB,'sv')
            self.aw.lcd6.setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['sv']}; background-color: {self.aw.lcdpaletteB['sv']};}}")
            self.aw.lcd7.setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['sv']}; background-color: {self.aw.lcdpaletteB['sv']};}}")
            for i in range(len(self.aw.qmc.extradevices)):
                self.aw.extraLCD1[i].setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['sv']}; background-color: {self.aw.lcdpaletteB['sv']};}}")
                self.aw.extraLCD2[i].setStyleSheet(f"QLCDNumber {{ border-radius: 4; color: {self.aw.lcdpaletteF['sv']}; background-color: {self.aw.lcdpaletteB['sv']};}}")
            if self.aw.largePIDLCDs_dialog:
                self.aw.largePIDLCDs_dialog.updateStyles()
            if self.aw.largeExtraLCDs_dialog:
                self.aw.largeExtraLCDs_dialog.updateStyles()
            if self.aw.largePhasesLCDs_dialog:
                self.aw.largePhasesLCDs_dialog.updateStyles()
        if lcdButton in [self.lcd7LEDButton,self.lcd7backButton]:
            if lcdButton == self.lcd7backButton:
                self.setlcdColor(self.aw.lcdpaletteB,self.aw.lcdpaletteF,'rstimer')
            else:
                self.setlcdColor(self.aw.lcdpaletteF,self.aw.lcdpaletteB,'rstimer')
            if self.aw.largeLCDs_dialog:
                self.aw.largeLCDs_dialog.updateStyles()
        if lcdButton in [self.lcd8LEDButton,self.lcd8backButton]:
            if lcdButton == self.lcd8backButton:
                self.setlcdColor(self.aw.lcdpaletteB,self.aw.lcdpaletteF,'slowcoolingtimer')
            else:
                self.setlcdColor(self.aw.lcdpaletteF,self.aw.lcdpaletteB,'slowcoolingtimer')
            if self.aw.largeLCDs_dialog:
                self.aw.largeLCDs_dialog.updateStyles()
        self.setColorButtons()

    def setColorButtons(self):
        for ll,tt in [
                # Curves (background curves handled separately)
                (self.metButton,'et'),
                (self.btButton,'bt'),
                (self.deltametButton,'deltaet'),
                (self.deltabtButton,'deltabt'),
                # Graph
                (self.canvasButton,'canvas'),
                (self.backgroundButton,'background'),
                (self.titleButton,'title'),
                (self.gridButton,'grid'),
                (self.yButton,'ylabel'),
                (self.xButton,'xlabel'),
                (self.timeguideButton,'timeguide'),
                (self.aucguideButton,'aucguide'),
                (self.aucareaButton,'aucarea'),
                (self.watermarksButton,'watermarks'),
                (self.rect1Button,'rect1'),
                (self.rect2Button,'rect2'),
                (self.rect3Button,'rect3'),
                (self.rect4Button,'rect4'),
                (self.rect5Button,'rect5'),
                (self.markersButton,'markers'),
                (self.textButton,'text'),
                (self.legendbgButton,'legendbg'),
                (self.legendborderButton,'legendborder'),
                (self.specialeventboxButton,'specialeventbox'),
                (self.specialeventtextButton,'specialeventtext'),
                (self.bgeventmarkerButton,'bgeventmarker'),
                (self.bgeventtextButton,'bgeventtext'),
                (self.mettextButton,'mettext'),
                (self.metboxButton,'metbox'),
                (self.analysismaskButton,'analysismask'),
                (self.statsanalysisbkgndButton,'statsanalysisbkgnd'),
                ]:
            self.setColorButton(ll,tt)

        # Curves, set background colors and alpha
        self.bgmetButton.setText(self.aw.qmc.backgroundmetcolor)
        self.bgbtButton.setText(self.aw.qmc.backgroundbtcolor)
        self.bgdeltametButton.setText(self.aw.qmc.backgrounddeltaetcolor)
        self.bgdeltabtButton.setText(self.aw.qmc.backgrounddeltabtcolor)
        self.bgextraButton.setText(self.aw.qmc.backgroundxtcolor)
        self.bgextra2Button.setText(self.aw.qmc.backgroundytcolor)
        self.bgmetButton.setStyleSheet('QPushButton { background-color: ' + self.aw.qmc.backgroundmetcolor + '; color: ' + self.aw.labelBorW(self.aw.qmc.backgroundmetcolor) + ';' + self.commonstyle + '}')
        self.bgbtButton.setStyleSheet('QPushButton { background-color: ' + self.aw.qmc.backgroundbtcolor + '; color: ' + self.aw.labelBorW(self.aw.qmc.backgroundbtcolor) + ';' + self.commonstyle + '}')
        self.bgdeltametButton.setStyleSheet('QPushButton { background-color: ' + self.aw.qmc.backgrounddeltaetcolor + '; color: ' + self.aw.labelBorW(self.aw.qmc.backgrounddeltaetcolor) + ';' + self.commonstyle + '}')
        self.bgdeltabtButton.setStyleSheet('QPushButton { background-color: ' + self.aw.qmc.backgrounddeltabtcolor + '; color: ' + self.aw.labelBorW(self.aw.qmc.backgrounddeltabtcolor) + ';' + self.commonstyle + '}')
        self.bgextraButton.setStyleSheet('QPushButton { background-color: ' + self.aw.qmc.backgroundxtcolor + '; color: ' + self.aw.labelBorW(self.aw.qmc.backgroundxtcolor) + ';' + self.commonstyle + '}')
        self.bgextra2Button.setStyleSheet('QPushButton { background-color: ' + self.aw.qmc.backgroundytcolor + '; color: ' + self.aw.labelBorW(self.aw.qmc.backgroundytcolor) + ';' + self.commonstyle + '}')
        self.opaqbgSpinBox.setValue(int(round(self.aw.qmc.backgroundalpha * 10)))

        # LEDs
        self.lcd1backButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['timer'] + '; color: ' + self.aw.lcdpaletteF['timer'] + ';' + self.commonstyle)
        self.lcd1LEDButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['timer'] + '; color: ' + self.aw.lcdpaletteF['timer'] + ';' + self.commonstyle)
        self.lcd2backButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['et'] + '; color: ' + self.aw.lcdpaletteF['et'] + ';' + self.commonstyle)
        self.lcd2LEDButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['et'] + '; color: ' + self.aw.lcdpaletteF['et'] + ';' + self.commonstyle)
        self.lcd3backButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['bt'] + '; color: ' + self.aw.lcdpaletteF['bt'] + ';' + self.commonstyle)
        self.lcd3LEDButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['bt'] + '; color: ' + self.aw.lcdpaletteF['bt'] + ';' + self.commonstyle)
        self.lcd4backButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['deltaet'] + '; color: ' + self.aw.lcdpaletteF['deltaet'] + ';' + self.commonstyle)
        self.lcd4LEDButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['deltaet'] + '; color: ' + self.aw.lcdpaletteF['deltaet'] + ';' + self.commonstyle)
        self.lcd5backButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['deltabt'] + '; color: ' + self.aw.lcdpaletteF['deltabt'] + ';' + self.commonstyle)
        self.lcd5LEDButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['deltabt'] + '; color: ' + self.aw.lcdpaletteF['deltabt'] + ';' + self.commonstyle)
        self.lcd6backButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['sv'] + '; color: ' + self.aw.lcdpaletteF['sv'] + ';' + self.commonstyle)
        self.lcd6LEDButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['sv'] + '; color: ' + self.aw.lcdpaletteF['sv'] + ';' + self.commonstyle)
        self.lcd7backButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['rstimer'] + '; color: ' + self.aw.lcdpaletteF['rstimer'] + ';' + self.commonstyle)
        self.lcd7LEDButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['rstimer'] + '; color: ' + self.aw.lcdpaletteF['rstimer'] + ';' + self.commonstyle)
        self.lcd8backButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['slowcoolingtimer'] + '; color: ' + self.aw.lcdpaletteF['slowcoolingtimer'] + ';' + self.commonstyle)
        self.lcd8LEDButton.setStyleSheet('background-color: ' + self.aw.lcdpaletteB['slowcoolingtimer'] + '; color: ' + self.aw.lcdpaletteF['slowcoolingtimer'] + ';' + self.commonstyle)

        if str(self.aw.qmc.palette['canvas']) == 'None':
#            self.canvasLabel.setStyleSheet("QLabel { background-color: #f0f0f0 }")
            self.canvasLabel.setStyleSheet('QPushButton {background-color: #f0f0f0 ;' + self.commonstyle + '}')

    def setColorButton(self,button,tag):
        c = self.aw.qmc.palette[tag]
        button.setText(c)
        tc = self.aw.labelBorW(c)
        button.setStyleSheet('QPushButton {background: ' + c + '; color: ' + tc + ';' + self.commonstyle + '}')

    # adds a new event to the Dlg
    @pyqtSlot(bool)
    def recolor1(self,_):
        self.aw.qmc.changeGColor(1)
        self.setColorButtons()

    @pyqtSlot(bool)
    def recolor2(self,_):
        self.aw.qmc.changeGColor(2)
        self.setColorButtons()

    def adjustOpaqenesss(self,spinbox,coloralpha):
        #block button
        spinbox.setDisabled(True)
        self.aw.qmc.alpha[coloralpha] = spinbox.value()/10.
#        coloralpha = spinbox.value()/10.
        self.aw.qmc.redraw(recomputeAllDeltas=False)
        #reactivate button
        spinbox.setDisabled(False)

    @pyqtSlot(int)
    def adjustOpaqenesssSlot(self,_):
        widget = self.sender()
#        if widget == self.opaqbgSpinBox:
#            self.adjustOpaqenesss(self.opaqbgSpinBox,self.aw.qmc.backgroundalpha)
        if widget == self.legendbgSpinBox:
            self.adjustOpaqenesss(self.legendbgSpinBox,'legendbg')
        if widget == self.analysismaskSpinBox:
            self.adjustOpaqenesss(self.analysismaskSpinBox,'analysismask')
        if widget == self.statsanalysisbkgndSpinBox:
            self.adjustOpaqenesss(self.statsanalysisbkgndSpinBox,'statsanalysisbkgnd')

    @pyqtSlot(bool)
    def setbgColorSlot(self,_):
        widget = self.sender()
        if widget == self.bgmetButton:
            self.setbgColor('ET',self.bgmetButton,self.aw.qmc.backgroundmetcolor)
        elif widget == self.bgbtButton:
            self.setbgColor('BT',self.bgbtButton,self.aw.qmc.backgroundbtcolor)
        elif widget == self.bgdeltametButton:
            self.setbgColor('DeltaET',self.bgdeltametButton,self.aw.qmc.backgrounddeltaetcolor)
        elif widget == self.bgdeltabtButton:
            self.setbgColor('DeltaBT',self.bgdeltabtButton,self.aw.qmc.backgrounddeltabtcolor)
        elif widget == self.bgextraButton:
            self.setbgColor('Extra1',self.bgextraButton,self.aw.qmc.backgroundxtcolor)
        elif widget == self.bgextra2Button:
            self.setbgColor('Extra2',self.bgextra2Button,self.aw.qmc.backgroundytcolor)

    def setbgColor(self,title,var,color):
        labelcolor = QColor(color)
        colorf = self.aw.colordialog(labelcolor)
        if colorf.isValid():
            color = str(colorf.name())
            self.aw.updateCanvasColors()
            tc = self.aw.labelBorW(color)
            var.setText(colorf.name())
            var.setStyleSheet('QPushButton { background-color: ' + color + '; color: ' + tc + ';' + self.commonstyle + '}')
#  is this needed?            var.setPalette(QPalette(colorf))
            self.aw.qmc.fig.canvas.redraw(recomputeAllDeltas=False)
            if title == 'ET':
                self.aw.qmc.backgroundmetcolor = color
            elif title == 'BT':
                self.aw.qmc.backgroundbtcolor = color
            elif title == 'DeltaET':
                self.aw.qmc.backgrounddeltaetcolor = color
            elif title == 'DeltaBT':
                self.aw.qmc.backgrounddeltabtcolor = color
            elif title == 'Extra1':
                self.aw.qmc.backgroundxtcolor = color
            elif title == 'Extra2':
                self.aw.qmc.backgroundytcolor = color
            self.aw.sendmessage(QApplication.translate('Message','Color of {0} set to {1}').format(title,str(color)))

    def setlcdColor(self,palette,disj_palette,select):
        res = self.aw.colordialog(QColor(palette[select]))
        if QColor.isValid(res):
            nc = str(res.name())
            if nc == disj_palette[select] or (nc in ['white', '#ffffff'] and disj_palette[select] in ['white', '#ffffff']) or (nc in ['black', '#000000'] and disj_palette[select] in ['black', '#000000']):
                # this QMessageBox is not rendered native on macOS for unkonwn reason. The same dialog called from a different dialog is rendered nativ.
                QMessageBox.warning(self.aw,
                    QApplication.translate('Message', 'Config LCD colors'),
                    QApplication.translate('Message', 'LCD digits color and background color cannot be the same.'),
                    QMessageBox.StandardButton.Ok)
            else:
                palette[select] = nc

    @pyqtSlot(bool)
    def setColorSlot(self,_):
        widget = self.sender()
        if widget == self.metButton:
            self.setColor('ET',self.metButton,'et')
        elif widget == self.btButton:
            self.setColor('BT',self.btButton,'bt')
        elif widget == self.deltametButton:
            self.setColor('DeltaET',self.deltametButton,'deltaet')
        elif widget == self.deltabtButton:
            self.setColor('DeltaBT',self.deltabtButton,'deltabt')
        elif widget == self.backgroundButton:
            self.setColor('Background',self.backgroundButton,'background')
        elif widget == self.gridButton:
            self.setColor('Grid',self.gridButton,'grid')
        elif widget == self.titleButton:
            self.setColor('Title',self.titleButton,'title')
        elif widget ==self.yButton:
            self.setColor('Y Button',self.yButton,'ylabel')
        elif widget == self.xButton:
            self.setColor('X Button',self.xButton,'xlabel')
        elif widget == self.rect1Button:
            self.setColor('Drying Phase',self.rect1Button,'rect1')
        elif widget == self.rect2Button:
            self.setColor('Maillard Phase',self.rect2Button,'rect2')
        elif widget == self.rect3Button:
            self.setColor('Finishing Phase',self.rect3Button,'rect3')
        elif widget == self.rect4Button:
            self.setColor('Cooling Phase',self.rect4Button,'rect4')
        elif widget == self.rect5Button:
            self.setColor('Bars Bkgnd',self.rect5Button,'rect5')
        elif widget == self.markersButton:
            self.setColor('Markers',self.markersButton,'markers')
        elif widget == self.textButton:
            self.setColor('Text',self.textButton,'text')
        elif widget == self.watermarksButton:
            self.setColor('Watermarks',self.watermarksButton,'watermarks')
        elif widget == self.timeguideButton:
            self.setColor('Time Guide',self.timeguideButton,'timeguide')
        elif widget == self.aucguideButton:
            self.setColor('AUC Guide',self.aucguideButton,'aucguide')
        elif widget == self.aucareaButton:
            self.setColor('AUC Area',self.aucareaButton,'aucarea')
        elif widget == self.legendbgButton:
            self.setColor('legendbg',self.legendbgButton,'legendbg')
        elif widget == self.legendborderButton:
            self.setColor('legendborder',self.legendborderButton,'legendborder')
        elif widget == self.canvasButton:
            self.setColor('canvas',self.canvasButton,'canvas')
        elif widget == self.specialeventboxButton:
            self.setColor('specialeventbox',self.specialeventboxButton,'specialeventbox')
        elif widget == self.specialeventtextButton:
            self.setColor('specialeventtext',self.specialeventtextButton,'specialeventtext')
        elif widget == self.bgeventmarkerButton:
            self.setColor('bgeventmarker',self.bgeventmarkerButton,'bgeventmarker')
        elif widget == self.bgeventtextButton:
            self.setColor('bgeventtext',self.bgeventtextButton,'bgeventtext')
        elif widget == self.mettextButton:
            self.setColor('mettext',self.mettextButton,'mettext')
        elif widget == self.metboxButton:
            self.setColor('metbox',self.metboxButton,'metbox')
        elif widget == self.analysismaskButton:
            self.setColor('Analysis Mask',self.analysismaskButton,'analysismask')
        elif widget == self.statsanalysisbkgndButton:
            self.setColor('Analysis Result',self.statsanalysisbkgndButton,'statsanalysisbkgnd')

    def colorButton(self,s):
        button = QPushButton(s)
        button.setPalette(QPalette(QColor(s)))
        button.setStyleSheet('QPushButton {background-color:' + s + ';' + self.commonstyle + '}')
        return button

    def setColor(self,title,var,color):
        labelcolor = QColor(self.aw.qmc.palette[color])
        colorf = self.aw.colordialog(labelcolor)
        if colorf.isValid():
            self.aw.qmc.palette[color] = str(colorf.name())
            self.aw.updateCanvasColors()
            self.aw.applyStandardButtonVisibility()
            self.aw.update_extraeventbuttons_visibility()
            var.setText(colorf.name())
            tc = self.aw.labelBorW(self.aw.qmc.palette[color])
            var.setStyleSheet('QPushButton { background: ' + self.aw.qmc.palette[color] + '; color: ' + tc + ';' + self.commonstyle + '}')
#            var.setPalette(QPalette(colorf))
            self.aw.qmc.fig.canvas.redraw(recomputeAllDeltas=False)
            if title == 'ET':
                self.aw.setLabelColor(self.aw.label2,QColor(self.aw.qmc.palette[color]))
            elif title == 'BT':
                self.aw.setLabelColor(self.aw.label3,QColor(self.aw.qmc.palette[color]))
            elif title == 'DeltaET':
                self.aw.setLabelColor(self.aw.label4,QColor(self.aw.qmc.palette[color]))
            elif title == 'DeltaBT':
                self.aw.setLabelColor(self.aw.label5,QColor(self.aw.qmc.palette[color]))
            self.aw.sendmessage(QApplication.translate('Message','Color of {0} set to {1}').format(title,str(self.aw.qmc.palette[color])))

    @pyqtSlot(int)
    def adjustintensity(self,_):
        #block button
        self.opaqbgSpinBox.setDisabled(True)
        self.aw.qmc.backgroundalpha = self.opaqbgSpinBox.value()/10.
        self.aw.qmc.redraw(recomputeAllDeltas=False)
        #reactivate button
        self.opaqbgSpinBox.setDisabled(False)
