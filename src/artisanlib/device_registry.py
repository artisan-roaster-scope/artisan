#
# ABOUT
# Device Registry for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# pyright: basic

from typing import Final

from artisanlib.util import deltaLabelUTF8


# ADD DEVICE: to add a device you have to modify several places. Search for the tag "ADD DEVICE:" in the code
# (check also the tags in comm.py and devices.py!!)
# - add to DEVICES
# NOTE: the index of the elements in this list is one less than the device id indicated in the comment below
# The index of device "NONE" in DEVICES is 17 not 18!
DEVICES: Final[list[str]] = [
    # Fuji PID               #0
    'Omega HH806AU',         #1
    'Omega HH506RA',         #2
    'CENTER 309',            #3
    'CENTER 306',            #4
    'CENTER 305',            #5
    'CENTER 304',            #6
    'CENTER 303',            #7
    'CENTER 302',            #8
    'CENTER 301',            #9
    'CENTER 300',            #10
    'VOLTCRAFT K204',        #11
    'VOLTCRAFT K202',        #12
    'VOLTCRAFT 300K',        #13
    'VOLTCRAFT 302KJ',       #14
    'EXTECH 421509',         #15
    'Omega HH802U',          #16
    'Omega HH309',           #17
    'NONE',                  #18
    '-ARDUINOTC4',           #19
    'TE VA18B',              #20
    '+CENTER 309 34',        #21
    '+PID SV/DUTY %',        #22
    'Omega HHM28[6]',        #23
    '+VOLTCRAFT K204 34',    #24
    '+Virtual',              #25
    '-DTAtemperature',       #26
    'Program',               #27
    '+ArduinoTC4 34',        #28
    'MODBUS',                #29
    'VOLTCRAFT K201',        #30
    'Amprobe TMD-56',        #31
    '+ArduinoTC4 56',        #32
    '+MODBUS 34',            #33
    'Phidget 1048 4xTC 01',  #34
    '+Phidget 1048 4xTC 23', #35
    '+Phidget 1048 4xTC AT', #36
    'Phidget 1046 4xRTD 01', #37
    '+Phidget 1046 4xRTD 23',#38
    'Mastech MS6514',        #39
    'Phidget IO 01',         #40
    '+Phidget IO 23',        #41
    '+Phidget IO 45',        #42
    '+Phidget IO 67',        #43
    '+ArduinoTC4 78',        #44
    'Yocto Thermocouple',    #45
    'Yocto PT100',           #46
    'Phidget 1045 IR',       #47
    '+Program 34',           #48
    '+Program 56',           #49
    'DUMMY',                 #50
    '+CENTER 304 34',        #51
    'Phidget 1051 1xTC 01',  #52
    'Hottop BT/ET',          #53
    '+Hottop Heater/Fan',    #54
    '+MODBUS 56',            #55
    'Apollo DT301',          #56
    'EXTECH 755',            #57
    'Phidget TMP1101 4xTC 01',  #58
    '+Phidget TMP1101 4xTC 23', #59
    '+Phidget TMP1101 4xTC AT', #60
    'Phidget TMP1100 1xTC',     #61
    'Phidget 1011 IO 01',       #62
    'Phidget HUB IO 01',        #63
    '+Phidget HUB IO 23',       #64
    '+Phidget HUB IO 45',       #65
    '-Omega HH806W',            #66 NOT WORKING
    'VOLTCRAFT PL-125-T2',      #67
    'Phidget TMP1200 1xRTD A',  #68
    'Phidget IO Digital 01',    #69
    '+Phidget IO Digital 23',   #70
    '+Phidget IO Digital 45',   #71
    '+Phidget IO Digital 67',   #72
    'Phidget 1011 IO Digital 01', #73
    'Phidget HUB IO Digital 01', #74
    '+Phidget HUB IO Digital 23',#75
    '+Phidget HUB IO Digital 45',#76
    'VOLTCRAFT PL-125-T4',       #77
    '+VOLTCRAFT PL-125-T4 34',   #78
    'S7',                        #79
    '+S7 34',                    #80
    '+S7 56',                    #81
    '+S7 78',                    #82
    'Aillio Bullet R1 BT/DT',             #83
    '+Aillio Bullet R1 Heater/Fan',       #84
    '+Aillio Bullet R1 BT RoR/Drum',      #85
    '+Aillio Bullet R1 Voltage/Exhaust',  #86
    '+Aillio Bullet R1 State/Fan RPM',    #87
    '+Program 78',               #88
    '+Program 910',              #89
    '+Slider 01',                #90
    '+Slider 23',                #91
    '-Probat Middleware',                 #92
    '-Probat Middleware burner/drum',     #93
    '-Probat Middleware fan/pressure',    #94
    'Phidget DAQ1400 Current',   #95
    'Phidget DAQ1400 Frequency', #96
    'Phidget DAQ1400 Digital',   #97
    'Phidget DAQ1400 Voltage',   #98
    'Aillio Bullet R1 IBTS/BT',  #99
    'Yocto IR',                  #100
    'Behmor BT/CT',              #101
    '+Behmor 34',                #102
    'VICTOR 86B',                #103
    '+Behmor 56',                #104
    '+Behmor 78',                #105
    'Phidget HUB IO 0',          #106
    'Phidget HUB IO Digital 0',  #107
    'Yocto 4-20mA Rx',           #108
    '+MODBUS 78',                #109
    '+S7 910',                   #110
    'WebSocket',                 #111
    '+WebSocket 34',             #112
    '+WebSocket 56',             #113
    '+Phidget TMP1200 1xRTD B',  #114
    'HB BT/ET',                  #115
    '+HB DT/IT',                 #116
    '+HB AT',                    #117
    '+WebSocket 78',             #118
    '+WebSocket 910',            #119
    'Yocto 0-10V Rx',            #120
    'Yocto milliVolt Rx',        #121
    'Yocto Serial',              #122
    'Phidget VCP1000',           #123
    'Phidget VCP1001',           #124
    'Phidget VCP1002',           #125
    'ARC BT/ET',                 #126
    '+ARC MET/IT',               #127
    '+ARC AT',                   #128
    'Yocto Power',               #129
    'Yocto Energy',              #130
    'Yocto Voltage',             #131
    'Yocto Current',             #132
    'Yocto Sensor',              #133
    'Santoker BT/ET',            #134
    '+Santoker Power/Fan',       #135
    '+Santoker Drum',            #136
    'Phidget DAQ1500',           #137
    'Kaleido BT/ET',             #138
    '+Kaleido SV/AT',            #139
    '+Kaleido Drum/AH',          #140
    '+Kaleido Heater/Fan',       #141
    'IKAWA',                     #142
    '+IKAWA SET/RPM',            #143
    '+IKAWA Heater/Fan',         #144
    '+IKAWA State/Humidity',     #145
    'Phidget DAQ1000 01',        #146
    '+Phidget DAQ1000 23',       #147
    '+Phidget DAQ1000 45',       #148
    '+Phidget DAQ1000 67',       #149
    '+MODBUS 910',               #150
    '+S7 1112',                  #151
    'Phidget DAQ1200 01',        #152
    '+Phidget DAQ1200 23',       #153
    'Phidget DAQ1300 01',        #154
    '+Phidget DAQ1300 23',       #155
    'Phidget DAQ1301 01',        #156
    '+Phidget DAQ1301 23',       #157
    '+Phidget DAQ1301 45',       #158
    '+Phidget DAQ1301 67',       #159
    f'+IKAWA {deltaLabelUTF8}Humidity/{deltaLabelUTF8}Humidity Dir.',    #160
    '+Omega HH309 34',           #161
    'Digi-Sense 20250-07',       #162
    'Extech 42570',              #163
    'Mugma BT/ET',               #164
    '+Mugma Heater/Fan',         #165
    '+Mugma Heater/Catalyzer',   #166
    '+Mugma SV',                 #167
    'Phidget TMP1202 1xRTD A',   #168
    '+Phidget TMP1202 1xRTD B',  #169
    'ColorTrack Serial',         #170
    'Santoker R BT/ET',          #171
    '+Santoker IR/Board',        #172
    '+Santoker DelatBT/DeltaET', #173
    'ColorTrack BT',             #174
    'Thermoworks BlueDOT',       #175
    'Aillio Bullet R2',          #176
    '+PID P/I',                  #177
    '+PID D/Error',              #178
    '+Shelly 3EM Pro Energy/Return', #179
    '+Shelly Plug Energy/Last',      #180
    '+Shelly 3EM Pro Power/S',       #181
    '+Shelly Plug Power/Temp',       #182
    '+Shelly Plug Voltage/Current',  #183
    'TASI TA612C',                   #184
    '+TASI TA612C 34',               #185
    '+CM ET/BT',                     #186
    '+RoastSeeNEXT Agtron/Crack',    #187
    '+RoastSeeNEXT RoR/FoR',         #188
    '+RoastSeeNEXT Distance/Time',   #189
    '+RoastSeeNEXT Yellow',          #190
    '+Phidget TMP1000',           #191
    '+Phidget HUM1000 Hum/Temp',  #192
    '+Phidget PRE1000',           #193
    '+Yocto Meteo Hum/Temp',      #194
    '+Yocto Meteo Pressure',      #195
    'Orbiter BT/ET',              #196
    '+Orbiter IT/DT',             #197
    '+Orbiter Sound/Drum',        #198
    '+Orbiter Damper/Heater',     #199
    '+Orbiter Air/RoR',           #200
    'MQTT',                       #201
    '+MQTT 34',                   #202
    '+MQTT 56',                   #203
    '+MQTT 78',                   #204
    '+MQTT 910',                  #205
    '+MQTT 1112',                 #206
]

# ids of (main) Phidget devices (without a + in front of their name string) as well as Phidget TMP100, HUM100 or PRE1000
PHIDGET_DEVICES: Final[list[int]] = [
    34, # Phidget 1048
    37, # Phidget 1046
    40, # Phidget IO
    47, # Phidget 1045
    52, # Phidget 1051
    58, # Phidget TMP1101
    61, # Phidget TMP1100
    62, # Phidget 1011
    63, # Phidget HUB IO 01
    64, # Phidget HUB IO 23 # + device but need to be mounted directly
    65, # Phidget HUB IO 45 # + device but need to be mounted directly
    68, # Phidget TMP1200
    69, # Phidget IO Digital
    73, # Phidget 1011 IO Digital
    74, # Phidget HUB IO Digital 01
    75, # Phidget HUB IO Digital 23 # + device but need to be mounted directly
    76, # Phidget HUB IO Digital 45 # + device but need to be mounted directly
    95, # Phidget DAQ1400 Current
    96, # Phidget DAQ1400 Frequency
    97, # Phidget DAQ1400 Digital
    98, # Phidget DAQ1400 Voltage
    106, # Phidget HUB IO 0
    107, # Phidget HUB IO Digital 0
    123, # Phidget VCP1000
    124, # Phidget VCP1001
    125, # Phidget VCP1002
    137, # Phidget DAQ1500
    146, # Phidget DAQ1000 01
    152, # Phidget DAQ1200 01
    154, # Phidget DAQ1300 01
    156, # Phidget DAQ1301 01
    168, # Phidget TMP1202
    191, # +Phidget TMP1000
    192, # +Phidget HUM1000 Hum/Temp
    193, # +Phidget PRE1000
]

# ids of (main) devices (without a + in front of their name string)
# that do NOT communicate via any serial port thus do not need any serial port configuration
NON_SERIAL_DEVICES: Final[list[int]] = PHIDGET_DEVICES + [
    18, # NONE (manual)
    27, # Program
    45, # Yocto Thermocouple
    46, # Yocto PT100
    79, # S7
    83, # Aillio Bullet R1 BT/DT
    99, # Aillio Bullet R1 IBTS/BT
    100, # Yocto IR
    108, # Yocto 4-20mA Rx
    111, # WebSocket
    120, # Yocto-0-10V-Rx
    121, # Yocto-milliVolt-Rx
    122, # Yocto-Serial
    129, # Yocto Power
    130, # Yocto Energy
    131, # Yocto Voltage
    132, # Yocto Current
    133, # Yocto Sensor
    134, # Santoker BT/ET
    138, # Kaleido BT/ET
    142, # IKAWA,
    164, # Mugma BT/ET
    171, # Santoker R BT/ET
    174, # ColorTrack BT
    175, # Thermoworks BlueDOT
    176, # Aillio Bullet R2
    194, # +Yocto Meteo Hum/Temp
    195, # +Yocto Meteo Pressure
]

# ids of devices temperature conversions should not be applied
NON_TEMP_DEVICES: Final[list[int]] = [
    22, # +PID SV/DUTY %
    25, # +Virtual
    40, # Phidget IO 01
    41, # +Phidget IO 23
    42, # +Phidget IO 45
    43, # +Phidget IO 67
    50, # DUMMY
    54, # +Hottop Heater/Fan
    57, # EXTECH 755
    62, # Phidget 1011 IO 01
    63, # Phidget HUB IO 01
    64, # +Phidget HUB IO 23
    65, # +Phidget HUB IO 45
    69, # Phidget IO Digital 01
    70, # +Phidget IO Digital 23
    71, # +Phidget IO Digital 45
    72, # +Phidget IO Digital 67
    73, # Phidget 1011 IO Digital 01
    74, # Phidget HUB IO Digital 0
    75, # +Phidget HUB IO Digital 23
    76, # +Phidget HUB IO Digital 45
    84, # +Aillio Bullet R1 Heater/Fan
    87, # +Aillio Bullet R1 State
    90, # +Slider 01
    91, # +Slider 23
    95, # Phidget DAQ1400 Current
    96, # Phidget DAQ1400 Frequency
    97, # Phidget DAQ1400 Digital
    98, # Phidget DAQ1400 Voltage
    106, # Phidget HUB IO 0
    107, # Phidget HUB IO Digital 0
    108, # Yocto 4-20mA Rx
    120, # Yocto-0-10V-Rx
    121, # Yocto-milliVolt-Rx
    122, # Yocto-Serial
    123, # Phidget VCP1000
    124, # Phidget VCP1001
    125, # Phidget VCP1002
    129, # Yocto Power
    130, # Yocto Energy
    131, # Yocto Voltage
    132, # Yocto Current
    133, # Yocto Sensor
    135, # Santoker Power/Fan
    136, # Santoker Drum
    137, # Phidget DAQ1500
    140, # Kaleido Drum/AH
    141, # Kaleido Heater/Fan
    143, # IKAWA Set/RPM
    144, # IKAWA Heater/Fan
    145, # IKAWA State/Humidity
    146, # Phidget DAQ1000 01
    147, # +Phidget DAQ1000 23
    148, # +Phidget DAQ1000 45
    149, # +Phidget DAQ1000 67
    152, # Phidget DAQ1200 01
    153, # +Phidget DAQ1200 23
    154, # Phidget DAQ1300 01
    155, # +Phidget DAQ1300 23
    156, # Phidget DAQ1301 01
    157, # +Phidget DAQ1301 23
    158, # +Phidget DAQ1301 45
    159, # +Phidget DAQ1301 67
    160, # IKAWA Delta Humidity / Delta Humidity direction
    165, # +Mugma Heater/Fan
    166, # +Mugma Heater/Catalyzer
    170, # ColorTrack Serial
    173, # +Santoker BT RoR / ET RoR
    174, # ColorTrack BT
    177, # +PID P/I
    178, # +PID D/Error
    179, # +Shelly 3EM Pro Energy/Return
    180, # +Shelly Plug Total/Last
    181, # +Shelly 3EM Pro Power/S
    182, # +Shelly Plug Power/Temp
    183, # +Shelly Plug Voltage/Current
    187, # +RoastSeeNEXT Agtron/Crack
    188, # +RoastSeeNEXT RoR/FOR
    189, # +RoastSeeNEXT Distance/Time
    190, # +RoastSeeNEXT Yellow
    191, # +Phidget TMP1000
    192, # +Phidget HUM1000 Hum/Temp
    193, # +Phidget PRE1000
    194, # +Yocto Meteo Hum/Temp
    195, # +Yocto Meteo Pressure
    198, # +Orbiter Sound/Drum
    199, # +Orbiter Damper/Heater
    200, # +Orbiter Air/RoR
]

# ids of special devices certain input filters should not be applied
SPECIAL_DEVICES: Final[list[int]] = [
    18, # NONE (Manual)
    25, # Virtual
    50, # Dummy
    90, # Slider01
    91, # Slider23
]

# ids of devices with binary results (0 and 1) certain input filters should not be applied
BINARY_DEVICES: Final[list[int]] = [
    69, # Phidget IO Digital 01
    70, # Phidget IO Digital 23
    71, # Phidget IO Digital 45
    72, # Phidget IO Digital 67
    73, # Phidget 1011 IO Digital 01
    74, # Phidget HUB IO Digital 01
    75, # Phidget HUB IO Digital 23
    76, # Phidget HUB IO Digital 45
]

# computed device info dictionary: device_id -> {name, index}
DEVICE_INFO: Final[dict[int, dict[str, str | int]]] = {
    i + 1: {"name": name, "index": i} for i, name in enumerate(DEVICES)
}


# -- helper functions ---------------------------------------------------------

def is_phidget_device(device_id: int) -> bool:
    return device_id in PHIDGET_DEVICES


def is_non_serial_device(device_id: int) -> bool:
    return device_id in NON_SERIAL_DEVICES


def is_non_temp_device(device_id: int) -> bool:
    return device_id in NON_TEMP_DEVICES


def is_special_device(device_id: int) -> bool:
    return device_id in SPECIAL_DEVICES


def is_binary_device(device_id: int) -> bool:
    return device_id in BINARY_DEVICES


def get_device_name(device_id: int) -> str:
    return DEVICES[device_id - 1]
