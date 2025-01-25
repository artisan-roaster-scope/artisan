---
layout: single
permalink: /machines/imf/
title: "IMF"
excerpt: "RMxxx"
header:
  overlay_image: /assets/images/IMF.jpg
  image: /assets/images/IMF.jpg
  teaser: assets/images/IMF.jpg
sidebar:
  nav: "machines"
---
* __Producer:__ [IMF SRL](http://www.imf-srl.com){:target="_blank"}, Italy
* __Machines:__ RM2/RM5/RM6/15/30/60/120/240/480 with PLC
* __Connection:__ MODBUS TCP via the network
* __Features:__ 
   - logging of bean temperature, inlet temperature and related rate-of-rise curves, as well as the burner temperature. 
   - control of drum speed, airflow and vortex valve on machines with the latest firmware installed


### Setup

The computer running Artisan must be on the same IP network as the roaster. The default IP address of the roaster is 192.168.2.32. Configure your computer to use a static IP address in the range of the roaster (192.168.2.x) but with x different from that of the roaster (eg. 192.168.2.42). Choose 255.255.255.0 as subnet mask. 
 
This can be done on Windows using the Network Sharing Center by adding a TCP/IPv4 Local Area Connection with those properties. On macOS you set your ethernet port in the Network Control panel to "IPv4: Manually" and fill in the IP and subnet mask accordingly.

**Watch out!** Artisan comes with three machine setups. The one named _RM legacy_ works with older machines that return data without decimals while the one named _RM_ works with the newer machines that return data with decimals. 

The one named _RM control_ adds the possibility to control the drum speed, airflow and vortex valve from Artisan during roasting (but not between batches). This setup requires the latest firmware version (installed by default on machines produced on 3/2023 or later and available for some older machines from IMF). Note that external software control needs to be enabled on the machine by using its HMI display. In MANUAL mode the vortex valve regulating the inlet temperature can be directly set between 0 and 100% using the corresponding Artisan slider. In AUTO mode one can specify an inlet temperature set value (IT SV) in Celsius. All automation functions implemented by Artisan can be applied to those controls.
{: .notice--primary}


**Watch out!** Artisan doesn't monitor unsafe temperatures, so you should never leave the roaster alone.
{: .notice--primary}


<a name="EnergyRatings"></a>
## Energy Ratings

|Model|Source|Burner (kW)|Motor (kW)|
|:-----|:-----:|:-----:|:-----:|
|||
| RM2 | Elec | 6 | 2 |
| RM2 | PNG/NG | 14 | 2 |
| RM6 | PNG/NG | 33 | 3 |
| RM15 | PNG/NG | 52 | 4 |
|||
| RM30 | PNG/NG | 140 | 9 |
| RM60 | PNG/NG | 280 | 13 |
| RM120 | PNG/NG | 550 | 15 |
| RM120 | PNG/NG | 970 | 20 |
| RM240 | PNG/NG | 2500 | 25 |
