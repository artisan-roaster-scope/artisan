---
layout: single
permalink: /devices/modbus/
title: "MODBUS"
excerpt: "ASCII/RTU/TCP/UDP"
header:
  overlay_image: /assets/images/modbus-logo.jpg
  image: /assets/images/modbus-logo.jpg
  teaser: assets/images/modbus-logo.jpg
---

Artisan supports all variants of the MODBUS protocol.

* MODBUS Serial ASCII
* MODBUS Serial Binary
* MODBUS Serial RTU
* MODBUS TCP
* MODBUS UDP

It can be configured to read registers via functions 1, 2, 3 and 4 for up to 6 data channels. See the posts [Modbus RTU](https://artisan-roasterscope.blogspot.it/2013/03/modbus-rtu.html) and [More Modbus](https://artisan-roasterscope.blogspot.it/2013/05/more-modbus.html) for configuration details.

Integer divisions by 10 and 100 as well as the decode of float and BCD encodings are supported. Bytes and words are can be big or little endian ordered.

PID mechanism of external devices can be connected via MODBUS to the Artisan PID controls (see the post on [PID support](https://artisan-roasterscope.blogspot.it/2016/11/pid-control.html) for details).

Buttons and sliders can send out `MODBUS Command`s via functions 5, 6, 15, 16 and 22. The following commands in the action description are supported.

Note that MODBUS Command actions can be sequenced by separating them with semicolons like in "read(0,10); mwrite(0,20,255,0,_)"

* `read(slaveId,register)`:  
reads <register> from slave <slaveID> using function 3 (Read Multiple Holding Registers). The result is bound to the placeholder `_` and thus can be used in later commands.
* `writeWord([slaveId,register,value],..,[slaveId,register,value])`:  
write register via function 16 (float)
* `write([slaveId,register,value],..,[slaveId,register,value])`:  
write register via function 6 (int) or function 16 (float)
* `wcoil(slaveId,register,<bool>)`:  
write coil via function 5
* `wcoils(slaveId,register,[<bool>,..,<bool>])`:  
write coils via function 15
* `mwrite(slaveId,register,andMask,orMask)`:  
mask write register via function 22
* `mwrite(slaveId,register,andMask,orMask,value)`:  
fake mask write register which evaluates thes masks on the `value` and writes the result using function 6. Together with a previous read to set the temporary variable `_` this can be used to simulate a mask write register (function 22) if the PLC does not support it directly.
* `writem(slaveId,register,value)` and  
`writem(slaveId,register,[<int>,..,<int>])`:  
write multiple holding registers via function 16
* `writeBCD([s,r,v],..,[s,r,v])`:  
write multiple holding registers BCD encoded via function 16
* `sleep(s)` :  
delay processing by `s` seconds (float)
* `button(<b>)` :  
sets the last button pressed to either "pressed" style if `b` is `1` or `True` or "normal"style, otherwise

The placeholders `{BT}`, `{ET}`, `{time}` substituted in MODBUScommand actions by the current bean temperature (BT), environmental temperature (ET) or the time in seconds (float).