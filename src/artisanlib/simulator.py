# -*- coding: utf-8 -*-
#
# ABOUT
# A simple device simulator for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2020

import numpy

class Simulator():
    def __init__(self, profile = None):
        self.profile = profile
        self.temp1 = profile["temp1"]
        self.temp2 = profile["temp2"]
        self.timex = profile["timex"]
        self.extratemp1 = profile["extratemp1"]
        self.extratemp2 = profile["extratemp2"]
        self.extratimex = profile["extratimex"]
        self.removeEmptyPrefix()
    
    def removeEmptyPrefix(self):
        try:
            # select the first BT index not an error value to start with
            start = list(map(lambda i: i != -1, self.temp2)).index(True) 
            self.temp1 = numpy.array(self.temp1[start:])
            self.temp2 = numpy.array(self.temp2[start:])
            self.timex = numpy.array(self.timex[start:])
            for i in range(len(self.extratimex)):
                self.extratemp1[i] = numpy.array(self.extratemp1[i][start:])
                self.extratemp2[i] = numpy.array(self.extratemp2[i][start:])
                self.extratimex[i] = numpy.array(self.extratimex[i][start:])
            # shift timestamps such that they start with 0
            if len(self.timex) > 0:
                self.timex = self.timex - self.timex[0]
            # shift timestamps such that they start with 0
            for i in range(len(self.extratimex)):
                if len(self.extratimex[i]) > 0:
                    self.extratimex[i] = self.extratimex[i] - self.extratimex[i][0]
        except Exception: # pylint: disable=broad-except
            pass
    
    def read(self,tx):
        et = -1
        bt = -1
        try:
            if tx == 0:
                et = self.temp1[0]
                bt = self.temp2[0]
            else:
                et = numpy.interp(tx,self.timex,self.temp1)
                bt = numpy.interp(tx,self.timex,self.temp2)
        except Exception: # pylint: disable=broad-except
            pass
        return et,bt
    
    def readextra(self,i,tx):
        t1 = -1
        t2 = -1
        try:
            if tx == 0:
                t1 = self.extratemp1[i][0]
                t2 = self.extratemp2[i][0]
            else:
                t1 = numpy.interp(tx,self.extratimex[i],self.extratemp1[i])
                t2 = numpy.interp(tx,self.extratimex[i],self.extratemp2[i])
        except Exception: # pylint: disable=broad-except
            pass
        return t2,t1
        