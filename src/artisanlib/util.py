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
from typing import Optional, Tuple, List, Union, Any
from typing_extensions import Final  # Python <=3.7
from typing_extensions import TypeGuard  # Python <=3.10

##

_log: Final[logging.Logger] = logging.getLogger(__name__)

application_name: Final[str] = 'Artisan'
application_viewer_name: Final[str] = 'ArtisanViewer'
application_organization_name: Final[str] = 'artisan-scope'
application_organization_domain: Final[str] = 'artisan-scope.org'


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

def decs2string(x) -> bytes:
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
def hex2int(h1,h2=None) -> int:
    if h2 is not None:
        return int(h1*256 + h2)
    return int(h1)
def str2cmd(s:str) -> bytes:
    return bytes(s,'ascii')
def cmd2str(c:bytes) -> str:
    return str(c,'latin1')
def s2a(s):
    return s.encode('ascii','ignore').decode('ascii')

# returns True if x is not None, not NaN and not the error value -1 or 0
def is_proper_temp(x):
    return x is not None and not numpy.isnan(x) and isinstance(x, (int, float)) and x not in [0, -1]

# returns the prefix of length ll of s and adds eclipse
def abbrevString(s:str, ll:int) -> str:
    if len(s) > ll:
        return f'{s[:ll-1]}...'
    return s

# used to convert time from int seconds to string (like in the LCD clock timer). input int, output string xx:xx
def stringfromseconds(seconds_raw:float, leadingzero=True) -> str:
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

def fromFtoC(Ffloat) -> float:
    if Ffloat in [-1,None] or numpy.isnan(Ffloat):
        return Ffloat
    return (Ffloat-32.0)*(5.0/9.0)

def fromCtoF(Cfloat) -> float:
    if Cfloat in [-1,None] or numpy.isnan(Cfloat):
        return Cfloat
    return (Cfloat*9.0/5.0)+32.0

def RoRfromCtoF(CRoR) -> float:
    if CRoR in [-1,None] or numpy.isnan(CRoR):
        return CRoR
    return CRoR*9.0/5.0

def RoRfromFtoC(FRoR) -> float:
    if FRoR in [-1,None] or numpy.isnan(FRoR):
        return FRoR
    return FRoR*(5.0/9.0)

def convertRoR(r,source_unit,target_unit):
    if source_unit == target_unit:
        return r
    if source_unit == 'C':
        return RoRfromCtoF(r)
    return RoRfromFtoC(r)

def convertTemp(t:float, source_unit:str, target_unit:str) -> float:
    if source_unit == '' or target_unit == '' or source_unit == target_unit:
        return t
    if source_unit == 'C':
        return fromCtoF(t)
    return fromFtoC(t)

def path2url(path):
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
def toString(x) -> str:
    return str(x)
def toList(x) -> List:
    if x is None:
        return []
    return list(x)
def toFloat(x) -> float:
    if x is None:
        return 0.
    try:
        return float(x)
    except Exception: # pylint: disable=broad-except
        return 0.
def toBool(x) -> bool:
    if isinstance(x,str):
        x_lower = x.lower()
        if x_lower in ('yes', 'true', 't', '1'):
            return True
        if x_lower in ('no', 'false', 'f', '0'):
            return False
        try:
            return bool(eval(x)) # pylint: disable=eval-used
        except Exception: # pylint: disable=broad-except
            return False
    return bool(x)
def toStringList(x) -> List[str]:
    if x:
        return [str(s) for s in x]
    return []
def toMap(x):
    return x
def removeAll(ll, s):
    for _ in range(ll.count(s)):  # @UndefinedVariable
        ll.remove(s)

# fills in intermediate interpolated values replacing -1 values based on surrounding values
# [1, 2, 3, -1, -1, -1, 10, 11] => [1, 2, 3, 4.75, 6.5, 8.25, 11]
# [1,2,3,-1,-1,-1,-1] => [1,2,3,-1,-1,-1,-1] # no final value to interpolate too, so trailing -1 are kept!
# [-1,-1,2] => [2, 2, 2] # a prefix of -1 of max length 'interpolate_max' will be replaced by the first value in l that is not -1
# INVARIANT: the resulting list has always the same length as l
# only gaps of length interpolate_max (should be set to the global aw.qmc.interpolatemax), if not None, are interpolated
def fill_gaps(ll, interpolate_max:int=3):
    res = []
    last_val = -1
    skip = -1
    for i,e in enumerate(ll):
        if i >= skip:
            if i == 0 and e == -1 and last_val == -1: # only for the prefix
                # a prefix of -1 will be replaced by the first value in ll that is not -1
                s = -1
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


# we store data in the user- and app-specific local default data directory
# for the platform
# note that the path is based on the ApplicationName and OrganizationName
# setting of the app
# eg. ~/Library/Application Support/artisan-scope/Artisan (macOS)
#     C:\Users\<USER>\AppData\Local\artisan-scope\Artisan (Windows)
#     ~/.local/shared/artisan-scope/Artisan (Linux)

# getDataDirectory() returns the Artisan data directory
# if app is not yet initialized None is returned
# otherwise the path is computed on first call and then memorized
# if the computed path does not exists it is created
# if creation or access of the path fails None is returned and memorized
def getDataDirectory():
    app = QCoreApplication.instance()
    return _getAppDataDirectory(app)

# internal function to return
@functools.lru_cache(maxsize=None)  #for Python >= 3.9 can use @functools.cache
def _getAppDataDirectory(app):
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
def getAppPath():
    platf = platform.system()
    if platf in ['Darwin','Linux']:
        if appFrozen():
            return QCoreApplication.applicationDirPath() + '/../../../'
        return os.path.dirname(os.path.realpath(__file__)) + '/../'
    if platf == 'Windows':
        if appFrozen():
            return os.path.dirname(sys.executable) + '\\'
        return os.path.dirname(os.path.realpath(__file__)) + '\\..\\'
    return QCoreApplication.applicationDirPath() + '/'

@functools.lru_cache(maxsize=None)  #for Python >= 3.9 can use @functools.cache
def getResourcePath():
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


# takes a hex color string and returns the same color as hex string with staturation set to 0 and incr. lightness
def toGrey(color):
    hslf = QColor(color).getHslF()
    gray = QColor.fromHslF(hslf[0],0,(1-hslf[2])/1.7+hslf[2],hslf[3]) # saturation set to 0
    return gray.name()

# takes a hex color string and returns the same color as hex string with reduced staturation and incr. lightness
def toDim(color):
    hslf = QColor(color).getHslF()
    gray = QColor.fromHslF(hslf[0],hslf[1]/4,(1-hslf[2])/1.7+hslf[2],hslf[3])
    return gray.name()

# creates QLinearGradient style from light to dark by default, or from dark to light if reverse is True
@functools.lru_cache(maxsize=None)  #for Python >= 3.9 can use @functools.cache
def createGradient(rgb, tint_factor=0.1, shade_factor=0.1, reverse=False):
    light_grad,dark_grad = createRGBGradient(rgb,tint_factor,shade_factor)
    if reverse:
        # dark to light
        return f'QLinearGradient(x1:0,y1:0,x2:0,y2:1,stop:0 {dark_grad}, stop:1 {light_grad})'
    # light to dark (default)
    return f'QLinearGradient(x1:0,y1:0,x2:0,y2:1,stop:0 {light_grad}, stop:1 {dark_grad})'

def createRGBGradient(rgb, tint_factor=0.3, shade_factor=0.3):
    try:
        rgb_tuple: Tuple[float, float, float]
        if isinstance(rgb, QColor):
            r,g,b,_ = rgb.getRgbF()
            rgb_tuple = (r,g,b)
        elif rgb[0:1] == '#':   # hex input like "#ffaa00"
#            rgb_tuple = tuple(int(rgb[i:i+2], 16)/255 for i in (1, 3 ,5))
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

@functools.lru_cache(maxsize=None)  #for Python >= 3.9 can use @functools.cache
def getLoggers():
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

def setFileLogLevel(logger, level) -> None:
    logger.setLevel(level)
    for handler in logger.handlers:
        if handler.get_name() == 'file':
            handler.setLevel(level)

def setFileLogLevels(level, logger_names) -> None:
    loggers = getLoggers()
    for logger in loggers:
        if logger.name in logger_names:
            setFileLogLevel(logger, level)

# returns True if new log level of loggers is DEBUG, False otherwise
def debugLogLevelToggle() -> bool:
    # first get all module loggers
    newDebugLevel = not debugLogLevelActive()
    setDebugLogLevel(newDebugLevel)
    return newDebugLevel

def natsort(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

#convert number to string an auto set the number of decimal places 0, 0.999, 9.99, 999.9, 9999
def scaleFloat2String(num):
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
        # we just keep this one and remove all other comma and dots
        return s[:last_dot].replace(',','').replace('.','') + s[last_dot:].replace(',','')
    # there is no dot in the string
    last_pos = s.rfind(',')
    if last_pos > -1:
        if last_pos + 1 == len(s):
            # this is just a trailing comma, we remove this and all other dots and commas
            return s.replace(',','').replace('.','')
        # we turn the last comma into a dot and remove all others
        return s[:last_pos].replace(',','') + '.' + s[last_pos+1:]
    return s

# typing tools

def is_int_list(xs: List[Any]) -> TypeGuard[List[int]]:
    return all(isinstance(x, int) for x in xs)

def is_float_list(xs: List[Any]) -> TypeGuard[List[float]]:
    return all(isinstance(x, float) for x in xs)
