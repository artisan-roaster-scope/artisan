---
layout: single
permalink: /devices/phidgets/
title: "Phidgets"
excerpt: "Various modules"
header:
  overlay_image: /assets/images/phidgets-logo.jpg
  image: /assets/images/phidgets-logo.jpg
  teaser: assets/images/phidgets-logo.jpg
modified: 2016-04-18T16:39:37-04:00
---
Artisan supports a large number of Phidgets that gather temperature and other data. It also supports Phidgets that can generate external output triggered by Artisan actions.

All Phidgets can be connected either directly via USB or remotely via network connection by using a [Phidgets SBC](http://www.phidgets.com/products.php?category=21&product_id=1073_0) as gateway.

There are Phidgets that feature a direct USB connection as well as the more recent [VINT Phidgets](https://www.phidgets.com/docs/What_is_VINT%3F) that are connected via a VINT USB hub to the USB port. Some are electrically isolated and thus more resistant against electrical noise.

Any number of Phidgets, of one type or mixed types, can be used in combination with any of the other supported devices.

The use of all Phidgets require the installation of the [Phidgets v22 driver](https://artisan-roasterscope.blogspot.de/2017/12/more-phidgets.html).

For more information read the posts [Roasting with Phidgets](https://artisan-roasterscope.blogspot.it/2017/12/roasting-with-phidgets.html) and [More Phidgets!](https://artisan-roasterscope.blogspot.it/2017/12/more-phidgets.html) on the [Artisan blog](https://artisan-roasterscope.blogspot.it/)

# Temperature Input

## Thermocouples

All of these devices support J, K, E and T thermocouples. The type of thermocouples used has to be configured in the Phidgets tab on the Artisan side (menu `Config >> Device, Phidgets tab`).

### 1 Channel

* [Phidget 1051](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=43) (USB)
* [Phidget TMP1100](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=725) (VINT, isolated)

### 4 Channel

* [Phidget IR 1048](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=38) (USB)
* [Phidget TMP1101](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=726) (VINT)

## Resistive Thermal Devices (RTDs)

### 1 Channel

* [Phidget TMP1200](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=968) (VINT)
 
**Watch out!** The TMP1200 supports 2-, 3- and 4-wire PT100 and PT1000 RTDs to be connected directly. The type of RTD used has to be configured on the Artisan side (menu `Config >> Device, Phidgets tab`)
{: .notice--primary}

### 4 Channel

* [Phidget 1046](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=35) (USB)

**Watch out!** The Phidget 1046 requires either a [Voltage Divider](http://www.phidgets.com/docs/3175_User_Guide#Using_a_Voltage_Divider) or a [Wheatstone Bridge](http://www.phidgets.com/docs/3175_User_Guide#Using_a_Wheatstone_Bridge) to connect a RTD). The applied wiring has to be configured within Artisan (menu `Config >> Device, Phidgets tab`)
{: .notice--primary}


## Infrared

Single channel IR with integrated sensor

* [Phidget IR 1045](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=34) (USB)


# Analog/Digital Input/Output

