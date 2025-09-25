---
layout: single
permalink: /devices/meters/
title: "Meters"
excerpt: "Omega, Center,.."
header:
  overlay_image: /assets/images/meters-logo.jpg
  image: /assets/images/meters-logo.jpg
  teaser: assets/images/meters-logo.jpg
toc: true
toc_label: "On this page"
toc_icon: "cog"
---
Artisan implements the communication protocols of a number of handheld meters that can operate autonomous, run on their own power source (battery or power-plug), come with a display and feature a serial interface to communicate with an external software.

Some of these devices come with an internal serial-2-USB interface, while others require an external serial-2-USB interface.

Any of these meters require a serial device driver installed that allows the computer to communicate with the serial-2-USB chip implemented by the hardware interface. Most common are

+ [VCP from FTDI](http://www.ftdichip.com/Drivers/VCP.htm) (preinstalled on Linux/macOS/Windows)
+ [CP210x from Silicon Labs](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers)
+ [PL2303 from Prolific](http://www.prolific.com.tw/US/ShowProduct.aspx?p_id=225&pcid=41)
+ __CH34x__:
  - Windows: [http://www.wch.cn/download/CH341SER_EXE.html](http://www.wch.cn/download/CH341SER_EXE.html)
  - macOS: [http://www.wch.cn/downloads/file/178.html](http://www.wch.cn/downloads/file/178.html)
  - Linux: [http://www.wch.cn/download/CH341SER_LINUX_ZIP.html](http://www.wch.cn/download/CH341SER_LINUX_ZIP.html)

**Watch out!** The FTDI driver is preinstalled on virtually all Linux distributions as well as all OS X versions supported by Artisan. Installing an additional FTDI driver on those operating system might lead to instabilities!
{: .notice--primary}

## Temperature Meters

### Single Channel

The single temperature meters listed above are rather simple and cost-efficient. If it is only the BT curve you are interested and don't want to spent too much money they are a good option. Note that the CENTER 300 is also on the market under the label VOLTCRAFT K201 and 300K with minor differences.

* [CENTER 300](http://www.centertek.com/product_d.php?lang=en&tb=1&id=64&cid=67) / VOLTCRAFT K201 / VOLTCRAFT 300K
  - Single K-Type
  - RS232 Interface (9600-8N1)
  - 9V Battery only
  - Software optional
  - Minimal stable sampling rate in Artisan: 4sec
* [CENTER 302](http://www.centertek.com/product_d.php?lang=en&tb=1&id=70&cid=67)
  - Single K/J-Type
  - RS232 Interface (9600-8N1)
  - 9V Battery only
  - Software optional
  - Minimal stable sampling rate in Artisan: 4sec
* [CENTER 305](http://www.centertek.com/product_d.php?lang=en&tb=1&id=82&cid=67)
  - Single K-Type
  - RS232 Interface (9600-8N1), cable included
  - 9V Battery only
  - Software included
  - Minimal stable sampling rate in Artisan: 4sec
* Apollo I DT301 (discontinued)
  - Single K/J-Type
  - Built in USB to serial converter (9600-8N1)

### Dual Channel

The dual temperature meters are perfect for the standard use of Artisan to log the BT and ET temperature curves. If your probe is a K-Type, which is the standard for measuring BT/ET in a coffee roaster, you can choose from any of the above meters. The Amprobe is especially interesting due to its competitive price tag (see [this post](http://artisan-roasterscope.blogspot.de/2013/06/artisan-monitoring-londinium.html) to learn how the Amprobe and Artisan helped to investigate the Londinium group temperature stability). The Omega HH506RA (or its EXTECH variant) is interesting for its optical-isolated serial2USB converter. However, this converter is an add-one that has to be purchased separately and the fixed serial speed of that device is quite low (although it works well with Artisan). All of the devices listed here exclusively run from battery, but for the last one which does not need any external power but for the USB connection

**Watch out!** Artisan maps the first input channel of a connected meter to ET (environment temperature) and the second input channel to BT (bean temperature).  When using a single probe for BT only, be sure to connect it to the second input channel.  For example, with a Mastech MS6514 the temperature probe for BT connects to input 'T2'.
{: .notice--primary}

* [CENTER 301](http://www.centertek.com/product_d.php?lang=en&tb=1&id=67&cid=67)
  - Dual K-Type
  - RS232 Interface (9600-8N1)
  - 9V Battery only
  - Software optional
  - Minimal stable sampling rate in Artisan: 4sec
  - USB Driver: [CP210x from Silicon Labs](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers)
* [CENTER 303](http://www.centertek.com/product_d.php?lang=en&tb=1&id=73&cid=67) / VOLTCRAFT 302KJ / VOLTCRAFT KJ202
  - Dual K/J-Type
  - RS232 Interface (9600-8N1)
  - 9V Battery only
  - Software optional
  - Minimal stable sampling rate in Artisan: 4sec
  - USB Driver: [CP210x from Silicon Labs](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers)
* [CENTER 306](http://www.centertek.com/product_d.php?lang=en&tb=1&id=85&cid=67) / VOLTCRAFT K202
  - Dual K-Type
  - RS232 Interface (9600-8N1), cable included
  - 9V Battery only
  - Internal memory
  - Software included
  - Minimal stable sampling rate in Artisan: 4sec
  - USB Driver: [CP210x from Silicon Labs](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers)
* [Omega HH506RA](http://www.omega.com/pptst/HH506A_HH506RA.html) / [EXTECH 421509](http://www.extech.com/products/421509)
  - Dual K/J/T/E/R/S/N-Type
  - RS232 Interface (2400-7E1)
  - Internal memory
  - 9V Battery only
  - Optional optical-isolated serial2USB converter
  - Minimal stable sampling rate in Artisan: 5sec
  - USB Driver: FTDI build into Linux/macOS/Windows
* [Amprobe TMD-56](https://www.amprobe.com/product/tmd-56/) / [Omega HH806AU](https://www.omega.com/en-us/sensors-and-sensing-equipment/temperature/thermometers/p/HH806) / [Mastech MS6514](http://www.mastech-group.com/products.php?PNo=89) / [PerfectPrime TC2100GN TC2100, 2-Channel](https://www.amazon.com/dp/B0776SD6JC/ref=cm_sw_r_cp_api_i_DkbwFb7YX283X)
  - Dual K/J/T/E/R/S/N-Type
  - Built in USB to serial converter (19200-8E1)
  - Internal memory
  - 4 x 1.5V AAA Batteries or external power
  - USB Driver: [CP210x from Silicon Labs](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers)
* [Omega HH802U](http://www.omega.com/pptst/HH802_803.html)
  - Dual K/J-Type
  - Built in USB to serial converter (19200-8E1)
  - 4 x 1.5V AAA Batteries or external power
* [VOLTCRAFT PL-125-T2](https://www.conrad.de/de/temperatur-messgeraet-voltcraft-pl-125-t2-200-bis-1372-c-fuehler-typ-k-j-kalibriert-nach-werksstandard-ohne-zertifi-1012836.html)
  - Dual K/J-Type
  - Built in USB to serial converter (9600-8N1)
  - 3 x 1.5V AAA Batteries
  - USB Driver: [CP210x from Silicon Labs](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers)
* [Digi-Sense 20250-07](https://www.coleparmer.com/i/digi-sense-ir-thermometer-thermocouple-probe-input-and-nist-traceable-calibration-30-1/2025007) / [Extech 42570](https://www.extech-online.com/index.php?main_page=product_info&cPath=78_21_35&products_id=99)
  - 1x Dual Laser InfraRed + 1x Type K Input
  - RS232 Interface (9600-8N1)
  - Software included
  - 9V Battery
  - USB Driver: [CP210x from Silicon Labs](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers)

 
 
### Four Channel

Those 4 channel meters in the list below are all basically identical. Just that the CENTER 304 (and one of the two VOLTCRAFT K204, no typo here!, does not include any data logging capability. However, that does not matter for its use with Artisan. Therefore, selecting the CENTER 304 over the CENTER309 makes sense as it is usually the cheaper device (so take care, there are two different devices labeled VOLTCRAFT K204, but they can easily be distinguished by price). 

* [CENTER 304](http://www.centertek.com/product_d.php?lang=en&tb=1&id=76&cid=67) / VOLTCRAFT K204
  - Four K-Type
  - RS232 Interface (9600-8N1)
  - Software optional
  - 9V Battery or external power
  - Minimal stable sampling rate in Artisan: 4sec
  - USB Driver: [CP210x from Silicon Labs](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers)
* [CENTER 309](http://www.centertek.com/product_d.php?lang=en&tb=1&id=79&cid=67) / VOLTCRAFT K204 / [Omega HH309](https://www.omega.com/en-us/test-inspection/handheld-meters/temperature-and-humidity-and-dew-point-meters/hh309a-tc-logger/p/HH309A) / [General Tools DT309DL](http://www.tequipment.net/GeneralDT309DL.html)
  - Four K-Type
  - RS232 Interface (9600-8N1)
  - Internal memory
  - Software included
  - 9V Battery or external power
  - Minimal stable sampling rate in Artisan: 4sec
  - USB Driver: [CP210x from Silicon Labs](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers)
* [VOLTCRAFT PL-125-T4](https://www.conrad.de/de/temperatur-messgeraet-voltcraft-pl-125-t4-200-bis-1372-c-fuehler-typ-k-j-kalibriert-nach-werksstandard-ohne-zertifi-1013036.html)
  - Four K/J-Type
  - Built in USB to serial converter (9600-8N1)
  - 3 x 1.5V AAA Batteries
  - USB Driver: [CP210x from Silicon Labs](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers)
* [Tasi TA612C](https://www.tasimeter.com/environmental-tester/contact-thermometer/data-logging-thermoucouple-thermometer.html)
  - Four K/J-Type
  - Built in USB to serial converter (9600-8N1)
  - 3 * 1.5V AA batteries or USB power
  - USB Driver [CH341 USB](http://www.wch.cn/)
 
## Multi Meters

Multi-meters allow to read different types of sensors by measuring a voltage or current input. Artisan supports two devices that feature a communication interface. The TE VA18B and the Victor 86B also support one temperature channel connecting to a K-Type thermocouple.

* [Omega HHM28](http://www.omega.com/pptst/HHM10_20_30.html)
  - AC/DC volts and current
  - RS232 Interface (2400-8N1)
  - 9V Battery only
* TE VA18B
  - single K-Type TC
  - AC/DC volts and current
  - optical-isolated USB Interface (2400-8N1)
  - 9V Battery only
* [DMM Victor 86B](http://www.victor-multimeter.com/products/digital-multimeter/victor-86b-digital-multimeter-648.html)
  - single K-type TC
  - AC/DC volts, current, temperature
  - Built in UBS to serial converter (CP210x driver, 2400-8N1)
  - 3x 1.5V Battery only


## Others

* [Extech 755](http://www.extech.com/products/HD755) 
  - Differential Pressure Manometer (0.5psi)
  - USB Interface
  - 9V battery only
