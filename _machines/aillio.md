---
layout: single
permalink: /machines/aillio/
title: "Aillio"
excerpt: "Bullet R1"
header:
  overlay_image: /assets/images/aillio.jpg
  image: /assets/images/aillio.jpg
  teaser: assets/images/aillio.jpg
---

* __Producer:__ [Aillio Limited](https://aillio.com), Taiwan
* __Machine:__ Bullet R1
* __Connection:__ vendor specific USB protocol
* __Features:__ 
  - logging of drum temperature (DT), bean temperature (BT), exhaust temperature, BT rate-of-rise curves, and voltage
  - control of fan, heater and drum speed
  - support for the new [IBTS IR sensor](https://medium.com/@aillio/the-start-of-something-39aa01d08fa9) and newer models version 1.5 and 2, and firmware versions, has been added in Artisan v1.6.1

**Watch out!** 
To connect successfully, Artisan running on Windows requires the **[Aillio USB Drivers For Legacy Version Only](https://s3.amazonaws.com/aillio/bulletr1interface/installation/LibUSB/libusb-win32-bin-1.2.6.0.exe)** `libusb-win32-bin-1.2.6.0.exe`, to be installed (from [Sweet Maria's legacy page](https://legacy.sweetmarias.com/library/aillio-bullet-r1-support/).
{: .notice--primary}

**Watch out!** For best performance, please start monitoring the
roaster before pre-heating.  Artisan doesn't monitor unsafe
temperatures, so you should never leave the roaster alone.
{: .notice--primary}

**Watch out!** Running Artisan in parallel with another roast logging software, like RoastTime, connected to the same machine might lead to unstabilities and crashes.
{: .notice--primary}
