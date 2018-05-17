---
title: "Phases"
permalink: /docs/phases/
excerpt: ""
last_modified_at: 2018-05-15T15:59:00-04:00
toc: false
---

### Phases

Menu>Config>Phases

Often roasters identify distinct roast phases.

- Drying: from heating the beans to the point where the beans turn yellow (DRY)
- Maillard: from DRY to the start of first crack (FCs)
- Finishing: from FCs to the end of the roast (DROP)

Artisan marks the drying phase in green, the Maillard phase in yellow and the finishing phase in brown. You can define two sets of phases limits (called Filter and Espresso) to switch between them.  You can choose to have Artisan automatically mark phases with a watermark on the graph with time and temp.  Checking the Watermarks and Phases LCD is essential.  The Phases are shown at the end of the roast on your graph depending on your choices under [Statistics](https://aritisan-scope.org/docs/statistics/).

In the Phases Dialog you can set the temperature limits of each phase.

![phases dialog](/assets/images/gsg/phases dialog.png)

Roast phases can either be used in manual mode, where their temperature limits are defined in the corresponding dialog, or in Auto Adjusted mode, where those limits are taken from the corresponding DRY and FCs events as keyed during a roast. In manual mode some people activate AutoDRY and AutoFCs to let Artisan generate the corresponding events once the BT reaches the limits of the corresponding phases defined in the dialog are reached.  So it’s really semi-automatic that way.   

The Phases LCD's are essential for your roasting. The Phases LCD are three small LCD panels at the top that displays information relative to the current progress of the roast and operates in one of three modes: time / percentage / temperature. A right click changes the mode between these three. In time mode for example after Tipping Point, you will see an estimate of when Dry End will happen and the first LCD will show the time since TP, and based on the current ROR, when Dry will happen.  These change as the roast progresses.  After TP and Dry are complete small numbers between the LCDs show the time between the two.  The most important is that you will have some idea of when FC is coming based on prior events and ROR and you can anticipate the need for air or gas changes.  

In percentage mode you can see the % time in each phase.  This is good to see the development time ratio after you have passed first crack.  So right click.

In temperature mode, you see the bean temperature change relative to the previous phase, so if you want to drop 10 degrees after first crack you can see that.  

1.3 adds expected time to DRY and FCs to phases LCDs in percentage and temperature mode.

Here are examples of how the three Phases LCDs work if you check the box to make them visible.  Each of the three small LCDs relate to one of the three roasting phases.

Each of the LCDs displays information relative to the current progress of the roast and operates in one of three modes: time / percentage / temperature.

For example, in the following situation, the roast just passed the turning point (TP) and is approaching DRY. The phasesLCDs are in time mode. The TP lcd indicates that 2:45 minutes have passed since TP and that, based on the current RoR, DRY is expected to happen 7:41 minutes into the roast. The last LCD does not have any meaningful information to be displayed yet.

![time past tp](/assets/images/gsg/Time past TP.png)


A little bit further into that roast, after DRY (39 seconds ago as reported by the second LCD and 6:15 minutes after TP) and approaching FCs, the last LCD reports that the FCs is estimated to happen at 11:08 minutes into the roast. Additionally, a small number between the TP and the DRY LCD tells us that DRY happened exactly 5:36 minutes after TP.

![time between tip and dry](/assets/images/gsg/time between tp and dry.png)


Finally, 21 seconds ago we reached FCs at 11:51, 4:21 minutes after DRY.

![time past FC](/assets/images/gsg/time past fc.png)

Many people are focused on a 20%-25% development ratio. Just clicking the phases LCDs with the right mouse button switches from time to percentage mode, and we see that we still have some time as we are only at 3% right now.

![dtr time](/assets/images/gsg/dtr time.png)

Another right-click on the phases LCDs toggles from percentage into temperature mode, indicating the temperature difference relative to the previous roasting event. This might be useful if we want to stop our roast e.g. 10C above FCs.

![bt increase since fcs](/assets/images/gsg/bt increase since fc.png)
