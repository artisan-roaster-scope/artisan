#
# ABOUT
# GIESEN CSV Roast Profile importer for Artisan

from pathlib import Path
import csv
import logging
from typing import List, TYPE_CHECKING
from typing import Final  # Python <=3.7

if TYPE_CHECKING:
    from artisanlib.types import ProfileData # pylint: disable=unused-import

try:
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.util import fill_gaps

_log: Final[logging.Logger] = logging.getLogger(__name__)

def replace_duplicates(data):
    lv = -1
    data_core = []
    for v in data:
        if v == lv:
            data_core.append(-1)
        else:
            data_core.append(v)
            lv = v
    # reconstruct first and last reading
    if len(data)>0:
        data_core[-1] = data[-1]
    return fill_gaps(data_core, interpolate_max=100)

# returns a dict containing all profile information contained in the given IKAWA CSV file
def extractProfileGiesenCSV(file,aw):
    res:ProfileData = {} # the interpreted data set

    res['samplinginterval'] = 1.0

    with open(file, newline='',encoding='utf-8') as csvFile:
        data = csv.reader(csvFile,delimiter=',')
        #read file header
        header = next(data)

        speed = None # holds last processed drum event value
        speed_last = None # holds the drum event value before the last one
        power = None # holds last processed heater event value
        power_last = None # holds the heater event value before the last one
        speed_event = False # set to True if a drum event exists
        power_event = False # set to True if a heater event exists
        specialevents:List[int] = []
        specialeventstype:List[int] = []
        specialeventsvalue:List[float] = []
        specialeventsStrings:List[str] = []
        timex:List[float] = []
        temp1:List[float] = []
        temp2:List[float] = []
        extra1:List[float] = [] # ror
        extra2:List[float] = [] # power
        extra3:List[float] = [] # speed
        extra4:List[float] = [] # pressure
        timeindex:List[int] = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actual index used
        i:int = 0
        for row in data:
            i = i + 1
            items = list(zip(header, row))
            item = {}
            for (name, value) in items:
                item[name] = value.strip()
            # take i as time in seconds
            timex.append(i)
            if 'air' in item:
                temp1.append(float(item['air']))
            else:
                temp1.append(-1)
            if 'beans' in item:
                temp2.append(float(item['beans']))
            else:
                temp2.append(-1)
            # mark CHARGE
            if timeindex[0] <= -1:
                timeindex[0] = i
            # add ror, power, speed and pressure
            if 'ror' in item:
                extra1.append(float(item['ror']))
            else:
                extra1.append(-1)
            if 'power' in item:
                extra2.append(float(item['power']))
            else:
                extra2.append(-1)
            if 'speed' in item:
                extra3.append(float(item['speed']))
            else:
                extra3.append(-1)
            if 'pressure' in item:
                extra4.append(float(item['pressure']))
            else:
                extra4.append(-1)

            if 'speed' in item:
                try:
                    v = float(item['speed'])
                    if v != speed:
                        # speed value changed
                        if v == speed_last:
                            # just a fluctuation, we remove the last added speed value again
                            speed_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 1)
                            del specialeventsvalue[speed_last_idx]
                            del specialevents[speed_last_idx]
                            del specialeventstype[speed_last_idx]
                            del specialeventsStrings[speed_last_idx]
                            speed = speed_last
                            speed_last = None
                        else:
                            speed_last = speed
                            speed = v
                            speed_event = True
                            v = v/10. + 1
                            specialeventsvalue.append(v)
                            specialevents.append(i)
                            specialeventstype.append(1)
                            specialeventsStrings.append(f'{speed:.1f}%')
                    else:
                        speed_last = None
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            if 'power' in item:
                try:
                    v = float(item['power'])
                    if v != power:
                        # power value changed
                        if v == power_last:
                            # just a fluctuation, we remove the last added power value again
                            power_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 3)
                            del specialeventsvalue[power_last_idx]
                            del specialevents[power_last_idx]
                            del specialeventstype[power_last_idx]
                            del specialeventsStrings[power_last_idx]
                            power = power_last
                            power_last = None
                        else:
                            power_last = power
                            power = v
                            power_event = True
                            v = v/10. + 1
                            specialeventsvalue.append(v)
                            specialevents.append(i)
                            specialeventstype.append(3)
                            specialeventsStrings.append(f'{power:.0f}%')
                    else:
                        power_last = None
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)

    res['timex'] = timex
    if aw.qmc.dropDuplicates:
        res['temp1'] = replace_duplicates(temp1)
        res['temp2'] = replace_duplicates(temp2)
    else:
        res['temp1'] = temp1
        res['temp2'] = temp2
    res['timeindex'] = timeindex

    res['extradevices'] = [25,25]
    res['extratimex'] = [timex[:],timex[:]]

    res['extraname1'] = ['ror','speed']
    res['extratemp1'] = [extra1,extra3]
    res['extramathexpression1'] = ['','']

    res['extraname2'] = ['power','pressure']
    res['extratemp2'] = [extra2,extra4]
    res['extramathexpression2'] = ['','']

    if len(specialevents) > 0:
        res['specialevents'] = specialevents
        res['specialeventstype'] = specialeventstype
        res['specialeventsvalue'] = specialeventsvalue
        res['specialeventsStrings'] = specialeventsStrings
        if power_event or speed_event:
            # first set etypes to defaults
            etypes:List[str] = [QApplication.translate('ComboBox', 'Air'),
                             QApplication.translate('ComboBox', 'Drum'),
                             QApplication.translate('ComboBox', 'Damper'),
                             QApplication.translate('ComboBox', 'Burner'),
                             '--']
            # update
            if speed_event:
                etypes[0] = 'Speed'
            if power_event:
                etypes[3] = 'Power'
            res['etypes'] = etypes
    res['title'] = Path(file).stem
    return res
