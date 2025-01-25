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

* __Producer:__ [GIESEN coffee-roasters](https://www.giesen.com/){:target="_blank"}, The Netherlands
* __Machines:__ WPG/WPE/W1/W6/W15/W30/W45/W60/W140 with networked PLC, including the PRO machines (6/2014 and later)
* __Connection:__ Siemens S7 network
* __Features:__
  - logging of exhaust temperature (ET), bean temperature (BT) and related rate-of-rise curves
  - logging and control of burner level, air flow, air temperature setpoint, drum speed
  - logging of the optional infrared (IR) and/or environmental temperature sensor (Env)
  - operation of actors (intake, flavouring, discharge, cooling, stirrer, LED, ...)

Artisan provides a custom machine setup for each Giesen model as well as a [few generic setups](#generic-machine-setups).




#### Generic Machine Setups (recommended for machines made before 2/2018)

There are also the following 3 generic setups for older firmware version:

- `WxA`: this one should work with all machines, but delivers temperature data without decimals
- `WxA coarse`: the WxA coarse setup is for older machines, which allow burner changes only in 10% steps, but is otherwise the same as the `WxA` setup
- `WxA+` : this setups requires an unlock code from Giesen, but delivers data in higher resolution with decimals

There are also variants of those generic Giesen machine setups which includes support for the optional infrared sensor (`IR`) and additional environmental temperature sensor (`Env`).

All of theses generic setups provide some extended custom buttons (press CMD-2 to switch to this extended button set; CMD-1 switches back to the standard button set) to operate the actors installed in some machines, like the stirrer.
 
 
<figure>
<center>
<a href="{{ site.baseurl }}/assets/images/buttons-giesen.png">
<img src="{{ site.baseurl }}/assets/images/buttons-giesen.png" style="width: 80%;"></a>
    <figcaption>custom event buttons</figcaption>
</center>
</figure>




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

<a name="EnergyRatings"></a>
## Energy Ratings


|Model|Source|Size (kg)|Burner (kW)|Motor (kW)|
|:-----|:-----:|:-----:|:-----:|:-----:|
|||
| WPE | Elec | 0.2 | 3.3 | 0.5
| WPG | LPG/NG | 0.2 | 3 | 0.5
|||
| W1 | Elec | 1 | 5 | 1
| W1 | LPG/NG | 1 | 5 | 1
| W6 | Elec | 6 | 19.2 | 1.12
| W6 | LPG/NG | 6 | 19.2 | 1.12
| W15 | Elec | 15 | 35 | 3.5
| W15 | LPG/NG | 15 | 35 | 3.5
|||
| W30 | LPG/NG | 30 | 71 | 5.1
| W45 | LPG/NG | 45 | 128 | 9.7
| W60 | LPG/NG | 60 | 174 | 12
| W140 | LPG/NG | 60 | 412 | 27.53

