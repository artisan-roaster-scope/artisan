---
layout: single
permalink: /devices/arduino/
title: "Arduino"
excerpt: "TC4/TC4C"
header:
  overlay_image: /assets/images/arduino-TC4-logo.jpg
  image: /assets/images/arduino-TC4-logo.jpg
  teaser: assets/images/arduino-TC4-logo.jpg
---

The Arduino/TC4 (available on [Tindi](https://www.tindie.com/products/greencardigan/tc4-arduino-shield-v602/))is an interesting option for those that do not worry much about handling electronics without a case. The TC4 is a 4-channel temperature probe shield that can be attached to the standard [Arduino UNO](http://arduino.cc/) open-hardware device. There is also an integrated product that combines a variant of the UNO with the TC4 in one package, named TC4C, as well as further variants like the [TC4+](https://coffee.gerstgrasser.net/). Furthermore, the HT Roaster Interface was developed as add on to the TC4/TC4C stack to allow the control of the [Hottop home roaster](http://www.hottopusa.com/) via serial commands that can be assigned to sliders or buttons in Artisan (see [this post](http://artisan-roasterscope.blogspot.de/2013/02/controlling-hottop.html) for details).

Artisan implements the [serial protocol](https://github.com/greencardigan/TC4-shield/blob/master/applications/Artisan/aArtisan/trunk/src/aArtisan/commands.txt) of the Arduino TC4/TC4C with PID support.

* [aArtisan firmware v3.10](https://github.com/greencardigan/TC4-shield/tree/master/applications/Artisan/aArtisan/tags/REL-310) from 1.7.2015 by Jim (baudrate: 115200)
* [aArtisanQ PID](https://github.com/greencardigan/TC4-shield/tree/master/applications/Artisan/aArtisan_PID/branches/aArtisanQ_PID_6) 6 firmware by Brad ([configuration notes](https://github.com/greencardigan/TC4-shield/blob/master/applications/Artisan/aArtisan_PID/tags/REL-aArtisanQ_PID_6_2_3/aArtisanQ_PID/Configuration%20Options.pdf), baudrate: 115200)

**Watch out!** Older TC4 firmware versions operated at the lower 19200 baudrate.
{: .notice--primary}

