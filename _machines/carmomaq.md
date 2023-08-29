---
layout: single
permalink: /machines/carmomaq/
title: "Carmomaq"
excerpt: ""
header:
  overlay_image: /assets/images/carmomaq-large.jpg
  image: /assets/images/carmomaq-large.jpg
  teaser: assets/images/carmomaq-small.jpg
sidebar:
  nav: "machines"
---
* __Producer:__ [Carmomaq](https://www.carmomaq.com.br/){:target="_blank"}, Brazil
* __Machines:__ machines with MODBUS support
* __Connection:__ MODBUS RTU via serial connection or MODBUS TCP via the network
* __Features:__
  - logging of environmental temperature (ET), bean temperature (BT) and related rate-of-rise curves
  - logging and control of burner level (0-100%), drum speed (0-120%) and air flow (0-120%)
  - control of further actors

<figure>
<center>
<a href="{{ site.baseurl }}/assets/images/buttons-carmomaq.png">
<img src="{{ site.baseurl }}/assets/images/buttons-carmomaq.png" style="width: 80%;"></a>
    <figcaption>custom event buttons (legacy setups)</figcaption>
</center>
</figure>

<figure>
<center>
<a href="{{ site.baseurl }}/assets/images/buttons-carmomaq2.png">
<img src="{{ site.baseurl }}/assets/images/buttons-carmomaq2.png" style="width: 80%;"></a>
    <figcaption>custom event buttons (2.0 setups)</figcaption>
</center>
</figure>

> **Setup Notes**  
>    
> For machines produced in 8/2020 and later choose one of the following machine setups  
> 
> - `Caloratto 2.0`
> - `Masteratto 2.0`
> - `Speciatto 2.0`
> - `Stratto 2.0`
>
>   
> For Caloratto and Materatto machines produced before 8/2020 choose the `Caloratto-Materatto_Legacy` machine setup.  
>    
> For older Stratto machines featuring Novus controls choose the machine setup `Stratto_1.0_Serial_Novus`.
{: .notice--primary}