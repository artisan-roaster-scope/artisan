---
layout: single
permalink: /phidgets/2x-rtd-set/
header:
  overlay_image: /assets/images/Phidgets/VINT-TMP1200-2xRTD-set-parts.JPG
  image: /assets/images/Phidgets/VINT-TMP1200-2xRTD-set-parts.JPG
title: "2x RTD Set"
excerpt: "Phidget VINT TMP1200"
toc: true
toc_label: "On this page"
toc_icon: "cog"
---

## Parts

This set is composed from the following 10 parts.

- 2x [TMP1200 RTD Phidget VINT Module](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=968){:target="_blank"}
- 1x [HUB0000 VINT Hub](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=643){:target="_blank"}
- 2x [TMP4109 PT1000 4-Wire RTD 11cm, ø3.2mm](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=1004){:target="_blank"}
- 2x [HDW4101 M12 Mounting Nut for Probes](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=634){:target="_blank"}
- 1x [Mini-USB Cable 120cm 24AWG](https://www.phidgets.com/?tier=3&catid=28&pcid=24&prodid=187){:target="_blank"}
- 2x [VINT Cable 10cm](https://www.phidgets.com/?tier=3&catid=30&pcid=26&prodid=153){:target="_blank"}


<figure class="full">
    <a href="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-parts.JPG"><img src="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-parts.JPG"></a>
    <figcaption>TMP1200 Set – Parts</figcaption>
</figure>


## Hardware Setup

The electronic is simple to wire up.

1. Connect the RTDs to the TMP1200 modules as in the picture below. The white wire is - (EXC-/RTD-) and the red wires are + (EXC+/RTD+).
2. Connect the TMP1200 modules to the VINT Hub using the Phidget cables.
3. Connect the VINT Hub to your computer with a USB cable

<figure class="third">
    <a href="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-hardware-setup.JPG"><img src="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-hardware-setup.JPG"></a>
    <a href="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-connection1.JPG"><img src="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-connection1.JPG"></a>
    <a href="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-connection2.JPG"><img src="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-connection2.JPG"></a>
    <figcaption>TMP1200 Set – Setup</figcaption>
</figure>


### Probe Installation

One probe should be installed into the lower part of the drum such that it is fully immerged into the bean mass measuring the *bean temperature (BT)*. The other probe should be installed in the middle of the drum such that it measures the air temperature just above the bean mass to report the *environmental temperature (ET)*. 

Both probes should be installed such that most part of their 11cm shield stays inside the drum without touching the drum paddels. To achieve this, the probes can be bended carefully inside the drum, but not at the tip where the sensor element sits.

Each of the TMP1200 modules have to be connected to a port on the HUB0000. The one connected to the BT probe at a lower port number (e.g. port 0) than the one connected to the ET probe (e.g. port 5).


### Hardware Test

Test your hardware setup and driver installation using the [Phidget Control Panel](https://www.phidgets.com/docs/Phidget_Control_Panel){:target="_blank"} by following the instructions found in the [user guide of the TMP1200 module](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=968){:target="_blank"}.




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
Config >> Machine >> Phidget >> VINT TMP1200 2xRTD
```

<figure class="half">
    <a href="/assets/images/Phidgets/machine-setup-2xRTD.png"><img src="/assets/images/Phidgets/machine-setup-2xRTD.png"></a>
    <a href="/assets/images/Phidgets/machine-setup-2xRTD-confirmation.png"><img src="/assets/images/Phidgets/machine-setup-2xRTD-confirmation.png"></a>
    <figcaption>TMP1200 Set – Artisan setup</figcaption>
</figure>

To test the Artisan setup for the TMP1200 set, just press ON and check if the ET and BT LCDs on the right side of the window report the correct readings.

**Watch out!** 
Note that the [Phidget Control Panel](https://www.phidgets.com/docs/Phidget_Control_Panel){:target="_blank"} needs to be closed beforehand to allow Artisan to connect to the Phidget hardware as only one app at a time can communicate with the modules.
{: .notice--primary}



## Extensions

The VINT TMP1200 2xRTD set can be easily extended.

### Ambient modules

The [ambient modules](/phidgets/ambient-extension/) can be plugged additionally into the Phidget HUB0000 to add ambient temperature, humidity, and barometric pressure data automatically to every roast.

### Further devices

You can easily plug additional [VINT modules supported by Artisan](/devices/phidgets/) into the free ports of the Phidget HUB0000 or add any other [device supported by Artisan](/devices/) like a USB Phidget.