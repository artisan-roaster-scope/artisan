---
layout: single
permalink: /devices/modbus/
title: "MODBUS"
excerpt: "ASCII/RTU/TCP/UDP"
header:
  overlay_image: /assets/images/modbus-logo.jpg
  image: /assets/images/modbus-logo.jpg
  teaser: assets/images/modbus-logo.jpg
modified: 2016-04-18T16:39:37-04:00
---

Artisan supports all variants of the MODBUS protocol.

* MODBUS Serial ASCII
* MODBUS Serial Binary
* MODBUS Serial RTU
* MODBUS TCP
* MODBUS UDP

It can be configured to read registers via MODBUS functions 1, 2, 3 and 4 for up to 6 data channels. See the posts [Modbus RTU](https://artisan-roasterscope.blogspot.it/2013/03/modbus-rtu.html) and [More Modbus](https://artisan-roasterscope.blogspot.it/2013/05/more-modbus.html) for configuration details.

Integer divisions by 10 and 100 as well as the decode of float and BCD encodings are supported. Bytes and words are can be big or little endian ordered.

PID mechanism of external devices can be connected via MODBUS to the Artisan PID controls (see the post on [PID support](https://artisan-roasterscope.blogspot.it/2016/11/pid-control.html) for details).

Buttons and sliders can send out `MODBUS Command`s via MODBUS function 5, 6, 15, 16 and 22. The following commands in the action description are supported.


* `write([slaveId,register,value],..,[slaveId,register,value])`:
write register via MODBUS function 6 (int) or function 16 (float)
* `wcoil(slaveId,register,<bool>)`:
write coil via MODBUS function 5
* `wcoils(slaveId,register,[<bool>,..,<bool>])`: write coils via MODBUS function 15
* `mwrite(slaveId,register,andMask,orMask)`: mask write register via MODBUS function 22
* `writem(slaveId,register,value)` and `writem(slaveId,register,[<int>,..,<int>])`:
write multiple holding registers via MODBUS function 16
* `writeBCD([s,r,v],..,[s,r,v])`: write multiple holding registers BCD encoded via MODBUS function 16