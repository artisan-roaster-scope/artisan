---
title: "Phases"
permalink: /docs/phases/
excerpt: ""
last_modified_at: 2018-05-15T15:59:00-04:00
---

### Phases

In the Phases Dialog you can set the temperature limits of each phase.

![phases dialog](/assets/images/gsg/phases dialog.png)

Roast phases can either be used in manual mode, where their temperature limits are defined in the corresponding dialog, or in Auto Adjusted mode, where those limits are taken from the corresponding DRY and FCs events as keyed during a roast. In manual mode some people activate AutoDRY and AutoFCs to let Artisan generate the corresponding events once the BT reaches the limits of the corresponding phases defined in the dialog are reached.  So it’s really semi-automatic that way.   You can define two sets of phases limits (called Filter and Espresso) to switch between them.  You can choose to have Artisan automatically mark phases with a watermark on the graph with time and temp.  Checking the Watermarks and Phases LCD is essential.

The Phases LCD are three small LCD panels at the top that displays information relative to the current progress of the roast and operates in one of three modes: time / percentage / temperature.  A right click changes the mode between these three.    In time mode for example after Tipping Point, you will see an estimate of when Dry End will happen and the first LCD will show the time since TP, and based on the current ROR, when Dry will happen.  These change as the roast progresses.  After TP and Dry are complete small numbers between the LCDs show the time between the two.  It’s really important to understand these so review the [blog post](/https://artisan-roasterscope.blogspot.com/2016/03/lcds.html) for pictures and explanation. The most important is that you will have some idea of when FC is coming based on prior events and ROR and you can anticipate the need for air or gas changes.  

In percentage mode you can see the % time in each phase.  This is good to see the development time ratio after you have passed first crack.  So right click.

In temperature mode, you see the bean temperature change relative to the previous phase, so if you want to drop 10 degrees after first crack you can see that.  

1.3 adds expected time to DRY and FCs to phases LCDs in percentage and temperature mode.
