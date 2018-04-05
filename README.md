<img align="right" src="https://raw.githubusercontent.com/MAKOMO/artisan/master/wiki/screenshots/artisan.png">

[Artisan](https://artisan-scope.org/) 
==========
Visual scope for coffee roasters

[![Linux/Mac build](https://img.shields.io/travis/artisan-roaster-scope/artisan.svg?label=Linux/Mac%20build)](https://travis-ci.org/artisan-roaster-scope/artisan)
[![Windows build](https://img.shields.io/appveyor/ci/rpaulo/artisan.svg?label=Windows%20build)](https://ci.appveyor.com/project/rpaulo/artisan)
[![Bintray binaries](https://img.shields.io/bintray/v/artisan/artisan-artifacts/artisan.svg) ](https://bintray.com/artisan/artisan-artifacts/artisan/master/link#files) 
[![Latest release](https://img.shields.io/github/release/artisan-roaster-scope/artisan.svg)](https://github.com/artisan-roaster-scope/artisan/releases)
![Github All Releases](https://img.shields.io/github/downloads/artisan-roaster-scope/artisan/total.svg)
![License](https://img.shields.io/github/license/artisan-roaster-scope/artisan.svg)

*WARNING: pre-release builds may not work.  Use at your own risk.*

Summary
-------

Artisan is a software that helps coffee roasters record, analyze, and control roast profiles. When used in conjunction with a thermocouple data logger or a proportional–integral–derivative controller (PID controller), this software can automate the creation of roasting metrics to help make decisions that influence the final coffee flavor.

Donations
---------

This software is open-source and absolutely free, also for commercial use.

If you think Artisan is useful to you, contribute financially to its further development. Send any amount via my [PayPal.Me page](https://www.paypal.me/MarkoLuther). Thanks!

> *Home roasting enthusiasts often donate 10-100.- (in $ or EUR), while small roasting businesses and consultant that use Artisan in their daily work tend to donate 100-300.- (in $ or EUR). For extra tech support, please inquire.*


![](https://github.com/MAKOMO/artisan/blob/master/wiki/screenshots/FZ94-PID-small.png?raw=true)

[Download](https://github.com/MAKOMO/artisan/releases/latest) (Mac/Windows/Linux)

[Installation Instructions](https://github.com/artisan-roaster-scope/artisan/blob/master/wiki/Installation.md)


Version History
---------------

| Version | Date | Comment |
|---------|------|---------|
| v1.3.0 | xx.04.2017 | Adds Siemens S7 support, MODBUS BCD decode, color themes, extraction yield calculator, support for machines of [Aillio](https://aillio.com/), [BC Roasters](http://www.buckeyecoffee.com/), [Bühler](http://www.buhlergroup.com/), [Coffed](http://coffed.pl/), [Coffee-Tech](https://www.coffee-tech.com/), [Coffeetool](http://coffeetool.gr/), [Giesen](http://www.giesencoffeeroasters.eu/), [IMF](http://www.imf-srl.com/), [K+M](https://www.kirschundmausser.de/), [Loring](https://loring.com/), [Proaster](http://proaster.coffee/), [San Franciscan](http://www.sanfranroaster.com/), [Toper](http://www.toper.com/), [US Roaster Corp](http://www.usroastercorp.com/)|
| v1.2.0 | 21.12.2017 | Adds [replay by temperature](https://artisan-roasterscope.blogspot.de/2017/10/profile-templates.html), support for [Phidgets API v22](https://www.phidgets.com/docs/Operating_System_Support), Phidgets USB devices [USB 1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=2), [1014](https://www.phidgets.com/?tier=3&prodid=9), [1017](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=15) and VINT devices [HUB0000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=643), [TMP1100](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=725), [TMP1101](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=726), [TMP1200](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=968), [OUT1000](https://www.phidgets.com/?view=search&q=OUT1000),[OUT1001](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=712),[OUT1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=713),[OUT1100](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=714), [VOLTCRAFT PL-125-T2](https://www.conrad.de/de/temperatur-messgeraet-voltcraft-pl-125-t2-200-bis-1372-c-fuehler-typ-k-j-kalibriert-nach-werksstandard-ohne-zertifi-1012836.html), as well as the [VOLTCRAFT PL-125-T4](https://www.conrad.de/de/temperatur-messgeraet-voltcraft-pl-125-t4-200-bis-1372-c-fuehler-typ-k-j-kalibriert-nach-werksstandard-ohne-zertifi-1013036.html), improved RoR and dropout handling  (last version supporting Mac OS X 10.12 and Linux glibc 2.17)|
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
License
-------

[![](http://www.gnu.org/graphics/gplv3-88x31.png)](http://www.gnu.org/copyleft/gpl.html)
