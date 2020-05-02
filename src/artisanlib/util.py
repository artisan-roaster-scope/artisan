import imp
import platform
import sys
import codecs

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
def u(x): # convert to unicode string
    return str(x)
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
def stringfromseconds(self, seconds_raw, leadingzero=True):
    seconds = int(round(seconds_raw))
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
#acepted formats: "00:00","-00:00"
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