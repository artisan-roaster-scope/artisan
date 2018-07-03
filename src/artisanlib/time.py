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
class ArtisanTime():
    def __init__(self):
        self.clock = time.perf_counter()

    def setHMS(self,*_):
        self.start()
        
    def start(self):
        self.clock = time.perf_counter()
        
    def elapsed(self):
        return (time.perf_counter() - self.clock)*1000.

    
