#
# ABOUT
# Artisan Autosave Dialog

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

from typing import Optional, cast, TYPE_CHECKING
from artisanlib.dialogs import ArtisanDialog

try:
    from PyQt6.QtCore import Qt, pyqtSlot, QSettings # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QLabel, QPushButton, QDialogButtonBox,  # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QGridLayout, QLineEdit) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QStandardItemModel # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import Qt, pyqtSlot, QSettings # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QDialogButtonBox, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox, QGridLayout, QLineEdit) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QStandardItemModel # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget # pylint: disable=unused-import
    from PyQt6.QtGui import QStandardItem, QCloseEvent # pylint: disable=unused-import

class autosaveDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Autosave'))

        settings = QSettings()
        if settings.contains('autosaveGeometry'):
            self.restoreGeometry(settings.value('autosaveGeometry'))

        self.helpdialog = None

        self.prefixEdit = QLineEdit(self.aw.qmc.autosaveprefix)
        self.prefixEdit.setToolTip(QApplication.translate('Tooltip', 'Automatic generated name'))
        self.prefixEdit.textChanged.connect(self.prefixChanged)
        prefixpreviewLabel = QLabel()
        prefixpreviewLabel.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignRight)
        prefixpreviewLabel.setText(QApplication.translate('Label', 'Preview:'))
        self.prefixPreview = QLabel()
        self.prefixpreviewrecordingLabel = QLabel()
        self.prefixpreviewrecordingLabel.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignRight)
        self.prefixPreviewrecording = QLabel()
        self.prefixChanged()

        autochecklabel = QLabel(QApplication.translate('CheckBox','Autosave [a]'))
        self.autocheckbox = QCheckBox()
        self.autocheckbox.setToolTip(QApplication.translate('Tooltip', 'ON/OFF of automatic saving when pressing keyboard letter [a]'))
        self.autocheckbox.setChecked(bool(self.aw.qmc.autosaveflag))

        addtorecentfileslabel = QLabel(QApplication.translate('CheckBox','Add to recent file list'))
        self.addtorecentfiles = QCheckBox()
        self.addtorecentfiles.setToolTip(QApplication.translate('Tooltip', 'Add auto saved file names to the recent files list'))
        self.addtorecentfiles.setChecked(self.aw.qmc.autosaveaddtorecentfilesflag)

        autopdflabel = QLabel(QApplication.translate('CheckBox','Save also'))
        self.autopdfcheckbox = QCheckBox()
        self.autopdfcheckbox.setToolTip(QApplication.translate('Tooltip', 'Save image alongside .alog profiles'))
        self.autopdfcheckbox.setChecked(self.aw.qmc.autosaveimage)
        self.imageTypesComboBox = QComboBox()
        self.imageTypesComboBox.addItems(self.aw.qmc.autoasaveimageformat_types)
        try:
            if not self.aw.QtWebEngineSupport:
                # disable "PDF Report" item if QtWebEngine Support is not available
                model = self.imageTypesComboBox.model()
                if model is not None:
                    item: Optional[QStandardItem] = cast(QStandardItemModel, model).item(self.aw.qmc.autoasaveimageformat_types.index('PDF Report'))
                    if item is not None:
                        item.setEnabled(False)
        except Exception: # pylint: disable=broad-except
            pass
        self.imageTypesComboBox.setCurrentIndex(self.aw.qmc.autoasaveimageformat_types.index(self.aw.qmc.autosaveimageformat))
        prefixlabel = QLabel()
        prefixlabel.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        prefixlabel.setText(QApplication.translate('Label', 'File Name Prefix'))

        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.autoChanged)
        self.dialogbuttons.rejected.connect(lambda : (None if self.close() else None)) # lambda to make mypy happy, turning close from None->bool into None->None
        self.helpButton = self.dialogbuttons.addButton(QDialogButtonBox.StandardButton.Help)
        if self.helpButton is not None:
            self.setButtonTranslations(self.helpButton,'Help',QApplication.translate('Button','Help'))
            self.helpButton.clicked.connect(self.showautosavehelp)

        pathButton = QPushButton(QApplication.translate('Button','Path'))
        pathButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pathEdit = QLineEdit(self.aw.qmc.autosavepath)
        self.pathEdit.setToolTip(QApplication.translate('Tooltip', 'Sets the directory to store batch profiles when using the letter [a]'))
        pathButton.clicked.connect(self.getpath)

        pathAlsoButton = QPushButton(QApplication.translate('Button','Path'))
        pathAlsoButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pathAlsoEdit = QLineEdit(self.aw.qmc.autosavealsopath)
        self.pathAlsoEdit.setToolTip(QApplication.translate('Tooltip', 'Sets the directory to store the save also files'))
        pathAlsoButton.clicked.connect(self.getalsopath)

        # this intermediate layout is needed to add the 'addtorecentfiles' checkbox into the existing grid layout.
        autochecklabelplus = QHBoxLayout()
        autochecklabelplus.addWidget(autochecklabel)
        autochecklabelplus.addWidget(self.addtorecentfiles)
        autochecklabelplus.addWidget(addtorecentfileslabel)
        autochecklabelplus.addStretch()

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.dialogbuttons)
        autolayout = QGridLayout()
        autolayout.addWidget(self.autocheckbox,0,0,Qt.AlignmentFlag.AlignRight)
        autolayout.addLayout(autochecklabelplus,0,1)
        autolayout.addWidget(prefixlabel,1,0)
        autolayout.addWidget(self.prefixEdit,1,1,1,2)
        autolayout.addWidget(prefixpreviewLabel,2,0)
        autolayout.addWidget(self.prefixPreview,2,1)
        autolayout.addWidget(self.prefixpreviewrecordingLabel,3,0)
        autolayout.addWidget(self.prefixPreviewrecording,3,1)
        autolayout.addWidget(pathButton,4,0)
        autolayout.addWidget(self.pathEdit,4,1,1,2)
        autolayout.addWidget(self.autopdfcheckbox,5,0,Qt.AlignmentFlag.AlignRight)
        autolayout.addWidget(autopdflabel,5,1)
        autolayout.addWidget(self.imageTypesComboBox,5,2)
        autolayout.addWidget(pathAlsoButton,6,0)
        autolayout.addWidget(self.pathAlsoEdit,6,1,1,2)
        autolayout.setColumnStretch(0,0)
        autolayout.setColumnStretch(1,10)
        autolayout.setColumnStretch(2,0)
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(autolayout)
        mainLayout.addStretch()
        mainLayout.addSpacing(10)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
        okButton: Optional[QPushButton] = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if okButton is not None:
            okButton.setFocus()
        self.setFixedHeight(self.sizeHint().height())

    @pyqtSlot(bool)
    def showautosavehelp(self,_:bool = False) -> None:
        from help import autosave_help # pyright:ignore [attr-defined] # pylint: disable=no-name-in-module
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate('Form Caption','Autosave Fields Help'),
                autosave_help.content()) # pyright:ignore # "content" in typed context  [no-untyped-call]

    def closeHelp(self) -> None:
        self.aw.closeHelpDialog(self.helpdialog)

    @pyqtSlot()
    def prefixChanged(self) -> None:
        autosaveprefix:str = self.prefixEdit.text()
        prefix = ''
        if autosaveprefix != '':
            prefix = autosaveprefix
        elif self.aw.qmc.batchcounter > -1 and self.aw.qmc.roastbatchnr > 0:
            prefix += self.aw.qmc.batchprefix + str(self.aw.qmc.roastbatchnr)
        elif self.aw.qmc.batchprefix != '':
            prefix += self.aw.qmc.batchprefix
        preview = self.aw.generateFilename(prefix, previewmode=2)
        self.prefixPreview.setText(preview)
        previewrecording = self.aw.generateFilename(prefix,previewmode=1)
        if previewrecording == preview:
            self.prefixpreviewrecordingLabel.setText('')
            self.prefixPreviewrecording.setText('')
        else:
            self.prefixpreviewrecordingLabel.setText(QApplication.translate('Label', 'While recording:'))
            self.prefixPreviewrecording.setText(previewrecording)

    @pyqtSlot(bool)
    def getpath(self,_:bool) -> None:
        filename = self.aw.ArtisanExistingDirectoryDialog(msg=QApplication.translate('Form Caption','AutoSave Path'))
        self.pathEdit.setText(filename)

    @pyqtSlot(bool)
    def getalsopath(self,_:bool) -> None:
        filename = self.aw.ArtisanExistingDirectoryDialog(msg=QApplication.translate('Form Caption','AutoSave Save Also Path'))
        self.pathAlsoEdit.setText(filename)

    @pyqtSlot()
    def autoChanged(self) -> None:
        self.aw.qmc.autosavepath = self.pathEdit.text()
        self.aw.qmc.autosavealsopath = self.pathAlsoEdit.text()
        if self.autocheckbox.isChecked():
            self.aw.qmc.autosaveflag = 1
            self.aw.qmc.autosaveprefix = self.prefixEdit.text()
            message = QApplication.translate('Message','Autosave ON. Prefix: {0}').format(self.prefixEdit.text())
            self.aw.sendmessage(message)
        else:
            self.aw.qmc.autosaveflag = 0
            self.aw.qmc.autosaveprefix = self.prefixEdit.text()
            message = QApplication.translate('Message','Autosave OFF. Prefix: {0}').format(self.prefixEdit.text())
            self.aw.sendmessage(message)
        self.aw.qmc.autosaveimage = self.autopdfcheckbox.isChecked()
        self.aw.qmc.autosaveimageformat = self.imageTypesComboBox.currentText()
        self.aw.qmc.autosaveaddtorecentfilesflag = self.addtorecentfiles.isChecked()
        self.close()

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        self.closeHelp()
        settings = QSettings()
        #save window geometry
        settings.setValue('autosaveGeometry',self.saveGeometry())
