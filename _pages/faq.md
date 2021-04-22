---
layout: single
permalink: /faq/
header:
  overlay_image: /assets/images/teaser-small.jpg
  image: /assets/images/teaser-small.jpg
title: "FAQ"
toc: true
toc_sticky: false

---

## General


**Where do I find support?**  
: Check the [Quick-Start Guide](/docs/quick-start-guide/) and ask the [community](/docs/community/) for help

**How can I support the project?**  
: Send us a [donation](/donate/), help with the translations ([contact](https://artisan-roasterscope.blogspot.com/p/contact-me.html){:target="_blank"}), if you are a developer, send us [Pull Requests on GitHub](https://github.com/artisan-roaster-scope/artisan/pulls){:target="_blank"}

**How to report bugs?**  
: Please report software bugs on the [Artisan issue tracker](https://github.com/artisan-roaster-scope/artisan/issues){:target="_blank"}

**How to get our machines supported?**  
: [Contact the Artisan team](https://artisan-roasterscope.blogspot.com/p/contact-me.html){:target="_blank"} and find out how to become a supporter

<br>


## Setup


**What is the minimum system required to run the app?**  
: Artisan supports 64bit macOS, Windows and Linux. For the minimum system versions see under [Platforms](/about/)

**Do I loose my settings on upgrading?**  
: No, the Artisan settings are stored separately from the app on you computer

**My LCDs show just `uu` or `-1`**
: This happens if your devices are not configured correctly.  Artisan is not getting valid readings.  Possible solutions include seeing if you have a reading on the device itself.  Make sure you have the right drivers are installed.  Make sure there is no software running blocking the single device access such as the Phidgets Control Panel in Phidget setups.  Double check your device set up. 

**How many devices does Artisan support?**  
: Any number. Every device is supposed to provide two data channels. The BT and ET channels are delivered by the main device. You can configure an unlimited number of extra devices, each providing two additional channels. For each extra device you have to choose the device type. Some device types, like MODBUS, S7 or Phidgets require additional configuration in separate tabs. Note that an Artisan device does not have to be connected to a physical device. [Virtual Devices](https://artisan-roasterscope.blogspot.com/2014/04/virtual-devices-and-symbolic-assignments.html){:target="_blank"} compute their data from the data of other channels using a [symbolic formula](https://artisan-roasterscope.blogspot.com/2019/11/symbolic-formulas-basics-new-variables.html){:target="_blank"}. Each channel can show its reading in an extra LCD and be rendered as an extra curve. Channel names and colors can be choosen freely. If you check the delta box of a channel its curve will be map to the right hand axis scale (the Rate-of-rise axis) instead of the temperature axis.

**Can I swap ET and BT without changing the wires?**  
: Under menu `Config > Curves`, tab `Filter`, check the box `ET<->BT`

**My Artisan does not have an ON button?**  
: You are running a second instance known as [ArtisanViewer mode](https://artisan-roasterscope.blogspot.com/2020/06/working-together-artisan-artisanviewer.html){:target="_blank"}.  This is to enable the roaster to see the last roast.  

**There is a delta between the Artisan readings and those displayed on my machine. How to fix this?**  
: The differences can result from a misconfiguration (wrong device temperature unit set in the MODBUS tab or wrong thermocouple type specified in the Phidget tab). Often it is just caused by the differences in the exact time the readings were taken or in the post processing on the readings (filtering, smoothing, rounding, averaging, ..). The reading displayed on the machine could be taken from a probe in another location than the one forwarding the signal to Artisan. Note that even the two probes fitted in dual-probes often report slightly different values due to differences in the positioning inside the shared shield. You can add a [symbolic formula](https://artisan-roasterscope.blogspot.com/2019/11/symbolic-formulas-basics-new-variables.html){:target="_blank"} to compensate for this effect. Thus often a simple offset will only work on one end of the temperature range. In that case your symbolic formula need to encode a linear or even quadratic mapping.



<br>

## Recording

**Can I change the background profile on the fly during roasting in Artisan?**
: Yes, just select a different one via the `Background` menu item under `Roast`. You can also press the `h` key on your keyboard as a short cut to directly open the corresponding file selector.

**Are there keyboard shortcuts to key in events?**
: There is a keyboard mode which is activated by pressing the `RETURN/ENTER` key. The selected button is highlighted. The selection can be changed using the left and right cursor keys. Pressing the space bar activates the selected button.

**I roast the same coffees at the same batch size regularly. Can I define templates for those roast properties?** 
: Yes. The roast properties can be saved as [Recent Roast Property](https://artisan-roasterscope.blogspot.com/2017/06/recent-roast-properties.html){:target="_blank"} by pressing the + button. Such roast properties can be recalled via the roast properties title popup or by selecting the corresponding item under the menu `File >> New`. Holding the option key while selecting an entry sets the properties without actually starting a new profile recoding.

**How to automatically repeat a roast profile?**
: In case you have setup Artisan to control your machine via sliders, you can [replay the events of a template background profile by time and/or temperature](https://artisan-roasterscope.blogspot.com/2017/10/profile-templates.html){:target="_blank"}. Alternative you can put the [PID Control](https://artisan-roasterscope.blogspot.com/2016/11/pid-control.html){:target="_blank"} in background-follow mode to duplicate a temperature curve of the background template.

**Are batch numbers assigned to my roasts?**  
: Yes, if you instruct Artisan to do so by activating the [batch counter](https://artisan-roasterscope.blogspot.com/2015/07/batch-counter.html){:target="_blank"}.

**How do I name, organize and save my profiles?**  
: Under menu `Roast > Roast Properties`, you can choose a name for your profile in the title field.  You can count your roasts using the [Batch Counter](https://artisan-roasterscope.blogspot.com/2015/07/batch-counter.html){:target="_blank"}, and you can use [Autosave](https://artisan-roasterscope.blogspot.com/2017/10/automatic-save.html){:target="_blank"} to automatically save both the Artisan file and rendered version in a format such as a PDF or jpg.  Many people Autosave to a cloud drive so they can access them anywhere.  The Autosave feature gives you [many options for the data included in the filename](https://artisan-roasterscope.blogspot.com/2020/05/autosave-file-naming.html){:target="_blank"}. 

**I can not see the rate-of-rise curve during roasting?**  
: In the upper right of your screen, ON starts reading the Devices. START will begin a roast profile recording the time and temps. After you hit START, wait at least 15 seconds (5 samples x 3sec default rate), you need to drop your beans into the roaster and hit CHARGE (or use Auto CHARGE) to get a ∆BT graph. Using the trier, when you determine you are at Dry End, hit the DRY END button, and do the same for FIRST CRACK START, and DROP. After the roast completes, hit the off button. Congratulations on your first roast. At the end of the roast you hit OFF to stop the recording. When you hit RESET, the current profile and background profile are removed and Artisan is reset to be ready for a new roast. You don’t have to RESET after every roast.

**How can I get the rate-of-rise in F/30sec?** 
: Artisan uses only proper physical units to render data, like C/min or F/min. However, as for any other signal you can apply a [symbolic formula](https://artisan-roasterscope.blogspot.com/2019/11/symbolic-formulas-basics-new-variables.html#30s){:target="_blank"} to the Rate-of-Rise signal which simply divides the readings by 2 to turn F/min into F/30sec, or by 4 to turn it into F/15sec.

**My RoR is all over the place. How do I make it readable?**  
: Carefully read about your [choices for smoothing the curve on the Quick Start Guide](/docs/curves/) and on the [Artisan blog](https://artisan-roasterscope.blogspot.com/2014/01/sampling-interval-smoothing-and-rate-of.html){:target="_blank"}.  You may have device noise or machine noise in your roaster so you may wish to read about [Digital Noise](https://artisan-roasterscope.blogspot.com/2017/06/digital-noise.html){:target="_blank"} and [On Idle Noise](https://artisan-roasterscope.blogspot.com/2019/03/on-idle-noise.html){:target="_blank"}.  If you choose smoothing you will have a small amount of time delay but only you can balance the readability of the data and the delay. 

**How accurate is the first-crack start prediction?**  
: the prediction of roasting events is based on the current roast time, temperature and rate-of-rise and the [target phase temperature](https://artisan-roasterscope.blogspot.com/2017/02/roast-phases-statistics-and-phases-lcds.html){:target="_blank"} and is made under the assumption of a constant rate-of-rise.

**How Do I record my gas and air changes?**  
: Events can be entered via [custom event buttons, event sliders, the generic event button, the mini event editor, a point-and-click action](https://artisan-roasterscope.blogspot.de/2013/02/events-buttons-and-palettes.html){:target="_blank"}, or automatically via [event quantifiers](https://artisan-roasterscope.blogspot.de/2014/04/event-quantifiers.html){:target="_blank"} monitoring the readings reported by a connected device. You create Buttons or Sliders under `Config > Events, and choose a way to display them.  More advanced displays can be created using [Event Annotations](https://artisan-roasterscope.blogspot.com/2020/05/special-events-annotations.html){:target="_blank"}. Event buttons can be ["relative"](https://artisan-roasterscope.blogspot.de/2015/10/increasing-heat.html), [sliders as well as event buttons can trigger actions](https://artisan-roasterscope.blogspot.de/2016/08/fz-94-4-taking-control.html){:target="_blank"} and [events can be replayed automatically](https://artisan-roasterscope.blogspot.com/2017/10/profile-templates.html){:target="_blank"}.

**How do I set the default values for special events when I start my roast?**  
: For event types with visible event slider corresponding event marks at the current slider position are set at CHARGE automatically. For other event types you can instruct any of the default buttons (like ON, CHARGE, ..) under [`Config > Events`](/docs/events/) on the first tab, to trigger custom event buttons by selecting the `Multiple Event` button action and enter the custom event button numbers to be triggered in the following text field, separated by a comma.




<br>

## Viewing

**How to display the RoR instead of the temperature at the cursor position next to the time in the top line coordiinate widget?** 
: Just press the `d` key to toggle between temperature and RoR readings
 show RoR instead of C in under coordinates

**How can I activate cross-lines at the cursor position?**  
: Just press the key t to toggle cross-lines and move the mouse. While cross-lines are active you can [place a start point and drag while holding the mouse button](https://artisan-roasterscope.blogspot.com/2017/12/artisan-v12.html){:target="_blank"} to measure the deltas between the current position and the start point.
 
**What does the unit `C*min` for the AUC denote?** 
: The [area–under–the-curve (AUC)](https://artisan-roasterscope.blogspot.com/2016/11/area-under-curve-auc.html){:target="_blank"} measures the area between a given base temperature (here in C) and the BT curve over a certain period. Thus the unit of AUC is the temperature unit multiplied by the time unit (minutes).

**What are those `CM` readings shown in the time axis label about?**  
: [This is a pair of values indicating how good your profiles ET and BT curves match the ones of the background template.](https://artisan-roasterscope.blogspot.com/2019/05/how-close.html){:target="_blank"} Better matches get lower `CM` values. The measure is named by the initials of the roasting operation, [Casino Mocca](https://casinomocca.com/){:target="_blank"}, that first suggested it.

**Can I change the z-order of curves?** 
: The drawing order of curves is fixed and follows the one of the LCDs. However, the order of the ET/BT LCDs can be swapped in the Device Assignment dialog (menu `Config > Device`) and the order of the RoR LCDs can be swapped in the Curves dialog (menu `Config > Curves`, first tab). Besides this you can hide curves temporarily by a click to their legend entry (activate the legend in the Axis dialog accessible via menu `Config > Axis`) to see what is behind.
