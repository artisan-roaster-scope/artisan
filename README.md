<img align="right" src="https://raw.githubusercontent.com/MAKOMO/artisan/master/wiki/screenshots/artisan.png">

[Artisan](https://github.com/MAKOMO/artisan/blob/master/README.md) 
==========
Visual scope for coffee roasters

[![Build Status](https://travis-ci.org/artisan-roaster-scope/artisan.svg?branch=master)](https://travis-ci.org/artisan-roaster-scope/artisan)

Build artifacts available at [bintray](https://dl.bintray.com/artisan/artisan-artifacts/).

Summary
-------

Artisan is a software that helps coffee roasters record, analyze, and control roast profiles. When used in conjunction with a thermocouple data logger or a proportional–integral–derivative controller (PID controller), this software can automate the creation of roasting metrics to help make decisions that influence the final coffee flavor.

Donations
---------

This software is open-source and absolutely free, even for commercial use.

If you think Artisan is useful to you, contribute financially to its further development. Send any amount via my [PayPal.Me page](https://www.paypal.me/MarkoLuther). Thanks!

> *Home roasting enthusiasts often donate 10-100.- (in $ or EUR), while small roasting businesses and consultant that use Artisan in their daily work tend to donate 100-300.- (in $ or EUR). For extra tech support, please inquire.*


![](https://github.com/MAKOMO/artisan/blob/master/wiki/screenshots/FZ94-PID-small.png?raw=true)

[Download](https://github.com/MAKOMO/artisan/releases/latest) (Mac/Windows/Linux)



Features
--------
- free for personal and commercial use
- multi-platform (Mac, Windows, and Linux)
- multi-language (English, German, French, Spanish, Portuguese, Swedish, Italian, Arabic, Japanese, Dutch, Norwegian, Finish, Hungarian, Hebrew, Polish, Greek, Turkish, Chinese, Russian, Thai, Indonesian, Korean,..)
- multi-device (manual and automatic logging of roast temperatures via supported devices; see [Device Selection](http://artisan-roasterscope.blogspot.de/2013/06/device-selection.html))
  * [Fuji PXR/PXG 4 & 5 PID](https://www.fujielectric.com/products/instruments/products/controller/top.html)
  * [Delta DTA/DTB PID](http://www.deltaww.com/Products/CategoryListT1.aspx?CID=060405&PID=ALL&hl=en-US)
  * [Modbus](http://artisan-roasterscope.blogspot.de/2013/05/more-modbus.html) Serial ASCII/RTU/Binary, TCP and UDP (known to work with PIDs of Fuji, ENDA, Watlow, meters like myPCLab, as well as several variable frequency drives)
  * Omega HH309, HH506RA, HH802U, HH806AU, HHM28
  * [General Tools DT309DL](https://www.generaltools.com/4-channel-data-logging-k-thermocouple-thermometer)
  * CENTER 300, 301, 302, 303, 304, 305, 306, 309
  * VOLTCRAFT K201, K202, K204, 300K, 302KJ, PL-125-T2, PL-125-T4
  * [EXTECH 755](http://www.extech.com/display/?id=14489) (differential pressure), [EXTECH 421509](http://www.extech.com/display/?id=14239)
  * [Apollo DT301](http://www.ueitest.com/products/temperature-humidity/dt301)
  * [Arduino TC4](http://www.mlgp-llc.com/arduino/public/arduino-pcb.html) with PID support
     - [aArtisan firmware v3.10](https://github.com/greencardigan/TC4-shield/tree/master/applications/Artisan/aArtisan/tags/REL-310) from 1.7.2015 by Jim ([serial commands](https://github.com/greencardigan/TC4-shield/blob/master/applications/Artisan/aArtisan/trunk/src/aArtisan/commands.txt), baudrate: 115200)
     - [aArtisanQ PID 6 firmware](https://github.com/greencardigan/TC4-shield/tree/master/applications/Artisan/aArtisan_PID/branches/aArtisanQ_PID_6) by Brad ([configuration notes](https://github.com/greencardigan/TC4-shield/blob/master/applications/Artisan/aArtisan_PID/tags/REL-aArtisanQ_PID_6_2_3/aArtisanQ_PID/Configuration%20Options.pdf), [serial commands](https://github.com/greencardigan/TC4-shield/blob/master/applications/Artisan/aArtisan_PID/branches/aArtisanQ_PID_6/aArtisanQ_PID/commands.txt), baudrate: 115200)
  * TE VA18B
  * HHM28 multimeter
  * Amprobe TMD-56 (non-wireless)
  * [Phidget IR 1045](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=34)
  * Phidget TC
     - 4x: [1048](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=38), VINT [TMP1101](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=726)
     - 1x: [1051](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=43)
     - 1x isolated: VINT [TMP1100](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=725)
  * Phidget RTD
     - 4x: [1046](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=35) (bridge needed)
     - 1x: VINT [TMP1200](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=968)
  * Phidget IO
      - 8x analog/digital in, 8x digital out: [1010](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=3), [1013](https://www.phidgets.com/?tier=3&prodid=8), [1018](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=18), [1019](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=20), [1073](https://www.phidgets.com/?tier=3&catid=1&pcid=0&prodid=69)
      - 6x analog/digital in, 6x digital out: VINT [HUB0000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=643)
      - 1x 12bit voltage out: VINT [OUT1000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=711)
      - 1x 12bit isolated voltage out: VINT [OUT1001](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=712)
      - 1x 16bit isolated voltage out: VINT [OUT1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=713)
      - 4x 12bit analog out: USB [1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=2)
      - 8x digital out: USB [1017](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=15)
      - 4x digital out: USB [1014](https://www.phidgets.com/?tier=3&prodid=9)
      - 4x digital PWM out: VINT [OUT1100](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=714)
      - 2x analog/digital in, 2x digital out: [1011](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=4)
  * Mastech MS6514
  * Yocto [Thermocouple](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-thermocouple) and [PT100](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-pt100)
  * external program
- and machines
  * [Probat Probatone 2](https://artisan-roasterscope.blogspot.de/2017/06/probat-probatone.html)
  * [Hottop KN-8828B-2K+](http://artisan-roasterscope.blogspot.de/2015/05/hottop-kn-8828b-2k.html)
  * Aillio Bullet R1
- multi-format (import and export of various file formats: HTML, PDF, SVG, CSV, JSON, Omega HH506RA, K202, K204, [RoastLogger](http://roastlogger.co.uk/coffee/roastlogger/roastlogger.htm), [Probat Pilot](http://www.probat-shoproaster.com/en/plants-equipment/control-software/general-features/), [Aillio Bullet R1](https://aillio.com))
- unlimited number of temperature and [virtual curves](https://artisan-roasterscope.blogspot.de/2014/04/virtual-devices-and-symbolic-assignments.html) incl. rate-of-rise curves for ET and BT
- [spike filter](http://artisan-roasterscope.blogspot.de/2013/05/fighting-spikes.html) and [curve smoothing](https://artisan-roasterscope.blogspot.de/2014/01/sampling-interval-smoothing-and-rate-of.html)
- [symbolic expressions](https://artisan-roasterscope.blogspot.de/2016/03/roast-calculus.html)
- Fahrenheit and Celsius support
- logging of roast events like FCs, FCe,.. via tablet-friendly buttons
- [custom event programmable buttons and sliders](http://artisan-roasterscope.blogspot.de/2013/02/events-buttons-and-palettes.html) supporting the [Hottop Roaster Interface](http://artisan-roasterscope.blogspot.de/2013/02/controlling-hottop.html)
- [time and temperature-based alarms](http://artisan-roasterscope.blogspot.de/2013/03/alarms.html) with user defined actions
- head-up-display and projections predicting ET/BT development
- [phases LCDs predicting and counting developments per phase](https://artisan-roasterscope.blogspot.de/2017/02/roast-phases-statistics-and-phases-lcds.html)
- automatic CHARGE/DROP event detection
- [event quantifiers](https://artisan-roasterscope.blogspot.de/2014/04/event-quantifiers.html)
- [template/background profile with playback aid and replay functions for reproduction of roasts](https://artisan-roasterscope.blogspot.de/2017/10/profile-templates.html)
- configurable profile evaluations and statistics
- weight input from digital scales ([Kern](http://www.kern-sohn.com/) and [Acaia](http://acaia.co/))
- color input from color meters (supports for now [Tonino](http://my-tonino.com/))
- cupping editor and graphs
- profile designer and wheel graph editor
- [LargeLCDs and WebLCDs](https://artisan-roasterscope.blogspot.de/2016/03/lcds.html)
- [volume calculator](https://artisan-roasterscope.blogspot.de/2014/11/batch-volume-and-bean-density.html)
- [batch counter](https://artisan-roasterscope.blogspot.de/2015/07/batch-counter.html)
- [roast, production (for tax reporting) and ranking reports](https://artisan-roasterscope.blogspot.de/2016/03/artisan-v099.html)
- [PID-based roast reproduction (follow background mode)](https://artisan-roasterscope.blogspot.de/2016/11/pid-control.html)
- [software PID](https://artisan-roasterscope.blogspot.de/2016/11/pid-control.html)
- [Area under the Curve (AUC)](https://artisan-roasterscope.blogspot.de/2016/11/area-under-curve-auc.html)


Documentation and Support
------------------------
- [Installation](wiki/Installation.md)
- [Artisan Blog](http://artisan-roasterscope.blogspot.de/) ([Overview](https://artisan-roasterscope.blogspot.de/p/contents.html))
- [User Mailing List](https://mailman.ghostdub.de/mailman/listinfo/artisan-user) (you need to subscribe to send and receive messages)
  * NOTES:
     - Only subscribers can send messages to the list. Messages from others are deleted by the system
     - Messages with large attachments (images) will be deleted by the system
- Documentation (written by users)
  * [Documentation on v0.5.x](http://coffeetroupe.com/artisandocs/)
  * [aArtisan/TC4 Driver Installation (PDF)](https://drive.google.com/file/d/0B4HTX5wS3NB2SlRQa1ozNnZ4Uk0/edit?usp=sharing) by John Hannon
  * [Controlling a Hottop Roaster with Artisan: The Basics v6 (PDF)](https://drive.google.com/file/d/0B4HTX5wS3NB2ZGxsTU4tbmtVUmM/edit?usp=sharing) by Barrie Fairley
  * [Artisan - Basic Setup and Tuning Guide (GoogleDocs)](https://docs.google.com/document/d/1eGtztr56t3GFYafTaMvQUDU3YQXK5nOFNcECM-q_WQ8/edit)
  * [Artisan Configurations for Huky and Phidgets 1048](https://drive.google.com/folderview?id=0B4HTX5wS3NB2TFVid0h2TGxBWG8&usp=sharing)  by Susan
    - [What We Know about PHIDGETS (PDF)](https://drive.google.com/file/d/0B4HTX5wS3NB2OWd4bmtMNVpQSWc/view?usp=sharing)
    - [ARTISAN #1 Configure Your Device (PDF)](https://drive.google.com/file/d/0B4HTX5wS3NB2MnRyQ1Z2NmdBWTg/view?usp=sharing)
    - [ARTISAN #2 Configure the Events (PDF)](https://drive.google.com/file/d/0B4HTX5wS3NB2cnNaMDVFbmZqVVk/view?usp=sharing)
    - [ARTISAN #3 Configure the Axes (PDF)](https://drive.google.com/file/d/0B4HTX5wS3NB2X3h4MjE4X3Z3RFE/view?usp=sharing)
    - [ARTISAN #4 Configure Tools Extras (PDF)](https://drive.google.com/file/d/0B4HTX5wS3NB2SmZua2VSd2FjZFE/view?usp=sharing)
  * Hottop USA: [Speaking Alarms for Windows](https://www.hottopusa.com/SayStatic.html)
  * INSTRUCTABLE: [Roast Coffee With Artisan and Phidgets](http://www.instructables.com/id/Roast-Coffee-With-Artisan-and-Phidgets)
- Tutorial Videos (provided by users)
  * [Rick Groszkiewicz](https://www.youtube.com/channel/UCrLDJbbG8c6fO1KXjbDTllw)
    - [YouTube video on Alarms](https://www.youtube.com/watch?v=KLnb8lZwHjE)
    - [YouTube video on Events](https://www.youtube.com/watch?v=614R8i-EoHI)
    - [YouTube video showing a full Hottop/TC4 roast](https://www.youtube.com/watch?v=mE2qdb4qGrc)
  * [A full software PID controlled on a Probatone 5 on Vimeo](https://vimeo.com/193018671)
  * [Hottop KN-8828B-2K+ YouTube tutorial](https://www.youtube.com/watch?v=glyE_6vv-Lo&t=110s) by [roastmasterscoffee](https://www.youtube.com/channel/UCsba_bXJQbqFX06X5xP_7ug)
  * [Hottop KN-8828B-2K+ YouTube tutorial](https://www.youtube.com/watch?v=T0If1ZbxjOI&t=310s) by [NapoHBarista TV](https://www.youtube.com/channel/UC-k4iHzxb8xrLZ2NSlUo8hg)
  * [Setup for TC4](https://www.youtube.com/watch?v=0-Co-pXF2NM) by [Brad](https://www.youtube.com/channel/UCxcEts9cSvi29QrXyt3qvsQ)
  * [TC4 PID Control](https://www.youtube.com/watch?v=ykuUCXhGAC4) by [Brad](https://www.youtube.com/channel/UCxcEts9cSvi29QrXyt3qvsQ)




Version History
---------------

| Version | Date | Comment |
|---------|------|---------|
| v1.2.0 | 21.12.2017 | Adds [replay by temperature](https://artisan-roasterscope.blogspot.de/2017/10/profile-templates.html), support for [Phidgets API v22](https://www.phidgets.com/docs/Operating_System_Support), Phidgets USB devices [USB 1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=2), [1014](https://www.phidgets.com/?tier=3&prodid=9), [1017](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=15) and VINT devices [HUB0000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=643), [TMP1100](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=725), [TMP1101](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=726), [TMP1200](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=968), [OUT1000](https://www.phidgets.com/?view=search&q=OUT1000),[OUT1001](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=712),[OUT1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=713),[OUT1100](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=714), [VOLTCRAFT PL-125-T2](https://www.conrad.de/de/temperatur-messgeraet-voltcraft-pl-125-t2-200-bis-1372-c-fuehler-typ-k-j-kalibriert-nach-werksstandard-ohne-zertifi-1012836.html), as well as the [VOLTCRAFT PL-125-T4](https://www.conrad.de/de/temperatur-messgeraet-voltcraft-pl-125-t4-200-bis-1372-c-fuehler-typ-k-j-kalibriert-nach-werksstandard-ohne-zertifi-1013036.html), improved RoR and dropout handling
| v1.1.0 | 10.06.2017 | Adds [Recent Roast Properties](https://artisan-roasterscope.blogspot.de/2017/06/recent-roast-properties.html), [Aillio Bullet R1](https://aillio.com) profile import and support for [Probat Probatone 2](https://artisan-roasterscope.blogspot.de/2017/06/probat-probatone.html) (last version supporting OS X 10.9, Windows XP/7 and 32bit OS versions)|
| v1.0.0 | 24.02.2017 | Adds [internal software PID](https://artisan-roasterscope.blogspot.de/2016/11/pid-control.html), external MODBUS PID control, Apollo DT301, Extech 755, fast MODBUS RTU, [AUC](https://artisan-roasterscope.blogspot.de/2016/11/area-under-curve-auc.html), RPi build, additional translations, bug fixes and stability improvements |
| v0.9.9 | 14.03.2016 | Adds [batch and ranking reports, batch conversions, follow-background for Fuji PIDs, additional keyboard short cuts, designer improvements, bug fixes](https://artisan-roasterscope.blogspot.de/2016/03/artisan-v099.html) (last version supporting OS X 10.7 and 10.8) |
| v0.9.8 | 21.10.2015 | US weight and volume units, extended [symbolic expressions and plotter](http://artisan-roasterscope.blogspot.de/2015/10/signals-symbolic-assignments-and-plotter.html), [ln()/x^2 approximations](http://artisan-roasterscope.blogspot.de/2015/10/natural-roasts.html), bug fixes |
| v0.9.7 | 29.07.2015 | Bug fixes |
| v0.9.6 | 20.07.2015 | Bug fixes |
| v0.9.5 | 06.07.2015 | [Batch counter](https://artisan-roasterscope.blogspot.de/2015/07/batch-counter.html), app settings export/import, bug fixes (last Windows Celeron and Mac OS X 10.6 version)|
| v0.9.4 | 06.06.2015 | Bug fixes |
| v0.9.3 | 15.05.2015 | Phidget [1051](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=43), [Hottop KN-8828B-2K+](http://artisan-roasterscope.blogspot.de/2015/05/hottop-kn-8828b-2k.html), one extra background curve, bug fixes |
| v0.9.2 | 16.01.2015 | Bug fixes |
| v0.9.1 | 03.01.2015 | [Acaia](http://acaia.co/) scale support, QR code, bug fixes |
| v0.9.0 | 17.11.2014 | MODBUS ASCII/TCP/UDP, Yocto [Thermocouple](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-thermocouple) and [PT100](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-pt100), Phidget 1045 IR, Phidget 1046 Wheatstone Bridge wiring, Phidgets async mode, Polish translations, [LargeLCDs, WebLCDs](https://artisan-roasterscope.blogspot.de/2016/03/lcds.html), 2nd set of roast phases, [volume calculator](https://artisan-roasterscope.blogspot.de/2014/11/batch-volume-and-bean-density.html), moisture loss and organic loss, container tare, RoR delta span, [phasesLCDs showing Rao's development ratio](https://artisan-roasterscope.blogspot.de/2017/02/roast-phases-statistics-and-phases-lcds.html) |
| v0.8.0 | 25.05.2014 | Phidget IO, Phidget remote, Arduino TC4 PID, Mastech MS6514 |
| v0.7.5 | 06.04.2014 | Bug fixes |
| v0.7.4 | 13.01.2014 | Bug fixes |
| v0.7.3 | 12.01.2014 | Bug fixes |
| v0.7.2 | 19.12.2013 | Bug fixes |
| v0.7.1 | 02.12.2013 | Bug fixes |
| v0.7.0 | 30.11.2013 | Phidget 1046/1048, phases LCDs, xkcd style, extended alarms, [Tonino](http://my-tonino.com/) support |
| v0.6.0 | 14.06.2013 | Monitoring-only mode, sliders, extended alarms, [Modbus RTU](http://artisan-roasterscope.blogspot.de/2013/05/more-modbus.html), Amprobe TMD-56, [spike filter](http://artisan-roasterscope.blogspot.de/2013/05/fighting-spikes.html), additional localizations |
| v0.5.6 | 08.11.2012 | Bug fixes  (last Mac OS X 10.4/10.5 version) |
| v0.5.2 | 23.07.2011 | Delta DTA PID support, automatic CHARGE/DROP |
| v0.5.0 | 10.06.2011 | HHM28, wheel graph, math plotter, multiple and [virtual devices, symbolic expressions](https://artisan-roasterscope.blogspot.de/2014/04/virtual-devices-and-symbolic-assignments.html), [custom buttons](http://artisan-roasterscope.blogspot.de/2013/02/events-buttons-and-palettes.html) |
| v0.4.0 | 10.04.2011 | Localization, events replay, [alarms](http://artisan-roasterscope.blogspot.de/2013/03/alarms.html), profile designer |
| v0.3.4 | 28.02.2011 | [Arduino TC4](http://www.mlgp-llc.com/arduino/public/arduino-pcb.html), TE VA18B, delta filter |
| v0.3.3 | 13.02.2011 | Fuji PXR5/PXG5, manual device, keyboard shortcuts, Linux |
| v0.3.0 | 11.01.2011 | New profile file format |
| v0.2.0 | 31.12.2010 | CENTER 300, 301, 302, 303, 304, 305, 306, VOLTCRAFT K202, K204 300K, 302KJ, EXTECH 421509 |
| v0.1.0 | 20.12.2010 | Initial release |

[Detailed Release History](wiki/ReleaseHistory.md)


----
Related Software
----------------
- [RoastLogger](http://roastlogger.co.uk/coffee/roastlogger/roastlogger.htm)
- [RoasterThing](http://www.roasterthing.com)
- [Typica](http://www.randomfield.com/programs/typica/)
- [Roast Monitor](http://coffeesnobs.com.au/RoastMonitor/)

if you need commercial support

- [Cropster](https://www.cropster.com/products/roast/)
- [roastlog](http://roastlog.com)
- [Profiling Dynamics™](http://www.roasterdynamics.com/Profiling_Dynamics.html)
- [Probat Pilot](http://www.probat-shoproaster.com/en/plants-equipment/control-software/general-features/)


----
License
-------

[![](http://www.gnu.org/graphics/gplv3-88x31.png)](http://www.gnu.org/copyleft/gpl.html)
