import prettytable
import re
try:
    from PyQt6.QtWidgets import QApplication # @Reimport @UnresolvedImport @UnusedImport # pylint: disable=import-error
except Exception: # pylint: disable=broad-except
    from PyQt5.QtWidgets import QApplication # type: ignore # @Reimport @UnresolvedImport @UnusedImport

def content():
    strlist = []
    helpstr = ''  # noqa: F841 #@UnusedVariable # pylint: disable=unused-variable
    newline = '\n'  # noqa: F841 #@UnusedVariable  # pylint: disable=unused-variable
    strlist.append('<head><style> td, th {border: 1px solid #ddd;  padding: 6px;} th {padding-top: 6px;padding-bottom: 6px;text-align: left;background-color: #0C6AA6; color: white;} </style></head> <body>')
    strlist.append('<b>')
    strlist.append(QApplication.translate('HelpDlg','PORTS CONFIGURATION'))
    strlist.append('</b>')
    tbl_Modbus = prettytable.PrettyTable()
    tbl_Modbus.field_names = [QApplication.translate('HelpDlg','MODBUS SETTINGS')]
    tbl_Modbus.add_row([QApplication.translate('HelpDlg','The MODBUS serial protocols RTU, ASCII, and Binary is using the specified serial port parameters. The MODBUS IP protocol on TCP and UDP is respecting the host IP and port.')])
    tbl_Modbus.add_row([QApplication.translate('HelpDlg','The inputs 1+2 configure the MODBUS device, inputs 3+4 configure the MODBUS_34 device and so on.\nInputs with the slave id set to 0 are turned off.')])
    tbl_Modbus.add_row([QApplication.translate('HelpDlg','Function 1 (Read Coils): registers 0 to 65535 corresponding to numbers 000001 to 065536\nFunction 2 (Read Discrete Inputs): registers 0 to 65535 corresponding to numbers 100001 to 165536\nFunction 3 (Read Multiple Holding Registers): registers 0 to 65535 corresponding to numbers 400001 to 465536\nFunction 4 (Read Input Registers): registers 0 to 65535 corresponding to numbers 300001 to 365536')])
    tbl_Modbus.add_row([QApplication.translate('HelpDlg','Dividers 1/10 and 1/100 can be set to recreate decimals of floats transported as integers multiplied by 10 or 100. Eg. a value of 145.2 might be transmitted as 1452, which is turned back into 145.2 by the 1/10 divider.')])
    tbl_Modbus.add_row([QApplication.translate('HelpDlg','Temperature readings are automatically converted based on the specified unit per input channel.')])
    tbl_Modbus.add_row([QApplication.translate('HelpDlg','If a 32bit decoder is set two succeeding 16bit registers are requested and the received 4 bytes are interpreted using the byte and word order as specified by the corresponding flag.')])
    tbl_Modbus.add_row([QApplication.translate('HelpDlg','The PID Control dialog can operate a connected PID slave using the given PID registers to set the p-i-d parameters and the set value (SV). MODBUS commands can be specified to turn the PID slave on and off from that PID Control dialog. See the help page in the Events Dialog for documentation of available MODBUS write commands.')])
    tbl_Modbus.add_row([QApplication.translate('HelpDlg','The Scan button opens a simple MODBUS scanner to search for data holding registers in the connected device.')])
    tbl_Modbus.add_row([QApplication.translate('HelpDlg','Refer to the User Manual of your MODBUS device for information specific to the setup required for your device.')])
    strlist.append(tbl_Modbus.get_html_string(attributes={'width':'100%','border':'1','padding':'1','border-collapse':'collapse'}))
    strlist.append('</body>')
    helpstr = ''.join(strlist)
    return re.sub(r'&amp;', r'&',helpstr)
