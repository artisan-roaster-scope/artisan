#
# ABOUT
# Artisan Utilities

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
from bisect import bisect_right
from pathlib import Path
from matplotlib import colors
from typing import Final, Optional, Literal, Dict, Tuple, List, Set, Sequence, Union, Any, TYPE_CHECKING
from typing_extensions import TypeGuard  # Python <=3.10

if TYPE_CHECKING:
    from artisanlib.main import Artisan # pylint: disable=unused-import
    import numpy.typing as npt # pylint: disable=unused-import

from artisanlib.atypes import ProfileData

##

_log: Final[logging.Logger] = logging.getLogger(__name__)

application_name: Final[str] = 'Artisan'
application_viewer_name: Final[str] = 'ArtisanViewer'
application_organization_name: Final[str] = 'artisan-scope'
application_organization_domain: Final[str] = 'artisan-scope.org'
application_desktop_file_name: Final[str] = 'org.artisan_scope.artisan'


try:
    from PyQt6.QtCore import QStandardPaths, QCoreApplication, QTime, QDate, QDateTime # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QColor  # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QStandardPaths, QCoreApplication, QTime, QDate, QDateTime  # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QColor  # type: ignore  # @UnusedImport @Reimport  @UnresolvedImport


deltaLabelPrefix:Final[str] = '<html>&Delta;&thinsp;</html>' # prefix constant for labels to compose DeltaET/BT by prepending this prefix to ET/BT labels
deltaLabelUTF8:Final[str] = 'Delta' if platform.system() == 'Linux' else '\u0394\u2009' # u("\u03B4") # prefix for non HTML Qt Widgets like QPushbuttons

deltaLabelBigPrefix:Final[str] = '<big><b>&Delta;</b></big>&thinsp;<big><b>' # same as above for big/bold use cases
deltaLabelMathPrefix:Final[str] = r'$\Delta\/$'  # prefix for labels in matplibgraphs to compose DeltaET/BT by prepending this prefix to ET/BT labels



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

# returns empty string for values out of the valid Unicode range
def uchr(x:int) -> str:
    try:
        return chr(x)
    except ValueError:
        return ''

def decodeLocal(x:Optional[Any]) -> Optional[str]:
    if x is not None:
        try:
            return codecs.unicode_escape_decode(x)[0]
        except Exception: # pylint: disable=broad-except
            return None
    return None
def decodeLocalStrict(x:Optional[Any], default:str = '') -> str:
    if x is None:
        return default
    try:
        return codecs.unicode_escape_decode(x)[0]
    except Exception: # pylint: disable=broad-except
        return default
def encodeLocal(x:Optional[Any]) -> Optional[str]:
    if x is not None:
        try:
            return codecs.unicode_escape_encode(str(x))[0].decode('utf8')
        except Exception: # pylint: disable=broad-except
            return None
    return None
def encodeLocalStrict(x:Optional[Any], default:str = '') -> str:
    if x is None:
        return default
    try:
        return codecs.unicode_escape_encode(str(x))[0].decode('utf8')
    except Exception: # pylint: disable=broad-except
        return default
def hex2int(h1:int, h2:Optional[int] = None) -> int:
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
def is_proper_temp(x:Union[None, int, float]) -> bool:
    return x is not None and not numpy.isnan(x) and isinstance(x, (int, float)) and x not in [0, -1, float('-inf'), float('inf')]

# returns the prefix of length ll-1 of s and adds Unicode ellipsis character
# the length of the resulting string is max(1, ll, len(s))
def abbrevString(s:str, ll:int) -> str:
    if len(s) > ll:
        return f'{s[:max(0,ll-1)]}\u2026'
    return s

# used to convert time from int seconds to string (like in the LCD clock timer). input int, output string xx:xx
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

def fromFtoC(Ffloat:Optional[float]) -> Optional[float]:
    if Ffloat is None or Ffloat == -1 or (Ffloat is not None and numpy.isnan(Ffloat)):
        return Ffloat
    return fromFtoCstrict(Ffloat)

def fromCtoFstrict(Cfloat:float) -> float:
    if Cfloat == -1:
        return Cfloat
    return (Cfloat*9.0/5.0)+32.0

def fromCtoF(Cfloat:Optional[float]) -> Optional[float]:
    """Converts Celsius to Fahrenheit
    >>> fromCtoF(-1)
    -1
    >>> fromCtoF(None)
    None
    >>> fromCtoF(32)
    89.6
    """
    if Cfloat is None or Cfloat == -1 or (Cfloat is not None and numpy.isnan(Cfloat)):
        return Cfloat
    return fromCtoFstrict(Cfloat)

def RoRfromCtoFstrict(CRoR:float) -> float:
    if CRoR == -1:
        return CRoR
    return CRoR*9.0/5.0

def RoRfromCtoF(CRoR:Optional[float]) -> Optional[float]:
    if CRoR is None or CRoR == -1 or (CRoR is not None and numpy.isnan(CRoR)):
        return CRoR
    return RoRfromCtoFstrict(CRoR)

def RoRfromFtoCstrict(FRoR:float) -> float:
    if FRoR == -1:
        return FRoR
    return FRoR*(5.0/9.0)

def RoRfromFtoC(FRoR:Optional[float]) -> Optional[float]:
    if FRoR is None or FRoR == -1 or (FRoR is not None and numpy.isnan(FRoR)):
        return FRoR
    return RoRfromFtoCstrict(FRoR)

def convertRoR(r:Optional[float], source_unit:Literal['C', 'F'], target_unit:Literal['C', 'F']) -> Optional[float]:
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
def toInt(x:Optional[Union[int,str,float]]) -> int:
    if x is None:
        return 0
    try:
        return int(round(float(x)))
    except Exception: # pylint: disable=broad-except
        return 0

def toString(x:Any) -> str:
    return str(x)

def toList(x:Any) -> List[Any]:
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
            return bool(eval(x)) # pylint: disable=eval-used
        except Exception: # pylint: disable=broad-except
            return False
    return bool(x)

def toStringList(x:List[Any]) -> List[str]:
    if x:
        return [str(s) for s in x]
    return []

def removeAll(ll:List[str], s:str) -> None:
    for _ in range(ll.count(s)):  # @UndefinedVariable
        ll.remove(s)

# fills in intermediate interpolated values replacing -1 values based on surrounding values
# [1, 2, 3, -1, -1, -1, 10, 11] => [1, 2, 3, 4.75, 6.5, 8.25, 11]
# [1,2,3,-1,-1,-1,-1] => [1,2,3,-1,-1,-1,-1] # no final value to interpolate too, so trailing -1 are kept!
# [-1,-1,2] => [2, 2, 2] # a prefix of -1 of max length 'interpolate_max' will be replaced by the first value in l that is not -1
# INVARIANT: the resulting list has always the same length as l
# only gaps of length interpolate_max (should be set to the global aw.qmc.interpolatemax), if not None, are interpolated
def fill_gaps(ll:Union[Sequence[Union[float, int]], 'npt.NDArray[numpy.floating[Any]]'], interpolate_max:int=3) -> List[float]:
    res:List[float] = []
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
                if interpolate_max is not None and interpolate_max < (next_idx - i):
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
                res.append(float(e))
                last_val = float(e)
    return res

def replace_duplicates(data:List[float]) -> List[float]:
    lv:float = -1
    data_core:List[float] = []
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
def getDataDirectory() -> Optional[str]:
    app = QCoreApplication.instance()
    return _getAppDataDirectory(app)

# internal function to return
@functools.lru_cache(maxsize=None)  #for Python >= 3.9 can use @functools.cache
def _getAppDataDirectory(app:'Artisan') -> Optional[str]:
    # temporarily switch app name to Artisan (as it might be ArtisanViewer)
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
def getDocumentsDirectory() -> Optional[str]:
    app = QCoreApplication.instance()
    return _getAppDocumentsDirectory(app)

# internal function to return
@functools.lru_cache(maxsize=None)  #for Python >= 3.9 can use @functools.cache
def _getAppDocumentsDirectory(app:'Artisan') -> Optional[str]:
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



@functools.lru_cache(maxsize=None)  #for Python >= 3.9 can use @functools.cache
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

@functools.lru_cache(maxsize=None)  #for Python >= 3.9 can use @functools.cache
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
def getDirectory(filename: str, ext: Optional[str] = None, share: bool = False) -> str:
    fn = filename
    if not share:
        app = QCoreApplication.instance()
        if app.artisanviewerMode: # type: ignore
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
def argb_colorname2rgba_colorname(c:str) -> str:
    if len(c) == 9 and c[0] == '#':
        return f'#{c[3:9]}{c[1:3]}'
    return c

# converts standard/MPL hex color strings to QColor ARGB names with alpha at the begin
def rgba_colorname2argb_colorname(c:str) -> str:
    if len(c) == 9 and c[0] == '#':
        return f'#{c[7:9]}{c[1:7]}'
    return c

# takes a hex color string and returns the same color as hex string with staturation set to 0 and incr. lightness
def toGrey(color:str) -> str:
    h, _s, l, a = QColor(rgba_colorname2argb_colorname(color)).getHslF()
    if h is not None and l is not None and a is not None:
        gray = QColor.fromHslF(h,0,(1-l)/1.7+l,a) # saturation set to 0
    else:
        gray = QColor.fromHslF(0.5,0,0.5,1.0)
    if len(color) == 9:
        return gray.name(QColor.NameFormat.HexArgb)
    return gray.name(QColor.NameFormat.HexRgb)

# takes a hex color string and returns the same color as hex string with reduced staturation and incr. lightness
def toDim(color:str) -> str:
    h, s, l, a = QColor(rgba_colorname2argb_colorname(color)).getHslF()
    if h is not None and s is not None and l is not None and a is not None:
        gray = QColor.fromHslF(h,s/4,(1-l)/1.7+l,a)
    else:
        gray = QColor.fromHslF(0.5,0,0.5,1.0)
    if len(color) == 9:
        return gray.name(QColor.NameFormat.HexArgb)
    return gray.name(QColor.NameFormat.HexRgb)

# creates QLinearGradient style from light to dark by default, or from dark to light if reverse is True
@functools.lru_cache(maxsize=None)  #for Python >= 3.9 can use @functools.cache
def createGradient(rgb:Union[QColor, str], tint_factor:float = 0.1, shade_factor:float = 0.1, reverse:bool = False) -> str:
    light_grad,dark_grad = createRGBGradient(rgb,tint_factor,shade_factor)
    if reverse:
        # dark to light
        return f'QLinearGradient(x1:0,y1:0,x2:0,y2:1,stop:0 {dark_grad}, stop:1 {light_grad})'
    # light to dark (default)
    return f'QLinearGradient(x1:0,y1:0,x2:0,y2:1,stop:0 {light_grad}, stop:1 {dark_grad})'

# NOTE: for now alpha values of the rgb argument are ignored and resulting colors are RGB without alphas
def createRGBGradient(rgb:Union[QColor, str], tint_factor:float = 0.3, shade_factor:float = 0.3) -> Tuple[str,str]:
    try:
        rgb_tuple: Tuple[float, float, float]
        if isinstance(rgb, QColor): # pyrefly: ignore[invalid-argument]
            r,g,b,_ = rgb.getRgbF() # type:ignore[unused-ignore]
            if r is not None and g is not None and b is not None:
                rgb_tuple = (r,g,b)
            else:
                rgb_tuple = (0.5,0.5,0.5)
        elif rgb[0:1] == '#':   # hex input like "#ffaa00" # type: ignore
#            rgb_tuple = tuple(int(rgb[i:i+2], 16)/255 for i in (1, 3 ,5))
            rgb_tuple = (float(int(rgb[1:3], 16)/255),float(int(rgb[3:5], 16)/255),float(int(rgb[5:7], 16)/255)) # type:ignore[unused-ignore]
        else:                 # color name
            rgb_tuple = colors.hex2color(colors.cnames[rgb]) # type:ignore[unused-ignore]
        #ref: https://stackoverflow.com/questions/6615002/given-an-rgb-value-how-do-i-create-a-tint-or-shade
        r,g,b = tuple(int(255 * (x * (1 - shade_factor))) for x in rgb_tuple) # type:ignore[unused-ignore]
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

@functools.lru_cache(maxsize=None)  #for Python >= 3.9 can use @functools.cache
def getLoggers() -> List[logging.Logger]:
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

def setFileLogLevels(level:int, logger_names:List[str]) -> None:
    loggers = getLoggers()
    for logger in loggers:
        if logger.name in logger_names:
            setFileLogLevel(logger, level)

# returns True if new log level of loggers is DEBUG, False otherwise
def debugLogLevelToggle() -> bool:
    newDebugLevel = not debugLogLevelActive()
    setDebugLogLevel(newDebugLevel)
    return newDebugLevel

def natsort(s:str) -> List[Union[int,str]]:
    return [int(t) if t.isdigit() else t.casefold() for t in re.split(r'(\d+)', s)]

#convert number to string and auto set the number of decimal places 0, 0.999, 9.99, 999.9, 9999
def scaleFloat2String(num:Union[float,str]) -> str:
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

weight_units:Final[Tuple[str,str,str,str]] = ('g','Kg','lb','oz')
weight_units_lower:Final[Tuple[str,str,str,str]] = ('g','kg','lb','oz') # just for display use
volume_units:Final[Tuple[str,str,str,str,str,str]] = ('l','gal','qt','pt','cup','ml')

def weightVolumeDigits(v:float) -> int:
    v = abs(v)
    if v >= 1000:
        return 1
    if v >= 100:
        return 2
    if v >= 10:
        return 3
    return 4

def float2floatWeightVolume(v:float) -> float:
    d = weightVolumeDigits(v)
    return float2float(v,d)

# the int n specifies the number of digits
def float2floatNone(f:Optional[float], n:int=1) -> Optional[float]:
    if f is None:
        return None
    return float2float(f,n)

# the int n>=0 specifies the number of digits
# returns 0 if f is not a number
def float2float(f:Union[float,str], n:int=1) -> float:
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
    #                g,            kg,         lb,             oz,
    convtable = [
                    [1.,           0.001,      0.00220462262,  0.035274],  # g
                    [1000,         1.,         2.205,          35.274],    # Kg
                    [453.591999,   0.45359237, 1.,             16.],       # lb
                    [28.3495,      0.0283495,  0.0625,         1.]         # oz
                ]
    if 0 <= i < len(convtable) and 0 <= o < len(convtable):
        return v*convtable[i][o]
    raise IndexError(f'index error in convertWeight({v},{i},{o})')

# i/o: 0:l (liter), 1:gal (gallons US), 2:qt, 3:pt, 4:cup, 5:cm^3/ml
def convertVolume(v:float, i:int, o:int) -> float:
                    #liter          gal             qt              pt              cup             ml/cm^3
    convtable = [
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

def is_int_list(xs: List[Any]) -> TypeGuard[List[int]]:
    return all(isinstance(x, int) and not isinstance(x, bool) for x in xs) # bool is a subclass of int!

def is_float_list(xs: List[Any]) -> TypeGuard[List[float]]:
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
def timearray2index(timearray:List[float], time:float, nearest:bool = True) -> int:
    i = bisect_right(timearray, time)
    if i:
        if nearest and i>0 and (i == len(timearray) or abs(time - timearray[i]) > abs(time - timearray[i-1])):
            return i-1
        return i
    return -1


def findTPint(timeindex:List[int], timex:List[float], temp:List[float]) -> int:
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
def events_internal_to_external_value(v:Optional[float]) -> int:
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


# serialize/deserialize


#Write object to file
def serialize(filename:str, obj:Dict[str, Any]) -> None:
    fn = str(filename)
    with open(fn, 'w+', encoding='utf-8') as f:
        f.write(repr(obj))


#Read object from file
def deserialize(filename:str) -> Dict[str, Any]:
    obj:Dict[str,Any] = {}
    try:
        fn = str(filename)
        if os.path.exists(fn):
            with open(fn, encoding='utf-8') as f:
                obj=ast.literal_eval(f.read()) # pylint: disable=eval-used
    except Exception as ex: # pylint: disable=broad-except
        _log.exception(ex)
    return obj


def csv_load(csvFile:io.TextIOWrapper) -> 'ProfileData':
    import csv
    profile = ProfileData()

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

    timex:List[float] = []
    temp1:List[float] = []
    temp2:List[float] = []

    # add extra devices
    number_extra_devices = min(10, int(len(extra_fields)/2)) # ApplicationWindow.nLCDS = 10
    extradevices:List[int] = [50]*number_extra_devices # type dummy
    extratimex:List[List[float]] = [[] for _ in range(number_extra_devices)] # we don't want exact copies of those empty lists as with [[]]*number_extra_devices!
    extratemp1:List[List[float]] = [[] for _ in range(number_extra_devices)]
    extratemp2:List[List[float]] = [[] for _ in range(number_extra_devices)]
    extraname1:List[str] = ['']*number_extra_devices
    extraname2:List[str] = ['']*number_extra_devices
    extramathexpression1:List[str] = ['']*number_extra_devices
    extramathexpression2:List[str] = ['']*number_extra_devices

    # set extra device names # NOTE: eventuelly we want to set/change the names only for devices that were just added in the line above!?
    for i, ef in enumerate(extra_fields):
        if i % 2 == 1:
            # odd
            extraname2[int(i/2)] = ef
        else:
            # even
            extraname1[int(i/2)] = ef

    #read data
    last_time:Optional[float] = None

    i = 0
    for row in data:
        i = i + 1
        try:
            items = list(zip(fields, row))
            item = {}
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

    timeindex:List[int] = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actual index used

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
        DRYe = timex_zero[timeindex[1]] if timeindex[1] else 0.
        FCs = timex_zero[timeindex[2]] if timeindex[2] else 0.
        FCe = timex_zero[timeindex[3]] if timeindex[3] else 0.
        SCs = timex_zero[timeindex[4]] if timeindex[4] else 0.
        SCe = timex_zero[timeindex[5]] if timeindex[5] else 0.
        DROP = timex_zero[timeindex[6]] if timeindex[6] else 0.
        COOL = timex_zero[timeindex[7]] if timeindex[7] else 0.
        events:List[Tuple[float,str]] = [
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
            headrow:List[str] = (['Time1','Time2','ET','BT','Event'] + functools.reduce(lambda x,y : x + [str(y[0]),str(y[1])], # type:ignore
                    (list(zip(profile['extraname1'][0:extradevices],profile['extraname2'][0:extradevices])) if 'extraname1' in profile and 'extraname2' in profile else []),
                    []))
            writer.writerow(headrow)
            last_time:Optional[str] = None
            events_set:Set[str] = set()
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


# returns total roast time in seconds based on given timeindex and timex structures or None if data is not extractable
def roast_time(timeindex:List[int], timex:List[float]) -> Optional[float]:
    if len(timex) == 0 or len(timeindex) < 7:
        return None
    starttime = (timex[timeindex[0]] if timeindex[0] != -1 and timeindex[0] < len(timex) else 0)
    endtime = (timex[timeindex[6]] if timeindex[6] > 0  and timeindex[6] < len(timex) else timex[-1])
    return endtime - starttime

# return the total roasting time of the given profile in seconds
def get_total_roast_time_from_profile(profile:ProfileData) -> Optional[float]:
    if 'timex' in profile and 'timeindex' in profile:
        timeindex = profile['timeindex']
        timex = profile['timex']
        return roast_time(timeindex, timex)
    return None
