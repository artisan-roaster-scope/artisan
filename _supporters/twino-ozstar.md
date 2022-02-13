---
layout: single
permalink: /machines/twino-ozstar/
title: "Twino/Ozstar"
excerpt: "Os-2/5/10/30/60/120K"
header:
  overlay_image: /assets/images/twino-ozstar.jpg
  image: /assets/images/twino-ozstar1.jpg
  teaser: assets/images/twino-ozstar1.jpg
sidebar:
  nav: "machines"
---

<img class="tab-image" src="{{ site.baseurl }}/assets/images/supporter-badge.png" width="150px">

* __Producer:__ [Özstar](https://www.ozstarmakina.com/){:target="_blank"}, Turkey
* __Machines:__ all Twino/Ozstar machines with networked PLC
* __Connection:__ MODBUS TCP via the network
* __Features:__
   - logging of environmental temperature (ET), bean temperature (BT) and related rate-of-rise curves
   - logging of mixer tank temperature, humidity, gas pressure, gas pressure (burner), feeding weight
   - control of airflow, drum and steerer motor speeds as well as burner power via sliders
   - activation/deactivation of fan, drum, burner, bean feeder, bean filler, stirrer, cooling motor 1 and 2 as well as the release door via buttons

<figure>
<center>
<a href="{{ site.baseurl }}/assets/images/buttons-Twino.png">
<img src="{{ site.baseurl }}/assets/images/buttons-Twino.png" style="width: 80%;"></a>
    <figcaption>custom event buttons</figcaption>
</center>
</figure>

### Setup

The computer running Artisan must be on the same IP network as the Twino/Ozstar roaster which usually is configured to have IP 192.168.2.180.
{: .notice--primary}
