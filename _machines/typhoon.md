---
layout: single
permalink: /machines/typhoon/
title: "Typhoon"
excerpt: "2/3/4/9kg"
header:
  overlay_image: /assets/images/typhoon2.jpg
  image: /assets/images/typhoon2.jpg
  teaser: assets/images/typhoon1-supporter.jpg
---

<img class="tab-image" src="{{ site.baseurl }}/assets/images/supporter-badge.png" width="150px">

* __Producer:__ [LLC Typhoon Coffee](https://typhoon.coffee/){:target="_blank"}, Russia
* __Machines:__ 2kg, 3kg (Cocoa), 4kg, and 9kg
* __Connection:__ MODBUS TCP via the network
* __Features:__ logging of bean temperature (BT), environmental temperatur (ET) and burner level and temperature


### Setup

The computer running Artisan must be on the same IP network as the roaster. The default IP address of the roaster is 192.168.0.210. Configure your computer to use a static IP address in the range of the roaster (192.168.0.x) but with x different from that of the roaster (eg. 192.168.0.42). Choose 255.255.255.0 as subnet mask. 
 
This can be done on Windows using the Network Sharing Center by adding a TCP/IPv4 Local Area Connection with those properties. On macOS you set your ethernet port in the Network Control panel to "IPv4: Manually" and fill in the IP and subnet mask accordingly.