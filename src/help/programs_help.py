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
    tbl_Programstop.add_row([QApplication.translate('HelpDlg','Allows to link to external programs that print temperature when called',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','The output of the program must be to Stdout (like when using print statements)',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','this allo ws to connect meters that use any programming language',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','Example of output needed from program for single temperature (BT)',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','"100.4" (note: "" not needed)',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','Example of output needed from program for double temperature (ET,BT)',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','"200.4,100.4" (note: temperatures are separated by a comma "ET,BT")',None)])
    strlist.append(tbl_Programstop.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    tbl_Programsbottom = prettytable.PrettyTable()
    tbl_Programsbottom.header = False
    tbl_Programsbottom.add_row([QApplication.translate('HelpDlg','Example of a file written in python language called test.py:',None)+newline+QApplication.translate('HelpDlg','#comment: print a string with two numbers separated by a comma',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','#!/usr/bin/env python',None)+newline+QApplication.translate('HelpDlg','print ("237.1,100.4")',None)])
    strlist.append(tbl_Programsbottom.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    strlist.append("</body>")
    helpstr = "".join(strlist)
    helpstr = re.sub(r"&amp;", r"&",helpstr)
    return helpstr