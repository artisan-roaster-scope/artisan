---
layout: single
permalink: /machines/coffeetool/
title: "Coffeetool"
excerpt: "R500/R3/R5/R15"
header:
  overlay_image: /assets/images/coffeetool.jpg
  image: /assets/images/coffeetool.jpg
  teaser: assets/images/coffeetool.jpg
sidebar:
  nav: "machines"
---
* __Producer:__ [Coffeetool](http://coffeetool.gr){:target="_blank"}, Greece
* __Machines:__ R500/R3/R5/R15 with networked PLC
* __Connection:__ MODBUS TCP via the network
* __Features:__
  - logging of environmental temperature (ET), bean temperature (BT) and related rate-of-rise curves
  - logging of burner temperature, burner level (0-100%), drum speed (0-100%) and air flow (0-100%)
  - some machines (at least the newer automatic models with Mitsubishi FX5 PLC) also allow the control of the burner level, drum speed and air flow using Artisan sliders and/or button

### Setup

The computer running Artisan must be on the same IP network as the Coffeetool roaster. Configure your computer to use a static IP address in the range of the roaster (192.168.1.x) but with x different from that of the roaster (which by default is 192.168.1.42). Choose for example 192.168.1.55. Set the subnet mask of your computers network setup to 255.255.255.0.