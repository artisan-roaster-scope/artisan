# runtime hook for PyInstaller and PyQt4
# needs to be done before any other PyQt import
import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)