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
    strlist.append('<b>')
    strlist.append(QApplication.translate('HelpDlg','ALARMS'))
    strlist.append('</b>')
    tbl_Alarmstop = prettytable.PrettyTable()
    tbl_Alarmstop.header = False
    tbl_Alarmstop.add_row([QApplication.translate('HelpDlg','Each alarm is only triggered once.\nAlarms are scanned in order from the top of the table to the bottom.')])
    strlist.append(tbl_Alarmstop.get_html_string(attributes={'width':'100%','border':'1','padding':'1','border-collapse':'collapse'}))
    tbl_Alarms = prettytable.PrettyTable()
    tbl_Alarms.field_names = [QApplication.translate('HelpDlg','Field'),QApplication.translate('HelpDlg','Description')]
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Nr'),QApplication.translate('HelpDlg','Alarm number for reference.')])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Status'),QApplication.translate('HelpDlg','Activate or Deactivate the alarm.')])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','If Alarm'),QApplication.translate('HelpDlg','Alarm triggered only if the alarm with the given number was triggered before. Use 0 for no guard.')])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','But Not'),QApplication.translate('HelpDlg','Alarm triggered only if the alarm with the given number was not triggered before. Use 0 for no guard.')])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','From'),QApplication.translate('HelpDlg','Alarm only triggered after the given event.')])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Time'),QApplication.translate('HelpDlg','If not 00:00, alarm is triggered mm:ss after the event "From" happens.')])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Source'),QApplication.translate('HelpDlg','The observed temperature source.')])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Condition'),QApplication.translate('HelpDlg','Alarm is triggered if source rises above or below the specified temperature.')])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Temp'),QApplication.translate('HelpDlg','The specified temperature limit.')])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Action'),QApplication.translate('HelpDlg','The action to be triggered if all conditions are fulfilled.')])
    tbl_Alarms.add_row([QApplication.translate('HelpDlg','Description'),QApplication.translate('HelpDlg','Commands for alarms with an action go here.  Anything after a &#39;#&#39; character is considered a comment and is ignored when processing the alarm.  ')])
    strlist.append(tbl_Alarms.get_html_string(attributes={'width':'100%','border':'1','padding':'1','border-collapse':'collapse'}))
    strlist.append('<br/><br/><b>')
    strlist.append(QApplication.translate('HelpDlg','ALARM CONFIGURATION OPTIONS'))
    strlist.append('</b>')
    tbl_Options = prettytable.PrettyTable()
    tbl_Options.field_names = [QApplication.translate('HelpDlg','Option'),QApplication.translate('HelpDlg','Description')]
    tbl_Options.add_row([QApplication.translate('HelpDlg','Add'),QApplication.translate('HelpDlg','Adds a new alarm to the bottom of the table.')])
    tbl_Options.add_row([QApplication.translate('HelpDlg','Insert'),QApplication.translate('HelpDlg','Inserts a new alarm above the selected alarm.')])
    tbl_Options.add_row([QApplication.translate('HelpDlg','Delete'),QApplication.translate('HelpDlg','Deletes the selected alarm.')])
    tbl_Options.add_row([QApplication.translate('HelpDlg','Copy Table'),QApplication.translate('HelpDlg','Copy the alarm table in tab separated format to the clipboard.  Option or ALT click to copy a tabular format to the clipboard.')])
    tbl_Options.add_row([QApplication.translate('HelpDlg','All On'),QApplication.translate('HelpDlg','Enables all alarms.')])
    tbl_Options.add_row([QApplication.translate('HelpDlg','All Off'),QApplication.translate('HelpDlg','Disables all alarms.')])
    tbl_Options.add_row([QApplication.translate('HelpDlg','Load'),QApplication.translate('HelpDlg','Load alarm definition from a file.')])
    tbl_Options.add_row([QApplication.translate('HelpDlg','Save'),QApplication.translate('HelpDlg','Save the alarm definitions to a file.')])
    tbl_Options.add_row([QApplication.translate('HelpDlg','Clear'),QApplication.translate('HelpDlg','Clears all alarms from the table.')])
    tbl_Options.add_row([QApplication.translate('HelpDlg','Help'),QApplication.translate('HelpDlg','Opens this window.')])
    tbl_Options.add_row([QApplication.translate('HelpDlg','Load from Profile'),QApplication.translate('HelpDlg','when ticked will replace the alarm table when loading a profile with the alarms stored in the profile.  If there are no alarms in the profile the alarm table will be cleared.')])
    tbl_Options.add_row([QApplication.translate('HelpDlg','Load from Background'),QApplication.translate('HelpDlg','when ticked will replace the alarm table when loading a background profile with the alarms stored in the profile.  If there are no alarms in the profile the alarm table will be cleared.')])
    tbl_Options.add_row([QApplication.translate('HelpDlg','PopUp TimeOut'),QApplication.translate('HelpDlg','A PopUp will automatically close after this time if the OK button has not been clicked.')])
    strlist.append(tbl_Options.get_html_string(attributes={'width':'100%','border':'1','padding':'1','border-collapse':'collapse'}))
    strlist.append('<br/><br/><b>')
    strlist.append(QApplication.translate('HelpDlg','Alarm Actions'))
    strlist.append('</b>')
    tbl_Actionstop = prettytable.PrettyTable()
    tbl_Actionstop.header = False
    tbl_Actionstop.add_row([QApplication.translate('HelpDlg','Enter the Command into the Description field of the Alarm.')])
    strlist.append(tbl_Actionstop.get_html_string(attributes={'width':'100%','border':'1','padding':'1','border-collapse':'collapse'}))
    tbl_Actions = prettytable.PrettyTable()
    tbl_Actions.field_names = [QApplication.translate('HelpDlg','Action'),QApplication.translate('HelpDlg','Command'),QApplication.translate('HelpDlg','Meaning')]
    tbl_Actions.add_row([QApplication.translate('HelpDlg','Pop Up'),QApplication.translate('HelpDlg','<text>'),QApplication.translate('HelpDlg','the text to  be displayed in the pop up')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','Call Program'),QApplication.translate('HelpDlg','A program/script path (absolute or relative)'),QApplication.translate('HelpDlg','start an external program')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','Event Button'),QApplication.translate('HelpDlg','<button number>'),QApplication.translate('HelpDlg','triggers the button, the button number comes from the Events Buttons configuration')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','Slider <1>'),QApplication.translate('HelpDlg','<value>'),QApplication.translate('HelpDlg','set the slider for special event nr. 1 to the value')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','Slider <2>'),QApplication.translate('HelpDlg','<value>'),QApplication.translate('HelpDlg','set the slider for special event nr. 2 to the value')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','Slider <3>'),QApplication.translate('HelpDlg','<value>'),QApplication.translate('HelpDlg','set the slider for special event nr. 3 to the value')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','Slider <4>'),QApplication.translate('HelpDlg','<value>'),QApplication.translate('HelpDlg','set the slider for special event nr. 4 to the value')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','START'),'&#160;',QApplication.translate('HelpDlg','trigger START')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','DRY'),'&#160;',QApplication.translate('HelpDlg','trigger the DRY event')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','FCs'),'&#160;',QApplication.translate('HelpDlg','trigger the FCs event')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','FCe'),'&#160;',QApplication.translate('HelpDlg','trigger the FCe event')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','SCs'),'&#160;',QApplication.translate('HelpDlg','trigger the SCs event')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','SCe'),'&#160;',QApplication.translate('HelpDlg','trigger the SCe event')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','DROP'),'&#160;',QApplication.translate('HelpDlg','trigger the DROP event')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','COOL END'),'&#160;',QApplication.translate('HelpDlg','trigger the COOL END event')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','OFF'),'&#160;',QApplication.translate('HelpDlg','trigger OFF')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','CHARGE'),'&#160;',QApplication.translate('HelpDlg','trigger the CHARGE event')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','RampSoak ON'),'&#160;',QApplication.translate('HelpDlg','turns PID on and switches to RampSoak mode')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','RampSoak OFF'),'&#160;',QApplication.translate('HelpDlg','turns PID off and switches to manual mode')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','Set Canvas Color'),QApplication.translate('HelpDlg','<color>'),QApplication.translate('HelpDlg','sets the canvas to <color>, can be in hex format, e.g. "#ffaa55" or a color name, e.g. "blue"')])
    tbl_Actions.add_row([QApplication.translate('HelpDlg','Reset Canvas Color'),'&#160;',QApplication.translate('HelpDlg','reset the canvas color to the color specified in Config>>Colors\ncanvas color resets automatically at OFF')])
    strlist.append(tbl_Actions.get_html_string(attributes={'width':'100%','border':'1','padding':'1','border-collapse':'collapse'}))
    strlist.append('</body>')
    helpstr = ''.join(strlist)
    helpstr = re.sub(r'&amp;', r'&',helpstr)
    return helpstr
