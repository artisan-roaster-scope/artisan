# The project file for the Artisan application.
#
# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# This file is part of Artisan.

# not sure if the following is strictly needed (might be needed for accent characters in source of translations)
CODECFORSRC = UTF-8
CODECFORTR = UTF-8

SOURCES = \
    artisanlib/alarms.py \
    artisanlib/autosave.py \
    artisanlib/axis.py \
    artisanlib/background.py \
    artisanlib/batches.py \
    artisanlib/calculator.py \
    artisanlib/colors.py \
    artisanlib/comm.py \
    artisanlib/comparator.py \
    artisanlib/cropster.py \
    artisanlib/cup_profile.py \
    artisanlib/curves.py \
    artisanlib/designer.py \
    artisanlib/devices.py \
    artisanlib/dialogs.py \
    artisanlib/events.py \
    artisanlib/giesen.py \
    artisanlib/ikawa.py \
    artisanlib/large_lcds.py \
    artisanlib/logs.py \
    artisanlib/main.py \
    artisanlib/modbusport.py \
    artisanlib/phases.py \
    artisanlib/pid_control.py \
    artisanlib/pid_dialogs.py \
    artisanlib/platformdlg.py \
    artisanlib/ports.py \
    artisanlib/roast_properties.py \
    artisanlib/rubasse.py \
    artisanlib/s7port.py \
    artisanlib/sampling.py \
    artisanlib/statistics.py \
    artisanlib/transposer.py \
    artisanlib/wheels.py \
    artisanlib/wsport.py \
    help/alarms_help.py \
    help/autosave_help.py \
    help/energy_help.py \
    help/eventannotations_help.py \
    help/eventbuttons_help.py \
    help/eventsliders_help.py \
    help/keyboardshortcuts_help.py \
    help/modbus_help.py \
    help/programs_help.py \
    help/s7_help.py \
    help/symbolic_help.py \
    help/transposer_help.py \
    plus/blend.py \
    plus/controller.py \
    plus/countries.py \
    plus/login.py \
    plus/queue.py \
    plus/stock.py \
    plus/sync.py

# the list of translation has to be synced with the script pylupdate6pro (for pylupdate6)
TRANSLATIONS = \
	translations/artisan_ar.ts \
	translations/artisan_da.ts \
	translations/artisan_de.ts \
	translations/artisan_el.ts \
	translations/artisan_es.ts \
	translations/artisan_fa.ts \
	translations/artisan_fi.ts \
	translations/artisan_fr.ts \
	translations/artisan_gd.ts \
	translations/artisan_he.ts \
	translations/artisan_hu.ts \
	translations/artisan_id.ts \
	translations/artisan_it.ts \
	translations/artisan_ja.ts \
	translations/artisan_ko.ts \
	translations/artisan_lv.ts \
	translations/artisan_nl.ts \
	translations/artisan_no.ts \
	translations/artisan_pl.ts \
	translations/artisan_pt_BR.ts \
	translations/artisan_pt.ts \
	translations/artisan_ru.ts \
	translations/artisan_sk.ts \
	translations/artisan_sv.ts \
	translations/artisan_th.ts \
	translations/artisan_tr.ts \
	translations/artisan_uk.ts \
	translations/artisan_vi.ts \
	translations/artisan_zh_CN.ts \
	translations/artisan_zh_TW.ts
