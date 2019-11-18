---
layout: single
permalink: /devices/phidgets/
title: "Phidgets"
excerpt: "Various modules"
header:
  overlay_image: /assets/images/phidgets-logo.jpg
  image: /assets/images/phidgets-logo.jpg
  teaser: assets/images/phidgets-logo.jpg
toc: true
toc_label: "On this page"
toc_icon: "cog"
---
Artisan supports a large number of Phidgets that gather temperature and other data. It also supports Phidgets that can generate external output triggered by Artisan actions.

All Phidgets can be connected either directly via USB or remotely via network connection by using a [Phidgets SBC](http://www.phidgets.com/products.php?category=21&product_id=1073_0) as gateway. Phidgets don't need any additional power supply.

There are Phidgets that feature a direct USB connection as well as the more recent [VINT Phidgets](https://www.phidgets.com/docs/What_is_VINT%3F) that are connected via a [VINT USB hub](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=643) to the USB port. Some are electrically isolated and thus more resistant against electrical noise.

Any number of Phidgets, of one type or mixed types, can be used in combination with any of the other supported devices.

**Watch out!** The use of all Phidgets require the installation of the [Phidgets v22 driver](https://artisan-roasterscope.blogspot.de/2017/12/more-phidgets.html).
{: .notice--primary}

For more information read the posts [Roasting with Phidgets](https://artisan-roasterscope.blogspot.it/2017/12/roasting-with-phidgets.html) and [More Phidgets!](https://artisan-roasterscope.blogspot.it/2017/12/more-phidgets.html) on the [Artisan blog](https://artisan-roasterscope.blogspot.it/)

**Watch out!** 
Artisan v2.1 and newer features one-click configurations for the following popular Phidget sets

- [VINT TMP1101 2xTC Set](/devices/phidget-sets#vint-tmp1101-2xtc)
- [VINT TMP1200 2xRTDs Set](/devices/phidget-sets#vint-tmp1200-2xrtd) (low [idle noise](https://artisan-roasterscope.blogspot.com/2019/03/on-idle-noise.html))
- [VINT Ambient Modules Extension](/devices/phidget-sets#vint-ambient-modules)
- USB 1048 Databridge

For all these Phidget sets (but the last one), complete hardware packages are available from the [artisan.plus shop](https://shop.artisan.plus/).
{: .notice--primary}


## 1. Temperature Input

### 1.1 Thermocouples (TCs)

All of these devices support J, K, E and T type thermocouples. The type of thermocouples used has to be configured in the Phidgets tab on the Artisan side (menu `Config >> Device, Phidgets tab`).

#### 1-Channel

* [Phidget 1051](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=43) (USB)
* [Phidget TMP1100](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=725) (VINT, isolated)

#### 4-Channel

* [Phidget 1048](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=38) (USB)
* [Phidget TMP1101](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=726) (VINT)

### 1.2 Resistive Thermal Devices (RTDs)

#### 1-Channel

* [Phidget TMP1200](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=968) (VINT)
 
**Watch out!** The TMP1200 supports 2-, 3- and 4-wire PT100 and PT1000 RTDs to be connected directly. The type of RTD used has to be configured on the Artisan side (menu `Config >> Device, Phidgets tab`)
{: .notice--primary}

#### 4-Channel

* [Phidget 1046](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=35) (USB)

**Watch out!** The Phidget 1046 requires either a [Voltage Divider](http://www.phidgets.com/docs/3175_User_Guide#Using_a_Voltage_Divider) or a [Wheatstone Bridge](http://www.phidgets.com/docs/3175_User_Guide#Using_a_Wheatstone_Bridge) to connect a RTD. The applied wiring has to be configured within Artisan (menu `Config >> Device, Phidgets tab`)
{: .notice--primary}


### 1.3 Infrared

Single channel IR with integrated sensor

* [Phidget IR 1045](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=34) (USB)


## 2. Analog/Digital Input & Output

Artisan can attach to all Phidgets IO ports. The input ports are configured as (extra) devices and are handled as temperature curves. Phidgets output can be activated via `IO Command`, `PWM Command` or `VOUT Command` button or slider actions configured in the Events tab (menu `Config >> Events`). Note that buttons and sliders themself can be triggered autoamtically via alarm actions.

* [Phidget  HUB0000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=643) (VINT HUB): 6x analog/digital in, 6x digital PWM out
* [Phidget OUT1000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=711) (VINT): 1x 12bit voltage out
* [Phidget OUT1001](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=712) (VINT): 1x 12bit isolated voltage out
* [Phidget OUT1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=713) (VINT): 1x 16bit isolated voltage out
* [Phidget OUT1100](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=714) (VINT): 4x digital PWM out
* [REL1000](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=966) (VINT): 4x digital out relays
* [REL1100](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=720) (VINT): 4x digital out 8A SSRs
* [REL1101](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=721) (VINT): 16x PWM-enabled SSRs (only first 4 channels supported)
* [Phidget DAQ1400](https://www.phidgets.com/?tier=3&catid=49&pcid=42&prodid=961) (VINT): 1x versatile input (frequency, current, voltage, digital)
* [Phidget 1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=2) (USB): 4x 12bit analog out
* [Phidget 1011](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=4) (USB): 2x analog/digital in, 2x digital out
* [Phidget 1014](https://www.phidgets.com/?tier=3&prodid=9) (USB): 4x digital out
* [Phidget 1017](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=15) (USB): 8x digital out
* [Phidget 1010](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=3) (USB), [Phidget 1013](https://www.phidgets.com/?tier=3&prodid=8) (USB), [Phidget 1018](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=18) (USB), [Phidget 1019](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=20) (USB), [Phidget 1073](https://www.phidgets.com/?tier=3&catid=1&pcid=0&prodid=69) (USB): 8x analog/digital in, 8x digital out

Each output action supports a number of different commands specified in the `Documentation` field. See the post [More Phidgets!](https://artisan-roasterscope.blogspot.it/2017/12/more-phidgets.html) for details.

## 3. RC Servo Controllers

* [Phidget RCC 1000](https://www.phidgets.com/?tier=3&catid=21&pcid=18&prodid=1015) (16x VINT, ext. powered)
* [Phidget 1061](https://www.phidgets.com/?tier=3&catid=21&pcid=18&prodid=1032) (8x USB, ext. powered)
* [Phidget 1066](https://www.phidgets.com/?tier=3&catid=21&pcid=18&prodid=1044) (1x USB powered) 

## 4. Ambient Sensors

Artisan v1.4 adds support for the following ambient sensors that allow to automatically fill the room temperature, relative humidity and barometric pressure data of roast profiles.

* [Phidget HUM1000](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=644) (VINT): Measure relative humidity from 0 to 100% and temperature from -40°C to +85°C
* [Phidget PRE1000](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=719) (VINT): Measure the absolute air pressures between 50 and 110 kPa