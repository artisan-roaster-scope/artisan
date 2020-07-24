import prettytable
import re
from PyQt5.QtWidgets import QApplication

def content():
    strlist = []
    helpstr = ''  #@UnusedVariable
    newline = '\n'  #@UnusedVariable
    strlist.append('<head><style> td, th {border: 1px solid #ddd;  padding: 6px;} th {padding-top: 6px;padding-bottom: 6px;text-align: left;background-color: #0C6AA6; color: white;} </style></head> <body>')
    strlist.append("<b>")
    strlist.append(QApplication.translate('HelpDlg','EXTERNAL PROGRAMS',None))
    strlist.append("</b>")
    tbl_Programstop = prettytable.PrettyTable()
    tbl_Programstop.header = False
    tbl_Programstop.add_row([QApplication.translate('HelpDlg','Link external programs that print temperature when called.  This allows to connect meters that use any program language.\n\nArtisan will start the program each sample period.  The program output must be to Stdout (like when using print statements).  The program must exit and must not be persistent.',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','If only one termperature is provided it will be interpreted as BT.  If more than one temperature is provided the values are order dependent with ET first and BT second.',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','Data may also be provided to the "Program" extra devices.  Extra device "Program" are the first two values, typically ET and BT.  "Program 34" are the third and fourth values.  Up to 10 values may be supplied.',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','Example of output needed from program for single temperature (BT):\n"100.4" (note: "" not needed)',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','Example of output needed from program for double temperature (ET,BT)\n"200.4,100.4" (note: temperatures are separated by a comma "ET,BT")',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','Example of output needed from program for double temperature (ET,BT) and extra devices (Program and Program 34)\n"200.4,100.4,312.4,345.6,299.0,275.5"',None)])
    strlist.append(tbl_Programstop.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    tbl_Programsbottom = prettytable.PrettyTable()
    tbl_Programsbottom.header = False
    tbl_Programsbottom.add_row([QApplication.translate('HelpDlg','Example of a file written in python language called test.py:',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','#comment: print a string with two numbers separated by a comma',None)+newline+QApplication.translate('HelpDlg','#!/usr/bin/env python',None)+newline+QApplication.translate('HelpDlg','print ("237.1,100.4")',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','Note: In many cases the path to the Python or other language executatable should be provided along with the external program path.  On Windows it is  advised to enclose the paths with quotation marks if there are any spaces, and use forward slashes &#39;/&#39; in the path.\n"C:/Python38-64/python.exe" "c:/scripts/test.py"',None)])
    strlist.append(tbl_Programsbottom.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    strlist.append("</body>")
    helpstr = "".join(strlist)
    helpstr = re.sub(r"&amp;", r"&",helpstr)
    return helpstr