#
# ABOUT
# IKAWA CSV Roast Profile importer for Artisan

from pathlib import Path
import time as libtime
import os
import csv
import re
import logging
try:
    from typing import Final
except ImportError:
    # for Python 3.7:
    from typing_extensions import Final

try:
    #ylint: disable = E, W, R, C
    from PyQt6.QtCore import QDateTime,Qt # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #ylint: disable = E, W, R, C
    from PyQt5.QtCore import QDateTime,Qt # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.util import encodeLocal


_log: Final = logging.getLogger(__name__)

# returns a dict containing all profile information contained in the given IKAWA CSV file
def extractProfileIkawaCSV(file,_):
    res = {} # the interpreted data set

    res['samplinginterval'] = 1.0

    # set profile date from the file name if it has the format "IKAWA yyyy-mm-dd hhmmss.csv"
    try:
        filename = os.path.basename(file)
        p = re.compile(r'IKAWA \d{4,4}-\d{2,2}-\d{2,2} \d{6,6}.csv')
        if p.match(filename):
            s = filename[6:-4] # the extracted date time string
            date = QDateTime.fromString(s,'yyyy-MM-dd HHmmss')
            res['roastdate'] = encodeLocal(date.date().toString())
            res['roastisodate'] = encodeLocal(date.date().toString(Qt.DateFormat.ISODate))
            res['roasttime'] = encodeLocal(date.time().toString())
            res['roastepoch'] = int(date.toSecsSinceEpoch())
            res['roasttzoffset'] = libtime.timezone
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)

    with open(file, newline='',encoding='utf-8') as csvFile:
        data = csv.reader(csvFile,delimiter=',')
        #read file header
        header = next(data)

        fan = None # holds last processed fan event value
        fan_last = None # holds the fan event value before the last one
        heater = None # holds last processed heater event value
        heater_last = None # holds the heater event value before the last one
        fan_event = False # set to True if a fan event exists
        heater_event = False # set to True if a heater event exists
        specialevents = []
        specialeventstype = []
        specialeventsvalue = []
        specialeventsStrings = []
        timex = []
        temp1 = []
        temp2 = []
        extra1 = []
        extra2 = []
        timeindex = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actal index used
        i = 0
        for row in data:
            i = i + 1
            items = list(zip(header, row))
            item = {}
            for (name, value) in items:
                item[name] = value.strip()
            # take i as time in seconds
            timex.append(i)
            if 'inlet temp' in item:
                temp1.append(float(item['inlet temp']))
            elif 'temp below' in item:
                temp1.append(float(item['temp below']))
            else:
                temp1.append(-1)
            # we map IKAWA Exhaust to BT as main events like CHARGE and DROP are marked on BT in Artisan
            if 'exaust temp' in item:
                temp2.append(float(item['exaust temp']))
            elif 'temp above' in item:
                temp2.append(float(item['temp above']))
            else:
                temp2.append(-1)
            # mark CHARGE
            if not timeindex[0] > -1 and 'state' in item and item['state'] == 'doser open':
                timeindex[0] = max(0,i)
            # mark DROP
            if timeindex[6] == 0 and 'state' in item and item['state'] == 'cooling':
                timeindex[6] = max(0,i)
            # add SET and RPM
            if 'temp set' in item:
                extra1.append(float(item['temp set']))
            elif 'setpoint' in item:
                extra1.append(float(item['setpoint']))
            else:
                extra1.append(-1)
            if 'fan speed (RPM)' in item:
                rpm = float(item['fan speed (RPM)'])
                extra2.append(rpm/100)
            elif 'fan speed' in item:
                rpm = float(item['fan speed'])
                extra2.append(rpm/100)
            else:
                extra2.append(-1)

            if 'fan set (%)' in item or 'fan set' in item:
                try:
                    if 'fan set (%)' in item:
                        v = float(item['fan set (%)'])
                    elif 'fan set' in item:
                        v = float(item['fan set'])
                    if v != fan:
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
                            fan_event = True
                            v = v/10. + 1
                            specialeventsvalue.append(v)
                            specialevents.append(i-1)
                            specialeventstype.append(0)
                            specialeventsStrings.append(f'{fan}' + '%')
                    else:
                        fan_last = None
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            if 'heater power (%)' in item or 'heater' in item:
                try:
                    if 'heater power (%)' in item:
                        v = float(item['heater power (%)'])
                    elif 'heater' in item:
                        v = float(item['heater'])
                    if v != heater:
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
                        else:
                            heater_last = heater
                            heater = v
                            heater_event = True
                            v = v/10. + 1
                            specialeventsvalue.append(v)
                            specialevents.append(i-1)
                            specialeventstype.append(3)
                            specialeventsStrings.append(f'{heater}' + '%')
                    else:
                        heater_last = None
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)

    res['mode'] = 'C'

    res['timex'] = timex
    res['temp1'] = temp1
    res['temp2'] = temp2
    res['timeindex'] = timeindex

    res['extradevices'] = [25]
    res['extratimex'] = [timex[:]]

    res['extraname1'] = ['SET']
    res['extratemp1'] = [extra1]
    res['extramathexpression1'] = ['']

    res['extraname2'] = ['RPM']
    res['extratemp2'] = [extra2]
    res['extramathexpression2'] = ['x/100']

    if len(specialevents) > 0:
        res['specialevents'] = specialevents
        res['specialeventstype'] = specialeventstype
        res['specialeventsvalue'] = specialeventsvalue
        res['specialeventsStrings'] = specialeventsStrings
        if heater_event or fan_event:
            # first set etypes to defaults
            res['etypes'] = [QApplication.translate('ComboBox', 'Air'),
                             QApplication.translate('ComboBox', 'Drum'),
                             QApplication.translate('ComboBox', 'Damper'),
                             QApplication.translate('ComboBox', 'Burner'),
                             '--']
            # update
            if fan_event:
                res['etypes'][0] = 'Fan'
            if heater_event:
                res['etypes'][3] = 'Heater'
    res['title'] = Path(file).stem
    return res
