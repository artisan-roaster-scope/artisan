#
# ABOUT
# artisan scope dashboard
#
# COPYRIGHT (C) 2010-2026 The artisan team represented by
#   Marko Luther <marko.luther@gmx.net> (maintainer) and all contributors
#
# LICENSE
# This program or module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# MAINTAINER
# Marko Luther, 2026
#
# AUTHOR
# Marko Luther, 2026

import os
import sys
import platform
import logging
from pathlib import Path
from typing import Final, override, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    from PyQt6.QtGui import QMouseEvent # pylint: disable=unused-import

from PyQt6.QtWidgets import QApplication, QWidget, QComboBox
from PyQt6.QtCore import Qt, QSettings, pyqtSlot, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QFontDatabase, QIcon

from uic import DashboardWidget # pyright: ignore[attr-defined] # pylint: disable=no-name-in-module


from artisanlib import __release_sponsor_url__
from artisanlib.styles import combobox_style, dashboard_style
from artisanlib.util import getStyleIconPath, float2floatWeightVolume, convertVolume, convertWeight, volume_units, weight_units, weight_units_lower, toStringList, comma2dot, getResourcePath, open_link
from artisanlib.styles import tool_button_icon_style, artisan_push_button_style, artisan_minor_push_button_style, link_push_button_style
from plus.util import plusLink

_log: Final[logging.Logger] = logging.getLogger(__name__)



class Dashboard(QWidget):

    DOCUMENTATION_URL:Final[str] = 'https://artisan-scope.org/docs'
    USER_FORUM_URL:Final[str] = 'https://github.com/artisan-roaster-scope/artisan/discussions'
    ISSUE_TRACKER_URL:Final[str] = 'https://github.com/artisan-roaster-scope/artisan/issues'
    DONATE_URL:Final[str] = 'https://artisan-scope.org/donate'

    TITLE_CHANGE_ESTABLISH_PERIOD:Final[int] = 400 # time in ms after which title changes are established

    canvas_clicked = pyqtSignal()

    def __init__(self, aw:'ApplicationWindow') -> None:
        super().__init__()

        self.aw = aw

        self.recent_files:list[str] = []

        self.setUpdatesEnabled(False) # disable display updates
        try:
            self.ui = DashboardWidget.Ui_Dashboard()
            self.ui.setupUi(self)

            # TODO: remove
            self.ui.beans_comboBox.addItems(['Brazil Santos [30,7kg]','some cool','items that look','different','all of them'])
            self.ui.blend_comboBox.addItems(['Brazil Santos [30,7kg]','some cool','items that look','different','all of them'])
            self.ui.space_comboBox.addItems(['Brazil Santos [30,7kg]','some cool','items that look','different','all of them'])

            # style
            self.ui.login_pushButton.setStyleSheet(artisan_push_button_style())
            self.ui.donate_pushButton.setStyleSheet(artisan_push_button_style())

            self.ui.plus_button.setStyleSheet(artisan_push_button_style())
            self.ui.plus_button.setFixedSize(QSize(26,26))
            self.ui.minus_button.setStyleSheet(artisan_push_button_style())
            self.ui.minus_button.setFixedSize(QSize(26,26))

            self.ui.properties_pushButton.setStyleSheet(artisan_minor_push_button_style())
            self.ui.compare_pushButton.setStyleSheet(artisan_minor_push_button_style())
            self.ui.load_pushButton.setStyleSheet(artisan_minor_push_button_style())
            self.ui.clear_pushButton.setStyleSheet(artisan_minor_push_button_style())
            self.ui.create_pushButton.setStyleSheet(artisan_minor_push_button_style())

            self.ui.documentation_pushButton.setStyleSheet(link_push_button_style)
            self.ui.documentation_pushButton.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            self.ui.forum_pushButton.setStyleSheet(link_push_button_style)
            self.ui.forum_pushButton.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            self.ui.issue_pushButton.setStyleSheet(link_push_button_style)
            self.ui.issue_pushButton.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            self.ui.platform_pushButton.setStyleSheet(link_push_button_style)
            self.ui.platform_pushButton.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

            self.ui.custom_blend.setStyleSheet(tool_button_icon_style(self.aw.app.darkmode,
                'pencil-edit-02-stroke-rounded-light.svg', 'pencil-edit-02-stroke-rounded-dark.svg'))
            self.ui.sync.setStyleSheet(tool_button_icon_style(self.aw.app.darkmode,
                'update-light.svg', 'update-light.svg'))
            self.ui.scheduler_toolButton.setStyleSheet(tool_button_icon_style(self.aw.app.darkmode,
                'calendar-03-stroke-rounded-blue.svg', 'calendar-03-stroke-rounded-blue.svg'))

            self.ui.scheduler_frame.setStyleSheet("""
                QFrame { border-width: 1px; border-style: solid; border-color: #BBBBBB; border-radius: 15px; background-color: #F3F3F3; }
                QFrame:hover { background-color: '#E0E0E0'; }
                QFrame:pressed { background-color: '#D0D0D0'; }
            """)

            # font # TODO: (not: el, ar, zh, jp, he)
            artisan_font_semibold_file = os.path.join(getResourcePath(),'Nunito-SemiBold.ttf')
            artisan_font_semibold_id = QFontDatabase.addApplicationFont(artisan_font_semibold_file)
            artisan_font_semibold_families = QFontDatabase.applicationFontFamilies(artisan_font_semibold_id)
            artisan_font_normal = os.path.join(getResourcePath(),'Nunito-Regular.ttf')
            artisan_font_normal_id = QFontDatabase.addApplicationFont(artisan_font_normal)
            artisan_font_normal_families = QFontDatabase.applicationFontFamilies(artisan_font_normal_id)

            main_header_font_size = (18 if platform.system() == 'Windows' else 20)
            sub_header_font_size = (14 if platform.system() == 'Windows' else 16)
            self.ui.roast_label.setFont(QFont(artisan_font_semibold_families[0], main_header_font_size, QFont.Weight.DemiBold))
            self.ui.profile_label.setFont(QFont(artisan_font_semibold_families[0], main_header_font_size, QFont.Weight.DemiBold))
            self.ui.inventory_group.setFont(QFont(artisan_font_normal_families[0], sub_header_font_size, QFont.Weight.Normal))
            self.ui.sponsor_label.setFont(QFont(artisan_font_normal_families[0], sub_header_font_size, QFont.Weight.Normal))
            self.ui.donate_label.setFont(QFont(artisan_font_normal_families[0], sub_header_font_size, QFont.Weight.Normal))

            # configure widgets
            self.ui.weight_unit_comboBox.addItems(weight_units_lower)
            self.ui.recentFiles_comboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
            self.ui.recentFiles_comboBox.setMaxVisibleItems(self.aw.MaxRecentFiles + 1) # if more items are added, the width is no longer adjusted to the contents
            self.ui.inventory_stackedWidget.setCurrentIndex(0)

            self.ui.properties_pushButton.setIconSize(QSize(14,14))
            self.ui.properties_pushButton.setIcon(QIcon(getStyleIconPath('settings-01-stroke-rounded-dark.svg')))

            self.ui.load_pushButton.setIconSize(QSize(14,14))
            self.ui.load_pushButton.setIcon(QIcon(getStyleIconPath('file-02-stroke-rounded-white.svg')))

            self.ui.clear_pushButton.setIconSize(QSize(14,14))
            self.ui.clear_pushButton.setIcon(QIcon(getStyleIconPath('cancel-01-stroke-rounded-white.svg')))

            self.ui.create_pushButton.setIconSize(QSize(14,14))
            self.ui.create_pushButton.setIcon(QIcon(getStyleIconPath('add-01-stroke-rounded-white.svg')))

            self.ui.compare_pushButton.setIconSize(QSize(14,14))
            self.ui.compare_pushButton.setIcon(QIcon(getStyleIconPath('git-compare-arrows-stroke-rounded-light.svg')))

            self.ui.donate_pushButton.setIconSize(QSize(14,14))
            self.ui.donate_pushButton.setIcon(QIcon(getStyleIconPath('heart-handshake-stroke-rounded-white.svg')))

            self.ui.login_pushButton.setIconSize(QSize(14,14))
            self.ui.login_pushButton.setIcon(QIcon(getStyleIconPath('user-circle-stroke-rounded-dark.svg')))

            self.ui.documentation_pushButton.setIconSize(QSize(10,10))
            self.ui.documentation_pushButton.setIcon(QIcon(getStyleIconPath('external-link-stroke-rounded.svg')))
            self.ui.forum_pushButton.setIconSize(QSize(10,10))
            self.ui.forum_pushButton.setIcon(QIcon(getStyleIconPath('external-link-stroke-rounded.svg')))
            self.ui.issue_pushButton.setIconSize(QSize(10,10))
            self.ui.issue_pushButton.setIcon(QIcon(getStyleIconPath('external-link-stroke-rounded.svg')))
            self.ui.platform_pushButton.setIconSize(QSize(10,10))
            self.ui.platform_pushButton.setIcon(QIcon(getStyleIconPath('external-link-stroke-rounded.svg')))


            if __release_sponsor_url__ == '': # pyright:ignore[reportUnnecessaryComparison]
                self.ui.groupBox_sponsor.setVisible(False)
            else:
                try:
                    self.ui.sponsor_logo_toolButton.setIcon(QIcon(Path.as_posix(Path(getResourcePath()).joinpath('release-sponsor-logo.svg'))))
                    self.ui.sponsor_logo_toolButton.setIconSize(QSize(150,75))
                    self.ui.sponsor_logo_toolButton.setStyleSheet("""
                        FixedRatio2ToolButton {
                            background-color: #ffffff;
                            border: 0px solid;
                            border-radius: 10px;
                            min-width: 150px;
                            max-width: 150px;
                        }
                        FixedRatio2ToolButton:hover {
                            background-color: #fAfAfA;
                        }
                        FixedRatio2ToolButton:pressed {
                            background-color: #f5f5f5;
                        }
                    """)
                except Exception: # pylint: disable=broad-except
                    self.ui.groupBox_sponsor.setVisible(False)

            # timers
            self.title_changed_timer = QTimer()
            self.title_changed_timer.setSingleShot(True)
            self.title_changed_timer.timeout.connect(self.title_changed)

            # connect signals
            self.ui.login_pushButton.clicked.connect(self.login_clicked)
            self.ui.title_comboBox.activated.connect(self.recent_roast_activated)
            self.ui.title_comboBox.editTextChanged.connect(self.recent_roast_enabled)
            self.ui.plus_button.clicked.connect(self.add_recent_roast)
            self.ui.minus_button.clicked.connect(self.delete_recent_roast)
            self.ui.beans_textEdit.editingFinished.connect(self.beans_edited)
            self.ui.weightinedit.editingFinished.connect(self.weightin_edited)
            self.ui.weight_unit_comboBox.currentIndexChanged.connect(self.weight_unit_changed)
            self.ui.recentFiles_comboBox.currentIndexChanged.connect(self.recent_files_index_changed)
            self.ui.properties_pushButton.clicked.connect(self.aw.editgraph)
            self.ui.load_pushButton.clicked.connect(self.profile_load_clicked)
            self.ui.clear_pushButton.clicked.connect(self.profile_clear_clicked)
            self.ui.scheduler_toolButton.clicked.connect(self.open_scheduler)

            self.ui.create_pushButton.clicked.connect(self.start_designer)
            self.ui.compare_pushButton.clicked.connect(self.aw.roastCompare)

            self.ui.documentation_pushButton.clicked.connect(self.open_documentation_url)
            self.ui.forum_pushButton.clicked.connect(self.open_forum_url)
            self.ui.issue_pushButton.clicked.connect(self.open_issue_tracker_url)
            self.ui.platform_pushButton.clicked.connect(self.open_platform_url)
            self.ui.donate_pushButton.clicked.connect(self.open_donate_url)
            self.ui.sponsor_logo_toolButton.clicked.connect(self.open_sponsor_url)

            self.canvas_clicked.connect(self.hide_dashboard)

            self.set_style()

        finally:
            self.setUpdatesEnabled(True) # re-enable display updates

    @override
    def mousePressEvent(self, a0:'QMouseEvent|None') -> None:
        # Check if it's a left click
        if a0 is not None and a0.button() == Qt.MouseButton.LeftButton and not (
                self.ui.groupBox_roast.underMouse() or
                self.ui.groupBox_profile.underMouse()):
            self.canvas_clicked.emit()
        # Call the base class implementation
        super().mousePressEvent(a0)


    def dashboard_active(self) -> bool:
        return self.aw.stack.currentIndex() == 1

    def toggle_dashboard(self) -> None:
        if self.dashboard_active():
            self.hide_dashboard()
        else:
            self.show_dashboard()

    def show_dashboard(self) -> None:
        if not self.aw.qmc.flagstart:
            self.update_dashboard(force=True)
            # only open the dashboard if not recording!
            self.aw.stack.setCurrentIndex(1)
            self.update_dashboard()

    @pyqtSlot()
    def hide_dashboard(self) -> None:
        self.aw.stack.setCurrentIndex(0)
        self.update_dashboard()

    # if force, update even if not visible
    # if init_title, the title popup is re-initialized (only needed if the popup content changes, not if only the title changes)
    # if dark_canvas, the corresponding style matching a dark canvas is selected
    def update_dashboard(self, force:bool=False, init_title:bool=True, dark_canvas:bool|None=None) -> None:
        darkmode = self.aw.dark_canvas_p(dark_canvas)

        if force or self.aw.stack.currentIndex() == 1:
            # only update if visible

            self.ui.recentFiles_comboBox.blockSignals(True)
            try:
                # overall style
                self.update_main_style(darkmode)

                # batch number
                roastpos = ('' if self.aw.qmc.roastbatchnr == 0 else f' ({self.aw.qmc.roastbatchpos})')
                self.ui.batch_nr.setText('' if self.aw.qmc.roastbatchnr == 0 else f'{self.aw.qmc.roastbatchprefix}{self.aw.qmc.roastbatchnr}{roastpos}')

                # title
                if init_title:
                    self.ui.title_comboBox.init(self.aw.recentRoastsMenuList, self.aw.qmc.title) # we need to initialize the popup and lineedit

                # plus/minus buttons
                self.update_recent_roast_buttons()

                # compare/create buttons
                self.update_compare_create_buttons()

                # inventory
                self.update_inventory_section(force)

                # beans
                self.ui.beans_textEdit.setNewPlainText(self.aw.qmc.beans)

                # batchsize
                self.ui.weightinedit.setText(f'{float2floatWeightVolume(self.aw.qmc.weight[0]):g}')

                # weight unit
                self.ui.weight_unit_comboBox.setCurrentIndex(weight_units.index(self.aw.qmc.weight[2]))

                # profile
                self.update_profile_section()
            finally:
                self.ui.recentFiles_comboBox.blockSignals(False)

        # always update tool icons
        self.update_tool_icons(darkmode)
        self.aw.ntb.update_tools()

    def update_main_style(self, darkmode:bool) -> None:
        combobox_stylesheet = combobox_style(False, getStyleIconPath('arrow-down-01-stroke-rounded-light.svg'))
        self.setStyleSheet(dashboard_style(darkmode or self.aw.dashboard_background_image is not None) + combobox_stylesheet)

    def update_background(self) -> None:
        if self.aw.dashboard_background_image is None:
            self.aw.stack.setStyleSheet('QStackedWidget {{background-color: transparent; }}')
            for pane in [self.ui.groupBox_roast, self.ui.groupBox_profile, self.ui.groupBox_links,
                    self.ui.groupBox_links, self.ui.groupBox_donation]:
                pane.setGraphicsEffect(None)
        else:
            self.aw.stack.setStyleSheet(f'QStackedWidget {{background-color: transparent; background-image: url({Path.as_posix(Path(self.aw.dashboard_background_image))}); }}')
            for pane in [self.ui.groupBox_roast, self.ui.groupBox_profile, self.ui.groupBox_links,
                    self.ui.groupBox_links, self.ui.groupBox_donation]:
                pane.setGraphicsEffect(self.aw.makeShadow(strong=True))
        self.update_image_tool_icon()
        # update overall style to get the border color of the panes right
        darkmode = self.aw.dark_canvas_p()
        self.update_main_style(darkmode)


#---- move to main.py
    def update_tool_icons(self, dark_canvas:bool|None=None) -> None:
        self.update_image_tool_icon(dark_canvas)
        self.update_exit_tool_icon(dark_canvas)

    def update_image_tool_icon(self, dark_canvas:bool|None=None) -> None:
        if self.aw.stack.currentIndex() == 1 and self.aw.inExpertMode():
            # dashboard visible
            self.aw.dashboardImageToolButton.setStyleSheet(tool_button_icon_style(
                self.aw.dark_canvas_p(dark_canvas),
                ('image-02-stroke-rounded-light.svg' if self.aw.dashboard_background_image is None else 'image-not-found-01-stroke-rounded-light.svg'),
                ('image-02-stroke-rounded-dark.svg' if self.aw.dashboard_background_image is None else 'image-not-found-01-stroke-rounded-dark.svg')))
            self.aw.dashboardImageToolButton.setToolTip(QApplication.translate('Tooltip','Set background image') if self.aw.dashboard_background_image is None else
                QApplication.translate('Tooltip','Remove background image'))
            self.aw.dashboardImageToolButton.setVisible(True)
        else:
            # dashboard hidden
            self.aw.dashboardImageToolButton.setVisible(False)

    def update_exit_tool_icon(self, dark_canvas:bool|None=None) -> None:
        if self.aw.qmc.designerflag or self.aw.qmc.wheelflag:
            # designer exit button visible
            self.aw.exitToolButton.setStyleSheet(tool_button_icon_style(
                self.aw.dark_canvas_p(dark_canvas),
                'cancel-square-stroke-rounded-light.svg',
                'cancel-square-stroke-rounded-dark.svg'
                ))
#            self.aw.dashboardImageToolButton.setToolTip(QApplication.translate('Tooltip','Set background image') if self.aw.dashboard_background_image is None else
#                QApplication.translate('Tooltip','Remove background image'))
            self.aw.exitToolButton.setVisible(True)
        else:
            # designer exit button hidden
            self.aw.exitToolButton.setVisible(False)
#----


    def update_inventory_section(self, force:bool=False) -> None:
        if force or self.aw.stack.currentIndex() == 1:
            self.ui.inventory_stackedWidget.setCurrentIndex(0 if self.aw.plus_account is None else 1)
            # enable/disable scheduler tool button
            self.ui.scheduler_frame.setEnabled(self.aw.plus_account is not None and not self.aw.app.artisanviewerMode)  # no scheduler in ArtisanViewer mode
            # scheduler tool icon
            self.ui.scheduler_toolButton.setStyleSheet(tool_button_icon_style(self.aw.app.darkmode,
                ('calendar-03-stroke-rounded-dark.svg' if self.aw.plus_account is None or self.aw.app.artisanviewerMode else 'calendar-03-stroke-rounded-blue.svg'),
                ('calendar-03-stroke-rounded-dark.svg' if self.aw.plus_account is None or self.aw.app.artisanviewerMode else 'calendar-03-stroke-rounded-blue.svg')))

    def clearPushButtonSetEnabled(self) -> None:
        self.ui.clear_pushButton.setEnabled(True)
        self.ui.clear_pushButton.setIcon(QIcon(getStyleIconPath('cancel-01-stroke-rounded-white.svg')))

    def clearPushButtonSetDisabled(self) -> None:
        self.ui.clear_pushButton.setEnabled(False)
        self.ui.clear_pushButton.setIcon(QIcon(getStyleIconPath('cancel-01-stroke-rounded.svg')))


    pyqtSlot()
    def update_profile_section(self) -> None:
        self.ui.recentFiles_comboBox.blockSignals(True)
        try:
            # recent files
            self.recent_files = toStringList(QSettings().value('recentFileList'))
            self.ui.recentFiles_comboBox.clear()
            self.ui.recentFiles_comboBox.addItems([''] + [Path(filepath).name for filepath in self.recent_files])

            # select the current background profile if it is in our list
            if self.aw.qmc.backgroundprofile is not None and self.aw.qmc.backgroundpath:
                try:
                    idx = self.recent_files.index(self.aw.qmc.backgroundpath)
                    self.ui.recentFiles_comboBox.setCurrentIndex(idx+1)
                except ValueError:
                    pass

                # background profile title
                self.ui.background_profile_label.setText(self.aw.qmc.titleB if self.aw.qmc.roastbatchnrB == 0 else
                        f'{self.aw.qmc.roastbatchprefixB}{self.aw.qmc.roastbatchnrB} {self.aw.qmc.titleB}')
                self.clearPushButtonSetEnabled()
            else:
                self.ui.background_profile_label.setText('')
                self.clearPushButtonSetDisabled()
        finally:
            self.ui.recentFiles_comboBox.blockSignals(False)


    def set_style(self) -> None:
        self.ui.title_comboBox.setStyleSheet(combobox_style(self.aw.app.darkmode, getStyleIconPath('arrow-down-01-stroke-rounded-light.svg'), 'bold'))
        self.ui.beans_textEdit.update_style(self.aw.app.darkmode)

    def update_recent_roast_buttons(self) -> None:
        if self.aw.qmc.title != QApplication.translate('Scope Title', 'Roaster Scope') and self.aw.qmc.weight[0] != 0:
            # enable "+" addRecentRoast button
            self.ui.plus_button.setEnabled(True)
            self.ui.minus_button.setEnabled(True)
        else:
            self.ui.plus_button.setEnabled(False)
            self.ui.minus_button.setEnabled(False)

    def update_compare_create_buttons(self) -> None:
        self.ui.compare_pushButton.setVisible(not self.aw.inProductionMode())
        self.ui.compare_pushButton.setEnabled(self.aw.curFile is not None)
        self.ui.compare_pushButton.setIcon(QIcon(getStyleIconPath(
            'git-compare-arrows-stroke-rounded-dark.svg' if self.aw.curFile is None else 'git-compare-arrows-stroke-rounded-light.svg')))
        #
        self.ui.create_pushButton.setVisible(not self.aw.inProductionMode())
        self.ui.create_pushButton.setEnabled(not self.aw.qmc.flagon)
        self.ui.create_pushButton.setIcon(QIcon(getStyleIconPath(
            'add-01-stroke-rounded-dark.svg' if self.aw.qmc.flagon else 'add-01-stroke-rounded-white.svg')))

    # slots

    @pyqtSlot(bool)
    def login_clicked(self, b:bool) -> None:
        del b
        import plus.controller as plus_controller
        plus_controller.toggle(self.aw)

    @pyqtSlot(int)
    def recent_roast_activated(self, i:int) -> None:
        # note, the first item is the edited text!
        if 0 < i <= len(self.aw.recentRoasts):
            rr = self.aw.recentRoasts[i-1]
            self.aw.setRecentRoast(rr)
            if 'background' in rr and rr['background'] is not None and rr['background'] != '':
                background_UUID = rr.get('roastUUID', None)
                self.aw.qmc.resetlinecountcaches()
                self.aw.loadAndRedrawBackgroundUUID(rr['background'],background_UUID)
            self.ui.title_comboBox.textEdited(rr['title'])
            self.ui.title_comboBox.setEditText(rr['title'])
#            self.update_dashboard(init_title=False) # not needed as this is done in loadAndRedraw
            self.aw.sendmessage(QApplication.translate('Message',f"Recent roast properties '{self.aw.recentRoastLabel(rr)}' set"))


    @pyqtSlot(str)
    def recent_roast_enabled(self, s:str) -> None:
        self.aw.qmc.title = s
        self.title_changed_timer.start(self.TITLE_CHANGE_ESTABLISH_PERIOD)

    @pyqtSlot()
    def title_changed(self) -> None:
        self.aw.qmc.title = self.aw.qmc.title
        self.update_recent_roast_buttons()
        self.aw.qmc.setProfileTitle(self.aw.qmc.title)

    @pyqtSlot(bool)
    def add_recent_roast(self, b:bool) -> None:
        del b
        try:
            if self.aw.qmc.title != QApplication.translate('Scope Title', 'Roaster Scope') and self.aw.qmc.weight[0] != 0:
                weightOut = volumeOut = densityRoasted = moistureRoasted = wholeColor = groundColor = None
                if QApplication.keyboardModifiers() == Qt.KeyboardModifier.AltModifier:  #alt click
                    # we add weightOut, volumeOut, moistureRoasted, wholeColor, groundColor
                    weightOut = self.aw.qmc.weight[1]
                    volumeOut = self.aw.qmc.volume[1]
                    densityRoasted = self.aw.qmc.density_roasted[0]
                    moistureRoasted = self.aw.qmc.moisture_roasted
                    wholeColor = self.aw.qmc.whole_color
                    groundColor = self.aw.qmc.ground_color
                rr = self.aw.createRecentRoast(
                    self.aw.qmc.title,
                    self.aw.qmc.beans,
                    self.aw.qmc.weight[0],
                    self.aw.qmc.weight[2],
                    self.aw.qmc.volume[0],
                    self.aw.qmc.volume[2],
                    self.aw.qmc.density[0],
                    self.aw.qmc.beansize_min,
                    self.aw.qmc.beansize_max,
                    self.aw.qmc.moisture_greens,
                    self.aw.qmc.color_systems[self.aw.qmc.color_system_idx],
                    self.aw.curFile, # could be empty
                    self.aw.qmc.roastUUID, # could be empty
                    self.aw.qmc.roastbatchnr, #self.batchcounterSpinBox # self.aw.superusermode and self.aw.qmc.batchcounter > -1
                    self.aw.qmc.roastbatchprefix,  #self.batchprefixedit
                    self.aw.plus_account,
                    self.aw.qmc.plus_store,
                    self.aw.qmc.plus_store_label,
                    self.aw.qmc.plus_coffee,
                    self.aw.qmc.plus_coffee_label,
                    self.aw.qmc.plus_blend_label,
                    self.aw.qmc.plus_blend_spec,
                    self.aw.qmc.plus_blend_spec_labels,
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

    @pyqtSlot(bool)
    def delete_recent_roast(self, b:bool) -> None:
        del b
        self.aw.recentRoasts = self.aw.delRecentRoast(self.aw.qmc.title, self.aw.qmc.weight[0], self.aw.qmc.weight[2])

    @pyqtSlot()
    def beans_edited(self) -> None:
        self.aw.qmc.beans = self.ui.beans_textEdit.toPlainText()
        self.aw.qmc.fileDirtySignal.emit()

    @pyqtSlot()
    def weightin_edited(self) -> None:
        if self.ui.weightinedit.text() == '':
            self.ui.weightinedit.setText(f'{float2floatWeightVolume(self.aw.qmc.weight[0]):g}')
        else:
            weight_in = comma2dot(str(self.ui.weightinedit.text()))
            self.ui.weightinedit.setText(weight_in)
            self.ui.weightinedit.repaint()
            try:
                self.aw.qmc.weight = (float(weight_in),self.aw.qmc.weight[1],self.aw.qmc.weight[2])
            except Exception: # pylint: disable=broad-except
                pass
            if self.aw.qmc.weight[0] != 0 and self.aw.qmc.density[0] != 0:
                weight_in_g = convertWeight(self.aw.qmc.weight[0],weight_units.index(self.aw.qmc.weight[2]),weight_units.index('g'))
                volume_in = weight_in_g / self.aw.qmc.density[0] # in g/l
                # convert to selected volume unit
                volume_in = convertVolume(volume_in,volume_units.index('l'),volume_units.index(self.aw.qmc.volume[2]))
                self.aw.qmc.volume = (volume_in, self.aw.qmc.volume[1], self.aw.qmc.volume[2])

            self.aw.qmc.fileDirtySignal.emit()
            # TODO (see roast_properties.py:weightineditChanged() :
            # + updated volume-in if green-density is set
            # - recentRoastEnabled() +/- buttons
            # - update plus popups => might also trigger an update on the beans edit
            # - check if enough stock, otherwise mark red!

    @pyqtSlot(int)
    def weight_unit_changed(self, i:int) -> None:
        previous_weight_unit_idx = weight_units.index(self.aw.qmc.weight[2]) # previous unit index
        weightUnit = self.ui.weight_unit_comboBox.currentText()
        if weightUnit == 'kg':
            weightUnit = 'Kg'
        new_weight_in = convertWeight(self.aw.qmc.weight[0],previous_weight_unit_idx,i)
        new_weight_out = convertWeight(self.aw.qmc.weight[1],previous_weight_unit_idx,i)
        self.ui.weightinedit.setText(f'{float2floatWeightVolume(new_weight_in):g}')
        self.aw.qmc.weight = (new_weight_in,new_weight_out,weightUnit)
        # TODO: update inventory popups like in roast_properties.py:changeWeightUnit

    @pyqtSlot(int)
    def recent_files_index_changed(self, i:int) -> None:
        if i > 0 and i-1 < len(self.recent_files):
            self.aw.loadBackgroundSignal.emit(self.recent_files[i-1], False)
            QTimer.singleShot(500, self.update_profile_section)

    @pyqtSlot(bool)
    def profile_load_clicked(self, b:bool) -> None:
        del b
        path:str|None = None
        if self.aw.qmc.backgroundprofile is not None and self.aw.qmc.backgroundpath:
            # if a background profile is loaded we open the file selector using its path
            path = self.aw.qmc.backgroundpath
        filename = self.aw.ArtisanOpenFileDialog(msg=QApplication.translate('Message','Load Background Roast Template'),path =path, ext='*.alog')
        if len(filename) != 0:
            self.aw.loadBackgroundSignal.emit(filename, False)

    @pyqtSlot(bool)
    def profile_clear_clicked(self, b:bool) -> None:
        del b
        self.aw.clearBackgroundSignal.emit()

    @pyqtSlot(bool)
    def open_scheduler(self, b:bool) -> None:
        del b
        if self.aw.plus_account is not None and not self.aw.app.artisanviewerMode:
            if self.aw.schedule_window is None:
                self.aw.start_scheduler()
            else:
                self.aw.schedule_window.activateWindow()


    @pyqtSlot(bool)
    def open_documentation_url(self, _b:bool) -> None:
        open_link(self.DOCUMENTATION_URL)

    @pyqtSlot(bool)
    def open_forum_url(self, _b:bool) -> None:
        open_link(self.USER_FORUM_URL)

    @pyqtSlot(bool)
    def open_issue_tracker_url(self, _b:bool) -> None:
        open_link(self.ISSUE_TRACKER_URL)

    @staticmethod
    @pyqtSlot(bool)
    def open_platform_url(_b:bool) -> None:
        open_link(plusLink())

    @pyqtSlot(bool)
    def open_donate_url(self, _b:bool) -> None:
        open_link(self.DONATE_URL)

    @staticmethod
    @pyqtSlot(bool)
    def open_sponsor_url(_b:bool) -> None:
        open_link(__release_sponsor_url__)

    @pyqtSlot(bool)
    def start_designer(self, _b:bool) -> None:
        self.aw.startdesigner(background_mode = True)
