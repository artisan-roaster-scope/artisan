#
# ABOUT
# Artisan Quick Cupping Dialog
# Shown after DROP event for quick rating and notes

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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    from PyQt6.QtWidgets import QWidget # pylint: disable=unused-import

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QVBoxLayout, QLabel,
                             QLineEdit, QButtonGroup, QRadioButton, QGroupBox)

from artisanlib.dialogs import ArtisanDialog

class QuickCuppingDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Quick Cupping'))

        # Store initial cupping notes to check if modified
        self.initial_cupping_notes = aw.qmc.cuppingnotes

        # Rating (1-5 stars)
        ratingLabel = QLabel('<b>' + QApplication.translate('Label', 'Rating') + '</b>')

        self.rating_group = QButtonGroup(self)
        rating_layout = QHBoxLayout()

        self.star_buttons = []
        for i in range(1, 6):
            rb = QRadioButton(str(i))
            rb.setToolTip(QApplication.translate('Tooltip', f'{i} star{"s" if i > 1 else ""}'))
            self.rating_group.addButton(rb, i)
            self.star_buttons.append(rb)
            rating_layout.addWidget(rb)

        # Default to 3 stars
        self.star_buttons[2].setChecked(True)

        rating_layout.addStretch()

        # Tasting notes (one line)
        notesLabel = QLabel('<b>' + QApplication.translate('Label', 'Tasting Notes') + '</b>')
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText(QApplication.translate('Placeholder', 'Quick tasting notes...'))

        # Defects checkboxes
        defectsLabel = QLabel('<b>' + QApplication.translate('Label', 'Defects') + '</b>')

        self.baked_check = QCheckBox(QApplication.translate('CheckBox', 'Baked'))
        self.scorched_check = QCheckBox(QApplication.translate('CheckBox', 'Scorched'))
        self.underdeveloped_check = QCheckBox(QApplication.translate('CheckBox', 'Underdeveloped'))
        self.tipping_check = QCheckBox(QApplication.translate('CheckBox', 'Tipping'))

        defects_layout = QHBoxLayout()
        defects_layout.addWidget(self.baked_check)
        defects_layout.addWidget(self.scorched_check)
        defects_layout.addWidget(self.underdeveloped_check)
        defects_layout.addWidget(self.tipping_check)
        defects_layout.addStretch()

        # Create group box for all content
        contentLayout = QVBoxLayout()
        contentLayout.addWidget(ratingLabel)
        contentLayout.addLayout(rating_layout)
        contentLayout.addSpacing(10)
        contentLayout.addWidget(notesLabel)
        contentLayout.addWidget(self.notes_edit)
        contentLayout.addSpacing(10)
        contentLayout.addWidget(defectsLabel)
        contentLayout.addLayout(defects_layout)

        contentGroup = QGroupBox()
        contentGroup.setLayout(contentLayout)

        # Connect standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.save_and_close)
        self.dialogbuttons.rejected.connect(self.reject)

        # Main layout
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(contentGroup)
        mainLayout.addWidget(self.dialogbuttons)

        self.setLayout(mainLayout)

        # Set focus to notes field
        self.notes_edit.setFocus()

    @pyqtSlot()
    def save_and_close(self) -> None:
        """Save the quick cupping data to the roast profile"""
        # Get rating
        rating = self.rating_group.checkedId()

        # Get tasting notes
        tasting_notes = self.notes_edit.text().strip()

        # Get defects
        defects = []
        if self.baked_check.isChecked():
            defects.append(QApplication.translate('Label', 'Baked'))
        if self.scorched_check.isChecked():
            defects.append(QApplication.translate('Label', 'Scorched'))
        if self.underdeveloped_check.isChecked():
            defects.append(QApplication.translate('Label', 'Underdeveloped'))
        if self.tipping_check.isChecked():
            defects.append(QApplication.translate('Label', 'Tipping'))

        # Build quick cupping note
        quick_note_parts = []

        # Add rating
        stars = '⭐' * rating
        quick_note_parts.append(f'{QApplication.translate("Label", "Rating")}: {stars} ({rating}/5)')

        # Add tasting notes if provided
        if tasting_notes:
            quick_note_parts.append(f'{QApplication.translate("Label", "Notes")}: {tasting_notes}')

        # Add defects if any
        if defects:
            quick_note_parts.append(f'{QApplication.translate("Label", "Defects")}: {", ".join(defects)}')

        # Combine into single note
        quick_note = '\n'.join(quick_note_parts)

        # Append to existing cupping notes (if any)
        if self.aw.qmc.cuppingnotes:
            self.aw.qmc.cuppingnotes += '\n\n' + quick_note
        else:
            self.aw.qmc.cuppingnotes = quick_note

        # Accept dialog
        self.accept()
