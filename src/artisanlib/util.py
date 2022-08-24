#

import logging
import platform
import sys
import math
import os
import re
import numpy
import functools
from pathlib import Path
from typing import Optional
try:
    from typing import Final
except ImportError:
    # for Python 3.7:
    from typing_extensions import Final
from matplotlib import colors


##

_log: Final = logging.getLogger(__name__)

application_name: Final = 'Artisan'
application_viewer_name: Final = 'ArtisanViewer'
application_organization_name: Final = 'artisan-scope'
application_organization_domain: Final = 'artisan-scope.org'


try:
    #ylint: disable = E, W, R, C
    from PyQt6.QtCore import QStandardPaths, QCoreApplication # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import QColor  # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #ylint: disable = E, W, R, C
    from PyQt5.QtCore import QStandardPaths, QCoreApplication # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import QColor  # @UnusedImport @Reimport  @UnresolvedImport


deltaLabelPrefix = '<html>&Delta;&thinsp;</html>' # prefix constant for labels to compose DeltaET/BT by prepending this prefix to ET/BT labels
if platform.system() == 'Linux':
    deltaLabelUTF8 = 'Delta'
else:
    deltaLabelUTF8 = '\u0394\u2009' # u("\u03B4") # prefix for non HTML Qt Widgets like QPushbuttons
deltaLabelBigPrefix = '<big><b>&Delta;</b></big>&thinsp;<big><b>' # same as above for big/bold use cases
deltaLabelMathPrefix = r'$\Delta\/$'  # prefix for labels in matplibgraphs to compose DeltaET/BT by prepending this prefix to ET/BT labels

def appFrozen():
    ib = False
    try:
        platf = str(platform.system())
        if platf == 'Darwin':
            # the sys.frozen is set by py2app and pyinstaller and is unset otherwise
            if getattr( sys, 'frozen', False ):
                ib = True
        elif platf == 'Windows':
            ib = hasattr(sys, 'frozen')
        elif platf == 'Linux':
            if getattr(sys, 'frozen', False):
                # The application is frozen
                ib = True
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)
    return ib

def decs2string(x):
    if len(x) > 0:
        return bytes(x)
    return b''
def stringp(x):
    return isinstance(x, str)
def uchr(x):
    return chr(x)
def decodeLocal(x):
    if x is not None:
        import codecs
        return codecs.unicode_escape_decode(x)[0]
    return None
def encodeLocal(x):
    if x is not None:
        import codecs
        return codecs.unicode_escape_encode(str(x))[0].decode('utf8')
    return None
def hex2int(h1,h2=None):
    if h2 is not None:
        return int(h1*256 + h2)
    return int(h1)
def str2cmd(s):
    return bytes(s,'ascii')
def cmd2str(c):
    return str(c,'latin1')
def s2a(s):
    return s.encode('ascii','ignore').decode('ascii')

# returns the prefix of length l of s and adds eclipse
def abbrevString(s,l):
    if len(s) > l:
        return f'{s[:l-1]}...'
    return s

# used to convert time from int seconds to string (like in the LCD clock timer). input int, output string xx:xx
def stringfromseconds(seconds_raw, leadingzero=True):
    # seconds = int(round(seconds_raw)) # note that round(1.5)=round(2.5)=2
    seconds = int(math.floor(seconds_raw + 0.5))
    if seconds >= 0:
        if leadingzero:
            return '%02d:%02d'% divmod(seconds, 60)
        return ('%d:%02d'% divmod(seconds, 60))
    #usually the timex[timeindex[0]] is already taken away in seconds before calling stringfromseconds()
    negtime = abs(seconds)
    if leadingzero:
        return f'-{("%02d:%02d"% divmod(negtime, 60))}'
    return f'-{("%d:%02d"% divmod(negtime, 60))}'

#Converts a string into a seconds integer. Use for example to interpret times from Roaster Properties Dlg inputs
#accepted formats: "00:00","-00:00"
def stringtoseconds(string):
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

def fromFtoC(Ffloat):
    if Ffloat in [-1,None] or numpy.isnan(Ffloat):
        return Ffloat
    return (Ffloat-32.0)*(5.0/9.0)

def fromCtoF(Cfloat):
    if Cfloat in [-1,None] or numpy.isnan(Cfloat):
        return Cfloat
    return (Cfloat*9.0/5.0)+32.0

def RoRfromCtoF(CRoR):
    if CRoR in [-1,None] or numpy.isnan(CRoR):
        return CRoR
    return (CRoR*9.0/5.0)

def RoRfromFtoC(FRoR):
    if FRoR in [-1,None] or numpy.isnan(FRoR):
        return FRoR
    return FRoR*(5.0/9.0)

def convertRoR(r,source_unit,target_unit):
    if source_unit == target_unit:
        return r
    if source_unit == 'C':
        return RoRfromCtoF(r)
    return RoRfromFtoC(r)

def convertTemp(t,source_unit,target_unit):
    if source_unit == target_unit:
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
def toInt(x):
    if x is None:
        return 0
    try:
        return int(round(float(x)))
    except Exception: # pylint: disable=broad-except
        return 0
def toString(x):
    return str(x)
def toList(x):
    if x is None:
        return []
    return list(x)
def toFloat(x):
    if x is None:
        return 0.
    try:
        return float(x)
    except Exception: # pylint: disable=broad-except
        return 0.
def toBool(x):
    if isinstance(x,str):
        if x == 'false':
            return False
        if x == 'true':
            return True
        try:
            return bool(eval(x)) # pylint: disable=eval-used
        except Exception: # pylint: disable=broad-except
            return False
    return bool(x)
def toStringList(x):
    if x:
        return [str(s) for s in x]
    return []
def toMap(x):
    return x
def removeAll(l,s):
    for _ in range(l.count(s)):  # @UndefinedVariable
        l.remove(s)

# fills in intermediate interpolated values replacing -1 values based on surrounding values
# [1, 2, 3, -1, -1, -1, 10, 11] => [1, 2, 3, 4.75, 6.5, 8.25, 11]
# [1,2,3,-1,-1,-1,-1] => [1,2,3,-1,-1,-1,-1] # no final value to interpolate too, so trailing -1 are kept!
# [-1,-1,2] => [2, 2, 2] # a prefix of -1 of max length 'interpolate_max' will be replaced by the first value in l that is not -1
# INVARIANT: the resulting list has always the same length as l
# only gaps of length interpolate_max (should be set to the global aw.qmc.interpolatemax), if not None, are interpolated
def fill_gaps(l, interpolate_max=3):
    res = []
    last_val = -1
    skip = -1
    for i,e in enumerate(l):
        if i >= skip:
            if i == 0 and e == -1 and last_val == -1: # only for the prefix
                # a prefix of -1 will be replaced by the first value in l that is not -1
                s = -1
                for ee in l[:5]:
                    if ee != -1:
                        s = ee
                        break
                res.append(s)
                last_val = s
            elif e == -1 and last_val != -1:
                next_val = None
                next_idx = None # first index of an element beyond i of a value different to -1
                for j in range(i+1,len(l)):
                    if l[j] != -1:
                        next_val = l[j]
                        next_idx = j
                        break
                if next_val is None or next_idx is None:
                    # no further valid values, we append the tail
                    res.extend(l[i:])
                    return res
                if interpolate_max is not None and interpolate_max < (next_idx - i):
                    # gap too big
                    res.extend(l[i:next_idx])
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
# eg. ~/Library/Application Support/artisan-Scope/Artisan (macOS)
#     C:/Users/<USER>/AppData/Local/artisan-Scope/Artisan" (Windows)
#     ~/.local/shared/artisan-scope/Artisan" (Linux)

# getDataDirectory() returns the Artisan data directory
# if app is not yet initialized None is returned
# otherwise the path is computed on first call and then memorized
# if the computed path does not exists it is created
# if creation or access of the path fails None is returned and memorized
def getDataDirectory():
    app = QCoreApplication.instance()
    if app is not None:
        return _getAppDataDirectory(app)
    return None

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
    res = ''
    platf = platform.system()
    if platf in ['Darwin','Linux']:
        if appFrozen():
            res = QCoreApplication.applicationDirPath() + '/../../../'
        else:
            res = os.path.dirname(os.path.realpath(__file__)) + '/../'
    elif platf == 'Windows':
        if appFrozen():
            res = os.path.dirname(sys.executable) + '\\'
        else:
            res = os.path.dirname(os.path.realpath(__file__)) + '\\..\\'
    else:
        res = QCoreApplication.applicationDirPath() + '/'
    return res

@functools.lru_cache(maxsize=None)  #for Python >= 3.9 can use @functools.cache
def getResourcePath():
    res = ''
    platf = platform.system()
    if platf == 'Darwin':
        if appFrozen():
            res = QCoreApplication.applicationDirPath() + '/../Resources/'
        else:
            res = os.path.dirname(os.path.realpath(__file__)) + '/../includes/'
    elif platf == 'Linux':
        if appFrozen():
            res = QCoreApplication.applicationDirPath() + '/'
        else:
            res = os.path.dirname(os.path.realpath(__file__)) + '/../includes/'
    elif platf == 'Windows':
        if appFrozen():
            res = os.path.dirname(sys.executable) + '\\'
        else:
            res = os.path.dirname(os.path.realpath(__file__)) + '\\..\\includes\\'
    else:
        res = QCoreApplication.applicationDirPath() + '/'
    return res

# if share is True, the same (cache) file is shared between the Artisan and
# ArtisanViewer apps
# and locks have to be used to avoid race conditions
def getDirectory(
    filename: str, ext: Optional[str] = None, share: bool = False
):
    fn = filename
    if not share:
        app = QCoreApplication.instance()
        if app.artisanviewerMode:
            fn = filename + '_viewer'
    fp = Path(getDataDirectory(), fn)
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
        if isinstance(rgb, QColor):
            r,g,b,_ = rgb.getRgbF()
            rgb_tuple = (r,g,b)
        elif rgb[0:1] == '#':   # hex input like "#ffaa00"
            rgb_tuple = tuple(int(rgb[i:i+2], 16)/255 for i in (1, 3 ,5))
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


# Logging

@functools.lru_cache(maxsize=None)  #for Python >= 3.9 can use @functools.cache
def getLoggers():
    return [logging.getLogger(name) for name in logging.root.manager.loggerDict if ('.' not in name)]  # @UndefinedVariable pylint: disable=no-member

def debugLogLevelActive() -> bool:
    try:
        return logging.getLogger('artisanlib').isEnabledFor(logging.DEBUG)
    except Exception: # pylint: disable=broad-except
        return False

def setDebugLogLevel(state: bool) -> None:
    if state:
        # debug logging on
        setFileLogLevels(logging.DEBUG)
        _log.info('debug logging ON')
    else:
        # debug logging off
        setFileLogLevels(logging.INFO)
        _log.info('debug logging OFF')

def setFileLogLevel(logger, level) -> None:
    logger.setLevel(level)
    for handler in logger.handlers:
        if handler.get_name() == 'file':
            handler.setLevel(level)

def setFileLogLevels(level) -> None:
    loggers = getLoggers()
    for logger in loggers:
        setFileLogLevel(logger, level)

# returns True if new log level of loggers is DEBUG, False otherwise
def debugLogLevelToggle() -> bool:
    # first get all module loggers
    newDebugLevel = not debugLogLevelActive()
    setDebugLogLevel(newDebugLevel)
    return newDebugLevel


def natsort(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]
