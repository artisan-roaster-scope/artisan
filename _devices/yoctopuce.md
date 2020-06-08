---
layout: single
permalink: /devices/yoctopuce/
title: "Yoctopuce"
excerpt: "PT100/Thermocouple/IR/Meteo/.."
header:
  overlay_image: /assets/images/yoctopuce-logo.png
  image: /assets/images/yoctopuce-logo.png
  teaser: assets/images/yoctopuce-logo.png
---

Artisan supports by now many Yoctopuce devices. Most prominently the Yocto Thermocouple and the Yocto PT100. Both connect directly via USB and do not need the installation of any additional driver. 

Artisan can access Yoctopuce devices connected to a [VirtualHub](https://www.yoctopuce.com/EN/virtualhub.php) from remote via a network connection, via the [YoctoHub-Ethernet](https://www.yoctopuce.com/EN/products/extensions-and-networking/yoctohub-ethernet), a [YoctoHub-Wireless](https://www.yoctopuce.com/EN/products/extensions-and-networking/yoctohub-wireless-n) hub or any other [Yoctopuce networking extension](http://www.yoctopuce.com/EN/products/category/extensions-and-networking). Just enter the IP address of the virtual hub under menu `Config >> Device, Yoctopuce tab`. 

Yoctopuce devices can be configured and tested using the [VirtualHub](https://www.yoctopuce.com/EN/virtualhub.php).

## [Yocto Thermocouple](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-thermocouple)

The Yocto Thermocouple offers two TC inputs supporting  J, K, E, N, R, S and T type thermocouples.

## [Yocto PT100](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-pt100)

The Yocto-PT100 can be used with PT100 probes using 2, 3 or 4 wires. The type of connection is setup in software. To reach the highest precision, a 4-wires probe should be used. 3-wires probes are reasonably precise and not too much affected by wire lengths, contrarily to 2-wires probes which are the least precise and very sensitive to wire length. 

The Yocto-PT100 features a built-in galvanic isolation between the USB control part and the PT100 measure circuit. It is therefore possible to use non-isolated PT100 probes, which are often more reactive and less expensive.


## [Yoctopuce Temperature IR](http://www.yoctopuce.com/EN/products/category/usb-environmental-sensors)

The Yocto IR module features an infrared sensor and communicates as all other Yocto modules via a fast USB connection. The Emissivity factor of the material observed can be configured for this sensor under menu ```Config >> Device```, in the ```Yoctopuce``` tab.


## [Yoctopuce Meteo](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-meteo-v2)

The Yocto Meteo board adds ambient data (temperature, pressure and humidity) automatically to each roast profile. Set the correct MASL for your location under menu Config >> Device, Ambient tab and select this sensor from the popups.


## [Yoctopuce 4-20mA-Rx](https://www.yoctopuce.com/EN/products/usb-electrical-sensors/yocto-4-20ma-rx)

The two channel Yocto-4-20mA-Rx device lets you read values returned by any industrial sensor following the 4-20mA standard.


## [Yoctopuce 0-10V-Tx](https://www.yoctopuce.com/EN/products/usb-electrical-interfaces/yocto-0-10v-tx)

*(support for this module is available in Artisan v2.4.0 and later)*

The Yocto-0-10V-Tx is a USB device with two channels that can generate independent voltages between 0 and 10V, e.g. to control modulating gas valves.

This Yoctopuce output can be activated via `VOUT Command` actions triggered by buttons or sliders configured in the Events tab (menu `Config >> Events`). The following command is supported to set the output voltage of a connected module:

* `vout(c,v[,sn])` : with  
`c` the channel (1 or 2),  
`v` the voltage [0.0-10.0] in V, and the optional argument  
`sn` which specifies either the modules serial number or its logical name (if `sn` is not given, the first module/channel found is addressed).


## [Yoctopuce 4-20mA-Tx](https://www.yoctopuce.com/EN/products/usb-electrical-interfaces/yocto-4-20ma-tx)

*(support for this module is available in Artisan v2.4.0 and later)*

The Yocto-4-20mA-Tx is a USB 4-20mA signal generator, e.g. to control a modulating gas valve.

This Yoctopuce output can be activated via `VOUT Command` actions triggered by buttons or sliders configured in the Events tab (menu `Config >> Events`). The following command is supported to set the output current of a connected module:

* `cout(c[,sn])` : with  
`c` the current [3.0-21.0] in mA, and the optional argument  
`sn` which specifies either the modules serial number or its logical name (if `sn` is not given, the first module found is addressed).

## [Yoctopuce PWM-Tx](https://www.yoctopuce.com/EN/products/usb-electrical-interfaces/yocto-pwm-tx)

*(support for this module is available in Artisan v2.4.0 and later)*

The Yoctopuce PWM module can be controlled via `PWM Command` actions triggered by buttons or sliders configured in the Events tab (menu `Config >> Events`).

The supported commands are:

- `enabled(c,b[,sn])` : PWM running state
- `freq(c,f[,sn])` : PWM frequency
- `duty(c,d[,sn])` : PWM period
- `move(c,d,t[,sn])` : changes progressively the PWM to the specified value over the given time interval

with 

- `c` : the channel (1 or 2)
- `b` : a bool given as 0, 1, False or True
- `f` : the frequency in Hz as an integer [0-1000000]
- `d` : the duty cycle in % as a float [0.0-100.0]
- `t` : the time as an integer in milliseconds
- `sn` : the modules serial number or its logical name


## Yoctopuce Relays

*(support for these modules is available in Artisan v2.4.0 and later)*

The following Yoctopuce relays can be controlled via `IO Command` actions triggered by buttons configured in the Events tab (menu `Config >> Events`). 

- [Yocto-Relay](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-relay): 2x Unipolar Relay, 60VDC, 30VAC r.m.s., 2A
- [Yocto-LatchedRelay](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-latchedrelay): 1x Latched Relay, 60VDC, 8A 
- [Yocto-MaxiCoupler-V2](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-maxicoupler-v2): 8x SSR, 48VDC or 30VAC r.m.s., 1.3A
- [Yocto-PowerRelay-V2](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-powerrelay-v2): 1x relay, 150VAC r.m.s., 5A
- [Yocto-PowerRelay-V3](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-powerrelay-v3): 1x relay, 250VAC r.m.s., 5A
- [Yocto-MaxiPowerRelay](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-maxipowerrelay): 5x relay, 250VAC r.m.s., 5A

The supported commands are:

* `on(c[,sn])` : turn channel c of the relay module on  
* `off(c[,sn])` : turn channel c of the relay module off
* `flip(c[,sn])` : toggle the state of channel c
* `pip(c,delay,duration[,sn])` : pulse the channel c on after a delay of `delay` milliseconds for the duration of `duration` milliseconds

The optional `sn` parameter specifies either the modules serial number or its logical name (if `sn` is not given, the first module found is addressed).

## [Yoctopuce Servo](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-servo)

*(support for this module is available in Artisan v2.4.0 and later)*

The Yoctopuce servo module can be controlled via `RC Command` actions triggered by buttons or sliders configured in the Events tab (menu `Config >> Events`).

The supported commands are:

- `enabled(c,b[,sn])` : enable/disable channel `c` of the servo module with `b` a boolean given as `0` or `1` or `False` or `True`
- `move(c,p[,t][,sn])` : move the servo connected on channel `c` to position `p`. The optional `t` gives the time in ms to arrive at the destination. If not given the servo moves as fast as possible.
- `neutral(c,n[,sn])` : specifies the duration in microseconds of a neutral pulse `n` (0..65000 [us]) for the servo connected on channel `c`
- `range(c,r[,sn])` : specifies the range `r` (0..100%) of the servo connected on channel `c`

The optional `sn` parameter specifies either the modules serial number or its logical name (if `sn` is not given, the first module found is addressed).

Please consult the [Yocto-Servo User's guide](https://www.yoctopuce.com/EN/products/yocto-servo/doc/SERVORC1.usermanual.html) for further information on this API.


