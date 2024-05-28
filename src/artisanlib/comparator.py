#
# ABOUT
# Artisan Roast Comparator

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2023

import sys
import platform
import numpy
from matplotlib import ticker, transforms
from matplotlib import rcParams
import logging
from typing import Final, TypedDict, Sequence, List, Union, Tuple, Optional, Literal, Callable, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from artisanlib.types import ProfileData # pylint: disable=unused-import
    from matplotlib.lines import Line2D # pylint: disable=unused-import
    from matplotlib.backend_bases import PickEvent # pylint: disable=unused-import
    from matplotlib.legend import Legend # pylint: disable=unused-import
    from PyQt6.QtWidgets import QLayoutItem, QLayout, QScrollBar # pylint: disable=unused-import
    from PyQt6.QtGui import QStandardItem, QKeyEvent, QDropEvent, QDragEnterEvent, QCloseEvent # pylint: disable=unused-import
    from PyQt6.QtCore import QMimeData # pylint: disable=unused-import

from artisanlib.util import (deltaLabelUTF8, decodeLocal, decodeLocalStrict, stringfromseconds, fromFtoCstrict,
        fromCtoFstrict, fill_gaps, float2float)
from artisanlib.suppress_errors import suppress_stdout_stderr
from artisanlib.dialogs import ArtisanDialog
from artisanlib.widgets import MyQComboBox
from artisanlib.qcheckcombobox import CheckComboBox

with suppress_stdout_stderr():
    from matplotlib import colormaps

try:
    from PyQt6.QtCore import (Qt, pyqtSignal, pyqtSlot, QSettings, QFile, QTextStream, QUrl,  # @UnusedImport @Reimport  @UnresolvedImport
        QFileInfo, QDate, QTime, QDateTime) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import (QColor, QDesktopServices, QStandardItemModel) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QTableWidget, QPushButton,  # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QSizePolicy, QHBoxLayout, QVBoxLayout, QHeaderView, QTableWidgetItem, QCheckBox) # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import (Qt, pyqtSignal, pyqtSlot, QSettings, QFile, QTextStream, QUrl, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QFileInfo, QDate, QTime, QDateTime) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import (QColor, QDesktopServices, QStandardItemModel) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QTableWidget, QPushButton, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
        QComboBox, QSizePolicy, QHBoxLayout, QVBoxLayout, QHeaderView, QTableWidgetItem, QCheckBox) # @UnusedImport @Reimport  @UnresolvedImport


_log: Final[logging.Logger] = logging.getLogger(__name__)

class Metadata(TypedDict, total=False):
    roastdate: QDateTime
    roastoftheday: str
    beans: str
    weight: str
    moisture_greens: float
    ambientTemp: str
    ambient_humidity: str
    ambient_pressure: str
    weight_loss: str
    ground_color: str
    AUC: str
    roastingnotes: str
    cuppingnotes: str


class RoastProfile:
    __slots__ = ['aw', 'visible', 'aligned', 'active', 'color', 'gray', 'label', 'title', 'curve_visibilities', 'event_visibility', 'zorder',
        'zorder_offsets', 'alpha', 'alpha_dim_factor', 'timeoffset', 'max_DeltaET', 'max_DeltaBT',
        'startTimeIdx', 'endTimeIdx', 'min_time', 'max_time', 'filepath', 'extraname1', 'extraname2', 'extra1_curve_visibilities', 'extra2_curve_visibilities',
        'timeindex', 'timex', 'temp1', 'temp2', 'extratimex', 'extratemp1', 'extratemp2', 'extrastemp1', 'extrastemp2',
        'E1', 'E2', 'E3', 'E4', 'stemp1', 'stemp2', 'delta1', 'delta2', 'etypes', 'events1', 'extraDelta1', 'extraDelta2',
        'events2', 'events_timex', 'l_temp1', 'l_temp2', 'l_extratemp1', 'l_extratemp2', 'l_delta1', 'l_delta2',
        'l_mainEvents1', 'l_mainEvents2', 'l_events1', 'l_events2', 'l_events3', 'l_events4',
        'ambientTemp', 'metadata', 'specialevents', 'specialeventstype', 'specialeventsvalue', 'TP']

    # NOTE: filepath/filename can also be a URL string
    def __init__(self, aw:'ApplicationWindow', profile:'ProfileData', filepath:str, color: Tuple[float, float, float, float]) -> None:
        self.aw = aw
        # state:
        self.visible:bool = True
        self.aligned:bool = True # if the profile could not be aligned it is not drawn
        self.active:bool = True # if selected or all are unselected; active profiles are drawn in color, inactive profiles in gray
        self.color:Tuple[float, float, float, float] = color
        hslf:Tuple[Optional[float], Optional[float], Optional[float], Optional[float]] = QColor.fromRgbF(*color).getHslF()
        self.gray:Tuple[float, float, float, float]
        ch:Optional[float] = hslf[0]
        cl:Optional[float] = hslf[2]
        ca:Optional[float] = hslf[3]
        if ch is not None and cl is not None and ca is not None:
            g0 = QColor.fromHslF(ch,0,cl,ca)
        else:
            g0 = QColor.fromHslF(0.5,0,0.5,0.5) # saturation set to 0
        self.gray = (
                (0 if g0.redF() is None else g0.redF()),
                (0 if g0.greenF() is None else g0.greenF()),
                (0 if g0.blueF() is None else g0.blueF()),
                (0 if g0.alphaF() is None else g0.alphaF()))
        self.label:str = ''
        self.title:str = ''
        #
        self.curve_visibilities:List[bool] = [True]*5 # visibility of ET, BT, DeltaET, DeltaBT, events curves
        self.extra1_curve_visibilities:List[bool] = [True]*self.aw.nLCDS # extra1 curve visibilities
        self.extra2_curve_visibilities:List[bool] = [True]*self.aw.nLCDS # extra2 curve visibilities
        self.event_visibility:int = 0 # either 0, or the number of the event line that is to be shown
        #
        self.zorder = 0 # artists with higher zorders are drawn on top of others (0-9)
        # zorder offset is added per curve type: events1, events2, BT, ET, DeltaBT, DeltaET, custom events, extra curves (only one of events1/events2 active!)
        self.zorder_offsets = [100,80,100,80,60,30,10,0]
        #
        self.alpha:List[float] = [1, 0.7, 0.5, 0.4, 0.6, 0.5] # color alpha per curve: BT, ET, DeltaBT, DeltaET, custom events, extra curves (alpha of main events taken from the corresponding curve)
        self.alpha_dim_factor:float = 0.3 # factor to be multiplied to current alpha values for inactive curves
        #
        self.timeoffset:float = 0 # in seconds
        self.max_DeltaET:float = 1
        self.max_DeltaBT:float = 1
        self.startTimeIdx:int = 0 # start index: either index of CHARGE if set or 0, set by recompute()
        self.endTimeIdx:int = 0   # end index: either index of DROP or last index, set by recompute()
        self.min_time:float = 0 # the minimum display time of this profile after alignment
        self.max_time:float = 0 # the maximum display time of this profile after alignment
        # profile data:
        self.filepath = filepath
        self.timeindex:List[int] = [-1,0,0,0,0,0,0,0]
        self.timex:List[float] = []
        self.temp1:List[float] = [] # holds raw data with gaps filled on loading
        self.temp2:List[float] = [] # holds raw data with gaps filled on loading
        # extra device data
        self.extratimex:List[List[float]] = []
        self.extratemp1:List[List[float]] = [] # holds raw data with gaps filled on loading
        self.extratemp2:List[List[float]] = [] # holds raw data with gaps filled on loading
        self.extraname1:List[str] = []
        self.extraname2:List[str] = []
        self.extraDelta1: List[bool] = []
        self.extraDelta2: List[bool] = []
        # events as list of timeidx/value pairs per event type
        self.E1:List[Tuple[float, float]] = []
        self.E2:List[Tuple[float, float]] = []
        self.E3:List[Tuple[float, float]] = []
        self.E4:List[Tuple[float, float]] = []
        # (re-)computed data:
        self.stemp1:Optional[Sequence[Optional[float]]] = None # smoothed from temp1 and cut to visible data only on recompute
        self.stemp2:Optional[Sequence[Optional[float]]] = None
        self.extrastemp1:List[Optional[Sequence[Optional[float]]]] = [] # smoothed from temp1 and cut to visible data only on recompute
        self.extrastemp2:List[Optional[Sequence[Optional[float]]]] = []
        self.delta1:Optional[Sequence[Optional[float]]] = None # based on smoothed stemp1, but not yet cut data as computed in recompute, and RoR smoothing applied, then cut to visible data
        self.delta2:Optional[Sequence[Optional[float]]] = None
        self.events1:Optional[Sequence[Optional[float]]] = None # ET temperatures of main events [CHARGE, DRY, FCs, FCe, SCs, SCe, DROP], None if not set
        self.events2:Optional[Sequence[Optional[float]]] = None # BT temperatures of main events [CHARGE, DRY, FCs, FCe, SCs, SCe, DROP], None if not set
        self.events_timex:Optional[Sequence[Optional[float]]] = None # roast times of main events [CHARGE, DRY, FCs, FCe, SCs, SCe, DROP] in seconds, None if not set
        self.specialevents:Optional[List[int]] = None
        self.specialeventstype:Optional[List[int]] = None
        self.specialeventsvalue:Optional[List[float]] = None
        #
        self.etypes:List[str] = self.aw.qmc.etypes[:-1]
        if 'etypes' in profile:
            self.etypes = [decodeLocalStrict(et) for et in profile['etypes'][:4]]
            if 'default_etypes' in profile:
                default_etypes = profile['default_etypes']
                for i, _ in enumerate(self.etypes):
                    if default_etypes[i]:
                        self.etypes[i] = self.aw.qmc.etypesdefault[i]
        #
        # fill profile data:
        if 'timex' in profile:
            self.timex = profile['timex']
        if 'temp1' in profile:
            self.temp1 = (fill_gaps(profile['temp1']) if self.aw.qmc.interpolateDropsflag else profile['temp1'])
        if 'temp2' in profile:
            self.temp2 = (fill_gaps(profile['temp2']) if self.aw.qmc.interpolateDropsflag else profile['temp2'])
        if 'timeindex' in profile:
            for i,ti in enumerate(profile['timeindex']):
                if i < len(self.timeindex):
                    self.timeindex[i] = ti
        if 'extradevices' in profile and isinstance(profile['extradevices'], list):
            l = len(profile['extradevices'])
            if ('extratimex' in profile and 'extratemp1' in profile and 'extratemp2' in profile and
                'extraname1' in profile and 'extraname2' in profile and 'extraDelta1' in profile and
                'extraDelta2' in profile):
                xtimex = profile['extratimex'][:l]
                xtemp1 = profile['extratemp1'][:l]
                xtemp2 = profile['extratemp2'][:l]
                xname1 = profile['extraname1'][:l]
                xname2 = profile['extraname2'][:l]
                delta1 = profile['extraDelta1'][:l]
                delta2 = profile['extraDelta2'][:l]
                if (isinstance(xtimex, list) and isinstance(xtemp1, list) and isinstance(xtemp2, list) and
                        isinstance(xname1, list) and isinstance(xname2, list) and
                        isinstance(delta1, list) and isinstance(delta2, list) and
                        len(xtimex) == len(xtemp1) == len(xtemp2) == len(xname1) == len(xname2) == len(delta1) == len(delta2) == l):
                    # ensure that all extra timex and temp lists are of the same length as self.timex
                    for i, timex in enumerate(xtimex):
                        if len(timex) == len(self.timex):
                            self.extratimex.append(timex)
                        else:
                            self.extratimex.append(self.timex)
                        if len(xtemp1[i]) == len(self.timex):
                            self.extratemp1.append(fill_gaps(xtemp1[i]) if self.aw.qmc.interpolateDropsflag else xtemp1[i])
                        else:
                            self.extratemp1.append([-1.]*len(self.timex))
                        if len(xtemp2[i]) == len(self.timex):
                            self.extratemp2.append(fill_gaps(xtemp2[i]) if self.aw.qmc.interpolateDropsflag else xtemp2[i])
                        else:
                            self.extratemp2.append([-1.]*len(self.timex))
                    self.extraname1 = [decodeLocalStrict(n).format(self.etypes[0],self.etypes[1],self.etypes[2],self.etypes[3]) for n in xname1] # we apply event name substitutions
                    self.extraname2 = [decodeLocalStrict(n).format(self.etypes[0],self.etypes[1],self.etypes[2],self.etypes[3]) for n in xname2] # we apply event name substitutions
                    self.extraDelta1 = delta1
                    self.extraDelta2 = delta2
        # temperature conversion
        m = str(profile['mode']) if 'mode' in profile else self.aw.qmc.mode
        self.ambientTemp: float
        if 'ambientTemp' in profile:
            self.ambientTemp = profile['ambientTemp']
        elif m == 'C':
            self.ambientTemp = 20
        else:
            self.ambientTemp = 68
        if self.aw.qmc.mode == 'C' and m == 'F':
            self.temp1 = [fromFtoCstrict(t) for t in self.temp1]
            self.temp2 = [fromFtoCstrict(t) for t in self.temp2]
            self.extratemp1 = [[fromFtoCstrict(t) for t in tl] for tl in self.extratemp1]
            self.extratemp2 = [[fromFtoCstrict(t) for t in tl] for tl in self.extratemp2]
            self.ambientTemp = fromFtoCstrict(self.ambientTemp)
        elif self.aw.qmc.mode == 'F' and m == 'C':
            self.temp1 = [fromCtoFstrict(t) for t in self.temp1]
            self.temp2 = [fromCtoFstrict(t) for t in self.temp2]
            self.extratemp1 = [[fromCtoFstrict(t) for t in tl] for tl in self.extratemp1]
            self.extratemp2 = [[fromCtoFstrict(t) for t in tl] for tl in self.extratemp2]
            self.ambientTemp = fromCtoFstrict(self.ambientTemp)
        if 'title' in profile:
            title:Optional[str] = decodeLocal(profile['title'])
            if title is not None:
                self.title = title
        if 'roastbatchnr' in profile and profile['roastbatchnr'] != 0:
            try:
                batchprefix:Optional[str] = decodeLocal(profile['roastbatchprefix']) # pyright:ignore[reportTypedDictNotRequiredAccess]
                if batchprefix is not None:
                    self.label = batchprefix + str(int(profile['roastbatchnr']))[:10] # pyright:ignore[reportTypedDictNotRequiredAccess]
            except Exception: # pylint: disable=broad-except
                pass
        if 'specialevents' in profile:
            self.specialevents = profile['specialevents']
        if 'specialeventstype' in profile:
            self.specialeventstype = profile['specialeventstype']
        if 'specialeventsvalue' in profile:
            self.specialeventsvalue = profile['specialeventsvalue']
        # artists
        self.l_temp1:Optional[Line2D] = None
        self.l_temp2:Optional[Line2D] = None
        self.l_extratemp1:List[Optional[Line2D]] = [None]*len(self.extratimex)
        self.l_extratemp2:List[Optional[Line2D]] = [None]*len(self.extratimex)
        self.l_delta1:Optional[Line2D] = None
        self.l_delta2:Optional[Line2D] = None
        self.l_mainEvents1:Optional[Line2D] = None
        self.l_mainEvents2:Optional[Line2D] = None
        self.l_events1:Optional[Line2D] = None
        self.l_events2:Optional[Line2D] = None
        self.l_events3:Optional[Line2D] = None
        self.l_events4:Optional[Line2D] = None
#        # delta clipping paths
#        self.l_delta1_clipping = None
#        self.l_delta2_clipping = None
        # add metadata
        self.metadata:Metadata = {}
        if 'roastdate' in profile:
            try:
                roastdate_str:Optional[str] = decodeLocal(profile['roastdate'])
                if roastdate_str is not None:
                    date = QDate.fromString(roastdate_str)
                    if not date.isValid():
                        date = QDate.currentDate()
                else:
                    date = QDate.currentDate()
                if 'roasttime' in profile:
                    try:
                        time_str:Optional[str] = decodeLocal(profile['roasttime'])
                        if time_str is not None:
                            time = QTime.fromString(time_str)
                            self.metadata['roastdate'] = QDateTime(date,time)
                        else:
                            self.metadata['roastdate'] = QDateTime(date, QTime())
                    except Exception: # pylint: disable=broad-except
                        self.metadata['roastdate'] = QDateTime(date, QTime())
                else:
                    self.metadata['roastdate'] = QDateTime(date, QTime())
            except Exception: # pylint: disable=broad-except
                pass
        # the new dates have the locale independent isodate format:
        if 'roastisodate' in profile:
            try:
                isodate_str:Optional[str] = decodeLocal(profile['roastisodate'])
                if isodate_str is not None:
                    date = QDate.fromString(isodate_str,Qt.DateFormat.ISODate)
                    if 'roasttime' in profile:
                        try:
                            roasttime_str:Optional[str] = decodeLocal(profile['roasttime'])
                            if roasttime_str is not None:
                                time = QTime.fromString(roasttime_str)
                                self.metadata['roastdate'] = QDateTime(date,time)
                            else:
                                self.metadata['roastdate'] = QDateTime(date, QTime())
                        except Exception: # pylint: disable=broad-except
                            self.metadata['roastdate'] = QDateTime(date, QTime())
                    else:
                        self.metadata['roastdate'] = QDateTime(date, QTime())
            except Exception: # pylint: disable=broad-except
                pass
        if 'roastepoch' in profile:
            try:
                self.metadata['roastdate'] = QDateTime.fromSecsSinceEpoch(profile['roastepoch'])
            except Exception: # pylint: disable=broad-except
                pass
        if 'roastbatchpos' in profile:
            self.metadata['roastoftheday'] = f'{self.aw.qmc.roastOfTheDay(profile["roastbatchpos"])}'
        if 'beans' in profile:
            beans_str = decodeLocal(profile['beans'])
            if beans_str is not None:
                self.metadata['beans'] = beans_str
        if 'weight' in profile and profile['weight'][0] != 0.0:
            w:float = float(profile['weight'][0])
            weight_unit:Optional[str] = decodeLocal(profile['weight'][2])
            if weight_unit is not None:
                if weight_unit != 'g':
                    w = float2float(w,1)
                self.metadata['weight'] = str(w).rstrip('0').rstrip('.') + weight_unit
        if 'moisture_greens' in profile and profile['moisture_greens'] != 0.0:
            self.metadata['moisture_greens'] = profile['moisture_greens']
        if 'ambientTemp' in profile:
            self.metadata['ambientTemp'] = f'{float2float(self.ambientTemp):g}{self.aw.qmc.mode}'
        if 'ambient_humidity' in profile:
            self.metadata['ambient_humidity'] = f"{float2float(profile['ambient_humidity']):g}%"
        if 'ambient_pressure' in profile:
            self.metadata['ambient_pressure'] = f"{float2float(profile['ambient_pressure']):g}hPa"
        if 'computed' in profile and profile['computed'] is not None and 'weight_loss' in profile['computed'] and \
                profile['computed']['weight_loss'] is not None:
            self.metadata['weight_loss'] = f"-{profile['computed']['weight_loss']:.1f}%"
        if 'ground_color' in profile:
            self.metadata['ground_color'] = f"#{profile['ground_color']}"
        if 'computed' in profile and profile['computed'] is not None and 'AUC' in profile['computed'] and profile['computed']['AUC'] is not None and \
                profile['computed']['AUC'] != 0:
            self.metadata['AUC'] = f"{profile['computed']['AUC']}C*min"
        if 'roastingnotes' in profile:
            roasting_notes:Optional[str] = decodeLocal(profile['roastingnotes'])
            if roasting_notes is not None:
                self.metadata['roastingnotes'] = roasting_notes
        if 'cuppingnotes' in profile:
            cupping_notes:Optional[str] = decodeLocal(profile['cuppingnotes'])
            if cupping_notes is not None:
                self.metadata['cuppingnotes'] = cupping_notes
        # TP time in time since DROP
        if 'computed' in profile and profile['computed'] is not None and 'TP_time' in profile['computed']:
            self.TP = profile['computed']['TP_time']
        else:
            self.TP = 0
        #
        self.recompute()
        self.draw()
        self.updateAlpha()

    # applies current smoothing values to temperature and delta curves
    def recompute(self) -> None:
        decay_smoothing_p = not self.aw.qmc.optimalSmoothing
        # we resample the temperatures to regular interval timestamps
        if self.timex is not None and self.timex and len(self.timex)>1:
            timex_lin = numpy.linspace(self.timex[0],self.timex[-1],len(self.timex))
        else:
            timex_lin = None
        self.stemp1 = list(self.aw.qmc.smooth_list(self.timex,self.temp1,window_len=self.aw.qmc.curvefilter,decay_smoothing=decay_smoothing_p,a_lin=timex_lin))
        self.stemp2 = list(self.aw.qmc.smooth_list(self.timex,self.temp2,window_len=self.aw.qmc.curvefilter,decay_smoothing=decay_smoothing_p,a_lin=timex_lin))
        # we resample the temperatures of extra device curves to regular interval timestamps
        self.extrastemp1 = []
        self.extrastemp2 = []
        for i, timex in enumerate(self.extratimex):
            if timex is not None and timex and len(timex)>1:
                timex_lin = numpy.linspace(timex[0],timex[-1],len(timex))
            else:
                timex_lin = None
            self.extrastemp1.append(list(self.aw.qmc.smooth_list(timex,self.extratemp1[i],window_len=self.aw.qmc.curvefilter,decay_smoothing=decay_smoothing_p,a_lin=timex_lin)))
            self.extrastemp2.append(list(self.aw.qmc.smooth_list(timex,self.extratemp2[i],window_len=self.aw.qmc.curvefilter,decay_smoothing=decay_smoothing_p,a_lin=timex_lin)))
        # recompute deltas
        cf = self.aw.qmc.curvefilter*2 # we smooth twice as heavy for PID/RoR calculation as for normal curve smoothing
        t1 = self.aw.qmc.smooth_list(self.timex,self.temp1,window_len=cf,decay_smoothing=decay_smoothing_p,a_lin=timex_lin)
        t2 = self.aw.qmc.smooth_list(self.timex,self.temp2,window_len=cf,decay_smoothing=decay_smoothing_p,a_lin=timex_lin)
        if self.timeindex[0]>-1:
            RoR_start = min(self.timeindex[0]+10, len(self.timex)-1)
        else:
            RoR_start = -1
        if self.aw.qmc.compareBBP and not self.aw.qmc.compareRoast:
            # no delta curve if BBP only
            self.delta1 = [None]*len(self.timex)
            self.delta2 = [None]*len(self.timex)
        else:
            self.delta1, self.delta2 = self.aw.qmc.recomputeDeltas(self.timex,RoR_start,self.timeindex[6],t1,t2,optimalSmoothing=not decay_smoothing_p,timex_lin=timex_lin)
        # calculate start/end index
        self.startTimeIdx = (self.timeindex[0] if self.timeindex[0] != -1 else 0)
        self.endTimeIdx = (self.timeindex[6] if self.timeindex[6] != 0 else len(self.timex)-1)
        if self.stemp1 is not None:
            self.stemp1 = [None if (not self.aw.qmc.compareBBP and i < self.startTimeIdx) or (not self.aw.qmc.compareRoast and i>self.startTimeIdx) or i > self.endTimeIdx else t for i,t in enumerate(self.stemp1)]
        if self.stemp2 is not None:
            self.stemp2 = [None if (not self.aw.qmc.compareBBP and i < self.startTimeIdx) or (not self.aw.qmc.compareRoast and i>self.startTimeIdx) or i > self.endTimeIdx else t for i,t in enumerate(self.stemp2)]
        for i, _ in enumerate(self.extratimex):
            extrastemp1_i = self.extrastemp1[i]
            extrastemp2_i = self.extrastemp2[i]
            if extrastemp1_i is not None:
                self.extrastemp1[i] = [None if (not self.aw.qmc.compareBBP and i < self.startTimeIdx) or (not self.aw.qmc.compareRoast and i>self.startTimeIdx) or i > self.endTimeIdx else t for i,t in enumerate(extrastemp1_i)]
            if extrastemp2_i is not None:
                self.extrastemp2[i] = [None if (not self.aw.qmc.compareBBP and i < self.startTimeIdx) or (not self.aw.qmc.compareRoast and i>self.startTimeIdx) or i > self.endTimeIdx else t for i,t in enumerate(extrastemp2_i)]
        # calculate max deltas
        self.max_DeltaET = 1
        if self.delta1 is not None and len(self.delta1) > 0:
            try:
                self.max_DeltaET = max(filter(None,self.delta1))
            except Exception: # pylint: disable=broad-except
                pass
        self.max_DeltaBT = 1
        if self.delta2 is not None and len(self.delta2) > 0:
            try:
                self.max_DeltaBT = max(filter(None,self.delta2))
            except Exception: # pylint: disable=broad-except
                pass
        self.events1 = []
        self.events2 = []
        self.events_timex = []
        if self.stemp1 is not None and self.stemp2 is not None:
            for ti in self.timeindex[:-1]:
                temp1 = self.stemp1[ti]
                temp2 = self.stemp2[ti]
                if ((len(self.events1) == 0 and ti != -1) or ti > 0):
                    self.events1.append(temp1)
                    self.events2.append(temp2)
                    self.events_timex.append(self.timex[ti])
                else:
                    self.events1.append(None)
                    self.events2.append(None)
                    self.events_timex.append(None)
        # update special events
        if self.specialevents is not None and self.specialeventstype is not None and self.specialeventsvalue is not None:
            # calculated bot and top corresponding to the temperature positions of the event values 0 and 100
            if self.aw.qmc.clampEvents:
                top = 100
                bot = 0
            else:
                if self.aw.qmc.step100temp is None:
                    top = self.aw.qmc.phases[0]
                else:
                    top = self.aw.qmc.step100temp
                bot = self.aw.qmc.ylimit_min
            value_offset = bot
            value_factor = (top-bot)/100
            self.E1 = []
            self.E2 = []
            self.E3 = []
            self.E4 = []

            last_E1, last_E2, last_E3, last_E4 = None, None, None, None
            for i,e in enumerate(self.specialevents):
                try:
                    etime = self.timex[e]
                    etype = self.specialeventstype[i]
                    evalue:float = self.aw.qmc.eventsInternal2ExternalValue(self.specialeventsvalue[i]) * value_factor + value_offset
                    # remember last event value per type before CHARGE
                    if (not self.aw.qmc.compareBBP and self.timeindex[0] != -1 and e < self.timeindex[0]):
                        if etype == 0:
                            last_E1 = evalue
                        elif etype == 1:
                            last_E2 = evalue
                        elif etype == 2:
                            last_E3 = evalue
                        elif etype == 3:
                            last_E4 = evalue
                    # only draw events between CHARGE and DRY
                    if (self.aw.qmc.compareRoast and (self.aw.qmc.compareBBP  or self.timeindex[0] == -1 or e >= self.timeindex[0]) and (self.timeindex[6] == 0 or e <= self.timeindex[6])) or (not self.aw.qmc.compareRoast and self.aw.qmc.compareBBP and (self.timeindex[0] == -1 or e <= self.timeindex[0])):
                        if etype == 0:
                            if last_E1 is not None and last_E1 != evalue:
                                # add event value @CHARGE
                                self.E1.append((self.timex[self.timeindex[0]],last_E1))
                                last_E1 = None
                            self.E1.append((etime,evalue))
                        elif etype == 1:
                            if last_E2 is not None and last_E2 != evalue:
                                # add event value @CHARGE
                                self.E2.append((self.timex[self.timeindex[0]],last_E2))
                                last_E2 = None
                            self.E2.append((etime,evalue))
                        elif etype == 2:
                            if last_E3 is not None and last_E3 != evalue:
                                # add event value @CHARGE
                                self.E3.append((self.timex[self.timeindex[0]],last_E3))
                                last_E3 = None
                            self.E3.append((etime,evalue))
                        elif etype == 3:
                            if last_E4 is not None and last_E4 != evalue:
                                # add event value @CHARGE
                                self.E4.append((self.timex[self.timeindex[0]],last_E4))
                                last_E4 = None
                            self.E4.append((etime,evalue))
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
            # add a last event at DROP/END to extend the lines to the end of roast
            if not self.aw.qmc.compareRoast and self.aw.qmc.compareBBP:
                # BBP-only mode
                end = (self.timex[-1] if self.timeindex[0] == -1 else self.timex[self.timeindex[0]])
            else:
                end = (self.timex[-1] if self.timeindex[6] == 0 else self.timex[self.timeindex[6]])
            if self.E1:
                self.E1.append((end,self.E1[-1][1]))
            if self.E2:
                self.E2.append((end,self.E2[-1][1]))
            if self.E3:
                self.E3.append((end,self.E3[-1][1]))
            if self.E4:
                self.E4.append((end,self.E4[-1][1]))

    def firstTime(self) -> float:
        try:
            return self.timex[0]
        except Exception: # pylint: disable=broad-except
            return 0

    def startTime(self) -> float:
        try:
            return self.timex[self.startTimeIdx]
        except Exception: # pylint: disable=broad-except
            return 0

    def endTime(self) -> float:
        try:
            return self.timex[self.endTimeIdx]
        except Exception: # pylint: disable=broad-except
            return self.timex[-1]

    def setVisible(self, b:bool) -> None:
        self.visible = b
        self.updateVisibilities()

    def setVisibilities(self, visibilities:List[bool], extra1_visibilitites:List[bool], extra2_visibilitites:List[bool], event_visibility:int) -> None:
        self.curve_visibilities = visibilities
        self.extra1_curve_visibilities = extra1_visibilitites
        self.extra2_curve_visibilities = extra2_visibilitites
        self.event_visibility = event_visibility
        self.updateVisibilities()

    def updateVisibilities(self) -> None:
        visibilities = self.curve_visibilities
        profile_visible = self.visible and self.aligned
        # main curves
        for i, ll in enumerate([self.l_temp1,self.l_temp2,self.l_delta1,self.l_delta2]):
            if ll is not None:
                ll.set_visible(profile_visible and visibilities[i])
        # extra curves
        for i, ll in enumerate(self.l_extratemp1):
            if ll is not None:
                ll.set_visible(profile_visible and self.extra1_curve_visibilities[i])
        for i, ll in enumerate(self.l_extratemp2):
            if ll is not None:
                ll.set_visible(profile_visible and self.extra2_curve_visibilities[i])
        # events
        for i, ll in enumerate([self.l_events1,self.l_events2,self.l_events3,self.l_events4]):
            if ll is not None:
                ll.set_visible(profile_visible and i+1 == self.event_visibility)
        #
        if self.l_mainEvents1 is not None:
            self.l_mainEvents1.set_visible(False)
        if self.l_mainEvents2 is not None:
            self.l_mainEvents2.set_visible(False)
        if profile_visible and visibilities[4]:
            if self.aw.qmc.swaplcds:
                # prefer the ET over BT
                if visibilities[0]: # ET visible
                    if self.l_mainEvents1 is not None:
                        self.l_mainEvents1.set_visible(True) # place the main events on the ET
                    if self.l_mainEvents2 is not None:
                        self.l_mainEvents2.set_visible(False)
                elif visibilities[1]: # BT visible
                    if self.l_mainEvents2 is not None:
                        self.l_mainEvents2.set_visible(True) # place the main events on the BT
                    if self.l_mainEvents1 is not None:
                        self.l_mainEvents1.set_visible(False)
            # prefer the BT over ET
            elif visibilities[1]: # BT visible
                if self.l_mainEvents2 is not None:
                    self.l_mainEvents2.set_visible(True) # place the main events on the BT
                if self.l_mainEvents1 is not None:
                    self.l_mainEvents1.set_visible(False)
            elif visibilities[0]: # ET visible
                if self.l_mainEvents1 is not None:
                    self.l_mainEvents1.set_visible(True) # place the main events on the ET
                if self.l_mainEvents2 is not None:
                    self.l_mainEvents2.set_visible(False)

    def setZorder(self, zorder:int) -> None:
        self.zorder = zorder
        if self.aw.qmc.swaplcds:
            lines = [self.l_mainEvents1,self.l_mainEvents2,self.l_temp1,self.l_temp2,self.l_delta2,self.l_delta1]
        else:
            lines = [self.l_mainEvents2,self.l_mainEvents1,self.l_temp2,self.l_temp1,self.l_delta2,self.l_delta1]
        if self.aw.qmc.swapdeltalcds:
            lines[4] = self.l_delta1
            lines[5] = self.l_delta2
        for i, ll in enumerate(lines):
            if ll is not None:
                ll.set_zorder(self.zorder + self.zorder_offsets[i])
        for ll in [self.l_events1,self.l_events2,self.l_events3,self.l_events4]:
            if ll is not None:
                ll.set_zorder(self.zorder + self.zorder_offsets[6])
        for ll in self.l_extratemp1 + self.l_extratemp2:
            if ll is not None:
                ll.set_zorder(self.zorder + self.zorder_offsets[7])

    # swap alpha values based on self.aw.qmc.swaplcds and self.aw.qmc.swapdeltalcds settings
    def updateAlpha(self) -> None:
        alpha = self.alpha[:]
        if self.aw.qmc.swaplcds:
            alpha[0] = self.alpha[1]
            alpha[1] = self.alpha[0]
        if self.aw.qmc.swapdeltalcds:
            alpha[2] = self.alpha[3]
            alpha[3] = self.alpha[2]
        for ll, a in zip( # type:ignore[unused-ignore] # pright: error: "object*" is not iterable
                [
                    self.l_mainEvents2, self.l_temp2,
                    self.l_mainEvents1, self.l_temp1,
                    self.l_delta2, self.l_delta1,
                    self.l_events1, self.l_events2, self.l_events3, self.l_events4],
                [
                    alpha[0],alpha[0],
                    alpha[1],alpha[1],
                    alpha[2],alpha[3],
                    alpha[4],alpha[4],alpha[4],alpha[4]
                ]):
            if ll is not None:
                ll.set_alpha(a if self.active else a*self.alpha_dim_factor)
        for ll in self.l_extratemp1 + self.l_extratemp2:
            if ll is not None:
                ll.set_alpha(alpha[5] if self.active else alpha[5]*self.alpha_dim_factor)

    def setActive(self, b:bool) -> None:
        self.active = b
        self.updateAlpha()
        for ll in [self.l_temp1,self.l_temp2,self.l_delta1,self.l_delta2,self.l_mainEvents1,self.l_mainEvents2,self.l_events1,self.l_events2,self.l_events3,self.l_events4]:
            if ll is not None:
                if self.active:
                    ll.set_color(self.color)
                else:
                    ll.set_color(self.gray)
        for ll in self.l_extratemp1 + self.l_extratemp2:
            if ll is not None:
                if self.active:
                    ll.set_color(self.color)
                else:
                    ll.set_color(self.gray)

    def setTimeoffset(self, offset:float) -> None:
        self.timeoffset = offset
        tempTrans = self.getTempTrans()
        for ll in [
            # shifting the temperature curves does not work for some curves that hold many points resulting some at the end being not displayed
            # thus we update the xdata explicitly below
            #self.l_temp1,self.l_temp2,
            self.l_mainEvents1,self.l_mainEvents2,self.l_events1,self.l_events2,self.l_events3,self.l_events4]:
            if ll is not None:
                ll.set_transform(tempTrans)

        tempTransZero = self.getTempTrans(0)
        deltaTransZero = self.getDeltaTrans(offset=0)

        for ll in [self.l_temp1,self.l_temp2]:
            if ll is not None:
                ll.set_transform(tempTransZero) # we reset the transformation to avoid a double shift along the timeaxis
                ll.set_xdata(numpy.array([x-offset if x is not None else None for x in self.timex]))

        # shifting the extra curves
        for i, (ll1, ll2) in enumerate(zip(self.l_extratemp1,self.l_extratemp2)):
            if ll1 is not None:
                ll1.set_transform(deltaTransZero if self.extraDelta1[i] else tempTransZero) # we reset the transformation to avoid a double shift along the timeaxis
                ll1.set_xdata(numpy.array([x-offset if x is not None else None for x in self.extratimex[i]]))
            if ll2 is not None:
                ll2.set_transform(deltaTransZero if self.extraDelta2[i] else tempTransZero) # we reset the transformation to avoid a double shift along the timeaxis
                ll2.set_xdata(numpy.array([x-offset if x is not None else None for x in self.extratimex[i]]))

        # shifting the delta curves does not work for some curves that hold many points resulting some at the end being not displayed
        # thus we update the xdata explicitly below
#        deltaTrans = self.getDeltaTrans()
#        for l in [self.l_delta1,self.l_delta2]:
#            if l is not None:
#                l.set_transform(deltaTrans)
        for ll in [self.l_delta1,self.l_delta2]:
            if ll is not None:
                ll.set_transform(deltaTransZero) # we reset the transformation to avoid a double shift along the timeaxis
                ll.set_xdata(numpy.array([x-offset if x is not None else None for x in self.timex]))

#        # update RoR clippings
#        self.l_delta1_clipping.set_transform(self.getDeltaTrans())
#        self.l_delta1.set_clip_path(self.l_delta1_clipping)
#        self.l_delta2_clipping.set_transform(self.getDeltaTrans())
#        self.l_delta2.set_clip_path(self.l_delta2_clipping)

    # returns the time transformation for the temperature curves
    def getTempTrans(self, offset:Optional[float] = None) -> Optional[transforms.Transform]:
        if self.aw.qmc.ax:
            if offset is None:
                offset = self.timeoffset
            # transformation pipelines are processed from left to right so in "A + B" first transformation A then transformation B is applied (on the result of A)
            # an artist transformation is supplied with data in data coordinates and should return data in display coordinates
            # ax.transData : transforms from data to display coordinates
            # transforms.Affine2D().translate() : applies its transformation
            return transforms.Affine2D().translate(-offset,0) + self.aw.qmc.ax.transData # pylint: disable=invalid-unary-operand-type
        return None

    # returns the time transformation for the delta curves
    def getDeltaTrans(self, offset:Optional[float] = None) -> transforms.Transform:
        if self.aw.qmc.delta_ax is not None:
            if offset is None:
                offset = self.timeoffset
            return transforms.Affine2D().translate(-offset,0) + self.aw.qmc.delta_ax.transData # pylint: disable=invalid-unary-operand-type
        return transforms.Affine2D()

    def undraw(self) -> None:
        for ll in [self.l_temp1,self.l_temp2,self.l_delta1,self.l_delta2,self.l_mainEvents1,self.l_mainEvents2,
                self.l_events1,self.l_events2,self.l_events3,self.l_events4]:
            try:
                if ll is not None:
                    ll.remove()
            except Exception: # pylint: disable=broad-except
                pass
        self.l_temp1 = None
        self.l_temp2 = None
        self.l_delta1 = None
        self.l_delta2 = None
        self.l_mainEvents1 = None
        self.l_mainEvents2 = None
        self.l_events1 = None
        self.l_events2 = None
        self.l_events3 = None
        self.l_events4 = None
        for i, (ll1, ll2) in enumerate(zip(self.l_extratemp1,self.l_extratemp2)):
            try:
                if ll1 is not None:
                    ll1.remove()
            except Exception: # pylint: disable=broad-except
                pass
            try:
                if ll2 is not None:
                    ll2.remove()
            except Exception: # pylint: disable=broad-except
                pass
            self.l_extratemp1[i] = None
            self.l_extratemp2[i] = None

    def draw(self) -> None:
        for i in range(self.aw.nLCDS):
            self.drawExtras(i)
        self.drawEvents1()
        self.drawEvents2()
        self.drawEvents3()
        self.drawEvents4()
        self.drawDeltaET()
        self.drawDeltaBT()
        self.drawET()
        self.drawBT()
        self.drawMainEvents2()
        self.drawMainEvents1()

    def drawExtras(self, i:int) -> None:
        if self.aw.qmc.ax is not None and len(self.extratimex)> i and self.extratimex[i]:
            c = (self.color if self.active else self.gray)
            alpha = (self.alpha[0] if self.active else self.alpha[0]*self.alpha_dim_factor)
            if self.extrastemp1[i] is not None:
                extramarkersizes1 = (self.aw.qmc.extramarkersizes1[i] if len(self.aw.qmc.extramarkersizes1)>i else self.aw.qmc.markersize_default)
                extramarkers1 = (self.aw.qmc.extramarkers1[i] if len(self.aw.qmc.extramarkers1)>i else self.aw.qmc.marker_default)
                extralinewidths1 = (self.aw.qmc.extralinewidths1[i] if len(self.aw.qmc.extralinewidths1)>i else self.aw.qmc.extra_linewidth_default)
                extralinestyles1 = (self.aw.qmc.extralinestyles1[i] if len(self.aw.qmc.extralinestyles1)>i else self.aw.qmc.linestyle_default)
                extradrawstyles1 = (self.aw.qmc.extradrawstyles1[i] if len(self.aw.qmc.extradrawstyles1)>i else self.aw.qmc.drawstyle_default)
                l_temp1, = self.aw.qmc.ax.plot(self.extratimex[i],numpy.array(self.extrastemp1[i]),transform=(self.getDeltaTrans() if self.extraDelta1[i] else self.getTempTrans()),
                    markersize=extramarkersizes1,marker=extramarkers1,visible=(self.visible and self.aligned),
                    sketch_params=None,
                    path_effects=self.aw.qmc.line_path_effects(self.aw.qmc.glow, self.aw.qmc.patheffects, self.aw.light_background_p, extralinewidths1, alpha=alpha),
                    linewidth=extralinewidths1,
                    linestyle=extralinestyles1,
                    drawstyle=extradrawstyles1,
                    alpha=alpha,
                    color=c,
                    label=f'{self.label} {self.aw.arabicReshape(self.extraname1[i])}')
                self.l_extratemp1[i] = l_temp1
            if self.extrastemp2[i] is not None:
                extramarkersizes2 = (self.aw.qmc.extramarkersizes2[i] if len(self.aw.qmc.extramarkersizes2)>i else self.aw.qmc.markersize_default)
                extramarkers2 = (self.aw.qmc.extramarkers2[i] if len(self.aw.qmc.extramarkers2)>i else self.aw.qmc.marker_default)
                extralinewidths2 = (self.aw.qmc.extralinewidths2[i] if len(self.aw.qmc.extralinewidths2)>i else self.aw.qmc.extra_linewidth_default)
                extralinestyles2 = (self.aw.qmc.extralinestyles2[i] if len(self.aw.qmc.extralinestyles2)>i else self.aw.qmc.linestyle_default)
                extradrawstyles2 = (self.aw.qmc.extradrawstyles2[i] if len(self.aw.qmc.extradrawstyles2)>i else self.aw.qmc.drawstyle_default)
                l_temp2, = self.aw.qmc.ax.plot(self.extratimex[i],numpy.array(self.extrastemp2[i]),transform=(self.getDeltaTrans() if self.extraDelta2[i] else self.getTempTrans()),
                    markersize=extramarkersizes2,marker=extramarkers2,visible=(self.visible and self.aligned),
                    sketch_params=None,
                    path_effects=self.aw.qmc.line_path_effects(self.aw.qmc.glow, self.aw.qmc.patheffects, self.aw.light_background_p, extralinewidths2, alpha=alpha),
                    linewidth=extralinewidths2,
                    linestyle=extralinestyles2,
                    drawstyle=extradrawstyles2,
                    alpha=alpha,
                    color=c,
                    label=f'{self.label} {self.aw.arabicReshape(self.extraname2[i])}')
                self.l_extratemp2[i] = l_temp2

    def drawBT(self) -> None:
        if self.aw.qmc.ax is not None and self.timex is not None and self.stemp2 is not None:
            alpha = (self.alpha[0] if self.active else self.alpha[1]*self.alpha_dim_factor)
            self.l_temp2, = self.aw.qmc.ax.plot(self.timex,numpy.array(self.stemp2),transform=self.getTempTrans(),markersize=self.aw.qmc.BTmarkersize,marker=self.aw.qmc.BTmarker,visible=(self.visible and self.aligned),
                sketch_params=None,
                path_effects=self.aw.qmc.line_path_effects(self.aw.qmc.glow, self.aw.qmc.patheffects, self.aw.light_background_p, self.aw.qmc.BTlinewidth, alpha=alpha),
                linewidth=self.aw.qmc.BTlinewidth,
                linestyle=self.aw.qmc.BTlinestyle,
                drawstyle=self.aw.qmc.BTdrawstyle,
                alpha=alpha,
                color=(self.color if self.active else self.gray),
                label=f'{self.label} {self.aw.arabicReshape(self.aw.BTname)}')

    def drawET(self) -> None:
        if self.aw.qmc.ax is not None and self.timex is not None and self.stemp1 is not None:
            alpha = (self.alpha[1] if self.active else self.alpha[1]*self.alpha_dim_factor)
            self.l_temp1, = self.aw.qmc.ax.plot(self.timex,numpy.array(self.stemp1),transform=self.getTempTrans(),markersize=self.aw.qmc.ETmarkersize,marker=self.aw.qmc.ETmarker,visible=(self.visible and self.aligned),
                sketch_params=None,
                path_effects=self.aw.qmc.line_path_effects(self.aw.qmc.glow, self.aw.qmc.patheffects, self.aw.light_background_p, self.aw.qmc.ETlinewidth, alpha=alpha),
                linewidth=self.aw.qmc.ETlinewidth,
                linestyle=self.aw.qmc.ETlinestyle,
                drawstyle=self.aw.qmc.ETdrawstyle,
                alpha=alpha,
                color=(self.color if self.active else self.gray),
                label=f'{self.label} {self.aw.arabicReshape(self.aw.ETname)}')

    def drawDeltaBT(self) -> None:
        if self.aw.qmc.ax is not None and self.timex is not None and self.delta2 is not None:
            alpha = (self.alpha[2] if self.active else self.alpha[1]*self.alpha_dim_factor)
            # we clip the RoR such that values below 0 are not displayed
#            self.l_delta2_clipping = patches.Rectangle((0,0),self.timex[self.endTimeIdx],self.max_DeltaBT, transform=self.getDeltaTrans())
            self.l_delta2, = self.aw.qmc.ax.plot(self.timex, numpy.array(self.delta2),transform=self.getDeltaTrans(),markersize=self.aw.qmc.BTdeltamarkersize,marker=self.aw.qmc.BTdeltamarker,visible=(self.visible and self.aligned),
                sketch_params=None,
                path_effects=self.aw.qmc.line_path_effects(self.aw.qmc.glow, self.aw.qmc.patheffects, self.aw.light_background_p, self.aw.qmc.BTdeltalinewidth, alpha=alpha),
                linewidth=self.aw.qmc.BTdeltalinewidth,
                linestyle=self.aw.qmc.BTdeltalinestyle,
                drawstyle=self.aw.qmc.BTdeltadrawstyle,
                alpha=alpha,
#                clip_path=self.l_delta2_clipping,clip_on=True,
                color=(self.color if self.active else self.gray),
                label=f"{self.label} {self.aw.arabicReshape(deltaLabelUTF8 + QApplication.translate('Label', 'BT'))}")

    def drawDeltaET(self) -> None:
        if self.aw.qmc.ax is not None and self.timex is not None and self.delta1 is not None:
            alpha = (self.alpha[3] if self.active else self.alpha[3]*self.alpha_dim_factor)
            # we clip the RoR such that values below 0 are not displayed
#            self.l_delta1_clipping = patches.Rectangle((0,0),self.timex[self.endTimeIdx],self.max_DeltaET, transform=self.getDeltaTrans())
            self.l_delta1, = self.aw.qmc.ax.plot(self.timex, numpy.array(self.delta1),transform=self.getDeltaTrans(),markersize=self.aw.qmc.ETdeltamarkersize,marker=self.aw.qmc.ETdeltamarker,visible=(self.visible and self.aligned),
                sketch_params=None,
                path_effects=self.aw.qmc.line_path_effects(self.aw.qmc.glow, self.aw.qmc.patheffects, self.aw.light_background_p, self.aw.qmc.ETdeltalinewidth, alpha=alpha),
                linewidth=self.aw.qmc.ETdeltalinewidth,
                linestyle=self.aw.qmc.ETdeltalinestyle,
                drawstyle=self.aw.qmc.ETdeltadrawstyle,
                alpha=alpha,
#                clip_path=self.l_delta1_clipping,clip_on=True,
                color=(self.color if self.active else self.gray),
                label=f"{self.label} {self.aw.arabicReshape(deltaLabelUTF8 + QApplication.translate('Label', 'ET'))}")

    def drawMainEvents1(self) -> None:
        if self.aw.qmc.ax is not None and self.events_timex is not None and self.events1 is not None:
            alpha = (self.alpha[1] if self.active else self.alpha[1]*self.alpha_dim_factor)
            self.l_mainEvents1, = self.aw.qmc.ax.plot(numpy.array(self.events_timex),numpy.array(self.events1),transform=self.getTempTrans(),
                markersize=self.aw.qmc.ETlinewidth + 3,marker='o',visible=(self.visible and self.aligned),
                sketch_params=None,
                path_effects=self.aw.qmc.line_path_effects(self.aw.qmc.glow, self.aw.qmc.patheffects, self.aw.light_background_p, self.aw.qmc.ETlinewidth, alpha=alpha),
                linewidth=0,linestyle='',
                alpha=alpha,
                color=(self.color if self.active else self.gray),
#                picker=5, # deprecated in MPL 3.3.x
                picker=True,
                pickradius=5,
                label=f"{self.label} {self.aw.arabicReshape(QApplication.translate('Label', 'Events'))}")
            if self.aw.qmc.graphstyle == 1 and self.l_mainEvents1 is not None:
                self.l_mainEvents1.set_sketch_params(1,700,12)

    def drawMainEvents2(self) -> None:
        if self.aw.qmc.ax is not None and self.events_timex is not None and self.events1 is not None:
            alpha = (self.alpha[0] if self.active else self.alpha[0]*self.alpha_dim_factor)
            self.l_mainEvents2, = self.aw.qmc.ax.plot(numpy.array(self.events_timex),numpy.array(self.events2),transform=self.getTempTrans(),
                markersize=self.aw.qmc.BTlinewidth + 3,marker='o',visible=(self.visible and self.aligned),
                sketch_params=None,
                path_effects=self.aw.qmc.line_path_effects(self.aw.qmc.glow, self.aw.qmc.patheffects, self.aw.light_background_p, self.aw.qmc.BTlinewidth, alpha=alpha),
                linewidth=0,linestyle='',
                alpha=alpha,
                color=(self.color if self.active else self.gray),
#                picker=5, # deprecated in MPL 3.3.x
                picker=True,
                pickradius=5,
                label=f"{self.label} {self.aw.arabicReshape(QApplication.translate('Label', 'Events'))}")
            if self.aw.qmc.graphstyle == 1 and self.l_mainEvents2 is not None:
                self.l_mainEvents2.set_sketch_params(4,800,20)

    # draw event lines n in [0,..,3]
    # returns line
    def drawEvents(self, events:List[Tuple[float, float]], n:int) -> Optional['Line2D']:
        if self.aw.qmc.ax is not None:
            if events:
                timex,values = zip(*events)
            else:
                timex,values = (),()
            line, = self.aw.qmc.ax.plot(list(timex), list(values), color=(self.color if self.active else self.gray),
                    linestyle='-',drawstyle='steps-post',linewidth = self.aw.qmc.Evaluelinethickness[n],
                    alpha = (self.alpha[4] if self.active else self.alpha[4]*self.alpha_dim_factor),
                    label = self.aw.qmc.etypesf(n))
            return line
        return None

    def drawEvents1(self) -> None:
        if self.E1 is not None:
            self.l_events1 = self.drawEvents(self.E1, 0)

    def drawEvents2(self) -> None:
        if self.E2 is not None:
            self.l_events2 =  self.drawEvents(self.E2, 1)

    def drawEvents3(self) -> None:
        if self.E3 is not None:
            self.l_events3 =  self.drawEvents(self.E3, 2)

    def drawEvents4(self) -> None:
        if self.E4 is not None:
            self.l_events4 =  self.drawEvents(self.E4, 3)


class CompareTableWidget(QTableWidget): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class
    deleteKeyPressed = pyqtSignal()

    @pyqtSlot('QKeyEvent')
    def keyPressEvent(self, event: Optional['QKeyEvent'] = None) -> None:
        if event is not None and event.key() in [Qt.Key.Key_Delete,Qt.Key.Key_Backspace]:
            self.deleteKeyPressed.emit()
        else:
            super().keyPressEvent(event)

    # fails in selectionChanged() if the first row header is clicked repeatedly and reports [0], [1],.. instead of [0],[],..
    def getselectedRowsFast(self) -> List[int]:
        selectedRows:List[int] = []
        for item in self.selectedItems():
            if item.row() not in selectedRows:
                selectedRows.append(item.row())
        if not selectedRows:
            return self.getLastRow()
        return selectedRows

    def getLastRow(self) -> List[int]:
        rows = self.rowCount()
        if rows > 0:
            return [rows-1]
        return []

class roastCompareDlg(ArtisanDialog):

    __slots__ = [ 'foreground', 'background', 'maxentries', 'basecolors', 'profiles', 'label_number', 'l_align', 'legend', 'legendloc_pos', 'addButton',
        'deleteButton', 'alignnames', 'alignComboBox', 'etypes', 'eventsComboBox', 'cb', 'model', 'button_7_org_state_hidden', 'button_1_org_state_hidden',
        'button_2_org_state_hidden', 'button_10_org_state_hidden', 'pick_handler_id', 'modeComboBox', 'buttonCONTROL_org_state_hidden', 'buttonONOFF_org_state_hidden',
        'buttonRESET_org_state_hidden', 'buttonSTARTSTOP_org_state_hidden', 'profileTable', 'delta_axis_visible' ]

    def __init__(self, parent:QWidget, aw:'ApplicationWindow', foreground:Optional[str] = None, background:Optional[str] = None) -> None:
        super().__init__(parent, aw)

        if platform.system() == 'Darwin':
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)

        self.setAcceptDrops(True)

        self.foreground:Optional[str] = foreground
        self.background:Optional[str] = background
        self.setWindowTitle(QApplication.translate('Form Caption','Comparator'))
        self.maxentries = 10 # maximum number of profiles to be compared
        self.basecolors: List[Tuple[float, float, float, float]] = list(colormaps['tab10'](numpy.linspace(0,1,10)))  # @UndefinedVariable # pylint: disable=maybe-no-member
        self.profiles:List[RoastProfile] = []
        self.label_number = 0
        #
        self.delta_axis_visible:Optional[bool] = None # True if twoAxisMode is active as detected by self.deltaAxisVisible()
        # align line
        self.l_align:Optional[Line2D] = None
        # legend
        self.legend:Optional[Legend] = None
        self.legendloc_pos:Optional[Tuple[float,float]] = None
        # table
        self.profileTable = CompareTableWidget()
        self.createProfileTable()
        # buttons
        self.addButton = QPushButton(QApplication.translate('Button','Add'))
        self.addButton.clicked.connect(self.add)
        self.addButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.deleteButton = QPushButton(QApplication.translate('Button','Delete'))
        self.deleteButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.deleteButton.clicked.connect(self.delete)
        # configurations
        modes = [
            QApplication.translate('ComboBox','Roast'),
            QApplication.translate('ComboBox','BBP+Roast'),
            QApplication.translate('ComboBox','BBP'),
            ]
        self.modeComboBox:MyQComboBox = MyQComboBox()
        self.modeComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.modeComboBox.addItems(modes)
        if self.aw.qmc.compareRoast and self.aw.qmc.compareBBP:
            self.modeComboBox.setCurrentIndex(1)
        elif not self.aw.qmc.compareRoast and self.aw.qmc.compareBBP:
            self.modeComboBox.setCurrentIndex(2)
        else:
            self.modeComboBox.setCurrentIndex(0)
        self.modeComboBox.currentIndexChanged.connect(self.changeModeidx)
        #
        alignLabel = QLabel(QApplication.translate('Label','Align'))
        self.alignnames = [
            QApplication.translate('Label','CHARGE'),
            QApplication.translate('Label','TP'),
            QApplication.translate('Label','DRY'),
            QApplication.translate('Label','FCs'),
            QApplication.translate('Label','FCe'),
            QApplication.translate('Label','SCs'),
            QApplication.translate('Label','SCe'),
            QApplication.translate('Label','DROP'),
            ]
        self.alignComboBox = MyQComboBox()
        self.alignComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.alignComboBox.addItems(self.alignnames)
        if not self.aw.qmc.compareRoast and self.aw.qmc.compareBBP:
            self.aw.qmc.compareAlignEvent = 0
            self.alignComboBox.setCurrentIndex(0)
            self.alignComboBox.setEnabled(False)
        else:
            self.alignComboBox.setCurrentIndex(self.aw.qmc.compareAlignEvent)
        self.alignComboBox.currentIndexChanged.connect(self.changeAlignEventidx)
        #
        self.eventsComboBox = MyQComboBox()
        self.eventsComboBox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.eventsComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.eventsComboBox.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Maximum)
        self.updateEventsMenu(None)
        self.eventsComboBox.setCurrentIndex(self.aw.qmc.compareEvents)
        self.eventsComboBox.currentIndexChanged.connect(self.changeEventsidx)
        #
        self.cb = CheckComboBox(placeholderText='')
        self.cb.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.model:QStandardItemModel = cast(QStandardItemModel, self.cb.model())

        self.updateCurvesMenu(None)
        self.cb.flagChanged.connect(self.flagChanged)

        settings1Layout = QHBoxLayout()
        settings1Layout.addWidget(self.modeComboBox)
        settings1Layout.addStretch()
        settings1Layout.addSpacing(10)
        settings1Layout.addStretch()
        settings1Layout.addWidget(alignLabel)
        settings1Layout.addWidget(self.alignComboBox)

        settings2Layout = QHBoxLayout()
        settings2Layout.addWidget(self.cb)
        settings1Layout.addSpacing(2)
        settings2Layout.addWidget(self.eventsComboBox)

        settingsLayout = QVBoxLayout()
        settingsLayout.addLayout(settings2Layout)
        settingsLayout.addLayout(settings1Layout)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addSpacing(10)
        buttonLayout.addWidget(self.deleteButton)
        buttonLayout.addStretch()
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(settingsLayout)
        mainLayout.addWidget(self.profileTable)
        mainLayout.addLayout(buttonLayout)
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(mainLayout)

        windowFlags = self.windowFlags()
        windowFlags |= Qt.WindowType.Tool
        if platform.system() == 'Windows':
            windowFlags |= Qt.WindowType.WindowMinimizeButtonHint  # Add minimize  button
        self.setWindowFlags(windowFlags)

        self.redraw()

        self.buttonRESET_org_state_hidden = self.aw.buttonRESET.isHidden() # RESET
        self.buttonONOFF_org_state_hidden = self.aw.buttonONOFF.isHidden() # ON/OFF
        self.buttonSTARTSTOP_org_state_hidden = self.aw.buttonSTARTSTOP.isHidden() # START/STOP
        self.buttonCONTROL_org_state_hidden = self.aw.buttonCONTROL.isHidden() # CONTROL

        self.disableButtons()
        self.aw.disableEditMenus(compare=True)

        self.pick_handler_id = self.aw.qmc.fig.canvas.mpl_connect('pick_event', self.onpick_event) # type: ignore[arg-type] # incompatible type "Callable[[PickEvent], None]"; expected "Callable[[Event], Any]

        settings = QSettings()
        if settings.contains('CompareGeometry'):
            self.restoreGeometry(settings.value('CompareGeometry'))

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # make keyPressEvent below work
        self.setFocus(Qt.FocusReason.MouseFocusReason)

    @pyqtSlot('QKeyEvent')
    def keyPressEvent(self, event: Optional['QKeyEvent'] = None) -> None:
        try:
            if event is not None:
                k = int(event.key())
                if k == 71:                       #G (toggle time auto axis mode)
                    self.modeComboBox.setCurrentIndex((self.modeComboBox.currentIndex()+1) % 3)
                else:
                    QWidget.keyPressEvent(self, event)
        except Exception: # pylint: disable=broad-except
            pass

    @staticmethod
    @pyqtSlot('QDragEnterEvent')
    def dragEnterEvent(event: Optional['QDragEnterEvent'] = None) -> None:
        if event is not None:
            mimeData:Optional[QMimeData] = event.mimeData()
            if mimeData is not None and mimeData.hasUrls():
                event.accept()
            else:
                event.ignore()

    @pyqtSlot('QDropEvent')
    def dropEvent(self, event: Optional['QDropEvent'] = None) -> None:
        if event is not None:
            mimeData:Optional[QMimeData] = event.mimeData()
            if mimeData is not None:
                urls = mimeData.urls()
                if urls and len(urls)>0:
                    res:List[str] = []
                    for url in urls:
                        if url.scheme() == 'file':
                            filename = url.toString(QUrl.UrlFormattingOption.PreferLocalFile)
                            qfile = QFileInfo(filename)
                            file_suffix = qfile.suffix()
                            if file_suffix == 'alog':
                                res.append(filename)
                    self.addProfiles(res)

    def enableButtons(self) -> None:
        if not self.buttonRESET_org_state_hidden:
            self.aw.buttonRESET.show() # RESET
        if not self.buttonONOFF_org_state_hidden:
            self.aw.buttonONOFF.show() # ON/OFF
        if not self.buttonSTARTSTOP_org_state_hidden:
            self.aw.buttonSTARTSTOP.show() # START/STOP
        if not self.buttonCONTROL_org_state_hidden:
            self.aw.buttonCONTROL.show() # CONTROL

    def disableButtons(self) -> None:
        self.aw.buttonRESET.hide() # RESET
        self.aw.buttonONOFF.hide() # ON/OFF
        self.aw.buttonSTARTSTOP.hide() # START/STOP
        self.aw.buttonCONTROL.hide() # CONTROL

    ### DRAWING

    def onpick_event(self, event:'PickEvent') -> None:
        p = next((p for p in self.profiles if event.artist in [p.l_mainEvents1,p.l_mainEvents2]), None)
        if p is not None and p.visible and p.active:
            # determine zorder of this profile:
            p_zorder:float = 0
            if p.l_mainEvents1 is not None and p.l_mainEvents1.get_visible():
                p_zorder = p.l_mainEvents1.get_zorder()
            elif p.l_mainEvents2 is not None and p.l_mainEvents2.get_visible():
                p_zorder = p.l_mainEvents2.get_zorder()

            # if there is any profile op != p which is also triggered by this mouse event and has a higher z-order, ignore this pick
            if any(op != p and any(me is not None and me.get_visible() and me.get_zorder() > p_zorder and me.contains(event.mouseevent)[0] for me in [op.l_mainEvents1,op.l_mainEvents2])
                    for op in self.profiles):
                return

            ind = event.ind[0] # type: ignore[attr-defined] # "PickEvent" has no attribute "ind"
            time = p.timex[p.timeindex[ind]]
            if p.timeindex[0] != -1:
                time -= p.timex[p.timeindex[0]]
            temp = float2float(p.temp2[p.timeindex[ind]])
            name_idx = ind + 1 if ind > 0 else ind
            event_name = self.alignnames[name_idx]
            event_name = self.aw.arabicReshape(event_name)
            self.aw.sendmessage(f'{p.label}: {event_name} @ {stringfromseconds(time,leadingzero=False)}, {temp}{self.aw.qmc.mode}')

    # if zgrid is != 0 and either ET or BT delta is selected or any of the visible extra curves is rendered on the delta axis we show the delta (second) y-axis
    def deltaAxisVisible(self) -> bool:
        return self.aw.qmc.zgrid>0 and (self.aw.qmc.compareDeltaET or self.aw.qmc.compareDeltaBT or
                    any((any(len(p.extraDelta1)>i and p.extraDelta1[i] and cv for i, cv in enumerate(p.extra1_curve_visibilities)) or
                         any(len(p.extraDelta2)>i and p.extraDelta2[i] and cv for i, cv in enumerate(p.extra2_curve_visibilities))) for p in self.profiles))

    def updateRightAxis(self) -> None:
        if self.aw.qmc.ax is not None:
            self.aw.qmc.ax.spines.right.set_visible(bool(self.aw.qmc.zgrid != 0 and self.delta_axis_visible))
            self.aw.qmc.ax.spines.top.set_visible(bool(self.aw.qmc.xgrid != 0 and self.aw.qmc.ygrid != 0 and self.aw.qmc.zgrid != 0 and self.delta_axis_visible))
        delta_axis_label = (self.aw.qmc.mode + self.aw.arabicReshape(QApplication.translate('Label', '/min')) if self.aw.qmc.zgrid>0 and self.delta_axis_visible else '')
        if self.aw.qmc.delta_ax is not None:
            prop = self.aw.mpl_fontproperties.copy()
            prop.set_size('small')
            fontprop_medium = self.aw.mpl_fontproperties.copy()
            fontprop_medium.set_size('medium')
            self.aw.qmc.delta_ax.set_ylabel(delta_axis_label,color = self.aw.qmc.palette['ylabel'],fontproperties=fontprop_medium)
            if self.delta_axis_visible and self.aw.qmc.zgrid>0:
                self.aw.qmc.delta_ax.yaxis.set_major_locator(ticker.MultipleLocator(self.aw.qmc.zgrid))
                self.aw.qmc.delta_ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
                for i in self.aw.qmc.delta_ax.get_yticklines():
                    i.set_markersize(10)
                for i in self.aw.qmc.delta_ax.yaxis.get_minorticklines():
                    i.set_markersize(5)
                for label in self.aw.qmc.delta_ax.get_yticklabels() :
                    label.set_fontproperties(prop)
            else:
                self.aw.qmc.delta_ax.yaxis.set_major_locator(ticker.NullLocator())
                self.aw.qmc.delta_ax.yaxis.set_minor_locator(ticker.NullLocator())

    def clearCanvas(self) -> None:
        scale = 1 if self.aw.qmc.graphstyle == 1 else 0
        length = 700 # 100 (128 the default)
        randomness = 12 # 2 (16 default)
        rcParams['path.sketch'] = (scale, length, randomness)

        if self.aw.qmc.ax is None:
            self.aw.qmc.ax = self.aw.qmc.fig.add_subplot(111,facecolor=self.aw.qmc.palette['background'])
        if self.aw.qmc.delta_ax is None:
            self.aw.qmc.delta_ax = self.aw.qmc.ax.twinx()

        self.aw.qmc.fig.suptitle('')
        self.aw.qmc.ax.set_title('')
        self.aw.qmc.ax.clear()
        self.aw.qmc.ax.set_facecolor(self.aw.qmc.palette['background'])
        self.aw.qmc.delta_ax.clear()
        self.aw.qmc.ax.set_ylim(self.aw.qmc.ylimit_min, self.aw.qmc.ylimit)
        grid_axis:Optional[Literal['both', 'x', 'y']] = None
        if self.aw.qmc.temp_grid and self.aw.qmc.time_grid:
            grid_axis = 'both'
        elif self.aw.qmc.temp_grid:
            grid_axis = 'y'
        elif self.aw.qmc.time_grid:
            grid_axis = 'x'
        if grid_axis is not None:
            self.aw.qmc.ax.grid(True,
                axis = grid_axis,
                color = self.aw.qmc.palette['grid'],
                linestyle = self.aw.qmc.gridstyles[self.aw.qmc.gridlinestyle],
                linewidth = self.aw.qmc.gridthickness,
                alpha = self.aw.qmc.gridalpha,
                sketch_params = 0,
                path_effects = [])

        self.aw.qmc.ax.spines.top.set_visible(bool(self.aw.qmc.xgrid != 0 and self.aw.qmc.ygrid != 0 and self.aw.qmc.zgrid != 0 and self.delta_axis_visible))
        self.aw.qmc.ax.spines.bottom.set_visible(self.aw.qmc.xgrid != 0)
        self.aw.qmc.ax.spines.left.set_visible(self.aw.qmc.ygrid != 0)
        self.aw.qmc.ax.spines.right.set_visible(bool(self.aw.qmc.zgrid != 0 and self.delta_axis_visible))

        prop = self.aw.mpl_fontproperties.copy()
        prop.set_size('small')
        fontprop_medium = self.aw.mpl_fontproperties.copy()
        fontprop_medium.set_size('medium')
        fontprop_large = self.aw.mpl_fontproperties.copy()
        fontprop_large.set_size('large')

        temp_axis_label = ('' if self.aw.qmc.ygrid == 0 else self.aw.qmc.mode)
        self.aw.qmc.ax.set_ylabel(temp_axis_label,color=self.aw.qmc.palette['ylabel'],rotation=0,labelpad=10,fontproperties=fontprop_medium)

        #time_axis_label = ("" if self.aw.qmc.xgrid == 0 else self.aw.arabicReshape(QApplication.translate('Label', 'min')))
        time_axis_label = '' # always hide as not very productive
        self.aw.qmc.set_xlabel(time_axis_label)

        tick_dir = 'inout'
        self.aw.qmc.ax.tick_params(\
            axis='x',           # changes apply to the x-axis
            which='both',       # both major and minor ticks are affected
            bottom=True,        # ticks along the bottom edge are on
            top=False,          # ticks along the top edge are off
            direction=tick_dir,
            labelbottom=True)   # labels along the bottom edge are on
        self.aw.qmc.ax.tick_params(\
            axis='y',           # changes apply to the y-axis
            which='both',       # both major and minor ticks are affected
            right=False,
            bottom=True,        # ticks along the bottom edge are on
            top=False,          # ticks along the top edge are off
            direction=tick_dir,
            labelbottom=True)   # labels along the bottom edge are on

        for label in self.aw.qmc.ax.get_xticklabels() :
            label.set_fontproperties(prop)
        for label in self.aw.qmc.ax.get_yticklabels() :
            label.set_fontproperties(prop)

        # format temperature as int, not float in the cursor position coordinate indicator
        self.aw.qmc.ax.fmt_ydata = self.aw.qmc.fmt_data
        self.aw.qmc.ax.fmt_xdata = self.aw.qmc.fmt_timedata

        self.aw.qmc.ax.set_zorder(self.aw.qmc.delta_ax.get_zorder()+1) # put ax in front of delta_ax (which remains empty!)
        #create a second set of axes in the same position as self.ax

        self.aw.qmc.delta_ax.tick_params(\
            axis='y',           # changes apply to the y-axis
            which='both',       # both major and minor ticks are affected
            left=False,         # ticks along the left edge are off
            bottom=False,       # ticks along the bottom edge are off
            top=False,          # ticks along the top edge are off
            direction='inout', # tick_dir # this does not work as ticks are not drawn at all in ON mode with this!?
            labelright=True,
            labelleft=False,
            labelbottom=False)   # labels along the bottom edge are off

        self.aw.qmc.ax.patch.set_visible(True)

        delta_axis_label = (self.aw.qmc.mode + self.aw.arabicReshape(QApplication.translate('Label', '/min')) if self.aw.qmc.zgrid>0 and self.delta_axis_visible else '')
        self.aw.qmc.delta_ax.set_ylabel(delta_axis_label,color = self.aw.qmc.palette['ylabel'],fontproperties=fontprop_medium)

        self.aw.qmc.delta_ax.yaxis.set_label_position('right')

        self.aw.qmc.delta_ax.set_ylim(self.aw.qmc.zlimit_min,self.aw.qmc.zlimit)
        if self.delta_axis_visible and self.aw.qmc.zgrid>0:
            self.aw.qmc.delta_ax.yaxis.set_major_locator(ticker.MultipleLocator(self.aw.qmc.zgrid))
            self.aw.qmc.delta_ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
            for i in self.aw.qmc.delta_ax.get_yticklines():
                i.set_markersize(10)
            for i in self.aw.qmc.delta_ax.yaxis.get_minorticklines():
                i.set_markersize(5)
            for label in self.aw.qmc.delta_ax.get_yticklabels() :
                label.set_fontproperties(prop)
        else:
            self.aw.qmc.delta_ax.yaxis.set_major_locator(ticker.NullLocator())
            self.aw.qmc.delta_ax.yaxis.set_minor_locator(ticker.NullLocator())

        # translate y-coordinate from delta into temp range to ensure the cursor position display (x,y) coordinate in the temp axis
        self.aw.qmc.delta_ax.fmt_ydata = self.aw.qmc.fmt_data
        self.aw.qmc.delta_ax.fmt_xdata = self.aw.qmc.fmt_timedata

        self.aw.qmc.ax.spines['top'].set_color('0.40')
        self.aw.qmc.ax.spines['bottom'].set_color('0.40')
        self.aw.qmc.ax.spines['left'].set_color('0.40')
        self.aw.qmc.ax.spines['right'].set_color('0.40')

        if self.aw.qmc.ygrid > 0:
            self.aw.qmc.ax.yaxis.set_major_locator(ticker.MultipleLocator(self.aw.qmc.ygrid))
            self.aw.qmc.ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
            for i in self.aw.qmc.ax.get_yticklines():
                i.set_markersize(10)
            for i in self.aw.qmc.ax.yaxis.get_minorticklines():
                i.set_markersize(5)
        else:
            self.aw.qmc.ax.yaxis.set_major_locator(ticker.NullLocator())
            self.aw.qmc.ax.yaxis.set_minor_locator(ticker.NullLocator())

        if self.aw.qmc.xgrid <= 0:
            self.aw.qmc.ax.xaxis.set_major_locator(ticker.NullLocator())
            self.aw.qmc.ax.xaxis.set_minor_locator(ticker.NullLocator())


        #update X ticks, labels, and colors
        self.aw.qmc.xaxistosm()

    # draw time alignment vertical line
    def drawAlignmentLine(self) -> None:
        if self.aw.qmc.ax is not None:
            self.l_align = self.aw.qmc.ax.axvline(0,
                color=self.aw.qmc.palette['grid'],
                linestyle=self.aw.qmc.gridstyles[self.aw.qmc.gridlinestyle],
                zorder=0,
                linewidth = self.aw.qmc.gridthickness*2,sketch_params=0,
                path_effects=[])

    def drawLegend(self) -> None:
        if self.aw.qmc.legendloc:
            loc:Union[int, Tuple[float,float]]
            if self.legend is None:
                if self.legendloc_pos is None:
                    loc = self.aw.qmc.legendloc
                else:
                    loc = self.legendloc_pos
            else:
                loc = self.legend._loc # type: ignore # "Legend" has no attribute "_loc" # pylint: disable=protected-access
            handles = []
            labels = []
            for p in self.profiles:
                if p.visible and p.aligned:
                    if self.aw.qmc.swaplcds:
                        lines = [p.l_temp1,p.l_temp2,p.l_delta1,p.l_delta2,p.l_events1,p.l_events2,p.l_events3,p.l_events4]
                    else:
                        lines = [p.l_temp2,p.l_temp1,p.l_delta2,p.l_delta1,p.l_events1,p.l_events2,p.l_events3,p.l_events4]
                    for ll in lines:
                        if ll is not None and ll.get_visible():
                            handles.append(ll)
                            labels.append(p.label)
                            break
            if len(handles) > 0:
                prop = self.aw.mpl_fontproperties.copy()
                prop.set_size('x-small')
                if self.aw.qmc.ax is not None:
                    self.legend = self.aw.qmc.ax.legend(handles,labels,loc=loc,
                        #ncol=ncol,
                        fancybox=True,prop=prop,shadow=False,frameon=True)

                if self.legend is not None:
                    try:
                        self.legend.set_in_layout(False) # remove legend from tight_layout calculation
                    except Exception: # set_in_layout not available in mpl<3.x # pylint: disable=broad-except
                        pass
                    try:
                        self.legend.set_draggable(state=True,use_blit=True)  #,update='bbox')
                    except Exception: # not available in mpl<3.x # pylint: disable=broad-except
                        self.legend.draggable(state=True) # type: ignore # for mpl 2.x
                    frame = self.legend.get_frame()
                    frame.set_facecolor(self.aw.qmc.palette['legendbg'])
                    frame.set_alpha(self.aw.qmc.alpha['legendbg'])
                    frame.set_edgecolor(self.aw.qmc.palette['legendborder'])
                    frame.set_linewidth(0.5)
                    for line,text in zip(self.legend.get_lines(), self.legend.get_texts()):
                        text.set_color(line.get_color())
            elif self.legend is not None:
                self.legend.remove()
        else:
            if self.legend is not None:
                self.legend.remove()
            self.legend = None

    def repaintDlg(self) -> None:
        self.drawLegend()
        self.aw.qmc.placelogoimage()
        self.aw.qmc.fig.canvas.draw()

    def redraw(self) -> None:
        self.clearCanvas()
        self.drawAlignmentLine()
        self.recompute()
        for rp in self.profiles:
            rp.draw()
            rp.updateAlpha()
        self.realign()
        self.updateZorders()
        self.repaintDlg()

    def redrawOnDeltaAxisVisibilityChanged(self) -> None:
        two_axis = self.deltaAxisVisible()
        if self.delta_axis_visible is None or self.delta_axis_visible != two_axis:
            # the two axis status changed thus we do a full redraw incl. a clearCanvas()
            self.delta_axis_visible = two_axis
            self.updateRightAxis()
        self.repaintDlg()

    ### Table

    def setProfileTableRow(self, i:int) -> None:
        profile = self.profiles[i]
        c = QColor.fromRgbF(*profile.color)
        color = QTableWidgetItem()
        color.setBackground(c)
        color.setFlags(Qt.ItemFlag.ItemIsEnabled) # do not change background color on row selection of the color items
        self.profileTable.setItem(i,0,color)
        flag = QCheckBox()
        flag.setChecked(profile.visible)
        flag.stateChanged.connect(self.visibilityChanged)
        flagWidget = QWidget()
        flagLayout = QHBoxLayout(flagWidget)
        flagLayout.addWidget(flag)
        flagLayout.setAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
        flagLayout.setContentsMargins(0,0,0,0)
        self.profileTable.setCellWidget(i,1,flagWidget)
        title_item = QTableWidgetItem(profile.title)
        tooltip = self.renderToolTip(profile)
        if tooltip is not None and tooltip != '':
            title_item.setToolTip(tooltip)
        self.profileTable.setItem(i,2,title_item)
        header = QTableWidgetItem(profile.label)
        self.profileTable.setVerticalHeaderItem(i,header)

    @staticmethod
    def renderToolTip(profile:RoastProfile) -> str:
        tooltip:str = ''
        if profile.metadata is not None:
            try:
                if 'roastdate' in profile.metadata:
                    tooltip = profile.metadata['roastdate'].date().toString()
                    tooltip += ', ' + profile.metadata['roastdate'].time().toString()[:-3]
                if 'roastoftheday' in profile.metadata:
                    if tooltip != '':
                        tooltip += '\n'
                    tooltip += profile.metadata['roastoftheday']
                if 'weight' in profile.metadata:
                    if tooltip != '':
                        tooltip += '\n'
                    tooltip += profile.metadata['weight']
                if 'beans' in profile.metadata:
                    if 'weight' in profile.metadata:
                        tooltip += ' '
                    elif tooltip != '':
                        tooltip += '\n'
                    tooltip += profile.metadata['beans'].strip()
                    if 'moisture_greens' in profile.metadata:
                        tooltip += f" ({float2float(profile.metadata['moisture_greens']):g}%)"
                if 'ambientTemp' in profile.metadata:
                    if tooltip != '':
                        tooltip += '\n'
                    tooltip += profile.metadata['ambientTemp']
                if 'ambient_humidity' in profile.metadata:
                    if 'ambientTemp' in profile.metadata:
                        tooltip += ', '
                    elif tooltip != '':
                        tooltip += '\n'
                    tooltip += profile.metadata['ambient_humidity']
                if 'ambient_pressure' in profile.metadata:
                    if 'ambientTemp' in profile.metadata or 'ambient_humidity' in profile.metadata:
                        tooltip += ', '
                    elif tooltip != '':
                        tooltip += '\n'
                    tooltip += profile.metadata['ambient_pressure']
                if 'weight_loss' in profile.metadata:
                    if tooltip != '':
                        tooltip += '\n'
                    tooltip += profile.metadata['weight_loss']
                if 'ground_color' in profile.metadata:
                    if 'weight_loss' in profile.metadata:
                        tooltip += ', '
                    elif tooltip != '':
                        tooltip += '\n'
                    tooltip += profile.metadata['ground_color']
                if 'AUC' in profile.metadata:
                    if 'weight_loss' in profile.metadata or 'ground_color' in profile.metadata:
                        tooltip += ', '
                    elif tooltip != '':
                        tooltip += '\n'
                    tooltip += profile.metadata['AUC']
                if 'roastingnotes' in profile.metadata:
                    if tooltip != '':
                        tooltip += '\n'
                    tooltip += profile.metadata['roastingnotes'].strip()
                if 'cuppingnotes' in profile.metadata:
                    if tooltip != '':
                        tooltip += '\n'
                    tooltip += profile.metadata['cuppingnotes'].strip()
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
        return tooltip.strip()

    def createProfileTable(self) -> None:
        try:
            self.profileTable.clear()
            self.profileTable.setTabKeyNavigation(True)
            self.profileTable.setColumnCount(3)
            self.profileTable.setAlternatingRowColors(True)
            self.profileTable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.profileTable.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
            self.profileTable.setShowGrid(False)
            vheader: Optional[QHeaderView] = self.profileTable.verticalHeader()
            if vheader is not None:
                vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            self.profileTable.setHorizontalHeaderLabels(['',
                                                         QApplication.translate('Label','ON'),
                                                         QApplication.translate('Label','Title')])
            hheader: Optional[QHeaderView] = self.profileTable.horizontalHeader()
            if hheader is not None:
                hheader.sectionClicked.connect(self.columnHeaderClicked)
            self.profileTable.setCornerButtonEnabled(True) # click in the left header corner selects all entries in the table
            self.profileTable.setSortingEnabled(False)

            vheader = self.profileTable.verticalHeader()
            if vheader is not None:
                vheader.setSectionsMovable(True)
                vheader.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
                vheader.sectionMoved.connect(self.sectionMoved)
                vheader.sectionDoubleClicked.connect(self.tableSectionClicked)

            self.profileTable.itemSelectionChanged.connect(self.selectionChanged)
            self.profileTable.deleteKeyPressed.connect(self.deleteSelected)

            header: Optional[QHeaderView] = self.profileTable.horizontalHeader()
            if header is not None:
                header.setStretchLastSection(True)
                header.setMinimumSectionSize(10)  # color column size
#                header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

            self.profileTable.setColumnWidth(0,10) # color column size
            self.profileTable.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            horizontalScrollBar: Optional[QScrollBar] = self.profileTable.horizontalScrollBar()
            if horizontalScrollBar is not None:
                horizontalScrollBar.setEnabled(False)
            self.profileTable.setAutoScroll(False) # disable scrolling to selected cell

        except Exception as ex: # pylint: disable=broad-except
            _log.exception(ex)
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message','Exception:') + ' createProfileTable() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))

    ### SLOTS

    @pyqtSlot(int)
    def columnHeaderClicked(self, i:int) -> None:
        if i == 1: # flag header clicked
            new_state = not all(p.visible for p in self.profiles)
            for r in range(self.profileTable.rowCount()):
                widget: Optional[QWidget] = self.profileTable.cellWidget(r,1)
                if widget is not None:
                    layout: Optional[QLayout] = widget.layout()
                    if layout is not None:
                        layoutItem: Optional[QLayoutItem] = layout.itemAt(0)
                        if layoutItem is not None:
                            flag = cast(QCheckBox, layoutItem.widget())
                            flag.blockSignals(True)
                            flag.setChecked(new_state)
                            flag.blockSignals(False)
                self.profiles[r].setVisible(new_state)
            # update chart
            self.updateDeltaLimits()
            self.autoTimeLimits()
            self.realign()
            self.repaintDlg()
            self.aw.qpc.update_phases(self.getPhasesData())
        elif i == 2: # title header clicked
            selected = self.profileTable.selectedRanges()
            if selected and len(selected) > 0:
                # disable selection
                self.profileTable.clearSelection()
            else:
                # select all
                self.profileTable.selectAll()

    @pyqtSlot(int,int,int)
    def sectionMoved(self, _logicalIndex:int, _oldVisualIndex:int, _newVisualIndex:int) -> None:
        self.updateMenus()
        self.realign()
        self.updateZorders()
        self.repaintDlg()
        self.aw.qpc.update_phases(self.getPhasesData())

    @pyqtSlot(int)
    def visibilityChanged(self, state:int) -> None:
        i = self.aw.findWidgetsRow(self.profileTable,self.sender(),1)
        if i is not None:
            self.profiles[i].setVisible(bool(state))
            self.updateDeltaLimits()
            self.autoTimeLimits()
            self.realign()
            self.repaintDlg()
            self.aw.qpc.update_phases(self.getPhasesData())


    @pyqtSlot(int,bool)
    def flagChanged(self, i:int, b:bool) -> None:
        if i == 0:
            self.aw.qmc.compareET = b
        elif i == 1:
            self.aw.qmc.compareBT = b
        elif i == 2:
            self.aw.qmc.compareDeltaET = b
            self.updateDeltaLimits()
        elif i == 3:
            self.aw.qmc.compareDeltaBT = b
            self.updateDeltaLimits()
        elif i == 5:
            self.aw.qmc.compareMainEvents = b
        else:
            offset:Final[int] = 7
            j:int = i - offset
            d,m = divmod(j,2)
            if m == 0:
                self.aw.qmc.compareExtraCurves1[d] = b
            else:
                self.aw.qmc.compareExtraCurves2[d] = b
        self.updateVisibilities()
        self.redrawOnDeltaAxisVisibilityChanged()

    @pyqtSlot(int)
    def changeModeidx(self, i:int) -> None:
        if int(not self.aw.qmc.compareRoast) + int(self.aw.qmc.compareBBP) != i:
            if i == 1: # BBP+Roast
                self.aw.qmc.compareRoast = True
                self.aw.qmc.compareBBP = True
                self.alignComboBox.setEnabled(True)
            elif i == 2: # BBP only
                self.aw.qmc.compareRoast = False
                self.aw.qmc.compareBBP = True
                if self.aw.qmc.compareAlignEvent != 0:
                    self.aw.qmc.compareAlignEvent = 0
                    self.blockSignals(True)
                    self.alignComboBox.setCurrentIndex(0)
                    self.blockSignals(False)
                self.alignComboBox.setEnabled(False)
            else: # Roast only
                self.aw.qmc.compareRoast = True
                self.aw.qmc.compareBBP = False
                self.alignComboBox.setEnabled(True)
            self.redraw()

    @pyqtSlot(int)
    def changeAlignEventidx(self, i:int) -> None:
        if self.aw.qmc.compareAlignEvent != i:
            self.aw.qmc.compareAlignEvent = i
            self.realign()
            self.repaintDlg()
            self.aw.qpc.update_phases(self.getPhasesData())

    @pyqtSlot(int)
    def changeEventsidx(self, i:int) -> None:
        self.aw.qmc.compareEvents = i
        self.updateVisibilities()
        self.repaintDlg()

    @pyqtSlot()
    def selectionChanged(self) -> None:
        selected = [self.aw.findWidgetsRow(self.profileTable,si,2) for si in self.profileTable.selectedItems()]
#        selected = self.profileTable.getselectedRowsFast() # does return [1],[2],[1],.. on repeated clicks on the row header of the first entry insteadd of [1],[0],[1],..
        for i,p in enumerate(self.profiles):
            if selected and i not in selected:
                p.setActive(False)
            else:
                p.setActive(True)
        self.updateProfileTableColors()
        self.repaintDlg()

    @pyqtSlot(int)
    def tableSectionClicked(self, i:int) -> None:
        fileURL = QUrl.fromLocalFile(self.profiles[i].filepath)
        if platform.system() == 'Windows' and not self.aw.app.artisanviewerMode:
            self.aw.app.sendMessage2ArtisanInstance(fileURL.toString(),self.aw.app._viewer_id) # pylint: disable=protected-access
        else:
            QDesktopServices.openUrl(fileURL)

    @pyqtSlot()
    def deleteSelected(self) -> None:
        self.deleteProfiles(self.profileTable.getselectedRowsFast())

    @pyqtSlot(bool)
    def add(self,_:bool = False) -> None:
        filenames = self.aw.reportFiles()
        if filenames:
            self.addProfiles(filenames)

    @pyqtSlot(bool)
    def delete(self,_:bool = False) -> None:
        self.deleteProfiles(self.profileTable.getselectedRowsFast())

    ### UPDATE functions

    def updateDeltaLimits(self) -> None:
        # update delta max limit in auto mode
        if (self.aw.qmc.autodeltaxET or self.aw.qmc.autodeltaxBT):
            dmax:float = 0
            for rp in self.profiles:
                if rp.visible and rp.aligned:
                    if (self.cb.itemCheckState(2) == Qt.CheckState.Checked and self.aw.qmc.autodeltaxET) or \
                        (self.cb.itemCheckState(2) == Qt.CheckState.Checked and self.cb.itemCheckState(3) != Qt.CheckState.Checked and self.aw.qmc.autodeltaxBT): # DeltaET
                        dmax = max(dmax,rp.max_DeltaET)
                    if (self.cb.itemCheckState(3) == Qt.CheckState.Checked and self.aw.qmc.autodeltaxBT) or \
                        (self.cb.itemCheckState(3) == Qt.CheckState.Checked and self.cb.itemCheckState(2) != Qt.CheckState.Checked and self.aw.qmc.autodeltaxET) : # DeltaBT
                        dmax = max(dmax,rp.max_DeltaBT)
            if dmax > 0:
                dmax = int(dmax) + 1
                if self.aw.qmc.delta_ax is not None:
                    self.aw.qmc.delta_ax.set_ylim(top=dmax) # we only autoadjust the upper limit
                self.aw.qmc.zlimit = int(round(dmax))

    def recompute(self) -> None:
        for rp in self.profiles:
            rp.recompute()

    def updateZorders(self) -> None:
        profiles = self.getProfilesVisualOrder()
        profiles.reverse()
        for zorder, rp in enumerate(profiles):
            rp.setZorder(zorder)

    def updateVisibilities(self) -> None:
        visibilities:List[bool] = [
                self.cb.itemCheckState(0) == Qt.CheckState.Checked, # ET
                self.cb.itemCheckState(1) == Qt.CheckState.Checked, # BT
                self.cb.itemCheckState(2) == Qt.CheckState.Checked, # DeltaET
                self.cb.itemCheckState(3) == Qt.CheckState.Checked, # DeltaBT
                self.cb.itemCheckState(5) == Qt.CheckState.Checked, # Main events
        ]
        extra1_visibilitites:List[bool] = []
        extra2_visibilitites:List[bool] = []
        offset:Final[int] = 7
        for i in range(self.aw.nLCDS):
            extra1_visibilitites.append(self.cb.itemCheckState(offset + i*2) == Qt.CheckState.Checked)
            extra2_visibilitites.append(self.cb.itemCheckState(offset + i*2 + 1) == Qt.CheckState.Checked)
        for p in self.profiles:
            p.setVisibilities(visibilities, extra1_visibilitites, extra2_visibilitites, self.aw.qmc.compareEvents)

    def updateEventsMenu(self, top:Optional[RoastProfile]) -> None:
        etypes:List[str]
        etypes = (self.aw.qmc.etypes[:-1] if top is None else top.etypes)
        idx:int = self.eventsComboBox.currentIndex()
        self.eventsComboBox.blockSignals(True)
        self.eventsComboBox.clear()
        self.eventsComboBox.addItems([''] + etypes)
        self.eventsComboBox.setCurrentIndex(idx)
        self.eventsComboBox.blockSignals(False)

    def updateAlignMenu(self, top:Optional[RoastProfile]) -> None:
        if top is not None:
            model = self.alignComboBox.model()
            assert isinstance(model, QStandardItemModel)
            for i in range(model.rowCount()):
                item: Optional[QStandardItem] = model.item(i)
                if item is not None:
                    if len(top.timeindex) > i and ((i == 0 and top.timeindex[i] != -1) or (i==1 and top.TP != 0) or (i>1 and top.timeindex[i-1] > 0)):
                        item.setEnabled(True)
                    else:
                        item.setEnabled(False)

    def updateCurvesMenu(self, top:Optional[RoastProfile]) -> None:
        self.model.clear()
        self.cb.addItem(self.aw.ETname)
        item0 = self.model.item(0)
        if item0 is not None:
            item0.setCheckable(True)
        self.cb.setItemCheckState(0,(Qt.CheckState.Checked if self.aw.qmc.compareET else Qt.CheckState.Unchecked))
        self.cb.addItem(self.aw.BTname)
        item1 = self.model.item(1)
        if item1 is not None:
            item1.setCheckable(True)
        self.cb.setItemCheckState(1,(Qt.CheckState.Checked if self.aw.qmc.compareBT else Qt.CheckState.Unchecked))
        self.cb.addItem(deltaLabelUTF8 + self.aw.ETname)
        item2 = self.model.item(2)
        if item2 is not None:
            item2.setCheckable(True)
        self.cb.setItemCheckState(2,(Qt.CheckState.Checked if self.aw.qmc.compareDeltaET else Qt.CheckState.Unchecked))
        self.cb.addItem(deltaLabelUTF8 + self.aw.BTname)
        item3 = self.model.item(3)
        if item3 is not None:
            item3.setCheckable(True)
        self.cb.setItemCheckState(3,(Qt.CheckState.Checked if self.aw.qmc.compareDeltaBT else Qt.CheckState.Unchecked))
        self.cb.insertSeparator(4)
        self.cb.addItem(QApplication.translate('CheckBox','Events'))
        item5 = self.model.item(5)
        if item5 is not None:
            item5.setCheckable(True)
        self.cb.setItemCheckState(5,(Qt.CheckState.Checked if self.aw.qmc.compareMainEvents else Qt.CheckState.Unchecked))
        # add extra device flags
        if top is not None and len(top.extraname1) > 0:
            self.cb.insertSeparator(6)
            offset:int = 7
            for i, (name1, name2) in enumerate(zip(top.extraname1, top.extraname2)):
                self.cb.addItem(QApplication.translate('CheckBox',name1))
                i1 = offset + i*2
                item1 = self.model.item(i1)
                if item1 is not None:
                    item1.setCheckable(True)
                self.cb.setItemCheckState(i1, (Qt.CheckState.Checked if self.aw.qmc.compareExtraCurves1[i] else Qt.CheckState.Unchecked))
                #
                self.cb.addItem(QApplication.translate('CheckBox',name2))
                i2 = offset + i*2 + 1
                item2 = self.model.item(i2)
                if item2 is not None:
                    item2.setCheckable(True)
                self.cb.setItemCheckState(i2, (Qt.CheckState.Checked if self.aw.qmc.compareExtraCurves2[i] else Qt.CheckState.Unchecked))

    def updateMenus(self) -> None:
        top:Optional[RoastProfile] = self.getTopProfileVisualOrder()
        self.updateAlignMenu(top)
        self.updateCurvesMenu(top)
        self.updateEventsMenu(top)

    def updateProfileTableItems(self) -> None:
        for i,p in enumerate(self.profiles):
            w = self.profileTable.item(i,2)
            if w is not None:
                if p.aligned:
                    if self.aw.app.darkmode:
                        w.setForeground(Qt.GlobalColor.white)
                    else:
                        w.setForeground(Qt.GlobalColor.black)
                else:
                    w.setForeground(Qt.GlobalColor.lightGray)

    def updateProfileTableColors(self) -> None:
        for i,p in enumerate(self.profiles):
            w = self.profileTable.item(i,0)
            if w is not None:
                if p.active:
                    c = QColor.fromRgbF(*p.color)
                else:
                    c = QColor.fromRgbF(*p.gray)
                w.setBackground(c)
        self.aw.qpc.update_phases(self.getPhasesData())

    # align all profiles to the first one w.r.t. to the event self.aw.qmc.compareAlignEvent
    #   0:CHARGE, 1:TP, 2:DRY, 3:FCs, 4:FCe, 5:SCs, 6:SCe, 7:DROP
    def realign(self) -> None:
        if len(self.profiles) > 0:
            profiles = self.getProfilesVisualOrder()
            # align top profile to its CHARGE event or first reading to 00:00
            top = profiles[0] # profile on top of the table / chart
            delta = top.startTime()
            top.setTimeoffset(delta)
            top.aligned = True
            # we calculate the min/max timex to to show all data considering this alignment to automatically set the time axis limits
            top.min_time = (top.firstTime() - delta if self.aw.qmc.compareBBP else 0)
#            top.max_time = top.endTime() - delta
            top.max_time = (top.endTime() - delta if self.aw.qmc.compareRoast else 0)
            # align all other profiles to the top profile w.r.t. self.aw.qmc.compareAlignEvent
            refTime:float
            if self.aw.qmc.compareAlignEvent == 0:
                refTime = 0
            elif self.aw.qmc.compareAlignEvent == 1: # TP
                refTime = top.TP
            elif self.aw.qmc.compareAlignEvent>1 and top.timeindex[self.aw.qmc.compareAlignEvent-1] > 0:
                refTime = top.timex[top.timeindex[self.aw.qmc.compareAlignEvent-1]] - delta
            else:
                # no reference point to align the other profiles too!
                if self.l_align is not None:
                    self.l_align.set_visible(False)
                return
            if self.l_align is not None:
                self.l_align.set_xdata([refTime])
                if any(p.visible for p in profiles):
                    self.l_align.set_visible(True)
                else:
                    self.l_align.set_visible(False)
            for p in profiles[1:]:
                if (self.aw.qmc.compareAlignEvent == 0 and p.timeindex[0] != -1):
                    eventTime = p.timex[p.timeindex[self.aw.qmc.compareAlignEvent]]
                    delta = eventTime - refTime
                    p.setTimeoffset(delta)
                    p.aligned = True
                    p.min_time = refTime - eventTime + (p.firstTime() if self.aw.qmc.compareBBP else p.startTime())
#                    p.max_time = p.endTime() - eventTime + refTime
                    p.max_time = (p.endTime() if self.aw.qmc.compareRoast else p.startTime()) - eventTime + refTime
                elif self.aw.qmc.compareAlignEvent==1 and p.TP > 0:
                    p_offset:float = 0
                    if p.timeindex[0]>-1:
                        p_offset = p.timex[p.timeindex[0]]
                    eventTime = p.TP + p_offset
                    delta = eventTime - refTime
                    p.setTimeoffset(delta)
                    p.aligned = True
                    p.min_time = refTime - eventTime + (p.firstTime() if self.aw.qmc.compareBBP else p.startTime())
#                    p.max_time = p.endTime() - eventTime + refTime
                    p.max_time = (p.endTime() if self.aw.qmc.compareRoast else p.startTime()) - eventTime + refTime
                elif self.aw.qmc.compareAlignEvent>1 and p.timeindex[self.aw.qmc.compareAlignEvent-1] > 0:
                    eventTime = p.timex[p.timeindex[self.aw.qmc.compareAlignEvent-1]]
                    delta = eventTime - refTime
                    p.setTimeoffset(delta)
                    p.aligned = True
                    p.min_time = refTime - eventTime + (p.firstTime() if self.aw.qmc.compareBBP else p.startTime())
#                    p.max_time = p.endTime() - eventTime + refTime
                    p.max_time = (p.endTime() if self.aw.qmc.compareRoast else p.startTime()) - eventTime + refTime
                elif (self.aw.qmc.compareAlignEvent == 0 or (self.aw.qmc.compareAlignEvent == 1 and top.TP == 0) or \
                        (self.aw.qmc.compareAlignEvent>1 and top.timeindex[self.aw.qmc.compareAlignEvent-1] == 0)):
                    # align to CHARGE or first reading
                    if p.timeindex[0] != -1:
                        eventTime = p.timex[p.timeindex[0]]
                    else:
                        eventTime = p.timex[0]
                    delta = eventTime - refTime
                    p.setTimeoffset(delta)
                    p.aligned = True
                    p.min_time = refTime - eventTime + (p.firstTime() if self.aw.qmc.compareBBP else p.startTime())
#                    p.max_time = p.endTime() - eventTime + refTime
                    p.max_time = (p.endTime() if self.aw.qmc.compareRoast else p.startTime()) - eventTime + refTime
                else:
                    p.aligned = False
            self.updateVisibilities()
            self.autoTimeLimits()
            self.updateProfileTableItems()
            self.updateDeltaLimits()
        # no profile loaded
        elif self.l_align is not None:
            # we hide the alignment line
            self.l_align.set_visible(False)

    ### ADD/DELETE table items

    def addProfile(self, filename:str, obj:'ProfileData') -> None:
        selected = [self.aw.findWidgetsRow(self.profileTable,si,2) for si in self.profileTable.selectedItems()]
        active = not bool(selected)
        # assign next color
        rp = RoastProfile(self.aw,obj,filename,self.basecolors[0])
        self.basecolors = self.basecolors[1:] # remove used color from list of available basecolors
        # set default label number if no batch number is available
        if rp.label == '':
            self.label_number += 1
            rp.label = str(self.label_number)
        # set initially inactive if currently any another profile is selected
        rp.setActive(active)
        # add profile to the list
        self.profiles.append(rp)
        # add profile to the table
        self.profileTable.setRowCount(len(self.profiles))
        self.setProfileTableRow(len(self.profiles)-1)

    def addProfileFromURL(self, extractor:Callable[[QUrl, 'ApplicationWindow'], Optional['ProfileData']], url:QUrl) -> None:
        _log.info('addProfileFromURL(%s)', url)
        try:
            obj:Optional[ProfileData] = extractor(url, self.aw)
            if obj:
                self.addProfile(str(url), obj)
                self.updateMenus()
                self.realign()
                self.updateZorders()
                self.repaintDlg()
                self.aw.qpc.update_phases(self.getPhasesData())
        except Exception as ex: # pylint: disable=broad-except
            _log.exception(ex)

    # Internal function not to be called directly. Use addProfiles() which also handles the repainting!
    def addProfileFromFile(self, filename:str) -> None:
        _log.debug('addProfileFromFile(%s)', filename)
        try:
            if len(self.profiles) < self.maxentries and not any(filename == p.filepath for p in self.profiles):
                f = QFile(filename)
                if not f.open(QFile.OpenModeFlag.ReadOnly):
                    raise OSError(f.errorString())
                stream = QTextStream(f)
                firstChar = stream.read(1)
                if firstChar == '{':
                    f.close()
                    obj = cast('ProfileData', self.aw.deserialize(filename))
                    self.addProfile(filename,obj)
        except Exception as ex: # pylint: disable=broad-except
            _log.exception(ex)

    def addProfiles(self, filenames:List[str]) -> None:
        if len(filenames) > 0:
            for filename in filenames:
                self.addProfileFromFile(filename)
            self.updateMenus()
            self.realign()
            self.updateZorders()
            self.redrawOnDeltaAxisVisibilityChanged()
            self.aw.qpc.update_phases(self.getPhasesData())

    def deleteProfile(self, i:int) -> None:
        self.profileTable.removeRow(i)
        p = self.profiles[i]
        self.basecolors.append(p.color) # we add the color back to the list of available ones
        self.profiles.remove(p)
        p.undraw()

    def deleteProfiles(self, indices:Optional[List[int]]) -> None:
        if indices is not None and len(indices) > 0:
            for i in sorted(indices,reverse=True):
                self.deleteProfile(i)
            self.updateMenus()
            self.realign()
            self.updateZorders()
            self.redrawOnDeltaAxisVisibilityChanged()
            self.aw.qpc.update_phases(self.getPhasesData())

    ### Utility

    def getTopProfileVisualOrder(self) -> Optional[RoastProfile]:
        for i,p in enumerate(self.profiles):
            if self.profileTable.visualRow(i) == 0:
                return p
        return None

    def getPhasesData(self) -> List[Tuple[str, float, Tuple[float,float,float], bool, bool, str]]:
        data :List[Tuple[str, float, Tuple[float,float,float], bool, bool, str]]= []
        profiles:List[RoastProfile] = self.getProfilesVisualOrder()
        for p in reversed(profiles):
            if p.visible:
                start:float = p.timex[p.timeindex[0]] if p.timeindex[0] != -1 else p.timex[0]
                total:float = p.timex[p.timeindex[6]] - start if p.timeindex[6] != 0 else p.timex[-1]
                dry:float = p.timex[p.timeindex[1]] - start if p.timeindex[1] != 0 else 0
                fcs:float = p.timex[p.timeindex[2]] - start if p.timeindex[2] != 0 else 0
                p1:float = dry
                p3:float = total - fcs if fcs != 0 else 0
                p2:float = total - p1 - p3 if p1 != 0 and p3 != 0 else 0
                c:QColor = QColor.fromRgbF(*p.color)
                data.append((p.label, total, (p1, p2, p3), p.active, p.aligned, c.name()))
        return data

    def getProfilesVisualOrder(self) -> List[RoastProfile]:
        res = self.profiles[:]
        for i,p in enumerate(self.profiles):
            res[self.profileTable.visualRow(i)] = p
        return res

    def autoTimeLimits(self) -> None:
        if self.aw.qmc.autotimex:
            min_timex:Optional[float] = None
            max_timex:Optional[float] = None
            for p in self.profiles:
                if p.visible and p.aligned:
                    if min_timex is None:
                        min_timex = p.min_time
                    else:
                        min_timex = min(min_timex,p.min_time)
                    if max_timex is None:
                        max_timex = p.max_time
                    else:
                        max_timex = max(max_timex,p.max_time)
            if min_timex is not None and max_timex is not None:
                time_period = max_timex - min_timex
                min_timex -= 1/16*time_period
                max_timex += 1/10*time_period
                self.aw.qmc.xaxistosm(min_time=min_timex, max_time=max_timex)

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        #disconnect pick handler
        self.aw.qmc.fig.canvas.mpl_disconnect(self.pick_handler_id)
        #save window geometry
        settings = QSettings()
        settings.setValue('CompareGeometry',self.saveGeometry())
        self.aw.comparator = None
        self.aw.roastCompareAction.setChecked(False)
        self.aw.qmc.reset()
        if self.foreground is not None and self.foreground.strip() != '':
            self.aw.loadFile(self.foreground)
        if self.background is not None and self.background.strip() != '':
            self.aw.loadbackground(self.background)
            self.aw.qmc.background = True
            self.aw.qmc.timealign(redraw=False)
            self.aw.qmc.redraw(forceRenewAxis=True)
        if (self.foreground is None or self.foreground.strip() == '') and (self.background is None or self.background.strip() == ''):
            #selected = [self.aw.findWidgetsRow(self.profileTable,si,2) for si in self.profileTable.selectedItems()]
            selected = self.profileTable.getselectedRowsFast()
            if len(selected) == 1:
                self.aw.loadFile(self.profiles[selected[0]].filepath)
        else:
            self.aw.qmc.timealign()
        self.enableButtons()
        self.aw.enableEditMenus()
        # enable "green flag" menu:
        try:
            self.aw.ntb.enable_edit_curve_parameters()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        self.aw.qpc.update_phases(None)
