#
# ABOUT
# ROEST CSV Roast Profile importer for Artisan

from pathlib import Path
import os
import csv
import re
import requests
import logging
from collections.abc import Callable
from typing import TypedDict, Final, NotRequired, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import

from PyQt6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout,
    QVBoxLayout, QLabel, QLineEdit, QToolButton, QDialogButtonBox, QComboBox)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QKeySequence, QAction, QIcon

from artisanlib.util import encodeLocalStrict, getResourcePath
from artisanlib.atypes import ProfileData
from artisanlib.dialogs import ArtisanDialog

_log: Final[logging.Logger] = logging.getLogger(__name__)


GET_TOKEN_URL = 'https://api.roestcoffee.com/o/token/'
GET_MACHINES_URL = 'https://api.roestcoffee.com/machines'

CONNECT_TIMEOUT:int = 3
READ_TIMEOUT:int = 5

clientId:str = ''
clientSecret:str = ''

class RoestMachine(TypedDict):
    name:str
    # MQTT config
    mqtt_user:str
    mqtt_password:str
    mqtt_topic:str
    # core data
    p3000:NotRequired[bool]  # adds target and hopper temperature, among others
    machine_image:NotRequired[str]
    # sensor config
    has_inlet:NotRequired[bool]
    has_drum:NotRequired[bool]
    has_pressure:NotRequired[bool]
    # additional information
    elevation: NotRequired[int]
    next_batch_number: NotRequired[int]


def getRequestToken(client_id:str, client_secret:str) -> str:
    token:str = ''
    try:
        _log.debug('requesting access token')
        res = requests.post(GET_TOKEN_URL,
            files = {'client_id': (None, client_id), 'client_secret': (None, client_secret), 'grant_type': (None, 'client_credentials')},
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            allow_redirects=False)
        if res.status_code == 200:
            data = res.json()
            data.get('access_token', '')
            if 'access_token' in data:
                _log.debug('access token received')
                token = data['access_token']
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)
    return token

def getMachines(client_id:str, client_secret:str) -> list[RoestMachine]:
    token:str = getRequestToken(client_id, client_secret)
    machines:list[RoestMachine] = []
    if token:
        try:
            _log.debug('requesting machines')
            res = requests.get(
                GET_MACHINES_URL,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                params = {'page_size': 'all'},
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'})
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    for item in data:
                        try:
                            # access fails if necessary MQTT data not available
                            mqtt_conf = item['mqtt_config']
                            # essential MQTT data
                            machine:RoestMachine = {
                                'name': item['name'],
                                'mqtt_user': mqtt_conf['username'],
                                'mqtt_password': mqtt_conf['subscribe_password'],
                                'mqtt_topic': mqtt_conf['topic']}
                            # sensor config
                            if 'sensor_config' in item:
                                sensor_conf = item['sensor_config']
                                if 'has_inlet' in sensor_conf and isinstance(sensor_conf['has_inlet'], bool):
                                    machine['has_inlet'] = sensor_conf['has_inlet']
                                if 'has_drum' in sensor_conf and isinstance(sensor_conf['has_drum'], bool):
                                    machine['has_drum'] = sensor_conf['has_drum']
                                if 'has_pressure' in sensor_conf and isinstance(sensor_conf['has_pressure'], bool):
                                    machine['has_pressure'] = sensor_conf['has_pressure']
                            #
                            if 'is_p2000' in item and isinstance(item['is_p2000'], bool):
                                machine['p3000'] = item['is_p2000']
                            if 'machine_image' in item and isinstance(item['machine_image'], str):
                                machine['machine_image'] = item['machine_image'].upper()
                            try:
                                if 'next_batch_no' in item and isinstance(item['next_batch_no'], int):
                                    machine['next_batch_number'] = item['next_batch_no']
                                if 'elevation' in item and isinstance(item['elevation'], int):
                                    machine['elevation'] = item['elevation']
                            except Exception: # pylint: disable=broad-except
                                pass
                            machines.append(machine)
                        except Exception as e: # pylint: disable=broad-except
                            _log.error(e)
                    _log.debug('machines received')
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
    return sorted(machines, key=lambda d: d['name'])




###

# returns a dict containing all profile information contained in the given ROEST CSV file
def extractProfileRoestCSV(file:str,
        _etypesdefault:list[str],
        alt_etypesdefault:list[str],
        _artisanflavordefaultlabels:list[str],
        eventsExternal2InternalValue:Callable[[int],float]) -> ProfileData:
    res:ProfileData = ProfileData() # the interpreted data set

    res['samplinginterval'] = 1.0

    res['roastertype'] = 'ROEST Sample Roaster'
    res['roastersize'] = 0.1
    res['roasterheating'] = 3 # electric

    # set profile title and batch number from the file name if it has the format "<name> - Batch <nnnn>.csv"
    try:
        filename = os.path.basename(file)
        p = re.compile(r'([^-]*) - Batch (\d{1,6}).csv')
        match = p.match(filename)
        if match is not None:
            groups = match.groups()
            if len(groups) == 2:
                res['title'] = encodeLocalStrict(groups[0])
                res['roastbatchnr'] = int(groups[1])
            else:
                res['title'] = encodeLocalStrict(Path(file).stem)
    except Exception as e: # pylint: disable=broad-except
        _log.exception(e)

    with open(file, newline='',encoding='utf-8-sig') as csvFile:
        data = csv.reader(csvFile,delimiter=',')
        #read file header
        header = [h.strip() for h in next(data)]

        total_cracks_header_item:str|None = None
        try:
            total_cracks_header_item = next(item for item in header if item.startswith('Total cracks'))
        except StopIteration:
            pass

        fan:float|None = None # holds last processed fan event value
        fan_last:float|None = None # holds the fan event value before the last one
        heater:float|None = None # holds last processed heater event value
        heater_last:float|None = None # holds the heater event value before the last one
        drum:float|None = None # holds last processed drum speed event value
        drum_last:float|None = None # holds the drum speed event value before the last one

        specialevents:list[int] = []
        specialeventstype:list[int] = []
        specialeventsvalue:list[float] = []
        specialeventsStrings:list[str] = []

        timex:list[float] = []
        temp1:list[float] = []
        temp2:list[float] = []

        extra1:list[float] = []  # Drum temp (°C)
        extra2:list[float] = []  # Inlet temp (°C)
        extra3:list[float] = []  # Heater (%)
        extra4:list[float] = []  # Fan (%)
        extra5:list[float] = []  # RPM (RPM)
        extra6:list[float] = []  # Events
        extra7:list[float] = []  # Cracks
        extra8:list[float] = []  # Pressure
        extra9:list[float] = []  # Exhaust Temp (°C)
        extra10:list[float] = [] # Target (°C)
        extra11:list[float] = [] # Total cracks
        extra12:list[float] = [] # --


        v:float|None


        timeindex:list[int] = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actual index used
        i:int = -1
        for row in data:
            i += 1
            items = list(zip(header, row, strict=True))
            item:dict[str,str] = {}
            for (name, value) in items:
                item[name] = value.strip()
            # take i as time in seconds
            try:
                timex.append(float(item['Time'])/1000)
            except Exception:  # pylint: disable=broad-except
                timex.append(i)

            if 'Air temp (°C)' in item:
                temp1.append(float(item['Air temp (°C)']))
            else:
                temp1.append(-1)

            if 'Bean temp (°C)' in item:
                temp2.append(float(item['Bean temp (°C)']))
            else:
                temp2.append(-1)

            # mark CHARGE
            if timeindex[0] < 0:
                timeindex[0] = max(0,i)

            # mark DRY
            if item['Event'].strip() == 'Yellowing' and timeindex[1] == 0:
                timeindex[1] = i

            # mark FCs
            if item['Event'].strip() == 'Firstcrack' and timeindex[2] == 0:
                timeindex[2] = i




            if 'Drum temp (°C)' in item:
                extra1.append(float(item['Drum temp (°C)']))
            else:
                extra2.append(-1)

            if 'Inlet temp (°C)' in item:
                extra2.append(float(item['Inlet temp (°C)']))
            else:
                extra2.append(-1)

            if 'Power (%)' in item:
                extra3.append(float(item['Power (%)']))
            else:
                extra3.append(-1)

            if 'Fan (%)' in item:
                extra4.append(float(item['Fan (%)']))
            else:
                extra4.append(-1)

            if 'RPM (RPM)' in item:
                extra5.append(float(item['RPM (RPM)']))
            else:
                extra5.append(-1)

            # unused (events)
            extra6.append(-1)

            # unused (cracks)
            extra7.append(-1)

            # unused (pressure)
            extra8.append(-1)

            if 'Exhaust Temp (°C)' in item:
                extra9.append(float(item['Exhaust Temp (°C)']))
            else:
                extra9.append(-1)

            if 'Target (°C)' in item:
                extra10.append(float(item['Target (°C)']))
            else:
                extra10.append(-1)

            # unused (total cracks)
            if total_cracks_header_item is not None and total_cracks_header_item in item:
                extra11.append(float(item[total_cracks_header_item]))
            else:
                extra11.append(-1)

            # unused
            extra12.append(-1)



            if 'Fan (%)' in item:
                try:
                    v = float(item['Fan (%)'])
                    if v != fan:
                        # fan value changed
                        if v == fan_last:
                            # just a fluctuation, we remove the last added fan value again
                            fan_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 0)
                            del specialeventsvalue[fan_last_idx]
                            del specialevents[fan_last_idx]
                            del specialeventstype[fan_last_idx]
                            del specialeventsStrings[fan_last_idx]
                            fan = fan_last
                            fan_last = None
                        else:
                            fan_last = fan
                            fan = v
                            v = v/10. + 1
                            specialeventsvalue.append(v)
                            specialevents.append(i)
                            specialeventstype.append(0)
                            specialeventsStrings.append(f'{fan}' + '%')
                    else:
                        fan_last = None
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)

            if 'RPM (RPM)' in item:
                try:
                    v = float(item['RPM (RPM)'])
                    if v != drum:
                        # drum value changed
                        if v == drum_last:
                            # just a fluctuation, we remove the last added drum value again
                            drum_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 1)
                            del specialeventsvalue[drum_last_idx]
                            del specialevents[drum_last_idx]
                            del specialeventstype[drum_last_idx]
                            del specialeventsStrings[drum_last_idx]
                            heater = heater_last
                            heater_last = None
                        drum_last = drum
                        drum = v
                        v = v/10. + 1
                        specialeventsvalue.append(v)
                        specialevents.append(i)
                        specialeventstype.append(1)
                        specialeventsStrings.append(f'{drum}' + '%')
                    else:
                        drum_last = None
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)

            if 'Power (%)' in item:
                try:
                    v = float(item['Power (%)'])
                    if v != heater:
                        # heater value changed
                        if v == heater_last:
                            # just a fluctuation, we remove the last added heater value again
                            heater_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 3)
                            del specialeventsvalue[heater_last_idx]
                            del specialevents[heater_last_idx]
                            del specialeventstype[heater_last_idx]
                            del specialeventsStrings[heater_last_idx]
                            heater = heater_last
                            heater_last = None
                        heater_last = heater
                        heater = v
                        specialeventsvalue.append(eventsExternal2InternalValue(int(round(v))))
                        specialevents.append(i)
                        specialeventstype.append(3)
                        specialeventsStrings.append(f'{heater}' + '%')
                    else:
                        heater_last = None
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)

    # mark DROP
    if timeindex[6] == 0:
        timeindex[6] = max(0,i)

    res['mode'] = 'C'

    res['timex'] = timex
    res['temp1'] = temp1
    res['temp2'] = temp2
    res['timeindex'] = timeindex

    res['extradevices'] = [202, 203, 204, 205, 206, 50]
    res['extratimex'] = [timex[:],timex[:],timex[:],timex[:],timex[:],timex[:]]

    res['extraname1'] = ['DT', '{3}', '{1}', 'cracks', 'XT', 'total cracks']
    res['extratemp1'] = [extra1, extra3, extra5, extra7, extra9, extra11]
    res['extramathexpression1'] = ['', '', '', '', '', '']

    res['extraname2'] = ['IT', '{0}', 'event', 'pressure', 'target', 'Extra 2']
    res['extratemp2'] = [extra2, extra4, extra6, extra8, extra10, extra12]
    res['extramathexpression2'] = ['', '', '', '', '', '']

    res['extraCurveVisibility1'] = [False, True, False, False, False, True, True, True, True, True]
    res['extraCurveVisibility2'] = [True, True, False, False, False, False, True, True, True, True]
    res['extraDelta1'] = [False]*10
    res['extraDelta2'] = [False]*10
    res['extraNoneTempHint1'] = [False, True, True, True, False, True]
    res['extraNoneTempHint2'] = [False, True, True, True, False, True]

    if len(specialevents) > 0:
        res['specialevents'] = specialevents
        res['specialeventstype'] = specialeventstype
        res['specialeventsvalue'] = specialeventsvalue
        res['specialeventsStrings'] = specialeventsStrings

    res['etypes'] = [encodeLocalStrict(etype) for etype in alt_etypesdefault]

    return res

class ROESTdialog(ArtisanDialog):

    __slots__ = [ 'client_id', 'client_secret', 'machines' ]

    def __init__(self, aw:'ApplicationWindow', client_id:str, client_secret:str) -> None:
        super().__init__(aw,aw)

        self.client_id:str = client_id
        self.client_secret:str = client_secret

        self.machines:list[RoestMachine] = []
        self.selected_machine:RoestMachine|None

        self.dialogbuttons.accepted.connect(self.setCredentials)
        self.dialogbuttons.rejected.connect(self.reject)

        self.ok_button = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if self.ok_button is not None:
            self.ok_button.setEnabled(False)
            self.ok_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.cancel_button = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Cancel)
        if self.cancel_button is not None:
            self.cancel_button.setDefault(True)
            # add additional CMD-. shortcut to close the dialog
            self.cancel_button.setShortcut(QKeySequence('Ctrl+.'))
            # add additional CMD-W shortcut to close this dialog
            cancelAction:QAction = QAction(self)
            cancelAction.triggered.connect(self.reject)
            cancelAction.setShortcut(QKeySequence.StandardKey.Cancel)
            self.cancel_button.addActions([cancelAction])


        self.labelTitle:QLabel = QLabel('ROEST')

        self.textClientId:QLineEdit = QLineEdit(self)
        self.textClientId.setMinimumWidth(300)
        self.textClientId.setPlaceholderText('Client Id')
        self.textClientId.setText(self.client_id)

        self.textClientSecret:QLineEdit = QLineEdit(self)
        self.textClientSecret.setPlaceholderText('Secret')
        self.textClientSecret.setText(self.client_secret)

        self.textClientId.textChanged.connect(self.textChanged)
        self.textClientSecret.textChanged.connect(self.textChanged)

        self.buttonUpdate = QToolButton()
        self.buttonUpdate.setToolTip(QApplication.translate('Tooltip','Update machines'))
        if self.aw.app.darkmode:
            self.buttonUpdate.setStyleSheet('''
                QToolButton:hover:pressed {border:none;border-radius:3px;background-color:#C5C5C5;color: #EEEEEE;}
                QToolButton:!hover {border:none;}
                QToolButton:hover {border:none;border-radius: 3px;background-color: #8F8F8F;color: #EEEEEE;}
                ''')
        else:
            self.buttonUpdate.setStyleSheet('''
                QToolButton:hover:pressed {border:none;border-radius:3px;background-color:#C5C5C5;color:#EEEEEE;}
                QToolButton:!hover {border:none;}
                QToolButton:hover {border:none;border-radius:3px;background-color:#CFCFCF;color:#EEEEEE;}
                ''')
        self.buttonUpdate.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.buttonUpdate.setEnabled(self.client_id != '' and self.client_secret != '')
        self.buttonUpdate.clicked.connect(self.trigger_machine_update)

        basedir = os.path.join(getResourcePath(),'Icons')
        p = os.path.join(basedir, ('update_dark.svg' if self.aw.app.darkmode else 'update_light.svg'))
        self.buttonUpdate.setIcon(QIcon(p))

        self.machinesCombo = QComboBox()


        #

        titleLabelLayout:QHBoxLayout = QHBoxLayout()
        titleLabelLayout.addStretch()
        titleLabelLayout.addWidget(self.labelTitle)
        titleLabelLayout.addStretch()

        credentialsLayout:QVBoxLayout = QVBoxLayout(self)
        credentialsLayout.addWidget(self.textClientId)
        credentialsLayout.addWidget(self.textClientSecret)

        credentialsGroup:QGroupBox = QGroupBox()
        credentialsGroup.setLayout(credentialsLayout)

        machinesLayout = QHBoxLayout()
        machinesLayout.addWidget(self.machinesCombo)
        machinesLayout.addWidget(self.buttonUpdate)

        machineGroup:QGroupBox = QGroupBox('Machine')
        machineGroup.setLayout(machinesLayout)


        buttonLayout:QHBoxLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.dialogbuttons)
        buttonLayout.addStretch()

        layout:QVBoxLayout = QVBoxLayout(self)
        layout.addLayout(titleLabelLayout)
        layout.addWidget(credentialsGroup)
        layout.addSpacing(5)
        layout.addWidget(machineGroup)
        layout.addLayout(buttonLayout)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

    @pyqtSlot(str)
    def textChanged(self, _:str) -> None:
        credentials_available:bool = self.textClientId.text() != '' and self.textClientSecret.text() != ''
        self.buttonUpdate.setEnabled(credentials_available)

    @pyqtSlot(bool)
    def trigger_machine_update(self, _:bool = False) -> None:
        self.machines = getMachines(self.textClientId.text(), self.textClientSecret.text())
        self.machinesCombo.clear()
        if self.ok_button is not None and self.machines:
            if self.cancel_button is not None:
                self.cancel_button.setDefault(False)
                self.cancel_button.setAutoDefault(False)
            self.ok_button.setDefault(True)
            self.ok_button.setEnabled(True)
        self.machinesCombo.addItems([(f"{m['name']} ({m['machine_image']})" if 'machine_image' in m else m['name']) for m in self.machines])


    @pyqtSlot()
    def setCredentials(self) -> None:
        self.client_id = self.textClientId.text()
        self.client_secret = self.textClientSecret.text()
        self.selected_machine = None
        if self.machines:
            try:
                machine_idx = self.machinesCombo.currentIndex()
                self.selected_machine = self.machines[machine_idx]
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
        self.accept()


# returns selected machine on success
def selectROESTmachine(aw:'ApplicationWindow') -> RoestMachine|None:
    global clientId, clientSecret # pylint:disable=global-statement
    rd = ROESTdialog(aw, clientId, clientSecret)
    rd.setWindowFlags(Qt.WindowType.Sheet)
    rd.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
    if rd.exec():
        # login dialog not canceled
        clientId = rd.client_id
        clientSecret = rd.client_secret
        return rd.selected_machine
    return None
