---
title: "Events"
permalink: /docs/events/
excerpt: ""
last_modified_at: 2020-04-30T15:59:00-04:00
toc: false
author: Michael Herbert
author_profile: true
---

### Events

Menu: `Config` >> `Events`

Creating Events allows you to record data to be shown on your roast graph with either Buttons or Sliders.  You can have multiple labeled sets of Events and manage them in the tab labelled Pallettes in the Events dialog box. Only Button defintions from the Buttons tab are saved in these pallettes.  Events allow recording of data into your roast profile and when used with Alarms allow for automation of the roasting process.  

Artisan’s standard buttons are as follows:
![Artisan buttons](/assets/images/gsg/standard buttons.png)

The buttons above contain key time points in your roast and after using the trier in the roaster, you would push the button when the event occurs. The buttons table can down be downloaded using the Copy Table button. Pushing these buttons during a roast will add data to your roast log.  You can find the data under `Roast` >> `Properties`, `Data` tab.  The Data and Events tabs can be downloaded using the Copy Table button on those dialogs. The custom event buttons themself come in three sizes (tiny, small and larger). This can be configured in the buttons tab of the Events dialog (menu Config >> Events, 2nd tab).  

![button sizes](/assets/images/gsg/buttton sizes.png)

Sliders can be used to create Events as well.   The sliders appear on the left side and can be used to input a variable value between 0 and 999. Make sure you check Decimal Places under `Curves` >> `UI` if you use them.  Your events will be rendered on your graphs (if you have the Events checked on the Sliders tab) with the first letter of the name of the event and two decimal places.  So Gas at a value of 35 would be G35.  Or if you don’t check decimal places G3.  

You can define up to four custom Events such as Gas and Airflow. Red buttons are Gas readings on propane and the Blue are Fan settings in the example below.
![buttons example](/assets/images/gsg/buttons example.png)


And here is what a slider looks like. NOTE if you have sliders checked on the config tab the initial value will be recorded into Artisan at the start of the roast:

![sliders example](/assets/images/gsg/slider example.png)


In order to set up custom events, you need to create Event types, under `Config` >> `Events`:
![config events](/assets/images/gsg/events config dialog 14.png)

You can label up to 4 event types. You can edit how they work with the tabs Buttons and Sliders.  When you click a button or move a slider Artisan records an event on a scale of 0-999.  You can display these events on your roasting graph.  You may need to set your temperature axis to a low of 0° in order to see these the best.  `Config` >> `Axes`.  If you check Mini Editor you will be able to add or edit existing events during the roast.  The Mini-Editor will appear below your Buttons.  

![events editor](/assets/images/gsg/events editor.png)

You have the option to render event values or descriptions instead of values.  A value would be for example a gas setting that your have set with a slider so if your event button is Gas and the value is 32 it would render G32.  In that that, case don't check the description box.  If you check the description box, it will describe the event.  For example A3(S0) would mean Alarm event 3, slider 0.  

Use the event button type "--" that creates an event adding labels to the graph rendering its button description.  For those using sliders the rendering will continue to be the first letter of the Event name and two digits of the value IF you check Decimal Places under `Config` >> `Curves`, `UI` tab.  If you don’t it will render only one digit.  

During a roast it is now possible to have Artisan draw a line at the current point in time, which helps to compare the current roast state with that of the template (RoR, background event markers,..). You can activate this feature in the Events dialog (menu `Config` >> `Events`) by ticking the flag Show Time Guide.  This helps you see Events you have in your Background roast profile.

![time guide](/assets/images/gsg/time guide.gif)


### Rendering Events on Your Curves

To see the values of the TP, DE, FCs etc, check the box for Annotations.  **You can now drag these Annotations if they are covering something else you want to see to move them on the graph.** 

For Events that you have defined, you will see to the right of Events a dialog box with drop down options:

![combo setting](/assets/images/gsg/combo example.png)

Flag will render an event either on your ET line or your BT line (check the box “show on BT”) and your event value or description if you check the box for Descr. (number represents how many letters).  If you are using values, the first letter of your event name and the event value will be rendered.  

Bar will show you a multicolored bar at the bottom of your graph with the first letter of your event name and the event value. Description is not relevant.

Step will show you a plot (step) graph with no values.  

Step + shows you a plot graph plus your descriptors on the BT line (same choices as under Flag)

Combo shows you a plot graph with the descriptors on the plot (step) graph. Background events are rendered too.  

Here are examples:

*Combo*
![combo example](/assets/images/gsg/combo rendering example.png)


*Step +*
![step+ example](/assets/images/gsg/step+rendering example.png)

You are also now able to add an event type that will show on the graph when you hit the event button.  With this new button type, you can define a button that will add an event item labeled with the description that shows up on the graph. You could record when you take a sample from the trier as an example.  


### Buttons Configuration Sample

![buttons config](/assets/images/gsg/buttons config.gif)

The above screenshot shows the Button Label and Description, Type, Value, Action, Documentation, Visibility, Color and Text Color.  The Label is what shows on the button.  The Description is what shows on the graph, and as with Alarms if you want to enter a note to yourself on what the button does, use a "#" and everything after the # is not displayed.  The Value is from 0-100.  So you have to adjust your scale to that.  For example if you are using 2.0-3.5kPa for gas you might have values 20-35.  You can choose the button to trigger a machine control action such as change the Hottop heater.  You can have the buttons visible or not and choose their color and text.  You can drag and drop to change the order of the buttons.  

*ADVANCED USERS* - The Action column is where you can add automation commands.  Check the Help page for the Events dialog to see all the possibitites.  The number of Artisan commands and other commands continues to grow with each release.  

**Note** in particular the Automation check marks at the bottom. If you want the event Charge to be automatically recorded, you need to press Start and let it be on for 5x your sampling rate in order to have AutoCharge work properly.  So for a sample rate of 3, don't charge the roaster until at least 15 seconds after you push Start.    

*Sliders Configuration Sample*

![sliders sample](/assets/images/gsg/sliders config example.png)  Min and Max are the key settings.  The factor and offset are used to convert dial settings by advanced users to linear output.

[For more information on the configurations of sliders, you can find information from Frans Goddijn’s excellent blog](http://kostverlorenvaart.blogspot.nl/2018/03/sliders-and-offsets-in-artisan.html)



Step and Step+ will have new Annotation options allowing the user to customize the labels that appear on the stair steps.  The user will be able to describe events in plain english with the strings. If your stair steps are too close together there is a setting in the dialog box, Allowed Annotation Overlap, which allows you to not render some the events.  There is also a new setting under `Config` >> `Axes` called 100% Event Step which adjusts where the stair steps show up on your graph.  Please read the [Artisan Blog post](https://artisan-roasterscope.blogspot.com/2020/05/special-events-annotations.html) for more details.

Event Annotations is the last tab in the Events dialog box and offers advanced [display features](https://artisan-roasterscope.blogspot.com/2020/05/special-events-annotations.html):

![Event Annotations Dialog24](/assets/images/gsg/Event Annotations 24.jpg)

A sampling of the string choices:

![Event Annotations Dialog](/assets/images/gsg/Event Annotations.jpg)

The examples:

![Event Annotations Examples](/assets/images/gsg/Event Examples.jpg)

Sample result:

![Event Annotations Results](/assets/images/gsg/Event Annotations Result.jpg)


*Quantifiers*

Quantifiers turn readings received from a connected device into custom events on their 0-100% scale. For example, if you have a channel configured to read burner output on a scale from 0-2000 you can decide to hide the corresponding curve (as it won't fit into the range of the standard temperature axis) or turn just the changes of its readings into events by defining a corresponding quantifier. You end up with a more readable and useful profile.

[Read ](https://artisan-roasterscope.blogspot.com/2014/04/event-quantifiers.html)more about quantifiers for advanced users.

Check out a [video](https://www.youtube.com/watch?time_continue=321&v=IrvC9dPqgjE) on the topic of Buttons and Alarms from an earlier version of Artisan by Michael Wright.

You can create [multiple palettes of buttons](https://artisan-roasterscope.blogspot.com/2013/02/events-buttons-and-palettes.html) as well to use in different roasting situations.
