#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# list_ports_vid_pid_osx_posix.py
#
# Copyright (c) 2013, Paul Holleis, Marko Luther
# All rights reserved.
# 
# 
# LICENSE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
from serial.tools.list_ports import comports

""" 
Contains tools for taking a serial object from the standard serial module,
and intellegently parse out and use PID/VID and iSerial values from it
"""   

def portdict_from_port(port):
    """
    Given a port object from serial.comport() create a vid/pid/iSerial/port dict if possible

    @param str identifier_string: String retrieved from a serial port
    @return dict: A dictionary VID/PID/iSerial/Port.  On parse error dict contails only 'Port':port'
    """
    identifier_string = port[-1]
    data = {'blob':port}
    data['port'] = port[0]
    try:
        vid, pid, serial_number = re.search('VID:PID=([0-9A-Fa-f]{1,4}):([0-9A-Fa-f]{1,4}) SNR=(\w*)', identifier_string).groups()
        data['VID'] = int(vid,16)
        data['PID'] = int(pid,16)
        data['iSerial'] = serial_number
    except AttributeError:
        pass
    return data   



def list_ports_by_vid_pid(vid=None, pid=None):
    """ Given a VID and PID value, scans for available port, and
	if matches are found, returns a dict of 'VID/PID/iSerial/Port'
	that have those values.

    @param int vid: The VID value for a port
    @param int pid: The PID value for a port
    @return iterator: Ports that are currently active with these VID/PID values
    """
    #Get a list of all ports
    ports = comports()
    return filter_ports_by_vid_pid(ports, vid, pid)

def filter_ports_by_vid_pid(ports,vid=None,pid=None):
    """ Given a VID and PID value, scans for available port, and
	f matches are found, returns a dict of 'VID/PID/iSerial/Port'
	that have those values.

    @param list ports: Ports object of valid ports
    @param int vid: The VID value for a port
    @param int pid: The PID value for a port
    @return iterator: Ports that are currently active with these VID/PID values
    """
    for port in ports:
        #Parse some info out of the identifier string
        try: 
            data = portdict_from_port(port)
            if vid == None or data['VID'] == vid:
                if  pid == None or  data['PID'] == pid:
                    yield data
        except:
            pass
