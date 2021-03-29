#!/usr/bin/env python3

# ABOUT
# Artisan Preferences Dialog

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
# Marko Luther, 2021

from uic import SetupDialog
from artisanlib.dialogs import ArtisanDialog

#try:
#    from PyQt6.QtCore import QLibraryInfo  # @UnusedImport @UnresolvedImport
#    pyqtversion = 6
#except Exception as e:
#    pyqtversion = 5
pyqtversion = 5 # until MPL and all build tools fully support PyQt6 we run on PyQt5


if pyqtversion < 6:
    from PyQt5.QtCore import Qt # @Reimport @UnusedImport
    from PyQt5.QtWidgets import (QApplication, QDialogButtonBox) # @Reimport @UnusedImport
    try: # hidden import to allow pyinstaller build on OS X to include the PyQt5.x private sip module
        from PyQt5 import sip #  # @Reimport @UnusedImport
    except:
        pass
#else:
#    from PyQt6.QtCore import Qt # @Reimport @UnusedImport
#    from PyQt6.QtWidgets import (QApplication, QDialogButtonBox) # @Reimport @UnusedImport
#    try: # hidden import to allow pyinstaller build on OS X to include the PyQt5.x private sip module
#        from PyQt6 import sip  # @Reimport @UnusedImport
#    except:
#        pass

def preferencesDialog(parent, aw):
    dialog = ArtisanDialog(parent,aw)
    dialog.setAttribute(Qt.WA_DeleteOnClose, False) # not to have the dialog object deleted on close as we still want to acces its data
    # install dialog content  
    ui = SetupDialog.Ui_SetupDialog()
    ui.setupUi(dialog)
    # install button translations if need for the locale
    if aw.locale not in aw.qtbase_locales:
        ui.buttonBox.button(QDialogButtonBox.Ok).setText(QApplication.translate("Button","OK", None))
        ui.buttonBox.button(QDialogButtonBox.Cancel).setText(QApplication.translate("Button","Cancel",None))
    # explicitly reset labels to have them translated with a controlled context
    dialog.setWindowTitle(QApplication.translate("Form Caption", "Setup"))
    ui.roasterSizeDoubleSpinBox.setToolTip(QApplication.translate("Tooltip", "The maximum nominal batch size of the machine in kg"))
    ui.labelOrganization.setText(QApplication.translate("Label", "Organization",None))
    ui.labelOperator.setText(QApplication.translate("Label", "Operator",None))
    ui.labelMachine.setText(QApplication.translate("Label", "Machine",None))
    ui.labelDrumSpeed.setText(QApplication.translate("Label", "Drum Speed",None))
    # fill dialog with data
    ui.OrganizationLineEdit.setText(aw.qmc.organization_setup)
    ui.OperatorLineEdit.setText(aw.qmc.operator_setup)
    ui.MachineLineEdit.setText(aw.qmc.roastertype_setup)
    ui.roasterSizeDoubleSpinBox.setValue(aw.qmc.roastersize_setup)
    ui.DrumSpeedLineEdit.setText(aw.qmc.drumspeed_setup)
    ui.buttonBox.accepted.connect(dialog.accept)
    ui.buttonBox.rejected.connect(dialog.reject)
    # fixed hight
    dialog.setFixedHeight(dialog.sizeHint().height())
    # show dialog
    if dialog.exec_():
        aw.qmc.organization_setup = ui.OrganizationLineEdit.text()
        aw.qmc.operator_setup = ui.OperatorLineEdit.text()
        aw.qmc.roastertype_setup = ui.MachineLineEdit.text()
        aw.qmc.roastersize_setup = ui.roasterSizeDoubleSpinBox.value()
        aw.qmc.drumspeed_setup = ui.DrumSpeedLineEdit.text()
        if aw.curFile is None and len(aw.qmc.timex) == 0:
            # no profile loaded and no data recorded (situation as after reset)
            # we write the changed setup data also to the profilels roast properties as a RESET would do
            aw.qmc.organization = aw.qmc.organization_setup
            aw.qmc.operator = aw.qmc.operator_setup
            aw.qmc.roastertype = aw.qmc.roastertype_setup
            aw.qmc.roastersize = aw.qmc.roastersize_setup
            aw.qmc.drumspeed = aw.qmc.drumspeed_setup
    dialog.deleteLater() # now we explicitly allow the dialog an its widgets to be GCed
    # the following will immedately release the memory dispite this parent link
    QApplication.processEvents() # we ensure events concerning this dialog are processed before deletion
    try:
        sip.delete(dialog)
        #print(sip.isdeleted(dialog))
    except:
        pass