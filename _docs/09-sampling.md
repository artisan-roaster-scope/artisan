---
title: "Sampling"
permalink: /docs/sampling/
excerpt: ""
last_modified_at: 2018-05-15T15:59:00-04:00
toc: false
author: Michael Herbert
author_profile: true
---

### Sampling and Oversampling

Menu: `Confg` >> `Sampling Interval`

![probes meter app](/assets/images/gsg/probes meter app.png)

The default for sampling is set to 3s.  For a Phidget device one second is possible, and Artisan goes down to .5s.  Oversampling will take two readings per interval and average them.

If you go below a 3s interval you will get a popup warning ![interval warning](/assets/images/gsg/sampling interval warning.png)

but you can experiment and see what is best for you. You can try it lower and see if your equipment can handle it. If you go down to 1s or less sampling, and you check oversampling, make sure it doesn't cause graph lines that are to jumpy.  

[More information](https://artisan-roasterscope.blogspot.com/2014/01/sampling-interval-smoothing-and-rate-of.html) on sampling in
Artisan.
