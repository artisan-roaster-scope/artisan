import prettytable
import re
from PyQt5.QtWidgets import QApplication

def content():
    strlist = []
    helpstr = ''  #@UnusedVariable
    newline = '\n'  #@UnusedVariable
    strlist.append('<head><style> td, th {border: 1px solid #ddd;  padding: 6px;} th {padding-top: 6px;padding-bottom: 6px;text-align: left;background-color: #0C6AA6; color: white;} </style></head> <body>')
    strlist.append("<b>")
    strlist.append(QApplication.translate('HelpDlg','ALARMS',None))
    strlist.append("</b>")
    tbl_Alarmstop = prettytable.PrettyTable()
    tbl_Alarmstop.header = False
    tbl_Alarmstop.add_row([QApplication.translate('HelpDlg','Each alarm is only triggered once.',None)])
    strlist.append(tbl_Alarmstop.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    tbl_Alarms = prettytable.PrettyTable()
    tbl_Alarms.field_names = [QApplication.translate('HelpDlg','Field',None),QApplication.translate('HelpDlg','Description',None)]
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Nr',None),QApplication.translate('HelpDlg','Alarm number for reference',None)])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Status',None),QApplication.translate('HelpDlg','Activate or Deactivate the alarm',None)])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','If Alarm',None),QApplication.translate('HelpDlg','Alarm triggered only if the alarm with the given number was triggered before. Use 0 for no guard.',None)])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','But Not',None),QApplication.translate('HelpDlg','Alarm triggered only if the alarm with the given number was not triggered before. Use 0 for no guard.',None)])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','From',None),QApplication.translate('HelpDlg','Alarm only triggered after the given event',None)])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Time',None),QApplication.translate('HelpDlg','If not 00:00, alarm is triggered mm:ss after the event "From" happened',None)])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Source',None),QApplication.translate('HelpDlg','The observed temperature source',None)])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Condition',None),QApplication.translate('HelpDlg','Alarm is triggered if source rises above or below the specified temperature',None)])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Temp',None),QApplication.translate('HelpDlg','The specified temperature limit',None)])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Action',None),QApplication.translate('HelpDlg','The action to be triggered if all conditions are fulfilled',None)])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Description',None),QApplication.translate('HelpDlg','The text of the popup, the name of the program, the number of the event button, the new value of the slider or the program to call',None)])
    strlist.append(tbl_Alarms.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    strlist.append("</body>")
    helpstr = "".join(strlist)
    helpstr = re.sub(r"&amp;", r"&",helpstr)
    return helpstr