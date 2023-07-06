#
# util.py
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

try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtCore import pyqtSlot # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import pyqtSlot # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.util import decodeLocal
from pathlib import Path
from plus import config
import datetime
import dateutil.parser
import logging
import os
import numpy
from typing import Optional, Union, Any, Dict, List, Tuple, TYPE_CHECKING  #for Python >= 3.9: can remove 'List' since type hints can now use the generic 'list'
from typing_extensions import Final  # Python <=3.7

if TYPE_CHECKING:
    from artisanlib.types import ProfileData, ComputedProfileInformation # pylint: disable=unused-import

_log: Final[logging.Logger] = logging.getLogger(__name__)


# Files


# returns the last modification date as EPOCH (float incl. milliseconds) of
# the given file if it exists, or None
def getModificationDate(path:str) -> Optional[float]:
    #    return Path(path).stat().st_mtime
    try:
        return os.path.getmtime(Path(path))
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
        return None


# Timestamps

# given a datetime object returns e.g. '2018-10-12T12:55:12.999Z'
def datetime2ISO8601(dt:datetime.datetime) -> str:
    (dtstr, micro) = dt.strftime('%Y-%m-%dT%H:%M:%S.%f').split('.')
    return f'{dtstr}.{(int(micro) / 1000):03.0f}Z'
#    return '%s.%03dZ' % (dtstr, int(micro) / 1000)

def ISO86012datetime(ts:str) -> datetime.datetime:
    return dateutil.parser.parse(ts)


def datetime2epoch(dt:datetime.datetime) -> float:
    return dt.timestamp()


def epoch2datetime(epoch:float) -> datetime.datetime:
#    return datetime.datetime.utcfromtimestamp(epoch) # considered dangerous!
    return datetime.datetime.fromtimestamp(epoch, tz=datetime.timezone.utc)


# given a epoch returns e.g. '2018-10-12T12:55:12.999Z'
def epoch2ISO8601(epoch:float) -> str:
    return datetime2ISO8601(epoch2datetime(epoch))


def ISO86012epoch(ts:str) -> float:
    return datetime2epoch(ISO86012datetime(ts))


def getGMToffset() -> int:
    try:
        offset = datetime.datetime.now(
            datetime.timezone.utc).astimezone().utcoffset()
        if offset is not None:
            return offset // datetime.timedelta(seconds=1)
    except Exception: # pylint: disable=broad-except
        pass
    return 0


# extra simple information from a dict
# res is assumed to be a dict and the projection result to be a non-empty string or a number
def extractInfo(res:Dict[str,Any], attr: str, default:Optional[Union[str,int,float,List[str]]]) -> Any:
    if attr in res and ((isinstance(res[attr], str) and res[attr] != '') or (isinstance(res[attr],(int, float)))):
        return res[attr]
    return default

# Prepare Temperatures for sending


def fromFtoC(Ffloat: Optional[float]) -> Optional[float]:
    if Ffloat is None or Ffloat == -1 or numpy.isnan(Ffloat):
        return Ffloat
    assert Ffloat is not None
    return (Ffloat - 32.0) * (5.0 / 9.0)


def temp2C(temp: Optional[float],mode:Optional[str] = None) -> Optional[float]:
    if (
        temp is not None and (mode == 'F' or (mode is None and config.app_window is not None and config.app_window.qmc is not None and
            config.app_window.qmc.mode == 'F'))
    ):  # @UndefinedVariable
        return fromFtoC(temp)  # @UndefinedVariable
    return temp

def tempDiff2C(temp: Optional[float]) -> Optional[float]:
    if (
        temp is not None and config.app_window is not None and config.app_window.qmc is not None and
            config.app_window.qmc.mode == 'F'
    ):  # @UndefinedVariable
        if temp in [-1, None] or numpy.isnan(temp):
            return temp
        return temp * 5.0/9.0  # @UndefinedVariable
    return temp


def RoRfromFtoC(Ffloat: Optional[float]) -> Optional[float]:
    if Ffloat is None or Ffloat == -1 or numpy.isnan(Ffloat):
        return Ffloat
    assert Ffloat is not None
    return Ffloat * (5.0 / 9.0)


def RoRtemp2C(temp: Optional[float],mode:Optional[str] = None) -> Optional[float]:
    assert config.app_window is not None
    if (
        temp is not None and (mode == 'F' or (mode is None and config.app_window.qmc.mode == 'F'
    ))):  # @UndefinedVariable
        return RoRfromFtoC(temp)  # @UndefinedVariable
    return temp


# Prepare Floats for sending

# in addition to float2float restricting to n decimals this one returns
# integers if possible
def float2floatMin(fs: Optional[float], n: int = 1) -> Optional[Union[float, int]]:
    if fs is None:
        return None
    assert config.app_window is not None
    f:float = config.app_window.float2float(float(fs), n)  # @UndefinedVariable
    i:int = int(f)
    if f == i:
        return i
    return f


# Prepare numbers for sending
# for numbers out of range None is returned
def limitnum(
    minn: Optional[float], maxn: Optional[float], n: Optional[float]
) -> Optional[float]:
    if (
        n is None
        or (maxn is not None and n > maxn)
        or (minn is not None and n < minn)
    ):
        return None
    return n


# Prepare temperature in C to the interval [-50,1000] for sending
# for numbers out of range None is returned
def limittemp(temp: Optional[float]) -> Optional[float]:
    if temp is None or numpy.isnan(temp) or temp > 1000 or temp < -50:
        return None
    return temp


# Prepare time in s to the interval [0,3600] for sending
# for numbers out of range None is returned
def limittime(tx: Optional[float]) -> Optional[float]:
    if tx is None or numpy.isnan(tx) or  tx > 3600 or tx < 0:
        return None
    return tx


# Prepare text for sending
# text longer than maxlen gets truncated and an eclipse added
def limittext(maxlen: int, s: Optional[str]) -> Optional[str]:
    if s is not None:
        if len(s) > maxlen:
            return f'{s[:maxlen]}..'
        return s
    return s


# Dicts


def addString2dict(dict_source:'ProfileData', key_source:str, dict_target:Dict[str, Any], key_target:str, maxlen:int) -> None:
    if key_source in dict_source and dict_source[key_source]: # type:ignore # TypedDict key must be a string literal; expected one of (
        txt = limittext(maxlen, decodeLocal(dict_source[key_source])) # type:ignore # TypedDict key must be a string literal; expected one of
        if txt is not None:
            dict_target[key_target] = txt


# factor is multiplied to the original value before the min/max calculation
# if min or max is None, the corresponding limit is not enforced, otherwise
# numbers beyond the given limit are replaced by None
# Note: None and 0 values are just dropped and no entry is added
def addNum2dict(
    dict_source:Union['ProfileData', 'ComputedProfileInformation'],
    key_source:str,
    dict_target:Dict[str, Any],
    key_target:str,
    minn:Optional[float],
    maxn:Optional[float],
    digits:int,
    factor:float=1.,
) -> None:
    if key_source in dict_source and dict_source[key_source]: # type: ignore # TypedDict key must be a string literal; expected one of
        n = dict_source[key_source]  # type:ignore # TypedDict key must be a string literal; expected one of
        if n is not None and factor is not None:
            n = n * factor
        n = limitnum(minn, maxn, n)  # may return None
        if n:
            dict_target[key_target] = float2floatMin(n, digits)


# consumes a list of source-target pairs, or just strings used as both source
# and target key, to be processed with add2dict
# factor is multiplied to the original value before the min/max calculation
# if min or max is None, the corresponding limit is not enforced, otherwise
# numbers beyond the given limit are replaced by None
def addAllNum2dict(
    dict_source:Union['ProfileData', 'ComputedProfileInformation'],
    dict_target:Dict[str, Any],
    key_source_target_pairs:List[Union[str, Tuple[str,str]]],
    minn:Optional[float],
    maxn:Optional[float],
    digits:int,
    factor:float=1.,
) -> None:
    for p in key_source_target_pairs:
        if isinstance(p, tuple):
            (key_source, key_target) = p
        else:
            key_source = key_target = p
        addNum2dict(
            dict_source,
            key_source,
            dict_target,
            key_target,
            minn,
            maxn,
            digits,
            factor,
        )


def addTime2dict(dict_source:Union['ProfileData', 'ComputedProfileInformation'], key_source:str, dict_target:Dict[str, Any], key_target:str) -> None:
    if key_source in dict_source and dict_source[key_source]:  # type:ignore # TypedDict key must be a string literal; expected one of
        tx = limittime(dict_source[key_source])  # type:ignore # TypedDict key must be a string literal; expected one of
        if tx is not None:
            dict_target[key_target] = float2floatMin(tx)


# consumes a list of source-target pairs, or just strings used as both source
# and target key, to be processed with add2dict
def addAllTime2dict(dict_source:Union['ProfileData', 'ComputedProfileInformation'], dict_target:Dict[str, Any], key_source_target_pairs:List[Union[str,Tuple[str,str]]]) -> None:
    for p in key_source_target_pairs:
        if isinstance(p, tuple):
            (key_source, key_target) = p
        else:
            key_source = key_target = p
        addTime2dict(dict_source, key_source, dict_target, key_target)


# mode indicates the temperature unit, "C" or "F", of the data if not None
def addTemp2dict(dict_source:Union['ProfileData', 'ComputedProfileInformation'], key_source:str, dict_target:Dict[str, Any], key_target:str, mode:Optional[str]=None) -> None:
    if key_source in dict_source and dict_source[key_source]:  # type:ignore # TypedDict key must be a string literal; expected one of
        temp = limittemp(temp2C(dict_source[key_source],mode))  # type:ignore # TypedDict key must be a string literal; expected one of
        if temp is not None and temp != -1 and not numpy.isnan(temp):
            dict_target[key_target] = float2floatMin(temp)

def addTempDiff2dict(dict_source:Union['ProfileData', 'ComputedProfileInformation'], key_source:str, dict_target:Dict[str, Any], key_target:str) -> None:
    if key_source in dict_source and dict_source[key_source]:  # type:ignore # TypedDict key must be a string literal; expected one of
        temp = limittemp(tempDiff2C(dict_source[key_source]))  # type:ignore # TypedDict key must be a string literal; expected one of
        if temp is not None and temp != -1 and not numpy.isnan(temp):
            dict_target[key_target] = float2floatMin(temp)

# consumes a list of source-target pairs, or just strings used as both source
# and target key, to be processed with add2dict
def addAllTemp2dict(dict_source:Union['ProfileData', 'ComputedProfileInformation'], dict_target:Dict[str, Any], key_source_target_pairs:List[Union[str,Tuple[str,str]]]) -> None:
    for p in key_source_target_pairs:
        if isinstance(p, tuple):
            (key_source, key_target) = p
        else:
            key_source = key_target = p
        addTemp2dict(dict_source, key_source, dict_target, key_target)


# mode indicates the temperature unit, "C" or "F", of the data if not None
def addRoRTemp2dict(dict_source:Union['ProfileData', 'ComputedProfileInformation'], key_source:str, dict_target:Dict[str, Any], key_target:str, mode:Optional[str]=None) -> None:
    if key_source in dict_source and dict_source[key_source]:  # type:ignore # TypedDict key must be a string literal; expected one of
        temp = limittemp(RoRtemp2C(dict_source[key_source],mode))  # type:ignore # TypedDict key must be a string literal; expected one of
        if temp is not None:
            dict_target[key_target] = float2floatMin(temp)


# returns extends dict_target by item with key_target holding the
# dict_source[key_source] value if key_source in dict_source and not empty
def add2dict(dict_source:'ProfileData', key_source:str, dict_target:Dict[str, Any], key_target:str) -> None:
    if key_source in dict_source and dict_source[key_source]:  # type:ignore # TypedDict key must be a string literal; expected one of
        dict_target[key_target] = dict_source[key_source]  # type:ignore # TypedDict key must be a string literal; expected one of


def getLanguage() -> str:
    try:
        if (
            config.app_window is not None
            and config.app_window.plus_account is not None
        ):
            assert isinstance(config.app_window.plus_language, str)
            return config.app_window.plus_language
    except Exception: # pylint: disable=broad-except
        # config.app_window might be still unbound
        pass
    return 'en'


# processing responses

# if rlimit = -1 or rused = -1 or pu = "", no update information is available and the state is not updated
@pyqtSlot(float,float,str,int,list)
def updateLimits(rlimit:float, rused:float, pu:str, notifications:int, machines: List[str]) -> None:  #for Python >= 3.9 can replace 'List' with the generic type hint 'list'
    if config.app_window:
        config.app_window.updateLimits(rlimit, rused, pu, notifications, machines)

# takes the JSON response dict and returns the account state as tuple
# rlimit:float, rused:float, pu:str, notifications:int
def extractAccountState(response: Dict[str,Any]) -> Tuple[float, float, str, int, List[str]]:
    rlimit:float = -1.
    rused:float = -1.
    pu:str = ''
    notifications:int = 0 # unqualified notifications
    machines:List[str] = [] # list of machine names with matching notifications
    try:
        if response:
            if 'ol' in response:
                ol = response['ol']
                if 'rlimit' in ol:
                    rlimit = ol['rlimit']
                if 'rused' in ol:
                    rused = ol['rused']
            if 'pu' in response:
                pu = response['pu']
            if 'notifications' in response:
                notificationDict = response['notifications']
                if 'unqualified' in notificationDict:
                    notifications = notificationDict['unqualified']
                if 'machines' in notificationDict:
                    machines = notificationDict['machines']
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    return rlimit, rused, pu, notifications, machines

@pyqtSlot(dict)
def updateLimitsFromResponse(response: Dict[str,Any]) -> None:
    rlimit,rused,pu,notifications,machines = extractAccountState(response)
    updateLimits(rlimit,rused,pu,notifications,machines)


# Open Web Links


def plusLink() -> str:
    return f'{config.web_base_url}/{getLanguage()}/'


def storeLink(plus_store:str) -> str:
    return f'{config.web_base_url}/{getLanguage()}/stores;id={plus_store}'


def coffeeLink(plus_coffee:str) -> str:
    return f'{config.web_base_url}/{getLanguage()}/coffees;id={plus_coffee}'


def blendLink(plus_blend:str) -> str:
    return f'{config.web_base_url}/{getLanguage()}/blends;id={plus_blend}'


def roastLink(plus_roast:str) -> str:
    return f'{config.web_base_url}/{getLanguage()}/roasts;id={plus_roast}'


def remindersLink() -> str:
    return f'{config.web_base_url}/{getLanguage()}/reminders'
