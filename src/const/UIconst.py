# -*- coding: cp1252 -*-
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

from PyQt5.QtWidgets import QApplication # @Reimport

import platform

import sys
if sys.version < '3':
    import codecs
    def u(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    def u(x):
        return x
        
platf = str(platform.system())


#######################################################################################
#################### MENU STRINGS  ####################################################
#######################################################################################

#Fake entries to get translations for the Mac Application Menu
_mac_services = QApplication.translate("MAC_APPLICATION_MENU", "Services", None)
_mac_hide = QApplication.translate("MAC_APPLICATION_MENU", "Hide {0}", None)
_mac_hideothers = QApplication.translate("MAC_APPLICATION_MENU", "Hide Others", None)
_mac_showall = QApplication.translate("MAC_APPLICATION_MENU", "Show All", None)
_mac_preferences = QApplication.translate("MAC_APPLICATION_MENU", "Preferences...", None)
_mac_quit = QApplication.translate("MAC_APPLICATION_MENU", "Quit {0}", None)
_mac_about = QApplication.translate("MAC_APPLICATION_MENU", "About {0}", None)

#File menu items
FILE_MENU = QApplication.translate("Menu", "File", None)
if platf != 'Darwin':
    FILE_MENU = "&" + FILE_MENU # the & adds a short cut automatically
FILE_MENU_NEW = QApplication.translate("Menu", "New", None)
FILE_MENU_OPEN = QApplication.translate("Menu", "Open...", None)
FILE_MENU_OPENRECENT = QApplication.translate("Menu", "Open Recent", None)
FILE_MENU_IMPORT = QApplication.translate("Menu", "Import", None)
FILE_MENU_SAVE = QApplication.translate("Menu", "Save", None)
FILE_MENU_SAVEAS = QApplication.translate("Menu", "Save As...", None)
FILE_MENU_SAVECOPYAS = QApplication.translate("Menu", "Save a Copy As...", None)
FILE_MENU_EXPORT = QApplication.translate("Menu", "Export", None)
FILE_MENU_CONVERT = QApplication.translate("Menu", "Convert To", None)
FILE_MENU_SAVEGRAPH = QApplication.translate("Menu", "Save Graph", None)
FILE_MENU_SAVEGRAPH_FULL_SIZE = QApplication.translate("Menu", "Full Size...", None)
FILE_MENU_SAVEGRAPH_Large = QApplication.translate("Menu", "Large (1200x?)...", None)
FILE_MENU_REPORT = QApplication.translate("Menu", "Report", None)
FILE_MENU_HTMLREPORT = QApplication.translate("Menu", "Roast", None)
FILE_MENU_PRODUCTIONREPORT = QApplication.translate("Menu", "Batches", None)
FILE_MENU_RANKINGREPORT = QApplication.translate("Menu", "Ranking", None)
FILE_MENU_REPORT_WEB = QApplication.translate("Menu", "Web...", None)
FILE_MENU_REPORT_CSV = QApplication.translate("Menu", "CSV...", None)
FILE_MENU_REPORT_EXCEL = QApplication.translate("Menu", "Excel...", None)
FILE_MENU_PRINT = QApplication.translate("Menu", "Print...", None)
if platf == 'Darwin':
    FILE_MENU_QUIT = "Quit"
    #FILE_MENU_QUIT = QApplication.translate("MAC_APPLICATION_MENU", "Quit {0}", None).format("Artisan")  
else: 
    FILE_MENU_QUIT = "Quit"
    #FILE_MENU_QUIT = "&" + QApplication.translate("Menu", "Quit", None)

#Edit menu items
EDIT_MENU = QApplication.translate("Menu", "Edit", None)
if platf != 'Darwin':
    EDIT_MENU = "&" + EDIT_MENU
EDIT_MENU_CUT = QApplication.translate("Menu", "Cut", None)
EDIT_MENU_COPY = QApplication.translate("Menu", "Copy", None)
EDIT_MENU_PASTE = QApplication.translate("Menu", "Paste", None)
    
#Roast menu items
ROAST_MENU = QApplication.translate("Menu", "Roast", None)
if platf != 'Darwin':
    ROAST_MENU = "&" + ROAST_MENU
ROAST_MENU_PROPERTIES = QApplication.translate("Menu", "Properties...", None)
ROAST_MENU_BACKGROUND = QApplication.translate("Menu", "Background...", None)
ROAST_MENU_CUPPROFILE = QApplication.translate("Menu", "Cup Profile...", None)
ROAST_MENU_CONVERT_TO_FAHRENHEIT = QApplication.translate("Menu", "Convert to Fahrenheit", None)
ROAST_MENU_CONVERT_TO_CELSIUS = QApplication.translate("Menu", "Convert to Celsius", None)
ROAST_MENU_FAHRENHEIT_MODE = QApplication.translate("Menu", "Fahrenheit Mode", None)
ROAST_MENU_CELSIUS_MODE = QApplication.translate("Menu", "Celsius Mode", None)
ROAST_MENU_SWITCH = QApplication.translate("Menu", "Switch Profiles", None)
ROAST_MENU_SWITCH_ETBT = QApplication.translate("Menu", "Switch ET<->BT", None)

#Conf menu items
CONF_MENU = QApplication.translate("Menu", "Config", None)
if platf != 'Darwin':
    CONF_MENU = "&" + CONF_MENU
CONF_MENU_MACHINE = QApplication.translate("Menu", "Machine", None)
CONF_MENU_THEMES = QApplication.translate("Menu", "Themes", None)
CONF_MENU_DEVICE = QApplication.translate("Menu", "Device...", None)
CONF_MENU_SERIALPORT = QApplication.translate("Menu", "Port...", None)
CONF_MENU_SAMPLING = QApplication.translate("Menu", "Sampling Interval...", None)
CONF_MENU_OVERSAMPLING = QApplication.translate("Menu", "Oversampling", None)
CONF_MENU_OVERSAMPLING = QApplication.translate("Menu", "Oversampling", None)
CONF_MENU_COLORS = QApplication.translate("Menu", "Colors...", None)
CONF_MENU_CONTROLS = QApplication.translate("Menu", "Controls", None)
CONF_MENU_READINGS = QApplication.translate("Menu", "Readings", None)
CONF_MENU_BUTTONS = QApplication.translate("Menu", "Buttons", None)
CONF_MENU_SLIDERS = QApplication.translate("Menu", "Sliders", None)
CONF_MENU_PHASES = QApplication.translate("Menu", "Phases...", None)
CONF_MENU_EVENTS = QApplication.translate("Menu", "Events...", None)
CONF_MENU_CURVES = QApplication.translate("Menu", "Curves...", None)
CONF_MENU_STATISTICS = QApplication.translate("Menu", "Statistics...", None)
CONF_MENU_AXES = QApplication.translate("Menu", "Axes...", None)
CONF_MENU_AUTOSAVE = QApplication.translate("Menu", "Autosave...", None)
CONF_MENU_BATCH = QApplication.translate("Menu", "Batch...", None)
CONF_MENU_ALARMS = QApplication.translate("Menu", "Alarms...", None)
CONF_MENU_TEMPERATURE = QApplication.translate("Menu", "Temperature", None)
CONF_MENU_LANGUAGE = QApplication.translate("Menu", "Language", None)

#Languages
CONF_MENU_ARABIC = u("\u0627\u0644\u0639\u0631\u0628\u064a\u0629") # Do not translate
CONF_MENU_GERMAN = u("Deutsch")  # Do not translate
CONF_MENU_GREEK = u("\u03b5\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac") # Do not translate
CONF_MENU_ENGLISH = u("English") # Do not translate
CONF_MENU_SPANISH = u("Espa\u00f1ol") # Do not translate
CONF_MENU_FARSI = u("\u0641\u0627\u0631\u0633\u06cc") # Do not translate
CONF_MENU_FINISH = u("Suomalainen") # Do not translate
CONF_MENU_FRENCH = u("Fran\u00e7ais") # Do not translate
CONF_MENU_HEBREW = u("\u05e2\u05d1\u05e8\u05d9\u05ea") # Do not translate
CONF_MENU_HUNGARIAN = u("Hungarian") # Do not translate
CONF_MENU_INDONESIAN = u("Indonesia") # Do not translate
CONF_MENU_ITALIAN = u("Italiano") # Do not translate
CONF_MENU_JAPANESE = u("\u65e5\u672c\u8a9e") # Do not translate
CONF_MENU_KOREAN = u("\ud55c\uad6d\uc758") # Do not translate
CONF_MENU_DUTCH = u("Nederlands") # Do not translate
CONF_MENU_NORWEGIAN = u("Norsk") # Do not translate
CONF_MENU_PORTUGUESE = u("Portugu\xeas") # Do not translate
CONF_MENU_BRASIL = u("Portugu\u00EAs do Brasil") # Do not translate
CONF_MENU_POLISH = u("Polski") # Do not translate
CONF_MENU_RUSSIAN = u("\u0440\u0443\u0441\u0441\u043a\u0438\u0439") # Do not translate
CONF_MENU_SWEDISH = u("Svenska") # Do not translate
CONF_MENU_THAI = u("Thai") # Do not translate
CONF_MENU_TURKISH = u("T\xfcrk\u00e7e") # Do not translate
CONF_MENU_CHINESE_CN = u("\u7b80\u4f53\u4e2d\u6587") # Do not translate
CONF_MENU_CHINESE_TW = u("\u7e41\u9ad4\u4e2d\u6587") # Do not translate

#Toolkit menu
TOOLKIT_MENU = QApplication.translate("Menu", "Tools", None)
if platf != 'Darwin':
    TOOLKIT_MENU = "&" + TOOLKIT_MENU
TOOLKIT_MENU_DESIGNER = QApplication.translate("Menu", "Designer", None)    
TOOLKIT_MENU_CALCULATOR = QApplication.translate("Menu", "Calculator", None)
TOOLKIT_MENU_WHEELGRAPH = QApplication.translate("Menu", "Wheel Graph", None)
TOOLKIT_MENU_LCDS = QApplication.translate("Menu", "LCDs", None)


#Settings menu
SETTINGS_MENU_LOAD = QApplication.translate("Menu", "Load Settings...", None)    
SETTINGS_MENU_LOADRECENT = QApplication.translate("Menu", "Load Recent Settings", None)
SETTINGS_MENU_SAVEAS = QApplication.translate("Menu", "Save Settings...", None)
SETTINGS_MENU_SAVETHEME = QApplication.translate("Menu", "Save Theme...", None)


#View menu items
VIEW_MENU = QApplication.translate("Menu", "View", None)
if platf != 'Darwin':
    VIEW_MENU = "&" + VIEW_MENU
VIEW_MENU_FULLSCREEN = QApplication.translate("Menu", "Full Screen", None) # "Enter Full Screen"

#Help menu items
HELP_MENU = QApplication.translate("Menu", "Help", None)
if platf != 'Darwin':
    HELP_MENU = "&" + HELP_MENU
##note that the "About" menu item is recognized only if it is named "About" on the Mac, but automatically translated by the Qt standard tranlators
HELP_MENU_ABOUT = QApplication.translate("MAC_APPLICATION_MENU", "About {0}", None).format("Artisan") 
HELP_MENU_ABOUT_ARTISANVIEWER = QApplication.translate("MAC_APPLICATION_MENU", "About {0}", None).format("ArtisanViewer") 
HELP_MENU_ABOUTQT = QApplication.translate("Menu", "About Qt", None)
HELP_MENU_DOCUMENTATION = QApplication.translate("Menu", "Documentation", None)
#HELP_MENU_BLOG = QApplication.translate("Menu", "Blog", None)
HELP_MENU_KEYBOARDSHORTCUTS = QApplication.translate("Menu", "Keyboard Shortcuts", None)
HELP_MENU_ERRORS = QApplication.translate("Menu", "Errors", None)
HELP_MENU_MESSAGES = QApplication.translate("Menu", "Messages", None)
HELP_MENU_SERIAL = QApplication.translate("Menu", "Serial", None)
if platf == 'Darwin':
    HELP_MENU_SETTINGS = "Settings"
else:
    HELP_MENU_SETTINGS = QApplication.translate("Menu", "Settings", None)
HELP_MENU_PLATFORM = QApplication.translate("Menu", "Platform", None)
HELP_MENU_RESET = QApplication.translate("Menu", "Factory Reset", None)
  
#######################################################################################
#################### DIALOG STRINGS  ##################################################
#######################################################################################
