readme.txt

Artisan helps coffee roasters record, analyze, and control roast profiles. With the help of a thermocouple data logger, or a proportional–integral–derivative controller (PID controller), this software offers roasting metrics to help make decisions that influence the final coffee flavor.


HOME

The project home is on Google Code were all source and binary files are available as well as an issue tracker.

<http://code.google.com/p/artisan/>


MAILING LISTS

Users: <https://lists.mokelbu.de/listinfo/artisan-user>
Developers: <https://lists.mokelbu.de/listinfo/artisan-devel>


FEATURES

o runs on Mac OS X 10.4/10.5/10.6, PPC, Windows, and Linux
o ET/BT logging and PID control supporting the following devices
 - Fuji PXR/PXG 4 & 5 PID
 - Omega HH309, HH506RA, HH802U, HH806AU, HHM28
 - CENTER 300, 301, 302, 303, 304, 305, 306, 309
 - VOLTCRAFT K202, K204, 300K, 302KJ
 - EXTECH 421509
 - Arduino/TC4
 - TE VA18B
 - HHM28 multimeter
 - virtual devices (symbolic devices)
 - device None (no device)
o unlimited number of devices/curves running at the same time
o symbolic manipulation of device outputs
o Fahrenheit and Celsius display and conversion
o manual logging of extra events (FCs,FCe,..)
o custom event buttons
o large buttons supporting touch panels
o live ET/BT rate-of-rise curves
o metric and thermal head-up-display predicting the ET/BT future during logging
o profile statistics and evaluations based on user configurable roast phases
o background reference profile
o user defined cup profiles and cup profile graphs
o HTML report creation
o CSV export
o Omega HH506 and K202 CSV import
o PID duty cycle
o profile designer
o wheel graph editor
o mathematical plotter
o localizations (partial translations for German, French, Spanish, Swedish, Italian)
o multi-core CPU performance enhancement support


INSTALLATION

o Windows

Artisan for Windows needs a Visual C++ runtime library (file) from Microsoft. If artisan cannot start it will open a window error. This is because your computer is missing this file. If you get a window error when you try to start artisan, install this program:

Microsoft Visual C++ 2008 SP1 Redistributable Package (x86)

http://www.microsoft.com/downloads/en/details.aspx?familyid=A5C84275-3B97-4AB7-A40D-3802B2AF5FC2&displaylang=en

If artisan starts when clicling on artisan.exe (a window pops open with many buttons), then your computer already have this file and you don't need to install anything. Newer OS like Windows 7 come with this file.


o Mac OS X (10.4.x/10.5.x/10.6x on PPC/Intel)

- Install USB/serial driver for your meter
 . for Omega meters download and run the FTDI VCP OS X installer
   http://www.ftdichip.com/Drivers/VCP.htm
 . for Voltkraft meters using the original Voltkraft USB cable it is the CP210x driver from Silicon Labs
   http://www.silabs.com/products/mcu/Pages/USBtoUARTBridgeVCPDrivers.aspx
- Download and run the Artisan OS X installer
- Double click on the dmg file you just downloaded
- Double click the disk image which appears on your desktop
- Drag the artisan application icon to your Applications directory


o Linux

The Linux package is compatible with Ubuntu Linux 10.10, aka the Maverick Meerkat, and Debian Linux 5.0 "Lenny" as well as 6.0 "Squeeze". For now, we simply offer a .deb Debian package that you have to install manually (see below). For future releases, we plan to have a repository so that you can "apt-get install artisan" and get updates automagically.



LICENCE

Artisan is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
   
Artisan is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
   
Copies of the GNU General Public License has been included with this 
distribution in the file `LICENSE.txt`. An online version is available at
<http://www.gnu.org/licenses/>.


LIBRARIES

Artisan uses the following libraries in unmodified forms:

- Python 2.7.x and 2.6.X released under the PSF licence http://www.python.org/psf/
  http://www.python.org/
- QT 4.7.x under the Qt GNU GPL v. 3.0 licence
  http://qt.nokia.com/
- Numpy 1.6.x and Scipy 0.9.x, Copyright (c) 2005, NumPy Developers; All Rights Reserved
  http://www.scipy.org/
- PyQt 4.8.x under the Qt GNU GPL v. 3.0 licence; Copyright (c) 2010 Riverbank Computing Limited
  http://www.riverbankcomputing.co.uk/software/pyqt/
- SIP 4.12.x under the Qt GNU GPL v. 3.0 licence; Copyright (c) 2010 Riverbank Computing Limited
  http://www.riverbankcomputing.co.uk/software/sip/
- matplotlib 1.0.x, Copyright (c) 2002-2009 John D. Hunter; All Rights Reserved
  http://matplotlib.sourceforge.net
- pyaudio 0.2.x under the MIT License; Copyright (c) 2006-2010 Hubert Pham
  http://people.csail.mit.edu/hubert/pyaudio/
- py2app under the PSF open source licence; Copyright (c) 2004-2006 Bob Ippolito <bob at redivi.com>
  Copyright (c) 2010-2011 Ronald Oussoren <ronaldoussoren at mac.com>.
  http://packages.python.org/py2app/
- py2exe, Copyright (c) 2000-2005 Thomas Heller, Mark Hammond, Jimmy Retzlaff
  http://www.py2exe.org/


VERSION HISTORY

v0.5.1 (18.6.2011)
- bug fixes

v0.5.0 (10.6.2011)
- support for Mac OS X 10.4 and PPC added
- added more translations
- added wheel graph editor
- added custom event-control buttons
- added Omega HHM28 multimeter device support
- added support for devices with 4 thermocouples
- added PID duty cycle
- added math plotter in Extras
- added run-time multiple device compatibility and symbolic expressions support
- improved configuration of Axes
- improved configuration of PID
- improved Arduino code/configuration
- improved cupping graphs
- improved performance/responsiveness in multi-core CPUs
- bug fixes

v0.5.0b2 (04.6.2011)
- improved cupping graphs
- improved performance in multi-core CPUs
- bug fixes

v0.5.0b1 (28.5.2011)
- support for Mac OS X 10.4 and PPC added
- added more translations
- added wheel graph editor
- added custom event-control buttons
- added Omega HHM28 multimeter device support
- added support for devices with 4 thermocouples
- added PID duty cycle
- added math plotter in Extras
- added run-time multiple device compatibility and symbolic expressions support
- improved configuration of Axes
- improved configuration of PID
- improved Arduino code
- bug fixes

v0.4.1 (13.4.2011)
- import of CSV is not limited anymore to filenames with "csv" extension
- improved VA18B support
- Windows binary includes the language translations that were missing in v0.4.0

v0.4.0 (10.4.2011)
- improved CSV import/export
- K202 CSV support added
- adds localization support
- adds german, french, spanish, swedish, italian menu translations
- fixed cut-copy-paste on Mac and added cut-copy-paste menu
- LCD color configuration
- replay of events via background dialog
- relative times are used everywhere
- adds profile designer
- adds alarms
- more robust Arduino/TC4 communication
- bug fixes

v0.3.4 (28.02.2011)
- adds Arduino/TC4 device support
- adds TE VA18b device support
- improved Fuji PXR/PXG support
- support for file paths with accent characters
- main window layout improvements
- improved events visualization and capacity
- improved roasting properties dialog
- statistic characteristic line as y-label to ensure visibility if axis limits are changed
- duplicate recent file names show containing directory
- remembers user selected profile path
- added DeltaET/DeltaBT filter to make those delta curves more useful
- adds volume and bean probe density
- adds new command to start/restart roasts
- bug fixes

v0.3.3 (13.02.2011)
- fixed typo in htmlReport
- fixed phases automatic adjusting mechanism
- serial communication improvements
- added support for Fuji PXR5/PXG5
- added NONE device
- added keyboard shortcuts for events and sound feedback
- initial Linux binary release
- added axis settings to application preferences

v0.3.2 (31.01.2011)
- fixed Center 309 communication
- fixed serial device scan on Linux
- added support for Omega HH309
- added open recent, save and (CSV) export menus
- added DRY END Button
- added sync of mid phase with the DRY END and FCs events
- added custom event types
- added events type mini editor widget
- added math tab in extras dialog
- added ambient temperature to roast properties
- extended projection mode
- updated several software components
- improved statistic bar positioning
- new mailing lists for users and developers established

v0.3.1 (12.01.2011)
- fixed issue on loading the user's application preferences

v0.3.0 (11.01.2011)
- fixed occasional ET/BT swap
- fixed issues wrt. accent characters
- added 10.5.x support for Intel-only
- new file format to store profiles
- added configurable min/max values for x/y axis
- added alignment of background profile wrt. CHARGE during roast
- added DeltaBT/DeltaET flags
- added "green Flag" button on Windows
- reorganized dialogs and menus
- added new HUD mode
- smaller changes and additions

v0.2.1 (02.01.2011)
- bug fixes

v0.2.0 (31.12.2010)
- added support for 
 . CENTER 300, 301, 302, 303, 304, 305, 306
 . VOLTCRAFT K202, K204, 300K, 302KJ
 . EXTECH 421509
- bug fixes

v0.1.0 (20.12.2010)
 - Initial release