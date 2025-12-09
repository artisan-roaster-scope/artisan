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

from PyQt6.QtCore import QDateTime

from typing import TypedDict, Required, TYPE_CHECKING

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
    roast_defects_loss: float
    total_loss: float
    volume_gain: float
    moisture_loss: float
    organic_loss: float
    volumein: float
    volumeout: float
    weightin: float
    weightout: float
    roast_defects_weight: float
    total_yield: float
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
    bbp_total_time: float
    bbp_bottom_temp: float
    bbp_begin_to_bottom_time: float
    bbp_bottom_to_charge_time: float
    bbp_begin_to_bottom_ror: float
    bbp_bottom_to_charge_ror: float

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
    timeindex: list[int]
    flavors: list[float]
    flavors_total_correction: float
    flavorlabels: list[str]
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
    plus_blend_spec_labels: list[str]
    beans: str
    weight: list[float|str] # NOTE: internally weight is a typed tuple
    volume: list[float|str] # NOTE: internally volume is a typed tuple
    density: list[float|str] # NOTE: internally density is a typed tuple
    density_roasted: list[float|str] # NOTE: internally density_roasted is a typed tuple
    defects_weight:float
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
    whole_color: float
    ground_color: float
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
    scheduleID: str
    scheduleDate: str
    beansize:str # legacy; float in str mapped to beansize_max
    beansize_min:str # int saved as str to external profiles (internal variable of type int)
    beansize_max:str # int saved as str to external profiles (internal variable of type int)
    specialevents: list[int]
    specialeventstype: list[int]
    specialeventsvalue: list[float]
    specialeventsStrings: list[str]
    default_etypes: list[bool]
    default_etypes_set: list[int]
    etypes: list[str]
    cuppingnotes: str
    roastingnotes: str
    timex: list[float]
    temp1: list[float]
    temp2: list[float]
    phases: list[int]
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
    extradevices: list[int]
    extraname1: list[str]
    extraname2: list[str]
    extratimex: list[list[float]]
    extratemp1: list[list[float]]
    extratemp2: list[list[float]]
    extramathexpression1: list[str]
    extramathexpression2: list[str]
    extradevicecolor1: list[str]
    extradevicecolor2: list[str]
    extraLCDvisibility1: list[bool]
    extraLCDvisibility2: list[bool]
    extraCurveVisibility1: list[bool]
    extraCurveVisibility2: list[bool]
    extraDelta1: list[bool]
    extraDelta2: list[bool]
    extraFill1: list[int]
    extraFill2: list[int]
    extramarkersizes1: list[float]
    extramarkersizes2: list[float]
    extramarkers1: list[str]
    extramarkers2: list[str]
    extralinewidths1: list[float]
    extralinewidths2: list[float]
    extralinestyles1: list[str]
    extralinestyles2: list[str]
    extradrawstyles1: list[str]
    extradrawstyles2: list[str]
    externalprogram: str
    externaloutprogram: str
    extraNoneTempHint1: list[bool]
    extraNoneTempHint2: list[bool]
    alarmsetlabel: str
    alarmflag: list[int]
    alarmguard: list[int]
    alarmnegguard: list[int]
    alarmtime: list[int]
    alarmoffset: list[int]
    alarmcond: list[int]
    alarmsource: list[int]
    alarmtemperature: list[float]
    alarmaction: list[int]
    alarmbeep: list[int]
    alarmstrings: list[str]
    backgroundpath: str
    backgroundUUID: str
    samplinginterval: float
    svLabel: str
    svValues: list[float]
    svRamps: list[int]
    svSoaks: list[int]
    svActions: list[int]
    svBeeps: list[bool]
    svDescriptions: list[str]
    pidKp: float
    pidKi: float
    pidKd: float
    pidPsetpointWeight: float
    pidDsetpointWeight: float
    pidSource: int
    svLookahead: int
    ramp_lookahead: int
    pidKp1: float
    pidKi1: float
    pidKd1: float
    pidKp2: float
    pidKi2: float
    pidKd2: float
    pidSchedule0: float
    pidSchedule1: float
    pidSchedule2: float
    gain_scheduling: bool
    gain_scheduling_on_SV: bool
    gain_scheduling_quadratic: bool
    devices: list[str]
    elevation: int
    computed: ComputedProfileInformation
    anno_positions: list[list[float]]
    flag_positions: list[list[float]]
    legendloc_pos: list[float]
    loadlabels: list[str]
    loadratings: list[float]
    ratingunits: list[int]
    sourcetypes: list[int]
    load_etypes: list[int]
    presssure_percents: list[bool]
    loadevent_zeropcts: list[int]
    loadevent_hundpcts: list[int]
    meterlabels: list[str]
    meterunits: list[int]
    metersources: list[int]
    meterfuels: list[int]
    co2kg_per_btu: list[float]
    biogas_co2_reduction: float
    preheatDuration: int
    preheatenergies: list[float]
    betweenbatchDuration: int
    betweenbatchenergies: list[float]
    coolingDuration: int
    coolingenergies: list[float]
    betweenbatch_after_preheat: bool
    electricEnergyMix: int
    gasMix: int
    meterreads: list[list[float]]
    plus_sync_record_hash: str
    bbp_begin: str
    bbp_time_added_from_prev: float
    bbp_endroast_epoch_msec: int
    bbp_endevents: list[list[float|None]]
    bbp_dropevents: list[list[float|None]]
    bbp_dropbt: float
    bbp_dropet: float
    bbp_drop_to_end: float

class ExtraDeviceSettings(TypedDict):
    extradevices           : list[int]
    extradevicecolor1      : list[str]
    extradevicecolor2      : list[str]
    extraname1             : list[str]
    extraname2             : list[str]
    extramathexpression1   : list[str]
    extramathexpression2   : list[str]
    extraLCDvisibility1    : list[bool]
    extraLCDvisibility2    : list[bool]
    extraCurveVisibility1  : list[bool]
    extraCurveVisibility2  : list[bool]
    extraDelta1            : list[bool]
    extraDelta2            : list[bool]
    extraFill1             : list[int]
    extraFill2             : list[int]
    extralinestyles1       : list[str]
    extralinestyles2       : list[str]
    extradrawstyles1       : list[str]
    extradrawstyles2       : list[str]
    extralinewidths1       : list[float]
    extralinewidths2       : list[float]
    extramarkers1          : list[str]
    extramarkers2          : list[str]
    extramarkersizes1      : list[float]
    extramarkersizes2      : list[float]
    default_etypes_set     : list[int]
    etypes                 : list[str]

Palette = tuple[
    list[int],    # 0: event button types
    list[float],  # 1: event button values (same length as event button types)
    list[int],    # 2: event button actions (same length as event button actions)
    list[int],    # 3: event button visibility (same length as event button actions)
    list[str],    # 4: event button action strings (same length as event button actions)
    list[str],    # 5: event button labels (same length as event button actions)
    list[str],    # 6: event button descriptions (same length as event button actions)
    list[str],    # 7: event button colors (same length as event button actions)
    list[str],    # 8: event button text colors (same length as event button actions)
    list[int],    # 9: slider visibilities; len=self.eventsliders
    list[int],    # 10: slider actions; len=self.eventsliders
    list[str],    # 11: slider commands; len=self.eventsliders
    list[float],  # 12: slider offsets; len=self.eventsliders
    list[float],  # 13: slider factors; len=self.eventsliders
    list[int],    # 14: quantifier active; len=self.eventsliders
    list[int],    # 15: quantifier sources; len=self.eventsliders
    list[int],    # 16: quantifier min; len=self.eventsliders
    list[int],    # 17: quantifier max; len=self.eventsliders
    list[int],    # 18: quanfifier coarse; len=self.eventsliders
    list[int],    # 19: slider min; len=self.eventsliders
    list[int],    # 20: slider max; len=self.eventsliders
    list[int],    # 21: slider coarse; len=self.eventsliders
    list[int],    # 22: slider temp flags; len=self.eventsliders
    list[str],    # 23: slider units; len=self.eventsliders
    list[int],    # 24: slider bernoulli flags; len=self.eventsliders
    str,          # 25: label
    list[int],    # 26: quantifier action flags; len=self.eventsliders
    list[int]    # 27: quantifier SV flags; len=self.eventsliders
    ]

class BTU(TypedDict):
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
    BTU_METER1              : float
    BTU_METER2              : float
    KWH_batch_per_green_kg  : float
    KWH_roast_per_green_kg  : float

class Wheel(TypedDict, total=False):
    wheelnames: list[list[str]]
    segmentlengths: list[list[float]]
    segmentsalpha: list[list[float]]
    wradii: list[float]
    startangle: list[float]
    projection: list[int]
    wheeltextsize: list[int]
    wheelcolor: list[list[str]]
    wheelparent: list[list[int]]
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
    roastdate: QDateTime|None
    beans: str
    weight: tuple[float,float,str]|None
    defects_weight: float
    whole_color: float
    ground_color: float
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
    weight_loss: str
    weight_in_num: float
    weight_out_num: float
    weight_loss_num: float
    defects_weight: str
    defects_loss: str
    defects_weight_num: float
    defects_loss_num: float
    whole_color: float
    ground_color: float
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
    title: Required[str]
    beans: str
    weightIn: Required[float]
    weightOut: float
    weightUnit: Required[str]
    volumeIn: float
    volumeOut: float
    volumeUnit: str
    densityWeight: float
    densityRoasted: float
    beanSize_min: int
    beanSize_max: int
    moistureGreen: float
    moistureRoasted: float
    wholeColor: float
    groundColor: float
    colorSystem: str
    background: str|None
    roastUUID: str|None
    batchnr: int
    batchprefix: str
    plus_account: str|None
    plus_store: str|None
    plus_store_label:str|None
    plus_coffee:str|None
    plus_coffee_label:str|None
    plus_blend_label:str|None
    plus_blend_spec:'Blend|None'
    plus_blend_spec_labels: list[str]|None

class SerialSettings(TypedDict):
    port: str
    baudrate: int
    bytesize: int
    stopbits: int
    parity: str
    timeout: float

class BTBreakParams(TypedDict):
    delay: list[list[float]]
    d_drop: list[list[float]]
    d_charge: list[list[float]]
    offset_charge: list[list[float]]
    offset_drop: list[list[float]]
    dpre_dpost_diff: list[list[float]]
    tight: int
    loose: int
    f: float
    maxdpre: float
    f_dtwice: float

class AlarmSet(TypedDict):
    label: str
    flags: list[int]
    guards: list[int]
    negguards: list[int]
    times: list[int]
    offsets: list[int]
    sources: list[int]
    conditions: list[int]
    temperatures: list[float]
    actions: list[int]
    beeps: list[int]
    alarmstrings: list[str]

class BbpCache(TypedDict, total=False):
    mode: str
    drop_bt: float
    drop_et: float
    end_roastepoch_msec: int
    end_events: list[list[float|None]]
    drop_events: list[list[float|None]]
    drop_to_end: float
