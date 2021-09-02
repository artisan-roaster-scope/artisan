<img align="right" src="https://raw.githubusercontent.com/artisan-roaster-scope/artisan/master/wiki/screenshots/artisan.png" width="70">

[Artisan](https://artisan-scope.org/) 
==========
Visual scope for coffee roasters

[![Windows/Mac/Linux build](https://img.shields.io/appveyor/ci/roasterdave/artisan.svg?label=Windows/Mac/Linux%20builds)](https://ci.appveyor.com/project/roasterdave/artisan)
[![Latest release](https://img.shields.io/github/release/artisan-roaster-scope/artisan.svg)](https://github.com/artisan-roaster-scope/artisan/releases/latest)
[![Pre-release](https://img.shields.io/github/release-pre/artisan-roaster-scope/artisan.svg)](https://github.com/artisan-roaster-scope/artisan/releases/continuous)
![Github All Releases](https://img.shields.io/github/downloads/artisan-roaster-scope/artisan/total.svg)
![License](https://img.shields.io/github/license/artisan-roaster-scope/artisan.svg)
[![pylint](https://github.com/artisan-roaster-scope/artisan/actions/workflows/pylint.yaml/badge.svg?branch=master&event=push)](https://github.com/artisan-roaster-scope/artisan/actions?query=workflow:pylint+event:push+branch:master)


*WARNING: pre-release builds may not work.  Use at your own risk.*

Summary
-------

Artisan is a software that helps coffee roasters record, analyze, and control roast profiles. When used in conjunction with a thermocouple data logger or a proportional–integral–derivative controller (PID controller), this software can automate the creation of roasting metrics to help make decisions that influence the final coffee flavor.

Donations
---------

This software is open-source and absolutely free, also for commercial use.

If you think Artisan is useful to you, contribute financially to its further development. Send any amount via my [PayPal.Me page](https://www.paypal.me/MarkoLuther). Thanks!

> *Home roasting enthusiasts often donate 10-100.- (in $ or EUR), while small roasting businesses and consultant that use Artisan in their daily work tend to donate 100-300.- (in $ or EUR). For extra tech support, please inquire.*


![](https://github.com/artisan-roaster-scope/artisan/blob/master/wiki/screenshots/artisan-cover.png?raw=true)

[Download](https://github.com/artisan-roaster-scope/artisan/releases/latest) (macOS/Windows/Linux)

[Installation Instructions](https://github.com/artisan-roaster-scope/artisan/blob/master/wiki/Installation.md)

[Documentation](https://artisan-scope.org/docs/)


PLEASE FOLLOW AND TAG US!  
&nbsp;&nbsp;&nbsp;&nbsp;<a href="https://www.facebook.com/ArtisanScope"><img src="https://github.com/artisan-roaster-scope/artisan/blob/master/wiki/screenshots/facebook-square.svg" width="30"></a>&nbsp;&nbsp;&nbsp;<a href="https://www.instagram.com/artisanscope/"><img src="https://github.com/artisan-roaster-scope/artisan/blob/master/wiki/screenshots/instagram-square.svg" width="30"></a>


<a id="version_history"></a>
Version History
---------------


[Detailed Release History](wiki/ReleaseHistory.md)


| Version | Date  | Comment |
|---------|------:|---------|
| [v2.4.6](https://github.com/artisan-roaster-scope/artisan/releases/tag/v2.4.6)  | July&nbsp;30,&nbsp;2021 | Adds [energy and CO2 calculator](https://artisan-roasterscope.blogspot.com/2021/07/tracking-energy-consumption-co2.html), new setups for [Probat UG and G Series machines](https://artisan-scope.org/machines/kirsch/) with control functionality, the new [FZ94 EVO](https://www.coffee-tech.com/products/shop-roasters/fz94-evo/) machine by [Coffee-Tech](https://artisan-scope.org/machines/coffeetech/), as well as machines of [Roastmax](https://artisan-scope.org/machines/roastmax/), [Craftsmith](https://artisan-scope.org/machines/craftsmith/) and [Carmomaq](https://artisan-scope.org/machines/roastmax/), updates [Giesen setups](https://artisan-scope.org/machines/giesen/) to control additional actors on larger machines, adds support for the [Yoctopuce modules Yocto-0-10V-Rx, Yocto-milliVolt-Rx and Yocto-Serial](https://artisan-scope.org/devices/yoctopuce/), extends Chinese and Spanish translations and adds translations for Vietnamese, Danish, Lativian, Slovak and Scottish.|
| [v2.4.4](https://github.com/artisan-roaster-scope/artisan/releases/tag/v2.4.4)  | Dec 14, 2020 | Adds machine setups for the [Nordic PLC](https://artisan-scope.org/machines/nordic/), [Fabrica Roasters](https://artisan-scope.org/machines/fabrica/) and [MCR Series in C](https://artisan-scope.org/machines/mcr/), importers for [Rubase](https://rubasseroasters.com/) and [Aillio](https://aillio.com/) RoastWorld, as well as PID Ramp/Soak pattern actions and templates (last version supporting Raspbian Stretch) |
| [v2.4.2](https://github.com/artisan-roaster-scope/artisan/releases/tag/v2.4.2)  | Oct&nbsp;2,&nbsp;2020 | Adds [support for machines of over 40 brands](https://artisan-scope.org/machines/index) including the [Probat PIII series](https://www.probat.com/en/products/shoproaster/produkte/roasters/p-series-probatino/), [IKAWA v3 CSV](https://www.ikawacoffee.com/) and [RoastLog profile](https://roastlog.com/) import,  "[Source Han Sans](https://en.wikipedia.org/wiki/Source_Han_Sans)" and "[WenQuanYi Zen Hei](https://en.wikipedia.org/wiki/WenQuanYi)" font options providing complete Chinese, Korean and Japanese character sets, sliders Bernoulli mode, and [WebSocket communication](https://artisan-scope.org/devices/websockets/) (last version supporting macOS 10.13 and 10.14) |
| [v2.4.0](https://github.com/artisan-roaster-scope/artisan/releases/tag/v2.4.0) | Jun 3, 2020 | Adds [Roast Comparator](https://artisan-roasterscope.blogspot.com/2020/05/roast-comparator.html), [Roast Simulator](https://artisan-roasterscope.blogspot.com/2020/05/roast-simulator.html), and [Profile Transposer](https://artisan-roasterscope.blogspot.com/2020/05/profile-transposer.html), Cropster, IKAWA and Giesen Software profile import, flexible [automatic file name generator](https://artisan-roasterscope.blogspot.com/2020/05/autosave-file-naming.html), [special event annotations](https://artisan-roasterscope.blogspot.com/2020/05/special-events-annotations.html), large PhasesLCDs, support for [Twino/Ozstar roasting machines](https://artisan-scope.org/machines/twino-ozstar/) and the [Giesen IR sensor](https://artisan-scope.org/machines/giesen/), S7 and MODBUS protocol optimizations and extensions, support for additional Phidgets and Yoctopuce IO modules |
| [v2.1.2](https://github.com/artisan-roaster-scope/artisan/releases/tag/v2.1.2)  | Dec&nbsp;24,&nbsp;2019 | Bug fixes |
| [v2.1.1](https://github.com/artisan-roaster-scope/artisan/releases/tag/v2.1.1)  | Nov&nbsp;29,&nbsp;2019 | Bug fixes |
| [v2.1.0](https://github.com/artisan-roaster-scope/artisan/releases/tag/v2.1.0) | Nov&nbsp;26,&nbsp;2019 | Adds [profile analyzer](https://artisan-roasterscope.blogspot.com/2019/11/analyzer.html), [extended symbolic formulas](https://artisan-roasterscope.blogspot.com/2019/11/symbolic-formulas-basics-new-variables.html), [background images](https://artisan-roasterscope.blogspot.com/2019/11/background-images.html), forward looking alarms and alarms triggered by temperature differences, support for the [Atilla](https://www.atilla.com.br/) GOLD plus 7" II, the [Besca Bee sample roaster](https://www.bescaroasters.com/roaster-detail/14/Sample-Roasters/Besca-Bee-Coffee-Roaster), additional [Coffed](https://coffed.pl/en) machines (SR3/5/15/25/60), [Coffeetool Rxx](https://coffeetool.gr/product-category/coffeeroasters/) machines with control, and [popular Phidget sets](https://artisan-scope.org/devices/phidget-sets/) (incl. the one featured in [On Idle Noise](https://artisan-roasterscope.blogspot.com/2019/03/on-idle-noise.html)) |
| [v2.0.0](https://github.com/artisan-roaster-scope/artisan/releases/tag/v2.0.0)  | Jun&nbsp;4,&nbsp;2019 | New icon and new look! Adds support for the [artisan.plus](https://artisan.plus/) inventory management service, [Coffee-Tech Engineering Silon ZR7](https://www.coffee-tech.com/products/shop-roasters/silon-zr-7-shop-roaster/), [Has Garanti HGS and HSR series](http://www.hasgaranti.com.tr/en/products/shop-type-products/shop-type-roasting-coffee-machine.html), [Kaldi Fortis](https://eng.homecaffe.net/product/kaldi-fortis-grande-coffee-roaster/126/category/223/display/1/), and the forthcoming [Behmor 1kg](https://behmor.com/jake-kilo-roaster/) |
| [v1.6.2](https://github.com/artisan-roaster-scope/artisan/releases/tag/v1.6.2) | Mar&nbsp;20,&nbsp;2019 | Enables communication with Phidgets under the Mac OS X 10.14 security framework |
| [v1.6.1](https://github.com/artisan-roaster-scope/artisan/releases/tag/v1.6.1) | Mar&nbsp;10,&nbsp;2019 | Adds support for the [Sedona Elite 2in1 roaster](http://www.buckeyecoffee.com/sedona-elite-roasters.html), the [Probat Roaster Middleware](https://www.probat.com/en/products/shoproaster/produkte/roasters/probatone-series/), the [Aillio R1](https://aillio.com/) v2 firmware incl. the new [IBTS IR sensor](https://medium.com/@aillio/the-start-of-something-39aa01d08fa9), the Phidgets [REL1000](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=966), [REL1100](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=720), [REL1101](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=721), and [DAQ1400](https://www.phidgets.com/?tier=3&catid=49&pcid=42&prodid=961), the Phidget RC Servo API ([Phidget RCC 1000](https://www.phidgets.com/?tier=3&catid=21&pcid=18&prodid=1015), [Phidget 1061](https://www.phidgets.com/?tier=3&catid=21&pcid=18&prodid=1032), and [Phidget 1066](https://www.phidgets.com/?tier=3&catid=21&pcid=18&prodid=1044)), the [Yocotopuce Meteo](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-meteo-v2) ambient sensor and the [Yocotopuce IR](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-temperature-ir) module, adds Brazilian portuguese translations and updated French translations |
| [v1.5.0](https://github.com/artisan-roaster-scope/artisan/releases/tag/v1.5.0)  | Oct&nbsp;17,&nbsp;2018 | Adds ArtisanViewer mode, Phidgets IO VoltageRatio, Program 78 and Program 910 devices, and support for manual [Besca roasting machines](https://www.bescaroasters.com/) |
| [v1.4.0](https://github.com/artisan-roaster-scope/artisan/releases/tag/v1.4.0) | Oct&nbsp;3,&nbsp;2018 | Adds time guide, additional PhasesLCD configurations, export/convert to Excel and import/export to Probat Pilot v1.4, channel tare, playback DROP event, always ON mode, support for ambient data and Phidget ambient sensors [HUM1000](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=644) and [PRE1000](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=719), [PID P-on-Measurement/Input mode](http://brettbeauregard.com/blog/2017/06/introducing-proportional-on-measurement/), improved curve smoothing, machine support for [Atilla GOLD plus 7"](http://www.atilla.com.br/p/atilla-5kg-gold-plus/), [Besca roasting machines](https://www.bescaroasters.com/), [Coffee-Tech Engineering Ghibli](https://www.coffee-tech.com/products/commercial-roasters/ghibli-r15/) and [Diedrich Roasters](https://www.diedrichroasters.com/)
| [v1.3.1](https://github.com/artisan-roaster-scope/artisan/releases/tag/v1.3.1) | May&nbsp;20,&nbsp;2018 | Adds support for [Fuji PID PXF](https://www.fujielectric.com/products/instruments/products/controller/PXF.html) |
| [v1.3.0](https://github.com/artisan-roaster-scope/artisan/releases/tag/v1.3.0) | Apr&nbsp;15,&nbsp;2018 | Adds Siemens S7 support, MODBUS BCD decode, color themes, extraction yield calculator, support for machines of [Aillio](https://aillio.com/), [BC Roasters](http://www.buckeyecoffee.com/), [Bühler](http://www.buhlergroup.com/), [Coffed](http://coffed.pl/), [Coffee-Tech](https://www.coffee-tech.com/), [Coffeetool](http://coffeetool.gr/), [Giesen](http://www.giesencoffeeroasters.eu/), [IMF](http://www.imf-srl.com/), [K+M](https://www.kirschundmausser.de/), [Loring](https://loring.com/), [Proaster](http://proaster.coffee/), [San Franciscan](http://www.sanfranroaster.com/), [Toper](http://www.toper.com/), [US Roaster Corp](http://www.usroastercorp.com/) |
| [v1.2.0](https://github.com/artisan-roaster-scope/artisan/releases/tag/v1.2.0) | Dec&nbsp;21,&nbsp;2017 | Adds [replay by temperature](https://artisan-roasterscope.blogspot.de/2017/10/profile-templates.html), support for [Phidgets API v22](https://www.phidgets.com/docs/Operating_System_Support), Phidgets USB devices [USB 1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=2), [1014](https://www.phidgets.com/?tier=3&prodid=9), [1017](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=15) and VINT devices [HUB0000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=643), [TMP1100](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=725), [TMP1101](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=726), [TMP1200](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=968), [OUT1000](https://www.phidgets.com/?view=search&q=OUT1000),[OUT1001](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=712), [OUT1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=713), [OUT1100](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=714), [VOLTCRAFT PL-125-T2](https://www.conrad.de/de/temperatur-messgeraet-voltcraft-pl-125-t2-200-bis-1372-c-fuehler-typ-k-j-kalibriert-nach-werksstandard-ohne-zertifi-1012836.html), as well as the [VOLTCRAFT PL-125-T4](https://www.conrad.de/de/temperatur-messgeraet-voltcraft-pl-125-t4-200-bis-1372-c-fuehler-typ-k-j-kalibriert-nach-werksstandard-ohne-zertifi-1013036.html), improved RoR and dropout handling  (last version supporting Mac OS X 10.12 and Linux glibc 2.17; first version requiring the Phidget v22 driver)|
| [v1.1.0](https://github.com/artisan-roaster-scope/artisan/releases/tag/v1.1.0) | Jun&nbsp;10,&nbsp;2017 | Adds [Recent Roast Properties](https://artisan-roasterscope.blogspot.de/2017/06/recent-roast-properties.html), [Aillio Bullet R1](https://aillio.com) profile import and support for [Probat Probatone 2](https://artisan-roasterscope.blogspot.de/2017/06/probat-probatone.html) (last version supporting OS X 10.9, Windows XP/7 and 32bit OS versions; last version supporting the Phidget v21 driver)|
| [v1.0.0](https://github.com/artisan-roaster-scope/artisan/releases/tag/v1.0.0) | Feb&nbsp;24,&nbsp;2017 | Adds [internal software PID](https://artisan-roasterscope.blogspot.de/2016/11/pid-control.html), external MODBUS PID control, Apollo DT301, Extech 755, fast MODBUS RTU, [AUC](https://artisan-roasterscope.blogspot.de/2016/11/area-under-curve-auc.html), RPi build, and additional translations |
| [v0.9.9](https://github.com/artisan-roaster-scope/artisan/releases/tag/v0.9.9) | Mar&nbsp;14,&nbsp;2016 | Adds [batch and ranking reports, batch conversions, follow-background for Fuji PIDs, additional keyboard short cuts, and designer improvements](https://artisan-roasterscope.blogspot.de/2016/03/artisan-v099.html) (last version supporting OS X 10.7 and 10.8) |
| [v0.9.8](https://github.com/artisan-roaster-scope/artisan/releases/tag/v0.9.8) | Oct&nbsp;21,&nbsp;2015 | Adds US weight and volume units and extended [symbolic expressions and plotter](http://artisan-roasterscope.blogspot.de/2015/10/signals-symbolic-assignments-and-plotter.html), [ln()/x^2 approximations](http://artisan-roasterscope.blogspot.de/2015/10/natural-roasts.html) |
| [v0.9.7](https://github.com/artisan-roaster-scope/artisan/releases/tag/v0.9.7) | Jul&nbsp;29,&nbsp;2015 | Bug fixes |
| [v0.9.6](https://github.com/artisan-roaster-scope/artisan/releases/tag/v0.9.6) | Jul&nbsp;20,&nbsp;2015 | Bug fixes |
| [v0.9.5](https://github.com/artisan-roaster-scope/artisan/releases/tag/v0.9.5) | Jul&nbsp;6,&nbsp;2015 | Adds [Batch counter](https://artisan-roasterscope.blogspot.de/2015/07/batch-counter.html) and app settings export/import (last Windows Celeron and Mac OS X 10.6 version)|
| [v0.9.4](https://github.com/artisan-roaster-scope/artisan/releases/tag/v0.9.4) | Jun,&nbsp;6,&nbsp;2015 | Bug fixes |
| [v0.9.3](https://github.com/artisan-roaster-scope/artisan/releases/tag/v0.9.3) | May&nbsp;15,&nbsp;2015 | Adds Phidget [1051](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=43), [Hottop KN-8828B-2K+](http://artisan-roasterscope.blogspot.de/2015/05/hottop-kn-8828b-2k.html), and one extra background curve |
| [v0.9.2](https://github.com/artisan-roaster-scope/artisan/releases/tag/v0.9.2) | Jan&nbsp;16,&nbsp;2015 | Bug fixes |
| v0.9.1 | Jan, 3, 2015 | Adds [Acaia](http://acaia.co/) scale support and WebLCD QR code |
| v0.9.0 | Nov 17, 2014 | MODBUS ASCII/TCP/UDP, Yocto [Thermocouple](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-thermocouple) and [PT100](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-pt100), Phidget 1045 IR, Phidget 1046 Wheatstone Bridge wiring, Phidgets async mode, Polish translations, [LargeLCDs, WebLCDs](https://artisan-roasterscope.blogspot.de/2016/03/lcds.html), 2nd set of roast phases, [volume calculator](https://artisan-roasterscope.blogspot.de/2014/11/batch-volume-and-bean-density.html), moisture loss and organic loss, container tare, RoR delta span, [phasesLCDs showing Rao's development ratio](https://artisan-roasterscope.blogspot.de/2017/02/roast-phases-statistics-and-phases-lcds.html) |
| v0.8.0 | May&nbsp;25,&nbsp;2014 | Phidget IO, Phidget remote, Arduino TC4 PID, Mastech MS6514 |
| v0.7.5 | Apr&nbsp;6,&nbsp;2014 | Bug fixes |
| v0.7.4 | Jan&nbsp;13,&nbsp;2014 | Bug fixes |
| v0.7.3 | Jan&nbsp;12,&nbsp;2014 | Bug fixes |
| v0.7.2 | Dec&nbsp;19,&nbsp;2013 | Bug fixes |
| v0.7.1 | Dec&nbsp;2,&nbsp;2013 | Bug fixes |
| v0.7.0 | Nov&nbsp;30,&nbsp;2013 | Phidget 1046/1048, phases LCDs, xkcd style, extended alarms, [Tonino](http://my-tonino.com/) support |
| v0.6.0 | Jun&nbsp;14,&nbsp;2013 | Monitoring-only mode, sliders, extended alarms, [Modbus RTU](http://artisan-roasterscope.blogspot.de/2013/05/more-modbus.html), Amprobe TMD-56, [spike filter](http://artisan-roasterscope.blogspot.de/2013/05/fighting-spikes.html), additional localizations |
| v0.5.6 | Nov&nbsp;8,&nbsp;2012 | Bug fixes  (last Mac OS X 10.4/10.5 version) |
| v0.5.2 | Jul&nbsp;23,&nbsp;2011 | Delta DTA PID support, automatic CHARGE/DROP |
| v0.5.0 | Jun&nbsp;10,&nbsp;2011 | HHM28, wheel graph, math plotter, multiple and [virtual devices, symbolic expressions](https://artisan-roasterscope.blogspot.de/2014/04/virtual-devices-and-symbolic-assignments.html), [custom buttons](http://artisan-roasterscope.blogspot.de/2013/02/events-buttons-and-palettes.html) |
| v0.4.0 | Apr&nbsp;10,&nbsp;2011 | Localization, events replay, [alarms](http://artisan-roasterscope.blogspot.de/2013/03/alarms.html), profile designer |
| v0.3.4 | Feb&nbsp;28,&nbsp;2011 | [Arduino TC4](http://www.mlgp-llc.com/arduino/public/arduino-pcb.html), TE VA18B, delta filter |
| v0.3.3 | Feb&nbsp;13,&nbsp;2011 | Fuji PXR5/PXG5, manual device, keyboard shortcuts, Linux |
| v0.3.0 | Jan&nbsp;11,&nbsp;2011 | New profile file format |
| v0.2.0 | Dec&nbsp;31,&nbsp;2010 | CENTER 300, 301, 302, 303, 304, 305, 306, VOLTCRAFT K202, K204 300K, 302KJ, EXTECH 421509 |
| v0.1.0 | Dec&nbsp;20,&nbsp;2010 | Initial release |


----
License
-------

[![](http://www.gnu.org/graphics/gplv3-88x31.png)](http://www.gnu.org/copyleft/gpl.html)
