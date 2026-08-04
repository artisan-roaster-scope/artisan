## Summary

Adds support for the **Skywalker V2 "Cyberroaster"** (ITOP FIR/NIR radiant electric drum
roaster) as a new Artisan device, over a **TC4-over-BLE** transport.

The change is **strictly additive and guarded**: no existing Artisan behavior changes when
the device is not selected. All device-specific logic lives in a new self-contained module
`src/artisanlib/skywalker.py`; the edits to core files are append-only and confined to
wiring the new device into Artisan's hardcoded device list.

## What's added

Two device entries are registered (ids must match their position in `devicefunctionlist`):

- **207 — `Skywalker BT/ET`**: main device, reads Bean Temp / Env Temp over BLE.
- **208 — `+Skywalker Burner/Air`**: extra device, echoes the OT1/OT2 duty values
  (burner / airflow) as percentages.

Both are `nonserial` (BLE, no serial-port plumbing). The `skywalker(OTn, val)` alarm command
lets roast events drive burner/airflow.

## Files touched

| File | Change |
|------|--------|
| `src/artisanlib/skywalker.py` | **New** — self-contained TC4-over-BLE device class |
| `src/artisanlib/comm.py` | `SKYWALKER_BTET` (207) + `SKYWALKER_PF` (208), appended to `devicefunctionlist` |
| `src/artisanlib/canvas.py` | Device-list entries, `nonserial` flag, BLE connect/disconnect |
| `src/artisanlib/devices.py` | Main-device selection for device 207 |
| `src/artisanlib/main.py` | `aw.skywalker` attribute, settings load/save, `skywalker(OTn,val)` alarm command |
| `src/help/eventbuttons_help.py`, `src/help/eventsliders_help.py` | `skywalker()` command documentation |
| `src/artisan.pro` | Register the new source file |

## Design notes / things to review

- **Device indices (207/208):** these *must* equal their position in
  `serialport.devicefunctionlist`. They are correct against the current `master` (last native
  entry being `+MQTT 1112` at 206). If other devices have landed since, the indices and the
  matching entries in `canvas.py` / `devices.py` / `comm.py` need to be shifted together.
- **Temperature units:** the Skywalker reports Celsius; values are converted with
  `fromCtoFstrict` only when `qmc.mode == 'F'`.
- **Hardware behavior (FIR/NIR specifics):** unlike classical roasters, **ET < BT is normal**
  on this machine (BT rises faster than ET right after the turning point). RoR_BT/RoR_ET
  ratios are not meaningful here. AirWave airflow above ~30% cools the drum.
- **Transport choice:** Bluetooth SPP is not viable on this firmware (it forces a PIN re-pair
  after every disconnect), so TC4-over-BLE is used as the reliable transport.
- Every fork-specific line in core files is marked with a `## CYBER ##` comment for easy
 