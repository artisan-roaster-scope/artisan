---
layout: single
permalink: /machines/trinitas/
title: "Trinitas"
excerpt: "T2/T7"
header:
  overlay_image: /assets/images/trinitas2.jpg
  image: /assets/images/trinitas2.jpg
  teaser: assets/images/trinitas.jpg
sidebar:
  nav: "machines"
---

<img class="tab-image" src="{{ site.baseurl }}/assets/images/supporter-badge-grey.png" width="150px">

* __Distributor:__ [Novustec](http://novustec.co.kr/){:target="_blank"}, South Korea

* __Machines:__ T2 and T7
* __Connection:__ MODBUS ASCII via USB; requires the installation of a [serial driver](/modbus_serial/)
* __Features:__ 
  - logging of bean temperature and environmental temperature
  - logging of airflow in % (some T2 and all T7)
  - logging of gas in % (some T7)

**Watch out!** There are two setups of the T2, one for machines providing airflow data and one for legacy machines not providing that data. If you encounter MODBUS errors on using the T2 setup with air, try regular T2 setup. Some T2 machines might report their data in Fahrenheit instead of Celsius and thus you encounter wrong readings. In that case change the "Mode" for the MODBUS Inputs 1-3 to "F" (from "C") in the MODBUS tab (menu `Config >> Port`, 3rd tab "MODBUS"). Similarly, some machines report the data multiplied by 10. If you encounter this, introduce a divider 1/10 for those MODBUS Inputs 1-3 by setting their Divider to "1/10" in the MODBUS tab (menu `Config >> Port`, 3rd tab "MODBUS").
{: .notice--primary}

**Watch out!** Some T7 machines use an older communication setup. If you encounter MODBUS errors try the T7 legacy setup. Some T7 machines report the gas in %. For those use the T7 gas setup, for all others the regular T7 machine setup.
{: .notice--primary}