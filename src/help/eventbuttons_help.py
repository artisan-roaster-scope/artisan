import prettytable
import re
from PyQt5.QtWidgets import QApplication

def content():
    strlist = []
    helpstr = ''  #@UnusedVariable
    newline = '\n'  #@UnusedVariable
    strlist.append('<head><style> td, th {border: 1px solid #ddd;  padding: 6px;} th {padding-top: 6px;padding-bottom: 6px;text-align: left;background-color: #0C6AA6; color: white;} </style></head> <body>')
    strlist.append("<b>")
    strlist.append(QApplication.translate('HelpDlg','EVENT CUSTOM BUTTONS',None))
    strlist.append("</b>")
    tbl_Buttons = prettytable.PrettyTable()
    tbl_Buttons.field_names = [QApplication.translate('HelpDlg','COL1',None),QApplication.translate('HelpDlg','COL2',None)]
    tbl_Buttons.add_row([QApplication.translate('HelpDlg','Button Label',None),QApplication.translate('HelpDlg','Enter \\n to create labels with multiple lines. \\t is substituted by the event type.',None)])
    tbl_Buttons.add_row([QApplication.translate('HelpDlg','Event Description',None),QApplication.translate('HelpDlg','Description of the Event to be recorded.< br>Event type Type of event to be recorded.',None)])
    tbl_Buttons.add_row([QApplication.translate('HelpDlg','Event Value',None),QApplication.translate('HelpDlg','Value of event (1-100) to be recorded',None)])
    tbl_Buttons.add_row([QApplication.translate('HelpDlg','Action',None),QApplication.translate('HelpDlg','Perform an action at the time of the event',None)])
    tbl_Buttons.add_row([QApplication.translate('HelpDlg','Documentation',None),QApplication.translate('HelpDlg','depends on the action type (&#39;{}&#39; is replaced by the event value)',None)])
    tbl_Buttons.add_row([QApplication.translate('HelpDlg','Button Visibility',None),QApplication.translate('HelpDlg','Hides/shows individual button',None)])
    strlist.append(tbl_Buttons.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    strlist.append("<br/><br/><b>")
    strlist.append(QApplication.translate('HelpDlg','COMMANDS',None))
    strlist.append("</b>")
    tbl_Commands = prettytable.PrettyTable()
    tbl_Commands.field_names = [QApplication.translate('HelpDlg','Command Type',None),QApplication.translate('HelpDlg','Command',None)]
    tbl_Commands.add_row([QApplication.translate('HelpDlg','Serial',None),QApplication.translate('HelpDlg','ASCII serial command or binary a2b_uu(serial command)',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg','Call Program',None),QApplication.translate('HelpDlg','A program/script path (absolute or relative)',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg','Multiple Event',None),QApplication.translate('HelpDlg','Adds events of other button numbers separated by a comma: 1,2,..',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg','Modbus',None),QApplication.translate('HelpDlg','write([slaveId,register,value],..,[slaveId,register,value]) \nwrite register: MODBUS function 6 (int) or function 16 (float)',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','wcoil(slaveId,register,<bool>) \nwrite coil: MODBUS function 5',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','wcoils(slaveId,register,[<bool>,..,<bool>]) \nwrite coils: MODBUS function 15',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg',' ',None),QApplication.translate('HelpDlg','mwrite(slaveId,register,andMask,orMask) \nmask write register: MODBUS function 22',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','writem(slaveId,register,value) or writem(slaveId,register,[<int>,..,<int>]) \nwrite registers: MODBUS function 16',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','writeWord(slaveId,register,value) \nwrite 32bit float to two 16bit int registers: MODBUS function 16',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','writes values to the registers in slaves specified by the given id',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg','S7',None),QApplication.translate('HelpDlg','getDBint(<dbnumber>,<start>) \nread int from S7 DB',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','getDBfloat(<dbnumber>,<start>) \nread fl oat from S7 DB',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','setDBint(<dbnumber>,<start>,<value>) \nwrite int to S7 DB',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','setDBfloat(<dbnumber>,<start>,<value>) \nwrite float to S7 DB',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg','DTA',None),QApplication.translate('HelpDlg','Insert Data address : value, ex. 4701:1000 and sv is 100. \nAlways multiply with 10 if value Unit: 0.1 / ex. 4719:0 stops heating',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg','IO',None),QApplication.translate('HelpDlg','set(n,0 ), set(n,1), toggle(n), pulse(n,t) to set Phidget IO digital output n',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg','PWM',None),QApplication.translate('HelpDlg',' out(n,v), toggle(n), pulse(n,t) set digital output channel n to PWM value v (0-100) on a Phidget OUT1100 \nouthub(n,v), togglehub(n), pulsehub(n,t) on a Phidget HUB',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg','VOUT',None),QApplication.translate('HelpDlg','out(n,v) set analog output channel n to output voltage value v in V (eg. 5.5 for 5.5V) on a Phidget OUT1000/OUT1001/OUT1002',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg','Hotop',None),QApplication.translate('HelpDlg','Hottop Heater: sets heater to value',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','Hottop Fan: sets fan to value',None)])
    tbl_Commands.add_row(['&#160;',QApplication.translate('HelpDlg','Hottop Command: motor(n),solenoid(n),stirrer(n),heater(h),fan(f) with n={0 ,1},h={0,..100},f={0,..10}',None)])
    tbl_Commands.add_row([QApplication.translate('HelpDlg','PID',None),QApplication.translate('HelpDlg','p-i-d: configures PID to the values <p>;<i>;<d>',None)])
    strlist.append(tbl_Commands.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    strlist.append("</body>")
    helpstr = "".join(strlist)
    helpstr = re.sub(r"&amp;", r"&",helpstr)
    return helpstr