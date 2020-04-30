import prettytable
import re
from PyQt5.QtWidgets import QApplication

def content():
    strlist = []
    helpstr = ''  #@UnusedVariable
    newline = '\n'  #@UnusedVariable
    strlist.append('<head><style> td, th {border: 1px solid #ddd;  padding: 6px;} th {padding-top: 6px;padding-bottom: 6px;text-align: left;background-color: #0C6AA6; color: white;} </style></head> <body>')
    strlist.append("<b>")
    strlist.append(QApplication.translate('HelpDlg','EVENT CUSTOM SLIDERS',None))
    strlist.append("</b>")
    tbl_Sliders = prettytable.PrettyTable()
    tbl_Sliders.field_names = [QApplication.translate('HelpDlg','Command Type',None),QApplication.translate('HelpDlg','Command',None)]
    tbl_Sliders.add_row([QApplication.translate('HelpDlg','Event',None),QApplication.translate('HelpDlg','Hide or show the corresponding slider',None)])
    tbl_Sliders.add_row([QApplication.translate('HelpDlg','Action',None),QApplication.translate('HelpDlg','Perform an action on the slider release',None)])
    strlist.append(tbl_Sliders.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    strlist.append("<br/><br/><b>")
    strlist.append(QApplication.translate('HelpDlg','Commands',None))
    strlist.append("</b>")
    tbl_Commandstop = prettytable.PrettyTable()
    tbl_Commandstop.header = False
    tbl_Commandstop.add_row([QApplication.translate('HelpDlg',' Command depends on the action type ("{}" is replaced by value*factor + offset)',None)])
    strlist.append(tbl_Commandstop.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    tbl_Commands = prettytable.PrettyTable()
    tbl_Commands.field_names = [QApplication.translate('HelpDlg','Command Type',None),QApplication.translate('HelpDlg','Command',None)]
    tbl_Commands.add_row([QApplication.translate('HelpDlg','Serial',None),QApplication.translate('HelpDlg','ASCII serial command or binary a2b_uu(serial command)',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg','Modbus',None),QApplication.translate('HelpDlg','write([slaveId,register,value],..,[slaveId,register,value]) \nwrite register: MODBUS function 6 (int) or function 16 (float)',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','wcoil(slaveId,register,<bool>) \nwrite coil: MODBUS function 5',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','wcoils(slaveId,register,[<bool>,..,<bool>]) \nwrite coils: MODBUS function 15',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg',' ',None),QApplication.translate('HelpDlg','mwrite(slaveId,register,andMask,orMask) \nmask write register: MODBUS function 22',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','writem(slaveId,register,value) or writem(slaveId,register,[<int>,..,<int>]) \nwrite registers: MODBUS function 16',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','writeBCD(slaveId,register,value) or writeBCD(slaveId,register,[<int>,..,<int>]) \nwrite BCD encoded int register: MODBUS function 16 (BCD)',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','writeWord(slaveId,register,value) \nwrite 32bit float to two 16bit int registers: MODBUS function 16',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','writes values to the registers in slaves specified by the given id',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg','DTA',None),QApplication.translate('HelpDlg','nsert Data address : value, ex. 4701:1000 and sv is 100. always multiply with 10 if value Unit: 0.1 / ex. 4719:0 stops heating',None)])
    strlist.append(tbl_Commands.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    tbl_Commandsbottom = prettytable.PrettyTable()
    tbl_Commandsbottom.header = False
    tbl_Commandsbottom.add_row([QApplication.translate('HelpDlg','Offset added as offset to the slider value',None)+newline+QApplication.translate('HelpDlg','Factor multiplicator of the slider value',None)])
    strlist.append(tbl_Commandsbottom.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    strlist.append("</body>")
    helpstr = "".join(strlist)
    helpstr = re.sub(r"&amp;", r"&",helpstr)
    return helpstr