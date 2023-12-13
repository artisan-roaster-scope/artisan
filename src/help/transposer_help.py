import prettytable
import re
try:
    from PyQt6.QtWidgets import QApplication # @Reimport @UnresolvedImport @UnusedImport # pylint: disable=import-error
except Exception: # pylint: disable=broad-except
    from PyQt5.QtWidgets import QApplication # type: ignore # @Reimport @UnresolvedImport @UnusedImport

def content() -> str:
    strlist = []
    helpstr = ''  # noqa: F841 #@UnusedVariable # pylint: disable=unused-variable
    newline = '\n'  # noqa: F841 #@UnusedVariable  # pylint: disable=unused-variable
    strlist.append('<head><style> td, th {border: 1px solid #ddd;  padding: 6px;} th {padding-top: 6px;padding-bottom: 6px;text-align: left;background-color: #0C6AA6; color: white;} </style></head> <body>')
    strlist.append('<b>')
    strlist.append(QApplication.translate('HelpDlg','TRANSPOSER'))
    strlist.append('</b>')
    tbl_Transposertop = prettytable.PrettyTable()
    tbl_Transposertop.header = False
    tbl_Transposertop.add_row([QApplication.translate('HelpDlg','The Transposer allows to map the current profile w.r.t. the time and temperature axis by setting targets time and temperature at major events like yellow point (DRY END) or first crack (FC START) or for time transformations also by target phases duration. Temperature transformation are only applied to the bean temperature (BT) curve while time transformations are applied to the whole profile.\n\nThree different mapping methods are available to compute from the current profile and the given targets a resulting profile. The linear and quadratic mappings are continuous functions while the discrete option is defined stepwise between the given source/target pairs and extended at the borders\n\nPressing the "Apply" button applies the current computed mapping to the loaded profile for inspection. "Reset" returns to the original profile shape. Leaving the Transposer with "OK" applies the current mapping to the profile. Leaving the Transposer with "Cancel" returns to the unchanged initially loaded profile.')])
    strlist.append(tbl_Transposertop.get_html_string(attributes={'width':'100%','border':'1','padding':'1','border-collapse':'collapse'}))
    strlist.append('<br/><br/><b>')
    strlist.append(QApplication.translate('HelpDlg','EXAMPLE 1: ADJUST TOTAL ROAST TIME'))
    strlist.append('</b>')
    tbl_Ex1AdjustTotalRoastTimetop = prettytable.PrettyTable()
    tbl_Ex1AdjustTotalRoastTimetop.header = False
    tbl_Ex1AdjustTotalRoastTimetop.add_row([QApplication.translate('HelpDlg','You might want to re-roast a profile, but extended/restricted to a total length of 10:00. \n\nLoad the profile and start the Transposer under Tools. Enter our target roast time of "10:00" minutes into the target DROP field under Time and select "linear" as mapping. Check the resulting times of the main events in the time tables last row, press "Apply" to view the transposed profile in the graph. If you are happy with the result, press "OK" and save the newly generated transposed profile such that you can use it as a template for future roasts.')])
    strlist.append(tbl_Ex1AdjustTotalRoastTimetop.get_html_string(attributes={'width':'100%','border':'1','padding':'1','border-collapse':'collapse'}))
    strlist.append('<br/><br/><b>')
    strlist.append(QApplication.translate('HelpDlg','EXAMPLE 2: MAP BETWEEN TWO ROASTING MACHINES'))
    strlist.append('</b>')
    tbl_Ex2MapBetweenTwoRoastingMatop = prettytable.PrettyTable()
    tbl_Ex2MapBetweenTwoRoastingMatop.header = False
    tbl_Ex2MapBetweenTwoRoastingMatop.add_row([QApplication.translate('HelpDlg','Transpose temperature readings from your smaller machine to your larger machine assuming on your larger machine the DRY and FC START events happen at different temperatures than on your smaller one.\n\nLoad the profile recorded on the smaller machine and open the Transposer. Select the linear mapping and put the DRY and FC START target temperatures as observed on your larger machine into the into the corresponding fields under BT. Underneath the table you see the calculated symbolic formula that can be copy-pasted into the BT symbolic formula under Config >> Devices to adjust the computed mapping automatically while roasting on your smaller machine to see the temperature reading as you expect them on the larger machine.')])
    strlist.append(tbl_Ex2MapBetweenTwoRoastingMatop.get_html_string(attributes={'width':'100%','border':'1','padding':'1','border-collapse':'collapse'}))
    strlist.append('</body>')
    helpstr = ''.join(strlist)
    return re.sub(r'&amp;', r'&',helpstr)
