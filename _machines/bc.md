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

* __Producer:__ [Buckeye Coffee Roasters Co. LCC](http://www.buckeyecoffee.com), USA
* __Machines:__ all with USB or Bluetooth connection
* __Connection:__ MODBUS RTU; requires the installation of a serial driver
* __Features:__ logging of environmental temperature (ET), bean temperature (BT) and related rate-of-rise curves

**Watch out!** Artsan v1.3.1 and later need a slightly different MODBUS setup (check menu `Config >> Port, 3rd tab MODBUS` for the BC roasters than previous versions.

* for v1.3.0 and earlier the `bytes` little endian flag needs to be unticked. The state of the `words` is not significant.
* for v1.3.1 and later both little-endian flags, `bytes` and `words`, need to be unticked.
{: .notice--primary}