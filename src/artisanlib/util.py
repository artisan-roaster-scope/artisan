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
