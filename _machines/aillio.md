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

> **Watch out!** 
> To connect successfully, Artisan running on macOS or Linux does not require any extra device driver to be installed.

> **Watch out!** 
> To connect successfully, Artisan v2.10.0 and older only(!), running on Windows
> requires libusb-win32-bin-1.2.6.0 driver to be installed. 
>  
> To install the libusb driver:
> * Connect the Bullet R1 to your computer.  Close RoasTime if it is running.
> * Download and run [zadig](https://zadig.akeo.ie/) (no installation required).
> * Select Options>> List All Devices.
>![alt text](../../assets/images/zadig_options_list_all.png)
>  
> * Select `Aillio LTD - Bullet R1 ROASTER FS (Interface 1)` from the pull down.
>![alt text](../../assets/images/zadig_pulldown.png)
>  
> * Select `libusb-win32 (v1.2.6.0)` on the right side of the driver line.
> * Click `Replace Driver`.  The button may show `Reinstall Driver`.  The driver installation may take several minutes.  Once complete you may close Zadig.  A Windows reboot is recommended.
>![alt text](../../assets/images/zadig_replace_driver.png)
>  
> * RoasTime will run with libusb installed.  There is no need to switch between USB drivers.  RoasTime may complain about the drivers when it is first started.  Look for the green light in the lower left corner as the indication that all is well.
>![alt text](../../assets/images/rt_startup_with_libusb.png)
{: .notice--primary}

**Watch out!** For best performance, please start monitoring the
roaster before pre-heating.  Artisan doesn't monitor unsafe
temperatures, so you should never leave the roaster alone.
{: .notice--primary}

**Watch out!** Running Artisan in parallel with another roast logging software, like RoastTime, connected to the same machine might lead to unstabilities and crashes.
{: .notice--primary}

<a name="EnergyRatings"></a>
## Energy Ratings

|Model|Source|Heater (kW)|
|:-----|:-----:|:-----:|
|||
| Bullet R1 | Elec | 1.55 |