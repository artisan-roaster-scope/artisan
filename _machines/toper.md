---
layout: single
permalink: /machines/toper/
title: "Toper"
excerpt: "TKM-SX, Cafemino,.."
header:
  overlay_image: /assets/images/toper.jpg
  image: /assets/images/toper.jpg
  teaser: assets/images/toper.jpg
---
* __Producer:__ [Toper](http://www.toper.com){:target="_blank"}, Turkey
* __Machines:__ the "Toper PLC" setup works via a network connection with machines featuring an Omron PLC (Toper TKM-SX) or the Schneider Modicon PLC (Cafemino). The "Toper USB" setup works with some other Toper roasters that feature an USB connector.
* __Connection:__ MODBUS TCP via network or MODBUS RTU via USB; requires the installation of a [serial driver](/modbus_serial/)
* __Features:__ logging of environmental temperature (ET), bean temperature (BT) and related rate-of-rise curves

### Setup

For the "Toperr PLC" setup, the computer running Artisan must be on the same IP network as the Toper roaster which usually is configured to have IP 192.168.137.90. Configure your computer to use a static IP address in the range 192.168.137.x (but with x different from that of the roaster which usually has 90), so for example 192.168.137.91, and set the subnet mask to 255.255.255.0. This can be done on Windows using the Network Sharing Center by adding a TCP/IPv4 Local Area Connection with those properties. On OS X you set your Ethernet port in the Network Control panel to "IPv4: Manually" and fill in the IP and subnet mask accordingly.
{: .notice--primary}

**Watch out!**
A video tutorial by Stuart Lee Archer of [Pumphrey's Coffee](http://www.pumphreys-coffee.co.uk) on [Connecting a Toper TKM SX to Artisan Roaster Scope](https://youtu.be/e4nrlxgq04o). Enjoy!
[![Connecting a Toper TKM SX](http://img.youtube.com/vi/e4nrlxgq04o/0.jpg)](https://youtu.be/e4nrlxgq04o)
{: .notice--primary}