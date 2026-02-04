---
title: "Quick-Start Guide"
permalink: /docs/quick-start-guide/
excerpt: "How to quickly install and setup Artisan"
last_modified_at: 2021-02-12T15:59:00-04:00
toc: false
author: Michael Herbert
author_profile: true
---

## Quick-Start Guide

**Watch out!** 
If you read through the topics on the left you will have a very good idea of how Artisan works.  This Quick-Start-Guide is not intended to answer all technical questions.
{: .notice--primary}

Artisan Quick-Start Guide is maintained by *Michael Herbert of [CarefreeBuzzBuzz](https://www.carefreebuzzbuzz.com/){:target="_blank"}*. If you have suggestions for improving the content of the Quick-Start-Guide or technical questions, please use the [Artisan discussion forum](https://github.com/artisan-roaster-scope/artisan/discussions) (GitHub registration required).  When clicking links in this Quick-Start-Guide, we suggest you open links in a new window.  You can also find a great deal of more advanced information at the [Artisan Blog](https://artisan-roasterscope.blogspot.com/).  Use the search bar in the upper left.




### artisan.plus

Introduced as part of Artisan v2, [artisan.plus](https://artisan.plus/en/) is an inventory management system which is not covered in the Quick Start Guide. Artisan v2 connects to the inventory management service. This service manages your stock of beans and automatically subtracts batches as you roast them. Beans can be specified to every detail and only essential meta data of roasts is stored online in the cloud. All roast profiles stay local just with you and are not shared with the platform.  You can read the [Artisan Plus Quick Start Guide](https://doc.artisan.plus/docs/quick-start-guide/).  Signing up for this service is a great way to support Artisan.  

Additional popup menus in the Roast Properties dialog (menu `Roast` >> `Properties`) allow you to choose from your stock and have beans information filled in automatically.

The [artisan.plus service](https://artisan.plus/en/) features support for

- multiple users, machines and stores
- blends & certifications
- charts, tax reports & predictions
- Support for offline roasting which Cropster doesn't.  Your roasts and profiles are uploaded when you reconnect to Plus.  


### Learn what Artisan can do and Your First Roast 

**Best Practices - Learn to save your settings.**   Go to `Help` >> `Save Settings`  
Maybe the most important step. Save your settings and make a habit of it before every upgrade and when you change settings.  Also after installing a new version do two things; read the release notes so you can spot anything relevant to your roasting, and look over the shortcuts as new ones are often being added.  

Skim the pages of this Quick Start Guide, learn what Artisan RoasterScope can do, and then go back and read the pages of interest in detail. For each roast, an Artisan "profile" will be created and can be saved in various formats and can be exported for sharing under File>Save Graph (be sure to review these).  For most of the topics below, you will find a page in this Quick Start Guide, and some are linked.  

New as of 2026 are User Interface Modes:  Standard, Expert, and Production.  Artisan 4 starts in Standard mode, which restricts menus and dialogs to basic configurations and functionalities. By using the Mode menu, Artisan can be switched to Expert mode, which restores full functionality, similar to previous versions. Additionally, there's a Production mode that hides all configuration options and features only the UI elements and functions necessary for production.

**Standard Mode Choices**

1.	`Config` >> `Temperature`  
Pick ˚F or ˚C.
2.	Run `Config` >> `Machine`, or set up your devices, and make sure the LCDs show your temps.  Some of these configurations will change the sampling rate and that’s ok.  
3.	`Config`>> `Events` and `Config` >> `Alarms`  
This is where you will focus your most time in setting things up the first time.  `Config` >> [`Events`](https://artisan-scope.org/docs/events/) and `Config` >> [`Alarms`](https://artisan-scope.org/docs/alarms/)  
These are critical, but they also take some work.  For this step it's really critical that you read the QSG in detail. First thing decide if you will use buttons or sliders to record gas changes. Decide which boxes you want to check, including `Auto DROP` and `Auto CHARGE`. I use `Auto DROP` and `Auto CHARGE`. If you use `Auto CHARGE`, make sure you hit Start at least 10 seconds before you drop your beans.  I mark TP, MET and I show the Time Guide. For both Buttons and Alarms, there are additional settings in Expert Mode.  
4.	`Config` >> [`Axes`](https://artisan-scope.org/docs/axes/)  
Check Auto, and set your range for your Temperature and Delta axes. Starting points could be 0-500 ˚F and 0-40˚F/min, or 0-250˚C and 0-20˚C/min.
5.	`Config` >> [`Batch`](https://artisan-scope.org/docs/batches/)  
Choose a prefix name and turn on the counter. 
6.	`Config` >> [`Autosave`](https://artisan-scope.org/docs/autosave/)  
Check autosave and add to recent. Choose a location and set the path.   If you use cloud storage, you can access your profiles from any device anywhere.  Choose a file name prefix. Check the Help screen to decide what to include. See the Quick Start Guide for examples. If you don't use Autosave, then use `File` >> `Report` and `File` >> `Save Graph`  
to export reports on your roasts and graphs to post. You can use “;” to take a screenshot. 
7.	`Config` >> [`Phases`](https://artisan-scope.org/docs/phases/)  
For Phases LCD mode, choose time for Drying, Temp for Maillard, and check the box Phases LCD All in the Finishing Line. Other choices are yours.
8.	`Roast` >> [`Properties`](https://artisan-scope.org/docs/properties/)  
Fill in the information and start saving the various roast profiles that you may use again. You can click on the Roast Properties line on top of the graph to open the Roast Properties dialog.
6.	 Tools Menu  
Once you have roasted a few batches, go back and read the documentation on the items in the Tools menu:  Comparator and Designer.  In Expert mode you will also have Analyzer,Simulator, Wheel Graph, Transposer and Calculator.
7.	[Shortcuts](https://artisan-scope.org/docs/shortcuts/)  
Go to `Help` >> `Shortcuts` to see how to enable them and see what keyboard shortcuts are available.  
8.	Standard Mode personalization  
 `Config` >> [Themes](https://artisan-scope.org/docs/themes/) to explore the options.    


**Expert Mode Choices**

1.	`Config` >> [`Sampling`](https://artisan-scope.org/docs/sampling/)  
Leave at 3 for now. After you have done 25-30 roasts and know the program better you can reduce it if your devices support that. Under Curves your Delta Span should be at least twice your sampling rate. 
2.	`Config` >> [`Curves`](https://artisan-scope.org/docs/curves/)   
Check the boxes needed on the RoR tab and set the values on the Filters page. Suggest you start with zero for all smoothing and check the Drop Spikes and Smooth Spikes choices. Set Delta Span at twice your sampling rate (3 by default) so 6.  If you find zero smoothing give you too many spikes, slowing increase the numbers.  Once you have an Artisan profile, you can change the numbers and see the results on screen.  Also in the`Config` >> `Curves` dialog, last tab, UI, you can pick a font and background image, IF you wish to personalize your screen.  
3.	`Config` >> [`Statistics`](https://artisan-scope.org/docs/statistics/)  
Check all the boxes on the top row.
4.	`Roast` >> [`Background`](https://artisan-scope.org/docs/background/)  
See the documentation on how to load a profile into the background to follow during roasting.
5.  Expert Mode Events Buttons and Alarms  
In Expert Mode, you can have the Default Buttons run an Alarm and you have access to custom Buttons and Annotations under `Config` >> [`Events`](https://artisan-scope.org/docs/events/).  For Buttons in Expert Mode choosing the Label of the Button and the Description are important. The Description will show your graph, using the Event Annotations - last tab. Make sure you complete the Event Annotations tab so you can see your gas and air changes on your profile. Design Alarms as you need them. I love talking Alarms to remind me of temps and return my air to the starting point. I also use Alarms to mark my initial settings.  There are a few additional Alarm settings in Expert mode in the bottom row including Load From Profile and Load from Background.  
7.	 Tools Menu 
In Expert Mode you will also have Analyzer,Simulator, Wheel Graph, Transposer and Calculator.  After you have completed some roasting, please watch the video [Getting the Most from Artisan's Tools](https://www.youtube.com/watch?v=8ivsccu9e_Y&t=3094s){:target="_blank"} to learn more about how to improve your roasting.  
8. Expert Mode Personalization includes Colors `Config` >> [Colors](https://artisan-scope.org/docs/colors/).  For some graph configuations, they are accessed with the last icon in the set on the left on the Roast graph (the one with jagged up arrow). 


The main controls look like this:
![View Controls](/assets/images/gsg/view menu controls.png)

Artisan’s standard event buttons are as follows:
![Artisan buttons](/assets/images/gsg/standard buttons.png)

In the upper right of your screen, `ON` starts reading the Devices.  `START` will begin a roast profile recording  the time and temps.  After you hit `START`, wait at least 15 seconds, before you drop your beans into the roaster and hit `CHARGE` (or use `Auto CHARGE`) to get a ∆BT graph.  Without a CHARGE event there is no ∆BT graph.  Using the trier, when you determine you are at Dry End, hit the `DRY END` button, and do the same for `FC START`, and `DROP`.  After the roast completes, hit the off button.  Congratulations on your first roast.  At the end of the roast you hit `OFF` to stop the recording. When you hit `RESET`, the current profile and background profile are removed and Artisan is reset to be ready for a new roast.  You don’t have to `RESET` after every roast. 

**NOTE:
*Unplug Your Laptop Before You Roast***

For some people, unless you have a USB isolator, you need to unplug your computer when using Artisan or you may get feedback loops that may create unwanted spikes in the graph.  If you are using a desktop, you may need an isolator if you are seeing the spikes.  

Before or after your first roast, look at the [Setup ](https://artisan-scope.org/docs/setup/) page to see how to adjust your bean temp readings and your sampling rates.

You can save your graphs under `File` >> `Save Graph` to various size formats or PDF.  You can also convert your data to other formats and export it under the `File` >> `Convert` and `File` >> `Export` commands.  You can import another roaster's file under `File` >> `Import`.  

To review your own files you can use `File` >> `Open` and search for a file or use the list under `File` >> `Open Recent`.  When starting a roast you can choose `File` >> `New` and pick one of the previous Roast Profiles you may have saved.  

## READY FOR YOUR FIRST ROAST
