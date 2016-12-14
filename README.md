<img align="right" src="https://raw.githubusercontent.com/MAKOMO/artisan/master/wiki/screenshots/artisan.png">

[Artisan](https://github.com/MAKOMO/artisan/blob/master/README.md) 
==========
Visual scope for coffee roasters


Summary
-------

Artisan is a software that helps coffee roasters record, analyze, and control roast profiles. When used in conjunction with a thermocouple data logger or a proportional–integral–derivative controller (PID controller), this software can automate the creation of roasting metrics to help make decisions that influence the final coffee flavor.

Donations
---------

This software is open-source and absolutely free, even for commercial use.

If you think Artisan is worth of some money and you are willing to contribute financially to its further development, feel free to send any amount through PayPal via this button in EUR

[![](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=N5WW9UN6K669L)

or via my [PayPal.Me page](https://www.paypal.me/MarkoLuther)



![](https://github.com/MAKOMO/artisan/blob/master/wiki/screenshots/FZ94-PID-small.png?raw=true)

[Download](https://github.com/MAKOMO/artisan/releases/latest) (Mac/Windows/Linux)



Features
--------
- free for personal and commercial use
- multi-platform (Mac, Windows, and Linux)
- multi-language (German, French, Spanish, Portuguese, Swedish, Italian, Arabic, Japanese, Dutch, Norwegian, Greek, Turkish, Chinese, Hungarian, Russian, ...)
- multi-device (manual and automatic logging of roast temperatures via supported devices; see blog post [Device Selection](http://artisan-roasterscope.blogspot.de/2013/06/device-selection.html))
  * Fuji PXR/PXG 4 & 5 PID
  * Delta DTA PID (works for DTB too)
  * [Modbus](http://artisan-roasterscope.blogspot.de/2013/05/more-modbus.html) Serial ASCII/RTU/Binary, TCP and UDP (known to work with PIDs of Fuji, ENDA, Watlow, meters like myPCLab, as well as several variable frequency drives)
  * Omega HH309, HH506RA, HH802U, HH806AU, HHM28
  * General Tools DT309DL
  * CENTER 300, 301, 302, 303, 304, 305, 306, 309
  * VOLTCRAFT K201, K202, K204, 300K, 302KJ
  * EXTECH 755, 421509
  * Apollo DT301
  * [Arduino TC4](http://www.mlgp-llc.com/arduino/public/arduino-pcb.html) with PID
  * TE VA18B
  * HHM28 multimeter
  * Amprobe TMD-56 (non-wireless)
  * Phidgets 1010, 1011, 1018, 1019, 1045, 1046, 1048, 1051, 1073
  * Mastech MS6514
  * Yocto Thermocouple and PT100
  * [Hottop KN-8828B-2K+](http://artisan-roasterscope.blogspot.de/2015/05/hottop-kn-8828b-2k.html)
  * external program
- multi-format (import and export of various file formats: HTML, PDF, SVG, CSV, JSON, Omega HH506RA, K202, K204, [RoastLogger](http://homepage.ntlworld.com/green_bean/coffee/roastlogger/roastlogger.htm))
- unlimited number of temperature and [virtual curves](https://artisan-roasterscope.blogspot.de/2014/04/virtual-devices-and-symbolic-assignments.html) incl. rate-of-rise curves for ET and BT
- [spike filter](http://artisan-roasterscope.blogspot.de/2013/05/fighting-spikes.html) and [curve smoothing](https://artisan-roasterscope.blogspot.de/2014/01/sampling-interval-smoothing-and-rate-of.html)
- [symbolic expressions](https://artisan-roasterscope.blogspot.de/2016/03/roast-calculus.html)
- Fahrenheit and Celsius support
- logging of roast events like FCs, FCe,.. via tablet-friendly buttons
- [custom event programmable buttons and sliders](http://artisan-roasterscope.blogspot.de/2013/02/events-buttons-and-palettes.html) supporting the [Hottop Roaster Interface](http://artisan-roasterscope.blogspot.de/2013/02/controlling-hottop.html)
- [time and temperature-based alarms](http://artisan-roasterscope.blogspot.de/2013/03/alarms.html) with user defined actions
- head-up-display and projections predicting ET/BT development
- phases LCDs predicting and counting developments per phase
- automatic CHARGE/DROP event detection
- [event quantifiers](https://artisan-roasterscope.blogspot.de/2014/04/event-quantifiers.html)
- template/background profile with playback aid for reproduction of roasts
- configurable profile evaluations and statistics
- weight input from digital scales ([Kern](http://www.kern-sohn.com/) and [Acaia](http://acaia.co/))
- color input from color meters (supports for now [Tonino](http://my-tonino.com/))
- cupping editor and graphs
- profile designer and wheel graph editor
- [LargeLCDs and WebLCDs](https://artisan-roasterscope.blogspot.de/2016/03/lcds.html)
- [volume calculator](https://artisan-roasterscope.blogspot.de/2014/11/batch-volume-and-bean-density.html)
- [batch counter](https://artisan-roasterscope.blogspot.de/2015/07/batch-counter.html)
- roast, production (for tax reporting) and ranking reports
- PID-based roast reproduction (follow background mode)
- [software PID](https://artisan-roasterscope.blogspot.de/2016/11/pid-control.html)
- [Area under the Curve (AUC)](https://artisan-roasterscope.blogspot.de/2016/11/area-under-curve-auc.html)


Documentation and Support
------------------------
- [Installation](wiki/Installation.md)
- [Artisan Blog](http://artisan-roasterscope.blogspot.de/)
- [User Mailing List](https://lists.mokelbu.de/listinfo/artisan-user) (you need to subscribe to send and receive messages)
  * NOTE: you will receive a warning on sign up that "the site is not secure". This is because the SSL-certificate to sign up for this list has expired. Just ignore this warning. The sign up and the use of the list IS secure. We currently don't have a way to fix that on the server. Sorry.
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





Version History
---------------

| Version | Date | Comment |
|---------|------|---------|
| v1.0.0 | XX.XX.XXXX | Adds [internal software PID](https://artisan-roasterscope.blogspot.de/2016/11/pid-control.html), external MODBUS PID control, Apollo DT301, Extech 755, fast MODBUS RTU, [AUC](https://artisan-roasterscope.blogspot.de/2016/11/area-under-curve-auc.html), RPi build, bug fixes and stability improvements |
| v0.9.9 | 14.03.2016 | Adds batch and ranking reports, batch conversions, follow-background for Fuji PIDs, additional keyboard short cuts, designer improvements, bug fixes |
| v0.9.8 | 21.10.2015 | US weight and volume units, extended [symbolic expressions and plotter](http://artisan-roasterscope.blogspot.de/2015/10/signals-symbolic-assignments-and-plotter.html), [ln()/x^2 approximations](http://artisan-roasterscope.blogspot.de/2015/10/natural-roasts.html), bug fixes |
| v0.9.7 | 29.07.2015 | Bug fixes |
| v0.9.6 | 20.07.2015 | Bug fixes |
| v0.9.5 | 06.07.2015 | [Batch counter](https://artisan-roasterscope.blogspot.de/2015/07/batch-counter.html), app settings export/import, bug fixes (last Windows Celeron and Mac OS X 10.6 version)|
| v0.9.4 | 06.06.2015 | Bug fixes |
| v0.9.3 | 15.05.2015 | Phidget 1051, [Hottop KN-8828B-2K+](http://artisan-roasterscope.blogspot.de/2015/05/hottop-kn-8828b-2k.html), one extra background curve, bug fixes |
| v0.9.2 | 16.01.2015 | Bug fixes |
| v0.9.1 | 03.01.2015 | [Acaia](http://acaia.co/) scale support, QR code, bug fixes |
| v0.9.0 | 17.11.2014 | MODBUS ASCII/TCP/UDP, Yocto TC and PT100, Phidget 1045 IR, Phidget 1046 Wheatstone Bridge wiring, Phidgets async mode, Polish translations, [LargeLCDs, WebLCDs](https://artisan-roasterscope.blogspot.de/2016/03/lcds.html), 2nd set of roast phases, [volume calculator](https://artisan-roasterscope.blogspot.de/2014/11/batch-volume-and-bean-density.html), moisture loss and organic loss, container tare, RoR delta span, phasesLCDs showing Rao's development ratio |
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
| v0.3.4 | 28.02.2011 | Arduino TC4, TE VA18B, delta filter |
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