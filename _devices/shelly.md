---
layout: single
permalink: /devices/shelly/
title: "Shelly"
excerpt: "Pro 3EM, Plus Plug"
header:
  overlay_image: /assets/images/shelly-logo.jpg
  image: /assets/images/shelly-logo.jpg
  teaser: assets/images/shelly-logo.jpg
---

# [Shelly Pro 3EM](https://www.shelly.com/products/shelly-pro-3em-3ct63){:target='_blank'}

Artisan reads

- with the extra device of type **`Shelly 3EM Pro Energy/Return`**
   - total active energy on all phases (`total_act`), consumed or produced [Wh]
   - total active returned energy on all phases (`total_act_ret`), fed back into the grid [Wh]
- with the extra device of type **`Shelly 3EM Pro Power/S`**
   - sum of the active power on all phases (`total_act_power`) [W]
   - sum of the apparent power on all phases(`total_aprt_power`) [VA]

 via simple RPC from the host specified in the Devices dialog under `Network >> Shelly Pro 3EM`.


# [Shelly Plus Plug](https://www.shelly.com/products/shelly-plug-s-gen3){:target='_blank'}


Artisan reads

- with the extra device of type **`Shelly Plug Total/Last`**
   - total energy consumed (`aenergy.total`) [Wh]
   - last minutes energy comsumption (`aenergy[0]`) [mW]
- with the extra device of type **`Shelly Plug Power/Temp`**
   - last measured instantaneous active power (`apower`) [W]
   - device temperature (`temperature.tC`) [C]
- with the extra device of type **`Shelly Plug Voltage/Current`**
   - voltage (`voltage`) [V]
   - current (`current`) [A]

via simple RPC from the host specified in the Devices dialog under `Network >> Shelly Plus Plug`.

Artisan can also switch the Shelly Plugs ON and OFF via custom event buttons using the `IO Command`

```
shellyrelay(n,b)
```

where `n` is the number of the plug (use 0 if the device has just one) and `b` is either 1 or `true` to turn the plug ON, or 0, `false` to turn it OFF.


