---
redirect_to: https://docs.artisan.tools/desktop/machines/dmr
layout: single
permalink: /machines/dmr/
title: "Dutch Master Roasters"
excerpt: ""
header:
  overlay_image: /assets/images/dmr.webp
  image: /assets/images/dmr.webp
  teaser: assets/images/dmr-teaser.webp
sidebar:
  nav: "machines"
---

<img class="tab-image" src="{{ site.baseurl }}/assets/images/supporter-badge.png" width="150px">

* __Distributor:__ [Dutch Master Roasters](https://dutchmasterroasters.com/){:target="_blank"}, The Netherlands
* __Machines:__ DMR5-A & DMR15-A
* __Connection:__ Network via MODBUS TCP
* __Features:__
   - logging of bean temperature (BT) and exhaust temperature (ET), optional IR bean temperature, burner %, drum pressure (Pa), drum speed (RPM) and fan speed (%)
   - burner, max burner, drum pressure (Pa), drum speed (RPM) and, setpoint air temperature control (SV)
 
**Watch out!** 
To control the machine using artisan scope, `Remote control` needs to be enabled in the Dutch Master Roasters app. This sets the machine into `AUTO` mode where artisans `Burner` slider defines the maximum burner power (20-100%). In `AUTO` mode, the actual burner power is controlled by the machine (within the range [0, maximum burner power]) to settle on the target air temperature (50-250C) which can be controlled by the `SP-Air` slider. This `AUTO` mode is useful for pre-heating and during the between-batch protocol.
{: .notice--primary}

<figure>
<center>
<a href="{{ site.baseurl }}/assets/images/buttons-dmr.webp">
<img src="{{ site.baseurl }}/assets/images/buttons-dmr.webp"></a>
    <figcaption>AUTO mode</figcaption>
</center>
</figure>


**Watch out!** 
Artisan also supports the newer machines manual mode which can be activated by pressing the `MANUAL` button. In manual mode, the burner slider controls the machines burner output directly (0-100%) and the machines control loop is deactivated.
{: .notice--primary}


<figure>
<center>
<a href="{{ site.baseurl }}/assets/images/buttons-dmr-manual.webp">
<img src="{{ site.baseurl }}/assets/images/buttons-dmr-manual.webp"></a>
    <figcaption>MANUAL mode</figcaption>
</center>
</figure>