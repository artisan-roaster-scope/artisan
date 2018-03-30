---
layout: single
permalink: /devices/yoctopuce/
title: "Yoctopuce"
excerpt: "PT100/Thermocouple"
header:
  overlay_image: /assets/images/yoctopuce-logo.png
  image: /assets/images/yoctopuce-logo.png
  teaser: assets/images/yoctopuce-logo.png
modified: 2016-04-18T16:39:37-04:00
---

Artisan supports both, the Yocto Thermocouple and the Yocto PT100. Both connect directly via USB and do not need the installation of any additional driver.

Artisan can access Yoctopuce devices connected to a [VirtualHub](https://www.yoctopuce.com/EN/virtualhub.php) from remote via a network connection. Just enter the IP address of the virtual hub under menu `Config >> Device, Yoctopuce tab`.

Yoctopuce devices can be configured and tested using the [VirtualHub](https://www.yoctopuce.com/EN/virtualhub.php).

## [Yocto Thermocouple](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-thermocouple)

The Yocto Thermocouple offers two TC inputs supporting  J, K, E, N, R, S and T type thermocouples.

## [Yocto PT100](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-pt100)

The Yocto-PT100 can be used with PT100 probes using 2, 3 or 4 wires. The type of connection is setup in software. To reach the highest precision, a 4-wires probe should be used. 3-wires probes are reasonably precise and not too much affected by wire lengths, contrarily to 2-wires probes which are the least precise and very sensitive to wire length. 

The Yocto-PT100 features a built-in galvanic isolation between the USB control part and the PT100 measure circuit. It is therefore possible to use non-isolated PT100 probes, which are often more reactive and less expensive.