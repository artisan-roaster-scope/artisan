#summary Setup Artisan

=Introduction=

There are usually two downloads needed in order to get the `artisan` software up and running on your platform, a driver for your meter (if it is USB) and the `artisan` application itself. 

  # Install USB driver
  # Install `artisan` application
  # Connect your meter via USB/serial
  # Launch `artisan` application
  # Configure device and serial settings

=Installation Windows=

For versions before v0.6 the main application is called artisan.exe and it is located inside the zip file. To start artisan click on artisan.exe. There are three configuration steps needed after downloading and unziping the artisan zip file.  

The v0.6 and later versions are distributed with an installer that installs also the Visual C++ runtime library from Microsoft if needed. So the next step can be skipped for those versions.
 
===Visual C++ Library Requirement===

Artisan for Windows needs a Visual C++ runtime library (file) from Microsoft. If artisan cannot start it will open a window error. This is because your computer is missing this file.
If you get a window error when you try to start artisan, install this program:

Microsoft Visual C++ 2008 SP1 Redistributable Package (x86) 

http://www.microsoft.com/downloads/en/details.aspx?familyid=A5C84275-3B97-4AB7-A40D-3802B2AF5FC2&displaylang=en

If artisan starts when clicling on artisan.exe (a window pops open with many buttons), then your computer already have this file and you don't need to install anything.
Newer OS like Windows 7 come with this file.

=Installation Mac OS X (>=10.6.x, 64bit processor only)=

  # Install USB/serial driver
    ** for Omega HH806AU and HH506RA meters download and run the [http://www.ftdichip.com/Drivers/VCP.htm FTDI VCP OS X installer]
    ** for Omega HH309A meters (with USB cable) download and run the VCP OS X installer to install the [http://www.silabs.com/products/mcu/Pages/USBtoUARTBridgeVCPDrivers.aspx CP210x driver from Silicon Labs]
    ** for the original Voltkraft USB cable it is the [http://www.silabs.com/products/mcu/Pages/USBtoUARTBridgeVCPDrivers.aspx CP210x driver from Silicon Labs]
   ** some other serial2USB dongles use the [[http://prolificusa.com/pl-2303hx-drivers/ Prolific PL2303 chips]] (on Mac OS X 10.8 and higher some reported that the org. Profilic driver failed to work, but the [http://sourceforge.net/projects/osx-pl2303/ NoZAP driver] did work)
  # Download and run the [http://code.google.com/p/artisan/downloads/list Artisan OS X installer]
  ## on OS X 10.8 Mountain Lion you need to tick "Allow applications downloaded from Anywhere" in the Security & Privacy Preference Panel to start the app
  ## Double click on the `dmg` file you just downloaded
  ## Double click the disk image which appears on your desktop
  ## Drag the `artisan` application icon to your `Applications` directory.

=Installation Linux=

The Linux package is compatible with Ubuntu Linux 12.04/12.10 (glibc 2.15) and CentOS 6.3/6.4 (glibc 2.12). For now, we simply offer a .deb Debian package as well as an .rpm Redhat package that you have to install manually. This can be done by either double clicking the package icon from your file viewer or by entering the following commands in a shell.

 * Ubuntu/Debian
  ** install
{{{
  # sudo dpkg -i artisan_<version>.deb
}}}
  ** uninstall
{{{  
  # sudo dpkg -r artisan
}}}
 * CentOS/Redhat
  ** install
{{{
  # sudo rpm -i artisan_<version>.rpm
}}}
  ** uninstall
{{{
  # sudo rpm -e artisan
}}}

In case you run into permission problems such that Artisan is not allowed to read or write to the selected /dev/_USB_ device, you might need to add your account (_username_) to the *dialout* group via

{{{
  # sudo adduser <username> dialout
}}}

After this command you might need to logout and login again. Try 

{{{
  # id
}}}

that your account was successful added to the dialout group.

=Device Configuration=

Once Artisan is up, chose your device using the menu *Conf* and then select the *Device* submenu. RS232 meters don't need any drivers but USB meters do. Fuji PIDs don't need any drivers (but they need an RS485-RS232 converter). Most common are the following drivers (check your serial2USB device chip to decide which one to install)

  * [http://www.ftdichip.com/Drivers/VCP.htm VCP from FTDI]
  * [http://www.silabs.com/products/mcu/Pages/USBtoUARTBridgeVCPDrivers.aspx CP210x from Silicon Labs]
  * [http://prolificusa.com/pl-2303hx-drivers/ PL2303 from Prolific] (on Mac OS X 10.8 and higher some reported that the org. Profilic driver failed to work, but the [http://sourceforge.net/projects/osx-pl2303/ NoZAP driver] did work).

To install a USB driver. Plug the meter in USB port. Let Windows find (for Mac setup see above) and install the driver automatically through the internet. You can also install the driver through manufacturer CD if you have one, or thorugh the manufacturer webpage

==Omega HH806AU / Amprobe TMD-56==

The Omega HH806AU as well as the Amprobe TMD-56 device are supported by Artisan only if they are communicating on channel 0.

 * How to check the channel number

{{{
When the meter is off press [C/F] key and [POWER] for 5
seconds, LCD's main display will show channel number,
the second display will show ID number.
}}}

 * How RESET the meter to channel zero

{{{
To SET CH/ID to 00,00, by pressing "T1-T2" key and
" " power key for more than 6 seconds with the meter
powered down. The meter will set channel and ID
to 00,00 status. The second display will show 00,
which means that the channel and ID has been set to
00.
}}}

==Fuji PXR/PXG 4 & 5 PID==

Artisan uses one decimal point. You have to manually configure your pid so that it outputs one digit after the  decimal point. See page 42 in the instruction manual: http://www.instrumart.com/assets/PXR459_manual.pdf


=Serial Configuration=

The serial settings for the meters (devices) are already configured by the artisan software automatically when you select a device for the first time (or when you change devices). Once you have chosen a device, the correct serial configuration is loaded and it will remain in memory. The only setting that is not configured is the serial port number being used. 
To find out your serial port, you can press the scan button and select the correct comm port from the options found by the Scan button.

You can test to see if you have the correct comm port by clicking the green button "ON" on the lower left corner. If you see the two temperatures from the meter come up on the LCDs, you have completed all the configuration steps. You can now start using artisan.

Report problems here:

[https://lists.mokelbu.de/listinfo/artisan-user]
    