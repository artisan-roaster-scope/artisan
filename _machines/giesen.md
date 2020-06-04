---
layout: single
permalink: /machines/giesen/
title: "Giesen"
excerpt: "WPG1/W1A/W6A/W15A"
header:
  overlay_image: /assets/images/giesen.jpg
  image: /assets/images/giesen.jpg
  teaser: assets/images/giesen.jpg
---
* __Producer:__ [GIESEN coffee-roasters](http://www.giesencoffeeroasters.eu){:target="_blank"}, The Netherlands
* __Machines:__ WPG1/W1A/W6A/W15A with networked PLC (6/2014 and later)
* __Connection:__ Siemens S7 network
* __Features:__
  - logging of environmental temperature (ET), bean temperature (BT) and related rate-of-rise curves
  - logging and control of burner level, air flow, air temperature setpoint, drum speed
  - logging of the optional infrared (IR) sensor

### Setup

The computer running Artisan must be on the same IP network as the Giesen roaster which usually is configured to have IP 192.168.2.180. Configure your computer to use a static IP address in the range 192.168.2.x (but with x different from that of the roaster which usually has 180), so for example 192.168.2.10, and set the subnet mask to 255.255.255.0. This can be done on Windows using the Network Sharing Center by adding a TCP/IPv4 Local Area Connection with those properties. On OS X you set your Ethernet port in the Network Control panel to "IPv4: Manually" and fill in the IP and subnet mask accordingly.

Other IP addresses of machines different from 192.168.2.180 that have been observed are

* WPG1: 172.30.30.10
* W1: 172.30.30.30
* W15: 172.30.30.50

{: .notice--primary}

**Watch out!** Artisan doesn't monitor unsafe temperatures, so you should never leave the roaster alone.
{: .notice--primary}