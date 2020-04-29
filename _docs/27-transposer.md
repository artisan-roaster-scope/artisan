---
title: "Profile Transposer"
permalink: /docs/transposer/
excerpt: ""
last_modified_at: 2020-04-29T15:59:00-04:00
toc: false
---

### Profile Transposer

*Menu>Tools>Transposer*


Comparing profiles recorded on different machines is a challenge as the heat and air dynamics differ on roasting machines.  There are some points in a roast that can be identified based on physical changes, like the yellow point (DRY) and the start of first-crack (FCs) that can be compared and used to construct a mapping from profiles recorded on one machine to those on another machine. The profile transposer is a tool that supports the construction and application of such mappings along the temperature axis, but also along the time axis e.g. extend or compress a profile.

Menu> Tools > Transposer allows you to transpose the current loaded profile (source) along the x-axis (time) and y-axis (temperature) to create a new bean temperature profile and apply it if you wish.  In both cases, the mapping between the source and the resulting target profile is constructed from a set of value pairs. Each such pair holds a source value taken from the currently loaded profile and its intended target value as entered in the profile transposer dialog. Value pairs are taken from the key points in the roast, which are CHARGE, DRY END (yellow point), FC START (first-crack start), SC START (second-crack start) and DROP.

**Profile Transposer Dialog**

The profile transposer dialog is split into 3 main sections, each holding a table with source values taken from the loaded profile and fields to enter the corresponding target values.
Phases: specification of time mappings by phases target time or percentage values
Time: specification of time mappings by target event times
BT: specification of bean temperature mappings by target bean temperatures
Phases or Time, but not both, can be used to specify target times for the construction of the time mapping, and the BT section allows to specify target temperatures for the construction of the temperature mapping.

**Using the dialog:**

A click on a target row header on any of the tables clears all its target values. A click on a column header in a table either clears the corresponding target value or, if a background profile is loaded, fills the target field with the corresponding value from the background profile.

**The buttons:**
"Apply" modifies the current profile with the mapping without having to close the dialog.  Note that the Batch name and number of your loaded roast will no longer appear.  
"Reset" reverts the profile to the original one. 
"Cancel" reverts also to the original profile closes the dialog box.
“OK" creates a new profile by applying the mapping to the loaded profile and closed the dialog box.

**Original Roast** – Below you see an original roast.  Note that you may wish to turn off events (Config>Events>Markers – deselect your option).    Transposer will not tell you how to change your gas air, but it will tell you a proposed new charge temperature if you change any of the BT temps.  

![Transposer Original](/assets/images/gsg/Transposer original.jpg)

**Background Roasts** – After you have used Transposer, you can go to Roast>Switch Profiles, select Save the profile, and it will load into as a background roast.  Remember to turn Events back on before you start roasting.  

**Changing the Phases**  - let’s say you want to change the times or percentages of your phases, enter the new ones in the target boxes.  You will get new targets to hit, but Transposer will not tell you how to get there with air and gas changes.  This is important to note, and you probably want to screenshot and print the dialog box results so you can plan how you will the new time targets.  

![Transposer Changed Phases](/assets/images/gsg/Transposer changed phases.jpg)

![Transposer Changed Phases Result](/assets/images/gsg/Transposer changed phases result.jpg)


**Change the Drop Time and/or Drop Temp** – in this example both the drop time and drop temp are lowered.  The dialog box will give you both new time and temperature targets (since you changed the drop temp), and notably a new proposed charge temp.  Again you will have to plan how to get to the targets.  When you change the Drop Time, you will see changes in the phase percentages as well.  In case you want to avoid the first two phases and the DRY END and FC START point changing, you can specify additional targets to fix those time points to their current times.

![Transposer longer time lower temp](/assets/images/gsg/Transposer longer time lower temp dialog.jpg)

![Transposer longer time lower temp result](/assets/images/gsg/Transposer longer time lower temp result .jpg)

and this image compares the Transposed profile with the original in the background

![Transposer original background](/assets/images/gsg/Transposer original background.jpg)

**Sample Roasting to Production Roaster – creating a symbolic offset value.**  
If your sample roasters hits FCs at a lower temp than your production roaster you would enter a value in the FCs for BT and at the bottom of the dialog it will suggest a symbolic offset you can use your sample roaster to produce similar temps on your production roaster.  

For additional technical explanations see the Artistan Blog post on Profile Transformer – coming.  






