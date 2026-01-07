#
# ABOUT
# HiBean JSON roast profile importer for Artisan

#from pathlib import Path
#import os
import time as libtime
import json
#import re
import logging
from collections.abc import Callable
from typing import Final

from PyQt6.QtCore import QDateTime, Qt

from artisanlib.util import encodeLocalStrict, encodeLocal, weight_units, weight_units_lower
from artisanlib.atypes import ProfileData

_log: Final[logging.Logger] = logging.getLogger(__name__)


# returns a dict containing all profile information contained in the given HiBean JSON file
def extractProfileHiBeanJSON(file:str,
        _etypesdefault:list[str],
        alt_etypesdefault:list[str],
        _artisanflavordefaultlabels:list[str],
        eventsExternal2InternalValue:Callable[[int],float]) -> ProfileData:
    res:ProfileData = ProfileData() # the interpreted data set

    with open(file, encoding='utf-8') as f:
        hibean_data = json.load(f)

        res['samplinginterval'] = hibean_data.get('sampleInterval', 1.0)
        res['mode'] = hibean_data.get('temperatureUnit', 'C')

        date_time_str = hibean_data.get('dateTime', '') # e.g. "2025-03-29T09:09:29.000", an ISO 8601 DateTime
        if date_time_str:
            date_time:QDateTime = QDateTime.fromString(date_time_str, Qt.DateFormat.ISODate)
            roastdate:str|None = encodeLocal(date_time.date().toString())
            if roastdate is not None:
                res['roastdate'] = roastdate
            roastisodate:str|None = encodeLocal(date_time.date().toString(Qt.DateFormat.ISODate))
            if roastisodate is not None:
                res['roastisodate'] = roastisodate
            roasttime:str|None = encodeLocal(date_time.time().toString())
            if roasttime is not None:
                res['roasttime'] = roasttime
            res['roastepoch'] = int(date_time.toSecsSinceEpoch())
            res['roasttzoffset'] = libtime.timezone

        res['roastingnotes'] = hibean_data.get('notes', '')

        roast_context = hibean_data.get('roastContext', {})

        res['title'] = roast_context.get('name', '')

        res['weight'] = [0,0,weight_units[0]]
        res['weight'][0] = roast_context.get('greenBeanWeight', {}).get('value', 0.0) if roast_context.get('greenBeanWeight') is not None else 0.0
        res['weight'][1] = roast_context.get('roastedBeanWeight', {}).get('value', 0.0) if roast_context.get('roastedBeanWeight') is not None else 0.0
        weight_unit = roast_context.get('greenBeanWeight', {}).get('unit', 'g').lower()
        if weight_unit == 'lbs':
            weight_unit = 'lb'
        weight_unit_idx = 0 # defaults to 'g' for unknown weight units
        try:
            weight_unit_idx = weight_units_lower.index(weight_unit)
        except ValueError:
            pass
        try:
            res['weight'][2] = weight_units[weight_unit_idx]
        except ValueError:
            pass

        res['ambientTemp'] = roast_context.get('envTemp', {}).get('value', 0.0) if roast_context.get('envTemp') is not None else 0.0
        res['ambient_humidity'] = roast_context.get('envHumidity', 0) if roast_context.get('envHumidity') is not None else 0
        res['ambient_pressure'] = roast_context.get('pressure', 0) if roast_context.get('pressure') is not None else 0

        device_info = hibean_data.get('deviceInfo', {})
        res['roastertype'] = device_info.get('name','')

        event2timeindex:list[int|None] = [None, 0, None, 1, 2, 3, 4, 5, 6] # maps HiBean event numbers to Artisan timeindex or None if no correspondence
        timeindex:list[int] = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actual index used
        timex:list[float] = []
        temp1:list[float] = []
        temp2:list[float] = []

        specialevents:list[int] = []
        specialeventstype:list[int] = []
        specialeventsvalue:list[float] = []
        specialeventsStrings:list[str] = []

        data_list = hibean_data.get('dataList', [])

        last_fan:int|None = None
        last_heat:int|None = None
        last_drum:int|None = None
        last_ts:int|None = None

        for idx, data_point in enumerate(data_list):
            timex.append(data_point.get('duration', 0.0))
            temp1.append(data_point.get('et', 0.0))
            temp2.append(data_point.get('bt', 0.0))
            if 'event' in data_point:
                try:
                    time_idx:int|None = event2timeindex[int(data_point['event'])]
                    if time_idx is not None:
                        timeindex[time_idx] = idx
                except Exception:  # pylint: disable=broad-except
                    pass

            roaster_params = data_point.get('roasterParams', [])

            try:
                fan:int = int(round(next((float(param.get('value', 0.0)) for param in roaster_params if param.get('key') == 'FC'), 0.0)))
                if fan != last_fan:
                    last_fan = fan
                    specialeventsvalue.append(eventsExternal2InternalValue(fan))
                    specialevents.append(idx)
                    specialeventstype.append(0)
                    specialeventsStrings.append(f'{fan}' + '%')
            except Exception: # pylint: disable=broad-except
                pass

            try:
                heat:int = int(round(next((float(param.get('value', 0.0)) for param in roaster_params if param.get('key') == 'HP'), 0.0)))
                if heat != last_heat:
                    last_heat = heat
                    specialeventsvalue.append(eventsExternal2InternalValue(heat))
                    specialevents.append(idx)
                    specialeventstype.append(3)
                    specialeventsStrings.append(f'{heat}' + '%')
            except Exception: # pylint: disable=broad-except
                pass

            try:
                drum:int = int(round(next((float(param.get('value', 0.0)) for param in roaster_params if param.get('key') == 'RC'), 0.0)))
                if drum != last_drum:
                    last_drum = drum
                    specialeventsvalue.append(eventsExternal2InternalValue(drum))
                    specialevents.append(idx)
                    specialeventstype.append(1)
                    specialeventsStrings.append(f'{drum}' + '%')
            except Exception: # pylint: disable=broad-except
                pass

            try:
                ts:int = int(round(next((float(param.get('value', 0.0)) for param in roaster_params if param.get('key') == 'TS'), 0.0)))
                if ts != last_ts:
                    last_ts = ts
                    specialeventsvalue.append(eventsExternal2InternalValue(ts))
                    specialevents.append(idx)
                    specialeventstype.append(2)
                    specialeventsStrings.append(str(ts))
            except Exception: # pylint: disable=broad-except
                pass

        res['timex'] = timex
        res['temp1'] = temp1
        res['temp2'] = temp2
        res['timeindex'] = timeindex

        if len(specialevents) > 0:
            res['specialevents'] = specialevents
            res['specialeventstype'] = specialeventstype
            res['specialeventsvalue'] = specialeventsvalue
            res['specialeventsStrings'] = specialeventsStrings

        alt_etypesdefault[2] = 'TS'
        res['etypes'] = [encodeLocalStrict(etype) for etype in alt_etypesdefault]



    return res
