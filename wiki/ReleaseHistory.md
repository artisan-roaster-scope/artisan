Detailed Release History
========================
----
v2.10.2 (XX, 2024)
------------------

* ADDITIONS
  - adds sensitive variants to autoCHARGE and autoDROP detection algorithms
* NEW HARDWARE SUPPORT
  - adds machine setups for various machines from Mill City Roasters
* CHANGES
  - upgrades to Qt/PyQt 6.6.1, pymodbus 3.6.2
* FIXES
  - fixes axis limits on starting the designer from a profile with time axis locked ([Discussion #1325](../../../discussions/1325))
  - fixes regresion that kept log dialogs (serial, message, error) empty ([Issue #1393](../../../issues/1393))
  - fixes regression which broke loading of certain MODBUS configurations correctly (eg. Loring)
  - fixes issue with MODBUS UDP communication that caused unnecessary retries and could break control of some Probat machines
  - fixes regression which broke the DROP alarm action
  - fixes regression which broke the PDF export on Linux
  - fixes regression which broke the transposer calculations
  - fixes regression which broke the simulator for profiles with extra device curves
  - fixes regression which broke the CHARGE timer ([Discussion #1358](../../../discussions/1358))
  - fixes regression which failed to time align profiles on load ([Discussion #1366](../../../discussions/1366))
  - fixes regression that caused IO Phidgets with channels in async mode to detach on ON ([Discussion #1394](../../../discussions/1394))
  - fixes regression which could lead to user customized event type names not being properly persisted in the application settings ([Issue #572](../../../issues/572))
  - fixes broken computation of the event slider calculators
  - fixes arabic reshaping and applies it also to Farsi
  - fixes long standing issue where the Designer looses one sample on each round-trip (thanks [/Terracotta-6](https://github.com/Terracotta-6) for reporting)
  - fixes CSV export ([Discussion #1357](../../../discussions/1357))
* REMOVALS


----
v2.10.0 (November 28, 2023)
------------------

* NEW FEATURES
  - adds equal and not equal temperature conditions to alarm rules
  - adds extra device curves to Comparator
  - adds new font graph font options [Comic Neue](http://comicneue.com/) (a redesigned Comic Sans) and [xkcd Script](https://github.com/ipython/xkcd-font/) (a more complete version of Humor)
  - adds alternative slider layout (controlled by the menu `Config >> Events`, Slider tab `Alternative Layout` flag)
  - adds optional alternative weight units in [artisan.plus](https://artisan.plus/) stock menus activated by holding the ALT (Windows) or OPTION (macOS) key
  - adds flags to control ET and BT projection lines separately
  - adds actions to clicks on large LCDs to set tare and to show/hide curves
  - adds additional translatable button labels (`\i`: STIRRER, `\f`: FILL, `\r`: RELEASE)
  - adds support for event name substitution in ET, BT channel names
  - adds `Artisan Command` `visible(i,b)` to change visibility of button `i` to `b` which has to be an expression which evaluates to a boolean, like 0, 1, false, true, ... ([Issue #1301](../../../issues/1301))
  - adds flag `Interpolate Drops` in `Config >> Curves`, tab `Filter` to disable data interpolation

* NEW HARDWARE SUPPORT
  - adds support for macOS 14 Sonoma and native support for Apple Silicon ([Issue #1221](../../../issues/1221))
  - adds back Raspberry Pi OS build (64bit Bookworm)
  - adds support for [Bühler Roastmaster](https://www.buhlergroup.com/global/de/products/roastmaster_coffeeroaster.html) RM20 Playone as well as RM60, RM120 and RM240
  - adds support for [Joper](https://joper-roasters.com/) PLC-based machines
  - adds support for [Cogen](https://cogen-company.com/) machines
  - adds support for [Typhoon](https://typhoon.coffee/) Hybrid roasters
  - adds support for additional [Carmomaq](https://carmomaq.com.br/) machine ([PR #1233](../../../pull/1233))
  - adds support for the [Phidget DAQ1000](https://phidgets.com/?prodid=622) 8x Voltage Input module ([Issue #1225](../../../issues/1225)), [DAQ1200](https://phidgets.com/?prodid=623) 4x Digital Input module, [DAQ1300](https://phidgets.com/?prodid=624) 4x Isolated Digital Input, [DAQ1301](https://phidgets.com/?prodid=625) 16x Isolated Digital Input ([Discussion #1139](../../../discussions/1139))
  - adds two more MODBUS channels (now 10 in total)
  - adds two more S7 channels (now 12 in total)
  - adds Hottop device logging ([Issue #1257](../../../issues/1257))

* CHANGES
  - minimum macOS version support pushed to Monterey (macOS 12)
  - all enabled alarms with fulfilled preconditions will be fired within a sampling interval instead of just one as in all versions before
  - updates background smoothing during recording to align 1:1 with the foreground ([Issue #1279](../../../issues/1279))
  - Smooth Spikes now always disabled during recording
  - if background is explicitly hidden, this state is preserved on loading a new profile with background
  - updates default serial speed for Kaleido Legacy from 9600 to 57600 baud
  - allow to call buttons with Multiple-Event actions from Multiple-Event actions, caution! allows for generating infinite call loops
  - enable the import of IKAWA profiles from URLs on platforms without Bluetooth BLE support
  - roasting and cupping notes are always deleted on RESET even if `delete Roast Properties on RESET` is not ticked
  - use default spawn instead fork multiprocessing also on macOS and replaced troublesome multiprocessing for Hottop and WebLCDs communication by asyncio
  - internal improvements leading to faster app start and exit as well as faster start of WebLCDs and more stable communication with Hottop roasters. As a consequence of this re-implementation, CONTROL can only be started after a connection to the Hottop via the button ON has been initialized.
  - upgrades dependencies (PyQt 6.6, matplotlib 3.8, pymodbus 3.5)
  - adds Idempotency-Key header to [artisan.plus](https://artisan.plus/) POST requests

* FIXES
  - improve autoDROP accuracy for most setups ([Issue #1232](../../../issues/1232))
  - corrects evaluation of `b{event}`
  - ensures that extra LCD, button and slider names are correctly updated if event names are changed on profile load and reset
  - ensure that after a factory reset the roast position counter starts at 1
  - fixes potential failure to detach Phidget RC channels
  - fixes event name rendering problem by adding missing background event name decoding ([Issue #1216](../../../issues/1216))
  - fixes typos in some CTE and Hottop machine setups
  - fixes item color handling in Comparator
  - fixes Japanese translation errors ([Issue #1256](../../../issues/1256))
  - fixes many Brazilian portuguese translation errors ([PR #1294](../../../pull/1294) & [PR #1297](../../../pull/1297)). Many thanks to your hugh contribution Max Oliver!
  - fixes German translation error ([Issue #1270](../../../issues/1270))
  - prevents stacking graph updates which can lead to high memory consumption during recording on slow machines
  - fixes regression which broke WebLCDs on Windows and Linux in Artisan v2.8.4 ([Issue #1229](../../../issues/1229))
  - fixes regression which broke S7 communnication on Linux builds in v2.8.4
  - fixes regression which broke even action Artisan Command `loadBackground` in v2.8.4 by substituting the underline symbol ([Issue #1288](../../../issues/1288))
  - fixes language selection for ArtisanViewer
  - fixes wrong message on toggling the `Beep` flag of the UI tab ([Issue #1283](../../../issues/1283))
  - fixes missing event annotations in Hebrew ([Issue #1323](../../../issues/1323))


----
v2.8.4 (June 21, 2023)
------------------


* ADDITIONS
  - adds official support for [Kaleido]([https://www.kaleido-roaster.com/](https://artisan-scope.org/machines/kaleido/)) Network, Serial and Legacy protocols
  - adds experimental support for [IKAWA HOME/PRO]([https://www.ikawacoffee.com/](https://artisan-scope.org/machines/ikawa/))
  - adds [Santoker Q Series and R Series](https://artisan-scope.org/machines/santoker/) support over serial (USB/Bluetooth)
  - adds IKAWA URL import
  - adds support for [Phidget TMP1200_1](https://phidgets.com/?view=search&q=TMP1200)
  - adds keyboard shortcuts CTRL+ENTER (on macOS COMMAND+ENTER) to start recording and SHIFT+ENTER to stop logging
  - adds slider and quantifier step size 5
  - adds `Create Events` flag to Software PID
  - adds energy/CO2 data to characteristics line
  - display configured roaster name and batch size as x-axis label if no profile is loaded
  - toggle hide-background per double-click on background profile name (subtitle) during roasting
  - adds dark mode support for Windows 10 (1607+), Windows 11 and Linux under Gnome (not available with UI style WindowsVista, best with Fusion)
  - adds configuration `Mark last pressed` to event button configuration to control if the last button pressed should be marked (default) or not
  - adds configuration "Tooltips" to toggle visibility of custom event buttons tooltips (default off)
  - adds symbolic variables `WEIGHTin`, `MOISTUREin` and `TEMPunit` to access corresponding Roast Properties
  - adds fields `~dryphasedeltatemp`, `~midphasedeltatemp`, `~finishphasedeltatemp`, `~fcstime`, and `~fcstime_long` to autosave
  - adds translated and state aware custom event button label tags
  - adds button action symbolic variable $ bound to button state
  - adds additional Artisan Command, IO Command, MODBUS Command, S7 Command, WebSocket Command button actions to set button states
  - adds Artisan Command pidSVC(<n>) allowing to specify the SV in C which gets correctly converted to F in Fahrenheit mode

* CHANGES
  - places event annotations on ET if BT is hidden
  - uses `Fusion` as default style on Windows
  - improved drag-and-drop action in custom event button table (hold ALT (Windows) or OPTION (macOS) key to swap instead of move)
  - makes title widgets autocompletion case sensitive in Roast Properties dialog
  - improves CMS drum and air remove slider precision
  - disconnect HOTTOP serial connection on changing serial port settings such that the changes can have an effect on reconnecting
  - detects and adjusts to OS screen setup changes
  - joins Phidget APIs such that PWM Command out() and IO Command set() commands can both be used on one attached module
  - updated machine setups (Besca automatic and full automatic, Giesen, Hottop KN-8828B-2K+, Kuban Supreme Automatic, NOR A Series, Probat P Series III, Twino Ozstar) to take advantage of button label translations
  - adds roaster batch size defaults for machine setups
  - if different from the system default, use current serial port or current IP host as default on running a machine setup
  - extended localizations
  - pushes default max temperature axis limit to 275C / 527F (was 250C / 500F)
  - upgrade to [pymodbus 3.3](https://github.com/pymodbus-dev/pymodbus), [Qt/PyQt 6.5](https://riverbankcomputing.com/software/pyqt/intro), [matplotlib 3.7](https://github.com/matplotlib/matplotlib)

* FIXES
  - fixes regression which broke MODBUS port scan ([Issue #1056](../../../issues/1056))
  - makes designer respect the auto DeltaET and DeltaBT axis ([Issue #1062](../../../issues/1062))
  - don't deactivate auto DeltaET/DeltaBT axis without changing the delta max limit ([Issue #1062](../../../issues/1062))
  - fixes regression which broke channel tare function ([Issue #1063](../../../issues/1063))
  - fixes Aillio R1: unable to detach kernel driver ([Issue #1065](../../../issues/1065))
  - fixes pdf export unnecessary title abbreviation ([Issue #1077](../../../issues/1077))
  - removes extra trailing newline from environment variables on calling scripts ([Issue #1092](../../../issues/1092))
  - fixes startup issue under Linux Wayland ([Issue #1001](../../../issues/1001))
  - fixes Arduino/TC4 PID source channel configuration in PID dialog ([Issue #1101](../../../issues/1101) & [Issue #1110](../../../issues/1110))
  - fixes a rare redraw issue caused by setting linewidth of extra lines to 0 ([Issue #1121](../../../issues/1121))
  - indicate slider focus also at 100% ([Issue #1126](../../../issues/1126))
  - fixes IO Command support for Phidget REL1101 ([Issue #1141](../../../issues/1141))
  - fixes MODBUS ASCII & BINARY communication and improves Arduino MODBUS RTU compatibility ([Issue #1145](../../../issues/1145))
  - fixes issues with the Designer config table ([Issue #1173](../../../issues/1173))
  - fixes Santoker Series Fahrenheit mode
  - fixes Santoker Series machine setup quantifiers to use SV mode
  - fixes missed picks in designer
  - fixes desktop screenshot for Qt6
  - fixes the +/- keyboard shortcuts for zooming to work across all keyboard layouts
  - fixes Probatone control token release under "Keep ON"
  - fixes regression which allowed to define custom blends with total ratio larger than 100%
  - fixes an issue sending multiple S7 commands via buttons as used in the Probat UG setups which could lead to a crash
  - ensures that rendering of axis respects curve style setting
  - persist ET marker size changes correctly
  - fixes of issues revealed by automatic static analyzers ([pylint](https://github.com/pylint-dev/pylint), [ruff](https://github.com/charliermarsh/ruff), [mypy](https://github.com/python/mypy), [pyright](https://github.com/microsoft/pyright))
  - fixes a regression where events generated on CHARGE could be rendered at wrong positions

* REMOVALS
  - removes support for original *.txt profile format of Artisan v0.4.0 (2011) and earlier
  - Aillio imports until a proper export is provided


----
v2.8.2 (December 21, 2022)
------------------

* NEW FEATURES
  - adds [Sivetz fluid bed roasting machines](https://artisan-scope.org/machines/sivetz/) support
  - adds [Santoker Q Series and R Series](https://artisan-scope.org/machines/santoker/) support ([Discussion #1019](../../../discussions/1019))
  - adds support for the [Yocto Watt module](https://artisan-scope.org/devices/yoctopuce/#Yocto-Watt) ([Discussion #955](../../../discussions/955)) and for [generic Yoctopuce sensors](https://artisan-scope.org/devices/yoctopuce/#Yocto-Sensor)
  - adds [Phidget DAQ1500](https://artisan-scope.org/devices/phidgets/#DAQ1500) support
  - adds Artisan Command `keepON(<bool>)`
  - adds MODBUS Commands `readBCD`, `read32`, `read32Signed`, `read32BCD`, and `readFloat`
  - adds extra device channels as PID sources to the Artisan internal software PID ([Discussion #998](../../../discussions/998))
  - adds flags to activated/deactivate background shifting via cursor keys and slider control via up/down keys ([Discussion #1026](../../../discussions/1026))
  - adds factory reset by pressing ALT/OPTION modifier on startup and skips saving app settings if ALT/OPTION is held on application exit
  - save generating Artisan version/revision/build numbers to '.alog' Artisan profiles
* CHANGES
  - better designer
  - corrects and improves autoCHARGE/autoDROP
  - improved MODBUS error handling and reconnect
  - interprets index access of symbolic variables RB1, RB2, B1, B2,.. w.r.t. foreground time respecting background alignment ([Issue #996](../../../issues/996))
  - keep updating software pid loop running while PID is OFF if software PID is configured
  - improved performance on 0.25sec sampling rate
  - test availability of given S7 port before trying to connect to avoid hangs
  - allow to use the batch prefix with deactivated batch counter supporting manual batch numbers in any format
  - updates keep-alive ping frequency on Probat setups
  - disables Phidget server password field if no host is given and thus mDNS/ZeroConf server discovery is active
  - coarse sliders move only with step size 10
  - restore profiles in graph after web ranking report
  - direct root logging to artisan log file
  - MODBUS lib internal debug messages are logged if debug logging mode is active and device logging is enabled (logging flag in device dialog)
  - synchronizes `Curves >> UI` tabs notification flag and Artisan Command notifications
  - upgrade to Python 3.11, pymodbus v3, Qt/PyQt 6.4.1, matplotlib 3.6.2
* FIXES
  - fixes symbolic variable RB1/RB2 index access ([Issue #996](../../../issues/996))
  - fixes S7 and MODBUS read commands which may fail due to cache misses breaking control on some machines like Probatone ([Issue #1002](../../../issues/1002))
  - fixes crash on pidOn/pidOff Artisan Commands ([Issue #1005](../../../issues/1005))
  - fixes saveGraph as PDF regression on Windows ([Issue #1011](../../../issues/1011))
  - fixes prevent low DPI settings that could trigger a crash on redrawing the canvas ([Issue #1024](../../../issues/1024))
  - fixes event step line extension to CHARGE in case event snap, 100%-step and showFull were disabled and implemented the mechanism also for the background profile
  - fixes the navigation history on reset and on changing axis settings
  - fixes Yocto-4-20mA-Rx device input
  - fixes Artisan Command `pidSource(<int>)`
  - fixes Phidget 1046 configuration
  - fixes regression which blocked background left/right shifts if keyboard moves was active
  - fixes regression which crashed the Fuji PXR PID dialog ([Issue #1054](../../../issues/1054))
* REMOVALS
   - drops builds for RPi Buster


----
v2.8.0 (October 21, 2022)
------------------

* NEW FEATURES
  - adds Comparator phases widget ([Issue #479](../../../issues/479))
  - adds auto time axis modes (Roast, BBP+Roast, BBP) toggle as popup in Axis and Comparator dialogs and via shortcut key G
  - adds support for [Besca](https://artisan-scope.org/machines/besca/) BEE v2 (2022 model), [Besca](https://artisan-scope.org/machines/besca/) BSC full-automatic, [Titanium Roasters](https://artisan-scope.org/machines/titanium/) and [Coffee Machines Sale](https://artisan-scope.org/machines/cms/) roasting machines
  - adds support for [San Franciscan](https://artisan-scope.org/machines/sf/) 2022 Eurotherm variant and [Diedrich DR](https://artisan-scope.org/machines/diedrich/)
  - adds support for the [Plugin Roast 2.0 module](https://www.pluginroast.com.br/)
  - adds back support for [Typhoon roasters](https://artisan-scope.org/machines/typhoon/) ([Issue #959](../../../issues/959))
  - adds energy defaults for [Probat](https://artisan-scope.org/machines/probat/) P01E
  - adds Loring CSV importer ([Issue #902](../../../issues/902))
  - adds individual control on the event types participating in playback aid and event playback
  - adds mm:ss time formats for special events annotations ([Issue #864](../../../issues/864))
  - adds additional keyboard shortcuts documentation under `Help >> Keyboard Shortcuts`
  - adds MODBUS IP timeout and retry parameters ([Issue #892](../../../issues/892))
  - adds MODBUS Serial delay and retry parameters
  - adds Modbus Command "writeLong" to send a 32bit integer to the connected MODBUS device
  - adds shortcut COMMAND/CTRL +/- to inc/dec graph resolution
  - adds minimal median filter to RoR computation during roasting if Smooth Spikes is enabled
  - adds RoRoR to mouse cross
  - adds file not found message to Artisan Command loadBackground
  - adds OPTION+B [Mac] / CTRL-SHIFT+B [Win] keyboard shortcut followed by two digits to fire corresponding custom event button action
* CHANGES
  - autoDROP on OFF only if CHARGE is set before
  - ArtisanViewer logs to separate file
  - ArtisanViewer submits changes to [artisan.plus](https://artisan.plus)
  - send roast templates temperature, pressure, humidity along every roast record to [artisan.plus](https://artisan.plus)
  - support unicode characters in filenames ([Issue #869](../../../issues/869))
  - CONTROL button rendered in red if PID is active
  - sets default batch size from nominal batch size
  - do not send the SV on PID start if in Ramp/Soak mode ([Issue #910](../../../issues/910))
  - updated WCRC cup profile scheme
  - remember last batch size even if "Delete roast properties on RESET" is ticked and initialize it by the machines nominal batch size as set on setup
  - hides axis spines and labels along axis ticks if axis step width is set to 0 (or the empty entry)
  - settings in the axis dialog are applied immediately
  - reduced curve smoothing and limits its range to 0-5 ([Issue #907](../../../issues/907))
  - hides COOL END button by default
  - Português do Brasil translation updates supported by the people behind the [Plugin Roast module](https://www.pluginroast.com.br/)
  - updated Chinese Traditional translations (by Yeh Cavix)
  - updated Vietnamese translations
  - updates Qt/PyQt to v6.4.0 and Matplotlib to v3.6.1
  - display 4 digits AUC ([Issue #977](../../../issues/977))
* FIXES
  - fixes regression in 2.6.0 where symbolic formulas were not processed on software PID input ([Issue #847](../../../issues/847))
  - fixes regression in 2.6.0 where the integrate Yoctopuce driver could not be loaded on Windows (non-legacy build) ([Issue #873](../../../issues/873))
  - fixes regression in 2.6.0 where connections to Acaia scales on Windows 10 could fail
  - fixes regression in 2.6.0 where support for Japanese was broken
  - fixes LCD order if LCD / DeltaLCD swap is set differently in settings on settings load
  - fixes conversion of temperature difference in F to C for det/dbt (```CM_ETD/CM_BTD```)
  - fixes pdf filename cut-off on saving ([Issue #898](../../../issues/898))
  - fixes autoDROP lack of precision ([Issue #859](../../../issues/859))
  - fixes issue with Chinese characters in Analyzer results annotation boxes ([Issue #869](../../../issues/869))
  - fixes event picks in Comparator to respect visibility, selection and z-order
  - fixes copy roast data table
  - adds verification of MODBUS/S7 result length and improved handling of MODBUS/S7 communication errors ([Issue #883](../../../issues/883) and [Issue #912](../../../issues/912))
  - fixes TE-VA18B decoding ([Issue #882](../../../issues/882))
  - prevents a potential deadlock on RampSoak processing
  - updates playback mode indicator (color of background profile name as subtitle in the upper right corner) on Artisan Command playback mode
  - avoids sending -1 error temperatures to the [artisan.plus platform](https://artisan.plus)
  - avoids unproductive event quantification while OFF
  - don't replay background events after background profile DROP
  - ensures that relative event buttons work correctly after PID control is turned off
  - fixes a rounding issue of a RoR smoothing parameter that could lead to a small x-axis offset between background curve and recorded curve ([Issue #907](../../../issues/907))
  - correctly re-aligns background profile after producing a ranking report

----
v2.6.0 (March 11, 2022)
------------------

* NEW FEATURES
  - additional machine setups for [ARC 800/S RTD](https://artisan-scope.org/machines/arc/), [NOR roasting machines](https://artisan-scope.org/machines/nor/), [Kuban Supreme Manual](https://artisan-scope.org/machines/kuban/), [Caparaó Prime Line](https://artisan-scope.org/machines/caparao/), [Prometheus Ignis](https://artisan-scope.org/machines/prometheus/), [Yoshan EC-500](https://artisan-scope.org/machines/yoshan/) and [Atillia gold plus 2022](https://artisan-scope.org/machines/atilla/)
  - adds support for the [Phidget HUB0001](https://www.phidgets.com/?prodid=1202) and the Phidget HUB0000 firmware 307
  - adds support for [Phidget VCP100x](https://www.phidgets.com/?tier=3&catid=16&pcid=14&prodid=953) Voltage Input modules
  - adds support for the new generation [Acaia](https://acaia.co/) [Pearl-S](https://acaia.co/collections/coffee-scales/products/pearl-model-s)/[Pearl2021](https://acaia.co/collections/coffee-scales/products/pearl)/[Lunar2021](https://acaia.co/products/lunar_2021) bluetooth scales
  - adds MODBUS signed integer decoders (16 and 32bit)
  - adds BBP comparison to Comparator ([Issue #788](../../../issues/788))
  - adds profiles received via `artisan://` urls to comparator
  - extends drag-and-drop to canvas of Comparator to add multiple profiles
  - adds pause/restart to Simulator via a click to the timer LCD
  - allows to change simulator speed by selecting the menu entry while holding a modifier key (shift: 1x, alt: 2x, control: 4x) as well on restarting the simulator after pausing
  - adds indicator of simulator source file and simulation speed in main window title
  - adds automatic temperature conversion to simulator
  - adds CHARGE timer
  - adds quadratic BT/ET and RoR projections, active after 5min into the roast
  - adds possibility to show/hide curves by a click on the corresponding LCD
  - adds slider mapping calculator
  - adds large scale LCD window
  - adds cursor coordinate clamp modes toggled by key z
  - adds LCD cursor showing readings at cursor position of foreground or background profile while not recording, toggled by key u
  - adds shortcut key y to show/hide the minieditor on recording
  - adds shortcut to toggle Playback Events by hitting the j key; its state is now visually indicated by the background profile name color (red=active, blue=inactive)
  - adds shortcut to start recording from monitoring by hitting the SPACE bar
  - adds shortcut to stop recording by hitting the SPACE bar in keyboard mode if all main event buttons already have been activated
  - adds shortcuts CTR+ key i, o, p and l to Roast Properties dialog to send scale weight to weight input field, weight output field, reset the accumulated scale weight and to open the volume calculator
  - adds automatic mark DROP on OFF if at least 7min were recorded and either Auto DROP is active or DROP button is hidden
  - adds PDF as export format of roast, production and ranking reports
  - adds "PDF Report" as additional format to autosave ([Issue #478](../../../issues/478))
  - adds notifications incl. Artisan Commands `notify` and `notifications` with support for [artisan.plus](https://artisan.plus) reminders
  - improves fidelity of analyzer calculations when samples are missing and other circumstances
  - adds support for the [artisan.plus](https://artisan.plus) HOME quota system
  - adds custom blend editor for [artisan.plus](https://artisan.plus) ([Issue #760](../../../issues/760))
  - adds Artisan Command "keyboard" to enable/disable keyboard mode
  - adds Artisan Commands `showCurve`, `showExtraCurve`, `showEvents`, and `showBackgroundEvents` to show/hide curves and events
  - implements Artisan Commands `PIDon`, `PIDoff`, `PIDtoggle`, `pidmode` for Fujji PIDs
  - adds symbolic variables `aTMP`, `aHUM` and `aPRE` to hold the last ambient temperature, humidity and pressure readings ([Issue #786](../../../issues/786))
  - adds logging infrastructure
  - adds Ukrainian localization
* CHANGES
  - seamless loading of profiles recorded under a different device setup
  - faster startup
  - improved sampling loop resulting in higher sample time accuracy down to the nano second on some platforms
  - improved translations for traditional Chinese
  - allow autoCHARGE to trigger again after undo CHARGE action
  - adds CHARGE to right-mouse popup if no CHARGE is yet set
  - for event slider is representing temperatures (temp ticked) while event descriptions are deactivated, event annotations in combo mode are now prefixed by the temperature unit
  - marks events on CHARGE only if event value not yet set before ([Issue #695](../../../issues/695))
  - warmup software PID on ON to have it ready on activate avoiding any initial swing
  - sorted action lists in events dialog
  - improved rendering of cursor coordinates widget (allow to deactivate via key d)
  - have zoom follow respecting the cursor coordinates mode (temp vs RoR)
  - disables main event buttons if undo is not applicable
  - deactivate open/import/convert menu actions in simulator modus
  - Phidget driver no longer bundled with Linux and RPi builds ([Issue #812](../../../issues/812))
  - keep ambient phidgets attached until app termination to increase system stability
  - default sampling interval set to 2sec (from 3sec)
  - updated library infrastructure (Python, Qt, PyQt, matplotlib, ...)
  - enables drag-and-drop of background annotations
  - PhasesLCDs show time to FCs if DRY is not set after DRY target passed
* DELETIONS
  - removes oversampling
  - removes HUD
  - removes Newton projections
  - removes Probat middleware and MCR support
  - removes support for Trobrat and Typhoon machines
  - removes Russian localization
* FIXES
  - fixes positioning of combo event annotations if "Show Full" is deactivated
  - fixes Acia Pearl disconnects and speeds up BLE connects
  - fixes Yocoto 0-10V Rx, milliVolt Rx, Serial device selection
  - fixes background aid beep configuration
  - fixes plotter computing the datatable for timeshifts incorrectly ([Discussion #692](../../../discussions/692))
  - fixes IKAWA import (thanks Jaejun Kim for your support on this)
  - adds url-decode to `artisan://` url processing to prevent character encoding issues
  - fixes lockup of CHARGE if button is pressed quickly after starting a recording
  - fixes an issue that prevented slider offsets with decimals to be accepted
  - fixes IO COMMAND sleep ([Issue #726](../../../issues/726))
  - fixes Fuji `setONOFFstandby` and `setrampsoakmode` in "MODBUS port" mode
  - ensures that the save legend position is correctly reconstructed
  - fix scaling of printing for high-dpi screens
  - fixes inverted Artisan Commands pidON and pidOFF
  - fixes Fuji PID saving of Ramp/Soak settings ([Issue #777](../../../issues/777))
  - fixes print layout on macOS
  - fixes missing time axis labels in Comparator ([Discussion #788](../../../discussions/786))
  - corrects timer lcd update rate in simulation mode
  - fixes redraw issue on time axis extension
  - ensures that the New menu item is added after factory reset
  - fix regression, properly install the Yocotopuce driver on Linux (incl. RPi) builds ([Issue #815](../../../issues/815))
  - button event actions now respecting the event types Bernoulli settings as slider actions do
  - fixes temperature conversion for HB/Arc roasters
  - fixes "too many open file handles" errors on S7 communication under Windows ([Issue #816](../../../issues/816))
  - fixes ArtisanViewer file open action when Artisan is recording and a file link on Windows ([Discussion #828](../../../issues/828))

----
v2.4.6 (July 30, 2021)
------------------

* NEW FEATURES
  - adds [energy and CO2 calculator](https://artisan-roasterscope.blogspot.com/2021/07/tracking-energy-consumption-co2.html)
  - adds a flag "Show Full" to the Curve and Background dialog to control of foreground and background curves before CHARGE and after DROP (keyboard shortcuts `i` and `o`)
  - adds "Clear the background before loading a new profile" and "Always hide background when loading a profile" flags to the Background dialog
  - adds hiding of background profile by a click on its (sub-)title
  - adds Roast Properties setup tab which includes machines nominal batch size and heating type
  - adds graph image export optimized for Facebook and Instagram and improves overall quality of image exports
  - adds Vietnamese, Danish, Scottish, Lativian and Slovak translations
  - adds AppImage package for a simple installation option on Linux ([Issue #557](../../../issues/557))
  - adds [Kirsch & Mausser](https://www.kirschundmausser.de/) machine setup with control functionality
  - adds custom buttons to all [Giesen](https://www.giesencoffeeroasters.eu/) machine setups to control additional actors (intake, flavouring, discharge, cooling, stirrer) on W30/W45/W60 machines
  - adds [Giesen](https://www.giesencoffeeroasters.eu/) machine setup for machines with coarse burner control in 10% steps
  - adds [Coffee-Tech FZ94 EVO](https://www.coffee-tech.com/products/shop-roasters/fz94-evo/) machine setup incl. control of burner, airflow and drum speed
  - adds [Roastmax](http://www.roastmaxroasters.com.au/) machine setup
  - adds [Craftsmith](https://www.craftsmithroasters.com/) machine setup
  - adds [Carmomaq](https://www.carmomaq.com.br/) roasters machine setup incl. control of burner, airflow and drum speed
  - adds [Petroncini](https://www.petroncini.com/) Maestro i06 machine setup
  - adds import of [Petroncini](https://www.petroncini.com/) CSV files
  - adds command_utility to perform command line utility tasks (help and version for now) ([PR #542](../../../pull/542))
  - adds current time `~currtime` to the autosave fields
  - adds a check for running Artisan while installing on Windows
  - adds `ArtisanCommand`s `moveBackground` and `pidLookahead`
  - allow comments in button definitions, everything after '#' is ignored (as in alarm descriptions)
  - adds MODBUS command `writeSingle(s,r,v)` and `writeSingle([s,r,v],..,[s,r,v])` to write a single MODBUS 16bit integer register.
  - adds [Phidgets](https://www.phidgets.com/) `frequency(ch,v[,<sn>])` PWM Command to set the PWM frequency on supported modules like the OUT1100
  - adds IO Command `limit(c,v[,sn])` to set the current limit on a DCMotor [Phidgets](https://www.phidgets.com/) ([Issue #626](../../../issues/626))
  - adds device logging for [Phidgets](https://www.phidgets.com/)
  - adds support for the Yoctopuce modules [Yocto-0-10V-Rx](https://www.yoctopuce.com/EN/products/usb-electrical-sensors/yocto-0-10v-rx), [Yocto-milliVolt-Rx](https://www.yoctopuce.com/EN/products/usb-electrical-sensors/yocto-millivolt-rx) and [Yocto-Serial](https://www.yoctopuce.com/EN/products/usb-electrical-interfaces/yocto-serial)
  - adds `{BTB}` and `{ETB}` command substitution replacing those placeholders by the value of BT and ET of the background profile, if loaded, at the current time in Serial/CallProgram/MODBUS/S7/WebSocket command actions
  - adds options to let event quantifiers fire slider actions and to avoid the quantification block delay on observing SVs instead of PVs ([Issue #608](../../../issues/608))
  - adds `RoR@FC`, `roastersize`, and energy/CO2 data to plus roast record
  - adds importing of Artisan profiles from URL inputs and `artisan://profile?url=<url>` links
  - adds from support for `artisan://template?<UUID>` links to load background profiles identified by the given UUID
  - adds donation popup
  - adds release sponsor
* CHANGES
  - Spanish translations updated ([PR #543](../../../pull/543), [PR #553](../../../pull/553), [PR #554](../../../pull/554))
  - Chinese translations updated (thanks to Leo Huang)
  - most other translations updated and extended
  - updates some [Coffed](https://artisan-scope.org/machines/coffed/) machine setup
  - allows mini editor to show and change time before recording CHARGE
  - statistics bar always use DE event value if it is set, if no DE event exists use the phases table temp
  - allows for a y-axis step sizes below 10
  - a step size of 0 (or the empty step entry for the x-axis) removes the ticks on the corresponding axis
  - better handling of decimal number input in Roast Properties by automatic conversion of decimal separators
  - dynamically update recent roasts according to [artisan.plus](https://artisan.plus) stock blend replacement situations
  - when available use greens temp in linear regressions computed by the profile analyzer
  - slider actions do now bind floats to the placeholder `{}` instead of integers, also for S7 commands (in previous versions only for IO, VOUT and RC Commands)
  - replaces the AUC readings per phase in the statistic line by the temperature delta per phase
  - marks roasted properties that are likely wrong (larger yield than batch size)
  - removes PLC_stop command on S7 disconnect
  - set step size of up/down arrow key action on coarse event sliders to 10
  - increases p-i-d input control for the internal Software PID to 3 decimals ([Issue #618](../../../issues/618))
  - align to begin of background profile on START instead of its CHARGE event ([Issue #616](../../../issues/616))
  - energy result values added to ranking reports
  - Dry, Mid and Finish Phase values added to the Excel and CSV ranking reports
  - synchronizes the behavior of opening profiles per double-click on Linux to the one on macOS and Windows (see [Working Together – Artisan, ArtisanViewer and artisan.plus
  ](https://artisan-roasterscope.blogspot.com/2020/06/working-together-artisan-artisanviewer.html))
  - the currently displayed profile is reopened after loading a new settings file
* FIXES
  - fixes adjustSV for Fuji PXF PID ([Issue #547](../../../issues/547))
  - prevent the automatic delta axis mechanism to make adjustments on starting a new recording
  - always convert computed volume in/out and weight in/out when any value present
  - fixes timer LCD color during cooling
  - fixes serial port popup selection
  - fixes the transposers input fields not accepting any input (regression in v2.4.4)
  - fixes a typo in the Web ranking reports
  - updates max buttons per row spinner on activating a palette
  - fixes gap in RoR curves produced by set and unset DROP event
  - fixes a RoR unit conversion bug
  - ensures that slider title color gets correctly set on restart on macOS and Linux
  - ensure that that serial communication log is updated also in OFF mode
  - correctly open profiles with spaces in the file path per double-click under Linux
  - fixes an unhandled exception in the quantifiers dialog box ([Issue #607](../../../issues/607))

----
v2.4.4 (December 14, 2020)
------------------

* NEW FEATURES
  - adds machine setups for the PLC equipped machines from [Nordic](https://artisan-scope.org/machines/nordic/), [Fabrica Roasters](https://artisan-scope.org/machines/fabrica/) and [MCR Series in C](https://artisan-scope.org/machines/mcr/)
  - adds support for [Phidget HUM1001](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=1179)
  - adds [Rubasse](https://rubasseroasters.com/) importer
  - adds [Aillio](https://aillio.com/) RoastWorld importer
  - adds MODBUS BCD Integer reading
  - adds flag to toggle polyfit RoR calculation
  - adds PID Ramp/Soak pattern actions
  - adds 3 Ramp/Soak templates
  - adds option to load Ramp/Soak patterns from background profile
  - adds labeled alarm sets
  - adds labels to event palettes
  - adds Qt base translations for Turkish, Dutch and Brazilian
  - adds _fetch full blocks_ option to instruct the S7 and MODBUS optimizer fetch maximal register blocks from lowest to largest register number
  - adds Artisan Commands: `popup(m[,t])`, `message(s)`, `setCanvasColor(c)`, `resetCanvasColor`, `button(e)` with `e = { START, CHARGE, DRY, FCs, FCe, SCs, SCe, DROP, COOL, OFF }`, `p-i-d(p,i,d)`, `pidSV(v)`, `pidRS(rs)`, `pidSource(n)`, `palette(p)`, `loadBackground(<filepath>)`, `clearBackground`, `alarmset(as)`, `adjustSV(n)`
  - adds Dijkstra curve font
* CHANGES
  - updates [Trinitas T2 and T7](https://artisan-scope.org/machines/trinitas/), [Oztürk](https://artisan-scope.org/machines/ozturk/) and [Giesen](https://artisan-scope.org/machines/giesen/) machine setups
  - renames empty MODBUS decoder entry to Int
  - renames MODBUS IntFloat decoder to Int32 and adds implementation
  - interprets Software PID Ramp/Soak patterns w.r.t. time since PID ON in monitoring only mode
  - uses custom bootloader on Windows to reduce false malware warnings ([Issue #519](../../../issues/519))
  - show only CHARGE to DROP period of background profile
  - adds FCs ROR to computed section of `.alog` Artisan Profiles
  - shows `uu` instead of -1 for error values in LCDs
  - automatic mode for the upper delta axis limits sets also a reasonable step size for the axis ticks
  - dialogs with tabs remember the last selected tab
  - use proper time edit widget to set alarm times in alarm table
  - extends ranking reports by additional attributes (Excel, CSV)
  - extends the Cropster XLS importer to work also with exports done in languages others than English
  - [artisan.plus](https://artisan.plus/): optimized synchronization
  - improved S7 serial logging and communication error handling
  - [special events annotations](https://artisan-roasterscope.blogspot.com/2020/05/special-events-annotations.html) respect the decimal places setting
  - updated Spanish translations ([PR #525](../../../pull/525), [PR #527](../../../pull/427), [PR #530](../../../pull/530), [PR #535](../../../pull/535), [PR #536](../../../pull/536) and [PR #537](../../../pull/537) by [
Richard Rodrigues](https://github.com/rich1n))
  - updated Chinese translations ([PR #532](../../../pull/532) and [PR #538](../../../pull/538) by [wuyi-ligux](https://github.com/wuyi-levard))
* FIXES
  - fixes regression which broke the event picker in v2.4.2
  - fixes another issue with the multiple event button action processing ([Issue #504](../../../issues/504))
  - fixes wrong temperature and delta curve alignment in Comparator after redraw
  - fixes further Hottop 2k+ communication on macOS 10.15.7 (adding to [Issue #475](../../../issues/475))
  - fixes Loring setup to ensure valid burner readings on all machines
  - resolves a feature interaction between oversampling and the S7/MODBUS optimizer that could lead to unnecessary communication
  - fixes an unhandled  exception when changing color pattern ([Issue #516](../../../issues/516))
  - fixes broken RPi Stretch build ([Issue #518](../../../issues/518))
  - fixes Phidget async sampling modes that could take readings beyond the current sampling interval on communication drops
  - corrects alarm nr in roast properties table
  - fixes Excel export issue occurring with DeltaBT turned off
  - hides annotations for curves hidden by clicking the legend
  - renamed ET and BT curves can be hidden by clicking the legend
  - enables the PID SV buttons also for the internal software PID as well as for external MODBUS/S7 PIDs
  - applies Delta BT auto axis computation also to Web Ranking reports


**Note**
_This is the last version supporting Raspbian Stretch_

----
v2.4.2 (October 2, 2020)
------------------

* NEW FEATURES
  - extended machine support
     - adds [CTE Ghibli touch](https://artisan-scope.org/machines/coffeetech/) setup incl. control of burner, fan and drum speed
     - adds updated [IMF RM](https://artisan-scope.org/machines/imf/) setups
     - adds burner control to [San Franciscan](https://www.sanfranroaster.com/) setup
     - adds Toper USB setup next to the network MODBUS/TCP variant to connect to  [Toper TKM-SX](https://artisan-scope.org/machines/toper/) roasters
     - adds support for the new [Probat Sample Roaster and P Series III roasters](https://artisan-scope.org/machines/probat/)
     - adds [support for machines of more than 40 additional brands](https://artisan-scope.org/machines/index): [Ambex](https://artisan-scope.org/machines/ambex/), [ARC S/800](https://artisan-scope.org/machines/arc/), [Bella TW](https://artisan-scope.org/machines/bellatw/), [Berto One and D](https://artisan-scope.org/machines/berto/), [Bideli](https://artisan-scope.org/machines/bideli/), [Blueking BK](https://artisan-scope.org/machines/blueking/), [Brambati PLC](https://artisan-scope.org/machines/brambati/), [Dätgen DR/DW](https://artisan-scope.org/machines/datgen/), [Dongyi BR/BY/DY](https://artisan-scope.org/machines/dongyi/), [Easyster](https://artisan-scope.org/machines/easyster/), [Froco PLC](https://artisan-scope.org/machines/froco/), [Garanti GKPX](https://artisan-scope.org/machines/garanti/), [Golden Roasters GR](https://artisan-scope.org/machines/goldenroasters/), [Hartanzah Roaster](https://artisan-scope.org/machines/hartanzah/), [HB-Roaster](https://artisan-scope.org/machines/hb/), [Hive Roaster](https://artisan-scope.org/machines/hive/), [IP Xenakis iRm_Series incl. full control](https://artisan-scope.org/machines/ipxenakis/), [KapoK](https://artisan-scope.org/machines/kapok/), [Kuban Supreme setup incl. full control](https://artisan-scope.org/machines/kuban/), [Lilla PLC](https://artisan-scope.org/machines/lilla/), [Mill City Roasters MCR Series](https://artisan-scope.org/machines/mcr/), [NOR Coffee Roaster](https://artisan-scope.org/machines/nor/), [Nordic](https://artisan-scope.org/machines/nordic/), [Opp Roaster](https://artisan-scope.org/machines/opp/), [Öztürk](https://artisan-scope.org/machines/ozturk/), [Petroncini](https://artisan-scope.org/machines/petroncini/), [Roaster & Roaster](https://artisan-scope.org/machines/roasterandroaster/), [Rasco Mac](https://artisan-scope.org/machines/rascomac/), [Rolltech EL](https://artisan-scope.org/machines/rolltech/), [Santoker](https://artisan-scope.org/machines/santoker/), [Tesla](https://artisan-scope.org/machines/tesla/), [Tostabar Genius](https://artisan-scope.org/machines/tostabar/), [TRINITAS T2 and T7](https://artisan-scope.org/machines/trinitas/), [Trobrat](https://artisan-scope.org/machines/trobrat/), [Typhoon](https://artisan-scope.org/machines/typhoon/), [VNT](https://artisan-scope.org/machines/vnt/), [Vortecs](https://artisan-scope.org/machines/vortecs/), [Wintop](https://artisan-scope.org/machines/wintop/), [Yang-Chia Feima](https://artisan-scope.org/machines/yangchia/), and [Yoshan](https://artisan-scope.org/machines/yoshan/)
  - adds RoastLog profile importer ([Issue #471](../../../issues/441))
  - adds IKAWA v3 CSV file importer
  - adds import support for new Aillio Bullet R1 JSON format ([Issue #508](../../../issues/508))
  - adds font options "Source Han Sans" offering CN, TW, KR, JP character sets and "WenQuanYi Zen Hei" offering CN and TW character sets ([Issue #493](../../../issues/493))
  - adds sliders Bernoulli mode to emit values respecting Bernoulli's gas law translating non-linear between gas flow (slider values) and gas pressure (gas valve). See [the corresponding discussion on home-barista.com](https://www.home-barista.com/home-roasting/coffee-roasting-best-practices-scott-rao-t65601-70.html#p724654).
  - adds input filter to interpolate duplicate readings that may disturb the RoR computation
  - adds support for [artisan.plus](https://artisan.plus/) dynamic blend replacements
  - adds additional date and time fields to [autosave](https://artisan-roasterscope.blogspot.com/2020/05/autosave-file-naming.html)
  - adds ET and BT rate-of-rise to [special events annotations](https://artisan-roasterscope.blogspot.com/2020/05/special-events-annotations.html)
  - adds post roast update for symbolic ET and BT values in the profile
  - adds option to hide '--' untyped special events
  - adds second set of settings for Phidget TMP1200 RTD modules allowing to run different types of RTDs (eg. PT100 and PT1000) in parallel
  - adds support for the Phidget TMP1000 Ambient Temperature sensor
  - adds VOUT Command `range` to set the voltage range of the Phidget voltage output modules ([Issue #472](../../../issues/472))
  - adds support for [WebSocket communication](https://artisan-scope.org/devices/websockets/)
  - adds S7 support to read booleans and the S7 Commands actions `setDBbool(<dbnumber>,<start>,<index>,<value>)` and `getDBbool(<dbnumber>,<start>,<index>)`
  - adds S7 Command `msetDBint` to write Integers to S7 registers using masks
  - adds S7 help page
  - adds S7 scanner
  - adds MODBUS and S7 decoding of Floats as Integers
* CHANGES
  - new RoR computation method based on linear polyfits ([PR #503](../../../pull/503) by [PDWest](https://github.com/PDWest)) and "optimized" variant based on the [Savitzky-Golay filter](https://en.wikipedia.org/wiki/Savitzky%E2%80%93Golay_filter) for display after recording
  - do not propagate error values -1 to the full formula if the full formula is enclosed in parentheses
  - allows three digits following [q,w,e,r] special event shortcut when the corresponding slider max value is greater than 100.  Be aware that when this is true three digits must be entered so a leading zero is required for values less than 100.
  - changes Windows keyboard shortcut to remove background curve to CTRL+SHIFT+h
  - updates GUI libs (Qt/PyQt/Matplotlib)
  - updates Brazilian and Greek translations
  - updated Chinese translations ([PR #491](../../../pull/491) & [PR #494](../../../pull/494) by [wuyi-ligux](https://github.com/wuyi-levard))
  - extends CSV batch reports by some additional fields
  - respects Delta ET/BT symbolic formulas in Roast Properties data table
  - aligns z-order of RoR curves to their LCD order
  - images are saved with opaque borders when the canvas color is not set
  - save image for Home-Barista increased to 1200px wide
* FIXES
  - ensures that Roasted Density value (in Roast Properties) does reset on new roasts if "Delete roast properties on RESET" is ticked ([Issue #470](../../../issues/470))
  - prevents removal of line artists that have already been deleted on switching the crosslines off ([Issue #473](../../../issues/473))
  - ensure that flags position cache is cleared on reset before loading a new profile ([Issue #474](../../../issues/474))
  - fixes Hottop 2k+ communication boken in the macOS build of Artisan v2.4 ([Issue #475](../../../issues/475))
  - fixes regression that calculated axis limits automatically on incomplete profiles while recording on leaving the Axis dialog ([Issue #476](../../../issues/476))
  - ensures that normal saves respect the autosave path for extra files (JSON, PDF,..) ([Issue #480](../../../issues/480))
  - allow to enter super-user mode with a simple left-click on the timer LCD as right-clicks are not available on touch screens ([Issue #481](../../../issues/481))
  - fixes a regression that prevented some roasts not to be successfully uploaded to artisan.plus in rare cases related to Fahrenheit conversion
  - ensures that autosave profiles get synced to artisan.plus in any case
  - fixes special event annotations will show when there is no DROP event
  - fixes plotting specialevents >100 while recording in step modes
  - makes the Comparator compatible to profiles created by legacy versions of Artisan
  - fixes a rare redraw problem in Comparator mode which result in curves being only partially visible
  - improves stability of serial communication with serial meters like the Center304/309/..
  - fixes crash on multiple event button actions ([Issue #504](../../../issues/504))
  - prevents saving NaN annotation and flag coordinates in profiles ([Issue #505](../../../issues/505))
  - fixes Transposer crash ([Issue #506](../../../issues/506))
  - fixes palette loading from .apal files

**Note**
_This is the last version supporting macOS 10.13 and 10.14_


----
v2.4.0 (June 3, 2020)
------------------

* NEW FEATURES
  - adds [Roast Comparator](https://artisan-roasterscope.blogspot.com/2020/05/roast-comparator.html), [Roast Simulator](https://artisan-roasterscope.blogspot.com/2020/05/roast-simulator.html), and [Profile Transposer](https://artisan-roasterscope.blogspot.com/2020/05/profile-transposer.html)
  - adds Cropster XLS, IKAWA CSV, Giesen Software CSV and RostPATH URL profile import
  - adds flexible [automatic file name generator](https://artisan-roasterscope.blogspot.com/2020/05/autosave-file-naming.html) ([Issue #430](../../../issues/430), see also [Saving Artisan Profiles - Naming, Saving, File Location etc](https://www.home-barista.com/home-roasting/saving-artisan-profiles-naming-saving-file-location-etc-t61713.html))
  - adds custom [special event annotations](https://artisan-roasterscope.blogspot.com/2020/05/special-events-annotations.html) in step and step+ modes that will show roast data including time, temperature DTR, etc.
  - adds support for the [Giesen IR sensor](https://artisan-scope.org/machines/giesen/)
  - adds support for [Twino/Ozstar roasting machines](https://artisan-scope.org/machines/twino-ozstar/)
  - adds S7 and MODBUS communication optimizer
  - adds two more S7 and MODBUS channels
  - adds support for Yoctopuce [Yocto-0-10V-Tx](https://www.yoctopuce.com/EN/products/usb-electrical-interfaces/yocto-0-10v-tx), [Yocto-4-20mA-Tx](https://www.yoctopuce.com/EN/products/usb-electrical-interfaces/yocto-4-20ma-tx), [Yocto-PWM-Tx](https://www.yoctopuce.com/EN/products/usb-electrical-interfaces/yocto-pwm-tx), [Yocto-4-20mA-Rx](https://www.yoctopuce.com/EN/products/usb-electrical-sensors/yocto-4-20ma-rx), [Yocto-Servo](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-servo) and Yoctopuce Relays modules ([Yocto-Relay](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-relay), [Yocto-LatchedRelay](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-latchedrelay), [Yocto-MaxiCoupler-V2](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-maxicoupler-v2), [Yocto-PowerRelay-V2](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-powerrelay-v2), [Yocto-PowerRelay-V3](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-powerrelay-v3), and [Yocto-MaxiPowerRelay](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-maxipowerrelay))
  - adds support for Phidget VINT DCMotor modules ([DCC1000](https://www.phidgets.com/?tier=3&catid=18&pcid=15&prodid=965), [DCC1002](https://www.phidgets.com/?tier=3&catid=18&pcid=15&prodid=1117) and [DCC1003](https://www.phidgets.com/?tier=3&catid=18&pcid=15&prodid=1118)), mDNS Phidget server service discovery and support for multiple Phidget IO modules identified by their hub serial number and port
  - better support of hi-resolution displays under Windows
  - adds large phases LCDs
  - adds status flags to the menu entries for all large LCD views
  - adds automatic mode for the upper delta axis limit
  - adds explicit upper y-axis limit for custom events 100% mark
  - adds "load from profile" flag to Axis dialog
  - adds link to Artisan homepage to About dialog
  - adds check for updates menu action ([Issue #447](../../../issues/447))
  - adds CSV and JSON to autosave file formats and allows to store extra autosave files in a separate directory
  - adds right-click to the batch number label action in the Roast Properties dialog which allows to edit the batch number (also in Viewer mode)
  - adds a dialog allowing to enter event details on using the right-click to BT popup to add a new event
  - adds support for complex expressions in button command actions (e.g. `write(1,{}*10)`)
  - adds support for multiple value substitutions in button and slider actions (ie. the placeholder `{}` can occur multiple times in the command string and gets always correctly substituted by the slider value)
  - adds a variant of the MODBUS mwrite command action that takes a value as further argument used to compute the value send to the slave via MODBUS function 6
  - adds MODBUS Command action `button(<bool>)` to set the extra event button state
  - adds `{BT}`, `{ET}`, `{t}` substitutions for Serial, Program, MDBUS and S7 command actions
  - adds space key action to create plain events while keyboard short cut event navigation is off
  - adds symbolic variables `RB1` and `RB2` to referring to the rate-of-rise readings of the background profile
  - adds an option to automatically open completed roasts in the ArtisanViewer on turning Artisan ON for the next roast
  - adds Open on DROP to Roast Properties dialog
  - adds Artisan Command `openProperties` to open the Roast Properties dialog from buttons (potentially invisible and triggered by alarms)
  - adds organization field to Roast Properties
  - adds loading of profiles on drag-and-drop to the main window
  - adds second extra device background curve
* CHANGES
  - remember the position of draggable annotations and the legend
  - event annotations in combo mode are rendered as value with the event slider suffix added if descr. mode is not ticked (thus a Burner event of value 85 with Burner event slider suffix % is rendered as 85% instead of the default B85)
  - the axis system to render custom events in Step/Step+/Combo mode extends now from the temperature axis minimum up to the lowest phases temperature if snap mode is not active (or the newly introduced explicit 100% y-axis limit given
  - extends grid alpha range from 1-5 to 1-10
  - allows to edit batch number in super mode also if the batch counter is deactivated
  - [artisan.plus](https://artisan.plus/): after 3 month of expired subscription stop trying to login automatically!
  - [artisan.plus](https://artisan.plus/): on changing the batch size the beans field is automatically updated to listing the weight per component of blends
  - on loading profiles with extra device channels Artisan will always ask to update your setup or not. Extra devices settings concerning just the visualization (like color) will always be taken from your current Artisan settings and never modified on loading a profile.
  - replace the generic "Select" label on extra device color buttons by the name of the selected color
  - suppress event quantification for slider changes triggered by the Artisan PID
  - improved online help system
  - the layout of large LCDs have been optimized to better use the available space
  - removes superfluous configurations relating to the removed evaluation feature from statistics dialog
  - memory usage and performance improvements and updated main libraries (Python, Qt, PyQt, matplotlib,..) providing many fixes
  - adds delta ET and delta BT readings to the LCDs when the scope is ON
  - updates the Besca automatic machines setup
  - in "Keep ON" modus (Sampling dialog), Roast Properties are cleared begin of new roasts if "Delete roast properties on RESET" in the Roast Properties dialog is ticked
* FIXES
  - fixes raw redraw issues ([Issue #390](../../../issues/390)) caused by an interaction of bitblit redraw triggered by draggable annotations and right-click event re-positioning mechanism
  - now fully fixes the Roast/Cup Profile where values keep changing to max or min if double clicked by adding incremental redraw to the cupping dialog ([Issue #360](../../../issues/360))
  - fixes a rare exception in device label substitution
  - re-enable the input of negative alarm values (a regression introduced in v2.0)
  - fixes a crash in the Yoctopuce driver on macOS 10.15
  - fixes Phidgets DAQ1400 current input
  - fixes Phidget HUB PWM output
  - fixes regression that broke S7 Command actions
  - fixes load theme inadvertently changing phases LCD modes
  - fixes to acaia support incl. proper weight conversion
  - fixed enable/disable of `File >> Save Copy As` and `File >> Conversion` menu actions based on app state
  - fixes a feature interaction between the background logo image and the cupping editor, the designer and the wheel graph editor
  - improves accuracy of displayed timestamps
  - improved crossline, timeline, AUC guide and projection line rendering
  - improved rendering of timestamps in mouse coordinates widget
  - background annotations setting now restored on exiting analyzer
  - disables dragging of items in extra event button table (header dragging is still enabled and processed)
  - accepts floats for extra devices serial timeouts
  - fixes to MET marker and to copy table
  - fixes a regression introduced in v2.0 that broke the input of negative alarm values
  - draws markers of "untyped" events of background profiles as flags if event markers mode is set to Step or Combo


----
v2.3.0
------------------

never released

----
v2.2.0
------------------

never released

----
v2.1.2 (December 24, 2019)
------------------

* NEW FEATURES
  - adds copy (to clipboard) action to the alarm table
* CHANGES
  - alarm popups are now non-modal
* FIXES
  - remembers settings path on exporting settings to update the batch counter correctly in the saved settings file
  - fixes exception when copying device table
  - fixes regression that broke file open events issued by the finder on macOS ([Issue #445](../../../issues/445))
  - updates large main LCDs via signals in the main thread to prevent interleaved access
  - ensures that plus records are only uploaded on the first time a drop is set and not on each update via the right-click to BT popup
  - fixes regression that prevented the timeline to be drawn in manual mode
  - hide background image while zoomed ([Issue #438](../../../issues/438))
  - automatically adjust transparent canvas in dark mode on macOS
  - fixes regression that resulted in the legend disappearing on clicks to hide curves
  - fixes rounding issue on creation of Excel ranking reports
  - fixes regression which prevented the registration of file paths generated by autosave
  - improves robustness the symbolic formula evaluation with indexed access
  - adds projections and timeline to follow-mode
  - preserve axes settings with analyze in Fahrenheit mode
  - prevents autoCHARGE and autDROP after undo on those events
  - prevents disappearing of projection lines on adding events

----
v2.1.1 (November 29, 2019)
------------------

* FIXES
  - fixes DROP action, broken in v2.1.0
  - fixes S7 communication, broken in v2.1.0
  - fixes rare issue with the exit handler

----
v2.1.0 (November 26, 2019)
------------------

* NEW FEATURES
  - ACTIONS: adds "Multiple Event" action to default buttons actions
  - ACTIONS: adds sleep(<n.m>) command to multiple button event action
  - ACTIONS: adds Modbus Command action `writeWord(slaveId,register,value)` to write 32bit decimal numbers using MODBUS
  - ACTIONS: adds additional Artisan Commands
     * `PIDon`, `PIDoff`, `PIDtoggle` to change the internal PID state
     * `pidmode(<n>)` with `<n>` 0: manual, 1: RS, 2: background follow
     * `playbackmode(<n>)` with `<n>` 0: off, 1: time, 2: BT, 3: ET
function 16
  - ALARMS: adds alarm actions to set and reset the canvas color
  - ALARMS: adds alarm actions to turn playback off and on
  - ALARMS: the "insert" and "add" actions of the alarms table takes default values from selected item if any
  - ALARMS: adds (If Alarm) alarms triggered by temperature differences
  - ANALYZER: first version that brings curve fit and RoR flick/crash analysis features
  - BATCH COUNTER: increases batch counter also in last loaded settings file
  - BATCH COUNTER: add a flag to control if the batch counter should be changed on loading a settings file
  - EVENTS: the "insert" and "add" actions of the custom button table takes default values from selected item if any
  - EXPORT: adds RoR and special event data to Excel exports
  - EXPORT: adds copy table button to several tables in tab separated format (roast data, roast events,...).  ALT-click (OPTION on macOS) to Copy button will copy a rendered variant of the data
  - EXPORT: adds ability to save the statistics summary box to a file
  - EXTRA DEVICES: adds "Update Profile" button to recompute the symbolic formulas of all Virtual Devices
  - EXTRA DEVICES: adds delta axis flags to have extra device curves drawn relative to the z-axis (C/min or F/min axis). Useful if a device sends directly RoR data (like potentially the TC4), if a Virtual Device is used to draw the RoR of a curve different to ET and BT
  - EXTRA DEVICES: adds extra device curve fills, value sets the opacity of the fill
  - MACHINE SUPPORT: extended Besca machine setups including the [Bee sample roaster](https://www.bescaroasters.com/roaster-detail/14/Sample-Roasters/Besca-Bee-Coffee-Roaster) and the setup "Besca BSC manual v2" for manual machines produced after 15.09.2019
  - MACHINE SUPPORT: updated [Coffeetool Rxx](https://coffeetool.gr/product-category/coffeeroasters/) machine setup to allow for burner, air flow and drum speed control
  - MACHINE SUPPORT: adds Drum Speed and Air Flow to Buhler Roastmaster setup
  - MACHINE SUPPORT: adds support for further [Coffed](https://coffed.pl/en) machines (SR3/5/15/25/60) automatic and manual variants
  - MACHINE SUPPORT: adds support for the [Atilla](https://www.atilla.com.br/) GOLD_plus_7'' II
  - MACHINE SUPPORT: adds machine configurations for [popular Phidget sets](https://artisan-scope.org/devices/phidget-sets/)
  - MATH: adds x^2 to the exponent function as well as the possibility to define an offset from CHARGE
  - PHIDGETS: adds Phidget HUB0000 IO 0 and Phidget HUB0000 IO Digital 0 one channel device types that allocate only that single one channel/port to allow the use of all HUB0000 ports with an uneven number of analog or digital IO channels
  - PHIDGETS: attach IO Phidgets already in OFF mode on demand
  - PHIDGETS: adds OUT1100, REL1000, REL1100, REL1101 to Phidget binary IO API
  - PHIDGETS: fully supports all 16 ports of the REL1101 (not only the first 4 as before)
  - PHIDGETS: adds ALT-RESET (OPTION-RESET on macOS) button action to additionally detach all IO Phidgets
  - PHIDGETS: adds Phidgets driver version to the about dialog
  - PLUS: adds [artisan.plus](artisan.plus) subscription status indicator
  - PLUS: adds artisan://roast/<uuid> URL scheme to link back to Artisan (click to the title) and artisan.plus (click to the date) on html roast, production and ranking reports
  - PLUS: adds confirmation dialog on disconnecting artisan.plus
  - PLUS: adds CTR-click (COMMAND on macOS) on plus icon to disconnect and erase credentials from keychain
  - PLUS: adds ALT+CTR-click (OPTION+COMMAND on macOS) on plus icon to toggle artisan.plus debug login (defaults to off)
  - PLUS: adds ALT-click (OPTION on macOS) on plus icon to compose an email containing the plus log
  - SYMBOLIC FORMULAS: adds symbolic formula variables R1 and R2 bound to the last ET/BT RoR values incl. indexed access
  - SYMBOLIC FORMULAS: adds Rate of Rise symbolic assignments ([Issue #383](../../../issues/383)) to allow e.g. to divide C/min readings by 2 to show them as C/30sec
  - SYMBOLIC FORMULAS: extends the roast calculus by additional symbolic variables to access the index of main events, predictions and AUC values and allows indexed access to profile, background time and curve values allowing to define forward looking alarms
  - UI: adds size selector (tiny, small, large) for custom event buttons
  - UI: adds dirty file indicator
  - UI: adds ALT-h (OPTION-h on macOS) keyboard shortcut to remove the background profile
  - UI: adds ALT-NEW (OPTION-NEW on macOS) keyboard shortcut to just load the recent roast settings (incl. the associated background) without actually starting the recording
  - UI: holding ALT key (OPTION on macOS) while adding roast to the list of recent roast properties to also add the weight, volume, density, moisture and color of the roasted batch to the record
  - UI: adds profile background images
  - UI: graph annotations can be now be repositioned by dragging
  - UI: adds large Delta, PID and Extra LCDs ([Issue #303](../../../issues/303))
  - UI: adds opacity configuration in Color Dialog for analytics, legend and Statistic Summary boxes
  - UI: adds dark mode support on macOS (improves Roast Properties and HTML reports)
* CHANGES
  - DEVICE SUPPORT: reworked ambient temperature collection from 1048/TMP1101 Phidgets or selected ambient temperature curve (now again triggered automatically at DROP) ([Issue #420](../../../issues/420))
  - TRANSLATIONS: adds back Farsi and Indonesian translations that got broken
  - TRANSLATIONS: updated Brazilian, French and Greek translations
  - UI: improve messages when clicking events in step, step+ and combo modes
  - UI: retain readings LCD visibility when closing/starting roast ([Issue #364](../../../issues/364))
  - UI: timer LCD hides and shows together with other main LCDs
  - UI: clearer menu titles for Config>Temperature and Tools>Temperature
  - UI: removed evaluations from the statistics bar
  - UI: autosave profiles are no longer added to the recent file menu
  - UI: reworked statistic summary featuring a configurable line length
  - UI: don't move sliders on RESET
* FIXES
  - ACTIONS: fixes broken Artisan Command "tare" ([Issue #376](../../../issues/376))
  - BATCH COUNTER: improves overwrite handling of counter on loading settings from .aset files ([Issue #372](../../../issues/372))
  - DEVICE SUPPORT: fixes Acaia lunar random disconnect failures
  - EVENTS: fixes random duplicate event entry on slider moves
  - EXPORT: enhancements and fixes to Web and Excel reports ([Issue #401](../../../issues/401))
  - EXPORT: fixed the broken Excel export
  - EXTRA DEVICES: ensures that extra channels of profiles with no extra curves loaded into a setup with extra curves get correctly initialised ([Issue #373](../../../issues/373))
  - EXTRA DEVICES: fixes extra LCD/Curve states on deleting the selected extra device if it is not the last (thanks Dave for spotting this!)
  - PHIDGETS: fixes a regression introduced in v1.6.1 that broke the Phidget HUB VoltageRatio input on uneven channels
  - PHIDGETS: ensure that VINT Phidgets are always assigned to Artisan device channels in order of the HUB port they are plugged in
  - SYMBOLIC FORMULAS: fixes symbolic variables E1,E2,E3,E4 holding last event value ([Issue #277](../../../issues/277))
  - UI: deactivate autoDRY and autoFCs for the current recording after the added event was undone to avoid further auto event triggers
  - UI: fixed PhasesLCD labels color not adjusting to canvas color
  - UI: fixes dpi not updating from saved settings
  - UI: fixes cross-line bitblit after resize
  - UI: fixed truncated menus on Windows by upgrading to PyQt 5.13.1
  - UI: fixed truncated ComboBox items on Mac OS X by upgrading to PyQt 5.13.1
  - UI: fixes density loss computation in Statistic Summary
  - UI: set file dirty and reset file path if extra device setup of profile was adjusted on load
  - UI: Roast/Cup Profile: value keep changing to max or min if double clicked ([Issue #360](../../../issues/360))
  - UI: Roast Properties "Title" Font Color problem ([Issue #371](../../../issues/371))
  - UI: toggling the mouse coordinates via key d updates the message line immediately ([Issue #422](../../../issues/422))


----
v2.0.0 (June 4, 2019)
------------------

* NEW FEATURES
  - adds support for the [artisan.plus](https://artisan.plus/) inventory management service ([Issue #231](../../../issues/231) and [Issue #308](../../../issues/308))
  - adds support for the [Coffee-Tech Engineering Silon ZR7](https://www.coffee-tech.com/products/shop-roasters/silon-zr-7-shop-roaster/)
  - adds support for [Has Garanti HGS and HSR series](http://www.hasgaranti.com.tr/en/products/shop-type-products/shop-type-roasting-coffee-machine.html)
  - adds support for [Kaldi Fortis](https://eng.homecaffe.net/product/kaldi-fortis-grande-coffee-roaster/126/category/223/display/1/)
  - adds support for [Behmor 1kg](https://behmor.com/jake-kilo-roaster/)
  - adds support for the [VICTOR 86B Digital Multimeter](http://www.china-victor.com/index.php?m=content&c=index&a=show&catid=42&id=26) (by Lewis Li)
  - adds support for [Acaia coffee scales](https://acaia.co/collections/coffee-scales) via directly Bluetooth Low Energy (BLE) communication without need for configuration or extra hardware (OS X only for now)
  - adds sorting of custom event buttons table by drag-and-drop ([Issue 214](../../../issues/214), resolved by [PR #345](../../../pull/345) contributed by Phil)
  - adds tick to swap Delta BT/ET LCDs and the corresponding curve z-order ([Issue 330](../../../issues/330))
  - allows to set RoR smoothing for ET and BT separately
  - adds beep to playback aid and noisy text messages
  - adds Artisan Command actions to enable/disable AutoCHARGE and AutoDROP (`autoCHARGE(<b>)` and `autoDROP(<b>)`)
  - adds Artisan Command `tare(<n>)` to tare channel `<n>` with `1 => ET, 2 => BT,..` ([Issue 331](../../../issues/331))
  - renders values of background events in Combo mode ([Issue 274](../../../issues/274))
  - adds background event marker and text settings to color configuration
  - adds translations for Farsi (thanks to Saeed Abdinasab)
* CHANGES
  - breaking feature: app domain changed to artisan-scope.org with the consequences that the app settings are now stored in a different location w.r.t. previous app versions
  - new app icon
  - new UI designs (buttons, LCDs,..)
  - curves are now drawn in LCD order thus ET is drawn above BT by default. If swap LCDs is ticked under Config >> Devices, also BT is drawn on top of ET.
  - hidden custom event button are interpreted as spacers to layout button groups
  - lib updates on all platforms but RPi (Python 3.7.3, Qt 5.12.3, PyQt 5.12.2, pymodbus 2.2, Matplotlib 3.1)
  - RESET button action disconnects serial, MODBUS and S7 connections
  - removes roasted weight, volume, density and moisture as well as colors from recent roast menu items
  - updated Chinese translations (thanks to Lewis Li)
* FIXES
  - fixes and error when starting designer ([Issue 340](../../../issues/340))
  - adds back the missing ET RoR LCD ([Issue 343](../../../issues/343))
  - fixes Update button in Roast Properties to harvest ambient sensors
  - improved Yoctopuce async mode (adds 1s* averaging on device mode)
  - fixes cross mouse rendering
  - keeps PhidgetManager running on "Keep ON"
  - improves the communication speed of several serial meters like the Voltcraft and Omega devices
  - fixes regression that could lead to a potential hang caused by slow communicating devices

----
v1.6.2 (March 20, 2019)
------------------

* CHANGES
  - larger slider handles
* FIXES
  - enables communication with Phidgets under the Mac OS X 10.14 security framework
  - removes MODBUS from the non-serial device list
  - ensures that uninstaller on Windows is removing everything
  - fixes regression that disabled the editing of roast properties event times


----
v1.6.1 (March 10, 2019)
------------------

* NEW FEATURES
  - adds focus indicator to event sliders
  - extends the import alarms action to load alarms also from `.alog` Artisan profiles besides
 dedicated Artisan alarm files (.alrm)
  - hide/show curves via click to corresponding entry in the legend
  - adds IO Command state feedback by mfurlotti ([PR #284](../../../pull/284))
  - adds support for more digital output Phidgets [REL1000](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=966), [REL1100](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=720) and the first 4 channels of [REL1101](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=721) ([Issue #286](../../../issues/286))
  - adds support for the Phidget [DAQ1400](https://www.phidgets.com/?tier=3&catid=49&pcid=42&prodid=961) (current/frequency/digital/voltage input)
  - adds support for the Phidget RC Servo API supporting the servo controllers [Phidget RCC 1000](https://www.phidgets.com/?tier=3&catid=21&pcid=18&prodid=1015) (16x VINT, ext. powered), [Phidget 1061](https://www.phidgets.com/?tier=3&catid=21&pcid=18&prodid=1032) (8x USB, ext. powered), and [Phidget 1066](https://www.phidgets.com/?tier=3&catid=21&pcid=18&prodid=1044) (1x USB powered) together with a wide range of servo motors from Phidgets (like the [Phidget 3540 10cm Linear Actor](https://www.phidgets.com/?tier=3&catid=25&pcid=22&prodid=406)) or other sources
  - adds support for the [Yocotopuce Meteo](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-meteo-v2) ambient sensors
  - adds support for the (upcoming) [Yocotopuce](http://www.yoctopuce.com/EN/products/category/usb-environmental-sensors) IR module
  - adds support for the [Probat Roaster Middleware](https://www.probat.com/en/products/shoproaster/produkte/roasters/probatone-series/)
  - adds 2in1 variant of Sedona Elite machine configuration
  - adds CMD-A keyboard shortcut to open alarms dialog
  - adds JPEG and BMP support (export/convert)
  - adds selection of autosave image type
  - adds batch number to title already during recording
  - adds a button to remove recent roast entries
  - adds Brazilian portuguese (as spoken in Brazil)
  - adds the possibility to rename ET/BT curves and LCDs on the graph
  - adds flags to show/hide time/temp grids
  - adds the Yocto async mode
  - adds roasted coffee density field and density loss calculation to Roast Properties
  - adds support for the [Aillio R1](https://aillio.com/) v1.5 and v2 firmware and new [IBTS IR sensor](https://medium.com/@aillio/the-start-of-something-39aa01d08fa9)
* CHANGES
  - improved Phidgets tab rendering
  - store reference to profile instead of background with recent roasts
  - faster draggable legend using bit blit on Mac OS X
  - updated default RoR limits (now 0-25C and 0-45F)
  - faster attach of Phidget devices
  - extends the range of allowed event values in the mini editor from 0-100 to 0-9999
  - allow to control Hottop 2k+ while not logging
  - updated French translations (thanks Nico!)
  - adds 0.05C and 0.02C Phidget Change Triggers
  - adds default focus to OK button and assigns CMD-W and CMD-. shortcuts to the Cancel button of most dialogs ([Issue 321](../../../issues/321))
  - improved Roast Properties dialog layout
* FIXES
  - fixes feature interaction between NewRoast and AlwaysOn that caused a hang ([Issue 275](../../../issues/275))
  - fixes sliders single step action
  - fixes the air and drum speed slider synchronization in the Probatone 7" setup
  - translates 1045 ambient readings correctly to Fahrenheit in Fahrenheit mode
  - improved accuracy of MET marker location
  - improved stability of Phidget Ambient Sensor attach
  - channel selection fix for Phidget OUT1002 by Mike
  - fixes various issues with the Cupping Dialog ([Issue #280](../../../issues/280))
  - fixes issue that event type is not retained
  - clears row selections on opening Roast Properties to have the "Create Alarm" action work on all events
  - fixed display when auto axis is checked and events annotations is unchecked
  - fixed a bug in RoR computation of the Ranking Report
  - fixes call program to split commands containing quotes correctly ([Issue #287](../../../issues/287))
  - fixes an issue with plotter on creation of extra devices where time information was missing
  - fixes the p-i-d command for the TC4 that got broken in v1.5
  - fixes the initialization of the Artisan internal PID ([Issue #310](../../../issues/310))
  - adds missing redraw if only background is automatically reloaded on app start
  - removes clamping of custom events on drawing a background profile with snap events is ticked ([Issue #296](../../../issues/296))
  - fixes an internal resource management issue that led to redraw issues or even hangs on slow machines ([Issue #298](../../../issues/298))
  - fixes an issue that prevented event replay after background events of a type without an active slider ([Issue #302](../../../issues/302))
  - fixes an interaction between autoDROP and manual DROP
  - ensures that profiles saved as PDF on autosave at the end of a roast contain the phases bar
  - fixes HUD button styles
  - fixes alignment of AUC shading when Smooth Curves value is large and Optimal Smoothing is not checked
  - fixes an issue on CHARGE on newer Aillio R1 firmware versions ([Issue #297](../../../issues/297))
  - fixes Phidgets 1046 async mode
  - fixes the broken negative target slider (PID) ([Issue #314](../../../issues/314))
  - moves the connected to MODBU message from errors to messages
  - fixes an issue on older Qt/PyQt version not supporting certain keyboard shortcuts ([Issue #326](../../../issues/326))
  - fixes a logical issue on Artisan discarding profiles when it should not do so ([Issue #329](../../../issues/329))

----
v1.6.0
------------------

never released

----
v1.5.0 (October 17, 2018)
------------------

* NEW FEATURES
  - adds ArtisanViewer mode allowing again to run a second (restricted) instance of Artisan ([Issue #260](../../../issues/260))
  - adds support for VoltageRatio for Phidgets IO enhancement ([Issue #252](../../../issues/252))
  - extends LCD rendering from [-999,9999] to render [-9999,99999] if "Decimal Places" are turned on
  - adds "Program 78" and "Program 910" device types
  - adds support for manual [Besca roasting machines](https://www.bescaroasters.com/)
* CHANGES
  - order of columns in roast/background properties events table, CSV import/export and Excel export swapped (ET always before BT)
  -  event values on the graph are not abbreviated anymore if "Decimal Places" is not ticked
* FIXES
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
v1.4.0 (October 3, 2018)
------------------

* NEW FEATURES
  - adds time guide option (most useful when following a background profile)
  - adds export and convert to Excel
  - adds PhasesLCD mode-by-phase selection
  - adds PhasesLCD mode that shows all of time/temp/percentage in finish phase across the 3 Phases LCDs ([Issue #235](../../../issues/235))
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
* CHANGES
  - ensures that background curves are always render using the same smoothing algorithm as the foreground
  - adds re-sampling and back-sampling to improve all smoothing algorithms
  - adds "Insert" button to trigger the extra event table insert action instead of abusing the "Add" button
  - use zero-based port numbering in Phidgets tab
  - renumbers config event types 1-4 to be consistent with plotter notation
  - adds roastUUID to `.alog` Artisan profiles
  - ensures that only a single instance runs per machine
  - adds a pop-up reminder message when you forget to right-click on the timer LCD in Hottop 2K+ mode ([Issue #220](../../../issues/220))
  - allow alarms to move sliders beyond the default range of 0-100 ([Issue #213](../../../issues/213))
  - maps internal PID duty 0-100% to the full min/max range of the selected positive/negative target sliders
  - updates in-app link to documentation
  - simplifies to one set of roast phases
  - more accurate timestamping
  - increases number of time/temp decimals in `.alog` Artisan profiles
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
* FIXES
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
v1.3.1 (May 20, 2018)
------------------

* NEW FEATURES
  - adds Cmd-Shift-S as shortcut for "Save As" ([Issue #194](../../../issues/194))
  - remembers fullscreen mode over restarts ([Issue #199](../../../issues/199))
  - allows to insert a custom event button line before the selected one by clicking Add
  - adds insert action to the alarm table to add an alarm line before the selected one
  - adds support for the new Fuji PID PXF
  - adds PXF variant of Sedona Elite and Phoenix machine configurations
  - adds copy as tab delimited text action for data tables
* CHANGES
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
* FIXES
  - ensures that the matplotlib font cache is used on Linux ([Issue #178](../../../issues/178))
  - fixes an error that could occur on deleting an event button definition ([Issue #179](../../../issues/179))
  - ensures proper persistence of the "Descr." checkbox state of the events dialog over restarts ([Issue #180](../../../issues/180))
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
v1.3.0 (April 15, 2018)
------------------

* NEW FEATURES
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
* CHANGES
  - reorganized some menus and dialogs
  - improves location calc for statssummary
  - allow alarm button action to trigger several buttons at once via a list. The following string is now valid: "1,2,3 # docu"
  - imports a broader range of Aillio bullet R1 profiles
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
* FIXES
  - fixes a bug that made the background RoR curves disappear on START
  - fixes a crash on clicking the SV slider
  - fixes designer reset issue
  - fixes p-i-d button action that never triggered
  - fixes coarse quantifiers
  - recomputes AUC in ranking reports based on actual AUC settings
  - fixes an issue where closing a confirmation dialog via its close box could lead to losing the recorded profile instead of canceling the activity
  - ensures that the persisted graph dpi is applied on startup and loading settings
  - fixed Issue #154 where replay-by-temp events would trigger out of order
  - fixes Phidgets 1046 device support broken in v1.2
  - restrict temperature conversion to temperature curves
  - fixes crash on some Linux platforms w.r.t. selection of items in tables like events, alarms,..


----
v1.2.0 (December 21, 2017)
------------------

* NEW FEATURES
   - adds alarm file name to Roasting Report
   - adds SV alarm action
   - adds event replay by temperature (donated by [doubleshot](https://www.doubleshot.cz/))
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
   - adds optional automatic saving of PDFs alongside `alog` Artisan profiles
   - adds Hottop to the machine menu
  - adds "remote only" flag to the Phidget tab to force remote access also for locally connected Phidgets if local Phidget server is running. That way the local Phidget server can be use on the machine running Artisan to access the Phidgets from Artisan and any other software (incl. the Phidget Control Panel) in parallel.
  - adds support for MODBUS function 1 (Read Coil) and 2 (Read Discrete Input)
  - sends DTA Commands to the BTread PID if the ETcontrol PID is not a DTA
  - adds IO Commands action to sliders
  - adds mechanism to show/hide the control bar as well as the readings LCDs
  - adds a roast phase statistics visualization to the ranking report (by Dave Baxter)
  - adds drum speed field to roast properties (by Dave Baxter)
* CHANGES
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
* FIXES
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

**NOTE**
_This is the last version supporting supporting Mac OS X 10.12 and Linux glibc 2.17_

----
v1.1.0 (June 10, 2017)
------------------

* NEW FEATURES
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
* CHANGES
   * changes background of snapped by-value events
   * renamed and localized custom event labels
   * profiles sampling interval setting cannot be modified after recording anymore
   * increases resolution on displaying by-value events from 0-10 to 0-100
   * improved LCD color defaults
* FIXES
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


**NOTE**
_This is the last version supporting supporting Mac OS X 10.9, Windows XP/7 and 32bit OS versions_

----
v1.0.0 (February 24, 2017)
------------------

* NEW FEATURES
   * adds [internal PID](https://artisan-roasterscope.blogspot.de/2016/11/pid-control.html) and support to control external MODBUS PIDs
   * adds two more MODBUS input channels (now 6 in total)
   * adds alarms triggered at a specified time after another alarm specified as "If Alarm" was triggered, if "from" rules is set to "If Alarm"
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
   * adds Yoctopuce VirtualHub support for accessing remote Yoctopuce devices over the network
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
* CHANGES
   * dramatically improves speed of MODBUS over serial communication (by patching the underlying pymodbus lib)
   * makes message, error and serial logs autoupdating
   * removes "insert" in alarm table, which is not compatible to the new flexible alarmtable sorting
   * restrict file extension to `.alog` on loading a profile
   * current slider and button definitions are now automatically saved to palette #0 on closing the events dialog such that those definitions cannot get lost accidentally by pressing a number key to quickly entering an event value during recording
   * reconstruct users environment on calling external programs on MacOS X, not to limit them to the Artisan contained limited Python environment
   * remembers playback aid settings
   * improved RoR smoothing during recordings
   * makes development percentage the default for the phases lcds
   * increases resolution for Yoctopuce devices
   * timeouts accept one decimal place
   * improved dialog layouts
* FIXES
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

**NOTE**
_This is the last version supporting Mac OS X 10.7 and 10.9_

----
v0.9.9 (March 14, 2016)
------------------

* NEW FEATURES
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
* CHANGES
   * existing extra device mathexpression formulas are no longer changed if extra devices have to be extended on loading a profile
   * deactivates the auto-swap of ET/BT on CSV import (issue #85)
   * increased Hottop safety BT limit from 212C/413F to 220C/428F
* FIXES
   * better initial Phidgets attach handling
   * improved RoR calculation
   * improved temperature and RoR curve drawing, fixes among others the issue of the delta curves missing from the roasting report (issue #84)
   * fixes regression on moving the background up and down
   * minor improvements
   * fixed rare slider selection visual artifact on OS X
   * ensures that alarms are sorted based on alarm numbers on opening the dialog
   * fixed volume increase calculation

**NOTE**
_This is the last version supporting Mac OS X 10.7 and 10.8_

----
v0.9.8 (October 21, 2015)
------------------

* NEW FEATURES
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
* CHANGES
  * custom event buttons and sliders remembers visibility status
  * plotter "Virtual Device" action renamed into "BT/ET", now adds plot data to BT/ET if no profile is loaded, otherwise it creates an additional Virtual Device
  * the symbolic variables ETB and BTB to access data from the background curves have been generalized and renamed into B1 and B2
  * default state of the statistic line on the bottom of the main window changed (right-click still toggles) and setting made persistent
  * time align of background profiles now possible per all major events possible (always aligns to CHARGE first, and if set to ALL, it aligns to all events in sequence of their occurrence)
  * increases the time and temperature resolution
* FIXES
  * fixed port name support in serial port popup on OS X
  * fixed printing on OS X
  * fixed sorting of alarm list of numbers larger than 9
  * fixed temperature conversion issues (phases / background profile interactions)
  * fixed Yocotopuce reconnect handling
  * fixed Fuji PRX duty signal
  * fixes a build issue on Mac OS X to prevent a startup crash related to X11 libraries

----
v0.9.7 (July 29, 2015)
------------------

* FIXES
  * fixes epoch rendering in profiles
  * fixes non-modal dialog UI hangs (PID dialog, messages, error, largeLCDs, serial, platform, calculator)
  * fixes Fuji PXR reading of times on "Read Ra/So values"

----
v0.9.6 (July 20, 2015)
------------------

* FIXES
  * fixed translations
  * fixed accent processing in extra background profile names
  * tolerate spaces in sequenced command actions
  * a further fix to a redraw bug introduced in v0.9.4
  * fixed Linux and Windows build setup

----
v0.9.5 (July 6, 2015)
------------------

* NEW FEATURES
  * adds timestamp to profiles
  * adds batch counter
  * adds exporting and importing of application settings (experimental!)
  * restricts Hottop control to "super-user" mode
  * adds Hottop BT=212C safety eject mechanism
* CHANGES
  * more stable Hottop communication via parallel processing
  * "call program" action on Mac OS X and Linux now calls the given script name instead of initiating an "open" action
  * upgrade to Qt5 on Mac OS X
  * performance improvements
* FIXES
  * fixed Yocto build issue on Mac OS X
  * fixed a redraw bug introduced in v0.9.4


**Note**
_This is the last version supporting the Windows Celeron platform and Mac OS X 10.6 (Intel only)_

----
v0.9.4 (June 6, 2015)
------------------

* NEW FEATURES
  * adds alarm table sorting
* CHANGES
  * improved custom event annotation rendering
  * roast report now lists additionally the ET temperature of events
  * updated underlying libs like Python/Qt/PyQt/Matplotlib/.. (Mac OS only)
  * Hottop control mode is active only in super-user mode (right-click on the Timer LCDs)
* FIXES
  * fixed element order in legend
  * fixed WebLCDs
  * fixes to Fuji PXR "RampSoak ON" mechanism


----
v0.9.3 (January 15, 2015)
------------------

* NEW FEATURES
  * adds CENTER304_34
  * adds Phidgets 1051 support
  * adds Hottop KN-8828B-2K+ support
  * display one (selectable) extra curve from the background profile
  * adds asynchronous, but regularly triggered event commands
  * proposes a file name in the file dialog on first save
* CHANGES
  * roast report now lists additionally the ET temperature of events
* FIXES
  * fix unicode handling in CSV import/export
  * slider and button actions with command arguments fixed
  * Mastech MS6514 communication improvements (thanks to eightbit11)
  * Omega HH806AU retry on failure during communication
  * fixes Yocto shared library loading on Windows and improves the reconnect on reset
  * missing quantifiers application on START
  * TC4 "Start PID on CHARGE" now works on consecutive roasts
  * TC4 enable ArduinoTC4_56 and ArduinoTC4_78 extra device use without adding ArduinoTC4_34
  * MODBUS communication improvements


----
v0.9.2 (January 16, 2015)
------------------

* NEW FEATURES
  * configurable commands on ON, OFF and per sampling interval
  * command sequencing using the semicolon as delimiter
  * adds MODBUS read, wcoil, wcoils commands and last result substitution variable accessible via the underline character
  * adds [HukyForum.com](http://www.hukyforum.com/index.php) image export
* FIXES
  * fixes color dialog for extra devices on OS X
  * fixes a potential crash caused by x-axis realignment during sampling
  * fixes communication issues with Phidgets especially in remote mode via an SBC
  * fixes WebLCD startup issues on slow Windows machines
  * fixes MODBUS over UDP/TCP IPv6 issues on Windows

----
v0.9.1 (Januay 3, 2015)
-----------------

* NEW FEATURES
  * adds QR code for WebLCD URL
  * adds keyboard short cut to retrieve readings from a serial scale (press ENTER in roast properties weight-in/out fields or volume calculator field)
  * adds support for the acaia BT coffee scale
  * adds serial scale support to Volume Calculator
  * adds tare support to Volume Calculator
* CHANGES
  * changes x-axis minor ticks to one minute distance
  * Python updated to v2.7.9
  * Italian translations update
* FIXES
  * fixes Arduino/TC4 temperature units
  * fixes button value restoring on palette load
  * fixes Volume Calculator unit conversion


----
v0.9.0 (November 17, 2014)
-------------------

* NEW FEATURES
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
  * adds quick custom event keyboard shortcuts (keys q-w-e-r followed by 3 digits)
  * file from which alarms were loaded is now displayed in the alarms dialog
  * extends phases lcds by Rao's style ratios and BT deltas
  * adds MET calculation (maximum ET between TP and DROP)
  * adds moisture of roasted beans to roast properties
  * background title as subtitle
  * adds flag to align of background profiles also w.r.t. FCs
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
* CHANGES
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
* FIXES
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
v0.8.0 (May 25, 2014)
-------------------

* NEW FEATURES
  * adds Mastech MS6514 support
  * adds Phidget IO support (eg. 1018 or SBC)
  * adds Phidget remote support (eg. via SBC)
  * adds Arduino TC4 PID support
* CHANGES
  * increased Arduino TC4 default serial baud rate from 19200 to 115200 to match the TC4 Firmware aArtisan v3.00
  * saves autosave path and Volume/Weight/Density units to app settings
  * roast profile data table and events value display respect decimal places settings
  * improved extra device handling on profile loading
  * simplified statistics line
  * updates libraries (Qt, PyQt, numpy, scipy)
  * do not load alarms from background profiles
* FIXES
  * fixes keyboard mode on reset
  * fixes multiple event button action
  * fixes mixup of alarm table introduced in 0.7.5


----
v0.7.5 (April 6, 2014)
-------------------

* NEW FEATURES
  * adds Phidgets 1048 probe type configuration
  * adds event quantifiers
  * adds CM correlation measure between fore- and background profile to statistics bar
  * adds symbolic variables for background temperatures for symbolic assignments
  * adds xy scale toggle via key d
  * adds modbus temperature mode per channel
  * adds Modbus/Fuji merger
* CHANGES
  * increased resolution of temperatures in profiles to two digits
  * updated Modbus lib (slightly faster)
* FIXES
  * improved serial communication
  * fixed extra event manual entry to allow digits
  * adds security patch
  * fixed background profile color selection
  * font fix for OS X 10.9


----
v0.7.4 (January 13, 2014)
-------------------

* FIXES
  * fixes ETBT swap functionality


----
v0.7.3 (January 12, 2014)
-------------------

* NEW FEATURES
  * adds oversampling
  * adds support for floats to the Modbus write command
* CHANGES
  * improved curve and RoR smoothing
  * improved autoCharge/autoDrop recognizer
  * updated Phidget library


----
v0.7.2 (December 19, 2013)
-------------------

* CHANGES
  * beep after an alarm trigger if sound is on and beep flag is set
  * autosave with empty prefix takes roast name as prefix if available
  * external program path added to program settings
* FIXES
  * fixed always active min/max filter
  * spike filter improvements
  * fixes time axis labels on CHARGE
  * fixed alarm trigger for button 1
  * improved autoCHARGE and autoDROP recognizers
  * fixes minieditor event type handling
  * fixes and improvements to RoastLogger import
  * makes the extra serial ports widget editable


----
v0.7.1 (December 2, 2013)
-------------------

* FIXES
  * fixes lockup on extra device use
  * fixes redraw artifact on axis changes
  * fixes minieditor navigation
  * fixes early autoDRY and autoFCs
  * fixes extra lines drawing


----
v0.7.0 (November 30, 2013)
-------------------

* NEW FEATURES
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
    * imports alarms from RoastLogger profiles (thanks to Miroslav)
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
* CHANGES
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
* FIXES
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
  * fixes the RoastLogger import of latin1 encoded files
  * PID LCD visibility
  * scan for ports on Linux
  * better error handling on exporting data
  * improved sample time accuracy
  * fixes wrong segment 4 soak time reported by "Read RS values"
  * updates translations (JP, NL)


----
v0.6.0 (June 14, 2013)
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
  * changed file extension of profiles from `.txt` to `.alog`
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
v0.5.6 (November 8, 2012)
------------------

* based on r787 (with modbus support removed)
* added support for Voltcraft K201 and fixed CENTER 301
* bug fixes

**NOTE**
_This is the last version supporting Mac OS X 10.4 and 10.5 (on Intel and PCC)_

----
v0.5.5 (September 28, 2011)
------------------

* fixes ArdruinoTC4 extra devices
* fixed autoDrop recognition
* fixes serial settings for extra devices

----
v0.5.4 (August 28, 2011)
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
v0.5.3 (July 30, 2011)
------------------
* improves performance of push buttons
* adds device external-program
* adds trouble shooting serial log
* fixes Linux Ubuntu and other bugs

----
v0.5.2 (July 23, 2011)
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
v0.5.1 (June 18, 2011)
------------------

* bug fixes

----
v0.5.0 (June 10, 2011)
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
v0.5.0b2 (June 4, 2011)
--------------------

* improved cupping graphs
* improved performance in multi-core CPUs
* bug fixes

----
v0.5.0b1 (May 28, 2011)
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
v0.4.1 (April 13, 2011)
------------------

* import of CSV is not limited anymore to filenames with "csv" extension
* improved VA18B support
* Windows binary includes the language translations that were missing in v0.4.0

----
v0.4.0 (April 10, 2011)
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
v0.3.4 (February 28, 2011)
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
v0.3.3 (February 13, 2011)
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
v0.3.2 (January 31, 2011)
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
v0.3.1 (January 12, 2011)
-------------------

 * fixed issue on loading the user's application preferences

----
v0.3.0 (January 11, 2011)
-------------------

* fixed occasional ET/BT swap
* fixed issues w.r.t. accent characters
* added OS X 10.5.x support for Intel-only
* new file format to store profiles
* added configurable min/max values for x/y axis
* added alignment of background profile w.r.t. CHARGE during roast
* added DeltaBT/DeltaET flags
* added "green Flag" button on Windows
* reorganized dialogs and menus
* added new HUD mode
* smaller changes and additions

----
v0.2.1 (January 2, 2011)
-------------------

* bug fixes

----
v0.2.0 (December 31, 2010)
-------------------

* added support for
 * CENTER 300, 301, 302, 303, 304, 305, 306
 * VOLTCRAFT K202, K204, 300K, 302KJ
 * EXTECH 421509
* bug fixes

----
v0.1.0 (December 20, 2010)
-------------------
* Initial release
====
