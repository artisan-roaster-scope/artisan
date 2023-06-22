#

import time

# higher resolution time signal (at least on macOS)
# base can change (eg. depending on the simulator mode)
class ArtisanTime:

    __slots__ = ['clock','base']

    def __init__(self) -> None:
        self.clock = time.perf_counter()
        self.base = 1000.

    def setBase(self,b):
        self.base = b

    def getBase(self):
        return self.base

    def setHMS(self,*_):
        self.start()

    def start(self):
        self.clock = time.perf_counter()

    def addClock(self, period):
        self.clock = self.clock + period

    def elapsed(self):
        return (time.perf_counter() - self.clock)*self.base

    def elapsedMilli(self):
        return (time.perf_counter() - self.clock)*self.base/1000.
