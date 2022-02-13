---
layout: single
permalink: /machines/caparao/
title: "Caparaó"
excerpt: "Prime Line"
header:
  overlay_image: /assets/images/caparao-large.jpg
  image: /assets/images/caparao-large.jpg
  teaser: assets/images/caparao-large.jpg
sidebar:
  nav: "machines"
---

* __Producer:__ [Caparaó Roasters](http://roasterscaparao.com.br/){:target="_blank"}, Brazil
* __Machine:__ all Prime Line machines
* __Connection:__ MODBUS TCP via the network
* __Features:__ 
  - logging of environmental temperature (ET), bean temperature (BT) and related rate-of-rise curves
  - logging and control of gas, drum speed, and airflow
  - control of actors like stirrer and release doors

<figure>
<a href="{{ site.baseurl }}/assets/images/buttons-caparao-prime.png">
<img src="{{ site.baseurl }}/assets/images/buttons-caparao-prime.png"></a>
    <figcaption>custom event buttons</figcaption>
</figure>

### Setup

The computer running Artisan must be on the same IP network as the Caparaó roaster which usually is configured to have IP 192.168.5.11. Configure your computer to use a static IP address in the range 192.168.5.x (but with x different from that of the roaster which usually has 11), so for example 192.168.0.15, and set the subnet mask to 255.255.255.0. This can be done on Windows using the Network Sharing Center by adding a TCP/IPv4 Local Area Connection with those properties. On OS X you set your Ethernet port in the Network Control panel to "IPv4: Manually" and fill in the IP and subnet mask accordingly.
{: .notice--primary}

