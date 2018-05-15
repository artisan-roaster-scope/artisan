---
layout: single
permalink: /gsg/
header:
  overlay_image: /assets/images/teaser-small.jpg
  image: /assets/images/teaser-small.jpg
title: "Artisan Getting Started Guide"
toc: true
toc_label: "On this page"
toc_icon: "cog"
---

### ARTISAN GETTING STARTED GUIDE

Artisan Getting Started Guide is maintained by *Michael Herbert of Evergreen Buzz Buzz.*

![Artisan 1.3](assets/images/gsg/artisan 1.3.png)

**Roasters Covered**

You will find many roaster manufacturers are now supporting Artisan.  In 1.3, you will find simplified setup for the ones offering support.  See [Artisan Machines](https://artisan-scope.org/machines/).

Under Config>Machine, 1.3 has direct support for:

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

**Installing Software and Getting Connected to a Roaster**

Determine what connection devices you have.  Mine had a
[Phidget 1048](https://www.phidgets.com/?tier=3&catid=14&pcid=12&prodid=38).

First install the
[Phidget software drivers](https://www.phidgets.com/docs/Software_Overview).

Then you need to
[install Artisan](https://github.com/artisan-roaster-scope/artisan).

The installer, on a MAC or PC, will first remove your prior version but this won’t remove your prior settings if you have them. You can also downgrade to a previous version by just uninstalling the current version and re-installing the old version without losing any settings.  On a MAC, you will get a warning that Artisan is from an unidentified developer.  That is being worked on but go to Settings>Security and Privacy, and you will be able to allow Artisan to install.  NOTE, save your stable settings before changing any settings or installing a new version (Help>Save Settings).
More complete
[Artisan Installation Instructions](https://github.com/artisan-roaster-scope/artisan/blob/master/wiki/Installation.md) here.  You can install Artisan before your roaster arrives.  

Connecting the Phidget was easy.  
From my Phidget 1048 the connections were made as follows:
![Phidget Connections](assets/images/gsg/phidget wiring.jpg)
