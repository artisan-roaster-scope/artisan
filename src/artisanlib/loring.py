#
# ABOUT
# Loring CSV Roast Profile importer for Artisan

from pathlib import Path
import time as libtime
import csv
import logging
from typing import Final, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    from artisanlib.types import ProfileData # pylint: disable=unused-import

try:
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtCore import QDateTime, Qt # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtCore import QDateTime, Qt # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.util import replace_duplicates, fromFtoCstrict, RoRfromFtoCstrict, encodeLocal

_log: Final[logging.Logger] = logging.getLogger(__name__)

# returns a dict containing all profile information contained in the given IKAWA CSV file
def extractProfileLoringCSV(file:str, aw:'ApplicationWindow') -> 'ProfileData':
    res:'ProfileData' = {} # the interpreted data set

    with open(file, newline='',encoding='utf-8') as csvFile:
        data = csv.reader(csvFile,delimiter=',')
        #read file header
        header = next(data)

        power = None # holds last processed heater event value
        power_last = None # holds the heater event value before the last one
        specialevents:List[int] = []
        specialeventstype:List[int] = []
        specialeventsvalue:List[float] = []
        specialeventsStrings:List[str] = []
        timex:List[float] = []
        temp1:List[float] = []
        temp2:List[float] = []
        extra1:List[float] = [] # burner
        extra2:List[float] = [] # inlet
        extra3:List[float] = [] # stack
        extra4:List[float] = [] # ror
        timeindex:List[int] = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actual index used

        power_event:bool = False

        start_datetime:Optional[QDateTime] = None
        last_sampling:Optional[float] = None
        sampling_interval:float = 6
        roasting:int = 0

        mode = 'C' # by default we assume temperature data in degree Celsius

        i = 0
        for row in data:
            items = list(zip(header, row))
            item = {}
            for (name, value) in items:
                item[name] = value.strip()

            try:
                if 'Time' in item and 'RoastTimeSeconds' in item and 'RoastingOnOff' in item and item['RoastingOnOff'] != '':

                    #time = int(item['RoastTimeSeconds']) # seems to be imprecise and does not correspond exactly to the 6s interval given by 'Time'

                    datetime:QDateTime = QDateTime.fromString(item['Time'], 'M/d/yyyy h:mm:ss AP')

                    if start_datetime is None:
                        start_datetime = datetime
                        time:float = 0
                        roastdate:Optional[str] = encodeLocal(start_datetime.date().toString())
                        if roastdate is not None:
                            res['roastdate'] = roastdate
                        roastisodate:Optional[str] = encodeLocal(start_datetime.date().toString(Qt.DateFormat.ISODate))
                        if roastisodate is not None:
                            res['roastisodate'] = roastisodate
                        roasttime:Optional[str] = encodeLocal(start_datetime.time().toString())
                        if roasttime is not None:
                            res['roasttime'] = roasttime
                        res['roastepoch'] = int(start_datetime.toSecsSinceEpoch())
                        res['roasttzoffset'] = libtime.timezone
                    else:
                        time = start_datetime.msecsTo(datetime) / 1000
                    timex.append(time)
                    if last_sampling is None:
                        last_sampling = time
                    else:
                        sampling_interval = ((sampling_interval * (i)) + (time - last_sampling)) / i+1
                        last_sampling = time

                    if 'RoastingOnOff' in item:
                        try:
                            roastingOnOff = int(item['RoastingOnOff']) # 1 = On, 0 = Off
                            if roasting == 0 and roastingOnOff == 1:
                                timeindex[0] = i # mark CHARGE
                            elif roasting == 1 and roastingOnOff == 0:
                                timeindex[6] = i # mark DROP
                            roasting = roastingOnOff
                        except Exception: # pylint: disable=broad-except
                            pass

                    # set DRY END
                    if timeindex[1] == 0 and 'ColorChangeOnOff' in item:
                        try:
                            colorchange = int(item['ColorChangeOnOff'])
                            if colorchange == 1:
                                timeindex[1] = i
                        except Exception: # pylint: disable=broad-except
                            pass
                    # set FCs
                    if timeindex[2] == 0 and 'FirstCrackOnOff' in item:
                        try:
                            firstcrack = int(item['FirstCrackOnOff'])
                            if firstcrack == 1:
                                timeindex[2] = i
                        except Exception: # pylint: disable=broad-except
                            pass
                    # set FCe (not sure this is signalled that way)
                    if timeindex[2] != 0 and timeindex[3] == 0 and 'FirstCrackOnOff' in item:
                        try:
                            firstcrack = int(item['FirstCrackOnOff'])
                            if firstcrack == 0:
                                timeindex[3] = i
                        except Exception: # pylint: disable=broad-except
                            pass
                    # set SCs
                    if timeindex[4] == 0 and 'SecondCrackOnOff' in item:
                        try:
                            sndcrack = int(item['SecondCrackOnOff'])
                            if sndcrack == 1:
                                timeindex[4] = i
                        except Exception: # pylint: disable=broad-except
                            pass
                    # set FCe (not sure this is signalled that way)
                    if timeindex[4] != 0 and timeindex[5] == 0 and 'SecondCrackOnOff' in item:
                        try:
                            sndcrack = int(item['SecondCrackOnOff'])
                            if sndcrack == 0:
                                timeindex[5] = i
                        except Exception: # pylint: disable=broad-except
                            pass

                    if 'DegreesCelciusOnOff' in item:
                        if item['DegreesCelciusOnOff'] == '0':
                            mode = 'F'
                        else:
                            mode = 'C'

                    if 'ReturnAirTemperature' in item and item['ReturnAirTemperature'] != '':
                        ET = float(item['ReturnAirTemperature'])/10 # °C x 10
                        if mode == 'F':
                            ET = fromFtoCstrict(ET)
                    else:
                        ET = -1
                    temp1.append(ET)

                    if 'BeanTemperature' in item and item['BeanTemperature'] != '':
                        BT = float(item['BeanTemperature'])/10 # °C x 10
                        if mode == 'F':
                            BT = fromFtoCstrict(BT)
                    else:
                        BT = -1
                    temp2.append(BT)

                    if 'BurnerPercentage' in item and item['BurnerPercentage'] != '':
                        X1 = float(item['BurnerPercentage'])/100 # 0-100% x 100

                        try:
                            v = X1
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
                                    specialeventsStrings.append(f'{X1:.1f}%')
                            else:
                                power_last = None
                        except Exception as e: # pylint: disable=broad-except
                            _log.exception(e)
                    else:
                        X1 = -1
                    extra1.append(X1)

                    if 'InletAirTemperature' in item and item['InletAirTemperature'] != '':
                        X2 = float(item['InletAirTemperature'])/10 # °C x 10
                        if mode == 'F':
                            X2 = fromFtoCstrict(X2)
                    else:
                        X2 = -1
                    extra2.append(X2)

                    if 'StackTemperature' in item and item['StackTemperature'] != '':
                        X3 = float(item['StackTemperature'])/10 # °C x 10
                        if mode == 'F':
                            X3 = fromFtoCstrict(X3)
                    else:
                        X3 = -1
                    extra3.append(X3)

                    if 'BeanTemperatureRateOfRise' in item and item['BeanTemperatureRateOfRise'] != '':
                        X4 = float(item['BeanTemperatureRateOfRise'])/10 # °C x 10
                        if mode == 'F':
                            X4 = RoRfromFtoCstrict(X4)
                    else:
                        X4 = -1
                    extra4.append(X4)


                    #item['CurveTemperatureBaselineOrProfile'] # °C x 10 # most likely the BT background profile or template; ignored for now
                    #item['EndPointTemperature'] # °C x 10 # ???
                    #item['Reserved']
                    #item['RoastMode_1_2_3'] # 1 Manual, 2 Burner, 3 Profile

            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
            i = i + 1

    res['samplinginterval'] = int(round(sampling_interval))

    res['timex'] = timex
    if aw.qmc.dropDuplicates:
        res['temp1'] = replace_duplicates(temp1)
        res['temp2'] = replace_duplicates(temp2)
    else:
        res['temp1'] = temp1
        res['temp2'] = temp2
    res['timeindex'] = timeindex

    res['extradevices'] = [33, 55]
    res['extratimex'] = [timex[:],timex[:]]

    res['extraname1'] = ['{3}','Stack']
    if aw.qmc.dropDuplicates:
        res['extratemp1'] = [replace_duplicates(extra1), replace_duplicates(extra3)]
    else:
        res['extratemp1'] = [extra1, extra3]
    res['extramathexpression1'] = ['','']

    res['extraname2'] = ['Inlet','RoR']
    if aw.qmc.dropDuplicates:
        res['extratemp2'] = [replace_duplicates(extra2), replace_duplicates(extra4)]
    else:
        res['extratemp2'] = [extra2, extra4]
    res['extramathexpression2'] = ['','']

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
