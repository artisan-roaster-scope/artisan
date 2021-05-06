---
layout: single
permalink: /machines/ip-cc/
title: "IP-CC"
excerpt: "iRm Series"
header:
  overlay_image: /assets/images/ip2.jpg
  image: /assets/images/ip2.jpg
  teaser: assets/images/ip1.jpg
---

* __Producer:__ [IP-CC Coffee Roasting Machines](https://www.ip-cc.com/){:target="_blank"}, Greece
* __Machines:__ iRm Series with networked Omron PLC
* __Connection:__ MODBUS TCP via the network
* __Features:__
  - logging of environmental temperature (ET), bean temperature (BT), burner temperature, and mixer temperature
  - logging and control of airflow, drum speed and burner power
  - activation of transfer, charge and drop doors

### Setup

The computer running Artisan must be on the same IP network as the roaster. The default IP address of the roaster is 10.100.0.15. Configure your computer to use a static IP address in the range of the roaster (10.100.0.x) but with x different from that of the roaster (eg. 10.100.0.42). Choose 255.255.255.0 as subnet mask. 
 
This can be done on Windows using the Network Sharing Center by adding a TCP/IPv4 Local Area Connection with those properties. On macOS you set your ethernet port in the Network Control panel to "IPv4: Manually" and fill in the IP and subnet mask accordingly.

**Watch out!** Artisan doesn't monitor unsafe temperatures, so you should never leave the roaster alone.
{: .notice--primary}