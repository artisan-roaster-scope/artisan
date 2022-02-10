---
layout: single
permalink: /machines/hb/
title: "HB-Roaster"
excerpt: "M6/L2/L6"
header:
  overlay_image: /assets/images/hb2.jpg
  image: /assets/images/hb2.jpg
  teaser: assets/images/hb1.jpg
sidebar:
  nav: "machines"
---
* __Producer:__ [HB-Roaster](https://hb-roaster.com/){:target="_blank"}, Germany
* __Machines:__ Standard (M6, L2, L6) and Model S (M6-S, L2-S, L6-S) HB Roaster variants
* __Connection:__ USB
* __Features:__ logging of environmental temperature (ET), bean temperature (BT), inlet temperature (IT) and drum temperature (DT) as well as ambient temperature

**Watch out!**
The communication via USB requires to install the serial driver

* Standard (M6, L2, L6): [CP210x VCP from Silicon Labs](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers)
* Model S (M6-S, L2-S, L6-S): CH34x
   - Windows: [http://www.wch.cn/download/CH341SER_EXE.html](http://www.wch.cn/download/CH341SER_EXE.html)
   - macOS: [http://www.wch.cn/downloads/file/178.html](http://www.wch.cn/downloads/file/178.html)
   - Linux: [http://www.wch.cn/download/CH341SER_LINUX_ZIP.html](http://www.wch.cn/download/CH341SER_LINUX_ZIP.html)
{: .notice--primary}