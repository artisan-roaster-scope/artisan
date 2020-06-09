---
title: "Axes"
permalink: /docs/axes/
excerpt: ""
last_modified_at: 2018-05-15T15:59:00-04:00
toc: false
---

### Axes

Menu>Config>Axes

![cofig axes](/assets/images/gsg/axes dialog.png)

 These settings control the dimensions of your graphs and are important to understand.  There are now two primary Axes check marks, Auto and Lock. If Auto is checked, Artisan computes from CHARGE and DROP sensible axis limits to have the full profile shown on your screen.  If Lock is checked, the min/max limits will come from the profile that has been loaded.  If Lock is also not checked, what you might call Normal mode, a user can set the limit to his likes and those limits are preserved over anything in a profile that is saved or loaded.

Lock is helpful if you plan to print out some profiles which should be scaled the same to make them easier to compare.  If you want to expand the x axis max during a roast by 3min check the Expand flag.  The RESET Min limit is new. This allows those that START quite early before CHARGE (like several minutes) to have Artisan set the x axis min limit on CHARGE (and also RESET) to the specified time. The RESET Max limit existed before and is set on each RESET.  If you hover your mouse over some of these, a tool tip pop up will appear.

In this dialog you can change the style and appearance of your grid.  More importantly, focus on the lower part of this dialog and define the temp and delta ranges of your grid along with the steps to be shown.  Note that in order to show your Events at the bottom of the graph you may need to set your Temp Min to 75 or below.  

The legend location is where the box with the white background and the legend for your graph line colors will appear.  The ideal location will depend on your other settings.  

The Event Step field is a new setting in Artisan.  It sets the temperature on the Y-axis that corresponds to a step value of 100.  By setting 100% Event Step to a relevant value, you can lower the special event lines below the bottom of the bean temperature (BT) curve.  You will have to experiment to find the best value for your setup.  
