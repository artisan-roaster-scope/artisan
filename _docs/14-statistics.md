---
title: "Statistics"
permalink: /docs/statistics/
excerpt: ""
last_modified_at: 2018-05-15T15:59:00-04:00
toc: false
---
### Statistics

Menu>Config>Statistics

![statistic dialog](/assets/images/gsg/statistics dialog.png)

These selections allow you to see the three roast phases in the classic Artisan colors (green, yellow, brown) at the end of the roast, with the items you check: time, bar, average ROR, AUC, evaluation (descriptive words).  Phases example with the time, bar and F/min:

![phases example](/assets/images/gsg/Three Phases.png)

These Phases depend on your settings in Configuration>Phases.  The Characteristics, at the bottom of your graph post roast, show basic information on the roast, like date, time, beans, batch-size, roast-loss, on the x-axis label if you have entered some of this information in Roast>Properties.  You have to enter Charge and Drop in order to get statistics which can be either manually via an event button or automatically.  Summary shows roast information on the right, post roast such as what roast of the day it is, weight loss, and other data.  Time after First Crack is now shown as a Characteristic at the bottom of the chart.

Sample post roast showing Characteristics at the bottom of the graph:
![post roast Characteristics](/assets/images/gsg/post roast charateristics.png)

Post roast, the placement and formatting of the statistic summary has been improved to make things more readable. Lines to render the green bean name and some of the roasting notes have been added to allow you to add some free text to the summary. Finally, barometric pressure has been add to the roast properties as well as to the ambient data line in this summary.  

![post roast statistics](/assets/images/gsg/stats in 14.png)

You can now save the Statistics box to a file so that you can print it for a coffee bag.  The format is PDF on a Mac and .png on Windows.  You can also change the background color and opacity under the Colors settings.  What goes in the box is determined by what you put in Roast Properties dialog as well as batch prefix/number, roast number of the day, ambient data (temp/humidity/pressure),machine name and drum speed.  


*Statistics – Area Under Curve*

AUC is not a curve to be recorded, but a derived parameter computing the area below the bean temperature curve and above the "base temperature" (specified in the dialog) from the start event (specified in the dialog) and the current moment in time. You can decide to measure AUC from a "base temperature" or from a selected "start event" such as Dry End via a check mark. You can additionally specify a target AUC value you are going for, or take the AUC of the background profile as target. Based on the target you can let Artisan compute a "Guide" (via check mark), a thin line at the moment in time the target AUC value might be reached. You can have the current AUC show in an LCD during the roast.  You may be able to right click the LCD to change it to countdown mode rather than the current AUC.  

AUC is “the idea that the area under the temperature curve could be an indicator on how much total energy the beans might have receive during the roasting process. While the rate-of-rise (RoR) of a temperature curve, calculated as the first (discrete) derivation, gives the current "speed" of the temperature increase or decrease and allows to predict the future, the area-under-the-curve (AUC) describes the past.

Initial users have suggested that using Dry End as a reference point is good because this allows comparison of AUC across different setups to account for the variations of temperatures (and probe placements). The yellow point can easily be observed independent of equipment and the amount of energy "blown" into the beans before DRY might not be too important for the end result.

You can now see your Area Under Curve.  AUC will also be recomputed for ranking reports based on actual AUC settings under Config>Statistics.  This will make AUC very useful in ranking reports.  Generally, AUC is a useful tool to compare roasts of the same bean.  More details can be found [here](https://artisan-roasterscope.blogspot.com/2016/11/area-under-curve-auc.html), and on [Frans Goddijn’s excellent blog](http://kostverlorenvaart.blogspot.com/2016/11/the-area-under-curve.html
https://www.home-barista.com/home-roasting/charting-auc-in-artisan-t46404.html).
