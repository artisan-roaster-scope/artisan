#
# ABOUT
# Artisan Time

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
# Marko Luther, 2023

import time

# higher resolution time signal (at least on macOS)
# base can change (eg. depending on the simulator mode)
class ArtisanTime:

    __slots__ = ['clock','base']

    def __init__(self) -> None:
        self.clock = time.perf_counter()
        self.base:float = 1000.

    def setBase(self,b:float) -> None:
        self.base = b

    def getBase(self) -> float:
        return self.base

    def start(self) -> None:
        self.clock = time.perf_counter()

    def addClock(self, period:float) -> None:
        self.clock = self.clock + period

    def elapsed(self) -> float:
        return (time.perf_counter() - self.clock)*self.base

    def elapsedMilli(self) -> float:
        return (time.perf_counter() - self.clock)*self.base/1000.
