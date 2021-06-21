---
layout: single
permalink: /machines/aillio/
title: "Aillio"
excerpt: "Bullet R1"
header:
  overlay_image: /assets/images/aillio.jpg
  image: /assets/images/aillio.jpg
  teaser: assets/images/aillio.jpg
sidebar:
  nav: "machines"
---

* __Producer:__ [Aillio Limited](https://aillio.com){:target="_blank"}, Taiwan
* __Machine:__ Bullet R1
* __Connection:__ vendor specific USB protocol
* __Features:__ 
  - logging of drum temperature (DT), bean temperature (BT), exhaust temperature, BT rate-of-rise curves, and voltage
  - control of fan, heater and drum speed
  - support for the new [IBTS IR sensor](https://medium.com/@aillio/the-start-of-something-39aa01d08fa9){:target="_blank"} and newer models version 1.5 and 2, and firmware versions, has been added in Artisan v1.6.1

**Watch out!** 
To connect successfully, Artisan running on Windows requires the **[Aillio USB Drivers For Legacy Version Only](https://s3.amazonaws.com/aillio/bulletr1interface/installation/LibUSB/libusb-win32-bin-1.2.6.0.exe){:target="_blank"}** `libusb-win32-bin-1.2.6.0.exe`, to be installed.  Link is from [Sweet Maria's legacy support page](https://legacy.sweetmarias.com/library/aillio-bullet-r1-support/){:target="_blank"}. For those with V2 there is a workaround for [using Artisan on Windows only](https://www.home-barista.com/home-roasting/artisan-2-0-and-aillio-bullet-r1-v2-t64271.html#p708297){:target="_blank"}

Alternatively you can install the legacy serial driver as follows with the Bullet R1 V2 plugged into the USB port of your computer:

* Download and run [zadig](https://zadig.akeo.ie/)
* You should see the `Aillio LTD - Bullet R 1 ROASTER FS` selected
* On the left side you will see your current driver
* On the right side pick `libusb-win32 (v1.2.6.0)`
* Install the driver
{: .notice--primary}

**Watch out!** For best performance, please start monitoring the
roaster before pre-heating.  Artisan doesn't monitor unsafe
temperatures, so you should never leave the roaster alone.
{: .notice--primary}

**Watch out!** Running Artisan in parallel with another roast logging software, like RoastTime, connected to the same machine might lead to unstabilities and crashes.
{: .notice--primary}
