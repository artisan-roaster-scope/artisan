#
# ABOUT
# RoastLog Roast Profile importer for Artisan

import time as libtime
import dateutil.parser
import requests
from requests_file import FileAdapter  # @UnresolvedImport
import re
from lxml import html
import logging
try:
    from typing import Final
except ImportError:
    # for Python 3.7:
    from typing_extensions import Final

try:
    #ylint: disable = E, W, R, C
    from PyQt6.QtCore import QDateTime, Qt # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #ylint: disable = E, W, R, C
    from PyQt5.QtCore import QDateTime, Qt # @UnusedImport @Reimport  @UnresolvedImport


from artisanlib.util import encodeLocal, stringtoseconds


_log: Final = logging.getLogger(__name__)

# returns a dict containing all profile information contained in the given RoastLog document pointed by the given QUrl
def extractProfileRoastLog(url,_):
    res = {} # the interpreted data set
    try:
        s = requests.Session()
        s.mount('file://', FileAdapter())
        page = s.get(url.toString(), timeout=(4, 15), headers={'Accept-Encoding' : 'gzip'})
        tree = html.fromstring(page.content)

        title = ''
        title_elements = tree.xpath('//h2[contains(@id,"page-title")]/text()')
        if len(title_elements)>0:
            title = title_elements[0].strip()

        tag_values = {}
        for tag in ['Roastable:', 'Starting mass:', 'Ending mass:', 'Roasted on:', 'Roasted by:', 'Roaster:', 'Roast level:', 'Roast Notes:']:
            tag_elements = tree.xpath(f'//td[contains(@class,"text-rt") and normalize-space(text())="{tag}"]/following::td[1]/text()')
            if len(tag_elements)>0:
                tag_values[tag] = '\n'.join([e.strip() for e in tag_elements])
        # {'Roastable:': '2003000 Diablo FTO BULK', 'Starting mass:': '140.00 lb', 'Ending mass:': '116.80 lb', 'Roasted on:': 'Thu, Jun 6th, 2019 11:11 PM', 'Roasted by:': 'Ryan@caffeladro.com', 'Roaster:': 'Diedrich CR-70'}

        if 'Roasted on:' in tag_values:
            try:
                dt = dateutil.parser.parse(tag_values['Roasted on:'])
                dateQt = QDateTime.fromSecsSinceEpoch(int(round(dt.timestamp())))
                if dateQt.isValid():
                    res['roastdate'] = encodeLocal(dateQt.date().toString())
                    res['roastisodate'] = encodeLocal(dateQt.date().toString(Qt.DateFormat.ISODate))
                    res['roasttime'] = encodeLocal(dateQt.time().toString())
                    res['roastepoch'] = int(dateQt.toSecsSinceEpoch())
                    res['roasttzoffset'] = libtime.timezone
            except Exception: # pylint: disable=broad-except
                pass

        w_in = 0
        w_out = 0
        u = 'lb'
        if 'Starting mass:' in tag_values:
            w_in,u = tag_values['Starting mass:'].strip().split(' ')
        if 'Ending mass:' in tag_values:
            w_out,u = tag_values['Ending mass:'].strip().split(' ')
        res['weight'] = [float(w_in),float(w_out),('Kg' if u.strip() == 'kg' else 'lb')]

        if 'Roasted by:' in tag_values:
            res['operator'] = tag_values['Roasted by:']
        if 'Roaster:' in tag_values:
            res['roastertype'] = tag_values['Roaster:']
        if 'Roast level:' in tag_values:
            try:
                c = int(round(float(tag_values['Roast level:'])))
                res['ground_color'] = c
            except Exception: # pylint: disable=broad-except
                pass
        if 'Roast Notes:' in tag_values:
            res['roastingnotes'] = tag_values['Roast Notes:']

        if title == '' and 'Roastable:' in tag_values:
            title = tag_values['Roastable:']
        if title != '':
            res['title'] = title


        # if DROP temp > 300 => F else C

        source_elements = tree.xpath('//script[contains(@id,"source")]/text()')
        if len(source_elements)>0:
            source_element = source_elements[0].strip()

            pattern = re.compile(r"\"rid=(\d+)\"")
            d = pattern.findall(source_element)
            if len(d)>0:
                rid = d[0]

                url = f'https://roastlog.com/roasts/profiles/?rid={rid}'
                headers = {
                    'X-Requested-With' : 'XMLHttpRequest',
                    'Accept' : 'application/json',
                    'Accept-Encoding' : 'gzip'}
                response = requests.get(url, timeout=(4, 15), headers=headers)
                data_json = response.json()

                timeindex = [-1,0,0,0,0,0,0,0]
                specialevents = []
                specialeventstype = []
                specialeventsvalue = []
                specialeventsStrings = []

                if 'line_plots' in data_json:
                    mode = 'F'
                    timex = []
                    temp1,temp2,temp3,temp4 = [],[],[],[]
                    temp3_label = 'TC3'
                    temp4_label = 'TC4'
#                    temp1ror = []
                    for lp in data_json['line_plots']:
                        if 'channel' in lp and 'data' in lp:
                            if lp['channel'] == 0: # BT
                                data = lp['data']
                                timex = [d[0]/1000 for d in data]
                                temp1 = [d[1] for d in data]
                            elif lp['channel'] == 1: # ET
                                temp2 = [d[1] for d in lp['data']]
                            elif lp['channel'] == 2: # XT1
                                temp3 = [d[1] for d in lp['data']]
                                if 'label' in lp:
                                    temp3_label = lp['label']
                            elif lp['channel'] == 3: # XT2
                                temp4 = [d[1] for d in lp['data']]
                                if 'label' in lp:
                                    temp4_label = lp['label']
#                            elif lp["channel"] == 4: # BT RoR
#                                temp1ror = [d[1] for d in lp["data"]]
                    res['timex'] = timex
                    if len(timex) == len(temp1):
                        res['temp2'] = temp1
                    else:
                        res['temp2'] = [-1]*len(timex)
                    if len(timex) == len(temp2):
                        res['temp1'] = temp2
                    else:
                        res['temp1'] = [-1]*len(timex)
                    if len(temp3) == len(timex) or len(temp4) == len(timex):
                        temp3_visibility = True
                        temp4_visibility = True
                        # add one (virtual) extra device
                        res['extradevices'] = [25]
                        res['extratimex'] = [timex]
                        if len(temp3) == len(timex):
                            res['extratemp1'] = [temp3]
                        else:
                            res['extratemp1'] = [[-1]*len(timex)]
                            temp3_visibility = False
                        if len(temp4) == len(timex):
                            res['extratemp2'] = [temp4]
                        else:
                            res['extratemp2'] = [[-1]*len(timex)]
                            temp4_visibility = False
                        res['extraname1'] = [temp3_label]
                        res['extraname2'] = [temp4_label]
                        res['extramathexpression1'] = ['']
                        res['extramathexpression2'] = ['']
                        res['extraLCDvisibility1'] = [temp3_visibility]
                        res['extraLCDvisibility2'] = [temp4_visibility]
                        res['extraCurveVisibility1'] = [temp3_visibility]
                        res['extraCurveVisibility2'] = [temp4_visibility]
                        res['extraDelta1'] = [False]
                        res['extraDelta2'] = [False]
                        res['extraFill1'] = [False]
                        res['extraFill2'] = [False]
                        res['extradevicecolor1'] = ['black']
                        res['extradevicecolor2'] = ['black']
                        res['extramarkersizes1'] = [6.0]
                        res['extramarkersizes2'] = [6.0]
                        res['extramarkers1'] = [None]
                        res['extramarkers2'] = [None]
                        res['extralinewidths1'] = [1.0]
                        res['extralinewidths2'] = [1.0]
                        res['extralinestyles1'] = ['-']
                        res['extralinestyles2'] = ['-']
                        res['extradrawstyles1'] = ['default']
                        res['extradrawstyles2'] = ['default']

                timex_events = {
                    'Intro temperature': 0,
                    'yellowing': 1,
                    'Yellow': 1,
                    'DRY': 1,
                    'Dry': 1,
                    'dry': 1,
                    'Dry End': 1,
                    'Start 1st crack': 2,
                    'START 1st': 2,
                    'End 1st crack': 3,
                    'Start 2nd crack': 4,
                    'End 2nd crack': 5,
                    'Drop temperature': 6
                }
                if 'table_events' in data_json:
                    for te in data_json['table_events']:
                        if 'label' in te and 'time' in te:
                            if te['label'] in timex_events:
                                try:
                                    timex_idx = res['timex'].index(stringtoseconds(te['time']))
                                    timeindex[timex_events[te['label']]] = max(0,timex_idx)
                                except Exception: # pylint: disable=broad-except
                                    pass
                            else:
                                try:
                                    timex_idx = res['timex'].index(stringtoseconds(te['time']))
                                    specialeventsStrings.append(te['label'])
                                    specialevents.append(timex_idx)
                                    specialeventstype.append(4)
                                    specialeventsvalue.append(0)
                                except Exception: # pylint: disable=broad-except
                                    pass
                res['timeindex'] = timeindex

                mode = 'F'
                if timeindex[6] != 0 and len(temp1) > timeindex[6] and temp1[timeindex[6]] < 250:
                    mode = 'C'
                if timeindex[0] > -1 and len(temp1) > timeindex[0] and temp1[timeindex[0]] < 250:
                    mode = 'C'
                res['mode'] = mode

                if len(specialevents) > 0:
                    res['specialevents'] = specialevents
                    res['specialeventstype'] = specialeventstype
                    res['specialeventsvalue'] = specialeventsvalue
                    res['specialeventsStrings'] = specialeventsStrings
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)
    return res
