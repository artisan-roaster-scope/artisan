#!/usr/bin/env python

# results in a three digits resolution (eg. 1.234)
#class ArtisanTime():
#    def __init__(self):
#        self.clock = QTime()
#
#    def setHMS(self,a,b,c,d):
#        self.clock.setHMS(a,b,c,d)
#        
#    def start(self):
#        self.clock.start()
#        
#    def elapsed(self):
#        return self.clock.elapsed()

import time

# higher resultion time signal (at least on Mac OS X)
class ArtisanTime(object):

    __slots__ = ['clock','base']
    
    def __init__(self):
        self.clock = time.perf_counter()
        self.base = 1000.
    
    def setBase(self,b):
        self.base = b

    def setHMS(self,*_):
        self.start()
        
    def start(self):
        self.clock = time.perf_counter()
        
    def elapsed(self):
        return (time.perf_counter() - self.clock)*self.base

    
