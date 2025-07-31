#
# ABOUT
# ROEST CSV Roast Profile importer for Artisan

from pathlib import Path
import os
import csv
import re
import logging
from typing import Final, Optional, List, Dict, Callable

from artisanlib.util import encodeLocalStrict
from artisanlib.atypes import ProfileData

_log: Final[logging.Logger] = logging.getLogger(__name__)


# returns a dict containing all profile information contained in the given ROEST CSV file
def extractProfileRoestCSV(file:str,
        _etypesdefault:List[str],
        alt_etypesdefault:List[str],
        _artisanflavordefaultlabels:List[str],
        eventsExternal2InternalValue:Callable[[int],float]) -> ProfileData:
    res:ProfileData = ProfileData() # the interpreted data set

    res['samplinginterval'] = 1.0

    res['roastertype'] = 'ROEST Sample Roaster'
    res['roastersize'] = 0.1
    res['roasterheating'] = 3 # electric

    # set profile title and batch number from the file name if it has the format "<name> - Batch <nnnn>.csv"
    try:
        filename = os.path.basename(file)
        p = re.compile(r'([^-]*) - Batch (\d{1,6}).csv')
        match = p.match(filename)
        if match is not None:
            groups = match.groups()
            if len(groups) == 2:
                res['title'] = encodeLocalStrict(groups[0])
                res['roastbatchnr'] = int(groups[1])
            else:
                res['title'] = encodeLocalStrict(Path(file).stem)
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)

    with open(file, newline='',encoding='utf-8-sig') as csvFile:
        data = csv.reader(csvFile,delimiter=',')
        #read file header
        header = [h.strip() for h in next(data)]

        fan:Optional[float] = None # holds last processed fan event value
        fan_last:Optional[float] = None # holds the fan event value before the last one
        heater:Optional[float] = None # holds last processed heater event value
        heater_last:Optional[float] = None # holds the heater event value before the last one
        drum:Optional[float] = None # holds last processed drum speed event value
        drum_last:Optional[float] = None # holds the drum speed event value before the last one

        specialevents:List[int] = []
        specialeventstype:List[int] = []
        specialeventsvalue:List[float] = []
        specialeventsStrings:List[str] = []

        timex:List[float] = []
        temp1:List[float] = []
        temp2:List[float] = []

        extra1:List[float] = []  # Inlet temp (°C)
        extra2:List[float] = []  # Target (°C)
        extra3:List[float] = []  # Heater (%)
        extra4:List[float] = []  # --- Heater PV (not used)
        extra5:List[float] = []  # RPM (RPM)
        extra6:List[float] = []  # ---- Drum PV (not used)
        extra7:List[float] = []  # Fan (%)
        extra8:List[float] = []  # ---- Fan PV (not used)
        extra9:List[float] = []  # Drum temp (°C)
        extra10:List[float] = []  # Exhaust Temp (°C)

        v:Optional[float]


        timeindex:List[int] = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actual index used
        i:int = -1
        for row in data:
            i += 1
            items = list(zip(header, row))
            item:Dict[str,str] = {}
            for (name, value) in items:
                item[name] = value.strip()
            # take i as time in seconds
            try:
                timex.append(float(item['Time'])/1000)
            except Exception:  # pylint: disable=broad-except
                timex.append(i)

            if 'Air temp (°C)' in item:
                temp1.append(float(item['Air temp (°C)']))
            else:
                temp1.append(-1)

            if 'Bean temp (°C)' in item:
                temp2.append(float(item['Bean temp (°C)']))
            else:
                temp2.append(-1)

            # mark CHARGE
            if timeindex[0] < 0:
                timeindex[0] = max(0,i)

            # mark DRY
            if item['Event'].strip() == 'Yellowing' and timeindex[1] == 0:
                timeindex[1] = i

            # mark FCs
            if item['Event'].strip() == 'Firstcrack' and timeindex[2] == 0:
                timeindex[2] = i



            if 'Inlet temp (°C)' in item:
                extra1.append(float(item['Inlet temp (°C)']))
            else:
                extra1.append(-1)

            if 'Target (°C)' in item:
                extra2.append(float(item['Target (°C)']))
            else:
                extra2.append(-1)

            if 'Power (%)' in item:
                extra3.append(float(item['Power (%)']))
            else:
                extra3.append(-1)

            # unused
            extra4.append(-1)

            if 'RPM (RPM)' in item:
                extra5.append(float(item['RPM (RPM)']))
            else:
                extra5.append(-1)

            # unused
            extra6.append(-1)

            if 'Fan (%)' in item:
                extra7.append(float(item['Fan (%)']))
            else:
                extra7.append(-1)

            # unused
            extra8.append(-1)

            if 'Drum temp (°C)' in item:
                extra9.append(float(item['Drum temp (°C)']))
            else:
                extra9.append(-1)

            if 'Exhaust Temp (°C)' in item:
                extra10.append(float(item['Exhaust Temp (°C)']))
            else:
                extra10.append(-1)

            if 'Fan (%)' in item:
                try:
                    v = float(item['Fan (%)'])
                    if v is not None and v != fan:
                        # fan value changed
                        if v == fan_last:
                            # just a fluctuation, we remove the last added fan value again
                            fan_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 0)
                            del specialeventsvalue[fan_last_idx]
                            del specialevents[fan_last_idx]
                            del specialeventstype[fan_last_idx]
                            del specialeventsStrings[fan_last_idx]
                            fan = fan_last
                            fan_last = None
                        else:
                            fan_last = fan
                            fan = v
                            v = v/10. + 1
                            specialeventsvalue.append(v)
                            specialevents.append(i)
                            specialeventstype.append(0)
                            specialeventsStrings.append(f'{fan}' + '%')
                    else:
                        fan_last = None
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)

            if 'RPM (RPM)' in item:
                try:
                    v = float(item['RPM (RPM)'])
                    if v is not None and v != drum:
                        # drum value changed
                        if v == drum_last:
                            # just a fluctuation, we remove the last added drum value again
                            drum_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 1)
                            del specialeventsvalue[drum_last_idx]
                            del specialevents[drum_last_idx]
                            del specialeventstype[drum_last_idx]
                            del specialeventsStrings[drum_last_idx]
                            heater = heater_last
                            heater_last = None
                        drum_last = drum
                        drum = v
                        v = v/10. + 1
                        specialeventsvalue.append(v)
                        specialevents.append(i)
                        specialeventstype.append(1)
                        specialeventsStrings.append(f'{drum}' + '%')
                    else:
                        drum_last = None
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)

            if 'Power (%)' in item:
                try:
                    v = float(item['Power (%)'])
                    if v is not None and v != heater:
                        # heater value changed
                        if v == heater_last:
                            # just a fluctuation, we remove the last added heater value again
                            heater_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 3)
                            del specialeventsvalue[heater_last_idx]
                            del specialevents[heater_last_idx]
                            del specialeventstype[heater_last_idx]
                            del specialeventsStrings[heater_last_idx]
                            heater = heater_last
                            heater_last = None
                        heater_last = heater
                        heater = v
                        specialeventsvalue.append(eventsExternal2InternalValue(int(round(v))))
                        specialevents.append(i)
                        specialeventstype.append(3)
                        specialeventsStrings.append(f'{heater}' + '%')
                    else:
                        heater_last = None
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)

    # mark DROP
    if timeindex[6] == 0:
        timeindex[6] = max(0,i)

    res['mode'] = 'C'

    res['timex'] = timex
    res['temp1'] = temp1
    res['temp2'] = temp2
    res['timeindex'] = timeindex

    res['extradevices'] = [50, 50, 50, 50, 50]
    res['extratimex'] = [timex[:],timex[:],timex[:],timex[:],timex[:]]

    res['extraname1'] = ['IT', '{3}', '{1}', '{0}', '{1} {4}']
    res['extratemp1'] = [extra1, extra3, extra5, extra7, extra9]
    res['extramathexpression1'] = ['', '', '', '', '']

    res['extraname2'] = ['SV', '-', '-', '-', 'XT']
    res['extratemp2'] = [extra2, extra4, extra6, extra8, extra10]
    res['extramathexpression2'] = ['', '', '', '', '']

    res['extraCurveVisibility1'] = [True, False, False, False, True, True, True, True, True, True]
    res['extraCurveVisibility2'] = [True, False, False, False, True, True, True, True, True, True]
    res['extraDelta1'] = [False]*10
    res['extraDelta2'] = [False]*10
    res['extraNoneTempHint1'] = [True, False, False, False, True]
    res['extraNoneTempHint2'] = [True, True, True, True, True]

    if len(specialevents) > 0:
        res['specialevents'] = specialevents
        res['specialeventstype'] = specialeventstype
        res['specialeventsvalue'] = specialeventsvalue
        res['specialeventsStrings'] = specialeventsStrings

    res['etypes'] = alt_etypesdefault

    return res
