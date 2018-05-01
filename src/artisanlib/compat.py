'''
Python 2.x/3.x Compatibility Layer
'''

import sys
import codecs
import binascii

if sys.version < '3':
    def decs2string(x):
        return "".join(chr(b) for b in x)
    def arange(x):
        return xrange(x)  # @UndefinedVariable
    def stringp(x):
        return isinstance(x, basestring)  # @UndefinedVariable
    def uchr(x):
        return unichr(x)  # @UndefinedVariable
    def o(x): # converts char to byte
        return ord(x)
    def u(x): # convert to unicode string
        return unicode(x)  # @UndefinedVariable
    def d(x):
        if x is not None:
            try:
                return codecs.unicode_escape_decode(x)[0]
            except Exception:
                return x
        else:
            return None
    def encodeLocal(x):
        if x is not None:
            return codecs.unicode_escape_encode(unicode(x))[0]  # @UndefinedVariable
        else:
            return None
    def hex2int(h1,h2=""):
        return int(binascii.hexlify(h1+h2),16)
    def s2a(s):
        return u(s).encode('ascii','ignore')
    def cmd2str(c):
        return c
    def str2cmd(s):
        return s2a(s)
else:
    def decs2string(x):
        if len(x) > 0:
            return bytes(x)
        else:
            return b""
    def arange(x):
        return range(x)
    def stringp(x):
        return isinstance(x, str)
    def uchr(x):
        return chr(x)
    def o(x): # converts char to byte
        return x
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