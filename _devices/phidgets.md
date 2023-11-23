---
layout: single
permalink: /devices/phidgets/
title: "Phidgets"
excerpt: "Various modules"
header:
  overlay_image: /assets/images/phidgets-logo-plain.jpg
  image: /assets/images/phidgets-logo-plain.jpg
  teaser: assets/images/phidgets-logo-plain.jpg
toc: true
toc_label: "On this page"
toc_icon: "cog"
---
Artisan supports a large number of Phidgets that gather temperature and other data. It also supports Phidgets that can generate external output triggered by Artisan actions.

All Phidgets can be connected either directly via USB or remotely via network connection by using a [Phidgets SBC](http://www.phidgets.com/products.php?category=21&product_id=1073_0){:target="_blank"} as gateway or a [wireless VINT HUB](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=1143){:target="_blank"} like the HUB5000. Most Phidgets don't need any additional power supply.


> **Watch out!**  
> Setting up Artisan for wireless access to Phidgets see below under [5. Remote Access](#remote-access).
{: .notice--primary}

There are Phidgets that feature a direct USB connection as well as the more recent [VINT Phidgets](https://www.phidgets.com/docs/What_is_VINT%3F){:target="_blank"}* that are connected via a [VINT USB hub](https://phidgets.com/?tier=2&catid=64&pcid=57){:target="_blank"} to the USB port. Some are electrically isolated and thus more resistant against electrical noise.

Any number of Phidgets, of one type or mixed types, can be used in combination with any of the other supported devices.

**Watch out!** The use of all Phidgets require the installation of the full [Phidgets v22 driver package](https://www.phidgets.com/){:target="_blank"}. On Linux you might want to setup also the [udev rules](https://www.phidgets.com/docs/OS_-_Linux#Advanced_Information) to allow driver access for non-root users.
{: .notice--primary}

For more information read the posts [Roasting with Phidgets](https://artisan-roasterscope.blogspot.it/2017/12/roasting-with-phidgets.html){:target="_blank"} and [More Phidgets!](https://artisan-roasterscope.blogspot.it/2017/12/more-phidgets.html){:target="_blank"} on the [Artisan blog](https://artisan-roasterscope.blogspot.it/){:target="_blank"}.

> **Watch out!**  
> Artisan v2.1 and newer features one-click configurations for the following popular Phidget sets
>
> - [VINT TMP1101 2x TC Set](/phidgets/2x-tc-set/)
> - [VINT TMP1200 2x RTDs Set](/phidgets/2x-rtd-set/) (low [Idle Noise](https://artisan-> roasterscope.blogspot.com/2019/03/on-idle-noise.html){:target="_blank"})
> - [VINT Ambient Modules Extension](/phidgets/ambient-extension/)
> - USB 1048 Databridge
> 
> For all these Phidget sets (but the last one), ready-to-use hardware packages are available from the > [artisan.plus shop](https://shop.artisan.plus/){:target="_blank"}.
{: .notice--primary}


## 1. Temperature Input

### 1.1 Thermocouples (TCs)

All of these devices support J, K, E and T type thermocouples. The type of thermocouples used has to be configured in the Phidgets tab on the Artisan side (menu `Config >> Device, Phidgets tab`).

#### 1-Channel

* [Phidget 1051](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=43){:target="_blank"} (USB)
* [Phidget TMP1100](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=725){:target="_blank"} (VINT, isolated)

#### 4-Channel

* [Phidget 1048](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=38){:target="_blank"} (USB)
* [Phidget TMP1101](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=726){:target="_blank"} (VINT)

### 1.2 Resistive Thermal Devices (RTDs)

#### 1-Channel

* [Phidget TMP1200](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=968){:target="_blank"} (VINT)
 
**Watch out!** The TMP1200 supports 2-, 3- and 4-wire PT100 and PT1000 RTDs to be connected directly. The type of RTD used has to be configured on the Artisan side (menu `Config >> Device, Phidgets tab`)
{: .notice--primary}

#### 2-Channel

<a name="DAQ1500"></a>
* [Phidget DAQ1500](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=957){:target="_blank"} (VINT)

**Watch out!** The Phidget DAQ1500 requires either a [Voltage Divider](http://www.phidgets.com/docs/3175_User_Guide#Using_a_Voltage_Divider){:target="_blank"} or a [Wheatstone Bridge](http://www.phidgets.com/docs/3175_User_Guide#Using_a_Wheatstone_Bridge){:target="_blank"} to connect a RTD. The applied wiring has to be configured within Artisan (menu `Config >> Device, Phidgets tab`)
{: .notice--primary}

#### 4-Channel

* [Phidget 1046](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=35){:target="_blank"} (USB)

**Watch out!** The Phidget 1046 requires either a [Voltage Divider](http://www.phidgets.com/docs/3175_User_Guide#Using_a_Voltage_Divider){:target="_blank"} or a [Wheatstone Bridge](http://www.phidgets.com/docs/3175_User_Guide#Using_a_Wheatstone_Bridge){:target="_blank"} to connect a RTD. The applied wiring has to be configured within Artisan (menu `Config >> Device, Phidgets tab`)
{: .notice--primary}


### 1.3 Infrared

Single channel IR with integrated sensor

* [Phidget IR 1045](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=34){:target="_blank"} (USB)


## 2. Ambient Sensors

Artisan v1.4 adds support for the following ambient sensors that allow to automatically fill the room temperature, relative humidity and barometric pressure data of roast profiles.

* Phidget [HUM1000](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=644){:target="_blank"} / [HUM1001](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=1179){:target="_blank"} (VINT): Measure relative humidity from 0 to 100% and ambient temperature from -40°C to +85°C
* Phidget [PRE1000](https://www.phidgets.com/?tier=3&catid=64&pcid=57&prodid=719){:target="_blank"} (VINT): Measure the absolute air pressures between 50 and 110 kPa
* Phidget [TMP1000](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=724){:target="_blank"} (VINT): Measure ambient temperature from -40°C to 85°C


## 3. Analog/Digital Input

Artisan can attach to all Phidgets IO ports. The input ports are configured as (extra) devices and are handled as temperature curves. 

* [Phidget 1010](https://phidgets.com/?tier=3&catid=105&pcid=85&prodid=4){:target="_blank"}  
  [Phidget 1013](https://phidgets.com/?prodid=8){:target="_blank"}  
  [Phidget 1018](https://phidgets.com/?tier=3&catid=105&pcid=85&prodid=1198){:target="_blank"}  
  [Phidget 1019](https://phidgets.com/?tier=3&catid=96&pcid=76&prodid=1035){:target="_blank"}  
  [Phidget SBC](https://phidgets.com/?tier=3&catid=64&pcid=57&prodid=969){:target="_blank"} : analog/digital in
	* `Phidget IO 01` : analog input (0-5V), ports 0 & 1
	* `Phidget IO 23` : analog input (0-5V), ports 2 & 3
	* `Phidget IO 45` : analog input (0-5V), ports 4 & 5
	* `Phidget IO 67` : analog input (0-5V), ports 6 & 7
	
	* `Phidget IO Digital 01` : digital input (0 or 1), ports 2 & 3
	* `Phidget IO Digital 23` : digital input (0 or 1), ports 2 & 3
	* `Phidget IO Digital 45` : digital input (0 or 1), ports 4 & 5
	* `Phidget IO Digital 67` : digital input (0 or 1), ports 6 & 7


* [Phidget 1011](https://phidgets.com/?tier=3&catid=105&pcid=85&prodid=4){:target="_blank"}  (2x Analog, 2x Digital)   
	* `Phidget 1011 IO 01` : analog input (0-5V), ports 0 and 1
	* `Phidget 1011 IO Digital 01` : digital input (0 or 1), ports 0 and 1

* [Phidget  HUB0007](https://phidgets.com/?tier=3&catid=64&pcid=57&prodid=1290){:target="_blank"} (VINT HUB): 1x analog/digital in

	* `Phidget HUB IO 0` : analog input (0-5V); attaches only port 0

* [Phidget  HUB0000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=643){:target="_blank"}  
  [Phidget  HUB0001](https://phidgets.com/?tier=3&catid=64&pcid=57&prodid=1202){:target="_blank"}  
  [Phidget  HUB0002](https://phidgets.com/?tier=3&catid=64&pcid=57&prodid=1289){:target="_blank"}   
  [Phidget HUB5000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=1143){:target="_blank"} (VINT HUB): 6x analog/digital in

	* `Phidget HUB IO 0` : analog input (0-5V); attaches only port 0
	* `Phidget HUB IO 01` : analog input (0-5V), ports 0 and 1
	* `Phidget HUB IO 23` : analog input (0-5V), ports 2 and 3
	* `Phidget HUB IO 45` : analog input (0-5V), ports 4 and 5

	* `Phidget HUB IO Digital 0` : digital input (0 or 1); attaches only port 0
	* `Phidget HUB IO Digital 01` : digital input (0 or 1), port 0 and 1
	* `Phidget HUB IO Digital 23` : digital input (0 or 1), port 2 and 3
	* `Phidget HUB IO Digital 45` : digital input (0 or 1), port 4 and 5

* [Phidget DAQ1000](https://phidgets.com/?tier=3&catid=106&pcid=86&prodid=622){:target="_blank"} (VINT): 8x analog in
	* `Phidget DAQ1000 01` : analog input (0-5V), ports 0 and 1
	* `Phidget DAQ1000 23` : analog input (0-5V), ports 2 and 3
	* `Phidget DAQ1000 45` : analog input (0-5V), ports 4 and 5
	* `Phidget DAQ1000 67` : analog input (0-5V), ports 6 and 7

* [Phidget DAQ1200](https://phidgets.com/?tier=3&catid=106&pcid=86&prodid=623){:target="_blank"} (VINT): 4x digital input
	* `Phidget DAQ1200 01` : digital input (0 or 1), ports 0 and 1
	* `Phidget DAQ1200 23` : digital input (0 or 1), ports 2 and 3

* [Phidget DAQ1300](https://phidgets.com/?tier=3&catid=106&pcid=86&prodid=624){:target="_blank"} (VINT): 4x isolated digital input
	* `Phidget DAQ1300 01` : digital input (0 or 1), ports 0 and 1
	* `Phidget DAQ1300 23` : digital input (0 or 1), ports 2 and 3

* [Phidget DAQ1301](https://phidgets.com/?tier=3&catid=106&pcid=86&prodid=625){:target="_blank"} (VINT): 16x digital input (only first 8 channels are supported!)
	* `Phidget DAQ1301 01` : digital input (0 or 1), ports 0 and 1
	* `Phidget DAQ1301 23` : digital input (0 or 1), ports 2 and 3
	* `Phidget DAQ1301 45` : digital input (0 or 1), ports 4 and 5
	* `Phidget DAQ1301 67` : digital input (0 or 1), ports 6 and 7

* [Phidget DAQ1400](https://www.phidgets.com/?tier=3&catid=49&pcid=42&prodid=961){:target="_blank"} (VINT): 1x versatile input (current, digital , frequency, voltage)

	* `Phidget DAQ1400 Current` : current input (A, 20mA max)
	* `Phidget DAQ1400 Digital` : digital input (0 or 1, 24V max)
	* `Phidget DAQ1400 Frequency` : frequency input (hz, 2Mhz max)
	* `Phidget DAQ1400 Voltage` : voltage input (0-5V)


* [Phidget VCP1000](https://phidgets.com/?tier=3&catid=16&pcid=14&prodid=953){:target="_blank"} (VINT): 1x 20-bit ±40V Voltage Input Phidget 
	* `Phidget VCP1000 ` : analog input (±312mV, ±40V)

* [Phidget VCP1001](https://phidgets.com/?tier=3&catid=16&pcid=14&prodid=954){:target="_blank"} (VINT): 1x ±40V Voltage Input Phidget; ±5V 
	* `Phidget VCP1001 ` : analog input (±15V or ±40V) 

* [Phidget VCP1002](https://phidgets.com/?tier=3&catid=16&pcid=14&prodid=955){:target="_blank"} (VINT): 1x ±1V Voltage Input Phidget 
	* `Phidget VCP1002 ` : analog input (±10mV -- ±1V)



## 4. Analog/Digital Output

Artisan can attach to all Phidgets IO ports. Phidgets output can be activated via `IO Command`, `PWM Command` or `VOUT Command` button or slider actions configured in the Events tab (menu `Config >> Events`). Note that buttons and sliders themself can be triggered autoamatically via alarm actions.


* [Phidget  HUB0007](https://phidgets.com/?tier=3&catid=64&pcid=57&prodid=1290){:target="_blank"} (VINT HUB): 1x voltage out
* [Phidget  HUB0000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=643){:target="_blank"}, 
  [Phidget  HUB0001](https://phidgets.com/?tier=3&catid=64&pcid=57&prodid=1202){:target="_blank"}, 
  [Phidget  HUB0002](https://phidgets.com/?tier=3&catid=64&pcid=57&prodid=1289){:target="_blank"},    
  [Phidget HUB5000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=1143){:target="_blank"} (VINT HUB): 6x voltage out
* [Phidget OUT1000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=711){:target="_blank"} (VINT): 1x 12bit voltage out
* [Phidget OUT1001](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=712){:target="_blank"} (VINT): 1x 12bit isolated voltage out
* [Phidget OUT1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=713){:target="_blank"} (VINT): 1x 16bit isolated voltage out
* [Phidget OUT1100](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=714){:target="_blank"} (VINT): 4x digital PWM out
* [REL1000](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=966){:target="_blank"} (VINT): 4x digital out relays
* [REL1100](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=720){:target="_blank"} (VINT): 4x digital out 8A SSRs
* [REL1101](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=721){:target="_blank"} (VINT): 16x PWM-enabled SSRs
* [Phidget 1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=2){:target="_blank"} (USB): 4x 12bit analog out
* [Phidget 1011](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=4){:target="_blank"} (USB): 2x analog/digital in, 2x digital out
* [Phidget 1014](https://www.phidgets.com/?tier=3&prodid=9){:target="_blank"} (USB): 4x digital out
* [Phidget 1017](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=15){:target="_blank"} (USB): 8x digital out
* [Phidget 1010](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=3){:target="_blank"} (USB), [Phidget 1013](https://www.phidgets.com/?tier=3&prodid=8){:target="_blank"} (USB), [Phidget 1018](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=18){:target="_blank"} (USB), [Phidget 1019](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=20){:target="_blank"} (USB), [Phidget 1073](https://www.phidgets.com/?tier=3&catid=1&pcid=0&prodid=69){:target="_blank"} (USB): 8x analog/digital in, 8x digital out

Each output action supports a number of different commands specified in the `Documentation` field. See the post [More Phidgets!](https://artisan-roasterscope.blogspot.it/2017/12/more-phidgets.html){:target="_blank"} for details.


### 4.1 Voltage Output

* Phidget [OUT1000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=711){:target="_blank"}, [OUT1001](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=712){:target="_blank"} and [OUT1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=713){:target="_blank"} (1x VINT)
* Phidget [1002](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=2){:target="_blank"} (4x USB)

Phidget Voltage Output modules can be controlled via `VOUT Command` actions triggered by buttons or sliders configured in the Events tab (menu `Config >> Events`). The following commands are supported:

* `out(ch,v[,sn])` : sets output voltage
* `range(ch,r[,sn])` : sets voltage voltage range (not available on OUT1000)
* `sleep(s)` : delay processing for `s` seconds

with

* `ch` : the channel to be addressed (integer)
* `v` : voltage in V (float), eg. 5.5 for 5.5V
* `s` : sleep time in seconds (float)
*  `r` : voltage range with `r=5` to `[0-5V]` and `r=10` to `[-10,10V]`
* `sn` : optional hub serial number or hub serial number and hub port specifier separated by a colon like in `out(0,5.5,560282)` or `out(0,5.5,560282:2)`. Using a command actions, like in `out(0,5.5)`, without specifying a hub serial number, will attach to the first yet unattached module connected to the hub with the lowest serial number instead. If just a port number is given as in `out(0,5.5,:2)`, the yet unattached module connected to the given port (here 2) of the first hub with the lowest serial number is addressed.

The default voltage range for the OUT1001 and OUT1002 is `[-10,10V]` (`r=10`). The following table summarizes the interplay of `r` and `v`.

| r |  v  | 5V Output | +-10V Output |
|--:|----:|----------:|-------------:|
| 5 | -10 |     --    |     --       |
| 5 |  -5 |     --    |     --       |
| 5 |   0 |     0V    |   -10V       |
| 5 | 2.5 |   2.5V    |     0V       |
| 5 |   5 |     5V    |    10V       |
| 10 | -10 |    0V    |   -10V       |
| 10 |  -5 | 1.25V    |    -5V       |
| 10 |   0 |  2.5V    |     0V       |
| 10 |   5 | 3.75V    |     5V       |
| 10 |  10 |    5V    |    10V       |


### 4.2 Digital Output

* [1014](){:target="_blank"} (4x USB)
* [OUT1100](){:target="_blank"}, [REL1000](){:target="_blank"}, [REL1100](){:target="_blank"}, [REL1101](){:target="_blank"} (4x VINT)
* [1017](){:target="_blank"} (8x USB)
* [1010](){:target="_blank"}, [1013](){:target="_blank"}, [1018](){:target="_blank"}, [1019](){:target="_blank"} (8x USB)

Phidget Digital Output modules can be controlled via `IO Command ` actions triggered by buttons or sliders configured in the Events tab (menu `Config >> Events`). The following commands are supported:

* `set(ch,b[,sn])` : switches state on/off
* `toggle(ch[,sn])` : toggles state
* `pulse(ch,t[,sn])` : sets the output of channel c to on for time t in milliseconds
* `sleep(s)` : delay processing for `s` seconds

with

* `ch` : the channel to be addressed (integer)
* `b` : bool with off (b=0) and on (b=1)
* `t` : time in milliseconds (integer)
* `s` : sleep time in seconds (float)
* `sn` : optional hub serial number or hub serial number and hub port specifier separated by a colon like in `set(0,1,560282)` or `set(0,1,560282:2)`. Using a command actions, like in `set(0,1)`, without specifying a hub serial number, will attach to the first yet unattached module connected to the hub with the lowest serial number instead. If just a port number is given as in `set(0,1,:2)`, the yet unattached module connected to the given port (here 2) of the first hub with the lowest serial number is addressed.


### 4.3 HUB PWM Output 

* [Phidget  HUB0007](https://phidgets.com/?tier=3&catid=64&pcid=57&prodid=1290){:target="_blank"} (1x VINT HUB)
* [Phidget  HUB0000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=643){:target="_blank"}, 
  [Phidget  HUB0001](https://phidgets.com/?tier=3&catid=64&pcid=57&prodid=1202){:target="_blank"}, 
  [Phidget  HUB0002](https://phidgets.com/?tier=3&catid=64&pcid=57&prodid=1289){:target="_blank"},    
  [Phidget HUB5000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=1143){:target="_blank"} (6x VINT HUB)

Phidget HUB PWM modules can be controlled via `PWM Command ` actions triggered by buttons or sliders configured in the Events tab (menu `Config >> Events`). The following commands are supported:

* `outhub(p,v[,<sn>])` : sets PWM in percent [0-100]
* `togglehub(p[,<sn>])` : toggles between last value not 0 and 0
* `pulsehub(p,t[,<sn>])` : turn on for the given time `t`

with

* `p` : the HUB port to be addressed (integer)
* `v` : value (integer)
* `t` : time in milliseconds (integer)
* `sn` : optional hub serial number like in `outhub(0,8,560282)`. Using a command actions, like in `outhub(0,8)`, without specifying a hub serial number will attach to the first unattached hub with the lowest serial number instead.


### 4.4 PWM Output

* [OUT1100](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=714){:target="_blank"}, [REL1100](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=720){:target="_blank"} (4x VINT)
* [REL1101](https://www.phidgets.com/?tier=3&catid=46&pcid=39&prodid=721){:target="_blank"} (16x VINT)

Phidget PWM modules can be controlled via `PWM Command ` actions triggered by buttons or sliders configured in the Events tab (menu `Config >> Events`). The following commands are supported:

* `out(ch,v[,<sn>])` : sets PWM in percent [0-100]
* `frequency(ch,f[,<sn>])` : sets PWM frequency in Hz (PWM frequency is always the same for all channels!)
* `toggle(ch[,<sn>])` : toggles between last value not 0 and 0
* `pulse(ch,t[,<sn>])` : turn on for the given time `t`

with

* `ch` : the channel to be addressed (integer)
* `v` : value (integer)
* `f` : frequency (real)
* `t` : time in milliseconds (integer)
* `sn` : optional hub serial number or hub serial number and hub port specifier separated by a colon like in `out(0,8,560282)` or `out(0,8,560282:2)`. Using a command actions, like in `out(0,8)`, without specifying a hub serial number, will attach to the first yet unattached module connected to the hub with the lowest serial number instead. If just a port number is given as in `out(0,8,:2)`, the yet unattached module connected to the given port (here 2) of the first hub with the lowest serial number is addressed.


### 4.5 DC Motor Control

Artisan v2.4 adds support for DC motor control.

* [DCC1000](https://www.phidgets.com/?tier=3&catid=18&pcid=15&prodid=965){:target="_blank"} and [DCC1002](https://www.phidgets.com/?tier=3&catid=18&pcid=15&prodid=1117){:target="_blank"} (1x VINT)
* [DCC1003](https://www.phidgets.com/?tier=3&catid=18&pcid=15&prodid=1118){:target="_blank"} (2x VINT)

Phidget DC Motor Control modules can be controlled via `IO Command` actions triggered by buttons or sliders configured in the Events tab (menu `Config >> Events`). The following commands are supported:

* `accel(ch,a[,sn])` sets acceleration (duty cycle / second)
* `vel(ch,v[,sn])`   sets target velocity (duty cycle)
* `limit(ch,v[,sn])`   sets current limit
* `sleep(s)` : delay processing for `s` seconds

with

* `ch` : the channel to be addressed (integer)
* `a` : acceleration (float)
* `v` : velocity (float)
* `s` : sleep time in seconds (float)
* `sn` : optional hub serial number or hub serial number and hub port specifier separated by a colon like in `accel(0,0.5,560282)` or `accel(0,0.5,560282:2)`. Using a command actions, like in `accel(0,0.5)`, without specifying a hub serial number, will attach to the first yet unattached module connected to the hub with the lowest serial number instead. If just a port number is given as in `accel(0,0.5,:2)`, the yet unattached module connected to the given port (here 2) of the first hub with the lowest serial number is addressed.


### 4.6 RC Servo Control

Artisan v1.6 adds support for RC servo control.

* [Phidget RCC 1000](https://www.phidgets.com/?tier=3&catid=21&pcid=18&prodid=1015){:target="_blank"} (16x VINT, ext. powered)
* [Phidget 1061](https://www.phidgets.com/?tier=3&catid=21&pcid=18&prodid=1032){:target="_blank"} (8x USB, ext. powered)
* [Phidget 1066](https://www.phidgets.com/?tier=3&catid=21&pcid=18&prodid=1044){:target="_blank"} (1x USB powered) 

Phidget RC Servo modules can be controlled via `RC Command` actions triggered by buttons or sliders configured in the Events tab (menu `Config >> Events`). The following commands are supported:

* `pulse(ch,min,max[,sn])` : sets the min/max pulse width in microseconds
* `pos(ch,min,max[,sn])` : sets the min/max position
* `engaged(ch,b[,sn])` : engage (b=1) or disengage (b = 0)
* `ramp(ch,b[,sn])` : activates or deactivates the speed ramping state
* `volt(ch,v[,sn])` : set the voltage to one of 5, 6 or 7.4 in Volt
* `accel(ch,a[,sn])` : set the acceleration
* `veloc(ch,l[,sn])` : set the velocity
* `set(ch,pos[,sn])` : set the target position

with

* `ch` : the channel to be addressed (integer)
* `min, max, l, pos` : values (integer)
* `b` : bool value given as 0 (false) or 1 (true)
* `sn` : optional hub serial number or hub serial number and hub port specifier separated by a colon like in `volt(0,6,560282)` or `volt(0,6,560282:2)`. Using a command actions, like in `volt(0,6)`, without specifying a hub serial number, will attach to the first yet unattached module connected to the hub with the lowest serial number instead. If just a port number is given as in `volt(0,6,:2)`, the yet unattached module connected to the given port (here 2) of the first hub with the lowest serial number is addressed.



See [Artisan v1.6.1](https://artisan-roasterscope.blogspot.com/2019/03/artisan-v161.html){:target="_blank"} under "RC Servos" for details.


## <a name="remote-access"></a>5. Remote Access

All Phidgets can be accessed either directly via USB or remotely via network connection. The device making its connected Phidgets accessible via remote access can be either a wireless VINT hub like the [Phidget HUB5000](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=1143){:target="_blank"}, a [Phidget SBC](https://www.phidgets.com/?tier=1&catid=1&pcid=0) or another computer running the Phidget driver. In the last case, one needs to activate the Network Server in the Phidget Control Panel running on the computer with the Phidgets physically connected to make those available for remote access. 

<figure>
    <a href="/assets/images/PhidgetNetworkServer.png"><img src="/assets/images/PhidgetNetworkServer.png"></a>
    <figcaption>Phidget Control Panel</figcaption>
</figure>

The first tab of the Phidget Control Panel lists all Phidgets accessible by the computer running it. It shows local Phidgets directly connected via USB/VINT as well as Phidgets accessible via the network indicating also the serving entity. Note that only enabled and published network servers without password protection are listed.

<figure>
    <a href="/assets/images/RemotePhidgets.png"><img src="/assets/images/RemotePhidgets.png"></a>
    <figcaption>Accessible Phidgets</figcaption>
</figure>

By default Artisan is only accessing local Phidgets. Ticking the flag in the Network section of the Phidget tab (menu ```Config >> Device```, 4th tab) makes networked Phidgets accessible to Artisan as well. In most cases there is no need to enter the name of the server under Host as the mDNS/ZeroConf protocol will find Phidget servers automatically. In rare cases (e.g. if you set a password on your Phidget Network Servder) one needs to enter the remote server name like ```hub5000.local``` or its IP address in the ```Host``` field and its password (if set) into the ```Password```field. If the ```Remote Only``` flag is ticked too, local Phidgets are ignored.

Note: using the ZeroConf protocol (no host/password in the Phidget tab set) Artisan harvest all modules served by all Phidget Network Servers discoverable on the same network. Thus it is for example possible to connect to modules served by multiple HUB5000 or computers.


<figure>
    <a href="/assets/images/PhidgetsTab.png"><img src="/assets/images/PhidgetsTab.png"></a>
    <figcaption>Phidgets Tab</figcaption>
</figure>
