Artisan helps coffee roasters record, analyze, and control roast profiles. With the help of a thermocouple data logger, or a proportional–integral–derivative controller (PID controller), this software offers roasting metrics to help make decisions that influence the final coffee flavor.


HOME

The project home is on GitHub were all source and binary files are available as well as an issue tracker.

<https://github.com/artisan-roaster-scope/artisan>


MAILING LISTS

Users: <https://lists.mokelbu.de/listinfo/artisan-user>
Developers: <https://lists.mokelbu.de/listinfo/artisan-devel>


ARTISAN BLOG

https://artisan-roasterscope.blogspot.de



FEATURES

o runs on Windows, Mac OS X (>=10.10) on Intel 64bit processor, and Linux (incl. Raspberry Pi)
o UI translated in several languages (English, German, French, Spanish, Portuguese, Swedish, Italian, Arabic, Japanese, Dutch, Norwegian, Finish, Hungarian, Hebrew, Polish, Greek, Turkish, Chinese, Russian, Thai, Indonesian, Korean,..)
o ET/BT logging and PID control supporting the following devices
 - Fuji PXR/PXG 4 & 5 PID
 - Delta DTA PID
 - Modbus Serial ASCII/RTU/Binary, TCP and UDP
 - Omega HH309, HH506RA, HH802U, HH806AU, HHM28
 - CENTER 300, 301, 302, 303, 304, 305, 306, 309
 - VOLTCRAFT K201, K202, K204, 300K, 302KJ, PL-125-T2, PL-125-T4
 - EXTECH 421509
 - Arduino/TC4 with PID
 - TE VA18B
 - HHM28 multimeter
 - non-wireless Amprobe TMD-56 (same as Omega HH806AU)
 - Phidget USB and remote (1010, 1011, 1018, 1019, 1046, 1048, 1051, 1073)
 - Mastech MS6514
 - virtual devices (symbolic devices)
 - device None (no device; manual input)
 - Yocto Thermocouple and PT100
 - Hottop KN-8828B-2K+
 - external program 
and machines
 - Probat Probatone 2
o unlimited number of devices/curves running at the same time
o symbolic manipulation of device outputs
o Fahrenheit and Celsius display and conversion
o manual logging of extra events (FCs,FCe,..)
o custom event buttons supporting up to 10 palettes
o different plotting modes of events
o large buttons supporting touch panels
o live ET/BT rate-of-rise curves
o metric and thermal head-up-display predicting the ET/BT future during logging
o profile statistics and evaluations based on user configurable roast phases
o background reference profile
o user defined cup profiles and cup profile graphs
o HTML report creation
o CSV and JSON export
o Omega HH506, K202, K204 CSV import
o PID duty cycle
o profile designer
o wheel graph editor
o mathematical plotter
o localizations (German, French, Spanish, Portuguese, Swedish, Italian, Arabic, Japanese, Dutch, Norsk, Greek, Turkish..)
o template/background reproduction playback aid
o cascading alarms with programmable outputs
o automatic CHARGE/DROP event detection
o support for digital scales (only Kern and acaia for now)
o event sliders supporting the Hottop Roaster Interface
o event quantifiers
o spike filter and curve smoothing
o color input from color meters
o LargeLCDs and WebLCDs
o volume calculator
o batch counter
o roast, production (for tax reporting) and ranking reports
o software PID and PID-based roast reproduction (follow background mode)
o Area under the Curve (AUC)


INSTALLATION

(see the Artisan project Wiki on GitHub for the latest installation instructions
https://github.com/artisan-roaster-scope/artisan/blob/master/wiki/Installation.md)


o Windows

Artisan for Windows needs a Visual C++ runtime library (file) from Microsoft. This is automatically installed from v0.6 on by the Artisan installer. If Artisan cannot start it will open a Windows error. This is because your computer is missing this file. If you get a window error when you try to start Artisan, install this program:

Microsoft Visual C++ 2008 SP1 Redistributable Package (x86)

http://www.microsoft.com/downloads/en/details.aspx?familyid=A5C84275-3B97-4AB7-A40D-3802B2AF5FC2&displaylang=en

If artisan starts when clicking on artisan.exe (a window pops open with many buttons), then your computer already have this file and you don't need to install anything. Newer OS like Windows 7 come with this file.


o Mac OS X (>=10.10.x)

- Install USB/serial driver for your meter
 . for Omega meters download and run the FTDI VCP OS X installer
   http://www.ftdichip.com/Drivers/VCP.htm
   NOTE: OS X 10.9 and later contain already support for the FTDI hardware and therefore no additional driver needs to be installed on those systems
 . for Voltkraft meters using the original Voltkraft USB cable it is the CP210x driver from Silicon Labs
   http://www.silabs.com/products/mcu/Pages/USBtoUARTBridgeVCPDrivers.aspx
 . some other serial2USB dongles use the Prolific PL2303 chips
   http://prolificusa.com/pl-2303hx-drivers
   (on Mac OS X 10.8 and higher some reported that the org. Profilic driver failed to 
    work, but the [http://sourceforge.net/projects/osx-pl2303/ NoZAP driver] did work)
- Download and run the Artisan OS X installer
(on OS X >=10.8 Mountain Lion you need to tick "Allow applications downloaded from Anywhere" in the Security & Privacy Preference Panel to start the app)
- Double click on the dmg file you just downloaded
- Double click the disk image which appears on your desktop
- Drag the artisan application icon to your Applications directory


o Linux

The Linux package is compatible with Ubuntu/Debian and CentOS/Redhat (glibc 2.12). For now, we simply offer a .deb Debian package as well as an .rpm Redhat package that you have to install manually. This can be done by either double clicking the package icon from your file viewer or by entering the following commands in a shell.

Installation on Ubuntu/Debian
# sudo dpkg -i artisan_<version>.deb

Uninstall on Ubuntu/Debian
# sudo dpkg -r artisan


Installation on CentOS/Redhat
# sudo rpm -i artisan_<version>.rpm

Uninstall on CentOS/Redhat
# sudo rpm -e artisan

In case you run into permission problems such that Artisan is not allowed to read or write to the selected /dev/USB device, you might need to add your account (username) to the dialout group via

# sudo adduser <username> dialout

After this command you might need to logout and login again. Try

# id

that your account was successful added to the dialout group.



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

- Python 2.7.x and 3.x released under the PSF licence http://www.python.org/psf/
  http://www.python.org/
- QT 4.8.x / 5.x under the Qt GNU Lesser General Public License version 2.1 (LGPL)
  http://qt-project.org/products/licensing
- Numpy and Scipy, Copyright (c) 2005, NumPy Developers; All Rights Reserved
  http://www.scipy.org/
- PyQt 5.x and SIP 4.x under the Qt GNU GPL v. 3.0 licence; Copyright (c) 2010 Riverbank Computing Limited
  http://www.riverbankcomputing.co.uk/software/pyqt/
- matplotlib, Copyright (c) 2002-2015 John D. Hunter; All Rights Reserved. Distributed under a licence based on PSF.
  http://matplotlib.sourceforge.net
- py2app under the PSF open source licence; Copyright (c) 2004-2006 Bob Ippolito <bob at redivi.com>
  Copyright (c) 2010-2012 Ronald Oussoren <ronaldoussoren at mac.com>.
  http://packages.python.org/py2app/
- py2exe, Copyright (c) 2000-2005 Thomas Heller, Mark Hammond, Jimmy Retzlaff
  http://www.py2exe.org/
- bbfreeze, Copyright (c) 2007-2012 brainbot technologies AG. Distributed under the zlib/libpng license
- pyinstaller under the GPL license
  http://www.pyinstaller.org
- pymodbus under the BSD License by Galen Collins
  https://github.com/bashwork/pymodbus
- arabic_reshaper.py under GPL by Abd Allah Diab (Mpcabd)



VERSION HISTORY

v1.2.0 (21.12.2017)
 - adds replay by temperature, 
 - support for Phidgets API v22
 - drops support for Phidgets API v21
 - adds support for Phidgets 1002, 1014, 1017, HUB0000, TMP1100, TMP1101, TMP1200, OUT1000, OUT1001, OUT1002, OUT1100
 - adds support for VOLTCRAFT PL-125-T2, VOLTCRAFT PL-125-T4
 - improved RoR and dropout handling

v1.1.0 (10.6.2017)
 - adds Recent Roast Properties
 - adds Aillio Bullet R1 profile import
 - adds support for Probat Probatone 2
 - bug fixes and stability improvements
=> last version supporting OS X 10.9
 
v1.0.0 (24.2.2017)
 - adds internal software PID
 - external MODBUS PID control and faster MODBUS RTU
 - adds support for Apollo DT301 and Extech 755
 - adds Area under the Curve (AUC)
 - adds additional translations
 - adds RPi build
 - bug fixes and stability improvements

v0.9.9 (14.3.2016)
 - adds batch and ranking reports as well as batch conversions
 - adds follow-background for Fuji PIDs
 - adds additional keyboard short cuts
 - designer improvements
 - bug fixes
=> last version supporting OS X 10.7 and 10.8

v0.9.8 (18.10.2015)
 - US weight and volume units
 - extended symbolic formulas and plotter
 - ln()/x^2 approximations
 - bug fixes
 
v0.9.7 (29.7.2015)
 - bug fixes

v0.9.6 (20.7.2015)
 - bug fixes

v0.9.5 (6.7.2015)
 - adds batch counter
 - adds app settings export/import
 - bug fixes
=> last Windows Celeron and Mac OS X 10.6 version

v0.9.4 (6.6.2015)
- bug fixes

v0.9.3 (15.5.2015)
- adds Phidget 1051 support
- adds Hottop KN-8828B-2K+ support
- adds an extra background curve
- bug fixes

v0.9.2 (16.1.2015)
- bug fixes

v0.9.1 (3.1.2015)
- adds QR code for WebLCD URL
- adds support for the acaia BT coffee scale
- bug fixes

v0.9.0 (17.11.2014)
- adds MODBUS ASCII/TCP/UDP support
- adds Yocto TC and PT100 support
- adds Phidget 1045 IR support
- adds Phidget 1046 Wheatstone Bridge wiring support
- adds Phidgets async mode
- adds Polish translations
- adds LargeLCDs and WebLCDs
- adds 2nd set of roast phases
- adds volume calculator
- adds moisture loss and organic loss
- adds container tar
- adds RoR delta span
- adds phasesLCDs showing Rao's development ratio
- bug fixes

v0.8.0 (25.05.2014)
- adds Mastech MS6514 support
- adds Phidget IO support
- adds Phidget remote support
- adds Arduino TC4 PID support
- bug fixes

v0.7.5 (6.04.2014)
- improved serial communication
- fixed extra event manual entry to allow digits
- adds Phidgets 1048 probe type configuration
- adds security patch
- fixed background profile color selection
- increased resolution of temperatures in profiles to two digits
- adds event quantifiers
- adds CM correlation measure between fore- and background profile to statistics bar
- font fix for OS X 10.9
- adds symbolic variables for background temperatures for symbolic assignments
- adds xy scale toggle via key d
- adds modbus temperature mode per channel
- updated Modbus lib
- adds Modbus/Fuji merger

v0.7.4 (13.01.2014)
- fixes ETBT swap functionality

v0.7.3 (12.01.2014)
- improved curve and RoR smoothing
- adds oversampling
- adds support for floats to the Modbus write command
- improved autoCharge/autoDrop recognizer
- updated Phidget library

v0.7.2 (19.12.2013)
- fixed always active min/max filter
- spike filter improvements
- beep after an alarm trigger if sound is on and beep flag is set
- fixes time axis labels on CHARGE
- fixed alarm trigger for button 1
- autosave with empty prefix takes roast name as prefix if available
- external program path added to program settings
- improved autoCHARGE and autoDROP recognizers
- fixes minieditor event type handling
- fixes and improvements to RoastLogger import
- makes the extra serial ports widget editable

v0.7.1 (2.12.2013)
- fixes lockup on extra device use
- fixes redraw artifact on axis changes
- fixes minieditor navigation
- fixes early autoDRY and autoFCs
- fixes extra lines drawing

v0.7.0 (30.11.2013)
- support for the Phidget 1046/1048 devices
- TP event marks (show on graph and in the message log)
- phase LCDs (TP, DRY, FCs) estimating time to the event and counting time after the event (aka a roast development counter)
- adds autoDRY and autoFCs
- links profiles to background profiles
- new graph style using xkcd, path effects and the Humor or Comic font
- allows ETBTa and RoR statistics to be displayed together
- various extensions to the alarms system
- keyboard control for sliders
- adds support for the (to be released) Tonino roast color meter
- some Fuji PID control enhancements
- improved manual mode
- bug fixes

v0.6.0 (14.06.2013)
- monitoring-only mode reporting readings on LCDs without recording
- event sliders e.g. to control the Hottop heater and fan via the HT Roaster Interface
- extended alarms triggered by time and temperature on any curve
- flexible Modbus RTU support allowing temperature reading and device control
- curve smoothing and spike filtering
- new localizations: Arabic, German, Greek, Spanish, French, Japanese, Norwegian, Portuguese, Turkish, Dutch, Chinese and Hungarian
- Windows installer, and icons on Windows and Linux

v0.5.6 (8.11.2012)
- Monitoring-only mode
- adds event sliders
- adds extended alarms
- adds Modbus RTU support
- adds Amprobe TMD-56 support
- adds spike filter
- adds additional localizations
- bug fixes
=> last Mac OS X 10.4/10.5 version and last version support PPC processors

v0.5.5 (28.9.2011)
- fixes ArdruinoTC4 extra devices
- fixed autoDrop recognition
- fixes serial settings for extra devices

v0.5.4 (28.8.2011)
- adds events by value
- adds custom event button palettes
- adds virtual device from plot
- adds K204 CSV import
- improves Designer
- improves Statistics
- improves Help dialogs
- improves relative times
- bug fixes

v0.5.3 (30.7.2011)
- improves performance of push buttons
- adds device external-program
- adds trouble shooting serial log
- fixes Linux Ubuntu and other bugs

v0.5.2 (23.7.2011)
- added Delta DTA PID support
- added automatic CHARGE/DROP event detection
- added separate RoR axis
- added cross lines locator
- smaller Mac OS builds with faster startup
- optimized legend and statistics layout
- improved Wheel Graph editor
- performance improvements
- bug fixes

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
