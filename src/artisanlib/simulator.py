#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ABOUT
# A simple device simulator for Artisan

import time as libtime
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
            self.temp1 = self.temp1[start:]
            self.temp2 = self.temp2[start:]
            self.timex = self.timex[start:]
            self.extratemp1 = self.extratemp1[start:]
            self.extratemp2 = self.extratemp2[start:]
            self.extratimex = self.extratimex[start:]
        except:
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
        except:
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
        except:
            pass
        return t2,t1
        