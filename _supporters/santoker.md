---
layout: single
permalink: /machines/santoker/
title: "Santoker"
excerpt: ""
header:
  overlay_image: /assets/images/santoker.jpg
  image: /assets/images/santoker.jpg
  teaser: assets/images/santoker.jpg
sidebar:
  nav: "machines"
---
<img class="tab-image" src="{{ site.baseurl }}/assets/images/supporter-badge.png" width="150px">

* __Producer:__ [Santoker](){:target="_blank"}, China

* __Machine Setups:__ 
  - `1xPXR`, `2xPXF`, `2xPXR`  
  machines with one or two Fuji PXR/PXG PIDs
  - `R Series USB`  
  R Series machines with USB connection
  - `R Series Bluetooth`  
  R Series machines with Bluetooth
  - `R Master Series WiFi`  
  R Master Series machines with WiFi (before 10/2023)
  - `R Master Series Bluetooth`  
  R Master Series machines with Bluetooth (after 10/2023)
  - `Q + X Series WiFi`  
  Q and X Series machines with WiFi (before 10/2023)
  - `Q + X Series Bluetooth`  
  Q and X Series machines with Bluetooth (after 10/2023)
  - `Cube Bluetooth`  
  Cube10 machines

* __Connection:__ 
  - Fuji based machines use MODBUS RTU via USB; requires the installation of a [serial driver](/modbus_serial/)
  - R Series connect via USB; requires the installation of a [serial driver](/modbus_serial/)
  - Q and X Series as well as the R Master Series machines connect via WiFi or Bluetooth
  - the Cube connects via Bluetooth
* __Features:__ 
  - logging of bean temperature (BT), environmental temperature (ET) and in some cases a third temperature
  - logging and control of fan and power for the Q and X Series, the Cube as well as the R Master Series models. The later allows to log the drum speed as well.