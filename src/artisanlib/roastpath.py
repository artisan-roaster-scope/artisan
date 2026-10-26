#
# ABOUT
# RoastPATH HTML roast profile importer for artisan scope
#
# COPYRIGHT (C) 2010-2026 The artisan team represented by
#   Marko Luther <marko.luther@gmx.net> (maintainer) and all contributors
#
# LICENSE
# This program or module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# MAINTAINER
# Marko Luther, 2026

import time
import json
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Final

from PyQt6.QtWidgets import QApplication

from artisanlib.util import weight_units, fromCtoFstrict #encodeLocal
from artisanlib.atypes import ProfileData


_log: Final[logging.Logger] = logging.getLogger(__name__)


# returns a dict containing all profile information contained in the given RoastPATH RPATH JSON file
def extractProfileRoastPath(file:str,
        _etypesdefault:list[str],
        _alt_etypesdefault:list[str],
        _artisanflavordefaultlabels:list[str],
        _eventsExternal2InternalValue:Callable[[int],float]
        ) -> ProfileData:
    res:ProfileData = ProfileData() # the interpreted data set

    with open(file, encoding='utf-8') as f:
        roastpath_data = json.load(f)

        res['samplinginterval'] = 1.0
        res['mode'] = 'C'
        res['roastepoch'] = int(roastpath_data.get('StartTimeEpoch', time.time()))
        res['title'] = roastpath_data.get('Name', QApplication.translate('Scope Title', 'Roaster Scope'))
        res['weight'] = [roastpath_data.get('BatchSizeKg',0),0,weight_units[1]]
        res['roastingnotes'] = roastpath_data.get('Notes', '')
        res['beans'] = roastpath_data.get('CoffeeName', '')

        timeindex:list[int] = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actual index used
        timex:list[float] = []
        temp1:list[float] = []
        temp2:list[float] = []

        # Key mapping structure: time_map[seconds_after_start][reading_type_name] = value
        time_map:dict[float, dict[int, float]] = defaultdict(dict)
        readings_list = roastpath_data.get('Readings', [])
        for readings in readings_list:
            if 'ReadingTypeId' in readings:
                reading_type = readings['ReadingTypeId']
                uom = readings.get('UomId', 0) # 0: F, 2: C
                data_points = readings.get('Data', [])

                if data_points:
                    for pt in data_points:
                        if 'SecondsAfterStart' in pt and 'StandardValue' in pt:
                            try:
                                seconds = pt.get('SecondsAfterStart')
                                val = pt.get('StandardValue')
                                if val != -1 and uom != 2:
                                    val = fromCtoFstrict(val) # convert to C
                                time_map[seconds][reading_type] = val
                            except Exception:  # pylint: disable=broad-except
                                pass

        timex = sorted(time_map.keys())
        for tx in timex:
            temp1.append(time_map[tx].get(3,-1))
            temp2.append(time_map[tx].get(1,-1))

        try:
            timeindex[0] = timex.index(0)
        except ValueError:
            pass

        for (tag, tidx) in [('GreenYellowSAS', 1), ('FirstCrackSAS', 2), ('SecondCrackSAS', 4), ('DropSAS', 6)]:
            if tag in roastpath_data:
                try:
                    sas = roastpath_data[tag]
                    if sas != 0:
                        timeindex[tidx] = timex.index(sas)
                except ValueError:
                    pass

        res['timex'] = timex
        res['temp1'] = temp1
        res['temp2'] = temp2
        res['timeindex'] = timeindex

    return res
