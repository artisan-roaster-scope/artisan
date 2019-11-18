---
layout: single
permalink: /devices/phidget-sets/
title: "Phidget SETS"
excerpt: "Selected Sets of Phidgets"
header:
  overlay_image: /assets/images/phidgets-logo-sets.jpg
  image: /assets/images/phidgets-logo-sets.jpg
  teaser: assets/images/phidgets-logo-sets.jpg
toc: true
toc_label: "On this page"
toc_icon: "cog"
---

Phidgets modules offer reliable measuring for roast logging with Artisan. In general Phidgets are plug-and-play, providing high-resolution data at high-speed. 

We describe here two basic setups that to our experience perform best. One setup is based on thermocouples (TCs) and a second, low-noise one, based on Resistive Thermal Devices (RTDs). For a technical discussion on the differences see *[On Idle Noise](https://artisan-roasterscope.blogspot.com/2019/03/on-idle-noise.html)*. An additional set of modules can be added to either of these two setups, providing ambient data (humidity, barometric pressure and room temperature).

- [VINT TMP1101 2xTC Set](#2xtc-set)
- [VINT TMP1200 2xRTD Set](#2xrtd-set) (low-noise)
- [VINT Ambient Modules Extension](#ambient-modules-extension)

All sets are based on the modern [VINT](https://www.phidgets.com/docs/What_is_VINT%3F Phidgets) as they provide additional flexibility, increased signal stability and generally consume less power from your USB port, in contrast to the direct-to-USB Phidgets (like the popular Phidget 1048 *databridge*)

Note that the sets use probes with a diameter of ø3.2mm which are considered slow by some. In the post linked above we argue that thinner probes have a lower signal-noise ratio, break regularly, and their speed advantage does not matter for the application in coffee roasting.

**Watch out!** 
The hardware parts of each set are available from [Phidgets.com](Phidgets.com), one of their [reseller](https://www.phidgets.com/docs/Dealers) or as a compiled package from the [Artisan shop](https://shop.artisan.plus/).
{: .notice--primary}


## 0. Software Installation

### Install the Phidget driver

Download and install the Phidget driver following the instructions for your platform:

- [Windows](https://www.phidgets.com/docs/OS_-_Windows)
- [macOS](https://www.phidgets.com/docs/OS_-_OS_X)
- [Linux](https://www.phidgets.com/docs/OS_-_Linux)
- [RPi](https://www.phidgets.com/?view=articles&article=GetStartedPhidgetsRaspberry)

### Install Artisan

Download and install the [latest Artisan version](https://github.com/artisan-roaster-scope/artisan/releases/latest). Choose the correct installer according your operating system:

- `artisan-win-XX.XX.XX.zip` (Windows)
- `artisan-mac-XX.XX.XX.dmg` (macOS)
- `artisan-linux-XX.XX.XX.rpm` (Linux Redhat/CentOS)
- `artisan-linux-XX.XX.XX.deb` (Linux Debian/Ubuntu)
- `artisan-linux-XX.XX.XX_raspbian-XX.deb`(Raspberry Pi)

**Watch out!** 
Artisan for macOS is also available via the Homebrew Cask package manager. See the [Artisan installation instructions](https://github.com/artisan-roaster-scope/artisan/blob/master/wiki/Installation.md) for further details.
{: .notice--primary}


<a id="2xtc-set"></a>
## 1. VINT TMP1101 2xTC Set

This setup centers around the VINT Phidget TMP1101 that provides up to 4 temperature channels, only 2 of those are used here to measure bean temperature (BT) and environmental temperature (ET).

### Parts

This set is composed from the following 8 parts.

- 1x [TMP1101 4x Thermocouple VINT Module](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=726)
- 1x [HUB0000 VINT Hub](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=643)
- 2x [TMP4106 K-Type Probe Thermocouple 11cm, ø3.2mm](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=729)
- 2x [HDW4101 M12 Mounting Nut for Probes](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=634)
- 1x [Mini-USB Cable 120cm 24AWG](https://www.phidgets.com/?tier=3&catid=28&pcid=24&prodid=187)
- 1x [Phidget VINT Cable 10cm](https://www.phidgets.com/?tier=3&catid=30&pcid=26&prodid=153)


<figure class="full">
    <a href="/assets/images/Phidgets/VINT-TMP1101-2xTC-set-parts.JPG"><img src="/assets/images/Phidgets/VINT-TMP1101-2xTC-set-parts.JPG"></a>
    <figcaption>TMP1101 Set – Parts</figcaption>
</figure>


### Hardware Setup

The electronic is simple to wire up.

1. Connect the thermocouples to the first two inputs of the TMP1101 module labeled 0 and 1 as in the picture below. The black-wire is - (GND) and the red-wire is +.
2. Connect the TMP1101 to the VINT Hub using the Phidget cable.
3. Connect the VINT Hub to your computer with a USB cable

<figure class="half">
    <a href="/assets/images/Phidgets/VINT-TMP1101-2xTC-set-hardware-setup.JPG"><img src="/assets/images/Phidgets/VINT-TMP1101-2xTC-set-hardware-setup.JPG"></a>
    <a href="/assets/images/Phidgets/VINT-TMP1101-2xTC-set-connection.JPG"><img src="/assets/images/Phidgets/VINT-TMP1101-2xTC-set-connection.JPG"></a>
    <figcaption>TMP1101 Set – Setup</figcaption>
</figure>

#### Probe Installation

The probe connected to the TMP1101 on input 0 should be installed into the lower part of the drum such that it is fully immerged into the bean mass measuring the *bean temperature (BT)*. The probe connected to the TMP1101 on input 1 should be installed in the middle of the drum such that it measures the air temperature just above the bean mass to report the *environmental temperature (ET)*. Both probes should be installed such that most part of their 11cm shield stays inside the drum without touching the drum paddels. To achieve this, the probes can be bended carefully inside the drum, but not at the tip where the sensor element sits.


#### Hardware Test

Test your hardware setup and driver installation using the [Phidget Control Panel](https://www.phidgets.com/docs/Phidget_Control_Panel) by following the instructions found in the [user guide of the TMP1101 module](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=726).



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
Note that the [Phidget Control Panel](https://www.phidgets.com/docs/Phidget_Control_Panel) needs to be closed beforehand to allow Artisan to connect to the Phidget hardware as only one app at a time can communicate with the modules.
{: .notice--primary}



### Possible Extensions

#### Two more TCs

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


#### Ambient modules

The [ambient modules](#vint-ambient-modules-extension) can be plugged additional into the Phidget HUB0000 to add ambient temperature, humidity, and barometric pressure data automatically to every roast. See
[below](#vint-ambient-modules-extension) for details on the setup and configuration.

#### Further devices

You can easily plug additional [VINT modules supported by Artisan](/devices/phidgets/) into the free ports of the Phidget HUB0000 or add any other [device supported by Artisan](/devices/) like a USB Phidget.

<a id="2xrtd-set"></a>
## 2. VINT TMP1200 2xRTD Set


### Parts

This set is composed from the following 10 parts.

- 2x [TMP1200 RTD Phidget VINT Module](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=968)
- 1x [HUB0000 VINT Hub](https://www.phidgets.com/?tier=3&catid=2&pcid=1&prodid=643)
- 2x [TMP4109 PT1000 4-Wire RTD 11cm, ø3.2mm](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=1004)
- 2x [HDW4101 M12 Mounting Nut for Probes](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=634)
- 1x [Mini-USB Cable 120cm 24AWG](https://www.phidgets.com/?tier=3&catid=28&pcid=24&prodid=187)
- 2x [VINT Cable 10cm](https://www.phidgets.com/?tier=3&catid=30&pcid=26&prodid=153)


<figure class="full">
    <a href="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-parts.JPG"><img src="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-parts.JPG"></a>
    <figcaption>TMP1200 Set – Parts</figcaption>
</figure>


### Hardware Setup

The electronic is simple to wire up.

1. Connect the RTDs to the TMP1200 modules as in the picture below. The white-wire is - (EXC-/RTD-) and the red-wires are + (EXC+/RTD+).
2. Connect the TMP1200 modules to the VINT Hub using the Phidget cables.
3. Connect the VINT Hub to your computer with a USB cable

<figure class="third">
    <a href="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-hardware-setup.JPG"><img src="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-hardware-setup.JPG"></a>
    <a href="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-connection1.JPG"><img src="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-connection1.JPG"></a>
    <a href="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-connection2.JPG"><img src="/assets/images/Phidgets/VINT-TMP1200-2xRTD-set-connection2.JPG"></a>
    <figcaption>TMP1200 Set – Setup</figcaption>
</figure>


#### Probe Installation

One probe should be installed into the lower part of the drum such that it is fully immerged into the bean mass measuring the *bean temperature (BT)*. The other probe should be installed in the middle of the drum such that it measures the air temperature just above the bean mass to report the *environmental temperature (ET)*. Both probes should be installed such that most part of their 11cm shield stays inside the drum without touching the drum paddels. To achieve this, the probes can be bended carefully inside the drum, but not at the tip where the sensor element sits.

Each of the TMP1200 modules have to be connected to a port on the HUB0000. The one connected to the BT probe at a lower port number (e.g. port 0) than the one connected to the ET probe (e.g. port 5).


#### Hardware Test

Test your hardware setup and driver installation using the [Phidget Control Panel](https://www.phidgets.com/docs/Phidget_Control_Panel) by following the instructions found in the [user guide of the TMP1200 module](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=968).



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
Note that the [Phidget Control Panel](https://www.phidgets.com/docs/Phidget_Control_Panel) needs to be closed beforehand to allow Artisan to connect to the Phidget hardware as only one app at a time can communicate with the modules.
{: .notice--primary}



### Possible Extensions

#### Ambient modules

The [ambient modules](#vint-ambient-modules-extension) can be plugged additionally into the Phidget HUB0000 to add ambient temperature, humidity, and barometric pressure data automatically to every roast. See
[below](#vint-ambient-modules-extension) for details on the setup and configuration.

#### Further devices

You can easily plug additional [VINT modules supported by Artisan](/devices/phidgets/) into the free ports of the Phidget HUB0000 or add any other [device supported by Artisan](/devices/) like a USB Phidget.

<a id="ambient-modules-extension"></a>
## 3. VINT Ambient Modules Extension

### Parts

This extension is composed from the following 4 additional parts.

- 1x [HUM1000 Humidity Phidget VINT Module](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=644)
- 1x [PRE1000 Barometer Phidget VINT Module](https://www.phidgets.com/?tier=3&catid=7&pcid=5&prodid=719)
- 2x [VINT Cable 10cm](https://www.phidgets.com/?tier=3&catid=30&pcid=26&prodid=153)

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

Test your hardware setup and driver installation using the [Phidget Control Panel](https://www.phidgets.com/docs/Phidget_Control_Panel) by following the instructions found in the [user guide of the HUM1000 module](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=644) and the [user guide of the PRE1000 module](https://www.phidgets.com/?tier=3&catid=7&pcid=5&prodid=719).


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

Artisan will prompt you to enter the elevation in metres above sea level (MASL) for your location. This value is important to calculate the correct barrometric pressure from the PRE1000 pressure sensor values.

To test the Artisan setup for the Ambient Modules set, just press ON and check if humidity, barometric pressure and ambient temperatures are correctly set in the Roast Properties dialog (menu `Roast >> Properties`) of Artisan.


<figure class="full">
    <a href="/assets/images/Phidgets/artisan-ambient-data.png"><img src="/assets/images/Phidgets/artisan-ambient-data.png"></a>
    <figcaption>Ambient Data in Artisan</figcaption>
</figure>


**Watch out!** 
Note that the [Phidget Control Panel](https://www.phidgets.com/docs/Phidget_Control_Panel) needs to be closed beforehand to allow Artisan to connect to the Phidget hardware as only one app at a time can communicate with the modules.
{: .notice--primary}


