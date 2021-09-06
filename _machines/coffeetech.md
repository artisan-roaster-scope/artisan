---
layout: single
permalink: /machines/coffeetech/
title: "Coffee Tech"
excerpt: "FZ-94/Ghibli/Silon"
header:
  overlay_image: /assets/images/ghibli15.jpg
  image: /assets/images/FZ94-1.jpg
  teaser: assets/images/FZ94-1-supporter-grey.jpg
sidebar:
  nav: "machines"
---
<img class="tab-image" src="{{ site.baseurl }}/assets/images/supporter-badge-grey.png" width="150px">

* __Producer:__ [Coffee-Tech Engineering Ltd.](https://www.coffee-tech.com){:target="_blank"}, Israel
* __Machine:__ FZ-94 Lab Roaster, Ghibli 15/30/45/60/90, and Ghibli Firewood, Silon ZR7
* __Connection:__ 
   * FZ-94, Ghibli (USB), Silon (USB): MODBUS RTU via USB-2-RS485 interface; requires the installation of a [serial driver](/modbus_serial/)
   * FZ-94 EVO, Ghibli (touch), Silon ZR7 (touch): MODBUS TCP via network connection
* __Features:__ 
  - logging of environmental temperature (ET), bean temperature (BT), drum temperature (DT)
  - control of set value (SV), fan speed and drum speed on some machines (FZ-94, FZ-94 EVO, Ghibli/Silon touch with latest firmware)

### Netwok Setup

For machines talking MODBUS TCP via network connection: the computer running Artisan must be on the same IP network as the roasting machine. By default the CTE roasting machines use the IP address 192.168.1.27, but for the FZ-94 EVO which uses 192.168.1.2 by default. Configure your computer to use a manual network setup with a static IP address in the range of the roasting machine 192.168.1.x, but with x different from that of the roaster (e.g. 192.168.1.51). Choose 255.255.255.0 as subnet mask.

### Notes

- some Ghibli series machines do not feature an environmental temperature sensor and report the drum temperature on the Artisan ET channel.
- the FZ-94 setup defines 2 configurations that can be switched by pressing the COMMAND/Apple key (macOS) / CONTROL key (Windows) modifer plus a number key.
  * CMD/CTR-1 (default): logs drum- and fan speed changes as custom events
  * CMD/CTR-2: defines drum- and fan speed sliders that allow to take control via a [re-configuration of the frequency drives](https://artisan-roasterscope.blogspot.de/2016/08/fz-94-4-taking-control.html){:target="_blank"}
- The drum heat limit can also be controlled via an SV slider by ticking `Control` in the device setup (menu `Config` >> `Device`)
- The Ghibli and Silon touch setups feature control of the burner level, fan speed and drum speed which requires the roaster to be equipped with the latest firmware.