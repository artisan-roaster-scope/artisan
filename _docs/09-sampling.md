---
title: "Sampling"
permalink: /docs/sampling/
excerpt: ""
last_modified_at: 2018-05-15T15:59:00-04:00
---

### Sampling and Oversampling

The default for sampling is set to 3s.  For a Phidget device one second is possible, and Artisan 1.3 goes down to .5s now.  Oversampling will take two readings per interval and average them.

If you go below a 3s interval you will get a popup warning ![interval warning](/assets/images/gsg/sampling interval warning.png)


You can try it lower and see if your equipment can handle it.  There have been reports that if you go down to 1s sampling, do NOT check oversampling as it causes very jumpy lines.  

Click for [more information on sampling in
Artisan](https://artisan-roasterscope.blogspot.com/2014/01/sampling-interval-smoothing-and-rate-of.html)
