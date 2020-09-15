---
layout: single
permalink: /machines/berto/
title: "Berto"
excerpt: "One/D/R"
header:
  overlay_image: /assets/images/berto.jpg
  image: /assets/images/berto.jpg
  teaser: assets/images/berto.jpg
---

* __Producer:__ [Berto Coffee Roaster](https://berto-online.com/){:target="_blank"}, Indonesia
* __Machines:__ One and D models with Autonics TX4S PIDs and R models with touch panel
* __Connection:__ MODBUS RTU via USB (One/D models) or MODBUS TCP via Network (R models)
* __Features:__ logging of environmental temperature (ET), bean temperature (BT) and related rate-of-rise curves. On the R model the roast is started and stopped also from Artisan.

### Setup One/D Models

The communication via MODBUS RTU requires to install a [serial driver](/modbus_serial/).

### Setup R Model

The computer running Artisan must be on the same IP network as the roaster. The default IP address of the roaster is 192.168.2.10. Configure your computer to use a static IP address in the range of the roaster (192.168.2.x) but with x different from that of the roaster (eg. 192.168.2.42). Choose 255.255.255.0 as subnet mask. 
 
This can be done on Windows using the Network Sharing Center by adding a TCP/IPv4 Local Area Connection with those properties. On macOS you set your ethernet port in the Network Control panel to "IPv4: Manually" and fill in the IP and subnet mask accordingly.