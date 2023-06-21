---
layout: single
permalink: /machines/besca/
title: "Besca"
excerpt: "BSC & Bee"
header:
  overlay_image: /assets/images/besca2.jpg
  image: /assets/images/BescaRoast.jpg
  teaser: assets/images/BescaRoast.jpg
sidebar:
  nav: "machines"
---
<img class="tab-image" src="{{ site.baseurl }}/assets/images/supporter-badge-grey.png" width="150px">

* __Producer:__ [Besca](https://www.bescaroasters.com){:target="_blank"}, Turkey
* __Machine:__ all Shop and Industrial BSC Roasters as well as the Bee sample roasters
* __Connection:__ MODBUS TCP via the network (BSC automatic); MODBUS RTU via USB (BSC manual & Bee)
* __Features:__ 
  - logging of environmental temperature (ET), bean temperature (BT) and related rate-of-rise curves
  - slider control of fan speed, burner level and drum speed (only BSC automatic)
  - control buttons to operate the drum, cooler, mixer, loader, destoner and afterburner (only BSC automatic)

<figure>
<center>
<a href="{{ site.baseurl }}/assets/images/buttons-besca-automatic.png">
<img src="{{ site.baseurl }}/assets/images/buttons-besca-automatic.png" style="width: 80%;"></a>
    <figcaption>custom event buttons</figcaption>
</center>
</figure>
 
**Watch out!** 
for Bee machines from 2022 you need to use the `Bee v2` machine setup. For older Bee machines, use the standard `Bee` machine setup.
{: .notice--primary}

**Watch out!** 
for manual machines produced after 15.09.2019, those with the touch screen, the Artisan machine setup _"Besca BSC manual v2"_ included in Artisan v2.1 and later should be used. For all other manual machines the _"Besca BSC manual v1"_ (or _"Besca BSC manual"_ in Artisan v2.0 and earlier)
{: .notice--primary}


**Watch out!**
The communication via MODBUS RTU requires to install a [serial driver](/modbus_serial/).
{: .notice--primary}