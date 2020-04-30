import prettytable
import re
from PyQt5.QtWidgets import QApplication

def content():
    strlist = []
    helpstr = ''  #@UnusedVariable
    newline = '\n'  #@UnusedVariable
    strlist.append('<head><style> td, th {border: 1px solid #ddd;  padding: 6px;} th {padding-top: 6px;padding-bottom: 6px;text-align: left;background-color: #0C6AA6; color: white;} </style></head> <body>')
    strlist.append("<b>")
    strlist.append(QApplication.translate('HelpDlg','MODBUS',None))
    strlist.append("</b>")
    tbl_Modbustop = prettytable.PrettyTable()
    tbl_Modbustop.header = False
    tbl_Modbustop.add_row([QApplication.translate('HelpDlg','The MODBUS device corresponds to input channels1 and 2.. The MODBUS_34 extra device adds input channels 3 and 4.',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','Inputs with slave id set to 0 are turned off.',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','Modbus function 3 "read holding register" is the standard. Modbus function 4 triggers the use of "read input register". Input registers (fct 4) usually are from 30000-39999.',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','Most devices hold data in 2 byte integer registers. A temperature of 145.2C is often sent as 1452. In that case you have to set the divider to "x/10".',None)+newline+QApplication.translate('HelpDlg','',None)+newline+QApplication.translate('HelpDlg','Few devices hold data as 4 byte floats in two registers. Tick the Float flag in this case.',None)])
    strlist.append(tbl_Modbustop.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    strlist.append("</body>")
    helpstr = "".join(strlist)
    helpstr = re.sub(r"&amp;", r"&",helpstr)
    return helpstr