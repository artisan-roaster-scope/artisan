---
layout: single
permalink: /devices/pid/
title: "PID"
excerpt: "Fuji/Delta"
header:
  overlay_image: /assets/images/pid.jpg
  image: /assets/images/pid.jpg
  teaser: assets/images/pid.jpg
modified: 2016-04-18T16:39:37-04:00
---

Artisan comes with specific support for the [Fuji PXG4/5 & PXR4/5](https://www.fujielectric.com/products/instruments/products/controller/top.html) and the [Delta DTA](http://www.deltaww.com/Products/CategoryListT1.aspx?CID=060405&PID=ALL&hl=en-US)  PIDs. For these PIDs Artisan provides dialogs to configure some of their settings like their Ramp-and-Soak patterns. Those can be accessed via the blue `PID` button on the main window, once the `Control` flag in the Device Assignment dialog is ticked (menu `Config >> Device`).

**Watch out!** Other PIDs can be operated by Artisan if they offer a [MODBUS](/devices/modbus/) interface. See the post on [PID support](https://artisan-roasterscope.blogspot.it/2016/11/pid-control.html) on the Artisan blog for details.
{: .notice--primary}