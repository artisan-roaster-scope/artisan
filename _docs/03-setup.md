---
title: "Setup"
permalink: /docs/setup/
excerpt: "Setup Artisan for a first roast"
last_modified_at: 2018-05-15T15:59:00-04:00
---

## Setup Hardware for Artisan

### Configure for a supported machine

You will find many roaster manufacturers are now supporting Artisan.  In 2.0, you will find simplified setup for the ones offering support.  See [Artisan Machines](https://artisan-scope.org/machines/).

Under Config>Machine, Artisan 2.0 has direct support for:

	• Aillio
	• Atilla
	• BC Roasters
	• Besca
	• Bühler
	• Coffeed
	• Coffee Tech
	• Coffeetool
	• Diedrich
	• Giesen
	• Has Garanti
	• Hottop
	• IMF
	• Kaldi
	• Kirsch & Mausser
	• Loring
	• Phoenix
	• Proaster
	• Probat
	• San Franciscan
	• Sedona
	• Toper
	• US Roaster Corp

### Configure for supported devices

You will need to configure the hardware device taking the readings from the roaster if its not a listed roaster above.  

The various devices supported can be found [here](https://artisan-roasterscope.blogspot.com/2013/06/device-selection.html). Information on PID control can be found [here](https://artisan-roasterscope.blogspot.com/2016/11/pid-control.html).  A discussion of virtual devices and symbolic assignments is [here](https://artisan-roasterscope.blogspot.com/2014/04/virtual-devices-and-symbolic-assignments.html). The most critical symbolic assignment is for your bean temp and that is explained below.
Port settings are found under Config>Port IF they are needed.

Artisan can now configure certain Phidgets much like a Machine.

![Phidget Setup](/assets/images/gsg/phidget config.jpg)

*Example* - Here is a quick discussion of connecting a Phidget.  Each device will differ. Connecting a Phidget is easy and you don't have to use the Port menu.  

For a Phidget 1048, the connections were made as follows:
![Phidget Connections](/assets/images/gsg/phidget wiring1.jpg) As thermocouples differ your wiring colors may vary.  And different devices will connect differently.
The correct wiring colors for the thermocouples used were as follows:

1. BT G – white
2. BT 0 – Red
3. ET G – white with blue stripe
4. ET 0 – white with red stripe
![Phidget Wiring](/assets/images/gsg/ET0 white with red stripe.jpg)


Want to know more?

[Roasting with Phidgets in Artisan](https://artisan-roasterscope.blogspot.com/2017/12/roasting-with-phidgets.html) and [More on Phidgets in Artisan](https://artisan-roasterscope.blogspot.de/2017/12/more-phidgets.html) go into greater depth on using Phidgets.  

If you need support for your device, go to the [Community](https://artisan-scope.org/docs/community/) page to see where to get help.  


### Configure Language, Temps and Sampling

*Language and Temp C or F*

Menu>Config>Temperature and Menu>Config>Language are where you go to choose your language and Celsius or Fahrenheit and switch between the two if you like.  

*Symbolic BT/ET*

What BT and ET temperatures do you want as reference points?

Some roasters are just fine with the readings their machines put out from their thermocouples.  Each machine is different and each machine’s thermocouples are placed differently and read differently.  Learn your machine is something you will hear over and over.  That said are you happy with first crack being at 365° or do you want it to be at 390°?  In order to adjust your machine thermocouples to give you dry end or first crack at temps that people think they should be at, you can enter an adjustment under Config>Device on the Tab – Symb ET/BT.  ![symoblic bt](/assets/images/gsg/device assignment - symbolic bt.png)


Also don’t expect these to match the PID in the roaster if the probes are in different places.

Do you have to do this? NO.    You will know your roaster best and these data points aren’t absolutes, they are just reference point.  Sight and smell and will tell you best when dry end and first crack happen.  Make sure to use a lower case “x” and an upper case won’t work.  If you see a reading of -1 in the temp LCD’s your formula may be incorrect.

*Sampling and Oversampling*

The default for sampling is set to 3s.  For a Phidget device one second is possible, and Artisan 1.3 goes down to .5s now.  Oversampling will take two readings per interval and average them.  See the [Sampling](https://artisan-scope.org/docs/sampling/) page for more details.  

If you go below a 3s interval you will get a popup warning ![interval warning](/assets/images/gsg/sampling interval warning.png)


You can try it lower and see if your equipment can handle it.  There have been reports that if you go down to 1s sampling, do NOT check oversampling as it causes very jumpy lines.  



NOTE *Unplug Your Laptop Before You Roast*
Note that for most people unless you have a USB isolator you need to unplug your computer when using Artisan or will get feedback loops that will create all sorts of crazy spikes in the graph.  If you are using a desktop I guess you need to get an isolator.  

### Settings- Load, Load Recent, Save

Menu>Help> is where you go to load and save settings.  Load Recent is a shortcut to settings you have recently used. You can use Artisan with more than roaster by saving two sets of settings and then using Load Recent to change between roasters.   

### Information for Troubleshooting

Menu>Help is a place you can find information on Errors, Messages from the program, a Serial log, search your settings, and information on the platform you are using.  

### Factory Reset

If you ever need to reset Artisan to factory settings, it's under Menu>Help>Factory Reset.  
