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

- total active energy on all phases (`total_act`), consumed or produced in [Wh]
- total active returned energy on all phases (`total_act_ret`), fed back into the grid in [Wh]

with the extra device of type `Shelly 3EM Pro Energy/Return` via simple RPC from the host specified in the Devices dialog under `Network >> Shelly Pro 3EM`.


# Shelly Plus Plug


Artisan reads

- total energy consumed (`apower`) in [Wh]
- last minutes energy comsumption (`aenergy[0]`) in [mW]

with the extra device of type `Shelly Plus Plug Total/Last` via simple RPC from the host specified in the Devices dialog under `Network >> Shelly Plus Plug`.