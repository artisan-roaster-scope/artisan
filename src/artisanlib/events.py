#
# ABOUT
# Artisan Events Dialog

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
import platform
import logging
from typing import Final, List, Optional, Any, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.types import Palette
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent # pylint: disable=unused-import

from artisanlib.util import uchr, comma2dot
from artisanlib.dialogs import ArtisanResizeablDialog, ArtisanDialog
from artisanlib.widgets import MyQComboBox, MyQDoubleSpinBox

from uic import SliderCalculatorDialog # pyright: ignore[attr-defined] # pylint: disable=no-name-in-module


try:
    from PyQt6.QtCore import (Qt, pyqtSlot, QSettings, QTimer) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import (QColor, QFont, QIntValidator) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QCheckBox, QComboBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, # @UnusedImport @Reimport  @UnresolvedImport
                                 QPushButton, QSpinBox, QWidget, QTabWidget, QDialogButtonBox, # @UnusedImport @Reimport  @UnresolvedImport
                                 QGridLayout, QGroupBox, QTableWidget, QHeaderView, QToolButton) # @UnusedImport @Reimport  @UnresolvedImport
#    from PyQt6 import sip # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import (Qt, pyqtSlot, QSettings, QTimer) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import (QColor, QFont, QIntValidator) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
                                 QPushButton, QSpinBox, QWidget, QTabWidget, QDialogButtonBox, # @UnusedImport @Reimport  @UnresolvedImport
                                 QGridLayout, QGroupBox, QTableWidget, QHeaderView, QToolButton) # @UnusedImport @Reimport  @UnresolvedImport
#    try:
#        from PyQt5 import sip # type: ignore # @Reimport @UnresolvedImport @UnusedImport
#    except ImportError:
#        import sip  # type: ignore # @Reimport @UnresolvedImport @UnusedImport


_log: Final[logging.Logger] = logging.getLogger(__name__)

class EventsDlg(ArtisanResizeablDialog):
    def __init__(self, parent:QWidget, aw:'ApplicationWindow', activeTab:int = 0) -> None:
        super().__init__(parent, aw)
        self.app = self.aw.app
        self.activeTab = activeTab

        self.buttonlistmaxlen:int = self.aw.buttonlistmaxlen

        self.extraeventslabels: List[str] = []
        self.extraeventsdescriptions: List[str] = []
        self.extraeventstypes: List[int] = []
        self.extraeventsvalues: List[float] = []
        self.extraeventbuttoncolor:List[str] = []
        self.extraeventbuttontextcolor:List[str] = []
        self.extraeventsactionstrings:List[str] = []
        self.extraeventsactions:List[int] = []
        self.extraeventsvisibility:List[int] = []

        self.eventslidervisibilities:List[int] = [0,0,0,0]
        self.eventslideractions:List[int] = [0,0,0,0]
        self.eventslidercommands:List[str] = ['','','','']
        self.eventslideroffsets:List[float] = [0.,0.,0.,0.]
        self.eventsliderfactors:List[float] = [1.0,1.0,1.0,1.0]
        self.eventslidermin:List[int] = [0,0,0,0]
        self.eventslidermax:List[int] = [100,100,100,100]
        self.eventsliderBernoulli:List[int] = [0,0,0,0]
        self.eventslidercoarse:List[int] = [0,0,0,0]
        self.eventslidertemp:List[int] = [0,0,0,0]
        self.eventsliderunits:List[str] = ['','','','']
        # quantifiers
        self.eventquantifieractive:List[int] = [0,0,0,0]
        self.eventquantifiersource:List[int] = [0,0,0,0]
        self.eventquantifiermin:List[int] = [0,0,0,0]
        self.eventquantifiermax:List[int] = [100,100,100,100]
        self.eventquantifiercoarse:List[int] = [0,0,0,0]
        self.eventquantifieraction:List[int] = [0,0,0,0]
        self.eventquantifierSV:List[int] = [0,0,0,0]
        # palettes
        self.buttonpalette:List[Palette] = []
        for _ in range(self.aw.max_palettes):
            self.buttonpalette.append(self.aw.makePalette())
        self.buttonpalettemaxlen:List[int] = [14]*10
        self.buttonpalette_label:str = self.aw.buttonpalette_label
        # styles
        self.EvalueColor:List[str] = self.aw.qmc.EvalueColor_default.copy()
        self.EvalueMarker:List[str] = ['o','s','h','D']
        self.Evaluelinethickness:List[float] = [1,1,1,1]
        self.Evaluealpha:List[float] = [.8,.8,.8,.8]
        self.EvalueMarkerSize:List[float] = [4,4,4,4]
        # event annotations
        self.specialeventannovisibilities:List[int] = [0,0,0,0]
        self.specialeventannotations:List[str] = ['','','','']

        self.custom_button_actions:List[str] = ['',
                                     QApplication.translate('ComboBox','Serial Command'),
                                     QApplication.translate('ComboBox','Call Program'),
                                     QApplication.translate('ComboBox','Multiple Event'),
                                     QApplication.translate('ComboBox','Modbus Command'),
                                     QApplication.translate('ComboBox','DTA Command'),
                                     QApplication.translate('ComboBox','IO Command'),
                                     QApplication.translate('ComboBox','Hottop Heater'),
                                     QApplication.translate('ComboBox','Hottop Fan'),
                                     QApplication.translate('ComboBox','Hottop Command'),
                                     QApplication.translate('ComboBox','p-i-d'),
                                     QApplication.translate('ComboBox','Fuji Command'),
                                     QApplication.translate('ComboBox','PWM Command'),
                                     QApplication.translate('ComboBox','VOUT Command'),
                                     QApplication.translate('ComboBox','S7 Command'),
                                     QApplication.translate('ComboBox','Aillio R1 Heater'),
                                     QApplication.translate('ComboBox','Aillio R1 Fan'),
                                     QApplication.translate('ComboBox','Aillio R1 Drum'),
                                     QApplication.translate('ComboBox','Aillio R1 Command'),
                                     QApplication.translate('ComboBox','Artisan Command'),
                                     QApplication.translate('ComboBox','RC Command'),
                                     QApplication.translate('ComboBox','WebSocket Command'),
                                     QApplication.translate('ComboBox','Stepper Command')]
        self.custom_button_actions_sorted:List[str] = sorted(self.custom_button_actions)

        titlefont = QFont()
        titlefont.setBold(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Events'))
        self.setModal(True)
        self.helpdialog = None
        settings = QSettings()
        if settings.contains('EventsGeometry'):
            self.restoreGeometry(settings.value('EventsGeometry'))

        self.storeState()

        ## TAB 7
        showAnnoLabel = QLabel()
        showAnnoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignRight)
        showAnnoLabel.setText(QApplication.translate('Label', 'Show'))
        showAnnoLabel.setFont(titlefont)
        AnnoLabel = QLabel()
        AnnoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignRight)
        AnnoLabel.setText(QApplication.translate('Label', 'Annotation'))
        AnnoLabel.setFont(titlefont)

        Epreview1Label = QLabel()
        Epreview1Label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignRight)
        Epreview1Label.setText(QApplication.translate('Label', 'Example before FCs'))
        Epreview1Label.setFont(titlefont)
        Epreview2Label = QLabel()
        Epreview2Label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignRight)
        Epreview2Label.setText(QApplication.translate('Label', 'Example after FCs'))
        Epreview2Label.setFont(titlefont)

        self.E1AnnoVisibility = QCheckBox(self.aw.qmc.etypesf(0))
        self.E1AnnoVisibility.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1AnnoVisibility.setChecked(bool(self.aw.qmc.specialeventannovisibilities[0]))
        self.E2Annovisibility = QCheckBox(self.aw.qmc.etypesf(1))
        self.E2Annovisibility.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2Annovisibility.setChecked(bool(self.aw.qmc.specialeventannovisibilities[1]))
        self.E3Annovisibility = QCheckBox(self.aw.qmc.etypesf(2))
        self.E3Annovisibility.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3Annovisibility.setChecked(bool(self.aw.qmc.specialeventannovisibilities[2]))
        self.E4Annovisibility = QCheckBox(self.aw.qmc.etypesf(3))
        self.E4Annovisibility.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4Annovisibility.setChecked(bool(self.aw.qmc.specialeventannovisibilities[3]))

        self.E1Edit = QLineEdit(self.aw.qmc.specialeventannotations[0])
        self.E1Edit.setMinimumSize(self.E1Edit.sizeHint())
        self.E1Edit.textChanged.connect(self.changeSpecialeventEdit1)
        self.E1Edit.setToolTip(QApplication.translate('Tooltip', 'Definition string for special event annotation'))
        self.E1Preview1 = QLabel(self.aw.qmc.parseSpecialeventannotation(self.E1Edit.text(),eventnum=0,applyto='preview',postFCs=False))
        self.E1Preview2 = QLabel(self.aw.qmc.parseSpecialeventannotation(self.E1Edit.text(),eventnum=0,applyto='preview',postFCs=True))

        self.E2Edit = QLineEdit(self.aw.qmc.specialeventannotations[1])
        self.E2Edit.setMinimumSize(self.E2Edit.sizeHint())
        self.E2Edit.textChanged.connect(self.changeSpecialeventEdit2)
        self.E2Edit.setToolTip(QApplication.translate('Tooltip', 'Definition string for special event annotation'))
        self.E2Preview1 = QLabel(self.aw.qmc.parseSpecialeventannotation(self.E2Edit.text(),eventnum=0,applyto='preview',postFCs=False))
        self.E2Preview2 = QLabel(self.aw.qmc.parseSpecialeventannotation(self.E2Edit.text(),eventnum=0,applyto='preview',postFCs=True))

        self.E3Edit = QLineEdit(self.aw.qmc.specialeventannotations[2])
        self.E3Edit.setMinimumSize(self.E3Edit.sizeHint())
        self.E3Edit.textChanged.connect(self.changeSpecialeventEdit3)
        self.E3Edit.setToolTip(QApplication.translate('Tooltip', 'Definition string for special event annotation'))
        self.E3Preview1 = QLabel(self.aw.qmc.parseSpecialeventannotation(self.E3Edit.text(),eventnum=0,applyto='preview',postFCs=False))
        self.E3Preview2 = QLabel(self.aw.qmc.parseSpecialeventannotation(self.E3Edit.text(),eventnum=0,applyto='preview',postFCs=True))

        self.E4Edit = QLineEdit(self.aw.qmc.specialeventannotations[3])
        self.E4Edit.setMinimumSize(self.E4Edit.sizeHint())
        self.E4Edit.textChanged.connect(self.changeSpecialeventEdit4)
        self.E4Edit.setToolTip(QApplication.translate('Tooltip', 'Definition string for special event annotation'))
        self.E4Preview1 = QLabel(self.aw.qmc.parseSpecialeventannotation(self.E4Edit.text(),eventnum=0,applyto='preview',postFCs=False))
        self.E4Preview2 = QLabel(self.aw.qmc.parseSpecialeventannotation(self.E4Edit.text(),eventnum=0,applyto='preview',postFCs=True))

        #tab 7
        eventannoLayout = QGridLayout()
        eventannoLayout.addWidget(showAnnoLabel, 0,0,Qt.AlignmentFlag.AlignLeft)
        eventannoLayout.addWidget(AnnoLabel,     0,1,Qt.AlignmentFlag.AlignLeft)
        eventannoLayout.addWidget(Epreview1Label,0,2,Qt.AlignmentFlag.AlignLeft)
        eventannoLayout.addWidget(Epreview2Label,0,3,Qt.AlignmentFlag.AlignLeft)

        eventannoLayout.addWidget(self.E1AnnoVisibility,1,0)
        eventannoLayout.addWidget(self.E2Annovisibility,2,0)
        eventannoLayout.addWidget(self.E3Annovisibility,3,0)
        eventannoLayout.addWidget(self.E4Annovisibility,4,0)

        eventannoLayout.addWidget(self.E1Edit,1,1)
        eventannoLayout.addWidget(self.E2Edit,2,1)
        eventannoLayout.addWidget(self.E3Edit,3,1)
        eventannoLayout.addWidget(self.E4Edit,4,1)
        eventannoLayout.addWidget(self.E1Preview1,1,2,Qt.AlignmentFlag.AlignLeft)
        eventannoLayout.addWidget(self.E2Preview1,2,2,Qt.AlignmentFlag.AlignLeft)
        eventannoLayout.addWidget(self.E3Preview1,3,2,Qt.AlignmentFlag.AlignLeft)
        eventannoLayout.addWidget(self.E4Preview1,4,2,Qt.AlignmentFlag.AlignLeft)
        eventannoLayout.addWidget(self.E1Preview2,1,3,Qt.AlignmentFlag.AlignLeft)
        eventannoLayout.addWidget(self.E2Preview2,2,3,Qt.AlignmentFlag.AlignLeft)
        eventannoLayout.addWidget(self.E3Preview2,3,3,Qt.AlignmentFlag.AlignLeft)
        eventannoLayout.addWidget(self.E4Preview2,4,3,Qt.AlignmentFlag.AlignLeft)

        eventannoLayout.setColumnStretch(0,0)
        eventannoLayout.setColumnStretch(1,10)
        eventannoLayout.setColumnStretch(2,0)
        eventannoLayout.setColumnStretch(3,0)

        overlapeditLabel = QLabel(QApplication.translate('Label', 'Allowed Annotation Overlap'))
        self.overlapEdit = QSpinBox()
        self.overlapEdit.setRange(0,100)    #(min,max)
        self.overlapEdit.setMinimumWidth(80)
        self.overlapEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.overlapEdit.setValue(int(self.aw.qmc.overlappct))
        self.overlapEdit.setSuffix(' %')

        helpcurveDialogButton = QDialogButtonBox()
        helpButton: Optional[QPushButton] = helpcurveDialogButton.addButton(QDialogButtonBox.StandardButton.Help)
        if helpButton is not None:
            self.setButtonTranslations(helpButton,'Help',QApplication.translate('Button','Help'))
            helpButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            helpButton.clicked.connect(self.showEventannotationhelp)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(overlapeditLabel)
        buttonLayout.addWidget(self.overlapEdit)
        buttonLayout.addStretch()
        buttonLayout.addWidget(helpButton)
        entryLayout = QHBoxLayout()
        entryLayout.addLayout(eventannoLayout)
        #entryLayout.addStretch()
        tab7Layout = QVBoxLayout()
        tab7Layout.addLayout(entryLayout)
        tab7Layout.addStretch()
        tab7Layout.addSpacing(10)
        tab7Layout.addLayout(buttonLayout)

        ## TAB 1
        self.eventsbuttonflag = QCheckBox(QApplication.translate('ComboBox','Event Button'))
        self.eventsbuttonflag.setToolTip(QApplication.translate('Tooltip', 'Display a button that registers events during the roast'))
        self.eventsbuttonflag.setChecked(bool(self.aw.eventsbuttonflag))
        self.eventsbuttonflag.stateChanged.connect(self.eventsbuttonflagChanged)
        self.annotationsflagbox = QCheckBox(QApplication.translate('CheckBox','Annotations'))
        self.annotationsflagbox.setChecked(bool(self.aw.qmc.annotationsflag))
        self.annotationsflagbox.setToolTip(QApplication.translate('Tooltip',
            'Display roast events time and temperature on {} curve',
            'Display roast events time and temperature on BT curve').format(QApplication.translate('Label','BT')))
        self.annotationsflagbox.stateChanged.connect(self.annotationsflagChanged)
        self.showeventsonbtbox = QCheckBox(QApplication.translate('CheckBox','Show on {}', 'Show on BT').format(QApplication.translate('Label','BT')))
        self.showeventsonbtbox.setToolTip(QApplication.translate('Tooltip',
            'Show event type 5 flags anchored on {}, when un-ticked they anchor to the greater of {} or {}',
            'Show event type 5 flags anchored on BT, when un-ticked they anchor to the greater of ET or BT').format(QApplication.translate('Label','BT'),QApplication.translate('Label','ET'),QApplication.translate('Label','BT')))
        self.showeventsonbtbox.setChecked(bool(self.aw.qmc.showeventsonbt))
        self.showeventsonbtbox.stateChanged.connect(self.showeventsonbtChanged)

        self.eventsclampflag = QCheckBox(QApplication.translate('CheckBox','Snap'))
        self.eventsclampflag.setToolTip(QApplication.translate('Tooltip', 'Custom events are drawn using the temperature scale'))
        self.eventsclampflag.setChecked(bool(self.aw.qmc.clampEvents))
        self.eventsclampflag.stateChanged.connect(self.eventsclampflagChanged)
        self.eventslabelsflag = QCheckBox(QApplication.translate('CheckBox','Descr.'))
        self.eventslabelsflag.setToolTip(QApplication.translate('Tooltip', 'Custom event descriptions are shown instead of type/value tags'))
        self.eventslabelsflag.setChecked(bool(self.aw.qmc.renderEventsDescr))
        self.eventslabelsflag.stateChanged.connect(self.eventslabelsflagChanged)
        self.eventslabelscharsSpinner = QSpinBox()
        self.eventslabelscharsSpinner.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.eventslabelscharsSpinner.setSingleStep(1)
        self.eventslabelscharsSpinner.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.eventslabelscharsSpinner.setRange(1,20)
        self.eventslabelscharsSpinner.setValue(int(self.aw.qmc.eventslabelschars))
        self.eventslabelscharsSpinner.setToolTip(QApplication.translate('Tooltip', 'Length of text in event marks'))
        self.eventslabelscharsSpinner.setEnabled(bool(self.aw.qmc.renderEventsDescr))


        if self.aw.qmc.eventsGraphflag not in [2,3,4]:
            self.eventsclampflag.setEnabled(False)
        barstylelabel = QLabel(QApplication.translate('Label','Markers'))
        barstyles = ['',
                    QApplication.translate('ComboBox','Flag'),
                    QApplication.translate('ComboBox','Bar'),
                    QApplication.translate('ComboBox','Step'),
                    QApplication.translate('ComboBox','Step+'),
                    QApplication.translate('ComboBox','Combo')]

        self.bartypeComboBox = QComboBox()
        self.bartypeComboBox.setToolTip(QApplication.translate('Tooltip', 'Choose display style of custom events'))
        self.bartypeComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
#        self.bartypeComboBox.setMaximumWidth(80)
        self.bartypeComboBox.addItems(barstyles)
        if not self.aw.qmc.eventsshowflag:
            self.bartypeComboBox.setCurrentIndex(0)
        else:
            self.bartypeComboBox.setCurrentIndex(self.aw.qmc.eventsGraphflag+1)
        self.bartypeComboBox.currentIndexChanged.connect(self.eventsGraphTypeflagChanged)
        typelabel1 = QLabel('1')
        typelabel2 = QLabel('2')
        typelabel3 = QLabel('3')
        typelabel4 = QLabel('4')
        typelabel5 = QLabel('5')
        self.showEtype1 = QCheckBox()
        self.showEtype2 = QCheckBox()
        self.showEtype3 = QCheckBox()
        self.showEtype4 = QCheckBox()
        self.showEtype5 = QCheckBox()
        self.showEtype1.setToolTip(QApplication.translate('Tooltip', 'Tick to display events of type {}', 'Tick to display events of type 1').format(1))
        self.showEtype2.setToolTip(QApplication.translate('Tooltip', 'Tick to display events of type {}', 'Tick to display events of type 1').format(2))
        self.showEtype3.setToolTip(QApplication.translate('Tooltip', 'Tick to display events of type {}', 'Tick to display events of type 1').format(3))
        self.showEtype4.setToolTip(QApplication.translate('Tooltip', 'Tick to display events of type {}', 'Tick to display events of type 1').format(4))
        self.showEtype5.setToolTip(QApplication.translate('Tooltip', 'Tick to display events of type {}', 'Tick to display events of type 1').format(5))
        self.showEtype1.setChecked(self.aw.qmc.showEtypes[0])
        self.showEtype2.setChecked(self.aw.qmc.showEtypes[1])
        self.showEtype3.setChecked(self.aw.qmc.showEtypes[2])
        self.showEtype4.setChecked(self.aw.qmc.showEtypes[3])
        self.showEtype5.setChecked(self.aw.qmc.showEtypes[4])
        self.showEtype1.stateChanged.connect(self.changeShowEtypes0)         #toggle
        self.showEtype2.stateChanged.connect(self.changeShowEtypes1)         #toggle
        self.showEtype3.stateChanged.connect(self.changeShowEtypes2)         #toggle
        self.showEtype4.stateChanged.connect(self.changeShowEtypes3)         #toggle
        self.showEtype5.stateChanged.connect(self.changeShowEtypes4)         #toggle
        self.etype0 = QLineEdit(self.aw.qmc.etypesf(0))
        self.etype0.setCursorPosition(0)
        self.etype1 = QLineEdit(self.aw.qmc.etypesf(1))
        self.etype1.setCursorPosition(0)
        self.etype2 = QLineEdit(self.aw.qmc.etypesf(2))
        self.etype2.setCursorPosition(0)
        self.etype3 = QLineEdit(self.aw.qmc.etypesf(3))
        self.etype3.setCursorPosition(0)
        self.etype4 = QLabel('--      ')
        self.etype0.setToolTip(QApplication.translate('Tooltip', 'Event type label'))
        self.etype1.setToolTip(QApplication.translate('Tooltip', 'Event type label'))
        self.etype2.setToolTip(QApplication.translate('Tooltip', 'Event type label'))
        self.etype3.setToolTip(QApplication.translate('Tooltip', 'Event type label'))
        self.etype4.setToolTip(QApplication.translate('Tooltip', 'Event type label'))
        self.etype0.setMaximumWidth(60)
        self.etype1.setMaximumWidth(60)
        self.etype2.setMaximumWidth(60)
        self.etype3.setMaximumWidth(60)
        self.E1colorButton = QPushButton(self.aw.qmc.etypesf(0))
        self.E1colorButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2colorButton = QPushButton(self.aw.qmc.etypesf(1))
        self.E2colorButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3colorButton = QPushButton(self.aw.qmc.etypesf(2))
        self.E3colorButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4colorButton = QPushButton(self.aw.qmc.etypesf(3))
        self.E4colorButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1colorButton.clicked.connect(self.setcoloreventline0)
        self.E2colorButton.clicked.connect(self.setcoloreventline1)
        self.E3colorButton.clicked.connect(self.setcoloreventline2)
        self.E4colorButton.clicked.connect(self.setcoloreventline3)
        self.E1textcolorButton = QPushButton(self.aw.qmc.etypesf(0))
        self.E1textcolorButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2textcolorButton = QPushButton(self.aw.qmc.etypesf(1))
        self.E2textcolorButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3textcolorButton = QPushButton(self.aw.qmc.etypesf(2))
        self.E3textcolorButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4textcolorButton = QPushButton(self.aw.qmc.etypesf(3))
        self.E4textcolorButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1textcolorButton.clicked.connect(self.setcoloreventtext0)
        self.E2textcolorButton.clicked.connect(self.setcoloreventtext1)
        self.E3textcolorButton.clicked.connect(self.setcoloreventtext2)
        self.E4textcolorButton.clicked.connect(self.setcoloreventtext3)
        #marker selection for comboboxes
        self.markers = ['',
                        QApplication.translate('Marker','Circle'),
                        QApplication.translate('Marker','Square'),
                        QApplication.translate('Marker','Pentagon'),
                        QApplication.translate('Marker','Diamond'),
                        QApplication.translate('Marker','Star'),
                        QApplication.translate('Marker','Hexagon 1'),
                        QApplication.translate('Marker','Hexagon 2'),
                        QApplication.translate('Marker','+'),
                        QApplication.translate('Marker','x'),
                        QApplication.translate('Marker','None')]
        #keys interpreted by matplotlib. Must match order of self.markers
        self.markervals = [None,'o','s','p','D','*','h','H','+','x','None']
        #Marker type
        self.marker1typeComboBox =  QComboBox()
        self.marker1typeComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.marker1typeComboBox.addItems(self.markers)
        if self.aw.qmc.EvalueMarker[0] in self.markervals:
            self.marker1typeComboBox.setCurrentIndex(self.markervals.index(self.aw.qmc.EvalueMarker[0]))
        else:
            self.marker1typeComboBox.setCurrentIndex(0) # set to first empty entry
        self.marker1typeComboBox.currentIndexChanged.connect(self.seteventmarker0)
        self.marker2typeComboBox =  QComboBox()
        self.marker2typeComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.marker2typeComboBox.addItems(self.markers)
        if self.aw.qmc.EvalueMarker[1] in self.markervals:
            self.marker2typeComboBox.setCurrentIndex(self.markervals.index(self.aw.qmc.EvalueMarker[1]))
        else:
            self.marker2typeComboBox.setCurrentIndex(0) # set to first empty entry
        self.marker2typeComboBox.currentIndexChanged.connect(self.seteventmarker1)
        self.marker3typeComboBox =  QComboBox()
        self.marker3typeComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.marker3typeComboBox.addItems(self.markers)
        if self.aw.qmc.EvalueMarker[2] in self.markervals:
            self.marker3typeComboBox.setCurrentIndex(self.markervals.index(self.aw.qmc.EvalueMarker[2]))
        else:
            self.marker3typeComboBox.setCurrentIndex(0) # set to first empty entry
        self.marker3typeComboBox.currentIndexChanged.connect(self.seteventmarker2)
        self.marker4typeComboBox =  QComboBox()
        self.marker4typeComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.marker4typeComboBox.addItems(self.markers)
        if self.aw.qmc.EvalueMarker[3] in self.markervals:
            self.marker4typeComboBox.setCurrentIndex(self.markervals.index(self.aw.qmc.EvalueMarker[3]))
        else:
            self.marker4typeComboBox.setCurrentIndex(0) # set to first empty entry
        self.marker4typeComboBox.currentIndexChanged.connect(self.seteventmarker3)
        valuecolorlabel = QLabel(QApplication.translate('Label','Color'))
        valuecolorlabel.setFont(titlefont)
        valuetextcolorlabel = QLabel(QApplication.translate('Label','Text Color'))
        valuetextcolorlabel.setFont(titlefont)
        valuesymbollabel = QLabel(QApplication.translate('Label','Marker'))
        valuesymbollabel.setFont(titlefont)
        valuethicknesslabel = QLabel(QApplication.translate('Label','Thickness'))
        valuethicknesslabel.setFont(titlefont)
        valuealphalabel = QLabel(QApplication.translate('Label','Opacity'))
        valuealphalabel.setFont(titlefont)
        valuesizelabel = QLabel(QApplication.translate('Label','Size'))
        valuesizelabel.setFont(titlefont)
        valuecolorlabel.setMaximumSize(80,20)
        valuetextcolorlabel.setMaximumSize(80,20)
        valuesymbollabel.setMaximumSize(70,20)
        valuethicknesslabel.setMaximumSize(80,20)
        valuealphalabel.setMaximumSize(80,20)
        valuesizelabel.setMaximumSize(80,20)
        self.E1thicknessSpinBox = QSpinBox()
        self.E1thicknessSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E1thicknessSpinBox.setSingleStep(1)
        self.E1thicknessSpinBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1thicknessSpinBox.setRange(1,10)
        self.E1thicknessSpinBox.setValue(int(round(self.aw.qmc.Evaluelinethickness[0])))
        self.E1thicknessSpinBox.valueChanged.connect(self.setElinethickness0)
        self.E2thicknessSpinBox = QSpinBox()
        self.E2thicknessSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E2thicknessSpinBox.setSingleStep(1)
        self.E2thicknessSpinBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2thicknessSpinBox.setRange(1,10)
        self.E2thicknessSpinBox.setValue(int(round(self.aw.qmc.Evaluelinethickness[1])))
        self.E2thicknessSpinBox.valueChanged.connect(self.setElinethickness1)
        self.E3thicknessSpinBox = QSpinBox()
        self.E3thicknessSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E3thicknessSpinBox.setSingleStep(1)
        self.E3thicknessSpinBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3thicknessSpinBox.setRange(1,10)
        self.E3thicknessSpinBox.setValue(int(round(self.aw.qmc.Evaluelinethickness[2])))
        self.E3thicknessSpinBox.valueChanged.connect(self.setElinethickness2)
        self.E4thicknessSpinBox = QSpinBox()
        self.E4thicknessSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E4thicknessSpinBox.setSingleStep(1)
        self.E4thicknessSpinBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4thicknessSpinBox.setRange(1,10)
        self.E4thicknessSpinBox.setValue(int(round(self.aw.qmc.Evaluelinethickness[3])))
        self.E4thicknessSpinBox.valueChanged.connect(self.setElinethickness3)
        self.E1alphaSpinBox = MyQDoubleSpinBox()
        self.E1alphaSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E1alphaSpinBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1alphaSpinBox.setRange(.1,1.)
        self.E1alphaSpinBox.setSingleStep(.1)
        self.E1alphaSpinBox.setValue(self.aw.qmc.Evaluealpha[0])
        self.E1alphaSpinBox.valueChanged.connect(self.setElinealpha0)
        self.E2alphaSpinBox = MyQDoubleSpinBox()
        self.E2alphaSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E2alphaSpinBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2alphaSpinBox.setRange(.1,1.)
        self.E2alphaSpinBox.setSingleStep(.1)
        self.E2alphaSpinBox.setValue(self.aw.qmc.Evaluealpha[1])
        self.E1alphaSpinBox.valueChanged.connect(self.setElinealpha1)
        self.E3alphaSpinBox = MyQDoubleSpinBox()
        self.E3alphaSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E3alphaSpinBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3alphaSpinBox.setRange(.1,1.)
        self.E3alphaSpinBox.setSingleStep(.1)
        self.E3alphaSpinBox.setValue(self.aw.qmc.Evaluealpha[2])
        self.E3alphaSpinBox.valueChanged.connect(self.setElinealpha2)
        self.E4alphaSpinBox = MyQDoubleSpinBox()
        self.E4alphaSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E4alphaSpinBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4alphaSpinBox.setRange(.1,1.)
        self.E4alphaSpinBox.setSingleStep(.1)
        self.E4alphaSpinBox.setValue(self.aw.qmc.Evaluealpha[3])
        self.E4alphaSpinBox.valueChanged.connect(self.setElinealpha3)
        #Marker size
        self.E1sizeSpinBox = MyQDoubleSpinBox()
        self.E1sizeSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E1sizeSpinBox.setSingleStep(0.5)
        self.E1sizeSpinBox.setRange(1,14)
        self.E1sizeSpinBox.setValue(self.aw.qmc.EvalueMarkerSize[0])
        self.E1sizeSpinBox.editingFinished.connect(self.setEmarkersize0)
        self.E2sizeSpinBox = MyQDoubleSpinBox()
        self.E2sizeSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E2sizeSpinBox.setSingleStep(0.5)
        self.E2sizeSpinBox.setRange(1,14)
        self.E2sizeSpinBox.setValue(self.aw.qmc.EvalueMarkerSize[1])
        self.E2sizeSpinBox.editingFinished.connect(self.setEmarkersize1)
        self.E3sizeSpinBox = MyQDoubleSpinBox()
        self.E3sizeSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E3sizeSpinBox.setSingleStep(0.5)
        self.E3sizeSpinBox.setRange(1,14)
        self.E3sizeSpinBox.setValue(self.aw.qmc.EvalueMarkerSize[2])
        self.E3sizeSpinBox.editingFinished.connect(self.setEmarkersize2)
        self.E4sizeSpinBox = MyQDoubleSpinBox()
        self.E4sizeSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E4sizeSpinBox.setSingleStep(0.5)
        self.E4sizeSpinBox.setRange(1,14)
        self.E4sizeSpinBox.setValue(self.aw.qmc.EvalueMarkerSize[3])
        self.E4sizeSpinBox.editingFinished.connect(self.setEmarkersize3)
        self.autoCharge = QCheckBox(QApplication.translate('Label','CHARGE'))
        self.autoCharge.setToolTip(QApplication.translate('Tooltip',
            'Auto detection of {}',
            'Auto detection of CHARGE').format(QApplication.translate('Label','CHARGE')))
        self.autoCharge.setChecked(self.aw.qmc.autoChargeFlag)
        self.autoCharge.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.chargeTimer = QCheckBox(QApplication.translate('CheckBox','{} Timer','CHARGE Timer').format(QApplication.translate('Label','CHARGE')))
        self.chargeTimer.setToolTip(QApplication.translate('Tooltip',
            'Countdown timer that sets {} after {}',
            'Countdown timer that sets CHARGE after START'
            ).format(QApplication.translate('Label','CHARGE'),QApplication.translate('Label','START')))
        self.chargeTimer.setChecked(self.aw.qmc.chargeTimerFlag)
        self.chargeTimer.stateChanged.connect(self.chargeTimerStateChanged)
        self.chargeTimer.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if self.app.artisanviewerMode:
            self.chargeTimer.setEnabled(False)
        self.chargeTimerSpinner = QSpinBox()
        self.chargeTimerSpinner.setEnabled(bool(self.aw.qmc.chargeTimerFlag))
        self.chargeTimerSpinner.setToolTip(QApplication.translate('Tooltip',
            'Countdown seconds from {} to {}',
            'Countdown seconds from START to CHARGE'
            ).format(QApplication.translate('Label','START'),QApplication.translate('Label','CHARGE')))
        self.chargeTimerSpinner.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.chargeTimerSpinner.setSingleStep(1)
        self.chargeTimerSpinner.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.chargeTimerSpinner.setRange(0,60)
        self.chargeTimerSpinner.setSuffix('s')
        self.chargeTimerSpinner.setValue(int(self.aw.qmc.chargeTimerPeriod))
        self.autoDrop = QCheckBox(QApplication.translate('Label','DROP'))
        self.autoDrop.setToolTip(QApplication.translate('Tooltip',
            'Auto detection of {}',
            'Auto detection of DROP').format(QApplication.translate('Label','DROP')))
        self.autoDrop.setChecked(self.aw.qmc.autoDropFlag)
        self.autoDrop.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.autoDrop.stateChanged.connect(self.autoDropStateChanged)

        autoEventModes = [QApplication.translate('ComboBox','Standard'), QApplication.translate('ComboBox','Sensitive')]
        self.autoChargeModeComboBox = QComboBox()
        self.autoChargeModeComboBox.setToolTip(QApplication.translate('Tooltip', 'Detection sensitivity'))
        self.autoChargeModeComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.autoChargeModeComboBox.addItems(autoEventModes)
        self.autoChargeModeComboBox.setCurrentIndex(self.aw.qmc.autoChargeMode)
        self.autoCharge.stateChanged.connect(self.autoChargeStateChanged)

        self.autoDropModeComboBox = QComboBox()
        self.autoDropModeComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.autoDropModeComboBox.addItems(autoEventModes)
        self.autoDropModeComboBox.setCurrentIndex(self.aw.qmc.autoDropMode)
        self.autoDropModeComboBox.setToolTip(QApplication.translate('Tooltip', 'Detection sensitivity'))

        self.markTP = QCheckBox(QApplication.translate('Label','TP'))
        self.markTP.setToolTip(QApplication.translate('Tooltip', 'Show marker at the turning point'))
        self.markTP.setChecked(self.aw.qmc.markTPflag)
        self.markTP.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        #show met
        self.ShowMet = QCheckBox(QApplication.translate('Label', 'MET'))
        self.ShowMet.setToolTip(QApplication.translate('Tooltip',
            'Show marker at Maximum {} between {} and {}',
            'Show marker at Maximum ET between TP and DROP'
            ).format(QApplication.translate('Label','ET'),QApplication.translate('Label','TP'),QApplication.translate('Label','DROP')))
        self.ShowMet.setChecked(self.aw.qmc.showmet)
        self.ShowMet.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.ShowMet.stateChanged.connect(self.changeShowMet)         #toggle
        self.ShowTimeguide = QCheckBox(QApplication.translate('CheckBox', 'Time Guide'))
        self.ShowTimeguide.setToolTip(QApplication.translate('Tooltip', 'During roast display a vertical line at the current time'))
        self.ShowTimeguide.setChecked(self.aw.qmc.showtimeguide)
        self.ShowTimeguide.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.ShowTimeguide.stateChanged.connect(self.changeShowTimeguide)

        if self.app.artisanviewerMode:
            self.autoCharge.setEnabled(False)
            self.autoDrop.setEnabled(False)
            self.autoChargeModeComboBox.setEnabled(False)
            self.autoDropModeComboBox.setEnabled(False)
            self.ShowTimeguide.setEnabled(False)

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.updatetypes)
        self.dialogbuttons.rejected.connect(self.restoreState)


        ###  TAB 2
        #number of buttons per row
        self.nbuttonslabel = QLabel(QApplication.translate('Label','Max Buttons Per Row'))
        self.nbuttonsSpinBox = QSpinBox()
        self.nbuttonsSpinBox.setMaximumWidth(100)
        self.nbuttonsSpinBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nbuttonsSpinBox.setRange(2,30)
        self.nbuttonsSpinBox.setValue(int(self.aw.buttonlistmaxlen))
        self.nbuttonsSpinBox.valueChanged.connect(self.setbuttonlistmaxlen)
        nbuttonsSizeLabel = QLabel(QApplication.translate('Label','Button Size'))
        self.nbuttonsSizeBox = MyQComboBox()
        size_items = [
                    QApplication.translate('ComboBox', 'tiny'),
                    QApplication.translate('ComboBox', 'small'),
                    QApplication.translate('ComboBox', 'large')
                ]
        self.nbuttonsSizeBox.addItems(size_items)
        self.nbuttonsSizeBox.setCurrentIndex(self.aw.buttonsize)
        self.markLastButtonPressed = QCheckBox(QApplication.translate('CheckBox','Mark Last Pressed'))
        self.markLastButtonPressed.setToolTip(QApplication.translate('Tooltip', 'Invert color of last button pressed'))
        self.markLastButtonPressed.setChecked(self.aw.mark_last_button_pressed)
        self.markLastButtonPressed.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.showExtraButtonTooltips = QCheckBox(QApplication.translate('CheckBox','Tooltips'))
        self.showExtraButtonTooltips.setToolTip(QApplication.translate('Tooltip', 'Show custom event button specification as button tooltip'))
        self.showExtraButtonTooltips.setChecked(self.aw.show_extrabutton_tooltips)
        self.showExtraButtonTooltips.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        #table for showing events
        self.eventbuttontable = QTableWidget()
        self.eventbuttontable.setTabKeyNavigation(True)
        self.eventbuttontable.itemSelectionChanged.connect(self.selectionChanged)
        vheader: Optional[QHeaderView] = self.eventbuttontable.verticalHeader()
        if vheader is not None:
            vheader.sectionMoved.connect(self.sectionMoved)
#        self.createEventbuttonTable()
        self.copyeventbuttonTableButton = QPushButton(QApplication.translate('Button', 'Copy Table'))
        self.copyeventbuttonTableButton.setToolTip(QApplication.translate('Tooltip','Copy table to clipboard, OPTION or ALT click for tabular text'))
        self.copyeventbuttonTableButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.copyeventbuttonTableButton.clicked.connect(self.copyEventButtonTabletoClipboard)
        addButton: Optional[QPushButton] = QPushButton(QApplication.translate('Button','Add'))
        if addButton is not None:
            addButton.setToolTip(QApplication.translate('Tooltip','Add new extra Event button'))
            #addButton.setMaximumWidth(100)
            addButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            addButton.clicked.connect(self.addextraeventbuttonSlot)
        delButton: Optional[QPushButton] = QPushButton(QApplication.translate('Button','Delete'))
        if delButton is not None:
            delButton.setToolTip(QApplication.translate('Tooltip','Delete the last extra Event button'))
            #delButton.setMaximumWidth(100)
            delButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            delButton.clicked.connect(self.delextraeventbutton)
        self.insertButton: Optional[QPushButton] = QPushButton(QApplication.translate('Button','Insert'))
        if self.insertButton is not None:
            self.insertButton.clicked.connect(self.insertextraeventbuttonSlot)
            self.insertButton.setMinimumWidth(80)
            self.insertButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.insertButton.setEnabled(False)
        helpDialogButton = QDialogButtonBox()
        helpButtonD: Optional[QPushButton] = helpDialogButton.addButton(QDialogButtonBox.StandardButton.Help)
        if helpButtonD is not None:
            helpButtonD.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            helpButtonD.setToolTip(QApplication.translate('Tooltip','Show help'))
            self.setButtonTranslations(helpButton,'Help',QApplication.translate('Button','Help'))
            helpButtonD.clicked.connect(self.showEventbuttonhelp)
        #color patterns
        #flag that prevents changing colors too fast
        self.changingcolorflag = False
        colorpatternlabel = QLabel(QApplication.translate('Label','Color Pattern'))
        self.colorSpinBox = QSpinBox()
        self.colorSpinBox.setWrapping(True)
        self.colorSpinBox.setMaximumWidth(100)
        self.colorSpinBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.colorSpinBox.setRange(0,359)
        self.colorSpinBox.valueChanged.connect(self.colorizebuttons)
        ## tab4
        transferpalettebutton = QPushButton(QApplication.translate('Button','<< Store Palette'))
        transferpalettebutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        setpalettebutton = QPushButton(QApplication.translate('Button','Activate Palette >>'))
        setpalettebutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        transferpalettecurrentLabel = QLabel(QApplication.translate('Label','current:'))
        self.transferpalettecurrentLabelEdit = QLineEdit(self.aw.buttonpalette_label)


        self.transferpalettecombobox = QComboBox()
        self.transferpalettecombobox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # next line needed to avoid truncation of entries on Mac OS X under Qt 5.12.1-5.12.3
        # https://bugreports.qt.io/browse/QTBUG-73653
        self.transferpalettecombobox.setMinimumWidth(120)
        self.updatePalettePopup()

        transferpalettebutton.clicked.connect(self.transferbuttonstoSlot)
        self.switchPaletteByNumberKey = QCheckBox(QApplication.translate('CheckBox','Switch Using Number Keys + Cmd'))
        self.switchPaletteByNumberKey.setChecked(self.aw.buttonpalette_shortcuts)
        self.switchPaletteByNumberKey.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        setpalettebutton.clicked.connect(self.setbuttonsfrom)
        backupbutton = QPushButton(QApplication.translate('Button','Save'))
        backupbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        restorebutton = QPushButton(QApplication.translate('Button','Load'))
        restorebutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        backupbutton.setToolTip(QApplication.translate('Tooltip','Backup all palettes to a text file'))
        restorebutton.setToolTip(QApplication.translate('Tooltip','Restore all palettes from a text file'))
        backupbutton.setMaximumWidth(140)
        restorebutton.setMaximumWidth(140)
        backupbutton.clicked.connect(self.backuppaletteeventbuttonsSlot)
        restorebutton.clicked.connect(self.restorepaletteeventbuttons)
        ## tab5
        eventtitlelabel = QLabel(QApplication.translate('Label','Event'))
        eventtitlelabel.setFont(titlefont)
        actiontitlelabel = QLabel(QApplication.translate('Label','Action'))
        actiontitlelabel.setFont(titlefont)
        commandtitlelabel = QLabel(QApplication.translate('Label','Command'))
        commandtitlelabel.setFont(titlefont)
        offsettitlelabel = QLabel(QApplication.translate('Label','Offset'))
        offsettitlelabel.setFont(titlefont)
        factortitlelabel = QLabel(QApplication.translate('Label','Factor'))
        factortitlelabel.setFont(titlefont)
        min_titlelabel = QLabel(QApplication.translate('Label','Min'))
        min_titlelabel.setFont(titlefont)
        max_titlelabel = QLabel(QApplication.translate('Label','Max'))
        max_titlelabel.setFont(titlefont)
        sliderBernoullititlelabel = QLabel(QApplication.translate('Label','Bernoulli'))
        sliderBernoullititlelabel.setFont(titlefont)
        slidercoarsetitlelabel = QLabel(QApplication.translate('Label','Step'))
        slidercoarsetitlelabel.setFont(titlefont)
        quantifieractiontitlelabel = QLabel(QApplication.translate('Label','Action'))
        quantifieractiontitlelabel.setFont(titlefont)
        quantifieractiontitlelabel.setToolTip(QApplication.translate('Tooltip','Triggered quantifier fires slider action'))
        quantifierSVtitlelabel = QLabel(QApplication.translate('Label','SV'))
        quantifierSVtitlelabel.setFont(titlefont)
        quantifierSVtitlelabel.setToolTip(QApplication.translate('Tooltip','No processing delay if source delivers the set value (SV) instead of the process value (PV)'))
        slidertemptitlelabel = QLabel(QApplication.translate('Label','Temp'))
        slidertemptitlelabel.setFont(titlefont)
        sliderunittitlelabel = QLabel(QApplication.translate('Label','Unit'))
        sliderunittitlelabel.setFont(titlefont)
        self.E1visibility = QCheckBox(self.aw.qmc.etypesf(0))
        self.E1visibility.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1visibility.setChecked(bool(self.aw.eventslidervisibilities[0]))
        self.E2visibility = QCheckBox(self.aw.qmc.etypesf(1))
        self.E2visibility.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2visibility.setChecked(bool(self.aw.eventslidervisibilities[1]))
        self.E3visibility = QCheckBox(self.aw.qmc.etypesf(2))
        self.E3visibility.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3visibility.setChecked(bool(self.aw.eventslidervisibilities[2]))
        self.E4visibility = QCheckBox(self.aw.qmc.etypesf(3))
        self.E4visibility.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4visibility.setChecked(bool(self.aw.eventslidervisibilities[3]))
        self.sliderActionTypes = ['',#QApplication.translate("ComboBox", "None"),
                       QApplication.translate('ComboBox', 'Serial Command'),
                       QApplication.translate('ComboBox', 'Modbus Command'),
                       QApplication.translate('ComboBox', 'DTA Command'),
                       QApplication.translate('ComboBox', 'Call Program'),
                       QApplication.translate('ComboBox', 'Hottop Heater'),
                       QApplication.translate('ComboBox', 'Hottop Fan'),
                       QApplication.translate('ComboBox', 'Hottop Command'),
                       QApplication.translate('ComboBox', 'Fuji Command'),
                       QApplication.translate('ComboBox', 'PWM Command'),
                       QApplication.translate('ComboBox', 'VOUT Command'),
                       QApplication.translate('ComboBox', 'IO Command'),
                       QApplication.translate('ComboBox', 'S7 Command'),
                       QApplication.translate('ComboBox', 'Aillio R1 Heater'),
                       QApplication.translate('ComboBox', 'Aillio R1 Fan'),
                       QApplication.translate('ComboBox', 'Aillio R1 Drum'),
                       QApplication.translate('ComboBox', 'Artisan Command'),
                       QApplication.translate('ComboBox', 'RC Command'),
                       QApplication.translate('ComboBox', 'WebSocket Command'),
                       QApplication.translate('ComboBox', 'Stepper Command')]
        self.sliderActionTypesSorted = sorted(self.sliderActionTypes)
        self.E1action = QComboBox()
        self.E1action.setToolTip(QApplication.translate('Tooltip', 'Action Type'))
        self.E1action.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1action.addItems(self.sliderActionTypesSorted)
        self.E1action.setCurrentIndex(self.sliderActionTypesSorted.index(self.sliderActionTypes[self.aw.eventslideractions[0]]))
        self.E2action = QComboBox()
        self.E2action.setToolTip(QApplication.translate('Tooltip', 'Action Type'))
        self.E2action.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2action.addItems(self.sliderActionTypesSorted)
        self.E2action.setCurrentIndex(self.sliderActionTypesSorted.index(self.sliderActionTypes[self.aw.eventslideractions[1]]))
        self.E3action = QComboBox()
        self.E3action.setToolTip(QApplication.translate('Tooltip', 'Action Type'))
        self.E3action.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3action.addItems(self.sliderActionTypesSorted)
        self.E3action.setCurrentIndex(self.sliderActionTypesSorted.index(self.sliderActionTypes[self.aw.eventslideractions[2]]))
        self.E4action = QComboBox()
        self.E4action.setToolTip(QApplication.translate('Tooltip', 'Action Type'))
        self.E4action.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4action.addItems(self.sliderActionTypesSorted)
        self.E4action.setCurrentIndex(self.sliderActionTypesSorted.index(self.sliderActionTypes[self.aw.eventslideractions[3]]))
        self.E1command = QLineEdit(self.aw.eventslidercommands[0])
        self.E2command = QLineEdit(self.aw.eventslidercommands[1])
        self.E3command = QLineEdit(self.aw.eventslidercommands[2])
        self.E4command = QLineEdit(self.aw.eventslidercommands[3])
        self.E1offset = MyQDoubleSpinBox()
        self.E1offset.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E1offset.setRange(-9999,9999)
        self.E1offset.setDecimals(2)
        self.E1offset.setValue(self.aw.eventslideroffsets[0])
        self.E2offset = MyQDoubleSpinBox()
        self.E2offset.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E2offset.setRange(-9999,9999)
        self.E2offset.setDecimals(2)
        self.E2offset.setValue(self.aw.eventslideroffsets[1])
        self.E3offset = MyQDoubleSpinBox()
        self.E3offset.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E3offset.setRange(-9999,9999)
        self.E3offset.setDecimals(2)
        self.E3offset.setValue(self.aw.eventslideroffsets[2])
        self.E4offset = MyQDoubleSpinBox()
        self.E4offset.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E4offset.setRange(-9999,9999)
        self.E4offset.setDecimals(2)
        self.E4offset.setValue(self.aw.eventslideroffsets[3])
        self.E1factor = MyQDoubleSpinBox()
        self.E1factor.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E1factor.setRange(-999,999)
        self.E1factor.setDecimals(4)
        self.E1factor.setValue(self.aw.eventsliderfactors[0])
        self.E1factor.setMaximumWidth(70)
        self.E2factor = MyQDoubleSpinBox()
        self.E2factor.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E2factor.setRange(-999,999)
        self.E2factor.setDecimals(4)
        self.E2factor.setValue(self.aw.eventsliderfactors[1])
        self.E2factor.setMaximumWidth(70)
        self.E3factor = MyQDoubleSpinBox()
        self.E3factor.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E3factor.setRange(-999,999)
        self.E3factor.setDecimals(4)
        self.E3factor.setValue(self.aw.eventsliderfactors[2])
        self.E3factor.setMaximumWidth(70)
        self.E4factor = MyQDoubleSpinBox()
        self.E4factor.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E4factor.setRange(-999,999)
        self.E4factor.setDecimals(4)
        self.E4factor.setValue(self.aw.eventsliderfactors[3])
        self.E4factor.setMaximumWidth(70)
        self.E1_min = QSpinBox()
        self.E1_min.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E1_min.setRange(0,self.aw.eventsMaxValue)
        self.E1_min.setValue(int(self.aw.eventslidermin[0]))
        self.E2_min = QSpinBox()
        self.E2_min.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E2_min.setRange(0,self.aw.eventsMaxValue)
        self.E2_min.setValue(int(self.aw.eventslidermin[1]))
        self.E3_min = QSpinBox()
        self.E3_min.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E3_min.setRange(0,self.aw.eventsMaxValue)
        self.E3_min.setValue(int(self.aw.eventslidermin[2]))
        self.E4_min = QSpinBox()
        self.E4_min.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E4_min.setRange(0,self.aw.eventsMaxValue)
        self.E4_min.setValue(int(self.aw.eventslidermin[3]))
        self.E1_max = QSpinBox()
        self.E1_max.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E1_max.setRange(0,self.aw.eventsMaxValue)
        self.E1_max.setValue(int(self.aw.eventslidermax[0]))
        self.E2_max = QSpinBox()
        self.E2_max.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E2_max.setRange(0,self.aw.eventsMaxValue)
        self.E2_max.setValue(int(self.aw.eventslidermax[1]))
        self.E3_max = QSpinBox()
        self.E3_max.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E3_max.setRange(0,self.aw.eventsMaxValue)
        self.E3_max.setValue(int(self.aw.eventslidermax[2]))
        self.E4_max = QSpinBox()
        self.E4_max.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E4_max.setRange(0,self.aw.eventsMaxValue)
        self.E4_max.setValue(int(self.aw.eventslidermax[3]))
        self.E1_calc = QToolButton()
        self.E1_calc.setText('...')
        self.E1_calc.setToolTip(QApplication.translate('Form Caption', 'Slider Calculator'))
        self.E1_calc.setAccessibleDescription('')
        self.E1_calc.clicked.connect(self.slider1ToolButton_triggered)
        self.E2_calc = QToolButton()
        self.E2_calc.setText('...')
        self.E2_calc.setToolTip(QApplication.translate('Form Caption', 'Slider Calculator'))
        self.E2_calc.clicked.connect(self.slider2ToolButton_triggered)
        self.E3_calc = QToolButton()
        self.E3_calc.setText('...')
        self.E3_calc.setToolTip(QApplication.translate('Form Caption', 'Slider Calculator'))
        self.E3_calc.clicked.connect(self.slider3ToolButton_triggered)
        self.E4_calc = QToolButton()
        self.E4_calc.setText('...')
        self.E4_calc.clicked.connect(self.slider4ToolButton_triggered)
        self.E4_calc.setToolTip(QApplication.translate('Form Caption', 'Slider Calculator'))

        # https://www.home-barista.com/home-roasting/coffee-roasting-best-practices-scott-rao-t65601-70.html#p724654
        bernoulli_tooltip_text = QApplication.translate('Tooltip', "Applies the Bernoulli's gas law to the values computed\nby applying the given factor and offset to the slider value\nassuming that the gas pressureand not the gas flow is controlled.\nTo reduce heat (or gas flow) by 50% the gas pressure\nhas to be reduced by 4 times.")
        self.E1slider_bernoulli = QCheckBox()
        self.E1slider_bernoulli.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1slider_bernoulli.setChecked(bool(self.aw.eventsliderBernoulli[0]))
        self.E1slider_bernoulli.setToolTip(bernoulli_tooltip_text)
        self.E2slider_bernoulli = QCheckBox()
        self.E2slider_bernoulli.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2slider_bernoulli.setChecked(bool(self.aw.eventsliderBernoulli[1]))
        self.E2slider_bernoulli.setToolTip(bernoulli_tooltip_text)
        self.E3slider_bernoulli = QCheckBox()
        self.E3slider_bernoulli.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3slider_bernoulli.setChecked(bool(self.aw.eventsliderBernoulli[2]))
        self.E3slider_bernoulli.setToolTip(bernoulli_tooltip_text)
        self.E4slider_bernoulli = QCheckBox()
        self.E4slider_bernoulli.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4slider_bernoulli.setChecked(bool(self.aw.eventsliderBernoulli[3]))
        self.E4slider_bernoulli.setToolTip(bernoulli_tooltip_text)

        self.sliderStepSizes:List[str] = ['1', '5', '10'] # corresponding to aw.eventslidercoarse values of 0, 2, and 1
        self.E1slider_step = QComboBox()
        self.E1slider_step.setToolTip(QApplication.translate('Tooltip', 'Step Size'))
        self.E1slider_step.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1slider_step.addItems(self.sliderStepSizes)
        self.E1slider_step.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventslidercoarse[0]))
        self.E2slider_step = QComboBox()
        self.E2slider_step.setToolTip(QApplication.translate('Tooltip', 'Step Size'))
        self.E2slider_step.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2slider_step.addItems(self.sliderStepSizes)
        self.E2slider_step.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventslidercoarse[1]))
        self.E3slider_step = QComboBox()
        self.E3slider_step.setToolTip(QApplication.translate('Tooltip', 'Step Size'))
        self.E3slider_step.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3slider_step.addItems(self.sliderStepSizes)
        self.E3slider_step.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventslidercoarse[2]))
        self.E4slider_step = QComboBox()
        self.E4slider_step.setToolTip(QApplication.translate('Tooltip', 'Step Size'))
        self.E4slider_step.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4slider_step.addItems(self.sliderStepSizes)
        self.E4slider_step.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventslidercoarse[3]))

        slider_temp_tooltip_text = QApplication.translate('Tooltip', 'Slider values interpreted as temperatures')
        self.E1slider_temp = QCheckBox()
        self.E1slider_temp.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1slider_temp.setChecked(bool(self.aw.eventslidertemp[0]))
        self.E1slider_temp.setToolTip(slider_temp_tooltip_text)
        self.E2slider_temp = QCheckBox()
        self.E2slider_temp.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2slider_temp.setChecked(bool(self.aw.eventslidertemp[1]))
        self.E2slider_temp.setToolTip(slider_temp_tooltip_text)
        self.E3slider_temp = QCheckBox()
        self.E3slider_temp.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3slider_temp.setChecked(bool(self.aw.eventslidertemp[2]))
        self.E3slider_temp.setToolTip(slider_temp_tooltip_text)
        self.E4slider_temp = QCheckBox()
        self.E4slider_temp.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4slider_temp.setChecked(bool(self.aw.eventslidertemp[3]))
        self.E4slider_temp.setToolTip(slider_temp_tooltip_text)
        maxwidth = 40
        slider_unit_tooltip_text = QApplication.translate('Tooltip', 'Unit to be added to generated event descriptions')
        self.E1unit = QLineEdit(self.aw.eventsliderunits[0])
        self.E1unit.setMaximumWidth(maxwidth)
        self.E1unit.setToolTip(slider_unit_tooltip_text)
        self.E2unit = QLineEdit(self.aw.eventsliderunits[1])
        self.E2unit.setMaximumWidth(maxwidth)
        self.E2unit.setToolTip(slider_unit_tooltip_text)
        self.E3unit = QLineEdit(self.aw.eventsliderunits[2])
        self.E3unit.setMaximumWidth(maxwidth)
        self.E3unit.setToolTip(slider_unit_tooltip_text)
        self.E4unit = QLineEdit(self.aw.eventsliderunits[3])
        self.E4unit.setMaximumWidth(maxwidth)
        self.E4unit.setToolTip(slider_unit_tooltip_text)
        helpsliderDialogButton = QDialogButtonBox()
        helpsliderbutton: Optional[QPushButton] = helpsliderDialogButton.addButton(QDialogButtonBox.StandardButton.Help)
        if helpsliderbutton is not None:
            helpsliderbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.setButtonTranslations(helpsliderbutton,'Help',QApplication.translate('Button','Help'))
            helpsliderbutton.clicked.connect(self.showSliderHelp)
        self.sliderKeyboardControlflag = QCheckBox(QApplication.translate('CheckBox','Keyboard Control'))
        self.sliderKeyboardControlflag.setToolTip(QApplication.translate('Tooltip', 'Move slider under focus using the up/down cursor keys'))
        self.sliderKeyboardControlflag.setChecked(self.aw.eventsliderKeyboardControl)
        self.sliderAlternativeLayoutFlag = QCheckBox(QApplication.translate('CheckBox','Alternative Layout'))
        self.sliderAlternativeLayoutFlag.setToolTip(QApplication.translate('Tooltip', 'Group Slider 1 with Slider 4 and Slider 2 with Slider 3'))
        self.sliderAlternativeLayoutFlag.setChecked(self.aw.eventsliderAlternativeLayout)
        ## tab4
        qeventtitlelabel = QLabel(QApplication.translate('Label','Event'))
        qeventtitlelabel.setFont(titlefont)
        sourcetitlelabel = QLabel(QApplication.translate('Label','Source'))
        sourcetitlelabel.setFont(titlefont)
        mintitlelabel = QLabel(QApplication.translate('Label','Min'))
        mintitlelabel.setFont(titlefont)
        maxtitlelabel = QLabel(QApplication.translate('Label','Max'))
        maxtitlelabel.setFont(titlefont)
        coarsetitlelabel = QLabel(QApplication.translate('Label','Step'))
        coarsetitlelabel.setFont(titlefont)
        self.E1active = QCheckBox(self.aw.qmc.etypesf(0))
        self.E1active.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1active.setChecked(bool(self.aw.eventquantifieractive[0]))
        self.E2active = QCheckBox(self.aw.qmc.etypesf(1))
        self.E2active.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2active.setChecked(bool(self.aw.eventquantifieractive[1]))
        self.E3active = QCheckBox(self.aw.qmc.etypesf(2))
        self.E3active.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3active.setChecked(bool(self.aw.eventquantifieractive[2]))
        self.E4active = QCheckBox(self.aw.qmc.etypesf(3))
        self.E4active.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4active.setChecked(bool(self.aw.eventquantifieractive[3]))

        self.E1coarse = QComboBox()
        self.E1coarse.setToolTip(QApplication.translate('Tooltip', 'Step Size'))
        self.E1coarse.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1coarse.addItems(self.sliderStepSizes)
        self.E1coarse.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventquantifiercoarse[0]))
        self.E2coarse = QComboBox()
        self.E2coarse.setToolTip(QApplication.translate('Tooltip', 'Step Size'))
        self.E2coarse.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2coarse.addItems(self.sliderStepSizes)
        self.E2coarse.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventquantifiercoarse[1]))
        self.E3coarse = QComboBox()
        self.E3coarse.setToolTip(QApplication.translate('Tooltip', 'Step Size'))
        self.E3coarse.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3coarse.addItems(self.sliderStepSizes)
        self.E3coarse.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventquantifiercoarse[2]))
        self.E4coarse = QComboBox()
        self.E4coarse.setToolTip(QApplication.translate('Tooltip', 'Step Size'))
        self.E4coarse.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4coarse.addItems(self.sliderStepSizes)
        self.E4coarse.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventquantifiercoarse[3]))
        self.E1quantifieraction = QCheckBox()
        self.E1quantifieraction.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1quantifieraction.setChecked(bool(self.aw.eventquantifieraction[0]))
        self.E1quantifieraction.setToolTip(QApplication.translate('Tooltip', 'fire slider action'))
        self.E2quantifieraction = QCheckBox()
        self.E2quantifieraction.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2quantifieraction.setChecked(bool(self.aw.eventquantifieraction[1]))
        self.E2quantifieraction.setToolTip(QApplication.translate('Tooltip', 'fire slider action'))
        self.E3quantifieraction = QCheckBox()
        self.E3quantifieraction.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3quantifieraction.setChecked(bool(self.aw.eventquantifieraction[2]))
        self.E3quantifieraction.setToolTip(QApplication.translate('Tooltip', 'fire slider action'))
        self.E4quantifieraction = QCheckBox()
        self.E4quantifieraction.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4quantifieraction.setChecked(bool(self.aw.eventquantifieraction[3]))
        self.E4quantifieraction.setToolTip(QApplication.translate('Tooltip', 'fire slider action'))
        self.E1quantifierSV = QCheckBox()
        self.E1quantifierSV.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E1quantifierSV.setChecked(bool(self.aw.eventquantifierSV[0]))
        self.E1quantifierSV.setToolTip(QApplication.translate('Tooltip', 'If source is a Set Value quantification gets never blocked'))
        self.E2quantifierSV = QCheckBox()
        self.E2quantifierSV.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E2quantifierSV.setChecked(bool(self.aw.eventquantifierSV[1]))
        self.E2quantifierSV.setToolTip(QApplication.translate('Tooltip', 'If source is a Set Value quantification gets never blocked'))
        self.E3quantifierSV = QCheckBox()
        self.E3quantifierSV.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E3quantifierSV.setChecked(bool(self.aw.eventquantifierSV[2]))
        self.E3quantifierSV.setToolTip(QApplication.translate('Tooltip', 'If source is a Set Value quantification gets never blocked'))
        self.E4quantifierSV = QCheckBox()
        self.E4quantifierSV.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.E4quantifierSV.setChecked(bool(self.aw.eventquantifierSV[3]))
        self.E4quantifierSV.setToolTip(QApplication.translate('Tooltip', 'If source is a Set Value quantification gets never blocked'))

        self.curvenames = []
        self.curvenames.append(QApplication.translate('ComboBox','ET'))
        self.curvenames.append(QApplication.translate('ComboBox','BT'))
        for i in range(len(self.aw.qmc.extradevices)):
            self.curvenames.append(self.aw.qmc.extraname1[i].format(self.etype0.text(),self.etype1.text(),self.etype2.text(),self.etype3.text()))
            self.curvenames.append(self.aw.qmc.extraname2[i].format(self.etype0.text(),self.etype1.text(),self.etype2.text(),self.etype3.text()))
        self.E1SourceComboBox = QComboBox()
        self.E1SourceComboBox.addItems(self.curvenames)
        if self.aw.eventquantifiersource[0] < len(self.curvenames):
            self.E1SourceComboBox.setCurrentIndex(self.aw.eventquantifiersource[0])
        self.E2SourceComboBox = QComboBox()
        self.E2SourceComboBox.addItems(self.curvenames)
        if self.aw.eventquantifiersource[1] < len(self.curvenames):
            self.E2SourceComboBox.setCurrentIndex(self.aw.eventquantifiersource[1])
        self.E3SourceComboBox = QComboBox()
        self.E3SourceComboBox.addItems(self.curvenames)
        if self.aw.eventquantifiersource[2] < len(self.curvenames):
            self.E3SourceComboBox.setCurrentIndex(self.aw.eventquantifiersource[2])
        self.E4SourceComboBox = QComboBox()
        self.E4SourceComboBox.addItems(self.curvenames)
        if self.aw.eventquantifiersource[3] < len(self.curvenames):
            self.E4SourceComboBox.setCurrentIndex(self.aw.eventquantifiersource[3])
        self.E1min = QSpinBox()
        self.E1min.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E1min.setRange(-99999,99999)
        self.E1min.setValue(self.aw.eventquantifiermin[0])
        self.E2min = QSpinBox()
        self.E2min.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E2min.setRange(-99999,99999)
        self.E2min.setValue(self.aw.eventquantifiermin[1])
        self.E3min = QSpinBox()
        self.E3min.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E3min.setRange(-99999,99999)
        self.E3min.setValue(self.aw.eventquantifiermin[2])
        self.E4min = QSpinBox()
        self.E4min.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E4min.setRange(-99999,99999)
        self.E4min.setValue(self.aw.eventquantifiermin[3])
        self.E1max = QSpinBox()
        self.E1max.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E1max.setRange(-99999,99999)
        self.E1max.setValue(self.aw.eventquantifiermax[0])
        self.E2max = QSpinBox()
        self.E2max.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E2max.setRange(-99999,99999)
        self.E2max.setValue(self.aw.eventquantifiermax[1])
        self.E3max = QSpinBox()
        self.E3max.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E3max.setRange(-99999,99999)
        self.E3max.setValue(self.aw.eventquantifiermax[2])
        self.E4max = QSpinBox()
        self.E4max.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.E4max.setRange(-99999,99999)
        self.E4max.setValue(self.aw.eventquantifiermax[3])
        applyDialogButton = QDialogButtonBox()
        applyquantifierbutton: Optional[QPushButton] = applyDialogButton.addButton(QDialogButtonBox.StandardButton.Apply)
        if applyquantifierbutton is not None:
            self.setButtonTranslations(applyquantifierbutton,'Apply',QApplication.translate('Button','Apply'))
            applyquantifierbutton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            applyquantifierbutton.clicked.connect(self.applyQuantifiers)
        self.clusterEventsFlag = QCheckBox(QApplication.translate('Label','Cluster'))
        self.clusterEventsFlag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.clusterEventsFlag.setChecked(bool(self.aw.clusterEventsFlag))
        ### LAYOUTS
        #### tab1 layout
        bartypeLayout = QHBoxLayout()
        bartypeLayout.addWidget(barstylelabel)
        bartypeLayout.addWidget(self.bartypeComboBox,Qt.AlignmentFlag.AlignLeft)
        FlagsLayout = QHBoxLayout()
        FlagsLayout.addStretch()
        FlagsLayout.addWidget(self.eventsbuttonflag)
        FlagsLayout.addSpacing(5)
        FlagsLayout.addWidget(self.showeventsonbtbox)
        FlagsLayout.addSpacing(5)
        FlagsLayout.addWidget(self.annotationsflagbox)
        FlagsLayout.addSpacing(5)
        FlagsLayout.addWidget(self.ShowTimeguide)
        FlagsLayout.addStretch()
        FlagsLayout.addLayout(bartypeLayout)
        FlagsLayout.addSpacing(10)
        FlagsLayout.addWidget(self.eventsclampflag)
        FlagsLayout.addSpacing(5)
        FlagsLayout.addWidget(self.eventslabelsflag)
        FlagsLayout.addSpacing(3)
        FlagsLayout.addWidget(self.eventslabelscharsSpinner)
        FlagsLayout.addStretch()

        AutoMarkGroupBox = QGroupBox(QApplication.translate('GroupBox','Automatic Marking'))
#        AutoMarkGroupBox.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)
        AutoMarkHBox = QHBoxLayout()
        AutoMarkHBox.addWidget(self.chargeTimer)
        AutoMarkHBox.addSpacing(3)
        AutoMarkHBox.addWidget(self.chargeTimerSpinner)
        AutoMarkHBox.addSpacing(30)
        AutoMarkGroupBox.setLayout(AutoMarkHBox)
        AutoMarkHBox.addWidget(self.autoCharge)
        AutoMarkHBox.addSpacing(3)
        AutoMarkHBox.addWidget(self.autoChargeModeComboBox)
        AutoMarkHBox.addSpacing(30)
        AutoMarkHBox.addWidget(self.autoDrop)
        AutoMarkHBox.addSpacing(3)
        AutoMarkHBox.addWidget(self.autoDropModeComboBox)
        AutoMarkHBox.addSpacing(30)
        AutoMarkHBox.addWidget(self.markTP)
        AutoMarkHBox.addSpacing(30)
        AutoMarkHBox.addWidget(self.ShowMet)
        AutoMarkHBox.setContentsMargins(5,0,5,0) # l,t,r,b
        AutoMarkHBox.setSpacing(7)

        FlagsLayout2 = QHBoxLayout()
        FlagsLayout2.addWidget(AutoMarkGroupBox)
        FlagsLayout2.addStretch()

        typeLayout = QGridLayout()
        typeLayout.addWidget(typelabel1,0,0)
        typeLayout.addWidget(self.showEtype1,0,1)
        typeLayout.addWidget(self.etype0,0,2)
        typeLayout.addWidget(typelabel2,0,3)
        typeLayout.addWidget(self.showEtype2,0,4)
        typeLayout.addWidget(self.etype1,0,5)
        typeLayout.addWidget(typelabel3,0,6)
        typeLayout.addWidget(self.showEtype3,0,7)
        typeLayout.addWidget(self.etype2,0,8)
        typeLayout.addWidget(typelabel4,0,9)
        typeLayout.addWidget(self.showEtype4,0,10)
        typeLayout.addWidget(self.etype3,0,11)
        typeLayout.addWidget(typelabel5,0,12)
        typeLayout.addWidget(self.showEtype5,0,13)
        typeLayout.addWidget(self.etype4,0,14)

        dialogButtonsLayout = QVBoxLayout()
        dialogButtonsLayout.addWidget(self.dialogbuttons)
        dialogButtonsLayout.addSpacing(15)
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addLayout(dialogButtonsLayout)
        buttonLayout.addSpacing(10)
        buttonLayout.setContentsMargins(0,0,0,0)
        buttonLayout.setSpacing(0)
        typeHBox = QHBoxLayout()
        typeHBox.addLayout(typeLayout)
        typeHBox.addStretch()
        typeHBox.setContentsMargins(5,0,5,0) # l,t,r,b
        TypeGroupLayout = QGroupBox(QApplication.translate('GroupBox','Event Types'))
        TypeGroupLayout.setLayout(typeHBox)
        self.buttonActionTypes = ['',#QApplication.translate("ComboBox", "None"),
                       QApplication.translate('ComboBox', 'Serial Command'),
                       QApplication.translate('ComboBox', 'Call Program'),
                       QApplication.translate('ComboBox', 'Modbus Command'),
                       QApplication.translate('ComboBox', 'DTA Command'),
                       QApplication.translate('ComboBox', 'IO Command'),
                       QApplication.translate('ComboBox', 'Hottop Heater'),
                       QApplication.translate('ComboBox', 'Hottop Fan'),
                       QApplication.translate('ComboBox', 'Hottop Command'),
                       QApplication.translate('ComboBox', 'p-i-d'),
                       QApplication.translate('ComboBox', 'Fuji Command'),
                       QApplication.translate('ComboBox', 'PWM Command'),
                       QApplication.translate('ComboBox', 'VOUT Command'),
                       QApplication.translate('ComboBox', 'S7 Command'),
                       QApplication.translate('ComboBox', 'Aillio R1 Heater'),
                       QApplication.translate('ComboBox', 'Aillio R1 Fan'),
                       QApplication.translate('ComboBox', 'Aillio R1 Drum'),
                       QApplication.translate('ComboBox', 'Aillio R1 Command'),
                       QApplication.translate('ComboBox', 'Artisan Command'),
                       QApplication.translate('ComboBox', 'RC Command'),
                       QApplication.translate('ComboBox', 'Multiple Event'),
                       QApplication.translate('ComboBox', 'WebSocket Command')]
        self.buttonActionTypesSorted = sorted(self.buttonActionTypes)
        self.CHARGEbutton = QCheckBox(QApplication.translate('CheckBox', 'CHARGE'))
        self.CHARGEbutton.setChecked(bool(self.aw.qmc.buttonvisibility[0]))
        self.CHARGEbutton.setToolTip(QApplication.translate('Tooltip', 'Display the button during roast'))
        self.CHARGEbuttonActionType = QComboBox()
        self.CHARGEbuttonActionType.setToolTip(QApplication.translate('Tooltip', 'Action type to fire when the button is clicked'))
        self.CHARGEbuttonActionType.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.CHARGEbuttonActionType.addItems(self.buttonActionTypesSorted)
        self.CHARGEbuttonActionType.setCurrentIndex(self.buttonActionTypesSorted.index(self.buttonActionTypes[self.aw.qmc.buttonactions[0]]))
        self.CHARGEbuttonActionString = QLineEdit(self.aw.qmc.buttonactionstrings[0])
        self.CHARGEbuttonActionString.setToolTip(QApplication.translate('Tooltip', 'Event action command'))
        self.DRYbutton = QCheckBox(QApplication.translate('CheckBox', 'DRY END'))
        self.DRYbutton.setToolTip(QApplication.translate('Tooltip', 'Display the button during roast'))
        self.DRYbutton.setChecked(bool(self.aw.qmc.buttonvisibility[1]))
        self.DRYbuttonActionType = QComboBox()
        self.DRYbuttonActionType.setToolTip(QApplication.translate('Tooltip', 'Action type to fire when the button is clicked'))
        self.DRYbuttonActionType.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.DRYbuttonActionType.addItems(self.buttonActionTypesSorted)
        self.DRYbuttonActionType.setCurrentIndex(self.buttonActionTypesSorted.index(self.buttonActionTypes[self.aw.qmc.buttonactions[1]]))
        self.DRYbuttonActionString = QLineEdit(self.aw.qmc.buttonactionstrings[1])
        self.DRYbuttonActionString.setToolTip(QApplication.translate('Tooltip', 'Event action command'))
        self.FCSbutton = QCheckBox(QApplication.translate('CheckBox', 'FC START'))
        self.FCSbutton.setChecked(bool(self.aw.qmc.buttonvisibility[2]))
        self.FCSbutton.setToolTip(QApplication.translate('Tooltip', 'Display the button during roast'))
        self.FCSbuttonActionType = QComboBox()
        self.FCSbuttonActionType.setToolTip(QApplication.translate('Tooltip', 'Action type to fire when the button is clicked'))
        self.FCSbuttonActionType.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.FCSbuttonActionType.addItems(self.buttonActionTypesSorted)
        self.FCSbuttonActionType.setCurrentIndex(self.buttonActionTypesSorted.index(self.buttonActionTypes[self.aw.qmc.buttonactions[2]]))
        self.FCSbuttonActionString = QLineEdit(self.aw.qmc.buttonactionstrings[2])
        self.FCSbuttonActionString.setToolTip(QApplication.translate('Tooltip', 'Event action command'))
        self.FCEbutton = QCheckBox(QApplication.translate('CheckBox', 'FC END'))
        self.FCEbutton.setChecked(bool(self.aw.qmc.buttonvisibility[3]))
        self.FCEbutton.setToolTip(QApplication.translate('Tooltip', 'Display the button during roast'))
        self.FCEbuttonActionType = QComboBox()
        self.FCEbuttonActionType.setToolTip(QApplication.translate('Tooltip', 'Action type to fire when the button is clicked'))
        self.FCEbuttonActionType.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.FCEbuttonActionType.addItems(self.buttonActionTypesSorted)
        self.FCEbuttonActionType.setCurrentIndex(self.buttonActionTypesSorted.index(self.buttonActionTypes[self.aw.qmc.buttonactions[3]]))
        self.FCEbuttonActionString = QLineEdit(self.aw.qmc.buttonactionstrings[3])
        self.FCEbuttonActionString.setToolTip(QApplication.translate('Tooltip', 'Event action command'))
        self.SCSbutton = QCheckBox(QApplication.translate('CheckBox', 'SC START'))
        self.SCSbutton.setChecked(bool(self.aw.qmc.buttonvisibility[4]))
        self.SCSbutton.setToolTip(QApplication.translate('Tooltip', 'Display the button during roast'))
        self.SCSbuttonActionType = QComboBox()
        self.SCSbuttonActionType.setToolTip(QApplication.translate('Tooltip', 'Action type to fire when the button is clicked'))
        self.SCSbuttonActionType.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.SCSbuttonActionType.addItems(self.buttonActionTypesSorted)
        self.SCSbuttonActionType.setCurrentIndex(self.buttonActionTypesSorted.index(self.buttonActionTypes[self.aw.qmc.buttonactions[4]]))
        self.SCSbuttonActionString = QLineEdit(self.aw.qmc.buttonactionstrings[4])
        self.SCSbuttonActionString.setToolTip(QApplication.translate('Tooltip', 'Event action command'))
        self.SCEbutton = QCheckBox(QApplication.translate('CheckBox', 'SC END'))
        self.SCEbutton.setChecked(bool(self.aw.qmc.buttonvisibility[5]))
        self.SCEbutton.setToolTip(QApplication.translate('Tooltip', 'Display the button during roast'))
        self.SCEbuttonActionType = QComboBox()
        self.SCEbuttonActionType.setToolTip(QApplication.translate('Tooltip', 'Action type to fire when the button is clicked'))
        self.SCEbuttonActionType.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.SCEbuttonActionType.addItems(self.buttonActionTypesSorted)
        self.SCEbuttonActionType.setCurrentIndex(self.buttonActionTypesSorted.index(self.buttonActionTypes[self.aw.qmc.buttonactions[5]]))
        self.SCEbuttonActionString = QLineEdit(self.aw.qmc.buttonactionstrings[5])
        self.SCEbuttonActionString.setToolTip(QApplication.translate('Tooltip', 'Event action command'))
        self.DROPbutton = QCheckBox(QApplication.translate('CheckBox', 'DROP'))
        self.DROPbutton.setChecked(bool(self.aw.qmc.buttonvisibility[6]))
        self.DROPbutton.setToolTip(QApplication.translate('Tooltip', 'Display the button during roast'))
        self.DROPbuttonActionType = QComboBox()
        self.DROPbuttonActionType.setToolTip(QApplication.translate('Tooltip', 'Action type to fire when the button is clicked'))
        self.DROPbuttonActionType.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.DROPbuttonActionType.addItems(self.buttonActionTypesSorted)
        self.DROPbuttonActionType.setCurrentIndex(self.buttonActionTypesSorted.index(self.buttonActionTypes[self.aw.qmc.buttonactions[6]]))
        self.DROPbuttonActionString = QLineEdit(self.aw.qmc.buttonactionstrings[6])
        self.DROPbuttonActionString.setToolTip(QApplication.translate('Tooltip', 'Event action command'))
        self.COOLbutton = QCheckBox(QApplication.translate('CheckBox', 'COOL END'))
        self.COOLbutton.setChecked(bool(self.aw.qmc.buttonvisibility[7]))
        self.COOLbutton.setToolTip(QApplication.translate('Tooltip', 'Display the button during roast'))
        self.COOLbuttonActionType = QComboBox()
        self.COOLbuttonActionType.setToolTip(QApplication.translate('Tooltip', 'Action type to fire when the button is clicked'))
        self.COOLbuttonActionType.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.COOLbuttonActionType.addItems(self.buttonActionTypesSorted)
        self.COOLbuttonActionType.setCurrentIndex(self.buttonActionTypesSorted.index(self.buttonActionTypes[self.aw.qmc.buttonactions[7]]))
        self.COOLbuttonActionString = QLineEdit(self.aw.qmc.buttonactionstrings[7])
        self.COOLbuttonActionString.setToolTip(QApplication.translate('Tooltip', 'Event action command'))
        self.ONbuttonLabel = QLabel(QApplication.translate('Label', 'ON'))
        self.ONbuttonActionType = QComboBox()
        self.ONbuttonActionType.setToolTip(QApplication.translate('Tooltip', 'Action type to fire when the button is clicked'))
        self.ONbuttonActionType.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.ONbuttonActionType.addItems(self.buttonActionTypesSorted)
        self.ONbuttonActionType.setCurrentIndex(self.buttonActionTypesSorted.index(self.buttonActionTypes[self.aw.qmc.extrabuttonactions[0]]))
        self.ONbuttonActionString = QLineEdit(self.aw.qmc.extrabuttonactionstrings[0])
        self.ONbuttonActionString.setToolTip(QApplication.translate('Tooltip', 'Event action command'))
        self.OFFbuttonActionType = QComboBox()
        self.OFFbuttonActionType.setToolTip(QApplication.translate('Tooltip', 'Action type to fire when the button is clicked'))
        self.OFFbuttonActionType.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.OFFbuttonActionType.addItems(self.buttonActionTypesSorted)
        self.OFFbuttonActionType.setCurrentIndex(self.buttonActionTypesSorted.index(self.buttonActionTypes[self.aw.qmc.extrabuttonactions[1]]))
        self.OFFbuttonActionString = QLineEdit(self.aw.qmc.extrabuttonactionstrings[1])
        self.OFFbuttonActionString.setToolTip(QApplication.translate('Tooltip', 'Event action command'))
        self.OFFbuttonLabel = QLabel(QApplication.translate('Label', 'OFF'))
        self.SAMPLINGbuttonActionType = QComboBox()
        self.SAMPLINGbuttonActionType.setToolTip(QApplication.translate('Tooltip', 'Sampling action type'))
        self.SAMPLINGbuttonActionType.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.SAMPLINGbuttonActionType.addItems(self.buttonActionTypesSorted)
        self.SAMPLINGbuttonActionType.setCurrentIndex(self.buttonActionTypesSorted.index(self.buttonActionTypes[self.aw.qmc.extrabuttonactions[2]]))
        self.SAMPLINGbuttonActionType.currentIndexChanged.connect(self.SAMPLINGbuttonActionTypeChanged)
        self.SAMPLINGbuttonActionType.setMinimumContentsLength(3)
        self.SAMPLINGbuttonActionType.setMinimumWidth(self.SAMPLINGbuttonActionType.minimumSizeHint().width())
        self.SAMPLINGbuttonActionString = QLineEdit(self.aw.qmc.extrabuttonactionstrings[2])
        self.SAMPLINGbuttonActionString.setToolTip(QApplication.translate('Tooltip', 'Sampling action command'))
        self.SAMPLINGbuttonActionInterval = QComboBox()
        self.SAMPLINGbuttonActionInterval.setToolTip(QApplication.translate('Tooltip', 'Run the sampling action synchronously ({}) every sampling interval or select a repating time interval to run it asynchronously while sampling').format('sync'))
        self.SAMPLINGbuttonActionInterval.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        buttonActionIntervals = ['sync', '1.0s', '1.5s', '2.0s', '2.5s', '3.0s', '3.5s', '4.0s', '4.5s', '5.0s', '10s', '20s', '30s', '45s', '1min']
        self.sampling_delays = [0,1000,1500,2000,2500,3000,3500,4000,4500,5000,10000,20000,30000,45000,60000]
        self.SAMPLINGbuttonActionInterval.addItems(buttonActionIntervals)
        self.SAMPLINGbuttonActionInterval.setMaximumWidth(70)
        try:
            self.SAMPLINGbuttonActionInterval.setCurrentIndex(self.sampling_delays.index(self.aw.qmc.extra_event_sampling_delay))
        except Exception: # pylint: disable=broad-except
            pass
        self.SAMPLINGbuttonActionInterval.setEnabled(bool(self.SAMPLINGbuttonActionType.currentIndex()))
        self.RESETbuttonLabel = QLabel(QApplication.translate('Label', 'RESET'))
        self.RESETbuttonActionType = QComboBox()
        self.RESETbuttonActionType.setToolTip(QApplication.translate('Tooltip', 'Action type to fire when the button is clicked'))
        self.RESETbuttonActionType.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.RESETbuttonActionType.addItems(self.buttonActionTypesSorted)
        self.RESETbuttonActionType.setCurrentIndex(self.buttonActionTypesSorted.index(self.buttonActionTypes[self.aw.qmc.xextrabuttonactions[0]]))
        self.RESETbuttonActionString = QLineEdit(self.aw.qmc.xextrabuttonactionstrings[0])
        self.RESETbuttonActionString.setToolTip(QApplication.translate('Tooltip', 'Event action command'))
        self.STARTbuttonLabel = QLabel(QApplication.translate('Label', 'START'))
        self.STARTbuttonActionType = QComboBox()
        self.STARTbuttonActionType.setToolTip(QApplication.translate('Tooltip', 'Action type to fire when the button is clicked'))
        self.STARTbuttonActionType.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.STARTbuttonActionType.addItems(self.buttonActionTypesSorted)
        self.STARTbuttonActionType.setCurrentIndex(self.buttonActionTypesSorted.index(self.buttonActionTypes[self.aw.qmc.xextrabuttonactions[1]]))
        self.STARTbuttonActionString = QLineEdit(self.aw.qmc.xextrabuttonactionstrings[1])
        self.STARTbuttonActionString.setToolTip(QApplication.translate('Tooltip', 'Event action command'))
        defaultButtonsLayout = QGridLayout()
        defaultButtonsLayout.addWidget(self.RESETbuttonLabel,0,0,Qt.AlignmentFlag.AlignRight)
        defaultButtonsLayout.addWidget(self.RESETbuttonActionType,0,1)
        defaultButtonsLayout.addWidget(self.RESETbuttonActionString,0,2)
        defaultButtonsLayout.addWidget(self.ONbuttonLabel,1,0,Qt.AlignmentFlag.AlignRight)
        defaultButtonsLayout.addWidget(self.ONbuttonActionType,1,1)
        defaultButtonsLayout.addWidget(self.ONbuttonActionString,1,2)
        defaultButtonsLayout.addWidget(self.OFFbuttonLabel,2,0,Qt.AlignmentFlag.AlignRight)
        defaultButtonsLayout.addWidget(self.OFFbuttonActionType,2,1)
        defaultButtonsLayout.addWidget(self.OFFbuttonActionString,2,2)
        defaultButtonsLayout.addWidget(self.STARTbuttonLabel,3,0,Qt.AlignmentFlag.AlignRight)
        defaultButtonsLayout.addWidget(self.STARTbuttonActionType,3,1)
        defaultButtonsLayout.addWidget(self.STARTbuttonActionString,3,2)
        defaultButtonsLayout.addWidget(self.CHARGEbutton,4,0)
        defaultButtonsLayout.addWidget(self.CHARGEbuttonActionType,4,1)
        defaultButtonsLayout.addWidget(self.CHARGEbuttonActionString,4,2)
        defaultButtonsLayout.addWidget(self.DRYbutton,5,0)
        defaultButtonsLayout.addWidget(self.DRYbuttonActionType,5,1)
        defaultButtonsLayout.addWidget(self.DRYbuttonActionString,5,2)
        defaultButtonsLayout.addWidget(self.FCSbutton,0,4)
        defaultButtonsLayout.addWidget(self.FCSbuttonActionType,0,5)
        defaultButtonsLayout.addWidget(self.FCSbuttonActionString,0,6)
        defaultButtonsLayout.addWidget(self.FCEbutton,1,4)
        defaultButtonsLayout.addWidget(self.FCEbuttonActionType,1,5)
        defaultButtonsLayout.addWidget(self.FCEbuttonActionString,1,6)
        defaultButtonsLayout.addWidget(self.SCSbutton,2,4)
        defaultButtonsLayout.addWidget(self.SCSbuttonActionType,2,5)
        defaultButtonsLayout.addWidget(self.SCSbuttonActionString,2,6)
        defaultButtonsLayout.addWidget(self.SCEbutton,3,4)
        defaultButtonsLayout.addWidget(self.SCEbuttonActionType,3,5)
        defaultButtonsLayout.addWidget(self.SCEbuttonActionString,3,6)
        defaultButtonsLayout.addWidget(self.DROPbutton,4,4)
        defaultButtonsLayout.addWidget(self.DROPbuttonActionType,4,5)
        defaultButtonsLayout.addWidget(self.DROPbuttonActionString,4,6)
        defaultButtonsLayout.addWidget(self.COOLbutton,5,4)
        defaultButtonsLayout.addWidget(self.COOLbuttonActionType,5,5)
        defaultButtonsLayout.addWidget(self.COOLbuttonActionString,5,6)
        defaultButtonsLayout.setContentsMargins(5,5,5,5)
        defaultButtonsLayout.setHorizontalSpacing(10)
        defaultButtonsLayout.setVerticalSpacing(5)
        defaultButtonsLayout.setColumnMinimumWidth(3,20)
        ButtonGroupLayout = QGroupBox(QApplication.translate('GroupBox','Default Buttons'))
        ButtonGroupLayout.setLayout(defaultButtonsLayout)
        if self.app.artisanviewerMode:
            ButtonGroupLayout.setEnabled(False)

        samplingLayout = QHBoxLayout()
        samplingLayout.addStretch()
        samplingLayout.addWidget(self.SAMPLINGbuttonActionType)
        samplingLayout.addWidget(self.SAMPLINGbuttonActionString)
        samplingLayout.addWidget(self.SAMPLINGbuttonActionInterval)
        samplingLayout.addStretch()
        samplingLayout.setContentsMargins(5,0,5,0) # l,t,r,b
        SamplingGroupLayout = QGroupBox(QApplication.translate('GroupBox','Sampling'))
        SamplingGroupLayout.setLayout(samplingLayout)
        if self.app.artisanviewerMode:
            SamplingGroupLayout.setEnabled(False)
        topLineLayout = QHBoxLayout()
        topLineLayout.addWidget(TypeGroupLayout)
        topLineLayout.setSpacing(5)
        topLineLayout.addStretch()
        topLineLayout.setSpacing(5)
        topLineLayout.addWidget(SamplingGroupLayout)
        tab1layout = QVBoxLayout()
        tab1layout.addLayout(FlagsLayout)
        tab1layout.addLayout(topLineLayout)
        tab1layout.addWidget(ButtonGroupLayout)
        tab1layout.addLayout(FlagsLayout2)
        tab1layout.addStretch()
        FlagsLayout.setContentsMargins(0,10,0,0)
        FlagsLayout.setSpacing(10)
        topLineLayout.setContentsMargins(0,0,0,0)
        tab1layout.setSpacing(2)
        tab1layout.setContentsMargins(0,0,0,0)
        nbuttonslayout = QHBoxLayout()
        nbuttonslayout.addWidget(self.nbuttonslabel)
        nbuttonslayout.addWidget(self.nbuttonsSpinBox)
        nbuttonslayout.addSpacing(10)
        nbuttonslayout.addWidget(nbuttonsSizeLabel)
        nbuttonslayout.addWidget(self.nbuttonsSizeBox)
        nbuttonslayout.addSpacing(10)
        nbuttonslayout.addWidget(colorpatternlabel)
        nbuttonslayout.addWidget(self.colorSpinBox)
        nbuttonslayout.addSpacing(10)
        nbuttonslayout.addWidget(self.markLastButtonPressed)
        nbuttonslayout.addSpacing(10)
        nbuttonslayout.addWidget(self.showExtraButtonTooltips)
        nbuttonslayout.addStretch()
        tab2buttonlayout = QHBoxLayout()
        tab2buttonlayout.addWidget(addButton)
        tab2buttonlayout.addWidget(self.insertButton)
        tab2buttonlayout.addWidget(delButton)
        tab2buttonlayout.addWidget(self.copyeventbuttonTableButton)
        tab2buttonlayout.addStretch()
        tab2buttonlayout.addWidget(helpDialogButton)
        ### tab2 layout
        tab2layout = QVBoxLayout()
        tab2layout.addWidget(self.eventbuttontable)
        tab2layout.addLayout(nbuttonslayout)
        tab2layout.addLayout(tab2buttonlayout)
        tab2layout.setSpacing(5)
        tab2layout.setContentsMargins(0,10,0,5)
        ### tab4 layout
        paletteGrid = QGridLayout()
        paletteGrid.addWidget(transferpalettebutton,0,1)
        paletteGrid.addWidget(self.transferpalettecombobox,1,0)
        paletteGrid.addWidget(transferpalettecurrentLabel,1,2)
        paletteGrid.addWidget(self.transferpalettecurrentLabelEdit,1,3)
        paletteGrid.addWidget(setpalettebutton,2,1)
        paletteBox = QHBoxLayout()
        paletteBox.addStretch()
        paletteBox.addLayout(paletteGrid)
        paletteBox.addStretch()
        paletteFlags = QHBoxLayout()
        paletteFlags.addStretch()
        paletteFlags.addWidget(self.switchPaletteByNumberKey)
        paletteFlags.addStretch()
        paletteManagementBox = QVBoxLayout()
        paletteManagementBox.addLayout(paletteBox)
        paletteManagementBox.addLayout(paletteFlags)
        paletteGroupLayout = QGroupBox(QApplication.translate('GroupBox','Management'))
        paletteGroupLayout.setLayout(paletteManagementBox)
        paletteButtons = QHBoxLayout()
        paletteButtons.addStretch()
        paletteButtons.addWidget(restorebutton)
        paletteButtons.addWidget(backupbutton)
        tab3layout = QVBoxLayout()
        tab3layout.addWidget(paletteGroupLayout)
        tab3layout.addLayout(paletteButtons)
        tab3layout.addStretch()
        ###
        valueLayout = QGridLayout()
        valueLayout.addWidget(valuecolorlabel,0,0)
        valueLayout.addWidget(valuetextcolorlabel,0,1)
        valueLayout.addWidget(valuesymbollabel,0,2)
        valueLayout.addWidget(valuethicknesslabel,0,3)
        valueLayout.addWidget(valuealphalabel,0,4)
        valueLayout.addWidget(valuesizelabel,0,5)
        valueLayout.addWidget(self.E1colorButton,1,0)
        valueLayout.addWidget(self.E1textcolorButton,1,1)
        valueLayout.addWidget(self.marker1typeComboBox,1,2)
        valueLayout.addWidget(self.E1thicknessSpinBox,1,3)
        valueLayout.addWidget(self.E1alphaSpinBox,1,4)
        valueLayout.addWidget(self.E1sizeSpinBox,1,5)
        valueLayout.addWidget(self.E2colorButton,2,0)
        valueLayout.addWidget(self.E2textcolorButton,2,1)
        valueLayout.addWidget(self.marker2typeComboBox,2,2)
        valueLayout.addWidget(self.E2thicknessSpinBox,2,3)
        valueLayout.addWidget(self.E2alphaSpinBox,2,4)
        valueLayout.addWidget(self.E2sizeSpinBox,2,5)
        valueLayout.addWidget(self.E3colorButton,3,0)
        valueLayout.addWidget(self.E3textcolorButton,3,1)
        valueLayout.addWidget(self.marker3typeComboBox,3,2)
        valueLayout.addWidget(self.E3thicknessSpinBox,3,3)
        valueLayout.addWidget(self.E3alphaSpinBox,3,4)
        valueLayout.addWidget(self.E3sizeSpinBox,3,5)
        valueLayout.addWidget(self.E4colorButton,4,0)
        valueLayout.addWidget(self.E4textcolorButton,4,1)
        valueLayout.addWidget(self.marker4typeComboBox,4,2)
        valueLayout.addWidget(self.E4thicknessSpinBox,4,3)
        valueLayout.addWidget(self.E4alphaSpinBox,4,4)
        valueLayout.addWidget(self.E4sizeSpinBox,4,5)
        valueHLayout = QHBoxLayout()
        valueHLayout.addStretch()
        valueHLayout.addLayout(valueLayout)
        valueHLayout.addStretch()
        ### tab5 layout
        tab5Layout = QGridLayout()
        tab5Layout.addWidget(eventtitlelabel,0,0)
        tab5Layout.addWidget(actiontitlelabel,0,1)
        tab5Layout.addWidget(commandtitlelabel,0,2)
        tab5Layout.addWidget(min_titlelabel,0,3)
        tab5Layout.addWidget(max_titlelabel,0,4)
        tab5Layout.addWidget(factortitlelabel,0,5)
        tab5Layout.addWidget(offsettitlelabel,0,6)
        tab5Layout.addWidget(sliderBernoullititlelabel,0,7)
        tab5Layout.addWidget(slidercoarsetitlelabel,0,8,Qt.AlignmentFlag.AlignCenter)
        tab5Layout.addWidget(slidertemptitlelabel,0,9)
        tab5Layout.addWidget(sliderunittitlelabel,0,10)
        tab5Layout.addWidget(self.E1visibility,1,0)
        tab5Layout.addWidget(self.E2visibility,2,0)
        tab5Layout.addWidget(self.E3visibility,3,0)
        tab5Layout.addWidget(self.E4visibility,4,0)
        tab5Layout.addWidget(self.E1action,1,1)
        tab5Layout.addWidget(self.E2action,2,1)
        tab5Layout.addWidget(self.E3action,3,1)
        tab5Layout.addWidget(self.E4action,4,1)
        tab5Layout.addWidget(self.E1command,1,2)
        tab5Layout.addWidget(self.E2command,2,2)
        tab5Layout.addWidget(self.E3command,3,2)
        tab5Layout.addWidget(self.E4command,4,2)
        tab5Layout.addWidget(self.E1_min,1,3)
        tab5Layout.addWidget(self.E2_min,2,3)
        tab5Layout.addWidget(self.E3_min,3,3)
        tab5Layout.addWidget(self.E4_min,4,3)
        tab5Layout.addWidget(self.E1_max,1,4)
        tab5Layout.addWidget(self.E2_max,2,4)
        tab5Layout.addWidget(self.E3_max,3,4)
        tab5Layout.addWidget(self.E4_max,4,4)
        tab5Layout.addWidget(self.E1factor,1,5)
        tab5Layout.addWidget(self.E2factor,2,5)
        tab5Layout.addWidget(self.E3factor,3,5)
        tab5Layout.addWidget(self.E4factor,4,5)
        tab5Layout.addWidget(self.E1offset,1,6)
        tab5Layout.addWidget(self.E2offset,2,6)
        tab5Layout.addWidget(self.E3offset,3,6)
        tab5Layout.addWidget(self.E4offset,4,6)
        tab5Layout.addWidget(self.E1slider_bernoulli,1,7,Qt.AlignmentFlag.AlignCenter)
        tab5Layout.addWidget(self.E2slider_bernoulli,2,7,Qt.AlignmentFlag.AlignCenter)
        tab5Layout.addWidget(self.E3slider_bernoulli,3,7,Qt.AlignmentFlag.AlignCenter)
        tab5Layout.addWidget(self.E4slider_bernoulli,4,7,Qt.AlignmentFlag.AlignCenter)
        tab5Layout.addWidget(self.E1slider_step,1,8,Qt.AlignmentFlag.AlignCenter)
        tab5Layout.addWidget(self.E2slider_step,2,8,Qt.AlignmentFlag.AlignCenter)
        tab5Layout.addWidget(self.E3slider_step,3,8,Qt.AlignmentFlag.AlignCenter)
        tab5Layout.addWidget(self.E4slider_step,4,8,Qt.AlignmentFlag.AlignCenter)
        tab5Layout.addWidget(self.E1slider_temp,1,9,Qt.AlignmentFlag.AlignCenter)
        tab5Layout.addWidget(self.E2slider_temp,2,9,Qt.AlignmentFlag.AlignCenter)
        tab5Layout.addWidget(self.E3slider_temp,3,9,Qt.AlignmentFlag.AlignCenter)
        tab5Layout.addWidget(self.E4slider_temp,4,9,Qt.AlignmentFlag.AlignCenter)
        tab5Layout.addWidget(self.E1unit,1,10)
        tab5Layout.addWidget(self.E2unit,2,10)
        tab5Layout.addWidget(self.E3unit,3,10)
        tab5Layout.addWidget(self.E4unit,4,10)
        tab5Layout.addWidget(self.E1_calc,1,11)
        tab5Layout.addWidget(self.E2_calc,2,11)
        tab5Layout.addWidget(self.E3_calc,3,11)
        tab5Layout.addWidget(self.E4_calc,4,11)

        SliderHelpHBox = QHBoxLayout()
        SliderHelpHBox.addStretch()
        SliderHelpHBox.addStretch()
        SliderHelpHBox.addWidget(helpsliderDialogButton)
        SliderHelpHBox.addStretch()
        SliderHelpHBox.addWidget(self.sliderAlternativeLayoutFlag)
        SliderHelpHBox.addSpacing(10)
        SliderHelpHBox.addWidget(self.sliderKeyboardControlflag)
        C5VBox = QVBoxLayout()
        C5VBox.addLayout(tab5Layout)
        C5VBox.addStretch()
        C5VBox.addLayout(SliderHelpHBox)
        ### tab6 layout
        tab6Layout = QGridLayout()
        tab6Layout.addWidget(qeventtitlelabel,0,0,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(sourcetitlelabel,0,1,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(quantifierSVtitlelabel,0,2,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(mintitlelabel,0,3,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(maxtitlelabel,0,4,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(coarsetitlelabel,0,5,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(quantifieractiontitlelabel,0,6,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(self.E1active,1,0)
        tab6Layout.addWidget(self.E2active,2,0)
        tab6Layout.addWidget(self.E3active,3,0)
        tab6Layout.addWidget(self.E4active,4,0)
        tab6Layout.addWidget(self.E1SourceComboBox,1,1)
        tab6Layout.addWidget(self.E2SourceComboBox,2,1)
        tab6Layout.addWidget(self.E3SourceComboBox,3,1)
        tab6Layout.addWidget(self.E4SourceComboBox,4,1)
        tab6Layout.addWidget(self.E1quantifierSV,1,2,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(self.E2quantifierSV,2,2,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(self.E3quantifierSV,3,2,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(self.E4quantifierSV,4,2,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(self.E1min,1,3)
        tab6Layout.addWidget(self.E2min,2,3)
        tab6Layout.addWidget(self.E3min,3,3)
        tab6Layout.addWidget(self.E4min,4,3)
        tab6Layout.addWidget(self.E1max,1,4)
        tab6Layout.addWidget(self.E2max,2,4)
        tab6Layout.addWidget(self.E3max,3,4)
        tab6Layout.addWidget(self.E4max,4,4)
        tab6Layout.addWidget(self.E1coarse,1,5,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(self.E2coarse,2,5,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(self.E3coarse,3,5,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(self.E4coarse,4,5,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(self.E1quantifieraction,1,6,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(self.E2quantifieraction,2,6,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(self.E3quantifieraction,3,6,Qt.AlignmentFlag.AlignCenter)
        tab6Layout.addWidget(self.E4quantifieraction,4,6,Qt.AlignmentFlag.AlignCenter)
        QuantifierApplyHBox = QHBoxLayout()
        QuantifierApplyHBox.addStretch()
        QuantifierApplyHBox.addWidget(self.clusterEventsFlag)
        QuantifierApplyHBox.addStretch()
        QuantifierApplyHBox.addWidget(applyquantifierbutton)
        C6HBox = QHBoxLayout()
        C6HBox.addStretch()
        C6HBox.addLayout(tab6Layout)
        C6HBox.addStretch()
        C6VBox = QVBoxLayout()
        C6VBox.addLayout(C6HBox)
        C6VBox.addStretch()
        C6VBox.addLayout(QuantifierApplyHBox)
###########################################
        #tab layout
        self.TabWidget = QTabWidget()
        C1Widget = QWidget()
        C1Widget.setLayout(tab1layout)
        self.TabWidget.addTab(C1Widget,QApplication.translate('Tab','Config'))
        C1Widget.setContentsMargins(5, 0, 5, 0)
        C2Widget = QWidget()
        C2Widget.setLayout(tab2layout)
        if self.app.artisanviewerMode:
            C2Widget.setEnabled(False)
        self.TabWidget.addTab(C2Widget,QApplication.translate('Tab','Buttons'))
        C5Widget = QWidget()
        C5Widget.setLayout(C5VBox)
        if self.app.artisanviewerMode:
            C5Widget.setEnabled(False)
        self.TabWidget.addTab(C5Widget,QApplication.translate('Tab','Sliders'))
        C6Widget = QWidget()
        C6Widget.setLayout(C6VBox)
        self.TabWidget.addTab(C6Widget,QApplication.translate('Tab','Quantifiers'))
        C3Widget = QWidget()
        C3Widget.setLayout(tab3layout)
        self.TabWidget.addTab(C3Widget,QApplication.translate('Tab','Palettes'))
        valueVLayout = QVBoxLayout()
        valueVLayout.addLayout(valueHLayout)
        valueVLayout.addStretch()
        C4Widget = QWidget()
        C4Widget.setLayout(valueVLayout)
        self.TabWidget.addTab(C4Widget,QApplication.translate('Tab','Style'))
        C7Widget = QWidget()
        C7Widget.setLayout(tab7Layout)
        self.TabWidget.addTab(C7Widget,QApplication.translate('Tab','Annotations'))

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.TabWidget)
        mainLayout.setSpacing(5)
        mainLayout.setContentsMargins(5, 15, 5, 0)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
        if platform.system() != 'Windows':
            ok_button: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button is not None:
                ok_button.setFocus()
        else:
            self.TabWidget.setFocus()

        self.TabWidget.currentChanged.connect(self.tabSwitched)

        # we set the active tab with a QTimer after the tabbar has been rendered once, as otherwise
        # some tabs are not rendered at all on Windows using Qt v6.5.1 (https://bugreports.qt.io/projects/QTBUG/issues/QTBUG-114204?filter=allissues)
        QTimer.singleShot(50, self.setActiveTab)

    @pyqtSlot()
    def setActiveTab(self) -> None:
        self.TabWidget.setCurrentIndex(self.activeTab)

    # returns the position in self.sliderStepSizes corresponding to the given eventslidercoarse setting n
    @staticmethod
    def slidercoarse2stepSizePos(n:int) -> int:
        if n == 1:
            return 2
        if n == 2:
            return 1
        return 0

    @pyqtSlot(str)
    def changeSpecialeventEdit1(self, _:str) -> None:
        self.specialeventEditchanged(1)
    @pyqtSlot(str)
    def changeSpecialeventEdit2(self, _:str) -> None:
        self.specialeventEditchanged(2)
    @pyqtSlot(str)
    def changeSpecialeventEdit3(self, _:str) -> None:
        self.specialeventEditchanged(3)
    @pyqtSlot(str)
    def changeSpecialeventEdit4(self, _:str) -> None:
        self.specialeventEditchanged(4)

    def specialeventEditchanged(self, n:int) -> None:
        if n == 1:
            self.E1Preview1.setText(self.aw.qmc.parseSpecialeventannotation(self.E1Edit.text(),eventnum=0,applyto='preview',postFCs=False))
            self.E1Preview2.setText(self.aw.qmc.parseSpecialeventannotation(self.E1Edit.text(),eventnum=0,applyto='preview',postFCs=True))
            self.aw.qmc.specialeventannotations[0] = self.E1Edit.text()
        if n == 2:
            self.E2Preview1.setText(self.aw.qmc.parseSpecialeventannotation(self.E2Edit.text(),eventnum=0,applyto='preview',postFCs=False))
            self.E2Preview2.setText(self.aw.qmc.parseSpecialeventannotation(self.E2Edit.text(),eventnum=0,applyto='preview',postFCs=True))
            self.aw.qmc.specialeventannotations[1] = self.E2Edit.text()
        if n == 3:
            self.E3Preview1.setText(self.aw.qmc.parseSpecialeventannotation(self.E3Edit.text(),eventnum=0,applyto='preview',postFCs=False))
            self.E3Preview2.setText(self.aw.qmc.parseSpecialeventannotation(self.E3Edit.text(),eventnum=0,applyto='preview',postFCs=True))
            self.aw.qmc.specialeventannotations[2] = self.E3Edit.text()
        if n == 4:
            self.E4Preview1.setText(self.aw.qmc.parseSpecialeventannotation(self.E4Edit.text(),eventnum=0,applyto='preview',postFCs=False))
            self.E4Preview2.setText(self.aw.qmc.parseSpecialeventannotation(self.E4Edit.text(),eventnum=0,applyto='preview',postFCs=True))
            self.aw.qmc.specialeventannotations[3] = self.E4Edit.text()

    @pyqtSlot(bool)
    def backuppaletteeventbuttonsSlot(self, _:bool = False) -> None:
        self.aw.backuppaletteeventbuttons(self.aw.buttonpalette,self.aw.buttonpalettemaxlen)
        self.transferpalettecombobox.setCurrentIndex(-1)

    @pyqtSlot(bool)
    def restorepaletteeventbuttons(self, _:bool = False) -> None:
        filename = self.aw.ArtisanOpenFileDialog(msg=QApplication.translate('Message','Load Palettes'),path=self.aw.profilepath)
        if filename:
            maxlen = self.aw.loadPalettes(filename,self.aw.buttonpalette)
            if maxlen is not None:
                self.aw.buttonpalettemaxlen = maxlen
            self.updatePalettePopup()

    @staticmethod
    def swapItems(l:List[Any], source:int, target:int) -> None:
        l[target],l[source] = l[source],l[target]

    @staticmethod
    def moveItem(l:List[Any], source:int, target:int) -> None:
        l.insert(target, l.pop(source))

    @pyqtSlot(int,int,int)
    def sectionMoved(self, logicalIndex:int, _oldVisualIndex:int, newVisualIndex:int) -> None:
        max_rows:int = len(self.extraeventstypes)


        # adjust vertical headers # seems not to be required with the clearContent/setRowCount(0) below
        self.eventbuttontable.setVerticalHeaderLabels([str(1 + self.eventbuttontable.visualRow(i)) for i in range(max_rows)])

        # adjust datamodel
        swap:bool = False # default action is to move item to new position
        if QApplication.queryKeyboardModifiers() == Qt.KeyboardModifier.AltModifier:
            # if ALT/OPTION key is hold, the items are swap
            swap = True
        l:List[Any]
        event_data:List[List[Any]] = [self.extraeventslabels, self.extraeventsdescriptions, self.extraeventstypes, self.extraeventsvalues,
                self.extraeventsactions, self.extraeventsactionstrings, self.extraeventsvisibility, self.extraeventbuttoncolor,
                self.extraeventbuttontextcolor]
        for l in event_data:
            if swap:
                self.swapItems(l, logicalIndex, newVisualIndex)
            else:
                self.moveItem(l, logicalIndex, newVisualIndex)

        self.eventbuttontable.clearContents() # resets the view
        self.eventbuttontable.setRowCount(0)  # resets the data model
        self.createEventbuttonTable()


    @pyqtSlot()
    def selectionChanged(self) -> None:
        selected = self.eventbuttontable.selectedRanges()
        if self.insertButton is not None:
            if selected and len(selected) > 0:
                self.insertButton.setEnabled(True)
            else:
                self.insertButton.setEnabled(False)

    @pyqtSlot(int)
    def changeShowMet(self, _:int) -> None:
        self.aw.qmc.showmet = not self.aw.qmc.showmet
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def SAMPLINGbuttonActionTypeChanged(self, index:int) -> None:
        self.SAMPLINGbuttonActionInterval.setEnabled(bool(index))

    @pyqtSlot(int)
    def autoChargeStateChanged(self, state:int) -> None:
        self.autoChargeModeComboBox.setEnabled(bool(state))

    @pyqtSlot(int)
    def autoDropStateChanged(self, state:int) -> None:
        self.autoDropModeComboBox.setEnabled(bool(state))

    @pyqtSlot(int)
    def changeShowTimeguide(self, _:int) -> None:
        self.aw.qmc.showtimeguide = not self.aw.qmc.showtimeguide

    @pyqtSlot(bool)
    def applyQuantifiers(self, _:bool = False) -> None:
        self.saveQuantifierSettings()
        # recompute the 4 event quantifier linspaces
        self.aw.computeLinespaces()
        # remove previous quantifier events
        # recompute quantifier events
        redraw = False
        for i in range(4):
            if self.aw.eventquantifieractive[i]:
                temp,timex = self.aw.quantifier2tempandtime(i)
                if temp:
                    # a temp curve exists
                    linespace = self.aw.eventquantifierlinspaces[i]
                    if self.aw.eventquantifiercoarse[i]:
                        linespacethreshold = abs(linespace[1] - linespace[0]) * self.aw.eventquantifierthresholdcoarse
                    else:
                        linespacethreshold = abs(linespace[1] - linespace[0]) * self.aw.eventquantifierthresholdfine
                    # loop over that data and classify each value
                    ld:Optional[float] = None # last digitized value
                    lt:Optional[float] = None # last digitized temp value
                    for ii, t in enumerate(temp):
                        if t != -1: # -1 is an error value
                            d = self.aw.digitize(t,linespace,self.aw.eventquantifiercoarse[i],i)
                            if d is not None and (ld is None or ld != d) and (ld is None or lt is None or linespacethreshold < abs(t - lt)):
                                # take only changes
                                # and only if significantly different than previous to avoid fluktuation
                                # establish this one
                                ld = d
                                lt = t
                                # add to event table
                                self.aw.qmc.addEvent(
                                    self.aw.qmc.time2index(timex[ii]),
                                    i,
                                    'Q'+ self.aw.qmc.eventsvalues(float(d+1)),
                                    float(d+1))
                                self.aw.qmc.fileDirty()
                    redraw = True
        if self.aw.clusterEventsFlag:
            self.aw.clusterEvents(True)
        if redraw:
            self.aw.qmc.redraw(recomputeAllDeltas=False)

    def saveEventTypes(self) -> None:
        self.aw.qmc.etypes[0] = self.etype0.text()
        self.aw.qmc.etypes[1] = self.etype1.text()
        self.aw.qmc.etypes[2] = self.etype2.text()
        self.aw.qmc.etypes[3] = self.etype3.text()

    @pyqtSlot(int)
    def tabSwitched(self, i:int) -> None:
        self.closeHelp()
        if i == 0:
            self.saveSliderSettings()
            self.saveQuantifierSettings()
        elif i == 1: # switched to Button tab
            self.saveEventTypes()
            self.createEventbuttonTable()
            self.saveSliderSettings()
            self.saveQuantifierSettings()
            self.saveAnnotationsSettings()
        elif i == 2: # switched to Slider tab
            self.saveQuantifierSettings()
            self.saveAnnotationsSettings()
            self.updateSliderTab()  # reflect updated event names if changed in tab 1
        elif i == 3: # switched to Quantifier tab
            self.saveSliderSettings()
            self.saveAnnotationsSettings()
            self.updateQuantifierTab() # reflect updated event names if changed in tab 1
        elif i == 4: # switched to Palette tab
            # store slider settings from Slider tab to global variables
            # store sliders
            self.saveSliderSettings()
            self.saveQuantifierSettings()
#            # store buttons (not done here anymore: buttons are saved on leaving the dialog with OK)
#            self.savetableextraeventbutton()
            self.saveAnnotationsSettings()
        elif i == 5: # switched to Style tab
            self.updateStyleTab()
            self.saveSliderSettings()
            self.saveQuantifierSettings()
            self.saveAnnotationsSettings()
        elif i == 6: # switched to Annotations tab
            self.updateAnnotationsTab()
            self.saveQuantifierSettings()

    def updateQuantifierTab(self) -> None:
        self.E1active.setText(self.etype0.text())
        self.E2active.setText(self.etype1.text())
        self.E3active.setText(self.etype2.text())
        self.E4active.setText(self.etype3.text())
        self.E1active.setChecked(bool(self.aw.eventquantifieractive[0]))
        self.E2active.setChecked(bool(self.aw.eventquantifieractive[1]))
        self.E3active.setChecked(bool(self.aw.eventquantifieractive[2]))
        self.E4active.setChecked(bool(self.aw.eventquantifieractive[3]))
        self.E1coarse.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventquantifiercoarse[0]))
        self.E2coarse.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventquantifiercoarse[1]))
        self.E3coarse.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventquantifiercoarse[2]))
        self.E4coarse.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventquantifiercoarse[3]))
        self.E1quantifieraction.setChecked(bool(self.aw.eventquantifieraction[0]))
        self.E2quantifieraction.setChecked(bool(self.aw.eventquantifieraction[1]))
        self.E3quantifieraction.setChecked(bool(self.aw.eventquantifieraction[2]))
        self.E4quantifieraction.setChecked(bool(self.aw.eventquantifieraction[3]))
        self.E1quantifierSV.setChecked(bool(self.aw.eventquantifierSV[0]))
        self.E2quantifierSV.setChecked(bool(self.aw.eventquantifierSV[1]))
        self.E3quantifierSV.setChecked(bool(self.aw.eventquantifierSV[2]))
        self.E4quantifierSV.setChecked(bool(self.aw.eventquantifierSV[3]))
        if self.aw.eventquantifiersource[0] < len(self.curvenames):
            self.E1SourceComboBox.setCurrentIndex(self.aw.eventquantifiersource[0])
        if self.aw.eventquantifiersource[1] < len(self.curvenames):
            self.E2SourceComboBox.setCurrentIndex(self.aw.eventquantifiersource[1])
        if self.aw.eventquantifiersource[2] < len(self.curvenames):
            self.E3SourceComboBox.setCurrentIndex(self.aw.eventquantifiersource[2])
        if self.aw.eventquantifiersource[3] < len(self.curvenames):
            self.E4SourceComboBox.setCurrentIndex(self.aw.eventquantifiersource[3])
        self.E1min.setValue(self.aw.eventquantifiermin[0])
        self.E2min.setValue(self.aw.eventquantifiermin[1])
        self.E3min.setValue(self.aw.eventquantifiermin[2])
        self.E4min.setValue(self.aw.eventquantifiermin[3])
        self.E1max.setValue(self.aw.eventquantifiermax[0])
        self.E2max.setValue(self.aw.eventquantifiermax[1])
        self.E3max.setValue(self.aw.eventquantifiermax[2])
        self.E4max.setValue(self.aw.eventquantifiermax[3])
        self.curvenames = []
#        self.curvenames.append(QApplication.translate('ComboBox','ET'))
#        self.curvenames.append(QApplication.translate('ComboBox','BT'))
        self.curvenames.append(self.aw.ETname.format(self.etype0.text(),self.etype1.text(),self.etype2.text(),self.etype3.text()))
        self.curvenames.append(self.aw.BTname.format(self.etype0.text(),self.etype1.text(),self.etype2.text(),self.etype3.text()))
        for i in range(len(self.aw.qmc.extradevices)):
            self.curvenames.append(self.aw.qmc.extraname1[i].format(self.etype0.text(),self.etype1.text(),self.etype2.text(),self.etype3.text()))
            self.curvenames.append(self.aw.qmc.extraname2[i].format(self.etype0.text(),self.etype1.text(),self.etype2.text(),self.etype3.text()))
        self.E1SourceComboBox.clear()
        self.E1SourceComboBox.addItems(self.curvenames)
        if self.aw.eventquantifiersource[0] < len(self.curvenames):
            self.E1SourceComboBox.setCurrentIndex(self.aw.eventquantifiersource[0])
        self.E2SourceComboBox.clear()
        self.E2SourceComboBox.addItems(self.curvenames)
        if self.aw.eventquantifiersource[1] < len(self.curvenames):
            self.E2SourceComboBox.setCurrentIndex(self.aw.eventquantifiersource[1])
        self.E3SourceComboBox.clear()
        self.E3SourceComboBox.addItems(self.curvenames)
        if self.aw.eventquantifiersource[2] < len(self.curvenames):
            self.E3SourceComboBox.setCurrentIndex(self.aw.eventquantifiersource[2])
        self.E4SourceComboBox.clear()
        self.E4SourceComboBox.addItems(self.curvenames)
        if self.aw.eventquantifiersource[3] < len(self.curvenames):
            self.E4SourceComboBox.setCurrentIndex(self.aw.eventquantifiersource[3])


    def updateStyleTab(self) -> None:
        # update color button texts
        self.E1colorButton.setText(self.etype0.text())
        self.E2colorButton.setText(self.etype1.text())
        self.E3colorButton.setText(self.etype2.text())
        self.E4colorButton.setText(self.etype3.text())
        self.E1textcolorButton.setText(self.etype0.text())
        self.E2textcolorButton.setText(self.etype1.text())
        self.E3textcolorButton.setText(self.etype2.text())
        self.E4textcolorButton.setText(self.etype3.text())
        ok_button = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button_width = ok_button.width()
            self.E1colorButton.setMinimumWidth(max(ok_button_width,self.E1textcolorButton.minimumSizeHint().width()))
            self.E1textcolorButton.setMinimumWidth(max(ok_button_width,self.E1textcolorButton.minimumSizeHint().width()))
        self.E1colorButton.setStyleSheet('border: none; outline: none; background-color: ' + self.aw.qmc.EvalueColor[0] + '; color: ' + self.aw.qmc.EvalueTextColor[0] + '; border-style: solid; border-width: 1px; border-radius: 4px; border-color: black; padding: 4px;')
        self.E2colorButton.setStyleSheet('border: none; outline: none; background-color: ' + self.aw.qmc.EvalueColor[1] + '; color: ' + self.aw.qmc.EvalueTextColor[1] + '; border-style: solid; border-width: 1px; border-radius: 4px; border-color: black; padding: 4px;')
        self.E3colorButton.setStyleSheet('border: none; outline: none; background-color: ' + self.aw.qmc.EvalueColor[2] + '; color: ' + self.aw.qmc.EvalueTextColor[2] + '; border-style: solid; border-width: 1px; border-radius: 4px; border-color: black; padding: 4px;')
        self.E4colorButton.setStyleSheet('border: none; outline: none; background-color: ' + self.aw.qmc.EvalueColor[3] + '; color: ' + self.aw.qmc.EvalueTextColor[3] + '; border-style: solid; border-width: 1px; border-radius: 4px; border-color: black; padding: 4px;')
        self.E1textcolorButton.setStyleSheet('border: none; outline: none; background-color: ' + self.aw.qmc.EvalueColor[0] + '; color: ' + self.aw.qmc.EvalueTextColor[0] + '; border-style: solid; border-width: 1px; border-radius: 4px; border-color: black; padding: 4px;')
        self.E2textcolorButton.setStyleSheet('border: none; outline: none; background-color: ' + self.aw.qmc.EvalueColor[1] + '; color: ' + self.aw.qmc.EvalueTextColor[1] + '; border-style: solid; border-width: 1px; border-radius: 4px; border-color: black; padding: 4px;')
        self.E3textcolorButton.setStyleSheet('border: none; outline: none; background-color: ' + self.aw.qmc.EvalueColor[2] + '; color: ' + self.aw.qmc.EvalueTextColor[2] + '; border-style: solid; border-width: 1px; border-radius: 4px; border-color: black; padding: 4px;')
        self.E4textcolorButton.setStyleSheet('border: none; outline: none; background-color: ' + self.aw.qmc.EvalueColor[3] + '; color: ' + self.aw.qmc.EvalueTextColor[3] + '; border-style: solid; border-width: 1px; border-radius: 4px; border-color: black; padding: 4px;')

        # update markers
        if self.aw.qmc.EvalueMarker[0] in self.markervals:
            self.marker1typeComboBox.setCurrentIndex(self.markervals.index(self.aw.qmc.EvalueMarker[0]))
        else:
            self.marker1typeComboBox.setCurrentIndex(0)
        if self.aw.qmc.EvalueMarker[1] in self.markervals:
            self.marker2typeComboBox.setCurrentIndex(self.markervals.index(self.aw.qmc.EvalueMarker[1]))
        else:
            self.marker2typeComboBox.setCurrentIndex(0)
        if self.aw.qmc.EvalueMarker[2] in self.markervals:
            self.marker3typeComboBox.setCurrentIndex(self.markervals.index(self.aw.qmc.EvalueMarker[2]))
        else:
            self.marker3typeComboBox.setCurrentIndex(0)
        if self.aw.qmc.EvalueMarker[3] in self.markervals:
            self.marker4typeComboBox.setCurrentIndex(self.markervals.index(self.aw.qmc.EvalueMarker[3]))
        else:
            self.marker4typeComboBox.setCurrentIndex(0)
        # line thickness
        self.E1thicknessSpinBox.setValue(int(round(self.aw.qmc.Evaluelinethickness[0])))
        self.E2thicknessSpinBox.setValue(int(round(self.aw.qmc.Evaluelinethickness[1])))
        self.E3thicknessSpinBox.setValue(int(round(self.aw.qmc.Evaluelinethickness[2])))
        self.E4thicknessSpinBox.setValue(int(round(self.aw.qmc.Evaluelinethickness[3])))
        # opacity
        self.E1alphaSpinBox.setValue(self.aw.qmc.Evaluealpha[0])
        self.E2alphaSpinBox.setValue(self.aw.qmc.Evaluealpha[1])
        self.E3alphaSpinBox.setValue(self.aw.qmc.Evaluealpha[2])
        self.E4alphaSpinBox.setValue(self.aw.qmc.Evaluealpha[3])
        # marker sizes
        self.E1sizeSpinBox.setValue(self.aw.qmc.EvalueMarkerSize[0])
        self.E2sizeSpinBox.setValue(self.aw.qmc.EvalueMarkerSize[1])
        self.E3sizeSpinBox.setValue(self.aw.qmc.EvalueMarkerSize[2])
        self.E4sizeSpinBox.setValue(self.aw.qmc.EvalueMarkerSize[3])

    def updateSliderTab(self) -> None:
        # set event names
        self.E1visibility.setText(self.etype0.text())
        self.E2visibility.setText(self.etype1.text())
        self.E3visibility.setText(self.etype2.text())
        self.E4visibility.setText(self.etype3.text())
        # set slider visibility
        self.E1visibility.setChecked(bool(self.aw.eventslidervisibilities[0]))
        self.E2visibility.setChecked(bool(self.aw.eventslidervisibilities[1]))
        self.E3visibility.setChecked(bool(self.aw.eventslidervisibilities[2]))
        self.E4visibility.setChecked(bool(self.aw.eventslidervisibilities[3]))
        # set slider action
        self.E1action.setCurrentIndex(self.sliderActionTypesSorted.index(self.sliderActionTypes[self.aw.eventslideractions[0]]))
        self.E2action.setCurrentIndex(self.sliderActionTypesSorted.index(self.sliderActionTypes[self.aw.eventslideractions[1]]))
        self.E3action.setCurrentIndex(self.sliderActionTypesSorted.index(self.sliderActionTypes[self.aw.eventslideractions[2]]))
        self.E4action.setCurrentIndex(self.sliderActionTypesSorted.index(self.sliderActionTypes[self.aw.eventslideractions[3]]))
        # set slider command
        self.E1command.setText(self.aw.eventslidercommands[0])
        self.E2command.setText(self.aw.eventslidercommands[1])
        self.E3command.setText(self.aw.eventslidercommands[2])
        self.E4command.setText(self.aw.eventslidercommands[3])
        # set slider offset
        self.E1offset.setValue(self.aw.eventslideroffsets[0])
        self.E2offset.setValue(self.aw.eventslideroffsets[1])
        self.E3offset.setValue(self.aw.eventslideroffsets[2])
        self.E4offset.setValue(self.aw.eventslideroffsets[3])
        # set slider factors
        self.E1factor.setValue(self.aw.eventsliderfactors[0])
        self.E2factor.setValue(self.aw.eventsliderfactors[1])
        self.E3factor.setValue(self.aw.eventsliderfactors[2])
        self.E4factor.setValue(self.aw.eventsliderfactors[3])
        # set slider min
        self.E1_min.setValue(int(self.aw.eventslidermin[0]))
        self.E2_min.setValue(int(self.aw.eventslidermin[1]))
        self.E3_min.setValue(int(self.aw.eventslidermin[2]))
        self.E4_min.setValue(int(self.aw.eventslidermin[3]))
        # set slider max
        self.E1_max.setValue(int(self.aw.eventslidermax[0]))
        self.E2_max.setValue(int(self.aw.eventslidermax[1]))
        self.E3_max.setValue(int(self.aw.eventslidermax[2]))
        self.E4_max.setValue(int(self.aw.eventslidermax[3]))
        # set slider Bernoulli
        self.E1slider_bernoulli.setChecked(bool(self.aw.eventsliderBernoulli[0]))
        self.E2slider_bernoulli.setChecked(bool(self.aw.eventsliderBernoulli[1]))
        self.E3slider_bernoulli.setChecked(bool(self.aw.eventsliderBernoulli[2]))
        self.E4slider_bernoulli.setChecked(bool(self.aw.eventsliderBernoulli[3]))
        # set slider coarse
        self.E1slider_step.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventslidercoarse[0]))
        self.E2slider_step.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventslidercoarse[1]))
        self.E3slider_step.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventslidercoarse[2]))
        self.E4slider_step.setCurrentIndex(self.slidercoarse2stepSizePos(self.aw.eventslidercoarse[3]))
        # set slider temp
        self.E1slider_temp.setChecked(bool(self.aw.eventslidertemp[0]))
        self.E2slider_temp.setChecked(bool(self.aw.eventslidertemp[1]))
        self.E3slider_temp.setChecked(bool(self.aw.eventslidertemp[2]))
        self.E4slider_temp.setChecked(bool(self.aw.eventslidertemp[3]))
        # set slider units
        self.E1unit.setText(self.aw.eventsliderunits[0])
        self.E2unit.setText(self.aw.eventsliderunits[1])
        self.E3unit.setText(self.aw.eventsliderunits[2])
        self.E4unit.setText(self.aw.eventsliderunits[3])

    def updateAnnotationsTab(self) -> None:
        # set event names
        self.E1AnnoVisibility.setText(self.etype0.text())
        self.E2Annovisibility.setText(self.etype1.text())
        self.E3Annovisibility.setText(self.etype2.text())
        self.E4Annovisibility.setText(self.etype3.text())
        # set annotation visibility
        self.E1AnnoVisibility.setChecked(bool(self.aw.qmc.specialeventannovisibilities[0]))
        self.E2Annovisibility.setChecked(bool(self.aw.qmc.specialeventannovisibilities[1]))
        self.E3Annovisibility.setChecked(bool(self.aw.qmc.specialeventannovisibilities[2]))
        self.E4Annovisibility.setChecked(bool(self.aw.qmc.specialeventannovisibilities[3]))

    @pyqtSlot(int)
    def setElinethickness0(self, _:int) -> None:
        self.setElinethickness(0)
    @pyqtSlot(int)
    def setElinethickness1(self, _:int) -> None:
        self.setElinethickness(1)
    @pyqtSlot(int)
    def setElinethickness2(self, _:int) -> None:
        self.setElinethickness(2)
    @pyqtSlot(int)
    def setElinethickness3(self, _:int) -> None:
        self.setElinethickness(3)

    def setElinethickness(self, val:int) -> None:
        self.E1thicknessSpinBox.setDisabled(True)
        self.E2thicknessSpinBox.setDisabled(True)
        self.E3thicknessSpinBox.setDisabled(True)
        self.E4thicknessSpinBox.setDisabled(True)
        if val == 0:
            self.aw.qmc.Evaluelinethickness[0] = self.E1thicknessSpinBox.value()
        if val == 1:
            self.aw.qmc.Evaluelinethickness[1] = self.E2thicknessSpinBox.value()
        if val == 2:
            self.aw.qmc.Evaluelinethickness[2] = self.E3thicknessSpinBox.value()
        if val == 3:
            self.aw.qmc.Evaluelinethickness[3] = self.E4thicknessSpinBox.value()
        self.E1thicknessSpinBox.setDisabled(False)
        self.E2thicknessSpinBox.setDisabled(False)
        self.E3thicknessSpinBox.setDisabled(False)
        self.E4thicknessSpinBox.setDisabled(False)
        self.aw.qmc.redraw()

    @pyqtSlot()
    def setEmarkersize0(self) -> None:
        self.setEmarkersize(0)
    @pyqtSlot()
    def setEmarkersize1(self) -> None:
        self.setEmarkersize(1)
    @pyqtSlot()
    def setEmarkersize2(self) -> None:
        self.setEmarkersize(2)
    @pyqtSlot()
    def setEmarkersize3(self) -> None:
        self.setEmarkersize(3)

    def setEmarkersize(self, val:int) -> None:
#        self.E1sizeSpinBox.setDisabled(True)
#        self.E2sizeSpinBox.setDisabled(True)
#        self.E3sizeSpinBox.setDisabled(True)
#        self.E4sizeSpinBox.setDisabled(True)
        if val == 0:
            self.aw.qmc.EvalueMarkerSize[0] = self.E1sizeSpinBox.value()
        if val == 1:
            self.aw.qmc.EvalueMarkerSize[1] = self.E2sizeSpinBox.value()
        if val == 2:
            self.aw.qmc.EvalueMarkerSize[2] = self.E3sizeSpinBox.value()
        if val == 3:
            self.aw.qmc.EvalueMarkerSize[3] = self.E4sizeSpinBox.value()
#        self.E1sizeSpinBox.setDisabled(False)
#        self.E2sizeSpinBox.setDisabled(False)
#        self.E3sizeSpinBox.setDisabled(False)
#        self.E4sizeSpinBox.setDisabled(False)
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(float)
    def setElinealpha0(self, _:float) -> None:
        self.setElinealpha(0)
    @pyqtSlot(float)
    def setElinealpha1(self,_:float) -> None:
        self.setElinealpha(1)
    @pyqtSlot(float)
    def setElinealpha2(self,_:float) -> None:
        self.setElinealpha(2)
    @pyqtSlot(float)
    def setElinealpha3(self,_:float) -> None:
        self.setElinealpha(3)

    def setElinealpha(self, val:int) -> None:
        self.E1alphaSpinBox.setDisabled(True)
        self.E2alphaSpinBox.setDisabled(True)
        self.E3alphaSpinBox.setDisabled(True)
        self.E4alphaSpinBox.setDisabled(True)
        if val == 0:
            self.aw.qmc.Evaluealpha[0] = self.E1alphaSpinBox.value()
        if val == 1:
            self.aw.qmc.Evaluealpha[1] = self.E2alphaSpinBox.value()
        if val == 2:
            self.aw.qmc.Evaluealpha[2] = self.E3alphaSpinBox.value()
        if val == 3:
            self.aw.qmc.Evaluealpha[3] = self.E4alphaSpinBox.value()
        self.E1alphaSpinBox.setDisabled(False)
        self.E2alphaSpinBox.setDisabled(False)
        self.E3alphaSpinBox.setDisabled(False)
        self.E4alphaSpinBox.setDisabled(False)
        self.aw.qmc.redraw()

    @pyqtSlot(bool)
    def transferbuttonstoSlot(self, _:bool = False) -> None:
        self.transferbuttonsto()

    def transferbuttonsto(self, pindex:Optional[int] = None) -> None:
        if pindex is None:
            pindex = self.transferpalettecombobox.currentIndex()
        if 0 <= pindex < 10:
            copy:Palette = (
                self.extraeventstypes[:],
                self.extraeventsvalues[:],
                self.extraeventsactions[:],
                self.extraeventsvisibility[:],
                self.extraeventsactionstrings[:],
                self.extraeventslabels[:],
                self.extraeventsdescriptions[:],
                self.extraeventbuttoncolor[:],
                self.extraeventbuttontextcolor[:],
                # added slider settings
                self.aw.eventslidervisibilities[:],
                self.aw.eventslideractions[:],
                self.aw.eventslidercommands[:],
                self.aw.eventslideroffsets[:],
                self.aw.eventsliderfactors[:],
                # added quantifier settings
                self.aw.eventquantifieractive[:],
                self.aw.eventquantifiersource[:],
                self.aw.eventquantifiermin[:],
                self.aw.eventquantifiermax[:],
                self.aw.eventquantifiercoarse[:],
                # added slider min/max
                self.aw.eventslidermin[:],
                self.aw.eventslidermax[:],
                # added slider coarse
                self.aw.eventslidercoarse[:],
                # added slider temp
                self.aw.eventslidertemp[:],
                # added slider unit
                self.aw.eventsliderunits[:],
                # added slider Bernoulli
                self.aw.eventsliderBernoulli[:],
                # added palette label
                self.transferpalettecurrentLabelEdit.text(),
                # added quantifier actions
                self.aw.eventquantifieraction[:],
                # added quantifier SV
                self.aw.eventquantifierSV[:]
            )

            self.aw.buttonpalette[pindex] = copy
            self.aw.buttonpalettemaxlen[pindex] = self.aw.buttonlistmaxlen
            self.transferpalettecombobox.setCurrentIndex(-1)
            self.updatePalettePopup()


    def localSetbuttonsfrom(self, pindex:int) -> int:
        copy = cast('Palette', self.aw.buttonpalette[pindex][:])
        if len(copy):
            self.extraeventstypes = copy[0][:] # pylint: disable=attribute-defined-outside-init
            self.extraeventsvalues = copy[1][:] # pylint: disable=attribute-defined-outside-init
            self.extraeventsactions = copy[2][:] # pylint: disable=attribute-defined-outside-init
            self.extraeventsvisibility = copy[3][:] # pylint: disable=attribute-defined-outside-init
            self.extraeventsactionstrings = copy[4][:] # pylint: disable=attribute-defined-outside-init
            self.extraeventslabels = copy[5][:] # pylint: disable=attribute-defined-outside-init
            self.extraeventsdescriptions = copy[6][:] # pylint: disable=attribute-defined-outside-init
            self.extraeventbuttoncolor = copy[7][:] # pylint: disable=attribute-defined-outside-init
            self.extraeventbuttontextcolor = copy[8][:] # pylint: disable=attribute-defined-outside-init
            # added slider settings
            if len(copy)>9 and len(copy[9]) == 4:
                self.aw.eventslidervisibilities = copy[9][:]
            else:
                self.aw.eventslidervisibilities = [0,0,0,0]
            if len(copy)>10 and len(copy[10]) == 4:
                self.aw.eventslideractions = copy[10][:]
            else:
                self.aw.eventslideractions = [0,0,0,0]
            if len(copy)>11 and len(copy[11]) == 4:
                self.aw.eventslidercommands = copy[11][:]
            else:
                self.aw.eventslidercommands = ['','','','']
            if len(copy)>12 and len(copy[12]) == 4:
                self.aw.eventslideroffsets = copy[12][:]
            else:
                self.aw.eventslideroffsets = [0., 0., 0., 0.]
            if len(copy)>13 and len(copy[13]) == 4:
                self.aw.eventsliderfactors = copy[13][:]
            else:
                self.aw.eventsliderfactors = [1.0,1.0,1.0,1.0]
            # quantifiers
            if len(copy)>14 and len(copy[14]) == 4:
                self.aw.eventquantifieractive = copy[14][:]
            else:
                self.aw.eventquantifieractive = [0,0,0,0]
            if len(copy)>15 and len(copy[15]) == 4:
                self.aw.eventquantifiersource = copy[15][:]
            else:
                self.aw.eventquantifiersource = [0,0,0,0]
            if len(copy)>16 and len(copy[16]) == 4:
                self.aw.eventquantifiermin = copy[16][:]
            else:
                self.aw.eventquantifiermin = [0,0,0,0]
            if len(copy)>17 and len(copy[17]) == 4:
                self.aw.eventquantifiermax = copy[17][:]
            else:
                self.aw.eventquantifiermax = [100,100,100,100]
            if len(copy)>18 and len(copy[18]) == 4:
                self.aw.eventquantifiercoarse = copy[18][:]
            else:
                self.aw.eventquantifiercoarse = [0,0,0,0]
            # slider min/max
            if len(copy)>19 and len(copy[19]) == 4:
                self.aw.eventslidermin = copy[19][:]
            else:
                self.aw.eventslidermin = [0,0,0,0]
            if len(copy)>20 and len(copy[20]) == 4:
                self.aw.eventslidermax = copy[20][:]
            else:
                self.aw.eventslidermax = [100,100,100,100]
            # slider coarse
            if len(copy)>21 and len(copy[21]) == 4:
                self.aw.eventslidercoarse = copy[21][:]
            else:
                self.aw.eventslidercoarse = [0,0,0,0]
            # slide temp
            if len(copy)>22 and len(copy[22]) == 4:
                self.aw.eventslidertemp = copy[22][:]
            else:
                self.aw.eventslidertemp = [0,0,0,0]
            # slider units
            if len(copy)>23 and len(copy[23]) == 4:
                self.aw.eventsliderunits = copy[23][:]
            else:
                self.aw.eventsliderunits = ['','','','']
            # slider bernoulli
            if len(copy)>24 and len(copy[24]) == 4:
                self.aw.eventsliderBernoulli = copy[24][:]
            else:
                self.aw.eventsliderBernoulli = [0,0,0,0]
            # palette label
            if len(copy)>25:
                self.aw.buttonpalette_label = copy[25]
            else:
                self.aw.buttonpalette_label = self.aw.buttonpalette_default_label
            if len(copy)>26 and len(copy[26]) == 4:
                self.aw.eventquantifieraction = copy[26][:]
            else:
                self.aw.eventquantifieraction = [0,0,0,0]
            if len(copy)>27 and len(copy[27]) == 4:
                self.aw.eventquantifierSV = copy[27][:]
            else:
                self.aw.eventquantifierSV = [0,0,0,0]

            self.aw.buttonlistmaxlen = self.aw.buttonpalettemaxlen[pindex]

            return 1  #success
        return 0  #failed

    @pyqtSlot(bool)
    def setbuttonsfrom(self, _:bool = False) -> None:
        pindex = self.transferpalettecombobox.currentIndex()
        if 0 <= pindex < 10:
            answer = self.localSetbuttonsfrom(pindex)
            if answer:
                self.nbuttonsSpinBox.setValue(int(self.aw.buttonlistmaxlen))
                self.transferpalettecurrentLabelEdit.setText(self.aw.buttonpalette_label)
                self.updatePalettePopup()
                self.updateSliderTab()
                self.updateQuantifierTab()
                self.createEventbuttonTable()
                self.transferpalettecombobox.setCurrentIndex(-1)

    def updatePalettePopup(self) -> None:
        self.transferpalettecombobox.clear()
        palettelist = []
        for i, _ in enumerate(self.aw.buttonpalette):
            palettelist.append(f'#{str(i)} {self.aw.buttonpalette[i][25]}')
        self.transferpalettecombobox.addItems(palettelist)
        self.transferpalettecombobox.setCurrentIndex(-1)

    #applies a pattern of colors
    @pyqtSlot(int)
    def colorizebuttons(self, pattern:int = 0) -> None:
        if self.changingcolorflag:
            n = self.colorSpinBox.value()
            self.colorSpinBox.setValue(int(n-1))
            return
        self.changingcolorflag = True

        if not pattern:
            pattern = self.colorSpinBox.value()

        ncolumns = self.aw.buttonlistmaxlen
        nbuttons = len(self.extraeventstypes)

        nrows,extra = divmod(nbuttons,ncolumns)

        step = pattern
        bcolor = []

        if extra:
            nrows += 1
        gap = int(-1*(230-50)/ncolumns)
        #Color
        for _ in range(nrows):
            for f in range(230,50,gap):
                color = QColor()
                color.setHsv(step,255,f,255)
                bcolor.append(str(color.name()))
            step += pattern*2

        #Apply Colors in Right Order
        for i in range(nbuttons):
            visualIndex = self.eventbuttontable.visualRow(i)
            self.extraeventbuttoncolor[i] = bcolor[visualIndex]
            #Choose text color
            if self.aw.colorDifference('white', bcolor[visualIndex]) > self.aw.colorDifference('black',bcolor[visualIndex]):
                self.extraeventbuttontextcolor[i] = 'white'
            else:
                self.extraeventbuttontextcolor[i] = 'black'
        self.changingcolorflag = False
        self.createEventbuttonTable()

    @pyqtSlot(int)
    def seteventmarker0(self, _:int) -> None:
        self.seteventmarker(0)
    @pyqtSlot(int)
    def seteventmarker1(self,_:int) -> None:
        self.seteventmarker(1)
    @pyqtSlot(int)
    def seteventmarker2(self,_:int) -> None:
        self.seteventmarker(2)
    @pyqtSlot(int)
    def seteventmarker3(self,_:int) -> None:
        self.seteventmarker(3)

    def seteventmarker(self, m:int) -> None:
        if m == 0 and self.marker1typeComboBox.currentIndex() != 0:
            self.aw.qmc.EvalueMarker[m] = str(self.markervals[self.marker1typeComboBox.currentIndex()])
        if m == 1 and self.marker2typeComboBox.currentIndex() != 0:
            self.aw.qmc.EvalueMarker[m] = str(self.markervals[self.marker2typeComboBox.currentIndex()])
        if m == 2 and self.marker3typeComboBox.currentIndex() != 0:
            self.aw.qmc.EvalueMarker[m] = str(self.markervals[self.marker3typeComboBox.currentIndex()])
        if m == 3 and self.marker4typeComboBox.currentIndex() != 0:
            self.aw.qmc.EvalueMarker[m] = str(self.markervals[self.marker4typeComboBox.currentIndex()])
        self.aw.qmc.redraw()

    @pyqtSlot(bool)
    def setcoloreventline0(self, _:bool = False) -> None:
        self.setcoloreventline(0)
    @pyqtSlot(bool)
    def setcoloreventline1(self,_:bool = False) -> None:
        self.setcoloreventline(1)
    @pyqtSlot(bool)
    def setcoloreventline2(self,_:bool = False) -> None:
        self.setcoloreventline(2)
    @pyqtSlot(bool)
    def setcoloreventline3(self,_:bool = False) -> None:
        self.setcoloreventline(3)

    def setcoloreventline(self, b:int) -> None:
        colorf = self.aw.colordialog(QColor(self.aw.qmc.EvalueColor[b]))
        if colorf.isValid():
            colorname = str(colorf.name())
            self.aw.qmc.EvalueColor[b] = colorname
            self.aw.updateSliderColors()
            self.updateStyleTab()
            self.aw.qmc.redraw()

    @pyqtSlot(bool)
    def setcoloreventtext0(self, _:bool = False) -> None:
        self.setcoloreventtext(0)
    @pyqtSlot(bool)
    def setcoloreventtext1(self,_:bool = False) -> None:
        self.setcoloreventtext(1)
    @pyqtSlot(bool)
    def setcoloreventtext2(self,_:bool = False) -> None:
        self.setcoloreventtext(2)
    @pyqtSlot(bool)
    def setcoloreventtext3(self,_:bool = False) -> None:
        self.setcoloreventtext(3)

    def setcoloreventtext(self, b:int) -> None:
        colorf = self.aw.colordialog(QColor(self.aw.qmc.EvalueTextColor[b]))
        if colorf.isValid():
            colorname = str(colorf.name())
            self.aw.qmc.EvalueTextColor[b] = colorname
            self.aw.updateSliderColors()
            self.updateStyleTab()
            self.aw.qmc.redraw()

    @pyqtSlot(int)
    def setbuttonlistmaxlen(self, _:int) -> None:
        self.aw.buttonlistmaxlen = self.nbuttonsSpinBox.value()

    def createEventbuttonTable(self) -> None:
        columns = 9
        if self.eventbuttontable is not None and self.eventbuttontable.columnCount() == columns:
            # rows have been already established
            # save the current columnWidth to reset them afte table creation
            self.aw.eventbuttontablecolumnwidths = [self.eventbuttontable.columnWidth(c) for c in range(self.eventbuttontable.columnCount())]

        self.nbuttonsSpinBox.setValue(int(self.aw.buttonlistmaxlen))
        nbuttons = len(self.extraeventstypes)

        # self.eventbuttontable.clear() # this crashes Ubuntu 16.04
#        if ndata != 0:
#            self.eventbuttontable.clearContents() # this crashes Ubuntu 16.04 if device table is empty and also sometimes else
#        self.eventbuttontable.clearSelection() # this seems to work also for Ubuntu 16.04

        self.eventbuttontable.setRowCount(nbuttons)
        self.eventbuttontable.setColumnCount(columns)
        self.eventbuttontable.setHorizontalHeaderLabels([QApplication.translate('Table','Label'),
                                                         QApplication.translate('Table','Description'),
                                                         QApplication.translate('Table','Type'),
                                                         QApplication.translate('Table','Value'),
                                                         QApplication.translate('Table','Action'),
                                                         QApplication.translate('Table','Documentation'),
                                                         QApplication.translate('Table','Visibility'),
                                                         QApplication.translate('Table','Color'),
                                                         QApplication.translate('Table','Text Color')
                                                         #,''
                                                         ])
        self.eventbuttontable.setAlternatingRowColors(True)
        self.eventbuttontable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.eventbuttontable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.eventbuttontable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.eventbuttontable.setShowGrid(True)

        #Enable Drag Sorting
        self.eventbuttontable.setDragEnabled(False) # content not draggable, only vertical header!
        self.eventbuttontable.setAutoScroll(False)

        vheader = self.eventbuttontable.verticalHeader()
        if vheader is not None:
            vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            vheader.setSectionsMovable(True)
            vheader.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
            vheader.setAutoScroll(False)

        visibility = [QApplication.translate('ComboBox','OFF'),
                      QApplication.translate('ComboBox','ON')]

        std_extra_events = [self.etype0.text(),self.etype1.text(),self.etype2.text(),self.etype3.text(),'--']
        std_extra_events += [uchr(177) + e for e in std_extra_events[:-1]] # chr(241)
        std_extra_events.insert(0,QApplication.translate('Label', '')) # we prepend the empty item that does not create an event entry


        for i in range(nbuttons):
            #0 label
            labeledit = QLineEdit(self.extraeventslabels[i].replace(chr(10),'\\n'))
            labeledit.editingFinished.connect(self.setlabeleventbutton)

            #1 Description
            descriptionedit = QLineEdit(self.extraeventsdescriptions[i])
            descriptionedit.editingFinished.connect(self.setdescriptioneventbutton)

            #2 Type
            typeComboBox = MyQComboBox()
            typeComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            typeComboBox.addItems(std_extra_events)
            if self.extraeventstypes[i] == 9:  # we add an offset of +1 here to jump over the new EVENT entry
                idx = 5
            elif self.extraeventstypes[i] == 4:
                idx = 0
            else:
                idx = self.extraeventstypes[i]+1

            typeComboBox.setCurrentIndex(idx)
            typeComboBox.currentIndexChanged.connect(self.settypeeventbutton)

            #3 Values
            valueEdit = QLineEdit()
#            valueEdit.setValidator(QRegExpValidator(QRegExp(r"^100|\-?\d?\d?$"),self)) # QRegExp(r"^100|\d?\d?$"),self))
            valueEdit.setValidator(QIntValidator(-999, 999, valueEdit))
            valueEdit.setText(self.aw.qmc.eventsvalues(self.extraeventsvalues[i]))
            valueEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
            valueEdit.editingFinished.connect(self.setvalueeventbutton)

            #4 Action
            actionComboBox = MyQComboBox()
            actionComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            actionComboBox.addItems(self.custom_button_actions_sorted)
            act = self.extraeventsactions[i]
            if act > 7:
                act = act - 1
            actionComboBox.setCurrentIndex(self.custom_button_actions_sorted.index(self.custom_button_actions[act]))
            actionComboBox.currentIndexChanged.connect(self.setactioneventbutton)

            #5 Action Description
            actiondescriptionedit = QLineEdit(self.extraeventsactionstrings[i])
            actiondescriptionedit.editingFinished.connect(self.setactiondescriptioneventbutton)

            #6 Visibility
            visibilityComboBox =  MyQComboBox()
            visibilityComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            visibilityComboBox.addItems(visibility)
            visibilityComboBox.setCurrentIndex(self.extraeventsvisibility[i])
            visibilityComboBox.currentIndexChanged.connect(self.setvisibilitytyeventbutton)
            #7 Color
            colorButton = QPushButton('Select')
            colorButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            colorButton.clicked.connect(self.setbuttoncolor)
            label = self.extraeventslabels[i][:]
            et = self.extraeventstypes[i]
            label = self.aw.substButtonLabel(-1,label,et, self.extraeventsvalues[i])
            colorButton.setText(label)
            colorButton.setStyleSheet(f'border: none; outline: none; background-color: {self.extraeventbuttoncolor[i]}; color: {self.extraeventbuttontextcolor[i]};')
            #8 Text Color
            colorTextButton = QPushButton('Select')
            colorTextButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            colorTextButton.clicked.connect(self.setbuttontextcolor)
            colorTextButton.setText(label)
            colorTextButton.setStyleSheet(f'border: none; outline: none; background-color: {self.extraeventbuttoncolor[i]}; color: {self.extraeventbuttontextcolor[i]};')
            #add widgets to the table
            self.eventbuttontable.setCellWidget(i,0,labeledit)
            self.eventbuttontable.setCellWidget(i,1,descriptionedit)
            self.eventbuttontable.setCellWidget(i,2,typeComboBox)
            self.eventbuttontable.setCellWidget(i,3,valueEdit)
            self.eventbuttontable.setCellWidget(i,4,actionComboBox)
            self.eventbuttontable.setCellWidget(i,5,actiondescriptionedit)
            self.eventbuttontable.setCellWidget(i,6,visibilityComboBox)
            self.eventbuttontable.setCellWidget(i,7,colorButton)
            self.eventbuttontable.setCellWidget(i,8,colorTextButton)


        hheader = self.eventbuttontable.horizontalHeader()
        if hheader is not None:
            hheader.setStretchLastSection(False)
            self.eventbuttontable.resizeColumnsToContents()
            hheader.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
            hheader.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
            hheader.resizeSection(6, hheader.sectionSize(6) + 15)
            hheader.resizeSection(7, self.aw.standard_button_min_width_px)
            hheader.resizeSection(8, self.aw.standard_button_min_width_px)

        self.eventbuttontable.setColumnWidth(0,70)
        self.eventbuttontable.setColumnWidth(1,80)
        self.eventbuttontable.setColumnWidth(2,100)
        self.eventbuttontable.setColumnWidth(3,50)
        self.eventbuttontable.setColumnWidth(4,150)

        # remember the columnwidth
        for i, _ in enumerate(self.aw.eventbuttontablecolumnwidths):
            if i not in [5,6,7,8]:
                try:
                    self.eventbuttontable.setColumnWidth(i,self.aw.eventbuttontablecolumnwidths[i])
                except Exception: # pylint: disable=broad-except
                    pass

    @pyqtSlot(bool)
    def copyEventButtonTabletoClipboard(self, _:bool=False) -> None:
        import prettytable
        nrows = self.eventbuttontable.rowCount()
        ncols = self.eventbuttontable.columnCount()
        clipboard = ''
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.AltModifier:  #alt click
            tbl = prettytable.PrettyTable()
            fields = []
            fields.append(' ')  # this column shows the row number
            for c in range(ncols):
                item = self.eventbuttontable.horizontalHeaderItem(c)
                if item is not None:
                    fields.append(item.text())
            tbl.field_names = fields
            for r in range(nrows):
                rows = []
                rows.append(str(r+1))
                # label
                labeledit = cast(QLineEdit, self.eventbuttontable.cellWidget(r,0))
                rows.append(labeledit.text())
                # description
                descriptionedit = cast(QLineEdit, self.eventbuttontable.cellWidget(r,1))
                rows.append(descriptionedit.text())
                # type
                typeComboBox = cast(MyQComboBox, self.eventbuttontable.cellWidget(r,2))
                rows.append(typeComboBox.currentText())
                # value
                valueEdit = cast(QLineEdit, self.eventbuttontable.cellWidget(r,3))
                rows.append(valueEdit.text())
                # action
                actionComboBox = cast(MyQComboBox, self.eventbuttontable.cellWidget(r,4))
                rows.append(actionComboBox.currentText())
                # action description
                actiondescriptionedit = cast(QLineEdit, self.eventbuttontable.cellWidget(r,5))
                rows.append(actiondescriptionedit.text())
                # visibility
                visibilityComboBox = cast(MyQComboBox, self.eventbuttontable.cellWidget(r,6))
                rows.append(visibilityComboBox.currentText())
                # color
                colorButton = cast(QPushButton, self.eventbuttontable.cellWidget(r,7))
                rows.append(colorButton.palette().button().color().name())
                # text color
                colorTextButton = cast(QPushButton, self.eventbuttontable.cellWidget(r,8))
                rows.append(colorTextButton.palette().button().color().name())
                tbl.add_row(rows)
            clipboard = tbl.get_string()
        else:
            clipboard += ' ' + '\t'  # this column shows the row number
            for c in range(ncols):
                item = self.eventbuttontable.horizontalHeaderItem(c)
                if item is not None:
                    clipboard += item.text()
                    if c != (ncols-1):
                        clipboard += '\t'
            clipboard += '\n'
            for r in range(nrows):
                clipboard += str(r+1) + '\t'
                labeledit = cast(QLineEdit, self.eventbuttontable.cellWidget(r,0))
                clipboard += labeledit.text() + '\t'
                descriptionedit = cast(QLineEdit, self.eventbuttontable.cellWidget(r,1))
                clipboard += descriptionedit.text() + '\t'
                typeComboBox = cast(MyQComboBox, self.eventbuttontable.cellWidget(r,2))
                clipboard += typeComboBox.currentText() + '\t'
                valueEdit = cast(QLineEdit, self.eventbuttontable.cellWidget(r,3))
                clipboard += valueEdit.text() + '\t'
                actionComboBox = cast(MyQComboBox, self.eventbuttontable.cellWidget(r,4))
                clipboard += actionComboBox.currentText() + '\t'
                actiondescriptionedit = cast(QLineEdit, self.eventbuttontable.cellWidget(r,5))
                clipboard += actiondescriptionedit.text() + '\t'
                visibilityComboBox = cast(MyQComboBox, self.eventbuttontable.cellWidget(r,6))
                clipboard += visibilityComboBox.currentText() + '\t'
                colorButton = cast(QPushButton, self.eventbuttontable.cellWidget(r,7))
                clipboard += colorButton.palette().button().color().name() + '\t'
                colorTextButton = cast(QPushButton, self.eventbuttontable.cellWidget(r,8))
                clipboard += colorTextButton.palette().button().color().name() + '\n'
        # copy to the system clipboard
        sys_clip = QApplication.clipboard()
        if sys_clip is not None:
            sys_clip.setText(clipboard)
        self.aw.sendmessage(QApplication.translate('Message','Event Button table copied to clipboard'))


    def savetableextraeventbutton(self) -> None:
        maxButton = len(self.extraeventstypes)
        #Clean Lists:
        #Labels
        self.aw.extraeventslabels         = [''] * maxButton
        #Description
        self.aw.extraeventsdescriptions   = [''] * maxButton
        #Types
        self.aw.extraeventstypes          = [4] * maxButton
        #Values
        self.aw.extraeventsvalues         = [0.] * maxButton
        #Actions
        self.aw.extraeventsactions        = [0] * maxButton
        #Action Description
        self.aw.extraeventsactionstrings  = [''] * maxButton
        #Visibility
        self.aw.extraeventsvisibility     = [1] * maxButton
        #Color
        self.aw.extraeventbuttoncolor     = ['#808080'] * maxButton
        #Text Color
        self.aw.extraeventbuttontextcolor = ['white'] * maxButton

        #Sorting buttons based on the visualRow
        for i in range(maxButton):
            visualIndex = i #self.eventbuttontable.visualRow(i)

            #Labels
            self.aw.extraeventslabels[visualIndex]         = self.extraeventslabels[i]
            #Description
            self.aw.extraeventsdescriptions[visualIndex]   = self.extraeventsdescriptions[i]
            #Types
            self.aw.extraeventstypes[visualIndex]          = self.extraeventstypes[i]
            #Values
            self.aw.extraeventsvalues[visualIndex]         = self.extraeventsvalues[i]
            #Actions
            self.aw.extraeventsactions[visualIndex]        = self.extraeventsactions[i]
            #Action Description
            self.aw.extraeventsactionstrings[visualIndex]  = self.extraeventsactionstrings[i]
            #Visibility
            self.aw.extraeventsvisibility[visualIndex]     = self.extraeventsvisibility[i]
            #Color
            self.aw.extraeventbuttoncolor[visualIndex]     = self.extraeventbuttoncolor[i]
            #Text Color
            self.aw.extraeventbuttontextcolor[visualIndex] = self.extraeventbuttontextcolor[i]

        #Apply Event Button Changes
        self.aw.update_extraeventbuttons_visibility()
        self.aw.realignbuttons()
        self.aw.settooltip() # has to be done after realignbuttons() to have set the aw.buttonlist correctly!

    @pyqtSlot()
    def setlabeleventbutton(self) -> None:
        i = self.aw.findWidgetsRow(self.eventbuttontable,self.sender(),0)
        if i is not None:
            labeledit = cast(QLineEdit, self.eventbuttontable.cellWidget(i,0))
            label = labeledit.text()
            label = label.replace('\\n', chr(10))
            if i < len(self.extraeventslabels):
                self.extraeventslabels[i] = label
                label = self.aw.substButtonLabel(-1, label, self.extraeventstypes[i], self.extraeventsvalues[i])
            #Update Color Buttons
            colorButton = cast(QPushButton, self.eventbuttontable.cellWidget(i,7))
            colorButton.setText(label)
            colorTextButton = cast(QPushButton, self.eventbuttontable.cellWidget(i,8))
            colorTextButton.setText(label)

    @pyqtSlot()
    def setdescriptioneventbutton(self) -> None:
        i = self.aw.findWidgetsRow(self.eventbuttontable,self.sender(),1)
        if i is not None:
            descriptionedit = cast(QLineEdit, self.eventbuttontable.cellWidget(i,1))
            if i < len(self.extraeventsdescriptions):
                self.extraeventsdescriptions[i] = descriptionedit.text()

    @pyqtSlot(int)
    def settypeeventbutton(self, _:int) -> None:
        i = self.aw.findWidgetsRow(self.eventbuttontable,self.sender(),2)
        if i is not None:
            typecombobox = cast(MyQComboBox, self.eventbuttontable.cellWidget(i,2))
            evType = typecombobox.currentIndex() - 1 # we remove again the offset of 1 here to jump over the new EVENT entry
            if i < len(self.extraeventstypes):
                if evType == -1:
                    evType = 4 # and map the first entry to 4
                elif evType == 4:
                    evType = 9 # and map the entry 4 to 9
                self.extraeventstypes[i] = evType
            labeledit = cast(QLineEdit, self.eventbuttontable.cellWidget(i,0))
            label = labeledit.text()
            label = label.replace('\\n', chr(10))
            if i < len(self.extraeventslabels):
                self.extraeventslabels[i] = label
                label = self.aw.substButtonLabel(-1, label, self.extraeventstypes[i], self.extraeventsvalues[i])
            #Update Color Buttons
            colorButton = cast(QPushButton, self.eventbuttontable.cellWidget(i,7))
            colorButton.setText(label)
            colorTextButton = cast(QPushButton, self.eventbuttontable.cellWidget(i,8))
            colorTextButton.setText(label)

    @pyqtSlot()
    def setvalueeventbutton(self) -> None:
        i = self.aw.findWidgetsRow(self.eventbuttontable,self.sender(),3)
        if i is not None:
            valueedit = cast(QLineEdit, self.eventbuttontable.cellWidget(i,3))
            if i < len(self.extraeventsvalues):
                self.extraeventsvalues[i] = self.aw.qmc.str2eventsvalue(str(valueedit.text()))
                labeledit = cast(QLineEdit, self.eventbuttontable.cellWidget(i,0))
                label = labeledit.text()
                label = label.replace('\\n', chr(10))
                if i < len(self.extraeventslabels):
                    self.extraeventslabels[i] = label
                    label = self.aw.substButtonLabel(-1, label, self.extraeventstypes[i], self.extraeventsvalues[i])
                #Update Color Buttons
                colorButton = cast(QPushButton, self.eventbuttontable.cellWidget(i,7))
                colorButton.setText(label)
                colorTextButton = cast(QPushButton, self.eventbuttontable.cellWidget(i,8))
                colorTextButton.setText(label)


    @pyqtSlot(int)
    def setactioneventbutton(self, _:int) -> None:
        i = self.aw.findWidgetsRow(self.eventbuttontable,self.sender(),4)
        if i is not None:
            actioncombobox = cast(MyQComboBox, self.eventbuttontable.cellWidget(i,4))
            if i < len(self.extraeventsactions):
                self.extraeventsactions[i] = self.custom_button_actions.index(self.custom_button_actions_sorted[actioncombobox.currentIndex()])
                if self.extraeventsactions[i] > 6: # increase action type as 7=CallProgramWithArg is not available for buttons
                    self.extraeventsactions[i] = self.extraeventsactions[i] + 1

    @pyqtSlot()
    def setactiondescriptioneventbutton(self) -> None:
        i = self.aw.findWidgetsRow(self.eventbuttontable,self.sender(),5)
        if i is not None:
            actiondescriptionedit = cast(QLineEdit, self.eventbuttontable.cellWidget(i,5))
            if i < len(self.extraeventsactionstrings):
                self.extraeventsactionstrings[i] = actiondescriptionedit.text()

    @pyqtSlot(int)
    def setvisibilitytyeventbutton(self, _:int) -> None:
        i = self.aw.findWidgetsRow(self.eventbuttontable,self.sender(),6)
        if i is not None:
            visibilityComboBox = cast(MyQComboBox, self.eventbuttontable.cellWidget(i,6))
            if i < len(self.extraeventsvisibility):
                self.extraeventsvisibility[i] = visibilityComboBox.currentIndex()

    @pyqtSlot(bool)
    def setbuttoncolor(self, _:bool = False) -> None:
        i = self.aw.findWidgetsRow(self.eventbuttontable,self.sender(),7)
        if i is not None and i < len(self.extraeventbuttoncolor):
            colorf = self.aw.colordialog(QColor(self.extraeventbuttoncolor[i]))
            if colorf.isValid():
                self.extraeventbuttoncolor[i] = str(colorf.name())
                textColor = self.extraeventbuttontextcolor[i]
                backColor =  self.extraeventbuttoncolor[i]
                label = self.extraeventslabels[i]
                style = f'border: none; outline: none; background-color: {backColor}; color: {textColor};'
                widget7 = self.eventbuttontable.cellWidget(i,7)
                if widget7 is not None:
                    widget7.setStyleSheet(style)
                widget8 = self.eventbuttontable.cellWidget(i,8)
                if widget8 is not None:
                    widget8.setStyleSheet(style)
                self.aw.checkColors([(QApplication.translate('Label','Event button')+' '+ label, backColor, ' '+QApplication.translate('Label','its text'), textColor)])

    @pyqtSlot(bool)
    def setbuttontextcolor(self, _:bool = False) -> None:
        i = self.aw.findWidgetsRow(self.eventbuttontable,self.sender(),8)
        if i is not None and i < len(self.extraeventbuttontextcolor):
            colorf = self.aw.colordialog(QColor(self.extraeventbuttontextcolor[i]))
            if colorf.isValid():
                self.extraeventbuttontextcolor[i] = str(colorf.name())
                textColor = self.extraeventbuttontextcolor[i]
                backColor =  self.extraeventbuttoncolor[i]
                label = self.extraeventslabels[i]
                style = f'border: none; outline: none; background-color: {backColor}; color: {textColor};'
                widget7 = self.eventbuttontable.cellWidget(i,7)
                if widget7 is not None:
                    widget7.setStyleSheet(style)
                widget8 = self.eventbuttontable.cellWidget(i,8)
                if widget8 is not None:
                    widget8.setStyleSheet(style)
                self.aw.checkColors([(QApplication.translate('Label','Event button')+' '+ label, backColor, ' '+QApplication.translate('Label','its text'),textColor)])

    def disconnectTableItemActions(self) -> None:
        for x in range(self.eventbuttontable.rowCount()):
            try:
                #
                labeledit = cast(QLineEdit, self.eventbuttontable.cellWidget(x,0))
                labeledit.editingFinished.disconnect() # label edit
                #
                descriptionedit = cast(QLineEdit, self.eventbuttontable.cellWidget(x,1))
                descriptionedit.editingFinished.disconnect() # description edit
                #
                typeComboBox = cast(MyQComboBox, self.eventbuttontable.cellWidget(x,2))
                typeComboBox.currentIndexChanged.disconnect() # type combo
                #
                valueEdit = cast(QLineEdit, self.eventbuttontable.cellWidget(x,3))
                valueEdit.editingFinished.disconnect() # value edit
                #
                actionComboBox = cast(MyQComboBox, self.eventbuttontable.cellWidget(x,4))
                actionComboBox.currentIndexChanged.disconnect() # action combo
                #
                actiondescriptionedit = cast(QLineEdit, self.eventbuttontable.cellWidget(x,5))
                actiondescriptionedit.editingFinished.disconnect() # action description
                #
                visibilityComboBox = cast(MyQComboBox, self.eventbuttontable.cellWidget(x,6))
                visibilityComboBox.currentIndexChanged.disconnect() # visibility combo
                #
                colorButton = cast(QPushButton, self.eventbuttontable.cellWidget(x,7))
                colorButton.clicked.disconnect() # color button
                #
                colorTextButton = cast(QPushButton, self.eventbuttontable.cellWidget(x,8))
                colorTextButton.clicked.disconnect() # color text button
            except Exception: # pylint: disable=broad-except
                pass

    @pyqtSlot(bool)
    def delextraeventbutton(self, _:bool = False) -> None:
        bindex = len(self.extraeventstypes)-1
        selected = self.eventbuttontable.selectedRanges()

        if len(selected) > 0:
            bindex = selected[0].topRow()

        if bindex >= 0:
            self.disconnectTableItemActions() # we ensure that signals from to be deleted items are not fired anymore
            self.extraeventslabels.pop(bindex)
            self.extraeventsdescriptions.pop(bindex)
            self.extraeventstypes.pop(bindex)
            self.extraeventsvalues.pop(bindex)
            self.extraeventsactions.pop(bindex)
            self.extraeventsactionstrings.pop(bindex)
            self.extraeventsvisibility.pop(bindex)
            self.extraeventbuttoncolor.pop(bindex)
            self.extraeventbuttontextcolor.pop(bindex)

            self.createEventbuttonTable()

    @pyqtSlot(bool)
    def addextraeventbuttonSlot(self, _:bool = False) -> None:
        self.insertextraeventbutton()

    @pyqtSlot(bool)
    def insertextraeventbuttonSlot(self, _:bool = False) -> None:
        self.insertextraeventbutton(True)

    def insertextraeventbutton(self, insert:bool = False) -> None:
        if len(self.extraeventstypes) >= self.aw.buttonlistmaxlen * 4: # max 4 rows of buttons of buttonlistmaxlen
            return
        try:
            focusWidget = QApplication.focusWidget()
            if focusWidget is not None and isinstance(focusWidget, QLineEdit):
                fw:QLineEdit = focusWidget
                fw.editingFinished.emit()
        except Exception: # pylint: disable=broad-except
            pass

        bindex = len(self.extraeventstypes)
        selected = self.eventbuttontable.selectedRanges()

        # defaults for new entries
        event_description:str = ''
        event_type:int = 4
        event_value:float = 0.
        event_action:int = 0
        event_string:str = ''
        event_visibility:int = 1
        event_buttoncolor:str = '#808080'
        event_textcolor:str = 'white'
        event_label:str = 'E'

        if len(selected) > 0:
            selected_idx = selected[0].topRow()
            if insert:
                bindex = selected_idx
            try:
                event_description = self.extraeventsdescriptions[selected_idx]
                event_type = self.extraeventstypes[selected_idx]
                event_value = self.extraeventsvalues[selected_idx]
                event_action = self.extraeventsactions[selected_idx]
                event_string = self.extraeventsactionstrings[selected_idx]
                event_visibility = self.extraeventsvisibility[selected_idx]
                event_buttoncolor = self.extraeventbuttoncolor[selected_idx]
                event_textcolor = self.extraeventbuttontextcolor[selected_idx]
                event_label = self.extraeventslabels[selected_idx]
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)

        if bindex >= 0:
            self.extraeventsdescriptions.insert(bindex,event_description)
            self.extraeventstypes.insert(bindex,event_type)
            self.extraeventsvalues.insert(bindex,event_value)
            self.extraeventsactions.insert(bindex,event_action)
            self.extraeventsactionstrings.insert(bindex,event_string)
            self.extraeventsvisibility.insert(bindex,event_visibility)
            self.extraeventbuttoncolor.insert(bindex,event_buttoncolor)
            self.extraeventbuttontextcolor.insert(bindex,event_textcolor)
            self.extraeventslabels.insert(bindex,event_label)

            self.createEventbuttonTable()

    @pyqtSlot(int)
    def eventsbuttonflagChanged(self, _:int) -> None:
        if self.eventsbuttonflag.isChecked():
            self.aw.buttonEVENT.setVisible(True)
            self.aw.eventsbuttonflag = 1
        else:
            self.aw.buttonEVENT.setVisible(False)
            self.aw.eventsbuttonflag = 0

    @pyqtSlot(int)
    def eventsclampflagChanged(self, _:int) -> None:
        if self.eventsclampflag.isChecked():
            self.aw.qmc.clampEvents = True
        else:
            self.aw.qmc.clampEvents = False
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def chargeTimerStateChanged(self, _:int) -> None:
        if self.chargeTimer.isChecked():
            self.chargeTimerSpinner.setEnabled(True)
        else:
            self.chargeTimerSpinner.setEnabled(False)
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def eventslabelsflagChanged(self, _:int) -> None:
        if self.eventslabelsflag.isChecked():
            self.aw.qmc.renderEventsDescr = True
            self.eventslabelscharsSpinner.setEnabled(True)
        else:
            self.aw.qmc.renderEventsDescr = False
            self.eventslabelscharsSpinner.setEnabled(False)
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def annotationsflagChanged(self, _:int) -> None:
        if self.annotationsflagbox.isChecked():
            self.aw.qmc.annotationsflag = 1
        else:
            self.aw.qmc.annotationsflag = 0
            # we clear the custom annotation positions on deactivation
            self.aw.qmc.l_annotations_dict = {}
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def showeventsonbtChanged(self, _:int) -> None:
        if self.showeventsonbtbox.isChecked():
            self.aw.qmc.showeventsonbt = True
        else:
            self.aw.qmc.showeventsonbt = False
        self.aw.qmc.l_event_flags_dict = {} # clear the custom event flag position cache
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def changeShowEtypes0(self, _:int) -> None:
        self.changeShowEtypes(0)
    @pyqtSlot(int)
    def changeShowEtypes1(self, _:int) -> None:
        self.changeShowEtypes(1)
    @pyqtSlot(int)
    def changeShowEtypes2(self, _:int) -> None:
        self.changeShowEtypes(2)
    @pyqtSlot(int)
    def changeShowEtypes3(self, _:int) -> None:
        self.changeShowEtypes(3)
    @pyqtSlot(int)
    def changeShowEtypes4(self, _:int) -> None:
        self.changeShowEtypes(4)

    def changeShowEtypes(self, etype:int) -> None:
        self.aw.qmc.showEtypes[etype] = not self.aw.qmc.showEtypes[etype]
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    @pyqtSlot(int)
    def eventsGraphTypeflagChanged(self, _:int) -> None:
        self.aw.qmc.eventsGraphflag = self.bartypeComboBox.currentIndex() - 1
        if self.aw.qmc.eventsGraphflag > 1:
            self.eventsclampflag.setEnabled(True)
        else:
            self.eventsclampflag.setEnabled(False)
        if self.aw.qmc.eventsGraphflag == -1:
            # we clear the custom annotation positions on deactivation
            self.aw.qmc.l_event_flags_dict = {}
            self.aw.qmc.eventsGraphflag = 0
            self.aw.qmc.eventsshowflag = 0
        else:
            self.aw.qmc.eventsshowflag = 1
        self.aw.qmc.redraw(recomputeAllDeltas=False)

    def saveSliderSettings(self) -> None:
        self.aw.eventslidervisibilities[0] = int(self.E1visibility.isChecked())
        self.aw.eventslidervisibilities[1] = int(self.E2visibility.isChecked())
        self.aw.eventslidervisibilities[2] = int(self.E3visibility.isChecked())
        self.aw.eventslidervisibilities[3] = int(self.E4visibility.isChecked())
        self.aw.eventslideractions[0] = self.sliderActionTypes.index(self.sliderActionTypesSorted[self.E1action.currentIndex()])
        self.aw.eventslideractions[1] = self.sliderActionTypes.index(self.sliderActionTypesSorted[self.E2action.currentIndex()])
        self.aw.eventslideractions[2] = self.sliderActionTypes.index(self.sliderActionTypesSorted[self.E3action.currentIndex()])
        self.aw.eventslideractions[3] = self.sliderActionTypes.index(self.sliderActionTypesSorted[self.E4action.currentIndex()])
        self.aw.eventslidercommands[0] = self.E1command.text()
        self.aw.eventslidercommands[1] = self.E2command.text()
        self.aw.eventslidercommands[2] = self.E3command.text()
        self.aw.eventslidercommands[3] = self.E4command.text()
        self.aw.eventslideroffsets[0] = self.E1offset.value()
        self.aw.eventslideroffsets[1] = self.E2offset.value()
        self.aw.eventslideroffsets[2] = self.E3offset.value()
        self.aw.eventslideroffsets[3] = self.E4offset.value()
        self.aw.eventsliderfactors[0] = float(self.E1factor.value())
        if self.aw.eventsliderfactors[0] == 0: # a zero does not make much sense and might be a user error
            self.aw.eventsliderfactors[0] = 1.0
        self.aw.eventsliderfactors[1] = float(self.E2factor.value())
        if self.aw.eventsliderfactors[1] == 1: # a zero does not make much sense and might be a user error
            self.aw.eventsliderfactors[1] = 1.0
        self.aw.eventsliderfactors[2] = float(self.E3factor.value())
        if self.aw.eventsliderfactors[2] == 1: # a zero does not make much sense and might be a user error
            self.aw.eventsliderfactors[2] = 1.0
        self.aw.eventsliderfactors[3] = float(self.E4factor.value())
        if self.aw.eventsliderfactors[3] == 1: # a zero does not make much sense and might be a user error
            self.aw.eventsliderfactors[3] = 1.0
        self.aw.eventslidermin[0] = int(min(self.E1_min.value(),self.E1_max.value()))
        self.aw.eventslidermin[1] = int(min(self.E2_min.value(),self.E2_max.value()))
        self.aw.eventslidermin[2] = int(min(self.E3_min.value(),self.E3_max.value()))
        self.aw.eventslidermin[3] = int(min(self.E4_min.value(),self.E4_max.value()))
        self.aw.eventslidermax[0] = int(max(self.E1_min.value(),self.E1_max.value()))
        self.aw.eventslidermax[1] = int(max(self.E2_min.value(),self.E2_max.value()))
        self.aw.eventslidermax[2] = int(max(self.E3_min.value(),self.E3_max.value()))
        self.aw.eventslidermax[3] = int(max(self.E4_min.value(),self.E4_max.value()))
        self.aw.eventsliderBernoulli[0] = int(self.E1slider_bernoulli.isChecked())
        self.aw.eventsliderBernoulli[1] = int(self.E2slider_bernoulli.isChecked())
        self.aw.eventsliderBernoulli[2] = int(self.E3slider_bernoulli.isChecked())
        self.aw.eventsliderBernoulli[3] = int(self.E4slider_bernoulli.isChecked())
        self.aw.eventslidercoarse[0] = self.slidercoarse2stepSizePos(self.E1slider_step.currentIndex())
        self.aw.eventslidercoarse[1] = self.slidercoarse2stepSizePos(self.E2slider_step.currentIndex())
        self.aw.eventslidercoarse[2] = self.slidercoarse2stepSizePos(self.E3slider_step.currentIndex())
        self.aw.eventslidercoarse[3] = self.slidercoarse2stepSizePos(self.E4slider_step.currentIndex())
        self.aw.eventslidertemp[0] = int(self.E1slider_temp.isChecked())
        self.aw.eventslidertemp[1] = int(self.E2slider_temp.isChecked())
        self.aw.eventslidertemp[2] = int(self.E3slider_temp.isChecked())
        self.aw.eventslidertemp[3] = int(self.E4slider_temp.isChecked())
        self.aw.eventsliderunits[0] = self.E1unit.text()
        self.aw.eventsliderunits[1] = self.E2unit.text()
        self.aw.eventsliderunits[2] = self.E3unit.text()
        self.aw.eventsliderunits[3] = self.E4unit.text()
        self.aw.updateSliderMinMax()
        self.aw.slidersAction.setEnabled(any(self.aw.eventslidervisibilities) or self.aw.pidcontrol.svSlider)

    def saveQuantifierSettings(self) -> None:
        self.aw.clusterEventsFlag = bool(self.clusterEventsFlag.isChecked())
        self.aw.eventquantifieractive[0] = int(self.E1active.isChecked())
        self.aw.eventquantifieractive[1] = int(self.E2active.isChecked())
        self.aw.eventquantifieractive[2] = int(self.E3active.isChecked())
        self.aw.eventquantifieractive[3] = int(self.E4active.isChecked())
        self.aw.eventquantifiercoarse[0] = self.slidercoarse2stepSizePos(self.E1coarse.currentIndex())
        self.aw.eventquantifiercoarse[1] = self.slidercoarse2stepSizePos(self.E2coarse.currentIndex())
        self.aw.eventquantifiercoarse[2] = self.slidercoarse2stepSizePos(self.E3coarse.currentIndex())
        self.aw.eventquantifiercoarse[3] = self.slidercoarse2stepSizePos(self.E4coarse.currentIndex())
        self.aw.eventquantifieraction[0] = int(self.E1quantifieraction.isChecked())
        self.aw.eventquantifieraction[1] = int(self.E2quantifieraction.isChecked())
        self.aw.eventquantifieraction[2] = int(self.E3quantifieraction.isChecked())
        self.aw.eventquantifieraction[3] = int(self.E4quantifieraction.isChecked())
        self.aw.eventquantifierSV[0] = int(self.E1quantifierSV.isChecked())
        self.aw.eventquantifierSV[1] = int(self.E2quantifierSV.isChecked())
        self.aw.eventquantifierSV[2] = int(self.E3quantifierSV.isChecked())
        self.aw.eventquantifierSV[3] = int(self.E4quantifierSV.isChecked())
        self.aw.eventquantifiersource[0] = int(self.E1SourceComboBox.currentIndex())
        self.aw.eventquantifiersource[1] = int(self.E2SourceComboBox.currentIndex())
        self.aw.eventquantifiersource[2] = int(self.E3SourceComboBox.currentIndex())
        self.aw.eventquantifiersource[3] = int(self.E4SourceComboBox.currentIndex())
        self.aw.eventquantifiermin[0] = int(self.E1min.value())
        self.aw.eventquantifiermin[1] = int(self.E2min.value())
        self.aw.eventquantifiermin[2] = int(self.E3min.value())
        self.aw.eventquantifiermin[3] = int(self.E4min.value())
        self.aw.eventquantifiermax[0] = int(self.E1max.value())
        self.aw.eventquantifiermax[1] = int(self.E2max.value())
        self.aw.eventquantifiermax[2] = int(self.E3max.value())
        self.aw.eventquantifiermax[3] = int(self.E4max.value())
        self.aw.computeLinespaces()

    def saveAnnotationsSettings(self) -> None:
        checkedvisibilities = [0,0,0,0]
        #the following line does not work
        #checkedvisibilities = [int(self.E1AnnoVisibility.isChecked()),int(self.E3AnnoVisibility.isChecked()),int(self.E3AnnoVisibility.isChecked()),int(self.E4AnnoVisibility.isChecked())]
        checkedvisibilities[0] = int(self.E1AnnoVisibility.isChecked())
        checkedvisibilities[1] = int(self.E2Annovisibility.isChecked())
        checkedvisibilities[2] = int(self.E3Annovisibility.isChecked())
        checkedvisibilities[3] = int(self.E4Annovisibility.isChecked())
        if self.aw.qmc.specialeventannovisibilities == checkedvisibilities:
            redraw = False
        else:
            redraw = True
        self.aw.qmc.specialeventannovisibilities[0] = int(self.E1AnnoVisibility.isChecked())
        self.aw.qmc.specialeventannovisibilities[1] = int(self.E2Annovisibility.isChecked())
        self.aw.qmc.specialeventannovisibilities[2] = int(self.E3Annovisibility.isChecked())
        self.aw.qmc.specialeventannovisibilities[3] = int(self.E4Annovisibility.isChecked())
        if redraw:
            self.aw.qmc.redraw(recomputeAllDeltas=False)

    #the inverse to restoreState
    def storeState(self) -> None:
        # event configurations
        self.eventsbuttonflagstored = self.aw.eventsbuttonflag
        self.eventsshowflagstored = self.aw.qmc.eventsshowflag
        self.annotationsflagstored = self.aw.qmc.annotationsflag
        self.showeventsonbtstored = self.aw.qmc.showeventsonbt
        self.showEtypesstored = self.aw.qmc.showEtypes[:]
        self.eventsGraphflagstored = self.aw.qmc.eventsGraphflag
        self.etypesstored = self.aw.qmc.etypes
        self.etypeComboBoxstored = self.aw.etypeComboBox
        self.chargeTimerFlagstored = self.aw.qmc.chargeTimerFlag
        self.chargeTimerPeriodstored = self.aw.qmc.chargeTimerPeriod
        self.autoChargeFlagstored = self.aw.qmc.autoChargeFlag
        self.autoDropFlagstored = self.aw.qmc.autoDropFlag
        self.autoChargeModestored = self.aw.qmc.autoChargeMode
        self.autoDropModestored = self.aw.qmc.autoDropMode
        self.markTPFlagstored = self.aw.qmc.markTPflag
        self.eventsliderKeyboardControlstored = self.aw.eventsliderKeyboardControl
        self.eventsliderAlternativeLayoutstored = self.aw.eventsliderAlternativeLayout
        # buttons
        self.extraeventslabels = self.aw.extraeventslabels[:]
        self.extraeventsdescriptions = self.aw.extraeventsdescriptions[:]
        self.extraeventstypes = self.aw.extraeventstypes[:]
        self.extraeventsvalues = self.aw.extraeventsvalues[:]
        self.extraeventsactions = self.aw.extraeventsactions[:]
        self.extraeventsactionstrings = self.aw.extraeventsactionstrings[:]
        self.extraeventsvisibility = self.aw.extraeventsvisibility[:]
        self.extraeventbuttoncolor = self.aw.extraeventbuttoncolor[:]
        self.extraeventbuttontextcolor = self.aw.extraeventbuttontextcolor[:]
        self.buttonlistmaxlen = self.aw.buttonlistmaxlen
        # sliders
        self.eventslidervisibilities = self.aw.eventslidervisibilities[:]
        self.eventslideractions = self.aw.eventslideractions[:]
        self.eventslidercommands = self.aw.eventslidercommands[:]
        self.eventslideroffsets = self.aw.eventslideroffsets[:]
        self.eventsliderfactors = self.aw.eventsliderfactors[:]
        self.eventslidermin = self.aw.eventslidermin[:]
        self.eventslidermax = self.aw.eventslidermax[:]
        self.eventsliderBernoulli = self.aw.eventsliderBernoulli[:]
        self.eventslidercoarse = self.aw.eventslidercoarse[:]
        self.eventslidertemp = self.aw.eventslidertemp[:]
        self.eventsliderunits = self.aw.eventsliderunits[:]
        # quantifiers
        self.eventquantifieractive = self.aw.eventquantifieractive[:]
        self.eventquantifiersource = self.aw.eventquantifiersource[:]
        self.eventquantifiermin = self.aw.eventquantifiermin[:]
        self.eventquantifiermax = self.aw.eventquantifiermax[:]
        self.eventquantifiercoarse = self.aw.eventquantifiercoarse[:]
        self.eventquantifieraction = self.aw.eventquantifieraction[:]
        self.eventquantifierSV = self.aw.eventquantifierSV[:]
        # palettes
        self.buttonpalette = self.aw.buttonpalette[:]
        self.buttonpalettemaxlen = self.aw.buttonpalettemaxlen
        self.buttonpalette_label = self.aw.buttonpalette_label
        # styles
        self.EvalueColor = self.aw.qmc.EvalueColor[:]
        self.EvalueMarker = self.aw.qmc.EvalueMarker[:]
        self.Evaluelinethickness = self.aw.qmc.Evaluelinethickness[:]
        self.Evaluealpha = self.aw.qmc.Evaluealpha[:]
        self.EvalueMarkerSize = self.aw.qmc.EvalueMarkerSize[:]
        # event annotations
        self.specialeventannovisibilities = self.aw.qmc.specialeventannovisibilities[:]
        self.specialeventannotations = self.aw.qmc.specialeventannotations[:]

    #called from Cancel button
    @pyqtSlot()
    def restoreState(self) -> None:
        # event configurations
        self.aw.eventsbuttonflag = self.eventsbuttonflagstored
        self.aw.qmc.eventsshowflag = self.eventsshowflagstored
        self.aw.qmc.annotationsflag = self.annotationsflagstored
        self.aw.qmc.showeventsonbt = self.showeventsonbtstored
        self.aw.qmc.showEtypes = self.showEtypesstored[:]
        self.aw.qmc.eventsGraphflag = self.eventsGraphflagstored
        self.aw.qmc.etypes = self.etypesstored
        self.aw.etypeComboBox = self.etypeComboBoxstored
        self.aw.qmc.chargeTimerFlag = self.chargeTimerFlagstored
        self.aw.qmc.chargeTimerPeriod = self.chargeTimerPeriodstored
        self.aw.qmc.autoChargeFlag = self.autoChargeFlagstored
        self.aw.qmc.autoDropFlag = self.autoDropFlagstored
        self.aw.qmc.autoChargeMode = self.autoChargeModestored
        self.aw.qmc.autoDropMode = self.autoDropModestored
        self.aw.qmc.markTPflag = self.markTPFlagstored
        self.aw.eventsliderKeyboardControl = self.eventsliderKeyboardControlstored
        self.aw.eventsliderAlternativeLayout = self.eventsliderAlternativeLayoutstored
        # buttons saved only if ok is pressed, so no restore needed
        self.aw.buttonlistmaxlen = self.buttonlistmaxlen
        # sliders
        self.aw.eventslidervisibilities = self.eventslidervisibilities
        self.aw.eventslideractions = self.eventslideractions
        self.aw.eventslidercommands = self.eventslidercommands
        self.aw.eventslideroffsets = self.eventslideroffsets
        self.aw.eventsliderfactors = self.eventsliderfactors
        self.aw.eventslidermin = self.eventslidermin
        self.aw.eventslidermax = self.eventslidermax
        self.aw.eventsliderBernoulli = self.eventsliderBernoulli
        self.aw.eventslidercoarse = self.eventslidercoarse
        self.aw.eventslidertemp = self.eventslidertemp
        self.aw.eventsliderunits = self.eventsliderunits
        # quantifiers
        self.aw.eventquantifieractive = self.eventquantifieractive
        self.aw.eventquantifiersource = self.eventquantifiersource
        self.aw.eventquantifiermin = self.eventquantifiermin
        self.aw.eventquantifiermax = self.eventquantifiermax
        self.aw.eventquantifiercoarse = self.eventquantifiercoarse
        self.aw.eventquantifieraction = self.eventquantifieraction
        # palettes
        self.aw.buttonpalette = self.buttonpalette
        self.aw.buttonpalettemaxlen = self.buttonpalettemaxlen
        self.aw.buttonpalette_label = self.buttonpalette_label
        # styles
        self.aw.qmc.EvalueColor = self.EvalueColor
        self.aw.qmc.EvalueMarker = self.EvalueMarker
        self.aw.qmc.Evaluelinethickness = self.Evaluelinethickness
        self.aw.qmc.Evaluealpha = self.Evaluealpha
        self.aw.qmc.EvalueMarkerSize = self.EvalueMarkerSize
        # event annotations
        self.aw.qmc.specialeventannovisibilities = self.specialeventannovisibilities[:]
        self.aw.qmc.specialeventannotations = self.specialeventannotations[:]
        self.close()

    #called from OK button
    @pyqtSlot()
    def updatetypes(self) -> None:
        try:
            self.closeHelp()
            self.aw.buttonsize = self.nbuttonsSizeBox.currentIndex()
            self.aw.mark_last_button_pressed = self.markLastButtonPressed.isChecked()
            self.aw.show_extrabutton_tooltips = self.showExtraButtonTooltips.isChecked()
            self.aw.buttonpalette_label = self.transferpalettecurrentLabelEdit.text()
            # save column widths
            self.aw.eventbuttontablecolumnwidths = [self.eventbuttontable.columnWidth(c) for c in range(self.eventbuttontable.columnCount())]
            #save default buttons
            self.aw.qmc.buttonvisibility[0] = self.CHARGEbutton.isChecked()
            self.aw.buttonCHARGE.setVisible(bool(self.aw.qmc.buttonvisibility[0]))
            if bool(self.aw.qmc.buttonvisibility[0]) and not self.aw.buttonCHARGE.isFlat() and not self.aw.buttonCHARGE.animating:
                # if animation is not running and button is enabled and not flat, we start the animation
                self.aw.buttonCHARGE.startAnimation()
            self.aw.qmc.buttonvisibility[1] = self.DRYbutton.isChecked()
            self.aw.buttonDRY.setVisible(bool(self.aw.qmc.buttonvisibility[1]))
            self.aw.qmc.buttonvisibility[2] = self.FCSbutton.isChecked()
            self.aw.buttonFCs.setVisible(bool(self.aw.qmc.buttonvisibility[2]))
            self.aw.qmc.buttonvisibility[3] = self.FCEbutton.isChecked()
            self.aw.buttonFCe.setVisible(bool(self.aw.qmc.buttonvisibility[3]))
            self.aw.qmc.buttonvisibility[4] = self.SCSbutton.isChecked()
            self.aw.buttonSCs.setVisible(bool(self.aw.qmc.buttonvisibility[4]))
            self.aw.qmc.buttonvisibility[5] = self.SCEbutton.isChecked()
            self.aw.buttonSCe.setVisible(bool(self.aw.qmc.buttonvisibility[5]))
            self.aw.qmc.buttonvisibility[6] = self.DROPbutton.isChecked()
            self.aw.buttonDROP.setVisible(bool(self.aw.qmc.buttonvisibility[6]))
            coolButtonVisibilityOrg = self.aw.qmc.buttonvisibility[7]
            self.aw.qmc.buttonvisibility[7] = self.COOLbutton.isChecked()
            if coolButtonVisibilityOrg != self.aw.qmc.buttonvisibility[7]:
                # adjust foreground or if no foreground but background is loaded the background; depending on showFull and COOL button state the max limit might be different
                self.aw.autoAdjustAxis(background=self.aw.qmc.background and (not len(self.aw.qmc.timex) > 3), deltas=False)
            self.aw.buttonCOOL.setVisible(bool(self.aw.qmc.buttonvisibility[7]))
            #save sliders
            self.saveSliderSettings()
            self.saveQuantifierSettings()
            # save palette label
            self.aw.buttonpalette_label = self.transferpalettecurrentLabelEdit.text()
            #
            self.aw.qmc.buttonactions[0] = self.buttonActionTypes.index(self.buttonActionTypesSorted[self.CHARGEbuttonActionType.currentIndex()])
            self.aw.qmc.buttonactions[1] = self.buttonActionTypes.index(self.buttonActionTypesSorted[self.DRYbuttonActionType.currentIndex()])
            self.aw.qmc.buttonactions[2] = self.buttonActionTypes.index(self.buttonActionTypesSorted[self.FCSbuttonActionType.currentIndex()])
            self.aw.qmc.buttonactions[3] = self.buttonActionTypes.index(self.buttonActionTypesSorted[self.FCEbuttonActionType.currentIndex()])
            self.aw.qmc.buttonactions[4] = self.buttonActionTypes.index(self.buttonActionTypesSorted[self.SCSbuttonActionType.currentIndex()])
            self.aw.qmc.buttonactions[5] = self.buttonActionTypes.index(self.buttonActionTypesSorted[self.SCEbuttonActionType.currentIndex()])
            self.aw.qmc.buttonactions[6] = self.buttonActionTypes.index(self.buttonActionTypesSorted[self.DROPbuttonActionType.currentIndex()])
            self.aw.qmc.buttonactions[7] = self.buttonActionTypes.index(self.buttonActionTypesSorted[self.COOLbuttonActionType.currentIndex()])
            self.aw.qmc.extrabuttonactions[0] = self.buttonActionTypes.index(self.buttonActionTypesSorted[self.ONbuttonActionType.currentIndex()])
            self.aw.qmc.extrabuttonactions[1] = self.buttonActionTypes.index(self.buttonActionTypesSorted[self.OFFbuttonActionType.currentIndex()])
            self.aw.qmc.extrabuttonactions[2] = self.buttonActionTypes.index(self.buttonActionTypesSorted[self.SAMPLINGbuttonActionType.currentIndex()])
            self.aw.qmc.xextrabuttonactions[0] = self.buttonActionTypes.index(self.buttonActionTypesSorted[self.RESETbuttonActionType.currentIndex()])
            self.aw.qmc.xextrabuttonactions[1] = self.buttonActionTypes.index(self.buttonActionTypesSorted[self.STARTbuttonActionType.currentIndex()])
            self.aw.qmc.buttonactionstrings[0] = self.CHARGEbuttonActionString.text()
            self.aw.qmc.buttonactionstrings[1] = self.DRYbuttonActionString.text()
            self.aw.qmc.buttonactionstrings[2] = self.FCSbuttonActionString.text()
            self.aw.qmc.buttonactionstrings[3] = self.FCEbuttonActionString.text()
            self.aw.qmc.buttonactionstrings[4] = self.SCSbuttonActionString.text()
            self.aw.qmc.buttonactionstrings[5] = self.SCEbuttonActionString.text()
            self.aw.qmc.buttonactionstrings[6] = self.DROPbuttonActionString.text()
            self.aw.qmc.buttonactionstrings[7] = self.COOLbuttonActionString.text()
            self.aw.qmc.extrabuttonactionstrings[0] = self.ONbuttonActionString.text()
            self.aw.qmc.extrabuttonactionstrings[1] = self.OFFbuttonActionString.text()
            self.aw.qmc.extrabuttonactionstrings[2] = self.SAMPLINGbuttonActionString.text()
            try:
                self.aw.qmc.extra_event_sampling_delay = self.sampling_delays[self.SAMPLINGbuttonActionInterval.currentIndex()]
            except Exception: # pylint: disable=broad-except
                pass
            self.aw.qmc.xextrabuttonactionstrings[0] = self.RESETbuttonActionString.text()
            self.aw.qmc.xextrabuttonactionstrings[1] = self.STARTbuttonActionString.text()

            self.aw.qmc.eventslabelschars = self.eventslabelscharsSpinner.value()

            self.aw.qmc.overlappct = int(self.overlapEdit.value())

            self.aw.buttonpalette_shortcuts = self.switchPaletteByNumberKey.isChecked()
            #save etypes
            if len(self.etype0.text()) and len(self.etype1.text()) and len(self.etype2.text()) and len(self.etype3.text()):
                self.aw.qmc.etypes[0] = self.etype0.text()
                self.aw.qmc.etypes[1] = self.etype1.text()
                self.aw.qmc.etypes[2] = self.etype2.text()
                self.aw.qmc.etypes[3] = self.etype3.text()
                colorPairsToCheck = []
                for i, _ in enumerate(self.aw.qmc.EvalueColor):
                    colorPairsToCheck.append(
                        (self.aw.qmc.etypes[i] + ' Event', self.aw.qmc.EvalueColor[i], 'Background', self.aw.qmc.palette['background']),
                    )
                    colorPairsToCheck.append(
                        (self.aw.qmc.etypes[i] + ' Text', self.aw.qmc.EvalueTextColor[i], self.aw.qmc.etypes[i] + ' Event', self.aw.qmc.EvalueColor[i]),
                    )
                self.aw.checkColors(colorPairsToCheck)
                # update minieditor event type ComboBox
                self.aw.etypeComboBox.clear()
                self.aw.etypeComboBox.addItems(self.aw.qmc.etypes)
                #update chargeTimer
                self.aw.qmc.chargeTimerFlag = self.chargeTimer.isChecked()
                self.aw.qmc.chargeTimerPeriod = self.chargeTimerSpinner.value()
                #update autoCharge/Drop flag
                self.aw.qmc.autoChargeFlag = self.autoCharge.isChecked()
                self.aw.qmc.autoDropFlag = self.autoDrop.isChecked()
                self.aw.qmc.markTPflag = self.markTP.isChecked()
                self.aw.qmc.autoChargeMode = self.autoChargeModeComboBox.currentIndex()
                self.aw.qmc.autoDropMode = self.autoDropModeComboBox.currentIndex()
                # keyboard control flag
                self.aw.eventsliderKeyboardControl = self.sliderKeyboardControlflag.isChecked()
                if self.aw.eventsliderKeyboardControl != self.eventsliderKeyboardControlstored and self.aw.sliderFrame.isVisible():
                    if self.aw.eventsliderKeyboardControl:
                        self.aw.setSliderFocusPolicy(Qt.FocusPolicy.StrongFocus)
                    else:
                        self.aw.setSliderFocusPolicy(Qt.FocusPolicy.NoFocus)
                self.aw.updateSliderLayout(self.sliderAlternativeLayoutFlag.isChecked())
                #save quantifiers
                self.aw.updateSlidersProperties() # set visibility and event names on slider widgets
# we don't do that anymore!
#                # we save the current button and slider definitions to palette 0
#                self.transferbuttonsto(0)
                self.aw.qmc.redraw(recomputeAllDeltas=False)
                self.aw.sendmessage(QApplication.translate('Message','Event configuration saved'))
                self.close()
            else:
                self.aw.sendmessage(QApplication.translate('Message','Found empty event type box'))
                #save quantifiers
                self.aw.updateSlidersProperties() # set visibility and event names on slider widgets
            #save special event annotations
            self.saveAnnotationsSettings()
            self.savetableextraeventbutton()
#            self.aw.closeEventSettings()
            # we need to update the ExtraLCDs as they might use event types in their names via substitutions
            if self.aw.largeExtraLCDs_dialog is not None:
                self.aw.largeExtraLCDs_dialog.reLayout()
            # we need to update the DeviceLCDs as they might use event types in their names via substitutions
            self.aw.establish_etypes()
            # restart PhidgetManager
            try:
                self.aw.qmc.restartPhidgetManager()
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
        except Exception as e: # pylint: disable=broad-except
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message', 'Exception:') + ' updatetypes(): {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))

    @pyqtSlot('QCloseEvent')
    def closeEvent(self,_:Optional['QCloseEvent'] = None) -> None:
        self.closeHelp()
        settings = QSettings()
        #save window geometry
        settings.setValue('EventsGeometry',self.saveGeometry())
        self.aw.EventsDlg_activeTab = self.TabWidget.currentIndex()

    @pyqtSlot(bool)
    def showEventbuttonhelp(self, _:bool = False) -> None:
        from help import eventbuttons_help # pyright: ignore [attr-defined] # pylint: disable=no-name-in-module
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate('Form Caption','Event Custom Buttons Help'),
                eventbuttons_help.content())

    @pyqtSlot(bool)
    def showSliderHelp(self, _:bool = False) -> None:
        from help import eventsliders_help # pyright: ignore [attr-defined] # pylint: disable=no-name-in-module
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate('Form Caption','Event Custom Sliders Help'),
                eventsliders_help.content())

    @pyqtSlot(bool)
    def showEventannotationhelp(self, _:bool = False) -> None:
        from help import eventannotations_help # pyright: ignore [attr-defined] # pylint: disable=no-name-in-module
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate('Form Caption','Event Annotations Help'),
                eventannotations_help.content())

    @pyqtSlot(bool)
    def slider1ToolButton_triggered(self, _:bool = False) -> None:
        self.openSliderCalculator(self.E1_min.value(), self.E1_max.value(), self.E1factor, self.E1offset)

    @pyqtSlot(bool)
    def slider2ToolButton_triggered(self, _:bool = False) -> None:
        self.openSliderCalculator(self.E2_min.value(), self.E2_max.value(), self.E2factor, self.E2offset)

    @pyqtSlot(bool)
    def slider3ToolButton_triggered(self, _:bool = False) -> None:
        self.openSliderCalculator(self.E3_min.value(), self.E3_max.value(), self.E3factor, self.E3offset)

    @pyqtSlot(bool)
    def slider4ToolButton_triggered(self, _:bool = False) -> None:
        self.openSliderCalculator(self.E4_min.value(), self.E4_max.value(), self.E4factor, self.E4offset)

    def closeHelp(self) -> None:
        self.aw.closeHelpDialog(self.helpdialog)

    @pyqtSlot()
    def calcSliderFactorOffset(self) -> None:
        sender = cast(QWidget, self.sender())
        dialog = cast(SliderCalculator, sender.window())
        dialog.ui.lineEdit_TargetValue_min.setText(comma2dot(dialog.ui.lineEdit_TargetValue_min.text()))
        dialog.ui.lineEdit_TargetValue_min.repaint()
        dialog.ui.lineEdit_TargetValue_max.setText(comma2dot(dialog.ui.lineEdit_TargetValue_max.text()))
        dialog.ui.lineEdit_TargetValue_max.repaint()

        min_text = dialog.ui.lineEdit_TargetValue_min.text()
        max_text = dialog.ui.lineEdit_TargetValue_max.text()

        offset = ''
        factor = ''
        if dialog.applyButton is not None:
            dialog.applyButton.setEnabled(False)
        if min_text != '' and max_text != '':
            try:
                min_slider = min(dialog.sliderMin, dialog.sliderMax)
                max_slider = max(dialog.sliderMin, dialog.sliderMax)
                tmin = float(min_text)
                tmax = float(max_text)
                min_target = min(tmin, tmax)
                max_target = max(tmin, tmax)
                if min_target != max_target and min_slider != max_slider:
                    import numpy
                    res = numpy.polyfit([min_slider, max_slider], [min_target, max_target], 1)
                    if len(res) == 2:
                        factor = f'{res[0]:.4f}'
                        offset = f'{res[1]:.2f}'
                        if dialog.applyButton is not None:
                            dialog.applyButton.setEnabled(True)
            except Exception: # pylint: disable=broad-except
                pass
        dialog.ui.lineEdit_Factor.setText(factor)
        dialog.ui.lineEdit_Offset.setText(offset)

    def openSliderCalculator(self,sliderMin:int, sliderMax:int, factorWidget:MyQDoubleSpinBox, offsetWidget:MyQDoubleSpinBox) -> None:
        dialog = SliderCalculator(self, self.aw, factorWidget, offsetWidget, sliderMin, sliderMax)
        # set data
        dialog.ui.lineEdit_SliderValue_min.setText(str(sliderMin))
        dialog.ui.lineEdit_SliderValue_max.setText(str(sliderMax))
        #
        if dialog.applyButton is not None:
            dialog.applyButton.setEnabled(False)
        # translations
        dialog.ui.label_min.setText(QApplication.translate('Label','Min'))
        dialog.ui.label_max.setText(QApplication.translate('Label','Max'))
        dialog.ui.label_SliderValue.setText(QApplication.translate('Label','Slider Value'))
        dialog.ui.label_TargetValue.setText(QApplication.translate('Label','Target Value'))
        dialog.ui.label_Factor.setText(QApplication.translate('Label','Factor'))
        dialog.ui.label_Offset.setText(QApplication.translate('Label','Offset'))
        # set validators
        dialog.ui.lineEdit_TargetValue_min.setValidator(self.aw.createCLocaleDoubleValidator(-99999., 99999., 2, dialog.ui.lineEdit_TargetValue_min))  # the max limit has to be high enough otherwise the connected signals are not send!
        dialog.ui.lineEdit_TargetValue_max.setValidator(self.aw.createCLocaleDoubleValidator(-99999., 99999., 2, dialog.ui.lineEdit_TargetValue_max))  # the max limit has to be high enough otherwise the connected signals are not send!
        # connect signals
        dialog.ui.lineEdit_TargetValue_min.editingFinished.connect(self.calcSliderFactorOffset)
        dialog.ui.lineEdit_TargetValue_max.editingFinished.connect(self.calcSliderFactorOffset)
        # fixed height
        layout  = dialog.layout()
        if layout is not None:
            layout.setSpacing(7)
        dialog.setFixedHeight(dialog.sizeHint().height())
        dialog.setFixedWidth(dialog.sizeHint().width())
        dialog.exec()

#########################################################################
#############  SLIDER Calculator Dialog  ################################
#########################################################################

class SliderCalculator(ArtisanDialog):
    def __init__(self, parent:QWidget, aw:'ApplicationWindow', factorWidget:MyQDoubleSpinBox, offsetWidget:MyQDoubleSpinBox,
            sliderMin:int, sliderMax:int) -> None:
        super().__init__(parent, aw)
        self.factorWidget = factorWidget
        self.offsetWidget = offsetWidget
        self.sliderMin = sliderMin
        self.sliderMax = sliderMax
        self.ui = SliderCalculatorDialog.Ui_SliderCalculator()
        self.ui.setupUi(self)
        self.setWindowTitle(QApplication.translate('Form Caption','Slider Calculator'))
        self.ui.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Apply)
        # hack to assign the Apply button the AcceptRole without losing default system translations
        applyButton = self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Apply)
        if applyButton is not None:
            self.ui.buttonBox.removeButton(applyButton)
            self.applyButton = self.ui.buttonBox.addButton(applyButton.text(), QDialogButtonBox.ButtonRole.AcceptRole)

    @pyqtSlot()
    def accept(self) -> None:
        if self.factorWidget is not None and self.offsetWidget is not None:
            factor_text = self.ui.lineEdit_Factor.text()
            offset_text = self.ui.lineEdit_Offset.text()
            if factor_text != '' and offset_text != '':
                try:
                    self.factorWidget.setValue(float(factor_text))
                    self.offsetWidget.setValue(float(offset_text))
                except Exception: # pylint: disable=broad-except
                    pass
        self.close()



#########################################################################
#############  CUSTOM EVENT DIALOG ######################################
#########################################################################

class customEventDlg(ArtisanDialog):
    def __init__(self, parent:QWidget, aw:'ApplicationWindow', time_idx:int = 0,description:str = '',event_type:int = 4, value:float = 0) -> None:
        super().__init__(parent, aw)
        if time_idx != 0:
            event_time = self.aw.qmc.timex[time_idx]
            if self.aw.qmc.timeindex[0] > -1:
                event_time -= self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
            event_time_str = ' @ ' + self.aw.eventtime2string(event_time)
        else:
            event_time_str = ''
        self.setWindowTitle(QApplication.translate('Form Caption','Event') + event_time_str)
        self.description = description
        self.type = event_type
        self.value:float = value

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.accept)
        self.dialogbuttons.rejected.connect(self.reject)

        descriptionLabel = QLabel(QApplication.translate('Table', 'Description'))
        self.descriptionEdit = QLineEdit(self.description)
        typeLabel = QLabel(QApplication.translate('Table', 'Type'))
        etypes = self.aw.qmc.getetypes()
        self.typeCombo = MyQComboBox()
        self.typeCombo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.typeCombo.addItems(etypes)
        self.typeCombo.setCurrentIndex(self.type)
        valueLabel = QLabel(QApplication.translate('Table', 'Value'))
        self.valueEdit = QLineEdit(self.aw.qmc.eventsvalues(self.value))

        grid = QGridLayout()
        grid.addWidget(descriptionLabel,0,0)
        grid.addWidget(self.descriptionEdit,0,1)
        grid.addWidget(typeLabel,1,0)
        grid.addWidget(self.typeCombo,1,1)
        grid.addWidget(valueLabel,2,0)
        grid.addWidget(self.valueEdit,2,1)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.dialogbuttons)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(grid)
        mainLayout.addStretch()
        mainLayout.addLayout(buttonsLayout)
        self.setLayout(mainLayout)

    def accept(self) -> None:
        self.description = self.descriptionEdit.text()
        evalue = self.valueEdit.text()
        self.value = self.aw.qmc.str2eventsvalue(str(evalue))
        self.type = self.typeCombo.currentIndex()
        super().accept()
