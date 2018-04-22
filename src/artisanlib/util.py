import imp
import sys
import platform

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