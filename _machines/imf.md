---
layout: single
permalink: /machines/imf/
title: "IMF"
excerpt: "RMxxx"
header:
  overlay_image: /assets/images/IMF.jpg
  image: /assets/images/IMF.jpg
  teaser: assets/images/IMF.jpg
---
* __Producer:__ [IMF SRL](http://www.imf-srl.com){:target="_blank"}, Italy
* __Machines:__ RM5/15/30/60/120/240/480 with PLC
* __Connection:__ MODBUS TCP via the network
* __Features:__ logging of bean temperature, inlet temperature and related rate-of-rise curves, as well as the burner temperature


### Setup

The computer running Artisan must be on the same IP network as the roaster. The default IP address of the roaster is 192.168.2.32. Configure your computer to use a static IP address in the range of the roaster (192.168.2.x) but with x different from that of the roaster (eg. 192.168.2.42). Choose 255.255.255.0 as subnet mask. 
 
This can be done on Windows using the Network Sharing Center by adding a TCP/IPv4 Local Area Connection with those properties. On macOS you set your ethernet port in the Network Control panel to "IPv4: Manually" and fill in the IP and subnet mask accordingly.

{: .notice--primary}

**Watch out!** Artisan comes with two machine setups. The one named _RM legacy_ works with older machines that return data without decimals while the one named _RM_ works with the newer machines that return data with decimals.
{: .notice--primary}


**Watch out!** Artisan doesn't monitor unsafe temperatures, so you should never leave the roaster alone.
{: .notice--primary}