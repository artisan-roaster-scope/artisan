#
# ABOUT
# Utilities
#
# COPYRIGHT (C) 2010-2026 The artisan team represented by
#   Marko Luther <marko.luther@gmx.net> (maintainer) and all contributors
#
# LICENSE
# This program or module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# MAINTAINER
# Marko Luther, 2026
#
# AUTHOR
# Marko Luther, 2023

import warnings
import codecs
import logging
import platform
import sys
import math
import os
import io
import re
import ast
import numpy
import functools
import datetime
from bisect import bisect_right
from pathlib import Path
from matplotlib import colors
from collections.abc import Iterator, Callable
from typing import Final, Literal, Any, TypeGuard, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from artisanlib.main import Artisan # pylint: disable=unused-import
    import numpy.typing as npt # pylint: disable=unused-import
    from artisanlib.atypes import ProfileData # pylint: disable=unused-import
    from proto import artisan_roast_pb2 # pylint: disable=unused-import


##

_log: Final[logging.Logger] = logging.getLogger(__name__)

# don't update any of those as they are used to find the app settings
application_name: Final[str] = 'Artisan'
application_viewer_name: Final[str] = 'ArtisanViewer'
application_organization_name: Final[str] = 'artisan-scope'
application_organization_domain: Final[str] = 'artisan-scope.org'
application_desktop_file_name: Final[str] = 'org.artisan_scope.artisan'


from PyQt6.QtCore import Qt, QStandardPaths, QCoreApplication, QTime, QDate, QDateTime
from PyQt6.QtGui import QColor


deltaLabelPrefix:Final[str] = '<html>&Delta;&thinsp;</html>' # prefix constant for labels to compose DeltaET/BT by prepending this prefix to ET/BT labels
deltaLabelUTF8:Final[str] = 'Delta' if platform.system() == 'Linux' else '\u0394\u2009' # u("\u03B4") # prefix for non HTML Qt Widgets like QPushbuttons

deltaLabelBigPrefix:Final[str] = ('<b>&Delta;</b>&thinsp;' if platform.system() == 'Linux' else '<big><b>&Delta;</b></big>&thinsp;') # same as above for big/bold use cases
deltaLabelMathPrefix:Final[str] = r'$\Delta\/$'  # prefix for labels in matplibgraphs to compose DeltaET/BT by prepending this prefix to ET/BT labels



@functools.lru_cache
def appFrozen() -> bool:
    ib = False
    try:
        platf = str(platform.system())
        if platf == 'Darwin':
            # the sys.frozen is set by py2app and pyinstaller and is unset otherwise
            if getattr( sys, 'frozen', False ):
                ib = True
        elif platf == 'Windows':
            ib = hasattr(sys, 'frozen')
        elif platf == 'Linux' and getattr(sys, 'frozen', False):
            # The application is frozen
            ib = True
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)
    return ib

@functools.lru_cache
def signature_message(version:str, revision:str, artisan_os:str) -> bytes:
    return bytes(f'{version}{revision}{artisan_os}', encoding='ascii')

##

def replace_umlauts(text: str) -> str:
    """replace special German umlauts (vowel mutations) from text."""
    vowel_char_map = {
        ord('ä'): 'ae', ord('ü'): 'ue', ord('ö'): 'oe', ord('ß'): 'ss',
        ord('Ä'): 'Ae', ord('Ü'): 'Ue', ord('Ö'): 'Oe'
    }
    return text.translate(vowel_char_map)

def to_ascii(s:str) -> str:
    from unidecode import unidecode
    return unidecode(replace_umlauts(s))

##

# returns empty string for values out of the valid Unicode range
def uchr(x:int) -> str:
    try:
        return chr(x)
    except ValueError:
        return ''

def decodeLocal(x:Any) -> str|None:
    if x is not None:
        try:
            return codecs.unicode_escape_decode(x)[0]
        except Exception: # pylint: disable=broad-except
            return None
    return None
def decodeLocalStrict(x:Any|None, default:str = '') -> str:
    if x is None:
        return default
    try:
        return codecs.unicode_escape_decode(x)[0]
    except Exception: # pylint: disable=broad-except
        return default
def encodeLocal(x:Any|None) -> str|None:
    if x is not None:
        try:
            return codecs.unicode_escape_encode(str(x))[0].decode('utf8')
        except Exception: # pylint: disable=broad-except
            return None
    return None
def encodeLocalStrict(x:Any|None, default:str = '') -> str:
    if x is None:
        return default
    try:
        return codecs.unicode_escape_encode(str(x))[0].decode('utf8')
    except Exception: # pylint: disable=broad-except
        return default
def hex2int(h1:int, h2:int|None = None) -> int:
    if h2 is not None:
        return int(h1*256 + h2)
    return int(h1)

# str2cmd converts string to bytes ignoring all non-ascii characters. Result to be used for low-level device communication.
def str2cmd(s:str) -> bytes:
    return s.encode('ascii', errors='ignore')
def cmd2str(c:bytes) -> str:
    return str(c,'latin1')
def s2a(s:str) -> str:
    return str2cmd(s).decode('ascii')

# returns True if x is not None, not NaN and not the error value -1 or 0
def is_proper_temp(x:None|int|float) -> bool:
    return x is not None and not numpy.isnan(x) and x not in [0, -1, float('-inf'), float('inf')]

# returns the prefix of length ll-1 of s and adds Unicode ellipsis character
# the length of the resulting string is max(1, ll, len(s))
def abbrevString(s:str, ll:int) -> str:
    if len(s) > ll:
        return f'{s[:max(0,ll-1)]}\u2026'
    return s

# used to convert time from int seconds to string (like in the LCD clock timer). input int, output string xx:xx
@functools.lru_cache(maxsize=100)
def stringfromseconds(seconds_raw:float, leadingzero:bool = True) -> str:
    sep = ':'
    if abs(seconds_raw)>60*60:
        seconds_raw /= 60
        sep = 'h'
    # seconds = int(round(seconds_raw)) # note that round(1.5)=round(2.5)=2
    seconds = int(math.floor(seconds_raw + 0.5))
    if seconds >= 0:
        d, m = divmod(seconds, 60)
        if leadingzero:
            return f'{d:02d}{sep}{m:02d}'
        return f'{d:d}{sep}{m:02d}'
    #usually the timex[timeindex[0]] is already taken away in seconds before calling stringfromseconds()
    negtime = abs(seconds)
    d, m = divmod(negtime, 60)
    if leadingzero:
        return f'-{d:02d}{sep}{m:02d}'
    return f'-{d:d}{sep}{m:02d}'

# Converts a string into a seconds integer. Use for example to interpret times from Roaster Properties Dlg inputs
# accepted formats: "00:00","-00:00"
# raises ValueError or IndexError on invalid inputs
@functools.lru_cache(maxsize=100)
def stringtoseconds(string:str) -> int:
    timeparts = string.split(':') # mm:ss
    hours:bool = False
    if len(timeparts) != 2:
        timeparts = string.split('h') # hh:mm
        if len(timeparts) != 2:
            raise ValueError(f"the string '{string}' is not a properly formatted time string of format xx:xx or -xx:xx or xxhxx or -xxhxx")
        hours = True
    if timeparts[0][0] != '-':  #if number is positive
        seconds = int(timeparts[1])
        seconds += int(timeparts[0])*60
        if hours:
            seconds *= 60
        return seconds
    seconds = int(timeparts[0])*60
    seconds -= int(timeparts[1])
    if hours:
        seconds *= 60
    return seconds    #return negative number

def fromFtoCstrict(Ffloat:float) -> float:
    if Ffloat == -1:
        return Ffloat
    return (Ffloat-32.0)*(5.0/9.0)

def fromFtoC(Ffloat:float|None) -> float|None:
    if Ffloat is None or Ffloat == -1 or numpy.isnan(Ffloat):
        return Ffloat
    return fromFtoCstrict(Ffloat)

def fromCtoFstrict(Cfloat:float) -> float:
    if Cfloat == -1:
        return Cfloat
    return (Cfloat*9.0/5.0)+32.0

def fromCtoF(Cfloat:float|None) -> float|None:
    """Converts Celsius to Fahrenheit
    >>> fromCtoF(-1)
    -1
    >>> fromCtoF(None)
    None
    >>> fromCtoF(32)
    89.6
    """
    if Cfloat is None or Cfloat == -1 or numpy.isnan(Cfloat):
        return Cfloat
    return fromCtoFstrict(Cfloat)

def RoRfromCtoFstrict(CRoR:float) -> float:
    if CRoR == -1:
        return CRoR
    return CRoR*9.0/5.0

def RoRfromCtoF(CRoR:float|None) -> float|None:
    if CRoR is None or CRoR == -1 or numpy.isnan(CRoR):
        return CRoR
    return RoRfromCtoFstrict(CRoR)

def RoRfromFtoCstrict(FRoR:float) -> float:
    if FRoR == -1:
        return FRoR
    return FRoR*(5.0/9.0)

def RoRfromFtoC(FRoR:float|None) -> float|None:
    if FRoR is None or FRoR == -1 or numpy.isnan(FRoR):
        return FRoR
    return RoRfromFtoCstrict(FRoR)

def convertRoR(r:float|None, source_unit:Literal['C', 'F'], target_unit:Literal['C', 'F']) -> float|None:
    if source_unit == target_unit:
        return r
    if source_unit == 'C':
        return RoRfromCtoF(r)
    return RoRfromFtoC(r)

def convertRoRstrict(r:float, source_unit:Literal['C', 'F'], target_unit:Literal['C', 'F']) -> float:
    if source_unit == target_unit:
        return r
    if source_unit == 'C':
        return RoRfromCtoFstrict(r)
    return RoRfromFtoCstrict(r)

def convertTemp(t:float, source_unit:str, target_unit:str) -> float:
    if source_unit in ('', target_unit) or target_unit == '':
        return t
    if source_unit == 'C':
        return fromCtoFstrict(t)
    return fromFtoCstrict(t)

# See https://discuss.python.org/t/pathname2url-changes-in-python-3-14-breaking-pip-tests/97091
# for changes to urllib in Pyton3.14
def path2url(path:str) -> str:
    import urllib.parse as urllib_urlparse  # @Reimport
    import urllib.request as urllib_request  # @Reimport
    return urllib_urlparse.urljoin(
      'file://', urllib_request.pathname2url(path))

# remaining artifacts from Qt4/5 compatibility layer:
# note: those conversion functions are sometimes called with string arguments
# thus a simple int(round(s)) won't work and a int(round(float(s))) needs to be applied
# float('inf') and float('-inf') cannot be converted to integer and are mapped to 0
def toInt(x:int|str|float|None) -> int:
    if x is None:
        return 0
    try:
        return int(round(float(x)))
    except Exception: # pylint: disable=broad-except
        return 0

def toString(x:Any) -> str:
    return str(x)

def toList(x:Any) -> list[Any]:
    if x is None:
        return []
    return list(x)

def toFloat(x:Any) -> float:
    if x is None:
        return 0.
    try:
        return float(x)
    except Exception: # pylint: disable=broad-except
        return 0.

def toBool(x:Any) -> bool:
    if isinstance(x,str):
        x_lower = x.lower()
        if x_lower in {'yes', 'true', 't', '1'}:
            return True
        if x_lower in {'no', 'false', 'f', '0'}:
            return False
        try:
            return bool(eval(x[:100])) # pylint: disable=eval-used
        except Exception: # pylint: disable=broad-except
            return False
    return bool(x)

def toStringList(x:list[Any]) -> list[str]:
    if x:
        return [str(s) for s in x]
    return []

# turns all integer values to floats in recursive list/dict structures
def rec_int_to_float(data:Any) -> Any:
    if isinstance(data, int):
        return float(data)
    if isinstance(data, dict):
        data_copy = data.copy()
        for k, v in data_copy.items():
            data_copy[k] = rec_int_to_float(v)
        return data_copy
    if isinstance(data, list):
        return [rec_int_to_float(v) for v in data]
    return data

def removeAll(ll:list[str], s:str) -> None:
    for _ in range(ll.count(s)):  # @UndefinedVariable
        ll.remove(s)

# fills in intermediate interpolated values replacing -1 values based on surrounding values
# [1, 2, 3, -1, -1, -1, 10, 11] => [1, 2, 3, 4.75, 6.5, 8.25, 11]
# [1,2,3,-1,-1,-1,-1] => [1,2,3,-1,-1,-1,-1] # no final value to interpolate too, so trailing -1 are kept!
# [-1,-1,2] => [2, 2, 2] # a prefix of -1 of max length 'interpolate_max' will be replaced by the first value in l that is not -1
# INVARIANT: the resulting list has always the same length as l
# only gaps of length interpolate_max (should be set to the global aw.qmc.interpolatemax), if not None, are interpolated
def fill_gaps(ll:'Sequence[float|int]|npt.NDArray[numpy.floating[Any]]', interpolate_max:int=3) -> list[float]:
    res:list[float] = []
    last_val:float = -1
    skip:int = -1
    for i,e in enumerate(ll):
        if i >= skip:
            if i == 0 and e == -1 and last_val == -1: # only for the prefix
                # a prefix of -1 will be replaced by the first value in ll that is not -1
                s:float = -1
                for ee in ll[:5]:
                    if ee != -1:
                        s = float(ee)
                        break
                res.append(s)
                last_val = s
            elif e == -1 and last_val != -1:
                next_val = None
                next_idx = None # first index of an element beyond i of a value different to -1
                for j in range(i+1,len(ll)):
                    if ll[j] != -1:
                        next_val = ll[j]
                        next_idx = j
                        break
                if next_val is None or next_idx is None:
                    # no further valid values, we append the tail
                    res.extend(ll[i:])
                    return res
                if interpolate_max < (next_idx - i):
                    # gap too big
                    res.extend(ll[i:next_idx])
                else:
                    # gap small enough, we interpolate
                    # compute intermediate values
                    step = (next_val - last_val) / (next_idx-i+1.)
                    for _ in range(next_idx-i):
                        last_val = last_val + step
                        res.append(last_val)
                skip = next_idx
            else:
                fe = float(e)
                res.append(fe)
                last_val = fe
    return res

def replace_duplicates(data:list[float]) -> list[float]:
    lv:float = -1
    data_core:list[float] = []
    max_eliminations: Final[int] = 20
    for v in data:
        if v == lv and not all(val == -1 for val in data_core[-(min(max_eliminations,len(data_core))):]):
            # replace by -1, only if the previous max_eliminations once were not replaced
            data_core.append(-1)
        else:
            data_core.append(v)
            lv = v
    # reconstruct first and last reading
    if len(data)>0:
        data_core[-1] = data[-1]
    return fill_gaps(data_core, interpolate_max=100)

# we store data in the user- and app-specific local default data directory
# for the platform
# note that the path is based on the ApplicationName and OrganizationName
# setting of the app
# eg. ~/Library/Application Support/artisan-scope/Artisan (macOS)
#     C:\Users\<USER>\AppData\Local\artisan-scope\Artisan (Windows)
#     ~/.local/share/artisan-scope/Artisan (Linux)
#     ~/.var/app/org.artisan_scope.artisan/data/artisan-scope/Artisan/artisan.log (Linux if installed via Flatpack)

# getDataDirectory() returns the Artisan data directory
# if app is not yet initialized None is returned
# otherwise the path is computed on first call and then memorized
# if the computed path does not exists it is created
# if creation or access of the path fails None is returned and memorized
def getDataDirectory() -> str|None:
    app = QCoreApplication.instance()
    return _getAppDataDirectory(app)

# internal function to return
@functools.cache
def _getAppDataDirectory(app:'Artisan') -> str|None:
    # temporarily switch app name to Artisan (as it might be artisanViewer)
    appName = app.applicationName()
    app.setApplicationName(application_name)
    data_dir = QStandardPaths.standardLocations(
        QStandardPaths.StandardLocation.AppLocalDataLocation
    )[0]
    app.setApplicationName(appName)
    try:
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        return data_dir
    except Exception:  # pylint: disable=broad-except
        return None


# getDocumentsDirectory() returns the Documents directory of the users account
# if app is not yet initialized None is returned
# otherwise the path is computed on first call and then memorized
# if the computed path does not exists it is created
# if creation or access of the path fails None is returned and memorized
def getDocumentsDirectory() -> str|None:
    app = QCoreApplication.instance()
    return _getAppDocumentsDirectory(app)

# internal function to return
@functools.cache
def _getAppDocumentsDirectory(app:'Artisan') -> str|None:
    # temporarily switch app name to Artisan (as it might be ArtisanViewer)
    appName = app.applicationName()
    app.setApplicationName(application_name)
    data_dir = QStandardPaths.standardLocations(
        QStandardPaths.StandardLocation.DocumentsLocation
    )[0]
    app.setApplicationName(appName)
    try:
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        return data_dir
    except Exception:  # pylint: disable=broad-except
        return None


@functools.cache
def getAppPath() -> str:
    platf = platform.system()
    if platf in {'Darwin','Linux'}:
        if appFrozen():
            return QCoreApplication.applicationDirPath() + '/../../../'
        return os.path.dirname(os.path.realpath(__file__)) + '/../'
    if platf == 'Windows':
        if appFrozen():
            return os.path.dirname(sys.executable) + '\\'
        return os.path.dirname(os.path.realpath(__file__)) + '\\..\\'
    return QCoreApplication.applicationDirPath() + '/'

@functools.cache
def getResourcePath() -> str:
    platf = platform.system()
    if platf == 'Darwin':
        if appFrozen():
            return QCoreApplication.applicationDirPath() + '/../Resources/'
        return os.path.dirname(os.path.realpath(__file__)) + '/../includes/'
    if platf == 'Linux':
        if appFrozen():
            return QCoreApplication.applicationDirPath() + '/'
        return os.path.dirname(os.path.realpath(__file__)) + '/../includes/'
    if platf == 'Windows':
        if appFrozen():
            return os.path.dirname(sys.executable) + '\\'
        return os.path.dirname(os.path.realpath(__file__)) + '\\..\\includes\\'
    return QCoreApplication.applicationDirPath() + '/'

# if share is True, the same (cache) file is shared between the Artisan and
# ArtisanViewer apps
# and locks have to be used to avoid race conditions
def getDirectory(filename: str, ext: str|None = None, share: bool = False) -> str:
    fn = filename
    if not share:
        app = QCoreApplication.instance()
        if app is not None and app.artisanviewerMode: # type:ignore[attr-defined]
            fn = filename + '_viewer'
    dd = getDataDirectory()
    fp = Path(('' if dd is None else dd), fn)
    if ext is not None:
        fp = fp.with_suffix(ext)
    try:
        fp = (
            fp.resolve()
        )  # older pathlib raise an exception if a path does not exist
    except Exception:  # pylint: disable=broad-except
        pass
    return str(fp)


# standard/MPL hex color strings append alpha information to the end, while QColor assumes the alpha information in color name strings at the begin

# converts QColor ARGB names to a standard/MPL hex color strings with alpha values at the end
@functools.lru_cache(maxsize=50)
def argb_colorname2rgba_colorname(c:str) -> str:
    if len(c) == 9 and c[0] == '#':
        return f'#{c[3:9]}{c[1:3]}'
    return c

# converts standard/MPL hex color strings to QColor ARGB names with alpha at the begin
@functools.lru_cache(maxsize=50)
def rgba_colorname2argb_colorname(c:str) -> str:
    if len(c) == 9 and c[0] == '#':
        return f'#{c[7:9]}{c[1:7]}'
    return c

# takes a hex color string and returns the same color as hex string with staturation set to 0 and incr. lightness
@functools.lru_cache(maxsize=50)
def toGrey(color:str) -> str:
    h, _s, l, a = QColor(rgba_colorname2argb_colorname(color)).getHslF()
    gray = QColor.fromHslF(h,0,(1-l)/1.7+l,a) # saturation set to 0
    if len(color) == 9:
        return gray.name(QColor.NameFormat.HexArgb)
    return gray.name(QColor.NameFormat.HexRgb)

# takes a hex color string and returns the same color as hex string with reduced staturation and incr. lightness
@functools.lru_cache(maxsize=50)
def toDim(color:str) -> str:
    h, s, l, a = QColor(rgba_colorname2argb_colorname(color)).getHslF()
    gray = QColor.fromHslF(h,s/4,(1-l)/1.7+l,a)
    if len(color) == 9:
        return gray.name(QColor.NameFormat.HexArgb)
    return gray.name(QColor.NameFormat.HexRgb)

# creates QLinearGradient style from light to dark by default, or from dark to light if reverse is True
@functools.cache
def createGradient(rgb:QColor|str, tint_factor:float = 0.1, shade_factor:float = 0.1, reverse:bool = False, left_to_right:bool = False) -> str:
    light_grad,dark_grad = createRGBGradient(rgb,tint_factor,shade_factor)
    if reverse:
        # dark to light
        if left_to_right:
            return f'QLinearGradient(x1:0,y1:0,x2:1,y2:0,stop:0 {dark_grad}, stop:1 {light_grad})'
        return f'QLinearGradient(x1:0,y1:0,x2:0,y2:1,stop:0 {dark_grad}, stop:1 {light_grad})'
    # light to dark (default)
    if left_to_right:
        return f'QLinearGradient(x1:0,y1:0,x2:1,y2:0,stop:0 {light_grad}, stop:1 {dark_grad})'
    return f'QLinearGradient(x1:0,y1:0,x2:0,y2:1,stop:0 {light_grad}, stop:1 {dark_grad})'

# NOTE: for now alpha values of the rgb argument are ignored and resulting colors are RGB without alphas
def createRGBGradient(rgb:QColor|str, tint_factor:float = 0.3, shade_factor:float = 0.3) -> tuple[str,str]:
    try:
        rgb_tuple: tuple[float, float, float]
        if isinstance(rgb, QColor):
            r,g,b,_ = rgb.getRgbF()
            rgb_tuple = (r,g,b)
        elif rgb[0:1] == '#':   # hex input like "#ffaa00"
            rgb_tuple = (float(int(rgb[1:3], 16)/255),float(int(rgb[3:5], 16)/255),float(int(rgb[5:7], 16)/255))
        else:                 # color name
            rgb_tuple = colors.hex2color(colors.cnames[rgb])
        #ref: https://stackoverflow.com/questions/6615002/given-an-rgb-value-how-do-i-create-a-tint-or-shade
        r,g,b = tuple(int(255 * (x * (1 - shade_factor))) for x in rgb_tuple)
        darker_rgb = f'#{r:02x}{g:02x}{b:02x}'
        r,g,b = tuple(int(255 * (x + (1 - x) * tint_factor)) for x in rgb_tuple)
        lighter_rgb = f'#{r:02x}{g:02x}{b:02x}'
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)
        lighter_rgb = darker_rgb = '#000000'
    return lighter_rgb,darker_rgb


# Networking

# returns True if the given ip:port can be connected to
def isOpen(ip: str, port: int) -> bool:
    import socket
    timeout = 0.3 # timeout in seconds
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((ip, port)) == 0
    except Exception as e: # pylint: disable=broad-except
        _log.info(e)
    return False


# Logging

@functools.cache
def getLoggers() -> list[logging.Logger]:
    return [logging.getLogger(name) for name in logging.root.manager.loggerDict if '.' not in name]  # @UndefinedVariable pylint: disable=no-member

def debugLogLevelActive() -> bool:
    try:
        return logging.getLogger('artisanlib').isEnabledFor(logging.DEBUG)
    except Exception: # pylint: disable=broad-except
        return False

def setDeviceDebugLogLevel(state: bool) -> None:
    if state:
        # debug logging on
        logging.getLogger('pymodbus.logging').setLevel(logging.DEBUG)
        logging.getLogger('pymodbus.client').setLevel(logging.DEBUG)
        _log.info('device debug logging ON')
    else:
        # debug logging off
        logging.getLogger('pymodbus.logging').setLevel(logging.ERROR)
        _log.info('device debug logging OFF')

def setDebugLogLevel(state: bool) -> None:
    if state:
        # debug logging on
        setFileLogLevels(logging.DEBUG, ['artisanlib', 'plus'])
        _log.info('debug logging ON')
    else:
        # debug logging off
        setFileLogLevels(logging.INFO, ['artisanlib', 'plus'])
        _log.info('debug logging OFF')

def setFileLogLevel(logger: logging.Logger, level:int) -> None:
    logger.setLevel(level)
    for handler in logger.handlers:
        if handler.get_name() == 'file':
            handler.setLevel(level)

def setFileLogLevels(level:int, logger_names:list[str]) -> None:
    loggers = getLoggers()
    for logger in loggers:
        if logger.name in logger_names:
            setFileLogLevel(logger, level)

# returns True if new log level of loggers is DEBUG, False otherwise
def debugLogLevelToggle() -> bool:
    newDebugLevel = not debugLogLevelActive()
    setDebugLogLevel(newDebugLevel)
    return newDebugLevel

def natsort(s:str) -> list[int|str]:
    return [int(t) if t.isdigit() else t.casefold() for t in re.split(r'(\d+)', s)]

#convert number to string and auto set the number of decimal places 0, 0.999, 9.99, 999.9, 9999
def scaleFloat2String(num:float|str) -> str:
    n = toFloat(num)
    if n == 0:
        return '0'
    if abs(n) < 10:
        return f'{n:.3f}'.rstrip('0').rstrip('.')
    if abs(n) >= 1000:
        return f'{n:.0f}'
    if abs(n) >= 100:
        return f'{n:.1f}'.rstrip('0').rstrip('.')
    return f'{n:.2f}'.rstrip('0').rstrip('.')


# for use in widgets that expects a double via a self.createCLocalDoubleValidator that accepts both,
# one dot and several commas. If there is no dot, the last comma is interpreted as decimal separator and the others removed
# if there is a dot, the last one is used as a decimal separator and all other comma and dots are removed.
# Trailing dots are removed as well.
def comma2dot(s:str) -> str:
    s = s.strip()
    last_dot = s.rfind('.')
    last_pos = s.rfind(',')
    if last_dot > -1 and (last_pos == -1 or last_dot > last_pos): # there is no comma after that last dot
        if last_dot + 1 == len(s):
            # this is just a trailing dot, we remove this and all other dots and commas
            return s.replace(',','').replace('.','')
        # we just keep this one and remove all other comma and dots; we also remove trailing zero decimals
        return s[:last_dot].replace(',','').replace('.','') + s[last_dot:].replace(',','').rstrip('0').rstrip('.')
    # there is no dot in the string
    if last_pos > -1:
        if last_pos + 1 == len(s):
            # this is just a trailing comma, we remove this and all other dots and commas
            return s.replace(',','').replace('.','')
        # we turn the last comma into a dot and remove all others; we also remove trailing zero decimals
        return s[:last_pos].replace(',','').replace('.','') + '.' + s[last_pos+1:].rstrip('0').rstrip('.')
    return s


#--- weight / volume

weight_units:Final[tuple[str,str,str,str]] = ('g','Kg','lb','oz')
weight_units_lower:Final[tuple[str,str,str,str]] = ('g','kg','lb','oz') # just for display use
volume_units:Final[tuple[str,str,str,str,str,str]] = ('l','gal','qt','pt','cup','ml')

def weightVolumeDigits(v:float) -> int:
    v = abs(v)
    if v >= 1000:
        return 1
    if v >= 100:
        return 2
    if v >= 10:
        return 3
    return 4


def round_base(x:float, base:int = 5) -> int:
    return base * round(x/base)


def float2floatWeightVolume(v:float) -> float:
    d = weightVolumeDigits(v)
    return float2float(v,d)


# the int n specifies the number of digits
def float2floatNone(f:float|None, n:int=1) -> float|None:
    if f is None:
        return None
    return float2float(f,n)

# the int n>=0 specifies the number of digits
# returns 0 if f is not a number
@functools.lru_cache(maxsize=500)
def float2float(f:float|str, n:int=1) -> float:
    n = max(n, 0)
    f = float(f)
    if n==0:
        if math.isnan(f):
            return 0
        return int(round(f))
    res:float = float(f'%.{n}f'%f)
    if math.isnan(res):
        return 0.0
    return res

# removes trailing zeros like f'{n:g}'
def float2str(n:float) -> str:
    return f'{n}'.rstrip('0').rstrip('.')

# i/o: 0:g, 1:Kg, 2:lb (pound), 3:oz (ounce)
def convertWeight(v:float, i:int, o:int) -> float:
    #                g,                         kg,                     lb,                  oz,
    convtable:list[list[float]] = [
                    [1.,                        0.001,                  2.20462262185/1000,  (2.20462262185*16) / 1000],  # g
                    [1000,                      1.,                     2.20462262185,       2.20462262185*16],           # kg
                    [1/(2.20462262185/1000),    1/2.20462262185,        1.,                  16.],                        # lb
                    [1000 / (2.20462262185*16), 1/(2.20462262185*16),   1/16,                1.]                          # oz
                ]
    if 0 <= i < len(convtable) and 0 <= o < len(convtable):
        return v*convtable[i][o]
    raise IndexError(f'index error in convertWeight({v},{i},{o})')

# i/o: 0:l (liter), 1:gal (gallons US), 2:qt, 3:pt, 4:cup, 5:cm^3/ml
def convertVolume(v:float, i:int, o:int) -> float:
                    #liter          gal             qt              pt              cup             ml/cm^3
    convtable:list[list[float]] = [
                    [1.,            0.26417205,     1.05668821,     2.11337643,     4.22675284,     1000.                ],    # liter
                    [3.78541181,    1.,             4.,             8.,             16,             3785.4117884         ],    # gallon
                    [0.94635294,    0.25,           1.,             2.,             4.,             946.352946           ],    # quart
                    [0.47317647,    0.125,          0.5,            1.,             2.,             473.176473           ],    # pint
                    [0.23658823,    0.0625,         0.25,           0.5,            1.,             236.5882365          ],    # cup
                    [0.001,         2.6417205e-4,   1.05668821e-3,  2.11337641e-3,  4.2267528e-3,   1.                   ]     # cm^3
                ]
    if 0 <= i < len(convtable) and 0 <= o < len(convtable):
        return v*convtable[i][o]
    raise IndexError(f'index error in convertVolume({v},{i},{o})')


# takes a weight, its weight unit index, and a weight unit target index (decides over metric vs imperial)
# and returns a string rendering the weight with unit, potentially adjusted by its magnitude
# with weight_unit_index:
#         0 => g
#         1 => kg
#         2 => lb
#         3 => oz
# if brief is set to 0 (default 0), 3 decimals are returned for lb/kg and 2 for oz/g, if brief > 0 the number of decimals is reduced by that value and
# the rendering might loose precision
# with smart_unit_upgrade (default True), a weight like 1600g is rendered more readable as 1.6kg (but leaves 1610g and 1601g as is)
@functools.lru_cache(maxsize=100)
def render_weight(amount:float, weight_unit_index:int, target_unit_idx:int,
        right_to_left_lang:bool = False, brief:int=0, smart_unit_upgrade:bool=True) -> str:
    w = convertWeight(
        amount, weight_unit_index, target_unit_idx
    )  # @UndefinedVariable
    if w < 1 and target_unit_idx == 1: # requested target unit: kg (unit downgrade: kg -> g)
        # we convert kg to the smaller unit g for readability despite requested target is kg as weight < 1kg
        w = convertWeight(
            amount, weight_unit_index, 0
        )  # @UndefinedVariable
        target_unit = weight_units[
            0
        ]  # @UndefinedVariable
    elif w >= 1000000 and target_unit_idx == 0: # requested target unit: g (unit upgrade: g -> t)
        # we convert kg to tonnes
        w = w / 1000000.0
        target_unit = 't'
    elif (w >= 10000 or (w >= 1000 and brief > 0)) and target_unit_idx == 0: # requested target unit: g (unit upgrade: g -> kg)
        # we convert g to the larger unit kg for readability
        w = convertWeight(
            amount, weight_unit_index, 1
        )  # @UndefinedVariable
        target_unit = weight_units[
            1
        ]  # @UndefinedVariable
    elif smart_unit_upgrade and w >= 1000 and target_unit_idx == 0: # requested target unit: g (unit smart upgrade: g -> kg)
        # if w is between 1000 and 10000 and has no decimals and at least two 0 we render more readable as kg (eg. 1600g => 1.6kg)
        # but 1601g => 1601g (not 1.601kg) and 1610g => 1610g (not 1.61kg as this is not shorter or easier to read)
        ws = str(float2float(w,1)).split('.')
        if len(ws[0].rstrip('0')) < 3 and (len(ws)<2 or ws[1] == '0'):
            w = convertWeight(
                amount, weight_unit_index, 1
            )  # @UndefinedVariable
            target_unit = weight_units[
                1
            ]  # @UndefinedVariable
        else:
            target_unit = weight_units[
                target_unit_idx
            ]  # @UndefinedVariable
    elif (w >= 10000 or (w >= 1000 and brief > 0)) and target_unit_idx == 1: # requested target unit: kg (unit upgrade: kg -> t)
        # we convert kg to tonnes
        w = w / 1000.0
        target_unit = 't'
    elif smart_unit_upgrade and w >= 1000 and target_unit_idx == 1: # requested target unit: kg (unit smart upgrade: kg -> t)
        # if w is between 1000 and 10000 and has no decimals and at least two 0 we render more readable as t (eg. 1600kg => 1.6t)
        # but 1601kg => 1601kg (not 1.601t) and 1610kg => 1610kg (not 1.61t as this is not shorter or easier to read)
        ws = str(float2float(w,1)).split('.')
        if len(ws[0].rstrip('0')) < 3 and (len(ws)<2 or ws[1] == '0'):
            w = w / 1000.0
            target_unit = 't'
        else:
            target_unit = weight_units[
                target_unit_idx
            ]  # @UndefinedVariable
    elif w >= 20000 and target_unit_idx == 2: # requested target unit: lb (unit upgrade: lb -> t)
        # we convert lbs to tonnes
        w = w / 2000.0
        target_unit = 't'  # US tons
    elif smart_unit_upgrade and w >= 2000 and target_unit_idx == 2: # requested target unit: lb (unit smart upgrade: lb -> t)
        # if w is between 2000 and 20000 and has no decimals and at least two 0 we render more readable as t (eg. 2600lb => 1.3t)
        # but 2601lb => 2601lb (not 1.3005t) and 2610lb => 2610lb (not 1.305t as this is not shorter or easier to read and more precise)
        ws = str(float2float(w,1)).split('.')
        if len(ws[0].rstrip('0')) < 3 and (len(ws)<2 or ws[1] == '0'):
            w = w / 2000.0
            target_unit = 't'
        else:
            target_unit = weight_units[
                target_unit_idx
            ]  # @UndefinedVariable
    elif smart_unit_upgrade and w < 1 and target_unit_idx == 2: # requested target unit: lb (unit downgrade: lb -> oz)
        # we convert lb to the smaller unit oz, only if smart_unit_upgrade is set, for readability despite requested target is lb as weight < 1lb
        w = convertWeight(
            amount, weight_unit_index, 3
        )  # @UndefinedVariable
        target_unit = weight_units[
            3
        ]  # @UndefinedVariable
    elif w >= 1600 and target_unit_idx == 3: # requested target unit: oz
        if w >= 32000:
            # we convert oz to US tonnes
            w = w / 32000.0
            target_unit = 't'  # US tons
        else:  # 32000 > w >= 1600 # 16oz == 1lb
            # we convert oz to lb
            w = w / 16.0
            target_unit = 'lb'
    else:
        target_unit = weight_units[
            target_unit_idx
        ]  # @UndefinedVariable

    decimals = 0 if w>=100 else 1
    if target_unit not in ['g', 'oz']:
        decimals += 2
    if brief > 0:
        decimals = max(0, decimals-brief)
    w = float2float(w,decimals)
    return (f'{target_unit.lower()}{w:g}' if right_to_left_lang else f'{w:g}{target_unit.lower()}')


# typing tools

def is_int_list(xs: list[Any]) -> TypeGuard[list[int]]:
    return all(isinstance(x, int) and not isinstance(x, bool) for x in xs) # bool is a subclass of int!

def is_float_list(xs: list[Any]) -> TypeGuard[list[float]]:
    return all(isinstance(x, float) for x in xs)


# locale tools

def right_to_left(locale:str) -> bool:
    return locale.casefold() in {'ar', 'fa', 'he'}


# others

# fast variant based on binary search on lists using bisect (using numpy.searchsorted is slower)
# side-condition: values in self.timex in linear order
# time: time in seconds
# nearest: if nearest is True the closest index is returned (slower), otherwise the previous (faster)
# returns
#   -1 on empty timex
#    0 if time smaller than first entry of timex
#  len(timex)-1 if time larger than last entry of timex (last index)
def timearray2index(timearray:list[float], time:float, nearest:bool = True) -> int:
    i = bisect_right(timearray, time)
    if i:
        if nearest and i>0 and (i == len(timearray) or abs(time - timearray[i]) > abs(time - timearray[i-1])):
            return i-1
        return i
    return -1


def findTPint(timeindex:list[int], timex:list[float], temp:list[float]) -> int:
    TP:float = 1000
    idx:int = 0
    start:int = 0
    end:int = len(timex)
    # try to consider only indices until the roast end and not beyond
    EOR_index = end
    if timeindex[6]:
        EOR_index = timeindex[6]
    if start < EOR_index < end:
        end = EOR_index
    # try to consider only indices until FCs and not beyond
    FCs_index = end
    if timeindex[2]:
        FCs_index = timeindex[2]
    if start < FCs_index < end:
        end = FCs_index
    # try to consider only indices from start of roast on and not before
    SOR_index = start
    if timeindex[0] != -1:
        SOR_index = timeindex[0]
    if start < SOR_index < end:
        start = SOR_index
    for i in range(end - 1, start -1, -1):
        if temp[i] > 0 and temp[i] < TP:
            TP = temp[i]
            idx = i
    return idx

@functools.lru_cache(maxsize=30)
def eventtime2string(time:float) -> str:
    if time == 0.0:
        return ''
    di,mo = divmod(time,60)
    return f'{di:02.0f}:{mo:02.0f}'


# eventsvalues maps the given internal event value v to an external event int value as displayed to the user as special event value
# historicaly internal event values ranged from [1-11] and external event values from [0-10]
#   that range was extended to 0-100 in later Artisan versions
# v is expected to be float value of range [-11.0,11.0] or None (interpreted as 0)
# negative values are not used as event values, but as step arguments in extra button definitions
#   11.0 => 100
#   10.1 => 91
#   10.0 => 90
#   1.1 => 1
#   1.0 => 0
#   0.5 => 0
#     0 => 0
#  -1.0 => 0
#  -1.1 => -1
# -10.0 => -90
# -10.1 => -91
# -11.0 => -100
### NOTE: This one is "LINKED" by a staticmethod for compatibility in canvas.py:tgraphcanvas()
def events_internal_to_external_value(v:float|None) -> int:
    if v is None:
        return 0
    if -1.0 <= v <= 1.0:
        return 0
    if v < -1.0:
        return -(int(round(abs(v)*10)) - 10)
    return int(round(v*10)) - 10

# the inverse of events_internal_to_external_value, converting an external to an internal event value
# v from [-100,100]
### NOTE: This one is "LINKED" by a staticmethod for compatibility in canvas.py:tgraphcanvas()
def events_external_to_internal_value(v:int) -> float:
    if v == 0:
        return 0.
    if v >= 1:
        return v/10. + 1.
    return v/10. - 1.


### curve smoothing


# smoothes a list (or numpy.array) of values 'y' at taken at times indicated by the numbers in list 'x'
# 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
# 'flat' results in moving average
# window_len should be odd
# based on http://wiki.scipy.org/Cookbook/SignalSmooth
# returns a smoothed numpy array or the original y argument
def smooth(x:'npt.NDArray[numpy.floating]', y:'npt.NDArray[numpy.float64]', window_len:int = 15, window:str = 'hanning') -> 'npt.NDArray[numpy.floating]':
    try:
        if len(x) == len(y) and len(x) > 1:
            if window_len > 2:
                # smooth curves
                #s = numpy.r_[2*x[0]-y[window_len:1:-1],y,2*y[-1]-y[-1:-window_len:-1]]
                #s=numpy.r_[y[window_len-1:0:-1],y,y[-2:-window_len-1:-1]]
                #s = y
                s = numpy.r_[y[window_len-1:0:-1],y,y[-1:-window_len:-1]]
                if window == 'flat': #moving average
                    w = numpy.ones(window_len,'d')
                else:
                    w = eval('numpy.'+window+'(window_len)') # pylint: disable=eval-used
                try:
                    ys = numpy.convolve(w/w.sum(), s, mode='valid')
                except Exception: # pylint: disable=broad-except
                    return y
                hwl = int(window_len/2)
                res = ys[hwl:-hwl]
                if len(res)+1 == len(y) and len(res) > 0:
                    try:
                        return ys[hwl-1:-hwl] # zuban:ignore[return-value,no-any-return,unused-ignore]
                    except Exception: # pylint: disable=broad-except
                        return y
                elif len(res) != len(y):
                    return y
                return res # zuban:ignore[return-value,no-any-return,unused-ignore]
            return y
        return y
    except Exception as ex: # pylint: disable=broad-except
        _log.exception(ex)
        return x


# https://gist.github.com/bhawkins/3535131
def medfilt(x:'npt.NDArray[numpy.double]', k:int) -> 'npt.NDArray[numpy.double]':
    """Apply a length-k median filter to a 1D array x.
    Boundaries are extended by repeating endpoints.
    """
    assert k % 2 == 1, 'Median filter length must be odd.'
    assert x.ndim == 1, 'Input must be one-dimensional.'
    if len(x) == 0:
        return x
    k2 = (k - 1) // 2
    y = numpy.zeros ((len (x), k), dtype=x.dtype)
    y[:,k2] = x
    for i in range (k2):
        j = k2 - i
        y[j:,i] = x[:-j]
        y[:j,i] = x[0]
        y[:-j,-(i+1)] = x[j:]
        y[-j:,-(i+1)] = x[-1]
    return numpy.median(y, axis=1)
#    return numpy.nanmedian(y, axis=1) # produces artefacts

# re-sample, filter and smooth slice
# takes numpy arrays a (time) and b (temp) of the same length and returns a numpy array representing the processed b values
# precondition: (filter_dropouts or window_len>2)
def smooth_slice(a:'npt.NDArray[numpy.double]', b:'npt.NDArray[numpy.float64]',
    window_len:int = 7, window:str = 'hanning', decay_weights:list[int]|None = None, decay_smoothing:bool = False,
    re_sample:bool = True, back_sample:bool = True, a_lin:'npt.NDArray[numpy.double]|None' = None,
    medfilt_factor:int = 3,
    filter_dropouts:bool=False) -> 'npt.NDArray[numpy.double]':
    a_mod:npt.NDArray[numpy.floating]
    # 1. re-sample
    if re_sample:
        if a_lin is None or len(a_lin) != len(a):
            a_mod = cast(numpy.ndarray[tuple[Literal[1]]], numpy.linspace(a[0],a[-1],len(a)))
        else:
            a_mod = a_lin
        b = cast(numpy.ndarray[Any], numpy.interp(a_mod, a, b)) # resample data to linear spaced time
    else:
        a_mod = a
    res:npt.NDArray[numpy.floating] = b # just in case the precondition (filter_dropouts or window_len>2) does not hold

    # 2. filter spikes (only applied offline)
    if filter_dropouts:
        try:
#            if self.flagon:
#                online_medfilt = LiveMedian(median_filter_factor)
#                b = numpy.array(list(map(online_medfilt, b)))
            bb = medfilt(b, medfilt_factor)
#            #scipyernative which performs equal, but produces larger artefacts at the borders and for intermediate NaN values for k>3
#            from scipy.signal import medfilt as scipy_medfilt
#            b = scipy_medfilt(b,3)
            res = bb
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            res = b
    # 3. smooth data
    if window_len>2:
        if decay_smoothing:
            # decay smoothing
            decay_weights_internal:npt.NDArray[numpy.int_]
            if decay_weights is None:
                decay_weights_internal = numpy.arange(1,window_len+1)
            else:
                window_len = len(decay_weights)
                decay_weights_internal = numpy.array(decay_weights)
            # invariant: window_len = len(decay_weights_internal)
            if decay_weights_internal.sum() == 0:
                res = b
            else:
                result:list[float] = []
                # ignore -1 readings in averaging and ensure a good ramp
                for i, v in enumerate(b):
                    seq = b[max(0,i-window_len + 1):i+1]
                    w = decay_weights_internal[max(0,window_len-len(seq)):]  # preCond: len(decay_weights_internal)=window_len and len(seq) <= window_len; postCond: len(w)=len(seq)
                    if len(w) == 0:
                        # we don't average if there is are no weights (e.g. if the original seq did only contain -1 values and got empty)
                        result.append(v)
                    else:
                        result.append(float(numpy.average(seq,axis=0,weights=w))) # works only if len(seq) = len(w)
                res = numpy.array(result)
                # postCond: len(res) = len(b)
        else:
            # optimal smoothing (the default)
            win_len = max(0,window_len)
            # at the lowest level we turn smoothing completely off
            res = (smooth(a_mod, b, win_len, window) if win_len != 1 else b)
    # 4. sample back
    if re_sample and back_sample:
        res = cast(numpy.ndarray[Any], numpy.interp(a, a_mod, res)) # pyright:ignore[reportUnknownArgumentType] # re-sampled back to original timestamps
    return numpy.array(res).astype(numpy.double)


# takes lists a (time array) and b (temperature array) containing invalid segments of -1/None values and returns a list with all segments of valid values smoothed
# a: list of timestamps
# b: list of readings
# re_sample: if true re-sample readings to a linear spaced time before smoothing
# back_sample: if true results are back-sampled to original timestamps given in "a" after smoothing
# a_lin: pre-computed linear spaced timestamps of equal length than a
# result is a numpy array or the b as numpy array with drop out readings -1 replaced by NaN if replace_error_value is set
def smooth_list(
        aa:'npt.NDArray[numpy.double]|npt.NDArray[numpy.floating]|Sequence[float]',
        b:'npt.NDArray[numpy.double]|npt.NDArray[numpy.floating]|Sequence[float]',
        window_len:int = 7,
        window:str = 'hanning',
        decay_weights:list[int]|None = None,
        decay_smoothing:bool = False,
        fromIndex:int = -1,
        toIndex:int = 0,
        re_sample:bool = True,
        back_sample:bool = True,
        a_lin:'npt.NDArray[numpy.double]|None' = None,
        medfilt_factor:int = 3,
        filter_dropouts:bool=False,
        replace_error_values:bool=True) -> 'npt.NDArray[numpy.double]':
    if len(aa) > 1 and len(aa) == len(b) and (filter_dropouts or window_len>2):
        #pylint: disable=E1103
        # 1. truncate
        if fromIndex > -1: # if fromIndex is set, replace prefix up to fromIndex by None
            if toIndex==0: # no limit
                toIndex=len(aa)
        else: # smooth list on full length
            fromIndex = 0
            toIndex = len(aa)
        a = numpy.array(aa[fromIndex:toIndex], dtype=numpy.double)
        # we mask the error value -1 and Numpy  in the temperature array
        mb:numpy.ndarray[tuple[Literal[1]],numpy.dtype[numpy.float64]] = cast(numpy.ndarray[tuple[Literal[1]],numpy.dtype[numpy.float64]], numpy.ma.masked_equal(b[fromIndex:toIndex], -1))
        # split in masked and
        unmasked_slices = [(x,False) for x in numpy.ma.clump_unmasked(mb)] # type:ignore[no-untyped-call,attr-defined,unused-ignore] # the valid readings
        masked_slices = [(x,True) for x in numpy.ma.clump_masked(mb)]  # type:ignore[no-untyped-call,attr-defined,unused-ignore] # the dropped values
        sorted_slices = sorted(unmasked_slices + masked_slices, key=lambda tup: tup[0].start) # pyright:ignore[reportUnknownArgumentType] # pyright: ignore[reportGeneralTypeIssues]
        b_smoothed:list[npt.NDArray[numpy.double]] = [] # pyright:ignore[reportUnknownArgumentType] # b_smoothed collects the smoothed segments in order
        b_smoothed.append(numpy.full(fromIndex, numpy.nan, dtype=numpy.double)) # pyright:ignore[reportUnknownArgumentType] # append initial segment to the list of resulting segments
        # we just smooth the unmsked slices and add the unmasked slices with NaN values
        for (s, m) in sorted_slices:
            if m:
                # a slice with all masked (invalid) readings
                b_smoothed.append(numpy.full(s.stop - s.start, numpy.nan, dtype=numpy.double)) # pyright:ignore[reportUnknownArgumentType]
            else:
                # a slice with proper data
                b_smoothed.append(smooth_slice(a[s], mb[s], window_len, window, decay_weights, decay_smoothing, re_sample, back_sample, a_lin,
                    medfilt_factor, filter_dropouts)) # pyright:ignore[reportUnknownArgumentType]
        b_smoothed.append(numpy.full(len(a)-toIndex, numpy.nan, dtype=numpy.double)) # append the final segment to the list of resulting segments
        bb = numpy.concatenate(b_smoothed)
    else:
        bb = numpy.array(b, dtype=numpy.double)
    if replace_error_values:
        bb[bb == -1] = numpy.nan
    else:
        bb[numpy.isnan(bb)] = -1
    return bb


### RoR computation

# computes the RoR over the time and temperature arrays tx and temp via polynoms of degree 1 at index i using a window of wsize
# the window size wsize needs to be at least 1 (two succeeding readings)
def polyRoR(tx:'npt.NDArray[numpy.double]', temp:'npt.NDArray[numpy.double]', wsize:int, i:int) -> float:
    if i == 0: # we duplicate the first possible RoR value instead of returning a 0
        i = 1
    if 0 < i < min(len(tx), len(temp)):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            left_index = max(0,i-wsize)
            LS_fit = numpy.polynomial.polynomial.polyfit(tx[left_index:i+1],temp[left_index:i+1], 1)
            return float(LS_fit[1]*60.)
    else:
        return 0

# with window size wsize=1 the RoR is computed over succeeding readings; tx and temp assumed to be of type numpy.array
def arrayRoR(tx:'npt.NDArray[numpy.double]', temp:'npt.NDArray[numpy.double]', wsize:int) -> 'npt.NDArray[numpy.floating]': # with wsize >=1
    # length compensation done downstream, not necessary here!
    with warnings.catch_warnings():
        # suppress warning if time difference is 0 which leads to a div by zero resulting in a warning and an inf value
        warnings.simplefilter('ignore')
        return (temp[wsize:] - temp[:-wsize]) / ((tx[wsize:] - tx[:-wsize])/60.)

# returns deltas and linearized timex;  both results can be None
# timex: the time array
# temp: the temperature array
# ds: the number of delta samples
# optimal_smoothing: use offline optimal smoothing algorithm (like a Savgol filter)
# timex_lin: the linearized time array or None
# delta_filter: delta filter setting
# roast_start_idx: the index of CHARGE
# roast_end_idx: the index of DROP
# polyfit_ror: use the polyfit RoR algorithm (if optimal_smoothing is set => Savgol filter)
# medfilt_factor: median filter factor
# filter_dropouts: if set dropouts are filtered out
# limit_ror: if set the resulting RoR is limited
# ror_limit_min: lower RoR limit
# ror_limit_max: upper RoR limit
# delta_symbolic_function: the symbolic function to be applied to the delta or None
# RTsname: the symbolic variable name of the delta (assigned for eval_math_expression)
# eval_math_expression: if given, this function is applied to each ror reading

# result is a numpy array or the b as numpy array which may contain NaN
def computeDeltas(
        timex:'npt.NDArray[numpy.double]',
        temp:'list[float]|npt.NDArray[numpy.double]|None',
        ds:int,
        optimal_smoothing:bool,
        timex_lin:'npt.NDArray[numpy.double]|None',
        delta_filter:int,
        roast_start_idx:int,
        roast_end_idx:int,
        polyfit_ror:bool,
        medfilt_factor:int,
        filter_dropouts:bool,
        limit_ror:bool,
        ror_limit_min:int,
        ror_limit_max:int,
        replace_error_values:bool = True,
        RTsname:str = '',
        delta_symbolic_function:str = '',
        eval_math_expression:Callable[[str,float,str,float], float]|None = None
        ) -> tuple[list[float|None]|None, 'npt.NDArray[numpy.double]|None']:
    if temp is not None:
        z1:npt.NDArray[numpy.floating]
        with numpy.errstate(divide='ignore'):
            lt = len(timex)
            ntemp = numpy.array([0 if x is None else x for x in temp]) # pyright: ignore[reportGeneralTypeIssues]
            if optimal_smoothing and polyfit_ror:
                # optimal RoR computation using polynoms with out timeshift
                dss = ds + 1 if ds % 2 == 0 else ds
                if len(ntemp) > dss:
                    try:
                        # ntemp is not linearized yet:
                        lin: npt.NDArray[numpy.double]
                        if timex_lin is None or len(timex_lin) != len(ntemp):
                            lin = numpy.linspace(timex[0],timex[-1],lt)
                        else:
                            lin = timex_lin
                        ntemp_lin = cast(numpy.ndarray[Any], numpy.interp(lin, timex, ntemp)) # pyright:ignore[reportUnknownArgumentType] # resample data in ntemp to linear spaced time
                        dist:float = (lin[-1] - lin[0]) / (len(lin) - 1) # pyright:ignore[reportUnknownArgumentType]
                        from scipy.signal import savgol_filter # type # ignore # @Reimport
                        z1 = savgol_filter(ntemp_lin, dss, 1, deriv=1, delta=dss)
                        z1 = z1 * (60./dist) * dss
                    except Exception: # pylint: disable=broad-except
                        # a numpy/OpenBLAS polyfit bug can cause polyfit to throw an exception "SVD did not converge in Linear Least Squares" on Windows Windows 10 update 2004
                        # https://github.com/numpy/numpy/issues/16744
                        # original version just picking the corner values:
                        z1 = arrayRoR(timex,ntemp,ds)
                else:
                    # in this case we use the standard algo
                    try:
                        # variant using incremental polyfit RoR computation
                        z1 = numpy.array([polyRoR(timex,ntemp,ds,i) for i in range(len(ntemp))])
                    except Exception: # pylint: disable=broad-except
                        # a numpy/OpenBLAS polyfit bug can cause polyfit to throw an exception "SVD did not converge in Linear Least Squares" on Windows Windows 10 update 2004
                        # https://github.com/numpy/numpy/issues/16744
                        # original version just picking the corner values:
                        z1 = arrayRoR(timex,ntemp,ds)
            elif polyfit_ror:
                try:
                    # variant using incremental polyfit RoR computation
                    z1 = numpy.array([polyRoR(timex,ntemp,ds,i) for i in range(len(ntemp))]) # windows size ds needs to be at least 2
                except Exception: # pylint: disable=broad-except
                    # a numpy/OpenBLAS polyfit bug can cause polyfit to throw an exception "SVD did not converge in Linear Least Squares" on Windows Windows 10 update 2004
                    # https://github.com/numpy/numpy/issues/16744
                    # original version just picking the corner values:
                    z1 = arrayRoR(timex,ntemp,ds)
            else:
                z1 = arrayRoR(timex,ntemp,ds)

        ld1 = len(z1) # pyright:ignore[reportUnknownArgumentType]
        # make lists equal in length
        if lt > ld1:
            z1 = numpy.append([z1[0] if ld1 else 0.]*(lt - ld1),z1) # pyright:ignore[reportUnknownArgumentType]
        # apply smybolic formula
        if delta_symbolic_function and eval_math_expression is not None and len(z1) == len(timex): # pyright:ignore[reportUnknownArgumentType]
            try:
                z1 = numpy.array([eval_math_expression(delta_symbolic_function, timex[i], RTsname, d) for i,d in enumerate(z1.tolist())]) # pyright:ignore[reportUnknownArgumentType]
            except Exception: # pylint: disable=broad-except
                pass
        # apply smoothing
        if optimal_smoothing:
            user_filter = delta_filter
        else:
            user_filter = int(round(delta_filter/2.))
        delta1 = smooth_list(timex,z1,window_len=user_filter,decay_smoothing=(not optimal_smoothing),a_lin=timex_lin, # pyright:ignore[reportUnknownArgumentType]
                        medfilt_factor=medfilt_factor, filter_dropouts=filter_dropouts, replace_error_values=replace_error_values)

        # cut out the part after DROP and before CHARGE and remove values beyond the RoRlimit
        return [
            d if ((roast_start_idx <= i <= roast_end_idx) and (d is not None and (not limit_ror or
                ror_limit_min < d < ror_limit_max)))
            else None
            for i,d in enumerate(delta1)
        ], timex_lin
    return None, timex_lin




### serialize/deserialize


#Write object to file
def serialize(filename:str, obj:dict[str, Any]) -> None:
    fn = str(filename)
    with open(fn, 'w+', encoding='utf-8') as f:
        f.write(repr(obj))


#Read object from file
def deserialize(filename:str) -> dict[str, Any]:
    obj:dict[str,Any] = {}
    try:
        fn = str(filename)
        if os.path.exists(fn):
            with open(fn, encoding='utf-8') as f:
                obj=ast.literal_eval(f.read()) # pylint: disable=eval-used
    except Exception as ex: # pylint: disable=broad-except
        _log.exception(ex)
    return obj



### CSV import/export


def csv_load(csvFile:io.TextIOWrapper) -> 'ProfileData':
    import csv
    profile:ProfileData = {}

    data = csv.reader(csvFile,delimiter='\t')
    #read file header
    header = next(data)
    date = QDate.fromString(header[0].split('Date:')[1],"dd'.'MM'.'yyyy")
    if len(header) > 11:
        try:
            tm = QTime.fromString(header[11].split('Time:')[1])
            profile['roasttime'] = encodeLocalStrict(tm.toString())
            roastdate = QDateTime(date,tm)
        except Exception: # pylint: disable=broad-except
            roastdate = QDateTime(date, QTime())
    else:
        roastdate = QDateTime(date, QTime())
    profile['roastdate'] = encodeLocalStrict(QDate(date).toString())
    profile['roastepoch'] = int(roastdate.toSecsSinceEpoch())
    profile['roasttzoffset'] = 0
    unit = header[1].split('Unit:')[1]
    if unit in {'F', 'C'}:
        profile['mode'] = unit
    #read column headers
    fields = next(data)
    extra_fields = fields[5:] # columns after 'Event'

    timex:list[float] = []
    temp1:list[float] = []
    temp2:list[float] = []

    # add extra devices
    number_extra_devices = min(10, int(len(extra_fields)/2)) # ApplicationWindow.nLCDS = 10
    extradevices:list[int] = [50]*number_extra_devices # type dummy
    extratimex:list[list[float]] = [[] for _ in range(number_extra_devices)] # we don't want exact copies of those empty lists as with [[]]*number_extra_devices!
    extratemp1:list[list[float]] = [[] for _ in range(number_extra_devices)]
    extratemp2:list[list[float]] = [[] for _ in range(number_extra_devices)]
    extraname1:list[str] = ['']*number_extra_devices
    extraname2:list[str] = ['']*number_extra_devices
    extramathexpression1:list[str] = ['']*number_extra_devices
    extramathexpression2:list[str] = ['']*number_extra_devices

    # set extra device names # NOTE: eventuelly we want to set/change the names only for devices that were just added in the line above!?
    for i, ef in enumerate(extra_fields):
        if i % 2 == 1:
            # odd
            extraname2[int(i/2)] = ef
        else:
            # even
            extraname1[int(i/2)] = ef

    #read data
    last_time:float|None = None

    i = 0
    for row in data:
        i = i + 1
        try:
            items = list(zip(fields, row, strict=True))
            item:dict[str,str] = {}
            for (name, value) in items:
                item[name] = value.strip()
            #add one measurement
            timez = float(stringtoseconds(item['Time1']))
            if not last_time or last_time < timez:
                timex.append(timez)
                temp1.append(float(item['ET']))
                temp2.append(float(item['BT']))
                for j, ef in enumerate(extra_fields):
                    if j % 2 == 1:
                        # odd
                        extratemp2[int(j/2)].append(float(item[ef]))
                    else:
                        # even
                        extratimex[int(j/2)].append(timez)
                        extratemp1[int(j/2)].append(float(item[ef]))
            last_time = timez
        except Exception: # pylint: disable=broad-except
            pass # invalid input can make stringtoseconds fail thus this row is ignored

    timeindex:list[int] = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actual index used

    #set events
    CHARGE_entry = header[2].split('CHARGE:')
    if len(CHARGE_entry)>1:
        try:
            CHARGE = stringtoseconds(CHARGE_entry[1])
            if CHARGE >= 0:
                timeindex[0] = max(-1, timearray2index(timex, CHARGE, True))
        except Exception:  # pylint: disable=broad-except
            pass

    for i, l in enumerate(['DRYe:', 'FCs:', 'FCe:', 'SCs:', 'SCe:', 'DROP:', 'COOL:']):
        try:
            label = stringtoseconds(header[i+4].split(l)[1])
            if label > 0:
                timeindex[i+1] = max(0, timearray2index(timex, label, True))
        except Exception:  # pylint: disable=broad-except
            pass

    profile['timex'] = timex
    profile['temp1'] = temp1
    profile['temp2'] = temp2
    profile['extradevices'] = extradevices
    profile['extraname1'] = extraname1
    profile['extraname2'] = extraname2
    profile['extratimex'] = extratimex
    profile['extratemp1'] = extratemp1
    profile['extratemp2'] = extratemp2
    profile['extramathexpression1'] = extramathexpression1
    profile['extramathexpression2'] = extramathexpression2
    profile['timeindex'] = timeindex

    return profile


def exportProfile2CSV(filename:str, profile:'ProfileData') -> bool:
    if all(key in profile for key in [ 'mode', 'timex', 'timeindex', 'temp1', 'temp2', 'roastdate', 'roasttime', 'extratimex' ]) and len(profile['timex']) > 0: # pyright: ignore[reportTypedDictNotRequiredAccess]
        import csv
        timeindex = profile['timeindex'] # pyright: ignore[reportTypedDictNotRequiredAccess]
        timex = profile['timex'] # pyright: ignore[reportTypedDictNotRequiredAccess]
        temp1 = profile['temp1'] # pyright: ignore[reportTypedDictNotRequiredAccess]
        temp2 = profile['temp2'] # pyright: ignore[reportTypedDictNotRequiredAccess]
        extradevices:int = (len(profile['extratimex']) if 'extratimex' in profile else 0) # pyright: ignore[reportTypedDictNotRequiredAccess]
        # make timex zero based
        timex_zero = [tx - timex[0] for tx in timex]
        CHARGE = timex_zero[timeindex[0]] if timeindex[0] > -1 else -1
        TP_index = findTPint(timeindex, timex, temp2)
        TP = timex_zero[TP_index] if TP_index and TP_index < len(timex_zero) else 0.
        DRYe = timex_zero[timeindex[1]] if timeindex[1] and timeindex[1] < len(timex) else 0.
        FCs = timex_zero[timeindex[2]] if timeindex[2] and timeindex[2] < len(timex) else 0.
        FCe = timex_zero[timeindex[3]] if timeindex[3] and timeindex[3] < len(timex) else 0.
        SCs = timex_zero[timeindex[4]] if timeindex[4] and timeindex[4] < len(timex) else 0.
        SCe = timex_zero[timeindex[5]] if timeindex[5] and timeindex[5] < len(timex) else 0.
        DROP = timex_zero[timeindex[6]] if timeindex[6] and timeindex[6] < len(timex) else 0.
        COOL = timex_zero[timeindex[7]] if timeindex[7] and timeindex[7] < len(timex) else 0.
        events:list[tuple[float,str]] = [
            (CHARGE,'CHARGE'),
            (TP,'TP'),
            (DRYe,'DRY End'),
            (FCs,'FCs'),
            (FCe,'FCe'),
            (SCs,'SCs'),
            (SCe,'SCe'),
            (DROP, 'DROP'),
            (COOL, 'COOL'),
        ]
        with open(filename, 'w',newline='',encoding='utf8') as outfile:
            writer= csv.writer(outfile,delimiter='\t')
            writer.writerow([
                'Date:' + QDate.fromString(decodeLocalStrict(profile['roastdate'])).toString("dd'.'MM'.'yyyy"), # pyright: ignore[reportTypedDictNotRequiredAccess]
                'Unit:' + profile['mode'], # pyright: ignore[reportTypedDictNotRequiredAccess]
                'CHARGE:' + (eventtime2string(CHARGE) if CHARGE > 0 else ('' if CHARGE < 0 else '00:00')),
                'TP:' + eventtime2string(TP),
                'DRYe:' + eventtime2string(DRYe),
                'FCs:' + eventtime2string(FCs),
                'FCe:' + eventtime2string(FCe),
                'SCs:' + eventtime2string(SCs),
                'SCe:' + eventtime2string(SCe),
                'DROP:' + eventtime2string(DROP),
                'COOL:' + eventtime2string(COOL),
                'Time:' + QTime.fromString(decodeLocalStrict(profile['roasttime'])).toString()[:-3]]) # pyright: ignore[reportTypedDictNotRequiredAccess]
            headrow:list[str] = (['Time1','Time2','ET','BT','Event'] + functools.reduce(lambda x,y : x + [str(y[0]),str(y[1])],
                    (list(zip(profile['extraname1'][0:extradevices],profile['extraname2'][0:extradevices], strict=True)) if 'extraname1' in profile and 'extraname2' in profile else []),
                    cast(list[str], [])))
            writer.writerow(headrow)
            last_time:str|None = None
            events_set:set[str] = set()
            for i, tx in enumerate(timex_zero):
                if tx >= CHARGE >= 0:
                    di,mo = divmod(tx - CHARGE, 60)
                    time2 = f'{di:02.0f}:{mo:02.0f}'
                else:
                    time2 = ''
                event:str = ''
                for ev in events:
                    if ev[1] not in events_set and (ev[0]!=0 or (ev[1]=='CHARGE' and ev[0]!=-1)) and int(round(tx)) == int(round(ev[0])):
                        event = ev[1]
                        events_set.add(ev[1])
                        break
                di,mo = divmod(tx,60)
                time1 = f'{di:02.0f}:{mo:02.0f}'
                if last_time is None or last_time != time1:
                    extratemps = []
                    if extradevices>0 and 'extratemp1' in profile and 'extratemp2' in profile:
                        for j in range(extradevices):
                            if j < len(profile['extratemp1']) and i < len(profile['extratemp1'][j]):
                                extratemps.append(str(profile['extratemp1'][j][i]))
                            else:
                                extratemps.append('-1')
                            if j < len(profile['extratemp2']) and i < len(profile['extratemp2'][j]):
                                extratemps.append(str(profile['extratemp2'][j][i]))
                            else:
                                extratemps.append('-1')
                    writer.writerow([str(time1),str(time2),str(temp1[i]),str(temp2[i]),str(event)] + extratemps)
                last_time = time1
        return True
    return False


#### roast time

# returns total roast time in seconds based on given timeindex and timex structures or None if data is not extractable
def roast_time(timeindex:list[int], timex:list[float]) -> float|None:
    if len(timex) == 0 or len(timeindex) < 7:
        return None
    starttime = (timex[timeindex[0]] if timeindex[0] != -1 and timeindex[0] < len(timex) else 0)
    endtime = (timex[timeindex[6]] if timeindex[6] > 0  and timeindex[6] < len(timex) else timex[-1])
    return endtime - starttime

# return the total roasting time of the given profile in seconds
def get_total_roast_time_from_profile(profile:'ProfileData') -> float|None:
    if 'timex' in profile and 'timeindex' in profile:
        timeindex = profile['timeindex']
        timex = profile['timex']
        return roast_time(timeindex, timex)
    return None


### register calculations for S7/MODBUS

# splits (sorted) list of registers into list of segments of (first,last) register tuples with maximal length of MAX_REGISTER_SEGMENT
# with last-first < max_register_segment
# ex with max_register_segment = 100:
#  max_blocks([0, 2, 20, 1040, 1105, 1215]) ==> [(0,20), (1040, 1105), (1215, 1215)]
def max_blocks(registers:list[int], max_register_segment:int = 100) -> list[tuple[int,int]]:
    registers_sorted = sorted(registers)
    res:list[tuple[int,int]] = []
    start_register:int|None = None
    last_register:int|None = None
    for register in registers_sorted:
        if start_register is None:
            start_register = register
        elif last_register is not None and register > start_register + max_register_segment - 1:
            res.append((start_register, last_register))
            start_register = register
        last_register = register
    # add the last remaining, not yet appended segment
    if start_register is not None and last_register is not None:
        res.append((start_register, last_register))
    return res

# calculates connected blocks of minimal length from a (unsorted) list of registers as list of pairs of the form (start-register,end-register)
def min_blocks(registers:list[int]) -> list[tuple[int,int]]:
    registers_sorted:list[int] = sorted(registers) # eg. [12392, 12393, 12394, 12462, 12463, 12465]
    # split in successive sequences (eg. gaps = [[12394, 12462], [12463, 12465]])
    gaps:list[list[int]] = [[s, er] for s, er in zip(registers_sorted, registers_sorted[1:], strict=False) if s+1 < er]
    # edges iter returns in sequence [12392, 12394, 12462, 12463, 12465, 12465]
    edges:Iterator[int] = iter(registers_sorted[:1] + sum(gaps, cast(list[int], [])) + registers_sorted[-1:])
    # sequences: eg. [(12392, 12394), (12462, 12463), (12465, 12465)]
    return list(zip(edges, edges, strict=True))



### roast message payload

# returns the profile encoded as roast message protobuf or None
def roast_message(profile:'ProfileData', org_id:str|None = None, machine_id:str|None = None,
        interpolate_drops:bool = True,
        smooth_curves:bool = True,
        curvefilter:int = 3,
        medfilt_factor:int = 3, # has to be uneven
        decay_smoothing_p:bool = False, # False: optimal smoothing
        add_additional_curves:int = 1, # 0:no additional curves, 1:visible additional curves, 2:all additional curves
        rate_of_rise:int = 1, # 0: no RoR curve, 1: only BT RoR, 2: ET and BT RoR
        limit_ror:bool = True,
        ror_limit_min:int = 0,
        ror_limit_max:int = 170,
        delta_span_ET:int = 20, # delta span RoR ET in seconds
        delta_span_BT:int = 20,  # delta span RoR BT in seconds
        medfilt_factor_RoR:int = 3, # has to be uneven
        delta_ET_filter:int = 7,
        delta_BT_filter:int = 7,
        min_sampling_interval:int = 1, # minimal sampling interval in seconds
        seconds_before_charge:int|None = 30, # if None, no data is removed before CHARGE
        seconds_after_drop:int|None = 30, # if None, no data is removed after DROP
        factor:int = 100 # all values in the resulting roast payload are multiplied by this factor
         # NOTE: a factor 10 results in visual steps in the computed RoR curve due to the low y-resolution of the delta axis
        ) -> 'artisan_roast_pb2.Roast|None': # pylint: disable=no-member

    from proto import artisan_roast_pb2 # type:ignore[unused-ignore]
    from scipy.interpolate import interp1d

    # timex
    timex:list[float] = profile.get('timex', [])

    if len(timex)<=0:
        return None

    mode:Final[str] = profile.get('mode', 'C')

    roast:artisan_roast_pb2.Roast = artisan_roast_pb2.Roast() # pylint: disable=no-member
    if org_id is not None:
        roast.org_id = org_id
    if machine_id is not None:
        roast.machine_id = machine_id
    if 'roastUUID' in profile:
        roast.roast_id = profile['roastUUID']

    roast.factor = factor

    # epoch
    # start of recording, corresponding to timex[0]
    # initialized to epoch of now
    roastepoch:int = QDateTime.currentDateTime().toSecsSinceEpoch()
    roastdate:QDateTime|None
    if 'roastepoch' in profile:
        roastepoch = profile['roastepoch']
    elif 'roastisodate' in profile:
        try:
            roastdate = None
            date = QDate.fromString(decodeLocalStrict(profile['roastisodate']),Qt.DateFormat.ISODate)
            if not date.isValid(): # ty:ignore[no-matching-overload]
                date = QDate.currentDate()
            if 'roasttime' in profile:
                try:
                    time = QTime.fromString(decodeLocalStrict(profile['roasttime']))
                    if not time.isValid(): # ty:ignore[no-matching-overload]
                        time = QTime().currentTime()
                    roastdate = QDateTime(date,time)
                except Exception: # pylint: disable=broad-except
                    roastdate = QDateTime(date, QTime())
            if roastdate is not None:
                roastepoch = int(roastdate.toSecsSinceEpoch())
        except Exception: # pylint: disable=broad-except
            pass
    elif 'roastdate' in profile:
        try:
            date = QDate.fromString(decodeLocalStrict(profile['roastdate']))
            if not date.isValid(): # ty:ignore[no-matching-overload]
                date = QDate.currentDate()
            if 'roasttime' in profile:
                try:
                    time = QTime.fromString(decodeLocalStrict(profile['roasttime']))
                    roastdate = QDateTime(date,time)
                except Exception: # pylint: disable=broad-except
                    roastdate = QDateTime(date, QTime())
            else:
                roastdate = QDateTime(date, QTime())
            roastepoch = int(roastdate.toSecsSinceEpoch())
        except Exception: # pylint: disable=broad-except
            pass

    # timeindex
    timeindex:list[int] = [-1,0,0,0,0,0,0,0]
    if 'timeindex' in profile and len(profile['timeindex']) == len(timeindex):
        timeindex = profile['timeindex']

    # samplint interval (we don't trust profile['samplinginterval'])
    tx_diff = numpy.diff(numpy.array(timex[1:])) # we skip the first sample as it might have been delayed/skipped
    sampling_interval = max(min_sampling_interval, int(round(float(numpy.average(tx_diff))))) # sampling interval in seconds

    # remove readings before CHARGE and after DROP
    start_idx:int = 0
    end_idx:int = len(timex)
    if seconds_before_charge is not None and timeindex[0]>-1 and timeindex[0]<len(timex):
        readings_before,_ = divmod(seconds_before_charge,sampling_interval)
        start_idx = max(0,timeindex[0]-readings_before)
    if seconds_after_drop is not None and timeindex[6]>0 and timeindex[6]<len(timex):
        readings_after,_ = divmod(seconds_after_drop,sampling_interval)
        end_idx = min(end_idx, timeindex[6]+readings_after+1)
    # adjust roastepoch (start of recording) by adding the duration removed
    roastepoch += int(round(timex[start_idx] - timex[0]))
    # adjust timex
    timex = timex[start_idx:end_idx]
    # adjust ET
    if 'temp1' in profile:
        profile['temp1'] = profile['temp1'][start_idx:end_idx]
    # adjust BT
    if 'temp2' in profile:
        profile['temp2'] = profile['temp2'][start_idx:end_idx]
    # adjust extra curves timex and temps
    if 'extratimex' in profile:
        profile['extratimex'] = profile['extratimex'][start_idx:end_idx]
    if 'extratemp1' in profile:
        for i,extratemp1 in enumerate(profile['extratemp1']):
            profile['extratemp1'][i] = extratemp1[start_idx:end_idx]
    if 'extratemp2' in profile:
        for i,extratemp2 in enumerate(profile['extratemp2']):
            profile['extratemp2'][i] = extratemp2[start_idx:end_idx]
    # adjust timeindex
    timeindex = [max(0,idx-start_idx) if idx!=0 else idx for idx in timeindex]
    # adjust event indices
    if 'specialevents' in profile:
        profile['specialevents'] = [max(0,idx-start_idx) for idx in profile['specialevents']]


    # resample
    ## 1. make 0 the first timex
    timex = [x - timex[0] for x in timex]
    ## 2. resample tx
    times_a = numpy.array(timex)
    tx_a = cast('npt.NDArray[numpy.double]', numpy.linspace(times_a.min(),times_a.max(),times_a.size))
    timex_resampled = cast('npt.NDArray[numpy.double]', numpy.arange(times_a.min(), times_a.max(), sampling_interval))
    timex_resampled_list:list[float] = list(timex_resampled)
    ## 3. milestones into idx of resampled tx
    timeindex = [-1 if (i == 0 and (idx == -1 or idx >= len(timex))) else (0 if (idx == 0 or idx >= len(timex)) else timearray2index(timex_resampled_list, timex[idx])) for (i, idx) in enumerate(timeindex)]


    # roast start / CHARGE
    last_idx:int = 0
    charge_offset:int = 0 # delta in seconds between time[0] (start of recording; roastepoch) and CHARGE (start of roast)
    if len(timeindex)>0 and timeindex[0]>-1 and len(timex_resampled)>timeindex[0]:
        charge_offset = timex_resampled[timeindex[0]]
        roast.milestones.charge_idx = timeindex[0]
        last_idx = timeindex[0]
    charge_epoch:float = roastepoch + charge_offset # start of recording + charge_offset
    roast.start = datetime.datetime.fromtimestamp(charge_epoch, tz=datetime.UTC) # type:ignore[assignment]

    # DRY END
    if len(timeindex)>1 and timeindex[1]>0 and len(timex_resampled)>timeindex[1]>last_idx:
        roast.milestones.dry_end_idx = timeindex[1]
        last_idx = timeindex[1]

    # FIRST CRACK START
    if len(timeindex)>1 and timeindex[2]>0 and len(timex_resampled)>timeindex[2]>last_idx:
        roast.milestones.first_crack_start_idx = timeindex[2]
        last_idx = timeindex[2]

    # FIRST CRACK END
    if len(timeindex)>1 and timeindex[3]>0 and len(timex_resampled)>timeindex[3]>last_idx:
        roast.milestones.first_crack_end_idx = timeindex[3]
        last_idx = timeindex[3]

    # SECOND CRACK START
    if len(timeindex)>1 and timeindex[4]>0 and len(timex_resampled)>timeindex[4]>last_idx:
        roast.milestones.second_crack_start_idx = timeindex[4]
        last_idx = timeindex[4]

    # SECOND CRACK END
    if len(timeindex)>1 and timeindex[5]>0 and len(timex_resampled)>timeindex[5]>last_idx:
        roast.milestones.second_crack_end_idx = timeindex[5]
        last_idx = timeindex[5]

    # roast end / DROP
    drop_epoch:float = roastepoch + (timex_resampled[-1] - timex_resampled[0])
    if len(timeindex)>6 and timeindex[6]>0 and len(timex_resampled)>timeindex[6]>last_idx:
        # DROP given, relative to CHARGE
        drop_epoch = charge_epoch + max(0, (timex_resampled[timeindex[6]] - timex_resampled[timeindex[0]] if timeindex[0]>-1 else timex_resampled[timeindex[6]] - timex_resampled[0]))
        roast.milestones.drop_idx = timeindex[6]
    elif len(timex)>0:
        # DROP not given, we take last timex reading
        drop_epoch = charge_epoch + max(0, (timex_resampled[-1] - timex_resampled[timeindex[0]] if timeindex[0]>-1 else timex_resampled[-1] - timex_resampled[0]))
    roast.end = datetime.datetime.fromtimestamp(drop_epoch, tz=datetime.UTC) # type:ignore[assignment]


    # times (aligned such that CHARGE is at 0)
    roast.times.extend([int(round(tx - charge_offset)) for tx in timex_resampled])

    # event and annotations
    events:dict[int, list[tuple[int, float]]] = {} # event_type_idx associated to (time_index, value) pairs
    annotations:list[tuple[int, str]] = [] # time_index, tag
    # collect events and annotations
    if 'specialevents' in profile and 'specialeventstype' in profile:
        for i, idx in enumerate(profile['specialevents']):
            if i < len(profile['specialeventstype']) and idx < len(timex):
                event_type = profile['specialeventstype'][i]
                idx_resampled = timearray2index(timex_resampled_list, timex[idx])
                if event_type < 4 and 'specialeventsvalue' in profile and i < len(profile['specialeventsvalue']):
                    # one of the 4 custom event types
                    event_value:float = profile['specialeventsvalue'][i]
                    if event_type in events:
                        events[event_type].append((idx_resampled, event_value))
                    else:
                        events[event_type] = [(idx_resampled, event_value)]
                elif (event_type == 4 and 'specialeventsStrings' in profile and
                        i < len(profile['specialeventsStrings'])):
                    # an event annotation
                    annotations.append((idx_resampled, profile['specialeventsStrings'][i]))
    # add events
    for event_type_idx, event_readings in events.items():
        if len(event_readings)>0:
            new_events = roast.events.add()
            if 'etypes' in profile and event_type_idx < len(profile['etypes']):
                new_events.name = decodeLocalStrict(profile['etypes'][event_type_idx]).strip()
            if ('eventsliderunits' in profile and event_type_idx < len(profile['eventsliderunits']) and
                    profile['eventsliderunits'][event_type_idx].strip() != ''):
                new_events.unit = decodeLocalStrict(profile['eventsliderunits'][event_type_idx]).strip()
            # sort events by index
            event_readings_sorted = sorted(event_readings, key=lambda el: el[0])
            new_events.time_indices.extend([el[0] for el in event_readings_sorted])
            new_events.values.extend([max(0,events_internal_to_external_value(el[1])) for el in event_readings_sorted])
    # add annotations
    if len(annotations)>0:
        # sort events by index
        annotations_sorted = sorted(annotations, key=lambda el: el[0])
        roast.annotations.time_indices.extend([el[0] for el in annotations_sorted])
        roast.annotations.tags.extend([decodeLocalStrict(el[1]).strip() for el in annotations_sorted])

    # reusable timex linspace
    time_lin:numpy.ndarray[tuple[Literal[1]],numpy.dtype[numpy.double]]|None = None
    if timex:
        time_lin = cast(numpy.ndarray[tuple[Literal[1]]], numpy.linspace(timex[0],timex[-1],len(timex)))

    # multiply reading by 10 and round to integer
    def reading2value(x:float|None, factor:int) -> int:
        return (-1 if x is None or x == -1 or math.isnan(x) else int(round(x*factor)))

    # et_values
    et_values = profile.get('temp1',[])
    # same length as times
    et_values = (et_values + [-1]*(len(timex) - len(et_values)))[:len(timex)]
    if mode == 'F':
        et_values = [fromFtoCstrict(et) for et in et_values]
    if interpolate_drops:
        et_values = fill_gaps(et_values)
    if smooth_curves:
        et_values = list(smooth_list(timex,et_values,
            window_len=curvefilter,
            decay_smoothing=decay_smoothing_p,
            a_lin=time_lin,
            medfilt_factor=medfilt_factor,
            filter_dropouts=False, # already filtered above
            replace_error_values=False)) # generate homogeneous list[float], preventing NaN
    # resample and type convert
    roast.et_values.extend([reading2value(x, factor) for x in interp1d(tx_a,numpy.array(et_values),fill_value='extrapolate')(timex_resampled)])

    # bt_values
    bt_values = profile.get('temp2',[])
    # same length as times
    bt_values = (bt_values + [-1]*(len(timex) - len(bt_values)))[:len(timex)]
    if mode == 'F':
        bt_values = [fromFtoCstrict(bt) for bt in bt_values]
    if interpolate_drops:
        bt_values = fill_gaps(bt_values)
    if smooth_curves:
        bt_values = list(smooth_list(timex,bt_values,
            window_len=curvefilter,
            decay_smoothing=decay_smoothing_p,
            a_lin=time_lin,
            medfilt_factor=medfilt_factor,
            filter_dropouts=False, # already filtered above
            replace_error_values=False))# generate homogeneous list[float], preventing NaN
    # resample and type convert
    roast.bt_values.extend([reading2value(x, factor) for x in interp1d(tx_a,numpy.array(bt_values),fill_value='extrapolate')(timex_resampled)])

    # rate-of-rise
    if rate_of_rise:
        # ET RoR
        if rate_of_rise > 1 and len(et_values)>0:
            delta_ET_samples = max(1,int(round(delta_span_ET / sampling_interval)))
            delta_et,_ = computeDeltas(
                numpy.array(timex),
                numpy.array(et_values),
                delta_ET_samples,   # delta span
                True,               # optimal smoothing
                time_lin,
                delta_ET_filter,    # delta filter
                (timeindex[0] if len(timeindex)>0 and timeindex[0]>-1 and len(timex)>timeindex[0] else 0),           # roast_start_idx
                (timeindex[6] if len(timeindex)>6 and timeindex[6]>0 and len(timex)>timeindex[6] else len(timex)-1), # roast_end_idx
                True, # polyfit ror computation (in combination with optimal smoothing this results in the application of the optimal Savgol filter)
                medfilt_factor_RoR, # median filter factor RoR
                False,              # no further dropout filtering
                limit_ror,          # limit RoR
                ror_limit_min,      # min RoR
                ror_limit_max       # max RoR
            )
            if delta_et is not None:
                # resample and type convert
                roast.et_ror_values.extend([reading2value(x, factor) for x in interp1d(tx_a,numpy.array(delta_et),fill_value='extrapolate')(timex_resampled)])
        # BT RoR
        if len(bt_values)>0:
            delta_BT_samples = max(1,int(round(delta_span_BT / sampling_interval)))
            delta_bt,_ = computeDeltas(
                numpy.array(timex),
                numpy.array(bt_values),
                delta_BT_samples,   # delta span
                True,               # optimal smoothing
                time_lin,
                delta_BT_filter,    # delta filter
                (timeindex[0] if len(timeindex)>0 and timeindex[0]>-1 and len(timex)>timeindex[0] else 0),           # roast_start_idx
                (timeindex[6] if len(timeindex)>6 and timeindex[6]>0 and len(timex)>timeindex[6] else len(timex)-1), # roast_end_idx
                True, # polyfit ror computation (in combination with optimal smoothing this results in the application of the optimal Savgol filter)
                medfilt_factor_RoR, # median filter factor RoR
                False,              # no further dropout filtering
                limit_ror,          # limit RoR
                ror_limit_min,      # min RoR
                ror_limit_max,      # max RoR
                False               # don't replace error values -1 by NaN
            )
            if delta_bt is not None:
                # resample and type convert
                roast.bt_ror_values.extend([reading2value(x, factor) for x in interp1d(tx_a,numpy.array(delta_bt),fill_value='extrapolate')(timex_resampled)])

    # additional_curves
    extranames1 = profile.get('extraname1',[])
    extravalues1 = profile.get('extratemp1',[])
    extra_nonetemp_hints1 = profile.get('extraNoneTempHint1',[])
    extra_nonetemp_hints1 += [False]*(len(extranames1) - len(extra_nonetemp_hints1)) # assume temperatures by default
    extra_visibility1 = profile.get('extraCurveVisibility1', [])
    extra_visibility1 += [True]*(len(extranames1) - len(extra_visibility1)) # assume curve visible by default
    #
    extranames2 = profile.get('extraname2',[])
    extravalues2 = profile.get('extratemp2',[])
    extra_nonetemp_hints2 = profile.get('extraNoneTempHint2',[])
    extra_nonetemp_hints2 += [False]*(len(extranames2) - len(extra_nonetemp_hints2)) # assume temperatures by default
    extra_visibility2 = profile.get('extraCurveVisibility2', [])
    extra_visibility2 += [True]*(len(extranames2) - len(extra_visibility2)) # assume curve visible by default
    #
    additional_curves = (list(zip(extranames1, extravalues1, extra_nonetemp_hints1, extra_visibility1, strict=False)) +
        list(zip(extranames2, extravalues2, extra_nonetemp_hints2, extra_visibility2, strict=False)))

    #
    if add_additional_curves:
        for name, readings, none_temp_hint, visible in additional_curves:
            if add_additional_curves == 2 or visible:
                # same length as times
                values = (readings + [-1]*(len(timex) - len(readings)))[:len(timex)]
                if any(v != -1 for v in values):
                    # only add curve is it contains readings
                    if mode == 'F' and not none_temp_hint:
                        values = [fromFtoCstrict(v) for v in values]
                    if interpolate_drops:
                        values = fill_gaps(values)
                    if smooth_curves:
                        values = list(smooth_list(timex,values,
                            window_len=curvefilter,
                            decay_smoothing=decay_smoothing_p,
                            a_lin=time_lin,
                            medfilt_factor=medfilt_factor,
                            filter_dropouts=False, # already filtered above
                            replace_error_values=False))# generate homogeneous list[float], preventing NaN
                    curve = roast.additional_curves.add()
                    curve.name = decodeLocalStrict(name).strip()
                    # resample and type convert
                    curve.values.extend([reading2value(x, factor) for x in interp1d(tx_a,numpy.array(values),fill_value='extrapolate')(timex_resampled)])
                    curve.temperatures = not none_temp_hint

    return roast


def roast_message_to_profile(roast:'artisan_roast_pb2.Roast') -> 'ProfileData': # pylint: disable=no-member
    # adds RoR curves (if available) as extra curves for inspection
    profile:ProfileData = {}

    from google.protobuf.json_format import MessageToDict

    roast_dict = MessageToDict(roast, preserving_proto_field_name=True)

    factor:int = roast_dict.get('factor', 1) # multiplication factor of all payload values

    # milestones
    timeindex:list[int] = [-1,0,0,0,0,0,0,0]
    if 'milestones' in roast_dict:
        milestone_indicies = [
                'charge_idx',
                'dry_end_idx',
                'first_crack_start_idx',
                'first_crack_end_idx',
                'second_crack_start_idx',
                'second_crack_end_idx',
                'drop_idx'
        ]
        for i, idx in enumerate(milestone_indicies):
            if idx in roast_dict['milestones']:
                timeindex[i] = roast_dict['milestones'][idx]
    profile['timeindex'] = timeindex

    specialevents: list[int] = []
    specialeventstype: list[int] = []
    specialeventsvalue: list[float] = []
    specialeventsStrings: list[str] = []
    eventsliderunits: list[str] = []
    etypes: list[str] = []

    # Annotations
    if 'annotations' in roast_dict:
        annotations:dict[str,list[int|str]] = roast_dict.get('annotations', {})
        for ind, tag in zip(
                cast(list[int], annotations.get('time_indices', [])),
                cast(list[str], annotations.get('tags', [])),
                strict=False):
            specialevents.append(ind)
            specialeventstype.append(4)
            specialeventsvalue.append(0)
            specialeventsStrings.append(tag)
    # Events
    if 'events' in roast_dict:
        events:list[dict[str,str|list[int]]] = roast_dict.get('events', [])
        for i, event in enumerate(events[:4]): # max 4 event types
            eventsliderunits.append(cast(str, event.get('unit', '')))
            etypes.append(cast(str, event.get('name', '')))
            for ind, value in zip(
                    cast(list[int], event.get('time_indices', [])),
                    cast(list[int], event.get('values', [])),
                    strict=False):
                specialevents.append(ind)
                specialeventstype.append(int(i))
                specialeventsvalue.append(events_external_to_internal_value(value))
                specialeventsStrings.append('')

    if len(specialevents)>0 and len(specialevents) == len(specialeventstype) == len(specialeventsStrings) == len(specialeventsvalue):
        # sort events by index
        nevents = len(specialevents)
        packed_events:list[tuple[int,int,str,float]] = []
        # pack
        for i in range(nevents):
            packed_events.append(
                (specialevents[i],
                 specialeventstype[i],
                 specialeventsStrings[i],
                 specialeventsvalue[i]))
        # sort
        packed_events_sorted = sorted(packed_events, key=lambda tup: tup[0])
        # unpack
        profile['specialevents'] = [e[0] for e in packed_events_sorted]
        profile['specialeventstype'] = [e[1] for e in packed_events_sorted]
        profile['specialeventsStrings'] = [e[2] for e in packed_events_sorted]
        profile['specialeventsvalue'] = [e[3] for e in packed_events_sorted]
        # add unit and event names
        profile['eventsliderunits'] = (eventsliderunits + ['']*(4 - len(eventsliderunits)))[:4] # exactly 4 units (default '')
        profile['etypes'] = (etypes + ['']*(4- len(etypes)))[:4] + ['--'] # exactly 4 plus a last one '--'

    # divide value by factor
    def value2reading(x:int, factor:int) -> float:
        return (-1 if x == -1 else x/factor)

    #times # shift by time of CHARGE such that first time is 0
    if 'times' in roast_dict:
        times = roast_dict['times']
        if len(times)>0:
            profile['timex'] = [tx-times[0] for tx in times]
            if 'et_values' in roast_dict:
                profile['temp1'] = [value2reading(x, factor) for x in roast_dict['et_values']][:len(times)] + [-1.0]*(len(times) - len(roast_dict['et_values']))
            if 'bt_values' in roast_dict:
                profile['temp2'] = [value2reading(x, factor) for x in roast_dict['bt_values']][:len(times)] + [-1.0]*(len(times) - len(roast_dict['bt_values']))

    if 'start' in roast_dict:
        # start points to the start of the roast (CHARGE)
        profile['roastepoch'] = int(round(datetime.datetime.fromisoformat(roast_dict['start']).timestamp()))


    if 'timex' in profile:

        # correct roastepoch which should point to the start of the recording
        if len(profile['timex']) > 0 and 'roastepoch' in profile:
            profile['roastepoch'] = profile['roastepoch'] + int(round(profile['timex'][0]))

        additional_curves = roast_dict.get('additional_curves',[])
        # make the number of additional curves even
        if len(additional_curves) % 2 != 0:
            additional_curves.append({
                    'name': 'Extra',
                    'values': [-1]*len(profile['timex']),
                    'temperatures': False})
        extradevices:list[int] = []
        extratimex:list[list[float]] = []
        extraname1:list[str] = []
        extraname2:list[str] = []
        extratemp1:list[list[float]] = []
        extratemp2:list[list[float]] = []
        extraCurveVisibility1:list[bool] = []
        extraCurveVisibility2:list[bool] = []
        extraDelta1:list[bool] = []
        extraDelta2:list[bool] = []
        for i, curve in enumerate(additional_curves):
            curve_readings = [value2reading(v, factor) for v in curve.get('values', [-1]*len(profile['timex']))]
            curve_readings = curve_readings[:len(profile['timex'])] + [-1.0]*(len(profile['timex']) - len(curve_readings))
            if i % 2 == 0:
                extraname2.append(curve.get('name', 'Extra'))
                extratemp2.append(curve_readings)
                extraCurveVisibility2.append(True)
                extraDelta2.append(False)
            else:
                extradevices.append(25) # virtual device
                extratimex.append(profile['timex'][:])
                extraname1.append(curve.get('name', 'Extra'))
                extratemp1.append(curve_readings)
                extraCurveVisibility1.append(True)
                extraDelta1.append(False)


        # add RoR curves as extra curves
        bt_ror_values:list[int] = roast_dict.get('bt_ror_values',[])
        if len(bt_ror_values)>0:
            bt_ror_readings:list[float] = [value2reading(v, factor) for v in bt_ror_values]
            bt_ror_readings = bt_ror_readings[:len(profile['timex'])] + [-1.0]*(len(profile['timex']) - len(bt_ror_readings))
            extradevices.append(25) # virtual device
            extratimex.append(profile['timex'][:])
            extraname1.append('BT RoR')
            extratemp1.append(bt_ror_readings)
            extraCurveVisibility1.append(False)
            extraDelta1.append(True)
        et_ror_values:list[int] = roast_dict.get('et_ror_values',[])
        if len(et_ror_values)>0:
            et_ror_readings:list[float] = [value2reading(v, factor) for v in et_ror_values]
            et_ror_readings = et_ror_readings[:len(profile['timex'])] + [-1.0]*(len(profile['timex']) - len(et_ror_readings))
            if len(bt_ror_values)>0:
                # add as extra curve 2
                extraname2.append('ET RoR')
                extratemp2.append(et_ror_readings)
                extraCurveVisibility2.append(False)
                extraDelta2.append(True)
            else:
                # add as extra curve 1
                extradevices.append(25) # virtual device
                extratimex.append(profile['timex'][:])
                extraname1.append('ET RoR')
                extratemp1.append(et_ror_readings)
                extraCurveVisibility1.append(False)
                extraDelta1.append(True)
        elif len(bt_ror_values)>0:
            # add missing extra 2 curve
            extraname2.append('Extra')
            extratemp2.append([-1]*len(profile['timex']))
            extraCurveVisibility2.append(False)
            extraDelta2.append(False)

        profile['extradevices'] = extradevices
        profile['extratimex'] = extratimex
        profile['extraname1'] = extraname1
        profile['extraname2'] = extraname2
        profile['extratemp1'] = extratemp1
        profile['extratemp2'] = extratemp2
        profile['extraCurveVisibility1'] = extraCurveVisibility1
        profile['extraCurveVisibility2'] = extraCurveVisibility2
        profile['extraDelta1'] = extraDelta1
        profile['extraDelta2'] = extraDelta2


    return profile
