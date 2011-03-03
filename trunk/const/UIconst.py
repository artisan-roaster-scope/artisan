# UI related constants for the Artisan application.
#
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
# This file is part of Artisan.

from PyQt4.QtGui import QApplication
import platform

platf = unicode(platform.system())

#######################################################################################
#################### MENU STRINGS  ####################################################
#######################################################################################

#File menu items
FILE_MENU = QApplication.translate("Menu", "File", None, QApplication.UnicodeUTF8)
if platf != u'Darwin':
    FILE_MENU = "&" + FILE_MENU
FILE_MENU_NEW = QApplication.translate("Menu", "New", None, QApplication.UnicodeUTF8)
FILE_MENU_OPEN = QApplication.translate("Menu", "Open...", None, QApplication.UnicodeUTF8)
FILE_MENU_OPENRECENT = QApplication.translate("Menu", "Open Recent", None, QApplication.UnicodeUTF8)
FILE_MENU_IMPORT = QApplication.translate("Menu", "Import", None, QApplication.UnicodeUTF8)
FILE_MENU_SAVE = QApplication.translate("Menu", "Save", None, QApplication.UnicodeUTF8)
FILE_MENU_SAVEAS = QApplication.translate("Menu", "Save As...", None, QApplication.UnicodeUTF8)
FILE_MENU_EXPORT = QApplication.translate("Menu", "Export...", None, QApplication.UnicodeUTF8)
FILE_MENU_SAVEGRAPH = QApplication.translate("Menu", "Save Graph", None, QApplication.UnicodeUTF8)
FILE_MENU_HTMLREPORT = QApplication.translate("Menu", "HTML Report", None, QApplication.UnicodeUTF8)
FILE_MENU_PRINT = QApplication.translate("Menu", "Print...", None, QApplication.UnicodeUTF8)

#Roast menu items
ROAST_MENU = QApplication.translate("Menu", "Roast", None, QApplication.UnicodeUTF8)
if platf != u'Darwin':
    ROAST_MENU = "&" + ROAST_MENU
ROAST_MENU_PROPERTIES = QApplication.translate("Menu", "Properties...", None, QApplication.UnicodeUTF8)
ROAST_MENU_BACKGROUND = QApplication.translate("Menu", "Background...", None, QApplication.UnicodeUTF8)
ROAST_MENU_CUPPROFILE = QApplication.translate("Menu", "Cup Profile...", None, QApplication.UnicodeUTF8)
ROAST_MENU_TEMPERATURE = QApplication.translate("Menu", "Temperature", None, QApplication.UnicodeUTF8)
ROAST_MENU_CALCULATOR = QApplication.translate("Menu", "Calculator", None, QApplication.UnicodeUTF8)

#Conf menu items
CONF_MENU = QApplication.translate("Menu", "Config", None, QApplication.UnicodeUTF8)
if platf != u'Darwin':
    CONF_MENU = "&" + CONF_MENU
CONF_MENU_DEVICE = QApplication.translate("Menu", "Device...", None, QApplication.UnicodeUTF8)
CONF_MENU_SERIALPORT = QApplication.translate("Menu", "Serial Port...", None, QApplication.UnicodeUTF8)
CONF_MENU_SAMPLING = QApplication.translate("Menu", "Sampling Interval...", None, QApplication.UnicodeUTF8)
CONF_MENU_COLORS = QApplication.translate("Menu", "Colors...", None, QApplication.UnicodeUTF8)
CONF_MENU_PHASES = QApplication.translate("Menu", "Phases...", None, QApplication.UnicodeUTF8)
CONF_MENU_EVENTS = QApplication.translate("Menu", "Events...", None, QApplication.UnicodeUTF8)
CONF_MENU_STATISTICS = QApplication.translate("Menu", "Statistics...", None, QApplication.UnicodeUTF8)
CONF_MENU_AXES = QApplication.translate("Menu", "Axes...", None, QApplication.UnicodeUTF8)
CONF_MENU_AUTOSAVE = QApplication.translate("Menu", "Autosave...", None, QApplication.UnicodeUTF8)
CONF_MENU_EXTRAS = QApplication.translate("Menu", "Extras...", None, QApplication.UnicodeUTF8)

#Help menu items
HELP_MENU = QApplication.translate("Menu", "Help", None, QApplication.UnicodeUTF8)
if platf != u'Darwin':
    HELP_MENU = "&" + HELP_MENU
#note that the "About" menu item is recognized only if it is named "About", but automatically translated by the Qt standard tranlators
HELP_MENU_ABOUT = "About" #QApplication.translate("Menu", "About", None, QApplication.UnicodeUTF8)
HELP_MENU_DOCUMENTATION = QApplication.translate("Menu", "Documentation", None, QApplication.UnicodeUTF8)
HELP_MENU_KEYBOARDSHORTCUTS = QApplication.translate("Menu", "Keyboard Shortcuts", None, QApplication.UnicodeUTF8)
HELP_MENU_ERRORS = QApplication.translate("Menu", "Errors", None, QApplication.UnicodeUTF8)


    
#######################################################################################
#################### DIALOG STRINGS  ##################################################
#######################################################################################
