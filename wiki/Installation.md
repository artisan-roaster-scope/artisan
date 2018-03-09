Setup Artisan
=============

Introduction
------------

There are usually two downloads needed in order to get the `artisan` software up and running on your platform, a driver for your meter (if it is USB) and the `artisan` application itself. 

1. Install USB driver
2. Install `artisan` application
3. Connect your meter via USB/serial
4. Launch `artisan` application
5. Configure device and serial settings

Installation Windows
--------------------

For versions before v0.6 the main application is called artisan.exe and it is located inside the zip file. To start artisan click on artisan.exe. There are three configuration steps needed after downloading and unziping the artisan zip file.  

The v0.6 and later versions are distributed with an installer that installs also the Visual C++ runtime library from Microsoft if needed. So the next step can be skipped for those versions.
 
### Visual C++ Library Requirement

Artisan for Windows needs a Visual C++ runtime library (file) from Microsoft. If artisan cannot start it will open a window error. This is because your computer is missing this file.
If you get a window error when you try to start artisan, install this program:

[Microsoft Visual C++ 2008 SP1 Redistributable Package (x86)](http://www.microsoft.com/downloads/en/details.aspx?familyid=A5C84275-3B97-4AB7-A40D-3802B2AF5FC2&displaylang=en)

If artisan starts when clicling on artisan.exe (a window pops open with many buttons), then your computer already have this file and you don't need to install anything.
Newer OS like Windows 7 come with this file.


Installation Mac OS X
---------------------
(>=10.9, 64bit processor only)

1. Install USB/serial driver
   + for Omega HH806AU and HH506RA meters download and run the [FTDI VCP OS X installer](http://www.ftdichip.com/Drivers/VCP.htm)
   NOTE: OS X 10.9 and later contain already support for the FTDI hardware and therefore no additional driver needs to be installed on those systems
   + for Omega HH309A meters (with USB cable) download and run the VCP OS X installer to install the [CP210x CP210x driver from Silicon Labs](http://www.silabs.com/products/mcu/Pages/USBtoUARTBridgeVCPDrivers.aspx)
   + for the original Voltkraft USB cable it is the [CP210x driver from Silicon Labs](http://www.silabs.com/products/mcu/Pages/USBtoUARTBridgeVCPDrivers.aspx)
   + some other serial2USB dongles use the [Prolific PL2303 driver](http://prolificusa.com/pl-2303hx-drivers/)

2. Download and run the [Artisan OS X installer](http://code.google.com/p/artisan/downloads/list)
3. on OS X 10.8 Mountain Lion and later you need to (temporarily during installation) tick "Allow applications downloaded from Anywhere" in the Security & Privacy Preference Panel to start the app.
4. Double click on the `dmg` file you just downloaded
5. Double click the disk image which appears on your desktop
6. Drag the `artisan` application icon to your `Applications` directory.
7. On first app start Mac OS X can warn about unidentified developer. See [https://support.apple.com/kb/PH21769](https://support.apple.com/kb/PH21769) on how to open an app from an unidentified developer.
8. On OS X: after first application start, tick again "Allow applications downloaded from Anywhere" in the Security & Privacy Preference Panel

Installation Linux
------------------

1. Install USB/serial driver4

Note that the FTDI serial driver is built-in for most Linux kernels after 3.5. 

2. Download and install the Artisan Linux installer for your platform

The Linux package is compatible with Ubuntu Linux 12.04/12.10 (glibc 2.15) and CentOS 6.3/6.4 (glibc 2.12). For now, we simply offer a .deb Debian package as well as an .rpm Redhat package that you have to install manually. This can be done by either double clicking the package icon from your file viewer or by entering the following commands in a shell. 

**Ubuntu/Debian**

+ install
      
```
  # sudo dpkg -i artisan_<version>.deb
```

+ uninstall

```
  # sudo dpkg -r artisan
```


**CentOS/Redhat**

+ install
   
```
  # sudo rpm -i artisan_<version>.rpm
```
   
+ uninstall
   
```
  # sudo rpm -e artisan
```


In case you run into permission problems such that Artisan is not allowed to read or write to the selected `/dev/_USB_` device, you might need to add your account (_username_) to the *dialout* group via

```
  # sudo adduser <username> dialout
```

After this command you might need to logout and login again. Try 

```
  # id
```

that your account was successful added to the dialout group.

**Arch Linux**

Artisan is available via the [Arch User Repository (AUR)](https://aur.archlinux.org/packages/artisan-roaster-scope/).



### Consistent USB names on Debian (by Rob Gardner)

On some Debian-based systems the USB device names are different, once /dev/tty/USB0 another time /dev/tty/USB1, on each connect of the same device. The solution is to add a udev rule that creates a symbolic link with a constant name to point to the actual device. In my situation, I added a file called 

```
  /etc/udev/rules.d/datalogger.rules
```

that contains this

```
  ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", GROUP="plugdev", SYMLINK="tmd-56"
```

This tells udev to create a symbolic link "tmd-56" to point to the real device file. You can use the 'lsusb' command to easily find the vendor and product ID for your device. Then I just simply tell Artisan that my serial port is /dev/tmd-56 and it always finds it, no matter
if the probe is plugged in before or after starting Artisan. You may need to customize the plugdev group also for your distro and add
yourself to the plugdev group. On some systems the "dialout" group is used for serial devices (see above).


Device Configuration
--------------------

Once Artisan is up, chose your device using the menu *Conf* and then select the *Device* submenu. RS232 meters don't need any drivers but USB meters do. Fuji PIDs don't need any drivers (but they need an RS485-RS232 converter). Most common are the following drivers (check your serial2USB device chip to decide which one to install)

+ [VCP from FTDI](http://www.ftdichip.com/Drivers/VCP.htm)
+ [CP210x from Silicon Labs](http://www.silabs.com/products/mcu/Pages/USBtoUARTBridgeVCPDrivers.aspx)
+ [PL2303 from Prolific](http://prolificusa.com/pl-2303hx-drivers/) (on Mac OS X 10.8 and higher some reported that the org. Profilic driver failed to work, but the [NoZAP driver](http://sourceforge.net/projects/osx-pl2303/) did work).

To install a USB driver. Plug the meter in USB port. Let Windows find (for Mac setup see above) and install the driver automatically through the internet. You can also install the driver through manufacturer CD if you have one, or thorugh the manufacturer webpage

### Omega HH806AU / Omega HH802U / Amprobe TMD-56

The Omega HH806AU, HH802U as well as the Amprobe TMD-56 device are supported by Artisan only if they are communicating on channel 0.

+ How to check the channel number

```
When the meter is off press [C/F] key and [POWER] for 5
seconds, LCD's main display will show channel number,
the second display will show ID number.
```

+ How RESET the meter to channel zero

```
To SET CH/ID to 00,00, by pressing the "T1-T2" key
(labeled "Hi/Lo Limits" on the HH802U) and
the power key for more than 6 seconds with the meter
powered down. The meter will set channel and ID
to 00,00 status. The second display will show 00,
which means that the channel and ID has been set to
00.
```

### Fuji PXR/PXG 4 & 5 PID

Artisan uses one decimal point. You have to manually configure your pid so that it outputs one digit after the  decimal point. See page 42 in the [instruction manual](http://www.instrumart.com/assets/PXR459_manual.pdf).

### Aillio Bullet R1

On Linux, Artisan needs read/write access to the USB device.
The easiest way to make sure permissions are always setup is to create
a udev rule.

Create a file in `/etc/udev/rules.d` named `60-aillio-r1.rules` containing
the following line:

```
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5741", MODE="0660", GROUP="you-group-name"
```

Make sure GROUP is set correctly based on your group.  Most of the
time your group name matches your user name, but you can confirm that
by running `id` on a terminal.


Serial Configuration
--------------------

The serial settings for the meters (devices) are already configured by the artisan software automatically when you select a device for the first time (or when you change devices). Once you have chosen a device, the correct serial configuration is loaded and it will remain in memory. The only setting that is not configured is the serial port number being used. 
To find out your serial port, select the correct comm port from the ports popup.

You can test to see if you have the correct comm port by clicking the green button "ON" on the top of the main window. If you see the two temperatures from the meter come up on the LCDs, you have completed all the configuration steps. You can now start using artisan.

Report problems on the [Artisan user mailing list](https://lists.mokelbu.de/listinfo/artisan-user)
    
