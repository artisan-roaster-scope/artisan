---
title: "Designer"
permalink: /docs/designer/
excerpt: ""
last_modified_at: 2018-05-15T15:59:00-04:00
toc: false
---

### Designer

Menu>Tools>Designer

Designer allows you to create a model roast profile.

![designer](/assets/images/gsg/Designer.png)

To save a profile created in designer mode, go to Tools>Designer and untick the Designer menu item, and you are left with a regular profile that you can save as any other one.

 You can also import a profile into Designer from one of your roasts; however, Designer extrapolates the curve from recorded Events in the profile and it won’t look like your exact profile.  

So, if the original curve is this:

![designer 1](/assets/images/gsg/designer 1.png)

It imports into Artisan by selecting from the top menu, Tools --> Designer. Designer warns you that you'll get something different.

![designer 2](/assets/images/gsg/designer 2.png)

And the result is certainly different.

![designer 3](/assets/images/gsg/designer 3.png)

To design a useful curve to use as a background when you roast next, you'll need to adjust the curve that connects them so it reflects the usual performance of your roaster. Right click to bring up Config, which will allow you to modify the key times like DE, FCs etc.   

![designer4](/assets/images/gsg/designer 4.png)

![designer6](/assets/images/gsg/designer 6.png)


Designing a curve is a sequential process: 1) right click choose - Config - to insert your main points; 2) insert new event points between the events you imported into Designer; 2) grab and drag those in-between points to adjust the curve that connects your imported events; 3) move your key events (vertical lines with dashes) like DE or FCs too where you want them by sliding them left or right; 4)fine tune the roast profile by dragging points to where you want them.  To get a declining the ROR curve make changes in the BT curve. Use a declining ROR curve as your guide to have Designer help you know where to locate targeted events.  

You can also see the impact on the phases by hovering over the colored phases bar.

![designer5](/assets/images/gsg/designer 5.png)
