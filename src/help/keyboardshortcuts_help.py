import prettytable
import re
try:
  from PyQt5.QtWidgets import QApplication
except Exception:
  from PyQt6.QtWidgets import QApplication

def content():
    strlist = []
    helpstr = ''  #@UnusedVariable
    newline = '\n'  #@UnusedVariable
    strlist.append('<head><style> td, th {border: 1px solid #ddd;  padding: 6px;} th {padding-top: 6px;padding-bottom: 6px;text-align: left;background-color: #0C6AA6; color: white;} </style></head> <body>')
    strlist.append("<b>")
    strlist.append(QApplication.translate('HelpDlg','KEYBOARD SHORTCUTS'))
    strlist.append("</b>")
    tbl_KeyboardShortcuts = prettytable.PrettyTable()
    tbl_KeyboardShortcuts.field_names = [QApplication.translate('HelpDlg','Keys'),QApplication.translate('HelpDlg','Description')]
    tbl_KeyboardShortcuts.add_row(['ENTER',QApplication.translate('HelpDlg','Turns ON/OFF Keyboard Shortcuts')])
    tbl_KeyboardShortcuts.add_row(['SPACE',QApplication.translate('HelpDlg','When Keyboard Shortcuts are ON chooses the current button\nWhen Keyboard Shortcuts are OFF adds a custom event')])
    tbl_KeyboardShortcuts.add_row(['LEFT,RIGHT,UP,DOWN',QApplication.translate('HelpDlg','Move background or key focus')])
    tbl_KeyboardShortcuts.add_row(['a',QApplication.translate('HelpDlg','Autosave')])
    tbl_KeyboardShortcuts.add_row(['CRTL+N',QApplication.translate('HelpDlg','Autosave + Reset + START')])
    tbl_KeyboardShortcuts.add_row(['t\u00A0\u00A0\u00A0[Windows: CTRL+SHIFT+t]',QApplication.translate('HelpDlg','Toggle mouse cross lines')])
    tbl_KeyboardShortcuts.add_row(['d',QApplication.translate('HelpDlg','Toggle xy cursor mode (off/temp/delta)')])
    tbl_KeyboardShortcuts.add_row(['z',QApplication.translate('HelpDlg','Toggle xy cursor clamp mode (off/BT/ET/BTB/ETB)')])
    tbl_KeyboardShortcuts.add_row(['c',QApplication.translate('HelpDlg','Shows/Hides Controls')])
    tbl_KeyboardShortcuts.add_row(['x',QApplication.translate('HelpDlg','Shows/Hides LCD Readings')])
    tbl_KeyboardShortcuts.add_row(['m',QApplication.translate('HelpDlg','Shows/Hides Event Buttons')])
    tbl_KeyboardShortcuts.add_row(['b',QApplication.translate('HelpDlg','Shows/Hides Extra Event Buttons')])
    tbl_KeyboardShortcuts.add_row(['s',QApplication.translate('HelpDlg','Shows/Hides Event Sliders')])
    tbl_KeyboardShortcuts.add_row(['p',QApplication.translate('HelpDlg','Toggle PID mode')])
    tbl_KeyboardShortcuts.add_row(['h\u00A0\u00A0\u00A0[Windows: CTRL+h]',QApplication.translate('HelpDlg','Load background profile')])
    tbl_KeyboardShortcuts.add_row(['ALT+h\u00A0\u00A0\u00A0[Windows: CTRL+SHIFT+h]',QApplication.translate('HelpDlg','Remove background profile')])
    tbl_KeyboardShortcuts.add_row(['I',QApplication.translate('HelpDlg','Toggle foreground curves “show full”')])
    tbl_KeyboardShortcuts.add_row(['o',QApplication.translate('HelpDlg','Toggle background curves “show full”')])
    tbl_KeyboardShortcuts.add_row(['l',QApplication.translate('HelpDlg','Load alarms')])
    tbl_KeyboardShortcuts.add_row(['+,-',QApplication.translate('HelpDlg','Inc/dec PID lookahead')])
    tbl_KeyboardShortcuts.add_row(['CRTL 0-9',QApplication.translate('HelpDlg','Changes Event Button Palettes')])
    tbl_KeyboardShortcuts.add_row([';',QApplication.translate('HelpDlg','Application ScreenShot')])
    tbl_KeyboardShortcuts.add_row([':',QApplication.translate('HelpDlg','Desktop ScreenShot')])
    tbl_KeyboardShortcuts.add_row(['q,w,e,r + <value>',QApplication.translate('HelpDlg','Quick Special Event Entry.  The keys q,w,e, and r correspond to special events 1,2,3 and 4.  A two digit numeric value must follow the shortcut letter, e.g. &#39;q75&#39;, when the correspoding event slider max value is 100 or less (default setting).   When the slider max value is greater than 100, three digits must be entered and for values less that 100 a leading zero is required, e.g. &#39;q075&#39;.  ')])
    tbl_KeyboardShortcuts.add_row(['v +  <value>',QApplication.translate('HelpDlg','Quick PID SV Entry.  Value is a three digit number.  For values less than 100 must be entered with a leading zero, e.g. &#39;v075&#39;.')])
    tbl_KeyboardShortcuts.add_row(['f\u00A0\u00A0\u00A0[Windows:  CTRL+SHIFT+f]',QApplication.translate('HelpDlg','Full Screen Mode')])
    strlist.append(tbl_KeyboardShortcuts.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    strlist.append("</body>")
    helpstr = "".join(strlist)
    helpstr = re.sub(r"&amp;", r"&",helpstr)
    return helpstr