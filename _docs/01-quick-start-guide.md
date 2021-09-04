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

Artisan Quick-Start Guide is maintained by *Michael Herbert of [CarefreeBuzzBuzz](https://www.carefreebuzzbuzz.com/){:target="_blank"}*. If you have suggestions for improving the content of the Quick-Start-Guide or technical questions, please use the [Artisan discussion forum](https://github.com/artisan-roaster-scope/artisan/discussions) (GitHub registration required).  When clicking links in this Quick-Start-Guide, we suggest you open links in a new window.  You can also find a great deal of information at the [Artisan Blog](https://artisan-roasterscope.blogspot.com/).




### artisan.plus

Introduced as part of Artisan v2, [artisan.plus](https://artisan.plus/en/) is an inventory management system which is not covered in the Quick Start Guide. Artisan v2 connects to the inventory management service. This service manages your stock of beans and automatically subtracts batches as you roast them. Beans can be specified to every detail and only essential meta data of roasts is stored online in the cloud. All roast profiles stay local just with you and are not shared with the platform.

Additional popup menus in the Roast Properties dialog (menu `Roast` >> `Properties`) allow you to choose from your stock and have beans information filled in automatically.

The [artisan.plus service](https://artisan.plus/en/) features support for

- multiple users, machines and stores
- blends & certifications
- charts, tax reports & predictions
- artisan integration support offline roasting



### Learn what Artisan can do and Your First Roast 

1.	Skim the pages of this Quick Start Guide, learn what Artisan RoasterScope can do, and then go back and read the pages of interest in detail. For each roast, an Artisan "profile" will be created and can be saved in various formats under File>Save Graph (be sure to review these).  For most of the topics below, you will find a page in this Quick Start Guide, and some are linked.  
2.	`Config` >> `Temperature`  
Pick ˚F or ˚C.
3.	`Config` >> [`Sampling`](https://artisan-scope.org/docs/sampling/)  
Leave at 3 for now. After you have done 25-30 roasts and know the program better you can reduce it if your devices support that. Under Curves your Delta Span should be at least twice your sampling rate.  Leave Oversampling unselected/unchecked.
4.	Run `Config` >> `Machine`, or set up your devices, and make sure the LCDs show your temps.  Some of these configurations will change the sampling rate and that’s ok.  
5.	`Config` >> [`Curves`](https://artisan-scope.org/docs/curves/)   
Check the boxes needed on the RoR tab and set the values on the Filters page. Suggest you start with zero for all smoothing and check the Drop Spikes and Smooth Spikes choices. Set Delta Span at twice your sampling rate (3 by default) so 6.  If you find zero smoothing give you too many spikes, slowing increase the numbers.  Once you have an Artisan profile, you can change the numbers and see the results on screen.  
6.	`Config`>> `Events` and `Config` >> `Alarms`  
these are the more complex steps and are addressed in the steps below.  
7.	`Config` >> [`Axes`](https://artisan-scope.org/docs/axes/)  
Check Auto, and set your range for your Temperature and Delta axes. Starting points could be 0-500 ˚F and 0-40˚F/min, or 0-250˚C and 0-20˚C/min.
8.	`Config` >> [`Batch`](https://artisan-scope.org/docs/batches/)  
Choose a prefix name and turn on the counter. 
9.	`Config` >> [`Autosave`](https://artisan-scope.org/docs/autosave/)  
Check autosave and add to recent. Choose a location and set the path.   If you use cloud storage, you can access your profiles from any device any where.  Choose a file name prefix. Check the Help screen to decide what to include. See the Quick Start Guide for examples.
10.	`Config` >> [`Statistics`](https://artisan-scope.org/docs/statistics/)  
Check all the boxes on the top row.
11.	`Config` >> [`Phases`](https://artisan-scope.org/docs/phases/)  
For Phases LCD mode, choose time for Drying, Temp for Maillard, and check the box Phases LCD All in the Finishing Line. Other choices are yours.
12.	`Roast` >> [`Properties`](https://artisan-scope.org/docs/properties/)  
Fill in the information and start saving the various roast profiles.
13.	`Roast` >> [`Background`](https://artisan-scope.org/docs/background/)  
See the documentation on how to load a profile into the background.
14.	`File` >> `Report` and `File` >> `Save Graph`  
Learn how to export reports on your roasts and graphs to post. You can use “;” to take a screenshot.  
15. `Help` >> `Save Settings`  
Maybe the most important step. Save your settings and make a habit of it before every upgrade and when you change settings.  
16.	`Config` >> [`Events`](https://artisan-scope.org/docs/events/) and `Config` >> [`Alarms`](https://artisan-scope.org/docs/alarms/)  
These are critical, but they also take some work. I put them last so that other important concepts aren't passed over while you work on this. For this step it's really critical that you read the QSG in detail. First thing decide if you will use buttons or sliders to record gas changes. Decide which boxes you want to check, including `Auto DROP` and `Auto CHARGE`. I use `Auto DROP` but not `Auto CHARGE` as that helps me focus on the start of the roast. If you use `Auto CHARGE`, make sure you hit Start at least 15 seconds before you drop your beans.  I mark TP, MET and I show the Time Guide. For Buttons choosing the Label of the Button and the Description are important. The Description will show your graph, using the Event Annotations - last tab. Make sure you complete the Event Annotations tab so you can see your gas and air changes on your profile. Design Alarms as you need them. I love talking Alarms to remind me of temps and return my air to the starting point. I also use Alarms to mark my initial settings.
17.	 Tools Menu  
Once you have roasted a few batches, go back and read the documentation on the items in the Tools menu: Analyzer, Comparator, Designer, Simulator, Wheel Graph, Transposer and Calculator.
18.	[Shortcuts](https://artisan-scope.org/docs/shortcuts/)  
Go to `Help` >> `Shortcuts` to see how to enable them and see what keyboard shortcuts are available.  
19.	More personalization  
Go to `Config` >> [`Colors`](https://artisan-scope.org/docs/colors/) and `Config` >> [`Themes`](https://artisan-scope.org/docs/themes/) to explore the options.  Note that some of the graph configurations are accessed with the last icon in the set on the left on the Roast graph (the one with jagged up arrow).  `Config` >> `Curves`, UI, pick a font and background image, IF you wish to personalize your use
20.	READY FOR YOUR FIRST ROAST

The main controls look like this:
![View Controls](/assets/images/gsg/view menu controls.png)

Artisan’s standard event buttons are as follows:
![Artisan buttons](/assets/images/gsg/standard buttons.png)

In the upper right of your screen, `ON` starts reading the Devices.  `START` will begin a roast profile recording  the time and temps.  After you hit `START`, wait at least 15 seconds, you need to drop your beans into the roaster and hit `CHARGE` (or use `Auto CHARGE`) to get a ∆BT graph.  Using the trier, when you determine you are at Dry End, hit the `DRY END` button, and do the same for `FC START`, and `DROP`.  After the roast completes, hit the off button.  Congratulations on your first roast.  At the end of the roast you hit `OFF` to stop the recording. When you hit `RESET`, the current profile and background profile are removed and Artisan is reset to be ready for a new roast.  You don’t have to `RESET` after every roast. 

**NOTE:
*Unplug Your Laptop Before You Roast***

For some people, unless you have a USB isolator, you need to unplug your computer when using Artisan or you may get feedback loops that may create unwanted spikes in the graph.  If you are using a desktop, you may need an isolator if you are seeing the spikes.  

Before or after your first roast, look at the [Setup ](https://artisan-scope.org/docs/setup/) page to see how to adjust your bean temp readings and your sampling rates.

You can save your graphs under `File` >> `Save Graph` to various size formats or PDF.  You can aslo convert your data to other formats and export it under the `File` >> `Convert` and `File` >> `Export` commands.  You can import another roaster's file under `File` >> `Import`.  

To review your own files you can use `File` >> `Open` and search for a file or use the list under `File` >> `Open Recent`.  When starting a roast you can choose `File` >> `New` and pick one of the previous Roast Profiles you may have saved.  
