---
layout: single
permalink: /machines/giesen/
title: "Giesen"
excerpt: ""
header:
  overlay_image: /assets/images/giesen.jpg
  image: /assets/images/giesen.jpg
  teaser: assets/images/giesen.jpg
sidebar:
  nav: "machines"
---

* __Producer:__ [GIESEN coffee-roasters](http://www.giesencoffeeroasters.eu){:target="_blank"}, The Netherlands
* __Machines:__ WPG/WPE/W1/W6/W15/W30/W45/W60 with networked PLC (6/2014 and later)
* __Connection:__ Siemens S7 network
* __Features:__
  - logging of exhaust temperature (ET), bean temperature (BT) and related rate-of-rise curves
  - logging and control of burner level, air flow, air temperature setpoint, drum speed
  - logging of the optional infrared (IR) and/or environmental temperature sensor (Env)
  - operation of actors (intake, flavouring, discharge, cooling, stirrer) on W30 and larger machines via custom buttons (press CMD-2 to switch to this extended button set; CMD-1 switches back to the standard button set)

<figure>
<center>
<a href="{{ site.baseurl }}/assets/images/buttons-giesen.png">
<img src="{{ site.baseurl }}/assets/images/buttons-giesen.png" style="width: 80%;"></a>
    <figcaption>custom event buttons</figcaption>
</center>
</figure>

**Watch out!** The WxA coarse setup is for older machines, which allow burner changes only in 10% steps.
{: .notice--primary}

**Watch out!** The WxA+ setups require an unlock code from Giesen and deliver data in higher resolution with decimals.
{: .notice--primary}

### Setup

The computer running Artisan must be on the same IP network as the Giesen roaster. Configure your computer to use a static IP address in the range of the roaster (192.168.2.x, 192.168.3.x or 172.30.30.x) but with x different from that of the roaster (see the tables below). Choose 255.255.255.0 as subnet mask.

#### Default IP Addresses Giesen Roasters before 2/2018 without touch panel:

| Model | IP-Roaster        | IP-PC (ex)       |
|-------|-------------------|------------------|
| W1    | 192.168.**2**.199 | 192.168.**2**.42 |
| W6    | 192.168.**2**.199 | 192.168.**2**.42 |
| W15   | 192.168.**2**.199 | 192.168.**2**.42 |
|       |                   |                  |
| W30   | 192.168.**3**.199 | 192.168.**3**.42 |
| W45   | 192.168.**3**.199 | 192.168.**3**.42 |
| W60   | 192.168.**3**.199 | 192.168.**3**.42 |


#### Default IP Addresses Giesen Roasters before 2/2018 with touch panel:

| Model | IP-Roaster        | IP-PC (ex)       |
|-------|-------------------|------------------|
| W1    | 192.168.**2**.180 | 192.168.**2**.42 |
| W6    | 192.168.**2**.180 | 192.168.**2**.42 |
| W15   | 192.168.**2**.180 | 192.168.**2**.42 |
|       |                   |                  |
| W30   | 192.168.**3**.180 | 192.168.**3**.42 |
| W45   | 192.168.**3**.180 | 192.168.**3**.42 |
| W60   | 192.168.**3**.180 | 192.168.**3**.42 |



#### Default IP Addresses Giesen Roasters after 2/2018:

| Model   | IP-Roaster   | IP-PC (ex)   |
|---------|--------------|--------------|
| WPG/WPE | 172.30.30.10 | 172.30.30.42 |
| W1      | 172.30.30.30 | 172.30.30.42 |
| W6      | 172.30.30.50 | 172.30.30.42 |
| W15     | 172.30.30.50 | 172.30.30.42 |
| W30     | 172.30.30.70 | 172.30.30.42 |
| W45     | 172.30.30.90 | 172.30.30.42 |
| W60     | 172.30.30.90 | 172.30.30.42 |
| W140    | 172.30.30.110 | 172.30.30.42 |

 
This can be done on Windows using the Network Sharing Center by adding a TCP/IPv4 Local Area Connection with those properties. On macOS you set your ethernet port in the Network Control panel to "IPv4: Manually" and fill in the IP and subnet mask accordingly.

**Watch out!** Artisan doesn't monitor unsafe temperatures, so you should never leave the roaster alone.
{: .notice--primary}