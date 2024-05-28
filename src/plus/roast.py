#
# roast.py
#
# Copyright (c) 2023, Paul Holleis, Marko Luther
# All rights reserved.
#
#
# ABOUT
# This module connects to the artisan.plus inventory management service

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from artisanlib.util import weight_units, convertWeight
from plus import config, util, stock
import hashlib
import logging

from typing import Final, Any, Optional, Dict, List, Tuple, TYPE_CHECKING  #for Python >= 3.9: can remove 'List', 'Dict' and 'Tuple' since type hints can use the generic 'list', 'dict' and 'tuple'


if TYPE_CHECKING:
    from artisanlib.types import ProfileData # pylint: disable=unused-import


_log: Final[logging.Logger] = logging.getLogger(__name__)

# given a profile dictionary extract key parameters to populate a Roast element
# background=True if the bp is holding a background profile (ambientTemp, AUCbase not converted to current temp mode)
def getTemplate(bp: 'ProfileData', background:bool=False) -> Dict[str, Any]:  #for Python >= 3.9 can replace 'Dict' with the generic type hint 'dict'
    _log.debug('getTemplate()')
    d: Dict[str, Any] = {}
    try:
        try:
            util.addNum2dict(
                bp, 'roastbatchnr', d, 'batch_number', 0, 65534, 0
            )
            util.addString2dict(
                bp, 'roastbatchprefix', d, 'batch_prefix', 50
            )
            util.addNum2dict(
                bp, 'roastbatchpos', d, 'batch_pos', 0, 255, 0
            )
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

        try:
            if 'roastepoch' in bp:
                d['date'] = util.epoch2ISO8601(bp['roastepoch'])
                gmt_offset = util.limitnum(
                    -60000, 60000, util.getGMToffset()
                )
                if gmt_offset is not None:
                    d['GMT_offset'] = gmt_offset
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

        if 'weight' in bp:
            try:
                w_in = bp['weight'][0]
                assert isinstance(w_in, (int, float))
                w_unit = bp['weight'][2]
                assert isinstance(w_unit, str)
                w = util.limitnum(
                    0,
                    65534,
                    convertWeight(
                        w_in,
                        weight_units.index(w_unit),
                        weight_units.index('Kg'),
                    ),
                )
                if w is not None:
                    d['start_weight'] = util.float2floatMin(w, 3)  # in kg
                else:
                    d['start_weight'] = 0
            except Exception as e:  # pylint: disable=broad-except
                _log.exception(e)
            try:
                w_in = bp['weight'][1]
                assert isinstance(w_in, (int, float))
                w_unit = bp['weight'][2]
                assert isinstance(w_unit, str)
                w = util.limitnum(
                    0,
                    65534,
                    convertWeight(
                        w_in,
                        weight_units.index(w_unit),
                        weight_units.index('Kg'),
                    ),
                )
                if w is not None:
                    d['end_weight'] = util.float2floatMin(w, 3)  # in kg
                else:
                    d['end_weight'] = 0
            except Exception as e:  # pylint: disable=broad-except
                _log.exception(e)

        if 'density_roasted' in bp and bp['density_roasted'][0]:
            try:
                dr = bp['density_roasted'][0]
                assert isinstance(dr, (int, float))
                n = util.limitnum(0, 1000, dr)
                if n is not None:
                    d['density_roasted'] = util.float2floatMin(n, 1)
            except Exception as e:  # pylint: disable=broad-except
                _log.exception(e)

        util.add2dict(bp, config.uuid_tag, d, 'id')                 # roast UUID
        util.add2dict(bp, config.schedule_uuid_tag, d, 's_item_id') # ScheduleItem UUID

        try:
            util.addNum2dict(bp, 'moisture_roasted', d, 'moisture', 0, 100, 1)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        try:
            util.addString2dict(bp, 'title', d, 'label', 255)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        try:
            util.addString2dict(bp, 'roastertype', d, 'machine', 50)
            util.addString2dict(bp, 'machinesetup', d, 'setup', 50)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

        try:
            if (
                'roastersize' in bp
                and bp['roastersize'] is not None
                and bp['roastersize'] != 0
            ):
                util.addNum2dict(
                    bp, 'roastersize', d, 'roastersize', 0, 999, 1
                )
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        try:
            if (
                'roasterheating' in bp
                and bp['roasterheating'] is not None
                and bp['roasterheating'] != 0
            ):
                util.addNum2dict(
                    bp, 'roasterheating', d, 'roasterheating', 0, 999, 0
                )
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

        try:
            util.addNum2dict(bp, 'whole_color', d, 'whole_color', 0, 255, 0)
            util.addNum2dict(bp, 'ground_color', d, 'ground_color', 0, 255, 0)
            if 'whole_color' in d or 'ground_color' in d:
                util.addString2dict(bp, 'color_system', d, 'color_system', 25)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

        try:
            mode = None
            if background and 'mode' in bp:
                # background profile data is not converted to the current temperature mode
                mode = bp['mode']
            util.addTemp2dict(bp, 'ambientTemp', d, 'temperature', mode)
            util.addNum2dict(
                bp, 'ambient_pressure', d, 'pressure', 800, 1200, 1
            )
            util.addNum2dict(bp, 'ambient_humidity', d, 'humidity', 0, 100, 1)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

        if 'computed' in bp:
            cp = bp['computed']

            util.addAllTemp2dict(
                cp,
                d,
                [
                    ('CHARGE_ET', 'charge_temp_ET'),
                    ('CHARGE_BT', 'charge_temp'),
                    ('TP_BT', 'TP_temp'),
                    ('DRY_BT', 'DRY_temp'),
                    ('FCs_BT', 'FCs_temp'),
                    ('FCe_BT', 'FCe_temp'),
                    ('DROP_BT', 'drop_temp'),
                    ('DROP_ET', 'drop_temp_ET'),
                ],
            )
            util.addAllTime2dict(
                cp,
                d,
                [
                    'TP_time',
                    'DRY_time',
                    'FCs_time',
                    'FCe_time',
                    ('DROP_time', 'drop_time'),
                ],
            )

            if 'fcs_ror' in cp:
                mode = None
                if background and 'mode' in bp:
                    # background profile data is not converted to the current temperature mode
                    mode = bp['mode']
                util.addRoRTemp2dict(cp, 'fcs_ror', d, 'FCs_RoR', mode)

            if 'finishphasetime' in cp:
                util.addTime2dict(cp, 'finishphasetime', d, 'DEV_time')
                if 'totaltime' in cp:
                    v = util.limitnum(
                        0,
                        100,
                        util.float2floatMin(
                            cp['finishphasetime'] / cp['totaltime'] * 100,
                            1,
                        ),
                    )
                    if v is not None:
                        d['DEV_ratio'] = v

            util.addNum2dict(cp, 'AUC', d, 'AUC', 0, 10000, 0)
            util.addTemp2dict(cp, 'AUCbase', d, 'AUC_base')

    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    return d


# remove all data but for what is to be synced with the server
def trimBlendSpec(blend_spec:stock.Blend) -> Optional[stock.Blend]:
    try:
        res:stock.Blend = {} # type: ignore # missing required fields (added later)
        if 'label' in blend_spec:
            res['label'] = blend_spec['label']
            if 'ingredients' in blend_spec and blend_spec['ingredients']:
                res_ingredients:List[stock.BlendIngredient] = []
                for ingredient in blend_spec['ingredients']:
                    res_ingredient:stock.BlendIngredient = {} # type: ignore # missing required fields (added later)
                    for tag in ['coffee', 'ratio', 'ratio_num', 'ratio_denom']:
                        if tag in ingredient:
                            res_ingredient[tag] = ingredient[tag] # type: ignore # field vars like 'tag' are not supported by mypy for TypedDicts
                    if res_ingredient:
                        res_ingredients.append(res_ingredient)
                if res_ingredients:
                    res['ingredients'] = res_ingredients
                    return res
        return None
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
        return None


def getRoast() -> Dict[str, Any]:  #for Python >= 3.9 can replace 'Dict' with the generic type hint 'dict'
    d = {}
    try:
        _log.debug('getRoast()')
        assert config.app_window is not None
        aw = config.app_window
        p:ProfileData = aw.getProfile()

        d = getTemplate(p)

        # id => roast_id
        if 'id' in d:
            d['roast_id'] = d['id']
            del d['id']

        # start_weight => amount
        if 'start_weight' in d:
            d['amount'] = d['start_weight']
            del d['start_weight']
        else:
            d['amount'] = 0

        # computed values added just for the profile, but not for
        # the profiles template
        try:
            if 'computed' in p:
                cp = p['computed']
                if 'det' in cp:
                    util.addTempDiff2dict(cp, 'det', d, 'CM_ETD')
                if 'dbt' in cp:
                    util.addTempDiff2dict(cp, 'dbt', d, 'CM_BTD')
                # Energy Consumption data only added if not zero
                util.addAllNum2dict(
                    cp,
                    d,
                    [
                        # energy consumption by source type in BTU
                        'BTU_ELEC',
                        'BTU_LPG',
                        'BTU_NG',
                        # energy consumption by process in BTU
                        'BTU_roast',
                        'BTU_preheat',
                        'BTU_bbp',
                        'BTU_cooling',
                        # total energy conumption per batch
                        'BTU_batch',
                    ],
                    None,  # no min limit
                    None,  # no max limit
                    1,  # 1 decimal places
                )

                util.addAllNum2dict(
                    cp,
                    d,
                    [
                        # CO2 production by process in g
                        'CO2_roast',
                        'CO2_preheat',
                        'CO2_bbp',
                        'CO2_cooling',
                        # total CO2 production per batch
                        'CO2_batch',
                    ],
                    None,  # no min limit
                    None,  # no max limit
                    3,  # 3 decimal places
                    factor=1
                    / 1000,
                    # CO2 data is forwarded in kg (instead of
                    # the Artisan internal g)
                )
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

        if aw.qmc.plus_store:
            d['location'] = aw.qmc.plus_store
        else:
            d['location'] = None
        if aw.qmc.plus_coffee:
            d['coffee'] = aw.qmc.plus_coffee
        else:
            d[
                'coffee'
            ] = None
            # we need to explicitly add empty selections otherwise
            # the coffee cannot be deleted from the online record
        if aw.qmc.plus_blend_spec and aw.qmc.plus_coffee is None:
            d['blend'] = trimBlendSpec(aw.qmc.plus_blend_spec)
        else:
            d[
                'blend'
            ] = None
            # we need to explicitly add empty selections otherwise
            # the coffee cannot be deleted from the online record

        # ensure that location is None if neither coffee nor blend is set
        if (
            d['coffee'] is None
            and d['blend'] is None
            and d['location'] is not None
        ):
            d['location'] = None

        try:
            util.addString2dict(p, 'roastingnotes', d, 'notes', 1023)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

        if aw.qmc.backgroundprofile:
            bp = aw.qmc.backgroundprofile
            template = getTemplate(bp,background=True)
            d['template'] = template

        # if profile is already saved, that modification date is send along to
        # the server instead the timestamp
        # of the moment the record is queued
        if aw.curFile is not None:
            mod_date:Optional[float] = util.getModificationDate(aw.curFile)
            if mod_date is not None:
                d['modified_at'] = util.epoch2ISO8601(mod_date)

    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
        return {}
    return d


################
# Sync Record (roast properties sync bidirectional between
# the client and the server)

# the following data items are suppressed from the roast record if they have 0
# values to avoid sending just tags with zeros:
sync_record_zero_supressed_attributes: List[str] = [  #for Python >= 3.9 can replace 'List' with the generic type hint 'list'
    'density_roasted',
    'batch_number',
    'batch_pos',
    'whole_color',
    'ground_color',
    'moisture',
    'temperature',
    'pressure',
    'humidity',
    'roastersize',
    'roasterheating',
    # ENERGY DATA
    # energy consumption by source type in BTU
    'BTU_ELEC',
    'BTU_LPG',
    'BTU_NG',
    # energy consumption by process in BTU
    'BTU_roast',
    'BTU_preheat',
    'BTU_bbp',
    'BTU_cooling',
    # total energy consumption per batch
    'BTU_batch',
    # CO2 production by process in g
    'CO2_roast',
    'CO2_preheat',
    'CO2_bbp',
    'CO2_cooling',
    # total CO2 production per batch
    'CO2_batch',
]

# the following data items are suppressed from the roast record if they hold the empty string
# to avoid sending just tags with empty strings:
sync_record_empty_string_supressed_attributes: List[str] = [  #for Python >= 3.9 can replace 'List' with the generic type hint 'list'
    'label',
    'batch_prefix',
    'color_system',
    'machine',
    'notes',
]

sync_record_non_supressed_attributes: List[str] = [  #for Python >= 3.9 can replace 'List' with the generic type hint 'list'
    'roast_id',
    'location',
    'coffee',
    'blend',
    'amount',
    'end_weight',
]

# all roast record attributes that participate in the sync process
sync_record_attributes: List[str] = (  #for Python >= 3.9 can replace 'List' with the generic type hint 'list'
    sync_record_non_supressed_attributes
    + sync_record_zero_supressed_attributes
    + sync_record_empty_string_supressed_attributes
)


# returns the current plus record and a hash over the plus record
# if applied, r is assumed to contain the complete roast data as returned
# by roast.getRoast()
def getSyncRecord(r: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], str]:  #for Python >= 3.9 can replace 'Dict' and 'Tuple' with the generic type hints 'dict' and 'tuple'
    _log.debug('getSyncRecord()')
    m = hashlib.sha256()
    d: Dict[str, Any] = {}
    try:
        if r is None:
            r = getRoast()
        # we take only the value of attributes to be synced back
        for a in sync_record_attributes:
            if a in r:
                d[a] = r[a]
                m.update(str(r[a]).encode('utf-8'))
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    _log.debug('getSyncRecord d -> %s', d)
    return d, m.hexdigest()
