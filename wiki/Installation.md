# Installation Instructions

## Step 0: Verify that your hardware is supported

Verify that your operating system fulfills the requirements listed under supported [Platforms](https://artisan-scope.org/about/#Platforms).

Verify that your roasting machine and the devices you plan to operate with Artisan are among the [Supported Machines](https://artisan-scope.org/machines/index) or [Supported Devices](https://artisan-scope.org/devices/index).

## Step 1: Download Artisan for your platform

Find and download the package of the latest release for your platform. The filenames are as follows, with `x.x.x` the version number.

* OS X: `artisan-mac-x.x.x.dmg`
* Windows: `artisan-win-x.x.x.zip`
* Linux Redhat/CentOS: `artisan-linux-x.x.x.rpm`
* Linux Debian/Ubuntu: `artisan-linux-x.x.x.deb`
* Raspberry Pi: `artisan-linux-x.x.x_raspbian-XX.deb`

## Step 2: Install Artisan on your system

### Windows

Extract the downloaded zip archive and start the included installer.

### Mac OS X

Mount the installation `.dmg` archive with a double-click and drag the contained `Artisan.app` to your `Applications` folder

You need to (temporarily during installation) tick "Allow applications downloaded from Anywhere" in the Security & Privacy Preference Panel to start the app. On first app start Mac OS X can warn about unidentified developer. See https://support.apple.com/kb/PH21769 on how to open an app from an unidentified developer. After first application start, tick again "Allow applications downloaded from Anywhere" in the Security & Privacy Preference Panel.

### Linux

Install the downloaded installer file by a double-click or run the installer via the following console command on 

__Redhat/CentOS__

```
# sudo rpm -i artisan-linux-x.x.x.rpm
```

__Debian/Ubuntu/Raspian__

```
# sudo dpkg -i artisan-linux-x.x.x.deb
```


## Step 3: Install serial driver (if needed)

To operate some devices like Phidget modules or certain meters you need to install corresponding drivers. See the corresponding Section under [Supported Devices](https://artisan-scope.org/devices/index) for further details.


### Linux

In case you run into permission problems such that Artisan is not allowed to read or write to the selected /dev/_USB_ device, you might need to add your account (username) to the dialout group via

```
# sudo adduser <username> dialout
```

After this command you might need to logout and login again. Try

```
# id
```

that your account was successful added to the dialout group.


Note that for apps running by non-root users access to Phidgets or Yoctopuce devices require the installation of corresponding udev rules. Check the [Phidgets](https://www.phidgets.com/docs/OS_-_Linux#Advanced_Information) and [Yoctopuce](https://www.yoctopuce.com/EN/article/how-to-begin-with-yoctopuce-devices-on-linux) platform installation notes.



## Step 4: Configure Artisan for your setup

You need to tell Artisan which machine or devices you attached. Startup Artisan and select your roasting machine (menu `Config >> Machines`) or open the Device Assignment dialog (menu `Config >> Device`) and configure your device here.

The serial settings for meters are already configured by Artisan automatically when you select a device for the first time (or when you change devices). The only setting that is not configured is the serial port number being used. To find out your serial port, connect your device/meter and select the correct comm port from the ports popup menu. You can test to see if you have the correct comm port by clicking the green button "ON" on the top of the main window. If you see the two temperatures from the meter come up on the LCDs, you have completed all the configuration steps. You can now start using artisan.


# Further Specific Notes

## Consistent USB names on Debian (by Rob Gardner)

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

## Omega HH806AU / Omega HH802U / Amprobe TMD-56

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

## Fuji PXR/PXG 4 & 5 PID

Artisan uses one decimal point. You have to manually configure your pid so that it outputs one digit after the  decimal point. See page 42 in the [instruction manual](http://www.instrumart.com/assets/PXR459_manual.pdf).

## Aillio Bullet R1

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