---
layout: single
permalink: /phidgets/ambient-extension/
header:
  overlay_image: /assets/images/Phidgets/VINT-Ambient-Modules-Extension-set-parts.JPG
  image: /assets/images/Phidgets/VINT-Ambient-Modules-Extension-set-parts.JPG
title: "Ambient Extension"
excerpt: "Phidget VINT HUM1000 & PRE1000"
toc: true
toc_label: "On this page"
toc_icon: "cog"
---

## Parts

This extension is composed from the following 4 additional parts.

- 1x [HUM1000 Humidity Phidget VINT Module](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=644){:target="_blank"}
- 1x [PRE1000 Barometer Phidget VINT Module](https://www.phidgets.com/?tier=3&catid=7&pcid=5&prodid=719){:target="_blank"}
- 2x [VINT Cable 10cm](https://www.phidgets.com/?tier=3&catid=30&pcid=26&prodid=153){:target="_blank"}

<figure class="full">
    <a href="/assets/images/Phidgets/VINT-Ambient-Modules-Extension-set-parts.JPG"><img src="/assets/images/Phidgets/VINT-Ambient-Modules-Extension-set-parts.JPG"></a>
    <figcaption>Ambient Modules Extension Set – Parts</figcaption>
</figure>

### Hardware Setup

Just plug-in each of the two ambient modules into a port on the HUB0000 using the VINT cables.

<figure class="full">
    <a href="/assets/images/Phidgets/VINT-Ambient-Modules-Extension-set-hadware-setup.JPG"><img src="/assets/images/Phidgets/VINT-Ambient-Modules-Extension-set-hadware-setup.JPG"></a>
    <figcaption>Ambient Modules Extension Set – Setup </figcaption>
</figure>

#### Hardware Test

Test your hardware setup and driver installation using the [Phidget Control Panel](https://www.phidgets.com/docs/Phidget_Control_Panel){:target="_blank"} by following the instructions found in the [user guide of the HUM1000 module](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=644){:target="_blank"} and the [user guide of the PRE1000 module](https://www.phidgets.com/?tier=3&catid=7&pcid=5&prodid=719){:target="_blank"}.


### Artisan Configuration

Start Artisan and select the menu 

```
Config >> Machine >> Phidget >> VINT Ambient Modules
```

<figure class="third">
    <a href="/assets/images/Phidgets/machine-setup-ambient.png"><img src="/assets/images/Phidgets/machine-setup-ambient.png"></a>
    <a href="/assets/images/Phidgets/machine-setup-ambient-confirmation.png"><img src="/assets/images/Phidgets/machine-setup-ambient-confirmation.png"></a>
    <a href="/assets/images/Phidgets/machine-setup-masl.png"><img src="/assets/images/Phidgets/machine-setup-masl.png"></a>
    <figcaption>Ambient Modules Set – Artisan setup</figcaption>
</figure>

Artisan will prompt you to enter the elevation in metres above sea level (MASL) for your location. This value is important to calculate the correct barometric pressure from the PRE1000 pressure sensor values.

To test the Artisan setup for the Ambient Modules set, just press ON and check if humidity, barometric pressure and ambient temperatures are correctly set in the Roast Properties dialog (menu `Roast >> Properties`) of Artisan.

<figure class="full">
    <a href="/assets/images/Phidgets/artisan-ambient-data.png"><img src="/assets/images/Phidgets/artisan-ambient-data.png"></a>
    <figcaption>Ambient Data in Artisan</figcaption>
</figure>

Ambient data is also forwarded to the inventory service [artisan.plus](https://artisan.plus/){:target="_blank"}.

<figure class="full">
    <a href="/assets/images/Phidgets/plus-ambient-data.png"><img src="/assets/images/Phidgets/plus-ambient-data.png"></a>
    <figcaption>Ambient Data in artisan.plus</figcaption>
</figure>

**Watch out!** 
Note that the [Phidget Control Panel](https://www.phidgets.com/docs/Phidget_Control_Panel){:target="_blank"} needs to be closed beforehand to allow Artisan to connect to the Phidget hardware as only one app at a time can communicate with the modules.
{: .notice--primary}