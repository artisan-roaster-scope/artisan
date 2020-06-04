---
layout: single
permalink: /machines/bc/
title: "BC Roasters"
excerpt: ""
header:
  overlay_image: /assets/images/BC-2000 BT.jpg
  image: /assets/images/BC-2000 BT.jpg
  teaser: assets/images/BC-2000 BT.jpg
---

* __Producer:__ [Buckeye Coffee Roasters Co. LCC](http://www.buckeyecoffee.com){:target="_blank"}, USA
* __Machines:__ all with USB or Bluetooth connection
* __Connection:__ MODBUS RTU; requires the installation of a serial driver
* __Features:__ logging of environmental temperature (ET), bean temperature (BT) and related rate-of-rise curves

{% capture notice-text %}
Artsan v1.3.1 and later need a slightly different MODBUS setup (check menu `Config >> Port`, 3rd tab `MODBUS`) than earlier versions where the state of the little-endian flag `words` was insignificant. Now both little-endian flags, `bytes` and `words`, should not be ticked as in the screenshot below.

![alt text](../../assets/images/BC_modbus.png)
{% endcapture %}

<div class="notice--primary">
  <h4>Watch out!</h4>
  <BR>
  {{ notice-text | markdownify }}
</div>

