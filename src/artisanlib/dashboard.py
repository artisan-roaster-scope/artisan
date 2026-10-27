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
from typing import Final, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import

from PyQt6.QtWidgets import QApplication, QWidget, QComboBox, QSizePolicy, QSpacerItem
from PyQt6.QtCore import Qt, QSettings, pyqtSlot, QTimer, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QFont, QFontDatabase, QIcon, QDesktopServices

from uic import DashboardWidget # pyright: ignore[attr-defined] # pylint: disable=no-name-in-module


from artisanlib import __release_sponsor_url__
from artisanlib.widgets import adjust_combobox_dropdown_width
from artisanlib.styles import combobox_style, dashboard_style
from artisanlib.util import (getStyleIconPath, float2floatWeightVolume, convertVolume, convertWeight, volume_units,
    weight_units, weight_units_lower, toStringList, comma2dot, getResourcePath, open_link, toInt, abbrevString,
    rgba_colorname2argb_colorname)
from artisanlib.styles import (tool_button_icon_style, artisan_push_button_style, tool_button_frame_style,
    artisan_minor_push_button_style, link_push_button_style, line_edit_style, separator_line_style)

import plus.stock
import plus.blend
import plus.connection
import plus.controller as plus_controller
from plus.util import plusLink, coffeeLink, storeLink, roastLink


_log: Final[logging.Logger] = logging.getLogger(__name__)



# lineedits: specify colors explicitly as OS dark/light-mode defaults don't apply here
LINE_EDIT_BACKGROUND_COLOR_DARK = '#70252525' #'#171717'
LINE_EDIT_BACKGROUND_COLOR_LIGHT = '#FFFFFF'
LINE_EDIT_COLOR_DARK = '#FFFFFF'
LINE_EDIT_COLOR_LIGHT = '#000000'
LINE_EDIT_BORDER_COLOR_DARK = '#555555'
LINE_EDIT_BORDER_COLOR_LIGHT = '#D7D7D7'

# sponsor logo background
SPONSOR_LOGO_BACKGROUND_COLOR_LIGHT = '#ffffff'
SPONSOR_LOGO_BACKGROUND_COLOR_DARK = '#4c97c3' #'#414456'
SPONSOR_LOGO_BACKGROUND_COLOR_HOVER_LIGHT = '#fBfBfB'
SPONSOR_LOGO_BACKGROUND_COLOR_HOVER_DARK = '#43a7cf' #'#494D61'
SPONSOR_LOGO_BACKGROUND_COLOR_PRESSED_LIGHT = '#f8f8f8'
SPONSOR_LOGO_BACKGROUND_COLOR_PRESSED_DARK = '#1985ba' #'#3A3C4C'


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

        # defaults

        self.beans_default:str = self.aw.qmc.beans
        self.density_default:float = self.aw.qmc.density[0]
        self.moisture_default:float = self.aw.qmc.moisture_greens
        self.screen_min_default:int = self.aw.qmc.beansize_min
        self.screen_max_default:int = self.aw.qmc.beansize_max

        # inventory section

        # variables populated by stock data as rendered in the corresponding popups
        self.plus_stores:list[tuple[str, str]]|None = None
        self.plus_coffees:list[tuple[str, tuple[plus.stock.Coffee, plus.stock.StockItem]]]|None = None
        self.plus_blends:list[plus.stock.BlendStructure]|None = None
        #
        self.plus_amount_selected:float|None = None # holds the max amount of the selected coffee/blend if known
        self.plus_amount_replace_selected:float|None = None # holds the max amount of the selected coffee/blend incl. replacements if known


        self.setUpdatesEnabled(False) # disable display updates
        try:
            self.ui = DashboardWidget.Ui_Dashboard()
            self.ui.setupUi(self)

            # configure inventory combos to allow for displaying stock in alternative unit on ALT/OPTION modifiers
            self.ui.beans_comboBox.set_get_current_unit(self.get_current_unit)
            self.ui.beans_comboBox.set_get_items(self.get_coffee_items)
            self.ui.blend_comboBox.set_get_current_unit(self.get_current_unit)
            self.ui.blend_comboBox.set_get_items(self.get_blend_items)

            # set static styles
            self.ui.login_pushButton.setStyleSheet(artisan_push_button_style())
            self.ui.donate_pushButton.setStyleSheet(artisan_push_button_style())

            header_styles:Final[str] = 'QLabel{color:rgb(40, 153, 199);background-color:transparent;}'
            self.ui.roast_label.setStyleSheet(header_styles)
            self.ui.profile_label.setStyleSheet(header_styles)
            self.ui.links_label.setStyleSheet(header_styles)
            self.ui.sponsor_label.setStyleSheet(header_styles)
            self.ui.donate_label.setStyleSheet(header_styles)

            self.ui.plus_button.setFixedSize(QSize(26,26))
            self.ui.minus_button.setFixedSize(QSize(26,26))

            # set label and tooltips with translations
            self.fill_labels_and_tooltips()

            artisan_font_semibold_file = os.path.join(getResourcePath(),'Nunito-SemiBold.ttf')
            artisan_font_semibold_id = QFontDatabase.addApplicationFont(artisan_font_semibold_file)
            artisan_font_semibold_families = QFontDatabase.applicationFontFamilies(artisan_font_semibold_id)
            artisan_font_normal = os.path.join(getResourcePath(),'Nunito-Regular.ttf')
            artisan_font_normal_id = QFontDatabase.addApplicationFont(artisan_font_normal)
            artisan_font_normal_families = QFontDatabase.applicationFontFamilies(artisan_font_normal_id)

            # factor 96 (Windows) to 72 (macOS): 75/96 = 0.75
            main_header_font_size = (15 if platform.system() != 'Darwin' else 20)
            sub_header_font_size = (10 if platform.system() != 'Darwin' else 14)
            self.ui.roast_label.setFont(QFont(artisan_font_semibold_families[0], main_header_font_size, QFont.Weight.DemiBold))
            self.ui.profile_label.setFont(QFont(artisan_font_semibold_families[0], main_header_font_size, QFont.Weight.DemiBold))
            self.ui.inventory_group.setFont(QFont(artisan_font_normal_families[0], sub_header_font_size, QFont.Weight.Normal))
            self.ui.links_label.setFont(QFont(artisan_font_normal_families[0], sub_header_font_size, QFont.Weight.Normal))
            self.ui.sponsor_label.setFont(QFont(artisan_font_normal_families[0], sub_header_font_size, QFont.Weight.Normal))
            self.ui.donate_label.setFont(QFont(artisan_font_normal_families[0], sub_header_font_size, QFont.Weight.Normal))

            selected_label_font = self.ui.selected_line_label.font()
            selected_label_font.setPointSize(selected_label_font.pointSize() -2)
            self.ui.selected_line_label.setFont(selected_label_font)
            self.ui.selected_line_label.setMaximumWidth(450) # prevent overflow into the INVENTORY group label

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
            self.ui.compare_pushButton.setIcon(QIcon(getStyleIconPath('git-compare-arrows-stroke-rounded.svg')))

            self.ui.donate_pushButton.setIconSize(QSize(20,20))
            self.ui.donate_pushButton.setIcon(QIcon(getStyleIconPath('heart-handshake-stroke-rounded-white.svg')))

            self.ui.plus_button.setIconSize(QSize(20,20))
            self.ui.plus_button.setIcon(QIcon(getStyleIconPath('add-01-stroke-rounded-white.svg')))

            self.ui.minus_button.setIconSize(QSize(20,20))
            self.ui.minus_button.setIcon(QIcon(getStyleIconPath('remove-01-stroke-rounded-white.svg')))

            self.ui.login_pushButton.setIconSize(QSize(20,20))
            self.ui.login_pushButton.setIcon(QIcon(getStyleIconPath('user-circle-stroke-rounded-dark.svg')))

            self.ui.documentation_pushButton.setIconSize(QSize(10,10))
            self.ui.documentation_pushButton.setIcon(QIcon(getStyleIconPath('external-link-stroke-rounded.svg')))
            self.ui.forum_pushButton.setIconSize(QSize(10,10))
            self.ui.forum_pushButton.setIcon(QIcon(getStyleIconPath('external-link-stroke-rounded.svg')))
            self.ui.issue_pushButton.setIconSize(QSize(10,10))
            self.ui.issue_pushButton.setIcon(QIcon(getStyleIconPath('external-link-stroke-rounded.svg')))
            self.ui.platform_pushButton.setIconSize(QSize(10,10))
            self.ui.platform_pushButton.setIcon(QIcon(getStyleIconPath('external-link-stroke-rounded.svg')))

            self.ui.weightinedit.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, self.ui.weightinedit))  # the max limit has to be high enough otherwise the connected signals are not send!

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
            self.ui.upload_toolButton.clicked.connect(self.aw.qmc.uploadProfile)

            self.ui.roast_link_toolButton.clicked.connect(self.open_roast_on_platform)
            self.ui.template_link_toolButton.clicked.connect(self.open_template_on_platform)

            self.ui.create_pushButton.clicked.connect(self.start_designer)
            self.ui.compare_pushButton.clicked.connect(self.aw.roastCompare)

            self.ui.sync.clicked.connect(self.trigger_stock_update)

            self.ui.documentation_pushButton.clicked.connect(self.open_documentation_url)
            self.ui.forum_pushButton.clicked.connect(self.open_forum_url)
            self.ui.issue_pushButton.clicked.connect(self.open_issue_tracker_url)
            self.ui.platform_pushButton.clicked.connect(self.open_platform_url)
            self.ui.donate_pushButton.clicked.connect(self.open_donate_url)
            self.ui.sponsor_logo_toolButton.clicked.connect(self.open_sponsor_url)

            self.ui.beans_comboBox.currentIndexChanged.connect(self.coffeeSelectionChanged)
            self.ui.blend_comboBox.currentIndexChanged.connect(self.blendSelectionChanged)
            self.ui.space_comboBox.currentIndexChanged.connect(self.storeSelectionChanged)
            self.ui.custom_blend.clicked.connect(self.customBlendButton_triggered)

        finally:
            self.setUpdatesEnabled(True) # re-enable display updates

###


    def get_current_unit(self) -> int:
        try:
            return weight_units.index(self.aw.qmc.weight[2])
        except Exception:  # pylint: disable=broad-except
            return 0

    def get_coffee_items(self, unit:int) -> list[str]:
        plus_coffees = plus.stock.getCoffees(unit, self.aw.qmc.plus_default_store)
        return [''] + plus.stock.getCoffeesLabels(plus_coffees)

    def get_blend_items(self, unit:int) -> list[str]:
        custom_blend:plus.stock.Blend|None = None
        if self.aw.qmc.plus_custom_blend is not None and self.aw.qmc.plus_custom_blend.name.strip() != '':
            coffees = plus.stock.getCoffeeLabels()
            if len(coffees)>1 and self.aw.qmc.plus_custom_blend.isValid(coffees.values()):
                custom_blend = plus.stock.Blend(
                    hr_id = '',
                    label = self.aw.qmc.plus_custom_blend.name.strip(),
                    ingredients = [plus.stock.BlendIngredient(ratio = c.ratio, coffee= c.coffee) for c in self.aw.qmc.plus_custom_blend.components])
        plus_blends = plus.stock.getBlends(unit,self.aw.qmc.plus_default_store, custom_blend)
        blend_items:list[str] = plus.stock.getBlendLabels(plus_blends)
        return [''] + blend_items

    ##

    def fill_labels_and_tooltips(self) -> None:

        # ROAST
        self.ui.roast_label.setText(QApplication.translate('Menu', 'Roast').upper())
        self.ui.title_label.setText(QApplication.translate('Label', 'Title'))
        self.ui.batchsize_label.setText(QApplication.translate('Label', 'Batch size'))
        self.ui.beans_textEdit.setPlaceholderText(QApplication.translate('Label', 'Beans'))
        self.ui.compare_pushButton.setText(QApplication.translate('Button', 'Compare'))
        self.ui.properties_pushButton.setText(QApplication.translate('Button', 'Properties'))
        self.ui.inventory_group.setTitle(QApplication.translate('GroupBox', 'INVENTORY'))
        self.ui.login_pushButton.setText(QApplication.translate('Button', 'LOGIN TO UNLOCK'))
        self.ui.beans_label.setText(QApplication.translate('Label', 'Beans'))
        self.ui.blend_label.setText(QApplication.translate('Label', 'Blend'))
        self.ui.space_label.setText(QApplication.translate('Label', 'Space'))

        self.ui.roast_label.setToolTip(QApplication.translate('Tooltip','Essential roast properties'))
        self.ui.batch_nr.setToolTip(QApplication.translate('Tooltip','Batch number'))
        self.ui.roast_link_toolButton.setToolTip(QApplication.translate('Tooltip','Open roast on platform'))
        self.ui.scheduler_frame.setToolTip(QApplication.translate('Tooltip','Open your roast schedule'))
        self.ui.upload_frame.setToolTip(QApplication.translate('Tooltip','Upload this roast'))
        self.ui.title_comboBox.setToolTip(QApplication.translate('Tooltip','Enter the roast title or set properties by choosing from a recent roast'))
        self.ui.plus_button.setToolTip(QApplication.translate('Tooltip', 'Add roast properties to list of recent roasts'))
        self.ui.minus_button.setToolTip(QApplication.translate('Tooltip', 'Remove roast properties from list of recent roasts'))

        self.ui.inventory_group.setToolTip(QApplication.translate('Tooltip', 'Green beans inventory'))
        self.ui.login_pushButton.setToolTip(QApplication.translate('Plus', 'Sign in to your artisan account'))
        self.ui.selected_line_label.setToolTip(QApplication.translate('Plus', 'Links to selected beans, blend and space on the platform'))
        self.ui.beans_comboBox.setToolTip(QApplication.translate('Tooltip', 'Select beans from your inventory'))
        self.ui.beans_label.setToolTip(QApplication.translate('Tooltip', 'Select beans from your inventory'))
        self.ui.blend_comboBox.setToolTip(QApplication.translate('Tooltip', 'Select a blend from your inventory'))
        self.ui.blend_label.setToolTip(QApplication.translate('Tooltip', 'Select a blend from your inventory'))
        self.ui.space_comboBox.setToolTip(QApplication.translate('Tooltip', 'Select a storage space'))
        self.ui.space_label.setToolTip(QApplication.translate('Tooltip', 'Select a storage space'))
        self.ui.custom_blend.setToolTip(QApplication.translate('Tooltip', 'Define a custom blend'))
        self.ui.sync.setToolTip(QApplication.translate('Tooltip', 'Update inventory from platform'))
        self.ui.beans_textEdit.setToolTip(QApplication.translate('Tooltip', 'Description of the green beans used'))
        self.ui.weightinedit.setToolTip(QApplication.translate('Tooltip', 'batch size'))
        self.ui.weight_unit_comboBox.setToolTip(QApplication.translate('Tooltip', 'weight unit'))
        self.ui.properties_pushButton.setToolTip(QApplication.translate('Tooltip', 'Open roast properties dialog'))
        self.ui.compare_pushButton.setToolTip(QApplication.translate('Tooltip', 'Open roast in {}').format(QApplication.translate('Menu', 'Comparator')))

        # TEMPLATE
        self.ui.profile_label.setText(QApplication.translate('Label', 'TEMPLATE'))
        self.ui.load_pushButton.setText(QApplication.translate('Button', 'Load'))
        self.ui.clear_pushButton.setText(QApplication.translate('Button', 'Clear'))
        self.ui.create_pushButton.setText(QApplication.translate('Button', 'Create'))

        self.ui.profile_label.setToolTip(QApplication.translate('Tooltip','Background roast template'))
        self.ui.background_profile_label.setToolTip(QApplication.translate('Tooltip','Name of current background template'))
        self.ui.template_link_toolButton.setToolTip(QApplication.translate('Tooltip','Open template on platform'))
        self.ui.load_pushButton.setToolTip(QApplication.translate('Tooltip','Load a profile as template into the background'))
        self.ui.recentFiles_comboBox.setToolTip(QApplication.translate('Tooltip','Choose a recent roast and load as roast template'))
        self.ui.clear_pushButton.setToolTip(QApplication.translate('Tooltip','Remove the loaded background roast template'))
        self.ui.create_pushButton.setToolTip(QApplication.translate('Tooltip','Start the {} and create a background roast template').format(QApplication.translate('Menu', 'Designer')))

        # LINKS
        self.ui.links_label.setText(QApplication.translate('Label', 'QUICK LINKS'))
        self.ui.documentation_pushButton.setText(QApplication.translate('Button', 'Documentation'))
        self.ui.forum_pushButton.setText(QApplication.translate('Button', 'User Forum'))
        self.ui.issue_pushButton.setText(QApplication.translate('Button', 'Report an Issue'))
        self.ui.platform_pushButton.setText(QApplication.translate('Button', 'Web Platform'))


        self.ui.links_label.setToolTip(QApplication.translate('Tooltip','Links to external information and services'))
        self.ui.documentation_pushButton.setToolTip(QApplication.translate('Tooltip','Explore the documentation'))
        self.ui.forum_pushButton.setToolTip(QApplication.translate('Tooltip','Ask questions, share tips, and connect with the community'))
        self.ui.issue_pushButton.setToolTip(QApplication.translate('Tooltip','Report a bug or request a feature'))
        self.ui.platform_pushButton.setToolTip(QApplication.translate('Tooltip','Browse to the artisan platform'))

        # SPONSOR
        self.ui.sponsor_label.setText(QApplication.translate('Label', 'RELEASE SPONSOR'))

        self.ui.sponsor_label.setToolTip(QApplication.translate('Tooltip','Sponsor of this release'))
        self.ui.sponsor_logo_toolButton.setToolTip(QApplication.translate('Tooltip','Visit our sponsor'))

        # DONATION
        self.ui.donate_label.setText(QApplication.translate('Label', 'SUPPORT ARTISAN'))
        self.ui.donate_pushButton.setText(QApplication.translate('Button', 'DONATE'))

        self.ui.donate_label.setToolTip(QApplication.translate('Tooltip','Help to keep artisan going'))
        self.ui.donate_pushButton.setToolTip(QApplication.translate('Tooltip','Send your donation'))
        self.ui.starts_label.setToolTip(QApplication.translate('Tooltip','Counts total number of recordings'))


    def dashboard_active(self) -> bool:
        return self.aw.stack.currentIndex() == 1

    def toggle_dashboard(self) -> None:
        if self.dashboard_active():
            self.hide_dashboard()
        else:
            self.show_dashboard()


    def disable_graph_tools(self) -> None:
        for graph_tool in [self.aw.ntb.home_tool, self.aw.ntb.back_tool, self.aw.ntb.forward_tool,
                self.aw.ntb.pan_tool, self.aw.ntb.zoom_tool, self.aw.ntb.edit_curve_parameters_action]:
            if graph_tool is not None:
                graph_tool.setVisible(False)
        self.update_hello_message()

    def enable_graph_tools(self) -> None:
        for graph_tool in [self.aw.ntb.home_tool, self.aw.ntb.back_tool, self.aw.ntb.forward_tool,
                self.aw.ntb.pan_tool, self.aw.ntb.zoom_tool, self.aw.ntb.edit_curve_parameters_action]:
            if graph_tool is not None:
                graph_tool.setVisible(True)
        self.aw.ntb.locLabel.setText('')

    def enable_dashboard_toggle_toolbutton(self) -> None:
        if self.aw.ntb.dashboard_tool is not None:
            self.aw.ntb.dashboard_tool.setVisible(True)

    def disable_dashboard_toggle_toolbutton(self) -> None:
        if self.aw.ntb.dashboard_tool is not None:
            self.aw.ntb.dashboard_tool.setVisible(False)

    def show_dashboard(self) -> None:
        if not (self.aw.qmc.designerflag or self.aw.comparator is not None):
            self.update_dashboard(force=True)
            self.aw.stack.setCurrentIndex(1)
            # always update tool icons
            self.update_tool_icons()
            self.aw.ntb.update_tools() # as we updated the dashboard above before making it visible we have to update the tools again here
            self.enable_dashboard_toggle_toolbutton()
            self.disable_graph_tools()

    @staticmethod
    @pyqtSlot(bool)
    def trigger_stock_update(_:bool = False) -> None:
        QTimer.singleShot(10, plus.stock.update) # full stock update (returns data even if schedule did not change)

    @pyqtSlot()
    def hide_dashboard(self) -> None:
        self.aw.stack.setCurrentIndex(0)
        # always update tool icons
        self.update_tool_icons()
        self.aw.ntb.update_tools()
        if (self.aw.qmc.designerflag or self.aw.comparator is not None):
            # disable dashboard/graph toggle toolbar button
            # if designer or comparator is open
            self.disable_dashboard_toggle_toolbutton()
        self.enable_graph_tools()

    # if force, update even if not visible
    # if init_title, the title popup is re-initialized (only needed if the popup content changes, not if only the title changes)
    # if dark_canvas, the corresponding style matching a dark canvas is selected
    def update_dashboard(self, force:bool=False, init_title:bool=True) -> None:
        darkmode = self.aw.dark_canvas_p()

        if force or self.aw.stack.currentIndex() == 1:
            # only update if visible

            self.ui.recentFiles_comboBox.blockSignals(True)
            try:
                # overall style
                self.update_main_style(darkmode)

                # batch number
                if self.aw.qmc.roastbatchnr == 0 and self.aw.curFile is None:
                    # batch number reserved but not yet realized
                    batch_pos = self.aw.qmc.batchsequence
                    batch_nr = self.aw.qmc.batchcounter + 1
                    self.ui.batch_nr.setEnabled(False)
                else:
                    # batch number set
                    batch_pos = self.aw.qmc.roastbatchpos
                    batch_nr = self.aw.qmc.roastbatchnr
                    self.ui.batch_nr.setEnabled(True)
                roastpos = ('' if batch_nr == 0 else f' ({batch_pos})')
                self.ui.batch_nr.setText('' if batch_nr == 0 else f'{self.aw.qmc.roastbatchprefix}{batch_nr}{roastpos}')

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
                try:
                    # prevent a call to self.weightin_edited() which should be called only on user input
                    self.ui.weightinedit.blockSignals(True)
                    self.ui.weightinedit.setText(f'{float2floatWeightVolume(self.aw.qmc.weight[0]):g}')
                finally:
                    self.ui.weightinedit.blockSignals(False)

                # weight unit
                try:
                    # prevent a call to self.weight_unit_changed() which should be called only on user input
                    self.ui.weight_unit_comboBox.blockSignals(True)
                    self.ui.weight_unit_comboBox.setCurrentIndex(weight_units.index(self.aw.qmc.weight[2]))
                finally:
                    self.ui.weight_unit_comboBox.blockSignals(False)

                # profile
                self.update_profile_section()

                # release sponsor
                self.update_release_sponsor(darkmode)

                # starts
                settings = QSettings()
                starts = 0
                if settings.contains('starts'):
                    starts = toInt(settings.value('starts'))
                    self.ui.starts_label.setText(QApplication.translate('Label',"You've roasted {} batches").format(starts))
            finally:
                self.ui.recentFiles_comboBox.blockSignals(False)

        # always update tool icons
        self.update_tool_icons()
        self.aw.ntb.update_tools()

    def update_release_sponsor(self, darkmode:bool) -> None:
        if __release_sponsor_url__ == '': # pyright:ignore[reportUnnecessaryComparison]
            self.ui.groupBox_sponsor.setVisible(False)
        else:
            try:
                self.ui.sponsor_logo_toolButton.setIcon(QIcon(Path.as_posix(Path(getResourcePath()).joinpath(
                    'release-sponsor-logo-dark.svg' if darkmode else 'release-sponsor-logo.svg'))))
                self.ui.sponsor_logo_toolButton.setIconSize(QSize(150,75))
                self.ui.sponsor_logo_toolButton.setStyleSheet(f"""
                    FixedRatio2ToolButton {{
                        background-color: {SPONSOR_LOGO_BACKGROUND_COLOR_DARK
                            if darkmode else SPONSOR_LOGO_BACKGROUND_COLOR_LIGHT};
                        border: 0px solid;
                        border-radius: 10px;
                        min-width: 176px;
                        max-width: 176px;
                    }}
                    FixedRatio2ToolButton:hover {{
                        background-color: {SPONSOR_LOGO_BACKGROUND_COLOR_HOVER_DARK
                            if darkmode else SPONSOR_LOGO_BACKGROUND_COLOR_HOVER_LIGHT};
                    }}
                    FixedRatio2ToolButton:pressed {{
                        background-color: {SPONSOR_LOGO_BACKGROUND_COLOR_PRESSED_DARK
                            if darkmode else SPONSOR_LOGO_BACKGROUND_COLOR_PRESSED_LIGHT};
                    }}
                """)
            except Exception: # pylint: disable=broad-except
                self.ui.groupBox_sponsor.setVisible(False)

    def update_main_style(self, darkmode:bool) -> None:
        self.setStyleSheet(dashboard_style(darkmode, self.aw.dashboard_background_image is not None, rgba_colorname2argb_colorname(self.aw.qmc.palette['canvas'])))
        # sponsor
        self.update_release_sponsor(darkmode)
        # push buttons
        self.ui.plus_button.setStyleSheet(artisan_push_button_style(darkmode))
        self.ui.minus_button.setStyleSheet(artisan_push_button_style(darkmode))
        self.ui.properties_pushButton.setStyleSheet(artisan_minor_push_button_style(darkmode, True))
        self.ui.compare_pushButton.setStyleSheet(artisan_minor_push_button_style(darkmode, True))
        self.ui.load_pushButton.setStyleSheet(artisan_minor_push_button_style(darkmode, True))
        self.ui.clear_pushButton.setStyleSheet(artisan_minor_push_button_style(darkmode, True))
        self.ui.create_pushButton.setStyleSheet(artisan_minor_push_button_style(darkmode, True))
        # tool buttons
        self.ui.custom_blend.setStyleSheet(tool_button_icon_style(darkmode,
            'pencil-edit-02-stroke-rounded-light.svg', 'pencil-edit-02-stroke-rounded-dark.svg'))
        self.ui.sync.setStyleSheet(tool_button_icon_style(darkmode,
            'update-light.svg', 'update-dark.svg'))
        #
        self.ui.scheduler_toolButton.setStyleSheet(tool_button_icon_style(darkmode,
            'calendar-03-stroke-rounded-blue.svg', 'calendar-03-stroke-rounded-blue.svg'))
        self.update_schedule_toolbutton()
        #
        self.ui.upload_toolButton.setStyleSheet(tool_button_icon_style(darkmode,
            'upload-01-stroke-rounded-blue.svg', 'upload-01-stroke-rounded-blue.svg'))
        self.update_upload_toolButton()
        #
        self.ui.roast_frame.setStyleSheet(separator_line_style(darkmode))
        self.ui.profile_frame.setStyleSheet(separator_line_style(darkmode))
        #
        self.ui.documentation_pushButton.setStyleSheet(link_push_button_style(darkmode))
        self.ui.forum_pushButton.setStyleSheet(link_push_button_style(darkmode))
        self.ui.issue_pushButton.setStyleSheet(link_push_button_style(darkmode))
        self.ui.platform_pushButton.setStyleSheet(link_push_button_style(darkmode))
        #
        self.ui.title_comboBox.setStyleSheet(combobox_style(
            darkmode,
            getStyleIconPath('arrow-down-01-stroke-rounded-dark.svg' if darkmode else 'arrow-down-01-stroke-rounded-light.svg'),
            'bold'))
        combobox_stylesheet = combobox_style(
            darkmode,
            getStyleIconPath('arrow-down-01-stroke-rounded-dark.svg' if darkmode else 'arrow-down-01-stroke-rounded-light.svg'))
        for combo_box in [self.ui.weight_unit_comboBox, self.ui.recentFiles_comboBox,
                self.ui.beans_comboBox, self.ui.blend_comboBox, self.ui.space_comboBox]:
            combo_box.setStyleSheet(combobox_stylesheet)
        #
        #
        self.ui.weightinedit.setStyleSheet(
            line_edit_style(
                darkmode,
                color = (LINE_EDIT_COLOR_DARK if darkmode else LINE_EDIT_COLOR_LIGHT),
                background_color = (LINE_EDIT_BACKGROUND_COLOR_DARK if darkmode else LINE_EDIT_BACKGROUND_COLOR_LIGHT)))
        self.ui.beans_textEdit.update_style(darkmode,
            background_color = (LINE_EDIT_BACKGROUND_COLOR_DARK if darkmode else LINE_EDIT_BACKGROUND_COLOR_LIGHT),
            border_color = (LINE_EDIT_BORDER_COLOR_DARK if darkmode else LINE_EDIT_BORDER_COLOR_LIGHT),
            color = (LINE_EDIT_COLOR_DARK if darkmode else LINE_EDIT_COLOR_LIGHT))

    def update_background(self) -> None:
        darkmode = self.aw.dark_canvas_p()
        if self.aw.dashboard_background_image is None:
            self.aw.stack.setStyleSheet('QStackedWidget {{background-color: transparent; }}')
        else:
            self.aw.stack.setStyleSheet(f'QStackedWidget {{background-color: transparent; background-image: url({Path.as_posix(Path(self.aw.dashboard_background_image))}); }}')
        if self.aw.dashboard_background_image is None or darkmode:
            for pane in [self.ui.groupBox_roast, self.ui.groupBox_profile, self.ui.groupBox_links,
                    self.ui.groupBox_links, self.ui.groupBox_donation]:
                pane.setGraphicsEffect(None)
        else:
            for pane in [self.ui.groupBox_roast, self.ui.groupBox_profile, self.ui.groupBox_links,
                    self.ui.groupBox_links, self.ui.groupBox_donation]:
                pane.setGraphicsEffect(self.aw.makeShadow(strong=True))
        self.update_image_tool_icon()
        # update overall style to get the border color of the panes right
        self.update_main_style(darkmode)


#---- move to main.py
    def update_tool_icons(self) -> None:
        self.update_image_tool_icon()
        self.update_exit_tool_icon()

    def update_image_tool_icon(self) -> None:
        if self.aw.stack.currentIndex() == 1 and self.aw.inExpertMode():
            # dashboard visible
            self.aw.dashboardImageToolButton.setStyleSheet(tool_button_icon_style(
                self.aw.dark_canvas_p(),
                ('image-02-stroke-rounded-light.svg' if self.aw.dashboard_background_image is None else 'image-not-found-01-stroke-rounded-light.svg'),
                ('image-02-stroke-rounded-dark.svg' if self.aw.dashboard_background_image is None else 'image-not-found-01-stroke-rounded-dark.svg')))
            self.aw.dashboardImageToolButton.setToolTip(QApplication.translate('Tooltip','Set background image') if self.aw.dashboard_background_image is None else
                QApplication.translate('Tooltip','Remove background image'))
            self.aw.dashboardImageToolButton.setVisible(True)
        else:
            # dashboard hidden
            self.aw.dashboardImageToolButton.setVisible(False)

    def update_exit_tool_icon(self) -> None:
        if self.aw.qmc.designerflag or self.aw.qmc.wheelflag:
            # designer exit button visible
            self.aw.exitToolButton.setStyleSheet(tool_button_icon_style(
                self.aw.dark_canvas_p(),
                'cancel-square-stroke-rounded-light.svg',
                'cancel-square-stroke-rounded-dark.svg'
                ))
            self.aw.exitToolButton.setVisible(True)
        else:
            # designer exit button hidden
            self.aw.exitToolButton.setVisible(False)
#----

    def update_schedule_toolbutton(self) -> None:
        darkmode = self.aw.dark_canvas_p()
        self.ui.scheduler_toolButton.setStyleSheet(tool_button_icon_style(darkmode,
            ('calendar-03-stroke-rounded-dark.svg' if self.aw.plus_account is None or self.aw.app.artisanviewerMode else 'calendar-03-stroke-rounded-blue.svg'),
            ('calendar-03-stroke-rounded-dark.svg' if self.aw.plus_account is None or self.aw.app.artisanviewerMode else 'calendar-03-stroke-rounded-blue.svg')))
        # scheduler tool button frame
        self.ui.scheduler_frame.setStyleSheet(tool_button_frame_style(darkmode))

    def update_hello_message(self) -> None:
        hello_message:str = ''
        if self.aw.plus_account is not None and plus_controller.is_connected():
            nickname = plus.connection.getNickname()
            if nickname:
                hello_message = QApplication.translate('Label','Hello {}!').format(nickname)
        self.aw.ntb.locLabel.setText(hello_message)

    # visible only if logged in as MAX
    # enabled only if no roastUID or not long enough
    def update_upload_toolButton(self) -> None:
        if self.aw.plus_account is None or self.aw.plus_subscription != 'MAX':
            self.ui.upload_frame.setVisible(False)
            # hide spacer
            item = self.ui.horizontalLayout.itemAt(5)
            if isinstance(item, QSpacerItem):
                item.changeSize(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
                self.ui.horizontalLayout.invalidate()
        else:
            darkmode = self.aw.dark_canvas_p()
            enabled = bool(self.aw.qmc.roastUUID and len(self.aw.qmc.timex) > 20)
            self.ui.upload_toolButton.setEnabled(enabled)
            self.ui.upload_frame.setEnabled(enabled)
            self.ui.upload_toolButton.setStyleSheet(tool_button_icon_style(darkmode,
                ('upload-01-stroke-rounded-blue.svg' if enabled else 'upload-01-stroke-rounded-dark.svg'),
                ('upload-01-stroke-rounded-blue.svg' if enabled else ('upload-01-stroke-rounded-white.svg' if darkmode else 'upload-01-stroke-rounded-dark.svg'))))
            # upload tool button frame
            self.ui.upload_frame.setStyleSheet(tool_button_frame_style(darkmode))
            self.ui.upload_frame.setVisible(True)
            # show spacer
            item = self.ui.horizontalLayout.itemAt(5)
            if isinstance(item, QSpacerItem):
                item.changeSize(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                self.ui.horizontalLayout.invalidate()

    def update_roast_link_toolbutton(self) -> None:
        darkmode = self.aw.dark_canvas_p()
        if self.aw.plus_account is None or self.aw.app.artisanviewerMode or not self.aw.qmc.roastUUID or not plus_controller.is_synced():
            self.ui.roast_link_toolButton.setVisible(False)
        else:
            self.ui.roast_link_toolButton.setVisible(True)
            self.ui.roast_link_toolButton.setStyleSheet(tool_button_icon_style(darkmode,
                'external-link-stroke-rounded-blue.svg',
                'external-link-stroke-rounded-blue.svg'))

    def update_template_link_toolbutton(self) -> None:
        darkmode = self.aw.dark_canvas_p()
        template_uuid:str|None = (self.aw.qmc.backgroundprofile['roastUUID'] if self.aw.qmc.backgroundprofile is not None and
            'roastUUID' in self.aw.qmc.backgroundprofile else None)
        if self.aw.plus_account is None or self.aw.app.artisanviewerMode or not template_uuid:
            self.ui.template_link_toolButton.setVisible(False)
        else:
            self.ui.template_link_toolButton.setVisible(True)
            self.ui.template_link_toolButton.setStyleSheet(tool_button_icon_style(darkmode,
                'external-link-stroke-rounded-blue.svg',
                'external-link-stroke-rounded-blue.svg'))


    def update_inventory_section(self, force:bool=False) -> None:
        if force or self.aw.stack.currentIndex() == 1:
            self.ui.inventory_stackedWidget.setCurrentIndex(0 if self.aw.plus_account is None else 1)

            # enable/disable scheduler tool button
            self.ui.scheduler_frame.setEnabled(self.aw.plus_account is not None and not self.aw.app.artisanviewerMode)  # no scheduler in ArtisanViewer mode
            # scheduler tool icon
            self.update_schedule_toolbutton()

            # enable/disable upload tool button
            self.ui.upload_frame.setEnabled(self.aw.plus_account is not None and not self.aw.app.artisanviewerMode)
            # upload tool icon
            self.update_upload_toolButton()

            self.update_roast_link_toolbutton()

            # update inventory section content
            if self.aw.plus_account is not None:
                plus.stock.init() # we try to init the stock from the cache before populating the popups

                self.populatePlusCoffeeBlendCombos()

                # current selected stock/coffee/blend _id
                # try to generate self.aw.qmc.plus_blend_spec_labels from self.aw.qmc.plus_blend_spec and current stock
                # if any coffee is missing from current stock, we keep what we have stored in the alog file
                if self.aw.qmc.plus_blend_spec is not None and 'ingredients' in self.aw.qmc.plus_blend_spec: # pyrefly: ignore
                    generated_blend_spec_labels:list[str] = []
                    for i in self.aw.qmc.plus_blend_spec['ingredients']: # pyrefly: ignore
                        c = plus.stock.getCoffee(i['coffee'])
                        if c is None:
                            generated_blend_spec_labels = [] # clear the list
                            break
                        generated_blend_spec_labels.append(c.get('label', ''))
                    if generated_blend_spec_labels:
                        self.aw.qmc.plus_blend_spec_labels = generated_blend_spec_labels

                self.updatePlusSelectedLine()

            else:
                self.ui.selected_line_label.setText('')
            self.update_hello_message()


    def updatePlusSelectedLine(self) -> None:
        try:
            darkmode = self.aw.dark_canvas_p()
            if darkmode:
                dark_mode_link_color = " style=\"color: #e5e9ec;\""
            else:
                dark_mode_link_color = ''
            line = ''
            if self.aw.qmc.plus_coffee is not None and self.aw.qmc.plus_coffee_label:
                line = f'<a href="{coffeeLink(self.aw.qmc.plus_coffee)}"{dark_mode_link_color}>{self.aw.qmc.plus_coffee_label}</a>'
            elif self.aw.qmc.plus_blend_spec and self.aw.qmc.plus_blend_spec_labels:
                # limit to max 3 component links
                line = f'{self.aw.qmc.plus_blend_label}: '
                first_component = True
                for i, ll in sorted(zip(self.aw.qmc.plus_blend_spec['ingredients'], self.aw.qmc.plus_blend_spec_labels, strict=True), key=lambda tup:tup[0]['ratio'],reverse = True)[:3]:
                    if first_component:
                        first_component = False
                    else:
                        line = line + ', '
                    c = f"<a href=\"{coffeeLink(i['coffee'])}\"{dark_mode_link_color}>{abbrevString(ll, 18)}</a>"
                    line = line + str(int(round(i['ratio']*100))) + '% ' + c
            if line and len(line)>0 and self.aw.qmc.plus_store is not None and self.aw.qmc.plus_store_label is not None:
                line = line + f'  (<a href="{storeLink(self.aw.qmc.plus_store)}"{dark_mode_link_color}>{self.aw.qmc.plus_store_label}</a>)'
#            if line == '':
#                # beans not specified
#                line = QApplication.translate('Label','Choose beans')

            self.ui.selected_line_label.setText(line)
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)

    def updateTitle(self, prev_coffee_label:str|None, prev_blend_label:str|None) -> None:
        titles_to_be_overwritten = [ '', QApplication.translate('Scope Title', 'Roaster Scope') ]
        if prev_coffee_label is not None:
            titles_to_be_overwritten.append(prev_coffee_label)
        if prev_blend_label is not None:
            titles_to_be_overwritten.append(prev_blend_label)
        if self.ui.title_comboBox.currentText() in titles_to_be_overwritten:
            if self.aw.qmc.plus_blend_label is not None:
                self.ui.title_comboBox.textEdited(self.aw.qmc.plus_blend_label)
                self.ui.title_comboBox.setEditText(self.aw.qmc.plus_blend_label)
            elif self.aw.qmc.plus_coffee_label is not None:
                self.ui.title_comboBox.textEdited(self.aw.qmc.plus_coffee_label)
                self.ui.title_comboBox.setEditText(self.aw.qmc.plus_coffee_label)
            else:
                default_title = QApplication.translate('Scope Title', 'Roaster Scope')
                self.ui.title_comboBox.textEdited(default_title)
                self.ui.title_comboBox.setEditText(default_title)


    @pyqtSlot(int)
    def storeSelectionChanged(self, n:int) -> None:
        if n != -1:
            prev_coffee_label = self.aw.qmc.plus_coffee_label
            prev_blend_label = self.aw.qmc.plus_blend_label
            self.populatePlusCoffeeBlendCombos(n)
            self.updateTitle(prev_coffee_label, prev_blend_label)

    def checkWeightIn(self) -> None:
        enough = True
        enough_replacement = False
        weightIn = 0.0
        try:
            weightIn = float(comma2dot(self.ui.weightinedit.text()))
        except Exception: # pylint: disable=broad-except
            pass
        if self.plus_amount_selected is not None:
            try:
                # convert weight to kg
                weightUnit = self.ui.weight_unit_comboBox.currentText()
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
                weightUnit = self.ui.weight_unit_comboBox.currentText()
                if weightUnit == 'kg':
                    wc = weightIn
                else:
                    wc = convertWeight(weightIn,weight_units.index(self.ui.weight_unit_comboBox.currentText()),weight_units.index('Kg'))
                if wc <= self.plus_amount_replace_selected:
                    enough_replacement = True
            except Exception: # pylint: disable=broad-except
                pass
        darkmode = self.aw.dark_canvas_p()
        if enough: # OK
            self.ui.weightinedit.setStyleSheet(
                line_edit_style(
                    darkmode,
                    color = (LINE_EDIT_COLOR_DARK if darkmode else LINE_EDIT_COLOR_LIGHT),
                    background_color = (LINE_EDIT_BACKGROUND_COLOR_DARK if darkmode else LINE_EDIT_BACKGROUND_COLOR_LIGHT)))
        elif self.aw.dark_canvas_p(): # OK
            self.ui.weightinedit.setStyleSheet(
                line_edit_style(
                    darkmode,
                    color = (LINE_EDIT_COLOR_DARK if darkmode else LINE_EDIT_COLOR_LIGHT),
                    background_color = '#ad0427')) # dark red
        elif enough_replacement:
            self.ui.weightinedit.setStyleSheet(
                line_edit_style(
                    darkmode,
                    color = '#0A5C90',
                    background_color = (LINE_EDIT_BACKGROUND_COLOR_DARK if darkmode else LINE_EDIT_BACKGROUND_COLOR_LIGHT))) # dark blue
        else: # ok
            self.ui.weightinedit.setStyleSheet(
                line_edit_style(
                    darkmode,
                    color = '#CC0F50',
                    background_color = (LINE_EDIT_BACKGROUND_COLOR_DARK if darkmode else LINE_EDIT_BACKGROUND_COLOR_LIGHT))) # light red

    @pyqtSlot(int)
    def coffeeSelectionChanged(self, n:int) -> None:
        # check for previously selected blend label
        prev_coffee_label = self.aw.qmc.plus_coffee_label
        prev_blend_label = self.aw.qmc.plus_blend_label
        if n < 1 or self.plus_coffees is None:
            self.defaultCoffeeData()
            self.aw.qmc.plus_store = None
            self.aw.qmc.plus_store_label = None
            self.aw.qmc.plus_coffee = None
            self.aw.qmc.plus_coffee_label = None
            self.plus_amount_selected = None
            self.plus_amount_replace_selected = None
            self.updateTitle(prev_coffee_label,prev_blend_label)
        else:
            # reset blend and set new coffee
            self.ui.blend_comboBox.setCurrentIndex(0)
            selected_coffee = self.plus_coffees[n-1]
            sd = plus.stock.getCoffeeStockDict(selected_coffee)
            self.aw.qmc.plus_store = sd['location_hr_id']
            self.aw.qmc.plus_store_label = sd['location_label']
            cd = plus.stock.getCoffeeCoffeeDict(selected_coffee)
            self.aw.qmc.plus_coffee = cd.get('hr_id','')
            self.aw.qmc.plus_coffee_label = plus.stock.coffeeLabel(cd)
            self.aw.qmc.plus_blend_label = None
            self.aw.qmc.plus_blend_spec = None
            self.aw.qmc.plus_blend_spec_labels = None
            if 'amount' in plus.stock.getCoffeeStockDict(selected_coffee):
                self.plus_amount_selected = plus.stock.getCoffeeStockDict(selected_coffee)['amount']
            else:
                self.plus_amount_selected = None
            self.plus_amount_replace_selected = None
            self.fillCoffeeData(selected_coffee,prev_coffee_label,prev_blend_label)
        self.checkWeightIn()
        self.updatePlusSelectedLine()

    def getBlendDictCurrentWeight(self, blend:tuple[str, tuple[plus.stock.Blend, plus.stock.StockItem, float, dict[str, str], float, list[tuple[float, plus.stock.Blend]]]]) -> plus.stock.Blend:
        if self.ui.weightinedit.text() != '':
            weightIn = float(comma2dot(self.ui.weightinedit.text()))
        else:
            weightIn = 0.0
        weight_unit_idx = self.ui.weight_unit_comboBox.currentIndex()
        v = convertWeight(weightIn,weight_unit_idx,weight_units.index('Kg')) # v is weightIn converted to kg
        return plus.stock.getBlendBlendDict(blend,v)

    @pyqtSlot(int)
    def blendSelectionChanged(self, n:int) -> None:
        # check for previously selected blend label
        prev_coffee_label = self.aw.qmc.plus_coffee_label
        prev_blend_label = self.aw.qmc.plus_blend_label
        if n < 1 or self.plus_blends is None:
            self.defaultCoffeeData()
            self.aw.qmc.plus_store = None
            self.aw.qmc.plus_store_label = None
            self.aw.qmc.plus_blend_label = None
            self.aw.qmc.plus_blend_spec = None
            self.aw.qmc.plus_blend_spec_labels = None
            self.plus_amount_selected = None
            self.updateTitle(prev_coffee_label,prev_blend_label)
        else:
            # reset coffee and set new blend
            self.ui.beans_comboBox.setCurrentIndex(0)
            selected_blend = self.plus_blends[n-1]
            bsd:plus.stock.StockItem = plus.stock.getBlendStockDict(selected_blend)
            self.aw.qmc.plus_store = bsd['location_hr_id']
            self.aw.qmc.plus_store_label = bsd['location_label']

            bd = self.getBlendDictCurrentWeight(selected_blend)
            self.aw.qmc.plus_coffee = None
            self.aw.qmc.plus_blend_label = bd['label']
            self.aw.qmc.plus_blend_spec = cast(plus.stock.Blend, dict(bd)) # make a copy of the blend dict
# UPDATE: we keep the hr_id in to be able to adjust the blend with its replacements if needed
#            # we trim the blend_spec to the external from
#            self.aw.qmc.plus_blend_spec.pop("hr_id", None) # remove the hr_id

            self.aw.qmc.plus_blend_spec_labels = [i.get('label','') for i in self.aw.qmc.plus_blend_spec['ingredients']]
            # remove labels from ingredients
            ingredients = []
            for i in self.aw.qmc.plus_blend_spec['ingredients']:
                entry = plus.stock.BlendIngredient(ratio = i['ratio'], coffee = i['coffee'])
                if 'ratio_num' in i:
                    entry['ratio_num'] = i['ratio_num']
                if 'ratio_denom' in i:
                    entry['ratio_denom'] = i['ratio_denom']
                ingredients.append(entry)
            self.aw.qmc.plus_blend_spec['ingredients'] = ingredients
            self.plus_amount_selected = plus.stock.getBlendMaxAmount(selected_blend)
            self.plus_amount_replace_selected = plus.stock.getBlendReplaceMaxAmount(selected_blend)
            self.fillBlendData(selected_blend,prev_coffee_label,prev_blend_label)
        self.checkWeightIn()
        self.updatePlusSelectedLine()


    @pyqtSlot(bool)
    def customBlendButton_triggered(self, _:bool = False) -> None:
        inWeight = self.aw.qmc.weight[0]

        coffees = plus.stock.getCoffeeLabels()

        if len(coffees)>1:
            if self.aw.qmc.plus_custom_blend is not None and self.aw.qmc.plus_custom_blend.isValid(coffees.values()):
                blend = self.aw.qmc.plus_custom_blend
            else:
                coffee_tuples = sorted(coffees.items(), key=lambda x: x[0])
                blend = plus.blend.CustomBlend(QApplication.translate('Form Caption','Custom Blend'),[
                    plus.blend.Component(coffee_tuples[0][1], 0.5),
                    plus.blend.Component(coffee_tuples[1][1], 0.5)
                ])
            # only entries of coffees with stock in the selected store or in all stores if no store is selected) should be enabled in blend component coffee popups
            coffee_hr_ids_with_stock_in_store:set[str] = set()
            if self.plus_coffees is not None:
                coffee_hr_ids_with_stock_in_store = {plus.stock.getCoffeeId(c) for c in self.plus_coffees if
                    # if there are multiple stores defined and non is selected, only coffees with stock in all stores are enabled in the blend component coffee popups
                    self.plus_stores is None or len(self.plus_stores) < 2 or self.ui.space_comboBox.currentIndex() != 0 or len(plus.stock.getCoffeeCoffeeStocks(c)) == len(self.plus_stores)}

            total_weight:float
            res, total_weight = plus.blend.openCustomBlendDialog(self.aw, self.aw, inWeight, self.aw.qmc.weight[2],
                    coffees, blend, coffee_hr_ids_with_stock_in_store)
            if res is not None: # not canceled
                self.aw.qmc.plus_custom_blend = res
                self.populatePlusCoffeeBlendCombos() # we update the blend menu to reflect the current custom blend
                if self.aw.qmc.plus_custom_blend.name.strip() == '' and self.aw.qmc.plus_blend_spec is not None and 'hr_id' in self.aw.qmc.plus_blend_spec and self.aw.qmc.plus_blend_spec['hr_id'] == '':
                    # if the custom blend entry was selected before, which is now removed, we select the empty first entry
                    self.ui.blend_comboBox.setCurrentIndex(0)
                    self.blendSelectionChanged(0)
                # update inweight
                inw = f'{float2floatWeightVolume(total_weight):g}'
                self.ui.weightinedit.setText(inw)
                self.weightin_edited()

    def plus_popups_set_enabled(self, b:bool) -> None:
        for combo in [self.ui.beans_comboBox, self.ui.blend_comboBox, self.ui.space_comboBox]:
            try:
                combo.setEnabled(b)
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)

    def plus_popups_block_signals(self, b:bool) -> None:
        for combo in [self.ui.beans_comboBox, self.ui.blend_comboBox, self.ui.space_comboBox]:
            try:
                combo.blockSignals(b)
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)

    def blends_popup_visible(self, visible:bool) -> None:
        self.ui.blend_label.setVisible(visible)
        self.ui.blend_comboBox.setVisible(visible)
    def spaces_popup_visible(self, visible:bool) -> None:
        self.ui.space_label.setVisible(visible)
        self.ui.space_comboBox.setVisible(visible)


    def markPlusCoffeeFields(self, b:bool) -> None:
        darkmode = self.aw.dark_canvas_p()
        if b:
            if darkmode:
                self.ui.beans_textEdit.update_style(
                    darkmode,
                    background_color = '#44333333',
                    selection_background_color = 'darkgray',
                    border_color = LINE_EDIT_BORDER_COLOR_DARK,
                    color = LINE_EDIT_COLOR_DARK)
            else:
                self.ui.beans_textEdit.update_style(
                    darkmode,
                    background_color = '#e4f3f8',
                    selection_background_color = '#E2E2E2',
                    border_color = LINE_EDIT_BORDER_COLOR_LIGHT,
                    color = LINE_EDIT_COLOR_LIGHT)
        elif darkmode:
            self.ui.beans_textEdit.update_style(
                darkmode,
                background_color = LINE_EDIT_BACKGROUND_COLOR_DARK,
                border_color = LINE_EDIT_BORDER_COLOR_DARK,
                color = LINE_EDIT_COLOR_DARK)
        else:
            self.ui.beans_textEdit.update_style(
                darkmode,
                background_color = LINE_EDIT_BACKGROUND_COLOR_LIGHT,
                border_color = LINE_EDIT_BORDER_COLOR_LIGHT,
                color = LINE_EDIT_COLOR_LIGHT)

    def updateBlendLines(self, blend:plus.stock.BlendStructure) -> None:
        if self.ui.weightinedit.text() != '':
            weightIn = float(comma2dot(self.ui.weightinedit.text()))
        else:
            weightIn = 0.0
        weight_unit_idx = self.ui.weight_unit_comboBox.currentIndex()
        blend_lines = plus.stock.blend2beans(blend,weight_unit_idx,weightIn)
        self.ui.beans_textEdit.clear()
        for ll in blend_lines:
            self.ui.beans_textEdit.appendPlainText(ll)

    def fillBlendData(self, blend:plus.stock.BlendStructure, prev_coffee_label:str|None, prev_blend_label:str|None) -> None:
        try:
            self.updateBlendLines(blend)
            blend_dict = self.getBlendDictCurrentWeight(blend)
            # moisture
            self.aw.qmc.moisture_greens = blend_dict.get('moisture', 0)
            # density
            self.aw.qmc.density = ((blend_dict['density'], 'g', 1, 'l') if 'density' in blend_dict else (0, 'g', 1, 'l'))
            # screen size
            if 'screen_min' in blend_dict:
                self.aw.qmc.beansize_min = blend_dict['screen_min']
            if 'screen_max' in blend_dict:
                self.aw.qmc.beansize_max = blend_dict['screen_max']
            # check if title should be changed (if still default, or equal to the previous selection:
            self.updateTitle(prev_coffee_label,prev_blend_label)
            self.markPlusCoffeeFields(True)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

    def fillCoffeeData(self, coffee:tuple[str, tuple[plus.stock.Coffee, plus.stock.StockItem]],
            prev_coffee_label:str|None, prev_blend_label:str|None) -> None:
        try:
            if not self.aw.qmc.safesaveflag:
                # update defaults
                self.beans_default = self.aw.qmc.beans
                self.density_default = self.aw.qmc.density[0]
                self.moisture_default = self.aw.qmc.moisture_greens
                self.screen_min_default = self.aw.qmc.beansize_min
                self.screen_max_default = self.aw.qmc.beansize_max

            cd = plus.stock.getCoffeeCoffeeDict(coffee)
            # beans description (only attribute which has a widget)
            self.aw.qmc.beans = plus.stock.coffee2beans(cd)
            self.ui.beans_textEdit.setPlainText(self.aw.qmc.beans)
            # moisture
            self.aw.qmc.moisture_greens = cd.get('moisture', 0)
            # density
            self.aw.qmc.density = ((cd['density'], 'g', 1, 'l') if 'density' in cd else (0, 'g', 1, 'l'))
            # screen size
            if 'screen_size' in cd:
                screen = cd['screen_size']
                self.aw.qmc.beansize_min = screen.get('min', 0)
                self.aw.qmc.beansize_max = screen.get('max', 0)
            else:
                self.aw.qmc.beansize_min = 0
                self.aw.qmc.beansize_max = 0
            #
            self.updateTitle(prev_coffee_label,prev_blend_label)
            self.markPlusCoffeeFields(True)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

    def defaultCoffeeData(self) -> None:
        # beans description (only attribute which has a widget)
        self.aw.qmc.beans = self.beans_default
        self.ui.beans_textEdit.setPlainText(self.aw.qmc.beans)
        self.aw.qmc.moisture_greens = self.moisture_default
        self.aw.qmc.density = (self.density_default, 'g', 1, 'l')
        self.aw.qmc.beansize_min = self.screen_min_default
        self.aw.qmc.beansize_max = self.screen_max_default
        #
        self.markPlusCoffeeFields(False)


    # storeIndex is the index of the selected store entry in the popup
    @pyqtSlot()
    @pyqtSlot(int)
    def populatePlusCoffeeBlendCombos(self, storeIndex:int|None = None) -> None:
        if self.aw.plus_account is not None:
            try: # this can crash if dialog got closed while this is processed in a different thread!
                self.plus_popups_set_enabled(False)

                #---- Stores

                if storeIndex is None or storeIndex == -1:
                    self.plus_stores = plus.stock.getStores()
                    try:
                        if len(self.plus_stores) == 1:
                            self.aw.qmc.plus_default_store = plus.stock.getStoreId(self.plus_stores[0])
                        self.spaces_popup_visible(len(self.plus_stores) > 1)
                    except Exception as e:  # pylint: disable=broad-except
                        _log.exception(e)
                    self.ui.space_comboBox.blockSignals(True)
                    self.ui.space_comboBox.clear()
                    store_items = plus.stock.getStoreLabels(self.plus_stores)
                    self.ui.space_comboBox.addItems([''] + store_items)
                    adjust_combobox_dropdown_width(self.ui.space_comboBox)
                    p = (plus.stock.getStorePosition(self.aw.qmc.plus_default_store,self.plus_stores) if self.aw.qmc.plus_default_store is not None else None)
                    if p is None:
                        self.ui.space_comboBox.setCurrentIndex(0)
                    else:
                        # we set to the default_store if available
                        self.ui.space_comboBox.setCurrentIndex(p+1)
                    self.ui.space_comboBox.blockSignals(False)

                storeIdx = self.ui.space_comboBox.currentIndex()

                # we reset the store if a coffee or blend is selected and the selected store is not equal to the default store
                # we clean the coffee/blend selection as it does not fit
                if storeIdx > 0 and self.plus_stores is not None and len(self.plus_stores)>storeIdx-1:
                    selected_store = self.plus_stores[storeIdx-1]
                    selected_store_id = plus.stock.getStoreId(selected_store)
                    if (self.aw.qmc.plus_coffee or self.aw.qmc.plus_blend_spec) and self.aw.qmc.plus_store != selected_store_id:
                        self.defaultCoffeeData()
                        self.plus_amount_selected = None
                        self.aw.qmc.plus_store_label = None
                        # we keep the plus_coffee_selected/label or plus_blend_selected_spec/labels to store and display them
                    self.aw.qmc.plus_default_store = selected_store_id
                else:
                    self.aw.qmc.plus_default_store = None

                mark_coffee_fields = False


                #---- Coffees

                self.plus_coffees = plus.stock.getCoffees(self.ui.weight_unit_comboBox.currentIndex(),self.aw.qmc.plus_default_store)
                self.ui.beans_comboBox.blockSignals(True)
                nr_previous_coffees = self.ui.beans_comboBox.count()
                self.ui.beans_comboBox.clear()
                self.ui.beans_comboBox.resetInverted() # not unit inversion yet implemented for dashboard
                coffee_items = plus.stock.getCoffeesLabels(self.plus_coffees)
                self.ui.beans_comboBox.addItems([''] + coffee_items)
                adjust_combobox_dropdown_width(self.ui.beans_comboBox)

                p = None
                if self.aw.qmc.plus_coffee is not None and self.aw.qmc.plus_store is not None:
                    p = plus.stock.getCoffeeStockPosition(self.aw.qmc.plus_coffee,self.aw.qmc.plus_store,self.plus_coffees)
                if p is None:
                    # not in the current stock
                    self.ui.beans_comboBox.setCurrentIndex(0)
                    #self.aw.qmc.plus_coffee = None # we don't "deselect" a coffee just because it is not in the popup!
                    self.ui.beans_comboBox.blockSignals(False)
                else:
                    # if roast is complete (charge and drop are set)
                    if nr_previous_coffees == 0 or (self.aw.qmc.timeindex[0] > -1 and self.aw.qmc.timeindex[6] > 0):
                        # we first change the index and then unblock signals to avoid properties being overwritten from the selected coffee
                        self.ui.beans_comboBox.setCurrentIndex(p+1)
                        self.ui.beans_comboBox.blockSignals(False)
                    else:
                        # if roast is not yet complete we unblock the signals before changing the index to get the coffee data be filled in
                        self.ui.beans_comboBox.blockSignals(False)
                        self.ui.beans_comboBox.setCurrentIndex(p+1)
                    mark_coffee_fields = True


                #---- Blends

                custom_blend:plus.stock.Blend|None = None
                # if a valid custom_blend with a non-empty name exists, we add it to the blend popups
                coffees = plus.stock.getCoffeeLabels()
                self.ui.custom_blend.setEnabled(len(coffees)>1) # there need at least to be two different coffes with stock in some warehouse
                if (self.aw.qmc.plus_custom_blend is not None and self.aw.qmc.plus_custom_blend.name.strip() != '' and
                        len(coffees)>1 and self.aw.qmc.plus_custom_blend.isValid(coffees.values())):
                    custom_blend = plus.stock.Blend(
                        hr_id = '',
                        label = self.aw.qmc.plus_custom_blend.name.strip(),
                        ingredients = [plus.stock.BlendIngredient(ratio = c.ratio, coffee = c.coffee) for c in self.aw.qmc.plus_custom_blend.components])
                self.plus_blends = plus.stock.getBlends(self.ui.weight_unit_comboBox.currentIndex(),self.aw.qmc.plus_default_store, custom_blend)
                self.ui.blend_comboBox.blockSignals(True)
                nr_previous_blends = self.ui.blend_comboBox.count()
                self.ui.blend_comboBox.clear()
                self.ui.blend_comboBox.resetInverted()
                blend_items = plus.stock.getBlendLabels(self.plus_blends)

                self.ui.blend_comboBox.addItems([''] + blend_items)
                adjust_combobox_dropdown_width(self.ui.blend_comboBox)

                self.blends_popup_visible(len(self.plus_blends) != 0)

                p = None
                if self.aw.qmc.plus_blend_spec is not None and self.aw.qmc.plus_store is not None:
                    p = plus.stock.getBlendSpecStockPosition(self.aw.qmc.plus_blend_spec, self.aw.qmc.plus_store, self.plus_blends)
                if p is None:
                    self.ui.blend_comboBox.setCurrentIndex(0)
                    #self.aw.qmc.plus_blend_spec = None # we don't deselect a blend just because it is not in the popup
                    self.ui.blend_comboBox.blockSignals(False)
                else:
                    # if roast is complete (charge and drop are set)
                    if nr_previous_blends == 0 or (self.aw.qmc.timeindex[0] > -1 and self.aw.qmc.timeindex[6] > 0):
                        # we first change the index and then unblock signals to avoid properties being overwritten from the selected blend
                        self.ui.blend_comboBox.setCurrentIndex(p+1)
                        self.ui.blend_comboBox.blockSignals(False)
                    else:
                        # if roast is not yet complete we unblock the signals before changing the index to get the blend data be filled in
                        self.ui.blend_comboBox.blockSignals(False)
                        self.ui.blend_comboBox.setCurrentIndex(p+1)
                    mark_coffee_fields = True

                self.markPlusCoffeeFields(mark_coffee_fields)
                self.updatePlusSelectedLine()

            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
            finally:
                self.plus_popups_set_enabled(True)
                self.plus_popups_block_signals(False)

################

    def clearPushButtonSetEnabled(self) -> None:
        self.ui.clear_pushButton.setEnabled(True)
        self.ui.clear_pushButton.setIcon(QIcon(getStyleIconPath('cancel-01-stroke-rounded-white.svg')))

    def clearPushButtonSetDisabled(self) -> None:
        darkmode = self.aw.dark_canvas_p()
        self.ui.clear_pushButton.setEnabled(False)
        self.ui.clear_pushButton.setIcon(QIcon(getStyleIconPath('cancel-01-stroke-rounded-white.svg' if darkmode else 'cancel-01-stroke-rounded.svg')))


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
            self.update_template_link_toolbutton()
        finally:
            self.ui.recentFiles_comboBox.blockSignals(False)


    def update_recent_roast_buttons(self) -> None:
        if self.aw.qmc.title not in {'', QApplication.translate('Scope Title', 'Roaster Scope')} and self.aw.qmc.weight[0] != 0:
            # enable "+" addRecentRoast and '-' removeRecentRoast button
            self.ui.plus_button.setEnabled(True)
            self.ui.plus_button.setIcon(QIcon(getStyleIconPath('add-01-stroke-rounded-white.svg')))
            self.ui.minus_button.setEnabled(True)
            self.ui.minus_button.setIcon(QIcon(getStyleIconPath('remove-01-stroke-rounded-white.svg')))
        else:
            self.ui.plus_button.setEnabled(False)
            darkmode = self.aw.dark_canvas_p()
            self.ui.plus_button.setIcon(QIcon(getStyleIconPath('add-01-stroke-rounded-white.svg' if darkmode else 'add-01-stroke-rounded.svg')))
            self.ui.minus_button.setEnabled(False)
            self.ui.minus_button.setIcon(QIcon(getStyleIconPath('remove-01-stroke-rounded-white.svg' if darkmode else 'remove-01-stroke-rounded.svg')))

    def update_compare_create_buttons(self) -> None:
        self.ui.compare_pushButton.setVisible(not self.aw.inProductionMode())
        self.ui.compare_pushButton.setEnabled(self.aw.curFile is not None)
        darkmode = self.aw.dark_canvas_p()
        self.ui.compare_pushButton.setIcon(QIcon(getStyleIconPath(
            ('git-compare-arrows-stroke-rounded-white.svg' if darkmode else 'git-compare-arrows-stroke-rounded.svg') if
                self.aw.curFile is None else 'git-compare-arrows-stroke-rounded-white.svg')))
        #
        self.ui.create_pushButton.setVisible(not self.aw.inProductionMode())
        self.ui.create_pushButton.setEnabled(not self.aw.qmc.flagon)
        self.ui.create_pushButton.setIcon(QIcon(getStyleIconPath(
            ('add-01-stroke-rounded-white.svg' if darkmode else 'add-01-stroke-rounded.svg') if self.aw.qmc.flagon else 'add-01-stroke-rounded-white.svg')))

    # slots

    @pyqtSlot(bool)
    def login_clicked(self, b:bool) -> None:
        del b
        # we clear all combos to ensure that on populating them beans data is not overwritten (see populatePlusCoffeeBlendCombos())
        self.ui.beans_comboBox.clear()
        self.ui.blend_comboBox.clear()
        self.ui.space_comboBox.clear()
        #
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
                self.aw.loadAndRedrawBackgroundUUIDSignal.emit(rr['background'],background_UUID)
            self.ui.title_comboBox.textEdited(rr['title']) # internal use in widget
#            self.ui.title_comboBox.setEditText(rr['title']) # seems not to be needed


            # we now set the actual values from the stock
            self.populatePlusCoffeeBlendCombos()
            if self.aw.qmc.plus_blend_spec is not None and self.plus_blends is not None and 'hr_id' in self.aw.qmc.plus_blend_spec:
                # try to apply blend replacement (blend recipe might have been updated on the server since this recent roast blend entry was established
                # search for the position of blend/location hr_id combo in self.plus_blends and call blendSelectionChanged with pos+1
                try:
                    pos_in_blends = next(i for i, b in enumerate(self.plus_blends) if \
                        plus.stock.getBlendId(b) == self.aw.qmc.plus_blend_spec['hr_id'] and
                        plus.stock.getBlendStockDict(b)['location_hr_id'] == self.aw.qmc.plus_store)
                    self.blendSelectionChanged(pos_in_blends+1)
                except Exception:  # pylint: disable=broad-except
                    self.updatePlusSelectedLine()
            else:
                # blend replacements not applied
                self.updatePlusSelectedLine()


    @pyqtSlot(str)
    def recent_roast_enabled(self, s:str) -> None:
        self.aw.qmc.title = s
        self.aw.qmc.fileDirtySignal.emit()
        self.title_changed_timer.start(self.TITLE_CHANGE_ESTABLISH_PERIOD)

    @pyqtSlot()
    def title_changed(self) -> None:
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
        if not self.aw.qmc.safesaveflag:
            self.beans_default = self.aw.qmc.beans
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
                self.ui.weightinedit.setText(f'{float2floatWeightVolume(self.aw.qmc.weight[0]):g}')
            if self.aw.qmc.weight[0] != 0 and self.aw.qmc.density[0] != 0:
                weight_in_g = convertWeight(self.aw.qmc.weight[0],weight_units.index(self.aw.qmc.weight[2]),weight_units.index('g'))
                volume_in = weight_in_g / self.aw.qmc.density[0] # in g/l
                # convert to selected volume unit
                volume_in = convertVolume(volume_in,volume_units.index('l'),volume_units.index(self.aw.qmc.volume[2]))
                self.aw.qmc.volume = (volume_in, self.aw.qmc.volume[1], self.aw.qmc.volume[2])
            if self.aw.plus_account is not None:
                blend_idx = self.ui.blend_comboBox.currentIndex()
                if blend_idx > 0:
                    self.blendSelectionChanged(blend_idx)
                coffee_idx = self.ui.beans_comboBox.currentIndex()
                if coffee_idx > 0:
                    self.coffeeSelectionChanged(coffee_idx)
            self.update_recent_roast_buttons()
            self.aw.qmc.fileDirtySignal.emit()

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
        self.weightin_edited()

    @pyqtSlot(int)
    def recent_files_index_changed(self, i:int) -> None:
        if i > 0 and i-1 < len(self.recent_files):
            self.aw.loadBackgroundSignal.emit(self.recent_files[i-1], False, True) # we load background explicitly (not as part of a foreground profiles) thus we force_show
            QTimer.singleShot(500, self.update_profile_section)

    @pyqtSlot(bool)
    def profile_load_clicked(self, b:bool) -> None:
        del b
        path:str|None = None
        if self.aw.qmc.backgroundprofile is not None and self.aw.qmc.backgroundpath:
            # if a background profile is loaded we open the file selector using its path
            path = self.aw.qmc.backgroundpath
        filename = self.aw.ArtisanOpenFileDialog(msg=QApplication.translate('Message','Load roast template'),path =path, ext='*.alog')
        if len(filename) != 0:
            self.aw.loadBackgroundSignal.emit(filename, False, True) # we load background explicitly (not as part of a foreground profiles) thus we force_show

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
    def open_roast_on_platform(self, _b:bool) -> None:
        if self.aw.qmc.roastUUID:
            QDesktopServices.openUrl(QUrl(roastLink(self.aw.qmc.roastUUID), QUrl.ParsingMode.TolerantMode))

    @pyqtSlot(bool)
    def open_template_on_platform(self, _b:bool) -> None:
        template_uuid:str|None = (self.aw.qmc.backgroundprofile['roastUUID'] if self.aw.qmc.backgroundprofile is not None and
            'roastUUID' in self.aw.qmc.backgroundprofile else None)
        if template_uuid:
            QDesktopServices.openUrl(QUrl(roastLink(template_uuid), QUrl.ParsingMode.TolerantMode))

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
