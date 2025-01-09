---
layout: single
permalink: /machines/kaleido/
title: "Kaleido & Beanseeker"
excerpt: "Sniper Series"
header:
  overlay_image: /assets/images/kaleido2.jpg
  image: /assets/images/kaleido2.jpg
  teaser: assets/images/kaleido.jpg
sidebar:
  nav: "machines"
---
<img class="tab-image" src="{{ site.baseurl }}/assets/images/supporter-badge.png" width="150px">

* __Producer:__ [Wuhan Kaleido Technology Co.,Ltd](https://kaleidostorm.com/){:target="_blank"}, CN
* __Machines:__ New 2023 machine generation (Serial/Network) and legacy dual-system models (Legacy)
* __Connection:__ Serial via USB or Bluetooth; requires the installation of a [serial driver](/modbus_serial/) and WiFi
* __Features:__ reads beans temperature (BT), environmental temperature (ET), ambient air temperature (AT), set value (SV), and heater/fan/drum settings. The setting allows to control the fan and heater levels as well as the drum speed via sliders and buttons.

<figure>
<center>
<a href="{{ site.baseurl }}/assets/images/kaleido-all-buttons.png" style="width: 80%;">
<img src="{{ site.baseurl }}/assets/images/kaleido-all-buttons.png" ></a>
<a href="{{ site.baseurl }}/assets/images/kaleido-essential-buttons.png" style="width: 80%;">
<img src="{{ site.baseurl }}/assets/images/kaleido-essential-buttons.png" ></a>
    <figcaption>custom event buttons</figcaption>
</center>
</figure>

**Watch out!** 
Press CMD-2 to switch to the reduced button set; CMD-1 switches back to the full button set.
{: .notice--primary}

**Watch out!** The legacy settings do not apply for the `Pro`version. Please use the configuration file provided by the manufacturer for connecting those machines.
{: .notice--primary}

**Watch out!** The legacy settings of Artisan use a serial speed of 9600. Some of the newer legacy machines instead communicate at 57600 baud. Change the baudrate using menu `Config >> Port` to 57600 if needed.
{: .notice--primary}