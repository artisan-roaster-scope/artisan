---
title: "Quick-Start Guide"
permalink: /docs/quick-start-guide/
excerpt: "How to quickly install and setup Artisan"
last_modified_at: 2018-05-15T15:58:49-04:00
---

## Quick-Start Guide

**If you read through the topics on the left you will have a very good idea of how Artisan works.  This Quick-Start-Guide is not intended to answer all technical questions.**  Artisan Quick-Start Guide is maintained by *Michael Herbert of Evergreen Buzz Buzz.*  If you have suggestions for improving the content of the Quick-Start Guide or technical questions, please use the commmunity mailing list on the [Community](https://artisan-scope.org/docs/community) page.

![Artisan 1.3](/assets/images/gsg/artisan 1-3.png)

**Roasters Covered**

You will find many roaster manufacturers are now supporting Artisan.  In 1.3, you will find simplified setup for the ones offering support.  See [Artisan Machines](https://artisan-scope.org/machines/).

Under Config>Machine, Artisan 1.3 has direct support for:

	•	Aillio Bullet R1 including profile imports
	•	BC Roasters
	•	Bühler Roastmaster
	•	Coffed SR5/SR25
	•	Coffee-Tech FZ-94
	•	Coffeetool R500/3/5/15
	•	Giesen W1A/W6A/W15A
	•	IMF RM5/RM15
	•	K+M UG15/UG22
	•	Loring S7/15/35/70
	•	Phoenix ORO
	•	Proaster
	•	San Franciscan SF1-75
	•	Sedona Elite
	•	Toper TKM-SX
	•	US Roaster Corp

### Installing Artisan

[Download and install Artisan](https://github.com/artisan-roaster-scope/artisan) first.

The installer, on a MAC or PC, will first remove your prior version but this won’t remove your prior settings if you have them. You can also downgrade to a previous version by just uninstalling the current version and re-installing the old version without losing any settings.  

If installing on a MAC, you will get a warning that Artisan is from an unidentified developer.  That is being worked on, and for now go to Settings>Security and Privacy, and you will be able to allow Artisan to install.  

To ensure no issues, save your stable settings before changing any settings or installing a new version (Help>Save Settings).
More complete instructions on the [installations page](/_docs/02-installation.md).  You can install Artisan before your roaster arrives.  

### Setup for your hardware
If you don't have a Roaster that supports the Artisan effort and isn't automatically configured by choosing that Roaster under Cofig>Machines, you will need to connect your devices to the roaster and to your computer.  Then you will need to use Config>Devices to tell Artisan how to read your hardware.

Determine what connection devices you have.  For example, a
[Phidget 1048](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=38) can measure four temperatures.  First install the
[Phidget software drivers](https://www.phidgets.com/docs/Software_Overview), or other drivers as needed.  Then connect the hardware which was easy for a Phidget 1048:
![Phidget Connections](/assets/images/gsg/phidget wiring.jpg) As thermocouples differ your wiring colors may vary.
The correct wiring colors for the thermocouples used were as follows:

1. BT G – white
2. BT 0 – Red
3. ET G – white with blue stripe
4. ET 0 – white with red stripe
![Phidget Wirring](/assets/images/gsg/ET0 white with red stripe.jpg)

Click for [detailed Phidget information in Artisan](https://artisan-roasterscope.blogspot.de/2017/12/more-phidgets.html)

### Your first roast

With Artisan open, to do your first roast, go to Menu>View and make sure Controls and Readings are checked.  Then make sure your roaster is on and heating, and that the LCDs for temperatures are getting a reading.  

*Buttons and Sliders*

The main controls look like this:
![View Controls](/assets/images/gsg/view menu controls.png)

Artisan’s standard event buttons are as follows:
![Artisan buttons](/assets/images/gsg/standard buttons.png)

The buttons above with start and stop your roasts and indicate key time points in your roast that will be logged.  After using the roaster's trier, you push the button when the event occurs.  Pushing these buttons during a roast will add data to your roast log.  You can find the data under Roast>Properties>Data tab. Sliders can be used to create custom Events as well, but not the standard events.   

When you are ready to charge the roaster, push the On Button. Then push the Start button, and give it about 15 seconds before you charge the roaster, and push the Charge button at the bottom of Artisan.  Using the trier, when you determine you are at Dry End, hit the Dry End Button, and do the same for First Crack Start, and Drop.  After the roast completes, hit the off button.  Congratulations on your first roast.  

**NOTE:
*Unplug Your Laptop Before You Roast***

For most people unless you have a USB isolator you need to unplug your computer when using Artisan or will get feedback loops that will create all sorts of crazy spikes in the graph.  If you are using a desktop I guess you need to get an isolator.

Before or after your first roast, look at the [setup page](/_docs/03-setup.md)to see how to adjust your bean temp readings and your sampling rates.

You can save your graphs under File>Save Graph to various size formats or PDF.  You can aslo convert your data to other formats and export it under the File>Convert and File>Export commands.  You can import another roaster's file under File>Import.  

To review your own files you can use File>Open and search for a file or use the list under File>Open Recent.  When starting a roast you can choose File>New and pick one of the previous Roast Profiles you may have saved.  
