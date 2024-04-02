---
layout: single
permalink: /machines/buhler/
title: "Bühler"
excerpt: "Roastmaster"
header:
  overlay_image: /assets/images/buhler.jpg
  image: /assets/images/buhler.jpg
  teaser: assets/images/buhler.jpg
sidebar:
  nav: "machines"
---

<img class="tab-image" src="{{ site.baseurl }}/assets/images/supporter-badge.png" width="150px">

* __Producer:__ [Bühler AG](http://www.buhlergroup.com/){:target="_blank"}, Switzerland
* __Machines:__ Roastmaster RM20 (Simatic & Playone), RM60, RM120, RM240
* __Connection:__ Siemens S7 network
* __Features:__ logging of burner temperature, bean temperature, afterburner temperature, drum pressure (pa), drum speed (Hz), and airflow (%)

> **Watch out!** 
> Some RM 20 Simatic machines run on a firmware not supporting the fetching of 
> the machine state resulting in a error like
> `S7 Communication Error: read_area(5,1061,16,2)`  
> For those machines there is a simplified setup named `RM_20_Simatic_Legacy` in Artisan v2.10.6 and newer.