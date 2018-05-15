---
title: "Events"
permalink: /docs/events/
excerpt: ""
last_modified_at: 2018-05-15T15:59:00-04:00
---

### Events

Creating Events allows you to record data with either Buttons or Sliders.  

Artisan’s standard buttons are as follows:
![Artisan buttons](/assets/images/gsg/standard buttons.png)

The buttons above contain key time points in your roast and after using the trier in the roaster, you would hit the button when the event occurs.  Pushing these buttons during a roast will add data to your roast log.  You can find the data under Roast>Properties>Data tab.

Sliders can be used to create Events as well.   The sliders appear on the left side and can be used to input a variable value between 0 and 999.  There is an image in the next section.  Make sure you check Decimal Places under Curves>UI if you use them.  Your events will be rendered on your graphs with the first letter of the name of the event and two decimal places.  So Gas at a value of 35 would be G35.  Or if you don’t check decimal places G3.  

You can define up to four custom Events such as Gas and Airflow. Red buttons are Gas readings on propane and the Blue are Fan settings.
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
