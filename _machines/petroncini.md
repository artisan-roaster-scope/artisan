---
layout: single
permalink: /machines/petroncini/
title: "Petroncini"
excerpt: "TT 5/10, 10/20, TT 60-400"
header:
  overlay_image: /assets/images/petroncini2.jpg
  image: /assets/images/petroncini2.jpg
  teaser: assets/images/petroncini1.jpg
---
* __Producer:__ [Petroncini Impianti S.p.A.](https://www.petroncini.com/){:target="_blank"}, Italy
* __Machines:__ TT 5/10, 10/20, TT120 with PLC
* __Connection:__ MODBUS TCP or Siemens S7 via the network
* __Features:__ logging of bean temperature (BT), environmental temperature (ET) and burner temperatures


### Setup

**Watch out!** Artisan comes with three machine setups for Petroncini roasters. The one named _TT ASEM_ works with older TT 5/10 and 10/20 machines based on a PLC talking MODBUS. The one named _TT Maestro Avantgarde_ works with TT 5/10 and 10/20 models, equipped with the Maestro or Avantgarde control system talking Siemens S7, produced from 2019 on. Finally, the setup named _TT Traditional_ connects to  traditional TT roasters from 60 to 400kg equipped with Siemens S7 PLCs.
{: .notice--primary}

The computer running Artisan must be on the same IP network as the roaster. The default IP address of the roaster is 192.168.100.1 (192.168.5.11 for the older TT ASEM models). Configure your computer to use a static IP address in the range of the roaster (192.168.100.x) but with x different from that of the roaster (eg. 192.168.100.42). Choose 255.255.255.0 as subnet mask. 
 
This can be done on Windows using the Network Sharing Center by adding a TCP/IPv4 Local Area Connection with those properties. On macOS you set your ethernet port in the Network Control panel to "IPv4: Manually" and fill in the IP and subnet mask accordingly.