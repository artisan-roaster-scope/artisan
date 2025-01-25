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
import re
import numpy
import functools
from pathlib import Path
from matplotlib import colors
from typing import Final, Optional, Tuple, List, Sequence, Union, Any, TYPE_CHECKING
from typing_extensions import TypeGuard  # Python <=3.10

if TYPE_CHECKING:
    from artisanlib.main import Artisan # pylint: disable=unused-import
    import numpy.typing as npt # pylint: disable=unused-import


##

_log: Final[logging.Logger] = logging.getLogger(__name__)

application_name: Final[str] = 'Artisan'
application_viewer_name: Final[str] = 'ArtisanViewer'
application_organization_name: Final[str] = 'artisan-scope'
application_organization_domain: Final[str] = 'artisan-scope.org'
application_desktop_file_name: Final[str] = 'org.artisan_scope.artisan'


try:
    from PyQt6.QtCore import QStandardPaths, QCoreApplication # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QColor  # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QStandardPaths, QCoreApplication  # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
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

def decs2string(x:List[int]) -> bytes:
    if len(x) > 0:
        return bytes(x)
    return b''
def uchr(x:int) -> str:
    return chr(x)
def decodeLocal(x:Optional[Any]) -> Optional[str]:
    if x is not None:
        return codecs.unicode_escape_decode(x)[0]
    return None
def decodeLocalStrict(x:Optional[Any], default:str = '') -> str:
    if x is None:
        return default
    return codecs.unicode_escape_decode(x)[0]
def encodeLocal(x:Optional[Any]) -> Optional[str]:
    if x is not None:
        return codecs.unicode_escape_encode(str(x))[0].decode('utf8')
    return None
def encodeLocalStrict(x:Optional[Any], default:str = '') -> str:
    if x is None:
        return default
    return codecs.unicode_escape_encode(str(x))[0].decode('utf8')
def hex2int(h1:int, h2:Optional[int] = None) -> int:
    if h2 is not None:
        return int(h1*256 + h2)
    return int(h1)
def str2cmd(s:str) -> bytes:
    return bytes(s,'ascii')
def cmd2str(c:bytes) -> str:
    return str(c,'latin1')
def s2a(s:str) -> str:
    return s.encode('ascii','ignore').decode('ascii')

# returns True if x is not None, not NaN and not the error value -1 or 0
def is_proper_temp(x:Union[None, int, float]) -> bool:
    return x is not None and not numpy.isnan(x) and isinstance(x, (int, float)) and x not in [0, -1]

# returns the prefix of length ll of s and adds eclipse
def abbrevString(s:str, ll:int) -> str:
    if len(s) > ll:
        return f'{s[:ll-1]}...'
    return s

# used to convert time from int seconds to string (like in the LCD clock timer). input int, output string xx:xx
def stringfromseconds(seconds_raw:float, leadingzero:bool = True) -> str:
    # seconds = int(round(seconds_raw)) # note that round(1.5)=round(2.5)=2
    seconds = int(math.floor(seconds_raw + 0.5))
    if seconds >= 0:
        d, m = divmod(seconds, 60)
        if leadingzero:
            return f'{d:02d}:{m:02d}'
        return f'{d:d}:{m:02d}'
    #usually the timex[timeindex[0]] is already taken away in seconds before calling stringfromseconds()
    negtime = abs(seconds)
    d, m = divmod(negtime, 60)
    if leadingzero:
        return f'-{d:02d}:{m:02d}'
    return f'-{d:d}:{m:02d}'

#Converts a string into a seconds integer. Use for example to interpret times from Roaster Properties Dlg inputs
#accepted formats: "00:00","-00:00"
def stringtoseconds(string:str) -> int:
    timeparts = string.split(':')
    if len(timeparts) != 2:
        return -1
    if timeparts[0][0] != '-':  #if number is positive
        seconds = int(timeparts[1])
        seconds += int(timeparts[0])*60
        return seconds
    seconds = int(timeparts[0])*60
    seconds -= int(timeparts[1])
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

def convertRoR(r:Optional[float], source_unit:str, target_unit:str) -> Optional[float]:
    if source_unit == target_unit:
        return r
    if source_unit == 'C':
        return RoRfromCtoF(r)
    return RoRfromFtoC(r)

def convertRoRstrict(r:float, source_unit:str, target_unit:str) -> float:
    if source_unit == target_unit:
        return r
    if source_unit == 'C':
        return RoRfromCtoFstrict(r)
    return RoRfromFtoCstrict(r)

def convertTemp(t:float, source_unit:str, target_unit:str) -> float:
    if source_unit in ('', target_unit) or target_unit == '':
        return t
    res : Optional[float]
    if source_unit == 'C':
        res = fromCtoF(t)
        if res is None:
            return t
        return res
    res = fromFtoC(t)
    if res is None:
        return t
    return res

def path2url(path:str) -> str:
    import urllib.parse as urlparse  # @Reimport
    import urllib.request as urllib  # @Reimport
    return urlparse.urljoin(
      'file:', urllib.pathname2url(path))

# remaining artifacts from Qt4/5 compatibility layer:
# note: those conversion functions are sometimes called with string arguments
# thus a simple int(round(s)) won't work and a int(round(float(s))) needs to be applied
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
                        s = ee
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
                res.append(e)
                last_val = e
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
        if isinstance(rgb, QColor):
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
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

#convert number to string and auto set the number of decimal places 0, 0.999, 9.99, 999.9, 9999
def scaleFloat2String(num:Union[float,str]) -> str:
    n = toFloat(num)
    if n == 0:
        return '0'
    if abs(n) < 1:
        return f'{n:.3f}'.rstrip('0').rstrip('.')
    if abs(n) >= 1000:
        return f'{n:.0f}'
    if abs(n) >= 100:
        return f'{n:.1f}'.rstrip('0').rstrip('.')
    return f'{n:.2f}'.rstrip('0').rstrip('.')


# for use in widgets that expects a double via a self.createCLocalDoubleValidator that accepts both,
# one dot and several commas. If there is no dot, the last comma is interpreted as decimal separator and the others removed
# if there is a dot, the last one is used as a decimal separator and all other comma and dots are removed
def comma2dot(s:str) -> str:
    s = s.strip()
    last_dot = s.rfind('.')
    if last_dot > -1:
        if last_dot + 1 == len(s):
            # this is just a trailing dot, we remove this and all other dots and commas
            return s.replace(',','').replace('.','')
        # we just keep this one and remove all other comma and dots; we also remove trailing zero decimals
        return s[:last_dot].replace(',','').replace('.','') + s[last_dot:].replace(',','').rstrip('0').rstrip('.')
    # there is no dot in the string
    last_pos = s.rfind(',')
    if last_pos > -1:
        if last_pos + 1 == len(s):
            # this is just a trailing comma, we remove this and all other dots and commas
            return s.replace(',','').replace('.','')
        # we turn the last comma into a dot and remove all others; we also remove trailing zero decimals
        return s[:last_pos].replace(',','') + '.' + s[last_pos+1:].rstrip('0').rstrip('.')
    return s


#--- weight / volume

weight_units:Final[Tuple[str,str,str,str]] = ('g','Kg','lb','oz')
weight_units_lower:Final[Tuple[str,str,str,str]] = ('g','kg','lb','oz') # just for display use
volume_units:Final[Tuple[str,str,str,str,str,str]] = ('l','gal','qt','pt','cup','ml')

def weightVolumeDigits(v:float) -> int:
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

# the int n specifies the number of digits
def float2float(f:float, n:int=1) -> float:
    f = float(f)
    if n==0:
        if math.isnan(f):
            return 0
        return int(round(f))
    res:float = float(f'%.{n}f'%f)
    if math.isnan(res):
        return 0.0
    return res

# i/o: 0:g, 1:Kg, 2:lb (pound), 3:oz (ounce)
def convertWeight(v:float, i:int, o:int) -> float:
    #                g,            kg,         lb,             oz,
    convtable = [
                    [1.,           0.001,      0.00220462262,  0.035274],  # g
                    [1000,         1.,         2.205,          35.274],    # Kg
                    [453.591999,   0.45359237, 1.,             16.],       # lb
                    [28.3495,      0.0283495,  0.0625,         1.]         # oz
                ]
    return v*convtable[i][o]

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
    return v*convtable[i][o]


# takes a weight, its weight unit index, and a weight unit target index (decides over metric vs imperial)
# and returns a string rendering the weight with unit, potentially adjusted by its magnitude
# with weight_unit_index:
#         0 => g
#         1 => kg
#         2 => lb
#         3 => oz
# if brief is set to 0 (default 0), 3 decimals are returned for lb/kg and 2 for oz/g, if brief > 0 the number of decimals is reduced by that value and
# the rendering might loose precision
# with smart_unit_upgrade, a weight like 1600g is rendered more readable as 1.6kg (but leaves 1610g and 1601g as is)
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
    return all(isinstance(x, int) for x in xs)

def is_float_list(xs: List[Any]) -> TypeGuard[List[float]]:
    return all(isinstance(x, float) for x in xs)


# locale tools

def right_to_left(locale:str) -> bool:
    return locale in {'ar', 'fa', 'he'}

#def locale2full_local(locale:str) -> str:
#    locale_map:Dict[str,str] = {
#        'ar': 'ar_AA',
#        'da': 'da_DK',
#        'de': 'de_DE',
#        'el': 'el_GR',
#        'en': 'en_US',
#        'es': 'es_ES',
#        'fa': 'fa_IR',
#        'fi': 'fi_FI',
#        'fr': 'fr_FR',
#        'gd': 'gd_GB',
#        'he': 'he_IL',
#        'hu': 'hu_HU',
#        'id': 'id_ID',
#        'it': 'it_IT',
#        'ja': 'ja_JP',
#        'ko': 'ko_KR',
#        'lv': 'lv_LV',
#        'nl': 'nl_NL',
#        'no': 'nn_NO',
#        'pt': 'pt_PT',
#        'pt_BR': 'pt_BR',
#        'pl': 'pl_PL',
#        'ru': 'ru_RU',
#        'sk': 'sk_SK',
#        'sv': 'sv_SE',
#        'th': 'th_TH',
#        'tr': 'tr_TR',
#        'uk': 'uk_UA',
#        'vi': 'vi_VN',
#        'zh_CN': 'zh_CN',
#        'zh_TW': 'zh_TW'
#    }
#    if locale in locale_map:
#        return locale_map[locale]
#    return locale
