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

# Shelly Pro 3EM

Artisan reads

- with the extra device of type `Shelly 3EM Pro Energy/Return`
   - total active energy on all phases (`total_act`), consumed or produced in [Wh]
   - total active returned energy on all phases (`total_act_ret`), fed back into the grid in [Wh]
- with the extra device of type `Shelly 3EM Pro Power/S`
   - sum of the active power on all phases (`total_act_power`) in [W]
   - sum of the apparent power on all phases(`total_aprt_power`) in [VA]

 via simple RPC from the host specified in the Devices dialog under `Network >> Shelly Pro 3EM`.


# Shelly Plus Plug


Artisan reads

- with the extra device of type `Shelly Plus Plug Total/Last`
   - total energy consumed (`aenergy.total`) in [Wh]
   - last minutes energy comsumption (`aenergy[0]`) in [mW]
- with the extra device of type `Shelly Plus Plug Power/Temp`
   - Last measured instantaneous active power (`apower`) in [W]
   - device temperature (`temperature.tC`) in C


via simple RPC from the host specified in the Devices dialog under `Network >> Shelly Plus Plug`.