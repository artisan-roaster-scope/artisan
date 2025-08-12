---
layout: single
permalink: /modbus_serial/
title: "MODBUS Serial"
excerpt: "RTU/ASCII"
header:
  overlay_image: /assets/images/modbus-logo.jpg
  image: /assets/images/modbus-logo.jpg
  teaser: assets/images/modbus-logo.jpg
toc: true
toc_label: "On this page"
toc_icon: "cog"
---
The MODBUS RTU/ASCII protocols are communicated over a RS485 connection. This is usually connects via a serial RS485-to-USB converter to the computer.

You need to install the corresponding serial driver for the chipset of this converter on your PC, otherwise no serial port for the device is created by your operating system on connecting the machine. Most common drivers are

**Watch out!** The FTDI driver is preinstalled on virtually all Linux distributions as well as all OS X versions supported by Artisan. Installing an additional FTDI driver on those operating system might lead to instabilities!
{: .notice--primary}

+ __FTDI VCP__: [FTDI Chip](http://www.ftdichip.com/Drivers/VCP.htm)
+ __CP210x__: [Silicon Labs](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers)
+ __PL2303__: [Prolific](http://www.prolific.com.tw/US/ShowProduct.aspx?p_id=225&pcid=41)
+ __CH34x__:
  - Windows: [http://www.wch.cn/download/CH341SER_EXE.html](http://www.wch.cn/download/CH341SER_EXE.html)
  - macOS: [http://www.wch.cn/downloads/file/178.html](http://www.wch.cn/downloads/file/178.html)
  - Linux: [http://www.wch.cn/download/CH341SER_LINUX_ZIP.html](http://www.wch.cn/download/CH341SER_LINUX_ZIP.html)




## Serial Driver Cheat Sheet
{: style="color: #4C97C3;" }

.. table to be extended and corrected as we receive new information from you ..

Machine                         | Driver | Remarks
------------------------------- | ------ | -----
[Ambex](/machines/ambex/) | FTDI
[Arc](/machines/arc/) | CP210x | CH34x on newer Models
[Besca](/machines/besca/) | FTDI | CH34x on some older machines
[BellaTW](/machines/bellatw/) | PL2303 | CH34x on some machines
[Bideli](/machines/bideli/) | CH34x | 
[BlueKing](/machines/blueking/) | CP210x | on some older machines FTDI, on others CH34x
[BC Roasters](/machines/bc/) | CP210x | on some older machines FTDI, on others CH34x
[Coffeed](/machines/coffed/) | CH34x
[Coffee Tech](/machines/coffeetech/) | FTDI
[Coffee Machines Sale](/machines/cms/) | CH34x
[Dätgen](/machines/datgen/) | CH34x
[Dongyi](/machines/dongyi/) | CP210x | FTDI on some older machines
[Easyster](/machines/easyster/) | FTDI
[Garanti](/machines/garanti/) | CP210x
[Golden Roasters](/machines/goldenroasters/) | CH34x
[Has Garanti](/machines/hasgaranti/) | FTDI
[HB](/machines/hb/) | CP210x
[Kaleido](/machines/kaleido/) | CH34x
[KapoK](/machines/kapok/) | CH34x
[NOR](/machines/nor/) | FTDI | CH34x (on N Series V.4 old machines)
[Nordic](/machines/nordic/) | PL2303
[Plugin Roast](https://www.pluginroast.com.br/) | CH34x
[Phoenix](/machines/phoenix/) | CH34x
[Proaster](/machines/proaster/) | FTDI
[Roastmax](/machines/roastmax/) | FTDI
[Rolltech](/machines/rolltech/) | CH34x
[San Franciscan](/machines/sf/) | FTDI
[Santoker](/machines/santoker/) | CP210x | FTDI on some machines
[Sedona](/machines/sedona/) | CP210x
[Toper](/machines/toper/) | CP210x | CH34x on some machines
[Yoshan](/machines/yoshan/) | CP210x


<!--
[HARTANZAH](/machines/hartanzah/) | FTDI
-->