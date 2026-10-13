---
layout: single
permalink: /devices/lebrew/
title: "RoastSee NEXT"
excerpt: "Realtime Color & Cracks"
header:
  overlay_image: /assets/images/RoastSee_Next.webp
  image: /assets/images/RoastSee_Next.webp
  teaser: assets/images/RoastSee_Next.webp
toc: false
toc_label: "On this page"
toc_icon: "cog"
---

The laser-based [RoastSee NEXT](https://lebrewtech.com/products/roastsee-next-3) is a real-time color meter by [Lebrew](https://lebrewtech.com/). The device reports Agtron readings during a roast. It connects to artisan scope via Bluetooth low-energy (BLE) to record the color curve and automatically which can be used to mark the DRY event based on a signal calculated by the device from the color curves RoR.

Artisan scope comes with a one-click machine setup which keeps the main device as configured but overwrites the extra device configuration adding the data channels provided by the Lebrew RoastSee NEXT. Those can be configured as well manually to extend existing extra device channels.

The device types connecting to the RoastSee NEXT are

- RoastSeeNEXT Agtron/Noise   
   - Agtron reading \[0,100\[
   - Noise \[0,46\] (0 before 45s after Yellow/DRY)
- RoastSeeNEXT RoR/FoR
   - RoR of the Agtron signal
   - Smoothed Agtron signal (outlier and weighted median over last 10 readings)
- RoastSeeNEXT Distance/Time
   - Distance to surface in mm
   - Time of detect Yellow/DRY point in seconds since recording on device started
- RoastSeeNEXT Yellow
   - Yellow mark (1 at the moment the Yellow/DRY point was detected; 0 otherwise)


The IO Command `lebrew(\<msg\>)` sends the given `\<msg\>` to the device while it is connected. This command can be assigned to buttons as shown below. Supported messages are

- `roasting` : switch to roasting screen
- `start` : start recording and start sending readings to artisan
- `stop` : stop recording and stop sending readings to artisan

On pressing the ON button, artisan scope connects to the device and sends the message `roasting` followed by the message `start` to receive readings.

<figure>
<a href="{{ site.baseurl }}/assets/images/RoastSeeNEXT_event_buttons.webp" target="_blank">
<img width="60%" src="{{ site.baseurl }}/assets/images/RoastSeeNEXT_event_buttons.webp"></a>
    <figcaption>Custom event buttons</figcaption>
</figure>

<figure>
<a href="{{ site.baseurl }}/assets/images/RoastSeeNEXT_clock_restart.webp" target="_blank">
<img width="60%" src="{{ site.baseurl }}/assets/images/RoastSeeNEXT_clock_restart.webp"></a>
    <figcaption>Restart device clock on CHARGE</figcaption>
</figure>