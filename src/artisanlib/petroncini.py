#
# ABOUT
# Petroncini CSV Roast Profile importer for Artisan

from pathlib import Path
import os
import csv
import re
import time as libtime
import logging
from typing import List, Optional, TYPE_CHECKING
from typing import Final  # Python <=3.7

if TYPE_CHECKING:
    from artisanlib.types import ProfileData # pylint: disable=unused-import
from artisanlib.util import fill_gaps, encodeLocal

try:
    from PyQt6.QtCore import QDateTime, QDate, QTime, Qt # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QDateTime, QDate, QTime, Qt # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


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
def extractProfilePetronciniCSV(file,aw):
    res:ProfileData = {}

    res['samplinginterval'] = 1.0

    roastdate:Optional[str]
    roastisodate:Optional[str]
    roasttime:Optional[str]

    # set profile date from the file name if it has the format "yyyy_mm_dd_hh_mm_ss.csv"
    try:
        filename = os.path.basename(file)
        p = re.compile(r'\d{4,4}_\d{1,2}_\d{1,2}_\d{1,2}_\d{1,2}_\d{1,2}.csv')
        if p.match(filename):
            s = filename[:-4] # the extracted date time string
            datetime:QDateTime = QDateTime.fromString(s,'yyyy_MM_dd_HH_mm_ss')
            roastdate = encodeLocal(datetime.date().toString())
            if roastdate is not None:
                res['roastdate'] = roastdate
            roastisodate = encodeLocal(datetime.date().toString(Qt.DateFormat.ISODate))
            if roastisodate is not None:
                res['roastisodate'] = roastisodate
            roasttime = encodeLocal(datetime.time().toString())
            if roasttime is not None:
                res['roasttime'] = roasttime
            res['roastepoch'] = int(datetime.toSecsSinceEpoch())
            res['roasttzoffset'] = libtime.timezone
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)

    with open(file, newline='',encoding='utf-8') as csvFile:
        data = csv.reader(csvFile,delimiter=';')
        #read file header
        next(data) # skip "Export path"
        next(data) # skip path
        header = [i.strip() for i in next(data)]

        roast_date = None
        power = None # holds last processed heater event value
        power_last = None # holds the heater event value before the last one
        power_event = False # set to True if a heater event exists
        specialevents:List[int] = []
        specialeventstype:List[int] = []
        specialeventsvalue:List[float] = []
        specialeventsStrings:List[str] = []
        timex:List[float] = []
        temp1:List[float] = [] # outlet temperature as ET
        temp2:List[float] = [] # bean temperature
        extra1:List[float] = [] # inlet temperature
        extra2:List[float] = [] # burner percentage
        timeindex:List[int] = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actual index used
        i = 0
        for row in data:
            if row == []:
                continue
            i = i + 1
            items = list(zip(header, row))
            item = {}
            for (name, value) in items:
                item[name] = value.strip()
            # take i as time in seconds
            timex.append(i)
            # extract roast_date
            if roast_date is None and 'Year' in item and 'Month' in item and 'Day' in item and 'Hour' in item and 'Minute' in item and 'Second' in item:
                try:
                    date:QDate = QDate(int(item['Year']),int(item['Month']),int(item['Day']))
                    time = QTime(int(item['Hour']),int(item['Minute']),int(item['Second']))
                    roast_date = QDateTime(date,time)
                except Exception:  # pylint: disable=broad-except
                    pass
            #
            if 'Outlet Temperature' in item:
                temp1.append(float(item['Outlet Temperature']))
            else:
                temp1.append(-1)
            if 'Beans Temperature' in item:
                temp2.append(float(item['Beans Temperature'].replace(',','.')))
            else:
                temp2.append(-1)
            # mark CHARGE
            if timeindex[0] <= -1:
                timeindex[0] = i
            # mark DROP
            if timeindex[0] > -1 and i>0:
                timeindex[6] = i-1
            # add ror, power, speed and pressure
            if 'Inlet Temperature' in item:
                extra1.append(float(item['Inlet Temperature']))
            else:
                extra1.append(-1)
            if 'Burner Percentage' in item:
                extra2.append(float(item['Burner Percentage']))
            else:
                extra2.append(-1)

            if 'Burner Percentage' in item:
                try:
                    v = float(item['Burner Percentage'])
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
                except Exception as e:  # pylint: disable=broad-except
                    _log.exception(e)

    res['timex'] = timex
    if aw.qmc.dropDuplicates:
        res['temp1'] = replace_duplicates(temp1)
        res['temp2'] = replace_duplicates(temp2)
    else:
        res['temp1'] = temp1
        res['temp2'] = temp2
    res['timeindex'] = timeindex

    res['extradevices'] = [33]
    res['extratimex'] = [timex[:]]

    res['extraname1'] = ['Burner']
    res['extratemp1'] = [extra2]
    res['extramathexpression1'] = ['']

    res['extraname2'] = ['']
    if aw.qmc.dropDuplicates:
        res['extratemp2'] = [replace_duplicates(extra1)]
    else:
        res['extratemp2'] = [extra1]
    res['extramathexpression2'] = ['']


    # set date
    if roast_date is not None and roast_date.isValid():
        roastdate = encodeLocal(roast_date.date().toString())
        if roastdate is not None:
            res['roastdate'] = roastdate
        roastisodate = encodeLocal(roast_date.date().toString(Qt.DateFormat.ISODate))
        if roastisodate is not None:
            res['roastisodate'] = roastisodate
        roasttime = encodeLocal(roast_date.time().toString())
        if roasttime is not None:
            res['roasttime'] = roasttime
        res['roastepoch'] = int(roast_date.toSecsSinceEpoch())
        res['roasttzoffset'] = libtime.timezone

    if len(specialevents) > 0:
        res['specialevents'] = specialevents
        res['specialeventstype'] = specialeventstype
        res['specialeventsvalue'] = specialeventsvalue
        res['specialeventsStrings'] = specialeventsStrings
        if power_event:
            # first set etypes to defaults
            res['etypes'] = [QApplication.translate('ComboBox', 'Air'),
                             QApplication.translate('ComboBox', 'Drum'),
                             QApplication.translate('ComboBox', 'Damper'),
                             QApplication.translate('ComboBox', 'Burner'),
                             '--']
    res['title'] = Path(file).stem
    return res
