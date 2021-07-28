import imp
import platform
import sys
import codecs
import math

import urllib.parse as urlparse  # @Reimport
import urllib.request as urllib  # @Reimport

deltaLabelPrefix = "<html>&Delta;&thinsp;</html>" # prefix constant for labels to compose DeltaET/BT by prepending this prefix to ET/BT labels
if platform.system() == 'Linux':
    deltaLabelUTF8 = "Delta"
else:
    deltaLabelUTF8 = "\u0394\u2009" # u("\u03B4") # prefix for non HTML Qt Widgets like QPushbuttons
deltaLabelBigPrefix = "<big><b>&Delta;</b></big>&thinsp;<big><b>" # same as above for big/bold use cases
deltaLabelMathPrefix = "$\Delta\/$"  # prefix for labels in matplibgraphs to compose DeltaET/BT by prepending this prefix to ET/BT labels

def appFrozen():
    ib = False
    try:
        platf = str(platform.system())
        if platf == "Darwin":
            # the sys.frozen is set by py2app and pyinstaller and is unset otherwise
            if getattr( sys, 'frozen', False ):
                ib = True
        elif platf == "Windows":
            ib = (hasattr(sys, "frozen") or # new py2exe
                hasattr(sys, "importers") # old py2exe
                or imp.is_frozen("__main__")) # tools/freeze
        elif platf == "Linux":
            if getattr(sys, 'frozen', False):
                # The application is frozen
                ib = True
    except Exception:
        pass
    return ib

def decs2string(x):
    if len(x) > 0:
        return bytes(x)
    else:
        return b""
def stringp(x):
    return isinstance(x, str)
def uchr(x):
    return chr(x)
# the historical u() needed for Python2/Qt4 got eliminated or replaced by str()
#def u(x): # convert to unicode string
#    return str(x)
def d(x):
    if x is not None:
        return codecs.unicode_escape_decode(x)[0]
    else:
        return None
def encodeLocal(x):
    if x is not None:
        return codecs.unicode_escape_encode(str(x))[0].decode("utf8")
    else:
        return None
def hex2int(h1,h2=None):
    if h2 is not None:
        return int(h1*256 + h2)
    else:
        return int(h1)
def str2cmd(s):
    return bytes(s,"ascii")
def cmd2str(c):
    return str(c,"latin1")
def s2a(s):
    return s.encode('ascii','ignore').decode("ascii")

# used to convert time from int seconds to string (like in the LCD clock timer). input int, output string xx:xx
def stringfromseconds(seconds_raw, leadingzero=True):
    # seconds = int(round(seconds_raw)) # note that round(1.5)=round(2.5)=2
    seconds = int(math.floor(seconds_raw + 0.5))
    if seconds >= 0:
        if leadingzero:
            return "%02d:%02d"% divmod(seconds, 60)
        else:
            return ("%2d:%02d"% divmod(seconds, 60)).strip()
    else:
        #usually the timex[timeindex[0]] is alreday taken away in seconds before calling stringfromseconds()
        negtime = abs(seconds)
        return "-%02d:%02d"% divmod(negtime, 60)

#Converts a string into a seconds integer. Use for example to interpret times from Roaster Properties Dlg inputs
#accepted formats: "00:00","-00:00"
def stringtoseconds(string):
    timeparts = string.split(":")
    if len(timeparts) != 2:
        return -1
    else:
        if timeparts[0][0] != "-":  #if number is positive
            seconds = int(timeparts[1])
            seconds += int(timeparts[0])*60
            return seconds
        else:
            seconds = int(timeparts[0])*60
            seconds -= int(timeparts[1])
            return seconds    #return negative number

def fromFtoC(Ffloat):
    if Ffloat in [-1,None]:
        return Ffloat
    else:
        return (Ffloat-32.0)*(5.0/9.0)

def fromCtoF(Cfloat):
    if Cfloat in [-1,None]:
        return Cfloat
    else:
        return (Cfloat*9.0/5.0)+32.0
        
def RoRfromCtoF(CRoR):
    if CRoR in [-1,None]:
        return CRoR
    else:
        return (CRoR*9.0/5.0)

def RoRfromFtoC(FRoR):
    if FRoR in [-1,None]:
        return FRoR
    else:
        return FRoR*(5.0/9.0)

def convertRoR(r,source_unit,target_unit):
    if source_unit == "C":
        if target_unit == "C":
            return r
        else:
            return RoRfromCtoF(r)
    elif source_unit == "F":
        if target_unit == "F":
            return r
        else:
            return RoRfromFtoC(r)
    else:
        return r
        
def convertTemp(t,source_unit,target_unit):
    if source_unit == "C":
        if target_unit == "C":
            return t
        else:
            return fromCtoF(t)
    elif source_unit == "F":
        if target_unit == "F":
            return t
        else:
            return fromFtoC(t)
    else:
        return t


def path2url(path):
    return urlparse.urljoin(
      'file:', urllib.pathname2url(path))
        
# remaining artifacts from Qt4/5 compatibility layer:
# note: those conversion functions are sometimes called with string arguments thus a simple int(round(s)) won't work and a int(round(float(s))) needs to be applied
def toInt(x):
    if x is None:
        return 0
    else:
        try:
            return int(round(float(x)))
        except:
            return 0
def toString(x):
    return str(x)
def toList(x):
    if x is None:
        return []
    else:
        return list(x)
def toFloat(x):
    if x is None:
        return 0.
    else:
        try:
            return float(x)
        except:
            return 0.
def toBool(x):
    if x is None:
        return False
    else:
        if isinstance(x,str):
            if x in ["false","False"]:
                return False
            else:
                return True
        else:
            return bool(x)
def toStringList(x):
    if x:
        return [str(s) for s in x]
    else:
        return []
def toMap(x):
    return x
def removeAll(l,s):
    for _ in range(l.count(s)):  # @UndefinedVariable
        l.remove(s)
        
# fills in intermediate interpolated values replacing -1 values based on surrounding values
# [1, 2, 3, -1, -1, -1, 10, 11] => [1, 2, 3, 4.75, 6.5, 8.25, 11]
# [1,2,3,-1,-1,-1,-1] => [1,2,3,-1,-1,-1,-1] # no final value to interpolate too, so trailing -1 are kept!
# [-1,-1,2] => [2, 2.0, 2] # a prefix of -1 will be replaced by the first value in l that is not -1
# INVARIANT: the resulting list has always the same lenght as l
def fill_gaps(l):
    res = []
    last_val = -1
    skip = -1
    for i,e in enumerate(l):
        if i >= skip:
            if e == -1 and last_val == -1:
                # a prefix of -1 will be replaced by the first value in l that is not -1
                s = -1
                for e in l:
                    if e != -1:
                        s = e
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
                if next_val is None:
                    # no further valid values, we append the tail
                    res.extend(l[i:])
                    return res
                else:
                    # compute intermediate values
                    step = (next_val - last_val) / (j-i+1.)
                    for _ in range(j-i):
                        last_val = last_val + step
                        res.append(last_val)
                    skip = next_idx
            else:
                res.append(e)
                last_val = e
    return res