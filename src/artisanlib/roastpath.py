#
# ABOUT
# RoastPATH HTML Roast Profile importer for Artisan

import time as libtime
import dateutil.parser
import requests
from requests_file import FileAdapter # type: ignore # @UnresolvedImport
import re
import json
from lxml import html
import logging
from typing import Final, TypedDict, Optional, List, Callable, TYPE_CHECKING


if TYPE_CHECKING:
    from PyQt6.QtCore import QUrl # pylint: disable=unused-import

try:
    from PyQt6.QtCore import QDateTime, Qt # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QDateTime, Qt # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.util import encodeLocal
from artisanlib.atypes import ProfileData


_log: Final[logging.Logger] = logging.getLogger(__name__)

class RoastPathDataItem(TypedDict, total=False):
    Timestamp: str
#    SecondsAfterStart: int
#    DisplayTime: str
#    DisplayUomId: int
    StandardValue: float
#    DisplayValue: float
#    ReadingTypeId: int
#    IsRateOfRiseReading: bool
#    RoastStageId: int
    EventName: Optional[str]
    Note: float
    NoteTypeId: int

class RoastPathData(TypedDict, total=False):
    btData: List[RoastPathDataItem]
    etData: List[RoastPathDataItem]
    atData: List[RoastPathDataItem]
    eventData: List[RoastPathDataItem]
    rorData: List[RoastPathDataItem]
    noteData: List[RoastPathDataItem]
    fuelData: List[RoastPathDataItem]
    fanData: List[RoastPathDataItem]
    drumData: List[RoastPathDataItem]

# returns a dict containing all profile information contained in the given RoastPATH document pointed by the given QUrl
def extractProfileRoastPathHTML(url:'QUrl',
        _etypesdefault:List[str],
        _alt_etypesdefault:List[str],
        _artisanflavordefaultlabels:List[str],
        eventsExternal2InternalValue:Callable[[int],float]) -> Optional[ProfileData]:
    res:ProfileData = ProfileData() # the interpreted data set
    try:
        sess = requests.Session()
        sess.mount('file://', FileAdapter())
        page = sess.get(url.toString(), timeout=(4, 15), headers={'Accept-Encoding' : 'gzip'})
        tree = html.fromstring(page.content)

        title = ''
        date = tree.xpath('//div[contains(@class, "roast-top")]/*/*[local-name() = "h5"]/text()')
        if isinstance(date, list) and len(date) > 0:
            date_str = str(date[0]).strip().split()
            if len(date_str) > 2:
                dateQt = QDateTime.fromString(date_str[-2]+date_str[-1], 'yyyy-MM-ddhh:mm')
                if dateQt.isValid():
                    rd:Optional[str] = encodeLocal(dateQt.date().toString())
                    if rd is not None:
                        res['roastdate'] = rd
                    rd_iso:Optional[str] = encodeLocal(dateQt.date().toString(Qt.DateFormat.ISODate))
                    if rd_iso is not None:
                        res['roastisodate'] = rd_iso
                    rt:Optional[str] = encodeLocal(dateQt.time().toString())
                    if rt is not None:
                        res['roasttime'] = rt
                    res['roastepoch'] = int(dateQt.toSecsSinceEpoch())
                    res['roasttzoffset'] = libtime.timezone
                title = ''.join(date_str[:-2]).strip()
                if len(title)>0 and title[-1] == '-': # we remove a trailing -
                    title = title[:-1].strip()
            elif len(date_str)>0:
                title = ''.join(date_str)

        coffee = ''
        for m in ['Roasted By','Coffee','Batch Size','Notes','Organization']:
            s:str = f'//*[@class="ml-2" and normalize-space(text())="Details"]/following::table[1]/tbody/tr[*]/td/*[normalize-space(text())="{m}"]/following::td[1]/text()'
            value = tree.xpath(s)
            if isinstance(value, list) and len(value) > 0:
                meta = str(value[0]).strip()
                try:
                    if m == 'Roasted By':
                        res['operator'] = meta
                    elif m == 'Coffee':
                        coffee = meta
                        if title in {'', 'Roast'}:
                            res['title'] = coffee
                    elif m == 'Notes':
                        res['roastingnotes'] = meta
                    elif m == 'Batch Size':
                        v,u = meta.split()
                        res['weight'] = [float(v),0,('Kg' if u.strip() == 'kg' else 'lb')]
                    elif m == 'Organization':
                        res['organization'] = meta
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)

        beans = ''
        for m in ['Nickname','Country','Region','Farm','Varietal','Process']:
            s = f'//*[@class="ml-2" and normalize-space(text())="Greens"]/following::table[1]/tbody/tr/td[count(//table/thead/tr/th[normalize-space(text())="{m}"]/preceding-sibling::th)+1]/text()'
            value = tree.xpath(s)
            if isinstance(value, list) and len(value)>0:
                meta = str(value[0]).strip()
                if meta != '':
                    if beans == '':
                        beans = meta
                    else:
                        beans += ', ' + meta
        if coffee != '' and title in res: # we did not use the "coffee" as title
            beans = coffee if beans == '' else coffee + '\n' + beans
        if beans != '':
            res['beans'] = beans
        if title != '' and 'title' not in res:
            res['title'] = title

        data:RoastPathData = RoastPathData()
        for elem in ['btData', 'etData', 'atData', 'eventData', 'rorData', 'noteData', 'fuelData', 'fanData', 'drumData']:
            page_content = ''
            try:
                page_content = page.content.decode('utf-8')
            except Exception: # pylint: disable=broad-except
                page_content = page.content.decode('latin-1')
            d = re.findall(fr"var {elem} = JSON\.parse\('(.+?)'\);", page_content, re.S)  # @UndefinedVariable
            if d:
                data[elem] = json.loads(d[0]) # type: ignore # generic strings accessors cannot be handled by mypy

        if 'btData' in data and len(data['btData']) > 0 and 'Timestamp' in data['btData'][0]:
            # BT
            bt = data['btData']
            baseTime = (dateutil.parser.parse(bt[0]['Timestamp']).timestamp() if 'Timestamp' in bt[0] else -1)
            res['mode'] = 'C'
            res['timex'] = [dateutil.parser.parse(d['Timestamp']).timestamp() - baseTime if 'Timestamp' in d else -1 for d in bt]
            res['temp2'] = [(d['StandardValue'] if 'StandardValue' in d and d['StandardValue'] != 0 else -1) for d in bt] # we drop 0 values as -1 to have Artisan suppress them!

            # ET
            if 'etData' in data:
                et = data['etData']
                res['temp1'] = [(d['StandardValue'] if 'StandardValue' in d and d['StandardValue'] != 0 else -1) for d in et]
                temp2len = len(res['temp2'])
                res['temp1'] = res['temp1'] + [-1]*(max(0,temp2len-len(res['temp1'])))  # extend if needed
                res['temp1'] = res['temp1'][:temp2len] # truncate
                # now temp1 should be the same length of temp2
            else:
                res['temp1'] = [-1.0]*len(res['temp2'])

            # Events
            timeindex = [-1,0,0,0,0,0,0,0]
            if 'eventData' in data:
                marks = {
                    'Charge' : 0,
                    'Green > Yellow' : 1,
                    'First Crack' : 2,
                    'Second Crack' : 4,
                    'Drop' : 6}
                for dd in data['eventData']:
                    if 'EventName' in dd and dd['EventName'] in marks and 'Timestamp' in dd:
                        tx = dateutil.parser.parse(dd['Timestamp']).timestamp() - baseTime
                        try:
#                            tx_idx = res["timex"].index(tx) # does not cope with dropouts as the next line:
                            tx_idx = next(i for i,item in enumerate(res['timex']) if item >= tx)
                            timeindex[marks[dd['EventName']]] = max(0, tx_idx) # pyrefly: ignore[index-error]
                        except Exception: # pylint: disable=broad-except
                            pass
            res['timeindex'] = timeindex

            # Notes
            noteData = None
            for tag in ['noteData','fuelData','fanData','drumData']:
                if tag in data:
                    if noteData is None:
                        noteData = data[tag] # type: ignore # mypy cannot check generic tags on TypedDicts
                    noteData = noteData + data[tag] # type: ignore # mypy cannot check generic tags on TypedDicts
            if noteData is not None:
                specialevents = []
                specialeventstype = []
                specialeventsvalue = []
                specialeventsStrings = []
                for n in noteData:
                    if 'Timestamp' in n and 'NoteTypeId' in n and 'Note' in n:
                        c = dateutil.parser.parse(n['Timestamp']).timestamp() - baseTime
                        try:
                            timex_idx = None
                            if c in res['timex']:
                                timex_idx = res['timex'].index(c)
                            elif c+1 in res['timex']:
                                timex_idx = res['timex'].index(c+1)
                            if timex_idx is not None:
                                specialevents.append(timex_idx)
                                note_type = n['NoteTypeId']
                                if note_type == 0: # Fuel/Power
                                    specialeventstype.append(3)
                                elif note_type == 1: # Fan
                                    specialeventstype.append(0)
                                elif note_type == 2: # Drum
                                    specialeventstype.append(1)
                                else: # n == 3: # Notes
                                    specialeventstype.append(4)
                                try:
                                    vv:float = float(n['Note'])
                                    specialeventsvalue.append(eventsExternal2InternalValue(round(vv)))
                                except Exception: # pylint: disable=broad-except
                                    specialeventsvalue.append(0)
                                specialeventsStrings.append(n['Note'])
                        except Exception as e: # pylint: disable=broad-except
                            _log.exception(e)
                if len(specialevents) > 0:
                    res['specialevents'] = specialevents
                    res['specialeventstype'] = specialeventstype
                    res['specialeventsvalue'] = specialeventsvalue
                    res['specialeventsStrings'] = specialeventsStrings

            if 'atData' in data or 'rorData' in data:
                res['extradevices'] = []
                res['extratimex'] = []
                res['extratemp1'] = []
                res['extratemp2'] = []
                res['extraname1'] = []
                res['extraname2'] = []
                res['extramathexpression1'] = []
                res['extramathexpression2'] = []
                res['extraLCDvisibility1'] = []
                res['extraLCDvisibility2'] = []
                res['extraCurveVisibility1'] = []
                res['extraCurveVisibility2'] = []
                res['extraDelta1'] = []
                res['extraDelta2'] = []
                res['extraFill1'] = []
                res['extraFill2'] = []
                res['extradevicecolor1'] = []
                res['extradevicecolor2'] = []
                res['extramarkersizes1'] = []
                res['extramarkersizes2'] = []
                res['extramarkers1'] = []
                res['extramarkers2'] = []
                res['extralinewidths1'] = []
                res['extralinewidths2'] = []
                res['extralinestyles1'] = []
                res['extralinestyles2'] = []
                res['extradrawstyles1'] = []
                res['extradrawstyles2'] = []

                # AT
                if 'atData' in data:
                    res['extradevices'].append(25)
                    res['extraname1'].append('AT')
                    res['extraname2'].append('')
                    res['extramathexpression1'].append('')
                    res['extramathexpression2'].append('')
                    res['extraLCDvisibility1'].append(True)
                    res['extraLCDvisibility2'].append(False)
                    res['extraCurveVisibility1'].append(True)
                    res['extraCurveVisibility2'].append(False)
                    res['extraDelta1'].append(False)
                    res['extraDelta2'].append(False)
                    res['extraFill1'].append(False)
                    res['extraFill2'].append(False)
                    res['extradevicecolor1'].append('black')
                    res['extradevicecolor2'].append('black')
                    res['extramarkersizes1'].append(6.0)
                    res['extramarkersizes2'].append(6.0)
                    res['extramarkers1'].append('None')
                    res['extramarkers2'].append('None')
                    res['extralinewidths1'].append(1.0)
                    res['extralinewidths2'].append(1.0)
                    res['extralinestyles1'].append('-')
                    res['extralinestyles2'].append('-')
                    res['extradrawstyles1'].append('default')
                    res['extradrawstyles2'].append('default')
                    at = data['atData']
                    timex = [dateutil.parser.parse(d['Timestamp']).timestamp() - baseTime if 'Timestamp' in d else 0 for d in at]
                    res['extratimex'].append(timex)
                    res['extratemp1'].append([d.get('StandardValue', -1) for d in at])
                    res['extratemp2'].append([-1.0]*len(timex))

                # BT RoR
                if 'rorData' in data:
                    res['extradevices'].append(25)
                    res['extraname1'].append('RoR')
                    res['extraname2'].append('')
                    res['extramathexpression1'].append('')
                    res['extramathexpression2'].append('')
                    res['extraLCDvisibility1'].append(True)
                    res['extraLCDvisibility2'].append(False)
                    res['extraCurveVisibility1'].append(False)
                    res['extraCurveVisibility2'].append(False)
                    res['extraDelta1'].append(True)
                    res['extraDelta2'].append(False)
                    res['extraFill1'].append(False)
                    res['extraFill2'].append(False)
                    res['extradevicecolor1'].append('black')
                    res['extradevicecolor2'].append('black')
                    res['extramarkersizes1'].append(6.0)
                    res['extramarkersizes2'].append(6.0)
                    res['extramarkers1'].append('None')
                    res['extramarkers2'].append('None')
                    res['extralinewidths1'].append(1.0)
                    res['extralinewidths2'].append(1.0)
                    res['extralinestyles1'].append('-')
                    res['extralinestyles2'].append('-')
                    res['extradrawstyles1'].append('default')
                    res['extradrawstyles2'].append('default')
                    ror = data['rorData']
                    timex = [dateutil.parser.parse(d['Timestamp']).timestamp() - baseTime if 'Timestamp' in d else 0 for d in ror]
                    res['extratimex'].append(timex)
                    res['extratemp1'].append([d.get('StandardValue', -1) for d in ror])
                    res['extratemp2'].append([-1.0]*len(timex))

    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)
    return res
