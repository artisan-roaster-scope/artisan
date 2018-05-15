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

![Artisan 1.3](/assets/images/gsg/artisan 1-3.png)

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
![Phidget Connections](/assets/images/gsg/phidget wiring.jpg)
As thermocouples differ your wiring colors may vary.
My correct wiring colors were as follows:

1. BT G – white
2. BT 0 – Red
3. ET G – white with blue stripe
4. ET 0 – white with red stripe
![Phidget Wirring](/assets/images/gsg/ET0 white with red stripe.jpg)

Click for [detailed Phidget information in Artisan](https://artisan-roasterscope.blogspot.de/2017/12/more-phidgets.html)



**for editing and dividing into pages**

Devices in Artisan

In 1.3, set up is automated for many roasters.  All you have to do is go to Config>Machine and choose your roaster.  If your roaster is not listed, assuming you have installed the Phidget driver and Artisan correctly, all you have to do is go to
![config device](/assets/images/gsg/config device menu.png) and indicate the proper device.  Some of the set ups can get quite complicated and more information is found in the [Artisan Installation Instructions](https://github.com/artisan-roaster-scope/artisan/blob/master/wiki/Installation.md)


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



# **The View Menu**

Under the new View menu, you determine what you see in the program at any given time including basic Controls, Readings (BT, ET, etc LCD’s on the right), Buttons and Sliders.  Toggle these on and off at the start to see what changes.

  ![View menu](/assets/images/gsg/view menu.png)




*Controls*
This toggles on the top line of controls on the right:
![View Controls](/assets/images/gsg/view menu controls.png)

*Readings*
 This turns on the small LCD panels on the right side that read the ET, BT and Delta ET and BT (rate of rise).  These are key readings you will use during the roast.

 ![view readings](/assets/images/gsg/view-readings.png)

*Buttons and Sliders*

Artisan’s standard buttons are as follows:
![Artisan buttons](/assets/images/gsg/standard buttons.png)



The buttons above contain key time points in your roast and after using the trier in the roaster, you would hit the button when the event occurs.  Pushing these buttons during a roast will add data to your roast log.  You can find the data under Roast>Properties>Data tab.

Sliders can be used to create Events as well.   The sliders appear on the left side and can be used to input a variable value between 0 and 999.  There is an image in the next section.  Make sure you check Decimal Places under Curves>UI if you use them.  Your events will be rendered on your graphs with the first letter of the name of the event and two decimal places.  So Gas at a value of 35 would be G35.  Or if you don’t check decimal places G3.  See the section below on Events.

# Curves

![cofig curves](/assets/images/gsg/config curves menu.png)

These are critical settings within Artisan and for most the first two tabs will be where your focus lies.  

First you decide which ROR curves and LCD’s you want to display, and the projection of them will be linear or Newton.  You will just have to play with those options and decide which you prefer.
![curves ror](/assets/images/gsg/curves ror.png)
Secondly you decide on the filters tab how you want the curves to display.  If you want the curves to be the same during and after the roast your settings will be different than if you want additional post roast filtering/smoothing.  
![curves filters](/assets/images/gsg/curves-filters.png)


*Filtering Raw Data*

Checking Drop Spikes will drop huge spikes that are within your set limits. This filter removes all readings that would result in a delta value that is either very high or very low compared to the previous deltas. This filter is able to catch spikes that happen in the standard range temperature values and can therefore not be caught by the min-max filter.

Checking Limits will allow you to set temp limits on how high or low your curve can go.  This will keep your curves within reasonable ranges.  The setting limits the readings accepted by Artisan to the specified range. Selecting the standard range of expected temperatures during a roast often already eliminates most of the spikes, because meters experiencing electric noise often return very high or very low readings.


IMPORTANT NOTE:  These two filters above are applied directly on the incoming data source before the data is recorded under Roast>Properties>Data tab. Therefore data eliminated by the min-max limit and the drop spikes filter is lost forever. This is in contrast to the other filters that in the remaining sections that work on the internal raw data and their effect is used to improve the visualization.

*Filtering During the Roast – All Curves*

Smooth Curves will impact the BT, ET and Delta curves.  This is the one you should adjust to your liking.  You have to balance between being able to read the data that is not too noisy and making meaningful adjustments to your roasting.  The only right answer is not what someone else sets, but how you use this to improve your own roasts and taste in the cup. Smooth Curves and Smooth Deltas also work on previously saved roasts.  If you have Optimal Smoothing checked you will have that algorithm apply over the Smooth Curves one.

Checking Smooth Spikes will activate a further low-pass filter that eliminates tiny spikes that occur on some systems randomly due to some electronic noise. This filter is only applied offline if optimal smoothing is active.

*Filtering During the Roast – ROR*

Smooth Deltas will impact only the delta curves and is applied after the Smooth Curves setting ONLY FOR THE DELTA CURVES during the roast.  This allows for further refinement of your Delta curve.  

Delta Span affects how far back in time Artisan looks when calculating a delta curve.
Increasing this setting should smooth live-recording delta curves.
Increasing this setting will not affect the standard temperature curves (ET/BT/etc.), only deltas.


The 3rd smoothing algorithm "Smooth2" has been removed.

*Filtering After the Roast*

Checking Optimal Smoothing turns on an different smoothing algorithm that does not produce and time shift (optimal in that respect) and can be applied only post roast.  It needs a complete roast as it looks at data forward as well as backward and forward data is not there during a roast.  If Optimal Smoothing is not checked, then online (during recording) and offline curve and RoR representation should be equal.


IMPORTANT NOTE:  Except for the raw data filters, the filter settings can be changed after recording or even after restart of the app and reload of the file (which stores the raw internal data only) to generate variations of the BT,ET and Delta curve rendering. If you send an Artisan file (.alog) to another user she might get a different rendering on her screen depending on her filter settings.  



Make sure under the Curves dialog box, you do two things on the UI tab.  Check the box for Decimal Places and investigate the fonts.  
![fonts example](/assets/images/gsg/font example - chemistry set.png)

# Axes

 These settings control the dimensions of your graphs and are important to understand.  There are now two primary Axes check marks, Auto and Lock. If Auto is checked, Artisan computes from CHARGE and DROP sensible axis limits to have the full profile shown on your screen.  If Lock is checked, the min/max limits will come from the profile that has been loaded.  If Lock is also not checked, what you might call Normal mode, a user can set the limit to his likes and those limits are preserved over anything in a profile that is saved or loaded. Lock is helpful if you plan to print out some profiles which should be scaled the same to make them easier to compare.  If you want to expand the x axis max during a roast by 3min check the Expand flag.  The RESET Min limit is new. This allows those that START quite early before CHARGE (like several minutes) to have Artisan set the x axis min limit on CHARGE (and also RESET) to the specified time. The RESET Max limit existed before and is set on each RESET.  If you hover your mouse over some of these, a tool tip pop up will appear.

![cofig axes](/assets/images/gsg/axes dialog.png)


In this dialog you can change the style and appearance of your grid.  More importantly, focus on the lower part of this dialog and define the temp and delta ranges of your grid along with the steps to be shown.  Note that in order to show your Events at the bottom of the graph you may need to set your Temp Min to 75 or below.  

# Events

Creating Events allows you to record data with either Buttons or Sliders.  You can define up to four custom Events such as Gas and Airflow. Red buttons are Gas readings on propane and the Blue are Fan settings.
![buttons example](/assets/images/gsg/buttons example.png)


And here is what a slider looks like. NOTE if you have sliders on the initial value will be recorded into Artisan:
![sliders example](/assets/images/gsg/sliders config example.png)


In order to set these up you need to create Events, under Config>Events:
![config events](/assets/images/gsg/events config dialog.png)

You can label up to 4 event types. You can edit how they work with the tabs Buttons and Sliders.  When you click a button or Artisan records an event on a scale of 0-999.  You can display these at the bottom of your roasting graph.  You need to set your temperature axis to a low of 0° in order to see these the best.  Config>Axes.  

In 1.3, you have the option to render event descriptions instead of values.  In addition, 1.3 adds a new custom event button type "--" that adds an event (compared to the pure action button of type " ") and can be used to add labels to the graph rendering its button description.  For those using sliders the rendering will continue to be the first letter of the Event name and two digits of the value IF you check Decimal Places under Config>Curves>UI.  If you don’t it will render only one digit.  

*Rendering Events on Your Curves*
Under Config>Events on the right side of the dialog box you will see under Events you now have a drop down with these options:
![combo setting](/assets/images/gsg/combo example.png)

Flag will you an event either on your ET line or your BT line (check the box “show on BT”) and your event description if you check the box for Descr.  (number represents how many letters) or it will show the first letter of your event name and the event value if you do not.  
Bar will show you a multicolored bar at the bottom of your graph with the first letter of your event name and the event value.  Description is not relevant.  
Step will show you a plot (step) graph with no values.  
Step + shows you a plot graph plus your descriptors on the BT line (same choices as under Flag)
Combo shows you a plot graph with the descriptors on the plot (step) graph.   
Here are examples:

*Combo*
![combo example](/assets/images/gsg/combo rendering example.png)


*Step +*
![step+ example](/assets/images/gsg/step+rendering example.png)

You are also now able to add an event type that will show on the graph when you hit the event button.  With this new button type, you can define a button that will add an event item labeled with the description that shows up on the graph at the moment in time you press the button.  You could record when you take a sample from the trier as an example.  


*Buttons Configuration Sample*
![buttons config](/assets/images/gsg/buttons config example.png)

The above screenshot shows the Button Label and Description, Type, Value, Action, Documentation, Visibility, Color and Text Color.  The Label is what shows on the button.  The Description is used to show on the graph.  The Value is from 0-100.  So you have to adjust your scale to that.  For example if you are using 2.0-3.5kPa for gas you might have values 20-35.  You can choose the button to trigger an machine control action such as change the Hottop heater.  You can have the buttons visible or not and choose their color and text.  NOTE in particular the Automation check marks at the bottom, I don’t have AutoCharge checked but if you do, you need to press Start and let it be on for 5x your sampling rate in order to have AutoCharge work.  

*Sliders Configuration Sample*

![sliders sample](/assets/images/gsg/slider example.png)

Quantifiers turn readings received from a connected device into custom events on their 0-100% scale. For example, if you have a channel configured to read burner output on a scale from 0-2000 you can decide to hide the corresponding curve (as it won't fit into the range of the standard temperature axis) or turn just the changes of its readings into events by defining a corresponding quantifier. You end up with a more readable and useful profile.

[Read more about quantifiers for advanced details](https://artisan-roasterscope.blogspot.com/2014/04/event-quantifiers.html)

[For more information on the configurations of sliders, you can find information from Frans Goddijn’s excellent blog](http://kostverlorenvaart.blogspot.nl/2018/03/sliders-and-offsets-in-artisan.html)

[A good video on the topic of Buttons and Alarms from an earlier version of Artisan by Michael Wright](https://www.youtube.com/watch?time_continue=321&v=IrvC9dPqgjE)

You can create [multiple palettes of buttons](https://artisan-roasterscope.blogspot.com/2013/02/events-buttons-and-palettes.html) as well.

# Alarms

Alarms can warn you of certain events and they can also trigger certain things to happen.  For some roasters with advanced controls they can even control the roaster.  

Two Artisan blog posts explain how to work them:

[Basics](https://artisan-roasterscope.blogspot.com/2013/03/alarms.html)

[Creation of alarms dependent upon other alarms](https://artisan-roasterscope.blogspot.com/2016/08/more-alarms.html)

[Talking alarms](https://artisan-roasterscope.blogspot.com/2017/12/talking-alarms.html)

Here is a simple alarm that ROR is at 30 after the charge so that I focus on heat and not let it stray up too much past the 32-39 range in the first few minutes.  This should trigger a pop up to be alert.  New in 1.3, is you can have the pop-up disappear after a X seconds.

![alarm sample](/assets/images/gsg/alarm config example.png)


Alarms are unordered by definition. All alarm conditions of not-yet activated alarms are evaluated once per sampling interval and where all pre-conditions are fulfilled the alarm is fired. Note that each alarm is only fired once.  An alarm is triggered only once even if it has both an alarm time and temperature set.  

You can program alarms to push an Event button, such as mark - Air Min at Charge.  In this case my Event Button 11 is Air Min.
![alarm event](/assets/images/gsg/alarm event example.png)

Note that some Dialog boxes throughout Artisan (cut off in the one above) have a Help button.  

Here is the one for Alarms:
![alarm help dialog](/assets/images/gsg/alarm help dialog.png)


Michael Wright, in the video linked above, uses Alarms for a much more sophisticated purpose in controlling his machine.  His alarm dialog is below for reference.

![alarms advanced](/assets/images/gsg/alarm pallette advanced.png)


Linked is another [video](https://www.youtube.com/watch?v=hYX6c1_rxFI) on alarms to cause an action



# Configuration>Phases and Statistics

These settings provide critical feedback on your roast so I encourage you to read the Artisan blog on these:

https://artisan-roasterscope.blogspot.com/2017/02/roast-phases-statistics-and-phases-lcds.html


# Phases



In the Phases Dialog you can set the temperature limits of each phase. These temperature limits will define the Phases in Statistics which you will review after a roast if you don’t select Auto Adjusted.  

![phases dialog](/assets/images/gsg/phases dialog.png)

Roast phases can either be used in manual mode, where their temperature limits are defined in the corresponding dialog, or in Auto Adjusted mode, where those limits are taken from the corresponding DRY and FCs events as keyed during a roast. In manual mode some people activate AutoDRY and AutoFCs to let Artisan generate the corresponding events once the BT reaches the limits of the corresponding phases defined in the dialog are reached.  So it’s really semi-automatic that way.   You can define two sets of phases limits (called Filter and Espresso) to switch between them.  You can choose to have Artisan automatically mark phases with a watermark on the graph with time and temp.  Checking the Watermarks and Phases LCD is essential.

The Phases LCD are three small LCD panels at the top that displays information relative to the current progress of the roast and operates in one of three modes: time / percentage / temperature.  A right click changes the mode between these three.    In time mode for example after Tipping Point, you will see an estimate of when Dry End will happen and the first LCD will show the time since TP, and based on the current ROR, when Dry will happen.  These change as the roast progresses.  After TP and Dry are complete small numbers between the LCDs show the time between the two.  It’s really important to understand these so review the blog post for pictures and explanation. The most important is that you will have some idea of when FC is coming based on prior events and ROR and you can anticipate the need for air or gas changes.  

In percentage mode you can see the % time in each phase.  This is good to see the development time ratio after you have passed first crack.  So right click.

In temperature mode, you see the bean temperature distance relative to the previous phase, so if you want to drop 10 degrees after first crack you can see that.  

1.3 adds expected time to DRY and FCs to phases LCDs in percentage and temperature mode.


# Statistics


These selections allow you to see the three phases in the classic Artisan colors (green, yellow, brown) at the end of the roast, with the items you check above, time, bar, average ROR, AUC, evaluation (descriptive words).  These Phases depend on your settings in Configuration>Phases.  The Characteristics, at the bottom of your graph post roast, show basic information on the roast, like date, time, beans, batch-size, roast-loss, on the x-axis label if you have entered some of this information in Roast>Properties.  You have to enter Charge and Drop in order to get statistics which can be either manually via an event button or automatically.  Summary shows roast information on the right, post roast.  New is 1.3, is the time after First Crack.

*Statistics – Area Under Curve*

AUC is not a curve to be recorded, but a derived parameter computing the area below the bean temperature curve and above the "base temperature" (specified in the dialog) from the start event (specified in the dialog) and the current moment in time. You can decide to measure AUC from a "base temperature" or from a selected "start event" such as Dry End via a check mark. You can additionally specify a target AUC value you are going for, or take the AUC of the background profile as target. Based on the target you can let Artisan compute a "Guide" (via check mark), a thin line at the moment in time the target AUC value might be reached. You can have the current AUC show in an LCD during the roast.  You may be able to right click the LCD to change it to countdown mode rather than the current AUC.  

AUC is “the idea that the area under the temperature curve could be an indicator on how much total energy the beans might have receive during the roasting process… While the rate-of-rise (RoR) of a temperature curve, calculated as the first (discrete) derivation, gives the current "speed" of the temperature increase and allows to predict the future, the area-under-the-curve (AUC) describes the past.

Initial users have suggested that using Dry End as a reference point is good because this allows comparison of AUC across different setups to account for the variations of temperatures (and probe placements). The yellow point can easily be observed independent of equipment and the amount of energy "blown" into the beans before DRY might not be too important for the end result.

You can now see your Area Under Curve.  AUC will be recomputed for ranking reports based on actual AUC settings under Config>Statistics.  This will make AUC very useful in ranking reports.  Generally AUC is useful tool to compare roasts of the same bean.  More details cand be found [here](https://artisan-roasterscope.blogspot.com/2016/11/area-under-curve-auc.html), and on [Frans Goddijn’s excellent blog](http://kostverlorenvaart.blogspot.com/2016/11/the-area-under-curve.html
https://www.home-barista.com/home-roasting/charting-auc-in-artisan-t46404.html).

Sample post roast graph showing Characteristics:
![post roast Characteristics](/assets/images/gsg/post roast charateristics.png)


# Colors
New color themes and color management options are available in 1.3.  Themes are new.  They contain a color set that affects how the display appears.  Artisan comes with several built-in themes that are both attractive and useful as example starting point for user defined themes.  The built-in themes are available at Config>Themes>Artisan.  A user can save a theme by clicking Help>Save Theme. User saved themes can be loaded from Config>Themes>User.  Themes affect only the display on the screen.  They do not affect any of the other Artisan settings.  Note that themes are a subset of the Artisan settings saved and loaded from the Help menu.

Almost every color used in Artisan can now be configured.  All these colors are saved in themes.  If your foreground and background colors are too similar you will get a message to check them out.  

Also new are enhanced dialogs that display the chosen colors within the dialog.
![colors dialog](/assets/images/gsg/colors dialog.png)


# Autosave
Pick and prefix and directory and choose to include a PDF or not.  You might want to consider a directory structure based upon coffee origin, roasting date or something else.

![autosave](/assets/images/gsg/autosave configuration.png)


# Batch
Count batches so you can use that to determine maintenance needs, or other purposes.  

![batch dialog](/assets/images/gsg/batch dialog.png)


Keyboard Shortcuts
With Artisan you can press the Spacebar to enter and exit into shortcut mode.  Here are the shortcuts:
![keyboard shortcuts](/assets/images/gsg/keyboard shortcuts.png)

# Roasting
Under the Roast you can input many parameters for your current batch and you can choose a Profile to run in the background.
![roasting menus](/assets/images/gsg/roast menu.png)


# Roast Properties
When you enter the coffee bean name here, it shows up on the graph.  To save them hit the + sign to the right of the name.  You can add notes about the beans, and the roaster.  With weight and volume entered, density can be calculated.  You can note moisture as well if you know it.  On the second tab Notes, you can add roasting and cupping notes.  Events and Data are entered by Artisan when the roast is done.  

![roast properties](/assets/images/gsg/roast properties dialog.png)

To reset the Properties you have to select the box “Delete roast properties on RESET” and then reset. You can also have the Properties box open on charge to remind you, mostly to at least, name your coffee.


*Density calculations*

Two blog posts on the density calculations [here](
https://artisan-roasterscope.blogspot.de/2014/11/batch-volume-and-bean-density.html) and [here](http://kostverlorenvaart.blogspot.nl/2014/12/lose-weight-gain-volume-about-coffee.html).

You need a beaker that is smaller than your batch size for this calculator.  You will put in your unit of measurement at the top (say a 400ml beaker), and then you put in your pre and post roast weights to fill that measure of beans on the left. The calculator takes your actual weight in and out from the Roast Properties and places in the right hand boxes.    The calculator will return the density both pre and post roast using the actual pre and post grams.  I think it might be easier to just measure 400grm and check the line on a beaker pre and post roast; however if you don’t do these steps the density won’t show up on the roast report.  Once you know the density of the bean you are using there is shortcut. Assume you know the bean’s density you can enter the known density in the Density field within the roast properties, select the correct density weight (e.g. grams) and volume units (e.g. one liter – but 1 in the box).  Put the cursor in the Volume field after putting in the weight and press the Enter key. Artisan will take the specified density and batch weight of the greens and compute the volume for you.

# Profile Background

In the Profile Background dialog box is where you would load the background profile, determine the opaqueness, and align an event such as charge.  You also can choose if events such as Charge should be shown.  The opaqueness and the colored the same as the current profile, or alternatively, individual colors can be set for each of the background curves.

![background profile](/assets/images/gsg/profile background dialog.png)


Playback Aid lets you get pop ups of events from the background roast and Playback Events actually execute the events. You can choose what you want to see from the prior roast, and you can move the graph up and down or to the side if you are just viewing two roasts later on.  
Playback events are explained [here](https://artisan-roasterscope.blogspot.de/2017/10/profile-templates.html).


# Cupping Profile

After you have cupped your coffee you can create cupping notes and produce a flavor wheel:

![cupping wheel](/assets/images/gsg/cupping notes.png)


# Reports
You can save one graph under File>Save Graph.  Multiple Artisan profiles can be converted into various other formats like CSV, PNG and PDF using File >> Convert To. Select the intended output format from the corresponding submenu, then select the Artisan profiles to be converted, along with the destination directory.   There are Reports for Roasts, Batches and Ranking under Files>Reports.  

For comparing your roasts, a great feature is Report>Ranking>Web
This is the web version and it’s hard to screen shot, but you get Load, Charge Temp, FC start time, FC temp, Drop time, Drop Temp, Dry %, Mai%, Dev%, AUC, and Loss.

Roast Ranking Report
![roast ranking top](/assets/images/gsg/roast ranking report 1.jpg)![roast ranking middle](/assets/images/gsg/roast ranking report2.jpg)![roast ranking last](/assets/images/gsg/roast ranking report 3.jpg)


You can run reports on your Batches – date, profile, beans, in, out, and loss.

Individual Roast Report
You can also run individual roast reports.  These are useful for analyzing an individual roast.  As they are static HTML page.  Hard to screen shot all at once.  

![roast report 1](/assets/images/gsg/roast report 1.jpg)![roast report 2](/assets/images/gsg/roast report 2.jpg)![roast report 3](/assets/images/gsg/roast report3.jpg)![roast report 4](/assets/images/gsg/roast report 4.jpg)



# Additional Readings for your Artisan Graphs

Using Phidgets to Record Airflow in Artisan

This is very useful for those that don’t have good airflow control or have both a fan and damper.  It can be done manually with an Magnehelic Gage and recorded using event buttons as well.  
If you were needing to replace a Phidget 1048 I think the parts list would be:

$32 for the differential air
https://www.phidgets.com/?tier=3&catid=7&=5&prodid=109
$30 for the VINT HUB0000
https://www.phidgets.com/?tier=3&catid= ... prodid=643
$35 for the VINT TMP1101
https://www.phidgets.com/?tier=3&catid= ... prodid=726

The Differential Air Pressure and TMP would plug into the Hub which plugs into the USB port.

See the following for instructions:
https://wbcoffee.blogspot.com/2018/04/installing-phidget-1136-differential.html


# Roaster Setup Specific Information
*Huky*
See:
https://drive.google.com/drive/u/0/folders/0B4HTX5wS3NB2TFVid0h2TGxBWG8  
which references on the Artisan Github page

https://github.com/artisan-roaster-scope/artisan/blob/master/README.md

*Hottop*
Also referenced at the Github page

https://drive.google.com/file/d/0B4HTX5wS3NB2ZGxsTU4tbmtVUmM/edit

*US Roaster Corp*
Feb 2018 Thread on HB for set up-

https://www.home-barista.com/home-roasting/us-roaster-artisan-start-up-t51065.html
