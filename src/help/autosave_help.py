import prettytable
import re
from PyQt5.QtWidgets import QApplication

def content():
    strlist = []
    helpstr = ''  #@UnusedVariable
    newline = '\n'  #@UnusedVariable
    strlist.append('<head><style> td, th {border: 1px solid #ddd;  padding: 6px;} th {padding-top: 6px;padding-bottom: 6px;text-align: left;background-color: #0C6AA6; color: white;} </style></head> <body>')
    strlist.append("<b>")
    strlist.append(QApplication.translate('HelpDlg','AUTOSAVE FIELDS',None))
    strlist.append("</b>")
    tbl_Autosave = prettytable.PrettyTable()
    tbl_Autosave.field_names = [QApplication.translate('HelpDlg','Prefix Field',None),QApplication.translate('HelpDlg','Source',None),QApplication.translate('HelpDlg','Example',None)]
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~batchprefix',None),QApplication.translate('HelpDlg','The batch prefix set in Config>Batch>Prefix',None),QApplication.translate('HelpDlg','Prod-',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~batchcounter',None),QApplication.translate('HelpDlg','The current batch number',None),653])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~batch',None),QApplication.translate('HelpDlg','Same as "~batchprefix~batchnum"',None),QApplication.translate('HelpDlg','Prod-653',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~batchposition',None),QApplication.translate('HelpDlg','The current batch position, or "Roast of the Day"',None),9])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~batch_long',None),QApplication.translate('HelpDlg','Same as Batch field in Roast Properties\n "~batchprefix~batchnum (~batchposition)"',None),QApplication.translate('HelpDlg','Prod-653 (9)',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~title',None),QApplication.translate('HelpDlg','From Roast>Properties>Title',None),QApplication.translate('HelpDlg','Ethiopia Guji',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~beans',None),QApplication.translate('HelpDlg','The first 30 characters of the first line \nFrom Roast>Properties>Beans',None),QApplication.translate('HelpDlg','Ethiopia Guji purchased from R',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~beans_line',None),QApplication.translate('HelpDlg','The entire first line From Roast>Properties>Beans',None),QApplication.translate('HelpDlg','Ethiopia Guji purchased from Royal',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~date',None),QApplication.translate('HelpDlg','Roast date in format yy-MM-dd',None),QApplication.translate('HelpDlg','20-02-05',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~date_long',None),QApplication.translate('HelpDlg','Roast date in format yyyy-MM-dd',None),QApplication.translate('HelpDlg','2020-02-05',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~time',None),QApplication.translate('HelpDlg','Roast time in format hhmm',None),1742])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~datetime',None),QApplication.translate('HelpDlg','Roast date and time in format yy-MM-dd_hhmm',None),QApplication.translate('HelpDlg','20-02-05_1742',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~datetime_long',None),QApplication.translate('HelpDlg','Roast date and time in format yyyy-MM-dd_hhmm',None),QApplication.translate('HelpDlg','2020-02-05_1742',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~operator',None),QApplication.translate('HelpDlg','From Roast>Properties>Operator',None),QApplication.translate('HelpDlg','Dave',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~weight',None),QApplication.translate('HelpDlg','From Roast>Properties>Weight Green',None),3])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~weightunits',None),QApplication.translate('HelpDlg','From Roast>Properties>Weight',None),QApplication.translate('HelpDlg','Kg',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~volume',None),QApplication.translate('HelpDlg','From Roast>Properties>Volume Green',None),4.1])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~volumeunits',None),QApplication.translate('HelpDlg','From Roast>Properties>Volume',None),QApplication.translate('HelpDlg','l',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~density',None),QApplication.translate('HelpDlg','From Roast>Properties>Density Green',None),756.4])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~densityunits',None),QApplication.translate('HelpDlg','From Roast>Properties>Density',None),QApplication.translate('HelpDlg','g_l',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~moisture',None),QApplication.translate('HelpDlg','From Roast>Properties>Moisture Green',None),11.7])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~machine',None),QApplication.translate('HelpDlg','From Roast>Properties>Machine',None),QApplication.translate('HelpDlg','SF-6',None)])
    tbl_Autosave.add_row([QApplication.translate('HelpDlg','~drumspeed',None),QApplication.translate('HelpDlg','From Roast>Properties>Drum Speed',None),64])
    strlist.append(tbl_Autosave.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    strlist.append("</body>")
    helpstr = "".join(strlist)
    helpstr = re.sub(r"&amp;", r"&",helpstr)
    return helpstr