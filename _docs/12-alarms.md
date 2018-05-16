---
title: "Alarms"
permalink: /docs/alarms/
excerpt: ""
last_modified_at: 2018-05-15T15:59:00-04:00
toc: false
---

### Alarms

Menu>Config>Alarms

Alarms can warn you of certain events and they can also trigger certain things to happen.  For some advanced users, you can even control the roaster with Alarms.  

Artisan blog posts explain how to work with Alarms:

[Basics](https://artisan-roasterscope.blogspot.com/2013/03/alarms.html)

[Creation of alarms dependent upon other alarms](https://artisan-roasterscope.blogspot.com/2016/08/more-alarms.html)

[Talking alarms](https://artisan-roasterscope.blogspot.com/2017/12/talking-alarms.html)

Here is a simple alarm that ROR is at 30 after the charge so that the roasters focuses on the next adjustment to make.  The alarm triggers a pop-up.  New in 1.3, is you can have the pop-up disappear after a X seconds.

![alarm sample](/assets/images/gsg/alarm config example.png)


Alarms are unordered by definition. All alarm conditions of not-yet activated alarms are evaluated once per sampling interval and where all pre-conditions are fulfilled the alarm is fired. Note that each alarm is only fired once.  An alarm is triggered only once even if it has both an alarm time and temperature trigger set.  

You can program alarms to push an Event button, such as mark - Air Min at Charge.  In this case my Event Button 11 is Air Min.
![alarm event](/assets/images/gsg/alarm event example.png)

Note that some Dialog boxes throughout Artisan (cut off in the one above) have a Help button.  

Here is the one for Alarms:
![alarm help dialog](/assets/images/gsg/alarm help dialog.png)


Michael Wright, in the video linked above, uses Alarms for a much more sophisticated purpose in controlling his machine.  His alarm dialog is below for reference.

![alarms advanced](/assets/images/gsg/alarm pallette advanced.png)


Linked is another [video](https://www.youtube.com/watch?v=hYX6c1_rxFI) on alarms to cause an action
