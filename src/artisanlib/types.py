#
# ABOUT
# Artisan Types

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


import datetime

try:
    from PyQt6.QtCore import QDateTime # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QDateTime  # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from typing import Optional,  Tuple, List, Union, TYPE_CHECKING
from typing_extensions import TypedDict  # Python <=3.7

if TYPE_CHECKING:
    from plus.stock import BlendList, Blend

class ComputedProfileInformation(TypedDict, total=False):
    CHARGE_ET: float
    CHARGE_BT: float
    TP_idx: int
    TP_time: float
    TP_ET: float
    TP_BT: float
    MET: float
    DRY_time: float
    DRY_ET: float
    DRY_BT: float
    FCs_time: float
    FCs_ET: float
    FCs_BT: float
    FCe_time: float
    FCe_ET: float
    FCe_BT: float
    SCs_time: float
    SCs_ET: float
    SCs_BT: float
    SCe_time: float
    SCe_ET: float
    SCe_BT: float
    DROP_time: float
    DROP_ET: float
    DROP_BT: float
    COOL_time: float
    COOL_ET: float
    COOL_BT: float
    totaltime: float
    dryphasetime: float
    midphasetime: float
    finishphasetime: float
    coolphasetime: float
    dry_phase_ror: float
    mid_phase_ror: float
    finish_phase_ror: float
    total_ror: float
    fcs_ror: float
    dry_phase_delta_temp: float
    mid_phase_delta_temp: float
    finish_phase_delta_temp: float
    total_ts: int
    total_ts_ET: int
    total_ts_BT: int
    AUC: int
    AUCbegin: str
    AUCbase: float
    AUCfromeventflag: int
    dry_phase_AUC: int
    mid_phase_AUC: int
    finish_phase_AUC: int
    weight_loss: float
    volume_gain: float
    moisture_loss: float
    organic_loss: float
    volumein: float
    volumeout: float
    weightin: float
    weightout: float
    green_density: float
    roasted_density: float
    set_density: float
    moisture_greens: float
    moisture_roasted: float
    ambient_humidity: float
    ambient_pressure: float
    ambient_temperature: float
    det: float
    dbt: float
    BTU_preheat: float
    CO2_preheat: float
    BTU_bbp: float
    CO2_bbp: float
    BTU_cooling: float
    CO2_cooling: float
    BTU_LPG: float
    BTU_NG: float
    BTU_ELEC: float
    BTU_batch: float
    BTU_batch_per_green_kg: float
    BTU_roast: float
    BTU_roast_per_green_kg: float
    CO2_batch: float
    CO2_batch_per_green_kg: float
    CO2_roast: float
    CO2_roast_per_green_kg: float
    KWH_batch_per_green_kg: float
    KWH_roast_per_green_kg: float

class ProfileData(TypedDict, total=False):
    recording_version: str
    recording_revision: str
    recording_build: str
    version: str
    revision: str
    build: str
    artisan_os: str
    artisan_os_version: str
    artisan_os_arch: str
    mode: str
    viewerMode: bool
    timeindex: List[int]
    flavors: List[float]
    flavorlabels: List[str]
    flavorstartangle: float
    flavoraspect: float
    title: str
    locale: str
    plus_store: str
    plus_store_label: str
    plus_coffee: str
    plus_coffee_label: str
    plus_blend_label: str
    plus_blend_spec: 'BlendList'
    plus_blend_spec_labels: List[str]
    beans: str
    weight: List[Union[float,str]] # NOTE: internally weight is a typed tuple
    volume: List[Union[float,str]] # NOTE: internally volume is a typed tuple
    density: List[Union[float,str]] # NOTE: internally density is a typed tuple
    density_roasted: List[Union[float,str]] # NOTE: internally density_roasted is a typed tuple
    roastertype: str
    roastersize: float
    roasterheating: int
    machinesetup: str
    operator: str
    organization: str
    drumspeed: str
    heavyFC: bool
    lowFC: bool
    lightCut: bool
    darkCut: bool
    drops: bool
    oily: bool
    uneven: bool
    tipping: bool
    scorching: bool
    divots: bool
    whole_color: int
    ground_color: int
    color_system: str
    volumeCalcWeightIn: str
    volumeCalcWeightOut: str
    roastdate: str
    roastisodate: str
    roasttime: str
    roastepoch: int
    roasttzoffset: int
    roastbatchnr: int
    roastbatchprefix: str
    roastbatchpos: int
    roastUUID: str
    beansize:str # legacy; float in str mapped to beansize_max
    beansize_min:str # int saved as str to external profiles (internal variable of type int)
    beansize_max:str # int saved as str to external profiles (internal variable of type int)
    specialevents: List[int]
    specialeventstype: List[int]
    specialeventsvalue: List[float]
    specialeventsStrings: List[str]
    etypes: List[str]
    cuppingnotes: str
    roastingnotes: str
    timex: List[float]
    temp1: List[float]
    temp2: List[float]
    phases: List[int]
    zmax: int
    zmin: int
    ymax: int
    ymin: int
    xmin: float
    xmax: float
    ambientTemp: float
    ambient_humidity: float
    ambient_pressure: float
    moisture_greens: float
    greens_temp: float
    moisture_roasted: float
    extradevices: List[int]
    extraname1: List[str]
    extraname2: List[str]
    extratimex: List[List[float]]
    extratemp1: List[List[float]]
    extratemp2: List[List[float]]
    extramathexpression1: List[str]
    extramathexpression2: List[str]
    extradevicecolor1: List[str]
    extradevicecolor2: List[str]
    extraLCDvisibility1: List[bool]
    extraLCDvisibility2: List[bool]
    extraCurveVisibility1: List[bool]
    extraCurveVisibility2: List[bool]
    extraDelta1: List[bool]
    extraDelta2: List[bool]
    extraFill1: List[int]
    extraFill2: List[int]
    extramarkersizes1: List[float]
    extramarkersizes2: List[float]
    extramarkers1: List[str]
    extramarkers2: List[str]
    extralinewidths1:List[float]
    extralinewidths2:List[float]
    extralinestyles1:List[str]
    extralinestyles2:List[str]
    extradrawstyles1:List[str]
    extradrawstyles2:List[str]
    externalprogram: str
    externaloutprogram: str
    extraNoneTempHint1: List[bool]
    extraNoneTempHint2: List[bool]
    alarmsetlabel:str
    alarmflag: List[int]
    alarmguard: List[int]
    alarmnegguard: List[int]
    alarmtime: List[int]
    alarmoffset: List[int]
    alarmcond: List[int]
    alarmsource: List[int]
    alarmtemperature: List[float]
    alarmaction: List[int]
    alarmbeep: List[int]
    alarmstrings: List[str]
    backgroundpath: str
    backgroundUUID: str
    samplinginterval: float
    svLabel: str
    svValues: List[float]
    svRamps: List[int]
    svSoaks: List[int]
    svActions: List[int]
    svBeeps: List[bool]
    svDescriptions: List[str]
    devices: List[str]
    elevation: int
    computed: ComputedProfileInformation
    anno_positions: List[List[float]]
    flag_positions: List[List[float]]
    legendloc_pos: List[float]
    loadlabels: List[str]
    loadratings: List[float]
    ratingunits: List[int]
    sourcetypes: List[int]
    load_etypes: List[int]
    presssure_percents: List[bool]
    loadevent_zeropcts: List[int]
    loadevent_hundpcts: List[int]
    preheatDuration: int
    preheatenergies:List[float]
    betweenbatchDuration: int
    betweenbatchenergies: List[float]
    coolingDuration: int
    coolingenergies: List[float]
    betweenbatch_after_preheat: bool
    electricEnergyMix: int
    plus_sync_record_hash: str


class ExtraDeviceSettings(TypedDict): #, total=False):
    extradevices           : List[int]
    extradevicecolor1      : List[str]
    extradevicecolor2      : List[str]
    extraname1             : List[str]
    extraname2             : List[str]
    extramathexpression1   : List[str]
    extramathexpression2   : List[str]
    extraLCDvisibility1    : List[bool]
    extraLCDvisibility2    : List[bool]
    extraCurveVisibility1  : List[bool]
    extraCurveVisibility2  : List[bool]
    extraDelta1            : List[bool]
    extraDelta2            : List[bool]
    extraFill1             : List[int]
    extraFill2             : List[int]
    extralinestyles1       : List[str]
    extralinestyles2       : List[str]
    extradrawstyles1       : List[str]
    extradrawstyles2       : List[str]
    extralinewidths1       : List[float]
    extralinewidths2       : List[float]
    extramarkers1          : List[str]
    extramarkers2          : List[str]
    extramarkersizes1      : List[float]
    extramarkersizes2      : List[float]
    etypes                 : List[str]

Palette = Tuple[
    List[int],    # 0: event button types
    List[float],  # 1: event button values (same length as event button types)
    List[int],    # 2: event button actions (same length as event button actions)
    List[int],    # 3: event button visibility (same length as event button actions)
    List[str],    # 4: event button actions (same length as event button actions)
    List[str],    # 5: event button labels (same length as event button actions)
    List[str],    # 6: event button descriptions (same length as event button actions)
    List[str],    # 7: event button colors (same length as event button actions)
    List[str],    # 8: event button text colors (same length as event button actions)
    List[int],    # 9: slider visibilities; len=self.eventsliders
    List[int],    # 10: slider actions; len=self.eventsliders
    List[str],    # 11: slider commands; len=self.eventsliders
    List[float],  # 12: slider offsets; len=self.eventsliders
    List[float],  # 13: slider factors; len=self.eventsliders
    List[int],    # 14: quantifier active; len=self.eventsliders
    List[int],    # 15: quantifier sources; len=self.eventsliders
    List[int],    # 16: quantifier min; len=self.eventsliders
    List[int],    # 17: quantifier max; len=self.eventsliders
    List[int],    # 18: quanfifier coarse; len=self.eventsliders
    List[int],    # 19: slider min; len=self.eventsliders
    List[int],    # 20: slider max; len=self.eventsliders
    List[int],    # 21: slider coarse; len=self.eventsliders
    List[int],    # 22: slider temp flags; len=self.eventsliders
    List[str],    # 23: slider units; len=self.eventsliders
    List[int],    # 24: slider bernoulli flags; len=self.eventsliders
    str,          # 25: label
    List[int],    # 26 quantifier action flags; len=self.eventsliders
    List[int]     # 27 quantifier SV flags; len=self.eventsliders
    ]

class BTU(TypedDict, total=False):
    load_pct    : float
    duration    : float
    BTUs        : float
    CO2g        : float
    LoadLabel   : str
    Kind        : int
    SourceType  : int
    SortOrder   : int

class EnergyMetrics(TypedDict, total=False):
    BTU_batch               : float
    BTU_batch_per_green_kg  : float
    CO2_batch               : float
    BTU_preheat             : float
    CO2_preheat             : float
    BTU_bbp                 : float
    CO2_bbp                 : float
    BTU_cooling             : float
    CO2_cooling             : float
    BTU_roast               : float
    BTU_roast_per_green_kg  : float
    CO2_roast               : float
    CO2_batch_per_green_kg  : float
    CO2_roast_per_green_kg  : float
    BTU_LPG                 : float
    BTU_NG                  : float
    BTU_ELEC                : float
    KWH_batch_per_green_kg  : float
    KWH_roast_per_green_kg  : float

class Wheel(TypedDict, total=False):
    wheelnames: List[List[str]]
    segmentlengths: List[List[float]]
    segmentsalpha: List[List[float]]
    wradii: List[float]
    startangle: List[float]
    projection: List[int]
    wheeltextsize: List[int]
    wheelcolor: List[List[str]]
    wheelparent: List[List[int]]
    wheeledge: float
    wheellinewidth: float
    wheellinecolor: str
    wheeltextcolor: str
    wheelaspect: float

class ProductionData(TypedDict, total=False):
    batchprefix: str
    batchnr: int
    roastUUID: str
    plus_coffee: str
    title: str
    roastdate: Optional[QDateTime]
    beans: str
    weight: Optional[Tuple[float,float,str]]
    whole_color: int
    ground_color: int
    color_system: str
    roastertype: str
    roastersize: float
    beansize_min: int
    beansize_max: int
    roastingnotes: str
    cuppingnotes: str

class ProductionDataStr(TypedDict):
    id: str # noqa: A003
    nr: str
    title: str
    datetime: datetime.datetime
    time: str # as string, rendered with data and time separated by a space
    beans: str
    weight_in: str
    weight_out: str
    weight_loss :str
    weight_in_num: float
    weight_out_num: float
    weight_loss_num: float
    whole_color: int
    ground_color: int
    color_system: str
    roastertype: str
    roastersize: float
    beansize_min: int
    beansize_max: int
    roastingnotes: str
    cuppingnotes: str

class CurveSimilarity(TypedDict):
    mse_BT: float
    mse_deltaBT: float
    rmse_BT: float
    rmse_deltaBT: float
    r2_BT: float
    r2_deltaBT: float
    ror_fcs_act: str
    ror_fcs_delta: str
    ror_max_delta: float
    ror_min_delta: float
    segmentresultstr: str

class RecentRoast(TypedDict, total=False):
    title: str
    beans: str
    weightIn: float
    weightOut: float
    weightUnit: str
    volumeIn: float
    volumeOut: float
    volumeUnit: str
    densityWeight: float
    densityRoasted: float
    beanSize_min: int
    beanSize_max: int
    moistureGreen: float
    moistureRoasted: float
    wholeColor: int
    groundColor: int
    colorSystem: str
    background: Optional[str]
    roastUUID: Optional[str]
    batchnr: int
    batchprefix: str
    plus_account: Optional[str]
    plus_store: Optional[str]
    plus_store_label:Optional[str]
    plus_coffee:Optional[str]
    plus_coffee_label:Optional[str]
    plus_blend_label:Optional[str]
    plus_blend_spec:Optional['Blend']
    plus_blend_spec_labels: Optional[List[str]]

class SerialSettings(TypedDict):
    port: str
    baudrate: int
    bytesize: int
    stopbits: int
    parity: str
    timeout: float
