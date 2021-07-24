---
layout: single
permalink: /machines/sf/
title: "San Franciscan"
excerpt: "SF1/SF6/SF10/SF25/SF75"
header:
  overlay_image: /assets/images/sf2.jpg
  image: /assets/images/sf.jpg
  teaser: assets/images/sf-supporter-grey.jpg
sidebar:
  nav: "machines"
---
<img class="tab-image" src="{{ site.baseurl }}/assets/images/supporter-badge-grey.png" width="150px">

* __Producer:__ [The San Franciscan Roaster Company](http://www.sanfranroaster.com){:target="_blank"}, USA
* __Machines:__ all roasters with a Watlow PM6 (requires the _EIA 485 Modbus RTU_ option)
* __Connection:__ MODBUS RTU via USB; requires the installation of a [serial driver](/modbus_serial/)
* __Features:__
  - logging of environmental temperature (ET), bean temperature (BT) and related rate-of-rise curves
  - gas control on machines produced after 8/2019

To activate the gas control, press CMD-2 to switch to the second [palette](https://artisan-roasterscope.blogspot.com/2013/02/events-buttons-and-palettes.html) which defines the slider to set the gas. CMD-1 activates the setup without the gas control slider.

<a name="EnergyRatings"></a>
## Energy Ratings

|Model|Source|Burner (BTU/h)|Burner (kW)|
|:-----|:-----:|:-----:|:-----:|
|||
| SF-1 (0.4kg) | LPG/NG | 10000 | 2.93 |
| SF-6 (2.7kg)| LPG/NG | 30000 | 8.79 |
| SF-10 (4.5kg) | LPG/NG | 50000 | 14.65 |
| SF-25 (11.3kg) | LPG/NG | 100000 | 29.31 |
| SF-75 (34kg) | LPG/NG | 300000 | 87.92 |