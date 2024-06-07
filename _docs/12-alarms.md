---
title: "Alarms"
permalink: /docs/alarms/
excerpt: ""
last_modified_at: 2019-01-03T15:59:00-04:00
author: Michael Herbert
author_profile: true
---

### Alarms - Purpose

Menu: `Config` >> `Alarms`

Alarms are for intermediate and advanced users.  Beginners should be aware they exist and as you gain experience with Artisan come back here and learn more about how powerful they can be as, you can even control the roaster with Alarms.

Alarms trigger certain actions to happen. Artisan alarms can help you in keeping the focus while roasting. The actions can be PopUPs, spoken words, or even controlling the roaster.  For example, if we would like Artisan to show a popup once the BT (bean temperature) raises beyond 180C, reminding us to turn down the heat on approaching FCs (First Crack Start). Here BT beyond 180C is the trigger and showing a popup is the action.

Alarms are unordered by definition. All alarm conditions of not-yet activated alarms are evaluated once per sampling interval and where all pre-conditions are fulfilled the alarm is fired. Note that each alarm is only fired once.  An alarm is triggered only once even if it has both an alarm time and temperature trigger set.   

Alarm sets allow you to make different sets of alarms for different roasting styles and other purposes.  There is a tab in the Alarm dialog box called Alarm Sets.  


### Alarms from Profiles and Background Roasts

If you want to load Alarms from a profile (.alog file) check Load from Profile, or if you want alarms from a background roast, check the box for Load from Background. Alarms are also saved when you save your settings.

![alarm trigger](/assets/images/gsg/alarms load background.png)

### Create Alarms from a Profile

If you have a previous roast loaded that contains some (custom) events, you open its event table (menu `Roast` >> `Properties`; 3rd tab `Events`) you can turn the list of events listed there into alarms by clicking "Create Alarms".

The "Create Alarms" action takes all SELECTED events listed in the table.  If NO events are  selected it takes all of them and turns each of them into an alarm rule. Make sure you check what is selected on on your screen.  Note that you can use the standard modifier keys on your operating system to achieve multi-selections (e.g. the command/apple key on macOS) and further note that other tables within Artisan behave in a similar way.


### Alarms To Trigger PopUPs

Open the alarm dialog (select menu Config/Alarms) and press Add. Now we have a new line in the alarm table with some columns. Bean Temp (BT) will be the Source, and the Condition will be the Temperature is 180. This defines the trigger of our alarm. As action we want to have Pop Up Window and add "Temp down!" as Description. If we would now start a roast we would get the pop-up already on CHARGE (assuming to charge at around 200C BT). So let's restrict the trigger by setting From to TP (Turning Point). That way, the trigger is active only after the turning point has been detected by Artisan. Now we are set and as long as the alarm status flag is ON this alarm will be triggered once per roast.

![alarm trigger](/assets/images/gsg/Alarm temp down.png)

Here is another simple alarm that ROR is at 30 after the charge so that the roasters focuses on the next adjustment to make.  The alarm triggers a pop-up.  New in 1.3, is you can have the pop-up disappear after a X seconds.

![alarm sample](/assets/images/gsg/alarm config example.png)

### Alarm Actions

You can program alarms to push an Event button and record that Event, such as mark - Air Min at Charge.  In this case my Event Button 11 is Air Min.
![alarm event](/assets/images/gsg/alarm event example.png)

Alarms on some roasters can turn down the heat automatically not just tell the human roaster to do it and record it. Easy if you have a TC4/HRI controlled Hottop. Just define a corresponding slider for the heater (see [Controlling a Hottop](https://artisan-roasterscope.blogspot.se/2013/02/controlling-hottop.html)) and change the alarms Action to Slider Power as well as its Description to 51. Once triggered this alarm will now move the slider to 51. This will trigger the associated slider action, sending out a command to the Hottop to turn down the heater to 51%.

![alarm trigger slider](/assets/images/gsg/Alarm trigger slider.png)

Read the [blog](https://artisan-roasterscope.blogspot.com/2018/05/automating-huky.html) post on automating a Huky to find out how the right hardware and alarms can control the roaster from Artisan.  Remember to never leave your roaster unattended though.  

### Time Triggered Alarms

Let's turn the fan speed to 72% 2min after FC automatically. For this we need a second alarm that moves our Fan slider to 72 based on a temporal criteria. As a From value we select FC START. Further, we set the Time of this on to 02:00 and it's temperature Source to the empty entry, just to be sure that this alarm is not triggered by any temperature change.

![alarm time trigger](/assets/images/gsg/Alarm time trigger.png)

### Alarm Chains

Assume you have a temperature probe in the air stream of the bean cooler.  Setting an alarm triggered as soon as the temperature of my cooling probe drops below 35C after DROP will not work as it will be triggered immediately on DROP. This is because the cooler probe will report room temperature when that event is detected. A case for alarm chains. To do this first define an alarm that triggers once the cooler temperature rises above, say 40C and select the empty alarm action for this (line 3 in the image below). Then create our desired drop-below-35C, by setting its IF Alarm value to the column number of our first alarm (line 4).  The line 3 alarm is guarding line 4 in the sense that 4 is only triggered IF line 3 has occurred. We are building a chain of alarms. An alarm in a chain is only triggered after its guard, eg. the Alarm specified by its If Alarm value, has been triggered before. Finally, we set the alarm Action here to Event Button and the description to 0 (a special case which triggers the COOL button).

![alarm chain](/assets/images/gsg/Alarm chain.png)


### Talking Alarms


If you want your alarms to talk to you, an Artisan blog posts explains [talking alarms](https://artisan-roasterscope.blogspot.com/2017/12/talking-alarms.html).  They are quite easy on a Mac as the software is built in and further explanation is [here](https://artisan-roasterscope.blogspot.com/2015/07/speaking-alarms-for-os-x.html).  Talking alarms have become one of my favorite features for making the roasting process semi-automatic.  The SAY command is not in the Help file action list but now you know what it is.  


### Help Dialog

The Help dialog box for Alarms shows the types of Alarms, the Configuration Options, and the Actions that can be taken.  Review this in detail before planning your alarms.  

Some things to remember

- time triggers set to 0:00 are ignored
- alarms with guards, i.e. the IF Alarm attribute, set to 0 are not guarded by any other alarm
- not all events that you can select to restrict the active period of a roast via the From attribute, like DryEnd, are set automatically by Artisan during a roast. Therefore, the corresponding alarms depending on those events are triggered only after those events are entered manually by pressing the corresponding event button
- an alarm is triggered only once even if it has both, an alarm time and temperature set

### Always On

For those automating their roasting, Artisan can turn back on automatically after terminating a recording. This is especially useful if one uses Alarms to control sessions with a sequence of roasts. So you might have configured an alarm that triggers the OFF action automatically at the end of the first roast, but there is no way to have Artisan turned ON again via Alarms as alarms are not processed while not sampling.  In Artisan v1.4 you can tick the Keep ON flag in the "Sampling Interval" dialog (menu `Config` >> `Sampling Interval`) to have Artisan turn itself on automatically after it received an OFF signal while recording. If there is unsaved data Artisan will still ask you to save that before doing a reset and running the ON action.

### Other Videos and Resources

Michael Wright has a [video](https://www.youtube.com/watch?time_continue=321&v=IrvC9dPqgjE) that uses Alarms for a much more sophisticated purpose in controlling his machine.  His alarm dialog is below for reference.

![alarms advanced](/assets/images/gsg/alarm pallette advanced.png)



Frans Goddijn has a [video](https://www.youtube.com/watch?v=hYX6c1_rxFI)
 on alarms to cause an action.


Rick Groszkiewicz
has a [video](https://www.youtube.com/watch?v=KLnb8lZwHjE) on alarms as well.
