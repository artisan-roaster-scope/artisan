---
title: "Quick-Start Guide"
permalink: /docs/quick-start-guide/
excerpt: "How to quickly install and setup Artisan"
last_modified_at: 2019-06-25T15:59:00-04:00
toc: false
---

## Quick-Start Guide

**If you read through the topics on the left you will have a very good idea of how Artisan works.  This Quick-Start-Guide is not intended to answer all technical questions.**  Artisan Quick-Start Guide is maintained by *Michael Herbert of  CarefreeBuzzBuzz.*  If you have suggestions for improving the content of the Quick-Start-Guide or technical questions, please use the community mailing list on the [Artisan Community](https://artisan-scope.org/docs/community/) page.  When clicking links in this Quick-Start-Guide, we suggest you open links in a new window.  You can also find a great deal of information at the [Artisan Blog](https://artisan-roasterscope.blogspot.com/).


Version 2.0 is a major milestone in the development of the artisan roast logger. It comes not only in a new look and with a new application icon, but also with support for the new Artisan.Plus inventory service described below.

A note on upgrading from v1.x:
Artisan 2 stores the application settings in a new location. On the initial start up of Artisan 2 the old settings are imported. From that moment on, changes to settings done with Artisan 2 will not be synchronized automatically back to previous versions. However, synchronizing settings via save/load settings (under menu Help) manually works across all versions. PLEASE EXPORT a working SETTINGS FILE and keep it saved to be able to track back in case changes do not work out as expected when upgrading.


## Artisan.Plus

Introduced as part of 2.0, this is an inventory management system which is not covered in the Quick Start Guide.  More information can be found at the Artisan Plus [website](https://artisan.plus/en/). Artisan v2 connects to the inventory management service. This service manages your stock of beans and automatically subtracts batches as you roast them. Beans can be specified to every detail and only essential meta data of roasts is stored online in the cloud. All roast profiles stay local just with you and are not shared with the platform.

Additional popup menus in the Roast Properties dialog (menu Roast >> Properties) allow you to choose from your stock and have beans information filled in automatically.

The service features support for
•	multiple users, machines and stores
•	blends & certifications
•	charts, tax reports & predictions
•	artisan integration support offline roasting



### Your first roast

**After you review the pages on the left and have done your setup,** with Artisan open, to do your first roast, go to Menu>View and make sure Controls and Readings are checked.  Then make sure your roaster is on and heating, and that the LCDs for temperatures are getting a reading.  

*Buttons and Sliders*

The main controls look like this:
![View Controls](/assets/images/gsg/view menu controls.png)

Artisan’s standard event buttons are as follows:
![Artisan buttons](/assets/images/gsg/standard buttons.png)

The buttons above with start and stop your roasts and indicate key time points in your roast that will be logged.  After using the roaster's trier, you push the button when the event occurs.  Pushing these buttons during a roast will add data to your roast log.  You can find the data under Roast>Properties>Data tab. Sliders can be used to create custom Events as well, but not the standard events.   

When you are ready to charge the roaster, push the On Button. Then push the Start button, and give it **about 15 seconds before you charge the roaster, and push the Charge button at the bottom of Artisan.**  Using the trier, when you determine you are at Dry End, hit the Dry End Button, and do the same for First Crack Start, and Drop.  After the roast completes, hit the off button.  Congratulations on your first roast.  

**NOTE:
*Unplug Your Laptop Before You Roast***

For most people, unless you have a USB isolator you need to unplug your computer when using Artisan or will get feedback loops that will create all sorts of crazy spikes in the graph.  If you are using a desktop I guess you need to get an isolator.

Before or after your first roast, look at the [Setup ](https://artisan-scope.org/docs/setup/) page to see how to adjust your bean temp readings and your sampling rates.

You can save your graphs under File>Save Graph to various size formats or PDF.  You can aslo convert your data to other formats and export it under the File>Convert and File>Export commands.  You can import another roaster's file under File>Import.  

To review your own files you can use File>Open and search for a file or use the list under File>Open Recent.  When starting a roast you can choose File>New and pick one of the previous Roast Profiles you may have saved.  
