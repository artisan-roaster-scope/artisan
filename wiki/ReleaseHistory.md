Detailed Release History
========================

----
v1.5.0 (17.10.2018)
------------------

 * New Features
   - adds ArtisanViewer mode allowing again to run a second (restricted) instance of Artisan ([Issue #260](../../../issues/260))
   - adds support for VoltageRatio for Phidgets IO enhancement ([Issue #252](../../../issues/252))
   - extends LCD rendering from [-999,9999] to render [-9999,99999] if "Decimal Places" are turned on
   - adds "Program 78" and "Program 910" device types
   - adds support for manual [Besca roasting machines](https://www.bescaroasters.com/)
 * Changes 
   - order of columns in roast/background properties events table, CSV import/export and Excel export swapped (ET always before BT)
   -  event values on the graph are not abbreviated anymore if "Decimal Places" is not ticked
 * Bug Fixes 
   - fixes udev rule installation on Redhat/CentOS rpm builds
   - fixes broken Linux builds crashing on opening the file selector ([Issue #259](../../../issues/259))
   - fixes Windows gevent build error by upgrading to PyInstaller 3.4
   - fixes broken Hottop communication on Windows ([Issue #258](../../../issues/258))
   - fixes WebLCDs not starting on Windows ([Issue #253](../../../issues/253))
   - fixes HUD crashing ([Issue #255](../../../issues/255))
   - LCDs do not truncate readings to last 3 digits anymore if "Decimal Places" are ticked, but indicate an overflow by rendering two dashes ([Issue #256](../../../issues/256))
   - fix issue preventing Stats Summary from showing if language is not set to English ([Issue #257](../../../issues/257))
   - adds sampling interval to profiles generated using the designer
   - ensures that profiles lacking an indication of the sampling interval used on recording are rendered when loaded into the background
   - fixes typo in drop-out handling resulting in disappearing curves during recording ([Issue #254](../../../issues/254))
   - ensures that "Snap Events" settings are persisted ([Issue #251](../../../issues/251))
   - fixes Excel export listing BT twice instead of BT and ET
   - fixes regression that deactivated curve smoothing completely



----
v1.4.0 (03.10.2018)
------------------

 * New Features
   - adds time guide option (most useful when following a background profile)  
   - adds export and convert to Excel
   - adds PhasesLCD mode-by-phase selection
   - adds PhasesLCD mode that shows all of time/temp/percentage in finish phase accros the 3 Phases LCDs ([Issue #235](../../../issues/235))   
   - adds flag to allow phases to be adjusted based on DRY and FCs of the background profile
   - adds [PID P-on-Measurement/Input mode](http://brettbeauregard.com/blog/2017/06/introducing-proportional-on-measurement/) for internal Software PID and [TC4 aArtisanQ v6.6 PID](https://github.com/greencardigan/TC4-shield/tree/master/applications/Artisan/aArtisan_PID/tags/REL_aArtisanQ_PID_6_6) (complementing the standard P-on-Error mode)
   - adds KeepON flag
   - adds playback DROP event from background profile by time or temperature
   - adds zero-ing of channels via extra symbolic variables Tn set to current value on right-click of corresponding LCD
   - adds barometric pressure to roast properties and statistic summary
   - adds support for ambient sensors Phidget [HUM1000](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=644) and [PRE1000](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=719)
   - add machine setup for Hottop TC4 configurations, [Atilla GOLD plus 7"](http://www.atilla.com.br/p/atilla-5kg-gold-plus/), [Besca roasting machines](https://www.bescaroasters.com/), [Coffee-Tech Engineering Ghibli](https://www.coffee-tech.com/products/commercial-roasters/ghibli-r15/) and [Diedrich Roasters](https://www.diedrichroasters.com/)
   - adds fan RPM to R1 Aillio setup
   - adds option to load alarms from background profiles
 * Changes 
   - ensures that background curves are always render using the same smoothing algorithm as the foreground
   - adds re-sampling and back-sampling to improve all smoothing algorithms
   - adds "Insert" button to trigger the extra event table insert action instead of abusing the "Add" button
   - use zero-based port numbering in Phidgets tab
   - renumbers config event types 1-4 to be consistent with plotter notation
   - adds roastUUID to alog profiles
   - ensures that only a single instance runs per machine
   - adds a pop-up reminder message when you forget to right-click on the timer LCD in Hottop 2K+ mode ([Issue #220](../../../issues/220))
   - allow alarms to move sliders beyond the default range of 0-100 ([Issue #213](../../../issues/213))
   - maps internal PID duty 0-100% to the full min/max range of the selected positive/negative target sliders
   - updates in-app link to documentation
   - simplifies to one set of roast phases
   - more accurate timestamping
   - increases number of time/temp decimals in alog profiles
   - LCDs extended to show readings beyond 4 digits without decimals ([Issue #238](../../../issues/238))
   - roast phase visualisation graph of the ranking report now also shown if more than maximally rendered profiles have been selected and this maximum was increased from 10 to 20
   - adds warning if more than 10 profiles are selected that graph will not be rendered ([Issue #226](../../../issues/226))
   - autoAdjusts now ensures also that the background profile is fully visible
   - split temperature menu actions and move conversions to Tools menu
   - improved rendering of statistic summary
   - adds beans and roasting notes to statistic summary
   - save and restore "geometry" of Events configuration dialog
   - reset window geometries and dpi settings on factory-reset
   - removes Py2.7 support and updates build environment
   - improved autoCHARGE/autoDROP in Fahrenheit mode
 * Bug Fixes 
   - fixes missing translations on Linux/RPi ([Issue #211](../../../issues/211))
   - fixes hanging message line in FullScreen mode
   - close the device assignment dialog before opening the serial dialog to ensure that it cannot hide the serial dialog if app is put in background and back in foreground again
   - avoids flicker of the navbar on loading setups if canvas color did not change
   - fixes S7 for Windows and Linux that got broken by the code restructuring in v1.3.1
   - fixes a modbus hickup due to modularization in relation to serial logging
   - allows a negative ambient temperature in roast properties ([Issue #221](../../../issues/221))
   - prevent an exception when editing times in an imported profile
   - format the first entry in RoastProperties>Data table for correct paste after copy
   - fixes the post roast calculation for CHARGE and DROP to match the auto calculations during a roast
   - change the way RoR is calculated for the first phase in the Designer to be consistent with the recorded profiles (from TP to DE)
   - disables CMD-N NEW action during recording until CHARGE and DROP are set ([Issue #225](../../../issues/225))
   - fixes slider layout issue and removes remaining PyQt4 support
   - fixed PID dialog geometry
   - render long legends more compact
   - makes Probat Pilot import/export compatible with latest Pilot version ([Issue #228](../../../issues/228))
   - allow duplicate button events of empty event type "-"
   - fixes slider event unit defaults
   - ensures visible selection and hover actions in navigation bar on OS X under any theme
   - fixes Events buttons labels which were not set correctly on changing their event type
   - deactivate figure_options in designer mode preventing all kind of side effects
   - fixes an issue of not fully restoring the main window geometry if a previous loaded profile is re-loaded on startup
   - fixes RoR Filter unit labels
   - fixes a redraw issue caused by deactivated event types leading to wrong background line count
   - improves autoCharge detection on fast sampling rates
   - ensures that drop-filter is applied on (non-optimal) decay smoothing
   - reduces long (blocking) delay between the two samplings occurring with oversampling turned on
   - fix an issue leading to a 100% duty after turning PID off and then on again
   - better error message when trying to install on 32bit windows
   - fixes Fuji PXR PID dialog ([Issue #243](../../../issues/243))
   - fixes an issue in the event quantifier that could lead to doublicate events


----
v1.3.1 (20.5.2018)
------------------

 * New Features 
   - adds Cmd-Shift-S as shortcut for "Save As" ([Issue #194](../../../issues/194))
   - remembers fullscreen mode over restarts ([Issue #199](../../../issues/199))
   - allows to insert a custom event button line before the selected one by clicking Add
   - adds insert action to the alarm table to add an alarm line before the selected one
   - adds support for the new Fuji PID PXF
   - adds PXF variant of Sedona Elite and Phoenix machine configurations
   - adds copy as tab delimited text action for data tables
 * Changes
   - restricts the "time-to" display introduced in v1.3 to the temperature mode rendering the percentage mode again as in v1.2 ([Issue #196](../../../issues/196))
   - all hundredths not only thenth in roast properties weight and volume ([Issue #198](../../../issues/198))
   - requires to tick the `Control` flag to activate the ´Control` button and the PID features also for the case of the TC4 with PID Firmware as for the Fuji PIDs ([Issue #205](../../../issues/205))
   - events created by sliders now put the values translated using the sliders offset and factor to the event descriptions together with a unit postfix
   - started internal code modularisation resulting in lower memory demand in most cases
   - removed support for Qt4
   - updates to pymodbus 1.5.2 for better error handling on noisy lines
   - increase width of phases LCDs to hold one more digit and update tooltip
   - improves slider release action
   - the semantic of the MODBUS little_endian `word` flag, relevant for Float values only, of the underlying pymodbus lib changed with the effect that some setups need to be updated (eg. the one for BC Roasters, and Coffeetool) by inversing the flag.
 * Bug Fixes
   - ensures that the matplotlib font cache is used on Linux ([Issue #178](../../../issues/178))
   - fixes an error that could occur on deleting an event button definition ([Issue #179](../../../issues/179))
   - ensures proper persistance of the "Descr." checkbox state of the events dialog over restarts ([Issue #180](../../../issues/180))
   - fixes a communication issue with Aillio Bullet R1 roasters running a newer firmware ([Issue #188](../../../issues/184))
   - fixes a build error in v1.3 that caused Artisan to crash on opening a file selector ([Issue #182](../../../issues/182),[Issue #187](../../../issues/187),[#188](../../../issues/188))
   - ensures that decimals in curve width are properly handled ([Issue #186](../../../issues/186))
   - fixes a regression that disallowed for negative event button values ([Issue #191](../../../issues/191))
   - fixes an unhandled exception in the alarm processing ([Issue #192](../../../issues/192))
   - fixes a rare case were the first event listed in roasting reports got duplicated ([Issue #195](../../../issues/195))
   - fixes Phidgets pulses that never latched back
   - fixes background title colors
   - fixes a problem setting extra device colors
   - fixes reveal of hidden buttons when changing Config>Colors
   - fixes some redraw hickups in fullscreen mode on OS X
   - fixes wrong character encoding of dates in statistic summaries
 * Builds
   - v1.3.1(0): build 0 (initial release)
   - v1.3.1(1): build 1 uploaded on 22.05.2018
     - fixes BC Roaster machine setup
   
----
v1.3.0 (15.4.2018)
------------------

 * New Features 
   - adds extraction yield calculator by Rui Paulo
   - adds configurable alarm popup timeout
   - adds MODBUS BCD decoding
   - adds support for the Siemens S7 protocol
   - adds support for custom event values larger than 100 up to 999
   - adds new custom event rendering options and the option  to render event descriptions instead of values
   - adds the new custom event button type "--" that adds an event (compared to the pure action button of type "  ") 
  and can be used to add labels to the graph rendering its button description
   - adds color themes
   - adds color check messages to warn when foreground and background colors are too similar
   - adds FC duration to characteristics
   - adds reload of last load profile on app start
   - adds ability to define left time axis limit on CHARGE/RESET
   - adds a flag to disable the (offline) optimal smoothing algorithm such that online (during recording) and offline curve and RoR representation should be equal.
  Note that without optimal smoothing active, temperature curves are not smoothed at all.
   - adds rendering of the AUC (Show Area)
   - adds sliders with min/max limits adjusting to the actual temperature unit
   - adds direct support for [Aillio Bullet R1](https://aillio.com/), [BC Roasters](http://www.buckeyecoffee.com/), [Bühler Roastmaster](http://www.buhlergroup.com/), [Coffed SR5/SR25](http://coffed.pl/), [Coffee-Tech FZ-94](https://www.coffee-tech.com/), [Coffeetool R500/3/5/15](http://coffeetool.gr/), [Giesen W1A/W6A/W15A](http://www.giesencoffeeroasters.eu/), [IMF RM5/RM15](http://www.imf-srl.com/), [K+M UG15/UG22](https://www.kirschundmausser.de/), [Loring S7/15/35/70](https://loring.com/), [Phoenix ORO](http://www.buckeyecoffee.com/), [Proaster](http://proaster.coffee/), [San Franciscan SF1-75](http://www.sanfranroaster.com/), [Sedona Elite](http://www.buckeyecoffee.com/), [Toper TKM-SX](http://www.toper.com/), [US Roaster Corp](http://www.usroastercorp.com/)
   - adds crash reporter
   - adds expected time to DRY and FCs to phases LCDs in percentage  and temperature mode
 * Changes
   - reorganized some menus and dialogs
   - improves location calc for statssummary
   - allow alarm button action to trigger several buttons at once via a list. The following string is now valid: "1,2,3 # docu"
   - imports a broader range of aillio bullet r1 profiles
   - various ranking report graph improvements
   - statistic summary layout improvements
   - enhances "Show on BT" to include all special events
   - keyboard mode jumps to the first non-flat button automatically
   - allow for 0.5s sampling rate
   - Hottop default setup adds DROP action to put fan to 100% and heater to 0% and open the door and event quantifier definition
   - deactivates mouse-over scroll wheel events on combo-boxes inside scrolling areas
   - allows one decimal in alarm value limits
   - redesigned slider style
   - cleaned up time axis setup and introduced the possibility to set the min time axis limit on RESET/CHARGE
   - changes some defaults (DeltaET lcd hidden, render delta curves thinner than temperature curves)
   - sliders and buttons remember their visibility per state (OFF/ON/START)
   - convert temperatures on profile load instead of switching the temperature mode
   - event actions are processed in parallel threads
   - Mac OS X app now code signed for easier installation
 * Bug Fixes
   - fixes a bug that made the background RoR curves disappear on START
   - fixes a crasher on clicking the SV slider
   - fixes designer reset issue
   - fixes p-i-d button action that never triggered
   - fixes coarse quantifiers
   - recomputes AUC in ranking reports based on actual AUC settings
   - fixes an issue where closing a confirmation dialog via its close box could lead to losing the recorded profile instead of canceling the activity
   - ensures that the persisted graph dpi is applied on startup and loading settings
   - fixed Issue #154 where replay-by-temp events would trigger out of order
   - fixes Phidgets 1046 device support broken in v1.2
   - restrict temperature conversion to temperature curves
   - fixes crasher on some Linux platforms w.r.t. selection of items in tables like events, alarms,..


----
v1.2.0 (21.12.2017)
------------------

 * New Features
	- adds alarm file name to Roasting Report
	- adds SV alarm action
	- adds event replay by temperature (donated by doubleshot)
  		- event replay is active only after CHARGE
  		- replay-by-temperature is active only after TP and before it falls back to replay-by-time
  		- to replay an event its event slider must be active (ticked) and the event name has to correspond to that of the background profile
	- adds option to show MET marker on ET curve, click icon to display MET details (by Dave Baxter)
	- adds option to show events markers on BT instead of ET (by Dave Baxter)
	- adds option to show statistics summary (try it with Auto Axis enabled) (by Dave Baxter)
	- makes the display optional for each of the four special events (by Dave Baxter)
	- adds click-and-drag measurements (by Dave Baxter)
	- adds support for Phidgets API v22
	- adds support for new VINT devices
 		- HUB0000 (Voltage Input, Digital Input, PWM Output)
 		- TMP1100 (1x Isolated TC)
 		- TMP1101 (4x TC)
 		- TMP1200 (1x RTD)
 		- OUT1100 (4x 5V PWM)
      - OUT1000 (4x 12bit Voltage Output, 0-4V2)
      - OUT1001 (4x 12bit Isolated Voltage Output, -10V to +10V)
      - OUT1002 (4x 16bit Isolated Voltage Output, -10V to +10V)
      - USB IO 1002 (4x Voltage Output)
      - USB IO 1014 (4x Digital Output)
      - USB IO 1017 (8x Digital Output)
   - adds toggle, out, set, pulse commands to operate digital and analog Phidgets outputs per buttons and sliders
	- adds Phidgets 1048 data rate configuration
   - adds Phidgets IO (1011, 1018,..) digital input support
	- adds support for multiple Phidgets devices of one type
	- adds keyboard shortcut to quickly load alarm file
	- adds support for the VOLTCRAFT PL-125-T2 and VOLTCRAFT PL-125-T4 (by Andreas Bader)
	- adds Exhaust Temperature to the Aillio Bullet import
	- adds optional automatic saving of PDFs alongside alog profiles
	- adds Hottop to the machine menu
   - adds "remote only" flag to the Phidget tab to force remote access also for locally connected Phidgets if local Phidget server is running. That way the local Phidget server can be use on the machine running Artisan to access the Phidgets from Artisan and any other software (incl. the Phidget Control Panel) in parallel.
   - adds support for MODBUS function 1 (Read Coil) and 2 (Read Discrete Input)
   - sends DTA Commands to the BTread PID if the ETcontrol PID is not a DTA
   - adds IO Commands action to sliders
   - adds mechanism to show/hide the control bar as well as the readings LCDs
   - adds a roast phase statistics visualization to the ranking report (by Dave Baxter)
   - adds drum speed field to roast properties (by Dave Baxter)
 * Changes
	- drops support for OS X 10.9 and earlier
	- extends special event lines to the drop time (by Dave Baxter)
	- drops support for Phidgets API v21
	- Phidgets IO changes
 		- drops raw mode and ratio metric flag
 		- data range changed from 0-1000 (0-4095 in raw mode) to 0-5000mV
	- adds tooltip translation for toolbar icon menus
	- suppresses wrong readings caused by communication drop outs
	- synchronizes background and foreground RoR smoothing to guarantee equal delay/shift
	- CRTL modifier now required to change palettes via number key shortcuts
	- disallow placing (new) events during recording via the right-click popup menu to BT
	- reduces initial window width from 811px to 800px to fit on the RPi 7" display
	- all builds are now based on Python3.5 and Qt5.9.x
	- axis defaults adjusted to increase size of relevant data on screen
	- releases Hottop control on OFF
	- adds coarse sliders stepping in multiples of 10 instead of 1
    - call program alarm actions interpret text after the comment delimiter # as a line comment
   - most Phidgets device names have been renamed to better reflect its type. Channels are now counted zero-based as on the hardware
   - wheel graph starts in view mode and remembers last loaded wheel
 * Bug Fixes
	- fixes for Numpy v1.13 and Matplotlib 2.1
	- fixes for the Probatone 7" setup
	- fixes an RoR filtering issue
	- improved RoR ramp up calculation avoiding initial hickups
	- fixes a MODBUS ASCII/BINARY build issue
	- fixes HUD button visibility
	- fixes background profiles TP time marks
	- fixed washed out event annotations during recording
	- fixes the wheel graph
	- fixes "Call Program" for commands with parameters called from alarms on Windows
   - fixes PID background-follow mode messing up at the end of the background profile
   - fixes Fuji PXR set p-i-d and set Ramp/Soaks

**Note**
_This is the latest version supporting supporting Mac OS X 10.12 and Linux glibc 2.17_

----
v1.1.0 (10.06.2017)
------------------

 * New Features
    * adds [Recent Roast Properties](https://artisan-roasterscope.blogspot.de/2017/06/recent-roast-properties.html)
    * adds "Fuji Command" to send commands to connected Fuji PIDs
    * adds ~ path expansion to users home directory and improves external program argument handling (thanks to Max)
    * adds prediction of DRY and MAY phases to Phases LCDs before the corresponding phases have been completed
    * adds configuration for RoR min/max filter
    * adds substitution of \r\n, \n and \t by the corresponding newline and tab characters in serial commands
    * adds \t by type substitution in event button labels and {n} substitutions in LCD labels
    * adds slider min/max settings
    * adds slider synchronization per event quantifiers
    * adds flags to hide/show background ET/BT curves
    * adds Aillio Bullet R1 profile import
    * adds [Probat Probatone 2 support](https://artisan-roasterscope.blogspot.de/2017/06/probat-probatone.html)
 * Changes
    * changes background of snapped by-value events
    * renamed and localized custom event labels
    * profiles sampling interval setting cannot be modified after recording anymore
    * increases resolution on displaying by-value events from 0-10 to 0-100
    * improved LCD color defaults
 * Bug Fixes
    * fixed random issue with line breaks in custom button labels
    * fixed Fuji background issue
    * fixes call-program issue on Python3
    * fixes extra event line initialisation
    * fixes PID I windup and minimizes extra PID smoothing delays
    * fixes auto time-axis alignment for background profiles
    * fixes 64bit Yoctopuce lib path for Windows builds
    * fixes "Start PID on CHARGE" for MODBUS/TC4 devices
    * fixes LCD color setup
    * fixes unicode handling in palette save/load
    * various small fixes and improvements to the quantifier and clustering mechanisms
    * fixes a failure to load profiles caused by a NaN in the computed section of saved profiles
    * fixes a Fuji MODBUS decoding issue on Python3


**Note**
_This is the latest version supporting supporting Mac OS X 10.9, Windows XP/7 and 32bit OS versions_
        
----
v1.0.0 (24.02.2017)
------------------

 * New Features
    * adds [internal PID](https://artisan-roasterscope.blogspot.de/2016/11/pid-control.html) and support to control external MODBUS PIDs
    * adds two more MODBUS input channels (now 6 in total)
    * adds alarms triggerd at a specified time after another alarm specified as "If Alarm" was triggered, if "from" rules is set to "If Alarm"    
    * adds improved Windows installer (option to uninstall previous versions during installation and silent option)
    * adds support for loading Artisan profiles from zip files for reporting (as kindly contributed by David Baxter)
    * adds experimental support for the [Apollo DT301](http://www.ueitest.com/products/temperature-humidity/dt301) (by Rob Gardner)
    * adds experimental support for the [Extech 755](http://www.extech.com/display/?id=14489) pressure manometer (by William and Brian Glen)
    * adds "Playback Events" function to playback background events if corresponding sliders with actions are defined
    * adds serial port to DUMMY device. If selected as main device, one can send serial commands to its serial port from alarms and buttons
    * adds support for multiple-connected Yoctopuce devices (thanks to Nick Watson)
    * adds undo of the last entered main event by clicking its button again
    * adds TP annotation on background profiles
    * adds SV slider to the Fuji PXG
    * adds pyinstaller build setup for Mac OS X
    * adds flag to disable/enable the number key shortcuts for switching palettes
    * adds MODBUS scanner
    * adds Custom Events clustering
    * adds flag to automatically open roast properties on CHARGE
    * adds Yoctopuce VirtualHub support for acessing remote Yoctopuce devices over the network
    * adds automatic unit conversion for Yoctopuce devices
    * adds profile C<->F batch conversion
    * adds a field for green bean temperature
    * adds p-i-d button action    
    * adds auto axis limits calculation via manual trigger or automatic on load
    * adds [AUC statistics, LCD and guide](https://artisan-roasterscope.blogspot.de/2016/11/area-under-curve-auc.html)
    * adds possibility to "clamp" by-value custom events to the x-axis in the range of 0-100
    * adds support for MODBUS mask-write (mwrite; function code 22) and write registers (writem; function code 16) methods
    * adds Raspberry Pi (Jessy) build
    * adds color labels to HTM ranking reports
    * adds Russian, Indonesian, Thai and Korean translations (thanks to Taras Prokopyuk, Azis Nawawi, Rit Multi, Joongbae Dave Cho)
    * adds Probat Pilot import/export
 * Changes
    * dramatically improves speed of MODBUS over serial communication (by patching the underlying pymodbus lib)
    * makes message, error and serial logs autoupdating
    * removes "insert" in alarm table, which is not compatible to the new flexible alarmtable sorting
    * restrict file extension to ".alog" on loading a profile
    * current slider and button definitions are now automatically saved to palette #0 on closing the events dialog such that those definitions cannot get lost accidentially by pressing a number key to quickly entering an event value during recording
    * reconstruct users environment on calling external programs on MacOS X, not to limit them to the Artisan contained limited Python environment
    * remembers playback aid settings
    * improved RoR smoothing during recordings
    * makes development percentage the default for the phases lcds
    * increases resolution for Yoctopuce devices
	* timeouts accept one decimal place
	* improved dialog layouts
 * Bug Fixes
    * improves ranking reports for mixed profiles with different temperature units
    * fixed an issue with the Arduino/TC4 communication setup
    * 3rd temperature channel of background profile did not move along the rest
    * fixes program path if used as extra devices
    * allows custom event values of value -1
    * improved Amprobe and Mastech support handling communication failures better
    * fixes image paths in HTML reports
    * fixes hangs and accent character support on "Playback Aid"
    * improved autoDROP
    * fixes WebLCDs on Mac OS X   
    * fixes Fuji PXG duty overflow for values from -3% to 0%
    * fixes handling of external program paths containing accent characters on Windows
    * fixes handling of accent characters in autosave path
	* improves handling of external program calls
    * various stability improvements
    * fixes hang on RESET serial action
    * fixes Phidgets remote access on Python 3

**Note**
_This is the latest version supporting Mac OS X 10.7 and 10.9_

----
v0.9.9 (14.03.2016)
------------------

 * New Features
    * adds zoom-and-follow function (toggled by a click on the HOME icon; keeps the current BT in the center)
    * adds MODBUS dividers
    * adds a flag to hide the "SV/% LCDs" (default on)
    * adds World Coffee Roasting Championship (WCRC) cupping profile
    * adds batch and ranking reports in HTML/CSV/Excel format
    * adds follow background for Fuji PIDs
    * adds high-res app icon for OS X
    * adds "File version" and "Product version" to Windows app installer
    * adds flag to let x^3 math regression start from TP instead of room temperature
    * adds background moving by using the cursor keys
    * adds PID keyboard shortcuts to toggle mode and (p key) and to incr/decr lookahead (+/- key)
    * designer: adds save/load of points
    * designer: adds keyboard entry on adding points    
    * availability on Arch Linux
    * adds batch conversion to various formats (CSV, JSON, PDF, PNG,..)
    * adds switch ET<->BT action
    * adds key shortcut (H key) to load background profile
    * adds a function to call a program on sampling with the temperatures ET, BT, ET-Background, and BT-Background as arguments
    * adds draggable legend
    * adds compatibility to Python3.4, pyserial3.x, Qt5, PyQt5, matplotlib 1.5 on all platforms
    * adds windows maximizing decoration to all dialogs on Windows and Linux
 * Changes
    * existing extra device mathexpression formulas are no longer changed if extra devices have to be extended on loading a profile
    * deactivates the auto-swap of ET/BT on CSV import (issue #85)
    * increased Hottop safety BT limit from 212C/413F to 220C/428F
 * Bug Fixes
    * better initial Phidgets attach handling
    * improved RoR calculation
    * improved temperature and RoR curve drawing, fixes among others the issue of the delta curves missing from the roasting report (issue #84)
    * fixes regression on moving the background up and down
    * minor improvements
    * fixed rare slider selection visual artifact on OS X
    * ensures that alarms are sorted based on alarm numbers on opening the dialog
    * fixed volume increase calculation

**Note**
_This is the latest version supporting Mac OS X 10.7 and 10.8_

----
v0.9.8 (21.10.2015)
------------------

 * New Features
   * adds menu entries to hide/show extra buttons and sliders
   * support of multiple selection in events table (event dialog)
   * adds events to alarm conversion (event dialog)
   * click on Control button in PID mode toggles PID standby mode
   * adds "Annotations" flag to hide annotations on BT (CHARGE, FCs, ..) (event dialog)
   * click on event items in events-by-value mode shows details in the message line
   * initial support for building Artisan on Windows/Python3/Qt5/PyQt5 platform
   * initial support for running on Raspberry Pi (Jessy)
   * adds event actions for RESET und START buttons (event dialog)
   * adds alarm actions CHARGE, RampSoak ON/OFF, PID ON/OFF (alarm dialog)
   * adds [ln() and x^2 math approximations](http://artisan-roasterscope.blogspot.de/2015/10/natural-roasts.html)
   * enhanced [symbolic formula evaluator and plotter](http://artisan-roasterscope.blogspot.de/2015/10/signals-symbolic-assignments-and-plotter.html) adding time shifting among others
   * adds support for US weight and volume units
   * adds XTB data to the background dialog if selected in the table of the background dialog
   * adds support for [event actions that change event values by a specified offset](http://artisan-roasterscope.blogspot.de/2015/10/increasing-heat.html) instead of an absolute value
 * Changes
   * custom event buttons and sliders remembers visibility status
   * plotter "Virtual Device" action renamed into "BT/ET", now adds plot data to BT/ET if no profile is loaded, otherwise it creates an additional Virtual Device
   * the symbolic variables ETB and BTB to access data from the background curves have been generalized and renamed into B1 and B2
   * default state of the statistic line on the bottom of the main window changed (right-click still toggles) and setting made persistent
   * time align of background profiles now possible per all major events possible (always aligns to CHARGE first, and if set to ALL, it aligns to all events in sequence of their occurence)
   * increases the time and temperature resolution
 * Bug Fixes
   * fixed port name support in serial port popup on OS X
   * fixed printing on OS X
   * fixed sorting of alarm list of numbers larger than 9
   * fixed temperature conversion issues (phases / background profile interactions)
   * fixed Yocotopuce reconnect handling
   * fixed Fuji PRX duty signal
   * fixes a build issue on Mac OS X to prevent a startup crash related to X11 libraries

----
v0.9.7 (29.7.2015)
------------------

 * Bug Fixes
   * fixes epoch rendering in profiles
   * fixes non-modal dialog UI hangs (PID dialog, messages, error, largeLCDs, serial, platform, calculator)
   * fixes Fuji PXR reading of times on "Read Ra/So values"

----
v0.9.6 (20.7.2015)
------------------

 * Bug Fixes
   * fixed translations
   * fixed accent processing in extra background profile names
   * tolerate spaces in sequenced command actions
   * a further fix to a redraw bug introduced in v0.9.4
   * fixed Linux and Windows build setup

----
v0.9.5 (6.7.2015)
------------------

 * New Features
   * adds timestamp to profiles
   * adds batch counter
   * adds exporting and importing of application settings (experimental!)
   * restricts Hottop control to "super-user" mode
   * adds Hottop BT=212C safety eject mechanism
 * Changes
   * more stable Hottop communication via parallel processing
   * "call program" action on Mac OS X and Linux now calls the given script name instead of initiating an "open" action
   * upgrade to Qt5 on Mac OS X
   * performance improvements
 * Bug Fixes
   * fixed Yocto build issue on Mac OS X
   * fixed a redraw bug introduced in v0.9.4


**Note**
_This is the latest version supporting the Windows Celeron platform and Mac OS X 10.6 (Intel only)_

----
v0.9.4 (6.6.2015)
------------------

 * New Features
   * adds alarm table sorting
 * Changes
   * improved custom event annotation rendering
   * roast report now lists additionally the ET temperature of events
   * updated underlying libs like Python/Qt/PyQt/Matplotlib/.. (Mac OS only)
   * Hottop control mode is active only in super-user mode (right-click on the Timer LCDs)
 * Bug Fixes
   * fixed element order in legend
   * fixed WebLCDs
   * fixes to Fuji PXR "RampSoak ON" mechanism


----
v0.9.3 (15.1.2015)
------------------

 * New Features
   * adds CENTER304_34
   * adds Phidgets 1051 support
   * adds Hottop KN-8828B-2K+ support
   * display one (selectable) extra curve from the background profile
   * adds asynchronous, but regularly triggered event commands
   * proposes a file name in the file dialog on first save
 * Changes
   * roast report now lists additionally the ET temperature of events
 * Bug Fixes
   * fix unicode handling in CSV import/export
   * slider and button actions with command arguments fixed
   * Mastech MS6514 communication improvements (thanks to eightbit11)
   * Omega HH806AU retry on failure during communication
   * fixes Yocto shared libary loading on Windows and improves the reconnect on reset
   * missing quantifiers application on START
   * TC4 "Start PID on CHARGE" now works on consequtive roasts
   * TC4 enable ArduinoTC4_56 and ArduinoTC4_78 extra device use without adding ArduinoTC4_34
   * MODBUS communication improvements


----
v0.9.2 (16.1.2015)
------------------

 * New Features
   * configurable commands on ON, OFF and per sampling interval
   * command sequencing using the semicolon as delimiter
   * adds MODBUS read, wcoil, wcoils commands and last result substitution variable accessible via the underline character
   * adds [HukyForum.com](http://www.hukyforum.com/index.php) image export
 * Bug Fixes
   * fixes color dialog for extra devices on OS X
   * fixes a potential crasher caused by x-axis realignment during sampling
   * fixes communication issues with Phidgets especially in remote mode via an SBC
   * fixes WebLCD startup issues on slow Windows machines
   * fixes MODBUS over UDP/TCP IPv6 issues on Windows

----
v0.9.1 (3.1.2015)
-----------------

 * New Features
   * adds QR code for WebLCD URL
   * adds keyboard short cut to retrieve readings from a serial scale (press ENTER in roast properties weight-in/out fields or volume calculator field)
   * adds support for the acaia BT coffee scale
   * adds serial scale support to Volume Calculator
   * adds tare support to Volume Calculator
 * Changes
   * changes x-axis minor ticks to one minute distance
   * Python updated to v2.7.9
   * Italian translations update
 * Bug Fixes
   * fixes Arduino/TC4 temperature units
   * fixes button value restoring on palette load
   * fixes Volume Calculater unit conversion


----
v0.9.0 (17.11.2014)
-------------------

 * New Features
   * adds MODBUS ASCII/TCP/UDP support (via pymodbus)
   * adds Yocto thermocouple and PT100 support
   * adds Phidget 1045 IR support
   * adds support for Phidgets 1046 Wheatstone Bridge wiring variant
   * extended Phidgets configurations (adds async support, data rates and change triggers)
   * adds program_34 and program_56 device to read extra channels from external program
   * adds DUMMY device that returns always 0 to allow mapping of extra channels to the main device (ET/BT)
   * adds "wcoils" to write MODBUS command "Write Multiple Coils" (function 15)
   * extended Italien translations
   * adds Polish translations
   * logs active non-zero slider values at CHARGE
   * adds coarse quantifiers 0-10, 10 steps instead of 100 as for standard quantifiers
   * Phidget 1048 sets ambient temperature (in roast dialog) automatically on DROP
   * adds quick custom event keybord shortcuts (keys q-w-e-r followed by 3 digits)
   * file from which alarms were loaded is now displayed in the alarms dialog
   * extends phases lcds by Rao's style ratios and BT deltas
   * adds MET calculation (maximum ET between TP and DROP)
   * adds moisture of roasted beans to roast properties
   * background title as subtitle
   * adds flag to align of background profiles also wrt. FCs
   * adds button action to set digital outputs on Phidgets IO
   * adds BT/ET rate-of-rise to the designer
   * adds "Delta Span" setting
   * adds "Call Program" action to sliders
   * LargeLCDs and WebLCDs
   * adds 2nd characteristics line on right click
   * adds time axis lock mode
   * adds a volume calculator
   * adds moisture loss and organic loss calculation
   * second set of phases definitions (now one for Espresso and one for Filter roasts)
   * adds configuration of Arduino/TC4 filter settings
   * container tare setup
 * Changes
   * recent file menu size extended from 10 to 20 entries
   * missing files are removed from recent file menu
   * automatic saved files are added to the recent files menu
   * updated build setup on Windows and Mac OS X
   * quantifier range extended from [-999,999] to [-99999,99999]
   * removes leading zeros from time annotations
   * faster OFF
   * moved Phidgets configurations to extra tab
   * precision of times and temperatures in stored profiles extended by another digit
   * alarm dialogs auto close after 10sec
 * Bug Fixes
   * fixes autosafe failure on invalid filenames
   * allow to hide HUD button and Control button in ArduinoTC4 mode
   * all serial ports and other connections are closed on OFF
   * x-Axis min limit can now be set to 00:00
   * fixed palette switching using keyboard shortcuts
   * native color dialog on Mac OS X blocked other dialogs and menu actions
   * call-program action fixed
   * mouse cross lines in deltaBT/ET mode fixed
   * fixed designer resize redraw issue
   * fixed the Fuji PXR SetRS
   * phases were updated on profile load despite the Auto Adjust phases not being ticked
   * CSV roundtrip on Windows
   * missing reset before import added
   * settings are stored on closing Artisan by closing its main window
   * fixed quantifier application


----
v0.8.0 (25.05.2014)
-------------------

 * New Features
   * adds Mastech MS6514 support
   * adds Phidget IO support (eg. 1018 or SBC)
   * adds Phidget remote support (eg. via SBC)
   * adds Arduino TC4 PID support
 * Changes
   * increased Arduino TC4 default serial baud rate from 19200 to 115200 to match the TC4 Firmware aArtisan v3.00
   * saves autosave path and Volume/Weight/Density units to app settings
   * roast profile data table and events value display respect decimal places settings
   * improved extra device handling on profile loading
   * simplified statistics line
   * updates libraries (Qt, PyQt, numpy, scipy)
   * do not load alarms from background profiles
 * Bug Fixes
   * fixes keyboard mode on reset
   * fixes multiple event button action
   * fixes mixup of alarm table introduced in 0.7.5


----
v0.7.5 (06.04.2014)
-------------------

 * New Features
   * adds Phidgets 1048 probe type configuration
   * adds event quantifiers
   * adds CM correlation measure between fore- and background profile to statistics bar
   * adds symbolic variables for background temperatures for symbolic assignments
   * adds xy scale toggle via key d
   * adds modbus temperature mode per channel
   * adds Modbus/Fuji merger
 * Changes
   * increased resolution of temperatures in profiles to two digits
   * updated Modbus lib (slightly faster)
 * Bug Fixes
   * improved serial communication
   * fixed extra event manual entry to allow digits
   * adds security patch
   * fixed background profile color selection
   * font fix for OS X 10.9


----
v0.7.4 (13.01.2014)
-------------------

 * Bug Fixes
   * fixes ETBT swap functionality


----
v0.7.3 (12.01.2014)
-------------------

 * New Features
   * adds oversampling
   * adds support for floats to the Modbus write command
 * Changes
   * improved curve and RoR smoothing
   * improved autoCharge/autoDrop recognizer
   * updated Phidget library


----
v0.7.2 (19.12.2013)
-------------------

 * Changes
   * beep after an alarm trigger if sound is on and beep flag is set
   * autosave with empty prefix takes roast name as prefix if available
   * external program path added to program settings
 * Bug Fixes
   * fixed always active min/max filter
   * spike filter improvements
   * fixes time axis labels on CHARGE
   * fixed alarm trigger for button 1
   * improved autoCHARGE and autoDROP recognizers
   * fixes minieditor event type handling
   * fixes and improvements to [RoastLogger](http://homepage.ntlworld.com/green_bean/coffee/roastlogger/roastlogger.htm) import
   * makes the extra serial ports widget editable


----
v0.7.1 (02.12.2013)
-------------------

 * Bug Fixes
   * fixes lockup on extra device use
   * fixes redraw artifact on axis changes
   * fixes minieditor navigation
   * fixes early autoDRY and autoFCs
   * fixes extra lines drawing


----
v0.7.0 (30.11.2013)
-------------------

 * New Features
   * adds support for the [Phidget 1046 4-Input PT100/RTD  Bridge](http://www.phidgets.com/products.php?product_id=1046_0) and for the [Phidget 1048 4-Input Temperature Sensor J/K/E/T-Type](http://www.phidgets.com/products.php?product_id=1048) devices
   * adds TP event marks (show on graph and in the message log)
   * adds flag in events dialog to control the display of the TP mark
   * adds autoDRY and autoFCs to phases dialog
   * adds phase LCDs (TP, DRY, FCs) estimating time to the event and counting time after the event
   * adds flag in phases dialog to deactivate phases LCDs
   * keeps a link to the loaded background file on saving a profile and automatically re-loads the background with the actual profile
   * adds a new graph style using xkcd, path effects and the Humor or Comic font
   * alarms
     * option load/save alarms along (background-) profiles
     * adds negative alarm guards "But not"
     * adds insert alarm button
     * adds new alarm actions to trigger default event actions like START, FCs,..
     * triggered alarms hold a gray background in the alarms dialog
     * imports alarms from [RoastLogger](http://homepage.ntlworld.com/green_bean/coffee/roastlogger/roastlogger.htm) profiles (thanks to Miroslav)
   * allows ETBTa and RoR statistics to be displayed together
   * adds support for the [Tonino roast color meter](http://my-tonino.com)
   * the last used extra event button is marked
   * adds extra device data to Roast Properties data table
   * adds "cool end" event to the event popup menu on right mouse click on the BT
   * adds "Fuji SV" as second channel to the +Fuji DUTY %
   * adds load/save and read/write all actions to Fuji control
   * adds keyboard control for sliders
   * adds an option to remove digits from temperature LCDs (extras dialog)
   * adds Hebrew localization
 * Changes
   * curve smoothing settings sensitivity has been doubled (for some internal reasons). So a value of 6 on Artisan v0.6 should be adjusted to 3 to have roughly the same effect.
   * autosave now takes the roast name from the roast properties and autosaves on OFF. Further, the date is now written as prefix
   * preserves autosave ON/OFF state over app restarts
   * x/y mouse pointer coordinate display now always displays temperatures and not temperature deltas if the RoR axis is active
   * reorganized tabs in Extras dialog
   * removes axis labels during recording
   * alarms guarded by TP event are now active beyond the DRY event
   * removed scan for ports button
   * legend only shows extra event types that are in use
   * alarm dialog edits directly the active alarm table with the consequence that alarms are not retriggered if
   * alarms are edited during roasting
   * right axis removed if DeltaET/BT is not active
   * extra courve LCDs are now of the same size as the ET/BT LCDs
   * updated underlying libs (Python, Qt, matplotlib)
 * Bug Fixes
   * fixes issues with the "Drop Spikes" filter
   * fixes "import profile into designer" action
   * fixes default directory in wheelgraph open file dialog
   * various fixes to the rendering of background profile annotations
   * fixes an issue that allowed alarms to be trigger several times
   * Windows font fixes
   * fixed events-by value redraw if minieditor is open
   * fixed a conflict between manual device ENTER key action and manual temperature input dialog
   * improved reliability of serial and modbus commands
   * fixes issue with Roast Reports on Windows
   * several fixes to alarm system
   * fixes the [ RoastLogger](http://homepage.ntlworld.com/green_bean/coffee/roastlogger/roastlogger.htm) import of latin1 encoded files
   * PID LCD visibility
   * scan for ports on Linux
   * better error handling on exporting data
   * improved sample time accuracy
   * fixes wrong segment 4 soak time reported by "Read RS values"
   * updates translations (JP, NL)


----
v0.6.0 (14.6.2013)
------------------

 * Events
   * adds COOL event recording the time the beans were cooled down
   * adds event sliders e.g. to control the Hottop heater and fan via the HT Roaster Interface
   * adds substitution of '{}' in event button/slider actions by button value
   * adds Modbus and DTA send command support attached to button events
   * adds ordering of events in events tab of Roast Properties dialog
   * event value range extended from [0-10] to [0-100]
   * allows events like FCs, FCe,.. (but for CHARGE) to be removed by inserting 0:00 as event time
 * Alarms
   * adds alarm chains via alarms guarded by other alarms added
   * adds alarms on all logged temperature curves incl. deltaET/deltaBT
   * adds alarms on rising and falling temperatures
   * adds SC_END, COOL and TP to the FROM list of alarms
   * adds an empty alarm action (None)
   * adds emtpty alarm from-time (START)
   * adds COOL event trigger as special case (via button #0)
   * adds slider change actions
   * adds time-based alarms triggered at the given seconds after the specified event like TP, FCs,..
   * adds save/load action to alarm table
 * Curves
   * adds ET/BT swap configuration
   * adds ambient temperature routing added
   * adds background deltaET/deltaBT
   * adds spike filter and smoothing
   * adds smoothing of all curves incl. background on load/redraw (not only DeltaET/DeltaBT)
   * improved and faster DeltaET/BT smoothing (via numpy)
   * adds customization of line and marker styles via the Figure Options menu (green flag button)
 * Supported Devices
   * adds 4 channel MODBUS RTU device support
   * adds improved Delta DTA/DTB support
   * adds support for digital scales from KERN
   * adds support for Amprobe TMD-56
 * UI
   * improved main window widget layout
   * improved dialog layouts
   * adds colorized LCDs using curve color
   * forces even x-axis ticks
   * adds dpi resolution and appearance application settings
   * adds full-screen support
   * adds new and improved localizations (Arabic, German, Greek, Spanish, French, Japanese, Norwegian, Portuguese, Turkish, Dutch, and Italian)
   * adds monitoring-only mode reporting readings on LCDs without recording. To start recording press START
   * adds customization of visibility of LCDs, curves, and default event buttons
   * improved label positioning on graphs
   * improved HTML Report (now called Roast Report)
   * adds automatic table columns resize to content and to dialog size
   * adds long cool phase warning (red time LCD)
   * adds BTETarea statistics per phase
   * adds user-definable default button actions
   * adds customization of default button visibility
   * adds optional hiding of ET/BT curves and ET/BT/DeltaET/BT LCDs
   * adds line- and marker styles set via the "GreenFlag" menu to application settings
   * fixed figure options dialog (green flag menu)
   * adds right-click popup on BT curve to change event time
 * File Handling
   * changed default directory on Mac from ~/Library to ~/Documents
   * changed file extension of profiles from .txt to .alog
   * adds load-by-double-click (Mac OS X only)
   * adds JSON import/export
   * adds RoastLogger import/export
   * adds PDF/SVG vector graph export
 * Packaging
   * removes support for PPC processors on the OS X platform
   * adds Linux binary builds (32bit and 64bit)
   * adds Windows installer
   * adds new app and file icons
   * upgrades underlying libs (Python, Qt, PyQt, numpy, scipy, matplotlib)
 * Others
   * adds Python 3 support
   * adds auto align background on CHARGE/autoCharge
   * improved localization support and unicode character handling
   * adds a CUSTOM cup profile that is stored in the application settings
   * adds computation of the area between the BT and ET curves (ETBTa)
   * adds extended roast characteristics/statistics (incl. ET/BT area abbreviated as ETBTa)
   * adds roast color and flags to specify roast defects
   * adds polyfits
   * bug fixes

----
v0.5.6 (8.11.2012)
------------------

 * based on r787 (with modbus support removed)
 * added support for Voltcraft K201 and fixed CENTER 301
 * bug fixes

**Note**
_This is the latest version supporting Mac OS X 10.4 and 10.5 (on Intel and PCC)_

----
v0.5.5 (28.9.2011)
------------------

 * fixes ArdruinoTC4 extra devices
 * fixed autoDrop recognition
 * fixes serial settings for extra devices

----
v0.5.4 (28.8.2011)
------------------

 * adds events by value
 * adds custom event button palettes
 * adds virtual device from plot
 * adds K204 CSV import
 * improves Designer
 * improves Statistics
 * improves Help dialogs
 * improves relative times
 * bug fixes

----
v0.5.3 (30.7.2011)
------------------
 * improves performance of push buttons
 * adds device external-program
 * adds trouble shooting serial log
 * fixes Linux Ubuntu and other bugs

----
v0.5.2 (23.7.2011)
------------------

 * added Delta DTA PID support
 * added automatic CHARGE/DROP event detection
 * added separate RoR axis
 * added cross lines locator
 * smaller Mac OS builds with faster startup
 * optimized legend and statistics layout
 * improved Wheel Graph editor
 * performance improvements
 * bug fixes

----
v0.5.1 (18.6.2011)
------------------

 * bug fixes

----
v0.5.0 (10.6.2011)
------------------

 * support for Mac OS X 10.4 and PPC added
 * added more translations
 * added wheel graph editor
 * added custom event-control buttons
 * added Omega HHM28 multimeter device support
 * added support for devices with 4 thermocouples
 * added PID duty cycle
 * added math plotter in Extras
 * added run-time multiple device compatibility and symbolic expressions support
 * improved configuration of Axes
 * improved configuration of PID
 * improved Arduino code/configuration
 * improved cupping graphs
 * improved performance/responsiveness in multi-core CPUs
 * bug fixes

----
v0.5.0b2 (04.6.2011)
--------------------

 * improved cupping graphs
 * improved performance in multi-core CPUs
 * bug fixes

----
v0.5.0b1 (28.5.2011)
--------------------

 * support for Mac OS X 10.4 and PPC added
 * added more translations
 * added wheel graph editor
 * added custom event-control buttons
 * added Omega HHM28 multimeter device support
 * added support for devices with 4 thermocouples
 * added PID duty cycle
 * added math plotter in Extras
 * added run-time multiple device compatibility and symbolic expressions support
 * improved configuration of Axes
 * improved configuration of PID
 * improved Arduino code
 * bug fixes

----
v0.4.1 (13.4.2011)
------------------

 * import of CSV is not limited anymore to filenames with "csv" extension
 * improved VA18B support
 * Windows binary includes the language translations that were missing in v0.4.0

----
v0.4.0 (10.4.2011)
------------------

 * improved CSV import/export
 * K202 CSV support added
 * adds localization support
 * adds german, french, spanish, swedish, italian menu translations
 * fixed cut-copy-paste on Mac and added cut-copy-paste menu
 * LCD color configuration
 * replay of events via background dialog
 * relative times are used everywhere
 * adds profile designer
 * adds alarms
 * more robust Arduino/TC4 communication
 * bug fixes

----
v0.3.4 (28.02.2011)
-------------------

 * adds Arduino/TC4 device support
 * adds TE VA18b device support
 * improved Fuji PXR/PXG support
 * support for file paths with accent characters
 * main window layout improvements
 * improved events visualization and capacity
 * improved roasting properties dialog
 * statistic characteristic line as y-label to ensure visibility if axis limits are changed
 * duplicate recent file names show containing directory
 * remembers user selected profile path
 * added DeltaET/DeltaBT filter to make those delta curves more useful
 * adds volume and bean probe density
 * adds new command to start/restart roasts
 * bug fixes

----
v0.3.3 (13.02.2011)
-------------------

 * fixed typo in htmlReport
 * fixed phases automatic adjusting mechanism
 * serial communication improvements
 * added support for Fuji PXR5/PXG5
 * added NONE device
 * added keyboard shortcuts for events and sound feedback
 * initial Linux binary release
 * added axis settings to application preferences

----
v0.3.2 (31.01.2011)
-------------------

 * fixed Center 309 communication
 * fixed serial device scan on Linux
 * added support for Omega HH309
 * added open recent, save and (CSV) export menus
 * added DRY END Button
 * added sync of mid phase with the DRY END and FCs events
 * added custom event types
 * added events type mini editor widget
 * added math tab in extras dialog
 * added ambient temperature to roast properties
 * extended projection mode
 * updated several software components
 * improved statistic bar positioning
 * new mailing lists for users and developers established

----
v0.3.1 (12.01.2011)
-------------------

 * fixed issue on loading the user's application preferences

----
v0.3.0 (11.01.2011)
-------------------

 * fixed occasional ET/BT swap
 * fixed issues wrt. accent characters
 * added OS X 10.5.x support for Intel-only
 * new file format to store profiles
 * added configurable min/max values for x/y axis
 * added alignment of background profile wrt. CHARGE during roast
 * added DeltaBT/DeltaET flags
 * added "green Flag" button on Windows
 * reorganized dialogs and menus
 * added new HUD mode
 * smaller changes and additions

----
v0.2.1 (02.01.2011)
-------------------

 * bug fixes

----
v0.2.0 (31.12.2010)
-------------------

 * added support for
  * CENTER 300, 301, 302, 303, 304, 305, 306
  * VOLTCRAFT K202, K204, 300K, 302KJ
  * EXTECH 421509
 * bug fixes

----
v0.1.0 (20.12.2010)
-------------------
 * Initial release
====