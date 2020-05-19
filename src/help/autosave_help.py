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
    tbl_Autosave.add_row(['~batchprefix',QApplication.translate('HelpDlg','The batch prefix set in Config>Batch>Prefix',None),'Prod-'])
    tbl_Autosave.add_row(['~batchcounter',QApplication.translate('HelpDlg','The current batch number',None),653])
    tbl_Autosave.add_row(['~batch',QApplication.translate('HelpDlg','Same as "~batchprefix~batchnum"',None),'Prod-653'])
    tbl_Autosave.add_row(['~batchposition',QApplication.translate('HelpDlg','The current batch position, or "Roast of the Day"',None),9])
    tbl_Autosave.add_row(['~batch_long',QApplication.translate('HelpDlg','Same as Batch field in Roast Properties\n "~batchprefix~batchnum (~batchposition)"',None),'Prod-653 (9)'])
    tbl_Autosave.add_row(['~title',QApplication.translate('HelpDlg','From Roast>Properties>Title',None),'Ethiopia Guji'])
    tbl_Autosave.add_row(['~beans',QApplication.translate('HelpDlg','The first 30 characters of the first line \nFrom Roast>Properties>Beans',None),'Ethiopia Guji purchased from R'])
    tbl_Autosave.add_row(['~beans_line',QApplication.translate('HelpDlg','The entire first line From Roast>Properties>Beans',None),'Ethiopia Guji purchased from Royal'])
    tbl_Autosave.add_row(['~date',QApplication.translate('HelpDlg','Roast date in format yy-MM-dd',None),'20-02-05'])
    tbl_Autosave.add_row(['~date_long',QApplication.translate('HelpDlg','Roast date in format yyyy-MM-dd',None),'2020-02-05'])
    tbl_Autosave.add_row(['~time',QApplication.translate('HelpDlg','Roast time in format hhmm',None),1742])
    tbl_Autosave.add_row(['~datetime',QApplication.translate('HelpDlg','Roast date and time in format yy-MM-dd_hhmm',None),'20-02-05_1742'])
    tbl_Autosave.add_row(['~datetime_long',QApplication.translate('HelpDlg','Roast date and time in format yyyy-MM-dd_hhmm',None),'2020-02-05_1742'])
    tbl_Autosave.add_row(['~operator',QApplication.translate('HelpDlg','From Roast>Properties>Operator',None),'Dave'])
    tbl_Autosave.add_row(['~weight',QApplication.translate('HelpDlg','From Roast>Properties>Weight Green',None),3])
    tbl_Autosave.add_row(['~weightunits',QApplication.translate('HelpDlg','From Roast>Properties>Weight',None),'Kg'])
    tbl_Autosave.add_row(['~volume',QApplication.translate('HelpDlg','From Roast>Properties>Volume Green',None),4.1])
    tbl_Autosave.add_row(['~volumeunits',QApplication.translate('HelpDlg','From Roast>Properties>Volume',None),'l'])
    tbl_Autosave.add_row(['~density',QApplication.translate('HelpDlg','From Roast>Properties>Density Green',None),756.4])
    tbl_Autosave.add_row(['~densityunits',QApplication.translate('HelpDlg','From Roast>Properties>Density',None),'g_l'])
    tbl_Autosave.add_row(['~moisture',QApplication.translate('HelpDlg','From Roast>Properties>Moisture Green',None),11.7])
    tbl_Autosave.add_row(['~machine',QApplication.translate('HelpDlg','From Roast>Properties>Machine',None),'SF-6'])
    tbl_Autosave.add_row(['~drumspeed',QApplication.translate('HelpDlg','From Roast>Properties>Drum Speed',None),64])
    strlist.append(tbl_Autosave.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    tbl_Autosavebottom = prettytable.PrettyTable()
    tbl_Autosavebottom.header = False
    tbl_Autosavebottom.add_row([QApplication.translate('HelpDlg','NOTES:\nAnything between single quotes &#39; will show in the file name only when ON.\nExample: &#39;REC ~batch&#39;\n\nAnything between double quotes " will show in the file name only when OFF. \nExample: "~operator"\n\nFor backward compatibility, when the Prefix field is text only the date and time are appended to the file name.\nExample: &#39;Autosave&#39; will result in file name &#39;Autosave_20-01-13_1705&#39;.\nTo show only the text place a single &#39;!&#39; at the start of the Prefix field\nExample: &#39;!Autosave&#39; will result in file name &#39;Autosave&#39;.\n\nTo maintain cross platform compatibility, file names may contain only letters, numbers, spaces, \nand the following special characters:  \n_ - . ( )',None)])
    strlist.append(tbl_Autosavebottom.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    strlist.append("<br/><br/><b>")
    strlist.append(QApplication.translate('HelpDlg','EXAMPLES',None))
    strlist.append("</b>")
    tbl_Examplestop = prettytable.PrettyTable()
    tbl_Examplestop.header = False
    tbl_Examplestop.add_row([QApplication.translate('HelpDlg','Data used to replace the fields in the Autosave File Name Prefix are pulled from the current Roast Properties.  ',None)])
    strlist.append(tbl_Examplestop.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    tbl_Examples = prettytable.PrettyTable()
    tbl_Examples.field_names = [QApplication.translate('HelpDlg','Autosave Field',None),QApplication.translate('HelpDlg','Example File Name',None)]
    tbl_Examples.add_row([QApplication.translate('HelpDlg','~title Roasted on ~date',None),QApplication.translate('HelpDlg','Burundi Roasted on 20-04-25.alog',None)])
    tbl_Examples.add_row([QApplication.translate('HelpDlg','~batchcounter ~title ~date_long',None),QApplication.translate('HelpDlg','1380 Burundi 2020-04-25_1136.alog',None)])
    tbl_Examples.add_row([QApplication.translate('HelpDlg','~beans ~machine ~drumspeedRPM ~weight~weightunits ~poisturePCT ~operator ~date ~batch(~batchposition)',None),QApplication.translate('HelpDlg','Burundi Kiganda Murambi Lot44 SF-25 64RPM 10.3Kg 10.2PCT Roberto 20-04-25 Prod-1380(6).alog',None)])
    tbl_Examples.add_row([QApplication.translate('HelpDlg','\u0027Recording ~batchcounter&#39; "~batch" ~title ~datetime_long',None),QApplication.translate('HelpDlg','When OFF:\nProd-1380 Burundi Kiganda Murambi 2020-04-25_1136.alog\nWhile Recording:\nRecording 1380  Burundi KigandaMurambi 2020-04-25_1136.alog',None)])
    strlist.append(tbl_Examples.get_html_string(attributes={"width":"100%","border":"1","padding":"1","border-collapse":"collapse"}))
    strlist.append("</body>")
    helpstr = "".join(strlist)
    helpstr = re.sub(r"&amp;", r"&",helpstr)
    return helpstr