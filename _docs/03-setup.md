---
title: "Setup"
permalink: /docs/setup/
excerpt: "Setup Artisan for a first roast"
last_modified_at: 2018-05-15T15:59:00-04:00
---

## Setup Hardware for Artisan

### Configure for a supported machine

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

### Configure for supported devices

Port settings are found under Config>Port IF they are needed.  

Here is a quick discussion of connecting a Phidget.  Each device will differ. Connecting a Phidget is easy and you don't have to use the Port menu.  

For a Phidget 1048, the connections were made as follows:
![Phidget Connections](/assets/images/gsg/phidget wiring.jpg) As thermocouples differ your wiring colors may vary.  And different devices will connect differently.

The correct wiring colors for the thermocouples used were as follows:

1. BT G – white
2. BT 0 – Red
3. ET G – white with blue stripe
4. ET 0 – white with red stripe
![Phidget Wirring](/assets/images/gsg/ET0 white with red stripe.jpg)

Click for [detailed Phidget information in Artisan](https://artisan-roasterscope.blogspot.de/2017/12/more-phidgets.html)


### Configure Language, Temps and Sampling

*Language and Temp C or F*

Menu>Config>Temperature and Menu>Config>Language are where you go to choose your language and Celsius or Fahrenheit and switch between the two if you like.  

*Symbolic BT/ET*

What BT and ET temperatures do you want as reference points?

Some roasters are just fine with the readings their machines put out from their thermocouples.  Each machine is different and each machine’s thermocouples are placed differently and read differently.  Learn your machine is something you will hear over and over.  That said are you happy with first crack being at 365° or do you want it to be at 390°?  In order to adjust your machine thermocouples to give you dry end or first crack at temps that people think they should be at, you can enter an adjustment under Config>Device on the Tab – Symb ET/BT.  ![symoblic bt](/assets/images/gsg/device assignment - symbolic bt.png)


Also don’t expect these to match the PID in the roaster if the probes are in different places.

Do you have to do this? NO.    You will know your roaster best and these data points aren’t absolutes, they are just reference point.  Sight and smell and will tell you best when dry end and first crack happen.  Make sure to use a lower case “x” and an upper case won’t work.  If you see a reading of -1 in the temp LCD’s your formula may be incorrect.

*Sampling and Oversampling*

The default for sampling is set to 3s.  For a Phidget device one second is possible, and Artisan 1.3 goes down to .5s now.  Oversampling will take two readings per interval and average them.

If you go below a 3s interval you will get a popup warning ![interval warning](/assets/images/gsg/sampling interval warning.png)


You can try it lower and see if your equipment can handle it.  There have been reports that if you go down to 1s sampling, do NOT check oversampling as it causes very jumpy lines.  

Click for [more information on sampling in
Artisan](https://artisan-roasterscope.blogspot.com/2014/01/sampling-interval-smoothing-and-rate-of.html)

NOTE *Unplug Your Laptop Before You Roast*
Note that for most people unless you have a USB isolator you need to unplug your computer when using Artisan or will get feedback loops that will create all sorts of crazy spikes in the graph.  If you are using a desktop I guess you need to get an isolator.  

# Settings- Load, Load Recent, Save

Menu>Help> is where you go to load and save settings.  Load Recent is a shortcut to settings you have recently used.  

# Information for Troubleshooting

Menu>Help is a place you can find information on Errors, Messages from the program, a Serial log, search your settings, and information on the platform you are using.  

#Factory Reset

If you ever need to reset Artisan to factory settings, it's under Menu>Help>Factory Reset.  

# Roaster Setup Specific Information
[*Huky*](https://drive.google.com/drive/u/0/folders/0B4HTX5wS3NB2TFVid0h2TGxBWG8) 


[*Hottop*](https://drive.google.com/file/d/0B4HTX5wS3NB2ZGxsTU4tbmtVUmM/edit)

[*US Roaster Corp*](https://www.home-barista.com/home-roasting/us-roaster-artisan-start-up-t51065.html)
