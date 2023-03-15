---
layout: single
permalink: /phidgets/2x-tc-set/
header:
  overlay_image: /assets/images/Phidgets/VINT-TMP1101-2xTC-set-parts.JPG
  image: /assets/images/Phidgets/VINT-TMP1101-2xTC-set-parts.JPG
title: "2x TC Set"
excerpt: "Phidget VINT TMP1101"
toc: true
toc_label: "On this page"
toc_icon: "cog"
---

[Phidget SETS](https://artisan-scope.org/devices/phidget-sets/)

This Phidget setup centers around the VINT Phidget TMP1101 module that provides up to 4 temperature channels.


## Parts

This set is composed from the following 8 parts.

- 1x [TMP1101 4x Thermocouple VINT Module](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=726){:target="_blank"}
- 1x [HUB0000 VINT Hub](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=643){:target="_blank"}
- 2x [TMP4106 K-Type Probe Thermocouple 11cm, ø3.2mm](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=729){:target="_blank"}
- 2x [HDW4102 M8 Mounting Nut for Probes](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=1240){:target="_blank"}  
(2x [HDW4101 M12 Mounting Nuts](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=634){:target="_blank"} up to 15.3.2023)
- 1x [Mini-USB Cable 120cm 24AWG](https://www.phidgets.com/?tier=3&catid=28&pcid=24&prodid=187){:target="_blank"}
- 1x [Phidget VINT Cable 10cm](https://www.phidgets.com/?tier=3&catid=30&pcid=26&prodid=153){:target="_blank"}


<figure class="full">
    <a href="/assets/images/Phidgets/VINT-TMP1101-2xTC-set-parts.JPG"><img src="/assets/images/Phidgets/VINT-TMP1101-2xTC-set-parts.JPG"></a>
    <figcaption>TMP1101 Set – Parts</figcaption>
</figure>


## Hardware Setup

The electronic is simple to wire up.

1. Connect the thermocouples to the first two inputs on the screw terminal of the TMP1101 module labeled 0 and 1 as in the picture below. The red wire (positive) goes into the numbered screw (0 or 1) and the black wire (negative) to one of the inputs marked with an arrow to &#9178; (ground).
2. Connect the TMP1101 to the VINT Hub using the Phidget cable.
3. Connect the VINT Hub to your computer with a USB cable

<figure class="half">
    <a href="/assets/images/Phidgets/VINT-TMP1101-2xTC-set-hardware-setup.JPG"><img src="/assets/images/Phidgets/VINT-TMP1101-2xTC-set-hardware-setup.JPG"></a>
    <a href="/assets/images/Phidgets/VINT-TMP1101-2xTC-set-connection.JPG"><img src="/assets/images/Phidgets/VINT-TMP1101-2xTC-set-connection.JPG"></a>
    <figcaption>TMP1101 Set – Setup</figcaption>
</figure>

### Probe Installation

The probe connected to the TMP1101 on input 0 should be installed into the lower part of the drum such that it is fully immerged into the bean mass measuring the *bean temperature (BT)*. 

The probe connected to the TMP1101 on input 1 should be installed in the middle of the drum such that it measures the air temperature above the bean mass to report the *environmental temperature (ET)*. 

Both probes should be installed such that most part of their 11cm shield stays inside the drum without touching the drum paddels. To achieve this, the probes can be bended carefully inside the drum, but not at the tip where the sensor element sits.


### Hardware Test

Test your hardware setup and driver installation using the [Phidget Control Panel](https://www.phidgets.com/docs/Phidget_Control_Panel){:target="_blank"} by following the instructions found in the [user guide of the TMP1101 module](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=726){:target="_blank"}.



## Software Setup

### Phidget driver Installation

Download and install the Phidget driver following the instructions for your platform:

- [Windows](https://www.phidgets.com/docs/OS_-_Windows){:target="_blank"}
- [macOS](https://www.phidgets.com/docs/OS_-_OS_X){:target="_blank"}
- [Linux](https://www.phidgets.com/docs/OS_-_Linux){:target="_blank"}
- [RPi](https://www.phidgets.com/?view=articles&article=GetStartedPhidgetsRaspberry){:target="_blank"}

### Artisan Installation

Download and install the [latest Artisan version](https://github.com/artisan-roaster-scope/artisan/releases/latest){:target="_blank"}. Choose the correct installer according your operating system:

- `artisan-win-XX.XX.XX.zip` (Windows)
- `artisan-mac-XX.XX.XX.dmg` (macOS)
- `artisan-linux-XX.XX.XX.rpm` (Linux Redhat/CentOS)
- `artisan-linux-XX.XX.XX.deb` (Linux Debian/Ubuntu)
- `artisan-linux-XX.XX.XX_raspbian-XX.deb`(Raspberry Pi)

**Watch out!** 
Artisan for macOS is also available via the Homebrew Cask package manager. See the [Artisan installation instructions](https://github.com/artisan-roaster-scope/artisan/blob/master/wiki/Installation.md){:target="_blank"} for further details.
{: .notice--primary}


### Artisan Configuration

Start Artisan and select the menu 

```
Config >> Machine >> Phidget >> VINT TMP1101 2xTC
```

<figure class="half">
    <a href="/assets/images/Phidgets/machine-setup-2xTC.png"><img src="/assets/images/Phidgets/machine-setup-2xTC.png"></a>
    <a href="/assets/images/Phidgets/machine-setup-2xTC-confirmation.png"><img src="/assets/images/Phidgets/machine-setup-2xTC-confirmation.png"></a>
    <figcaption>TMP1101 Set – Artisan setup</figcaption>
</figure>

To test the Artisan setup for the TMP1101 set, just press ON and check if the ET and BT LCDs on the right side of the window report the correct readings.

**Watch out!** 
Note that the [Phidget Control Panel](https://www.phidgets.com/docs/Phidget_Control_Panel){:target="_blank"} needs to be closed beforehand to allow Artisan to connect to the Phidget hardware as only one app at a time can communicate with the modules.
{: .notice--primary}



## Extensions

The VINT TMP1101 2xTC set can be easily extended.

### Two more TCs

The set uses only 2 of the 4 channels available on the TMP1101. One can easily add 2 additional TCs (k-type or j-type) to read for example the temperature of the exhaust air, an approximation of the drum temperature by placing a TC from the outside close to the drum surface or a TC into the air coming from the cooling bin to document fast enough cooling of the beans.

Hardware setup up for two additional TCs is simple. Just screw them into the left-over ports. For the Artisan configuration you add an extra device channel of type `Phidget TMP1101 4xTC 23` via menu

```
Config >> Device >> Extra Devices (2nd tab)
```

<figure class="full">
    <a href="/assets/images/Phidgets/TMP1101-additional-channels.png"><img src="/assets/images/Phidgets/TMP1101-additional-channels.png"></a>
    <figcaption>TMP1101 Set – channel 3 and 4 configuration</figcaption>
</figure>

If your additional TCs are not of type k you need to switch the TC type of those channels in the Phidgets configuration tab via menu

```
Config >> Device >> Phidgets (4th tab), TMP1101 section
```

<figure class="full">
    <a href="/assets/images/Phidgets/TMP1101-additional-channels-type-conf.png"><img src="/assets/images/Phidgets/TMP1101-additional-channels-type-conf.png"></a>
    <figcaption>TMP1101 Set – configure probe type of channel 3 and 4</figcaption>
</figure>


### Ambient modules

The [ambient modules](/phidgets/ambient-extension/) can be plugged additional into the Phidget HUB0000 to add ambient temperature, humidity, and barometric pressure data automatically to every roast.

### Further devices

You can easily plug additional [VINT modules supported by Artisan](/devices/phidgets/) into the free ports of the Phidget HUB0000 or add any other [device supported by Artisan](/devices/) like a USB Phidget.