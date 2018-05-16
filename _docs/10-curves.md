---
title: "Curves"
permalink: /docs/curves/
excerpt: ""
last_modified_at: 2018-05-15T15:59:00-04:00
---

### Curves

![cofig curves](/assets/images/gsg/config curves menu.png)

These are critical settings within Artisan and for most the first two tabs will be where your focus lies.  

First you decide which ROR curves and LCD’s you want to display.
![curves ror](/assets/images/gsg/curves ror.png)

Secondly you move to the filters tab to determine how you want the curves to display.  If you want the curves to be the same during and after the roast your settings will be different than if you want additional post roast filtering/smoothing. **These are critical settings so take your time here.  As you adjust the settings, consider if the results allow you to understand and interpret your results so that you can improve taste in the cup.  For some, to much variation in the curves becomes hard to interpret so they turn up the smoothing.**
![curves filters](/assets/images/gsg/curves-filters.png)


*Filtering Raw Data*

Checking Drop Spikes will drop huge spikes that are within your set limits. This filter removes all readings that would result in a delta value that is either very high or very low compared to the previous deltas. This filter is able to catch spikes that happen in the standard range temperature values and can therefore not be caught by the min-max filter.

Checking Limits will allow you to set temp limits on how high or low your curve can go.  This will keep your curves within reasonable ranges.  This setting limits the readings accepted by Artisan to the specified range. Selecting the standard range of expected temperatures during a roast often already eliminates most of the spikes, because meters experiencing electric noise often return very high or very low readings.


IMPORTANT NOTE:  These two filters above are applied directly on the incoming data source before the data is recorded under Roast>Properties>Data tab. Therefore data eliminated by the min-max limit and the drop spikes filter is lost forever. This is in contrast to the other filters that in the remaining sections that work on the internal raw data and their effect is used to improve the visualization.

*Filtering During the Roast – All Curves*

Smooth Curves will impact the BT, ET and Delta curves.  This is the one you should adjust to your liking.  You have to balance between being able to read the data that is not too noisy and making meaningful adjustments to your roasting.  The only right answer is not what someone else sets, but how you use this to improve your own roasts and taste in the cup. Smooth Curves and Smooth Deltas also work on previously saved roasts.  If you have Optimal Smoothing checked you will have that algorithm apply over the Smooth Curves one.

Checking Smooth Spikes will activate a further low-pass filter that eliminates tiny spikes that occur on some systems randomly due to some electronic noise. This filter is only applied offline if optimal smoothing is active.

*Filtering During the Roast – ROR*

Smooth Deltas will impact only the delta curves and is applied after the Smooth Curves setting ONLY FOR THE DELTA CURVES during the roast.  This allows for further refinement of your Delta curve.  

Delta Span affects how far back in time Artisan looks when calculating a delta curve.
Increasing this setting should smooth live-recording delta curves.
Increasing this setting will not affect the standard temperature curves (ET/BT/etc.), only deltas.


*Filtering After the Roast*

Checking Optimal Smoothing turns on an different smoothing algorithm that does not produce and time shift (optimal in that respect) and can be applied only post roast.  It needs a complete roast as it looks at data forward as well as backward and forward data is not there during a roast.  If Optimal Smoothing is not checked, then online (during recording) and offline curve and RoR representation should be equal.


IMPORTANT NOTE:  Except for the raw data filters, the filter settings can be changed after recording or even after restart of the app and reload of the file (which stores the raw internal data only) to generate variations of the BT,ET and Delta curve rendering. If you send an Artisan file (.alog) to another user she might get a different rendering on her screen depending on her filter settings, so you may want to send your settings file as well.  

*UI Tab*

Make sure under the Curves dialog box, you do two things on the UI tab.  Check the box for Decimal Places and investigate the fonts.  Here is an example of the Comic font.
![fonts example](/assets/images/gsg/font example - chemistry set.png)
